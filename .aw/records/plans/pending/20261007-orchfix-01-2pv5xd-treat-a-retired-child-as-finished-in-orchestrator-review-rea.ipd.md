# IPD: Treat a retired child as finished in orchestrator review readiness and drop it from the child table

- Date: 2026-10-07
- Kind: child
- Concern: Retiring a child plan (`aw ipd set superseded|not-executed <child>`) leaves its orchestrator permanently unapprovable. Measured 2026-10-07: after `62pkkg` was retired `not-executed`, `aw set approved itamry` refused with `[child-status-not-ready] 62pkkg: child 62pkkg has status 'not-executed' (must be to-review, reviewed, approved, auto-approved, or executed)` and the remedy "bring the child to `to-review`", which is impossible for a retired plan and wrong advice. The cause: `orchestrator_readiness._READY_CHILD_STATUSES` admits `executed` but not the two retirement statuses, although the runner's own retirement predicate already treats every `ipd_schema.TERMINAL` status as having ended a child's participation (`runner_shared` "Every child `Status:` that ENDS its participation in a Set", derived from `ipd_schema.TERMINAL`). Separately, nothing updates the orchestrator when a child is retired, so its `## Child IPDs` table and checklist keep naming the child as live work.
- Scope: (1) Make orchestrator review readiness treat a child under a retirement directory with `Status: superseded` or `not-executed` as finished, exactly as it treats `executed`, and say so in its finding text when such a child is present; (2) when `aw ipd set superseded|not-executed` retires a child, append a dated `## Workflow history` line to its orchestrator naming the retired child, and print a hint naming the orchestrator; (3) amend spec `25kzda` Section 2.5d condition 2 to match. EXCLUDES rewriting the orchestrator's child table or checklist automatically (prose a human or review owns), changing retirement or coverage rules, and the refusal-message styling owned by plan `juu1rj`.
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/status_set.py, tests/test_orchestrator_readiness.py, tests/test_orchestrator_child_retired.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Spec: 25kzda
- Set: orchfix
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2pv5xd

## Workflow history
- 2026-10-07 to-review (aw set): authored review-ready at the maintainer's request 2026-10-07

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Retiring a child plan never strands its orchestrator: the orchestrator stays approvable and retirable, and its own history says which child was retired and when.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: readiness

- [ ] E-01 In `agent_workflows/orchestrator_readiness.review_readiness`, treat a child whose `- Status:` is `superseded` or `not-executed` AND which sits in the matching terminal directory (`run_selection_policy.is_in_terminal_directory`) as ready without linting, the same way the `executed` branch does. Derive the accepted set from `ipd_schema.TERMINAL` rather than spelling the three statuses again, so it cannot drift from the runner's retirement predicate. A retirement status OUTSIDE its terminal directory stays a finding.
  - Depends on: none
  - Expected outcome: an orchestrator whose children are one `reviewed` and one `not-executed` (in `not-executed/`) is ready; one with a `not-executed` status in `pending/` is not.
  - Execution state: pending

- [ ] E-02 When at least one child is accepted as retired, add an informational note (not a finding, so it never blocks) naming each retired child, so a human reading `aw ipd coverage` or a refusal sees why the Set is smaller than its table. Correct `REMEDY_CHILD_STATUS` so it no longer tells the reader to bring a terminal child to `to-review`: for a child in a terminal status it names `aw ipd set <status> <orchestrator> ...` review of the orchestrator's table instead.
  - Depends on: E-01
  - Expected outcome: the readiness result for the E-01 case carries the note; a remedy is never "bring to to-review" for a terminal child.
  - Execution state: pending

### Task group 2: retirement updates the orchestrator

- [ ] E-03 In `agent_workflows/status_set.py`, when a plan with `- Kind: child` is moved to `superseded` or `not-executed`, find its Set's orchestrator (`runner_shared.read_set_membership`), append `- <date> same-status (aw set): child <id6> retired <status>: <message>` to the orchestrator's `## Workflow history` through the same history-append path the setter already uses, stage both files together so a self-commit includes both, and print a one-line hint naming the orchestrator and saying its child table may need an edit. Do nothing when the Set has no orchestrator or the orchestrator is itself terminal.
  - Depends on: none
  - Expected outcome: retiring a child in a scratch repo leaves one new history line on its orchestrator, both files in one commit, and the hint on stdout; retiring a plan with no Set changes nothing else.
  - Execution state: pending

