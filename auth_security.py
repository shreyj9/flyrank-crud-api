"""Authorization-header parsing used by protected routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException


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
