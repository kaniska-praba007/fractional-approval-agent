"""Narrow adapter around the Hyperon (``hyperon`` PyPI package) MeTTa runtime.

This is the *Hyperon/MeTTa* boundary only. It is NOT an Omega integration:
Omega runs on PeTTa/SWI-Prolog and is driven by an LLM loop (see
docs/OMEGA_INTEGRATION.md).

Fail-closed contract: only ``ReasoningStatus.SUCCESS`` carries valid conclusions.
Every other status (no_result, rejected, invalid_input, engine_error, timeout) means
"no conclusion / no approval" and must never disburse funds.

Safety: callers pass *validated tokens*, never raw arbitrary MeTTa text. Facts and
queries are built from validated identifiers and relations from an explicit
allow-list. Money values are strictly non-negative integers; floats and booleans
are strictly rejected. Results are traversed via the native Hyperon Atom API.
"""
from __future__ import annotations

import concurrent.futures
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Sequence

# Valid identifier pattern:
# - lowercase identifier: e.g. collective-owner, alice, owner-of
# - uppercase IDs with hyphen/numbers: e.g. HFA-101, TEST-DUST
# - hex addresses: e.g. 0xalice, 0xcommunity_fund
# - standard currency codes: e.g. USD, KES
# - standard status codes: LIVING, ESTATE_MANAGED, CONTESTED
_IDENT_RE = re.compile(
    r"^[a-z][a-z0-9_-]{0,63}$|"
    r"^[A-Z0-9]+-[A-Z0-9_-]+$|"
    r"^0x[a-zA-Z0-9_]+$|"
    r"^[A-Z]{3,4}$|"
    r"^(LIVING|ESTATE_MANAGED|CONTESTED)$"
)
_DEFAULT_TIMEOUT_S = 10.0

DEFAULT_ALLOWED_RELATIONS: frozenset[str] = frozenset({
    "owner-of",
    "member-of",
    "artwork-reserve",
    "artwork-royalty",
    "artwork-community",
    "artwork-fee",
    "artwork-status",
    "artwork-cap",
})


class ReasoningStatus(str, Enum):
    SUCCESS = "success"
    NO_RESULT = "no_result"
    REJECTED = "rejected"
    INVALID_INPUT = "invalid_input"
    ENGINE_ERROR = "engine_error"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class CoOwnerPayout:
    owner: str
    wallet: str
    bps: int
    amount_minor: int


@dataclass(frozen=True)
class SettlementProof:
    artwork_id: str
    gross_minor: int
    platform_fee_minor: int
    net_minor: int
    artist_royalty_minor: int
    community_cut_minor: int
    dust_minor: int
    community_total_minor: int
    co_owner_payouts: tuple[CoOwnerPayout, ...]
    conservation_verified: bool


@dataclass(frozen=True)
class SettlementRejection:
    rejection_code: str
    details: tuple[object, ...] = ()


@dataclass(frozen=True)
class Fact:
    relation: str
    args: tuple[object, ...] = ()
    atom: object = None

    def to_atom(self):
        """Construct Hyperon Atom representation of this fact using Hyperon Atom API."""
        if self.atom is not None:
            return self.atom
        from hyperon.atoms import E, S, ValueAtom
        atom_args = []
        for a in self.args:
            if isinstance(a, int):
                atom_args.append(ValueAtom(a))
            elif isinstance(a, str):
                atom_args.append(S(a))
            else:
                atom_args.append(a)
        return E(S(self.relation), *atom_args)


@dataclass(frozen=True)
class ReasoningRequest:
    """rule_file: trusted .metta file.
    query_function: head symbol of the query.
    query_args: validated arguments (symbols or integer amounts); one free variable ``$result`` is appended.
    allowed_relations: allow-list of fact relation names."""
    rule_file: Path
    facts: Sequence[Fact]
    query_function: str
    query_args: tuple[object, ...]
    allowed_relations: frozenset[str] = DEFAULT_ALLOWED_RELATIONS


@dataclass(frozen=True)
class ReasoningResult:
    status: ReasoningStatus
    conclusions: tuple[str, ...] = ()
    proof: SettlementProof | None = None
    rejection: SettlementRejection | None = None
    engine_version: str | None = None
    program: str | None = None  # exact program text executed, for debugging/audit
    raw_output: str | None = None
    diagnostics: str | None = None
    fact_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.status is ReasoningStatus.SUCCESS and bool(self.conclusions)


