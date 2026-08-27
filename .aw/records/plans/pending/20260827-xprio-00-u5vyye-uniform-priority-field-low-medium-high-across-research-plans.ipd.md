# IPD: Uniform Priority field (low/medium/high) across research, plans, and specs

- Date: 2026-08-27
- Kind: orchestrator
- Concern: Only backlog carries a `- Priority:` field today (`PRIORITIES = {high,medium,low}`, `_PRIORITY_RE`, backlog.py:53/60); research, plans/IPDs, and specs have none, so they cannot be prioritized on the attention board. Graduated from backlog `p9o1oo` (Set `xtypepriority`); rationale there. Decision: a UNIFORM 3-level scale `low | medium | high` across research/plans/specs, matching backlog exactly (reliably distinguishable; the 'urgent' case is covered orthogonally by `Blocks-Release`, so no 4th tier). Child Set minted with FRESH setid `xprio` (NOT the source's `xtypepriority`) per graduation policy (spec 4w7d6s); link: child `From-Backlog: p9o1oo`, source `Graduated-To: xprio`.
- Scope: Add a recognized-but-optional `Priority` field (reusing backlog's `{high,medium,low}` vocab + `_PRIORITY_RE`) to plans/IPDs, specs, and research, plus their setters and validation, and populate `Item.priority` in each type's attention record builder so the board sorts/labels them (attention.py already HAS `Item.priority` at :45 and renders it for backlog; the per-type builders `_plans_record`:317, `_spec_record`:289, `_research_record`:371 just need to read + pass it). Three per-type children (each = contract/schema recognition + setter + check + attention wiring for one type): 01 plans/IPDs, 02 specs, 03 research. Recognized-but-OPTIONAL everywhere (like Scope-Paths/Blocks-Release/Summary) so existing artifacts are not mass-failed; ABSENT = unprioritized (do not force a default). Reuse ONE shared vocab (`PRIORITIES`) - do not fork three copies.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/cli.py, agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/backlog.py, tests/
- Status: draft
- Set: xprio
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: u5vyye

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Give research, plans/IPDs, and specs a uniform recognized-but-optional `Priority` (low/medium/high, matching backlog) with setters, validation, and attention-board rendering, so every prioritizable artifact type sorts/labels on the board. Graduated from backlog p9o1oo.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the per-type work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [ ] E-01 After children 01-03 execute, confirm all three types accept an optional `Priority` (low/medium/high) via one shared vocab, absent = unprioritized (no mass-fail), each type's setter writes+validates it, `aw check` flags an invalid value, and `aw attention` sorts/labels all four types (backlog+plans+specs+research) by priority. Full suite green.
  - Depends on: none
  - Expected outcome: uniform Priority across the four types on the board; one shared PRIORITIES vocab; suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | 1b45el | Priority on IPD schema + `aw ipd set`/`scaffold` + `_plans_record` attention | none |
| 02 | rp859c | Priority on spec contract + `aw specs set` + `_spec_record` attention | none |
| 03 | 6vgd0k | Priority on research frontmatter + `aw research new`/`set` + `_research_record` attention | none |

Children are INDEPENDENT (different contracts/setters) and may execute in any order; each reuses the ONE shared `backlog.PRIORITIES` vocab (do not fork). Orchestrator verifies. (Source link: `From-Backlog: p9o1oo`; source `Graduated-To: xprio`.)

## Completion criteria (the whole Set is done only when)

- plans/IPDs, specs, and research each recognize an optional `Priority` (shared low/medium/high vocab), with setter + `aw check` enum validation, and each populates `Item.priority` in its attention record builder.
- Absent Priority = unprioritized everywhere (no forced default; no mass-fail of existing artifacts).
- `aw attention` sorts/labels backlog + plans + specs + research by priority uniformly.
- Full suite green.

## Cross-IPD validation

- ONE shared `PRIORITIES` vocab consumed by all types (grep: no forked copies).
- `Item.priority` populated by every per-type record builder; the board renders all four types identically.
- Recognized-but-optional posture consistent with Scope-Paths/Blocks-Release/Summary (no mass-fail).

## Deferred / out of scope (with reason)

- A 4th 'urgent' tier: excluded (Blocks-Release covers it; 3 levels are reliably distinguishable).
- The uniform Summary field (ud28vy) and Item-Dependencies (ipddeps): separate, same recognized-but-optional pattern.

## Scope check

- Over-scope: none.
- Under-scope: none (all three type contracts + setters + checks + attention covered).

## Required tests / validation

Aggregate of children: each type accepts/writes/validates Priority; invalid value flagged by `aw check`; absent = unprioritized (no failure); `aw attention` sorts/labels each type by priority; shared-vocab (single definition) assertion.

## Open questions

### OQ-01: Should an absent Priority render as unprioritized or as an implicit 'medium' on the board?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Default to UNPRIORITIZED (do not fabricate a value; backlog already treats absent as unset). If the board needs a sort position for unprioritized items, sort them after explicit priorities. Decide rendering detail at implementation.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
