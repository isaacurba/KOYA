from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.booking import Booking, BookingStatus
from src.models.slot import Slot
from src.repositories.booking_repository import BookingRepository
from src.repositories.slot_repository import SlotRepository


@pytest.fixture
def sample_slot(db_session: Session) -> Slot:
    """Fixture providing a saved appointment slot for booking tests."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = Slot(
        id="slot-100",
        provider="Dr Ade",
        start=now + timedelta(hours=2),
        end=now + timedelta(hours=2, minutes=30),
    )
    return slot_repo.create(slot)


def test_create_and_get_booking(db_session: Session, sample_slot: Slot):
    """Verify that a booking can be persisted and retrieved by ID."""
    repo = BookingRepository(db_session)
    booking = Booking(
        id="book-1",
        slot_id=sample_slot.id,
        name="Ada Obi",
        email="ada@example.com",
        status=BookingStatus.CONFIRMED.value,
    )

    created = repo.create(booking)
    assert created.id == "book-1"
    assert created.slot_id == sample_slot.id
    assert created.name == "Ada Obi"
    assert created.email == "ada@example.com"
    assert created.status == "confirmed"
    assert created.created_at is not None

    fetched = repo.get_by_id("book-1")
    assert fetched is not None
    assert fetched.id == "book-1"
    assert fetched.name == "Ada Obi"
    assert fetched.email == "ada@example.com"
    assert fetched.status == "confirmed"


def test_get_by_id_not_found(db_session: Session):
    """Verify that get_by_id returns None for non-existent bookings."""
    repo = BookingRepository(db_session)
    result = repo.get_by_id("unknown-booking-id")
    assert result is None


def test_get_confirmed_by_slot_id(db_session: Session, sample_slot: Slot):
    """Verify retrieval of active confirmed booking for a slot."""
    repo = BookingRepository(db_session)

    # When no booking exists for the slot
    assert repo.get_confirmed_by_slot_id(sample_slot.id) is None

    # When confirmed booking exists
    booking = Booking(
        id="b-active",
        slot_id=sample_slot.id,
        name="Ada Obi",
        email="ada@example.com",
        status=BookingStatus.CONFIRMED.value,
    )
    repo.create(booking)

    confirmed = repo.get_confirmed_by_slot_id(sample_slot.id)
    assert confirmed is not None
    assert confirmed.id == "b-active"
    assert confirmed.status == "confirmed"


def test_get_confirmed_by_slot_id_ignores_cancelled(db_session: Session, sample_slot: Slot):
    """Verify that get_confirmed_by_slot_id returns None if the booking is cancelled."""
    repo = BookingRepository(db_session)
    booking = Booking(
        id="b-cancelled",
        slot_id=sample_slot.id,
        name="Ada Obi",
        email="ada@example.com",
        status=BookingStatus.CANCELLED.value,
    )
    repo.create(booking)

    confirmed = repo.get_confirmed_by_slot_id(sample_slot.id)
    assert confirmed is None


def test_update_status(db_session: Session, sample_slot: Slot):
    """Verify that a booking status can be updated and persisted."""
    repo = BookingRepository(db_session)
    booking = Booking(
        id="b-update",
        slot_id=sample_slot.id,
        name="Ada Obi",
        email="ada@example.com",
        status=BookingStatus.CONFIRMED.value,
    )
    repo.create(booking)

    # Update using enum
    updated = repo.update_status(booking, BookingStatus.CANCELLED)
    assert updated.status == "cancelled"

    refetched = repo.get_by_id("b-update")
    assert refetched is not None
    assert refetched.status == "cancelled"


def test_preserving_cancelled_booking_history(db_session: Session, sample_slot: Slot):
    """Verify that cancelling a booking preserves historical records and allows a new booking."""
    repo = BookingRepository(db_session)

    # First patient books
    booking_1 = Booking(
        id="b-first",
        slot_id=sample_slot.id,
        name="Patient One",
        email="p1@example.com",
        status=BookingStatus.CONFIRMED.value,
    )
    repo.create(booking_1)

    # Patient cancels
    repo.update_status(booking_1, BookingStatus.CANCELLED)

    # Second patient books the same slot
    booking_2 = Booking(
        id="b-second",
        slot_id=sample_slot.id,
        name="Patient Two",
        email="p2@example.com",
        status=BookingStatus.CONFIRMED.value,
    )
    repo.create(booking_2)

    # Verify both bookings exist in history
    history = repo.list_by_slot_id(sample_slot.id)
    assert len(history) == 2
    assert history[0].id == "b-first"
    assert history[0].status == "cancelled"
    assert history[1].id == "b-second"
    assert history[1].status == "confirmed"

    # Confirmed lookup returns only the active one
    confirmed = repo.get_confirmed_by_slot_id(sample_slot.id)
    assert confirmed is not None
    assert confirmed.id == "b-second"


def test_constraint_preventing_two_confirmed_bookings_for_same_slot(db_session: Session, sample_slot: Slot):
    """Verify database partial unique index prevents concurrent confirmed bookings for the same slot."""
    repo = BookingRepository(db_session)

    booking_1 = Booking(
        id="b-concurrent-1",
        slot_id=sample_slot.id,
        name="Patient One",
        email="p1@example.com",
        status=BookingStatus.CONFIRMED.value,
    )
    repo.create(booking_1)

    # Attempt to create a second confirmed booking for the same slot
    booking_2 = Booking(
        id="b-concurrent-2",
        slot_id=sample_slot.id,
        name="Patient Two",
        email="p2@example.com",
        status=BookingStatus.CONFIRMED.value,
    )

    with pytest.raises(IntegrityError):
        repo.create(booking_2)


def test_check_constraint_rejects_invalid_status(db_session: Session, sample_slot: Slot):
    """Verify database check constraint rejects statuses other than 'confirmed' or 'cancelled'."""
    repo = BookingRepository(db_session)

    invalid_booking = Booking(
        id="b-invalid",
        slot_id=sample_slot.id,
        name="Patient Invalid",
        email="invalid@example.com",
        status="pending",  # Invalid status not in ('confirmed', 'cancelled')
    )

    with pytest.raises(IntegrityError):
        repo.create(invalid_booking)
