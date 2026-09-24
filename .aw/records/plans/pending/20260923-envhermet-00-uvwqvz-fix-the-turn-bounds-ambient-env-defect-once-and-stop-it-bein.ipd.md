# IPD: Fix the turn-bounds ambient-env defect once and stop it being filed a twenty-fifth time

- Date: 2026-09-23
- Kind: orchestrator
- Concern: A SINGLE NON-HERMETIC TEST ASSERTION HAS PRODUCED TWENTY-THREE OPEN BACKLOG ITEMS, AND BOTH HALVES OF THAT SENTENCE ARE DEFECTS. The DEFECT half: `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` reads the AMBIENT `OPENCODE_CONFIG_CONTENT`, which `run_opencode` always sets for a turn, so the file is green for a human (`144 passed`) and red for every lane agent (`1 failed, 143 passed`, measured at HEAD `22cf67d9`). The PROCESS half: nothing warns a filer that the item already exists, so agents hitting it kept filing it; `uj5g58` counted 18 and the live count is 23, meaning six arrived after the item that counted them.
  THESE TWO MUST SHIP TOGETHER, WHICH IS THE ONLY REASON THIS SET EXISTS. Fixing only the test leaves the next environment-sensitive defect free to be filed twenty times over; fixing only the guard leaves twenty-three live release blockers describing a real red test. Each child is independently correct and independently reviewable, so the Set is an ordering device and not a bundle.
  THE COST IS CONCENTRATED IN FALSE EVIDENCE, NOT IN UNTIDINESS. An agent following the execution contract measures a baseline and compares failure sets by node id; this failure appears in both measurements and cancels, so the common outcome is a wasted investigation and the dangerous outcome is an agent that either "fixes" a correct test or learns to ignore a red node in a file where a genuine failure may appear next. Precedent for that cost, measured rather than hypothesized: executed plan `ty7w6o` had to spend a stash-and-re-run plus a targeted variable neutralization purely to prove the failure was not its own.
  THE DEFECT HALF IS CONFIRMED AT REVIEW AND IS SHARPER THAN THE PLAN STATES. Re-measured in a lane at HEAD `a16698cc`: `python3 -m pytest tests/test_turn_bounds.py` gives `1 failed, 147 passed`, and `env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE python3 -m pytest tests/test_turn_bounds.py` gives `148 passed`, with no code change between the two. The failing assertion is the `policy_key not in main_env` one, and the ambient value is present here (`{"permission": {"external_directory": "deny", "question": "deny"}}`). NOTE THE COUNTS HAVE DRIFTED from the `144`/`143` this plan records, which is exactly why the children are required to re-derive them rather than assert them.
  THE CENSUS HALF IS SUBSTANTIALLY STALE AND THE CORRECTION MATTERS FOR F-3 AND OQ-01. Re-measured at review: the family is now TWENTY-FIVE filings, of which TWENTY-FOUR are already `graduated` and carry `- Graduated-To: envhermet`, so they are `active` in `aw attention` rather than a wall of `ready` blockers. EXACTLY ONE remains `open`: `wnabns`, and it carries `- Blocks-Release: next` with NO `Graduated-To` and no plan citing it. So the "twenty-three live release blockers" figure is no longer true, and the honest statement is that the bulk of the board noise was already discharged by graduation before this review. See F-3 (corrected) and the NEW F-5, which is the one that has operational consequence.
- Scope: Order and track the two children this needs. IN: child 01 (`heglfv`) makes the turn-bounds policy assertions read the constructed child env rather than the ambient one, preserving the `R4.1` guarantee; child 02 (`fwgq2u`) gives `aw backlog new` an advisory near-duplicate guard following `aw graduation`'s shipped precedent. OUT, and owned by neither child: retroactively consolidating the twenty-three items (a records act needing human judgement about which filing survives, safe only once child 01 has landed); removing `OPENCODE_CONFIG_CONTENT` from `run_opencode`, which carries the turn's configuration; and the `AW_EXECUTION_ROLE` variant some filings describe, which `conftest.py` already scrubs and whose residue `rolevac` `8i0xa7` owns.
- Scope-Paths: .aw/records/plans/pending/20260923-envhermet-01-heglfv-make-the-turn-bounds-policy-assertions-read-the-constructed.ipd.md, .aw/records/plans/pending/20260923-envhermet-02-fwgq2u-give-aw-backlog-new-a-near-duplicate-guard-so-one-defect-can.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: envhermet
- Order: 0
- Highest E allocated: 02
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: uvwqvz
- From-Backlog: uj5g58
- Blocks-Release: next

