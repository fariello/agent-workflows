# IPD: Restore check.scope-drift behavioral coverage on a shared lane-arranging fixture so the vacuous-pass shape cannot be rewritten

- Date: 2026-09-29
- Kind: child
- Concern: THE GUARD THE BACKLOG ITEM ASKED TO PROTECT NO LONGER EXISTS, AND THE RULE IS NOW WHOLLY UNCOVERED. Backlog `caf5ed` was filed 2026-09-22 against six scope-drift test arrangements that had just been repaired to allocate a real lane, asking for something to stop the NEXT one being written the old way. Two days later commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted all four files carrying them: `tests/test_check_engine_receipt_liveness.py`, `tests/test_event_derived_lifecycle.py`, `tests/test_phase4_hooks.py`, `tests/test_finalize_scope_ownership.py` (verified absent from the working tree; recoverable at `19313eed^`). So the item's premise has inverted: there is no longer a fixture pattern to guard, there is a LIVE RULE WITH NO BEHAVIORAL TEST. MEASURED THIS TURN, not inferred: inserting an unconditional `return drift` at the top of `check_engine.check_scope_drift`, so the rule reports NOTHING FOR ANY INPUT, leaves the full bare suite GREEN at `3246 passed, 2 skipped`, and leaves the `slow`/`livecorpus` selection at its unchanged pre-existing `3 failed, 204 passed` (identical failures with and without the mutation, so unrelated). The only surviving mention of the rule is `tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_check_commit_invariants_composition`, which `mock.patch`es `agent_workflows.check_engine.check_scope_drift` to return a hand-built sentinel and therefore asserts COMPOSITION while deliberately never exercising the rule; that is why it survived the mutation. The exposure is not theoretical: the rule's own docstring records that a wrong-tree comparison once produced 350 findings across six plans where the lane-correct measurement yields 9/5/1/0, so a silent regression here returns either that noise or nothing at all.
- Scope: Restore the DELETED BEHAVIORAL COVERAGE of `check_engine.check_scope_drift` as one new test module, arranged through ONE shared fixture helper added to `tests/support.py` so the lane cannot be forgotten by the next author, and make every silent assertion carry a paired firing positive control so a rule that reported nothing could not satisfy the module. This is the backlog item's CANDIDATE DIRECTION (1) (a shared arranging helper) combined with its DIRECTION (3) (the positive-control convention), and it deliberately DECLINES its DIRECTION (2) (a meta-test asserting each file allocates a lane) because that is a code-structure pin `GUIDING_PRINCIPLES.md` P16 prohibits outright; the reasoning is recorded in Findings rather than left implicit. EXCLUDES restoring the three unrelated halves of the deleted files (receipt liveness, event-derived transition validity, and finalize ownership attribution), which lost their own coverage in the same commit but are separate surfaces with separate claims and belong to the general trim audit `xvp5vx`; this plan restores only what the drift advisory itself asserts. EXCLUDES any change to `check_engine.check_scope_drift` or to `worktree_lease`: the rule's behavior is the SUBJECT here and must not move while coverage is being written around it.
- Scope-Paths: tests/support.py, tests/test_check_scope_drift.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: caf5ed
- Set: caf5ed
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: qqg41f

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `caf5ed`. THE ITEM'S PREMISE WAS FALSIFIED AND THE PLAN SAYS SO RATHER THAN EXECUTING IT LITERALLY: the item asks for a guard on six fixtures that commit `19313eed` deleted two days after it was filed, so a plan that "repaired the pattern" would be guarding nothing. The measurement that redirected it is recorded in Concern and reproduced in V-01: the rule now passes the suite while returning nothing for every input. Three choices were made against evidence and are contestable in Findings: the item's candidate direction (2) is REFUSED as a P16-prohibited code-structure pin; the helper goes in `tests/support.py` on the precedent of `support.ready_plan_text`, which exists for exactly this reason ("rather than ... twenty-one hand-maintained copies"); and the fixture resolves the lane through the production allocator so it cannot drift from where the rule looks.
- 2026-09-29 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make `check_engine.check_scope_drift` provably covered again, and make the next author who arranges a
scope-drift case get the lane for free instead of having to remember it.

