# IPD: Raw SGR escapes in pwatch, runners_monitor and render_stream honor color_depth

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `y11p5u` (filed during plan `lv0dvv` / backlog `cvtg9u`, reclassified `bug` by the maintainer on 2026-10-12 with ruling "color_depth=none must turn off ALL color"): plan `lv0dvv` made the generic `Term` styling axis (`Term.colorize`, `Term.color256`, and all `Term` helpers built on them) honor `term.resolve_color_depth`, but three modules still emit hard-coded SGR literals gated only on a boolean `color_enabled` / `color` / `enabled` flag instead of the resolved depth tier. Measured at HEAD `f4d434a6a` in this lane with an isolated `XDG_CONFIG_HOME` and `TERM=xterm-256color`: at both `color_depth=none` and `color_depth=16`, `pwatch.render_snapshot` emits 16 escapes including 8 `38;5;` sequences, `runners_monitor.render_runner_table` emits 24 escapes including 7 `38;5;` sequences, `render_stream.Palette(True)("boom", "red", "bold")` emits 2 escapes at pin `none`, `render_stream.make_badge` emits 6 `38;5;` sequences, `render_stream.format_stop_badge` emits 3 `38;5;` and 1 `48;5;` sequences, `render_stream.format_tally_badge` emits 4 `38;5;` sequences, and `render_stream.format_statusline_lines` emits 101 escapes including 72 `38;5;` and 2 `48;5;` sequences. In addition, `tests/test_term.py` (`LifecycleColorDepthSeamSweepTests` and `LifecycleColorDepthCrossSurfaceCliTests`) still carries the now-stale F-08 / `cvtg9u` docstring caveat that `lv0dvv` deferred to `y11p5u`.
- Scope: IN: route the 256-color and SGR styling in `agent_workflows/pwatch.py`, `agent_workflows/runners_monitor.py`, and `agent_workflows/render_stream.py` (`Palette.__call__`, `make_badge`, `format_stop_badge`, `format_tally_badge`, `format_statusline_lines`, and `format_run_summary_box`) through `term.resolve_color_depth` and `term.color_16_for_index` so pin `none` emits zero ANSI SGR escapes, pin `16` (and unpinned 16-color terminals such as `TERM=vt100`) emits 16-color SGR codes with zero `38;5;` or `48;5;` sequences, and pin `256` stays byte-identical to today; reword the two stale F-08 / `cvtg9u` docstrings in `tests/test_term.py`; add behavioral tests in `tests/test_generic_color_depth.py`; and add one `CHANGELOG.md` entry. OUT: any change to `agent_workflows/term.py` or `agent_workflows/lifecycle_style.py`; terminal cursor/screen control CSI sequences (`ENTER_ALT_SCREEN`, `LEAVE_ALT_SCREEN`, `CURSOR_HOME`, `CLEAR_LINE`, `CLEAR_TO_EOS`, `_CURSOR_HIDE`, `_CURSOR_SHOW`, `\033[3A\r\033[K`) which are interactive screen controls gated on TTY interactivity rather than SGR color codes.
- Scope-Paths: agent_workflows/pwatch.py, agent_workflows/runners_monitor.py, agent_workflows/render_stream.py, tests/test_term.py, tests/test_generic_color_depth.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- From-Backlog: y11p5u
- Blocks-Release: next
- Work-Kind: bug
- Priority: low
- Set: y11p5u
- Order: 1
- Highest E allocated: 05
- Author: antigravity
- Id: 32fso3

## Workflow history
- 2026-10-14 to-review (aw set): authored from backlog y11p5u

- 2026-10-14 draft (antigravity): created.

## Goal

