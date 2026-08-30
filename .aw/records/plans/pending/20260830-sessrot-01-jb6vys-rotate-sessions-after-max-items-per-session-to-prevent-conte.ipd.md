# IPD: Rotate sessions after max items per session to prevent context bloat and timeouts

- Date: 2026-08-30
- Kind: child
- Concern: Non-isolated turns (such as plan reviews) within the same Set currently share an unbounded single session, leading to context window explosion (e.g. 280k tokens) and upstream API timeouts on large review batches.
- Scope: Implement `--max-items-per-session <N>` (default 4) across `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, tracking per-session turn counts in state, rotating to a fresh session when the threshold is reached, and adding comprehensive regression tests.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_session_rotation.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: approved
- Approval: human (attested by antigravity: user requested implementation)
- Set: sessrot
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: jb6vys

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored with 4-item default turn limit and symmetric driver support.
- 2026-08-30 approved (antigravity): human approval attested per user directive.

## Goal

Bound context window accumulation in multi-item runs by rotating to a fresh host session after a configurable number of non-isolated turns (default: 4 turns per session via `--max-items-per-session`), preventing upstream model timeouts while retaining local context continuity across related plans.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: OpenCode runner session rotation

- [ ] E-01 Add `--max-items-per-session` CLI argument (default: 4; 0 to disable) to `oc_runipd.py` start and resume parsers, persist it in `options`, and track `session_turn_counts` in state.
  - Depends on: none
  - Expected outcome: `state["options"]["max_items_per_session"]` defaults to 4 and persists across state saves.
  - Execution state: pending

- [ ] E-02 Update `run_opencode` and `execute_item` in `agent_workflows/oc_runipd.py` to rotate to a fresh session (`session = None`) when the active session reaches the turn threshold, and allow planned session rotations without raising unexpected session change errors.
  - Depends: E-01
  - Expected outcome: Review turns 1..4 reuse session `S1`; review turn 5 starts fresh session `S2` and sets `state["set_sessions"][setid] = S2`.
  - Execution state: pending

### Task group 2: Antigravity runner session rotation

- [ ] E-03 Implement symmetric `--max-items-per-session` option and turn counting rotation in `agent_workflows/agy_runipd.py`.
  - Depends on: E-01
  - Expected outcome: `agy_runipd.py` tracks session turn counts and drops inherited session/continue when the threshold is reached.
  - Execution state: pending

### Task group 3: Test suite coverage

- [ ] E-04 Create `tests/test_session_rotation.py` testing default rotation at 4 items, custom `--max-items-per-session 2`, disabled rotation with `--max-items-per-session 0`, state persistence, and symmetric behavior in `oc_runipd.py` and `agy_runipd.py`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: All tests pass with full branch coverage on session rotation logic.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `state["set_sessions"]`: maps Set IDs to persistent session IDs for non-isolated turns.
- `state["options"]`: stores runner options and CLI flag overrides.
- Symmetry requirement: `test_lane_session_isolation.py` enforces that session isolation rules in `oc_runipd` and `agy_runipd` remain symmetric.

## Findings

- During large review batches (e.g. 4+ plan reviews in one Set), context window grows linearly and exceeded 280k tokens, triggering upstream 10-minute LLM inference timeouts.
- Rotating sessions after 4 turns bounds token usage to manageable levels while preserving helpful context across adjacent plans.

## Proposed changes (ordered, validatable)

1. Add CLI options and state initialization in `oc_runipd.py` (E-01).
2. Implement turn threshold check and rotation in `oc_runipd.py` (E-02).
3. Implement turn threshold check and rotation in `agy_runipd.py` (E-03).
4. Add comprehensive test suite in `tests/test_session_rotation.py` (E-04).

## Deferred / out of scope (with reason)

- **Isolated worktree execution turns**: Isolated worktree turns already get a fresh session for every single item; this rotation logic applies to non-isolated turns (such as plan reviews).

## Scope check

- Over-scope: none. Strictly implements session turn counting and rotation.
- Under-scope: none. Implemented symmetrically in both `oc_runipd` and `agy_runipd`.

## Required tests / validation

- `python3 -m pytest tests/test_session_rotation.py` passing.
- `python3 -m pytest tests/test_lane_session_isolation.py` passing.
- `python3 -m pytest tests/test_oc_runipd.py` passing.

## Spec / documentation sync

- Updates CLI help text for `aw oc run` and `aw agy run`.

## Open questions

### OQ-01: Does rotating a session discard the worktree or plan files?

- Blocking: no
- Status: resolved
- Owner: resolved from architecture
- Resolution or deferral rationale: RESOLVED - No. Plan reviews edit files on disk; the fresh session loads the current on-disk state via prompt and file injection without losing any repository progress.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Python test showing `max_items_per_session` parsed and stored in state options with default 4.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test simulating 6 review turns in `oc_runipd` verifying rotation at item 5 without `DriverError`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test simulating review turns in `agy_runipd` verifying rotation at the threshold.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `pytest tests/test_session_rotation.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
