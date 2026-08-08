# IPD: research naming, id, and frontmatter contract (Set `research-org`, Order 1)

- Date: 2026-07-30
- Kind: child
- Concern: define the single authoritative contract that all research tooling and docs depend on: the filename grammar, the stable `<id6>` id, the enumerated `<model>`/`<kind>` vocabularies, and the frontmatter schema. Resolves spec open questions OQ1 (kind vocab), OQ4 (set-date-in-name vs per-file created), OQ5 (id length/alphabet), OQ6 (state paths).
- Scope: authoritative definitions + constants + docs ONLY. No behavior change, no migration, no tool that consumes it yet (those are Orders 2 to 07). Requires spec `.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md`.
- Status: approved
- Set: research-org
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-08-07 human maintainer (via opencode its_direct/pt3-claude-opus-4.8-1m-us): "Consider them all approved. Please do them in the recommended order."

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): first child of Set `research-org`; establishes the contract so Orders 2 to 07 reference ONE definition (cross-IPD consistency).
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-C01-1 (E-05 rewrite the existing stale-grammar README, do not append). Contract verified correct against the spec; already used stdlib unittest (no PR-001 change needed).

## Goal

Produce the definitive, machine- and human-readable contract for research artifacts so every later child and the tool share one source of truth. Nothing consumes it yet; this child only DEFINES it and documents it. This prevents the drift the orchestrator's cross-IPD validation guards against.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: contract module

- [ ] E-01 add `agent_workflows/research_contract.py` with the `<id6>` primitives: 6-char base36-lowercase (`[0-9a-z]`) alphabet, a compiled id regex, and a `\b<id6>\b` reference regex.
  - Depends on: none
  - Expected outcome: id regex matches a sample id in a filename and in prose; rejects a 5-char, a 7-char, and a non-base36 token.
  - Execution state: pending
- [ ] E-02 define the enumerated `<model>` and `<kind>` vocabularies as constants (from the corpus survey) + a normalization map (`gpt-56` -> `gpt56`; `chatgpt` recorded as provenance) + a documented extension list.
  - Depends on: E-01
  - Expected outcome: known kinds/models accepted; `gpt-56` normalizes; an unknown kind is rejected with a suggestion.
  - Execution state: pending
- [ ] E-03 define the filename grammar `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md` and the directory layout (hot states at `research/` root; `reference/YYYYMM-Www/` and `archive/YYYYMM-Www/` shards) as a tested parser/formatter pair; set date in the name, per-file `created` in frontmatter.
  - Depends on: E-01, E-02
  - Expected outcome: parse+format round-trips >=3 real corpus-derived names, a singleton, and an optional-`<model>` name.
  - Execution state: pending
- [ ] E-04 define the research frontmatter schema (id, created, set, order, topic[], model, kind, status{intake,active,reference,archive}, outcome{adopted,rejected,informational,none-yet}, summary, consumed-by[]) with a validator returning structured errors.
  - Depends on: E-01
  - Expected outcome: a valid block passes; missing `id` / bad `status` fail with precise messages.
  - Execution state: pending

### Task group 2: docs + tests

- [ ] E-05 REWRITE the existing `.agents/docs/research/README.md` (which currently documents the SUPERSEDED `YYYYMMDD-HHMM-NN` grammar), REPLACING that stale grammar with the new contract (grammar, states, id, tool pointer) referencing the spec; do not merely append.
  - Depends on: E-01
  - Expected outcome: README states ONLY the new grammar + states + id + where the tool lives; the superseded `YYYYMMDD-HHMM-NN` grammar no longer appears; no em/en dashes.
  - Execution state: pending
