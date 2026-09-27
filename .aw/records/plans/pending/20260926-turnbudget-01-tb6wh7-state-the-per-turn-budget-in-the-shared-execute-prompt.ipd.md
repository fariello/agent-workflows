# IPD: State the per-turn budget in the shared execute prompt

- Date: 2026-09-26
- Kind: child
- Concern: The driver knows the two bounds that can end an execute turn (the stall timeout, default 600s of no observed progress, and the hard per-turn ceiling, `lane_containment.MAX_TURN_TIMEOUT` = 4h pulled in by `driver_bound_for_host`), and the agent is told neither. An agent cannot decide whether a multi-minute suite run fits before starting it; it finds the bound by being killed. This is x7wfyx item A, never implemented (x7wfyx item B shipped via dy9ymn).
- Scope: IN: (a) resolve the host's per-turn ceiling once at run init and freeze it into `state["options"]` so the shared prompt stays host-neutral; (b) a short "Turn budget" paragraph in `runner_shared.build_prompt` next to the FOREGROUND paragraph, stating the stall timeout and the per-turn ceiling as a per-turn budget; (c) outcome tests in `tests/test_oc_runipd.py`. OUT: computing a REMAINING budget (the prompt is rendered before the turn starts, so it can only state the per-turn budget, never what is left); changing either bound's value; the verifier prompt; the review prompt; x7wfyx item B.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: 4bhxni
- Blocks-Release: next
- Set: turnbudget
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: tb6wh7

## Workflow history
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-006 all FIXED. Re-derived every number by driving the real code (driver_bound_for_host(None)=14400.0, driver_bound_for_host(parse('240m'))=14100.0) and both hosts' prompts. Found and fixed: a FOURTH build_prompt caller the plan did not name (tests/test_attempt_lane_facts.py asserts absolute_paths_outside_lane == [] over the whole prompt, a property check that fails on a new line); a fixture passing state with NO options key at all, so E-02's fallback needed state.get not state[...]; both bounds are FLOATS so a naive render says '600.0 seconds' and a truncated hours value would tell an agy agent 'about 3 hours' when it has 3.9, understating the budget the paragraph exists to make computable; the host-neutrality premise was false (build_prompt already imports lane_containment); and E-05's agy --prepare-only hedge was unnecessary (measured working offline). Findings in .aw/records/reviews/20260926-turnbudget-01-tb6wh7-state-the-per-turn-budget-in-the-shared-execute-prompt.review.md
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 4bhxni: State the stall timeout and per-turn ceiling in the shared execute prompt; carries Blocks-Release next by maintainer decision.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every execute-turn prompt, on both hosts, tells the agent its per-turn budget in seconds: the stall timeout (terminated after that long with no observed progress) and the hard per-turn ceiling (terminated after that long regardless). The agent can then decide arithmetically whether a long command fits, and when it does not, record a deferred question instead of being killed mid-command.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Freeze the resolved ceiling into run state

- [ ] E-01 In `runner_shared.initialize_run_core`, add an optional keyword parameter (for example `turn_ceiling_seconds: float | None = None`) and write it into `state["options"]` as `"turn_ceiling"` beside `"stall_timeout"`. Pass it from each host's `initialize_run`: `oc_runipd.initialize_run` passes `lane_containment.driver_bound_for_host(None)`; `agy_runipd.initialize_run` passes `lane_containment.driver_bound_for_host(lane_containment.parse_host_ceiling_seconds(host_options["timeout"]))`. Use the SAME expressions the two supervision sites use (`oc_runipd` `TurnBoundWatch(... max_turn_timeout=lane_containment.driver_bound_for_host(None))`, `agy_runipd` `max_turn_timeout=lane_containment.driver_bound_for_host(lane_containment.parse_host_ceiling_seconds(timeout))`) so the prompt states the bound that actually fires.
  - Depends on: none
  - Expected outcome: a freshly initialized oc run has `options.turn_ceiling == 14400.0`; an agy run with default `--timeout 240m` has `options.turn_ceiling == 14100.0` (240m minus the 300s `HOST_CEILING_OFFSET_SECONDS`). Measured at authoring: `driver_bound_for_host(None) == 14400.0`, `driver_bound_for_host(parse_host_ceiling_seconds('240m')) == 14100.0`.
  - Execution state: pending
