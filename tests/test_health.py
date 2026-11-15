import pytest
import httpx
from fastapi.testclient import TestClient


def test_health_check_sync(client: TestClient):
    """Verify application boots and responds to synchronous requests."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Clinic Booking API"


@pytest.mark.asyncio
async def test_health_check_async(async_client: httpx.AsyncClient):
    """Verify application responds via async HTTPX client."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Clinic Booking API"
