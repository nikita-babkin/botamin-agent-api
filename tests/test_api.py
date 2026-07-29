import importlib
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api(monkeypatch, tmp_path):
    monkeypatch.setenv("BOTAMIN_API_KEY", "test-secret")
    for module_name in ("app.main", "app.booking", "app.config"):
        sys.modules.pop(module_name, None)

    config = importlib.import_module("app.config")
    booking = importlib.import_module("app.booking")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "BOOKINGS_FILE", tmp_path / "bookings.jsonl")
    monkeypatch.setattr(booking, "DATA_DIR", tmp_path)
    monkeypatch.setattr(booking, "BOOKINGS_FILE", tmp_path / "bookings.jsonl")
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def headers() -> dict[str, str]:
    return {"X-API-Key": "test-secret"}


def test_health(api):
    response = api.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_slots_require_api_key(api):
    response = api.post("/available-slots", json={"date_mode": "nearest", "period": "any"})
    assert response.status_code == 401


def test_available_slots(api):
    response = api.post(
        "/available-slots",
        headers=headers(),
        json={"date_mode": "nearest", "period": "any"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["slots"]) == 2

    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    for item in body["slots"]:
        slot = datetime.fromisoformat(item["slot_datetime"])
        assert slot.date() > today
        assert slot.weekday() < 5
        assert 9 <= slot.hour <= 17


def test_booking_and_duplicate(api):
    slot = api.post(
        "/available-slots",
        headers=headers(),
        json={"date_mode": "nearest", "period": "any"},
    ).json()["slots"][0]["slot_datetime"]
    payload = {
        "slot_datetime": slot,
        "contact": "@test_user",
        "work_email": "user@company.ru",
        "company_activity": "Продажа оборудования",
    }
    assert api.post("/book-meeting", headers=headers(), json=payload).json()["success"] is True
    duplicate = api.post("/book-meeting", headers=headers(), json=payload)
    assert duplicate.json()["success"] is False
    assert duplicate.json()["reason"] == "Этот слот уже занят"


def test_invalid_email(api):
    response = api.post(
        "/book-meeting",
        headers=headers(),
        json={
            "slot_datetime": "2030-01-10T11:00:00+03:00",
            "contact": "@test_user",
            "work_email": "invalid-email",
            "company_activity": "Продажа оборудования",
        },
    )
    assert response.status_code == 422
