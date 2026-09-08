# IPD: Re-home the host-neutral names into runner_shared in reviewable batches without a cycle or a lost re-export

- Date: 2026-09-08
- Kind: child
- Concern: `agy_runipd` depends on `oc_runipd` for names that have nothing to do with opencode, so a host driver is a library for the other host's driver. RE-MEASURED BY AST WALK at HEAD `44d4950d`: 47 names imported oc-to-agy across eight `ImportFrom` statements (4 at `:266`, 21 at `:308`, 17 at `:333`, one each at `:1399`, `:2371`, `:2380`, `:2387`, `:2399`); ZERO agy-to-oc. Grouped by concern the 47 are 13 dependency-graph names, 12 backlog-closing, 4 run-ordering, 3 recovery-routing, 3 shutdown-reporting, 2 suite-checking, plus a remainder. None of those concerns is about opencode.
  THE HOME ALREADY EXISTS AND THE MOVE PATTERN IS ESTABLISHED. Executed plan `818uru` created `runner_shared.py` and moved 34 symbols into it as a PURE MOVE, verified by AST-identity assertions against the pre-move definitions plus object-identity assertions that both runners resolve to the same object, with its ONE permitted behavior change declared in writing. Its scope fence then said explicitly "Do NOT re-home the 40 oc-to-agy imports", which is why this work is real and unowned. The module is `runner_shared.py`, not `runner_common.py` as the backlog item says: `818uru` OQ-01 renamed it by maintainer ruling because `runner_common` "can be misread as a generic dumping ground".
  THE EXECUTION HAZARD IS A FORMATTER, NOT THE MOVE. Backlog `cnwy8g` records that `ruff` REMOVED 6 of these re-exports on a first commit attempt, caught only by a cross-driver symmetry test, "which is why the `as <same-name>` form is load-bearing rather than cosmetic". Both `ruff` and `ruff-format` are pre-commit hooks in this repository, so this will happen again on this plan's commits unless the form is preserved deliberately. The test that caught it is `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1179`), whose `test_the_implementation_is_shared_not_copied` (`:1201`) asserts OBJECT IDENTITY for eleven of these names, and whose `_SHARED_NAMES` tuple (`:1182`) is where a re-homed name gets registered.
- Scope: Move every name child 01 classified host-neutral from `oc_runipd.py` into `runner_shared.py`, in reviewable batches, as a PURE MOVE with no body change, keeping the shared module free of any runner import and the agy-to-oc direction at zero, preserving the `as <same-name>` re-export form, and extending the cross-driver symmetry guard. CLOSES backlog `cnwy8g`. EXCLUDES any name classified opencode-specific or UNSETTLED by child 01; excludes any diverged symbol (`818uru` deferred those behind `lanectn`); excludes any behavior change whatsoever.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_runner_item_dependencies.py, tests/test_runner_layering.py, tests/test_runner_refork_guard.py
- Item-Dependencies: executed:9kmbr0
- Status: to-review
- Set: runnerlayer
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 1f7xno
- From-Backlog: cnwy8g

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `cnwy8g` as Order 02 of the `runnerlayer` Set, and the child that CLOSES the item, because the layering correction the item describes is delivered here rather than by the classification. NO `- Blocks-Release:` FIELD, deliberately and faithfully to the item, whose Gate section says "No `Blocks-Release` gate. This is a layering correction, not a live failure" and records that its one behavioral consequence (`DriverError`) was owned by `818uru` E-03, which has executed and which I verified: `oc.DriverError is agy.DriverError is runner_shared.DriverError` -> `True`.
  FOUR MEASUREMENTS SHAPED THIS PLAN. FIRST, 47 names not 40, across eight statements not six, and the delta is reported on child 01 so an executor is not hunting for `DriverError` (gone) or the wrapper the item cites at `agy_runipd.py:87-93` (also gone; that range now holds a `render_stream` re-export comment). SECOND, `818uru` is `executed` and its fence excluded exactly this work, so the item's sequencing precondition is satisfied and nothing here steps on it. THIRD, `818uru`'s own record documents that a NAIVE LIFT FAILS: four of its 34 symbols called symbols OUTSIDE the moved set, two of them diverged, and those dependencies had to be INJECTED rather than imported. That is the single most likely way this plan breaks, and E-02 is written around it. FOURTH, the guard that caught the ruff deletion is a real test at a real location and asserts object identity for eleven of these names, so it must be extended rather than replaced.
  WHY BATCHES AND NOT ONE MOVE: `818uru` moved 34 symbols in one plan and needed six E-items and a characterization baseline to do it safely. This plan may move a comparable number, and a single all-at-once diff would be unreviewable and would make a bisect useless if one move broke something. E-02's batching is by CONCERN GROUP, which is also how child 01's classification is organized, so each batch is independently reviewable and independently revertible.

