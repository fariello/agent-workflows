# IPD: Unify the plan record type and its two readers, overriding the 818uru split

- Date: 2026-09-15
- Kind: child
- Concern: The two runners build DIFFERENT `PlanRecord` NamedTuples (oc's carries `kind`, agy's does not), which forces `parse_plan_file` and `build_dynamic_manifest` to stay forked and forces agy to re-read `- Kind:` from disk for information oc already has in hand.
- Scope: Collapse the two record types into one in `runner_shared.py` and unify their two readers. This DELIBERATELY OVERRIDES the earlier decision recorded by this Set's own child `818uru`, which pinned the two types as distinct and wrote a test asserting it; that test must be inverted, not deleted.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_rununify_record.py
- Item-Dependencies: executed:i3d6ml
- Status: to-review
- Set: rununify
- Order: 6
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: sy7uwh
- From-Backlog: alw22r

## Workflow history
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored after confirming that the reason 818uru pinned the split has since dissolved; see F-2.

## Goal

Make `discover_plans` build ONE record type for both hosts, so `parse_plan_file` and
`build_dynamic_manifest` stop being forked and agy stops re-reading a field from disk that the record
should already carry. This is the last structural blocker before the five large host-shaped functions.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-establish that the override is warranted

- [ ] E-01 CONFIRM AT EXECUTION HEAD that the reason `818uru` pinned the split has genuinely dissolved, and refuse to proceed if it has not. Specifically: show that agy now DOES consume `kind` (through the shared `action_for`, which reads it to detect an orchestrator), that agy currently obtains it by re-reading the plan file via its own `_plan_kind` helper rather than from the record, and that no code path depends on agy's record LACKING the field. If any of those is false, stop and report rather than overriding a decision whose premise still holds.
  - Depends on: none
  - Expected outcome: pasted evidence for each of the three points, or an explicit refusal naming which premise still holds.
  - Execution state: pending

### Task group 2: the unification

- [ ] E-02 Define ONE `PlanRecord` in `runner_shared.py`, taking oc's field set (it is a strict superset: it carries `kind` where agy's does not) per the maintainer's 2026-09-14 ruling, and have both hosts import that name. Keep every existing field and its meaning; this is a merge of two shapes, not a redesign of the record.
  - Depends on: E-01
  - Expected outcome: `oc_runipd.PlanRecord is agy_runipd.PlanRecord` is True, the shared type carries `kind`, and no field present today on either side is lost.
  - Execution state: pending

- [ ] E-03 Unify `parse_plan_file` on the shared record, using oc's version (it already reads `- Kind:` through the shared `_read_kind`), and DELETE agy's `_plan_kind` disk re-read along with its call in `build_dynamic_manifest`, which then takes `rec.kind` exactly as oc's does. Removing that helper is the actual payoff of this plan: it exists solely to work around the record split.
  - Depends on: E-02
  - Expected outcome: one `parse_plan_file`, one `build_dynamic_manifest`, `_plan_kind` deleted, and the manifest still carries a correct `kind` for an orchestrator on BOTH hosts.
  - Execution state: pending

### Task group 3: invert the pin, do not delete it

- [ ] E-04 INVERT `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` rather than deleting it, following this repo's own precedent for a pinned decision that a later phase deliberately reverses (`tests/test_wtiso_characterization.py`). The class currently asserts the two types are distinct, that oc's has `kind` and agy's does not, and that each host gets its OWN type. It must now assert they are the SAME type, that the shared type carries `kind`, and that both hosts build it. Its docstring says "This plan may NOT unify them; that is a class (c) reconciliation for a later child" -- this IS that child, so cite this plan's id in the rewritten docstring so the reversal is traceable.
  - Depends on: E-03
  - Expected outcome: the class still exists, still guards the record shape, and now guards the UNIFIED shape with a docstring naming `sy7uwh` as the authorizing plan.
  - Execution state: pending

- [ ] E-05 Add `tests/test_rununify_record.py` proving the payoff and the risk are both covered: one record type shared, `kind` populated from a real plan file on BOTH hosts, `_plan_kind` gone (AST scan, so a re-fork is caught), and the ORCHESTRATOR-DETECTION path that motivated the whole coupling still works end to end on both hosts (an `approved` orchestrator derives `orchestrate`, not `execute`).
  - Depends on: E-03
  - Expected outcome: a suite that fails if the record splits again, if `kind` stops being populated, or if orchestrator detection regresses on either host.
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
  removes, and that the parsing itself already delegates to the shared `_read_kind`.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | `tests/test_runner_shared.py:1530` | An earlier child of THIS Set (`818uru`) deliberately pinned the two record types as distinct and wrote a test forbidding unification, explicitly deferring it to "a later child". Overriding that is legitimate only because this plan IS that child, and the override must be visible in the test rather than accomplished by deleting it. |
