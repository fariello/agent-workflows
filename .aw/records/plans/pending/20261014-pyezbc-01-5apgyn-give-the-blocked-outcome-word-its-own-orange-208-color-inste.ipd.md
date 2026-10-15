# IPD: Give the BLOCKED outcome word its own orange 208 color instead of the cyan else-branch

- Date: 2026-10-14
- Kind: child
- Concern: Outcome-word color selection in `render_stream.render_run_summary_table`
- Scope: Give the `BLOCKED` outcome word an explicit branch in `render_stream.render_run_summary_table` that styles it through the shared lifecycle resolver as stage `blocked` (orange 208, `\033[38;5;208m` at depth 256, the authored 16-color code at depth 16, plain at depth none) instead of falling through to the cyan (`\033[36m`) else-branch, and pin SGR codes for `BLOCKED` and all sibling ladder outcome words in `tests/test_zero_dispatch_outcome.py`.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_zero_dispatch_outcome.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: pyezbc
- Set: pyezbc (Give the BLOCKED outcome word its own orange 208 color instead of the cyan else-branch)
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: 5apgyn
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-14 to-review (antigravity): created review-ready plan from backlog item `pyezbc` (`064awu` Finding F-06).

## Goal

Give the `"BLOCKED"` run-summary outcome word in `render_stream.render_run_summary_table` its own explicit branch styled through the shared lifecycle resolver (`Palette.lifecycle`) as semantic stage `blocked` (orange 208, `\033[38;5;208m` at depth 256, per spec `uonrjg` Sections 0.5, 5, and 7.2; lifecycle rendering MUST use the shared resolver per R10.3) instead of falling through to the cyan (`\033[36m`) `else` branch, and pin the SGR color selection for `"BLOCKED"` and all other outcome-word ladder outputs in `tests/test_zero_dispatch_outcome.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Explicit orange 208 branch for `BLOCKED` in `render_stream.render_run_summary_table`

- [ ] E-01 In `agent_workflows/render_stream.py` inside `render_stream.render_run_summary_table`, give `"BLOCKED"` its own explicit branch that renders the word through the shared lifecycle resolver rather than a raw SGR literal: build `blocked_resolved = _LS.Resolved(stage=_LS.BLOCKED, style=_LS.style_for(_LS.BLOCKED), family=_LS.FAMILY_RUNNER_ITEM)` (the same construction `render_stream.py` already uses near line 1267) and, where banner line 1 is formatted (`f"Outcome: {outcome_color}{outcome_str}{c_reset}..."`, around line 4504), substitute `pal.lifecycle(blocked_resolved, outcome_str, bold=False)` for `f"{outcome_color}{outcome_str}{c_reset}"` when `outcome_str == "BLOCKED"`, leaving every other word on the existing `outcome_color` expression (around lines 4346-4363). Do NOT add a raw `"\033[38;5;208m"` literal: such a literal ignores the `color_depth` pin, which is the exact defect plan `32fso3` (backlog `y11p5u`) is removing from this function. Update the `ys1dor E-02` comment block (around lines 4339-4345) to note that `"BLOCKED"` is styled by the lifecycle resolver and only `"QUEUED"` (plus `exit_reason` passthrough strings matching no earlier branch) reaches the `c_cyan` fallback.
  - Depends on: none
  - Expected outcome: with `color_depth` pinned to `256`, `render_stream.render_run_summary_table` renders `Outcome: \033[38;5;208mBLOCKED\033[0m` under `pal=Palette(True)` (byte-identical to what a raw literal would emit); pinned to `16` it renders `\033[35mBLOCKED\033[0m` (`term.color_16_for_stage("blocked") == 35`, measured at review); pinned to `none`, or under `pal=Palette(False)`, it renders `Outcome: BLOCKED` with no ANSI escape; while all other outcome words (`"COMPLETED"`, `STRANDED_OUTCOME`, `"INTERRUPTED"`, `"PARTIAL"`, `NO_WORK_OUTCOME`, `"FAILED"`, `"QUEUED"`, and custom `exit_reason` passthrough strings) retain their exact existing SGR codes.
  - Execution state: pending

### Task group 2: Outcome-word SGR color regression tests in `tests/test_zero_dispatch_outcome.py`

- [ ] E-02 In `tests/test_zero_dispatch_outcome.py` inside `TestZeroDispatchOutcome.test_outcome_color_selection` (lines 593-648), add assertions that: (a) every `"BLOCKED"`-producing queue status shape (`"blocked"`, `"dependency-blocked"`, `"fail-gate"`, `"fail-begin"`, `"fail-depend"`, and `"not-run"`) renders `"BLOCKED"` with SGR code `"38;5;208"` (and explicitly not `"36"`) under `Palette(True)` via `_extract_sgr_code(rendered, "BLOCKED")`; (b) `"BLOCKED"` under `Palette(False)` renders bare `"Outcome: BLOCKED"` with no `"\033["` escape sequence; (b2) with `color_depth` pinned to `16`, `"BLOCKED"` renders SGR `"35"` and the output contains no `"38;5;208"`, and pinned to `none` renders no escape on the `BLOCKED` word; and (c) the remaining ladder words (`"FAILED"` -> `"31"`, `"INTERRUPTED"` -> `"33"`, `"QUEUED"` -> `"36"`) alongside the already-tested `"COMPLETED"` (`"32"`), `STRANDED_OUTCOME` (`"31"`), `"PARTIAL"` (`"33"`), `NO_WORK_OUTCOME` (`"33"`), and fallback `exit_reason="NOTHING TO DO"` (`"36"`) all retain their expected SGR codes. DEPTH ISOLATION: `Palette.lifecycle_term()` resolves depth from the user's `color_depth` pin and then `COLORTERM`/`TERM` (`term.resolve_color_depth(override=True)`), so a developer shell with `TERM=linux`/`vt100` or a pinned config would otherwise turn the `"38;5;208"` assertion into `"35"`. Every `Palette(True)` assertion therefore runs with the depth pinned explicitly via `config.set_config_value("color_depth", ...)` inside a temporary `XDG_CONFIG_HOME`, with `TERM`, `COLORTERM`, `NO_COLOR`, and `FORCE_COLOR` saved and restored (the `_DepthTestBase` pattern in `tests/test_generic_color_depth.py`), and a fresh `Palette` per depth (it caches its `Term`).
  - Depends on: E-01
  - Expected outcome: `tests/test_zero_dispatch_outcome.py` pins the complete 8-word outcome-ladder SGR color table plus all 6 `"BLOCKED"` item-status producers under both `Palette(True)` and `Palette(False)` and at pinned depths `256`, `16`, and `none`, passes regardless of the invoking shell's `TERM`, and fails when the `outcome_str == "BLOCKED"` branch in `render_stream.render_run_summary_table` is removed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run-summary banner color constants in `render_stream.render_run_summary_table` (`# Colors`, lines 4331-4337) are unbolded foreground SGR sequences gated on `color = pal.enabled` (around line 3986): `c_cyan = "\033[36m" if color else ""`, `c_green = "\033[32m" if color else ""`, `c_yellow = "\033[33m" if color else ""`, `c_red = "\033[31m" if color else ""`, and `c_reset = "\033[0m" if color else ""`. Banner line 1 (`b_line1`, lines 4503-4508) formats `f"Outcome: {outcome_color}{outcome_str}{c_reset}{restarts_str}   ..."`.
- Spec `uonrjg` (`.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`) Section 0.5 (`### 0.5 Palette-Token Inventory`, line 122), Section 5 (`## 5. Semantic Stage Vocabulary`, line 330), and Section 7.2 (`### 7.2 Stream & Summary Table Renderer (agent_workflows/render_stream.py)`, line 521) assign semantic stage `blocked` to orange 208 (`\033[38;5;208m`), explicitly separating `blocked` (orange 208) from `ready`/`queued` (cyan), `active`/`recovering` (yellow), `failed` (red), and `done` (green).
- `tests/test_zero_dispatch_outcome.py` already owns `_extract_sgr_code(rendered: str, word: str) -> str | None` (`def _extract_sgr_code`, lines 71-75) with regex `rf"\033\[([0-9;]+)m{re.escape(word)}\033\[0m"`, which parses semicolon-delimited 256-color SGR parameters such as `"38;5;208"` without modification, and owns `TestZeroDispatchOutcome.test_outcome_color_selection` (`def test_outcome_color_selection`, lines 593-648).
- Pending plan `rowilw` (`.aw/records/plans/pending/20261014-1h98o3-01-rowilw-discriminate-live-fail-gate-items-by-attempt-failure-and-out.ipd.md`) declares `- Scope-Paths: agent_workflows/render_stream.py, tests/test_outcome_word_ladder.py` and modifies `outcome_class_of_item` and the `fail_count`/`blocked_count` ladder arms, not `outcome_color`. Placing our test assertions in `tests/test_zero_dispatch_outcome.py` (following plan `4po0sc`) keeps test files disjoint and matches the existing owner of `test_outcome_color_selection`.
- `Palette.lifecycle(resolved, text, bold=False)` (`render_stream.py` around line 256) renders through `Term.style_lifecycle_text`, which honors the resolved depth tier. Measured at review: stage `blocked` with `bold=False` gives `\033[38;5;208mBLOCKED\033[0m` at pin `256`, `\033[35mBLOCKED\033[0m` at pin `16`, and plain `BLOCKED` at pin `none`. `lifecycle_style.style_for("blocked")` is `color=208, bold=True`, so `bold=False` is required to match the unbolded sibling banner colors.
- Pending plan `32fso3` (Set `y11p5u`) also edits `render_run_summary_table` (its E-03 step 5 gates the banner `c_*` colors on depth `none`). Routing `BLOCKED` through the resolver here is consistent with that plan and adds no new depth-blind literal for it to remove.
- Run the test suite via bare `python3 -m pytest` (never pass `-n0`, extra `-q`, or `-p no:randomly`). Commit only via `aw commit`.

## Findings

### F-01: `render_stream.render_run_summary_table` colors `"BLOCKED"` cyan (`\033[36m`) via the `outcome_color` fallback `else` branch

In `agent_workflows/render_stream.py` inside `render_stream.render_run_summary_table`, the 8-rung outcome-word ladder (`if exit_reason:` through `outcome_str = "QUEUED"`, lines 4224-4330) selects `outcome_str` from eight canonical words (or a caller-supplied `exit_reason` override): `"INTERRUPTED"`, `"FAILED"`, `"BLOCKED"`, `"COMPLETED"`, `NO_WORK_OUTCOME` (`"NO WORK PERFORMED"`), `STRANDED_OUTCOME` (`"STRANDED"`), `"PARTIAL"`, and `"QUEUED"`. Immediately below (`outcome_color = (`, lines 4346-4363), the banner color is selected by a nested conditional expression:

| Ladder word (`outcome_str`) | Matching `outcome_color` condition in `render_stream.render_run_summary_table` | Measured pre-change SGR (`Palette(True)`) | Measured `Palette(False)` ANSI | Spec `uonrjg` semantic stage / target SGR |
| --- | --- | --- | --- | --- |
| `"COMPLETED"` | `outcome_str == "COMPLETED"` (line 4348) | `"32"` (`c_green`) | None (`False`) | `done` -> green (`"32"`) |
| `"STRANDED"` (`STRANDED_OUTCOME`) | `outcome_str == STRANDED_OUTCOME` (line 4351) | `"31"` (`c_red`) | None (`False`) | `failed` -> red (`"31"`) |
| `"INTERRUPTED"` | `"INTERRUPT" in outcome_str` (line 4355) | `"33"` (`c_yellow`) | None (`False`) | `active`/`recovering`/interrupted -> yellow (`"33"`) |
| `"PARTIAL"` | `outcome_str == "PARTIAL"` (line 4357) | `"33"` (`c_yellow`) | None (`False`) | partial -> yellow (`"33"`) |
| `"NO WORK PERFORMED"` (`NO_WORK_OUTCOME`) | `outcome_str == NO_WORK_OUTCOME` (line 4358) | `"33"` (`c_yellow`) | None (`False`) | zero-dispatch warning (`4po0sc` D-06) -> yellow (`"33"`) |
| `"FAILED"` | `"FAIL" in outcome_str` (line 4360) | `"31"` (`c_red`) | None (`False`) | `failed` -> red (`"31"`) |
| `"BLOCKED"` (across `"blocked"`, `"dependency-blocked"`, `"fail-gate"`, `"fail-begin"`, `"fail-depend"`, `"not-run"`) | **None — falls into `else c_cyan` (line 4360)** | **`"36"` (`c_cyan`, defect)** | None (`False`) | **`blocked` -> orange 208 (`"38;5;208"` at depth 256, via `Palette.lifecycle`)** |
| `"QUEUED"` | `else c_cyan` (line 4360) | `"36"` (`c_cyan`) | None (`False`) | `ready`/`queued` -> cyan (`"36"`) |

As documented by the inline comment in `render_stream.render_run_summary_table` (`# ys1dor E-02: THE STRANDED BRANCH IS EXPLICIT`, lines 4339-4345), `"This selection is a set of SUBSTRING tests whose ELSE-BRANCH IS CYAN, not an obviously-wrong color, so an unhandled outcome word looks deliberate while being wrong"`. Because `"BLOCKED"` has no explicit branch and does not contain `"INTERRUPT"`, `"STOP"`, or `"FAIL"`, every run whose outcome is `"BLOCKED"` renders `Outcome: \033[36mBLOCKED\033[0m` in cyan (the `ready`/`queued` color) instead of orange 208 (`\033[38;5;208m`).

### F-02: Rendering `BLOCKED` through `Palette.lifecycle(..., bold=False)` matches the banner convention and spec `uonrjg` Sections 7.2 and R10.3

Every outcome-word color in `render_stream.render_run_summary_table` (`c_green`, `c_red`, `c_yellow`, `c_cyan`, lines 4333-4336) is an unbolded foreground SGR sequence gated on `if color else ""`, wrapped at `b_line1` (`f"Outcome: {outcome_color}{outcome_str}{c_reset}{restarts_str}   ..."`, line 4504). (Correction at review: the earlier claim that `render_stream.format_statusline` defines `c_amber = "\033[38;5;208m"` near line 2536 is false; no `c_amber` exists in the module, and the only `38;5;208` literals are the BOLD `\033[1;38;5;208m` stop-badge and countdown colors.) The canonical orange 208 for stage `blocked` lives in `lifecycle_style` (`style_for("blocked").color == 208`) and is rendered depth-aware by `Palette.lifecycle`, which with `bold=False` yields the unbolded `\033[38;5;208m` at depth 256 that matches the sibling banner colors, and `""` styling under `Palette(False)`. Spec `uonrjg` R10.3 requires lifecycle rendering in `render_stream.py` to use that shared resolver.

## Proposed changes (ordered, validatable)

1. **`agent_workflows/render_stream.py` (`E-01`)**:
   - In `render_stream.render_run_summary_table`, leave the `outcome_color` expression's existing branches untouched and render the word for banner line 1 as:
     ```python
     if outcome_str == "BLOCKED":
         blocked_resolved = _LS.Resolved(
             stage=_LS.BLOCKED,
             style=_LS.style_for(_LS.BLOCKED),
             family=_LS.FAMILY_RUNNER_ITEM,
         )
         outcome_display = pal.lifecycle(blocked_resolved, outcome_str, bold=False)
     else:
         outcome_display = f"{outcome_color}{outcome_str}{c_reset}"
     ```
     and use `{outcome_display}` in place of `{outcome_color}{outcome_str}{c_reset}` in `b_line1`. Update the `ys1dor E-02` comment accordingly.

2. **`tests/test_zero_dispatch_outcome.py` (`E-02`)**:
   - In `TestZeroDispatchOutcome.test_outcome_color_selection` (`def test_outcome_color_selection`, lines 593-648), add assertions covering:
     - `"BLOCKED"` -> `"38;5;208"` at pinned depth `256` (and `assertNotEqual(..., "36")`) across all six blocked-class item statuses (`"blocked"`, `"dependency-blocked"`, `"fail-gate"`, `"fail-begin"`, `"fail-depend"`, `"not-run"`) under `Palette(True)`.
     - `"BLOCKED"` under `Palette(False)` renders `"Outcome: BLOCKED"` with no `"\033["` sequence in the output; at pinned depth `16` it renders `"35"` with no `"38;5;208"`; at pinned depth `none` the word carries no escape.
     - Complete ladder SGR coverage: `"FAILED"` (`status="failed"`, attempts `[{'number': 1}]`) -> `"31"`, `"INTERRUPTED"` (`status="interrupted"`, attempts `[{'number': 1}]`) -> `"33"`, `"QUEUED"` (`status="queued"`, attempts `[]`) -> `"36"`, alongside existing assertions for `"COMPLETED"` (`"32"`), `STRANDED_OUTCOME` (`"31"`), `"PARTIAL"` (`"33"`), `NO_WORK_OUTCOME` (`"33"`), and fallback `exit_reason="NOTHING TO DO"` (`"36"`).

## Deferred / out of scope (with reason)

- Routing raw `38;5;N` literals in `agent_workflows/render_stream.py` (including statusline and summary-table banner constants gated only on `bool(pal.enabled)`) through `Palette` / `lifecycle_style` tokens so `color_depth=16` downgrades 256-color escapes to 16-color ANSI codes and `color_depth=none` removes them (this plan's own `BLOCKED` branch is already depth-aware).
  - Carrier: y11p5u
- Discriminating live `fail-gate` queue items in `render_stream.outcome_class_of_item` and the `render_stream.render_run_summary_table` ladder when an item attempted execution and failed its gate (`FAILED` vs `BLOCKED`).
  - Carrier: 1h98o3

## Scope check

- Over-scope: none.
- Under-scope: none. Both the explicit `"BLOCKED"` color branch in `render_stream.render_run_summary_table` and the SGR color regression tests in `tests/test_zero_dispatch_outcome.py` are included.

## Required tests / validation

- Run targeted unit tests in `tests/test_zero_dispatch_outcome.py`, `tests/test_outcome_word_ladder.py`, and `tests/test_run_summary_table.py`.
- Run a negative-control / mutation proof verifying that removing the `outcome_str == "BLOCKED"` branch (so `BLOCKED` falls back to `c_cyan`) causes `TestZeroDispatchOutcome.test_outcome_color_selection` to fail with `"36" != "38;5;208"`, applied via a patch file under `/tmp` and reverted, never `git stash`.
- Run `tests/test_zero_dispatch_outcome.py` once with `TERM=vt100` exported to prove the depth pin isolates the assertions from the shell.
- Run the full repository test suite via bare `python3 -m pytest` and run `aw check` and `aw sanitize --agent`.

## Spec / documentation sync

- N/A with reason: Spec `uonrjg` (`.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`) Sections 0.5, 5, and 7.2 already specify orange 208 (`\033[38;5;208m`) for semantic stage `blocked` in `agent_workflows/render_stream.py`; this plan brings `render_stream.render_run_summary_table`'s `Outcome: BLOCKED` banner color into compliance with that existing specification.

## Open questions

### OQ-01: Should `"BLOCKED"` in `render_stream.render_run_summary_table` use unbolded `\033[38;5;208m` or bold `\033[1;38;5;208m`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Unbolded. Every sibling outcome color in `render_stream.render_run_summary_table` (`c_green = "\033[32m"`, `c_red = "\033[31m"`, `c_yellow = "\033[33m"`, `c_cyan = "\033[36m"`, lines 4333-4336) is unbolded. It is produced by `pal.lifecycle(blocked_resolved, outcome_str, bold=False)`, which at depth 256 emits exactly `\033[38;5;208m` (measured at review), rather than by a raw literal (see OQ-03). (The earlier citation of a `c_amber` constant in `format_statusline` was wrong; none exists.)

### OQ-02: Should the SGR color regression tests for `"BLOCKED"` live in `tests/test_zero_dispatch_outcome.py` or `tests/test_outcome_word_ladder.py`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Place them in `tests/test_zero_dispatch_outcome.py` inside `TestZeroDispatchOutcome.test_outcome_color_selection` (lines 593-648), which already owns `_extract_sgr_code` (lines 71-75) and the `outcome_color` SGR assertions introduced by plan `4po0sc` (`E-03`), and avoids file overlap with pending plan `rowilw` on `tests/test_outcome_word_ladder.py`.

### OQ-03: Raw `"\033[38;5;208m"` literal or the shared lifecycle resolver?

- Blocking: no
- Status: resolved
- Owner: plan author (reviewer decision, recorded as D-1 in the review record)
- Resolution or deferral rationale: The shared resolver. The plan justifies orange by mapping `BLOCKED` to lifecycle stage `blocked`, and spec `uonrjg` R10.3 says lifecycle rendering in `render_stream.py` MUST use the shared resolver. A raw literal would also ignore the `color_depth` pin (maintainer ruling 2026-10-12 recorded on backlog `y11p5u`: "color_depth=none must turn off ALL color"), creating new work for plan `32fso3`. Demonstrated at review: `Palette(True).lifecycle(Resolved(stage="blocked", ...), "BLOCKED", bold=False)` returned `'\x1b[38;5;208mBLOCKED\x1b[0m'` at pin `256`, `'\x1b[35mBLOCKED\x1b[0m'` at pin `16`, and `'BLOCKED'` at pin `none`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/render_stream.py` showing the `outcome_str == "BLOCKED"` branch rendering through `pal.lifecycle(..., bold=False)` and NO new `38;5;208` literal, plus the output of a `python3` probe (isolated `XDG_CONFIG_HOME`, depth pinned) calling `render_stream.render_run_summary_table` across all 8 canonical ladder words (`COMPLETED`, `STRANDED`, `FAILED`, `INTERRUPTED`, `PARTIAL`, `NO WORK PERFORMED`, `BLOCKED`, `QUEUED`) under `Palette(True)` at pins `256`, `16`, and `none` and under `Palette(False)`, confirming `BLOCKED` emits SGR `'38;5;208'` at `256`, `'35'` at `16`, and no escape at `none` or under `Palette(False)`, while every other word keeps `'32'`, `'31'`, `'33'`, or `'36'` exactly as before.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste: (1) output of `python3 -m pytest tests/test_zero_dispatch_outcome.py tests/test_outcome_word_ladder.py tests/test_run_summary_table.py` showing all tests pass; (2) output of a negative-control check demonstrating that without the `outcome_str == "BLOCKED"` branch in `render_stream.render_run_summary_table`, `TestZeroDispatchOutcome.test_outcome_color_selection` fails with `'36' != '38;5;208'`, followed by `git status --short` showing the mutation reverted; (3) the `TERM=vt100` run of `tests/test_zero_dispatch_outcome.py` passing; and (4) the summary line of bare `python3 -m pytest` plus `aw check` and `aw sanitize --agent` output. Any failure or finding must be shown pre-existing by reproducing it on the unmodified base commit, with the output pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Execute only after human approval (`- Status: approved`, set with `aw ipd set approved 5apgyn --by-human ...`). All open questions (OQ-01 to OQ-03) are resolved.
- Order: E-01 then E-02.
- Scope fence (a declaration, not a stop condition): changes are limited to `- Scope-Paths:`. An out-of-scope edit that proves necessary is made and then justified to the finalize scope gate (`--scope-reason`).
- Honesty rule: every `V-*` MUST carry the ACTUAL pasted command and runner output; never claim a pass that was not run.
- Commit only Scope-Paths files through `aw commit 5apgyn -- <paths>`; never `git add -A`; never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns begin/finalize, so do not run `aw ipd finalize` there. In a hand execution, run `aw ipd finalize 5apgyn` once every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-`git mv` the plan to `executed/` or hand-edit `- Status:`.