- [ ] E-02 Make the prompt robust to a state that predates this plan (a resumed run whose frozen `options` has no `turn_ceiling`): `build_prompt` must fall back to `lane_containment.MAX_TURN_TIMEOUT` when the key is absent, and must omit the corresponding sentence (not print `0`) when a bound is disabled (`stall_timeout` of `0`/`None`, or ceiling `0.0`, which `driver_bound_for_host` returns when `MAX_TURN_TIMEOUT <= 0`).
  - Depends on: E-01
  - Expected outcome: no `KeyError` and no "0 seconds" budget on a legacy or disabled-bound state.
  - TOLERATE A MISSING `options` KEY ENTIRELY, not just a missing `turn_ceiling` within it. Measured at review: `tests/test_defect_report.py`'s fixture calls `build_prompt` with `{"run_id": "run-x", "repo": "."}`, which has NO `options` key, and both hosts render successfully today. So read through `state.get("options", {})` (or an equivalent); `state["options"]["turn_ceiling"]` would raise `KeyError` and turn a currently-passing test red.
  - IF BOTH BOUNDS ARE DISABLED, OMIT THE WHOLE PARAGRAPH rather than emitting a heading with no content. A "Turn budget" label followed by nothing is worse than silence: it tells the agent a budget exists and then declines to state it.
  - Execution state: pending

### Task group 2: The prompt paragraph

- [ ] E-03 In `runner_shared.build_prompt`, add a "Turn budget" paragraph directly after the paragraph beginning "Run every command you need the RESULT of in the FOREGROUND", rendered from `state["options"]["stall_timeout"]` (default `DEFAULT_STALL_TIMEOUT`) and `state["options"]["turn_ceiling"]`. Wording, ASCII only, stating it as a PER-TURN budget (never "remaining"): this turn is terminated after N seconds with no observed progress, and after M seconds (about H hours) in total regardless of progress; before starting a long command, estimate whether it fits; if it cannot fit, record a deferred question with the preserved state instead of starting it.
  - Depends on: E-02
  - Expected outcome: both hosts' prompts carry the paragraph with the host's own numbers; the prompt stays pure ASCII.
  - PLACE IT BEFORE `{role_block}`, NOT AFTER THE PARAGRAPH'S LAST LINE BLINDLY. Verified at review: the FOREGROUND paragraph is immediately followed by `{role_block}` and then the outcome-JSON block. Inserting between the FOREGROUND text and `{role_block}` keeps the lifecycle-role notice and the JSON schema contiguous; inserting after `{role_block}` would split them. Nothing may be added AFTER the reporting contract, which `tests/test_defect_report.py::PromptDemandTests::test_prompt_integration_and_format` asserts by comparing `prompt[start:]` to `reporting_contract.contract_text()` exactly.
  - FORMAT THE NUMBERS, do not interpolate the raw floats. Both values are FLOATS (`DEFAULT_STALL_TIMEOUT: float = 600.0`; `driver_bound_for_host` returns `14400.0`/`14100.0`), so a bare f-string renders "600.0 seconds" and "14400.0 seconds" to the agent. Use an integer-seconds rendering (for example `f"{stall:g}"` or `int(round(...))`, both verified at review to give `600` and `14400`). For the parenthetical hours, ROUND rather than truncate: `int(14100/3600)` is `3`, so "about 3 hours" would UNDERSTATE the agy ceiling by nearly an hour, while `round(14100/3600, 1)` is `3.9`. An understated budget is the wrong direction for a paragraph whose purpose is arithmetic, so state the rounded value or omit the parenthetical entirely when it would mislead.
  - HOST-NEUTRALITY, CORRECTED. The plan's original claim that `build_prompt` "never [reads] a host module" is FALSE as written: the function already opens with `from agent_workflows import ipd_lifecycle, lane_containment, reporting_contract`, and E-02's own fallback requires `lane_containment.MAX_TURN_TIMEOUT`. The real invariant, stated in this module's standing rule, is that `runner_shared` must not import EITHER RUNNER (`oc_runipd`/`agy_runipd`); `lane_containment` is host-neutral and already imported here. So keep reading the per-run number from `state["options"]` (which is what makes the agy `--timeout` case work) and use the existing `lane_containment` import for the fallback constant, without claiming an import restriction that does not exist.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-04 In `tests/test_oc_runipd.py`, near `TestIsolatedTurnPromptPointsAtTheLane`, add a test that renders the prompt through BOTH `oc_runipd.build_prompt` and `agy_runipd.build_prompt` from a state whose options carry a distinctive `stall_timeout` (for example `417`) and `turn_ceiling` (for example `9876`), and asserts each prompt contains `417` and `9876` in the budget paragraph, contains no non-ASCII character, and does not contain the word "remaining". Add a second case with `options: {}` (legacy state) asserting the prompt renders, states `600` for the stall timeout and `14400` for the ceiling.
  - Depends on: E-03
  - Expected outcome: new tests pass; each fails if the paragraph is removed or reads a hard-coded number.
  - Execution state: pending
