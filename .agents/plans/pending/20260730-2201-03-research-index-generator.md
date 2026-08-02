# IPD: research tiered index generator + `find` (Set `research-org`, Order 3)

- Date: 2026-07-30
- Concern: make "what did we find re X?" and "what needs addressing?" answerable without reading the corpus, via a tool-generated tiered manifest (INDEX.json = all; INDEX.md = bounded hot glance) and a query verb. Resolves OQ2 (default N) and OQ3 (commit vs generate the index).
- Scope: index generation + query + drift check, consuming Order-01 frontmatter and Order-02-created docs. No rename (04), no archival moves (05). Requires Orders 01, 02 executed; if their symbols are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 3
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the token-economy payoff (F1/F2).

## Goal

`aw research index [--check]` regenerates `INDEX.json` (every doc) and `INDEX.md` (most-recent-N by set last-touched + intake band; includes reference; EXCLUDES archive) from frontmatter; `aw research find --id|--set|--topic|--status` answers queries over the JSON cheaply. `--check` fails on drift. Spec Sections 4.7, 4.8, 5.2, 5.5.

## Detailed Implementation Checklist (TODO)

- [ ] **Precheck**: Orders 01+02 executed; contract + create verbs present, else STOP.
- [ ] **Task 1: INDEX.json** (all docs from frontmatter).
- [ ] **Task 2: INDEX.md** (intake + most-recent-N, reference in / archive out, do-not-edit header).
- [ ] **Task 3: `aw research find`** filters.
- [ ] **Task 4: `--check`** drift gate.
- [ ] **Task 5: document OQ2/OQ3** in README.
- [ ] **Tests** `tests/test_research_index.py`; run it + full suite and PASTE output.
- [ ] **Lifecycle/commit** path-scoped; `git add` new files; never push.

## Project conventions discovered (Step 0)

- Contract: import parsing/frontmatter/state vocab from Order 01; the index is a pure function of frontmatter (F2), never hand-maintained.
- Generated-file precedent: dir READMEs are generated no-clobber; INDEX.md is similarly generated (with a "do not edit" header) but IS refreshed (not no-clobber).
- CLI: extend the `research` subcommand group from Order 02.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C3-1 | HIGH | Low | agent (A1/F1) | token economy | Answering the two core questions must not require reading docs; a generated index over frontmatter does it. | spec 1, 4.7 |
| C3-2 | MEDIUM | Low | scale | glance size | At hundreds of files INDEX.md must stay bounded -> most-recent-N window, archive excluded. | spec 2, 4.8, 4.9 |
| C3-3 | MEDIUM | Low | integrity | drift | FS and index must not silently diverge -> `--check`. | spec 5.2/F4 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.7/5.2 | `aw research index`: scan research frontmatter, build `INDEX.json` (all docs, all fields incl. resolved current path). | `agent_workflows/research_cmd.py`, `agent_workflows/research_index.py` (new) | Low | test: JSON contains every fixture doc with correct fields |
| 2 | 4.8/4.9 | Generate `INDEX.md`: intake band + most-recent-N (by set last-touched, default N; OQ2), grouped by set, reference included, archive EXCLUDED; "do not edit" header. | `agent_workflows/research_index.py` | Low | test: an archived fixture is absent from INDEX.md but present in JSON; N honored; intake shown |
| 3 | 5.5 | `aw research find --id|--set|--topic|--status`: query INDEX.json, print terse rows. | `agent_workflows/research_cmd.py` | Low | test: each filter returns the expected ids from a fixture set |
| 4 | 5.2/F4 | `--check`: nonzero on drift (missing/invalid frontmatter, name-vs-frontmatter mismatch, stale generated views). | `agent_workflows/research_index.py` | Low | test: clean tree passes; a hand-edited stale INDEX.md fails |
| 5 | OQ3 | Decide + document commit-vs-generate: COMMIT `INDEX.json`+`INDEX.md` (fresh clones/weak agents have them) and keep them fresh via `--check` (wireable into pre-commit later). | `.agents/docs/research/README.md` | Low | README states the commit policy + the `--check` gate |

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

- OQ2 default N (lean 30 to 50) and OQ3 commit-the-index (lean yes) are resolved here; confirm at review.

## Validation and cross-check (verify before reporting done)

- [ ] Precheck: cite Orders 01+02 in executed/ and their symbols importable.
- [ ] Task 1: PASTE JSON snippet showing all fixture docs + fields.
- [ ] Task 2: PASTE INDEX.md fixture output; confirm archived doc ABSENT, intake present, N honored.
- [ ] Task 3: confirm each `find` filter returns expected ids; cite test output.
- [ ] Task 4: confirm clean passes, stale fails; cite.
- [ ] Task 5: confirm README states N + commit policy + `--check`.
- [ ] PASTE `pytest tests/test_research_index.py -q` + full-suite summary; leak-clean.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; else do not transition.

## Approval and execution gate

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02; if absent, STOP. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation item is verified with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (index/find/check only; no file moves). Never create or push a tag / Release / PyPI upload.
