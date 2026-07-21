from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.alembic_config import escape_alembic_config_value
from app.db.base import Base
from scripts.check_cloud_runtime import find_missing_alembic_runtime_paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_percent_encoded_database_url_round_trips_through_alembic_config():
    database_url = "mysql+asyncmy://placeholder:placeholder%21@db.example:3306/example"
    config = Config()

    config.set_main_option("sqlalchemy.url", escape_alembic_config_value(database_url))

    assert config.get_main_option("sqlalchemy.url") == database_url


def test_migration_revision_chain_has_one_complete_head():
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    revisions = {
        revision.revision: revision.down_revision
        for revision in ScriptDirectory.from_config(config).walk_revisions()
    }

    assert revisions == {
        "20260719_02": "20260717_01",
        "20260717_01": None,
    }


def test_alembic_metadata_contains_every_migrated_table():
    assert set(Base.metadata.tables) == {
        "analysis_records",
        "chat_histories",
        "knowledge_documents",
        "resumes",
        "users",
    }


def test_cloud_image_source_contains_alembic_runtime_paths():
    assert find_missing_alembic_runtime_paths(PROJECT_ROOT) == []


def test_migrations_render_complete_mysql_ddl_without_duplicate_operations(monkeypatch, tmp_path):
    database_url = (
        "mysql+asyncmy://placeholder:placeholder%21@db.example:3306/example?charset=utf8mb4"
    )
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    output = StringIO()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        with redirect_stdout(output):
            command.upgrade(config, "head", sql=True)
    finally:
        get_settings.cache_clear()

    rendered_sql = output.getvalue()
    for table_name in (
        "users",
        "resumes",
        "analysis_records",
        "chat_histories",
        "knowledge_documents",
    ):
        assert rendered_sql.count(f"CREATE TABLE {table_name}") == 1

    assert rendered_sql.count("ADD COLUMN job_description") == 1
    assert rendered_sql.count("ADD COLUMN chat_type") == 1
    assert rendered_sql.count("ADD COLUMN sources_json") == 1
