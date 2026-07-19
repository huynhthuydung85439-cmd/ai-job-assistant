from langchain_core.documents import Document

from app.rag.vector_store import KnowledgeVectorStore


class KnowledgeRetriever:
    def __init__(self, vector_store: KnowledgeVectorStore, top_k: int) -> None:
        self._vector_store = vector_store
        self._top_k = top_k

    def retrieve(self, question: str, user_id: int) -> list[Document]:
        return self._vector_store.search(question, user_id=user_id, top_k=self._top_k)
