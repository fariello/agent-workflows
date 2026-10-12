# Review findings: plan z2ugxc

- Subject-Id: z2ugxc
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`d93f29677`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean (one advisory `IPD-Z602` density note on E-10) before semantic review, and `--phase review-finalize` was clean after revisions (the same advisory remains, see D-3).

Re-verified:
- `git show 19313eed7^:tests/test_runner_backlog_close.py` recovers the file: 58 `def test_`, 12 `^class ` (F-01). Recovered to `/tmp/opencode/yf1p8y-deleted.py` for reading only.
- F-03 greps re-run at review HEAD: `backlog_item_paths_for_commit` names no file under `tests/`; `backlog_item_paths_for_id`, `backlog-items-left-open`, `backlog-close-integrity-violation`, `_SIGNAL_REPORT_DONE` name only `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`; `emit_shutdown_report`, `register_signal_report`, `signal_report_callback`, `render_unclosed_report`, `render_runs_pointer`, `record_unclosed_backlog_items` name only that fixture and `tests/test_runner_delegation_and_host_independence.py` (F-03, F-04 confirmed).
- F-05: `runner_shared.py` banner "runnerlayer Order 02 (`1f7xno`) ... THE RE-HOMED HOST-NEUTRAL NAMES" carries "which is what `tests/test_runner_layering.py` now freezes" and "`tests/test_runner_shared.py::ReHomedHostNeutralNameTests` proves it"; `oc_runipd.py` twin "proven by AST fingerprint in `tests/test_runner_shared.py::ReHomedHostNeutralNameTests`". Neither test exists. Commits `13760db4a` and `edcbbe275` exist (batch 1/6 and 6/6).
- `tests/test_runner_delegation_and_host_independence.py` docstring line "(which is tracked under backlog item yf1p8y)" exists.
- Symbols named by E-03..E-08 exist in `runner_shared`: `emit_shutdown_report`, `register_signal_report`, `signal_report_callback`, `render_unclosed_report`, `render_runs_pointer`, `record_unclosed_backlog_items`, `_SIGNAL_REPORT_STATE`, `_SIGNAL_REPORT_DONE`, `backlog_item_paths_for_id`, `backlog_item_paths_for_commit`, `evaluate_backlog_close`, `process_backlog_close`, rules `attention.committed-duplicate` / `attention.committed-absent`. Both drivers define `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS`; `agy_runipd.main` returns `143 if is_sigterm else 130`.
- Helpers `_make_scratch_repo`, `_write_backlog_item`, `_write_plan`, `_write_spec` exist in `tests/test_backlog_handoff_close.py`.
- `.github/workflows/tests.yml`: matrix includes `windows-latest`; the `-m slow` step is `continue-on-error: true` (ADVISORY).
- `pytest-randomly` is installed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Coverage | recovered file: `ReadsTheFromBacklogLink.test_the_link_is_frozen_into_run_state_by_a_REAL_run`, `test_absent_and_placeholder_values_mean_no_linked_item`; `SharedNotCopied.test_both_drivers_call_the_close_from_their_finalize_success_branch`; `ShutdownReportOnInterrupt.test_the_sigterm_funnel_is_wired_in_both_drivers_main` | E-04's description covered only verdicts, setter, and fail-closed cases. It did not describe the From-Backlog link read/freeze rows or the finalize-success-branch call row, and E-07 did not describe the SIGTERM-wiring row. All four are behavioral (real `initialize_run`, real `execute_item` turn, real signal disposition), and an E-03 UNGUARDED verdict on any of them had no restore item to land in. E-07's "run-path rows of `SharedNotCopied`" did not say which rows. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now owns the link rows and the finalize-call row, E-07 owns the SIGTERM-wiring row, and E-07 names exactly which `SharedNotCopied` rows it owns. |
| PR-002 | MEDIUM | IN-SCOPE | E. Mutation soundness | plan E-03 "`python3 -m pytest -o addopts="" -q -n auto tests/`" | `-o addopts=""` drops the marker filter, so the selection silently includes `livecorpus` tests, whose red or green depends on the corpus rather than the mutation. It also had no unmutated baseline, so a pre-existing failure would read as "COVERED". The plan also never required proof that a mutation did not leak into a commit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now runs `-m "not livecorpus"` (keeping `slow`, where guards may live), takes one unmutated baseline and counts only new failures, allows `rg -l` screening while still requiring a full run for a GREEN verdict, and requires `git diff --quiet -- agent_workflows/` after each restore. The gate forbids committing while a mutation is applied. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence / E. CI | `.github/workflows/tests.yml` slow step `continue-on-error: true` | E-10 said "CI runs `-m slow` as its own gating step". That is false: the step is advisory, so slow-marking a restored guard would remove it from gating CI. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The claim is corrected, and E-10 now prefers keeping the tests fast so they stay in the gating selection. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Portability | `.github/workflows/tests.yml` matrix `windows-latest`; E-07 real `SIGINT`/`SIGTERM` subprocess tests | Real-signal subprocess tests do not behave the same on Windows: `send_signal(SIGINT)` is not a console Ctrl-C, and SIGTERM runs no Python handler. The tests would fail on a gating CI leg, and a test could hang with no timeout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now adds a named `skipif(win32)` on the real-signal tests, relies on the `main` funnel test to cover Windows, and requires `communicate(timeout=30)` plus a kill on timeout. |
| PR-005 | LOW | IN-SCOPE | G. Right-sizing | `IPD-Z602` on E-10 | E-10 bundled the comment-only AST proof, which validates E-09's production edit, with suite timing and runs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The AST proof is now a separate E-11/V-11 that also checks `git diff --name-only` covers only the two production files. Every reference was swept (Proposed changes, Scope check, Required tests, Step 0, gate). |
| PR-006 | LOW | IN-SCOPE | E. Executability | E-10 "`-p randomly` seeds varying (the default)" | Default seeds are not recorded as distinct, so "three randomized runs" could repeat one seed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-10 now uses three explicit, different `--randomly-seed=<n>` values. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status line, the scope fence, the MUST-paste honesty rule, conditional runner/executor ownership of begin/finalize, and the no-`git mv` rule. The OQ owners were also recorded as `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All of those were added, and the owners were set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | One new module or fold into existing files (OQ-01)? | Keep one new module | Fold rows into `tests/test_outer_close_spec_carrier.py` etc. (scatters the triage) | executed `1o7i7g` precedent; live "deleted in `19313eed`" comments in `oc_runipd.py`/`agy_runipd.py` | yes |
| D-2 | Include `slow` tests in the E-03 mutation selection? | Yes; exclude only `livecorpus` | Fast suite only (misses guards in slow modules such as `tests/test_runner_stop_triggers_e2e.py`) | `pyproject.toml` markers; plan F-03 cites that slow-adjacent module | yes |
| D-3 | Split E-10 further to silence the remaining `IPD-Z602` advisory? | No; timing, randomized runs and the bare suite are one verification pass over one module | Three E-items for three runs of the same artifact (no independent deliverable) | `ipd_lint.check_density` is advisory and "Does NOT affect the conformance disposition" | yes |
