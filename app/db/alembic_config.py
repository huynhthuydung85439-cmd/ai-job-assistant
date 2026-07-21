"""Helpers for safely passing runtime settings through Alembic's ConfigParser."""


def escape_alembic_config_value(value: str) -> str:
    """Escape ConfigParser interpolation markers while preserving the parsed value."""
    return value.replace("%", "%%")
