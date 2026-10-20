"""Fiduciary Settlement Proof Viewer & Interactive Simulator - Streamlit Dashboard.

Strict Rule (AGENTS.md & docs/PROOF_SHAPE.md):
- Displays proof atoms and reason codes verbatim from canonical proof fixtures and MeTTa runtime.
- ZERO money maths in the UI: numbers are displayed directly as stored in the proof.
- Prominent synthetic data banner.
- All monetary values are integer minor units (cents).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures" / "proofs"
ARTWORKS_PATH = ROOT_DIR / "data" / "artworks.json"
AUDIT_LOG_PATH = ROOT_DIR / "data" / "audit_log.json"


@st.cache_data
def load_all_fixtures() -> dict[str, dict[str, Any]]:
    fixtures: dict[str, dict[str, Any]] = {}
    if FIXTURES_DIR.exists():
        for f in sorted(FIXTURES_DIR.glob("*.json")):
            with open(f, "r", encoding="utf-8") as fp:
                fixtures[f.name] = json.load(fp)
    return fixtures


@st.cache_data
def load_artworks() -> list[dict[str, Any]]:
    if ARTWORKS_PATH.exists():
        with open(ARTWORKS_PATH, "r", encoding="utf-8") as fp:
            return json.load(fp)
    return []


def load_audit_log() -> list[dict[str, Any]]:
    if AUDIT_LOG_PATH.exists():
        try:
            with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            return []
    return []


def inject_custom_styles() -> None:
    st.markdown(
        """
        <style>
        /* Modern Glassmorphic / FinTech Theme */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }
        .main-header {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.12) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 14px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.8rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        .brand-badge {
            background: linear-gradient(90deg, #6366F1, #8B5CF6);
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            display: inline-block;
            margin-bottom: 0.5rem;
        }
        .title-text {
            font-size: 2.1rem;
            font-weight: 800;
            color: #F9FAFB;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .subtitle-text {
            font-size: 0.95rem;
            color: #9CA3AF;
            margin-top: 0.4rem;
        }
        .metric-card {
            background: rgba(19, 28, 46, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 1.1rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(99, 102, 241, 0.4);
        }
        .verdict-approved {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%);
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 10px;
            padding: 1rem;
            color: #10B981;
            font-weight: 700;
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .verdict-rejected {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%);
            border: 1px solid rgba(239, 68, 68, 0.4);
            border-radius: 10px;
            padding: 1rem;
            color: #EF4444;
            font-weight: 700;
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .flow-pill {
            display: inline-block;
            background: #1F2937;
            color: #E5E7EB;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-family: monospace;
            border: 1px solid #374151;
        }
        .badge-living {
            background: rgba(16, 185, 129, 0.2);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-estate {
            background: rgba(245, 158, 11, 0.2);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.4);
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="main-header">
            <span class="brand-badge">&#x25C6; TrustGate Protocol</span>
            <div class="title-text">Fractional Approval Agent &amp; Proof Viewer</div>
            <div class="subtitle-text">
                Deterministic Neuro-Symbolic Fiduciary Settlement &bull; Powered by MeTTa / Hyperon
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Mandatory Synthetic Data Notice (AGENTS.md)
    st.warning(
        "**Simulated, Synthetic Data Only:** All artwork IDs, prices, valuation curves, "
        "and wallet addresses are synthetic test fixtures designed for cryptographic verification benchmarks."
    )


def render_scenario_inspector(fixtures: dict[str, dict[str, Any]]) -> None:
    st.markdown("### Fiduciary Settlement Proof Inspector")
    st.caption("Inspect pre-computed canonical scenario proofs generated through the Hyperon symbolic reasoning kernel.")

    fixture_keys = list(fixtures.keys())
    
    col_sel, col_desc = st.columns([2, 3])
    with col_sel:
        selected_key = st.selectbox(
            "Select Scenario Fixture",
            fixture_keys,
            format_func=lambda k: f"{k.replace('.json', '').replace('_', ' ').upper()}",
            index=0,
        )
    
    proof = fixtures[selected_key]
    status = proof.get("status", "UNKNOWN")
    reason_code = proof.get("reason_code")
    producing_layer = proof.get("producing_layer", "unknown")
    artwork_id = proof.get("artwork_id", "N/A")
    currency = proof.get("currency", "USD")

    with col_desc:
        st.markdown(f"**Loaded Fixture:** `{selected_key}` &nbsp;|&nbsp; **Producing Layer:** `{producing_layer}`")
        if status == "APPROVED":
            st.markdown(
                '<div class="verdict-approved">&#x2714; VERDICT: APPROVED (Compliant Resale)</div>',
                unsafe_allow_html=True,
            )
        else:
            reason_label = reason_code if reason_code else "UNKNOWN_ERROR"
            st.markdown(
                f'<div class="verdict-rejected">&#x2716; VERDICT: REJECTED &mdash; {reason_label}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Core Metrics Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="Artwork ID", value=artwork_id)
    with c2:
        st.metric(label="Settlement Currency", value=currency)
    with c3:
        st.metric(label="Reason Code", value=str(reason_code) if reason_code else "None (Clean)")
    with c4:
        st.metric(label="Producing Layer", value=producing_layer)

    st.markdown("---")
    st.markdown("#### Conservation Breakdown (Integer Minor Units)")
    st.caption("All figures displayed directly as stored in the proof atom (Zero UI Math).")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Gross Amount", f"{proof.get('gross', 0):,} cents")
    m2.metric("Platform Fee", f"{proof.get('fee', 0):,} cents")
    m3.metric("Artist Royalty", f"{proof.get('artist', 0):,} cents")
    m4.metric("Community Fund", f"{proof.get('community', 0):,} cents")
    m5.metric("Swept Dust", f"{proof.get('dust', 0):,} cents")

    coowners = proof.get("coowners", [])
    if coowners:
        st.markdown("#### Fractional Co-Owner Payout Allocations")
        table_rows = []
        for c in coowners:
            table_rows.append(
                {
                    "Co-Owner": c.get("owner"),
                    "Wallet Address": c.get("wallet"),
                    "Disbursed Amount (cents)": f"{c.get('amount', 0):,} cents",
                }
            )
        st.table(table_rows)
    else:
        st.info("No co-owner disbursements. Payout accounts are empty (`coowners: []`).")

    with st.expander("Canonical Proof JSON Structure", expanded=False):
        st.json(proof)


def render_live_simulator() -> None:
    st.markdown("### Live Neuro-Symbolic Settlement Engine")
    st.caption("Submit a structured or natural language bid to trigger MeTTa verification.")

    from agent.settle import settle

    artworks = load_artworks()
    artwork_map = {art["artwork_id"]: art for art in artworks}
    artwork_options = list(artwork_map.keys())

    col_form, col_info = st.columns([3, 2])

    with col_form:
        selected_art_id = st.selectbox(
            "Select Target Artwork",
            artwork_options,
            format_func=lambda aid: f"{aid} - {artwork_map[aid].get('title', '')}",
        )
        target_art = artwork_map[selected_art_id]
        default_currency = target_art.get("reserve", {}).get("currency", "USD")

        input_mode = st.radio(
            "Input Mode",
            ["Structured Parameters", "Natural Language Bid"],
            horizontal=True,
        )

        override_enabled = st.checkbox("Apply Manager Override (Secondary Market Governance)")
        override_royalty_bps = None
        override_rationale = ""
        if override_enabled:
            override_royalty_bps = st.number_input(
                "Override Royalty BPS (Must be >= floor)",
                min_value=0,
                max_value=10000,
                value=target_art.get("royalty_bps", 1000),
                step=50,
            )
            override_rationale = st.text_input(
                "Governance Rationale (Min 15 chars)",
                value="Authorized fiduciary estate consensus override protocol",
            )

        submit_pressed = False
        settle_request: dict[str, Any] = {}

        if input_mode == "Structured Parameters":
            gross_minor_val = st.number_input(
                f"Gross Bid Amount in Minor Units ({default_currency} Cents)",
                min_value=1,
                max_value=1000000000,
                value=target_art.get("reserve", {}).get("amount_minor", 300000),
                step=10000,
            )
            nonce_val = st.text_input(
                "Transaction Nonce (Anti-Replay)",
                value=f"sim-tx-{selected_art_id.lower()}-live",
            )
            submit_pressed = st.button("Execute Settlement Through MeTTa", type="primary", use_container_width=True)

            if submit_pressed:
                settle_request = {
                    "artwork_id": selected_art_id,
                    "gross_minor": int(gross_minor_val),
                    "currency": default_currency,
                    "nonce": nonce_val,
                }
                if override_enabled:
                    settle_request["override"] = {
                        "royalty_bps": int(override_royalty_bps),
                        "rationale": override_rationale,
                    }
        else:
            bid_text = st.text_area(
                "Natural Language Bid Prompt",
                value=f"Offer ${target_art.get('reserve', {}).get('amount_minor', 300000) // 100:,} for {selected_art_id}",
            )
            nl_nonce = st.text_input("Transaction Nonce", value=f"nl-tx-{selected_art_id.lower()}-live")
            submit_pressed = st.button("Parse & Settle via Hyperon", type="primary", use_container_width=True)

            if submit_pressed:
                settle_request = {
                    "text": bid_text,
                    "nonce": nl_nonce,
                }
                if override_enabled:
                    settle_request["override"] = {
                        "royalty_bps": int(override_royalty_bps),
                        "rationale": override_rationale,
                    }

    with col_info:
        st.markdown("#### Target Asset Metadata")
        st.markdown(f"**Title:** {target_art.get('title')}")
        st.markdown(f"**Creator:** {target_art.get('creator_name')}")
        st.markdown(f"**Status:** `{target_art.get('status')}`")
        res_amt = target_art.get("reserve", {}).get("amount_minor", 0)
        res_curr = target_art.get("reserve", {}).get("currency", "USD")
        st.markdown(f"**Reserve Floor:** `{res_amt:,} {res_curr} cents`")
        st.markdown(f"**Royalty Baseline:** `{target_art.get('royalty_bps', 0)} bps` (Floor: `{target_art.get('royalty_floor_bps', 0)} bps`)")
        st.markdown(f"**Community Cut:** `{target_art.get('community_bps', 0)} bps`")
        st.markdown(f"**Platform Fee:** `{target_art.get('platform_fee_bps', 0)} bps`")

    if submit_pressed and settle_request:
        st.markdown("---")
        st.markdown("### Execution Result")
        with st.spinner("Evaluating symbolic invariants in Hyperon MeTTa..."):
            try:
                res_proof = settle(settle_request)
                res_status = res_proof.get("status")
                res_code = res_proof.get("reason_code")
                res_layer = res_proof.get("producing_layer")

                if res_status == "APPROVED":
                    st.success(f"**SETTLEMENT APPROVED** &mdash; Reason: {res_code or 'Compliant'} &nbsp;|&nbsp; Layer: `{res_layer}`")
                else:
                    st.error(f"**SETTLEMENT REJECTED** &mdash; Reason: `{res_code}` &nbsp;|&nbsp; Layer: `{res_layer}`")

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Gross Minor", f"{res_proof.get('gross', 0):,} cents")
                c2.metric("Platform Fee", f"{res_proof.get('fee', 0):,} cents")
                c3.metric("Artist Royalty", f"{res_proof.get('artist', 0):,} cents")
                c4.metric("Community Cut", f"{res_proof.get('community', 0):,} cents")
                c5.metric("Swept Dust", f"{res_proof.get('dust', 0):,} cents")

                with st.expander("Resulting Proof Atom (Canonical)", expanded=True):
                    st.json(res_proof)
            except Exception as e:
                st.error(f"Settlement failed closed with runtime error: {e}")


def render_registry_view() -> None:
    st.markdown("### Fractional Art Registry (Canonical Facts)")
    st.caption("Immutable smart contract covenants and fractional cap tables stored in `data/artworks.json`.")

    artworks = load_artworks()
    for art in artworks:
        with st.container():
            st.markdown(
                f"""
                <div class="metric-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #F3F4F6;">{art.get('artwork_id')} &mdash; {art.get('title')}</h4>
                        <span class="{'badge-living' if art.get('status') == 'LIVING' else 'badge-estate'}">{art.get('status')}</span>
                    </div>
                    <div style="color: #9CA3AF; margin-top: 0.3rem;">Creator: <b>{art.get('creator_name')}</b> ({art.get('creator_wallet')})</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("**Covenants:**")
                res = art.get("reserve", {})
                st.write(f"- Reserve Price: `{res.get('amount_minor', 0):,} {res.get('currency', 'USD')} cents`")
                st.write(f"- Artist Royalty: `{art.get('royalty_bps', 0)} bps` (Contractual Floor: `{art.get('royalty_floor_bps', 0)} bps`)")
                st.write(f"- Community Preservation: `{art.get('community_bps', 0)} bps`")
                st.write(f"- Platform Fee: `{art.get('platform_fee_bps', 0)} bps`")
            with col2:
                st.markdown("**Cap Table:**")
                cap_table = art.get("cap_table", [])
                st.dataframe(cap_table, use_container_width=True)


def render_audit_trail() -> None:
    st.markdown("### SHA-256 Hash-Chained Audit Log")
    st.caption("Verifiable, append-only cryptographic audit commitments stored in `data/audit_log.json`.")

    entries = load_audit_log()
    if not entries:
        st.info("No audit log records found. Execute a transaction in the Live Simulator to generate an entry.")
        return

    st.markdown(f"**Total Hash-Chained Commitments:** `{len(entries)}`")
    for idx, item in enumerate(reversed(entries)):
        proof_data = item.get("proof", {})
        status = proof_data.get("status", "UNKNOWN")
        st.markdown(
            f"""
            <div class="metric-card" style="margin-bottom: 0.8rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-family: monospace; color: #818CF8; font-weight: 600;">Block #{len(entries) - 1 - idx} &bull; Nonce: {item.get('nonce')}</span>
                    <span style="font-size: 0.8rem; color: #9CA3AF;">{item.get('timestamp')}</span>
                </div>
                <div style="font-size: 0.75rem; font-family: monospace; color: #6B7280; margin-top: 0.4rem; word-break: break-all;">
                    <b>HASH:</b> {item.get('entry_hash')} <br>
                    <b>PREV:</b> {item.get('prev_hash')}
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.85rem;">
                    Status: <b>{status}</b> &nbsp;|&nbsp; Artwork: <code>{proof_data.get('artwork_id')}</code> &nbsp;|&nbsp; Gross: <code>{proof_data.get('gross', 0):,} cents</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    st.set_page_config(
        page_title="TrustGate: Fractional Approval Agent",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_custom_styles()
    render_header()

    fixtures = load_all_fixtures()
    if not fixtures:
        st.error(f"No fixture files found in `{FIXTURES_DIR}`. Run `python scripts/generate_proof_fixtures.py`.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "Proof Inspector",
        "Live Simulator",
        "Artwork Registry",
        "Audit Trail",
    ])

    with tab1:
        render_scenario_inspector(fixtures)
    with tab2:
        render_live_simulator()
    with tab3:
        render_registry_view()
    with tab4:
        render_audit_trail()


if __name__ == "__main__":
    main()
