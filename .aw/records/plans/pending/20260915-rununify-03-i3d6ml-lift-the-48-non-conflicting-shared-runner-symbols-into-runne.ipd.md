# IPD: Lift the 48 non-conflicting shared runner symbols into runner_shared with oc as the source

- Date: 2026-09-15
- Kind: child
- Concern: 48 symbols exist in BOTH `oc_runipd.py` and `agy_runipd.py` with no behavioral disagreement between the two BODIES, so every fix to one is a fix the other silently misses. This is the bulk of the `rununify` duplication. CORRECTED AT REVIEW 2026-09-16: "no behavioral disagreement" is NOT the same as "liftable", and this plan originally conflated them. Measured, only 5 of the 48 are liftable with no prerequisite and no observable change; 10 are ALREADY single-implementation behind a maintainer-ruled injection wrapper and MUST NOT be touched; 1 is pinned UNMOVABLE; and 32 need at least one symbol or constant that is neither in the 48 nor yet in `runner_shared`. See F-7 through F-14 and OQ-03.
- Scope: Move the liftable subset to `runner_shared.py`, taking the `oc_runipd` version as the source per the maintainer's 2026-09-14 ruling, and leave each host reaching the shared name. THE EXACT SUBSET IS NOT YET SETTLED and is OQ-03, which is `Blocking: yes`: the re-scope needed to make this plan sound restructures a Set with nine pending children and an approved orchestrator whose retirement gate reads the child table, so it is the maintainer's call, not the executor's. No behavior change, no host parameter needed (the 8 symbols that DO need one are child 04's).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_rununify_lift.py, tests/test_runner_refork_guard.py, tests/test_runner_backlog_close.py, tests/test_runner_shutdown.py, tests/test_orchestrator_probe_cache.py, tests/test_lane_allocation_idempotent.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: rununify
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: i3d6ml
- From-Backlog: alw22r

## Workflow history
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 12 findings (PR-001..PR-012), 10 FIXED, PR-001/PR-004 OPEN and escalated as blocking OQ-03. Plan linted clean but measured the wrong property (body equality, not closure), so 43 of its 48 symbols are not liftable as written and 11 must never move. Revised in place to the 9 sound symbols; the re-scope decision is the maintainer's.
- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-001 through PR-012 (10 FIXED, PR-001 and PR-004 OPEN and escalated as the new blocking OQ-03). THE PLAN LINTED CLEAN AND WAS NOT EXECUTABLE, because it measured the wrong property: it partitioned the 66 shared symbols by BODY EQUALITY and treated the 48 that agree as liftable, but a definition can move only if every module-level name it closes over resolves in `runner_shared`. Re-measured with that closure test at HEAD `476354fc`: 5 of 48 are liftable, 4 more are liftable but change observable output, 11 must NEVER move, and 28 need a prerequisite. As written each of E-02/E-03/E-04 would fail partway through on an import-time `NameError` after partially relocating a 9,375-line and a 5,727-line module. WORST FINDING: E-02 directed the executor to DELETE the 10 `INJECTED` host wrappers, which are already single-implementation and whose wrapper is a maintainer ruling (`818uru` OQ-02, quoted in `oc_runipd.py:557`, asserted by `SingleDefinitionTests`) with two recorded rejected alternatives; E-03 separately included `disable_lane_prompt`, pinned unmovable in three places because lifting it silently breaks prompt suppression in unattended runs. Also found a Set-level cycle the dependency checker cannot see (6 symbols need children 04/05/06, all of which declare `executed:i3d6ml`), a right-sizing failure the count-based lint could not detect (~1,850 lines in three items), and two right answers resting on false premises, both corrected: OQ-02's "nothing parses these filenames" is false (`run_analytics_statistics.py:1248` does, so agy's verifier logs are TODAY misclassified and adopting oc's form REPAIRS a live defect), and `write_prompt`'s difference is semantic rather than tag order. REVISED IN PLACE to 9 sound symbols with the 11 exclusions converted into a deliverable plus proof-of-absence evidence, bidirectional non-vacuity, 5 missing test files fenced, and the suite bar corrected against a measured pre-existing flake (7308 passed, 1 load-dependent timeout that passes in isolation). NOT DECIDED, deliberately: which of four re-scopes the Set should take, since each restructures a Set with nine pending children and an approved orchestrator. Typed record at `.aw/records/reviews/20260916-rununify-03-i3d6ml-lift-the-48-non-conflicting-shared-runner-symbols-into-runne.review.md` with 12 findings and 5 decisions, 2 of them irreversible and escalated.
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored against a fresh measurement at HEAD; the parent's E-01 inventory of 2026-09-03 is stale and the corrected numbers are recorded in Findings.

## Goal

Collapse the shared symbols that carry no behavioral disagreement into ONE definition in
`runner_shared.py`, so a fix lands once and reaches both hosts. This is the largest slice of the
`rununify` Set and it unblocks the parent's placeholder child rows.

READ THIS BEFORE EXECUTING. It is NOT the lowest-risk slice, and it is NOT executable as authored.
The 2026-09-16 review re-measured every one of the 48 and found the plan's central premise inverted:
"the two bodies agree" was treated as "the definition can move", and those are different properties.
A lift is possible only when EVERY module-level name the body closes over is already resolvable in
`runner_shared`, and for 43 of the 48 it is not. The honest partition, measured (method in F-7):

