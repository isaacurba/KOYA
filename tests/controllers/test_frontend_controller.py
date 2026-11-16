from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient

from src.config.settings import get_settings
from src.models.slot import Slot
from src.repositories.slot_repository import SlotRepository


def test_serve_frontend_index(client: TestClient):
    """Verify that GET / serves the frontend HTML page successfully without authentication."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "CarePoint Clinic" in response.text
    assert "<form id=\"booking-form\"" in response.text


def test_serve_frontend_app(client: TestClient):
    """Verify that GET /app also serves the patient interface."""
    response = client.get("/app")
    assert response.status_code == 200
    assert "CarePoint Clinic" in response.text


def test_serve_static_assets(client: TestClient):
    """Verify that static CSS and JavaScript assets load successfully."""
    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    assert "--primary" in css_res.text

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "DOMContentLoaded" in js_res.text


def test_no_api_key_leakage_in_frontend_assets():
    """Verify the secret API key is never exposed or hardcoded in any frontend static asset."""
    settings = get_settings()
    static_dir = Path(__file__).resolve().parents[2] / "src" / "static"

    for file_path in static_dir.glob("*"):
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8")
            assert settings.API_KEY not in content, f"API Key leaked in {file_path.name}"
            # Ensure browser code does not send X-API-Key header
            assert "X-API-Key" not in content, f"X-API-Key header referenced in {file_path.name}"


def test_frontend_list_slots_without_api_key(client: TestClient, db_session):
    """Verify GET /frontend-api/slots succeeds without requiring an X-API-Key header."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot_repo.create(Slot(id="s-fe-1", provider="Dr Ade", start=now + timedelta(days=1), end=now + timedelta(days=1, minutes=30)))

    response = client.get("/frontend-api/slots")
    assert response.status_code == 200
    data = response.json()
    assert "slots" in data
    assert len(data["slots"]) == 1
    assert data["slots"][0]["id"] == "s-fe-1"
    assert data["slots"][0]["available"] is True


def test_frontend_list_slots_provider_filter(client: TestClient, db_session):
    """Verify provider filtering works through the frontend BFF route."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot_repo.create(Slot(id="s1", provider="Dr Ade", start=now + timedelta(days=1), end=now + timedelta(days=1, minutes=30)))
    slot_repo.create(Slot(id="s2", provider="Dr Ngozi", start=now + timedelta(days=2), end=now + timedelta(days=2, minutes=30)))

    response = client.get("/frontend-api/slots?provider=Dr%20Ngozi")
    assert response.status_code == 200
    slots = response.json()["slots"]
    assert len(slots) == 1
    assert slots[0]["id"] == "s2"
    assert slots[0]["provider"] == "Dr Ngozi"


def test_frontend_create_booking_success(client: TestClient, db_session):
    """Verify creating a booking via POST /frontend-api/bookings without API key."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = slot_repo.create(Slot(id="s-book", provider="Dr Ade", start=now + timedelta(days=1), end=now + timedelta(days=1, minutes=30)))

    payload = {"slot_id": slot.id, "name": "Ada Obi", "email": "ada@example.com"}
    response = client.post("/frontend-api/bookings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["slot_id"] == slot.id
    assert data["name"] == "Ada Obi"
    assert data["email"] == "ada@example.com"
    assert data["status"] == "confirmed"


def test_frontend_create_booking_validation_error(client: TestClient):
    """Verify invalid booking data returns 400 with consistent error structure."""
    payload = {"slot_id": "s1", "name": "  ", "email": "not-an-email"}
    response = client.post("/frontend-api/bookings", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()


def test_frontend_create_booking_conflict(client: TestClient, db_session):
    """Verify duplicate booking via BFF route returns 409 conflict."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = slot_repo.create(Slot(id="s-conflict", provider="Dr Ade", start=now + timedelta(days=1), end=now + timedelta(days=1, minutes=30)))

    payload1 = {"slot_id": slot.id, "name": "Patient 1", "email": "p1@example.com"}
    res1 = client.post("/frontend-api/bookings", json=payload1)
    assert res1.status_code == 201

    payload2 = {"slot_id": slot.id, "name": "Patient 2", "email": "p2@example.com"}
    res2 = client.post("/frontend-api/bookings", json=payload2)
    assert res2.status_code == 409
    assert "already booked" in res2.json()["error"]


def test_frontend_get_and_cancel_booking(client: TestClient, db_session):
    """Verify looking up and cancelling a booking via frontend routes."""
    slot_repo = SlotRepository(db_session)
    now = datetime.now(timezone.utc)
    slot = slot_repo.create(Slot(id="s-cancel", provider="Dr Ade", start=now + timedelta(days=1), end=now + timedelta(days=1, minutes=30)))

    # Book
    create_res = client.post("/frontend-api/bookings", json={"slot_id": slot.id, "name": "Ada", "email": "ada@example.com"})
    booking_id = create_res.json()["id"]

    # Lookup
    get_res = client.get(f"/frontend-api/bookings/{booking_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == booking_id
    assert get_res.json()["status"] == "confirmed"

    # Cancel
    cancel_res = client.delete(f"/frontend-api/bookings/{booking_id}")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Verify slot is available again
    slots_res = client.get("/frontend-api/slots")
    slot_data = next(s for s in slots_res.json()["slots"] if s["id"] == slot.id)
    assert slot_data["available"] is True

    # Repeated cancellation gives 409
    repeat_res = client.delete(f"/frontend-api/bookings/{booking_id}")
    assert repeat_res.status_code == 409
    assert "already been cancelled" in repeat_res.json()["error"]


def test_assessment_endpoints_strictly_require_api_key(client: TestClient):
    """Verify that core assessment endpoints continue enforcing X-API-Key."""
    assert client.get("/slots").status_code == 401
    assert client.post("/bookings", json={}).status_code == 401
    assert client.delete("/bookings/123").status_code == 401
    assert client.post("/reset", json={"slots": []}).status_code == 401


def test_no_public_frontend_reset_route(client: TestClient):
    """Verify that there is no public frontend reset route exposed."""
    response = client.post("/frontend-api/reset", json={})
    assert response.status_code in (404, 405)
