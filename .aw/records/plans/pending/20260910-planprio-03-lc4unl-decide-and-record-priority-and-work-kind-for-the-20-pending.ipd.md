# IPD: Decide and record Priority and Work-Kind for the pending plans with no source item

- Date: 2026-09-10
- Kind: child
- Concern: The pending plans that carry no resolvable `- From-Backlog:` cannot inherit `Priority` and `Work-Kind` from a source, so sibling 02's mechanical backfill leaves them empty. Without a value they stay unprioritized on the board, and they are disproportionately the plans with no backlog origin, which may be exactly the ones most needing triage. RE-MEASURED AT REVIEW (2026-09-12, HEAD `5e0e9873`): the population is 28, not the authored 24 nor the title's 20, spread over 10 Sets (`runanalytics` 10, `planprio` 4, `nobugship` 4, `orchprobe` 3, `setidfix` 2, and one each in `lanectn`, `defreport`, `integearn`, `runnerbugs`, `rdyrecheck`), and split by status 13 `approved`, 11 `reviewed`, 4 `to-review`. Do NOT re-quote these either; E-01 re-derives them.
- Scope: Assign both fields to every pending plan sibling 02 could not reach, using a SECOND derivation route where one exists (a child inheriting from its Set orchestrator) and a single human decision list for the genuine remainder. Writes through the shipped `aw ipd set` setters only. Does NOT touch any plan sibling 02 handled, does NOT edit terminal plans, and does NOT change any vocabulary.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: executed:lkexaw
- Status: reviewed
- Readiness: no-go
- Set: planprio
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: lc4unl

## Workflow history

- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN and escalated to blocking OQ-02), PR-002 (BLOCKER, OPEN and escalated to blocking OQ-03), PR-003 (BLOCKER, OPEN, inherits the parent's blocking OQ-02, escalated here as OQ-04), PR-004..PR-012 FIXED; readiness `no-go`. Record: `.aw/records/reviews/20260910-planprio-03-lc4unl-decide-and-record-priority-and-work-kind-for-the-20-pending.review.md`. `aw ipd lint --phase author` CONFORMING (clean, 0 findings) before semantic review. Suite measured bare at HEAD `5e0e9873`: `5971 passed, 3 skipped, 2 xfailed in 58.02s`. DISCLOSURE: same agent/model family authored this Set, so treat as a near-self-review; its value rests on what was EXECUTED.
  THE PLAN'S THESIS IS SOUND: a population with no source needs a decision, and shrinking that decision before asking a human is the right instinct. THE SET-INHERITANCE ROUTE IS ALSO SOUND, and review measured it delivering a real reduction: 13 human decisions covering 28 plans rather than 28. Neither was changed.
  BUT THE ROUTE RESOLVES ZERO PLANS AS SEQUENCED, which is the first blocker and was proven by computing it rather than reasoning about it. E-02 says a child inherits from its Set orchestrator "where the orchestrator carries both fields", and E-02 runs BEFORE E-03. Measured over the live population: NOT ONE orchestrator of the 28 carries both fields today, so E-02 resolves 0 of 28 and the whole population falls through to E-03, which is exactly the 28-question outcome the plan exists to avoid. The route only works if the orchestrator is DECIDED FIRST, which inverts the E-02/E-03 order. Escalated as blocking OQ-02.
  THE SECOND BLOCKER IS THAT FOUR PLANS SILENTLY DEPEND ON SIBLING 02 RUNNING FIRST, contradicting this plan's own independence claim. Measured: `orchprobe`'s orchestrator `yeh7gc` and `lanectn`'s `h0zljh` each carry a RESOLVABLE `- From-Backlog:`, so sibling 02 fills them; their 4 children can then inherit. If this plan runs FIRST, those 4 go to the human decision list unnecessarily. The gate's claim that "whichever runs second simply sees a smaller population" is true for the FIELDS test but false for the inheritance PAYOFF. Escalated as blocking OQ-03.
  THE THIRD BLOCKER IS INHERITED: `- Item-Dependencies: executed:lkexaw` is the edge the parent's review measured as stranding 18 already-approved pending plans, and this plan defends it with the same reasoning the parent found false. Escalated here as OQ-04 so this file refuses execution too, with the decision made ONCE at the parent.
  THREE FURTHER MEASURED HAZARDS. (1) E-03 REQUIRES A HUMAN AND THE PLAN HAS NO NON-INTERACTIVE PATH: under `aw oc run` the driver states the run is non-interactive, so E-03 cannot complete and E-04 depends on it. (2) A SETID SELECTOR WOULD REVERT AN EXECUTED PLAN here as it would in sibling 02: 3 of the 10 setids in this population also name a terminal plan, and a dry-run on `runanalytics` reports `executed -> approved`. (3) 13 OF THE 28 ARE `approved`, so the setter's false history line (sibling 02's blocking OQ-02) applies to 13 plans here rather than 5.
- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after the maintainer chose the full option on 2026-09-10 including "decide the 20". THE TITLE SAYS "the pending plans" RATHER THAN "the 20" DELIBERATELY, because the count was already stale when this was written: measured at authoring the population is 24, not 20, and four of those are this very Set's own plans (`d0cbt3`, `lkexaw`, `8u6770`, `lc4unl`), which did not exist when the figure of 20 was quoted an hour earlier. Two more (`216rgg`, `w2y5ac`) were authored concurrently by another agent. So the population is a MOVING TARGET and any plan pinning it to a number will be wrong on the day it runs. A SECOND DERIVATION ROUTE WAS FOUND, which shrinks the human decision considerably: 10 of the 24 are children of the ONE `runanalytics` Set, so they can inherit from their orchestrator rather than needing 10 separate judgements. That leaves roughly a dozen genuine decisions rather than 24.

