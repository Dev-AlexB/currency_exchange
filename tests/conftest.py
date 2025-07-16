import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def sync_client():
    return TestClient(app)


@pytest_asyncio.fixture(scope="session")
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client
