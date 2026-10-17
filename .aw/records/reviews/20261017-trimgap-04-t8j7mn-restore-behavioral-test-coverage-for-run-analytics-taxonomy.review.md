# Review findings: plan t8j7mn

- Subject-Id: t8j7mn
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `c2e7cb6f3`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Child plan (Set `trimgap`, Order 4), test-only.

Verified in the lane (scratch test files under `tests/test_zz_scratch_*` and scratch mutations of `agent_workflows/run_analytics_taxonomy.py`, all removed or restored; `git diff agent_workflows/` empty; the stray `.coverage` removed; `git status` clean apart from the plan and this record):
- `19313eed^:tests/test_run_analytics_taxonomy.py`: `51 passed in 0.36s`; coverage `353 stmts, 11 miss, 97%`, which matches F-02 and F-03.
- The 29 `b1mx2w` keys and operators match F-01. Sweep against the restored file alone: 29 of 29 KILLED.
- Every E-02 (a) to (j) value reproduced by direct call. With them added: `52 passed`, `99%`, only line 320 missed (the wrapper-flag skip in `_segment_head`). Deleting that loop is not caught, with or without E-02.
- The plan's named spot-checks are all caught: `classify_command` one-label, `assert_no_command_text` no-op, `unclassified_regressed` returning `(False, "")`, and removal of the duration strip.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing (residual branch unguarded) | `run_analytics_taxonomy._segment_head` loop `while parts and parts[0].startswith("-")`; F-03 vs review coverage | F-03's list of missed lines includes "the wrapper duration-skip", but E-02 never reaches the wrapper-flag skip line. After E-02, coverage is 99 percent, and deleting that loop goes uncaught. Wrapper handling is one of the classifier behaviors the Goal names. | all Low | FIXED | Added E-02 (k): `_segment_head("xargs -0 grep foo") == ("grep", "foo")`. The expected outcome is now 100 percent coverage. V-02 and Required tests now include the loop-deletion mutation. Added F-05. |
| PR-002 | LOW | UNDER-SCOPE | E. Goal verification | Goal "Done means a mutation ... turns a routine test red"; V-items spot-check 4 mutations | No step proves all 29 keys are guarded. The review sweep shows they are today, but nothing requires that to be shown at execution time. | all Low | FIXED | Added E-03 and V-03: a sweep of all 29 keys, each with its `b1mx2w` operator; any mutation no test catches must be fixed. |
| PR-003 | LOW | IN-SCOPE | Execution contract (scope-fence wording) | E-01 "STOP on that test" | E-01 told the executor to STOP over a failing test. The scope-fence rule (2026-09-01 ruling) forbids a STOP directive for this case. | all Low | FIXED | Replaced it with the Set's rule for handling a failing test: decide whether the change is intended or a regression; for a regression, use `xfail(strict=True)` plus a gated bug item, then continue. |
| PR-004 | LOW | IN-SCOPE | Live-artifact bar | E-01 "51 restored tests pass ... `: 51`"; V-01 "the 51 restored tests" | A test count was used as the pass bar. | all Low | FIXED | Changed the bars to "every restored test passes", with N re-derived at execution and the counts kept as context. V-01 now says to report a `CORE TIER BUDGET EXCEEDED` warning instead of un-marking tests (backlog `o58dro`). |
| PR-005 | LOW | IN-SCOPE | Execution contract | gate paragraph | The gate lacked the honesty rule, the staged-file check, the rule for who runs finalize, and the scope-fence wording. It also used the placeholder `aw commit <plan>`. | all Low | FIXED | Rewrote the gate as a full execution contract using `aw commit t8j7mn`, and added a step to clean up the `.coverage` file. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `_segment_head("timeout -k 5 30s pytest")` returns head `30s`. Assert it, or file it? | Neither. Recorded in Deferred with the reason it was declined; E-02 does not assert that input | Pin the current output (would freeze behavior that may be a defect), or file a bug (no measured user-visible impact, so it fails the AGENTS.md perceptible-impact test) | rubric D "Do not freeze accidental behavior"; `AGENTS.md` "INEFFICIENCY A USER CAN NOTICE"; F-05 | yes |
| D-2 | Add a full sweep even though the restored file already kills all 29 keys? | Yes (E-03) | Rely on spot-checks (they cover 5 mutations, not 29 keys) | plan Goal; consistency with sibling reviews `pdemar` / `syzi9i` | yes |
