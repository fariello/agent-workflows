# IPD: migrate existing plans onto the clustering grammar (Set `plans-adopter`, Order 6)

- Date: 2026-08-08
- Kind: child
- Concern: apply the convention to this repo's existing plan corpus (the dogfood): assign every plan a stable `Id`, rename all executed and pending plans to the Set-clustering grammar, rewrite the three plan-citation forms, and regenerate the manifest, so plans cluster by topic in the tree with all citations preserved.
- Scope: a one-time, reviewed data migration of `.agents/plans/**` using the Order 02 to 05 tools. The clustering grammar is `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` (OQ1). Requires Orders 01 to 05 executed; if their tools are absent, STOP. MANDATORY dry-run mapping + STOP-for-human-review before any apply.
- Status: executed
- Set: plans-adopter
- Order: 6
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 7qx7ys

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the accepted one-time cost that proves the convention on real data. Authored from spec `20260808-plansadopt-01-qkc93l-shared-artifact-core` Section 4.7 + 4.8.
- 2026-08-08 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-002/D2 (HIGH): Id validity on migrated executed plans is verified via `aw plans index --check` (checks all dispositions), NOT `aw ipd lint` (skips terminal-dir plans as legacy); PR-004/D5: bare-stem rewrite must not touch spec-only stems.
- 2026-08-08 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): produced the dry-run mapping and STOPPED for human review across two rounds (which refined the set-id readability + the `Set: <terse> (<descriptive>)` format); on approval migrated 122 plans onto the clustering grammar (Id backfill, terse-set-id + descriptive metadata, tracked git renames, 287 citations rewritten across ~40 files, spec-only stems untouched, INDEX regenerated). Excluded the 2 other-agent + 3 in-flight plans-adopter plans. Reconciled the stale plan-name normalizer/test to accept the clustering grammar. Product commit 05c4deb; full suite green (Ran 673 tests OK, skipped=1); `aw plans index --check` clean but for the 2 excluded strays; leak-clean; no em/en dashes in authored files. All E-01..E-06 performed and V-01..V-06 pass.
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

Every plan (executed + pending; the exact count is re-counted at execution) ends up: carrying a stable `- Id:`, named to the clustering grammar `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`, grouped by its existing `Set:`/`Order:` (Set-less plans as singletons), with all in-repo citations updated across the three forms, and the manifest regenerated. Moves are tracked git renames; the plan BODY and workflow history stay verbatim (only the name and the added `Id` line change). `aw plans index --check` passes clean afterward. Spec Section 4.7 + 4.8.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: prepare and STOP-gate

- [x] E-01 confirm Orders 01 to 05 are executed and their tools are present, else STOP; then re-count the migratable plans (executed + pending; exclude non-plan files like `STATUS.md`/`INDEX.*`/`README.md`) and record that exact before-total.
  - Depends on: none
  - Expected outcome: the Order 02 to 05 tools are usable; a re-counted before-total is recorded (do NOT rely on a hardcoded number).
  - Execution state: performed
- [x] E-02 produce a full DRY-RUN migration mapping (every migratable plan: old path -> assigned `Id` + new clustering name + Set/Order + disposition) AND the citation-rewrite diff for all THREE forms (full-name, bare-stem, range), verify 1:1 completeness against the E-01 before-total, then STOP for human review BEFORE any apply.
  - Depends on: E-01
  - Expected outcome: a reviewable mapping + citation diff accounting for every plan and every citation, with no gaps/dupes; nothing moved or rewritten yet.
  - Execution state: performed

### Task group 2: apply

- [x] E-03 assign each plan a collision-checked `- Id:` (backfill the metadata block; keep body + workflow history verbatim).
  - Depends on: E-02
  - Expected outcome: every migratable plan has a valid unique `Id`. NOTE: `aw ipd lint` treats terminal-dir (executed/superseded/not-executed) plans as `legacy/not evaluated` and does NOT check their metadata, so Id validity on the migrated corpus is verified via `aw plans index --check` (Order 03, which checks Id on ALL plans regardless of disposition), NOT via `aw ipd lint`.
  - Execution state: performed
- [x] E-04 rename each plan to the clustering grammar via the Order-04 `set-assign --rename`/`mv` (tracked git renames); Set-less plans become singletons keyed on their slug.
  - Depends on: E-03
  - Expected outcome: plans cluster by Set in the name-sorted tree; git tracks moves as renames (R), not delete+add.
  - Execution state: performed
- [x] E-05 rewrite all in-repo citations across the three forms via the Order-04 reference updater + the old-stem->new-name map; a bare stem is rewritten ONLY when it maps to a plan in the migration table (a spec-only stem sharing the `YYYYMMDD-HHMM-NN` grammar is left untouched); report + resolve danglers.
  - Depends on: E-04
  - Expected outcome: the dangling-cite report is empty after `--apply`; sample cites of each form resolve; a spec-only bare stem is confirmed NOT rewritten.
  - Execution state: performed