| Group | Count | What it is | Where it belongs |
|---|---|---|---|
| A | 5 | Liftable today, closure-clean, no prerequisite | this plan |
| B | 4 | Liftable today but their OBSERVABLE output differs between hosts | this plan, only with the change disclosed |
| C | 10 | ALREADY one implementation behind a maintainer-ruled injection wrapper | OUT: touching them reverses a ruling |
| D | 1 | `disable_lane_prompt`, pinned UNMOVABLE by a test whose reason still holds | OUT |
| E | 6 | Blocked on a module CONSTANT (or transitively on a group-E symbol) | a new precursor child, or a declared E-item here |
| F | 6 | Blocked on an oc-only HELPER that is not in the 48 | a new precursor child |
| G | 6 | Blocked on a symbol child 04, 05 or 06 owns | AFTER those children; inverts this plan's position in the Set |
| H | 10 | Blocked only on a plain `import` line the shared module lacks | trivial, but must be stated |

5 + 4 + 10 + 1 + 6 + 6 + 6 + 10 = 48, so every symbol the plan claimed is accounted for and none is
double-counted. Per-group membership is in "Deferred / out of scope" below; per-symbol blockers are
what E-01 must reproduce.

Groups C and D are the load-bearing correction: 11 of the 48 must NOT be lifted at all, and for 10 of
them this plan's own E-02 instructs the executor to do the opposite of what the maintainer ruled.
Group G is the sequencing correction: this plan declares `Item-Dependencies: none` while six of its
symbols depend on children that declare `executed:i3d6ml` and therefore cannot run first.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the lift

EXECUTOR: DO NOT START. OQ-03 is `Blocking: yes` and the lint gate refuses this plan at every
checkpoint until the maintainer answers it. The checklist below is REWRITTEN to the measured reality
but it is deliberately NOT a complete authorization: E-02 and E-03 name the two groups whose scope
depends on the answer.

- [ ] E-01 RE-MEASURE the closure at execution HEAD before moving anything, and refuse to proceed on a stale list. The method must be the CLOSURE test, not the body-equality test the original plan used: for each candidate, parse the `oc_runipd` definition, collect every free name that resolves at module level, and report which of those are (a) already defined in `runner_shared`, (b) inside the candidate set so they move together, or (c) NEITHER, which makes the candidate unliftable until its prerequisite moves. Emit the eight groups A through H from the Goal table with their members, and state any symbol that changed group since 2026-09-16 by name.
  - Depends on: none
  - Expected outcome: a pasted group listing at execution HEAD produced by the closure method, with per-symbol prerequisites named for every blocked candidate; any drift from the groups recorded in the Goal table and F-7 is stated explicitly with the symbol name and its new group.
  - Execution state: pending

- [ ] E-02 Lift GROUP A ONLY, the 5 that are closure-clean today: `EmptyStatusSelection`, `StallTimeout`, `_findings_block_reason`, `build_review_prompt`, `make_integration_validation_runner`. Define each once in `runner_shared` and have both runners reach the shared object, so `oc_runipd.X is agy_runipd.X` holds. NOTE THE TWO EXCEPTION CLASSES ARE THE RISKY PAIR despite being 2 and 20 lines: each runner's `main` catches its OWN today, and `tests/test_runner_shared.py:1305` asserts `StallTimeout` is a `DriverError` subclass in both, so unifying them changes which `except` clause catches a cross-host raise. Prove the catch still works rather than assuming it.
  - Depends on: E-01
  - Expected outcome: 5 single definitions in `runner_shared`, `is`-identical from both hosts, `__module__` reporting `runner_shared`; and for the two exception classes a demonstrated raise-and-catch through each runner's `except DriverError`.
  - Execution state: pending

- [ ] E-03 Lift GROUP B, the 4 that are closure-clean but whose OBSERVABLE OUTPUT differs between the hosts, and disclose each change: `attempt_log_path` and `write_prompt` (F-4/F-11, the filename shape), `resolve_prior_lane` and `sync_receipt_into_worktree`. For `write_prompt` the difference is NOT tag order but SEMANTICS: oc treats `suffix` as REPLACING the `exec`/`review` prefix while agy treats it as an ADDITIONAL tag, so the same call produces `03-abc123-verify-attempt-1.md` on oc and `03-abc123-exec-verify-attempt-1.md` on agy. For `attempt_log_path` the consequence is worse than cosmetic: `run_analytics_statistics._VERIFY_LOG_RE` (`agent_workflows/run_analytics_statistics.py:1248`) matches `-attempt-<n>-verify.jsonl`, which is oc's shape, so agy's verifier logs are ALREADY invisible to the verifier-phase analytics and adopting oc's form FIXES a live defect. Say so in the report; do not present it as a neutral rename.
  - Depends on: E-01
  - Expected outcome: 4 single definitions; the `write_prompt` semantic difference stated as a semantic change with both filenames shown; the `attempt_log_path` unification recorded as REPAIRING agy's analytics invisibility, with the regex it now satisfies cited.
  - Execution state: pending

- [ ] E-04 DO NOT TOUCH GROUP C OR GROUP D, and record why in the execution report rather than silently skipping them. Group C is the 10 INJECTED symbols (`run_checked`, `save_state`, `discover_plans`, `validate_manifest`, `print_status`, `git_head`, `git_status`, `git_common_dir`, `build_lane_outcome`, `integrate_lane_branch`): each already has exactly ONE implementation in `runner_shared` and keeps a deliberate one-line host wrapper that binds a host-specific dependency, a shape the maintainer ruled on in `818uru` OQ-02 and which `tests/test_runner_shared.py:573` asserts must persist. Group D is `disable_lane_prompt`, pinned by `tests/test_runner_shared.py:1238` because it writes `_LANE_PROMPT_DISABLED` through `global` while each host's `_lane_reclaim_prompt` reads its own copy. This item's DELIVERABLE is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later.
  - Depends on: E-01
  - Expected outcome: an execution-report paragraph naming all 11 excluded symbols, the ruling or pinned test that excludes each, and the explicit statement that lifting them would reverse a decision rather than complete this plan.
  - Execution state: pending

