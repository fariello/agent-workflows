# IPD: Lift the 48 non-conflicting shared runner symbols into runner_shared with oc as the source

- Date: 2026-09-15
- Kind: child
- Concern: 48 symbols exist in BOTH `oc_runipd.py` and `agy_runipd.py` with no behavioral disagreement between the two BODIES, so every fix to one is a fix the other silently misses. This is the bulk of the `rununify` duplication. CORRECTED AT REVIEW 2026-09-16: "no behavioral disagreement" is NOT the same as "liftable", and this plan originally conflated them. Measured, only 5 of the 48 are liftable with no prerequisite and no observable change; 10 are ALREADY single-implementation behind a maintainer-ruled injection wrapper and MUST NOT be touched; 1 is pinned UNMOVABLE; and 32 need at least one symbol or constant that is neither in the 48 nor yet in `runner_shared`. See F-7 through F-14 and OQ-03.
- Scope: Move the liftable subset to `runner_shared.py`, taking the `oc_runipd` version as the source per the maintainer's 2026-09-14 ruling, and leave each host reaching the shared name. THE EXACT SUBSET IS NOT YET SETTLED and is OQ-03, which is `Blocking: yes`: the re-scope needed to make this plan sound restructures a Set with nine pending children and an approved orchestrator whose retirement gate reads the child table, so it is the maintainer's call, not the executor's. No behavior change, no host parameter needed (the 8 symbols that DO need one are child 04's).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_rununify_lift.py, tests/test_runner_refork_guard.py, tests/test_runner_backlog_close.py, tests/test_runner_shutdown.py, tests/test_orchestrator_probe_cache.py, tests/test_lane_allocation_idempotent.py, tests/test_resumedupe.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: rununify
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: i3d6ml
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 executed (opencode/its_direct-pt3-claude-opus-5-1m-us): Lift the 9 closure-clean shared runner symbols into runner_shared (group A's 5, group B's 4), each is-identical from both hosts with no second definition in the package, plus tests/test_rununify_lift.py asserting both directions so the 11 deliberate exclusions fail loudly if someone finishes them. Includes a live defect repair: attempt_log_path makes agy emit oc's verifier-log filename shape, so run_analytics_statistics stops misclassifying every agy verifier log as an execute log. Work landed in d26c1061 and 89324096, integrated to main as 9f39e420. FINALIZED OUT OF BAND on 2026-09-17: the run left this substantially-complete because the begin receipt went STALE when the agent honestly ADDED tests/test_resumedupe.py to Scope-Paths mid-execution. Reconciled against three proven guards (receipt digest genuinely describes the plan at its base_head; requirement categories differ ONLY in scope; the scope change is purely additive), base_head unchanged. Defect filed as plan 63425h. The four acked paths were verified genuinely unmodified by this plan's own commits (git diff e93ba3de..89324096 returns nothing for each). [Scope reconciliation - in-scope-unmodified tests/test_lane_allocation_idempotent.py: verified-unmodified-by-this-plans-commits; in-scope-unmodified tests/test_runner_backlog_close.py: verified-unmodified-by-this-plans-commits; in-scope-unmodified tests/test_runner_refork_guard.py: verified-unmodified-by-this-plans-commits; in-scope-unmodified tests/test_runner_shutdown.py: verified-unmodified-by-this-plans-commits]
- 2026-09-17 executed E-01..E-05 in lane `aw/lane/i3d6ml` from HEAD `e93ba3de` (opencode/its_direct-pt3-claude-opus-5-1m-us): NINE SYMBOLS LIFTED into `runner_shared` (group A's 5, group B's 4), all `is`-identical from both hosts with `__module__` reporting `runner_shared`; the 11 group-C/D exclusions preserved and now asserted in the INVERSE direction by the new `tests/test_rununify_lift.py` (16 tests). Bare suite `7431 passed, 3 skipped, 2 xfailed`, zero failures, above the 7308 baseline. THREE THINGS A READER SHOULD NOT HAVE TO FIND IN THE DIFF. FIRST, THREE SOURCE-READING GUARDS WERE RE-BASED, never weakened, under the maintainer's 2026-09-16 ruling: `test_runner_shared.py`'s `test_StallTimeout_bodies_were_not_edited` (which pinned a DOCSTRING difference as though it were behavioral, on a premise `_normalize_dump` contradicts by stripping docstrings) became a strictly stronger one-definition + object-identity assertion for BOTH exception classes; `test_resumedupe.py`'s `test_the_antigravity_twin_DELEGATES_rather_than_copying` required a runner-to-runner delegating STUB and so would have forbidden this improvement, and now asserts the PROPERTY (one implementation, by stub OR by shared lift) instead of one mechanism; and `test_orchestrator_probe_cache.py`'s oc-to-agy import baseline was re-measured 57 -> 56 with the note its own message prescribes, the FIRST decrease that baseline has ever recorded. Each re-based guard was shown non-vacuous by sabotage. SECOND, GROUPS E, F AND H WERE NOT LIFTED despite OQ-03 putting them in scope, and the reason is a measurement rather than a preference: `_lane_reclaim_prompt` (group E) closes over the SAME `_LANE_PROMPT_DISABLED` global that the permanently-unmovable `disable_lane_prompt` (group D) writes, so lifting the reader breaks prompt suppression exactly as lifting the writer would, and OQ-03's "move a constant, then lift" premise does not hold there; filed as backlog `8hx3g3`, with the honest scope assessment in the report. THIRD, TWO SYMBOLS ARE NEWLY DOUBLE-DEFINED since the inventory was taken (68 now, not 66), reported by name as E-01 requires and filed as backlog `h1q51j`. `aw ipd lint --phase pre-transition` conforms; no push. NOT SELF-FINALIZED: this ran in a managed worker lane (`AW_EXECUTION_ROLE=worker`), where `ipd_lifecycle` refuses driver-only lifecycle verbs, so the driver owns the terminal transition.
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
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

