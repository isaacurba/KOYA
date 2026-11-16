from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from pydantic import BaseModel, Field, field_validator, model_validator


class SlotCreateDTO(BaseModel):
    """DTO for creating or replacing appointment slots."""
    id: str = Field(..., min_length=1, description="Unique slot identifier")
    provider: str = Field(..., min_length=1, description="Healthcare provider name")
    start: datetime = Field(..., description="Appointment start time in UTC")
    end: datetime = Field(..., description="Appointment end time in UTC")

    @field_validator("id", "provider", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v

    @field_validator("start", "end", mode="after")
    @classmethod
    def ensure_tz_aware(cls, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @model_validator(mode="after")
    def validate_chronology(self) -> Self:
        if self.start >= self.end:
            raise ValueError("Appointment start time must be before end time.")
        return self


class SlotResponseDTO(BaseModel):
    """DTO representing an appointment slot with computed availability."""
    id: str
    provider: str
    start: datetime
    end: datetime
    available: bool

    model_config = {"from_attributes": True}


class SlotListResponseDTO(BaseModel):
    """DTO wrapping a list of appointment slots."""
    slots: list[SlotResponseDTO]


class ResetSlotsRequestDTO(BaseModel):
    """DTO payload for resetting the appointment schedule."""
    slots: list[SlotCreateDTO] = Field(default_factory=list)
