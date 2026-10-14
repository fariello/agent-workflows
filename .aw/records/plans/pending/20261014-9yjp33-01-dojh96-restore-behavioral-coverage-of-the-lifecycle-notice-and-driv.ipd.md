# IPD: Restore behavioral coverage of the lifecycle notice and driver prompt pure-ASCII invariant

- Date: 2026-10-14
- Kind: child
- Concern: The pure-ASCII invariant of the driver execution and verifier prompts, and of the `ipd_lifecycle.runner_owns_lifecycle_notice` block they embed, has had no live behavioral guard since `tests/test_reporting_contract.py` (including `DriverPromptTests::test_prompts_are_pure_ascii`) was deleted in `19313eed`.
- Scope: Add one new behavioral test module that renders the real execution, recovery, and verifier prompts through both host drivers (`oc_runipd`, `agy_runipd`) under both `self_finalize` settings, and the notice itself, and asserts on the rendered text: every string is pure ASCII and every prompt embeds the exact notice for its run's ownership mode. No production code change.
- Scope-Paths: tests/test_driver_prompt_ascii.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 9yjp33
- Set: 9yjp33
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: dojh96

## Workflow history

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored review-ready from backlog `9yjp33`.

## Goal

Restore an outcome-only (P16-compliant) test proving that the prompts both drivers hand an agent, and the lifecycle-ownership notice inside them, contain no non-ASCII character, with a non-vacuity check that the notice is actually embedded, so introducing a non-ASCII character into `runner_owns_lifecycle_notice` or a prompt composer fails the suite again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Author the behavioral test module

- [ ] E-01 Create `tests/test_driver_prompt_ascii.py` with test `test_lifecycle_notice_is_pure_ascii_in_both_modes`: call `ipd_lifecycle.runner_owns_lifecycle_notice` for `driver_owns_transition` in (True, False) and `run_id` in (None, `"run-20260101T000000Z-1"`), assert each result is non-empty and that the set of characters with `ord(c) > 127` is empty (report the offending characters in the failure message).
  - Depends on: none
  - Expected outcome: The test exists and passes against the current notice text.
  - Execution state: pending
- [ ] E-02 Add test `test_driver_prompts_are_pure_ascii`: for each module in (`oc_runipd`, `agy_runipd`), each `self_finalize` in (True, False) placed in `state["options"]`, render `build_prompt(item, state, run_dir, plan_path, False)`, `build_prompt(..., True)` (recovery), and `build_verifier_prompt(item, state, run_dir, plan_path)` with `item = {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}`, `run_dir` and `plan_path` under pytest `tmp_path`; assert no character `ord(c) > 127` in each rendered prompt, labelled per module/mode/surface via `subTest`.
  - Depends on: E-01
  - Expected outcome: All 12 renderings pass against current code (measured during authoring: every rendering returned an empty non-ASCII set).
  - Execution state: pending
- [ ] E-03 Add test `test_driver_prompts_embed_the_notice_for_their_mode`: on the same 12 renderings, assert `runner_owns_lifecycle_notice(self_finalize, run_id=state["run_id"])` is a substring of the prompt, and that the opposite mode's notice is NOT a substring, so the ASCII check in E-02 provably covers the notice text and the conditional ownership statement reaches the agent.
  - Depends on: E-02
  - Expected outcome: The test passes against current code (measured during authoring: the matching notice was present in all 12 renderings).
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): tests must call the code and assert on real outputs; no `inspect`/`ast`/regex over source. The backlog item restates it ("only behavioral outcomes may be restored, never a source-reading pin").
- Both host drivers delegate to one composer: `oc_runipd.build_prompt` / `agy_runipd.build_prompt` call `runner_shared.build_prompt` with host labels, and `build_verifier_prompt` calls `runner_shared.build_verifier_prompt`; each composer calls `ipd_lifecycle.runner_owns_lifecycle_notice(bool(state.get("options", {}).get("self_finalize", True)), run_id=...)`. Testing through both host modules covers both label sets.
- The suite runs bare as `python3 -m pytest` (`pyproject.toml` `addopts` supplies `-q -n auto`); narrowed runs with per-test detail use `-o addopts=""`.
- Existing coverage: `tests/test_lifecycle_holder_gate.py::...test_no_self_finalize_delegated_agent_turn_succeeds` asserts notice CONTENT (`--run-id`, "The runner performs `aw ipd begin`") but neither ASCII-ness nor embedding in the prompts; this plan does not duplicate those content assertions.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The `runner_owns_lifecycle_notice` docstring states the prompts embedding it "were asserted pure ASCII by `tests/test_reporting_contract.py::DriverPromptTests::test_prompts_are_pure_ascii` (deleted in `19313eed`; no live guard currently asserts this)". | `agent_workflows/ipd_lifecycle.py`, `runner_owns_lifecycle_notice` docstring, "Pure and ASCII-only" paragraph |
| F-02 | Plan `ev7t1w` site S-14 classified this as `RETIRE-UNGUARDED`, and `rg -n "pure_ascii" tests/` returns empty. | `.aw/records/plans/*/20261011-iosmvn-03-ev7t1w-*.ipd.md` row S-14 |
| F-03 | The deleted test rendered `mod.build_prompt(item, state, Path("/tmp/run-dir"), Path("/tmp/repo/plan.ipd.md"), False)` and `mod.build_verifier_prompt(...)` for `(oc_runipd, agy_runipd)` and asserted `sorted({c for c in prompt if ord(c) > 127}) == []`: purely behavioral, so it may be restored as-is in spirit. | `git show 19313eed7^:tests/test_reporting_contract.py`, class `DriverPromptTests` |
| F-04 | The deleted test's `_state()` carried no `options`, so it exercised only the default `self_finalize=True` notice; the delegated (`--no-self-finalize`) notice, which interpolates `run_id`, was never covered. E-02/E-03 cover both. | Same source; `runner_owns_lifecycle_notice` `if not driver_owns_transition` branch |
| F-05 | The invariant holds today: an authoring-time render of all 12 combinations returned an empty non-ASCII set and contained the matching notice. | Authoring probe output: every line `[] True` |

