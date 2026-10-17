# IPD: Add aw runs answer to answer a live or finished run's questions

- Date: 2026-10-17
- Kind: child
- Concern: With the inbox (Order 03) and live consumption (Order 04) in place, a human still has no tool to answer. Spec `6kwd2e` R9.5 (amended 2026-10-17) requires `aw runs answer` as the reference adapter: list a run's (or every live run's) open questions and answer them from a second terminal, interactively or with flags, writing only through the shared answer writer. It also requires `aw runs questions` to work against a live runner run (R4a.2); today it reads only `.aw/workflow-artifacts/<workflow>/<run-id>/open-questions.md`, which runner runs never write (`run_cli._run_questions`).
- Scope: IN: the `answer` leaf under `aw runs` (registered with the other run-family leaves in `cli.py`), interactive and non-interactive forms, `--agent`/`--json` output, listing across live runs when no run id is given, and pointing `aw runs questions` at a runner run directory's inbox when the run id names one. OUT: chat channels (Orders 09-11).
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/question_inbox.py, tests/test_runs_answer.py, CHANGELOG.md
- Item-Dependencies: executed:mtmqlm
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 5
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8u071n

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let a human answer a waiting question from any terminal while the run keeps going, with one command (spec `6kwd2e` R9.5, R4a.2).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the verb

- [ ] E-01 Add `aw runs answer [<run-id>] [<question_id>] [--answer TEXT | --choice N]` in `run_cli.py`, registered beside `decisions`/`questions` in `cli.py` and in `command_surface` with exit contract 0 answered/listed, 1 nothing open, 2 bad invocation or unknown run. Resolve run ids against `.aw/records/runs/` (runner runs). With no run id, list open questions across every LIVE run (driver lock held) and choose interactively.
  - Depends on: none
  - Expected outcome: `aw runs answer --help` documents both forms and the exit codes; an unknown run exits 2.
  - Execution state: pending

- [ ] E-02 Interactive form: show each open question (text, artifact id6, options numbered, evidence summary), read a free-text answer or an option number with a plain blocking read (this is the human's own process, not the runner), write it through `question_inbox.write_answer` with `channel=cli`, `actor=human`, `sender=<OS user>`, and only then show the next question (R1.7's rule). Print `recorded`/`already answered`/the refusal reason for each.
  - Depends on: E-01
  - Expected outcome: answering two questions in one session writes two answer files in order; answering an already-answered one prints `already answered` and writes nothing new.
  - Execution state: pending

- [ ] E-03 Non-interactive form and machine output: `--answer`/`--choice` with an explicit question id writes one answer without prompting; `--agent` emits an `aw.agent/v1` result record listing open questions or the write outcome; `--no-interactive` with no answer flag lists and exits.
  - Depends on: E-02
  - Expected outcome: the non-interactive form exits 0 and writes the same record shape as the interactive form; `--agent` output parses as one JSON result record.
  - Execution state: pending

### Task group 2: questions verb and docs

- [ ] E-04 Make `aw runs questions <run-id>` read `<run_dir>/open-questions.md` (or the inbox directly) when the id names a runner run under `.aw/records/runs/`, keeping the current `workflow-artifacts` lookup for Set runs. Add a `CHANGELOG.md` entry (user-facing prose, no em or en dashes) describing `aw runs answer`.
  - Depends on: E-03
  - Expected outcome: against a live scripted run with one parked item, `aw runs questions <run-id>` prints the question and exits 0 (A10c).
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_runs_answer.py` driving the CLI as a subprocess against a fixture run directory and against a LIVE scripted run (driver still running on a later item): interactive answers via stdin, non-interactive form, `--agent`, already-answered, unknown question, and `aw runs questions` mid-run (A45, A10c).
  - Depends on: E-04
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run-family leaves are registered in `cli.py` (`_register_run_leaf`) and dispatched in `run_cli.main`.
- Every verb's exit codes are declared in `command_surface`.
- CHANGELOG entries are user-facing prose (AGENTS.md: no em or en dashes).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `run_cli._run_questions` reads only `.aw/workflow-artifacts/...`, so it returns 2 for every runner run today (spec `6kwd2e` R4a.1 note).

## Proposed changes (ordered, validatable)

1. E-01 register. 2. E-02 interactive. 3. E-03 non-interactive/agent. 4. E-04 questions verb + changelog. 5. E-05 tests.

## Deferred / out of scope (with reason)

- Answering from a chat app: Orders 10-11.
  - Carrier: qrup8m, mrlblc

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_runs_answer.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R9.5 and R4a.2 as amended.

## Open questions

### OQ-01: Should `aw runs answer` live under `aw runs` or `aw run`?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: `aw runs`. It sits beside the read verbs `questions` and `decisions` that a human already uses to inspect a run, and spec `6kwd2e` R9.5 names it `aw runs answer`. It mutates only the inbox, never the ledger beyond the `human_answer` record the writer adds.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw runs answer --help` and the exit code of an unknown run id.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a transcript of the interactive form answering two questions via piped stdin, and `ls` of the answer files afterwards.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the non-interactive command, its exit code, and its `--agent` output line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw runs questions <run-id>` output and exit code captured while the scripted run is still dispatching a later item, plus the CHANGELOG diff.
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
