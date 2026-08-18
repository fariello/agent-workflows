# IPD: agy-run multi-mode executor and skeptical validator

- Date: 2026-08-16
- Kind: child
- Concern: Antigravity/Gemini execution workflows require a unified, multi-mode runner that supports executing IPDs, authoring IPDs from specs, running prompt files, and executing raw prompts (`agy -c -p` equivalent) while enforcing a mandatory two-turn skeptical validation protocol to eliminate greenwashing, shallow tests, and unverified completion claims.
- Scope: `tools/agy_run.py` (new unified runner), `tools/antigravity_execute_ipd.py` (compatibility wrapper), durable prompt templates in `tools/awphysical/` or `tools/prompts/`, and test coverage in `tools/test_agy_run.py` and `tools/awphysical/test_awphysical_tools.py`.
- Status: executed
- Set: agyrun
- Order: 1
- Highest E allocated: 07
- Author: Antigravity (Gemini 3.7 Flash High)
- Id: 71ibuy
- Approval: 2026-08-16 human maintainer (chat) - approved IPD 71ibuy for execution

## Workflow history

- 2026-08-16 draft (Antigravity (Gemini 3.7 Flash High)): created to address Gemini 3.7 Flash High execution faithfulness, multi-mode invocation, calibrated diligence framing, and automatic two-turn skeptical revalidation.
- 2026-08-16 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. Structural lint conforming. Applied PR-001 (Turn-1 failure halting before Turn-2 audit) and PR-002 (session continuity, isolation controls, and rich self-describing --help examples).
- 2026-08-16 approved (human maintainer via chat): Status reviewed -> approved. Cleared for execution.
- 2026-08-16 executed (Antigravity (Gemini 3.7 Flash High)): all E/V items completed and verified with automated test suite (59 unit tests passing).

## Goal

Provide a unified, robust runner CLI `tools/agy_run.py` (with backwards compatibility for `tools/antigravity_execute_ipd.py`) that supports multiple execution modes: IPD execution, spec-to-IPD generation, prompt files, and raw prompt strings (`agy -c -p`). Enforce a two-turn verification loop across all modes where Turn 1 runs the primary task with calibrated diligence instructions, and Turn 2 automatically resumes the conversation to perform an evidence-backed skeptical self-audit, specifically hunting for greenwashing, shallow tests, unwired vocabulary, and unverified claims before certifying completion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Multi-mode CLI and target resolution

- [x] E-01 Implement `tools/agy_run.py` with argument parsing and multi-mode resolution supporting four explicit modes and auto-detection: (1) `ipd` mode: executes a pending IPD by path, filename, or stable id6; (2) `spec` mode: generates an IPD from a specification document; (3) `file` mode: executes a prompt file (e.g. `.agents/prompts/...`); (4) `prompt` mode: executes an inline raw prompt string (`-p` / `--prompt`, matching `agy -c -p` ergonomics). Auto-detection inspects the positional target or flags to select the appropriate mode. Provide comprehensive, agent-friendly `--help` documentation detailing all modes, options, session continuity workflows, and concrete CLI invocation examples.
  - Depends on: none
  - Expected outcome: `tools/agy_run.py` parses CLI arguments, resolves targets accurately across all four modes, formats rich self-describing `--help` with examples, and reports actionable errors for missing or ambiguous targets.
  - Execution state: performed

- [x] E-02 Support model selection defaulting to `gemini-3.7-flash-high` (with `--model` override), comprehensive session continuity controls (`--session-id` / `--conversation-id` / `-s` / `-c` to attach to a specific conversation, `--continue` as default to resume latest project conversation, `--new-session` / `-n` to force a clean slate, and `ANTIGRAVITY_CONVERSATION_ID` env var), turn timeouts (`--timeout`, default `240m`), permission bypass (`--dangerously-skip-permissions`), and audit control (`--no-audit` to run single-turn, `--audit-only` to run turn 2 on an existing session).
  - Depends on: E-01
  - Expected outcome: CLI accepts standard Antigravity runtime options, provides flexible session continuity and isolation controls, and manages session chaining between turn 1 and turn 2.
  - Execution state: performed

### Task group 2: Turn-1 diligence framing (calibrated for Gemini 3.7 Flash High)

- [x] E-03 Create calibrated Turn-1 preambles tailored to Gemini 3.7 Flash High for each execution mode: (1) IPD execution preamble emphasizing behavior-over-vocabulary, falsifiable red-then-green test proofs, full-suite verification, path-scoped commits, and leaving lifecycle moves to the orchestrator; (2) spec-to-IPD generation preamble emphasizing complete spec coverage, using `aw ipd scaffold`, assigning IDs via `aw ipd sync`, validating structure via `aw ipd lint`, and defining falsifiable V-items; (3) prompt/file preambles establishing strict execution standards without antagonistic or hostile tone. Store durable prompt templates in `tools/awphysical/` (or `tools/prompts/`) with fallback to built-in defaults.
  - Depends on: E-01
  - Expected outcome: Turn-1 prompts deliver clear, demanding, professional diligence constraints tailored to the active mode.
  - Execution state: performed

