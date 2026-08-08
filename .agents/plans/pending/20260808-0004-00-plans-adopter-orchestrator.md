# IPD (ORCHESTRATOR): generalize the artifact-organization core and apply it to `.agents/plans/` (Set `plans-adopter`)

- Date: 2026-08-08
- Kind: orchestrator
- Concern: apply the shipped research-organization model (DECISIONS D123) to `.agents/plans/` per the approved companion spec `.agents/docs/specs/20260808-0004-01-artifact-organization-plans-adopter.spec.md`: extract an area-agnostic core, give plans a stable `Id`, surface the existing `Set:` grouping in a manifest, make Set regrouping/rename citation-safe, weekly-shard the terminal disposition dirs, and migrate the corpus onto a Set-clustering filename grammar, so a human and an agent can browse plans by topic at scale.
- Scope: ORCHESTRATOR for the ordered Set `plans-adopter`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It does NOT itself change files (each child does its own edits). Implementation is scoped to `plans/` (and the shared core); `prompts/`/`comms/`/`walkthroughs/` are named future adopters, not implemented.
- Status: to-review
- Set: plans-adopter
- Order: 0
- Highest E allocated: 09
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from the approved spec `20260808-0004-01-artifact-organization-plans-adopter.spec.md`. Split into a Set because the work spans a shared-core extraction, an `ipd_schema` metadata + linter change, a manifest surface, a regroup/rename tool, a shard/archival tool, a one-time corpus migration with citation rewriting, and framework scaffolding + decision updates, with clear dependency ordering.

## Goal

Deliver the plans-adopter end to end: extract the area-agnostic core shared with research; add a required stable `- Id:` to plan metadata (linter + scaffold/sync); build the plans manifest (`INDEX.json` + browse-by-Set view + `--check`); add the `aw plans set-assign`/`mv` regroup verb and the `aw plans archive` verb with weekly `YYYYMM-Www` shards in all terminal disposition dirs; migrate all plans onto the `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` clustering grammar with citations preserved; and wire scaffold + directives + prior-decision updates. Dogfood in this repo. Do not build the convention for `prompts/`/`comms/`/`walkthroughs/` yet (named future adopters).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

The orchestrator's execution leaves gate the children and run the whole-Set checks. They use the same stable E/V contract as every other actionable IPD.

- [ ] E-01 verify Child 01 (shared area-agnostic core) is executed and its own two checklists are verified.
  - Depends on: none
  - Expected outcome: `agent_workflows/artifact_core.py` exists (id6, shard math, dangling detector, manifest/`--check` shape, writing-safety); research imports it with no behavior change.
  - Execution state: pending
- [ ] E-02 verify Child 02 (`Id` in `ipd_schema` + linter + scaffold/sync) is executed after Child 01 and its own checklists are verified.
  - Depends on: E-01
  - Expected outcome: `- Id:` is a required, linter-validated plan metadata field; `aw ipd scaffold`/`sync` emit it.
  - Execution state: pending
- [ ] E-03 verify Child 03 (plans manifest + browse-by-Set + `--check`) is executed after Children 01 and 02 and its own checklists are verified.
  - Depends on: E-01, E-02
  - Expected outcome: `aw plans index [--check]` builds `INDEX.json` + a Set-grouped bounded view and fails on drift.
  - Execution state: pending
- [ ] E-04 verify Child 04 (regroup/rename verb) is executed after Children 01 through 03 and its own checklists are verified.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `aw plans set-assign`/`mv` (re)assign `Set:`/`Order:` and optionally rename to the clustering grammar, keeping `Id` and rewriting citations.
  - Execution state: pending
- [ ] E-05 verify Child 05 (shards + archival) is executed after Children 01, 03, and 04 and its own checklists are verified.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: weekly `YYYYMM-Www/` shards in `executed/`/`superseded/`/`not-executed/`; `aw plans archive` targeted + aged sweep with preview.
  - Execution state: pending
- [ ] E-06 verify Child 06 (one-time corpus migration) is executed after Children 01 through 05 and its own checklists are verified.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: all plans have an `Id`, are renamed to the clustering grammar as tracked renames, the three citation forms are rewritten, and `aw plans index --check` is clean.
  - Execution state: pending
- [ ] E-07 verify Child 07 (scaffold/directives/decisions) is executed after Children 01, 03, and 05 and its own checklists are verified.
  - Depends on: E-01, E-03, E-05
  - Expected outcome: installer scaffolds the terminal-dir shards; AGENTS.md pointer notes the `aw plans` grouping verbs; DECISIONS D124 + P-relevant + TODO edits are complete.
  - Execution state: pending
- [ ] E-08 run the cross-IPD validation.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: consistency, no-drift, dependency-correctness, and no-collision checks pass.
  - Execution state: pending
- [ ] E-09 run the final suite and repository dogfood checks and paste actual output.
  - Depends on: E-08
  - Expected outcome: the suite is green, leak-clean, no em/en dashes, and `aw plans index --check` is clean on this repo's migrated `plans/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260808-0004-01-shared-artifact-core.md` | Extract `agent_workflows/artifact_core.py` (id6 primitives, weekly-shard date math, dangling-cite detector, tiered-manifest + `--check` shape, writing-command safety); refactor `research_contract`/`research_index`/`research_refs`/`research_archive` to import it with NO behavior change. | none |
