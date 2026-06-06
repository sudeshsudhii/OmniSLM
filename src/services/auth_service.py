"""
OmniSLM Auth Service.

Handles user registration, login, JWT token management, and API key validation.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.core.exceptions import (
    AuthenticationError,
    ConflictError,
    InvalidTokenError,
    NotFoundError,
)
from src.core.types import AuthContext, TokenPair
from src.infrastructure.database.models import ApiKey, Role, Tenant, User, UserRole

logger = get_logger(__name__)
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Application service for authentication and authorization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- Registration ----

    async def register(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
        tenant_name: str | None = None,
    ) -> dict:
        """Register a new user and create their tenant."""
        # Check if email exists
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ConflictError(f"User with email '{email}' already exists")

        # Create tenant
        tenant_slug = (tenant_name or email.split("@")[0]).lower().replace(" ", "-")
        # Ensure unique slug
        slug_check = await self.db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
        if slug_check.scalar_one_or_none():
            tenant_slug = f"{tenant_slug}-{uuid.uuid4().hex[:6]}"

        tenant = Tenant(
            name=tenant_name or f"{email.split('@')[0]}'s Workspace",
            slug=tenant_slug,
        )
        self.db.add(tenant)
        await self.db.flush()

        # Create user
        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=pwd_context.hash(password),
            display_name=display_name or email.split("@")[0],
        )
        self.db.add(user)
        await self.db.flush()

        # Create default admin role and assign
        admin_role = Role(
            tenant_id=tenant.id,
            name="tenant_admin",
            description="Full tenant access",
            is_system=True,
        )
        self.db.add(admin_role)
        await self.db.flush()

        user_role = UserRole(user_id=user.id, role_id=admin_role.id)
        self.db.add(user_role)

        logger.info("User registered", user_id=str(user.id), email=email)

        return {
            "user_id": str(user.id),
            "tenant_id": str(tenant.id),
            "email": email,
        }

    # ---- Login ----

    async def login(self, email: str, password: str) -> TokenPair:
        """Authenticate user with email and password, return token pair."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise AuthenticationError("Invalid email or password")

        if not pwd_context.verify(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if user.status != "active":
            raise AuthenticationError("Account is suspended or deleted")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Get roles
        roles = await self._get_user_roles(user.id)

        # Generate tokens
        tokens = self._create_token_pair(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            roles=roles,
        )

        logger.info("User logged in", user_id=str(user.id), email=email)
        return tokens

    # ---- Token Management ----

    def _create_token_pair(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        roles: list[str],
    ) -> TokenPair:
        """Create JWT access + refresh token pair."""
        now = datetime.now(timezone.utc)

        access_payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "roles": roles,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        }
        access_token = jwt.encode(
            access_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        refresh_payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
        }
        refresh_token = jwt.encode(
            refresh_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    def verify_access_token(self, token: str) -> AuthContext:
        """Verify and decode a JWT access token, returning AuthContext."""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
        except JWTError as e:
            raise InvalidTokenError(f"Invalid token: {e}") from e

        if payload.get("type") != "access":
            raise InvalidTokenError("Not an access token")

        return AuthContext(
            user_id=uuid.UUID(payload["sub"]),
            tenant_id=uuid.UUID(payload["tenant_id"]),
            email=payload["email"],
            roles=payload.get("roles", []),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """Exchange a refresh token for a new token pair."""
        try:
            payload = jwt.decode(
                refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
        except JWTError as e:
            raise InvalidTokenError(f"Invalid refresh token: {e}") from e

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Not a refresh token")

        user_id = payload["sub"]
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user or user.status != "active":
            raise AuthenticationError("User not found or inactive")

        roles = await self._get_user_roles(user.id)
        return self._create_token_pair(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            roles=roles,
        )

    # ---- API Key Management ----

    async def create_api_key(
        self,
        auth: AuthContext,
        name: str,
        scopes: list[str] | None = None,
        expires_in_days: int | None = None,
    ) -> dict:
        """Create a new API key. Returns the raw key (shown only once)."""
        raw_key = f"{settings.api_key_prefix}{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[: len(settings.api_key_prefix) + 8]

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = ApiKey(
            tenant_id=auth.tenant_id,
            user_id=auth.user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes or [],
            expires_at=expires_at,
        )
        self.db.add(api_key)
        await self.db.flush()

        logger.info("API key created", key_id=str(api_key.id), name=name)

        return {
            "id": str(api_key.id),
            "key": raw_key,  # Only returned once!
            "key_prefix": key_prefix,
            "name": name,
            "scopes": scopes or [],
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    async def validate_api_key(self, raw_key: str) -> AuthContext:
        """Validate an API key and return AuthContext."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[: len(settings.api_key_prefix) + 8]

        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.key_prefix == key_prefix,
                ApiKey.key_hash == key_hash,
                ApiKey.status == "active",
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise InvalidTokenError("Invalid API key")

        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            raise InvalidTokenError("API key has expired")

        # Update last used
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Get user for context
        user_result = await self.db.execute(select(User).where(User.id == api_key.user_id))
        user = user_result.scalar_one_or_none()
        email = user.email if user else ""
        roles = await self._get_user_roles(api_key.user_id) if api_key.user_id else []

        return AuthContext(
            user_id=api_key.user_id or uuid.UUID(int=0),
            tenant_id=api_key.tenant_id,
            email=email,
            roles=roles,
        )

    # ---- Helpers ----

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """Fetch a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    async def _get_user_roles(self, user_id: uuid.UUID) -> list[str]:
        """Get role names for a user."""
        result = await self.db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return [row[0] for row in result.all()]
