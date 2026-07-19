from collections.abc import AsyncIterator
from io import BytesIO

import httpx
import pytest
import pytest_asyncio
from pydantic import SecretStr
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models import AnalysisRecord, ChatHistory, Resume, User
from app.rag.rag_service import get_rag_service
from app.schemas.resume import ResumeAnalysisResponse
from app.services.chat import get_chat_service
from app.services.resume_analyzer import get_resume_analyzer_service


class SuccessfulChatService:
    async def chat(self, message: str) -> str:
        return f"AI answer: {message}"


class SuccessfulResumeAnalyzer:
    async def analyze(
        self,
        resume_text: str,
        job_description: str,
    ) -> ResumeAnalysisResponse:
        return ResumeAnalysisResponse(
            score=88,
            matching_skills=["Python"],
            missing_skills=["Kubernetes"],
            resume_advices=["Add measurable outcomes"],
            interview_questions=["How do you scale an API?"],
        )


class SuccessfulRAGService:
    async def answer(self, question: str, user_id: int) -> tuple[str, list[str]]:
        assert user_id > 0
        return f"RAG answer: {question}", ["jd.pdf"]


def create_pdf(text: str = "Python FastAPI experience") -> bytes:
    output = BytesIO()
    document = canvas.Canvas(output)
    document.drawString(72, 750, text)
    document.showPage()
    document.save()
    return output.getvalue()


@pytest_asyncio.fixture
async def database_client() -> AsyncIterator[
    tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]]
]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    test_settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite://",
        jwt_secret_key=SecretStr("test-only-jwt-secret-at-least-32-characters"),
        bcrypt_rounds=4,
    )
    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    app.dependency_overrides.pop(get_db_session, None)
    app.dependency_overrides.pop(get_settings, None)
    app.dependency_overrides.pop(get_chat_service, None)
    app.dependency_overrides.pop(get_resume_analyzer_service, None)
    app.dependency_overrides.pop(get_rag_service, None)
    await engine.dispose()


async def register_and_login(client: httpx.AsyncClient) -> tuple[int, str]:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secure-password",
        },
    )
    assert register_response.status_code == 201
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "secure-password"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    return body["user_id"], body["token"]


@pytest.mark.asyncio
async def test_register_login_and_password_hashing(database_client) -> None:
    client, session_factory = database_client
    user_id, token = await register_and_login(client)

    assert user_id > 0
    assert token.count(".") == 2
    async with session_factory() as session:
        user = await session.get(User, user_id)
        assert user is not None
        assert user.password_hash != "secure-password"
        assert user.password_hash.startswith("$2")

    duplicate_response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "another@example.com",
            "password": "secure-password",
        },
    )
    assert duplicate_response.status_code == 409

    failed_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "wrong-password"},
    )
    assert failed_login.status_code == 401
    assert failed_login.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_authenticated_resume_and_analysis_are_persisted(database_client) -> None:
    client, session_factory = database_client
    user_id, token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    upload_response = await client.post(
        "/api/v1/resume/upload",
        files={"file": ("resume.pdf", create_pdf(), "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200
    resume_id = upload_response.json()["resume_id"]

    app.dependency_overrides[get_resume_analyzer_service] = SuccessfulResumeAnalyzer
    analysis_response = await client.post(
        "/api/v1/resume/analyze",
        json={
            "resume_id": resume_id,
            "resume_text": upload_response.json()["text"],
            "job_description": "Python role requiring Kubernetes",
        },
        headers=headers,
    )
    assert analysis_response.status_code == 200

    async with session_factory() as session:
        resume = await session.get(Resume, resume_id)
        record = await session.scalar(
            select(AnalysisRecord).where(AnalysisRecord.resume_id == resume_id)
        )
        assert resume is not None
        assert resume.user_id == user_id
        assert resume.filename == "resume.pdf"
        assert "Python FastAPI" in resume.content
        assert record is not None
        assert record.score == 88
        assert record.job_description == "Python role requiring Kubernetes"
        assert record.result_json["missing_skills"] == ["Kubernetes"]


@pytest.mark.asyncio
async def test_authenticated_chat_is_persisted_and_anonymous_chat_still_works(
    database_client,
) -> None:
    client, session_factory = database_client
    user_id, token = await register_and_login(client)
    app.dependency_overrides[get_chat_service] = SuccessfulChatService

    authenticated = await client.post(
        "/api/v1/chat",
        json={"message": "Analyze this role"},
        headers={"Authorization": f"Bearer {token}"},
    )
    anonymous = await client.post(
        "/api/v1/chat",
        json={"message": "Anonymous question"},
    )

    assert authenticated.status_code == 200
    assert anonymous.status_code == 200
    async with session_factory() as session:
        histories = (
            await session.scalars(
                select(ChatHistory).where(ChatHistory.user_id == user_id)
            )
        ).all()
        assert len(histories) == 1
        assert histories[0].question == "Analyze this role"
        assert histories[0].answer == "AI answer: Analyze this role"
        assert histories[0].chat_type == "chat"


@pytest.mark.asyncio
async def test_authenticated_rag_chat_is_persisted(database_client) -> None:
    client, session_factory = database_client
    user_id, token = await register_and_login(client)
    app.dependency_overrides[get_rag_service] = SuccessfulRAGService

    response = await client.post(
        "/api/v1/knowledge/chat",
        json={"question": "What skills are required?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["sources"] == ["jd.pdf"]
    async with session_factory() as session:
        histories = (
            await session.scalars(
                select(ChatHistory).where(ChatHistory.user_id == user_id)
            )
        ).all()
        assert len(histories) == 1
        assert histories[0].question == "What skills are required?"
        assert histories[0].answer == "RAG answer: What skills are required?"
        assert histories[0].chat_type == "rag"
        assert histories[0].sources_json == ["jd.pdf"]