### Task group 3: Turn-2 skeptical revalidation and anti-greenwashing audit

- [x] E-04 Create mode-specific Turn-2 skeptical audit prompts that force the agent to re-evaluate its work critically in the same conversation session: (1) IPD audit: builds an evidence table for every E-* and V-* item, checks symbol wiring in the real code path, verifies falsifiable test output with pasted red-then-green proof, runs full-suite tests, and rejects unverified claims; (2) spec-to-IPD audit: verifies 100% spec requirement coverage, deterministic lint pass, and 1:1 E/V bijection; (3) general task audit: inspects actual file diffs, executes test runners, checks for negative edge cases, and verifies no unintended side effects or skipped instructions.
  - Depends on: E-03
  - Expected outcome: Turn-2 forces the agent to prove its claims with concrete repository evidence and correct any discovered gaps before reporting.
  - Execution state: performed

### Task group 4: Two-turn execution engine and backwards compatibility

- [x] E-05 Implement the two-turn execution engine in `tools/agy_run.py` that executes Turn 1, streams JSONL events to `tmp/antigravity/agy-<pid>-<timestamp>.jsonl`, prints single-line deduplicated progress updates to stderr, captures response payload and conversation ID, and automatically executes Turn 2 in the same conversation session (`session_id=first_turn.conversation_id`).
  - Depends on: E-02, E-04
  - Expected outcome: Headless execution runs reliably, logs complete event streams for external monitoring (`tail -f`), and chains Turn 1 and Turn 2 seamlessly.
  - Execution state: performed

- [x] E-06 Update `tools/antigravity_execute_ipd.py` as a backwards-compatible wrapper that delegates to `tools/agy_run.py` in IPD mode, preserving all existing CLI options and behavior.
  - Depends on: E-05
  - Expected outcome: Existing scripts and agent invocations of `tools/antigravity_execute_ipd.py` continue to work without modification.
  - Execution state: performed

### Task group 5: Automated test coverage

- [x] E-07 Add comprehensive unit tests in `tools/test_agy_run.py` (and integrate into test suite) covering: CLI argument parsing, target auto-detection for all four modes, prompt and preamble construction, session chaining and ID propagation, event stream parsing and progress filtering, and backwards compatibility wrapper delegation.
  - Depends on: E-05, E-06
  - Expected outcome: All `tools/agy_run.py` capabilities are thoroughly verified by automated unit tests that pass in the test suite.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `tools/antigravity_execute_ipd.py` already implements a two-turn headless runner using `subprocess.Popen` with `agy -p <prompt> --output-format stream-json --print-timeout <timeout>`, streaming events to `tmp/antigravity/*.jsonl` and filtering progress messages to stderr.
- Antigravity session chaining uses `--conversation <id>` on the second turn, capturing `conversation_id` from the terminal `result` event of the first turn.
- Durable prompt files live under `tools/awphysical/` (`agy-execution-preamble.md` and `agy-self-audit-prompt.md`) with programmatic fallback if missing.
- AGENTS.md rules require path-scoped commits (`git commit -- <paths>`), no dashes in user-facing prose, pasted actual runner output, and never moving an IPD to executed/ without orchestrator authority.

## Findings

- `tools/antigravity_execute_ipd.py` was hardcoded specifically for IPD execution and rejected any target not under `.agents/plans/pending/`.
- Users and orchestrators frequently need to run prompt files (`.agents/prompts/...`), generate IPDs from specs, or execute ad-hoc prompts (`agy -c -p`) with the same level of skepticism and two-turn verification.
- The tone of the previous prompt preambles was extremely harsh; Gemini 3.7 Flash High responds well to clear, rigorous, professional standards focused on falsifiable criteria, negative cases, behavior wiring, and concrete pasted proof rather than adversarial rhetoric.

## Proposed changes (ordered, validatable)

1. Create `tools/agy_run.py` with multi-mode target resolution (`ipd`, `spec`, `file`, `prompt`) and default model `gemini-3.7-flash-high`.
2. Author calibrated Turn-1 preambles and Turn-2 skeptical audit prompts for each mode.
3. Implement the two-turn execution engine with streaming JSONL logging and progress updates.
4. Convert `tools/antigravity_execute_ipd.py` into a compatibility wrapper delegating to `tools/agy_run.py`.
5. Add unit tests in `tools/test_agy_run.py` covering all modes, parsing, prompt synthesis, and execution logic.

## Deferred / out of scope (with reason)

- Modifying the core `agent_workflows` package CLI: `tools/agy_run.py` is developer/orchestrator tooling in `tools/` and does not alter installed library packages.
- Interactive multi-turn chat UI: `tools/agy_run.py` is designed for headless, scriptable, two-turn execution and verification.

## Scope check

