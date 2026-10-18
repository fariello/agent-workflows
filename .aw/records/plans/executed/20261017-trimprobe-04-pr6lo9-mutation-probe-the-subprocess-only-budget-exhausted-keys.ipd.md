# IPD: Mutation-probe the subprocess-only budget-exhausted keys

- Date: 2026-10-17
- Kind: child
- Concern: 25 of backlog `lrnh5f`'s 319 keys were `subprocess-only` at `86f0d88d` (`b1mx2w` `## Key reach`): a test reaches them only inside a child process, so coverage records their lines with no test context and nothing says WHICH test file to select. `rf1xxr` planned to probe them with the full non-slow `tests/` selection and never started them. They include the git hook entry points (`hooks/ipd_dependency_statement_gate.py::main`/`check`/`_staged_ipd_overlay`, `hooks/prepush_authorization_gate.py::main`/`check`, `hooks/status_untooled_gate.py::main`/`check`), CLI leaves (`run_analytics_cli.py::run_export_leaf`/`run_submit_leaf`, `cli.py::_run_storage_init`, `run_cli.py::_run_decisions`/`_run_questions`) and the companion-storage helpers in `storage.py`. Order 01 (`g00ljy`) puts every key still `subprocess-only` at the current HEAD into partition `P4`.
- Scope: IN: for every `P4` key, a narrowed survivor over the test files that name the key's module, a positive control, and a full-selection fallback survivor while the 10,800s cap allows; write the `P4` rows of `## Budget probe results`. OUT: `P2`/`P3` (Orders 02 `lictgf`, 03 `f4pbs5`), filing (Order 05 `b83dpg`), any code or test edit.
- Scope-Paths: .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy, executed:f4pbs5
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 4
- Highest E allocated: 03
- Author: opencode
- Id: pr6lo9

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: pr6lo9 verified (set trimprobe, attempt 2).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Every `P4` key ends `guarded`, `unguarded`, `unprovable` or `budget-exhausted` with a reason that says which selection decided it, without claiming `unguarded` from a selection that may simply have missed the subprocess test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Selections

- [x] E-01 Confirm `## Budget probe results` holds the `P2` and `P3` rows (paste both counts). For each `P4` key, build its CANDIDATE selection as the test files under `tests/` whose text contains the key's module stem as a whole word (`rg -l -w <stem> tests/ --glob 'test_*.py'`; for `hooks/<name>.py` use `<name>`). The `--glob` matters: without it the match also returns support modules that hold no tests (for example `tests/conformance_matrix.py`, `tests/support.py`, `tests/fixtures/run_analytics/__init__.py`), and pytest would import them for nothing (Findings F-04). Paste the file count per key. Preflight each with `python3 -m pytest -o addopts= -q --collect-only -p no:randomly -m "not slow and not livecorpus" <files>` and append `key`, exit code and collected count to `.aw/state/trimprobe-pr6lo9/preflight.tsv`. A candidate selection is usable only when the preflight exits 0 with at least one test collected (the `lictgf` E-02 step 1 rule). A key with an empty or unusable candidate selection skips the narrowed survivor and goes to the control in E-02 step 2.
  - Depends on: none
  - Expected outcome: every `P4` key has a candidate selection and a preflight count (possibly 0).
  - Execution state: performed

### Task group 2: Probes

