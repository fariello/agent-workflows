# IPD: Make a setid a hard cross-type-unique identity and replace shared-setid graduation coupling with typed links

- Date: 2026-09-08
- Kind: orchestrator
- Concern: A SETID IS TREATED AS AN IDENTITY BY THE CHECKER AND AS A SHARED LABEL BY EVERY GRADUATION, AND THE TWO CANNOT BOTH BE RIGHT. `check.setid-collision` is already severity `error` in the rule table (`check_engine.py:95`), yet MEASURED the tree carries FORTY such findings across THIRTY distinct setids, and every single one is the same benign shape: a backlog item sharing its setid with the plan Set it graduated into (`durablecapture` 4, `runverdict` 4, then `runviewdisc`/`runrecon`/`awinbox`/`integearn` at 2 each, and twenty-four more at 1 each). RE-MEASURED AT REVIEW 2026-09-08 (HEAD `15dba2d7`): the plan's authoring figures of 29 findings across 21 setids are STALE and the population GREW by eleven findings and nine setids in a single day, which is itself the strongest available evidence for Order 03's root-cause fix (see F-13). So a rule the catalog calls an error fires 29 times on the repository's own working convention, which is the definition of a rule nobody can act on.
  THAT IS WHY THE ORDER OF THIS SET IS LOAD-BEARING AND IS NOT NEGOTIABLE. Spec `4w7d6s` Section 5 states it directly: "A one-time sweep MUST identify and resolve any other existing cross-type setid collisions before I2 is turned on fail-closed, so enabling the hard rule does not mass-fail the tree." Enabling hard enforcement first would turn 40 benign findings into 40 blocking failures across plans other agents are actively executing. And the sweep alone is NOT durable either: the next graduation recreates a collision immediately, which this very Set demonstrated at authoring (scaffolding four plans into `Set: setiduniq` instantly collided with backlog item `sjsoqq`, and they were regrouped to `setidhard` under the spec's own G1 rule before anything else was written). Root cause first (Order 03's fresh-setid mint), then the sweep, then enforcement.
  THE POPULATION IS ACTIVELY GROWING, WHICH IS THIS SET'S STRONGEST ARGUMENT AND WAS MEASURED RATHER THAN PREDICTED (F-13). Between authoring and review, ONE DAY apart, the findings went from 29 across 21 setids to 40 across 30: eleven new benign collisions and nine new setids, every one created by an ordinary graduation reusing its source's setid. So the root-cause claim is not a theory about what would happen after a sweep; it is a measured RATE. Two consequences worth carrying. FIRST, the sweep's cost rises with every day this Set waits on its gate, so the two blocking questions below are the expensive part of this plan and are worth putting to the maintainer promptly. SECOND, Order 01's evidence must be measured at ITS OWN execution time and never against a number written here, because by then the population will have moved again.
  ONE OF THE ITEM'S SIX DELIVERABLES IS ALREADY DONE AND MUST NOT BE REBUILT. Deliverable #3 (setter UX: resolve a setid WITHIN the requested type) landed in `9107790` with coverage in `tests/test_status_set.py`, and the item's own Progress note records it. Deliverable #1 is HALF done in a way that is easy to misread: the severity is ALREADY `error` (`check_engine.py:95`), so the remaining work is not a severity flip but retiring the soft/whitelistable POSTURE the spec's I2 names, and proving the rule is actionable, which is impossible while 29 benign findings stand.
  THE SPEC IS `draft` AND CARRIES THREE OPEN QUESTIONS, which is the gate on this whole Set rather than a detail. `4w7d6s` is `- Status: draft` with OQ-01 (does `Graduated-To` cover spec-to-spec), OQ-02 (does I1 over-constrain legitimate within-type clustering), OQ-03 (is a fresh-setid mint compatible with the same-name mental model) all `- Status: open`. Its own header says "REVISABLE before implementation" and the backlog item says implement it "once the spec is reviewed". OQ-02 and OQ-03 are not cosmetic: OQ-02 decides whether the predicate this Set hardens is even correct, and OQ-03 decides Order 03's whole user-visible behavior.
- Scope: Coordinate a four-child Set that makes a setid a cross-type-unique identity in the order the spec requires: prevent new collisions at their source, clear the existing ones, add the typed forward link that removes the need for a shared setid, and only then hold the hard posture. This orchestrator changes NO product code; it sequences the children, verifies the whole-Set acceptance criteria, and holds the spec-approval gate. Deliverable #3 is EXCLUDED as already landed.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: setidhard
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yku4ga
- From-Backlog: sjsoqq

## Workflow history
- 2026-09-09 reviewed (aw set): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-701..PR-707; PR-701 (BLOCKER) left OPEN, both blocking maintainer questions unanswered (no interactive channel); readiness no-go.

