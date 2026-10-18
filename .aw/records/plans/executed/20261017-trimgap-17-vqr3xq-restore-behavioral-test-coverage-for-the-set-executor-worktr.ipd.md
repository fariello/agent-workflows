# IPD: Restore behavioral test coverage for the Set executor, worktree leases, Set lifecycle and host adapters

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine non-slow selection did not reach at baseline HEAD `86f0d88d`, because suite trim `19313eed` deleted the tests that drove them. This child owns the Set-execution and host-adapter slice: groups 17 (`ipd_set_executor.py`, 13 keys), 20 (`set_lifecycle.py`, 5), 24 (`host_launchers.py`, 4), 28 (`worktree_lease.py`, 7), 29 (`host_adapters.py`, 4), 31 (`ipd_set_plan.py`, 3), 33 (`agy_verifier.py`, 2), 35 (`set_state.py`, 1), 41 (`set_records.py`, 1) and 43 (`host_runner.py`, 1), 41 keys in all.
- Scope: Restore four deleted test modules from `19313eed^` at their original paths, minus code-pinning tests, marked `core`, and add residual tests for three keys the restored files reach without asserting on (`SkillPackage.to_dict` is not reached at all; `SkillPackage.resource_paths` and `HostAdapter.advertises_supported` survive early-return mutation, F-04). The 41 keys: `ipd_set_executor.disposition_pass`, `build_lanes`, `routing_config_from_mapping`, `RoutingConfig.resolve`, `make_authorization_record`, `classify_node_work`, `classify_node_work._is_coding`, `classify_node_work._is_prose`, `AuthorizationLedger.proposals`, `AuthorizationLedger.authorized_decisions`, `ready_lanes`, `plan_wave`, `authorize_mutation`; `set_lifecycle.derive_progress`, `stale_evidence_seqs_after_integration`, `make_invalidation_records`, `terminal_transition_allowed`, `resume_or_report`; `host_launchers.plan_launch`, `verify_fresh`, `enforce_model_binding`, `resume_task_packet`; `worktree_lease.LeaseTable.__init__`, `LeaseTable.claim`, `LeaseTable.release`, `LeaseTable.owner_of`, `assert_worker_scope`, `allocate_session`, `path_is_worker_forbidden`; `host_adapters.SkillPackage.to_dict`, `SkillPackage.resource_paths`, `resolve_role_target`, `HostAdapter.advertises_supported`; `ipd_set_plan._run_resume_report`, `run_execute_set`, `_resolve_repo_and_plans`; `agy_verifier.AgySessionDouble.invoke`, `finalize_run`; `set_state.derive_set_state`; `set_records.write_local_projections`; `host_runner.validate_terminal_envelope`. EXCLUDES any production change; EXCLUDES `tests/test_migration_compact_shims.py`, which plan `syzi9i` owns.
- Scope-Paths: tests/test_ipd_set_executor.py, tests/test_exec_set_workflow.py, tests/test_host_runner.py, tests/test_host_adapters_skills.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 17
- Highest E allocated: 05
- Author: opencode
- Id: vqr3xq

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: vqr3xq verified (set trimgap, attempt 1).
- 2026-10-17 approved (aw set): status set to approved

- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, applied the proposed edits to scratch copies, measured per-key reach via coverage contexts, durations, and an early-return mutation sweep over every key; scratch copies and `.coverage` were removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make all 41 keys above reached by the routine bare core-tier run through behavioral tests that build lanes, schedule waves, claim and release leases, derive Set state, plan and verify host launches, and build skill packages, asserting on returned records, refusals and written projections. Done means an early-return mutation of any of the 41 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for E-01..E-04: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent and a module-level `pytestmark = pytest.mark.core` (all four files are cheap, 0.37s summed CPU at authoring); add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. Disposition rule if a kept test (or an E-05 measured value) fails at execution HEAD (none did at authoring, F-02, nor at review, F-05): do not mark the owning item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.

### Task group 1: restore the modules

- [x] E-01 Restore `tests/test_ipd_set_executor.py` with no test deletions (it builds every fixture in a tmpdir; its `agent_workflows/x.py` strings are fixture path data, not source reads).
  - Depends on: none
  - Expected outcome: every test in the restored file passes (19 at authoring and at review; the count is context, not the bar) and the file is core-selected.
  - Execution state: performed

- [x] E-02 Restore `tests/test_exec_set_workflow.py`, deleting the five tests that assert on the text of shipped workflow prose files rather than on behavior (F-02): `ExecSetWorkflowV01.test_workflow_files_exist`, `test_explicit_runtime_fallback_documented`, `ExecSetCliSurfaceV02.test_help_advertises_only_real_commands`, `test_lifecycle_wording_inherited_not_reauthored`, `ExecSetPackagingV03.test_body_has_no_obvious_leak_markers`.
  - Depends on: none
  - Expected outcome: every remaining test passes (9 at authoring and review; context, not the bar); `rg -n "read_text" tests/test_exec_set_workflow.py` returns nothing.
  - Execution state: performed

- [x] E-03 Restore `tests/test_host_runner.py` with no deletions.
  - Depends on: none
  - Expected outcome: every test in the restored file passes (20 at authoring and review; context, not the bar).
  - Execution state: performed

- [x] E-04 Restore `tests/test_host_adapters_skills.py`, removing from `test_reuses_engine_shim_generator_not_forked` only the two object-identity assertions `self.assertIs(ha.generate_shim_members, engine.generate_shim_members)` and `self.assertIs(ha.shim_body, engine.shim_body)` (they pin re-export structure, F-02); keep the rest of that test, which generates shims from the shipped workflow tree and asserts on the output, and reword its docstring so it no longer claims to assert object identity (it should state that it checks `COMMAND_SHIM_DIRS` equality and the generated-shim output; PR-006).
  - Depends on: none
  - Expected outcome: every test in the restored file passes (17 at authoring and review; context, not the bar); `rg -n "assertIs\(ha\." tests/test_host_adapters_skills.py` returns nothing.
  - Execution state: performed

