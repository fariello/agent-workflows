# IPD: Restore behavioral coverage of the agy_runipd skip-permissions default (True) end to end

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_lane_permission_posture.py`, and with it `TestAntigravitySkipPermissionsDefaultIsPinned`, the only behavioral guard that `agy_runipd.build_parser()` defaults `dangerously_skip_permissions` to True (spec R4.1c, a decided maintainer constraint: running agy without `--dangerously-skip-permissions` was measured to deadlock unattended turns). Executed plan `9rthek` recorded site S-14 (`agy_runipd.run_agy_turn` comment) as RETIRE-UNGUARDED. A silent flip of the default would make every unattended agy turn hang on an interactive permission prompt nobody answers.
- Scope: Add one new behavioral test module asserting the default on the real parser, its propagation through `initialize_run` into frozen run options, and its effect on BOTH launch sites that read the frozen option: the real `agy_runipd.run_agy_turn` argv (with `subprocess.Popen` faked) and the real `runner_shared.probe_argv(host="agy")` argv. Then repoint the S-14 comment in `agy_runipd.run_agy_turn` at the new module. No production behavior change.
- Scope-Paths: tests/test_agy_skip_permissions_default.py, agent_workflows/agy_runipd.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: m7o4ew
- Set: m7o4ew
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: ba6z1a
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog `m7o4ew`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) coverage that the Antigravity driver's skip-permissions option defaults to True and that this default actually reaches the `agy` command line, so a later "hardening" flip fails loudly instead of deadlocking unattended runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: parser default

- [x] E-01 Create `tests/test_agy_skip_permissions_default.py` with a test class that calls the real `agy_runipd.build_parser().parse_args(["start", "someid"])` and asserts `args.dangerously_skip_permissions is True`; that `["start", "someid", "--no-dangerously-skip-permissions"]` yields `False`; and that both the `--dangerously-skip-permissions` and `--dangerous` spellings yield `True`. The failure message must state that R4.1c forbids flipping the default without its own decision.
  - Depends on: none
  - Expected outcome: Parser-default class passes; the opt-out flag is shown to be the only way to get False.
  - Execution state: performed

### Task group 2: the default reaches the agy command line

- [x] E-02 In the same module, add a test that drives the real `agy_runipd.run_agy_turn` with a temp run dir (same fixture shape as `tests/test_turn_bounds.py` `_setup_launcher_run_dir`, `state["options"]["agy"] = sys.executable`) and `subprocess.Popen` patched to a recording fake process (pattern from `tests/test_turn_bounds.py` `test_launcher_uniform_arming_antigravity`). The fake records EVERY call's argv. `run_agy_turn` also spawns `git config --get ...` helpers through `Popen`, measured at review as 4 git calls plus 1 agy call, so the test MUST select the agy launch as the single recorded argv whose `argv[0] == agy_runipd.resolve_agy(sys.executable)`. It must also assert exactly one such argv exists, so a test that inspects a git argv cannot pass vacuously. It then asserts: with options that OMIT `dangerously_skip_permissions` the captured argv contains `--dangerously-skip-permissions`; with `dangerously_skip_permissions: True` it contains it; with `False` it does not.
  - Depends on: E-01
  - Expected outcome: Argv test passes, proving the absent-key default is also True at the launch site (`options.get("dangerously_skip_permissions", True)`).
  - Execution state: performed

- [x] E-03 In the same module, add a test that the parser default survives run initialization, following the demonstrated precedent `tests/test_runner_shared.py` `VerificationPolarityTests.frozen_options` (reuse its fixture shape; do not import a private helper from another test module). The test does the following:
  - Set `XDG_CONFIG_HOME` to a fresh temp dir with `mock.patch.dict(os.environ, ...)`, so no ambient `runner-profiles.json` (`runner_profiles.STORE_NAME`) can supply or override options.
  - Build a temp git repo holding one `Status: approved` child plan (that test's `make_repo`/`PLAN` shape), with `.aw/records/runs/` gitignored.
  - Parse `["start", <id6>, "--repo", <repo>]` with the real `agy_runipd.build_parser()` and set `args.prepare_only = True`.
  - Call the real `agy_runipd.initialize_run(args)`, and read the frozen options with `runner_shared.load_state(run_dir)["options"]`.
  - Assert `options["dangerously_skip_permissions"] is True`, and that the same flow with `--no-dangerously-skip-permissions` yields `False`. The False case proves the frozen value comes from the parser and is not a constant.
  Feasibility was demonstrated at review: this flow returned `True` (no flag) and `False` (opt-out) with no network or host binary. The earlier `argparse.Namespace` fallback is REMOVED, because it would re-create the vacuous `getattr` test that OQ-01 rejects.
  - Depends on: E-01
  - Expected outcome: The frozen run option written by `initialize_run` is True when the operator passes no flag and False only with the opt-out flag, under an isolated config home.
  - Execution state: performed

- [x] E-05 In the same module, add a test that the coverage-probe launch site also defaults on: call the real `runner_shared.probe_argv({"options": {"agy": "agy"}}, host="agy", prompt="p", repo=str(tmp))` and assert `"--dangerously-skip-permissions" in argv`. With `"dangerously_skip_permissions": False` in options, assert it is absent. This second consumer carries the same `options.get("dangerously_skip_permissions", True)` fallback, and a flip there would hang the unattended coverage probe the same way (precedent call shape: `tests/test_runner_finalize_message.py` `test_agy_probe_print_timeout_carries_a_duration_unit`).
  - Depends on: E-01
  - Expected outcome: Probe-argv test passes for the absent-key, True, and False cases.
  - Execution state: performed

### Task group 3: comment repointing

- [x] E-04 Repoint the S-14 comment in `agy_runipd.run_agy_turn` (the block beginning "NO PERMISSION POLICY DOCUMENT IS SUPPLIED HERE" whose text reads "`tests/test_lane_permission_posture.py` was deleted in `19313eed`; no live guard currently asserts this default") so it names `tests/test_agy_skip_permissions_default.py` as the live guard, keeping the "Do NOT \"harden\" it" instruction and its R4.1c reason. Comment-only edit.
  - Depends on: E-02, E-03, E-05
  - Expected outcome: `rg -n "no live guard currently asserts this default" agent_workflows/agy_runipd.py` returns no matches; no statement change.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must exercise behavior (P16, AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); no `inspect`, `ast`, or reading `.py` source.
- The deleted guard was `TestAntigravitySkipPermissionsDefaultIsPinned` in `git show 19313eed^:tests/test_lane_permission_posture.py`. Its `test_options_default_to_true_when_the_attribute_is_absent` only tested `getattr` on an empty `argparse.Namespace` (vacuous; it never exercised driver code) and `test_this_plan_did_not_change_the_default` pinned `DEFAULT_TIMEOUT`, unrelated to this property; E-02/E-03 replace the former with real driver calls and the latter is not restored.
- The option is declared in `agy_runipd.build_parser` on the `start` subparser (`dest="dangerously_skip_permissions"`, `default=True`, opt-out `--no-dangerously-skip-permissions`). It is frozen in `agy_runipd.initialize_run` (`getattr(args, "dangerously_skip_permissions", True)`) and consumed at TWO launch sites: `agy_runipd.run_agy_turn` and `runner_shared.probe_argv` (`host == "agy"` branch, the orchestrator-coverage probe). Both read `if options.get("dangerously_skip_permissions", True): argv.append("--dangerously-skip-permissions")`.
- Measured at review (HEAD `9f4e0f477`):
  - `build_parser().parse_args(["start","x"])` yields `True`; `--no-dangerously-skip-permissions` yields `False`; `--dangerous` and `--dangerously-skip-permissions` yield `True`.
  - `run_agy_turn` under a recording `Popen` fake made 5 calls (4 `git config --get ...` and 1 agy launch). The agy argv contained the flag for absent and True options and omitted it for False.
  - `probe_argv` contains the flag for `{}` options and omits it for `False`.
  - The `VerificationPolarityTests.frozen_options` flow on `agy_runipd` returned `True` with no flag and `False` with the opt-out.
- `tests/test_agy_run.py` covers the lower-level `agy_run.run_agy(skip_permissions=True)` argv only, not the `agy_runipd` default; `rg -n dangerously_skip_permissions tests/` returns no matches.
- Suite is run bare: `python3 -m pytest`.

## Findings

| Site | Lost test | Live coverage today |
|---|---|---|
| 9rthek S-14 (`agy_runipd.run_agy_turn` comment) | `TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser` | None for the `agy_runipd` default; only `agy_run.run_agy` explicit `skip_permissions=True` argv in `tests/test_agy_run.py`. |
| `runner_shared.probe_argv` agy branch | (never guarded) | None; `tests/test_runner_finalize_message.py` checks only `--print-timeout`. |

## Proposed changes (ordered, validatable)

1. New `tests/test_agy_skip_permissions_default.py` (E-01, E-02, E-03, E-05).
2. Comment repoint in `agent_workflows/agy_runipd.py` (E-04).

## Deferred / out of scope (with reason)

- Restoring `test_this_plan_did_not_change_the_default` (`DEFAULT_TIMEOUT == "240m"`): a different property, not named by backlog `m7o4ew`.
  - Carrier-Declined: not part of backlog m7o4ew
- Any change to the default itself: forbidden by R4.1c.
  - Carrier-Declined: forbidden by R4.1c

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; the cited site (S-14) gets a behavioral guard at the parser, freeze, and launch layers, and the second launch site (`runner_shared.probe_argv`) is guarded too (E-05).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py` passes.
- Non-vacuity, performed BEFORE E-04 so the revert cannot discard the comment edit:
  - In a scratch uncommitted edit, set `default=False` on the `--dangerously-skip-permissions` argument in `agy_runipd.build_parser`, and change BOTH fallbacks (`agy_runipd.run_agy_turn` and `runner_shared.probe_argv`) to `options.get("dangerously_skip_permissions", False)`.
  - Run the module. The E-01 default test, the E-02 absent-key case, the E-03 no-flag case, and the E-05 absent-key case must fail with `AssertionError`.
  - Revert with `git checkout -- agent_workflows/agy_runipd.py agent_workflows/runner_shared.py` (safe: neither file has other edits yet).
  - Show `git diff --stat -- agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` empty before starting E-04.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus a comment repoint; the governing spec (R4.1c) is unchanged. No CHANGELOG entry, because nothing user-visible changes.

