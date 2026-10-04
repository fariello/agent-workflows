# IPD: Let a production action resume an unfinished handoff instead of refusing it as a duplicate

- Date: 2026-10-04
- Kind: child
- Concern: After Orders 06 and 07, a graduation that exhausts its corrections leaves the backlog item `open`. The maintainer's direction (2026-10-04) is that a failed graduation is RESUMED, not restarted, and that its plans are kept. Today that is impossible in two ways. First, `production_checks.backlog_graduate_count` refuses when any active plan already carries the same `- From-Backlog:` (`duplicate_active = True` for a baseline plan not in a terminal directory), so re-running graduation on an item whose earlier plans exist fails with `BACKLOG-GRADUATE-COUNT` without doing anything; `spec_plan_count` has the same rule for `From-Spec`. Second, the production prompt (`build_backlog_production_prompt`) tells the agent to "Author one or more review-ready plans" with no mention of existing ones, so even if the count check passed the agent would write a second Set. Spec `25kzda` 3.3, 3.4, 4.8 and 4.9 as amended by Order 01 make continued output legitimate and redefine the count checks. This matters immediately: Order 09 reopens backlog items whose orchestrators already exist on `main`.
- Scope: IN: change `backlog_graduate_count` and `spec_plan_count` to accept existing active plans that carry the same source link as this action's continued output, refusing only a second Set (active plans for the same source spanning more than one `- Set:`) or a new plan linking a different source; give the production prompts a "continue this handoff" section, emitted only when such plans exist, listing each existing plan's path, status and the shared readiness check's findings, and instructing the agent to fix those plans rather than write a parallel Set; include existing plans in the Set-level verification (Order 06's verifier receives existing plus new paths). OUT: the readiness check (Order 03); the correction loop (Order 07); retiring or superseding existing plans (a human decision); recovering work left only in a preserved lane from an earlier run (the lane is already preserved and nameable by `aw runs`; integrating it is a separate operator action).
- Scope-Paths: agent_workflows/production_checks.py, agent_workflows/runner_shared.py, tests/test_production_resume_handoff.py
- Item-Dependencies: executed:nnsa2o
- Status: to-review
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 8
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 24qw39

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 08 of Set `gradcover`. Implements the "continued, not re-produced" rule of `25kzda` 3.3/3.4 and the amended `SPEC-PLAN-COUNT` / `BACKLOG-GRADUATE-COUNT` pass criteria from Order 01.

## Goal

Make re-running graduation on an `open` backlog item (or plan production on an `approved` spec) whose earlier plans exist continue and finish those plans, with the agent told exactly what is wrong with each, instead of refusing as a duplicate or writing a second Set.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: counting

- [ ] E-01 Change `backlog_graduate_count`: a baseline active plan carrying `- From-Backlog: <item>` is CONTINUED OUTPUT, not a duplicate. Fail only when (a) after the turn there is no active plan linking the item at all, (b) a new plan links a different item, or (c) the active plans linking the item carry more than one distinct `- Set:` value (two parallel Sets for one item). Make the message name which of the three applies and list the plans involved. Apply the same change to `spec_plan_count` with `- From-Spec:`. Expose a helper `existing_handoff_plans(repo, source_type, source_id6)` returning the active linked plans, used by E-02 and E-03.
  - Depends on: none
  - Expected outcome: an item with three existing linked plans in one Set and no new plan passes the count check; one where the turn wrote a second Set fails naming both Sets; one with zero linked plans after the turn fails as before.
  - Execution state: pending

### Task group 2: the prompt and the verifier

- [ ] E-02 In `build_backlog_production_prompt` and `build_spec_production_prompt`, when `existing_handoff_plans` is non-empty, add a section "Continue this handoff" listing each plan's repo-relative path, `- Status:`, and, for an orchestrator, the rendered findings of `orchestrator_readiness.review_readiness(..., ask=False)`, followed by the instruction: "These plans are the existing handoff for this item. Fix them in place; do not write a second Set. Add a child plan only for work no existing child performs, and add its row to the orchestrator's `## Child IPDs` table. Bring any `draft` plan to `to-review` with `aw ipd set to-review <id6>` once it is complete." With no existing plans the prompt is byte-identical to before.
  - Depends on: E-01
  - Expected outcome: the prompt for an item with existing plans lists them with statuses and findings; the prompt for a fresh item is unchanged byte for byte.
  - Execution state: pending