| F-2 | HIGH | `agy_runipd.py:158`, `:354`, `:1660` | THE PREMISE OF THE SPLIT HAS DISSOLVED. When `818uru` pinned it, agy had no use for `kind`. agy now imports the shared `action_for`, which READS `kind` to detect an orchestrator, and agy supplies it by re-reading the plan file through its own `_plan_kind` helper. So the split now costs a redundant disk read and buys nothing. |
| F-3 | HIGH | `tests/test_runner_shared.py:1568` | The existing suite already warns that a shared constructor dropping `kind` "would silently disable orchestrator detection". That is the precise failure mode of this change, and it is type-shaped and silent, so E-05 must assert the orchestrator DERIVATION end to end and not merely that a field exists. |
| F-4 | MED | `agy_runipd.py:1660` | `_plan_kind`'s own docstring names the record split as its reason for existing and calls unifying the two types "a later reconciliation". Deleting the helper is therefore the intended outcome, not collateral damage. |
| F-5 | MED | `build_dynamic_manifest` | The two versions differ in exactly ONE expression: `'kind': rec.kind` versus `'kind': _plan_kind(rec.path)`. Once the record is unified this symbol becomes byte-identical, so it collapses for free rather than needing its own reconciliation. |
| F-6 | LOW | `oc_runipd.py:2689` | oc already writes `rec.kind` into the manifest, so the shared form is the one already in production on the oc side; agy's is the deviation being removed. |

## Proposed changes (ordered, validatable)

1. Re-confirm the override is warranted at execution HEAD, and refuse if it is not (E-01).
2. One `PlanRecord` in `runner_shared`, oc's superset field set (E-02).
3. One `parse_plan_file` and one `build_dynamic_manifest`; delete `_plan_kind` (E-03).
4. Invert the pinning test, citing this plan (E-04).
5. Add the payoff-and-risk suite, including end-to-end orchestrator detection (E-05).

## Deferred / out of scope (with reason)

- The 48 no-disagreement symbols (child 03, `i3d6ml`, this plan's dependency), the 8 host-string symbols
  (child 04, `tx6q0h`), and the two behavior conflicts (child 05, `ct4w0a`).
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11. Several
  of them CONSUME `PlanRecord`, which is why this plan is ordered before them: unifying the record first
  removes a variable from each of those five splits.
- REDESIGNING the record (renaming fields, adding new ones, changing types). This is a merge of two
  existing shapes and nothing more; a field nobody reads today must not appear.

## Scope check

- Over-scope: none. Three source files and two test files, three symbols plus one deleted helper.
- Under-scope: this plan does not unify `action_for`/`determine_action` naming, which child 03 or 04
  settles; it only relies on whichever name survives.

## Required tests / validation

1. `tests/test_rununify_record.py` (new): one shared record type; `kind` populated from a real plan file
   on BOTH hosts; `_plan_kind` absent by AST scan; and END-TO-END orchestrator detection on both hosts
   (an `approved` orchestrator derives `orchestrate`).
2. `tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` INVERTED and green, with a docstring
   naming this plan as the authorizing reversal.
3. NON-VACUITY: drop `kind` from the shared record and show BOTH the new suite and the inverted class
   FAIL, naming orchestrator detection; then restore. F-3 makes this control mandatory, because the
   failure mode is silent.
4. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green.
5. `tests/test_orchestrator_retirement.py` and `tests/test_orchestrator_probe_cache.py` green, named
   because both reason about orchestrators and would be affected by a `kind` regression.
6. Bare `python3 -m pytest`, summary pasted, no new failure against the baseline at execution time.

## Spec / documentation sync

No `.spec.md` change. `PlanRecord` is an internal type; no spec names it or its fields. The decision
being overridden lives in a TEST and in `818uru`'s plan record, not in a spec, which is why E-04's
inversion plus this plan's own history entry is the complete and correct paper trail.

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted proof of all three premises (agy consumes `kind` via the shared `action_for`; agy obtains it by re-reading the file through `_plan_kind`; nothing depends on agy's record lacking the field), or the explicit refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.PlanRecord is agy_runipd.PlanRecord` returning True, the shared `_fields` tuple, and a field-by-field comparison against BOTH pre-change types showing nothing was lost.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted identity results for `parse_plan_file` and `build_dynamic_manifest`; an AST scan showing `_plan_kind` is gone; and a rendered manifest entry from BOTH hosts carrying the correct `kind` for an orchestrator plan.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the inverted test class pasted, showing it now asserts the unified shape and names this plan in its docstring, plus its green run.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THREE parts, all pasted. (a) `python3 -m pytest tests/test_rununify_record.py -o addopts=""` green, including the end-to-end orchestrator-derivation case on both hosts. (b) The NON-VACUITY control from Required tests item 3: with `kind` dropped, both the new suite and the inverted class FAIL naming orchestrator detection, then restored green. (c) Bare `python3 -m pytest` with no new failure, plus the two named orchestrator suites green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS: E-01, because this plan overrides a deliberate earlier decision and
must refuse if that decision's premise still holds; and V-05(b), because the failure mode here is
SILENT and type-shaped (a dropped `kind` disables orchestrator detection without crashing), so a control
that cannot fail would leave the whole change unproven.