- [ ] E-05 In `tests/test_oc_runipd.py`, add one test that the resolved ceiling reaches run state on each host: initialize a run with `--prepare-only` in a temp git repo (the pattern of `test_default_start_command_invocation` for oc; `agy_runipd.main([..., "--prepare-only"])` as in `tests/test_agy_runipd_cli.py` for agy), load the run's `state.json`, and assert `options.turn_ceiling` is `14400.0` on oc and `14100.0` on agy with default `--timeout`.
  - Depends on: E-01
  - Expected outcome: the value the prompt reads is the value the driver enforces, on both hosts.
  - THE HEDGE IS REMOVED BECAUSE IT WAS TESTED. The plan offered a fallback ("if an agy `--prepare-only` fixture turns out to need host resolution that cannot run offline, assert via `initialize_run` with a patched model resolver"). Driven at review: `agy_runipd.main(["appr01", "--repo", <tmp>, "--prepare-only"])` returned `0` OFFLINE, created the run directory, and wrote `options.timeout = 240m` with `options.stall_timeout = 600.0`. So the direct fixture works and no patched resolver is needed; use it. Note the two existing agy `--prepare-only` cases in `tests/test_agy_runipd_cli.py` (`test_main_exit_codes_for_empty_sweep_and_missing_id6`) deliberately assert NO run dir is created, so they are not a usable model for reading `state.json`; the plan's own oc pattern plus a real selector is.
  - Execution state: pending

### Task group 4: Full suite

