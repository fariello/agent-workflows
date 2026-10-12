# IPD: File each unguarded or regressed property as grouped backlog items

- Date: 2026-10-11
- Kind: child
- Concern: An audit that ends in a findings doc leaves its gaps invisible to `aw attention`, which reads backlog, plans and specs but not research prose (`AGENTS.md` "What needs attention": "Do NOT keep committed backlog only in prose"). Orders 05 to 07 produce `unguarded` properties, `regression` replay failures, and a `triaged-not-mutated` tail; each needs a tracked carrier or the audit retires the question without answering it, the exact failure plan `oyh28b` warned of ("a census that runs clean and files nothing ... would retire the question").
- Scope: IN: file one backlog item per ROOT-CAUSE GROUP (same production module plus same remedy shape: restore a behavioral test, or fix a regression) with `aw backlog new`, naming every property `P-NN` and deleted test it covers; file ONE rollup item enumerating the `triaged-not-mutated` and `property-unidentifiable` remainder if non-empty; cap at 10 grouped items plus the rollup (remaining groups go into the rollup by name); justify each `- Work-Kind:` (`chore` for an absent test by default; `bug` with `- Blocks-Release: next` when Order 06 recorded `regression` with user-visible wrong behavior, per the repository's gating rule); record every filed id6 and a final reconciliation in the findings doc; dedupe against live items before filing. Also verify, as the Set's whole-Set checks, that every inventory file has a verdict and every non-`guarded` outcome has a carrier, and that the Set left no code or test change outside the three tool files and their tests. OUT: writing replacement tests or fixing regressions (each filed item's own work); changing backlog `e486tz`'s status.
- Scope-Paths: .aw/records/backlog/, .aw/records/research/
- Item-Dependencies: executed:rq3q7v
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 8
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xmr5qj

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Turn every non-guarded audit outcome into a tracked, grouped backlog carrier and prove, by reconciliation, that no uncited file and no outcome was dropped.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Dedupe and file

- [ ] E-01 Group every `unguarded` property (Order 07) and every `regression` replay failure (Order 06 `## Replay failures`) by (production module, remedy shape). For each group, search live items for the module and deleted test names (`aw find backlog <module>`, and `grep -rln "<deleted test basename>" .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked`); OPEN any hit and record whether it actually covers the group (`owned-confirmed` / `owned-rejected`). Write a `## Filing plan` section listing each group, its dedupe judgement, its intended work-kind with a one-sentence justification, and whether it is filed or rolled up.
  - Depends on: none
  - Expected outcome: every unguarded and regression outcome appears in exactly one group with a dedupe judgement.
  - Execution state: pending

- [ ] E-02 File each non-owned group, top 10 by (regressions first, then exclusive line count), with `aw backlog new --summary "<...>" --work-kind <chore|bug> [--blocks-release next] --body "<properties P-NN, deleted tests, mutation verdicts, findings doc id6>" --apply`, pasting each output; then, if any group is beyond the cap or any row is `triaged-not-mutated` / `property-unidentifiable` / `unprovable`, file ONE rollup item enumerating them by `P-NN` and file path. Record each filed id6 in the findings doc's `## Filed items` section.
  - Depends on: E-01
  - Expected outcome: at most 10 grouped items plus at most one rollup, each with pasted creation output; every `bug` carries `- Blocks-Release: next`.
  - Execution state: pending

### Task group 2: Whole-Set reconciliation

- [ ] E-03 Write a `## Reconciliation` section in the findings doc: (a) inventory file count equals the sum of `## Verdict totals` (Order 05); (b) every `pass-exclusive` group has a derived-property row (Order 06); (c) every `behavioral` property is in `## Mutation results` or `triaged-not-mutated` (Order 07); (d) every outcome other than `guarded`, `pin-retired`, `recreated`-with-full-name-overlap, `subject-retired`, `api-moved`-with-surviving-coverage, `pass-shared`-guarded, `no-product-reach` and `intended-change` names a carrier id6 from E-02 or an `owned-confirmed` live item; (e) `git diff --name-only <Set base>..HEAD -- agent_workflows tests tools` lists only the eight files Orders 01 to 04 declared (`tools/lost_guard_census.py`, `tests/test_lost_guard_census.py`, `tools/deleted_test_replay.py`, `tests/test_deleted_test_replay.py`, `tools/mutation_probe.py`, `tests/test_mutation_probe.py`, `tools/replay_coverage_diff.py`, `tests/test_replay_coverage_diff.py`) plus `tools/README.md`, where `<Set base>` is the parent of `1ub8ex`'s first commit (`git log --format=%H --grep 1ub8ex | tail -1`).
  - Depends on: E-02
  - Expected outcome: all five reconciliation checks pass with pasted numbers, or each failure is named with its fix applied in this pass.
  - Execution state: pending

- [ ] E-04 Run `aw research index`, `aw backlog check` and `aw check`, then commit via `aw commit <this plan> -- .aw/records/backlog/ .aw/records/research/`, after confirming `git diff --cached --name-only` lists only the new backlog items and the findings doc/index.
  - Depends on: E-03
  - Expected outcome: index and checks conform (or only pre-existing findings unrelated to this Set remain, pasted with their rule ids); one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Committed backlog lives in `records/backlog/`, created with `aw backlog new`, never in prose (`AGENTS.md` "What needs attention").
- Group by root cause, not one item per citation (`oyh28b` E-07: "DO NOT FILE 43 SEPARATE ITEMS. Group by ROOT CAUSE").
- Work-kind is a judgement recorded with evidence: an absent test is `chore` by default; user-perceptible wrong behavior is `bug` and must carry `- Blocks-Release:` while live (`AGENTS.md` "Every live bug gates the next release").
- Retired code pins are never filed for restoration (P16; `oyh28b` "TWO REFUSALS ARE ABSOLUTE").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Research prose is invisible to `aw attention`. | `AGENTS.md` "What needs attention": the view maps backlog, plans and specs; "Do NOT keep committed backlog only in prose". |
| F-02 | The predecessor audit capped filing at eight plus a rollup to keep the queue readable. | `oyh28b` E-07 "file at most EIGHT items in this pass ... and ONE further item that enumerates the remaining groups". |
| F-03 | Basename dedupe both over- and under-matches, so owned claims must be opened. | `oyh28b` F-20 and E-07 "OPEN the named item and confirm it actually covers this citation". |

## Proposed changes (ordered, validatable)

1. Group and dedupe (E-01).
2. File grouped items and the rollup (E-02).
3. Whole-Set reconciliation (E-03).
4. Checks and commit (E-04).

## Deferred / out of scope (with reason)

- Writing replacement behavioral tests and fixing regressions: each filed item is its own unit of work and graduates separately.
  - Carrier-Declined: The obligation travels with the items E-02 files; a single carrier for all of them would duplicate those items.
- Closing backlog `e486tz`: the runner sets it `graduated` when this Set is authored; it closes `done` through the normal backlog close after the Set executes.
  - Carrier-Declined: Lifecycle step owned by the runner and `aw backlog set`, not by this plan.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `aw backlog check` and `aw check` after filing.
- Reconciliation checks (a) to (e) pass with pasted numbers.

## Spec / documentation sync

N/A: backlog and research records only.

## Open questions

### OQ-01: Should a `regression` be filed `bug` automatically?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Per the repository's user-perceptible-impact test, `bug` requires that the changed behavior is visible to a user; E-01 records that judgement with its evidence per group. A regression in an internal helper with no user-visible effect is `chore`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `## Filing plan` table, with every `owned-*` judgement naming the item id6 opened and one sentence on what it covers.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw backlog new ... --apply` output for every filed item and the rollup, and `aw find backlog <id6>` for one `bug` item showing `- Blocks-Release: next` (or a statement that no group was filed `bug`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `## Reconciliation` section with the numbers for (a) to (d) and the pasted `git diff --name-only` output for (e).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `aw research index --check`, `aw backlog check`, `aw check` outputs, the pasted `git diff --cached --name-only` before commit, and the `aw commit` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: no code or test edits; commit only `.aw/records/backlog/` and `.aw/records/research/` through `aw commit <plan> -- <paths>`; never `git add -A`, never push. Do not change backlog `e486tz`'s status. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
