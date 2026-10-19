---
name: Task
about: Workstream task issue for teammate implementation
title: 'feat(<scope>): <summary>'
labels: task
assignees: ''
---

### Goal
<!-- 1-2 sentence description of the feature or bug fix -->

### Target Branch
`area/task-id-name` (Branched from latest `main`)

### Files Allowed to Touch
<!-- Explicit list of files owned by this task -->
- `...`

### Files Forbidden to Touch
<!-- Enforce branch isolation (AGENTS.md & docs/BRANCHES.md) -->
- Do NOT touch other workstream files (`agent/*`, `metta/*`, `data/*`, `app/*`).

### Test That Proves Done
<!-- Command to verify implementation -->
```bash
pytest tests/test_<module>.py -v
```

### Checklist
- [ ] Read `docs/START_HERE.md` and `docs/DECISIONS.md`.
- [ ] Remove `xfail` marker from tests and implement stub.
- [ ] Strict integer minor units (cents) — zero floats.
- [ ] No secrets committed.
- [ ] Add entry to `PROGRESS.md`.
- [ ] All tests pass locally and CI passes.