## Goal

Leave no pending plan unprioritized, while making only the judgements that genuinely require a human and deriving everything else.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: shrink the decision before asking for it

- [ ] E-01 RE-DERIVE THE POPULATION AT EXECUTION TIME AND DO NOT TRUST ANY COUNT IN THIS PLAN. Compute the pending plans that carry no resolvable `- From-Backlog:` AND do not yet carry both fields (sibling 02 will have populated many). Measured at authoring: 24 carried no source, of which 4 are this Set's own plans. The number WILL differ: plans are authored continuously by several agents, and this Set's own four plans are in the population.
  EXCLUDE WHAT SIBLING 02 ALREADY WROTE, by testing for the FIELDS rather than for the source reference. A plan that gained values from inheritance must not be re-decided here.
  RECORD THE ORDER AND KIND PER ROW, not only the Set, because E-02's route keys on them: a plan is a candidate for Set inheritance only if it is `- Kind: child` AND its Set has an Order-0 orchestrator that carries (or will carry) both fields. Without those two columns the table cannot be partitioned and E-02 becomes guesswork.
  RECORD THE STATUS PER ROW TOO, because it decides the setter risk. Measured at review, 13 of the 28 are `approved`, which is the population that trips the false-history-line problem (OQ-03 on sibling 02, and the same hazard here).
  REVIEW'S READING, for comparison only: 28 plans across 10 Sets (`runanalytics` 10, `planprio` 4, `nobugship` 4, `orchprobe` 3, `setidfix` 2, then `lanectn`, `defreport`, `integearn`, `runnerbugs`, `rdyrecheck` with one each), split 13 `approved` / 11 `reviewed` / 4 `to-review`. Derive your own and state the delta.
  - Depends on: none
  - Expected outcome: a printed list of plans still missing either field, each row carrying Set, Kind, Order, Status and `Blocks-Release`, the count stated as measured rather than quoted, and the delta against review's 28 recorded.
  - Execution state: pending

- [ ] E-02 PARTITION THE POPULATION INTO WHAT A SET ORCHESTRATOR CAN SETTLE AND WHAT NEEDS A HUMAN, WITHOUT WRITING ANYTHING YET. This item was RE-SCOPED at review from "apply the route" to "plan the route", because applying it here is what makes it resolve nothing (PR-001, blocking OQ-02).
  THE ROUTE IS SOUND AND ITS PAYOFF IS REAL. A child inheriting its Set orchestrator's values is the same derivation sibling 02 performs from a backlog source, one level up, and it is legitimate because a Set is by definition one coherent piece of work. MEASURED at review, once the orchestrators are decided the route yields 13 human decisions covering 28 plans instead of 28.
  BUT AS SEQUENCED IT RESOLVES ZERO, WHICH IS WHY THIS ITEM NO LONGER WRITES. E-02 ran before E-03 and required the orchestrator to ALREADY carry both fields. MEASURED over the live population: NOT ONE of the orchestrators carries both fields today, so the condition holds for 0 of 28 plans and the entire population falls through to E-03, producing exactly the 28-question outcome this plan exists to avoid. The order must invert (decide orchestrators first, then derive children) and OQ-02 owns that.
  PARTITION INTO THREE CLASSES AND STATE THE COUNTS. (a) CHILD OF A SET WHOSE ORCHESTRATOR SIBLING 02 WILL FILL: measured at review, `orchprobe` (orchestrator `yeh7gc`, source `5ev6lh`) and `lanectn` (orchestrator `h0zljh`, source `vqv9im`), covering 4 children. These need NO human decision at all IF sibling 02 has run; that is PR-002 and blocking OQ-03. (b) CHILD OF A SET WHOSE ORCHESTRATOR NEEDS A HUMAN: `runanalytics` (9 children under `5lxvl3`), `planprio` (3 under `d0cbt3`), `nobugship` (3 under `qmgn12`), so 3 decisions cover 15 plans plus their 3 orchestrators. (c) NO IN-POPULATION ORCHESTRATOR TO INHERIT FROM: `setidfix` (2), `orchprobe`'s own remainder if (a) does not apply, `defreport`, `integearn`, `runnerbugs`, `rdyrecheck` (1 each), which are individual decisions.
  VERIFY THE ORCHESTRATOR EXISTS IN `pending/` BEFORE COUNTING ON IT. Measured, 5 Sets in the population have NO Order-0 plan in `pending/` at all (`setidfix`, `defreport`, `integearn`, `runnerbugs`, `rdyrecheck`), so their children have nothing to inherit from and belong in class (c). Do not assume a Set has an orchestrator because it has an Order.
  - Depends on: E-01
  - Expected outcome: the population partitioned into the three classes with counts, every orchestrator named with its own source-or-needs-a-decision state, the projected number of human decisions stated (review measured 13), and NO value written by this item.
  - Execution state: pending

