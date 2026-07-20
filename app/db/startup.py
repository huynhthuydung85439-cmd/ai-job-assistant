"""Prepare the database before the API process starts.

The container entrypoint calls this module before Uvicorn. It only checks
connectivity and upgrades Alembic to ``head``; it never runs downgrade or
destructive SQL.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from time import monotonic

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

MIGRATION_LOCK_NAME = "ai_job_assistant_alembic_upgrade"


def _positive_number_from_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive number") from exc
    if value <= 0:
        raise ValueError(f"{name} must be a positive number")
    return value


def _create_engine() -> AsyncEngine:
    database_url = get_settings().database_url
    connect_args: dict[str, float] = {}
    if database_url.startswith("mysql+asyncmy://"):
        connect_args["connect_timeout"] = _positive_number_from_env(
            "DB_CONNECT_TIMEOUT_SECONDS", 5
        )
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        poolclass=NullPool,
        connect_args=connect_args,
    )


async def _wait_for_database(engine: AsyncEngine) -> None:
    timeout = _positive_number_from_env("DB_STARTUP_TIMEOUT_SECONDS", 90)
    retry_interval = _positive_number_from_env("DB_CONNECT_RETRY_SECONDS", 2)
    deadline = monotonic() + timeout
    attempt = 0

    while True:
        attempt += 1
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            print(f"Database connection is ready (attempt {attempt}).", flush=True)
            return
        except Exception:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"Database was not reachable within {timeout:g} seconds"
                ) from None
            print(
                f"Database is not ready (attempt {attempt}); retrying.",
                flush=True,
            )
            await asyncio.sleep(min(retry_interval, remaining))


def _run_alembic_upgrade() -> None:
    print("Running Alembic upgrade to head.", flush=True)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
    )


async def _migrate_with_mysql_lock(engine: AsyncEngine) -> None:
    lock_timeout = int(_positive_number_from_env("DB_MIGRATION_LOCK_TIMEOUT_SECONDS", 120))
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT GET_LOCK(:lock_name, :lock_timeout)"),
            {"lock_name": MIGRATION_LOCK_NAME, "lock_timeout": lock_timeout},
        )
        if result.scalar_one() != 1:
            raise TimeoutError(
                f"Could not acquire the database migration lock within {lock_timeout} seconds"
            )

        try:
            _run_alembic_upgrade()
        finally:
            await connection.execute(
                text("SELECT RELEASE_LOCK(:lock_name)"),
                {"lock_name": MIGRATION_LOCK_NAME},
            )


async def prepare_database() -> None:
    engine = _create_engine()
    try:
        await _wait_for_database(engine)
        if engine.dialect.name == "mysql":
            await _migrate_with_mysql_lock(engine)
        else:
            _run_alembic_upgrade()
    finally:
        await engine.dispose()


def main() -> int:
    try:
        asyncio.run(prepare_database())
    except Exception as exc:
        # Do not include exception details: connection errors may contain
        # deployment-specific host or credential information.
        print(
            f"Database preparation failed ({type(exc).__name__}); API will not start.",
            file=sys.stderr,
            flush=True,
        )
        return 1

    print("Database migration completed successfully.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
