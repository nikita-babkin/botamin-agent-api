import secrets
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.booking import (
    format_spoken_datetime,
    generate_slots,
    load_booked_slots,
    next_workday,
    normalize_to_moscow,
    resolve_requested_date,
    save_booking,
    validate_booking_slot,
)
from app.config import API_KEY, MSK
from app.schemas import BookingRequest, SlotsRequest


app = FastAPI(title="Botamin Booking API", version="1.0.0")


def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "Botamin Booking API", "status": "running", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "current_time_moscow": datetime.now(MSK).isoformat()}


@app.post("/available-slots", dependencies=[Depends(verify_api_key)])
def available_slots(request: SlotsRequest) -> dict:
    now = datetime.now(MSK)
    selected_date = resolve_requested_date(
        date_mode=request.date_mode,
        specific_date=request.specific_date,
        today=now.date(),
    )
    return {
        "success": True,
        "timezone": "Europe/Moscow",
        "meeting_duration_minutes": 20,
        "slots": generate_slots(selected_date, request.period),
    }


@app.post("/book-meeting", dependencies=[Depends(verify_api_key)])
def book_meeting(request: BookingRequest) -> dict:
    now = datetime.now(MSK)
    slot = normalize_to_moscow(request.slot_datetime)
    validation_error = validate_booking_slot(slot, now)

    if validation_error:
        return {
            "success": False,
            "reason": validation_error,
            "replacement_slots": generate_slots(next_workday(now.date()), "any"),
        }

    if slot.isoformat() in load_booked_slots():
        return {
            "success": False,
            "reason": "Этот слот уже занят",
            "replacement_slots": generate_slots(slot.date(), "any"),
        }

    booking = save_booking(
        slot=slot,
        contact=request.contact.strip(),
        work_email=str(request.work_email),
        company_activity=request.company_activity.strip(),
    )
    return {
        "success": True,
        "booking_id": booking["booking_id"],
        "message": "Встреча подтверждена",
        "slot_datetime": booking["slot_datetime"],
        "spoken": format_spoken_datetime(slot),
    }
