# IPD: runipd prints same-session continuation hint on exit

- Date: 2026-08-24
- Kind: child
- Concern: When a runipd run finishes, the OpenCode session id(s) it used are captured in `state.json` (top-level `session_id` and the per-Set `set_sessions` map) even when `--session` was not passed - OpenCode creates a session per Set and runipd reads the id back out of the streamed JSONL log via `extract_session_id`. But nothing surfaces those ids to the user on exit. To run ANOTHER IPD or file under the SAME session context (so the agent keeps its accumulated context), the user must currently open `state.json` and copy the id by hand. The driver should print a continuation hint on exit naming the captured session id(s) and the exact command to reuse them.
- Scope: At the end of a `start`/`resume` run (in `run_queue`, after the final report is written), print a concise, colorized continuation hint that (a) lists the captured session id(s) - per Set when a run spans multiple Sets, since each Set has its own session - and (b) shows the exact command to run a NEW IPD/file in that same session context (`runipd --session <ses_...> <selector>`, and equivalently once graduated `aw oc runipd --session <ses_...> <selector>`), plus the `resume` command for continuing THIS run. Handle 0/1/N captured sessions honestly (say '(none captured)' when empty). No behavior change to execution; output-only. Single-child plan for the runipdsess Set.
- Scope-Paths: tools/ipdrunner/runipd.py, tools/ipdrunner/test_runipd.py
- Status: to-review
- Set: runipdsess
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rxkf1e

## Workflow history
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; single-child plan to print a same-session continuation hint on runipd exit.

## Goal

Make it trivial to run a follow-on IPD/file in the same OpenCode session context after a run ends, by printing the captured session id(s) and the exact reuse command on exit, instead of requiring the user to read `state.json` by hand.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Continuation-hint renderer

