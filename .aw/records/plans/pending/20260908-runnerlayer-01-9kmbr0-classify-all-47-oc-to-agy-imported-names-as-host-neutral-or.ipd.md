# IPD: Classify every oc-to-agy imported name as host-neutral or opencode-specific and freeze the set

- Date: 2026-09-08
- Kind: child
- Concern: The coupling between the two host drivers is invisible and growing, and nobody can act on it because no classification exists. RE-MEASURED BY AST WALK at HEAD `00143b02` (review, 2026-09-09): `agy_runipd.py` imports **48** names FROM `agent_workflows.oc_runipd` across eight `ImportFrom` statements (now at `:273`, `:315`, `:340`, `:1385`, `:2310`, `:2319`, `:2326`, `:2338`), while `oc_runipd` imports ZERO from agy. Backlog `cnwy8g` recorded 40 on 2026-09-03; it was 47 at authoring on 2026-09-08 (verified: an AST walk of `agy_runipd.py` at commit `44d4950d` gives exactly 47) and 48 one day later.
  THE FIGURE 47 IS AN AUTHORING SNAPSHOT AND MUST NOT BE USED AS A PASS CRITERION. The 48th name is `dependency_status_detailed`, and it is MISSING from this plan's own E-02 enumeration, which itemizes exactly 47 and omits it. Verified by two-way set difference at review: live-minus-enumerated is exactly `{dependency_status_detailed}` and enumerated-minus-live is EMPTY, so nothing else drifted. DERIVE THE COUNT BY AST AT EXECUTION TIME and treat every number in this plan as prose. This is not pedantry: a `V-02` that demanded "the 47" would fail a correct measurement of 48, and a classification silently scoped to 47 leaves one name unclassified, after which child 02's residual set difference cannot balance.
  THE MISSED NAME IS THE SHARPEST ARGUMENT THIS PLAN HAS FOR ITS OWN GUARD. `dependency_status_detailed` is precisely the name whose ABSENCE from the symmetry guard's `_SHARED_NAMES` tuple let that guard pass over agy's real, broken copy for months, which `03ie04` E-04 fixed by adding it. So the one name every enumeration in this Set forgot is the one whose omission from a guard already caused the exact class of defect this Set exists to prevent.
  THE ACCRETION IS THE DEFECT THIS CHILD FIXES, AND IT IS MEASURABLE. Diffed the item's explicit 40-name list against the live AST result: `DriverError` and `build_isolation_notice` LEFT (the first because executed plan `818uru` moved it to `runner_shared`, verified `oc.DriverError is agy.DriverError is runner_shared.DriverError` -> `True`; the second because both hosts now define their own, at `oc_runipd.py:4773` and `agy_runipd.py:2287`), and TEN arrived: `_read_kind`, `announce_run_order`, `build_verify_and_continue_notice`, `classify_recovery_disposition`, `dependency_status_detailed`, `resolve_prior_lane`, `route_recovery_turn`, `run_order_rationale`, `simulate_dispatch_order`, `update_execution_order`. Every one of the ten is dependency, run-ordering or recovery-routing logic with nothing opencode-specific about it.
  WHY A CLASSIFICATION IS A DELIVERABLE AND NOT A STEP. Backlog `cnwy8g`'s first requirement is verbatim: "Classify all 40 first. Some are genuinely opencode-specific and must stay in `oc_runipd` ...; the rest belong in the shared library. Do not bulk-move." A move reviewed against a classification made during the move is a move reviewed against nothing. Grouped by concern, the live 48 are 14 dependency-graph names, 12 backlog-closing, 4 run-ordering, 3 recovery-routing, 3 shutdown-reporting, 2 suite-checking, and a remainder including the nested-`aw` pin and the tool-identity guard. Most are plainly neutral, which means the classification's real work is identifying the FEW that are not and saying why.
  A PAIRWISE SHARING CHECK IS ALSO BLIND TO THESE, which is the item's consequence 3: a check asking "do both runners DEFINE this?" sees an imported symbol as already shared, so the true shared surface is understated by the whole import set.
- Scope: Produce the classification as a durable reviewable artifact (EVERY name in the AST-measured set, a stated criterion, a verdict per name, and the reason for every name the criterion could not settle), and add a guard that FREEZES the oc-to-agy import set so the next addition fails a test instead of being discovered by an audit. MOVES NOTHING and changes no behavior. EXCLUDES the re-homing itself (child 02 `1f7xno`); excludes any diverged symbol (`818uru` deferred those); excludes the reverse direction, which is already zero.
  THE SET SIZE IS "WHATEVER THE AST SAYS AT EXECUTION TIME", NOT A NUMBER FROM THIS PLAN. Stated in Scope because it defines what "every name" obliges: the count was 40 at filing, 47 at authoring and 48 at review, so a run that classifies "the 47" has left a name unclassified. Classify the set you MEASURE, report the count you found, and note any delta against this plan's prose. A count differing from 48 is CORRECT and expected, not a discrepancy to reconcile away.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_layering.py, tests/test_runner_item_dependencies.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: runnerlayer
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 9kmbr0
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: cnwy8g

## Workflow history
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-09 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-C01..PR-C09 all FIXED; readiness go-pending-approval

- 2026-09-09 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-C01..PR-C09, all nine FIXED, none deferred. Readiness `go-pending-approval`. Record: `.aw/records/reviews/20260908-runnerlayer-01-9kmbr0-classify-all-47-oc-to-agy-imported-names-as-host-neutral-or.review.md`. `aw ipd lint --phase author` conformed BEFORE semantic review and `--phase review-finalize` conforms after, so nothing here was structural. DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on RE-MEASURING rather than re-reading.
  THE DESIGN IS SOUND AND SURVIVED WHOLESALE. Classification-before-move is the right split, the criterion offered is the only checkable formulation on the table, and freezing the SET rather than the count is correct for exactly the churn measured. Confirmed by measurement: the reverse direction really is zero, all 48 names really are `oc_runipd`-owned definitions, `DriverError` really is one object, and the criterion's three worked examples hold.
  TWO DEFECTS WOULD HAVE PRODUCED A GUARD THAT FROZE THE WRONG SET, which is worse than no guard because it certifies a stale surface. FIRST (PR-C02, BLOCKER), FIVE of the 48 imports are NESTED inside delegating wrapper functions, so the obvious `for node in tree.body` implementation under-reports by five and still passes a naive add/revert mutation check; measured further, `agy.<name> is oc.<name>` is FALSE for all five, so an identity-based audit cannot see that tier at all. E-03 now mandates `ast.walk` and E-04 adds a nested-import mutation that a body-only guard fails. SECOND (PR-C03, HIGH), the 48 imported names carry only 45 distinct BOUND names because four wrappers share the local `_shared`, so a set keyed on `asname or name` collapses them and reports no change when one is added or removed; the pin is now specified on `alias.name`.
  THE PLAN'S CENTRAL NUMBER WAS ALSO STALE AND WAS THE SAME OMISSION ITS PARENT CAUGHT (PR-C01, HIGH). An AST walk gives 48, not 47, and the missing name is `dependency_status_detailed`, absent from this plan's E-02 enumeration; two-way set difference confirms it is the only drift, and an AST walk at the authoring commit `44d4950d` confirms 47 was correct THEN. It is also the exact name whose absence from `_SHARED_NAMES` let the symmetry guard pass over agy's real broken copy for months, so the omission reproduces in this plan's paperwork the failure the plan exists to prevent. Every count here is now framed as a snapshot to re-derive, and V-02 forbids a literal count as a pass criterion.
  ALSO FIXED: OQ-02 is RESOLVED by measurement rather than left open, since there are ZERO pass-through re-exports, and the useful distinction (three binding tiers, 21/22/5) now replaces it in E-02 and F-13 (PR-C04); one name's body hardcodes `closed by aw oc run` while agy calls the same function, a real live provenance defect now recorded and explicitly deferred rather than silently misclassified (PR-C05); every import-statement line citation in the plan was wrong one day after authoring, and the symmetry guard's anchors had moved roughly 440 lines and hold TWELVE names not eleven (PR-C06, PR-C07); the suite baseline named a test that now passes, while the two real failures are environmental and one of them is another agent's untracked files in this shared checkout, which the fence now forbids "fixing" (PR-C08); and E-04's mutation check needed an explicit revert proof, since it transiently edits the highest-contention file in the repository (PR-C09). Two decisions recorded (D-1, D-2); both `Reversible: yes`. OQ-01 deliberately LEFT OPEN: the per-name verdicts are this child's own deliverable, and its collision risk was checked and cited rather than pre-decided.

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `cnwy8g` as Order 01 of the `runnerlayer` Set. NO `- Blocks-Release:` FIELD, deliberately and faithfully to the item, whose Gate section says "No `Blocks-Release` gate. This is a layering correction, not a live failure" and records that its one behavioral consequence (`DriverError`) was owned by `818uru` E-03, which has executed. Inventing a gate here would be a false claim about release risk.
  MEASUREMENTS THAT CHANGED THE PLAN. FIRST, 47 not 40, across eight statements not six, and I report the exact delta so an executor working from the item's list is not hunting for `DriverError` (gone, and its cited wrapper at `agy_runipd.py:87-93` is gone too; that range now holds a `render_stream` re-export comment). SECOND, the item's sequencing precondition is SATISFIED: `818uru` reads `- Status: executed` and its scope fence says "Do NOT re-home the 40 oc-to-agy imports", so this work is real and unowned. THIRD, the module is `runner_shared.py`, not `runner_common.py` as the item says: `818uru` OQ-01 renamed it by maintainer ruling because `runner_common` "can be misread as a generic dumping ground". FOURTH, and this is why the freeze guard is E-03 rather than a nice-to-have: the coupling grew by nine names in five days with a green suite throughout, so a classification without a guard would be stale within the week.
  WHY THIS CHILD MOVES NOTHING. The item says "Do not bulk-move" and requires classification first. Keeping the move out means this child's entire diff is a classification artifact plus tests, which is reviewable in one pass, and child 02 is then reviewed against a frozen input rather than against a judgment being made as it goes.

## Goal

Produce a defensible per-name classification of every oc-to-agy import in the AST-measured set, and make the set impossible to change silently again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: state the criterion, then apply it

