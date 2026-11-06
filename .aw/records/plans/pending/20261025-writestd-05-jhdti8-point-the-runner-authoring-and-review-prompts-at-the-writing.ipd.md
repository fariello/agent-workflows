# IPD: Point the runner authoring and review prompts at the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-06 requires the runner's authoring and review prompts to direct the agent to the writing standard. Maintainer commit `0cbfcc706` shipped the standard at `.aw/system/workflows/technical-writing/technical-writing.md` (layout-relative: `.agents/workflows/technical-writing/technical-writing.md` in the legacy layout). The two authoring builders, `runner_shared.build_spec_production_prompt` (two branches: approved spec and implementing spec) and `runner_shared.build_backlog_production_prompt`, write and revise plans in unattended runs and do not mention the standard. Review turns already reach it through the workflow bodies: `runner_shared.build_review_prompt` returns a bare `/plan-review` or `/spec-review` command by design, and the steps-mode review (`review_sequence.render_prompt`) lists the `plan-review/steps/` files, which Order 06 (`e4n4p3`) points at the standard.
- Scope: Add one requirement line, naming the layout-resolved path of the shipped standard, to the "## Production Contract" list of all three authoring prompt variants, and test it. EXCLUDES `build_review_prompt` and `review_sequence.render_prompt` (the review prompts reach the standard through the workflow bodies and step files Order 06 edits), the correction prompts `build_production_set_correction_prompt` and `build_review_orchestrator_correction_prompt` (they resume a session that already received the authoring or review prompt), and the execution prompt `build_prompt`, which executes plans rather than writes them.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_production_prompt_writing_standard.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s
- Status: to-review
- Readiness: go-pending-approval
- Review-Depth: standard
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
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; re-scoped to the standard shipped by 0cbfcc706 (g4719s OQ-02 answer); PR-001..PR-008 FIXED; review record .aw/records/reviews/20261025-writestd-05-jhdti8-point-the-runner-authoring-and-review-prompts-at-the-writing.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make unattended plan authoring follow the shipped writing standard, including its diagram requirement, as interactive authoring already does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: prompts

