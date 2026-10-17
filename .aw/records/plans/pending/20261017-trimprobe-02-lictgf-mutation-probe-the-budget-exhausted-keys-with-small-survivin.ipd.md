# IPD: Mutation-probe the budget-exhausted keys with small surviving selections

- Date: 2026-10-17
- Kind: child
- Concern: Order 01 (`g00ljy`) assigns to partition `P2` the `reached` budget-exhausted keys of backlog `lrnh5f` whose reaching selections are cheapest (cumulative estimated survivor cost at most 7,200s). None of them has a guard verdict: `rf1xxr` never started them (`b1mx2w` `## Rollup mutation results`, Reason `budget exhausted at 10833.66s`). Without a verdict nobody knows whether the surviving suite would catch a broken return in any of them, and so whether a deleted test's coverage needs restoring.
- Scope: IN: survivor probe (plus a file-level fallback and a positive control where the rules below require them) for every `P2` key in `## Probe queue` order, under a 10,800s cumulative cap; write the `P2` rows of `## Budget probe results`. OUT: `P3` (Order 03 `f4pbs5`), `P4` (Order 04 `pr6lo9`), filing (Order 05 `b83dpg`), any code or test edit.
- Scope-Paths: .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 2
- Highest E allocated: 03
- Author: opencode
- Id: lictgf

## Workflow history

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Every `P2` key ends `guarded`, `unguarded`, `unprovable` or (only if the cap is hit) `budget-exhausted`, each verdict backed by a saved probe JSON and a preflighted selection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Selections

- [ ] E-01 Record `git rev-parse HEAD` and the Order 01 HEAD from `## Inputs`, and paste `git diff --stat <Order 01 HEAD> HEAD -- agent_workflows tests | tail -1`. Re-derive each `P2` key's reaching node ids at THIS HEAD (the Order 01 scratch is not in this lane): run `python3 tools/replay_coverage_diff.py baseline --out .aw/state/trimprobe-lictgf/base -- -m "not slow and not livecorpus" <the union of the P2 keys' Surviving test files from ## Probe queue>` and paste its stdout, then map each key's contexts to node ids with the same longest-existing-file-prefix rule Order 01 used. A `P2` key absent from this narrowed baseline is NOT concluded unreached (the union is narrower than `tests/`); its node-id selection is empty and it goes straight to the file-level step of E-02.
  - Depends on: none
  - Expected outcome: every `P2` key has a node-id selection (possibly empty) and its committed surviving-file selection.
  - Execution state: pending

### Task group 2: Probes

- [ ] E-02 For each `P2` key in queue order, and only while the cumulative `wall_s` of this plan's probes is at most 10,800s (do not START a key past the cap; every unstarted key gets `budget-exhausted` with the cumulative time): (1) PREFLIGHT the node-id selection with `python3 -m pytest -o addopts= -q --collect-only -p no:randomly -m "not slow and not livecorpus" <node ids>` and record the collected count; pass every selection as EXPLICIT arguments (never an `@argfile`, which collected almost nothing and yielded a false `survived` at authoring, `g00ljy` F-04). (2) SURVIVOR: `python3 tools/mutation_probe.py <key> --op <queue operator> --format json -- [-n 6 when the count exceeds 100] -m "not slow and not livecorpus" <node ids>`. (3) FALLBACK: when the node-id survivor is `survived` or the node-id selection is empty, preflight and re-run the survivor with the key's committed `Surviving test files` instead, since a narrowed selection can omit a test that reaches the key only in a subprocess; the file-level result decides. (4) CONTROL, only when the deciding survivor is `survived` and the queue names a control file: `python3 tools/mutation_probe.py <key> --op <operator> --format json --extra-test 19313eed:<control file> -- <control file>`; with control file `none` the key is `unprovable` with reason `no deleted reaching file`. (5) MAP with the `rf1xxr` E-02 rule: survivor `killed` -> `guarded`; survivor `survived` with control `killed` -> `unguarded`; survivor `killed-by-import` -> one retry with an untried operator from `tools.mutation_probe.OPERATORS` that `apply_operator` accepts, recording both, else `unprovable`; survivor `invalid`/`error`/`timeout`, or control `survived`/`invalid`/`killed-by-import`/`error`/`timeout` -> `unprovable` with the reason. Save every JSON under `.aw/state/trimprobe-lictgf/` and record any non-empty `checkout_status_changed` and `extra_tests_overwrote` in the row. A key's `wall_s` is the sum of all its probe runs.
  - Depends on: E-01
  - Expected outcome: each started key has a final verdict; `git status --short` and `git worktree list` are unchanged across the batch.
  - Execution state: pending

### Task group 3: Record

- [ ] E-03 Append (creating the section if absent) `## Budget probe results` with columns `Key`, `Partition`, `Operator`, `Selection` (`node-ids` or `files`), `Collected`, `Survivor`, `Control`, `Final verdict`, `Reason`, `wall_s`, one row per `P2` key, followed by a `P2` subtotal line (count per final verdict and total `wall_s`). Run `aw research index`, then commit only the doc with `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: one row per `P2` key; one path-scoped commit.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: paste the two HEADs, the `git diff --stat` tail, the narrowed `baseline` stdout, and the count of `P2` keys with a non-empty and with an empty node-id selection.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a scratch script's summary over `.aw/state/trimprobe-lictgf/*.json` listing, per key, every run's `verdict`, `head`, collected count and `wall_s`; confirm no deciding run had a preflight count of 0; paste the cumulative `wall_s`; paste `git status --short` and `git worktree list` before and after the batch showing them unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `P2` subtotal line and a count of `## Budget probe results` rows with Partition `P2` equal to the queue's `P2` count; paste the `aw commit` output and `git show --stat HEAD` listing only the doc.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Order 01 (`g00ljy`) is `executed`. Scope fence: `- Scope-Paths:` declares only this Set's order-01 findings doc; probe JSON lives under the gitignored `.aw/state/trimprobe-lictgf/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc; never record a verdict you did not measure. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
