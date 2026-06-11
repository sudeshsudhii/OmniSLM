"""
OmniSLM API Dependencies.

FastAPI dependency injection for services and auth context.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.core.exceptions import AuthenticationError, InvalidTokenError
from src.core.types import AuthContext
from src.core.interfaces.runtime import BaseRuntime
from src.core.registry.runtime_registry import runtime_registry
from src.core.types import ModelRuntime
from src.infrastructure.database.session import get_db
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService

settings = get_settings()

# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)


def get_default_runtime() -> BaseRuntime:
    """Get the default runtime (Ollama) from the registry."""
    return runtime_registry.get_runtime(ModelRuntime.OLLAMA.value)


# ---- Service Factories ----


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Inject AuthService with database session."""
    return AuthService(db)


def get_chat_service(
    db: AsyncSession = Depends(get_db),
    runtime: BaseRuntime = Depends(get_default_runtime),
) -> ChatService:
    """Inject ChatService with database and default runtime."""
    return ChatService(db, runtime)


# ---- Auth Context ----


async def get_auth_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Extract and validate authentication from the request.

    Supports:
    1. Bearer JWT token (Authorization header)
    2. API Key (X-API-Key header)
    """
    auth_service = AuthService(db)

    # Try Bearer token first
    if credentials and credentials.credentials:
        try:
            return auth_service.verify_access_token(credentials.credentials)
        except (AuthenticationError, InvalidTokenError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e.message),
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    # Try API Key
    if x_api_key:
        try:
            return await auth_service.validate_api_key(x_api_key)
        except InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e.message),
            ) from e

    # No credentials provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide Bearer token or X-API-Key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Type alias for convenience
Auth = Annotated[AuthContext, Depends(get_auth_context)]