- [x] E-06 regenerate `INDEX.json` + the browse-by-Set view and run `aw plans index --check`; paste the check result, dangling report, suite summary, and before/after count.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: `aw plans index --check` exits clean; the browse-by-Set view groups the corpus; the full suite stays green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Use the Order 02 to 05 tools; do NOT hand-edit names/metadata where a tool exists.
- Existing Set cohorts to preserve (verified in the corpus): `install-safety-and-ownership` (7), `ipd-structure` (7), `research-org` (8), `ipd-dual-checklist-convention` (4), `untrack-workflow-artifacts` (4), `plans-adopter` (this Set), and others; Set-less plans become singletons. Re-derive the exact cohorts at execution.
- Plans are cited THREE ways: full filename, bare `YYYYMMDD-HHMM-NN` stem, and range shorthand; the migration builds the old-stem->new-name map and rewrites all three (Order 04).
- HAZARD (verified at review): the bare-stem `YYYYMMDD-HHMM-NN` grammar is SHARED with `.agents/docs/specs/` filenames (e.g. `20260808-plansadopt-01-qkc93l-shared-artifact-core` is BOTH a plan and a spec). A bare-stem rewrite MUST disambiguate a plan citation from a spec citation (resolve the stem to a plan `Id` only when it maps to a plan in the migration table; leave spec-only stems untouched). The dry-run diff (E-02) surfaces every bare-stem rewrite for human review to catch a mis-hit; do NOT blind-rewrite bare stems.
- The plan BODY and append-only workflow history are IMMUTABLE (spec 4.8): only the filename and the added `Id` line change. Moves are tracked git renames so history is preserved.
- Migratable = plan `*.md` under a disposition dir; EXCLUDE `STATUS.md`, `INDEX.json`, `INDEX.md`, `README.md`, `.gitkeep`.
- Test runner: stdlib `unittest`, NOT pytest.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C6-1 | HIGH | Medium | maintainer | dogfood | The convention is unproven until applied to the real corpus; migration is the proof + the browse-by-topic value. | spec 4.7 |
| C6-2 | HIGH | Medium-High | integrity | citations | The bare-stem and range citation forms are the risky rewrite; a STOP-gated dry-run diff + audit is mandatory. | Order 04 C4-2 |
| C6-3 | MEDIUM | Medium | history | immutability | Executed plan bodies/history must stay verbatim; only names + the Id line change. | spec 4.8 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.7 | Re-count + full dry-run mapping + citation diff; STOP for review | (none written) | Low | E-02 |
| 2 | 4.7 | Backfill `Id` on every plan | `.agents/plans/**` | Medium | E-03 |
| 3 | 4.7 | Rename all plans to the clustering grammar (tracked renames) | `.agents/plans/**` | Medium | E-04 |
| 4 | 4.7 | Rewrite the three citation forms; resolve danglers | `DECISIONS.md`, `.agents/plans/**`, `.agents/docs/**`, `TODO.md`, README/ARCHITECTURE | Medium-High | E-05 |
| 5 | 4.4 | Regenerate INDEX; `aw plans index --check` clean | `.agents/plans/INDEX.*` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Migrating prompts/comms/walkthroughs | n/a | scope | Future adopters. | Order 07 TODO |
| Rewriting git history of old plan names | complexity | Destructive; content preserved; not needed. | Not planned |
| Moving migrated plans into weekly shards | n/a | scope | Initial migration clusters by Set at the disposition-dir root; deliberate sharding is a later `aw plans archive` act. | Order 05 verb, post-migration |

## Scope check

- Over-scope: none - a bounded migration of the existing plan tree + citation updates.
- Under-scope: MUST account for EVERY migratable plan, preserve EVERY citation (all three forms), keep bodies/history verbatim, and end with a clean `aw plans index --check`.

## Required tests / validation

Migration is data, validated by the tools: after execution, `aw plans index --check` exits clean; the dangling-cite report is empty; a spot-check of >=3 previously-cited plans (one per citation form: full-name, bare-stem, range) shows their cites still resolve; a sample of moved plans shows as git renames (`git status`/`git log --follow` reports `R`, not delete+add); the full suite `python3 -m unittest discover -s tests -t .` stays green (PASTE the `Ran N tests ... OK` summary). Record a before/after plan count (every migratable plan accounted for). Leak-clean; no em/en dashes in authored Markdown.

## Spec / documentation sync

Regenerate `.agents/plans/INDEX.*` and refresh `STATUS.md` from the migrated state. No spec change (this executes the spec).

