# IPD: Restore behavioral coverage for agent record validation, id6 collision set and artifact type inference

- Date: 2026-10-23
- Kind: child
- Concern: Residual backlog item `nzc6dm` carries three record-handling keys whose `return-none` mutants the routine core tier does not kill, although core reaches all three: `agent_schema.validate_agent_record` (group 22, `wo21z5` `budget-exhausted`), `artifact_rename._existing_type_id6s` (group 23, `unprovable`) and `doctor._infer_artifact_type` (group 34, `budget-exhausted`). Measured at authoring HEAD `6c0a6b72a` (F-01, F-02): each is reached by core-marked tests, yet each `return-none` mutant SURVIVES those tests, because the core callers only check that something was emitted, not what these helpers decided. So a regression that let every malformed `aw.agent/v1` record validate, that made id6 minting blind to existing ids (collision risk on a permanent identity), or that sent every `aw doctor` remediation to the `plans` type would pass the routine gate.
- Scope: Add ONE new core-marked test module, `tests/test_record_residual_helpers.py`, with direct behavioral tests of the three keys and of their observable effect through their public callers (`agent_schema.is_valid_agent_record`, `doctor.build_remediation`), asserting on returned error lists, id sets and remediation text (values measured at F-03); then probe all three under the core selection. EXCLUDES any production-code change and any change to existing tests.
- Scope-Paths: tests/test_record_residual_helpers.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: nzc6dm
- Set: trimgap
- Order: 33
- Highest E allocated: 05
- Author: opencode
- Id: v44udc
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (uncollectable ...Tests class names -> plain Test* classes), PR-002 (run module before commit), PR-003 (execution contract), PR-004 (budget-only overrun, grep bounds) fixed; F-03 values re-measured at 503f15cbd

- 2026-10-23 to-review (opencode): authored from backlog `nzc6dm` (groups 22, 23, 34). Measured core reach at HEAD `6c0a6b72a`, probed each key against its core-reaching files (all `survived`), and measured every asserted return value before writing expected outcomes.
- 2026-10-23 draft (opencode): created.

## Goal

Make a `return-none` mutation of any of the three keys turn a routine core-tier test red. Done means all three report `verdict: killed` under a `-m core` selection containing the new module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the new core-tier module

- [x] E-01 Create `tests/test_record_residual_helpers.py` with a provenance docstring naming backlog `nzc6dm`, plan `v44udc` and findings `wo21z5`; `import pytest`; module-level `pytestmark = pytest.mark.core`; and a `TestValidateAgentRecord` class. All three classes in this module are PLAIN pytest classes whose names start with `Test` (no `unittest.TestCase` base): `pyproject.toml` `[tool.pytest.ini_options]` sets no `python_classes`, so pytest's default `Test*` prefix applies and a class named `...Tests` without a `TestCase` base is silently NOT collected, while a `TestCase` subclass cannot receive the `tmp_path` fixture E-02 and E-03 need (both demonstrated at review, record `v44udc` Round 1). With `good = {"schema": agent_schema.SCHEMA_VERSION, "kind": "result", "cmd": "x", "exit": 0, "outcome": "ok", "verified": True, "complete": True}`, assert: `validate_agent_record(good) == []` and `is_valid_agent_record(good)` is True; `validate_agent_record(dict(good, exit=7)) == ["Field 'exit' must be an integer in (0, 1, 2), got '7'"]`; `validate_agent_record({})` contains the three errors `"Invalid schema: expected 'aw.agent/v1', got 'None'"`, `"Invalid kind: 'None' must be one of ('result', 'summary', 'item', 'error')"` and `"Field 'cmd' must be a non-empty string"`, and `is_valid_agent_record({})` is False; a result record without `verified`/`complete` reports `"Result record missing boolean 'verified' field"` and `"Result record missing boolean 'complete' field"`.
  - Depends on: none
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: performed

