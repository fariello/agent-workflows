# IPD: Compact stream prefixes: merge reason into think, rename subagent to child, and add tool fallback

- Date: 2026-09-07
- Kind: child
- Concern: Stream alignment, gutter width efficiency, and elimination of unpadded dynamic tool prefixes.
- Scope: In `agent_workflows/render_stream.py` and `agent_workflows/agy_runipd.py`, merge the dead `reason` prefix into `think`, rename `subagent` to `child` (`↳ child:`), and introduce a fixed `tool` prefix (`• tool:`) for unmapped tools. Shrink the stream gutter padding from 12 to 9 columns and ensure unmapped tool invocations always start their payload with `<tool_name>:`. Update all tests and golden transcripts across OpenCode and Antigravity runners.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py, tools/ipdrunner/test_runagy.py
- Item-Dependencies: executed:tlou48
- Status: executed
- Set: streamfx
- Order: 2
- Highest E allocated: 03
- Author: antigravity/gemini-2.5-pro
- Id: xs19dk

## Workflow history
- 2026-09-07 executed (antigravity/gemini-2.5-pro): compact stream prefixes, rename subagent to child, and add tool fallback
- 2026-09-07 approved (aw set, --by-human): approved by user: I'd go with child I think. Let's make all the changes.

- 2026-09-07 to-review (antigravity/gemini-2.5-pro): Completed review-ready IPD for stream prefix compaction and child/tool prefix updates.
- 2026-09-07 draft (antigravity/gemini-2.5-pro): created.

## Goal

Compact live runner stream output by retiring the unused `reason` prefix into `think`, renaming the 8-letter `subagent` to the 5-letter `child` (`↳ child:`), and introducing a fixed 4-letter `tool` prefix (`• tool:`) for unmapped tools. This reduces the maximum prefix length from 11 to 8, allowing the global gutter pad to shrink from 12 to 9 columns while guaranteeing that unmapped tools never push output out of column alignment.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Stream prefix compaction and width policy update

- [x] E-01 In `agent_workflows/render_stream.py`, update prefix tables, width policy, and unmapped tool handling.
  - In `EVENT_PREFIXES`: remove `"reason"`, replace `"subagent": "\u21b3 subagent:"` with `"child": "\u21b3 child:"`, and add `"tool": "\u2022 tool:"`.
  - In `EVENT_PREFIXES_ASCII`: remove `"reason"`, replace `"subagent": "\u21b3 subagent:"` with `"child": "\u21b3 child:"`, and add `"tool": "- tool:"`.
  - In `format_event_prefix()`: when `kind` is not found in the prefix table, fall back to `table["tool"]` instead of formatting an unpadded dynamic label.
  - In `TOOL_PREFIX_KIND`: map `"task": "child"`.
  - In `render_event()` for `etype == "tool_use"`: resolve unmapped tools to `kind = "tool"`, and ensure the payload begins with `<tool_name>: ` so the tool name is always explicit at the start of the payload column.
  - Update width policy docstrings to reflect the 5 East-Asian-Ambiguous glyphs (`◀`, `▶`, `◇`, `◈`, `•`) and 5 Narrow glyphs (`✎`, `⌕`, `☑`, `↳`, `❯`), with a derived pad of 9 columns.
  - Depends on: none
  - Expected outcome: Stream prefixes align to column 9, `subagent` displays as `↳ child:   `, and unmapped tools render with `• tool:    <tool_name>: ...`.
  - Execution state: performed

### Task group 2: Antigravity runner prefix and child event update

- [x] E-02 In `agent_workflows/agy_runipd.py`, update prefix kinds and child rendering.
  - In `agy_prefix_kind()`: fall back to `"tool"` instead of returning the dynamic tool name for unknown tools.
  - In `render_agy_event()` for `step_type == "subagent"`: use `format_event_prefix("child", pal, use_unicode, style=prefix_style)` and format text with `noun = "child" if count == 1 else "children"`.
  - Depends on: E-01
  - Expected outcome: Antigravity driver emits `↳ child:    <count> child(ren) <state>` and routes unmapped tools to `• tool:    `.
  - Execution state: performed

### Task group 3: Test suite and transcript synchronization