- [ ] E-03 PUT THE DECIDABLE UNITS TO THE MAINTAINER AS ONE LIST, NOT AS N QUESTIONS, AND ASK ABOUT ORCHESTRATORS RATHER THAN ABOUT EVERY CHILD. For each unit give its Concern in one line, its Set, whether it carries `- Blocks-Release:`, and a RECOMMENDED `Priority` and `Work-Kind` with a one-clause reason, so the maintainer confirms or corrects a table rather than answering a series of prompts. The maintainer explicitly asked for this shape ("as a single list rather than twenty questions").
  THE LIST IS THE 13 UNITS FROM E-02's PARTITION, NOT THE 28 PLANS. Measured at review: 3 orchestrator decisions (`5lxvl3`, `d0cbt3`, `qmgn12`) settle 15 children between them, class (a)'s 4 children need nothing if sibling 02 has run, and the remaining rows are individual. State the coverage explicitly in the table ("this row settles N plans") so the maintainer can see that confirming 13 rows disposes of 28 plans; a table that hides the fan-out invites them to wonder what they are actually approving.
  IF THERE IS NO HUMAN TO ASK, RECORD AND DEFER RATHER THAN GUESSING OR STALLING. Under `aw oc run` / `aw agy run` the driver states the run is non-interactive and forbids invoking an interactive question tool, and the `askme` workflow's own contract is to record and defer in that case rather than block. So: compose the table, WRITE IT into this plan as the deferred artifact, leave every affected plan untouched, and report that E-04 is deferred pending a human. Do NOT fabricate a confirmation, and do NOT self-approve the table on the executor's authority; a derived recommendation is evidence, not a decision. This branch is what stops the plan stalling a whole unattended queue.
  DERIVE THE RECOMMENDATION, DO NOT GUESS IT. `Work-Kind` is usually readable from the plan's own Concern (a plan fixing a measured defect is `bug`; one adding a capability is `feature`; one moving or renaming records is `chore`; one closing a safety gap is `security`; one cleaning up after another plan is `followup`). For `Priority`, a plan carrying `- Blocks-Release:` is a candidate for `high` but this is NOT automatic: `p9o1oo` records that the urgent case is covered orthogonally by `Blocks-Release`, so the two must not be conflated. State each recommendation's basis.
  THIS PLAN'S OWN FOUR PLANS ARE IN THE LIST and must not be quietly self-assigned a flattering priority; recommend them like any other and let the maintainer rule. Measured at review, all four `planprio` plans are in the population, and under the corrected route they collapse into ONE row (a decision on orchestrator `d0cbt3` settling `lkexaw`, `8u6770` and `lc4unl`), which makes the conflict of interest easier to see rather than harder.
  COMPOSE THE PROMPT PER P12 AND THE `askme` MEMORY KERNEL, not as a wall of evidence: enough context to decide from the prompt alone, no chronology, no filenames unless essential, and do NOT restate the options the interactive tool will render. A 28-row table pasted into a prompt is precisely what P12 exists to prevent; a 13-row table with a coverage column and a one-clause basis per row is the shape to aim for.
  - Depends on: E-02
  - Expected outcome: one table of the ~13 decidable units with a recommended pair, its basis and its coverage count, put to the maintainer if one is present, and their confirmations or corrections recorded verbatim; OR, in a non-interactive run, the same table written into this plan with E-04 explicitly deferred and nothing written to any other plan.
  - Execution state: pending

