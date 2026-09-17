# IPD: Unify the plan record type and its two readers, overriding the 818uru split

- Date: 2026-09-15
- Kind: child
- Concern: The two runners build DIFFERENT `PlanRecord` NamedTuples (oc's carries `kind`, agy's does not), which forces `parse_plan_file` and `build_dynamic_manifest` to stay forked and forces agy to re-read `- Kind:` from disk for information oc already has in hand.
- Scope: Collapse the two record types into one in `runner_shared.py` and unify their two readers. This DELIBERATELY OVERRIDES the earlier decision recorded by this Set's own child `818uru`, which pinned the two types as distinct and wrote a test asserting it; that test must be inverted, not deleted. CORRECTED AT REVIEW 2026-09-16: there are TWO pins, not one (`tests/test_orchestrator_retirement.py:2470` also asserts agy's record lacks `kind`, in a file this plan never named), and E-03's instruction to DELETE `_plan_kind` would REGRESS a live agy capability, because the helper has a SECOND call site (`agy_runipd.py:2260`) serving a legacy-manifest fallback that has nothing to do with the record split and that oc has never had. See F-7 and F-8.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_rununify_record.py, tests/test_orchestrator_retirement.py, tests/test_orchestrator_probe_cache.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: rununify
- Order: 6
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: sy7uwh
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 executed (opencode/its_direct-pt3-claude-opus-5-1m-us): Unify the plan record type and its two readers: ONE PlanRecord, parse_plan_file and build_dynamic_manifest in runner_shared, and give the legacy-manifest kind fallback to BOTH hosts (fixing an oc defect where an approved orchestrator named by a manifest omitting kind derived execute and would have spent a paid agent turn on a plan that authors no code). Work landed in commits 65c75d37, 2e7c17f1, 20311677, integrated to main as d8dc4073. FINALIZED OUT OF BAND on 2026-09-17: the original run left this substantially-complete because the begin receipt went STALE when the executing agent honestly ADDED tests/test_orchestrator_probe_cache.py to Scope-Paths mid-execution. Reconciled manually against three proven guards (the receipt's digest genuinely describes the plan text at its base_head; the requirement categories differ ONLY in scope; the scope change is purely additive in both the requirement and the allowlist), with base_head left unchanged. The defect is filed as plan 63425h.
- 2026-09-17 execution-evidence-recorded (opencode/its_direct-pt3-claude-opus-5-1m-us, via `aw oc run` lane `sy7uwh`): THIS ENTRY RECORDS EVIDENCE ONLY AND ASSERTS NO TERMINAL TRANSITION. The plan's `- Status:` stays `approved` and the file stays in `pending/`; the `approved -> executed` transition is the RUNNER's to perform through `aw ipd finalize`, which is also why this lane could not run `aw ipd begin` (`AW-LIFECYCLE-ROLE-001` correctly refuses a worker-role process). ALL FIVE E-ITEMS PERFORMED AND ALL FIVE V-ITEMS PASS with pasted evidence. There is now ONE `PlanRecord` (`runner_shared.py:3282`, oc's field set), ONE `parse_plan_file`, ONE `build_dynamic_manifest`, and the six readers `parse_plan_file` closes over are all resolvable in `runner_shared`; `oc_runipd.PlanRecord is agy_runipd.PlanRecord` is True and the merge is a strict UNION (nothing lost, nothing invented). Both pins were INVERTED rather than deleted, each citing this plan, and `test_the_agy_queue_entry_carries_kind` was verified green at HEAD `85c14014` AND here with only its one record-shape assertion changed. `tests/test_rununify_record.py` adds 24 tests including the FIRST-EVER coverage of the legacy-manifest fallback. Bare `python3 -m pytest`: `7537 passed`, one failure which is F-13's named flake (`47 passed` for its file in isolation). SIX THINGS A READER SHOULD KNOW THAT THE PLAN DID NOT SAY. (1) OQ-03 OPTION 2 WAS IMPLEMENTED, not just authorized: `resolve_manifest_kind` is wired into BOTH hosts' queue-build AND `--action` preflight sites, so oc's measured defect (deriving `execute` for an approved orchestrator named by a legacy manifest, spending a paid agent turn on a plan that authors no code) is FIXED rather than merely documented. (2) THE `_read_id`/`_read_status` MOVE HAD TO DEVIATE from E-03's wording: a module-level `selectors` import in `runner_shared` fails a deliberate import-graph guard, so the function-local form (the module's own convention for `ipd_lint`/`ipd_schema`) was used; the guard was SATISFIED and no allowlist was widened. (3) THREE ADJACENT DEFECTS the unification exposed were fixed in the same pass, all of the same kind (two sites deriving `kind` differently): oc's queue entry froze the RAW manifest value while deriving `action` from the resolved one, so a resume would have disagreed with the run that created it; both hosts' `--action` preflight read `kind` raw while the dispatch resolved it, contradicting that block's own comment promising the two "cannot disagree"; and the preflight resolved the plan path only when the status was missing, so a legacy manifest with a status but no `kind` had nothing to fall back to. (4) F-13's SUITE BASELINE IS STALE: measured at HEAD in a throwaway worktree, the true baseline is `7513 passed, 0 failed`, not `7308 passed, 1 failed`, so the named failure is a flake rather than a standing one; against the true baseline this change is exactly `+24`. (5) THE oc-to-agy IMPORT COUPLING DROPPED 56 -> 53 (`_read_kind`, `_read_item_dependencies`, `_read_from_backlog` now reach agy through `runner_shared`), re-measured and re-noted in `tests/test_orchestrator_probe_cache.py` as that assertion's own message instructs; this also retires a stated excuse, since `_read_kind`'s old import comment claimed the reader had to stay in `oc_runipd` until `cnwy8g` moved the whole reader family. (6) THE NON-VACUITY CONTROLS WERE RUN AGAINST THE REAL SOURCE and one of them IMPROVED A TEST: control 1's first form crashed loudly (`TypeError`) and so was the wrong control for a failure F-3 says is SILENT, and control 2 initially failed one assertion too early to name the `execute`-where-`orchestrate` consequence this plan requires, so the assertion order was corrected. THREE BACKLOG ITEMS FILED for defects found and not fixed here: `ykfgpd` (the now-vestigial `discover_plans` injection seam), `1gw7nl` (stale record-split citations possibly remaining outside this fence), `hdxp39` (a pre-existing ruff-format drift in `runner_shared.py` that forces every plan touching the file to choose between sweeping a co-worker's reformat or restoring it by hand; restored by hand here). Nothing pushed.
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
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

