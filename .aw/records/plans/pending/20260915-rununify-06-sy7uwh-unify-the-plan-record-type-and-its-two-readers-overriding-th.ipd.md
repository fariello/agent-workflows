# IPD: Unify the plan record type and its two readers, overriding the 818uru split

- Date: 2026-09-15
- Kind: child
- Concern: The two runners build DIFFERENT `PlanRecord` NamedTuples (oc's carries `kind`, agy's does not), which forces `parse_plan_file` and `build_dynamic_manifest` to stay forked and forces agy to re-read `- Kind:` from disk for information oc already has in hand.
- Scope: Collapse the two record types into one in `runner_shared.py` and unify their two readers. This DELIBERATELY OVERRIDES the earlier decision recorded by this Set's own child `818uru`, which pinned the two types as distinct and wrote a test asserting it; that test must be inverted, not deleted. CORRECTED AT REVIEW 2026-09-16: there are TWO pins, not one (`tests/test_orchestrator_retirement.py:2470` also asserts agy's record lacks `kind`, in a file this plan never named), and E-03's instruction to DELETE `_plan_kind` would REGRESS a live agy capability, because the helper has a SECOND call site (`agy_runipd.py:2260`) serving a legacy-manifest fallback that has nothing to do with the record split and that oc has never had. See F-7 and F-8.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_rununify_record.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: rununify
- Order: 6
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: sy7uwh
- From-Backlog: alw22r

## Workflow history
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 8 findings (PR-301..PR-308), 7 FIXED, PR-301 OPEN and escalated as blocking OQ-03. All six original findings reproduce and the unification is sound. Blocker is an omission: _plan_kind has two callers and deleting it would reintroduce the pgq326 defect (an approved orchestrator in a legacy manifest gets agent-executed) on a path no test covers. Also found a second pin the plan never named, six readers parse_plan_file closes over, a third unrelated PlanRecord, and an unfounded dependency edge pointing the wrong way.
- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-301 through PR-308 (7 FIXED, PR-301 OPEN and escalated as the new blocking OQ-03). ALL SIX ORIGINAL FINDINGS REPRODUCE and the plan's central judgement is correct: oc's `PlanRecord` IS a strict superset differing in exactly `kind`, `parse_plan_file` differs in exactly the two lines that read and pass it, F-5's one-expression `build_dynamic_manifest` difference is exact, and F-2's premise for overriding `818uru` really has dissolved. THE BLOCKER IS AN OMISSION: `_plan_kind` has TWO callers and E-03 says to delete the helper. Only `agy_runipd.py:1693` is the record-split workaround its docstring describes; `:2260` is a LEGACY-MANIFEST FALLBACK (no `kind` key in a hand-written manifest -> re-read the plan file) that oc has never had. MEASURED both ways: with it an approved orchestrator derives `orchestrate`, without it `execute`, so it would be AGENT-EXECUTED, reproducing exactly the defect `orchretire-03` (`pgq326`) fixed, on a path NO test covers, so every existing test would have stayed green. That also raised a question the plan could not know to ask and which the standing ruling reserves for the maintainer: the hosts already DISAGREE about this correctness gate in oc's disfavor, an A/NOT-A case, so whether the fallback stays agy-only, is given to both, or is dropped is OQ-03. TWO FURTHER OMISSIONS: there are TWO pins asserting the split, not one (`tests/test_orchestrator_retirement.py:2470` also asserts agy's record lacks `kind`, in a file the plan never fenced, whose surrounding test is also the best end-to-end guard for F-3's silent failure and must survive), and `parse_plan_file` closes over SIX module-level readers absent from `runner_shared`, so a naive move fails at import time. ALSO: a THIRD unrelated `PlanRecord` in `plans.py` will trip the parent's required repo-wide scan and must be allowlisted rather than "fixed" or the scan narrowed; E-01's premise 3 was reported too cleanly (nothing REQUIRES the field's absence, but two tests ASSERT it); and the `executed:i3d6ml` edge is unfounded AND POINTS THE WRONG WAY, since child 03's `discover_plans`/`expand_selectors` need `parse_plan_file` which THIS plan unifies, so it is removed and this plan should run BEFORE child 03 (third unfounded edge found in this Set today). Re-scoped: E-03 moves the six readers and removes only the record-split call site while preserving the fallback, E-04 inverts BOTH pins with citations, E-05 adds the first-ever fallback coverage plus the allowlisted repo-wide scan, a second non-vacuity control deletes the helper to prove the failure, one test file fenced, four further suites named, baseline named (7308 passed, one load-dependent flake). NOT DECIDED, deliberately: the fallback's disposition; note OQ-03 is narrow and option 1 makes the plan executable immediately with no behavior change. Typed record at `.aw/records/reviews/20260916-rununify-06-sy7uwh-unify-the-plan-record-type-and-its-two-readers-overriding-th.review.md` with 8 findings and 5 decisions, 1 irreversible and escalated.
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored after confirming that the reason 818uru pinned the split has since dissolved; see F-2.