## Goal

Make every host-neutral name live in the shared module, so a fix reaches both drivers and neither driver is a library for the other.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prepare before moving anything

- [ ] E-01 READ CHILD 01'S CLASSIFICATION AND FREEZE THIS PLAN'S WORK LIST FROM IT, then RE-MEASURE the live import set and reconcile the two. Do NOT derive the work list from this plan's prose: the count moved from 40 to 47 in the five days before this plan was written, so it will have moved again.
  RECONCILE THE DELTA EXPLICITLY, do not silently take the intersection. If a name appeared after child 01's classification, it is UNCLASSIFIED and must NOT be moved on a guess; record it and either classify it against child 01's stated criterion or leave it and say so. If a classified name has disappeared, record that too. A plan that quietly moves whatever is currently there has abandoned the classification the Set exists to be reviewed against.
  RESPECT THE UNSETTLED VERDICTS. Child 01 may have recorded names as UNSETTLED with reasons. An UNSETTLED name is NOT a host-neutral name and must not be moved. If moving one seems obviously right, that is a maintainer question, not a judgment call to make inside a pure-move plan.
  - Depends on: none
  - Expected outcome: a frozen work list derived from child 01's classification and reconciled against a fresh AST measurement, with every added, removed and UNSETTLED name named and its disposition stated; no name moved on a guess.
  - Execution state: pending

- [ ] E-02 MAP EACH NAME'S OUTBOUND CALLS BEFORE MOVING IT, because a naive lift fails and `818uru` measured exactly how. Its record states that four of its 34 symbols called symbols OUTSIDE the moved set (`run_checked` -> `pinned_child_env`, `discover_plans` -> `parse_plan_file`, `save_state` -> `write_report`, `validate_manifest` -> `parse_dependency_token`), two of them DIVERGED between the hosts, so those dependencies were INJECTED rather than imported.
  FOR EACH NAME IN THE WORK LIST, RECORD WHAT ITS BODY CALLS and whether each callee is (a) already in `runner_shared`, (b) also being moved in this plan, (c) still in `oc_runipd` and staying, or (d) DIVERGED between the hosts. Case (c) is the one that would create the very back-edge this plan exists to remove, and case (d) is `818uru`'s injection case. Produce this map BEFORE the first move; it decides the batch order.
  A NAME WHOSE CALLEES CANNOT BE SATISFIED WITHOUT A BACK-EDGE DOES NOT MOVE IN THIS PLAN. Record it as blocked with the specific callee that blocks it. Moving it and adding a `from agent_workflows.oc_runipd import ...` to `runner_shared` would be strictly worse than leaving it, because it would put the cycle in the shared module.
  - Depends on: E-01
  - Expected outcome: a per-name callee map classifying every callee into the four cases; a batch order derived from it; any name blocked by a case (c) callee recorded as blocked with the callee named, and NOT moved.
  - Execution state: pending

### Task group 2: move, one concern group at a time

