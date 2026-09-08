# IPD: Classify all 47 oc-to-agy imported names as host-neutral or opencode-specific and freeze the count

- Date: 2026-09-08
- Kind: child
- Concern: The coupling between the two host drivers is invisible and growing, and nobody can act on it because no classification exists. RE-MEASURED BY AST WALK at HEAD `44d4950d`: `agy_runipd.py` imports 47 names FROM `agent_workflows.oc_runipd` across eight `ImportFrom` statements (4 at `:266`, 21 at `:308`, 17 at `:333`, one each at `:1399`, `:2371`, `:2380`, `:2387`, `:2399`), while `oc_runipd` imports ZERO from agy. Backlog `cnwy8g` recorded 40 on 2026-09-03; five days later it is 47, which is roughly 1.4 names per day, and nothing in the test suite noticed.
  THE ACCRETION IS THE DEFECT THIS CHILD FIXES, AND IT IS MEASURABLE. Diffed the item's explicit 40-name list against the live AST result: `DriverError` and `build_isolation_notice` LEFT (the first because executed plan `818uru` moved it to `runner_shared`, verified `oc.DriverError is agy.DriverError is runner_shared.DriverError` -> `True`; the second because both hosts now define their own, at `oc_runipd.py:4717` and `agy_runipd.py:2348`), and NINE arrived: `_read_kind`, `announce_run_order`, `build_verify_and_continue_notice`, `classify_recovery_disposition`, `resolve_prior_lane`, `route_recovery_turn`, `run_order_rationale`, `simulate_dispatch_order`, `update_execution_order`. Every one of the nine is run-ordering or recovery-routing logic with nothing opencode-specific about it.
  WHY A CLASSIFICATION IS A DELIVERABLE AND NOT A STEP. Backlog `cnwy8g`'s first requirement is verbatim: "Classify all 40 first. Some are genuinely opencode-specific and must stay in `oc_runipd` ...; the rest belong in the shared library. Do not bulk-move." A move reviewed against a classification made during the move is a move reviewed against nothing. Grouped by concern, the live 47 are 13 dependency-graph names, 12 backlog-closing, 4 run-ordering, 3 recovery-routing, 3 shutdown-reporting, 2 suite-checking, and a remainder including the nested-`aw` pin and the tool-identity guard. Most are plainly neutral, which means the classification's real work is identifying the FEW that are not and saying why.
  A PAIRWISE SHARING CHECK IS ALSO BLIND TO THESE 47, which is the item's consequence 3: a check asking "do both runners DEFINE this?" sees an imported symbol as already shared, so the true shared surface is understated by up to 47 names.
- Scope: Produce the classification as a durable reviewable artifact (all 47 names, a stated criterion, a verdict per name, and the reason for every name the criterion could not settle), and add a guard that FREEZES the oc-to-agy count so the next addition fails a test instead of being discovered by an audit. MOVES NOTHING and changes no behavior. EXCLUDES the re-homing itself (child 02 `1f7xno`); excludes any diverged symbol (`818uru` deferred those); excludes the reverse direction, which is already zero.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_layering.py, tests/test_runner_item_dependencies.py
- Item-Dependencies: none
- Status: to-review
- Set: runnerlayer
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 9kmbr0
- From-Backlog: cnwy8g

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `cnwy8g` as Order 01 of the `runnerlayer` Set. NO `- Blocks-Release:` FIELD, deliberately and faithfully to the item, whose Gate section says "No `Blocks-Release` gate. This is a layering correction, not a live failure" and records that its one behavioral consequence (`DriverError`) was owned by `818uru` E-03, which has executed. Inventing a gate here would be a false claim about release risk.
  MEASUREMENTS THAT CHANGED THE PLAN. FIRST, 47 not 40, across eight statements not six, and I report the exact delta so an executor working from the item's list is not hunting for `DriverError` (gone, and its cited wrapper at `agy_runipd.py:87-93` is gone too; that range now holds a `render_stream` re-export comment). SECOND, the item's sequencing precondition is SATISFIED: `818uru` reads `- Status: executed` and its scope fence says "Do NOT re-home the 40 oc-to-agy imports", so this work is real and unowned. THIRD, the module is `runner_shared.py`, not `runner_common.py` as the item says: `818uru` OQ-01 renamed it by maintainer ruling because `runner_common` "can be misread as a generic dumping ground". FOURTH, and this is why the freeze guard is E-03 rather than a nice-to-have: the coupling grew by nine names in five days with a green suite throughout, so a classification without a guard would be stale within the week.
  WHY THIS CHILD MOVES NOTHING. The item says "Do not bulk-move" and requires classification first. Keeping the move out means this child's entire diff is a classification artifact plus tests, which is reviewable in one pass, and child 02 is then reviewed against a frozen input rather than against a judgment being made as it goes.

