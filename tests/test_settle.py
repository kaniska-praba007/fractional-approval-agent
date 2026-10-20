"""Tests for agent/settle.py end-to-end fiduciary settlement pipeline."""
import ast
import json
from pathlib import Path
from typing import Any

import pytest

from agent.settle import settle

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = ROOT / "tests" / "scenarios"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "proofs"


class FakeAuditLog:
    def __init__(self, seen_nonces: list[str] | None = None, raise_on_append: bool = False, raise_on_seen: bool = False):
        self.seen_nonces = set(seen_nonces or [])
        self.appended: list[tuple[dict, str]] = []
        self.raise_on_append = raise_on_append
        self.raise_on_seen = raise_on_seen
        self.call_log: list[str] = []

    def seen_nonce(self, nonce: str) -> bool:
        self.call_log.append(f"seen_nonce:{nonce}")
        if self.raise_on_seen:
            raise NotImplementedError("Audit log seen_nonce stub")
        return nonce in self.seen_nonces

    def append(self, proof: dict, nonce: str) -> dict:
        self.call_log.append(f"append:{nonce}")
        if self.raise_on_append:
            raise RuntimeError("Audit log append failed to write block")
        self.appended.append((proof, nonce))
        self.seen_nonces.add(nonce)
        return {"index": len(self.appended), "nonce": nonce, "hash": "0xabc123"}


class FakeLedger:
    def __init__(self, raise_on_post: bool = False):
        self.posted: list[tuple[dict, str | None]] = []
        self.raise_on_post = raise_on_post
        self.call_log: list[str] = []

    def post(self, proof: dict, nonce: str | None = None) -> dict:
        self.call_log.append(f"post:{proof.get('status')}")
        if self.raise_on_post:
            raise RuntimeError("Ledger post failed")
        self.posted.append((proof, nonce))
        return {"transaction_id": f"tx-{len(self.posted)}", "status": "POSTED"}


class FakeParser:
    def __init__(self, return_dict: dict | None = None, raise_error: bool = False):
        self.return_dict = return_dict
        self.raise_error = raise_error
        self.called_with: list[str] = []

    def parse_request(self, text: str) -> dict:
        self.called_with.append(text)
        if self.raise_error:
            raise ValueError(f"Ambiguous or malformed bid text: {text}")
        return self.return_dict or {}


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

    audit = FakeAuditLog()
    ledger = FakeLedger()
    request = sc["input"]
    result = settle(request, audit=audit, ledger=ledger)

    expected = {k: v for k, v in fixture.items() if k != "producing_layer"}
    actual = {k: v for k, v in result.items() if k != "producing_layer"}
    assert actual == expected


def test_sc07_duplicate_nonce_rejected_before_bridge():
    audit = FakeAuditLog(seen_nonces=["nonce-sc01-998811"])
    ledger = FakeLedger()
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-sc01-998811",
    }
    result = settle(request, audit=audit, ledger=ledger)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "DUPLICATE_NONCE"
    assert result["producing_layer"] == "audit_log"
    assert len(ledger.posted) == 0
    assert len(audit.appended) == 1
    assert audit.appended[0][0]["status"] == "REJECTED"
    assert audit.appended[0][1] == "nonce-sc01-998811"


def test_sc08_unknown_artwork_engine_failure_nothing_posted():
    audit = FakeAuditLog()
    ledger = FakeLedger()
    request = {
        "artwork_id": "UNKNOWN-ARTWORK-999",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-sc08-337700",
    }
    result = settle(request, audit=audit, ledger=ledger)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "ENGINE_UNAVAILABLE"
    assert len(ledger.posted) == 0
    assert len(audit.appended) == 1
    assert audit.appended[0][0]["status"] == "REJECTED"


def test_sc09_offline_text_request_parsed_approved():
    parser = FakeParser(return_dict={
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
    })
    audit = FakeAuditLog()
    ledger = FakeLedger()
    request = {
        "text": "Bid $10,000 for HFA-101",
        "nonce": "nonce-sc09-112233",
    }
    result = settle(request, offline=True, parser=parser, audit=audit, ledger=ledger)
    assert result["status"] == "APPROVED"
    assert result["reason_code"] is None
    assert result["artwork_id"] == "HFA-101"
    assert result["gross"] == 1000000
    assert result["producing_layer"] == "parser"
    assert len(audit.appended) == 1
    assert len(ledger.posted) == 1


def test_sc09_parser_failure_malformed_output():
    parser = FakeParser(raise_error=True)
    audit = FakeAuditLog()
    ledger = FakeLedger()
    request = {
        "text": "I offer somewhere between 10k and 15k maybe",
        "nonce": "nonce-malformed-99",
    }
    result = settle(request, offline=True, parser=parser, audit=audit, ledger=ledger)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "LLM_MALFORMED_OUTPUT"
    assert result["producing_layer"] == "parser"
    assert len(ledger.posted) == 0
    assert len(audit.appended) == 1


