# IPD: Re-derive a plan's target population at execution time instead of trusting an authored id list

- Date: 2026-09-12
- Kind: child
- Concern: A PLAN'S SUCCESS CRITERION NAMES A POPULATION THAT WAS MEASURED WHEN THE PLAN WAS WRITTEN, SO AN EXECUTOR CAN SATISFY IT BY DOING NOTHING. Found 2026-09-12 while answering the maintainer's question about `qhy3i3` E-07, and it is not hypothetical: E-07's `Expected outcome` reads "for each of the FIVE MEASURED PLANS, the stale finding is reported ... `subject_gating_blocks` then returns empty", naming `4h7tt0` PR-002, `kbqpkn` PR-801, `5lxvl3` PR-002, `y9vpvv` PR-904 and `daexj1` PR-401. MEASURED at HEAD: ALL FIVE now return ZERO gating findings, having been cleared by the maintainer's two manual passes on 2026-09-10. So an executor that validates against that criterion finds nothing to fix, reports E-07 complete, and has fixed nothing.
  MEANWHILE THE DEFECT IS LIVE SOMEWHERE THE LIST DOES NOT MENTION, which is what makes this more than untidiness. On 2026-09-12 `aw set approved` refused a 94-plan batch on `fduoj4` alone, whose PR-702 had been answered on 2026-09-10 and whose finding row still read `OPEN`: a SIXTH instance of exactly the defect E-07 exists to fix, created after E-07 was authored. E-07 as written would have skipped it. The plan would have passed its own validation while the bug that motivated it blocked a real command.
  THE PLAN IS ALREADY HALF-RIGHT, AND THE ASYMMETRY IS THE DEFECT. E-07's INSTRUCTION says "for each plan, match a resolved question's `- Finding: <ID>` against the review record's current-round findings", which is correct and population-independent. Only its `Expected outcome` names the five. Its sibling E-06 gets this right, requiring "a RE-MEASURED per-plan table", so the correct shape is already present in the same plan and E-07 diverges from it.
  E-06 IS NOW EXPOSED TOO, BY TODAY'S OWN WORK. Its criterion is `aw att --type plan --readiness no-go` being empty, and that board went empty on 2026-09-12 when five plans were cleared. So E-06 can also now report success having changed nothing. That is not a flaw in E-06's wording, which correctly says re-measured; it is what happens when a criterion is a repo-state SNAPSHOT rather than a property.
  THE PATTERN IS NARROWER THAN IT FIRST LOOKS, WHICH BOUNDS THIS PLAN. 56 `Expected outcome` lines across `pending/` carry a hardcoded count, but most count CODE facts that do not drift (`4h7tt0`'s "four measured test assertions", `8hald1`'s "fourteen-key core"). Verified: of the four plans whose criterion names a measured PLAN population, only `qhy3i3` counts LIVE ARTIFACTS. So the fix is a convention plus one plan's repair, not a 56-plan sweep.
- Scope: Repair `qhy3i3` E-07's and E-06's success criteria so they state a PROPERTY rather than a snapshot population, and record the convention where a future author will read it, so a criterion counting live artifacts is written re-derived from the start. EXCLUDES the 52 criteria that count stable CODE facts (test assertions, schema keys), which do not drift and are correct as written; EXCLUDES executing `qhy3i3` itself; and EXCLUDES any change to `plan_readiness` or `review_findings` behavior, since this is an authoring-contract defect and not a code defect.
- Scope-Paths: .aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md, .aw/records/specs/, .aw/system/workflows/plan-review/plan-review.md
- Item-Dependencies: none
- Status: to-review
- Priority: medium
- Work-Kind: bug
- Blocks-Release: next
- Set: stalecrit
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: tgop8e