- [ ] E-04 WRITE THE CONFIRMED ORCHESTRATOR AND INDIVIDUAL VALUES THROUGH THE SHIPPED SETTER, using the EXACT form sibling 02's review verified: `aw ipd set <that-plan's-current-status> <id6> --priority <p> --work-kind <k> --message "<why>" --no-commit --yes`. Every element is load-bearing and four were added at review.
  USE THE id6, NEVER A SETID, AND THIS IS THE SHARPEST HAZARD IN THE ITEM. A setid resolves to EVERY plan carrying it, terminal ones included. MEASURED at review, 3 of the 10 setids in this population also name a terminal plan (`integearn`, `lanectn`, `runanalytics`), and `aw ipd set approved runanalytics --priority medium --work-kind feature --dry-run` reports `executed -> approved` on plan `xbwq8n` in `executed/`. Backlog `f5pttg` (`open`, high) records this exact command having silently reverted seven executed plans. The temptation is acute here precisely BECAUSE this plan thinks in Sets: the whole point of E-02 is that one decision covers a Set, and the wrong way to apply that is one setid command.
  DRY-RUN EVERY INVOCATION AND READ IT. A line reading anything but `unchanged` for exactly the one plan you named means the selector over-matched; STOP rather than proceeding. That is the unsafe-condition stop, not a scope stop.
  PASS `--message`, BECAUSE A SAME-STATUS WRITE OTHERWISE FABRICATES A HISTORY LINE. MEASURED at review on orchestrator `5lxvl3` (`approved`): without it the setter appends `- <date> approved (aw set): status set to approved`, asserting a transition that did not happen. 13 of the 28 plans here are `approved`, so this is the majority of the population rather than an edge case. Sibling 02's blocking OQ-02 owns the question of whether that is acceptable; whatever it answers applies here identically and this plan must not answer it independently.
  PASS `--no-commit`. Otherwise the setter offers to commit after each write, and accepting mid-loop in this shared checkout sweeps whatever else is staged.
  NEVER HAND-EDIT FRONT MATTER. The setter owns field position (it inserts both directly after `- Status:`, verified) and the history record.
  - Depends on: E-03
  - Expected outcome: every confirmed unit written; every invocation used an id6, a dry-run preflight, `--no-commit` and a truthful `--message`; no plan's `- Status:` changed; nothing written in a non-interactive run where E-03 deferred.
  - Execution state: pending

- [ ] E-05 DERIVE THE CHILDREN FROM THEIR NOW-DECIDED ORCHESTRATORS, which is the step that makes E-02's partition pay off and which the authored plan had no item for.
  ONLY NOW DOES THE INHERITANCE CONDITION HOLD. E-02 measured that no orchestrator carried both fields; E-04 has just given them values, so a child may now inherit. Apply the same setter form as E-04, one child at a time, by id6.
  RECORD WHICH CHILDREN WERE DERIVED AND FROM WHICH ORCHESTRATOR, so a later correction can target them: OQ-01's whole safety argument is that a child whose priority genuinely differs can be fixed individually afterwards, and that is only true if the derivation is auditable.
  DO NOT DERIVE ACROSS A SET BOUNDARY and do not derive from an orchestrator that is not Order-0 of that child's own Set. A shared setid is a topic label, not a containment claim (D153), so match on the `- Set:` value AND the Order-0 position, not on the filename.
  - Depends on: E-04
  - Expected outcome: every class (a) and class (b) child carrying its Set orchestrator's values, with a per-child record of the orchestrator it inherited from, and no cross-Set derivation.
  - Execution state: pending

- [ ] E-06 PROVE NOTHING ELSE MOVED AND THE RESULT IS OBSERVABLE, which the authored E-04 bundled with the write and partly could not demonstrate.
  SHOW NO COLLATERAL METADATA CHANGE: no plan's `Status`, `Readiness`, `Set`, `Order` or `Id` differs, and only the two field lines plus one history line per plan changed.
  PROVE NO TERMINAL PLAN WAS TOUCHED: `git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed` must be EMPTY. Given the measured 3-setid collision this is the assertion that would catch the `f5pttg` failure mode before it commits.
  DO NOT REQUIRE `aw check plans` CLEAN. Measured bare at review (HEAD `5e0e9873`) it exits 1 with `errors 140  warnings 0` (124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`), none caused by this plan. Capture that count BEFORE the first edit and compare per rule id. An executor told to make it clean would either stall or edit another agent's plans, which the shared-checkout rule forbids.
  USE A PRIORITY SURFACE THAT ACTUALLY HAS THE COLUMN. MEASURED at review: a piped `aw att --type plan` emits `- [plans] <path> (<status>)` with NO Priority column, so the authored evidence command cannot show what it asks. Use `FORCE_COLOR=1 aw att --type plan` or `aw att --type plan --format json`, whose per-item `priority` key is machine-readable; review measured 13 non-null before this Set runs, so state the before and after counts and the delta.
  RE-VERIFY THE INDEX BEFORE EVERY COMMIT, and again after any failed hook: other agents commit concurrently and pre-commit's stash/restore can leave their paths staged.
  - Depends on: E-05
  - Expected outcome: no collateral metadata change, an empty terminal-directory status, `aw check plans` compared per rule against the pre-edit baseline, and the non-null `priority` count stated before and after with the delta matching the plans written.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd set --priority` / `--work-kind` persist "on a no-op transition", so a field-only write needs no status change and no hand-editing. DRIVEN at review on an `approved` plan: exit 0, prints `unchanged`, both fields written after `- Status:`, status untouched.
- A SAME-STATUS WRITE WITHOUT `--message` FABRICATES A HISTORY LINE. Measured on `5lxvl3`: `- <date> approved (aw set): status set to approved` on a plan that did not transition. 13 of the 28 plans here are `approved`, so this is the majority case. Sibling 02's blocking OQ-02 owns whether that is acceptable.
- A SETID SELECTOR IS DANGEROUS AND AN id6 IS NOT. 3 of the 10 setids in this population also name a terminal plan (`integearn`, `lanectn`, `runanalytics`), and a dry-run on `runanalytics` reports `executed -> approved` on `xbwq8n` in `executed/`. Backlog `f5pttg` records this having reverted seven executed plans for real, and it is still `open`.
- `--dry-run` AND `--no-commit` BOTH WORK on this path and are the two mechanical guards for a bulk field write.
- NO ORCHESTRATOR IN THIS POPULATION CARRIES BOTH FIELDS TODAY, measured. So Set inheritance cannot be applied before the orchestrators are decided; the route needs the decision first and the derivation second.
- FIVE SETS IN THE POPULATION HAVE NO Order-0 PLAN IN `pending/` AT ALL (`setidfix`, `defreport`, `integearn`, `runnerbugs`, `rdyrecheck`), so their children have no orchestrator to inherit from. Having an `- Order:` does not imply the Set has an orchestrator here.
- A SHARED SETID IS A TOPIC LABEL, NOT A CONTAINMENT CLAIM (D153). Match a child to its orchestrator on the `- Set:` value AND Order-0 position, never on the filename, and never derive across a Set boundary.
- A RUNNER TURN HAS NO HUMAN. Both drivers state the run is non-interactive and forbid invoking an interactive question tool; the `askme` workflow's own contract is to record and defer rather than block. Any plan whose critical path is a human decision needs an explicit deferral branch or it stalls an unattended queue.
- THE PRIORITY COLUMN IS NOT ON THE PIPED BOARD. `aw att --type plan` piped emits `- [plans] <path> (<status>)`; the column lives only in the colored renderer. Use `FORCE_COLOR=1` or `--format json` (13 items carried a non-null `priority` at review).
- `aw check plans` IS 140 ERRORS DEEP BEFORE THIS PLAN RUNS (124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`), so "clean" is unobtainable and a per-rule delta is the only honest bar.
- `Priority` and `Blocks-Release` are ORTHOGONAL by explicit decision: source item `p9o1oo` records that the urgent case "is already covered orthogonally by `Blocks-Release`, so no 4th tier". A release-blocking plan is therefore not automatically `high`.
- A value must never be FABRICATED (`xprio` orchestrator `u5vyye` OQ-01, which ruled an absent priority renders as unprioritized rather than as an implicit `medium`). Deriving from a named artifact is not fabrication; inventing one to fill a column is.
- `aw ipd scaffold` does not emit either field (`ipd_authoring.py:170-185`), which is why this population exists at all and why sibling 01 fixes the scaffold.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | MEDIUM | The population is a MOVING TARGET and the quoted figure of 20 was stale within the hour; the authored 24 is now stale too. RE-MEASURED at review: 28 pending plans carry no resolvable source and still lack a field, across 10 Sets, split 13 `approved` / 11 `reviewed` / 4 `to-review`. Any step pinning the count will be wrong on execution day, so E-01 re-derives it. |
| F-2 | MEDIUM | A second derivation route exists and cuts the human decision by more than half: measured at review, 13 decisions cover all 28 plans. The largest single lever is `runanalytics` (1 orchestrator decision settling 9 children), with `planprio` and `nobugship` settling 3 each. |
| F-2b | BLOCKER | **THE ROUTE RESOLVES ZERO PLANS AS SEQUENCED.** E-02 required the Set orchestrator to ALREADY carry both fields and ran BEFORE E-03. Measured over the live population: NOT ONE orchestrator carries both fields, so the condition holds for 0 of 28 and the whole population falls through to the human list, producing exactly the 28-question outcome this plan exists to avoid. The order must invert: decide orchestrators first, then derive children. Blocking OQ-02. |
| F-2c | BLOCKER | **FOUR PLANS SILENTLY DEPEND ON SIBLING 02 RUNNING FIRST**, contradicting this plan's independence claim. `orchprobe`'s orchestrator `yeh7gc` (source `5ev6lh`) and `lanectn`'s `h0zljh` (source `vqv9im`) each carry a resolvable source, so sibling 02 fills them and their 4 children can then inherit for free. Run first and those 4 become needless human decisions. The gate's "whichever runs second simply sees a smaller population" is true for the FIELDS test and false for the inheritance PAYOFF. Blocking OQ-03. |
| F-3 | LOW | `Work-Kind` is largely readable from a plan's own Concern, so most recommendations can be derived rather than guessed, which is what makes a single confirmation table viable instead of N prompts. |
| F-4 | LOW | This plan's own four plans sit in the population it decides, which is a mild conflict of interest worth naming: they must be recommended on the same basis as any other plan, not self-assigned a convenient priority. Under the corrected route they collapse into ONE row (a decision on `d0cbt3`), which makes the conflict easier to see rather than harder. |
| F-5 | BLOCKER | **E-03's CRITICAL PATH IS A HUMAN AND THERE WAS NO NON-INTERACTIVE BRANCH.** Under `aw oc run` / `aw agy run` the driver states the run is non-interactive and forbids invoking an interactive question tool, and E-04 depends on E-03, so an unattended run would either stall or fabricate a confirmation. E-03 now records-and-defers, matching the `askme` contract. |
| F-6 | HIGH | **A SETID SELECTOR WOULD REVERT AN EXECUTED PLAN.** 3 of the 10 setids here also name a terminal plan, and `aw ipd set approved runanalytics --dry-run` reports `executed -> approved` on `xbwq8n` in `executed/`. The temptation is acute precisely because this plan thinks in Sets. Backlog `f5pttg` records the same command having reverted seven executed plans, and it is `open`. |
| F-7 | HIGH | **13 OF THE 28 ARE `approved`**, so the setter's fabricated history line applies to the majority of this population rather than an edge of it. Sibling 02 escalated the same defect over 5 plans; here it is 13. This plan must inherit that answer, not decide it. |
| F-8 | MEDIUM | **FIVE SETS HAVE NO Order-0 PLAN IN `pending/`** (`setidfix`, `defreport`, `integearn`, `runnerbugs`, `rdyrecheck`), so their children have nothing to inherit from and are individual decisions. E-02 assumed an orchestrator exists wherever a Set does. |
| F-9 | MEDIUM | **TWO PRESCRIBED EVIDENCE COMMANDS CANNOT PRODUCE WHAT THEY ASK.** A piped `aw att --type plan` has no Priority column, and `aw check plans` carries 140 pre-existing errors so it can never be shown "clean". Both corrected. |
| F-10 | LOW | The authored E-04 bundled a bulk write, a no-collateral-change proof and an observability claim into one item, so a partial completion would have been indistinguishable from a full one. Split into E-04, E-05 and E-06. |

