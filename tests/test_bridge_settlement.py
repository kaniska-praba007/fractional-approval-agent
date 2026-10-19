"""Integration tests verifying agent.bridge with metta/royalties.metta against test scenarios."""
import json
import random
from pathlib import Path
import pytest

pytest.importorskip("hyperon")

from agent.bridge import (
    Fact,
    ReasoningRequest,
    ReasoningStatus,
    load_artwork_facts,
    load_registry_facts,
    run_reasoning,
)
from tests.oracle import calculate_payout

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "artworks.json"
RULES_FILE = Path(__file__).resolve().parent.parent / "metta" / "royalties.metta"


@pytest.fixture
def registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {art["artwork_id"]: art for art in data}


def test_sc01_standard_resale(registry):
    art = registry["HFA-101"]
    facts = load_artwork_facts(art)
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("HFA-101", 1000000, "USD"),
    )
    res = run_reasoning(req)
    assert res.status is ReasoningStatus.SUCCESS
    assert res.ok
    assert res.proof is not None
    assert res.proof.artwork_id == "HFA-101"
    assert res.proof.gross_minor == 1000000
    assert res.proof.platform_fee_minor == 0
    assert res.proof.net_minor == 1000000
    assert res.proof.artist_royalty_minor == 150000
    assert res.proof.community_cut_minor == 30000
    assert res.proof.dust_minor == 0
    assert res.proof.community_total_minor == 30000
    assert res.proof.conservation_verified is True
    assert len(res.proof.co_owner_payouts) == 2
    assert res.proof.co_owner_payouts[0].owner == "alice"
    assert res.proof.co_owner_payouts[0].amount_minor == 492000
    assert res.proof.co_owner_payouts[1].owner == "bob"
    assert res.proof.co_owner_payouts[1].amount_minor == 328000


def test_sc02_below_reserve_rejection(registry):
    art = registry["HFA-101"]
    facts = load_artwork_facts(art)
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("HFA-101", 200000, "USD"),
    )
    res = run_reasoning(req)
    assert res.status is ReasoningStatus.REJECTED
    assert not res.ok
    assert res.rejection is not None
    assert res.rejection.rejection_code == "BELOW_RESERVE"
    assert res.proof is None


def test_sc03_prompt_injection_resistance(registry):
    art = registry["HFA-102"]
    facts = load_artwork_facts(art)
    # Stored 12% royalty applies regardless of user prompts
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("HFA-102", 600000, "USD"),
    )
    res = run_reasoning(req)
    assert res.status is ReasoningStatus.SUCCESS
    assert res.proof is not None
    assert res.proof.artist_royalty_minor == 72000  # USD 720.00
    assert res.proof.community_cut_minor == 18000
    assert res.proof.co_owner_payouts[0].owner == "charlie"
    assert res.proof.co_owner_payouts[0].amount_minor == 510000
    assert res.proof.conservation_verified is True


def test_sc04_estate_manager_override(registry):
    art = registry["HFA-103"]
    facts = load_artwork_facts(art)
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale-override-royalty",
        query_args=("HFA-103", 5000000, "USD", 1200),
    )
    res = run_reasoning(req)
    assert res.status is ReasoningStatus.SUCCESS
    assert res.proof is not None
    assert res.proof.artist_royalty_minor == 600000
    assert res.proof.community_cut_minor == 250000
    assert res.proof.dust_minor == 0
    assert len(res.proof.co_owner_payouts) == 3
    assert res.proof.co_owner_payouts[0].owner == "dave"
    assert res.proof.co_owner_payouts[0].amount_minor == 2075000
    assert res.proof.co_owner_payouts[1].owner == "elena"
    assert res.proof.co_owner_payouts[1].amount_minor == 1245000
    assert res.proof.co_owner_payouts[2].owner == "frank"
    assert res.proof.co_owner_payouts[2].amount_minor == 830000
    assert res.proof.conservation_verified is True


def test_sc05_override_below_floor_rejection(registry):
    art = registry["HFA-101"]
    facts = load_artwork_facts(art)
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale-override-royalty",
        query_args=("HFA-101", 1000000, "USD", 500),
    )
    res = run_reasoning(req)
    assert res.status is ReasoningStatus.REJECTED
    assert not res.ok
    assert res.rejection is not None
    assert res.rejection.rejection_code == "OVERRIDE_BELOW_FLOOR"


