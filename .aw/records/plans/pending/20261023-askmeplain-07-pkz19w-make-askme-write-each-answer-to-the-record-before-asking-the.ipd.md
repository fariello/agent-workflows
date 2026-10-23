# IPD: Make askme write each answer to the record before asking the next question

- Date: 2026-10-23
- Kind: child
- Concern: Live trial T12 on Claude Code + Sonnet 5 (plan `lkn1zt`, findings `auwidn`, D-9, counted from the T05 run with maintainer approval) asked three open questions one at a time but held all three answers in the conversation and wrote them together only after the third ("All three open questions on plan `m4rcyy` are now answered. Recording the decisions in the plan now."). If the session had been interrupted after the second answer, both earlier decisions would have been lost. The workflow already says "Record the answer before asking the next question." (`askme.md` "Record project decisions"), but the line sits at the END of the recording bullets, far from "Ask and wait" where the next question is composed. The same host recorded each answer first in T06, and the other three combinations did so in every multi-question row (tool sequences `question, edit, question, edit, ...` in OpenCode + gem T04, Antigravity T04), so the behavior is inconsistent rather than absent.
- Scope: IN: in `askme.md` `## Ask and wait`, add an explicit ordering step: after a definite answer, write it to the record (per "Record project decisions") and only then compose or ask the next question; batching answers to write at the end is not allowed; in `## Finish`, say the final report summarizes records already written, not a write step. Mirror the reasoning in `rationale.md`; add a behavioral installer-output test. OUT: other `lkn1zt` defects (plans `9vttho`, `lf4j52`, `wfy9ii`, `l5f2hg`).
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery.py, CHANGELOG.md
- Item-Dependencies: executed:lkn1zt
- Status: to-review
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: askmeplain
- Order: 7
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: pkz19w

## Workflow history
- 2026-10-23 to-review (aw set): authored review-ready from lkn1zt findings auwidn (D-9)

- 2026-10-23 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every host persist each answer to its record before asking the next question, so an interrupted session never loses a decision the user already made.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [ ] E-01 In `.aw/system/workflows/askme/askme.md` `## Ask and wait`, add a short paragraph: when the user gives a definite answer, write it to the record now (as "Record project decisions" describes) before you compose or ask the next question; do not keep answers in the conversation to write later. In `## Finish`, change "After the answers are recorded, report the decisions" so it is clear the records were already written one at a time and the report only summarizes them. Mirror the reasoning in `.aw/system/workflows/askme/rationale.md` in one paragraph citing `lkn1zt` `auwidn` Claude Code T12.
  - Depends on: none
  - Expected outcome: the ordering paragraph, the Finish wording, and the rationale paragraph are present; the existing "Record the answer before asking the next question." bullet stays.
  - Execution state: pending
- [ ] E-02 Add a behavioral test to `tests/test_askme_command_delivery.py` that installs into a temporary repo (`tests.support.init_repo`) and asserts the INSTALLED `askme.md` contains the E-01 ordering paragraph's operative phrase in `## Ask and wait`. Add one CHANGELOG bullet under the topmost pending heading (plain language, no em or en dashes).
  - Depends on: E-01
  - Expected outcome: the test passes against the edited body and fails against the pre-change body; CHANGELOG bullet present.
  - Execution state: pending
- [ ] E-03 Run the bare suite `python3 -m pytest` and the new test by path.
  - Depends on: E-02
  - Expected outcome: both pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The workflow body `.aw/system/workflows/askme/askme.md` is referenced by every host shim (`engine.shim_body`).
- Delivery tests: `tests/test_askme_command_delivery.py`; assertions on installed output only.
- Every live bug gates the next release, hence `- Blocks-Release: next`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Answers batched until the end | `auwidn` Claude Code T12 (via T05): "Recording the decisions in the plan now." after the third answer |
| F-2 | Same host recorded per answer in another session | `auwidn` Claude Code T06 |
| F-3 | Other hosts record per answer | `auwidn` OpenCode + gem T12, Antigravity T12 tool sequences |
| F-4 | The rule exists, positioned away from the asking step | `askme.md` "Record project decisions": "Record the answer before asking the next question." |

## Proposed changes (ordered, validatable)

E-01 to E-03, each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Live re-run of T12 on Claude Code: maintainer-attended act.
  - Carrier-Declined: re-verification reuses `lkn1zt`'s method at the maintainer's discretion.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

The installer-output test (E-02) and the bare `python3 -m pytest` (E-03), outputs pasted.

## Spec / documentation sync

N/A for specs. `rationale.md` in E-01; `CHANGELOG.md` in E-02.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/askme.md .aw/system/workflows/askme/rationale.md` hunks for the ordering paragraph, the Finish wording and the rationale paragraph.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` output with the new test passing (and failing against the pre-change body), plus the CHANGELOG diff.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted final summary line of the bare `python3 -m pytest` run showing no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit pkz19w -- <paths>`; never push or tag. Finalize with `aw ipd finalize pkz19w --actor <agent/model> --message <summary> --apply` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
