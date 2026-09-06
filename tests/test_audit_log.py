import json
import pytest
from app.services.audit_log import (
    log_verification,
    verify_audit_chain,
    get_all_records,
    GENESIS_HASH,
)

@pytest.fixture
def audit_env(tmp_path):
    return str(tmp_path / "audit_store.json")

def _dummy_record(doc_id="DOC-100", verdict="VERIFIED", tampering=10, face=85):
    return {
        "timestamp": "2026-09-02T12:00:00Z",
        "document_id": doc_id,
        "verdict": verdict,
        "tampering_score": tampering,
        "face_match_score": face,
    }

def test_empty_chain_validation(audit_env):
    res = verify_audit_chain(filepath=audit_env)
    assert res["valid"] is True
    assert res["entries_checked"] == 0

def test_strict_schema_enforcement(audit_env):
    with pytest.raises(ValueError):
        log_verification({"document_id": "DOC-1"}, filepath=audit_env)

def test_single_and_multi_append(audit_env):
    h1 = log_verification(_dummy_record("DOC-1"), filepath=audit_env)
    h2 = log_verification(_dummy_record("DOC-2"), filepath=audit_env)
    records = get_all_records(filepath=audit_env)
    assert len(records) == 2
    assert records[0]["previous_hash"] == GENESIS_HASH
    assert records[0]["hash"] == h1
    assert records[1]["previous_hash"] == h1
    assert records[1]["hash"] == h2

def test_tamper_detection_in_record(audit_env):
    for i in range(4):
        log_verification(_dummy_record(f"DOC-{i}"), filepath=audit_env)
    with open(audit_env, "r", encoding="utf-8") as f:
        data = json.load(f)
    data[2]["record"]["verdict"] = "REJECTED"
    with open(audit_env, "w", encoding="utf-8") as f:
        json.dump(data, f)
    audit = verify_audit_chain(filepath=audit_env)
    assert audit["valid"] is False
    assert audit["tampered_index"] == 2

def test_corrupted_json_handling(audit_env):
    with open(audit_env, "w", encoding="utf-8") as f:
        f.write("{corrupt_json: true, broken")
    audit = verify_audit_chain(filepath=audit_env)
    assert audit["valid"] is False
    assert "corrupted" in audit["reason"].lower()
