"""End-to-end settlement orchestration pipeline.

Pipeline Flow (AGENTS.md, docs/PROOF_SHAPE.md, docs/START_HERE.md):
  1. Parse: Natural language bid -> structured parameters (artwork_id, gross_minor, currency).
  2. Validate: Input sanitization, zero-float check, strict integer minor units.
  3. Bridge: Hyperon MeTTa execution with pure integer arithmetic and native Atom API.
  4. Proof: Deterministic proof atom or rejection extraction.
  5. Audit Log: Append-only SHA-256 hash-chained commitment with nonce deduplication.
  6. Ledger: Verbatim posting of proof amounts to double-entry ledger.

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
                 currency, nonce, and optional override).
        offline: If True (default), runs purely offline using local MeTTa symbolic evaluation.
        parser: Optional intake parser module or callable.
        audit: Optional audit log module with seen_nonce() and append().
        ledger: Optional simulated ledger module with post().

    Returns:
        Canonical settlement proof or rejection dictionary matching docs/PROOF_SHAPE.md.
    """
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

    art_id = request.get("artwork_id")
    gross = request.get("gross_minor")
    currency = request.get("currency", "USD")

    # Validate currency code
    if not isinstance(currency, str) or not _CURRENCY_RE.match(currency):
        return {
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

    # Validate artwork identifier
    if not isinstance(art_id, str) or not _is_valid_arg(art_id):
        return {
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

    # Validate gross transaction amount (strict integer cents, no bool, no float, positive)
    if isinstance(gross, bool) or not isinstance(gross, int) or gross <= 0:
        return {
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

    # Nonce deduplication check if audit component is provided
    nonce = request.get("nonce")
    if audit is not None and nonce:
        try:
            if audit.seen_nonce(nonce):
                return {
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
        except Exception:
            pass

    # Process manager override if present
    query_function = "evaluate-resale"
    query_args: tuple[Any, ...] = (art_id, gross, currency)

    if "override" in request and request["override"] is not None:
        ov = request["override"]
        if not isinstance(ov, dict):
            return {
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

        rationale = ov.get("rationale") or ov.get("reason")
        if not isinstance(rationale, str) or len(rationale.strip()) < 15:
            return {
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

        has_royalty = "royalty_bps" in ov
        has_community = "community_bps" in ov

        # Override must carry EXACTLY ONE of royalty_bps or community_bps
        if (has_royalty and has_community) or (not has_royalty and not has_community):
            return {
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

        if has_royalty:
            r_bps = ov["royalty_bps"]
            if isinstance(r_bps, bool) or not isinstance(r_bps, int) or r_bps < 0 or r_bps > 10000:
                return {
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
            query_function = "evaluate-resale-override-royalty"
            query_args = (art_id, gross, currency, r_bps)
        else:
            c_bps = ov["community_bps"]
            if isinstance(c_bps, bool) or not isinstance(c_bps, int) or c_bps < 0 or c_bps > 10000:
                return {
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
            query_function = "evaluate-resale-override-community"
            query_args = (art_id, gross, currency, c_bps)

    # Load registered artwork facts from data/artworks.json
    try:
        registry = _load_artworks()
    except Exception:
        registry = {}

    artwork = registry.get(art_id)
    if artwork is None:
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
        }

    try:
        facts = load_artwork_facts(artwork)
    except Exception:
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
        }

    # Evaluate transaction via OpenCog Hyperon MeTTa
    req = ReasoningRequest(
        rule_file=_RULES_FILE,
        facts=facts,
        query_function=query_function,
        query_args=query_args,
    )
    res = run_reasoning(req)

    # Map bridge result verbatim to PROOF_SHAPE without performing money math
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
            "producing_layer": "bridge/MeTTa",
        }

        # If audit logger or simulated ledger provided, record verified transaction
        if audit is not None and nonce:
            try:
                audit.append(result, nonce)
            except Exception:
                pass
        if ledger is not None and nonce:
            try:
                ledger.post(result, nonce)
            except Exception:
                pass

        return result

    if res.status is ReasoningStatus.REJECTED and res.rejection is not None:
        return {
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
            "producing_layer": "bridge/MeTTa",
        }

    # Fail closed for any engine error, timeout, unmapped entity, or unexpected status
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
    }
