## Pull Request Description

### Summary
<!-- 2-3 line summary of changes made in this PR -->

Closes #<!-- issue number -->

### Checklist
- [ ] **Tests written first:** Unit/integration tests were added before implementation.
- [ ] **No money maths outside MeTTa:** Python and UI only validate and copy proof values; MeTTa computes all payouts.
- [ ] **Integer cents only (No floats):** All financial values are strictly integer minor units (cents) and basis points (bps).
- [ ] **No secrets:** Real API keys are isolated in local `.env` and nowhere in the committed files.
- [ ] **PROGRESS.md updated:** Added a detailed entry summarizing this sprint's deliverables.
- [ ] **CI green:** All automated checks (`CI / test`) pass cleanly.
- [ ] **Assisted-by line:** Commit message includes `Assisted-by: <tool and model>`.
