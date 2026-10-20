
"""Tests for append-only SHA-256 hash-chained audit log."""
import json

import pytest

from agent import audit_log
from agent.audit_log import (
    AuditError,
    append,
    seen_nonce,
    verify_chain,
    verify_chain_details,
)


SAMPLE_PROOF = {
    "status": "APPROVED",
    "reason_code": None,
    "artwork_id": "HFA-101",
    "currency": "USD",
    "gross": 1000000,
    "fee": 0,
    "artist": 150000,
    "community": 30000,
    "dust": 0,
    "pool": 820000,
    "coowners": [
        {"owner": "alice", "wallet": "0xalice", "amount": 492000},
        {"owner": "bob", "wallet": "0xbob", "amount": 328000},
    ],
    "producing_layer": "bridge/MeTTa",
}


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audit_log, "AUDIT_LOG_PATH", tmp_path / "audit_log.json"
    )


def test_append_chains_hashes():
    e1 = append(SAMPLE_PROOF, nonce="nonce-test-01")
    e2 = append(SAMPLE_PROOF, nonce="nonce-test-02")

    assert "hash" in e1
    assert "hash" in e2
    assert e1["prev_hash"] == "0" * 64
    assert e2["prev_hash"] == e1["hash"]
    assert verify_chain() is True


def test_tampered_entry_fails_verify_chain():
    append(SAMPLE_PROOF, nonce="nonce-tamper-01")

    path = audit_log.AUDIT_LOG_PATH
    entries = json.loads(path.read_text(encoding="utf-8"))
    entries[0]["proof"]["gross"] = 999999
    path.write_text(json.dumps(entries), encoding="utf-8")

    assert verify_chain() is False


def test_duplicate_nonce_detected():
    nonce = "nonce-unique-12345"

    assert seen_nonce(nonce) is False
    append(SAMPLE_PROOF, nonce=nonce)
    assert seen_nonce(nonce) is True

    with pytest.raises(AuditError, match="DUPLICATE_NONCE"):
        append(SAMPLE_PROOF, nonce=nonce)


def test_float_values_are_rejected():
    proof = {**SAMPLE_PROOF, "gross": 10.5}

    with pytest.raises(AuditError, match="FLOAT_NOT_ALLOWED"):
        append(proof, nonce="nonce-float")


def test_corrupted_chain_blocks_append():
    append(SAMPLE_PROOF, nonce="nonce-first")

    path = audit_log.AUDIT_LOG_PATH
    entries = json.loads(path.read_text(encoding="utf-8"))
    entries[0]["hash"] = "f" * 64
    path.write_text(json.dumps(entries), encoding="utf-8")

    with pytest.raises(AuditError, match="AUDIT_CHAIN_INVALID"):
        append(SAMPLE_PROOF, nonce="nonce-second")


def test_audit_verify_chain_details_structured():
    details = verify_chain_details()
    assert details["verified"] is True
    assert details["block_count"] == 0
    assert details["status"] == "AUDIT_LOG_EMPTY_GENESIS"

    append(SAMPLE_PROOF, nonce="nonce-struct-01")
    append(SAMPLE_PROOF, nonce="nonce-struct-02")

    details = verify_chain_details()
    assert details["verified"] is True
    assert details["block_count"] == 2
    assert details["status"] == "VALID"


def test_duplicate_nonce_returns_structured_rejection_and_logs():
    from agent.settle import settle

    nonce = "nonce-settle-replay-999"
    req = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": nonce,
    }

    first_res = settle(req, audit=audit_log)
    assert first_res["status"] == "APPROVED"
    assert seen_nonce(nonce) is True

    replay_res = settle(req, audit=audit_log)
    assert replay_res["status"] == "REJECTED"
    assert replay_res["reason_code"] == "DUPLICATE_NONCE"
    assert replay_res["producing_layer"] == "audit_log"

    entries = json.loads(audit_log.AUDIT_LOG_PATH.read_text(encoding="utf-8"))
    assert len(entries) == 2
    assert entries[0]["proof"]["status"] == "APPROVED"
    assert entries[1]["proof"]["status"] == "REJECTED"
    assert entries[1]["proof"]["reason_code"] == "DUPLICATE_NONCE"
    assert verify_chain() is True