Two properties, both currently absent. FIRST, breaking the rule must break the suite: today it can
return nothing for every input and nothing fails. SECOND, an arrangement that silently stops measuring
must be visible: every assertion of SILENCE is paired with an arrangement that FIRES from the same
fixture, so a rule that had stopped working entirely fails the firing row rather than passing all the
silent ones.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared arranging fixture

- [ ] E-01 ADD ONE SHARED SCOPE-DRIFT ARRANGER TO `tests/support.py` THAT ALLOCATES THE LANE ITSELF, SO A CALLER CANNOT FORGET IT. Add a function (suggested `scope_drift_repo`) that builds a complete drift subject in one call and RETURNS BOTH the repo root and the lane path, because the caller needs the lane to place its change and the rule needs the root. The ONE deliverable is that arranging function, and the steps below are its body rather than separate concerns. It `git init`s a repo by reusing `support.init_repo` (the established helper) rather than re-implementing it. It writes a `.gitignore` containing BOTH `.aw/state/` and `.aw/worktrees/`, because those are the two runtime trees `check_scope_drift` defensively excludes and an ungitignored lane directory would otherwise appear as a changed path. It writes a plan under `.aw/records/plans/pending/` carrying a real `- Id:` and a parameterized `- Scope-Paths:`, commits, and captures HEAD as the frozen base. It writes the begin receipt at that base through the PRODUCTION path helper `ipd_lifecycle.receipt_path_for` rather than a hand-built `.aw/state/ipd-lifecycle/<id6>.receipt.json` string, so the fixture cannot drift from where `ipd_lifecycle.read_receipt` looks. Finally it allocates the lane via `worktree_lease.allocate_worktree(root, plan_id, base_commit=base)`. THE `base_commit=base` ARGUMENT IS LOAD-BEARING, NOT TIDINESS: `check_engine._plan_execution_tree` runs `merge-base --is-ancestor base_head HEAD` in the lane and returns `None` (rule silent) when it fails, and `allocate_worktree`'s own docstring records that a lane cut from an older base makes intervening commits appear in the delta. Expose parameters for `scope_paths`, the plan id, and whether to write the receipt at all, since the silent rows below need exactly those three knobs. MEASURED PRECEDENT for putting it here rather than in a new module: `support.ready_plan_text` was extracted for this exact reason, its docstring citing "twenty-one hand-maintained copies", and the four deleted files each rolled their own arranger (`_allocate_lane`/`_dirty_out_of_scope`/`_arrange`, `_repo`, `_mk_repo`/`_lane_of`, and one ad-hoc block) which is the duplication that let the lane be forgotten in the first place.
  - Depends on: none
  - Expected outcome: `tests/support.py` exports one arranger returning `(root, lane)`; called with its defaults and a change written under `lane/other/`, `check_engine.check_scope_drift(root)` returns exactly one finding whose detail names `other`; no test file needs to mention `allocate_worktree` to get a correct subject.
  - Execution state: pending

- [ ] E-02 STATE IN THE ARRANGER'S DOCSTRING WHY THE CHANGE BELONGS IN THE LANE, AS A PRECONDITION OF THE RULE RATHER THAN AS FIXTURE SCAFFOLDING. The docstring must say that `check_scope_drift` measures the plan's ISOLATED LANE and reports nothing at all for a plan without one, so a change placed in the main checkout is INVISIBLE to it and any assertion built that way passes for a reason unrelated to its subject. Cite the authority already recorded in the rule itself: `check_scope_drift`'s docstring section "WHICH TREE IS MEASURED IS PART OF THE RULE" (rcptstale `wmnmei`, backlog `v880xk`, maintainer ruling 2026-09-10), and the accepted cost it names, that hand work in a shared main checkout gets no advisory. This is the knowledge that was lost when the four files were deleted: three of them carried explicit warnings against exactly this vacuity, and with the files gone nothing records it. Keep it in the HELPER's docstring specifically, because that is the one place every future caller must pass through.
  - Depends on: E-01
  - Expected outcome: the arranger's docstring states the lane precondition, names the measured-tree ruling, and says plainly that a main-tree arrangement yields a vacuous pass; no equivalent prose is duplicated into the test module, which points at the helper instead.
  - Execution state: pending

