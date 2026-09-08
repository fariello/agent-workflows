# IPD: Show what a source already graduated to before authoring another plan for it and then make the graduation path reachable

- Date: 2026-09-08
- Kind: orchestrator
- Concern: Nothing tells whoever is about to graduate a spec or backlog item that the source ALREADY has plans, so the expensive failure the maintainer named ("We don't want multiple IPDs for the same things, especially if already implemented") has no guard at all. VERIFIED AT HEAD `a2e0438a`: `check_engine` has `check.from-backlog-dangling` and `check.from-spec-dangling`, which validate that a plan's source id6 RESOLVES to a real artifact. Neither asks the reverse question, and grepping the rule table for a duplicate or already-implemented check returns nothing.
  THE RAW MATERIAL EXISTS AND HAS GROWN, WHICH MAKES THIS TRACTABLE. Measured across the whole plans tree: 125 plans carry a source link (the item recorded 71), spanning 72 distinct sources, of which 17 have MORE THAN ONE plan. The largest clusters are `From-Spec: 25kzda` x9 (8 executed, 1 not-executed), `From-Backlog: kjzlgw` x8 (all executed), `From-Spec: 7ckptx` x7 (4 executed, 3 approved), and `From-Spec: kw5y2s` x6 (all executed). So a would-be tenth plan for `25kzda` faces 8 executed siblings and nothing says so.
  THE HARD PART IS THAT MULTIPLE PLANS PER SOURCE ARE NORMAL AND CORRECT, which is why a naive uniqueness rule would be worse than nothing. A spec is deliberately decomposed into an ordered Set of children, and spec `25kzda`'s own graduation text says a run "may produce more than one IPD". The `25kzda` cluster of nine is right, not a defect.
  HALF 1 OF THE ITEM IS PARTLY OBSOLETE AND THE REMAINDER IS SMALLER THAN IT SAYS. The item states `--action plan` "parses and its entire legal domain is unreachable" and that "NO selector reaches a spec or a backlog item however it is spelled". Both were true when filed and neither is fully true now. `--action plan` no longer silently accepts-and-misroutes: it FAILS CLOSED with a named refusal (`ACTION_IMPLEMENTED` is `frozenset({'review'})`, and `enforce_requested_action('plan', ...)` raises "`--action plan` is not implemented yet ... No run was started"), which landed in `a3bb14bf` on 2026-09-05, the day BEFORE the item was written. And `runner_shared.discover_specs` now EXISTS and finds 9 specs including `25kzda`, shipped by executed plan `5slbpi` E-05 ("Let needs-review discovery reach the SPECS tree"). What remains is that spec discovery is wired only into the REVIEW sweep, not into selector expansion or the queue builder, so a spec still cannot be the subject of a `plan` action.
