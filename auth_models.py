"""Request models used by the authentication endpoints."""

from pydantic import BaseModel, field_validator


class AuthCredentials(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip()
        if not email:
            raise ValueError("Email is required")
        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Password is required")
        return value
