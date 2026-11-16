from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base

if TYPE_CHECKING:
    from src.models.booking import Booking


class Slot(Base):
    """SQLAlchemy model representing an appointment slot offered by a clinic provider."""
    __tablename__ = "slots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # One-to-many relationship: One slot can have multiple booking records over time (history + active)
    bookings: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="slot",
        cascade="all, delete",
        passive_deletes=True,
    )