- [x] E-01 STATE THE CRITERION FOR HOST-NEUTRAL ONCE, IN WRITING, BEFORE CLASSIFYING ANYTHING, and site it where the classification lives so a later reader can re-derive the same verdicts. A classification without a stated rule is a list of opinions and cannot be reviewed.
  A DEFENSIBLE CRITERION, offered rather than imposed: a name is OPENCODE-SPECIFIC only if its BODY references an opencode-only concept, meaning the `opencode` binary, its CLI flags, its session format, or its JSON stream shape. Everything else is host-neutral. Judge the BODY, not the name: three of these names sound host-specific and are documented as neutral. `pinned_child_env` and `pinned_module_argv` pin a NESTED `aw` invocation, and the in-tree comment at `agy_runipd.py:269-272` says both drivers must stay symmetric and that "a second copy is exactly how the previous inert half-pin came to differ from what it looked like it did". `announce_run_order` prints through the shared `render_stream` formatter and holds no opencode concept at all.
  APPLY THE CRITERION TO CODE, NOT TO PROSE, AND KNOW WHAT THAT EXCLUDES. A docstring or comment mentioning `aw oc run` is NOT a body reference to an opencode concept, and this distinction decides real cases rather than being hypothetical. MEASURED AT REVIEW by stripping comments from each of the 48 definitions and scanning the remainder: exactly THREE contain an `oc` token, and only ONE of them is in executable code. `queue_sort_key` (`oc_runipd.py:3838`) mentions `aw oc run` only in a COMMENT recording a measured incident, and `render_runs_pointer` (`:1563`) only in a DOCSTRING whose point is that `aw oc runs` does not exist; both are neutral. `process_backlog_close` (`:1426`) is the one real case: its commit message STRING is `f"closed by aw oc run: IPD ..."` at `:1474`, which agy's own call site at `agy_runipd.py:3907` would write verbatim, so agy-driven runs already record a wrong provenance today. That is a genuine finding to RECORD, not a reason to call the function opencode-specific, since the host label is a parameterizable value rather than an opencode concept. Do not fix it here; this child moves and changes nothing.
  NAME THE HARD CASES RATHER THAN DECIDING THEM QUIETLY. `run_suite_check` is neutral in principle but its docstring records that the primary-checkout choice was measured against lane behavior; `_artifact_owners` delegates to `check_engine` and is neutral; `_read_kind`/`_read_from_backlog`/`_read_item_dependencies` are front-matter readers whose siblings `_read_id`/`_read_status` were ALREADY moved to `selectors` by `2r306y`, which is direct precedent for where they belong. Where the criterion genuinely cannot settle a name, record it as UNSETTLED with the reason and escalate; do not force a verdict to make the list tidy.
  ONE NAME IS SETTLED BY THE CRITERION AGAINST THE SHAPE OF ITS BODY, and saying so here saves the executor a wrong turn. `ToolIdentityError` is a CLASS, defined only in `oc_runipd` (`:406`) while its sibling `StallTimeout` is deliberately defined in BOTH drivers (`oc_runipd.py:380`, `agy_runipd.py:703`) with an in-tree note saying that is on purpose. So its verdict is neutral by the criterion (nothing in it is about opencode) while its MOVE is not a plain function relocation, because both drivers' `except` clauses bind it. Record the verdict and flag the move shape for child 02's callee map; do not resolve the move here.
  - Depends on: none
  - Expected outcome: one written criterion, sited with the classification; the judge-the-body rule stated, INCLUDING that a comment or docstring mention is not a body reference; at least the three documented sound-specific-but-neutral cases called out so a future reader does not re-litigate them.
  - Execution state: performed

- [x] E-02 CLASSIFY EVERY NAME IN THE MEASURED SET against that criterion, producing a durable artifact that lists every name, its verdict, and a one-line reason. Derive the list by AST WALK at execution time, never from this plan: the count was 40 at filing, 47 at authoring and 48 at review, and it will likely have moved again.
  GROUP BY CONCERN, because the groups are where the argument lives and a flat list is unreviewable. Measured groups at review HEAD `00143b02`: 14 dependency-graph (`edge_satisfied`, `dependency_status`, `dependency_status_detailed`, `dependency_depth`, `dependency_reasons`, `dependency_target_id6`, `queue_sort_key`, `cascade_dependency_blocked`, `parse_dependency_token`, `preflight_dependency_findings`, `enforce_dependency_preflight`, `DEPENDENCY_FATAL_RULES`, `_read_item_dependencies`, `_artifact_owners`), 12 backlog-closing (`BacklogCloseVerdict`, `CARRIER_KIND_IPD`, `CARRIER_KIND_OTHER`, `close_backlog_item`, `commit_backlog_close`, `evaluate_backlog_close`, `process_backlog_close`, `resolve_backlog_item`, `record_unclosed_backlog_items`, `unclosed_backlog_items`, `render_unclosed_report`, `_read_from_backlog`), 4 run-ordering (`announce_run_order`, `run_order_rationale`, `simulate_dispatch_order`, `update_execution_order`), 3 recovery-routing (`route_recovery_turn`, `classify_recovery_disposition`, `resolve_prior_lane`), 3 shutdown-reporting (`emit_shutdown_report`, `register_signal_report`, `signal_report_callback`), 2 suite-checking (`run_suite_check`, `SuiteCheckResult`), plus `ToolIdentityError`, `assert_child_tool_identity`, `pinned_child_env`, `pinned_module_argv`, `_read_kind`, `build_verify_and_continue_notice`, `render_runs_pointer`, `collect_earned_paths`, `run_earned_paths`, `integration_is_earned`. THIS ENUMERATION IS A REVIEW-TIME SNAPSHOT: reconcile it against your own measurement and report any delta rather than trusting it.
  RECORD WHETHER EACH NAME IS ALREADY A RE-EXPORT OF SOMETHING ELSE. THE ANSWER WAS MEASURED AT REVIEW AND IS ZERO, which retires this sub-question rather than leaving the executor to rediscover it: all 48 names are REAL DEFINITIONS in `oc_runipd` (checked by walking oc's own `ImportFrom` and definition nodes; the intersection of the 48 with oc's imported names is EMPTY). So there is no cheap re-point tier, and child 02's sizing is 48 definition moves minus whatever this classification excludes. Re-measure and confirm rather than assuming, since a future edit could introduce one.
  RECORD INSTEAD THE DISTINCTION THAT DOES EXIST, BECAUSE IT IS WHAT CHILD 02 ACTUALLY NEEDS. The 48 split three ways by HOW agy binds them, and the three tiers have materially different move costs. (a) 21 are PURE MODULE-LEVEL RE-EXPORTS whose bound name agy never references: `BacklogCloseVerdict`, `CARRIER_KIND_IPD`, `CARRIER_KIND_OTHER`, `DEPENDENCY_FATAL_RULES`, `_artifact_owners`, `close_backlog_item`, `collect_earned_paths`, `commit_backlog_close`, `dependency_depth`, `dependency_reasons`, `dependency_target_id6`, `edge_satisfied`, `evaluate_backlog_close`, `preflight_dependency_findings`, `record_unclosed_backlog_items`, `render_unclosed_report`, `resolve_backlog_item`, `run_earned_paths`, `signal_report_callback`, `simulate_dispatch_order`, `unclosed_backlog_items`. These are the `as <same-name>` form `ruff` deletes. (b) 22 are module-level and CONSUMED in agy's own body, so a move must keep the binding reachable. (c) 5 are LAZY IMPORTS INSIDE A DELEGATING WRAPPER: `enforce_dependency_preflight` (`agy_runipd.py:1385`), `classify_recovery_disposition` (`:2310`), `resolve_prior_lane` (`:2319`), `build_verify_and_continue_notice` (`:2326`), `route_recovery_turn` (`:2338`). Tier (c) is the one that would be missed: measured, `agy.<name> is oc.<name>` is FALSE for all five (agy exposes its own wrapper function), whereas it is TRUE for the module-level tiers. So an identity-based guard cannot see tier (c) at all, which is exactly why E-03 must measure by AST over `ImportFrom` nodes and must include nested ones.
  - Depends on: E-01
  - Expected outcome: a durable artifact classifying every name derived by AST at execution time, grouped by concern, each with a verdict and a one-line reason, and each marked with its BINDING TIER (pure module-level re-export, module-level consumed, or lazy-import delegating wrapper) plus a re-measured confirmation that it is a real definition in `oc_runipd` rather than a pass-through; unsettled names listed as unsettled.
  - Execution state: performed

### Task group 2: make the count impossible to grow silently

- [x] E-03 ADD A GUARD THAT FREEZES THE oc-to-agy IMPORT SET, so adding a name fails a test rather than being found by an audit days later. This is the item's consequence 3 turned into a gate: a pairwise "do both runners define this?" check sees an imported symbol as already shared, so nothing today notices accretion.
  ASSERT BY AST OVER `ImportFrom` NODES, NOT BY GREP, AND WALK THE WHOLE TREE RATHER THAN THE MODULE BODY. Grep counts a string mention and miscounts an `as <same-name>` re-export; the AST does neither. Use `ast.walk`, not a loop over `tree.body`: measured, 43 of the 48 imports are module-level and FIVE are nested inside delegating wrapper functions (`agy_runipd.py:1385`, `:2310`, `:2319`, `:2326`, `:2338`), so a body-only walk silently under-reports by five and freezes the wrong set.
  PIN THE ORIGINAL NAMES, NOT THE BOUND ALIASES. Measured, the 48 alias entries carry only 45 distinct BOUND names, because four wrappers bind their import to the same local `_shared` and one binds `_oc_enforce_dependency_preflight`. A set built from `asname or name` therefore collapses to 45 and would report a false "no change" when one of those four is added or removed. Build the set from `alias.name`, which is 48 distinct values.
  FREEZE THE SET, NOT ONLY THE NUMBER. A guard on the count alone passes when one name is added and another removed, which is exactly the churn measured over the last six days (two left, ten arrived). Pin the SORTED SET of names, so any change is surfaced with its name.
  ASSERT THE REVERSE DIRECTION IS ZERO in the same guard. It is zero today (measured), and a future edit making it nonzero would create a cycle; catching that costs one line here and is otherwise nobody's job. Note what already exists so this is an addition rather than a duplicate: `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` (`:308`) asserts the SUBSTRING `"import oc_runipd" not in agy_src`, which the live code passes ONLY because every real import uses the symbol-level `from agent_workflows.oc_runipd import` spelling; `agy_runipd.py:1379-1384` documents that the spelling is chosen deliberately to keep that guard meaningful for the blanket-dependency case it targets. So the existing guard is a substring check on a spelling, not a count of the coupling, and it is not what E-03 duplicates. Do not weaken or rewrite it.
  MAKE THE FAILURE MESSAGE CONSTRUCTIVE, not merely prohibitive. This repository records that a gate saying only "X is forbidden" gets complied with by DELETION. The message must name the added symbol and say the constructive action: put a host-neutral symbol in `runner_shared`, and if it is genuinely opencode-specific, add it to the frozen set with a reason. A guard whose only advice is "do not do that" will be satisfied by someone deleting a needed re-export.
  THE PIN IS A MOVING TARGET BY DESIGN, SO SAY SO IN THE TEST ITSELF. Child 02 changes this set on purpose, one batch at a time, and its E-05 already requires updating the pin in the SAME commit as each move. Write the frozen-set comment to state that shrinking it via a sanctioned move is expected and correct while growing it is the regression, so a later maintainer does not read a legitimate child-02 edit as tampering, and does not read the pin as a licence to delete it when it goes red.
  - Depends on: E-02
  - Expected outcome: a test pinning the SORTED SET of ORIGINAL oc-to-agy imported names, measured by `ast.walk` so nested imports are included, asserting the reverse direction is zero, failing with a message that names the changed symbol and states both constructive options, and carrying a comment distinguishing a sanctioned shrink from a regression.
  - Execution state: performed

- [x] E-04 MUTATION-CHECK THE GUARD. A guard that cannot fail is not evidence. Add a name to agy's import list from oc, show the guard FAILS and its message names that symbol, revert, show it passes. Then REMOVE a name and show the guard also fails, since the set is pinned rather than the count.
  ADD A THIRD MUTATION THAT PROVES THE NESTED-IMPORT COVERAGE, because it is the one E-03 requirement a module-body-only guard would silently fail while still passing the first two mutations. Add a throwaway import INSIDE a function body (the shape of the five real wrappers at `agy_runipd.py:1385`, `:2310`, `:2319`, `:2326`, `:2338`) and show the guard catches it too. Without this mutation, a guard written with `for node in tree.body` passes E-04 and freezes a set that is short by five.
  MUTATE A DIFFERENT SYMBOL FOR THE REMOVAL THAN FOR THE ADDITION, and prefer removing a PURE re-export from tier (a), since those are the names `ruff` actually deletes and therefore the regression the removal half exists to catch.
  REVERT BY RESTORING THE FILE, NOT BY RE-EDITING FROM MEMORY, and confirm with `git diff --exit-code` on both drivers before finishing. These are the two highest-contention files in the repository and a residual mutation left in either one would be attributed to whoever committed next.
  - Depends on: E-03
  - Expected outcome: three mutations demonstrated (a module-level addition, a nested in-function addition, and a removal of a pure re-export), each failing with a message naming the changed symbol, each passing after revert, with `git diff --exit-code` clean on both drivers at the end.
  - Execution state: performed

