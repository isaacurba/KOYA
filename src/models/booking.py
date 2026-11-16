from __future__ import annotations
import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.slot import Slot


class BookingStatus(str, enum.Enum):
    """Lifecycle status for clinic appointment bookings."""
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(Base):
    """SQLAlchemy model representing a patient's appointment booking."""
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    slot_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("slots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BookingStatus.CONFIRMED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationship back to the booked slot
    slot: Mapped[Slot] = relationship("Slot", back_populates="bookings")

    __table_args__ = (
        # Ensure status is strictly 'confirmed' or 'cancelled' at the database level
        CheckConstraint(
            "status IN ('confirmed', 'cancelled')",
            name="chk_booking_status",
        ),
        # Partial unique index: guarantees at most one confirmed booking per slot
        Index(
            "uq_confirmed_slot_booking",
            "slot_id",
            unique=True,
            postgresql_where=text("status = 'confirmed'"),
            sqlite_where=text("status = 'confirmed'"),
        ),
    )
