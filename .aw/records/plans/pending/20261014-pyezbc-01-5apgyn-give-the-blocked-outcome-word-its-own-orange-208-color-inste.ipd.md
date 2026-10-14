# IPD: Give the BLOCKED outcome word its own orange 208 color instead of the cyan else-branch

- Date: 2026-10-14
- Kind: child
- Concern: Outcome-word color selection in `render_stream.render_run_summary_table`
- Scope: Give the `BLOCKED` outcome word an explicit orange 208 (`\033[38;5;208m`) branch in `render_stream.render_run_summary_table` instead of falling through to the cyan (`\033[36m`) else-branch, and pin SGR codes for `BLOCKED` and all sibling ladder outcome words in `tests/test_zero_dispatch_outcome.py`.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_zero_dispatch_outcome.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: pyezbc
- Set: pyezbc (Give the BLOCKED outcome word its own orange 208 color instead of the cyan else-branch)
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: 5apgyn

## Workflow history

- 2026-10-14 to-review (antigravity): created review-ready plan from backlog item `pyezbc` (`064awu` Finding F-06).

## Goal

Give the `"BLOCKED"` run-summary outcome word in `render_stream.render_run_summary_table` its own explicit orange 208 (`\033[38;5;208m`) color branch (matching semantic stage `blocked` in spec `uonrjg` Sections 0.5, 5, and 7.2) instead of falling through to the cyan (`\033[36m`) `else` branch, and pin the SGR color selection for `"BLOCKED"` and all other outcome-word ladder outputs in `tests/test_zero_dispatch_outcome.py`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Explicit orange 208 branch for `BLOCKED` in `render_stream.render_run_summary_table`

- [ ] E-01 In `agent_workflows/render_stream.py` inside `render_stream.render_run_summary_table` at the `# Colors` block (`c_red = "\033[31m" if color else ""`, line 4336) and `outcome_color = (` (lines 4346-4363), define `c_orange = "\033[38;5;208m" if color else ""` alongside the existing banner color constants and add an explicit `c_orange if outcome_str == "BLOCKED" else ...` branch to `outcome_color` before the cyan fallback (`else c_cyan`, line 4360), updating the `ys1dor E-02` comment block (`# ys1dor E-02: THE STRANDED BRANCH IS EXPLICIT`, lines 4339-4345) to note that `"BLOCKED"` now has its own explicit orange 208 branch and only `"QUEUED"` (plus arbitrary `exit_reason` passthrough strings not matching an earlier branch) reaches the `c_cyan` fallback.
  - Depends on: none
  - Expected outcome: `render_stream.render_run_summary_table` renders `Outcome: \033[38;5;208mBLOCKED\033[0m` when `pal=Palette(True)` (`color` is `True`) and `Outcome: BLOCKED` with no ANSI escapes when `pal=Palette(False)` (`color` is `False`), while all other outcome words (`"COMPLETED"`, `STRANDED_OUTCOME`, `"INTERRUPTED"`, `"PARTIAL"`, `NO_WORK_OUTCOME`, `"FAILED"`, `"QUEUED"`, and custom `exit_reason` passthrough strings) retain their exact existing SGR codes.
  - Execution state: pending

### Task group 2: Outcome-word SGR color regression tests in `tests/test_zero_dispatch_outcome.py`

