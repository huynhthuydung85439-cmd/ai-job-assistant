"""Add history metadata and user-owned knowledge documents.

Revision ID: 20260719_02
Revises: 20260717_01
Create Date: 2026-07-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260719_02"
down_revision: str | None = "20260717_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_records",
        sa.Column("job_description", mysql.LONGTEXT(), nullable=True),
    )
    op.add_column(
        "chat_histories",
        sa.Column(
            "chat_type",
            sa.String(length=16),
            server_default="chat",
            nullable=False,
        ),
    )
    op.add_column(
        "chat_histories",
        sa.Column("sources_json", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_chat_histories_chat_type",
        "chat_histories",
        ["chat_type"],
        unique=False,
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("collection_name", sa.String(length=128), nullable=False),
        sa.Column("vector_ids", sa.JSON(), nullable=False),
        sa.Column(
            "create_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_documents_user_id",
        "knowledge_documents",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_documents_user_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_chat_histories_chat_type", table_name="chat_histories")
    op.drop_column("chat_histories", "sources_json")
    op.drop_column("chat_histories", "chat_type")
    op.drop_column("analysis_records", "job_description")