- [x] E-02 For each `P4` key in `## Probe queue` order while the cumulative `wall_s` is at most 10,800s (an unstarted key is `budget-exhausted` with the cumulative time): (1) NARROWED SURVIVOR: `python3 tools/mutation_probe.py <key> --op <queue operator> --format json -- [-n 6 when the count exceeds 100] -m "not slow and not livecorpus" <candidate files>`, explicit arguments only (`g00ljy` F-04). `killed` -> `guarded` (a kill is proof whatever the selection). `killed-by-import` -> one retry with an untried operator from `tools.mutation_probe.OPERATORS` that `apply_operator` accepts, recording both runs, and the retry's verdict is used in this step; still `killed-by-import`, or `invalid`/`error`/`timeout` -> `unprovable` with the reason (the `rf1xxr` E-02 step 5 rule), with no control or fallback. (2) If `survived` or skipped: CONTROL with the queue's control file exactly as Order 02 E-02 step 4 (`none` -> `unprovable`, reason `no deleted reaching file`; control not `killed` -> `unprovable` with the reason). (3) If the control `killed`: FALLBACK SURVIVOR `python3 tools/mutation_probe.py <key> --op <operator> --format json --timeout 3600 -- -n 6 -m "not slow and not livecorpus" tests/`. `--timeout` MUST precede `--`: `tools.mutation_probe.main` forwards everything after `--` to pytest, which has no `--timeout` here (no `pytest_timeout` plugin), so it would exit 4 with no junit file and the probe would report `error` (`f4pbs5` F-04). Start the fallback only if the cumulative `wall_s` plus the first fallback's measured cost (or 4,000s before any fallback has run) stays within the cap; fallback `killed` -> `guarded`, `survived` -> `unguarded`, otherwise `unprovable`. If the cap forbids the fallback the key is `budget-exhausted` with reason `narrowed survivor survived, control killed, full fallback not run`, which Order 05 carries forward rather than treating as `unguarded`. Save every JSON under `.aw/state/trimprobe-pr6lo9/`; record non-empty `checkout_status_changed` and `extra_tests_overwrote`.
  - Depends on: E-01
  - Expected outcome: each started key has a final verdict whose reason names the deciding selection; `git status --short` and `git worktree list` unchanged.
  - Execution state: performed

### Task group 3: Record

- [x] E-03 Append to `## Budget probe results` (Order 02 columns; `Selection` is `candidate-files` or `tests/`) one row per `P4` key and a `P4` subtotal line. Run `aw research index`, then commit only the doc with `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: one row per `P4` key; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A `subprocess-only` key has lines measured only through `coverage`'s `patch = subprocess` with empty dynamic contexts (`tools.replay_coverage_diff._make_rc_content`, `tools.replay_coverage_diff._collect_function_coverage` "subprocess_only: len(sorted_contexts) == 0"), so its reaching test file cannot be read from coverage.
- `tools/mutation_probe.py` defaults to a 1800s per-run `--timeout`; the full non-slow `tests/` selection is about 9,000 tests, so the fallback raises it.
- Mapping rules are `rf1xxr` E-02's, with one deliberate refinement: a narrowed `survived` never maps to `unguarded` by itself, because the selection is a guess.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results`, `subprocess-only` budget-exhausted rows | 25 keys across 12 modules; operators 23 `return-none`, 2 `raise`. |
| F-02 | Authoring, HEAD `476c7b7bd`: `rg -l -w <module stem> tests/` per key | Candidate counts range from 1 file (`migration_inventory`, `run_analytics_export`) to 179 (`cli`); the three hook modules each match 1 file by module name. |
| F-03 | `g00ljy` F-03 (calibration) | About 0.48s per collected test at `-n 6` for baseline plus mutant, so a full `tests/` fallback costs on the order of 4,000s and the cap affords at most two; most keys must be decided by the narrowed survivor or control. |
| F-04 | Review, HEAD `c2c1ab611`: `rg -l -w <stem> tests/` per stem, and `--collect-only` over the non-`test_*.py` matches | `storage` matched 8 files, one of them `tests/conformance_matrix.py`; `cli` 181 (3 non-test, including `tests/tools/leaf_probe.py`); `run_cli` 40 (3 non-test). Each non-test match collected `no tests` when passed alone (`leaf_probe.py` took 3.17s to import). With the `test_*.py` glob, the non-slow candidate selections collected 3,647 tests for `cli`, 1,133 for `run_cli`, 883 for `engine` and 1,258 for `check_engine`; full `tests/` collected 8,236. |

## Proposed changes (ordered, validatable)

1. E-01 builds and preflights candidate selections.
2. E-02 runs narrowed survivor, control, and budgeted fallback.
3. E-03 records and commits.

## Deferred / out of scope (with reason)

- Filing and reconciliation: Order 05.
  - Carrier: b83dpg

