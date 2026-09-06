"""
Audit Log Router
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from app.services.audit_log import get_all_records, verify_audit_chain

router = APIRouter(prefix="/audit-log", tags=["Audit Log"])


@router.get("", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def read_audit_log():
    try:
        return get_all_records()
    except IOError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to access audit log store: {str(exc)}",
        )


@router.get("/verify", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def verify_log_integrity():
    return verify_audit_chain()
