# IPD: Write a per-run question and answer inbox through one shared answer writer

- Date: 2026-10-17
- Kind: child
- Concern: A parked question (Order 02) lives only on the queue item inside `state.json`. Spec `6kwd2e` R9.1-R9.2 (amended 2026-10-17) make a per-run inbox the ONE answer carrier: `questions/<question_id>.json` written when an item parks, `answers/<question_id>.json` written by any adapter, and one shared writer that enforces first-answer-wins, atomicity, `actor == "human"` and the ledger record. Without it every later channel (CLI, terminal, Telegram) would write answers its own way.
- Scope: IN: a new module `agent_workflows/question_inbox.py` with the question and answer file schemas, `write_question` (called by the driver at park time), `write_answer` (the only answer writer), `read_open_questions`, `read_answers`, run-scoped question ids (`<position>-<id6>-<worker question_id>`), the artifact content hash (R5.6), and the `human_answer` ledger entry; wiring `write_question` into the park branch. Also writes the `open-questions.md` projection at park time (R4a.1) from the same data. OUT: consuming answers (Order 04), the CLI (Order 05), channels (Orders 09-11).
- Scope-Paths: agent_workflows/question_inbox.py, agent_workflows/runner_shared.py, agent_workflows/set_records.py, tests/test_question_inbox.py
- Item-Dependencies: executed:epsti7
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: mtmqlm

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give every question one durable file and every answer one guarded writer, so any number of answering surfaces can be added without touching the run loop (spec `6kwd2e` R9.1, R9.2, R4a.1, R5.4, R5.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the module

- [ ] E-01 Create `agent_workflows/question_inbox.py` with `write_question(run_dir, item, question) -> Path` writing `questions/<qid>.json` (schema `aw.question/v1`: `question_id`, `run_id`, `artifact_id6`, `artifact_path`, `artifact_hash` = SHA-256 of the artifact file at park time, `fingerprint`, `gates_verdict`, `text`, `options`, `allow_free_text`, `evidence`, `action` (review/execute), `created_at`, `status: open`). Run-scoped `qid = f"{position:02d}-{id6}-{worker_qid}"`. Atomic write (temp in same dir, fsync, `os.replace`).
  - Depends on: none
  - Expected outcome: a written question file round-trips through `read_open_questions` and carries the artifact hash of the file as it was at park time.
  - Execution state: pending

- [ ] E-02 Add `write_answer(run_dir, qid, *, answer, choice, channel, sender, actor) -> AnswerResult` as the ONLY answer writer (R9.2): refuse an unknown `qid`; refuse `actor != "human"`; refuse a `choice` outside the options and a free-text answer when `allow_free_text` is false; take a per-question `filelock`; if `answers/<qid>.json` exists return `already` and record the attempt in `answers/<qid>.rejected.jsonl` without changing the answer; otherwise write `aw.answer/v1` (`question_id`, `answer`, `choice`, `actor`, `channel`, `sender`, `artifact_hash` copied from the question, `answered_at`) atomically and append the `human_answer` ledger event to `events.jsonl`. Return `recorded`/`already`/`rejected` with a reason.
  - Depends on: E-01
  - Expected outcome: two concurrent writers for one qid yield exactly one `recorded` and one `already`; unknown qid, non-human actor and out-of-range choice are `rejected`; the answer file never appears half-written.
  - Execution state: pending

### Task group 2: wire it at park time

- [ ] E-03 In the park branch added by Order 02, call `write_question` for each valid question and store the returned run-scoped qids on the item. Then write `open-questions.md` from `read_open_questions` minus answered ones, replacing the unwired `set_records.write_local_projections` path for runner runs (R4a.1). Writing must not raise into the run loop: on an OSError record an event and keep the item parked.
  - Depends on: E-02
  - Expected outcome: a scripted run that parks one item leaves `questions/<qid>.json` and an `open-questions.md` listing it while the run is still advancing.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_question_inbox.py`: schema round-trip, hash capture, concurrent first-answer-wins with real threads, every refusal reason, atomicity (no partial file after a simulated crash between temp write and rename), the ledger event, and the park-time wiring through a scripted run.
  - Depends on: E-03
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Atomic writes use a temp file in the destination directory then `os.replace` (pattern used across the package for run state).
- `filelock` is the package's only runtime dependency and the established lock primitive.
- `run_ledger_schema` requires `human_answer` records to carry `actor == "human"`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `set_records.write_local_projections` has no caller in the package (spec `6kwd2e` R4a.1 correction).
- `aw runs questions` reads `open-questions.md`; writing it at park time makes the existing verb work mid-run.

## Proposed changes (ordered, validatable)

1. E-01 question writer. 2. E-02 answer writer. 3. E-03 park wiring and projection. 4. E-04 tests.

## Deferred / out of scope (with reason)

- Reading answers in the loop: Order 04.
  - Carrier: j0ufrj
- Pointing `aw runs questions` at the runner run directory if its current lookup misses it: Order 05.
  - Carrier: 8u071n

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_inbox.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R9.1, R9.2, R4a.1 as amended 2026-10-17.

## Open questions

### OQ-01: Where should rejected or duplicate answers be recorded?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: beside the answer, in `answers/<qid>.rejected.jsonl`, and as an event in `events.jsonl`. R9.2 requires a second answer to be 'reported and recorded, never applied'; a sidecar keeps the accepted answer file single-valued.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session writing a question for a fixture artifact and printing the read-back record including `artifact_hash`, compared with `sha256sum` of the artifact.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test output for the concurrent-writers case (one `recorded`, one `already`) and each refusal reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `ls <run_dir>/questions` and the `open-questions.md` contents from a scripted run captured while a later item is still queued.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
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
