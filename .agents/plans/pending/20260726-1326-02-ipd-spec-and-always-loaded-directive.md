# IPD: canonical IPD spec doc + a concise always-loaded directive requiring it

- Date: 2026-07-26
- Concern: execution completeness / instruction reliability - weaker/faster models follow an explicit MUST + a concrete file path better than scattered soft guidance; a single canonical IPD spec plus a short always-loaded pointer makes the IPD conventions (including the Part 1 checklist + completion clause) rigorously followable
- Scope: add a canonical `ipd-spec.md` under `.agents/docs/specs/` consolidating the IPD authoring/execution conventions, and add ONE concise directive to the agent-workflows-managed AGENTS.md block (via `agents_pointer_prose`) pointing agents at it and requiring the completion rule. Product-code touch is limited to the engine prose template string + regenerated AGENTS.md. DEPENDS ON Part 1 (Order 1) of this Set.
- Status: to-review
- Set: ipd-completeness-guardrails
- Order: 2
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-26 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from the same `gits.opencode` inbox FYI as Part 1, treated as untrusted/advisory and verified against our own files. Part 2 of the `ipd-completeness-guardrails` Set: it consolidates the IPD conventions into a canonical `ipd-spec.md` and adds a concise always-loaded directive requiring it (the reporter found weaker models respond better to a strong MUST + a concrete path). Split from Part 1 because it adds always-loaded token cost and edits the managed AGENTS.md block, which overlaps the TODO.md `aw:block` edit-protection item.

## Goal

Give agents ONE canonical, referenceable IPD spec (`.agents/docs/specs/ipd-spec.md`) that consolidates the IPD authoring + execution conventions (the template structure, the Part 1 `## Detailed Implementation Checklist (TODO)`, the completion clause, the chunk-into-a-Set guidance, and the existing lifecycle/status/commit rules), and a SHORT always-loaded directive in the managed AGENTS.md block that points at it and states the completion rule as an explicit MUST. Keep the always-loaded addition to one or two lines (the block stays lean, D99/D100); the full detail lives in the spec (P8, referenced-not-restated).

Why it matters: the reporter observed that weaker/faster executing models (Gemini Flash) follow an explicit MUST + a concrete file path far more reliably than soft, scattered guidance. A canonical spec makes the conventions authoritative and testable; a concise always-loaded pointer makes an agent aware of it every session without inlining the whole thing.

## Project conventions discovered (Step 0)

- The always-loaded managed block is sourced from `agents_pointer_prose()` in `agent_workflows/engine.py` (the single prose SOURCE post-D104; `agents_pointer_block()` is the legacy wrapper) and regenerated into `AGENTS.md` via the sectioned `merge_aw_block`/`agents_managed_block` path (D104). A reinstall/refresh must be an EMPTY DIFF on AGENTS.md (idempotence invariant).
- The block is deliberately LEAN (D99/D100): it points at things (P8), it does not inline principle/workflow/spec bodies. Adding always-loaded tokens is a real cost, so the directive must be one or two lines.
- Specs live under `.agents/docs/specs/` (e.g. the agent-comms convention, the clean-delta spec) named `YYYYMMDD-HHMM-NN-<slug>.md`; no `ipd-spec.md` exists yet.
- This overlaps the TODO.md item "do not hand-edit inside aw:block": both edit the managed block; coordinate the wording so the block does not grow more than necessary.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| J1 | MEDIUM | Low | executing agent (weaker/faster tier) | instruction reliability | IPD conventions are spread across the template, AGENTS.md plans block, the plans README, and DECISIONS; a weaker model has no single authoritative MUST-follow document, so it follows conventions inconsistently. | template `assess/templates/ipd.md`; `AGENTS.md` AGENT-PLANS block; `.agents/plans/README.md` |
| J2 | MEDIUM | Medium | maintainer | always-loaded cost / managed block | The strongest lever the reporter found is a concise always-loaded MUST + a concrete path, but the always-loaded block is deliberately lean and is the managed `aw:block` (regenerated from `agents_pointer_prose`); the directive must be short, go through the engine template (not a direct AGENTS.md edit), and keep the reinstall empty-diff invariant. | `engine.py` `agents_pointer_prose`; D104 sectioned block; D99/D100 lean-block precedent |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | J1 | Write `.agents/docs/specs/YYYYMMDD-HHMM-NN-ipd-spec.md` (canonical IPD spec): consolidate the IPD template structure, the Part-1 `## Detailed Implementation Checklist (TODO)` + completion clause, the chunk-into-a-Set guidance, and the existing status vocabulary / lifecycle / path-scoped-commit / never-push / paste-actual-output rules, by REFERENCE to their authoritative homes (template, AGENTS.md plans block, plans README, DECISIONS), not by duplicating them. It is the single "how to author + execute an IPD" entry point. | a new spec doc under `.agents/docs/specs/` | Low | spec exists, consolidates by reference (no divergent restatement), covers checklist + completion + chunking + lifecycle/commit rules; no em/en dashes |
| 2 | J2 | Add ONE concise directive to `agents_pointer_prose()` (the always-loaded managed-block source, NOT the legacy `agents_pointer_block()` wrapper): a short line stating that when authoring or executing an IPD you MUST follow `.agents/docs/specs/<ipd-spec>.md`, including its mandatory checklist and the completion rule (do not claim done or move a plan to `executed/` until every checklist item is checked AND verified). Then regenerate `AGENTS.md` via the sectioned path to an empty diff. Keep it to one or two lines; the detail lives in the spec (P8). | `agent_workflows/engine.py`, `AGENTS.md` | Medium | the directive is added to `agents_pointer_prose` (not the legacy wrapper); AGENTS.md regenerated to an empty diff (idempotent); one/two lines only; the `AGENT-PLANS` sibling block untouched |
| 3 | J1,J2 | Tests + docs: confirm the full suite stays green and that AGENTS.md matches the regenerated template (a reinstall is an empty diff), consistent with the D104 mechanism; DECISIONS entry (pin at execution) for the canonical spec + the always-loaded directive (extends the Part-1 decision); CHANGELOG. Cross-reference Part 1, the archived `gits` FYI, and the TODO.md `aw:block` item. | `tests/` (existing AGENTS/idempotence coverage), `DECISIONS.md`, `CHANGELOG.md` | Medium | full suite green (paste actual output); AGENTS.md empty-diff on reinstall; DECISIONS/CHANGELOG present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| A separate GEMINI.md-specific directive distinct from the AGENTS.md one | Low | scope | The managed block already mirrors into CLAUDE.md/GEMINI.md when present (D104); one directive in the shared block reaches Gemini via the mirror. A Gemini-only variant is only warranted if evidence shows the shared directive is insufficient. | Revisit if evidence shows Gemini needs a stronger/separate directive. |
| The "do not hand-edit inside aw:block" directive (TODO.md) | Low | scope | Related managed-block edit, but a distinct concern; batching them risks bloating the block. | Its own IPD (already in TODO.md). |
| Making the always-loaded directive long/imperative beyond one or two lines | Low | complexity/tokens | Violates the lean-block precedent (D99/D100); the spec carries the detail. | n/a |