- [ ] E-06 Run the bare suite `python3 -m pytest`. Fix a failure only if it is a genuine consequence of this change, never by weakening an assertion.
  - Depends on: E-04, E-05
  - Expected outcome: suite green.
  - THE COMPLETE SET OF EXISTING `build_prompt` CALLERS IN THE SUITE IS FOUR FILES, not the two the plan named. Enumerated at review with `rg -n "build_prompt" tests/`: `tests/test_defect_report.py:72`, `tests/test_finalize_sendback.py:557` and `:592`, `tests/test_oc_runipd.py:4561`/`:4593`/`:4640`, and `tests/test_attempt_lane_facts.py:456`. Check ALL FOUR, and note none of the four carries `pytest.mark.slow`, so all run in the bare suite.
  - THE ONE WITH A NON-OBVIOUS FAILURE MODE is `tests/test_attempt_lane_facts.py:456`, which feeds the rendered prompt to `lane_containment.absolute_paths_outside_lane` and asserts the list is EMPTY. That is a PROPERTY check over the whole prompt whose own docstring says "a newly added line ... fail[s] it", so any absolute path in the new paragraph breaks it. Verified at review that a numbers-only paragraph is safe (`absolute_paths_outside_lane` on the proposed wording returns `[]`), so the rule for E-03 is concrete: the budget paragraph must contain NO absolute path. If one is ever wanted there, that test is the gate it must pass.
  - THE SECOND NON-OBVIOUS ONE is `tests/test_defect_report.py:72`, whose fixture passes `{"run_id": "run-x", "repo": "."}` with NO `options` KEY AT ALL, not merely an empty one. So E-02's fallback must tolerate a MISSING `options` key, not just a missing `turn_ceiling` inside it; `state.get("options", {})` rather than `state["options"]`. Verified at review that both hosts' `build_prompt` render successfully from that state today (7833 and 7836 characters), so a `KeyError` introduced here would be a NEW failure in a test that passes now.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared` must import NEITHER RUNNER (`oc_runipd`/`agy_runipd`); host-varying values arrive via `HostLabels`, injected callables, or frozen `state["options"]`. It MAY import host-neutral modules, and `build_prompt` already imports `lane_containment`, `ipd_lifecycle` and `reporting_contract` on its first line (F-8). Freezing the ceiling into options is chosen over a new `HostLabels` field because `HostLabels` holds STRINGS with no defaults, while the ceiling is a number that depends on a per-run option (agy `--timeout`), so it is run state, not a host label.
- `stall_timeout` is already frozen in `initialize_run_core` (`"stall_timeout": stall_timeout`) and overridable on resume (`state.setdefault("options", {})["stall_timeout"] = args.stall_timeout` in both hosts). Reading it from `options` at render time therefore reflects a resume-time override automatically (F-12).
- Prompt must stay ASCII (`PromptDemandTests.test_prompt_integration_and_format` checks `ord(c) > 127`) and NOTHING may follow the reporting contract (the same test compares `prompt[start:]` to `reporting_contract.contract_text()` exactly).
- FOUR test files render `build_prompt`, not two (F-9): `tests/test_defect_report.py`, `tests/test_finalize_sendback.py`, `tests/test_oc_runipd.py`, `tests/test_attempt_lane_facts.py`. None is slow-marked, so all run in the bare suite.
- Both timing values are FLOATS, so agent-facing prose needs explicit formatting (F-11).
- Commits via `aw commit tb6wh7 -- <paths>`; suite run bare.

## Findings

| # | Evidence (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | `runner_shared.build_prompt` (~:24052), FOREGROUND paragraph "Run every command you need the RESULT of in the FOREGROUND" (~:24208) | Confirmed. |
| F-2 | `runner_shared.initialize_run_core` `stall_timeout = (getattr(args, "stall_timeout", default_stall_timeout) ...)` (~:24563) and `"stall_timeout": stall_timeout` (~:24589) | Confirmed; default 600.0 (`DEFAULT_STALL_TIMEOUT` in both hosts). |
| F-3 | `lane_containment.MAX_TURN_TIMEOUT: float = 4 * 60 * 60.0` (~:1107), `def driver_bound_for_host` (~:1123) | Confirmed. |
| F-4 | `agy_runipd.DEFAULT_TIMEOUT = "240m"` (~:767), `host_options["timeout"]`; `oc_runipd` passes `driver_bound_for_host(None)` | Confirmed. NOTE the effective agy ceiling is 14100s, not 4h: `driver_bound_for_host` subtracts `HOST_CEILING_OFFSET_SECONDS` (300s) when a host ceiling exists. The prompt must state 14100 on agy, which is why the value is resolved through `driver_bound_for_host` rather than stated as `MAX_TURN_TIMEOUT`. |
| F-5 | backlog 4bhxni text "tests/test_turn_bounds.py asserts three FOREGROUND properties" | STALE: `tests/test_turn_bounds.py` was deleted in commit `19313eed` (test trim); only a `.pyc` remains. No test currently pins the FOREGROUND paragraph. |
| F-6 | backlog 4bhxni "tests/test_defect_report.py hard-codes a per-host prompt-length baseline" | NOT FOUND at HEAD: `tests/test_defect_report.py` asserts contract placement and ASCII, no length baseline (`git grep "len(prompt"` in tests returns nothing relevant). No re-baselining is expected. |
| F-7 | backlog x7wfyx history "Item A outstanding ... continues to gate the release" | x7wfyx is `graduated` with `Blocks-Release: next`; its item A had no carrier with the gate. THIS PLAN now carries that gate: `- Blocks-Release: next` here is what makes x7wfyx's claim true. Re-verified at review: `x7wfyx` is `Status: graduated`, `Work-Kind: bug`, `Blocks-Release: next`, and its 2026-09-24 history line says item A "continues to gate the release". |
| F-8 | `runner_shared.build_prompt` opening line: `from agent_workflows import ipd_lifecycle, lane_containment, reporting_contract` | FOUND AT REVIEW: the plan's host-neutrality premise was MISSTATED. E-03 as authored said `build_prompt` "reads only `state["options"]`, never a host module", and OQ-02 leaned on that. `build_prompt` ALREADY imports `lane_containment` (and `ipd_lifecycle`), and E-02's own fallback to `MAX_TURN_TIMEOUT` REQUIRES that import. The real standing rule is that `runner_shared` must not import EITHER RUNNER; `lane_containment` is host-neutral. The frozen-option design is still the right choice, for the reason OQ-02 gives second (the agy ceiling depends on the per-run `--timeout`), but the import-restriction argument is wrong and is corrected in E-03 and OQ-02 so a future reader does not derive a false rule from it. |
| F-9 | `tests/test_attempt_lane_facts.py:456`; `lane_containment.absolute_paths_outside_lane` docstring ("a newly added line ... fail[s] it") | FOUND AT REVIEW, AND IT IS THE PLAN'S LARGEST UNDECLARED REGRESSION SURFACE. A FOURTH test file renders `build_prompt` and asserts `absolute_paths_outside_lane(prompt, lane_root) == []`, a property check over the ENTIRE prompt that fails on any new out-of-lane absolute path. E-06 named only two files. Verified safe for the proposed wording (`absolute_paths_outside_lane` returns `[]` on it), which converts a latent break into a concrete constraint: the budget paragraph must contain NO absolute path. |
| F-10 | `tests/test_defect_report.py:72-78` fixture state `{"run_id": "run-x", "repo": "."}` | FOUND AT REVIEW: that fixture passes NO `options` KEY AT ALL, so E-02's "options has no `turn_ceiling`" framing understates the case. `state["options"]` would raise `KeyError` and redden a test that passes today (measured: both hosts render 7833/7836 characters from it). E-02 now requires `state.get("options", {})`. |
| F-11 | `DEFAULT_STALL_TIMEOUT: float = 600.0`; `driver_bound_for_host` returning `14400.0`/`14100.0`; `--stall-timeout type=float` | FOUND AT REVIEW: both numbers are FLOATS, so a bare interpolation prints "600.0 seconds" and "14400.0 seconds" into agent-facing prose. Worse for the hours parenthetical: `int(14100/3600)` is `3`, so a truncating render would tell an agy agent "about 3 hours" when it has 3.9, UNDERSTATING the budget in a paragraph whose entire purpose is arithmetic. E-03 now requires an integer-seconds format and a ROUNDED (not truncated) hours value. Note E-04's substring assertions (`417`, `600`, `14400`) pass either way, since `"600" in "600.0"`, so the tests as authored would NOT have caught this. |
| F-12 | `--stall-timeout` accepted on `resume` (verified: `parse_args(["resume","run-x","--repo",".","--stall-timeout","42"])` -> `42.0`) and written back with `state.setdefault("options", {})["stall_timeout"] = args.stall_timeout` in BOTH hosts; `--timeout` is on the `start` subparser only | CHECKED AND CLEAN, recorded because it is the obvious way this design could have been wrong. Reading the stall value from `options` at render time means a resume-time override is reflected in the prompt automatically. The agy ceiling cannot diverge either, since `--timeout` cannot be changed on resume, so a ceiling frozen at init still matches the one `driver_bound_for_host(options["timeout"])` computes at the supervision site. No action needed; do not "fix" this. |

## Proposed changes (ordered, validatable)

1. E-01/E-02 freeze the resolved ceiling in run state with safe fallbacks.
2. E-03 render the paragraph from state.
3. E-04/E-05 outcome tests on both hosts.
4. E-06 full suite.

## Deferred / out of scope (with reason)

- A true REMAINING budget (elapsed-time-aware): the prompt is written before the turn starts; a live remaining figure would need a mid-turn channel that does not exist. Stated as per-turn budget instead.
  - Carrier-Declined: needs a mid-turn channel that does not exist; the per-turn budget fully addresses the reported failure.
- Adding the budget to the verifier or review prompts: they are separate builders with their own regression surface; file a backlog item if wanted.
  - Carrier-Declined: verifier and review turns are short and were not the reported failure; no work is owed.

## Scope check

- Over-scope: none.
- Under-scope (CLOSED at review, all three by tightening existing items rather than adding files): the fourth `build_prompt` caller `tests/test_attempt_lane_facts.py` was unnamed (F-9, now in E-06); the `options`-key-absent case was understated (F-10, now in E-02); and float rendering was unaddressed (F-11, now in E-03). None requires a new scope path: E-06 only READS those files unless one genuinely breaks, and the gate already permits a justified out-of-fence test edit with `--scope-reason`.
- Declared-but-possibly-unmodified: `tests/test_oc_runipd.py` holds both E-04 and E-05, so all four declared paths should be modified. If any is not, `--scope-ack` it at finalize.

## Required tests / validation

The maintainer's standing rule is to test OUTCOMES only: no test pins the paragraph's wording, a fingerprint, or "code unchanged". The two tests assert observable outcomes: the numbers the driver will enforce appear in the prompt both hosts actually send (with distinctive values, so a hard-coded literal fails), the prompt stays ASCII, a legacy state renders the defaults, and the frozen run state carries the host-correct ceiling. Few tests: two test methods (E-04 with two cases, E-05 across two hosts).

TWO LIMITS OF THIS TEST SET, recorded at review so they are not mistaken for coverage. FIRST, the distinctive-value assertions are SUBSTRING checks, and `"600" in "600.0"` is True, so they pass whether or not E-03 formats the floats (F-11); the float rendering is therefore verified by V-03's pasted paragraph and by reading, not by an assertion. Add an explicit `assertNotIn(".0 seconds", prompt)` if a mechanical check is wanted. SECOND, nothing here proves the budget the prompt STATES is the budget the driver ENFORCES at the supervision site; E-05 proves only that the frozen value equals the expression both sites use. That is the honest limit: the two sites compute the same expression from the same frozen input (F-12 records why they cannot diverge), which is an argument from reading rather than an end-to-end measurement, and an end-to-end one would need a real 4-hour turn.

## Spec / documentation sync

No `.spec.md` is amended. Spec `7ckptx` (worker lane containment) R4.4 defines the bounds; this plan only REPORTS them to the agent and changes neither their values nor their enforcement, so the spec's contract is unchanged.

## Open questions

### OQ-01: Work-Kind and the release gate

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: MAINTAINER DECIDED 2026-09-26 that this plan MUST carry `- Blocks-Release: next`. Work-Kind stays `followup` (inherited from 4bhxni): AGENTS.md "Every live bug gates the next release" auto-gates only `bug`, and the measured incident's cause was a host truncation (x7wfyx CORRECTION 2026-09-22, dy9ymn F-7), not a defect this prompt addresses, so `bug` is not required by policy. The gate is an explicit maintainer choice, not a policy consequence. It also makes x7wfyx's recorded claim ("Item A outstanding ... continues to gate the release") true, since no other artifact carried item A with the gate (F-7).

### OQ-02: New HostLabels field vs frozen option

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: frozen `state["options"]["turn_ceiling"]`. The agy ceiling depends on the per-run `--timeout` option, so it is run state, and freezing it at init matches how `stall_timeout` is handled (see Project conventions). CORRECTED AT REVIEW (F-8): the original rationale also leaned on `build_prompt` being unable to touch a host module, which is FALSE (it already imports `lane_containment`, `ipd_lifecycle` and `reporting_contract`, and E-02's fallback needs the first). The choice stands on the run-state argument alone, which is the sound one; the import argument is withdrawn so nobody derives a rule from it.

### OQ-03: Does the stated budget stay true for the turn the agent is actually in?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES for both numbers, resolved at review from the flag surfaces rather than assumed. The STALL value is read from `options` at render time and `--stall-timeout` IS accepted on `resume` and written back into `options` by both hosts, so an override is reflected in the next prompt automatically. The CEILING cannot drift because `--timeout` exists only on the `start` subparser, so the value frozen at init is still what `driver_bound_for_host(options["timeout"])` computes at the supervision site. Recorded as F-12 because this is the obvious way a frozen-at-init number could have gone stale, and the answer is that it cannot on either host; an executor should not "improve" this by recomputing the ceiling per turn.
- Carrier-Declined: nothing outstanding. Both bounds are correct as designed and no follow-up is owed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `initialize_run_core` and both hosts' `initialize_run` call sites, plus the E-05 test output (or a `python3 -c` that initializes each host with `--prepare-only` and prints `options.turn_ceiling`) showing `14400.0` for oc and `14100.0` for agy.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the output of the E-04 legacy-state case (`options: {}`) passing, and a `python3 -c` rendering a prompt with `options={"stall_timeout": 0, "turn_ceiling": 0.0}` then `grep -c "0 seconds"` on it returning 0.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the rendered "Turn budget" paragraph from an oc prompt and from an agy prompt (default options), showing `600` and `14400` on oc, `600` and `14100` on agy, and no word "remaining".
  - ALSO REQUIRED, because E-04's substring assertions cannot catch it (F-11): the pasted paragraphs must show INTEGER seconds (`600`, not `600.0`; `14400`, not `14400.0`) and, if an hours parenthetical is present, a value that does not UNDERSTATE the bound (`3.9` or "nearly 4" for the agy 14100s case, never a truncated `3`). Paste the agy paragraph specifically, since that is the case truncation would get wrong.
  - ALSO REQUIRED: paste the paragraph's position, showing it sits between the FOREGROUND paragraph and the lifecycle-role block, and that `tests/test_defect_report.py::PromptDemandTests::test_prompt_integration_and_format` still passes (nothing added after the reporting contract).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_oc_runipd.py -k <new test names>` output with the new tests passing, AND the same command's failing output after temporarily replacing the rendered stall value with a literal `600`, proving the distinctive-value assertion bites.
  - DO THE MUTATION IN A THROWAWAY WORKTREE, NOT IN THIS CHECKOUT. Use `git worktree add --detach <gitignored path> HEAD` (`.gitignore` ignores `.aw/worktrees/` and `tmp/`), apply the mutation there, run, paste, and `git worktree remove`. This is a SHARED checkout: a mutate-then-revert in place is the one step in this plan that can lose work if interrupted, and the obvious wrong reflex (`git stash`) would move a co-worker's uncommitted changes. If an in-place mutation is used anyway, revert it in the very next command and say so in the evidence.
  - ALSO CONFIRM `-k <names>` ACTUALLY SELECTS SOMETHING: paste the selection line and check it does not read `N deselected` with `0` collected. A `-k` pattern matching no test exits 0 having run nothing, which would make this V-item vacuous.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the new state test passing for both hosts, naming both in the output.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (`N passed`, no failures).
  - ALSO REQUIRED, naming the four affected files explicitly (F-9): paste `python3 -m pytest -o addopts="" -q tests/test_defect_report.py tests/test_finalize_sendback.py tests/test_oc_runipd.py tests/test_attempt_lane_facts.py` all passing. The bare run covers them, but naming them makes the prompt-caller surface auditable rather than trusting that a green total included the one property test (`tests/test_attempt_lane_facts.py`) most likely to break.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one paragraph, the one frozen option it reads, and their tests. Assessed against the right-sizing diagnostics at review: each E-item is one focused pass in one region, and no item was split (E-01/E-02 are the state seam, E-03 the render, E-04/E-05 the two independent test surfaces, E-06 the suite).

