# IPD: Re-derive a plan's target population at execution time instead of trusting an authored id list

- Date: 2026-09-12
- Kind: child
- Concern: A PLAN'S SUCCESS CRITERION NAMES A POPULATION THAT WAS MEASURED WHEN THE PLAN WAS WRITTEN, SO AN EXECUTOR CAN SATISFY IT BY DOING NOTHING. Found 2026-09-12 while answering the maintainer's question about `qhy3i3` E-07, and it is not hypothetical: E-07's `Expected outcome` reads "for each of the FIVE MEASURED PLANS, the stale finding is reported ... `subject_gating_blocks` then returns empty", naming `4h7tt0` PR-002, `kbqpkn` PR-801, `5lxvl3` PR-002, `y9vpvv` PR-904 and `daexj1` PR-401. MEASURED at HEAD: ALL FIVE now return ZERO gating findings, having been cleared by the maintainer's two manual passes on 2026-09-10. So an executor that validates against that criterion finds nothing to fix, reports E-07 complete, and has fixed nothing.
  MEANWHILE THE DEFECT IS LIVE SOMEWHERE THE LIST DOES NOT MENTION, which is what makes this more than untidiness. On 2026-09-12 `aw set approved` refused a 94-plan batch on `fduoj4` alone, whose PR-702 had been answered on 2026-09-10 and whose finding row still read `OPEN`: a SIXTH instance of exactly the defect E-07 exists to fix, created after E-07 was authored. E-07 as written would have skipped it. The plan would have passed its own validation while the bug that motivated it blocked a real command.
  THE PLAN IS ALREADY HALF-RIGHT, AND THE ASYMMETRY IS THE DEFECT. E-07's INSTRUCTION says "for each plan, match a resolved question's `- Finding: <ID>` against the review record's current-round findings", which is correct and population-independent. Only its `Expected outcome` names the five. Its sibling E-06 gets this right, requiring "a RE-MEASURED per-plan table", so the correct shape is already present in the same plan and E-07 diverges from it.
  E-06 IS NOW EXPOSED TOO, BY TODAY'S OWN WORK. Its criterion is `aw att --type plan --readiness no-go` being empty, and that board went empty on 2026-09-12 when five plans were cleared. So E-06 can also now report success having changed nothing. That is not a flaw in E-06's wording, which correctly says re-measured; it is what happens when a criterion is a repo-state SNAPSHOT rather than a property.
  THE PATTERN IS NARROWER THAN IT FIRST LOOKS, WHICH BOUNDS THIS PLAN. Re-measured at review because the authored figures did not reproduce (PR-004): `pending/` holds 690 `Expected outcome` lines, of which 169 carry a digit and 224 a spelled number, so the authored "56 with a hardcoded count" understates the raw population by roughly a factor of four. The BOUND still holds and is what matters: of the 17 criteria that count a plan/child/item population, most are an orchestrator counting its own DECLARED children (a fixed authored fact, not a drifting live one), and only `qhy3i3` and `vhbvwz` count LIVE ARTIFACTS. So the fix remains a convention plus one plan's repair; the corrected numbers are in F-6.
  THE POPULATION IS NOT EMPTY TODAY, WHICH INVERTS THE PLAN'S OWN FRAMING (PR-002). The authored Concern says an executor "finds nothing to fix" because all five named plans return zero. The five DO return zero, verified. But re-derived at review across all 65 plans carrying a `- Finding:` escalation, `subject_gating_blocks` returns NON-EMPTY for FOUR plans: `ki6tom` PR-201, `32ij2j` PR-016 and PR-017, `xtklpd` PR-023, `yku4ga` PR-701. Of those, `ki6tom` PR-201 and `yku4ga` PR-701 sit behind questions that are `- Status: resolved`, so they are EXACTLY the stale-bookkeeping defect E-07 exists to close, and they are live right now. The other three are behind questions still genuinely `open` and MUST NOT be touched, which is the negative case V-07 already demands. So E-07 has real work, its authored list would miss all of it, and the zero-is-a-pass reasoning E-02 was about to record for it is FALSE.
