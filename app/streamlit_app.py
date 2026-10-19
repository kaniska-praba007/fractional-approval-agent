"""Fiduciary Settlement Proof Viewer - Streamlit Dashboard.

Strict Rule (AGENTS.md & docs/PROOF_SHAPE.md):
- Displays proof atoms and reason codes verbatim from canonical proof fixtures.
- ZERO money maths in the UI: numbers are displayed directly as stored in the proof.
- Prominent synthetic data banner.
"""
from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "proofs"


def load_all_fixtures() -> dict[str, dict]:
    fixtures = {}
    if FIXTURES_DIR.exists():
        for f in sorted(FIXTURES_DIR.glob("*.json")):
            with open(f, "r", encoding="utf-8") as fp:
                fixtures[f.name] = json.load(fp)
    return fixtures


def main():
    st.set_page_config(
        page_title="TrustGate: Proof Viewer",
        page_icon="🎨",
        layout="wide",
    )

    # Mandatory Synthetic Data Notice (AGENTS.md)
    st.warning("⚠️ **Simulated, synthetic data only.** All artwork IDs, prices, and wallet addresses are synthetic test fixtures.")

    st.title("🎨 Fractional Approval Agent: Proof Viewer")
    st.caption("Neuro-symbolic fiduciary compliance and royalty settlement proofs (MeTTa / Hyperon runtime).")

    fixtures = load_all_fixtures()
    if not fixtures:
        st.error(f"No fixture files found in `{FIXTURES_DIR}`. Run `python scripts/generate_proof_fixtures.py`.")
        return

    st.sidebar.header("Test Scenarios")
    fixture_names = list(fixtures.keys())
    selected_name = st.sidebar.selectbox("Select Scenario Fixture", fixture_names)

    proof = fixtures[selected_name]

    status = proof.get("status", "UNKNOWN")
    reason_code = proof.get("reason_code")
    layer = proof.get("producing_layer", "unknown")
    artwork_id = proof.get("artwork_id", "N/A")
    currency = proof.get("currency", "USD")

    # Header verdict card
    st.subheader(f"Scenario: `{selected_name}`")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if status == "APPROVED":
            st.success(f"**Verdict:** {status}")
        else:
            st.error(f"**Verdict:** {status}")

    with col2:
        st.info(f"**Producing Layer:** `{layer}`")

    with col3:
        st.metric(label="Artwork ID", value=artwork_id)

    with col4:
        if reason_code:
            st.error(f"**Reason Code:** `{reason_code}`")
        else:
            st.success("**Reason Code:** None (Clean Approval)")

    st.divider()

    # Financial Breakdown - verbatim from proof JSON (Zero UI calculation)
    st.subheader("Financial Breakdown (Integer Minor Units / Cents)")
    mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)

    mcol1.metric("Gross Amount", f"{proof.get('gross', 0):,} {currency}¢")
    mcol2.metric("Platform Fee", f"{proof.get('fee', 0):,} ¢")
    mcol3.metric("Artist Royalty", f"{proof.get('artist', 0):,} ¢")
    mcol4.metric("Community Cut", f"{proof.get('community', 0):,} ¢")
    mcol5.metric("Swept Dust", f"{proof.get('dust', 0):,} ¢")

    # Co-owner splits table
    coowners = proof.get("coowners", [])
    if coowners:
        st.write("#### Fractional Co-Owner Allocations")
        st.table([
            {
                "Co-Owner": c.get("owner"),
                "Wallet Address": c.get("wallet"),
                "Disbursed Amount (cents)": f"{c.get('amount', 0):,} ¢",
            }
            for c in coowners
        ])
    elif status == "REJECTED":
        st.info("No funds disbursed. Payout accounts are empty (`coowners: []`).")

    # Raw Proof JSON representation
    with st.expander("🔍 View Raw Proof JSON", expanded=True):
        st.json(proof)


if __name__ == "__main__":
    main()
