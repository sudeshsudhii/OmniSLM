"""
OmniSLM Auth Routes — /api/v1/auth/*
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import Auth, get_auth_service
from src.api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserProfile,
)
from src.core.exceptions import AuthenticationError, ConflictError, InvalidTokenError
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """Register a new user and create their workspace/tenant."""
    try:
        result = await auth_service.register(
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            tenant_name=body.tenant_name,
        )
        return RegisterResponse(**result)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message) from e


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate and receive JWT access + refresh tokens."""
    try:
        tokens = await auth_service.login(email=body.email, password=body.password)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message
        ) from e


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    body: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Exchange a refresh token for a new token pair."""
    try:
        tokens = await auth_service.refresh_tokens(body.refresh_token)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message
        ) from e


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
)
async def get_me(
    auth: Auth,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserProfile:
    """Get the authenticated user's profile."""
    user = await auth_service.get_user_by_id(auth.user_id)
    return UserProfile(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        tenant_id=str(user.tenant_id),
        roles=auth.roles,
        created_at=user.created_at,
    )
