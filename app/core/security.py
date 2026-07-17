from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import Settings
from app.core.exceptions import (
    AuthConfigurationError,
    AuthenticationError,
    PasswordPolicyError,
)


def _jwt_secret(settings: Settings) -> str:
    secret = settings.jwt_secret_key.get_secret_value().strip()
    if not secret:
        raise AuthConfigurationError
    return secret


def hash_password(password: str, rounds: int = 12) -> str:
    encoded = password.encode("utf-8")
    if not 8 <= len(encoded) <= 72:
        raise PasswordPolicyError
    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, _jwt_secret(settings), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> int:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(settings),
            algorithms=[settings.jwt_algorithm],
        )
        subject = payload.get("sub")
        if subject is None:
            raise AuthenticationError
        return int(subject)
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise AuthenticationError from exc