## Workflow history
- 2026-09-13 to-review (aw set): Authored 2026-09-12 from a maintainer question about what 're-derive the population' meant, filed as an IPD at their instruction rather than a backlog item. THE DEFECT: qhy3i3 E-07's Expected outcome names five measured plans, and all five return zero gating findings today, so an executor validating against that criterion fixes nothing and passes; meanwhile fduoj4 PR-702, a sixth instance created after E-07 was authored, refused a 94-plan approval batch hours ago. The plan's INSTRUCTION is already correct and population-independent, so only the BAR is wrong, and sibling E-06 gets it right, which is the asymmetry. E-06 is now exposed too because the no-go board went empty this session. Scoped on measurement: of 56 hardcoded counts in pending Expected outcome lines, only qhy3i3's counts live artifacts, so this is a convention plus one repair rather than a 56-plan sweep. Review-ready: no TODO placeholders, E/V bijection 3/3, every V-item demands pasted evidence, and OQ-01 records that this adds no dependency edge on qhy3i3.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a plan's success criterion something an executor cannot satisfy by doing nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: repair the criteria, then record the convention

- [ ] E-01 REWRITE `qhy3i3` E-07's AND E-06's `Expected outcome` SO THEY STATE A PROPERTY, NOT A POPULATION.
  E-07 TODAY reads "for each of the FIVE MEASURED PLANS ... `subject_gating_blocks` then returns empty". Replace with a property that holds whatever the population turns out to be: every plan carrying a RESOLVED blocking question whose `- Finding: <ID>` names a finding still unresolved in its review record's CURRENT round is reported, and under `--apply` each is marked `fixed`; afterwards NO such plan remains. State the enumeration as CONTEXT ("five were measured at authoring on 2026-09-10; re-derive at execution") rather than as the bar.
  E-06's WORDING IS ALREADY CORRECT ("a RE-MEASURED per-plan table") AND ITS CRITERION IS NOT: `aw att --type plan --readiness no-go` being empty became TRUE on 2026-09-12 independently of this plan, so it can now be satisfied by doing nothing. Add that the table must be produced and NON-VACUOUS, or state explicitly that an empty board is an acceptable outcome ONLY when accompanied by the per-plan rows showing why each plan left the board.
  DO NOT DELETE THE MEASURED IDS. They are real evidence of when the defect existed and they let a reader check the author's reasoning; demote them from criterion to context. Deleting them would trade one honesty problem for another.
  KEEP THE INSTRUCTIONS AS THEY ARE. E-07's instruction ("for each plan, match a resolved question's `- Finding: <ID>` ...") is already population-independent and correct; this item changes the BAR, not the method.
  - Depends on: none
  - Expected outcome: both criteria state a property with the authored counts demoted to context, the instructions unchanged, and `aw ipd lint` conforming on `qhy3i3`.
  - Execution state: pending

- [ ] E-02 ADD A GUARD SO A VACUOUS PASS IS VISIBLE, because a corrected criterion still cannot force an executor to notice an empty population.
  THE FAILURE THIS FENCES is a run that reports success having changed nothing, which is what both items could do today. The cheapest honest guard is to require the executor to REPORT THE DERIVED POPULATION SIZE before acting, and to state explicitly when it is zero, so "nothing to do" becomes an observation rather than a silent pass. A validation item that accepts "0 found, 0 fixed" without that statement cannot distinguish a clean repo from a broken query.
  DECIDE WHETHER ZERO IS A PASS OR A REFUSAL, AND RECORD IT. For E-07 zero is legitimately a pass (the stale findings may genuinely all be cleared, as they are today). For a plan whose whole purpose is to fix a measured population, zero should be a REFUSAL prompting re-measurement, because it more likely means the query drifted than that the work vanished. Do not apply one answer to both without saying why.
  - Depends on: E-01
  - Expected outcome: each repaired criterion requires the derived population size to be reported, with zero explicitly stated, and each records whether zero passes or refuses and why.
  - Execution state: pending

