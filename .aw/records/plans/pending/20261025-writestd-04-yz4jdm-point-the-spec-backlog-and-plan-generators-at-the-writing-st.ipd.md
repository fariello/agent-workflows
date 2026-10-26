# IPD: Point the spec, backlog, and plan generators at the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-06 requires the skeletons that `aw ipd scaffold`, `aw specs new`, and `aw backlog new` write to name the writing standard, because the skeleton is what an author reads while writing. Today none does: `ipd_authoring._SECTION_BODY`, `specs._render_new_spec`, and `backlog._render_item` contain no such line. `assess/templates/ipd.md` and `orchestrator-ipd.md` mirror the scaffold and must match it (`tests/test_ipd_schema.py` compares the child template with the schema).
- Scope: Add one permanent pointer line to each generator's output and to the two `assess` IPD templates. EXCLUDES runner prompts (Order 05) and workflow bodies (Order 06).
- Scope-Paths: agent_workflows/ipd_authoring.py, agent_workflows/specs.py, agent_workflows/backlog.py, .aw/system/workflows/assess/templates/ipd.md, .aw/system/workflows/assess/templates/orchestrator-ipd.md, tests/fixtures/, tests/test_generators_writing_standard_pointer.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: yz4jdm

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every newly created spec, backlog item, and plan tell its author where the writing standard is.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: generators

- [ ] E-01 In `ipd_authoring._SECTION_BODY[S.H_PROJECT_CONVENTIONS]`, append a bullet: "Write and proofread this plan per `.aw/system/workflows/standards/technical-artifact-writing.md`, including requirement 12 (diagrams)." Do not add it to `_AUTHORING_PLACEHOLDERS`, following the comment there about permanent guidance. Make the same addition to `assess/templates/ipd.md` and `assess/templates/orchestrator-ipd.md`. If a checked-in conforming fixture under `tests/fixtures/` is a scaffold output that a test compares byte for byte, regenerate it with `ipd_authoring.build_skeleton` as that fixture's comment says.
  - Depends on: none
  - Expected outcome: a scaffolded child and orchestrator plan contain the bullet and lint conforming.
  - Execution state: pending

- [ ] E-02 In `specs._render_new_spec`, add after the metadata block a line `> Write and proofread this spec per `.aw/system/workflows/standards/technical-artifact-writing.md`, including requirement 12 (diagrams).` Confirm `validate_spec` still passes on the output.
  - Depends on: none
  - Expected outcome: a new spec contains the line and `aw specs check` passes.
  - Execution state: pending

- [ ] E-03 In `backlog._render_item`, add the same pointer line after the `## Workflow history` block and before any body. Confirm `validate_item` passes.
  - Depends on: none
  - Expected outcome: a new backlog item contains the line and `aw backlog check` passes.
  - Execution state: pending

- [ ] E-04 Create `tests/test_generators_writing_standard_pointer.py` (marker `core`) that runs each of the three verbs with `--apply` in a temporary repository and asserts the written file names the standard's path and passes its own lint or check. Add a CHANGELOG entry.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the test passes.
  - Execution state: pending

- [ ] E-05 Run the routine gate and commit.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `_AUTHORING_PLACEHOLDERS` marks stub text; permanent guidance must not be listed there (comment at `ipd_authoring._SECTION_BODY`).
- `tests/test_ipd_schema.py` reads `assess/templates/ipd.md` as `CHILD_TEMPLATE`, so the template must keep the schema's heading order.

## Findings

- `specs._render_new_spec` writes metadata and history only, so the pointer is the first body line.

## Proposed changes (ordered, validatable)

1. Plan scaffold and templates (E-01).
2. Spec and backlog generators (E-02, E-03).
3. Test (E-04), gate and commit (E-05).

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_generators_writing_standard_pointer.py`, `tests/test_ipd_schema.py`, `tests/test_ipd_authoring.py`, the bare suite.

## Spec / documentation sync

No spec edit; spec `ecmw83` R-06 specifies this.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw ipd scaffold` preview output (no `--apply`) for a child and an orchestrator in a temporary repository, showing the bullet, and `aw ipd lint` on each written copy.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw specs new --title t` preview output in a temporary repository and `aw specs check` on the written file.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw backlog new` preview output in a temporary repository and `aw backlog check` on the written file.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_generators_writing_standard_pointer.py tests/test_ipd_schema.py tests/test_ipd_authoring.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit yz4jdm -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
