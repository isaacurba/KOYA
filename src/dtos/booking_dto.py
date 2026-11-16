from __future__ import annotations

import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# RFC 5322-compliant pattern ensuring local-part and valid domain label structure
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


class BookingCreateDTO(BaseModel):
    """DTO for incoming booking creation requests."""
    slot_id: str = Field(..., min_length=1, description="Unique identifier of the slot to reserve")
    name: str = Field(..., min_length=1, description="Patient's full name")
    email: str = Field(..., min_length=1, description="Patient's email address")

    @field_validator("slot_id", "name", mode="before")
    @classmethod
    def strip_text(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalize_and_validate_email(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Email must be a string.")
        v = v.strip().lower()
        if not v:
            raise ValueError("Email cannot be empty.")
        if not EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address format: '{v}'.")
        return v


class BookingResponseDTO(BaseModel):
    """DTO for outgoing booking responses."""
    id: str
    slot_id: str
    name: str
    email: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