- [ ] E-03 MOVE THE FIRST BATCH AS A PURE MOVE and prove the pattern works before touching the rest. Take the concern group whose callee map is cleanest from E-02, not the largest.
  PURE MOVE MEANS THE BODY IS BYTE-IDENTICAL. `818uru` verified each move with an AST-identity assertion against the pre-move definition plus an object-identity assertion that both runners resolve to the same object. Use that same pattern; `tests/test_runner_shared.py` already exists from that plan and is where these assertions live. Do NOT reformat, rename a local, add a type hint, or improve a docstring while moving. If a body must change, that is a different plan.
  PRESERVE THE `as <same-name>` RE-EXPORT FORM in both drivers for anything that remains reachable through them. `ruff` previously deleted six of these, and `ruff` plus `ruff-format` are pre-commit hooks here, so the deletion will be attempted on this plan's first commit. Expect a hook rejection, and when it happens, RE-VERIFY the staged set before retrying: `pre-commit` stashes unstaged changes and can restore paths you never staged.
  `runner_shared` MUST IMPORT NEITHER RUNNER. That is `818uru` E-01's admission rule and this Set's CID-2. Assert it by AST rather than by import success: a lazy in-function import succeeds at module load and is still a layering violation.
  - Depends on: E-02
  - Expected outcome: the first concern group moved; each move verified by AST-identity against the pre-move body plus object identity across `oc_runipd`, `agy_runipd` and `runner_shared`; re-export form intact through a real hook-passing commit; `runner_shared` importing neither runner, asserted by AST.
  - Execution state: pending

- [ ] E-04 MOVE THE REMAINING BATCHES, one concern group per commit, each independently revertible. Re-run the bare suite after each batch and compare failing NODE IDS, not totals; a batch that changes the failing set stops the plan rather than being pushed through.
  COMMIT PER BATCH, NOT ONCE AT THE END. The reason is mechanical: if one move breaks something, a per-batch history makes it a one-commit revert and a bisect useful, whereas a single large commit makes the failure a puzzle. Path-scope every commit and verify the staged set before each.
  DO NOT LET A LATER BATCH SILENTLY WIDEN AN EARLIER DECISION. If moving a name in batch 3 turns out to require moving something E-02 marked as staying, STOP and report; that is E-02's map being wrong, which is worth knowing, not something to absorb.
  - Depends on: E-03
  - Expected outcome: every host-neutral name in the frozen work list moved, one concern group per commit; the bare suite's failing node-id set unchanged after every batch; any discovered map error reported rather than absorbed.
  - Execution state: pending

### Task group 3: prove the direction and guard it

- [ ] E-05 EXTEND THE CROSS-DRIVER SYMMETRY GUARD, never replace it. `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1179`) asserts presence AND object identity for eleven of these names via `test_the_implementation_is_shared_not_copied` (`:1201`), with `_SHARED_NAMES` at `:1182`. It is the test that caught `ruff` deleting six re-exports, so it is the guard that matters most here.
  DO NOT WEAKEN ITS OTHER ASSERTION. The same module separately asserts that a shared module "must not learn about the runner or its run state". A re-homed name that drags run-state knowledge into `runner_shared` would trip it, and that trip is CORRECT: it means the name was misclassified, not that the test is wrong.
  UPDATE CHILD 01'S FROZEN SET. Child 01 pinned the SORTED SET of oc-to-agy imported names in `tests/test_runner_layering.py`. Every move changes that set, so the pin must be updated in the SAME commit as the move it reflects, or the suite is red between commits and a bisect becomes useless. Do NOT delete the pin to make the suite pass; that is exactly the destructive fix child 01's constructive failure message exists to prevent.
  - Depends on: E-04
  - Expected outcome: `_SHARED_NAMES` extended with every re-homed name; the run-state assertion untouched and passing; child 01's frozen set updated in the same commit as each move; the pin still present and still failing on an unsanctioned addition.
  - Execution state: pending

