# IPD: plans scaffold, directives, and decision updates (Set `plans-adopter`, Order 7)

- Date: 2026-08-08
- Kind: child
- Concern: wire the plans convention into the framework: installer scaffold for the terminal-dir shard parents, a thin AGENTS.md pointer note for the `aw plans` grouping/manifest verbs, a DECISIONS pointer entry, and a TODO future-work note naming `prompts/` as the next adopter.
- Scope: scaffold + directives + prior-decision edits, consuming Orders 01/03/05. No new tool behavior. Requires Orders 01, 03, 05 executed; if their symbols/paths are absent, STOP.
- Status: approved
- Set: plans-adopter
- Order: 7
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-08-08 human maintainer (via opencode its_direct/pt3-claude-opus-4.8-1m-us): "Approved all. Please read and execute the orchestrator."

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the framework wiring + the recorded decision. Authored from spec `20260808-0004-01` Section 4, 6.
- 2026-08-08 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; verified the RESEARCH_SHARD_SUBDIRS precedent, the created-count (24 -> 27 with 3 terminal-dir shards), and the installer auto-commit behavior; no defects found.
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

Make the plans convention ship and be discoverable at near-zero permanent token cost, and record the decision. Scaffold the terminal-dir shard parents via the installer; add a SHORT AGENTS.md pointer section for the `aw plans index`/`find`/`set-assign`/`mv`/`archive` verbs ("browse/regroup plans by Set; do not hand-name or hand-maintain the plans index"); add a DECISIONS pointer entry to the plans-adopter spec; add a TODO future-work note naming `prompts/` the subsequent adopter. Spec Sections 4, 6.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: scaffold and pointer

- [ ] E-01 confirm Orders 01, 03, 05 are executed and their SYMBOLS/verbs are present (`artifact_core`, `aw plans index`, `aw plans archive`), else STOP. Do NOT require populated weekly shard dirs to exist (they are created on demand by `aw plans archive`).
  - Depends on: none
  - Expected outcome: the Order 01/03/05 symbols/verbs are importable/invokable; if absent the child halts.
  - Execution state: pending
- [ ] E-02 extend the installer scaffold: add the weekly-shard PARENT layout for the terminal disposition dirs (`executed/`, `superseded/`, `not-executed/`) so the layout is discoverable in a fresh repo; extend BOTH the real and dry-run branches of `create_setup_artifacts`; update the created-count assertion in `tests/test_setup_artifacts.py` and assert real-vs-dry-run parity for the new artifacts.
  - Depends on: E-01
  - Expected outcome: the terminal-dir shard scaffolding is created (no-clobber); dry-run matches real; idempotent; the created-count assertion is updated.
  - Execution state: pending
- [ ] E-03 add the thin AGENTS.md pointer: a SHORT new `###` section in `agents_pointer_prose` naming the `aw plans` grouping/manifest verbs ("browse/regroup plans by Set with `aw plans`; do not hand-name or hand-maintain the plans index"); regenerate AGENTS.md; the AGENT-PLANS sibling untouched (byte-identical).
  - Depends on: E-01
  - Expected outcome: `aw install .` yields an AGENTS.md diff limited to the new pointer section; AGENT-PLANS is byte-identical.
  - Execution state: pending

### Task group 2: prior-decision edits and tests

- [ ] E-04 add a DECISIONS pointer entry (pin the number at execution; next is D124) referencing the plans-adopter spec `20260808-0004-01`; note it applies the D123 model to plans via the shared core + the stable `Id` + Set-clustering, and cites D122 (the ipd_schema it extends).
  - Depends on: E-01
  - Expected outcome: the entry is present, points to the spec, and cites D123 (the model) and D122 (ipd_schema).
  - Execution state: pending
- [ ] E-05 update the TODO future-work note: mark `plans/` DONE (this Set) and name `prompts/` the subsequent adopter (weakest case; low volume; research-prompt lineage already handled), with `comms/`/`walkthroughs/` after.
  - Depends on: E-01
  - Expected outcome: the TODO note reflects plans done + prompts next.
  - Execution state: pending
