from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from src.models.booking import Booking, BookingStatus
from src.models.slot import Slot
from src.repositories.slot_repository import SlotRepository


def test_create_and_get_slot(db_session: Session):
    """Verify that a slot can be created and retrieved by its ID."""
    repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = Slot(
        id="s1",
        provider="Dr Ade",
        start=now + timedelta(hours=1),
        end=now + timedelta(hours=1, minutes=30),
    )

    created = repo.create(slot)
    assert created.id == "s1"
    assert created.provider == "Dr Ade"

    fetched = repo.get_by_id("s1")
    assert fetched is not None
    assert fetched.id == "s1"
    assert fetched.provider == "Dr Ade"
    assert fetched.start == slot.start
    assert fetched.end == slot.end


def test_get_by_id_not_found(db_session: Session):
    """Verify that get_by_id returns None when a slot does not exist."""
    repo = SlotRepository(db_session)
    result = repo.get_by_id("non-existent-id")
    assert result is None


def test_list_all_chronological_order(db_session: Session):
    """Verify that slots are listed in ascending order of their start times."""
    repo = SlotRepository(db_session)
    base_time = datetime(2026, 12, 10, 8, 0, tzinfo=timezone.utc)

    # Insert slots out of chronological order
    s3 = Slot(id="s3", provider="Dr Ade", start=base_time + timedelta(hours=3), end=base_time + timedelta(hours=3, minutes=30))
    s1 = Slot(id="s1", provider="Dr Ade", start=base_time + timedelta(hours=1), end=base_time + timedelta(hours=1, minutes=30))
    s2 = Slot(id="s2", provider="Dr Ade", start=base_time + timedelta(hours=2), end=base_time + timedelta(hours=2, minutes=30))

    repo.create(s3)
    repo.create(s1)
    repo.create(s2)

    slots = repo.list_all()
    assert len(slots) == 3
    assert [s.id for s in slots] == ["s1", "s2", "s3"]
    assert slots[0].start < slots[1].start < slots[2].start


def test_list_all_filter_by_provider(db_session: Session):
    """Verify that listing slots can be filtered by healthcare provider."""
    repo = SlotRepository(db_session)
    base_time = datetime(2026, 12, 10, 9, 0, tzinfo=timezone.utc)

    s1 = Slot(id="s1", provider="Dr Ade", start=base_time, end=base_time + timedelta(minutes=30))
    s2 = Slot(id="s2", provider="Dr Ngozi", start=base_time + timedelta(hours=1), end=base_time + timedelta(hours=1, minutes=30))
    s3 = Slot(id="s3", provider="Dr Ade", start=base_time + timedelta(hours=2), end=base_time + timedelta(hours=2, minutes=30))

    repo.create(s1)
    repo.create(s2)
    repo.create(s3)

    ade_slots = repo.list_all(provider="Dr Ade")
    assert len(ade_slots) == 2
    assert {s.id for s in ade_slots} == {"s1", "s3"}

    ngozi_slots = repo.list_all(provider="Dr Ngozi")
    assert len(ngozi_slots) == 1
    assert ngozi_slots[0].id == "s2"

    unknown_slots = repo.list_all(provider="Dr NonExistent")
    assert len(unknown_slots) == 0


def test_list_all_empty(db_session: Session):
    """Verify that list_all returns an empty sequence when no slots exist."""
    repo = SlotRepository(db_session)
    slots = repo.list_all()
    assert len(slots) == 0


def test_reset_slots(db_session: Session):
    """Verify that reset_slots replaces all existing slots and cleans up past bookings."""
    repo = SlotRepository(db_session)
    base_time = datetime(2026, 12, 10, 9, 0, tzinfo=timezone.utc)

    # Initial slots and a booking
    old_slot = Slot(id="old-s1", provider="Dr Old", start=base_time, end=base_time + timedelta(minutes=30))
    repo.create(old_slot)

    old_booking = Booking(
        id="old-b1",
        slot_id="old-s1",
        name="Ada Obi",
        email="ada@example.com",
        status=BookingStatus.CONFIRMED.value,
    )
    db_session.add(old_booking)
    db_session.commit()

    # Reset with new slots
    new_s1 = Slot(id="new-s1", provider="Dr New", start=base_time + timedelta(days=1), end=base_time + timedelta(days=1, minutes=30))
    new_s2 = Slot(id="new-s2", provider="Dr New", start=base_time + timedelta(days=2), end=base_time + timedelta(days=2, minutes=30))

    result = repo.reset_slots([new_s1, new_s2])
    assert len(result) == 2

    # Old slot should no longer exist
    assert repo.get_by_id("old-s1") is None
    # Old booking should no longer exist
    assert db_session.get(Booking, "old-b1") is None

    # New slots should be present
    all_slots = repo.list_all()
    assert len(all_slots) == 2
    assert [s.id for s in all_slots] == ["new-s1", "new-s2"]


def test_reset_slots_to_empty(db_session: Session):
    """Verify resetting with an empty list clears all slots."""
    repo = SlotRepository(db_session)
    base_time = datetime(2026, 12, 10, 9, 0, tzinfo=timezone.utc)

    s1 = Slot(id="s1", provider="Dr Ade", start=base_time, end=base_time + timedelta(minutes=30))
    repo.create(s1)

    result = repo.reset_slots([])
    assert len(result) == 0
    assert len(repo.list_all()) == 0
