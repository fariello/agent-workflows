# IPD: plans weekly shards + archival (Set `plans-adopter`, Order 5)

- Date: 2026-08-08
- Kind: child
- Concern: tame the flat, unbounded terminal disposition dirs (measured pain: 116 files in `executed/`) by adding weekly `YYYYMM-Www/` cold shards inside every terminal dir, with a deliberate, tool-invoked archival verb (never a background side effect).
- Scope: weekly shards inside `executed/`/`superseded/`/`not-executed/` (OQ3); `aw plans archive` (targeted + a deliberate aged sweep with preview); INDEX refresh after moves. `pending/`/`reusable/` stay flat. Consumes the Order-01 core (shard math, atomic move), Order-03 manifest, Order-04 reference-update. No bulk migration (06). Requires Orders 01, 03, 04.
- Status: reviewed
- Set: plans-adopter
- Order: 5
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the scale mechanism. Authored from spec `20260808-0004-01` Section 4.6 + OQ3.
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

Give the terminal disposition dirs weekly `YYYYMM-Www/` cold shards and an `aw plans archive` verb (targeted deep-shelve of a plan/Set, plus a bare aged sweep with a per-item preview) so aged plans leave the flat top of `executed/`/`superseded/`/`not-executed/` while `pending/`/`reusable/` stay flat. Refresh the manifest after any move. Moves keep the plan's `Id` and are tracked git renames.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: shard layout + move helper

- [ ] E-01 confirm Orders 01+03+04 are executed and their symbols are present, else STOP.
  - Depends on: none
  - Expected outcome: the core + manifest + reference-update symbols are importable; if absent the tool halts before moving files.
  - Execution state: pending
- [ ] E-02 add the shard-move helper: move a terminal plan from its disposition-dir root into `<disposition>/YYYYMM-Www/` (weekly shard from the plan's date, via the core shard math) as an atomic tracked `git mv`, keeping `Id`; reuse Order 04's reference-update so any full-path cite is rewritten (id/bare-stem cites are unaffected by a dir-only move).
  - Depends on: E-01
  - Expected outcome: a terminal plan moves into the correct week shard of its disposition dir; id + cites intact.
  - Execution state: pending

### Task group 2: archive verbs, refresh, tests

- [ ] E-03 add `aw plans archive <id6|set-id>`: deep-shelve the target plan (or whole Set) into the appropriate `<disposition>/YYYYMM-Www/` shard, dry-run/preview default + `--apply`.
  - Depends on: E-02
  - Expected outcome: a named plan/Set moves into its shard on `--apply`, previewed otherwise.
  - Execution state: pending
- [ ] E-04 add bare `aw plans archive`: select terminal plans older than a default age still sitting at a disposition-dir root, PREVIEW the list, and move on `--apply`. Deliberate and on-invocation only; never a background/index-time side effect.
  - Depends on: E-02
  - Expected outcome: aged flat-root terminal plans are selected; recent ones excluded; the preview is shown before any move.
  - Execution state: pending
- [ ] E-05 refresh the manifest (Order 03) after any archival move so the browse-by-Set view and `INDEX.json` reflect the new shard paths.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: an archived plan's resolved path in the manifest updates; `index --check` stays clean.
  - Execution state: pending
- [ ] E-06 add `tests/test_plans_archive.py` (shard-move id/cites intact + correct week shard + tracked rename; targeted archive; aged sweep + preview; INDEX refresh); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Disposition dirs are the coarse lifecycle; the shard layer is fine-grained cold storage WITHIN each terminal dir. `pending/`/`reusable/` (hot/standing) stay flat.
- Shard math (`shard_for_date`, `YYYYMM-Www`) and the atomic move/`git mv` come from the Order-01 core; the reference-update from Order 04; the manifest refresh from Order 03. No fork.
- A dir-only move (root -> shard within the same disposition dir) changes the plan's PATH but not its filename; so full-path citations may need rewriting, but bare-stem/id citations are unaffected. Archival is ALWAYS deliberate/on-invocation (mirrors `aw archive` for research, spec 4.10).
- Test runner: stdlib `unittest`, NOT pytest.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C5-1 | HIGH | Medium | scale | glance size | 116 flat files in `executed/` renoise the tree; cold plans must leave the flat root. | spec 1, 2, 4.6 |
| C5-2 | MEDIUM | Low | safety | surprise | Archival must be deliberate + previewed; no silent/background moves. | spec 4.6, 4.10 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.6 | Shard-move helper (root -> `<disposition>/YYYYMM-Www/`, atomic git mv, keep Id, reuse ref-update) | `agent_workflows/plans_archive.py` (new), `agent_workflows/cli.py` | Medium | E-02 |
| 2 | 4.6 | `aw plans archive <id6|set-id>` targeted deep-shelve, preview + `--apply` | `agent_workflows/plans_archive.py` | Medium | E-03 |
| 3 | 4.6 | Bare `aw plans archive` aged sweep + preview | `agent_workflows/plans_archive.py` | Medium | E-04 |
| 4 | 4.4 | INDEX refresh after moves | `agent_workflows/plans_archive.py` | Low | E-05 |
| 5 | 4.6 | tests | `tests/test_plans_archive.py` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Bulk migrating the existing corpus into shards | n/a | scope | The migration decides initial shard placement at scale. | Order 06 |
| Sharding `pending/`/`reusable/` | n/a | scope | Hot/standing tiers stay flat (OQ3). | N/A |

## Scope check

- Over-scope: none - shard layout + archive verbs + refresh.
- Under-scope: MUST keep archival deliberate/previewed, keep `Id`+cites intact on move, shard all THREE terminal dirs, and keep `pending/`/`reusable/` flat.

## Required tests / validation

`tests/test_plans_archive.py`: shard-move (correct `YYYYMM-Www` shard for the plan's date, unchanged Id, tracked git rename, full-path cite rewritten); targeted `aw plans archive <id|set>`; bare aged sweep (aged selected, recent excluded, preview shown); INDEX refresh (archived plan's path updates, `index --check` clean). Run it + the full suite `python3 -m unittest discover -s tests -t .`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/plans/README.md`: the terminal-dir shard layout, the `aw plans archive` verb + preview safety, and that `pending/`/`reusable/` stay flat.

## Open questions

### OQ-01: default sweep age for terminal plans

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: the bare-sweep default age mirrors the research archival default (older than two weeks), always previewed before any move; configurable. Confirm the exact age at execution; if it changes, only this child changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01+03+04 in `executed/`; confirm the tool halts when their symbols are absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a shard-move showing the correct week shard within the disposition dir + unchanged Id; confirm the move is a tracked git rename and any full-path cite was rewritten.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: confirm targeted `aw plans archive <id|set>` previews then moves on `--apply`; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm the bare sweep selects aged flat-root terminal plans, excludes recent ones, and shows a preview before moving; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm an archived plan's manifest path updates and `aw plans index --check` stays clean after the move; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m unittest tests.test_plans_archive -v` + the full-suite `Ran N tests ... OK` summary; leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 03, 04. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds scope (shards + archive verbs only; no bulk migration). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
