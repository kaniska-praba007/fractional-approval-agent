"""Deterministic rule-based natural language bid parser.

Strict Contract (AGENTS.md & docs/PROOF_SHAPE.md):
- Converts human bids (e.g. '12k', '$12,500', 'USD 10,000') into integer minor units (cents).
- Rejects ambiguous inputs, multiple competing prices, or invalid asset IDs.
- Adversarial prompt injection defense: ignores system instructions embedded in input text.
- Strictly returns integer cents (NO floats anywhere in the codebase).

Example Usage:
>>> parse_amount_cents("12k")
1200000
>>> parse_amount_cents("$12,500")
1250000
>>> parse_request("Bid 10,000 USD on HFA-101")
{'artwork_id': 'HFA-101', 'gross_minor': 1000000, 'currency': 'USD', 'nonce': '...'}
"""
from __future__ import annotations

import re
import uuid

# Ambiguous keywords indicating approximation or ranges (never guess on ambiguous bids)
_AMBIGUOUS_PATTERNS = [
    re.compile(r"\bbetween\b", re.IGNORECASE),
    re.compile(r"\baround\b", re.IGNORECASE),
    re.compile(r"\babout\b", re.IGNORECASE),
    re.compile(r"\bapprox(?:imately)?\b", re.IGNORECASE),
    re.compile(r"\bor\b", re.IGNORECASE),
    re.compile(r"\bmaybe\b", re.IGNORECASE),
    re.compile(r"\bfree\b", re.IGNORECASE),
    re.compile(r"\bunknown\b", re.IGNORECASE),
    re.compile(r"\b(?:from\s+)?\d+k?\s+(?:to|-)\s+\d+k?\b", re.IGNORECASE),
]

# Supported ISO currency codes
_SUPPORTED_CURRENCIES = ["USD", "KES", "EUR", "GBP"]

# Pattern to recognize known artwork IDs: e.g. HFA-101, HFA-102, HFA-103, TEST-DUST, TEST-FEE, TEST-KES
_ARTWORK_ID_PATTERN = re.compile(r"\b([A-Z0-9]+-[A-Z0-9_-]+)\b")


def _parse_decimal_str_to_cents(whole_part: str, frac_part: str) -> int:
    """Helper to convert whole and fractional decimal string parts to integer cents without floats."""
    if not whole_part:
        whole = 0
    else:
        whole = int(whole_part)

    if len(frac_part) == 0:
        cents = 0
    elif len(frac_part) == 1:
        cents = int(frac_part) * 10
    elif len(frac_part) == 2:
        cents = int(frac_part)
    else:
        raise ValueError(f"Sub-cent fractional precision not permitted: .{frac_part}")

    total = whole * 100 + cents
    if total <= 0:
        raise ValueError("Amount must be strictly positive")
    return total


def parse_amount_cents(text: str) -> int:
    """Parse a human-entered currency string into exact integer minor units (cents).

    Args:
        text: Input string such as "12k", "$12,500", "USD 10,000", "1.5k".

    Returns:
        Exact integer amount in cents (e.g. 1200000 for "12k").

    Raises:
        ValueError: If input is ambiguous, negative, non-numeric, or unparseable.
    """
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Empty input string")

    # Reject ambiguous keywords if present
    for pattern in _AMBIGUOUS_PATTERNS:
        if pattern.search(cleaned):
            raise ValueError(f"Ambiguous amount expression: {cleaned}")

    # Check for negative numbers
    if cleaned.startswith("-") or re.search(r"(?:^|\s)-\s*\$?\d+", cleaned):
        raise ValueError(f"Negative amount not permitted: {cleaned}")

    # Strip currency symbols and names
    stripped = cleaned
    for curr in _SUPPORTED_CURRENCIES:
        stripped = re.sub(rf"\b{curr}\b", "", stripped, flags=re.IGNORECASE)
    stripped = stripped.replace("$", "").replace(",", "").strip()

    # Pattern 1: 'k' or 'K' suffix (e.g. '12k', '1.5k', '2.25k')
    k_match = re.match(r"^(\d+)(?:\.(\d+))?[kK]$", stripped)
    if k_match:
        whole_str, frac_str = k_match.groups()
        whole = int(whole_str)
        # Max decimal digits allowed for k suffix without sub-cent precision is 2 (e.g. 1.25k = $1,250.00)
        # 1.234k would have 3 decimal places, which is rejected.
        if not frac_str:
            frac_cents = 0
        elif len(frac_str) == 1:
            frac_cents = int(frac_str) * 10000
        elif len(frac_str) == 2:
            frac_cents = int(frac_str) * 1000
        else:
            raise ValueError(f"Sub-cent precision in k suffix: {text}")
        total = whole * 100000 + frac_cents
        if total <= 0:
            raise ValueError("Amount must be strictly positive")
        return total

    # Pattern 2: Decimal or integer standard amount (e.g. '12500', '500.50', '0.99')
    std_match = re.match(r"^(\d+)(?:\.(\d+))?$", stripped)
    if std_match:
        whole_str, frac_str = std_match.groups()
        return _parse_decimal_str_to_cents(whole_str, frac_str or "")

    raise ValueError(f"Could not parse valid integer cents from: {text}")