## Workflow history
- 2026-09-24 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-106, all FIXED, none deferred, none open. Readiness `go-pending-approval`. Record: `.aw/records/reviews/20260923-envhermet-00-uvwqvz-fix-the-turn-bounds-ambient-env-defect-once-and-stop-it-bein.review.md`. `aw ipd lint --phase author` conformed BEFORE semantic review and `--phase review-finalize` conforms after, so nothing found was structural; the `IPD-S407` typed child-tracking row check reports CONFORMING for both rows, so no repair loop was entered. DISCLOSURE: same agent and model authored this plan, so this is a SELF-REVIEW, and its value rests on RUNNING the claims rather than re-reading them.
  THE CORE DEFECT IS CONFIRMED BY DIRECT MEASUREMENT, which is the most important thing a reviewer of this plan can establish. In a lane at HEAD `a16698cc`: `python3 -m pytest tests/test_turn_bounds.py` -> `1 failed, 147 passed`; `env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE python3 -m pytest tests/test_turn_bounds.py` -> `148 passed`, no code change between the two. The failing assertion is `policy_key not in main_env`. So the premise is real and the Set is worth running.
  TWO MEASUREMENTS HAD DRIFTED, AND THE DIRECTION MATTERS. The suite counts moved `144`/`143` to `148`/`147`, and the filing corpus moved 23 to 25, of which TWENTY-FOUR are now already `graduated` carrying `- Graduated-To: envhermet`. That retires F-3 (the "23 live release blockers" claim) to INFO and adds CID-4 requiring both children to re-derive rather than quote, since the plan's own numbers went stale twice within days.
  THE FINDING A HUMAN SHOULD READ IS PR-103. Exactly one member of the family is still `open`: `wnabns`, which carries `- Blocks-Release: next`, has NO `- Graduated-To:`, and is cited by NO plan (child 01 carries `mepbmp` instead). Measured: `evaluate_blocking_close` REFUSES its close because that "would silently drop that release gate". So as authored, this Set fixes the defect `wnabns` describes and then leaves it as a permanent `ready` release blocker that cannot legitimately be closed. Added as completion criterion 6, verified by V-01, resolved in OQ-02 to a HANDOFF, with the mechanical trap named: `--from-backlog` SETS rather than appends, so the fix is to ADD a second bullet, not to overwrite `mepbmp` and strand that gate instead.
  PR-104 IS THE SUBTLER ONE AND IT UNDERCUT THIS PLAN'S OWN F-4. Four deferred rows named no durable carrier, so `aw check` reported `check.ipd-uncarried-obligation` at `error` and this plan would have blocked its own finalize. The sharpest case is the consolidation task F-4 was written to protect: declaring it out of scope does NOT make it survive, because once this plan reaches `executed` it classes `done` in `aw attention` and the obligation vanishes unrecorded. Carrier fields added throughout; re-measured to 0 findings.
- 2026-09-24 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-101..PR-106 all FIXED; readiness go-pending-approval
- 2026-09-24 migrated (orchtyped/68uhp0): checklist migrated to typed child-tracking rows per spec r07vma.

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from the twenty-three-item turn-bounds family plus `uj5g58`. `- Blocks-Release: next` is INHERITED; every member carries it.
  THIS PARENT CARRIES ORCHESTRATION ONLY, DELIBERATELY. Per `AGENTS.md`, a runner RETIRES an orchestrator once every child is `executed` and SKIPS the pre-transition E/V checkpoint, so any work parked here would be marked complete having never been performed. Both E-items below are child-completion checks, and the two substantive deliverables belong to `heglfv` and `fwgq2u`. The one thing that might have been parent-only work, consolidating the twenty-three items, is explicitly declared OUT rather than left implicit, because it needs human judgement and would otherwise be exactly the uncovered-parent-work the coverage gate refuses on.
  ORDER IS MEANINGFUL BUT NOT A HARD DEPENDENCY: child 01 fixes the defect that generated the duplicates and child 02 stops the next one recurring, so 01 first is the useful sequence; neither declares an `- Item-Dependencies:` edge on the other because they touch disjoint files (`tests/test_turn_bounds.py` versus `agent_workflows/backlog.py`) and either can land alone.

