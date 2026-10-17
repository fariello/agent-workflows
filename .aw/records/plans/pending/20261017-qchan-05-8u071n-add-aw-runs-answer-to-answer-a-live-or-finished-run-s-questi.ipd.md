# IPD: Add aw runs answer to answer a live or finished run's questions

- Date: 2026-10-17
- Kind: child
- Concern: With the inbox (Order 03) and live consumption (Order 04) in place, a human still has no tool to answer. Spec `6kwd2e` R9.5 (amended 2026-10-17) requires `aw runs answer` as the reference adapter: list a run's (or every live run's) open questions and answer them from a second terminal, interactively or with flags, writing only through the shared answer writer. It also requires `aw runs questions` to work against a live runner run (R4a.2); today it reads only `.aw/workflow-artifacts/<workflow>/<run-id>/open-questions.md`, which runner runs never write (`run_cli._run_questions`).
- Scope: IN: the `answer` leaf under `aw runs` (registered with the other run-family leaves in `cli.py`), interactive and non-interactive forms, `--agent`/`--json` output, listing across live runs when no run id is given, and pointing `aw runs questions` at a runner run directory's inbox when the run id names one. OUT: chat channels (Orders 09-11).
- Scope-Paths: agent_workflows/run_cli.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/question_inbox.py, tests/test_runs_answer.py, CHANGELOG.md, docs/cli-output-contract.md
- Item-Dependencies: executed:mtmqlm
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 5
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8u071n
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let a human answer a waiting question from any terminal while the run keeps going, with one command (spec `6kwd2e` R9.5, R4a.2).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the verb

- [ ] E-01 Register `aw runs answer [<run-id>] [<question_id>] [--answer TEXT | --choice N]` DIRECTLY on `runs_sub` in `cli.py`, the way `analyze` is registered, NOT through `_register_run_leaf` (which adds a REQUIRED single `target` positional and would make both positionals mandatory) and NOT by adding it to `run_viewer.RUNS_VIEWER_LEAF_NAMES` (that tuple feeds `_register_run_leaf` and the unresolvable-target suggestion list). `run-id` and `question_id` are `nargs="?"`; `--answer` and `--choice` are mutually exclusive; `--dir`/`--repo` defaults to `argparse.SUPPRESS` as on the other `runs_sub` leaves. Dispatch it in `run_cli.run_cli` beside `decisions`/`questions`. Declare it in `command_surface.COMMAND_INVENTORY` as `command="runs answer"`, `command_class="mutation"`, `mutation_gate="none"` (it writes only through the shared writer, and only when a human gives an answer), `legacy_flags=("--answer", "--choice", "--agent", "--json")`, `exit_contract=(0, 1, 2)`. Update the two `aw runs` help strings in `cli.py` that name the "FOUR exceptions" to read-only (`_RUNS_DESCRIPTION` and the `"runs"` entry of the family help table) so they name `answer` as a fifth, and add an `aw runs answer` line to `_RUNS_EPILOG`. Resolve a run id through `runner_shared.state_root(repo)` (never a hardcoded `.aw/records/runs/`, which is wrong under a companion records backend) and accept only a directory holding `state.json`. With no run id, enumerate run directories under `state_root` whose `run_viewer.driver_holder_state` is `HOLDER_LIVE` or `HOLDER_UNKNOWN` (unknown is listed and labelled `liveness unknown`, never dropped), and that hold at least one open question.
  - Depends on: none
  - Expected outcome: `aw runs answer --help` documents both forms and the exit codes; `aw runs answer` with no arguments parses (both positionals optional); an unknown run id exits 2; `aw runs --help` names `answer` among the exceptions; `tests/test_conformance_matrix_structure.py` and `tests/test_command_surface_declarations.py` pass with the new leaf.
  - Execution state: pending

