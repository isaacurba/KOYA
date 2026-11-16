from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.dtos.booking_dto import BookingCreateDTO
from src.exceptions.domain import (
    BookingAlreadyCancelled,
    BookingNotFound,
    SlotAlreadyBooked,
    SlotInPast,
    SlotNotFound,
)
from src.models.booking import BookingStatus
from src.models.slot import Slot
from src.repositories.booking_repository import BookingRepository
from src.repositories.slot_repository import SlotRepository
from src.services.booking_service import BookingService
from src.services.slot_service import SlotService


@pytest.fixture
def future_slot(db_session: Session) -> Slot:
    """Fixture providing a slot starting in the future."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = Slot(
        id="s-future",
        provider="Dr Ade",
        start=now + timedelta(days=2),
        end=now + timedelta(days=2, minutes=30),
    )
    return slot_repo.create(slot)


@pytest.fixture
def past_slot(db_session: Session) -> Slot:
    """Fixture providing a slot whose start time is already in the past."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = Slot(
        id="s-past",
        provider="Dr Ade",
        start=now - timedelta(hours=2),
        end=now - timedelta(hours=1, minutes=30),
    )
    return slot_repo.create(slot)


def test_create_booking_success(db_session: Session, future_slot: Slot):
    """Verify that a valid booking is successfully created with normalized fields."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    result = service.create_booking(
        slot_id=future_slot.id,
        name="  Ada Obi  ",
        email="  Ada.Obi@Example.COM  ",
    )

    assert result.id is not None
    assert result.slot_id == future_slot.id
    assert result.name == "Ada Obi"
    assert result.email == "ada.obi@example.com"
    assert result.status == BookingStatus.CONFIRMED.value
    assert result.created_at is not None


def test_create_booking_slot_not_found(db_session: Session):
    """Verify SlotNotFound is raised when attempting to book a non-existent slot."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    with pytest.raises(SlotNotFound):
        service.create_booking(
            slot_id="non-existent-slot",
            name="Ada Obi",
            email="ada@example.com",
        )


def test_create_booking_past_slot_rejected(db_session: Session, past_slot: Slot):
    """Verify SlotInPast is raised when attempting to book an appointment slot in the past."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    with pytest.raises(SlotInPast):
        service.create_booking(
            slot_id=past_slot.id,
            name="Ada Obi",
            email="ada@example.com",
        )


def test_create_booking_duplicate_prevention(db_session: Session, future_slot: Slot):
    """Verify SlotAlreadyBooked is raised when attempting to book an already confirmed slot."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    # First booking succeeds
    service.create_booking(
        slot_id=future_slot.id,
        name="Patient One",
        email="p1@example.com",
    )

    # Second booking for the same slot must fail
    with pytest.raises(SlotAlreadyBooked):
        service.create_booking(
            slot_id=future_slot.id,
            name="Patient Two",
            email="p2@example.com",
        )


def test_invalid_booking_data_validation():
    """Verify that BookingCreateDTO rejects empty names and invalid email formats."""
    # Empty name
    with pytest.raises(ValidationError):
        BookingCreateDTO(slot_id="s1", name="   ", email="test@example.com")

    # Invalid email
    with pytest.raises(ValidationError):
        BookingCreateDTO(slot_id="s1", name="Ada Obi", email="invalid-email-address")

    # Missing domain dot in email
    with pytest.raises(ValidationError):
        BookingCreateDTO(slot_id="s1", name="Ada Obi", email="ada@example")


def test_get_booking_success(db_session: Session, future_slot: Slot):
    """Verify retrieving an existing booking by its ID."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    created = service.create_booking(
        slot_id=future_slot.id,
        name="Ada Obi",
        email="ada@example.com",
    )

    fetched = service.get_booking(created.id)
    assert fetched.id == created.id
    assert fetched.slot_id == future_slot.id
    assert fetched.name == "Ada Obi"
    assert fetched.email == "ada@example.com"
    assert fetched.status == "confirmed"


def test_get_booking_not_found(db_session: Session):
    """Verify BookingNotFound is raised for a non-existent booking ID."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    with pytest.raises(BookingNotFound):
        service.get_booking("non-existent-booking-id")


def test_cancel_booking_success(db_session: Session, future_slot: Slot):
    """Verify cancelling an existing booking changes status to cancelled."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    booking_service = BookingService(booking_repo, slot_repo)
    slot_service = SlotService(slot_repo)

    created = booking_service.create_booking(
        slot_id=future_slot.id,
        name="Ada Obi",
        email="ada@example.com",
    )

    cancelled = booking_service.cancel_booking(created.id)
    assert cancelled.id == created.id
    assert cancelled.status == "cancelled"

    # Verify slot availability is restored
    slots = slot_service.list_slots()
    slot_result = next(s for s in slots if s.id == future_slot.id)
    assert slot_result.available is True


def test_cancel_booking_not_found(db_session: Session):
    """Verify BookingNotFound is raised when cancelling a non-existent booking."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    with pytest.raises(BookingNotFound):
        service.cancel_booking("non-existent-id")


def test_repeated_cancellation_rejected(db_session: Session, future_slot: Slot):
    """Verify BookingAlreadyCancelled is raised when attempting to cancel an already-cancelled booking."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    created = service.create_booking(
        slot_id=future_slot.id,
        name="Ada Obi",
        email="ada@example.com",
    )

    # First cancellation succeeds
    service.cancel_booking(created.id)

    # Second cancellation must fail with BookingAlreadyCancelled
    with pytest.raises(BookingAlreadyCancelled):
        service.cancel_booking(created.id)


def test_booking_again_after_cancellation(db_session: Session, future_slot: Slot):
    """Verify that a slot can be booked again after a previous booking was cancelled."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    # First patient books and then cancels
    b1 = service.create_booking(
        slot_id=future_slot.id,
        name="Patient One",
        email="p1@example.com",
    )
    service.cancel_booking(b1.id)

    # Second patient books the same slot — must succeed
    b2 = service.create_booking(
        slot_id=future_slot.id,
        name="Patient Two",
        email="p2@example.com",
    )
    assert b2.id != b1.id
    assert b2.slot_id == future_slot.id
    assert b2.status == "confirmed"

    # Both bookings exist in the database (history preserved)
    history = booking_repo.list_by_slot_id(future_slot.id)
    assert len(history) == 2
    assert history[0].status == "cancelled"
    assert history[1].status == "confirmed"


def test_create_booking_concurrency_race_condition(db_session: Session, future_slot: Slot, monkeypatch):
    """Verify that when a race condition bypasses application check, database IntegrityError raises SlotAlreadyBooked."""
    booking_repo = BookingRepository(db_session)
    slot_repo = SlotRepository(db_session)
    service = BookingService(booking_repo, slot_repo)

    # First booking
    service.create_booking(
        slot_id=future_slot.id,
        name="Patient One",
        email="p1@example.com",
    )

    # Monkeypatch get_confirmed_by_slot_id to return None (simulating two simultaneous requests reading 'available')
    monkeypatch.setattr(booking_repo, "get_confirmed_by_slot_id", lambda slot_id: None)

    # The database partial unique index will trigger IntegrityError, and service translates it to SlotAlreadyBooked
    with pytest.raises(SlotAlreadyBooked):
        service.create_booking(
            slot_id=future_slot.id,
            name="Patient Two",
            email="p2@example.com",
        )

