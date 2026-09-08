# IPD: OpenCode and Agy runner telemetry lifecycle integration

- Date: 2026-09-08
- Kind: child
- Concern: Make both driver implementations emit equivalent per-invocation telemetry on every lifecycle path.
- Scope: Integrate the shared collector into OpenCode and Agy runner attempts, verifiers, recovery/resume paths, and shutdown handling; amend the runner contract accordingly.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shutdown.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py, tests/test_agy_runipd_cli.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:lhccjf
- Status: reviewed
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 4
- Highest E allocated: 07
- Author: Codex
- Id: 5f2h8i

## Workflow history

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-053..PR-062, ALL TEN FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE BLOCKER IS THAT THE CONVENTIONS SECTION INSTRUCTED THE EXECUTOR TO DO SOMETHING FOUR EXECUTED PLANS' GUARD TESTS FORBID (PR-053, F-1). It said "cleanup must be registered there when necessary rather than relying only on happy-path `finally` blocks", which reads as "register a signal handler". Measured, FOUR guards assert `signal.signal(` appears in NEITHER driver (`tests/test_lane_allocation_idempotent.py:406`, `tests/test_runner_stop.py:652`, `tests/test_runner_stop_level3.py:792`, `tests/test_runner_stop_level4.py:785`), reserving SIGINT/SIGTERM for `runstop` Phase 5 (`71vjbn`), and `oc_runipd.py:1587-1610` records a prior plan being refused exactly this, stating the designs are "incompatible, not merely double-registered" and that seizing the registration would have deleted a measured handler deadlock fix and a roughly 50 percent lost-escalation race fix; spec `c4gd2h` R5 independently forbids divergent cleanup with A9 requiring exactly one implementation. An executor following the authored convention would have gone four suites red and re-broken two fixed races. E-05 now requires reaching teardown through the EXISTING funnels (`clean_shutdown`, and the `except KeyboardInterrupt` path that needs no registration), permits an edit to `runner_shutdown.py` ONLY to have the existing routine stop a registered sampler, and V-05 demands a grep plus the four guards passing unmodified. SECOND, THE SPEC IS BOUND TO THE CODE BIDIRECTIONALLY AND THE PLAN'S AMENDMENT ORDER WOULD HAVE BROKEN IT (PR-054, F-2): `tests/test_run_flag_surface.py` reads spec `25kzda` as a FILE (`:43-50`), extracts Section 2.1's grammar and fails BOTH on a spec-declared flag the code lacks (`:136`) and the converse (`:150`), while E-03-as-authored said to amend the spec "in the same execution BEFORE implementation"; the spec's own 2026-09-07 history records Section 2.1 being deliberately left unamended for precisely this reason. E-07 now states the constraint, and OQ-01 defaults to NO flag since Order 03's OQ-01 already resolved telemetry config to a `project.json` key rather than a CLI surface. THIRD, THE EXECUTION ID COULD NOT SATISFY THE PLAN'S OWN UNIQUENESS REQUIREMENT (PR-055, F-3): `attempt_no` is `len(item.get("attempts", [])) + 1` (`oc_runipd.py:5917`) over a list PERSISTED in `state.json` (`:5947`), so an id keyed on `(position, id6, attempt_no, phase)` is STABLE across a resume and collides with the earlier invocation, and executor-versus-verifier is distinguished today only by a `suffix="verify"` string on the log path, so phase must be an explicit field rather than inferred from a filename; now E-02 and OQ-02 with a mutation check. FOURTH, THE GOAL HARDCODED A RUN PATH IN A SET WHOSE ORDER 01 EXISTS TO REMOVE THAT LITERAL (PR-056, F-4): `state_root:188-189` consults no authority while the records root is relocatable (`project_context.py:783-790`), and Order 01's review established the literal is built at six live sites; the Goal and E-01 now require resolution through that resolver and state that telemetry is NOT in the reserved `analytics/` tree. ALSO FIXED: "wrap all OpenCode subprocess invocation boundaries" overstated the target by six sites, since there is exactly ONE agent-launch `Popen` per host (`oc_runipd.py:5526`, `agy_runipd.py:2889`) with two callers each while the other `subprocess.run` calls are version probes (PR-057, F-5); the three E-items were mechanically sized, as eight of eleven Set plans carry exactly three and the lint conformed both before and after, now SEVEN items with V-01..V-07 to bijection and `Highest E allocated` 03 -> 07 (PR-058, F-6, the third sibling split after `bzz5e6` 3->6 and `lhccjf` 3->8); the gate carried no execution contract, the fourth sibling in a row (PR-059, F-7); the strongest claim in the plan had no CONTROL run, so V-01 could have passed on an instrumented run that changed a state transition (PR-060, F-8); the 47-name `oc_runipd`-to-`agy_runipd` import surface and `tests/test_runner_refork_guard.py` were unmentioned despite "semantic alignment" being a goal (PR-061, F-9); and no baseline was recorded, now `2 failed, 5655 passed` with both failures attributed as pre-existing live-corpus couplings, plus 18 escaped backticks unescaped after Order 01's six, Order 02's four and Order 03's ten (PR-062, F-10).

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): mapped the collector to both runner lifecycles, resume identity, verifier phases, and shutdown failure modes.

## Goal

