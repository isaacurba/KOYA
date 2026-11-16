from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from src.dtos.booking_dto import BookingCreateDTO, BookingResponseDTO
from src.exceptions.domain import (
    BookingAlreadyCancelled,
    BookingNotFound,
    SlotAlreadyBooked,
    SlotInPast,
    SlotNotFound,
)
from src.models.booking import Booking, BookingStatus
from src.repositories.booking_repository import BookingRepository
from src.repositories.slot_repository import SlotRepository


class BookingService:
    """Service implementing business rules for clinic appointment bookings."""

    def __init__(self, booking_repo: BookingRepository, slot_repo: SlotRepository) -> None:
        self.booking_repo = booking_repo
        self.slot_repo = slot_repo

    def create_booking(
        self,
        slot_id: str | BookingCreateDTO,
        name: str | None = None,
        email: str | None = None,
    ) -> BookingResponseDTO:
        """Create a new confirmed appointment booking.

        1. Confirms the slot exists.
        2. Rejects slots whose start time has already passed.
        3. Prevents booking if already confirmed (application check).
        4. Persists the confirmed booking.
        5. Catches concurrency race conditions via partial unique index IntegrityError and raises SlotAlreadyBooked.
        """
        if isinstance(slot_id, BookingCreateDTO):
            dto = slot_id
        else:
            dto = BookingCreateDTO(slot_id=slot_id, name=name, email=email)

        # 1. Slot existence check
        slot = self.slot_repo.get_by_id(dto.slot_id)
        if slot is None:
            raise SlotNotFound(f"Appointment slot '{dto.slot_id}' does not exist.")

        # 2. Reject past start times
        now = datetime.now(timezone.utc)
        slot_start = slot.start if slot.start.tzinfo else slot.start.replace(tzinfo=timezone.utc)
        if slot_start <= now:
            raise SlotInPast(f"Cannot book appointment slot '{dto.slot_id}' because it has already started.")

        # 3. Application-level availability check
        existing_confirmed = self.booking_repo.get_confirmed_by_slot_id(dto.slot_id)
        if existing_confirmed is not None:
            raise SlotAlreadyBooked(f"Appointment slot '{dto.slot_id}' is already booked.")

        # 4. Prepare booking entity
        booking = Booking(
            id=str(uuid.uuid4()),
            slot_id=dto.slot_id,
            name=dto.name,
            email=dto.email,
            status=BookingStatus.CONFIRMED.value,
        )

        # 5. Database persistence with concurrency protection
        try:
            created = self.booking_repo.create(booking)
        except IntegrityError as exc:
            orig_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
            if "uq_confirmed_slot_booking" in orig_msg or "unique" in orig_msg.lower():
                raise SlotAlreadyBooked(
                    f"Appointment slot '{dto.slot_id}' is already booked."
                ) from exc
            # Surface other unexpected database errors (e.g. check constraints, foreign key issues)
            raise

        return BookingResponseDTO.model_validate(created)

    def get_booking(self, booking_id: str) -> BookingResponseDTO:
        """Retrieve a booking by its unique identifier."""
        booking = self.booking_repo.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFound(f"Booking with id '{booking_id}' does not exist.")
        return BookingResponseDTO.model_validate(booking)

    def cancel_booking(self, booking_id: str) -> BookingResponseDTO:
        """Cancel an existing confirmed booking.

        - Rejects with 404 if booking not found.
        - Rejects with 409 if already cancelled.
        - Updates status to 'cancelled', preserving history and freeing the slot.
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFound(f"Booking with id '{booking_id}' does not exist.")

        if booking.status == BookingStatus.CANCELLED.value:
            raise BookingAlreadyCancelled(f"Booking with id '{booking_id}' has already been cancelled.")

        updated = self.booking_repo.update_status(booking, BookingStatus.CANCELLED)
        return BookingResponseDTO.model_validate(updated)
