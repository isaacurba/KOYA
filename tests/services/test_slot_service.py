from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from src.dtos.slot_dto import ResetSlotsRequestDTO, SlotCreateDTO
from src.models.booking import Booking, BookingStatus
from src.models.slot import Slot
from src.repositories.slot_repository import SlotRepository
from src.services.slot_service import SlotService


def test_list_slots_empty(db_session: Session):
    """Verify list_slots returns an empty list when no slots exist."""
    slot_repo = SlotRepository(db_session)
    service = SlotService(slot_repo)
    slots = service.list_slots()
    assert slots == []


def test_list_slots_all_available_without_bookings(db_session: Session):
    """Verify slots without bookings are marked as available."""
    slot_repo = SlotRepository(db_session)
    service = SlotService(slot_repo)
    base_time = datetime.now(timezone.utc) + timedelta(days=1)

    slot_repo.create(Slot(id="s1", provider="Dr Ade", start=base_time, end=base_time + timedelta(minutes=30)))
    slot_repo.create(Slot(id="s2", provider="Dr Ngozi", start=base_time + timedelta(hours=1), end=base_time + timedelta(hours=1, minutes=30)))

    results = service.list_slots()
    assert len(results) == 2
    assert results[0].available is True
    assert results[1].available is True


def test_list_slots_unavailable_when_confirmed_booking_exists(db_session: Session):
    """Verify that a confirmed booking makes a slot unavailable."""
    slot_repo = SlotRepository(db_session)
    service = SlotService(slot_repo)
    base_time = datetime.now(timezone.utc) + timedelta(days=1)

    s1 = slot_repo.create(Slot(id="s1", provider="Dr Ade", start=base_time, end=base_time + timedelta(minutes=30)))
    s2 = slot_repo.create(Slot(id="s2", provider="Dr Ade", start=base_time + timedelta(hours=1), end=base_time + timedelta(hours=1, minutes=30)))

    # Book s1
    booking = Booking(
        id="b1",
        slot_id=s1.id,
        name="Ada Obi",
        email="ada@example.com",
        status=BookingStatus.CONFIRMED.value,
    )
    db_session.add(booking)
    db_session.commit()

    results = service.list_slots()
    assert len(results) == 2

    s1_result = next(s for s in results if s.id == "s1")
    s2_result = next(s for s in results if s.id == "s2")
    assert s1_result.available is False
    assert s2_result.available is True


def test_list_slots_cancelled_booking_leaves_slot_available(db_session: Session):
    """Verify that a cancelled booking does not mark a slot as unavailable."""
    slot_repo = SlotRepository(db_session)
    service = SlotService(slot_repo)
    base_time = datetime.now(timezone.utc) + timedelta(days=1)

    s1 = slot_repo.create(Slot(id="s1", provider="Dr Ade", start=base_time, end=base_time + timedelta(minutes=30)))

    # Cancelled booking on s1
    cancelled_booking = Booking(
        id="b-cancelled",
        slot_id=s1.id,
        name="Ada Obi",
        email="ada@example.com",
        status=BookingStatus.CANCELLED.value,
    )
    db_session.add(cancelled_booking)
    db_session.commit()

    results = service.list_slots()
    assert len(results) == 1
    assert results[0].id == "s1"
    assert results[0].available is True


def test_list_slots_chronological_ordering(db_session: Session):
    """Verify that slots are listed in ascending start-time order."""
    slot_repo = SlotRepository(db_session)
    service = SlotService(slot_repo)
    base = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)

    # Insert out of order
    slot_repo.create(Slot(id="s3", provider="Dr Ade", start=base + timedelta(hours=3), end=base + timedelta(hours=3, minutes=30)))
    slot_repo.create(Slot(id="s1", provider="Dr Ade", start=base + timedelta(hours=1), end=base + timedelta(hours=1, minutes=30)))
    slot_repo.create(Slot(id="s2", provider="Dr Ade", start=base + timedelta(hours=2), end=base + timedelta(hours=2, minutes=30)))

    results = service.list_slots()
    assert [s.id for s in results] == ["s1", "s2", "s3"]
    assert results[0].start < results[1].start < results[2].start


def test_list_slots_filter_by_provider(db_session: Session):
    """Verify listing slots filtered by provider."""
    slot_repo = SlotRepository(db_session)
    service = SlotService(slot_repo)
    base = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)

    slot_repo.create(Slot(id="s1", provider="Dr Ade", start=base, end=base + timedelta(minutes=30)))
    slot_repo.create(Slot(id="s2", provider="Dr Ngozi", start=base + timedelta(hours=1), end=base + timedelta(hours=1, minutes=30)))

    ade_slots = service.list_slots(provider="Dr Ade")
    assert len(ade_slots) == 1
    assert ade_slots[0].id == "s1"

    ngozi_slots = service.list_slots(provider="Dr Ngozi")
    assert len(ngozi_slots) == 1
    assert ngozi_slots[0].id == "s2"


def test_reset_slots_transactional_replacement(db_session: Session):
    """Verify reset_slots removes old slots and bookings, inserting new ones."""
    slot_repo = SlotRepository(db_session)
    service = SlotService(slot_repo)
    base = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)

    # Existing slot and booking
    old_slot = slot_repo.create(Slot(id="old-s", provider="Dr Old", start=base, end=base + timedelta(minutes=30)))
    old_booking = Booking(id="old-b", slot_id="old-s", name="Old Patient", email="old@example.com", status="confirmed")
    db_session.add(old_booking)
    db_session.commit()

    # Reset with new slots
    new_start_1 = base + timedelta(days=2)
    new_start_2 = base + timedelta(days=3)
    reset_dto = ResetSlotsRequestDTO(
        slots=[
            SlotCreateDTO(id="new-1", provider="Dr New", start=new_start_1, end=new_start_1 + timedelta(minutes=30)),
            SlotCreateDTO(id="new-2", provider="Dr New", start=new_start_2, end=new_start_2 + timedelta(minutes=30)),
        ]
    )

    reset_result = service.reset_slots(reset_dto)
    assert len(reset_result) == 2
    assert {s.id for s in reset_result} == {"new-1", "new-2"}
    assert all(s.available is True for s in reset_result)

    # Old slot and booking should be gone
    assert slot_repo.get_by_id("old-s") is None
    assert db_session.get(Booking, "old-b") is None
