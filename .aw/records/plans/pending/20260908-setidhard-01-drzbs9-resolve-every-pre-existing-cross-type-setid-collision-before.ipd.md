# IPD: Resolve every pre-existing cross-type setid collision before hard enforcement can be enabled

- Date: 2026-09-08
- Kind: child
- Concern: THE TREE CARRIES TWENTY-NINE `check.setid-collision` FINDINGS ACROSS TWENTY-ONE DISTINCT SETIDS, AND ALL TWENTY-NINE ARE THE SAME BENIGN SHAPE. Measured at HEAD by calling `check_engine.check_collisions` directly and grouping by setid: `durablecapture` 4, `runverdict` 4, `runrecon` 2, `integearn` 2, then `specvis`, `testiso`, `hookretry`, `rcptstale`, `mergedirty`, `bklgkind`, `rdattest`, `runghostid`, `gatejrnl`, `depreview`, `runnoop`, `nogitmsg`, `selfmdialect`, `actorparen`, `hardreach`, `runnerlayer` and `scopeattr` at 1 each. Every one is a BACKLOG ITEM sharing its setid with the plan Set it graduated into, for example `.aw/records/backlog/graduated/20260907-specvis-01-dk16dx-...backlog.md` against `.aw/records/plans/pending/20260907-specvis-01-st5klo-...ipd.md`. This is not sloppiness; it is how a reader currently sees at a glance that an item and a plan are the same work.
  THE SWEEP IS A SPEC REQUIREMENT AND ITS POSITION IS FIXED. Spec `4w7d6s` Section 5: "A one-time sweep MUST identify and resolve any other existing cross-type setid collisions before I2 is turned on fail-closed, so enabling the hard rule does not mass-fail the tree. (Mirror the grandfathering discipline used for Scope-Paths / dependency cutover: find violators, fix, then enforce.)"
  BUT SWEEPING FIRST WOULD BE WASTED WORK, WHICH IS WHY THIS ITEM DEPENDS ON ORDER 03. Every one of the 29 collisions was CREATED by a graduation reusing its source's setid, so until Order 03 mints a fresh child setid, the next graduation recreates one. This was demonstrated at authoring time rather than reasoned about: scaffolding this very Set into `Set: setiduniq` immediately collided with backlog item `sjsoqq`, and the four plans were regrouped to `setidhard` under the spec's own G1 rule before any prose was written. A sweep run before Order 03 would have to be run again.
  THE NAMED MIGRATION CASE IS STILL REAL AND IS OLDER THAN THE OTHERS. The closed backlog item `.aw/records/backlog/done/20260823-agentadhere-01-3gr7fk-...backlog.md` still carries `- Set: agentadhere`, shared with EIGHT executed plans (`3b4f8u`, `gfokao`, `uisjns`, `8dto0g`, `wqj1ne`, `diundn`, `r2ks4k` and the Set's own members). This is the collision that originally motivated the whole item, via a confusing cross-type "type mismatch" from `aw ipd set approved agentadhere`. Note the setter half of that symptom is ALREADY FIXED (`9107790`), so what remains here is the DATA.
  THE DANGEROUS WAY TO DO THIS IS TO RENAME THE PLAN SETS, and it looks equally valid from the finding text. A plan Set's setid appears in filenames, in `Item-Dependencies` edges, in review-record filenames, in run records, and in prose across the tree, and SEVERAL of the 21 colliding setids belong to plans that are `approved` or executing RIGHT NOW under other agents (`scopeattr`/`h9cn0y`, `depreview`/`03ie04`, `integearn`/`32ij2j` among them). Renaming the SOURCE touches one file per collision, and once Order 02 exists the `Graduated-To` forward link records the relationship the shared name used to carry. The spec points the same way for `agentadhere`: "re-group the closed backlog item to its own unique setid".
- Scope: Resolve every pre-existing cross-type setid collision by regrouping the SOURCE artifact (the backlog item or spec), never a plan Set that is live, and record the lineage via the `Graduated-To` link Order 02 provides. Data only: this child changes NO code and adds NO check. It ends with `check.setid-collision` at zero so the hard posture Order 00 verifies becomes reachable.
- Scope-Paths: .aw/records/backlog, .aw/records/specs, .aw/records/research
- Item-Dependencies: executed:dw7i3m
- Status: to-review
- Set: setidhard
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: drzbs9
- From-Backlog: sjsoqq

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `sjsoqq` deliverable #6, RE-SEQUENCED and RE-TARGETED. The item's own claim that "`aw check all` now reports 0 setid-collision findings" is STALE: measured 29 findings across 21 setids at HEAD. Its accompanying claim that the `agentadhere` collision "PHYSICALLY persists" is TRUE and re-verified (`3gr7fk` still carries `- Set: agentadhere`, shared with eight executed plans). TWO AUTHORING DECISIONS that the item left open. FIRST, this child DEPENDS ON Order 03 (`executed:dw7i3m`) even though it has a lower Order digit, because every one of the 29 collisions was created by graduation reusing a source setid, so a sweep before the root-cause fix would be undone by the next graduation; demonstrated at authoring when scaffolding this Set into `Set: setiduniq` instantly collided with `sjsoqq`. SECOND, the sweep renames the SOURCE, not the plan Set, because a plan setid is cited across filenames, dependency edges, review records and run records, and several of the 21 belong to plans that are approved or executing under other agents right now; the spec's own Section 5 prescribes exactly this for `agentadhere`.

## Goal

Leave `check.setid-collision` at zero by fixing 21 collisions in the one place that is cheap and safe to change, so a rule the catalog already calls an error stops firing on the repository's own convention.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: inventory before touching anything

- [ ] E-01 RE-MEASURE THE COLLISION SET AND CLASSIFY EVERY MEMBER BEFORE RENAMING ANY FILE. Do not trust this plan's list: the tree moves hourly and four other agents are graduating items into new Sets right now, so the set will differ.
  BUILD THE INVENTORY BY CALLING THE PREDICATE, not by parsing report text: `check_engine.check_collisions(repo_root)` filtered to `rule == "check.setid-collision"`, grouped by the setid parsed from each finding's detail. Authoring baseline for orientation only: 29 findings, 21 distinct setids.
  FOR EACH COLLIDING SETID RECORD FOUR FACTS, because they decide what may be touched: every artifact carrying it with its type and path; which side is the SOURCE (backlog item or spec) and which is the PLAN Set; the plan Set's current `- Status:` and lifecycle directory; and whether a `From-Backlog` edge already joins the two.
  FLAG ANY COLLISION THAT IS NOT THE BENIGN SHAPE. All 29 measured at authoring were source-versus-its-own-graduated-plan. If your inventory contains a collision between two artifacts with NO graduation relationship, or between two artifacts of the same type, that is a DIFFERENT defect and must be reported rather than swept: renaming one side of a relationship you have not established would destroy real information.
  - Depends on: none
  - Expected outcome: a per-setid inventory with the four facts, an explicit count, and any non-benign collision flagged for a human rather than renamed.
  - Execution state: pending

### Task group 2: regroup the sources

- [ ] E-02 REGROUP THE SOURCE ARTIFACT OF EACH BENIGN COLLISION TO A FRESH SETID, AND NEVER THE PLAN SET. This is the item's deliverable #6 and the direction the spec prescribes.
  USE THE TOOLED VERB, NOT A HAND RENAME: `aw group backlog <file> --set <new> --rename --apply` (and `aw group specs ...` for a spec source). The verb owns the clustering filename and rewrites references; hand-naming is exactly what the naming authority exists to prevent.
  PASS `--order` EXPLICITLY. MEASURED AT AUTHORING: `aw group plans <id> --set X --rename --apply` WITHOUT `--order` reset the Order to `00` on all four plans of this Set, including three children, silently producing three Order-0 children. Assume the same hazard for `aw group backlog` and verify each regrouped file's `- Order:` afterwards rather than trusting the verb.
  DO NOT RENAME A PLAN SET AT ALL in this child, and especially not one that is live. Several colliding setids belong to plans that are `approved` or executing under other agents (`scopeattr`, `depreview`, `integearn` among those measured). A plan setid is cited in filenames, `Item-Dependencies` edges, review-record filenames, run records and prose; the source side is one file.
  DERIVE A DISTINCT-BUT-RECOGNIZABLE NAME, per the spec's OQ-03 reasoning: only the setid TOKEN must differ, and the human-readable slug may still echo the source, so traceability survives for a human reader as well as for the typed link.
  - Depends on: E-01
  - Expected outcome: every benign collision's SOURCE regrouped to a fresh setid via the tooled verb, each regrouped file's Order verified unchanged, and no plan Set renamed.
  - Execution state: pending

- [ ] E-03 RESOLVE THE `agentadhere` CASE EXPLICITLY, because it is the collision that motivated the whole item and it differs from the other twenty in one way that matters.
  ITS SOURCE IS A CLOSED ITEM: `.aw/records/backlog/done/20260823-agentadhere-01-3gr7fk-...backlog.md` carries `- Set: agentadhere`, shared with EIGHT executed plans. Regrouping a `done` item is safe (nothing schedules it) and is what the spec prescribes: "re-group the closed backlog item to its own unique setid ... and (per G3) record the plan Set it graduated into via `Graduated-To`".
  DO NOT TOUCH THE EIGHT EXECUTED PLANS. They are in `executed/`, their bodies are immutable by policy, and their setid is cited in the historical record. The collision is cleared from the SOURCE side alone.
  STATE WHAT THIS DOES AND DOES NOT FIX. It clears the finding and unblocks the original `aw ipd set approved agentadhere` symptom's DATA half; the SETTER half was already fixed in `9107790` and must not be rebuilt.
  - Depends on: E-02
  - Expected outcome: `3gr7fk` regrouped to its own setid with a `Graduated-To` recording the `agentadhere` plan Set; the eight executed plans untouched; the finding gone.
  - Execution state: pending

### Task group 3: prove the sweep is complete and cost-free

- [ ] E-04 PROVE `check.setid-collision` IS ZERO AND THAT NOTHING ELSE MOVED. The sweep's whole purpose is to make the hard posture reachable, so a partial sweep leaves the same unactionable rule with a smaller number.
  COMPARE PER RULE, NEVER BY TOTAL. `aw check all` reports 98 findings at HEAD across many rules this Set does not own, and that total will not reach zero. The criterion is `check.setid-collision` at ZERO with no other rule's count risen. In particular watch `check.name-nonconformant` (a regroup rewrites filenames) and `check.from-backlog-dangling` (a rename must not break an existing back-link).
  ASSERT `aw doctor` AGREES. The two surfaces have disagreed before about the id6 twin (`aw check all` reported zero id6-collisions while `aw doctor` reported one, because of the retired-path filter), so agreement must be demonstrated rather than assumed.
  RUN THE SUITE BARE and judge on the DELTA. Baseline on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case, which asserts against SIBLING PLANS' live status and is therefore exactly the kind of test a mass regroup could perturb. If its failure changes shape, say so explicitly rather than counting it as the same known failure.
  - Depends on: E-03
  - Expected outcome: `check.setid-collision` zero; no other rule's count risen; `aw doctor` agreeing; bare-suite delta empty with counts stated and the known failure's shape confirmed unchanged.
  - Execution state: pending

- [ ] E-05 PROVE NO TRACEABILITY WAS LOST, which is the real risk of this child and the reason the maintainer might reject the whole approach. Before the sweep a reader could see the relationship in the shared NAME; after it, the relationship must be readable from the typed links alone.
  FOR EVERY REGROUPED SOURCE, DEMONSTRATE BOTH DIRECTIONS RESOLVE: the plan's `From-Backlog: <source id6>` resolves to the regrouped item, and the source's `Graduated-To: <plan setid>` resolves to the plan Set (the check Order 02 adds). A regroup that clears a finding while orphaning the relationship has made the tree worse.
  CHECK THE BACK-LINK SURVIVED THE RENAME. `From-Backlog` points by id6, which a regroup does NOT change, so it should survive by construction; verify that rather than assuming it, since `--rename` also rewrites references and could plausibly touch one.
  REPORT ANY SOURCE THAT HAS NO GRADUATION LINK AT ALL. If a colliding pair turns out to have no `From-Backlog` edge, then the shared setid was the ONLY record of the relationship and regrouping it destroys information. That case must be reported for a human, not resolved by inventing a link.
  - Depends on: E-04
  - Expected outcome: both link directions demonstrated resolving for every regrouped source; any source lacking a graduation link reported rather than silently regrouped.
  - Execution state: pending

## Project conventions discovered (Step 0)

- EVERY ONE OF THE 29 LIVE FINDINGS IS THE SAME BENIGN SHAPE: a backlog item sharing its setid with the plan Set it graduated into, across 21 distinct setids. Measured by calling `check_engine.check_collisions` and grouping by setid.
- THE SPEC PRESCRIBES RENAMING THE SOURCE, not the Set: for `agentadhere` it says "re-group the closed backlog item to its own unique setid" (Section 5).
- SEVERAL COLLIDING SETIDS BELONG TO LIVE PLANS (`scopeattr`, `depreview`, `integearn` measured `approved`), which is why the plan side is untouchable here.
- `aw group <type> ... --rename --apply` WITHOUT `--order` RESETS Order TO `00`. Measured on this Set's own four plans at authoring. Always pass `--order` and verify afterwards.
- `From-Backlog` POINTS BY id6, which a regroup does not change, so the back-link should survive a rename by construction. Verify rather than assume.
- `aw check all` IS NOT GREEN (98 findings at HEAD). Compare per RULE.
- THE TWO CHECK SURFACES HAVE DISAGREED BEFORE: `aw check all` versus `aw doctor` on the id6 twin, because of the retired-path filter. Demonstrate agreement.
- THE KNOWN SUITE FAILURE ASSERTS AGAINST SIBLING PLANS' LIVE STATUS (`tests/test_orchestrator_retirement.py`), so a mass regroup is exactly the kind of change that could perturb it.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the sweep's real size | 29 findings across 21 distinct setids, ALL benign source-versus-its-own-plan pairs. `durablecapture` 4, `runverdict` 4, `runrecon` 2, `integearn` 2, seventeen more at 1. | `check_collisions` at HEAD grouped by setid |
| F-2 | HIGH | the item's status claim is STALE | It says "`aw check all` now reports 0 setid-collision findings". Measured: 29. | `aw check all --agent` at HEAD |
| F-3 | HIGH | renaming the plan side is dangerous | A plan setid is cited in filenames, `Item-Dependencies`, review filenames, run records and prose, and several colliding Sets are `approved` or executing under other agents right now. | statuses read at HEAD |
| F-4 | HIGH | sweeping before Order 03 is wasted | Every collision was created by graduation reusing a source setid; the next graduation recreates one. DEMONSTRATED: scaffolding this Set into `setiduniq` instantly collided with `sjsoqq`. | measured at authoring; the regroup to `setidhard` |
| F-5 | MEDIUM | the named case is real and older | `3gr7fk` (a `done` item) still carries `- Set: agentadhere`, shared with EIGHT executed plans. | `grep 'Set: agentadhere' .aw/records/` |
| F-6 | MEDIUM | its setter symptom is already fixed | The confusing "type mismatch" from `aw ipd set approved agentadhere` was deliverable #3, landed in `9107790` with `tests/test_status_set.py` coverage. Only the DATA remains. | the item's own Progress note |
| F-7 | MEDIUM | the regroup verb has an Order hazard | `aw group plans <id> --set X --rename --apply` with no `--order` reset all four of this Set's plans to Order `00`, including three children. | measured at authoring |
| F-8 | MEDIUM | traceability is the real risk | Before the sweep the shared NAME carried the relationship. After it, only the typed links do, so both directions must be proven to resolve or the tree is worse off. | spec G2/G3/G5 |
| F-9 | LOW | the back-link should survive | `From-Backlog` points by id6 and a regroup does not change an id6. | `releases.check_from_backlog` resolves by id6 |

## Proposed changes (ordered, validatable)

1. Re-measure and classify every collision, flagging any non-benign shape for a human (E-01).
2. Regroup each benign collision's SOURCE to a fresh setid via the tooled verb, with `--order` passed explicitly (E-02).
3. Resolve `agentadhere` from the source side, leaving the eight executed plans untouched (E-03).
4. Prove `check.setid-collision` is zero, no other rule rose, and `aw doctor` agrees (E-04).
5. Prove both link directions still resolve for every regrouped source (E-05).

## Deferred / out of scope (with reason)

- ENABLING OR HARDENING THE ENFORCEMENT POSTURE. This child clears the DATA so the posture becomes reachable; Order 00 verifies the posture as a whole-Set criterion. Hardening before the sweep is precisely what the spec forbids.
- THE `Graduated-To` FIELD AND ITS CHECK. Order 02 (`bwgyum`) builds them. This child CONSUMES them in E-03 and E-05, which is why it must not run before Order 02 either (its dependency on Order 03 transitively gives that, since Order 03 depends on Order 02).
- PREVENTION AT CREATION AND THE FRESH-SETID MINT. Order 03 (`dw7i3m`). This child is a one-time data sweep and adds no guard; without Order 03 its result decays.
- RENAMING ANY PLAN SET. Excluded on measured risk (F-3) and by the spec's own prescription. If a collision genuinely cannot be resolved from the source side, report it rather than renaming a live Set.
- DELIVERABLE #3 (setter type-scoping). Landed in `9107790`; Order 00 checks it as a regression only.
- FIXING `aw group`'s ORDER RESET (F-7). A real defect, but a different surface with its own tests. This child works around it by passing `--order` and verifying; the fix is reported to the maintainer.
- THE id6 COLLISION FAMILY. Already hard, out of scope in the spec, and `sk7ggr` (`id6integ-01`) is in flight on it.

## Scope check

- Over-scope: none. Data only, in the records trees, with no code and no check added.
- Scope-Paths justification: `.aw/records/backlog` holds the source side of every measured collision and is where E-02 and E-03 act; `.aw/records/specs` is declared because a SPEC can equally be a graduation source and E-01's inventory may find one (the spec's G3 applies to specs as well as items); `.aw/records/research` is declared because the item's own origin note records research reports among the `agentadhere` carriers, so the inventory may reach one. If E-01 finds no spec or research collision, those two paths may finish UNCHANGED, which is the expected outcome and not an incomplete item.
- Under-scope, stated rather than left as `none`: this child changes no code, adds no check, renames no plan Set, does not build `Graduated-To`, does not add creation-time prevention, does not harden the posture, and does not fix `aw group`'s Order reset. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY. If the known `test_orchestrator_retirement` failure changes SHAPE (different assertion text), say so rather than counting it as unchanged, because it reads sibling plans' live status.
- `aw check all --agent` PER-RULE counts before and after, pasted. `check.setid-collision` must be ZERO. Watch `check.name-nonconformant` and `check.from-backlog-dangling` specifically, since a regroup rewrites filenames and references.
- `aw doctor` setid-collision set after the sweep, demonstrated equal to `aw check all`'s.
- THE PER-SETID INVENTORY from E-01 pasted in full, so a reviewer can see what was touched and what was not.
- BOTH LINK DIRECTIONS resolved for every regrouped source (E-05), with the commands and their output.
- EVERY REGROUPED FILE'S `- Order:` verified unchanged, given F-7's measured hazard.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change is expected from this child: it EXECUTES spec `4w7d6s` Section 5 rather than amending it. The spec is `- Status: draft` and Order 00's E-02 holds that gate; this child must not begin until it is answered.

