# Review findings: plan i18yaz

- Subject-Id: i18yaz
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `8f07d726b`. The plan was committed and byte-identical to the sealed lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean and `aw ipd coverage` reported
ready before revision. After revision `IPD-S408` reported a stale coverage record. Attempt 1 of 2 ran
`aw ipd coverage --no-commit i18yaz`, which re-recorded the coverage, and `review-finalize` was then clean.

Re-measured at review:
- `32jpl1` is in `.aw/records/plans/executed/` (`- Status: executed`, finalize commit `f4de9ea19`). Its V-items record `map_driver_status_to_run_state` and three empty symmetric differences.
- `eow7p4` is `to-review`, carries `Item-Dependencies: executed:32jpl1`, and its E-05/V-05 owns checks (a) to (f).
- Both children declare `agent_workflows/runner_shared.py`.
- `tests/test_runner_refork_guard.py` and `tests/test_runner_shutdown.py` do not exist. Both were deleted by `19313eed7`.
- `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`.
- Backlog `ildjse` is `- Status: open`. Its history line from 2026-10-06 reads "re-run graduation to complete the handoff".
- `grep run_state|verify_roles|run_recovery` over both drivers returns nothing. The translation lives in `runner_shared` (`map_driver_status_to_run_state`), and `_v_session` is still discarded at the verify site.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Orchestrator checklist | plan E-01/E-02 prose; `eow7p4` E-05 "RUN THE SET-LEVEL CHECKS orchestrator `i18yaz` assigns" | E-01 and E-02 still described PERFORMING cross-child checks (Scope-Paths collision, before/after vocabulary comparison, readers passing) that E-05 of `eow7p4` now owns. That leaves two owners, and orchestrator retirement skips this plan's E/V checkpoint. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and E-02 are rewritten as confirm-child-executed items that read `32jpl1`'s record and `eow7p4`'s V-05. V-01 and V-02 now demand the `Status` line, the post-transition lint, and the evidence quoted from V-05. |
| PR-002 | MEDIUM | IN-SCOPE | E. Evidence feasibility | V-02 "`tests/test_runner_shutdown.py`"; Cross-IPD "`tests/test_runner_refork_guard.py`"; both absent (deleted in `19313eed7`) | V-02 demanded passing output from a test file that does not exist, so it could not be satisfied. A cross-IPD check also cited a deleted file as precedent. | all Low | FIXED | V-02 now quotes `eow7p4` V-05. The cross-IPD bullet records that the cited file was deleted. |
| PR-003 | LOW | IN-SCOPE | G. Scope-collision claim | Both children's `- Scope-Paths:` include `agent_workflows/runner_shared.py` | E-01 required that the children's Scope-Paths "do not collide", which is false and also unnecessary because the dependency edge serializes them. | all Low | FIXED | Restated: the shared path is expected and serialized by `executed:32jpl1`. |
| PR-004 | LOW | IN-SCOPE | G. Lifecycle / provenance | `ildjse` `Status: open`, history "re-run graduation to complete the handoff"; plan gate "set to `graduated` by the authoring turn" | The gate claimed the item is graduated, but the demotion of 2026-10-06 reopened it. | all Low | FIXED | The gate now states the current state and that graduation must be re-run (not `done`). |
| PR-005 | LOW | IN-SCOPE | G. Accuracy | Required tests quoted `-m 'not slow'`; `pyproject.toml:205` | The plan misquoted the configured `addopts`. | all Low | FIXED | Corrected to quote `pyproject.toml`. |
| PR-006 | LOW | UNDER-SCOPE | G. Execution contract | Approval gate | The gate lacked the scope-fence declaration wording and did not say who owns finalize when the plan is executed by hand. | all Low | FIXED | Added both. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the orchestrator itself re-run the vocabulary comparison and the readers? | No; it confirms `eow7p4` V-05 | Keep the duplicate checks on the parent | `eow7p4` E-05 text; AGENTS.md says orchestrator retirement skips the E/V checkpoint | yes |
| D-2 | Should this review re-graduate `ildjse`? | No; the gate records that it is owed | Run `aw backlog set graduated ildjse` now | plan-review edits plans only; the graduation is an authoring/runner act | yes |