## Goal

Land both halves of the turn-bounds duplication problem: the test defect that generated twenty-three filings, and the missing guard that let them all be filed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: children

- [ ] E-01 CONFIRM heglfv REACHED executed
  - Depends on: none
  - Expected outcome: `heglfv` is in `.aw/records/plans/executed/` with every `V-*` carrying observed evidence, including the pasted green run with the variable SET, the demonstration that the fixed test can still fail, and re-derived counts (not this plan's stale `144`/`143`). Also confirm `wnabns`'s gate is preserved per completion criterion 6 and OQ-02.
  - Execution state: pending
  Child 01 fixes turn-bounds policy assertions to read constructed child env.

- [ ] E-02 CONFIRM fwgq2u REACHED executed
  - Depends on: none
  - Expected outcome: `fwgq2u` is in `.aw/records/plans/executed/` with every `V-*` carrying observed evidence, including the measured added latency, the negative-control assertion, and confirmation by inspection that its tests read no live backlog tree (CID-2, whose corpus has already shrunk from 23 open to 1).
  - Execution state: pending
  Child 02 gives aw backlog new an advisory near-duplicate guard.

## Child IPDs, sequence, and dependencies

| Order | Id | Plan | Depends on | Status | Owns |
| --- | --- | --- | --- | --- | --- |
| 01 | `heglfv` | `20260923-envhermet-01-heglfv-make-the-turn-bounds-policy-assertions-read-the-constructed.ipd.md` | none | `to-review` | The DEFECT: make the turn-bounds policy assertions read the constructed child env, not the ambient one, preserving `R4.1`. Touches `tests/test_turn_bounds.py`. |
| 02 | `fwgq2u` | `20260923-envhermet-02-fwgq2u-give-aw-backlog-new-a-near-duplicate-guard-so-one-defect-can.ipd.md` | none | `to-review` | The PROCESS: give `aw backlog new` an advisory near-duplicate guard following `aw graduation`'s precedent. Touches `agent_workflows/backlog.py`. |

SEQUENCE IS USEFUL BUT NOT ENFORCED. Child 01 fixes the defect that generated the twenty-three filings and child 02 stops the next such defect recurring, so 01-then-02 is the informative order. Neither declares an `- Item-Dependencies:` edge on the other, deliberately: they touch DISJOINT files, so either may land alone and both may execute in parallel isolated worktrees without contending.

## Completion criteria (the whole Set is done only when)

1. `tests/test_turn_bounds.py` passes with `OPENCODE_CONFIG_CONTENT` both SET and UNSET, and the `R4.1` assertion is unchanged in strength (child 01). The pass/fail COUNTS are re-derived at execution time, never quoted from this plan: they were `144`/`143` at authoring and `148`/`147` at review, so a criterion pinned to a number would be wrong before it was read.
2. The fixed test is demonstrated still able to FAIL under a deliberate mutation, so the hermeticity fix did not make it vacuous (child 01).
3. `aw backlog new` reports plausible existing items, never refuses, and states its own detection limits in its output (child 02).
4. The guard is proved against fixtures derived from the real filings AND shown not to flag a genuinely distinct negative-control pair (child 02). The corpus SIZE is re-derived (23 at authoring, 25 at review); the property is that every member of the measured family would have been flagged, not that a particular count was.
5. Both children are in `.aw/records/plans/executed/` with every `V-*` carrying observed evidence.
6. `wnabns`'s release gate is PROVABLY PRESERVED rather than stranded (F-5). Either a plan in this Set carries `- From-Backlog: wnabns` with the same `- Blocks-Release:`, or the item is closed with cited evidence, or its gate is explicitly cleared. Verified by `aw check` reporting no `check.orphaned-live-blocker` or blocking-close finding for it. This is a completion criterion rather than a deferral because without it this Set fixes the defect and leaves a permanent `ready` release blocker describing it.

NOT A COMPLETION CRITERION, stated so nobody adds it later: retroactively consolidating the duplicate items. It needs human judgement (OQ-01) and is declared out of scope; a retiring orchestrator would otherwise mark it done unperformed. It now names a carrier (`uj5g58`) so that declaring it out does not silently discard it, per F-6.

## Cross-IPD validation

- CID-1 THE TWO CHILDREN MUST NOT BOTH EDIT ONE FILE. Child 01 is confined to `tests/test_turn_bounds.py` and child 02 to `agent_workflows/backlog.py` plus its new test module. Verify by diffing each child's committed paths against its declared `- Scope-Paths:` after both land; an overlap means one child widened silently.
- CID-2 CHILD 02's GUARD MUST NOT DEPEND ON THE FAMILY STAYING OPEN, AND THIS IS NO LONGER HYPOTHETICAL. Its tests must use fixtures, not the live tree (`jb0sc1`, `caf5ed`, `agrlvw` all record that hazard). Measured at review: 24 of the 25 filings have ALREADY moved from `open` to `graduated` since this plan was authored, so a guard whose tests read live `open` items is already looking at a corpus of ONE. Verify by running child 02's tests after child 01 is executed AND by confirming by inspection that no test reads `.aw/records/backlog/` at all.
- CID-4 NEITHER CHILD MAY QUOTE THIS PLAN'S MEASUREMENTS AS CURRENT. Both the suite counts (F-1) and the corpus size (F-2) drifted between authoring and review, in both cases within days. Each child re-derives what it asserts and records the value it measured, per the live-artifact re-derivation convention. Verify by checking each child's evidence states a measured value and the head it was measured at.
- CID-3 NEITHER CHILD MAY WEAKEN A GUARANTEE TO PASS. Child 01 must keep `R4.1`'s "no denial policy on a non-isolated turn" assertion, and child 02 must keep the advisory non-refusing. Verify by quoting both from the executed plans' evidence.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN (`AGENTS.md`): retirement skips the E/V checkpoint, so parent-only work would be discharged unperformed. Both items here are child-completion checks by construction, and the consolidation task that would have been parent-only work is declared out of scope instead.
- THE TWO CHILDREN TOUCH DISJOINT FILES, so they carry no dependency edge and may execute in either order or in parallel isolated worktrees.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER (CONFIRMED) | `tests/test_turn_bounds.py` | The policy assertion reads the ambient `OPENCODE_CONFIG_CONTENT`, so the file is green for a human and red for every lane agent. Owned by child 01. RE-MEASURED at review with the counts corrected: the specific failing assertion is `policy_key not in main_env`, and the drifted counts are why both children must re-derive rather than quote. | at review: bare `1 failed, 147 passed`; `env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE` -> `148 passed`, no code change between |
| F-2 | HIGH (CONFIRMED, count corrected) | `aw backlog new` | No near-duplicate guard, so the same defect was filed repeatedly. The corpus is TWENTY-FIVE filings at review, not 23. Owned by child 02, whose `aw graduation` precedent was verified to exist and to be advisory exactly as described. | live enumeration of the family; `aw graduation --help` confirming "Read-only and ADVISORY: it shows and never refuses" and the three-case limits statement |
| F-3 | INFO (was MED; STALE) | release gating | ORIGINAL CLAIM: all 23 carry `Blocks-Release: next`, so one defect reads as 23 release blockers. CORRECTED at review: 24 of the 25 are already `graduated` with `- Graduated-To: envhermet`, so they class `active` rather than `ready` and are no longer a blocker wall. The board noise was largely discharged by graduation before this review. | each item's `- Status:` and `- Graduated-To:`; `aw attention` classes `uj5g58` as `active` |
| F-4 | MED (scope, SHARPENED) | this parent | Consolidating the family is the one task no child covers, and declaring it OUT is correct per the orchestrator-coverage rule. But declaring it out is NOT the same as preserving it: see F-6. | `AGENTS.md` orchestrator-coverage rule; `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']` |
| F-5 | HIGH (NEW, from review) | backlog `wnabns` | The ONE still-`open` member of the family is a release blocker that NOTHING carries. It reads `- Status: open`, `- Blocks-Release: next`, has no `- Graduated-To:`, and no plan in the tree carries `- From-Backlog: wnabns` (child 01 carries `mepbmp` instead). Measured consequence: `evaluate_blocking_close` REFUSES to close it, "closing it `done` would silently drop that release gate". So when this Set lands and fixes the defect `wnabns` describes, the item cannot legitimately be closed and remains a standing `ready` release blocker for an already-fixed defect. Child 01 should carry it, which is a one-field change (`aw ipd set <status> <plan> --from-backlog wnabns` is not additive, so see OQ-02 for the chosen mechanism). | `grep -rn wnabns .aw/records/plans/` finds only two incidental mentions in executed plans; `evaluate_blocking_close(wnabns, 'done')` -> `legitimate=False`, reason quoted |
| F-6 | MED (NEW, from review) | this plan's `## Deferred` section | Four deferred rows record outstanding obligations with NO durable carrier, so `aw check` reports `check.ipd-uncarried-obligation` at `error` and `aw ipd lint --phase pre-transition` merges the same finding: this plan would block its own finalize. The consolidation task (F-4) is the sharpest case, because declaring it out of scope does not make it survive - once this plan reaches `executed` it classes `done` in `aw attention` and the consolidation obligation vanishes with no record, which is precisely the outcome F-4 was written to avoid. | `evaluate_durable_carrier` -> `error`, "5 obligation(s) name no durable carrier"; `evaluate_carrier_obligation` returns `legitimate=False` for all four deferred rows |

## Proposed changes (ordered, validatable)

1. Child 01 (`heglfv`) makes the turn-bounds assertions hermetic without weakening `R4.1`.
2. Child 02 (`fwgq2u`) adds the advisory near-duplicate guard at filing time.

## Deferred / out of scope (with reason)

- RETROACTIVELY CONSOLIDATING THE FAMILY. Needs human judgement about which filing survives and what each records; safe only after child 01 lands. Declared out rather than parked on this parent, per F-4. NOTE F-6: declaring it out does NOT preserve it, so it now names a carrier rather than relying on this prose surviving the plan's own retirement.
  - Carrier: uj5g58
- REMOVING `OPENCODE_CONFIG_CONTENT` FROM `run_opencode`. It carries the turn's configuration; changing the runner to satisfy a test inverts the priority.
  - Carrier-Declined: a rejected alternative, not an outstanding obligation. Nothing remains to be done, so there is nothing for a future artifact to carry.
- THE `AW_EXECUTION_ROLE` VARIANT some filings describe. Already scrubbed in `conftest.py` (verified at review: `os.environ.pop("AW_EXECUTION_ROLE", None)` at import time); the residual vacuity it caused is owned by `rolevac` `8i0xa7`.
  - Carrier: 8i0xa7
- EXTENDING THE DUPLICATE GUARD TO OTHER RECORD TYPES. Out of child 02's measured corpus; a successor plan if its measurement shows the pattern elsewhere.
  - Carrier: uj5g58
- THE SESSION-WIDE CONFTEST SCRUB OF `OPENCODE_CONFIG_CONTENT`, which is the obvious symmetry with the shipped `AW_EXECUTION_ROLE` scrub and is deliberately NOT taken. Child 01's OQ-01 rejects it on measured grounds: that mechanism is what made `rolevac` `8i0xa7`'s guard vacuous, so adopting it here would knowingly create the same debt. Recorded at parent level because a reader who sees the conftest precedent will otherwise ask why it was not reused.
  - Carrier-Declined: rejected with a recorded reason (child 01 OQ-01), not deferred. The alternative mechanism is what child 01 builds instead.

## Scope check

- Over-scope: this plan edits NOTHING but its own child plans' tracking. The two `- Scope-Paths:` entries are the children themselves.
- Under-scope: if a third defect surfaces in this family during execution, add a CHILD for it and a row here rather than performing it on this parent, per `AGENTS.md`.
- Under-scope, AND THE ONE AN EXECUTOR MUST RESOLVE BEFORE RUNNING THIS SET: F-5's gate preservation is an ACT (adding a `- From-Backlog: wnabns` bullet to child 01), and it must be OWNED BY A CHILD, never performed on this parent. The reason is mechanical and is the rule this parent's own history line already cites: a runner RETIRES an orchestrator once every child is `executed` and SKIPS the pre-transition E/V checkpoint, so an act parked here would be marked complete having never been performed, and the coverage gate exists to refuse exactly that. V-01 therefore VERIFIES the gate was preserved (verification is legitimate parent work) while child 01 PERFORMS it. Child 01 is not in this review's scope, so this review did not edit it; the executor must either add the bullet as part of child 01's work or author a child for it. Do NOT satisfy this by deleting the criterion.

## Required tests / validation

- No test runs on this parent: it performs no code change. Each child runs the bare `python3 -m pytest` and pastes its own summary line per the execution contract. Bare means bare: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and a second `-q` would suppress the `N passed` line this contract requires.
- This plan's validation is that both children reached `executed` with their own `V-*` evidence present, which V-01 and V-02 verify by inspection.
- V-01 additionally verifies completion criterion 6 (F-5) by inspection and by a pasted `aw check` result. That is verification of a child's act, not work performed here.
- THE FAMILY'S OWN FAILURE MODE APPLIES TO THIS SET'S EVIDENCE: a child that runs the suite from inside a lane will see the very failure this Set fixes, and before child 01 lands that failure is EXPECTED in a baseline. Each child must therefore name it explicitly in its baseline rather than letting it cancel silently, which is the reporting discipline executed plan `ty7w6o` had to improvise for exactly this test.

## Spec / documentation sync

- N/A for this parent: it changes no code and no contract. Child 01 notes that `R4.1` is unchanged in strength; child 02 updates `aw backlog new`'s documented behavior.

## Open questions

### OQ-01: Should the duplicate filings be consolidated once child 01 lands?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: uj5g58
- Resolution or deferral rationale: NOT blocking, and deliberately not performed by this Set. It needs a human because the filings are not identical: some name a different test method, at least two attribute the failure to `AW_EXECUTION_ROLE` instead (a different cause, already scrubbed), and a bulk close keyed on a similarity judgement is exactly the automatic-close this Set's child 02 argues against for good reason. THE PRESSURE BEHIND THIS QUESTION DROPPED SHARPLY AT REVIEW, and saying so is the honest report: 24 of the 25 filings are already `graduated` with `- Graduated-To: envhermet`, so they class `active` rather than `ready` and are no longer presented to the release gate as a wall of blockers. What remains is a records-tidiness question about `graduated` items whose plan has landed, plus the ONE genuine gap F-5 names, which is now a completion criterion rather than part of this question. Recommend a separate human-approved records change after child 01 is `executed`. The item carries a carrier (`uj5g58`) so the question survives this plan's retirement.

### OQ-02: How should `wnabns`'s stranded release gate be preserved (F-5)?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Carrier: wnabns
- Resolution or deferral rationale: RESOLVED AT REVIEW, from the repository's own close-legitimacy ladder rather than by asking. The problem is measured: `wnabns` is `open` with `- Blocks-Release: next`, no `- Graduated-To:`, and no plan citing it, and `evaluate_blocking_close` refuses its close because that "would silently drop that release gate". `AGENTS.md` names exactly three legitimate fixes: HANDOFF, SATISFIED, or DE-GATED. HANDOFF IS CHOSEN, because it is the only one of the three that is true: child 01 genuinely does fix the defect `wnabns` describes, so a plan carrying `- From-Backlog: wnabns` with the same gate is an accurate statement rather than a bookkeeping dodge. DE-GATED is rejected because the defect is real and release-blocking until child 01 lands. SATISFIED is rejected because it requires citing an in-tree artifact that already discharges the item, and none exists yet.
  ONE MECHANICAL CONSTRAINT THE EXECUTOR MUST NOT TRIP: child 01 already carries `- From-Backlog: mepbmp`, and `aw ipd set ... --from-backlog` SETS the field rather than appending, so naively pointing it at `wnabns` would DROP `mepbmp`'s handoff and strand that gate instead. The repository supports multiple source bullets on one plan (executed plan `y9s4vm`'s review measured five plans carrying two source links each), so the correct act is to ADD a second `- From-Backlog:` bullet to child 01, not to overwrite the first. Whether that is done by the setter or by hand is the executor's call; verify afterwards with `aw check` reporting no `check.from-backlog-dangling` and no blocking-close finding for either item.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `heglfv`'s path shown under `.aw/records/plans/executed/`, and its `V-02` observed-evidence block quoted, showing the pasted green run with `OPENCODE_CONFIG_CONTENT` SET and the mutation proving the fixed test can still fail. PLUS the re-derived counts with the head they were measured at, stated as measured values rather than quoted from this plan (CID-4). PLUS the `R4.1` assertion quoted from the executed child to show it was not weakened (CID-3). PLUS, for completion criterion 6 and F-5, `wnabns`'s `- Status:`/`- Blocks-Release:` pasted with the mechanism that preserved its gate, pasted proof that `mepbmp`'s existing handoff was not overwritten in the process (both `- From-Backlog:` bullets present, per OQ-02), and `aw check` output showing no `check.from-backlog-dangling`, no `check.orphaned-live-blocker`, and no blocking-close finding for either item. A claim that the gate "was handled" without the pasted `aw check` result does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `fwgq2u`'s path shown under `.aw/records/plans/executed/`, and its `V-02`/`V-03` observed-evidence blocks quoted, showing the advisory output with stated limits, the measured latency, and the negative-control pair not flagged. PLUS the quoted evidence that it never REFUSES (CID-3) and a pasted confirmation that its test module reads no path under `.aw/records/backlog/` (CID-2).
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: two children, disjoint files, no dependency edge; this parent carries orchestration only.