def parse_request(text: str) -> dict:
    """Extract artwork_id, gross_minor, currency, and nonce from raw natural language text.

    Guarantees:
    - Adversarial prompt injection statements have zero impact on parsed values.
    - Currency defaults to 'USD' if not explicitly found.
    - Generates a cryptographically strong unique nonce.
    - Zero floats used anywhere.

    Args:
        text: Unstructured bid proposal text.

    Returns:
        Dictionary containing 'artwork_id', 'gross_minor', 'currency', and 'nonce'.

    Raises:
        ValueError: If input cannot be deterministically resolved to a single valid bid.
    """
    if not text or not text.strip():
        raise ValueError("Empty request text")

    # Reject explicit ambiguity phrases
    for pattern in _AMBIGUOUS_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"Ambiguous bid expression: {text}")

    # Extract artwork ID
    artwork_matches = _ARTWORK_ID_PATTERN.findall(text)
    if not artwork_matches:
        raise ValueError("No valid artwork ID found in bid text")
    # If multiple distinct artwork IDs found, reject as ambiguous
    unique_artworks = list(dict.fromkeys(artwork_matches))
    if len(unique_artworks) > 1:
        raise ValueError(f"Multiple artwork IDs found in bid text: {unique_artworks}")
    artwork_id = unique_artworks[0]

    # Extract currency (default USD)
    currency = "USD"
    for curr in _SUPPORTED_CURRENCIES:
        if re.search(rf"\b{curr}\b", text, re.IGNORECASE):
            currency = curr.upper()
            break

    # Check for explicitly negative bid amounts: e.g. "-500 USD", "-$500", "Bid -500"
    if re.search(r"(?:^|\s)-\s*\$?\s*\d+", text):
        raise ValueError(f"Negative bid amount not permitted: {text}")

    # Find monetary amount tokens in text
    amount_candidates = []

    # Check for $... amounts
    for match in re.finditer(r"\$\s*(\d[\d,]*(?:\.\d+)?)", text):
        amount_candidates.append(match.group(0))

    # Check for k suffix amounts (e.g. 10k, 25k, 1.5k)
    for match in re.finditer(r"\b(\d+(?:\.\d+)?)[kK]\b", text):
        amount_candidates.append(match.group(0))

    # Check for currency prefixed or suffixed amounts (e.g. 10000 USD, USD 10000)
    for curr in _SUPPORTED_CURRENCIES:
        for match in re.finditer(rf"\b{curr}\s*(\d[\d,]*(?:\.\d+)?)\b", text, re.IGNORECASE):
            amount_candidates.append(match.group(0))
        for match in re.finditer(rf"\b(\d[\d,]*(?:\.\d+)?)\s*{curr}\b", text, re.IGNORECASE):
            amount_candidates.append(match.group(0))

    # If no explicit formatted candidates, look for standalone positive integers
    # Be careful not to pick up the number in the artwork ID (e.g. 101 in HFA-101)
    # Also ignore percentages (e.g. 0%, 100%) so they don't count as bid amounts!
    if not amount_candidates:
        clean_for_plain = _ARTWORK_ID_PATTERN.sub(" ", text)
        clean_for_plain = re.sub(r"\b\d+%", " ", clean_for_plain)
        for match in re.finditer(r"\b(\d[\d,]*(?:\.\d+)?)\b", clean_for_plain):
            amount_candidates.append(match.group(0))

    if not amount_candidates:
        raise ValueError("No monetary amount found in bid text")

    # Parse candidate amounts to integer cents
    parsed_amounts = []
    for cand in amount_candidates:
        try:
            cents = parse_amount_cents(cand)
            parsed_amounts.append(cents)
        except ValueError:
            continue

    if not parsed_amounts:
        raise ValueError(f"Could not parse valid amount from candidates: {amount_candidates}")

    # If multiple distinct amounts were parsed, reject as ambiguous
    unique_amounts = set(parsed_amounts)
    if len(unique_amounts) > 1:
        raise ValueError(f"Multiple competing bid amounts found: {unique_amounts}")

    gross_minor = parsed_amounts[0]
    nonce = f"nonce-{uuid.uuid4().hex[:12]}"

    return {
        "artwork_id": artwork_id,
        "gross_minor": gross_minor,
        "currency": currency,
        "nonce": nonce,
    }
