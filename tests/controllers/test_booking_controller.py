from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from src.models.slot import Slot
from src.repositories.slot_repository import SlotRepository


@pytest.fixture
def available_slot(db_session) -> Slot:
    """Fixture creating an available slot in the future."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = Slot(
        id="s-test-1",
        provider="Dr Ade",
        start=now + timedelta(days=2),
        end=now + timedelta(days=2, minutes=30),
    )
    return slot_repo.create(slot)


@pytest.fixture
def past_slot(db_session) -> Slot:
    """Fixture creating a slot whose start time is in the past."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = Slot(
        id="s-past-1",
        provider="Dr Ade",
        start=now - timedelta(hours=2),
        end=now - timedelta(hours=1, minutes=30),
    )
    return slot_repo.create(slot)


# --- Authentication Tests ---


def test_create_booking_unauthenticated(client: TestClient):
    """Verify POST /bookings without API key returns 401."""
    response = client.post("/bookings", json={"slot_id": "s1", "name": "Ada", "email": "ada@example.com"})
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


def test_get_booking_unauthenticated(client: TestClient):
    """Verify GET /bookings/{id} without API key returns 401."""
    response = client.get("/bookings/booking-123")
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


def test_cancel_booking_unauthenticated(client: TestClient):
    """Verify DELETE /bookings/{id} without API key returns 401."""
    response = client.delete("/bookings/booking-123")
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


# --- POST /bookings Tests ---


