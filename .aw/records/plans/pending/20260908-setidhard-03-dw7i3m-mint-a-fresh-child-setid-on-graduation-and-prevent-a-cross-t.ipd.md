# IPD: Mint a fresh child setid on graduation and prevent a cross-type duplicate at every creation and move verb

- Date: 2026-09-08
- Kind: child
- Concern: NOTHING PREVENTS A CROSS-TYPE SETID COLLISION AT CREATION, WHICH IS WHY ALL TWENTY-ONE OF THEM EXIST. Measured: `ipd_authoring` consults no setid-collision predicate at all (zero hits searching for one), so `aw ipd scaffold --set <token>` will happily mint a Set whose token a backlog item already owns. Contrast id6, where minting IS collision-checked (`artifact_core.generate_id6(existing)` takes a set of taken ids and every mint site supplies one). The setid has an identity rule and no gate; the id6 has a gate. This child adds the missing gate and removes the practice that keeps tripping it.
  THIS WAS DEMONSTRATED WHILE AUTHORING THIS VERY SET, not reasoned about. Scaffolding these four plans with `--set setiduniq` (the source item's own setid, the intuitive choice) instantly created the exact collision the Set exists to prevent, against backlog item `sjsoqq`. Nothing warned. They were regrouped to `setidhard` under spec `4w7d6s`'s own G1 rule before any prose was written. That is the whole defect in one action: the intuitive graduation move produces a violation, silently.
  SO THE ROOT CAUSE IS A CONVENTION, NOT CARELESSNESS, AND THAT IS WHAT MAKES THIS THE HARDEST CHILD. Every one of the 29 live findings is a backlog item sharing its setid with the plan Set it graduated into, and the shared name is currently the ONLY thing that shows a reader at a glance that item `dk16dx` and plan `st5klo` are the same work. Spec G1 replaces that with a FRESH child setid plus typed bidirectional links, which is strictly more machine-readable and strictly less skimmable. That trade is the parent's blocking OQ-02 and is a maintainer call.
  THE PREVENTION HALF HAS A SPECIFIC SHAPE THE SPEC FIXES. I3 names five verb families that must refuse: `aw ipd scaffold`, `aw research new`/`new-comparison`, `aw backlog new`, `aw group`, `aw rename`, "consulting the collision predicate the way id6 minting already prevents id6 reuse". Note `aw group` and `aw rename` are MOVE verbs, so they must refuse moving INTO a taken token, which is a different check from refusing to CREATE one and is the one that would have caught this Set's own regroup had it gone the other way.
  ONE PREVENTION SITE IS ALSO A HAZARD, MEASURED. `aw group plans <id> --set X --rename --apply` WITHOUT `--order` reset the Order to `00` on all four of this Set's plans, including three children, silently producing three Order-0 children in one Set. That is a live defect in a verb this child must edit, so the executor will be working inside it and must not make it worse; it is reported separately and is deliberately NOT this child's fix.
- Scope: Remove the practice that creates cross-type setid collisions (mint a FRESH child setid on graduation, spec G1) and add the gate that would catch it anyway (refuse to create or move into a cross-type-duplicate setid at the five verb families, spec I3). EXCLUDES the sweep of existing collisions (Order 01), the `Graduated-To` link this depends on (Order 02), and fixing `aw group`'s unrelated Order reset.
- Scope-Paths: agent_workflows/ipd_authoring.py, agent_workflows/artifact_rename.py, agent_workflows/backlog.py, agent_workflows/research_cmd.py, agent_workflows/check_engine.py, tests/test_setid_prevention.py, tests/test_ipd_authoring.py
- Item-Dependencies: executed:bwgyum
- Status: to-review
- Set: setidhard
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: dw7i3m
- From-Backlog: sjsoqq

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `sjsoqq` deliverables #2 and #5 (spec `4w7d6s` I3 and G1). Verified at HEAD: `ipd_authoring` consults NO setid-collision predicate (searched), so prevention is genuinely unbuilt, and the contrast with id6 minting (`generate_id6(existing)`, collision-checked at every site) is the model spec I3 explicitly names. THE DEFECT WAS DEMONSTRATED RATHER THAN ASSUMED: scaffolding this Set's four plans with `--set setiduniq`, the intuitive graduation choice, instantly collided with backlog `sjsoqq` and nothing warned; they were regrouped to `setidhard` per G1 before authoring continued. This child carries `Item-Dependencies: executed:bwgyum` because it may only stop minting a shared setid once Order 02's typed forward link exists to carry the relationship the name currently carries; and Order 01's sweep in turn depends on THIS child, so the dependency chain is 02 then 03 then 01 while the Order digits read 01, 02, 03. ALSO RECORDED: `aw group plans ... --rename --apply` without `--order` resets Order to `00` (measured on this Set's own plans), a live defect in a verb this child must edit; it is reported separately and excluded here.

## Goal

Stop creating the collision, so the sweep is a one-time cleanup rather than a recurring chore, and make the identity rule enforceable at the moment an artifact is named.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared predicate, consulted everywhere

- [ ] E-01 EXTRACT ONE SETID-AVAILABILITY PREDICATE AND DO NOT WRITE A SECOND DETECTOR. The judgement "is this setid already owned by another type" already exists inside `check_collisions`, which builds a per-setid map of `(type, descriptive, path)` as it walks every supported type. What does not exist is a callable a MINT site can ask before writing.
  MODEL IT ON THE id6 PRECEDENT, which spec I3 names explicitly: `generate_id6(existing)` takes the set of taken values and the caller supplies it, keeping the generator pure and testable. Do the same here: a function that returns the taken setid map (or answers a single availability question against it), with no filesystem access hidden inside the mint path's hot loop.
  IT MUST SEE TERMINAL ARTIFACTS. A setid belonging to eight `executed` plans is still taken; the `agentadhere` case is exactly that shape. If the inventory helper you build on defaults to excluding retired paths, override it explicitly with a comment saying why, because that default is correct for most rules and wrong for identity. This is the same trap the id6 twin hit, where `aw check all` reported zero collisions while `aw doctor` reported one purely because `executed/` counts as retired.
  DISTINGUISH CROSS-TYPE FROM WITHIN-TYPE, which is the spec's own OQ-02 and the thing a blunt implementation gets wrong. `setidhard` appearing on four PLANS at different Orders is legitimate clustering and must remain legal; `setidhard` appearing on a plan AND a backlog item is the violation. The existing checker already makes this distinction (it compares `prev_type != record_type` for the cross-type case and only then compares descriptives within a type), so follow it rather than inventing a rule.
  - Depends on: none
  - Expected outcome: one shared availability predicate seeing every type including terminal artifacts, distinguishing cross-type from within-type, with no second detector written.
  - Execution state: pending

### Task group 2: refuse at creation and at move

- [ ] E-02 REFUSE TO CREATE INTO A TAKEN SETID at the creation verbs: `aw ipd scaffold`, `aw backlog new`, `aw research new` and `new-comparison`. This is the half that would have stopped this Set's own violation.
  THE MESSAGE MUST NAME THE OWNER AND THE RECOVERY, not merely refuse. The spec's I4 already prescribes the shape for the setter case: the specific setid-collision message plus the `aw group ... --set <new>` recovery, never a generic error. A refusal that says only "taken" leaves an agent guessing, and an agent that guesses will retry with a near-identical token.
  DO NOT BLOCK LEGITIMATE CLUSTERING. Adding Order 04 to an existing plan Set uses that Set's own setid and MUST still work. Test that explicitly, because a naive "is this setid in use" check forbids it and would make multi-child Sets impossible to author.
  - Depends on: E-01
  - Expected outcome: each creation verb refuses a cross-type-taken setid with a message naming the owning artifact and the `aw group` recovery; adding a further Order to an existing Set still succeeds.
  - Execution state: pending

- [ ] E-03 REFUSE TO MOVE INTO A TAKEN SETID at `aw group` and `aw rename`. This is a DIFFERENT check from E-02 and is easy to omit: it validates the DESTINATION token rather than a freshly minted one.
  THE MOVE CASE IS THE ONE THIS SET EXERCISED. The regroup that fixed this Set's own violation moved four plans into `setidhard`; had that token belonged to another type, nothing would have refused, and the fix would itself have been a violation.
  BEWARE THE SELF-COLLISION FALSE POSITIVE. When `aw group` moves an artifact into a setid, the artifact's OWN current setid may be the one being vacated, and a naive check that runs after a partial write could see the mover as its own conflict. Establish the ordering and test the idempotent case (regrouping into the setid it already has must be a no-op, not a refusal).
  DO NOT CHANGE `aw group`'s ORDER BEHAVIOR while you are inside it. The measured Order-reset defect (F-8) is a real bug in this verb, but fixing it here would widen this child's blast radius into a surface with its own tests. Leave it, and do not make it worse.
  - Depends on: E-02
  - Expected outcome: both move verbs refuse a cross-type-taken destination with the same message shape; regrouping into an artifact's existing setid remains a no-op; `aw group`'s Order behavior is untouched.
  - Execution state: pending

### Task group 3: mint fresh on graduation

- [ ] E-04 MAKE GRADUATION MINT A FRESH CHILD SETID RATHER THAN REUSING THE SOURCE'S (spec G1), and make the recommended token DISCOVERABLE so the convention is followed rather than fought.
  THIS IS A CONVENTION CHANGE, NOT ONLY A CODE CHANGE, and it is the reason the parent carries a blocking OQ. Today's practice is intuitive and universal: 21 of 21 measured graduations reused the source setid. So a refusal alone will simply be worked around unless the tool SUGGESTS a good fresh token at the moment of refusal.
  DERIVE A DISTINCT-BUT-RECOGNIZABLE SUGGESTION, per spec OQ-03: only the setid TOKEN must differ, and the slug may still echo the source, so a human still recognizes the pair. Suggest, do not impose: if the derived candidate is ALSO taken, the message must say so rather than looping.
  THE RELATIONSHIP MUST BE CARRIED BY THE LINK, WHICH IS WHY THIS DEPENDS ON ORDER 02. Do not land the fresh-setid mint if `Graduated-To` does not exist: that would remove the only readable source-to-plan pointer and leave nothing in its place, making the tree strictly worse. Verify Order 02 executed before performing this item.
  RECORD WHAT IS LOST. The at-a-glance name match is a real affordance the maintainer uses. State in the docs (E-05) that lineage now reads from `From-Backlog` and `Graduated-To`, and name the commands that follow each direction, or the change trades a visible affordance for an invisible one.
  - Depends on: E-03
  - Expected outcome: graduation mints a fresh child setid, the refusal suggests a distinct-but-recognizable available token, the mint refuses to proceed if `Graduated-To` is absent from the tree, and the lost affordance is named.
  - Execution state: pending

- [ ] E-05 DOCUMENT THE NEW CONVENTION WHERE AN AGENT WILL ACTUALLY READ IT, because a convention nobody reads is a convention that gets violated and then swept again.
  THE TWO PLACES THAT MATTER: `.aw/records/backlog/README.md`'s "Promotion to a plan" section, which currently tells an author to "author an IPD ... then `aw backlog set <item> --status done`" and says nothing about setids or forward links; and the `- Field:` grammar block in the same README, which must list `Graduated-To`. Order 02 also touches this README for the field; coordinate rather than conflict, and if Order 02 already added the field, add only the setid rule here.
  SAY BOTH DIRECTIONS EXPLICITLY: a graduated plan Set gets a FRESH setid; the child carries `From-Backlog: <id6>`; the source carries `Graduated-To: <setid>`; and here is how to follow each. That is what replaces the shared name.
  DO NOT EDIT THE AGENTS.md MANAGED BLOCK. It is installed from `engine.py` into managed repos and hand-editing it is how a managed block drifts from its source. If the graduation contract there needs updating, that is a change to `engine.py`'s installed text and a separate decision; RECORD it as a finding.
  - Depends on: E-04
  - Expected outcome: the README documents the fresh-setid rule and both link directions with the commands to follow them; no managed block hand-edited; any needed managed-block change recorded as a finding.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 TEST EVERY REFUSAL AND EVERY PERMITTED CASE FROM FIXTURES, and prove the tree did not move.
  SEVEN CASES MINIMUM: creating into a cross-type-taken setid REFUSES with the owner named; creating into a free setid succeeds; adding a further Order to an EXISTING Set succeeds (the clustering case a naive check breaks); moving into a cross-type-taken setid REFUSES; moving into an artifact's OWN existing setid is a no-op; graduation mints a FRESH setid; graduation REFUSES if `Graduated-To` is absent.
  ASSERT THE CLUSTERING CASE AND THE SELF-MOVE CASE SEPARATELY, since those are the two false positives that would make the gate unusable and they are the ones a passing "refuses correctly" suite hides.
  BUILD FIXTURES, NOT LIVE-TREE TESTS. Order 01's sweep and four concurrent agents are changing the records trees; a test asserting that `specvis` is taken would fail for unrelated reasons.
  PROVE NO NEW FINDINGS AND NO REGRESSION. `aw check all --agent` per-rule counts before and after: `check.setid-collision` must not RISE (Order 01 is what drives it to zero; this child must not add to it), and no other rule's count may change. `aw check all` reports 98 findings at HEAD, so compare per RULE and never by total.
  RUN THE SUITE BARE and judge on the DELTA. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY. Watch `tests/test_ipd_authoring.py` and the scaffold tests specifically, since this child adds a refusal to a verb every other test uses to build fixtures: a new gate in `scaffold` can break unrelated suites that scaffold into a convenient token.
  - Depends on: E-05
  - Expected outcome: all seven cases asserted from fixtures with the two false-positive cases standing alone; no rule's count risen; bare-suite delta empty with the scaffold-dependent suites explicitly checked.
  - Execution state: pending

## Project conventions discovered (Step 0)

- PREVENTION IS GENUINELY UNBUILT: `ipd_authoring` consults no setid-collision predicate (searched, zero hits).
- THE id6 PRECEDENT IS THE MODEL AND THE SPEC SAYS SO: `generate_id6(existing)` is collision-checked with the caller supplying the taken set, keeping the generator pure. I3 asks for the same shape for setids.
- THE JUDGEMENT ALREADY EXISTS INSIDE `check_collisions`: it builds a per-setid `(type, descriptive, path)` map and compares `prev_type != record_type` for the cross-type case. Reuse that notion; do not write a second detector.
- WITHIN-TYPE REUSE IS LEGITIMATE CLUSTERING. Four plans sharing `setidhard` at different Orders is correct and must stay legal; the spec's OQ-02 exists to confirm the predicate distinguishes it.
- IDENTITY MUST SEE TERMINAL ARTIFACTS. A setid on eight `executed` plans is taken. The id6 twin was measurably blind here: `aw check all` reported zero id6 collisions while `aw doctor` reported one, purely because `executed/` counts as retired.
- `aw group ... --rename --apply` WITHOUT `--order` RESETS Order TO `00`. Measured on this Set's own four plans, producing three Order-0 children. A live defect in a verb this child edits; do not fix it here, do not worsen it.
- SCAFFOLD IS USED BY OTHER TEST SUITES to build fixtures, so a new refusal there can break unrelated tests.
- THE MANAGED AGENTS.md BLOCK IS INSTALLED FROM `engine.py`; never hand-edit it.
- `aw check all` IS NOT GREEN (98 findings). Compare per RULE.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | prevention is unbuilt | `ipd_authoring` consults no setid-collision predicate, so `aw ipd scaffold --set <taken>` mints a violation silently. Contrast id6, checked at every mint site. | grep over `ipd_authoring.py`; `artifact_core.generate_id6` |
| F-2 | HIGH | the defect was demonstrated, not theorized | Scaffolding this Set with `--set setiduniq` (the source's own setid, the intuitive choice) instantly collided with backlog `sjsoqq`. Nothing warned. Regrouped to `setidhard` per G1. | measured at authoring |
| F-3 | HIGH | the root cause is a universal convention | 21 of 21 measured graduations reused the source setid, and the shared name is currently the only at-a-glance link. So a refusal alone will be worked around unless the tool suggests a good token. | the 29-finding inventory |
| F-4 | HIGH | this must not land before Order 02 | Removing the shared setid without `Graduated-To` in place deletes the only readable source-to-plan pointer, making the tree worse. Hence the dependency edge. | spec G1/G3; Order 02's scope |
| F-5 | HIGH | move is a separate check from create | `aw group`/`aw rename` validate a DESTINATION token, not a minted one. This Set's own fix used the move path, which nothing guards. | spec I3; the regroup performed at authoring |
| F-6 | MEDIUM | two false positives would make the gate unusable | Adding an Order to an existing Set (legitimate clustering) and regrouping into an artifact's own setid (idempotent no-op) must both remain permitted; a naive check forbids both. | spec OQ-02; `check_collisions`'s own type comparison |
| F-7 | MEDIUM | identity must include terminal artifacts | `agentadhere` is taken by eight `executed` plans. The id6 twin was blind to exactly this, disagreeing between `aw check all` and `aw doctor`. | `grep 'Set: agentadhere'`; the id6 retired-filter measurement |
| F-8 | MEDIUM | a live defect sits in a verb this child edits | `aw group plans ... --set X --rename --apply` with no `--order` reset all four of this Set's plans to Order `00`, including three children. Reported separately; excluded here. | measured at authoring |
| F-9 | MEDIUM | a new scaffold refusal can break unrelated suites | Other test modules use `aw ipd scaffold` to build fixtures and may scaffold into a convenient token. | the scaffold-dependent test modules |
| F-10 | LOW | the recovery message shape is already specified | Spec I4 requires the specific setid-collision message plus the `aw group ... --set <new>` recovery, never a generic error. | spec I4 |

## Proposed changes (ordered, validatable)

1. Extract one setid-availability predicate seeing every type including terminal artifacts, distinguishing cross-type from within-type (E-01).
2. Refuse creation into a taken setid at the four creation verbs, naming the owner and the recovery (E-02).
3. Refuse moving into a taken setid at `aw group` and `aw rename`, preserving the idempotent self-move (E-03).
4. Mint a fresh child setid on graduation, suggesting a recognizable available token, refusing if `Graduated-To` is absent (E-04).
5. Document the new convention and both link directions where an author reads them (E-05).
6. Assert seven cases from fixtures, with the two false-positive cases standing alone, and prove no regression (E-06).

## Deferred / out of scope (with reason)

- SWEEPING THE 21 EXISTING COLLISIONS. Order 01 (`drzbs9`), which depends on this child so the sweep is not immediately undone.
- BUILDING `Graduated-To` AND ITS CHECK. Order 02 (`bwgyum`), which this child depends on: the fresh-setid mint must not land without the link that replaces the shared name.
- HARDENING THE ENFORCEMENT POSTURE. Order 00 verifies the posture as a whole-Set criterion, and the spec forbids hardening before the sweep.
- FIXING `aw group`'s ORDER RESET (F-8). A real defect in a verb this child edits, but a different surface with its own tests; widening scope into it would put an unrelated behavior change inside a gate plan. Reported to the maintainer.
- DELIVERABLE #3 (setter type-scoped resolution). Landed in `9107790`; spec I4's within-tree resolution is already satisfied and Order 00 checks it as a regression.
- EDITING THE MANAGED AGENTS.md BLOCK. Installed from `engine.py`; a change there is a separate decision. E-05 records it as a finding if needed.
- MAKING `Graduated-To` MANDATORY. Order 02 deliberately left the flag optional so concurrent graduations keep working. This child may require it on the GRADUATION path specifically (that is E-04's point) but must not make the field mandatory everywhere.
- THE id6 COLLISION FAMILY. Already hard and out of scope in the spec; `sk7ggr` (`id6integ-01`) is in flight on it and this child must not touch it.

## Scope check

- Over-scope: none. One predicate, refusals at five verb families, one mint-site change, documentation, and tests.
- Scope-Paths justification: `agent_workflows/ipd_authoring.py` holds `aw ipd scaffold`'s mint path and is where E-02's plan-side refusal and E-04's fresh-setid mint belong; `agent_workflows/artifact_rename.py` holds the shared rename/group machinery (`compute_target_name`, the `--to-id6` mint) that E-03's move refusal must gate; `agent_workflows/backlog.py` holds `aw backlog new` (E-02) and the graduation setter E-04 hooks; `agent_workflows/research_cmd.py` holds `research new`/`new-comparison`, two of the five verb families I3 names; `agent_workflows/check_engine.py` holds `check_collisions`, whose per-setid map is the notion E-01 must extract rather than duplicate; `tests/test_setid_prevention.py` is new and carries the seven fixture cases; `tests/test_ipd_authoring.py` is the existing scaffold suite that F-9 says a new refusal can break. NOTE `.aw/records/backlog/README.md` is deliberately NOT declared here even though E-05 edits it: Order 02 already declares it for the field documentation, and two children declaring the same records file would collide at the finalize scope gate. If Order 02 has not yet added the field, E-05 must coordinate rather than declare the file late; record that as a finding.
- Under-scope, stated rather than left as `none`: this child does not sweep existing collisions, does not build `Graduated-To`, does not harden the posture, does not fix `aw group`'s Order reset, does not touch the setter type-scoping, does not edit the managed block, and does not touch the id6 family. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- SEVEN FIXTURE CASES (E-06), with the CLUSTERING case (adding an Order to an existing Set) and the SELF-MOVE case (regrouping into the same setid) asserted SEPARATELY and their assertions quoted, since they are the false positives that would make the gate unusable.
- `tests/test_ipd_authoring.py` and every other scaffold-dependent suite re-run with their OWN summary lines pasted, per F-9.
- `aw check all --agent` PER-RULE counts before and after: `check.setid-collision` must not RISE, and no other rule's count may change. Never compare totals (98 at HEAD).
- THE REFUSAL MESSAGES pasted verbatim for a creation refusal and a move refusal, showing each names the OWNING artifact and the `aw group ... --set <new>` recovery, per spec I4.
- THE FRESH-MINT SUGGESTION pasted, showing a distinct-but-recognizable token, plus the behavior when that candidate is ALSO taken.
- A DEMONSTRATION that graduation REFUSES when `Graduated-To` is absent from the tree, proving the Order 02 dependency is enforced in code and not only declared.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`.aw/records/backlog/README.md` must document the fresh-setid rule and both link directions (E-05), because this child changes the convention every future graduation follows and the README's "Promotion to a plan" section is where an author looks. It is NOT declared in this plan's `Scope-Paths` deliberately: Order 02 declares it for the `Graduated-To` field, and two children declaring the same records file would collide at the finalize scope gate. Coordinate with Order 02's edit; if that edit has not landed, record a finding rather than declaring the file late.

The MANAGED AGENTS.md BLOCK describes the graduation contract to every agent and is installed from `engine.py`. If it needs to state the fresh-setid rule, that is a change to `engine.py`'s installed text plus a re-install, which is a separate decision with its own blast radius across managed repos. RECORD it as a finding; do not hand-edit the block, which is how a managed block silently drifts from its source.

Spec `4w7d6s` is the authority for I3 and G1 and is `- Status: draft`. This plan IMPLEMENTS it and does not amend it, so the spec file is not declared. Order 00's E-02 holds the approval gate. If the maintainer's answer to the parent's OQ-02 NARROWS I1 (for example exempting a backlog-to-plan pair joined by a resolvable `From-Backlog`), then E-04's fresh-setid mint is no longer wanted and this child must be re-authored rather than partially executed.

Write no em or en dashes in user-facing prose, including the refusal messages, which are operator-facing.

## Open questions

### OQ-01: Should the fresh-setid mint be enforced, or only suggested?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ENFORCED ON THE GRADUATION PATH, SUGGESTED EVERYWHERE ELSE. The evidence is that suggestion alone does not change behavior here: 21 of 21 measured graduations reused the source setid, and the practice is intuitive enough that this Set's own authoring did it too, unprompted, minutes after reading the spec that forbids it. So a soft nudge would leave the sweep to be repeated. But enforcement must be narrow: a refusal at graduation is a refusal at one deliberate act with an obvious remedy, whereas refusing every reuse anywhere would forbid legitimate within-type clustering (F-6). E-02 and E-03 therefore refuse only CROSS-TYPE takes, and E-04's mint refuses only on the graduation path.

### OQ-02: What happens when the derived fresh setid is also taken?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SAY SO AND STOP; DO NOT LOOP OR APPEND A COUNTER. The tempting implementations are a retry loop or a numeric suffix, and both are wrong for the same reason: a setid is a human-skimmable token whose whole value is that it means something, so `specvis2` is a worse outcome than asking the author to choose. E-04 therefore requires the message to state that the derived candidate is also taken and to name its owner, leaving the choice to the author. This mirrors how the id6 mint differs deliberately: an id6 is opaque and machine-generated, so looping is correct there and wrong here.

### OQ-03: Should the move refusal apply when the destination setid is taken by the SAME type?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, AND THIS IS THE FALSE POSITIVE THAT WOULD BREAK THE TOOL. Moving a plan into a setid that other PLANS already carry is exactly how a multi-child Set is assembled, and it is how this Set's own four plans were regrouped into `setidhard`. The invariant being enforced is I1, CROSS-TYPE uniqueness; within-type sharing with a consistent descriptive is legitimate clustering and is already checked separately by the existing rule. E-03 must therefore gate on the cross-type case only, and E-06 asserts the within-type move still succeeds as its own standalone case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate and confirm by inspection that it reuses `check_collisions`'s cross-type notion rather than implementing a second detector (show the searches proving no duplicate scan was added). Paste evidence it sees TERMINAL artifacts, for example that `agentadhere` (taken by eight `executed` plans) is reported taken. Paste evidence it distinguishes within-type clustering, for example that `setidhard` is NOT reported as a cross-type conflict against its own four plans.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the ACTUAL refusal output for each creation verb attempting a cross-type-taken setid, showing the owning artifact and the `aw group ... --set <new>` recovery in the message text. Paste the unpiped exit codes. THEN paste the permitted case: creating into a free setid, and adding a further Order to an EXISTING Set, both succeeding.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ACTUAL refusal for `aw group` and for `aw rename` moving into a cross-type-taken destination, with exit codes. Paste the IDEMPOTENT case: regrouping an artifact into the setid it already carries, showing a no-op rather than a refusal. Paste NEGATIVE proof that `aw group`'s Order behavior was not changed (its Order handling before and after, and confirmation the F-8 defect was neither fixed nor worsened).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a graduation showing a FRESH child setid minted and the suggestion text offering a distinct-but-recognizable token. Paste the also-taken case showing it names the owner and stops rather than appending a counter (OQ-02). Paste the ACTUAL refusal when `Graduated-To` is absent from the tree, proving the Order 02 dependency is enforced in code, and confirm in one sentence that Order 02 was `executed` before this item ran.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the README text as written, showing the fresh-setid rule and BOTH link directions with the commands that follow each. Confirm in one sentence whether Order 02 had already added the `Graduated-To` field entry, and how you coordinated rather than conflicting. Paste proof no managed block was edited (`git diff` over `AGENTS.md` showing no change inside the `aw:block` markers), plus any managed-block finding you recorded.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the ACTUAL passing output of all seven fixture cases, QUOTING the clustering assertion and the self-move assertion separately so it is visible they assert permission rather than refusal. Paste `tests/test_ipd_authoring.py`'s own summary line and that of every other scaffold-dependent suite (F-9). Paste `aw check all --agent` PER-RULE counts before and after, showing `check.setid-collision` did not rise and no other rule changed. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS CHILD IS THE ROOT-CAUSE FIX AND MUST RUN AFTER ORDER 02, DESPITE ITS HIGHER ORDER DIGIT BEING MISLEADING IN THE OTHER DIRECTION. It carries `- Item-Dependencies: executed:bwgyum` because removing the shared setid before the typed forward link exists would delete the only readable source-to-plan pointer. Order 01's sweep then depends on THIS child, so the dependency chain is 02, 03, 01 while the digits read 01, 02, 03. The runner sorts by dependency depth first and handles this; a human must read the edges.

IT INHERITS ORDER 00's TWO BLOCKING QUESTIONS, and for this child the second one is decisive rather than procedural. Order 00's OQ-02 asks whether hard cross-type uniqueness is the right answer at all, given that all 29 live findings are the repository's own working convention and the shared name is a real affordance the maintainer uses. If the answer is that the affordance matters more and I1 should be NARROWED instead, then E-04's fresh-setid mint is unwanted and this child must be re-authored, not partially executed. Do not begin task group 3 on a guess.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME rather than by the line numbers cited here. Do NOT fix or worsen `aw group`'s Order reset (F-8). Do NOT hand-edit the managed AGENTS.md block. Do NOT declare `.aw/records/backlog/README.md` in this plan's Scope-Paths; coordinate with Order 02, which declares it. Build tests from FIXTURES, never from live records. Paste ACTUAL command output including refusal text and unpiped exit codes, and compare `aw check` findings PER RULE, never by total. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the two standalone false-positive assertions and the demonstration that graduation refuses without `Graduated-To`.