- [ ] E-03 RECORD THE CONVENTION WHERE A FUTURE AUTHOR WILL READ IT, so this is fixed once rather than per plan.
  THE RULE TO WRITE, in one or two sentences: an `Expected outcome` that counts LIVE ARTIFACTS must state the property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. A count of stable CODE facts (test assertions, schema keys, enum members) is exempt, which is why this is a narrow rule and not a ban on numbers.
  PUT IT WHERE THE LINTER OR THE REVIEWER WILL SEE IT. Candidates, in order of reach: the `ipd-spec` doc under `.aw/records/specs/` (the structural contract `aw ipd lint` implements), and `plan-review.md`'s finalize checklist (which already checks that validation items demand concrete evidence). Choose ONE primary home and cite it from the other rather than duplicating the rule, which is the drift this repo's reporting-contract parity test exists to prevent.
  DO NOT ATTEMPT A LINT RULE FOR IT. Deciding whether a number counts artifacts or code facts requires reading the sentence, so a mechanical check would either miss most cases or flag the 52 legitimate ones. State the convention and let review enforce it; say so explicitly, so a later reader does not mistake the absence of a lint rule for an oversight.
  - Depends on: E-02
  - Expected outcome: the convention recorded in ONE primary home with the code-facts exemption stated, cited from the second surface, and an explicit note that no lint rule is attempted and why.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ORDER 07 IS THE AUTHORITY AND IT IS ALREADY `implemented`: spec `20260817-2124-01-records-taxonomy-cleanup` (`u7xtni`), history line "run-artifacts -> `.aw/workflow-artifacts/`". This Set DELIVERS that decision; it does not revisit it.
- RUN SCRATCH IS UNTRACKED BECAUSE OF D92: run records carry local context, absolute home paths and session detail, so committing them publishes machine identity into permanent history. That is the reason, and it is why "just track it" is not an option.
- THIS REPO'S ROOT `.gitignore:62-68` ALREADY ENCODES THE TARGET STATE and is the best statement of intent in the tree, but it is NOT shipped: a target repo receives the framework-owned `.aw/.gitignore` instead. Never cite the root file as evidence that a target repo is protected.
- PATTERNS IN `.aw/.gitignore` ARE `.aw/`-RELATIVE AND MUST BE ANCHORED. The template's own `/inbox/` comment records the measured reason: a bare `inbox/` matched at any depth and silently swallowed the TRACKED `records/comms/shared/inbox/` lane, breaking `aw install`.
- `_ensure_aw_gitignore` IS THE ONLY PATH THAT REACHES AN ALREADY-INSTALLED REPO, because a repo that already has a `.aw/.gitignore` never re-reads the template. Every prior addition in that function carries a comment saying exactly this.
- `install_into_repo` IS THE SHARED CHOKEPOINT for every entry point (`aw install` via `engine.run()`, `aw setup` via `cli._run_setup` -> `cli._install_one`, and library callers). Wiring into `run()` reaches only one of them.
- `.aw/records/` IS TRACKED DURABLE RECORDS, NOT SCRATCH: `records/reviews/` alone holds 170 typed `.review.md` files. An agent already mistook it for the scratch home and moved run records into `.aw/records/reviews/untracked/`.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | E-07's criterion is already vacuous | It names five plans (`4h7tt0`, `kbqpkn`, `5lxvl3`, `y9vpvv`, `daexj1`); ALL FIVE return zero gating findings today, cleared by the maintainer's manual passes of 2026-09-10. An executor validating against it fixes nothing and passes. | `subject_gating_blocks` run on all five at authoring |
| F-2 | HIGH | the defect it targets is live where the list does not look | `fduoj4` PR-702 refused a 94-plan `aw set approved` batch on 2026-09-12; answered 2026-09-10, finding row still `OPEN`. A SIXTH instance, created after E-07 was authored, which E-07 as written would skip. | the failed batch; the plan's resolved OQ-03 |
| F-3 | MEDIUM | the instruction and the criterion disagree | E-07's instruction is population-independent ("for each plan, match a resolved question's `- Finding: <ID>` ..."), only its `Expected outcome` names the five. So the method is right and the bar is wrong. | the item text |
| F-4 | MEDIUM | the correct shape is already in the same plan | Sibling E-06 requires "a RE-MEASURED per-plan table", so E-07 diverges from a convention its own plan follows elsewhere. | E-06's expected outcome |
| F-5 | MEDIUM | E-06 is now exposed by today's work | Its criterion is `aw att --type plan --readiness no-go` being empty; that board went empty on 2026-09-12 when five plans were cleared, so it too can pass having changed nothing. Its WORDING is correct; the criterion is a snapshot. | `aw att` run at authoring |
| F-6 | LOW | the pattern is narrower than a raw grep suggests | 56 `Expected outcome` lines carry a hardcoded count, but most count stable CODE facts (`4h7tt0` "four measured test assertions", `8hald1` "fourteen-key core"). Of the four naming a measured PLAN population, only `qhy3i3` counts live artifacts. | both greps plus a read of each |