## Goal

Produce a defensible per-name classification of all 47 oc-to-agy imports, and make the count impossible to grow silently again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: state the criterion, then apply it

- [ ] E-01 STATE THE CRITERION FOR HOST-NEUTRAL ONCE, IN WRITING, BEFORE CLASSIFYING ANYTHING, and site it where the classification lives so a later reader can re-derive the same verdicts. A classification without a stated rule is a list of opinions and cannot be reviewed.
  A DEFENSIBLE CRITERION, offered rather than imposed: a name is OPENCODE-SPECIFIC only if its BODY references an opencode-only concept, meaning the `opencode` binary, its CLI flags, its session format, or its JSON stream shape. Everything else is host-neutral. Judge the BODY, not the name: three of these names sound host-specific and are documented as neutral. `pinned_child_env` and `pinned_module_argv` pin a NESTED `aw` invocation, and the in-tree comment at `agy_runipd.py:262-265` says both drivers must stay symmetric and that "a second copy is exactly how the previous inert half-pin came to differ from what it looked like it did". `announce_run_order` prints through the shared `render_stream` formatter and holds no opencode concept at all.
  NAME THE HARD CASES RATHER THAN DECIDING THEM QUIETLY. `run_suite_check` is neutral in principle but its timeout and cwd were tuned against one driver's behavior; `_artifact_owners` delegates to `check_engine` and is neutral; `_read_kind`/`_read_from_backlog`/`_read_item_dependencies` are front-matter readers whose siblings `_read_id`/`_read_status` were ALREADY moved to `selectors` by `2r306y`, which is direct precedent for where they belong. Where the criterion genuinely cannot settle a name, record it as UNSETTLED with the reason and escalate; do not force a verdict to make the list tidy.
  - Depends on: none
  - Expected outcome: one written criterion, sited with the classification; the judge-the-body rule stated; at least the three documented sound-specific-but-neutral cases called out so a future reader does not re-litigate them.
  - Execution state: pending