Make `pwatch`, `runners_monitor`, and `render_stream` headers, badges, statusline, run summary box, and `Palette.__call__` honor the `color_depth` configuration pin and 16-color terminal detection (`term.resolve_color_depth` and `term.color_16_for_index`), so `color_depth=none` emits zero ANSI SGR escapes across all three modules, `color_depth=16` (and unpinned 16-color terminals) emits basic 16-color SGR escapes with no `38;5;` or `48;5;` sequences, and `color_depth=256` remains byte-identical to today, while retiring the stale F-08 / `cvtg9u` caveat from `tests/test_term.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: capture the baseline

- [ ] E-01 Capture the pre-edit test baseline before modifying any file: run the targeted suite `python3 -m pytest tests/test_term.py tests/test_generic_color_depth.py tests/test_runners_monitor.py tests/test_statusline_behavior.py tests/test_statusline_stop_tally.py tests/test_run_summary_table.py -o addopts=""` and the bare suite `python3 -m pytest`, recording the summary line and any failing node ids. (Measured at authoring in this lane: the 6-file targeted run passes `181 passed in 36.57s`.) The post-change bar is zero regressions relative to this baseline.
  - Depends on: none
  - Expected outcome: recorded summary lines and failing-node-id lists for both the 6-file targeted run and the bare suite.
  - Execution state: pending

### Task group 2: route raw SGR literals through `term.resolve_color_depth` and `term.color_16_for_index`

- [ ] E-02 In `agent_workflows/pwatch.py` and `agent_workflows/runners_monitor.py`, replace hard-coded `38;5;` SGR literals with depth-resolved SGR formatting backed by `term.resolve_color_depth` and `term.color_16_for_index`:
  1. In `agent_workflows/pwatch.py`, keep `C_RESET = "\033[0m"`, `C_BOLD = "\033[1m"`, and `C_DIM = "\033[2m"`, and replace the 18 module-level `38;5;` string constants (`C_TREE` through `C_ARG_TEXT`) with integer palette index constants (`IDX_TREE = 241`, `IDX_AGY = 48`, `IDX_AGENT = 177`, `IDX_PYTHON = 75`, `IDX_SHELL = 208`, `IDX_TOOL = 221`, `IDX_PROC_DEFAULT = 255`, `IDX_PID = 245`, `IDX_COUNT = 220`, `IDX_PARENT = 141`, `IDX_THREAD = 139`, `IDX_THREAD_TAG = 242`, `IDX_BANNER = 39`, `IDX_RECORD = 203`, `IDX_TIMESTAMP = 244`, `IDX_ARG_FLAG = 117`, `IDX_ARG_PATH = 186`, `IDX_ARG_TEXT = 252`, plus `IDX_RUNNER_DEC = 81`).
  2. Add `_effective_depth(color_enabled: bool, *, depth: str | None = None) -> str` (returning `term.DEPTH_NONE` when `not color_enabled`, `depth` when `depth in term.COLOR_DEPTHS`, else `term.resolve_color_depth(override=True)`) and `sgr_256(code: int, *, bold: bool = False, depth: str | None = None) -> str` (resolving `tier = term.resolve_color_depth(override=True) if depth is None else depth`; returning `""` at `term.DEPTH_NONE`, `f"\033[{'1;' if bold else ''}{term.color_16_for_index(n)}m"` at `term.DEPTH_16`, and `f"\033[{'1;' if bold else ''}38;5;{n}m"` at `term.DEPTH_256`).
  3. Thread optional keyword-only `*, depth: str | None = None` through `ansi_truncate`, `get_process_color`, `format_colored_argument`, `format_arguments`, `process_label`, `render_group`, and `render_snapshot`, resolving `tier = _effective_depth(color_enabled, depth=depth)` once in `render_snapshot` (and as the fallback in each function when called directly) so `tier == term.DEPTH_NONE` takes the plain uncolored branch (emitting no `C_DIM`, `C_RESET`, or `sgr_256` escapes) and `tier == term.DEPTH_16` emits 16-color SGR codes with no `38;5;`. In `pwatch.main`, resolve `depth = term.DEPTH_NONE if args.no_color else term.resolve_color_depth(sys.stdout)` and `color_enabled = depth != term.DEPTH_NONE`, and format `runner_decorations[pid]`, `rec_banner`, and `header` using `sgr_256(..., depth=depth)` and `render_snapshot(..., depth=depth)`.
  4. In `agent_workflows/runners_monitor.py`, update `render_runner_table` to resolve `depth = pwatch._effective_depth(color_enabled)` and `styled = depth != term.DEPTH_NONE`, gating `r`, `bold`, and `dim` on `styled` and formatting `c_pid` (`pwatch.IDX_PID`), `c_step` (`81`), `c_set` (`186`), `c_id6` (`220`, `bold=True`), `c_act` (`214`), `c_cpu_high` (`203`, `bold=True`), `c_cpu_mid` (`215`), and `c_activity` (`255`) via `pwatch.sgr_256(..., depth=depth)`. In `run_table_dashboard`, resolve `depth = term.DEPTH_NONE if getattr(args, "no_color", False) else term.resolve_color_depth(sys.stdout)` and `color_enabled = depth != term.DEPTH_NONE`, and format `c_banner` (`pwatch.IDX_BANNER`, `bold=True`) and `c_time` (`pwatch.IDX_TIMESTAMP`) via `pwatch.sgr_256(..., depth=depth)`.
  - Depends on: E-01
  - Expected outcome: at pin `none` on a capable TTY, `pwatch.render_snapshot(..., color_enabled=True)`, `pwatch.get_process_color`, `pwatch.format_colored_argument(..., True)`, `pwatch.main`, `runners_monitor.render_runner_table(..., color_enabled=True)`, and `runners_monitor.run_table_dashboard` emit zero `\033` escapes; at pin `16` (and unpinned `TERM=vt100`) they emit 16-color SGR escapes with zero `38;5;` sequences; at pin `256` they are byte-identical to HEAD.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/render_stream.py`, route `Palette.__call__`, `make_badge`, `format_stop_badge`, `format_tally_badge`, `format_statusline_lines`, and `format_run_summary_box` through the resolved color depth tier:
  1. In `Palette.__call__`, after `if not self.enabled or not styles: return text`, add `if self.lifecycle_term().lifecycle_depth() == _T.DEPTH_NONE: return text` so event/severity styling turns off at pin `none`; update `Palette`'s docstring accordingly.
  2. Add module-private helpers `_effective_color_depth(color: bool, *, pal: Palette | None = None, depth: str | None = None) -> str` (returning `_T.DEPTH_NONE` when `not color`, `depth` when `depth in _T.COLOR_DEPTHS`, `pal.lifecycle_term().lifecycle_depth()` when `pal is not None`, else `_T.resolve_color_depth(override=True)`), `_sgr256(code: int, *, bold: bool = False, depth: str = _T.DEPTH_256) -> str`, `_sgr_bg256(code: int, *, depth: str = _T.DEPTH_256) -> str` (returning `""` at `DEPTH_NONE`, `f"\033[{_T.color_16_for_index(n) + 10}m"` at `DEPTH_16`, and `f"\033[48;5;{n}m"` at `DEPTH_256`), and `_sgr_dark_fg(depth: str = _T.DEPTH_256) -> str` (returning `""` at `DEPTH_NONE`, `"\033[1;30m"` at `DEPTH_16`, and `"\033[38;5;16;1m"` at `DEPTH_256`; see OQ-01).
  3. In `make_badge`, `format_stop_badge`, and `format_tally_badge`, accept optional keyword-only `depth: str | None = None`, resolve `tier = _effective_color_depth(color, depth=depth)` and `styled = tier != _T.DEPTH_NONE`, and replace all raw `38;5;` and `48;5;` literals with `_sgr256`, `_sgr_bg256`, and `_sgr_dark_fg` at `depth=tier` (returning `(plain, plain)` when `not styled`).
  4. In `format_statusline_lines`, resolve `tier = _effective_color_depth(pal is not None and pal.enabled, pal=pal)` and `color_enabled = tier != _T.DEPTH_NONE`; pass `depth=tier` to `format_stop_badge`, `make_badge`, and `format_tally_badge`; and replace all raw `38;5;` and `48;5;` literals (`bdr_color`, `bg_frame`, `fg_frame`, `fg_dark`, `c_dim_run`, `b_blue`, `b_clock`, `b_bar`, `b_target`, `b_cost`, `b_warn`, `c_variant_color`, `c_data`, `dim_hdr`) with `_sgr256`, `_sgr_bg256`, and `_sgr_dark_fg` at `depth=tier`.
  5. In `format_run_summary_box`, change `color = pal.enabled` to `color = pal.enabled and pal_term.lifecycle_depth() != _T.DEPTH_NONE` so the summary box's banner/header SGR codes (`c_bold`, `c_cyan`, `c_green`, `c_yellow`, `c_red`, `c_reset`) are suppressed at pin `none`.
  - Depends on: E-01
  - Expected outcome: at pin `none` on a capable TTY, `Palette(True)("boom", "red", "bold")`, `make_badge`, `format_stop_badge`, `format_tally_badge`, `format_statusline_lines`, and `format_run_summary_box` emit zero `\033` escapes; at pin `16` (and unpinned `TERM=vt100`) they emit 16-color SGR escapes with zero `38;5;` and zero `48;5;` sequences while preserving statusline rectangularity and `_strip_ansi(styled) == plain`; at pin `256` they are byte-identical to HEAD.
  - Execution state: pending

