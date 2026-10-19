# Start Here: Developer Onboarding

## What We Build
An auditable, neuro-symbolic fiduciary compliance and royalty settlement agent for fractional fine art (#BuyBlackArt on BASIX.Market).
It provides deterministic payout proofs, an immutable rule-by-rule justification trail, and non-destructive manager overrides.
Core reasoning is evaluated symbolically via MeTTa on Hyperon; zero floating-point math is allowed anywhere in the system.

## The Settlement Pipeline
```
messy text -> parser -> validation -> bridge -> MeTTa rules -> proof -> audit log -> ledger -> UI
```

## Hard Rules (AGENTS.md)
1. **No money maths outside MeTTa:** MeTTa computes all payouts; Python only validates types and ranges; the UI and ledger only copy proof values.
2. **Integer cents (Zero Floats):** Money is strictly integer minor units (e.g. USD cents: `$10,000` = `1000000`). Percentages are integer basis points (bps).
3. **Fail closed:** Any invariant breach, invalid token, timeout, or ambiguity results in zero disbursed funds and a machine-readable reason code.
4. **Synthetic data only:** Never use real partner or rights-holder records; all catalog entries and wallet addresses are synthetic test fixtures.
5. **No secrets:** Real API keys live strictly in gitignored `.env`; `.env.example` contains placeholders only; never commit keys or print them.
6. **Offline by default:** The core application and test suite run 100% offline with no API key or external network dependencies.

## Clone, Setup & Run

### Windows (PowerShell)
```powershell
git clone https://github.com/kaniska-praba007/fractional-approval-agent.git
cd fractional-approval-agent
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
pytest -v
streamlit run app/streamlit_app.py
```

### Linux / macOS (Bash)
```bash
git clone https://github.com/kaniska-praba007/fractional-approval-agent.git
cd fractional-approval-agent
chmod +x scripts/setup.sh
./scripts/setup.sh
source .venv/bin/activate
pytest -v
streamlit run app/streamlit_app.py
```

## Your Branch, Your File, Your Test

| Branch Name | Stub File | Test File | Done Definition |
| :--- | :--- | :--- | :--- |
| `agent/2.4-audit-log` | `agent/audit_log.py` | `tests/test_audit.py` | Remove `xfail`, all 3 tests pass, SHA-256 chain verified. |
| `parser/3.1-rule-parser` | `agent/parser.py` | `tests/test_parser.py` | Remove `xfail`, all 4 tests pass, injection resistance verified. |
| `agent/2.6-sim-ledger` | `agent/ledger.py` | `tests/test_ledger.py` | Remove `xfail`, all 5 tests pass, zero-sum double-entry verified. |
| `agent/2.5-override-wiring` | `agent/settle.py` | `tests/test_settle.py` | Pipeline end-to-end green, proof matches schema. |
| `ui/6.1-dashboard` | `app/Home.py` | `tests/test_ui.py` | Multi-page UI renders proofs, audit trail, manager overrides. |
| `docs/7.3-readme-disclosure` | `README.md` | Clean clone check | Complete docs, video link, AI disclosure, checklist passed. |

## How to Open a PR
1. Create task branch from latest `main`: `git checkout -b area/task-id-name`
2. Follow isolation invariants: touch ONLY your assigned files.
3. Commit format: `type(scope): summary [task-id]` with `Assisted-by: <tool>` trailer.
4. Verify tests: `pytest -v` must be 100% green.
5. Update `PROGRESS.md` with your sprint summary.
6. Push and open PR against `main`. Do NOT merge yourself.

## Key Timelines & Deadlines
- **Internal Feature Freeze:** Tuesday 20 Oct 2026, ~2:00 PM IST
- **Target Video & Submission Prep:** Tuesday 20 Oct 2026, 7:00 PM IST
- **Final Hackathon Submission Lock:** Tuesday 20 Oct 2026, 8:30 PM IST

## Reference Links
- [docs/FLOWS.md](file:///c:/Users/Der%20Krieger%20Goose/fractional-approval-agent/docs/FLOWS.md): Visual transaction flow diagrams.
- [docs/PROOF_SHAPE.md](file:///c:/Users/Der%20Krieger%20Goose/fractional-approval-agent/docs/PROOF_SHAPE.md): Canonical proof atom JSON contract & reason codes.
- [docs/BRANCHES.md](file:///c:/Users/Der%20Krieger%20Goose/fractional-approval-agent/docs/BRANCHES.md): Branch lifecycle, allowed files, and sequential merge order.
- [docs/TEAM_PROMPTS.md](file:///c:/Users/Der%20Krieger%20Goose/fractional-approval-agent/docs/TEAM_PROMPTS.md): Ready-to-use teammate task prompts.