def _is_valid_arg(value: object) -> bool:
    """Validate that an argument is safe: string token matching _IDENT_RE or safe int.
    Strictly rejects floats, booleans, negative integers, parentheses, quotes, whitespace,
    empty strings, nested expressions, or unknown types."""
    if isinstance(value, (float, bool)):
        return False
    if isinstance(value, int):
        return value >= 0
    if isinstance(value, str):
        if not value:
            return False
        if any(c in value for c in "()\"'"):
            return False
        if any(c.isspace() for c in value):
            return False
        return bool(_IDENT_RE.match(value))
    return False


def _validate(req: ReasoningRequest) -> str | None:
    """Return an error message, or None if the request is well-formed."""
    if not isinstance(req, ReasoningRequest):
        return "request must be a ReasoningRequest"
    if not isinstance(req.rule_file, Path) or not req.rule_file.is_file():
        return "rule_file must be an existing file"
    if not isinstance(req.query_function, str) or not _IDENT_RE.match(req.query_function):
        return "invalid query_function"
    if not all(_is_valid_arg(a) for a in req.query_args):
        return "invalid query argument"
    for f in req.facts:
        if not isinstance(f, Fact) or f.relation not in req.allowed_relations:
            return "fact relation not in allow-list"
        if f.atom is not None:
            if not all(_is_valid_arg(a) for a in f.args):
                return "invalid fact argument"
            continue
        if not f.args or not all(_is_valid_arg(a) for a in f.args):
            return "invalid fact argument"
    return None


def _build_program(req: ReasoningRequest) -> str:
    rules = req.rule_file.read_text(encoding="utf-8")
    fact_strs = []
    for f in req.facts:
        if f.atom is not None:
            fact_strs.append(str(f.atom))
        else:
            try:
                fact_strs.append(str(f.to_atom()))
            except Exception:
                fact_strs.append(f"({f.relation} {' '.join(str(a) for a in f.args)})")
    facts = "\n".join(fact_strs)
    query = f"!({req.query_function} {' '.join(str(a) for a in req.query_args)} $result)"
    return f"{rules}\n{facts}\n{query}\n"


def _engine_version() -> str | None:
    try:
        from importlib.metadata import version
        return version("hyperon")
    except Exception:  # pragma: no cover
        return None


def _run_hyperon(req_or_program: ReasoningRequest | str) -> list[list[object]]:
    from hyperon import MeTTa
    metta = MeTTa()
    if isinstance(req_or_program, str):
        return metta.run(req_or_program)

    # 1. Load rules
    rules = req_or_program.rule_file.read_text(encoding="utf-8")
    metta.run(rules)

    # 2. Add fact atoms to space directly via Hyperon Atom API
    space = metta.space()
    for f in req_or_program.facts:
        space.add_atom(f.to_atom())

    # 3. Query
    query = f"!({req_or_program.query_function} {' '.join(str(a) for a in req_or_program.query_args)} $result)"
    return metta.run(query)


def load_artwork_facts(artwork: dict) -> list[Fact]:
    """Convert an artwork dictionary into validated Fact objects for Hyperon AtomSpace."""
    art_id = artwork["artwork_id"]
    reserve = artwork["reserve"]
    facts: list[Fact] = [
        Fact("artwork-reserve", (art_id, reserve["amount_minor"], reserve["currency"])),
        Fact("artwork-royalty", (art_id, artwork["royalty_bps"], artwork["royalty_floor_bps"])),
        Fact("artwork-community", (art_id, artwork["community_bps"], artwork["community_wallet"])),
        Fact("artwork-fee", (art_id, artwork.get("platform_fee_bps", 0))),
        Fact("artwork-status", (art_id, artwork.get("status", "LIVING"))),
    ]

    # Convert cap table to recursive atom expression using Hyperon Atom API:
    # (cons-share (share-entry alice 6000 0xalice) (cons-share (share-entry bob 4000 0xbob) ()))
    from hyperon.atoms import E, S, ValueAtom

    cap_atom = E()
    for entry in reversed(artwork.get("cap_table", [])):
        owner = entry["owner"]
        bps = entry["bps"]
        wallet = entry["wallet"]
        if not _is_valid_arg(owner) or not _is_valid_arg(bps) or not _is_valid_arg(wallet):
            raise ValueError(f"Invalid cap table entry: {entry}")
        entry_atom = E(S("share-entry"), S(owner), ValueAtom(bps), S(wallet))
        cap_atom = E(S("cons-share"), entry_atom, cap_atom)

    cap_fact_atom = E(S("artwork-cap"), S(art_id), cap_atom)
    facts.append(Fact("artwork-cap", (art_id,), atom=cap_fact_atom))
    return facts