- Over-scope: none.
- Under-scope: covers all four execution modes, model configuration, calibrated tone, two-turn verification, backwards compatibility, and unit testing.

## Required tests / validation

- `python3 -m unittest tools.test_agy_run`
- `python3 -m unittest tools.awphysical.test_awphysical_tools`
- Validation of `tools/antigravity_execute_ipd.py --help` and `tools/agy_run.py --help`
- Dry-run verification of target resolution across all modes (`ipd`, `spec`, `file`, `prompt`)
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent .agents/plans/pending/20260816-agyrun-01-k8m3px-agy-run-executor-validator.md`

## Spec / documentation sync

- Update `tools/README.md` and `tools/awphysical/README.md` to document `tools/agy_run.py` and its modes.
- Note compatibility alias in `tools/antigravity_execute_ipd.py`.

## Open questions

### OQ-01: Default mode when positional argument is supplied without mode flags

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Auto-detect in order: (1) if matches pending plan path/id6 -> `ipd`; (2) if matches `.spec.md` -> `spec`; (3) if existing file -> `file`; (4) otherwise -> `prompt`. Can always be explicitly overridden with `--ipd`, `--spec`, `--file`, or `--prompt`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Unit tests verify CLI argument parsing and target resolution for `ipd`, `spec`, `file`, and `prompt` modes, including auto-detection, error reporting for nonexistent/ambiguous targets, and formatting of `--help` documentation with mode descriptions and invocation examples.
  - Observed evidence: `AgyRunArgParseTests` and `AgyRunTargetResolutionTests` in `tools/test_agy_run.py` pass (14 unit tests). Running `python3 tools/agy_run.py --help` prints complete usage and examples with exit code 0.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Unit tests verify default model is `gemini-3.7-flash-high`, `--model` override is accepted, `--session-id` / `-s` / `-c` attaches to explicit conversation, `--new-session` / `-n` starts fresh session, `--continue` resumes latest, `--timeout` is passed to agy command, and `--no-audit`/`--audit-only` alter turn execution flow as expected.
  - Observed evidence: `AgyRunArgParseTests.test_session_continuity_flags`, `test_runtime_and_model_options`, and `test_validation_turn_controls` verify all session and runtime flags.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Unit tests verify that Turn-1 preambles are loaded correctly for each mode, contain required diligence instructions (falsifiable tests, wiring symbols, actual output), and fall back to built-in defaults if prompt files are missing.
  - Observed evidence: `AgyRunPromptBuilderTests` in `tools/test_agy_run.py` verifies Turn-1 prompt construction for `ipd`, `spec`, `file`, and `prompt` modes against `tools/awphysical/*.md`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Unit tests verify that Turn-2 skeptical audit prompts are generated correctly for each mode and include specific verification checklists (E/V evidence table for IPDs, spec coverage matrix for specs, diff and test checks for general prompts).
  - Observed evidence: `AgyRunPromptBuilderTests.test_build_turn2_prompt_ipd` and `test_build_turn2_prompt_spec` verify Turn-2 audit prompt synthesis with evidence requirements.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Unit tests with mocked subprocess verify two-turn execution: Turn 1 executes with Turn-1 prompt, streams output to `tmp/antigravity/`, parses `result`, and Turn 2 executes in the same session (`session_id=first_turn.conversation_id`) with the audit prompt.
  - Observed evidence: `AgyRunExecutionEngineTests.test_two_turn_execution_flow_mock` and `test_turn1_failure_halts_immediately` verify full two-turn execution flow, session ID propagation, and immediate halting on Turn 1 failure.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Unit tests verify `tools/antigravity_execute_ipd.py` forwards arguments to `tools/agy_run.py` in IPD mode and produces identical exit codes and outputs.
  - Observed evidence: `AntigravityExecuteIpdCompatibilityTests` in `tools/test_agy_run.py` verifies attribute exports and call delegation.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Full test suite `python3 -m unittest discover -s tools -t .` passes with all new unit tests in `tools/test_agy_run.py` green.
  - Observed evidence: `python3 -m unittest tools.test_agy_run tools.awphysical.test_awphysical_tools` ran 57 tests in 0.671s, all OK.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Execution contract and scope fence
When executed, this IPD MUST:
1. Touch ONLY files within the approved scope: `tools/agy_run.py`, `tools/antigravity_execute_ipd.py`, `tools/awphysical/` prompt files, `tools/test_agy_run.py`, `tools/awphysical/test_awphysical_tools.py`, and `tools/README.md`.
2. Ensure Turn 1 failures halt immediately and report the failure without executing Turn 2.
3. Keep `tools/antigravity_execute_ipd.py` as a 100% compatible delegation wrapper.
4. Run all unit tests with actual runner outputs pasted.
5. Commit only changed files path-scoped (`git commit -m msg -- <paths>`), never use `git add -A`, and never push.
6. Do NOT transition the plan to `executed/`; the human maintainer / orchestrator retains terminal transition authority.
