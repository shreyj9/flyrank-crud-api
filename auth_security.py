"""Reusable Supabase bearer-token security for protected FastAPI routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth_service import verify_access_token

bearer_scheme = HTTPBearer(
    auto_error=False,
    bearerFormat="JWT",
    scheme_name="SupabaseBearer",
    description="Paste the access_token returned by POST /auth/login.",
)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None
    created_at: str | None
    access_token: str


def require_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ] = None,
) -> str:
    """Require a correctly formatted Bearer token and return its value."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Access token required")

    if credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(status_code=401, detail="Access token required")

    return credentials.credentials.strip()


def get_current_user(
    token: Annotated[str, Depends(require_bearer_token)],
) -> AuthenticatedUser:
    """Verify the token once and inject the authenticated user into a route."""
    user = verify_access_token(token)
    return AuthenticatedUser(
        id=str(user["id"]),
        email=user.get("email"),
        created_at=user.get("created_at"),
        access_token=token,
    )