- [ ] E-06 add `tests/test_research_contract.py` (id regex; vocab accept/normalize/reject; name parse+format round-trip incl. singleton + optional model; frontmatter validate pass/fail); run it + the full suite and paste both.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P4 durable knowledge, P5 externalize state; P5's research carve-out is revised by this Set, edited in Order 07 not here).
- Spec: `.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md` (Sections 4.1, 4.2, 4.4, 4.5, 5.4, 5.8 are the source for this contract).
- Existing naming enforcement lives in `normalize_plan_names.py` / the `aw plan-names` verb; the research grammar is a NEW, richer grammar and must NOT silently break that verb (coordinated in Order 06/07). This child only defines constants/docs; it does not wire the normalizer.
- Precedent: `agent_workflows/ipd_schema.py` (the IPD structural schema) is the pattern for a stdlib-only, pure contract module; mirror its style.
- House rule: no em/en dashes in authored Markdown; external artifacts verbatim.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C1-1 | HIGH | Low | architect | consistency | Without one authoritative contract, the later children will each restate/fork the grammar and vocab and drift. | spec Section 3 H1, orchestrator cross-IPD validation |
| C1-2 | MEDIUM | Low | tooling | correctness | `<id6>` must be word-boundary greppable (`\b<id6>\b`) or F5 dangling-cite detection fails. | spec 4.1/D2 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | C1-2 | `<id6>` primitives | `agent_workflows/research_contract.py` (new) | Low | E-01 |
| 2 | C1-1 | model/kind vocab + normalization | `agent_workflows/research_contract.py` | Low | E-02 |
| 3 | C1-1 | filename grammar + dir layout parse/format | `agent_workflows/research_contract.py` | Low | E-03 |
| 4 | C1-1 | frontmatter schema + validator | `agent_workflows/research_contract.py` | Low | E-04 |
| 5 | C1-1 | README + tests | `.agents/docs/research/README.md`, `tests/test_research_contract.py` | Low | E-05, E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| The `aw research` CLI that USES this contract | n/a | scope | This child is the contract only. | Order 02+ |
| Wiring `normalize_plan_names`/`aw plan-names` to the research grammar | n/a | scope | Keep this child behavior-free; normalizer coordination is a migration/scaffold concern. | Order 06/07 |
| P5 text edit + DECISIONS entry | n/a | scope | Consolidated in one place to avoid double-edits. | Order 07 |

## Scope check

- Over-scope: none - constants, a parse/format/validate module, and one README. No CLI, no file moves.
- Under-scope: MUST define id + grammar + vocab + frontmatter schema as tested, importable primitives so Orders 2 to 07 import rather than restate them.

## Required tests / validation

New `tests/test_research_contract.py`: id regex (match in name + prose; reject wrong length/charset); vocab accept/normalize/reject; name parse+format round-trip incl. singleton and optional `<model>`; frontmatter validate pass/fail with precise errors. Run `python3 -m unittest tests.test_research_contract -v` then `python3 -m unittest discover -s tests -t .`; paste both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md` documents the contract (grammar, states, id, tool pointer). The canonical rationale remains the spec; the README points to it.

## Open questions

### OQ-01: spec leans (id/date/shards/kind vocab)

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: OQ1/OQ4/OQ5/OQ6 from the spec are adopted with the spec's leans (base36-6 id; set-date-in-name + per-file `created`; hot-at-root + weekly `reference`/`archive` shards; corpus-derived kind vocab + extension). If a lean changes, only this child changes and the others inherit it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a test showing the id regex matches `k7m2xq` in `...-k7m2xq-...md` and in prose, and rejects a 5-char, 7-char, and non-base36 token.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a test showing `gpt-56` -> `gpt56` normalization and an unknown kind rejected with a suggestion.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a test round-tripping >=3 real corpus-derived names, a singleton (set of one), and an optional-`<model>` name through parse+format.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a test showing a valid frontmatter block passes and missing-`id` / bad-`status` fail with precise messages.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm `research/README.md` states the NEW grammar + states + id + tool pointer and points to the spec, AND that the superseded `YYYYMMDD-HHMM-NN` grammar no longer appears (grep shows no residual); no em/en dashes; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m unittest tests.test_research_contract -v` result AND the full-suite summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Contract-only child; no behavior consumes it yet. Do NOT claim done or move to `executed/` until every `E-*` is `performed`+checked AND its matching `V-*` is `pass`+checked with concrete evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (this child defines the contract; it does NOT add the CLI, migrate files, or edit P5/DECISIONS). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