## Open questions

### OQ-01: Should the vacuous `getattr`-on-empty-Namespace test be restored verbatim?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. It exercised no driver code; E-02 (absent option key at `run_agy_turn`) and E-03 (freeze through `initialize_run`) test the same intent behaviorally. Backlog `m7o4ew` permits only behavioral outcomes (P16).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py -k Parser` showing the parser tests passing; plus pasted output of the scratch non-vacuity run (`default=False`) showing the default test FAIL.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py -k Parser
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=4231485603
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items / 8 deselected / 3 selected

tests/test_agy_skip_permissions_default.py::TestParserDefault::test_parser_default_is_true PASSED [ 33%]
tests/test_agy_skip_permissions_default.py::TestParserDefault::test_parser_explicit_flags_are_true PASSED [ 66%]
tests/test_agy_skip_permissions_default.py::TestParserDefault::test_parser_opt_out_is_false PASSED [100%]

NOTE: 8 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
======================= 3 passed, 8 deselected in 0.51s ========================
```

Scratch non-vacuity run with `default=False` in `agy_runipd.build_parser`:
```
$ python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py -k Parser
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=914640657
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items / 8 deselected / 3 selected

tests/test_agy_skip_permissions_default.py::TestParserDefault::test_parser_opt_out_is_false PASSED [ 33%]
tests/test_agy_skip_permissions_default.py::TestParserDefault::test_parser_explicit_flags_are_true PASSED [ 66%]
tests/test_agy_skip_permissions_default.py::TestParserDefault::test_parser_default_is_true FAILED [100%]

