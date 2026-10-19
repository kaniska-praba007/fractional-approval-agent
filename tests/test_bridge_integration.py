"""REAL integration tests: execute the actual installed Hyperon/MeTTa runtime.
No mocks. Skipped (not passed) if `hyperon` is not installed.
Run only these:  pytest -m integration -v
Omega is NOT exercised here (see docs/OMEGA_INTEGRATION.md)."""
from pathlib import Path

import pytest

pytest.importorskip("hyperon")

from agent.bridge import Fact, ReasoningRequest, ReasoningStatus, run_reasoning  # noqa: E402

pytestmark = pytest.mark.integration

RULES = Path("metta/ownership_demo.metta")
REL = frozenset({"owner-of", "member-of"})


def req(facts, artwork="artwork1"):
    return ReasoningRequest(rule_file=RULES, facts=facts, query_function="collective-owner",
                            query_args=(artwork,), allowed_relations=REL)


def test_real_known_input_yields_expected_conclusion():
    r = run_reasoning(req([Fact("owner-of", ("artwork1", "alice")),
                           Fact("member-of", ("alice", "collective1"))]))
    assert r.status is ReasoningStatus.SUCCESS
    assert r.conclusions == ("collective1",)
    assert r.engine_version  # recorded
    assert r.raw_output == "[[collective1]]"


def test_real_missing_premise_is_no_result():
    r = run_reasoning(req([Fact("owner-of", ("artwork1", "alice"))]))
    assert r.status is ReasoningStatus.NO_RESULT and not r.ok


def test_real_no_facts_is_no_result():
    assert run_reasoning(req([])).status is ReasoningStatus.NO_RESULT


def test_real_reversed_relation_does_not_conclude():
    r = run_reasoning(req([Fact("owner-of", ("alice", "artwork1")),
                           Fact("member-of", ("alice", "collective1"))]))
    assert r.status is ReasoningStatus.NO_RESULT


def test_real_unknown_artwork_is_no_result():
    r = run_reasoning(req([Fact("owner-of", ("artwork1", "alice")),
                           Fact("member-of", ("alice", "collective1"))], artwork="artwork2"))
    assert r.status is ReasoningStatus.NO_RESULT


def test_real_unknown_query_function_not_treated_as_success():
    r = ReasoningRequest(rule_file=RULES, facts=[], query_function="no-such-rule",
                         query_args=("artwork1",), allowed_relations=REL)
    out = run_reasoning(r)
    assert out.status is ReasoningStatus.ENGINE_ERROR and not out.ok


def test_real_malformed_rule_file_is_engine_error(tmp_path):
    bad = tmp_path / "bad.metta"
    bad.write_text("(= (broken $x) (unclosed", encoding="utf-8")
    r = ReasoningRequest(rule_file=bad, facts=[], query_function="broken",
                         query_args=("a",), allowed_relations=REL)
    out = run_reasoning(r)
    assert out.status is ReasoningStatus.ENGINE_ERROR and out.diagnostics


def test_real_stable_across_runs():
    facts = [Fact("owner-of", ("artwork1", "alice")), Fact("member-of", ("alice", "collective1"))]
    assert {run_reasoning(req(facts)).conclusions for _ in range(5)} == {("collective1",)}
