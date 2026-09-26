# IPD: State the per-turn budget in the shared execute prompt

- Date: 2026-09-26
- Kind: child
- Concern: The driver knows the two bounds that can end an execute turn (the stall timeout, default 600s of no observed progress, and the hard per-turn ceiling, `lane_containment.MAX_TURN_TIMEOUT` = 4h pulled in by `driver_bound_for_host`), and the agent is told neither. An agent cannot decide whether a multi-minute suite run fits before starting it; it finds the bound by being killed. This is x7wfyx item A, never implemented (x7wfyx item B shipped via dy9ymn).
- Scope: IN: (a) resolve the host's per-turn ceiling once at run init and freeze it into `state["options"]` so the shared prompt stays host-neutral; (b) a short "Turn budget" paragraph in `runner_shared.build_prompt` next to the FOREGROUND paragraph, stating the stall timeout and the per-turn ceiling as a per-turn budget; (c) outcome tests in `tests/test_oc_runipd.py`. OUT: computing a REMAINING budget (the prompt is rendered before the turn starts, so it can only state the per-turn budget, never what is left); changing either bound's value; the verifier prompt; the review prompt; x7wfyx item B.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: to-review
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
  - Execution state: pending

### Task group 2: The prompt paragraph

- [ ] E-03 In `runner_shared.build_prompt`, add a "Turn budget" paragraph directly after the paragraph beginning "Run every command you need the RESULT of in the FOREGROUND", rendered from `state["options"]["stall_timeout"]` (default `DEFAULT_STALL_TIMEOUT`) and `state["options"]["turn_ceiling"]`. Wording, ASCII only, stating it as a PER-TURN budget (never "remaining"): this turn is terminated after N seconds with no observed progress, and after M seconds (about H hours) in total regardless of progress; before starting a long command, estimate whether it fits; if it cannot fit, record a deferred question with the preserved state instead of starting it. Keep `build_prompt` host-neutral: it reads only `state["options"]`, never a host module.
  - Depends on: E-02
  - Expected outcome: both hosts' prompts carry the paragraph with the host's own numbers; the prompt stays pure ASCII.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-04 In `tests/test_oc_runipd.py`, near `TestIsolatedTurnPromptPointsAtTheLane`, add a test that renders the prompt through BOTH `oc_runipd.build_prompt` and `agy_runipd.build_prompt` from a state whose options carry a distinctive `stall_timeout` (for example `417`) and `turn_ceiling` (for example `9876`), and asserts each prompt contains `417` and `9876` in the budget paragraph, contains no non-ASCII character, and does not contain the word "remaining". Add a second case with `options: {}` (legacy state) asserting the prompt renders, states `600` for the stall timeout and `14400` for the ceiling.
  - Depends on: E-03
  - Expected outcome: new tests pass; each fails if the paragraph is removed or reads a hard-coded number.
  - Execution state: pending
- [ ] E-05 In `tests/test_oc_runipd.py`, add one test that the resolved ceiling reaches run state on each host: initialize a run with `--prepare-only` in a temp git repo (the pattern of `test_default_start_command_invocation` for oc; `agy_runipd.main([..., "--prepare-only"])` as in `tests/test_agy_runipd_cli.py` for agy), load the run's `state.json`, and assert `options.turn_ceiling` is `14400.0` on oc and `14100.0` on agy with default `--timeout`. If an agy `--prepare-only` fixture turns out to need host resolution that cannot run offline, assert via `agy_runipd.initialize_run` with a patched model resolver instead and say so in the evidence.
  - Depends on: E-01
  - Expected outcome: the value the prompt reads is the value the driver enforces, on both hosts.
  - Execution state: pending

### Task group 4: Full suite

- [ ] E-06 Run the bare suite `python3 -m pytest`. The shared prompt changed, so `tests/test_defect_report.py` `PromptDemandTests.test_prompt_integration_and_format` (asserts the prompt ends with the reporting contract and is ASCII) and `tests/test_finalize_sendback.py` (renders `build_prompt`) must still pass; fix a failure only if it is a genuine consequence of this change, never by weakening an assertion.
  - Depends on: E-04, E-05
  - Expected outcome: suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared` must import neither runner; host-varying values arrive via `HostLabels`, injected callables, or frozen `state["options"]` (docstring of `runner_shared.build_prompt`, `HostLabels`). Freezing the ceiling into options is chosen over a new `HostLabels` field because `HostLabels` holds STRINGS with no defaults, while the ceiling is a number that depends on a per-run option (agy `--timeout`), so it is run state, not a host label.
- `stall_timeout` is already frozen in `initialize_run_core` (`"stall_timeout": stall_timeout`) and overridable on resume (`state.setdefault("options", {})["stall_timeout"] = args.stall_timeout` in both hosts).
- Prompt must stay ASCII (`PromptDemandTests.test_prompt_integration_and_format` checks `ord(c) > 127`).
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
| F-7 | backlog x7wfyx history "Item A outstanding ... continues to gate the release" | x7wfyx is `graduated` with `Blocks-Release: next`; its item A had no carrier with the gate. THIS PLAN now carries that gate: `- Blocks-Release: next` here is what makes x7wfyx's claim true. |

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
- Under-scope: none known.

## Required tests / validation

The maintainer's standing rule is to test OUTCOMES only: no test pins the paragraph's wording, a fingerprint, or "code unchanged". The two tests assert observable outcomes: the numbers the driver will enforce appear in the prompt both hosts actually send (with distinctive values, so a hard-coded literal fails), the prompt stays ASCII, a legacy state renders the defaults, and the frozen run state carries the host-correct ceiling. Few tests: two test methods (E-04 with two cases, E-05 across two hosts).

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
- Resolution or deferral rationale: frozen `state["options"]["turn_ceiling"]`. The agy ceiling depends on the per-run `--timeout` option, so it is run state, and freezing it at init matches how `stall_timeout` is handled (see Project conventions).

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
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_oc_runipd.py -k <new test names>` output with the new tests passing, AND the same command's failing output after temporarily replacing the rendered stall value with a literal `600` in a scratch working copy (revert before commit; do not commit the mutation), proving the distinctive-value assertion bites.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the new state test passing for both hosts, naming both in the output.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (`N passed`, no failures).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a change to the shared execute prompt every agent turn on both hosts receives (one paragraph), one new frozen run option, and two outcome tests. The release gate is the maintainer's explicit 2026-09-26 decision (OQ-01).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the four files in `- Scope-Paths:`; in the two host modules only the `initialize_run` call into `initialize_run_core`. Do not expand scope casually; if the work genuinely requires a file outside the fence (for example a test elsewhere that renders `build_prompt` and legitimately needs updating), make the edit and JUSTIFY it at finalize with `--scope-reason`; a declared path left unmodified needs `--scope-ack`. Genuine stop condition: an unresolvable concurrent edit to `runner_shared.py`.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every test claim; the V-04 mutation check must show a real failure.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit tb6wh7 -- <paths>`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize tb6wh7 --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). Then set backlog `4bhxni` done citing the executed plan; x7wfyx's item-A gate is then satisfied by this plan's execution.