- [ ] E-02 In `tests/test_zero_dispatch_outcome.py` inside `TestZeroDispatchOutcome.test_outcome_color_selection` (lines 593-648), add assertions that: (a) every `"BLOCKED"`-producing queue status shape (`"blocked"`, `"dependency-blocked"`, `"fail-gate"`, `"fail-begin"`, `"fail-depend"`, and `"not-run"`) renders `"BLOCKED"` with SGR code `"38;5;208"` (and explicitly not `"36"`) under `Palette(True)` via `_extract_sgr_code(rendered, "BLOCKED")`; (b) `"BLOCKED"` under `Palette(False)` renders bare `"Outcome: BLOCKED"` with no `"\033["` escape sequence; and (c) the remaining ladder words (`"FAILED"` -> `"31"`, `"INTERRUPTED"` -> `"33"`, `"QUEUED"` -> `"36"`) alongside the already-tested `"COMPLETED"` (`"32"`), `STRANDED_OUTCOME` (`"31"`), `"PARTIAL"` (`"33"`), `NO_WORK_OUTCOME` (`"33"`), and fallback `exit_reason="NOTHING TO DO"` (`"36"`) all retain their expected SGR codes.
  - Depends on: E-01
  - Expected outcome: `tests/test_zero_dispatch_outcome.py` pins the complete 8-word outcome-ladder SGR color table plus all 6 `"BLOCKED"` item-status producers under both `Palette(True)` and `Palette(False)`, and fails when the `outcome_str == "BLOCKED"` branch in `render_stream.render_run_summary_table` is removed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run-summary banner color constants in `render_stream.render_run_summary_table` (`# Colors`, lines 4331-4337) are unbolded foreground SGR sequences gated on `color = bool(pal and getattr(pal, "enabled", False))` (line 4135): `c_cyan = "\033[36m" if color else ""`, `c_green = "\033[32m" if color else ""`, `c_yellow = "\033[33m" if color else ""`, `c_red = "\033[31m" if color else ""`, and `c_reset = "\033[0m" if color else ""`. Banner line 1 (`b_line1`, lines 4503-4508) formats `f"Outcome: {outcome_color}{outcome_str}{c_reset}{restarts_str}   ..."`.
- Spec `uonrjg` (`.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`) Section 0.5 (`### 0.5 Palette-Token Inventory`, line 122), Section 5 (`## 5. Semantic Stage Vocabulary`, line 330), and Section 7.2 (`### 7.2 Stream & Summary Table Renderer (agent_workflows/render_stream.py)`, line 521) assign semantic stage `blocked` to orange 208 (`\033[38;5;208m`), explicitly separating `blocked` (orange 208) from `ready`/`queued` (cyan), `active`/`recovering` (yellow), `failed` (red), and `done` (green).
- `tests/test_zero_dispatch_outcome.py` already owns `_extract_sgr_code(rendered: str, word: str) -> str | None` (`def _extract_sgr_code`, lines 71-75) with regex `rf"\033\[([0-9;]+)m{re.escape(word)}\033\[0m"`, which parses semicolon-delimited 256-color SGR parameters such as `"38;5;208"` without modification, and owns `TestZeroDispatchOutcome.test_outcome_color_selection` (`def test_outcome_color_selection`, lines 593-648).
- Pending plan `rowilw` (`.aw/records/plans/pending/20261014-1h98o3-01-rowilw-discriminate-live-fail-gate-items-by-attempt-failure-and-out.ipd.md`) declares `- Scope-Paths: agent_workflows/render_stream.py, tests/test_outcome_word_ladder.py` and modifies `outcome_class_of_item` and the `fail_count`/`blocked_count` ladder arms, not `outcome_color`. Placing our test assertions in `tests/test_zero_dispatch_outcome.py` (following plan `4po0sc`) keeps test files disjoint and matches the existing owner of `test_outcome_color_selection`.
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
| `"BLOCKED"` (across `"blocked"`, `"dependency-blocked"`, `"fail-gate"`, `"fail-begin"`, `"fail-depend"`, `"not-run"`) | **None — falls into `else c_cyan` (line 4360)** | **`"36"` (`c_cyan`, defect)** | None (`False`) | **`blocked` -> orange 208 (`"38;5;208"`, `c_orange`)** |
| `"QUEUED"` | `else c_cyan` (line 4360) | `"36"` (`c_cyan`) | None (`False`) | `ready`/`queued` -> cyan (`"36"`) |

As documented by the inline comment in `render_stream.render_run_summary_table` (`# ys1dor E-02: THE STRANDED BRANCH IS EXPLICIT`, lines 4339-4345), `"This selection is a set of SUBSTRING tests whose ELSE-BRANCH IS CYAN, not an obviously-wrong color, so an unhandled outcome word looks deliberate while being wrong"`. Because `"BLOCKED"` has no explicit branch and does not contain `"INTERRUPT"`, `"STOP"`, or `"FAIL"`, every run whose outcome is `"BLOCKED"` renders `Outcome: \033[36mBLOCKED\033[0m` in cyan (the `ready`/`queued` color) instead of orange 208 (`\033[38;5;208m`).