- Scope: Repair `qhy3i3` E-07's and E-06's success criteria so they state a PROPERTY rather than a snapshot population, and record the convention where a future author will read it, so a criterion counting live artifacts is written re-derived from the start. EXCLUDES the criteria that count stable CODE facts (test assertions, schema keys) or an orchestrator's own declared children, which do not drift and are correct as written; EXCLUDES executing `qhy3i3` itself; and EXCLUDES any change to `plan_readiness` or `review_findings` behavior, since this is an authoring-contract defect and not a code defect.
- Scope-Paths: .aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md, .aw/records/specs/, .aw/system/workflows/plan-review/plan-review.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Priority: medium
- Work-Kind: bug
- Blocks-Release: next
- Set: stalecrit
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: tgop8e
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-13 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review at HEAD 3dd2047d; APPROVE WITH REVISIONS APPLIED, readiness go-pending-approval. PR-001..PR-007 all FIXED in place, none deferred, none REPLAN; D-1..D-4 recorded. aw ipd lint CONFORMING at --phase author before review and --phase review-finalize after every revision; suite BARE 5971 passed, 3 skipped, 2 xfailed; aw sanitize clean. NEAR-SELF-REVIEW, so the plan's claims were EXECUTED rather than re-read, and four measurements contradicted it. (1) PR-002, the one that changes what an executor does: the thesis is right and the PREMISE IS INVERTED. The five plans E-07 names do all return zero (F-1 confirmed), but re-derived over all 65 plans carrying a - Finding: escalation, subject_gating_blocks is NON-EMPTY for four, and ki6tom PR-201 plus yku4ga PR-701 sit behind RESOLVED questions, so they are E-07's live target right now while 32ij2j and xtklpd are behind still-open questions and must not be touched. E-07 has real work its authored list misses, and E-02 was about to record 'zero is a pass, as it is today' as a decision resting on a falsified premise; the zero rule now requires the DENOMINATOR so a broken query cannot pass as a clean repo. (2) PR-003/PR-005 rest on one measurement the plan needed and lacked: an Expected outcome line is OUTSIDE the frozen requirement digest (frozen_region_digest d5380e65acf1a485 unchanged across the repair, changed when action text is edited), and qhy3i3 has no begin receipt among the 24 on disk. That both de-risks editing an APPROVED plan and DECIDES E-03's open choice of home, since review is the only enforcement surface that can exist: plan-review.md rubric G is now primary with a one-sentence pointer in ipd-spec. Guardrails added for the approved-plan edit: no Status/Approval/Readiness touched, no action text touched, digest equality proven, edit recorded in qhy3i3's own history. (3) PR-001: the Project conventions and Deferred sections were BYTE-IDENTICAL to wfartifacts child gzhd7t, and the gate carried that Set's run-records prohibition; the same defect on the same two sections from the same source was fixed on 4y95tp days earlier, so it is a copy habit, recorded as F-8. (4) PR-004: the 56/52 counts do not reproduce (690 Expected outcome lines, 169 with a digit, 224 spelled), and 52 was never a measurement; the BOUND survives, so exclusions now name the CLASS rather than a count, and F-7 records that vhbvwz's live-artifact count has ALREADY drifted 273->300, the plan's own thesis on an artifact it excludes. OQ-01 corrected to resolved (PR-006): its body said resolved while its field said open. Preserved unchanged: the diagnosis, the instruction/criterion asymmetry, keeping the measured ids as context, no dependency edge on qhy3i3, and no lint rule.
- 2026-09-13 to-review (aw set): Authored 2026-09-12 from a maintainer question about what 're-derive the population' meant, filed as an IPD at their instruction rather than a backlog item. THE DEFECT: qhy3i3 E-07's Expected outcome names five measured plans, and all five return zero gating findings today, so an executor validating against that criterion fixes nothing and passes; meanwhile fduoj4 PR-702, a sixth instance created after E-07 was authored, refused a 94-plan approval batch hours ago. The plan's INSTRUCTION is already correct and population-independent, so only the BAR is wrong, and sibling E-06 gets it right, which is the asymmetry. E-06 is now exposed too because the no-go board went empty this session. Scoped on measurement: of 56 hardcoded counts in pending Expected outcome lines, only qhy3i3's counts live artifacts, so this is a convention plus one repair rather than a 56-plan sweep. Review-ready: no TODO placeholders, E/V bijection 3/3, every V-item demands pasted evidence, and OQ-01 records that this adds no dependency edge on qhy3i3.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a plan's success criterion something an executor cannot satisfy by doing nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: repair the criteria, then record the convention

- [x] E-01 REWRITE `qhy3i3` E-07's AND E-06's `Expected outcome` SO THEY STATE A PROPERTY, NOT A POPULATION.
  E-07 TODAY reads "for each of the FIVE MEASURED PLANS ... `subject_gating_blocks` then returns empty". Replace with a property that holds whatever the population turns out to be: every plan carrying a RESOLVED blocking question whose `- Finding: <ID>` names a finding still unresolved in its review record's CURRENT round is reported, and under `--apply` each is marked `fixed`; afterwards NO such plan remains. State the enumeration as CONTEXT ("five were measured at authoring on 2026-09-10; re-derive at execution") rather than as the bar.
  E-06's WORDING IS ALREADY CORRECT ("a RE-MEASURED per-plan table") AND ITS CRITERION IS NOT: `aw att --type plan --readiness no-go` being empty became TRUE on 2026-09-12 independently of this plan, so it can now be satisfied by doing nothing. Add that the table must be produced and NON-VACUOUS, or state explicitly that an empty board is an acceptable outcome ONLY when accompanied by the per-plan rows showing why each plan left the board.
  DO NOT DELETE THE MEASURED IDS. They are real evidence of when the defect existed and they let a reader check the author's reasoning; demote them from criterion to context. Deleting them would trade one honesty problem for another.
  KEEP THE INSTRUCTIONS AS THEY ARE. E-07's instruction ("for each plan, match a resolved question's `- Finding: <ID>` ...") is already population-independent and correct; this item changes the BAR, not the method.
  CARRY THE RE-DERIVED POPULATION INTO E-07's CONTEXT, since review measured it and an executor should not have to (PR-002). State that at 2026-09-12 the five named plans returned zero while `subject_gating_blocks` returned non-empty for `ki6tom` PR-201 and `yku4ga` PR-701 behind RESOLVED questions (the live stale-bookkeeping cases) and for `32ij2j` PR-016/PR-017 and `xtklpd` PR-023 behind questions still `open` (which must NOT be touched). Mark this measurement as CONTEXT carrying the same re-derive instruction, not as a new bar; it will drift exactly as the first list did.
  THIS EDITS AN APPROVED PLAN, SO RECORD IT THERE (PR-003). `qhy3i3` is `Status: approved` with a human `- Approval:` line. Append a `## Workflow history` record to `qhy3i3` naming this plan (`tgop8e`) as the author of the change and stating that only criteria and context were touched, no E-item action text and no `Scope-Paths`. Do NOT alter its `- Status:`, its `- Approval:`, or its `- Readiness:`: those are attestations owned by other roles.
  - Depends on: none
  - Expected outcome: both criteria state a property with the authored counts demoted to context, the re-derived population carried as context, the instructions unchanged, a history record added to `qhy3i3` attributing the edit, its `Status`/`Approval`/`Readiness` byte-unchanged, and `aw ipd lint` conforming on `qhy3i3`.
  - Execution state: performed

