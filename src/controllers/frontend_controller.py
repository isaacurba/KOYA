from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.dtos.booking_dto import BookingCreateDTO, BookingResponseDTO
from src.dtos.slot_dto import SlotListResponseDTO
from src.repositories.booking_repository import BookingRepository
from src.repositories.slot_repository import SlotRepository
from src.services.booking_service import BookingService
from src.services.slot_service import SlotService

router = APIRouter(prefix="/frontend-api", tags=["Frontend BFF"])


@router.get("/slots", response_model=SlotListResponseDTO, status_code=200)
def frontend_list_slots(
    provider: str | None = Query(None, description="Optional filter by healthcare provider"),
    db: Session = Depends(get_db),
):
    """BFF endpoint allowing the patient web interface to list appointment slots."""
    slot_repo = SlotRepository(db)
    slot_service = SlotService(slot_repo)
    slots = slot_service.list_slots(provider=provider)
    return SlotListResponseDTO(slots=slots)


@router.post("/bookings", response_model=BookingResponseDTO, status_code=201)
def frontend_create_booking(
    payload: BookingCreateDTO,
    db: Session = Depends(get_db),
):
    """BFF endpoint allowing patients to book an appointment slot."""
    booking_repo = BookingRepository(db)
    slot_repo = SlotRepository(db)
    booking_service = BookingService(booking_repo, slot_repo)
    return booking_service.create_booking(payload)


@router.get("/bookings/{id}", response_model=BookingResponseDTO, status_code=200)
def frontend_get_booking(
    id: str,
    db: Session = Depends(get_db),
):
    """BFF endpoint allowing patients to retrieve their booking confirmation details."""
    booking_repo = BookingRepository(db)
    slot_repo = SlotRepository(db)
    booking_service = BookingService(booking_repo, slot_repo)
    return booking_service.get_booking(id)


@router.delete("/bookings/{id}", response_model=BookingResponseDTO, status_code=200)
def frontend_cancel_booking(
    id: str,
    db: Session = Depends(get_db),
):
    """BFF endpoint allowing patients to cancel an existing confirmed booking."""
    booking_repo = BookingRepository(db)
    slot_repo = SlotRepository(db)
    booking_service = BookingService(booking_repo, slot_repo)
    return booking_service.cancel_booking(id)
