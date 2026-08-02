# IPD: research naming, id, and frontmatter contract (Set `research-org`, Order 1)

- Date: 2026-07-30
- Concern: define the single authoritative contract that all research tooling and docs depend on: the filename grammar, the stable `<id6>` id, the enumerated `<model>`/`<kind>` vocabularies, and the frontmatter schema. Resolves spec open questions OQ1 (kind vocab), OQ4 (set-date-in-name vs per-file created), OQ5 (id length/alphabet), OQ6 (state paths).
- Scope: authoritative definitions + constants + docs ONLY. No behavior change, no migration, no tool that consumes it yet (those are Orders 2 to 07). Requires spec `.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md`.
- Status: to-review
- Set: research-org
- Order: 1
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): first child of Set `research-org`; establishes the contract so Orders 2 to 07 reference ONE definition (cross-IPD consistency).

## Goal

Produce the definitive, machine- and human-readable contract for research artifacts so every later child and the tool share one source of truth. Nothing consumes it yet; this child only DEFINES it and documents it. This prevents the drift the orchestrator's cross-IPD validation guards against.

## Detailed Implementation Checklist (TODO)

- [ ] **Task 1: id primitives** - add `research_contract.py` with base36-6 id alphabet/length, id regex, and `\b<id6>\b` reference regex.
- [ ] **Task 2: vocab** - `<model>`/`<kind>` enumerations + normalization map + extension list.
- [ ] **Task 3: grammar** - parse/format for `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md` + the directory-layout constants.
- [ ] **Task 4: frontmatter schema + validator** with structured errors.
- [ ] **Task 5: README** documents the contract (points to the spec).
- [ ] **Tests** `tests/test_research_contract.py`; run it + full suite and PASTE output.
- [ ] **Lifecycle/commit** path-scoped; `git add` new files; never push.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P4 durable knowledge, P5 externalize state; P5's research carve-out is revised by this Set, edited in Order 07 not here).
- Spec: `.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md` (Sections 4.1, 4.2, 4.4, 4.5, 5.4, 5.8 are the source for this contract).
- Existing naming enforcement lives in `normalize_plan_names.py` / the `aw plan-names` verb; the research grammar is a NEW, richer grammar and must NOT silently break that verb (coordinated in Order 06/07). This child only defines constants/docs; it does not wire the normalizer.
- House rule: no em/en dashes in authored Markdown; external artifacts verbatim.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C1-1 | HIGH | Low | architect | consistency | Without one authoritative contract, the 6 later children will each restate/fork the grammar and vocab and drift. | spec Section 3 H1, orchestrator cross-IPD validation |
| C1-2 | MEDIUM | Low | tooling | correctness | `<id6>` must be word-boundary greppable (`\b<id6>\b`) or F5 dangling-cite detection fails. | spec 4.1/D2 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | OQ5, 4.1 | Define `<id6>` = 6 chars, base36 lowercase (`[0-9a-z]`), random, collision-checked; word-boundary clean. Add a constants module (e.g. `agent_workflows/research_contract.py`) with the id alphabet/length, a compiled id regex, and a `\b<id6>\b` reference regex. | `agent_workflows/research_contract.py` (new) | Low | unit test: id regex matches a sample id in a filename and in prose, rejects a 5- and 7-char and non-base36 token |
| 2 | OQ1, 5.4 | Define the enumerated `<model>` and `<kind>` vocabularies as constants (from the corpus survey) + a normalization map (`gpt-56`->`gpt56`, `chatgpt`->recorded provenance) + an extension mechanism (a documented list the tool reads). | `agent_workflows/research_contract.py` | Low | unit test: known kinds/models accepted; `gpt-56` normalizes; unknown kind rejected with a suggestion |
| 3 | OQ4, OQ6, 4.2/4.9 | Define the filename grammar `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md` and the directory layout (hot states at `research/` root; `reference/YYYYMM-Www/` and `archive/YYYYMM-Www/` shards) as a documented, tested parser/formatter pair (parse a name -> fields; format fields -> name). Set date in name; per-file `created` in frontmatter. | `agent_workflows/research_contract.py` | Low | unit test round-trips several real corpus-derived names through parse+format; singleton (set of one) parses; optional `<model>` handled |
| 4 | 5.8 | Define the frontmatter schema (id, created, set, order, topic[], model, kind, status{intake,active,reference,archive}, outcome{adopted,rejected,informational,none-yet}, summary, consumed-by[]) with a validator that returns structured errors. | `agent_workflows/research_contract.py` | Low | unit test: a valid block passes; missing `id`/bad `status` fails with a precise message |
| 5 | all | Document the contract in `.agents/docs/research/README.md` (regenerated content is fine) and reference the spec; add a DECISIONS pointer is deferred to Order 07 (one place). | `.agents/docs/research/README.md` (or its template) | Low | README states the grammar + states + id + where the tool lives; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| The `aw research` CLI that USES this contract | n/a | scope | This child is the contract only. | Order 02+ |
| Wiring `normalize_plan_names`/`aw plan-names` to the research grammar | scope | Keep this child behavior-free; normalizer coordination is a migration/scaffold concern. | Order 06/07 |
| P5 text edit + DECISIONS entry | scope | Consolidated in one place to avoid double-edits. | Order 07 |

## Scope check

- Over-scope: none - constants, a parse/format/validate module, and one README. No CLI, no file moves.
- Under-scope: MUST define id + grammar + vocab + frontmatter schema as tested, importable primitives so Orders 2 to 07 import rather than restate them.

## Required tests / validation

New `tests/test_research_contract.py`: id regex (match in name + prose; reject wrong length/charset); vocab accept/normalize/reject; name parse+format round-trip incl. singleton and optional `<model>`; frontmatter validate pass/fail with precise errors. Run `python -m pytest tests/test_research_contract.py -q` and PASTE output; then full `python -m pytest -q` (expect prior count + the new tests; paste actual). Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md` documents the contract (grammar, states, id, tool pointer). The canonical rationale remains the spec; the README points to it.

## Open questions

- OQ1/OQ4/OQ5/OQ6 from the spec are RESOLVED here with the leans in the spec (base36-6; set-date-in-name + per-file `created`; hot-at-root + weekly shards for reference/archive; corpus-derived kind vocab + extension). Confirm at review; if the human changes a lean, only this child changes and the others inherit it.

## Validation and cross-check (verify before reporting done)

- [ ] Task 1: CONFIRM the id regex matches `k7m2xq` in `...-k7m2xq-...md` and in prose, rejects 5/7-char and non-base36; cite the test output.
- [ ] Task 2: CONFIRM `gpt-56`->`gpt56` normalizes and an unknown kind is rejected with a suggestion; cite test output.
- [ ] Task 3: CONFIRM parse+format round-trips >=3 real corpus-derived names, a singleton, and an optional-`<model>` name; cite test output.
- [ ] Task 4: CONFIRM a valid frontmatter block passes and missing-`id`/bad-`status` fail with precise messages; cite test output.
- [ ] Task 5: CONFIRM `research/README.md` states grammar+states+id+tool pointer and points to the spec; no em/en dashes.
- [ ] PASTE `pytest tests/test_research_contract.py -q` and the full-suite summary; confirm leak-clean.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; else do not transition.

## Approval and execution gate

Proposal; human review + approval required; not auto-executed. Contract-only child; no behavior consumes it yet. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation item is verified with concrete evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (this child defines the contract; it does NOT add the CLI, migrate files, or edit P5/DECISIONS). Never create or push a tag / Release / PyPI upload.

Recommended next steps: review (optionally `/plan-review`); on approval execute; then Order 02 depends on this.
