# IPD: Sweep pre-existing open questions before dispatch

- Date: 2026-10-17
- Kind: child
- Concern: Questions that already exist before a run starts (`### OQ-*` blocks with `- Status: open` in queued artifacts) are never put to the human by a runner: `/plan-review` NO-GOs on any open question, and the runners never read open questions at dispatch (spec `6kwd2e` 0.2, R1). Spec R1 requires a pre-flight sweep that collects them across the resolved queue, asks a present human in one bounded batch with a human-scale timeout, records each answer durably IN THE ARTIFACT before the next question, and parks the rest.
- Scope: IN: collecting open OQ blocks across the resolved queue (whatever types it holds, not a hardcoded plans tree), a new bounded free-text prompt distinct from `prompt_for_gate_phrase` (R1.3: `select` with a configurable human-scale timeout, never `readline()`/`input()`), `--blocking-only`, durable artifact write-back (`- Status: resolved`, rationale naming the human and date, `- Blocking:` unchanged) committed through the tooled path, running at the pre-flight gate seam beside `enforce_draft_admission_gate`, and presence decided only by `is_interactive_run` (R7.1). Unanswered questions under an unattended run are written to the inbox (Order 03) as open questions so `aw runs answer` and channels can answer them. OUT: cross-question dedup (Order 08 owns `question_fingerprint` reuse and ordering; this plan calls it if present and otherwise asks in queue order).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/question_inbox.py, agent_workflows/ipd_lint.py, tests/test_question_preflight.py
- Item-Dependencies: executed:mtmqlm
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 4kkcex

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Put every already-known open question in the queue to a present human before any work starts, keep each answer in the artifact itself, and route the rest to the inbox (spec `6kwd2e` R1).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: collect and ask

- [ ] E-01 Add `collect_preflight_questions(repo, queue) -> list[PreflightQuestion]` in `runner_shared.py` reading every queued artifact's open `### OQ-*` blocks through the existing OQ parser (`ipd_lint.check_open_questions` / `ipd_schema.OQ_FIELDS`), default scope all open questions, `--blocking-only` narrowing to `Blocking: yes` (R1.1, R1.2). Register `--blocking-only` and `--question-timeout SECONDS` (default 300) on both hosts' `start` parsers.
  - Depends on: none
  - Expected outcome: for a fixture queue with 3 artifacts holding 2 blocking and 2 non-blocking open questions, the collector returns 4, and 2 with `--blocking-only` (A1).
  - Execution state: pending

- [ ] E-02 Add `prompt_for_free_text(question, *, timeout, stream) -> str | None`: refuses when `is_interactive_run` is false; uses `select` with the given timeout on stdin and reads available bytes non-blockingly; returns None on timeout (meaning PARK, not refuse). It must not call `input()` or `readline()` (R1.3, R1.3a, A2, A16, A27).
  - Depends on: E-01
  - Expected outcome: with a patched clock it returns None on timeout without blocking; its default timeout differs from `GATE_PROMPT_TIMEOUT`; with `--unattended` and a TTY it returns None without writing a prompt (A14, A41).
  - Execution state: pending

### Task group 2: record and route

- [ ] E-03 Run the sweep at the pre-flight seam (both hosts, beside `enforce_draft_admission_gate`, after selection resolves and before any dispatch, R1.4, A28). Before the first question print the sitting's shape: distinct questions, artifacts affected (R4.4 subset). For each answer, write it into the artifact immediately (set `- Status: resolved`; rationale `answered by <OS user> via aw run pre-flight on <date>: <answer>`; leave `- Blocking:` unchanged) and commit it through `aw commit --no-plan` with the run id in the message BEFORE asking the next question (R1.5, R1.7, A40, A18).
  - Depends on: E-02
  - Expected outcome: after answering 2 of 4 questions and timing out on the third, the two artifacts read `- Status: resolved` with the rationale, their `- Blocking:` lines are unchanged, and a commit exists per answer.
  - Execution state: pending

- [ ] E-04 Route unanswered pre-flight questions to the inbox: write each as an open question (`action: preflight`, artifact hash at sweep time) so `aw runs answer` can answer it later, and treat the owning item like a parked item (do not dispatch it while a `Blocking: yes` question on it is open). An inbox answer to a pre-flight question is written back into the artifact by the same function as E-03 when consumed (hook into Order 04's `consume_answers`).
  - Depends on: E-03
  - Expected outcome: under `--unattended`, a queue with one blocking open question writes it to `questions/`, holds that item, and dispatches the others; answering via `aw runs answer` resolves it in the artifact at the next checkpoint and the item then dispatches.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_question_preflight.py` on both hosts covering A1, A2, A14, A16, A18, A27 (behavioral: a patched `select` and a stdin that never yields must not hang the test), A28, A40, A41, and the unattended inbox route (A47: under `--unattended` with a TTY no prompt is shown, the inbox is written, and an answer from `aw runs answer` is consumed at the next checkpoint).
  - Depends on: E-04
  - Expected outcome: the module passes on both hosts.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Front-loaded prompts all sit at one pre-flight seam (spec `25kzda` :278; `enforce_draft_admission_gate`).
- `is_interactive_run` is the only presence predicate (spec `6kwd2e` R7.1).
- Record answers durably in the artifact, never only in the gitignored run directory (`askme.md` 'Record project decisions').
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `prompt_for_gate_phrase` is an admission gate with a short timeout where silence means refuse; free text needs silence to mean park (spec `6kwd2e` R1.3).
- The runners never read OQ blocks at dispatch (exploration 2026-10-17).

## Proposed changes (ordered, validatable)

1. E-01 collect. 2. E-02 bounded prompt. 3. E-03 ask and record. 4. E-04 inbox route. 5. E-05 tests.

## Deferred / out of scope (with reason)

- Fingerprint dedup and unblock-count ordering of the batch: Order 08 (this plan asks in queue order until 08 lands).
  - Carrier: jshwxb

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_preflight.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R1 and R7.1; the unattended inbox route is R9.7.

## Open questions

### OQ-01: Commit each pre-flight answer immediately, or batch them?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: immediately, one tooled commit per answer. R1.7 requires each answer durable before the next question so an interrupted sitting loses nothing; a batched commit would lose every answer given before an interrupt.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the collector output for the fixture queue with and without `--blocking-only`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test output proving timeout returns None under a patched clock, the default timeout value next to `GATE_PROMPT_TIMEOUT`, and the no-prompt result under `--unattended` with a TTY.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the two artifacts' OQ blocks after the sitting and `git log --oneline -3` showing one commit per answer (produced by E-03 at the pre-flight seam).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the unattended run's `questions/` listing, the held item's status, and the artifact's OQ block after `aw runs answer` and the next checkpoint.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
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
