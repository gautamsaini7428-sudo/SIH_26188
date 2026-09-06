"""
Tamper-Evident SHA-256 Hash Chain Audit Service
Module 2 - SIH Problem Statement 26188
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from filelock import FileLock
from pydantic import BaseModel, Field, ValidationError

DEFAULT_AUDIT_PATH = os.path.abspath(os.getenv("AUDIT_LOG_FILE", "audit_log.json"))
LOCK_TIMEOUT_SECONDS = 5.0
GENESIS_HASH = "0" * 64


class VerificationRecordSchema(BaseModel):
    document_id: str = Field(..., min_length=1, max_length=128)
    verdict: str = Field(..., pattern="^(VERIFIED|SUSPECTED|REJECTED|ERROR)$")
    tampering_score: int = Field(..., ge=0, le=100)
    face_match_score: int = Field(..., ge=0, le=100)
    timestamp: str = Field(..., min_length=10)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def calculate_hash(previous_hash: str, record: Dict[str, Any]) -> str:
    payload = f"{previous_hash}{_canonical_json(record)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_lock(filepath: str) -> FileLock:
    return FileLock(f"{filepath}.lock", timeout=LOCK_TIMEOUT_SECONDS)


def _read_chain_raw(filepath: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    if not os.path.exists(filepath):
        return [], None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return [], None
            data = json.loads(content)
            if not isinstance(data, list):
                return None, "Root audit log element is not a valid JSON array."
            return data, None
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, f"Audit log file contains malformed/corrupted JSON: {str(exc)}"
    except OSError as exc:
        return None, f"Operating system file read error: {str(exc)}"


def _write_chain_atomic(chain: List[Dict[str, Any]], filepath: str) -> None:
    target_dir = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(target_dir, exist_ok=True)
    temp_file = f"{filepath}.tmp.{os.getpid()}"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(chain, f, indent=2, ensure_ascii=True)
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_file, filepath)


def log_verification(record: Dict[str, Any], filepath: str = DEFAULT_AUDIT_PATH) -> str:
    try:
        validated = VerificationRecordSchema(**record)
        sanitized_record = validated.model_dump()
    except ValidationError as exc:
        raise ValueError(f"Audit log record schema validation failed: {exc}") from exc

    lock = _get_lock(filepath)
    with lock:
        chain, err = _read_chain_raw(filepath)
        if err:
            raise IOError(f"Cannot append to an unreadable or corrupt audit chain: {err}")

        if not chain:
            previous_hash = GENESIS_HASH
            new_index = 0
        else:
            previous_hash = chain[-1]["hash"]
            new_index = chain[-1]["index"] + 1

        entry_hash = calculate_hash(previous_hash, sanitized_record)

        entry = {
            "index": new_index,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "record": sanitized_record,
            "previous_hash": previous_hash,
            "hash": entry_hash,
        }

        chain.append(entry)
        _write_chain_atomic(chain, filepath)
        return entry_hash


def get_all_records(filepath: str = DEFAULT_AUDIT_PATH) -> List[Dict[str, Any]]:
    lock = _get_lock(filepath)
    with lock:
        chain, err = _read_chain_raw(filepath)
        if err:
            raise IOError(err)
        return chain or []


def verify_audit_chain(filepath: str = DEFAULT_AUDIT_PATH) -> Dict[str, Any]:
    lock = _get_lock(filepath)
    with lock:
        chain, err = _read_chain_raw(filepath)

    if err:
        return {
            "valid": False,
            "entries_checked": 0,
            "tampered_index": None,
            "reason": f"Audit file corrupted: {err}",
        }

    if not chain:
        return {
            "valid": True,
            "entries_checked": 0,
            "tampered_index": None,
            "reason": "Audit chain is empty.",
        }

    for i, entry in enumerate(chain):
        if entry.get("index") != i:
            return {
                "valid": False,
                "entries_checked": i,
                "tampered_index": i,
                "reason": f"Index discontinuity detected at position {i}.",
            }

        prev_hash = entry.get("previous_hash")
        rec = entry.get("record")
        stored_hash = entry.get("hash")

        if i == 0:
            if prev_hash != GENESIS_HASH:
                return {
                    "valid": False,
                    "entries_checked": 0,
                    "tampered_index": 0,
                    "reason": f"Genesis block points to invalid previous hash '{prev_hash}'.",
                }
        else:
            parent_hash = chain[i - 1].get("hash")
            if prev_hash != parent_hash:
                return {
                    "valid": False,
                    "entries_checked": i,
                    "tampered_index": i,
                    "reason": f"Hash chain linkage broken at index {i}.",
                }

        recalculated_hash = calculate_hash(prev_hash, rec)
        if recalculated_hash != stored_hash:
            return {
                "valid": False,
                "entries_checked": i,
                "tampered_index": i,
                "reason": f"Cryptographic signature mismatch at index {i}.",
            }

    return {
        "valid": True,
        "entries_checked": len(chain),
        "tampered_index": None,
        "reason": "Audit chain cryptographic integrity verified successfully.",
    }
