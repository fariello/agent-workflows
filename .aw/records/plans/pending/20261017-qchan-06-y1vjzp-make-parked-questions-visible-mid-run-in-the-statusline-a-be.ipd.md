# IPD: Make parked questions visible mid-run in the statusline, a bell, aw runs questions and aw attention

- Date: 2026-10-17
- Kind: child
- Concern: A parked question that nobody notices is never answered. Spec `6kwd2e` R4a (mid-run visibility) and R9.6 require a live parked-question count on the runner statusline that names `aw runs answer <run-id>`, one terminal bell on the first park (TTY only, suppressed by presentation overrides), and `aw attention` to surface parked questions for active runs under an explicit label rather than the truncated raw-status fallback, without folding them into `blocked` (OQ-01 ruling) and without touching the artifact's own status.
- Scope: IN: statusline count and hint (`render_stream.Statusline` / `format_statusline_lines` / `print_final_statusline`), a shared parked-question counter, the once-per-run bell called from both park branches, the `awaiting-human` run label in `attention` (alias table, priority order, run column) and a parked-question count in the attention output (human and `--format json`). OUT: off-machine notification (Orders 09-11); `aw runs questions` (Order 05).
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/attention.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_question_visibility.py
- Item-Dependencies: executed:mtmqlm
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 6
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: y1vjzp

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make a waiting question visible on the console the human walked away from and in the standing 'what needs attention' view (spec `6kwd2e` R4a.3-R4a.6, R9.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the runner console

- [ ] E-01 Add `runner_shared.parked_question_count(state) -> int`: the number of OPEN gating questions across queue items whose status is `awaiting-human`, counted from the run-scoped qids Order 03 (`mtmqlm` E-03) stores on each parked item, falling back to `len(item["questions"])` (Order 02 `epsti7` E-02) when no qids are stored; never a count of parked ITEMS (spec `6kwd2e` A10d says "3 parked items reports 3", and one item may carry several questions, so the fixture uses one question per item and a second fixture asserts 2 questions on 1 item reports 2). Pure, reads `state` only, no file I/O, because the statusline re-renders every second. Then extend `render_stream.format_statusline_lines` with a keyword `parked_questions: int | None = None` and, in `Statusline._render_lines_unlocked` and `print_final_statusline`, pass `runner_shared.parked_question_count(self.state)` (import lazily, as the existing `runner_stop` import is). When the value is >= 1, render a badge in the BOTTOM-RIGHT segment of the bottom border (the slot the stop badge uses), styled with the `waiting-input` lifecycle color (`lifecycle_style.WAITING_INPUT`): `? N question(s) · aw runs answer <run-id>` in unicode mode, `? N question(s) - aw runs answer <run-id>` in ASCII mode. When a stop badge is also present, the stop badge wins that segment and the question badge moves into the empty column-3/column-4 span, so neither hides the other. When the badge is wider than the available span, keep the count and truncate the hint with `term.truncate_visible`, but never drop the `aw runs answer` prefix; the box must stay rectangular (every line the same visible width). With 0 or `None`, every line must stay byte-identical to today.
  - Depends on: none
  - Expected outcome: a rendered statusline for a state with 3 parked items (one question each) contains `3 questions` and `aw runs answer <run-id>` on its bottom border (A10d, A46); 2 questions on 1 item renders `2 questions`; with no parked items the four lines equal today's output; every line has the same visible width with and without the badge and with a stop badge present.
  - Execution state: pending

- [ ] E-02 Bell (R4a.4, R4a.5). Add `runner_shared.ring_bell_on_first_park(run_dir, state, *, stream) -> bool` and call it in BOTH park branches added by Order 02 (`epsti7` E-02 execute, E-06 review), directly after the item is set `awaiting-human` and saved. It writes one BEL (`\a`) to `stream` (the driver's `sys.stdout`, the stream the statusline draws on) ONLY when all hold: `state.get("bell_rung")` is falsy; `stream.isatty()` is true; the run's frozen `options["output_mode"]` is `clean` (the `--quiet` and `--raw` presentation overrides of `runner_shared.add_output_mode_flags` suppress it); and the run is not in agent mode (`--as-agent`, where stdout carries machine records). Before writing, set `state["bell_rung"] = True` and persist it with `save_state`, so a crash between the two can only lose a bell, never ring twice; it is set ONLY when the bell was actually written, so a park on a non-TTY first does not consume the run's single bell. Never raises into the park branch (an OSError writing is swallowed and recorded as a `bell-failed` event). `bell_rung` survives `resume` because it lives in `state.json`.
  - Depends on: E-01
  - Expected outcome: with a TTY stream the bell byte appears exactly once across three parks and not again after a simulated resume; with a non-TTY stream, `--quiet`, `--raw` or agent mode it never appears and `bell_rung` stays unset (A10e, A10f).
  - Execution state: pending

### Task group 2: aw attention

- [ ] E-03 In `attention.py`, give `awaiting-human` an explicit run label `awaiting-human` everywhere the live-run column is fed, so it reaches neither the truncation fallback nor the `fail-*` group: add it to `_RUN_STATUS_ALIASES` (identity, so `--run-status awaiting-human` filters and the selector vocabulary accept it), plus the short alias `question` mapping to it; add it to `_RUN_PRIORITY_ORDER` ranked directly below `running` (a parked item outranks a queued or finished copy of the same id6 in another live run); confirm `_resolve_run_lifecycle("awaiting-human")` resolves to the `waiting-input` stage (it does today through `lifecycle_style`'s `("awaiting-human", WAITING_INPUT)` row). The run column is 14 characters wide (`_render_table_row` `run_raw = (run_state or "-")[:14]`) and `awaiting-human` is exactly 14, so it renders whole. Do NOT change any artifact's native status, `attention_contract` class maps, or the cross-tree class (A10h).
  - Depends on: E-02
  - Expected outcome: `aw attention --runs` for a repo with an active run holding one parked item shows `awaiting-human` in that item's run column (not `awaitin`, not a `fail-*` word) with the waiting-input glyph; `--run-status awaiting-human` and `--run-status question` both select it; the item's artifact `- Status:` and `attention_class` are unchanged (A10g label half, A10h).
  - Execution state: pending

- [ ] E-05 Add `attention.get_parked_question_counts(repo_root) -> Dict[str, int]` returning, per LIVE run (`run_viewer.driver_holder_state == HOLDER_LIVE`, the same filter `get_active_runs_map` uses), the run id to `runner_shared.parked_question_count(state)` for runs with a nonzero count. Surface it: in human output, one line per such run below the summary footer, `run <run-id>: N question(s) waiting; answer with aw runs answer <run-id>`, printed whether or not `--runs` was given (R4a.6 "without the human knowing to run a run-specific verb"); in `--format json`, an APPENDED top-level key `parked_questions: [{"run_id": ..., "count": N}]` after `stranded_lanes` (same append-only rule that key's comment states), `[]` when none. Do NOT change any artifact's native status or cross-tree class (A10h).
  - Depends on: E-03
  - Expected outcome: `aw attention` (no flags) prints the `1 question waiting` line naming `aw runs answer <run-id>`; `--format json` carries `parked_questions` with count 1 and every pre-existing key unchanged in value and order; with no live run holding a parked question the human output is unchanged and the key is `[]` (A10g count half).
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_question_visibility.py` asserting spec `6kwd2e` A10d, A10e, A10f, A10g, A10h, A46: statusline rendering with counts and hint in unicode and ASCII, the zero-question byte-identity, rectangularity with and without the stop badge and with a long run id; the bell once on a TTY stream across three parks and after a reload of `state.json`, never on a non-TTY stream (capture through a stream object whose `isatty()` returns False and through a real pipe), never under `--quiet`/`--raw`/agent mode; `aw attention` driven as a subprocess against a fixture repo whose run directory's `driver.lock` is held LIVE by a helper process for the duration of the assertion (the liveness predicate is flock acquirability, so a lock file alone is not live), asserting the exact label text `awaiting-human`, the waiting line, the JSON key, and the artifact status before and after. Also run the existing statusline and attention suites unchanged.
  - Depends on: E-05
  - Expected outcome: the module passes, the existing statusline and attention suites pass unchanged, and the routine gate passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The statusline is the single live surface; do not add a second one (spec `6kwd2e` R4a.3).
- `aw attention` classes come from the artifact's own status; run dispositions belong to the live-run column (spec `6kwd2e` R4a.6 correction).
- The live-run column is fed by `attention.get_active_runs_map` through `canonical_run_status`, ranked by `_RUN_PRIORITY_ORDER`, filtered through `_RUN_STATUS_ALIASES`, and rendered at width 14 (`_render_table_row`) or as `[run: <status>]` (`_render_item_row`); liveness is `run_viewer.driver_holder_state` (flock acquirability).
- `attention.render_json` keys are append-only (its `stranded_lanes` comment).
- The statusline box is 4 lines and rectangular; its bottom border carries the tally (left), run id (centre) and stop badge (right). `test_format_statusline_user_example_box_layout` byte-pins the default layout, so the zero-question path must stay byte-identical.
- Presentation overrides for runner output are `--quiet` and `--raw` (`runner_shared.add_output_mode_flags`, frozen as `options["output_mode"]`) and agent mode (`--as-agent`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `get_active_runs_map` falls through to the raw string for unknown statuses (`canonical_run_status(raw_st) or raw_st`), which the spec reports as rendering `awaitin`; verified at review that `canonical_run_status("awaiting-human")` returns the raw word, `_RUN_PRIORITY_ORDER` has no entry (priority 0, so any other live run's status for the same id6 wins), and `_RUN_STATUS_ALIASES` lacks it, so `--run-status awaiting-human` matches only by accident of the raw string.
- `lifecycle_style` already maps `awaiting-human` to `waiting-input`; `_resolve_run_lifecycle("awaiting-human")` returns stage `waiting-input` today, while an invented label such as `question` resolves to `unknown`, which is why the label is the status word itself.
- No BEL is written anywhere in the runners today.
- No notification surface exists in the runners (research `xjsc9k`).

## Proposed changes (ordered, validatable)

1. E-01 counter + statusline badge. 2. E-02 bell. 3. E-03 attention run label. 4. E-05 attention parked-question count. 5. E-04 tests.

## Deferred / out of scope (with reason)

- Push and chat notification: Orders 09-11.
  - Carrier: txl556, qrup8m, mrlblc

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_question_visibility.py tests/test_statusline_stop_tally.py tests/test_statusline_behavior.py tests/test_statusline_visible_width.py tests/test_statusline_ascii_mode.py tests/test_attention.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R4a.3-R4a.6 and R9.6 as amended; no spec file is edited. The `aw attention --format json` payload gains one appended key (`parked_questions`), additive and backward compatible.

## Open questions

### OQ-01: Which label does `aw attention` show for a parked item?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (review decision D-1)
- Resolution or deferral rationale: RESOLVED: the status word `awaiting-human` itself, with `question` accepted as a filter alias. The plan's original `question` resolves to lifecycle stage `unknown` (measured: `_resolve_run_lifecycle("question").stage == "unknown"`), so it would render without the waiting-input glyph and color, while `awaiting-human` resolves to `waiting-input` and fits the 14-character run column exactly. Spec R4a.6 requires only a distinct explicit label that is not the fallback and not `blocked`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the rendered statusline (plain, `pal` disabled) for the 3-item fixture showing `3 questions` and `aw runs answer <run-id>`, the 2-questions-on-1-item fixture, the per-line visible widths with and without the badge (equal), and the assertion that the zero-question render equals the pre-change output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the byte count of `\a` in the captured TTY stream (1) after three parks through the scripted park branch (produced by E-02's call in Order 02's park branches), still 1 after a reload of `state.json` and a fourth park, and 0 for the non-TTY, `--quiet`, `--raw` and agent-mode cases, plus the persisted `bell_rung` value in each case.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw attention --runs` output for the fixture showing `awaiting-human` in the run column, the `--run-status awaiting-human` and `--run-status question` outputs selecting it, and the artifact's `- Status:` line and `attention_class` before and after, captured while the helper holds `driver.lock` (produced by E-03's alias, priority and run-label changes in `attention.py`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste plain `aw attention` output for the fixture showing the `1 question waiting` line naming `aw runs answer <run-id>`, the `--format json` top-level key list (pre-existing keys in their original order, then `parked_questions`) and its value, and the same two outputs with no live parked run (`parked_questions: []`, no waiting line), captured while the helper holds `driver.lock` (produced by E-05's `get_parked_question_counts`).
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
