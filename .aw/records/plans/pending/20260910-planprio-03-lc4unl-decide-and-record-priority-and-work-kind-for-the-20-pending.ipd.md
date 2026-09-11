# IPD: Decide and record Priority and Work-Kind for the pending plans with no source item

- Date: 2026-09-10
- Kind: child
- Concern: The pending plans that carry no resolvable `- From-Backlog:` cannot inherit `Priority` and `Work-Kind` from a source, so sibling 02's mechanical backfill leaves them empty. Without a value they stay unprioritized on the board, and they are disproportionately the plans with no backlog origin, which may be exactly the ones most needing triage.
- Scope: Assign both fields to every pending plan sibling 02 could not reach, using a SECOND derivation route where one exists (a child inheriting from its Set orchestrator) and a single human decision list for the genuine remainder. Writes through the shipped `aw ipd set` setters only. Does NOT touch any plan sibling 02 handled, does NOT edit terminal plans, and does NOT change any vocabulary.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: executed:lkexaw
- Status: to-review
- Set: planprio
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: lc4unl

## Workflow history

- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after the maintainer chose the full option on 2026-09-10 including "decide the 20". THE TITLE SAYS "the pending plans" RATHER THAN "the 20" DELIBERATELY, because the count was already stale when this was written: measured at authoring the population is 24, not 20, and four of those are this very Set's own plans (`d0cbt3`, `lkexaw`, `8u6770`, `lc4unl`), which did not exist when the figure of 20 was quoted an hour earlier. Two more (`216rgg`, `w2y5ac`) were authored concurrently by another agent. So the population is a MOVING TARGET and any plan pinning it to a number will be wrong on the day it runs. A SECOND DERIVATION ROUTE WAS FOUND, which shrinks the human decision considerably: 10 of the 24 are children of the ONE `runanalytics` Set, so they can inherit from their orchestrator rather than needing 10 separate judgements. That leaves roughly a dozen genuine decisions rather than 24.

## Goal

Leave no pending plan unprioritized, while making only the judgements that genuinely require a human and deriving everything else.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: shrink the decision before asking for it

- [ ] E-01 RE-DERIVE THE POPULATION AT EXECUTION TIME AND DO NOT TRUST ANY COUNT IN THIS PLAN. Compute the pending plans that carry no resolvable `- From-Backlog:` AND do not yet carry both fields (sibling 02 will have populated many). Measured at authoring: 24 carried no source, of which 4 are this Set's own plans. The number WILL differ: plans are authored continuously by several agents, and this Set's own four plans are in the population.
  EXCLUDE WHAT SIBLING 02 ALREADY WROTE, by testing for the FIELDS rather than for the source reference. A plan that gained values from inheritance must not be re-decided here.
  - Depends on: none
  - Expected outcome: a printed list of plans still missing either field, with each plan's Set, Kind, Status and `Blocks-Release`, and the count stated as measured rather than quoted.
  - Execution state: pending

- [ ] E-02 APPLY THE SECOND DERIVATION ROUTE: A CHILD INHERITS FROM ITS SET ORCHESTRATOR. Where a plan is `- Kind: child` and its Set's Order-0 orchestrator carries both fields, inherit them rather than asking. This is the same reasoning sibling 02 uses (take the value from an artifact the plan itself names) applied one level up, and it is legitimate because a Set is by definition one coherent piece of work.
  MEASURED AT AUTHORING: 10 of the 24 are children of the single `runanalytics` Set (`bzz5e6`, `lhccjf`, `5f2h8i`, `8hald1`, `aflsz3`, `6eq3oq`, `mm5p3v`, `ixis0c`, `9xycbh`, plus its orchestrator `5lxvl3`), so ONE decision on that orchestrator settles ten plans. Check every multi-child Set in the population for the same shape, not only that one.
  THE ORCHESTRATOR ITSELF STILL NEEDS A VALUE, so this route reduces N decisions to 1 per Set; it does not eliminate them. Where the orchestrator ALSO lacks both fields, it goes to E-03.
  - Depends on: E-01
  - Expected outcome: a list of children resolved by Set inheritance with the orchestrator each inherited from, and a reduced remainder for E-03; the reduction is stated numerically.
  - Execution state: pending

