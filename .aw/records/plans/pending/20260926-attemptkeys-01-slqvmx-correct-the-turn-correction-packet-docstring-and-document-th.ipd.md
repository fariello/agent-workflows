# IPD: Correct the turn_correction_packet docstring and document the prior-attempt allowlist's driver-only contract

- Date: 2026-09-26
- Kind: child
- Concern: THE PRIOR-ATTEMPT ALLOWLIST SILENTLY DROPS EVERY KEY NOT ON IT, AND ONE DOCSTRING TELLS THE NEXT AUTHOR THE OPPOSITE. `lane_containment.prior_attempt_summary` returns, for an ISOLATED turn (the default for an execute item), only the keys in `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` (25 keys). Measured at HEAD `61ef21d8` with `rg -o 'attempt(_record)?\["([a-z_]+)"\]\s*='` over `agent_workflows/`: 80 distinct keys are assigned onto attempt records that way, of which 63 are not allowlisted and so never reach an isolated turn's `Prior attempt:` line (the pattern misses dict-literal writes, so these counts are indicative, not exact). That is CORRECT for containment (spec `7ckptx` R1.1: path-bearing keys such as `prompt`, `worktree`, `verify_log` must not leak), but nothing at the allowlist says so, and `runner_shared.turn_correction_packet`'s docstring states falsely that the packet "is recorded on the ATTEMPT under the allowlisted `turn_correction` key, so it reaches the next turn's prompt through that one channel". Measured: `"turn_correction" in _PRIOR_ATTEMPT_SAFE_KEYS` is `False`, and `prior_attempt_summary({"turn_correction": {...}, "session_id": "s", "exit_code": 0, "finalize_refused": "r"}, Path("/tmp"))` returns `{'exit_code': 0, 'finalize_refused': 'r'}`. The packet actually arrives through `runner_shared.build_correction_notice`, whose docstring and `build_prompt`'s comment state this correctly.
- Scope: IN: (a) correct `turn_correction_packet`'s "WHICH CONSTRUCTION PATH CARRIES IT" paragraph to name `build_correction_notice` as the delivery channel and state that `turn_correction` is deliberately NOT allowlisted; (b) replace the three-line comment above `_PRIOR_ATTEMPT_SAFE_KEYS` with a documented contract (a new attempt key is DRIVER-ONLY unless added here; delivering a fact to the agent must go through an explicit prompt notice or an allowlist entry; adding an entry requires that the value can never carry a filesystem path), with a short `_PRIOR_ATTEMPT_DRIVER_ONLY_EXAMPLES` comment block naming representative driver-only keys and why; (c) one sentence in `prior_attempt_summary`'s docstring pointing at that contract; (d) ONE behavioral test. OUT: any change to the projection's behavior or to the allowlist's members (spec `7ckptx` R1.1 fail-closed); a key-enumerator or any source-scanning test (maintainer ruling 2026-09-26); a denylist (the backlog's option (b), which inverts the fail-closed direction).
- Scope-Paths: agent_workflows/lane_containment.py, agent_workflows/runner_shared.py, tests/test_prior_attempt_projection.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: ytrz7u
- Set: attemptkeys
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: slqvmx

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ytrz7u on the maintainer's batch-graduation instruction and the 2026-09-26 ruling (no source-scanning tests; fix the false docstring and document the driver-only contract, behavior unchanged). Allowlist membership and the projection's output were re-measured at HEAD 61ef21d8.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Stop the prior-attempt projection from being a silent trap: correct the one docstring that claims `turn_correction` rides the allowlist, and write the allowlist's contract where the next author adding an attempt key will read it, with the projection's behavior unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD and paste: `python3 -c "from agent_workflows import lane_containment as L; from pathlib import Path; print('turn_correction' in L._PRIOR_ATTEMPT_SAFE_KEYS, 'session_id' in L._PRIOR_ATTEMPT_SAFE_KEYS, 'finalize_refused' in L._PRIOR_ATTEMPT_SAFE_KEYS); print(L.prior_attempt_summary({'turn_correction': {'x': 1}, 'session_id': 's', 'exit_code': 0, 'finalize_refused': 'r'}, Path('/tmp')))"`, and `rg -n "allowlisted .turn_correction" agent_workflows`. If `turn_correction` IS now allowlisted (for example because a concurrent plan added it), the docstring may be true: STOP E-02 and report, and do E-03/E-04 only.
  - Depends on: none
  - Expected outcome: `False False True`; `{'exit_code': 0, 'finalize_refused': 'r'}`; one `rg` hit in `runner_shared.turn_correction_packet`.
  - Execution state: pending

### Task group 2: documentation

- [ ] E-02 CORRECT `runner_shared.turn_correction_packet`'s docstring paragraph "WHICH CONSTRUCTION PATH CARRIES IT". Replace the sentences from "It is the EXISTING recovery-prompt channel" through "through that one channel." with, in substance: the packet is recorded on the attempt under `turn_correction` for the RECORD, and it reaches the next turn through `build_correction_notice`, which `build_prompt` renders as its own notice; `turn_correction` is deliberately NOT in `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`, so the `Prior attempt:` line does not carry it on an isolated turn (the first shape tried, measured inert by `xipfy1`). Keep the `run_packet.build_step_packet` sentence and the "WHAT IS OMITTED" paragraph unchanged. Change no code.
  - Depends on: E-01
  - Expected outcome: `rg -n "allowlisted .turn_correction" agent_workflows` returns nothing; the paragraph names `build_correction_notice`.
  - Execution state: pending

- [ ] E-03 DOCUMENT THE CONTRACT at `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`. Replace the existing `#:` comment with a block stating: (1) WHAT IT GUARANTEES: an isolated turn sees only these keys, because every other attempt key may carry an absolute driver-side path (spec `7ckptx` R1.1), and dropping is fail-closed. (2) THE CONTRACT FOR A NEW KEY: any key written onto an attempt record is DRIVER-ONLY by default and will NOT reach an isolated agent. (3) HOW TO DELIVER A FACT TO THE AGENT: either render an explicit prompt notice (the supported route, for example `runner_shared.build_correction_notice` for `turn_correction`) or add the key here, and only if its value can never carry a filesystem path. (4) WHY THE FAILURE IS SILENT: a unit test asserting on the attempt dict still passes, so the author must check the rendered prompt of an ISOLATED turn (as `tests/test_finalize_sendback.py` does for `finalize_refused`). Then add a `# _PRIOR_ATTEMPT_DRIVER_ONLY_EXAMPLES` comment block (comments only, no new symbol, no test reads it) listing a few representative driver-only keys with a one-phrase reason each, verified against the tree at execution. They are `prompt`/`worktree`/`verify_log`/`lane_plan_path` (absolute paths), `session_id` (host session handle, driver bookkeeping), `turn_correction` (delivered by its own notice), `suite_baseline` (driver-side gate state). Add one sentence to `prior_attempt_summary`'s docstring pointing at that block. Do NOT change the tuple's members or the function body.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/lane_containment.py` shows only comment/docstring lines; the tuple and `prior_attempt_summary`'s `return` lines are byte-identical.
  - Execution state: pending

### Task group 3: prove behavior is as documented

- [ ] E-04 ADD `tests/test_prior_attempt_projection.py` with ONE behavioral test class (no `inspect.getsource`/`read_text` of package source, maintainer ruling 2026-09-26): calling `lane_containment.prior_attempt_summary` with a `lane_root` (isolated) on an attempt dict carrying `turn_correction`, `session_id`, `prompt` (an absolute path string), `exit_code`, and `finalize_refused` returns a dict WITHOUT `turn_correction`, `session_id`, or `prompt` and WITH `exit_code` and `finalize_refused` unchanged; the same dict with `lane_root=None` (non-isolated, spec `7ckptx` R1.3) is returned unchanged including all five keys; and `None` input returns `None`. Name the test so its failure message explains the contract (e.g. `test_isolated_projection_drops_driver_only_keys_and_keeps_allowlisted_ones`).
  - Depends on: E-02, E-03
  - Expected outcome: passes before and after (behavior is unchanged by design); it pins the documented contract so a future allowlist or projection change that leaks `session_id`/`turn_correction`, or drops an allowlisted key, goes red.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `7ckptx` R1.1/R1.3: an isolated turn's prompt names nothing outside the lane; a non-isolated turn gets the record unchanged. `prior_attempt_summary` implements both, and its docstring says path-valued keys are "DROPPED, not rewritten".
- `runner_shared.build_correction_notice` and the comment in `build_prompt` ("retrywire (`xipfy1`) E-04 ... MEASURABLY INERT") already describe the correct delivery channel; only `turn_correction_packet`'s docstring disagrees.
- `tests/test_finalize_sendback.py` already asserts `finalize_refused` membership and that it survives the projection; this plan adds the complementary drop-side assertion rather than duplicating those.
- Tests are behavioral only (maintainer ruling 2026-09-26); run BARE `python3 -m pytest`, narrowed runs with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8` on 2026-09-26.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `runner_shared.turn_correction_packet` docstring | Claims `turn_correction` is allowlisted and reaches the prompt via `Prior attempt:`. It is not and does not. | `'turn_correction' in L._PRIOR_ATTEMPT_SAFE_KEYS` -> `False`; projection output omits it |
| F-2 | LOW | `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` | No stated contract for new keys; most written keys are silently driver-only. | 80 keys assigned via `attempt[...] =`, 63 not allowlisted (indicative, pattern-based) |
| F-3 | INFO | delivery | The correct channel exists and is documented in two other places. | `build_correction_notice` docstring "THE DELIVERY CHANNEL"; `build_prompt` comment "WHY THIS IS RENDERED HERE" |
| F-4 | INFO | overlap | Pending plan `zrvtm2` writes attempt `session_id`/cost/tokens; `cost`/`tokens` are already allowlisted and `session_id` is not. This plan changes no behavior, so there is no ordering dependency; E-03's example list is re-verified at execution. | `zrvtm2` Scope; E-01 membership check |

## Proposed changes (ordered, validatable)

1. E-01 re-measures membership and the projection.
2. E-02 corrects the false docstring.
3. E-03 documents the contract beside the allowlist.
4. E-04 adds one behavioral test of the documented contract.

## Deferred / out of scope (with reason)

- A test that enumerates attempt keys and fails when one is neither allowlisted nor marked driver-only (backlog option (a)).
  - Carrier-Declined: maintainer ruling 2026-09-26, no source-scanning tests.
- Replacing the allowlist with a denylist (backlog option (b)).
  - Carrier-Declined: inverts the fail-closed containment direction spec `7ckptx` R1.1 requires; a new path-bearing key would leak by default.
- Adding any key (e.g. `session_id`) to the allowlist.
  - Carrier-Declined: no current consumer needs it in an isolated prompt; behavior is deliberately unchanged here.

## Scope check

- Over-scope: none.
- Under-scope: none.
- Scope-Paths justification: `lane_containment.py` (comment and docstring), `runner_shared.py` (one docstring), new test file.

## Required tests / validation

- `tests/test_prior_attempt_projection.py` (new), one behavioral class; passes before and after, since behavior is unchanged.
- `tests/test_finalize_sendback.py` stays green.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: spec `7ckptx` R1.1/R1.3 already require exactly the behavior documented here; no `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs change (internal docstrings and comments only).

## Open questions

### OQ-01: Add a key-enumerator test (backlog option (a))?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No. Maintainer ruling 2026-09-26 (recorded on backlog `ytrz7u`'s history): no source-scanning tests; fix the false docstring and document the driver-only keys next to the allowlist, behavior unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `python3 -c` output and the `rg` hit.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the docstring diff and `rg -n "allowlisted .turn_correction" agent_workflows` returning nothing (exit 1).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `lane_containment.py` diff, showing only `#` comment and docstring lines changed; paste the E-01 `python3 -c` command re-run with identical output (behavior unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_prior_attempt_projection.py tests/test_finalize_sendback.py -o addopts="" -q` passing with counts; then, to show the new test is not vacuous, temporarily add `"session_id"` to `_PRIOR_ATTEMPT_SAFE_KEYS` and paste the new test FAILING, then restore and paste it passing. Paste the bare `python3 -m pytest` summary BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Documentation and one test, no behavior change: a false docstring in `turn_correction_packet` is corrected, the prior-attempt allowlist gains a written contract saying new attempt keys are driver-only unless deliberately added (and how to deliver a fact to the agent instead), and one behavioral test pins that driver-only keys are dropped for an isolated turn while allowlisted keys survive. Per the maintainer's 2026-09-26 ruling there is no key-enumerator or source-scanning test.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the three paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 must show the new test going red under a deliberate allowlist leak.

Commit ONLY paths in `- Scope-Paths:` through `aw commit slqvmx -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `ytrz7u` `done` with `--evidence` citing the executed plan.