### Task group 2: the restored behavioral coverage

- [ ] E-03 WRITE `tests/test_check_scope_drift.py` WITH THE FOUR-ROW TABLE THAT CARRIES THE RULE'S CORE CONTRACT, EVERY ROW ARRANGED THROUGH THE E-01 HELPER. Restore, as behavior, the four cases the deleted `test_event_derived_lifecycle.py::TestScopeDrift` asserted, each a distinct clause of the rule: (a) an out-of-scope change in the lane FIRES, and the finding's detail must NAME the offending path, not merely be non-empty; (b) an IN-SCOPE change is SILENT, which is the rule's purpose; (c) a `grandfathered` `Scope-Paths:` is SILENT, which is the documented sentinel carve-out `check_scope_drift` honors by treating an empty frozen allowlist as advisory-satisfied, and which somebody could "helpfully" tighten; (d) NO RECEIPT is SILENT, which is what stops the sweep attributing every uncommitted file in a shared checkout to whichever plan it found first. ROW (a) IS THE ANTI-VACUITY CONTROL FOR ROWS (b) TO (d) AND MUST BE IN THE SAME TABLE: three assertions of silence are all satisfied by a rule that reports nothing, which is precisely the state measured at authoring, so the firing row is what makes the other three mean anything. Row (d) MUST STILL ALLOCATE ITS LANE (pass the helper's write-receipt knob, do not skip the allocation), so its silence is attributable to the MISSING RECEIPT alone and not to the plan having no lane to measure. The failure message must diagnose the systematic mode explicitly: if all three silent rows pass while row (a) fails, the rule has stopped reporting entirely and the silent rows are vacuous.
  - Depends on: E-01, E-02
  - Expected outcome: `tests/test_check_scope_drift.py` holds a four-row table; the whole module passes on the unmodified tree; row (a) asserts the offending path appears in the finding detail; every row obtains its subject from the E-01 helper and no row hand-builds a lane.
  - Execution state: pending

- [ ] E-04 ADD THE TWO LIVENESS ROWS THAT PROVE A SPENT RECEIPT IS IGNORED, WHICH IS THE CLAUSE THAT KEPT ONE PLAN FROM OWNING ANOTHER AGENT'S FILES. `check_scope_drift` delegates to `_receipt_is_live` and skips a receipt in two cases that must not silently collapse into "always live": (a) the plan sits in a TERMINAL lifecycle directory, so a plan moved to `.aw/records/plans/executed/` with an identical out-of-scope change in its lane is SILENT while the same plan under `pending/` FIRES; and (b) the frozen `base_head` is NOT an ancestor of HEAD, so a receipt frozen at a commit unreachable from HEAD is SILENT. THESE TWO ROWS ARE PAIRED WITH A FIRING TWIN BY CONSTRUCTION, which is what keeps them from being vacuous: (a) asserts that the ONLY difference between firing and silence is the plan's directory, so the arrangement is proven capable of firing before the terminal case is claimed to suppress it. Use the same helper; for (a) move the plan file between the pending and terminal directories rather than building two unrelated repos, so the comparison is genuinely one-variable. Cover the terminal case through a `<disposition>/YYYYMM/` SHARDED path too, since the rule reads the disposition from the plan's path and a sharded terminal plan is the shape a real archived plan has.
  - Depends on: E-03
  - Expected outcome: four rows (pending-fires, terminal-silent, sharded-terminal-silent, unreachable-base-silent) pass on the unmodified tree; the terminal pair differs only in the plan's directory; each silent row is shown to become firing when its single suppressing condition is removed.
  - Execution state: pending