def test_call_order_approved_audit_then_ledger():
    event_order: list[str] = []

    class OrderTrackingAudit(FakeAuditLog):
        def append(self, proof: dict, nonce: str) -> dict:
            event_order.append("audit_append")
            return super().append(proof, nonce)

    class OrderTrackingLedger(FakeLedger):
        def post(self, proof: dict, nonce: str | None = None) -> dict:
            event_order.append("ledger_post")
            return super().post(proof, nonce)

    audit = OrderTrackingAudit()
    ledger = OrderTrackingLedger()
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-order-test-1",
    }
    result = settle(request, audit=audit, ledger=ledger)
    assert result["status"] == "APPROVED"
    assert event_order == ["audit_append", "ledger_post"]


def test_rejected_calls_audit_append_not_ledger_post():
    audit = FakeAuditLog()
    ledger = FakeLedger()
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 200000,  # Below reserve 300,000
        "currency": "USD",
        "nonce": "nonce-reject-order-1",
    }
    result = settle(request, audit=audit, ledger=ledger)
    assert result["status"] == "REJECTED"
    assert len(audit.appended) == 1
    assert len(ledger.posted) == 0


def test_audit_append_raises_fails_closed():
    audit = FakeAuditLog(raise_on_append=True)
    ledger = FakeLedger()
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-append-fail-1",
    }
    result = settle(request, audit=audit, ledger=ledger)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "ENGINE_UNAVAILABLE"
    assert "diagnostics" in result
    assert len(ledger.posted) == 0


def test_stub_not_implemented_fails_closed_with_diagnostics():
    audit = FakeAuditLog(raise_on_seen=True)
    ledger = FakeLedger()
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-stub-fail-1",
    }
    result = settle(request, audit=audit, ledger=ledger)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "ENGINE_UNAVAILABLE"
    assert "NotImplementedError" in result.get("diagnostics", "")
    assert len(ledger.posted) == 0


def test_missing_nonce_when_audit_used_rejected():
    audit = FakeAuditLog()
    ledger = FakeLedger()
    request = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        # nonce missing
    }
    result = settle(request, audit=audit, ledger=ledger)
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "INVALID_AMOUNT"


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
    result = settle(request, audit=FakeAuditLog(), ledger=FakeLedger())
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
    result = settle(request, audit=FakeAuditLog(), ledger=FakeLedger())
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
    result = settle(request, audit=FakeAuditLog(), ledger=FakeLedger())
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
    result = settle(request, audit=FakeAuditLog(), ledger=FakeLedger())
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "INVALID_AMOUNT"


def test_override_community_reduction_rejected_by_metta():
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
    result = settle(request, audit=FakeAuditLog(), ledger=FakeLedger())
    assert result["status"] == "REJECTED"
    assert result["reason_code"] == "OVERRIDE_NOT_ALLOWED"
    assert result["gross"] == 1000000
    assert result["artist"] == 0
    assert result["community"] == 0
    assert result["pool"] == 0
    assert result["coowners"] == []


def test_override_community_increase_approved_by_metta():
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
    result = settle(request, audit=FakeAuditLog(), ledger=FakeLedger())
    assert result["status"] == "APPROVED"
    assert result["reason_code"] is None
    assert result["community"] == 50000
    assert result["artist"] == 150000
    assert result["pool"] == 800000


def test_invalid_amount_validation():
    for bad_amount in [-100, 0, 100.5, True, False, "1000000"]:
        req = {
            "artwork_id": "HFA-101",
            "gross_minor": bad_amount,
            "currency": "USD",
            "nonce": f"nonce-bad-amt-{bad_amount}",
        }
        res = settle(req, audit=FakeAuditLog(), ledger=FakeLedger())
        assert res["status"] == "REJECTED"
        assert res["reason_code"] == "INVALID_AMOUNT"


def test_unknown_artwork_fails_closed():
    req = {
        "artwork_id": "UNKNOWN-ARTWORK-999",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-unknown-art-1",
    }
    res = settle(req, audit=FakeAuditLog(), ledger=FakeLedger())
    assert res["status"] == "REJECTED"
    assert res["reason_code"] == "ENGINE_UNAVAILABLE"
    assert res["gross"] == 1000000
    assert res["pool"] == 0
    assert res["coowners"] == []


@pytest.mark.xfail(reason="Teammate stubs in agent.audit_log and agent.ledger not merged into main yet")
def test_real_modules_end_to_end_xfail():
    """Real modules stub wiring: xfails until teammate branches merge into main."""
    req = {
        "artwork_id": "HFA-101",
        "gross_minor": 1000000,
        "currency": "USD",
        "nonce": "nonce-real-modules-1",
    }
    res = settle(req)
    assert res["status"] == "APPROVED"


def test_no_money_math_in_settle_py():
    """Verify settle.py performs zero arithmetic (+, -, *, /, //) on monetary values."""
    settle_file = ROOT / "agent" / "settle.py"
    source = settle_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(settle_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)):
            line = source.splitlines()[node.lineno - 1]
            forbidden_tokens = {"gross", "net", "fee", "artist", "community", "dust", "pool", "amount", "proof"}
            op_str = type(node.op).__name__
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and any(tok in child.id.lower() for tok in forbidden_tokens):
                    pytest.fail(f"Money arithmetic detected in settle.py line {node.lineno}: '{line.strip()}' (operator: {op_str})")
