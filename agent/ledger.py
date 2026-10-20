
"""Simulated double-entry ledger using integer minor units only."""
from __future__ import annotations

from copy import deepcopy
from threading import RLock


_LOCK = RLock()
_ENTRIES: list[dict] = []
_TRANSACTIONS: list[dict] = []
_NONCES: set[str] = set()


def _amount(value) -> bool:
    """Accept integer minor units, never booleans or floats."""
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_proof(proof: dict) -> None:
    if not isinstance(proof, dict):
        raise ValueError("INVALID_PROOF")

    for field in ("gross", "fee", "artist", "community", "dust", "pool"):
        if field not in proof or not _amount(proof[field]) or proof[field] < 0:
            raise ValueError("INVALID_AMOUNT")

    if not isinstance(proof.get("status"), str):
        raise ValueError("INVALID_PROOF")

    coowners = proof.get("coowners", [])
    if not isinstance(coowners, list):
        raise ValueError("INVALID_PROOF")

    for owner in coowners:
        if not isinstance(owner, dict):
            raise ValueError("INVALID_PROOF")
        if not isinstance(owner.get("owner"), str) or not owner["owner"]:
            raise ValueError("INVALID_PROOF")
        if not _amount(owner.get("amount")) or owner["amount"] < 0:
            raise ValueError("INVALID_AMOUNT")


def _make_entries(proof: dict) -> list[dict]:
    """Copy authoritative proof amounts into signed ledger entries."""
    entries = [{"account": "buyer_receivable", "amount": -proof["gross"]}]

    if proof["fee"]:
        entries.append({
            "account": "platform_fee",
            "amount": proof["fee"],
        })

    entries.append({"account": "artist", "amount": proof["artist"]})
    entries.append({
        "account": "community_fund",
        "amount": proof["community"] + proof["dust"],
    })

    for coowner in proof.get("coowners", []):
        entries.append({
            "account": coowner["owner"],
            "amount": coowner["amount"],
        })

    if sum(entry["amount"] for entry in entries) != 0:
        raise ValueError("UNBALANCED_TRANSACTION")

    return entries


def post(proof: dict, nonce: str | None = None) -> dict:
    """Post an approved proof without recalculating settlement amounts."""
    _validate_proof(proof)

    with _LOCK:
        if proof["status"] != "APPROVED":
            return {
                "transaction_id": None,
                "status": "REJECTED",
                "entries_count": 0,
            }

        if nonce is not None:
            if not isinstance(nonce, str) or not nonce.strip():
                raise ValueError("INVALID_NONCE")
            if nonce in _NONCES:
                raise ValueError("DUPLICATE_NONCE")

        entries = _make_entries(proof)
        transaction_id = f"tx-{len(_TRANSACTIONS) + 1}"

        transaction = {
            "transaction_id": transaction_id,
            "nonce": nonce,
            "proof": deepcopy(proof),
            "entries": deepcopy(entries),
        }

        _ENTRIES.extend(deepcopy(entries))
        _TRANSACTIONS.append(transaction)
        if nonce is not None:
            _NONCES.add(nonce)

        return {
            "transaction_id": transaction_id,
            "status": "POSTED",
            "entries_count": len(entries),
        }


def balances() -> dict[str, int]:
    """Return each account's signed net balance."""
    with _LOCK:
        result: dict[str, int] = {}
        for entry in _ENTRIES:
            account = entry["account"]
            result[account] = result.get(account, 0) + entry["amount"]
        return result


def verify() -> bool:
    """Verify ledger structure, balances, and nonce uniqueness."""
    with _LOCK:
        if not _TRANSACTIONS:
            return False

        seen: set[str] = set()
        all_entries: list[dict] = []

        for transaction in _TRANSACTIONS:
            nonce = transaction["nonce"]
            if nonce is not None:
                if nonce in seen:
                    return False
                seen.add(nonce)

            entries = transaction["entries"]
            if not isinstance(entries, list) or not entries:
                return False

            if any(
                not isinstance(entry, dict)
                or not isinstance(entry.get("account"), str)
                or not _amount(entry.get("amount"))
                for entry in entries
            ):
                return False

            if sum(entry["amount"] for entry in entries) != 0:
                return False

            all_entries.extend(entries)

        return all_entries == _ENTRIES and seen == _NONCES
