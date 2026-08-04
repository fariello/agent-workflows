# IPD: research state lifecycle + weekly archival shards (Set `research-org`, Order 5)

- Date: 2026-07-30
- Concern: implement the state lifecycle (intake/active/reference/archive) and the weekly `YYYYMM-Www` cold shards for reference and archive, with deliberate, tool-invoked archival verbs (never a background side effect).
- Scope: state transitions + shard layout + `aw archive` verbs, consuming Orders 01 and 03. No corpus migration (06). Requires Orders 01, 03 executed; if their symbols are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 5
- Quarantine: old-shape draft; superseded by the ipd-structure convention, to be re-authored to the E-*/V-* shape
- Quarantine owner: maintainer (IPD-system-first sequencing decision, 2026-08-03)
- Quarantine follow-up: re-author the research-org Set to the new schema after the ipd-structure Set lands
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the compartmentalization + scale mechanism.

- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's IPD-system-first sequencing decision defers this old-shape research-org plan; quarantined under spec Section 13.3 (metadata trio added) pending re-authoring to the new E-*/V-* shape after the ipd-structure Set. Not conforming, not an error; an informational disposition.

## Goal

Move cold docs into weekly shards and manage state: `reference/YYYYMM-Www/` (mattered; in the hot glance via most-recent-N) and `archive/YYYYMM-Www/` (just-in-case; excluded from the hot glance). `aw archive [research] <set-id|doc-id>` deep-shelves a target; bare `aw archive [research]` sweeps aged candidates (older than two weeks by default) with a PREVIEW before moving. Promotion to `reference` is a distinct deliberate act. Spec Sections 4.5, 4.9, 4.10.

## Detailed Implementation Checklist (TODO)

- [ ] **Precheck**: Orders 01+03 executed; symbols present, else STOP.
- [ ] **Task 1: shard layout + status-transition move** (id/cites intact).
- [ ] **Task 2: targeted `aw archive <id>`** (dry-run/apply).
- [ ] **Task 3: bare `aw archive` aged sweep** (preview).
- [ ] **Task 4: miscategorization flag**.
- [ ] **Task 5: INDEX refresh after move**.
- [ ] **Tests** `tests/test_research_archive.py`; run it + full suite and PASTE output.
- [ ] **Lifecycle/commit** path-scoped; `git add` new files; never push.

## Project conventions discovered (Step 0)

- Contract: state vocab + shard-path constants from Order 01; recency/last-touched from Order 03's index.
- Determinism: archival is ALWAYS on invocation, never index-time or background (spec 4.10); mirror the dry-run/preview + `--apply` safety pattern.
- The reference-vs-archive judgment is curation, not derivable; the tool DEFAULTS (cited -> reference; uncited+aged -> archive candidate) and FLAGS miscategorization.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C5-1 | HIGH | Medium | scale | glance size | Cold items must leave the hot area or the glance/tree renoise at hundreds of files. | spec 2, 4.9 |
| C5-2 | MEDIUM | Low | safety | surprise | Archival must be deliberate + previewed; no silent moves. | spec 4.10 |
| C5-3 | MEDIUM | Medium | curation | correctness | reference vs archive is a recorded judgment; tool must default + flag, not silently guess. | spec 4.5 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.5/4.9 | Shard layout + a `status` transition helper: set `status` in frontmatter AND move the file to the matching location (`reference/YYYYMM-Www/`, `archive/YYYYMM-Www/`, or hot root for intake/active), keeping `<id6>`; reuse Order 04's reference-update on move. | `agent_workflows/research_archive.py` (new), `agent_workflows/research_cmd.py` | Medium | test: promoting to reference moves into the correct week shard; id + cites intact |
| 2 | 4.10 | `aw archive [research] <set-id|doc-id>`: deep-shelve target(s) to `archive/YYYYMM-Www/`, dry-run/preview default + `--apply`. | `agent_workflows/research_cmd.py` | Medium | test: named set moves to archive shard on `--apply`, previewed otherwise |
| 3 | 4.10 | Bare `aw archive [research]`: select candidates older than two weeks (default) that are uncited, PREVIEW, move on `--apply`. | `agent_workflows/research_archive.py` | Medium | test: aged uncited fixture selected; recent/cited excluded; preview shown |
| 4 | 4.5 | Miscategorization flag: a doc in `archive/` that IS cited by DECISIONS/plan is reported ("should be reference?"). | `agent_workflows/research_archive.py` | Low | test: archived-but-cited fixture is flagged |
| 5 | 4.7 | After any archival move, refresh INDEX (reference stays in most-recent-N window; archive excluded). | `agent_workflows/research_cmd.py` | Low | test: archived doc leaves INDEX.md, reference doc remains |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Classifying the existing 78 files | n/a | scope | Migration curation. | Order 06 |
| Applying shards to plans/prompts | n/a | scope | Future adopters. | Order 07 TODO |

## Scope check

- Over-scope: none - state transitions + shards + archive verbs + refresh.
- Under-scope: MUST keep archival deliberate/previewed, keep `<id6>`+cites intact on move, and keep archive out of the hot glance while reference stays in.

## Required tests / validation

`tests/test_research_archive.py`: promote-to-reference shard move (id/cites intact); targeted archive; aged-uncited sweep selection + preview; miscategorization flag; INDEX refresh (archive out, reference in). Run it + full `python -m pytest -q`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md`: the four states, weekly shards, the archive verbs + preview safety, and the reference-vs-archive curation rule.

## Open questions

- Default sweep age (two weeks) and whether the sweep also requires uncited (lean: aged AND uncited). Confirm at review.

## Validation and cross-check (verify before reporting done)

- [ ] Precheck: cite Orders 01+03 in executed/.
- [ ] Task 1: PASTE a promote-to-reference move showing correct week shard + unchanged id + updated cite.
- [ ] Task 2: confirm targeted archive previews then moves on `--apply`; cite.
- [ ] Task 3: confirm aged+uncited selected, recent/cited excluded, preview shown; cite.
- [ ] Task 4: confirm archived-but-cited is flagged; cite.
- [ ] Task 5: confirm archived doc leaves INDEX.md and reference remains; cite.
- [ ] PASTE `pytest tests/test_research_archive.py -q` + full-suite summary; leak-clean.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; else do not transition.

## Approval and execution gate

Proposal; human review + approval; not auto-executed. Requires Orders 01, 03; if absent, STOP. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation item is verified with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (states/shards/archive verbs only; no corpus migration). Never create or push a tag / Release / PyPI upload.