- Scope: The two children this needs, in the order the item requires. IN: (a) the PRE-GRADUATION VIEW, read-only and advisory, reporting every existing plan for a source with its status and Set so whoever graduates sees the cluster before authoring, plus the honest statement of which of the three cases it can and cannot detect; (b) making a spec or backlog selector REACHABLE for the plan action, building on the spec discovery that now exists rather than adding a second enumeration. OUT: per-requirement spec tracking (backlog `f1sw71`, which the item names as the blocker for the "already implemented" case); any semantic already-implemented verdict; any change to the two existing dangling checks.
- Scope-Paths: .aw/records/plans/pending/20260908-graduate-01-jxxec8-report-every-existing-plan-for-a-source-before-a-tenth-is-au.ipd.md, .aw/records/plans/pending/20260908-graduate-02-iuxtjy-make-a-spec-or-backlog-selector-reachable-for-the-plan-actio.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: graduate
- Order: 0
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: y9s4vm
- From-Backlog: 6h7y2y

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `6h7y2y`, PARTIALLY: Half 2 (the guard) is graduated whole, and Half 1 (the verb) is graduated NARROWED because two of its three premises have been overtaken by shipped work. The item carries no `- Blocks-Release:` so none is inherited or invented.
  THE OBSOLESCENCE, MEASURED RATHER THAN INFERRED, AND IT IS THE REASON THIS SET IS TWO CHILDREN RATHER THAN A LARGER ONE. FIRST, the item's headline reproduction (`aw oc run start --action plan 25kzda` misrouting into a "not an IPD plan" error) no longer describes the failure: `--action plan` now FAILS CLOSED with a named not-implemented refusal that starts no run, which landed at `a3bb14bf` on 2026-09-05, ONE DAY BEFORE the item was filed on 2026-09-06. So the operator-facing hazard the item leads with is already gone; what survives is the capability gap. SECOND, the item says "NO selector reaches a spec or a backlog item however it is spelled" and cites `discover_plans` walking only the plans trees. That is now FALSE for specs: `runner_shared.discover_specs` exists, is documented as "the SPEC sibling of `discover_plans`", reads identity and status through the shared authorities with no new path literal, and measurably finds 9 specs including `25kzda`. Executed plan `5slbpi` E-05 shipped it. THIRD, and this is the surviving gap child 02 owns: `discover_specs` is consumed only by the REVIEW sweep, so a spec still cannot be the subject of a `plan` action.
  I ALSO CHECKED WHETHER THE ITEM'S OWN SOURCE SPEC WAS ALREADY GRADUATED, since that is exactly the duplication this Set exists to prevent, and it partly was: spec `6m4kow` (which the item cites as having independently recorded the same measurement) has THREE executed plans carrying `From-Spec: 6m4kow` (`eyh1fu`, `5slbpi`, `wpomxa`). That is the clearest possible argument for child 01: had the pre-graduation view existed, whoever filed this item would have seen those three and scoped it differently from the start. Recorded as F-3 and as this Set's own motivating case.
  THE ITEM'S SEQUENCING INSTRUCTION IS HONORED AND IS NOT NEGOTIABLE HERE: "build the guard BEFORE or WITH the verb, not after. A working `--action plan` with no duplicate check is a machine for generating redundant plans faster than a human can." Hence child 01 is Order 01 and child 02 declares `executed:jxxec8`.

## Goal

Make the cluster of plans a source already has visible before anyone authors another, and only then let a spec or backlog item be the subject of a plan action.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: drive the two children in the required order

