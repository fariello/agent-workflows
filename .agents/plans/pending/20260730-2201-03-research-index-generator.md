# IPD: research tiered index generator + `find` (Set `research-org`, Order 3)

- Date: 2026-07-30
- Kind: child
- Concern: make "what did we find re X?" and "what needs addressing?" answerable without reading the corpus, via a tool-generated tiered manifest (INDEX.json = all; INDEX.md = bounded hot glance) and a query verb. Resolves OQ2 (default N) and OQ3 (commit vs generate the index).
- Scope: index generation + query + drift check, consuming Order-01 frontmatter, Order-02-created docs, and Order-04's dangling-cite detector primitive (so `--check` catches citation rot, spec 5.2). No rename verbs (04), no archival moves (05). Requires Orders 01, 02, 04 executed; if their symbols are absent, STOP. Executes AFTER Order 04.
- Status: approved
- Set: research-org
- Order: 3
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-08-07 human maintainer (via opencode its_direct/pt3-claude-opus-4.8-1m-us): "Consider them all approved. Please do them in the recommended order."

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the token-economy payoff (F1/F2).
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (pytest->unittest), PR-006 (dep on Order 04 + `--check` consumes its dangling detector, spec 5.2's 4th class), PR-011 (OQ2 N=40 configurable; OQ3 commit-the-index confirmed), PR-C03-6 (determinism: byte-compare + total sort), PR-C03-7 (`--agent` output + 0/1/2 exit codes), PR-C03-9 (V asserts reference PRESENT).

## Goal

`aw research index [--check]` regenerates `INDEX.json` (every doc) and `INDEX.md` (most-recent-N by set last-touched + intake band; includes reference; EXCLUDES archive) from frontmatter; `aw research find --id|--set|--topic|--status` answers queries over the JSON cheaply. `--check` fails on drift. Spec Sections 4.7, 4.8, 5.2, 5.5.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: index generation

- [ ] E-01 confirm Orders 01+02+04 are executed and the contract + create verbs + Order-04 dangling-cite detector are present, else STOP.
  - Depends on: none
  - Expected outcome: `research_contract`, the create verbs, and Order 04's dangling-cite primitive are importable; if absent the tool halts before generating.
  - Execution state: pending
- [ ] E-02 add `aw research index`: scan research frontmatter and build `INDEX.json` (all docs, all fields including the resolved current path). The index is a PURE, deterministic function of frontmatter (no model/network/writes beyond the two generated files); INDEX.md ordering uses a total deterministic sort (set last-touched desc, then set-id, then `<id6>`) so equal dates never reorder.
  - Depends on: E-01
  - Expected outcome: the JSON contains every fixture doc with correct fields; regenerating twice yields byte-identical output.
  - Execution state: pending
- [ ] E-03 generate `INDEX.md`: intake band + most-recent-N (by set last-touched; default N = 40, overridable via a `research_contract` constant and `aw research index --limit N`; resolves OQ2), grouped by set, reference INCLUDED, archive EXCLUDED, with a "do not edit" header.
  - Depends on: E-02
  - Expected outcome: an archived fixture is absent from INDEX.md but present in JSON; a reference fixture is PRESENT in INDEX.md; N (=40) is honored; intake is shown.
  - Execution state: pending

### Task group 2: query, drift, docs, tests

- [ ] E-04 add `aw research find --id|--set|--topic|--status`: query INDEX.json and print terse rows.
  - Depends on: E-02
  - Expected outcome: each filter returns the expected ids from a fixture set.
  - Execution state: pending
- [ ] E-05 add `--check`: exit nonzero on drift (missing/invalid frontmatter, name-vs-frontmatter mismatch, stale generated view detected by in-memory regenerate-and-byte-compare, AND a dangling citation via Order 04's imported detector primitive; spec 5.2's four drift classes). Provide `--agent` tab-separated `location\trule\tseverity` output and distinct exit codes (0 clean, 1 drift, 2 could-not-run), mirroring `aw ipd lint`.
  - Depends on: E-02, E-03
  - Expected outcome: a clean tree passes; a hand-edited stale INDEX.md fails; a dangling citation fails; `--agent` emits machine-readable records.
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

- Contract: import parsing/frontmatter/state vocab from Order 01; the index is a pure, deterministic function of frontmatter (F2), never hand-maintained; no model/network.
- Dangling-cite detection is NOT reimplemented here; `--check` imports Order 04's `research_refs.py` detector primitive (spec 5.2). This is why Order 03 depends on and runs after Order 04.
- Generated-file precedent: dir READMEs are generated no-clobber; INDEX.md is similarly generated (with a "do not edit" header) but IS refreshed (not no-clobber). Determinism + `--agent` output + distinct exit codes follow the `aw ipd lint` precedent.
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
| 4 | 5.2/F4 | `--check`: nonzero on drift (missing/invalid frontmatter, name-vs-frontmatter mismatch, stale generated view via byte-compare, dangling citation via Order 04's detector); `--agent` output + 0/1/2 exit codes. | `agent_workflows/research_index.py` | Low | E-05 |
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

`tests/test_research_index.py`: JSON completeness; INDEX.md bounded + archive-excluded + reference-INCLUDED + intake-shown + N(=40) honored; determinism (regenerate twice, byte-identical); `find` filters; `--check` clean-vs-drift for all four classes incl. dangling-citation; `--agent` output shape + exit codes. Run it + full `python3 -m unittest discover -s tests -t .`; PASTE both (the `Ran N tests ... OK` summary). Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md`: index tiers, N default, commit policy (OQ3), the `--check` gate.

## Open questions

### OQ-01: default N and commit-the-index policy (OQ2/OQ3)

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: RESOLVED at review (2026-08-07). OQ2: default N = 40, overridable via a `research_contract` constant and `aw research index --limit N`. OQ3: COMMIT the generated `INDEX.json`+`INDEX.md` (so fresh clones and weak agents have them) and keep them fresh via the `--check` gate (wireable into pre-commit later).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01+02 in `executed/` and their symbols importable; confirm the tool halts when they are absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a JSON snippet showing all fixture docs + fields; confirm regenerating the index twice yields byte-identical output (determinism).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste INDEX.md fixture output; confirm the archived doc is ABSENT, a reference doc is PRESENT, intake is present, and N (=40) is honored.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm each `find` filter returns the expected ids; cite test output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm a clean tree passes, a stale INDEX.md fails, AND a dangling citation fails (via Order 04's imported detector); paste a sample `--agent` tab-separated record and confirm exit codes 0/1/2; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: confirm the README states the N default + commit policy + `--check` gate; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m unittest tests.test_research_index -v` + the full-suite `Ran N tests ... OK` summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (index/find/check only; no file moves). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
