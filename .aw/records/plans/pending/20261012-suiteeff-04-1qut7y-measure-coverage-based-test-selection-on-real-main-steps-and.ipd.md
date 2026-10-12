# IPD: Measure coverage-based test selection on real main steps and adopt it for agent iteration only if it pays

- Date: 2026-10-12
- Kind: child
- Concern: Exact-tree caching (Order 02) reuses only identical trees (19% of October's baselines). Consecutive `main` tips differ by a median of 1 package file and 1 test file, but STATIC selection cannot exploit that: the median test file transitively imports 154 of 186 package modules, so a one-file step invalidates 92% of test files. Coverage-level selection (pytest-testmon records which code blocks each test executes and reruns only tests whose blocks changed) could, but its saving on this repo is unmeasured, and the hub modules (`runner_shared.py` 43,720 lines, changed in 72 of 283 consecutive steps; `cli.py` 58) may defeat it. It also carries risks the exact cache does not: it can miss tests affected through data files, subprocess-only paths, or dynamic imports.
- Scope: IN: a measurement, recorded as a research findings artifact, replaying at least 20 consecutive real `main` steps from October through pytest-testmon in a scratch worktree, reporting per step the selected-test fraction, wall time versus the full suite, and selection RECALL (does the selected set include every test that fails at that step; checked by also running the full suite at each step); a stated adoption threshold; and ONLY IF the threshold is met, an opt-in `aw suite --select` path for agent iteration that never feeds the integration gate. OUT: using selection for the runner's integration gate or baseline (the full suite stays the authority); adding `pytest-testmon` as a hard dependency (it becomes an optional `[test]` extra only on adoption).
- Scope-Paths: .aw/records/research/, agent_workflows/suite_cache.py, agent_workflows/cli.py, agent_workflows/runner_shared.py, pyproject.toml, tests/test_suite_select.py, docs/cli-human-guide.md, CHANGELOG.md
- Item-Dependencies: executed:0o0wt2
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1qut7y

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 04 of Set `suiteeff` from backlog `58x9mw`.

## Goal

Know, from measurement on this repository's own history, whether coverage-based selection would cut agents' iteration suites substantially without missing failures, and adopt it for agent iteration only if it does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure

- [ ] E-01 Run the measurement on a quiet host (record `uptime` before and after; abort and retry later if load average exceeds the core count). In a scratch detached worktree (`git worktree add --detach`, removed afterwards), with `pytest-testmon` installed in a throwaway venv (never the operator's), take the 21 most recent consecutive distinct `main` first-parent commits from October whose diff touches `agent_workflows/` or `tests/`: build the testmon database with a full run at the first, then at each next commit run (a) `pytest --testmon` and (b) the full bare suite, recording per step: tests selected, tests total, wall time of each, failing node ids of each, and RECALL = |failing(full) intersect selected| / |failing(full)| (1.0 when the full suite has no failures). Record the exact commands.
  - Depends on: none
  - Expected outcome: a per-step table of 20 rows and the summary statistics: median and p90 selected fraction, median time saving, minimum recall, and the list of any missed failing tests with the reason.
  - Execution state: pending

- [ ] E-02 Record the measurement with `aw research new --kind findings --slug testmon-selection-measurement --apply` (do not hand-name it), including the table, the commands, the host load, the adoption THRESHOLD stated before reading the result (adopt iff median selected fraction <= 0.5 AND minimum recall == 1.0 over all 20 steps), and the decision ADOPT or DECLINE with its reason.
  - Depends on: E-01
  - Expected outcome: a research findings artifact under `.aw/records/research/` with a decision line.
  - Execution state: pending

### Task group 2: adopt (only on ADOPT) or record the decline

- [ ] E-03 IF E-02 decided ADOPT: add `aw suite --select` in `suite_cache.py`/`cli.py` that runs `pytest --testmon` against a testmon database kept beside Order 02's cache in the git common dir (one per interpreter/package digest), prints a banner "SELECTED RUN: not a full-suite verdict; run `aw suite` before reporting the suite green", never stores into or reads from the full-suite cache, and refuses with a clear message when `pytest-testmon` is not installed; add `pytest-testmon` to the `test` optional extra in `pyproject.toml`; add one sentence to the execute prompt template in `runner_shared.py` offering `aw suite --select` for iteration while still requiring `aw suite` before reporting green; add `tests/test_suite_select.py` (behavioral: in a fixture repo with two independent modules and tests, editing one module's function makes `--select` run only its test; the banner is printed; nothing is written to the full-suite cache). IF DECLINE: change no code, and record in this item's evidence that the decline completes it.
  - Depends on: E-02
  - Expected outcome: on ADOPT, the opt-in command and its tests; on DECLINE, no code change.
  - Execution state: pending

- [ ] E-04 On ADOPT only: a `docs/cli-human-guide.md` paragraph on `--select` and a `- Added:` CHANGELOG bullet, no em or en dashes; then run the bare suite and record its summary. On DECLINE: record "no docs change (declined)".
  - Depends on: E-03
  - Expected outcome: docs and changelog on ADOPT; nothing on DECLINE.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Research artifacts are created only through `aw research new` (AGENTS.md "Durable reference": do not hand-name research files).
- Measure end to end before claiming a performance result (AGENTS.md "INEFFICIENCY A USER CAN NOTICE IS A DEFECT": measure the command a user runs, warm and cold).
- The full suite is the integration authority (orchestrator `z3cqvz` Cross-IPD validation).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | Steps are small. | 283 consecutive October baseline commits: median 1 package `.py` file and 1 test file changed per step, p90 5 and 4. |
| F-02 | Static selection fails. | Median transitive import closure of a test file: 154 of 186 modules; median 92% of test files invalidated per step. |
| F-03 | Hub modules change often. | `runner_shared.py` changed in 72 of 283 steps, `cli.py` 58, `check_engine.py` 36. |

## Proposed changes (ordered, validatable)

1. Measure (E-01) and record with a pre-stated threshold (E-02).
2. Adopt behind an explicit opt-in, or record the decline (E-03, E-04).

## Deferred / out of scope (with reason)

- Selection for the integration gate or baseline: rejected; recall below 1.0 would merge red work.

## Scope check

- Over-scope: none; code paths are touched only on ADOPT.
- Under-scope: none.

## Required tests / validation

The measurement itself (E-01) runs both selected and full suites at every step; on ADOPT, `tests/test_suite_select.py` and a bare suite run.

## Spec / documentation sync

On ADOPT: `docs/cli-human-guide.md`, `CHANGELOG.md`. No spec governs test selection.

## Open questions

### OQ-01: Why a threshold of 0.5 selected and recall 1.0?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: below a 2x saving the extra machinery (a second database, a second mode agents must understand) is not worth its risk; and any missed failing test in 20 real steps means agents would be told "green" on red code during iteration, which then costs a failed integration. Stated before measuring so the result cannot move the bar.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted per-step table (20 rows), the `uptime` lines before and after, the exact commands, and `git worktree list` after cleanup showing the scratch worktree removed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the research artifact path, its pasted threshold and decision lines, and `aw research index --check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: on ADOPT, pasted passing `python3 -m pytest tests/test_suite_select.py` and a pasted `aw suite --select` run showing the banner and the selected count; on DECLINE, `git diff --stat` over the code Scope-Paths showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: on ADOPT, the docs and CHANGELOG diff with no em/en dash and the pasted post-change bare suite summary, plus a check that `--select` output is never recorded in the full-suite cache (list the cache dir before and after a `--select` run); on DECLINE, the pasted "no docs change (declined)" line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Ready for `/plan-review` then human approval. Depends on `0o0wt2` executed. A DECLINE is a complete, successful outcome for this plan. Commit only Scope-Paths via `aw commit 1qut7y -- <paths>`; never push; paste real output into each `V-*`.
