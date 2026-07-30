"""Reusable authentication dependency for protected FastAPI routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from auth_service import verify_access_token


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None
    created_at: str | None
    access_token: str


def require_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Require an Authorization: Bearer <token> header and return the token."""
    if authorization is None:
        raise HTTPException(status_code=401, detail="Access token required")

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Access token required")

    return token.strip()


def get_current_user(
    token: Annotated[str, Depends(require_bearer_token)],
) -> AuthenticatedUser:
    """Verify the bearer token once and inject the authenticated user."""
    user = verify_access_token(token)
    return AuthenticatedUser(
        id=str(user["id"]),
        email=user.get("email"),
        created_at=user.get("created_at"),
        access_token=token,
    )
