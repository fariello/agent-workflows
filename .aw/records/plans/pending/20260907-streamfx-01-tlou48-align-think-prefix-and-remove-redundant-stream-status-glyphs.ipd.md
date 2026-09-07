# IPD: Align think prefix and remove redundant stream status glyphs

- Date: 2026-09-07
- Kind: child
- Concern: Stream alignment, clarity, and elimination of redundant status checkmarks in live runner output.
- Scope: In `agent_workflows/render_stream.py` and `agent_workflows/agy_runipd.py`, replace the unaligned bullet `• ` for `text` events with the padded `◈ think: ` prefix (ASCII `~ think:`), and remove the redundant leading status glyph gutter (`✓ `) from tool lines so they begin directly with their aligned tool prefix (`❯ bash:`, `☑ todo:`, `✎ edit:`). Update golden transcripts and unit tests across both hosts.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py, tools/ipdrunner/test_runagy.py
- Item-Dependencies: none
- Status: approved
- Set: streamfx
- Order: 1
- Highest E allocated: 03
- Author: antigravity/gemini-2.5-pro
- Id: tlou48
- Approval: 2026-09-07, human ("approved"): approved by user: Yes. Post haste.

## Workflow history
- 2026-09-07 approved (aw set, --by-human): approved by user: Yes. Post haste.

- 2026-09-07 to-review (antigravity/gemini-2.5-pro): Completed review-ready IPD aligning think prefix and removing redundant status glyphs.
- 2026-09-07 draft (antigravity/gemini-2.5-pro): created.

## Goal