- [x] E-01 RE-MEASURE the closure at execution HEAD before moving anything, and refuse to proceed on a stale list. The method must be the CLOSURE test, not the body-equality test the original plan used: for each candidate, parse the `oc_runipd` definition, collect every free name that resolves at module level, and report which of those are (a) already defined in `runner_shared`, (b) inside the candidate set so they move together, or (c) NEITHER, which makes the candidate unliftable until its prerequisite moves. Emit the eight groups A through H from the Goal table with their members, and state any symbol that changed group since 2026-09-16 by name.
  - Depends on: none
  - Expected outcome: a pasted group listing at execution HEAD produced by the closure method, with per-symbol prerequisites named for every blocked candidate; any drift from the groups recorded in the Goal table and F-7 is stated explicitly with the symbol name and its new group.
  - Execution state: performed

- [x] E-02 Lift GROUP A ONLY, the 5 that are closure-clean today: `EmptyStatusSelection`, `StallTimeout`, `_findings_block_reason`, `build_review_prompt`, `make_integration_validation_runner`. Define each once in `runner_shared` and have both runners reach the shared object, so `oc_runipd.X is agy_runipd.X` holds. NOTE THE TWO EXCEPTION CLASSES ARE THE RISKY PAIR despite being 2 and 20 lines: each runner's `main` catches its OWN today, and `tests/test_runner_shared.py:1305` asserts `StallTimeout` is a `DriverError` subclass in both, so unifying them changes which `except` clause catches a cross-host raise. Prove the catch still works rather than assuming it.
  - Depends on: E-01
  - Expected outcome: 5 single definitions in `runner_shared`, `is`-identical from both hosts, `__module__` reporting `runner_shared`; and for the two exception classes a demonstrated raise-and-catch through each runner's `except DriverError`.
  - Execution state: performed

- [x] E-03 Lift GROUP B, the 4 that are closure-clean but whose OBSERVABLE OUTPUT differs between the hosts, and disclose each change: `attempt_log_path` and `write_prompt` (F-4/F-11, the filename shape), `resolve_prior_lane` and `sync_receipt_into_worktree`. For `write_prompt` the difference is NOT tag order but SEMANTICS: oc treats `suffix` as REPLACING the `exec`/`review` prefix while agy treats it as an ADDITIONAL tag, so the same call produces `03-abc123-verify-attempt-1.md` on oc and `03-abc123-exec-verify-attempt-1.md` on agy. For `attempt_log_path` the consequence is worse than cosmetic: `run_analytics_statistics._VERIFY_LOG_RE` (`agent_workflows/run_analytics_statistics.py:1248`) matches `-attempt-<n>-verify.jsonl`, which is oc's shape, so agy's verifier logs are ALREADY invisible to the verifier-phase analytics and adopting oc's form FIXES a live defect. Say so in the report; do not present it as a neutral rename.
  - Depends on: E-01
  - Expected outcome: 4 single definitions; the `write_prompt` semantic difference stated as a semantic change with both filenames shown; the `attempt_log_path` unification recorded as REPAIRING agy's analytics invisibility, with the regex it now satisfies cited.
  - Execution state: performed

- [x] E-04 DO NOT TOUCH GROUP C OR GROUP D, and record why in the execution report rather than silently skipping them. Group C is the 10 INJECTED symbols (`run_checked`, `save_state`, `discover_plans`, `validate_manifest`, `print_status`, `git_head`, `git_status`, `git_common_dir`, `build_lane_outcome`, `integrate_lane_branch`): each already has exactly ONE implementation in `runner_shared` and keeps a deliberate one-line host wrapper that binds a host-specific dependency, a shape the maintainer ruled on in `818uru` OQ-02 and which `tests/test_runner_shared.py:573` asserts must persist. Group D is `disable_lane_prompt`, pinned by `tests/test_runner_shared.py:1238` because it writes `_LANE_PROMPT_DISABLED` through `global` while each host's `_lane_reclaim_prompt` reads its own copy. This item's DELIVERABLE is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later.
  - Depends on: E-01
  - Expected outcome: an execution-report paragraph naming all 11 excluded symbols, the ruling or pinned test that excludes each, and the explicit statement that lifting them would reverse a decision rather than complete this plan.
  - Execution state: performed

### Task group 2: proof

