# IPD: Never report a coverage answer as recorded when it was not written

- Date: 2026-10-06
- Kind: child
- Concern: `aw ipd coverage` asks the model, gets an answer, and then may silently fail to save it while still reporting success. Measured 2026-10-06 while authoring this Set: on the uncommitted orchestrator `67lvds`, `aw ipd coverage 67lvds` printed only "Orchestrator 67lvds is ready for review." and exited 0, but wrote nothing into the plan; the `--agent` record showed `"written": false, "committed": false` and spent one model call (`"calls": 1`). The cause is `coverage_record.write`: with `commit=True` it checks `git status --porcelain -- <plan>` first and, when the plan has uncommitted changes, returns `written=False` with the detail "plan file ... already has uncommitted changes; record not written". `runner_shared.probe_orchestrator` keeps that detail only inside `ProbeOutcome.detail`, and `orchestrator_readiness.review_readiness` turns a `no-executions` answer into `ready=True` without looking at `written`. The human output of `run_coverage` prints "(record written, ...)" only when written and prints nothing otherwise, so the operator is told the plan is ready while every model-free gate (`aw ipd lint`, `aw check`, `aw ipd set`) still refuses it for having no record. The same silent loss can happen at every asking consumer of spec `25kzda` 2.5d: the production action, the post-review check, and the retirement-time re-check, each of which would then refuse later for a record they were told was established.
- Scope: IN: make an answer that could not be recorded a finding, not a pass. In `orchestrator_readiness.review_readiness`, when `ask=True` and the probe answered (pass or fail) but `written` is False, add a finding `coverage-record-not-written` naming the reason from the write result and the remedy (commit or stash the plan's changes, or pass `--no-commit` to write without committing), so `ready` is False; carry the write result's detail on `ProbeOutcome` as its own field instead of folding it into `detail`; print the reason in `run_coverage`'s human output; exit 1 (findings), not 0. Decide and record the write behavior for a dirty plan: write the record without committing it (so the answer is not lost) and report `committed: false` with the reason, rather than discarding the answer, unless measured evidence shows that writing into a dirty file can sweep in someone else's edit through a later commit, in which case keep refusing and say so. OUT: the coverage record format; the probe prompt; the run-start gate's handling (it already records a known hole when it cannot proceed cleanly; confirm it does not report a pass for an unwritten answer and fix it in the same way if it does).
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/runner_shared.py, agent_workflows/coverage_record.py, tests/test_coverage_not_written.py, tests/test_orchestrator_probe_quotes.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 6
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7kczdo

## Workflow history
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 06 of Set `runfresh` at the maintainer's instruction ("Add it."), after the defect was found while recording `67lvds`'s own coverage answer. Independent of Orders 01 to 05.

## Goal

Make every place that asks the coverage question either save the answer or say plainly that it did not, so no command reports a plan ready while its answer is missing from the plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: decide what happens to a dirty plan

- [ ] E-01 Decide the write behavior for a plan with uncommitted changes. Measure first: in a fixture repository, give the plan an uncommitted edit, write the record without committing (call `coverage_record.write(..., commit=False)`), then run the normal commit paths that could later commit that file (`aw commit <plan> -- <path>`, `aw ipd set <status> <id6> --commit`) and record whether each commits the record together with the uncommitted edit, and whether that loses or misattributes anyone's work. If writing without committing is safe, make `write` with `commit=True` on a dirty plan write the record, skip the commit, and return `written=True, committed=False` with the reason; otherwise keep refusing to write and say why. Record the measurement and the decision in OQ-01. If the behavior changes, update the existing pin `tests/test_orchestrator_probe_quotes.py::TestGitCommitOnWriteAndDirtyPlan::test_dirty_plan_is_not_written_or_committed` (it asserts "already has uncommitted changes; record not written" and no `- Coverage:` line) to assert the new outcome rather than deleting it; if the behavior is kept, leave that file untouched and acknowledge it at finalize with `--scope-ack`.
  - Depends on: none
  - Expected outcome: OQ-01 records the measurement and the chosen behavior; `coverage_record.write` on a dirty plan behaves as chosen and always returns a non-empty reason when it did not do both write and commit.
  - Execution state: pending

### Task group 2: never report an unrecorded answer as a pass

- [ ] E-02 Add `write_attempted: bool = False` and `write_detail: str = ""` fields to `ProbeOutcome`, set in `probe_orchestrator`'s two write branches from the write result, leaving `detail` for the probe's own text. In `orchestrator_readiness.review_readiness`'s `ask=True` branch, when the outcome is not cached, `write_attempted` is True and `written` is False, add a finding with a new code constant `CODE_COVERAGE_NOT_WRITTEN = "coverage-record-not-written"`, the write reason as detail, and a remedy constant naming the fix (commit or stash the plan's changes, or re-run with `--no-commit` if E-01 kept the refusal), so `ready` is False. Gate on `write_attempted`, NOT on the answer: `probe_orchestrator` writes nothing for an `executions` answer without quotes or for `could-not-ask`, and those already carry their own findings, so they must not gain a second one. Add the new code to `CONDITION_4_CODES`, because the retirement-time re-check in `runner_shared.dispatch_orchestrator_item` filters readiness findings by that set and would otherwise retire on an answer it did not record. Add `write_detail` to `ReviewReadiness` and to `run_coverage`'s `--agent` per-orchestrator record, so a written-but-not-committed outcome carries its reason. A written-but-not-committed record is NOT a finding (the answer is saved); it is reported as `committed: false` with its reason.
  - Depends on: E-01
  - Expected outcome: an asking `review_readiness` whose record could not be written returns `ready=False` with one `coverage-record-not-written` finding; one whose record was written but not committed returns `ready=True`, `committed=False` and a non-empty `write_detail`; an `executions` answer without quotes yields its `coverage-fail` finding and no `coverage-record-not-written` finding; `CONDITION_4_CODES` contains the new code.
  - Execution state: pending

