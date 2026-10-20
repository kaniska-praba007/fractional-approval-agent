"""Tests validating data/artworks.json synthetic registry."""
import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "artworks.json"


def test_registry_file_exists_and_is_valid_json():
    assert REGISTRY_PATH.exists(), f"Missing {REGISTRY_PATH}"
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) >= 4


def test_registry_contains_required_artworks():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    artworks_by_id = {art["artwork_id"]: art for art in data}
    for expected_id in ["HFA-101", "HFA-102", "HFA-103", "TEST-DUST", "TEST-FEE", "TEST-KES"]:
        assert expected_id in artworks_by_id, f"Missing {expected_id} in registry"


def test_registry_strict_integer_and_no_floats():
    """Verify that every numeric field in data/artworks.json is strictly an int and not float/bool."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Raw check: no decimal points inside numbers
    # (Checking loaded objects first)
    data = json.loads(raw_text)

    def check_no_floats(obj, path=""):
        if isinstance(obj, float):
            raise AssertionError(f"Forbidden float found at {path}: {obj}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                check_no_floats(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                check_no_floats(v, f"{path}[{i}]")

    check_no_floats(data)


def test_registry_cap_tables_sum_to_10000():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for art in data:
        cap_table = art.get("cap_table", [])
        assert len(cap_table) > 0, f"Artwork {art['artwork_id']} has empty cap table"
        total_bps = sum(entry["bps"] for entry in cap_table)
        assert total_bps == 10000, f"Artwork {art['artwork_id']} cap table sums to {total_bps}, expected 10000"


def test_registry_business_rules_invariants():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for art in data:
        art_id = art["artwork_id"]
        # All synthetic
        assert art.get("synthetic") is True, f"{art_id} must have synthetic: true"
        # Platform fee 0 (except TEST-FEE platform fee benchmark)
        if art_id != "TEST-FEE":
            assert art.get("platform_fee_bps") == 0, f"{art_id} platform_fee_bps must be 0"
        else:
            assert art.get("platform_fee_bps") == 250, f"{art_id} platform_fee_bps must be 250"
        # Royalty floor <= royalty
        assert art.get("royalty_floor_bps", 0) <= art.get("royalty_bps", 0), (
            f"{art_id} royalty_floor_bps > royalty_bps"
        )
        # Reserve is positive integer
        assert art["reserve"]["amount_minor"] > 0
        assert isinstance(art["reserve"]["amount_minor"], int)
        assert not isinstance(art["reserve"]["amount_minor"], bool)
