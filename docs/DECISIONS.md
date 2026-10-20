# Architectural & Design Decisions Log

This document records the foundational architectural, mathematical, and workflow decisions made for the Fractional Approval Agent.

---

## Dated Decisions Log

- **2026-10-19 — Conservation Equation Definition:** `pool = gross - fee - artist - community`; `sum(coowner amounts) + dust = pool`; `dust` sweeps deterministically to the community fund (`community_total = community + dust`), ensuring exact zero-loss conservation `fee + artist + community + sum(shares) + dust == gross`.
  - *Reason:* Prevents fractional division round-off loss and guarantees that all unallocated single cents benefit community preservation.

- **2026-10-19 — Canonical Reason Codes Reference:** Standardized on 11 machine-readable failure reason codes (`BELOW_RESERVE`, `OVERRIDE_BELOW_FLOOR`, `OVERRIDE_NOT_ALLOWED`, `ARTWORK_CONTESTED`, `UNSUPPORTED_CURRENCY`, `DUPLICATE_NONCE`, `ENGINE_UNAVAILABLE`, `LLM_MALFORMED_OUTPUT`, `INVALID_AMOUNT`, `AMOUNT_ABOVE_CAP`, `CAP_TABLE_INVALID`, `ARTWORK_FLAGGED`).
  - *Reason:* Downstream layers (audit log, UI, manager console) require deterministic, unified error handling rather than ad-hoc strings.

- **2026-10-19 — Scenario SC-09 Classification:** SC-09 is classified as "Offline Mode Fallback, APPROVED", where the deterministic parser and MeTTa evaluate valid transaction parameters without an LLM.
  - *Reason:* Enforces AGENTS.md Hard Rule 9 requiring the core demo to operate 100% offline without API keys.

- **2026-10-19 — Fact Ingestion Boundary:** Facts ingested into the MeTTa AtomSpace originate strictly from `data/artworks.json` via `load_artwork_facts`.
  - *Reason:* Guarantees that untrusted runtime user prompts cannot inject fake reserve prices, living statuses, or arbitrary wallet destinations.

- **2026-10-19 — Authoritative Fiduciary Rules Location:** Settlement rules live strictly in `metta/royalties.metta`.
  - *Reason:* Adheres to AGENTS.md Hard Rule 2 ("MeTTa does all money maths"); prevents rule divergence between Python and symbolic layers.

- **2026-10-19 — Hyperon as Authoritative Engine; Omega Optional:** The pinned `hyperon==0.2.10` runtime is the authoritative execution engine; SingularityNET Omega is an optional enhancement and is completely off the critical path.
  - *Reason:* Core evaluation must remain fast, reproducible, and verifiable offline without Docker or external runtime dependencies.

- **2026-10-19 — Double-Entry Ledger Invariant:** `agent/ledger.py` copies amounts verbatim from verified proof atoms and only validates that debits and credits sum to zero; it never computes payouts.
  - *Reason:* Upholds strict separation of concerns and prevents shadow payout calculations outside MeTTa.

- **2026-10-19 — Strict Integer Cents Representation:** All money amounts are represented strictly in integer minor units (e.g. cents) and basis points (bps); no floats or decimals are permitted in Python, MeTTa, JSON, or UI.
  - *Reason:* Eliminates IEEE 754 floating-point inaccuracies, precision drift, and compliance audit failures.

- **2026-10-19 — Platform Fee Baseline:** Platform fee is 0 bps for all scenario artworks in `data/artworks.json`.
  - *Reason:* Reflects the initial zero-fee community promotion covenant for #BuyBlackArt on BASIX.Market while preserving the deductibility slot in the conservation formula.

- **2026-10-19 — Working Milestone Targets:** Working internal feature freeze is Tuesday 20 Oct 2026 at ~2:00 PM IST; target submission preparation at 7:00 PM IST; final submission lock at 8:30 PM IST.
  - *Reason:* Provides a safe 6.5-hour operational buffer to record the 3-minute video, verify submission checklists, and test clean clones.

- **2026-10-20 — Fee Deduction & Currency Edge Cases:** Non-zero platform fee deduction (SC-10) and same-currency settlement (SC-11) added; cross-currency FX is out of scope (fails closed with `UNSUPPORTED_CURRENCY`, SC-12).
  - *Reason:* Validates first-deduction remainder rounding and dynamic currency handling while avoiding floating-point or external FX rate oracle dependencies.

---

## Open & Unverified Questions

1. **Exact Official Platform Lock Time:**
   - *Status:* Unverified. While our team working schedule targets Tuesday 20 Oct 2026, 8:30 PM IST, the exact server-side platform lock on BASIX.Market needs human confirmation with hackathon organizers.

2. **Judging Rubric Priority Weighting:**
   - *Status:* Unverified. Whether the 30% technical weight prioritizes pure MeTTa symbolic reduction or end-to-end multi-agent orchestration remains subject to organizer clarification.

3. **Codebase Co-Ownership / MIT Licensing Terms:**
   - *Status:* Open. Confirmation needed from the human lead regarding whether external rights-holder synthetic tags affect open-source MIT licensing upon submission.

4. **Omega-on-PeTTa Symbolic Parity:**
   - *Status:* Unverified. Parity between SingularityNET Omega's Prolog/PeTTa interpreter and Hyperon 0.2.10 MeTTa syntax for complex recursive `cons-share` expressions has not been proven.
