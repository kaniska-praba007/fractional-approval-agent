"""End-to-end settlement orchestration pipeline.

Pipeline Flow (AGENTS.md, docs/PROOF_SHAPE.md, docs/START_HERE.md, docs/FLOWS.md):
  1. Parse: Natural language bid -> structured parameters (artwork_id, gross_minor, currency).
  2. Validate: Input sanitization, zero-float check, strict integer minor units.
  3. Nonce Check: Deduplication against append-only audit log before invoking reasoning.
  4. Bridge: Hyperon MeTTa execution with pure integer arithmetic and native Atom API.
  5. Proof: Deterministic proof atom or rejection extraction.
  6. Audit Log: Append-only SHA-256 hash-chained commitment.
  7. Ledger: Verbatim posting of approved proof amounts to double-entry ledger.

CRITICAL INVARIANTS:
- Offline by default: Runs fully offline without external network calls or LLM API keys.
- If OFFLINE_MODE environment variable is set (or offline=True), no LLM calls are made.
- Fail closed: Any pipeline invariant failure returns a REJECTED proof shape.
- Zero floats: All amounts are strictly integer minor units (cents).
- Zero money math: settle() performs NO arithmetic (+, -, *, /, //) on monetary values;
  all values are copied verbatim from the MeTTa bridge proof atom.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from agent.bridge import (
    ReasoningRequest,
    ReasoningStatus,
    _is_valid_arg,
    load_artwork_facts,
    run_reasoning,
)

_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _ROOT / "data" / "artworks.json"
_RULES_FILE = _ROOT / "metta" / "royalties.metta"

_CURRENCY_RE = re.compile(r"^[A-Z]{3,4}$")


def _load_artworks() -> dict[str, dict]:
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {art["artwork_id"]: art for art in data}


def _record_audit(audit: Any, entry: dict, nonce: str) -> str | None:
    """Helper to append an entry to the audit log if audit is configured.
    Returns error string if append raised an exception, None on success."""
    if audit is not None and hasattr(audit, "append"):
        try:
            audit.append(entry, nonce)
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"
    return None


def settle(
    request: dict,
    offline: bool = True,
    parser: Any = None,
    audit: Any = None,
    ledger: Any = None,
) -> dict:
    """Execute the end-to-end fiduciary settlement pipeline.

    Orchestrates: parse -> validate -> bridge -> proof -> audit log -> ledger.

    Args:
        request: Input dictionary with structured fields (artwork_id, gross_minor,
                 currency, nonce, and optional override) or raw text for parsing.
        offline: If True (default), runs purely offline using local MeTTa symbolic evaluation.
        parser: Intake parser module or callable. If None, imported lazily from agent.parser.
        audit: Audit log module with seen_nonce() and append(). If None, imported lazily.
        ledger: Simulated ledger module with post(). If None, imported lazily.

    Returns:
        Canonical settlement proof or rejection dictionary matching docs/PROOF_SHAPE.md.
    """
    # Lazy import of real default components when not injected
    if parser is None:
        try:
            from agent import parser as default_parser
            parser = default_parser
        except Exception:
            pass

    if audit is None:
        try:
            from agent import audit_log as default_audit
            audit = default_audit
        except Exception:
            pass

    if ledger is None:
        try:
            from agent import ledger as default_ledger
            ledger = default_ledger
        except Exception:
            pass

    # Ensure offline mode default
    is_offline = offline or (os.getenv("OFFLINE_MODE", "1") == "1")

    if not isinstance(request, dict):
        return {
            "status": "REJECTED",
            "reason_code": "INVALID_AMOUNT",
            "artwork_id": "UNKNOWN",
            "currency": "USD",
            "gross": 0,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }

    # Handle natural language text intake via parser if raw text is provided
    from_parser = False
    req_data = dict(request)
    if "text" in req_data and ("artwork_id" not in req_data or "gross_minor" not in req_data):
        if parser is None or not hasattr(parser, "parse_request"):
            return {
                "status": "REJECTED",
                "reason_code": "LLM_MALFORMED_OUTPUT",
                "artwork_id": "UNKNOWN",
                "currency": "USD",
                "gross": 0,
                "fee": 0,
                "artist": 0,
                "community": 0,
                "dust": 0,
                "pool": 0,
                "coowners": [],
                "producing_layer": "parser",
            }
        try:
            parsed = parser.parse_request(req_data["text"])
            if not isinstance(parsed, dict) or "artwork_id" not in parsed or "gross_minor" not in parsed:
                raise ValueError("Incomplete parsed parameters")
            req_data.update(parsed)
            from_parser = True
        except Exception as exc:
            rejection = {
                "status": "REJECTED",
                "reason_code": "LLM_MALFORMED_OUTPUT",
                "artwork_id": "UNKNOWN",
                "currency": "USD",
                "gross": 0,
                "fee": 0,
                "artist": 0,
                "community": 0,
                "dust": 0,
                "pool": 0,
                "coowners": [],
                "producing_layer": "parser",
                "diagnostics": f"{type(exc).__name__}: {exc}",
            }
            nonce_val = req_data.get("nonce")
            if audit is not None and isinstance(nonce_val, str) and nonce_val:
                _record_audit(audit, rejection, nonce_val)
            return rejection

    art_id = req_data.get("artwork_id")
    gross = req_data.get("gross_minor")
    currency = req_data.get("currency", "USD")
    nonce = req_data.get("nonce")

    # Nonce presence check when audit log is active
    if audit is not None and (not isinstance(nonce, str) or not nonce.strip()):
        return {
            "status": "REJECTED",
            "reason_code": "INVALID_AMOUNT",
            "artwork_id": art_id if isinstance(art_id, str) else "UNKNOWN",
            "currency": currency if isinstance(currency, str) else "USD",
            "gross": 0,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }

    # Validate currency code
    if not isinstance(currency, str) or not _CURRENCY_RE.match(currency):
        rejection = {
            "status": "REJECTED",
            "reason_code": "INVALID_AMOUNT",
            "artwork_id": art_id if isinstance(art_id, str) else "UNKNOWN",
            "currency": "USD",
            "gross": 0,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }
        if audit is not None and isinstance(nonce, str) and nonce:
            _record_audit(audit, rejection, nonce)
        return rejection

    # Validate artwork identifier
    if not isinstance(art_id, str) or not _is_valid_arg(art_id):
        rejection = {
            "status": "REJECTED",
            "reason_code": "INVALID_AMOUNT",
            "artwork_id": "UNKNOWN",
            "currency": currency,
            "gross": 0,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }
        if audit is not None and isinstance(nonce, str) and nonce:
            _record_audit(audit, rejection, nonce)
        return rejection

    # Validate gross transaction amount (strict positive integer minor units, no bool, no float)
    if isinstance(gross, bool) or not isinstance(gross, int) or gross <= 0:
        rejection = {
            "status": "REJECTED",
            "reason_code": "INVALID_AMOUNT",
            "artwork_id": art_id,
            "currency": currency,
            "gross": 0,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }
        if audit is not None and isinstance(nonce, str) and nonce:
            _record_audit(audit, rejection, nonce)
        return rejection

    # Nonce deduplication check against audit log (runs before bridge)
    if audit is not None and hasattr(audit, "seen_nonce") and nonce:
        try:
            if audit.seen_nonce(nonce):
                rejection = {
                    "status": "REJECTED",
                    "reason_code": "DUPLICATE_NONCE",
                    "artwork_id": art_id,
                    "currency": currency,
                    "gross": gross,
                    "fee": 0,
                    "artist": 0,
                    "community": 0,
                    "dust": 0,
                    "pool": 0,
                    "coowners": [],
                    "producing_layer": "audit_log",
                }
                _record_audit(audit, rejection, nonce)
                return rejection
        except Exception as exc:
            return {
                "status": "REJECTED",
                "reason_code": "ENGINE_UNAVAILABLE",
                "artwork_id": art_id,
                "currency": currency,
                "gross": gross,
                "fee": 0,
                "artist": 0,
                "community": 0,
                "dust": 0,
                "pool": 0,
                "coowners": [],
                "producing_layer": "bridge_fail_closed",
                "diagnostics": f"{type(exc).__name__}: {exc}",
            }

    # Process manager override parameters
    query_function = "evaluate-resale"
    query_args: tuple[Any, ...] = (art_id, gross, currency)

    if "override" in req_data and req_data["override"] is not None:
        ov = req_data["override"]
        if not isinstance(ov, dict):
            rejection = {
                "status": "REJECTED",
                "reason_code": "INVALID_AMOUNT",
                "artwork_id": art_id,
                "currency": currency,
                "gross": gross,
                "fee": 0,
                "artist": 0,
                "community": 0,
                "dust": 0,
                "pool": 0,
                "coowners": [],
                "producing_layer": "bridge_fail_closed",
            }
            if audit is not None and isinstance(nonce, str) and nonce:
                _record_audit(audit, rejection, nonce)
            return rejection

        rationale = ov.get("rationale") or ov.get("reason")
        if not isinstance(rationale, str) or len(rationale.strip()) < 15:
            rejection = {
                "status": "REJECTED",
                "reason_code": "INVALID_AMOUNT",
                "artwork_id": art_id,
                "currency": currency,
                "gross": gross,
                "fee": 0,
                "artist": 0,
                "community": 0,
                "dust": 0,
                "pool": 0,
                "coowners": [],
                "producing_layer": "bridge_fail_closed",
            }
            if audit is not None and isinstance(nonce, str) and nonce:
                _record_audit(audit, rejection, nonce)
            return rejection

        has_royalty = "royalty_bps" in ov
        has_community = "community_bps" in ov

        # Override must carry EXACTLY ONE of royalty_bps or community_bps
        if (has_royalty and has_community) or (not has_royalty and not has_community):
            rejection = {
                "status": "REJECTED",
                "reason_code": "INVALID_AMOUNT",
                "artwork_id": art_id,
                "currency": currency,
                "gross": gross,
                "fee": 0,
                "artist": 0,
                "community": 0,
                "dust": 0,
                "pool": 0,
                "coowners": [],
                "producing_layer": "bridge_fail_closed",
            }
            if audit is not None and isinstance(nonce, str) and nonce:
                _record_audit(audit, rejection, nonce)
            return rejection

        if has_royalty:
            r_bps = ov["royalty_bps"]
            if isinstance(r_bps, bool) or not isinstance(r_bps, int) or r_bps < 0 or r_bps > 10000:
                rejection = {
                    "status": "REJECTED",
                    "reason_code": "INVALID_AMOUNT",
                    "artwork_id": art_id,
                    "currency": currency,
                    "gross": gross,
                    "fee": 0,
                    "artist": 0,
                    "community": 0,
                    "dust": 0,
                    "pool": 0,
                    "coowners": [],
                    "producing_layer": "bridge_fail_closed",
                }
                if audit is not None and isinstance(nonce, str) and nonce:
                    _record_audit(audit, rejection, nonce)
                return rejection
            query_function = "evaluate-resale-override-royalty"
            query_args = (art_id, gross, currency, r_bps)
        else:
            c_bps = ov["community_bps"]
            if isinstance(c_bps, bool) or not isinstance(c_bps, int) or c_bps < 0 or c_bps > 10000:
                rejection = {
                    "status": "REJECTED",
                    "reason_code": "INVALID_AMOUNT",
                    "artwork_id": art_id,
                    "currency": currency,
                    "gross": gross,
                    "fee": 0,
                    "artist": 0,
                    "community": 0,
                    "dust": 0,
                    "pool": 0,
                    "coowners": [],
                    "producing_layer": "bridge_fail_closed",
                }
                if audit is not None and isinstance(nonce, str) and nonce:
                    _record_audit(audit, rejection, nonce)
                return rejection
            query_function = "evaluate-resale-override-community"
            query_args = (art_id, gross, currency, c_bps)

    # Load registered artwork facts from data/artworks.json
    try:
        registry = _load_artworks()
    except Exception:
        registry = {}

    artwork = registry.get(art_id)
    if artwork is None:
        rejection = {
            "status": "REJECTED",
            "reason_code": "ENGINE_UNAVAILABLE",
            "artwork_id": art_id,
            "currency": currency,
            "gross": gross,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }
        if audit is not None and isinstance(nonce, str) and nonce:
            _record_audit(audit, rejection, nonce)
        return rejection

    try:
        facts = load_artwork_facts(artwork)
    except Exception as exc:
        rejection = {
            "status": "REJECTED",
            "reason_code": "ENGINE_UNAVAILABLE",
            "artwork_id": art_id,
            "currency": currency,
            "gross": gross,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
            "diagnostics": f"fact generation error: {exc}",
        }
        if audit is not None and isinstance(nonce, str) and nonce:
            _record_audit(audit, rejection, nonce)
        return rejection

    # Evaluate transaction through OpenCog Hyperon MeTTa
    req = ReasoningRequest(
        rule_file=_RULES_FILE,
        facts=facts,
        query_function=query_function,
        query_args=query_args,
    )
    res = run_reasoning(req)

    # Map bridge result verbatim to PROOF_SHAPE without performing money math
    producing_layer = "parser" if from_parser else "bridge/MeTTa"

    if res.status is ReasoningStatus.SUCCESS and res.proof is not None:
        p = res.proof
        result = {
            "status": "APPROVED",
            "reason_code": None,
            "artwork_id": p.artwork_id,
            "currency": currency,
            "gross": p.gross_minor,
            "fee": p.platform_fee_minor,
            "artist": p.artist_royalty_minor,
            "community": p.community_cut_minor,
            "dust": p.dust_minor,
            "pool": p.pool_minor,
            "coowners": [
                {"owner": c.owner, "wallet": c.wallet, "amount": c.amount_minor}
                for c in p.co_owner_payouts
            ],
            "producing_layer": producing_layer,
        }

        # 1. Commit to audit log
        if audit is not None and hasattr(audit, "append") and nonce:
            try:
                audit.append(result, nonce)
            except Exception as exc:
                return {
                    "status": "REJECTED",
                    "reason_code": "ENGINE_UNAVAILABLE",
                    "artwork_id": art_id,
                    "currency": currency,
                    "gross": gross,
                    "fee": 0,
                    "artist": 0,
                    "community": 0,
                    "dust": 0,
                    "pool": 0,
                    "coowners": [],
                    "producing_layer": "bridge_fail_closed",
                    "diagnostics": f"{type(exc).__name__}: {exc}",
                }

        # 2. Post to ledger (only after audit succeeds)
        if ledger is not None and hasattr(ledger, "post"):
            try:
                ledger.post(result, nonce)
            except Exception as exc:
                return {
                    "status": "REJECTED",
                    "reason_code": "ENGINE_UNAVAILABLE",
                    "artwork_id": art_id,
                    "currency": currency,
                    "gross": gross,
                    "fee": 0,
                    "artist": 0,
                    "community": 0,
                    "dust": 0,
                    "pool": 0,
                    "coowners": [],
                    "producing_layer": "bridge_fail_closed",
                    "diagnostics": f"{type(exc).__name__}: {exc}",
                }

        return result

    if res.status is ReasoningStatus.REJECTED and res.rejection is not None:
        rejection = {
            "status": "REJECTED",
            "reason_code": res.rejection.rejection_code,
            "artwork_id": art_id,
            "currency": currency,
            "gross": gross,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": producing_layer,
        }
        if audit is not None and isinstance(nonce, str) and nonce:
            _record_audit(audit, rejection, nonce)
        return rejection

    # Fail closed for any engine error, timeout, unmapped entity, or unexpected status
    rejection = {
        "status": "REJECTED",
        "reason_code": "ENGINE_UNAVAILABLE",
        "artwork_id": art_id,
        "currency": currency,
        "gross": gross,
        "fee": 0,
        "artist": 0,
        "community": 0,
        "dust": 0,
        "pool": 0,
        "coowners": [],
        "producing_layer": "bridge_fail_closed",
        "diagnostics": res.diagnostics or "engine returned no result or multiple unreduced atoms",
    }
    if audit is not None and isinstance(nonce, str) and nonce:
        _record_audit(audit, rejection, nonce)
    return rejection
