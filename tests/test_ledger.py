
"""Tests for the simulated double-entry ledger."""
import json
from pathlib import Path

import pytest

from agent import ledger
from agent.ledger import post, balances, verify


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "proofs"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(autouse=True)
def isolated_ledger():
    ledger.reset()
    yield
    ledger.reset()


def test_sc01_balances_match_fixture():
    sc01 = load_fixture("sc01_standard_resale.json")
    receipt = post(sc01, nonce="nonce-sc01-ledger")

    assert receipt["status"] == "POSTED"

    result = balances()
    assert result.get("artist", 0) == sc01["artist"]
    assert result.get("community_fund", 0) == (
        sc01["community"] + sc01["dust"]
    )

    for coowner in sc01["coowners"]:
        assert result.get(coowner["owner"], 0) == coowner["amount"]

    assert verify() is True


def test_sc02_rejected_posts_nothing():
    sc02 = load_fixture("sc02_below_reserve.json")
    before = balances()

    receipt = post(sc02, nonce="nonce-sc02-ledger")

    assert receipt["status"] == "REJECTED"
    assert balances() == before
    assert verify() is True


def test_sc06_dust_goes_to_community_fund():
    sc06 = load_fixture("sc06_dust_split.json")
    post(sc06, nonce="nonce-sc06-ledger")

    result = balances()
    assert result.get("community_fund", 0) == (
        sc06["community"] + sc06["dust"]
    )
    assert verify() is True


def test_replayed_nonce_does_not_change_balances():
    sc01 = load_fixture("sc01_standard_resale.json")
    post(sc01, nonce="nonce-replay-001")
    before = balances()

    with pytest.raises(ValueError, match="DUPLICATE_NONCE"):
        post(sc01, nonce="nonce-replay-001")

    assert balances() == before
    assert verify() is True


def test_empty_ledger_is_verified():
    assert verify() is True


def test_float_amount_is_rejected():
    proof = load_fixture("sc01_standard_resale.json")
    proof["gross"] = float(proof["gross"])

    with pytest.raises(ValueError, match="INVALID_AMOUNT"):
        post(proof, nonce="nonce-float")


def test_balances_are_separated_by_currency():
    usd = load_fixture("sc01_standard_resale.json")
    kes = load_fixture("sc11_kes_currency.json")

    post(usd, nonce="nonce-usd")
    post(kes, nonce="nonce-kes")

    result = ledger.balances_by_currency()

    assert "USD" in result
    assert "KES" in result
    assert result["USD"].get("artist", 0) == usd["artist"]
    assert result["KES"].get("artist", 0) == kes["artist"]


def test_sc06_dust_is_a_separate_ledger_entry():
    sc06 = load_fixture("sc06_dust_split.json")
    post(sc06, nonce="nonce-sc06-separate-dust")

    community_entries = [
        entry
        for entry in ledger._ENTRIES
        if entry.get("account") == "community_fund"
    ]

    assert len(community_entries) == 2
    assert balances().get("community_fund", 0) == 1


def test_reset_clears_ledger():
    sc01 = load_fixture("sc01_standard_resale.json")
    post(sc01, nonce="nonce-reset")

    ledger.reset()

    assert ledger._ENTRIES == []
    assert ledger._TRANSACTIONS == []
    assert ledger._NONCES == set()
    assert verify() is True


def test_ledger_empty_state_returns_clean_status():
    ledger.reset()
    st = ledger.status()
    assert st["status"] == "LEDGER_INITIALIZED_ZERO_ENTRIES"
    assert st["transaction_count"] == 0
    assert st["entry_count"] == 0
    assert st["balances"] == {}
    assert verify() is True
