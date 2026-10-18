# IPD: Mutation-probe the budget-exhausted keys with large surviving selections

- Date: 2026-10-17
- Kind: child
- Concern: Order 01 (`g00ljy`) assigns to partition `P3` the `reached` budget-exhausted keys of backlog `lrnh5f` left after `P2`'s 7,200s estimate: the keys reached by the most tests (shared helpers such as `project_context._resolve_effective_aw_home`, `result_types.select_output`, `cli._dispatch`, whose surviving files collected 6,258, 4,387 and 2,869 tests at authoring). None of them has a guard verdict: `rf1xxr` never started them (`b1mx2w` `## Rollup mutation results`, Reason `budget exhausted at 10833.66s`). Without a verdict nobody knows whether the surviving suite would catch a broken return in any of them, and so whether a deleted test's coverage needs restoring.
- Scope: IN: survivor probe (plus a file-level fallback and a positive control where the rules below require them) for every `P3` key in `## Probe queue` order, under a 10,800s cumulative cap; write the `P3` rows of `## Budget probe results`. OUT: `P2` (Order 02 `lictgf`), `P4` (Order 04 `pr6lo9`), filing (Order 05 `b83dpg`), any code or test edit.
- Scope-Paths: .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy, executed:lictgf
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 3
- Highest E allocated: 03
- Author: opencode
- Id: f4pbs5

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: f4pbs5 verified (set trimprobe, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Every `P3` key ends `guarded`, `unguarded`, `unprovable` or (only if the cap is hit) `budget-exhausted`, each verdict backed by a saved probe JSON and a preflighted selection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Selections

- [x] E-01 Confirm `## Budget probe results` already holds the Order 02 `P2` rows (paste their count). Record `git rev-parse HEAD` and the Order 01 HEAD from `## Inputs`, and paste `git diff --stat <Order 01 HEAD> HEAD -- agent_workflows tests | tail -1`. Re-derive each `P3` key's reaching node ids at THIS HEAD (the Order 01 scratch is not in this lane): run `python3 tools/replay_coverage_diff.py baseline --out .aw/state/trimprobe-f4pbs5/base -- -m "not slow and not livecorpus" <the union of the P3 keys' Surviving test files from ## Probe queue>` and paste its stdout, then map each key's contexts to node ids with the same longest-existing-file-prefix rule Order 01 used. A `P3` key absent from this narrowed baseline, or present with `subprocess_only: true` (no test contexts), is NOT concluded unreached or subprocess-only (the union is narrower than `tests/`); its node-id selection is empty and it goes straight to the file-level step of E-02.
  - Depends on: none
  - Expected outcome: every `P3` key has a node-id selection (possibly empty) and its committed surviving-file selection.
  - Execution state: performed

### Task group 2: Probes

- [x] E-02 For each `P3` key in queue order, and only while the cumulative `wall_s` of this plan's probes is at most 10,800s (do not START a key past the cap; every unstarted key gets `budget-exhausted` with the cumulative time): (1) PREFLIGHT the node-id selection with `python3 -m pytest -o addopts= -q --collect-only -p no:randomly -m "not slow and not livecorpus" <node ids>` and append `key`, selection kind (`node-ids` or `files`), exit code and collected count to `.aw/state/trimprobe-f4pbs5/preflight.tsv`; pass every selection as EXPLICIT arguments (never an `@argfile`, which collected almost nothing and yielded a false `survived` at authoring, `g00ljy` F-04). A selection is usable only when its preflight exits 0 with at least one test collected: when ANY single argument is unresolvable pytest prints `ERROR: not found: <arg>` and exits 4 even though it reports the other items as collected, and the probe run with the same arguments then runs nothing and yields a false `survived` (`lictgf` F-04). On a nonzero exit, drop every argument named in a `not found` line, list them in the row's Reason as `unresolved: <n>`, and re-preflight; if none remain the node-id selection is empty. The file-level fallback is preflighted under the same rule, and a key whose file-level selection is also unusable is `unprovable` with reason `empty selection`. (2) SURVIVOR: `python3 tools/mutation_probe.py <key> --op <queue operator> --format json [--timeout 3600 when the count exceeds 3000] -- [-n 6 when the count exceeds 100] -m "not slow and not livecorpus" <node ids>`. `--timeout` is the PROBE's option and MUST precede `--`: everything after `--` is passed to pytest (`tools.mutation_probe.main` "post_sep"), and this repository's pytest has no `--timeout` (no `pytest_timeout` plugin), so it would exit 4 with `unrecognized arguments: --timeout`, write no junit file, and the probe would report `error` (Findings F-04). The same placement applies to the file-level fallback. (3) FALLBACK: when the node-id survivor is `survived` or the node-id selection is empty, preflight and re-run the survivor with the key's committed `Surviving test files` instead, since a narrowed selection can omit a test that reaches the key only in a subprocess; the file-level result decides. (4) CONTROL, only when the deciding survivor is `survived` and the queue names a control file: `python3 tools/mutation_probe.py <key> --op <operator> --format json --extra-test 19313eed:<control file> -- <control file>`; with control file `none` the key is `unprovable` with reason `no deleted reaching file`. (5) MAP with the `rf1xxr` E-02 rule: survivor `killed` -> `guarded`; survivor `survived` with control `killed` -> `unguarded`; survivor `killed-by-import` -> one retry with an untried operator from `tools.mutation_probe.OPERATORS` that `apply_operator` accepts, recording both, else `unprovable`; survivor `invalid`/`error`/`timeout`, or control `survived`/`invalid`/`killed-by-import`/`error`/`timeout` -> `unprovable` with the reason. Save every JSON under `.aw/state/trimprobe-f4pbs5/` and record any non-empty `checkout_status_changed` and `extra_tests_overwrote` in the row. A key's `wall_s` is the sum of all its probe runs.
  - Depends on: E-01
  - Expected outcome: each started key has a final verdict; `git status --short` and `git worktree list` are unchanged across the batch.
  - Execution state: performed

### Task group 3: Record

- [x] E-03 Append to `## Budget probe results` (same columns as Order 02) one row per `P3` key, followed by a `P3` subtotal line (count per final verdict and total `wall_s`). Run `aw research index`, then commit only the doc with `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: one row per `P3` key; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `tools/mutation_probe.py`: `target` is `<path.py>::<qualname>`; `--op` is one of `OPERATORS`; `--extra-test COMMIT:PATH` reads `COMMIT^:PATH`; with no selection it falls back to `-n auto -m "not slow and not livecorpus"` with NO path, which pytest resolves through `pyproject.toml` `testpaths` to a core subset (`rf1xxr` E-02 step 1), so a selection is always passed. It mutates committed HEAD in a disposable worktree, so uncommitted edits in the lane do not affect it.
- Survivor/control/mapping and the preflight are the rules executed plan `rf1xxr` used, so these verdicts are comparable with the 37 it produced.
- `.aw/state/` is gitignored and not shared between lanes; this plan re-derives node ids itself (E-01).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `g00ljy` F-03 and F-05 (authoring, HEAD `476c7b7bd`) | A 963-test probe at `-n 6` took 459.68s (about 0.48 s per collected test, baseline plus mutant). `P3` keys' reaching contexts are far fewer than their file selections (25,601 contexts versus 104,864 file-level items over all 292 reached keys), which is why the node-id selection, not the file selection, is the first survivor. The default probe `--timeout` is 1800s per pytest run (`tools.mutation_probe.main`), hence the raised timeout for the largest selections. |
| F-02 | `g00ljy` F-04 | An `@argfile` selection produced a false `survived` in 5.77s; explicit arguments produced `killed` (118 newly failing). Hence the explicit-argument rule and preflight. |
| F-03 | `rf1xxr` `## Rollup mutation results` row for `check_engine.py::check_system_layout` | A real `unguarded` result: survivor `survived`, control `killed` (11). This is the shape that becomes a restore item in Order 05. |
| F-04 | Review demonstration at HEAD `cb60e5c80`: `python3 -c "import pytest_timeout"` -> `ModuleNotFoundError`; `python3 -m pytest -o addopts= -q --collect-only -p no:randomly --timeout 3600 tests/test_check_engine.py` -> `error: unrecognized arguments: --timeout`, exit 4; the same arguments run as `tools.mutation_probe.probe` runs its baseline (`--continue-on-collection-errors --junitxml <f>`) -> exit 4 and no junit file written | As authored, `--timeout 3600` sat after `--`, which `tools.mutation_probe.main` forwards to pytest. Every key above 3,000 collected tests (the largest `P3` keys) would have ended `error` -> `unprovable` with no probe performed. The option belongs before `--`, where `main` parses it as the probe's per-run timeout. |
| F-05 | `lictgf` F-04 (review demonstration) | One unresolvable node id makes the collect-only preflight exit 4 while still printing a non-zero collected count, and the probe then runs nothing and reports `survived`. Hence the exit-0 rule in E-02 step (1). |

## Proposed changes (ordered, validatable)

1. E-01 confirms Order 02 landed and re-derives selections at this HEAD.
2. E-02 probes in queue order under the cap.
3. E-03 records and commits.

## Deferred / out of scope (with reason)

- `P4` keys and filing: Orders 04 and 05 of this Set.
  - Carrier: pr6lo9, b83dpg

## Scope check

- Over-scope: none. One records doc; probes run in disposable worktrees outside the repo.
- Under-scope: none. Every `P3` key gets a row in E-03. Any key the cap leaves unstarted is recorded `budget-exhausted` and Order 05 carries it forward to a new backlog item.

## Required tests / validation

- Each probe JSON's `head` equals `git rev-parse HEAD`.
- Every deciding run's preflight exited 0 with at least one test collected (`preflight.tsv`).
- No probe JSON has `verdict: error` caused by an argument pytest rejected.
- Row count equals the `P3` count in `## Probe queue`.
- `git status --short` unchanged by probes.

## Spec / documentation sync

N/A: a measurement record only; no `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Probe with `return-none` for every key, or each key's recorded operator?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: the recorded operator (as corrected by `g00ljy` E-03). The backlog body says "probe ... with mutation operator return-none", which matches 278 of the 319 rows; the other 41 were assigned `raise`, `negate-return` or `return-false` in `hpjj44` `## Derived properties` because `return-none` is a weak or equivalent mutant for them (for example a predicate where `None` is as falsy as the real `False`). Using the recorded operator keeps verdicts comparable with `rf1xxr`'s 37.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the two HEADs, the `git diff --stat` tail, the narrowed `baseline` stdout, and the count of `P3` keys with a non-empty and with an empty node-id selection.
  - Observed evidence:
    Order 01 HEAD:
    `f3afece925f521dd5a6e930e02b584a2c08cf950`
    Current plan starting HEAD:
    `d9ed1bcc6d1b3875070650d413a5c81e7476b1f6`
    `git diff --stat f3afece925f521dd5a6e930e02b584a2c08cf950 HEAD -- agent_workflows tests | tail -1`:
    ```
     101 files changed, 41690 insertions(+), 3696 deletions(-)
    ```
    Narrowed `baseline` stdout:
    ```
    Baseline recorded to /mnt/md1/VC/agent-workflows/.aw/worktrees/f4pbs5/.aw/state/trimprobe-f4pbs5/base/baseline.json
    head: d9ed1bcc6d1b3875070650d413a5c81e7476b1f6
    xdist: True
    functions: 4270
    subprocess_only: 97
    wall_s: 1001.53
    ```
    Counts of `P3` keys:
    - 37 non-empty node-id selections
    - 0 empty node-id selections
    - Total: 37 keys
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a scratch script's summary over `.aw/state/trimprobe-f4pbs5/*.json` joined with `.aw/state/trimprobe-f4pbs5/preflight.tsv` listing, per key, every run's selection kind, `verdict`, `head`, preflight exit and collected count, and `wall_s`; confirm from that join that every run whose verdict enters the doc was preceded by a preflight with exit 0 and a collected count of at least 1, and paste the total count of `unresolved` node ids dropped (or `0`); paste the command line of one run with more than 3,000 collected tests showing `--timeout 3600` before `--` (or state that no such key was started); paste the cumulative `wall_s`; paste `git status --short` and `git worktree list` before and after the batch showing them unchanged.
  - Observed evidence:
    Summary script output (`python3 .aw/state/trimprobe-f4pbs5/v02_summary.py`):
    ```
    Total probe JSON files in .aw/state/trimprobe-f4pbs5: 32
    Distinct HEADs across all probe JSONs: {'d9ed1bcc6d1b3875070650d413a5c81e7476b1f6'}
    Total probe runs wall_s: 10845.88s
    Total keys in e02_results.json: 37
    Cumulative wall_s recorded: 10845.88s

    Join Summary:
    Key                                                          | Kind      | Preflight     | Verdict    | Wall_s
    ---------------------------------------------------------------------------------------------------------
    agent_workflows/run_analytics_telemetry.py::TelemetryColl... | node-ids  | exit 0 (266)  | guarded    | 216.17
    agent_workflows/run_analytics_telemetry.py::TelemetryColl... | files     | exit 0 (1160) | unprovable | 699.74
    agent_workflows/run_analytics_telemetry.py::TelemetryColl... | node-ids  | exit 0 (266)  | guarded    | 224.17
    agent_workflows/run_analytics_telemetry.py::TelemetryColl... | node-ids  | exit 0 (266)  | guarded    | 226.57
    agent_workflows/run_analytics_telemetry.py::TelemetryColl... | node-ids  | exit 0 (266)  | guarded    | 255.41
    agent_workflows/run_analytics_telemetry.py::_validate_lab... | files     | exit 0 (1160) | unguarded  | 759.95
    agent_workflows/run_analytics_telemetry.py::_validate_too... | files     | exit 0 (1160) | unguarded  | 808.98
    agent_workflows/run_analytics_telemetry.py::node_pseudonym   | files     | exit 0 (1160) | unguarded  | 918.20
    agent_workflows/run_analytics_telemetry.py::_validate_num... | files     | exit 0 (1162) | unguarded  | 779.41
    agent_workflows/run_analytics_telemetry.py::ResourceProbe... | node-ids  | exit 0 (268)  | guarded    | 256.45
    agent_workflows/run_analytics_telemetry.py::SystemResourc... | node-ids  | exit 0 (268)  | guarded    | 203.79
    agent_workflows/run_analytics_telemetry.py::_as_label        | node-ids  | exit 0 (268)  | guarded    | 239.68
    agent_workflows/run_analytics_telemetry.py::_refuse_unknown  | node-ids  | exit 0 (269)  | guarded    | 217.42
    agent_workflows/run_analytics_telemetry.py::_validate_scalar | node-ids  | exit 0 (269)  | guarded    | 262.02
    agent_workflows/run_analytics_telemetry.py::validate_event   | node-ids  | exit 0 (269)  | guarded    | 230.28
    agent_workflows/runner_shared.py::gate_answer_is_warranted   | node-ids  | exit 0 (270)  | guarded    | 1455.25
    agent_workflows/check_engine.py::_review_index               | files     | exit 0 (1282) | unprovable | 725.35
    agent_workflows/agent_schema.py::normalize_repo_path         | node-ids  | exit 0 (331)  | guarded    |  98.77
    agent_workflows/agy_verifier.py::run_fresh_verifier          | node-ids  | exit 0 (344)  | guarded    | 1044.18
    agent_workflows/verify_roles.py::validate_verifier_packet    | node-ids  | exit 0 (344)  | guarded    | 1224.09
    agent_workflows/verify_roles.py::check_role_action           | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/run_analytics_config.py::_coerce_bool        | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/run_analytics_config.py::parse_telemetry_... | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/result_types.py::CommandResult.to_agent_r... | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/ipd_lint.py::lint_file                       | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/renderers.py::BaseRenderer.emit              | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/ipd_lint.py::check_item_dependencies         | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/config.py::findings_gate_threshold           | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/config.py::read_review_findings_gate         | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/ipd_schema.py::parse_item_dependencies       | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/check_engine.py::_iter_type_files            | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/agent_schema.py::validate_agent_record       | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/term.py::stdin_is_interactive                | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/term.py::is_interactive                      | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/cli.py::_dispatch                            | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/result_types.py::select_output               | n/a       | n/a           | budget-exhausted |   0.00
    agent_workflows/project_context.py::_resolve_effective_aw... | n/a       | n/a           | budget-exhausted |   0.00
    ---------------------------------------------------------------------------------------------------------

    All deciding probe preflights exit 0 with >= 1 collected: True
    Total unresolved node ids dropped: 0

    Final Verdict Distribution:
      budget-exhausted: 17
      guarded: 14
      unguarded: 4
      unprovable: 2
    ```
    No run over 3000 collected tests was started (dispatch stopped at cumulative wall_s 10845.88s after key 20 per E-02 cap; key 37 was not started).
    Cumulative `wall_s`: 10845.88s (capped at 10,800s; key 20 completed at 10845.88s and unstarted keys 21-37 marked budget-exhausted per E-02).
    `git status --short` before batch:
    (empty)
    `git status --short` after batch:
    (empty)
    `git worktree list` before batch: 29 worktrees.
    `git worktree list` after batch: 29 worktrees (zero leftover disposable worktrees).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `P3` subtotal line and a count of `## Budget probe results` rows with Partition `P3` equal to the queue's `P3` count, and the `P2` row count unchanged from E-01; paste the `aw commit` output and `git show --stat HEAD` listing only the doc.
  - Observed evidence:
    P3 subtotal line:
    ```
    | **P3 subtotal** | `P3` | | | | | | **37 keys** (budget-exhausted: 17, guarded: 14, unguarded: 4, unprovable: 2) | | **10845.88s** |
    ```
    Count of `## Budget probe results` rows with Partition `P3`: 37 (equal to queue's `P3` count of 37).
    Count of `## Budget probe results` rows with Partition `P2`: 263 (unchanged from E-01).
    `aw commit` output:
    ```
    aw commit: committed 1 path(s): c7da1e9ca973abcf88602a5e6d47ab9e478c28f2
    ```
    `git show --stat HEAD`:
    ```
    commit c7da1e9ca973abcf88602a5e6d47ab9e478c28f2 (HEAD -> aw/lane/f4pbs5)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Sun Oct 18 02:46:09 2026 -0400

        work(f4pbs5): Mutation-probe the budget-exhausted keys with large surviving selections

        AW-Run: run-20261017T220251Z-1893841
        AW-Item: f4pbs5
        AW-Runner: aw agy run

     ...17-trimprobe-01-wo21z5-budget-probe.findings.md | 38 ++++++++++++++++++++++
     1 file changed, 38 insertions(+)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 (`g00ljy`) and 02 (`lictgf`) are `executed` (Order 02 first so both append to the same section in a fixed order). Scope fence: `- Scope-Paths:` declares only this Set's order-01 findings doc; probe JSON lives under the gitignored `.aw/state/trimprobe-f4pbs5/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc; never record a verdict you did not measure. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