This plan is `reviewed` and needs explicit human approval before execution. `reviewed` records that the review happened; `- Readiness: go-pending-approval` means it passed review and awaits sign-off.

WHAT A HUMAN IS APPROVING: a change to the shared execute prompt every agent turn on both hosts receives (one paragraph), one new frozen run option, and two outcome tests. The release gate is the maintainer's explicit 2026-09-26 decision (OQ-01), NOT a policy consequence: the backlog item this graduated from records itself as "NOT release-gating", and `- Work-Kind: followup` is not in the auto-gating set, so the gate exists solely because the maintainer said so and because it makes x7wfyx's recorded claim true (F-7).

THE BLAST RADIUS IS EVERY TURN ON BOTH HOSTS, which is what makes an otherwise small change worth reading carefully. Four test files render this prompt (F-9), one of them a PROPERTY check that fails on any new out-of-lane absolute path, and one fixture passes a state with no `options` key at all (F-10). Both are now constraints on E-02/E-03 rather than surprises for the executor.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the four files in `- Scope-Paths:`; in the two host modules only the `initialize_run` call into `initialize_run_core`, and in `runner_shared.py` only `build_prompt` and `initialize_run_core`. Specifically NOT in scope: the value of either bound, the supervision sites in either host, the verifier prompt, the review prompt. Do not expand scope casually; if the work genuinely requires a file outside the fence (for example one of the other three `build_prompt` callers legitimately needing an update), make the edit and JUSTIFY it at finalize with `--scope-reason`; a declared path left unmodified needs `--scope-ack`. Genuine stop condition: an unresolvable concurrent edit to `runner_shared.py`.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every test claim; the V-04 mutation check must show a real failure, and must confirm its `-k` pattern selected a non-zero number of tests. Run the suite BARE (`python3 -m pytest`); do not add `-n0`, a second `-q`, or `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit tb6wh7 -- <paths>`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is `aw ipd finalize tb6wh7 --actor <agent/model> --message <summary> --apply`; OWNERSHIP IS CONDITIONAL, the RUNNER performs it in a managed lane and the executor performs it only in an unmanaged or hand-driven run, and it is never hand-rolled with `git mv`. Then set backlog `4bhxni` done citing the executed plan; x7wfyx's item-A gate is then satisfied by this plan's execution.

NOTE ON CLOSING `4bhxni`: it carries `- Blocks-Release: next`, so `aw backlog set done` FAILS CLOSED unless the gate is provably preserved or released. This plan carries `- From-Backlog: 4bhxni` AND the same `- Blocks-Release: next`, so the HANDOFF route applies once this plan is `executed`; close it with `--evidence` citing the executed plan path rather than reaching for `--blocks-release -`, which would DROP the gate instead of discharging it. `x7wfyx` is a separate item and is not closed by this plan.
