# IPD: Correct the stale runbook-directive premise in the _trailers_from_args docstring

- Date: 2026-09-26
- Kind: child
- Concern: The docstring of `work_cmd._trailers_from_args` explains why agent code commits carry no `AW-Run`/`AW-Item` trailers by saying the agent commits with raw `git commit -m msg -- <path>` "per the runbook directive". That directive was removed by plan y9vpvv (commitguard Order 02): every driver prompt now instructs `aw commit <plan> -- <paths>`. The conclusion (agent commits are untrailered) is still true; the stated cause is false, so a reader trying to close the gap is pointed at a directive that no longer exists.
- Scope: IN: the docstring of `agent_workflows/work_cmd._trailers_from_args` only. OUT: any behavior change, any new flag, wiring run/item ids into the agent's `aw commit` (that is the gap the docstring documents, and closing it is a separate design decision), the driver prompts.
- Scope-Paths: agent_workflows/work_cmd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: t5ycse
- Set: staledocs
- Order: 2
- Highest E allocated: 02
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: xts8ux

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog t5ycse: Rewrite the _trailers_from_args docstring to name the real gap (aw commit gets no run/item ids).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the `_trailers_from_args` docstring state the real remaining gap: the runner now instructs the agent to commit through `aw commit <plan> -- <paths>`, but supplies no run id or item id6 to that command, so the agent's code commits (the `base_head..HEAD` range `ipd_lifecycle` reads) still carry no `AW-Run`/`AW-Item` trailers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Rewrite the docstring paragraph

- [ ] E-01 In `agent_workflows/work_cmd._trailers_from_args`, rewrite the paragraph beginning "THE RUNNER WIRING IS NOW PARTLY LANDED" so that: the WIRED half is unchanged (driver-side `oc_runipd.commit_backlog_close` passes `run_item_trailers(run_id, plan_id6)`); the DEFERRED half says the agent's code commits are now instructed through `aw commit <plan> -- <paths>` (the four prompt sites: the execution-directive item 4 in `oc_runipd` and `agy_runipd` default runbook text, and the two "commit through `aw commit <plan> -- <paths>`" lines in `runner_shared`'s review/verify prompts), which reaches this function, but the runner passes no `run_id`/`item_id6` (nor `trailers`) to that invocation and `aw commit` has no public flag for them, so `_trailers_from_args` returns `[]` for every agent commit. Remove the sentence claiming the commits "pass through no `offer_commit` call, and so cannot be reached by wiring one" and the "raw `git commit -m msg -- <path>` per the runbook directive" clause. Keep the final paragraph about not auto-deriving the plan id6.
  - Depends on: none
  - Expected outcome: the docstring names `aw commit` as the instructed path and "no ids supplied" as the cause; `grep -n "runbook directive\|git commit -m msg" agent_workflows/work_cmd.py` returns nothing.
  - Execution state: pending

### Task group 2: Verify no behavior changed

- [ ] E-02 Run the bare suite `python3 -m pytest` and confirm `git diff --stat` touches only `agent_workflows/work_cmd.py` and that the diff is inside the docstring (no code line changed).
  - Depends on: E-01
  - Expected outcome: suite passes; diff is docstring-only.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Docstrings and code comments are internal artifacts: dashes are fine, no user-facing prose rule applies.
- Commits via `aw commit xts8ux -- agent_workflows/work_cmd.py`; never push.
- Suite is run bare: `python3 -m pytest` (AGENTS.md "HOW TO RUN THE SUITE").

## Findings

| # | Location (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | `work_cmd._trailers_from_args` (~:439-470), text "per the runbook directive, pass through no `offer_commit` call" | Stale premise, confirmed. The brief's line range ~:439-454 is right (the backlog item's :422-423 has drifted). |
| F-2 | `oc_runipd.py` "4. Commit only files you changed ... through `aw commit <plan> -- <paths>`" (~:1996), same text in `agy_runipd.py` (~:1958), `runner_shared.py` "commit through `aw commit <plan> -- <paths>`" (~:23845, ~:23938) | Confirmed. `grep -c "git commit -m msg"` is 0 in `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py`, `engine.py`. |
| F-3 | `work_cmd._trailers_from_args` body: `getattr(args, "run_id", None)`, `getattr(args, "item_id6", None)` | `aw commit` exposes no `--run-id`/`--item-id6` flag (only a programmatic namespace attribute), and no prompt passes one, so the gap is exactly "no ids supplied". Confirmed; the brief's claim holds. |

## Proposed changes (ordered, validatable)

1. E-01 rewrite the one docstring paragraph.
2. E-02 run the suite and confirm docstring-only diff.

## Deferred / out of scope (with reason)

- Supplying run/item ids to the agent's `aw commit` (env var, prompt-substituted flag, or other): a behavior and contract change with its own design questions (m73aet E-03 deliberately declined a public flag). Not this plan.
  - Carrier: a6xbso

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

No new test. The maintainer's standing rule is to test OUTCOMES only, and a docstring edit has no outcome to test; a test pinning docstring wording is exactly the source-text pin that rule forbids. Validation is the bare suite passing (proves nothing regressed) plus the grep and diff checks in V-01/V-02.

## Spec / documentation sync

N/A: internal docstring only; no spec or user-facing doc describes this function.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the rewritten paragraph (`sed -n` over the docstring) and the output of `grep -n "runbook directive\|git commit -m msg" agent_workflows/work_cmd.py` (expected: empty) and `grep -n "aw commit <plan>" agent_workflows/work_cmd.py` (expected: at least one hit inside `_trailers_from_args`).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (expected `N passed`, no failures) and `git diff --stat` showing only `agent_workflows/work_cmd.py`, plus `git diff -U0 agent_workflows/work_cmd.py` showing every changed line lies inside the docstring.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a docstring-only edit in one function; no behavior change.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/work_cmd.py`, docstring of `_trailers_from_args` only. Do not expand scope casually; if the work genuinely requires another file, make the edit and JUSTIFY it at finalize with `--scope-reason`. Genuine stop condition: an unresolvable concurrent edit to `work_cmd.py`.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for the suite; never claim a pass that was not run.

Commit ONLY `agent_workflows/work_cmd.py` through `aw commit xts8ux -- agent_workflows/work_cmd.py`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize xts8ux --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). Then set backlog `t5ycse` done citing the executed plan.
