
"""Append-only SHA-256 hash-chained audit log."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


GENESIS_HASH = "0" * 64
AUDIT_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "audit_log.json"
_LOCK = RLock()


class AuditError(ValueError):
    """Raised when an audit operation cannot safely complete."""


def _canonical(value: dict) -> str:
    if not isinstance(value, dict):
        raise AuditError("INVALID_PROOF")
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False
        )
    except (TypeError, ValueError) as exc:
        raise AuditError("INVALID_PROOF") from exc


def _validate_no_floats(value):
    if isinstance(value, float):
        raise AuditError("FLOAT_NOT_ALLOWED")
    if isinstance(value, dict):
        for item in value.values():
            _validate_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            _validate_no_floats(item)


def _read():
    if not AUDIT_LOG_PATH.exists():
        return []
    try:
        entries = json.loads(AUDIT_LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError("AUDIT_LOG_UNREADABLE") from exc
    if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
        raise AuditError("AUDIT_LOG_INVALID")
    return entries


def _write(entries):
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = AUDIT_LOG_PATH.with_suffix(".json.tmp")
    try:
        temp.write_text(
            json.dumps(entries, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        temp.replace(AUDIT_LOG_PATH)
    except OSError as exc:
        raise AuditError("AUDIT_LOG_WRITE_FAILED") from exc


def _hash(prev_hash, timestamp, nonce, proof_payload):
    raw = prev_hash + timestamp + nonce + proof_payload
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _verify(entries):
    previous = GENESIS_HASH
    nonces = set()

    try:
        for index, entry in enumerate(entries):
            if entry["index"] != index:
                return False
            nonce = entry["nonce"]
            if not isinstance(nonce, str) or not nonce or nonce in nonces:
                return False
            if entry["prev_hash"] != previous:
                return False

            proof_payload = _canonical(entry["proof"])
            _validate_no_floats(entry["proof"])
            expected = _hash(
                previous, entry["timestamp"], nonce, proof_payload
            )
            if entry["hash"] != expected:
                return False

            previous = expected
            nonces.add(nonce)
    except (KeyError, TypeError, ValueError, AuditError):
        return False

    return True


def append(proof: dict, nonce: str) -> dict:
    """Append a proof and reject nonce reuse."""
    proof_payload = _canonical(proof)
    _validate_no_floats(proof)

    if not isinstance(nonce, str) or not nonce.strip():
        raise AuditError("INVALID_NONCE")

    with _LOCK:
        entries = _read()
        if not _verify(entries):
            raise AuditError("AUDIT_CHAIN_INVALID")
        actual_nonce = nonce
        if any(e["nonce"] == nonce or e["nonce"].startswith(f"{nonce}#") for e in entries):
            if proof.get("status") != "REJECTED":
                raise AuditError("DUPLICATE_NONCE")
            actual_nonce = f"{nonce}#rejected-{len(entries)}"

        previous = entries[-1]["hash"] if entries else GENESIS_HASH
        timestamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        entry = {
            "index": len(entries),
            "timestamp": timestamp,
            "nonce": actual_nonce,
            "proof": json.loads(proof_payload),
            "prev_hash": previous,
            "hash": _hash(previous, timestamp, actual_nonce, proof_payload),
        }
        _write(entries + [entry])
        return json.loads(json.dumps(entry))


def verify_chain() -> bool:
    """Check every record and hash link."""
    with _LOCK:
        try:
            return _verify(_read())
        except AuditError:
            return False


def verify_chain_details() -> dict[str, Any]:
    """Verify SHA-256 chain links across all blocks and return structured validation metadata."""
    with _LOCK:
        try:
            entries = _read()
            if not entries:
                return {
                    "verified": True,
                    "block_count": 0,
                    "status": "AUDIT_LOG_EMPTY_GENESIS",
                }
            is_valid = _verify(entries)
            return {
                "verified": is_valid,
                "block_count": len(entries),
                "status": "VALID" if is_valid else "CORRUPTED",
            }
        except AuditError as exc:
            return {
                "verified": False,
                "block_count": 0,
                "status": f"ERROR_{exc}",
            }


def seen_nonce(nonce: str) -> bool:
    """Return True if a nonce is already present in the valid log."""
    if not isinstance(nonce, str) or not nonce:
        return False
    with _LOCK:
        entries = _read()
        if not _verify(entries):
            raise AuditError("AUDIT_CHAIN_INVALID")
        return any(
            entry["nonce"] == nonce or entry["nonce"].startswith(f"{nonce}#")
            for entry in entries
        )