`.aw/records/backlog/README.md`'s "Promotion to a plan" section describes the graduation convention and is where the fresh-setid rule belongs once Order 03 lands. That documentation edit is Order 02's or Order 03's, NOT this child's, and this child does not declare the README.

If the executor finds prose ANYWHERE (in a README, a spec, or an AGENTS.md block) that instructs a graduation to REUSE the source's setid, that is the convention this Set changes and it must be REPORTED as a finding for the child that owns the documentation, not edited here.

Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Which side of each collision should be renamed?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE SOURCE, ALWAYS, and the evidence is asymmetric enough to settle it without a maintainer ruling. A plan Set's setid is cited in plan filenames, in `Item-Dependencies` edges, in review-record filenames (which carry the reviewed plan's id6 and setid), in run records and in prose across the tree; the SOURCE side is one file per collision. Measured, several colliding setids belong to plans that are `approved` or executing under other agents right now, so renaming them would rewrite artifacts live runs are reading. The spec's Section 5 independently prescribes the same direction for `agentadhere` ("re-group the closed backlog item"). The residual cost is the at-a-glance name match, which E-05 replaces with proven typed links, and which Order 00's OQ-02 puts to the maintainer as the Set-level question.

### OQ-02: What should a regrouped source's new setid be called?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: DISTINCT TOKEN, RECOGNIZABLE SLUG, per the spec's OQ-03 reasoning that "the human-readable slug can still echo the source (only the setid token must differ)". So a `specvis` item may become, for example, `specvisitem`, keeping the filename readable while making the token unique. This is deliberately left as a naming convention rather than an algorithm, because E-01's inventory may reveal sources whose obvious derived token is ALSO taken, and the executor must then pick another rather than follow a rule off a cliff. What is NOT acceptable is a meaningless token (a hash or a number), since the slug is the only thing a human skims.

