# IPD: Add variant flag to aw oc run for forwarding model reasoning effort

- Date: 2026-09-01
- Kind: child
- Concern: The `aw oc runipd` (and `aw oc run`) driver exposes `--model` but does not expose `--variant` to forward model variant / reasoning effort (e.g. `high`, `medium`, `low`, `minimal`) to the underlying `opencode run` invocation.
- Scope: Add `--variant` to the `start` and `resume` CLI parsers in `agent_workflows/oc_runipd.py`, track `options["variant"]` in the run state, pass `["--variant", options["variant"]]` when constructing the child OpenCode process arguments in `build_launch_cmd`, and add unit test coverage in `tests/test_oc_runipd.py` and `tests/test_oc_runipd_cli.py`.
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py
- Item-Dependencies: none
- Status: executed
- Set: ocvariant
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: 429f30

## Workflow history
- 2026-09-01 executed (antigravity): finalize plan 429f30 for adding --variant to aw oc run

- 2026-09-01 draft (antigravity): created.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 approved (antigravity): human approval attested per user directive.

## Goal

Enable users to pass `--variant <effort>` (e.g. `--variant high`) to `aw oc run` / `aw oc runipd` so that model reasoning effort and variants are forwarded directly to OpenCode child turns.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Parser & State Storage

- [x] E-01 Add `--variant` argument to `start` and `resume` parsers in `agent_workflows/oc_runipd.py` and record `variant` in run options state.
  - Depends on: none
  - Expected outcome: CLI accepts `--variant` and stores it in run state options.
  - Execution state: performed

### Task group 2: Launch Command Construction

- [x] E-02 Update `build_launch_cmd` in `agent_workflows/oc_runipd.py` to append `["--variant", options["variant"]]` when `options["variant"]` is present.
  - Depends on: E-01
  - Expected outcome: `opencode run` is invoked with `--variant <value>`.
  - Execution state: performed

### Task group 3: Unit Tests & Verification

- [x] E-03 Add unit test assertions in `tests/test_oc_runipd.py` and `tests/test_oc_runipd_cli.py` verifying `--variant` argument parsing and command construction.
  - Depends on: E-01, E-02
  - Expected outcome: Full pytest suite passes cleanly.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows/oc_runipd.py`: `build_parser`, `create_run_state`, `resume_run`, and `build_launch_cmd`.
- `tests/test_oc_runipd_cli.py`: Parity tests for `aw oc runipd` / `aw opencode run`.

## Findings

- `opencode run` supports `--variant <string>` for model reasoning effort (e.g. `high`, `minimal`).
- Mirroring `--model` handling ensures identical lifecycle persistence across resumes.

## Proposed changes (ordered, validatable)

1. Add `--variant` to `build_parser` start and resume parsers (E-01).
2. Wire `variant` into `state["options"]` and `build_launch_cmd` (E-02).
3. Add unit tests for `--variant` (E-03).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_oc_runipd.py tests/test_oc_runipd_cli.py` passing.
- Full repository test suite passing bare.

## Spec / documentation sync

- N/A (CLI flag addition to driver).

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Unit test verifying `--variant` parsed and stored in state.
  - Observed evidence: Verified via `test_variant_parsing_and_launch_cmd` in `tests/test_oc_runipd.py`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Unit test verifying `build_launch_cmd` includes `--variant <val>`.
  - Observed evidence: Verified via `test_variant_parsing_and_launch_cmd` in `tests/test_oc_runipd.py` and `test_variant_flag_forwarding` in `tests/test_oc_runipd_cli.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Full repository pytest suite passes cleanly.
  - Observed evidence: `3998 passed, 3 skipped, 4 xfailed in 46.67s` and clean leak check.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
