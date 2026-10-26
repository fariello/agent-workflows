# IPD: Point the runner authoring and review prompts at the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-06 requires the runner's authoring prompts to direct the agent to the writing standard. `runner_shared.build_spec_production_prompt` (both branches: from an approved spec and from an implementing spec) and `runner_shared.build_backlog_production_prompt` write plans in unattended runs and say nothing about it. Review turns are a bare slash command (`runner_shared.build_review_prompt` docstring: deliberately prose-free on the command line), so the reviewer reaches the standard through the workflow body, which Order 06 changes.
- Scope: Add one requirement line to each production prompt and test it. EXCLUDES `build_review_prompt` (deliberately prose-free) and execution prompts (`build_prompt`), which execute plans rather than write them.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_production_prompt_writing_standard.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 5
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jhdti8

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make unattended plan authoring follow the writing standard, as interactive authoring does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: prompts

- [ ] E-01 In `runner_shared.build_spec_production_prompt` (both branches) and `runner_shared.build_backlog_production_prompt`, add to the contract section one line: "Write and proofread every plan you author per `.aw/system/workflows/standards/technical-artifact-writing.md`, including requirement 12 (diagrams). If that file is absent, report the missing dependency and do not claim compliance." Use the same wording in all three places.
  - Depends on: none
  - Expected outcome: all three prompts contain the line.
  - Execution state: pending

- [ ] E-02 Create `tests/test_production_prompt_writing_standard.py` (marker `core`) that calls the three builders with minimal fixture items in a temporary repository and asserts each returned prompt contains the standard's path, and that `build_review_prompt` output is unchanged by this plan (compare with its output for the same input at the baseline commit recorded before E-01). Add a CHANGELOG entry.
  - Depends on: E-01
  - Expected outcome: the test passes.
  - Execution state: pending

- [ ] E-03 Run the routine gate and commit.
  - Depends on: E-01, E-02
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared` is shared by both hosts (`oc_runipd`, `agy_runipd`), so one edit covers both.
- Function-local imports in `runner_shared` avoid import cycles; this plan adds none.

## Findings

- Builders: `build_spec_production_prompt` (headings `# Plan production from implementing spec` and `# Plan production from approved spec`) and `build_backlog_production_prompt` (heading `# Plan production from open backlog item`).

## Proposed changes (ordered, validatable)

1. Add the line (E-01).
2. Test (E-02), gate and commit (E-03).

## Deferred / out of scope (with reason)

- Review prompt: stays a bare slash command by design; the workflow body carries the instruction (Order 06).
  - Carrier: e4n4p3

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_production_prompt_writing_standard.py` and the bare suite.

## Spec / documentation sync

No spec edit.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the E-02 test run.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_production_prompt_writing_standard.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit jhdti8 -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
