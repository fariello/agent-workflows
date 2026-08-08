# IPD: migrate existing plans onto the clustering grammar (Set `plans-adopter`, Order 6)

- Date: 2026-08-08
- Kind: child
- Concern: apply the convention to this repo's existing plan corpus (the dogfood): assign every plan a stable `Id`, rename all executed and pending plans to the Set-clustering grammar, rewrite the three plan-citation forms, and regenerate the manifest, so plans cluster by topic in the tree with all citations preserved.
- Scope: a one-time, reviewed data migration of `.agents/plans/**` using the Order 02 to 05 tools. The clustering grammar is `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` (OQ1). Requires Orders 01 to 05 executed; if their tools are absent, STOP. MANDATORY dry-run mapping + STOP-for-human-review before any apply.
- Status: reviewed
- Set: plans-adopter
- Order: 6
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the accepted one-time cost that proves the convention on real data. Authored from spec `20260808-0004-01` Section 4.7 + 4.8.
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

Every plan (executed + pending; the exact count is re-counted at execution) ends up: carrying a stable `- Id:`, named to the clustering grammar `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`, grouped by its existing `Set:`/`Order:` (Set-less plans as singletons), with all in-repo citations updated across the three forms, and the manifest regenerated. Moves are tracked git renames; the plan BODY and workflow history stay verbatim (only the name and the added `Id` line change). `aw plans index --check` passes clean afterward. Spec Section 4.7 + 4.8.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: prepare and STOP-gate

- [ ] E-01 confirm Orders 01 to 05 are executed and their tools are present, else STOP; then re-count the migratable plans (executed + pending; exclude non-plan files like `STATUS.md`/`INDEX.*`/`README.md`) and record that exact before-total.
  - Depends on: none
  - Expected outcome: the Order 02 to 05 tools are usable; a re-counted before-total is recorded (do NOT rely on a hardcoded number).
  - Execution state: pending
- [ ] E-02 produce a full DRY-RUN migration mapping (every migratable plan: old path -> assigned `Id` + new clustering name + Set/Order + disposition) AND the citation-rewrite diff for all THREE forms (full-name, bare-stem, range), verify 1:1 completeness against the E-01 before-total, then STOP for human review BEFORE any apply.
  - Depends on: E-01
  - Expected outcome: a reviewable mapping + citation diff accounting for every plan and every citation, with no gaps/dupes; nothing moved or rewritten yet.
  - Execution state: pending

### Task group 2: apply

- [ ] E-03 assign each plan a collision-checked `- Id:` (backfill the metadata block; keep body + workflow history verbatim).
  - Depends on: E-02
  - Expected outcome: every migratable plan has a valid unique `Id`; `aw ipd lint` Id check passes on each.
  - Execution state: pending
- [ ] E-04 rename each plan to the clustering grammar via the Order-04 `set-assign --rename`/`mv` (tracked git renames); Set-less plans become singletons keyed on their slug.
  - Depends on: E-03
  - Expected outcome: plans cluster by Set in the name-sorted tree; git tracks moves as renames (R), not delete+add.
  - Execution state: pending
- [ ] E-05 rewrite all in-repo citations across the three forms via the Order-04 reference updater + the old-stem->new-name map; report + resolve danglers.
  - Depends on: E-04
  - Expected outcome: the dangling-cite report is empty after `--apply`; sample cites of each form resolve.
  - Execution state: pending
- [ ] E-06 regenerate `INDEX.json` + the browse-by-Set view and run `aw plans index --check`; paste the check result, dangling report, suite summary, and before/after count.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: `aw plans index --check` exits clean; the browse-by-Set view groups the corpus; the full suite stays green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Use the Order 02 to 05 tools; do NOT hand-edit names/metadata where a tool exists.
- Existing Set cohorts to preserve (verified in the corpus): `install-safety-and-ownership` (7), `ipd-structure` (7), `research-org` (8), `ipd-dual-checklist-convention` (4), `untrack-workflow-artifacts` (4), `plans-adopter` (this Set), and others; Set-less plans become singletons. Re-derive the exact cohorts at execution.
- Plans are cited THREE ways: full filename, bare `YYYYMMDD-HHMM-NN` stem, and range shorthand; the migration builds the old-stem->new-name map and rewrites all three (Order 04).
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

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01 to 05 in `executed/` and paste the re-counted migratable-plan before-total (executed + pending, exclusions applied).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the full dry-run mapping (old path -> Id + new name + Set/NN) and the citation-rewrite diff; confirm the row count equals the E-01 before-total with no gaps/dupes and that nothing was moved/rewritten before review.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: confirm EVERY migratable plan has a valid unique `Id` (paste `aw ipd lint` Id-check evidence on a sample + a count).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a migrated cohort (shared Set, ordered NN, clustering names) and `git status`/`git log --follow` for a sample showing renames (R), not delete+add.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the (empty) dangling-cite report and >=3 resolved sample cites, one per citation form (full-name, bare-stem, range).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `aw plans index --check` = clean; confirm the browse-by-Set view groups the corpus; paste the full-suite summary; the before/after plan count reconciles (all accounted for); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01 to 05; if absent, STOP. The dry-run mapping + citation diff (E-02) MUST be reviewed by the human BEFORE any apply. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including a clean `aw plans index --check` and an empty dangling report); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files (the plan tree + the citation-bearing files it updates), path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown (plan bodies stay verbatim). STOP and report if execution exceeds scope (plan migration + its citations only). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