- [ ] E-02 CLASSIFY ALL 47 NAMES against that criterion, producing a durable artifact that lists every name, its verdict, and a one-line reason. Derive the list of 47 by AST WALK at execution time, never from this plan: the count was 40 five days before this plan was written and will likely have moved again.
  GROUP BY CONCERN, because the groups are where the argument lives and a flat list of 47 is unreviewable. Measured groups at HEAD: 13 dependency-graph (`edge_satisfied`, `dependency_status`, `dependency_depth`, `dependency_reasons`, `dependency_target_id6`, `queue_sort_key`, `cascade_dependency_blocked`, `parse_dependency_token`, `preflight_dependency_findings`, `enforce_dependency_preflight`, `DEPENDENCY_FATAL_RULES`, `_read_item_dependencies`, `_artifact_owners`), 12 backlog-closing (`BacklogCloseVerdict`, `CARRIER_KIND_IPD`, `CARRIER_KIND_OTHER`, `close_backlog_item`, `commit_backlog_close`, `evaluate_backlog_close`, `process_backlog_close`, `resolve_backlog_item`, `record_unclosed_backlog_items`, `unclosed_backlog_items`, `render_unclosed_report`, `_read_from_backlog`), 4 run-ordering (`announce_run_order`, `run_order_rationale`, `simulate_dispatch_order`, `update_execution_order`), 3 recovery-routing (`route_recovery_turn`, `classify_recovery_disposition`, `resolve_prior_lane`), 3 shutdown-reporting (`emit_shutdown_report`, `register_signal_report`, `signal_report_callback`), 2 suite-checking (`run_suite_check`, `SuiteCheckResult`), plus `ToolIdentityError`, `assert_child_tool_identity`, `pinned_child_env`, `pinned_module_argv`, `_read_kind`, `build_verify_and_continue_notice`, `render_runs_pointer`, `collect_earned_paths`, `run_earned_paths`, `integration_is_earned`.
  RECORD WHETHER EACH NAME IS ALREADY A RE-EXPORT OF SOMETHING ELSE. Several of these may be names `oc_runipd` itself imports from a third module and merely re-exports; such a name needs no move at all, only a re-point of agy's import, which is materially cheaper than a definition move. Distinguishing them is the single most useful thing this classification can do for child 02's sizing.
  - Depends on: E-01
  - Expected outcome: a durable artifact classifying every name derived by AST at execution time, grouped by concern, each with a verdict and a one-line reason, and each marked as a real definition in `oc_runipd` or as a pass-through re-export; unsettled names listed as unsettled.
  - Execution state: pending

### Task group 2: make the count impossible to grow silently

- [ ] E-03 ADD A GUARD THAT FREEZES THE oc-to-agy IMPORT COUNT, so adding a 48th name fails a test rather than being found by an audit five days later. This is the item's consequence 3 turned into a gate: a pairwise "do both runners define this?" check sees an imported symbol as already shared, so nothing today notices accretion.
  ASSERT BY AST OVER `ImportFrom` NODES, NOT BY GREP. Grep counts a string mention and miscounts an `as <same-name>` re-export; the AST does neither. The measurement that produced 47 is the measurement the guard must reproduce, or the guard and the plan disagree from birth.
  FREEZE THE SET, NOT ONLY THE NUMBER. A guard on the count alone passes when one name is added and another removed, which is exactly the churn measured over the last five days (two left, nine arrived). Pin the SORTED SET of names, so any change is surfaced with its name.
  ASSERT THE REVERSE DIRECTION IS ZERO in the same guard. It is zero today, and a future edit making it nonzero would create a cycle; catching that costs one line here and is otherwise nobody's job.
  MAKE THE FAILURE MESSAGE CONSTRUCTIVE, not merely prohibitive. This repository records that a gate saying only "X is forbidden" gets complied with by DELETION. The message must name the added symbol and say the constructive action: put a host-neutral symbol in `runner_shared`, and if it is genuinely opencode-specific, add it to the frozen set with a reason. A guard whose only advice is "do not do that" will be satisfied by someone deleting a needed re-export.
  - Depends on: E-02
  - Expected outcome: a test pinning the SORTED SET of oc-to-agy imported names, measured by AST, asserting the reverse direction is zero, and failing with a message that names the added symbol and states both constructive options.
  - Execution state: pending

- [ ] E-04 MUTATION-CHECK THE GUARD. A guard that cannot fail is not evidence. Add a name to agy's import list from oc, show the guard FAILS and its message names that symbol, revert, show it passes. Then REMOVE a name and show the guard also fails, since the set is pinned rather than the count.
  - Depends on: E-03
  - Expected outcome: two mutations demonstrated (one addition, one removal), each failing with a message naming the changed symbol, each passing after revert.
  - Execution state: pending

### Task group 3: do not disturb what already works

