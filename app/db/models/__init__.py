"""Import all models so Alembic can discover their metadata."""

from app.models import AnalysisRecord, ChatHistory, Resume, User

__all__ = ["AnalysisRecord", "ChatHistory", "Resume", "User"]
