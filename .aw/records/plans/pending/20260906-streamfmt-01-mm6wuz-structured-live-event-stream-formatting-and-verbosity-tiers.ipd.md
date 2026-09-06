# IPD: Structured Live Event Stream Formatting and Verbosity Tiers

- Date: 2026-09-06
- Kind: child
- Concern: Live runner execution streams in OpenCode (`oc_runipd.py`) and Antigravity (`agy_runipd.py`) emit unadorned, generic tool lines that obscure what the model is doing: edits and writes omit line additions/deletions and patch stats; reads and search queries lack line and match context; `todowrite` emits a static item count rather than state transitions; and no tiered verbosity flags exist to filter stream noise or ensure consistent vertical column alignment.
- Scope: Define a canonical fixed-width (13-column) prefix grammar across all event types with vertically aligned text; track and format `todowrite` state transitions (created, progress with active/completed titles, and completion); extract and render `filediff` (+/- lines) and touched file sets for edits and writes; introduce verbosity tiers (`quiet`, default, `verbose` / `-v`, `debug` / `-vv`); wire the verbosity flags into both `oc_runipd.py` and `agy_runipd.py`; and pin behavior with comprehensive unit and golden tests.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py, tests/test_oc_runipd_cli.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: streamfmt
- Order: 1
- Highest E allocated: 07
- Author: Gabriele Fariello <gabriele.fariello@gmail.com>
- Id: mm6wuz

## Workflow history

- 2026-09-06 to-review (Gabriele Fariello <gabriele.fariello@gmail.com>): created review-ready IPD for structured stream formatting, verbosity tiers, and alignment.

## Goal

