from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from src.models.booking import Booking, BookingStatus
from src.models.slot import Slot
from src.repositories.slot_repository import SlotRepository


def test_list_slots_unauthenticated(client: TestClient):
    """Verify that GET /slots without X-API-Key returns 401 Unauthorized."""
    response = client.get("/slots")
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


def test_list_slots_invalid_key(client: TestClient):
    """Verify that GET /slots with an invalid X-API-Key returns 401 Unauthorized."""
    response = client.get("/slots", headers={"X-API-Key": "incorrect-key"})
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


def test_list_slots_empty(client: TestClient, auth_headers: dict[str, str]):
    """Verify that GET /slots returns an empty list when no slots exist."""
    response = client.get("/slots", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "slots" in data
    assert data["slots"] == []


def test_list_slots_with_availability(client: TestClient, auth_headers: dict[str, str], db_session):
    """Verify GET /slots returns chronologically ordered slots with dynamic availability."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)

    s1 = slot_repo.create(Slot(id="s1", provider="Dr Ade", start=now + timedelta(days=1), end=now + timedelta(days=1, minutes=30)))
    s2 = slot_repo.create(Slot(id="s2", provider="Dr Ade", start=now + timedelta(days=2), end=now + timedelta(days=2, minutes=30)))

    # Book s1
    booking = Booking(id="b1", slot_id="s1", name="Patient One", email="p1@example.com", status=BookingStatus.CONFIRMED.value)
    db_session.add(booking)
    db_session.commit()

    response = client.get("/slots", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    slots = data["slots"]
    assert len(slots) == 2
    assert slots[0]["id"] == "s1"
    assert slots[0]["available"] is False
    assert slots[1]["id"] == "s2"
    assert slots[1]["available"] is True


def test_list_slots_filter_by_provider(client: TestClient, auth_headers: dict[str, str], db_session):
    """Verify GET /slots?provider=... filters slots by the provider name."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)

    slot_repo.create(Slot(id="s1", provider="Dr Ade", start=now + timedelta(days=1), end=now + timedelta(days=1, minutes=30)))
    slot_repo.create(Slot(id="s2", provider="Dr Ngozi", start=now + timedelta(days=2), end=now + timedelta(days=2, minutes=30)))

    response = client.get("/slots?provider=Dr%20Ade", headers=auth_headers)
    assert response.status_code == 200
    slots = response.json()["slots"]
    assert len(slots) == 1
    assert slots[0]["id"] == "s1"
    assert slots[0]["provider"] == "Dr Ade"


def test_reset_slots_unauthenticated(client: TestClient):
    """Verify that POST /reset without API key returns 401."""
    payload = {"slots": []}
    response = client.post("/reset", json=payload)
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


def test_reset_slots_success(client: TestClient, auth_headers: dict[str, str], db_session):
    """Verify that POST /reset replaces slots and returns 200."""
    now = datetime.now(timezone.utc)
    start_time = (now + timedelta(days=1)).isoformat()
    end_time = (now + timedelta(days=1, minutes=30)).isoformat()

    payload = {
        "slots": [
            {
                "id": "s-new",
                "provider": "Dr Ade",
                "start": start_time,
                "end": end_time,
            }
        ]
    }

    response = client.post("/reset", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Slots reset successfully"
    assert data["count"] == 1

    # Verify via GET /slots
    get_res = client.get("/slots", headers=auth_headers)
    assert get_res.status_code == 200
    slots = get_res.json()["slots"]
    assert len(slots) == 1
    assert slots[0]["id"] == "s-new"
    assert slots[0]["available"] is True


def test_reset_slots_invalid_payload(client: TestClient, auth_headers: dict[str, str]):
    """Verify that POST /reset with invalid payload returns 400 with standard error format."""
    # start after end
    now = datetime.now(timezone.utc)
    payload = {
        "slots": [
            {
                "id": "s-bad",
                "provider": "Dr Ade",
                "start": (now + timedelta(hours=2)).isoformat(),
                "end": (now + timedelta(hours=1)).isoformat(),
            }
        ]
    }
    response = client.post("/reset", json=payload, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "start time must be before end time" in data["error"]
