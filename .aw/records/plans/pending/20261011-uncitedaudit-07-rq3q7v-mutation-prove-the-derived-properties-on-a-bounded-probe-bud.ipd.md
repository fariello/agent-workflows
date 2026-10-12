# IPD: Mutation-prove the derived properties on a bounded probe budget

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` asks to "mutation-prove surviving coverage". After Order 06 (`anzu8q`), each shortlisted property has a production symbol, an operator, a reaching-test selection and a positive control, but no proof. A property counts as guarded only if breaking it makes a SURVIVING test fail (`GUIDING_PRINCIPLES.md` Section 16, "A test is only valid if breaking the underlying behavior makes the test fail"), and a `survived` verdict is only meaningful if the same mutant is killable at all, which is what the positive control (the deleted test re-added in the probe worktree) shows.
- Scope: IN: for each shortlisted property, run `tools/mutation_probe.py` (Order 03) twice: SURVIVOR run with the narrowed selection (reaching tests from Order 04, or the full default selection when `subprocess_only` or no reaching tests), and CONTROL run adding `--extra-test 19313eed:<deleted path>` with the deleted test as the only selection; record verdicts `guarded` (survivor killed), `unguarded` (survivor survived, control killed), `unprovable` (control also survived or `invalid`: the operator does not break what the deleted test asserted; record and do not file), `import-only` (`killed-by-import`; rerun once with a different operator, else `unprovable`). Append a `## Mutation results` table to the findings doc. OUT: filing items (Order 08); editing code or tests.
- Scope-Paths: .aw/records/research/
- Item-Dependencies: executed:g55j1e, executed:anzu8q
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 7
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: rq3q7v

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Give each shortlisted property a controlled, reproducible mutation verdict (`guarded` / `unguarded` / `unprovable` / `import-only`) recorded with the exact probe commands and outputs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Probe

- [ ] E-01 Record the probe environment: HEAD sha, `git worktree list` and `git status --short` of the invoking checkout, and a bare `python3 -m pytest` summary line as the suite baseline, in a `## Mutation environment` section of the findings doc.
  - Depends on: none
  - Expected outcome: environment section with HEAD and the pasted baseline summary.
  - Execution state: pending

- [ ] E-02 For each `## Mutation shortlist` row (from `anzu8q`), run the SURVIVOR and CONTROL probes with `python3 tools/mutation_probe.py <key> --op <operator> --format json [...] -- <selection>` (control: `--extra-test 19313eed:<deleted path> -- <wt-relative deleted path>`), saving JSON under a temp dir; assign the verdict per the Scope's rules; append one `## Mutation results` row per property: `P-NN`, key, operator, survivor verdict with baseline/mutated fail counts and up to 3 newly failing nodeids, control verdict, final verdict, wall time. Stop adding probes when cumulative wall time exceeds the cap `anzu8q` E-03 recorded, and move unprobed rows to `triaged-not-mutated` with the reason `budget exhausted at <time>`.
  - Depends on: E-01
  - Expected outcome: every shortlisted property has a final verdict or is in `triaged-not-mutated` with a reason; `git status --short` outside `.aw/records/research/` and `git worktree list` unchanged after the batch.
  - Execution state: pending

### Task group 2: Record

- [ ] E-03 Add a `## Mutation totals` table (counts per final verdict, total wall time), run `aw research index`, and commit via `aw commit <this plan> -- .aw/records/research/`.
  - Depends on: E-02
  - Expected outcome: totals reconcile with the shortlist count; index conforms; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Never edit tracked files of the shared checkout for an experiment; the probe isolates each mutant in a disposable worktree (`g55j1e` Concern; `AGENTS.md` "Shared checkout").
- Baseline failures are subtracted, never credited (`g55j1e` F-03: 38 nodes failing at `fca848304`).
- An unproven tail is reported as `triaged-not-mutated` with its reason, an honest partial (`oyh28b` E-05).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | A `survived` verdict without a positive control cannot distinguish "unguarded" from "operator does not break the property". | Mutation semantics; `g55j1e` E-02 tests the `--extra-test` positive-control case for exactly this reason. |
| F-02 | Full default selection costs ~200 s per run. | Bare run at `fca848304`: `201.44s`. |

## Proposed changes (ordered, validatable)

1. Environment and suite baseline (E-01).
2. Survivor and control probes per property within budget (E-02).
3. Totals, index, commit (E-03).

## Deferred / out of scope (with reason)

- Filing `unguarded` properties and `regression` replay failures: Order 08 (`xmr5qj`).
  - Carrier: xmr5qj
- Writing replacement tests: a per-gap deliverable of the items Order 08 files.
  - Carrier: xmr5qj

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- Every probe JSON's `verdict` matches its table row.
- `git status --short` and `git worktree list` unchanged across the batch.
- `aw research index --check` conforms.

## Spec / documentation sync

N/A: research record only.

## Open questions

### OQ-01: What if the suite baseline at execution differs from authoring?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The probe computes its own baseline per run inside the worktree (`g55j1e` E-01), so a drifted baseline changes nothing about verdict validity; E-01 records the bare-suite figure only for context.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `## Mutation environment` section including the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: two pasted probe JSON outputs (produced by `tools/mutation_probe.py` `main`) for one `unguarded` row (survivor `survived`, control `killed`) and one `guarded` row, or a statement that a class did not occur; pasted `git status --short` and `git worktree list` from before and after the batch.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `## Mutation totals` table summing to the shortlist count, pasted `aw research index --check`, and `git show --stat HEAD` listing only `.aw/records/research/` paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: no code or test edits; every mutant runs only inside `tools/mutation_probe.py`'s disposable worktree; commit only `.aw/records/research/` through `aw commit <plan> -- .aw/records/research/`; never push. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
