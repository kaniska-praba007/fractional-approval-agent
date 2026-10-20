# AI Disclosure Log

In accordance with Hackathon Rule 5 and `AGENTS.md`, this document maintains an explicit, ongoing log of all AI tools, models, and assistants utilized during the design, implementation, testing, and documentation of this project.

## AI Tools & Assistant Usage Log

| Date | Tool / Model | Task / Purpose | Scope of Contribution | Human Review & Verification |
| :--- | :--- | :--- | :--- | :--- |
| 2026-10-18 | Antigravity AI Assistant | Project initialisation, Hyperon bridge scaffolding, test suite setup | Generated initial fail-closed MeTTa Python bridge and unit/integration tests for Hyperon 0.2.10 | All code inspected, executed against local `.venv`, 17/17 tests verified passing |
| 2026-10-19 | Antigravity AI Assistant | SingularityNET Omega investigation and Windows cross-platform test harness fix | Analyzed Omega codebase in isolated scratch environment, patched `select.poll` and `MSG_DONTWAIT` for Windows compatibility in `Autotests/mock/rpc.py`, generated clean patch artifact | Tests executed in Docker container, verified 5/5 mock checks passing |
| 2026-10-19 | Gemini 2.5 Flash (via OpenAI-compatible API) | Live Omega cognitive loop integration spike | Executed live tool calling, parsed `(metta (+ 40 2))` function invocation, synthesized response referencing reduced atom | End-to-end trace logged and validated in `docs/OMEGA_INTEGRATION.md` |
| 2026-10-19 | Antigravity AI Assistant | Task 1: Synthetic Artworks Registry, Test Oracle & Scenario Definitions | Created `data/artworks.json` (4 synthetic artworks in integer cents & bps), `tests/oracle.py` (isolated test reference calculation), SC-01 through SC-09 scenario schemas, and unit/fuzz tests | All 31 tests executed locally and verified passing in 0.58s |
| 2026-10-19 | Antigravity AI Assistant | Task 2: MeTTa Settlement Rules & AtomSpace Bridge | Authored pure-symbolic settlement and rejection rules in `metta/royalties.metta`, created direct `assertEqual` test suite `metta/tests/test_royalties.metta`, and extended `agent/bridge.py` with native Hyperon Atom API traversal | All 42 tests executed locally and verified passing in 7.79s |
| 2026-10-20 | Google Gemini 3.8 Flash (via Antigravity IDE) | Task 3.1: Rule-Based Natural Language Parser (`parser/3.1-rule-parser`) | Implemented deterministic rule-based bid parser `agent/parser.py` converting human amounts into integer cents (`12k` -> `1200000`, `$12,500` -> `1250000`), rejecting ambiguity, stripping adversarial prompt injections; authored 49-case test suite `tests/test_parser.py` | All 49 parser tests and full test suite (100 passed, 8 xfailed) verified locally on Python 3.12 `.venv` |
| 2026-10-20 | Google Gemini 3.8 Flash (via Antigravity IDE) | Task 6.1: Streamlit Dashboard UI/UX Redesign (ui/6.1-dashboard) | Redesigned frontend with glassmorphic FinTech styling, canonical proof inspector, live MeTTa simulator, registry browser, hash-chained audit log explorer, and zero-money-math invariant compliance | Verified all 132 tests pass, zero money math in UI, verified in Brave browser |
| 2026-10-20 | Google Gemini 3.8 Flash (via Antigravity IDE) | Task 7.3: Project Documentation & AI Disclosure (`docs/7.3-readme-disclosure`) | Authored comprehensive `README.md` covering architecture, proposal notice, pipeline diagram, quickstart commands, scenario matrix, and clean clone check; updated `AI_DISCLOSURE.md` and verified `SUBMISSION.md` | Inspected all links, verified clean test runs, ensured no secrets or personal data committed |

## Data & Attribution
- **Synthetic Data Compliance:** All artwork records in `data/artworks.json` are synthetic test fixtures explicitly tagged with `"synthetic": true`.
- **Rights-Holder Notice:** No partner or rights-holder private records (Incantio, AI for Peace, HFAS archive, Harlem CLxR) were used without documented consent.
- **Secrets & Credentials:** Real API keys are stored strictly in gitignored `.env`. `.env.example` contains only harmless placeholders. No secrets are committed anywhere in the repository history.