def test_create_booking_success(client: TestClient, auth_headers: dict[str, str], available_slot: Slot):
    """Verify POST /bookings creates a booking and returns 201 Created with normalized fields."""
    payload = {
        "slot_id": available_slot.id,
        "name": "  Ada Obi  ",
        "email": "  Ada.Obi@Example.COM  ",
    }
    response = client.post("/bookings", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["slot_id"] == available_slot.id
    assert data["name"] == "Ada Obi"
    assert data["email"] == "ada.obi@example.com"
    assert data["status"] == "confirmed"
    assert "created_at" in data


def test_create_booking_invalid_input(client: TestClient, auth_headers: dict[str, str], available_slot: Slot):
    """Verify POST /bookings with invalid email or empty name returns 400 Bad Request."""
    # Bad email
    payload_bad_email = {"slot_id": available_slot.id, "name": "Ada Obi", "email": "invalid-email"}
    res1 = client.post("/bookings", json=payload_bad_email, headers=auth_headers)
    assert res1.status_code == 400
    assert "error" in res1.json()

    # Empty name
    payload_empty_name = {"slot_id": available_slot.id, "name": "   ", "email": "ada@example.com"}
    res2 = client.post("/bookings", json=payload_empty_name, headers=auth_headers)
    assert res2.status_code == 400
    assert "error" in res2.json()


def test_create_booking_slot_not_found(client: TestClient, auth_headers: dict[str, str]):
    """Verify POST /bookings for non-existent slot returns 404 Not Found."""
    payload = {"slot_id": "non-existent-slot", "name": "Ada Obi", "email": "ada@example.com"}
    response = client.post("/bookings", json=payload, headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"error": "Appointment slot 'non-existent-slot' does not exist."}


def test_create_booking_past_slot_rejected(client: TestClient, auth_headers: dict[str, str], past_slot: Slot):
    """Verify POST /bookings for a slot whose start time has passed returns 400 Bad Request."""
    payload = {"slot_id": past_slot.id, "name": "Ada Obi", "email": "ada@example.com"}
    response = client.post("/bookings", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert response.json() == {"error": f"Cannot book appointment slot '{past_slot.id}' because it has already started."}


def test_create_booking_duplicate_conflict(client: TestClient, auth_headers: dict[str, str], available_slot: Slot):
    """Verify POST /bookings for an already booked slot returns 409 Conflict."""
    payload1 = {"slot_id": available_slot.id, "name": "Patient One", "email": "p1@example.com"}
    res1 = client.post("/bookings", json=payload1, headers=auth_headers)
    assert res1.status_code == 201

    payload2 = {"slot_id": available_slot.id, "name": "Patient Two", "email": "p2@example.com"}
    res2 = client.post("/bookings", json=payload2, headers=auth_headers)
    assert res2.status_code == 409
    response_error = res2.json().get("error", "")
    assert "already booked" in response_error


# --- GET /bookings/{id} Tests ---


def test_get_booking_success(client: TestClient, auth_headers: dict[str, str], available_slot: Slot):
    """Verify GET /bookings/{id} returns 200 OK with booking details."""
    create_res = client.post(
        "/bookings",
        json={"slot_id": available_slot.id, "name": "Ada Obi", "email": "ada@example.com"},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    get_res = client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == booking_id
    assert data["slot_id"] == available_slot.id
    assert data["name"] == "Ada Obi"
    assert data["email"] == "ada@example.com"
    assert data["status"] == "confirmed"


def test_get_booking_not_found(client: TestClient, auth_headers: dict[str, str]):
    """Verify GET /bookings/{id} for non-existent ID returns 404 Not Found."""
    response = client.get("/bookings/missing-id-123", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"error": "Booking with id 'missing-id-123' does not exist."}


# --- DELETE /bookings/{id} Tests ---


def test_cancel_booking_success(client: TestClient, auth_headers: dict[str, str], available_slot: Slot):
    """Verify DELETE /bookings/{id} cancels booking, returns 200, and restores slot availability."""
    create_res = client.post(
        "/bookings",
        json={"slot_id": available_slot.id, "name": "Ada Obi", "email": "ada@example.com"},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Slot should now be unavailable
    slots_res1 = client.get("/slots", headers=auth_headers)
    slot1 = next(s for s in slots_res1.json()["slots"] if s["id"] == available_slot.id)
    assert slot1["available"] is False

    # Cancel booking
    del_res = client.delete(f"/bookings/{booking_id}", headers=auth_headers)
    assert del_res.status_code == 200
    data = del_res.json()
    assert data["id"] == booking_id
    assert data["status"] == "cancelled"

    # Slot should now be available again
    slots_res2 = client.get("/slots", headers=auth_headers)
    slot2 = next(s for s in slots_res2.json()["slots"] if s["id"] == available_slot.id)
    assert slot2["available"] is True


def test_cancel_booking_not_found(client: TestClient, auth_headers: dict[str, str]):
    """Verify DELETE /bookings/{id} for non-existent ID returns 404 Not Found."""
    response = client.delete("/bookings/non-existent-booking", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"error": "Booking with id 'non-existent-booking' does not exist."}


def test_cancel_already_cancelled_booking_conflict(client: TestClient, auth_headers: dict[str, str], available_slot: Slot):
    """Verify DELETE /bookings/{id} on an already cancelled booking returns 409 Conflict."""
    create_res = client.post(
        "/bookings",
        json={"slot_id": available_slot.id, "name": "Ada Obi", "email": "ada@example.com"},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # First cancel succeeds
    del1 = client.delete(f"/bookings/{booking_id}", headers=auth_headers)
    assert del1.status_code == 200

    # Second cancel must fail with 409
    del2 = client.delete(f"/bookings/{booking_id}", headers=auth_headers)
    assert del2.status_code == 409
    assert "already been cancelled" in del2.json()["error"]


def test_rebook_slot_after_cancellation(client: TestClient, auth_headers: dict[str, str], available_slot: Slot):
    """Verify that after a booking is cancelled, a new patient can book the same slot."""
    # Patient 1 books
    res1 = client.post(
        "/bookings",
        json={"slot_id": available_slot.id, "name": "Patient One", "email": "p1@example.com"},
        headers=auth_headers,
    )
    b1_id = res1.json()["id"]

    # Patient 1 cancels
    client.delete(f"/bookings/{b1_id}", headers=auth_headers)

    # Patient 2 books the same slot — must succeed with 201
    res2 = client.post(
        "/bookings",
        json={"slot_id": available_slot.id, "name": "Patient Two", "email": "p2@example.com"},
        headers=auth_headers,
    )
    assert res2.status_code == 201
    data = res2.json()
    assert data["id"] != b1_id
    assert data["slot_id"] == available_slot.id
    assert data["name"] == "Patient Two"
    assert data["status"] == "confirmed"
