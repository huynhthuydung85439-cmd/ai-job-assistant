from typing import Annotated

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, DuplicateUserError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db_session
from app.models.user import User


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def register(self, username: str, email: str, password: str) -> User:
        normalized_username = username.strip()
        normalized_email = email.strip().lower()
        existing = await self._session.scalar(
            select(User.id).where(
                or_(User.username == normalized_username, User.email == normalized_email)
            )
        )
        if existing is not None:
            raise DuplicateUserError

        user = User(
            username=normalized_username,
            email=normalized_email,
            password_hash=hash_password(password, self._settings.bcrypt_rounds),
        )
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateUserError from exc
        await self._session.refresh(user)
        return user

    async def login(self, username: str, password: str) -> tuple[str, int]:
        user = await self._session.scalar(
            select(User).where(User.username == username.strip())
        )
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError
        return create_access_token(user.id, self._settings), user.id

    async def get_user_from_token(self, token: str) -> User:
        from app.core.security import decode_access_token

        user_id = decode_access_token(token, self._settings)
        user = await self._session.get(User, user_id)
        if user is None:
            raise AuthenticationError
        return user


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(session=session, settings=settings)