- [ ] E-05 PROVE THIS CHILD CHANGED NO BEHAVIOR. It moves nothing and its only source-file touches are the classification's siting and any comment. The suite's failing NODE IDS must be identical against a baseline measured in the executing worktree.
  DO NOT REPLACE THE EXISTING SYMMETRY GUARD. `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1179`) already asserts presence AND object identity for eleven of these names via `test_the_implementation_is_shared_not_copied` (`:1201`), and it is the test that caught `ruff` deleting six re-exports. This child may EXTEND it or leave it alone; it may not rewrite it, and it must not weaken the separate assertion there that a shared module "must not learn about the runner or its run state".
  COMPARE NODE IDS, NEVER TOTALS. A bare `python3 -m pytest` on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which asserts live plan statuses and drifts as plans advance), while a lane worktree shows roughly 32 environmental failures because several tests read live repo state. Totals are noise here; node ids are the signal.
  - Depends on: E-03
  - Expected outcome: the bare suite's failing node-id set identical before and after, measured in the executing worktree and both sets pasted; the existing symmetry guard untouched or extended, never rewritten.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `818uru` IS THE PRECEDENT AND THE PRECONDITION. It created `runner_shared.py`, moved 34 symbols as a PURE MOVE verified by AST-identity plus object-identity assertions, declared its ONE permitted behavior change in writing, and explicitly fenced out "re-homing the 40 oc-to-agy imports". It reads `- Status: executed`.
- THE MODULE IS `runner_shared.py`, NOT `runner_common.py`. `818uru` OQ-01 renamed it by maintainer ruling with a stated reason. The backlog item predates the rename.
- THE FRONT-MATTER READERS HAVE PRECEDENT FOR WHERE THEY BELONG: `2r306y` moved `_read_id` and `_read_status` to `selectors.py` because "both host runners used to carry their own private copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers." `_read_kind`, `_read_from_backlog` and `_read_item_dependencies` are their siblings.
- SOME NAMES SOUND HOST-SPECIFIC AND ARE DOCUMENTED AS NEUTRAL. `agy_runipd.py:262-265` records that the nested-`aw` pin must stay symmetric across drivers and that a second copy is how a previous half-pin silently diverged. Judge the body, not the name.
- `ruff` WILL DELETE AN UNUSED RE-EXPORT. Both `ruff` and `ruff-format` are pre-commit hooks here, and the item records `ruff` removing six of these re-exports on a first commit attempt, caught only by the cross-driver symmetry test. The `as <same-name>` form is load-bearing.
- A GATE MUST NAME THE CONSTRUCTIVE FIX. Recorded in this repository's own guidance: a message saying only that something is forbidden gets complied with by deletion. E-03's failure message is written to that rule.
- Suite bare: `python3 -m pytest`. Do not add `-n0`, a second `-q`, or `-p no:randomly`; `pyproject.toml` `addopts` already supplies the intended flags.

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `agy_runipd.py:266`, `:308`, `:333`, `:1399`, `:2371`, `:2380`, `:2387`, `:2399` | 47 names imported oc-to-agy across EIGHT statements; 0 agy-to-oc. The item recorded 40 across six. | AST walk over `ImportFrom` nodes in both modules |
| F-2 | HIGH | measured | THE COUPLING GREW BY NINE NAMES IN FIVE DAYS with a green suite throughout, and two left. So a count-only guard would be fooled by churn and a classification without a guard goes stale within a week. | set difference between the item's 40 and the live 47 |
| F-3 | HIGH | nothing | NO test today notices a new oc-to-agy import. The existing symmetry guard checks that eleven NAMED symbols are shared; it cannot see a 48th name appearing. | read `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` |
| F-4 | DISCHARGED | `runner_shared.py:159`; `oc_runipd.py:176`; `agy_runipd.py:181` | `DriverError` is now ONE object across both drivers and `runner_shared`, so the item's only behavioral consequence is fixed and this Set carries no release gate. | `oc.DriverError is agy.DriverError is runner_shared.DriverError` -> `True` |
| F-5 | STALE-CITATION | `agy_runipd.py:84-96` | The item cites a `DriverError` translation wrapper at `:87-93`; that code is gone and the range now holds a `render_stream` re-export comment. Navigating by the item's line numbers reads the wrong code. | source read |
| F-6 | MED | `oc_runipd.py:4717`, `agy_runipd.py:2348` | `build_isolation_notice` left the import list because BOTH hosts now define it, which is a re-fork rather than an improvement. Worth recording in the classification even though re-forks are `2r306y`'s subject, not this Set's. | source read of both definitions |
| F-7 | MED | `tests/test_runner_item_dependencies.py:1179`, `:1182`, `:1201` | `CrossDriverSymmetryTests` asserts presence and OBJECT IDENTITY for eleven of these names and separately forbids a shared module learning about run state. It is the guard that caught the ruff deletion; extend, never replace. | source read |
| F-8 | MED | `2r306y` | `_read_id`/`_read_status` were already moved to `selectors.py` with a stated one-definition rationale, which is direct precedent for the three remaining `_read_*` names in this list. | that plan's record |
| F-9 | LOW | grouped | 13 dependency-graph, 12 backlog-closing, 4 run-ordering, 3 recovery-routing, 3 shutdown-reporting, 2 suite-checking names, none of which is about opencode. So the expected classification moves most of the list, and a result keeping most names in oc is the surprising outcome that would need explaining. | grouped the live 47 by concern |