### Task group 3: docstring sync, behavioral tests, and changelog

- [ ] E-04 Reword the two stale residual-exposure docstrings in `tests/test_term.py` and add `RawLiteralColorDepthTests` in `tests/test_generic_color_depth.py`:
  1. In `tests/test_term.py`, update bullet `1.` of `LifecycleColorDepthSeamSweepTests` and bullet `1.` of `LifecycleColorDepthCrossSurfaceCliTests` (and the `# Cell 3 (none tier)` comment in `test_cross_surface_cli_color_depth_ladder`) to remove `"generic axis ... ignores the depth pin entirely per finding F-08, tracked in carrier backlog item cvtg9u"` and `"ignores color_depth per F-08 (tracked in backlog item cvtg9u)"`, rewording them to state that those two classes scope their assertions to the lifecycle axis while the generic `Term` axis (`lv0dvv` / `cvtg9u`) and the out-of-`Term` raw-literal surfaces covered by `y11p5u` (`pwatch`, `runners_monitor`, and `render_stream` headers, statusline, and `Palette.__call__`) are guarded in `tests/test_generic_color_depth.py`.
  2. In `tests/test_generic_color_depth.py`, add `RawLiteralColorDepthTests(_DepthTestBase)` with behavioral tests (no source inspection, per P16):
     - `test_pwatch_color_depth_ladder`: exercises `get_process_color`, `format_colored_argument` (flag, path, text), `render_snapshot` (populated tree with parent, collapsed group, threads, runner decorations, truncated width, plus empty-match fallback), and `pwatch.main(["--once", ...])` on `_FakeTTY()` (both pattern mode and `--runners` mode) across pins `none` (0 `\033`), `16` (`\033[` present, 0 `38;5;`), `256` (`38;5;` present and matching 256-color bytes), `NO_COLOR=1` at pin `256` (0 `\033`), and unpinned `TERM=vt100` (`\033[` present, 0 `38;5;`).
     - `test_runners_monitor_color_depth_ladder`: exercises `render_runner_table` (high/mid/low CPU rows) and `run_table_dashboard` (`--once` on `_FakeTTY()`) across pins `none` (0 `\033`, words intact), `16` (`\033[` present, 0 `38;5;`), `256` (`38;5;` present), `NO_COLOR=1` at pin `256` (0 `\033`), and unpinned `TERM=vt100` (`\033[` present, 0 `38;5;`).
     - `test_render_stream_headers_statusline_and_palette_color_depth_ladder`: exercises `Palette(True)("boom", "red", "bold")`, `format_event_prefix("bash", pal=Palette(True))`, `make_badge`, `format_stop_badge` (levels `1..4` and `"custom"`, Unicode and ASCII), `format_tally_badge` (`failed=0` and `failed=1`, Unicode and ASCII), `format_statusline_lines` (with `model`, `variant`, `stop_level=1`, `items_passed=2`, `items_failed=1`, `cwd`, `run_id`, `activity="executing"`, `stall_remaining=120.0`, Unicode and ASCII), and `format_run_summary_box` across pins `none` (0 `\033`, `colored == plain`), `16` (`\033[` present, 0 `38;5;` and 0 `48;5;`, 4-line single visible width, `_strip_ansi(styled) == plain`), `256` (`38;5;` and `48;5;` present, byte-identical to 256-color output), and unpinned `TERM=vt100` (`\033[` present, 0 `38;5;` and 0 `48;5;`).
  - Depends on: E-02, E-03
  - Expected outcome: `python3 -m pytest tests/test_generic_color_depth.py tests/test_term.py -o addopts=""` passes; with E-02 and E-03 temporarily reverted, `tests/test_generic_color_depth.py` still collects and all three `RawLiteralColorDepthTests` methods fail individually.
  - Execution state: pending

