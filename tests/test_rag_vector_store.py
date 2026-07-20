import pytest
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from app.core.config import Settings
from app.core.exceptions import RAGDisabledError
from app.rag.retriever import KnowledgeRetriever
from app.rag.vector_store import KnowledgeVectorStore, create_knowledge_vector_store


def test_chroma_persists_and_retrieves_knowledge(tmp_path) -> None:
    embeddings = DeterministicFakeEmbedding(size=32)
    persist_directory = tmp_path / "chroma"
    chroma = Chroma(
        collection_name="test_knowledge",
        embedding_function=embeddings,
        persist_directory=str(persist_directory),
    )
    vector_store = KnowledgeVectorStore(chroma)
    documents = [
        Document(
            id="doc-1",
            page_content="Python FastAPI Kubernetes skills are required.",
            metadata={"source": "job-description.pdf", "user_id": "1"},
        ),
        Document(
            id="doc-2",
            page_content="Behavioral interview preparation guide.",
            metadata={"source": "interview-guide.pdf", "user_id": "2"},
        ),
    ]

    ids = vector_store.add_documents(documents)
    reopened_store = KnowledgeVectorStore(
        Chroma(
            collection_name="test_knowledge",
            embedding_function=embeddings,
            persist_directory=str(persist_directory),
        )
    )
    results = KnowledgeRetriever(reopened_store, top_k=2).retrieve(
        "Python FastAPI Kubernetes skills are required.",
        user_id=1,
    )

    assert ids == ["doc-1", "doc-2"]
    assert len(results) == 1
    assert results[0].metadata["source"] == "job-description.pdf"


def test_disabled_rag_does_not_create_chroma_directory(tmp_path) -> None:
    persist_directory = tmp_path / "must-not-exist"
    settings = Settings(
        _env_file=None,
        rag_enabled=False,
        chroma_persist_directory=str(persist_directory),
    )

    with pytest.raises(RAGDisabledError):
        create_knowledge_vector_store(settings=settings)

    assert not persist_directory.exists()
