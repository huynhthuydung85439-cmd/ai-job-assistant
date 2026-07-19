from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import Settings, get_settings


class KnowledgeVectorStore:
    def __init__(self, store: VectorStore, embeddings: Embeddings | None = None) -> None:
        self.store = store
        self._embeddings = embeddings

    def add_documents(self, documents: list[Document]) -> list[str]:
        document_ids = [document.id for document in documents]
        if any(document_id is None for document_id in document_ids):
            raise ValueError("Every knowledge document chunk must have an id")
        ids = [str(document_id) for document_id in document_ids]
        return self.store.add_documents(documents=documents, ids=ids)

    def search(self, question: str, user_id: int, top_k: int) -> list[Document]:
        return self.store.similarity_search(
            question,
            k=top_k,
            filter={"user_id": str(user_id)},
        )

    def delete(self, ids: list[str]) -> None:
        if ids:
            self.store.delete(ids=ids)

    def warmup(self) -> None:
        if self._embeddings is None:
            raise RuntimeError("Embedding model is not available for warmup")
        self._embeddings.embed_query("AI job assistant knowledge base warmup")


def create_embeddings(settings: Settings | None = None) -> Embeddings:
    resolved_settings = settings or get_settings()
    return HuggingFaceEmbeddings(
        model_name=resolved_settings.embedding_model,
        model_kwargs={"device": resolved_settings.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )


def create_knowledge_vector_store(
    settings: Settings | None = None,
    embeddings: Embeddings | None = None,
) -> KnowledgeVectorStore:
    resolved_settings = settings or get_settings()
    persist_directory = Path(resolved_settings.chroma_persist_directory)
    persist_directory.mkdir(parents=True, exist_ok=True)
    resolved_embeddings = embeddings or create_embeddings(resolved_settings)
    store = Chroma(
        collection_name=resolved_settings.chroma_collection_name,
        embedding_function=resolved_embeddings,
        persist_directory=str(persist_directory),
    )
    return KnowledgeVectorStore(store, resolved_embeddings)


@lru_cache
def get_embedding_model() -> Embeddings:
    return create_embeddings()


@lru_cache
def get_knowledge_vector_store() -> KnowledgeVectorStore:
    return create_knowledge_vector_store(embeddings=get_embedding_model())
