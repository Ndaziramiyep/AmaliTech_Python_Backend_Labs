"""Pydantic request/response schemas for the auth API."""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    """Request body for POST /register."""

    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """Request body for POST /login."""

    email: str
    password: str


class UserResponse(BaseModel):
    """Public representation of a registered user."""

    id: str
    username: str
    email: str


class LoginResponse(BaseModel):
    """Response body for a successful POST /login."""

    success: bool
