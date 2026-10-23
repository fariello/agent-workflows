# IPD: Verify and record the core-tier guard for the 24 residual keys already killed

- Date: 2026-10-23
- Kind: child
- Concern: Residual backlog item `nzc6dm` (Set `trimgap`, groups 16 to 52 of the `wo21z5` `## Filing plan`) rolls up 43 keys. Probed at authoring HEAD `6c0a6b72a` (F-01, F-02), 24 of them are ALREADY killed by the routine core tier: a mutant of each fails at least one core-marked test that reaches it. Most were `budget-exhausted` in `wo21z5` (never probed), and four (`comms.validate_envelope_header`, `cli._dispatch`, `engine.resolve_source_root`, `engine.migrate_local_lanes_to_untracked`) were since restored into core by executed sibling plans `y4bt1c` and `33f8tn`. The other 19 keys are covered by sibling plans `1z19cn`, `qx3ppg`, `j77z5h`, `sbcmke` and `v44udc` (F-03). What is owed for these 24 is the recorded, re-checked proof that the routine gate guards them, plus a restore for any key whose guard has regressed by execution time.
- Scope: Re-probe the 24 keys at execution HEAD under a `-m core` selection and record every verdict; for any key that no longer reports `killed`, add a behavioral test to one new core-marked module `tests/test_residual_guard_fallback.py`, and only then. EXCLUDES any production-code change; EXCLUDES the 19 keys owned by the five sibling plans; EXCLUDES changes to existing test files.
- Scope-Paths: tests/test_residual_guard_fallback.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: nzc6dm
- Set: trimgap
- Order: 34
- Highest E allocated: 06
- Author: opencode
- Id: e6lq6y

## Workflow history

- 2026-10-23 to-review (opencode): authored from backlog `nzc6dm`. Measured core reach of all 43 keys at HEAD `6c0a6b72a` and probed the 32 core-reached keys against their core-reaching files (24 `killed`, 8 `survived`); the 8 survivors and the 11 unreached keys are assigned to five sibling plans.
- 2026-10-23 draft (opencode): created.

## Goal

Close the 24 already-guarded keys of `nzc6dm` with pasted mutation-probe evidence at execution HEAD that the routine core tier kills each one, and restore coverage only for any key where that is no longer true. Done means 24 recorded `verdict: killed` lines under `-m core`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-derive the core selection

- [ ] E-01 Record the core-tier reach at execution HEAD: `python3 tools/replay_coverage_diff.py baseline --out .aw/state/e6lq6y/core -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` (gitignored scratch). For each of the 24 keys in the F-02 table, map its `contexts` in `baseline.json` to test FILES with the longest-existing-file-prefix rule (`tests.test_x.Class.test` -> `tests/test_x.py`, the rule `wo21z5` `## Method` step 5 uses) and write `<key>\t<op>\t<files>` to `.aw/state/e6lq6y/sel.tsv`. A key absent from the baseline gets the selection `tests/` (the full core tier).
  - Depends on: none
  - Expected outcome: the baseline prints its `head` (equal to execution HEAD) and `functions` count; `sel.tsv` has 24 rows, and at authoring all 24 keys were present in the core baseline (F-01).
  - Execution state: pending

### Task group 2: probe the 24 keys

- [ ] E-02 Probe the parsing, output and config keys (the first eight rows of F-02: `ipd_schema._parse_item_dependency_edge`, `ipd_schema.parse_item_dependencies`, `result_types.CommandResult.to_agent_record`, `result_types.select_output`, `run_analytics_config._coerce_bool`, `run_analytics_config.parse_telemetry_settings`, `term.stdin_is_interactive`, `term.is_interactive`): for each row run `python3 tools/mutation_probe.py --op <op> --format json <key> -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" <files>` with `<op>` and `<files>` from `sel.tsv`. `tools/mutation_probe.py` mutates in its own disposable worktree, so the checkout is never modified. Record `verdict`, `baseline_failing`, `mutant_failing` and `wall_s` per key.
  - Depends on: E-01
  - Expected outcome: eight `verdict: killed` (F-02 authoring values: 14, 25, 21, 218, 8, 13, 9, 4 newly failing).
  - Execution state: pending

- [ ] E-03 Probe the record, CLI and engine keys (F-02 rows 9 to 16: `backlog.run_new`, `benchmark_manifest.BenchmarkManifest.to_dict`, `check_engine._review_index`, `cli._dispatch`, `comms.validate_envelope_header`, `engine.resolve_source_root`, `engine.migrate_local_lanes_to_untracked`, `leak_sanitizer.scan_text`) the same way and record the same fields.
  - Depends on: E-01
  - Expected outcome: eight `verdict: killed` (authoring: 18, 5, 6, 156, 4, 38, 2, 39).
  - Execution state: pending

- [ ] E-04 Probe the remaining keys (F-02 rows 17 to 24: `project_context._resolve_effective_aw_home`, `renderers.BaseRenderer.emit`, `research_cmd.build_frontmatter`, `research_contract.validate_frontmatter`, `run_analytics_privacy._project_number_map`, `run_ledger_schema.validate_record`, `selectors.resolve_for_mutation`, `verify_roles.check_role_action`) the same way and record the same fields.
  - Depends on: E-01
  - Expected outcome: eight `verdict: killed` (authoring: 440, 40, 53, 4, 3, 17, 7, 6).
  - Execution state: pending