Write one telemetry JSONL file per OpenCode and Agy execution or verification invocation, at `<resolved-run-dir>/telemetry/<execution-id>.jsonl`. RESOLVE THAT PATH, DO NOT COMPOSE IT: the run root comes from Order 01's (`xbwq8n`) resolver plus a named constant, never from a hardcoded `.aw/records/runs` literal, because the records root is relocatable by `records_backend` (`project_context.py:783-790`) while `runner_shared.state_root:188-189` hardcodes the repository case, and Order 01 exists to remove exactly that literal from its six live sites. Telemetry is a per-RUN artifact under the run directory and is NOT inside Order 01's reserved `analytics/` tree.

Preserve distinct attempts and nodes across resume, which requires more than reusing `attempt_no`: that value derives from a PERSISTED list and so does not reset on resume (F-3), so the execution id needs a per-invocation component. Keep the two runners semantically aligned through ONE shared definition rather than two parallel implementations, and never let telemetry failure alter the work result, proven against paired uninstrumented control runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE. This plan was authored with THREE E-items, as were eight of the Set's eleven plans; the count-based lint reported conforming, and it cannot see conceptual density. E-02-as-authored named FOUR independent deliverables (the agy integration, the shutdown wiring, resume/recovery identity, and sampler non-orphaning) across unrelated test surfaces, and E-03 bundled an approved-spec amendment with a whole non-interference test matrix. Siblings `bzz5e6` (3 -> 6) and `lhccjf` (3 -> 8) were split for the identical reason. Split into seven items across four groups.

### Task group 1: The shared seam

- [ ] E-01 Establish the ONE host-neutral instrumentation seam in `runner_shared`, and resolve the telemetry directory THROUGH Order 01's resolver rather than composing a path.
  DO NOT WRITE THE PATH AS A LITERAL. The Goal's `<run>/telemetry/<execution-id>.jsonl` must be derived from Order 01's (`xbwq8n`) run-root resolver plus a named constant, not composed by hand. Measured: `runner_shared.state_root` (`:188-189`) returns `repo / ".aw" / "records" / "runs"` consulting NO authority, while the records root is RELOCATABLE by `records_backend` of `repository`/`companion`/`home` (`project_context.py:783-790`). Order 01's review established that `state_root` IS the defect and that the literal is built at SIX live sites; this child must not add a seventh. Order 01 also reserves `analytics/` and ships `path_is_within_analytics`; telemetry is a per-RUN artifact under the run directory, NOT under `analytics/`, so state that distinction explicitly so an executor does not file it in the reserved tree.
  ONE SEAM, NOT TWO. Both hosts must reach telemetry through `runner_shared`, never through the other host's driver: `agy_runipd` already imports 47 names from `oc_runipd` (measured by AST walk 2026-09-08) and `tests/test_runner_refork_guard.py` pins that no runner redefines an extracted symbol and that every runner attribute is the owning module's object. A second copy here is the exact defect that guard exists to catch.
  - Depends on: none
  - Expected outcome: a host-neutral context manager (or equivalent) in `runner_shared` taking the resolved run dir and the invocation identity; the telemetry path derived from Order 01's resolver plus a constant; no new `.aw/records/runs` literal; no new `oc_runipd` import in `agy_runipd`.
  - Execution state: pending

- [ ] E-02 Define the INVOCATION IDENTITY and prove it is unique per invocation, which is the property the whole Set's later analysis rests on.
  MEASURED, AND IT IS THE SUBTLEST HAZARD IN THIS PLAN: `attempt_no` is derived as `len(item.get("attempts", [])) + 1` (`oc_runipd.py:5917`), and the `attempts` list is PERSISTED in `state.json` (appended at `:5947`), so it does NOT reset across a resume in the same run directory. Good. But an execution id keyed on `(position, id6, attempt_no, phase)` alone is therefore stable across a resume, which is exactly what the plan's own Findings section forbids ("must not be inferred later from a single run-level snapshot"). The executor and verifier are distinguished today only by a `suffix="verify"` string passed to the log-path builder (`attempt_log_path`, `oc_runipd.py:4939-4947`), so PHASE must be an explicit field and not inferred from a filename. Decide and record what makes the id unique: include a per-invocation random or time component, and state why the chosen construction cannot collide on a resume, a retry, or a verifier re-run.
  - Depends on: E-01
  - Expected outcome: an execution id that is provably distinct for two invocations of the same item, attempt and phase separated by a resume; phase carried as an explicit field; the uniqueness argument recorded rather than assumed.
  - Execution state: pending

### Task group 2: Host wiring

- [ ] E-03 Wire the seam into OpenCode's TWO invocation call sites and its single child-launch boundary.
  THE SITES ARE MEASURED AND FEWER THAN "ALL SUBPROCESS BOUNDARIES" SUGGESTS. `run_opencode` (`:5304`) has exactly ONE `subprocess.Popen`, at `oc_runipd.py:5526`, already wrapped in `runner_shutdown.track_child`. It has exactly TWO callers: the executor at `:6147` and the verifier at `:6392`. The Proposed-changes phrase "all OpenCode subprocess invocation boundaries" is misleading: the module holds several other `subprocess.run` calls (`:604`, `:923`, `:1011`, `:5041`, `:5262`, `:5275`) which are version probes and helpers, NOT agent invocations, and instrumenting them would produce telemetry for work nobody wants measured. Wrap the agent turn, and say so.
  - Depends on: E-02
  - Expected outcome: telemetry opens before the `track_child(Popen(...))` at the one launch boundary and closes on success, non-zero exit, stall-timeout kill, signal, cancellation, and launcher exception; both the executor and the verifier caller are covered; the version/helper `subprocess.run` sites are NOT instrumented.
  - Execution state: pending

