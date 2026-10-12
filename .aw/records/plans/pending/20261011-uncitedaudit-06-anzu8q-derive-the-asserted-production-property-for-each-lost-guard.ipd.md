# IPD: Derive the asserted production property for each lost-guard candidate the audit surfaced

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` names the step explicitly: "derive asserted properties". Plan `oyh28b` E-05 established why this cannot be skipped: "A MUTATION SUBJECT IS A PRODUCTION BEHAVIOR, NOT A DELETED TEST FILE ... Mutation requires naming the PROPERTY ... and then breaking THAT in production code." Order 05 (`8d0qsg`) produces candidate production functions grouped by key with the deleted tests reaching them, but a function key is not a property: one function can carry several behaviors, and a mutation that breaks the wrong one proves nothing. The uncited files have no comment stating their purpose, so the property must be read from the deleted test's own assertions.
- Scope: IN: for each candidate group in the findings doc's `## Candidates for Order 06` section, read the reaching deleted test functions (`git show 19313eed^:<path>`), state the asserted property in one sentence naming the production symbol, classify it (`behavioral`, `pin-retired` when the only assertion is a code-structure pin per P16, `property-unidentifiable` when the assertions do not determine a checkable behavior), choose a mutation operator from Order 03's set that breaks exactly that property, and for `fail-investigate` groups decide `regression` vs `intended-change` from `git log` of the production symbol since `19313eed`, citing the commit; append all of it to the SAME findings doc as a `## Derived properties` section. Then select the mutation shortlist for Order 07. OUT: running mutants (Order 07), filing items (Order 08), editing any code or test.
- Scope-Paths: .aw/records/research/
- Item-Dependencies: executed:8d0qsg
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 6
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: anzu8q

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Convert each candidate production function into a named, checkable property with a mutation operator that breaks it, plus a regression verdict for every product-caused replay failure, recorded in the audit's findings doc.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Derivation

- [ ] E-01 For every `pass-exclusive` candidate group in the findings doc (created by `8d0qsg`, located with `aw find research uncited-trim-audit` or by its id6 recorded in `8d0qsg`'s V-01), append a row to a `## Derived properties` table: group id `P-NN`, production key, reaching deleted tests (file::name), the property in one sentence ("`<symbol>` returns/raises/writes X when Y"), classification (`behavioral` / `pin-retired` / `property-unidentifiable`, with the asserting line quoted for the latter two), mutation operator (`return-none` / `return-true` / `return-false` / `negate-return` / `raise` / `noop`) with one sentence on why that operator breaks this property, and the baseline reaching-test count and `subprocess_only` flag from Order 04's data. Record the rule "a group whose property cannot be named is `property-unidentifiable` and is NOT mutated", per `oyh28b` E-05 step 2.
  - Depends on: none
  - Expected outcome: every `pass-exclusive` group has exactly one row with a classification and, if `behavioral`, an operator.
  - Execution state: pending

- [ ] E-02 For every `fail-investigate` group, append a `## Replay failures` table row: failing nodeids, the assertion message, the production symbol, `git log --oneline 19313eed..HEAD -- <module path>` commits that touched it, and a verdict `regression` (behavior changed with no recorded intent; cite the commit) or `intended-change` (cite the plan/backlog id6 or commit message stating the change). A group with no explaining commit is `regression`.
  - Depends on: none
  - Expected outcome: every `fail-investigate` file accounted for with a cited verdict.
  - Execution state: pending

### Task group 2: Shortlist

- [ ] E-03 Select the Order 07 shortlist and record it as a `## Mutation shortlist` section: all `behavioral` groups ranked by exclusive line count descending, then ties by number of reaching deleted test functions; budget each by estimated cost (narrowed selection: reaching tests only, estimated from their count; `subprocess_only` or zero reaching tests: full default selection, about 200 s each), and cap the shortlist at 40 probes or 3 hours of estimated wall time, whichever is smaller. List the remainder as `triaged-not-mutated` with the cap as the stated reason. Also record, for each shortlisted group, the POSITIVE CONTROL: the deleted test path Order 07 will pass via `--extra-test` to show the mutant is killable. Run `aw research index` and commit via `aw commit <this plan> -- .aw/records/research/`.
  - Depends on: E-01, E-02
  - Expected outcome: shortlist and remainder present with the cap stated; index conforms; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 forbids restoring or proposing code-structure pins (`GUIDING_PRINCIPLES.md` Section 16); a pin-only property is recorded `pin-retired`, never mutated or filed for restoration (`oyh28b` E-05 step 3).
- Mutation subjects are production behaviors, not test files (`oyh28b` E-05, PR-008).
- A budget is a measurement, not a preference: one bare-suite selection is ~200 s here (bare run at `fca848304`: `201.44s`), so an unbounded mutation pass is not affordable (`oyh28b` F-06).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Function keys need a property statement before mutation. | `oyh28b` E-05 "A MUTATION SUBJECT IS A PRODUCTION BEHAVIOR"; `oyh28b` recorded `property-unidentifiable` as a legitimate outcome. |
| F-02 | Uncited files carry no comment describing their purpose; the deleted assertions are the only source. | Definition of the uncited partition (`compute_reach_partition` in `tools/lost_guard_census.py`). |
| F-03 | Narrowed mutation runs are much cheaper than the ~200 s bare selection when coverage names the reaching tests. | `sk2rbf` F-03; per-file pytest startup ~0.4 s (`nzzu8n` F-04). |

## Proposed changes (ordered, validatable)

1. Derived properties for `pass-exclusive` groups (E-01).
2. Regression verdicts for `fail-investigate` groups (E-02).
3. Budgeted mutation shortlist with positive controls (E-03).

## Deferred / out of scope (with reason)

- Running the shortlisted mutants: Order 07 (`rq3q7v`).
  - Carrier: rq3q7v
- `pass-shared` groups: the surviving suite reaches every line these deleted tests reached; whether it ASSERTS on them is a mutation question, but with no exclusive reach they are lower yield than `pass-exclusive`. They are listed in `triaged-not-mutated` if they do not fit the cap.
  - Carrier: rq3q7v

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `aw research index --check` conforms after E-03.
- Every `pass-exclusive` and `fail-investigate` group from the `## Candidates for Order 06` section is accounted for.

## Spec / documentation sync

N/A: research record only.

## Open questions

### OQ-01: Is a 40-probe / 3-hour cap right?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: It is a budget, recorded with its reason, and Order 08 files the remainder rather than dropping it; `oyh28b` used a five-candidate cap on a full-suite cost basis, and coverage narrowing (Order 04) is what makes a larger cap affordable here. A reviewer may change the number without changing the design.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: count of `## Derived properties` rows equal to the count of `pass-exclusive` groups in `## Candidates for Order 06` (paste both counts), counts per classification, and three pasted example rows including one non-`behavioral` with its quoted assertion line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: count of `## Replay failures` rows equal to the `fail-investigate` count, and every `regression` row's cited commit pasted with its one-line `git log` entry.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted shortlist header with probe count and estimated wall time under the cap, the `triaged-not-mutated` count, pasted `aw research index --check` and `git show --stat HEAD` listing only `.aw/records/research/` paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: no code or test edits; commit only `.aw/records/research/` through `aw commit <plan> -- .aw/records/research/`; never push. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