- [x] E-02 Add an `TestExistingTypeId6s` class using `tmp_path` (git-initialized with `git init -q`): write `.aw/records/plans/pending/20261001-sx-01-abc123-x.ipd.md` containing `- Id: abc123` and `.aw/records/plans/pending/legacy.md` containing `- Id: zzz999`, and assert `artifact_rename._existing_type_id6s(tmp_path, "plans") == {"abc123", "zzz999"}` (both the clustered filename id6 and a legacy file's `- Id:` line are collected, which is what keeps a fresh mint from colliding); and an empty git-initialized repo returns `set()`.
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: performed

- [x] E-03 Add an `TestInferArtifactType` class: `doctor._infer_artifact_type` returns `None` for `""` and `"README.md"`; `"plans"` for `".aw/records/plans/pending/a.ipd.md"`; `"specs"` for `"x.spec.md"`; `"prompts"` for `".agents/prompts/a"`; `"backlog"` for `"x.backlog.md"`; `"research"` for `".aw/records/research/x"`; `"walkthroughs"` for `"x.walkthrough.md"`; `"comms"` for `".aw/records/comms/a"`; `"releases"` for `"x.release.md"`. Then assert the observable effect through `doctor.build_remediation(artifact_core.Drift(loc, "check.name-nonconformant", "d"), tmp_path)`: for `loc = ".aw/records/specs/20261001-abc123-01-abc123-x.spec.md"` the `summary_fix` contains `aw rename specs abc123`, and for `loc = ".aw/records/backlog/open/20261001-sx-01-abc123-x.backlog.md"` it contains `aw rename backlog abc123` (a mutant would route both to `plans`).
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: performed

### Task group 2: commit and prove the mutants die in core

- [x] E-04 First run `python3 -m pytest -o addopts="" -v -n0 tests/test_record_residual_helpers.py` and confirm every test PASSED (this is the V-01..V-03 evidence; fix the module before committing, never commit a red module). Then verify `git diff --cached --name-only` lists only that path, commit the module with `aw commit v44udc -- tests/test_record_residual_helpers.py` (the probe in E-05 reads committed HEAD, which is why the commit precedes it), then run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim, plus `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_record_residual_helpers.py`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: bare run shows no failures and includes the new tests; the module costs well under one second serial. A `CORE TIER BUDGET EXCEEDED` block with zero failing tests is a pre-existing, load-dependent host condition: record it verbatim and do not count it as a failure of this plan; any failing test IS a failure.
  - Execution state: performed

- [x] E-05 For each key K in (`agent_workflows/agent_schema.py::validate_agent_record`, `agent_workflows/artifact_rename.py::_existing_type_id6s`, `agent_workflows/doctor.py::_infer_artifact_type`), run `python3 tools/mutation_probe.py --op return-none --format json K -- -o addopts= -q -p no:randomly -n0 -m core tests/test_record_residual_helpers.py`, after E-04's commit. A kill under this core-marked subset is a kill under the full core tier, a superset. Record each `verdict`, `baseline_failing` and `mutant_failing`; if any key survives, add the missing assertion, commit the same way, and re-probe.
  - Depends on: E-04
  - Expected outcome: three `verdict: killed`, each `baseline_failing: 0`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16): every test calls a production function and asserts on its result.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget; module-level `pytestmark = pytest.mark.core` is the established way in.
