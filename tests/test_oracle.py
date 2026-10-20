"""Tests validating tests/oracle.py independent calculation and scenarios."""
import json
import random
from pathlib import Path
import pytest

from tests.oracle import calculate_payout, OracleRejection, ConservationInvariantError

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "artworks.json"
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"


@pytest.fixture
def registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {art["artwork_id"]: art for art in data}


def test_scenario_files_exist_and_parse():
    expected_scenarios = [f"sc0{i}" for i in range(1, 10)] + [f"sc{i}" for i in range(10, 13)]
    found = list(SCENARIOS_DIR.glob("*.json"))
    assert len(found) >= 12
    for s in expected_scenarios:
        matches = list(SCENARIOS_DIR.glob(f"{s}_*.json"))
        assert len(matches) == 1, f"Missing or duplicate scenario file for {s}"
        with open(matches[0], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "scenario_id" in data
            assert "input" in data
            assert "expected" in data


def test_oracle_sc01_standard_resale(registry):
    art = registry["HFA-101"]
    proof = calculate_payout(art, gross_minor=1000000, currency="USD")
    assert proof.gross == 1000000
    assert proof.platform_fee == 0
    assert proof.net == 1000000
    assert proof.artist_royalty == 150000
    assert proof.community_cut == 30000
    assert proof.dust == 0
    assert proof.community_total == 30000
    assert len(proof.co_owner_shares) == 2
    assert proof.co_owner_shares[0].owner == "alice"
    assert proof.co_owner_shares[0].amount_minor == 492000
    assert proof.co_owner_shares[1].owner == "bob"
    assert proof.co_owner_shares[1].amount_minor == 328000
    assert proof.conservation_verified is True


def test_oracle_sc02_below_reserve(registry):
    art = registry["HFA-101"]
    with pytest.raises(OracleRejection) as exc_info:
        calculate_payout(art, gross_minor=200000, currency="USD")
    assert exc_info.value.code == "BELOW_RESERVE"


def test_oracle_sc03_prompt_injection_stored_rule(registry):
    art = registry["HFA-102"]
    # Even if prompt injection is attempted, stored rules apply
    proof = calculate_payout(art, gross_minor=600000, currency="USD")
    assert proof.gross == 600000
    assert proof.artist_royalty == 72000  # USD 720.00 (12%)
    assert proof.community_cut == 18000   # USD 180.00 (3%)
    assert proof.dust == 0
    assert len(proof.co_owner_shares) == 1
    assert proof.co_owner_shares[0].owner == "charlie"
    assert proof.co_owner_shares[0].amount_minor == 510000


def test_oracle_sc04_manager_override(registry):
    art = registry["HFA-103"]
    # Manager increases royalty from 1000 to 1200 bps
    proof = calculate_payout(art, gross_minor=5000000, currency="USD", override_royalty_bps=1200)
    assert proof.gross == 5000000
    assert proof.artist_royalty == 600000
    assert proof.community_cut == 250000
    assert proof.dust == 0
    assert len(proof.co_owner_shares) == 3
    assert proof.co_owner_shares[0].owner == "dave"
    assert proof.co_owner_shares[0].amount_minor == 2075000
    assert proof.co_owner_shares[1].owner == "elena"
    assert proof.co_owner_shares[1].amount_minor == 1245000
    assert proof.co_owner_shares[2].owner == "frank"
    assert proof.co_owner_shares[2].amount_minor == 830000
    assert proof.conservation_verified is True


def test_oracle_sc05_override_below_floor(registry):
    art = registry["HFA-101"]
    with pytest.raises(OracleRejection) as exc_info:
        calculate_payout(art, gross_minor=1000000, currency="USD", override_royalty_bps=500)
    assert exc_info.value.code == "OVERRIDE_BELOW_FLOOR"


def test_oracle_sc06_dust_split(registry):
    art = registry["TEST-DUST"]
    proof = calculate_payout(art, gross_minor=10001, currency="USD")
    assert proof.gross == 10001
    assert proof.artist_royalty == 0
    assert proof.community_cut == 0
    assert proof.dust == 1
    assert proof.community_total == 1
    assert len(proof.co_owner_shares) == 3
    assert proof.co_owner_shares[0].amount_minor == 3333
    assert proof.co_owner_shares[1].amount_minor == 3333
    assert proof.co_owner_shares[2].amount_minor == 3334
    assert proof.conservation_verified is True


def test_oracle_sc10_platform_fee(registry):
    art = registry["TEST-FEE"]
    proof = calculate_payout(art, gross_minor=1000033, currency="USD")
    assert proof.gross == 1000033
    assert proof.platform_fee == 25000  # (1000033 * 250) // 10000 == 25000 (remainder 8250 floored)
    assert proof.net == 975033
    assert proof.artist_royalty == 97503  # (975033 * 1000) // 10000 == 97503
    assert proof.community_cut == 19500   # (975033 * 200) // 10000 == 19500
    assert proof.dust == 0
    assert proof.community_total == 19500
    assert len(proof.co_owner_shares) == 2
    assert proof.co_owner_shares[0].owner == "alice"
    assert proof.co_owner_shares[0].amount_minor == 514818
    assert proof.co_owner_shares[1].owner == "bob"
    assert proof.co_owner_shares[1].amount_minor == 343212
    assert proof.conservation_verified is True


def test_oracle_sc11_kes_same_currency(registry):
    art = registry["TEST-KES"]
    proof = calculate_payout(art, gross_minor=100000000, currency="KES")
    assert proof.gross == 100000000
    assert proof.currency == "KES"
    assert proof.platform_fee == 0
    assert proof.net == 100000000
    assert proof.artist_royalty == 10000000
    assert proof.community_cut == 3000000
    assert proof.dust == 0
    assert proof.community_total == 3000000
    assert len(proof.co_owner_shares) == 2
    assert proof.co_owner_shares[0].owner == "karanja"
    assert proof.co_owner_shares[0].amount_minor == 60900000
    assert proof.co_owner_shares[1].owner == "mutua"
    assert proof.co_owner_shares[1].amount_minor == 26100000
    assert proof.conservation_verified is True


def test_oracle_sc12_kes_currency_mismatch(registry):
    art = registry["TEST-KES"]
    with pytest.raises(OracleRejection) as exc_info:
        calculate_payout(art, gross_minor=1000000, currency="USD")
    assert exc_info.value.code == "UNSUPPORTED_CURRENCY"


def test_oracle_seeded_fuzz_conservation_invariant(registry):
    """Seed random generator and test 200 arbitrary transactions ensuring conservation invariant."""
    rng = random.Random(42)

    for art_id, art in registry.items():
        reserve = art["reserve"]["amount_minor"]
        curr = art["reserve"]["currency"]
        for _ in range(50):
            gross = rng.randint(reserve, min(reserve * 20 + 123456, 1_000_000_000))
            proof = calculate_payout(art, gross_minor=gross, currency=curr)
            # Verify conservation: fee + artist + community + sum(owners) + dust == gross
            total_distributed = (
                proof.platform_fee
                + proof.artist_royalty
                + proof.community_cut
                + sum(c.amount_minor for c in proof.co_owner_shares)
                + proof.dust
            )
            assert total_distributed == gross
            assert proof.community_total == proof.community_cut + proof.dust


def test_oracle_rejects_invalid_inputs(registry):
    art = registry["HFA-101"]
    # Boolean input (subclass of int in Python)
    with pytest.raises(OracleRejection):
        calculate_payout(art, gross_minor=True, currency="USD")  # type: ignore

    # Zero or negative
    with pytest.raises(OracleRejection):
        calculate_payout(art, gross_minor=0, currency="USD")
    with pytest.raises(OracleRejection):
        calculate_payout(art, gross_minor=-50000, currency="USD")

    # Currency mismatch
    with pytest.raises(OracleRejection):
        calculate_payout(art, gross_minor=1000000, currency="EUR")