- [ ] E-06 PROVE THE RESIDUAL EQUALS THE CLASSIFICATION. The set of names still imported oc-to-agy must be EXACTLY the names child 01 classified opencode-specific, plus any name E-01 recorded as unclassified and E-02 recorded as blocked. A set difference in either direction is a failure, not a rounding error.
  PRINT TWO SET DIFFERENCES, BOTH EMPTY, rather than asserting equality in prose. Extra residual means something that should have moved did not; missing residual means something moved that was not sanctioned, which is the more serious direction because it means an opencode-specific symbol is now in the shared module.
  ASSERT THE REVERSE DIRECTION IS STILL ZERO. It is zero today, and this plan's whole subject is directionality; a cycle introduced while fixing a layering violation would be the worst possible outcome.
  - Depends on: E-05
  - Expected outcome: two empty set differences printed; the residual accounted for name by name against child 01's classification plus the recorded unclassified and blocked names; the agy-to-oc count still zero, measured by AST.
  - Execution state: pending

- [ ] E-07 CLOSE BACKLOG `cnwy8g` THROUGH THE SETTER, not by hand, and only after E-06 passes. The item carries NO `Blocks-Release` gate, so its close is not gate-gated, but it must still be closed by the tool so the workflow history records it.
  DO NOT INVENT A GATE ON THE WAY OUT. If E-02 or E-04 discovered a SECOND behavioral defect traceable to this layering, the item's own instruction is to "gate it then", which means FILING a new item carrying its own gate, not retroactively gating this Set. Record any such discovery.
  - Depends on: E-06
  - Expected outcome: `cnwy8g` reads `- Status: done`, closed via `aw backlog set` with a message citing this plan; `aw backlog check` clean; no `Blocks-Release` field added to any plan in this Set; any second behavioral defect filed as a new item rather than gating this one.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `818uru` IS THE PATTERN. PURE MOVE, verified by AST-identity against the pre-move definition PLUS object-identity across both runners; its ONE permitted behavior change (re-parenting `StallTimeout` onto the shared `DriverError`) was declared in writing in its scope fence rather than discovered in a diff. `tests/test_runner_shared.py` exists from that plan and is where those assertions live.
- A NAIVE LIFT FAILS, MEASURED. `818uru` found four of its 34 symbols called symbols OUTSIDE the moved set, two of them DIVERGED, and injected those dependencies rather than importing them. This is why E-02 exists as its own item.
- THE MODULE IS `runner_shared.py`. `818uru` OQ-01 renamed it from `runner_common` by maintainer ruling; the backlog item predates that.
- `runner_shared` IMPORTS NEITHER RUNNER, and that is an admission rule rather than a coincidence (`818uru` E-01). Assert it by AST, since a lazy in-function import would pass an import-success check.
- `ruff` WILL DELETE AN UNUSED RE-EXPORT and has already deleted six of these once. `ruff` and `ruff-format` are pre-commit hooks here. The `as <same-name>` form is load-bearing, and a hook rejection on the first commit attempt is expected rather than surprising.
- AFTER A FAILED HOOK, RE-VERIFY THE INDEX. `pre-commit` stashes unstaged changes and restores them when a hook rejects, which can leave paths you never staged in the index. This repository has concurrent agents, so an unverified retry can sweep someone else's work into this plan's commit.
- THE SYMMETRY GUARD IS THE REAL PROTECTION. `CrossDriverSymmetryTests` (`:1179`) checks presence and object identity for eleven names and separately forbids a shared module learning about run state. Extend it; a trip of the run-state assertion means a misclassification, not a bad test.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses), while a lane worktree shows roughly 32 environmental failures.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `agy_runipd.py:266`, `:308`, `:333`, `:1399`, `:2371`, `:2380`, `:2387`, `:2399` | 47 names imported oc-to-agy across eight statements; 0 agy-to-oc. Most are dependency-graph, backlog-closing, run-ordering, recovery-routing, shutdown-reporting or suite-checking, none about opencode. | AST walk over `ImportFrom` nodes in both modules |
| F-2 | HIGH | `818uru` record | A NAIVE LIFT FAILS: four of its 34 symbols called symbols outside the moved set, two DIVERGED, requiring injection rather than import. This is the most likely way this plan breaks. | that plan's findings |
| F-3 | HIGH | `.pre-commit-config.yaml`; backlog `cnwy8g` | `ruff` previously removed 6 of these re-exports on a first commit attempt, caught only by the cross-driver symmetry test, and `ruff` plus `ruff-format` are hooks here. Expect a rejection. | config read; the item's recorded incident |
| F-4 | HIGH | `tests/test_runner_item_dependencies.py:1179`, `:1182`, `:1201` | `CrossDriverSymmetryTests` asserts presence AND object identity for eleven of these names and separately forbids a shared module learning about run state. Extend, never replace. | source read |
| F-5 | MED | `.aw/records/plans/executed/20260903-rununify-02-818uru-...ipd.md` | The precondition is satisfied: `818uru` is `executed` and its fence says "Do NOT re-home the 40 oc-to-agy imports", so this work is unowned. | that plan's `- Status:` and fence |
| F-6 | DISCHARGED | `runner_shared.py:159`; `oc_runipd.py:176`; `agy_runipd.py:181` | The item's only behavioral consequence is fixed: `DriverError` is ONE object across both drivers and the shared module. Hence no release gate on this Set. | identity check |
| F-7 | STALE-CITATION | `agy_runipd.py:84-96` | The item cites a `DriverError` translation wrapper at `:87-93`; that code is gone and the range now holds a `render_stream` re-export comment. | source read |
| F-8 | MED | `oc_runipd.py:4717`, `agy_runipd.py:2348` | `build_isolation_notice` left the import list because BOTH hosts now DEFINE it, which is a re-fork rather than an improvement. Out of this plan's scope (re-forks are `2r306y`'s subject) but worth recording so it is not read as progress. | source read of both definitions |
| F-9 | MED | `2r306y` | `_read_id`/`_read_status` were already moved to `selectors.py` with a one-definition rationale, so the remaining `_read_*` names may belong in `selectors` rather than `runner_shared`. Child 01's classification should have said which; if it did not, E-01's reconciliation is where that surfaces. | that plan's record |

