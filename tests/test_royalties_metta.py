"""Integration test running metta/tests/test_royalties.metta directly against Hyperon."""
from pathlib import Path
import pytest

pytest.importorskip("hyperon")
from hyperon import MeTTa

METTA_DIR = Path(__file__).resolve().parent.parent / "metta"
RULES_FILE = METTA_DIR / "royalties.metta"
TESTS_FILE = METTA_DIR / "tests" / "test_royalties.metta"


def test_direct_metta_royalties_test_file():
    """Execute all native assertEqual assertions in test_royalties.metta directly in Hyperon.

    Strict Rule (AGENTS.md):
    - Test MeTTa rules directly against the pinned hyperon runtime before writing Python around them.
    - Show the real output.
    """
    assert RULES_FILE.exists()
    assert TESTS_FILE.exists()

    runner = MeTTa()
    # Load rules into runner AtomSpace
    runner.run(RULES_FILE.read_text(encoding="utf-8"))

    # Run test assertions
    results = runner.run(TESTS_FILE.read_text(encoding="utf-8"))

    assert len(results) == 6, f"Expected 6 test results, got {len(results)}"
    for idx, res in enumerate(results):
        # In Hyperon, a passed assertEqual evaluates to [()]
        # A failed assertEqual evaluates to [(Error (assertEqual ...) "...")]
        assert len(res) == 1, f"Test {idx + 1} unexpected result count: {res}"
        atom_str = str(res[0])
        assert not atom_str.startswith("(Error"), f"Test {idx + 1} failed: {atom_str}"
        assert atom_str == "()", f"Test {idx + 1} did not succeed: {atom_str}"
