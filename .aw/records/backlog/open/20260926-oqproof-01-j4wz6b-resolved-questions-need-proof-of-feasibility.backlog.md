- Id: j4wz6b
- Status: open
- Blocks-Release: next
- Set: oqproof
- Priority: medium
- Work-Kind: bug
- Summary: An agent can mark a plan's open question resolved with an answer nobody tested, so an approved plan can carry an unworkable instruction that only execution discovers

## Workflow history
- 2026-09-26 created (aw backlog): Filed from vtkfq8 triage 2026-09-26: OQ-03 was resolved at review with a mechanism that could not work; the run spent a turn discovering it.

OBSERVED. Plan vtkfq8 (carrierauth-01) was reviewed and approved with OQ-03 resolved as 'emit a commented / inert carrier placeholder that the gate does NOT read'. Review had MEASURED the obligation's cause (F-6, F-7) but never tried the chosen fix, and it cannot work: the obligation comes from the example question's '- Status: open' (check_engine._question_obligations), not from a missing carrier line, so no comment can suppress it. The executor discovered this in run run-20260926T051642Z-116672 (deferred question 06-vtkfq8-DQ1), stopped as the plan's own stop condition required, and the item ended fail-verify. The maintainer re-ruled OQ-03 on 2026-09-26 (commit 35d72343). The resolution also claimed 'Owner: maintainer' while being written by the reviewer: the reviewer, not the maintainer, chose the mechanism.

WHY IT IS A DEFECT (user-perceptible): one paid turn (13m, 762k tokens) plus a human round trip were spent learning something a 30-second experiment at review would have shown, and the plan read as 'approved, no open questions' to the operator deciding what to run unattended. The same shape recurs whenever a reviewer resolves a HOW question by describing a mechanism instead of demonstrating it.

PREVENTION TO DECIDE (candidate shapes, not decided here): (1) /plan-review 3.1: a question resolved by choosing a MECHANISM must cite a reproduction showing the mechanism works (the same standard F-rows already meet), else it stays open or becomes an explicit E-item spike with a stop condition; (2) the resolution must not claim 'Owner: maintainer' unless the maintainer actually answered, which is checkable against the workflow history and review Decisions table; (3) a plan whose resolution itself says 'confirm empirically ... if NO form works, stop' should be flagged by review as carrying a live feasibility risk, and surfaced as such in the readiness verdict rather than as resolved. Related: backlog lv92c6 (approved plan with a false premise).