- [ ] E-01 Add a `render_continuation_hint(state, run_dir) -> str` helper in `tools/ipdrunner/runipd.py` that reads the captured sessions from `state` (the per-Set `set_sessions` map, falling back to top-level `session_id`) and returns a hint block. Behavior by count: 0 sessions -> a line noting no session was captured (e.g. "No OpenCode session was captured for this run."); exactly 1 -> name it once and show the reuse command; N (multi-Set) -> list each `setid: ses_...` and show the reuse command using a representative/most-recent id, noting each Set has its own session. Include: the same-context command `runipd --session <ses_...> <new-selector>` (primary use: run a NEW IPD/file in that session), and the `runipd resume --repo <repo> <run-id>` command (to continue THIS run's queue, which already reuses the persisted per-Set sessions). Use the existing `Palette`/`should_color` helpers so the hint is colorized like the rest of the output and degrades to plain text when not a TTY / NO_COLOR.
  - Depends on: none
  - Expected outcome: a pure function that, given a run state, returns the correct hint text for 0/1/N captured sessions.
  - Execution state: pending

### Task group 2: Emit on exit

- [ ] E-02 Call `render_continuation_hint` at the end of `run_queue` (after `write_report`, around runipd.py:1429-1431) and print it to stdout before returning the exit code, so both the `start` and `resume` paths (which both end via `run_queue`) show it. Do NOT print it for the `status`/`report` subcommands (they do not run the queue). Ensure the hint prints on both success and partial/failed completion (any normal `run_queue` return), and is suppressed cleanly when no session was captured (still print the short "no session captured" note). Keep it out of the `KeyboardInterrupt` path's existing terse message (interrupt already prints its own line).
  - Depends on: E-01
  - Expected outcome: finishing a run prints the continuation hint naming the captured session id(s) and the reuse command; `status`/`report` do not.
  - Execution state: pending

### Task group 3: Test

- [ ] E-03 In `tools/ipdrunner/test_runipd.py`, add tests for `render_continuation_hint` covering the three shapes: zero captured sessions (no-session note, no `ses_` id, no crash), exactly one (id named once, reuse command present), and multiple Sets (each `setid: ses_...` listed). Assert the reuse command string contains `--session` and the captured id. If feasible, add a light integration assertion that a completed `run_queue` (with a stubbed executor that records a session id into `set_sessions`) emits the hint on stdout.
  - Depends on: E-01, E-02
  - Expected outcome: passing tests pinning the 0/1/N output contract and the on-exit emission.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Session ids are captured even without `--session`: `extract_session_id` (runipd.py:846-865) reads `sessionID`/`sessionId`/`session_id` from the streamed OpenCode JSONL log; `execute_item` persists them into `state["set_sessions"][setid]`, `state["session_id"]`, and the per-attempt record (runipd.py:1240-1248). Verified against real run dirs where `options.session` was None yet `set_sessions` held real `ses_...` ids (e.g. `.aw/records/runs/run-20260824T150827Z-2301181` with four per-Set sessions).
- A run may span multiple Sets, each with its own session, so the hint must handle N ids, not assume one.
- `start` reuses a supplied `--session` for a NEW run: `initialize_run` reads `args.session` into `initial_session` and seeds `set_sessions`/`session_id` (runipd.py:725-732); `run_opencode` passes it to the `opencode` binary (runipd.py:1053-1059). So `runipd --session <captured-id> <new-file>` genuinely continues the same session context - the hint is truthful.
- Both `start` and `resume` return via `run_queue`, which already reloads final `state` and calls `write_report` at its tail (runipd.py:1429-1431) - the natural place to emit the hint.
- Output uses `Palette`/`should_color` (runipd.py:93-127) with `--quiet`/`--raw`/`clean` modes; the hint should respect color but is a summary line, not a per-event stream, so it prints in all modes.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | Med | Toolkit user | Captured session id(s) are only in `state.json`; to run a follow-on file in the same session context the user must hand-read the file. A visible exit hint removes that friction. |
| F-02 | Low | Maintainer | The hint must handle 0/1/N sessions because multi-Set runs capture one session per Set; a naive "the session" message would be wrong on multi-Set runs. |

## Proposed changes (ordered, validatable)

1. Add `render_continuation_hint(state, run_dir)` handling 0/1/N captured sessions, colorized via existing helpers.
2. Print it at the end of `run_queue` (covers both `start` and `resume`); exclude `status`/`report`.
3. Add tests pinning the 0/1/N output contract and on-exit emission.

## Deferred / out of scope (with reason)

- No change to session capture, execution, or state schema; this is output-only. The `--session` semantics already exist and are reused as-is.
- The `aw oc runipd` graduation (awocrunner Set) is separate; this change lands in `tools/ipdrunner/runipd.py` and will move with the core when that Set executes (the hint text may mention both `runipd` and `aw oc runipd` forms, but wiring the packaged command is not this plan).
- Interrupt (Ctrl-C) keeps its existing terse message; adding the full hint to the interrupt path is out of scope (state may be mid-write).

## Scope check

- Over-scope: none. One helper, one call site, and tests, all in the runner and its test file.
- Under-scope: none. Covers the renderer, the emission on both queue-running paths, and the 0/1/N contract.

## Required tests / validation

- `python3 tools/ipdrunner/test_runipd.py` (or `python3 -m pytest tools/ipdrunner/test_runipd.py`) green, including the new `render_continuation_hint` tests.
- Manual: finish a small run without `--session` and confirm the exit hint lists the captured `ses_...` id(s) and the `runipd --session <id> <selector>` command; run `runipd status <run-id>` and confirm the hint is NOT printed.
- `pre-commit run --files tools/ipdrunner/runipd.py tools/ipdrunner/test_runipd.py`.

## Spec / documentation sync

- Update the `ipdrunner/` section of `tools/README.md` only if it enumerates output/exit behavior; otherwise N/A. (The awocrunner Set's child 04 owns the broader `aw oc runipd` doc sync; do not duplicate it here.)

## Open questions

### OQ-01: On a multi-Set run, which session id should the primary reuse command use?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: RESOLVED for the common case: list every `setid: ses_...` so the user can pick, and use the most-recently-updated session (top-level `state["session_id"]`, which tracks the last captured id) as the default in the example command. Non-blocking; the full list is always shown so no id is hidden.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted test output showing `render_continuation_hint` returns the correct text for zero, one, and multiple captured sessions (no-session note; single id + reuse command; per-Set list).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted terminal output of a completed run (without `--session`) showing the continuation hint with the captured `ses_...` id and `runipd --session ... <selector>` command; and pasted `runipd status <run-id>` output confirming the hint is absent there.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 tools/ipdrunner/test_runipd.py` (or pytest) output with the new tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one small, cohesive concern (surface the captured session on exit so a follow-on run can reuse the same context), confined to a helper, one call site, and its tests.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved (list all per-Set ids; default the example to the most-recent). No blocking open question remains.
2. Scope fence: touch ONLY `tools/ipdrunner/runipd.py` and `tools/ipdrunner/test_runipd.py`. Output-only change; do NOT alter session capture, execution, or the state schema. Do NOT modify the `agent_workflows/` package. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (the test run and a real run's exit hint); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