## Proposed changes (ordered, validatable)

1. Rewrite `qhy3i3` E-07's and E-06's criteria as properties, demoting the authored ids to context (E-01).
2. Require the derived population size to be reported, and record whether zero passes or refuses, per item (E-02).
3. Record the convention in one primary home with the code-facts exemption, cited from the second surface (E-03).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan does not execute `qhy3i3`, does not touch the 52 criteria counting stable code facts, does not change `plan_readiness` or `review_findings` behavior (this is an authoring-contract defect, not a code defect), and deliberately attempts NO lint rule, for the reason E-03 states.

## Required tests / validation

- BOTH REPAIRED CRITERIA state a property, with the authored ids surviving as context and the instruction lines unchanged; `aw ipd lint` conforming on `qhy3i3`.
- THE ZERO CASE IS DECIDED PER ITEM with its reason, not by one blanket answer, since E-07 and a measured-population plan legitimately differ.
- THE CONVENTION DISCRIMINATES, demonstrated on one criterion it flags (`qhy3i3` E-07 as authored) and one it exempts (`8hald1`'s fourteen-key core).
- THE RULE IS NOT DUPLICATED across its two surfaces; the second cites the first.
- `python3 -m pytest` BARE, failure-SET delta empty (this plan edits records and docs, so no delta is expected; run it to prove that).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE CONVENTION IS THE DELIVERABLE, so E-03 IS the spec-sync work rather than a trailing obligation, and it must land in ONE primary home: the `ipd-spec` doc under `.aw/records/specs/` (the structural contract `aw ipd lint` implements) or `plan-review.md`'s finalize checklist (which already requires validation items to demand concrete evidence). Cite from the other; do not duplicate, which is the drift the reporting-contract parity test exists to catch.

NOTE THIS AMENDS AN APPROVED-BY-USE CONTRACT, so the choice of home matters: `plan-review.md` reaches every reviewer on every plan, while the spec reaches the linter's authority. E-03 must state which was chosen and why, rather than leaving a reader to infer it.

## Open questions

### OQ-01: Should `qhy3i3` be executed before or after this repair?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: AFTER, AND THIS PLAN DOES NOT BLOCK ITS APPROVAL. Resolved from what the two plans actually do rather than asked, because the maintainer already put the sequencing question ("Should I run qhy3i3 first?") and the answer was measured then: `qhy3i3` E-07's INSTRUCTION is correct and population-independent, so an executor following the instruction rather than the criterion does the right thing today. What this plan fixes is the BAR that would let a careless run pass vacuously.
  SO THE ORDER IS A PREFERENCE, NOT A DEPENDENCY, and `- Item-Dependencies:` is deliberately `none`. If `qhy3i3` runs first, its executor must re-derive anyway per its own instruction, and this plan then repairs a criterion already satisfied honestly. If this plan runs first, `qhy3i3`'s executor gets an unambiguous bar. The second is better and neither is wrong.
  DO NOT ADD A DEPENDENCY EDGE TO FORCE THE PREFERENCE. Measured cost of doing so: `qhy3i3` is approved and queued with 93 other plans, and an edge would strand it behind a plan authored minutes ago for a benefit its own instruction already delivers. NOT BLOCKING.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both `Expected outcome` lines BEFORE and AFTER. Confirm by quotation that neither states a fixed population as the bar, that the authored ids survive as context, and that E-07's instruction line is UNCHANGED. Paste `aw ipd lint` on `qhy3i3` showing conforming. A criterion still naming "the five measured plans" as the bar is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: quote the added requirement from each repaired criterion, showing the derived population size must be reported and zero explicitly stated. Quote the recorded zero-is-pass-or-refusal decision for EACH item with its reason; a single blanket answer applied to both without justification is a FAILED validation, since E-07 and a measured-population plan differ on this point.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the recorded convention verbatim from its primary home, showing both the rule and the code-facts exemption. Paste the citation from the second surface and confirm the rule is NOT duplicated there. Quote the note explaining why no lint rule is attempted. Then demonstrate the rule discriminates: name one criterion it would flag (`qhy3i3` E-07 as authored) and one it correctly exempts (`8hald1`'s "fourteen-key core"), so it is shown to be narrow rather than a ban on counting.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
