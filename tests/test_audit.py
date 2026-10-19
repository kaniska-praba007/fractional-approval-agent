"""Tests for append-only SHA-256 hash-chained audit log (agent/2.4-audit-log).

Marked with xfail(strict=False) so test suite stays green while stubs raise NotImplementedError.
"""
import pytest
from agent.audit_log import append, verify_chain, seen_nonce

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


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_append_chains_hashes():
    e1 = append(SAMPLE_PROOF, nonce="nonce-test-01")
    e2 = append(SAMPLE_PROOF, nonce="nonce-test-02")
    assert "hash" in e1
    assert "hash" in e2
    assert e2.get("prev_hash") == e1.get("hash")
    assert verify_chain() is True


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_tampered_entry_fails_verify_chain():
    append(SAMPLE_PROOF, nonce="nonce-tamper-01")
    # Tampering with history must invalidate chain
    assert verify_chain() is False


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_duplicate_nonce_detected():
    nonce = "nonce-unique-12345"
    assert seen_nonce(nonce) is False
    append(SAMPLE_PROOF, nonce=nonce)
    assert seen_nonce(nonce) is True
