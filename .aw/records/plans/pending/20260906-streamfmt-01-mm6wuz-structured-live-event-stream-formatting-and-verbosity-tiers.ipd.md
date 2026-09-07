# IPD: Structured Live Event Stream Formatting and Verbosity Tiers

- Date: 2026-09-06
- Kind: child
- Concern: Live runner execution streams in OpenCode (`oc_runipd.py`) and Antigravity (`agy_runipd.py`) emit unadorned, generic tool lines that obscure what the model is doing: edits and writes omit line additions/deletions and patch stats; reads and search queries lack line and match context; `todowrite` emits a static item count rather than state transitions; and no tiered verbosity flags exist to filter stream noise or ensure consistent vertical column alignment.
- Scope: Define a canonical fixed-width (13-column) prefix grammar across all event types with vertically aligned text; track and format `todowrite` state transitions (created, progress with active/completed titles, and completion); extract and render `filediff` (+/- lines) and touched file sets for edits and writes; introduce verbosity tiers (`quiet`, default, `verbose` / `-v`, `debug` / `-vv`); wire the verbosity flags into both `oc_runipd.py` and `agy_runipd.py`; and pin behavior with comprehensive unit and golden tests.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py, tests/test_oc_runipd_cli.py, tests/test_agy_runipd_cli.py, tests/test_runner_stop_triggers.py, tools/ipdrunner/test_runagy.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: streamfmt
- Order: 1
- Highest E allocated: 12
- Author: Gabriele Fariello <gabriele.fariello@gmail.com>
- Id: mm6wuz
- Approval: 2026-09-06, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-07 executed (opencode its_direct/pt3-claude-opus-5-1m-us): implemented E-01..E-12; all twelve V-* verified with pasted runner output; `aw ipd lint --phase pre-transition` conforms. SUITE: bare `python3 -m pytest` -> `31 failed, 5563 passed, 3 skipped, 2 xfailed`. The 31 are PRE-EXISTING: a clean clone of HEAD 6091014c run bare gives `31 failed, 5505 passed` and the sorted FAILED sets are BYTE-IDENTICAL (diffed, empty), so zero regressions and +58 passing tests. `tools/ipdrunner/test_runagy.py -k AgyEventRender` 4 passed -> 9 passed, its 10 unrelated pre-existing failures unchanged and NOT touched. THREE self-inflicted regressions were found and fixed during execution: a second `save_state` call site broke the pinned per-runner count in `test_runner_shared` (both drivers now persist both display options through ONE call); `test_runner_stop_level3` indexed the exact `render_event(...)` call string that the new keyword arguments broke (re-anchored on the assignment prefix); and `test_reporting_contract` tripped on the HEAD-baseline clone sitting inside the tree (scratch removed, no code cause). Both OQs resolved as the plan delegated: OQ-01 KEEPS the status glyph beside the class prefix (a status carried only by COLOR would be invisible in a non-TTY transcript, which is where the 40 measured error events matter most); OQ-02 REMOVES `-v`/`--version` from the implicit-start set in BOTH drivers. E-08 KEPT `modified_files` with `render_run_summary_table` as its named reader (scopes match: both per-run). Five further decisions recorded in the run's decisions register; no DEFERRED question. CHANGELOG entry written (5 bullets, user-facing prose, no em/en dashes); `aw sanitize --agent` clean. Committed path-scoped, NOT pushed.

- 2026-09-06 approved (aw set): status set to approved

- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review; APPROVE WITH REVISIONS APPLIED; PR-001..PR-012. Structural lint conformed at `--phase author` and `--phase review-finalize`. Every claim was re-measured independently against 380 real session logs (98,401 events) under `.aw/records/runs/*/sessions/*.jsonl`. SIX material corrections. (1) PR-001, the one that would have shipped visibly broken output: FOUR of the nine chosen glyphs (`◀`, `▶`, `◇`, `◈`) are `unicodedata.east_asian_width == "A"` (AMBIGUOUS), not narrow, so the plan's conventions claim "all chosen glyphs are 1 character in width" is false for the property that matters; on any terminal resolving Ambiguous to double-width, exactly the `read`/`write`/`diagnostic`/`reason` prefixes shift by one column and the alignment the plan exists to deliver is lost. E-01 now fences padding to a stated-and-tested width policy and E-09 adds a narrow-glyph fallback with the ASCII precedent `use_unicode` already sets (`render_stream.py:476-483`). (2) PR-002: the plan's own prefix table does not fit 13 columns: `↳ subagent:` is 11 chars, `◇ diagost:` is a misspelling of `diagnostic`, and the correctly spelled `◇ diagnostic:` is EXACTLY 13, leaving zero separator before the payload. Widths corrected and the misspelling removed. (3) PR-003: `filediff` DOES NOT EXIST on `write` events; measured over 4,685 occurrences it is present on `edit` ONLY, and `write` carries `{diagnostics, filepath, exists, truncated}` with no line count at all, so E-03's `▶ write: <path> (new file, <lines> lines)` had no source field and the executor would have had to invent one. E-03 now derives the count from `input.content` and reads `metadata.exists` for the new-versus-overwrite distinction (measured 465 new / 15 overwrite). (4) PR-004: suppressing `read` and `find` at the default tier was justified as "avoid terminal flooding" but the measurement contradicts it: `read`+`grep`+`glob` are 7.9% of all `tool_use` (median 3 per session) while `bash`, which the plan KEEPS, is 69.7%. The stated rationale is removed and the tier is re-justified on signal, not volume. (5) PR-005: `-v` cannot be added as the plan describes. `"-v"` is a member of the implicit-start shim's `subcommands` set in BOTH drivers (`oc_runipd.py:7774`, `agy_runipd.py:4688`), so `aw oc run -v X` today reaches argparse as `["-v","X"]` WITHOUT `start` and fails `invalid choice: 'X'`, while `-vv` (not in the set) is rewritten correctly - measured, and a divergence a test in `tests/test_runner_stop_triggers.py:1018-1029` pins. E-05/E-06 now handle the shim and that structural test joined the fence. (6) PR-006: the golden transcript is not the only pinned renderer test. `tools/ipdrunner/test_runagy.py:30-101` asserts on `render_agy_event` output through the re-export shim and is OUTSIDE `testpaths = ["tests"]`, so a bare `python3 -m pytest` cannot see it and V-07 as written would have reported green over four broken assertions.

- 2026-09-06 to-review (Gabriele Fariello <gabriele.fariello@gmail.com>): created review-ready IPD for structured stream formatting, verbosity tiers, and alignment.

## Goal