- [ ] E-02 Interactive form, entered only when `term.is_interactive()` is true and no `--answer`/`--choice` was given: for each open question (`question_inbox.read_open_questions`) show the text, artifact id6, numbered options and an evidence summary, with every agent-authored field passed through `term.strip_ansi` and stripped of other control characters except newline and tab, because question text comes from a worker turn and must not drive the operator's terminal. Read a free-text answer or an option number with a plain blocking read (this is the human's own process, not the runner, so spec `6kwd2e` R9.4a does not apply); refuse free text when the question's `allow_free_text` is false and re-prompt; an empty line skips the question. Write each answer through `question_inbox.write_answer` with `channel="cli"`, `actor="human"`, `sender=getpass.getuser()` and only then show the next question (R1.7's rule). Print `recorded`, `already answered`, or the writer's refusal reason for each. EOF or Ctrl-C ends the session keeping every answer already written. Exit 0 when at least one answer was recorded, otherwise 1.
  - Depends on: E-01
  - Expected outcome: answering two questions in one session writes two answer files in order; answering an already-answered one prints `already answered` and writes nothing new; a question text containing an ANSI escape is printed without the escape byte; EOF after the first answer leaves that answer on disk.
  - Execution state: pending

- [ ] E-03 Non-interactive form and machine output. `--answer`/`--choice` REQUIRES both a run id and a question id (else exit 2 with a usage message) and writes one answer without prompting. When stdin is not interactive (or `--no-interactive`) and no answer flag is given, list the open questions and exit without prompting. Exit codes: 0 recorded or questions listed; 1 nothing open, `already answered`, or a writer refusal on a valid question (out-of-range choice, free text not allowed, over-length, question `answered` or `stale`); 2 bad invocation, unknown run, or a qid the writer refuses as malformed or absent. `--agent` emits exactly ONE `aw.agent/v1` `result` record (through `agent_schema`, not `run_cli._emit_machine`, whose bare-JSON shape is the `aw runs` family exemption; spec `6kwd2e` R9.5 and A45 require this leaf to emit an `aw.agent/v1` result instead) with `outcome` and `exit` equal to the process exit code, and carrying either `questions` (each with `run_id`, `question_id`, `artifact_id6`, `text`, `options`, `allow_free_text`, `gates_verdict`) or `answer` (`run_id`, `question_id`, `status` = `recorded`/`already`/`rejected`, `reason`). `--json` emits the same payload pretty-printed. Every path in the output is repo-relative (`agent_schema.normalize_repo_path`).
  - Depends on: E-02
  - Expected outcome: the non-interactive form exits 0 and writes the same record shape as the interactive form; `--agent` output parses as one JSON object passing `agent_schema.validate_agent_record` with `exit` equal to the process exit code; an `already` answer exits 1; a malformed qid exits 2.
  - Execution state: pending

### Task group 2: questions verb and docs