- [ ] E-01 CONFIRM CHILD 01 (`jxxec8`) IS EXECUTED before child 02 runs, and confirm it BY READING THE CHILD'S STATUS ON DISK rather than trusting this table. The order is the item's own instruction and its stated reason is that the verb without the guard is "a machine for generating redundant plans faster than a human can".
  - Depends on: none
  - Expected outcome: `jxxec8` reads `- Status: executed` and sits in `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM CHILD 02 (`iuxtjy`) IS EXECUTED, and confirm that it consumed the EXISTING `discover_specs` rather than adding a second spec enumeration. That is the specific way this Set could do damage: a parallel enumeration would make the review sweep and the plan action disagree about which specs exist.
  - Depends on: E-01
  - Expected outcome: `iuxtjy` reads `- Status: executed`; a grep shows exactly one spec-enumeration function in `runner_shared`; the review sweep and the plan action resolve the same spec set.
  - Execution state: pending

- [ ] E-03 CONFIRM BACKLOG `6h7y2y` WAS CLOSED BY CHILD 02, not by this parent, and that no `Blocks-Release` gate was invented for it. The item carries none.
  - Depends on: E-02
  - Expected outcome: backlog `6h7y2y` reads `- Status: done`, closed by `iuxtjy` which carries `- From-Backlog: 6h7y2y`; no plan in this Set carries a `- Blocks-Release:` field; `aw backlog check` clean.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

BOTH children are AUTHORED and `aw ipd lint` conforming, each `to-review`. There are NO placeholder rows: an orchestrator whose table declares a row resolving to no plan refuses retirement (`unauthored-child-rows`).

| Order | Id | What it does | Depends on |
|---|---|---|---|
| 01 | `jxxec8` | THE GUARD, and the item's "minimum useful version": a read-only advisory view reporting every existing plan carrying a source id6, with its status and Set, so whoever graduates sees "25kzda already has 9 plans, 8 executed" before authoring a tenth. Also states honestly which of the item's three cases it can and cannot detect, and does NOT attempt the already-implemented verdict, which is blocked on `f1sw71`. FIRST, because the item requires the guard before the verb. | none |
| 02 | `iuxtjy` | THE VERB, NARROWED: make a spec or backlog selector reachable for the `plan` action by CONSUMING the `discover_specs` that executed plan `5slbpi` already shipped, and wire the pre-graduation view from child 01 into that path so the guard fires where it matters. Does NOT re-fix the `--action plan` refusal, which already fails closed. CLOSES backlog `6h7y2y`. | `executed:jxxec8` |

Hard constraints both children inherit, stated once here:

- MULTIPLE PLANS PER SOURCE ARE LEGITIMATE. A spec decomposes into an ordered Set of children with distinct Orders and non-overlapping scope, and spec `25kzda`'s graduation text says a run "may produce more than one IPD". Measured, 17 of 72 sources have more than one plan and the largest cluster (nine) is correct. NO CHILD MAY IMPLEMENT A `count > 1` UNIQUENESS RULE; that would flag correct work and teach people to ignore the warning.
- THE GUARD IS ADVISORY AND READ-ONLY. The item's minimum version "does not need to decide, only to show". A child that REFUSES a graduation on a heuristic would block legitimate decomposition, and there is no mechanical way to distinguish the three cases today (see the next constraint).
- THE ALREADY-IMPLEMENTED CASE CANNOT BE ANSWERED MECHANICALLY AND NO CHILD MAY PRETEND OTHERWISE. There is no per-requirement tracking: a spec carries ONE whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog `f1sw71` tracks that gap. Each child must say plainly which cases it detects and which it cannot.
- NO SECOND SPEC ENUMERATION. `runner_shared.discover_specs` exists and is documented as the spec sibling of `discover_plans`, reading identity and status through the shared authorities with NO new path literal (asserted by an AST test that rejects a new `"records/specs"` literal in that module). A parallel enumeration would make the review sweep and the plan action disagree.
- DO NOT WEAKEN THE TWO EXISTING DANGLING CHECKS. `check.from-backlog-dangling` and `check.from-spec-dangling` validate the forward direction and are `error` severity. This Set adds a reverse-direction VIEW; it does not touch them.
- NO CHILD ADDS A `Blocks-Release` GATE. The item carries none.
- CHILDREN ARE SEQUENTIAL because the item requires the guard first, NOT because of file overlap. The runner isolates each item in its own worktree, so overlap with other pending Sets is not a runtime hazard and must not be reported to a human as one.

## Completion criteria (the whole Set is done only when)

- Whoever is about to graduate a source can see, before authoring, every existing plan for it with each plan's status and Set (child 01).
- The view distinguishes what it CAN detect (existing plans, their statuses, whether any reached a terminal state) from what it CANNOT (whether a requirement is semantically implemented), and says so in its own output rather than only in a plan (child 01).
- NO uniqueness rule was added: a source with nine legitimate children is not reported as a defect (child 01).
- A spec or backlog selector resolves for the `plan` action, through the EXISTING `discover_specs` rather than a second enumeration (child 02).
- The pre-graduation view fires on that path, so the guard is not merely available but reached (child 02).
- The `--action plan` fail-closed refusal was NOT re-implemented and still fails closed for any case child 02 does not implement (child 02).
- Backlog `6h7y2y` is closed by child 02 with its partial obsolescence recorded in the item (child 02).

WHICH V-ITEM OWNS EACH CRITERION, stated because a criterion no `V-*` demands evidence for is an aspiration rather than a gate. THIS PARENT'S V-ITEMS OWN ONLY ORCHESTRATION: that each child reached `executed` in the required order, that no second spec enumeration exists, and that the backlog ledger was discharged by child 02. EVERY SUBSTANTIVE CRITERION is owned by a child's own `V-*`, where the pre-transition E/V checkpoint is enforced. This parent does NOT re-verify any of them; citing a child's pasted evidence is the correct discharge.

## Cross-IPD validation

- CID-1: NO UNIQUENESS RULE. For the largest real cluster (`From-Spec: 25kzda`, nine plans), the view REPORTS the cluster and flags no defect. Demonstrated against the live corpus, not a fixture, since the point is that correct real work is not flagged.
- CID-2: ONE SPEC ENUMERATION. `runner_shared` contains exactly one spec-discovery function after this Set, and the review sweep and the plan action resolve the SAME spec set for the same repository. Asserted by object identity and by comparing the two resolutions, not by grep alone.
- CID-3: HONEST LIMITS IN THE OUTPUT. The view's own output states which of the three cases (legitimate decomposition, accidental duplication, already implemented) it can and cannot detect. A view that silently implies it detected all three is a failed CID-3 even if its data is correct.
- CID-4: THE FORWARD CHECKS ARE UNTOUCHED. `check.from-backlog-dangling` and `check.from-spec-dangling` behave identically before and after, demonstrated by their rule output on the live corpus.
- CID-5: THE FAIL-CLOSED REFUSAL SURVIVES. For every action or type child 02 does not implement, `enforce_requested_action` still refuses and starts no run. A Set that made an unimplemented path silently proceed would be worse than the gap it closed.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN. This parent's three items each CONFIRM a child's terminal state or the ledger. The runner retires an orchestrator once every child is `executed` and deliberately SKIPS the pre-transition E/V checkpoint, so work parked on a parent is marked complete having never been performed.
- `discover_specs` ALREADY EXISTS AND IS CAREFULLY BUILT. It reads identity through `check_engine._ITEM_ID_RE`, status through `selectors.read_front_matter_status`, and enumerates through `check_engine._iter_spec_records` so it adds NO path literal, guarded by an AST test. It SKIPS a spec with no `- Id:` deliberately, because such a spec "cannot be named by a selector, cannot carry a review record ... and cannot be attested". Measured, it finds 9 of 28 specs, and that gap is documented in its own docstring rather than being a bug.
- `--action plan` ALREADY FAILS CLOSED. `ACTION_CHOICES` is `('review', 'plan', 'execute')` while `ACTION_IMPLEMENTED` is `frozenset({'review'})`, and the refusal names the missing per-type dispatch and says "No run was started". Do not re-fix this.
- THE FORWARD DANGLING CHECKS ARE `error` SEVERITY AND ALREADY SHIPPED. The reverse question is genuinely absent, which is what this Set adds.
- SPEC `6m4kow` IS THE DESIGN AUTHORITY FOR THE SPEC-REVIEW SIDE and already has three executed plans, so anything this Set does near spec review must not re-decide what those settled.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `check_engine.py` rule table | The reverse-direction question is genuinely unasked: only `check.from-backlog-dangling` and `check.from-spec-dangling` exist, and both validate the FORWARD direction. No duplicate or already-implemented check exists. | grepped the rule table for duplicate/already-implemented; no hits |
| F-2 | MED | plans tree | 125 plans carry a source link (the item recorded 71) across 72 distinct sources, 17 of which have MORE THAN ONE plan. Largest: `25kzda` x9 (8 executed, 1 not-executed), `kjzlgw` x8 (all executed), `7ckptx` x7 (4 executed, 3 approved), `kw5y2s` x6. | walked the tree parsing `From-Spec`/`From-Backlog` and `- Status:` |
| F-3 | HIGH | executed plans `eyh1fu`, `5slbpi`, `wpomxa` | THIS SET'S OWN MOTIVATING CASE: spec `6m4kow`, which the item cites, ALREADY has three executed plans carrying `From-Spec: 6m4kow`. Had the pre-graduation view existed, the item would have been scoped differently. | grepped `From-Spec: 6m4kow` across the plans tree |
| F-4 | PARTLY OBSOLETE | `oc_runipd.ACTION_IMPLEMENTED`; commit `a3bb14bf` | THE ITEM'S REPRODUCTION NO LONGER DESCRIBES THE FAILURE. `--action plan` now FAILS CLOSED with a named refusal that starts no run. That landed 2026-09-05, ONE DAY BEFORE the item was filed. | `enforce_requested_action('plan', ...)` raises "not implemented yet ... No run was started"; `git log -S ACTION_IMPLEMENTED` |
| F-5 | PARTLY OBSOLETE | `runner_shared.discover_specs`; executed plan `5slbpi` E-05 | THE ITEM'S "NO SELECTOR REACHES A SPEC" CLAIM IS NOW FALSE FOR SPECS. `discover_specs` exists, is the documented spec sibling of `discover_plans`, and measurably finds 9 specs including `25kzda`. | called it: 9 specs, `25kzda` present with `status='approved'` |
| F-6 | MED | `runner_shared.py:1107` | WHAT SURVIVES: `discover_specs` is consumed ONLY by the review sweep. It is not wired into selector expansion or the queue builder, so a spec still cannot be the subject of a `plan` action. That is child 02's whole job. | read its only call site |
| F-7 | CONSTRAINT | spec `25kzda` graduation text; F-2 | MULTIPLE PLANS PER SOURCE ARE CORRECT: a spec decomposes into an ordered Set, and the nine-plan `25kzda` cluster is right. A `count > 1` rule would flag correct work. | spec text plus the measured cluster statuses |
| F-8 | BLOCKER-FOR-ONE-CASE | backlog `f1sw71`; `attention_contract` | THE ALREADY-IMPLEMENTED CASE IS NOT MECHANICALLY ANSWERABLE. A spec carries one whole-artifact status with no partial-implementation state, and `implemented` needs only a resolvable citation, not semantic verification. `f1sw71` (open) tracks it. | the item's own citation, re-verified; `f1sw71` exists and is open |

## Proposed changes (ordered, validatable)

1. Child 01 (`jxxec8`) adds the read-only pre-graduation view, reports the cluster with statuses and Sets, and states its own limits, adding no uniqueness rule and no already-implemented verdict.
2. Child 02 (`iuxtjy`) makes a spec or backlog selector reachable for the `plan` action by consuming the existing `discover_specs`, wires the view into that path, and closes backlog `6h7y2y`.

## Deferred / out of scope (with reason)

- PER-REQUIREMENT SPEC TRACKING and any semantic already-implemented verdict. Backlog `f1sw71` (open), which the item itself names as the blocker: "there is no per-requirement tracking, so 'is requirement G5 built?' cannot be answered mechanically". The item explicitly says this Set "can ship its plan-level guard without waiting for it, and should say honestly which of the three cases above it can and cannot detect".
- RE-FIXING THE `--action plan` REFUSAL. F-4: it already fails closed with a named refusal, landed the day before the item was filed. Re-doing it would be work an existing commit already declares.
- ADDING A SECOND SPEC ENUMERATION. F-5: `discover_specs` exists and is guarded by an AST test against a new path literal. Consume it.
- ANY `count > 1` UNIQUENESS RULE. F-7: it would flag the nine-plan `25kzda` cluster, which is correct decomposition.
- A REFUSING GUARD. The item's minimum version "does not need to decide, only to show", and with the already-implemented case unanswerable (F-8) a refusal would rest on a heuristic.
- CHANGING THE TWO FORWARD DANGLING CHECKS. They work and are `error` severity.
- THE SPEC-REVIEW WORKFLOW AND THE `to-review -> reviewed` ATTESTATION. Spec `6m4kow` and its three executed plans own that; re-deciding it here would collide.

## Scope check

- Over-scope: none. This parent edits no source file; its `Scope-Paths` are the two children it authored.
- Under-scope: stated rather than left as `none`. After this Set the already-implemented case is still undetectable (`f1sw71`), and the guard is ADVISORY, so a determined author can still create a redundant plan; the Set's claim is that they will have been shown the cluster first, not that they are prevented.

## Required tests / validation

Each child carries its own tests. This parent runs none: its three items read child status and the ledger from disk. `python3 -m pytest` bare is each child's obligation, with the baseline measured in the executing worktree and failing NODE IDS compared, never totals. CID-1 and CID-2 are deliberately measured against the LIVE corpus rather than fixtures, because the properties being asserted are that real correct work is not flagged and that two real resolutions agree.

## Spec / documentation sync

Spec `25kzda` (`- Status: approved`) DESCRIBES THE GRADUATION PATH AS SHIPPED BEHAVIOR IT IS NOT, and that is the live discrepancy this Set narrows. Its §1.3 lists "Author an IPD from an approved spec" and "Graduate an open backlog item into an IPD" as dispositions of `aw <host> run`, and §2.1 registers `--action plan` whose legality rules say it is legal "only for an `approved` spec or `open` backlog item". Child 02 moves the code TOWARD that text, so no amendment is expected FROM child 02.
TWO THINGS TO DETERMINE AND REPORT, and this is child 02's obligation rather than this parent's. FIRST, whether §2.1's legality table for `plan` requires MORE than child 02 implements; if child 02 implements a subset, the spec still overstates the shipped behavior and the honest response is to record the remaining gap in the plan, NOT to amend the spec to match a partial implementation. SECOND, whether spec `6m4kow` (`to-review`) constrains the guard's shape, since it is the design authority for the spec-side dispatch and already has three executed plans.
Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Where does the pre-graduation view live: a `check` rule, a `find`/`show` surface, or a step in the graduation path?

- Blocking: no
- Status: open
- Owner: child 01 (`jxxec8`) executor, with the maintainer if a new rule severity is proposed
- Resolution or deferral rationale: NOT blocking this parent, which performs no work; it is child 01's first design decision and is recorded there as that child's own OQ. The considerations, stated so the child does not re-derive them: a `check` RULE runs in CI and on every `aw check`, which would report the 17 multi-plan sources as findings on every run, and with 17 legitimate clusters that is noise unless the severity is `info`. A READ surface (a `find`/`show` flag) is consulted deliberately by whoever graduates, which matches the item's "advisory and read-only; it does not need to decide, only to show", but it only helps if someone remembers to run it, which is why child 02 wires it into the graduation path. Those two are complementary rather than exclusive.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste child `jxxec8`'s `- Status:` line and its path, read at validation time, showing `executed` and `.aw/records/plans/executed/`. Paste its view's ACTUAL output for `From-Spec: 25kzda` showing the nine plans with their statuses and Sets, and paste the sentence in which the view states its own limits, since CID-3 turns on that being in the OUTPUT rather than in a plan.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste child `iuxtjy`'s `- Status:` line and path showing `executed`. Paste a grep showing exactly ONE spec-enumeration function in `runner_shared`, and paste the two resolutions (review sweep and plan action) for the same repository showing they return the SAME spec set. Paste an `--action plan` invocation for a case child 02 did NOT implement, showing it still FAILS CLOSED and started no run.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste backlog `6h7y2y`'s `- Status:` line showing `done`, and name WHICH child closed it, confirming this parent closed none. Paste `aw backlog check` clean. Paste a grep over all three plans in this Set showing NO `- Blocks-Release:` field was added. Paste the item's recorded partial-obsolescence note, confirming F-4 and F-5 were written into the item rather than only into these plans.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: this parent commits nothing and edits no source file. Each child commits ONLY the files it changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved y9s4vm --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. The runner retires this orchestrator automatically once both children read `executed` on disk; if a human executes the Set by hand instead, work the three E-items above in order. THE ORDER IS THE ITEM'S OWN INSTRUCTION AND IS NOT AN IMPLEMENTATION DETAIL: "A working `--action plan` with no duplicate check is a machine for generating redundant plans faster than a human can."