## Proposed changes (ordered, validatable)

1. New file `tests/test_driver_prompt_ascii.py` with the notice ASCII test (E-01).
2. The 12-rendering prompt ASCII test (E-02).
3. The notice-embedding non-vacuity test (E-03).

## Deferred / out of scope (with reason)

- The other deleted `DriverPromptTests` cases (reporting-contract embedding, required JSON keys, review prompt shape): not named by backlog `9yjp33`; any gap belongs to its own item.
- Updating the stale "no live guard currently asserts this" sentence in the `runner_owns_lifecycle_notice` docstring: `agent_workflows/ipd_lifecycle.py` is outside Scope-Paths (see OQ-01).

## Scope check

- Over-scope: none.
- Under-scope: none; falsifiability of the restored guard is demonstrated in V-01 and V-02 by a temporary local mutation that is reverted and never committed.

## Required tests / validation

- `python3 -m pytest tests/test_driver_prompt_ascii.py -o addopts="" -v` passes (all three tests).
- Mutation check: temporarily insert a non-ASCII character (for example U+2014) into the `driver_owns_transition=True` return string of `runner_owns_lifecycle_notice`, rerun the module, observe `test_lifecycle_notice_is_pure_ascii_in_both_modes` and `test_driver_prompts_are_pure_ascii` FAIL, then `git checkout -- agent_workflows/ipd_lifecycle.py` and confirm `git diff --name-only agent_workflows/` is empty.
- Full suite `python3 -m pytest` passes bare.
- The new file reads no production source (no `inspect`, `ast`, or `read_text` of `agent_workflows/`).

## Spec / documentation sync

N/A: no behavior or contract change; this plan adds a test only, and no spec describes the prompts' test coverage.

## Open questions

### OQ-01: Should the stale "no live guard" docstring sentence in `runner_owns_lifecycle_notice` be repointed at the new test?

- Blocking: no
- Status: deferred
- Owner: maintainer (trigger: next edit of agent_workflows/ipd_lifecycle.py)
- Resolution or deferral rationale: Deferred. Editing `agent_workflows/ipd_lifecycle.py` widens a test-only change into production code, and the sentence remains accurate history ("deleted in `19313eed`"); the sibling restoration plan `k6twdf` (backlog `081smx`) made the same call for `pwatch.main`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted actual output of `python3 -m pytest tests/test_driver_prompt_ascii.py -o addopts="" -v` showing `test_lifecycle_notice_is_pure_ascii_in_both_modes` PASSED; AND pasted output of the same command with a U+2014 temporarily inserted into the notice showing that test FAILED naming the character; AND pasted empty `git diff --name-only agent_workflows/` after reverting. Observation produced by the test E-01 creates.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing `test_driver_prompts_are_pure_ascii` PASSED, and under the same temporary mutation as V-01 FAILED; plus pasted `git show --stat HEAD` (or `git diff --name-only` of the execution commit) listing only `tests/test_driver_prompt_ascii.py`, and `rg -n "inspect|import ast|read_text" tests/test_driver_prompt_ascii.py` returning no hits.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output showing `test_driver_prompts_embed_the_notice_for_their_mode` PASSED, and the pasted bare `python3 -m pytest` summary line (`N passed`) with no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <this plan> -- tests/test_driver_prompt_ascii.py`; never commit the temporary mutation of `agent_workflows/ipd_lifecycle.py` used in V-01/V-02, and never push. Move to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