### Task group 3: do not disturb what already works

- [x] E-05 PROVE THIS CHILD CHANGED NO BEHAVIOR. It moves nothing and its only source-file touches are the classification's siting and any comment. The suite's failing NODE IDS must be identical against a baseline measured in the executing worktree.
  DO NOT REPLACE THE EXISTING SYMMETRY GUARD. `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` (`:1617`) already asserts presence AND object identity for TWELVE of these names via `test_the_implementation_is_shared_not_copied` (`:1656`), with the pinned tuple `_SHARED_NAMES` at `:1633`. FIND THEM BY NAME, NOT BY LINE: these anchors moved roughly 440 lines since this plan was authored, which is why the earlier `:1179`/`:1201`/`:1182` citations in this plan were wrong. It is the test that caught `ruff` deleting six re-exports. This child may EXTEND it or leave it alone; it may not rewrite it, and it must not weaken the separate assertion in that module that a shared rule module "must not learn about the runner or its run state" (`:1602`, `:1613`).
  THE TWELFTH NAME IS `dependency_status_detailed`, ADDED BY `03ie04` E-04 FOR A MEASURED REASON, and the in-tree comment at `:1620-1632` states it: its absence from that tuple is what let the guard pass over agy's real copy of the function for months. That comment also records what identity does NOT catch (a copy assigned over the re-export at import time) and that the hole is accepted. Do not "simplify" the tuple and do not read its comment as stale.
  COMPARE NODE IDS, NEVER TOTALS. Measured bare on main at review HEAD `00143b02`: `2 failed, 5918 passed, 3 skipped, 2 xfailed`. Both failures are ENVIRONMENTAL, not this plan's, and neither is the `tests/test_orchestrator_retirement.py` failure this plan previously named: that module now gives `112 passed`. The two are `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (it scans the working tree and trips over 189 untracked `opencode-recovery/*.md` transcripts, which are another agent's files and MUST NOT be touched) and `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` (a 30-second subprocess timeout under a loaded parallel run; it gives `7 passed` when run alone). DO NOT QUOTE THESE FIGURES AS YOUR BASELINE either: measure in the executing worktree, since a lane sees a different `.aw/state` and a different untracked set.
  - Depends on: E-03
  - Expected outcome: the bare suite's failing node-id set identical before and after, measured in the executing worktree and both sets pasted; the existing symmetry guard untouched or extended, never rewritten; any residual failure identified as environmental by name rather than absorbed into a total.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `818uru` IS THE PRECEDENT AND THE PRECONDITION. It created `runner_shared.py`, moved 34 symbols as a PURE MOVE verified by AST-identity plus object-identity assertions, declared its ONE permitted behavior change in writing, and explicitly fenced out "re-homing the 40 oc-to-agy imports". It reads `- Status: executed`.
- THE MODULE IS `runner_shared.py`, NOT `runner_common.py`. `818uru` OQ-01 renamed it by maintainer ruling with a stated reason. The backlog item predates the rename.
- THE FRONT-MATTER READERS HAVE PRECEDENT FOR WHERE THEY BELONG: `2r306y` moved `_read_id` and `_read_status` to `selectors.py` because "both host runners used to carry their own private copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers." `_read_kind`, `_read_from_backlog` and `_read_item_dependencies` are their siblings.
- SOME NAMES SOUND HOST-SPECIFIC AND ARE DOCUMENTED AS NEUTRAL. `agy_runipd.py:269-272` records that the nested-`aw` pin must stay symmetric across drivers and that a second copy is how a previous half-pin silently diverged. Judge the body, not the name.
- `ruff` WILL DELETE AN UNUSED RE-EXPORT. Both `ruff` and `ruff-format` are pre-commit hooks here, and the item records `ruff` removing six of these re-exports on a first commit attempt, caught only by the cross-driver symmetry test. The `as <same-name>` form is load-bearing, and 21 of the 48 names are exactly that form with no other reference in agy, so they are the exposed ones.
- A GATE MUST NAME THE CONSTRUCTIVE FIX. Recorded in this repository's own guidance: a message saying only that something is forbidden gets complied with by deletion. E-03's failure message is written to that rule.
- THE COUPLING HAS THREE BINDING SHAPES, NOT ONE, and only two are visible to an identity check. 43 imports are module-level and 5 are lazy imports inside delegating wrappers; measured, `agy.<name> is oc.<name>` is False for all five wrappers and True for the module-level re-exports. Any guard or audit built on object identity alone is blind to the wrapper tier, which is why E-03 is specified as an AST walk.
- AN EXISTING GUARD ALREADY WATCHES THE REVERSE DIRECTION, BY SUBSTRING. `tests/test_review_findings_cascade.py:308` asserts `"import oc_runipd" not in agy_src`, and `agy_runipd.py:1379-1384` documents that the symbol-level import spelling is chosen deliberately so that guard stays meaningful for the blanket-dependency case. E-03 adds a set-and-direction pin; it does not replace that check.
- Suite bare: `python3 -m pytest`. Do not add `-n0`, a second `-q`, or `-p no:randomly`; `pyproject.toml` `addopts` already supplies the intended flags. Measured at review: `2 failed, 5918 passed, 3 skipped, 2 xfailed`, both failures environmental and named in E-05.
- THE REPOSITORY IS A SHARED CHECKOUT AND CURRENTLY HOLDS ANOTHER PARTY'S UNTRACKED FILES. 189 `opencode-recovery/*.md` transcripts are present and are what makes the reporting-contract test red. They are not this plan's, must not be deleted, moved, or committed, and their presence must not be "fixed" to make a baseline green.

## Findings