## Proposed changes (ordered, validatable)

1. Re-derive the population by testing for the FIELDS, not the source reference, recording Kind/Order/Status per row (E-01).
2. PARTITION into what a Set orchestrator can settle and what needs a human, writing nothing (E-02). Gated on OQ-02.
3. Put the ~13 decidable units to the maintainer as ONE table with bases and coverage counts, or record-and-defer if no human is present (E-03).
4. Write the confirmed orchestrator and individual values through the setter, by id6, dry-run first, `--no-commit`, truthful `--message` (E-04).
5. Derive the children from their now-decided orchestrators, recording the source of each (E-05).
6. Prove no collateral change, no terminal plan touched, and the result observable on a surface that has the column (E-06).

## Deferred / out of scope (with reason)

- ANY PLAN SIBLING 02 REACHED. Excluded by construction in E-01, which tests for the fields rather than the source reference.
- TERMINAL PLANS. Immutable by policy and exempt via sibling 01's sentinel. This plan must PROVE it touched none (E-06), because a setid selector would silently revert them.
- FIXING THE SETTER'S FABRICATED HISTORY LINE. Sibling 02's blocking OQ-02 owns it; the honest fix is code in the shared status setter, outside this plan's declared paths and intersecting the open backlog item `x6tk1u`. This plan inherits whatever is decided there and works around it with `--message`.
- DECIDING ANOTHER SET'S PRIORITY BEYOND ITS ORCHESTRATOR. Where a Set's orchestrator is decided here, its children inherit; this plan does not reach into a Set to re-rank individual children against their orchestrator.
- CORRECTING A SET ORCHESTRATOR'S OWN VALUE. If an orchestrator's inherited-down value looks wrong, report it; re-deciding another Set's priority is not this plan's business.
- BACKFILLING SPECS OR RESEARCH, which carry the same optional field. Raised as the parent's OQ-01.