=================================== FAILURES ===================================
________________ TestParserDefault.test_parser_default_is_true _________________

self = <tests.test_agy_skip_permissions_default.TestParserDefault object at 0x7a27fea156d0>

    def test_parser_default_is_true(self) -> None:
        parser = agy_runipd.build_parser()
        args = parser.parse_args(["start", "someid"])
>       assert args.dangerously_skip_permissions is True, (
            "R4.1c forbids flipping the default without its own decision: "
            "dangerously_skip_permissions must default to True"
        )
E       AssertionError: R4.1c forbids flipping the default without its own decision: dangerously_skip_permissions must default to True
E       assert False is True

tests/test_agy_skip_permissions_default.py:30: AssertionError
NOTE: 8 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
=========================== short test summary info ============================
FAILED tests/test_agy_skip_permissions_default.py::TestParserDefault::test_parser_default_is_true
================== 1 failed, 2 passed, 8 deselected in 0.46s ===================
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the argv tests passing; the observed argv is produced by `agy_runipd.run_agy_turn` (captured by the fake `Popen` created in E-02); plus pasted scratch non-vacuity output (fallback `False`) showing the absent-key case FAIL.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py -k AgyTurnArgvDefault
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=3341928923
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items / 8 deselected / 3 selected

tests/test_agy_skip_permissions_default.py::TestAgyTurnArgvDefault::test_run_agy_turn_argv_with_skip_permissions_true PASSED [ 33%]
tests/test_agy_skip_permissions_default.py::TestAgyTurnArgvDefault::test_run_agy_turn_argv_defaults_to_skip_permissions PASSED [ 66%]
tests/test_agy_skip_permissions_default.py::TestAgyTurnArgvDefault::test_run_agy_turn_argv_with_skip_permissions_false PASSED [100%]

