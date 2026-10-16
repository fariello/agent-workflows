# IPD: Mutation-probe the reached rollup properties on a bounded budget

- Date: 2026-10-16
- Kind: child
- Concern: The 747 rollup keys (backlog `9qvfie` outcome 2) were never mutation-probed: `rq3q7v` spent its budget (3466.82s) on two full-default-selection survivor runs (`hpjj44` `## Mutation totals`). A key's guard status follows from its `hpjj44` classification or its reach class (Order 03 `8dyt88` `## Key reach`) for four classes and needs a probe for the rest: an `unreached` key cannot be guarded by the routine non-slow selection, since no test in that selection executes it (in-process or in a traced subprocess), so any mutant of it survives that selection by construction; a `reached` key may or may not be guarded, and only a probe with a positive control decides. Probing with a NARROWED selection (the surviving test files whose contexts reach the key) costs seconds rather than the ~1600s a full-selection survivor took.
- Scope: IN: assign every key a final verdict from its reach class and `hpjj44` classification without a probe where the class decides it (`pin-retired`, `property-unidentifiable`, `key-gone`, `unreached`); probe `reached` keys (and then `subprocess-only` keys with the explicit full non-slow `tests/` selection, budget permitting) with `tools/mutation_probe.py`, survivor plus positive control, in descending `hpjj44` exclusive-line order until a 10,800s cumulative cap; write `## Rollup mutation results` and totals. OUT: filing (Order 06 `z2xs98`); code or test edits.
- Scope-Paths: .aw/records/research/*-trimcarry-01-*.findings.md
- Item-Dependencies: executed:8dyt88
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 5
- Highest E allocated: 03
- Author: opencode
- Id: rf1xxr

## Workflow history
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Replace "triaged, not mutated" with a final verdict for as many of the 747 keys as a bounded budget allows, and an explicit reason for every key it does not reach.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Verdicts that need no probe

- [ ] E-01 Record `git rev-parse HEAD` and the `head` Order 03 recorded in `## Baseline`, and paste `git diff --stat <Order 03 head> HEAD -- agent_workflows tests`. Derive the key set from COMMITTED sources only (Order 03's `keys.txt` and `baseline.json` live under the gitignored `.aw/state/` and are NOT present in this plan's isolated worktree): the `production-key` rows of `hpjj44` `## Triaged not mutated` (747) must equal the `Key` column of `## Key reach`. For each of the 747 keys, take `Classification` and `Mutation Operator` from `hpjj44` `## Derived properties` and `Reach class` from the Set doc's `## Key reach`, and assign without probing, in this order: `pin-retired` (Classification `pin-retired`; carrier-free per `hpjj44` reconciliation (d)); `property-unidentifiable` (Classification `property-unidentifiable`; operator `n/a`); `key-gone` (reach class `key-gone`; the subject no longer exists at HEAD); `unguarded-unreached` (reach class `unreached`: no test in the routine non-slow selection executes the function, in-process or in a traced subprocess, so none can kill a mutant of it; the `Reason` cell MUST say "unreached by the non-slow selection at <Order 03 head>", because `slow`/`livecorpus` tests were excluded from the measurement (`8dyt88` `## Method`)). If the pasted diff is non-empty, every `key-gone` or `unguarded-unreached` key whose module file appears in it is instead `to-probe` (its reach class is stale), and the changed `tests/` paths are listed under the table as a caveat for Order 06. Every remaining key is `to-probe`. Write the `## Rollup mutation results` header table (`Key`, `Operator`, `Reach class`, `Final verdict`, `Reason`, `Survivor`, `Control`, `wall_s`) with these rows filled.
  - Depends on: none
  - Expected outcome: every key has a row; the non-probe classes are final; the `to-probe` set is listed in `hpjj44` exclusive-line order (`reached` keys first, then `subprocess-only`).
  - Execution state: pending

### Task group 2: Budgeted probes

- [ ] E-02 For each `to-probe` key in order, until the cumulative `wall_s` of this batch exceeds 10,800s (the cap `hpjj44` `## Mutation shortlist` used): (1) SELECTION: for `reached`, `-m "not slow and not livecorpus"` plus the surviving test files from `## Key reach` (the same marker filter the reach was measured under); for `subprocess-only`, `-n auto -m "not slow and not livecorpus" tests/`. Do NOT omit the `--` selection: the probe's no-argument default (`-n auto -m "not slow and not livecorpus"`, `tools/mutation_probe.py` `probe`) names no path, so pytest falls back to `pyproject.toml` `testpaths`, which is a 19-module core list (707 tests collected at review versus 9195 for `tests/`), and a survivor on that subset would yield a false `unguarded`. (2) PREFLIGHT every selection with `python3 -m pytest -o addopts= -q --collect-only <the exact selection arguments of step 1>` (exit 0, at least one test collected; a key with no collectable selection is `unprovable` with reason `empty selection`), since a selection that collects nothing still yields a valid empty junit file and a false `survived` (`rq3q7v` F-03). (3) SURVIVOR: `python3 tools/mutation_probe.py <key> --op <operator> --format json -- <selection>`. (4) CONTROL: `python3 tools/mutation_probe.py <key> --op <operator> --format json --extra-test 19313eed:<deleted reaching file> -- <deleted reaching file>`, taking the deleted file with the most exclusive lines from `hpjj44` `## Derived properties` `Reaching Test Files` (when that path exists again at HEAD, restored by Orders 01/02 or one of the 4 recreated files, the probe overwrites it with the `19313eed^` blob and lists it in `extra_tests_overwrote`; record that in the row). Run the control only when the survivor is `survived`. (5) MAP with the `rq3q7v` rule: survivor `killed` -> `guarded`; survivor `survived` with control `killed` -> `unguarded`; survivor `killed-by-import` -> rerun survivor (and control if needed) once with an operator from the tool's `OPERATORS` that this key has not tried and that `apply_operator` accepts (an `invalid` verdict means it does not), recording both attempts, else `unprovable`; survivor `invalid`/`error`/`timeout`, or control `survived`/`invalid`/`killed-by-import`/`error`/`timeout` -> `unprovable` with the reason. Save each JSON under the gitignored `.aw/state/trimcarry-rf1xxr/`, and record any non-empty `checkout_status_changed` in the row. A key's `wall_s` is its survivor plus control (plus retry) `wall_s`. Do not START a key once the cumulative `wall_s` exceeds the cap; every key not started gets `budget-exhausted` with the cumulative time.
  - Depends on: E-01
  - Expected outcome: each probed key has a final verdict; no `unguarded` rests on a selection that failed preflight or on the bare `testpaths` default; `git status --short` and `git worktree list` unchanged after the batch.
  - Execution state: pending

### Task group 3: Totals and commit

- [ ] E-03 Write `## Rollup mutation totals`: count per final verdict (`pin-retired`, `property-unidentifiable`, `key-gone`, `unguarded-unreached`, `guarded`, `unguarded`, `unprovable`, `budget-exhausted`) summing to 747, total probe `wall_s`, and a per-module table of non-`guarded`, non-carrier-free keys for Order 06's grouping. Run `aw research index`, then commit only the doc: `aw commit <this plan> -- <doc path>`.
  - Depends on: E-02
  - Expected outcome: totals sum to 747; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tools/mutation_probe.py` CLI: `target` as `<path.py>::<qualname>`, `--op {return-none,return-true,return-false,negate-return,raise}`, `--extra-test COMMIT:PATH` (reads `COMMIT^:PATH`), `--timeout`, `--format json`, pytest selection after `--`; with no selection it uses `-n auto -m "not slow and not livecorpus"`. It mutates committed HEAD in a disposable worktree and reports `checkout_status_changed`.
- Survivor/control/mapping rules and the preflight are the ones executed plan `rq3q7v` used (its Scope and E-02 steps 1 to 6), so verdicts are comparable with `hpjj44`.
- Operators in `hpjj44` `## Derived properties` for the 747 keys are `return-none` 616, `raise` 81, `negate-return` 23, `return-false` 19, `n/a` 8 (review count; the 8 `n/a` are exactly the 5 `pin-retired` and 3 `property-unidentifiable` keys).
- The probe runs pytest with `-o addopts=` plus the given selection; with NO selection its default names no path, so pytest uses `pyproject.toml` `testpaths` (a 19-module core list since `ad9213cc6`). Measured at review HEAD `5cf4fb46a`: `--collect-only -m "not slow and not livecorpus"` -> `707/712 tests collected`; the same with `tests/` -> `9195/9494 tests collected`. Every selection in this plan is therefore explicit.
- Measured at review: `python3 tools/mutation_probe.py agent_workflows/ipd_lifecycle.py::_scope_match --op return-false --format json -- -n 2 -m "not slow and not livecorpus" tests/test_scope_match.py` -> `"verdict": "killed"`, `"newly_failing_total": 2`, `"checkout_status_changed": []`, `"wall_s": 11.46`; `git status --short` empty and `git worktree list` count unchanged (14) before and after.
- Order 03's scratch (`.aw/state/trimcarry-8dyt88/`) is gitignored (`.aw/.gitignore` `/state/`), so it does not reach this plan's isolated worktree; only the committed findings doc carries Order 03's results.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | No rollup key was probed; the whole prior budget went to two full-selection survivors (1600.47s and 1866.35s). | `hpjj44` `## Mutation results` rows `PROP-01`, `PROP-02`; `## Mutation totals` 3466.82s. |
| F2 | A narrowed control run cost 17.26s in `rq3q7v`. | `rq3q7v` V-02 pasted control JSON `"wall_s": 17.26`. |
| F3 | At derivation 263 of the 747 keys had surviving contexts; Order 03 re-measures this at HEAD. | `8dyt88` F2. |
| F4 | 5 keys are `pin-retired` and 3 `property-unidentifiable`, all inside the 747. | Authoring join of `## Derived properties` classification with `## Triaged not mutated`. |

## Proposed changes (ordered, validatable)

1. Non-probe verdicts (E-01).
2. Budgeted survivor plus control probes (E-02).
3. Totals and commit (E-03).

## Deferred / out of scope (with reason)

- Keys left `budget-exhausted`: Order 06 files them as one grouped item naming this section.
  - Carrier: z2xs98
- Raising the 10,800s cap: a cost decision for the maintainer; the cap matches `hpjj44`'s.
  - Carrier-Declined: deliberate non-goal; the residue stays tracked through Order 06.

## Scope check

- Over-scope: none.
- Under-scope: none; every one of the 747 keys ends with a verdict or `budget-exhausted`.

## Required tests / validation

No tests are authored. Validity is checked by V-01..V-03 (row count 747, preflight passed for every narrowed `unguarded`, totals reconcile).

## Spec / documentation sync

N/A: research record only.

## Open questions

### OQ-01: Is `unguarded-unreached` a sound verdict without a probe?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes, for the routine non-slow selection: a key absent from the baseline's `functions` has no line hit by that selection at all, in-process or in a subprocess (the baseline traces subprocesses, `tools/replay_coverage_diff.py` `_make_rc_content` `patch = subprocess`; lines hit with no test context are the separate `subprocess_only` class, which this plan probes). The residual hole is the excluded `slow`/`livecorpus` tests, so the verdict's reason names the selection and Order 06 must read it as "unguarded by the routine gate", not "unguarded by any test". The positive control is skipped for these keys, so the verdict says "unguarded" without proving the operator is killable; Order 06's filed item restores a test and proves the kill there.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git rev-parse HEAD`, Order 03's recorded head, and the `git diff --stat` from E-01; pasted output of a `python3 -c` check that `## Rollup mutation results` has 747 distinct keys equal to both the `production-key` rows of `hpjj44` `## Triaged not mutated` and the `Key` column of `## Key reach`; pasted counts for the four non-probe classes and the `to-probe` count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for one `guarded` and one `unguarded` row (or a statement that a class did not occur), the pasted survivor and control JSONs produced by `tools/mutation_probe.py` `main`, with the `unguarded` row's collect-only preflight line and its selection showing an explicit path argument; pasted `python3 -c` check over all saved JSONs that every row's survivor/control verdicts match its JSON and every JSON `head` is the same HEAD; pasted `git status --short` and `git worktree list` before and after the batch.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `## Rollup mutation totals` with the sum shown as 747; pasted `aw commit` output and `git show --stat HEAD` listing only the findings doc.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Order 03 (`8dyt88`) is `executed` and its doc carries `## Key reach`. Every mutant runs only inside `tools/mutation_probe.py`'s disposable worktree; probe JSON goes under the gitignored `.aw/state/`. Scope fence: `- Scope-Paths:` declares only the Set's findings doc; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command whose numbers enter the doc; never record a verdict you did not run. Commit only the doc through `aw commit <plan> -- <doc path>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
