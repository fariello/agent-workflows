# IPD: Align spec ecmw83 with the shipped AGENTS.md writing-standard paragraph and dash ruling

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-05 requires a managed `AGENTS.md` paragraph pointing to the writing standard, and a dash rule widened to specs, backlog items, and plans in the execution contract, `GUIDING_PRINCIPLES.md` P13, `CONTRIBUTING.md`, `GEMINI.md`, `prose-style.md`, and `intent-audit.md`. Maintainer commit `0cbfcc706` already shipped the paragraph (`### Technical writing standard` in `engine.agents_pointer_prose`, regenerated into `AGENTS.md`, tested by `tests/test_technical_writing_delivery.py`) and deliberately kept the existing dash split. The maintainer confirmed that ruling on 2026-11-05 (plan `g4719s` OQ-02: keep the shipped file and its dash ruling, amend the spec, reconsider Orders 02 and 03). So the original E-items are either done or contradict that ruling. What remains is that spec `ecmw83` R-05, AC-03, N1, and N2 still describe the superseded design.
- Scope: Amend spec `ecmw83` R-05, AC-03, N1, and N2 to describe the shipped paragraph, the kept dash split, and the shipped standard's scope; confirm the shipped state with the existing delivery test and the block regeneration check. EXCLUDES any change to `engine.py`, `AGENTS.md`, P13, `CONTRIBUTING.md`, `GEMINI.md`, `prose-style.md`, `intent-audit.md`, or DECISIONS (the shipped text already matches the ruling), the spec rows that Order 01 `g4719s` amends (R-01, R-02, MD-2, AC-01, AC-02), and R-07 (Order 03).
- Scope-Paths: .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md
- Item-Dependencies: executed:g4719s
- Status: reviewed
- Readiness: go-pending-approval
- Review-Depth: simple
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 2
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: gzhw9c

## Workflow history
- 2026-11-06 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed
- 2026-11-05 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; re-scoped to a spec amendment after the g4719s OQ-02 ruling; PR-001..PR-005 FIXED; review record .aw/records/reviews/20261025-writestd-02-gzhw9c-add-the-writing-standard-paragraph-to-the-agents-md-managed.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make spec `ecmw83` describe the managed `AGENTS.md` writing-standard paragraph and the dash rule as they shipped in commit `0cbfcc706` and as the maintainer confirmed on 2026-11-05, so later Orders are reviewed against a contract the code satisfies.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: spec amendment

- [ ] E-01 (spec `ecmw83` R-05) Amend `.aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md`. Make these edits and no others. (1) R-05: replace the requirement text with "The `AGENTS.md` managed block (`engine.agents_pointer_prose`) must contain a `### Technical writing standard` paragraph that tells the agent to read and follow the standard at the path in R-01 before it creates, revises, reviews, or proofreads technical text, to check the complete text against every numbered requirement, and to report the standard as missing rather than claim compliance. The execution contract's dash clause, `GUIDING_PRINCIPLES.md` P13, `CONTRIBUTING.md`, `prose-style.md`, `verify-execution/intent-audit.md`, and `GEMINI.md` keep the existing split: no em or en dashes in user-facing prose; internal artifacts, including specs, plans, and backlog items, are exempt (MD-2 as superseded)." and change its Section column to "3 MD-2 (superseded)". (2) AC-03: replace the criterion with "`python3 -m tools.regen_agents_block --check` reports no drift, and `tests/test_technical_writing_delivery.py` passes: the installed `AGENTS.md` names the standard's path for both install layouts." (3) N1: append "The shipped standard itself also covers user-facing documentation (commit `0cbfcc706`); this non-goal limits only this spec's sweep (R-08) and advisory (R-07)." (4) N2: append the same sentence. Then run `aw specs note .aw/records/specs/to-review/20261025-writestd-01-ecmw83-writing-standard.spec.md --message "R-05, AC-03, N1, N2 aligned with the shipped AGENTS.md paragraph and kept dash split (plan gzhw9c; maintainer ruling g4719s OQ-02)"`. Do not change the spec's `- Status:`.
  - Depends on: none
  - Expected outcome: R-05 and AC-03 describe the shipped state with no widened dash clause; N1 and N2 carry the scope sentence; the spec has one new history line and the same status.
  - Execution state: pending