OQ-03 WAS ANSWERED BY THE MAINTAINER ON 2026-09-16 AND IS `Status: resolved` (option 2: give the
legacy-manifest fallback to BOTH hosts). The "DO NOT START" hold that stood here is therefore
DISCHARGED, and `aw ipd lint` reports this plan `conforming`. Executed 2026-09-17 at HEAD `85c14014`.

- [x] E-01 CONFIRM AT EXECUTION HEAD that the reason `818uru` pinned the split has genuinely dissolved, and refuse to proceed if it has not. Specifically: show that agy now DOES consume `kind` (through the shared `action_for`, which reads it to detect an orchestrator), that agy currently obtains it by re-reading the plan file via its own `_plan_kind` helper rather than from the record, and that no code path depends on agy's record LACKING the field. If any of those is false, stop and report rather than overriding a decision whose premise still holds. THE REVIEW ALREADY RAN THIS at 2026-09-16 and premises 1 and 2 CONFIRM (`agy.action_for is runner_shared.action_for`; `action_for('orchestrator','approved')` -> `orchestrate`; `_plan_kind` called at `agy_runipd.py:1693` and `:2260`). PREMISE 3 IS THE ONE THAT NEEDS CARE and the review's answer is NUANCED, not a clean pass: no code path REQUIRES the field's absence, but TWO TESTS ASSERT it (`tests/test_runner_shared.py:1550` and `tests/test_orchestrator_retirement.py:2470`), and the second is not in this plan's original fence. Report both, and treat a test-asserted invariant as something to invert deliberately rather than as "nothing depends on it".
  - Depends on: none
  - Expected outcome: pasted evidence for each of the three points, naming BOTH asserting tests for premise 3, or an explicit refusal naming which premise still holds.
  - Execution state: performed
  - Execution note: PERFORMED 2026-09-17 at HEAD `85c14014`. All three premises re-measured independently of the review; the override is warranted and this item does NOT refuse. Premise 1 CONFIRMS: `agy.action_for is runner_shared.action_for` -> True, and `action_for('orchestrator','approved')` -> `orchestrate` while `action_for(None,'approved')` -> `execute`, so agy genuinely consumes `kind`. Premise 2 CONFIRMS: AST-measured, `_plan_kind` was defined at `agy_runipd.py:1735` and called at `:1768` and `:2335` (the review's `:1693`/`:2260` line numbers had drifted by intervening work; the two CALL SITES are the same two), and `build_dynamic_manifest` read `'kind': _plan_kind(rec.path)` on agy against `'kind': rec.kind` on oc. Premise 3 is reported AS THE REVIEW REQUIRED, nuanced rather than clean: no code path REQUIRES the field's absence, but TWO TESTS ASSERT it, and BOTH are named -- `tests/test_runner_shared.py:1666` and `tests/test_orchestrator_retirement.py:2559` (again line-drifted from the review's `:1550`/`:2470`), each carrying `assertNotIn("kind", agy_runipd.PlanRecord._fields)`. Both were INVERTED by E-04 rather than treated as "nothing depends on it". Also re-measured: oc's field set was a strict SUPERSET of agy's differing in exactly `{'kind'}`, and the two types were distinct objects.

### Task group 2: the unification

- [x] E-02 Define ONE `PlanRecord` in `runner_shared.py`, taking oc's field set (VERIFIED at review to be a strict superset, differing in exactly `kind`) per the maintainer's 2026-09-14 ruling, and have both hosts reach that name. Keep every existing field and its meaning; this is a merge of two shapes, not a redesign. NOTE A NAME COLLISION rather than a conflict: `agent_workflows/plans.py:90` defines an UNRELATED `PlanRecord` (fields `path`/`area`/`disposition`/`status`/`set_id`/`order`, a different concept with no importers of that name), so a repo-wide AST scan for "one `PlanRecord`" will find it and MUST NOT treat it as a re-fork. Name it in the scan's allowlist with that reason.
  - Depends on: E-01
  - Expected outcome: `oc_runipd.PlanRecord is agy_runipd.PlanRecord` is True, the shared type carries `kind`, no field present today on either side is lost, and `plans.PlanRecord` is left untouched with its exclusion recorded.
  - Execution state: performed
  - Execution note: ONE `PlanRecord` now lives at `runner_shared.py:3282`, taking oc's field set verbatim, and both hosts import it by name (`oc_runipd.py`, `agy_runipd.py`). Measured: `oc_runipd.PlanRecord is agy_runipd.PlanRecord` -> True and both are `runner_shared.PlanRecord`. The merge is a UNION and nothing else: every one of oc's ten fields and every one of agy's nine is present, and `set(shared) == set(oc) | set(agy)` so no field nobody read before was invented (OQ-02's requirement). `agent_workflows/plans.py` is UNTOUCHED (`git diff HEAD -- agent_workflows/plans.py` is empty) and its unrelated `PlanRecord` (`path`/`area`/`disposition`/`status`/`set_id`/`order`) is ALLOWLISTED in the repo-wide scan by `tests/test_rununify_record.py::ALLOWLISTED_COLLISIONS` with its reason recorded there. The allowlist is itself guarded: `test_the_allowlisted_collision_is_REAL_and_carries_its_reason` fails if an entry becomes stale, carries no reason, or ever names a type that has acquired the runners' shape (i.e. a genuine fork hidden in the allowlist).

- [x] E-03 Unify `parse_plan_file` and `build_dynamic_manifest` on the shared record, using oc's version. TWO PREREQUISITES THE ORIGINAL PLAN OMITTED, both measured at review. (a) `parse_plan_file` closes over SIX module-level readers absent from `runner_shared`: `_PLAN_FILENAME_RE` (byte-identical in both hosts, so it simply moves), `_read_kind`, `_read_item_dependencies` and `_read_from_backlog` (oc-owned; agy already imports them FROM oc), plus `_read_id` and `_read_status` (both hosts import these from `selectors`, so the shared module imports them the same way). Move or import each; a naive lift fails at import time. (b) REMOVE `_plan_kind`'s RECORD-SPLIT USE ONLY, at `agy_runipd.py:1693`, which becomes `rec.kind` exactly as oc's does. DO NOT DELETE THE HELPER: its second caller (`agy_runipd.py:2260`) is a LEGACY-MANIFEST FALLBACK for a hand-written manifest carrying no `kind` key, oc has no equivalent, and deleting it makes an approved orchestrator in such a manifest derive `execute` and be AGENT-EXECUTED, reproducing the exact defect `orchretire-03` (`pgq326`) fixed (F-7). Whether that fallback should instead be given to BOTH hosts is OQ-03.
  - Depends on: E-02
  - Expected outcome: one `parse_plan_file`, one `build_dynamic_manifest`, the six readers resolvable in `runner_shared`, `_plan_kind`'s record-split call site gone while its legacy-manifest fallback still works (demonstrated, not assumed), and the manifest still carrying a correct `kind` for an orchestrator on BOTH hosts.
  - Execution state: performed
  - Execution note: PERFORMED, including BOTH prerequisites the original checklist omitted, and with OQ-03's answer implemented rather than deferred. (a) THE SIX READERS: `_read_kind` (`runner_shared.py:3216`), `_read_item_dependencies` (`:3224`), `_read_from_backlog` (`:3259`) and `_PLAN_FILENAME_RE` (`:194`) now live in `runner_shared`; `_read_id`/`_read_status` resolve through FUNCTION-LOCAL imports inside `parse_plan_file` rather than at module scope. That last choice is deliberate and is a correction to this item's own instruction ("the shared module imports them the same way", i.e. at module level): a module-level `selectors` import FAILS `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate::test_no_new_module_level_first_party_import_in_runner_shared`, a deliberate import-graph guard allowing only `render_stream` plus the designated peer `runner_profiles`. Measured before choosing: of the 12 non-runner modules importing `runner_shared`, five (`attention`, `completion`, `ipd_lifecycle`, `ipd_set_plan`, `runner_shutdown`) do NOT currently reach `selectors`, so a module-level import would newly tax them. The function-local form is the module's OWN convention (`_read_item_dependencies` and `_read_from_backlog` do the same), so the guard was satisfied WITHOUT weakening it -- no allowlist was widened. `_KIND_RE` moved too rather than being left as a duplicate constant. (b) `_plan_kind` IS GONE FROM BOTH HOSTS AS A NAME, but NOT as a capability, and the distinction is the whole point of F-7: its record-split caller became `rec.kind`, and its LEGACY-MANIFEST FALLBACK was LIFTED to `runner_shared.plan_kind_from_file` + `resolve_manifest_kind`. AST-measured: zero `_plan_kind` definitions and zero call sites in either host. OQ-03 OPTION 2 IMPLEMENTED: `resolve_manifest_kind` is now called at BOTH hosts' queue-build sites AND at both hosts' `--action` legality preflight sites, so oc gained the fallback it lacked. THREE FIXES BEYOND THE LETTER OF THE ITEM, each because unifying exposed them: (i) oc's queue entry froze the RAW manifest `kind` while deriving `action` from the resolved one, so a resume would have disagreed with the run that created it -- it now freezes the resolved value, as agy always did; (ii) both hosts' `--action` preflight read `kind` raw while the dispatch resolved it, contradicting that block's own comment promising the two "cannot disagree" -- both now use the shared resolution; (iii) the preflight resolved the plan PATH only when the status was missing, so a legacy manifest WITH a status but WITHOUT a `kind` had no path to fall back to -- the path is now resolved once, unconditionally.

### Task group 3: invert the pin, do not delete it

- [x] E-04 INVERT BOTH PINS rather than deleting either, following this repo's own precedent for a pinned decision a later phase deliberately reverses (`tests/test_wtiso_characterization.py`, VERIFIED at review to be exactly that pattern). PIN ONE, `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` (`:1530`), currently asserts the two types are distinct, that oc's has `kind` and agy's does not, and that each host gets its OWN type; it must now assert they are the SAME type, that the shared type carries `kind`, and that both hosts build it. Its docstring says "This plan may NOT unify them; that is a class (c) reconciliation for a later child" -- this IS that child, so cite this plan's id in the rewritten docstring. PIN TWO, FOUND AT REVIEW AND ABSENT FROM THE ORIGINAL PLAN: `tests/test_orchestrator_retirement.py:2470` asserts `"kind" not in agy_runipd.PlanRecord._fields` with the comment "that invariant is not this plan's to break". Invert that single assertion in place, cite `sy7uwh`, and leave the rest of the surrounding test (which proves agy's queue entry carries `kind` and derives `orchestrate`) UNTOUCHED, because it is the end-to-end guard F-3 makes mandatory and it must keep passing before and after.
  - Depends on: E-03
  - Expected outcome: BOTH pins still exist, both now guard the UNIFIED shape, each carrying a docstring or comment naming `sy7uwh` as the authorizing plan; and `test_the_agy_queue_entry_carries_kind`'s orchestrator derivation still green.
  - Execution state: performed
  - Execution note: BOTH PINS INVERTED IN PLACE, NEITHER DELETED. PIN ONE, `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests`: the class survives with a rewritten docstring that names `sy7uwh` as the authorizing plan, quotes the "This plan may NOT unify them" instruction it is discharging, and states WHY the override is legitimate (the premise dissolved). Its assertions now read `assertIs` on the two types, `kind` present for BOTH hosts, and both hosts building the SAME type out of `discover_plans`; the old `test_the_oc_path_still_populates_kind` became `test_BOTH_paths_populate_kind`, which is the payoff (`818uru` could only check oc, because agy's record had no such field). One test was ADDED, `test_no_field_was_lost_when_the_two_shapes_MERGED`, holding both pre-merge field sets as literals so a later change that drops a field fails HERE naming the field. PIN TWO, `tests/test_orchestrator_retirement.py`: exactly ONE assertion line changed, from `assertNotIn("kind", agy_runipd.PlanRecord._fields)` to `assertIn(...)` plus an identity check, with a comment citing `sy7uwh` and quoting the superseded "not this plan's to break" note. `git diff -U3` on that file shows the whole change is that one assertion, the `oc_runipd` import it needs, and documentation -- everything above the line is untouched, as required. `test_the_agy_queue_entry_carries_kind` PASSES BEFORE AND AFTER: verified at HEAD `85c14014` in a scratch worktree (`1 passed`) and at this working tree (`1 passed`).

- [x] E-05 Add `tests/test_rununify_record.py` proving the payoff and the risks are covered: one record type shared; `kind` populated from a real plan file on BOTH hosts; the ORCHESTRATOR-DETECTION path that motivated the whole coupling still working end to end on both hosts (an `approved` orchestrator derives `orchestrate`, not `execute`); a repo-wide AST scan for a re-forked `PlanRecord` that ALLOWLISTS `plans.py`'s unrelated type with its reason (E-02); an assertion that `_plan_kind`'s RECORD-SPLIT call site is gone; and, the case the original plan would have destroyed, a test that agy's LEGACY-MANIFEST FALLBACK still resolves `kind` from disk when the manifest lacks the key, so an approved orchestrator still derives `orchestrate` (F-7). That last case has NO coverage in the suite today, which is why deleting the helper looked free.
  - Depends on: E-03
  - Expected outcome: a suite that fails if the record splits again, if `kind` stops being populated, if orchestrator detection regresses on either host, or if the legacy-manifest fallback is removed.
  - Execution state: performed
  - Execution note: `tests/test_rununify_record.py` added, 24 tests in five classes, all green. Covers every case this item lists: ONE record type and ONE reader by OBJECT IDENTITY plus a REPO-WIDE AST scan across `agent_workflows/*.py` (not pairwise, per the parent's F10) that allowlists `plans.py`'s unrelated type with its reason; `kind` populated from a real plan file on BOTH hosts; END-TO-END orchestrator derivation on BOTH hosts through the real `discover_plans` -> `build_dynamic_manifest` -> `action_for` path, with the negative side (an ordinary child still deriving `execute`) asserted too so the unification cannot have made everything an orchestrator; an AST assertion that `_plan_kind`'s record-split call site is gone; and THE LEGACY-MANIFEST FALLBACK, which had NO coverage in the suite before this plan, asserted for BOTH hosts per OQ-03. THREE TESTS BEYOND THE ITEM'S LIST, each earning its place: the fallback must NOT fire when the manifest DOES carry `kind` (otherwise every run pays a file read per plan, which is the cost this plan removed); an unreadable plan file must fail to the SAFE direction (`None` -> `execute`, i.e. agent-handled, never silently retired); and the shipped `tools/ipdrunner/*-driver-manifest.json` files are checked to still match the fallback's premise, since the fallback exists for real files rather than a hypothetical. `NonVacuityControls` additionally exercises the guards' own logic in-process, and the REAL-SOURCE controls are recorded under V-05(b).

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

- Over-scope: none. Three source files and four test files, three symbols plus one call-site removal.
- Under-scope, CORRECTED AT EXECUTION 2026-09-17: a SEVENTH `Scope-Paths` entry was required and is
  added, `tests/test_orchestrator_probe_cache.py`. It was found by the `aw commit` scope gate REFUSING,
  which is the gate working as designed rather than a surprise, and it is a FOURTH instance of exactly
  the pattern F-8 established (a guard the plan did not know it would trip). That file holds TWO guards
  this change necessarily moves: `test_the_oc_to_agy_import_count_did_not_increase`, whose baseline
  DECREASES 56 -> 53 because the three readers now reach agy through `runner_shared` instead of through
  `oc_runipd`, re-measured and re-noted exactly as that assertion's own failure message instructs; and
  `test_no_new_module_level_first_party_import_in_runner_shared`, the import-graph guard that DECIDED the
  function-local `selectors` import (it was satisfied, NOT widened, and its allowlist is untouched). The
  edit to that file is therefore two baseline/annotation updates in guards this plan legitimately moves,
  with no assertion weakened.
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
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-16. The directive, given
  directly: "at the end of the SET, there should be one code base shared by the two runners that
  contains 100% of the otherwise redundant code that currently is duplicated between the two runners."
  That selects OPTION 2: GIVE THE FALLBACK TO BOTH HOSTS by lifting it into the shared manifest-reading
  path, so oc also re-reads `- Kind:` when a manifest omits it. Option 1 (preserve as agy-only) is
  refused because it deliberately leaves the two hosts disagreeing on a correctness gate, which is
  exactly the drift this Set exists to end, and it leaves the fallback duplicated-by-absence rather than
  shared. Option 3 (drop it from both) is refused because it knowingly reintroduces a defect a prior
  plan deliberately fixed, and nothing in the directive asks for capability to be removed.
  WHY OPTION 2 IS THE SAFE DIRECTION, restating the review's own measurement: today, given a
  hand-written manifest that omits the `kind` key and names an approved orchestrator, `aw agy run`
  re-reads the plan file, sees `- Kind: orchestrator` and correctly RETIRES it, while `aw oc run`
  derives `execute` and spends a paid agent turn executing a plan that authors no code. Both were
  measured at review. So oc is the DEFICIENT host here, and the Set's standing "oc is preferred" ruling
  does not apply, because this is precisely the A / NOT-A exception that ruling carves out. Unifying
  toward agy's behavior fixes a real oc defect; unifying toward oc's would install the defect in both.
  THE BEHAVIOR CHANGE TO oc IS HEREBY AUTHORIZED, which is the authorization the question asked for.
  The plan must still prove it end to end rather than assert it: V-03 already requires a demonstration
  that agy's legacy-manifest fallback still derives `orchestrate` for an approved orchestrator when the
  manifest omits `kind`, and per that item's own closing sentence it must now show oc doing the same.
  Add the missing test the review found (the fallback is uncovered today), so the shared path is pinned
  for both hosts rather than for neither.
  THE REVIEWER'S ANALYSIS BELOW IS PRESERVED; its recommendation is ratified.
  --- original analysis, recommendation now ratified ---
  NOT RESOLVABLE FROM REPOSITORY EVIDENCE. The evidence settles that
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

- [x] V-01 validates E-01
  - Required evidence: pasted proof of all three premises (agy consumes `kind` via the shared `action_for`; agy obtains it by re-reading the file through `_plan_kind`; nothing depends on agy's record lacking the field), or the explicit refusal. For premise 3 specifically, NAME BOTH asserting tests (`tests/test_runner_shared.py:1550` and `tests/test_orchestrator_retirement.py:2470`) rather than reporting a clean pass, since a test-asserted invariant is something to invert deliberately.
  - Observed evidence: measured at HEAD `85c14014` BEFORE any edit, via `python3` against the unmodified tree:

    ```text
    === E-01 PREMISE 1: agy CONSUMES `kind` through the shared `action_for` ===
    agy.action_for is runner_shared.action_for -> True
    oc.action_for  is runner_shared.action_for -> True
    action_for('orchestrator','approved')      -> orchestrate
    action_for(None,'approved')                -> execute
    action_for reads `kind`: True

    === E-01 PREMISE 2: agy obtains `kind` by RE-READING the plan file via `_plan_kind` ===
    oc_runipd: _plan_kind def lines=[] call lines=[]
    agy_runipd: _plan_kind def lines=[1735] call lines=[1768, 2335]
    agy build_dynamic_manifest kind expression: ['"kind": _plan_kind(rec.path),']
    oc  build_dynamic_manifest kind expression: ['"kind": rec.kind,']

    === E-01 PREMISE 3: NOTHING REQUIRES the field's absence, but TWO TESTS ASSERT IT ===
    oc  PlanRecord._fields: ('id6', 'setid', 'status', 'order', 'path', 'rel_path', 'dependencies', 'kind', 'dependency_error', 'from_backlog')
    agy PlanRecord._fields: ('id6', 'setid', 'status', 'order', 'path', 'rel_path', 'dependencies', 'dependency_error', 'from_backlog')
    oc is a strict SUPERSET of agy, differing in exactly: {'kind'}
    the two types are distinct objects: True
    ASSERTING TEST: tests/test_runner_shared.py:1666: self.assertNotIn("kind", agy_runipd.PlanRecord._fields)
    ASSERTING TEST: tests/test_orchestrator_retirement.py:2559: self.assertNotIn("kind", agy_runipd.PlanRecord._fields)
    ```

    ALL THREE PREMISES CONFIRM, so this item does NOT refuse and the override proceeds. PREMISE 3 IS REPORTED AS THE HONEST NUANCE the item demands, NOT as a clean pass: no code path REQUIRES the field's absence, and BOTH asserting tests are named above. Their line numbers had DRIFTED from the review's citations (`:1550` -> `:1666`, `:2470` -> `:2559`) through intervening work, as had `_plan_kind`'s (`:1693`/`:2260` -> `:1768`/`:2335`); the identities are unchanged and both tests were inverted deliberately by E-04.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.PlanRecord is agy_runipd.PlanRecord` returning True, the shared `_fields` tuple, and a field-by-field comparison against BOTH pre-change types showing nothing was lost. PLUS confirmation that `agent_workflows/plans.py:90`'s unrelated `PlanRecord` is UNCHANGED and is allowlisted in the scan with its reason (F-10).
  - Observed evidence: measured against the changed tree with `python3`:

    ```text
    === V-02: ONE record type, nothing lost, plans.py untouched ===
    oc_runipd.PlanRecord is agy_runipd.PlanRecord -> True
    ... and both are runner_shared.PlanRecord     -> True
    shared _fields: ('id6', 'setid', 'status', 'order', 'path', 'rel_path', 'dependencies', 'kind', 'dependency_error', 'from_backlog')

    FIELD-BY-FIELD against BOTH pre-change types:
      oc  pre-change id6               present in shared: True
      oc  pre-change setid             present in shared: True
      oc  pre-change status            present in shared: True
      oc  pre-change order             present in shared: True
      oc  pre-change path              present in shared: True
      oc  pre-change rel_path          present in shared: True
      oc  pre-change dependencies      present in shared: True
      oc  pre-change kind              present in shared: True
      oc  pre-change dependency_error  present in shared: True
      oc  pre-change from_backlog      present in shared: True
      agy pre-change id6               present in shared: True
      agy pre-change setid             present in shared: True
      agy pre-change status            present in shared: True
      agy pre-change order             present in shared: True
      agy pre-change path              present in shared: True
      agy pre-change rel_path          present in shared: True
      agy pre-change dependencies      present in shared: True
      agy pre-change dependency_error  present in shared: True
      agy pre-change from_backlog      present in shared: True
    nothing lost: True
    nothing invented: True

    plans.py's UNRELATED PlanRecord is UNCHANGED and is a different object:
      plans.PlanRecord._fields = ('path', 'area', 'disposition', 'status', 'set_id', 'order')
      plans.PlanRecord is runner_shared.PlanRecord -> False
      allowlisted in the scan with its reason:
        ('plans.py', 'PlanRecord') -> an UNRELATED plans-tree inventory row (path/area/disposition/status/set_id/order) with no importers of that name; a name collision, not a re-fork of the runners' record
    ```

    `plans.py` UNCHANGED, proven by git rather than by inspection: `git diff HEAD -- agent_workflows/plans.py` produces ZERO lines of output.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted identity results for `parse_plan_file` and `build_dynamic_manifest`; evidence that all SIX readers (`_PLAN_FILENAME_RE`, `_read_kind`, `_read_item_dependencies`, `_read_from_backlog`, `_read_id`, `_read_status`) resolve in `runner_shared` (F-9); an AST scan showing `_plan_kind`'s RECORD-SPLIT call site at `agy_runipd.py:1693` is gone; a rendered manifest entry from BOTH hosts carrying the correct `kind` for an orchestrator plan; AND, the case the original plan would have destroyed, a demonstration that agy's legacy-manifest fallback STILL derives `orchestrate` for an approved orchestrator when the manifest omits `kind` (F-7). If the maintainer chose OQ-03 option 2, show oc doing the same.
  - Observed evidence: all five parts measured against the changed tree with `python3`:

    ```text
    === V-03 (a): ONE parse_plan_file and ONE build_dynamic_manifest ===
      oc.parse_plan_file is agy.parse_plan_file -> True ; is runner_shared.parse_plan_file -> True
      oc.build_dynamic_manifest is agy.build_dynamic_manifest -> True ; is runner_shared.build_dynamic_manifest -> True

    === V-03 (b): all SIX readers resolve in runner_shared (F-9) ===
      runner_shared._PLAN_FILENAME_RE          present: True
      runner_shared._read_kind                 present: True
      runner_shared._read_item_dependencies    present: True
      runner_shared._read_from_backlog         present: True
      _read_id/_read_status resolve via function-local imports inside parse_plan_file:
        from agent_workflows.selectors import read_front_matter_id as _read_id
        from agent_workflows.selectors import read_front_matter_status as _read_status

    === V-03 (c): _plan_kind's RECORD-SPLIT call site at agy_runipd.py:1693 is GONE (AST) ===
      oc_runipd: _plan_kind defs=[] calls=[]
      agy_runipd: _plan_kind defs=[] calls=[]

    === V-03 (d): a rendered manifest entry from BOTH hosts carries the correct kind ===
      oc_runipd: entry={"set": "kindset", "status": "approved", "order": 0, "kind": "orchestrator"} action_for -> orchestrate
      agy_runipd: entry={"set": "kindset", "status": "approved", "order": 0, "kind": "orchestrator"} action_for -> orchestrate

    === V-03 (e): THE LEGACY-MANIFEST FALLBACK, on BOTH hosts (F-7 / OQ-03 option 2) ===
      legacy manifest entry has a 'kind' key: False
      oc_runipd: resolve_manifest_kind -> 'orchestrator' ; action_for -> orchestrate
      agy_runipd: resolve_manifest_kind -> 'orchestrator' ; action_for -> orchestrate
      both hosts agree: True
    ```

    (e) IS THE ITEM'S CLOSING REQUIREMENT DISCHARGED: the maintainer DID choose OQ-03 option 2, and oc is shown doing the same as agy. For contrast, the SAME probe run at HEAD `85c14014` before any edit measured the disagreement this fixes: `agy ... -> orchestrate` against `oc ... -> execute`, i.e. oc would have AGENT-EXECUTED an approved orchestrator named by a legacy manifest.

    NOTE ON (b), stated because it deviates from the item's wording: `_read_id`/`_read_status` are reachable in `runner_shared` through FUNCTION-LOCAL imports, not the module-level import the item anticipated. A module-level `selectors` import fails a deliberate import-graph guard (`tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate::test_no_new_module_level_first_party_import_in_runner_shared`) that allows only `render_stream` and `runner_profiles`. The guard was SATISFIED, not weakened: no allowlist was widened, and the function-local form is the module's own existing convention for `ipd_lint`/`ipd_schema`. Measured justification: five of the twelve non-runner modules importing `runner_shared` do not currently reach `selectors` at all, so a module-level import would newly tax them.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: BOTH inverted pins pasted, each showing it now asserts the unified shape and each citing this plan, plus their green runs. PLUS `test_the_agy_queue_entry_carries_kind` shown green with only its single record-shape assertion changed, since it is the end-to-end guard F-3 makes mandatory and rewriting it would remove the protection this plan most needs.
  - Observed evidence: PIN ONE, `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests`, now asserting the UNIFIED shape and citing this plan in its docstring:

    ```python
    class DiscoverPlansRecordTypeTests(unittest.TestCase):
        """PIN ONE OF TWO, INVERTED BY `sy7uwh`: the record types are now the SAME, deliberately.
        ...
        rununify 06 (`sy7uwh`) IS THAT LATER CHILD, authorized by the maintainer's 2026-09-14
        unify-toward-oc ruling, so the assertions are INVERTED IN PLACE rather than deleted ...

        def test_the_two_PlanRecord_types_are_now_ONE_shared_type(self):
            self.assertIs(oc_runipd.PlanRecord, agy_runipd.PlanRecord)
            self.assertIs(oc_runipd.PlanRecord, runner_shared.PlanRecord)
            self.assertIn("kind", runner_shared.PlanRecord._fields)
    ```

    PIN TWO, `tests/test_orchestrator_retirement.py`, the single assertion inverted in place and citing `sy7uwh`:

    ```python
    # PIN TWO OF TWO, INVERTED BY rununify 06 (`sy7uwh`), which IS the "later child" that
    # `818uru` deferred the unification to. This line used to read
    # `assertNotIn("kind", agy_runipd.PlanRecord._fields)` with the comment "`818uru` pinned the
    # two as distinct and that invariant is not this plan's to break" ...
    self.assertIn("kind", agy_runipd.PlanRecord._fields)
    self.assertIs(agy_runipd.PlanRecord, oc_runipd.PlanRecord)
    ```

    BOTH GREEN:

    ```text
    tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::test_BOTH_paths_populate_kind PASSED [ 25%]
    tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::test_no_field_was_lost_when_the_two_shapes_MERGED PASSED [ 50%]
    tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::test_the_two_PlanRecord_types_are_now_ONE_shared_type PASSED [ 75%]
    tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::test_each_runner_now_gets_the_SAME_record_type PASSED [100%]

    ====================== 4 passed, 131 deselected in 0.25s =======================

    tests/test_orchestrator_retirement.py::TheActionDecisionIsSHAREDCode::test_the_agy_queue_entry_carries_kind PASSED [100%]

    ====================== 1 passed, 136 deselected in 0.26s =======================
    ```

    ONLY ITS SINGLE RECORD-SHAPE ASSERTION CHANGED, proven by the full `git diff -U3` of that file being confined to (i) that one assertion, (ii) the `oc_runipd` import the new identity check needs, and (iii) comments/docstring. Everything above the line -- the real `discover_plans` + `build_dynamic_manifest` path, the `entry["kind"] == "orchestrator"` check and the `action_for(...) == "orchestrate"` derivation -- is byte-identical.

    GREEN BEFORE AND AFTER, which is the property that makes it a usable guard: run at HEAD `85c14014` in a throwaway `git worktree` (`1 passed, 136 deselected in 0.75s`) and again at this working tree (`1 passed, 136 deselected in 0.26s`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_record.py -o addopts=""` green, including the end-to-end orchestrator-derivation case on both hosts and the legacy-manifest fallback case. (b) BOTH non-vacuity controls from Required tests item 4: with `kind` dropped, the new suite and the inverted class FAIL naming orchestrator detection; with `_plan_kind` deleted entirely, the legacy-manifest test FAILS naming `execute` where `orchestrate` was required; both restored green. (c) The repo-wide `PlanRecord` scan output showing exactly one runner-owned definition plus the allowlisted `plans.py` entry. (d) Bare `python3 -m pytest` at or above 7308 passed with no new failure judged against F-13's named flake, plus the orchestrator, shim and dependency suites named in Required tests items 6 to 8 green.
  - Observed evidence: (a) THE NEW SUITE GREEN:

    ```text
    $ python3 -m pytest tests/test_rununify_record.py -o addopts=""
    collected 24 items

    tests/test_rununify_record.py ........................                   [100%]

    ============================== 24 passed in 1.45s ==============================
    ```

    (b) BOTH NON-VACUITY CONTROLS, performed against the REAL SHIPPED SOURCE (edited, run, restored) rather than only in-process, because a control that never touches the code it guards proves less.

    CONTROL 1, `kind` dropped. The FIRST attempt renamed the record field, which raised `TypeError: PlanRecord.__new__() got an unexpected keyword argument 'kind'` -- a LOUD failure, and therefore the wrong control, because F-3's whole point is that the real failure is SILENT. Redone as the silent form (`kind = None` in `parse_plan_file`, so nothing raises), which is exactly what a shared constructor dropping the field would do:

    ```text
    >                   self.assertEqual(
                            mod.action_for(entry["kind"], entry["status"]),
                            "orchestrate",
                            "an approved orchestrator must NOT be agent-executed; deriving "
                            "`execute` here spends a paid agent turn on a plan that authors no code",
                        )
    E                   AssertionError: 'execute' != 'orchestrate'
    E                   - execute
    E                   + orchestrate
    E                    : an approved orchestrator must NOT be agent-executed; deriving `execute` here spends a paid agent turn on a plan that authors no code

    FAILED tests/test_rununify_record.py::OrchestratorDetectionStillWorksEndToEnd::test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts
    ```

    And the INVERTED CLASS catches the same silent drop, as this item requires:

    ```text
    >                   self.assertEqual(record.kind, "child")
    E                   AssertionError: None != 'child'

    FAILED tests/test_runner_shared.py::DiscoverPlansRecordTypeTests::test_BOTH_paths_populate_kind
    ================= 1 failed, 3 passed, 131 deselected in 0.26s ==================
    ```

    Pin two also fails under it (`FAILED tests/test_orchestrator_retirement.py::TheActionDecisionIsSHAREDCode::test_the_agy_queue_entry_carries_kind`).

    CONTROL 2, the fallback deleted (`resolve_manifest_kind` degraded to the bare `entry.get("kind")` pass-through that oc had before this plan):

    ```text
    E                   AssertionError: 'execute' != 'orchestrate'
    E                   - execute
    E                   + orchestrate
    E                    : oc_runipd derived the wrong ACTION for an approved orchestrator named by a LEGACY manifest that omits the `kind` key. `execute` here AGENT-EXECUTES a plan that authors no code, reintroducing the exact defect orchretire-03 (`pgq326`) fixed; the cause is a missing manifest-then-file fallback (`plan_kind_from_file`)

    FAILED tests/test_rununify_record.py::TheLegacyManifestFallbackWorksOnBothHosts::test_a_manifest_WITHOUT_kind_still_derives_orchestrate_on_BOTH_hosts
    ```

    THE CONTROL IMPROVED THE TEST, which is worth recording as a finding rather than hiding. On its first run the test failed at `None != 'orchestrator'` -- correct, but it stopped BEFORE the statement naming the consequence, and this V-item requires the failure to name `execute` where `orchestrate` was required. The assertion order was therefore inverted (derivation first, kind second, as corroboration) so the control reports the consequence, which is the output pasted above.

    BOTH RESTORED GREEN:

    ```text
    tests/test_rununify_record.py ........................                   [100%]
    ============================== 24 passed in 1.52s ==============================

    tests/test_rununify_record.py ........................                   [ 85%]
    tests/test_runner_shared.py ....                                         [100%]
    ====================== 28 passed, 131 deselected in 1.61s ======================
    ```

    (c) THE REPO-WIDE SCAN, over all of `agent_workflows/*.py` rather than pairwise (the parent's F10):

    ```text
    === REPO-WIDE AST scan over agent_workflows/*.py (not pairwise) ===
    PlanRecord                 ['plans.py:90  <-- ALLOWLISTED name collision', 'runner_shared.py:3282']
    parse_plan_file            ['runner_shared.py:3318']
    build_dynamic_manifest     ['runner_shared.py:3455']
    _read_kind                 ['runner_shared.py:3216']
    _read_item_dependencies    ['runner_shared.py:3224']
    _read_from_backlog         ['runner_shared.py:3259']
    _PLAN_FILENAME_RE          ['runner_shared.py:194']

    Runner-owned definitions counted (allowlist excluded): exactly 1 each, all in runner_shared.py
    ```

    (d) BARE SUITE, run as `python3 -m pytest` with no added flags:

    ```text
    1 failed, 7537 passed, 3 skipped, 2 xfailed in 97.85s (0:01:37)
    FAILED tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130
    ```

    THE ONE FAILURE IS F-13's NAMED FLAKE, and it is judged rather than assumed: it is the exact test F-13 names, it fails on a `subprocess.TimeoutExpired` under parallel load, and its file passes in isolation -- `47 passed in 2.75s` for the whole file, `7 passed` for the class alone.

    THE BASELINE IS CORRECTED, and this is a FINDING against F-13 rather than a pass over it. F-13 recorded `1 failed, 7308 passed` at the 2026-09-16 review. Measured at THIS execution HEAD `85c14014` in a throwaway `git worktree` (so no edit of mine could influence it): **`7513 passed, 3 skipped, 2 xfailed`, ZERO failures**. So the true baseline is 205 tests higher than F-13 states and the flake did NOT reproduce there, meaning F-13's count is stale and its "one known failure" is a flake rather than a standing failure. Against the true baseline this change is `7513 -> 7537`, i.e. exactly `+24`, matching the 24 tests E-05 adds and confirming NO pre-existing test was lost.

    THE NAMED SUITES (Required tests items 5 to 8) GREEN, run together:

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py \
        tests/test_orchestrator_retirement.py tests/test_orchestrator_probe_cache.py \
        tests/test_oc_runipd_shim.py tests/test_agy_runipd_shim.py \
        tests/test_runner_item_dependencies.py tests/test_runner_backlog_close.py \
        tests/test_runner_shared.py tests/test_runner_refork_guard.py \
        tests/test_rununify_lift.py tests/test_rununify_conflicts.py tests/test_rununify_record.py
    789 passed in 24.23s
    ```

    A SEVENTH CONSEQUENCE FOUND ONLY AT COMMIT TIME, recorded because it is a real trap for the next
    plan that moves a function out of a runner. Once `parse_plan_file` moved, neither host CALLED
    `_read_id` any more, so the `ruff --fix` pre-commit hook deleted that import as unused -- and that
    silently broke a contract, because `tests/test_runner_refork_guard.py` requires BOTH runners to keep
    EXPOSING `_read_id` bound to `selectors.read_front_matter_id` (measured: two tests failed with
    `oc_runipd._read_id is MISSING`). The `as <same-name>` re-export form that this repo relies on
    elsewhere was NOT sufficient (ruff stripped it again on the next hook run) and neither module's
    `__all__` lists the private readers, so the import now carries an explicit `# noqa: F401` naming the
    test that requires it. THE LESSON GENERALIZES: moving a symbol out of a runner can make an unrelated
    RE-EXPORT look unused, and the hook's auto-fix will then remove a binding another module's contract
    depends on. Two further mechanical consequences were handled in the same pass: the new deep-in-file
    import blocks tripped `E402` and were hoisted into each host's top-of-file shared-import block, and
    the hook reformatted `agent_workflows/runner_shared.py`'s one PRE-EXISTING format drift, which was
    restored by hand so this change does not sweep in a line it does not own (filed as backlog
    `hdxp39`). Re-verified after each: `pre-commit run ruff` and `pre-commit run ruff-format` both
    `Passed` on all seven changed files, and the bare suite still reports `7537 passed`.

    ENVIRONMENT NOTE, recorded because it changes how the numbers above must be read. This lane runs with `AW_EXECUTION_ROLE=worker` exported, which makes `aw ipd begin` correctly REFUSE (`AW-LIFECYCLE-ROLE-001`) and consequently fails 32 tests that shell out to it -- including the whole of `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role`, whose assertion is literally `assertNotEqual(os.environ.get("AW_EXECUTION_ROLE"), "worker")`. Those 32 are an ARTIFACT OF THE LANE, not of this change: they fail identically at HEAD. Every count above was therefore taken with `env -u AW_EXECUTION_ROLE`, and the same unset was applied to the HEAD baseline, so baseline and result are measured the same way.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. EVALUATED AT REVIEW 2026-09-16 rather than inherited. The five items
  are one concern each and the revision added no item, only obligations inside existing ones: E-03 gained
  the six-reader prerequisite and the partial `_plan_kind` removal, E-04 gained the second pin, E-05
  gained two cases. E-03 is now the densest item and is the one to watch, but its parts are inseparable:
  the readers must move for the function to move, and the call-site surgery is inside the same two
  functions being unified, verified by one `V-*`.

OQ-03 WAS OPEN AND `Blocking: yes` WHEN THIS PARAGRAPH WAS WRITTEN. IT IS NOW `Status: resolved`: the
maintainer answered it on 2026-09-16 in favor of OPTION 2 (give the legacy-manifest fallback to BOTH
hosts), and E-03 implemented that answer -- `runner_shared.plan_kind_from_file` /
`resolve_manifest_kind` are called by both hosts, so oc gained the fallback it lacked and the two hosts
no longer disagree about that correctness gate. `aw ipd lint` reports this plan `conforming`.

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
