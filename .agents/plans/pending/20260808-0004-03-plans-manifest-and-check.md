# IPD: plans manifest + browse-by-Set + `--check` (Set `plans-adopter`, Order 3)

- Date: 2026-08-08
- Kind: child
- Concern: make "what plans did we do about X?" answerable at a glance by surfacing the existing `Set:` grouping in a generated manifest, and prevent the filesystem and the manifest from silently diverging via a `--check` drift gate.
- Scope: `aw plans index [--check]` building `INDEX.json` (every plan) + a browse-by-`Set:` human view bounded to the 40 most-recent Sets; `--check` fails on drift (missing/invalid `Id`, name-vs-metadata mismatch, stale generated view, dangling plan citation). Consumes the Order-01 core and Order-02 `Id`; complements (does not replace) the existing `STATUS.md`. No rename, no shards, no migration. Requires Orders 01, 02.
- Status: reviewed
- Set: plans-adopter
- Order: 3
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the browse-by-topic payoff. Authored from spec `20260808-0004-01` Section 4.4 + OQ5.
- 2026-08-08 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-003/D4: the plans manifest scan MUST be recursive so sharded plans are visible (plans.py:scan is non-recursive and would miss them); added the plans.py/STATUS.md recursion reconciliation as a tracked follow-up.
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

`aw plans index` regenerates `INDEX.json` (all plans, all fields incl. disposition + Set + Order + Id + resolved path) and a browse-by-`Set:` human view (each Set lists its members in `Order`; Sets ordered by most-recent activity; bounded to the 40 most-recent Sets, the rest in JSON); `aw plans index --check` fails on drift. This turns the plans corpus into a topic-browsable, drift-checked manifest using the grouping metadata plans already carry.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: manifest generation

- [ ] E-01 confirm Orders 01+02 are executed (`artifact_core` + the required plan `Id`) and their symbols are present, else STOP.
  - Depends on: none
  - Expected outcome: the core + `Id` support are importable; if absent the tool halts before generating.
  - Execution state: pending
- [ ] E-02 add `aw plans index`: scan `.agents/plans/**` plan metadata (disposition from the top-level dir; `Id`/`Set`/`Order`/`Status`/`Kind` from the block) and build `INDEX.json` (every plan, all fields, resolved current path) as a pure deterministic function of the plans + their metadata. The scan MUST be RECURSIVE (`rglob`) so plans that Order 05 moves into `<disposition>/YYYYMM-Www/` weekly shards are visible; the disposition is the TOP-LEVEL dir even when a plan sits in a shard subdir. (Note: `plans.py:scan` uses a non-recursive `glob("*.md")` and would MISS sharded plans; `plans_index` uses its own recursive scan and does not inherit that limitation. Reconciling `plans.py`/`STATUS.md` recursion is tracked as a follow-up, see Deferred.)
  - Depends on: E-01
  - Expected outcome: the JSON contains every plan (including any in a shard subdir) with correct fields + top-level disposition; regenerating twice is byte-identical.
  - Execution state: pending
- [ ] E-03 generate the browse-by-`Set:` human view: group by `Set` (members in `Order`), Sets ordered by most-recent activity, bounded to the 40 most-recent Sets (configurable via a core constant / `--limit`); ungrouped plans (no `Set`) shown in a singleton band; a "do not edit" header. Complement `STATUS.md`, do not replace it.
  - Depends on: E-02
  - Expected outcome: the view groups by Set, honors the bound, and lists members in Order.
  - Execution state: pending

### Task group 2: query, drift, tests

- [ ] E-04 add `aw plans find --id|--set|--status|--disposition`: query the manifest and print terse rows (token-cheap; no corpus read).
  - Depends on: E-02
  - Expected outcome: each filter returns the expected plans from a fixture set.
  - Execution state: pending
- [ ] E-05 add `--check`: exit nonzero on drift, reusing the Order-01 core drift shape + the core dangling detector; the four classes are (a) missing/invalid `Id`, (b) name-vs-metadata mismatch (once plans are clustered; pre-migration a non-clustered name is NOT a mismatch), (c) stale generated view (byte-compare), (d) dangling plan citation. Provide `--agent` output + 0/1/2 exit codes.
  - Depends on: E-02, E-03
  - Expected outcome: a clean tree passes; each drift class fails; `--agent` emits machine-readable records.
  - Execution state: pending