| 02 | `20260808-0004-02-plan-id-in-ipd-schema.md` | Add `- Id:` (6-char base36 from the core) as a REQUIRED plan metadata field in `ipd_schema`; `aw ipd lint` validates it; `aw ipd scaffold`/`sync` emit it. | 01 |
| 03 | `20260808-0004-03-plans-manifest-and-check.md` | `aw plans index [--check]`: `INDEX.json` (all plans) + a browse-by-`Set:` view bounded to the 40 most-recent Sets; `--check` drift gate (missing/invalid `Id`, name-vs-metadata mismatch, stale view, dangling plan citation). | 01, 02 |
| 04 | `20260808-0004-04-plans-regroup-and-refs.md` | `aw plans set-assign`/`mv`: (re)assign `Set:`/`Order:`, optionally rename to `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`, keep `Id`, rewrite plan citations (full-name, bare-stem, range) via the stable id; reuse the core dangling detector. | 01, 02, 03 |
| 05 | `20260808-0004-05-plans-shards-and-archival.md` | Weekly `YYYYMM-Www/` shards inside `executed/`/`superseded/`/`not-executed/`; `aw plans archive` (targeted + deliberate aged sweep with preview); INDEX refresh. | 01, 03, 04 |
| 06 | `20260808-0004-06-migrate-existing-plans.md` | One-time migration: assign `Id`, rename all executed+pending plans to the clustering grammar (tracked renames), rewrite the three citation forms, regenerate INDEX; dry-run mapping + STOP-for-review gate. | 01, 02, 03, 04, 05 |
| 07 | `20260808-0004-07-plans-scaffold-directives-decisions.md` | Installer scaffold (terminal-dir shard parents), AGENTS.md pointer note for the `aw plans` grouping verbs, DECISIONS D124 pointer entry, TODO update (prompts named next adopter). | 01, 03, 05 |

Execution order (dependency-correct): 01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07.

## Completion criteria (the whole Set is done only when)

- Each child (01 to 07) is executed and its OWN two checklists are verified with concrete evidence.
- The cross-IPD validation below passes.
- The suite is green after each child and at the end; leak-clean; no em/en dashes in authored Markdown.
- This repo's `.agents/plans/` is fully migrated onto the clustering grammar (Child 06) and `aw plans index --check` passes clean.

## Cross-IPD validation

- Consistency: the id6 primitive, shard date math, dangling-cite detector, and manifest/`--check` shape are defined ONCE in the shared core (Child 01) and both the research modules and the plans code reference that single definition (no forks). Read them together and confirm no contradiction.
- No collision: the plan `Id` lives in the existing `ipd_schema` metadata block and does NOT introduce a second research-style frontmatter block; `Set:`/`Order:`/`Status:`/`Kind:`/watermark keep their existing meaning.
- No research regression: `research_contract`/`research_index`/`research_refs`/`research_archive` behave identically after importing the core (their tests still pass unchanged).
- Dependency correctness: execution order 01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07; no child uses a later child's symbols; the migration (06) runs only after the Id/manifest/regroup/shard tools exist.
- Size check: each child stays within the IPD size guidance (prefer <=5 task groups / <=18 E leaves); if any child grows past it during authoring, split it further.

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| Applying the convention to `prompts/`, `comms/`, `walkthroughs/` | scope | Plans is the highest-value adopter; prompts are the weakest case (low volume, existing lifecycle, research-prompt lineage already handled). | TODO future-work note (Child 07); a later Set. |
| A pre-commit/CI hook for `aw plans index --check` | usability | Ships hook-less like `aw ipd lint` (spec OQ4); the workflows carry the obligation. | The shared deferred leak-sanitizer / `aw ipd lint` hook-wiring follow-up. |
| A unified single `aw <area>` verb surface across research + plans | complexity | One id CONCEPT (shared core) is adopted, but verbs stay area-native so agents keep the plans mental model. | Not planned. |

## Scope check

- Over-scope: none - this orchestrator only coordinates; the children make the bounded edits.
- Under-scope: the Set MUST deliver, for plans/: the shared core, the required `Id`, the manifest + `--check`, the regroup/rename verb, the shards + archival verb, the corpus migration with citations preserved, and the scaffold/directive/decision updates. Anything less leaves the convention half-applied.

## Required tests / validation

Per-child validation (each child names its own literal commands) plus the cross-IPD checks above. Run `python3 -m unittest discover -s tests -t .` after each child and at the end; paste ACTUAL output (the `Ran N tests ... OK` summary); `aw check-local-leaks . --agent` clean; no em/en dashes. Final acceptance: `aw plans index --check` passes on this repo's migrated `plans/`.

## Open questions

### OQ-01: spec open questions OQ1 to OQ5 ownership

- Blocking: no
- Status: resolved
- Owner: the individual children
- Resolution or deferral rationale: the spec's OQ1 to OQ5 were RESOLVED with the human at spec approval (2026-08-08): clustering grammar `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` (drop HHMM); `Id` required for all plans; all terminal disposition dirs shard weekly; `--check` ships hook-less; the browse view is grouped by `Set:` bounded to 40 recent Sets. Each child implements its assigned resolution; the orchestrator does not re-open them.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Child 01 in `.agents/plans/executed/` with `Status: executed` and its own Validation checklist verified; confirm the research suite passed unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: cite Child 02 executed after Child 01 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: cite Child 03 executed after Children 01 and 02 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: cite Child 04 executed after Children 01 through 03 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: cite Child 05 executed after Children 01, 03, and 04 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: cite Child 06 executed after Children 01 through 05 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: cite Child 07 executed after Children 01, 03, and 05 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: confirm the id6/shard/detector/manifest primitives are defined once in `artifact_core` and consumed by both research and plans with no fork; confirm the plan `Id` did not introduce a second frontmatter block; confirm execution order respected the dependency table.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste the actual final `python3 -m unittest` summary line (`Ran N tests ... OK`); confirm `aw plans index --check` clean, leak-clean, and no em/en dashes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload. Terminal lifecycle transition is a POST-gate transaction, never an execution/validation checklist item.