- [ ] E-04 Wire the identical seam into Agy's matching boundary, and prove PARITY by construction rather than by inspection.
  Agy mirrors the shape exactly: one `subprocess.Popen` at `agy_runipd.py:2889` inside `run_agy_turn` (`:2768`), with two callers, the executor at `:3437` and the verifier at `:3657`. Assert parity as a TEST over the shared seam's fields, not as a reviewer's reading of two files. Note the carve-out the sibling Set already measured: host-parameterized TEXT is legitimately not one object (`DEPENDENCY_BLOCK_RECOVERY_HINT` differs per host by design), so parity means the same FIELDS and the same phase semantics, not byte-identical strings.
  - Depends on: E-03
  - Expected outcome: agy emits the same field set and phase semantics through the same shared object; a field-by-field parity assertion covering both hosts; no host-specific telemetry branch.
  - Execution state: pending

- [ ] E-05 Make the sampler stop on every teardown path WITHOUT registering a signal handler and WITHOUT adding a second cleanup routine.
  THE CONVENTION THIS PLAN AUTHORED IS A TRAP AND MUST BE READ CAREFULLY. It says "cleanup must be registered there when necessary rather than relying only on happy-path `finally` blocks". Taken literally that is FORBIDDEN, measured: FOUR executed plans installed guards asserting `signal.signal(` appears in NEITHER driver (`tests/test_lane_allocation_idempotent.py:406`, `tests/test_runner_stop.py:652`, `tests/test_runner_stop_level3.py:792`, `tests/test_runner_stop_level4.py:785`), reserving SIGINT/SIGTERM registration for `runstop` Phase 5 (`71vjbn`). `oc_runipd.py:1587-1610` records a prior plan being refused exactly this, and states the designs are "incompatible, not merely double-registered", noting that seizing the registration would have deleted a measured handler deadlock fix and a ~50% lost-escalation race fix. Independently, spec `c4gd2h` R5 forbids divergent per-level cleanup and A9 requires a structural check that exactly ONE cleanup implementation exists.
  SO THE CORRECT SHAPE IS: reach teardown through the EXISTING funnels. `clean_shutdown` (`runner_shutdown.py:451`) already runs the four invariants best-effort with 7 call sites, and `oc_runipd` already reaches SIGINT via `except KeyboardInterrupt` which needs no registration at all. If `runner_shutdown.py` must change, the change is to have the EXISTING routine also stop a registered sampler; it is NOT a new cleanup path. Order 03's collector must already be idempotent on close, so double-close is its contract to keep, not a reason to add a guard here.
  - Depends on: E-03, E-04
  - Expected outcome: the sampler is provably stopped on normal completion, exception, stall kill, SIGINT and SIGTERM; a grep proving this plan added NO `signal.signal(` to either driver and added no second cleanup routine; the four guard tests still passing UNMODIFIED.
  - Execution state: pending

### Task group 3: Non-interference

- [ ] E-06 Prove INSTRUMENTATION CANNOT CHANGE THE WORK, by fault injection rather than by assertion.
  This is the item the plan's own gate cares most about ("must never turn successful work into failure or mask an existing failure"), and it was previously one clause inside a bundled item. Inject a failure at each telemetry boundary (probe raises, probe times out, telemetry directory unwritable, disk full on append, collector constructor raises, close raises) and assert the runner's exit status, merge decision, state transitions, item status and cleanup report are BYTE-IDENTICAL to an uninstrumented control run.
  A CONTROL RUN IS REQUIRED, not just a passing instrumented run: "the run still succeeded" and "the run succeeded for the same reasons" are different claims, and only the second is non-interference.
  - Depends on: E-05
  - Expected outcome: each injected telemetry fault leaves exit status, state transitions and cleanup unchanged against a paired control; a telemetry write failure produces the documented warning where writable and is silent where not; no injected fault turns success into failure or masks a failure.
  - Execution state: pending

### Task group 4: Spec

- [ ] E-07 Amend spec `25kzda` to name telemetry as a best-effort derived run artifact, and do it WITHOUT tripping the bidirectional spec-code contract test.
  KNOW THE TEST BEFORE YOU EDIT THE SPEC. `tests/test_run_flag_surface.py` reads that spec FILE (`SPEC_PATH`, `:43-50`), extracts its Section 2.1 grammar block, and asserts BOTH directions: `test_every_flag_the_spec_declares_is_accounted_for` (`:136`) fails when the spec declares a flag the code neither registers nor explicitly excludes in `DECLARED_BUT_NOT_OWNED_HERE`, and `test_no_owned_flag_is_absent_from_the_spec` (`:150`) fails on the converse. So if this amendment adds ANY run flag (for example a `--no-telemetry`) to Section 2.1's grammar, it MUST land in the same change as the flag's registration in `runner_shared.RUN_POLICY_FLAGS`, or the suite goes red. The precedent is explicit: the spec's own 2026-09-07 history records Section 2.1 being deliberately NOT amended for exactly this reason, because "the two ladder flags plan `51vw4y` needs cannot be declared before they are registered, since `tests/test_run_flag_surface.py` binds spec and code bidirectionally, so that amendment lands inside `51vw4y`'s own execution as one atomic change".
  PREFER NOT ADDING A FLAG AT ALL. Order 03 (`lhccjf`) owns the telemetry configuration and its OQ-01 resolves it to a config key in `.aw/config/project.json` with a machine-local override, NOT a run flag. If that holds, this amendment touches the run-artifact inventory and the privacy/default/disable semantics and leaves Section 2.1 alone, which is both simpler and avoids the bidirectional trap. If a flag is genuinely wanted, it is a separate decision to raise, not to slip in here.
  AMENDING AN APPROVED SPEC IS LEGITIMATE HERE AND MUST BE DECLARED. The spec reads `- Status: approved`; the repository's own contract permits a plan to amend a spec it changes the behavior of, provided the file is declared in `Scope-Paths` (it is) so the pre-run spec-impact announcement names it. Do not edit any OTHER spec: `c4gd2h` bears on E-05 and is NOT declared here.
  - Depends on: E-06
  - Expected outcome: `25kzda` records telemetry as a best-effort derived artifact that is never a gate, with privacy/default/disable semantics; Section 2.1's grammar is either untouched or amended atomically with a registered flag; the pre-run spec-impact announcement names the file; `tests/test_run_flag_surface.py` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Both runners own `state.json`, driver `events.jsonl`, `sessions/`, `outcomes/`, prompts, and execution reports; telemetry is a separate derived subtree and must not be confused with the hash-chained run ledger.
