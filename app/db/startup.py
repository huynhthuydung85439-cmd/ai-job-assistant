"""Prepare the database before the API process starts.

The container entrypoint calls this module before Uvicorn. It only checks
connectivity and upgrades Alembic to ``head``; it never runs downgrade or
destructive SQL.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
from time import monotonic
from urllib.parse import quote

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

MIGRATION_LOCK_NAME = "ai_job_assistant_alembic_upgrade"

_MYSQL_ERROR_DESCRIPTIONS = {
    1044: "database access denied",
    1045: "authentication failed",
    1049: "database does not exist",
    2002: "unable to reach database server",
    2003: "unable to reach database server",
    2005: "database host resolution failed",
    2006: "database connection was lost",
    2013: "database connection was lost",
}

_DATABASE_URL_PATTERN = re.compile(
    r"(?i)\b(?:mysql|postgresql|sqlite)(?:\+[a-z0-9_]+)?:/{2,3}[^\s\"'<>]+"
)
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(database_url|password|passwd|pwd|username|user|api[_-]?key|secret|token)"
    r"(\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)


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


def _exception_chain(exc: BaseException) -> list[BaseException]:
    """Return wrapped database exceptions without rendering their messages."""
    pending: list[BaseException] = [exc]
    found: list[BaseException] = []
    seen: set[int] = set()

    while pending:
        current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        found.append(current)

        for wrapped in (
            getattr(current, "orig", None),
            current.__cause__,
            current.__context__,
        ):
            if isinstance(wrapped, BaseException):
                pending.append(wrapped)

    return found


def _mysql_error_code(exceptions: list[BaseException]) -> int | None:
    for exc in exceptions:
        for arg in getattr(exc, "args", ()):
            if isinstance(arg, int) and not isinstance(arg, bool):
                return arg
    return None


def _describe_database_error(exc: BaseException) -> str:
    """Classify a connection error without exposing its original message or URL."""
    exceptions = _exception_chain(exc)
    error_type = type(exc).__name__
    mysql_error_code = _mysql_error_code(exceptions)

    if mysql_error_code in _MYSQL_ERROR_DESCRIPTIONS:
        description = _MYSQL_ERROR_DESCRIPTIONS[mysql_error_code]
        return f"{error_type}: {description} (MySQL error {mysql_error_code})"

    messages = " ".join(
        str(arg).lower()
        for current in exceptions
        for arg in getattr(current, "args", ())
        if not isinstance(arg, BaseException)
    )
    if any(isinstance(current, TimeoutError) for current in exceptions) or any(
        marker in messages for marker in ("timed out", "timeout")
    ):
        description = "connection timed out"
    elif any(isinstance(current, ConnectionRefusedError) for current in exceptions) or any(
        marker in messages for marker in ("connection refused", "errno 111", "winerror 10061")
    ):
        description = "connection refused"
    elif "access denied" in messages or "authentication failed" in messages:
        description = "authentication failed"
    elif "unknown database" in messages:
        description = "database does not exist"
    elif any(
        marker in messages
        for marker in ("getaddrinfo", "name or service not known", "nodename nor servname")
    ):
        description = "database host resolution failed"
    else:
        description = "connection attempt failed"

    return f"{error_type}: {description}"


def _database_sensitive_values(database_url: URL | None) -> list[str]:
    if database_url is None:
        return []

    sensitive_values: set[str] = set()
    for value in (database_url.username, database_url.password):
        if value:
            sensitive_values.add(value)
            sensitive_values.add(quote(value, safe=""))
    return sorted(sensitive_values, key=len, reverse=True)


def _sanitize_alembic_output(output: str, database_url: URL | None) -> str:
    sanitized = _DATABASE_URL_PATTERN.sub("<redacted-database-url>", output)
    for sensitive_value in _database_sensitive_values(database_url):
        sanitized = sanitized.replace(sensitive_value, "<redacted>")
    return _SECRET_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}<redacted>",
        sanitized,
    ).strip()


def _describe_alembic_failure(stdout: str, stderr: str) -> str:
    output = f"{stdout}\n{stderr}".lower()
    if "interpolation syntax" in output or "interpolationerror" in output:
        return "Alembic configuration interpolation failed"
    if "access denied" in output or "authentication failed" in output:
        return "database authentication or authorization failed"
    if "unknown database" in output:
        return "database does not exist"
    if "already exists" in output or "duplicate column" in output:
        return "migration conflicts with the existing database schema"
    if "can't locate revision" in output or "no such revision" in output:
        return "migration revision is missing"
    if any(
        marker in output
        for marker in ("can't connect", "connection refused", "timed out", "timeout")
    ):
        return "database connection failed during migration"
    if "no module named" in output and "alembic" in output:
        return "Alembic is not installed in the runtime image"
    return "Alembic command failed"


def _print_alembic_streams(
    stdout: str,
    stderr: str,
    database_url: URL | None,
    *,
    include_empty: bool,
) -> None:
    for stream_name, stream_value in (("stdout", stdout), ("stderr", stderr)):
        sanitized = _sanitize_alembic_output(stream_value, database_url)
        if not sanitized and not include_empty:
            continue
        destination = sys.stderr if stream_name == "stderr" else sys.stdout
        print(
            f"Alembic {stream_name} (sanitized):\n{sanitized or '<empty>'}",
            file=destination,
            flush=True,
        )


def _print_alembic_failure(
    *,
    exception_type: str,
    reason: str,
    stdout: str,
    stderr: str,
    return_code: int | None,
    database_url: URL | None,
) -> None:
    code_text = str(return_code) if return_code is not None else "unavailable"
    print(
        "Alembic upgrade failed; "
        f"exception_type={exception_type}; reason={reason}; return_code={code_text}.",
        file=sys.stderr,
        flush=True,
    )
    _print_alembic_streams(
        stdout,
        stderr,
        database_url,
        include_empty=True,
    )


def _create_engine() -> AsyncEngine:
    database_url = get_settings().database_url
    connect_args: dict[str, float] = {}
    if database_url.startswith("mysql+asyncmy://"):
        connect_args["connect_timeout"] = _positive_number_from_env("DB_CONNECT_TIMEOUT_SECONDS", 5)
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
        except Exception as exc:
            error_description = _describe_database_error(exc)
            remaining = deadline - monotonic()
            if remaining <= 0:
                print(
                    f"Database is not ready (attempt {attempt}); "
                    f"error={error_description}; retry deadline reached.",
                    flush=True,
                )
                raise TimeoutError(
                    f"Database was not reachable within {timeout:g} seconds"
                ) from None
            print(
                f"Database is not ready (attempt {attempt}); error={error_description}; retrying.",
                flush=True,
            )
            await asyncio.sleep(min(retry_interval, remaining))


def _run_alembic_upgrade(database_url: URL | None = None) -> None:
    print("Running Alembic upgrade to head.", flush=True)
    command = [sys.executable, "-m", "alembic", "upgrade", "head"]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        _print_alembic_failure(
            exception_type=type(exc).__name__,
            reason="Alembic process could not be started",
            stdout="",
            stderr="",
            return_code=None,
            database_url=database_url,
        )
        raise

    if result.returncode != 0:
        _print_alembic_failure(
            exception_type="CalledProcessError",
            reason=_describe_alembic_failure(result.stdout, result.stderr),
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
            database_url=database_url,
        )
        raise subprocess.CalledProcessError(result.returncode, command) from None

    _print_alembic_streams(
        result.stdout,
        result.stderr,
        database_url,
        include_empty=False,
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
            _run_alembic_upgrade(engine.url)
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
            _run_alembic_upgrade(engine.url)
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