### Task group 2: residual assertions

- [x] E-05 Append to `tests/test_host_adapters_skills.py` a `ResidualKeyTests(unittest.TestCase)` class with three tests, each asserting a value observed at authoring (F-04): (a) `ha.SkillPackage(name="demo", skill_dir=".agents/skills", trigger_description="t", semantic_digest="d1", explicit_invocation="aw x", main_file_content="h\u00e9llo", resources=[ha.SkillResource(relative_path="scripts/a.py", content="x")]).to_dict()` equals `{"name": "demo", "skill_dir": ".agents/skills", "trigger_description": "t", "semantic_digest": "d1", "explicit_invocation": "aw x", "main_file_path": ".agents/skills/demo/SKILL.md", "main_file_bytes": 6, "resource_paths": [".agents/skills/demo/scripts/a.py"]}` (UTF-8 byte count, not character count); (b) the same package's `resource_paths()` equals `[".agents/skills/demo/scripts/a.py"]` and a package with `resources=[]` returns `[]`; (c) `ha.HostAdapter(host="h", exact_version="1", pointer_file="P", skill_dir="s", role_map={}, supported_features=["native-skills"], unverified_features=["subagents"], fallback_runtime="r")` returns True from `advertises_supported("native-skills")` and False from `advertises_supported("subagents")` (an unverified feature is never advertised). Re-measure each value at execution HEAD first; apply the RESTORE RULE disposition if one changed.
  - Depends on: E-04
  - Expected outcome: three new tests pass and kill the scratch mutations named in V-05.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): prose-text assertions and `assertIs` re-export identity checks are dropped (E-02, E-04).
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget): all four files are cheap enough to mark whole.
- Plan `syzi9i` (Order 11 of this Set) restores `tests/test_migration_compact_shims.py` and explicitly excludes `host_adapters.SkillPackage.to_dict` as "owned by other trimgap items"; this child is that owner (E-05).
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `hpjj44` `## Derived properties` reaching-file column for the 41 keys | The keys map to deleted `tests/test_ipd_set_executor.py`, `tests/test_exec_set_workflow.py`, `tests/test_host_runner.py`, `tests/test_host_adapters_skills.py` and (for `SkillPackage.to_dict`) `tests/test_migration_compact_shims.py`. |
| F-02 | `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`; reading the files | All four replay `pass` (19, 14, 20, 17). `test_exec_set_workflow.py` has five tests that only assert substrings of `.aw/system/workflows/...md` prose; `test_host_adapters_skills.py` has two `assertIs` re-export identity assertions. |
| F-03 | Scratch restore with E-01..E-04, `--cov-context=test` | 40 of 41 keys execute; `SkillPackage.to_dict` has zero executed lines. 65 tests, 0.37s summed CPU. |
| F-04 | Early-return mutation sweep, each reverted | 38 keys killed. `SkillPackage.to_dict` -> `{}` survives (unreached); `SkillPackage.resource_paths` -> `[]` survives; `HostAdapter.advertises_supported` -> `False` survives (only the `True` polarity is asserted). Direct calls at HEAD produced the E-05 values. |
| F-05 | Plan review at HEAD `c50b2ce2f`: scratch copies `tests/test_zzscr_*.py` from `19313eed^` with the E-02/E-04 edits plus an E-05 scratch class; a `return None` sweep over all 41 keys; coverage JSON mapped to each key's body lines; all scratch files, `.coverage` and production edits removed (`git diff agent_workflows/` empty, `git status` clean) | Unedited replay `70 passed in 1.19s`; edited `65 passed` (19+9+20+17), `rg read_text` and `rg assertIs(ha.` empty; with E-05 `68 passed` (also under `-n 4` and random order). All 41 keys have an executed body line. Sweep over the four restored files: 39 of 41 killed; `SkillPackage.to_dict` and `HostAdapter.advertises_supported` survive. `advertises_supported` -> `True` is ALREADY killed by the restored files (`1 failed, 38 passed`); the surviving polarity is `-> False` (`64 passed, 1 skipped`). With E-05: `to_dict -> {}`, `resource_paths -> []`, `advertises_supported -> True` and `-> False` each fail a `ResidualKeyTests` test. The four V-01..V-03 spot-check mutations are each killed. E-05 values reproduced exactly. |

## Proposed changes (ordered, validatable)

1. E-01..E-04 restore the four modules with the listed edits.
2. E-05 adds residual assertions for the three under-asserted keys.

## Deferred / out of scope (with reason)

none. (`tests/test_migration_compact_shims.py` is owned by `syzi9i`; the one `q86fxm` key only it reached is covered by E-05.)

## Scope check

- Over-scope: none. Four test files; no production code.
- Under-scope: none for the 41 keys (F-03, F-04, F-05, E-05); V-05 now demands the full 41-key sweep the Goal promises.

## Required tests / validation

