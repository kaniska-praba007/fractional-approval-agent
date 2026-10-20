
"""Append-only SHA-256 hash-chained audit log."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock


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
        if any(e["nonce"] == nonce for e in entries):
            raise AuditError("DUPLICATE_NONCE")

        previous = entries[-1]["hash"] if entries else GENESIS_HASH
        timestamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        entry = {
            "index": len(entries),
            "timestamp": timestamp,
            "nonce": nonce,
            "proof": json.loads(proof_payload),
            "prev_hash": previous,
            "hash": _hash(previous, timestamp, nonce, proof_payload),
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


def seen_nonce(nonce: str) -> bool:
    """Return True if a nonce is already present in the valid log."""
    if not isinstance(nonce, str) or not nonce:
        return False
    with _LOCK:
        entries = _read()
        if not _verify(entries):
            raise AuditError("AUDIT_CHAIN_INVALID")
        return any(entry["nonce"] == nonce for entry in entries)
