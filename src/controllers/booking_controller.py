from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.dtos.booking_dto import BookingCreateDTO, BookingResponseDTO
from src.repositories.booking_repository import BookingRepository
from src.repositories.slot_repository import SlotRepository
from src.services.booking_service import BookingService

router = APIRouter(tags=["Bookings"])


@router.post("/bookings", response_model=BookingResponseDTO, status_code=201)
def create_booking(
    payload: BookingCreateDTO,
    db: Session = Depends(get_db),
):
    """Create a new appointment booking for an available slot."""
    booking_repo = BookingRepository(db)
    slot_repo = SlotRepository(db)
    booking_service = BookingService(booking_repo, slot_repo)
    return booking_service.create_booking(payload)


@router.get("/bookings/{id}", response_model=BookingResponseDTO, status_code=200)
def get_booking(
    id: str,
    db: Session = Depends(get_db),
):
    """Retrieve an existing booking by its unique identifier."""
    booking_repo = BookingRepository(db)
    slot_repo = SlotRepository(db)
    booking_service = BookingService(booking_repo, slot_repo)
    return booking_service.get_booking(id)


@router.delete("/bookings/{id}", response_model=BookingResponseDTO, status_code=200)
def cancel_booking(
    id: str,
    db: Session = Depends(get_db),
):
    """Cancel an existing booking and restore availability of the appointment slot."""
    booking_repo = BookingRepository(db)
    slot_repo = SlotRepository(db)
    booking_service = BookingService(booking_repo, slot_repo)
    return booking_service.cancel_booking(id)