## Proposed changes (ordered, validatable)

1. E-01 freezes the work list from child 01's classification and reconciles it against a fresh AST measurement, naming every delta and every UNSETTLED name.
2. E-02 maps each name's callees into four cases and derives the batch order, refusing to move anything that would need a back-edge.
3. E-03 moves the cleanest batch as a PURE MOVE, proving the AST-identity plus object-identity pattern and surviving the formatter.
4. E-04 moves the remaining batches, one concern group per commit, comparing failing node ids after each.
5. E-05 extends the symmetry guard and updates child 01's frozen set in the same commit as each move.
6. E-06 proves the residual equals the classification with two empty set differences and the reverse direction still zero.
7. E-07 closes backlog `cnwy8g` through the setter without inventing a gate.

## Deferred / out of scope (with reason)

- ANY NAME CLASSIFIED OPENCODE-SPECIFIC OR UNSETTLED BY CHILD 01. An UNSETTLED name is not a host-neutral name; moving one because it looks obvious would discard the classification this Set is reviewed against.
- ANY NAME BLOCKED BY A CALLEE THAT STAYS IN `oc_runipd` (E-02 case (c)). Moving it would put the back-edge in the SHARED module, which is strictly worse than the current state.
- RECONCILING ANY DIVERGED SYMBOL. `818uru` deferred class (c) diverged symbols behind `lanectn` and its characterization baseline, and named the two `PlanRecord` definitions as staying. If a callee is diverged, `818uru`'s injection pattern applies; reconciling it does not.
- ANY BEHAVIOR CHANGE, INCLUDING A DOCSTRING IMPROVEMENT OR A TYPE HINT ADDED WHILE MOVING. Named explicitly because a pure move is where tidying is most tempting and least reviewable.
- FIXING THE `build_isolation_notice` RE-FORK (F-8). Re-forks are `2r306y`'s subject.
- ADDING A `Blocks-Release` GATE. The item carries none and explains why. A second behavioral defect gets FILED, not retro-gated.
- MOVING A NAME INTO `selectors` RATHER THAN `runner_shared` (F-9) unless child 01's classification says so. If the classification is silent, record the question rather than choosing a destination this Set never reviewed.

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY to remove a moved definition and to adjust an import or re-export. Do NOT change any body, any gate, or any behavior. `tests/test_runner_layering.py` is in scope only to update child 01's frozen set, never to delete or weaken it.
- Under-scope: stated rather than left as `none`. After this plan the drivers are peers with respect to IMPORTS, but each still carries its own diverged symbols, its own duplicated constants (`SUCCESS_STATES` and `EXECUTION_SUCCESS_STATES` are measured equal but not identical), and at least one re-fork (`build_isolation_notice`). `rununify` owns those.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, and re-run after EVERY batch, comparing failing NODE IDS not totals. `tests/test_runner_shared.py` holds the AST-identity and object-identity assertions from `818uru` and is where each move's proof belongs. `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` must be EXTENDED and must keep passing, including its assertion that a shared module must not learn about run state. `tests/test_runner_layering.py` holds child 01's frozen set and must be updated per move, never deleted. `tests/test_runner_refork_guard.py` is declared in case a moved name belongs in its `REFORK_TABLE`; if it is not touched, acknowledge the declared-but-unmodified path at finalize rather than editing it to justify the declaration.