- [ ] E-06 add `tests/test_plans_index.py` (JSON completeness; Set-grouped view + bound + Order; `find` filters; `--check` clean-vs-each-drift-class; determinism); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `plans.py` already scans `.agents/plans/**` and renders a disposition-grouped `STATUS.md` (`render_status_index`); this child ADDS a Set-grouped manifest + JSON + `--check`, it does not replace `STATUS.md`. Reuse `plans.py`'s record TYPES where sensible, but NOT its scan: `plans.py:scan` uses a non-recursive `glob("*.md")` (`plans.py:165`) and cannot see plans inside `<disposition>/YYYYMM-Www/` shards; `plans_index` MUST scan recursively (`ipd_lint._iter_plan_files` already uses `rglob`, the precedent). Deriving disposition from the TOP-LEVEL dir regardless of shard depth.
- The drift/`--check` shape, dangling detector, and determinism come from `artifact_core` (Order 01); `Id` comes from `ipd_schema` (Order 02). No fork.
- Pre-migration, plan filenames are still the timestamp stem; the name-vs-metadata drift class only applies to CLUSTERED names, so it must not false-positive on un-migrated plans.
- Test runner: stdlib `unittest`, NOT pytest.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C3-1 | HIGH | Low | human+agent | browse | The existing `Set:` grouping is invisible/unindexed; a manifest surfaces it cheaply. | spec 1, 2, 4.4 |
| C3-2 | MEDIUM | Low | integrity | drift | The FS and manifest must not diverge -> `--check` reusing the core gate. | spec 4.4 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.4 | `aw plans index`: build `INDEX.json` from plan metadata (pure, deterministic) | `agent_workflows/plans_index.py` (new), `agent_workflows/cli.py` | Low | E-02 |
| 2 | 4.4/OQ5 | Browse-by-Set view, bounded to 40 recent Sets, members in Order | `agent_workflows/plans_index.py` | Low | E-03 |
| 3 | 4.4 | `aw plans find` over the manifest | `agent_workflows/plans_index.py`, `agent_workflows/cli.py` | Low | E-04 |
| 4 | 4.4 | `--check` (core drift shape + dangling detector); `--agent` + 0/1/2 | `agent_workflows/plans_index.py` | Medium | E-05 |
| 5 | 4.4 | tests | `tests/test_plans_index.py` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Renaming plans to cluster by Set | n/a | scope | Order 04 (regroup) + Order 06 (migration). | Orders 04, 06 |
| Moving plans into shards | n/a | scope | Order 05. | Order 05 |
| Wiring `--check` into a pre-commit hook | usability | Hook-less per spec OQ4; the workflows carry the obligation. | Deferred hook follow-up |
| Making `plans.py:scan`/`STATUS.md` recursive so the disposition board also sees sharded plans | functionality | `plans_index` scans recursively so the manifest is correct; the legacy `STATUS.md` board would under-count sharded plans until `plans.py:scan` is made recursive too. Bounded, but touches the existing board; scoped as a small follow-up rather than expanded here. | A later small fix (or folded into Order 05) |

## Scope check

- Over-scope: none - generate + query + check.
- Under-scope: MUST produce a complete `INDEX.json`, a bounded Set-grouped human view, and a drift gate that reuses the core (no fork) and does not false-positive on un-migrated names.

## Required tests / validation

`tests/test_plans_index.py`: JSON completeness; Set-grouped view (members in Order, bound honored, singleton band); `find` filters; `--check` clean vs each of the four drift classes (incl. dangling via the core detector, and NO false positive on an un-migrated timestamp-stem name); determinism (regenerate twice, byte-identical). Run it + the full suite `python3 -m unittest discover -s tests -t .`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

Document `aw plans index`/`find`/`--check` in `.agents/plans/README.md` (the plans-area README): the manifest tiers, the browse-by-Set view + bound, the commit policy for `INDEX.json`, and the `--check` gate. The `STATUS.md` note is updated to point at the new Set-grouped view as its complement.

## Open questions

### OQ-01: commit `INDEX.json` vs generate-on-demand

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: COMMIT `INDEX.json` and the Set-grouped view (as research does, D123) so a fresh clone and a weak agent have them without running the tool; keep them fresh via `--check`. This mirrors the research decision for consistency.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01+02 in `executed/` and their symbols importable; confirm the tool halts when they are absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a JSON snippet showing all fixture plans + fields (incl. disposition/Set/Order/Id); confirm a plan placed in a `<disposition>/YYYYMM-Www/` shard subdir IS included with its top-level disposition (recursive scan); confirm regenerating twice is byte-identical.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the Set-grouped view showing grouping by Set, members in Order, the 40-Set bound honored, and a singleton band for Set-less plans.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm each `find` filter (`--id`/`--set`/`--status`/`--disposition`) returns the expected plans; cite test output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm a clean tree passes and EACH of the four drift classes fails; confirm an un-migrated timestamp-stem name is NOT flagged as a name-vs-metadata mismatch; paste a sample `--agent` record + exit codes 0/1/2.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m unittest tests.test_plans_index -v` + the full-suite `Ran N tests ... OK` summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds scope (index/find/check only; no file moves/renames). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
