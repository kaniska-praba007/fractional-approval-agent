"""Simulated double-entry ledger in integer cents.

CRITICAL INVARIANT (AGENTS.md & docs/PROOF_SHAPE.md):
- The ledger COPIES amounts from the authoritative proof atom and only checks
  that debit and credit entries sum to zero.
- It performs NO settlement calculation and NO money maths.
- All amounts are strictly integer minor units (cents).
- Rejected proofs post nothing.
- Replayed nonces are rejected without modifying ledger balances.

Double-entry bookkeeping convention:
  Debits: Buyer / Escrow Receivable (gross amount)
  Credits:
    - Platform Fee Account
    - Artist Royalty Account
    - Community Fund Account (base community cut + dust)
    - Co-owner Accounts (each fractional owner's share)
  Total debits == Total credits. Sum of signed entries == 0.

Example Usage:
>>> proof = {
...     "status": "APPROVED",
...     "artwork_id": "HFA-101",
...     "currency": "USD",
...     "gross": 1000000,
...     "fee": 0,
...     "artist": 150000,
...     "community": 30000,
...     "dust": 0,
...     "pool": 820000,
...     "coowners": [
...         {"owner": "alice", "wallet": "0xalice", "amount": 492000},
...         {"owner": "bob", "wallet": "0xbob", "amount": 328000}
...     ]
... }
>>> post(proof)
{'transaction_id': 'tx-1', 'status': 'POSTED', 'entries_count': 5}
>>> balances()
{'buyer_receivable': -1000000, 'artist_0xartist101': 150000, 'community_fund': 30000, 'alice': 492000, 'bob': 328000}
>>> verify()
True
"""
from __future__ import annotations


def post(proof: dict, nonce: str | None = None) -> dict:
    """Post an approved settlement proof to the simulated double-entry ledger.

    Copies amounts verbatim from the proof without recomputing payouts.
    Validates that total debits equal total credits (sum to zero).
    If proof status is 'REJECTED', posts nothing.

    Args:
        proof: Canonical proof dictionary matching docs/PROOF_SHAPE.md.
        nonce: Optional unique transaction identifier to prevent replay.

    Returns:
        Ledger posting transaction receipt with transaction ID and entry count.

    Raises:
        ValueError: If entries do not sum to zero or nonce is duplicated.
        NotImplementedError: Stub implementation for scaffold/0.5.
    """
    raise NotImplementedError("Ledger post not implemented yet (owned by agent/2.6-sim-ledger)")


def balances() -> dict[str, int]:
    """Retrieve current account balances in integer minor units (cents).

    Returns:
        Mapping of account identifier to net balance integer in minor units.

    Raises:
        NotImplementedError: Stub implementation for scaffold/0.5.
    """
    raise NotImplementedError("Ledger balances not implemented yet (owned by agent/2.6-sim-ledger)")


def verify() -> bool:
    """Verify that all ledger transactions are balanced and sum to zero.

    Returns:
        True if the entire ledger satisfies double-entry conservation; False otherwise.

    Raises:
        NotImplementedError: Stub implementation for scaffold/0.5.
    """
    raise NotImplementedError("Ledger verify not implemented yet (owned by agent/2.6-sim-ledger)")
