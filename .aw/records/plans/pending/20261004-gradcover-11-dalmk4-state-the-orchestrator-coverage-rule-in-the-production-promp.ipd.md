# IPD: State the orchestrator coverage rule in the production prompts, the scaffold template and AGENTS.md

- Date: 2026-10-04
- Kind: child
- Concern: Authors are never told the rule the runner enforces. `runner_shared.build_backlog_production_prompt` and `build_spec_production_prompt` each list seven contract items (status `to-review`, provenance, gate inheritance, Scope-Paths, Item-Dependencies, lint, do not modify requirements) and say nothing about orchestrator plans, child plans, or work no child covers. The orchestrator skeleton written by `aw ipd scaffold --kind orchestrator` (`ipd_authoring._SECTION_BODY`) pre-fills `- TODO: whole-Set completion criteria.`, `- TODO: cross-IPD consistency / no-drift / dependency checks.` and `TODO: how the executed plan is verified.`; those are exactly three of the sections the probe reads, and the natural way to fill them is with whole-Set obligations that name no owner, which the probe's prompt calls uncovered work. The managed `AGENTS.md` block (source of truth in `engine.py`) instructs, under "Acting on a backlog item", "set the item to `graduated`" with no precondition, and its "ORCHESTRATOR COVERAGE GATE" paragraph says the gate runs "once per queued orchestrator", which Order 04 changes. `/plan-review` documents the `IPD-S407` row check but not review readiness. Telling authors the rule up front is what makes the gates added by Orders 05, 06 and 10 rarely fire.
- Scope: IN: add a "Orchestrator plans" section to both production prompts; change the three orchestrator skeleton placeholders to text that requires a named owner; amend the managed `AGENTS.md` block in `engine.py` (the "Acting on a backlog item" step (5) precondition, and the "ORCHESTRATOR COVERAGE GATE" paragraph's scope, quote and named-owner sentences) and regenerate this repository's `AGENTS.md` from it with the installer, not by hand; add a review-readiness subsection to `.aw/system/workflows/plan-review/plan-review.md` and the two `plan-review-long` step files that already carry the `IPD-S407` subsection. OUT: any gate or check (Orders 03 to 10); the skeleton's child-plan sections; any other managed-block paragraph.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_authoring.py, agent_workflows/engine.py, AGENTS.md, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/02-review-and-revise.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, tests/test_authoring_coverage_guidance.py
- Item-Dependencies: executed:26m1nb
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 11
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: dalmk4

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 11 of Set `gradcover`. Depends on Order 05 so the text it writes describes a gate that exists. The `AGENTS.md` wording below is the text to insert; the executor may make wording-level edits for line length but not change what it requires.

## Goal

Make every place an author or reviewer reads before writing an orchestrator plan state the same rule the gates enforce: each whole-Set obligation names, by id6, the child plan that performs it, and work no child performs gets a new child plan and a table row, never a parent step and never a deleted checklist.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the text authors read while writing

- [ ] E-01 Add to both `build_backlog_production_prompt` and `build_spec_production_prompt`, after the Production Contract list, a section "## Orchestrator plans (when you write a Set)" with these four items: (1) every item under `## Completion criteria`, `## Cross-IPD validation` and `## Required tests / validation` names, by id6, the child plan in this Set's `## Child IPDs` table that performs it; (2) work no existing child performs gets a NEW child plan and a table row, never a step on the orchestrator; (3) the orchestrator's checklist contains only `CONFIRM <child-id6> REACHED <status>` rows, and you never delete it; (4) before you finish, run `aw ipd coverage <orchestrator-id6>` and fix every quoted finding it prints. Keep the section out of a prompt for a single-plan handoff only if the prompt cannot know in advance; since it cannot, always include it.
  - Depends on: none
  - Expected outcome: both rendered prompts contain the section with all four items and the literal `aw ipd coverage` command.
  - Execution state: pending

- [ ] E-02 Change the orchestrator skeleton placeholders in `ipd_authoring._SECTION_BODY`: `H_COMPLETION` to `- TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.`; `H_CROSS_IPD` to `- TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.`; and, for the orchestrator kind only, `H_REQUIRED_TESTS` to `TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.` Keep each placeholder detectable as a stub by `authoring_placeholders_resolved` (the `TODO:` prefix), and leave the child kind's `H_REQUIRED_TESTS` text unchanged.
  - Depends on: E-01
  - Expected outcome: `aw ipd scaffold --kind orchestrator` (dry run) shows the three new placeholders; `--kind child` shows the old `Required tests` placeholder; a freshly scaffolded orchestrator is still reported as a stub.
  - Execution state: pending

### Task group 2: the text agents read before acting

- [ ] E-03 Amend the managed block in `engine.py`. In "Acting on a backlog item", replace step (5) "set the item to `graduated`, NOT `done`, because ..." with "set the item to `graduated`, NOT `done`, and only once every plan you wrote is `to-review` or later, lints, and, for an orchestrator, passes `aw ipd coverage <id6>`: `aw backlog set graduated` refuses otherwise. `graduated` means the design is handed off while `done` means the code is written and validated." In the "THE ORCHESTRATOR COVERAGE GATE" paragraph, replace "before any agent turn, lane worktree or session, a run asks a MODEL once per queued orchestrator" with "before any agent turn, lane worktree or session, a run that may RETIRE an orchestrator asks a MODEL once per orchestrator it could retire, and asks again immediately before retiring it"; add after the "WHEN IT FIRES" sentence: "The refusal QUOTES each uncovered passage. Work the orchestrator assigns by id6 to a child in its own `## Child IPDs` table is covered and is not reported. The same check also gates `aw ipd set to-review|reviewed|approved` on an orchestrator and a graduation's handoff, so fix the quoted passage before setting the status, not after the run refuses." Then regenerate `AGENTS.md` in this repository with the installer's refresh path (`python3 -m agent_workflows install . --yes` or the documented refresh command), never by hand.
  - Depends on: E-02
  - Expected outcome: the managed block in the regenerated `AGENTS.md` contains the new step (5) precondition, the "may RETIRE" scope, the quote sentence, and the named-child sentence; nothing outside the managed block changed.
  - Execution state: pending

- [ ] E-04 Add to `/plan-review` (`.aw/system/workflows/plan-review/plan-review.md`, beside "Orchestrator checklist row check and bounded repair loop (`IPD-S407`)") and to the two `plan-review-long` files that carry the same subsection, a subsection "Orchestrator review readiness (`IPD-S408`)" telling the reviewer to run `aw ipd coverage <id6>` on an orchestrator under review and resolve each quoted finding by assigning it by id6 to a child in the table or by adding a child plan and its row (never by deleting the checklist), recording each attempt in the review round as the `IPD-S407` loop does, and leaving the plan `to-review` with `- Readiness:` absent if unresolved. Leave the installed command shims under `.opencode/commands/` and `.claude/commands/` alone: they only point at these files.
  - Depends on: E-03
  - Expected outcome: all three workflow files contain the subsection with the `aw ipd coverage` command and the never-delete rule.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_authoring_coverage_guidance.py` asserting OUTCOMES: the rendered backlog and spec production prompts (built by calling the two functions on fixture inputs) contain the four rule items and `aw ipd coverage`; `aw ipd scaffold --kind orchestrator` run as a subprocess emits the three new placeholders and `--kind child` does not emit the orchestrator `Required tests` text; a scaffolded orchestrator is still a stub under `authoring_placeholders_resolved`; and a fresh `aw install` into a temp repository writes an `AGENTS.md` whose managed block contains the new step (5) precondition. These assert generated output, never production source text. Prove the tests can fail by reverting E-01 and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation fails it; `tests/test_installer.py` and existing scaffold tests still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE MANAGED BLOCK'S SOURCE OF TRUTH IS `engine.py`. `CONTRIBUTING.md` states the execution contract "lives in the managed `AGENT-WORKFLOWS` block in `AGENTS.md`. That block is the canonical home"; the block text itself is generated from `engine.py` and installed into every managed repository. Edit `engine.py`, then regenerate.
- `AGENTS.md` IS AI-FACING, so the no-dash rule for user-facing prose does not apply (execution contract in `AGENTS.md`).
- A SKELETON PLACEHOLDER MUST STAY DETECTABLE. `ipd_authoring._AUTHORING_PLACEHOLDERS` and `authoring_placeholders_resolved` decide whether a draft is still a stub; the comment above `H_PROJECT_CONVENTIONS` warns that permanent guidance must not be listed there.
- TESTS ASSERT GENERATED OUTPUT, never production source or docstrings (`GUIDING_PRINCIPLES.md` P16; "NEVER assert that specific text ... remain unchanged in a script"). Asserting a rendered prompt's content is an output assertion.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The production prompts omit the rule. Their Production Contract has seven numbered items, none mentioning orchestrators or coverage. | `build_backlog_production_prompt` and `build_spec_production_prompt` bodies |
| F-02 | The skeleton invites unowned obligations. A 2026-10-03 dry run of `aw ipd scaffold --kind orchestrator` printed `- TODO: whole-Set completion criteria.`, `- TODO: cross-IPD consistency / no-drift / dependency checks.` and `TODO: how the executed plan is verified.` under the three probed sections. | the dry-run output; `ipd_authoring._SECTION_BODY` |
| F-03 | The managed block's step (5) has no precondition and its gate paragraph describes the pre-Order-04 scope. | the "Acting on a backlog item" and "THE ORCHESTRATOR COVERAGE GATE" text in `engine.py`'s managed block and in the installed `AGENTS.md` |
| F-04 | `/plan-review` covers `IPD-S407` only. Its "Orchestrator checklist row check and bounded repair loop (`IPD-S407`)" subsection has no coverage or readiness step; the two `plan-review-long` step files mirror it. | the three workflow files |

## Proposed changes (ordered, validatable)

1. Production prompt section (E-01).
2. Orchestrator skeleton placeholders (E-02).
3. Managed `AGENTS.md` block and regeneration (E-03).
4. `/plan-review` subsection (E-04).
5. Output tests and a mutation proof (E-05).

## Deferred / out of scope (with reason)

- `docs/authoring.md` and `docs/orchestration.md`. Neither describes the coverage gate today (`docs/orchestration.md` has no `coverage` or `probe` match), so no sentence becomes false; adding user-facing documentation of the new gates is release-notes work.
  - Carrier-Declined: measured; no false sentence in user docs; covered by release notes at release-review
- THE `C-*` / `Owner:` FORMAT. E-02's `Owner: <child-id6>` placeholder is guidance text, not a parsed field.
  - Carrier-Declined: maintainer sequencing 2026-10-04

## Scope check

- Over-scope: none. Each path is one place an author or reviewer reads, plus one test file.
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_authoring_coverage_guidance.py tests/test_installer.py tests/test_scaffold_history_clock.py tests/test_backlog_production.py tests/test_spec_production.py -q` pasted.
- Mutation run pasted.
- `git diff AGENTS.md` pasted, showing changes only inside the managed block.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec edited. Documentation edited: `AGENTS.md` (managed block, regenerated from `engine.py`) and the three `/plan-review` workflow files, so the instructions match the gates specified in `25kzda` 2.5b/2.5d and `77tr3o` R-13 as amended by Order 01.

## Open questions

### OQ-01: Should the production prompt include the orchestrator section only when the agent writes an orchestrator?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: always include it. The prompt is written before the agent decides whether to split the work into a Set, so it cannot know; the section costs a few lines and is ignored for a single-plan handoff.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of both prompt builders and one rendered prompt from each showing the section with its four items.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `_SECTION_BODY` and dry-run scaffold output for both kinds, plus `authoring_placeholders_resolved` returning False on the new orchestrator skeleton.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `engine.py` diff, the regeneration command and its output, and `git diff AGENTS.md` confined to the managed block and containing the four required sentences.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diff of the three workflow files, each showing the new subsection with `aw ipd coverage` and the never-delete rule.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new file passing with its count; the mutation failing and the revert passing; a grep of the test file for reads of `agent_workflows/*.py`, `inspect` and `ast.parse` returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Regenerate `AGENTS.md` with the installer; never hand-edit the managed block. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
