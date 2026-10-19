# Agent Instructions

> **Read First:** Before starting any work, read [docs/START_HERE.md](docs/START_HERE.md) and [docs/DECISIONS.md](docs/DECISIONS.md).

Read this file first and follow it for the whole session. The architecture, money model, settlement order, state machine and scope are in `docs/CONTEXT.md`. If a task conflicts with it, stop and ask the human lead instead of choosing.

## Start of work
1. Read `BRIEF.md` (check the version and date at the top) and `tracks/track-02-builders.md`. Do not load other tracks.
2. Read `docs/CONTEXT.md`, `GIT_WORKFLOW.md` and `PROGRESS.md`.
3. Confirm with the student the track (Track 02: Builders, Advanced) and challenge (01: Trusted With Money, HFAS brief) and check that `README.md` records them. Never change either without explicit confirmation.
4. Plan within the challenge's scope. If an idea falls outside it, say so before building it.
5. If `BRIEF.md` conflicts with a BASIX.MARKET announcement, flag it and follow the official version.

## Hard rules
1. **No floats.** Money is integer minor units plus a currency code. Percentages are integer basis points. No `float`, decimal literals, `round()` or `/` on money in Python, MeTTa, JSON or the UI.
2. **MeTTa does all money maths.** Python may validate inputs (types, ranges, allow-lists) but must not compute payouts. The UI shows numbers from the proof atom and never computes them. An independent calculation may exist only inside tests.
3. **Test MeTTa rules directly against the pinned `hyperon` runtime** before writing Python around them. Show the real output.
4. **Never edit files in `tests/` or `metta/tests/` to make a test pass.** Never delete, skip or weaken a test. If a test looks wrong, stop and explain. Changes to test assertions need the human lead's approval.
5. **No hardcoded expected outputs.** Tests use seeded random inputs and an independent calculation. Code that special-cases test values is a failure.
6. **No silent failures.** No bare `except:` and no `except Exception: pass`. Every error fails closed with a reason code from `docs/CONTEXT.md` section 7, or is raised.
7. **Fail closed.** Unknown artwork, empty or multiple MeTTa results, invalid data, a failed invariant or any unexpected error means no money moves and a failure is logged.
8. **Read MeTTa results through the Hyperon atom API,** never by splitting strings.
9. **No network in tests.** Mock the LLM. The core demo must run offline with no API key. Omega and Docker are optional extras, never required to run the repo.
10. **Overrides go back through MeTTa.** They may only increase artist or community bps, never below the floor, always with a reason of at least 15 characters. Never overwrite history; append events.
11. **Keep the reasoning visible.** Every decision must be explainable in the output and UI (rule by rule).

## During work
- Keep `AI_DISCLOSURE.md` up to date: every tool used and what each was used for. Never remove or hide AI use.
- Do not use partner or rights-holder data (Incantio, AI for Peace, HFAS archive, Harlem CLxR) unless the student has documented permission. Use placeholders labelled as synthetic.
- Never commit secrets. Keys live in `.env` (git-ignored). `.env.example` holds placeholders only. Never print a key in logs, commands or documents.
- Do not write absolute local paths (such as `C:\Users\...` or `file:///` links) into committed files. Use relative links.
- If a file or video shows identifiable people, remind the student that filming and publishing need consent.
- Do not invent rules, deadlines, prizes or partner commitments. If something is unclear, ask the student to check with the organisers.

## Git
- Work on a branch named for the task (`area/task-id-name`). Never commit to or push `main`. Never force-push.
- Commit format: `type(scope): summary [task-id]`. Add an `Assisted-by: <tool and model>` line to AI-assisted commits.
- Small commits. Do not rewrite files that are not part of the task. Do not create empty placeholder files.
- Add a detailed entry to `PROGRESS.md` when a task is done, and update `PROGRESS.md` after each sprint.

## Before submitting
- Work through `SUBMISSION.md` and report each item as passed, failed or not applicable.
- Do not submit on the student's behalf. The student submits on BASIX.MARKET.

## Never
- Claim a prize, a placement or co-ownership on the team's behalf.
- Change the track or challenge without the student's explicit confirmation.

## Commands (PowerShell)
```
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
streamlit run app/Home.py
```
