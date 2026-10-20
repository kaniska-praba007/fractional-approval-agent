"""HFAS #BuyBlackArt - Fractional Approval & Settlement Engine.

Streamlit Executive Compliance Dashboard & Fiduciary Settlement Console.

Strict Rules (AGENTS.md & docs/PROOF_SHAPE.md):
- Displays proof atoms and reason codes verbatim from canonical proof fixtures and MeTTa runtime.
- ZERO money maths in the UI: numbers are displayed directly as stored in the proof.
- Pure integer arithmetic (divmod) for plain-English financial formatting. Strictly NO floats.
- Prominent synthetic data notice banner.
- All JSON proof structures strictly housed in collapsed expanders labeled "Raw proof".
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


def format_money_dual(amount_minor: int | None, currency: str = "USD") -> str:
    """Format minor units to '$10,000.00 USD (1,000,000 cents)' using integer arithmetic only."""
    if amount_minor is None:
        amount_minor = 0
    if not isinstance(amount_minor, int):
        amount_minor = int(amount_minor)
    sign = "-" if amount_minor < 0 else ""
    major, minor = divmod(abs(amount_minor), 100)
    symbol = "$" if currency == "USD" else f"{currency} "
    return f"{sign}{symbol}{major:,}.{minor:02d} {currency} ({amount_minor:,} cents)"


def format_money_short(amount_minor: int | None, currency: str = "USD") -> str:
    """Format minor units to '$10,000.00 USD' using integer arithmetic only."""
    if amount_minor is None:
        amount_minor = 0
    if not isinstance(amount_minor, int):
        amount_minor = int(amount_minor)
    sign = "-" if amount_minor < 0 else ""
    major, minor = divmod(abs(amount_minor), 100)
    symbol = "$" if currency == "USD" else f"{currency} "
    return f"{sign}{symbol}{major:,}.{minor:02d} {currency}"


# Backward-compatibility alias
format_currency = format_money_dual


def inject_custom_styles() -> None:
    st.markdown(
        """
        <style>
        /* Modern Glassmorphic / FinTech Theme */
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }
        .main-header {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.16) 0%, rgba(168, 85, 247, 0.12) 100%);
            border: 1px solid rgba(99, 102, 241, 0.35);
            border-radius: 14px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
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
            font-size: 1.95rem;
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
        [data-testid="stMetricValue"] {
            font-size: 1.15rem !important;
            white-space: normal !important;
            word-break: break-word !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            color: #9CA3AF !important;
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
            <span class="brand-badge">&#x25C6; HFAS #BuyBlackArt Initiative</span>
            <div class="title-text">HFAS #BuyBlackArt &mdash; Fractional Approval &amp; Settlement Engine (Proposal Architecture)</div>
            <div class="subtitle-text">
                Deterministic Neuro-Symbolic Fiduciary Settlement &bull; Powered by MeTTa / Hyperon
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Mandatory Synthetic Data Notice (AGENTS.md)
    st.warning(
        "**Simulated Synthetic Benchmarks:** In accordance with the Harlem Fine Arts Show (HFAS) #BuyBlackArt brief, "
        "all artwork records, cap tables, valuation reserves, and wallet addresses are synthetic fixtures "
        "designed for verifiable fiduciary settlement benchmarks."
    )


def render_marketplace_settlement(fixtures: dict[str, dict[str, Any]]) -> None:
    st.markdown("### Marketplace Settlement & Fiduciary Verification")
    st.caption("Executive curator portal: Trigger primary and secondary resales, verify compliance, and inspect live payout distributions.")

    from agent.settle import settle

    artworks = load_artworks()
    artwork_map = {art["artwork_id"]: art for art in artworks}
    artwork_options = list(artwork_map.keys())

    col_form, col_info = st.columns([3, 2])

    with col_form:
        default_art_index = artwork_options.index("HFA-101") if "HFA-101" in artwork_options else 0
        selected_art_id = st.selectbox(
            "Select Target Artwork",
            artwork_options,
            index=default_art_index,
            format_func=lambda aid: f"{aid} - {artwork_map[aid].get('title', '')}",
        )
        target_art = artwork_map[selected_art_id]
        default_currency = target_art.get("reserve", {}).get("currency", "USD")

        input_mode = st.radio(
            "Input Mode",
            ["Structured Parameters", "Natural Language Bid"],
            horizontal=True,
        )

        submit_pressed = False
        settle_request: dict[str, Any] = {}
        default_bid_minor = 1000000 if selected_art_id == "HFA-101" else target_art.get("reserve", {}).get("amount_minor", 1000000)

        if input_mode == "Structured Parameters":
            gross_minor_val = st.number_input(
                f"Gross Bid Amount in Minor Units ({default_currency} Cents)",
                min_value=1,
                max_value=1000000000,
                value=default_bid_minor,
                step=10000,
            )
            nonce_val = st.text_input(
                "Transaction Nonce (Anti-Replay)",
                value=f"sim-tx-{selected_art_id.lower()}-live",
            )
            submit_pressed = st.button("Execute Settlement Through MeTTa", type="primary", width="stretch")

            if submit_pressed:
                settle_request = {
                    "artwork_id": selected_art_id,
                    "gross_minor": int(gross_minor_val),
                    "currency": default_currency,
                    "nonce": nonce_val,
                }
        else:
            default_bid_major, _ = divmod(default_bid_minor, 100)
            bid_text = st.text_area(
                "Natural Language Bid Prompt",
                value=f"Offer ${default_bid_major:,} for {selected_art_id}",
            )
            nl_nonce = st.text_input("Transaction Nonce", value=f"nl-tx-{selected_art_id.lower()}-live")
            submit_pressed = st.button("Parse & Settle via Hyperon", type="primary", width="stretch")

            if submit_pressed:
                settle_request = {
                    "text": bid_text,
                    "nonce": nl_nonce,
                }

    with col_info:
        st.markdown("#### Target Asset Metadata")
        st.markdown(f"**Title:** {target_art.get('title')}")
        st.markdown(f"**Creator:** {target_art.get('creator_name')}")
        st.markdown(f"**Status:** `{target_art.get('status')}`")
        res_amt = target_art.get("reserve", {}).get("amount_minor", 0)
        res_curr = target_art.get("reserve", {}).get("currency", "USD")
        st.markdown(f"**Reserve Floor:** `{format_money_dual(res_amt, res_curr)}`")
        st.markdown(f"**Royalty Baseline:** `{target_art.get('royalty_bps', 0)} bps` (Contractual Floor: `{target_art.get('royalty_floor_bps', 0)} bps`)")
        st.markdown(f"**Community Cut:** `{target_art.get('community_bps', 0)} bps`")
        st.markdown(f"**Platform Fee:** `{target_art.get('platform_fee_bps', 0)} bps`")

    # Settlement Execution Results
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
                    st.success(f"**SETTLEMENT APPROVED** &mdash; Reason: {res_code or 'Compliant Resale'} &nbsp;|&nbsp; Producing Layer: `{res_layer}`")
                else:
                    st.error(f"**SETTLEMENT REJECTED** &mdash; Reason: `{res_code}` &nbsp;|&nbsp; Producing Layer: `{res_layer}`")

                res_curr = res_proof.get("currency", default_currency)

                # Executive 4-Metric Grid (The Curator's Vital Signs)
                st.markdown("#### Executive Payout Allocation")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Gross Sale Price", format_money_dual(res_proof.get("gross", 0), res_curr))
                c2.metric("Artist Royalty (Droit de Suite)", format_money_dual(res_proof.get("artist", 0), res_curr))
                c3.metric("Community Preservation Fund", format_money_dual(res_proof.get("community", 0), res_curr))
                c4.metric("Fractional Net Pool", format_money_dual(res_proof.get("pool", 0), res_curr))

                # Secondary splits
                s1, s2 = st.columns(2)
                s1.metric("Platform Fee", format_money_dual(res_proof.get("fee", 0), res_curr))
                s2.metric("Swept Dust", format_money_dual(res_proof.get("dust", 0), res_curr))

                # Fractional co-owners table
                coowners = res_proof.get("coowners", [])
                if coowners:
                    st.markdown("#### Fractional Co-Owner Disbursements")
                    table_rows = []
                    for c in coowners:
                        table_rows.append(
                            {
                                "Co-Owner": c.get("owner"),
                                "Wallet Address": c.get("wallet"),
                                "Disbursed Amount": format_money_dual(c.get("amount", 0), res_curr),
                            }
                        )
                    st.table(table_rows)

                with st.expander("Raw proof", expanded=False):
                    st.json(res_proof)
            except Exception as e:
                st.error(f"Settlement failed closed with runtime error: {e}")

    # Secondary / Benchmarks Expander
    st.markdown("---")
    with st.expander("Stress-Test & Cross-Border Benchmarks", expanded=False):
        st.markdown("#### Pre-Computed Canonical Proof Benchmarks")
        st.caption("Inspect verification fixtures (TEST-DUST, TEST-KES, TEST-FEE, below reserve, duplicate nonce).")

        fixture_keys = list(fixtures.keys())
        sc_selected_key = st.selectbox(
            "Select Benchmark Scenario Fixture",
            fixture_keys,
            format_func=lambda k: f"{k.replace('.json', '').replace('_', ' ').upper()}",
            index=0,
            key="benchmark_fixture_selector",
        )

        sc_proof = fixtures[sc_selected_key]
        sc_status = sc_proof.get("status", "UNKNOWN")
        sc_reason_code = sc_proof.get("reason_code")
        sc_producing_layer = sc_proof.get("producing_layer", "unknown")
        sc_currency = sc_proof.get("currency", "USD")

        if sc_status == "APPROVED":
            st.markdown(f'<div class="verdict-approved">&#x2714; VERDICT: APPROVED (Compliant Resale) &nbsp;|&nbsp; Producing Layer: <code>{sc_producing_layer}</code></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-rejected">&#x2716; VERDICT: REJECTED &mdash; {sc_reason_code} &nbsp;|&nbsp; Producing Layer: <code>{sc_producing_layer}</code></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        bc1, bc2, bc3, bc4 = st.columns(4)
        bc1.metric("Gross Amount", format_money_dual(sc_proof.get("gross", 0), sc_currency))
        bc2.metric("Artist Royalty", format_money_dual(sc_proof.get("artist", 0), sc_currency))
        bc3.metric("Community Fund", format_money_dual(sc_proof.get("community", 0), sc_currency))
        bc4.metric("Fractional Net Pool", format_money_dual(sc_proof.get("pool", 0), sc_currency))

        sc_coowners = sc_proof.get("coowners", [])
        if sc_coowners:
            st.markdown("**Disbursements:**")
            sc_table_rows = [
                {
                    "Co-Owner": c.get("owner"),
                    "Wallet Address": c.get("wallet"),
                    "Disbursed Amount": format_money_dual(c.get("amount", 0), sc_currency),
                }
                for c in sc_coowners
            ]
            st.table(sc_table_rows)

        with st.expander("Raw proof", expanded=False):
            st.json(sc_proof)


def render_manager_override() -> None:
    st.markdown("### Fiduciary Manager Governance Console")
    st.caption("Governance portal: Apply transparent secondary market overrides strictly bounded by statutory floor covenants.")

    from agent.settle import settle

    st.info(
        "🛡️ **Fiduciary Governance Guardrail:** Secondary market overrides are evaluated directly by MeTTa symbolic invariants. "
        "Royalty adjustments may only increase artist or community allocations and must strictly respect the contractual "
        "floor (1,000 bps / 10.00%). Violations are fail-closed and strictly rejected by MeTTa."
    )

    artworks = load_artworks()
    artwork_map = {art["artwork_id"]: art for art in artworks}
    artwork_options = list(artwork_map.keys())

    col_form, col_info = st.columns([3, 2])

    with col_form:
        default_art_index = artwork_options.index("HFA-101") if "HFA-101" in artwork_options else 0
        selected_art_id = st.selectbox(
            "Target Artwork for Governance Action",
            artwork_options,
            index=default_art_index,
            format_func=lambda aid: f"{aid} - {artwork_map[aid].get('title', '')}",
            key="override_art_selector",
        )
        target_art = artwork_map[selected_art_id]
        currency = target_art.get("reserve", {}).get("currency", "USD")

        current_bps = target_art.get("royalty_bps", 1000)
        floor_bps = target_art.get("royalty_floor_bps", 1000)

        override_royalty_bps = st.number_input(
            f"Proposed Royalty Rate in BPS (Must be >= floor {floor_bps} bps)",
            min_value=floor_bps,
            max_value=10000,
            value=max(current_bps, floor_bps + 500),
            step=50,
        )

        override_rationale = st.text_area(
            "Mandatory Fiduciary Governance Rationale (Min 15 chars)",
            value="Authorized fiduciary estate consensus override protocol",
        )

        override_nonce = st.text_input(
            "Governance Nonce (Anti-Replay)",
            value=f"gov-override-{selected_art_id.lower()}-v1",
        )

        override_gross_minor = st.number_input(
            f"Gross Settlement Amount in Minor Units ({currency} Cents)",
            min_value=1,
            max_value=1000000000,
            value=1000000 if selected_art_id == "HFA-101" else target_art.get("reserve", {}).get("amount_minor", 1000000),
            step=10000,
            key="override_gross_input",
        )

        submit_override = st.button("Submit Fiduciary Override to MeTTa", type="primary", width="stretch")

    with col_info:
        st.markdown("#### Contractual Covenants & Invariant Bounds")
        st.markdown(f"**Asset:** `{selected_art_id}` &mdash; {target_art.get('title')}")
        st.markdown(f"**Creator:** {target_art.get('creator_name')} ({target_art.get('creator_wallet')})")
        st.markdown(f"**Status:** `{target_art.get('status')}`")
        res_amt = target_art.get("reserve", {}).get("amount_minor", 0)
        st.markdown(f"**Reserve Floor:** `{format_money_dual(res_amt, currency)}`")
        st.markdown(f"**Statutory Floor Covenant:** `{floor_bps} bps`")
        st.markdown(f"**Current Baseline Royalty:** `{current_bps} bps`")
        st.markdown(f"**Proposed Override Royalty:** `{override_royalty_bps} bps`")

        if override_royalty_bps < floor_bps:
            st.error(f"Invariant Violation: Proposed rate ({override_royalty_bps} bps) is below floor ({floor_bps} bps).")
        else:
            st.success(f"Compliant Proposal: Proposed rate ({override_royalty_bps} bps) satisfies floor covenant.")

    if submit_override:
        st.markdown("---")
        st.markdown("### Governance Execution Verdict")
        if len(override_rationale.strip()) < 15:
            st.error("Rejection: Governance rationale must be at least 15 characters.")
            return

        settle_request = {
            "artwork_id": selected_art_id,
            "gross_minor": int(override_gross_minor),
            "currency": currency,
            "nonce": override_nonce,
            "override": {
                "royalty_bps": int(override_royalty_bps),
                "rationale": override_rationale,
            },
        }

        with st.spinner("Submitting override to MeTTa invariant kernel..."):
            try:
                res_proof = settle(settle_request)
                res_status = res_proof.get("status")
                res_code = res_proof.get("reason_code")
                res_layer = res_proof.get("producing_layer")

                if res_status == "APPROVED":
                    st.success(f"**OVERRIDE APPROVED** &mdash; Reason: {res_code or 'Compliant Floor Bound'} &nbsp;|&nbsp; Producing Layer: `{res_layer}`")
                else:
                    st.error(f"**OVERRIDE REJECTED** &mdash; Reason: `{res_code}` &nbsp;|&nbsp; Producing Layer: `{res_layer}`")

                res_curr = res_proof.get("currency", currency)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Gross Sale Price", format_money_dual(res_proof.get("gross", 0), res_curr))
                c2.metric("Elevated Artist Royalty", format_money_dual(res_proof.get("artist", 0), res_curr))
                c3.metric("Community Fund", format_money_dual(res_proof.get("community", 0), res_curr))
                c4.metric("Fractional Net Pool", format_money_dual(res_proof.get("pool", 0), res_curr))

                coowners = res_proof.get("coowners", [])
                if coowners:
                    st.markdown("#### Adjusted Co-Owner Disbursements")
                    table_rows = [
                        {
                            "Co-Owner": c.get("owner"),
                            "Wallet Address": c.get("wallet"),
                            "Disbursed Amount": format_money_dual(c.get("amount", 0), res_curr),
                        }
                        for c in coowners
                    ]
                    st.table(table_rows)

                with st.expander("Raw proof", expanded=False):
                    st.json(res_proof)
            except Exception as e:
                st.error(f"Governance execution failed closed: {e}")


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
                st.write(f"- Reserve Price: `{format_money_dual(res.get('amount_minor', 0), res.get('currency', 'USD'))}`")
                st.write(f"- Artist Royalty: `{art.get('royalty_bps', 0)} bps` (Contractual Floor: `{art.get('royalty_floor_bps', 0)} bps`)")
                st.write(f"- Community Preservation: `{art.get('community_bps', 0)} bps`")
                st.write(f"- Platform Fee: `{art.get('platform_fee_bps', 0)} bps`")
            with col2:
                st.markdown("**Cap Table:**")
                cap_table = art.get("cap_table", [])
                st.dataframe(cap_table, width="stretch")


def render_audit_trail() -> None:
    st.markdown("### SHA-256 Hash-Chained Audit Log")
    st.caption("Verifiable, append-only cryptographic audit commitments stored in `data/audit_log.json`.")

    entries = load_audit_log()
    if not entries:
        st.info("No audit log records found. Execute a transaction in Marketplace Settlement to generate an entry.")
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
                    <b>HASH:</b> {item.get('hash')} <br>
                    <b>PREV:</b> {item.get('prev_hash')}
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.85rem;">
                    Status: <b>{status}</b> &nbsp;|&nbsp; Artwork: <code>{proof_data.get('artwork_id')}</code> &nbsp;|&nbsp; Gross: <code>{format_money_dual(proof_data.get('gross', 0), proof_data.get('currency', 'USD'))}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Raw proof", expanded=False):
            st.json(proof_data)


def main():
    st.set_page_config(
        page_title="HFAS #BuyBlackArt — Fractional Approval Agent",
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
        "Marketplace Settlement",
        "Fiduciary Manager Override",
        "Immutable Audit Log",
        "Artwork & Cap Table Registry",
    ])

    with tab1:
        render_marketplace_settlement(fixtures)
    with tab2:
        render_manager_override()
    with tab3:
        render_audit_trail()
    with tab4:
        render_registry_view()


if __name__ == "__main__":
    main()