## Goal

Make `discover_plans` build ONE record type for both hosts, so `parse_plan_file` and
`build_dynamic_manifest` stop being forked and agy stops re-reading a field from disk that the record
should already carry. This is the last structural blocker before the five large host-shaped functions.

READ THIS BEFORE EXECUTING. The 2026-09-16 review verified EVERY claim in this plan's Findings table:
F-1's pin exists with the quoted docstring, F-2's premise really has dissolved, F-3's silent failure mode
is real and is warned about in the existing suite, F-4's `_plan_kind` docstring names the split as its
reason, F-5's one-expression difference is exact, and F-6 holds. Measured: oc's `PlanRecord` field set is
a STRICT superset of agy's, differing in exactly `kind`, and `parse_plan_file` differs in exactly the two
lines that read and pass it. The unification is correct and well-motivated. THREE OMISSIONS BLOCK IT.

FIRST, `_plan_kind` HAS TWO CALL SITES AND THE PLAN ADDRESSES ONE. E-03 says to delete the helper
outright. Its second caller (`agy_runipd.py:2260`) is a LEGACY-MANIFEST FALLBACK: when a hand-written
manifest carries no `kind` key, agy re-reads the plan file rather than deriving `execute` for an
orchestrator. oc has NO such fallback (`oc_runipd.py:3446` passes `plan.get("kind")` straight through).
Measured at review: with the fallback, an approved orchestrator in a legacy manifest yields
`orchestrate`; without it, `action_for(None, "approved")` yields `execute`, so the orchestrator would be
AGENT-EXECUTED. That is precisely the defect `orchretire-03` (`pgq326`) fixed, and no test covers it. The
record-split workaround must be removed WITHOUT removing the fallback (F-7).

SECOND, THERE ARE TWO PINS, NOT ONE. Besides `DiscoverPlansRecordTypeTests`,
`tests/test_orchestrator_retirement.py:2470` also asserts `"kind" not in agy_runipd.PlanRecord._fields`,
with a comment saying that invariant "is not this plan's to break". E-04 inverts only the first, so the
second would fail and the plan does not fence its file (F-8).

THIRD, `parse_plan_file` CANNOT MOVE ALONE. It closes over six module-level readers that are not yet in
`runner_shared`: `_PLAN_FILENAME_RE`, `_read_kind`, `_read_item_dependencies`, `_read_from_backlog`
(all oc-owned, with agy importing the last three FROM oc), plus `_read_id` and `_read_status` (which
both hosts import from `selectors`). None is difficult and `_PLAN_FILENAME_RE` is byte-identical across
hosts, but the plan's checklist does not mention them and a naive move fails at import time (F-9).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-establish that the override is warranted

EXECUTOR: DO NOT START. OQ-03 is `Blocking: yes` and the lint gate refuses this plan at every
checkpoint until the maintainer answers it. E-03 is what that answer governs.

- [ ] E-01 CONFIRM AT EXECUTION HEAD that the reason `818uru` pinned the split has genuinely dissolved, and refuse to proceed if it has not. Specifically: show that agy now DOES consume `kind` (through the shared `action_for`, which reads it to detect an orchestrator), that agy currently obtains it by re-reading the plan file via its own `_plan_kind` helper rather than from the record, and that no code path depends on agy's record LACKING the field. If any of those is false, stop and report rather than overriding a decision whose premise still holds. THE REVIEW ALREADY RAN THIS at 2026-09-16 and premises 1 and 2 CONFIRM (`agy.action_for is runner_shared.action_for`; `action_for('orchestrator','approved')` -> `orchestrate`; `_plan_kind` called at `agy_runipd.py:1693` and `:2260`). PREMISE 3 IS THE ONE THAT NEEDS CARE and the review's answer is NUANCED, not a clean pass: no code path REQUIRES the field's absence, but TWO TESTS ASSERT it (`tests/test_runner_shared.py:1550` and `tests/test_orchestrator_retirement.py:2470`), and the second is not in this plan's original fence. Report both, and treat a test-asserted invariant as something to invert deliberately rather than as "nothing depends on it".
  - Depends on: none
  - Expected outcome: pasted evidence for each of the three points, naming BOTH asserting tests for premise 3, or an explicit refusal naming which premise still holds.
  - Execution state: pending

### Task group 2: the unification

