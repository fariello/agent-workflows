# IPD: Restore behavioral coverage of the agy_runipd skip-permissions default (True) end to end

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_lane_permission_posture.py`, and with it `TestAntigravitySkipPermissionsDefaultIsPinned`, the only behavioral guard that `agy_runipd.build_parser()` defaults `dangerously_skip_permissions` to True (spec R4.1c, a decided maintainer constraint: running agy without `--dangerously-skip-permissions` was measured to deadlock unattended turns). Executed plan `9rthek` recorded site S-14 (`agy_runipd.run_agy_turn` comment) as RETIRE-UNGUARDED. A silent flip of the default would make every unattended agy turn hang on an interactive permission prompt nobody answers.
- Scope: Add one new behavioral test module asserting the default on the real parser, its propagation through `initialize_run` into frozen run options, and its effect on the real `run_agy_turn` argv (with `subprocess.Popen` faked); then repoint the S-14 comment in `agy_runipd.run_agy_turn` at the new module. No production behavior change.
- Scope-Paths: tests/test_agy_skip_permissions_default.py, agent_workflows/agy_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: m7o4ew
- Set: m7o4ew
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: ba6z1a

## Workflow history

- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog `m7o4ew`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) coverage that the Antigravity driver's skip-permissions option defaults to True and that this default actually reaches the `agy` command line, so a later "hardening" flip fails loudly instead of deadlocking unattended runs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: parser default

- [ ] E-01 Create `tests/test_agy_skip_permissions_default.py` with a test class that calls the real `agy_runipd.build_parser().parse_args(["start", "someid"])` and asserts `args.dangerously_skip_permissions is True`; that `["start", "someid", "--no-dangerously-skip-permissions"]` yields `False`; and that both the `--dangerously-skip-permissions` and `--dangerous` spellings yield `True`. The failure message must state that R4.1c forbids flipping the default without its own decision.
  - Depends on: none
  - Expected outcome: Parser-default class passes; the opt-out flag is shown to be the only way to get False.
  - Execution state: pending

### Task group 2: the default reaches the agy command line

- [ ] E-02 In the same module, add a test that drives the real `agy_runipd.run_agy_turn` with a temp run dir (same fixture shape as `tests/test_turn_bounds.py` `_setup_launcher_run_dir`, `state["options"]["agy"] = sys.executable`) and `subprocess.Popen` patched to a recording fake process (pattern from `tests/test_turn_bounds.py` `test_launcher_uniform_arming_antigravity`), and asserts: with options that OMIT `dangerously_skip_permissions` the captured argv contains `--dangerously-skip-permissions`; with `dangerously_skip_permissions: True` it contains it; with `False` it does not.
  - Depends on: E-01
  - Expected outcome: Argv test passes, proving the absent-key default is also True at the launch site (`options.get("dangerously_skip_permissions", True)`).
  - Execution state: pending

- [ ] E-03 In the same module, add a test that the parser default survives run initialization: parse `["start", <selector>, "--prepare-only"]` (plus `--repo` pointing at a temp git repo holding one approved child plan, as existing `initialize_run` tests such as `tests/test_orchestrator_retirement.py` build) with the real `agy_runipd.build_parser()`, call the real `agy_runipd.initialize_run(args)`, read the written `state.json`, and assert `state["options"]["dangerously_skip_permissions"] is True`. If constructing a real run in a temp repo proves infeasible for `initialize_run` without network or host binaries, record the reason in the plan and cover the freeze step by passing an `argparse.Namespace` lacking the attribute instead, asserting the frozen option is still True.
  - Depends on: E-01
  - Expected outcome: The frozen run option is True when the operator passes no flag.
  - Execution state: pending

### Task group 3: comment repointing

- [ ] E-04 Repoint the S-14 comment in `agy_runipd.run_agy_turn` (the block beginning "NO PERMISSION POLICY DOCUMENT IS SUPPLIED HERE" whose text reads "`tests/test_lane_permission_posture.py` was deleted in `19313eed`; no live guard currently asserts this default") so it names `tests/test_agy_skip_permissions_default.py` as the live guard, keeping the "Do NOT \"harden\" it" instruction and its R4.1c reason. Comment-only edit.
  - Depends on: E-02
  - Expected outcome: `rg -n "no live guard currently asserts this default" agent_workflows/agy_runipd.py` returns no matches; no statement change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior (P16, AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); no `inspect`, `ast`, or reading `.py` source.
- The deleted guard was `TestAntigravitySkipPermissionsDefaultIsPinned` in `git show 19313eed^:tests/test_lane_permission_posture.py`. Its `test_options_default_to_true_when_the_attribute_is_absent` only tested `getattr` on an empty `argparse.Namespace` (vacuous; it never exercised driver code) and `test_this_plan_did_not_change_the_default` pinned `DEFAULT_TIMEOUT`, unrelated to this property; E-02/E-03 replace the former with real driver calls and the latter is not restored.
- The option is declared in `agy_runipd.build_parser` on the `start` subparser (`dest="dangerously_skip_permissions"`, `default=True`, opt-out `--no-dangerously-skip-permissions`), frozen in `agy_runipd.initialize_run` (`getattr(args, "dangerously_skip_permissions", True)`), and consumed in `agy_runipd.run_agy_turn` (`if options.get("dangerously_skip_permissions", True): argv.append("--dangerously-skip-permissions")`).
- `tests/test_agy_run.py` covers the lower-level `agy_run.run_agy(skip_permissions=True)` argv only, not the `agy_runipd` default; `rg -n dangerously_skip_permissions tests/` returns no matches.
- Suite is run bare: `python3 -m pytest`.

## Findings

| Site | Lost test | Live coverage today |
|---|---|---|
| 9rthek S-14 (`agy_runipd.run_agy_turn` comment) | `TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser` | None for the `agy_runipd` default; only `agy_run.run_agy` explicit `skip_permissions=True` argv in `tests/test_agy_run.py`. |

## Proposed changes (ordered, validatable)

1. New `tests/test_agy_skip_permissions_default.py` (E-01..E-03).
2. Comment repoint in `agent_workflows/agy_runipd.py` (E-04).

## Deferred / out of scope (with reason)

- Restoring `test_this_plan_did_not_change_the_default` (`DEFAULT_TIMEOUT == "240m"`): a different property, not named by backlog `m7o4ew`.
- Any change to the default itself: forbidden by R4.1c.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; the one cited site (S-14) gets a behavioral guard at parser, freeze, and launch layers.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py` passes.
- Non-vacuity: in a scratch uncommitted edit set `default=False` on the `--dangerously-skip-permissions` argument in `agy_runipd.build_parser` and change the `run_agy_turn` fallback to `options.get("dangerously_skip_permissions", False)`; the E-01, E-02 (absent-key case) and E-03 tests fail; revert and show `git diff --stat agent_workflows/agy_runipd.py` empty apart from the E-04 comment.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus a comment repoint; the governing spec (R4.1c) is unchanged.

