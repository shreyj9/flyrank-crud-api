"""Small service layer around the Supabase Auth SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException

from auth_client import supabase


def _serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def serialize_user(user: Any) -> dict[str, object | None]:
    """Return only safe user metadata to API clients."""
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": _serialize_datetime(user.created_at),
    }


def signup_user(email: str, password: str) -> dict[str, object]:
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
    except Exception as error:
        raise HTTPException(status_code=400, detail="Unable to create account") from error

    if response.user is None:
        raise HTTPException(status_code=400, detail="Unable to create account")

    return {"user": serialize_user(response.user)}


def login_user(email: str, password: str) -> dict[str, object]:
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception as error:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials",
        ) from error

    if response.session is None:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
        "token_type": "bearer",
        "expires_in": response.session.expires_in,
    }


def verify_access_token(token: str) -> dict[str, object | None]:
    """Ask Supabase to validate a JWT and return safe user metadata."""
    try:
        response = supabase.auth.get_user(token)
    except Exception as error:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        ) from error

    if response.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return serialize_user(response.user)


def logout_current_session() -> None:
    """Ask Supabase to revoke the current session's refresh token."""
    try:
        supabase.auth.sign_out()
    except Exception as error:
        raise HTTPException(status_code=503, detail="Unable to end session") from error