- [x] E-02 ADD A GUARD SO A VACUOUS PASS IS VISIBLE, because a corrected criterion still cannot force an executor to notice an empty population.
  THE FAILURE THIS FENCES is a run that reports success having changed nothing, which is what both items could do today. The cheapest honest guard is to require the executor to REPORT THE DERIVED POPULATION SIZE before acting, and to state explicitly when it is zero, so "nothing to do" becomes an observation rather than a silent pass. A validation item that accepts "0 found, 0 fixed" without that statement cannot distinguish a clean repo from a broken query.
  DECIDE WHETHER ZERO IS A PASS OR A REFUSAL, AND RECORD IT, PER ITEM. The authored reasoning for E-07 was "zero is legitimately a pass, as it is today"; that premise is FALSE and was corrected at review (PR-002): re-derived across all 65 plans carrying a `- Finding:` escalation, the population is FOUR plans, two of them (`ki6tom` PR-201, `yku4ga` PR-701) behind RESOLVED questions and therefore exactly E-07's target. So do NOT write "zero is expected" into E-07.
  THE HONEST RULE, WHICH IS NEITHER OF THE TWO AUTHORED ANSWERS: zero is a pass ONLY when the executor also shows the QUERY WORKED. A bare "0 found, 0 fixed" cannot distinguish a clean repo from a broken predicate, which is the very confusion this plan exists to end. Require the executor to paste the derived population WITH its denominator (how many plans were examined, e.g. "65 plans carry a `- Finding:` escalation; 4 return non-empty; 2 of those sit behind resolved questions"), so a zero is corroborated by a non-zero denominator. Under that rule zero passes for E-07 and a silent zero does not.
  FOR E-06 STATE THE SAME SHAPE AGAINST ITS OWN BOARD: an empty `aw att --type plan --readiness no-go` passes only alongside the per-plan rows showing why each plan left the board, which is the non-vacuity requirement E-01 adds.
  - Depends on: E-01
  - Expected outcome: each repaired criterion requires the derived population size to be reported WITH its denominator and zero explicitly stated, each records whether zero passes or refuses and why, and E-07's recorded reason does not rest on the falsified "the population is empty today" premise.
  - Execution state: performed

- [x] E-03 RECORD THE CONVENTION WHERE A FUTURE AUTHOR WILL READ IT, so this is fixed once rather than per plan.
  THE RULE TO WRITE, in one or two sentences: an `Expected outcome` that counts LIVE ARTIFACTS must state the property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. A count of stable CODE facts (test assertions, schema keys, enum members) is exempt, which is why this is a narrow rule and not a ban on numbers.
  THE PRIMARY HOME IS `plan-review.md`, DECIDED AT REVIEW RATHER THAN LEFT TO THE EXECUTOR (PR-005). The authored item offered two candidates and deferred the choice; the choice follows mechanically from this plan's own decision not to build a lint rule. The `ipd-spec` doc is the contract `aw ipd lint` IMPLEMENTS, so a rule sited there asserts an obligation the linter does not check and cannot check, and `ipd-spec` is `Status: implemented`, making an edit there a spec amendment with a heavier gate. `plan-review.md` is where a REVIEWER reads, and review is the only enforcer this rule will ever have; its rubric section G already carries the sibling requirement that validation items demand concrete evidence, which is the right neighbor. Site the rule in section G beside that requirement.
  CITE IT FROM THE `ipd-spec` DOC IN ONE SENTENCE, do not restate it, which is the anti-duplication rule the reporting-contract parity test exists to enforce. If that citation would require amending an `implemented` spec beyond a single pointer sentence, STOP at the pointer and say so in the plan record.
  DO NOT ATTEMPT A LINT RULE FOR IT. Deciding whether a number counts artifacts or code facts requires reading the sentence, so a mechanical check would either miss most cases or flag the many legitimate ones. This is confirmed mechanically, not merely asserted: an `Expected outcome` line is OUTSIDE the frozen requirement digest (see the conventions section), so no existing gate reads it and review is the ONLY enforcement surface available. State the convention and let review enforce it; say so explicitly, so a later reader does not mistake the absence of a lint rule for an oversight.
  - Depends on: E-02
  - Expected outcome: the convention recorded in `plan-review.md` rubric section G with the code-facts exemption stated, a one-sentence pointer added to the `ipd-spec` doc without restating the rule, and an explicit note that no lint rule is attempted and why.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CORRECTED AT REVIEW (PR-001): this whole section was previously a BYTE-IDENTICAL COPY of the conventions block from `wfartifacts` child `gzhd7t`, an unrelated Set about relocating run scratch to `.aw/workflow-artifacts/`. Nothing in it described this plan. The identical defect was caught and fixed on `4y95tp` days earlier (its PR-003), so this is a recurrence, not a novelty; the entries below are what review actually measured about THIS plan's subject.
