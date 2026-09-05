from fastapi import APIRouter, Depends, Request, Response, HTTPException, status, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from app.database import get_db
from app.auth import verify_password, create_access_token, get_current_user
from app.models import User
from app.schemas import LoginRequest, LoginResponse, AuthMeResponse, UserDTO
from app.config import get_settings

router = APIRouter(prefix="", tags=["auth"])
settings = get_settings()


async def _perform_login(
    db: AsyncSession,
    response: Response,
    email_or_username: str,
    password_str: str,
) -> LoginResponse:
    """Helper to authenticate user and issue JWT token + cookie."""
    result = await db.execute(
        select(User).where(or_(User.email == email_or_username, User.username == email_or_username))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password_str, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # JWT payload embedded with role & checkpoint location
    user_email = user.email or user.username or "officer@mha.gov.in"
    token_data = {
        "sub": user_email,
        "role": user.role,
        "checkpoint_location": user.checkpoint_location,
    }
    token = create_access_token(token_data)

    # Set HttpOnly cookie
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )

    user_dto = UserDTO(
        email=user_email,
        role=user.role,
        checkpoint_location=user.checkpoint_location,
    )

    return LoginResponse(
        success=True,
        message="Authentication successful",
        access_token=token,
        token_type="bearer",
        user=user_dto,
    )


@router.post("/auth/login", response_model=LoginResponse)
@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    body: Optional[LoginRequest] = None,
    email: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate officer or supervisor with email + password.

    Supports both JSON body (`{ "email": "...", "password": "..." }`) and Form Data.
    Returns JWT access_token and embeds role + checkpoint_location in payload.
    """
    target_email = None
    target_password = None

    if body and (body.email or body.username):
        target_email = body.email or body.username
        target_password = body.password
    elif email or username:
        target_email = email or username
        target_password = password
    else:
        # Fallback to json parsing if direct body was raw JSON
        try:
            json_data = await request.json()
            target_email = json_data.get("email") or json_data.get("username")
            target_password = json_data.get("password")
        except Exception:
            pass

    if not target_email or not target_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing email or password",
        )

    return await _perform_login(db, response, target_email, target_password)


@router.post("/auth/logout", response_model=LoginResponse)
@router.post("/logout", response_model=LoginResponse)
async def logout(response: Response) -> LoginResponse:
    """Logout - clears session cookie."""
    response.delete_cookie(key="session", path="/")
    return LoginResponse(success=True, message="Logged out successfully")


@router.get("/auth/me", response_model=AuthMeResponse)
@router.get("/me", response_model=AuthMeResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> AuthMeResponse:
    """Get current authenticated user info."""
    user_email = current_user.email or current_user.username or "officer@mha.gov.in"
    user_dto = UserDTO(
        email=user_email,
        role=current_user.role,
        checkpoint_location=current_user.checkpoint_location,
    )
    return AuthMeResponse(authenticated=True, user=user_dto)