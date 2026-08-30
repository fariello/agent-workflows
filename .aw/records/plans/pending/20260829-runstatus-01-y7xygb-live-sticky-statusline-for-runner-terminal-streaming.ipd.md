# IPD: Live sticky statusline for runner terminal streaming

- Date: 2026-08-29
- Kind: child
- Concern: Live runner terminal streaming UX with persistent sticky statusline.
- Scope: Add Statusline renderer and timer in agent_workflows/render_stream.py, integrating clock, elapsed, idle activity, block progress bar [NN/MM], target setid:id6, cumulative cost, and formatted token metrics into runner terminal execution in oc_runipd.py and agy_runipd.py with clean non-TTY fallback and unit tests in tests/test_render_stream.py.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py
- Item-Dependencies: none
- Status: reviewed
- Set: runstatus
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: y7xygb

## Workflow history
- 2026-08-30 reviewed (antigravity): Plan review completed: verified exact statusline format, non-TTY fallback, and thread safety

- 2026-08-29 draft (antigravity): created.
- 2026-08-29 to-review (antigravity): authored complete plan.

## Goal

Add a persistent, live statusline to the bottom of runner terminal streaming (`aw oc runipd` / `aw agy runipd`) displaying local time, elapsed time, time since last activity, block progress bar with item counter `[NN/MM]`, target `<setid>:<id6>`, cumulative cost, and formatted token counts (`in`, `out`, `cache`), with seamless log event coordination and non-TTY fallback.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Core Statusline Formatter & Component in `agent_workflows/render_stream.py`

- [ ] E-01 Implement progress bar formatting and `Statusline` class in `agent_workflows/render_stream.py`.
  - Depends on: none
  - Expected outcome: `format_progress_bar(current, total)` returns `████████░░ 80% [4/5]`. `format_statusline(...)` produces `22:15:30 │ 14m22s (idle 3s) │ ████████░░ 80% [4/5] │ reposcfg:8h9lap │ $0.24 │ 24.5k in, 4.1k out, 88.2k cache` with no leading spaces. `Statusline` runs a 1Hz daemon timer to redraw in place via `\r\033[K` on TTY streams, tracks idle/elapsed duration, and coordinates `write_event` to clear/re-render above the statusline.
  - Execution state: pending

### Task group 2: Wire Statusline into `oc_runipd.py` and `agy_runipd.py`

- [ ] E-02 Wire `Statusline` into child execution loops in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-01
  - Expected outcome: Runner child execution instantiates and manages `Statusline` across turns, feeding item context (`setid`, `id6`, item index, total count) and token stream updates, routing event log lines through `statusline.write_event()`, with clean shutdown on completion, interrupt, or non-TTY fallback.
  - Execution state: pending

### Task group 3: Unit Tests and Regression Verification

- [ ] E-03 Add unit test coverage in `tests/test_render_stream.py` and verify full suite passes.
  - Depends on: E-02
  - Expected outcome: Tests verify progress bar edge cases, statusline formatting, thread lifecycle, `write_event` line management, and non-TTY safety. Full test suite passes clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Streaming rendering logic lives in `agent_workflows/render_stream.py` (`Palette`, `StreamTracker`, `render_event`, `format_tokens`).
- `StreamTracker` accumulates `input_tokens`, `output_tokens`, `cache_tokens`, and `cost`.
- Runners (`oc_runipd.py`, `agy_runipd.py`) execute child processes with `subprocess.Popen` and stream lines in real-time.
- Terminal outputs check `should_color(stream)` and `stream.isatty()` for TTY-specific ANSI handling.

## Findings

- Heartbeat currently prints periodic lines (`still working on ...`) every 15s to stderr, which scroll in the log rather than staying pinned at the bottom.
- A live statusline pinned at the bottom with `\r\033[K` provides continuous visibility into elapsed time, idle duration, overall run progress, item identity, and cost without polluting log history.
- When `render_event` outputs a line, clearing the statusline, printing the event with `\n`, and re-emitting the statusline prevents garbled or interlaced text.

## Proposed changes (ordered, validatable)

1. **`agent_workflows/render_stream.py`**:
   - Add `format_progress_bar(current: int, total: int, width: int = 10) -> str`.
   - Add `format_statusline(...)` generating the exact layout:
     `<HH:MM:SS> │ <elapsed>m<elapsed>s (idle <s>s) │ <bar> <pct>% [<N>/<M>] │ <setid>:<id6> │ $<cost> │ <in> in, <out> out, <cache> cache`.
   - Add `Statusline` class with 1Hz background timer, `touch()`, `update_item()`, `write_event()`, `clear()`, and context manager protocol.

2. **`agent_workflows/oc_runipd.py` & `agent_workflows/agy_runipd.py`**:
   - Instantiate `Statusline` in child turn loop, passing tracker and plan index.
   - Coordinate event streaming through `statusline.write_event()`.

3. **`tests/test_render_stream.py`**:
   - Test progress bar rendering (0%, 50%, 100%, 0/0).
   - Test statusline segment assembly and exact divider formatting.
   - Test event writing and stream clearing.

## Deferred / out of scope (with reason)

- Full-screen curses/TUI interface; simple ANSI statusline in standard stdout stream is lightweight, portable, and non-intrusive.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_render_stream.py -v`
- Full test suite `pytest`
- `aw sanitize --agent`
- Manual execution check of runner output formatting.

## Spec / documentation sync

- Inline docstrings in `render_stream.py`.

## Open questions

### OQ-01: Non-TTY fallback behavior

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: When `sys.stdout.isatty()` is False (e.g. piped or redirected to file), `Statusline` disables live `\r` redrawing and acts as a passive pass-through so log files remain clean without ANSI redraw noise.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests in `tests/test_render_stream.py` verify progress bar and statusline string formatting matching the exact spec.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Child execution in `oc_runipd` and `agy_runipd` successfully streams events and updates statusline without exceptions.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `pytest tests/test_render_stream.py -v` and full test suite pass with 0 failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

All work is bounded to runner progress stream rendering, terminal statusline, and tests.
