from langchain_core.documents import Document

from app.rag.vector_store import KnowledgeVectorStore


class KnowledgeRetriever:
    def __init__(self, vector_store: KnowledgeVectorStore, top_k: int) -> None:
        self._retriever = vector_store.store.as_retriever(search_kwargs={"k": top_k})

    def retrieve(self, question: str) -> list[Document]:
        return self._retriever.invoke(question)