- `python3 -m pytest <the four files> -o addopts="" -v` passes, per-test list pasted.
- Reach: the same run with `--cov=agent_workflows.ipd_set_executor --cov=agent_workflows.set_lifecycle --cov=agent_workflows.host_launchers --cov=agent_workflows.worktree_lease --cov=agent_workflows.host_adapters --cov=agent_workflows.ipd_set_plan --cov=agent_workflows.agy_verifier --cov=agent_workflows.set_state --cov=agent_workflows.set_records --cov=agent_workflows.host_runner --cov-report=term-missing`, showing each of the 41 keys executing.
- Reach per key: run the same command with `--cov-report=json:<tmp>/cov.json` and, for each of the 41 keys, report whether any line of its function body is in `executed_lines` (a short script locating each body by symbol is fine; scratch, not committed). `term-missing` alone does not attribute lines to keys.
- Mutation spot-checks (scratch, reverted): `path_is_worker_forbidden` return False, `verify_fresh` return None, `write_local_projections` return None, `derive_set_state` return None, plus the four in V-05; then a full `return None` sweep over all 41 keys against the four files (the Goal's bar and the orchestrator `kn7xtw` invariant this child owns).
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`; delete any `.coverage` data file and scratch script afterwards.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Which child owns `host_adapters.SkillPackage.to_dict`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: this child. `syzi9i` excludes it by name as owned elsewhere, and `q86fxm` group 29 lists it; E-05 adds a direct behavioral assertion rather than restoring a second large file.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `-v` run showing every test in the file PASSED and zero failed or errored (the count is context, not the bar); paste the failures from scratch `path_is_worker_forbidden` return-False and `derive_set_state` return-None mutations (reverted).
  - Observed evidence:
    - `python3 -m pytest tests/test_ipd_set_executor.py -o addopts="" -v`:
      ```
      tests/test_ipd_set_executor.py::WorktreeLeaseV02::test_session_is_per_lane PASSED [  5%]
      tests/test_ipd_set_executor.py::WorktreeLeaseV02::test_real_worktree_create_and_teardown PASSED [ 10%]
      tests/test_ipd_set_executor.py::WorktreeLeaseV02::test_lease_prevents_second_claim PASSED [ 15%]
      tests/test_ipd_set_executor.py::WorktreeLeaseV02::test_worker_path_fence PASSED [ 21%]
      tests/test_ipd_set_executor.py::SchedulerV01::test_every_node_gets_a_disposition PASSED [ 26%]
      tests/test_ipd_set_executor.py::SchedulerV01::test_the_frontier_admits_exactly_the_dependency_satisfied_nodes PASSED [ 31%]
      tests/test_ipd_set_executor.py::SchedulerV01::test_wave_uses_analyzer PASSED [ 36%]
      tests/test_ipd_set_executor.py::SetProgressV03::test_every_progress_shape_derives_its_own_set_state PASSED [ 42%]
      tests/test_ipd_set_executor.py::RoutingV01::test_every_lane_resolves_the_binding_for_its_own_class PASSED [ 47%]
      tests/test_ipd_set_executor.py::RoutingV01::test_missing_binding_fails_closed PASSED [ 52%]
      tests/test_ipd_set_executor.py::RoutingV01::test_build_lanes_fail_closed_on_missing PASSED [ 57%]
      tests/test_ipd_set_executor.py::HandshakeV01::test_mutation_rejected_without_authorization PASSED [ 63%]
      tests/test_ipd_set_executor.py::HandshakeV01::test_mutation_allowed_after_recorded_authorization PASSED [ 68%]
      tests/test_ipd_set_executor.py::HandshakeV01::test_proposal_pending_until_disposed PASSED [ 73%]
      tests/test_ipd_set_executor.py::ClassifierV01::test_every_touched_path_set_lands_in_its_work_class PASSED [ 78%]
      tests/test_ipd_set_executor.py::TerminalGateV03::test_each_precondition_refuses_on_its_own_and_says_why PASSED [ 84%]
      tests/test_ipd_set_executor.py::LifecycleV03::test_resume_fails_closed_on_unknown_outcome PASSED [ 89%]
      tests/test_ipd_set_executor.py::LifecycleV03::test_integration_triggered_evidence_invalidation PASSED [ 94%]
      tests/test_ipd_set_executor.py::IntegrationGateV02::test_every_lane_outcome_set_gets_its_own_typed_verdict PASSED [100%]
      ============================== 19 passed in 0.71s ==============================
      ```
    - Scratch `path_is_worker_forbidden` return-False failure:
      ```
      FAILED tests/test_ipd_set_executor.py::WorktreeLeaseV02::test_worker_path_fence
      AssertionError: LeaseConflictError not raised
      ========================= 1 failed, 18 passed in 0.50s =========================
      ```
    - Scratch `derive_set_state` return-None failure:
      ```
      FAILED tests/test_ipd_set_executor.py::SetProgressV03::test_every_progress_shape_derives_its_own_set_state
      AssertionError: Lists differ: ["  every required node verified terminal ...
      ========================= 1 failed, 18 passed in 0.57s =========================
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a diff against `19313eed^` showing only the five removed tests plus the marker and docstring lines; paste the `-v` run showing every remaining test PASSED and zero failed, the empty `rg` output, and the failure from a scratch `write_local_projections` return-None mutation (reverted).
  - Observed evidence:
    - `git diff 19313eed^:tests/test_exec_set_workflow.py tests/test_exec_set_workflow.py`:
      ```diff
      diff --git a/tests/test_exec_set_workflow.py b/tests/test_exec_set_workflow.py
      index ad6aac7ac..9ec2c4af3 100644
      --- a/tests/test_exec_set_workflow.py
      +++ b/tests/test_exec_set_workflow.py
      @@ -7,6 +7,8 @@ V-02: the CLI surfaces the help advertises actually dispatch - `aw run decisions
             no nonexistent command; lifecycle wording is Order 02's (inherited, not re-authored).
       V-03: generated-drift + packaging + security are clean (the shim regenerates byte-identically; the
             workflow body carries no leak; the manifest row points at a real body).
      +
      +Restored under backlog q86fxm and findings b1mx2w from revision 19313eed^, omitting five tests that asserted on prose and help text rather than behavior (ExecSetWorkflowV01.test_workflow_files_exist, test_explicit_runtime_fallback_documented, ExecSetCliSurfaceV02.test_help_advertises_only_real_commands, test_lifecycle_wording_inherited_not_reauthored, ExecSetPackagingV03.test_body_has_no_obvious_leak_markers).
       """

       from __future__ import annotations
      @@ -21,8 +23,11 @@ from agent_workflows import host_adapters as HA
       from agent_workflows import migration_compact as MC
       from agent_workflows import run_cli
       from agent_workflows import set_records
      +import pytest
       from tests.support import REPO_ROOT, SOURCE_WORKFLOWS

      +pytestmark = pytest.mark.core
      +

       class ExecSetWorkflowV01(unittest.TestCase):
           def setUp(self):
      @@ -32,12 +37,6 @@ class ExecSetWorkflowV01(unittest.TestCase):
               self.workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
               self.wf_map = {w.command: w for w in self.workflows}

      -    def test_workflow_files_exist(self):
      -        self.assertTrue(self.body.is_file(), "exec-set body missing")
      -        self.assertTrue(self.readme.is_file(), "exec-set README missing")
      -        self.assertGreater(len(self.body.read_text(encoding="utf-8").strip()), 200)
      -        self.assertGreater(len(self.readme.read_text(encoding="utf-8").strip()), 50)
      -
           def test_manifest_registers_exec_set(self):
               self.assertIn("exec-set", self.wf_map)
               wf = self.wf_map["exec-set"]
      @@ -62,12 +61,6 @@ class ExecSetWorkflowV01(unittest.TestCase):
                   # regeneration is byte-identical -> no drift
                   self.assertFalse(MC.detect_shim_drift(content, content))

      -    def test_explicit_runtime_fallback_documented(self):
      -        # The body must document the always-available explicit runtime, not only the slash command.
      -        body = self.body.read_text(encoding="utf-8")
      -        self.assertIn("aw ipd execute-set", body)
      -        self.assertIn("--plan-only", body)

       class ExecSetCliSurfaceV02(unittest.TestCase):
           def _projection(self, root, recs):
      @@ -152,71 +145,12 @@ class ExecSetCliSurfaceV02(unittest.TestCase):
               )
               self.assertEqual(ipd_set_plan.run_execute_set(ns), 2)

      -    def test_help_advertises_only_real_commands(self):
      -        # The exec-set body advertises the run INSPECTION verbs and execute-set --resume. Every one
      -        # must be a real dispatch path (no help line names a nonexistent command).
      -        body = (
      -            REPO_ROOT / ".aw" / "system" / "workflows" / "exec-set" / "exec-set.md"
      -        ).read_text(encoding="utf-8")
      -        for advertised in (
      -            "aw runs status",
      -            "aw runs decisions",
      -            "aw runs questions",
      -            "aw ipd execute-set --resume",
      -        ):
      -            self.assertIn(advertised, body)
      -        # The retired spellings must NOT be advertised any more.
      -        for retired in ("aw run status", "aw run decisions", "aw run questions"):
      -            self.assertNotIn(retired, body)
      -        # And the advertised leaves must really exist on the `runs` parser (not just in prose).
      -        from agent_workflows.cli import _build_parser
      -        from agent_workflows.command_surface import discover_parser_leaves
      -
      -        leaves = discover_parser_leaves(_build_parser())
      -        for leaf in ("runs status", "runs decisions", "runs questions"):
      -            self.assertIn(leaf, leaves)
      -        # --max-parallel was trimmed (not a wired flag) - it must NOT be advertised.
      -        self.assertNotIn("--max-parallel", body)
      -
      -    def test_lifecycle_wording_inherited_not_reauthored(self):
      -        # Order 02 owns the shared child-STOP-containment wording on ipd-lifecycle.md; this Order must
      -        # not re-author it. Confirm the canonical phrase still lives there (inherited).
      -        lifecycle = (
      -            REPO_ROOT
      -            / ".aw"
      -            / "system"
      -            / "workflows"
      -            / "ipd-lifecycle"
      -            / "ipd-lifecycle.md"
      -        ).read_text(encoding="utf-8")
      -        self.assertIn("CHILD-scoped", lifecycle)
      -        self.assertIn("Set coordinator", lifecycle)
      -        # execset Order 02 owns that wording (its additive-clarification marker is present).
      -        self.assertIn("execset Order 02", lifecycle)

       class ExecSetPackagingV03(unittest.TestCase):
           def test_manifest_body_points_at_real_file(self):
               workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
               wf = {w.command: w for w in workflows}["exec-set"]
               self.assertTrue((REPO_ROOT / wf.body).is_file())

      -    def test_body_has_no_obvious_leak_markers(self):
      -        # A light packaging check: the shipped body carries no home-path/user leak (the canonical
      -        # sanitizer runs repo-wide in CI; this is a fast local guard for this specific file).
      -        body = (
      -            REPO_ROOT / ".aw" / "system" / "workflows" / "exec-set" / "exec-set.md"
      -        ).read_text(encoding="utf-8")
      -        self.assertNotIn("/home/", body)
      -        self.assertNotIn("/Users/", body)

           def test_regeneration_is_deterministic(self):
               workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
               a = INS.generate_shim_members(workflows, SOURCE_WORKFLOWS)
      ```
    - `python3 -m pytest tests/test_exec_set_workflow.py -o addopts="" -v`:
      ```
      tests/test_exec_set_workflow.py::ExecSetWorkflowV01::test_manifest_registers_exec_set PASSED [ 11%]
      tests/test_exec_set_workflow.py::ExecSetWorkflowV01::test_shims_generated_and_no_drift PASSED [ 22%]
      tests/test_exec_set_workflow.py::ExecSetWorkflowV01::test_skill_package_digest_parity PASSED [ 33%]
      tests/test_exec_set_workflow.py::ExecSetPackagingV03::test_manifest_body_points_at_real_file PASSED [ 44%]
      tests/test_exec_set_workflow.py::ExecSetPackagingV03::test_regeneration_is_deterministic PASSED [ 55%]
      tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02::test_run_decisions_dispatches_and_reads_projection PASSED [ 66%]
      tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02::test_run_questions_dispatches PASSED [ 77%]
      tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02::test_execute_set_resume_flag_exists PASSED [ 88%]
      tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02::test_run_decisions_missing_projection_exit2 PASSED [100%]
      ============================== 9 passed in 0.57s ===============================
      ```
    - `rg -n "read_text" tests/test_exec_set_workflow.py` output: empty (exit code 1).
    - Scratch `write_local_projections` return-None failure:
      ```
      FAILED tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02::test_run_questions_dispatches
      FAILED tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02::test_run_decisions_dispatches_and_reads_projection
      ========================= 2 failed, 7 passed in 0.50s ==========================
      ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` run showing every test in the file PASSED, zero failed, and the failure from a scratch `verify_fresh` return-None mutation (reverted).
  - Observed evidence:
    - `python3 -m pytest tests/test_host_runner.py -o addopts="" -v`:
      ```
      tests/test_host_runner.py::RunnerSpawnV01::test_cancellation_before_spawn PASSED [  5%]
      tests/test_host_runner.py::RunnerSpawnV01::test_run_task_refuses_to_admit_a_leak PASSED [ 10%]
      tests/test_host_runner.py::RunnerSpawnV01::test_argv_passed_as_list PASSED [ 15%]
      tests/test_host_runner.py::RunnerSpawnV01::test_evidence_gate_rejects_failed_exit PASSED [ 20%]
      tests/test_host_runner.py::RunnerSpawnV01::test_exit0_no_diff_is_not_completion PASSED [ 25%]
      tests/test_host_runner.py::RunnerSpawnV01::test_terminal_envelope_valid PASSED [ 30%]
      tests/test_host_runner.py::RunnerSpawnV01::test_redaction_before_ledger PASSED [ 35%]
      tests/test_host_runner.py::RunnerSpawnV01::test_timeout_is_failure PASSED [ 40%]
      tests/test_host_runner.py::RunnerSpawnV01::test_shell_string_rejected PASSED [ 45%]
      tests/test_host_runner.py::RunnerSpawnV01::test_worker_states_map_to_ledger PASSED [ 50%]
      tests/test_host_runner.py::KiroMatrixRowV03::test_kiro_row_shape PASSED  [ 55%]
      tests/test_host_runner.py::KiroMatrixRowV03::test_kiro_row_present_and_copilot_cursor_retained PASSED [ 60%]
      tests/test_host_runner.py::FreshVerificationV03::test_task_local_resume PASSED [ 65%]
      tests/test_host_runner.py::FreshVerificationV03::test_completed_with_evidence_can_finalize PASSED [ 70%]
      tests/test_host_runner.py::FreshVerificationV03::test_wrong_model_fails_closed PASSED [ 75%]
      tests/test_host_runner.py::FreshVerificationV03::test_distinct_sessions_and_finalize PASSED [ 80%]
      tests/test_host_runner.py::FreshVerificationV03::test_soft_denied_exit0_cannot_finalize PASSED [ 85%]
      tests/test_host_runner.py::CapabilityGatedV02::test_no_evidence_selects_fallback PASSED [ 90%]
      tests/test_host_runner.py::CapabilityGatedV02::test_no_fallback_allowed_refuses PASSED [ 95%]
      tests/test_host_runner.py::CapabilityGatedV02::test_positive_evidence_enables_native PASSED [100%]
      ============================== 20 passed in 0.35s ==============================
      ```
    - Scratch `verify_fresh` return-None failure:
      ```
      FAILED tests/test_host_runner.py::FreshVerificationV03::test_distinct_sessions_and_finalize
      AttributeError: 'NoneType' object has no attribute 'executor_session_id'
      ========================= 1 failed, 19 passed in 0.41s =========================
      ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a diff against `19313eed^` showing only the two removed `assertIs` lines, the reworded `test_reuses_engine_shim_generator_not_forked` docstring, plus marker and module docstring; paste the `-v` run showing every test PASSED, zero failed, and the empty `rg` output.
  - Observed evidence:
    - `git diff 19313eed^:tests/test_host_adapters_skills.py tests/test_host_adapters_skills.py` (prior to E-05 addition):
      ```diff
      diff --git a/tests/test_host_adapters_skills.py b/tests/test_host_adapters_skills.py
      index c0f0c0598..012279cf9 100644
      --- a/tests/test_host_adapters_skills.py
      +++ b/tests/test_host_adapters_skills.py
      @@ -37,6 +37,8 @@ Tests that are NOT rows carry a one-line docstring saying why they stay separate
       reasons: the claim is an `assertRaises`; the subject is the real workflow tree on disk rather than a
       fixture; the claim is structural (object identity between two modules); or the setup is materially
       different (a temporary directory used as an isolation base).
      +
      +Restored under backlog q86fxm and findings b1mx2w from revision 19313eed^, omitting two code-pinning object-identity assertions from test_reuses_engine_shim_generator_not_forked.
       """

       from __future__ import annotations
      @@ -48,7 +50,10 @@ from pathlib import Path
       from agent_workflows import agy_verifier as av
       from agent_workflows import engine
       from agent_workflows import host_adapters as ha
      +import pytest
       from agent_workflows import host_capability_registry as hcr
      +
      +pytestmark = pytest.mark.core
       from agent_workflows import verify_roles
       from agent_workflows.run_ledger_store import RedactionPolicy

      @@ -688,15 +693,11 @@ class HostAdapterTests(unittest.TestCase):
               )

           def test_reuses_engine_shim_generator_not_forked(self):
      -        """Kept separate: object IDENTITY between two modules, plus a sweep over the REAL workflow tree.
      +        """Checks COMMAND_SHIM_DIRS equality and the generated-shim output.

      -        Every table row builds a fixture; this asserts `host_adapters` is the same object as
      -        `engine`'s generator (a re-forked copy that behaves identically today is how two generators
      -        drift apart) and then generates from the shipped `.aw/system/workflows` tree, whose absence
      -        legitimately skips the test.
      +        Every table row builds a fixture; this asserts COMMAND_SHIM_DIRS equality and generates
      +        from the shipped `.aw/system/workflows` tree, whose absence legitimately skips the test.
               """
      -        self.assertIs(ha.generate_shim_members, engine.generate_shim_members)
      -        self.assertIs(ha.shim_body, engine.shim_body)
               self.assertEqual(ha.COMMAND_SHIM_DIRS, engine.COMMAND_SHIM_DIRS)

               source_root = _find_source_root()
      ```
    - `python3 -m pytest tests/test_host_adapters_skills.py -k "not ResidualKeyTests" -o addopts="" -v`:
      ```
      tests/test_host_adapters_skills.py::SkillPackageTests::test_every_build_configuration_produces_a_valid_router_package PASSED [  5%]
      tests/test_host_adapters_skills.py::SecurityTests::test_secret_redaction_in_adapter_reasons PASSED [ 11%]
      tests/test_host_adapters_skills.py::SecurityTests::test_external_path_refusal_via_assert_contained PASSED [ 17%]
      tests/test_host_adapters_skills.py::SecurityTests::test_isolated_base_refuses_real_home PASSED [ 23%]
      tests/test_host_adapters_skills.py::SecurityTests::test_every_negative_probe_is_observed_to_fail_closed_with_no_side_effect PASSED [ 29%]
      tests/test_host_adapters_skills.py::SkillDigestTests::test_the_digest_is_deterministic_and_changes_only_with_the_workflow PASSED [ 35%]
      tests/test_host_adapters_skills.py::AgyFreshVerifierTests::test_doubles_never_spawn_agy PASSED [ 41%]
      tests/test_host_adapters_skills.py::AgyFreshVerifierTests::test_execution_and_verifier_have_distinct_sessions PASSED [ 47%]
      tests/test_host_adapters_skills.py::AgyFreshVerifierTests::test_fresh_verifier_refuses_same_session_identity PASSED [ 52%]
      tests/test_host_adapters_skills.py::AgyFreshVerifierTests::test_each_verification_mode_reaches_the_opposite_conclusion_on_one_packet PASSED [ 58%]
      tests/test_host_adapters_skills.py::AgyFreshVerifierTests::test_non_verifier_role_cannot_author_decision PASSED [ 64%]
      tests/test_host_adapters_skills.py::HostAdapterTests::test_reuses_engine_shim_generator_not_forked PASSED [ 70%]
      tests/test_host_adapters_skills.py::HostAdapterTests::test_roles_map_to_native_features_and_fall_back_when_absent PASSED [ 76%]
      tests/test_host_adapters_skills.py::HostAdapterTests::test_an_adapter_advertises_exactly_what_the_registry_can_prove PASSED [ 82%]
      tests/test_host_adapters_skills.py::DiscoveryPolicyTests::test_disabling_skill_leaves_explicit_invocation_usable PASSED [ 88%]
      tests/test_host_adapters_skills.py::DiscoveryPolicyTests::test_inlined_authority_is_detected_without_flagging_a_clean_router PASSED [ 94%]
      tests/test_host_adapters_skills.py::DiscoveryPolicyTests::test_each_workflow_shape_gets_the_discovery_policy_it_needs PASSED [100%]
      ============================== 17 passed in 0.30s ==============================
      ```
    - `rg -n "assertIs\(ha\." tests/test_host_adapters_skills.py` output: empty (exit code 1).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `-v` lines for the three `ResidualKeyTests` tests PASSED; paste the failures from scratch `SkillPackage.to_dict` return-`{}`, `SkillPackage.resource_paths` return-`[]`, `HostAdapter.advertises_supported` return-`False` (the polarity only E-05 kills, F-05) and return-`True` mutations, each naming the failing `ResidualKeyTests` test (reverted); paste the per-key reach listing from Required tests showing all 41 keys with an executed body line; paste the full 41-key `return None` sweep over the four files showing every key KILLED; the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
    - `-v` lines for the three `ResidualKeyTests` tests PASSED:
      ```
      tests/test_host_adapters_skills.py::ResidualKeyTests::test_skill_package_to_dict_byte_count_and_paths PASSED [ 90%]
      tests/test_host_adapters_skills.py::ResidualKeyTests::test_host_adapter_advertises_supported_polarity PASSED [ 95%]
      tests/test_host_adapters_skills.py::ResidualKeyTests::test_skill_package_resource_paths_populated_and_empty PASSED [100%]
      ```
    - Scratch mutations:
      - `SkillPackage.to_dict` return `{}`:
        ```
        FAILED tests/test_host_adapters_skills.py::ResidualKeyTests::test_skill_package_to_dict_byte_count_and_paths
        AssertionError: {} != {'name': 'demo', 'skill_dir': '.agents/ski[212 chars]py']}
        ========================= 1 failed, 19 passed in 0.31s =========================
        ```
      - `SkillPackage.resource_paths` return `[]`:
        ```
        FAILED tests/test_host_adapters_skills.py::ResidualKeyTests::test_skill_package_resource_paths_populated_and_empty
        FAILED tests/test_host_adapters_skills.py::ResidualKeyTests::test_skill_package_to_dict_byte_count_and_paths
        AssertionError: Lists differ: [] != ['.agents/skills/demo/scripts/a.py']
        ========================= 2 failed, 18 passed in 0.35s =========================
        ```
      - `HostAdapter.advertises_supported` return `False`:
        ```
        FAILED tests/test_host_adapters_skills.py::ResidualKeyTests::test_host_adapter_advertises_supported_polarity
        AssertionError: False is not true
        ========================= 1 failed, 19 passed in 0.33s =========================
        ```
      - `HostAdapter.advertises_supported` return `True`:
        ```
        FAILED tests/test_host_adapters_skills.py::ResidualKeyTests::test_host_adapter_advertises_supported_polarity
        FAILED tests/test_host_adapters_skills.py::HostAdapterTests::test_an_adapter_advertises_exactly_what_the_registry_can_prove
        AssertionError: Lists differ: ["  an EMPTY registry, nothing probed ...
        ========================= 2 failed, 18 passed in 0.35s =========================
        ```
    - Per-key reach listing (all 41 keys with an executed body line):
      ```
      OK   agent_workflows/ipd_set_executor.py disposition_pass                         hits: 14
      OK   agent_workflows/ipd_set_executor.py build_lanes                              hits: 10
      OK   agent_workflows/ipd_set_executor.py routing_config_from_mapping              hits: 8
      OK   agent_workflows/ipd_set_executor.py RoutingConfig.resolve                    hits: 5
      OK   agent_workflows/ipd_set_executor.py make_authorization_record                hits: 1
      OK   agent_workflows/ipd_set_executor.py classify_node_work                       hits: 18
      OK   agent_workflows/ipd_set_executor.py classify_node_work._is_coding            hits: 4
      OK   agent_workflows/ipd_set_executor.py classify_node_work._is_prose             hits: 2
      OK   agent_workflows/ipd_set_executor.py AuthorizationLedger.proposals            hits: 3
      OK   agent_workflows/ipd_set_executor.py AuthorizationLedger.authorized_decisions hits: 1
      OK   agent_workflows/ipd_set_executor.py ready_lanes                              hits: 9
      OK   agent_workflows/ipd_set_executor.py plan_wave                                hits: 3
      OK   agent_workflows/ipd_set_executor.py authorize_mutation                       hits: 2
      OK   agent_workflows/set_lifecycle.py    derive_progress                          hits: 8
      OK   agent_workflows/set_lifecycle.py    stale_evidence_seqs_after_integration    hits: 16
      OK   agent_workflows/set_lifecycle.py    make_invalidation_records                hits: 5
      OK   agent_workflows/set_lifecycle.py    terminal_transition_allowed              hits: 9
      OK   agent_workflows/set_lifecycle.py    resume_or_report                         hits: 5
      OK   agent_workflows/host_launchers.py   plan_launch                              hits: 6
      OK   agent_workflows/host_launchers.py   verify_fresh                             hits: 5
      OK   agent_workflows/host_launchers.py   enforce_model_binding                    hits: 3
      OK   agent_workflows/host_launchers.py   resume_task_packet                       hits: 1
      OK   agent_workflows/worktree_lease.py   LeaseTable.__init__                      hits: 2
      OK   agent_workflows/worktree_lease.py   LeaseTable.claim                         hits: 7
      OK   agent_workflows/worktree_lease.py   LeaseTable.release                       hits: 4
      OK   agent_workflows/worktree_lease.py   LeaseTable.owner_of                      hits: 1
      OK   agent_workflows/worktree_lease.py   assert_worker_scope                      hits: 3
      OK   agent_workflows/worktree_lease.py   allocate_session                         hits: 1
      OK   agent_workflows/worktree_lease.py   path_is_worker_forbidden                 hits: 2
      OK   agent_workflows/host_adapters.py    SkillPackage.to_dict                     hits: 1
      OK   agent_workflows/host_adapters.py    SkillPackage.resource_paths              hits: 1
      OK   agent_workflows/host_adapters.py    resolve_role_target                      hits: 4
      OK   agent_workflows/host_adapters.py    HostAdapter.advertises_supported         hits: 1
      OK   agent_workflows/ipd_set_plan.py     _run_resume_report                       hits: 9
      OK   agent_workflows/ipd_set_plan.py     run_execute_set                          hits: 7
      OK   agent_workflows/ipd_set_plan.py     _resolve_repo_and_plans                  hits: 3
      OK   agent_workflows/agy_verifier.py     AgySessionDouble.invoke                  hits: 4
      OK   agent_workflows/agy_verifier.py     finalize_run                             hits: 3
      OK   agent_workflows/set_state.py        derive_set_state                         hits: 13
      OK   agent_workflows/set_records.py      write_local_projections                  hits: 9
      OK   agent_workflows/host_runner.py      validate_terminal_envelope               hits: 2
      All 41 keys reached: True
      ```
    - Full 41-key `return None` sweep (all 41 keys killed):
      ```
      KILLED   agent_workflows/ipd_set_executor.py disposition_pass                         -> 1 failed, 67 passed in 1.24s
      KILLED   agent_workflows/ipd_set_executor.py build_lanes                              -> 5 failed, 63 passed in 1.15s
      KILLED   agent_workflows/ipd_set_executor.py routing_config_from_mapping              -> 4 failed, 64 passed in 1.15s
      KILLED   agent_workflows/ipd_set_executor.py RoutingConfig.resolve                    -> 4 failed, 64 passed in 1.11s
      KILLED   agent_workflows/ipd_set_executor.py make_authorization_record                -> 1 failed, 67 passed in 1.34s
      KILLED   agent_workflows/ipd_set_executor.py classify_node_work                       -> 5 failed, 63 passed in 1.11s
      KILLED   agent_workflows/ipd_set_executor.py classify_node_work._is_coding            -> 1 failed, 67 passed in 1.15s
      KILLED   agent_workflows/ipd_set_executor.py classify_node_work._is_prose             -> 1 failed, 67 passed in 1.46s
      KILLED   agent_workflows/ipd_set_executor.py AuthorizationLedger.proposals            -> 1 failed, 67 passed in 1.22s
      KILLED   agent_workflows/ipd_set_executor.py AuthorizationLedger.authorized_decisions -> 2 failed, 66 passed in 1.08s
      KILLED   agent_workflows/ipd_set_executor.py ready_lanes                              -> 3 failed, 65 passed in 1.42s
      KILLED   agent_workflows/ipd_set_executor.py plan_wave                                -> 1 failed, 67 passed in 1.19s
      KILLED   agent_workflows/ipd_set_executor.py authorize_mutation                       -> 1 failed, 67 passed in 1.14s
      KILLED   agent_workflows/set_lifecycle.py    derive_progress                          -> 1 failed, 67 passed in 2.32s
      KILLED   agent_workflows/set_lifecycle.py    stale_evidence_seqs_after_integration    -> 1 failed, 67 passed in 1.97s
      KILLED   agent_workflows/set_lifecycle.py    make_invalidation_records                -> 1 failed, 67 passed in 1.19s
      KILLED   agent_workflows/set_lifecycle.py    terminal_transition_allowed              -> 1 failed, 67 passed in 1.10s
      KILLED   agent_workflows/set_lifecycle.py    resume_or_report                         -> 1 failed, 67 passed in 2.86s
      KILLED   agent_workflows/host_launchers.py   plan_launch                              -> 3 failed, 65 passed in 1.03s
      KILLED   agent_workflows/host_launchers.py   verify_fresh                             -> 1 failed, 67 passed in 1.15s
      KILLED   agent_workflows/host_launchers.py   enforce_model_binding                    -> 1 failed, 67 passed in 1.67s
      KILLED   agent_workflows/host_launchers.py   resume_task_packet                       -> 1 failed, 67 passed in 1.14s
      KILLED   agent_workflows/worktree_lease.py   LeaseTable.__init__                      -> 1 failed, 67 passed in 2.15s
      KILLED   agent_workflows/worktree_lease.py   LeaseTable.claim                         -> 1 failed, 67 passed in 1.19s
      KILLED   agent_workflows/worktree_lease.py   LeaseTable.release                       -> 1 failed, 67 passed in 1.32s
      KILLED   agent_workflows/worktree_lease.py   LeaseTable.owner_of                      -> 1 failed, 67 passed in 1.83s
      KILLED   agent_workflows/worktree_lease.py   assert_worker_scope                      -> 1 failed, 67 passed in 1.13s
      KILLED   agent_workflows/worktree_lease.py   allocate_session                         -> 1 failed, 67 passed in 1.12s
      KILLED   agent_workflows/worktree_lease.py   path_is_worker_forbidden                 -> 1 failed, 67 passed in 2.06s
      KILLED   agent_workflows/host_adapters.py    SkillPackage.to_dict                     -> 1 failed, 67 passed in 1.11s
      KILLED   agent_workflows/host_adapters.py    SkillPackage.resource_paths              -> 3 failed, 65 passed in 1.50s
      KILLED   agent_workflows/host_adapters.py    resolve_role_target                      -> 1 failed, 67 passed in 1.19s
      KILLED   agent_workflows/host_adapters.py    HostAdapter.advertises_supported         -> 1 failed, 66 passed, 1 skipped in 1.07s
      KILLED   agent_workflows/ipd_set_plan.py     _run_resume_report                       -> 1 failed, 67 passed in 1.13s
      KILLED   agent_workflows/ipd_set_plan.py     run_execute_set                          -> 1 failed, 67 passed in 1.09s
      KILLED   agent_workflows/ipd_set_plan.py     _resolve_repo_and_plans                  -> 1 failed, 67 passed in 1.17s
      KILLED   agent_workflows/agy_verifier.py     AgySessionDouble.invoke                  -> 1 failed, 67 passed in 1.16s
      KILLED   agent_workflows/agy_verifier.py     finalize_run                             -> 1 failed, 67 passed in 2.42s
      KILLED   agent_workflows/set_state.py        derive_set_state                         -> 1 failed, 67 passed in 1.13s
      KILLED   agent_workflows/set_records.py      write_local_projections                  -> 2 failed, 66 passed in 1.06s
      KILLED   agent_workflows/host_runner.py      validate_terminal_envelope               -> 1 failed, 67 passed in 1.31s
      All 41 keys killed by return None sweep: True
      ```
    - Bare pytest summary line: `1469 passed, 3 warnings in 33.60s` (via `aw suite`).
    - Final `git diff agent_workflows/` is empty.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; none block.
- Scope fence (a declaration, not a stop condition): the four Scope-Paths test files are the only intended changes. Any other path you edit (for example a `bug` backlog item filed under the RESTORE RULE) must be justified at finalize with `--scope-reason`; a declared path left unmodified needs `--scope-ack`.
- Honesty rule: every V-item MUST paste the ACTUAL runner output; never claim a pass, a kill, or a reach you did not run and observe.
- Mutation spot-checks and the sweep are scratch production edits: revert each immediately, and confirm `git diff agent_workflows/` is empty before committing. Delete any `.coverage` file and scratch script.
- Commit: only the four Scope-Paths files, through `aw commit vqr3xq -- <paths>`; run `git diff --cached --name-only` first and unstage anything not yours. Never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize vqr3xq` instead. Never hand-`git mv` the plan.
