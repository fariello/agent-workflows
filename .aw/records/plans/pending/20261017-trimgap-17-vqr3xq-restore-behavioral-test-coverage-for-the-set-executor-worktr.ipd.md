# IPD: Restore behavioral test coverage for the Set executor, worktree leases, Set lifecycle and host adapters

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine non-slow selection did not reach at baseline HEAD `86f0d88d`, because suite trim `19313eed` deleted the tests that drove them. This child owns the Set-execution and host-adapter slice: groups 17 (`ipd_set_executor.py`, 13 keys), 20 (`set_lifecycle.py`, 5), 24 (`host_launchers.py`, 4), 28 (`worktree_lease.py`, 7), 29 (`host_adapters.py`, 4), 31 (`ipd_set_plan.py`, 3), 33 (`agy_verifier.py`, 2), 35 (`set_state.py`, 1), 41 (`set_records.py`, 1) and 43 (`host_runner.py`, 1), 41 keys in all.
- Scope: Restore four deleted test modules from `19313eed^` at their original paths, minus code-pinning tests, marked `core`, and add residual tests for three keys the restored files reach without asserting on (`SkillPackage.to_dict` is not reached at all; `SkillPackage.resource_paths` and `HostAdapter.advertises_supported` survive early-return mutation, F-04). The 41 keys: `ipd_set_executor.disposition_pass`, `build_lanes`, `routing_config_from_mapping`, `RoutingConfig.resolve`, `make_authorization_record`, `classify_node_work`, `classify_node_work._is_coding`, `classify_node_work._is_prose`, `AuthorizationLedger.proposals`, `AuthorizationLedger.authorized_decisions`, `ready_lanes`, `plan_wave`, `authorize_mutation`; `set_lifecycle.derive_progress`, `stale_evidence_seqs_after_integration`, `make_invalidation_records`, `terminal_transition_allowed`, `resume_or_report`; `host_launchers.plan_launch`, `verify_fresh`, `enforce_model_binding`, `resume_task_packet`; `worktree_lease.LeaseTable.__init__`, `LeaseTable.claim`, `LeaseTable.release`, `LeaseTable.owner_of`, `assert_worker_scope`, `allocate_session`, `path_is_worker_forbidden`; `host_adapters.SkillPackage.to_dict`, `SkillPackage.resource_paths`, `resolve_role_target`, `HostAdapter.advertises_supported`; `ipd_set_plan._run_resume_report`, `run_execute_set`, `_resolve_repo_and_plans`; `agy_verifier.AgySessionDouble.invoke`, `finalize_run`; `set_state.derive_set_state`; `set_records.write_local_projections`; `host_runner.validate_terminal_envelope`. EXCLUDES any production change; EXCLUDES `tests/test_migration_compact_shims.py`, which plan `syzi9i` owns.
- Scope-Paths: tests/test_ipd_set_executor.py, tests/test_exec_set_workflow.py, tests/test_host_runner.py, tests/test_host_adapters_skills.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 17
- Highest E allocated: 05
- Author: opencode
- Id: vqr3xq

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, applied the proposed edits to scratch copies, measured per-key reach via coverage contexts, durations, and an early-return mutation sweep over every key; scratch copies and `.coverage` were removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make all 41 keys above reached by the routine bare core-tier run through behavioral tests that build lanes, schedule waves, claim and release leases, derive Set state, plan and verify host launches, and build skill packages, asserting on returned records, refusals and written projections. Done means an early-return mutation of any of the 41 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for E-01..E-04: create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent and a module-level `pytestmark = pytest.mark.core` (all four files are cheap, 0.37s summed CPU at authoring); add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w`, revision `19313eed^` and what was deliberately not restored; keep every other test body unchanged. If a kept test fails at execution HEAD, STOP on it: record it in Findings, and either update only that expectation for an intended change (cite the commit found by `git log -S`) or file a `bug` backlog item with `--blocks-release next` for a regression.

### Task group 1: restore the modules

- [ ] E-01 Restore `tests/test_ipd_set_executor.py` with no test deletions (it builds every fixture in a tmpdir; its `agent_workflows/x.py` strings are fixture path data, not source reads).
  - Depends on: none
  - Expected outcome: 19 tests pass, all core-selected.
  - Execution state: pending

- [ ] E-02 Restore `tests/test_exec_set_workflow.py`, deleting the five tests that assert on the text of shipped workflow prose files rather than on behavior (F-02): `ExecSetWorkflowV01.test_workflow_files_exist`, `test_explicit_runtime_fallback_documented`, `ExecSetCliSurfaceV02.test_help_advertises_only_real_commands`, `test_lifecycle_wording_inherited_not_reauthored`, `ExecSetPackagingV03.test_body_has_no_obvious_leak_markers`.
  - Depends on: none
  - Expected outcome: 9 tests pass; `rg -n "read_text" tests/test_exec_set_workflow.py` returns nothing.
  - Execution state: pending

- [ ] E-03 Restore `tests/test_host_runner.py` with no deletions.
  - Depends on: none
  - Expected outcome: 20 tests pass.
  - Execution state: pending

- [ ] E-04 Restore `tests/test_host_adapters_skills.py`, removing from `test_reuses_engine_shim_generator_not_forked` only the two object-identity assertions `self.assertIs(ha.generate_shim_members, engine.generate_shim_members)` and `self.assertIs(ha.shim_body, engine.shim_body)` (they pin re-export structure, F-02); keep the rest of that test, which generates shims from the shipped workflow tree and asserts on the output.
  - Depends on: none
  - Expected outcome: 17 tests pass; `rg -n "assertIs\(ha\." tests/test_host_adapters_skills.py` returns nothing.
  - Execution state: pending

### Task group 2: residual assertions

- [ ] E-05 Append to `tests/test_host_adapters_skills.py` a `ResidualKeyTests(unittest.TestCase)` class with three tests, each asserting a value observed at authoring (F-04): (a) `ha.SkillPackage(name="demo", skill_dir=".agents/skills", trigger_description="t", semantic_digest="d1", explicit_invocation="aw x", main_file_content="h\u00e9llo", resources=[ha.SkillResource(relative_path="scripts/a.py", content="x")]).to_dict()` equals `{"name": "demo", "skill_dir": ".agents/skills", "trigger_description": "t", "semantic_digest": "d1", "explicit_invocation": "aw x", "main_file_path": ".agents/skills/demo/SKILL.md", "main_file_bytes": 6, "resource_paths": [".agents/skills/demo/scripts/a.py"]}` (UTF-8 byte count, not character count); (b) the same package's `resource_paths()` equals `[".agents/skills/demo/scripts/a.py"]` and a package with `resources=[]` returns `[]`; (c) `ha.HostAdapter(host="h", exact_version="1", pointer_file="P", skill_dir="s", role_map={}, supported_features=["native-skills"], unverified_features=["subagents"], fallback_runtime="r")` returns True from `advertises_supported("native-skills")` and False from `advertises_supported("subagents")` (an unverified feature is never advertised). Re-measure each value at execution HEAD first; apply the RESTORE RULE stop if one changed.
  - Depends on: E-04
  - Expected outcome: three new tests pass and kill the scratch mutations named in V-05.
  - Execution state: pending

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

## Proposed changes (ordered, validatable)

1. E-01..E-04 restore the four modules with the listed edits.
2. E-05 adds residual assertions for the three under-asserted keys.

## Deferred / out of scope (with reason)

none. (`tests/test_migration_compact_shims.py` is owned by `syzi9i`; the one `q86fxm` key only it reached is covered by E-05.)

## Scope check

- Over-scope: none. Four test files; no production code.
- Under-scope: none for the 41 keys (F-03, F-04, E-05).

## Required tests / validation

- `python3 -m pytest <the four files> -o addopts="" -v` passes, per-test list pasted.
- Reach: the same run with `--cov=agent_workflows.ipd_set_executor --cov=agent_workflows.set_lifecycle --cov=agent_workflows.host_launchers --cov=agent_workflows.worktree_lease --cov=agent_workflows.host_adapters --cov=agent_workflows.ipd_set_plan --cov=agent_workflows.agy_verifier --cov=agent_workflows.set_state --cov=agent_workflows.set_records --cov=agent_workflows.host_runner --cov-report=term-missing`, showing each of the 41 keys executing.
- Mutation spot-checks (scratch, reverted): `path_is_worker_forbidden` return False, `verify_fresh` return None, `write_local_projections` return None, `derive_set_state` return None, plus the three in V-05.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

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

- [ ] V-01 validates E-01
  - Required evidence: paste the `-v` run listing 19 PASSED; paste the failures from scratch `path_is_worker_forbidden` return-False and `derive_set_state` return-None mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a diff against `19313eed^` showing only the five removed tests plus the marker and docstring lines; paste the `-v` run listing 9 PASSED, the empty `rg` output, and the failure from a scratch `write_local_projections` return-None mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` run listing 20 PASSED and the failure from a scratch `verify_fresh` return-None mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a diff against `19313eed^` showing only the two removed `assertIs` lines plus marker and docstring; paste the `-v` run listing 17 PASSED and the empty `rg` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` lines for the three `ResidualKeyTests` tests PASSED; paste the failures from scratch `SkillPackage.to_dict` return-`{}`, `SkillPackage.resource_paths` return-`[]` and `HostAdapter.advertises_supported` return-`True` mutations (reverted); paste the reach output from Required tests showing all 41 keys executing, the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the four Scope-Paths files through `aw commit vqr3xq -- <paths>`; never push. Mutation spot-checks are scratch production edits that must be reverted and absent from the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
