# Review findings: plan 8bhcd3

- Subject-Id: 8bhcd3
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `be0827929`. The plan was byte-identical to the lane input and already committed (`4119fb0d6`), so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean` with one `info` advisory, `IPD-Z602` (density on E-02, see D-3). Child plan (Set `trimgap`, Order 15), test-only, one declared path.

Verified in the lane (scratch test file, scratch coverage data and production mutations all removed or reverted afterwards; `git status` clean, `git diff agent_workflows/` empty):
- `19313eed^:tests/test_run_analytics_telemetry.py` (1331 lines) has every construct E-01 names: `import ast`, `_FORBIDDEN_CODE_IDENTIFIERS`, `_code_identifiers`, `_imported_modules`, the three text-asserting tests, the fragment-assembled `_HANDLE`, and the `"control: a handle IS a fail-severity finding"` assertion.
- With the E-01 edits applied under `tests/`: `59 passed` serially, under `-n 4`, and under random order; the `rg` forbidden-pattern check returns nothing; `--cov` gives `647 stmts, 84 miss, 87%`, matching F-02.
- With the E-01 edits, `import re` is left unused (its only user was the deleted canary-literal test). `ruff check` reports `F401` on it, which the original file did not have (the original's other 17 ruff findings are pre-existing and unrelated).
- Every E-02 value from (a) to (g) was re-measured by direct call and matched. `ResourceSampler._run` catches a `tick` exception and returns, so (g) raises no pytest thread-exception warning.
- A draft of E-02 (a) to (g) left `ResourceSampler._run`'s `continue` line missed in 5 of 5 runs. The constructor clamps `check_interval = min(interval, max(0.05, interval/4))`, which equals `interval` at 0.01, so the skip branch is unreachable with that setup. A deterministic (h) using an injected `monotonic` covered it in 3 of 3 runs, and the coverage JSON then showed empty `missing_lines` for all 24 keys (67 passed).
- Every listed mutation was killed by the draft: `_parse_accelerator_csv` return None (2 failed), `build_event` return None (2), `FakeResourceProbeAdapter._count` raise (3), `TelemetryCollector.sample` return None (5), `tick` taken-path True->False (2), `tick` skip-path False->True (2), `_as_int` return 0 (1).
- Bare `python3 -m pytest` with the draft file present: `820 passed in 27.12s`, within the 30s core budget.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Coverage (goal unreachable as written) | `run_analytics_telemetry.ResourceSampler._run` `if now - last < self.interval: continue` (line 1502); `ResourceSampler.__init__` `self.check_interval = min(self.interval, max(0.05, self.interval / 4.0))` | E-02's Expected outcome requires no missed line inside any key, but (f) with `interval_seconds=0.01` can never execute the `continue` skip branch, because `check_interval` clamps to the interval. Measured as missed in 5 of 5 runs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-02 (h): an injected `monotonic` plus a short `check_interval` drives the skip branch deterministically. Demonstrated at review in 3 of 3 runs; F-05 updated. |
| PR-002 | MEDIUM | IN-SCOPE | Executability (stop directive) | E-01 "STOP on that test"; E-02 "apply the same STOP rule"; `plan-review.md` scope-fence ruling 2026-09-01 | Same defect as sibling `438gkf` PR-001: a STOP plus an out-of-scope `bug` filing, with no justification route and no handling for the failing test. | all Low | FIXED | Replaced with the disposition rule (cite and adjust, or file a gated `bug`, justify with `--scope-reason`, mark `xfail(strict=True)`, continue). |
| PR-003 | MEDIUM | IN-SCOPE | Validation (evidence the command cannot produce) | Required tests Reach `--cov-report=term-missing` "shows every one of the 24 keys' bodies executed"; E-02 Expected outcome | `term-missing` reports module lines, not functions, so per-key reach had to be hand-mapped. Coverage also wrote an untracked `.coverage` into the worktree root (observed at review). | all Low | FIXED | Reach now reads the coverage JSON per-function `executed_lines`/`missing_lines` for each key, with `COVERAGE_FILE` under the gitignored `.aw/state/`; V-02 demands a clean `git status`. |
| PR-004 | LOW | IN-SCOPE | Correctness (lint hook) | `19313eed^` file `import re` used only in `test_no_literal_canary_is_committed_in_this_file`; `.pre-commit-config.yaml` `ruff --fix` | The E-01 edits leave `import re` unused (`F401`). The repository's ruff hook would rewrite and reject the commit, or an executor might leave a dead import. | all Low | FIXED | E-01 now also deletes `import re`, and its Expected outcome and V-01 demand `ruff check --select F401` clean. |
| PR-005 | LOW | IN-SCOPE | Validation (count as bar; ambiguous mutation) | E-01 "its 59 restored tests pass"; V-01 "the 59 restored tests"; Required tests "`tick` return `not` its result" | A collected test count was the bar. "Negate return" on `tick` (which has two return paths) was ambiguous. | all Low | FIXED | The bar is now behavior, with 59 kept as context. The `tick` mutation is spelled out as both paths flipped one at a time, and the review kill counts are recorded. |
| PR-006 | LOW | IN-SCOPE | Execution contract | old gate paragraph | The gate lacked the honesty rule, the staged-set check, the scope-fence wording, and conditional finalize ownership; it also used an `<plan>` placeholder. | all Low | FIXED | Gate rewritten as an execution contract naming `aw commit 8bhcd3`. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 errors, 0 warnings, 1 info (`IPD-Z602`, accepted per D-3).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What happens to a restored test that fails because of a regression? | File a gated `bug` item, mark the test `xfail(strict=True)`, continue | STOP; delete the test; leave it failing | AGENTS.md "Every live bug gates the next release"; plan-review scope-fence ruling; sibling `438gkf` D-1 | yes |
| D-2 | How should the unreachable `_run` skip branch be covered? | Add (h) with an injected `monotonic` and a short `check_interval` | Drop the "no key-body miss" bar; use a longer real-time interval (slow, flaky) | `ResourceSampler.__init__` clamp; measured 5/5 missed without and 3/3 covered with (h) | yes |
| D-3 | Split E-02 (now eight sub-cases) per the `IPD-Z602` advisory? | Keep it as one item | One E-item per sub-case or two (pure functions vs thread lifecycle) | All sub-cases target one module, one appended class and one V-item, and run in about 1s; sibling `438gkf` D-3 | yes |
| D-4 | Keep `test_run_analytics_packaging.py` out of this plan? | Keep it out (plan OQ-02) | Restore it here | F-06: its telemetry reach is a subset of the restored file's, and one of its tests imports a name that no longer exists | yes |