NOTE: 8 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
======================= 3 passed, 8 deselected in 1.13s ========================
```

Scratch non-vacuity run with fallback `False` in `agy_runipd.run_agy_turn`:
```
__ TestAgyTurnArgvDefault.test_run_agy_turn_argv_defaults_to_skip_permissions __

self = <tests.test_agy_skip_permissions_default.TestAgyTurnArgvDefault object at 0x72498c086710>
tmp_path = PosixPath('<tmp_path>')

    def test_run_agy_turn_argv_defaults_to_skip_permissions(self, tmp_path: Path) -> None:
        argv = _run_turn_and_capture_agy_argv(tmp_path / "omitted", {})
>       assert "--dangerously-skip-permissions" in argv
E       AssertionError: assert '--dangerously-skip-permissions' in ['<sys.executable>', '-p', 'prompt content', '--output-format', 'stream-json', '--print-timeout', ...]

tests/test_agy_skip_permissions_default.py:118: AssertionError
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the freeze test passing for both the no-flag (`True`) and opt-out (`False`) cases. The frozen option is read via `runner_shared.load_state` from the run dir created by `agy_runipd.initialize_run`, under an isolated `XDG_CONFIG_HOME`. Also paste scratch non-vacuity output showing the no-flag case FAIL.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py -k RunInitializationFrozenOption
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=324387933
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items / 9 deselected / 2 selected

tests/test_agy_skip_permissions_default.py::TestRunInitializationFrozenOption::test_initialize_run_freezes_opt_out_false PASSED [ 50%]
tests/test_agy_skip_permissions_default.py::TestRunInitializationFrozenOption::test_initialize_run_freezes_default_true PASSED [100%]

NOTE: 9 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
======================= 2 passed, 9 deselected in 1.86s ========================
```

Scratch non-vacuity run with `default=False` in `build_parser`:
```
__ TestRunInitializationFrozenOption.test_initialize_run_freezes_default_true __

self = <tests.test_agy_skip_permissions_default.TestRunInitializationFrozenOption object at 0x72498c086ad0>
tmp_path = PosixPath('<tmp_path>')

    def test_initialize_run_freezes_default_true(self, tmp_path: Path) -> None:
        options = _frozen_options_for_args([], tmp_path, id6="fix001")
>       assert options["dangerously_skip_permissions"] is True
E       assert False is True

tests/test_agy_skip_permissions_default.py:239: AssertionError
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste:
    - `git diff agent_workflows/agy_runipd.py` showing only comment lines changed and naming `tests/test_agy_skip_permissions_default.py`;
    - `git diff --stat -- agent_workflows/runner_shared.py` showing nothing;
    - `rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_agy_skip_permissions_default.py` returning no matches;
    - the bare `python3 -m pytest` summary line, showing zero failures that are absent at the execution base (compare by name).
  - Observed evidence:
