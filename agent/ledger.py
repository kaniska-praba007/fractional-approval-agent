
"""Simulated double-entry ledger using integer minor units only."""
from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any


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

    currency = proof.get("currency")
    if not isinstance(currency, str) or not currency.strip():
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
    """Copy proof amounts and currency into ledger entries."""
    currency = proof["currency"]

    entries = [
        {
            "account": "buyer_receivable",
            "amount": -proof["gross"],
            "currency": currency,
        }
    ]

    if proof["fee"]:
        entries.append({
            "account": "platform_fee",
            "amount": proof["fee"],
            "currency": currency,
        })

    entries.append({
        "account": "artist",
        "amount": proof["artist"],
        "currency": currency,
    })

    # Keep community and dust separate; do not add money values.
    entries.append({
        "account": "community_fund",
        "amount": proof["community"],
        "currency": currency,
    })
    entries.append({
        "account": "community_fund",
        "amount": proof["dust"],
        "currency": currency,
    })

    for coowner in proof.get("coowners", []):
        entries.append({
            "account": coowner["owner"],
            "amount": coowner["amount"],
            "currency": currency,
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
    """Return each account's signed net balance (existing API)."""
    with _LOCK:
        result: dict[str, int] = {}
        for entry in _ENTRIES:
            account = entry["account"]
            result[account] = result.get(account, 0) + entry["amount"]
        return result


def balances_by_currency() -> dict[str, dict[str, int]]:
    """Return signed account balances grouped by currency."""
    with _LOCK:
        result: dict[str, dict[str, int]] = {}
        for entry in _ENTRIES:
            currency = entry["currency"]
            account = entry["account"]
            currency_balances = result.setdefault(currency, {})
            currency_balances[account] = (
                currency_balances.get(account, 0) + entry["amount"]
            )
        return result

def status() -> dict[str, Any]:
    """Return the operational status of the double-entry ledger.

    Safely reports empty initial state without throwing unhandled exceptions.
    """
    with _LOCK:
        if not _TRANSACTIONS:
            return {
                "status": "LEDGER_INITIALIZED_ZERO_ENTRIES",
                "transaction_count": 0,
                "entry_count": 0,
                "balances": {},
            }
        return {
            "status": "ACTIVE",
            "transaction_count": len(_TRANSACTIONS),
            "entry_count": len(_ENTRIES),
            "balances": balances(),
        }


def reset() -> None:
    """Clear entries, transactions, and replay-protection nonces."""
    with _LOCK:
        _ENTRIES.clear()
        _TRANSACTIONS.clear()
        _NONCES.clear()


def verify() -> bool:
    """Verify ledger structure, currencies, balances, and nonce uniqueness."""
    with _LOCK:
        # An untouched, empty ledger is valid.
        if not _TRANSACTIONS:
            return not _ENTRIES and not _NONCES

        seen: set[str] = set()
        all_entries: list[dict] = []

        for transaction in _TRANSACTIONS:
            if not isinstance(transaction, dict):
                return False

            nonce = transaction.get("nonce")
            if nonce is not None:
                if not isinstance(nonce, str) or nonce in seen:
                    return False
                seen.add(nonce)

            entries = transaction.get("entries")
            if not isinstance(entries, list) or not entries:
                return False

            proof = transaction.get("proof")
            if not isinstance(proof, dict):
                return False

            currency = proof.get("currency")
            if not isinstance(currency, str) or not currency.strip():
                return False

            for entry in entries:
                if (
                    not isinstance(entry, dict)
                    or not isinstance(entry.get("account"), str)
                    or not _amount(entry.get("amount"))
                    or entry.get("currency") != currency
                ):
                    return False

            if sum(entry["amount"] for entry in entries) != 0:
                return False

            all_entries.extend(entries)

        return all_entries == _ENTRIES and seen == _NONCES