- [ ] E-05 PROVE THE NEW MODULE IS SENSITIVE BY MUTATION, AND RECORD THE RESULT IN THE MODULE DOCSTRING AS ITS REASON FOR EXISTING. A restored test is only worth its line count if breaking the behavior breaks it, and this whole plan exists because the current suite is green against a rule that returns nothing. Re-run the authoring mutation (an unconditional early `return drift` at the top of `check_engine.check_scope_drift`) and confirm the new module FAILS, then revert it and confirm the module passes. Then run a SECOND, narrower mutation that a composition test could never catch: delete the `exec_tree is None` guard so the rule falls back to measuring whichever tree it runs in, and confirm a row fails. State the outcome in the module docstring as the module's charter, and state its BOUND honestly: this module covers the drift advisory's own decisions (which tree, receipt liveness, the grandfathered sentinel, in-scope silence) and does NOT restore the receipt-liveness, transition-validity, or finalize-ownership claims that died with the same four files. DO NOT write the mutation into the repository in any form, and DO NOT add a test that reads `check_engine`'s source to assert the guard is present: that is the code-structure pin P16 forbids, and the mutation is a one-off validation technique whose evidence belongs in V-05.
  - Depends on: E-03, E-04
  - Expected outcome: with the early-return mutation applied the new module fails and the pasted output names the failing rows; with it reverted the module passes; the second (fallback-tree) mutation also fails at least one row; the module docstring states the charter and the bound; `git diff` confirms no production file was left modified.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- TESTS ASSERT BEHAVIOR, NEVER CODE STRUCTURE. `GUIDING_PRINCIPLES.md` P16 ("Test outcomes and behavior, never code structure or text") prohibits `inspect.getsource`, `ast.parse`, `read_text()` or regex against production code to verify wiring, and prohibits census and count pins. `AGENTS.md` restates it for authored AND RESTORED tests specifically. This decides the design question the backlog item left open; see Findings F-01.
