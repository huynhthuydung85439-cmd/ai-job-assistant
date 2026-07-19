import pytest
from langchain_core.documents import Document
from langchain_core.language_models import FakeListChatModel

from app.rag.rag_service import RAGService


class StubRetriever:
    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents

    def retrieve(self, question: str, user_id: int) -> list[Document]:
        assert question
        assert user_id == 7
        return self.documents


@pytest.mark.asyncio
async def test_rag_service_answers_with_retrieved_sources() -> None:
    documents = [
        Document(
            page_content="岗位要求 Python、FastAPI 和 MySQL。",
            metadata={"source": "job-description.pdf"},
        ),
        Document(
            page_content="候选人需要具备 Docker 部署经验。",
            metadata={"source": "job-description.pdf"},
        ),
    ]
    service = RAGService(
        loader=object(),
        vector_store=object(),
        retriever=StubRetriever(documents),
        model_factory=lambda: FakeListChatModel(
            responses=["该岗位需要 Python、FastAPI、MySQL 和 Docker。"]
        ),
        collection_name="test_knowledge",
    )

    answer, sources = await service.answer("这个岗位需要哪些技能？", user_id=7)

    assert answer == "该岗位需要 Python、FastAPI、MySQL 和 Docker。"
    assert sources == ["job-description.pdf"]


@pytest.mark.asyncio
async def test_rag_service_handles_empty_knowledge_base_without_model_call() -> None:
    service = RAGService(
        loader=object(),
        vector_store=object(),
        retriever=StubRetriever([]),
        model_factory=lambda: (_ for _ in ()).throw(AssertionError("model should not be created")),
        collection_name="test_knowledge",
    )

    answer, sources = await service.answer("未知问题", user_id=7)

    assert answer == "知识库中没有找到相关资料。"
    assert sources == []