- Existing attempts already record cost and token summaries after log extraction. Telemetry adds resource context and invocation identity without becoming the authority for those totals.
- CORRECTED AT REVIEW, BECAUSE THE AUTHORED WORDING INVITED A FORBIDDEN CHANGE. It read "cleanup must be registered there when necessary rather than relying only on happy-path `finally` blocks", which reads naturally as "register a signal handler". THAT IS PROHIBITED, measured: FOUR executed plans installed guards asserting `signal.signal(` appears in NEITHER driver (`tests/test_lane_allocation_idempotent.py:406`, `tests/test_runner_stop.py:652`, `tests/test_runner_stop_level3.py:792`, `tests/test_runner_stop_level4.py:785`), reserving SIGINT/SIGTERM registration for `runstop` Phase 5 (`71vjbn`). `oc_runipd.py:1587-1610` records a prior plan being refused exactly this and states the designs are "incompatible, not merely double-registered", because seizing the registration would have deleted a measured handler deadlock fix and a roughly 50 percent lost-escalation race fix. Spec `c4gd2h` R5 independently forbids divergent per-level cleanup, with A9 requiring a structural check that exactly ONE cleanup implementation exists.
- SO THE AVAILABLE FUNNELS ARE THE EXISTING ONES: `runner_shutdown.clean_shutdown` (`:451`, 7 call sites) already performs the four invariants best-effort, and `oc_runipd` already reaches SIGINT through `except KeyboardInterrupt`, which needs no registration. A legitimate edit to `runner_shutdown.py` teaches the EXISTING routine to stop a registered sampler; it never adds a second path. `runner_shutdown.py` is declared in this plan's `Scope-Paths` for that narrow purpose only.
- THE INVOCATION BOUNDARY IS ONE `Popen` PER HOST WITH TWO CALLERS, not "all subprocess boundaries". OpenCode: `subprocess.Popen` at `oc_runipd.py:5526` inside `run_opencode` (`:5304`), already wrapped in `runner_shutdown.track_child`, called from the executor (`:6147`) and the verifier (`:6392`). Agy: `Popen` at `agy_runipd.py:2889` inside `run_agy_turn` (`:2768`), called from `:3437` and `:3657`. The other `subprocess.run` sites in `oc_runipd` (`:604`, `:923`, `:1011`, `:5041`, `:5262`, `:5275`) are version probes and helpers and must NOT be instrumented.
- THE RUNS ROOT IS RELOCATABLE AND MUST NOT BE COMPOSED BY HAND. `runner_shared.state_root` (`:188-189`) hardcodes `repo / ".aw" / "records" / "runs"` while `project_context.py:783-790` resolves the records root from a `records_backend` of `repository`, `companion` or `home`. Order 01 (`xbwq8n`) owns the resolver and its review established the literal exists at SIX live sites; this child must add no seventh. Telemetry is a per-RUN artifact under the run directory, NOT under Order 01's reserved `analytics/` tree.
- BOTH HOSTS MUST SHARE ONE DEFINITION. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and `tests/test_runner_refork_guard.py` pins that no runner redefines an extracted symbol and that every runner attribute is the owning module's object. Reach telemetry through `runner_shared`; never through the other host's driver.
- THE CONTROLLING SPEC IS READ AS A FILE BY A CONTRACT TEST. `tests/test_run_flag_surface.py` (`SPEC_PATH` at `:43-50`) parses spec `25kzda` Section 2.1's grammar and asserts BOTH directions (`:136` spec-declares-but-code-lacks; `:150` code-has-but-spec-lacks). A flag added to the spec without being registered in `runner_shared.RUN_POLICY_FLAGS` in the SAME change turns the suite red. The spec's own 2026-09-07 history records Section 2.1 being deliberately left unamended for precisely this reason.
- Prompts, child stdout, and session JSONL are sensitive source artifacts and must never be copied into telemetry.
- Driver behavior and output are heavily tested. Test instrumentation through injected collectors to avoid timing flakes.

## Findings

There can be multiple executor attempts and an independent verifier invocation per IPD, plus later resume in the same run directory. Therefore the execution ID, attempt, phase, start/end times, model identity, and node pseudonym must be recorded per file and must not be inferred later from a single run-level snapshot.

"Telemetry disabled" means no telemetry directory or event file is created. "Periodic sampling disabled" still permits the default start/end basic events unless all telemetry is disabled.

