"""Pydantic schemas for the auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Signup payload."""

    email: EmailStr
    password: str = Field(min_length=8, description="At least 8 characters.")


class UserRead(BaseModel):
    """A user as returned by the API — never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class Token(BaseModel):
    """A successful login response."""

    access_token: str
    token_type: str = "bearer"