## Proposed changes (ordered, validatable)

1. E-01 states the criterion in writing, with the judge-the-body rule and the three documented sound-specific-but-neutral cases.
2. E-02 classifies all 47 names derived by AST at execution time, grouped by concern, marking pass-through re-exports separately from real definitions.
3. E-03 freezes the SORTED SET by AST, asserts the reverse direction is zero, and fails with a constructive message naming the added symbol.
4. E-04 mutation-checks the guard on both an addition and a removal.
5. E-05 proves no behavior changed by comparing failing node-id sets, leaving the existing symmetry guard intact.

## Deferred / out of scope (with reason)

- THE RE-HOMING ITSELF. Child 02 (`1f7xno`). Split because the item requires classification first ("Do not bulk-move") and because a move reviewed against a classification made during the move is reviewed against nothing.
- RECONCILING ANY DIVERGED SYMBOL. `818uru` deferred class (c) diverged symbols behind `lanectn` and its characterization baseline, and named the two `PlanRecord` definitions as staying. This child classifies only names agy IMPORTS from oc.
- FIXING THE `build_isolation_notice` RE-FORK (F-6). It is a re-fork, which is `2r306y`'s subject, not this Set's. Recorded in the classification so it is not lost, but not fixed here.
- ANY MOVE, ANY BEHAVIOR CHANGE, AND ANY REWRITE OF THE EXISTING SYMMETRY GUARD.
- ADDING A `Blocks-Release` GATE. The item explicitly carries none and explains why.
- THE REVERSE DIRECTION as a problem to solve: it is already zero. E-03 merely pins it there.

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY for siting the classification and any comment it needs. Do NOT move a definition, change a body, or edit an import list in this child.
- Under-scope: stated rather than left as `none`. After this child nothing has moved: the drivers are still not peers. That is child 02's work, and this child's guard makes the gap visible in the meantime rather than closing it.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. The new guard belongs in a new `tests/test_runner_layering.py` rather than inside the dependency-focused module, because it is about module layering and not about dependencies; `tests/test_runner_item_dependencies.py` is declared in `Scope-Paths` only in case the existing symmetry guard is EXTENDED, and if it is not touched, acknowledge that at finalize rather than editing it to justify the declaration.

## Spec / documentation sync

N/A, with the reason stated rather than asserted: this child relocates nothing, changes no operator-facing string, no run-record shape, and no documented contract. It adds a classification artifact and a test. No spec governs which module a host-neutral helper lives in.
ONE THING TO CHECK RATHER THAN ASSUME: if the classification artifact is written as prose intended for a human reader rather than as code or test data, it is user-facing prose and must contain no em or en dashes, per this repository's authoring rule. If it is test data or a code comment, that rule does not apply. Decide which it is and say so.