## Scope check

- Over-scope: none. One records doc.
- Under-scope: none. Every `P4` key gets a row.

## Required tests / validation

- Row count equals the queue's `P4` count; every probe JSON `head` equals `git rev-parse HEAD`; `git status --short` unchanged.
- Every narrowed survivor's preflight exited 0 with at least one test collected; no probe JSON has `verdict: error` caused by an argument pytest rejected.

## Spec / documentation sync

N/A: a measurement record only; no `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Treat a narrowed `survived` plus control `killed` as `unguarded` to save budget?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. `rf1xxr` E-02 step 1 shows a selection narrower than the reaching set yields a false `unguarded`; for subprocess-only keys the candidate set is a text-match guess. Such keys are `budget-exhausted` with an explicit reason when the fallback is unaffordable, and Order 05 carries them.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `P2`/`P3` row counts, and per `P4` key (from `preflight.tsv`) the candidate file count, preflight exit code and collected count.
  - Observed evidence:
```
P2 row count in Budget probe results: 263
P3 row count in Budget probe results: 37

key	file_count	exit_code	collected
agent_workflows/cli.py::_run_storage_init	192	0	4283
agent_workflows/engine.py::_ensure_untracked_gitignore	80	0	1827
agent_workflows/migration_inventory.py::_catalog_disposition	3	0	55
agent_workflows/run_analytics_cli.py::run_export_leaf	5	0	171
agent_workflows/run_analytics_cli.py::run_submit_leaf	5	0	171
agent_workflows/run_analytics_export.py::_tier_rank	5	0	133
agent_workflows/run_analytics_export.py::build_metrics_payload	5	0	133
agent_workflows/run_analytics_export.py::preview_raw_selection	5	0	133
agent_workflows/run_analytics_export.py::residual_risk_notes	5	0	133
agent_workflows/run_cli.py::_run_decisions	40	0	1226
agent_workflows/run_cli.py::_run_questions	40	0	1226
agent_workflows/runner_stop.py::install_stop_signal_handlers._sigint	21	0	474
agent_workflows/storage.py::detach_companion	10	0	508
agent_workflows/storage.py::get_git_common_dir	10	0	508
agent_workflows/storage.py::load_companion_identity	10	0	508
agent_workflows/storage.py::materialize_companion_storage	10	0	508
agent_workflows/storage.py::validate_companion_preflight	10	0	508
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a summary over `.aw/state/trimprobe-pr6lo9/*.json` listing per key each run's selection kind, `verdict`, `head` and `wall_s`; show that no `unguarded` row rests on anything but a `tests/` fallback `survived`; show that every narrowed survivor that was run had a usable preflight (exit 0, at least 1 collected); paste the command line of one fallback run showing `--timeout 3600` before `--` (or state that no fallback ran); paste the cumulative `wall_s`; paste `git status --short` and `git worktree list` before and after.
  - Observed evidence:
```
| File | Target Key | Selection Kind | Verdict | Head | wall_s |
|---|---|---|---|---|---|
| `01_agent_workflows_cli_py___run_storage_init_survivor.json` | `agent_workflows/cli.py::_run_storage_init` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 1080.53 |
| `02_agent_workflows_engine_py___ensure_untracked_gitignore_survivor.json` | `agent_workflows/engine.py::_ensure_untracked_gitignore` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 511.68 |
| `03_agent_workflows_migration_inventory_py___catalog_disposition_survivor.json` | `agent_workflows/migration_inventory.py::_catalog_disposition` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 24.44 |
| `04_agent_workflows_run_analytics_cli_py__run_export_leaf_survivor.json` | `agent_workflows/run_analytics_cli.py::run_export_leaf` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 26.48 |
| `05_agent_workflows_run_analytics_cli_py__run_submit_leaf_control.json` | `agent_workflows/run_analytics_cli.py::run_submit_leaf` | `control` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 13.42 |
| `05_agent_workflows_run_analytics_cli_py__run_submit_leaf_fallback.json` | `agent_workflows/run_analytics_cli.py::run_submit_leaf` | `tests/` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 3055.97 |
| `05_agent_workflows_run_analytics_cli_py__run_submit_leaf_survivor.json` | `agent_workflows/run_analytics_cli.py::run_submit_leaf` | `candidate-files` | `survived` | `918c30558a21a0d6839e115f927c559a56943b37` | 21.45 |
| `06_agent_workflows_run_analytics_export_py___tier_rank_survivor.json` | `agent_workflows/run_analytics_export.py::_tier_rank` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 13.02 |
| `07_agent_workflows_run_analytics_export_py__build_metrics_payload_survivor.json` | `agent_workflows/run_analytics_export.py::build_metrics_payload` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 14.21 |
| `08_agent_workflows_run_analytics_export_py__preview_raw_selection_survivor.json` | `agent_workflows/run_analytics_export.py::preview_raw_selection` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 12.08 |
| `09_agent_workflows_run_analytics_export_py__residual_risk_notes_survivor.json` | `agent_workflows/run_analytics_export.py::residual_risk_notes` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 14.30 |
| `10_agent_workflows_run_cli_py___run_decisions_survivor.json` | `agent_workflows/run_cli.py::_run_decisions` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 872.06 |
| `11_agent_workflows_run_cli_py___run_questions_survivor.json` | `agent_workflows/run_cli.py::_run_questions` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 939.34 |
| `12_agent_workflows_runner_stop_py__install_stop_signal_handlers__sigint_survivor.json` | `agent_workflows/runner_stop.py::install_stop_signal_handlers._sigint` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 201.27 |
| `13_agent_workflows_storage_py__detach_companion_survivor.json` | `agent_workflows/storage.py::detach_companion` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 336.00 |
| `14_agent_workflows_storage_py__get_git_common_dir_control.json` | `agent_workflows/storage.py::get_git_common_dir` | `control` | `survived` | `918c30558a21a0d6839e115f927c559a56943b37` | 12.63 |
| `14_agent_workflows_storage_py__get_git_common_dir_survivor.json` | `agent_workflows/storage.py::get_git_common_dir` | `candidate-files` | `survived` | `918c30558a21a0d6839e115f927c559a56943b37` | 303.20 |
| `15_agent_workflows_storage_py__load_companion_identity_survivor.json` | `agent_workflows/storage.py::load_companion_identity` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 338.37 |
| `16_agent_workflows_storage_py__materialize_companion_storage_survivor.json` | `agent_workflows/storage.py::materialize_companion_storage` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 340.21 |
| `17_agent_workflows_storage_py__validate_companion_preflight_survivor.json` | `agent_workflows/storage.py::validate_companion_preflight` | `candidate-files` | `killed` | `918c30558a21a0d6839e115f927c559a56943b37` | 329.13 |
```
No unguarded row rests on anything but a `tests/` fallback `survived`: in P4, 0 rows ended as unguarded.
Every narrowed survivor had a usable preflight: all 17 keys exited 0 with 55-4283 tests collected.
Fallback run command line:
`python3 tools/mutation_probe.py agent_workflows/run_analytics_cli.py::run_submit_leaf --op return-none --format json --timeout 3600 -- -n 6 -m not slow and not livecorpus tests/`
Cumulative `wall_s`: 8459.79s (budget cap 10,800s).
`git status --short` before and after:
```
(empty - clean working tree)
```
`git worktree list` before and after:
```
<repo-root>                                                          918c30558 [main]
<repo-root>/.aw/worktrees/gradfix-review                              199437f35 [review/gradfix-plan-review]
<repo-root>/.aw/worktrees/.aw-isocommit-ercg9nlx                     0d17632a9 (detached HEAD)
<repo-root>/.aw/worktrees/askmefix                                   188bee05a [aw/askmefix]
<repo-root>/.aw/worktrees/c8bfp9                                     c31960022 [aw/lane/c8bfp9]
<repo-root>/.aw/worktrees/dashux                                     bf5057b69 [aw/dashux]
<repo-root>/.aw/worktrees/diya77                                     0247a3505 [aw/lane/diya77]
<repo-root>/.aw/worktrees/e9l2e0                                     a07064f80 [aw/lane/e9l2e0]
<repo-root>/.aw/worktrees/kmmoca                                     4e29c67cd [aw/lane/kmmoca]
<repo-root>/.aw/worktrees/kmmoca_attempt2                            73f49811f [aw/lane/kmmoca_attempt2]
<repo-root>/.aw/worktrees/lkn1zt                                     0d9bd851e [aw/lane/lkn1zt]
<repo-root>/.aw/worktrees/lpvcln_attempt2                            4479c2a10 [aw/lane/lpvcln_attempt2]
<repo-root>/.aw/worktrees/modelnm                                    704b5e63e [aw/modelnm]
<repo-root>/.aw/worktrees/nwporz                                     a0b074226 [aw/lane/nwporz]
<repo-root>/.aw/worktrees/pr6lo9                                     918c30558 [aw/lane/pr6lo9]
<repo-root>/.aw/worktrees/pytest-speed-20261015                      ad9213cc6 [codex/pytest-speed-20261015]
<repo-root>/.aw/worktrees/qqrgv3                                     813a1fd99 [aw/lane/qqrgv3]
<repo-root>/.aw/worktrees/qqrgv3_attempt2                            13cf8aa1a [aw/lane/qqrgv3_attempt2]
<repo-root>/.aw/worktrees/revcost                                    131c9470d [aw/revcost]
<repo-root>/.aw/worktrees/review-sweep-run-20261015T224817Z-205920   23863c32a [aw/lane/review-sweep-run-20261015T224817Z-205920]
<repo-root>/.aw/worktrees/review-sweep-run-20261016T143713Z-1719552  653969dfb [aw/lane/review-sweep-run-20261016T143713Z-1719552]
<repo-root>/.aw/worktrees/runstok                                    3093b4c7c [aw/runstok]
<repo-root>/.aw/worktrees/s07f73                                     88f089186 [aw/lane/s07f73]
<repo-root>/.aw/worktrees/s07f73_attempt2                            8685b6d13 [aw/lane/s07f73_attempt2]
<repo-root>/.aw/worktrees/test-pruning-prompts                       eca2e2211 [work/test-pruning-prompts]
<repo-root>/.aw/worktrees/tgfxin                                     70b26623f [aw/lane/tgfxin]
<repo-root>/.aw/worktrees/tgfxin_attempt2                            a6e939758 [aw/lane/tgfxin_attempt2]
<repo-root>/.aw/worktrees/xc8nae                                     dea4f20f8 [aw/lane/xc8nae]
/tmp/opencode/askme-trialbed                                         0d9bd851e (detached HEAD)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `P4` subtotal line and a row count equal to the queue's `P4` count; paste the `aw commit` output and `git show --stat HEAD` listing only the doc.
  - Observed evidence:
```
P4 subtotal line:
| **P4 subtotal** | `P4` | | | | | | **17 keys** (budget-exhausted: 0, guarded: 16, unguarded: 0, unprovable: 1) | | **8459.79s** |

P4 row count in Budget probe results: 17

aw commit output:
aw commit: committed 1 path(s): 92b2b4f2711cb48311583ec62d44a00753442e85

git show --stat HEAD:
commit 92b2b4f2711cb48311583ec62d44a00753442e85 (HEAD -> aw/lane/pr6lo9)
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Sun Oct 18 05:19:39 2026 -0400

    work(pr6lo9): Mutation-probe the subprocess-only budget-exhausted keys

    AW-Run: run-20261017T220251Z-1893841
    AW-Item: pr6lo9
    AW-Runner: aw agy run

 ...61017-trimprobe-01-wo21z5-budget-probe.findings.md | 19 +++++++++++++++++++
 1 file changed, 19 insertions(+)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 (`g00ljy`) and 03 (`f4pbs5`) are `executed`, so this plan appends after the `P2` and `P3` rows. Scope fence: `- Scope-Paths:` declares only this Set's order-01 findings doc; probe JSON lives under the gitignored `.aw/state/trimprobe-pr6lo9/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