- [ ] E-05 Add one `- Fixed:` bullet at the top of the `## 2.0.0 (pending)` change list in `CHANGELOG.md`: `aw pwatch`, `aw runners`, and runner stream headers, statuslines, event prefixes, and run summaries now honor the `color_depth` pin and 16-color terminal detection, so `none` removes all ANSI color escapes from those surfaces and `16` uses basic 16-color ANSI codes instead of 256-color sequences; write no em or en dashes (user-facing prose rule).
  - Depends on: E-02, E-03
  - Expected outcome: one new `- Fixed:` bullet under `## 2.0.0 (pending)` in `CHANGELOG.md`, containing no em or en dashes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Single color-depth resolver (`agent_workflows/term.py`, `term.resolve_color_depth` and `Term.lifecycle_depth`): spec `uonrjg` R9.3a.2 mandates a single definition of color depth across the package (`none`, `16`, `256`), where Rung 1 (`should_color`) outranks Rung 2 (the user's `color_depth` pin), Rung 3 (`COLORTERM`/`TERM` detection), and Rung 4 (`DEFAULT_COLOR_DEPTH = "256"`).
- Single derived 256->16 generic reduction (`agent_workflows/term.py`, `term.color_16_for_index`): added by executed plan `lv0dvv` with a chroma guard so saturated xterm-256 indices map to basic 16-color SGR codes without collapsing to gray.
- Import boundary on `agent_workflows/render_stream.py` (documented at `render_stream.resolve_item_lifecycle`): `render_stream` imports `term as _T` and `lifecycle_style as _LS` (and `run_selection_policy`), and must not import `pwatch` or `runners_monitor`.
- Behavioral tests only (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES` P16): never inspect source text; drive the functions and CLI entry points and assert on returned/printed strings and exit codes.
- Run the test suite bare as `python3 -m pytest` (`AGENTS.md` repo-local development contract); use `-o addopts=""` only when collecting per-file counts on a narrowed subset.
- User-facing prose (`CHANGELOG.md`) must contain no em or en dashes.
- Commit via `aw commit 32fso3 -- <paths>`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | `pwatch.py`, `runners_monitor.py`, and `render_stream.py` ignore `color_depth` at pins `none` and `16`. | Lane reproduction probe at HEAD `f4d434a6a` (`TERM=xterm-256color`, isolated `XDG_CONFIG_HOME`): at both `color_depth=none` and `color_depth=16`, `pwatch.render_snapshot` emits 16 escapes (8 `38;5;`), `runners_monitor.render_runner_table` emits 24 escapes (7 `38;5;`), `Palette(True)("boom", "red", "bold")` emits 2 escapes, `make_badge` emits 6 `38;5;`, `format_stop_badge` emits 3 `38;5;` and 1 `48;5;`, `format_tally_badge` emits 4 `38;5;`, and `format_statusline_lines` emits 101 escapes (72 `38;5;`, 2 `48;5;`). |
| F-02 | `render_stream.py` grew from 14 `38;5;` occurrences at `3ecef6088` to 29 `38;5;` and 6 `48;5;` occurrences at `f4d434a6a`, plus `format_run_summary_box` gating 16-color banner escapes on `pal.enabled` alone. | Commits `64109615f` and `e80098654` added `format_stop_badge`, `format_tally_badge`, the top-right CWD pill (`bg_frame`/`fg_frame`/`fg_dark`), and `c_dim_run` in `render_stream.format_statusline_lines`. In `render_stream.format_run_summary_box`, `color = pal.enabled` leaves `c_bold`/`c_cyan`/`c_green`/`c_yellow`/`c_red` active when `pal.lifecycle_term().lifecycle_depth()` is `DEPTH_NONE`. |
| F-03 | The two Powerline pill badges in `render_stream.py` (`format_stop_badge` and the CWD tab in `format_statusline_lines`) use `48;5;N` background codes and `\033[38;5;16;1m` dark foreground text, where naive `term.color_16_for_index(16)` returns `31` (red). | Direct probe of `term.color_16_for_index`: `214 -> 33`, `196 -> 31`, `67 -> 36`, `16 -> 31` (because `_CANDIDATE_16_RGB` omits black `30`). Mapping `48;5;N` at `DEPTH_16` to `color_16_for_index(N) + 10` (`43`, `41`, `46`) and `\033[38;5;16;1m` to `\033[1;30m` avoids red-on-red collision on stop level 3/4 while keeping `DEPTH_256` byte-identical. |
| F-04 | Threading the resolved `depth` from `Palette.lifecycle_term().lifecycle_depth()` in `format_statusline_lines` avoids per-call config I/O in hot statusline sweeps. | `tests/test_statusline_behavior.py` (`TestStatuslineBoxInvariants`) constructs `pal_styled = rs.Palette(True)` once and renders hundreds of combinations (and 31,104 renders in the `@pytest.mark.slow` sweep). Reading `pal.lifecycle_term().lifecycle_depth()` reuses the `Term` already cached on `pal._term` and passes `depth=tier` to `make_badge`, `format_stop_badge`, and `format_tally_badge`, adding zero filesystem reads inside the loop. |
| F-05 | No test or module outside `pwatch.py` and `runners_monitor.py` references `pwatch.C_*`. | Repo-wide scan across `agent_workflows/` and `tests/` for `C_RESET`, `C_BOLD`, `C_DIM`, and all 18 `C_*` 256-color constants in `pwatch.py`: only `pwatch.py` and `runners_monitor.py` reference them. |

## Proposed changes (ordered, validatable)

1. Capture the 6-file targeted baseline and full bare `python3 -m pytest` baseline (E-01).
2. Replace raw `38;5;` constants and gating in `agent_workflows/pwatch.py` and `agent_workflows/runners_monitor.py` with `sgr_256` and `_effective_depth` routed through `term.resolve_color_depth` and `term.color_16_for_index` (E-02).
3. Route `Palette.__call__`, `make_badge`, `format_stop_badge`, `format_tally_badge`, `format_statusline_lines`, and `format_run_summary_box` in `agent_workflows/render_stream.py` through `_effective_color_depth`, `_sgr256`, `_sgr_bg256`, and `_sgr_dark_fg` (E-03).
4. Reword the two stale F-08 / `cvtg9u` docstrings in `tests/test_term.py` and add `RawLiteralColorDepthTests` in `tests/test_generic_color_depth.py` with negative-control verification (E-04).
5. Add one `- Fixed:` entry to `CHANGELOG.md` (E-05).

## Deferred / out of scope (with reason)

- Terminal cursor and alternate-screen control sequences (`pwatch.ENTER_ALT_SCREEN`, `pwatch.LEAVE_ALT_SCREEN`, `pwatch.CURSOR_HOME`, `pwatch.CLEAR_LINE`, `pwatch.CLEAR_TO_EOS`, `render_stream._CURSOR_HIDE`, `render_stream._CURSOR_SHOW`, and `Statusline` cursor-up/erase-line `\033[3A\r\033[K`): these are interactive terminal layout controls gated on `isatty()`, not SGR color/style escapes (`\033[...m`), and are outside `color_depth`.
  - Carrier-Declined: non-color CSI cursor/screen controls are orthogonal to the color_depth ladder by contract

## Scope check

- Over-scope: none. `agent_workflows/term.py` and `agent_workflows/lifecycle_style.py` are not modified; only the three raw-literal modules, the two test files, and `CHANGELOG.md` are touched.
- Under-scope: none. Every `38;5;` and `48;5;` site in `pwatch.py`, `runners_monitor.py`, and `render_stream.py`, plus `Palette.__call__`, `format_run_summary_box`, and the two `tests/test_term.py` docstrings named in `y11p5u`, are covered.

## Required tests / validation

- `python3 -m pytest tests/test_generic_color_depth.py tests/test_term.py tests/test_runners_monitor.py tests/test_statusline_behavior.py tests/test_statusline_stop_tally.py tests/test_run_summary_table.py -o addopts=""` passes.
- Negative control: temporarily revert `agent_workflows/pwatch.py`, `agent_workflows/runners_monitor.py`, and `agent_workflows/render_stream.py` (via a patch file under `/tmp`, never `git stash`), run `python3 -m pytest tests/test_generic_color_depth.py -k RawLiteralColorDepthTests -o addopts=""`, confirm the file collects and all three test methods fail, then re-apply the patch.
- Bare `python3 -m pytest`: no node id fails that was not in the E-01 baseline.
- `aw ipd lint` on this plan conforms at `pre-transition` before the terminal move.

## Spec / documentation sync

- Spec `uonrjg`: N/A, not amended (this plan brings the remaining non-`Term` surfaces into conformance with DECISIONS D42 and the `color_depth` config contract).
- `CHANGELOG.md`: one `- Fixed:` bullet under `## 2.0.0 (pending)` (E-05).
- `tests/test_term.py`: docstrings of `LifecycleColorDepthSeamSweepTests` and `LifecycleColorDepthCrossSurfaceCliTests` updated as requested in `y11p5u` (E-04).

## Open questions

### OQ-01: How should the `48;5;N` background and `\033[38;5;16;1m` dark-foreground pill badges in `render_stream.py` degrade at `DEPTH_16`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence (F-03). Commits `64109615f` and `e80098654` added Unicode pill badges in `format_stop_badge` and `format_statusline_lines` using `48;5;214` / `48;5;196` / `48;5;67` backgrounds and `\033[38;5;16;1m` dark foreground text. Calling `term.color_16_for_index(16)` directly returns `31` (red) because `_CANDIDATE_16_RGB` lists only non-black foreground SGR codes, which would produce unreadable red-on-red text on urgent stop pills (`196 -> 31`). Therefore `_sgr_bg256` maps `code` at `DEPTH_16` to `term.color_16_for_index(code) + 10` (standard ANSI 16-color background offset: `214 -> 43`, `196 -> 41`, `67 -> 46`) and `_sgr_dark_fg` maps `\033[38;5;16;1m` at `DEPTH_16` to `\033[1;30m` (bold black) and at `DEPTH_NONE` to `""`, while keeping `DEPTH_256` byte-identical.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted summary line of the 6-file targeted `python3 -m pytest ... -o addopts=""` run and pasted final summary line (plus any `FAILED` node-id list) of the bare `python3 -m pytest` baseline run before any edit.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/pwatch.py agent_workflows/runners_monitor.py` pasted; plus pasted output of a `python3 -c` probe (isolated `XDG_CONFIG_HOME`, `TERM=xterm-256color`) exercising `pwatch.render_snapshot(..., color_enabled=True)` and `runners_monitor.render_runner_table(..., color_enabled=True)` at pins `none`, `16`, and `256`, showing `esc=0` at `none`, `esc>0` and `38;5=0` at `16`, and `38;5>0` (matching the pre-change counts `esc=16 38;5=8` and `esc=24 38;5=7`) at `256`. The code paths producing the observation are `pwatch.render_snapshot` -> `pwatch._effective_depth` -> `pwatch.sgr_256` and `runners_monitor.render_runner_table` -> `pwatch._effective_depth` -> `pwatch.sgr_256` (E-02).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff agent_workflows/render_stream.py` pasted; plus pasted output of a `python3 -c` probe (isolated `XDG_CONFIG_HOME`, `TERM=xterm-256color`) exercising `Palette(True)("boom", "red", "bold")`, `make_badge`, `format_stop_badge`, `format_tally_badge`, `format_statusline_lines`, and `format_run_summary_box` at pins `none`, `16`, and `256`, showing `esc=0` at `none`, `esc>0` with `38;5=0` and `48;5=0` at `16`, and `38;5` / `48;5` counts matching the pre-change baseline at `256`. The code paths producing the observation are `render_stream.Palette.__call__`, `render_stream.make_badge`, `render_stream.format_stop_badge`, `render_stream.format_tally_badge`, `render_stream.format_statusline_lines`, and `render_stream.format_run_summary_box` -> `render_stream._effective_color_depth` (E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff tests/test_term.py` pasted showing the two updated docstrings in `LifecycleColorDepthSeamSweepTests` and `LifecycleColorDepthCrossSurfaceCliTests`; pasted output of `python3 -m pytest tests/test_generic_color_depth.py tests/test_term.py tests/test_runners_monitor.py tests/test_statusline_behavior.py tests/test_statusline_stop_tally.py tests/test_run_summary_table.py -o addopts=""` showing all passed; pasted output of `python3 -m pytest tests/test_generic_color_depth.py -k RawLiteralColorDepthTests -o addopts=""` with E-02 and E-03 temporarily reverted showing 3 failed, followed by `git status --short` confirming the fix is restored; and pasted final summary line of the post-change bare `python3 -m pytest` run confirming no new failures relative to V-01.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff CHANGELOG.md` pasted showing the single added `- Fixed:` bullet under `## 2.0.0 (pending)`, and `git diff CHANGELOG.md | grep -nP '[\x{2013}\x{2014}]'` returning empty (exit 1).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract once approved:
- Perform E-01..E-05 in order; every open question is resolved.
- Scope fence: `- Scope-Paths:` lists `agent_workflows/pwatch.py`, `agent_workflows/runners_monitor.py`, `agent_workflows/render_stream.py`, `tests/test_term.py`, `tests/test_generic_color_depth.py`, and `CHANGELOG.md`. Do not modify `agent_workflows/term.py` or `agent_workflows/lifecycle_style.py`.
- Honesty: paste the ACTUAL command and test runner output into each `V-*`; never claim a pass you did not run.
- Commit only your own Scope-Paths files via `aw commit 32fso3 -- <paths>`; never `git add -A`, never push.
- Lifecycle transition: under `aw oc run` / `aw agy run` the runner finalizes and moves the plan; do not run `aw ipd finalize` yourself there. In a hand execution, run `aw ipd finalize 32fso3` once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`. Never hand-roll a `git mv` to `executed/` and never hand-edit `- Status:`.
