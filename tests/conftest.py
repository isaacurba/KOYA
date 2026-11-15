from typing import AsyncGenerator
import pytest
import pytest_asyncio
import httpx
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Synchronous test client fixture."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Asynchronous HTTPX test client fixture using ASGI transport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
