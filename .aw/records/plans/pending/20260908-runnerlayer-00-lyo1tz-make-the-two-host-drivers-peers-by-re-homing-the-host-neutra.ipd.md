# IPD: Make the two host drivers peers by re-homing the host-neutral half of the 47 oc-to-agy imports

- Date: 2026-09-08
- Kind: orchestrator
- Concern: One host driver depends on the other host's driver module, so the two are not peers. RE-MEASURED BY AST WALK at HEAD `44d4950d`: `agy_runipd.py` imports 47 names FROM `agent_workflows.oc_runipd` across eight `ImportFrom` statements (4 at `:266`, 21 at `:308`, 17 at `:333`, and one each at `:1399`, `:2371`, `:2380`, `:2387`, `:2399`), while `oc_runipd` imports ZERO names from `agy_runipd`. Counted by AST rather than grep, so an `as <same-name>` re-export is counted once and a string mention is not counted at all.
  THE COUNT HAS GROWN SINCE THE ITEM WAS FILED, WHICH IS THE ARGUMENT FOR DOING THIS NOW. Backlog `cnwy8g` recorded 40 on 2026-09-03; it is 47 five days later. Diffed against the item's list: `DriverError` and `build_isolation_notice` LEFT (the first because executed plan `818uru` moved it to `runner_shared`, verified by object identity across all three modules; the second because both hosts now define their own), and NINE arrived (`_read_kind`, `announce_run_order`, `build_verify_and_continue_notice`, `classify_recovery_disposition`, `resolve_prior_lane`, `route_recovery_turn`, `run_order_rationale`, `simulate_dispatch_order`, `update_execution_order`). So the coupling is actively accreting, at roughly 1.4 names per day, and most of the new arrivals are run-ordering and recovery-routing logic that is not opencode-specific at all.
  MOST OF THE 47 ARE NOT OPENCODE-SPECIFIC. By name: dependency-graph evaluation (`edge_satisfied`, `dependency_status`, `dependency_depth`, `queue_sort_key`, `cascade_dependency_blocked`, `parse_dependency_token`, `preflight_dependency_findings`, `enforce_dependency_preflight`, `DEPENDENCY_FATAL_RULES`, `dependency_reasons`, `dependency_target_id6`, `_read_item_dependencies`, `_artifact_owners`), backlog closing (`BacklogCloseVerdict`, `close_backlog_item`, `commit_backlog_close`, `evaluate_backlog_close`, `process_backlog_close`, `resolve_backlog_item`, `record_unclosed_backlog_items`, `unclosed_backlog_items`, `render_unclosed_report`, `_read_from_backlog`, `CARRIER_KIND_IPD`, `CARRIER_KIND_OTHER`), shutdown reporting (`emit_shutdown_report`, `register_signal_report`, `signal_report_callback`), suite checking (`run_suite_check`, `SuiteCheckResult`), run ordering (`announce_run_order`, `run_order_rationale`, `simulate_dispatch_order`, `update_execution_order`), and recovery routing (`route_recovery_turn`, `classify_recovery_disposition`, `resolve_prior_lane`). None of those is about opencode.
  THE ONE BEHAVIORAL DEFECT THIS LAYERING PRODUCED IS ALREADY FIXED, AND THAT MATTERS FOR THE GATE. The item's consequence 1 was `DriverError` existing as two distinct classes with a hand-written translation wrapper at `agy_runipd.py:87-93`, so `enforce_dependency_preflight` raised oc's class where agy's `main` caught agy's. VERIFIED FIXED at HEAD: `oc.DriverError is agy.DriverError is runner_shared.DriverError` -> `True`, and both drivers now bind it from `runner_shared` (`oc_runipd.py:176`, `agy_runipd.py:181`). Executed plan `818uru` did that, and its E-03 carried the release gate. So this Set is a LAYERING CORRECTION with no live behavioral defect of its own, which is exactly what the item's own gate paragraph says: "No `Blocks-Release` gate. This is a layering correction, not a live failure."