OPEN QUESTIONS: OQ-02 is resolved. OQ-01 remains `open` and is `Blocking: no`, owned by the maintainer, and carries `uj5g58`; it is a records-tidiness decision that does not gate this Set's correctness.

ONE PRECONDITION BEFORE EXECUTION, from F-5 and OQ-02: `wnabns`'s release gate must be handed to child 01 by ADDING a second `- From-Backlog: wnabns` bullet, not by overwriting the existing `mepbmp` one. `aw ipd set ... --from-backlog` SETS rather than appends, so the naive call would strand `mepbmp`'s gate instead. This is a child's act, never this parent's (see the Scope check). Without it, this Set fixes the defect and leaves `wnabns` as a permanent `ready` release blocker describing work already done, which `evaluate_blocking_close` will then refuse to close.

SCOPE FENCE (a declaration, not a stop instruction). This parent declares only its two child plan files and edits nothing else; each child declares its own paths. An out-of-scope edit is made and then JUSTIFIED at finalize with `--scope-reason`, and a declared-but-unmodified path with `--scope-ack`; `aw ipd finalize` refuses to complete without them.

THE ONE GENUINE STOP CONDITION: if a child's baseline shows `tests/test_turn_bounds.py` failures BEYOND the single known `test_the_permission_policy_by_contrast_IS_isolation_scoped` node, stop and report rather than absorbing them. This Set's entire premise is that exactly one assertion is non-hermetic; additional failures mean the family is wider than measured and the children are scoped wrong.

This plan is `to-review` and requires explicit human approval before execution. It performs no code change and commits nothing beyond its own lifecycle records. Its children commit only the paths named in their own `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Test claims must paste the actual runner output; a claimed pass with no pasted `N passed` line is a failed item. On completion of both children, `aw ipd lint --phase pre-transition` must conform and both `V-*` items must carry observed evidence. The lifecycle transition to `.aw/records/plans/executed/` is performed by the RUNNER as a rollup retirement when this Set is dispatched by `aw oc run`/`aw agy run`, and by `aw ipd finalize` when an executor drives the Set by hand; never by a hand-rolled `git mv`.