- [ ] E-04 Make `aw runs questions <run-id>` read `<run_dir>/open-questions.md` (written by `question_inbox.write_projection`, Order 03 E-03) when the target resolves to a runner run directory under `runner_shared.state_root(repo)`; otherwise keep the current `workflow-artifacts` lookup unchanged, so Set runs and the ledger fixture behave exactly as today (`tests/test_live_conformance_sweep.py` expects exit 1 for `runs questions` on its ledger fixture). A runner run that exists but has never parked a question reports none open (exit 1), not a missing projection. Update the `questions` leaf help in `cli.py`, which today says it reads only `.aw/workflow-artifacts/<workflow>/<run-id>/`. Add a `CHANGELOG.md` entry (user-facing prose, no em or en dashes) describing `aw runs answer` and the runner-run support of `aw runs questions`. Add one sentence to `docs/cli-output-contract.md` Section 3.1, beside the existing `aw run init` exception, stating that `aw runs answer` emits `aw.agent/v1` records under `--agent` and stays within exits 0-2.
  - Depends on: E-03
  - Expected outcome: against a live scripted run with one parked item, `aw runs questions <run-id>` prints the question and exits 0 (A10c); against the ledger fixture it still exits 1; against a runner run with no parks it exits 1.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_runs_answer.py` (asserts spec `6kwd2e` A45 and A10c) driving the CLI as a subprocess. Two fixtures: (a) a run directory under a temporary repo's `state_root` built with Order 03's `question_inbox.write_question`; (b) a LIVE run: a real driver run with the scripted-host pattern (`tests/test_run_proposal_channel.py`) in which item 1 parks through Order 02/03's park branch and item 2's scripted turn blocks on a file barrier, so the driver holds `driver.lock` and is still dispatching while the test runs `aw runs questions` and `aw runs answer`, then releases the barrier. Cover: interactive answers via stdin (forced with `--interactive`), non-interactive form, `--agent` record validation, `--json`, already-answered, unknown run, unknown and malformed qid, out-of-range choice, free text refused when not allowed, ANSI stripped from question text, EOF mid-session keeping earlier answers, no-run-id listing across live runs, `aw runs questions` mid-run (A10c), and the unchanged Set-run/ledger path.
  - Depends on: E-04
  - Expected outcome: the module passes, and the routine gate passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run-family leaves taking one required `target` are registered in `cli.py` through `_register_run_leaf` from `run_viewer.RUNS_VIEWER_LEAF_NAMES`; leaves with a different positional shape (`analyze`, `query`, `export`, `submit`) are registered directly on `runs_sub`. `_ViewerOrLeafSubParsersAction` routes any registered leaf name. `run_cli.run_cli` dispatches the ledger leaves by `runs_command`.
- The `aw runs` help text names its mutating exceptions explicitly ("FOUR exceptions, named rather than counted"), so a new mutating leaf must be named there.
- `aw runs` leaves emit bare JSON under the documented family exemption (`docs/cli-output-contract.md` Section 3.1; `tests/conformance_matrix.py` `sanctioned_raw`); a leaf that emits `aw.agent/v1` is bound to exits 0-2.
- Runner run directories resolve through `runner_shared.state_root`, liveness through `run_viewer.driver_holder_state` (flock acquirability; `HOLDER_UNKNOWN` is never treated as dead).
- The interactivity decision is `term.is_interactive`.
- Every verb's exit codes are declared in `command_surface`.
- CHANGELOG entries are user-facing prose (AGENTS.md: no em or en dashes).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `run_cli._run_questions` reads only `.aw/workflow-artifacts/...` (`_projection_dir` -> `set_records.run_artifacts_dir`), so it returns 2 for every runner run today (spec `6kwd2e` R4a.1 note).
- `_register_run_leaf` adds a required `target`, so it cannot express `answer`'s two optional positionals.
- `question_inbox` does not exist yet; it lands with Order 03 (`mtmqlm`), whose `write_answer` validates the qid (`QID_RE`), the choice, free-text permission, length and control characters, and records the `human_answer` event. This plan relies on those refusals rather than duplicating them.

## Proposed changes (ordered, validatable)

1. E-01 register. 2. E-02 interactive. 3. E-03 non-interactive/agent. 4. E-04 questions verb + changelog. 5. E-05 tests.

## Deferred / out of scope (with reason)

- Answering from a chat app: Orders 10-11.
  - Carrier: qrup8m, mrlblc

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_runs_answer.py tests/test_conformance_matrix_structure.py tests/test_command_surface_declarations.py tests/test_live_conformance_sweep.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

Implements spec `6kwd2e` R9.5 and R4a.2 as amended; no spec file is edited. Documentation: `CHANGELOG.md`, the `aw runs` help text in `cli.py`, and `docs/cli-output-contract.md` Section 3.1 (E-04), because the new leaf is the first `aw runs` leaf that emits `aw.agent/v1` records.

## Open questions

### OQ-01: Should `aw runs answer` live under `aw runs` or `aw run`?

- Blocking: no
- Status: resolved
- Owner: plan author (settled by spec `6kwd2e` R9.5, which names the verb; recorded at review as decision D-1)
- Resolution or deferral rationale: RESOLVED: `aw runs`. It sits beside the read verbs `questions` and `decisions` that a human already uses to inspect a run, and spec `6kwd2e` R9.5 names it `aw runs answer`. It mutates only the inbox, never the ledger beyond the `human_answer` record the writer adds.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw runs answer --help`, the exit code of an unknown run id, the `aw runs --help` line naming `answer` as an exception, and the passing output of `tests/test_conformance_matrix_structure.py` and `tests/test_command_surface_declarations.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a transcript of the interactive form (forced with `--interactive`) answering two questions via piped stdin, `ls` of the answer files afterwards, the `already answered` line for a repeat, and the output for a question whose text contains an ANSI escape shown through `cat -v` with no `^[` present.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the non-interactive command, its exit code, its `--agent` output line and the result of `agent_schema.validate_agent_record` on it, plus the exit codes of an `already` answer (1) and a malformed qid (2).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw runs questions <run-id>` output and exit code captured while the scripted run's item 2 is blocked on its barrier (the driver holds `driver.lock`; produced by Order 03 E-03's park-time `write_projection` and E-04's runner-run lookup), the exit code against the ledger fixture (1), and the `CHANGELOG.md` and `docs/cli-output-contract.md` diffs.
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