- `tests/support.py` IS THE ESTABLISHED HOME FOR A SHARED ARRANGER, and `support.ready_plan_text` is the governing precedent: it is built from the real generator `ipd_authoring.build_skeleton` "rather than from a hand-written string, so a change to the authored skeleton reaches every fixture instead of drifting away from twenty-one hand-maintained copies". `support.init_repo` and `support.git` already exist and must be reused rather than re-implemented. There is NO `tests/conftest.py` (only a repo-root `conftest.py`, whose surface is the home sandbox and the per-test timeout), and no `tests/helpers/` or `tests/support/` package, so a new module is not warranted.
- BOTH TEST IMPORT STYLES ARE LIVE AND EVENLY SPLIT (30 files use `from tests import support`, 30 use a direct `import support` form), so either is conventional; match the neighbouring files rather than introducing a third.
- THE RULE'S OWN DOCSTRING IS THE AUTHORITY ON WHICH TREE IT MEASURES, and it is explicit that a plan with no usable lane "is reported on NOT AT ALL" and that the main-tree comparison must not be reintroduced "on the argument that coverage was lost by accident". A restored test must therefore arrange in the lane; this is the rule's contract, not a fixture preference.
- A FINDING IS ONE PER PLAN, NOT ONE PER PATH, carrying the count and a bounded path summary in its detail. A restored assertion must therefore assert on the DETAIL's content for the offending path, not on `len(drift)` equalling the number of dirty files.

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The backlog item's candidate direction (2), a meta-test asserting each scope-drift test file allocates a lane, is PROHIBITED and must be refused rather than silently dropped. | `GUIDING_PRINCIPLES.md` P16 forbids "substring/regex searches" and `ast.parse` "against production code", forbids "count or census pins", and requires that "breaking the underlying behavior makes the test fail"; `AGENTS.md` extends it to RESTORED tests. A meta-test scanning test files for an `allocate_worktree` call asserts code structure: it passes for a file that calls the allocator and ignores the handle, and fails for a correct file that obtains its lane through the E-01 helper. | Directions (1) and (3) are adopted; (2) is declined in "Deferred / out of scope" with this reason, not omitted. The shared helper subsumes its intent: a caller that goes through the helper cannot forget the lane, so there is nothing left to scan for. |
| F-02 | The item's stated premise is FALSIFIED: all four files it names are gone, so there is no fixture pattern left to guard. | `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_check_engine_receipt_liveness.py`, `tests/test_event_derived_lifecycle.py`, `tests/test_phase4_hooks.py`, `tests/test_finalize_scope_ownership.py`; all four are absent from the working tree and recoverable at `19313eed^`. The item was filed 2026-09-22, two days earlier. | The plan RESTORES coverage rather than guarding an existing pattern. Executing the item literally would produce a guard over an empty set. |
| F-03 | `check_scope_drift` currently has ZERO behavioral coverage: it can return nothing for every input with the suite green. MEASURED, not inferred. | An unconditional `return drift` inserted at the top of `check_engine.check_scope_drift` leaves `python3 -m pytest` at `3246 passed, 2 skipped` and the `slow`/`livecorpus` selection at its pre-existing `3 failed, 204 passed` (byte-identical failures with and without the mutation). | This is the plan's justification and the mutation is reused as V-05's sensitivity proof. It also sets the acceptance bar: the new module must FAIL under that mutation. |
| F-04 | The one surviving mention of the rule cannot catch a behavioral regression, BY DESIGN, and must not be mistaken for coverage. | `tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_check_commit_invariants_composition` `mock.patch`es `agent_workflows.check_engine.check_scope_drift` to return a hand-built sentinel and asserts `"check.scope-drift" in rules`. It asserts COMPOSITION, which is a real and separate claim. | Leave that test untouched and out of Scope-Paths. The new module is additive; it does not duplicate the composition claim. |
| F-05 | A lane-arranged subject genuinely FIRES and the identical main-tree arrangement is genuinely SILENT, so the vacuity the item describes is real and the fixture shape in E-01 is proven to work before it is written. | Executed probe this turn over a throwaway repo, same arrangement twice, varying only the tree the change is written into: dirt in LANE gave 1 finding, `"1 changed path is outside the plan's declared Scope-Paths: 'other/'"`; dirt in MAIN TREE gave 0 findings, SILENT. | E-01's parameter list and the `base_commit=base` requirement are taken from a working arrangement, not from the deleted files' prose. The firing detail's shape also fixes how row (a) asserts (on the detail, per the one-finding-per-plan convention). |
| F-06 | The lane MUST be cut at the frozen base or the rule goes silent for a reason unrelated to the test's subject, which is a second, subtler vacuity route. | `check_engine._plan_execution_tree` runs `merge-base --is-ancestor base_head HEAD` in the lane and returns `None` on failure, and `check_scope_drift` then `continue`s with the comment "not lane-isolated (or the lane's base is unusable) -> no honest subject". `worktree_lease.allocate_worktree` documents the same hazard for a lane cut from an older base. | E-01 passes `base_commit=base` explicitly and E-01's expected outcome names it, so a future caller cannot regress to a `HEAD`-cut lane and read the resulting silence as a pass. |
| F-07 | Three of the four deleted files carried explicit written warnings against this exact vacuity, and deleting them destroyed the only record of it. | The deleted `test_event_derived_lifecycle.py::TestScopeDrift` docstring stated that without lane isolation "all three silent rows would pass against a rule that had stopped working entirely, which is exactly the vacuity this docstring warns about"; `test_check_engine_receipt_liveness.py` and `test_phase4_hooks.py` carried equivalent warnings (the latter using the word VACUOUSLY). | E-02 re-homes that knowledge in the HELPER's docstring rather than in one test module, so it survives the deletion of any single test file. This is the structural fix the item asked for. |
| F-08 | The scope of the restoration must be bounded to the drift advisory, because the four deleted files carried three other unrelated surfaces. | Only one of the four was primarily about drift; `test_finalize_scope_ownership.py` was mostly finalize ownership attribution with exactly one drift test, and the others carried receipt-liveness and event-derived transition-validity claims. Backlog `xvp5vx` already owns the general "audit what lost its only guard in 19313eed" work, and its maintainer ruling forbids restoring code-pinning tests. | Those surfaces are named in "Deferred / out of scope" and left to `xvp5vx`, rather than being swept into this plan or silently forgotten. |

