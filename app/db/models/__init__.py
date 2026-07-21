"""Import all models so Alembic can discover their metadata."""

from app.models import AnalysisRecord, ChatHistory, KnowledgeDocument, Resume, User

__all__ = ["AnalysisRecord", "ChatHistory", "KnowledgeDocument", "Resume", "User"]
