"""End-to-end settlement orchestration pipeline.

Pipeline Flow (AGENTS.md, docs/PROOF_SHAPE.md, docs/START_HERE.md):
  1. Parse: Natural language bid -> structured parameters (artwork_id, gross_minor, currency).
  2. Validate: Input sanitization, relation allow-lists, zero-float check.
  3. Bridge: Hyperon MeTTa execution with pure integer arithmetic and native Atom API.
  4. Proof: Deterministic proof atom or rejection extraction.
  5. Audit Log: Append-only SHA-256 hash-chained commitment with nonce deduplication.
  6. Ledger: Verbatim posting of proof amounts to double-entry ledger.

CRITICAL INVARIANTS:
- Offline by default: Runs fully offline without external network calls or LLM API keys.
- If OFFLINE_MODE environment variable is set (or offline=True), no LLM calls are made.
- Fail closed: Any pipeline invariant failure returns a REJECTED proof shape.
- Zero floats: All amounts are strictly integer minor units (cents).
"""
from __future__ import annotations

import os


def settle(request: dict, offline: bool = True) -> dict:
    """Execute the end-to-end fiduciary settlement pipeline.

    Orchestrates: parse -> validate -> bridge -> proof -> audit log -> ledger.

    Args:
        request: Input dictionary with either structured fields (artwork_id, gross_minor,
                 currency, nonce) or raw bid text to be parsed.
        offline: If True (default), runs purely offline using deterministic rule parsing
                 and local MeTTa symbolic evaluation without external API calls.

    Returns:
        Canonical settlement proof or rejection dictionary matching docs/PROOF_SHAPE.md.

    Raises:
        NotImplementedError: Pipeline orchestration stub for scaffold/0.5.
    """
    # Check offline configuration; default to True unless explicitly overridden
    is_offline = offline or (os.getenv("OFFLINE_MODE", "1") == "1")

    if not is_offline and not os.getenv("GEMINI_API_KEY"):
        # Fail closed if online mode requested without API credentials
        return {
            "status": "REJECTED",
            "reason_code": "ENGINE_UNAVAILABLE",
            "artwork_id": request.get("artwork_id", "UNKNOWN"),
            "currency": request.get("currency", "USD"),
            "gross": request.get("gross_minor", 0),
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }

    raise NotImplementedError("Full pipeline orchestration will be wired in agent/2.5-override-wiring")
