# IPD: Mutation-probe the subprocess-only budget-exhausted keys

- Date: 2026-10-17
- Kind: child
- Concern: 25 of backlog `lrnh5f`'s 319 keys were `subprocess-only` at `86f0d88d` (`b1mx2w` `## Key reach`): a test reaches them only inside a child process, so coverage records their lines with no test context and nothing says WHICH test file to select. `rf1xxr` planned to probe them with the full non-slow `tests/` selection and never started them. They include the git hook entry points (`hooks/ipd_dependency_statement_gate.py::main`/`check`/`_staged_ipd_overlay`, `hooks/prepush_authorization_gate.py::main`/`check`, `hooks/status_untooled_gate.py::main`/`check`), CLI leaves (`run_analytics_cli.py::run_export_leaf`/`run_submit_leaf`, `cli.py::_run_storage_init`, `run_cli.py::_run_decisions`/`_run_questions`) and the companion-storage helpers in `storage.py`. Order 01 (`g00ljy`) puts every key still `subprocess-only` at the current HEAD into partition `P4`.
- Scope: IN: for every `P4` key, a narrowed survivor over the test files that name the key's module, a positive control, and a full-selection fallback survivor while the 10,800s cap allows; write the `P4` rows of `## Budget probe results`. OUT: `P2`/`P3` (Orders 02 `lictgf`, 03 `f4pbs5`), filing (Order 05 `b83dpg`), any code or test edit.
- Scope-Paths: .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy, executed:f4pbs5
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 4
- Highest E allocated: 03
- Author: opencode
- Id: pr6lo9

## Workflow history

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Every `P4` key ends `guarded`, `unguarded`, `unprovable` or `budget-exhausted` with a reason that says which selection decided it, without claiming `unguarded` from a selection that may simply have missed the subprocess test.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Selections

- [ ] E-01 Confirm `## Budget probe results` holds the `P2` and `P3` rows (paste both counts). For each `P4` key, build its CANDIDATE selection as the test files under `tests/` whose text contains the key's module stem as a whole word (`rg -l -w <stem> tests/`; for `hooks/<name>.py` use `<name>`), and paste the file count per key. Preflight each with `python3 -m pytest -o addopts= -q --collect-only -p no:randomly -m "not slow and not livecorpus" <files>` and record the collected count. A key with an empty or zero-collecting candidate selection skips the narrowed survivor and goes to the fallback in E-02.
  - Depends on: none
  - Expected outcome: every `P4` key has a candidate selection and a preflight count (possibly 0).
  - Execution state: pending

### Task group 2: Probes

- [ ] E-02 For each `P4` key in `## Probe queue` order while the cumulative `wall_s` is at most 10,800s (an unstarted key is `budget-exhausted` with the cumulative time): (1) NARROWED SURVIVOR: `python3 tools/mutation_probe.py <key> --op <queue operator> --format json -- [-n 6 when the count exceeds 100] -m "not slow and not livecorpus" <candidate files>`, explicit arguments only (`g00ljy` F-04). `killed` -> `guarded` (a kill is proof whatever the selection). (2) If `survived` or skipped: CONTROL with the queue's control file exactly as Order 02 E-02 step 4 (`none` -> `unprovable`, reason `no deleted reaching file`; control not `killed` -> `unprovable` with the reason). (3) If the control `killed`: FALLBACK SURVIVOR over `-n 6 -m "not slow and not livecorpus" tests/` with `--timeout 3600`, started only if the cumulative `wall_s` plus the first fallback's measured cost (or 4,000s before any fallback has run) stays within the cap; fallback `killed` -> `guarded`, `survived` -> `unguarded`, otherwise `unprovable`. If the cap forbids the fallback the key is `budget-exhausted` with reason `narrowed survivor survived, control killed, full fallback not run`, which Order 05 carries forward rather than treating as `unguarded`. Save every JSON under `.aw/state/trimprobe-pr6lo9/`; record non-empty `checkout_status_changed` and `extra_tests_overwrote`.
  - Depends on: E-01
  - Expected outcome: each started key has a final verdict whose reason names the deciding selection; `git status --short` and `git worktree list` unchanged.
  - Execution state: pending

### Task group 3: Record

- [ ] E-03 Append to `## Budget probe results` (Order 02 columns; `Selection` is `candidate-files` or `tests/`) one row per `P4` key and a `P4` subtotal line. Run `aw research index`, then commit only the doc with `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: one row per `P4` key; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A `subprocess-only` key has lines measured only through `coverage`'s `patch = subprocess` with empty dynamic contexts (`tools.replay_coverage_diff._make_rc_content`, `tools.replay_coverage_diff._function_coverage` sets `subprocess_only` when contexts are empty), so its reaching test file cannot be read from coverage.
- `tools/mutation_probe.py` defaults to a 1800s per-run `--timeout`; the full non-slow `tests/` selection is about 9,000 tests, so the fallback raises it.
- Mapping rules are `rf1xxr` E-02's, with one deliberate refinement: a narrowed `survived` never maps to `unguarded` by itself, because the selection is a guess.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results`, `subprocess-only` budget-exhausted rows | 25 keys across 12 modules; operators 23 `return-none`, 2 `raise`. |
| F-02 | Authoring, HEAD `476c7b7bd`: `rg -l -w <module stem> tests/` per key | Candidate counts range from 1 file (`migration_inventory`, `run_analytics_export`) to 179 (`cli`); the three hook modules each match 1 file by module name. |
| F-03 | `g00ljy` F-03 (calibration) | About 0.48s per collected test at `-n 6` for baseline plus mutant, so a full `tests/` fallback costs on the order of 4,000s and the cap affords at most two; most keys must be decided by the narrowed survivor or control. |

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

- [ ] V-01 validates E-01
  - Required evidence: paste the `P2`/`P3` row counts, and per `P4` key the candidate file count and preflight collected count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a summary over `.aw/state/trimprobe-pr6lo9/*.json` listing per key each run's selection kind, `verdict`, `head` and `wall_s`; show that no `unguarded` row rests on anything but a `tests/` fallback `survived`; paste the cumulative `wall_s`; paste `git status --short` and `git worktree list` before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `P4` subtotal line and a row count equal to the queue's `P4` count; paste the `aw commit` output and `git show --stat HEAD` listing only the doc.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 (`g00ljy`) and 03 (`f4pbs5`) are `executed`, so this plan appends after the `P2` and `P3` rows. Scope fence: `- Scope-Paths:` declares only this Set's order-01 findings doc; probe JSON lives under the gitignored `.aw/state/trimprobe-pr6lo9/`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