- [ ] E-03 In both production branches of `execute_item_core`, pass existing linked plans plus newly produced plans to the per-plan and Set-level verifiers, so a continued handoff is verified as a whole, and include the existing plan ids in the transition message (`graduated by run <id>: <ids>`).
  - Depends on: E-02
  - Expected outcome: a continued handoff whose existing orchestrator is fixed by the turn passes and the item reaches `graduated` with all plan ids named; one whose existing orchestrator is left unready fails `BACKLOG-GRADUATE-SET` naming it.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_production_resume_handoff.py`: unit cases for the three count outcomes for both source types; a prompt case asserting the continue section lists existing plans and findings and a byte-identity case for a fresh item; integration cases with the fake-host production fixtures where (i) the item has an existing orchestrator with a `draft` child and the scripted agent sets that child `to-review` (item ends `graduated`, no new Set written), (ii) the agent writes a parallel Set instead (fails `BACKLOG-GRADUATE-COUNT` naming two Sets), (iii) the spec twin of (i). Prove the tests can fail by restoring the old duplicate rule and pasting the failure of (i).
  - Depends on: E-03
  - Expected outcome: the new file passes; the mutation fails it; existing production tests pass, with any test that pinned the old duplicate refusal updated to the amended rule and named in the evidence.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `- Set:` IS THE GROUPING. Plans of one Set share `- Set: <setid>`; `read_set_membership` resolves a Set from disk.
- AN ACTIVE PLAN IS ONE NOT IN A TERMINAL DIRECTORY. `production_checks._TERMINAL_DISPOSITIONS` is `executed`, `superseded`, `not-executed`.
- A PROMPT CHANGE MUST NOT ALTER THE COMMON CASE. The precedent is `build_correction_notice` ("A FIRST ATTEMPT GETS NOTHING, so an ordinary prompt is byte-identical to before").
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The duplicate rule refuses any pre-existing active linked plan. In `backlog_graduate_count`, a baseline plan whose disposition is not terminal and whose `From-Backlog` equals the item sets `duplicate_active = True`, and `duplicate_active or count == 0 or has_unlinked_new_plan` returns the `BACKLOG-GRADUATE-COUNT` finding. | `backlog_graduate_count` body |
| F-02 | The prompt has no notion of existing plans. `build_backlog_production_prompt` emits a fixed "Production Contract" and "Prohibitions" list; it never reads the plans tree. | `build_backlog_production_prompt` body |
| F-03 | Order 09 will reopen backlog items whose orchestrators are on `main` (11 `graduated` items at authoring). Without this plan, graduating any of them again fails immediately with `BACKLOG-GRADUATE-COUNT`. | Order 09's scope; F-01 |
| F-04 | `25kzda` 3.4's "Forbidden unattended" cell for `graduated` forbids "Re-graduating it (producing duplicate IPDs for an item whose design is already handed off)". That remains true: this plan applies only to an `open` item; a `graduated` item is still skipped. | the quoted 3.4 cell |

## Proposed changes (ordered, validatable)

1. Redefine the two count checks around continued output and parallel Sets, with a shared helper (E-01).
2. Add the conditional "Continue this handoff" prompt section (E-02).
3. Verify existing plus new plans together (E-03).
4. Tests and mutation proof (E-04).

## Deferred / out of scope (with reason)

- INTEGRATING WORK LEFT IN A PRESERVED LANE BY AN EARLIER EXHAUSTED RUN. The lane is preserved and listed by `aw runs`; bringing it onto `main` is an operator decision with its own existing tooling.
  - Carrier-Declined: existing lane tooling covers it; no measured gap
- SUPERSEDING A WRONG EARLIER SET. A human decision (`AGENTS.md` retirement rule).
  - Carrier-Declined: reserved to the maintainer

## Scope check

- Over-scope: none. Two production modules and one test file.
- Under-scope: an existing test may pin the old duplicate refusal; if so it is updated under this plan's test scope and named in V-04, since the amended spec changes the expected outcome. That test file is then NOT in Scope-Paths and must be justified at finalize with `--scope-reason`.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_production_resume_handoff.py tests/test_production_set_check.py tests/test_production_correction_turn.py tests/test_backlog_production.py tests/test_spec_production.py -q` pasted.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements `25kzda` 3.3, 3.4, 4.8 `SPEC-PLAN-COUNT` and 4.9 `BACKLOG-GRADUATE-COUNT` as amended by Order 01. No spec edited here.

## Open questions

### OQ-01: Should a `graduated` item whose plans have fallen back also be resumable by graduation?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO, it must first be set back to `open`. `25kzda` 3.4 forbids re-graduating a `graduated` item unattended, and the explicit reopen records why. Order 10's `check.graduation-incomplete` reports such items and names `aw backlog set open <id6>` as the remedy; Order 09 performs the reopen for the existing cases.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of both count functions and the helper. Paste the unit outputs for continued output (pass), parallel Set (fail naming both Sets), no linked plan (fail), unlinked new plan (fail), for both source types.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a rendered prompt for an item with an existing orchestrator showing the section, the plan list with statuses and findings, and the instruction text; paste the byte-identity assertion passing for a fresh item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste integration case (i)'s final item status `graduated`, the transition message naming existing and new ids, and a count of Sets linked to the item (1); paste the failing variant naming the unready existing orchestrator.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new file passing with its count; any updated pre-existing test named with its before and after assertion; the mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths plus any justified test update.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
