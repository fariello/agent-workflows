# IPD (ORCHESTRATOR): research-organization convention and tooling (Set `research-org`)

- Date: 2026-07-30
- Concern: implement the approved `.agents/` artifact-organization design for `.agents/docs/research/` (the spec `.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md`): stable greppable ids, filename-encoded set grouping, tool-owned lifecycle, a tiered generated manifest, weekly cold shards, and progressive-disclosure tooling, so a human and an agent can cheaply answer "what did we find re X?" and "what still needs addressing?" at scale.
- Scope: ORCHESTRATOR for the ordered Set `research-org`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It does NOT itself change files (each child does its own edits). Implementation is scoped to `research/` only; `plans/executed/` and other areas are named future adopters (tracked in TODO, Child 07).
- Status: to-review
- Set: research-org
- Order: 0
- Quarantine: old-shape draft; superseded by the ipd-structure convention, to be re-authored to the E-*/V-* shape
- Quarantine owner: maintainer (IPD-system-first sequencing decision, 2026-08-03)
- Quarantine follow-up: re-author the research-org Set to the new schema after the ipd-structure Set lands
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from the approved spec `20260730-2152-01-agents-artifact-organization.spec.md`. Split into a Set because the work spans a naming/schema contract, three distinct tool surfaces, a data migration of 78 files, and framework scaffolding + convention edits (well beyond one IPD's size guidance) with clear dependency ordering.

- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's IPD-system-first sequencing decision defers this old-shape research-org plan; quarantined under spec Section 13.3 (metadata trio added) pending re-authoring to the new E-*/V-* shape after the ipd-structure Set. Not conforming, not an error; an informational disposition.

## Goal

Deliver the research-organization convention end to end for `.agents/docs/research/`: define the identity/naming/frontmatter contract; build the `aw research` and `aw archive` tooling (creation, indexing, querying, regrouping, archival); migrate the 78 existing research files onto the convention; and wire the scaffold + directives + prior-decision revisions. Dogfood in this repo. Do not build the convention for other `.agents/` areas yet (future adopters are named, not implemented).

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260730-2201-01-research-naming-and-frontmatter-contract.md` | Define the naming grammar, `<id6>` id, enumerated `<model>`/`<kind>` vocab, and the frontmatter schema as the authoritative contract (resolves OQ1/OQ4/OQ5/OQ6). Pure spec/docs/constants; no behavior yet. | none |
| 02 | `20260730-2201-02-aw-research-create-tool.md` | `aw research new` and `new-comparison`: id generation, name assembly, vocab validation/normalization, starter frontmatter, self-revealing next-step output. | 01 |
| 03 | `20260730-2201-03-research-index-generator.md` | Tiered manifest: `INDEX.json` (all) + `INDEX.md` (most-recent-N + intake, reference in, archive out); `aw research index [--check]`; `aw research find`. Resolves OQ2/OQ3. | 01, 02 |
| 04 | `20260730-2201-04-research-rename-and-refs-tool.md` | `aw research set-assign`/`mv`: regroup/rename, update references repo-wide, flag dangling `\b<id6>\b` citations (F5). | 01, 02, 03 |
| 05 | `20260730-2201-05-research-archival-and-states.md` | State lifecycle (intake/active/reference/archive), weekly `YYYYMM-Www` shards for reference and archive, `aw archive [research] [<id>]` (targeted + deliberate aged sweep with preview). | 01, 03 |
| 06 | `20260730-2201-06-migrate-existing-research.md` | Back-fill frontmatter + `<id6>`, group cohorts into sets, normalize model-token drift, classify initial status/outcome, regenerate INDEX, preserve citations for the 78 existing files. | 01, 02, 03, 04, 05 |
| 07 | `20260730-2201-07-scaffold-directives-and-decision-updates.md` | Installer scaffold (READMEs, dir shape), thin AGENTS.md pointer (F6), P5 revision, DECISIONS pointer entry, TODO future-work note (plans/executed/ next). | 01, 03, 05 |

## Detailed Implementation Checklist (TODO)

The orchestrator's "actions" are gating the children and running the cross-IPD checks.

- [ ] **Child 01 executed** (naming/frontmatter contract) and its own checklists verified.
- [ ] **Child 02 executed** (create tool, after 01) and verified.
- [ ] **Child 03 executed** (index generator, after 01/02) and verified.
- [ ] **Child 04 executed** (rename/refs tool, after 01/02/03) and verified.
- [ ] **Child 05 executed** (archival/states, after 01/03) and verified.
- [ ] **Child 06 executed** (migrate 78 files, after 01 to 05) and verified.
- [ ] **Child 07 executed** (scaffold/directives/decisions, after 01/03/05) and verified.
- [ ] **Cross-IPD validation run** (consistency / no-drift / dependency correctness / size).
- [ ] **Suite green** after the last child (paste actual output); leak-clean; no em/en dashes; `aw research index --check` clean.

## Completion criteria (the whole Set is done only when)

- Each child (01 to 07) is executed and its OWN two checklists are verified with concrete evidence.
- The cross-IPD validation below passes.
- The suite is green after each child and at the end; leak-clean; no em/en dashes in authored Markdown.
- This repo's `.agents/docs/research/` is fully migrated onto the convention (Child 06) and `aw research index --check` passes clean.

## Cross-IPD validation

- Consistency: the naming grammar, `<id6>` definition, `<model>`/`<kind>` vocab, frontmatter schema, and state vocabulary are defined ONCE in Child 01 and every later child + the tool + the docs reference that single definition (no forks). Read them together and confirm no contradiction.
- No duplication/drift: children 02 to 07 consume Child 01's contract; the spec's open questions (OQ1 to OQ6) are each resolved in exactly one child and not re-litigated elsewhere.
- Dependency correctness: no child uses a later child's symbols; the create tool (02) does not assume the index (03); the migration (06) runs only after the create/index/rename/archival tools exist.
- Size check: each child stays within the IPD size guidance (prefer <=5 major steps); if any child grows past it during authoring, split it further.

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| Applying the convention to `plans/executed/`, `prompts/`, `comms/`, `walkthroughs/` | scope | Highest-value is plans, but the Set is deliberately research-first to prove the model before the 179-file migration. | TODO future-work note (Child 07); a later Set. |
| History rewrite to purge old research names from git history | complexity/functionality | Renames preserve content; old names in history are harmless and rewriting history is destructive (needs explicit human approval, release-review posture). | Not planned. |
| Auto/background archival | usability | Archival must be deliberate and tool-invoked (spec 4.10); no background side effects. | N/A. |

## Scope check

- Over-scope: none - this orchestrator only coordinates; the children make the bounded edits.
- Under-scope: the Set MUST deliver, for research/: the naming/id/frontmatter contract, the create + index + rename + archival tooling, the migration of all 78 existing files with citations preserved, and the scaffold/directive/decision updates. Anything less leaves the convention half-applied.

## Required tests / validation

Per-child validation (each child names its own literal commands) plus the cross-IPD checks above. Run `python -m pytest -q` after each child and at the end; paste ACTUAL output; `aw check-local-leaks . --agent` clean; no em/en dashes. Final acceptance: `aw research index --check` passes on this repo's migrated `research/`.

## Open questions

- The spec's OQ1 to OQ6 are assigned to specific children (01 owns OQ1/OQ4/OQ5/OQ6; 03 owns OQ2/OQ3). Each child confirms its assigned OQ with the human at its own review; the orchestrator does not pre-decide them.

## Validation and cross-check (verify before reporting the Set complete)

Each item maps to a checklist item above; provide concrete evidence.

- [ ] Each child 01 to 07 is in `.agents/plans/executed/` with `Status: executed` and its own Validation checklist verified; cite each.
- [ ] Cross-IPD validation performed: quote the naming grammar + `<id6>` + frontmatter schema + state vocab from Child 01 and confirm the tool and every later child match; confirm execution order respected the dependency table.
- [ ] Paste the actual final `pytest` summary line; confirm `aw research index --check` clean, leak-clean, and no em/en dashes.
- [ ] Report any child that is incomplete/blocked/unverified EXPLICITLY; do NOT mark the Set complete otherwise.

## Approval and execution gate

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload.