### Task group 2: confirm and commit

- [ ] E-02 Confirm the shipped state the amended spec now describes: run `python3 -m tools.regen_agents_block --check` and `python3 -m pytest -o addopts="" -v tests/test_technical_writing_delivery.py`, then the bare routine gate `python3 -m pytest`, `aw specs check`, and commit the spec.
  - Depends on: E-01
  - Expected outcome: no block drift, the delivery tests pass, the routine gate passes, `aw specs check` reports no error for `ecmw83`, and the commit holds only the spec file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `engine.agents_pointer_prose` is the single source of the managed pointer prose; this repository's block is regenerated with `python3 -m tools.regen_agents_block`, which reported "Up to date" at review.
- A plan may amend a spec and must list it in `- Scope-Paths:` (`AGENTS.md`, "A PLAN MAY AMEND A SPEC").
- Order 01 `g4719s` E-01 edits the same spec file (R-01, R-02, MD-2, AC-01, AC-02); this plan's `executed:g4719s` edge serializes the two.

## Findings

- `engine.agents_pointer_prose` already renders `### Technical writing standard` with the read-and-follow, check-every-requirement, preserve, report-ambiguity, and report-missing clauses (`agent_workflows/engine.py` "### Technical writing standard"); `AGENTS.md` carries it; `tests/test_technical_writing_delivery.py` asserts it for both layouts and in an installed repository (2 passed at review).
- The shipped standard says "This standard adds no dash rule of its own" and defers to the execution contract. The maintainer kept that ruling (`g4719s` OQ-02, 2026-11-05). Widening the dash clause and P13, `CONTRIBUTING.md`, `GEMINI.md`, `prose-style.md`, and `intent-audit.md` (the original E-02, E-05, E-06) and recording a DECISIONS entry for it (the original E-07) would reverse that ruling, so they are removed.
- Spec `ecmw83` N1 and N2 exclude user-facing prose and other record types, but the shipped standard covers both. They stay true as limits on this spec's sweep and advisory, so E-01 qualifies them rather than deleting them.

## Proposed changes (ordered, validatable)

1. Amend spec `ecmw83` R-05, AC-03, N1, N2 (E-01).
2. Confirm the shipped state and commit (E-02).

## Deferred / out of scope (with reason)

- The orchestrator `8fvkmp` child-table row for Order 02 and its AC-03 completion criterion still describe the widened dash rule. They belong to the orchestrator and are fixed in its own re-review.
  - Carrier: 8fvkmp
- Sweep Orders 07 to 09 (`sfez3e`, `uog8nc`, `381ml6`) and the dash advisory Order 03 (`k2x0yl`) rest on the widened dash rule; their own re-reviews decide their scope under the kept ruling.
  - Carrier: 8fvkmp

## Scope check

- Over-scope: none.
- Under-scope: none. The managed paragraph and its install test already exist.

## Required tests / validation

`python3 -m tools.regen_agents_block --check`, `tests/test_technical_writing_delivery.py` (spec `ecmw83` AC-03), `aw specs check`, and the routine gate (V-02).

## Spec / documentation sync

This plan amends spec `ecmw83` (E-01), listed in `- Scope-Paths:`. Why: the maintainer ruled on 2026-11-05 (`g4719s` OQ-02) that the standard and its dash ruling stand as shipped by `0cbfcc706`, so R-05 and AC-03 must stop requiring a widened dash clause, and N1 and N2 must stop implying the standard excludes documentation. No user-facing documentation changes, so no CHANGELOG entry.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: (spec `ecmw83` AC-03) paste `git diff` of the spec showing only the four edits and one history line, and `grep -n -- '- Status:'` on the spec showing it unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-03) paste the `regen_agents_block --check` output, the `tests/test_technical_writing_delivery.py` run with every test PASSED, the summary line of bare `python3 -m pytest`, the `aw specs check` result for `ecmw83`, and the `aw commit` output listing the committed path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after Order 01 `g4719s` is `executed` (its edge enforces this; both plans edit spec `ecmw83`). Before editing the spec, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; a needed file outside it is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit gzhw9c -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize gzhw9c` itself.
