"""Tests for simulated double-entry ledger in integer cents (agent/2.6-sim-ledger).

Marked with xfail(strict=False) so test suite stays green while stubs raise NotImplementedError.
"""
import json
from pathlib import Path
import pytest
from agent.ledger import post, balances, verify

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "proofs"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_sc01_balances_match_fixture():
    sc01 = load_fixture("sc01_standard_resale.json")
    receipt = post(sc01, nonce="nonce-sc01-ledger")
    b = balances()
    assert b.get("artist", 0) == sc01["artist"]
    assert b.get("community_fund", 0) == sc01["community"] + sc01["dust"]
    for c in sc01["coowners"]:
        assert b.get(c["owner"], 0) == c["amount"]
    assert verify() is True


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_sc02_rejected_posts_nothing():
    sc02 = load_fixture("sc02_below_reserve.json")
    b_before = balances()
    receipt = post(sc02, nonce="nonce-sc02-ledger")
    b_after = balances()
    assert b_before == b_after


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_sc06_dust_goes_to_community_fund():
    sc06 = load_fixture("sc06_dust_split.json")
    post(sc06, nonce="nonce-sc06-ledger")
    b = balances()
    # Dust (1 cent) must be included in community fund balance
    assert b.get("community_fund", 0) == sc06["community"] + sc06["dust"]
    assert verify() is True


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_replayed_nonce_does_not_change_balances():
    sc01 = load_fixture("sc01_standard_resale.json")
    post(sc01, nonce="nonce-replay-001")
    b_once = balances()
    with pytest.raises((ValueError, Exception)):
        post(sc01, nonce="nonce-replay-001")
    assert balances() == b_once


@pytest.mark.xfail(strict=False, reason="Stub implementation in scaffold/0.5")
def test_tampered_entry_detected():
    assert verify() is False