- [ ] E-03 Make `run_coverage`'s human output always say what happened to the record: "record written and committed", "record written, not committed: <reason>", or "record NOT written: <reason>", and exit 1 when any selected orchestrator's record was not written. Check the run-start gate (`enforce_orchestrator_probe_gate`) for the same case: when it proceeds on a pass whose record was not written, it must say so in its output and event; add that if missing.
  - Depends on: E-02
  - Expected outcome: `aw ipd coverage <id6>` on a dirty plan never prints only "ready for review"; it prints the record outcome and exits as specified.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_coverage_not_written.py` driving the real `aw ipd coverage` command IN-PROCESS through `agent_workflows.cli.main(["ipd", "coverage", <plan>, ...])` with the working directory set to a fixture repository, `runner_shared.ask_orchestrator_probe` replaced by a double (`mock.patch.object`), and stdout captured, asserting the return code and printed text: a clean committed plan (written and committed, exit 0); a dirty plan (outcome per E-01, with the human text and the `--agent` record both stating it, and the exit code); the `--no-commit` case; plus a `review_readiness(ask=True, asker=...)` unit case for the not-written finding and one for the retirement-time re-check refusing on it (drive `dispatch_orchestrator_item`'s retire path with an `asker` double, or assert the finding's code is in `CONDITION_4_CODES` and the re-check's filtered list is non-empty). A SUBPROCESS cannot be used for the asking cases: no seam reaches a child process, a pre-arranged current record makes the command skip the ask entirely, and under pytest the child inherits `PYTEST_CURRENT_TEST`, so the real spawn is refused by `runner_shared._assert_probe_spawn_is_permitted`. Prove the test can fail by removing the E-02 finding and pasting the dirty-plan case passing as "ready" (the old defect).
  - Depends on: E-03
  - Expected outcome: the new file passes; the mutation reproduces the 2026-10-06 behavior and fails the test; existing coverage and readiness tests pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `coverage_record.write` refuses to write into a dirty plan with `commit=True` to avoid committing someone else's in-flight edit (its docstring: "checks if `git status --porcelain -- <plan>` shows uncommitted changes BEFORE writing; if so, returns without writing or committing"). E-01 measures whether writing without committing keeps that protection.
- `aw commit` COMMITS ONLY THE INTERSECTION of the paths named and what it staged, so a later `aw commit` of the plan would include both the record and any other uncommitted edit to the same file; that is the case E-01 must measure.
- A finding, not a silent flag, is how readiness reports a problem (spec `25kzda` 2.5d "EVERY REFUSAL names the failing condition").
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The 2026-10-06 measurement: `aw ipd coverage 67lvds --agent` on the uncommitted plan returned `"ready":true,"cached":false,"calls":1,"written":false,"committed":false`; the human form printed only "Orchestrator 67lvds is ready for review." with exit 0; the plan had no `- Coverage:` line afterwards; `aw ipd lint` then reported `IPD-S408: coverage-record-absent`. After committing the plan, the same command returned `"written":true,"committed":true`. | the two `--agent` records and the lint output, captured in this session |
| F-02 | The reason is produced and dropped. `coverage_record.write` returns detail "plan file ... already has uncommitted changes; record not written"; `probe_orchestrator` appends it to `detail`; `review_readiness` reads only `answer`, `cached`, `calls`, `written`, `committed` and never turns `written=False` into a finding. | `coverage_record.write`; `probe_orchestrator`'s write branches; `review_readiness`'s `ask=True` branch |
| F-03 | The human renderer is silent when not written: `run_coverage` prints "(record written, committed=...)" only under `elif r.written:`. | `run_coverage` human rendering |

## Proposed changes (ordered, validatable)

1. Measure and decide the dirty-plan write behavior (E-01).
2. Carry the write reason separately and make an unwritten answer a finding (E-02).
3. Always print the record outcome; exit 1 when not written; check the run-start gate (E-03).
4. Subprocess tests with a mutation reproducing the old behavior (E-04).

## Deferred / out of scope (with reason)

- AUTO-COMMITTING A DIRTY PLAN TOGETHER WITH THE RECORD. That would commit someone else's in-flight edit under the tool's name, which the existing refusal exists to prevent.
  - Carrier-Declined: the existing protection is correct; this plan only stops the silent loss

## Scope check

- Over-scope: none. Three production modules, one new test file, and one existing test file that changes only if E-01 changes the dirty-plan behavior.
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_coverage_not_written.py tests/test_orchestrator_readiness.py tests/test_coverage_record.py tests/test_orchestrator_probe_quotes.py -q` pasted.
- E-01's measurement pasted.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec edited. Spec `25kzda` 2.5d already requires every refusal to name its failing condition and 2.5e requires only the tool to write the record; this plan makes the asking consumers honor both when the write does not happen.

## Open questions

### OQ-01: On a dirty plan, write the record without committing, or refuse to write?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: to be resolved by E-01's measurement, which the executor records here. Either answer is acceptable to this plan because E-02 and E-03 make the outcome visible; what is not acceptable is the current behavior of discarding a paid answer while reporting success.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the fixture measurement for each later commit path (what it committed), the decision recorded in OQ-01, the `coverage_record.write` diff, and a test or REPL run showing its dirty-plan return value and reason.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `ProbeOutcome`, `ReviewReadiness`, `CONDITION_4_CODES` and `review_readiness` diffs and the unit outputs for not-written (`ready=False`, one `coverage-record-not-written` finding), written-not-committed (`ready=True`, `committed=False`, non-empty `write_detail`), and an `executions` answer without quotes (no `coverage-record-not-written` finding).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw ipd coverage` human output and exit code for clean, dirty and `--no-commit` fixtures; paste the run-start gate check result and diff if changed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test file passing with its count (and `tests/test_orchestrator_probe_quotes.py` passing, with its diff if E-01 changed the behavior); the retirement re-check case's output; the mutation reproducing "ready for review" on the dirty plan and failing the test; the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