## Proposed changes (ordered, validatable)

1. `tests/support.py`: add one scope-drift arranger that builds the repo, the plan, the receipt at the frozen base, and the lane cut at that base, returning `(root, lane)`, parameterized on `scope_paths`, plan id, and whether a receipt is written (E-01), with a docstring stating the lane precondition and citing the measured-tree ruling (E-02).
2. `tests/test_check_scope_drift.py`: add the four-row core-contract table, arranged entirely through that helper, with the firing row as the in-table anti-vacuity control for the three silent rows (E-03).
3. `tests/test_check_scope_drift.py`: add the four liveness rows (pending-fires, terminal-silent, sharded-terminal-silent, unreachable-base-silent), each paired with a firing twin so no silence is claimed from an arrangement not first proven capable of firing (E-04).
4. Validate the module by mutation (early return, then removal of the lane-subject guard), confirm it fails under both and passes on the unmodified tree, and record the charter and its bound in the module docstring (E-05).

Nothing in `agent_workflows/` changes. The rule is the subject under test and must not move while its coverage is written.

## Deferred / out of scope (with reason)

- A META-TEST ASSERTING EACH SCOPE-DRIFT TEST FILE ALLOCATES A LANE (the item's candidate direction 2). REFUSED, not deferred: it is a code-structure pin prohibited by `GUIDING_PRINCIPLES.md` P16 and by `AGENTS.md`, and it would be both unsound (green for a file that calls the allocator and discards the handle) and wrong (red for a correct file using the E-01 helper). Its intent is met by making the helper the only reasonable arranging route. See F-01.
  - Carrier-Declined: Nothing is owed, because this row records a PROHIBITION rather than unbuilt work. Filing an item would misrepresent a settled policy conclusion as an outstanding task: `GUIDING_PRINCIPLES.md` P16 already forbids the mechanism outright, so the only artifact a carrier could produce is a test the repository has ruled must not exist. The backlog item's own wording offers the three directions as candidates and asserts none, so declining one of them is answering the question it asked rather than dropping it. Recorded here so a reviewer meets the refusal and its reason rather than reading silence as an oversight.
- RESTORING THE RECEIPT-LIVENESS SUITE AS ITS OWN SURFACE. The deleted `test_check_engine_receipt_liveness.py` asserted `_receipt_is_live`'s behavior in its own right (fail-safe on error, disposition parsing, aggregator and hook exit codes). This plan covers liveness only where `check_scope_drift` DEPENDS on it (E-04). The rest belongs to the trim audit `xvp5vx`.
  - Carrier: xvp5vx
- RESTORING THE EVENT-DERIVED TRANSITION-VALIDITY AND FINALIZE-OWNERSHIP COVERAGE lost in the same commit. Separate subjects with separate claims; see F-08. Left to `xvp5vx` so this plan stays one focused pass.
  - Carrier: xvp5vx
- CHANGING `check_scope_drift`, `_plan_execution_tree`, `_receipt_is_live`, OR `worktree_lease`. Out of scope by construction: writing coverage around a moving subject would prove nothing. If E-03 or E-04 finds a genuine BUG in the rule, record it as a new backlog item and leave the rule alone rather than fixing it here.
  - Carrier-Declined: Nothing is owed unless something is found, so there is no work to carry today. This row is a SCOPE FENCE on this plan, not a deferred defect: no finding here measures a fault in the rule, and the rule behaves as its docstring specifies. Filing a carrier now would assert a bug nobody has measured. The contingency is already directed at the moment it could arise, since the row itself instructs the executor to file a new backlog item if E-03 or E-04 surfaces a genuine defect, and V-05's clean `git diff --stat agent_workflows/` is what enforces the fence.
- THE ADVISORY'S ACCEPTED BLIND SPOT, that hand work in a shared main checkout gets no advisory at all. This is a deliberate maintainer ruling recorded in the rule's docstring, not a defect, and E-03's row (b) must not be written in a way that argues against it.
  - Carrier-Declined: Nothing is owed, because this is an accepted cost rather than a gap. `check_engine.check_scope_drift`'s own docstring records the trade as deliberate (maintainer ruling 2026-09-10) and instructs a reader not to reintroduce a main-tree comparison "on the argument that coverage was lost by accident", so a carrier proposing to close it would be filing work the ruling forbids. It is named here because a reader of the restored coverage will notice the blind spot and should meet the ruling rather than mistake it for something this plan missed.

## Scope check

- Over-scope: none. Both declared paths are test-only; no production module, spec, or document is touched.
- Under-scope: the three sibling surfaces deleted by `19313eed` alongside the drift coverage remain uncovered after this plan, and it does not claim otherwise; they are enumerated in "Deferred / out of scope" and owned by `xvp5vx`. This plan closes the drift advisory's own hole and E-05 states that bound in the module docstring so a later reader does not mistake the module for a full restoration of the four deleted files.

## Required tests / validation

- `python3 -m pytest tests/test_check_scope_drift.py` passes on the unmodified tree, run bare (the configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; add no flags).
- The full bare suite `python3 -m pytest` passes, with the pasted `N passed` summary line, confirming the new `tests/support.py` symbol breaks no existing importer of that module.
- SENSITIVITY IS MANDATORY AND IS THE POINT OF THE PLAN (E-05): with an unconditional early `return drift` at the top of `check_engine.check_scope_drift`, `tests/test_check_scope_drift.py` must FAIL; with the `exec_tree is None` guard removed so the rule measures whatever tree it runs in, at least one row must FAIL. Both mutations reverted afterwards, proven by a clean `git diff` over `agent_workflows/`.
- Each SILENT row must be shown to become FIRING when its single suppressing condition is removed, which is what distinguishes a meaningful silence from an arrangement that stopped measuring.
- `git status --short` is clean of stray lanes and temp repos after the run: the fixture allocates real worktrees, so a leaked lane would pollute the checkout.

## Spec / documentation sync

N/A with reason. No spec governs the drift advisory's TEST coverage, and the rule's behavior is unchanged by this plan, so there is no contract to amend: `check_engine.check_scope_drift`'s docstring already records the measured-tree ruling (rcptstale `wmnmei`, backlog `v880xk`, maintainer ruling 2026-09-10) and this plan neither extends nor narrows it. No `.spec.md` file is in Scope-Paths, deliberately. `GUIDING_PRINCIPLES.md` P16 and `CONTRIBUTING.md` are likewise NOT edited: P16 already prohibits the pin this plan declines, and restating it would be the duplication `CONTRIBUTING.md`'s own "Keep each policy or rule in exactly one canonical place" bullet warns against.

## Open questions

### OQ-01: Should the restored module also cover the pre-commit gate's exit-code behavior for this rule, which died with `tests/test_phase4_hooks.py`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved from repository evidence rather than deferred. The deleted `test_phase4_hooks.py` asserted that the opt-in gate exits 1 on an out-of-scope lane change and 0 on a clean one, which is a claim about THE HOOK's composition and exit code, not about the advisory's decisions. `check_scope_drift`'s docstring records that the gate "prints that field verbatim as its teaching message", so the hook consumes the rule's output and its coverage is a separate surface with a separate failure mode. Adding it here would widen this plan past one focused pass and would overlap the hook coverage that `xvp5vx` must triage as a whole. The drift rows in this module are what make the rule's output correct in the first place; a hook asserting an exit code over a rule that reports nothing is exactly the vacuity being fixed, so the ordering (rule coverage first) is deliberate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the added `tests/support.py` arranger quoted in full, showing it calls `support.init_repo`, writes `.gitignore` with BOTH `.aw/state/` and `.aw/worktrees/`, derives the receipt path from `ipd_lifecycle.receipt_path_for` (no hand-built path string), and calls `worktree_lease.allocate_worktree(..., base_commit=<frozen base>)`. Plus PASTED output of a throwaway invocation that calls the helper with defaults, writes a file under `lane/other/`, and prints `check_engine.check_scope_drift(root)`: the printed result must be exactly one finding whose detail contains `other`. A printed empty list FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the arranger's docstring quoted verbatim, showing it states (a) that the rule measures the isolated lane, (b) that a plan with no lane is reported on not at all, and (c) that a main-tree arrangement therefore passes vacuously. Plus a `grep`-style confirmation that the citation of the measured-tree ruling (`wmnmei` / `v880xk` / 2026-09-10) appears in it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTED output of `python3 -m pytest tests/test_check_scope_drift.py` showing the four-row table passing, plus the table quoted from the source showing all four rows (out-of-scope FIRES, in-scope SILENT, grandfathered SILENT, no-receipt SILENT) and showing that the no-receipt row still allocates its lane. Plus, for the firing row, the asserted substring proving the OFFENDING PATH is checked in the finding detail rather than only the finding count. Plus a demonstration that the three silent rows are non-vacuous: for each, paste the FAILING output produced when its single suppressing condition is removed (change moved out of scope; sentinel replaced with a real allowlist; receipt written), then confirm the row passes again once reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTED passing output for the four liveness rows, plus evidence that the terminal pair differs ONLY in the plan's directory (quote both arrangements side by side). Plus proof that each silent liveness row is non-vacuous: paste the FAILING output when the plan is moved back to `pending/` for the terminal rows, and when the receipt's `base_head` is set to a reachable commit for the unreachable-base row. The sharded row must show a `<disposition>/YYYYMM/` path in its arrangement.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THE MUTATION EVIDENCE, in four pasted blocks. (1) With an unconditional early `return drift` at the top of `check_engine.check_scope_drift`, `python3 -m pytest tests/test_check_scope_drift.py` output showing FAILURES and naming the failing rows. (2) With the `exec_tree is None` guard removed, output showing at least one FAILING row. (3) After reverting both, output of the full bare `python3 -m pytest` showing its `N passed` summary line, plus `git diff --stat agent_workflows/` printing NOTHING. (4) The module docstring quoted, showing the charter and the explicit bound that the receipt-liveness, transition-validity, and finalize-ownership surfaces are NOT restored here. A claim of sensitivity without the failing output pasted FAILS this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `Readiness:` and NO `Approval:` field: both are outputs of
`/plan-review` and of a human sign-off respectively, and writing either here would forge an attestation
a gate reads. Execution requires explicit human approval first.

On execution, the contract in `AGENTS.md` applies: commit only the two declared paths through
`aw commit <plan> -- tests/support.py tests/test_check_scope_drift.py`, never `git add -A`, never push,
and paste ACTUAL runner output rather than claiming a pass. The mutations required by E-05 and V-05 are
VALIDATION SCRATCH and must never be committed; V-05 requires a clean `git diff --stat agent_workflows/`
as proof. The fixture allocates REAL git worktrees, so confirm no lane or temp repo is left behind before
committing. Do not move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.
