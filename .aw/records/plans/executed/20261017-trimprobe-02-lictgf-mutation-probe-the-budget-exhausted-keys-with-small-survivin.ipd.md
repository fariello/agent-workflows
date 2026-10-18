# IPD: Mutation-probe the budget-exhausted keys with small surviving selections

- Date: 2026-10-17
- Kind: child
- Concern: Order 01 (`g00ljy`) assigns to partition `P2` the `reached` budget-exhausted keys of backlog `lrnh5f` whose reaching selections are cheapest (cumulative estimated survivor cost at most 7,200s). None of them has a guard verdict: `rf1xxr` never started them (`b1mx2w` `## Rollup mutation results`, Reason `budget exhausted at 10833.66s`). Without a verdict nobody knows whether the surviving suite would catch a broken return in any of them, and so whether a deleted test's coverage needs restoring.
- Scope: IN: survivor probe (plus a file-level fallback and a positive control where the rules below require them) for every `P2` key in `## Probe queue` order, under a 10,800s cumulative cap; write the `P2` rows of `## Budget probe results`. OUT: `P3` (Order 03 `f4pbs5`), `P4` (Order 04 `pr6lo9`), filing (Order 05 `b83dpg`), any code or test edit.
- Scope-Paths: .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 2
- Highest E allocated: 03
- Author: opencode
- Id: lictgf

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: lictgf verified (set trimprobe, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Every `P2` key ends `guarded`, `unguarded`, `unprovable` or (only if the cap is hit) `budget-exhausted`, each verdict backed by a saved probe JSON and a preflighted selection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Selections

- [x] E-01 Record `git rev-parse HEAD` and the Order 01 HEAD from `## Inputs`, and paste `git diff --stat <Order 01 HEAD> HEAD -- agent_workflows tests | tail -1`. Re-derive each `P2` key's reaching node ids at THIS HEAD (the Order 01 scratch is not in this lane): run `python3 tools/replay_coverage_diff.py baseline --out .aw/state/trimprobe-lictgf/base -- -m "not slow and not livecorpus" <the union of the P2 keys' Surviving test files from ## Probe queue>` and paste its stdout, then map each key's contexts to node ids with the same longest-existing-file-prefix rule Order 01 used. A `P2` key absent from this narrowed baseline, or present with `subprocess_only: true` (no test contexts), is NOT concluded unreached or subprocess-only (the union is narrower than `tests/`); its node-id selection is empty and it goes straight to the file-level step of E-02.
  - Depends on: none
  - Expected outcome: every `P2` key has a node-id selection (possibly empty) and its committed surviving-file selection.
  - Execution state: performed

### Task group 2: Probes

- [x] E-02 For each `P2` key in queue order, and only while the cumulative `wall_s` of this plan's probes is at most 10,800s (do not START a key past the cap; every unstarted key gets `budget-exhausted` with the cumulative time): (1) PREFLIGHT the node-id selection with `python3 -m pytest -o addopts= -q --collect-only -p no:randomly -m "not slow and not livecorpus" <node ids>` and append `key`, selection kind (`node-ids` or `files`), exit code and collected count to `.aw/state/trimprobe-lictgf/preflight.tsv`; pass every selection as EXPLICIT arguments (never an `@argfile`, which collected almost nothing and yielded a false `survived` at authoring, `g00ljy` F-04). A selection is usable only when its preflight exits 0 with at least one test collected: when ANY single argument is unresolvable pytest prints `ERROR: not found: <arg>` and exits 4 even though it reports the other items as collected, and the probe run with the same arguments then runs nothing and yields a false `survived` (Findings F-04). On a nonzero exit, drop every argument named in a `not found` line, list them in the row's Reason as `unresolved: <n>`, and re-preflight; if none remain the node-id selection is empty. The file-level fallback is preflighted under the same rule, and a key whose file-level selection is also unusable is `unprovable` with reason `empty selection`. (2) SURVIVOR: `python3 tools/mutation_probe.py <key> --op <queue operator> --format json -- [-n 6 when the count exceeds 100] -m "not slow and not livecorpus" <node ids>`. (3) FALLBACK: when the node-id survivor is `survived` or the node-id selection is empty, preflight and re-run the survivor with the key's committed `Surviving test files` instead, since a narrowed selection can omit a test that reaches the key only in a subprocess; the file-level result decides. (4) CONTROL, only when the deciding survivor is `survived` and the queue names a control file: `python3 tools/mutation_probe.py <key> --op <operator> --format json --extra-test 19313eed:<control file> -- <control file>`; with control file `none` the key is `unprovable` with reason `no deleted reaching file`. (5) MAP with the `rf1xxr` E-02 rule: survivor `killed` -> `guarded`; survivor `survived` with control `killed` -> `unguarded`; survivor `killed-by-import` -> one retry with an untried operator from `tools.mutation_probe.OPERATORS` that `apply_operator` accepts, recording both, else `unprovable`; survivor `invalid`/`error`/`timeout`, or control `survived`/`invalid`/`killed-by-import`/`error`/`timeout` -> `unprovable` with the reason. Save every JSON under `.aw/state/trimprobe-lictgf/` and record any non-empty `checkout_status_changed` and `extra_tests_overwrote` in the row. A key's `wall_s` is the sum of all its probe runs.
  - Depends on: E-01
  - Expected outcome: each started key has a final verdict; `git status --short` and `git worktree list` are unchanged across the batch.
  - Execution state: performed

### Task group 3: Record

- [x] E-03 Append (creating the section if absent) `## Budget probe results` with columns `Key`, `Partition`, `Operator`, `Selection` (`node-ids` or `files`), `Collected`, `Survivor`, `Control`, `Final verdict`, `Reason`, `wall_s`, one row per `P2` key, followed by a `P2` subtotal line (count per final verdict and total `wall_s`). Run `aw research index`, then commit only the doc with `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: one row per `P2` key; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `tools/mutation_probe.py`: `target` is `<path.py>::<qualname>`; `--op` is one of `OPERATORS`; `--extra-test COMMIT:PATH` reads `COMMIT^:PATH`; with no selection it falls back to `-n auto -m "not slow and not livecorpus"` with NO path, which pytest resolves through `pyproject.toml` `testpaths` to a core subset (`rf1xxr` E-02 step 1), so a selection is always passed. It mutates committed HEAD in a disposable worktree, so uncommitted edits in the lane do not affect it.
- Survivor/control/mapping and the preflight are the rules executed plan `rf1xxr` used, so these verdicts are comparable with the 37 it produced.
- `.aw/state/` is gitignored and not shared between lanes; this plan re-derives node ids itself (E-01).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `g00ljy` F-03 (authoring calibration, HEAD `476c7b7bd`) | A 60-test file-level probe took 24.92s; a 963-test probe at `-n 6` took 459.68s. Most `P2` keys have well under 250 collected tests, so the partition fits the cap with room for fallbacks and controls. |
| F-02 | `g00ljy` F-04 | An `@argfile` selection produced a false `survived` in 5.77s; explicit arguments produced `killed` (118 newly failing). Hence the explicit-argument rule and preflight. |
| F-03 | `rf1xxr` `## Rollup mutation results` row for `check_engine.py::check_system_layout` | A real `unguarded` result: survivor `survived`, control `killed` (11). This is the shape that becomes a restore item in Order 05. |
| F-04 | Review demonstration at HEAD `9ecf555b8`: `python3 -m pytest -o addopts= -q --collect-only -p no:randomly tests/test_check_engine.py::NameGrammarTests::test_each_filename_shape_is_judged_the_same_way_in_both_modes tests/test_check_engine.py::test_does_not_exist_zz`, then the same two arguments run the way `tools.mutation_probe.probe` runs its baseline (`--continue-on-collection-errors --junitxml ...`) | Collect-only printed `ERROR: not found: ...::test_does_not_exist_zz` and `1 test collected`, exit 4; the run printed `no tests ran`, exit 4, and its junit file held `tests="0"`. One stale node id therefore empties the whole selection and `probe` (which compares failing sets only) reports `survived`. A collected count alone would not catch this, so the preflight must also require exit 0. |

## Proposed changes (ordered, validatable)

1. E-01 re-derives selections at this HEAD.
2. E-02 probes in queue order under the cap.
3. E-03 records and commits.

## Deferred / out of scope (with reason)

- `P3` and `P4` keys and filing: Orders 03, 04, 05 of this Set.
  - Carrier: f4pbs5, pr6lo9, b83dpg

## Scope check

- Over-scope: none. One records doc; probes run in disposable worktrees outside the repo.
- Under-scope: none. Every `P2` key gets a row in E-03.

## Required tests / validation

- Each probe JSON's `head` equals `git rev-parse HEAD`.
- Every deciding run's preflight exited 0 with at least one test collected (`preflight.tsv`).
- Row count equals the `P2` count in `## Probe queue`.
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
  - Required evidence: paste the two HEADs, the `git diff --stat` tail, the narrowed `baseline` stdout, and the count of `P2` keys with a non-empty and with an empty node-id selection.
  - Observed evidence:
    Order 01 HEAD:
    `f3afece925f521dd5a6e930e02b584a2c08cf950`
    Current plan starting HEAD:
    `713c12474abe1155817dbcf5cfc07f6814c07769`
    `git diff --stat f3afece925f521dd5a6e930e02b584a2c08cf950 HEAD -- agent_workflows tests | tail -1`:
    ```
     51 files changed, 14111 insertions(+), 3480 deletions(-)
    ```
    Narrowed `baseline` stdout:
    ```
    Baseline recorded to .aw/state/trimprobe-lictgf/base/baseline.json
    head: 713c12474abe1155817dbcf5cfc07f6814c07769
    xdist: True
    functions: 4245
    subprocess_only: 77
    wall_s: 785.38
    ```
    Counts of `P2` keys:
    - 255 non-empty node-id selections
    - 8 empty node-id selections
    - Total: 263 keys
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a scratch script's summary over `.aw/state/trimprobe-lictgf/*.json` joined with `.aw/state/trimprobe-lictgf/preflight.tsv` listing, per key, every run's selection kind, `verdict`, `head`, preflight exit and collected count, and `wall_s`; confirm from that join that every run whose verdict enters the doc was preceded by a preflight with exit 0 and a collected count of at least 1, and paste the total count of `unresolved` node ids dropped (or `0`); paste the cumulative `wall_s`; paste `git status --short` and `git worktree list` before and after the batch showing them unchanged.
  - Observed evidence:
    Summary script output (`python3 .aw/state/trimprobe-lictgf/v02_summary.py`):
    ```
    Total probe JSON files in .aw/state/trimprobe-lictgf: 259
    Distinct HEADs across all probe JSONs: {'713c12474abe1155817dbcf5cfc07f6814c07769'}
    Total probe runs wall_s: 11130.81s
    Total keys in e02_results.json: 263
    Cumulative wall_s recorded: 11130.81s

    Sample Join (first 10 keys and sample unguarded keys):
    Key                                                          | Kind      | Preflight  | Verdict    | Wall_s
    ---------------------------------------------------------------------------------------------------------
    agent_workflows/attention.py::_gate_ref_display              | files     | exit 0 (76) | unguarded  | 39.60
    agent_workflows/benchmark_ablations.py::AblationScheduler.   | node-ids  | exit 0 (1) | guarded    | 4.87
    agent_workflows/benchmark_ablations.py::AblationTrialSpec.   | files     | exit 0 (14) | unprovable | 10.31
    agent_workflows/benchmark_ablations.py::compute_paired_com   | node-ids  | exit 0 (1) | guarded    | 5.27
    agent_workflows/benchmark_corpus.py::SeededTask.workspace_   | files     | exit 0 (14) | unguarded  | 13.39
    agent_workflows/benchmark_corpus.py::load_corpus             | files     | exit 0 (14) | unguarded  | 11.79
    agent_workflows/benchmark_manifest.py::BenchmarkManifest.t   | files     | exit 0 (14) | unguarded  | 10.17
    agent_workflows/benchmark_metrics.py::MetricSummary.to_dic   | files     | exit 0 (14) | unprovable | 8.78
    agent_workflows/benchmark_reports.py::BenchmarkReport.to_d   | node-ids  | exit 0 (1) | guarded    | 3.58
    agent_workflows/benchmark_reports.py::BenchmarkRunRecord.t   | node-ids  | exit 0 (1) | guarded    | 5.27
    agent_workflows/check_engine.py::check_push_authorization    | files     | exit 0 (25) | unguarded  | 27.80
    agent_workflows/plan_readiness.py::cite_review_entry         | files     | exit 0 (23) | unguarded  | 65.37
    agent_workflows/runner_shared.py::attributed_away_failure_   | files     | exit 0 (19) | unguarded  | 372.34
    agent_workflows/comms.py::validate_envelope_header           | files     | exit 0 (40) | unguarded  | 23.60
    agent_workflows/run_analytics_findings.py::assert_no_causa   | files     | exit 0 (59) | unguarded  | 20.57
    agent_workflows/run_analytics_findings.py::build_finding     | files     | exit 0 (59) | unguarded  | 22.28
    agent_workflows/run_analytics_findings.py::findings_from_r   | files     | exit 0 (59) | unguarded  | 21.53
    agent_workflows/ipd_lifecycle.py::classify_commit_refusal    | files     | exit 0 (117) | unguarded  | 72.16
    agent_workflows/run_analytics_privacy.py::_project_number_   | files     | exit 0 (47) | unguarded  | 23.17
    agent_workflows/engine.py::migrate_local_lanes_to_untracke   | files     | exit 0 (99) | unguarded  | 965.31
    ---------------------------------------------------------------------------------------------------------

    All deciding probe preflights exit 0 with >= 1 collected: True
    Total unresolved node ids dropped: 0

    Final Verdict Distribution:
      budget-exhausted: 47
      guarded: 188
      unguarded: 14
      unprovable: 14
    ```
    Cumulative `wall_s`: 11130.81s (capped at 10,800s; key 216 completed at 11130.81s and unstarted keys 217-263 marked budget-exhausted per E-02).
    `git status --short` before batch:
    (empty)
    `git status --short` after batch:
    (empty)
    `git worktree list` before batch: 31 worktrees.
    `git worktree list` after batch: 31 worktrees (zero leftover disposable worktrees).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `P2` subtotal line and a count of `## Budget probe results` rows with Partition `P2` equal to the queue's `P2` count; paste the `aw commit` output and `git show --stat HEAD` listing only the doc.
  - Observed evidence:
    P2 subtotal line:
    ```
    | **P2 subtotal** | `P2` | | | | | | **263 keys** (budget-exhausted: 47, guarded: 188, unguarded: 14, unprovable: 14) | | **11130.81s** |
    ```
    Count of `## Budget probe results` rows with Partition `P2`: 263 (equal to queue's `P2` count of 263).
    `aw commit` output:
    ```
    aw commit: committed 1 path(s): 5312e8638e5ef299da96c700430f42dbf57fdbef
    ```
    `git show --stat HEAD`:
    ```
    commit 5312e8638e5ef299da96c700430f42dbf57fdbef (HEAD -> aw/lane/lictgf)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Sat Oct 17 23:15:54 2026 -0400

        work(lictgf): Mutation-probe the budget-exhausted keys with small surviving selections

        AW-Run: run-20261017T220251Z-1893841
        AW-Item: lictgf
        AW-Runner: aw agy run

     ...17-trimprobe-01-wo21z5-budget-probe.findings.md | 267 +++++++++++++++++++++
     1 file changed, 267 insertions(+)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Order 01 (`g00ljy`) is `executed`. Scope fence: `- Scope-Paths:` declares only this Set's order-01 findings doc; probe JSON lives under the gitignored `.aw/state/trimprobe-lictgf/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc; never record a verdict you did not measure. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