### Task group 3: conditional restore

- [ ] E-05 For every key E-02 to E-04 report as anything other than `killed` (a `survived`, or a `baseline_failing` above 0 that makes the verdict unreliable): create `tests/test_residual_guard_fallback.py` (provenance docstring naming `nzc6dm`, `e6lq6y`, `wo21z5`; `import pytest`; `pytestmark = pytest.mark.core`) if it does not exist, and add one test per such key that calls the key through its nearest public caller and asserts on its returned value, mining the body from the key's `wo21z5` control file at `19313eed^` where an equivalent test exists. Commit with `aw commit e6lq6y -- tests/test_residual_guard_fallback.py`, then re-probe that key with `-m core tests/test_residual_guard_fallback.py` as the selection. If every key reported `killed`, make NO file change and record "no restore needed" in Findings.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: either no new file, or a file adding only tests, after which every previously non-killed key re-probes `verdict: killed`.
  - Execution state: pending

- [ ] E-06 Only if E-05 created the fallback module: run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim. If E-05 made no change, record "not applicable: no file changed" with the E-05 evidence.
  - Depends on: E-05
  - Expected outcome: either a bare run with no failures including the fallback tests, or the recorded not-applicable line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`). A probe whose selection is `-m "core and not slow and not livecorpus"` over files that reach the key measures exactly whether the merge gate kills it, because the full core tier is a superset of that selection.
- Verify-first precedent in this Set: pending siblings `92tzo6` and `qpmq2o` probe at execution HEAD and add tests only for keys that survive; this plan applies the same shape.
- Probe tools: `tools/replay_coverage_diff.py baseline` (records per-function test contexts) and `tools/mutation_probe.py` (`--op`, `--format json`, selection after `--`), the tools `wo21z5` used.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16) for any fallback test E-05 adds.
- Commit only through `aw commit e6lq6y -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/replay_coverage_diff.py baseline --out .aw/state/nzc6dm-auth/core -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `6c0a6b72a` | `head: 6c0a6b72a15c8eb6047168d7d66fac73630a1f29`, `functions: 2892`, `wall_s: 125.48`. 32 of the 43 `nzc6dm` keys are reached by core; 11 are not. All 43 keys still exist at HEAD and their operators apply (`tools.mutation_probe.apply_operator`). |
| F-02 | `tools/mutation_probe.py --op <op> --format json <key> -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" <core-reaching files>` at `6c0a6b72a`; columns: key, op, reaching files, mutant_failing, wall_s; every row `verdict: killed`, `baseline_failing: 0` | see the table below (24 rows, 2203.4s total) |
| F-03 | the remaining 19 keys | 8 core-reached keys survived (`validate_agent_record`, `_existing_type_id6s`, `_infer_artifact_type` -> `v44udc`; `check_push_authorization`, `get_git_common_dir`, `_observe_tool_versions`, `lane_id_from_branch` -> `sbcmke`; `format_spec_impact_announcement` -> `j77z5h`). 11 are unreached by core: `apply_renames`, `_dirs`, `classify_commit_refusal` -> `qx3ppg`; `Palette.status`, `_status_glyph_char`, `_gate_ref_display`, `cite_review_entry` -> `j77z5h`; `attributed_away_failure_ids` -> `sbcmke`; `AblationTrialSpec.cell_key`, `MetricSummary.to_dict`, `GateEvaluationResult.to_dict` -> `1z19cn`. 24 + 8 + 11 = 43. |

F-02 table:

