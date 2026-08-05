# IPD: research tiered index generator + `find` (Set `research-org`, Order 3)

- Date: 2026-07-30
- Kind: child
- Concern: make "what did we find re X?" and "what needs addressing?" answerable without reading the corpus, via a tool-generated tiered manifest (INDEX.json = all; INDEX.md = bounded hot glance) and a query verb. Resolves OQ2 (default N) and OQ3 (commit vs generate the index).
- Scope: index generation + query + drift check, consuming Order-01 frontmatter and Order-02-created docs. No rename (04), no archival moves (05). Requires Orders 01, 02 executed; if their symbols are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 3
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the token-economy payoff (F1/F2).
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.

## Goal

`aw research index [--check]` regenerates `INDEX.json` (every doc) and `INDEX.md` (most-recent-N by set last-touched + intake band; includes reference; EXCLUDES archive) from frontmatter; `aw research find --id|--set|--topic|--status` answers queries over the JSON cheaply. `--check` fails on drift. Spec Sections 4.7, 4.8, 5.2, 5.5.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: index generation

- [ ] E-01 confirm Orders 01+02 are executed and the contract + create verbs are present, else STOP.
  - Depends on: none
  - Expected outcome: `research_contract` + the create verbs are importable; if absent the tool halts before generating.
  - Execution state: pending
- [ ] E-02 add `aw research index`: scan research frontmatter and build `INDEX.json` (all docs, all fields including the resolved current path).
  - Depends on: E-01
  - Expected outcome: the JSON contains every fixture doc with correct fields.
  - Execution state: pending
- [ ] E-03 generate `INDEX.md`: intake band + most-recent-N (by set last-touched, default N; OQ2), grouped by set, reference included, archive EXCLUDED, with a "do not edit" header.
  - Depends on: E-02
  - Expected outcome: an archived fixture is absent from INDEX.md but present in JSON; N is honored; intake is shown.
  - Execution state: pending

### Task group 2: query, drift, docs, tests

- [ ] E-04 add `aw research find --id|--set|--topic|--status`: query INDEX.json and print terse rows.
  - Depends on: E-02
  - Expected outcome: each filter returns the expected ids from a fixture set.
  - Execution state: pending
- [ ] E-05 add `--check`: exit nonzero on drift (missing/invalid frontmatter, name-vs-frontmatter mismatch, stale generated views).
  - Depends on: E-02, E-03
  - Expected outcome: a clean tree passes; a hand-edited stale INDEX.md fails.
  - Execution state: pending
- [ ] E-06 decide and document commit-vs-generate (OQ3) in the README: COMMIT `INDEX.json`+`INDEX.md` (so fresh clones/weak agents have them) and keep them fresh via `--check` (wireable into pre-commit later).
  - Depends on: E-05
  - Expected outcome: the README states the commit policy + the `--check` gate.
  - Execution state: pending
- [ ] E-07 add `tests/test_research_index.py` (JSON completeness; INDEX.md bounded + archive-excluded + intake-shown + N honored; `find` filters; `--check` clean-vs-drift); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Contract: import parsing/frontmatter/state vocab from Order 01; the index is a pure function of frontmatter (F2), never hand-maintained.
- Generated-file precedent: dir READMEs are generated no-clobber; INDEX.md is similarly generated (with a "do not edit" header) but IS refreshed (not no-clobber).
- CLI: extend the `research` subcommand group from Order 02.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C3-1 | HIGH | Low | agent (A1/F1) | token economy | Answering the two core questions must not require reading docs; a generated index over frontmatter does it. | spec 1, 4.7 |
| C3-2 | MEDIUM | Low | scale | glance size | At hundreds of files INDEX.md must stay bounded -> most-recent-N window, archive excluded. | spec 2, 4.8, 4.9 |
| C3-3 | MEDIUM | Low | integrity | drift | FS and index must not silently diverge -> `--check`. | spec 5.2/F4 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.7/5.2 | `aw research index`: scan research frontmatter, build `INDEX.json` (all docs, all fields incl. resolved current path). | `agent_workflows/research_cmd.py`, `agent_workflows/research_index.py` (new) | Low | E-02 |
| 2 | 4.8/4.9 | Generate `INDEX.md`: intake band + most-recent-N (by set last-touched, default N; OQ2), grouped by set, reference included, archive EXCLUDED; "do not edit" header. | `agent_workflows/research_index.py` | Low | E-03 |
| 3 | 5.5 | `aw research find --id|--set|--topic|--status`: query INDEX.json, print terse rows. | `agent_workflows/research_cmd.py` | Low | E-04 |
| 4 | 5.2/F4 | `--check`: nonzero on drift (missing/invalid frontmatter, name-vs-frontmatter mismatch, stale generated views). | `agent_workflows/research_index.py` | Low | E-05 |
| 5 | OQ3 | Decide + document commit-vs-generate: COMMIT `INDEX.json`+`INDEX.md` (fresh clones/weak agents have them) and keep them fresh via `--check` (wireable into pre-commit later). | `.agents/docs/research/README.md` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Moving files to shards / archive | n/a | scope | Archival moves are Order 05; index only READS locations. | Order 05 |
| Wiring `--check` into the pre-commit hook | usability | Keep this child tool-only; hook wiring is a scaffold concern. | Order 07 (optional) |

## Scope check

- Over-scope: none - generate + query + check.
- Under-scope: MUST bound INDEX.md (N + archive-excluded), keep JSON complete, and detect drift.

## Required tests / validation

`tests/test_research_index.py`: JSON completeness; INDEX.md bounded + archive-excluded + intake-shown + N honored; `find` filters; `--check` clean-vs-drift. Run it + full `python -m pytest -q`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md`: index tiers, N default, commit policy (OQ3), the `--check` gate.

## Open questions

### OQ-01: default N and commit-the-index policy (OQ2/OQ3)

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: OQ2 default N is adopted at a lean of 30 to 50, and OQ3 is resolved to COMMIT the generated `INDEX.json`+`INDEX.md` and keep them fresh via `--check`. Confirm both leans at review; if either changes, only this child changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01+02 in `executed/` and their symbols importable; confirm the tool halts when they are absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a JSON snippet showing all fixture docs + fields.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste INDEX.md fixture output; confirm the archived doc is ABSENT, intake is present, and N is honored.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm each `find` filter returns the expected ids; cite test output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm a clean tree passes and a stale INDEX.md fails; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: confirm the README states the N default + commit policy + `--check` gate; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `pytest tests/test_research_index.py -q` + the full-suite summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (index/find/check only; no file moves). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