### Findings (review, measured 2026-09-08 at HEAD `d9a32cdd`)

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `tests/test_lane_allocation_idempotent.py:406`, `tests/test_runner_stop.py:652`, `tests/test_runner_stop_level3.py:792`, `tests/test_runner_stop_level4.py:785`; `oc_runipd.py:1587-1610`; spec `c4gd2h` R5/A9 | **THE CONVENTIONS SECTION INVITED A CHANGE THAT FOUR EXECUTED PLANS' GUARD TESTS FORBID.** "Cleanup must be registered there ... rather than relying only on happy-path `finally` blocks" reads as "register a signal handler", and four separate guards assert `signal.signal(` appears in NEITHER driver, reserving SIGINT/SIGTERM for `runstop` Phase 5 (`71vjbn`). A prior plan was refused exactly this, with the record stating the designs are "incompatible, not merely double-registered" and that seizing registration would have deleted a measured handler deadlock fix and a ~50% lost-escalation race fix. Spec `c4gd2h` R5 also forbids divergent cleanup, A9 requiring exactly one implementation. An executor following the authored convention would have gone four tests red and re-broken two fixed races | all four guard assertions read; the refusal comment read; spec requirements read |
| F-2 | HIGH | `tests/test_run_flag_surface.py:43-50`, `:136`, `:150`; spec `25kzda` Workflow history 2026-09-07 | **THE SPEC IS BOUND TO THE CODE BIDIRECTIONALLY BY A CONTRACT TEST, AND E-03-AS-AUTHORED SAID TO AMEND THE SPEC "IN THE SAME EXECUTION BEFORE IMPLEMENTATION".** That test reads the spec FILE, extracts Section 2.1's grammar, and fails when the spec declares a flag the code neither registers nor explicitly excludes, AND on the converse. So a spec-first amendment that adds any run flag turns the suite red until the registration lands. The spec's own history records Section 2.1 being deliberately NOT amended for this exact reason on 2026-09-07 ("cannot be declared before they are registered ... so that amendment lands inside `51vw4y`'s own execution as one atomic change"). The plan neither knew the test nor the precedent | test source read; spec history entry read |
| F-3 | HIGH | `oc_runipd.py:5917` (`attempt_no = len(item.get("attempts", [])) + 1`), `:5947` (persisted); `attempt_log_path:4939-4947` (`suffix="verify"`) | **THE EXECUTION ID COULD NOT SATISFY THE PLAN'S OWN UNIQUENESS REQUIREMENT AS SPECIFIED.** The Findings section demands identity not be inferable "from a single run-level snapshot", but `attempt_no` derives from a PERSISTED `attempts` list, so an id keyed on `(position, id6, attempt_no, phase)` is STABLE across a resume in the same run directory, colliding with the earlier invocation. Separately, executor and verifier are distinguished today only by a `suffix="verify"` string on the log path, so phase must be an explicit field rather than inferred from a filename. Neither point was addressed | source read; `attempts` append site confirmed |
| F-4 | HIGH | `runner_shared.state_root:188-189`; `project_context.py:783-790`; Order 01 (`xbwq8n`) review | **THE GOAL HARDCODED A RUN-RELATIVE PATH IN A SET WHOSE ORDER 01 EXISTS TO REMOVE THAT LITERAL.** `state_root` returns `repo / ".aw" / "records" / "runs"` consulting no authority while the records root is relocatable via `records_backend` (`repository`/`companion`/`home`); Order 01's review established `state_root` IS the defect and that the literal is built at SIX live sites. Composing `<run>/telemetry/...` by hand would add a seventh and would place telemetry wrong for any non-repository backend. The plan also never said telemetry is NOT inside Order 01's reserved `analytics/` tree, which an executor could reasonably assume | source read; Order 01 review record read |
| F-5 | MEDIUM | plan's Proposed changes as authored; `oc_runipd.py:604`, `:923`, `:1011`, `:5041`, `:5262`, `:5275` versus `:5526` | **"WRAP ALL OPENCODE SUBPROCESS INVOCATION BOUNDARIES" OVERSTATES THE TARGET BY SIX SITES.** There is exactly ONE agent-launch `Popen` per host (`oc_runipd.py:5526`, `agy_runipd.py:2889`), each with two callers (executor and verifier). The other `subprocess.run` calls are version probes and helpers; instrumenting them would emit telemetry for work nobody wants measured and would inflate the event volume Order 03's overhead budget is sized against | grepped every subprocess site in both drivers and traced the callers |
| F-6 | MEDIUM | plan E-01..E-03 as authored; eight of eleven `runanalytics` plans at exactly 3 E-items | **THE E-ITEMS WERE MECHANICALLY SIZED.** E-02 named four independent deliverables (agy integration, shutdown wiring, resume identity, sampler non-orphaning) across unrelated test surfaces, and E-03 bundled an approved-spec amendment with an entire non-interference matrix. The count-based lint reported conforming before and after the split, so it cleared nothing. Siblings `bzz5e6` (3 -> 6) and `lhccjf` (3 -> 8) were split for the identical reason | `grep -c` across the Set; lint conforming both ways |
| F-7 | MEDIUM | plan gate as authored | The gate carried two sentences and NO execution contract: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle-move instruction, no re-locate-by-symbol warning. Sibling Orders 01, 02 and 03 each had the identical omission, so it is a Set-wide authoring pattern | plan read; three sibling review records read |
| F-8 | MEDIUM | plan's non-interference clause | The strongest claim in the plan ("never let telemetry failure alter the work result") was one clause inside a bundled item, with no CONTROL run required. "The run still succeeded" and "the run succeeded for the same reasons" are different claims and only the second is non-interference; without a paired uninstrumented control, V-01 could have passed on an instrumented run that changed a state transition | plan read |
| F-9 | LOW | `agy_runipd` import surface; `tests/test_runner_refork_guard.py` | `agy_runipd` imports 47 names from `oc_runipd` (AST-measured). The plan required "semantic alignment" between hosts without naming the shared-definition discipline or the guard test that enforces it, so a second telemetry implementation in the agy driver would have satisfied a reviewer reading for parity of BEHAVIOR while forking the code | AST walk; guard test names read |
| F-10 | LOW | suite baseline; plan source (18 escaped backticks pre-fix) | The plan required a bare suite run with no baseline recorded. Measured bare at `d9a32cdd`: `2 failed, 5655 passed, 3 skipped, 2 xfailed`, both failures (`test_orchestrator_retirement::RealRepositorySets`, `test_plan_readiness::ApprovalGateRealCorpusTests`) pinned to the live mutable plan corpus and pre-existing. Also 18 escaped backtick pairs rendered as literal backslashes, after Order 01's six, Order 02's four and Order 03's ten | bare run at review; `grep -c` before the fix |