## Scope check

- Over-scope: none. Only the pending plans tree, only two fields plus one history line per plan.
- Under-scope: this plan does not prevent the population reappearing; sibling 01's scaffold fix is what does that, which is why this plan depends on it.
- Under-scope, FOUND AT REVIEW and now carried rather than left implicit: the authored plan had no item DERIVING the children after their orchestrators were decided (E-02's condition could never hold before E-03, so the derivation had no home), and no separated proof that the result is observable. Now E-05 and E-06.
- A KNOWN LIMIT, STATED HONESTLY: this plan inherits sibling 02's unresolved question about the setter's fabricated history line, and 13 of its 28 plans are `approved`, so the majority of this population is affected by a defect this plan does not own and must not decide alone.
- A SECOND KNOWN LIMIT: Set inheritance assumes a Set's children share its priority. That is a reasonable default and it is exactly what OQ-01 records, but it is a DEFAULT rather than a fact, which is why E-05 must make every derivation auditable so a wrong one can be corrected individually.

## Required tests / validation

No new test file: this plan changes records, not code.

- THE THROWAWAY-COPY REHEARSAL before touching the real tree, which is how review found the setid and history-line hazards: copy the repo, run one write, inspect the diff, discard the copy. Never rehearse a bulk write in a shared checkout.
- THE DRY-RUN PREFLIGHT on every invocation, with its output read. Anything but `unchanged` for exactly the plan you named means the selector over-matched.
- THE TERMINAL-DIRECTORY PROOF: `git status --porcelain` over `executed/`, `superseded/` and `not-executed/` must be empty (E-06/V-06).
- `aw check plans` COMPARED PER RULE ID against a baseline captured before the first edit. Do NOT require clean: measured bare at review (HEAD `5e0e9873`) it exits 1 with `errors 140  warnings 0`, none of it caused by this plan.
- BOTH PRIORITY SURFACES: `FORCE_COLOR=1 aw att --type plan` and `aw att --type plan --format json`, with a before-and-after non-null count (review measured 13 before).
- `python3 -m pytest` BARE, baseline established BEFORE the first edit, judged on the failure SET rather than the count. A record change should not affect it and a difference would be informative. Review measured `5971 passed, 3 skipped, 2 xfailed in 58.02s` at HEAD `5e0e9873`, REFERENCE ONLY. Run it bare: the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0` or a second `-q` makes the run slower and suppresses the summary line the contract requires you to paste.
- `aw sanitize --agent` clean before treating any output as shareable.

## Spec / documentation sync

N/A: sibling 01 amends the spec defining the metadata fields. This plan writes values into existing recognized fields and changes no contract.

## Open questions

### OQ-01: May a child inherit `Priority` from its Set orchestrator, or must every plan be decided individually?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer only if the Set-inheritance route is rejected
- Resolution or deferral rationale: PROCEED WITH SET INHERITANCE AND SAY SO IN THE REPORT. A Set is by definition one coherent piece of work with one orchestrator holding its sequencing, so its children sharing the Set's priority is the same kind of derivation sibling 02 performs from a backlog source: a value taken from an artifact the plan itself names, not a fabricated one. The measured payoff is large (ten plans settled by one decision) and the risk is low, since a child whose priority genuinely differs from its Set can be corrected individually afterwards.   Non-blocking because the alternative (decide all of them) is merely slower, not wrong; if the maintainer prefers per-plan decisions, E-03's table simply grows. Record which children were resolved this way so any correction is easy to target.
  MEASURED AT REVIEW, WHICH STRENGTHENS THE CASE: the route yields 13 human decisions covering 28 plans, and the correction-is-easy argument is now enforced rather than hoped for, because E-05 requires a per-child record of the orchestrator it inherited from. Note the route's PRECONDITION was wrong as sequenced (no orchestrator carries the fields yet), which is blocking OQ-02 and not this question.

### OQ-02: Set inheritance resolves zero plans while E-02 precedes E-03. Invert the order, or drop the route?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: MEASURED BY COMPUTATION, NOT PREDICTED, WHICH IS WHY IT IS BLOCKING. E-02 as authored inherits from a Set orchestrator "where the orchestrator carries both fields", and it runs BEFORE E-03. Over the live population at HEAD `5e0e9873`, NOT ONE of the orchestrators of the 28 plans carries both fields, so the condition is satisfied for 0 of 28 and the entire population falls through to E-03's human list. The plan's whole value proposition (roughly a dozen decisions rather than 24) evaluates to zero reduction as written, and the maintainer would be handed the 28-question table they explicitly asked to avoid.
  THE ROUTE ITSELF IS SOUND AND THE FIX IS AN ORDERING ONE. Once the orchestrators are decided, the derivation works and the payoff is large: measured, 13 decisions cover all 28 plans, because `runanalytics` alone settles 9 children from one orchestrator and `planprio` and `nobugship` settle 3 each.
  THREE OPTIONS. (a) INVERT: E-02 becomes a PARTITION step that writes nothing, E-03 decides the 13 units (orchestrators plus the individual remainder), E-04 writes them, and a new step derives the children afterwards. Cost: one more E-item and a checklist that no longer reads as decide-then-derive-in-one-pass; the plan grows from 4 items to 6. Benefit: the route delivers its measured reduction, the human sees 13 rows instead of 28, and each row can state how many plans it settles. (b) DROP SET INHERITANCE and decide all 28 individually. Cost: 28 judgements, which is what the maintainer declined, and it discards a derivation the repository already treats as legitimate elsewhere. Benefit: the simplest possible checklist. (c) SEED THE ORCHESTRATORS MECHANICALLY (for example give every orchestrator `medium`) then derive. Cost: that is FABRICATION, which `xprio`'s own ruling forbids and which this plan's conventions section explicitly names as the line not to cross. Benefit: no human needed.
  RECOMMENDATION (a), and review has already restructured the plan that way so the shape is inspectable: E-02 now partitions and writes nothing, E-03 asks about the 13 units with a coverage column, E-04 writes the decided values, and the new E-05 derives the children once their orchestrators have values. It is BLOCKING nonetheless because the restructure changes what the maintainer is asked to confirm (13 orchestrator-and-individual rows rather than a per-plan list), and that is their call to accept.
  (c) IS THE ONE TO AVOID: it would satisfy the board's Priority column while making every value untrustworthy, which is the opposite of what this Set exists to achieve.

### OQ-03: Four plans can inherit for free IF sibling 02 runs first. Does this plan still claim independence?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: THE INDEPENDENCE CLAIM IS TRUE FOR CORRECTNESS AND FALSE FOR COST, and the distinction was invisible until the orchestrators were inspected individually. This plan's gate says it "is INDEPENDENT of sibling 02 and may run before, after or concurrently with it, because E-01 tests for the fields rather than for the source reference, so whichever runs second simply sees a smaller population." The FIELDS test is indeed order-safe: nothing is double-written either way. But the INHERITANCE PAYOFF is not.
  MEASURED: two Sets in this population have an orchestrator that carries a RESOLVABLE `- From-Backlog:` and therefore gets its values from sibling 02, not from a human. `orchprobe`'s orchestrator is `yeh7gc` (source `5ev6lh`) with 3 children in the population, and `lanectn`'s is `h0zljh` (source `vqv9im`) with 1. So 4 children can be derived at zero human cost IF sibling 02 has already run, and become 4 unnecessary rows on the maintainer's table if this plan runs first.
  THREE OPTIONS. (a) DECLARE AN ORDERING PREFERENCE WITHOUT A HARD EDGE: state in the gate that running after sibling 02 is preferred because it shrinks the human list by 4, while keeping the plans independently runnable. Cost: a runner may still pick either order, so the saving is not guaranteed. Benefit: no new dependency edge, no new failure mode, and the preference is recorded where an operator sees it. (b) ADD A REAL EDGE (`- Item-Dependencies:` gains `executed:8u6770`). Cost: this plan then cannot run until sibling 02 completes, and sibling 02 currently carries its OWN two blocking questions, so the edge imports that delay; it also removes the concurrency the parent's child table explicitly permits. Benefit: the 4 free derivations are guaranteed. (c) HAVE E-02 RESOLVE AN ORCHESTRATOR'S SOURCE ITSELF rather than waiting for sibling 02 to write it. Cost: duplicates sibling 02's logic in a second plan, which is the drift this repository repeatedly pays for; the two would then have to agree about resolution and exclusion rules. Benefit: order becomes genuinely irrelevant.
  RECOMMENDATION (a), because the cost of the wrong order is 4 extra confirmations rather than a wrong outcome, and a hard edge would couple this plan to a sibling that is itself blocked. Whichever is chosen, the gate's current independence sentence must be qualified: it is order-safe but not order-neutral.

### OQ-04: This plan's dependency edge is the parent's blocking defect. Answer the PARENT's OQ-02, then bring this plan's `- Item-Dependencies:` into agreement.

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-003
- Resolution or deferral rationale: ANSWERED AT THE PARENT, NOT HERE, AND RECORDED HERE SO THE GATE HOLDS ON THIS FILE TOO. `- Item-Dependencies: executed:lkexaw` makes this plan wait for the child that installs the requiredness gate. The parent's review measured that ordering as stranding 18 already-approved pending plans the moment sibling 01 lands, because the gate fires at EVERY lint phase for a plan whose persisted status is at the ready-to-execute tier; of those 18, 13 have no source and therefore need THIS plan's decision table, which is what makes the circularity acute: the plans the gate strands are disproportionately the ones only this plan can unblock. The parent offers three costed options (stamp the exemption marker inside Order 01 as the shipped `oorry1` precedent did; reverse the order; or stage the gate as advisory) and recommends the first.
  DECIDE IT ONCE, on the parent (`d0cbt3` OQ-02), and record the same answer here. If the answer removes or reverses the edge, the `- Item-Dependencies:` line in this file must change in the same commit, because the parent's child table and this child's front matter are two statements of one fact.
  DO NOT DEFEND THE EDGE WITH THIS PLAN'S AUTHORED JUSTIFICATION, which the parent's measurement contradicts: "deciding values before the gate and the scaffold fix exist would write values nothing enforces" inverts the mechanism, since a value written before the gate exists is precisely what the gate then finds satisfied.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the re-derived population with the command that produced it and the count, each row carrying Set, Kind, Order, Status and `Blocks-Release`. State how it differs from review's 28 and the authored 24. Confirm the query tested for the FIELDS rather than for `From-Backlog` (paste the predicate). Paste the per-status split; review measured 13 `approved`, 11 `reviewed`, 4 `to-review`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the three-class partition with its counts and the projected number of human decisions (review measured 13 covering 28). For EVERY Set in the population, paste whether it has an Order-0 plan in `pending/` at all (review measured 5 that do not) and, where it does, whether that orchestrator already carries both fields, gets them from sibling 02, or needs a human. Confirm explicitly that this item WROTE NOTHING: `git status --porcelain -- .aw/records/plans` must be empty at its end.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste OQ-02's and OQ-03's recorded answers FIRST, since they decide the table's shape and whether 4 rows are needed at all. Then paste the recommendation table as it was put to the maintainer, including each row's stated basis AND its coverage count, then their response verbatim and the resulting final assignments. Any correction they made must be visible as a correction, not silently folded in. IF THE RUN WAS NON-INTERACTIVE: paste the driver's own non-interactive notice, the table as written into this plan, and an explicit statement that E-04 through E-06 are deferred and no other plan was touched. A fabricated or self-granted confirmation is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for the FIRST plan written, paste the `--dry-run` output showing exactly ONE plan named and `unchanged`, then the real invocation and its `git diff` showing only the two fields plus one history line changed with `- Status:` unchanged. Paste the history line and confirm it carries the supplied `--message` rather than `status set to approved`. Paste the full command list proving every invocation used an id6 and `--no-commit`; a single setid invocation is a FAILED validation given the measured `executed -> approved` result on `runanalytics`. Confirm no hand-edit was used.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the per-child derivation record: each child id6, the orchestrator id6 it inherited from, and the two values. Confirm every such child is `- Kind: child`, that the orchestrator is Order-0 of that child's OWN `- Set:` value (not merely a filename match, per D153), and that the orchestrator genuinely carried both fields at the time of derivation. State the numeric reduction actually achieved (from N plans to M human decisions) and compare it to E-02's projection.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste a grep proving no plan's `Status`/`Readiness`/`Set`/`Order`/`Id` changed, and `git diff --stat` over this plan's commits. Paste `git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed` showing it EMPTY; a non-empty result is a FAILED validation regardless of everything else. Paste `aw check plans` with its count and per-rule breakdown compared to the pre-edit baseline (review's was `errors 140`: 124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`), naming any new rule id; do not claim it clean and do not reduce a count by editing another party's plan. Paste `FORCE_COLOR=1 aw att --type plan` and `aw att --type plan --format json` with the non-null `priority` count before and after (review measured 13 before) and the delta. Do NOT paste a piped `aw att --type plan` and call the missing column a failure. Paste `git diff --cached --name-only` from before the final commit. Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline, compared on failure SETS rather than counts; review measured `5971 passed, 3 skipped, 2 xfailed in 58.02s` at HEAD `5e0e9873`, reference only.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: no-go`. It must NOT be executed: THREE blocking questions stand, OQ-02 (the inheritance route resolving zero as sequenced), OQ-03 (the sibling-02 ordering payoff), and OQ-04 (the parent's dependency-edge defect), so `aw ipd lint` refuses it at every checkpoint until they are answered and a human then sets it `approved`. Answer them with `/askme`; OQ-04 is decided ONCE at the parent.