## Open questions

### OQ-01: Should the vacuous `getattr`-on-empty-Namespace test be restored verbatim?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. It exercised no driver code; E-02 (absent option key at `run_agy_turn`) and E-03 (freeze through `initialize_run`) test the same intent behaviorally. Backlog `m7o4ew` permits only behavioral outcomes (P16).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_agy_skip_permissions_default.py -k Parser` showing the parser tests passing; plus pasted output of the scratch non-vacuity run (`default=False`) showing the default test FAIL.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the argv tests passing; the observed argv is produced by `agy_runipd.run_agy_turn` (captured by the fake `Popen` created in E-02); plus pasted scratch non-vacuity output (fallback `False`) showing the absent-key case FAIL.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the freeze test passing, with the frozen option read from the `state.json` written by `agy_runipd.initialize_run` (or, if the documented fallback was taken, the recorded infeasibility reason and the Namespace-based test passing); plus scratch non-vacuity output showing it FAIL.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `git diff agent_workflows/agy_runipd.py` showing only comment lines changed and naming `tests/test_agy_skip_permissions_default.py`; pasted `rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_agy_skip_permissions_default.py` returning no matches; pasted bare `python3 -m pytest` summary line showing the full suite passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit <plan> -- <paths>`; never push. After every `V-*` item records pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle (`aw ipd finalize`).
