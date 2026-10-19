"""Tests for bridge hardening: strict input validation and Hyperon Atom API fact building."""
from pathlib import Path
import pytest

from agent.bridge import Fact, ReasoningRequest, ReasoningStatus, run_reasoning

RULES = Path("metta/ownership_demo.metta")
REL = frozenset({"owner-of", "member-of", "artwork-reserve"})


def make_req(query_args=("artwork1",), facts=None):
    if facts is None:
        facts = [Fact("owner-of", ("artwork1", "alice"))]
    return ReasoningRequest(
        rule_file=RULES,
        facts=facts,
        query_function="collective-owner",
        query_args=query_args,
        allowed_relations=REL,
    )


def test_invalid_query_args_rejected():
    invalid_cases = [
        "(bad)",
        "a b",
        "",
        "HFA-101)",
        "(+ 1 2)",  # nested expression
        "\"quoted\"",
        "'singlequoted'",
        ("(nested)",),  # nested tuple expression
    ]
    for bad in invalid_cases:
        res = run_reasoning(make_req(query_args=(bad,)))
        assert res.status is ReasoningStatus.INVALID_INPUT, f"Expected INVALID_INPUT for query_arg: {bad!r}"


def test_invalid_fact_args_rejected():
    invalid_cases = [
        "(bad)",
        "a b",
        "",
        "HFA-101)",
        "(cons-share x)",  # nested expression
        "\"quoted\"",
        "'singlequoted'",
        ("nested", "tuple"),
    ]
    for bad in invalid_cases:
        facts = [Fact("owner-of", (bad, "alice"))]
        res = run_reasoning(make_req(facts=facts))
        assert res.status is ReasoningStatus.INVALID_INPUT, f"Expected INVALID_INPUT for fact arg: {bad!r}"


def test_valid_identifiers_pass():
    for valid in ("HFA-101", "TEST-DUST"):
        res = run_reasoning(make_req(query_args=(valid,)))
        assert res.status != ReasoningStatus.INVALID_INPUT, f"Expected {valid!r} to pass validation"
