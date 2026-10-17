# IPD: Carry emergent questions in the worker outcome file with driver-computed fingerprints

- Date: 2026-10-17
- Kind: child
- Concern: A runner worker that meets a question it cannot resolve from evidence has no carrier for it. Measured 2026-10-17: the execute prompt (`runner_shared.build_prompt`) tells the worker to record a DEFERRED question in prose in `decisions-and-questions.md`, and the outcome JSON's `deferred_question_ids` is a free-text list that only `render_stream` reads, for one report line. Nothing machine-readable reaches the driver, so nothing can park, dedupe or route the question. Spec `6kwd2e` R2 (approved, amended 2026-10-17) requires a `questions[]` array in the outcome JSON with a driver-computed fingerprint.
- Scope: IN: the `questions[]` outcome field (schema, tolerant never-raising validator, bounded and sanitized like `validate_proposal`), the driver-computed fingerprint (R4.1a, one shared normalizer), the execute-prompt instruction to use it under the askme three-way sort (R2.5, cited not restated), and the review-turn route: an isolated review turn writes its questions to the same outcome path. OUT: what the driver does with a valid question (Order 02 parks it; Order 03 writes the inbox); deduplication across items (Order 08).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_question_carrier.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0jooqz

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give the worker one validated, machine-readable way to hand the driver a question it cannot resolve, so later Orders can park it, route it to the human, and resume with the answer (spec `6kwd2e` R2, R4.1a).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the field and its validator

- [ ] E-01 In `agent_workflows/runner_shared.py`, define `QUESTIONS_KEY = "questions"` and a pure validator `validate_questions(outcome) -> QuestionsVerdict` beside `validate_proposal`, which it mirrors: never raises; verdict `absent`/`valid`/`malformed`; each entry REQUIRES `question_id` (worker-local, `[A-Za-z0-9._-]{1,40}`), `text` (<= 2000 chars), `artifact_id6` (an id6), `gates_verdict` (bool), `evidence` (list of <= 10 strings, each <= 500 chars), and MAY carry `options` (list of 2-8 labels, each <= 120 chars), `allow_free_text` (bool, default true) and a worker `fingerprint` (kept only as `proposed_fingerprint`, never trusted). Text fields pass `sanitize_front_matter_text`. A malformed entry yields a diagnostic NAMING the missing or bad field (R2.2, A29), and the verdict reports per-entry results so one bad entry does not drop the valid ones. Cap the array at 20 entries.
  - Depends on: none
  - Expected outcome: valid, absent, and each malformed case (missing field, over-length text, bad id6, too many options, non-list) return the documented verdict with the field named; a worker `fingerprint` never appears as the computed one.
  - Execution state: pending

- [ ] E-02 Add `question_fingerprint(text, options) -> str` in `runner_shared.py`: deterministic normalization (Unicode NFKC, casefold, collapse whitespace, strip trailing punctuation, sorted normalized option labels) hashed with SHA-256, truncated to 16 hex chars, and used by BOTH hosts through the shared module (R4.1a, A19). The validator fills `fingerprint` on every valid entry from this function.
  - Depends on: E-01
  - Expected outcome: two texts differing only in case, whitespace and trailing `?` produce one fingerprint; different option sets produce different fingerprints; the worker-proposed value is ignored.
  - Execution state: pending

### Task group 2: tell the worker

- [ ] E-03 Extend the execute prompt (`runner_shared.build_prompt`) and its outcome-JSON literal with the `questions` field: when a material question is the HUMAN'S to decide under the askme three-way sort (cite `.aw/system/workflows/askme/askme.md` 'Establish facts before asking'; do not restate it, R2.5), record it in `questions[]`, finish all independent work, and exit normally; never prompt and never wait (R2.3). A question it resolves itself still gets a `D-*` row (R2.6). Keep `deferred_question_ids` for compatibility but say `questions[]` supersedes it.
  - Depends on: E-01
  - Expected outcome: the rendered execute prompt for a fixture item contains the `questions` literal and the askme citation, on both hosts.
  - Execution state: pending

- [ ] E-04 Give an ISOLATED review turn the same carrier: append to the in-lane statement that `build_review_prompt` already emits on its own lines the outcome path and the `questions` instruction, and make the review-turn post-processing in `execute_item_core` read that outcome with `read_recorded_outcome` when present. A review that writes no outcome behaves exactly as today.
  - Depends on: E-01
  - Expected outcome: a review fixture whose scripted host writes an outcome with one valid question exposes that question to the driver; a review that writes none is unchanged.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_question_carrier.py`: validator cases (E-01), fingerprint determinism and host parity (E-02, called through `oc_runipd` and `agy_runipd` re-exports), prompt contents on both hosts (E-03), the A10a/A10b/A31 contract (a scripted worker that records a `D-*` row and no question is NOT parked; one that returns a gating question IS; the prompt names the askme sort that decides between them), and the review-turn read (E-04) using the scripted-host pattern of `tests/test_run_proposal_channel.py`.
  - Depends on: E-04
  - Expected outcome: the module passes and each test asserts on returned values, rendered prompt text, or driver-visible state.
  - Execution state: pending

## Project conventions discovered (Step 0)

- New outcome fields follow `validate_proposal` / `validate_defect_report`: tolerant, never raising, bounded, sanitized, with a verdict object (`runner_shared`).
- Both hosts reach shared behavior through `runner_shared`; host modules only re-export (`oc_runipd.py` / `agy_runipd.py` import blocks).
- `/askme` owns the decide-or-ask rule; other text cites it (spec `6kwd2e` R2.5).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `build_prompt` instructs prose-only deferred questions ("record a DEFERRED question with the work completed...").
- `deferred_question_ids` is read only by `render_stream` for one reason line.
- A review turn is a bare slash command (`build_review_prompt` docstring: "Deliberately prose-free ON THE COMMAND LINE"), so its carrier must ride the in-lane statement lines, not the command line.

## Proposed changes (ordered, validatable)

1. E-01 validator. 2. E-02 fingerprint. 3. E-03 execute prompt. 4. E-04 review route. 5. E-05 tests. Each is independently testable.

## Deferred / out of scope (with reason)

- Cross-item deduplication and ordering: Order 08 (`jshwxb`).
  - Carrier: jshwxb
- Acting on a valid question: Order 02 (`epsti7`).
  - Carrier: epsti7

## Scope check

- Over-scope: none.
- Under-scope: none. The validator, fingerprint, both prompts and their test are all in this plan.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_carrier.py` and the routine gate `python3 -m pytest`.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R2 and R4.1a as written; no spec text changes.

## Open questions

### OQ-01: Should review turns use the same outcome file as execute turns?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED from repository evidence: yes. `read_recorded_outcome` already resolves the per-position outcome path for any item, and spec `6kwd2e` 0.35 says the mechanism is uniform across both actions; a second carrier would need a second parser.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session printing the verdict for valid, absent, and each malformed case named in E-01, showing the named field in each diagnostic.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste output showing equal fingerprints for the case/whitespace/punctuation variants, a different fingerprint for a different option set, and that a worker-supplied fingerprint is not used; computed through both `oc_runipd` and `agy_runipd`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `questions` literal and the askme citation from a rendered execute prompt on each host.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the passing test output for the review-turn read case and the unchanged no-outcome case.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the runner output of `python3 -m pytest -o addopts="" -q tests/test_question_carrier.py` and of the routine gate, including the `N passed` lines.
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
