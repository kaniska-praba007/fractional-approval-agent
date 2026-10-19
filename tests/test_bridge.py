"""UNIT tests for agent.bridge. These use a fake runner for failure paths and
do NOT prove the real Hyperon runtime works. See test_bridge_integration.py."""
import time
from pathlib import Path

from agent.bridge import Fact, ReasoningRequest, ReasoningStatus, run_reasoning

RULES = Path("metta/ownership_demo.metta")
REL = frozenset({"owner-of", "member-of"})


def req(**kw):
    base = dict(rule_file=RULES, facts=[Fact("owner-of", ("artwork1", "alice"))],
                query_function="collective-owner", query_args=("artwork1",), allowed_relations=REL)
    base.update(kw)
    return ReasoningRequest(**base)


def fake(output):
    return lambda program: output


def test_unit_success_shape():
    r = run_reasoning(req(), _runner=fake([["collective1"]]))
    assert r.status is ReasoningStatus.SUCCESS and r.conclusions == ("collective1",) and r.ok


def test_unit_empty_is_no_result_not_ok():
    r = run_reasoning(req(), _runner=fake([[]]))
    assert r.status is ReasoningStatus.NO_RESULT and not r.ok and r.conclusions == ()


def test_unit_unreduced_expression_is_engine_error():
    r = run_reasoning(req(), _runner=fake([["(collective-owner artwork1 $result)"]]))
    assert r.status is ReasoningStatus.ENGINE_ERROR and not r.ok


def test_unit_error_atom_is_engine_error():
    r = run_reasoning(req(), _runner=fake([["(Error x BadType)"]]))
    assert r.status is ReasoningStatus.ENGINE_ERROR


def test_unit_unexpected_shape_is_engine_error():
    for bad in (None, [], [[], []], "x"):
        assert run_reasoning(req(), _runner=fake(bad)).status is ReasoningStatus.ENGINE_ERROR


def test_unit_runtime_exception_is_engine_error_with_diagnostics():
    def boom(_):
        raise RuntimeError("Unexpected end of expression")
    r = run_reasoning(req(), _runner=boom)
    assert r.status is ReasoningStatus.ENGINE_ERROR and "Unexpected end" in r.diagnostics
    assert r.program  # preserved for debugging


def test_unit_missing_runtime_is_engine_error():
    def missing(_):
        raise ImportError("No module named 'hyperon'")
    assert run_reasoning(req(), _runner=missing).status is ReasoningStatus.ENGINE_ERROR


def test_unit_timeout():
    r = run_reasoning(req(), timeout_s=0.05, _runner=lambda p: time.sleep(0.5))
    assert r.status is ReasoningStatus.TIMEOUT and not r.ok


def test_unit_invalid_inputs():
    cases = [
        req(query_args=("artwork1) (shell",)),            # injection attempt
        req(query_function="a b"),
        req(facts=[Fact("owner-of", ("x", "y z"))]),
        req(facts=[Fact("owner-of", ("X",))]),             # uppercase rejected
        req(facts=[Fact("evil", ("a", "b"))]),             # not allow-listed
        req(facts=[Fact("owner-of", ())]),
        req(rule_file=Path("does/not/exist.metta")),
    ]
    for c in cases:
        r = run_reasoning(c, _runner=lambda p: (_ for _ in ()).throw(AssertionError("runtime must not run")))
        assert r.status is ReasoningStatus.INVALID_INPUT, c
    assert run_reasoning("not a request").status is ReasoningStatus.INVALID_INPUT