- Scope: The two children this correction needs. IN: (a) CLASSIFY all 47 names as host-neutral or genuinely opencode-specific, with the criterion stated and applied per name, and FREEZE the count so accretion becomes visible; (b) RE-HOME the host-neutral ones into `runner_shared.py` in reviewable batches, preserving the `as <same-name>` re-export form and keeping the oc-to-agy direction at zero. OUT: reconciling any DIVERGED symbol (`818uru` deferred those behind `lanectn` and its characterization baseline); changing any behavior whatsoever; adding a `Blocks-Release` gate this item deliberately does not carry.
- Scope-Paths: .aw/records/plans/pending/20260908-runnerlayer-01-9kmbr0-classify-all-47-oc-to-agy-imported-names-as-host-neutral-or.ipd.md, .aw/records/plans/pending/20260908-runnerlayer-02-1f7xno-re-home-the-host-neutral-names-into-runner-shared-in-reviewa.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: runnerlayer
- Order: 0
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: lyo1tz
- From-Backlog: cnwy8g

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `cnwy8g`. NO `- Blocks-Release:` FIELD IS CARRIED, and that is deliberate and faithful to the item rather than an omission: the item's own Gate section says "No `Blocks-Release` gate. This is a layering correction, not a live failure", and its one behavioral consequence (`DriverError`) was owned by `818uru` E-03, which carried the gate and has executed.
  EVERY CLAIM RE-MEASURED at HEAD `44d4950d`, and three of them changed. FIRST, the count is 47, not 40, across EIGHT `ImportFrom` statements rather than six; I diffed the item's explicit 40-name list against the live AST result and report exactly which two left and which nine arrived, because an executor working from the item's list would have looked for `DriverError` and `build_isolation_notice` and not found them. SECOND, THE ITEM'S SEQUENCING PRECONDITION IS SATISFIED: it says "Do this AFTER `818uru` executes", and `818uru` reads `- Status: executed` in `.aw/records/plans/executed/`, with its scope fence explicitly stating "Do NOT re-home the 40 oc-to-agy imports", so the work is genuinely unowned and this Set is not stepping on it. THIRD, the item's consequence 1 is DISCHARGED: `DriverError` is now ONE object shared by both drivers and `runner_shared` (measured by identity, not grep), so the hand-written translation wrapper the item cites at `agy_runipd.py:87-93` is no longer what lives there; that line range now holds a `render_stream` re-export comment. An executor citing the item's line numbers would have been reading the wrong code.
  THE ITEM'S CONSEQUENCE 2 IS STILL LIVE AND IS THE MAIN EXECUTION HAZARD. It records that `ruff` REMOVED 6 of these re-exports on a first commit attempt, caught only by a cross-driver symmetry test, which is why the `as <same-name>` form is load-bearing rather than cosmetic. `ruff` and `ruff-format` are both wired as pre-commit hooks in this repository, so the hazard is present on every commit this Set makes. The symmetry test that caught it is `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1179`), whose `test_the_implementation_is_shared_not_copied` asserts object identity for eleven of these names; it must be EXTENDED, never replaced.
  WHY TWO CHILDREN AND NOT ONE: the item's own first requirement is "Classify all 40 first ... Do not bulk-move", and a classification is a reviewable artifact in its own right. Splitting also means the expensive half (the move) is reviewed against a frozen classification rather than against a judgment made mid-move.

## Goal

Stop one host driver from being a library for the other, by moving the host-neutral names to the shared module and leaving only genuinely opencode-specific ones behind.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: drive the two children in order

