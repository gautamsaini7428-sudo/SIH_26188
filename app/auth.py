from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.config import get_settings
from app.database import get_db
from app.models import User

settings = get_settings()

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

SECRET_KEY = settings.session_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "access_token_expire_minutes", 480)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = None

    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email_or_username = payload.get("sub")
    if not email_or_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query by email or username
    result = await db.execute(
        select(User).where(or_(User.email == email_or_username, User.username == email_or_username))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_officer(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that only users with OFFICER role can execute document verification."""
    if current_user.role.upper() != "OFFICER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Officer role required for verification intake. Supervisors must use review console.",
        )
    return current_user


async def require_supervisor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that only users with SUPERVISOR role can access supervisor endpoints."""
    if current_user.role.upper() != "SUPERVISOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor access required for this operation",
        )
    return current_user


get_current_supervisor = require_supervisor


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that only users with ADMIN or SUPERVISOR role can access admin operations."""
    if current_user.role.upper() not in ("ADMIN", "SUPERVISOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return current_user


get_current_admin = require_admin


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)