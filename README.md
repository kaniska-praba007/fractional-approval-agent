# CuraFide - Fiduciary Fractional Settlement Agent
> **#BuyBlackArt on BASIX.Market**

[![CI](https://github.com/kaniska-praba007/fractional-approval-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/kaniska-praba007/fractional-approval-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Symbolic Engine: Hyperon 0.2.10](https://img.shields.io/badge/symbolic-Hyperon%200.2.10-purple)](https://github.com/trueagi-io/hyperon-experimental)

**Track:** Track 03: Next Level Devs 
**Challenge:** Challenge 01: Trusted With Money (HFAS Brief: #BuyBlackArt)

---

## Partner Brief Proposal Notice
> **Notice:** This proposal is based on the Harlem Fine Arts Show (HFAS) brief for **#BuyBlackArt** on BASIX.Market. All demonstration artwork catalog records, collector identities, and wallet addresses are synthetic placeholders marked `"synthetic": true`. No private or unreleased rights-holder data is used.

---

## 3-Minute Demo Video
- **Video Link:** [Watch the 3-Minute Demonstration Video](https://youtu.be/placeholder-demo-video)
- A 3-minute glass-box walkthrough demonstrating deterministic resale settlements, reserve floor protections, prompt injection defense, fiduciary manager overrides with statutory floor enforcement, replay defenses, and cryptographic SHA-256 audit log verification.

---

## Problem & Motivation

Fractional fine-art secondary markets require strict fiduciary trust. However, prevailing automated agent workflows suffer from critical vulnerabilities:
1. **IEEE 754 Floating-Point Inaccuracies:** Binary floating-point division (`/` or `round()`) leaks fractions of cents, failing strict audit standards.
2. **Probabilistic Hallucinations:** LLM-based financial calculation can hallucinate rates, waive royalties, or succumb to prompt injections.
3. **Black-Box Opacity:** Conventional ML systems cannot provide a step-by-step, mathematically proven justification trail.
4. **Destructive Overrides:** Traditional overrides rewrite database history, destroying non-repudiation.

---

## The Solution: Neuro-Symbolic Fiduciary Agent

**Finance TrustGate (CuraFide)** enforces mathematical certainty and transparent fiduciary governance:
- **MeTTa Does All Money Maths:** OpenCog Hyperon (`hyperon==0.2.10`) executes symbolic deduction rules in integer minor units (USD cents or KES cents) and basis points (bps).
- **Exact Conservation Equation:** Platform fee deducted first; net proceeds split into secondary royalty (*Droit de Suite*), community preservation cut, and cap-table shares; single-cent dust deterministically sweeps to the Community Arts Fund:
  $$\text{fee} + \text{artist} + \text{community} + \sum_{i} \text{amount}_i + \text{dust} \equiv \text{gross}$$
- **Fail-Closed Security:** Ambiguous inputs, reserve price breaches, unmapped assets, or illegal overrides halt with zero disbursed funds and emit standardized machine-readable reason codes.
- **Glass-Box Audit Trail:** Every transaction is committed to an append-only SHA-256 hash-chained log with nonce replay defenses.
- **Simulated Double-Entry Ledger:** Posts balanced debit and credit entries verifying zero-sum balance sheet reconciliation.

---

## The 9-Stage Pipeline Architecture

```text
messy text ──► parser ──► validation ──► bridge ──► MeTTa rules ──► proof ──► audit log ──► ledger ──► UI
```

| Layer | Component | Core Responsibility | Guarantees |
| :--- | :--- | :--- | :--- |
| **Intake / NLP** | `agent/parser.py` | Extracts `artwork_id`, `gross_minor`, and currency. | Strips prompt injections, fails closed on ambiguity, zero floats. |
| **Validation** | `agent/bridge.py` | Sanitizes inputs, allow-lists relations, verifies integers. | Rejects negative amounts, non-integers, booleans, and floats. |
| **Bridge** | `agent/bridge.py` | Traverses native Hyperon Atom API; manages runtime. | Zero string splitting; fail-closed on empty or multiple atoms. |
| **Symbolic Core** | `metta/royalties.metta` | Executes deduction hierarchy & cap-table splits. | Integer floor arithmetic, dust sweep, conservation assertion. |
| **Controller** | `agent/settle.py` | Coordinates pipeline stages end-to-end. | Runs 100% offline by default without external network or API keys. |
| **Audit Logger** | `agent/audit_log.py` | Commits proofs to append-only log with SHA-256 chain. | Nonce replay defense (`seen_nonce`), cryptographic verification. |
| **Double-Entry** | `agent/ledger.py` | Posts balanced journals copying proof values verbatim. | Verified zero-sum balance sheets; never computes payouts. |
| **Compliance UI** | `app/Home.py`, `app/pages/` | Visualizes proofs, audit logs, and overrides. | Reads values strictly from proof atoms; zero client-side math. |

---

## Scenario Walkthroughs (SC-01 through SC-12)

| Scenario | Title | Description | Expected Status | Reason Code |
| :--- | :--- | :--- | :--- | :--- |
| **SC-01** | Standard Resale | Resale of `HFA-101` for $10,000 (1,000,000¢) with Alice (60%) and Bob (40%). | `APPROVED` | `null` |
| **SC-02** | Below Reserve | Resale of `HFA-101` at $2,000 below registered $3,000 reserve floor. | `REJECTED` | `BELOW_RESERVE` |
| **SC-03** | Prompt Injection | Hostile bid attempting to set royalty to 0%; stored 12% covenant enforced. | `APPROVED` | `null` |
| **SC-04** | Manager Override | Estate bonus override (+200 bps) on `HFA-103` approved with valid rationale. | `APPROVED` | `null` |
| **SC-05** | Override Below Floor | Illegal override reducing royalty below statutory floor (5% < 10%). | `REJECTED` | `OVERRIDE_BELOW_FLOOR` |
| **SC-06** | Dust Sweep Precision | Odd-cent split (10,001¢) over 3333/3333/3334 shares; 1¢ swept to community. | `APPROVED` | `null` |
| **SC-07** | Replay Attack Defense | Resubmitting previously settled nonce blocked at intake. | `REJECTED` | `DUPLICATE_NONCE` |
| **SC-08** | Engine Fail-Closed | Unregistered artwork (`UNKNOWN-999`) returns empty atoms; funds remain locked. | `REJECTED` | `ENGINE_UNAVAILABLE` |
| **SC-09** | Offline Determinism | Natural language bid processed purely offline without external LLM API. | `APPROVED` | `null` |
| **SC-10** | Platform Fee Rounding| Resale on `TEST-FEE` with 250 bps fee; tests floor division fee rounding. | `APPROVED` | `null` |
| **SC-11** | Kenyan Shillings (KES)| Multi-currency settlement on `TEST-KES` transacted in KES cents. | `APPROVED` | `null` |
| **SC-12** | Currency Mismatch | Settlement in USD for KES-denominated asset fails closed safely. | `REJECTED` | `UNSUPPORTED_CURRENCY` |

---

## Tech Stack

- **Symbolic Reasoning Engine:** OpenCog Hyperon (`hyperon==0.2.10`).
- **Cognitive Operator Integration (Off Critical Path):** SingularityNET Omega.
- **Intake & Orchestration:** Python 3.10 – 3.12, Pydantic, Regular Expressions.
- **Cryptographic Audit:** SHA-256 Hash Chaining.
- **Double-Entry Ledger:** Zero-sum integer balance verification.
- **Frontend Dashboard:** Streamlit (`app/Home.py` and `app/pages/*.py`).
- **Testing & Quality Assurance:** Pytest, randomized invariant fuzzers, GitHub Actions CI.

---

## Clean Clone & Quickstart

### Prerequisites
- Python 3.10, 3.11, or 3.12 (required for Hyperon binary wheels).
- Git.

### Windows (PowerShell)
```powershell
git clone https://github.com/kaniska-praba007/fractional-approval-agent.git
cd fractional-approval-agent
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
pytest -q
streamlit run app/Home.py
```

### Linux / macOS (Bash)
```bash
git clone https://github.com/kaniska-praba007/fractional-approval-agent.git
cd fractional-approval-agent
chmod +x scripts/setup.sh
./scripts/setup.sh
source .venv/bin/activate
pytest -q
streamlit run app/Home.py
```

---

## Automated CI Guardrails

Every commit and pull request is automatically verified by GitHub Actions (`.github/workflows/ci.yml`):
1. **Decimal Guard in MeTTa:** Fails if decimal literals (`[0-9]+\.[0-9]+`) appear in `metta/*.metta`.
2. **Python Floating Point & Silent Error Guard:** Fails if `float(`, bare `except:`, or `except Exception: pass` appear in `agent/` or `app/`.
3. **Full Automated Test Suite:** Runs all unit, integration, MeTTa, and invariant tests via `pytest`.

---

## Repository Structure

```text
fractional-approval-agent/
├── README.md                  # Comprehensive architecture and onboarding guide
├── AI_DISCLOSURE.md           # Mandatory AI tool and assistant disclosure log
├── SUBMISSION.md              # Hackathon submission checklist
├── AGENTS.md                  # Strict team invariants and agent instructions
├── PROGRESS.md                # Sprint-by-sprint verifiable session log
├── data/
│   ├── artworks.json          # Synthetic catalog registry (integer cents & bps)
│   └── audit_log.json         # SHA-256 hash-chained audit log
├── metta/
│   ├── royalties.metta        # Authoritative symbolic settlement & rejection rules
│   └── tests/
│       └── test_royalties.metta # Direct Hyperon assertEqual test assertions
├── agent/
│   ├── parser.py              # Rule-based NLP bid parser with injection defense
│   ├── bridge.py              # Native Hyperon Atom API bridge & validator
│   ├── settle.py              # End-to-end pipeline orchestrator
│   ├── audit_log.py           # Append-only hash-chained audit trail & replay defense
│   └── ledger.py              # Simulated double-entry ledger in integer cents
├── app/
│   ├── Home.py                # Streamlit compliance dashboard landing page
│   ├── streamlit_app.py       # Standalone scenario proof viewer
│   └── pages/                 # Multi-page compliance and treasury views
├── tests/
│   ├── oracle.py              # Isolated pure-integer reference test calculation
│   ├── test_parser.py         # 49 NLP and adversarial injection tests
│   ├── test_bridge_settlement.py # End-to-end symbolic reduction integration tests
│   ├── test_audit.py          # Audit log cryptographic chain & replay tests
│   └── test_ledger.py         # Double-entry balance sheet reconciliation tests
└── scripts/
    ├── setup.ps1              # Automated Windows setup script
    └── setup.sh               # Automated POSIX setup script
```

---

## What We Build Next
1. **On-Chain Settlement Adapters:** Connect canonical proofs to smart contract escrow release triggers on EVM / Algorand / Hedera.
2. **Dynamic Cap-Table Governance:** Enable decentralized on-chain voting for estate-managed and DAO-owned art co-ops.
3. **Hardware Enclave Signatures:** Sign verified proof atoms inside confidential computing enclaves (Intel SGX / AWS Nitro) before ledger commitment.

---

## Team

- **Giridharan K** — NLP Rule Parser, Documentation & AI Disclosure, Test Suite Hardening
- **Harish Mohan** — Core MeTTa Rules, AtomSpace Bridge, Pipeline Architecture
- **Rakshitha** — Cryptographic Audit Trail & Replay Defense (`agent/audit_log.py`) & Simulated Double-Entry Ledger (`agent/ledger.py`)
- **Harish Mohan** - Streamlit Dashboard & UI 

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