- [ ] E-01 CONFIRM CHILD 01 (`9kmbr0`) IS EXECUTED before child 02 runs. The classification must be frozen before anything moves, because the item's own requirement is "Classify all 40 first ... Do not bulk-move". Read the child's `- Status:` on disk rather than trusting this table.
  - Depends on: none
  - Expected outcome: `9kmbr0` reads `- Status: executed` and sits in `.aw/records/plans/executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM CHILD 02 (`1f7xno`) IS EXECUTED and that the oc-to-agy import count is LOWER than it was, with the residual set being exactly the names child 01 classified as opencode-specific. A count that did not fall means nothing moved; a count that fell below the classification's prediction means something moved that was not sanctioned.
  - Depends on: E-01
  - Expected outcome: `1f7xno` reads `- Status: executed`; the AST-measured oc-to-agy count equals the classification's opencode-specific count; the agy-to-oc direction is still ZERO.
  - Execution state: pending

- [ ] E-03 CONFIRM BACKLOG `cnwy8g` WAS CLOSED BY CHILD 02, not by this parent, and that no `Blocks-Release` gate was invented for it along the way. The item deliberately carries none.
  - Depends on: E-02
  - Expected outcome: backlog `cnwy8g` reads `- Status: done`, closed by `1f7xno` which carries `- From-Backlog: cnwy8g`; no plan in this Set carries a `- Blocks-Release:` field; `aw backlog check` clean.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

BOTH children are AUTHORED and `aw ipd lint` conforming, each `to-review`. There are NO placeholder rows: an orchestrator whose table declares a row resolving to no plan refuses retirement (`unauthored-child-rows`).

| Order | Id | What it does | Depends on |
|---|---|---|---|
| 01 | `9kmbr0` | Classify all 47 imported names as host-neutral or genuinely opencode-specific, with the criterion stated once and applied per name, and add a guard that FREEZES the count so future accretion fails a test instead of being discovered five days later. Produces the classification as a reviewable artifact and moves nothing. | none |
| 02 | `1f7xno` | Re-home the host-neutral names into `runner_shared.py` in reviewable batches, preserving the `as <same-name>` re-export form, keeping `runner_common`-style admission (the shared module imports NEITHER runner), and extending the cross-driver symmetry test rather than replacing it. CLOSES backlog `cnwy8g`. | `executed:9kmbr0` |

Hard constraints both children inherit, stated once here:

- THE oc-to-agy DIRECTION MAY ONLY SHRINK, AND THE agy-to-oc DIRECTION MUST STAY AT ZERO. Measured at HEAD: 47 and 0. No child may create a cycle, and `runner_shared` must import NEITHER runner, which is `818uru` E-01's already-established admission rule.
- THE `as <same-name>` RE-EXPORT FORM IS LOAD-BEARING, NOT COSMETIC. The item records that `ruff` REMOVED 6 of these re-exports on a first commit attempt, caught only by a cross-driver symmetry test. `ruff` and `ruff-format` are pre-commit hooks in this repository, so this will happen again unless the form is preserved deliberately.
- EXTEND THE SYMMETRY GUARD, NEVER REPLACE IT. `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1179`) asserts object identity for eleven of these names via `test_the_implementation_is_shared_not_copied`. It is the test that caught the ruff deletion. Its `_SHARED_NAMES` tuple (`:1182`) is where a re-homed name is registered.
- NO BEHAVIOR CHANGE WHATSOEVER. This Set moves definitions. If a move would change what any function does, what any exception `main` catches, or what any test asserts, STOP and report rather than adjusting the behavior to fit the move. `818uru` set this precedent: it re-parented one exception's base class and declared that as its ONE permitted exception, in writing.
- DO NOT TOUCH A DIVERGED SYMBOL. `818uru` deliberately deferred reconciling class (c) diverged symbols behind `lanectn` and its own characterization baseline, and named the two `PlanRecord` definitions as staying put. A name that is DEFINED DIFFERENTLY in the two drivers is not in this Set's scope; only names agy IMPORTS from oc are.
- NO CHILD ADDS A `Blocks-Release` GATE. The item deliberately carries none, and its one behavioral consequence was discharged by `818uru` E-03. If a child discovers a SECOND behavioral defect traceable to this layering, the item's own instruction is to "gate it then", which means filing it, not gating this Set retroactively.
- CHILDREN ARE SEQUENTIAL because the classification must be frozen before the move, NOT because of file overlap. The runner isolates each item in its own worktree and returns changes through the merge-and-revalidate gate, so overlap with the other Sets declaring `oc_runipd.py`/`agy_runipd.py` is not a runtime hazard and must not be reported to a human as one.

## Completion criteria (the whole Set is done only when)

- All 47 names carry a recorded classification with a STATED criterion, so a later reader can re-derive the same answer (child 01).
- A guard FREEZES the oc-to-agy count, so the next name added to that import list fails a test rather than being discovered by an audit five days later (child 01).
- Every name classified host-neutral is DEFINED in `runner_shared.py` and resolves to ONE object from both drivers, asserted by object identity rather than grep (child 02).
- The residual oc-to-agy import set is EXACTLY the names classified opencode-specific, with no extras and no omissions (child 02).
- `runner_shared` imports NEITHER runner, and the agy-to-oc direction is still zero (child 02).
- No `as <same-name>` re-export was silently deleted by a formatter, demonstrated by a commit that passed the pre-commit hooks with the symmetry test green (child 02).
- No behavior changed: the full suite's failing NODE IDS are unchanged against a baseline measured in the executing worktree (both children).
- Backlog `cnwy8g` is closed by child 02 and no `Blocks-Release` gate was invented (child 02).

WHICH V-ITEM OWNS EACH CRITERION, stated because a criterion no `V-*` demands evidence for is an aspiration rather than a gate. THIS PARENT'S V-ITEMS OWN ONLY ORCHESTRATION: that each child reached `executed` in order, that the count fell to exactly the predicted residual, and that the backlog ledger was discharged by child 02. EVERY SUBSTANTIVE CRITERION is owned by a child's own `V-*`, where the pre-transition E/V checkpoint is enforced. This parent does NOT re-verify any of them; citing a child's pasted evidence is the correct discharge.

## Cross-IPD validation

- CID-1: THE DIRECTION IS MONOTONE. The AST-measured count of names `agy_runipd` imports from `oc_runipd` is 47 before this Set and strictly lower after; the count `oc_runipd` imports from `agy_runipd` is 0 before and 0 after. Measured by AST walk over `ImportFrom` nodes, never by grep.
- CID-2: NO CYCLE. `runner_shared` imports neither `oc_runipd` nor `agy_runipd`, asserted by AST rather than by import success (a lazy in-function import succeeds at module load and is still a layering violation).
- CID-3: RESIDUAL EQUALS CLASSIFICATION. The set of names still imported oc-to-agy after child 02 is exactly the set child 01 classified opencode-specific. A set difference in EITHER direction is a failed CID-3, printed as two empty sets rather than asserted in prose.
- CID-4: IDENTITY, NOT TEXT. Every re-homed name resolves to the SAME object from `oc_runipd`, `agy_runipd` and `runner_shared`. Grep cannot distinguish a shared object from a textually identical copy, which is how `render_stream` was re-forked.
- CID-5: NO BEHAVIOR CHANGE. The bare suite's failing NODE IDS are identical before and after the Set, against a baseline measured in the executing worktree. Totals are not evidence; node ids are.
- CID-6: THE FORMATTER DID NOT WIN. A commit made through the repository's own pre-commit hooks left every `as <same-name>` re-export intact, demonstrated by the symmetry test passing AFTER that commit rather than only in the working tree.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN. This parent's three items each CONFIRM a child's terminal state or the ledger; no classification, no move, and no measurement of its own lives here. The runner retires an orchestrator once every child is `executed` and deliberately SKIPS the pre-transition E/V checkpoint, so work parked on a parent is marked complete having never been performed.
- `818uru` IS THE PRECEDENT AND THE PRECONDITION. It created `runner_shared.py`, moved 34 common symbols as a PURE MOVE verified by AST-identity plus object-identity assertions, declared its ONE permitted behavior change in writing, and explicitly fenced out "re-homing the 40 oc-to-agy imports". It reads `- Status: executed`. Read it before designing either child.
- THE MODULE NAME WAS DECIDED. `818uru` OQ-01 resolved `runner_common` -> `runner_shared` by maintainer ruling, because the latter "reads as the module shared by the host runners, whereas `runner_common` can be misread as a generic dumping ground". The item still says `runner_common`; the real module is `runner_shared.py`.
- `ruff` WILL DELETE AN UNUSED RE-EXPORT. Both `ruff` and `ruff-format` are pre-commit hooks here. The `as <same-name>` form is what makes a re-export survive, and the repository documents the previous loss of six of them.
- THE SYMMETRY TEST IS THE REAL GUARD. `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1179`) checks presence AND object identity for eleven of these names, and separately asserts a shared module "must not learn about the runner or its run state". Extend it.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses), while a lane worktree shows roughly 32 environmental failures.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `agy_runipd.py:266`, `:308`, `:333`, `:1399`, `:2371`, `:2380`, `:2387`, `:2399` | `agy_runipd` imports 47 names from `oc_runipd` across EIGHT statements; `oc_runipd` imports 0 from agy. The item recorded 40 across six. | AST walk over `ImportFrom` nodes in both modules |
| F-2 | HIGH | measured | THE COUPLING IS ACCRETING at roughly 1.4 names per day. Diffed against the item's list: `DriverError` and `build_isolation_notice` left; `_read_kind`, `announce_run_order`, `build_verify_and_continue_notice`, `classify_recovery_disposition`, `resolve_prior_lane`, `route_recovery_turn`, `run_order_rationale`, `simulate_dispatch_order`, `update_execution_order` arrived. | set difference between the item's 40 and the live 47 |
| F-3 | DISCHARGED | `oc_runipd.py:176`, `agy_runipd.py:181`, `runner_shared.py:159` | The item's ONE behavioral consequence is FIXED: `oc.DriverError is agy.DriverError is runner_shared.DriverError` -> `True`, both bound from `runner_shared`. `818uru` E-03 did it and carried the release gate. So this Set has no live behavioral defect, which is why it carries no gate. | identity check; source read |
| F-4 | STALE-CITATION | `agy_runipd.py:84-96` | The item cites a hand-written `DriverError` translation wrapper at `agy_runipd.py:87-93`. That code is GONE; the range now holds a `render_stream` re-export comment. An executor navigating by the item's line numbers reads the wrong code. | source read |
| F-5 | HIGH | pre-commit config; item consequence 2 | `ruff` and `ruff-format` are both pre-commit hooks, and `ruff` previously REMOVED 6 of these re-exports on a first commit attempt, caught only by a cross-driver symmetry test. The `as <same-name>` form is load-bearing. | `.pre-commit-config.yaml`; the item's recorded incident |
| F-6 | MED | `tests/test_runner_item_dependencies.py:1179`, `:1182` | `CrossDriverSymmetryTests` asserts presence and OBJECT IDENTITY for eleven of these names and separately forbids a shared module learning about run state. This is the guard to extend. | source read |
| F-7 | MED | `.aw/records/plans/executed/20260903-rununify-02-818uru-...ipd.md` | THE SEQUENCING PRECONDITION IS SATISFIED: `818uru` is `executed` and its scope fence says "Do NOT re-home the 40 oc-to-agy imports", so the work is real and unowned. | that plan's `- Status:` and fence text |
| F-8 | MED | `818uru` OQ-01 | The module is `runner_shared.py`, not `runner_common.py` as the item says; the rename was a maintainer ruling with a stated reason. | that plan's resolved OQ |
| F-9 | LOW | measured | Most of the 47 are plainly host-neutral by name: 13 dependency-graph, 12 backlog-closing, 4 run-ordering, 3 recovery-routing, 3 shutdown-reporting, 2 suite-checking. So the classification is expected to move most of the list, and a classification that keeps most names in oc would be the surprising result worth explaining. | grouped the live 47 by concern |

## Proposed changes (ordered, validatable)

1. Child 01 (`9kmbr0`) classifies all 47 names against a stated criterion and freezes the count with a guard, moving nothing.
2. Child 02 (`1f7xno`) re-homes the host-neutral ones into `runner_shared.py` in reviewable batches, preserving re-export form, keeping the shared module free of runner imports, and extending the symmetry guard. It closes backlog `cnwy8g`.

## Deferred / out of scope (with reason)

- RECONCILING ANY DIVERGED SYMBOL. `818uru` deliberately deferred class (c) diverged symbols behind `lanectn` and its own characterization baseline, and named the two `PlanRecord` definitions as staying. This Set moves only names agy IMPORTS from oc; a name defined differently in both is a different problem.
- ANY BEHAVIOR CHANGE. Named in the fence because a move that "tidies" a body while relocating it is the most likely way this Set breaks something. `818uru` set the precedent of declaring its single permitted exception in writing.
- ADDING A `Blocks-Release` GATE. The item explicitly carries none and explains why. If a second behavioral defect is traced to this layering, the item's instruction is to gate it then, which means filing a new item.
- THE REVERSE DIRECTION. `oc_runipd` imports zero names from agy and this Set must keep it there. Nothing to do, stated so a reader does not look for it.
- SPLITTING `oc_runipd.py` OR `agy_runipd.py` GENERALLY. The `rununify` Set (`5e4sb6`, approved, with unauthored children 03+) owns the broader unification. This Set does the ONE thing that Set explicitly fenced out.

## Scope check

- Over-scope: none. This parent edits no source file; its `Scope-Paths` are the two children it authored.
- Under-scope: stated rather than left as `none`. After this Set the drivers are peers with respect to IMPORTS, but they still each carry their own diverged symbols and their own `SUCCESS_STATES`-style duplicated constants (measured equal but not identical), which `rununify` owns.

## Required tests / validation

Each child carries its own tests. This parent runs none: its three items read child status and the ledger from disk. `python3 -m pytest` bare is each child's obligation, with the baseline measured in the executing worktree and failing NODE IDS compared, never totals. CID-5 makes an unchanged failing-node-id set the Set's central evidence, since this is a pure-move Set.

## Spec / documentation sync

N/A for this parent, with the reason stated rather than asserted: this Set relocates definitions and changes no documented contract, no operator-facing string, and no run-record shape. No spec governs which module a host-neutral helper lives in.
ONE THING FOR CHILD 02 TO CHECK RATHER THAN ASSUME: if any re-homed name is NAMED in a spec, a README, or a docstring that cites its module path, that citation becomes wrong when the definition moves. Grep the `.aw/records/specs/` tree and the package docstrings for the re-homed names before finalizing, and fix any stale module-path citation as documentation rather than leaving the tree self-contradictory. Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: What is the criterion for host-neutral, and who arbitrates a genuinely ambiguous name?

- Blocking: no
- Status: open
- Owner: child 01 (`9kmbr0`) executor, escalating to the maintainer only for names the criterion cannot settle
- Resolution or deferral rationale: NOT blocking this parent, which performs no work; it is child 01's first task and is recorded there as that child's own OQ. The criterion is not obvious for every name: `run_suite_check` runs a test suite, which is host-neutral in principle, but its timeout and cwd choices were tuned against one driver's behavior; `announce_run_order` prints through a shared formatter and is plainly neutral; `pinned_child_env` and `pinned_module_argv` pin a NESTED `aw` invocation, which sounds host-specific but the in-tree comment at `agy_runipd.py:262-265` says both drivers must stay symmetric and that a second copy is how a previous half-pin diverged, so those are neutral by their own documentation. A defensible criterion is: a name is opencode-specific only if its BODY references an opencode-only concept (the `opencode` binary, its CLI flags, its session format). Child 01 should state the criterion it used and list any name the criterion could not settle, rather than silently choosing.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste child `9kmbr0`'s `- Status:` line and its path, read at validation time, showing `executed` and `.aw/records/plans/executed/`. Paste the classification it produced (all 47 names with their verdicts) and the criterion it stated, since that artifact is what child 02 is reviewed against.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste child `1f7xno`'s `- Status:` line and path showing `executed`. Paste the AST-measured oc-to-agy import count BEFORE (47) and AFTER, and the agy-to-oc count both times (0 and 0). Paste the SET DIFFERENCE between the residual imports and child 01's opencode-specific classification, printed as two empty sets; a nonempty difference in either direction is a failed V-02. Paste the AST assertion that `runner_shared` imports neither runner.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste backlog `cnwy8g`'s `- Status:` line showing `done`, and name WHICH child closed it, confirming this parent closed none. Paste `aw backlog check` clean. Paste a grep over all four plans in this Set showing NO `- Blocks-Release:` field was added, since the item deliberately carries none and inventing one would be a false gate.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: this parent commits nothing and edits no source file. Each child commits ONLY the files it changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index, and since this Set's commits will be hook-rejected at least once if a formatter strips a re-export. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved lyo1tz --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. The runner retires this orchestrator automatically once both children read `executed` on disk; if a human executes the Set by hand instead, work the three E-items above in order.
