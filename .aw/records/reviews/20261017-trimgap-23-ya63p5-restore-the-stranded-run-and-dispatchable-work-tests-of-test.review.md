# Review findings: plan ya63p5

- Subject-Id: ya63p5
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `31623e157`. The plan was already committed and unchanged, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` returned `clean` with 0 findings. This is a test-only child plan (Set `trimgap`, Order 23).

What was checked in the lane, all of which was removed or reverted afterwards (`git diff agent_workflows/` empty; `git status` clean apart from the plan and this record):
- A scratch merged file built per E-01 and E-02: `42 passed` serially, under `-n 4` and at random seeds 1 to 3. `-m core` collects 42.
- Early-return mutations of 11 targets, run against both the current file and the merged one.
- A scratch E-03 test and a coverage JSON.
- The pinned `pre-commit` ruff hooks.

The plan's restore is sound: every F-01 target except one is now guarded where today it is not. The findings below cover the one target that stays unguarded, the lint check, and the validation wording.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Coverage gap left by the restore | plan F-01 lists `runner_shared.emit_shutdown_report`; `agent_workflows/runner_shared.py:47056` `emit_shutdown_report`; `19313eed^:tests/test_run_summary_table.py:320` `test_oc_runipd_main_sigterm_and_sigint_handling` | The restored SIGINT/SIGTERM tests run `emit_shutdown_report` but never assert on what it prints. A `return None` mutation passes the merged file (`42 passed`). The tests that do catch it (`tests/test_runner_backlog_close_behavior.py` `TestUnclosedReport`, 9 failed) are not core-marked (`no tests collected (51 deselected)`). So the routine gate still would not notice the shutdown report vanishing. | all Low | FIXED | Added E-03 and V-03: one core test that asserts the `aw runs` pointer is printed exactly once to stdout across two calls, with the globals restored afterwards. In scratch it fails under the `return None` mutation and under removal of the idempotence guard, and it does not depend on test order. Added F-05. |
| PR-002 | MEDIUM | IN-SCOPE | Executability (lint check) | plan E-01 and V-01 "`ruff check` ... is clean"; `.pre-commit-config.yaml` `ruff-pre-commit` `rev: v0.4.4` | `ruff` on PATH is 0.16.3. It already reports 2 errors on the CURRENT file at HEAD (`I001`, `RUF059`) and 5 on the merged file, so the stated bar cannot be met without editing kept test bodies. The pinned hooks the repository actually enforces pass. The plan also did not warn that `ruff-format` rewrites the file (it removed 39 blank lines). | all Low | FIXED | E-01, V-01 and Required tests now use `pre-commit run ruff` and `pre-commit run ruff-format` on the file, explain the version mismatch, and say to commit the rewritten file. |
| PR-003 | LOW | IN-SCOPE | Validation (the command cannot produce the evidence) | plan Required tests `--cov-report=term-missing` "showing ... executing" | `term-missing` does not attribute executed lines to individual functions. | all Low | FIXED | Replaced with a per-function check that uses a JSON coverage report. |
| PR-004 | LOW | IN-SCOPE | Pass bar uses a live count | plan E-01, E-02, V-02, Required tests "42" | Collected test counts were used as the pass bar. | all Low | FIXED | The bar is now "every test passes, zero failed, none deselected", with the counts kept as context. The bar still lists the 33 appended names, because those come from the backlog. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | plan Approval gate; E-01 "STOP on it" | The gate lacked the honesty rule, the staged-set check, the rule for who runs finalize, and the scope-fence-as-declaration wording. The rule for a failing test told the executor to STOP and gave no xfail disposition. This did not match the sibling plans. | all Low | FIXED | Rewrote the gate as a full execution contract and used the Set's disposition rule. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings. The orchestrator `kn7xtw` cites `ya63p5 V-02` for the bare-suite line, and V-02 still demands it.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Cover `emit_shutdown_report` by core-marking `tests/test_runner_backlog_close_behavior.py`'s `TestUnclosedReport` instead of adding a test here? | Add one test here (E-03) | Mark the other file. Rejected: that file is outside this plan's Scope-Paths and no `trimgap` child owns it. | plan Scope-Paths; F-05 | yes |
| D-2 | Keep `test_the_committed_fixture_is_tracked_and_not_gitignored` (it runs `git check-ignore`)? | Keep it | Drop it. Rejected: it asserts on the outcome of running a command on a test fixture and reads no production source, which `AGENTS.md` rule (4) allows. | plan Conventions; `AGENTS.md` | yes |