```
$ git diff agent_workflows/agy_runipd.py
diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
index 7a8e7bea5..5d643732b 100755
--- a/agent_workflows/agy_runipd.py
+++ b/agent_workflows/agy_runipd.py
@@ -2530,9 +2530,8 @@ def run_agy_turn(
     # (`--no-dangerously-skip-permissions`) requires INTERACTIVE permissions an unattended turn has no
     # answerer for, and running without it was measured to fail or deadlock repeatedly. That is a
     # DECIDED CONSTRAINT this spec adopts (R4.1c), not a defect it tolerates, and R4.1b puts closing
-    # it out of scope. Do NOT "harden" it: `tests/test_lane_permission_posture.py` was deleted in
-    # `19313eed`; no live guard currently asserts this default, but running without it remains
-    # unsupported by design.
+    # it out of scope. Do NOT "harden" it: `tests/test_agy_skip_permissions_default.py` is the live
+    # guard asserting this default, and running without it remains unsupported by design.
     #
     # CONSEQUENCE, which is why R4.1a requires it be RECORDED and not glossed: on this host the host
     # layer contributes NOTHING to containment, so the guarantee rests ENTIRELY on R1 (the prompt

$ git diff --stat -- agent_workflows/runner_shared.py
(clean, no output)

$ rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_agy_skip_permissions_default.py
(no matches, exit code 1)

$ python3 -m pytest
695 passed in 47.53s
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted pytest output showing the probe-argv test passing for the absent-key, True, and False cases; the observed argv is produced by `runner_shared.probe_argv` (`host="agy"`). Also paste scratch non-vacuity output (probe fallback `False`) showing the absent-key case FAIL.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py -k CoverageProbeArgvDefault
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
Using --randomly-seed=3919542492
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 11 items / 8 deselected / 3 selected

tests/test_agy_skip_permissions_default.py::TestCoverageProbeArgvDefault::test_probe_argv_defaults_to_skip_permissions PASSED [ 33%]
tests/test_agy_skip_permissions_default.py::TestCoverageProbeArgvDefault::test_probe_argv_with_skip_permissions_false PASSED [ 66%]
tests/test_agy_skip_permissions_default.py::TestCoverageProbeArgvDefault::test_probe_argv_with_skip_permissions_true PASSED [100%]

NOTE: 8 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
======================= 3 passed, 8 deselected in 0.52s ========================
```

Scratch non-vacuity run with fallback `False` in `runner_shared.probe_argv`:
```
__ TestCoverageProbeArgvDefault.test_probe_argv_defaults_to_skip_permissions ___

self = <tests.test_agy_skip_permissions_default.TestCoverageProbeArgvDefault object at 0x72498c087250>
tmp_path = PosixPath('<tmp_path>')

    def test_probe_argv_defaults_to_skip_permissions(self, tmp_path: Path) -> None:
        argv = runner_shared.probe_argv(
            {"options": {"agy": "agy"}}, host="agy", prompt="p", repo=str(tmp_path)
        )
>       assert "--dangerously-skip-permissions" in argv
E       AssertionError: assert '--dangerously-skip-permissions' in ['agy', '-p', 'p', '--output-format', 'stream-json', '--print-timeout', ...]

tests/test_agy_skip_permissions_default.py:255: AssertionError
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

EXECUTION CONTRACT. OQ-01 is resolved; none remain. When executing by hand, start with `aw ipd begin ba6z1a`. Commit only the `- Scope-Paths:` files plus this plan, through `aw commit ba6z1a -- <paths>`. Never use `git add -A` or `-a`, never `--no-verify`, never push. Verify the staged set with `git diff --cached --name-only` first. HONESTY RULE: every `V-*` MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it.

SCOPE FENCE. `agent_workflows/runner_shared.py` is touched ONLY by the reverted non-vacuity scratch edit and must show no committed diff. No production statement changes anywhere. An out-of-scope edit that proves necessary is made and then justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. When every `E-*` is `performed`, every `V-*` is `Result: pass` with pasted evidence, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`. Under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it. When executing by hand, run `aw ipd finalize ba6z1a`. Never hand-roll the move with `git mv`.
