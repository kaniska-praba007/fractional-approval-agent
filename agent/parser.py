"""Deterministic rule-based natural language bid parser.

Strict Contract (AGENTS.md & docs/PROOF_SHAPE.md):
- Converts human bids (e.g. '12k', '$12,500', 'USD 10,000') into integer minor units (cents).
- Rejects ambiguous inputs, multiple competing prices, or invalid asset IDs.
- Adversarial prompt injection defense: ignores system instructions embedded in input text.
- Strictly returns integer cents (NO floats).

Example Usage:
>>> parse_amount_cents("12k")
1200000
>>> parse_amount_cents("$12,500")
1250000
>>> parse_request("Bid 10,000 USD on HFA-101")
{'artwork_id': 'HFA-101', 'gross_minor': 1000000, 'currency': 'USD'}
"""
from __future__ import annotations


def parse_amount_cents(text: str) -> int:
    """Parse a human-entered currency string into exact integer minor units (cents).

    Args:
        text: Input string such as "12k", "$12,500", "USD 10,000".

    Returns:
        Exact integer amount in cents (e.g. 1200000 for "12k").

    Raises:
        ValueError: If input is ambiguous, negative, non-numeric, or unparseable.
        NotImplementedError: Stub implementation for scaffold/0.5.
    """
    raise NotImplementedError("parse_amount_cents not implemented yet (owned by parser/3.1-rule-parser)")


def parse_request(text: str) -> dict:
    """Extract artwork_id, gross_minor, and currency from a raw natural language bid.

    Args:
        text: Unstructured bid proposal text.

    Returns:
        Dictionary containing 'artwork_id', 'gross_minor', and 'currency'.

    Raises:
        ValueError: If input cannot be deterministically resolved to a single valid bid.
        NotImplementedError: Stub implementation for scaffold/0.5.
    """
    raise NotImplementedError("parse_request not implemented yet (owned by parser/3.1-rule-parser)")