## Scope check

- Over-scope: none - one canonical spec doc + one concise always-loaded directive (via the engine template + regenerated AGENTS.md) + docs. No review-logic change, no batching of the separate aw:block item.
- Under-scope: the spec MUST consolidate by reference not duplication (J1, P8); the directive MUST be short, go through `agents_pointer_prose` (not the legacy wrapper or a direct AGENTS.md edit), keep the reinstall empty-diff invariant, and leave the `AGENT-PLANS` sibling block untouched (J2); MUST depend on and reference Part 1's checklist + completion clause (do not restate them divergently).

## Required tests / validation

- The canonical spec exists under `.agents/docs/specs/` (named per convention) and consolidates the IPD conventions by reference (checklist + completion clause from Part 1, chunking, status/lifecycle/commit/paste-output rules) with no divergent restatement.
- The always-loaded directive is added to `agents_pointer_prose()` (one/two lines) and `AGENTS.md` is regenerated via the sectioned path so a reinstall is an EMPTY DIFF; the `AGENT-PLANS` sibling block is byte-identical.
- Full suite `python -m pytest -q` GREEN (there is an engine template-string change + AGENTS/idempotence coverage; paste ACTUAL output). `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- The new `ipd-spec.md`, `agent_workflows/engine.py` (`agents_pointer_prose`) + regenerated `AGENTS.md`, DECISIONS, CHANGELOG. Cross-reference Part 1, the archived `gits` FYI, and the TODO.md `aw:block` item.

## Open questions

- OQ1 (one shared directive vs per-host): RESOLVED - one directive in the shared managed block, which mirrors into CLAUDE.md/GEMINI.md via D104; a Gemini-specific variant is deferred unless evidence shows it is needed.
- OQ2 (coordinate with the aw:block edit-protection item): NOTED - keep this directive to one or two lines so it does not preempt or bloat the future aw:block directive; the two remain separate IPDs.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. DEPENDS ON Part 1 (Order 1) of this Set being executed first (the `ipd-spec.md` references the checklist + completion clause Part 1 adds; if Part 1's additions are absent, STOP and report).

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope (in particular, keep the always-loaded directive to one or two lines and do NOT edit `AGENTS.md` directly - edit `agents_pointer_prose` and regenerate). Never create or push a tag / Release / PyPI upload. Never disturb the `AGENT-PLANS` sibling block.

Recommended next steps:
1. Review (optionally `/plan-review`). Confirm Part 1 is executed first.
2. On human approval, execute, validate (full suite + AGENTS.md empty-diff), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
