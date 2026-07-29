from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class SlotsRequest(BaseModel):
    date_mode: Literal["nearest", "tomorrow", "specific_date"] = "nearest"
    specific_date: date | None = None
    period: Literal["any", "morning", "afternoon"] = "any"

    @model_validator(mode="after")
    def validate_specific_date(self) -> "SlotsRequest":
        if self.date_mode == "specific_date" and self.specific_date is None:
            raise ValueError("specific_date обязателен при date_mode=specific_date")
        return self


class BookingRequest(BaseModel):
    slot_datetime: datetime
    contact: str = Field(min_length=2, description="Телефон или Telegram пользователя")
    work_email: EmailStr
    company_activity: str = Field(min_length=2, description="Чем занимается компания")