### F-02: Unbolded `\033[38;5;208m` (`c_orange`) matches the `render_run_summary_table` banner color convention and spec `uonrjg` Section 7.2

Every outcome-word color in `render_stream.render_run_summary_table` (`c_green`, `c_red`, `c_yellow`, `c_cyan`, lines 4333-4336) is an unbolded foreground SGR sequence gated on `if color else ""`, wrapped at `b_line1` (`f"Outcome: {outcome_color}{outcome_str}{c_reset}{restarts_str}   ..."`, line 4504). In the same module, `render_stream.format_statusline` (`c_amber = "\033[38;5;208m" if color else ""`, line 2536) already uses the identical unbolded 256-color SGR sequence `"\033[38;5;208m" if color else ""` for orange 208 (`stage.blocked` in `lifecycle_style.py`, line 245, and spec `uonrjg` Section 0.5 / Section 7.2). Defining `c_orange = "\033[38;5;208m" if color else ""` in `render_stream.render_run_summary_table` and adding `c_orange if outcome_str == "BLOCKED" else c_cyan` gives `"BLOCKED"` its own explicit orange 208 color under `Palette(True)` and `""` under `Palette(False)`.

## Proposed changes (ordered, validatable)

1. **`agent_workflows/render_stream.py` (`E-01`)**:
   - In `render_stream.render_run_summary_table` at the `# Colors` block (`c_red = "\033[31m" if color else ""`, line 4336), add:
     ```python
     c_orange = "\033[38;5;208m" if color else ""
     ```
   - In `outcome_color = (` (lines 4346-4363), add an explicit `outcome_str == "BLOCKED"` branch returning `c_orange` before the `c_cyan` fallback, and update the comment above `outcome_color`:
     ```python
     outcome_color = (
         c_green
         if outcome_str == "COMPLETED"
         else (
             c_red
             if outcome_str == STRANDED_OUTCOME
             else (
                 c_yellow
                 if (
                     "INTERRUPT" in outcome_str
                     or "STOP" in outcome_str
                     or outcome_str == "PARTIAL"
                     or outcome_str == NO_WORK_OUTCOME
                 )
                 else (
                     c_red
                     if "FAIL" in outcome_str
                     else (c_orange if outcome_str == "BLOCKED" else c_cyan)
                 )
             )
         )
     )
     ```

2. **`tests/test_zero_dispatch_outcome.py` (`E-02`)**:
   - In `TestZeroDispatchOutcome.test_outcome_color_selection` (`def test_outcome_color_selection`, lines 593-648), add assertions covering:
     - `"BLOCKED"` -> `"38;5;208"` (`c_orange`, and `assertNotEqual(..., "36")`) across all six blocked-class item statuses (`"blocked"`, `"dependency-blocked"`, `"fail-gate"`, `"fail-begin"`, `"fail-depend"`, `"not-run"`) under `Palette(True)`.
     - `"BLOCKED"` under `Palette(False)` renders `"Outcome: BLOCKED"` with no `"\033["` sequence in the output.
     - Complete ladder SGR coverage: `"FAILED"` (`status="failed"`, attempts `[{'number': 1}]`) -> `"31"`, `"INTERRUPTED"` (`status="interrupted"`, attempts `[{'number': 1}]`) -> `"33"`, `"QUEUED"` (`status="queued"`, attempts `[]`) -> `"36"`, alongside existing assertions for `"COMPLETED"` (`"32"`), `STRANDED_OUTCOME` (`"31"`), `"PARTIAL"` (`"33"`), `NO_WORK_OUTCOME` (`"33"`), and fallback `exit_reason="NOTHING TO DO"` (`"36"`).

## Deferred / out of scope (with reason)

- Routing raw `38;5;N` literals in `agent_workflows/render_stream.py` (including statusline and summary-table banner constants gated only on `bool(pal.enabled)`) through `Palette` / `lifecycle_style` tokens so `AW_COLOR_DEPTH=16` (`color_depth=1`) downgrades 256-color escapes to 16-color ANSI codes.
  - Carrier: y11p5u
- Discriminating live `fail-gate` queue items in `render_stream.outcome_class_of_item` and the `render_stream.render_run_summary_table` ladder when an item attempted execution and failed its gate (`FAILED` vs `BLOCKED`).
  - Carrier: 1h98o3