## Spec / documentation sync

N/A for the move itself, with the reason stated rather than asserted: relocating a definition changes no documented contract, no operator-facing string, and no run-record shape. No spec governs which module a host-neutral helper lives in.
ONE THING TO CHECK RATHER THAN ASSUME, and it is a real risk in a move plan: if any re-homed name is NAMED in a spec, a README, or a docstring that cites its MODULE PATH, that citation becomes wrong the moment the definition moves. Grep the `.aw/records/specs/` tree and the package docstrings for every name in the work list before finalizing, and fix any stale module-path citation as documentation. A tree that contradicts itself about where a symbol lives is worse than one that never said. Any prose you write for a human reader must contain no em or en dashes.
Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Where does a name whose natural owner is a THIRD module go?

- Blocking: no
- Status: open
- Owner: this plan's executor, deferring to child 01's classification where it speaks
- Resolution or deferral rationale: NOT blocking, because the deferred section already instructs that such a name NOT be moved to a destination this Set never reviewed, so the plan is executable by leaving it. The concrete case is F-9: `2r306y` moved `_read_id` and `_read_status` into `selectors.py` because that module owns front-matter reading, and `_read_kind`, `_read_from_backlog` and `_read_item_dependencies` are their siblings. Moving them to `runner_shared` would be defensible but would put a reader in the runner-sharing module while its two siblings live in `selectors`, which is a worse arrangement than either extreme. If child 01's classification named a destination, follow it; if not, record the question and leave those three where they are.

### OQ-02: Should a pass-through re-export be re-pointed rather than moved?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-01 and E-02 already require each name be identified as a real definition or a pass-through before anything moves, so the cheaper path is available wherever it applies. Where `oc_runipd` merely re-exports a name it imports from a third module, agy importing it from oc is still a layering violation (agy reaches through oc), but the FIX is a one-line re-point of agy's import to the owning module, with NO definition move and NO risk of a body change. That is strictly better and should be preferred wherever child 01 marked a name as a pass-through. Recorded as an OQ because the classification may not have distinguished them, in which case this plan measures it.