- `artifact_rename._existing_type_id6s` feeds `artifact_core.mint_id6` in `run_rename_generic`'s `--to-id6` path, so its id set is the collision guard for a permanent identity.
- Probe tool: `tools/mutation_probe.py` as used by `wo21z5` and siblings.
- Commit only through `aw commit v44udc -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/replay_coverage_diff.py baseline --out .aw/state/nzc6dm-auth/core -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `6c0a6b72a` | Core reaches `validate_agent_record` (22 contexts in 7 files), `_existing_type_id6s` (4, `tests/test_spec_id6_filenames.py`) and `_infer_artifact_type` (6 in 4 files). |
| F-02 | `tools/mutation_probe.py --op return-none --format json <K> -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" <core-reaching files>` at `6c0a6b72a` | `validate_agent_record`: `survived`, 0 (65.95s). `_existing_type_id6s`: `survived`, 0 (16.0s). `_infer_artifact_type`: `survived`, 0 (72.0s). Reach without assertion. |
| F-03 | direct calls at HEAD `6c0a6b72a` | `validate_agent_record(good)` -> `[]`; `exit=7` -> `["Field 'exit' must be an integer in (0, 1, 2), got '7'"]`; `{}` -> the three schema/kind/cmd errors in E-01; a result without `verified`/`complete` -> the two missing-boolean errors. `_existing_type_id6s` on the E-02 fixture -> `{'abc123', 'zzz999'}`; empty repo -> `set()`. `_infer_artifact_type`: values as listed in E-03 (`'.aw/records/reviews/x.md'` and `'.aw/records/runs/x'` -> `None`, so those are not asserted as types). `build_remediation` with `check.name-nonconformant`: spec loc -> `rename with 'aw rename specs abc123 --slug <corrected-slug> --apply' ...`; backlog loc -> `... 'aw rename backlog abc123 ...`. |
| F-04 | re-run at review HEAD `503f15cbd` | Every F-03 value reproduces verbatim (all `validate_agent_record` error lists, `{'abc123', 'zzz999'}` / `set()`, all ten `_infer_artifact_type` results, both `build_remediation` `summary_fix` strings); `git diff --stat 6c0a6b72a..HEAD` on `agent_schema.py`, `artifact_rename.py`, `doctor.py`, `selectors.py` is empty. `doctor.build_remediation`'s `check.name-nonconformant` branch uses `target_type = art_type or "plans"`, confirming a `return-none` mutant routes both locations to `plans`. |

## Proposed changes (ordered, validatable)

1. E-01 creates the module and the agent-record validation tests.
2. E-02 adds the id6 collision-set tests.
3. E-03 adds the artifact-type inference tests and their remediation effect.
4. E-04 commits the module and records the bare core gate.
5. E-05 probes the three keys under the core selection.

## Deferred / out of scope (with reason)