Provide clear, high-signal, vertically aligned live event streaming across both host runners (`oc_runipd` and `agy_runipd`), enabling operators to immediately see what code is modified, what tasks are progressing, and how tools are executing without terminal noise, controllable via tiered verbosity flags (`-v`, `-vv`, `--quiet`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fixed-width prefix formatting and column alignment

- [ ] E-01 In `agent_workflows/render_stream.py`, define the canonical fixed-width (13-column) prefix formatting for event stream lines: `◀ read:`, `▶ write:`, `✎ edit:`, `⌕ find:`, `☑ todo:`, `◇ diagost:`, `◈ reason:`, `↳ subagent:`, `❯ bash:`. Ensure label padding is computed on the uncolored text before ANSI escapes are applied, so following content begins at column 14 and is strictly vertically left-aligned.
  - Depends on: none
  - Expected outcome: every rendered event line aligns its payload text at column 14 regardless of glyph or label length.
  - Execution state: pending

### Task group 2: Structured state tracking for todos and diffs

- [ ] E-02 In `agent_workflows/render_stream.py`, extend `StreamTracker` to record prior `todowrite` item states (`todos: list[dict]`). Compute state transitions on incoming `todowrite` events: initialization (`initialized N tasks (X active, Y pending)`), progress (`[X/N done]: completed "<title>" -> active "<title>"`), and all-done (`all N tasks completed`). Render with `☑ todo:` and uniform color.
  - Depends on: E-01
  - Expected outcome: `todowrite` events clearly communicate task additions and completions rather than static counts.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/render_stream.py`, extract `filediff` (`additions`, `deletions`), line counts, and diagnostics metadata for `edit` and `write` tool events. Format edits as `✎ edit:      <path> (+<add>, -<del>)` and writes as `▶ write:     <path> (new file, <lines> lines)`. Track modified file paths in `StreamTracker.modified_files`.
  - Depends on: E-01
  - Expected outcome: file modifications display concrete diff statistics and accumulate in tracker state.
  - Execution state: pending

### Task group 3: Verbosity tiers and CLI wiring

- [ ] E-04 Implement tiered verbosity filtering in `render_event()` in `agent_workflows/render_stream.py`:
  - `quiet`: IPD banners, heartbeats, and fatal errors only.
  - `default` (level 0): bash commands, edits and writes with diff stats, todo transitions, subagent lifecycles, and diagnostics/errors. (Suppress `read` and `find` events to avoid terminal flooding).
  - `verbose` (level 1, `-v`): surface `read` (with line ranges and byte sizes) and `find` (`grep`/`glob` pattern and match counts).
  - `debug` (level 2, `-vv`): surface `reason` (thinking/thought snippets) and detailed diff hunks.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: operators can tune stream noise from quiet to detailed without code changes.
  - Execution state: pending

- [ ] E-05 Wire `-v` / `--verbose` (`action="count"`) into `agent_workflows/oc_runipd.py`: update `_add_output_mode_flags()`, store `verbosity` in run options and state, and pass `verbosity` to `render_event()`.
  - Depends on: E-04
  - Expected outcome: `aw oc run <target> -v` and `-vv` control streaming detail in the OpenCode driver.
  - Execution state: pending

- [ ] E-06 Wire aligned stream rendering and `-v` / `--verbose` into `agent_workflows/agy_runipd.py`: update `render_agy_event()` to use the 13-column aligned prefixes, extract relative file paths and execution stats, and add `-v` / `--verbose` CLI options to `build_parser()`.
  - Depends on: E-04
  - Expected outcome: `aw agy run <target> -v` and `-vv` produce identical structured formatting in the Antigravity driver.
  - Execution state: pending

### Task group 4: Suite verification and golden test synchronization

- [ ] E-07 Update the golden transcript in `tests/test_render_stream.py` to match the new 13-column aligned formatting, add unit test fixtures for todos, diff extraction, and verbosity filtering, and verify the entire test suite passes bare (`python3 -m pytest`).
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: `python3 -m pytest` passes completely with zero regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `_GOLDEN_EVENTS` in `tests/test_render_stream.py:179-194` pins rendered output byte-for-byte; updating the renderer requires updating the golden expectations.
- `Palette` in `agent_workflows/render_stream.py:27-100` wraps strings with ANSI escape sequences (`\033[...]` and `\033[0m`); applying padding after ANSI wrapping results in misaligned columns because `len()` includes the invisible escape bytes. Padding must happen before colorization, or via an ANSI-aware width helper (`_strip_ansi`).
- `_add_output_mode_flags()` in `agent_workflows/oc_runipd.py:7252-7269` currently configures `--quiet`, `--raw`, and default `clean` using a mutually exclusive group; `-v` / `--verbose` should complement `output_mode` or integrate smoothly with `output_mode="clean"`.
- `render_agy_event()` in `agent_workflows/agy_runipd.py:386-460` extracts `TargetFile` with `Path(...).name` (bare basename); converting this to relative path from workspace root provides meaningful context while keeping lines compact.
- East Asian Width and Unicode: all chosen glyphs (`◀`, `▶`, `✎`, `⌕`, `☑`, `◇`, `◈`, `↳`, `❯`) are 1 character in width. Formatting `<glyph> <label>:` padded to 13 characters gives exact column alignment across standard monospace terminals.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | OpenCode logs rich `tool_use` metadata including `filediff` (`additions`, `deletions`), diff patches, and diagnostics, but `render_event()` currently prints only generic titles. | `agent_workflows/render_stream.py:161-181` |
| F-2 | OpenCode logs `todowrite` tasks with descriptions, priority, and statuses, but currently renders only static counts (`10 todos`). | `agent_workflows/render_stream.py:165-170` |
| F-3 | Antigravity logs `write_to_file` and `replace_file_content` with full `TargetFile` paths, but `render_agy_event()` strips paths to basenames and omits diff metrics. | `agent_workflows/agy_runipd.py:426-439` |
| F-4 | Neither runner provides `-v` or `--verbose` flags to control streaming detail, offering only binary `--quiet` or default `clean`. | `agent_workflows/oc_runipd.py:7252-7269` |
| F-5 | Golden tests in `tests/test_render_stream.py` verify exact byte outputs of sample events; modifying line formats requires updating pinned test transcripts. | `tests/test_render_stream.py:179-215` |
| F-6 | Padded string width calculations must account for ANSI escape sequences to prevent visual gutter misalignment. | `agent_workflows/render_stream.py:140-145` |

## Proposed changes (ordered, validatable)

1. Implement 13-column aligned prefix formatting in `render_stream.py` (E-01).
2. Implement `todowrite` state transition tracking and formatting in `StreamTracker` (E-02).
3. Implement `edit`/`write` diff statistics extraction and modified file tracking (E-03).
4. Implement tiered verbosity filtering in `render_event()` (E-04).
5. Wire `-v` / `--verbose` flags into `oc_runipd.py` (E-05).
6. Wire aligned formatting and `-v` / `--verbose` into `agy_runipd.py` (E-06).
7. Synchronize golden tests and verify full suite with bare pytest (E-07).

## Deferred / out of scope (with reason)

- Multi-line drawer or foldout widgets in the bottom pinned `Statusline` are deferred to keep the change focused on the live stream and tracker counters.
- Interactive keyboard shortcuts to toggle verbosity dynamically at runtime are deferred to a separate terminal UX plan.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Unit tests for fixed-width prefix formatting and ANSI alignment in `tests/test_render_stream.py`.
- Unit tests for `todowrite` lifecycle transitions in `tests/test_render_stream.py`.
- Unit tests for diff stat extraction and file tracking in `tests/test_render_stream.py`.
- CLI flag parsing tests for `-v`, `--verbose`, and `-vv` in `tests/test_oc_runipd_cli.py` and `tests/test_agy_runipd_cli.py`.
- Full pytest suite execution without options: `python3 -m pytest`.

## Spec / documentation sync

- Update CLI help strings for `oc_runipd` and `agy_runipd` to document the `-v` / `--verbose` flags and their effects.

## Open questions

None. All formatting glyphs, column widths, and verbosity tiers were aligned during design discussion.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests in `tests/test_render_stream.py` asserting that each prefix string occupies exactly 13 visual columns prior to content and ANSI color codes do not disrupt column alignment.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Unit tests in `tests/test_render_stream.py` verifying state transitions across sequential `todowrite` events (empty, pending, in-progress, completed).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Unit tests in `tests/test_render_stream.py` verifying diff stat extraction, new file line counting, and tracking of modified file paths in `StreamTracker`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Unit tests in `tests/test_render_stream.py` verifying that event types are correctly surfaced or suppressed at each verbosity level.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: CLI parsing unit tests in `tests/test_oc_runipd_cli.py` asserting `-v`, `--verbose`, and `-vv` parse correctly to numeric verbosity levels 1 and 2.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Unit tests in `tests/test_agy_runipd_cli.py` verifying `render_agy_event()` produces conformant 13-column aligned lines and relative paths.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Output from a bare `python3 -m pytest` run demonstrating that all tests pass without regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

All work is self-contained within the runner stream rendering modules and their associated CLI flags and unit tests. Pre-execution review and approval via `aw plan-review` or human attestation is required before execution.
