# Review findings: plan oi9kr8

- Subject-Id: oi9kr8
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`5d68bcc27`), so no snapshot was needed. `aw ipd lint --phase author` was conforming. `--phase pre-transition` reported only the expected not-yet-executed `IPD-S404` items: the Deferred rows already carry `Carrier`/`Carrier-Evidence`/`Carrier-Declined`.

Claims verified on the current tree:
- `git ls-files --error-unmatch tests/test_ipdrunner_runagy_shim.py` exits 0, and `git ls-files tools/ipdrunner/test_runagy.py` prints nothing.
- `git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests tools` exits 1.
- `tests.test_uncollected_test_modules.EXEMPT` holds exactly the three keys F-04 names.
- Running the shim module and the guard together gives `27 passed`, and `--collect-only` counts 25 shim tests.
- `git show --stat b417e9c2d` shows the move, plus comment-only edits to `agy_runipd.py` and `oc_runipd.py`. Those are comments, not runner behavior, so Deferred row 3 holds.
- `runner_shared._VERDICT_TABLE` has `VERDICT_BLOCKED: VerdictMapping(VERIFY_DISP_BLOCKED, True, "fail-verify", True)`.
- `runner_shared.attempt_log_path`, `runner_shared.edge_satisfied` and `runner_shared.process_backlog_close` all exist.
- Plans `g0u7f9`, `vzk1iw` and `3or4ce` are in `executed/`, and `g0u7f9` F-3..F-9 and F-12 read as cited.
- Backlog `byz9pj` and `3rj8wr` are `graduated`, and `gte0pd` is `done`.
- `git grep` over `.aw/records/specs` and `docs` returns nothing (exit 1).

I replayed the pre-move module (`git show b417e9c2d^:tools/ipdrunner/test_runagy.py`) from a temporary copy and then removed it. The result was `10 failed, 15 passed`, with exactly the three shapes the plan lists. One historical name differs: `test_verification_blocked_sets_disposition_partial` before the move is `test_verification_blocked_sets_status_fail_verify` after it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D. Anti-regression | E-03 said "If ... `E-02` reported any failure ..., apply the minimal repair to the offending file in `Scope-Paths`". Scope-Paths lists the two test files only. | The conditional repair path let an executor make a red test green by editing the test, even when the cause was a new runner regression. That hides a live bug. The backlog item itself says to "triage each" as stale test versus product regression, and AGENTS.md says every live bug gates the next release. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires a per-failure drift-vs-regression triage first. Only test drift may be repaired. A regression is filed as `bug` with `Blocks-Release: next`, and the item is marked `blocked` instead of finalized. The Scope and Expected outcome text was updated to match. |
| PR-002 | LOW | IN-SCOPE | G. Live-artifact convention | E-02 Expected outcome lists 10 test function names as the shapes "including all three failure shapes" | Test function names are artifacts of test organization and must not serve as the bar. The list also did not record that one historical name was renamed, so an executor comparing it to the backlog's "10 failing tests" could wrongly conclude a test was lost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The names are now marked as non-binding pointers to the three behaviors. The bar stays "every collected test passes, re-derived at execution", and the rename is recorded. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract / evidence | `- Scope-Paths:` omitted the plan file; the 10-failure triage rested on `g0u7f9` alone | The plan file was not declared in Scope-Paths, although the plan edits its own checklist. The historical triage had no independent reproduction recorded in this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the plan path to Scope-Paths. Added F-06 recording the review replay (`10 failed, 15 passed` before the move; `27 passed` and 25 collected now). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should E-03 handle a failure caused by a runner regression? | File a `bug` backlog item with `Blocks-Release: next`, mark the item `blocked`, and leave the test red | Widen Scope-Paths to the runner and fix it in this plan, which is over-scope for a verify-and-close plan | Backlog `3rj8wr` body ("Not yet known which failures are stale tests and which are product regressions; triage each"); AGENTS.md "Every live bug gates the next release" | yes |
| D-2 | Accept OQ-01 (no code change expected)? | Yes, as authored | Reopen | Tree verification above; precedent plan `3or4ce` in `executed/` | yes |
