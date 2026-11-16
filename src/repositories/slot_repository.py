from __future__ import annotations

from typing import Sequence
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from src.models.booking import Booking
from src.models.slot import Slot


class SlotRepository:
    """Repository managing database persistence and queries for Slot entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, slot_id: str) -> Slot | None:
        """Retrieve a single appointment slot by its unique identifier."""
        return self.session.get(Slot, slot_id)

    def list_all(self, provider: str | None = None) -> Sequence[Slot]:
        """List appointment slots ordered chronologically by earliest start time.

        If a provider is specified, filters slots to only that provider.
        """
        stmt = select(Slot).options(selectinload(Slot.bookings))
        if provider:
            stmt = stmt.where(Slot.provider == provider)
        stmt = stmt.order_by(Slot.start.asc())
        return self.session.scalars(stmt).all()

    def reset_slots(self, slots: list[Slot]) -> list[Slot]:
        """Atomically replace all existing appointment slots and bookings with the provided slots."""
        try:
            # Delete dependent bookings first, then slots
            self.session.execute(delete(Booking))
            self.session.execute(delete(Slot))
            if slots:
                self.session.add_all(slots)
            self.session.commit()
            for slot in slots:
                self.session.refresh(slot)
            return slots
        except Exception:
            self.session.rollback()
            raise

    def create(self, slot: Slot) -> Slot:
        """Persist a new appointment slot to the database."""
        try:
            self.session.add(slot)
            self.session.commit()
            self.session.refresh(slot)
            return slot
        except Exception:
            self.session.rollback()
            raise