- [ ] E-06 add scaffold tests (terminal-dir shard parents created; dry-run; idempotent; created-count updated; real/dry-run parity) in the existing scaffold harness; run them plus the full suite and paste output; confirm the AGENTS.md regen diff is limited to the new pointer section.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green; the AGENTS.md regen is limited to the pointer section.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Scaffold precedent: `create_setup_artifacts`/`ensure_docs_readmes` in `engine.py` and the `RESEARCH_SHARD_SUBDIRS` pattern (from research-org Order 07) are the model for adding the terminal-dir shard parents; extend BOTH branches and update the created-count assertion (there is a hard-won parity test).
- The always-loaded block is `agents_pointer_prose()` (engine.py), regenerated into AGENTS.md via the sectioned path; a refresh MUST limit the diff to the new pointer section and not disturb the `AGENT-PLANS` sibling (byte-identical).
- DECISIONS entries are short dated pointers to specs (D112/D122/D123 style); keep depth in the spec.
- The installer auto-commits AGENTS.md + the managed-sections manifest on a non-dry-run install; expect a `sync via installer` commit alongside the source edit (a known behavior).
- Test runner: stdlib `unittest`, NOT pytest.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C7-1 | HIGH | Low | weak-agent | discovery | The `aw plans` verbs help only if agents know to use them; discoverable at near-zero always-loaded token cost. | spec 4.4 |
| C7-2 | MEDIUM | Low | provenance | record | The plans-adopter decision must be recorded (DECISIONS pointer) so it is not lost. | spec 6 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.6 | Installer scaffold: terminal-dir shard parents (real+dry-run), count assertion + parity | `agent_workflows/engine.py`, `tests/test_setup_artifacts.py` | Low | E-02 |
| 2 | 4.4 | Thin AGENTS.md pointer section for `aw plans` verbs; regenerate (diff limited to the section) | `agent_workflows/engine.py`, `AGENTS.md` | Low | E-03 |
| 3 | 6 | DECISIONS pointer entry (D124) citing the spec + D123 + D122 | `DECISIONS.md` | Low | E-04 |
| 4 | 6 | TODO note: plans done, prompts next | `TODO.md` | Low | E-05 |
| 5 | 4 | scaffold tests | `tests/test_setup_artifacts.py` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Implementing the convention for prompts/comms/walkthroughs | scope | Named future adopters; plans-first by value. | The TODO note; a later Set |
| A pre-commit hook for `aw plans index --check` | scope | Hook-less per spec OQ4; the workflows carry the obligation. | Deferred hook follow-up |

## Scope check

- Over-scope: none - scaffold + one pointer section + DECISIONS/TODO edits.
- Under-scope: MUST make the plans convention scaffolded, discoverable (thin pointer), and record the decision so nothing contradicts the shipped convention.

## Required tests / validation

Extend `tests/test_setup_artifacts.py` (terminal-dir shard parents; dry-run; idempotent; created-count updated; real/dry-run parity). Confirm the AGENTS.md regen diff is limited to the new pointer section and AGENT-PLANS is byte-identical. Run `python3 -m unittest discover -s tests -t .`; PASTE (the `Ran N tests ... OK` summary). Leak-clean; no em/en dashes.

## Spec / documentation sync

`DECISIONS.md` (D124 pointer), `TODO.md` (plans done, prompts next), `.agents/plans/README.md` (the shard layout + `aw plans` verbs, if not already added by Orders 03/05), `AGENTS.md` (regenerated pointer). The spec itself is unchanged (this executes it).

## Open questions

### OQ-01: exact wording of the AGENTS.md plans pointer

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: a SHORT new `###` section (a few sentences, consistent with the existing pointer sections) naming the `aw plans` verbs and "browse/regroup plans by Set; do not hand-name or hand-maintain the plans index"; detail stays in `aw plans --help` + `.agents/plans/README.md` (progressive disclosure). The empty-diff-except-this-section invariant is what the validation enforces.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01/03/05 in `executed/` and confirm their symbols/verbs are importable/invokable (not that populated shard dirs exist).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the scaffold test output (terminal-dir shard parents created no-clobber; dry-run matches real; idempotent); confirm the created-count assertion was updated and real-vs-dry-run parity holds.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff -- AGENTS.md` showing the diff limited to the new pointer section; confirm AGENT-PLANS is byte-identical.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm the DECISIONS entry (D124) exists, points to the plans-adopter spec, and cites D123 + D122.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm the TODO note marks plans done and names prompts the next adopter.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the full-suite `Ran N tests ... OK` summary; confirm leak-clean and no em/en dashes; confirm the AGENTS.md regen diff is limited to the pointer section.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 03, 05. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including the limited AGENTS.md diff and byte-identical AGENT-PLANS); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds scope (scaffold/pointer/DECISIONS/TODO only; edit only the existing `agents_pointer_prose`; regenerate AGENTS.md, do not hand-edit). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