## Open questions

### OQ-01: Which names does the criterion fail to settle, and who arbitrates?

- Blocking: no
- Status: open
- Owner: this plan's executor for the list, the maintainer for any name the criterion cannot settle
- Resolution or deferral rationale: NOT blocking, because E-01 and E-02 already require that an unsettleable name be recorded as UNSETTLED with its reason rather than forced, so the plan completes with or without an arbitration. The likely candidates, named so the executor does not have to rediscover them: `run_suite_check` and `SuiteCheckResult` (neutral in principle, tuned against one driver's timeout and cwd behavior); `integration_is_earned`, `collect_earned_paths` and `run_earned_paths` (integration is host-neutral in concept but the `integpath` Set is actively editing that surface, so moving them may collide); and `build_verify_and_continue_notice` and `render_runs_pointer` (wording functions, which `render_stream` would arguably own rather than `runner_shared`). An UNSETTLED verdict is a legitimate output of this child; a forced one is not.

### OQ-02: Should a pass-through re-export be counted as coupling at all?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 requires the distinction be RECORDED either way, so child 02 gets the information regardless of how the question is answered. It matters for the guard's semantics: if `oc_runipd` merely re-exports a name it imports from a third module, agy importing it from oc is still a layering violation (agy is reaching through oc to reach that module) but the FIX is a one-line re-point rather than a definition move. Whether the frozen set counts such names is a judgement about what the guard is for. Recommend counting them, since the direction is what the guard protects, and recording them as cheap to fix.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the criterion as written and where it is sited. Paste the judge-the-body rule and the three sound-specific-but-neutral cases as recorded. State whether the artifact is human prose or test data, and if prose, confirm it contains no em or en dashes.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the FULL classification: every name, its group, its verdict, its one-line reason, and whether it is a real definition in `oc_runipd` or a pass-through re-export. Paste the AST measurement that produced the name list AT EXECUTION TIME, and if the count differs from 47, say so and explain; both drivers are edited by live runs and the number will move. Paste the UNSETTLED list, even if empty, so a reader can see the criterion was applied rather than stretched.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the guard as written, showing it measures by AST over `ImportFrom` nodes and pins the SORTED SET rather than only the count, and that it asserts the reverse direction is zero. Paste it PASSING. Paste the failure message text and confirm it names the changed symbol and states BOTH constructive options (put it in `runner_shared`, or add it to the frozen set with a reason).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste BOTH mutations in full. For the addition: the added import, the FAILING output with the message naming that symbol, the revert, the passing output. For the removal: the same four. A V-04 pasting only the addition is incomplete, because the removal is what proves the SET is pinned rather than the count.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the bare-suite failing NODE ID sets before and after, measured in the executing worktree, and show they are identical. Do not paste totals as the argument. Paste `tests/test_runner_item_dependencies.py` passing, and state whether `CrossDriverSymmetryTests` was extended or left alone; if left alone, acknowledge the declared-but-unmodified `Scope-Paths` entry rather than editing the file to justify it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the four paths in `- Scope-Paths:`. Do NOT move any definition. Do NOT change any function body. Do NOT edit either driver's import list. Do NOT rewrite `CrossDriverSymmetryTests` or weaken its assertion that a shared module must not learn about run state. Do NOT touch a diverged symbol. Do NOT fix the `build_isolation_notice` re-fork. Do NOT add a `Blocks-Release` field. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL AND RE-MEASURE BY AST, NEVER BY THE LINE NUMBERS OR THE COUNT IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day, and this import count itself moved from 40 to 47 in five days. Derive the name list yourself.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 9kmbr0 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do NOT close backlog `cnwy8g` here: nothing has been re-homed after this child, and closing it would claim a layering correction that has not happened. Child 02 (`1f7xno`) closes it.