- [ ] E-03 PUT THE GENUINE REMAINDER TO THE MAINTAINER AS ONE LIST, NOT AS N QUESTIONS. For each remaining plan give its Concern in one line, its Set, whether it carries `- Blocks-Release:`, and a RECOMMENDED `Priority` and `Work-Kind` with a one-clause reason, so the maintainer confirms or corrects a table rather than answering a series of prompts. The maintainer explicitly asked for this shape ("as a single list rather than twenty questions").
  DERIVE THE RECOMMENDATION, DO NOT GUESS IT. `Work-Kind` is usually readable from the plan's own Concern (a plan fixing a measured defect is `bug`; one adding a capability is `feature`; one moving or renaming records is `chore`; one closing a safety gap is `security`; one cleaning up after another plan is `followup`). For `Priority`, a plan carrying `- Blocks-Release:` is a candidate for `high` but this is NOT automatic: `p9o1oo` records that the urgent case is covered orthogonally by `Blocks-Release`, so the two must not be conflated. State each recommendation's basis.
  THIS PLAN'S OWN FOUR PLANS ARE IN THE LIST and must not be quietly self-assigned a flattering priority; recommend them like any other and let the maintainer rule.
  - Depends on: E-02
  - Expected outcome: one table covering every remaining plan with a recommended pair and its basis, put to the maintainer, and their confirmations or corrections recorded verbatim.
  - Execution state: pending

