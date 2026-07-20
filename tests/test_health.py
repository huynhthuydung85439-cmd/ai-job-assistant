import httpx
import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints.health import health_check
from app.core.config import Settings
from app.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "rag_enabled": True,
    }


@pytest.mark.asyncio
async def test_health_check_reports_database_and_disabled_rag() -> None:
    class UnavailableDatabaseSession:
        async def execute(self, _statement):
            raise SQLAlchemyError("database unavailable")

    response = await health_check(
        UnavailableDatabaseSession(),
        Settings(_env_file=None, rag_enabled=False),
    )

    assert response.model_dump() == {
        "status": "degraded",
        "database": "unavailable",
        "rag_enabled": False,
    }
