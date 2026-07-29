import json
import uuid
from datetime import date, datetime, timedelta

from app.config import BOOKINGS_FILE, DATA_DIR, MSK


RU_WEEKDAYS = [
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
]

RU_MONTHS = [
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]


def next_workday(current_date: date) -> date:
    candidate = current_date + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def move_to_workday(candidate: date) -> date:
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def format_spoken_datetime(value: datetime) -> str:
    weekday = RU_WEEKDAYS[value.weekday()]
    month = RU_MONTHS[value.month]
    return f"{weekday}, {value.day} {month}, в {value:%H:%M} по Москве"


def resolve_requested_date(
    date_mode: str,
    specific_date: date | None,
    today: date,
) -> date:
    if date_mode == "tomorrow":
        candidate = today + timedelta(days=1)
    elif date_mode == "specific_date" and specific_date:
        candidate = specific_date
    else:
        candidate = next_workday(today)

    if candidate <= today:
        candidate = next_workday(today)
    return move_to_workday(candidate)


def get_slot_hours(period: str) -> list[int]:
    if period == "morning":
        return [10, 12]
    if period == "afternoon":
        return [14, 16]
    return [11, 15]


def normalize_to_moscow(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=MSK)
    return value.astimezone(MSK)


def load_booked_slots() -> set[str]:
    if not BOOKINGS_FILE.exists():
        return set()

    result: set[str] = set()
    with BOOKINGS_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                booking = json.loads(line)
                result.add(booking["slot_datetime"])
            except (json.JSONDecodeError, KeyError):
                continue
    return result


def generate_slots(selected_date: date, period: str) -> list[dict[str, str]]:
    booked_slots = load_booked_slots()
    result: list[dict[str, str]] = []
    candidate_date = selected_date

    while len(result) < 2:
        candidate_date = move_to_workday(candidate_date)
        for hour in get_slot_hours(period):
            slot = datetime(
                candidate_date.year,
                candidate_date.month,
                candidate_date.day,
                hour,
                tzinfo=MSK,
            )
            if slot.isoformat() in booked_slots:
                continue
            result.append(
                {
                    "slot_datetime": slot.isoformat(),
                    "spoken": format_spoken_datetime(slot),
                }
            )
            if len(result) == 2:
                break
        candidate_date = next_workday(candidate_date)
    return result


def validate_booking_slot(slot: datetime, now: datetime) -> str | None:
    if slot.date() <= now.date():
        return "На сегодня и прошедшие даты встречи не назначаются"
    if slot.weekday() >= 5:
        return "Встречи доступны только по будням"
    if (slot.hour, slot.minute) < (9, 0):
        return "Время начала встречи должно быть не раньше 09:00"
    if (slot.hour, slot.minute) > (17, 0):
        return "Время начала встречи должно быть не позже 17:00"
    return None


def save_booking(
    slot: datetime,
    contact: str,
    work_email: str,
    company_activity: str,
) -> dict[str, str | int]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    booking_id = f"BOT-{uuid.uuid4().hex[:8].upper()}"
    booking: dict[str, str | int] = {
        "booking_id": booking_id,
        "slot_datetime": slot.isoformat(),
        "duration_minutes": 20,
        "contact": contact,
        "work_email": work_email,
        "company_activity": company_activity,
        "created_at": datetime.now(MSK).isoformat(),
    }
    with BOOKINGS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(booking, ensure_ascii=False) + "\n")
    return booking