- [ ] E-02 Define ONE `PlanRecord` in `runner_shared.py`, taking oc's field set (VERIFIED at review to be a strict superset, differing in exactly `kind`) per the maintainer's 2026-09-14 ruling, and have both hosts reach that name. Keep every existing field and its meaning; this is a merge of two shapes, not a redesign. NOTE A NAME COLLISION rather than a conflict: `agent_workflows/plans.py:90` defines an UNRELATED `PlanRecord` (fields `path`/`area`/`disposition`/`status`/`set_id`/`order`, a different concept with no importers of that name), so a repo-wide AST scan for "one `PlanRecord`" will find it and MUST NOT treat it as a re-fork. Name it in the scan's allowlist with that reason.
  - Depends on: E-01
  - Expected outcome: `oc_runipd.PlanRecord is agy_runipd.PlanRecord` is True, the shared type carries `kind`, no field present today on either side is lost, and `plans.PlanRecord` is left untouched with its exclusion recorded.
  - Execution state: pending

- [ ] E-03 Unify `parse_plan_file` and `build_dynamic_manifest` on the shared record, using oc's version. TWO PREREQUISITES THE ORIGINAL PLAN OMITTED, both measured at review. (a) `parse_plan_file` closes over SIX module-level readers absent from `runner_shared`: `_PLAN_FILENAME_RE` (byte-identical in both hosts, so it simply moves), `_read_kind`, `_read_item_dependencies` and `_read_from_backlog` (oc-owned; agy already imports them FROM oc), plus `_read_id` and `_read_status` (both hosts import these from `selectors`, so the shared module imports them the same way). Move or import each; a naive lift fails at import time. (b) REMOVE `_plan_kind`'s RECORD-SPLIT USE ONLY, at `agy_runipd.py:1693`, which becomes `rec.kind` exactly as oc's does. DO NOT DELETE THE HELPER: its second caller (`agy_runipd.py:2260`) is a LEGACY-MANIFEST FALLBACK for a hand-written manifest carrying no `kind` key, oc has no equivalent, and deleting it makes an approved orchestrator in such a manifest derive `execute` and be AGENT-EXECUTED, reproducing the exact defect `orchretire-03` (`pgq326`) fixed (F-7). Whether that fallback should instead be given to BOTH hosts is OQ-03.
  - Depends on: E-02
  - Expected outcome: one `parse_plan_file`, one `build_dynamic_manifest`, the six readers resolvable in `runner_shared`, `_plan_kind`'s record-split call site gone while its legacy-manifest fallback still works (demonstrated, not assumed), and the manifest still carrying a correct `kind` for an orchestrator on BOTH hosts.
  - Execution state: pending

### Task group 3: invert the pin, do not delete it