### Task group 2: proof

- [ ] E-05 Add `tests/test_rununify_lift.py` asserting the lift held FOR THE SYMBOLS THIS PLAN ACTUALLY LIFTED (groups A and B, 9 symbols), driven by a NAMED TABLE in the test file rather than by the literal 48: each name resolves to the same object from both hosts, `runner_shared` is its defining module, and no runner holds a second `def`/`class` for it (AST scan, repo-wide per the parent's F10, not a pairwise check). The table must also carry the EXCLUDED sets so the test states the boundary: group C is asserted to STILL have its host wrapper (the inverse assertion), and group D is asserted to still be defined in both runners. A test asserting only what moved would let a later agent "complete" the lift by deleting a wrapper the maintainer ruled must stay.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a test file that FAILS if any lifted symbol is re-forked into a runner AND fails if an excluded symbol is lifted, naming which symbol broke in either direction.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic (6231 lines at authoring,
  confirmed at review), created by this Set's own child `818uru`. It imports no runner, which is why it
  can hold both hosts' shared code without a cycle. NOTE the corollary the original plan missed: it
  also imports very little else, which is exactly why 32 of the 48 cannot move yet.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` (`:308`) asserts the
  SUBSTRING `import oc_runipd` never appears in `agy_runipd`. NOTE FOR THE EXECUTOR: agy currently
  satisfies that guard only on a technicality, using the symbol-level `from agent_workflows.oc_runipd
  import X` spelling because the substring test looks for the module-alias form.
  `enforce_dependency_preflight` documents this in its own body (`agy_runipd.py:1538`). CORRECTED AT
  REVIEW: the original plan claimed E-02 "removes those imports outright and makes the guard
  meaningful again". It does not. Only 5 of the 57 oc-to-agy imports are among the 48, and 4 of those 5
  are blocked, so the guard stays as technically-satisfied as it is today.
- The oc-to-agy import count is pinned at 57 by
  `tests/test_orchestrator_probe_cache.py::test_the_oc_to_agy_import_count_did_not_increase` (`:1203`).
  Re-measure it and record the new count with a note, exactly as its own message instructs; do not
  delete the assertion. Realistic decrease from this plan as re-scoped: one.
- THE INJECTION-WRAPPER CONVENTION IS A RULING, NOT AN ACCIDENT (`818uru` OQ-02, quoted verbatim in
  `oc_runipd.run_checked`'s docstring at `oc_runipd.py:557`): where shared code needs a host-specific
  dependency, the dependency is passed EXPLICITLY at exactly one visible site per runner via a one-line
  host wrapper. Threading the parameter through every call site was rejected (86 call sites), and a
  registration seam was rejected separately (import-order-dependent global state). `INJECTED` in
  `tests/test_runner_shared.py:76` is the enumerated set. An agent that reads "the runners still each
  have a `def run_checked`" as remaining duplication will undo a decision; the test at `:573` is what
  stops it.
- `TERMINAL_STATES`, `FULL_AUTO_APPROVAL_MESSAGE`, `LANE_PROMPT_TIMEOUT`, `_SIGINT_GRACE_SECONDS` and
  `_SIGTERM_GRACE_SECONDS` are byte-identical in both runners and defined in NEITHER
  `runner_shared` nor any shared module, so they are the cheapest real precursor available. But note
  `tests/test_runner_backlog_close.py:1141` and `tests/test_runner_shutdown.py:160` both assert on
  `inspect.getsource(mod.terminate_process)` containing the two grace-constant NAMES, and
  `tests/test_runner_shutdown.py:173` mutates `oc._SIGINT_GRACE_SECONDS` and requires the change to
  reach the shared reaper. Moving those constants without keeping a per-runner binding breaks all three.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | parent `5e4sb6` E-01 note, artifact `tvnq50` | THE INVENTORY IS STALE and its headline number is the reason this Set stalled. It recorded 88 shared symbols, 52 diverged, and 46 undecided pending human reading. Re-measured at HEAD: 66 shared, and the "needs a human decision" set is FOUR, not 46. |
| F-2 | HIGH | measured at HEAD | The 66 shared symbols partition as: 14 already delegating, 21 identical code with prose-only differences, 8 differing only in a host label/title/argv token, 2 genuine behavior conflicts, 3 record-type coupled, 5 large host-shaped functions, and 13 mechanical-only. The 48 in THIS plan carry no disagreement at all. CONFIRMED AT REVIEW 2026-09-16: the 66 total and this seven-way partition both REPRODUCE exactly. The defect is not the count; it is the inference drawn from it, that "no disagreement" implies "liftable" (F-7). |
| F-3 | MED | `agy_runipd.py` | 14 symbols are already thin wrappers delegating to oc or to `runner_shared`. The duplication for these is nominal, but the delegating stub keeps a runner-to-runner import alive, which is why they are in scope rather than skipped. |
| F-4 | MED | `attempt_log_path`, `write_prompt` | These two differ in the ORDER of the filename tag (`-{id6}-{prefix}{tag}` vs `-{id6}{tag}-{prefix}`), so unifying CHANGES ON-DISK FILENAMES for one host. Not a behavior change in logic but it is observable, so it must be stated rather than absorbed. |
| F-5 | MED | `reconcile_disposition`, `reconcile_interrupted`, `retry_deferred_integrations` | agy uses the DEFENSIVE form (`item.get('configured_file','')`, `dict(item)`) where oc indexes directly. Blind application of "oc wins" would reintroduce a `KeyError` on a recovery path where the key can legitimately be absent. This plan keeps agy's form for exactly these three and says so. |
| F-6 | LOW | `tests/test_orchestrator_probe_cache.py:1203` | The oc-to-agy import count baseline (57) will DROP when a lift removes an import, failing that assertion. Expected, and the assertion's own message prescribes re-measuring rather than deleting. CORRECTED: only 5 of the 57 imports are among the 48 (`build_verify_and_continue_notice`, `classify_recovery_disposition`, `enforce_dependency_preflight`, `resolve_prior_lane`, `route_recovery_turn`), and 4 of those 5 are BLOCKED (group F or G), so the realistic decrease from this plan as re-scoped is ONE, not fourteen. |

### Findings added by the 2026-09-16 plan review

| # | Sev | Where | Finding |
|---|---|---|---|
| F-7 | BLOCKER | the plan's own method | THE PARTITION MEASURES THE WRONG PROPERTY. Body equality (AST-compare with docstrings stripped) says the two hosts AGREE; it says nothing about whether the definition can MOVE. A definition can move only if every module-level free name it closes over is resolvable in `runner_shared`. Re-measured with that closure test at HEAD: of the 48, exactly 5 are closure-clean, 4 more are closure-clean but change observable output, and 32 close over at least one name that is neither in `runner_shared` nor in the 48. The three E-items would each fail partway through on a `NameError` at import time. |
| F-8 | BLOCKER | E-02 as authored; `tests/test_runner_shared.py:76`, `:541`, `:573` | E-02 INSTRUCTS THE EXECUTOR TO REVERSE A MAINTAINER RULING. Ten of its fourteen "already thin delegations" (`run_checked`, `save_state`, `discover_plans`, `validate_manifest`, `print_status`, `git_head`, `git_status`, `git_common_dir`, `build_lane_outcome`, `integrate_lane_branch`) are the `INJECTED` set: the implementation is ALREADY single and shared, and the one-line host wrapper is the DELIBERATE mechanism that binds a host-specific dependency (`pinned_child_env`, `write_report`, `parse_plan_file`, `parse_dependency_token`, `driver_label`, `run_checked`, `host_label`). `oc_runipd.run_checked`'s docstring records the ruling and the two rejected alternatives; `SingleDefinitionTests` asserts the wrapper persists. E-02's "deletes the delegating stub" would delete exactly what that ruling installed, for zero de-duplication gain. |
| F-9 | BLOCKER | E-03 as authored; `tests/test_runner_shared.py:1238`, `agent_workflows/runner_shared.py:95`, `:620` | E-03 INCLUDES A SYMBOL THREE PLACES DECLARE UNMOVABLE. `disable_lane_prompt` writes `_LANE_PROMPT_DISABLED` through `global`. Lifting it makes it write the SHARED module's flag while each host's `_lane_reclaim_prompt` keeps reading its OWN, so prompt suppression on a repeated interrupt silently stops working. The symptom is an unattended run pausing for a question nobody is there to answer. `UnmovableSymbolTests` pins it, `runner_shared` documents the exclusion twice, and `tests/test_lane_allocation_idempotent.py:816` exercises the behavior in both hosts. |
| F-10 | HIGH | `- Item-Dependencies: none`; the six blocked symbols | THE DECLARED DEPENDENCY DIRECTION IS BACKWARDS FOR SIX SYMBOLS. `save_state` needs `write_report` (child 04), `_escalation_recorder`/`handle_stop_command`/`install_stop_triggers` need `_detect_driver_command` (child 04), `driver_finalize` needs `_compute_scope_reconciliation` (child 04), `reconcile_interrupted` needs `extract_session_id` (child 05), and `discover_plans`/`expand_selectors` need `parse_plan_file` (child 06). All three of those children declare `Item-Dependencies: executed:i3d6ml`, so they cannot precede this plan and this plan cannot precede them. As authored the Set contains a cycle in fact, though not one the dependency checker can see, because the coupling is by SYMBOL and the declaration is by PLAN. |
| F-11 | HIGH | `write_prompt` in both runners; `agent_workflows/run_analytics_statistics.py:1248` | F-4 UNDERSTATES ITS OWN FINDING TWICE. First, `write_prompt`'s difference is SEMANTIC, not tag order: oc's `suffix` REPLACES the `exec`/`review` prefix, agy's ADDS to it, so the verifier prompt is `03-abc123-verify-attempt-1.md` on oc and `03-abc123-exec-verify-attempt-1.md` on agy. Second, `attempt_log_path`'s divergence is a LIVE DEFECT, not a cosmetic one: `_VERIFY_LOG_RE` matches `-attempt-<n>-verify.jsonl`, which only oc produces, so every agy verifier log is already misclassified as an execute log by the verifier-phase analytics. Adopting oc's form REPAIRS that. A plan that files this under "mechanical only" loses the one user-visible improvement it makes. |
| F-12 | HIGH | E-04's premise; `enforce_dependency_preflight`, `reconcile_disposition`, `retry_deferred_integrations` | THREE OF THE THIRTEEN "MECHANICAL ONLY" SYMBOLS ARE NOT MECHANICAL. `enforce_dependency_preflight` in agy is not a formatting variant: it is a documented cross-runner import wrapper carrying a deliberate `except DriverError: raise` and a 12-line note on why the narrowed guard stays (`agy_runipd.py:1530`), plus a host-divergent `DEPENDENCY_FATAL_RULES` (oc-only). `reconcile_disposition` closes over `TERMINAL_STATES`, `_read_status`, `runner_stop` and `runner_shared`. `retry_deferred_integrations` closes over the oc-only `process_backlog_close`. Calling these mechanical invites an executor to lift them without noticing the prerequisite. |
| F-13 | MEDIUM | F-5 and OQ-01's defensive-form claim | THE DEFENSIVE-FORM EXCEPTION IS ARGUED FROM THE WRONG DIRECTION, though the conclusion is right. F-5 says keeping agy's `.get` avoids a `KeyError` "on a recovery path", which reads as speculative. It is not: `initialize_run` writes `configured_file` on every queue entry it freezes (`oc_runipd.py:3452`, `agy_runipd.py:2267`), so a live entry always has it, and the exposure is a queue entry frozen by an OLDER driver version being resumed. That is a REAL and narrow case, and oc itself already hedges 9 of its own 13 call sites with `.get`. The defensive form is correct; state the actual reason so a future reader does not "simplify" it back. |
| F-14 | MEDIUM | E-02/E-03/E-04 right-sizing | EACH E-ITEM BUNDLES A WHOLE GROUP AS ONE PASS, and the count-based lint cannot see it. E-02 moved 14 symbols across 400 oc lines, E-03 21 symbols across 664, E-04 13 symbols across 783: nearly 1,850 lines relocated in three items, each needing its own dependency analysis, its own docstring merge decision, and its own import rewiring in two 5,700-to-9,400-line files that the parent plan itself calls the highest-contention files in the repo. A failure midway leaves the package unimportable. The re-scoped items are 5, 4 and 0 symbols, which is one focused pass each. |
| F-15 | MEDIUM | `- Scope-Paths:` as authored | THE SCOPE FENCE OMITS FIVE TEST FILES THE CHANGE MUST EDIT. Named for the executor rather than discovered at finalize time: `tests/test_runner_refork_guard.py` (its `Owned` table enumerates shared symbols and its comment block explains the INJECTED and UNMOVABLE exclusions), `tests/test_runner_backlog_close.py:1141` (asserts `terminate_process`'s source contains the two grace constants), `tests/test_runner_shutdown.py:160` (same, via `inspect.getsource`), `tests/test_orchestrator_probe_cache.py:1203` (the import-count baseline), and `tests/test_lane_allocation_idempotent.py:816` (the prompt-suppression behavior in both hosts). Added to `Scope-Paths`. |
| F-16 | LOW | V-05(c)'s baseline claim | THE SUITE BASELINE IS CORRECT AND ITS ZERO-FAILURE BAR IS NOT ACHIEVABLE AS STATED. Measured at HEAD: `7308 passed, 3 skipped, 2 xfailed` with ONE failure, `test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, which is a 30-second subprocess timeout under parallel load and PASSES in isolation (`7 passed in 1.13s`). V-05 should require no NEW failures against that named pre-existing flake rather than zero failures absolutely, or the executor will chase a defect this plan did not cause. |

