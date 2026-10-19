# Ready-to-Paste GitHub Issues

Copy and paste these issue templates directly into GitHub Issues before starting the parallel sprints.
**Milestone Target:** Internal Code Freeze — **Tuesday 20 Oct 2026, 2:00 PM IST**.

---

### Issue 1: `agent/2.4-audit-log`
**Title:** `feat(audit): implement append-only SHA-256 hash-chained audit log [2.4-audit-log]`
**Milestone / Label:** `freeze Tue 2 PM IST`, `task`, `teammate`

**Goal:** Implement cryptographic hash-chained audit logging with nonce deduplication in `agent/audit_log.py`.
**Full Spec:** `docs/TEAM_PROMPTS.md`, Prompt 1

**Checklist:**
- [ ] Branch from `main` after `scaffold/0.5` is merged: `git checkout -b agent/2.4-audit-log`.
- [ ] Read `docs/START_HERE.md` and `docs/DECISIONS.md`.
- [ ] Fill in `agent/audit_log.py` stubs (`append`, `verify_chain`, `seen_nonce`).
- [ ] Remove `@pytest.mark.xfail` from `tests/test_audit.py` and verify all tests pass.
- [ ] Update `PROGRESS.md`, commit with `Assisted-by`, and open PR (freeze Tue 2 PM IST).

---

### Issue 2: `parser/3.1-rule-parser`
**Title:** `feat(parser): deterministic natural language bid parser with prompt-injection defense [3.1-rule-parser]`
**Milestone / Label:** `freeze Tue 2 PM IST`, `task`, `teammate`

**Goal:** Implement deterministic regex/rule parser converting human bids (e.g. "12k" -> integer cents) in `agent/parser.py`.
**Full Spec:** `docs/TEAM_PROMPTS.md`, Prompt 2

**Checklist:**
- [ ] Branch from `main` after `scaffold/0.5` is merged: `git checkout -b parser/3.1-rule-parser`.
- [ ] Read `docs/START_HERE.md` and `docs/DECISIONS.md`.
- [ ] Fill in `agent/parser.py` stubs (`parse_amount_cents`, `parse_request`).
- [ ] Remove `@pytest.mark.xfail` from `tests/test_parser.py` and verify injection tests pass.
- [ ] Update `PROGRESS.md`, commit with `Assisted-by`, and open PR (freeze Tue 2 PM IST).

---

### Issue 3: `agent/2.6-sim-ledger`
**Title:** `feat(ledger): simulated double-entry bookkeeping ledger in integer cents [2.6-sim-ledger]`
**Milestone / Label:** `freeze Tue 2 PM IST`, `task`, `teammate`

**Goal:** Implement zero-sum double-entry ledger in `agent/ledger.py` copying proof amounts verbatim without computing math.
**Full Spec:** `docs/TEAM_PROMPTS.md`, Prompt 5

**Checklist:**
- [ ] Branch from `main` after `scaffold/0.5` is merged: `git checkout -b agent/2.6-sim-ledger`.
- [ ] Read `docs/START_HERE.md` and `docs/DECISIONS.md`.
- [ ] Fill in `agent/ledger.py` stubs (`post`, `balances`, `verify`).
- [ ] Remove `@pytest.mark.xfail` from `tests/test_ledger.py` and verify all 5 tests pass.
- [ ] Update `PROGRESS.md`, commit with `Assisted-by`, and open PR (freeze Tue 2 PM IST).

---

### Issue 4: `agent/2.5-override-wiring`
**Title:** `feat(settle): wire end-to-end settlement pipeline and manager override re-evaluation [2.5-override-wiring]`
**Milestone / Label:** `freeze Tue 2 PM IST`, `task`, `lead`

**Goal:** Orchestrate parse -> validate -> bridge -> proof -> audit log -> ledger pipeline in `agent/settle.py`.
**Full Spec:** `docs/TEAM_PROMPTS.md`, Prompt 6

**Checklist:**
- [ ] Branch from `main` after `scaffold/0.5` is merged: `git checkout -b agent/2.5-override-wiring`.
- [ ] Read `docs/START_HERE.md` and `docs/DECISIONS.md`.
- [ ] Connect `settle()` to `bridge.py`, `audit_log.py`, `ledger.py`, and `override.py`.
- [ ] Add integration test `tests/test_settle.py` verifying full pipeline across SC-01 through SC-09.
- [ ] Update `PROGRESS.md`, commit with `Assisted-by`, and open PR (freeze Tue 2 PM IST).

---

### Issue 5: `ui/6.1-dashboard`
**Title:** `feat(ui): multi-page Streamlit compliance dashboard, proof inspector, and override console [6.1-dashboard]`
**Milestone / Label:** `freeze Tue 2 PM IST`, `task`, `teammate`

**Goal:** Build interactive multi-page Streamlit application in `app/` rendering proofs, audit trail, and manager overrides.
**Full Spec:** `docs/TEAM_PROMPTS.md`, Prompt 3

**Checklist:**
- [ ] Branch from `main` after `scaffold/0.5` is merged: `git checkout -b ui/6.1-dashboard`.
- [ ] Read `docs/START_HERE.md` and `docs/DECISIONS.md`.
- [ ] Build catalog viewer, settlement runner, glass-box "Why?" explainer, and manager override UI.
- [ ] Ensure ZERO money maths in Python UI (copy numbers verbatim from proof atoms).
- [ ] Update `PROGRESS.md`, commit with `Assisted-by`, and open PR (freeze Tue 2 PM IST).

---

### Issue 6: `docs/7.3-readme-disclosure`
**Title:** `docs(submission): finalize README, architecture diagrams, AI disclosure, and video demo [7.3-readme-disclosure]`
**Milestone / Label:** `freeze Tue 2 PM IST`, `task`, `teammate`

**Goal:** Assemble final submission deliverables: `README.md`, proposal notice, `AI_DISCLOSURE.md`, and 3-minute video link.
**Full Spec:** `docs/TEAM_PROMPTS.md`, Prompt 4

**Checklist:**
- [ ] Branch from `main` after `scaffold/0.5` is merged: `git checkout -b docs/7.3-readme-disclosure`.
- [ ] Read `docs/START_HERE.md` and `docs/DECISIONS.md`.
- [ ] Author comprehensive `README.md` and record all AI usage in `AI_DISCLOSURE.md`.
- [ ] Work through `SUBMISSION.md` checklist and link 3-minute demo video.
- [ ] Update `PROGRESS.md`, commit with `Assisted-by`, and open PR (freeze Tue 2 PM IST).