## Scope check

- Over-scope: none.
- Under-scope: none. Both the explicit `"BLOCKED"` color branch in `render_stream.render_run_summary_table` and the SGR color regression tests in `tests/test_zero_dispatch_outcome.py` are included.

## Required tests / validation

- Run targeted unit tests in `tests/test_zero_dispatch_outcome.py`, `tests/test_outcome_word_ladder.py`, and `tests/test_run_summary_table.py`.
- Run a negative-control / mutation proof verifying that reverting `c_orange if outcome_str == "BLOCKED"` to `c_cyan` causes `TestZeroDispatchOutcome.test_outcome_color_selection` to fail with `"36" != "38;5;208"`.
- Run the full repository test suite via bare `python3 -m pytest` and run `aw check` and `aw sanitize --agent`.

## Spec / documentation sync

- N/A with reason: Spec `uonrjg` (`.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`) Sections 0.5, 5, and 7.2 already specify orange 208 (`\033[38;5;208m`) for semantic stage `blocked` in `agent_workflows/render_stream.py`; this plan brings `render_stream.render_run_summary_table`'s `Outcome: BLOCKED` banner color into compliance with that existing specification.

## Open questions

### OQ-01: Should `"BLOCKED"` in `render_stream.render_run_summary_table` use unbolded `\033[38;5;208m` (`c_orange`) or bold `\033[1;38;5;208m`?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Use unbolded `\033[38;5;208m` (`c_orange = "\033[38;5;208m" if color else ""`). Every sibling outcome color in `render_stream.render_run_summary_table` (`c_green = "\033[32m"`, `c_red = "\033[31m"`, `c_yellow = "\033[33m"`, `c_cyan = "\033[36m"`, lines 4333-4336) is unbolded, `render_stream.format_statusline` (`c_amber = "\033[38;5;208m" if color else ""`, line 2536) uses the same unbolded SGR sequence, and backlog item `pyezbc` explicitly cites spec `uonrjg` Section 7.2 (`orange 208`).

### OQ-02: Should the SGR color regression tests for `"BLOCKED"` live in `tests/test_zero_dispatch_outcome.py` or `tests/test_outcome_word_ladder.py`?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Place them in `tests/test_zero_dispatch_outcome.py` inside `TestZeroDispatchOutcome.test_outcome_color_selection` (lines 593-648), which already owns `_extract_sgr_code` (lines 71-75) and the `outcome_color` SGR assertions introduced by plan `4po0sc` (`E-03`), and avoids file overlap with pending plan `rowilw` on `tests/test_outcome_word_ladder.py`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/render_stream.py` showing `c_orange = "\033[38;5;208m" if color else ""` and `c_orange if outcome_str == "BLOCKED" else c_cyan` in `render_stream.render_run_summary_table`, plus the output of a `python3 -c` one-liner calling `render_stream.render_run_summary_table` across all 8 canonical ladder words (`COMPLETED`, `STRANDED`, `FAILED`, `INTERRUPTED`, `PARTIAL`, `NO WORK PERFORMED`, `BLOCKED`, `QUEUED`) under `Palette(True)` and `Palette(False)` confirming `BLOCKED` emits SGR `'38;5;208'` under `Palette(True)` and no ANSI escapes under `Palette(False)` while all other words keep `'32'`, `'31'`, `'33'`, and `'36'`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste: (1) output of `python3 -m pytest tests/test_zero_dispatch_outcome.py tests/test_outcome_word_ladder.py tests/test_run_summary_table.py` showing all tests pass; (2) output of a negative-control check demonstrating that without the `outcome_str == "BLOCKED"` branch in `render_stream.render_run_summary_table`, `TestZeroDispatchOutcome.test_outcome_color_selection` fails with `'36' != '38;5;208'`; and (3) output of bare `python3 -m pytest`, `aw check`, and `aw sanitize --agent` showing 0 failures and 0 findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute this plan until it reaches `- Status: approved` via `aw ipd approve` (or runner review/approval gate). Upon execution and verification of `E-01`..`E-02` and `V-01`..`V-02`, transition the plan to `executed` via `aw ipd move` and commit only scoped paths via `aw commit 5apgyn -- <paths>`.