def load_registry_facts(artworks: Sequence[dict]) -> list[Fact]:
    """Convert a list of artwork records into a combined list of Fact objects."""
    all_facts: list[Fact] = []
    for art in artworks:
        all_facts.extend(load_artwork_facts(art))
    return all_facts


def run_reasoning(
    req: ReasoningRequest,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    _runner=_run_hyperon,
) -> ReasoningResult:
    """Run one reasoning request. Never raises; fails closed on any invariant violation.

    Enforces fail-closed semantics:
    - Empty results return NO_RESULT.
    - Multiple results return ENGINE_ERROR.
    - Rejections return REJECTED.
    """
    problem = _validate(req)
    if problem:
        return ReasoningResult(ReasoningStatus.INVALID_INPUT, diagnostics=problem)

    try:
        program = _build_program(req)
    except OSError as exc:
        return ReasoningResult(ReasoningStatus.INVALID_INPUT, diagnostics=f"cannot read rule_file: {exc}")

    version = _engine_version()
    fact_ids = tuple(f"{f.relation}:{'/'.join(str(a) for a in f.args)}" for f in req.facts)
    common = dict(engine_version=version, program=program, fact_ids=fact_ids)

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    runner_arg = req if _runner is _run_hyperon else program
    future = pool.submit(_runner, runner_arg)
    try:
        raw = future.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError:
        return ReasoningResult(ReasoningStatus.TIMEOUT, diagnostics=f"no result within {timeout_s}s", **common)
    except ImportError as exc:
        return ReasoningResult(ReasoningStatus.ENGINE_ERROR, diagnostics=f"hyperon unavailable: {exc}", **common)
    except Exception as exc:
        return ReasoningResult(ReasoningStatus.ENGINE_ERROR, diagnostics=f"{type(exc).__name__}: {exc}", **common)
    finally:
        pool.shutdown(wait=False)

    return _interpret(raw, common)


def _interpret(raw: object, common: dict) -> ReasoningResult:
    raw_text = str(raw)

    # Expect exactly one query => one result list.
    if not isinstance(raw, list) or len(raw) != 1 or not isinstance(raw[0], list):
        return ReasoningResult(
            ReasoningStatus.ENGINE_ERROR,
            raw_output=raw_text,
            diagnostics="unexpected output shape",
            **common,
        )

    result_atoms = raw[0]
    # Empty result -> NO_RESULT
    if not result_atoms:
        return ReasoningResult(ReasoningStatus.NO_RESULT, raw_output=raw_text, **common)

    # Multiple results -> fail closed (ENGINE_ERROR)
    if len(result_atoms) > 1:
        return ReasoningResult(
            ReasoningStatus.ENGINE_ERROR,
            raw_output=raw_text,
            diagnostics=f"multiple results returned ({len(result_atoms)} atoms); failing closed",
            **common,
        )

    atom = result_atoms[0]

    # Native Hyperon Atom API traversal
    if hasattr(atom, "get_metatype"):
        from hyperon import AtomKind

        kind = atom.get_metatype()
        if kind == AtomKind.SYMBOL:
            symbol_name = atom.get_name()
            if _IDENT_RE.match(symbol_name):
                return ReasoningResult(
                    ReasoningStatus.SUCCESS,
                    conclusions=(symbol_name,),
                    raw_output=raw_text,
                    **common,
                )
            return ReasoningResult(
                ReasoningStatus.ENGINE_ERROR,
                raw_output=raw_text,
                diagnostics=f"malformed or unreduced result atom: {symbol_name}",
                **common,
            )

        if kind == AtomKind.EXPR:
            children = atom.get_children()
            if not children:
                return ReasoningResult(ReasoningStatus.NO_RESULT, raw_output=raw_text, **common)

            head_atom = children[0]
            head = head_atom.get_name() if head_atom.get_metatype() == AtomKind.SYMBOL else str(head_atom)

            if head == "proof":
                proof = _parse_proof_atom(atom)
                if not proof.conservation_verified:
                    return ReasoningResult(
                        ReasoningStatus.ENGINE_ERROR,
                        raw_output=raw_text,
                        diagnostics="conservation invariant failed in MeTTa proof",
                        **common,
                    )
                return ReasoningResult(
                    ReasoningStatus.SUCCESS,
                    conclusions=("APPROVED",),
                    proof=proof,
                    raw_output=raw_text,
                    **common,
                )

            if head == "rejected":
                rejection = _parse_rejected_atom(atom)
                return ReasoningResult(
                    ReasoningStatus.REJECTED,
                    conclusions=(),
                    rejection=rejection,
                    diagnostics=f"REJECTED: {rejection.rejection_code}",
                    raw_output=raw_text,
                    **common,
                )

            if head == "Error":
                return ReasoningResult(
                    ReasoningStatus.ENGINE_ERROR,
                    raw_output=raw_text,
                    diagnostics=f"MeTTa Error: {atom}",
                    **common,
                )

            return ReasoningResult(
                ReasoningStatus.ENGINE_ERROR,
                raw_output=raw_text,
                diagnostics=f"unreduced expression atom: {atom}",
                **common,
            )

    # Fallback for fake string runner in mock unit tests
    atom_str = str(atom)
    if atom_str.startswith("(Error") or atom_str.startswith("(") and atom_str.endswith(")"):
        return ReasoningResult(
            ReasoningStatus.ENGINE_ERROR,
            raw_output=raw_text,
            diagnostics=f"malformed or unreduced result atoms: {[atom_str]}",
            **common,
        )
    if not _IDENT_RE.match(atom_str):
        return ReasoningResult(
            ReasoningStatus.ENGINE_ERROR,
            raw_output=raw_text,
            diagnostics=f"malformed or unreduced result atoms: {[atom_str]}",
            **common,
        )

    return ReasoningResult(
        ReasoningStatus.SUCCESS,
        conclusions=(atom_str,),
        raw_output=raw_text,
        **common,
    )


