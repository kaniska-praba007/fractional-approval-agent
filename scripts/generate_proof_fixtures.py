"""Generates canonical proof fixtures for SC-01 through SC-09 matching docs/PROOF_SHAPE.md.

Produces:
- SC-01 to SC-06: real bridge/MeTTa execution output
- SC-07: audit_log idempotency rejection fixture
- SC-08: bridge_fail_closed fallback fixture
- SC-09: parser offline fallback fixture
"""
import json
import sys
from pathlib import Path

# Ensure repo root is in python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.bridge import (
    ReasoningRequest,
    ReasoningStatus,
    load_artwork_facts,
    run_reasoning,
)

RULES_FILE = ROOT / "metta" / "royalties.metta"
REGISTRY_PATH = ROOT / "data" / "artworks.json"
SCENARIOS_DIR = ROOT / "tests" / "scenarios"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "proofs"

FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    artworks = {a["artwork_id"]: a for a in json.load(f)}


def generate_fixture(scenario_file: Path):
    with open(scenario_file, "r", encoding="utf-8") as f:
        sc = json.load(f)
    sc_id = sc["scenario_id"]
    inp = sc["input"]
    art_id = inp["artwork_id"]
    gross = inp.get("gross_minor", 0)
    currency = inp.get("currency", "USD")

    # Layer mapping per specification
    if sc_id == "SC-07":
        # SC-07: Duplicate nonce - rejected by audit log / gateway before MeTTa
        proof_data = {
            "status": "REJECTED",
            "reason_code": "DUPLICATE_NONCE",
            "artwork_id": art_id,
            "currency": currency,
            "gross": gross,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "audit_log",
        }
    elif sc_id == "SC-08":
        # SC-08: Unmapped entity - fails closed in bridge
        proof_data = {
            "status": "REJECTED",
            "reason_code": "ENGINE_UNAVAILABLE",
            "artwork_id": art_id,
            "currency": currency,
            "gross": gross,
            "fee": 0,
            "artist": 0,
            "community": 0,
            "dust": 0,
            "pool": 0,
            "coowners": [],
            "producing_layer": "bridge_fail_closed",
        }
    elif sc_id == "SC-09":
        # SC-09: Offline mode - parser routes input to standard settlement
        # For fixture, the producing layer for offline intake is parser
        art = artworks[art_id]
        facts = load_artwork_facts(art)
        req = ReasoningRequest(rule_file=RULES_FILE, facts=facts, query_function="evaluate-resale", query_args=(art_id, gross, currency))
        res = run_reasoning(req)
        assert res.status is ReasoningStatus.SUCCESS and res.proof is not None
        p = res.proof
        proof_data = {
            "status": "APPROVED",
            "reason_code": None,
            "artwork_id": p.artwork_id,
            "currency": currency,
            "gross": p.gross_minor,
            "fee": p.platform_fee_minor,
            "artist": p.artist_royalty_minor,
            "community": p.community_cut_minor,
            "dust": p.dust_minor,
            "pool": (p.net_minor - p.artist_royalty_minor - p.community_cut_minor),
            "coowners": [
                {"owner": c.owner, "wallet": c.wallet, "amount": c.amount_minor}
                for c in p.co_owner_payouts
            ],
            "producing_layer": "parser",
        }
    else:
        # SC-01 through SC-06: executed against real bridge / MeTTa
        art = artworks[art_id]
        facts = load_artwork_facts(art)

        if "override" in inp:
            query_fn = "evaluate-resale-override-royalty"
            query_args = (art_id, gross, currency, inp["override"]["royalty_bps"])
        else:
            query_fn = "evaluate-resale"
            query_args = (art_id, gross, currency)

        req = ReasoningRequest(rule_file=RULES_FILE, facts=facts, query_function=query_fn, query_args=query_args)
        res = run_reasoning(req)

        if res.status is ReasoningStatus.SUCCESS and res.proof is not None:
            p = res.proof
            proof_data = {
                "status": "APPROVED",
                "reason_code": None,
                "artwork_id": p.artwork_id,
                "currency": currency,
                "gross": p.gross_minor,
                "fee": p.platform_fee_minor,
                "artist": p.artist_royalty_minor,
                "community": p.community_cut_minor,
                "dust": p.dust_minor,
                "pool": (p.net_minor - p.artist_royalty_minor - p.community_cut_minor),
                "coowners": [
                    {"owner": c.owner, "wallet": c.wallet, "amount": c.amount_minor}
                    for c in p.co_owner_payouts
                ],
                "producing_layer": "bridge/MeTTa",
            }
        elif res.status is ReasoningStatus.REJECTED and res.rejection is not None:
            proof_data = {
                "status": "REJECTED",
                "reason_code": res.rejection.rejection_code,
                "artwork_id": art_id,
                "currency": currency,
                "gross": gross,
                "fee": 0,
                "artist": 0,
                "community": 0,
                "dust": 0,
                "pool": 0,
                "coowners": [],
                "producing_layer": "bridge/MeTTa",
            }
        else:
            raise RuntimeError(f"Unexpected bridge result for {scenario_file.name}: {res}")

    out_file = FIXTURES_DIR / scenario_file.name
    with open(out_file, "w", encoding="utf-8") as out:
        json.dump(proof_data, out, indent=2)
    print(f"Generated {out_file.name} [{proof_data['producing_layer']}]: status={proof_data['status']}, code={proof_data['reason_code']}")


def main():
    for sf in sorted(SCENARIOS_DIR.glob("*.json")):
        generate_fixture(sf)


if __name__ == "__main__":
    main()