- 2026-09-08 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-701..PR-707, six FIXED and PR-701 (BLOCKER) left OPEN. Readiness NO-GO. Record: `.aw/records/reviews/20260908-setidhard-00-yku4ga-make-a-setid-a-hard-cross-type-unique-identity-and-replace-s.review.md`. STRUCTURAL PREFLIGHT DOES NOT CLEAR AND THAT IS CORRECT: `aw ipd lint --phase author` returns EXIT 1 with two `IPD-Q501` diagnostics, one per `Blocking: yes` question, and both questions are `- Owner: maintainer`. This review ATTEMPTED to put them to the maintainer and found NO interactive channel in this session, so under the workflow's non-interactive exception both are left explicitly OPEN rather than converted into an agent decision. They are now machine-linked to PR-701 via a typed `- Finding:` subfield on each. THE DESIGN NEEDED NO CHANGES: the sequencing argument verified link by link (the severity really is already `error` at `check_engine.py:95`; the spec's Section 5 really does require the sweep before hard enforcement; the Order-versus-dependency inversion is correctly encoded and `queue_sort_key`'s docstring confirms declared edges win over Order digits; `check_from_backlog` really is the mirror to copy; `Graduated-To` really has zero occurrences; `ipd_authoring` really consults no setid predicate; the `agentadhere` target really persists; and the retirement hazard is real, with `84j8d7` still in `executed/` carrying `Execution state: pending` on E-01). WHAT REVIEW CORRECTED IS MEASUREMENT DRIFT, all of it one day old. The two headline counts were stale: 40 findings across 30 setids, not 29 across 21, and the `aw check all` total is 238, not 98. THE SHAPE CLAIM HELD EXACTLY (all 40 locations are backlog-side, zero plan-side). THE GROWTH IS THE ONE NEW FACT AND IT STRENGTHENS THE SET: eleven new findings and nine new setids appeared in a SINGLE DAY, every one from an ordinary graduation, so the root-cause claim is now a measured rate rather than a prediction, and the sweep's cost rises while the gate is unanswered. Also fixed: the spec is NOT findable by id6 glob (its filename is the legacy pre-cutover form, so `ls specs/*4w7d6s*` returns nothing and E-02's whole job would misfire); the plan implied the SPEC's questions were the gate when all three are `Blocking: no` and the real hold is this plan's own two; and the suite baseline was stale in both halves with a different, environmental failing node. Four decisions recorded (D-1..D-4); D-1 is `Reversible: no` and is escalated by both blocking questions, which is why it is not merely recorded.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `sjsoqq` as a four-child Set, NARROWED and RE-SEQUENCED. Deliverable #3 is DEAD (landed in `9107790`, verified, with its test coverage) and is excluded. Deliverable #1 is HALF dead in a misleading way: `check.setid-collision` is ALREADY severity `error` at `check_engine.py:95`, so the remaining work is the POSTURE and the actionability, not a severity flip. THE MEASUREMENT THAT SHAPED THE SEQUENCE: 29 findings across 21 distinct setids existed at authoring and ALL were the benign backlog-shares-its-plan's-setid pattern (re-measured at review: 40 across 30, same shape), so the sweep (Order 01) cannot precede the root-cause fix (Order 03) without being immediately undone, and enforcement cannot precede either without mass-failing plans four agents are executing. The item's own claim that "`aw check all` now reports 0 setid-collision findings" is STALE and was corrected by measurement: it reported 29 at authoring and 40 at review. AUTHORING NOTE, recorded because it is this Set's best evidence for its own necessity: scaffolding these four plans into `Set: setiduniq` immediately created the exact collision the Set exists to prevent (with backlog `sjsoqq`), and they were regrouped to `setidhard` per the spec's own G1. Doing that also surfaced a TOOL DEFECT worth reporting separately: `aw group plans <id> --set X --rename --apply` with no `--order` reset all four plans' Order to `00`, including three children, silently producing three Order-0 children in one Set.

## Goal

Make a setid mean exactly one thing (the identity of one Set, in one tree) so a rule the catalog already calls an error becomes a rule an agent can act on, and so graduation records its lineage in a typed link instead of a colliding name.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set and hold its gate

- [ ] E-01 EXECUTE THE CHILDREN IN THE DECLARED ORDER AND CONFIRM EACH REACHED `executed` BEFORE THE NEXT BEGINS. The order is a spec requirement, not a preference, so this item exists to make it explicit for an agent told simply to "execute `setidhard`".
  THE CHILD TABLE AND THE DEPENDENCY REASONING LIVE IN `## Child IPDs, sequence, and dependencies` below; read it rather than re-deriving the order. The one rule to carry here: dispatch by the DEPENDENCY EDGES, not the Order digits, because the declared order (01, 02, 03) and the dependency order (02, 03, 01) deliberately differ.
  - Depends on: none
  - Expected outcome: each child reaches `executed` with its dependency edges satisfied; the sweep runs after the root-cause fix; nothing is executed while the spec gate below is unmet.
  - Execution state: pending

- [ ] E-02 HOLD THE SPEC-APPROVAL GATE, and do not treat it as paperwork. Spec `4w7d6s` is `- Status: draft` and carries THREE open questions, two of which change what the children build.
  FIND THE SPEC BY id6 SEARCH, NOT BY FILENAME (F-14). Its name is the LEGACY pre-cutover form with no id6 in it: `.aw/records/specs/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`. A glob for `*4w7d6s*` under `specs/` matches NOTHING, so an executor doing the obvious lookup will report the spec missing and either stop for the wrong reason or, worse, conclude the gate is vacuous. Use `rg -l 4w7d6s .aw/records/specs/`. Verified at review: the file is present, `- Status: draft`, `- Id: 4w7d6s`, three OQs open.
  AND NOTE WHERE THE BLOCK ACTUALLY LIVES (F-15): all three of the SPEC's open questions carry `- Blocking: no`. What stops this Set is THIS plan's own OQ-01 and OQ-02, both `Blocking: yes`, which `aw ipd lint` refuses at every checkpoint from `author` onward. So do not report "the spec's questions are non-blocking, therefore we may proceed": the gate is this plan's, and it is a lint-enforced refusal rather than a judgement call.
  WHY THIS IS A REAL GATE. OQ-02 asks whether I1 over-constrains legitimate WITHIN-type clustering (same setid, same type, same descriptive, different Order), which is the normal shape of every multi-child Set in this repository, including this one. If the answer is that the predicate must distinguish those, then the predicate the whole Set hardens needs correcting first. OQ-03 asks whether a fresh-setid mint is compatible with the same-name mental model, which is Order 03's entire user-visible behavior. The backlog item's own instruction is to implement the spec "once the spec is reviewed", and the spec's header says "REVISABLE before implementation".
  DO NOT SET THE SPEC APPROVED YOURSELF, and do not write an approval attestation. `aw spec set approved <id6> --by-human --message ...` records a HUMAN's ruling; an agent writing it forges the attestation. Report that the gate is unmet and stop.
  RE-READ THE SPEC AT EXECUTION TIME rather than trusting this plan's summary of it. If the spec has since been revised, the children's requirements move with it, and this orchestrator's job is to notice that rather than to execute a stale reading.
  - Depends on: none
  - Expected outcome: a written statement of the spec's status and each OQ's disposition at execution time; execution proceeds only if the spec is approved (or the maintainer explicitly authorizes proceeding), and refuses otherwise with the reason.
  - Execution state: pending

### Task group 2: verify the whole Set

- [ ] E-03 VERIFY THE SPEC'S SIX ACCEPTANCE CRITERIA AS A SET, after every child has executed, because no single child can demonstrate them and this is the only place they meet.
  THE SIX, from spec Section 6, each needing whole-Set evidence: (1) the rule is fail-closed in `aw check`/`aw doctor`, NO tree carries a cross-type duplicate, and `agentadhere` specifically is resolved; (2) creation/move verbs refuse a cross-type duplicate with an actionable message; (3) `aw ipd set <setid>` resolves within the requested type (ALREADY TRUE via `9107790`, so this is a regression check, not new work); (4) `Graduated-To` exists, is multi-valued, is written by graduation, and `check.graduated-to-dangling` flags an unresolved entry; (5) graduation mints a fresh child setid and each direction of the link resolves; (6) the migration sweep resolved everything and the full suite plus `aw check all` are green after enforcement.
  CRITERION 6's "GREEN" NEEDS A HONEST DEFINITION, because `aw check all` is NOT green today and will not be made green by this Set. It reports 238 findings at review (174 `check.scope-drift`, 40 this rule) across many rules this Set does not touch; the plan's authoring figure of 98 is stale. So the criterion this Set can actually meet is: `check.setid-collision` is ZERO, and no OTHER rule's count rose. Compare per RULE, never by total, and say so in the evidence rather than reporting a total that cannot reach zero.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. MEASURE YOUR OWN BASELINE; this plan's is stale in both halves. Re-measured at review (HEAD `15dba2d7`): `1 failed, 5919 passed, 3 skipped, 2 xfailed in 49.87s`, and the failing node is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL (a gitignored local dump the test's skip list does not cover) and may be absent in your checkout. The previously-named `tests/test_orchestrator_retirement.py` failure now PASSES. The "roughly 32 environmental failures in a lane worktree" figure is also stale: a fresh linked worktree measured CLEANER than the primary checkout. Criterion: AFTER minus BEFORE is EMPTY.
  - Depends on: E-01
  - Expected outcome: all six criteria evidenced with whole-Set proof; `check.setid-collision` at zero with no other rule's count risen; bare-suite delta empty with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SEVERITY IS ALREADY `error`. `check_engine.py:95` registers `check.setid-collision` as `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09")`, alongside `check.id6-collision`. The item's deliverable #1 is therefore about POSTURE and actionability, not a severity flip. Do not "promote" what is already promoted.
- EVERY ONE OF THE LIVE FINDINGS IS BENIGN, and they are all the same shape: a backlog item sharing its setid with the plan Set it graduated into. RE-MEASURED AT REVIEW: FORTY findings across THIRTY distinct setids, and ALL 40 locations sit in `.aw/records/backlog/` (zero on the plan side), which confirms the shape claim exactly while correcting the counts. The authoring figures (29/21) are stale. This is why the rule is unactionable today and why Order 03 is the root-cause fix.
- DELIVERABLE #3 IS DONE (`9107790`, with `tests/test_status_set.py` coverage). Excluded from this Set.
- `check_from_backlog` (`releases.py:580`) IS THE EXACT MIRROR for `check.graduated-to-dangling`: it scans plans/specs/backlog by `rglob`, tolerates the field anywhere for symmetry, resolves against `backlog.existing_backlog_ids`, and rides the once-per-full-sweep seam. Order 02 must follow it rather than invent a shape.
- NOTHING PREVENTS A COLLISION AT CREATION TODAY: `ipd_authoring` has no setid-collision consultation at all (searched). That is Order 03's I3 half.
- THE SPEC IS `draft` WITH THREE OPEN QUESTIONS and says "REVISABLE before implementation". Two of the three change what the children build. VERIFIED AT REVIEW, and note two things the plan does not say. FIRST, ITS FILENAME CARRIES NO id6 (F-14): the spec is the legacy pre-cutover `.aw/records/specs/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`, so `ls .aw/records/specs/*4w7d6s*` returns NOTHING and an executor searching by id6 filename will think its source of truth is missing. Find it by `rg -l 4w7d6s .aw/records/specs/` or by title. SECOND, ALL THREE OF THE SPEC'S OWN OQs ARE `- Blocking: no` (F-15); what holds this Set is THIS plan's own OQ-01 and OQ-02, both `Blocking: yes`, which the lint refuses at every checkpoint. Do not go looking for a block inside the spec.
- `aw check all` IS NOT GREEN and will not be made green here. RE-MEASURED AT REVIEW: 238 findings total, not 98, of which 174 are `check.scope-drift` and 40 are `check.setid-collision`. So the total more than doubled in a day and is even less usable as a criterion than the plan assumed. Compare per RULE, and measure the totals yourself rather than quoting either figure.
- `aw group plans <id> --set X --rename --apply` WITHOUT `--order` RESETS Order TO `00`. Measured at authoring: all four of this Set's plans became Order 0, including three children. Pass `--order` explicitly. (Reported separately as a tool defect; not this Set's work.)
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the rule is unactionable today | `check.setid-collision` findings are ALL the benign backlog-shares-its-plan's-setid pattern, so a rule the catalog calls an error fires on the repo's own working convention. COUNTS RE-MEASURED AT REVIEW: 40 findings across 30 distinct setids (authoring recorded 29 across 21; see F-13 for the growth). All 40 locations are in `.aw/records/backlog/`. | `aw check all --agent` at HEAD `15dba2d7`, grouped by rule and setid |
| F-2 | HIGH | the item's own status claim is STALE | It says "`aw check all` now reports 0 setid-collision findings". Measured: 29. The item's accompanying claim that the collision "PHYSICALLY persists" is still true. | `aw check all --agent` at HEAD |
| F-3 | HIGH | order is a spec requirement | Spec Section 5: a sweep MUST resolve existing collisions "before I2 is turned on fail-closed, so enabling the hard rule does not mass-fail the tree". Enforcing first would block plans four agents are executing. | `4w7d6s` Section 5 |
| F-4 | HIGH | but the sweep alone is not durable | The next graduation recreates a collision. DEMONSTRATED at authoring: scaffolding this Set into `Set: setiduniq` instantly collided with backlog `sjsoqq`. Hence Order 03 before Order 01. | measured; the regroup to `setidhard` |
| F-5 | HIGH | the spec gate is real, not paperwork | `4w7d6s` is `- Status: draft` with OQ-01/02/03 all `open`. OQ-02 questions whether the predicate this Set hardens is correct for within-type clustering; OQ-03 decides Order 03's user-visible behavior. | the spec's front matter and Section 7 |
| F-6 | MEDIUM | deliverable #1 is HALF done and easy to misread | `check.setid-collision` is ALREADY `error` at `check_engine.py:95`. The remaining work is retiring the soft/whitelistable posture I2 names and making the rule actionable. | `check_engine.py:95` |
| F-7 | MEDIUM | deliverable #3 is fully done | Setter type-scoping landed in `9107790` with `tests/test_status_set.py` coverage, per the item's own Progress note. Excluded. | the item's Progress note; the test file |
| F-8 | MEDIUM | the migration target still exists | The closed backlog item `3gr7fk` still carries `- Set: agentadhere`, sharing it with eight executed plans. The named migration case is real. | `grep 'Set: agentadhere' .aw/records/` |
| F-9 | MEDIUM | the mirror to follow already exists | `check_from_backlog` (`releases.py:580`) is the dangling-check shape `check.graduated-to-dangling` should copy: rglob over three trees, resolve against a known-id set, once per full sweep. | `releases.py:580-619` |
| F-10 | MEDIUM | nothing prevents a collision at creation | `ipd_authoring` consults no setid-collision predicate (searched: zero hits). I3 is genuinely unbuilt. | grep over `ipd_authoring.py` |
| F-11 | LOW | `Graduated-To` does not exist anywhere | Zero occurrences in the package. Order 02 builds it from nothing. | grep over `agent_workflows/` |
| F-12 | LOW | a tool defect was found while authoring | `aw group plans <id> --set X --rename --apply` with no `--order` reset all four plans to Order `00`, producing three Order-0 children. Reported separately; not this Set's work. | measured at authoring |
| F-13 | HIGH | **the collision population is GROWING, which strengthens the Set's own case** | Re-measured at review one day after authoring: 40 findings across 30 distinct setids, up from 29 across 21, so ELEVEN new benign collisions and NINE new setids appeared in a single day. ALL 40 locations are in `.aw/records/backlog/` (zero plan-side), confirming the shape claim exactly. This is Order 03's root-cause argument measured in the wild rather than predicted, and it also means the sweep's cost rises with every day the Set waits. | `aw check all --agent` at HEAD `15dba2d7`, grouped by rule and by setid tree |
| F-14 | HIGH | **the spec exists but NOT at a path the plan's citation implies** | The plan cites spec `4w7d6s` throughout and it does resolve, but its filename is the LEGACY pre-cutover form `.aw/records/specs/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`, which carries no id6 in the name. So `ls .aw/records/specs/*4w7d6s*` returns NOTHING and an executor searching by id6 filename will conclude its single source of truth is missing. Verified present with `- Status: draft`, `- Id: 4w7d6s`, and all three OQs `- Status: open`. | `rg -l 4w7d6s .aw/records/`; the file's front matter read directly |
| F-15 | MEDIUM | the spec's three OQs are all NON-blocking on the spec itself | Measured: OQ-01, OQ-02 and OQ-03 in `4w7d6s` each carry `- Blocking: no`. That does NOT weaken this plan's gate (its own OQ-01/OQ-02 are `Blocking: yes` and are what the lint holds), but the plan describes the spec's questions in a way that reads as if the spec itself were blocked. State the distinction so an executor does not look for a block that is not there. | the spec's `### OQ-*` blocks, lines 135-157 |
| F-16 | MEDIUM | every child, edge and id6 in the child table verifies EXACTLY | Measured: `drzbs9` Order 1 `Item-Dependencies: executed:dw7i3m`; `bwgyum` Order 2 `none`; `dw7i3m` Order 3 `executed:bwgyum`. All three `Kind: child`, all three `to-review`. So the declared-order-versus-dependency-order inversion the plan describes is real and correctly encoded, and `queue_sort_key`'s docstring confirms dependency depth is the FIRST sort key with declared edges winning over Order. | the three child files; `oc_runipd.py:3838-3845` |
| F-17 | LOW | the retirement hazard the plan warns about is real and already in the record | Verified: the executed plan `84j8d7` still carries `- Execution state: pending` on E-01 and `- Result: pending` on V-01 while sitting in `executed/`, so the false-completion class the gate paragraph cites is not hypothetical. Backlog `5ev6lh` is graduated into the `orchprobe` Set as the plan says. | `grep` over the executed plan; `5ev6lh`'s workflow history |

## Proposed changes (ordered, validatable)

1. Sequence the children by their dependency edges, not their Order digits, and confirm each reaches `executed` (E-01).
2. Hold the spec-approval gate and refuse to execute a draft spec's design, without forging an approval (E-02).
3. Verify the spec's six acceptance criteria as a Set, comparing `aw check` per rule rather than by total (E-03).

## Child IPDs, sequence, and dependencies

| Order | Id | What it delivers | Why it sits here |
|---|---|---|---|
| 01 | `drzbs9` | Resolve every pre-existing cross-type setid collision (the sweep, spec Section 5) | Must run BEFORE the hard posture is held, or every benign finding becomes a blocking failure. Must run AFTER Order 03, or the next graduation recreates a collision immediately. |
| 02 | `bwgyum` | `Graduated-To` forward link + `check.graduated-to-dangling` (spec G3/G5) | The typed link is what makes a shared setid UNNECESSARY, so it must exist before Order 03 stops minting one. |
| 03 | `dw7i3m` | Fresh child setid on graduation + prevention at every creation/move verb (spec G1/I3) | The ROOT CAUSE. Every live finding was created by a graduation reusing its source's setid, and the population grew from 29 to 40 in one day (F-13), so this is the item that stops the bleeding. |

THE DECLARED ORDER IS 01, 02, 03 BUT THE DEPENDENCY ORDER IS 02, 03, 01, and that tension is deliberate and must be honored via `Item-Dependencies` rather than by renumbering. `drzbs9` (the sweep) carries `Item-Dependencies: executed:dw7i3m` precisely because sweeping before the root cause is fixed is wasted work: the next graduation would recreate a collision. `dw7i3m` in turn carries `Item-Dependencies: executed:bwgyum`, because it may only stop minting a shared setid once the typed forward link that replaces it exists.

THE RUNNER WILL DISPATCH THIS CORRECTLY WITHOUT RENUMBERING. `aw oc run` / `aw agy run` sort the queue with DEPENDENCY DEPTH as the first sort key (`queue_sort_key` / `dependency_depth` in `oc_runipd.py`) and re-check edges at dispatch, so a dependent never precedes its dependency. A HUMAN executing this Set by hand must read the dependency edges, not the Order digits, and the digits are kept as authored so the filenames stay stable for the citations already written against them.

## Completion criteria (the whole Set is done only when)

1. All three children are `executed` on disk, with `drzbs9` demonstrably finalized AFTER `dw7i3m`.
2. `check.setid-collision` reports ZERO findings, and no other `aw check` rule's per-rule count has risen (40 of 238 findings at review were this rule; the total cannot reach zero and is not the criterion).
3. `aw doctor` and `aw check all` agree on the setid-collision set, since the two surfaces have disagreed before on the id6 twin.
4. `Graduated-To` exists, is multi-valued, is written by graduation, and `check.graduated-to-dangling` fires on a deliberately broken forward link.
5. A graduation round trip mints a FRESH child setid and both link directions resolve.
6. The bare suite's AFTER failure set minus its BEFORE set is EMPTY.
7. Spec `4w7d6s` has been answered by a human on OQ-01/02/03 and moved off `draft` by the attested route; the Set does NOT complete on an agent-written status.

## Cross-IPD validation

- CID-1 THE SWEEP MUST NOT PRECEDE THE ROOT-CAUSE FIX. Verify by comparing `drzbs9`'s and `dw7i3m`'s finalize commits, not by trusting the Order digits. A sweep that ran first is wasted work and its result cannot be trusted, because any graduation between the two would have recreated a collision.
- CID-2 NO CHILD MAY LEAVE THE RULE UNACTIONABLE. After the Set, `check.setid-collision` must be zero. A child that resolves some collisions and leaves others has produced the same unactionable rule the Set exists to fix, only with a smaller number.
- CID-3 NO OTHER RULE'S COUNT MAY RISE. Orders 02 and 03 add a field and a check plus refusals at several verbs; each could plausibly introduce a naming or dangling finding elsewhere. Compare per rule, before and after the whole Set.
- CID-4 THE TWO LINK DIRECTIONS MUST BE VALIDATED INDEPENDENTLY. `From-Backlog` resolution (existing) and `Graduated-To` resolution (Order 02, new) are different scans over different trees; passing one proves nothing about the other, and the spec's G5 requires both.
- CID-5 NO PLAN SET THAT IS MID-EXECUTION MAY BE RENAMED. Several of the colliding setids (30 measured at review, 21 at authoring) belong to plans that are approved or executing under other agents. Order 01 must evidence, per collision, that it renamed the source rather than a live Set (OQ-03).
- CID-6 THE ALREADY-SHIPPED BEHAVIOR MUST STILL HOLD. Deliverable #3 (setter type-scoped resolution, `9107790`) is excluded from this Set as done; Order 00's E-03 must confirm it as a REGRESSION check, so an incidental change to selector resolution cannot silently undo it.

## Deferred / out of scope (with reason)

- DELIVERABLE #3 (setter type-scoped resolution). Already landed in `9107790` with test coverage. Rebuilding it would duplicate shipped work; Order 00's E-03 checks it as a REGRESSION only.
- THE id6 IDENTITY INVARIANT. Already hard (D140, `check.id6-collision`, `check.id6-identity-slot`) and explicitly out of scope in the spec. Separately, `sk7ggr` (`id6integ-01`, graduated from `wx95o4`) is in flight on the id6 side and this Set must not touch it.
- THE FILENAME GRAMMAR ITSELF. Unchanged, per the spec's Scope; the parent naming spec is `implemented` and transition-frozen.
- THE RUNNER. Named out of scope by the spec. No child touches `oc_runipd.py` or `agy_runipd.py`.
- MAKING `aw check all` GREEN OVERALL. Impossible here and not attempted: 238 findings measured at review (174 of them `check.scope-drift`) span rules this Set does not own; the authoring figure of 98 is stale. The honest criterion is `check.setid-collision` at zero with no other rule's count risen.
- SPEC-TO-SPEC AND BACKLOG-TO-SPEC GRADUATION LINKS. The spec's own OQ-01 defers this; `Graduated-To` targets plan Sets by default and generalizes only if a real case appears.
- FIXING `aw group`'s ORDER RESET (F-12). A real defect found while authoring this Set, but it is a separate surface with its own tests, and folding it in would mean this Set's Scope-Paths grew to cover an unrelated verb. Reported to the maintainer instead.

## Scope check

- Over-scope: none. This orchestrator writes no product code; it sequences, gates, and verifies.
- Scope-Paths justification: `.aw/records/plans/pending` only, because an orchestrator's deliverable is coordination plus the whole-Set verification record. Every product-code path is declared by the child that edits it, which is what makes the runners' pre-run announcement and the finalize scope gate meaningful per child.
- Under-scope, stated rather than left as `none`: this orchestrator does not itself resolve any collision, does not add `Graduated-To`, does not change any verb, and does not approve the spec. Each is either a child's job or a human's.

## Required tests / validation

- `python3 -m pytest` BARE after the last child, with the summary line pasted. MEASURE YOUR OWN BASELINE (the plan's `1 failed, 5648 passed` is stale; review measured `1 failed, 5919 passed, 3 skipped, 2 xfailed`, with a DIFFERENT and environmental failing node). Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- `aw check all --agent` PER-RULE counts before the Set and after, pasted. `check.setid-collision` must be ZERO; no other rule's count may rise. Baseline RE-MEASURED at review: 238 findings total, 40 of them `check.setid-collision`, 174 of them `check.scope-drift`. Both authoring figures (98 total, 29 this rule) are stale; measure your own before and after.
- `aw doctor` agreeing with `aw check all` on the setid-collision set, since the two surfaces have disagreed before on the id6 twin.
- THE SPEC'S SIX ACCEPTANCE CRITERIA each evidenced individually (E-03), including criterion 3 as a regression check on already-shipped behavior.
- A GRADUATION ROUND TRIP end to end: graduate a fixture source, confirm a FRESH child setid, confirm both link directions resolve, and confirm `check.graduated-to-dangling` fires on a broken forward link.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `4w7d6s` is this Set's single source of truth and is `draft`. It is NOT declared in this orchestrator's `Scope-Paths` because this plan does not amend it; if the maintainer's answers to OQ-01/02/03 require spec text changes, the plan making them must declare the spec file itself, per the spec-amendment rule.

On completion the spec should move to `implemented` by the normal attested route with cited evidence, and its three open questions must carry recorded resolutions rather than being left open behind an implemented status. That transition is a human-attested act; an agent may not set `implemented` without cited evidence and may not set `approved` at all without the maintainer's instruction.

`.aw/records/backlog/README.md` documents the promotion convention ("author an IPD ... then `aw backlog set <item> --status done`"). Once `Graduated-To` exists (Order 02) that prose is incomplete, since graduation will also write a forward link. Order 02 owns that documentation edit and must declare the README in its own `Scope-Paths`.

Write no em or en dashes in user-facing prose any child authors.

## Open questions

### OQ-01: May this Set execute while spec `4w7d6s` is still `draft` with three open questions?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-701
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10, AND THE HONEST ANSWER IS NOT "YES" OR "NO" BUT "THE SET AS DESIGNED MUST NOT EXECUTE AT ALL". The question asked whether the Set may run while spec `4w7d6s` was `draft` with three open questions. Those three are now resolved (`c2d80c49`), and resolving them REVERSED the spec's central invariant rather than confirming it, so the gate this question holds is not cleared, it is superseded.
  WHAT THE MAINTAINER DECIDED, recorded here because this plan must not be read as merely waiting: a setid is a SHARED, CROSS-TYPE TOPIC LABEL, not a unique identity. Research, specs, prompts, backlog items and plans concerning one issue may all carry the SAME setid, and that is CORRECT, because it is what makes a topic visible from filenames alone. The real defect behind this whole effort was a LOOKUP defect, not a naming defect. Their framing: artifacts concerning one issue are naturally one set to a user, and a shared setid makes that relationship obvious while distinct setids OBFUSCATE it.
  SO THE SPEC'S NORMATIVE ITEMS SPLIT. DEAD: I1 (cross-type uniqueness), I2's hardening direction (it must be DOWNGRADED, not promoted), I3 (prevention at creation), G1 (fresh child setid on graduation). SURVIVING: I4 (type-scoped setter resolution), which becomes the whole point; and G2/G3/G4/G5 (the id6-keyed graduation links). The replacement work is type-scoped resolution plus a re-scoped collision check, not enforcement.
  CONSEQUENCE FOR THIS ORCHESTRATOR: RE-SCOPE, DO NOT SILENTLY PROCEED. Two of its three children die (`dw7i3m` implements G1+I3, `drzbs9` sweeps collisions that are now correct) and one survives (`bwgyum`, which builds G3/G5). This plan no longer describes its Set, so it must either narrow to the surviving link work plus the new resolution fix, or be retired so the replacement spec graduates a fresh Set. That is checklist item T-07 and it is NOT done by this answer.
  DELIBERATELY NOT DONE HERE: no plan is retired and no readiness is cleared. Retirement waits on the replacement spec, and `drzbs9`'s `executed:dw7i3m` edge must be cleared in the same pass or it will point at something that never executes.

### OQ-02: Does hard cross-type uniqueness break the legitimate backlog-to-plan naming convention this repository actually uses?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-701
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10: YES, IT BREAKS IT, AND THAT IS WHY THE DESIGN IS REVERSED. This question named the tension correctly and its instinct was right: the backlog-to-plan name match is not sloppiness, it is how a reader sees at a glance that an item and the plan Set it graduated into are the same work. The maintainer chose to keep that and to discard the uniqueness invariant.
  THE MEASUREMENTS BEHIND THE RULING, taken before the decision and reproducible, are larger than this plan's 40-findings-across-30-setids figure. Of 433 distinct filename-slot setids, 117 SPAN MORE THAN ONE RECORD TYPE, and the widest are genuine topics (`agentadhere` = 7 plans + 1 backlog item + 5 research reports; `lanectn` = 7 plans + 7 reviews + 1 walkthrough). I1 would have forbidden all 117. Sharing is also partly AUTOMATIC AND DELIBERATE: `review_findings.build_review_name` builds a review's filename from the SUBJECT's setid and id6, documented there as "the join key ... not a fresh identifier", so plans-plus-reviews sharing a setid is designed behavior and accounts for 47 of the 117.
  AND THE CHECK IS MISLABELLING CORRECT BEHAVIOR. `check.setid-collision` ships at severity `error` (`check_engine.py:95-97`) and reports 38 findings on the default scope, 86 with `--all` (both figures re-verified 2026-09-10). Of the 86, 78 are the backlog-plus-plans topic sharing now ENDORSED, 2 plans-plus-research, 1 plans-plus-walkthrough, and only 5 are within-type conflicting-descriptive cases that remain genuine defects. So the rule must be re-scoped rather than deleted: the within-type half is load-bearing.
  THE MOTIVATING FAILURE WAS A LOOKUP DEFECT, WHICH IS THE REAL FIX. The spec's own evidence was `aw ipd set approved agentadhere` failing with "selector 'agentadhere' resolved to artifact(s) of type ['backlog', 'research'] ... scoped to 'plans'": the setter held BOTH the setid and the target type and still gave up, when resolution by `(type, setid)` was available and unused. Fixing that is the surviving deliverable.
  ACCEPTED COST, STATED BECAUSE IT IS REAL: a bare setid stays AMBIGUOUS by design, so every name-taking verb needs a type scope or a disambiguating prompt. The maintainer judged filename-level topic discovery worth more than global uniqueness.
  AN IRONY WORTH RECORDING SO IT IS NOT RE-DISCOVERED AS EVIDENCE: this Set exists partly because scaffolding it as `setiduniq` instantly collided with its own source backlog item `sjsoqq`, and the plans cite that as live proof of the defect. Under the reversal that collision was CORRECT BEHAVIOR, so the demonstration proved the opposite of what it was read as proving.

### OQ-03: Should the migration rename the SOURCE or the PLAN Set in each collision (30 setids measured at review, 21 at authoring)?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED TO ORDER 01, which owns the sweep, but flagged here because the two choices have very different costs and the cheap-looking one is wrong. Renaming the PLAN Set touches plan filenames, which are cited by id6 and setid across reviews, `Item-Dependencies`, run records and prose, and several of the affected Sets are approved or executing RIGHT NOW. NOTE THE MEASUREMENT THAT MAKES THE ANSWER EASIER (F-13): all 40 findings sit on the BACKLOG side, so renaming the source is a one-file edit per collision and touches no plan filename at all. Renaming the SOURCE (the backlog item) touches one file per collision and its `Graduated-To` forward link then records the relationship. The spec's Section 5 precedent points the same way: for `agentadhere` it says to "re-group the closed backlog item to its own unique setid", i.e. rename the source. Order 01 must state its choice per collision and must not rename a Set that is mid-execution.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste each child's final `- Status:` and its lifecycle directory, proving all three reached `executed`. Paste the dependency edge on `drzbs9` and evidence it executed AFTER `dw7i3m` (compare their finalize timestamps or commits), since sweeping before the root-cause fix is the sequencing error this item exists to prevent. If any child was executed out of dependency order, report it as a finding rather than accepting the end state.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste spec `4w7d6s`'s `- Status:` line and each of its three OQ `- Status:` lines AS READ AT EXECUTION TIME, not as quoted by this plan, AND paste the command you used to locate the file, showing you found it by id6 search rather than by a filename glob that cannot match (F-14). If the spec is still `draft`, paste the refusal and confirm in one sentence that no child was executed. If it is approved, paste the attesting `## Workflow history` line showing a human recorded it, and confirm you did not write that line yourself.
    ALSO PASTE THIS PLAN'S OWN OQ-01 AND OQ-02 STATUS LINES, because those are the questions that actually gate the Set and both are `Blocking: yes`. Reporting the spec's three non-blocking questions as though they were the gate is a FAILED validation (F-15).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the six acceptance criteria one at a time with the ACTUAL command output evidencing each, including criterion 3 as a regression check. Paste `aw check all --agent` PER-RULE counts before and after, showing `check.setid-collision` at ZERO and no other rule's count risen; do NOT report a total, which cannot reach zero (238 measured at review, 98 at authoring; both stale by the time you run). Paste `aw doctor`'s setid-collision set and confirm it agrees with `aw check all`. Paste the graduation round trip, including `check.graduated-to-dangling` firing on a deliberately broken forward link. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS SET CARRIES TWO BLOCKING OPEN QUESTIONS AND MUST NOT EXECUTE UNTIL BOTH ARE ANSWERED. OQ-01 is the spec-approval gate; OQ-02 asks whether hard cross-type uniqueness is even the right answer given that all live findings are the repository's own working convention. The refusal is MECHANICAL, not advisory, and was measured at review: `aw ipd lint` returns exit 1 on this plan with two `IPD-Q501` diagnostics naming both questions, and it does so from the `author` checkpoint onward rather than only at `pre-execution`. So this plan cannot reach `approved` or be executed while they stand, which is exactly the intended behavior.

BOTH QUESTIONS ARE THE MAINTAINER'S AND REVIEW COULD NOT ASK THEM. `/plan-review` on 2026-09-08 tried and found no interactive channel in that session, so both are left explicitly OPEN with their required decisions stated. Nothing in this Set has been decided by an agent, and no readiness has been claimed beyond `no-go`.

WHY THAT IS THE RIGHT POSTURE RATHER THAN OVER-CAUTION: this Set's first live act would be to change a naming convention every future graduation follows, and its sweep would rename artifacts belonging to 30 setids (measured at review, up from 21 at authoring), several of which are approved or executing right now under other agents. That is a maintainer decision about how they read their own tree, and it is cheaper to ask than to sweep and revert.

AND THE COST OF WAITING IS NOW MEASURED, which is the one thing review can add to the decision (F-13): the collision population grew from 29 findings across 21 setids to 40 across 30 in a SINGLE DAY, every new one produced by an ordinary graduation. So the queue of work Order 01 must sweep grows while the gate is unanswered. That is an argument for asking promptly, not for proceeding without an answer.

EXECUTION CONTRACT for every child. Commit only files that child changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME rather than by the line numbers cited here. Do NOT rename any plan Set that is mid-execution (OQ-03). Do NOT set spec `4w7d6s` to `approved` or `implemented`; those are attested human acts. Paste ACTUAL command output, and compare `aw check` findings PER RULE, never by total. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. This orchestrator retires only when every child is `executed` on disk. Do not claim done or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and V-01..V-03 carry concrete pasted evidence. NOTE the rollup deliberately SKIPS an orchestrator's own E/V checkpoint (backlog `5ev6lh`, graduated into the `orchprobe` Set), so E-03's whole-Set verification is exactly the class of parent-only work that gets discharged unperformed by a runner retirement. If this Set is run by `aw oc run` or `aw agy run`, E-03 must be performed by hand before the parent is retired, or its evidence will be a false completion claim of precisely the kind `84j8d7` already put in the permanent record.