| Key | Op | Reaching core files | mutant_failing | wall_s |
|---|---|---:|---:|---:|
| `agent_workflows/ipd_schema.py::_parse_item_dependency_edge` | `return-none` | 5 | 14 | 44.84 |
| `agent_workflows/ipd_schema.py::parse_item_dependencies` | `return-none` | 9 | 25 | 123.03 |
| `agent_workflows/result_types.py::CommandResult.to_agent_record` | `return-none` | 7 | 21 | 84.12 |
| `agent_workflows/result_types.py::select_output` | `return-none` | 15 | 218 | 205.70 |
| `agent_workflows/run_analytics_config.py::_coerce_bool` | `return-none` | 4 | 8 | 65.73 |
| `agent_workflows/run_analytics_config.py::parse_telemetry_settings` | `return-none` | 4 | 13 | 43.95 |
| `agent_workflows/term.py::stdin_is_interactive` | `negate-return` | 13 | 9 | 145.13 |
| `agent_workflows/term.py::is_interactive` | `return-false` | 13 | 4 | 78.39 |
| `agent_workflows/backlog.py::run_new` | `return-none` | 1 | 18 | 20.71 |
| `agent_workflows/benchmark_manifest.py::BenchmarkManifest.to_dict` | `return-none` | 1 | 5 | 7.86 |
| `agent_workflows/check_engine.py::_review_index` | `return-none` | 5 | 6 | 49.22 |
| `agent_workflows/cli.py::_dispatch` | `return-none` | 11 | 156 | 225.52 |
| `agent_workflows/comms.py::validate_envelope_header` | `return-none` | 1 | 4 | 11.02 |
| `agent_workflows/engine.py::resolve_source_root` | `return-none` | 10 | 38 | 209.61 |
| `agent_workflows/engine.py::migrate_local_lanes_to_untracked` | `return-none` | 1 | 2 | 13.99 |
| `agent_workflows/leak_sanitizer.py::scan_text` | `return-none` | 10 | 39 | 56.17 |
| `agent_workflows/project_context.py::_resolve_effective_aw_home` | `return-none` | 44 | 440 | 445.23 |
| `agent_workflows/renderers.py::BaseRenderer.emit` | `return-none` | 9 | 40 | 151.53 |
| `agent_workflows/research_cmd.py::build_frontmatter` | `return-none` | 2 | 53 | 18.28 |
| `agent_workflows/research_contract.py::validate_frontmatter` | `return-none` | 4 | 4 | 103.72 |
| `agent_workflows/run_analytics_privacy.py::_project_number_map` | `return-none` | 1 | 3 | 12.02 |
| `agent_workflows/run_ledger_schema.py::validate_record` | `return-none` | 4 | 17 | 15.35 |
| `agent_workflows/selectors.py::resolve_for_mutation` | `return-none` | 2 | 7 | 21.19 |
| `agent_workflows/verify_roles.py::check_role_action` | `return-none` | 5 | 6 | 51.05 |

## Proposed changes (ordered, validatable)

1. E-01 re-derives the core selection for the 24 keys at execution HEAD.
2. E-02 to E-04 probe the 24 keys in three groups of eight and record each verdict.
3. E-05 restores coverage only for any key that no longer reports `killed`.
4. E-06 runs the bare gate only if E-05 changed a file.

## Deferred / out of scope (with reason)

- The 19 non-guarded keys of `nzc6dm`.
  - Carrier: 1z19cn
  - Carrier: qx3ppg
  - Carrier: j77z5h
  - Carrier: sbcmke
  - Carrier: v44udc
- Writing new tests for keys that already probe `killed`.
  - Carrier-Declined: no work is owed; a guarded key has no gap, and redundant tests only add core-tier time (the reasoning siblings `92tzo6` and `qpmq2o` apply).

## Scope check

- Over-scope: none. The only declared path is the conditional fallback module; no production file or existing test changes.
- Under-scope: none. All 24 guarded keys are re-probed (E-02 to E-04) with a conditional restore (E-05); the other 19 keys are carried by named sibling plans (F-03).

## Required tests / validation

- E-01 baseline summary and the 24-row `sel.tsv` pasted.
- 24 `tools/mutation_probe.py` JSON verdicts pasted, each `killed` with `baseline_failing: 0` (E-02 to E-04), or, for any that is not, the E-05 fallback test, its passing run and its `killed` re-probe.
- `git diff --stat <execution base>..HEAD -- agent_workflows/` empty (no production change).

## Spec / documentation sync

N/A: verification and, at most, tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Probe each key over its core-reaching files or over the full core tier?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Over its core-reaching files under `-m core`. A test that does not execute a function cannot fail because of that function's mutation, so the reaching files are the only core tests that can kill it, and a `killed` verdict there implies `killed` under the full core tier. It cost 2203s for the 24 keys at authoring (F-02), against roughly 125s per key for the full tier (F-01 baseline wall time), so it keeps the verification affordable. E-01 assigns `tests/` (the full tier) to any key the baseline no longer shows as reached, so nothing is silently skipped.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `head:` and `functions:` lines printed by `tools/replay_coverage_diff.py baseline` (E-01), with `head` equal to execution HEAD, and the full 24-row `.aw/state/e6lq6y/sel.tsv`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the eight JSON outputs produced by `tools/mutation_probe.py` for the E-02 keys, each showing `head`, `operator`, the `-m core and not slow and not livecorpus` selection, `verdict`, `baseline_failing` and `mutant_failing`; every row `killed` with `baseline_failing: 0`, or the row handed to E-05.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the eight JSON outputs for the E-03 keys with the same fields and the same pass condition.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the eight JSON outputs for the E-04 keys with the same fields and the same pass condition.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste either `git status --short tests/` showing no new file plus the recorded "no restore needed" line, or the `aw commit` output naming only `tests/test_residual_guard_fallback.py`, its `-o addopts="" -v` run with every test PASSED, `grep -nE "inspect|getsource|ast\."` over it returning nothing, and a `killed` re-probe JSON for each restored key.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste either the bare `python3 -m pytest` summary line with no `failed` and any `CORE TIER BUDGET EXCEEDED` block verbatim, or the recorded not-applicable line; plus `git diff --stat <execution base>..HEAD -- agent_workflows/` showing no change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract: all open questions are resolved. SCOPE FENCE: `tests/test_residual_guard_fallback.py` only, created only if E-05 requires it; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Commit through `aw commit e6lq6y -- tests/test_residual_guard_fallback.py` when a file changes, never push, never `git add -A`, and paste actual runner output for every `V-*`. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