### OQ-03: What if a colliding pair has no graduation link at all?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REPORT IT, DO NOT SWEEP IT. If no `From-Backlog` edge joins the two artifacts, then the shared setid is the ONLY record that they are related, and regrouping the source would destroy that information while making the finding disappear, which is strictly worse than the finding. E-01 must flag such a pair and E-05 must report it; the remedy (establish the real link first, or accept that they are unrelated and rename deliberately) is a human decision because it requires knowing the intent behind two artifacts. All 29 collisions measured at authoring were joined pairs, so this is a guard rather than an expected case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the per-setid inventory IN FULL, with each collision's artifacts, types, paths, the plan Set's `- Status:` and directory, and whether a `From-Backlog` edge joins the pair. Paste the raw count and compare it to the authoring baseline of 29 findings across 21 setids, stating the difference. Confirm explicitly whether any collision was NOT the benign shape, and if so, that it was reported rather than renamed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the ACTUAL `aw group` command and its output for each regrouped source. Paste each regrouped file's `- Set:` and `- Order:` AFTER the regroup, proving the Order was not reset (F-7). Paste NEGATIVE proof that no plan file was renamed: a `git status --porcelain .aw/records/plans/` showing no plan path changes attributable to this child.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `3gr7fk`'s front matter before and after, showing the new setid and the `Graduated-To` entry. Paste proof the eight `agentadhere` executed plans are untouched (`git status` plus their unchanged `- Set:` lines). Paste `aw check all --agent` filtered to `agentadhere`, showing the finding gone. State in one sentence that the setter half was already fixed in `9107790` and was not rebuilt.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw check all --agent` PER-RULE counts before and after, showing `check.setid-collision` at ZERO and naming every rule whose count changed with the reason. Paste `aw doctor`'s setid-collision set and confirm in one sentence it equals `aw check all`'s. THEN paste the BARE `python3 -m pytest` summary lines before and after, state the failure-set delta, and confirm the known `test_orchestrator_retirement` failure's assertion text is UNCHANGED (or report how it changed).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: for EVERY regrouped source, paste the resolution of BOTH directions: the plan's `From-Backlog` resolving to the regrouped item, and the source's `Graduated-To` resolving to the plan Set. Paste the output of `check.graduated-to-dangling` over the tree showing zero findings. If any source lacked a graduation link, paste that report and confirm it was NOT regrouped.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS CHILD MUST NOT RUN FIRST DESPITE ITS ORDER DIGIT. It carries `- Item-Dependencies: executed:dw7i3m` deliberately: sweeping before Order 03 mints fresh setids means the next graduation recreates a collision, and the sweep would have to be repeated. The runner sorts by dependency depth first and will handle this; a human executing by hand must read the edge.

IT ALSO INHERITS ORDER 00's TWO BLOCKING QUESTIONS. OQ-01 there is the spec-approval gate (`4w7d6s` is `draft` with three open questions), and OQ-02 there asks whether hard cross-type uniqueness is the right answer at all given that all 29 findings are the repository's own working convention. If the maintainer narrows I1 instead, this child's sweep is unnecessary and must not be run.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Use the TOOLED regroup verb and pass `--order` explicitly; never hand-rename a records file. Do NOT rename any plan Set, and do NOT edit any file under `.aw/records/plans/`. Do NOT touch a backlog item outside the measured collision set, since other agents are graduating items concurrently. Paste ACTUAL command output and compare `aw check` findings PER RULE, never by total. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the full per-setid inventory and both link directions for every regrouped source.