## Open questions

### OQ-01: singleton set-id derivation for Set-less plans

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: a plan with no `Set:` becomes a singleton whose `<set-id>` is derived by kebab-normalizing its slug (mirroring the research migration's singleton rule); its `Id` is the stable handle regardless. The full dry-run mapping (E-02) surfaces every derived set-id for review before apply.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: cite Orders 01 to 05 in `executed/` and paste the re-counted migratable-plan before-total (executed + pending, exclusions applied).
  - Observed evidence: Orders 01-05 are executed (`.agents/plans/executed/20260808-plansadopt-01..05-*`). Re-count: 127 plan files total; excluded = the 2 other-agent pending plans + the 3 still-in-flight plans-adopter plans (00/06/07, mid-lifecycle); migrated = 122 (120 executed + 2 not-executed). The 4 already-executed plans-adopter members (01-05) were included and clustered as `plansadopt`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the full dry-run mapping (old path -> Id + new name + Set/NN) and the citation-rewrite diff; confirm the row count equals the E-01 before-total with no gaps/dupes and that nothing was moved/rewritten before review.
  - Observed evidence: the full dry-run mapping (81 set-ids + 122-row old->new table + citation impact: 287 occurrences across ~40 files incl. 66 in DECISIONS.md, 5 in TODO.md) was produced and reviewed with the human across two STOP-gate rounds BEFORE any apply; the human approved. Row count 122 == the migratable before-total. Two STOP-gate refinements resulted from the review (terse readable set-ids; the `Set: <terse> (<descriptive>)` format). Nothing moved until `--apply`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: confirm EVERY migratable plan has a valid unique `Id` via `aw plans index --check` (which validates Id on all dispositions incl. `executed/`); paste the check output showing no missing/invalid-Id drift + a count of plans carrying an Id. Do NOT rely on `aw ipd lint` (it skips terminal-dir plans as legacy).
  - Observed evidence: `aw plans index --check --agent` reports zero `id-missing`/`id-invalid` on the 122 migrated plans (the only 2 remaining `id-missing` are the intentionally-excluded other-agent stray pending plans). All migrated plans carry a valid `- Id:` (10 pre-metadata-convention legacy plans, which lack an `- Author:` line, had the Id backfilled after the last metadata bullet). Validation is via `aw plans index --check` (not `aw ipd lint`, which skips terminal-dir plans as legacy), as designed.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste a migrated cohort (shared Set, ordered NN, clustering names) and `git status`/`git log --follow` for a sample showing renames (R), not delete+add.
  - Observed evidence: the `ipdstruct` cohort clustered as `20260802-ipdstruct-00..06-<id6>-<slug>.md` (shared date + set + ordered NN); `git status --porcelain` shows 122 `R` (rename) entries and 0 delete+add for moved plans (history preserved). `Set:` metadata carries `ipdstruct (ipd-structure)`.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the (empty) dangling-cite report and >=3 resolved sample cites, one per citation form (full-name, bare-stem, range); AND confirm a spec-only bare stem sharing the `YYYYMMDD-HHMM-NN` grammar (e.g. an `.agents/docs/specs/` id that is not a plan) was NOT rewritten.
  - Observed evidence: `aw plans index --check` reports ZERO `dangling-citation`. Sample resolved rewrites: full-name + bare-stem + range cites of `20260802-1944-00..06` were rewritten to `20260802-ipdstruct-00..06-...` in DECISIONS.md (old stem count 0, new stem present). Spec-only guard: `20260726-1340-01-ipd-spec.md` (a spec whose stem `20260726-1340-01` shares the grammar) was NOT renamed and its 3 bare-stem cites in DECISIONS survive intact.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `aw plans index --check` = clean; confirm the browse-by-Set view groups the corpus; paste the full-suite summary; the before/after plan count reconciles (all accounted for); leak-clean.
  - Observed evidence: `aw plans index --check --agent` is clean except the 2 excluded stray plans (0 stale-index, 0 dangling, 0 name-mismatch). `INDEX.md` groups the corpus by Set (browse-by-topic). Full suite `python3 -m unittest discover -s tests -t .` -> `Ran 673 tests in 153.136s / OK (skipped=1)` (incl. the reconciled `normalize_plan_names` conformance test). Before/after: 122 migrated in, all present + indexed (INDEX shows 127 total incl. the 5 excluded). `aw sanitize --agent` exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01 to 05; if absent, STOP. The dry-run mapping + citation diff (E-02) MUST be reviewed by the human BEFORE any apply. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including a clean `aw plans index --check` and an empty dangling report); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files (the plan tree + the citation-bearing files it updates), path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown (plan bodies stay verbatim). STOP and report if execution exceeds scope (plan migration + its citations only). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