- Restoring the `wo21z5` control files (`tests/test_evidence_receipts.py`, `tests/test_prompt_id6_filenames.py`).
  - Carrier-Declined: no work is owed; they are 251 and 375 lines of broader integration, while the gap is three missing assertions that direct tests close at a fraction of the core cost.

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. All three keys get direct assertions (E-01 to E-03) and a core-selection probe (E-05).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_record_residual_helpers.py`: every test PASSED, list pasted (E-01 to E-03).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-04).
- Three `tools/mutation_probe.py` JSON results pasted, each `verdict: killed`, `baseline_failing: 0` (E-05).
- `git diff --stat <E-04 parent>..HEAD -- agent_workflows/` empty (no production change).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Assert the private helpers directly, or only through public callers?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Both, where a public caller exists. Direct calls pin each branch cheaply; the public-caller assertions (`is_valid_agent_record`, `build_remediation`) show the decision reaches an output a user sees. `_existing_type_id6s` has only the `--to-id6` rename path as a caller, which needs a full rename transaction, so it is asserted directly; this matches the Set precedent (executed `33f8tn` tested two private helpers directly where no cheaper public surface existed).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_record_residual_helpers.py` showing the provenance docstring (naming `nzc6dm`, `v44udc`, `wo21z5`) and `pytestmark = pytest.mark.core`; the `-v` lines for every `TestValidateAgentRecord` test, each PASSED; and `grep -nE "\binspect\b|getsource|\bast\." tests/test_record_residual_helpers.py` returning nothing; and the `-v` output's collected count for the module is non-zero for each of the three classes (no class silently uncollected).
  - Observed evidence:
    Head of `tests/test_record_residual_helpers.py`:
    ```python
    """Direct behavioral tests for agent record validation, id6 collision sets, and artifact type inference.

    Restores core-tier behavioral coverage for record-handling residual helpers recorded in
    backlog item nzc6dm, plan v44udc, and findings wo21z5:
    - agent_schema.validate_agent_record (group 22)
    - artifact_rename._existing_type_id6s (group 23)
    - doctor._infer_artifact_type (group 34)
    """

    from __future__ import annotations

    import subprocess
    from pathlib import Path

    import pytest

    from agent_workflows import agent_schema, artifact_core, artifact_rename, doctor

    pytestmark = pytest.mark.core
    ```
    `-v` lines for `TestValidateAgentRecord`:
    ```
    tests/test_record_residual_helpers.py::TestValidateAgentRecord::test_validate_agent_record_invalid_exit_code PASSED [ 62%]
    tests/test_record_residual_helpers.py::TestValidateAgentRecord::test_validate_agent_record_missing_verified_and_complete PASSED [ 75%]
    tests/test_record_residual_helpers.py::TestValidateAgentRecord::test_validate_agent_record_empty_record PASSED [ 87%]
    tests/test_record_residual_helpers.py::TestValidateAgentRecord::test_validate_agent_record_valid_record PASSED [100%]
    ```
    `grep -nE "\binspect\b|getsource|\bast\." tests/test_record_residual_helpers.py` output:
    ```
    (exit code 1, empty output)
    ```
    Collected counts per class:
    Collected 8 items across all 3 classes (TestValidateAgentRecord: 4, TestExistingTypeId6s: 2, TestInferArtifactType: 2; all non-zero).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` lines for every `TestExistingTypeId6s` test, each PASSED.
  - Observed evidence:
    ```
    tests/test_record_residual_helpers.py::TestExistingTypeId6s::test_existing_type_id6s_empty_repo PASSED [ 37%]
    tests/test_record_residual_helpers.py::TestExistingTypeId6s::test_existing_type_id6s_collects_clustered_and_legacy_ids PASSED [ 50%]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` lines for every `TestInferArtifactType` test, each PASSED, including the `build_remediation` assertions.
  - Observed evidence:
    ```
    tests/test_record_residual_helpers.py::TestInferArtifactType::test_infer_artifact_type_mappings PASSED [ 12%]
    tests/test_record_residual_helpers.py::TestInferArtifactType::test_build_remediation_summary_fix_routes_to_inferred_type PASSED [ 25%]
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) naming only `tests/test_record_residual_helpers.py`; the bare `python3 -m pytest` summary line with no `failed` (a budget-only overrun is recorded, not failed, per E-04), any `CORE TIER BUDGET EXCEEDED` block verbatim, and the module's `--durations=0` output.
  - Observed evidence:
    `aw commit` output:
    ```
    aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/v44udc but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/v44udc's package (set AW_NO_REEXEC=1 to disable)
    aw commit: committed 1 path(s): 03c9e50e50e17441dd2d774788b0869c54b071d1
    ```
    `git show --stat 03c9e50e50e17441dd2d774788b0869c54b071d1`:
    ```
    commit 03c9e50e50e17441dd2d774788b0869c54b071d1
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Sat Oct 24 09:42:18 2026 -0400

        work(v44udc): Restore behavioral coverage for agent record validation, id6 collision set and artifact type inference

        AW-Run: run-20261024T014611Z-3126016
        AW-Item: v44udc
        AW-Runner: aw agy run

     tests/test_record_residual_helpers.py | 128 ++++++++++++++++++++++++++++++++++
     1 file changed, 128 insertions(+)
    ```
    Bare `python3 -m pytest` summary line and `CORE TIER BUDGET EXCEEDED` block:
    ```
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 69.39s exceeded budget of 30.00s.
    Host 1-minute load average: 13.90 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    Top 10 slowest core tests:
       1.   8.48s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       2.   7.41s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       3.   6.42s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       4.   5.61s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       5.   5.10s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       6.   4.44s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
       7.   4.36s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       8.   3.98s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
       9.   3.40s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
      10.   2.96s  tests/test_ipd_lint.py::ReadinessAttestationTests::test_every_readiness_carrying_plan_in_the_tree_is_attested
    ===========================================================================================

    1823 passed, 11 warnings in 69.38s (0:01:09)
    ```
    Module `--durations=0` output (`python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_record_residual_helpers.py`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=4273098010
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/v44udc
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 8 items

    tests/test_record_residual_helpers.py ........                           [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== slowest durations ===============================
    0.01s call     tests/test_record_residual_helpers.py::TestExistingTypeId6s::test_existing_type_id6s_collects_clustered_and_legacy_ids
    0.01s call     tests/test_record_residual_helpers.py::TestExistingTypeId6s::test_existing_type_id6s_empty_repo

    (22 durations < 0.005s hidden.  Use -vv to show these durations.)
    ============================== 8 passed in 0.52s ===============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the three JSON outputs produced by `tools/mutation_probe.py` (E-05), each with `head` equal to the E-04 commit or later, a selection containing `-m core tests/test_record_residual_helpers.py`, `verdict: killed` and `baseline_failing: 0`; and `git diff --stat <E-04 parent>..HEAD -- agent_workflows/` showing no change.
  - Observed evidence:
    Target 1: `agent_workflows/agent_schema.py::validate_agent_record`
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "03c9e50e50e17441dd2d774788b0869c54b071d1", "mutant_failing": 4, "newly_failing": ["tests.test_record_residual_helpers.TestValidateAgentRecord::test_validate_agent_record_empty_record", "tests.test_record_residual_helpers.TestValidateAgentRecord::test_validate_agent_record_invalid_exit_code", "tests.test_record_residual_helpers.TestValidateAgentRecord::test_validate_agent_record_missing_verified_and_complete", "tests.test_record_residual_helpers.TestValidateAgentRecord::test_validate_agent_record_valid_record"], "newly_failing_total": 4, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_record_residual_helpers.py"], "target": "agent_workflows/agent_schema.py::validate_agent_record", "verdict": "killed", "wall_s": 5.95}
    ```
    Target 2: `agent_workflows/artifact_rename.py::_existing_type_id6s`
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "03c9e50e50e17441dd2d774788b0869c54b071d1", "mutant_failing": 2, "newly_failing": ["tests.test_record_residual_helpers.TestExistingTypeId6s::test_existing_type_id6s_collects_clustered_and_legacy_ids", "tests.test_record_residual_helpers.TestExistingTypeId6s::test_existing_type_id6s_empty_repo"], "newly_failing_total": 2, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_record_residual_helpers.py"], "target": "agent_workflows/artifact_rename.py::_existing_type_id6s", "verdict": "killed", "wall_s": 6.25}
    ```
    Target 3: `agent_workflows/doctor.py::_infer_artifact_type`
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "03c9e50e50e17441dd2d774788b0869c54b071d1", "mutant_failing": 2, "newly_failing": ["tests.test_record_residual_helpers.TestInferArtifactType::test_build_remediation_summary_fix_routes_to_inferred_type", "tests.test_record_residual_helpers.TestInferArtifactType::test_infer_artifact_type_mappings"], "newly_failing_total": 2, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_record_residual_helpers.py"], "target": "agent_workflows/doctor.py::_infer_artifact_type", "verdict": "killed", "wall_s": 5.06}
    ```
    Diff check:
    `<E-04 parent>` is `6057fe9e73b0f9b98ce13bc00ceea047cc4ddde8`.
    `git diff --stat 6057fe9e73b0f9b98ce13bc00ceea047cc4ddde8..HEAD -- agent_workflows/` is empty (no change).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract: all open questions are resolved. Scope fence: `- Scope-Paths:` (`tests/test_record_residual_helpers.py`) is a declaration, not a stop condition; if the work genuinely requires a file outside it, make the edit and justify it (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit through `aw commit v44udc -- tests/test_record_residual_helpers.py` after verifying `git diff --cached --name-only` lists only that path; never push, never `git add -A`. You MUST paste the ACTUAL runner output into every `V-*`; never claim a test passed or a mutant died that you did not run. Lifecycle: after every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
