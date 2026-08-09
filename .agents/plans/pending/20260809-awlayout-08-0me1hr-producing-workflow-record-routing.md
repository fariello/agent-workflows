# IPD: Producing workflow record routing

- Date: 2026-08-09
- Kind: child
- Concern: Route every generated plan, prompt, assessment, review, report, evidence file, and communication through the logical records root.
- Scope: record-producing packaged workflow bodies, one shared record-routing reference or helper, generated host shims, path-policy tests, and no unrelated workflow semantics.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 8
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: 0me1hr

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L8-01 [HIGH] (the forbidden-producer-path audit is a blunt `rg` matching ~48 legitimate references - inventory, specs validator, fixtures, scanner roots - and can never yield the orchestrator's 'zero-match' proof; redefine as an allowlist-backed, producer-WRITE-scoped test driven off the maintained producer inventory). L8-02 (name the resolver's DUAL consumption surface: CLI `aw path records` for workflow bodies + the Order 01 Python API for `agent_workflows` producers; carry the commit-policy value with the records root). L8-03 (add a negative test that no producer writes under the resolved `state` root - only `records`). L8-05 (concrete external-Git-absence proof: resolved external records root is outside the target work-tree; `git status` shows no external record).

## Goal

Remove hard-coded assumptions that generated artifacts live inside the target repository. Preserve established record categories while making path resolution, Git behavior, and user-visible locations backend-neutral.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Inventory and contract

- [ ] E-01 Build a checked inventory of every packaged workflow that creates, moves, archives, links, stages, or reports a generated artifact; classify each output as plan, prompt, assessment, review, report, evidence, communication, or AW state.
  - Depends on: none
  - Expected outcome: the implementation has an explicit producer-to-logical-path table and does not accidentally route AW state as records.
  - Execution state: pending
- [ ] E-02 Add one packaged record-routing reference or CLI helper that resolves canonical record categories through `aw path records`, defines backend-neutral relative paths, and explains target-Git behavior.
  - Depends on: E-01
  - Expected outcome: workflow authors use one concise path contract instead of repeating backend or `.agents/` assumptions.
  - Execution state: pending

### Task group 2: Producer conversion

- [ ] E-03 Convert planning, specification, prompt, communication, and research-like document producers to the shared routing contract; preserve naming, lifecycle, and cross-reference semantics.
  - Depends on: E-02
  - Expected outcome: document artifacts are created under the selected records backend and reported by resolved absolute or target-relative path as appropriate.
  - Execution state: pending
- [ ] E-04 Convert assessment, incident, migration, review, release, verification, and benchmark evidence producers; stage or commit records only when the repository backend and existing workflow contract both allow it.
  - Depends on: E-03
  - Expected outcome: external records are never offered to target Git, while repository records retain intentional Git behavior.
  - Execution state: pending
- [ ] E-05 Add inventory completeness, forbidden-literal, backend matrix, link rendering, package-data, shim-parity, and representative end-to-end workflow tests.
  - Depends on: E-04
  - Expected outcome: every producer is covered and no active workflow bypasses logical root resolution.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Workflow bodies under `.agents/workflows/` are packaged sources; host shims are derived artifacts.
- Existing artifact names and lifecycle rules carry compatibility value and should change only where path semantics require it.
- Markdown links between target files and external records may need absolute paths or explicit display labels.
- Git staging is an opt-in workflow action, not an automatic consequence of producing a record.

## Findings

| Artifact class | Logical owner | Must not be confused with |
|---|---|---|
| plans, specs, prompts, assessments, reviews | records | AW operational actions |
| run reports and verification evidence | records | install event history |
| workflow communication artifacts | records | registry metadata |
| setup actions and install facts | state | project records |

## Proposed changes (ordered, validatable)

1. Inventory all producers before editing.
2. Define one routing contract.
3. Convert document-oriented producers.
4. Convert run and evidence producers with Git gates.
5. Prove inventory coverage and backend parity.

## Deferred / out of scope (with reason)

- Moving preexisting artifacts is Order 09.
- Changing artifact taxonomies or workflow purposes is excluded; this plan changes location semantics only.
- General filesystem output not owned by an AW workflow is outside AW routing.

## Scope check

- Over-scope: no action-state routing, taxonomy redesign, legacy moves, or remote Git operations.
- Under-scope: all packaged producers, links, reported paths, Git behavior, shims, package data, and representative executions are covered.

## Required tests / validation

- `python3 -m unittest discover -s tests -p '*path*' -v`
- `python3 -m agent_workflows shim generate`
- `python3 -m agent_workflows parity`
- `rg -n '\.agents/(plans|prompts|assessments|reviews|reports|comms)' .agents/workflows agent_workflows tests`
- `python3 -m unittest discover -s tests -v`

## Spec / documentation sync

- Store the final producer inventory as a maintained test fixture or concise developer reference, not as an unaudited one-time note.
- Keep route categories aligned with the canonical 2026-08-09 layout specification.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: inventory review accounts for every filesystem-writing packaged workflow and distinguishes record output from state.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: reference or helper tests map every record category under all three backends with no physical-root literals in callers.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: representative document workflows produce equivalent names and lifecycle results in home, companion, and repository backends.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: evidence-producing workflow tests prove external files never enter target Git and repository records retain explicit staging behavior.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: forbidden-literal audit has only documented compatibility exceptions; parity, package-data, representative end-to-end, and full suites pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: all workflow producers must move together behind one route contract to avoid split artifact behavior.

STOP if Orders 01, 03, or 05 are incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
