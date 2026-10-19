"""Independent reference calculation for artwork payouts (Test Oracle).

Strict Rule (AGENTS.md & docs/CONTEXT.md):
- This module is used ONLY by tests to verify MeTTa reasoning outputs.
- It must NEVER be called by application runtime or production code.
- Pure integer arithmetic: minor units (cents) and basis points (bps).
- NO floats, NO round(), NO decimal literals, NO `/`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class CoOwnerShare:
    owner: str
    wallet: str
    bps: int
    amount_minor: int


@dataclass(frozen=True)
class PayoutProof:
    artwork_id: str
    currency: str
    gross: int
    platform_fee: int
    net: int
    artist_royalty: int
    community_cut: int
    pool: int
    co_owner_shares: tuple[CoOwnerShare, ...]
    dust: int
    community_total: int
    conservation_verified: bool


class OracleRejection(Exception):
    """Raised when the independent test oracle detects a covenant or validation violation.
    
    Canonical reason codes (docs/PROOF_SHAPE.md):
    - BELOW_RESERVE: Gross resale price is below registered reserve floor.
    - OVERRIDE_BELOW_FLOOR: Manager override attempted to breach artist royalty floor.
    - OVERRIDE_NOT_ALLOWED: Manager override attempted to decrease community fund cut.
    - ARTWORK_CONTESTED: Artwork status is marked CONTESTED.
    - UNSUPPORTED_CURRENCY: Currency does not match registered reserve currency.
    - DUPLICATE_NONCE: Replay attack detected by intake gateway / audit log.
    - ENGINE_UNAVAILABLE: Reasoning engine unmapped entity, timeout, or runtime failure.
    - LLM_MALFORMED_OUTPUT: Natural language bid could not be deterministically parsed.
    - INVALID_AMOUNT: Gross amount non-integer, negative, zero, float, or boolean.
    - AMOUNT_ABOVE_CAP: Proposed gross exceeds maximum supported transaction cap.
    - CAP_TABLE_INVALID: Cap table shares do not sum to 10,000 bps or deductions >= 10,000 bps.
    - ARTWORK_FLAGGED: Artwork carries active compliance/provenance flags.
    """
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"Rejected ({code}): {message}")
        self.code = code


class ConservationInvariantError(Exception):
    pass


def calculate_payout(
    artwork: dict,
    gross_minor: int,
    currency: str,
    override_royalty_bps: int | None = None,
    override_community_bps: int | None = None,
) -> PayoutProof:
    """Calculate the payout distribution according to CONTEXT Section 6.

    Uses integer floor division (//). Fails closed on any invariant violation.
    """
    if not isinstance(gross_minor, int) or isinstance(gross_minor, bool):
        raise OracleRejection("INVALID_AMOUNT", "Gross amount must be an integer")
    if gross_minor <= 0:
        raise OracleRejection("INVALID_AMOUNT", "Gross amount must be strictly positive")
    if gross_minor > 1_000_000_000:
        raise OracleRejection("AMOUNT_ABOVE_CAP", "Amount exceeds maximum accepted sale cap")

    # Validate currency match
    reserve_obj = artwork.get("reserve", {})
    reserve_currency = reserve_obj.get("currency", "USD")
    if currency != reserve_currency:
        raise OracleRejection("UNSUPPORTED_CURRENCY", f"Currency {currency} does not match reserve {reserve_currency}")

    # Reserve check
    reserve_minor = reserve_obj.get("amount_minor", 0)
    if gross_minor < reserve_minor:
        raise OracleRejection("BELOW_RESERVE", f"Gross {gross_minor} is below reserve {reserve_minor}")

    # Status and flag checks
    status = artwork.get("status", "LIVING")
    if status == "CONTESTED":
        raise OracleRejection("ARTWORK_CONTESTED", f"Artwork status is CONTESTED")

    flags = artwork.get("flags", [])
    if flags:
        raise OracleRejection("ARTWORK_FLAGGED", f"Artwork has flags: {flags}")

    # Rates
    royalty_bps = artwork.get("royalty_bps", 0)
    royalty_floor_bps = artwork.get("royalty_floor_bps", 0)
    community_bps = artwork.get("community_bps", 0)
    platform_fee_bps = artwork.get("platform_fee_bps", 0)

    # Manager override logic
    if override_royalty_bps is not None:
        if override_royalty_bps < royalty_floor_bps:
            raise OracleRejection("OVERRIDE_BELOW_FLOOR", f"Override {override_royalty_bps} is below floor {royalty_floor_bps}")
        royalty_bps = override_royalty_bps

    if override_community_bps is not None:
        if override_community_bps < community_bps:
            raise OracleRejection("OVERRIDE_NOT_ALLOWED", "Override cannot decrease community bps")
        community_bps = override_community_bps

    if royalty_bps + community_bps + platform_fee_bps >= 10000:
        raise OracleRejection("CAP_TABLE_INVALID", "Deductions equal or exceed 10000 bps")

    # Step 4: platform fee & net
    platform_fee = (gross_minor * platform_fee_bps) // 10000
    net = gross_minor - platform_fee

    # Step 5: artist, community, pool
    artist_royalty = (net * royalty_bps) // 10000
    community_cut = (net * community_bps) // 10000
    pool = net - artist_royalty - community_cut

    # Step 6: co-owner shares in fixed cap-table order
    cap_table = artwork.get("cap_table", [])
    owner_shares_list: list[CoOwnerShare] = []
    sum_owner_shares = 0
    cap_sum_bps = 0

    for entry in cap_table:
        owner_bps = entry["bps"]
        cap_sum_bps += owner_bps
        owner_share_minor = (pool * owner_bps) // 10000
        owner_shares_list.append(
            CoOwnerShare(
                owner=entry["owner"],
                wallet=entry["wallet"],
                bps=owner_bps,
                amount_minor=owner_share_minor,
            )
        )
        sum_owner_shares += owner_share_minor

    if cap_sum_bps != 10000:
        raise OracleRejection("CAP_TABLE_INVALID", f"Cap table sum is {cap_sum_bps}, must be 10000")

    # Step 7: dust goes to community fund
    dust = pool - sum_owner_shares
    if dust < 0:
        raise ConservationInvariantError(f"Negative dust calculated: {dust}")

    community_total = community_cut + dust

    # Step 8: Conservation invariant
    # fee + artist + community + sum(co-owners) + dust == gross
    total_distributed = platform_fee + artist_royalty + community_cut + sum_owner_shares + dust
    if total_distributed != gross_minor:
        raise ConservationInvariantError(
            f"Conservation violated: total {total_distributed} != gross {gross_minor}"
        )

    return PayoutProof(
        artwork_id=artwork["artwork_id"],
        currency=currency,
        gross=gross_minor,
        platform_fee=platform_fee,
        net=net,
        artist_royalty=artist_royalty,
        community_cut=community_cut,
        pool=pool,
        co_owner_shares=tuple(owner_shares_list),
        dust=dust,
        community_total=community_total,
        conservation_verified=True,
    )
