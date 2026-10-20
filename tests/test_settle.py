"""Tests for agent/settle.py end-to-end fiduciary settlement pipeline."""
import ast
import json
from pathlib import Path

import pytest

from agent.settle import settle

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = ROOT / "tests" / "scenarios"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "proofs"


@pytest.mark.parametrize("scenario_file", [
    "sc01_standard_resale.json",
    "sc02_below_reserve.json",
    "sc03_prompt_injection.json",
    "sc04_manager_override.json",
    "sc05_override_below_floor.json",
    "sc06_dust_split.json",
    "sc10_platform_fee.json",
    "sc11_kes_currency.json",
    "sc12_kes_currency_mismatch.json",
])
def test_settle_matches_canonical_fixtures(scenario_file):
    sc_path = SCENARIOS_DIR / scenario_file
    fix_path = FIXTURES_DIR / scenario_file
    with open(sc_path, "r", encoding="utf-8") as f:
        sc = json.load(f)
    with open(fix_path, "r", encoding="utf-8") as f:
        fixture = json.load(f)

    request = sc["input"]
    result = settle(request)

    expected = {k: v for k, v in fixture.items() if k != "producing_layer"}
    actual = {k: v for k, v in result.items() if k != "producing_layer"}
    assert actual == expected


def test_override_both_royalty_and_community_rejected():
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-both-override-1",
        "override": {
            "royalty_bps": 1200,
            "community_bps": 500,
            "rationale": "Valid length justification string for override",
        },
    }
    result = settle(request)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "INVALID_AMOUNT"
    assert result["gross"] == 1000000
    assert result["artist"] == 0
    assert result["community"] == 0
    assert result["pool"] == 0
    assert result["coowners"] == []


def test_override_neither_royalty_nor_community_rejected():
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-neither-override-1",
        "override": {
            "rationale": "Valid length justification string for override",
        },
    }
    result = settle(request)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "INVALID_AMOUNT"


def test_override_short_rationale_rejected():
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-short-rationale-1",
        "override": {
            "royalty_bps": 1200,
            "rationale": "too short",
        },
    }
    result = settle(request)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "INVALID_AMOUNT"


def test_override_invalid_bps_type_rejected():
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-bool-bps-1",
        "override": {
            "royalty_bps": True,
            "rationale": "Valid length justification string for override",
        },
    }
    result = settle(request)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "INVALID_AMOUNT"


def test_override_community_reduction_rejected_by_metta():
    # HFA-101 has 300 bps community cut; manager tries to reduce it to 100 bps
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-comm-reduction-1",
        "override": {
            "community_bps": 100,
            "rationale": "Attempting to reduce community allocation below covenant",
        },
    }
    result = settle(request)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "OVERRIDE_NOT_ALLOWED"
    assert result["gross"] == 1000000
    assert result["artist"] == 0
    assert result["community"] == 0
    assert result["pool"] == 0
    assert result["coowners"] == []


def test_override_community_increase_approved_by_metta():
    # HFA-101 has 300 bps community cut; manager increases to 500 bps
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-comm-increase-1",
        "override": {
            "community_bps": 500,
            "rationale": "Increased community fund grant for neighborhood preservation",
        },
    }
    result = settle(request)
    assert result["status"] == "APPROVED"
    assert result["reason_code"] is None
    assert result["community"] == 50000  # 500 bps of 1,000,000
    assert result["artist"] == 150000   # 1500 bps stored
    assert result["pool"] == 800000


def test_invalid_amount_validation():
    for bad_amount in [-100, 0, 100.5, True, False, "1000000"]:
        req = {
            "artwork_id": "HFA-101",
            "gross_minor": bad_amount,
            "currency": "USD",
            "nonce": f"nonce-bad-amt-{bad_amount}",
        }
        res = settle(req)
        assert res["status"] == "REJECTED"
        assert res["reason_code"] == "INVALID_AMOUNT"


def test_unknown_artwork_fails_closed():
    req = {
        "artwork_id": "UNKNOWN-ARTWORK-999",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-unknown-art-1",
    }
    res = settle(req)
    assert res["status"] == "REJECTED"
    assert res["reason_code"] == "ENGINE_UNAVAILABLE"
    assert res["gross"] == 1000000
    assert res["pool"] == 0
    assert res["coowners"] == []


def test_no_money_math_in_settle_py():
    """Verify settle.py performs zero arithmetic (+, -, *, /, //) on monetary values."""
    settle_file = ROOT / "agent" / "settle.py"
    source = settle_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(settle_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)):
            # Disallow any binary arithmetic on identifiers representing monetary amounts
            line = source.splitlines()[node.lineno - 1]
            # Ensure no arithmetic involving gross, net, fee, artist, community, dust, pool, or proof
            forbidden_tokens = {"gross", "net", "fee", "artist", "community", "dust", "pool", "amount", "proof"}
            op_str = type(node.op).__name__
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and any(tok in child.id.lower() for tok in forbidden_tokens):
                    pytest.fail(f"Money arithmetic detected in settle.py line {node.lineno}: '{line.strip()}' (operator: {op_str})")
