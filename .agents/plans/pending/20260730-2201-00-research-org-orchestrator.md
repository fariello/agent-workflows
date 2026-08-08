# IPD (ORCHESTRATOR): research-organization convention and tooling (Set `research-org`)

- Date: 2026-07-30
- Kind: orchestrator
- Concern: implement the approved `.agents/` artifact-organization design for `.agents/docs/research/` (the spec `.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md`): stable greppable ids, filename-encoded set grouping, tool-owned lifecycle, a tiered generated manifest, weekly cold shards, and progressive-disclosure tooling, so a human and an agent can cheaply answer "what did we find re X?" and "what still needs addressing?" at scale.
- Scope: ORCHESTRATOR for the ordered Set `research-org`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It does NOT itself change files (each child does its own edits). Implementation is scoped to `research/` only; `plans/executed/` and other areas are named future adopters (tracked in TODO, Child 07).
- Status: approved
- Set: research-org
- Order: 0
- Highest E allocated: 09
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-08-07 human maintainer (via opencode its_direct/pt3-claude-opus-4.8-1m-us): "Consider them all approved. Please do them in the recommended order."

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from the approved spec `20260730-2152-01-agents-artifact-organization.spec.md`. Split into a Set because the work spans a naming/schema contract, three distinct tool surfaces, a data migration of the existing research corpus, and framework scaffolding + convention edits (well beyond one IPD's size guidance) with clear dependency ordering.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (pytest->unittest), PR-002 (stale "78"->re-count), PR-006 (dependency reorder 01,02,04,03,05,06,07 + dangling-detector single source), PR-011 (OQ2/OQ3 pinned N=40), plus the cross-IPD dangling-gate consistency check. Independent parallel read-only audit lanes + human decisions on 7 open questions.

## Goal

Deliver the research-organization convention end to end for `.agents/docs/research/`: define the identity/naming/frontmatter contract; build the `aw research` and `aw archive` tooling (creation, indexing, querying, regrouping, archival); migrate the existing research files onto the convention (the exact count is re-counted at execution, not hardcoded); and wire the scaffold + directives + prior-decision revisions. Dogfood in this repo. Do not build the convention for other `.agents/` areas yet (future adopters are named, not implemented).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

The orchestrator's execution leaves gate the children and run the whole-Set checks. They use the same stable E/V contract as every other actionable IPD.

- [ ] E-01 verify Child 01 (naming/frontmatter contract) is executed and its own two checklists are verified.
  - Depends on: none
  - Expected outcome: the naming grammar, `<id6>`, `<model>`/`<kind>` vocab, and frontmatter schema are complete.
  - Execution state: pending
- [ ] E-02 verify Child 02 (create tool) is executed after Child 01 and its own checklists are verified.
  - Depends on: E-01
  - Expected outcome: `aw research new`/`new-comparison` are complete.
  - Execution state: pending
- [ ] E-04 verify Child 04 (rename/refs tool) is executed after Children 01 and 02 and its own checklists are verified.
  - Depends on: E-01, E-02
  - Expected outcome: regroup/rename (atomic tracked) + reference update (pinned scan root) + the reusable dangling detector primitive are complete.
  - Execution state: pending
- [ ] E-03 verify Child 03 (index generator + find) is executed after Children 01, 02, and 04 and its own checklists are verified (its `--check` consumes Order 04's dangling detector).
  - Depends on: E-01, E-02, E-04
  - Expected outcome: the tiered INDEX (N=40) + `find` + `--check` (four drift classes incl. dangling) are complete.
  - Execution state: pending
- [ ] E-05 verify Child 05 (archival/states) is executed after Children 01, 03, and 04 and its own checklists are verified.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: the state lifecycle + weekly shards + `aw archive` verbs (per-item preview/override) are complete.
  - Execution state: pending
- [ ] E-06 verify Child 06 (migrate the existing corpus) is executed after Children 01 through 05 and its own checklists are verified.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the corpus migration with preserved citations and a clean `index --check` is complete.
  - Execution state: pending
- [ ] E-07 verify Child 07 (scaffold/directives/decisions) is executed after Children 01, 03, and 05 and its own checklists are verified.
  - Depends on: E-01, E-03, E-05
  - Expected outcome: scaffold + thin AGENTS.md pointer + P5/DECISIONS/TODO edits are complete.
  - Execution state: pending
- [ ] E-08 run the cross-IPD validation.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: consistency, no-drift, dependency-correctness, and size checks pass.
  - Execution state: pending
- [ ] E-09 run the final suite and repository dogfood checks and paste actual output.
  - Depends on: E-08
  - Expected outcome: the suite is green, leak-clean, no em/en dashes, and `aw research index --check` is clean.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260730-2201-01-research-naming-and-frontmatter-contract.md` | Define the naming grammar, `<id6>` id, enumerated `<model>`/`<kind>` vocab, and the frontmatter schema as the authoritative contract (resolves OQ1/OQ4/OQ5/OQ6). Pure spec/docs/constants; no behavior yet. | none |
| 02 | `20260730-2201-02-aw-research-create-tool.md` | `aw research new` and `new-comparison`: id generation, name assembly, vocab validation/normalization, starter frontmatter, self-revealing next-step output. | 01 |
| 04 | `20260730-2201-04-research-rename-and-refs-tool.md` | `aw research set-assign`/`mv`: regroup/rename (atomic tracked), update references over a pinned scan root (full-old-name token only), and a REUSABLE dangling `\b<id6>\b` detector primitive (F5). Runs BEFORE 03 so 03 can consume the detector. | 01, 02 |
| 03 | `20260730-2201-03-research-index-generator.md` | Tiered manifest: `INDEX.json` (all) + `INDEX.md` (most-recent-N=40 + intake, reference in, archive out); `aw research index [--check]` (consumes Order 04's dangling detector for the 4th drift class, spec 5.2); `aw research find`. Resolves OQ2/OQ3. | 01, 02, 04 |
| 05 | `20260730-2201-05-research-archival-and-states.md` | State lifecycle (intake/active/reference/archive), weekly `YYYYMM-Www` shards for reference and archive, `aw archive [research] [<id>]` (targeted + deliberate aged-and-uncited sweep with per-item preview/override); reuses Order 04's reference-updater on move. | 01, 03, 04 |
| 06 | `20260730-2201-06-migrate-existing-research.md` | Dry-run mapping + STOP gate, then back-fill frontmatter + `<id6>`, group cohorts into sets (tracked renames), normalize model-token drift, prompt-lineage, classify initial status/outcome, regenerate INDEX, preserve citations for the existing corpus (count re-counted at execution). | 01, 02, 03, 04, 05 |
| 07 | `20260730-2201-07-scaffold-directives-and-decision-updates.md` | Installer scaffold (`reference/`/`archive/` dirs + convention README; research/ already scaffolded), thin AGENTS.md pointer section (F6), P5 narrowing (specs stay path-stable, research exempt), DECISIONS pointer entry (D123, cites D88), TODO future-work note (plans/executed/ next). | 01, 03, 05 |

Execution order (dependency-correct): 01 -> 02 -> 04 -> 03 -> 05 -> 06 -> 07. Order 04 executes before Order 03 because Order 03's `index --check` consumes Order 04's dangling-cite detector primitive (spec 5.2), and Order 04's rename/reference logic resolves against the filesystem + the Order 01 id6 regex (not the generated INDEX), so there is no reverse dependency.

## Completion criteria (the whole Set is done only when)

- Each child (01 to 07) is executed and its OWN two checklists are verified with concrete evidence.
- The cross-IPD validation below passes.
- The suite is green after each child and at the end; leak-clean; no em/en dashes in authored Markdown.
- This repo's `.agents/docs/research/` is fully migrated onto the convention (Child 06) and `aw research index --check` passes clean.

## Cross-IPD validation

- Consistency: the naming grammar, `<id6>` definition, `<model>`/`<kind>` vocab, frontmatter schema, and state vocabulary are defined ONCE in Child 01 and every later child + the tool + the docs reference that single definition (no forks). Read them together and confirm no contradiction.
- Dangling-cite single source: the dangling `\b<id6>\b` detector is defined ONCE as a reusable primitive in Child 04 (`research_refs.py`) and CONSUMED by Child 03's `index --check` (spec 5.2's fourth drift class) and Child 05's miscategorization flag; confirm no child reimplements it.
- No duplication/drift: children 02 to 07 consume Child 01's contract; the spec's open questions (OQ1 to OQ6) are each resolved in exactly one child and not re-litigated elsewhere.
- Dependency correctness: execution order is 01 -> 02 -> 04 -> 03 -> 05 -> 06 -> 07; no child uses a later child's symbols; the create tool (02) does not assume the index (03); Child 04 does not assume the index (03); Child 03 consumes Child 04's detector; the migration (06) runs only after the create/index/rename/archival tools exist.
- Size check: each child stays within the IPD size guidance (prefer <=5 task groups / <=18 E leaves); if any child grows past it during authoring, split it further.

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| Applying the convention to `plans/executed/`, `prompts/`, `comms/`, `walkthroughs/` | scope | Highest-value is plans, but the Set is deliberately research-first to prove the model before the 179-file migration. | TODO future-work note (Child 07); a later Set. |
| History rewrite to purge old research names from git history | complexity/functionality | Renames preserve content; old names in history are harmless and rewriting history is destructive (needs explicit human approval, release-review posture). | Not planned. |
| Auto/background archival | usability | Archival must be deliberate and tool-invoked (spec 4.10); no background side effects. | N/A. |

## Scope check

- Over-scope: none - this orchestrator only coordinates; the children make the bounded edits.
- Under-scope: the Set MUST deliver, for research/: the naming/id/frontmatter contract, the create + index + rename + archival tooling, the migration of ALL existing migratable files (count re-counted at execution) with citations preserved, and the scaffold/directive/decision updates. Anything less leaves the convention half-applied.

## Required tests / validation

Per-child validation (each child names its own literal commands) plus the cross-IPD checks above. Run `python3 -m unittest discover -s tests -t .` after each child and at the end; paste ACTUAL output (the `Ran N tests ... OK` summary); `aw check-local-leaks . --agent` clean; no em/en dashes. Final acceptance: `aw research index --check` passes on this repo's migrated `research/`.

## Open questions

### OQ-01: spec open questions OQ1 to OQ6 ownership

- Blocking: no
- Status: resolved
- Owner: the individual children
- Resolution or deferral rationale: the spec's OQ1 to OQ6 are assigned to specific children (01 owns OQ1/OQ4/OQ5/OQ6; 03 owns OQ2/OQ3) and were RESOLVED at the 2026-08-07 plan-review with the human: id6 = base36-6 collision-checked; set-date-in-name + per-file `created` in frontmatter; hot states at root, `reference/`/`archive/` weekly-sharded; default N = 40 (configurable); INDEX.json + INDEX.md committed and kept fresh via `--check`; kind vocab corpus-derived with a tool extension mechanism. Each child records its own resolution.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Child 01 in `.agents/plans/executed/` with `Status: executed` and its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: cite Child 02 executed after Child 01 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: cite Child 04 executed after Children 01 and 02 with its own Validation checklist verified.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: cite Child 03 executed after Children 01, 02, and 04 with its own Validation checklist verified (incl. the `--check` dangling class consuming Order 04).
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
  - Required evidence: quote the naming grammar + `<id6>` + frontmatter schema + state vocab from Child 01 and confirm the tool and every later child match; confirm the dangling detector is defined once (Child 04) and consumed by Child 03/05; confirm execution order respected the dependency table (01, 02, 04, 03, 05, 06, 07).
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste the actual final `python3 -m unittest` summary line (`Ran N tests ... OK`); confirm `aw research index --check` clean, leak-clean, and no em/en dashes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload. Terminal lifecycle transition is a POST-gate transaction, never an execution/validation checklist item.