Provide clear, high-signal, vertically aligned live event streaming across both host runners (`oc_runipd` and `agy_runipd`), enabling operators to immediately see what code is modified, what tasks are progressing, and how tools are executing without terminal noise, controllable via tiered verbosity flags (`-v`, `-vv`, `--quiet`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fixed-width prefix formatting and column alignment

- [x] E-01 In `agent_workflows/render_stream.py`, define the canonical fixed-width prefix formatting for event stream lines. The prefix set is `◀ read:`, `▶ write:`, `✎ edit:`, `⌕ find:`, `☑ todo:`, `◇ diag:`, `◈ reason:`, `↳ subagent:`, `❯ bash:`. Compute the padding on the UNCOLORED text before any ANSI escape is applied (or via an ANSI-aware width helper built on the existing `_strip_ansi`, `render_stream.py:92-93`), so the payload begins at a single fixed column for every prefix.
  - The pad width MUST be derived from `max(len(p) for p in PREFIXES) + 1`, computed in code from the prefix table itself rather than hardcoded as the literal `13`. Measured: the longest prefix in the set above is `↳ subagent:` at 11 codepoints, so 13 is correct today but silently wrong the moment a longer label is added; a derived constant cannot drift out of step with the table. A test MUST assert the derivation, not just the current value.
  - WIDTH POLICY, which this item must state in a code comment and a test must pin: padding is computed in CODEPOINTS (`len`) and is therefore exact only for glyphs that render single-width. Four of the nine glyphs (`◀` U+25C0, `▶` U+25B6, `◇` U+25C7, `◈` U+25C8) have `unicodedata.east_asian_width == "A"` (Ambiguous), meaning a terminal MAY render them double-width; the other five (`✎`, `⌕`, `☑`, `↳`, `❯`) are `"N"` (Narrow). See E-09 for the fallback that makes this honest rather than assumed. Do NOT restate the false claim that all nine are single-width.
  - Depends on: none
  - Expected outcome: every rendered event line aligns its payload at one derived column for all nine prefixes, the pad width is computed from the table, and the codepoint-versus-display-width limitation is documented in code rather than asserted away.
  - Execution state: performed

### Task group 2: Structured state tracking for todos and diffs

- [x] E-02 In `agent_workflows/render_stream.py`, extend `StreamTracker` to record prior `todowrite` item states (`todos: list[dict]`). Compute state transitions on incoming `todowrite` events: initialization (`initialized N tasks (X active, Y pending)`), progress (`[X/N done]: completed "<title>" -> active "<title>"`), and all-done (`all N tasks completed`). Render with `☑ todo:` and uniform color.
  - READ THE STATES FROM `state.metadata.todos`, not from `state.title`. Measured over 984 `todowrite` events: `title` is only ever the string `"<N> todos"` (top values `0 todos` x164, `1 todos` x124, `4 todos` x110), while `metadata.todos` is the full item list with keys exactly `{content, status, priority}` and `metadata.truncated` was `False` in 982 of 982 cases. `state.input.todos` carries the same list (0 length mismatches in 981 paired samples); prefer `metadata` and fall back to `input` so a metadata-less event still renders.
  - HANDLE THE FOUR REAL SHAPES the measurement found, so the formatter cannot raise or lie on live input: statuses observed are `completed` (3,438), `pending` (3,246), `in_progress` (837) and `cancelled` (4), so `cancelled` MUST be accounted for and MUST NOT be counted as done; and the count of `in_progress` items per event is NOT always 1 (measured 1 x797, 0 x169, 2 x10, 3 x4, 4 x2), so a format assuming exactly one active task is wrong for 185 of 984 events. State explicitly what renders for zero active and for multiple active.
  - THE TRACKER IS RUN-SCOPED, NOT ITEM-SCOPED. One `StreamTracker` is created per invocation (`oc_runipd.py:6899`) and passed to every item's turn (`:7051`), so `tracker.todos` persists ACROSS plans in a multi-item queue. Without a reset the first `todowrite` of item 2 is diffed against item 1's final list and renders a nonsense transition. Reset the todo state at turn start (or key it by session/item) and pin that with a test.
  - Depends on: E-01
  - Expected outcome: `todowrite` events communicate real transitions read from `metadata.todos`, handle `cancelled` and zero-or-many active items without raising, and do not leak state from a previous queue item.
  - Execution state: performed

- [x] E-03 In `agent_workflows/render_stream.py`, extract `edit` diff statistics and `write` file facts, and track modified file paths in `StreamTracker.modified_files`. Format edits as `✎ edit:` + `<path> (+<add>, -<del>)` and writes as `▶ write:` + `<path> (<new file|overwrote>, <lines> lines)`.
  - `filediff` EXISTS ON `edit` ONLY. Measured over every `filediff` occurrence in the corpus (4,685 dict-valued instances, 4,663 of them on the `edit` tool and ZERO on any other tool): `state.metadata.filediff` is a dict with keys exactly `{file, patch, additions, deletions}`, and `additions`/`deletions` are `int` in 4,685 of 4,685 cases (no string coercion needed). So the `(+<add>, -<del>)` form is sound for `edit`.
  - `write` HAS NO `filediff` AND NO LINE COUNT. Measured over 480 completed `write` events, `state.metadata` keys are exactly `{diagnostics, filepath, exists, truncated}` and `metadata.filediff` was `None` in 480 of 480. There is therefore no field the original `(new file, <lines> lines)` text could have come from. Derive the count from `state.input.content` (`content.count("\n")`, or splitlines) and take the new-versus-overwrite word from `metadata.exists` (measured `False` x465, `True` x15) rather than assuming every write is a new file. If `input.content` is absent, render the path with no count instead of guessing.
  - Read the path from `metadata.filediff.file` for `edit` and `metadata.filepath` for `write`, and render it RELATIVE to the repo root when it is inside it; both fields are absolute in the corpus, and an absolute path here is also a leak-sanitizer concern (`aw sanitize --agent`) if it ever reaches a shared artifact.
  - Note `metadata.diagnostics` is present on 5,165 events and NON-EMPTY on 3,160 of them (Pyright entries keyed by absolute path). Do not render diagnostics at the default tier from this item; E-04 owns which tier surfaces them.
  - Depends on: E-01
  - Expected outcome: edit lines carry real `additions`/`deletions` from `filediff`, write lines carry a content-derived line count and the correct new-versus-overwrite word, and no code path reads a `filediff` off a `write` event where the field does not exist.
  - Execution state: performed

- [x] E-08 Decide and implement what CONSUMES `StreamTracker.modified_files`, or do not add the field. As E-03 states it, the set is written and never read, and dead accumulating state is worse than none: it is one more thing to keep correct with no observable behavior proving it right.
  - The two defensible consumers already exist. `render_run_summary_table` (`render_stream.py:1047`) is the end-of-run box table both hosts call and already aggregates per-item cost/tokens/status; a "files touched" count or list belongs there. `Statusline` (`:597`) is the live 4-line box and could carry a count, but its columns are BYTE-PINNED by `test_format_statusline_user_example_box_layout` (`tests/test_render_stream.py:402-436`) which asserts exact border strings and equal line lengths, so adding a column there is a wider change than it looks; if that is the choice, say so and expect to re-pin that test.
  - THE SAME RUN-SCOPED LIFETIME PROBLEM AS E-02 APPLIES. One tracker serves the whole invocation (`oc_runipd.py:6899`, `:7051`), so `modified_files` accumulates across every plan in the queue. For a per-run total that is correct; for a per-item display it is wrong. State which one is intended.
  - If neither consumer is wanted in this plan, REMOVE the field from E-03 and record that decision, rather than landing unused state.
  - Depends on: E-03
  - Expected outcome: `modified_files` either has a named reader with a test asserting the rendered output, or it does not exist; and its accumulation scope is stated.
  - Execution state: performed

### Task group 3: Verbosity tiers and CLI wiring

- [x] E-04 Implement tiered verbosity filtering in `render_event()` in `agent_workflows/render_stream.py`:
  - `quiet`: IPD banners, heartbeats, and fatal errors only. NOTE this tier ALREADY EXISTS as `output_mode == "quiet"` and is implemented by NOT CALLING `render_event` at all (`oc_runipd.py:5651-5657` branches `raw`/`clean` and falls through for `quiet`). So `quiet` is not a `render_event` verbosity level; do not add a redundant second suppression path inside the renderer. State in code which layer owns `quiet`.
  - `default` (level 0): bash commands, edits and writes with diff stats, todo transitions, subagent lifecycles, and diagnostics/errors. Suppress `read` and `find`.
  - THE JUSTIFICATION FOR SUPPRESSING `read`/`find` IS SIGNAL, NOT VOLUME, and the plan must not claim otherwise. Measured across 380 sessions and 27,673 `tool_use` events: `read`+`grep`+`glob` are 7.9% of tool calls (median 3 per session, mean 5.7, max 53), while `bash`, which this tier KEEPS, is 69.7% (median 28, max 219), and `text` narration is 41.7% of all rendered lines. Hiding 7.9% while keeping 69.7% cannot be described as flood control. The defensible reason is that a read or a glob does not change the repository and is therefore low-signal for an operator watching for effects, whereas `bash` and `edit` are the mutating operations.
  - `verbose` (level 1, `-v`): surface `read` and `find`. For `read`, the available fields are `metadata.display.lineStart`/`lineEnd`/`totalLines`/`truncated` (present on 2,103 of 2,103 read events) and `input.offset`/`limit` (both present on 1,543 of 2,110, neither on 509). THERE IS NO BYTE SIZE ANYWHERE in the read payload (measured: zero occurrences of any `bytes`/`size`/`byteSize` field), so the original "byte sizes" requirement is unimplementable as stated and is replaced by the line range. For `find`, `grep` carries `metadata.matches` (47 events) and `glob` carries `metadata.count` (21 events); note these two field names DIFFER and a single lookup will silently render nothing for one of them.
  - `debug` (level 2, `-vv`): surface detailed diff hunks from `metadata.filediff.patch`, and the `metadata.diagnostics` payload. DO NOT promise a `reason`/thinking tier: there is no reasoning event in the corpus (event `type` values are exactly `text`, `tool_use`, `step_start`, `step_finish`, `error`; every `"reasoning"` string in the logs is the integer token-count field `"reasoning":0` inside `step_finish`). The `◈ reason:` prefix therefore has no producer today; either drop it from the table in E-01 or state in code that it is reserved and unreachable. Do not ship a documented flag whose effect cannot occur.
  - HANDLE THE `error` EVENT TYPE, which is currently dropped. `render_event` has no `error` branch, so a real observed event (`{"type":"error","error":{"name":"UnknownError","data":{"message":"The operation timed out."}}}`, 1 occurrence) renders as `None` and the operator sees nothing. This tier list claims "fatal errors only" at `quiet`, which is false while the renderer discards them. Render `error` at EVERY tier including `quiet`'s fallback path, or state explicitly that another layer reports it and cite that layer.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: operators can tune stream noise from quiet to detailed; every tier's promised content maps to a field proven to exist in the corpus; and no tier advertises an event class the renderer cannot produce.
  - Execution state: performed

- [x] E-05 Wire `-v` / `--verbose` (`action="count"`, `default=0`) into `agent_workflows/oc_runipd.py`: add it in `_add_output_mode_flags()` (`:7252`) so both `start` and `resume` get it (`:7514`, `:7572`), store `verbosity` in run options (beside `output_mode`, `:2981`) and in `state`, thread it through `execute_item`/`run_opencode` to the `render_event` call site (`:5655`), and persist it on resume the way `output_mode` already is (`:6843-6853`).
  - RESOLVE THE `-v` SHIM COLLISION FIRST; this is why the item cannot be a pure `add_argument`. `"-v"` is a member of the implicit-start `subcommands` set in `main()` (`oc_runipd.py:7774`), so a LEADING `-v` is treated as a subcommand and NOT prefixed with `start`. Measured at HEAD: `aw oc run -v somesetid` -> `runipd: error: argument command: invalid choice: 'somesetid'`, while `aw oc run -vv somesetid` (because `-vv` is not in the set) -> `runipd: error: unrecognized arguments: -vv`. So the two spellings fail DIFFERENTLY today and neither reaches `start`. Note also that `-v` is listed in that set as an abbreviation of `--version`, yet NEITHER driver registers a `--version` argument (measured: `parse_args(["--version"])` -> `unrecognized arguments: --version`, exit 2), so the set entry guards a flag that does not exist.
  - Choose ONE and say which in the code: (a) remove `"-v"`/`"--version"` from the `subcommands` set so the shim prefixes `start` and the new flag parses in both positions, or (b) keep `-v` reserved and make `--verbose` the only leading-position spelling. Option (a) is the smaller change but TOUCHES A STRUCTURALLY PINNED LITERAL: `tests/test_runner_stop_triggers.py:1018-1029` re-declares that exact set inline and `:994-1009` regexes `subcommands = \{(.*?)\}` out of BOTH driver sources, and the source comment at `oc_runipd.py:7768-7770` explicitly forbids hoisting the set into a constant. Whichever option is chosen, the two drivers MUST stay identical, because that regex test asserts parity across both files.
  - Depends on: E-04
  - Expected outcome: `aw oc run <target> -v` and `-vv` both parse to `verbosity` 1 and 2 and control streaming detail, in leading AND trailing argument position, with the shim collision resolved deliberately rather than by accident.
  - Execution state: performed

- [x] E-06 Wire aligned stream rendering and `-v` / `--verbose` into `agent_workflows/agy_runipd.py`: update `render_agy_event()` (`:386-464`) to use the shared aligned prefixes, extract repo-relative file paths (replacing the bare-basename `Path(...).name` at `:433-436`), and add `-v` / `--verbose` to `build_parser()` (`:4367`) plus the same `subcommands`-set resolution E-05 chose (`agy_runipd.py:4688`).
  - `render_agy_event` TAKES NO TRACKER and its signature is `(raw_line, pal)`. To reach parity with the oc renderer it needs the verbosity level and, for the E-02/E-03 state, a tracker; changing that signature is a public-ish change (the `tools/ipdrunner/runagy.py` shim re-exports every module attribute, `:29-31`). Add new parameters as KEYWORD arguments with defaults so existing two-argument calls keep working, and cite that shim as the reason.
  - THE AGY SCHEMA IS NOT THE OC SCHEMA and no agy event exists in the corpus to measure against (measured: zero `"event":"step_update"` lines in all 380 session logs; every log is OpenCode). Its fields are `event`/`step_update.state`/`step_update.tool_info.parameters` (`:414-439`) with `ACTIVE`/`DONE`/`ERROR` states, and the parameter names are `CommandLine`/`Query`/`AbsolutePath`/`TargetFile`/`Pattern`. There is NO `filediff` equivalent, so agy edit lines CANNOT carry `(+add, -del)`. State plainly which parts of the oc format are reachable here and which are not; do not promise "identical structured formatting" for a field the host does not emit. `duration_seconds` (`:445-447`) is agy-only and should be preserved.
  - Depends on: E-04
  - Expected outcome: `aw agy run <target> -v` and `-vv` parse identically to the oc driver, agy lines use the same prefixes and alignment, and the format differences forced by the agy schema are documented rather than claimed away.
  - Execution state: performed

### Task group 4: Display-width honesty and the alignment invariant

- [x] E-09 In `agent_workflows/render_stream.py`, add the narrow-glyph fallback that makes the E-01 width policy honest. Provide a non-Unicode (or narrow-safe) prefix table selected by the same kind of switch the statusline already uses: `format_statusline_lines` takes `use_unicode: bool = True` and swaps `╭┬╮│─` for `+|-` at `:476-483`, so the precedent, the parameter name, and the placement all exist. Route the four Ambiguous-width glyphs (`◀`, `▶`, `◇`, `◈`) through it.
  - Reuse the existing parameter spelling `use_unicode` rather than inventing a second flag, so a caller that already threads it for the statusline threads one concept, not two.
  - Depends on: E-01
  - Expected outcome: an operator on a terminal that renders Ambiguous-width glyphs double-width can get exact alignment, and the fallback is selected by the flag already used for this purpose.
  - Execution state: performed

- [x] E-10 Add the missing regression coverage for the padding-versus-ANSI interaction that the plan's own conventions section names as the failure mode. In `tests/test_render_stream.py`, assert that for EVERY prefix in the table, `len(_strip_ansi(rendered_prefix))` equals the derived pad width with color BOTH enabled and disabled, and that the colored and plain transcripts agree after stripping (the existing `test_colored_transcript_strips_back_to_plain`, `:242-248`, is the pattern to extend).
  - This is separate from E-07's golden update: the golden pins ONE transcript, while this pins the INVARIANT across all nine prefixes, which is what actually stops a future prefix addition from breaking alignment silently.
  - Depends on: E-01, E-09
  - Expected outcome: a padding regression fails a test naming the prefix that broke, rather than only shifting a golden diff.
  - Execution state: performed

### Task group 5: Suite verification and pinned-test synchronization

- [x] E-07 Update the golden transcript in `tests/test_render_stream.py` to match the new aligned formatting, add unit test fixtures for todos, diff extraction, and verbosity filtering, and verify the suite passes bare (`python3 -m pytest`).
  - THE GOLDEN IS THREE ASSERTIONS, NOT ONE. `_GOLDEN_EVENTS` (`:179-192`) feeds `test_plain_transcript_is_byte_identical` (`:215-227`), `test_driver_reexport_produces_identical_transcript` (`:229-240`) and `test_colored_transcript_strips_back_to_plain` (`:242-248`). The re-export test drives the SAME stream through `oc_runipd`'s re-exported names and compares the two, so it fails if the drivers diverge, not if the format changes; keep that property intact rather than re-pinning it to a new literal.
  - The current expected transcript is `• Reading the plan.` / `… bash: git status` / `✓ bash: git status` / `✗ edit: patch failed` / the raw non-JSON line. Note the pre-existing status glyphs `✓`/`✗`/`…`/`•` are ORTHOGONAL to the nine new prefixes and are not in E-01's table; state whether the new format keeps the status glyph, replaces it, or renders both, because the golden cannot be updated without deciding that.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-09, E-10, E-11, E-12
  - Expected outcome: `python3 -m pytest` passes completely with zero regressions, and all three golden assertions still assert something meaningful.
  - Execution state: performed

- [x] E-11 Update `tools/ipdrunner/test_runagy.py` for the E-06 format change. `AgyEventRenderTests` (`:18-101`) asserts on `render_agy_event` output through the `runagy.py` re-export shim: `test_render_tool_step_active_and_done` asserts `"run_command"` and `"pytest tests/ -v"` appear in the rendered line and that `"1.25s"` appears for the DONE case, and `test_render_init`/`test_render_result_*` pin the init and result lines.
  - THIS MODULE IS INVISIBLE TO THE BARE SUITE. `pyproject.toml:154` sets `testpaths = ["tests"]`, so `python3 -m pytest` never collects `tools/`; measured, a bare collect returns zero items from `tools/ipdrunner`. So V-07's bare run CANNOT prove this module green and the executor MUST run it explicitly: `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender` (measured `4 passed` at HEAD). Do NOT run the whole module as the pass criterion: its `AgyExecutionLifecycleTests` are ALREADY RED at HEAD (measured `10 failed, 10 passed`) for reasons unrelated to this plan, so a whole-module run cannot distinguish a regression this plan caused from pre-existing failure. Record the `-k AgyEventRender` count before and after.
  - Depends on: E-06
  - Expected outcome: the four render assertions outside `testpaths` are updated and shown green explicitly, and the pre-existing unrelated failures in the same file are reported rather than silently inherited or "fixed".
  - Execution state: performed

- [x] E-12 Update the structural `subcommands`-set test in `tests/test_runner_stop_triggers.py` to match the E-05 decision. `test_stop_is_listed_in_both_shims_subcommand_sets` (`:994-1009`) regexes `subcommands = \{(.*?)\}` out of both driver sources and asserts `"stop"` is present; `test_a_plain_selector_is_still_implicitly_started` (`:1011-1032`) RE-DECLARES the set inline as a literal, including `"-v"` and `"--version"`, and evaluates the shim against that copy.
  - If E-05 removes `"-v"`, that inline copy is now a stale duplicate that no longer describes the code, and the test keeps passing while asserting a set the drivers do not have. Update the copy and add an assertion that the shim now prefixes `start` for a LEADING `-v` (the behavior E-05 changes), so the fix has a regression guard in the same place the old behavior was pinned.
  - If E-05 instead keeps `-v` reserved, add an assertion that a leading `-v` is NOT rewritten and that `--verbose` is, so the deliberate asymmetry is pinned rather than left as a surprise.
  - Note this module is heavily `pytest.mark.slow` (`:540`, `:785`, `:857`, `:1127`, `:1511`, `:1757`) and `addopts` filters `-m 'not slow'` (`pyproject.toml:169`), BUT the two classes above are NOT marked slow (`ImplicitStartShimTests` at `:956`, `StopVerbSurfaceTests` at `:1035`), so they DO run in the bare suite. Confirm that by naming the count.
  - Depends on: E-05
  - Expected outcome: the structural parity test describes the drivers' actual `subcommands` sets and pins the new leading-flag behavior in both drivers.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `_GOLDEN_EVENTS` in `tests/test_render_stream.py:179-192` pins rendered output byte-for-byte; updating the renderer requires updating the golden expectations. It feeds THREE tests, not one (`:215`, `:229`, `:242`); see E-07.
- `Palette` in `agent_workflows/render_stream.py:70-89` wraps strings with ANSI escape sequences (`\033[...]` and `\033[0m`); applying padding after ANSI wrapping results in misaligned columns because `len()` includes the invisible escape bytes. Padding must happen before colorization, or via an ANSI-aware width helper (`_strip_ansi`, `:92-93`).
- `_add_output_mode_flags()` in `agent_workflows/oc_runipd.py:7252-7269` currently configures `--quiet`, `--raw`, and default `clean` using a mutually exclusive group; `-v` / `--verbose` should complement `output_mode` or integrate smoothly with `output_mode="clean"`. Note `quiet` is implemented by NOT CALLING `render_event` (`:5651-5657`), so it is a call-site decision, not a renderer level.
- `render_agy_event()` in `agent_workflows/agy_runipd.py:386-464` extracts `TargetFile` with `Path(...).name` (bare basename); converting this to relative path from workspace root provides meaningful context while keeping lines compact.
- DISPLAY WIDTH, corrected during review. It is NOT true that all nine glyphs are single-width. Measured with `unicodedata.east_asian_width`: `◀` (U+25C0), `▶` (U+25B6), `◇` (U+25C7) and `◈` (U+25C8) are `"A"` (AMBIGUOUS, terminal-dependent, commonly double-width in CJK-configured or East-Asian-font terminals); only `✎`, `⌕`, `☑`, `↳`, `❯` are `"N"` (Narrow). Padding by codepoint count is therefore exact for five of nine and terminal-dependent for four. E-09 owns the fallback; do not restate the original claim.
- PREFIX WIDTHS, measured. `◀ read:` 7, `▶ write:` 8, `✎ edit:` 7, `⌕ find:` 7, `☑ todo:` 7, `◈ reason:` 9, `↳ subagent:` 11, `❯ bash:` 7. The plan's original `◇ diagost:` (10) was a MISSPELLING of `diagnostic`; the correctly spelled `◇ diagnostic:` is EXACTLY 13, which would leave zero separator before the payload at a 13-column pad, so the label was shortened to `◇ diag:` (7). With the corrected table the longest prefix is 11 and a derived pad of 12 or 13 both work; E-01 requires the value be DERIVED from the table rather than hardcoded.
- `StreamTracker` LIFETIME IS RUN-SCOPED, not item-scoped: constructed once per invocation (`oc_runipd.py:6899`) and passed to every item (`:7051`) and to the end-of-run summary (`:7133`). Any new per-turn state added to it (E-02 todos, E-03 modified files) accumulates across queue items unless reset.
- `tools/ipdrunner/test_runagy.py` is a SECOND pinned renderer test and is OUTSIDE `testpaths = ["tests"]` (`pyproject.toml:154`), so a bare `python3 -m pytest` never collects it (measured: zero items from `tools/`). Ten of its twenty tests are ALREADY FAILING at HEAD for unrelated reasons (measured `10 failed, 10 passed`); the four render tests pass (`-k AgyEventRender` -> `4 passed`).
- The event vocabulary is exactly five `type` values, measured over 98,401 events in 380 session logs: `text` (39,580 part-events), `tool_use` (27,591), `step_start` (25,522), `step_finish` (25,500), `error` (1). There is NO reasoning/thinking event; `render_event` has no `error` branch, so the one real error event renders as `None` today.
- Tool mix, measured over 27,673 `tool_use` events: `bash` 19,289 (69.7%), `edit` 4,721 (17.1%), `read` 2,110 (7.6%), `todowrite` 984 (3.6%), `write` 488 (1.8%), `grep` 47, `glob` 21, `task` 11. Each `callID` appears EXACTLY ONCE (27,514 of 27,514 single-event calls) and status is `completed` 27,474 / `error` 40, so there is no start/finish pairing to correlate: a renderer sees one terminal event per tool call.
- Session logs under `.aw/records/runs/` are GITIGNORED (`.aw/.gitignore:14`, zero tracked files), so they are legitimate local evidence for measurement but MUST NOT be copied into a tracked test fixture verbatim: they contain absolute maintainer paths. Run `aw sanitize --agent` before treating any excerpt as shareable.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | OpenCode logs rich `tool_use` metadata including `filediff` (`additions`, `deletions`), diff patches, and diagnostics, but `render_event()` currently prints only generic titles. | `agent_workflows/render_stream.py:161-181` |
| F-2 | OpenCode logs `todowrite` tasks with descriptions, priority, and statuses, but currently renders only static counts (`10 todos`). | `agent_workflows/render_stream.py:165-170` |
| F-3 | Antigravity logs `write_to_file` and `replace_file_content` with full `TargetFile` paths, but `render_agy_event()` strips paths to basenames and omits diff metrics. | `agent_workflows/agy_runipd.py:426-439` |
| F-4 | Neither runner provides `-v` or `--verbose` flags to control streaming detail, offering only binary `--quiet` or default `clean`. | `agent_workflows/oc_runipd.py:7252-7269` |
| F-5 | Golden tests in `tests/test_render_stream.py` verify exact byte outputs of sample events; modifying line formats requires updating pinned test transcripts. | `tests/test_render_stream.py:179-215` |
| F-6 | Padded string width calculations must account for ANSI escape sequences to prevent visual gutter misalignment. | `agent_workflows/render_stream.py:140-145` |
| F-7 | CORRECTION to the original conventions claim: four of the nine glyphs are East Asian Width `"A"` (Ambiguous), not Narrow, so codepoint padding is terminal-dependent for `read`, `write`, `diag` and `reason`. Owned by E-09. | measured: `unicodedata.east_asian_width` for U+25C0/25B6/25C7/25C8 = `A`; U+270E/2315/2611/21B3/276F = `N` |
| F-8 | CORRECTION: `filediff` is present on `edit` ONLY. Measured 4,685 dict-valued `filediff` occurrences, 4,663 on `edit` and zero on any other tool; `write` metadata is `{diagnostics, filepath, exists, truncated}` with `filediff` `None` in 480 of 480 completed writes. The original E-03 write format had no source field. Owned by E-03. | 380 session logs under `.aw/records/runs/*/sessions/*.jsonl` (gitignored, local evidence) |
| F-9 | CORRECTION: `-v` is already a member of the implicit-start `subcommands` set in both drivers, so a LEADING `-v` is not prefixed with `start` and fails; `-vv` is not in the set and fails differently. Neither driver registers the `--version` the set entry guards. Owned by E-05/E-12. | `agent_workflows/oc_runipd.py:7774`; `agent_workflows/agy_runipd.py:4688`; measured `parse_args(["--version"])` -> exit 2 `unrecognized arguments` |
| F-10 | CORRECTION: `read` events carry NO byte size (measured zero `bytes`/`size`/`byteSize` fields over 2,110 read events); they carry `metadata.display.lineStart`/`lineEnd`/`totalLines`. `grep` reports `metadata.matches` and `glob` reports `metadata.count`, DIFFERENT field names. Owned by E-04. | 2,103 read events with `display` keys `{type, path, text, lineStart, lineEnd, totalLines, truncated}`; 47 grep + 21 glob events |
| F-11 | CORRECTION: the default tier's "avoid terminal flooding" rationale is contradicted by the data. `read`+`grep`+`glob` are 7.9% of tool calls (median 3/session) while the retained `bash` is 69.7% (median 28/session) and `text` narration is 41.7% of all rendered lines. Owned by E-04. | measured over 380 sessions, 27,673 `tool_use` events, 47,498 would-be rendered lines |
| F-12 | There is NO reasoning/thinking event in the stream, so the proposed `◈ reason:` prefix and the `-vv` "thinking snippets" tier have no producer. Every `"reasoning"` occurrence in the logs is the integer `"reasoning":0` token-count field inside `step_finish`. Owned by E-04. | measured `type` values: `text`, `tool_use`, `step_start`, `step_finish`, `error` only |
| F-13 | `render_event` silently drops the `error` event type (no branch, returns `None`), so the `quiet` tier's promise of "fatal errors only" is currently unbacked by the renderer. Owned by E-04. | `agent_workflows/render_stream.py:153-203`; one real `{"type":"error",...}` event observed |
| F-14 | `tools/ipdrunner/test_runagy.py:18-101` is a SECOND pinned renderer test invisible to the bare suite (`testpaths = ["tests"]`), and ten of its twenty tests are already red at HEAD for unrelated reasons. Owned by E-11. | `pyproject.toml:154`; measured `10 failed, 10 passed` whole-module, `4 passed` with `-k AgyEventRender` |
| F-15 | `StreamTracker` is constructed ONCE PER INVOCATION and shared by every queue item, so new per-turn state (E-02 todos, E-03 modified files) leaks across plans without an explicit reset. Owned by E-02 and E-08. | `agent_workflows/oc_runipd.py:6899`, `:7051`, `:7133` |

## Proposed changes (ordered, validatable)

1. Implement derived-width aligned prefix formatting in `render_stream.py` (E-01).
2. Implement `todowrite` state transition tracking and formatting in `StreamTracker`, read from `metadata.todos`, with a per-turn reset (E-02).
3. Implement `edit` diff-stat extraction and `write` content-derived line counts, with repo-relative paths (E-03).
4. Decide and implement a reader for `modified_files`, or drop the field (E-08).
5. Implement tiered verbosity filtering in `render_event()`, including the `error` branch (E-04).
6. Add the narrow-glyph fallback for the four Ambiguous-width glyphs (E-09).
7. Resolve the `-v` shim collision and wire `-v` / `--verbose` into `oc_runipd.py` (E-05).
8. Wire aligned formatting and `-v` / `--verbose` into `agy_runipd.py`, documenting the schema-forced format differences (E-06).
9. Add the all-prefix alignment invariant test (E-10).
10. Update `tools/ipdrunner/test_runagy.py` and run it explicitly (E-11).
11. Update the structural `subcommands`-set test in both drivers (E-12).
12. Synchronize the three golden assertions and verify the suite with bare pytest (E-07).

## Deferred / out of scope (with reason)

- Multi-line drawer or foldout widgets in the bottom pinned `Statusline` are deferred to keep the change focused on the live stream and tracker counters.
- Interactive keyboard shortcuts to toggle verbosity dynamically at runtime are deferred to a separate terminal UX plan.
- A TRUE display-width helper (a `wcwidth`-style table mapping every codepoint to 0/1/2 columns) is deferred. The repo has no such helper today (measured: zero occurrences of `east_asian_width`, `wcwidth`, or any `display_width` symbol outside this plan) and adding one is a general-purpose text-measurement facility, not a stream-formatting change. E-09's narrow-glyph fallback is the bounded fix; if a future item needs exact width for arbitrary user content, it should own that helper.
- Emitting a `reason`/thinking line is deferred because the host does not produce such an event today (F-12). If OpenCode later emits one, the reserved prefix is the place to add it.
- Fixing the ten pre-existing failures in `tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests` is OUT OF SCOPE: they are red at HEAD for reasons unrelated to rendering, and repairing them here would hide whether this plan's own change is clean. E-11 requires reporting their state, not fixing it.

## Scope check

- Over-scope: none.
- Under-scope: five gaps were found in review and are now IN scope as E-08 through E-12 (a reader for `modified_files`; the display-width fallback; the all-prefix alignment invariant; the out-of-`testpaths` agy render tests; the structural `subcommands` test that the `-v` change invalidates). `tests/test_runner_stop_triggers.py` and `tools/ipdrunner/test_runagy.py` were added to `Scope-Paths` because both pin behavior this plan changes.

## Required tests / validation

- Unit tests for derived-width prefix formatting and ANSI alignment in `tests/test_render_stream.py`, asserting the pad width is DERIVED from the prefix table and that every prefix satisfies the invariant with color on and off (E-10).
- Unit tests for `todowrite` lifecycle transitions in `tests/test_render_stream.py`, driven from `metadata.todos` and covering: initialization, one active, ZERO active, MULTIPLE active, a `cancelled` item, all-done, and a cross-item reset proving no leak from a previous plan's list.
- Unit tests for `edit` diff-stat extraction (`additions`/`deletions` as ints), `write` line counting from `input.content` with `exists` True and False, absent-`content` degradation, and repo-relative path rendering.
- Unit test that a `{"type":"error",...}` event renders a visible line rather than `None`.
- CLI flag parsing tests for `-v`, `--verbose`, and `-vv` in `tests/test_oc_runipd_cli.py` and `tests/test_agy_runipd_cli.py`, covering BOTH leading and trailing position (leading is the case that fails today, F-9), for `start` AND `resume`, and through the `aw oc run` / `aw agy run` wrapper as well as the driver directly.
- `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender` run EXPLICITLY, because `testpaths` excludes it (F-14). Baseline at HEAD is `4 passed`.
- Full pytest suite execution BARE: `python3 -m pytest`. Do not add `-n0`, a second `-q`, or `-p no:randomly`; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.
- HERMETICITY: every new test must construct its events INLINE as literals. Do NOT read `.aw/records/runs/` from a test: that tree is gitignored (`.aw/.gitignore:14`), absent in CI and in the runner's default isolated worktree, and contains absolute maintainer paths.

## Spec / documentation sync

- Update CLI help strings for `oc_runipd` and `agy_runipd` to document the `-v` / `--verbose` flags and their effects, in `_add_output_mode_flags()` (`oc_runipd.py:7252`) and `build_parser()` (`agy_runipd.py:4367`).
- If E-05 changes the leading-`-v` behavior, the `subcommands`-set comment at `oc_runipd.py:7768-7770` (and its agy twin) documents that set's contract and MUST be updated to say what `-v` now means; leaving it stale would mislead the next reader into re-adding the entry.
- CHANGELOG: this changes user-visible terminal output and adds two operator-facing flags, so it warrants a `CHANGELOG.md` entry. Write it in USER-FACING prose (no em or en dashes, per `CONTRIBUTING.md:142`). If the executor concludes no entry is warranted, say so explicitly with the reason rather than leaving it unaddressed.
- No spec under `.aw/records/specs/` governs stream rendering (searched; the runner specs cover stop levels, lane containment, and verification defaults, not display), so no spec amendment is required. State the paths checked at execution rather than asserting N/A.

## Open questions

### OQ-01: Does the type prefix keep, replace, or merge with the existing per-status glyph?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: The renderer already emits a STATUS glyph per tool event (`✓` completed, `✗` error, `…` running, `•` other; `render_stream.py:171-178`) and the golden pins it (`… bash: git status` then `✓ bash: git status`). The nine new prefixes encode TOOL CLASS, an orthogonal axis, so the two are not interchangeable and E-07 cannot re-pin the golden without a decision. Resolved to the executor rather than the maintainer because repository evidence settles the constraint: each `callID` produces EXACTLY ONE event (measured 27,514 of 27,514 single-event calls) with status `completed` in 27,474 cases and `error` in 40, so the status glyph carries almost no information in practice while the tool class carries all of it. Whichever the executor chooses, it MUST be stated in a code comment, applied uniformly to all nine prefixes, and reflected in the golden. Not escalated: both choices are implementable, testable, and reversible before release.

### OQ-02: Should `-v` stop being reserved in the implicit-start `subcommands` set?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: E-05 must pick one of two resolutions (remove `"-v"`/`"--version"` from the set so a leading `-v` is prefixed with `start`, or keep `-v` reserved and make `--verbose` the only leading spelling). Resolved to the executor from repository evidence: the set entry guards a `--version` flag that NEITHER driver actually registers (measured: `parse_args(["--version"])` exits 2 with `unrecognized arguments`), so the reservation currently protects nothing, which argues for removal. Not escalated as blocking because either choice is a one-literal edit in two files, is pinned by E-12, and is reversible. If the maintainer instead wants a real `--version` implemented, that is a separate item and this plan should keep `-v` reserved; say so in review of the executed result rather than blocking here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: PASTE the new test's output plus the derived pad width the code computes. Assert and show: (a) `len(_strip_ansi(prefix))` for all nine prefixes, each equal to the derived pad; (b) that the pad is computed from the prefix table (a test that changes the table and observes the pad change, or that asserts `PAD == max(len(p) for p in PREFIXES) + 1`), NOT a test that only compares against the literal 13; (c) the code comment stating the codepoint-versus-display-width limitation, quoted. A test asserting only `== 13` does NOT satisfy this item.
  - Observed evidence: (a) DERIVED PAD AND PER-PREFIX WIDTH, color OFF and ON. `format_event_prefix` pads the UNCOLORED
    label and appends the ANSI escape after, so the colored form strips back to the same width:

        $ python3 -c "print event_prefix_pad(True), max(len(p))+1, EVENT_PREFIX_PAD, and per-prefix widths"
        event_prefix_pad(True) = 12
        max(len(p))+1          = 12
        EVENT_PREFIX_PAD       = 12
        read      label_len= 7  plain=12  colored_stripped=12
        write     label_len= 8  plain=12  colored_stripped=12
        edit      label_len= 7  plain=12  colored_stripped=12
        find      label_len= 7  plain=12  colored_stripped=12
        todo      label_len= 7  plain=12  colored_stripped=12
        diag      label_len= 7  plain=12  colored_stripped=12
        reason    label_len= 9  plain=12  colored_stripped=12
        subagent  label_len=11  plain=12  colored_stripped=12
        bash      label_len= 7  plain=12  colored_stripped=12

    (b) THE PAD IS DERIVED, NOT COMPARED TO A LITERAL. Three assertions cover this and none is a bare
    `== 12`: `test_the_pad_is_derived_from_the_table_not_hardcoded` asserts `event_prefix_pad(u) ==
    max(len(p) for p in table.values()) + 1` for BOTH width policies,
    `test_the_pad_follows_the_table_when_the_table_changes` LENGTHENS the table and asserts the pad
    moves with it, and `test_the_invariant_BITES...` injects the defect (see V-10). The literal 12 is
    additionally asserted only as a MEASUREMENT of the current table (`max(len(p)) == 11`), so adding
    a longer label moves both sides together.

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q -k EventPrefixAlignment
        ........                                                                 [100%]
        8 passed, 69 deselected in 0.20s

    (c) THE CODE COMMENT stating the codepoint-versus-display-width limitation, quoted verbatim from
    `agent_workflows/render_stream.py`:

        # WIDTH POLICY, stated here because it is the one thing about this table that is NOT exact.
        # `EVENT_PREFIX_PAD` is computed in CODEPOINTS (`len`), so the payload column is exact only for
        # glyphs a terminal renders SINGLE-WIDTH. Measured with `unicodedata.east_asian_width`, four of
        # the nine glyphs are `"A"` (AMBIGUOUS, i.e. terminal-dependent and commonly double-width in a
        # CJK-configured terminal): U+25C0, U+25B6, U+25C7, U+25C8. The other five (U+270E, U+2315,
        # U+2611, U+21B3, U+276F) are `"N"` (Narrow). So do NOT claim every glyph is single-width: it is
        # false for four of them, and on a terminal that resolves Ambiguous to two columns exactly those
        # four rows shift by one column.

    `test_the_width_policy_limitation_is_documented_in_code` pins that the comment, and the
    `EVENT_PREFIXES_ASCII` fallback it names, stay present. NOTE the pad is 12 and not the plan's
    originally quoted 13: review corrected the misspelled `diagnostic` label to `diag`, leaving
    `subagent` at 11 as the longest, and E-01 requires the value be DERIVED rather than written.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE test output for SEVEN distinct `todowrite` cases, each rendered line quoted: initialization; exactly one `in_progress`; ZERO `in_progress`; TWO or more `in_progress`; a list containing a `cancelled` item (which must not be counted as done); all-done; and a cross-item RESET case proving item 2's first `todowrite` is not diffed against item 1's final list. Also show the source field used is `metadata.todos` (or the `input.todos` fallback), not `state.title`.
  - Observed evidence: SEVEN CASES, each rendered line quoted (payload column at 12, as V-01 pins):
        1 initialization             '/ todo:     initialized 3 tasks (1 active, 2 pending)'
        2 exactly one active         '/ todo:     [1/3 done]: completed "A" -> active "B"'
        3 ZERO active                '/ todo:     [2/3 done]: completed "B" -> no active task'
        4 TWO+ active (init)         '/ todo:     initialized 3 tasks (0 active, 3 pending)'
        4 TWO+ active                '/ todo:     [0/3 done]: active "A", "B"'
        5 cancelled (init)           '/ todo:     initialized 2 tasks (0 active, 2 pending)'
        5 cancelled NOT counted done '/ todo:     [0/2 done]: active "B"'
        6 all-done (init)            '/ todo:     initialized 2 tasks (1 active, 1 pending)'
        6 all-done                   '/ todo:     all 2 tasks completed'

        7 CROSS-ITEM RESET:
          item1 final                '/ todo:     initialized 2 tasks (1 active, 1 pending)'
          item2 WITHOUT reset        '/ todo:     [0/1 done]: active "item2-A"'
          item2 WITH begin_turn      '/ todo:     initialized 1 tasks (1 active, 0 pending)'

    (The status glyph and the todo glyph are transcribed as `/` above only to keep this record
    ASCII-safe for the leak-sanitizer; the live lines carry the real glyphs, and the byte-exact forms
    are pinned by the tests named below.)

    Case 5 is the one worth reading twice: a list of `[cancelled, in_progress]` renders `[0/2 done]`,
    NOT `all 2 tasks completed`, so a cancelled task is never reported as an accomplishment. Case 7
    shows the leak concretely: without `begin_turn()` item 2's FIRST event renders a transition diffed
    against item 1's list; with the reset the driver performs at turn start it renders an
    initialization.

    SOURCE FIELD is `metadata.todos`, NOT `state.title`. With `title="4 todos"` PRESENT on the event,
    the rendered line does not contain it, and `input.todos` is the documented FALLBACK when metadata
    is absent. Both are asserted by `test_source_is_metadata_todos_not_the_title` and
    `test_input_todos_is_the_fallback_when_metadata_is_absent`.

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q -k TodoTransition
        .............                                                            [100%]
        13 passed, 64 deselected in 0.20s

    The driver-side half (the reset is CALLED, not merely available) is pinned by
    `test_the_driver_resets_the_tracker_at_turn_start`; the call is in `run_opencode`, immediately
    before the child is spawned.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE test output covering: an `edit` event with int `additions`/`deletions` rendering `(+N, -M)`; a `write` with `metadata.exists` False rendering the new-file wording and a line count derived from `input.content`; a `write` with `exists` True rendering the overwrite wording; a `write` with NO `input.content` degrading to a path with no count rather than raising or printing a wrong number; and a path shown REPO-RELATIVE. Additionally show that NO code path reads `filediff` off a `write` event (F-8): a `write` fixture whose metadata omits `filediff` entirely must render correctly.
  - Observed evidence: edit int adds/dels   'edit:     agent_workflows/x.py (+12, -3)'
        write exists=False   'write:    new.py (new file, 3 lines)'
        write exists=True    'write:    old.py (overwrote, 2 lines)'
        write NO content     'write:    x.py (new file)'
        write NO filediff    'write:    y.py (new file, 1 lines)'
        repo-RELATIVE path   'edit:     tests/deep/nested/t.py (+1, -0)'

    (Glyphs elided from this record for sanitizer safety; the byte-exact forms are asserted in
    `EditWritePayloadTests`, which builds the expected prefix from `EVENT_PREFIXES`.)

    Row by row against what V-03 requires: `additions`/`deletions` arrive as `int` and render
    `(+12, -3)`; `metadata.exists` False renders the new-file wording with a count DERIVED from
    `input.content` (3 lines from a three-line string); `exists` True renders `overwrote`; with NO
    `input.content` the line degrades to a path and the correct word with NO count, rather than raising
    or printing a guessed number; and paths render repo-relative (an absolute `/repo/tests/deep/
    nested/t.py` becomes `tests/deep/nested/t.py`).

    THE `write NO filediff` ROW IS THE F-8 FIXTURE: its metadata is exactly the measured shape
    `{diagnostics, filepath, exists, truncated}` with `filediff` ABSENT ENTIRELY, and it renders
    correctly. Structurally, no executable line in the write formatter reads the field:

        write formatter EXECUTABLE code mentions filediff? False

    Measured on comment-and-docstring-stripped source via `ast.unparse`, so the docstring that EXPLAINS
    the absence does not satisfy the check; `test_no_code_path_reads_filediff_off_a_write` uses the
    same helper. A path OUTSIDE the repo is left absolute rather than truncated
    (`test_a_path_outside_the_repo_is_left_absolute_rather_than_truncated`).

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q -k "EditWritePayload or ModifiedFilesConsumer"
        ............                                                             [100%]
        12 passed, 65 deselected in 0.20s
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE a per-tier matrix showing, for each of levels 0/1/2, which event classes rendered and which returned `None`: `bash`, `edit`, `write`, `todowrite`, `read`, `grep`, `glob`, `task`, `text`, `error`. The `error` row MUST render at every level (F-13). For level 1, show the `read` line carrying a LINE RANGE (not a byte size, which does not exist, F-10) and show `grep` reading `metadata.matches` while `glob` reads `metadata.count`. For level 2, show a `filediff.patch` hunk and a `diagnostics` payload. Also state, with the `oc_runipd.py:5651-5657` citation, that `quiet` is owned by the call site and is not a renderer level.
  - Observed evidence: PER-TIER MATRIX. `RENDER` means a line was produced, `None` means the event was suppressed:
        event      | level 0  | level 1  | level 2
        bash       | RENDER   | RENDER   | RENDER
        edit       | RENDER   | RENDER   | RENDER
        write      | RENDER   | RENDER   | RENDER
        todowrite  | RENDER   | RENDER   | RENDER
        read       | None     | RENDER   | RENDER
        grep       | None     | RENDER   | RENDER
        glob       | None     | RENDER   | RENDER
        task       | RENDER   | RENDER   | RENDER
        text       | RENDER   | RENDER   | RENDER
        error      | RENDER   | RENDER   | RENDER

    THE `error` ROW RENDERS AT EVERY LEVEL, level 0 included. That is F-13: the branch did not exist
    before, so this real observed event rendered as `None` and the operator saw nothing.

        error at L0  : 'diag:     UnknownError: The operation timed out.'

    LEVEL 1 detail. `read` carries a LINE RANGE and no byte size (F-10: there is none anywhere in the
    payload), and `grep` reads `metadata.matches` while `glob` reads `metadata.count`, which are
    DIFFERENT field names:

        level1 read  : 'read:     c.py (lines 1-40 of 400)'
        level1 grep  : 'find:     grep foo (7 hits)'
        level1 glob  : 'find:     glob *.py (3 hits)'

    LEVEL 2 detail: the `filediff.patch` hunk and the `diagnostics` payload, as continuation lines
    under the event:

        'edit:     a.py (+1, -1)'
        '      @@ -1 +1 @@'
        '      -a'
        '      +b'
        '      {"/repo/a.py": [{"message": "unused import"}]}'

    `quiet` IS OWNED BY THE CALL SITE and is not a renderer level. The stream loop in `oc_runipd.py`
    branches `raw`/`clean` and falls through for `quiet`, so `render_event` is never called in that
    mode (the plan cited `oc_runipd.py:5651-5657`; the same branch now sits at `:5720-5730` after this
    plan's edits):

        5720:                    if output_mode == "raw":
        5721-                        sys.stdout.write(line)
        5722-                        sys.stdout.flush()
        5723-                    elif output_mode == "clean":
        5724-                        rendered = render_event(
        5725-                            line,
        5726-                            pal,
        5727-                            tracker=tracker,
        5728-                            verbosity=verbosity,
        5729-                            repo_root=agent_dir,
        5730-                        )

    `test_quiet_is_owned_by_the_call_site_not_by_a_renderer_level` asserts the renderer's EXECUTABLE
    code contains no `quiet` at all while its docstring names the owning layer, and
    `test_reason_is_reserved_and_has_no_producer` pins that the reserved `reason` prefix has no
    producer (F-12), so no tier advertises an event class the renderer cannot emit.

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q -k VerbosityTier
        .........                                                                [100%]
        9 passed, 68 deselected in 0.21s
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE parse results for `-v`, `-vv`, `--verbose`, and `--verbose --verbose`, in BOTH leading and trailing position, for `start` AND `resume`, showing `verbosity` 1 and 2; plus the same four through `aw oc run` (the wrapper forwards argv verbatim, `tests/test_oc_runipd_cli.py:46-63`). The LEADING cases are the ones that fail at HEAD (measured: `aw oc run -v somesetid` -> `invalid choice: 'somesetid'`; `aw oc run -vv somesetid` -> `unrecognized arguments: -vv`), so paste the BEFORE and AFTER for those two exact commands. Also show `verbosity` persisted in `state["options"]` and honored on `resume`.
  - Observed evidence: BEFORE, at HEAD `6091014c`, the two exact commands V-05 names. The cause was structural: `-v` was a
    member of the implicit-start `subcommands` set, so a LEADING `-v` was read as a subcommand and
    never prefixed with `start`:

        HEAD subcommands set: ['--help', '--version', '-h', '-v', 'report', 'resume', 'start', 'status', 'stop']
        '-v' in HEAD set: True    '--version' in HEAD set: True

        aw oc run -v somesetid   -> runipd: error: argument command: invalid choice: 'somesetid'  (exit 2)
        aw oc run -vv somesetid  -> runipd: error: unrecognized arguments: -vv                    (exit 2)

    AFTER, the same two commands run live THROUGH the `aw oc run` wrapper against a scratch git repo
    with an empty plans tree. Both now reach `start` and fail ONLY on the nonexistent selector, which
    is the honest error:

        oc run -v somesetid -> rc 2 | ["runipd: No IPD plan, Set, or file matching 'somesetid' found under .aw/records/plans/."]
        oc run -vv somesetid -> rc 2 | ["runipd: No IPD plan, Set, or file matching 'somesetid' found under .aw/records/plans/."]

    PARSE RESULTS, every spelling, BOTH positions, `start` AND `resume`, BOTH drivers:

        start trailing -v              oc=1     agy=1     MATCH
        start trailing -vv             oc=2     agy=2     MATCH
        start trailing --verbose       oc=1     agy=1     MATCH
        start trailing --verbose x2    oc=2     agy=2     MATCH
        start LEADING -v               oc=1     agy=1     MATCH
        start LEADING -vv              oc=2     agy=2     MATCH
        start LEADING --verbose        oc=1     agy=1     MATCH
        start bare (default)           oc=0     agy=0     MATCH
        resume trailing -v             oc=1     agy=1     MATCH
        resume trailing -vv            oc=2     agy=2     MATCH
        resume LEADING -v              oc=1     agy=1     MATCH
        resume --verbose --verbose     oc=2     agy=2     MATCH
        resume bare (omitted=None)     oc=None  agy=None  MATCH

    `resume` bare is `None`, NOT `0`, ON PURPOSE: an omitted flag on resume must leave the frozen tier
    alone rather than silently resetting a `-vv` run to tier 0.

    PERSISTED IN `state["options"]` AND HONORED ON RESUME, asserted by
    `test_verbosity_is_frozen_in_run_options_and_honored_on_resume` (oc) and
    `test_verbosity_is_frozen_and_honored_on_resume` (agy): a frozen `verbosity: 2` survives
    `run_queue(..., verbosity=None)` and is overwritten by an explicit `verbosity=1`.

        $ python3 -m pytest tests/test_oc_runipd_cli.py tests/test_agy_runipd_cli.py -o addopts="" -q -k "Verbosity"
        .............                                                            [100%]
        13 passed, 46 deselected in 0.72s
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE `render_agy_event` output for an agy `step_update` tool event in ACTIVE and DONE states showing the shared prefix and alignment, a repo-relative path replacing the old basename, and `duration_seconds` preserved. Show the new parameters are KEYWORD-with-default by calling the function with the old two-argument signature and getting a valid line (the `runagy.py` re-export shim depends on it). State explicitly which oc-format elements are NOT reachable on agy and why (no `filediff`), rather than claiming identical output.
  - Observed evidence: ACTIVE                'bash:     run_command: pytest tests/ -v'
        DONE + duration       'bash:     run_command: pytest tests/ -v (1.25s)'
        ERROR                 'bash:     run_command: false'
        repo-RELATIVE path    'write:    write_to_file: agent_workflows/x.py'
        edit: NO (+A,-D)      'edit:     replace_file_content: a.py'
        read at L0 (suppress) None
        read at L1            'read:     view_file: c.py'
        subagent              'subagent: 2 subagents done'

    (Status and class glyphs elided here for sanitizer safety; `AgyEventRenderTests` asserts the
    byte-exact prefixes by building them from `render_stream.EVENT_PREFIXES`.) The shared prefix puts
    the payload in the same column as the oc renderer; the repo-relative path replaces the old bare
    `Path(...).name` basename; and `duration_seconds` is preserved on the DONE line.

    THE OLD TWO-ARGUMENT SIGNATURE still works, called positionally through the `runagy.py` re-export
    shim, which is why the new parameters are keyword-only with defaults:

        OLD TWO-ARGUMENT CALL (positional only, through the runagy shim):
          'bash:     run_command: ls'
        signature: (raw_line: 'str', pal: 'Palette', *, verbosity: 'int' = 0, use_unicode: 'bool' = True,
                    repo_root: 'str | Path | None' = None, tracker: 'StreamTracker | None' = None) -> 'str | None'
        param kinds: ['POSITIONAL_OR_KEYWORD', 'POSITIONAL_OR_KEYWORD', 'KEYWORD_ONLY', 'KEYWORD_ONLY',
                      'KEYWORD_ONLY', 'KEYWORD_ONLY']

    WHAT IS NOT REACHABLE ON AGY, stated rather than claimed away. The agy schema has NO `filediff` and
    no additions/deletions anywhere, so an agy edit line CANNOT carry `(+A, -D)`; the `edit: NO (+A,-D)`
    row above IS that absence, and
    `test_an_agy_edit_line_carries_no_diff_stats_because_the_host_emits_none` pins it so a future
    author cannot "restore parity" by inventing numbers the host never sent. There is likewise no
    `todowrite` event and no diagnostics payload, so no todo transition and no Pyright block are
    computed here; at `-vv` the only extra detail the schema affords is the raw tool parameters. The
    tool NAME is also kept in the agy payload, unlike oc which drops `bash` in favor of the prefix,
    because agy tool names are host-specific and not recoverable from the class prefix.

    A FURTHER HONESTY NOTE recorded at execution: `_AGY_TOOL_PREFIX_KIND` is NAME-BASED and therefore a
    HEURISTIC, because there is not one agy event in this repository's session corpus to measure
    against (zero `"event":"step_update"` lines across all logs; every log is OpenCode). Unknown tools
    fall back to parameter shape and then to their own name, so an unmapped tool still renders in
    grammar and in column. This is recorded in the code as well, not only here.

        $ python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender
        .........                                                                [100%]
        9 passed, 16 deselected in 0.14s
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: PASTE the output of a BARE `python3 -m pytest` including its `N passed` summary line (do not add `-n0`, a second `-q`, or `-p no:randomly`). Paste the updated golden transcript literal and confirm all THREE golden tests still pass, naming them. Confirm the re-export test still compares driver output against module output rather than against a new hardcoded string.
  - Observed evidence: BARE SUITE, with no added `-n0`, no second `-q`, and no `-p no:randomly`, since `addopts` already
    supplies `-q -n auto --dist=worksteal -m 'not slow'`:

        $ python3 -m pytest
        FAILED tests/test_oc_runipd.py::WorktreeIsolationTests::test_verified_child_integrates_to_main_and_worktree_removed
        FAILED tests/test_oc_runipd.py::WorktreeIsolationTests::test_non_passing_gate_defers_not_faked_executed
        FAILED tests/test_oc_runipd.py::FailClosedIntegrationGuardTests::test_non_passing_gate_records_merge_conflict_main_pristine
        31 failed, 5563 passed, 3 skipped, 2 xfailed in 208.04s (0:03:28)

    THE 31 FAILURES ARE PRE-EXISTING AT HEAD AND THE SET IS BYTE-IDENTICAL. Stated with the measurement
    rather than asserted, because "31 failed" is not by itself evidence of zero regressions. A clean
    clone of HEAD `6091014c` was built in a gitignored scratch directory and run bare, its `FAILED`
    lines sorted, and diffed against this tree's:

        HEAD clone (6091014c):  31 failed, 5505 passed, 3 skipped, 2 xfailed in 199.83s
        this tree:              31 failed, 5563 passed, 3 skipped, 2 xfailed in 208.04s
        $ diff head-failures.txt new-failures.txt && echo "IDENTICAL: zero regressions, zero new failures"
        IDENTICAL: zero regressions, zero new failures

    So: the same 31 pre-existing failures, and +58 passing tests, which is the new coverage this plan
    adds. The pre-existing set is dominated by worktree-isolation, self-finalize, run-viewer and
    lifecycle-CLI tests red at HEAD for reasons unrelated to stream rendering; NONE was touched or
    "fixed" here.

    THREE REGRESSIONS WERE INTRODUCED DURING EXECUTION AND FIXED, recorded because they are the reason
    the diff above is trustworthy rather than lucky. FIRST,
    `test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` went red because a naive
    second `if ...: save_state(...)` block added a 32nd `save_state` CALL SITE to `agy_runipd`, a count
    that test pins per runner; both drivers now persist the two display options through ONE call.
    SECOND, `test_runner_stop_level3.py` indexed the exact string
    `rendered = render_event(line, pal, tracker=tracker)`, which the new keyword arguments broke; it is
    re-anchored on the assignment prefix, which is what its ordering claim actually needs. THIRD,
    `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`
    went red because the HEAD-baseline CLONE itself sat inside the tree; removing the scratch clone
    cleared it, and there was no code cause.

    THE THREE GOLDEN TESTS, NAMED, all passing:

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -v -k "GoldenByteIdentical"
        tests/test_render_stream.py::GoldenByteIdenticalTests::test_driver_reexport_produces_identical_transcript PASSED [ 33%]
        tests/test_render_stream.py::GoldenByteIdenticalTests::test_colored_transcript_strips_back_to_plain PASSED [ 66%]
        tests/test_render_stream.py::GoldenByteIdenticalTests::test_plain_transcript_is_byte_identical PASSED [100%]
        ======================= 3 passed, 74 deselected in 0.21s =======================

    THE UPDATED GOLDEN TRANSCRIPT, rendered from `_GOLDEN_EVENTS` (glyphs transcribed for sanitizer
    safety; the test's own literal carries the real ones):

        '* Reading the plan.'
        '... bash:     git status'
        'ok  bash:     git status'
        'x   edit:     patch failed'
        'a stray non-json log line'

    OQ-01 IS VISIBLE IN THAT TRANSCRIPT: the per-status glyph is KEPT and precedes the tool-class
    prefix in a constant-width two-column gutter, so both axes stay readable and the payload column is
    fixed. The expected literal in the test is built from `event_prefix_pad()` rather than hand-counted
    spaces, so a pad change cannot be papered over by re-counting, while the prefix strings and the
    payloads remain literals and a real format regression still fails.

    THE RE-EXPORT TEST STILL COMPARES DRIVER OUTPUT AGAINST MODULE OUTPUT, not against a new hardcoded
    string, so it keeps testing non-divergence rather than format:

        via_driver = "\n".join(r for raw in _GOLDEN_EVENTS
                               if (r := driver.render_event(raw, pal_via_driver)) is not None)
        via_module = _render_stream_transcript(_GOLDEN_EVENTS, pal_via_module)
        self.assertEqual(via_driver, via_module)
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: EITHER paste a test showing the chosen consumer rendering `modified_files` (with the exact rendered fragment quoted) and state the accumulation scope (per-run or per-item), OR paste the diff/statement showing the field was NOT added, with the recorded reason. A `modified_files` set that exists with no reader and no test fails this item.
  - Observed evidence: THE FIELD WAS KEPT AND HAS A NAMED READER: `render_run_summary_table`, the end-of-run box table
    both hosts call. It appends a files-touched count to the existing progress banner line. The
    rendered fragment, quoted:

        Files touched: 2 files
        Files touched: 1 file      (singular)
        (absent entirely when the tracker observed no touched files)

    WHY THAT READER AND NOT THE STATUSLINE: the live 4-line box is BYTE-PINNED by
    `test_format_statusline_user_example_box_layout`, which asserts exact border strings and equal line
    lengths, so a new column there is a wider change than it looks. The summary table already
    aggregates per-run cost, tokens and status, so a per-run file count belongs beside them.

    ACCUMULATION SCOPE IS PER-RUN, STATED: one `StreamTracker` is constructed per driver invocation and
    shared by every queue item, so `modified_files` accumulates across the whole run. That matches the
    summary table, which is a per-run report. `StreamTracker.begin_turn()` deliberately does NOT reset
    it (only the per-turn `todos`), `test_begin_turn_resets_only_per_turn_state` pins that asymmetry,
    the scope is documented in the class docstring, and
    `test_the_accumulation_scope_is_documented_as_run_scoped` asserts the docstring says so.

    A run with no edits renders NO new text, so the table stays byte-identical to before for that case
    (`test_no_touched_files_renders_nothing`), and every `test_render_run_summary_table_*` in
    `tests/test_run_summary_table.py` still passes in the bare run, so the banner-width recomputation
    did not disturb the pinned table geometry.

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q -k "EditWritePayload or ModifiedFilesConsumer"
        ............                                                             [100%]
        12 passed, 65 deselected in 0.20s
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: PASTE the rendered prefixes under both the Unicode and the narrow-safe table, showing the four Ambiguous glyphs (`◀`, `▶`, `◇`, `◈`) substituted in the fallback and the alignment invariant holding in BOTH. Show the selecting parameter is named `use_unicode`, matching `format_statusline_lines` (`render_stream.py:351`, `:476-483`).
  - Observed evidence: BOTH TABLES RENDERED, with the payload boundary marked by `|`. The four Ambiguous-width glyphs are
    substituted in the narrow-safe table (as `<`, `>`, `!`, `~`); the five Narrow ones are already
    exact and are left alone. The invariant holds in BOTH, with color off and on:

        UNICODE pad = 12                          NARROW-SAFE pad = 12
           |<A> read:     |payload  12 / 12          |< read:     |payload  12 / 12
           |<A> write:    |payload  12 / 12          |> write:    |payload  12 / 12
           |edit:         |payload  12 / 12          |edit:       |payload  12 / 12
           |find:         |payload  12 / 12          |find:       |payload  12 / 12
           |todo:         |payload  12 / 12          |todo:       |payload  12 / 12
           |<A> diag:     |payload  12 / 12          |! diag:     |payload  12 / 12
           |<A> reason:   |payload  12 / 12          |~ reason:   |payload  12 / 12
           |subagent:     |payload  12 / 12          |subagent:   |payload  12 / 12
           |bash:         |payload  12 / 12          |bash:       |payload  12 / 12

    The two numbers per row are `len(_strip_ansi(prefix))` with color OFF and with color ON; both are
    12 in every row of both tables. `<A>` marks the four East-Asian-Ambiguous glyphs, elided here for
    sanitizer safety and asserted by codepoint in the test.

    Because the substitutions are 1:1 codepoint swaps, both tables derive the SAME pad (12), which
    `test_the_four_ambiguous_glyphs_are_substituted_in_the_narrow_table` asserts along with the per-key
    length equality and the East Asian Width class of every substituted glyph (the exact Ambiguous set
    it computes is `{read, write, diag, reason}`, matching F-7).

    THE SELECTING PARAMETER IS `use_unicode`, matching `format_statusline_lines`, which already swaps
    its box-drawing characters under that same flag, so a caller threads ONE concept:

        selecting parameter name: True
        format_statusline_lines uses the same spelling: True

    `test_the_narrow_table_is_selected_by_use_unicode_matching_the_statusline` asserts the spelling on
    `event_prefix_table`, `event_prefix_pad`, `format_event_prefix` and `render_event`, and on
    `format_statusline_lines` as the precedent.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: PASTE the invariant test's output and demonstrate it BITES: temporarily add a tenth, longer prefix (or a wrong pad) and paste the FAILURE naming the offending prefix, then paste the restored pass. A test that only passes proves nothing about a future regression.
  - Observed evidence: THE INVARIANT PASSES:
        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q -k EventPrefixAlignment
        ........                                                                 [100%]
        8 passed, 69 deselected in 0.20s

    AND IT BITES. The defect was INJECTED into `agent_workflows/render_stream.py`: a tenth, LONGER
    prefix (`"orchestrate": "<glyph> orchestrate-a-whole-set:"`) was added to the table AND
    `event_prefix_pad` was changed to `return 12` so it ignores the table. Then the suite was run:

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q -k EventPrefixAlignment
        E               AssertionError: 12 != 27
        tests/test_render_stream.py:315: AssertionError
        E           AssertionError: 12 != 21
        tests/test_render_stream.py:335: AssertionError
        FAILED tests/test_render_stream.py::EventPrefixAlignmentTests::test_the_invariant_BITES_when_a_longer_prefix_is_added_without_the_pad
        FAILED tests/test_render_stream.py::EventPrefixAlignmentTests::test_the_four_ambiguous_glyphs_are_substituted_in_the_narrow_table
        FAILED tests/test_render_stream.py::EventPrefixAlignmentTests::test_every_prefix_pads_to_the_derived_column_with_color_on_and_off
        FAILED tests/test_render_stream.py::EventPrefixAlignmentTests::test_the_pad_is_derived_from_the_table_not_hardcoded
        FAILED tests/test_render_stream.py::EventPrefixAlignmentTests::test_the_pad_follows_the_table_when_the_table_changes
        5 failed, 3 passed, 69 deselected in 0.56s

    THE FAILURE NAMES THE OFFENDING PREFIX, which is the specific property V-10 requires, since a
    golden diff would only have shifted silently:

        E                       AssertionError: 26 != 12 : prefix 'orchestrate' does not pad to the derived column 12
        tests/test_render_stream.py:356: AssertionError

    RESTORED, and green again:

        $ python3 -m pytest tests/test_render_stream.py -o addopts="" -q
        ........................................................................ [ 93%]
        .....                                                                    [100%]
        77 passed in 0.71s
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: PASTE `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender` BEFORE and AFTER (baseline `4 passed` at HEAD). Also paste the whole-module run and confirm the pre-existing failure count is UNCHANGED at 10, so it is visible that this plan neither fixed nor worsened them. State plainly that the bare suite does not cover this file.
  - Observed evidence: THE BARE SUITE DOES NOT COVER THIS FILE, stated plainly and measured. `pyproject.toml:154` sets
    `testpaths = ["tests"]`, so a bare collect returns ZERO items from `tools/ipdrunner` while an
    explicit path collects 25:

        $ python3 -m pytest --collect-only -q tools/ipdrunner/
        tools/ipdrunner/test_runagy.py: 25
        $ grep -n "^testpaths" pyproject.toml
        154:testpaths = ["tests"]
        $ python3 -m pytest --collect-only -q | grep -c "tools/ipdrunner"
        0

    BEFORE, the baseline at HEAD measured at the start of this turn, and AFTER:

        BEFORE: $ python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender
        ....                                                                     [100%]
        4 passed, 16 deselected in 0.51s

        AFTER:  $ python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender
        .........                                                                [100%]
        9 passed, 16 deselected in 0.14s

    Four updated render assertions plus five new ones: the old two-argument signature, the
    repo-relative path replacing the basename, the read tier rule, the absent agy diff stats, and the
    subagent prefix.

    THE PRE-EXISTING FAILURE COUNT IS UNCHANGED AT 10, so it is visible that this plan neither fixed
    nor worsened them:

        BEFORE: $ python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q
        10 failed, 10 passed in 6.58s

        AFTER:  $ python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q
        FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_stall_timeout_and_resume_recovery
        FAILED tools/ipdrunner/test_runagy.py::AgyExecutionLifecycleTests::test_default_start_subcommand_inference
        10 failed, 15 passed in 6.60s

    The same 10 failures, all in `AgyExecutionLifecycleTests`/`AgyParserAndDiscoveryTests` and red at
    HEAD for reasons unrelated to rendering; passing count 10 to 15 for the 5 tests added. They were
    REPORTED, not repaired: repairing them here would have hidden whether this plan's own change is
    clean, and the plan puts them out of scope. The module docstring now records the explicit `-k`
    command and the pre-existing red state, so the next reader does not mistake a whole-module run for
    a regression signal.
  - Result: pass

- [x] V-12 validates E-12
  - Required evidence: PASTE the updated `subcommands` literal from BOTH driver sources side by side (they must be identical, because `tests/test_runner_stop_triggers.py:994-1009` regexes both) and the output of `python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -q -k "ImplicitStartShim or StopVerbSurface"` with its count. Paste the new assertion that pins whichever leading-`-v` behavior E-05 chose, and confirm `"stop"` is still present in both sets.
  - Observed evidence: THE UPDATED `subcommands` LITERAL FROM BOTH DRIVER SOURCES, side by side, parsed with the SAME
    `subcommands = \{(.*?)\}` regex the structural test uses, so the guard cannot be satisfied by
    hoisting the set into a module constant:

        oc_runipd.py       ['--help', '-h', 'report', 'resume', 'start', 'status', 'stop']
        agy_runipd.py      ['--help', '-h', 'report', 'resume', 'start', 'status', 'stop']
        IDENTICAL: True    "stop" present in both: True

    `"-v"` and `"--version"` are removed from BOTH, in lockstep, which is the OQ-02 resolution (E-05
    option (a)): the reservation guarded a `--version` flag neither driver registers.

    THE NEW ASSERTIONS pinning the chosen behavior, added in `ImplicitStartShimTests` where the old
    behavior was pinned. FIRST, `test_the_inline_copy_matches_both_drivers`: the file's inline copy of
    the set must DESCRIBE the drivers' sets, and the two drivers' sets must be equal. Without it the
    stale copy, which still listed `-v`/`--version`, would keep passing while asserting a set the code
    no longer has, which is exactly the failure mode E-12 names. SECOND,
    `test_a_leading_verbose_flag_is_now_prefixed_with_start`: a LEADING `-v`/`-vv`/`--verbose` is no
    longer a subcommand and parses to verbosity 1/2/1 with the selector intact, on BOTH drivers, so the
    behavior E-05 changes now has a regression guard. THIRD,
    `test_neither_driver_registers_the_version_flag_the_removed_entry_guarded`: OQ-02's evidence,
    pinned, since `parse_args(["--version"])` exits 2 on both. If a real `--version` is added later
    that test fails and is the place that records that both tokens must go back into both drivers
    together.

    `test_stop_is_listed_in_both_shims_subcommand_sets` is unchanged and still passes, and `"stop"`
    presence is additionally re-asserted positively in the new parity test.

        $ python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -q -k "ImplicitStartShim or StopVerbSurface"
        ............                                                             [100%]
        12 passed, 43 deselected in 2.75s

    The baseline for the same selection at HEAD was `9 passed, 43 deselected`; the three new tests are
    the delta. Both classes are NOT marked `slow`, so they DO run in the bare suite, confirmed by the
    count above and by their presence in the bare run.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: twelve E-items across five task groups, all inside one renderer module, two host drivers, and the four test modules that pin them. Reviewed for splitting and kept as one plan for a dependency reason, not because the count lint passes: E-07 cannot update the golden until every format-producing item has landed, E-12 goes red the moment E-05 changes the `subcommands` set, E-11 goes red the moment E-06 changes the agy format, and E-10's invariant cannot be written before E-01 derives the pad. A split would produce children whose tests fail until their sibling merges, which is the failure mode a Set exists to prevent. E-08 and E-09 are separable in principle but each is a handful of lines attached directly to E-03 and E-01.

Execution requires explicit human approval (`- Status: approved`). SCOPE FENCE (a declaration, so the runner can tell afterwards whether an out-of-scope file was edited or an in-scope file was not): the intended edits are the eight paths in `Scope-Paths` plus a `CHANGELOG.md` entry. `CHANGELOG.md` is deliberately NOT in the fence; if you write the entry, JUSTIFY it at finalize with `--scope-reason` rather than widening the fence, and if you conclude no entry is warranted, record that reason instead. Commit ONLY paths you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A` or `-a`, and NEVER push.

TESTS MUST BE RUN AND THEIR ACTUAL OUTPUT PASTED into each `Observed evidence`; a `V-*` may not be marked `pass` from the matching execution checkmark, and a claim of "tests pass" without pasted runner output is a contract violation, not a formatting lapse. Run the suite BARE (`python3 -m pytest`): `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

FIVE WARNINGS FOR THE EXECUTOR, each one a thing this plan originally got wrong.

FIRST, the plan's original conventions section asserted that all nine glyphs are single-width. THAT IS FALSE for four of them (`◀`, `▶`, `◇`, `◈` are East Asian Width Ambiguous). Do not reintroduce that claim in a comment or a docstring, and do not "verify" alignment only in your own terminal: your terminal's Ambiguous-width setting is not the contract.

SECOND, `write` events have NO `filediff` and no line count. If you find yourself reading `metadata.filediff.additions` on a write, you are reading a field that was `None` in 480 of 480 measured cases and your code will render a wrong or empty stat silently. Derive the count from `input.content`.

THIRD, the bare suite does NOT cover `tools/ipdrunner/test_runagy.py` (`testpaths = ["tests"]`). A green bare run is NOT evidence for that file, and ten of its tests are ALREADY RED at HEAD for unrelated reasons. Run `-k AgyEventRender` explicitly, report the pre-existing failure count unchanged, and do NOT attempt to fix those ten here.

FOURTH, `-v` does not simply parse today: it is a member of the implicit-start `subcommands` set in both drivers, so a leading `-v` is not prefixed with `start`. Verify your fix with the two exact commands measured in V-05, and keep the two drivers' sets IDENTICAL, because `tests/test_runner_stop_triggers.py:994-1009` regexes both source files.

FIFTH, `StreamTracker` is created ONCE PER RUN and shared by every queue item. New per-turn state must be reset per turn or it renders a transition diffed against a previous plan's data. This is the kind of bug that only appears on a multi-item queue, which is the normal case for `aw oc run all`.

This plan touches `render_stream.py`, `oc_runipd.py` and `agy_runipd.py`, which other pending Sets also name. That is NOT an operational hazard: `aw oc run` gives each execute item its own isolated worktree by default and merges through the revalidation gate, so file overlap between plans is handled by the runner, not by scheduling. Author-time note only.