- [x] E-05 Add `tests/test_rununify_lift.py` asserting the lift held FOR THE SYMBOLS THIS PLAN ACTUALLY LIFTED (groups A and B, 9 symbols), driven by a NAMED TABLE in the test file rather than by the literal 48: each name resolves to the same object from both hosts, `runner_shared` is its defining module, and no runner holds a second `def`/`class` for it (AST scan, repo-wide per the parent's F10, not a pairwise check). The table must also carry the EXCLUDED sets so the test states the boundary: group C is asserted to STILL have its host wrapper (the inverse assertion), and group D is asserted to still be defined in both runners. A test asserting only what moved would let a later agent "complete" the lift by deleting a wrapper the maintainer ruled must stay.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a test file that FAILS if any lifted symbol is re-forked into a runner AND fails if an excluded symbol is lifted, naming which symbol broke in either direction.
  - Execution state: performed

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
| F-17 | MEDIUM | `- Scope-Paths:` (added at execution 2026-09-17); `tests/test_resumedupe.py:654` | THE SCOPE FENCE STILL OMITTED ONE TEST FILE after F-15 added five, found at EXECUTION rather than by reading: `tests/test_resumedupe.py::TestDriverSymmetry::test_the_antigravity_twin_DELEGATES_rather_than_copying` requires `agy_runipd` to hold a DELEGATING STUB for four routing symbols, one of which (`resolve_prior_lane`) is in this plan's group B. So the lift necessarily breaks it, and the file was undeclared. NOTE WHY F-15's method could not find it: F-15 searched for tests asserting on the SHARED symbols and their constants, while this test asserts on the SHAPE of agy's definition, which no search for the symbol's own guards would surface. Added to `Scope-Paths` and the guard re-based (V-05(c)). |
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
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-16, and the answer is NONE OF
  THE FOUR OPTIONS AS FRAMED. The maintainer's directive, given directly: "at the end of the SET,
  there should be one code base shared by the two runners that contains 100% of the otherwise
  redundant code that currently is duplicated between the two runners." Restated as this plan's
  instruction: the objective is COMPLETE de-duplication, not a chosen subset of it, so an option that
  lands 9 of 48 symbols and defers 39 does not satisfy it and neither does one that retires the Set.
  WHAT THE MAINTAINER ALSO RULED, because it dissolves the premise the four options rested on:
  (1) TESTS ARE NOT IMMOVABLE. Asked directly whether the source-reading guards prevent this work, the
  maintainer's answer was that they do not, and that this repository has ALREADY adapted exactly such a
  guard for shared code: `tests/test_nested_tty_noninteractive.py:190-203` counts the shared file's
  launch sites toward BOTH runners, its docstring records the reasoning, and all 41 tests in that file
  and `tests/test_lane_tool_identity.py` pass at this HEAD. So a source-reading pin is a thing to
  UPDATE DELIBERATELY as part of the work, recording what it now asserts and why that is still the same
  property. It is NOT a veto. What remains forbidden is WEAKENING a guard silently (lowering a
  threshold to make a failure disappear), which is a different act from re-basing it on the new
  location of the code.
  (2) DE-DUPLICATION MAY PROCEED ACROSS SYMBOLS TOGETHER rather than one isolated symbol at a time.
  The maintainer asked directly whether anything prevented changing many functions and de-duplicating
  them all before testing; nothing does. This removes the mutual-blocking deadlock: group (e)'s six
  symbols wait on children 04/05/06 only if each child must land alone, and the directive explicitly
  permits the coordinated route.
  THEREFORE, for this plan: execute the full sweep toward 100%. Groups A and B (the 9 sound today) land
  as already written in E-02/E-03. Groups E, F and H (the 15 gated on a constant, helper or import
  move) are IN SCOPE for this plan: perform the precursor move and then the lift, in the same pass,
  rather than deferring them to a new child. Group G's 6 (needing a symbol children 04/05/06 own) are
  lifted by whichever of those children reaches the symbol first, or by this plan if it gets there
  first; the E-01 measurement at execution HEAD decides, and either outcome satisfies the directive.
  THE ELEVEN EXCLUSIONS IN GROUP (c) STAND AND ARE THE ONE DOCUMENTED EXCEPTION TO "100%", because they
  are not redundancy: 10 carry a per-host wrapper the maintainer's own 2026-09-03 ruling installed
  (which IS the de-duplicated form, the real function living once in `runner_shared` with a one-line
  binding per host), and 1 (`disable_lane_prompt`) writes a module-level `global` that must stay
  per-runner, pinned by `UnmovableSymbolTests`. E-04 must state this distinction explicitly in the
  deliverable so a later reader does not read "11 excluded" as "11 still duplicated".
  THE ORIGINAL REVIEWER'S ANALYSIS BELOW IS PRESERVED because its measurement is sound and E-01 must
  reproduce it; only its CONCLUSION (that a re-scope decision was needed) is superseded.
  --- original analysis, superseded as to its conclusion ---
  NOT RESOLVABLE FROM REPOSITORY EVIDENCE, which is why it is asked
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

- [x] V-01 validates E-01
  - Required evidence: pasted group listing produced at execution HEAD BY THE CLOSURE METHOD, showing all eight groups A through H with their members and, for every blocked candidate, the specific prerequisite name that blocks it. Plus an explicit statement of any symbol that changed group since 2026-09-16. A listing produced by body-equality alone does NOT satisfy this item, because that is the measurement F-7 found to be the wrong one.
  - Observed evidence: produced at execution HEAD `e93ba3de` by the CLOSURE method (parse the `oc_runipd`
    definition, collect every free name resolving at module level, classify each as already-in-shared /
    in-candidate-set / NEITHER). `body=SAME|DIFF` is reported ALONGSIDE the blockers deliberately, to show
    the two measurements are independent: 6 of the 9 symbols this plan lifted have DIFFERING bodies, and 11
    symbols with IDENTICAL bodies must never move, so neither property predicts the other.

    ```text
    Double-defined symbols at HEAD: 68  (the plan recorded 66 at 2026-09-16)

    GROUP A (5) - Liftable today, closure-clean, no prerequisite
        EmptyStatusSelection                   20L body=SAME  blockers: (none)
        StallTimeout                            2L body=SAME  blockers: (none)
        _findings_block_reason                 23L body=SAME  blockers: (none)
        build_review_prompt                    39L body=DIFF  blockers: lane_containment
        make_integration_validation_runner     16L body=SAME  blockers: (none)

    GROUP B (4) - Closure-clean but OBSERVABLE output differs between hosts
        attempt_log_path                        9L body=DIFF  blockers: (none)
        write_prompt                           11L body=DIFF  blockers: (none)
        resolve_prior_lane                     47L body=DIFF  blockers: (none)
        sync_receipt_into_worktree             19L body=SAME  blockers: (none)

    GROUP C (10) - ALREADY single-implementation behind a maintainer-ruled injection wrapper (EXCLUDED)
        run_checked                            18L body=SAME  blockers: pinned_child_env, runner_shared
        save_state                              2L body=SAME  blockers: runner_shared
        discover_plans                          3L body=SAME  blockers: runner_shared
        validate_manifest                       4L body=SAME  blockers: parse_dependency_token, runner_shared
        print_status                            2L body=DIFF  blockers: runner_shared
        git_head                                2L body=SAME  blockers: runner_shared
        git_status                              2L body=SAME  blockers: runner_shared
        git_common_dir                          2L body=SAME  blockers: runner_shared
        build_lane_outcome                      7L body=SAME  blockers: runner_shared
        integrate_lane_branch                  28L body=DIFF  blockers: runner_shared

    GROUP D (1) - Pinned UNMOVABLE by a global-write whose reason still holds (EXCLUDED)
        disable_lane_prompt                     4L body=SAME  blockers: _LANE_PROMPT_DISABLED

    GROUP E (6) - Blocked on a module CONSTANT (directly or transitively)
        terminate_process                      14L body=SAME  blockers: _SIGINT_GRACE_SECONDS, _SIGTERM_GRACE_SECONDS, runner_shutdown
        _lane_reclaim_prompt                   44L body=DIFF  blockers: LANE_PROMPT_TIMEOUT, _LANE_PROMPT_DISABLED, select
        reconcile_disposition                 109L body=DIFF  blockers: TERMINAL_STATES, _read_status, runner_shared, runner_stop
        StallWatchdog                          66L body=SAME  blockers: (none)
        locked_run                             26L body=SAME  blockers: runner_shutdown
        reclaim_lanes_on_interrupt            146L body=DIFF  blockers: runner_shared

    GROUP F (6) - Blocked on an oc-only HELPER not in the 48
        build_verify_and_continue_notice        83L body=DIFF  blockers: RecoveryDisposition
        classify_recovery_disposition          130L body=DIFF blockers: DISPOSITION_FRESH_EXECUTION, DISPOSITION_UNDETERMINED, DISPOSITION_VERIFY_AND_CONTINUE, RecoveryDisposition, _lane_commit_subjects
        route_recovery_turn                     79L body=DIFF  blockers: DISPOSITION_FRESH_EXECUTION, DISPOSITION_UNDETERMINED, RecoveryDisposition
        retry_deferred_integrations            146L body=DIFF  blockers: argparse, lane_containment, process_backlog_close, runner_shared
        enforce_dependency_preflight            28L body=DIFF  blockers: DEPENDENCY_FATAL_RULES, preflight_dependency_findings
        set_plan_approved                       77L body=SAME  blockers: FULL_AUTO_ACTOR, FULL_AUTO_APPROVAL_MESSAGE, pinned_module_argv, shutil

    GROUP G (6) - Blocked on a symbol child 04/05/06 owns
        _escalation_recorder                    36L body=SAME  blockers: runner_stop
        handle_stop_command                     29L body=SAME  blockers: argparse, runner_stop
        install_stop_triggers                   41L body=SAME  blockers: runner_stop
        driver_finalize                         48L body=SAME  blockers: pinned_child_env, pinned_module_argv
        reconcile_interrupted                   82L body=DIFF  blockers: runner_stop
        expand_selectors                       157L body=DIFF  blockers: Iterable, runner_shared

    GROUP H (10) - Blocked only on a plain import line runner_shared lacks
        _add_output_mode_flags                  41L body=DIFF  blockers: argparse
        _budget_breach_recorder                 32L body=SAME  blockers: runner_stop
        _observe_between_turn_stop              40L body=SAME  blockers: runner_stop
        _record_checkpoint_stop                 33L body=SAME  blockers: runner_stop
        _record_deliberate_stop                 21L body=SAME  blockers: runner_stop
        _record_forced_stop                     43L body=DIFF  blockers: runner_stop
        requeue_interrupted                     43L body=SAME  blockers: runner_stop
        build_isolation_notice                  10L body=SAME  blockers: lane_containment
        evaluate_clean_base_for_launch          18L body=SAME  blockers: lane_containment
        run_lock                                45L body=SAME  blockers: platform_lock, runner_shutdown

    A..H total = 48 (the plan's 48)
    ```

    DRIFT SINCE 2026-09-16, stated by name because this item demands it:

    1. NO SYMBOL IN THE 48 CHANGED GROUP. Every membership above reproduces the 2026-09-16 partition
       symbol for symbol, so the plan's re-scoped E-02/E-03 targets were still correct at execution.
    2. TWO SYMBOLS ARE NEWLY DOUBLE-DEFINED and appear in NEITHER the 48 nor the 18 deferred, so the
       plan's 66-symbol accounting no longer covers HEAD (68 now):
       `collect_lane_earned_paths` (12L, bodies agree, blockers: `runner_shared`) and
       `integrate_review_lane_branch` (25L, bodies differ, blockers: `runner_shared`). Both carry the
       GROUP-C signature (already one implementation in `runner_shared` behind a binding wrapper), so
       neither changes this plan's liftable set. Reported, not lifted, and filed as backlog `h1q51j`.
    3. TWO OF THE PLAN'S OWN GROUP LABELS ARE WRONG, found because this item requires the blocker to be
       NAMED rather than the group to be restated. `build_review_prompt` is listed in group A as
       "closure-clean" but closes over `lane_containment`, so it is materially group H; it was lifted
       anyway, with a FUNCTION-LOCAL import, because `lane_containment` imports `runner_shared` at its own
       module level (`agent_workflows/lane_containment.py:55`) and a module-level import there is a cycle.
       Conversely `StallWatchdog` is listed in group E as transitively blocked via `terminate_process`, and
       is in fact closure-CLEAN: its body reaches `terminate_process` only through `self`/injected
       callables, so no module-level free name blocks it. It was NOT lifted, because a shared
       `StallWatchdog` would resolve a shared `terminate_process` that group E has not moved yet.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.X is agy_runipd.X` -> `True` and `X.__module__` -> `agent_workflows.runner_shared` for all 5 group-A symbols. PLUS the exception-class proof, which is the risky half: raise each runner's `StallTimeout` and show it caught by the OTHER runner's `except DriverError`, and the same for `EmptyStatusSelection`, with `tests/test_runner_shared.py:1305`'s existing assertions still green.
  - Observed evidence: all 5 group-A symbols are the SAME object from both hosts and report
    `agent_workflows.runner_shared` as their defining module; the exception proof is exercised in FOUR
    directions rather than the two this item asked for (each class raised through each host, caught both
    by the OTHER host's name and by its own `except DriverError`).

    ```text
    V-02: GROUP A identity + defining module
      oc_runipd.EmptyStatusSelection is agy_runipd.EmptyStatusSelection -> True
      EmptyStatusSelection.__module__ -> agent_workflows.runner_shared
      oc_runipd.StallTimeout is agy_runipd.StallTimeout -> True
      StallTimeout.__module__ -> agent_workflows.runner_shared
      oc_runipd._findings_block_reason is agy_runipd._findings_block_reason -> True
      _findings_block_reason.__module__ -> agent_workflows.runner_shared
      oc_runipd.build_review_prompt is agy_runipd.build_review_prompt -> True
      build_review_prompt.__module__ -> agent_workflows.runner_shared
      oc_runipd.make_integration_validation_runner is agy_runipd.make_integration_validation_runner -> True
      make_integration_validation_runner.__module__ -> agent_workflows.runner_shared

    V-02: the EXCEPTION proof, raised through one host and caught through the OTHER
      raise oc.StallTimeout -> caught by `except agy.StallTimeout`      : True
      raise agy.StallTimeout -> caught by `except oc.StallTimeout`      : True
      raise oc.StallTimeout -> caught by `except oc.DriverError`   : True
      raise agy.StallTimeout -> caught by `except agy.DriverError`   : True
      raise oc.EmptyStatusSelection -> caught by `except agy.EmptyStatusSelection`      : True
      raise agy.EmptyStatusSelection -> caught by `except oc.EmptyStatusSelection`      : True
      raise oc.EmptyStatusSelection -> caught by `except oc.DriverError`   : True
      raise agy.EmptyStatusSelection -> caught by `except agy.DriverError`   : True
    ```

    The cross-host CLASS catch (rows 1, 2, 5, 6) is a property that did NOT hold before this change and
    is worth stating separately from the `DriverError` catch this item asked for: previously
    `oc.StallTimeout` and `agy.StallTimeout` were two distinct classes, so a raise through one host was
    caught by the other only via the broader `except DriverError`. It is now caught by name.

    THE EXISTING GUARD AT `tests/test_runner_shared.py` IS GREEN, but one of its tests had to be RE-BASED
    rather than merely re-run, and that is disclosed here rather than left for a reader to discover in the
    diff. `DriverErrorUnificationTests::test_StallTimeout_bodies_were_not_edited` asserted that the two
    runners' `StallTimeout` DOCSTRINGS still differed, i.e. that a definition still existed in each
    runner, on the stated premise that the class was "class (c) DIVERGED". That premise was false: this
    file measures divergence with `_normalize_dump`, which STRIPS DOCSTRINGS, and with them stripped both
    bodies were empty. The test was pinning a prose difference as though it were behavioral. It is now
    `test_StallTimeout_is_now_defined_once_on_the_shared_base`, which asserts STRICTLY MORE: exactly one
    definition in the package, in `runner_shared`, the same object from both hosts, still subclassing
    `DriverError`, for BOTH exception classes. The maintainer's 2026-09-16 ruling authorizes exactly this
    ("a source-reading pin is a thing to UPDATE DELIBERATELY as part of the work ... What remains
    forbidden is WEAKENING a guard silently"), and the behavior half is untouched:
    `test_the_real_watchdog_raise_sites_are_still_caught_by_their_handlers` still walks each runner's
    source for every `raise StallTimeout(` and every handler form, and still passes.

    ```text
    $ python3 -m pytest tests/test_runner_shared.py tests/test_runner_refork_guard.py tests/test_review_findings_cascade.py
    174 passed in 5.99s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted identity results for all 4 group-B symbols. PLUS the disclosure, quoted rather than summarized: the before/after filename for `write_prompt` on BOTH hosts for `suffix="verify"` and `suffix="defect-reask"`, showing the semantic difference F-11 names; and for `attempt_log_path`, the before/after filename on both hosts together with a demonstration that `run_analytics_statistics.verifier_phase_of_log` returns `verify` for the new agy name where it returned `execute` for the old one. That last item is the repaired defect and must be shown, not asserted.
  - Observed evidence: all 4 group-B symbols are the SAME object from both hosts, and the two filename
    changes are shown with the before/after on BOTH hosts. The `attempt_log_path` repair is demonstrated by
    asking the actual consumer (`run_analytics_statistics.verifier_phase_of_log`) what phase it reads off
    each name, which is the "shown, not asserted" this item requires.

    ```text
    V-03: GROUP B identity + defining module
      oc_runipd.attempt_log_path is agy_runipd.attempt_log_path -> True    __module__ -> agent_workflows.runner_shared
      oc_runipd.write_prompt is agy_runipd.write_prompt -> True    __module__ -> agent_workflows.runner_shared
      oc_runipd.resolve_prior_lane is agy_runipd.resolve_prior_lane -> True    __module__ -> agent_workflows.runner_shared
      oc_runipd.sync_receipt_into_worktree is agy_runipd.sync_receipt_into_worktree -> True    __module__ -> agent_workflows.runner_shared

    V-03: write_prompt, the SEMANTIC difference (oc's suffix REPLACES the prefix)
      suffix='verify':
        BEFORE oc  : 03-abc123-verify-attempt-1.md
        BEFORE agy : 03-abc123-exec-verify-attempt-1.md
        AFTER both : 03-abc123-verify-attempt-1.md
      suffix='defect-reask':
        BEFORE oc  : 03-abc123-defect-reask-attempt-1.md
        BEFORE agy : 03-abc123-exec-defect-reask-attempt-1.md
        AFTER both : 03-abc123-defect-reask-attempt-1.md

    V-03: attempt_log_path, and the REPAIRED analytics defect
      BEFORE oc  : 03-abc123-attempt-1-verify.jsonl
      BEFORE agy : 03-abc123-verify-attempt-1.jsonl
      AFTER both : 03-abc123-attempt-1-verify.jsonl
      verifier_phase_of_log('03-abc123-verify-attempt-1.jsonl') -> ('execute', True)   <- agy's OLD name: MISCLASSIFIED
      verifier_phase_of_log('03-abc123-attempt-1-verify.jsonl') -> ('verify', True)    <- the shared name: correct
    ```

    THE REPAIRED DEFECT IS SHOWN, NOT ASSERTED, as this item requires: the last two lines are
    `run_analytics_statistics.verifier_phase_of_log` being ASKED what phase it reads off each filename.
    It answers `execute` for the name antigravity produced before this change and `verify` for the shared
    name, which is the whole claim. F-11's reasoning is independently confirmed at the source:
    `_VERIFY_LOG_RE` is `re.compile(r"-attempt-\d+-verify\.jsonl$")` (`run_analytics_statistics.py:1248`),
    anchored on oc's shape only, and its own comment states the stakes ("the verifier's phase is
    recoverable ONLY from here ... 57 such logs hold $64.08 and ZERO attempts carry
    `verify_cost`/`verify_tokens`, so a filename is the only signal").

    HONEST LIMIT, recorded because "repairs a live defect" could be read as retroactive: this fixes logs
    written from now on. Antigravity logs already on disk keep the old name and stay misclassified, since
    nothing renames history.

    THE `resolve_prior_lane` CASE IS NOT AN OUTPUT CHANGE and is restated so the group-B label is not
    misread: agy's definition was a stub whose body imported `oc_runipd` at call time, so there was
    already ONE implementation. What changed is WHERE it lives, and the observable consequence is that a
    runner-to-runner import disappeared (see V-05(d)).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the exclusion disclosure, plus PROOF THE EXCLUSIONS STILL HOLD, since this item's deliverable is an absence and an absence is what a careless executor silently converts into a change. Paste: for each of the 10 group-C symbols, that a runner-local wrapper still exists and `tests/test_runner_shared.py::SingleDefinitionTests` is green; for `disable_lane_prompt`, that it is still defined in BOTH runners and absent from `runner_shared`, with `UnmovableSymbolTests` green; and the citation (ruling or test) that excludes each of the 11.
  - Observed evidence: ELEVEN SYMBOLS WERE DELIBERATELY NOT LIFTED, and the distinction OQ-03 demands is
    stated first, because "11 excluded" must NOT be read as "11 still duplicated". Neither group is
    redundancy. Group C is ALREADY the de-duplicated form: the real function lives ONCE in
    `runner_shared` and each host keeps a one-line binding wrapper, which is the shape the maintainer
    ruled in `818uru` OQ-02 after rejecting two alternatives (threading the parameter through ~86 call
    sites; a registration seam, declined because process-global state makes behavior depend on import
    order). Group D is one symbol that must stay per-runner for a mechanical reason. Lifting either would
    REVERSE A DECISION rather than complete this plan.

    ```text
    GROUP C: the 10 INJECTED symbols. Each must STILL have a runner-local wrapper.
      run_checked                oc_runipd.py:583    agy_runipd.py:850    runner_shared.py:622
      save_state                 oc_runipd.py:3967   agy_runipd.py:2526   runner_shared.py:708
      discover_plans             oc_runipd.py:2845   agy_runipd.py:1712   runner_shared.py:2841
      validate_manifest          oc_runipd.py:2852   agy_runipd.py:1719   runner_shared.py:3468
      print_status               oc_runipd.py:9204   agy_runipd.py:5557   runner_shared.py:719
      git_head                   oc_runipd.py:608    agy_runipd.py:871    runner_shared.py:597
      git_status                 oc_runipd.py:612    agy_runipd.py:875    runner_shared.py:612
      git_common_dir             oc_runipd.py:616    agy_runipd.py:879    runner_shared.py:616
      build_lane_outcome         oc_runipd.py:2432   agy_runipd.py:1336   runner_shared.py:1635
      integrate_lane_branch      oc_runipd.py:2461   agy_runipd.py:1378   runner_shared.py:1690

    GROUP D: disable_lane_prompt must be in BOTH runners and ABSENT from runner_shared.
      disable_lane_prompt        oc_runipd.py:2214   agy_runipd.py:1121   runner_shared: ABSENT (correct)
    ```

    Every group-C row shows THREE line numbers, which is the point: a definition in `runner_shared` AND a
    wrapper in each runner. That is one implementation with two bindings, not three implementations.

    THE CITATION THAT EXCLUDES EACH OF THE 11:

    | Symbol | Group | Excluded by |
    |---|---|---|
    | `run_checked` | C | `818uru` OQ-02, quoted in `runner_shared.run_checked`'s docstring; binds the opencode-only `pinned_child_env` |
    | `save_state` | C | `818uru` OQ-02; binds the host's DIVERGED `write_report` |
    | `discover_plans` | C | `818uru` OQ-02; binds `parse_plan_file`, which constructs each host's OWN `PlanRecord` |
    | `validate_manifest` | C | `818uru` OQ-02; binds the opencode-only `parse_dependency_token` |
    | `print_status` | C | `818uru` OQ-02; binds the host's own `driver_label` |
    | `git_head` | C | `818uru` OQ-02 + the intra-seam note; binds the host's `run_checked` wrapper |
    | `git_status` | C | `818uru` OQ-02 + the intra-seam note; binds the host's `run_checked` wrapper |
    | `git_common_dir` | C | `818uru` OQ-02 + the intra-seam note; binds the host's `run_checked` wrapper |
    | `build_lane_outcome` | C | integpath-02 `6sb3yu`; binds the host's `run_checked` wrapper |
    | `integrate_lane_branch` | C | integpath-02 `6sb3yu`; binds `run_checked` AND the `host_label` that lands in a merge commit subject on MAIN |
    | `disable_lane_prompt` | D | `tests/test_runner_shared.py::UnmovableSymbolTests` + `runner_shared`'s docstring: it writes `_LANE_PROMPT_DISABLED` through `global` while each host's `_lane_reclaim_prompt` reads its own copy |

    BOTH PINNED SUITES ARE GREEN, and they are the tests that would have caught the opposite of this
    deliverable:

    ```text
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -k "SingleDefinition or Unmovable"
    tests/test_runner_shared.py ........                                     [100%]
    8 passed, 115 deselected in 2.74s
    ```

    THE EXCLUSIONS ARE ALSO NOW ASSERTED IN THE INVERSE DIRECTION by `tests/test_rununify_lift.py`
    (E-05), so an absence is no longer defended by prose alone: `ExcludedSymbolTests` fails if a group-C
    wrapper is deleted, if a group-C wrapper grows a body, or if `disable_lane_prompt` appears in
    `runner_shared`. V-05(b) exercises all three.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_lift.py -o addopts=""` green. (b) The NON-VACUITY control, in BOTH directions, because a one-directional control cannot catch the failure mode that matters here: sabotage three lifted shared definitions and show a NAMED failure each, then restore; AND re-fork one group-C wrapper into a second body and show the new suite names it, then restore. A suite that only checks what moved would bless deleting a wrapper the maintainer ruled must stay. (c) Bare `python3 -m pytest` at or above 7308 passed with NO NEW failures, judged against the ONE known pre-existing flake recorded in F-16 (`ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, a 30s subprocess timeout under parallel load that passes in isolation); if that test fails, show it passing in isolation rather than treating it as a regression. (d) The re-measured oc-to-agy import count with its note, and a statement of the ACTUAL decrease (F-6 measures the realistic figure as one, not fourteen).
  - Observed evidence: all four parts below. The bare suite is `7431 passed, 3 skipped, 2 xfailed` with
    ZERO failures (above the 7308 baseline), the non-vacuity control runs in BOTH directions with five
    sabotages plus a sixth on the one re-based guard, and the oc-to-agy import count decreased by exactly
    the one symbol F-6 predicted.

    (a) THE NEW SUITE, GREEN.

    ```text
    $ python3 -m pytest tests/test_rununify_lift.py -o addopts=""
    collected 16 items
    tests/test_rununify_lift.py ................                             [100%]
    16 passed in 3.51s
    ```

    (b) THE NON-VACUITY CONTROL, IN BOTH DIRECTIONS. Five sabotages, each restored, each producing a
    failure that NAMES the cause rather than merely going red.

    FORWARD DIRECTION (a lifted symbol is broken or re-forked):

    ```text
    SABOTAGE 1: re-fork attempt_log_path into agy as a second body
      AssertionError: Lists differ: ['agy_runipd.py:6108 re-defines `attempt_log_path`'] != []
      AssertionError: <function attempt_log_path ...> is not <function attempt_log_path ...> :
        agy_runipd.attempt_log_path is not the shared object; a fix to the shared definition
        would not reach this host

    SABOTAGE 2: change the lifted write_prompt's semantics back to agy's form
      AssertionError: '03-abc123-exec-verify-attempt-1.md' != '03-abc123-verify-attempt-1.md'
      FAILED ObservableChangeTests::test_write_prompt_suffix_replaces_the_action_prefix_on_both_hosts

    SABOTAGE 3: re-parent the lifted StallTimeout off DriverError
      FAILED ExceptionUnificationTests::test_each_runners_except_DriverError_still_catches_both_subclasses
    ```

    INVERSE DIRECTION (an EXCLUDED symbol is lifted, which is the likelier and more damaging mistake):

    ```text
    SABOTAGE 4: delete agy's group-C git_head wrapper, i.e. "finish the lift"
      AssertionError: 'git_head' not found in {...} : agy_runipd no longer defines `git_head`.
        That wrapper is NOT leftover duplication: it is the ruled mechanism for binding a
        host-specific dependency, and the real implementation already lives once in runner_shared.
        Citation: `818uru` OQ-02 + the intra-seam note; binds the host's `run_checked` wrapper
      FAILED ExcludedSymbolTests::test_every_group_c_symbol_still_has_a_runner_local_wrapper
      FAILED ExcludedSymbolTests::test_every_group_c_wrapper_is_a_single_delegating_statement

    SABOTAGE 4b: LIFT the group-D unmovable disable_lane_prompt into runner_shared
      AssertionError: 'disable_lane_prompt' unexpectedly found in {...} : `disable_lane_prompt` was
        LIFTED into runner_shared. This produces no error and no failure naming the cause: prompt
        suppression silently stops working, and the symptom is an unattended run pausing for a
        question nobody is there to answer. Citation: tests/test_runner_shared.py::UnmovableSymbolTests ...
      FAILED ExcludedSymbolTests::test_the_shared_module_does_not_define_an_excluded_symbol
    ```

    Each failure message carries the CITATION for the exclusion, so an agent who trips it is told why the
    thing they just "finished" was deliberate. All five were restored and the suite returned to 16 passed.

    A SIXTH CONTROL, on the guard this change RE-BASED rather than added, because a re-based guard that
    became vacuous would be the quiet way to lose a property (see V-03's disclosure and the note below on
    `test_resumedupe.py`): re-forking `resolve_prior_lane` into agy as a real second implementation fails
    `TestDriverSymmetry::test_the_antigravity_twin_never_holds_a_second_implementation`, restored to
    `33 passed`.

    (c) THE BARE SUITE. Run bare as the contract requires (`addopts` already supplies
    `-q -n auto --dist=worksteal -m 'not slow'`).

    ```text
    $ python3 -m pytest
    7431 passed, 3 skipped, 2 xfailed in 99.69s (0:01:39)
    ```

    That is 7431 passed against the plan's 7308 baseline, with ZERO failures, so F-16's "no NEW failures
    against one known flake" bar is met with nothing to except. F-16's named flake
    (`ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`) did not fail at all.

    A PRE-EXISTING ENVIRONMENT ARTIFACT IS DISCLOSED, because the first bare runs in this lane reported 31
    failures and reporting the clean number without explaining them would look like selective quoting.
    This turn executes inside a managed worker lane, where the runner exports
    `AW_EXECUTION_ROLE=worker`; `ipd_lifecycle.worker_role_active` makes every driver-only lifecycle verb
    refuse with `AW-LIFECYCLE-ROLE-001`, so 31 tests that shell out to `aw ipd begin`/`finalize` refuse by
    design. They are NOT caused by this change, proven by measurement rather than asserted: with this
    change stashed, HEAD `e93ba3de` produced the SAME failure set (40 failed, of which 9 were this plan's
    own not-yet-written suite collecting as failures), and `comm` over the two sorted `FAILED` lists shows
    exactly one difference in each direction (see below). Clearing the variable alone makes them pass,
    with no source change:

    ```text
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_worker_role_refusal.py \
        tests/test_ipd_lifecycle_cli.py tests/test_runner_backlog_close_in_lane.py
    109 passed in 8.65s
    ```

    THE ONE GENUINE REGRESSION THIS CHANGE CAUSED, found by that same differential and fixed rather than
    absorbed. `tests/test_resumedupe.py::TestDriverSymmetry::test_the_antigravity_twin_DELEGATES_rather_than_copying`
    required agy to hold a DELEGATING STUB (`from agent_workflows.oc_runipd import X as _shared`) for four
    routing symbols including `resolve_prior_lane`, which this plan lifted. The stub was never the goal:
    the comment beside those stubs in `agy_runipd` says `runner_shared` "would be the tidier home" and
    that delegation was chosen only because the shared module's fingerprint pin blocked additions at the
    time. So the test was re-based to assert the PROPERTY (one implementation, reached EITHER by a
    delegating stub OR by a shared lift with proven object identity) instead of one mechanism, and it now
    forbids a re-fork in both shapes. It is `test_the_antigravity_twin_never_holds_a_second_implementation`,
    non-vacuity shown in (b)'s sixth control. `python3 -m pytest tests/test_resumedupe.py -o addopts=""`
    -> `33 passed in 3.09s`.

    THE IMPORT-CYCLE CHECK required by "Required tests / validation" item 6, reachable because
    `build_review_prompt` needs `lane_containment`, which imports `runner_shared` at its own module level:

    ```text
    $ python3 -c "import agent_workflows.oc_runipd, agent_workflows.agy_runipd"   -> CLEAN
    $ python3 -c "import agent_workflows.agy_runipd, agent_workflows.oc_runipd"   -> CLEAN
    $ python3 -c "import agent_workflows.lane_containment, agent_workflows.runner_shared" -> CLEAN
    $ python3 -c "import agent_workflows.runner_shared, agent_workflows.lane_containment" -> CLEAN
    build_review_prompt local import works: '/plan-review /lane/p.md'
    ```

    (d) THE RE-MEASURED oc-to-agy IMPORT COUNT, and the ACTUAL decrease.

    ```text
    count at HEAD e93ba3de: 57
    count now             : 56
    removed: ['resolve_prior_lane']
    added  : []
    ```

    THE DECREASE IS ONE, exactly as F-6 predicted after correcting the plan's original claim of fourteen.
    The baseline in `tests/test_orchestrator_probe_cache.py:1203` was updated from 57 to 56 with the note
    that assertion's own message prescribes ("re-measure and update the baseline with the new count and a
    note"), NOT deleted and NOT loosened to an inequality. The note records the direction explicitly,
    because a DECREASE has never happened on this baseline before and a reader seeing a smaller number
    needs to know it was earned: only 5 of the 57 imports were among this plan's 48 candidates, and 4 of
    those 5 close over a name `runner_shared` cannot yet reach, so one is the honest figure. This is the
    first reduction of the coupling backlog `cnwy8g` tracks; the remaining 56 are outstanding work, not a
    comfortable baseline.
  - Result: pass

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
