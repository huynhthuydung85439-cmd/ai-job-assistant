from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.services.auth import AuthService, get_auth_service

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
async def register(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = await service.register(
        username=payload.username,
        email=str(payload.email),
        password=payload.password.get_secret_value(),
    )
    return UserResponse(id=user.id, username=user.username, email=user.email)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and obtain a JWT",
)
async def login(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    token, user_id = await service.login(
        username=payload.username,
        password=payload.password.get_secret_value(),
    )
    return LoginResponse(token=token, user_id=user_id)
