import pytest
from langchain_core.documents import Document
from sqlalchemy import select

from app.main import app
from app.models import KnowledgeDocument
from app.rag.loader import LoadedKnowledge
from app.rag.rag_service import get_rag_service
from tests.test_user_persistence import (
    database_client,  # noqa: F401
    register_and_login,
)


class SuccessfulRAGService:
    collection_name = "test_knowledge"

    def __init__(self) -> None:
        self.upload_count = 0
        self.deleted_ids: list[str] = []
        self.warmed_up = False

    async def upload_pdf(
        self,
        filename: str,
        content: bytes,
        user_id: int,
    ) -> LoadedKnowledge:
        assert content.startswith(b"%PDF-")
        assert user_id > 0
        self.upload_count += 1
        document_id = f"knowledge-doc-{self.upload_count}"
        return LoadedKnowledge(
            document_id=document_id,
            filename=filename,
            pages=2,
            chunks=[
                Document(
                    id=f"{document_id}-chunk-1",
                    page_content="Python FastAPI",
                    metadata={"user_id": str(user_id)},
                ),
                Document(
                    id=f"{document_id}-chunk-2",
                    page_content="MySQL Docker",
                    metadata={"user_id": str(user_id)},
                ),
            ],
        )

    async def answer(self, question: str, user_id: int) -> tuple[str, list[str]]:
        assert user_id > 0
        return f"RAG answer: {question}", ["job-description.pdf"]

    async def delete_chunks(self, ids: list[str]) -> None:
        self.deleted_ids.extend(ids)

    async def warmup(self) -> None:
        self.warmed_up = True


def use_rag_service(service: SuccessfulRAGService) -> None:
    app.dependency_overrides[get_rag_service] = lambda: service


@pytest.mark.asyncio
async def test_knowledge_endpoints_require_authentication(
    database_client,  # noqa: F811
) -> None:
    client, _ = database_client
    service = SuccessfulRAGService()
    use_rag_service(service)

    responses = [
        await client.post(
            "/api/v1/knowledge/upload",
            files={"file": ("jd.pdf", b"%PDF-test", "application/pdf")},
        ),
        await client.get("/api/v1/knowledge/documents"),
        await client.post("/api/v1/knowledge/warmup"),
        await client.post(
            "/api/v1/knowledge/chat",
            json={"question": "What skills are required?"},
        ),
    ]

    assert [response.status_code for response in responses] == [401, 401, 401, 401]


@pytest.mark.asyncio
async def test_knowledge_upload_list_and_delete_are_persistent_and_isolated(
    database_client,  # noqa: F811
) -> None:
    client, session_factory = database_client
    user_id, token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    service = SuccessfulRAGService()
    use_rag_service(service)

    for filename in ("job-description.pdf", "handbook.pdf"):
        response = await client.post(
            "/api/v1/knowledge/upload",
            files={"file": (filename, b"%PDF-test", "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 201
        assert response.json()["collection_name"] == "test_knowledge"
        assert response.json()["chunks"] == 2

    page = await client.get(
        "/api/v1/knowledge/documents?page=1&page_size=1",
        headers=headers,
    )
    assert page.status_code == 200
    page_body = page.json()
    assert page_body["total"] == 2
    assert page_body["pages"] == 2
    assert len(page_body["items"]) == 1
    document_id = page_body["items"][0]["document_id"]

    async with session_factory() as session:
        records = (
            await session.scalars(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.user_id == user_id
                )
            )
        ).all()
        assert len(records) == 2
        assert all(record.chunk_count == 2 for record in records)
        assert all(len(record.vector_ids) == 2 for record in records)

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
    bob_page = await client.get("/api/v1/knowledge/documents", headers=bob_headers)
    assert bob_page.status_code == 200
    assert bob_page.json()["total"] == 0
    forbidden_delete = await client.delete(
        f"/api/v1/knowledge/documents/{document_id}",
        headers=bob_headers,
    )
    assert forbidden_delete.status_code == 404

    deleted = await client.delete(
        f"/api/v1/knowledge/documents/{document_id}",
        headers=headers,
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"document_id": document_id, "deleted": True}
    assert len(service.deleted_ids) == 2


@pytest.mark.asyncio
async def test_knowledge_chat_warmup_and_validation(
    database_client,  # noqa: F811
) -> None:
    client, _ = database_client
    _, token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    service = SuccessfulRAGService()
    use_rag_service(service)

    warmup = await client.post("/api/v1/knowledge/warmup", headers=headers)
    assert warmup.status_code == 200
    assert warmup.json()["status"] == "ready"
    assert service.warmed_up is True

    chat = await client.post(
        "/api/v1/knowledge/chat",
        json={"question": "What skills are required?"},
        headers=headers,
    )
    assert chat.status_code == 200
    assert chat.json()["sources"] == ["job-description.pdf"]

    blank = await client.post(
        "/api/v1/knowledge/chat",
        json={"question": "   "},
        headers=headers,
    )
    assert blank.status_code == 422

    non_pdf = await client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("notes.txt", b"notes", "text/plain")},
        headers=headers,
    )
    assert non_pdf.status_code == 415
    assert non_pdf.json()["code"] == "unsupported_pdf"
