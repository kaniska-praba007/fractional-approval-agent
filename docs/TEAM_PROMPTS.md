# Teammate Implementation Prompts

This document provides four self-contained, copy-paste prompts that team members can drop directly into their AI coding assistants (e.g. Antigravity IDE, Claude, or Cursor). Each prompt is pre-configured with the project's strict rules, branch targets, test contracts, and scope boundaries.

---

## Prompt 1: Hash-Chained Audit Trail (`agent/2.4-audit-log`)

```markdown
Read AGENTS.md and docs/BRANCHES.md first. Follow all repository rules strictly.

### Task Overview
You are implementing the append-only, SHA-256 hash-chained audit log with idempotency/nonce verification on branch `agent/2.4-audit-log`.

### Branch & Scope Rules
- **Branch from:** `main` (run: `git checkout main && git pull origin main && git checkout -b agent/2.4-audit-log`)
- **Files you may touch:** `agent/audit.py`, `tests/test_audit.py`, `data/audit_log.json`
- **Files forbidden to touch:** `metta/*`, `agent/bridge.py`, `data/artworks.json`, `app/*`
- **Dependencies:** Consumes the canonical proof dictionary defined in `docs/PROOF_SHAPE.md`. Does NOT require MeTTa or LLM.

### Non-Negotiable Financial & Engineering Constraints
1. **No money maths:** The audit logger records proofs emitted by the bridge; it does not calculate payouts.
2. **Integer units only:** Amounts are integer cents. Never use floats.
3. **Synthetic data only:** Label all demo entries as synthetic.
4. **No secrets:** Never commit API keys or private credentials.
5. **Fail closed:** If an audit record fails hash validation or contains a duplicate nonce, raise `AuditError("DUPLICATE_NONCE")`.

### Implementation Requirements
1. **Test-Driven Development:** Write `tests/test_audit.py` FIRST.
   - Test 1: Genesis block initialization with fixed previous hash `"0" * 64`.
   - Test 2: Appending a valid proof computes `SHA-256(prev_hash + timestamp + nonce + proof_payload)`.
   - Test 3: Detecting tampered log entries (chain validation raises `AuditIntegrityError`).
   - Test 4: Duplicate nonce check (`nonce` seen previously raises `AuditError("DUPLICATE_NONCE")`).
   - Test 5: Exporting log as an inspectable JSON list for the UI.
2. **Implementation (`agent/audit.py`):**
   - Implement `AuditEntry` dataclass: `index`, `timestamp_iso`, `nonce`, `prev_hash`, `entry_hash`, `payload`.
   - Implement `AuditLog` class with `record_proof(nonce: str, proof: dict) -> AuditEntry`.
   - Implement `verify_integrity() -> bool`.
   - Implement file persistence to `data/audit_log.json`.

### Verification & Completion
- Run tests: `pytest tests/test_audit.py -v` (must be 100% passing).
- Run full suite: `pytest` to ensure no regressions.
- Add an entry to `PROGRESS.md` under a new section documenting the audit log implementation.
- Commit format: `feat(audit): append-only hash-chained audit trail with idempotency check [2.4-audit-log]`
  Include: `Assisted-by: <tool and model>`
- Push to origin: `git push -u origin agent/2.4-audit-log`
- Open a Pull Request into `main`. Do NOT merge it.
```

---

## Prompt 2: Rule-Based Natural Language Parser (`parser/3.1-rule-parser`)

```markdown
Read AGENTS.md and docs/BRANCHES.md first. Follow all repository rules strictly.

### Task Overview
You are implementing the deterministic rule-based natural language bid parser on branch `parser/3.1-rule-parser`. This module converts unstructured human inputs into validated integer minor units.

### Branch & Scope Rules
- **Branch from:** `main` (run: `git checkout main && git pull origin main && git checkout -b parser/3.1-rule-parser`)
- **Files you may touch:** `agent/parser.py`, `tests/test_parser.py`
- **Files forbidden to touch:** `metta/*`, `agent/bridge.py`, `agent/audit.py`, `data/*`, `app/*`
- **Dependencies:** Pure Python standard library (regex, typing). No MeTTa or LLM required.

### Non-Negotiable Constraints
1. **Zero floats:** Output must be an integer minor unit (cents). No `float(amount)` or decimal arithmetic.
2. **Fail closed on ambiguity:** If a string is ambiguous (e.g. `"10 or 12k"`, `"around 500"`, `"free"`), reject with `ParserError("AMBIGUOUS_AMOUNT")`. Never guess!
3. **Adversarial defense:** Prompt injections (e.g., `"ignore previous instructions"`, `"(shell rm)"`, quotes, semicolons) must be detected and rejected.
4. **No secrets & synthetic data only.**

### Implementation Requirements
1. **Test-Driven Development:** Write `tests/test_parser.py` FIRST with at least 20 comprehensive test cases:
   - Valid formats: `"$10,000"`, `"10000 USD"`, `"12k"`, `"12.5k"` (reject or handle via integer 1250000 cents without float arithmetic: `int(12) * 100000 + int(5) * 10000`), `"5M"`, `"500,000 cents"`.
   - Currency extraction: Extracts `"USD"`, `"KES"`, default `"USD"`.
   - Artwork ID extraction: Extracts uppercase IDs matching `^[A-Z0-9]+-[A-Z0-9_-]+$` (e.g. `"HFA-101"`).
   - Ambiguity rejections: Reject `"10-12k"`, `"approx $500"`, `"best offer"`, `"-500"`, `"0"`.
   - Adversarial prompt injection rejections: At least 5 injection strings attempting to set 0 royalty or execute MeTTa expressions.
2. **Implementation (`agent/parser.py`):**
   - `@dataclass(frozen=True) class ParsedBid: artwork_id: str | None, amount_minor: int, currency: str, raw_text: str`.
   - Implement `parse_bid_intent(text: str) -> ParsedBid`.
   - Clean regex pattern matching without binary floating-point conversion.

### Verification & Completion
- Run tests: `pytest tests/test_parser.py -v` (all 20+ tests passing).
- Run full suite: `pytest` to confirm zero regressions.
- Add an entry to `PROGRESS.md`.
- Commit format: `feat(parser): rule-based bid parser with adversarial prompt rejection [3.1-rule-parser]`
  Include: `Assisted-by: <tool and model>`
- Push to origin: `git push -u origin parser/3.1-rule-parser`
- Open a Pull Request into `main`. Do NOT merge it.
```

---

## Prompt 3: Streamlit Compliance Dashboard (`ui/6.1-dashboard`)

```markdown
Read AGENTS.md and docs/BRANCHES.md first. Follow all repository rules strictly.

### Task Overview
You are building the multi-page Streamlit compliance and settlement dashboard on branch `ui/6.1-dashboard`. It provides an intuitive interface for collectors, gallery directors, and curators to inspect proofs and audit traces.

### Branch & Scope Rules
- **Branch from:** `main` (run: `git checkout main && git pull origin main && git checkout -b ui/6.1-dashboard`)
- **Files you may touch:** `app/Home.py`, `app/pages/*.py`, `tests/test_ui.py`
- **Files forbidden to touch:** `metta/*`, `agent/bridge.py`, `data/artworks.json`
- **Dependencies:** Uses Streamlit. Reads canonical proof fixtures from `tests/fixtures/proofs/` and metadata from `data/artworks.json`.

### Non-Negotiable Financial & UI Constraints
1. **NO money calculations in UI:** The UI NEVER multiplies, divides, or calculates cuts. It reads and renders values strictly from the proof fixture or bridge atom proof.
2. **Integer formatting only:** Convert integer cents to display strings using string formatting:
   `f"${cents // 100:,}.{cents % 100:02d}"`. NEVER call `float(cents) / 100`!
3. **Multi-page architecture:** Follow `docs/CONTEXT.md` §1 structure:
   - `app/Home.py`: Mission, #BuyBlackArt, Harlem Fine Arts Show (HFAS) context, ecosystem map.
   - `app/pages/1_🎨_Artwork_Registry.py`: Catalog cards with cap tables, reserve prices, and synthetic tags.
   - `app/pages/2_⚖️_Settle_Transaction.py`: Interactive simulation; trigger settlement and inspect proof fixtures.
   - `app/pages/3_🛡️_Manager_Console.py`: Glass-box audit trail view and manager override submission form.
   - `app/pages/4_📊_Treasury_&_Payouts.py`: Wallet yields, artist distributions, and Community Arts Fund balance.
4. **Rich aesthetics:** Use premium styling, dark mode accents, responsive layout, clear status badges (`APPROVED` in green, `REJECTED` in red).
5. **No placeholders:** Use real synthetic catalog data.

### Implementation Requirements
1. Write a smoke test in `tests/test_ui.py` verifying pages import and helper formatters format minor units without floats.
2. Build `app/Home.py` and the 4 pages.
3. Test locally: `streamlit run app/Home.py`

### Verification & Completion
- Run test: `pytest tests/test_ui.py -v`
- Run full suite: `pytest`
- Add an entry to `PROGRESS.md`.
- Commit format: `feat(ui): multi-page fiduciary compliance and treasury dashboard [6.1-dashboard]`
  Include: `Assisted-by: <tool and model>`
- Push to origin: `git push -u origin ui/6.1-dashboard`
- Open a Pull Request into `main`. Do NOT merge it.
```

---

## Prompt 4: Documentation & Final AI Disclosure (`docs/7.3-readme-disclosure`)

```markdown
Read AGENTS.md and docs/BRANCHES.md first. Follow all repository rules strictly.

### Task Overview
You are finalizing the project documentation, installation instructions, architecture breakdown, and full AI disclosure log on branch `docs/7.3-readme-disclosure`.

### Branch & Scope Rules
- **Branch from:** `main` (run: `git checkout main && git pull origin main && git checkout -b docs/7.3-readme-disclosure`)
- **Files you may touch:** `README.md`, `AI_DISCLOSURE.md`, `SUBMISSION.md`
- **Files forbidden to touch:** `agent/*`, `metta/*`, `app/*`, `data/*`

### Mandatory Content Requirements
1. **`README.md`:**
   - **Track & Challenge:** Track 02: Builders — Advanced; Challenge 01: Trusted With Money (HFAS Brief: #BuyBlackArt).
   - **Partner Brief Proposal Notice:** State clearly: *"This proposal is based on the Harlem Fine Arts Show (HFAS) brief for #BuyBlackArt."*
   - **Synthetic Data Compliance:** Explicit statement that all catalog records, wallet hashes, and transactions are synthetic placeholders marked `"synthetic": true`.
   - **Architecture Diagram:** Hybrid neural-symbolic cognitive architecture diagram (Perception -> Omega/Bridge -> Hyperon AtomSpace -> Audit Log -> Manager Console).
   - **Quickstart & Setup Instructions:** Verified clean clone commands on PowerShell:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     pip install -r requirements.txt
     pytest
     streamlit run app/Home.py
     ```
   - **Scenario Walkthroughs:** Overview of SC-01 through SC-09 showing how invariant proofs defend artist royalties and community funds.
2. **`AI_DISCLOSURE.md`:**
   - Comprehensive log detailing every AI tool used across the project lifecycle:
     - Antigravity AI Coding Assistant (planning, test scaffolding, MeTTa rules, bridge implementation).
     - Gemini 2.5 Flash (via OpenAI-compatible API for the live Omega cognitive loop integration spike).
     - Claude (if used for architecture review or document drafting).
     - State explicitly that Copilot was not used (or log it only if a teammate used it).
3. **`SUBMISSION.md`:**
   - Report each submission checklist item as passed, failed, or not applicable.

### Verification & Completion
- Verify that every markdown link and code block is valid.
- Run `pytest` to confirm working tree is clean.
- Add an entry to `PROGRESS.md`.
- Commit format: `docs: complete README, architecture map, and AI disclosure log [7.3-readme-disclosure]`
  Include: `Assisted-by: <tool and model>`
- Push to origin: `git push -u origin docs/7.3-readme-disclosure`
- Open a Pull Request into `main`. Do NOT merge it.
```