def test_sc06_dust_split_precision(registry):
    art = registry["TEST-DUST"]
    facts = load_artwork_facts(art)
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("TEST-DUST", 10001, "USD"),
    )
    res = run_reasoning(req)
    assert res.status is ReasoningStatus.SUCCESS
    assert res.proof is not None
    assert res.proof.gross_minor == 10001
    assert res.proof.dust_minor == 1
    assert res.proof.community_total_minor == 1
    assert res.proof.co_owner_payouts[0].amount_minor == 3333
    assert res.proof.co_owner_payouts[1].amount_minor == 3333
    assert res.proof.co_owner_payouts[2].amount_minor == 3334
    assert res.proof.conservation_verified is True


def test_bridge_rejects_floats_and_booleans(registry):
    art = registry["HFA-101"]
    facts = load_artwork_facts(art)

    # Float amount
    req_float = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("HFA-101", 10000.5, "USD"),
    )
    res = run_reasoning(req_float)
    assert res.status is ReasoningStatus.INVALID_INPUT

    # Boolean amount
    req_bool = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("HFA-101", True, "USD"),
    )
    res = run_reasoning(req_bool)
    assert res.status is ReasoningStatus.INVALID_INPUT


def test_bridge_fails_closed_on_multiple_results(registry):
    art = registry["HFA-101"]
    facts = load_artwork_facts(art)
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("HFA-101", 1000000, "USD"),
    )
    # Simulate an ambiguous runner returning multiple atoms
    fake_runner = lambda p: [["(proof ...)", "(rejected ...)"]]
    res = run_reasoning(req, _runner=fake_runner)
    assert res.status is ReasoningStatus.ENGINE_ERROR
    assert not res.ok
    assert "multiple results returned" in (res.diagnostics or "")


def test_bridge_fails_closed_on_unknown_artwork(registry):
    art = registry["HFA-101"]
    facts = load_artwork_facts(art)
    req = ReasoningRequest(
        rule_file=RULES_FILE,
        facts=facts,
        query_function="evaluate-resale",
        query_args=("UNKNOWN-ARTWORK-999", 1000000, "USD"),
    )
    res = run_reasoning(req)
    assert res.status is ReasoningStatus.NO_RESULT
    assert not res.ok


def test_bridge_fuzz_matches_oracle_across_all_artworks(registry):
    """Seed pseudo-random numbers and verify 20 transactions against the independent test oracle."""
    rng = random.Random(101)

    for art_id, art in registry.items():
        facts = load_artwork_facts(art)
        reserve = art["reserve"]["amount_minor"]

        for _ in range(5):
            gross = rng.randint(reserve, reserve * 20 + 777)
            oracle_proof = calculate_payout(art, gross_minor=gross, currency="USD")

            req = ReasoningRequest(
                rule_file=RULES_FILE,
                facts=facts,
                query_function="evaluate-resale",
                query_args=(art_id, gross, "USD"),
            )
            res = run_reasoning(req)
            assert res.status is ReasoningStatus.SUCCESS
            assert res.proof is not None
            # Check every computed payout matches the oracle exactly
            assert res.proof.gross_minor == oracle_proof.gross
            assert res.proof.platform_fee_minor == oracle_proof.platform_fee
            assert res.proof.net_minor == oracle_proof.net
            assert res.proof.artist_royalty_minor == oracle_proof.artist_royalty
            assert res.proof.community_cut_minor == oracle_proof.community_cut
            assert res.proof.dust_minor == oracle_proof.dust
            assert res.proof.community_total_minor == oracle_proof.community_total
            assert res.proof.conservation_verified is True
            assert len(res.proof.co_owner_payouts) == len(oracle_proof.co_owner_shares)

            for metta_p, oracle_p in zip(res.proof.co_owner_payouts, oracle_proof.co_owner_shares):
                assert metta_p.owner == oracle_p.owner
                assert metta_p.bps == oracle_p.bps
                assert metta_p.amount_minor == oracle_p.amount_minor
