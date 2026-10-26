# IPD: Add the writing-standard paragraph to the AGENTS.md managed block and widen the dash scope

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-05 requires every agent in every managed repository to be told, in its always-loaded instructions, to read the writing standard before writing or reviewing a spec, backlog item, or plan. It also requires the dash rule (MD-2) to cover those three artifact types. Today the managed `AGENTS.md` block (`engine.agents_pointer_prose`) has no such paragraph, and its execution contract, `GUIDING_PRINCIPLES.md` P13, `CONTRIBUTING.md`, `GEMINI.md`, `assess/references/prose-style.md`, and `verify-execution/intent-audit.md` all exempt specs and plans from the dash rule.
- Scope: Add a `### Technical artifact writing` paragraph to `engine.agents_pointer_prose`; widen the dash clause of its `### Agent execution contract` paragraph; regenerate this repository's `AGENTS.md` block; restate the same scope in P13, `CONTRIBUTING.md`, `GEMINI.md`, `prose-style.md`, and `intent-audit.md`; record the change as a DECISIONS entry. EXCLUDES any lint behavior (Order 03) and workflow-body references (Order 06).
- Scope-Paths: agent_workflows/engine.py, AGENTS.md, .aw/system/managed-sections.json, GUIDING_PRINCIPLES.md, CONTRIBUTING.md, GEMINI.md, .aw/system/workflows/assess/references/prose-style.md, .aw/system/workflows/verify-execution/intent-audit.md, DECISIONS.md, tests/test_agents_writing_standard_pointer.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: gzhw9c

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every agent's always-loaded instructions name the writing standard and apply the dash rule to specs, backlog items, and plans.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: managed block

- [ ] E-01 In `engine.agents_pointer_prose`, add a paragraph `### Technical artifact writing` immediately before `### Ask self-contained questions`. Its text is the draft's "Required agent instruction" with the path `.aw/system/workflows/standards/technical-artifact-writing.md`: before creating, revising, reviewing, or proofreading any backlog item, specification, implementation plan, or plan Set, read and follow the standard; check the complete artifact against every numbered requirement before delivery, including requirement 12 on diagrams; correct writing defects only within the authorized scope; preserve obligations, identifiers, quotations, evidence, and lifecycle authority; report unresolved ambiguity that affects meaning; if the standard cannot be read, report the missing dependency and do not claim compliance.
  - Depends on: none
  - Expected outcome: the paragraph is in the rendered block for both layouts (`aw` and `legacy`).
  - Execution state: pending

- [ ] E-02 In the `### Agent execution contract` paragraph of `engine.agents_pointer_prose`, replace the dash clause with: write no em or en dashes in user-facing prose you author (READMEs, CHANGELOG, docs meant for end users) or in specs, backlog items, and plans (the writing standard, requirement 11); other internal artifacts (research findings, prompts, walkthroughs, commit messages, code comments) remain exempt, and you should spend no effort avoiding dashes there.
  - Depends on: E-01
  - Expected outcome: the clause names specs, backlog items, and plans as covered.
  - Execution state: pending

- [ ] E-03 Run `python3 -m tools.regen_agents_block` to rewrite this repository's `AGENTS.md` managed block and section hashes, then `python3 -m tools.regen_agents_block --check`.
  - Depends on: E-02
  - Expected outcome: `AGENTS.md` carries both changes and the check reports no drift.
  - Execution state: pending

- [ ] E-04 Create `tests/test_agents_writing_standard_pointer.py` (marker `core`). It installs the toolkit into a temporary git repository and asserts that the installed `AGENTS.md` contains `### Technical artifact writing` and the path of the standard, and that the path it names exists in that repository.
  - Depends on: E-03
  - Expected outcome: the test passes.
  - Execution state: pending

### Task group 2: restated policy

- [ ] E-05 Rewrite `GUIDING_PRINCIPLES.md` P13 so it states: the no em or en dash rule applies to user-facing text and to specs, backlog items, and plans (spec `ecmw83` MD-2); other internal artifacts remain exempt; deterministic tooling reports dashes in specs, backlog items, and plans only as `info` advisories. Keep its clarity paragraph. Make the matching edit to `CONTRIBUTING.md` "Authoring conventions" and the dash bullet of `GEMINI.md`.
  - Depends on: none
  - Expected outcome: all three files state the same scope.
  - Execution state: pending

- [ ] E-06 In `assess/references/prose-style.md`, change the section "USER-FACING versus INTERNAL" and "No em dashes" so specs, backlog items, and plans are covered and the other internal artifacts stay exempt; name the writing standard as the authority for those three types. In `verify-execution/intent-audit.md`, change the bullet beginning `the no-em/en-dash rule is applied only to user-facing prose` to the same scope.
  - Depends on: none
  - Expected outcome: both shipped files state the same scope as P13.
  - Execution state: pending

- [ ] E-07 Add the next free DECISIONS entry (after D177 at authoring time; use the next number at execution) titled "The dash rule covers specs, backlog items, and plans". Record the maintainer ruling of 2026-10-25, the reason (the shipped writing standard, spec `ecmw83`), and that the IPD dash code `IPD-D701` stays retired while Order 03 adds an `info` advisory under a new code. Add a CHANGELOG entry.
  - Depends on: E-05
  - Expected outcome: the entry exists and cites `ecmw83`.
  - Execution state: pending

- [ ] E-08 Run the routine gate and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the bare suite passes and the commit holds only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `engine.agents_pointer_prose` is the single source of the managed pointer prose; `agents_managed_sections` wraps it as the `aw:pointer` section.
- In this repository the block is regenerated with `python3 -m tools.regen_agents_block`; `tests/test_agents_section_records.py` fails if it is stale.
- `GEMINI.md` is hand-written and not managed (the explore map, `update_agents_pointer`), so it is edited directly.

## Findings

- Dash exemption sites: `engine.agents_pointer_prose` execution contract (substring `it does NOT apply to internal or AI-facing artifacts`), P13, `CONTRIBUTING.md` (substring `Do not use em or en dashes in USER-FACING prose`), `GEMINI.md`, `prose-style.md` (heading `USER-FACING versus INTERNAL`), `intent-audit.md`.
- No test pins the exemption wording (a search of `tests/` for `spend no effort avoiding` returns nothing).

## Proposed changes (ordered, validatable)

1. Managed block paragraph and contract clause (E-01, E-02).
2. Regenerate and test (E-03, E-04).
3. Restate policy in the five other sites and record the decision (E-05 to E-07).
4. Gate and commit (E-08).

## Deferred / out of scope (with reason)

- `AGENTS.md` text below `<!-- /aw:block -->` is repo-local and unchanged.
  - Carrier-Declined: no obligation; the repo-local sections contain no dash rule.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_agents_writing_standard_pointer.py`, `tests/test_agents_section_records.py` (through the routine gate), and the bare suite.

## Spec / documentation sync

No spec edit. `GUIDING_PRINCIPLES.md` and DECISIONS change as recorded above.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -c "from agent_workflows import engine; t=engine.agents_pointer_prose('aw'); i=t.index('### Technical artifact writing'); print(t[i:i+900])"`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered clause from the same `python3 -c` approach, located by the substring `write no em or en dashes`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `--check` output and `git diff --stat AGENTS.md .aw/system/managed-sections.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_agents_writing_standard_pointer.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff GUIDING_PRINCIPLES.md CONTRIBUTING.md GEMINI.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff .aw/system/workflows/assess/references/prose-style.md .aw/system/workflows/verify-execution/intent-audit.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the new DECISIONS entry and `git diff --stat CHANGELOG.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the summary line of bare `python3 -m pytest` and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit gzhw9c -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