Provide clean, consistent, and vertically aligned live streaming output across both OpenCode and Antigravity runners by rendering model thoughts as `◈ think: ` and eliminating redundant leading checkmark glyphs (`✓ `) in front of tool prefixes that already carry their own icon (`❯ bash:`, `☑ todo:`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Stream renderer update for think prefix and tool lines

- [ ] E-01 In `agent_workflows/render_stream.py`, add `think` to prefix tables and streamline event formatting.
  - In `EVENT_PREFIXES`, add `"think": "\u25c8 think:"` (`◈ think:`).
  - In `EVENT_PREFIXES_ASCII`, add `"think": "~ think:"`.
  - In `render_event()` for `etype == "text"`: format using `prefix = format_event_prefix("think", pal, use_unicode, style="cyan")` and return `f"{prefix}{text}"`.
  - In `render_event()` for `etype == "tool_use"`: remove the leading `{glyph} ` gutter. Format directly with `prefix = format_event_prefix(kind, pal, use_unicode, style=prefix_style)` and `head = f"{prefix}{payload}" if payload else prefix.rstrip()`, setting `prefix_style = "red"` if `status in ("error", "failed")` else `"bold"`.
  - In `render_event()` for `etype == "error"`: remove leading status glyph and format with `prefix = format_event_prefix("diag", pal, use_unicode, style="red"); return prefix + pal(_one_line(body, 300), "red")`.
  - Depends on: none
  - Expected outcome: `text` events render as `◈ think:    <text>` and tool events start directly with `❯ bash:    `, `☑ todo:    `, etc.
  - Execution state: pending

### Task group 2: Antigravity driver stream renderer update

- [ ] E-02 In `agent_workflows/agy_runipd.py`, streamline `render_agy_event` tool formatting.
  - In `render_agy_event()` for `step_type == "tool"`: remove `pal(glyph_char, glyph_color) + " "` from `head` so lines start directly with `format_event_prefix(kind, pal, use_unicode) + summary`.
  - Depends on: E-01
  - Expected outcome: `render_agy_event` emits lines starting directly with the tool prefix without redundant checkmark glyph.
  - Execution state: pending

### Task group 3: Test updates across both runners

- [ ] E-03 Update test suites in `tests/test_render_stream.py` and `tools/ipdrunner/test_runagy.py`.
  - In `tests/test_render_stream.py`:
    - Update `test_text_event_renders_narration` to assert `"\u25c8 think:".ljust(pad) + "Reading the plan."`.
    - Update `test_tool_use_renders_tool_and_title` to assert line starts with `\u276f bash:` without leading `\u2713 `.
    - Update `test_tool_use_derives_title_from_input_when_missing` to assert line starts with `\u25c0 read:` without leading `\u2026 `.
    - Update `_GOLDEN_EVENTS` transcript in `GoldenByteIdenticalTests` to match new format without leading status gutter and with `◈ think:`.
    - Add tests asserting `"think"` in `EVENT_PREFIXES` and `EVENT_PREFIXES_ASCII`, verifying correct derived pad and alignment.
  - In `tools/ipdrunner/test_runagy.py`:
    - Update `test_render_tool_step_active_and_done` assertions for `plain_active` and `plain_done` to assert lines start with `render_stream.EVENT_PREFIXES["bash"].ljust(self.pad)` without leading status glyph.
  - Depends on: E-01, E-02
  - Expected outcome: All targeted and full test suites pass cleanly.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `EVENT_PREFIX_PAD` is derived dynamically as `max(len(p) for p in table.values()) + 1`. Since `↳ subagent:` is 11 codepoints, `pad` is 12.
- `len("◈ think:")` is 8 codepoints, so adding `think` does not alter the maximum pad width (12 columns).
- `_GOLDEN_EVENTS` in `tests/test_render_stream.py` serves as the golden transcript oracle for stream rendering byte compatibility.
- `tools/ipdrunner/test_runagy.py` tests `render_agy_event` via re-export and lives outside default `testpaths`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Tool events currently prepend `✓ ` in front of prefixes like `❯ bash:` and `☑ todo:`, creating visually redundant stacked glyphs (`✓ ❯`, `✓ ☑`). | live runner logs and `render_stream.py:713` |
| F-2 | Model narration events (`etype == "text"`) currently render as `• <text>` using an unaligned bullet, breaking vertical column alignment. | `render_stream.py:601` |
| F-3 | `◈ think:` provides a dedicated, visually distinct icon (`◈`) for thoughts and aligns with the 12-column payload margin. | `render_stream.py:126` and prompt review |

## Proposed changes (ordered, validatable)

1. Add `"think"` to `EVENT_PREFIXES` and `EVENT_PREFIXES_ASCII` in `agent_workflows/render_stream.py`, and format `etype == "text"` with `think` prefix (E-01).
2. Remove leading `{glyph} ` gutter from `tool_use` and `error` in `agent_workflows/render_stream.py` (E-01).
3. Remove leading status glyph from tool steps in `agent_workflows/agy_runipd.py` (E-02).
4. Update unit tests and golden transcripts in `tests/test_render_stream.py` and `tools/ipdrunner/test_runagy.py` (E-03).

## Deferred / out of scope (with reason)

- Modifying past session run logs in `.aw/records/runs/`: historical session logs are immutable records.

## Scope check

- Over-scope: none.
- Under-scope: none. Touches exactly the stream renderers and their test suites.

## Required tests / validation

- `tests/test_render_stream.py`
- `tools/ipdrunner/test_runagy.py`
- `python3 -m pytest tests/test_render_stream.py tools/ipdrunner/test_runagy.py`
- Bare suite: `python3 -m pytest`
- Pre-commit hooks clean pass.
- Leak check `aw sanitize --agent`.

## Spec / documentation sync

N/A. Internal stream display formatting; no specification changes required.

## Open questions

### OQ-01: How should failed tool executions be distinguished without a leading status gutter?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Highlight the prefix and payload in red (`prefix_style="red"`), ensuring failures are immediately noticeable without cluttering normal completed operations with checkmarks.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste python test output verifying `render_event` emits `◈ think:    ` for text events and `❯ bash:    ` without `✓ ` for bash tool events.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste python test output verifying `render_agy_event` emits tool lines starting directly with the tool prefix.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste pytest output showing all tests in `tests/test_render_stream.py` and `tools/ipdrunner/test_runagy.py` passing, plus bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY `agent_workflows/render_stream.py`, `agent_workflows/agy_runipd.py`, `tests/test_render_stream.py`, and `tools/ipdrunner/test_runagy.py`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit.
