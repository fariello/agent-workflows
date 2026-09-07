# IPD: Suppress synthetic system protocol messages in run streams

- Date: 2026-09-06
- Kind: child
- Concern: Runner stream cleanliness and noise suppression during live unattended runs.
- Scope: Filter and sanitize LLM platform protocol placeholders matching `[System: Empty ...]` in `agent_workflows/render_stream.py` (for `oc_runipd.py`) and `agent_workflows/agy_runipd.py` (for `agy_runipd.py`), suppressing standalone placeholders completely and stripping prefixed placeholders while preserving real agent text.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: sysproto
- Order: 1
- Highest E allocated: 03
- Author: antigravity/gemini-2.5-pro
- Id: eqzd0h

## Workflow history

- 2026-09-06 to-review (antigravity/gemini-2.5-pro): Completed review-ready IPD suppressing synthetic system protocol messages.
- 2026-09-06 draft (antigravity/gemini-2.5-pro): created.

## Goal

Prevent synthetic LLM platform protocol placeholders (e.g. `[System: Empty message content sanitised to satisfy protocol]`) from cluttering live terminal streams in both OpenCode (`aw oc run`) and Antigravity (`aw agy run`) runners.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: shared helper in `render_stream.py` and OpenCode integration

- [ ] E-01 Implement `strip_system_protocol_messages` in `agent_workflows/render_stream.py` and hook it into `render_event`.
  Compile regex `_SYSTEM_PROTOCOL_MSG_RE = re.compile(r"\[System:\s*Empty\b[^\]]*\]", re.IGNORECASE)`.
  Define `strip_system_protocol_messages(text: str) -> str` to iteratively strip matching bracketed tokens until none remain (handling nested and chained placeholders), stripping surrounding whitespace.
  In `render_event`:
  - For `etype == "text"`: call `strip_system_protocol_messages` on `part.get("text")`. If the resulting text is empty, return `None`. Otherwise format with `pal("• ", "cyan") + _one_line(text, 400)`.
  - For `JSONDecodeError` fallback: if `strip_system_protocol_messages(line)` is empty, return `None`.
  - Depends on: none
  - Expected outcome: `render_event` suppresses pure placeholder text and strips prefixed placeholders from text events.
  - Execution state: pending

### Task group 2: Antigravity runner integration

- [ ] E-02 In `agent_workflows/agy_runipd.py`, import `strip_system_protocol_messages` from `agent_workflows.render_stream` and sanitize events in `render_agy_event`.
  - For `JSONDecodeError` fallback lines, if `strip_system_protocol_messages(line)` is empty, return `None`.
  - For text/message events or step updates containing message/text, strip placeholders; if empty, return `None`.
  - Depends on: E-01
  - Expected outcome: `render_agy_event` suppresses standalone placeholders and strips prefixed placeholders.
  - Execution state: pending

### Task group 3: test coverage

- [ ] E-03 Add comprehensive unit tests in `tests/test_render_stream.py` and `tests/test_agy_runipd_cli.py`.
  - Test all 20 discovered unique variants from `.aw/records/runs/` against `strip_system_protocol_messages`.
  - Test `render_event` returning `None` for standalone placeholder text events.
  - Test `render_event` stripping placeholder prefix and returning `• <real text>` when real agent text is attached.
  - Test `render_agy_event` suppressing standalone placeholders.
  - Depends on: E-01, E-02
  - Expected outcome: All new and existing tests pass cleanly; suite remains green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/render_stream.py` is the established host-neutral stream-rendering module shared between both `oc_runipd.py` and `agy_runipd.py`.
- `agy_runipd.py` already imports `_one_line`, `Palette`, `Statusline`, `Heartbeat`, etc. from `render_stream.py`.
- `render_event` returns `None` to indicate an event should not be rendered to the statusline / stdout.
- The 20 unique variants found in `.aw/records/runs/` all share the prefix `[System: Empty ` and end with `]`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | 20 unique variants of `[System: Empty ...]` exist in `.aw/records/runs/*/sessions/*.jsonl`. All appear inside `type: "text"` event parts (`part.text`). | ripgrep inspection of `.aw/records/runs/` |
| F-2 | Some stream events chain placeholders or attach placeholders as a prefix to genuine agent thoughts (e.g. `[System: Empty ...]\n\nNow let me look at...`). | sample examination of session jsonl files |
| F-3 | Standalone placeholders provide zero information to human or agent operators and should be suppressed (`return None`). Attached placeholders should have the placeholder stripped so the real message text displays cleanly. | analysis of `render_event` and `render_agy_event` |

## Proposed changes (ordered, validatable)

1. Add `strip_system_protocol_messages` in `agent_workflows/render_stream.py` and apply it in `render_event` (E-01).
2. Import and apply `strip_system_protocol_messages` in `agent_workflows/agy_runipd.py` `render_agy_event` (E-02).
3. Add unit tests for `strip_system_protocol_messages`, `render_event`, and `render_agy_event` covering all 20 variants and prefix stripping (E-03).

## Deferred / out of scope (with reason)

- Modifying historical run session records in `.aw/records/runs/`: deferred because historical session logs are immutable records of past executions.

## Scope check

- Over-scope: none.
- Under-scope: none. Touches only the two stream renderers and their respective test suites.

## Required tests / validation

- Unit tests in `tests/test_render_stream.py` verifying each of the 20 variants.
- Test in `tests/test_agy_runipd_cli.py` verifying `render_agy_event` behavior.
- Targeted tests: `python3 -m pytest tests/test_render_stream.py tests/test_agy_runipd_cli.py`.
- Pre-commit hooks clean pass.
- Leak check `aw sanitize --agent` clean pass.

## Spec / documentation sync

N/A. No spec or external user documentation changes required. Stream rendering noise suppression is an internal presentation enhancement.

## Open questions

### OQ-01: How to handle placeholders attached to real agent text?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Strip the placeholder prefix and display the genuine text, rather than suppressing the entire turn text.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste python test output verifying `strip_system_protocol_messages` and `render_event` behavior on sample placeholder inputs (both standalone returning None and prefixed returning stripped text).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste python test output verifying `render_agy_event` returns None on sample placeholder lines.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste pytest output for `tests/test_render_stream.py` and `tests/test_agy_runipd_cli.py` passing, plus bare `python3 -m pytest` test summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY `agent_workflows/render_stream.py`, `agent_workflows/agy_runipd.py`, `tests/test_render_stream.py`, and `tests/test_agy_runipd_cli.py`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit.
