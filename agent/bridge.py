"""Narrow adapter around the Hyperon (``hyperon`` PyPI package) MeTTa runtime.

This is the *Hyperon/MeTTa* boundary only. It is NOT an Omega integration:
Omega runs on PeTTa/SWI-Prolog and is driven by an LLM loop (see
docs/OMEGA_INTEGRATION.md).

Fail-closed contract: only ``ReasoningStatus.SUCCESS`` carries conclusions.
Every other status (no_result, invalid_input, engine_error, timeout) means
"no conclusion" and must never be treated as an approval by callers.

Safety: callers pass *validated tokens*, never raw MeTTa text. Facts and the
query are built from identifiers matching ``_IDENT`` and relations from an
explicit allow-list, so user text cannot inject executable expressions. The
rule file is a trusted repository file selected by the application.
"""
from __future__ import annotations

import concurrent.futures
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Sequence

_IDENT = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_DEFAULT_TIMEOUT_S = 10.0


class ReasoningStatus(str, Enum):
    SUCCESS = "success"
    NO_RESULT = "no_result"
    INVALID_INPUT = "invalid_input"
    ENGINE_ERROR = "engine_error"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class Fact:
    relation: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class ReasoningRequest:
    """rule_file: trusted .metta file. query_function: head symbol of the query.
    query_args: identifier arguments; one free variable ``$result`` is appended.
    allowed_relations: allow-list of fact relation names."""
    rule_file: Path
    facts: Sequence[Fact]
    query_function: str
    query_args: tuple[str, ...]
    allowed_relations: frozenset[str]


@dataclass(frozen=True)
class ReasoningResult:
    status: ReasoningStatus
    conclusions: tuple[str, ...] = ()
    engine_version: str | None = None
    program: str | None = None  # exact program text executed, for debugging/audit
    raw_output: str | None = None
    diagnostics: str | None = None
    fact_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.status is ReasoningStatus.SUCCESS and bool(self.conclusions)


def _validate(req: ReasoningRequest) -> str | None:
    """Return an error message, or None if the request is well-formed."""
    if not isinstance(req, ReasoningRequest):
        return "request must be a ReasoningRequest"
    if not isinstance(req.rule_file, Path) or not req.rule_file.is_file():
        return "rule_file must be an existing file"
    if not _is_ident(req.query_function):
        return "invalid query_function"
    if not all(_is_ident(a) for a in req.query_args):
        return "invalid query argument"
    for f in req.facts:
        if not isinstance(f, Fact) or f.relation not in req.allowed_relations:
            return "fact relation not in allow-list"
        if not f.args or not all(_is_ident(a) for a in f.args):
            return "invalid fact argument"
    return None


def _is_ident(value: object) -> bool:
    return isinstance(value, str) and bool(_IDENT.match(value))


def _build_program(req: ReasoningRequest) -> str:
    rules = req.rule_file.read_text(encoding="utf-8")
    facts = "\n".join(f"({f.relation} {' '.join(f.args)})" for f in req.facts)
    query = f"!({req.query_function} {' '.join(req.query_args)} $result)"
    return f"{rules}\n{facts}\n{query}\n"


def _engine_version() -> str | None:
    try:
        from importlib.metadata import version
        return version("hyperon")
    except Exception:  # pragma: no cover - metadata absence is non-fatal
        return None


def _run_hyperon(program: str) -> list[list[object]]:
    from hyperon import MeTTa  # imported lazily so a missing runtime is a typed error
    return MeTTa().run(program)


def run_reasoning(req: ReasoningRequest, timeout_s: float = _DEFAULT_TIMEOUT_S,
                  _runner=_run_hyperon) -> ReasoningResult:
    """Run one reasoning request. Never raises; never returns SUCCESS without
    at least one well-formed conclusion.

    ``_runner`` exists only so unit tests can simulate runtime failures; such
    tests do not prove the real runtime works (see tests/test_bridge_integration.py).
    """
    problem = _validate(req)
    if problem:
        return ReasoningResult(ReasoningStatus.INVALID_INPUT, diagnostics=problem)

    try:
        program = _build_program(req)
    except OSError as exc:
        return ReasoningResult(ReasoningStatus.INVALID_INPUT, diagnostics=f"cannot read rule_file: {exc}")
    version = _engine_version()
    fact_ids = tuple(f"{f.relation}:{'/'.join(f.args)}" for f in req.facts)
    common = dict(engine_version=version, program=program, fact_ids=fact_ids)

    # The thread cannot be killed on timeout; the call is abandoned (see docs).
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = pool.submit(_runner, program)
    try:
        raw = future.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError:
        return ReasoningResult(ReasoningStatus.TIMEOUT, diagnostics=f"no result within {timeout_s}s", **common)
    except ImportError as exc:
        return ReasoningResult(ReasoningStatus.ENGINE_ERROR, diagnostics=f"hyperon unavailable: {exc}", **common)
    except Exception as exc:  # parse errors surface as RuntimeError in hyperon
        return ReasoningResult(ReasoningStatus.ENGINE_ERROR, diagnostics=f"{type(exc).__name__}: {exc}", **common)
    finally:
        pool.shutdown(wait=False)

    return _interpret(raw, common)


def _interpret(raw: object, common: dict) -> ReasoningResult:
    raw_text = str(raw)
    # Expect exactly one query => one result list.
    if not isinstance(raw, list) or len(raw) != 1 or not isinstance(raw[0], list):
        return ReasoningResult(ReasoningStatus.ENGINE_ERROR, raw_output=raw_text,
                               diagnostics="unexpected output shape", **common)
    atoms = [str(a) for a in raw[0]]
    if not atoms:
        return ReasoningResult(ReasoningStatus.NO_RESULT, raw_output=raw_text, **common)
    # Hyperon returns unreduced expressions and (Error ...) atoms as ordinary
    # results, so only plain identifier symbols are accepted as conclusions.
    bad = [a for a in atoms if not _IDENT.match(a)]
    if bad:
        return ReasoningResult(ReasoningStatus.ENGINE_ERROR, raw_output=raw_text,
                               diagnostics=f"malformed or unreduced result atoms: {bad}", **common)
    return ReasoningResult(ReasoningStatus.SUCCESS, conclusions=tuple(sorted(set(atoms))),
                           raw_output=raw_text, **common)