def _parse_proof_atom(atom) -> SettlementProof:
    """Traverse a (proof ...) expression atom strictly using Hyperon Atom API."""
    from hyperon import AtomKind

    children = atom.get_children()
    # proof format:
    # 0: proof
    # 1: artwork_id (Symbol)
    # 2: gross (Grounded int)
    # 3: fee (Grounded int)
    # 4: net (Grounded int)
    # 5: artist (Grounded int)
    # 6: comm (Grounded int)
    # 7: dust (Grounded int)
    # 8: comm_total (Grounded int)
    # 9: shares (Expr)
    # 10: conserved (Grounded bool)
    artwork_id = children[1].get_name()
    gross = children[2].get_object().content
    fee = children[3].get_object().content
    net = children[4].get_object().content
    artist = children[5].get_object().content
    comm = children[6].get_object().content
    dust = children[7].get_object().content
    comm_total = children[8].get_object().content

    shares: list[CoOwnerPayout] = []
    curr = children[9]
    while curr.get_metatype() == AtomKind.EXPR and len(curr.get_children()) == 3:
        head_name = curr.get_children()[0].get_name()
        if head_name != "cons-payout":
            break
        entry_children = curr.get_children()[1].get_children()
        owner = entry_children[1].get_name()
        bps = entry_children[2].get_object().content
        wallet = entry_children[3].get_name()
        amt = entry_children[4].get_object().content
        shares.append(CoOwnerPayout(owner=owner, wallet=wallet, bps=bps, amount_minor=amt))
        curr = curr.get_children()[2]

    conserved = children[10].get_object().content is True

    return SettlementProof(
        artwork_id=artwork_id,
        gross_minor=gross,
        platform_fee_minor=fee,
        net_minor=net,
        artist_royalty_minor=artist,
        community_cut_minor=comm,
        dust_minor=dust,
        community_total_minor=comm_total,
        co_owner_payouts=tuple(shares),
        conservation_verified=conserved,
    )


def _parse_rejected_atom(atom) -> SettlementRejection:
    """Traverse a (rejected ...) expression atom strictly using Hyperon Atom API."""
    from hyperon import AtomKind

    children = atom.get_children()
    code = children[1].get_name()
    details: list[object] = []
    for c in children[2:]:
        if c.get_metatype() == AtomKind.SYMBOL:
            details.append(c.get_name())
        elif c.get_metatype() == AtomKind.GROUNDED:
            details.append(c.get_object().content)
        else:
            details.append(str(c))
    return SettlementRejection(rejection_code=code, details=tuple(details))
