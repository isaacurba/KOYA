from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.booking import Booking, BookingStatus


class BookingRepository:
    """Repository managing database persistence and queries for Booking entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, booking_id: str) -> Booking | None:
        """Retrieve a booking by its unique identifier."""
        return self.session.get(Booking, booking_id)

    def get_confirmed_by_slot_id(self, slot_id: str) -> Booking | None:
        """Retrieve the active confirmed booking for a given slot, if one exists."""
        stmt = (
            select(Booking)
            .where(
                Booking.slot_id == slot_id,
                Booking.status == BookingStatus.CONFIRMED.value,
            )
        )
        return self.session.scalars(stmt).first()

    def create(self, booking: Booking) -> Booking:
        """Persist a new booking to the database.

        If a confirmed booking already exists for the same slot, the database
        partial unique index will raise an IntegrityError, which is rolled back and re-raised.
        """
        try:
            self.session.add(booking)
            self.session.commit()
            self.session.refresh(booking)
            return booking
        except Exception:
            self.session.rollback()
            raise

    def update_status(self, booking: Booking, status: str | BookingStatus) -> Booking:
        """Update the lifecycle status of an existing booking (e.g. 'confirmed' -> 'cancelled')."""
        status_value = status.value if isinstance(status, BookingStatus) else status
        booking.status = status_value
        try:
            self.session.add(booking)
            self.session.commit()
            self.session.refresh(booking)
            return booking
        except Exception:
            self.session.rollback()
            raise

    def list_by_slot_id(self, slot_id: str) -> Sequence[Booking]:
        """List all historical and active bookings associated with a slot."""
        stmt = (
            select(Booking)
            .where(Booking.slot_id == slot_id)
            .order_by(Booking.created_at.asc())
        )
        return self.session.scalars(stmt).all()