## Proposed changes (ordered, validatable)

1. E-01 puts ONE host-neutral seam in `runner_shared`, with the telemetry path resolved through Order 01's resolver rather than composed.
2. E-02 settles invocation identity, whose resume-collision hazard is measured in F-3 and is the property every later Order depends on.
3. E-03 wraps OpenCode's single agent-launch boundary at both callers (executor and verifier), NOT the six version/helper `subprocess.run` sites.
4. E-04 wraps Agy's matching boundary and pins parity as a test rather than a reading.
5. E-05 stops the sampler through the EXISTING funnels, registering no signal handler and adding no second cleanup routine.
6. E-06 proves non-interference by fault injection against paired uninstrumented control runs.
7. E-07 amends spec `25kzda`, having first checked the bidirectional contract test that makes a spec-only flag edit fail.

## Deferred / out of scope (with reason)

- Resource probe implementation, the event schema, the node pseudonym, the sampler itself and the configuration model are ALL Order 03 (`lhccjf`), whose `Scope-Paths` are `run_analytics_telemetry.py` and `run_analytics_config.py`. This plan WIRES that collector in and reimplements none of it. Verified against Order 03's front matter and its reviewed item list.
- The run-root resolver and the reserved `analytics/` namespace are Order 01 (`xbwq8n`). This plan consumes the resolver and adds no path literal.
- Parsing and statistical use of telemetry are Orders 05 (`8hald1`, ingestion) and 06 (`aflsz3`, taxonomy/pricing/statistics). Verified against their front matter.
- Changes to agent prompts or model selection are not needed to collect driver-owned telemetry.
- Historical runs without telemetry remain supported and receive explicit missing-coverage flags.

## Scope check

