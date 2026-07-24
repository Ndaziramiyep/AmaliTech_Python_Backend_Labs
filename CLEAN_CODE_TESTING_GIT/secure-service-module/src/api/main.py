"""Thin FastAPI wrapper exposing UserService over HTTP.

This module is deliberately minimal: it only translates HTTP requests into
calls on UserService and maps domain exceptions to HTTP status codes. All
authentication logic lives in `src.auth`, framework-free and unit-testable
in isolation -- FastAPI is purely a delivery mechanism on top of it.
"""

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, status

from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.service import UserService

from .schemas import LoginRequest, LoginResponse, RegisterRequest, UserResponse

app = FastAPI(title="Secure Service Module API")


@lru_cache
def get_user_service() -> UserService:
    """Return a process-wide UserService backed by in-memory storage.

    Cached so every request shares the same repository instance. Swapping
    in a database-backed UserRepository later means changing only this
    function -- UserService and the routes below stay untouched.
    """
    return UserService(InMemoryUserRepository(), BcryptPasswordHasher())


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest, service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Register a new user and return the created user's public fields."""
    try:
        user = service.register_user(payload.username, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InvalidPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return UserResponse(id=user.id, username=user.username, email=user.email)


@app.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest, service: UserService = Depends(get_user_service)
) -> LoginResponse:
    """Verify login credentials for an existing user."""
    try:
        service.verify_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except InvalidPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return LoginResponse(success=True)