- AN `Expected outcome` LINE IS NOT PART OF THE FROZEN CONTRACT, WHICH IS THE MECHANICAL FACT THAT SHAPES THIS PLAN. `ipd_lifecycle._requirements_from_plan` freezes only `Scope-Paths`, each E-leaf's `.text`, and each V-leaf's `.text`, and `ipd_lint.parse` puts an indented `- Key: value` sub-field in `Leaf.fields` while `.text` is the ACTION LINE ALONE. MEASURED at review: rewriting `qhy3i3` E-07's `Expected outcome` leaves `frozen_region_digest` BYTE-IDENTICAL (`d5380e65...` before and after), while editing the E-07 action text DOES change it. Two consequences follow, and both matter here: the repair is safe against an existing begin receipt, AND no gate reads the criterion, so the convention E-03 records is enforced by REVIEW alone.
- A `V-*` LEAF'S FROZEN TEXT IS ONLY ITS HEADER LINE. Measured: `V-07`'s `.text` is exactly `V-07 validates E-07`, so the `Required evidence:` sub-field, which is where every real bar lives, is outside the digest too. So "strengthen the validation bar" is never blocked by a receipt, and equally never protected by one.
- `qhy3i3` IS `Status: approved` WITH A HUMAN `- Approval:` LINE, so editing it is editing an approved contract. It has NO begin receipt (`.aw/state/ipd-lifecycle/` holds 24 receipts, none for `qhy3i3`), so no frozen receipt can go stale; the concern is provenance, not mechanism, and E-01 must record what it changed in that plan's own history.
- `subject_gating_blocks` IS THE PRODUCTION PREDICATE and it takes `(repo, id6)`, returning a tuple of `GatingBlock`. Call it rather than re-implementing the match; the whole defect class this plan addresses is authored lists diverging from what that function returns.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | E-07's criterion is already vacuous | It names five plans (`4h7tt0`, `kbqpkn`, `5lxvl3`, `y9vpvv`, `daexj1`); ALL FIVE return zero gating findings today, cleared by the maintainer's manual passes of 2026-09-10. An executor validating against it fixes nothing and passes. CONFIRMED at review by re-running `subject_gating_blocks` on all five: each returns `()`. | `subject_gating_blocks` run on all five at authoring and again at review |
| F-1b | HIGH | but the population is NOT empty, which inverts the plan's framing | The Concern reasons from "an executor finds nothing to fix". Re-derived at review across all 65 plans carrying a `- Finding:` escalation, `subject_gating_blocks` is NON-EMPTY for four: `ki6tom` PR-201 and `yku4ga` PR-701 behind questions that are `- Status: resolved` (exactly E-07's stale-bookkeeping target, live now), plus `32ij2j` PR-016/PR-017 and `xtklpd` PR-023 behind questions still `open` (which must not be touched). So E-07 has real work its authored list misses entirely, and E-02's authored "zero is legitimately a pass, as it is today" rested on a false premise. | re-derivation over 65 plans at review |
| F-2 | HIGH | the defect it targets is live where the list does not look | `fduoj4` PR-702 refused a 94-plan `aw set approved` batch on 2026-09-12; answered 2026-09-10, finding row still `OPEN`. A SIXTH instance, created after E-07 was authored, which E-07 as written would skip. | the failed batch; the plan's resolved OQ-03 |
| F-3 | MEDIUM | the instruction and the criterion disagree | E-07's instruction is population-independent ("for each plan, match a resolved question's `- Finding: <ID>` ..."), only its `Expected outcome` names the five. So the method is right and the bar is wrong. | the item text |
| F-4 | MEDIUM | the correct shape is already in the same plan | Sibling E-06 requires "a RE-MEASURED per-plan table", so E-07 diverges from a convention its own plan follows elsewhere. | E-06's expected outcome |
| F-5 | MEDIUM | E-06 is now exposed by today's work | Its criterion is `aw att --type plan --readiness no-go` being empty; that board went empty on 2026-09-12 when five plans were cleared, so it too can pass having changed nothing. Its WORDING is correct; the criterion is a snapshot. | `aw att` run at authoring |
| F-6 | LOW | the pattern is narrower than a raw grep suggests, but the authored numbers were wrong | CORRECTED AT REVIEW. Re-measured: `pending/` holds 690 `Expected outcome` lines; 169 carry a digit, 224 a spelled number, so "56 with a hardcoded count" understated the raw population roughly fourfold and the derived "52 exempt" figure never existed. The BOUND survives: 17 criteria count a plan/child/item population, most being an orchestrator counting its OWN declared children (a fixed authored fact), and only `qhy3i3` and `vhbvwz` count live artifacts. | re-run at review over all 690 lines |
| F-7 | MEDIUM | a second live-artifact criterion exists, so `qhy3i3` is not unique | `vhbvwz` E-02's criterion is "the 273 currently-mismatching plans report correctly with zero files rewritten". Re-measured at review with the production readers (`attention._history_section_lines` + `attention_contract.HISTORY_RECORD_RE` + `last_history_at`): the count is now 300 of 601 multi-record plans, not 273. So a live-artifact count in an approved plan has ALREADY drifted by 27, which is this plan's thesis demonstrated on an artifact the plan says it excludes. NOT swept in here (it belongs to another Set); named as a follow-up so the exclusion is deliberate rather than an oversight. | measured at review |
| F-8 | MEDIUM | the copied-conventions defect is a recurrence across Sets, not a one-off | This plan's `## Project conventions` and `## Deferred` sections were byte-identical to `wfartifacts` child `gzhd7t`. The SAME defect was found and fixed on `4y95tp` (its PR-003, same two sections, same source Set). Two independent plans inheriting an unrelated Set's context indicates an authoring-time copy habit rather than a slip. Fixed here (PR-001); the cross-Set pattern is out of scope and recorded. | `diff` of both sections against `gzhd7t`; `4y95tp`'s review record |

## Proposed changes (ordered, validatable)

1. Rewrite `qhy3i3` E-07's and E-06's criteria as properties, demoting the authored ids to context, carrying the re-derived population as context, and recording the edit in that plan's own history without touching any attestation field (E-01).
2. Require the derived population size to be reported WITH its denominator, and record whether zero passes or refuses per item, without resting on the falsified empty-population premise (E-02).
3. Record the convention in `plan-review.md` rubric section G with the code-facts exemption, pointed to from the `ipd-spec` doc (E-03).

## Deferred / out of scope (with reason)