- [ ] E-04 WRITE THE CONFIRMED VALUES THROUGH THE SHIPPED SETTER and prove nothing else moved. Use `aw ipd set <current-status> <id6> --priority <p> --work-kind <k>`, which persists both on a no-op transition; never hand-edit front matter. Then show that no plan's `Status`, `Readiness`, `Set`, `Order` or `Id` changed, that `aw check plans` reports no new finding, and that every pending plan now carries both fields or a recorded reason why not.
  RE-VERIFY THE INDEX BEFORE EVERY COMMIT, and again after any failed hook: other agents commit concurrently and pre-commit's stash/restore can leave their paths staged.
  - Depends on: E-03
  - Expected outcome: every plan in the population carries both fields; the working invocation is recorded; no collateral metadata change; `aw att --type plan` shows no unprioritized pending plan remaining.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd set --priority` / `--work-kind` persist "on a no-op transition", so a field-only write needs no status change and no hand-editing.
- `Priority` and `Blocks-Release` are ORTHOGONAL by explicit decision: source item `p9o1oo` records that the urgent case "is already covered orthogonally by `Blocks-Release`, so no 4th tier". A release-blocking plan is therefore not automatically `high`.
- A value must never be FABRICATED (`xprio` orchestrator `u5vyye` OQ-01, which ruled an absent priority renders as unprioritized rather than as an implicit `medium`). Deriving from a named artifact is not fabrication; inventing one to fill a column is.
- `aw ipd scaffold` does not emit either field (`ipd_authoring.py:170-185`), which is why this population exists at all and why sibling 01 fixes the scaffold.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | MEDIUM | The population is a MOVING TARGET and the quoted figure of 20 was stale within the hour. Measured at authoring: 24 pending plans carry no resolvable source, four of which are this Set's own plans and two of which another agent authored concurrently. Any step pinning the count will be wrong on execution day, so E-01 re-derives it. |
| F-2 | MEDIUM | A second derivation route exists and cuts the human decision roughly in half: 10 of the 24 are children of the single `runanalytics` Set, so one decision on that orchestrator settles ten plans. Only the orchestrator itself needs a judgement. |
| F-3 | LOW | `Work-Kind` is largely readable from a plan's own Concern, so most recommendations can be derived rather than guessed, which is what makes a single confirmation table viable instead of N prompts. |
| F-4 | LOW | This plan's own four plans sit in the population it decides, which is a mild conflict of interest worth naming: they must be recommended on the same basis as any other plan, not self-assigned a convenient priority. |

## Proposed changes (ordered, validatable)

1. Re-derive the population by testing for the FIELDS, not the source reference (E-01).
2. Resolve children from their Set orchestrator where possible, stating the reduction (E-02).
3. Put the genuine remainder to the maintainer as ONE recommendation table with bases (E-03).
4. Write confirmed values through the setter and prove no collateral change (E-04).

## Deferred / out of scope (with reason)

- ANY PLAN SIBLING 02 REACHED. Excluded by construction in E-01, which tests for the fields rather than the source reference.
- TERMINAL PLANS. Immutable by policy and exempt via sibling 01's sentinel.
- CORRECTING A SET ORCHESTRATOR'S OWN VALUE. If an orchestrator's inherited-down value looks wrong, report it; re-deciding another Set's priority is not this plan's business.
- BACKFILLING SPECS OR RESEARCH, which carry the same optional field. Raised as the parent's OQ-01.

## Scope check

- Over-scope: none. Only the pending plans tree, only two fields plus history.
- Under-scope: this plan does not prevent the population reappearing; sibling 01's scaffold fix is what does that, which is why this plan depends on it.

## Required tests / validation

No new test file: this plan changes records, not code. Run the bare suite (`python3 -m pytest`) and paste the summary anyway, since a record change should not affect it and a difference would be informative. Establish the baseline BEFORE the first edit.

## Spec / documentation sync

N/A: sibling 01 amends the spec defining the metadata fields. This plan writes values into existing recognized fields and changes no contract.

## Open questions

### OQ-01: May a child inherit `Priority` from its Set orchestrator, or must every plan be decided individually?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer only if the Set-inheritance route is rejected
- Resolution or deferral rationale: PROCEED WITH SET INHERITANCE AND SAY SO IN THE REPORT. A Set is by definition one coherent piece of work with one orchestrator holding its sequencing, so its children sharing the Set's priority is the same kind of derivation sibling 02 performs from a backlog source: a value taken from an artifact the plan itself names, not a fabricated one. The measured payoff is large (ten plans settled by one decision) and the risk is low, since a child whose priority genuinely differs from its Set can be corrected individually afterwards. Non-blocking because the alternative (decide all of them) is merely slower, not wrong; if the maintainer prefers per-plan decisions, E-03's table simply grows. Record which children were resolved this way so any correction is easy to target.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the re-derived population with the command that produced it and the count. State explicitly how it differs from the 24 measured at authoring, and confirm the query tested for the FIELDS rather than for `From-Backlog` (paste the predicate).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the children resolved by Set inheritance, each with the orchestrator id6 and the two inherited values, and state the numeric reduction (from N to M). Confirm every such child is `- Kind: child` and that its orchestrator genuinely carried both fields.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the recommendation table as it was put to the maintainer, including each recommendation's stated basis, then paste their response verbatim and the resulting final assignments. Any correction they made must be visible as a correction, not silently folded in.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the working `aw ipd set` invocation and one plan's `git diff` showing only the two fields and history changed with `- Status:` unchanged. Paste a grep proving no plan's `Status`/`Readiness`/`Set`/`Order`/`Id` changed. Paste `aw check plans` clean, `aw att --type plan` showing no pending plan without a priority, and `git diff --cached --name-only` from before the final commit proving only this item's files were staged. Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

It carries `- Item-Dependencies: executed:lkexaw` deliberately, for the same reason sibling 02 does: deciding values before the gate and the scaffold fix exist would write values nothing enforces and leave the root cause in place.

It is INDEPENDENT of sibling 02 and may run before, after or concurrently with it, because E-01 tests for the fields rather than for the source reference, so whichever runs second simply sees a smaller population.

Execution contract for whoever runs it: commit ONLY paths under the declared `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE ONE JUDGEMENT HAZARD: this plan asks a human to confirm a table it composed, and this plan's own four plans are in that table. Recommend them on the same basis as every other plan. A recommendation that quietly gives this Set's own work a higher priority than it argued for elsewhere is the failure to avoid.
