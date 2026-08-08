# IPD: research state lifecycle + weekly archival shards (Set `research-org`, Order 5)

- Date: 2026-07-30
- Kind: child
- Concern: implement the state lifecycle (intake/active/reference/archive) and the weekly `YYYYMM-Www` cold shards for reference and archive, with deliberate, tool-invoked archival verbs (never a background side effect).
- Scope: state transitions + shard layout + `aw archive` verbs, consuming Orders 01, 03, and 04 (moving a file changes its path, so it reuses Order 04's reference-updater rather than reimplementing it). No corpus migration (06). Requires Orders 01, 03, 04 executed; if their symbols are absent, STOP.
- Status: approved
- Set: research-org
- Order: 5
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-08-07 human maintainer (via opencode its_direct/pt3-claude-opus-4.8-1m-us): "Consider them all approved. Please do them in the recommended order."

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the compartmentalization + scale mechanism.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (pytest->unittest), PR-C05-2 (declare dep on Order 04 for reference-update), PR-C05-5 (per-item accept/override curation with recorded `status`, spec 4.5), PR-C05-6 (bare-sweep selector = aged AND uncited, confirmed), PR-C05-4/7 (miscat detection via `consumed-by`/Order-04 detector), atomic tracked moves.

## Goal

Move cold docs into weekly shards and manage state: `reference/YYYYMM-Www/` (mattered; in the hot glance via most-recent-N) and `archive/YYYYMM-Www/` (just-in-case; excluded from the hot glance). `aw archive [research] <set-id|doc-id>` deep-shelves a target; bare `aw archive [research]` sweeps aged candidates (older than two weeks by default) with a PREVIEW before moving. Promotion to `reference` is a distinct deliberate act. Spec Sections 4.5, 4.9, 4.10.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: state transitions and shards

- [ ] E-01 confirm Orders 01+03+04 are executed and their symbols are present, else STOP.
  - Depends on: none
  - Expected outcome: the contract + index + Order-04 reference-updater symbols are importable; if absent the tool halts before moving files.
  - Execution state: pending
- [ ] E-02 add the shard layout + `status` transition helper: set `status` in frontmatter AND move the file to the matching location (`reference/YYYYMM-Www/`, `archive/YYYYMM-Www/`, or hot root for intake/active) as an atomic tracked rename (prefer `git mv`, staged), keeping `<id6>`; reuse Order 04's reference-updater on move (do not reimplement it).
  - Depends on: E-01
  - Expected outcome: promoting to reference moves into the correct week shard via a tracked rename; id + cites intact.
  - Execution state: pending

### Task group 2: archive verbs, flags, refresh, tests

- [ ] E-03 add `aw archive [research] <set-id|doc-id>`: deep-shelve target(s) to `archive/YYYYMM-Www/`, dry-run/preview default + `--apply`.
  - Depends on: E-02
  - Expected outcome: a named set moves to the archive shard on `--apply`, previewed otherwise.
  - Execution state: pending
- [ ] E-04 add bare `aw archive [research]`: select candidates that are BOTH older than two weeks AND uncited, PREVIEW each with the tool's DEFAULT classification (reference vs archive), let the operator accept or override PER ITEM before applying, then move accepted items on `--apply` and record the resulting `status` in frontmatter (the recorded reference-vs-archive judgment, spec 4.5).
  - Depends on: E-02
  - Expected outcome: an aged-and-uncited fixture is proposed with a default; recent or cited docs are excluded; a per-item override is honored and its recorded `status` reflects the accepted choice.
  - Execution state: pending
- [ ] E-05 add the miscategorization flag: detect a doc in `archive/` that IS cited (via its frontmatter `consumed-by` and/or a repo `\b<id6>\b` scan using Order 04's detector) and report it ("should be reference?").
  - Depends on: E-02
  - Expected outcome: an archived-but-cited fixture is flagged by the named detection mechanism.
  - Execution state: pending
- [ ] E-06 refresh INDEX after any archival move (reference stays in the most-recent-N window; archive excluded).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: an archived doc leaves INDEX.md; a reference doc remains.
  - Execution state: pending
- [ ] E-07 add `tests/test_research_archive.py` (promote-to-reference shard move id/cites intact; targeted archive; aged-uncited sweep + preview; miscategorization flag; INDEX refresh); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05, E-06
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Contract: state vocab + shard-path constants from Order 01; recency/last-touched from Order 03's index; reference-updater + dangling detector from Order 04.
- Determinism: archival is ALWAYS on invocation, never index-time or background (spec 4.10); mirror the dry-run/preview + `--apply` safety pattern; moves are atomic tracked renames.
- The reference-vs-archive judgment is curation, not derivable; the tool DEFAULTS (cited -> reference; uncited+aged -> archive candidate), PROMPTS per item for accept/override, RECORDS the resulting `status`, and FLAGS miscategorization. Citation is detected via `consumed-by` and/or Order 04's `\b<id6>\b` detector.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C5-1 | HIGH | Medium | scale | glance size | Cold items must leave the hot area or the glance/tree renoise at hundreds of files. | spec 2, 4.9 |
| C5-2 | MEDIUM | Low | safety | surprise | Archival must be deliberate + previewed; no silent moves. | spec 4.10 |
| C5-3 | MEDIUM | Medium | curation | correctness | reference vs archive is a recorded judgment; tool must default + flag, not silently guess. | spec 4.5 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.5/4.9 | Shard layout + a `status` transition helper: set `status` in frontmatter AND move the file to the matching location (`reference/YYYYMM-Www/`, `archive/YYYYMM-Www/`, or hot root for intake/active), keeping `<id6>`; reuse Order 04's reference-update on move. | `agent_workflows/research_archive.py` (new), `agent_workflows/research_cmd.py` | Medium | E-02 |
| 2 | 4.10 | `aw archive [research] <set-id|doc-id>`: deep-shelve target(s) to `archive/YYYYMM-Www/`, dry-run/preview default + `--apply`. | `agent_workflows/research_cmd.py` | Medium | E-03 |
| 3 | 4.10/4.5 | Bare `aw archive [research]`: select aged-and-uncited candidates, PREVIEW each with a default classification, accept/override PER ITEM, move on `--apply`, record the resulting `status`. | `agent_workflows/research_archive.py` | Medium | E-04 |
| 4 | 4.5 | Miscategorization flag: a doc in `archive/` that IS cited (via `consumed-by`/Order-04 detector) is reported ("should be reference?"). | `agent_workflows/research_archive.py` | Low | E-05 |
| 5 | 4.7 | After any archival move, refresh INDEX (reference stays in most-recent-N window; archive excluded). | `agent_workflows/research_cmd.py` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Classifying the existing research corpus | n/a | scope | Migration curation. | Order 06 |
| Applying shards to plans/prompts | n/a | scope | Future adopters. | Order 07 TODO |

## Scope check

- Over-scope: none - state transitions + shards + archive verbs + refresh.
- Under-scope: MUST keep archival deliberate/previewed, keep `<id6>`+cites intact on move, and keep archive out of the hot glance while reference stays in.

## Required tests / validation

`tests/test_research_archive.py`: promote-to-reference shard move (id/cites intact, tracked rename); targeted archive; aged-and-uncited sweep selection + preview + per-item accept/override + recorded `status`; miscategorization flag (via `consumed-by`/Order-04 detector); INDEX refresh (archive out, reference in). Run it + full `python3 -m unittest discover -s tests -t .`; PASTE both (the `Ran N tests ... OK` summary). Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md`: the four states, weekly shards, the archive verbs + preview safety, and the reference-vs-archive curation rule.

## Open questions

### OQ-01: default sweep age and uncited requirement

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: RESOLVED at review (2026-08-07). The bare-sweep default selector is aged (older than two weeks) AND uncited (a deliberate safety tightening over spec 4.10's bare "aged" default, so a still-referenced doc is never auto-proposed); always previewed with a per-item accept/override before any move.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01+03 in `executed/`; confirm the tool halts when their symbols are absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a promote-to-reference move showing the correct week shard + unchanged id + updated cite; confirm the move is a tracked git rename (R).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: confirm targeted archive previews then moves on `--apply`; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm aged-and-uncited is selected, recent/cited excluded, the per-item preview with a default is shown, a per-item override is honored, and the resulting `status` is recorded in frontmatter; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm an archived-but-cited doc is flagged via the named mechanism (`consumed-by` and/or Order 04's detector); cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: confirm an archived doc leaves INDEX.md and a reference doc remains; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m unittest tests.test_research_archive -v` + the full-suite `Ran N tests ... OK` summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 03; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (states/shards/archive verbs only; no corpus migration). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
