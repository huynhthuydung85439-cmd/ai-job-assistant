import pytest

from app.main import app
from app.rag.rag_service import get_rag_service
from app.services.chat import get_chat_service
from app.services.resume_analyzer import get_resume_analyzer_service
from tests.test_user_persistence import (
    SuccessfulChatService,
    SuccessfulRAGService,
    SuccessfulResumeAnalyzer,
    create_pdf,
    database_client,  # noqa: F401
    register_and_login,
)


@pytest.mark.asyncio
async def test_history_lists_details_pagination_and_user_isolation(
    database_client,  # noqa: F811
) -> None:
    client, _ = database_client
    _, token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    app.dependency_overrides[get_resume_analyzer_service] = SuccessfulResumeAnalyzer
    app.dependency_overrides[get_chat_service] = SuccessfulChatService
    app.dependency_overrides[get_rag_service] = SuccessfulRAGService

    resume_ids: list[int] = []
    for filename in ("resume-one.pdf", "resume-two.pdf"):
        upload = await client.post(
            "/api/v1/resume/upload",
            files={"file": (filename, create_pdf(), "application/pdf")},
            headers=headers,
        )
        assert upload.status_code == 200
        resume_ids.append(upload.json()["resume_id"])

    analysis = await client.post(
        "/api/v1/resume/analyze",
        json={
            "resume_id": resume_ids[0],
            "resume_text": "Python FastAPI experience",
            "job_description": "Senior Backend Engineer\nPython and Kubernetes required",
        },
        headers=headers,
    )
    assert analysis.status_code == 200

    ordinary_chat = await client.post(
        "/api/v1/chat",
        json={"message": "How should I prepare?"},
        headers=headers,
    )
    assert ordinary_chat.status_code == 200
    rag_chat = await client.post(
        "/api/v1/knowledge/chat",
        json={"question": "Which skills are required?"},
        headers=headers,
    )
    assert rag_chat.status_code == 200

    resumes = await client.get(
        "/api/v1/history/resumes?page=1&page_size=1",
        headers=headers,
    )
    assert resumes.status_code == 200
    assert resumes.json()["total"] == 2
    assert resumes.json()["pages"] == 2
    assert len(resumes.json()["items"]) == 1
    assert "content" not in resumes.json()["items"][0]
    assert "text" not in resumes.json()["items"][0]

    analyses = await client.get("/api/v1/history/analyses", headers=headers)
    assert analyses.status_code == 200
    analysis_item = analyses.json()["items"][0]
    assert analysis_item["score"] == 88
    assert analysis_item["job_title"] == "Senior Backend Engineer"
    detail = await client.get(
        f"/api/v1/history/analyses/{analysis_item['id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["job_description"].startswith("Senior Backend Engineer")
    assert detail_body["result"]["matching_skills"] == ["Python"]
    assert detail_body["result"]["missing_skills"] == ["Kubernetes"]

    chats = await client.get("/api/v1/history/chats", headers=headers)
    rag_chats = await client.get("/api/v1/history/rag-chats", headers=headers)
    assert chats.status_code == 200
    assert chats.json()["total"] == 1
    assert chats.json()["items"][0]["sources"] == []
    assert rag_chats.status_code == 200
    assert rag_chats.json()["total"] == 1
    assert rag_chats.json()["items"][0]["sources"] == ["jd.pdf"]

    register_bob = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "secure-password",
        },
    )
    assert register_bob.status_code == 201
    login_bob = await client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "secure-password"},
    )
    bob_headers = {"Authorization": f"Bearer {login_bob.json()['token']}"}
    for endpoint in ("resumes", "analyses", "chats", "rag-chats"):
        response = await client.get(
            f"/api/v1/history/{endpoint}",
            headers=bob_headers,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0
    hidden_detail = await client.get(
        f"/api/v1/history/analyses/{analysis_item['id']}",
        headers=bob_headers,
    )
    assert hidden_detail.status_code == 404


@pytest.mark.asyncio
async def test_history_endpoints_require_authentication(
    database_client,  # noqa: F811
) -> None:
    client, _ = database_client

    for endpoint in ("resumes", "analyses", "chats", "rag-chats"):
        response = await client.get(f"/api/v1/history/{endpoint}")
        assert response.status_code == 401
