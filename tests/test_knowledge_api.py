import httpx
import pytest
from langchain_core.documents import Document

from app.main import app
from app.rag.loader import LoadedKnowledge
from app.rag.rag_service import get_rag_service


class SuccessfulRAGService:
    async def upload_pdf(self, filename: str, content: bytes) -> LoadedKnowledge:
        assert filename == "job-description.pdf"
        assert content.startswith(b"%PDF-")
        return LoadedKnowledge(
            document_id="knowledge-doc-1",
            filename=filename,
            pages=2,
            chunks=[
                Document(id="chunk-1", page_content="Python FastAPI", metadata={}),
                Document(id="chunk-2", page_content="MySQL Docker", metadata={}),
            ],
        )

    async def answer(self, question: str) -> tuple[str, list[str]]:
        assert question == "这个岗位需要哪些技能？"
        return "该岗位需要 Python 和 FastAPI。", ["job-description.pdf"]


async def request_with_rag_service(
    method: str,
    path: str,
    **kwargs,
) -> httpx.Response:
    app.dependency_overrides[get_rag_service] = SuccessfulRAGService
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)
    finally:
        app.dependency_overrides.pop(get_rag_service, None)


@pytest.mark.asyncio
async def test_knowledge_upload_returns_ingestion_summary() -> None:
    response = await request_with_rag_service(
        "POST",
        "/api/v1/knowledge/upload",
        files={"file": ("job-description.pdf", b"%PDF-test", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json() == {
        "document_id": "knowledge-doc-1",
        "filename": "job-description.pdf",
        "pages": 2,
        "chunks": 2,
    }


@pytest.mark.asyncio
async def test_knowledge_chat_returns_answer_and_sources() -> None:
    response = await request_with_rag_service(
        "POST",
        "/api/v1/knowledge/chat",
        json={"question": "这个岗位需要哪些技能？"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "该岗位需要 Python 和 FastAPI。",
        "sources": ["job-description.pdf"],
    }


@pytest.mark.asyncio
async def test_knowledge_chat_rejects_blank_question() -> None:
    response = await request_with_rag_service(
        "POST",
        "/api/v1/knowledge/chat",
        json={"question": "   "},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_knowledge_upload_rejects_non_pdf() -> None:
    response = await request_with_rag_service(
        "POST",
        "/api/v1/knowledge/upload",
        files={"file": ("notes.txt", b"notes", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_pdf"