## Proposed changes (ordered, validatable)

1. Re-measure the CLOSURE at execution HEAD (E-01) and refuse to proceed on a stale list.
2. Lift group A, the 5 closure-clean symbols (E-02), proving the exception-class catch still works.
3. Lift group B, the 4 whose observable output changes, disclosing each change (E-03).
4. Record the group C and group D exclusions as a deliverable, not a silent skip (E-04).
5. Add the anti-re-fork suite, asserting BOTH what moved and what must not move (E-05).

## Deferred / out of scope (with reason)

- The 8 host-parameter symbols (`driver_actor`, `write_report`, `build_prompt`,
  `build_verifier_prompt`, `render_continuation_hint`, `enforce_requested_action`,
  `_detect_driver_command`, `_compute_scope_reconciliation`): child 04. They need a host-label
  parameter designed once, which is a different act from a lift.
- `extract_session_id` and `driver_begin`: child 05. Genuine behavior conflicts needing the maintainer's
  union/adopt rulings.
- `PlanRecord`, `parse_plan_file`, `build_dynamic_manifest`: child 06. Coupled to a test that
  explicitly PINS the two record types as distinct, so unifying them overrides an earlier decision.
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11, one
  each. These are genuinely host-shaped and need a core/hook split, not a winner.

### Removed from scope by the 2026-09-16 review (F-8, F-9)