CORRECTED AT REVIEW (PR-001): this section was also a byte-identical copy from `wfartifacts` child `gzhd7t` (run scratch, D92, `tools/untrack-workflow-artifacts.py`, backlog `2812t3`, Order 05's deletion prohibition). None of it is touched by this plan. The exclusions below are this plan's real ones.

- EXECUTING `qhy3i3`. This plan repairs its criteria and does not run it. OQ-01 records why that is a preference rather than a dependency edge.
- ANY CHANGE TO `plan_readiness` OR `review_findings` BEHAVIOR. The defect is an authoring-contract defect: the predicate is right and the authored list is wrong. Deliberately excluded so the fix cannot become a code change nobody reviewed.
- A LINT RULE FOR THE CONVENTION. Deliberately not attempted, for the reason E-03 states: deciding whether a number counts artifacts or code facts requires reading the sentence.
- THE OTHER 16 CRITERIA THAT COUNT A PLAN/CHILD/ITEM POPULATION (re-measured at review; see F-6). Most are an orchestrator counting its OWN declared children, which is a fixed authored fact rather than a drifting live population, so they are correctly written. `vhbvwz`'s "the 273 currently-mismatching plans" is the one genuine sibling instance and is recorded in F-7 as a NAMED follow-up rather than swept in here, because it belongs to an approved plan in another Set.
- REPAIRING EVERY PLAN THAT COPIED A CONVENTIONS BLOCK FROM ANOTHER SET. This plan fixes its own (PR-001). The recurrence across Sets is a separate concern, noted in F-8.

## Scope check

- Over-scope: none. NOTE the declared `- Scope-Paths:` entry `.aw/records/specs/` is a DIRECTORY, so it permits editing any spec in the tree while E-03 needs exactly one (the `ipd-spec` doc). Verified at review that `ipd_lifecycle._scope_match` treats a trailing-slash entry as covering every path beneath it, so the fence is wider than the work. Left as-is deliberately, because narrowing it to a single spec file would edit a `Scope-Paths` entry and thereby change the frozen requirement digest; the executor is instead told below to touch only the `ipd-spec` doc and to justify anything else at `aw ipd finalize`.
- Under-scope, stated rather than left as `none`: this plan does not execute `qhy3i3`, does not touch the criteria counting stable code facts or an orchestrator's own declared children, does not change `plan_readiness` or `review_findings` behavior (this is an authoring-contract defect, not a code defect), does not repair `vhbvwz`'s already-drifted live-artifact count (F-7, another Set's approved plan), does not repair the other plans that copied a conventions block from an unrelated Set (F-8), and deliberately attempts NO lint rule, for the reason E-03 states.

## Required tests / validation

- BOTH REPAIRED CRITERIA state a property, with the authored ids surviving as context and the instruction lines unchanged; `aw ipd lint` conforming on `qhy3i3`.
- `qhy3i3`'s FROZEN REGION IS BYTE-UNCHANGED, proven by `ipd_lifecycle.frozen_region_digest` before and after the repair (they must be EQUAL, since only criteria and context change). A digest that CHANGED means an E-item action line or a `Scope-Paths` entry was edited, which this plan forbids, and is a FAILED validation.
- `qhy3i3`'s `- Status:`, `- Approval:` and `- Readiness:` LINES ARE BYTE-UNCHANGED, and a history record attributing the edit to `tgop8e` was appended.
- THE ZERO CASE IS DECIDED PER ITEM with its reason and its DENOMINATOR, not by one blanket answer, and E-07's reason does not assert the falsified "population is empty today" premise.
- THE CONVENTION DISCRIMINATES, demonstrated on one criterion it flags (`qhy3i3` E-07 as authored) and one it exempts (`8hald1`'s fourteen-key core).
- THE RULE IS NOT DUPLICATED across its two surfaces; the `ipd-spec` doc carries a one-sentence pointer only.
- `python3 -m pytest` BARE, failure-SET delta empty (this plan edits records and docs, so no delta is expected; run it to prove that).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE CONVENTION IS THE DELIVERABLE, so E-03 IS the spec-sync work rather than a trailing obligation. THE HOME IS DECIDED, not left open (PR-005): `plan-review.md` rubric section G is primary, and the `ipd-spec` doc gets a one-sentence pointer. The reason is that review is the ONLY enforcement surface this rule can have, which is not a preference but a measured fact: an `Expected outcome` line lies outside `ipd_lifecycle._requirements_from_plan`'s frozen digest, so no gate reads it. Siting the rule in `ipd-spec` would put an unenforceable obligation in the document `aw ipd lint` implements. Cite, do not duplicate, which is the drift the reporting-contract parity test exists to catch.

THE `ipd-spec` DOC IS `Status: implemented`, so touching it is a spec amendment and not a free edit. Keep it to the pointer sentence. The declared `- Scope-Paths:` includes `.aw/records/specs/` as a DIRECTORY, so the fence permits more than intended; touch ONLY the `ipd-spec` doc, and if any other spec is edited, justify it with `--scope-reason` at `aw ipd finalize` rather than treating the broad fence as permission. Note that `runner_shared.declared_spec_paths` recognizes a spec by the `.spec.md` facet, so a directory entry yields NO declared spec paths and the runner's pre-run spec-edit announcement will NOT name this amendment; the executor must therefore say plainly in the plan record that a spec was amended.

## Open questions

### OQ-01: Should `qhy3i3` be executed before or after this repair?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: AFTER, AND THIS PLAN DOES NOT BLOCK ITS APPROVAL. STATUS CORRECTED AT REVIEW (PR-006): this question was authored `- Status: open` while its own text says "Resolved from what the two plans actually do rather than asked" and reaches a firm answer, so the field contradicted the body. It is a recorded decision, not an outstanding one, and `resolved` is the honest value; leaving it `open` would have made `aw attention` count a decided question as outstanding work. Resolved from what the two plans actually do rather than asked, because the maintainer already put the sequencing question ("Should I run qhy3i3 first?") and the answer was measured then: `qhy3i3` E-07's INSTRUCTION is correct and population-independent, so an executor following the instruction rather than the criterion does the right thing today. What this plan fixes is the BAR that would let a careless run pass vacuously.
  SO THE ORDER IS A PREFERENCE, NOT A DEPENDENCY, and `- Item-Dependencies:` is deliberately `none`. If `qhy3i3` runs first, its executor must re-derive anyway per its own instruction, and this plan then repairs a criterion already satisfied honestly. If this plan runs first, `qhy3i3`'s executor gets an unambiguous bar. The second is better and neither is wrong.
  DO NOT ADD A DEPENDENCY EDGE TO FORCE THE PREFERENCE. Measured cost of doing so: `qhy3i3` is approved and queued with 93 other plans, and an edge would strand it behind a plan authored minutes ago for a benefit its own instruction already delivers. NOT BLOCKING.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste both `Expected outcome` lines BEFORE and AFTER. Confirm by quotation that neither states a fixed population as the bar, that the authored ids survive as context, and that E-07's instruction line is UNCHANGED. Paste `aw ipd lint` on `qhy3i3` showing conforming. A criterion still naming "the five measured plans" as the bar is a FAILED validation.
    ALSO paste `ipd_lifecycle.frozen_region_digest(qhy3i3_text)` BEFORE and AFTER, which must be EQUAL, proving no E-item action line and no `Scope-Paths` entry was touched; a CHANGED digest is a FAILED validation. Paste a `git diff` of `qhy3i3` confirming its `- Status:`, `- Approval:` and `- Readiness:` lines are byte-unchanged, and paste the appended history record attributing the edit to `tgop8e`. Paste the re-derived population carried into E-07's context, showing the four non-empty plans and which two sit behind resolved questions.
  - Observed evidence: BOTH EXPECTED OUTCOME LINES BEFORE AND AFTER:

    E-07 BEFORE:
    `  - Expected outcome: for each of the five measured plans, the stale finding is reported with the resolved question that settles it, and under `--apply` a new round marks it `fixed`; `subject_gating_blocks` then returns empty for that plan. Nothing is written without `--apply`.`

    E-07 AFTER:
    `  - Expected outcome: every plan carrying a RESOLVED blocking question whose `- Finding: <ID>` names a finding still unresolved in its review record's CURRENT round is reported with the resolved question that settles it, and under `--apply` each is marked `fixed` by appending a new round; afterwards NO such plan remains and `subject_gating_blocks` returns empty for each. Nothing is written without `--apply`. The derived population size must be reported WITH its denominator (total plans examined carrying a `- Finding:` escalation) and zero explicitly stated if empty; a zero count passes ONLY when corroborated by a non-zero denominator showing the query ran, rather than passing silently.`

    E-06 BEFORE:
    `  - Expected outcome: a re-measured per-plan table with the command that produced it, each row naming the three condition results and the action taken (updated, or refused with the specific surviving cause), plus `aw att --type plan --readiness no-go` before and after. Every refusal is explained rather than worked around.`

    E-06 AFTER:
    `  - Expected outcome: a re-measured per-plan table with the command that produced it, each row naming the three condition results and the action taken (updated, or refused with the specific surviving cause), plus `aw att --type plan --readiness no-go` before and after. Every refusal is explained rather than worked around. The table must be produced and NON-VACUOUS; an empty `aw att --type plan --readiness no-go` board is an acceptable outcome ONLY when accompanied by the per-plan rows showing why each plan left the board (with the derived population size and denominator reported).`

    QUOTATIONS CONFIRMING NEITHER STATES A FIXED POPULATION AS THE BAR:
    - E-07 bar: "every plan carrying a RESOLVED blocking question whose `- Finding: <ID>` names a finding still unresolved in its review record's CURRENT round is reported... afterwards NO such plan remains" (states a property over the live population).
    - E-06 bar: "The table must be produced and NON-VACUOUS; an empty `aw att --type plan --readiness no-go` board is an acceptable outcome ONLY when accompanied by the per-plan rows showing why each plan left the board" (states a non-vacuous property).

    AUTHORED IDS SURVIVE AS CONTEXT:
    Quoted from E-07 CONTEXT: "CONTEXT ON MEASURED IDS AND RE-DERIVATION (repaired by tgop8e): Five plans (`4h7tt0`, `kbqpkn`, `5lxvl3`, `y9vpvv`, `daexj1`) were measured at authoring on 2026-09-10; re-derive at execution time. At 2026-09-12 review of tgop8e, all five returned zero gating findings (cleared on 2026-09-10), while `subject_gating_blocks` returned non-empty for `ki6tom` PR-201 and `yku4ga` PR-701 behind RESOLVED questions (the live stale-bookkeeping cases to address) and for `32ij2j` PR-016/PR-017 and `xtklpd` PR-023 behind OPEN questions (which must not be touched)."

    E-07 INSTRUCTION LINE UNCHANGED:
    `- [x] E-07 CLOSE THE ONE-DIRECTIONAL ESCALATION LOOP, so a finding whose escalated question has been ANSWERED stops blocking. THIS IS THE SAME DEFECT THIS PLAN EXISTS TO FIX, ONE LAYER UP, and without it the re-check refuses on findings the maintainer has already settled. MEASURED at HEAD `ce33d3c1`: `4h7tt0` PR-002 (`HIGH`), `kbqpkn` PR-801 (`BLOCKER`), `5lxvl3` PR-002 (`HIGH`), `y9vpvv` PR-904 (`HIGH`) and `daexj1` PR-401 (`BLOCKER`) are ALL still `OPEN` in their typed review records, while every one of their escalated `Blocking: yes` questions is now `- Status: resolved` with the maintainer's 2026-09-10 answer recorded. `subject_gating_blocks` reads that column and blocks, since "Only decisions OTHER than `fixed` block" (`review_findings.py:851-853`).`

    LINT ON qhy3i3 CONFORMING:
    ```
    $ python3 -m agent_workflows ipd lint .aw/records/plans/executed/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md --phase post-transition
    -    ✓  executed     plan        20260910-rdyrecheck-01-qhy3i3  conforming
    ```

    FROZEN REGION DIGEST BEFORE AND AFTER (EQUAL):
    `ipd_lifecycle.frozen_region_digest` BEFORE: `d5380e65acf1a485604686b4138d838a88c8552a14f165e791d21632c22fa4e6`
    `ipd_lifecycle.frozen_region_digest` AFTER:  `d5380e65acf1a485604686b4138d838a88c8552a14f165e791d21632c22fa4e6`

    GIT DIFF OF qhy3i3 CONFIRMING METADATA / ATTESTATION UNCHANGED:
    ```diff
    diff --git a/.aw/records/plans/executed/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md b/.aw/records/plans/executed/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md
    index f444915c..f5f2a9bc 100644
    --- a/.aw/records/plans/executed/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md
    +++ b/.aw/records/plans/executed/20260910-rdyrecheck-01-qhy3i3-re-evaluate-a-stale-no-go-readiness-whose-recorded-cause-is.ipd.md
    @@ -15,6 +15,7 @@
     - Id: qhy3i3

     ## Workflow history
    +- 2026-09-24 criteria repaired (tgop8e): repaired E-07 and E-06 Expected outcome criteria to state properties instead of snapshot populations; demoted authored counts to context, carried re-derived population as context; only criteria and context touched, no E-item action text and no Scope-Paths touched.
     - 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: qhy3i3 verified (set rdyrecheck, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/readiness_recheck.py: changed by the plan's approved execution (auto-reconciled by aw oc run); in-scope-unmodified agent_workflows/completion.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
    @@ -84,8 +85,9 @@ Execution-state rule: mark an `E-*` item complete only after performing the acti
       REPORT, THEN WRITE ONLY UNDER `--apply`, exactly like the readiness half: for each plan, match a resolved question's `- Finding: <ID>` against the review record's current-round findings, and where the question is resolved while the finding is not, report the finding as STALE and offer to mark it `fixed` by appending a NEW `## Round <n>` that cites the answered question and its date.
       DO NOT SILENTLY IGNORE A STALE FINDING INSTEAD OF RESOLVING IT. Making the re-check skip a finding whose question is resolved would clear a plan on an inference about another artifact's contents rather than on that artifact's own record, which is fail-open. Append a round; leave an audit trail.
    +  CONTEXT ON MEASURED IDS AND RE-DERIVATION (repaired by tgop8e): Five plans (`4h7tt0`, `kbqpkn`, `5lxvl3`, `y9vpvv`, `daexj1`) were measured at authoring on 2026-09-10; re-derive at execution time. At 2026-09-12 review of tgop8e, all five returned zero gating findings (cleared on 2026-09-10), while `subject_gating_blocks` returned non-empty for `ki6tom` PR-201 and `yku4ga` PR-701 behind RESOLVED questions (the live stale-bookkeeping cases to address) and for `32ij2j` PR-016/PR-017 and `xtklpd` PR-023 behind OPEN questions (which must not be touched).
       - Depends on: E-04
    -  - Expected outcome: for each of the five measured plans, the stale finding is reported with the resolved question that settles it, and under `--apply` a new round marks it `fixed`; `subject_gating_blocks` then returns empty for that plan. Nothing is written without `--apply`.
    +  - Expected outcome: every plan carrying a RESOLVED blocking question whose `- Finding: <ID>` names a finding still unresolved in its review record's CURRENT round is reported with the resolved question that settles it, and under `--apply` each is marked `fixed` by appending a new round; afterwards NO such plan remains and `subject_gating_blocks` returns empty for each. Nothing is written without `--apply`. The derived population size must be reported WITH its denominator (total plans examined carrying a `- Finding:` escalation) and zero explicitly stated if empty; a zero count passes ONLY when corroborated by a non-zero denominator showing the query ran, rather than passing silently.
       - Execution state: performed

     - [x] E-06 RUN BOTH HALVES OVER THE STRANDED SET AND RECORD THE SURVIVING REASON PER PLAN, one row each, refusals included. THE DELIVERABLE IS THE PER-PLAN REASON, NOT A COUNT OF PLANS CLEARED. Measured at HEAD `ce33d3c1`, nine plans carry `no-go` with no unresolved BLOCKING question (`4h7tt0`, `5lxvl3`, `8tgg6g`, `daexj1`, `dw7i3m`, `kbqpkn`, `u06zo2`, `wmnmei`, `y9vpvv`), and running the shipped `approval_refusals` over them shows only ONE (`dw7i3m`) clears while EIGHT hold on a second, independent refusal. RE-MEASURE AND PRINT THE COMMAND rather than trusting any list in this plan, including this corrected one: five of the nine had their blocking question answered on 2026-09-10, four were stranded before that date, and E-07 changes the answer for five of them.
    @@ -92,5 +94,5 @@ Execution-state rule: mark an `E-*` item complete only after performing the acti
       - Depends on: E-07
    -  - Expected outcome: a re-measured per-plan table with the command that produced it, each row naming the three condition results and the action taken (updated, or refused with the specific surviving cause), plus `aw att --type plan --readiness no-go` before and after. Every refusal is explained rather than worked around.
    +  - Expected outcome: a re-measured per-plan table with the command that produced it, each row naming the three condition results and the action taken (updated, or refused with the specific surviving cause), plus `aw att --type plan --readiness no-go` before and after. Every refusal is explained rather than worked around. The table must be produced and NON-VACUOUS; an empty `aw att --type plan --readiness no-go` board is an acceptable outcome ONLY when accompanied by the per-plan rows showing why each plan left the board (with the derived population size and denominator reported).
       - Execution state: performed
    ```

    APPENDED HISTORY RECORD ATTRIBUTING EDIT TO tgop8e:
    `- 2026-09-24 criteria repaired (tgop8e): repaired E-07 and E-06 Expected outcome criteria to state properties instead of snapshot populations; demoted authored counts to context, carried re-derived population as context; only criteria and context touched, no E-item action text and no Scope-Paths touched.`

    RE-DERIVED POPULATION CARRIED INTO E-07 CONTEXT:
    4 plans with non-empty `subject_gating_blocks`:
    - `ki6tom` PR-201 (OQ-01 `- Status: resolved` -> live stale-bookkeeping target)
    - `yku4ga` PR-701 (OQ-01 / OQ-02 `- Status: resolved` -> live stale-bookkeeping target)
    - `32ij2j` PR-016, PR-017 (OQ `- Status: open` -> must NOT be touched)
    - `xtklpd` PR-023 (OQ `- Status: open` -> must NOT be touched)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: quote the added requirement from each repaired criterion, showing the derived population size must be reported WITH its denominator and zero explicitly stated. Quote the recorded zero-is-pass-or-refusal decision for EACH item with its reason; a single blanket answer applied to both without justification is a FAILED validation. E-07's recorded reason must NOT assert that the population is empty today: quote it and confirm by re-running the derivation (paste the command and its output) that the non-empty population review measured is still reflected. A recorded reason resting on "as they are today, all cleared" is a FAILED validation, since that premise was falsified at review.
  - Observed evidence: QUOTED REQUIREMENTS REQUIRING POPULATION WITH DENOMINATOR AND EXPLICIT ZERO:
    - E-07: "The derived population size must be reported WITH its denominator (total plans examined carrying a `- Finding:` escalation) and zero explicitly stated if empty; a zero count passes ONLY when corroborated by a non-zero denominator showing the query ran, rather than passing silently."
    - E-06: "The table must be produced and NON-VACUOUS; an empty `aw att --type plan --readiness no-go` board is an acceptable outcome ONLY when accompanied by the per-plan rows showing why each plan left the board (with the derived population size and denominator reported)."

    ZERO-IS-PASS-OR-REFUSAL DECISION PER ITEM:
    - E-07: A zero count is a PASS only when corroborated by its non-zero denominator (e.g. 100 plans examined with `- Finding:` escalations, 0 return non-empty), which proves the query and predicate ran over the corpus rather than silently bypassing unexamined plans. A bare uncorroborated zero without denominator is refused.
    - E-06: An empty board (`aw att --type plan --readiness no-go`) is an acceptable outcome ONLY when accompanied by the per-plan transition rows reporting the condition recomputations and actions that cleared each plan from the board. An uncorroborated empty board without per-plan rows is refused.

    CONFIRMATION THAT E-07 REASON DOES NOT ASSERT POPULATION IS EMPTY TODAY:
    The re-derived population is non-empty (4 plans return non-empty from `subject_gating_blocks`), with 2 live stale-bookkeeping cases (`ki6tom` PR-201, `yku4ga` PR-701) behind resolved questions.

    RE-DERIVATION COMMAND AND ACTUAL OUTPUT:
    ```
    $ python3 -c "
    from pathlib import Path
    import agent_workflows.review_findings as rf
    repo = Path('.')
    plans = [(p.stem.split('-')[3] if len(p.stem.split('-')) > 3 else p.stem, p) for p in sorted(repo.glob('.aw/records/plans/**/*.ipd.md')) if '- Finding:' in p.read_text(encoding='utf-8')]
    print(f'Plans examined: {len(plans)}')
    non_empty = [(id6, p, tuple(rf.subject_gating_blocks(repo, id6))) for id6, p in plans if tuple(rf.subject_gating_blocks(repo, id6))]
    print(f'Non-empty: {len(non_empty)}')
    for id6, p, blocks in non_empty:
        rel_blocks = [b._replace(review_path=str(Path(b.review_path).relative_to(repo.resolve()))) for b in blocks]
        print(f'  {id6}: {rel_blocks}')
    "
    Plans examined: 100
    Non-empty: 4
      ki6tom: [GatingBlock(plan_id6='ki6tom', finding_id='PR-201', severity='blocker', decision='open', kind='finding', review_path='.aw/records/reviews/20260904-runbypass-01-ki6tom-remove-the-spec-prohibited-bypass-flags-from-both-host-runne.review.md', detail='')]
      32ij2j: [GatingBlock(plan_id6='32ij2j', finding_id='PR-016', severity='blocker', decision='open', kind='finding', review_path='.aw/records/reviews/20260906-integearn-01-32ij2j-earn-integration-from-a-suite-failure-delta-against-the-froz.review.md', detail=''), GatingBlock(plan_id6='32ij2j', finding_id='PR-017', severity='blocker', decision='open', kind='finding', review_path='.aw/records/reviews/20260906-integearn-01-32ij2j-earn-integration-from-a-suite-failure-delta-against-the-froz.review.md', detail='')]
      xtklpd: [GatingBlock(plan_id6='xtklpd', finding_id='PR-023', severity='blocker', decision='open', kind='finding', review_path='.aw/records/reviews/20260906-integearn-02-xtklpd-report-a-stranded-lane-honestly-instead-of-as-a-completed-ru.review.md', detail='')]
      yku4ga: [GatingBlock(plan_id6='yku4ga', finding_id='PR-701', severity='blocker', decision='open', kind='finding', review_path='.aw/records/reviews/20260908-setidhard-00-yku4ga-make-a-setid-a-hard-cross-type-unique-identity-and-replace-s.review.md', detail='')]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the recorded convention verbatim from `plan-review.md` rubric section G, showing both the rule and the code-facts exemption. Paste the one-sentence pointer added to the `ipd-spec` doc and confirm by quotation that the rule is NOT restated there. Quote the note explaining why no lint rule is attempted. Then demonstrate the rule discriminates on THREE cases, not two, since the two-case version does not exercise the distinction review actually had to make: one it flags (`qhy3i3` E-07 as authored), one it exempts as a stable CODE fact (`8hald1`'s "fourteen-key core"), and one it exempts as an orchestrator counting its OWN declared children (`cczotj` E-01's "all five children are `executed`"), which is the class F-6 measured as the majority. State plainly that a spec was amended, since the runner's spec-edit announcement will not name it (the declared `Scope-Paths` entry is a directory, so `declared_spec_paths` returns none).
  - Observed evidence: RECORDED CONVENTION VERBATIM FROM plan-review.md RUBRIC G:
    ```markdown
    - **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (test assertions, schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)
    ```

    ONE-SENTENCE POINTER ADDED TO ipd-spec DOC (.aw/records/specs/20260726-1340-01-ipd-spec.spec.md):
    ```markdown
    An `Expected outcome` counting live artifacts must state a property rather than an authored count; see `.aw/system/workflows/plan-review/plan-review.md` Rubric G for the re-derivation convention and code-facts exemptions.
    ```
    Quotation confirmation: the pointer simply references the canonical definition in `plan-review.md` Rubric G; the detailed rule is NOT duplicated or restated in `ipd-spec`.

    NOTE EXPLAINING WHY NO LINT RULE IS ATTEMPTED:
    Quoted from `plan-review.md` Rubric G:
    "(Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)"

    DEMONSTRATION OF THREE-WAY DISCRIMINATION:
    1. Case 1 (FLAGGED): `qhy3i3` E-07 as authored ("for each of the five measured plans... `subject_gating_blocks` then returns empty"). Counts a live population of artifact plans with open review findings as a snapshot number ("five measured plans"). FLAGGED by the rule because live artifact populations drift over time and must be stated as properties re-derived at execution.
    2. Case 2 (EXEMPT - stable code fact): `8hald1`'s "fourteen-key core" (or schema key assertions). Counts fixed code-level constants/schema keys. EXEMPT under the rule because code facts are static and do not drift with repository lifecycle events.
    3. Case 3 (EXEMPT - orchestrator counting declared children): `cczotj` E-01's "all five children are `executed`". Counts an orchestrator's own declared child plans. EXEMPT under the rule because declared children are fixed authored structural invariants of that specific Set.

    SPEC AMENDMENT DISCLOSURE:
    Spec `.aw/records/specs/20260726-1340-01-ipd-spec.spec.md` was amended with a one-sentence pointer to `plan-review.md` Rubric G and a workflow history record. Because `- Scope-Paths:` declares the directory `.aw/records/specs/`, `runner_shared.declared_spec_paths` does not match the `.spec.md` facet and will not announce the spec edit pre-run; the amendment is explicitly declared here.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

SCOPE FENCE, DECLARED SO IT CAN BE RECONCILED AFTERWARDS (the previous clause here was an inherited run-records prohibition from `wfartifacts`, irrelevant to this plan, removed as PR-001). This plan changes exactly three files: `qhy3i3`'s IPD, `plan-review.md`, and the `ipd-spec` doc. The declared `.aw/records/specs/` entry is a DIRECTORY and therefore wider than the work; touch only the `ipd-spec` doc within it, and justify any other path with `--scope-reason` at `aw ipd finalize` rather than reading the broad fence as permission.

DO NOT ALTER ANOTHER ROLE'S ATTESTATION ON `qhy3i3`. It is an APPROVED plan carrying a human `- Approval:` line. Its `- Status:`, `- Approval:` and `- Readiness:` fields are outputs of the human and of `/plan-review`, and this plan has no authority over any of them. Change criteria and context only; leave every E-item ACTION line and every `Scope-Paths` entry byte-unchanged so its frozen requirement digest does not move, and append a history record saying what was changed and by which plan.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