### Task group 3: spec and tests

- [ ] E-04 Amend spec `25kzda` Section 2.5d condition 2 to read that a child carrying `executed`, `superseded` or `not-executed` in its matching terminal directory is ready without being linted, and record it with `aw specs note`. The spec stays `approved`.
  - Depends on: E-01
  - Expected outcome: Section 2.5d names the three terminal statuses; `aw specs check` conforms.
  - Execution state: pending

- [ ] E-05 Add `tests/test_orchestrator_child_retired.py` and extend `tests/test_orchestrator_readiness.py` driving the real functions and `aw ipd set` in a scratch repo: retired child accepted; retired status in the wrong directory refused; the note and corrected remedy; retirement appends the orchestrator history line and commits both files; then `aw ipd set approved <orchestrator>` succeeds where it refused before. No source introspection.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: both modules pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- One predicate, several consumers: `review_readiness` feeds `aw ipd set`, `aw ipd lint` (`IPD-S408`), `aw check plans` and the runner (spec `25kzda` 2.5d CONSUMERS), so one fix covers all of them.
- Spec edits are declared in `- Scope-Paths:` (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Review readiness refuses a retired child and prints impossible advice. | Session 2026-10-07: `aw set approved ...` printed `child 62pkkg has status 'not-executed' (must be to-review, reviewed, approved, auto-approved, or executed)` with "Remedy: bring the child to `to-review`". `orchestrator_readiness._READY_CHILD_STATUSES = frozenset({"to-review", "reviewed", "approved", "auto-approved", "executed"})`. |
| F-02 | The runner already treats every terminal status as finishing a child. | `runner_shared` set-retirement predicate docstring: "Every child `Status:` that ENDS its participation in a Set ... DERIVED from `ipd_schema.TERMINAL`"; `RETIRED_PLAN_STATUSES = frozenset({"superseded", "not-executed"})`. |
| F-03 | Spec 2.5d condition 2 lists only `executed` as the terminal ready status. | Spec `25kzda` Section 2.5d, condition 2. |
| F-04 | Retiring a child writes nothing to its orchestrator. | `status_set.run_set_command` moves and edits only the matched records. |

## Proposed changes (ordered, validatable)

1. Accept retired children (E-01).
2. Note and corrected remedy (E-02).
3. Orchestrator history line on retirement (E-03).
4. Spec amendment (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- Rewriting the orchestrator's child table and checklist automatically. They are reviewed prose with reasons attached; a tool editing them would rewrite text a review signed off. The history line and hint make the edit visible; review owns it.
  - Carrier-Declined: no defect remains once a retired child no longer blocks readiness; the table edit is editorial.
- Refusal message styling and target-aware wording.
  - Carrier: juu1rj

## Scope check

- Over-scope: none. `orchestrator_readiness.py` E-01, E-02; `status_set.py` E-03; the spec E-04; tests E-05.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_orchestrator_readiness.py tests/test_orchestrator_child_retired.py tests/test_orchestrator_retirement.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

THIS PLAN AMENDS spec `25kzda` Section 2.5d condition 2, declared in `- Scope-Paths:`. Why: the condition contradicts the runner's own retirement predicate (F-02), and every consumer of `review_readiness` is reviewed against that text.

## Open questions

### OQ-01: Should a retired child also stop counting toward the orchestrator's coverage question?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: No change needed. Coverage asks whether the orchestrator carries work no child covers; a retired child covered nothing, so any work assigned only to it already reads as uncovered, which is the right answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session printing `review_readiness` for the accepted and the wrong-directory cases.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered note and a remedy for a terminal child.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the orchestrator's new history line, `git show --stat HEAD` with both files, and the hint line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the spec diff, the new workflow-history line and `aw specs check`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module runs with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