- [ ] E-04 INVERT BOTH PINS rather than deleting either, following this repo's own precedent for a pinned decision a later phase deliberately reverses (`tests/test_wtiso_characterization.py`, VERIFIED at review to be exactly that pattern). PIN ONE, `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` (`:1530`), currently asserts the two types are distinct, that oc's has `kind` and agy's does not, and that each host gets its OWN type; it must now assert they are the SAME type, that the shared type carries `kind`, and that both hosts build it. Its docstring says "This plan may NOT unify them; that is a class (c) reconciliation for a later child" -- this IS that child, so cite this plan's id in the rewritten docstring. PIN TWO, FOUND AT REVIEW AND ABSENT FROM THE ORIGINAL PLAN: `tests/test_orchestrator_retirement.py:2470` asserts `"kind" not in agy_runipd.PlanRecord._fields` with the comment "that invariant is not this plan's to break". Invert that single assertion in place, cite `sy7uwh`, and leave the rest of the surrounding test (which proves agy's queue entry carries `kind` and derives `orchestrate`) UNTOUCHED, because it is the end-to-end guard F-3 makes mandatory and it must keep passing before and after.
  - Depends on: E-03
  - Expected outcome: BOTH pins still exist, both now guard the UNIFIED shape, each carrying a docstring or comment naming `sy7uwh` as the authorizing plan; and `test_the_agy_queue_entry_carries_kind`'s orchestrator derivation still green.
  - Execution state: pending

- [ ] E-05 Add `tests/test_rununify_record.py` proving the payoff and the risks are covered: one record type shared; `kind` populated from a real plan file on BOTH hosts; the ORCHESTRATOR-DETECTION path that motivated the whole coupling still working end to end on both hosts (an `approved` orchestrator derives `orchestrate`, not `execute`); a repo-wide AST scan for a re-forked `PlanRecord` that ALLOWLISTS `plans.py`'s unrelated type with its reason (E-02); an assertion that `_plan_kind`'s RECORD-SPLIT call site is gone; and, the case the original plan would have destroyed, a test that agy's LEGACY-MANIFEST FALLBACK still resolves `kind` from disk when the manifest lacks the key, so an approved orchestrator still derives `orchestrate` (F-7). That last case has NO coverage in the suite today, which is why deleting the helper looked free.
  - Depends on: E-03
  - Expected outcome: a suite that fails if the record splits again, if `kind` stops being populated, if orchestrator detection regresses on either host, or if the legacy-manifest fallback is removed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` exists specifically to pin this split and
  its docstring calls it "the FIFTH dependency the authoring measurement missed, and the subtlest one",
  explaining that a shared constructor building the wrong type fails SILENTLY and type-shaped rather
  than crashing. That warning applies to this plan and is why E-05 tests orchestrator detection end to
  end rather than only asserting field presence.
- `tests/test_wtiso_characterization.py` is the repo's precedent for pinning a behavior so a later phase
  must deliberately come and invert the assertion. E-04 follows it: invert, cite the authorizing plan,
  never delete.
- `agy_runipd.py:158` imports the shared `action_for`, and the comment at `:140-142` records that agy
  previously had its own `determine_action` and that using oc's `action_for` for an orchestrator was a
  real defect. So agy's need for `kind` is documented in its own source.
- `agy_runipd.py:1660` `_plan_kind` documents that it is a workaround for exactly the split this plan
  removes, and that the parsing itself already delegates to the shared `_read_kind`. CRITICAL ADDITION
  FROM REVIEW: that docstring describes only ONE of its two callers. The second (`agy_runipd.py:2260`) is
  a legacy-manifest fallback with an independent reason, documented in the comment at `:2257`, and it
  must survive. Reading the docstring alone leads directly to the mistake E-03 originally made.
- `agent_workflows/plans.py:90` defines a DIFFERENT `PlanRecord` (fields `path`/`area`/`disposition`/
  `status`/`set_id`/`order`) that is unrelated to the runners' record and has no importers of that name.
  The parent's F10 requires the single-definition check be REPO-WIDE, so it will surface; allowlist it
  rather than "fixing" it or narrowing the scan to a pairwise check.
- `action_for` and `determine_action` are BOTH already in `runner_shared` (`:4703`, `:4711`) and are
  DIFFERENT functions: `action_for(kind, status)` adds orchestrator dispatch and delegates the rest to
  `determine_action(status)`. Both hosts import both. So nothing in this plan waits on a naming
  reconciliation, and the Scope check's original claim to the contrary is withdrawn.
- `PlanRecord` must remain a re-exported ATTRIBUTE of each runner module: `tests/test_oc_runipd_shim.py:46`
  and `tests/test_agy_runipd_shim.py:43` both assert the compatibility shim exposes it. A shared type
  bound under the same name satisfies them; a rename does not.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | `tests/test_runner_shared.py:1530` | An earlier child of THIS Set (`818uru`) deliberately pinned the two record types as distinct and wrote a test forbidding unification, explicitly deferring it to "a later child". Overriding that is legitimate only because this plan IS that child, and the override must be visible in the test rather than accomplished by deleting it. |
| F-2 | HIGH | `agy_runipd.py:158`, `:354`, `:1660` | THE PREMISE OF THE SPLIT HAS DISSOLVED. When `818uru` pinned it, agy had no use for `kind`. agy now imports the shared `action_for`, which READS `kind` to detect an orchestrator, and agy supplies it by re-reading the plan file through its own `_plan_kind` helper. So the split now costs a redundant disk read and buys nothing. |
| F-3 | HIGH | `tests/test_runner_shared.py:1568` | The existing suite already warns that a shared constructor dropping `kind` "would silently disable orchestrator detection". That is the precise failure mode of this change, and it is type-shaped and silent, so E-05 must assert the orchestrator DERIVATION end to end and not merely that a field exists. |
| F-4 | MED | `agy_runipd.py:1660` | `_plan_kind`'s own docstring names the record split as its reason for existing and calls unifying the two types "a later reconciliation". Deleting the helper is therefore the intended outcome, not collateral damage. |
| F-5 | MED | `build_dynamic_manifest` | The two versions differ in exactly ONE expression: `'kind': rec.kind` versus `'kind': _plan_kind(rec.path)`. Once the record is unified this symbol becomes byte-identical, so it collapses for free rather than needing its own reconciliation. |
| F-6 | LOW | `oc_runipd.py:2689` | oc already writes `rec.kind` into the manifest, so the shared form is the one already in production on the oc side; agy's is the deviation being removed. **VERIFIED at review.** |

### Findings added by the 2026-09-16 plan review

ALL SIX ORIGINAL FINDINGS REPRODUCE. Verified individually: F-1's pin exists at
`tests/test_runner_shared.py:1530` with the quoted "later child" docstring; F-2's premise really has
dissolved (`agy.action_for is runner_shared.action_for` is True and `action_for('orchestrator',
'approved')` returns `orchestrate`); F-3's warning is present in the existing suite and its failure mode
is genuinely silent; F-4's `_plan_kind` docstring names the split as its reason for existing; F-5's
one-expression difference is exact (`'kind': rec.kind` vs `'kind': _plan_kind(rec.path)`); F-6 holds.
Also verified independently: oc's field set is a strict superset differing in exactly `kind`, and
`parse_plan_file` differs in exactly the two lines that read and pass it. The findings below are what the
plan OMITTED.

| # | Sev | Where | Finding |
|---|---|---|---|
| F-7 | BLOCKER | `agy_runipd.py:2260`; `oc_runipd.py:3446`; executed at review | **`_plan_kind` HAS TWO CALL SITES AND DELETING IT REGRESSES A LIVE AGY CAPABILITY.** E-03 says to delete the helper. Only ONE caller (`:1693`) is the record-split workaround F-4 describes. The other (`:2260`) is a LEGACY-MANIFEST FALLBACK: when a hand-written manifest carries no `kind` key, agy re-reads the plan file rather than deriving `execute` for an orchestrator. oc has NO equivalent (`:3446` passes `plan.get("kind")` straight through). MEASURED: with the fallback an approved orchestrator in a legacy manifest yields `orchestrate`; without it `action_for(None,"approved")` yields `execute`, so the orchestrator is AGENT-EXECUTED. That is the exact defect `orchretire-03` (`pgq326`) fixed, per the comment at `agy_runipd.py:2257`, and NO test covers it, which is why deleting the helper looked free. |
| F-8 | HIGH | `tests/test_orchestrator_retirement.py:2470` | **THERE ARE TWO PINS, NOT ONE, AND THE PLAN NAMES ONE.** Besides `DiscoverPlansRecordTypeTests`, this test asserts `"kind" not in agy_runipd.PlanRecord._fields`, with the comment "The record type itself is UNCHANGED: `818uru` pinned the two as distinct and that invariant is not this plan's to break." E-04 inverts only the first pin, so the second FAILS, and its file was not in `Scope-Paths`, so `aw ipd finalize` would additionally refuse the out-of-scope edit. The surrounding test is also the best existing end-to-end guard (it proves agy's queue entry carries `kind` and derives `orchestrate`), so it must keep passing rather than be rewritten. |
| F-9 | HIGH | `parse_plan_file`'s closure | **`parse_plan_file` CANNOT MOVE ALONE; SIX MODULE-LEVEL READERS MUST BE RESOLVABLE FIRST.** Closure-checked at review: `_PLAN_FILENAME_RE`, `_read_kind`, `_read_item_dependencies`, `_read_from_backlog`, `_read_id`, `_read_status`. None is in `runner_shared` today. `_PLAN_FILENAME_RE` is byte-identical across hosts so it simply moves; `_read_kind`/`_read_item_dependencies`/`_read_from_backlog` are oc-owned with agy already importing them FROM oc (so moving them also removes three oc-to-agy imports); `_read_id`/`_read_status` are `selectors` re-exports both hosts already share, so the shared module imports them the same way. Not difficult, but unstated, and a naive move fails at import time rather than in a test. |
| F-10 | MEDIUM | `agent_workflows/plans.py:90` | **A THIRD `PlanRecord` EXISTS AND A REPO-WIDE SCAN WILL FIND IT.** `plans.py` defines an UNRELATED `PlanRecord` (`path`/`area`/`disposition`/`status`/`set_id`/`order`), a different concept with no importers of that name. The parent orchestrator's F10 requires the single-definition check be REPO-WIDE across `agent_workflows/*.py` rather than pairwise, so E-05's scan will flag it. It must be allowlisted WITH its reason, or the executor will either "fix" an unrelated type or weaken the scan to pairwise, which is the check F10 exists to prevent. |
| F-11 | MEDIUM | `- Item-Dependencies: executed:i3d6ml` | **THE DEPENDENCY ON CHILD 03 IS UNFOUNDED.** Closure-checked at review: none of `PlanRecord`, `parse_plan_file` or `build_dynamic_manifest` references anything among child 03's 48 symbols. Note the converse IS true and is child 03's problem, not this plan's: child 03's `discover_plans` and `expand_selectors` need `parse_plan_file`, which is why child 03's own review recorded them as blocked on THIS plan. So the correct edge direction is the opposite of the one declared, and the honest answer is no edge here plus an edge there. Removed, which frees this plan to run first. |
| F-12 | LOW | `- Scope-Paths:` as authored | **THE FENCE OMITS THE FILE E-04 MUST EDIT.** `tests/test_orchestrator_retirement.py` carries the second pin (F-8) and is also named in Required tests item 5, so the plan already knew it was affected. Added. Also worth the executor's attention though NOT fenced (no edit expected): `PlanRecord` is referenced by `tests/test_oc_runipd_shim.py:46` and `tests/test_agy_runipd_shim.py:43`, which require it to remain a re-exported ATTRIBUTE of each runner module; a shared type re-exported under the same name satisfies them, but a rename would not. |
| F-13 | LOW | Required tests item 6 | **THE SUITE BASELINE IS UNSTATED AND ONE FAILURE IS PRE-EXISTING.** Measured at review, bare `python3 -m pytest`: `1 failed, 7308 passed, 3 skipped, 2 xfailed`. The failure is `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, a 30s subprocess timeout under parallel load that passes in isolation (`7 passed in 1.13s`). Named so the executor does not chase it. |

## Proposed changes (ordered, validatable)

1. Re-confirm the override is warranted at execution HEAD, and refuse if it is not (E-01).
2. One `PlanRecord` in `runner_shared`, oc's superset field set, with `plans.py`'s unrelated type
   allowlisted (E-02).
3. Move the six readers `parse_plan_file` closes over, unify both readers, and remove `_plan_kind`'s
   RECORD-SPLIT call site while PRESERVING its legacy-manifest fallback (E-03).
4. Invert BOTH pins, citing this plan in each (E-04).
5. Add the payoff-and-risk suite, including end-to-end orchestrator detection and the first-ever
   coverage of the legacy-manifest fallback (E-05).

## Deferred / out of scope (with reason)

- The 48 no-disagreement symbols (child 03, `i3d6ml`), the 8 host-string symbols (child 04, `tx6q0h`),
  and the two behavior conflicts (child 05, `ct4w0a`). NOTE the declared edge on `i3d6ml` was REMOVED at
  review (F-11): closure-checked, nothing here needs anything child 03 owns, and the real coupling runs
  the OTHER way (child 03's `discover_plans` and `expand_selectors` need `parse_plan_file`, which this
  plan unifies), so this plan should run BEFORE child 03 rather than after it.
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11. Several
  of them CONSUME `PlanRecord`, which is why this plan is ordered before them: unifying the record first
  removes a variable from each of those five splits.
- REDESIGNING the record (renaming fields, adding new ones, changing types). This is a merge of two
  existing shapes and nothing more; a field nobody reads today must not appear.

## Scope check

- Over-scope: none. Three source files and three test files, three symbols plus one call-site removal.
- Under-scope, CORRECTED AT REVIEW: the plan is LARGER than it claimed in three ways it must now carry
  (F-7, F-8, F-9): six readers must become resolvable in `runner_shared` before `parse_plan_file` can
  move; a SECOND pin must be inverted in a second test file; and `_plan_kind` must be partially rather
  than wholly removed, with new coverage for the fallback that survives. None of these is optional and
  each was invisible in the original checklist.
- Under-scope, WITHDRAWN AT REVIEW: the original note said this plan "does not unify
  `action_for`/`determine_action` naming, which child 03 or 04 settles; it only relies on whichever name
  survives." There is nothing to settle. Both functions ALREADY live in `runner_shared` (`:4703`,
  `:4711`) and are DIFFERENT functions, `action_for` adding orchestrator dispatch and delegating the rest
  to `determine_action`. Both hosts import both. So no dependency on either child arises from this.

## Required tests / validation

1. `tests/test_rununify_record.py` (new): one shared record type; `kind` populated from a real plan file
   on BOTH hosts; END-TO-END orchestrator detection on both hosts (an `approved` orchestrator derives
   `orchestrate`); a REPO-WIDE AST scan for a re-forked `PlanRecord` that allowlists `plans.py`'s
   unrelated type with its reason (F-10); and an assertion that `_plan_kind`'s RECORD-SPLIT call site is
   gone.
2. THE LEGACY-MANIFEST FALLBACK COVERED FOR THE FIRST TIME (F-7): a hand-written manifest with NO `kind`
   key, pointing at an `approved` orchestrator on disk, must still derive `orchestrate` on agy. This test
   FAILS if `_plan_kind` is deleted outright, which is exactly the mistake E-03 originally invited, and
   nothing in the suite catches it today.
3. BOTH PINS INVERTED and green, each citing this plan (F-8): `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests`
   and the single assertion at `tests/test_orchestrator_retirement.py:2470`. The surrounding
   `test_the_agy_queue_entry_carries_kind` must pass BEFORE and AFTER, unchanged apart from that one line.
4. NON-VACUITY, TWO controls, because two different silent failures are possible: (a) drop `kind` from the
   shared record and show BOTH the new suite and the inverted class FAIL naming orchestrator detection;
   (b) delete `_plan_kind` entirely and show the legacy-manifest test FAILS naming `execute` where
   `orchestrate` was required. Restore both. F-3 makes (a) mandatory; F-7 makes (b) mandatory.
5. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green.
6. `tests/test_orchestrator_retirement.py` and `tests/test_orchestrator_probe_cache.py` green, named
   because both reason about orchestrators and would be affected by a `kind` regression.
7. `tests/test_oc_runipd_shim.py` and `tests/test_agy_runipd_shim.py` green, named because both require
   `PlanRecord` to remain a re-exported ATTRIBUTE of each runner module (F-12); a shared type re-exported
   under the same name satisfies them, a rename would not.
8. `tests/test_runner_item_dependencies.py` and `tests/test_runner_backlog_close.py` green, named because
   both exercise `parse_plan_file` and `build_dynamic_manifest` directly.
9. Bare `python3 -m pytest`, summary pasted, at or above the 7308-passed baseline MEASURED AT REVIEW
   2026-09-16, with NO NEW failure judged against the one known flake named in F-13; if that test fails,
   show it passing in isolation rather than treating it as a regression.

## Spec / documentation sync

No `.spec.md` change. `PlanRecord` is an internal type; no spec names it or its fields. The decision
being overridden lives in TESTS and in `818uru`'s plan record, not in a spec, which is why E-04's
inversion plus this plan's own history entry is the complete and correct paper trail.

CHECKED AT REVIEW 2026-09-16 and the no-change conclusion HOLDS, with one correction and one caveat.
CORRECTION: "a TEST" is TWO tests (F-8), so the paper trail is complete only if BOTH are inverted with a
citation; inverting one and letting the other fail would leave the override half-recorded and the suite
red. CAVEAT: the orchestrator DISPATCH contract that `kind` feeds is documented in `action_for`'s own
docstring, which warns it "is a DISPATCH decision, not a retirement authorization" and that the
retirement transition re-checks eligibility itself. This plan does not touch that boundary, and an
executor tempted to "simplify" orchestrator handling while unifying the record would; the boundary is
noted here so it is visibly out of scope rather than merely unmentioned.

## Open questions

### OQ-01: Is it legitimate for one child of a Set to override a decision made by an earlier child of the same Set?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: Yes, and here it is the earlier child's own instruction. `818uru`
  pinned the split and wrote, in the test itself, "This plan may NOT unify them; that is a class (c)
  reconciliation for a later child." This is that child, authorized by the maintainer's 2026-09-14
  ruling to unify toward oc. The obligation the override carries is TRACEABILITY, which E-04 discharges
  by inverting the assertion and naming this plan in its docstring rather than deleting the guard.

### OQ-02: Should the shared record take oc's field set, or a new minimal intersection?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: oc's field set, because it is a strict SUPERSET of agy's, so a merge
  loses nothing and the standing ruling prefers oc. An intersection would drop `kind` and thereby
  disable the orchestrator detection both hosts now depend on, which is the exact silent failure F-3
  names. No new field is added; anything not present on either side today stays absent.

### OQ-03: agy has a legacy-manifest `kind` fallback that oc lacks. Preserve it as agy-only, or give it to both?

- Blocking: yes
- Finding: PR-301
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT RESOLVABLE FROM REPOSITORY EVIDENCE. The evidence settles that
  the fallback EXISTS, is agy-only, is uncovered by tests, and must not be deleted; it does not settle
  whether the two hosts should now behave the SAME way here, and that is a behavior question about a
  correctness gate rather than a refactor detail.
  THE SYMPTOM, plainly: a runner can be pointed at a hand-written manifest. If that manifest omits the
  `kind` key and names an APPROVED ORCHESTRATOR, then today `aw agy run` re-reads the plan file, sees
  `- Kind: orchestrator`, and correctly retires it, while `aw oc run` derives `execute` and spends an
  AGENT TURN executing a plan that authors no code. Measured both ways at review. So the hosts already
  disagree about a correctness gate, in oc's DISfavor, which is the opposite of this Set's usual
  direction and is why "adopt oc" cannot be applied mechanically here.
  WHY THIS PLAN CANNOT DECIDE IT: the Set's standing ruling is "oc is preferred unless one host does A
  and the other NOT A". This is exactly an A / NOT-A case, so by the ruling's own terms it needs a
  per-symbol decision, and the maintainer gave per-symbol rulings for `extract_session_id` and
  `driver_begin` but was never asked about this one, because the plan did not know the second call site
  existed.
  The options:
  1. PRESERVE AS AGY-ONLY. Keep `_plan_kind` for its fallback caller only, remove the record-split
     caller, and add the missing test. Smallest change, strictly no regression, and it leaves the two
     hosts disagreeing on a correctness gate, which is the drift this Set exists to end.
  2. GIVE THE FALLBACK TO BOTH HOSTS by lifting it into the shared manifest-reading path, so oc also
     re-reads `- Kind:` when a manifest omits it. Removes the disagreement in the SAFE direction and
     fixes a real (if narrow) oc defect. It is a behavior change to oc, so it needs this authorization.
  3. DROP THE FALLBACK FROM BOTH, treating a manifest without `kind` as unsupported and requiring
     `aw` to regenerate it. Cleanest code, and it knowingly reintroduces the `pgq326` defect for anyone
     with an old manifest, so it should be chosen only if hand-written manifests are declared unsupported.
  My recommendation is OPTION 2, with OPTION 1 as the safe fallback if the maintainer would rather not
  change oc's behavior inside a record-unification child. I did NOT act on either, because option 2
  changes what `aw oc run` does with an existing manifest and option 3 removes a guard that a prior plan
  deliberately added.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted proof of all three premises (agy consumes `kind` via the shared `action_for`; agy obtains it by re-reading the file through `_plan_kind`; nothing depends on agy's record lacking the field), or the explicit refusal. For premise 3 specifically, NAME BOTH asserting tests (`tests/test_runner_shared.py:1550` and `tests/test_orchestrator_retirement.py:2470`) rather than reporting a clean pass, since a test-asserted invariant is something to invert deliberately.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.PlanRecord is agy_runipd.PlanRecord` returning True, the shared `_fields` tuple, and a field-by-field comparison against BOTH pre-change types showing nothing was lost. PLUS confirmation that `agent_workflows/plans.py:90`'s unrelated `PlanRecord` is UNCHANGED and is allowlisted in the scan with its reason (F-10).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted identity results for `parse_plan_file` and `build_dynamic_manifest`; evidence that all SIX readers (`_PLAN_FILENAME_RE`, `_read_kind`, `_read_item_dependencies`, `_read_from_backlog`, `_read_id`, `_read_status`) resolve in `runner_shared` (F-9); an AST scan showing `_plan_kind`'s RECORD-SPLIT call site at `agy_runipd.py:1693` is gone; a rendered manifest entry from BOTH hosts carrying the correct `kind` for an orchestrator plan; AND, the case the original plan would have destroyed, a demonstration that agy's legacy-manifest fallback STILL derives `orchestrate` for an approved orchestrator when the manifest omits `kind` (F-7). If the maintainer chose OQ-03 option 2, show oc doing the same.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: BOTH inverted pins pasted, each showing it now asserts the unified shape and each citing this plan, plus their green runs. PLUS `test_the_agy_queue_entry_carries_kind` shown green with only its single record-shape assertion changed, since it is the end-to-end guard F-3 makes mandatory and rewriting it would remove the protection this plan most needs.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_record.py -o addopts=""` green, including the end-to-end orchestrator-derivation case on both hosts and the legacy-manifest fallback case. (b) BOTH non-vacuity controls from Required tests item 4: with `kind` dropped, the new suite and the inverted class FAIL naming orchestrator detection; with `_plan_kind` deleted entirely, the legacy-manifest test FAILS naming `execute` where `orchestrate` was required; both restored green. (c) The repo-wide `PlanRecord` scan output showing exactly one runner-owned definition plus the allowlisted `plans.py` entry. (d) Bare `python3 -m pytest` at or above 7308 passed with no new failure judged against F-13's named flake, plus the orchestrator, shim and dependency suites named in Required tests items 6 to 8 green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. EVALUATED AT REVIEW 2026-09-16 rather than inherited. The five items
  are one concern each and the revision added no item, only obligations inside existing ones: E-03 gained
  the six-reader prerequisite and the partial `_plan_kind` removal, E-04 gained the second pin, E-05
  gained two cases. E-03 is now the densest item and is the one to watch, but its parts are inseparable:
  the readers must move for the function to move, and the call-site surgery is inside the same two
  functions being unified, verified by one `V-*`.

OQ-03 IS OPEN AND `Blocking: yes`. `aw ipd lint` refuses this plan at every checkpoint until the
maintainer answers it, including `aw ipd begin`. Note the question is NARROW: the record unification
itself is authorized and sound, and only the disposition of agy's legacy-manifest fallback waits.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, restated after the 2026-09-16 review:

1. F-7, THE SECOND `_plan_kind` CALLER. The single most likely way to damage this repository from this
   plan is to follow E-03's original instruction literally and delete the helper, silently reintroducing
   the `pgq326` defect (an approved orchestrator in a legacy manifest gets AGENT-EXECUTED) on a path no
   test covers. V-03 and V-05(b) exist to make that impossible to do accidentally.
2. F-3's SILENT, TYPE-SHAPED FAILURE plus V-05(b)'s first control. A dropped `kind` disables orchestrator
   detection without crashing, so a control that cannot fail leaves the whole change unproven. This was
   the original plan's own best insight and it remains correct.
3. F-8, THE SECOND PIN. Verify BOTH pins are inverted with a citation and that
   `test_the_agy_queue_entry_carries_kind` still passes with only its one record-shape line changed.
4. E-01's premise 3, because "nothing depends on it" and "two tests assert it" are different statements,
   and the honest report is the second.