### OQ-03: What if a batch's failing node-id set changes and the cause is another agent's concurrent commit?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because the correct response is the same either way: STOP and report rather than push through. It is recorded because it is likely rather than hypothetical: this repository has concurrent agents working in the same checkout, both drivers are the highest-contention files in it, and this plan runs the suite after every batch. A changed failing set whose new node ids are in modules this plan never touched is evidence of a concurrent change, not of this plan's breakage, and the honest report says which. Re-measure the baseline in the worktree rather than comparing against a number from this document.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste child 01's classification as read, and the fresh AST measurement taken at execution time. Paste the reconciliation: every name added since the classification, every one removed, and every UNSETTLED one, each with its disposition. If the live count is not 47, say so; both drivers are edited by live runs. Paste the frozen work list this plan will act on.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the per-name callee map, with every callee classified as already-shared, also-moving, staying-in-oc, or DIVERGED. Paste the derived batch order and the reason for its first element. Paste every name recorded as BLOCKED with the specific callee that blocks it; an empty blocked list is an acceptable answer only if the map shows why.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for EVERY name in the first batch, paste the AST-identity assertion against its pre-move body AND the object-identity output showing `oc_runipd`, `agy_runipd` and `runner_shared` resolve to the same object. Paste the AST walk showing `runner_shared` imports NEITHER runner. Paste the actual commit that passed the pre-commit hooks, and paste the symmetry test passing AFTER that commit rather than only in the working tree, since the formatter acts at commit time. If a hook rejected the first attempt, paste that too along with the re-verified staged set.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the per-batch commit list, one concern group each. For each batch, paste the bare-suite failing NODE ID set after it, and show every set is identical to the baseline. Do not paste totals as the argument. If any batch changed the set, paste the investigation and its conclusion rather than a workaround.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the extended `_SHARED_NAMES` tuple and `CrossDriverSymmetryTests` PASSING, including its run-state assertion. Paste child 01's frozen set as updated, and paste it still FAILING on an unsanctioned addition (mutate, show the failure, revert). Paste proof the pin was updated in the same commit as the move it reflects, not in a later cleanup commit.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste TWO set differences, both printed EMPTY: residual minus classification-opencode-specific-plus-unclassified-plus-blocked, and the reverse. Paste the residual accounted for name by name. Paste the AST-measured agy-to-oc count showing it is still zero. Paste the oc-to-agy count before (47 or whatever E-01 measured) and after.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the ACTUAL output of the `aw backlog set` call closing `cnwy8g`, not a hand-edited file. Paste the item's `- Status:` line showing `done` and its workflow-history entry citing this plan. Paste `aw backlog check` clean. Paste a grep over all four plans in this Set showing NO `- Blocks-Release:` field was added. If a second behavioral defect was found, paste the new item's id and confirm it carries its own gate rather than this Set carrying one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the move cannot be split further without making the residual unverifiable. E-06's central evidence is that the set of names still imported oc-to-agy EXACTLY equals the classification's opencode-specific set, and that equality can only be checked once every host-neutral name has moved. A plan that moved half the names would leave a residual that matches nothing and would have to invent a partial expectation, which is precisely the unreviewable state this Set exists to leave behind. The work is nonetheless internally batched by concern group with a commit and a suite comparison per batch (E-04), so the reviewable unit is small even though the plan's completion criterion is whole-set.

Scope fence: touch ONLY the seven paths in `- Scope-Paths:`. Do NOT change any function body, docstring, type hint, or local name while moving. Do NOT move a name classified opencode-specific, UNSETTLED, or blocked. Do NOT add any import of either runner to `runner_shared`. Do NOT delete or weaken child 01's frozen set, `CrossDriverSymmetryTests`, or its run-state assertion. Do NOT touch a diverged symbol. Do NOT fix the `build_isolation_notice` re-fork. Do NOT add a `Blocks-Release` field. Do NOT move a name into `selectors` unless child 01's classification says so. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL AND RE-MEASURE BY AST, NEVER BY THE LINE NUMBERS OR THE COUNT IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day, and this import count moved from 40 to 47 in five days.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. THAT RE-VERIFICATION IS NOT BOILERPLATE ON THIS PLAN: a `ruff` rejection is EXPECTED here (it has already deleted six of these re-exports once), `pre-commit` stashes and restores unstaged changes when a hook rejects, and this repository has concurrent agents whose paths could be restored into your index. Never fix a polluted index with a bare `git reset` or `git stash`; unstage precisely with `git restore --staged <path>`. Prefer `aw commit <plan> -- <paths>`, which snapshots the index before staging and commits only the intersection. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 1f7xno --by-human --message ...`) before execution, and child 01 (`9kmbr0`) must read `executed` first, which the declared `- Item-Dependencies: executed:9kmbr0` enforces. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `cnwy8g`, which both children of this Set carry as `- From-Backlog:`. It closes HERE and not on child 01, because the layering correction it describes is delivered by the move, and closing it after a classification alone would claim a correction that had not happened.