| Id | Severity | Location (F-1..F-9 re-measured at review HEAD `00143b02`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `agy_runipd.py:273`, `:315`, `:340`, `:1385`, `:2310`, `:2319`, `:2326`, `:2338` | 48 names imported oc-to-agy across EIGHT statements; 0 agy-to-oc. The item recorded 40 across six; this plan was authored at 47. | AST walk over `ImportFrom` nodes in both modules |
| F-2 | HIGH | measured | THE COUPLING GREW BY TEN NAMES IN SIX DAYS with a green suite throughout, and two left. So a count-only guard would be fooled by churn and a classification without a guard goes stale within a week. | set difference between the item's 40 and the live 48 |
| F-3 | HIGH | nothing | NO test today notices a new oc-to-agy import. The existing symmetry guard checks that twelve NAMED symbols are shared; it cannot see a 49th name appearing. | read `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` |
| F-4 | DISCHARGED | `runner_shared.py:170`; `oc_runipd.py:185`; `agy_runipd.py:188` | `DriverError` is now ONE object across both drivers and `runner_shared`, so the item's only behavioral consequence is fixed and this Set carries no release gate. | `oc.DriverError is agy.DriverError is runner_shared.DriverError` -> `True` |
| F-5 | STALE-CITATION | `agy_runipd.py:84-96` | The item cites a `DriverError` translation wrapper at `:87-93`; that code is gone and the range now holds a `render_stream` re-export comment. Navigating by the item's line numbers reads the wrong code. | source read |
| F-6 | MED | `oc_runipd.py:4773`, `agy_runipd.py:2287` | `build_isolation_notice` left the import list because BOTH hosts now define it, which is a re-fork rather than an improvement. Worth recording in the classification even though re-forks are `2r306y`'s subject, not this Set's. | source read of both definitions |
| F-7 | MED | `tests/test_runner_item_dependencies.py:1617`, `:1633`, `:1656` | `CrossDriverSymmetryTests` asserts presence and OBJECT IDENTITY for TWELVE of these names and the module separately forbids a shared rule module learning about run state (`:1602`). It is the guard that caught the ruff deletion; extend, never replace. | source read; counted `_SHARED_NAMES` in-process |
| F-8 | MED | `2r306y` | `_read_id`/`_read_status` were already moved to `selectors.py` (`selectors.py:246`, `:251`) with a stated one-definition rationale, which is direct precedent for the three remaining `_read_*` names in this list. | that plan's record; `tests/test_runner_refork_guard.py:105-106` tables both as `selectors`-owned |
| F-9 | LOW | grouped | 14 dependency-graph, 12 backlog-closing, 4 run-ordering, 3 recovery-routing, 3 shutdown-reporting, 2 suite-checking names, none of which is about opencode. So the expected classification moves most of the list, and a result keeping most names in oc is the surprising outcome that would need explaining. | grouped the live 48 by concern |
| F-10 | HIGH | this plan's own E-02 enumeration | THE 48TH NAME WAS MISSING FROM THIS PLAN AND IT IS THE WORST POSSIBLE ONE TO MISS. `dependency_status_detailed` appears in no list here; two-way set difference confirms it is the only drift. It is also the exact name whose absence from `_SHARED_NAMES` let the symmetry guard pass over agy's real broken copy for months (`03ie04` E-04), so the omission reproduces in this Set's paperwork the very failure the Set exists to prevent. | AST walk vs. the E-02 list; `tests/test_runner_item_dependencies.py:1639-1641` |
| F-11 | HIGH | `agy_runipd.py:1385`, `:2310`, `:2319`, `:2326`, `:2338` | FIVE OF THE 48 IMPORTS ARE NESTED INSIDE FUNCTION BODIES, so a guard iterating `tree.body` freezes a set short by five and still passes a naive mutation check. Measured further: `agy.<name> is oc.<name>` is FALSE for all five (agy exposes its own delegating wrapper), so an identity-based audit is blind to this tier entirely. | `ast.walk` vs. body-only walk; identity checked in-process |
| F-12 | MED | `agy_runipd.py:315`, `:340`, `:1385` | THE BOUND-NAME SET IS 45 WHILE THE IMPORTED-NAME SET IS 48: four wrappers bind to the same local `_shared` and one to `_oc_enforce_dependency_preflight`. A frozen set keyed on `asname or name` collapses those four into one entry and reports no change when one is added or removed. Pin `alias.name`. | counted both sets in-process |
| F-13 | MED | `oc_runipd.py` (all 48 definitions) | THERE IS NO PASS-THROUGH RE-EXPORT TIER AT ALL: all 48 are real definitions in `oc_runipd`, so E-02's "which are cheap re-points?" question has the answer zero. The distinction that DOES exist and matters for child 02's sizing is the binding tier: 21 pure module-level re-exports, 22 module-level consumed, 5 lazy wrapper imports. | walked oc's own `ImportFrom` and definition nodes; intersection with the 48 is empty |
| F-14 | MED | `oc_runipd.py:1474` | ONE NAME'S BODY CARRIES A HARDCODED HOST LABEL: `process_backlog_close` writes the commit message `closed by aw oc run: ...`, and agy calls the SAME shared function (`agy_runipd.py:3907`), so an antigravity-driven run already records a false provenance today. It is still host-NEUTRAL by the criterion (a host label is a parameter, not an opencode concept), but it is a real live defect to RECORD rather than fix here. | stripped comments from all 48 bodies and scanned; only this one has an `oc` token in executable code |
| F-15 | LOW | `oc_runipd.py:3838`, `:1563` | TWO MORE NAMES MENTION `aw oc run` IN PROSE ONLY: `queue_sort_key` in a comment recording an incident, `render_runs_pointer` in a docstring saying `aw oc runs` does not exist. Both are neutral. Recorded so the executor applies the criterion to CODE and does not misclassify them on a grep. | same scan, comment-stripped vs. raw |
| F-16 | LOW | `oc_runipd.py:406`, `:380`, `agy_runipd.py:703` | `ToolIdentityError` is a CLASS whose sibling `StallTimeout` is DELIBERATELY defined in both drivers, with an in-tree note saying so. Neutral by the criterion, but its move shape is an exception binding rather than a function relocation, which is child 02's problem and worth flagging in the classification. | source read of all three definitions |
| F-17 | LOW | `tests/test_reporting_contract.py`, `tests/test_runner_backlog_close.py` | THE SUITE BASELINE IN THIS PLAN NAMED THE WRONG FAILING TEST. Measured `2 failed, 5918 passed`; `tests/test_orchestrator_retirement.py` now gives `112 passed`. The two real failures are environmental: an untracked-file scan tripping over 189 `opencode-recovery/*.md` files belonging to another agent, and a 30s subprocess timeout that passes in isolation. | bare `python3 -m pytest`; each module re-run alone |

## Proposed changes (ordered, validatable)

1. E-01 states the criterion in writing, with the judge-the-body rule (code, not comments or docstrings) and the documented sound-specific-but-neutral cases.
2. E-02 classifies every name in the AST-measured set at execution time, grouped by concern, recording each name's BINDING TIER and confirming it is a real definition rather than a pass-through.
3. E-03 freezes the SORTED SET of ORIGINAL names by `ast.walk` (so nested imports count), asserts the reverse direction is zero, and fails with a constructive message naming the changed symbol.
4. E-04 mutation-checks the guard on a module-level addition, a nested in-function addition, and a removal, reverting cleanly each time.
5. E-05 proves no behavior changed by comparing failing node-id sets, leaving the existing symmetry guard intact.

## Deferred / out of scope (with reason)

- THE RE-HOMING ITSELF. Child 02 (`1f7xno`). Split because the item requires classification first ("Do not bulk-move") and because a move reviewed against a classification made during the move is reviewed against nothing.
  - Carrier: 1f7xno
- RECONCILING ANY DIVERGED SYMBOL. `818uru` deferred class (c) diverged symbols behind `lanectn` and its characterization baseline, and named the two `PlanRecord` definitions as staying. This child classifies only names agy IMPORTS from oc.
  - Carrier-Declined: not this Set's obligation to carry. `818uru` (executed) deferred the diverged symbols behind `lanectn` and its characterization baseline, so the obligation already sits with that work; this child only classifies names agy IMPORTS from oc, and a diverged symbol is by definition one agy does NOT import. Inventing a carrier here would duplicate an obligation another plan already owns.
- FIXING THE `build_isolation_notice` RE-FORK (F-6). It is a re-fork, which is `2r306y`'s subject, not this Set's. Recorded in the classification so it is not lost, but not fixed here.
  - Carrier-Declined: NOTHING IS OUTSTANDING, verified at execution rather than assumed. F-6 recorded `build_isolation_notice` LEAVING the import list because both hosts define their own. Re-measured here: it is absent from the 56-name set, so it is not part of this plan's subject at all, and the re-fork question belongs to the re-fork guard's own domain (`tests/test_runner_refork_guard.py`, owner `2r306y`). There is no residual obligation for a carrier to hold.
- ANY MOVE, ANY BEHAVIOR CHANGE, AND ANY REWRITE OF THE EXISTING SYMMETRY GUARD.
  - Carrier-Declined: a SCOPE FENCE, not an obligation. This row forbids work rather than postponing it, so there is nothing for a carrier to carry: the move is `1f7xno`'s (carried above), and "do not rewrite the symmetry guard" is satisfied permanently by having left it untouched (V-05).
- ADDING A `Blocks-Release` GATE. The item explicitly carries none and explains why.
  - Carrier-Declined: a decision already taken, not deferred work. Backlog `cnwy8g` states "No `Blocks-Release` gate. This is a layering correction, not a live failure", and its one behavioral consequence (`DriverError`) was discharged by `818uru` E-03. A carrier would assert an outstanding release risk that does not exist. NOTE the separate defect this turn FILED (`2kspdy`) does carry `- Blocks-Release: next`, on its own merits as a bug, which is a different claim from gating this layering Set.
- THE REVERSE DIRECTION as a problem to solve: it is already zero. E-03 merely pins it there.
  - Carrier-Declined: NOT DEFERRED, DONE. The reverse direction was zero and is now PINNED at zero by `FrozenImportSetTests::test_the_agy_to_oc_direction_is_ZERO` in `tests/test_runner_layering.py`, which this plan created and V-03 shows passing. There is no residual obligation: a future nonzero value fails a test rather than waiting on a carrier.
- FIXING THE HARDCODED `aw oc run` HOST LABEL IN `process_backlog_close` (F-14). It is a real live defect, and it is a BEHAVIOR change to a commit message that agy-driven runs write, so it is out of a move-nothing child's scope. RECORD it in the classification with its evidence so it is not lost; if child 02 re-homes the function, the label becomes a parameter question for that plan, and if neither plan takes it, it belongs in the backlog rather than in silence.
  - Carrier: 2kspdy
- THE TWO ENVIRONMENTAL SUITE FAILURES (F-17). Neither is caused by or fixed by this plan. In particular, do NOT delete, move, or commit the 189 untracked `opencode-recovery/*.md` files to make the reporting-contract test green; they are another party's work in a shared checkout.
  - Carrier: 4vn040

## Scope check

- Over-scope: `oc_runipd.py` and `agy_runipd.py` are in scope ONLY for siting the classification and any comment it needs. Do NOT move a definition, change a body, or edit an import list in this child. NOTE the one legitimate transient exception: E-04's mutation check MUST temporarily edit agy's import list to prove the guard fails, and MUST revert it, verified with `git diff --exit-code`. A mutation left behind would be an unsanctioned edit to the highest-contention file in the repository.
- Under-scope: stated rather than left as `none`. After this child nothing has moved: the drivers are still not peers. That is child 02's work, and this child's guard makes the gap visible in the meantime rather than closing it. Also unclosed by design: the hardcoded host label F-14 records, which this child only documents.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. The new guard belongs in a new `tests/test_runner_layering.py` rather than inside the dependency-focused module, because it is about module layering and not about dependencies; `tests/test_runner_item_dependencies.py` is declared in `Scope-Paths` only in case the existing symmetry guard is EXTENDED, and if it is not touched, acknowledge that at finalize rather than editing it to justify the declaration.
WHY A NEW FILE AND NOT `tests/test_runner_refork_guard.py`, since that is the nearest sibling and the question will occur to the executor: that module's `REFORK_TABLE` contract is "a NON-RUNNER module owns this symbol; no runner may re-define it", and the in-tree comment at `tests/test_runner_item_dependencies.py:1620-1626` records the consequence, that naming `oc_runipd` as an owner there would make its AST half forbid oc's own definition. These 48 names are `oc_runipd`-OWNED, so they cannot be tabled there. A new layering module is the correct home, and this paragraph exists so a future reader does not "consolidate" it into the refork guard and break it.
ALSO RUN `python3 -m pytest tests/test_runner_refork_guard.py tests/test_runner_shared.py tests/test_review_findings_cascade.py` EXPLICITLY and paste the result. These three hold the guards this plan's subject-matter is nearest to (re-fork ownership, the shared-module admission rule and the pure-move fingerprints, and the substring reverse-direction check), so an accidental interaction shows up here as a named failure rather than as a node-id diff the executor has to interpret.

## Spec / documentation sync

N/A, with the reason stated rather than asserted: this child relocates nothing, changes no operator-facing string, no run-record shape, and no documented contract. It adds a classification artifact and a test. No spec governs which module a host-neutral helper lives in.
ONE THING TO CHECK RATHER THAN ASSUME: if the classification artifact is written as prose intended for a human reader rather than as code or test data, it is user-facing prose and must contain no em or en dashes, per this repository's authoring rule. If it is test data or a code comment, that rule does not apply. Decide which it is and say so.

## Open questions

### OQ-01: Which names does the criterion fail to settle, and who arbitrates?

- Blocking: no
- Status: resolved
- Owner: this plan's executor for the list, the maintainer for any name the criterion cannot settle
- Resolution or deferral rationale: NOT blocking, because E-01 and E-02 already require that an unsettleable name be recorded as UNSETTLED with its reason rather than forced, so the plan completes with or without an arbitration. The likely candidates, named so the executor does not have to rediscover them: `run_suite_check` and `SuiteCheckResult` (neutral in principle, but the docstring at `oc_runipd.py:3637` records that the primary-checkout choice was measured against lane behavior); `integration_is_earned`, `collect_earned_paths` and `run_earned_paths` (integration is host-neutral in concept but the `integpath` Set is actively editing that surface, so moving them may collide); and `build_verify_and_continue_notice` and `render_runs_pointer` (wording functions, which `render_stream` would arguably own rather than `runner_shared`). An UNSETTLED verdict is a legitimate output of this child; a forced one is not.
  THE COLLISION RISK ON THE THREE EARNED-INTEGRATION NAMES WAS CHECKED AT REVIEW AND IS REAL BUT NOT YET LIVE. Three `integpath` plans remain in `pending/` (`51vw4y`, `rl67b0`, `3v7wo6`) and two of them declare `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` in `- Scope-Paths:`; `rl67b0`'s own F-15 discusses `run_suite_check` and `integration_is_earned` directly. None has executed. Since THIS child moves nothing, there is no collision to manage here, and the question is genuinely child 02's: an UNSETTLED verdict on those three with this citation is the useful output.
  RESOLVED AT EXECUTION, BY APPLYING THE CRITERION TO ALL 56 BODIES RATHER THAN BY ARBITRATION, so no maintainer ruling is needed and none is requested. THE ANSWER TO "WHICH NAMES DOES THE CRITERION FAIL TO SETTLE?" IS: NONE. `UNSETTLED_VERDICTS` is empty and all 56 names are `host-neutral`, measured by stripping comments and docstrings from every definition and finding exactly ONE `oc` token in executable code, which is a host LABEL and therefore a parameter rather than an opencode concept (filed as `2kspdy`).
  THE QUESTION CONFLATED TWO AXES, AND SEPARATING THEM IS WHAT RESOLVES IT. Every candidate it names is settled by the criterion and unsettled only on its MOVE: `run_suite_check`/`SuiteCheckResult` (a primary-checkout choice measured against lane behavior is a sequencing fact, not an opencode concept), `integration_is_earned`/`collect_earned_paths`/`run_earned_paths` (a possible collision with another Set is not a property of the body), and `build_verify_and_continue_notice`/`render_runs_pointer` (a contested DESTINATION between `runner_shared` and `render_stream` presupposes the name is neutral and moving). So all seven carry a neutral verdict plus a `move_note`, and all seven are listed in `MOVE_UNSETTLED` in `tests/test_runner_layering.py`. THE ARBITER IS THEREFORE CHILD 02 FOR THE MOVE, AND NOBODY FOR THE VERDICT.
  ONE CITATION IN THIS QUESTION IS NOW STALE AND IS CORRECTED RATHER THAN REPEATED: the three `integpath` plans no longer "remain in `pending/`". Located by id6 at execution, `51vw4y`, `rl67b0` and `3v7wo6` are ALL in `.aw/records/plans/executed/`. The collision the question worried about resolved itself without this Set, which is also visible in the import set: three of the twelve names that ARRIVED since review are suite-checking helpers. Child 02 should re-measure that surface rather than inherit either this question's claim or my correction of it.

### OQ-02: Should a pass-through re-export be counted as coupling at all?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT, and the answer makes the question moot rather than answered: there are ZERO pass-through re-exports. All 48 names are real definitions in `oc_runipd` (verified by walking oc's own `ImportFrom` and definition nodes; the intersection of the imported set with oc's own imported names is EMPTY), so no name is a cheap one-line re-point and the frozen set cannot include or exclude a tier that does not exist. The RECOMMENDATION the question carried (count them, since the direction is what the guard protects) still stands as the rule to apply should a future edit introduce one, which is why E-02 requires re-confirming the tier at execution time rather than trusting this resolution. What replaced the question is the BINDING-TIER distinction recorded in F-13 and required by E-02, which is the information child 02 actually needs.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the criterion as written and where it is sited. Paste the judge-the-body rule INCLUDING its comment-and-docstring exclusion, and the three sound-specific-but-neutral cases as recorded. State whether the artifact is human prose or test data, and if prose, confirm it contains no em or en dashes.
  - Observed evidence: SITED IN `tests/test_runner_layering.py`, in the module docstring, ABOVE the classification table it governs, so the rule and the verdicts cannot be read apart. ARTIFACT FORM, decided as the Spec/documentation-sync section requires: TEST DATA, not human prose. The classification is a `tuple[Name, ...]` of typed rows that the guard in the same module DERIVES its frozen set from (`FROZEN_OC_TO_AGY_IMPORTS = frozenset(row.name for row in CLASSIFICATION)`), so admitting an import requires classifying it and the two can never drift. The em/en-dash prohibition therefore does NOT apply (it governs user-facing prose); no such character was used regardless, verified: `grep -c '[\u2014\u2013]' tests/test_runner_layering.py` -> `0`.
    THE CRITERION AS WRITTEN (verbatim from the docstring):
    ```
    A name is OPENCODE-SPECIFIC if and only if its BODY references an opencode-only concept,
    meaning the `opencode` binary, its CLI flags, its session format, or its JSON stream shape.
    EVERYTHING ELSE IS HOST-NEUTRAL.
    ```
    THE JUDGE-THE-BODY RULE, WITH THE COMMENT-AND-DOCSTRING EXCLUSION (verbatim):
    ```
    JUDGE THE BODY, NOT THE NAME. Three names in this set sound host-specific and are documented
    as neutral. `pinned_child_env` and `pinned_module_argv` pin a NESTED `aw` invocation, and the
    in-tree comment above agy's import of them records that BOTH drivers must stay symmetric and
    that "a second copy is exactly how the previous inert half-pin came to differ from what it
    looked like it did". `announce_run_order` prints through the shared `render_stream` formatter
    and holds no opencode concept at all.

    JUDGE CODE, NOT PROSE. A comment or docstring mentioning `aw oc run` is NOT a body reference
    to an opencode concept. This distinction decides real cases in this very set rather than being
    hypothetical: measured at execution by stripping comments AND docstrings from all 56
    definitions, exactly ONE retains an `oc` token in executable code (`process_backlog_close`,
    see its row), while `queue_sort_key`, `run_order_rationale`, `render_runs_pointer` and
    `dependency_status_detailed` carry one in PROSE ONLY and are neutral. A grep would have
    misclassified four names.
    ```
    THE MEASUREMENT BEHIND THAT EXCLUSION, run at execution rather than quoted from the plan. Comment-and-docstring-stripped scan of all 56 definitions: `{"process_backlog_close": ["aw oc run"]}` is the ONLY code hit. RAW (unstripped) scan additionally flags `queue_sort_key`, `run_order_rationale`, `render_runs_pointer` and `dependency_status_detailed` on `aw oc run`, plus `announce_run_order`, `assert_child_tool_identity`, `queue_plan_path` and `record_item_spec_edits` on an `agy` mention. So a grep-based classification would have misclassified EIGHT names; applying the criterion to code misclassifies none.
    THE THREE SOUND-SPECIFIC-BUT-NEUTRAL CASES, all three recorded as rows with a `move_note`: `pinned_child_env` ("pins a nested `aw` child's PYTHONPATH to the runner's own package root; about `aw`, not opencode", move_note "the plan's worked example: sounds host-specific, is documented as requiring symmetry"), `pinned_module_argv` ("builds argv invoking the runner's OWN `agent_workflows` CLI; the suppressing half of the pin"), and `announce_run_order` ("prints the execution order through the SHARED `render_stream` formatter", move_note "the plan's worked example of a name that sounds host-specific and is not"). The in-tree comment the criterion cites was re-located BY SYMBOL rather than by the plan's stale `:269-272`: it now sits immediately above agy's `from agent_workflows.oc_runipd import (ToolIdentityError, assert_child_tool_identity, pinned_child_env, pinned_module_argv)` statement at `agent_workflows/agy_runipd.py:411-414` (the statement itself at `:415`), and reads verbatim "Both drivers must stay symmetric, and a second copy is exactly how the previous inert half-pin came to differ from what it looked like it did."
    ONE DELIBERATE ADDITION TO THE CRITERION, disclosed rather than slipped in: the docstring adds an explicit AXIS SEPARATION saying "is this host-neutral?" and "can it move, and where to?" are different questions, so an `unsettled` VERDICT is reserved for a name the criterion itself cannot settle, while a contested destination or a sequencing collision is recorded in `move_note` and listed in `MOVE_UNSETTLED`. Reason: OQ-01's own candidate list mixes the two (`run_suite_check` is "neutral in principle" but may COLLIDE with the pending `integpath` Set; `render_runs_pointer` is neutral but `render_stream` may own it), and calling those verdicts unsettled would report the criterion as having failed on names it settles cleanly.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the FULL classification: every name, its group, its verdict, its one-line reason, its BINDING TIER, and a re-confirmation that it is a real definition in `oc_runipd` rather than a pass-through. Paste the AST measurement that produced the name list AT EXECUTION TIME. DO NOT ASSERT A LITERAL COUNT AS A PASS CRITERION: this plan's prose carries 40, 47 and 48 and the true value moved during review, so state the count you measured and reconcile it against the review-time 48 by naming any arrived or departed name. A count differing from 48 PASSES this item; a classification that covers fewer names than were measured FAILS it. Paste the UNSETTLED list, even if empty, so a reader can see the criterion was applied rather than stretched. Confirm specifically that `dependency_status_detailed` carries a verdict, since it is the name this plan's own enumeration omitted.
  - Observed evidence: THE COUNT I MEASURED IS 56, not 40, 47 or 48, and per this plan's own instruction that is CORRECT rather than a discrepancy. Measured by `ast.walk` over `ImportFrom` nodes at execution time:
    ```
    $ python3 -c "..."   # ast.walk over agy_runipd for ImportFrom whose module endswith oc_runipd
    alias_entries        : 56
    distinct_alias_names : 56
    distinct_bound_names : 54
    nested_entries       : 4
    statements           : [415, 477, 513, 555, 1797, 2349, 2359, 2371]
    tiers                : {'pure-reexport': 34, 'module-level-consumed': 18, 'lazy-wrapper': 4}
    passthroughs         : []
    non_definitions      : []
    reverse (agy -> oc)  : 0
    ```
    RECONCILIATION AGAINST THE REVIEW-TIME 48, by two-way set difference rather than by count, with every name named. TWELVE ARRIVED, all in the thirteen days since review: `SPEC_NOT_FINALIZED`, `SPEC_RECONCILED`, `SPEC_RECONCILE_REFUSED`, `queue_plan_path`, `queue_with_plan_paths`, `record_item_spec_edits`, `report_run_spec_edits`, `spec_edit_record`, `spec_edit_summary` (nine forming an entirely NEW concern group, declared spec-edit visibility), plus `SUITE_CHECK_ARGV`, `extract_suite_failures`, `parse_suite_summary` (three joining suite-checking). FOUR DEPARTED, and every one departed the RIGHT way, which is this Set's thesis being proven by other plans: `_read_kind`, `_read_from_backlog`, `_read_item_dependencies` and `resolve_prior_lane` are now defined in `agent_workflows/runner_shared.py` (at `:5580`, `:5623`, `:5588` and `:14269`), so agy no longer reaches into a host driver for them. Note the three `_read_*` names departing makes the destination debate in OQ-01 and child 02's F-9/OQ-01 MOOT for those three: they went to `runner_shared`, not `selectors`, and they went without this Set.
    THE ACCRETION RATE IS THEREFORE UNCHANGED AND THE FREEZE GUARD IS JUSTIFIED BY IT: 40 on 2026-09-03, 47 on 2026-09-08, 48 on 2026-09-09, 56 on 2026-09-22, with a green suite throughout and four names leaving in the same window twelve arrived. A count-only guard would have passed straight through that.
    `dependency_status_detailed` CARRIES A VERDICT, as specifically required: `host-neutral`, group `dependency-graph`, tier `module-level`, reason "the `_detailed` sibling adding a root-cause map; mentions `aw oc run` in PROSE only", with a `move_note` recording that it is the name whose absence from `_SHARED_NAMES` let the symmetry guard pass over agy's real broken copy for months. It appears in the table below.
    UNSETTLED VERDICTS: EMPTY (`UNSETTLED_VERDICTS = ()`), and stated as a measurement rather than as tidiness. Every one of the 56 bodies was read; exactly one contains an `oc` token in executable code and that one is a host LABEL, which the criterion classifies as a parameter rather than an opencode concept. ALL 56 ARE HOST-NEUTRAL, zero opencode-specific. That is a strong enough claim to state its falsifiable consequence, which the artifact does: it PREDICTS child 02's residual oc-to-agy set is EMPTY, so a residual child 02 cannot move is a finding against this classification.
    WHAT IS UNSETTLED IS THE MOVE, NOT THE VERDICT, kept on a separate axis (`MOVE_UNSETTLED`, 7 names): `build_verify_and_continue_notice` and `render_runs_pointer` (destination contested, `render_stream` may own a wording function rather than `runner_shared`), and `run_suite_check`, `SuiteCheckResult`, `integration_is_earned`, `collect_earned_paths`, `run_earned_paths` (the `integpath` surface).
    CORRECTING THIS PLAN ON THE `integpath` RISK RATHER THAN REPEATING IT: OQ-01 records at review that three `integpath` plans "remain in `pending/`", and that is NO LONGER TRUE. Re-checked at execution by locating each by id6: `51vw4y`, `rl67b0` and `3v7wo6` are ALL in `.aw/records/plans/executed/`. So the collision this plan flagged has RESOLVED itself, and those five names are listed under `MOVE_UNSETTLED` on the weaker ground that the `integpath` Set has recently rewritten that exact surface (which is also why three of the twelve arrived names are suite-checking helpers), not because a pending plan is about to touch it. Child 02 should re-measure rather than inherit either claim.
    REAL-DEFINITION RE-CONFIRMATION, not assumed from the review's resolution of OQ-02: measured again at execution, and it is still ZERO pass-throughs. All 56 names are oc's OWN definitions (`non_definitions: []`, `passthroughs: []` above), and it is now GATED rather than noted, by `ClassificationIntegrityTests::test_every_frozen_name_is_a_REAL_DEFINITION_in_oc_runipd`, so a future pass-through is caught rather than rediscovered.
    THE INFORMATION CHILD 02 ACTUALLY NEEDS, which no count conveys and which this plan did not ask for but the classification records anyway: 20 of the 56 bodies CLOSE OVER an oc-private module-level name and therefore cannot move alone (see the `closes_over` column). The sharpest cases are `integration_is_earned` (6 co-dependencies), `classify_recovery_disposition` (5), and the `_SIGNAL_REPORT_*` mutable globals that `register_signal_report`/`emit_shutdown_report` share, which must move together or the two hosts would keep separate registries.
    THE FULL CLASSIFICATION, all 56 rows, grouped by concern, each with verdict, tier, reason and co-dependencies (dumped from the live table, sorted by group then name):
    ```
    NAME                                 GROUP                  VERDICT        TIER             REASON / CLOSES-OVER
    BacklogCloseVerdict                  backlog-closing        host-neutral   pure-reexport    the verdict record for one item; a data class
    CARRIER_KIND_IPD                     backlog-closing        host-neutral   pure-reexport    carrier-kind constant; a records-vocabulary string
    CARRIER_KIND_OTHER                   backlog-closing        host-neutral   pure-reexport    carrier-kind constant; a records-vocabulary string
    close_backlog_item                   backlog-closing        host-neutral   pure-reexport    closes an item through the lifecycle-owned setter, never by editing the file | closes_over=run_checked
    commit_backlog_close                 backlog-closing        host-neutral   pure-reexport    path-scoped-commits the moved item file via the shared tooled commit path | closes_over=run_checked
    evaluate_backlog_close               backlog-closing        host-neutral   pure-reexport    decides whether THIS run may close the item, and why not if it may not | closes_over=_carrier_kind
    process_backlog_close                backlog-closing        host-neutral   module-level     orchestrates the close after a plan reaches executed; the ONE body with an `oc` token in CODE | closes_over=collect_lane_earned_paths
    record_unclosed_backlog_items        backlog-closing        host-neutral   pure-reexport    appends the unclosed-item ledger record before anything is printed
    render_unclosed_report               backlog-closing        host-neutral   pure-reexport    formats that ledger for a human; text assembly
    resolve_backlog_item                 backlog-closing        host-neutral   pure-reexport    finds the item file whose `- Id:` matches; filesystem lookup
    unclosed_backlog_items               backlog-closing        host-neutral   pure-reexport    lists items this run touched but did not close, with reasons; reads run state
    DEPENDENCY_FATAL_RULES               dependency-graph       host-neutral   pure-reexport    a frozenset of check-rule ids; data, and not host data
    _artifact_owners                     dependency-graph       host-neutral   pure-reexport    looks owners up in the shared identity index; body is a `check_engine` call
    cascade_dependency_blocked           dependency-graph       host-neutral   module-level     propagates dependency-blocked over reverse edges to a fixed point | closes_over=EXECUTION_SUCCESS_STATES,SUCCESS_STATES,TERMINAL_STATES
    dependency_depth                     dependency-graph       host-neutral   pure-reexport    longest in-queue prerequisite chain; the FIRST queue sort key, host-independent
    dependency_reasons                   dependency-graph       host-neutral   pure-reexport    renders why an edge is unsatisfied; reporting text, no gating decision
    dependency_status                    dependency-graph       host-neutral   module-level     aggregates edge verdicts for one plan; no host concept in the body
    dependency_status_detailed           dependency-graph       host-neutral   module-level     the `_detailed` sibling adding a root-cause map; mentions `aw oc run` in PROSE only | closes_over=EXECUTION_SUCCESS_STATES,TERMINAL_STATES
    dependency_target_id6                dependency-graph       host-neutral   pure-reexport    parses an id6 out of a dependency token; string handling
    edge_satisfied                       dependency-graph       host-neutral   module-level     decides whether one typed dependency edge is satisfied; pure record/state logic
    enforce_dependency_preflight         dependency-graph       host-neutral   lazy-wrapper     raises `DriverError` on an invalid selected graph; `DriverError` is ALREADY shared
    parse_dependency_token               dependency-graph       host-neutral   module-level     resolves one token to a shared `ipd_schema.ItemDependency`; delegates to a non-runner module
    preflight_dependency_findings        dependency-graph       host-neutral   pure-reexport    runs the SHARED evaluator over selected plans; already a thin call into `check_engine` | closes_over=_consuming_actions_for
    queue_sort_key                       dependency-graph       host-neutral   module-level     deterministic ready-node ordering (spec 25kzda 5.4); `aw oc run` appears in a COMMENT
    collect_earned_paths                 earned-integration     host-neutral   pure-reexport    diffs an attempt's head range to list the paths it produced; a git diff | closes_over=run_checked
    integration_is_earned                earned-integration     host-neutral   pure-reexport    decides whether a completed turn earned automatic integration; verifier/suite logic | closes_over=INTEGRATION_EARNED_BY_SUITE,INTEGRATION_EARNED_BY_VERIFIER,INTEGRATION_REFUSED_NO_SIGNAL,INTEGRATION_REFUSED_SUITE_FAILED,INTEGRATION_REFUSED_VERIFIER_DECLINED,IntegrationVerdict
    run_earned_paths                     earned-integration     host-neutral   pure-reexport    unions the per-attempt earned paths across a run; reads run state
    build_verify_and_continue_notice     recovery-routing       host-neutral   lazy-wrapper     builds the prompt block telling a resumed turn to verify prior work; prompt text, host-agnostic | closes_over=RecoveryDisposition
    classify_recovery_disposition        recovery-routing       host-neutral   lazy-wrapper     routes a recovery turn from git FACTS via `worktree_lease`; no host concept | closes_over=DISPOSITION_FRESH_EXECUTION,DISPOSITION_UNDETERMINED,DISPOSITION_VERIFY_AND_CONTINUE,RecoveryDisposition,_lane_commit_subjects
    route_recovery_turn                  recovery-routing       host-neutral   lazy-wrapper     records the routing verdict durably and dispatches; writes run state and events | closes_over=DISPOSITION_FRESH_EXECUTION,DISPOSITION_UNDETERMINED,RecoveryDisposition,save_state
    announce_run_order                   run-ordering           host-neutral   module-level     prints the execution order through the SHARED `render_stream` formatter
    run_order_rationale                  run-ordering           host-neutral   module-level     compares requested against actual order and explains the difference; `aw oc run` in PROSE only
    simulate_dispatch_order              run-ordering           host-neutral   pure-reexport    simulates the dispatch order `run_queue` will take; operates on the queue structure
    update_execution_order               run-ordering           host-neutral   module-level     records actual dispatch order into run state; state bookkeeping
    emit_shutdown_report                 shutdown-reporting     host-neutral   module-level     idempotently writes then prints the unclosed-item record on shutdown | closes_over=_SIGNAL_REPORT_DONE,_SIGNAL_REPORT_STATE
    register_signal_report               shutdown-reporting     host-neutral   module-level     publishes run state for the signal handlers to report from | closes_over=_SIGNAL_REPORT_STATE
    render_runs_pointer                  shutdown-reporting     host-neutral   module-level     formats the trailing `aw runs <run-id>` pointer; its docstring notes `aw oc runs` does NOT exist
    signal_report_callback               shutdown-reporting     host-neutral   pure-reexport    returns the callable the SIGINT/SIGTERM handlers invoke; a closure factory
    SPEC_NOT_FINALIZED                   spec-edit-visibility   host-neutral   pure-reexport    reconciliation-state constant; a string
    SPEC_RECONCILED                      spec-edit-visibility   host-neutral   pure-reexport    reconciliation-state constant; a string
    SPEC_RECONCILE_REFUSED               spec-edit-visibility   host-neutral   pure-reexport    reconciliation-state constant; a string
    queue_plan_path                      spec-edit-visibility   host-neutral   pure-reexport    resolves the plan FILE a queue entry refers to; names BOTH drivers' freeze keys in its docstring
    queue_with_plan_paths                spec-edit-visibility   host-neutral   pure-reexport    re-expresses the queue in the shape the shared spec helper documents; an adapter
    record_item_spec_edits               spec-edit-visibility   host-neutral   pure-reexport    stores one item's reconciliation on its queue entry; takes `reconcile` as a PARAMETER
    report_run_spec_edits                spec-edit-visibility   host-neutral   module-level     prints the end-of-run declared-spec-edit report; wired at three summary sites per host
    spec_edit_record                     spec-edit-visibility   host-neutral   pure-reexport    the spec-filtered view of one item's two-way scope reconciliation; record shaping
    spec_edit_summary                    spec-edit-visibility   host-neutral   pure-reexport    aggregates per-item spec records into the per-run view; reads durable state only
    SUITE_CHECK_ARGV                     suite-checking         host-neutral   pure-reexport    the argv of the repository suite, `(python, -m, pytest)`; nothing to do with a host driver
    SuiteCheckResult                     suite-checking         host-neutral   pure-reexport    the record of what the driver observed running the suite; a data class
    extract_suite_failures               suite-checking         host-neutral   pure-reexport    pulls FAILED/ERROR node ids out of suite output; regex over pytest text | closes_over=SUITE_FAILURE_LINE_LIMIT,_SUITE_FAILURE_LINE_RE
    parse_suite_summary                  suite-checking         host-neutral   pure-reexport    extracts the suite COUNT LINE; exists because `runner_shared` may not import a host driver | closes_over=_SUITE_SUMMARY_RE
    run_suite_check                      suite-checking         host-neutral   module-level     runs the repository suite in the PRIMARY checkout and reads the result; runs pytest, not opencode | closes_over=SUITE_CHECK_TIMEOUT_SECONDS
    ToolIdentityError                    tool-identity          host-neutral   module-level     the run-fatal identity mismatch exception; nothing in it is about opencode
    assert_child_tool_identity           tool-identity          host-neutral   pure-reexport    verifies a pinned child resolves this package to the runner's own copy; fails closed | closes_over=_AW_PIN_PROBE,_TOOL_IDENTITY_VERIFIED
    pinned_child_env                     tool-identity          host-neutral   module-level     pins a nested `aw` child's PYTHONPATH to the runner's own package root; about `aw`, not opencode | closes_over=runner_package_root
    pinned_module_argv                   tool-identity          host-neutral   module-level     builds argv invoking the runner's OWN `agent_workflows` CLI; the suppressing half of the pin | closes_over=_AW_PIN_BOOTSTRAP
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the guard as written, showing FOUR properties explicitly: it measures by `ast.walk` over `ImportFrom` nodes (not `tree.body`, so the five nested wrapper imports are counted), it keys the set on `alias.name` (not `asname or name`, since four wrappers share the local `_shared` and would collapse), it pins the SORTED SET rather than only the count, and it asserts the reverse direction is zero. Paste it PASSING, and paste the SIZE of the set it froze alongside your own independent measurement so the two agree. Paste the failure message text and confirm it names the changed symbol and states BOTH constructive options (put it in `runner_shared`, or add it to the frozen set with a reason). Paste the comment distinguishing a sanctioned child-02 shrink from a regression.
  - Observed evidence: THE GUARD IS `tests/test_runner_layering.py` (new file), two test classes, 5 tests. All four required properties below, each shown in the source that implements it.
    PROPERTY 1, `ast.walk` AND NOT `tree.body`. Note the plan says FIVE nested imports; I measured FOUR, because `resolve_prior_lane` (one of the review-time five) has since moved to `runner_shared` and its wrapper no longer imports from oc. The property is unchanged and the mutation in V-04(b) proves it bites:
    def oc_to_agy_imports(source: str, *, module_suffix: str = "oc_runipd") -> list[ast.alias]:
        """Every `from ...<module_suffix> import` ALIAS in ``source``, anywhere in the tree.

        WALKS THE WHOLE TREE, NOT `tree.body`, AND THAT IS THE POINT. Measured at this execution,
        4 of the 56 imports are NESTED inside delegating wrapper functions, so a guard iterating
        `tree.body` under-reports by four and freezes a set that is short by exactly the tier no
        other check can see (`agy.<name> is oc.<name>` is FALSE for all four, because agy exposes
        its own wrapper, so an identity-based audit is blind to them too).

        AST AND NOT GREP: a substring search counts a mention inside a comment or docstring and
        cannot distinguish an `as <same-name>` re-export from a use.
        """
        aliases: list[ast.alias] = []
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(module_suffix):
                aliases.extend(node.names)
        return aliases
    PROPERTY 2, KEYED ON `alias.name` AND NOT `asname or name`. Measured at execution: 56 alias entries carry only 54 distinct BOUND names, because THREE lazy wrappers bind to the same local `_shared` (the plan says four; `resolve_prior_lane`'s wrapper left). A bound-name key would collapse those three to one:
    def imported_names(source: str, *, module_suffix: str = "oc_runipd") -> frozenset[str]:
        """The ORIGINAL names imported, keyed on `alias.name` and NEVER on `asname or name`.

        Measured at this execution: the 56 aliases carry only 54 distinct BOUND names, because
        three lazy wrappers bind their import to the same local `_shared`. A set keyed on the bound
        name therefore COLLAPSES those three into one entry and reports no change when one of them
        is added or removed, which is precisely the silent accretion this guard exists to stop.
        """
        return frozenset(alias.name for alias in oc_to_agy_imports(source, module_suffix=module_suffix))
    PROPERTY 3, THE SORTED SET AND NOT THE COUNT. The pin is a `frozenset` DERIVED from the classification table, and the failure reports `added`/`removed` as SORTED NAME LISTS, so a one-out-one-in change (exactly what happened between review and execution) is reported by name rather than passing silently:
    # THE FROZEN SET. DERIVED from the classification above, deliberately: there is no second list
    # to keep in step, and admitting a name REQUIRES classifying it.
    #
    # SHRINKING THIS SET IS EXPECTED AND CORRECT. `runnerlayer` Order 02 (`1f7xno`) re-homes these
    # names one batch at a time and updates this table in the SAME commit as each move, so a row
    # disappearing alongside a move in `runner_shared` is the plan working. GROWING it is the
    # regression this module exists to catch. And if this guard goes RED, the fix is NEVER to delete
    # it or to trim the table to match: read the failure message, which names the symbol and states
    # the two legitimate options.
    # =============================================================================================
    FROZEN_OC_TO_AGY_IMPORTS: frozenset[str] = frozenset(row.name for row in CLASSIFICATION)
    PROPERTY 4, THE REVERSE DIRECTION PINNED AT ZERO, in `FrozenImportSetTests::test_the_agy_to_oc_direction_is_ZERO`, which reuses the same AST measurement with `module_suffix="agy_runipd"` and asserts the sorted result equals `[]`. Its docstring records what it does NOT duplicate: the existing substring claim in `tests/test_review_findings_cascade.py` (a `"import agy_runipd"` needle inside the `SharedPredicateTests.CLAIMS` data table at `:701-715`) is a SPELLING check inside a test about the review-findings predicate, and agy's symbol-level `from agent_workflows.oc_runipd import` form is chosen deliberately so that needle stays meaningful for the blanket-import case it targets. That test was NOT weakened or rewritten; it still passes (see V-05).
    PASSING, as written:
    ```
    $ python3 -m pytest tests/test_runner_layering.py -o addopts="" -q
    .....                                                                    [100%]
    5 passed in 0.45s
    ```
    THE FROZEN SIZE AGAINST AN INDEPENDENT MEASUREMENT, the two agreeing:
    ```
    $ python3 -c "import test_runner_layering as m; ..."
    frozen set size    : 56
    classification rows: 56
    live measured      : 56
    equal              : True
    aliases (entries)  : 56
    distinct bound     : 54     <- why the key must be alias.name
    tiers              : {'pure-reexport': 34, 'module-level': 18, 'lazy-wrapper': 4}
    verdicts           : {'host-neutral': 56}
    move_unsettled     : 7
    unsettled verdicts : ()
    ```
    THE FAILURE MESSAGE, pasted from an ACTUAL failing run (mutation (a) of V-04), naming the symbol and stating BOTH constructive options:
    ```
    AssertionError: the oc-to-agy import surface changed, and this guard exists because nothing else in the suite notices that.
      ADDED (agy now imports these from oc and the table does not classify them): utc_now

    WHAT TO DO, depending on which way it moved:
      * You ADDED a name. If it is HOST-NEUTRAL (its body references no opencode-only concept: not the `opencode` binary, its CLI flags, its session format, or its JSON stream shape), it does NOT belong in a host driver at all. Put the definition in `agent_workflows/runner_shared.py` and have BOTH drivers import it from there; then this guard needs no edit. If it is genuinely OPENCODE-SPECIFIC, add a `Name(...)` row to CLASSIFICATION in this file with verdict `OPENCODE_SPECIFIC` and a reason saying which opencode concept its body references. Either way the name gets a verdict.
      * You REMOVED a name by re-homing it (this is `runnerlayer` Order 02's whole job): delete its row from CLASSIFICATION in the SAME commit as the move, so the suite is never red between commits.
      * DO NOT delete or weaken this guard, and do not trim the table to whatever the code now says. That converts a caught regression into an uncaught one, and a blanket `as <same-name>` re-export is exactly what `ruff` silently deleted six of once already.
    ```
    BOTH OPTIONS ARE PRESENT AND ARE CONSTRUCTIVE, per this repository's rule that a prohibition-only gate gets complied with by DELETION: option one is "put the definition in `runner_shared` and import it in both drivers" (which needs no edit to the guard at all), option two is "add a `Name(...)` row with verdict `OPENCODE_SPECIFIC` and a reason naming the opencode concept". The third bullet forbids the destructive fix explicitly, citing the `ruff` incident.
    THE SANCTIONED-SHRINK COMMENT is the `# THE FROZEN SET.` block pasted under Property 3 above: "SHRINKING THIS SET IS EXPECTED AND CORRECT ... a row disappearing alongside a move in `runner_shared` is the plan working. GROWING it is the regression this module exists to catch."
    ONE DESIGN CHOICE BEYOND WHAT E-03 REQUIRED, disclosed: the pin is DERIVED from the classification (`frozenset(row.name for row in CLASSIFICATION)`) rather than being a second hand-maintained tuple. Reason: a separate list is a second thing to keep in step, and this plan's own history is a list drifting from the code (its E-02 enumeration silently omitted `dependency_status_detailed`). Deriving it means admitting a name REQUIRES classifying it, which is what E-03's failure message promises.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste ALL THREE mutations in full. For each: the exact edit, the FAILING output with the message naming that symbol, the revert, and the passing output. The three are (a) a module-level addition, (b) an addition NESTED INSIDE A FUNCTION BODY, and (c) a removal of a pure module-level re-export. A V-04 missing (b) is incomplete, because a body-only guard passes (a) and (c) while freezing a set short by five; a V-04 missing (c) is incomplete, because the removal is what proves the SET is pinned rather than the count. Finish by pasting `git diff --exit-code -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing no residual mutation in either driver.
  - Observed evidence: ALL THREE MUTATIONS PERFORMED, each on a DIFFERENT symbol as E-04 requires, each reverted by RESTORING THE FILE from a byte-identical copy taken before the first mutation (never by re-editing from memory).
    PRE-MUTATION BASELINE, so the reverts are provable:
    ```
    $ git diff --exit-code -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py && echo "CLEAN-BEFORE-MUTATION"
    CLEAN-BEFORE-MUTATION
    $ cp agent_workflows/agy_runipd.py .aw/state/scratch-9kmbr0/agy_runipd.py.orig
    $ sha256sum agent_workflows/agy_runipd.py .aw/state/scratch-9kmbr0/agy_runipd.py.orig
    8635b474533aeb51a92eef7351e97625f044f43dd21b80093f139793e9d9d2a5  agent_workflows/agy_runipd.py
    8635b474533aeb51a92eef7351e97625f044f43dd21b80093f139793e9d9d2a5  .aw/state/scratch-9kmbr0/agy_runipd.py.orig
    ```
    MUTATION (a), A MODULE-LEVEL ADDITION. THE EXACT EDIT, into the `DEPENDENCY_FATAL_RULES` statement (`agy_runipd.py:513`):
    ```
     from agent_workflows.oc_runipd import (
         DEPENDENCY_FATAL_RULES as DEPENDENCY_FATAL_RULES,
    +    utc_now as utc_now,  # E-04 MUTATION (a): transient module-level addition, reverted below.
    $ git diff --stat -- agent_workflows/agy_runipd.py
     agent_workflows/agy_runipd.py | 1 +
     1 file changed, 1 insertion(+)
    ```
    FAILING, WITH THE MESSAGE NAMING `utc_now`:
    ```
    E       AssertionError: the oc-to-agy import surface changed, and this guard exists because nothing else in the suite notices that.
    E         ADDED (agy now imports these from oc and the table does not classify them): utc_now
    E
    E       WHAT TO DO, depending on which way it moved:
    E         * You ADDED a name. If it is HOST-NEUTRAL ... Put the definition in `agent_workflows/runner_shared.py` and have BOTH drivers import it from there ... If it is genuinely OPENCODE-SPECIFIC, add a `Name(...)` row to CLASSIFICATION in this file with verdict `OPENCODE_SPECIFIC` and a reason saying which opencode concept its body references.
    E         * You REMOVED a name by re-homing it ... delete its row from CLASSIFICATION in the SAME commit as the move ...
    E         * DO NOT delete or weaken this guard ...
    FAILED tests/test_runner_layering.py::FrozenImportSetTests::test_the_oc_to_agy_import_set_is_exactly_the_frozen_set
    1 failed, 4 passed in 0.53s
    ```
    REVERT AND PASS:
    ```
    $ cp .aw/state/scratch-9kmbr0/agy_runipd.py.orig agent_workflows/agy_runipd.py && git diff --exit-code -- agent_workflows/agy_runipd.py && echo "REVERT-(a)-CLEAN"
    REVERT-(a)-CLEAN
    $ python3 -m pytest tests/test_runner_layering.py -o addopts="" -q
    .....                                                                    [100%]
    5 passed in 0.44s
    ```
    MUTATION (b), AN ADDITION NESTED INSIDE A FUNCTION BODY, on a DIFFERENT symbol, in agy's `classify_recovery_disposition` delegating wrapper (the shape of the real lazy-wrapper tier):
    ```
         from agent_workflows.oc_runipd import classify_recovery_disposition as _shared

    +    # E-04 MUTATION (b): transient NESTED addition, the tier a `tree.body` guard cannot see.
    +    from agent_workflows.oc_runipd import append_jsonl as _mutation_probe  # noqa: F401
    +
         return _shared(repo, item, state)
    $ git diff --stat -- agent_workflows/agy_runipd.py
     agent_workflows/agy_runipd.py | 3 +++
     1 file changed, 3 insertions(+)
    ```
    FAILING, WITH THE MESSAGE NAMING `append_jsonl`, AND FAILING TWICE, which is stronger than E-04 asked for: the frozen-set guard catches the name AND the tier-consistency test catches that a nested import is not declared as `lazy-wrapper`:
    ```
    E       AssertionError: the oc-to-agy import surface changed, and this guard exists because nothing else in the suite notices that.
    E         ADDED (agy now imports these from oc and the table does not classify them): append_jsonl
    FAILED tests/test_runner_layering.py::FrozenImportSetTests::test_the_oc_to_agy_import_set_is_exactly_the_frozen_set
    FAILED tests/test_runner_layering.py::ClassificationIntegrityTests::test_every_lazy_wrapper_row_really_is_a_NESTED_import
    2 failed, 3 passed in 0.48s
    ```
    AND THE PROOF THAT THIS MUTATION IS THE ONE A BODY-ONLY GUARD WOULD MISS, which is the whole point of (b), measured directly rather than asserted:
    ```
    tree.body sees: 52 | ast.walk sees: 57
    INVISIBLE to a body-only guard: ['append_jsonl', 'build_verify_and_continue_notice', 'classify_recovery_disposition', 'enforce_dependency_preflight', 'route_recovery_turn']
    is the mutation 'append_jsonl' invisible to a body-only guard? True
    ```
    REVERT AND PASS:
    ```
    $ cp .aw/state/scratch-9kmbr0/agy_runipd.py.orig agent_workflows/agy_runipd.py && git diff --exit-code -- agent_workflows/agy_runipd.py && echo "REVERT-(b)-CLEAN"
    REVERT-(b)-CLEAN
    $ python3 -m pytest tests/test_runner_layering.py -o addopts="" -q
    .....                                                                    [100%]
    5 passed in 0.42s
    ```
    MUTATION (c), A REMOVAL OF A PURE MODULE-LEVEL RE-EXPORT, on a THIRD distinct symbol, chosen from tier (a) as E-04 directs because those are the names `ruff` actually deletes:
    ```
    -    simulate_dispatch_order as simulate_dispatch_order,
    $ git diff --stat -- agent_workflows/agy_runipd.py
     agent_workflows/agy_runipd.py | 1 -
     1 file changed, 1 deletion(-)
    ```
    FAILING ON THE REMOVAL, which is what proves the SET is pinned and not the count:
    ```
    E       AssertionError: the oc-to-agy import surface changed, and this guard exists because nothing else in the suite notices that.
    E         REMOVED (the table classifies these but agy no longer imports them): simulate_dispatch_order
    E         * You REMOVED a name by re-homing it (this is `runnerlayer` Order 02's whole job): delete its row from CLASSIFICATION in the SAME commit as the move, so the suite is never red between commits.
    FAILED tests/test_runner_layering.py::FrozenImportSetTests::test_the_oc_to_agy_import_set_is_exactly_the_frozen_set
    1 failed, 4 passed in 0.53s
    ```
    REVERT, PASS, AND THE FINAL RESIDUAL-MUTATION PROOF ON BOTH DRIVERS:
    ```
    $ cp .aw/state/scratch-9kmbr0/agy_runipd.py.orig agent_workflows/agy_runipd.py
    $ python3 -m pytest tests/test_runner_layering.py -o addopts="" -q
    .....                                                                    [100%]
    5 passed in 0.48s
    $ git diff --exit-code -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py && echo "git diff --exit-code: CLEAN (exit 0) on BOTH drivers"
    git diff --exit-code: CLEAN (exit 0) on BOTH drivers
    $ sha256sum agent_workflows/agy_runipd.py .aw/state/scratch-9kmbr0/agy_runipd.py.orig
    8635b474533aeb51a92eef7351e97625f044f43dd21b80093f139793e9d9d2a5  agent_workflows/agy_runipd.py
    8635b474533aeb51a92eef7351e97625f044f43dd21b80093f139793e9d9d2a5  .aw/state/scratch-9kmbr0/agy_runipd.py.orig
    ```
    `oc_runipd.py` WAS NEVER MUTATED AT ALL (all three mutations are agy-side, since agy is the importing driver), and the hash equality above shows agy is byte-identical to its pre-mutation state, so neither of the two highest-contention files in the repository carries a residual edit. NOTE the scratch copy lives under `.aw/state/`, which is GITIGNORED, so it is not a stray tracked artifact.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the bare-suite failing NODE ID sets before and after, measured in the executing worktree, and show they are identical. Do not paste totals as the argument, and do not quote this plan's review-time figures as your baseline. For each residual failure, name it and say why it is environmental rather than caused here; if either of the two F-17 failures is present, say so by node id and confirm you did not "fix" it (in particular that no `opencode-recovery/*.md` file was deleted, moved, or committed). Paste `tests/test_runner_item_dependencies.py` passing AND the explicit run of `tests/test_runner_refork_guard.py tests/test_runner_shared.py tests/test_review_findings_cascade.py` passing. State whether `CrossDriverSymmetryTests` was extended or left alone; if left alone, acknowledge the declared-but-unmodified `Scope-Paths` entry rather than editing the file to justify it.
  - Observed evidence: BASELINE MEASURED IN THIS LANE WORKTREE BEFORE ANY EDIT, not quoted from this plan (whose review-time figures are stale in both halves):
    ```
    $ python3 -m pytest        # BEFORE, bare, in the executing worktree
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 8161 passed, 3 skipped, 2 xfailed, 3 warnings in 158.68s (0:02:38)
    ```
    AFTER, same command, same worktree:
    ```
    $ python3 -m pytest        # AFTER
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 8166 passed, 3 skipped, 2 xfailed, 3 warnings in 115.21s (0:01:55)
    ```
    THE FAILING NODE-ID SETS ARE IDENTICAL, which is the argument (the totals differ only because this plan ADDS 5 tests, 8161 + 5 = 8166, and that arithmetic is context, not the criterion):
    ```
    BEFORE: {tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped}
    AFTER : {tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped}
    identical: yes; added: none; removed: none
    ```
    THE ONE RESIDUAL FAILURE IS ENVIRONMENTAL AND IS PROVEN SO RATHER THAN ASSERTED. It is not caused by this plan (it is red in the BEFORE run, on an untouched tree) and its cause is THIS LANE's own ambient environment: the test asserts a NON-isolated turn receives no permission-denial policy by checking `policy_key not in main_env` (`tests/test_turn_bounds.py:310`), and `main_env` inherits the ambient environment, in which `OPENCODE_CONFIG_CONTENT` is set because a contained worker lane is exactly where that variable is exported. Measured here: `env | grep -c OPENCODE_CONFIG_CONTENT` -> `1`. Narrowed run to show it is the only failure in its module: `python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q` -> `1 failed, 75 passed in 5.18s`. I did NOT weaken, skip or "fix" it, and I did not touch `tests/test_turn_bounds.py`: the assertion encodes the real isolation contract (R4.1) and the fault is the test's hermeticity, not the code. ALREADY FILED FOUR TIMES, so I deliberately did NOT file a fifth duplicate: `4vn040`, `8dp3zp`, `hco0mk` and `r67fl1` in `.aw/records/backlog/open/` all describe this exact node id and the same ambient-variable cause.
    NEITHER F-17 FAILURE IS PRESENT, so the plan's baseline is stale in both halves and I report that rather than reconciling it away. `tests/test_reporting_contract.py` and `tests/test_runner_backlog_close.py` both PASS in this lane, and the 189 untracked `opencode-recovery/*.md` files the plan describes are NOT in this worktree (`git status --porcelain` showed a clean tree at turn start, and shows exactly my two new files now). CONFIRMED REGARDLESS, as the fence requires: I deleted, moved, committed and modified NO untracked file I did not create, and no `opencode-recovery/*.md` file was touched in any way.
    `tests/test_runner_item_dependencies.py` PASSING, which is the module holding `CrossDriverSymmetryTests`:
    ```
    $ python3 -m pytest tests/test_runner_item_dependencies.py -o addopts="" -q
    ............................................................             [100%]
    60 passed in 4.67s
    ```
    THE EXPLICIT THREE-MODULE RUN THIS PLAN REQUIRES, passing:
    ```
    $ python3 -m pytest tests/test_runner_refork_guard.py tests/test_runner_shared.py tests/test_review_findings_cascade.py -o addopts="" -q
    ........................................................................ [ 29%]
    ........................................................................ [ 59%]
    ........................................................................ [ 89%]
    .........................                                                [100%]
    241 passed in 44.51s
    ```
    `CrossDriverSymmetryTests` WAS LEFT ALONE, neither extended nor rewritten, and its `_SHARED_NAMES` tuple is untouched. REASON, stated rather than implied: it is the guard that caught `ruff` deleting six re-exports, and this child adds a guard on the SET OF IMPORTS rather than on any named symbol's identity, so extending a runner-owned-identity list would have added nothing this plan needs while touching the highest-value existing check. I also re-read it rather than trusting the plan's citation, and found TWO of the plan's claims stale: the class is now at `tests/test_runner_item_dependencies.py:2949` (not `:1617`), `_SHARED_NAMES` at `:2965` (not `:1633`), and the tuple holds FOURTEEN names, not the twelve the plan asserts in three places. The two additions are `classify_drain_block` and `record_transient_dependency_wait`, added by `depblock 01 (akzy45)` E-04 for the reason the in-tree comment gives: the drain arm is the one dependency site each host still implements separately. Also note `test_the_implementation_is_shared_not_copied`, which the plan names, NO LONGER EXISTS: it was merged with its presence-checking sibling into `test_every_shared_name_is_present_on_both_drivers_and_is_the_SAME_object` (`:2991`). I found it BY CLASS NAME as the plan's own fence instructs, and the module's assertion that a shared rule module "must not learn about the runner or its run state" is likewise untouched and passing.
    DECLARED-BUT-UNMODIFIED `Scope-Paths` ENTRY, ACKNOWLEDGED RATHER THAN JUSTIFIED BY AN EDIT: `tests/test_runner_item_dependencies.py` was declared "only in case the existing symmetry guard is EXTENDED". It was not extended, so the file is UNMODIFIED, which the plan explicitly says to acknowledge at finalize rather than to edit the file to justify the declaration. `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` are likewise declared and UNMODIFIED: they were needed only for E-04's transient mutation, which was reverted to byte-identical (see V-04). So of four declared paths, ONE is modified (`tests/test_runner_layering.py`, created) and THREE are acknowledged unmodified. The lifecycle transition supplies `--scope-ack` for each.
    ONE PATH CHANGED THAT IS NOT IN `Scope-Paths`, disclosed here rather than left for the scope gate to discover: `.aw/records/backlog/open/20260922-2kspdy-01-2kspdy-backlog-close-hardcoded-host-label.backlog.md`, the backlog item filing the live defect F-14 describes (the hardcoded `aw oc run` host label). The turn contract REQUIRES filing a durable carrier for each finding, and the plan's own Deferred section says that if neither plan takes the fix "it belongs in the backlog rather than in silence". Created with `aw backlog new --apply`; no source behavior changed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the four paths in `- Scope-Paths:`. Do NOT move any definition. Do NOT change any function body. Do NOT PERMANENTLY edit either driver's import list; E-04's mutation check edits it transiently and MUST revert, proven by `git diff --exit-code`. Do NOT rewrite `CrossDriverSymmetryTests` or weaken the module's assertion that a shared rule module must not learn about run state. Do NOT touch a diverged symbol. Do NOT fix the `build_isolation_notice` re-fork. Do NOT fix the hardcoded `aw oc run` host label (F-14); record it. Do NOT add a `Blocks-Release` field. Do NOT delete, move, or commit any `opencode-recovery/*.md` file or any other untracked file you did not create. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL AND RE-MEASURE BY AST, NEVER BY THE LINE NUMBERS OR THE COUNT IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs. MEASURED AT REVIEW, one day after authoring: every one of this plan's original import-statement line citations was wrong (`:266` is now `:273`, `:308` is `:315`, `:333` is `:340`, and the four nested ones all moved), the symmetry guard's anchors moved roughly 440 lines, and the import count itself moved 40 -> 47 -> 48 over six days. Derive the name list yourself and find every symbol by NAME.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 9kmbr0 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do NOT close backlog `cnwy8g` here: nothing has been re-homed after this child, and closing it would claim a layering correction that has not happened. Child 02 (`1f7xno`) closes it.