- Over-scope: no analyzer, pricing, SPA, export, network, or setup wizard. Specifically, and each for a measured reason: do NOT add `signal.signal(` to either driver (four executed plans' guards forbid it and `runstop` Phase 5 `71vjbn` owns the registration); do NOT add a second cleanup routine (spec `c4gd2h` R5/A9), so an edit to `runner_shutdown.py` may only teach the EXISTING routine to stop a registered sampler; do NOT instrument the version/helper `subprocess.run` sites; do NOT add a new `.aw/records/runs` literal (Order 01 owns the resolver); do NOT reimplement the collector, its probes or its config, which are Order 03's; do NOT write telemetry into Order 01's reserved `analytics/` tree; do NOT weaken `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS`; and do NOT edit any spec other than `25kzda`, which is the only one declared here (`c4gd2h` bears on E-05 and is NOT declared).
- An out-of-scope edit is not forbidden outright, it must be JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Declare rather than improvise.
- Under-scope: covers executor, verifier, retries, resume, cancellation, signals, exceptions, both hosts, and controlling spec sync. The invocation-identity uniqueness proof (E-02), the paired control runs for non-interference (E-06) and the spec contract-test check (E-07) were under-scope before review.
- CONCURRENT-EDIT HAZARD, worth knowing before starting: `oc_runipd.py` and `agy_runipd.py` are the two highest-contention files in this repository and several pending Sets declare them. Under `aw oc run` each item gets an isolated worktree and returns through the merge-and-revalidate gate, so overlap is handled; if editing BY HAND alongside another agent, re-measure every cited line by symbol first.

## Required tests / validation

Baseline, measured bare at HEAD `d9a32cdd`: `2 failed, 5655 passed, 3 skipped, 2 xfailed`. Both failures (`tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` and `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`) are pinned to the live mutable plan corpus and are PRE-EXISTING, not caused by this work. Re-measure in the executing worktree and compare failing NODE IDS; the criterion is an empty delta against your own baseline, never a total.

THE FOUR GUARD SUITES ARE THE ONES MOST LIKELY TO CATCH A MISTAKE HERE and must be run and pasted UNMODIFIED: `tests/test_lane_allocation_idempotent.py`, `tests/test_runner_stop.py`, `tests/test_runner_stop_level3.py`, `tests/test_runner_stop_level4.py` (the `signal.signal(` prohibition), plus `tests/test_runner_refork_guard.py` (one shared definition per symbol) and `tests/test_run_flag_surface.py` (the spec-code binding). Weakening any of them to make this plan pass is a stop condition, not a fix.

- OpenCode and Agy parity for start/end metadata and phase/attempt identity, asserted field-by-field as a test rather than by inspection.
- A resumed invocation of the same item, attempt and phase must produce a DIFFERENT execution id than the pre-resume invocation (F-3), with a mutation check proving the test can fail.
- Paired UNINSTRUMENTED control runs for every non-interference case, since a passing instrumented run alone does not establish that the run succeeded for the same reasons (F-8).
- Resume on a different pseudonymous node; retry in the same run; verifier with a different model.
- Disabled telemetry creates nothing; basic default produces two lifecycle events; periodic mode samples.
- Probe timeout/exception/disk-write failure leaves original runner status and exit behavior unchanged and produces the documented warning path where writable.
- Signal, cancellation, launch failure, merge failure, verifier failure, and normal completion close samplers.
- Existing runner CLI/shim/shutdown tests, bare `python3 -m pytest`, and `git diff --check`. Run the suite BARE; do not add `-n0`, a second `-q`, or `-p no:randomly`, since `pyproject.toml` `addopts` already supplies the intended flags.
- No test may spawn a real agent process or depend on wall-clock timing. Inject the collector and the clock, per the plan's own convention about timing flakes, and assert it by construction with a stub that RAISES if a real launch is attempted.

## Spec / documentation sync

Amend `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (`- Id: 25kzda`, `- Status: approved`; the filename predates the id6-in-filename convention, so the id is findable only by grepping `- Id:`). It is declared in `Scope-Paths`, so the pre-run spec-impact announcement will name it. Preserve its deterministic validation and merge requirements; telemetry is observational and best effort, never a gate.

CORRECTED AT REVIEW: "IN THE SAME EXECUTION BEFORE IMPLEMENTATION" IS THE WRONG ORDER IF A FLAG IS INVOLVED (F-2). `tests/test_run_flag_surface.py` reads this spec as a FILE (`SPEC_PATH`, `:43-50`), extracts Section 2.1's grammar, and asserts BOTH directions: a flag the spec declares but the code neither registers nor explicitly excludes fails `:136`, and a flag the code registers but the spec omits fails `:150`. So a spec-first amendment that adds a run flag turns the suite red until the registration lands, and the two must be ONE atomic change. This is settled precedent, not speculation: the spec's own 2026-09-07 history records Section 2.1 being deliberately left unamended because "the two ladder flags plan `51vw4y` needs cannot be declared before they are registered, since `tests/test_run_flag_surface.py` binds spec and code bidirectionally".

THE SIMPLEST CORRECT ANSWER IS PROBABLY NO FLAG AT ALL. Order 03 (`lhccjf`) owns telemetry configuration and its OQ-01 resolves it to a key in `.aw/config/project.json` with a machine-local override, not a run flag. If that holds, this amendment touches the run-artifact inventory and the privacy/default/disable semantics and leaves Section 2.1 alone. If a flag is genuinely wanted, raise it as a decision rather than slipping it into a spec edit.

AMENDING AN APPROVED SPEC IS LEGITIMATE AND DELIBERATE HERE. The repository's contract permits a plan to amend a spec whose behavior it changes, provided the file is declared so the runner can announce it. What is NOT permitted is editing an undeclared spec: `c4gd2h` governs E-05's shutdown constraint and is deliberately not declared, so if execution concludes `c4gd2h` must change, that is a STOP-and-raise.

## Open questions

"No open questions" was not accurate: the plan required two decisions it specified nowhere. Both are answerable from repository evidence rather than by asking, so both are recorded resolved with their basis. Siblings `bzz5e6` and `lhccjf` each carried the same inaccurate claim.

### OQ-01: Does this amendment add a run flag, and therefore have to register it atomically?

- Blocking: no
- Status: resolved
- Owner: executor (record the outcome; the CONSTRAINT is decided here)
- Resolution or deferral rationale: RESOLVED AT REVIEW as "default to NO FLAG, and if you add one, register it in the same change". The constraint is not negotiable: `tests/test_run_flag_surface.py` binds spec Section 2.1 and `runner_shared.RUN_POLICY_FLAGS` bidirectionally (`:136` and `:150`), so a spec-only flag declaration is a guaranteed suite failure, and the spec's own 2026-09-07 history records Section 2.1 being left unamended for exactly this reason. The DEFAULT is no flag, because Order 03's OQ-01 already resolved telemetry configuration to a `.aw/config/project.json` key with a machine-local override rather than a CLI surface, and a second control surface for one setting is the kind of duplication this Set's siblings were repeatedly corrected for. If the executor concludes a flag is genuinely needed, it lands atomically with its registration, and V-07 requires the evidence either way.

### OQ-02: How is an execution id made unique across a resume, given `attempt_no` does not reset?

- Blocking: no
- Status: resolved
- Owner: executor (record the construction and its uniqueness argument)
- Resolution or deferral rationale: RESOLVED AT REVIEW as "the id must carry a per-invocation component, and the argument must be written down". Measured, `attempt_no = len(item.get("attempts", [])) + 1` (`oc_runipd.py:5917`) reads a list PERSISTED in `state.json` (`:5947`), so it does not reset on resume; that is correct for attempt numbering and it means a composite of `(position, id6, attempt_no, phase)` is STABLE across a resume and would collide with the earlier invocation's file, defeating the plan's own requirement that identity not be inferable from a single run-level snapshot. Phase must also be an explicit field: executor and verifier are distinguished today only by a `suffix="verify"` string on the log path (`attempt_log_path:4939-4947`), and inferring phase from a filename is exactly the kind of derived-from-presentation coupling that breaks when the filename changes. Rejected: reusing the session log's naming scheme, because it carries the same collision and adds a dependency on a presentation detail. V-02 requires the resume case demonstrated with a mutation check proving the test can fail.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the resolved telemetry path for a `records_backend` of `repository` AND of one non-`repository` value (`companion` or `home`), showing it follows the relocated root; a test asserting only the repository path passes vacuously. Paste a repo-wide grep proving this change added NO new `.aw/records/runs` literal (Order 01's six sites are the ceiling). Paste an object-identity check showing both hosts resolve the seam to the SAME object from `runner_shared`, and an AST-measured `oc_runipd`-to-`agy_runipd` import count showing it did not increase from 47. State explicitly that telemetry is a per-run artifact and NOT inside Order 01's reserved `analytics/` tree.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste two execution ids for the SAME item, attempt and phase separated by a simulated resume in the same run directory, showing they DIFFER; paste the ids for an executor and a verifier invocation of the same attempt, showing phase is an explicit field and not inferred from a filename suffix. Paste the recorded uniqueness argument. Include a mutation check: key the id on `(position, id6, attempt_no, phase)` only, show the resume test FAILS, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the telemetry produced for each OpenCode termination path (clean success, non-zero exit, stall-timeout kill, SIGINT, cancellation, launcher exception), each showing a `start` and a best-effort `end`, with the run outcome unchanged. Paste proof BOTH callers are covered (executor `:6147` and verifier `:6392`, re-located by symbol). Paste proof the version/helper `subprocess.run` sites were NOT instrumented.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the same termination matrix for Agy. Paste the FIELD-BY-FIELD parity assertion output covering both hosts, and name any field that is legitimately host-parameterized with the reason (the `DEPENDENCY_BLOCK_RECOVERY_HINT` carve-out shape). A reviewer's reading of two files is not evidence; paste the test.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste sampler-stopped proof for normal completion, exception, stall kill, SIGINT and SIGTERM. Paste a grep over BOTH drivers showing this change added no `signal.signal(` and no second cleanup routine. Paste the four guard tests (`test_lane_allocation_idempotent.py`, `test_runner_stop.py`, `test_runner_stop_level3.py`, `test_runner_stop_level4.py`) passing UNMODIFIED, since they are what would catch the forbidden shape. If `runner_shutdown.py` was edited, paste the diff showing the EXISTING routine gained a stop call rather than a new path being added, with spec `c4gd2h` R5/A9 cited.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: for EACH injected fault (probe raises, probe timeout, unwritable telemetry dir, append failure, constructor raises, close raises), paste the instrumented run's exit status, item statuses, merge decision and cleanup report BESIDE a paired UNINSTRUMENTED control run, showing them identical. A passing instrumented run alone is not evidence of non-interference. Paste the documented warning where the tree is writable and its absence where it is not.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `25kzda` diff showing telemetry recorded as a best-effort derived artifact that is never a gate, with privacy/default/disable semantics. Paste the pre-run spec-impact announcement naming the file. Paste `tests/test_run_flag_surface.py` PASSING, and state explicitly whether Section 2.1's grammar was touched: if it was, paste the flag's registration in `runner_shared.RUN_POLICY_FLAGS` landing in the SAME change (the bidirectional binding makes a spec-only flag edit a guaranteed failure); if it was not, say so. Confirm no other spec file was edited.
  - Observed evidence:
  - Result: pending

Additionally, and NOT as a separate V-item because it validates no single E-item: V-07 must also carry bare `python3 -m pytest` and `git diff --check` from the executing worktree, against the baseline the executor measured itself, comparing failing NODE IDS and never totals, plus the runner-focused suites named in the required-tests section.

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: both runner integrations must ship together to prevent host-specific observability and schema drift. NOTE THE SCOPE OF THAT ARGUMENT: it justifies ONE PLAN, not one ITEM. Parity is precisely why the two host wirings belong in the same plan; it does not make the seam, the identity scheme, the two wirings, the shutdown behavior, the non-interference proof and the spec amendment one deliverable, which is why the seven items exist (F-6).

EXECUTION CONTRACT. This plan requires explicit human approval (`aw ipd set approved 5f2h8i --by-human --message ...`), and its `Item-Dependencies` refuse dispatch until `lhccjf` (Order 03) is `executed`. That dependency is load-bearing rather than bookkeeping: Order 03 owns the collector, its probes, its configuration and its idempotent close, and this plan only WIRES that object in. Two plans depend on this one, Order 05 (`8hald1`) which ingests what it writes and Order 10 (`9xycbh`) which covers it end to end.

- Commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index you never staged. Other agents and humans work concurrently in this checkout, and this plan touches the two most contended files in it.
- THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT. Never fill an `Observed evidence:` field from memory or from a matching execution checkmark. If a validation cannot be performed, say so plainly and leave it `pending`: an honest gap is acceptable and a fabricated pass is not.
- RE-LOCATE EVERY CITED SYMBOL BY NAME, NOT BY LINE. Every coordinate here was measured at HEAD `d9a32cdd`; the sibling `orchprobe` Set watched the same class of citation drift twice within two days, and `oc_runipd.py` is among the fastest-moving files in the repository.
- RE-MEASURE THE BASELINE YOURSELF and compare failing NODE IDS, never totals.
- Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

Telemetry failures are diagnostic only and must never turn successful work into failure or mask an existing failure. THREE STOP CONDITIONS, each because the alternative is worse than stopping: if you find yourself needing to add `signal.signal(` to either driver, STOP and raise it, because four executed plans' guards forbid it and `runstop` Phase 5 owns that registration; if you find yourself adding a second cleanup routine rather than extending the one that exists, STOP, because spec `c4gd2h` R5/A9 prohibits it; and if you find yourself weakening or editing any of the six named guard tests to make this plan pass, STOP, because those guards are the only thing standing between this Set and the defects they were written for.