- [x] E-03 Update test assertions in `tests/test_render_stream.py` and `tools/ipdrunner/test_runagy.py`.
  - In `tests/test_render_stream.py`:
    - Update expected derived pad from 12 to 9.
    - Update `ambiguous` set in narrow table tests to `{"read", "write", "diag", "think", "tool"}`.
    - Update `test_reason_is_reserved_and_has_no_producer` to assert `reason` is retired and `think` is the sole thought prefix.
    - Update `GoldenByteIdenticalTests` transcript for pad 9.
    - Update `TodoTransitionTests` and `EditWritePayloadTests` assertions for pad 9.
    - Add tests asserting `child` and `tool` prefix formats and unmapped tool payload formatting.
  - In `tools/ipdrunner/test_runagy.py`:
    - Update `test_the_subagent_line_uses_the_shared_prefix` to assert `↳ child:` and `2 children done` with pad 9.
    - Verify all `AgyEventRenderTests` pass against pad 9.
  - Depends on: E-01, E-02
  - Expected outcome: All stream rendering unit tests across both runners pass cleanly with pad 9.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `EVENT_PREFIX_PAD` is dynamically derived as `max(len(p) for p in table.values()) + 1`. With `subagent` (11 chars) replaced by `child` (8 chars), the maximum prefix length drops from 11 to 8, yielding a pad of 9.
- Both `•` (U+2022) and `◈` (U+25C8) are East-Asian Ambiguous (`unicodedata.east_asian_width == "A"`), substituted by `-` and `~` in `EVENT_PREFIXES_ASCII`.
- `tools/ipdrunner/test_runagy.py` tests `render_agy_event` via re-export.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | `subagent` (`↳ subagent:`, 11 chars) was the single widest entry in `EVENT_PREFIXES`, forcing a 12-column gutter across all events. | `render_stream.py:128` |
| F-2 | `reason` is an unused speculative placeholder that duplicates `think`'s glyph (`◈`) without having any producer. | `render_stream.py:113-118` |
| F-3 | Unmapped tools currently construct dynamic labels (`• <tool>:`) that exceed the column pad for any tool name longer than 4 characters, breaking stream vertical alignment. | `render_stream.py:220` |
| F-4 | Replacing `subagent` with `child` (8 chars) and adding `tool` (7 chars) drops the maximum prefix length to 8 chars, shrinking the global gutter to 9 columns. | codepoint measurement |

## Proposed changes (ordered, validatable)

1. In `agent_workflows/render_stream.py`, remove `reason`, rename `subagent` to `child`, add `tool` fallback prefix, update `format_event_prefix` and `render_event` (E-01).
2. In `agent_workflows/agy_runipd.py`, update `agy_prefix_kind` fallback to `"tool"` and update subagent step rendering to `child` (E-02).
3. In `tests/test_render_stream.py` and `tools/ipdrunner/test_runagy.py`, update pad assertions, ambiguous glyphs set, and golden transcripts to match pad 9 (E-03).

## Deferred / out of scope (with reason)

- Modifying past session run logs in `.aw/records/runs/`: historical session logs are immutable records.

## Scope check

- Over-scope: none.
- Under-scope: none. Touches exactly the stream renderers and their test suites.

## Required tests / validation

- `tests/test_render_stream.py`
- `tools/ipdrunner/test_runagy.py`
- `python3 -m pytest tests/test_render_stream.py tools/ipdrunner/test_runagy.py -k AgyEventRenderTests`
- Bare suite: `python3 -m pytest`
- Pre-commit hooks clean pass.
- Leak check `aw sanitize --agent`.

## Spec / documentation sync

N/A. Internal stream display formatting; no specification changes required.

## Open questions

### OQ-01: How should the payload of an unmapped tool be formatted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Ensure the payload starts with `<tool_name>: ` so the operator immediately knows which tool was called, while the preface remains the constant `• tool:    `.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste python test output verifying `render_event` emits `↳ child:   ` for task events, `• tool:    <name>: ...` for unmapped tools, and derived pad is 9.
  - Observed evidence: Verified. python3 -c with render_event: pad: 9; task renders as '↳ child:  explore the codebase'; unmapped tool renders as '• tool:   ask_question: Pick branch'.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste python test output verifying `render_agy_event` emits `↳ child:    2 children done` and routes unmapped tools to `• tool:   `.
  - Observed evidence: Verified. python3 -c with render_agy_event: subagent renders as '↳ child:  2 children done'; unmapped tool renders as '• tool:   custom_op'.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste pytest output showing all tests in `tests/test_render_stream.py` and `tools/ipdrunner/test_runagy.py -k AgyEventRenderTests` passing with pad 9.
  - Observed evidence: Verified. pytest tests/test_render_stream.py -> 81 passed; pytest tools/ipdrunner/test_runagy.py -k AgyEventRenderTests -> 9 passed; pre-commit and aw sanitize clean.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY `agent_workflows/render_stream.py`, `agent_workflows/agy_runipd.py`, `tests/test_render_stream.py`, and `tools/ipdrunner/test_runagy.py`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit.