- [ ] E-01 (spec `ecmw83` R-06) In `agent_workflows/runner_shared.py`, add one private helper beside `_ORCHESTRATOR_PLANS_SECTION`, `_writing_standard_contract_line(root: Path, number: int) -> str`. It imports `engine` function-locally (`from agent_workflows import engine`, the module's convention), computes the standard's path as `engine.resolve_workflows_dir(engine.resolve_target_layout(root)) + "/technical-writing/technical-writing.md"`, and returns exactly: `f"{number}. Write and proofread every plan you author or revise per `{path}`, including requirement 12 (diagrams). If that file is absent, report the missing dependency and do not claim compliance."`. Append its result as the LAST numbered item of the "## Production Contract" list in each of the three variants, using the builder's existing `root`: item 9 in both branches of `build_spec_production_prompt` (after item 8, "Mandatory uncited requirement..."), and item 8 in `build_backlog_production_prompt` (after item 7). Do not renumber existing items: "## Continue this handoff" cites items 1 and 2 by number.
  - Depends on: none
  - Expected outcome: each of the three prompt variants carries the line as the last "## Production Contract" item, with the same wording apart from the item number, and the path follows the target repository's layout.
  - Execution state: pending

- [ ] E-02 (spec `ecmw83` R-06) Create `tests/test_production_prompt_writing_standard.py` with `pytestmark = pytest.mark.core`. In a temporary directory, write a minimal spec at `.aw/records/specs/approved/` carrying `- Id:` and `- Status: approved`, the same spec under `.aw/records/specs/implementing/` with `- Status: implementing`, and a minimal backlog item (the fixture shape of `tests/test_authoring_coverage_guidance.py::ProductionPromptCoverageGuidanceTests`). Call the three builder variants and assert, for each: the line containing `technical-writing/technical-writing.md` lies between "## Production Contract" and the next "## " heading; it names `.aw/system/workflows/technical-writing/technical-writing.md` when the repository has a `.aw/system/` directory; and it names `.agents/workflows/technical-writing/technical-writing.md` when the repository has only `.agents/workflows/`. Assert the three lines are identical once the leading item number is removed. Also assert that the non-isolated `build_review_prompt` output for an IPD item is still the single line `/plan-review <relative path>`, which shows the review command stayed prose-free. Add one line under the topmost pending heading of `CHANGELOG.md` (`## 2.0.0 (pending)` at review; re-read at execution), next to the existing "technical writing standard" entry: unattended plan authoring by `aw oc run` and `aw agy run` now directs the agent to the writing standard. Use no em or en dash (CHANGELOG is user-facing).
  - Depends on: E-01
  - Expected outcome: the test passes, and it fails when the E-01 line is removed from any one variant.
  - Execution state: pending

- [ ] E-03 Run the new test with `tests/test_authoring_coverage_guidance.py`, `tests/test_production_resume_handoff.py`, and `tests/test_spec_production.py` (the existing prompt-builder tests), then the bare routine gate `python3 -m pytest`, then commit through `aw commit jhdti8 -- <paths>`.
  - Depends on: E-01, E-02
  - Expected outcome: every listed test and the bare suite pass, and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared` is shared by both hosts (`oc_runipd`, `agy_runipd`), so one edit covers both. Both call sites of each builder (the shared-checkout path and the lane path in `runner_shared`) go through the same function.
- Function-local imports in `runner_shared` avoid import cycles (the `build_review_prompt` docstring). `engine` does not import `runner_shared` at module level (its only reference is function-local), so a function-local `engine` import in the helper is cycle-free.
- The layout is resolved per target repository: `engine.resolve_target_layout` returns `aw` when `.aw/system/` exists and `legacy` when only `.agents/workflows/` exists, and `engine.resolve_workflows_dir` maps that to the bundle root. A review-time probe printed `.aw/system/workflows/technical-writing/technical-writing.md` for an `aw` tree and an empty tree, and `.agents/workflows/technical-writing/technical-writing.md` for a legacy tree.
- Tests exercise behavior (GUIDING_PRINCIPLES P16): E-02 calls the builders and asserts on the rendered prompts, as `tests/test_authoring_coverage_guidance.py` already does for the orchestrator rules.

## Findings

- Authoring builders: `build_spec_production_prompt` (headings `# Plan production from approved spec` and `# Plan production from implementing spec`, selected by the spec's `- Status:` read through `status_set.read_artifact_record`) and `build_backlog_production_prompt` (heading `# Plan production from open backlog item`). A `def build_.*prompt` search in `runner_shared` finds no other authoring builder, so the "plan production prompt" named in spec `ecmw83` Section 4 ("Runner prompt" row) is one of these two.
- The spec-approved "## Production Contract" list ends at item 8 and the backlog list at item 7. `_append_continue_handoff_section` writes "Production Contract items 1 and 2 apply to NEW plans only.", so appending keeps every existing number valid.
- In a "## Continue this handoff" turn the agent edits existing plans, so the line says "author or revise".
- Review: `build_review_prompt` returns `/<handler> <path>` and must stay prose-free on the command line (its docstring). The steps-mode review renders `review_sequence.render_prompt`, which lists `review_sequence.KERNEL_STEP_FILE` and the `review_sequence.CHECK_STEP_FILES` entries; Order 06 (`e4n4p3` E-04) adds the standard to `_kernel.md` and `p-proofread.md`.
- Correction prompts (`build_production_set_correction_prompt`, `build_review_orchestrator_correction_prompt`) are sent by resuming the authoring or review session, so the agent already holds the instruction.

## Proposed changes (ordered, validatable)

1. Add the helper and the contract line (E-01).
2. Test and changelog (E-02); run the gate and commit (E-03).

## Deferred / out of scope (with reason)

- Review prompts: they stay a bare slash command (or a step-file list) by design; the workflow bodies and step files carry the instruction (Order 06).
  - Carrier: e4n4p3

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_production_prompt_writing_standard.py` (new), the existing prompt-builder tests `tests/test_authoring_coverage_guidance.py`, `tests/test_production_resume_handoff.py`, and `tests/test_spec_production.py`, and the bare suite.

## Spec / documentation sync

No spec edit. Spec `ecmw83` R-06 requires the runner's authoring and review prompts to direct the agent to the standard; this plan covers the authoring prompts, and the review prompts reach the standard through the workflow bodies Order 06 edits (Decision D-2 in the review record). `docs/technical-artifact-writing.md` lists the workflows that repeat the instruction and stays accurate; the CHANGELOG line (E-02) records the runner change.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff agent_workflows/runner_shared.py` showing the helper and its three call sites, and the contract line printed from each of the three variants by calling the builders (for example a short `python3 -c` script over a temporary repository), showing items 9, 9, and 8 with the `.aw/system/workflows/technical-writing/technical-writing.md` path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_production_prompt_writing_standard.py` with every test PASSED; then the same run after temporarily removing the E-01 line from `build_backlog_production_prompt`, showing FAILED, and the restored PASSED run; and `git diff CHANGELOG.md` showing one added line under the pending heading.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the summary line of `python3 -m pytest -o addopts="" tests/test_production_prompt_writing_standard.py tests/test_authoring_coverage_guidance.py tests/test_production_resume_handoff.py tests/test_spec_production.py`, the summary line of bare `python3 -m pytest`, and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved (it is `to-review` at review time; the orchestrator `8fvkmp` gate carries the same condition), and only after Order 01 `g4719s` is `executed` (its edge enforces this; it adds requirement 12, which the prompt line names). Every open question is resolved. Before editing, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit jhdti8 -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize jhdti8` itself.
