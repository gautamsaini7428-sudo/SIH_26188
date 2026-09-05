"""
Async File Upload Handler

Handles secure file uploads with validation, unique naming, and cleanup.
"""

import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".bmp", ".tiff", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
    "image/bmp",
    "image/tiff",
    "image/webp",
}


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    # Check extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check MIME type (basic check, can be spoofed)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type not allowed: {file.content_type}",
        )


async def save_upload_file(file: UploadFile, subdir: str = "") -> str:
    """
    Save uploaded file asynchronously with unique name.

    Args:
        file: FastAPI UploadFile object
        subdir: Optional subdirectory under UPLOAD_DIR

    Returns:
        Relative path to saved file (for database storage)
    """
    validate_file(file)

    upload_dir = Path(settings.upload_dir) / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    ext = Path(file.filename or "").suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / unique_name

    # Read and validate size before creating on disk
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB",
        )

    # Save asynchronously
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Return relative path from upload_dir
    return str(file_path.relative_to(settings.upload_dir))


def get_file_url(relative_path: str) -> str:
    """Convert relative path to accessible URL (for frontend)."""
    return f"/uploads/{relative_path}"


def delete_file(relative_path: str) -> bool:
    """Delete a file by relative path."""
    try:
        full_path = Path(settings.upload_dir) / relative_path
        if full_path.exists():
            full_path.unlink()
            return True
    except Exception:
        pass
    return False


def file_exists(relative_path: str) -> bool:
    """Check if file exists."""
    full_path = Path(settings.upload_dir) / relative_path
    return full_path.exists()