IT CARRIES `- Item-Dependencies: executed:lkexaw`, AND THAT EDGE IS THE PARENT'S BLOCKING DEFECT rather than a settled choice. The authored justification read: "deciding values before the gate and the scaffold fix exist would write values nothing enforces and leave the root cause in place." THAT REASONING DOES NOT SURVIVE THE PARENT'S MEASUREMENT and is retained only so the correction is visible: a value written before the gate exists is precisely what the gate then finds satisfied. The circularity is sharper here than for sibling 02, because 13 of the 18 plans the gate strands have no source and can therefore be unblocked ONLY by this plan. See OQ-04.

IT IS ORDER-SAFE BUT NOT ORDER-NEUTRAL WITH RESPECT TO SIBLING 02. The authored claim that it "is INDEPENDENT of sibling 02 and may run before, after or concurrently" is true for CORRECTNESS (E-01 tests for the fields, so nothing is double-written either way) and FALSE FOR COST: measured, two orchestrators in this population get their values from sibling 02, so 4 children can be derived for free if 02 has run and become 4 needless human confirmations if it has not. See OQ-03.

Execution contract for whoever runs it: commit ONLY paths under the declared `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. Pass `--no-commit` on every setter call so the tool never offers a commit mid-loop.

NOTE THE ONE JUDGEMENT HAZARD: this plan asks a human to confirm a table it composed, and this plan's own four plans are in that table. Recommend them on the same basis as every other plan. A recommendation that quietly gives this Set's own work a higher priority than it argued for elsewhere is the failure to avoid. Under the corrected route the four collapse into a single row (a decision on orchestrator `d0cbt3`), which makes the conflict easier for the maintainer to see rather than harder.

SIX CORRECTIONS FROM REVIEW THAT MUST NOT BE RE-INHERITED, each measured rather than reasoned:

1. DECIDE ORCHESTRATORS BEFORE DERIVING CHILDREN. As sequenced, Set inheritance resolved 0 of 28 plans, because no orchestrator carries both fields yet. That is blocking OQ-02, and the restructure into partition / decide / write / derive is what makes the measured 13-decisions-for-28-plans reduction real.
2. SELECT BY id6, NEVER BY SETID. 3 of the 10 setids here also name a terminal plan, and `aw ipd set approved runanalytics --dry-run` reports `executed -> approved` on `xbwq8n` in `executed/`. Backlog `f5pttg` records this having reverted seven executed plans for real. The temptation is acute because this plan reasons in Sets.
3. PASS `--message`, OR THE SETTER FABRICATES A HISTORY LINE. 13 of the 28 are `approved`, so this is the majority of the population; sibling 02's blocking OQ-02 owns whether that is acceptable and this plan inherits the answer.
4. DO NOT RE-QUOTE ANY COUNT. The title's 20, the authored 24 and review's 28 are all historical; E-01 derives a fourth.
5. DO NOT STALL OR SELF-APPROVE UNDER A RUNNER. There is no human in a runner turn; E-03 records the table and defers, and a fabricated confirmation is a failed validation.
6. DO NOT REQUIRE `aw check plans` CLEAN, and do not read the Priority column from a piped `aw att`. The sweep carries 140 pre-existing errors; the piped board has no such column.
