from types import SimpleNamespace

import pytest
from sqlalchemy.exc import OperationalError

from app.db import startup


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TimeoutError("operation timed out"), "TimeoutError: connection timed out"),
        (
            ConnectionRefusedError("connection refused"),
            "ConnectionRefusedError: connection refused",
        ),
        (
            OperationalError(
                "SELECT 1",
                {},
                RuntimeError(1045, "Access denied for user '<USERNAME>'"),
            ),
            "OperationalError: authentication failed (MySQL error 1045)",
        ),
        (
            RuntimeError(1049, "Unknown database '<DATABASE>'"),
            "RuntimeError: database does not exist (MySQL error 1049)",
        ),
    ],
)
def test_describe_database_error_classifies_common_failures(error, expected):
    assert startup._describe_database_error(error) == expected


def test_describe_database_error_does_not_expose_exception_details():
    sensitive_url = (
        "mysql+asyncmy://<USERNAME>:<PASSWORD>@172.17.0.15:3306/"
        "ai-job-assistant-d5ehi66ba6134c4?charset=utf8mb4"
    )

    description = startup._describe_database_error(RuntimeError(sensitive_url))

    assert description == "RuntimeError: connection attempt failed"
    assert sensitive_url not in description
    assert "<USERNAME>" not in description
    assert "<PASSWORD>" not in description


class _FailingConnectionContext:
    async def __aenter__(self):
        raise RuntimeError(1045, "Access denied for user '<USERNAME>' using '<PASSWORD>'")

    async def __aexit__(self, exc_type, exc, traceback):
        return False


@pytest.mark.asyncio
async def test_wait_for_database_logs_only_sanitized_error(monkeypatch, capsys):
    engine = SimpleNamespace(connect=lambda: _FailingConnectionContext())
    monotonic_values = iter((0.0, 0.5, 1.0))

    monkeypatch.setenv("DB_STARTUP_TIMEOUT_SECONDS", "0.75")
    monkeypatch.setattr(startup, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(startup.asyncio, "sleep", _no_sleep)

    with pytest.raises(TimeoutError, match="Database was not reachable"):
        await startup._wait_for_database(engine)

    output = capsys.readouterr().out
    assert "RuntimeError: authentication failed (MySQL error 1045)" in output
    assert "retrying" in output
    assert "retry deadline reached" in output
    assert "<USERNAME>" not in output
    assert "<PASSWORD>" not in output
    assert "mysql+asyncmy://" not in output


async def _no_sleep(_seconds: float) -> None:
    return None