- GROUP C, the 10 INJECTED symbols (`run_checked`, `save_state`, `discover_plans`,
  `validate_manifest`, `print_status`, `git_head`, `git_status`, `git_common_dir`,
  `build_lane_outcome`, `integrate_lane_branch`). NOT deferred: PERMANENTLY out of scope. Each is
  already a single shared implementation, and its host wrapper is the ruled mechanism for binding a
  host dependency (`818uru` OQ-02, quoted in `oc_runipd.run_checked`'s docstring). There is nothing
  here to de-duplicate.
- GROUP D, `disable_lane_prompt`. Permanently out of scope for the `global` reason pinned in
  `tests/test_runner_shared.py:1238`.

### Blocked on a precursor, not on a later child (groups E, F, H: 22 symbols)

These are genuinely liftable and genuinely blocked, so they are named with their blocker rather than
dropped. Whether they belong in a re-scoped version of THIS plan or in a new precursor child is OQ-03.

- GROUP E (6), blocked on a module CONSTANT, directly or transitively. `terminate_process` needs
  `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS`; `_lane_reclaim_prompt` needs
  `LANE_PROMPT_TIMEOUT`; `reconcile_disposition` needs `TERMINAL_STATES`; and three more follow
  transitively because they call a group-E symbol (`StallWatchdog` calls `terminate_process`,
  `locked_run` calls `run_lock`, `reclaim_lanes_on_interrupt` calls `_lane_reclaim_prompt`). All five
  constants are byte-identical across hosts, so they can simply move, subject to the three tests named
  in Project conventions that assert on the constant NAMES inside `terminate_process`'s source.
- GROUP F (6), blocked on an oc-only HELPER. `build_verify_and_continue_notice`,
  `classify_recovery_disposition` and `route_recovery_turn` need `RecoveryDisposition`, the three
  `DISPOSITION_*` constants and `_lane_commit_subjects`; `retry_deferred_integrations` needs
  `process_backlog_close`; `enforce_dependency_preflight` needs `preflight_dependency_findings` AND a
  host-divergent `DEPENDENCY_FATAL_RULES` (oc-only); `set_plan_approved` needs `pinned_module_argv` AND
  a host-divergent `FULL_AUTO_ACTOR` (`'aw oc run --full-auto'` vs `'aw agy run --full-auto'`). THE
  LAST TWO ARE THEREFORE CHILD 04's, not a precursor's: a host-divergent constant is exactly the host
  descriptor child 04 designs.
- GROUP H (10), blocked ONLY on an `import` line `runner_shared` lacks: `argparse`
  (`_add_output_mode_flags`, `retry_deferred_integrations`), `runner_stop` (`_budget_breach_recorder`,
  `_observe_between_turn_stop`, `_record_checkpoint_stop`, `_record_deliberate_stop`,
  `_record_forced_stop`, `requeue_interrupted`), `lane_containment` (`build_isolation_notice`,
  `evaluate_clean_base_for_launch`), `platform_lock` and `runner_shutdown` (`run_lock`), plus `select`
  and `Iterable`. Trivial, with ONE trap: `lane_containment` already imports `runner_shared` at module
  level (`agent_workflows/lane_containment.py:55`), so adding it at module level creates an import
  CYCLE. It must be a function-local import, the convention `runner_shared` already uses in 20-plus
  places.

### Blocked on a LATER child, which is the sequencing defect (group G: 6 symbols)

Named separately because these are the ones that make `- Item-Dependencies: none` false (F-10):
`_escalation_recorder`, `handle_stop_command` and `install_stop_triggers` need
`_detect_driver_command` (child 04); `driver_finalize` needs `_compute_scope_reconciliation` (child
04); `reconcile_interrupted` needs `extract_session_id` (child 05); `expand_selectors` needs
`parse_plan_file` (child 06). Children 04, 05 and 06 all declare `Item-Dependencies: executed:i3d6ml`.

## Scope check

- Over-scope: none, after the review removed groups C and D.
- Under-scope: this plan as re-scoped lifts 9 symbols, not 48, and reduces neither runner's line count
  materially. That is the honest size of the "no judgement call needed" slice; the original 48 figure
  counted 10 symbols that are already unified, 1 that must never move, and 32 that need a prerequisite.

## Required tests / validation

1. `tests/test_rununify_lift.py` (new): object identity across both hosts for the 9 symbols this plan
   lifts, `__module__` is `runner_shared`, an AST scan proving no runner re-forks any of them, AND the
   inverse assertions that the 10 group-C wrappers and the 1 group-D definition are still present.
2. The existing guards must stay green, named because they constrain this change:
   `tests/test_runner_shared.py` (especially `SingleDefinitionTests` at `:541` and
   `UnmovableSymbolTests` at `:1238`, both of which the ORIGINAL scope would have broken),
   `tests/test_runner_refork_guard.py`,
   `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` (`:308`),
   `tests/test_orchestrator_probe_cache.py` (its import-count baseline re-measured with a note),
   `tests/test_lane_allocation_idempotent.py:816` (prompt suppression in both hosts).
3. Both hosts' suites: `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.
4. Bare `python3 -m pytest`, summary line pasted, at or above the 7308-passed baseline MEASURED AT
   REVIEW 2026-09-16, with the one known flake named in F-16 excluded by showing it green in isolation.
5. NON-VACUITY IN BOTH DIRECTIONS: sabotage a lifted shared definition and show a named failure; AND
   re-fork an excluded group-C wrapper into a second body and show a named failure. A lift suite that
   only proves what moved cannot catch the more likely mistake, which is lifting something that must
   not move.
6. IMPORT-CYCLE CHECK, because group H makes it reachable: `lane_containment` imports `runner_shared`
   at module level (`agent_workflows/lane_containment.py:55`), so any shared code needing
   `lane_containment` must import it inside the function. Show `python3 -c "import
   agent_workflows.oc_runipd, agent_workflows.agy_runipd"` clean, in both import orders.

## Spec / documentation sync

No `.spec.md` change. This is an internal refactor with no operator-visible contract change, with ONE
exception to disclose: F-4's filename unification changes a prompt/log filename for one host. That is
not spec-governed (no spec names those filenames), but it must appear in the execution report.

CHECKED AT REVIEW 2026-09-16 and the conclusion HOLDS, with the reasoning recorded so the next reader
need not re-derive it. Two specs are adjacent and neither is amended. Spec `25kzda` 2.1 declares a
CLOSED run-flag list which `tests/test_run_flag_surface.py` asserts against the spec file, and
`_add_output_mode_flags` (group H) touches display flags that `oc_runipd.py:8529` records as
deliberately NOT registered in that table, so lifting it changes no declared flag. Spec `c4gd2h` R5
forbids a second `terminate_process` implementation, and this plan reduces implementations rather than
adding one, so it moves toward that requirement. NOTE the honest caveat for whoever executes group E:
`c4gd2h` R5's guard is asserted through `inspect.getsource` on each runner's `terminate_process`
(`tests/test_runner_shutdown.py:160`, `tests/test_runner_backlog_close.py:1141`), so a lift that leaves
no per-runner binding fails those tests without any spec having changed.

## Open questions

### OQ-01: For the three defensive-form cases, does "oc is preferred" override the safer form?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: NO. The maintainer's ruling was "oc_runipd.py is always the
  preferred version UNLESS there are significant differences (one does A the other NOT A)". A direct
  index versus a defaulted `.get` on a recovery path IS such a difference: one raises where the other
  continues, and the raising form is reachable when `configured_file` is absent from a frozen queue
  entry. Keeping agy's defensive form is the ruling applied, not an exception to it.
  SHARPENED AT REVIEW 2026-09-16 (F-13), because the original rationale reads as speculative and a
  future reader would "simplify" it away: the key is written on EVERY queue entry `initialize_run`
  freezes (`oc_runipd.py:3452`, `agy_runipd.py:2267`), so a live entry always carries it and the real
  exposure is narrow and specific: a queue frozen by an OLDER driver build and resumed by this one.
  Independent corroboration that the defensive form is already house style: oc itself uses
  `.get('configured_file','')` at 9 of its own 13 call sites and indexes directly at only 4. NOTE the
  three symbols this question governs are all BLOCKED for other reasons (`reconcile_disposition` on
  `TERMINAL_STATES`, `reconcile_interrupted` on child 05's `extract_session_id`,
  `retry_deferred_integrations` on `process_backlog_close`), so the decision stands but is not
  exercised by this plan as re-scoped.

### OQ-02: Should the filename-order difference (F-4) be resolved toward oc even though it renames files?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: Yes, oc's order, per the standing ruling. Reaching the right
  answer for the WRONG REASON, corrected at review 2026-09-16 (F-11). The claim "nothing parses them
  by position (they are globbed by `id6`)" IS FALSE, and it was the only stated basis. Something does
  parse by position: `run_analytics_statistics._VERIFY_LOG_RE`
  (`agent_workflows/run_analytics_statistics.py:1248`) is anchored on `-attempt-<n>-verify.jsonl`,
  which is oc's shape ONLY, so every agy verifier session log is TODAY misclassified as an execute log
  by the verifier-phase analytics. `run_viewer.py:761` looks for the same oc-shaped name first and
  falls back to a loose glob, so it degrades rather than breaks. The answer is therefore still oc's
  form, but because adopting it REPAIRS a live analytics defect on the agy side, not because the names
  are unparsed. That reframing is what makes it a disclosed improvement rather than an accepted risk.
  Also corrected: the `write_prompt` difference is SEMANTIC (oc's `suffix` replaces the prefix, agy's
  appends), not a tag reordering.

### OQ-03: This plan's 48-symbol scope is not achievable. Which re-scope do you want?

- Blocking: yes
- Finding: PR-001, PR-004
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT RESOLVABLE FROM REPOSITORY EVIDENCE, which is why it is asked
  rather than decided. The evidence settles WHAT IS TRUE (the measurement in F-7 and the Goal table);
  it does not settle what this Set should DO about it, and every available answer changes the shape of
  a Set that has nine pending children plus an approved orchestrator (`5e4sb6`) whose retirement gate
  reads the child table. Restructuring that is a scope and priority decision, which
  GUIDING_PRINCIPLES reserves to the human.
  THE FACTS, all measured at HEAD 476354fc and reproducible by E-01's method:
  (a) 5 of the 48 are liftable today with no prerequisite;
  (b) 4 more are liftable today but change observable output, one of which repairs a live agy
  analytics defect (F-11);
  (c) 11 must NEVER be lifted, 10 because a maintainer ruling installed their host wrapper (F-8) and 1
  because a `global` write pins it (F-9);
  (d) 15 are liftable after a precursor moves a constant, a helper, or an import (groups E, F, H);
  (e) 6 need a symbol that children 04, 05 and 06 own, and all three of those children declare
  `Item-Dependencies: executed:i3d6ml`, so they cannot precede this plan (F-10).
  WHAT I ALREADY DID, so no answer starts from nothing: the checklist above is rewritten to the 9
  symbols that are sound today (E-02, E-03), the 11 exclusions are made an explicit deliverable rather
  than a silent skip (E-04), and every blocked symbol is named with its blocker in "Deferred / out of
  scope". So this plan is EXECUTABLE AS REVISED and delivers a real, if small, slice. The question is
  what happens to the other 39.
  The options, with what each costs:
  1. EXECUTE AS REVISED (9 symbols) and let a NEW precursor child take groups E, F and H, with group G
     folded into children 04 through 06 where those symbols already live. Smallest safe step; the Set
     grows by one child and children 04 to 06 grow slightly.
  2. RE-SCOPE THIS PLAN UPWARD to 24 symbols by absorbing groups E, F and H as declared E-items here
     (move the 5 shareable constants, the 6 oc-only helpers, the imports, then lift). No new child, but
     this plan stops being a "lift" and becomes a lift-plus-extraction, roughly tripling its size and
     re-introducing the right-sizing problem F-14 records.
  3. RETIRE THIS PLAN as superseded and re-derive the whole remaining Set from the closure measurement,
     which would produce a different and probably smaller set of children in dependency order. Most
     honest, most expensive, and it invalidates the nine pending children's numbering.
  4. EXECUTE AS REVISED and open a BACKLOG ITEM for the remaining 39 rather than authoring children
     now, deferring the Set-shape decision until the small slice has landed.
  My recommendation is OPTION 1: it keeps every child single-concern, preserves the existing numbering,
  and the precursor child is a genuinely separate act (extracting a constant is not lifting a
  function). I did NOT act on it, because creating a child and re-pointing three children's
  dependencies restructures the Set.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted group listing produced at execution HEAD BY THE CLOSURE METHOD, showing all eight groups A through H with their members and, for every blocked candidate, the specific prerequisite name that blocks it. Plus an explicit statement of any symbol that changed group since 2026-09-16. A listing produced by body-equality alone does NOT satisfy this item, because that is the measurement F-7 found to be the wrong one.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.X is agy_runipd.X` -> `True` and `X.__module__` -> `agent_workflows.runner_shared` for all 5 group-A symbols. PLUS the exception-class proof, which is the risky half: raise each runner's `StallTimeout` and show it caught by the OTHER runner's `except DriverError`, and the same for `EmptyStatusSelection`, with `tests/test_runner_shared.py:1305`'s existing assertions still green.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted identity results for all 4 group-B symbols. PLUS the disclosure, quoted rather than summarized: the before/after filename for `write_prompt` on BOTH hosts for `suffix="verify"` and `suffix="defect-reask"`, showing the semantic difference F-11 names; and for `attempt_log_path`, the before/after filename on both hosts together with a demonstration that `run_analytics_statistics.verifier_phase_of_log` returns `verify` for the new agy name where it returned `execute` for the old one. That last item is the repaired defect and must be shown, not asserted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the exclusion disclosure, plus PROOF THE EXCLUSIONS STILL HOLD, since this item's deliverable is an absence and an absence is what a careless executor silently converts into a change. Paste: for each of the 10 group-C symbols, that a runner-local wrapper still exists and `tests/test_runner_shared.py::SingleDefinitionTests` is green; for `disable_lane_prompt`, that it is still defined in BOTH runners and absent from `runner_shared`, with `UnmovableSymbolTests` green; and the citation (ruling or test) that excludes each of the 11.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_lift.py -o addopts=""` green. (b) The NON-VACUITY control, in BOTH directions, because a one-directional control cannot catch the failure mode that matters here: sabotage three lifted shared definitions and show a NAMED failure each, then restore; AND re-fork one group-C wrapper into a second body and show the new suite names it, then restore. A suite that only checks what moved would bless deleting a wrapper the maintainer ruled must stay. (c) Bare `python3 -m pytest` at or above 7308 passed with NO NEW failures, judged against the ONE known pre-existing flake recorded in F-16 (`ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, a 30s subprocess timeout under parallel load that passes in isolation); if that test fails, show it passing in isolation rather than treating it as a regression. (d) The re-measured oc-to-agy import count with its note, and a statement of the ACTUAL decrease (F-6 measures the realistic figure as one, not fourteen).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. RE-ASSESSED AT REVIEW 2026-09-16 (F-14), because the original
  answer was reached without evaluating conceptual density and the count-based lint cannot see it. As
  AUTHORED the plan failed right-sizing outright: three E-items relocated 14, 21 and 13 symbols across
  400, 664 and 783 lines of `oc_runipd` respectively, roughly 1,850 lines moved between two files the
  parent plan itself calls the highest-contention files in the repo, with each symbol needing its own
  dependency analysis and import rewiring, and a mid-item failure leaving the package unimportable. As
  REVISED the items are 5 symbols, 4 symbols, and a disclosure, which is one focused pass each and a
  genuine `standard`.

OQ-03 IS OPEN AND `Blocking: yes`. `aw ipd lint` refuses this plan at every checkpoint until the
maintainer answers it, including `aw ipd begin`, so it cannot be executed or auto-approved in its
current state. That is the intended gate, not an obstacle to work around: the question is which
re-scope the Set should take, and answering it for the maintainer would restructure a Set with nine
pending children and an approved orchestrator.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`);
never `git add -A` and never push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as
`python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, restated after the 2026-09-16 review:

1. THE GROUP C EXCLUSION (F-8). The single most likely way to damage this repository from this plan is
   to read the 10 surviving one-line host wrappers as leftover duplication and delete them. They are a
   maintainer ruling with two explicitly rejected alternatives. E-04 exists to make that visible and
   V-04 exists to prove it held.
2. `disable_lane_prompt` (F-9). Lifting it produces no error, no test failure that names the cause, and
   a silent loss of prompt suppression whose symptom appears only in an unattended overnight run.
3. V-05(b)'s BIDIRECTIONAL non-vacuity control. A lift suite asserting object identity can pass
   vacuously if it resolves names through the wrong module, and a one-directional control would bless
   over-lifting.
4. `attempt_log_path` (F-11). Verify the analytics claim independently before trusting it: the change is
   presented as repairing a live defect, and a reviewer should confirm `_VERIFY_LOG_RE` really does miss
   agy's current filename rather than take the plan's word for it.
