# IPD: migrate the existing 78 research files onto the convention (Set `research-org`, Order 6)

- Date: 2026-07-30
- Concern: apply the convention to this repo's existing research corpus (the dogfood): back-fill frontmatter + `<id6>`, group cohorts into sets, normalize model-token drift, classify initial status/outcome, generate the index, and preserve all citations.
- Scope: a one-time, reviewed data migration of `.agents/docs/research/**` using the Order 02 to 05 tools. Requires Orders 01 to 05 executed; if their tools are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 6
- Quarantine: old-shape draft; superseded by the ipd-structure convention, to be re-authored to the E-*/V-* shape
- Quarantine owner: maintainer (IPD-system-first sequencing decision, 2026-08-03)
- Quarantine follow-up: re-author the research-org Set to the new schema after the ipd-structure Set lands
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the accepted one-time cost that proves the convention on real data.

- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's IPD-system-first sequencing decision defers this old-shape research-org plan; quarantined under spec Section 13.3 (metadata trio added) pending re-authoring to the new E-*/V-* shape after the ipd-structure Set. Not conforming, not an error; an informational disposition.

## Goal

Every existing research file (78 at survey time; re-count at execution) ends up: named to the grammar, carrying valid frontmatter with a stable `<id6>`, grouped into its set (or a singleton), classified with a reviewed `status`/`outcome`, indexed, and with all in-repo citations updated. `aw research index --check` passes clean afterward. Spec Section 9.

## Detailed Implementation Checklist (TODO)

- [ ] **Precheck**: Orders 01 to 05 executed; tools present, else STOP. Re-count research files (survey said 78).
- [ ] **Task 1: back-fill frontmatter + id** for every doc.
- [ ] **Task 2: group cohorts + normalize names/model drift**.
- [ ] **Task 3: update citations** (DECISIONS/plans/TODO/docs); danglers resolved.
- [ ] **Task 4: reviewed status/outcome classification** + shard.
- [ ] **Task 5: generate INDEX + `index --check`**.
- [ ] **Tests/validation** as above; PASTE `index --check` result, dangling report, suite summary, before/after count.
- [ ] **Lifecycle/commit** path-scoped; `git add` new files; never push.

## Project conventions discovered (Step 0)

- Use the Order 02 to 05 tools; do NOT hand-edit names/frontmatter where a tool exists.
- Existing cohorts to preserve as sets: the two dated bundles (`20260726-0054-aw-delivery-*`, `20260726-1045-host-probe-*`), the `plan-review/` set (14 files), the `opencode/` and `opencode-security/` groups, the `suggested-future-skill-usage.*` set. Standalone advisories/findings become singletons.
- `created` derives from git-first-commit (earliest-evidence rule already used by the normalizer).
- Citations to update: DECISIONS.md (10 refs), executed plans (14 files), TODO.md/roadmaps.
- External research artifacts stay VERBATIM in content (only names/frontmatter are added); the no-dash rule applies to what WE author.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C6-1 | HIGH | Medium | maintainer | dogfood | The convention is unproven until applied to the real corpus; migration is the proof + the value delivery. | spec 9 |
| C6-2 | HIGH | Medium | integrity | citations | 10 DECISIONS + 14 plan cites must survive the renames. | measured refs |
| C6-3 | MEDIUM | Medium | curation | classification | Initial reference-vs-archive is a reviewed judgment, not a blind default. | spec 4.5/9 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 9.1 | Back-fill frontmatter + `<id6>` for every research doc (created from git-first-commit; topic/kind/model inferred; consumed-by inferred from existing cites). | `.agents/docs/research/**` | Medium | every file has valid frontmatter; `index --check` frontmatter stage clean |
| 2 | 9.2/9.3 | Group cohorts into sets via `set-assign` and normalize names/model-token drift (`gpt-56`->`gpt56`, prefix->suffix). | `.agents/docs/research/**` | Medium | each named cohort shares date/set + ordered NN; singletons well-formed |
| 3 | 9.5 | Update in-repo citations (DECISIONS/plans/TODO/docs) via the Order 04 reference updater; report + resolve danglers. | `DECISIONS.md`, `.agents/plans/**`, `TODO.md`, docs | Medium | dangling-cite report is empty after `--apply`; sample cites resolve |
| 4 | 9.4 | Classify initial `status`/`outcome` as a REVIEWED pass (cited -> reference; uncited/dead-end -> archive candidate), then shard per Order 05. | `.agents/docs/research/**` | Medium | classification recorded per doc; miscategorization flag empty |
| 5 | 9 | Generate `INDEX.json`+`INDEX.md`; run `aw research index --check`. | `.agents/docs/research/INDEX.*` | Low | `index --check` exits 0; INDEX.md bounded + archive-excluded |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Migrating plans/prompts/comms | n/a | scope | Future adopters. | Order 07 TODO |
| Rewriting git history of old names | complexity | Destructive; content preserved; not needed. | Not planned |

## Scope check

- Over-scope: none - a bounded migration of the existing research tree + citation updates.
- Under-scope: MUST account for EVERY existing file, preserve EVERY citation, and end with a clean `index --check`.

## Required tests / validation

Migration is data, validated by the tools: after execution, `aw research index --check` exits 0; the dangling-cite report (Order 04) is empty; a spot-check of >=3 previously-cited docs shows their DECISIONS/plan cites still resolve; the full suite `python -m pytest -q` stays green (PASTE). Record a before/after file count (all accounted for). Leak-clean; no em/en dashes in authored frontmatter/README.

## Spec / documentation sync

Regenerate `.agents/docs/research/README.md`/INDEX from the migrated state. No spec change (this executes the spec).

## Open questions

- Set-id names for existing cohorts (e.g. `awdeliv`, `hostprobe`, `planrev`, `occomms`, `ocsec`, `skills`). Confirm at review.

## Validation and cross-check (verify before reporting done)

- [ ] Precheck: cite Orders 01 to 05 in executed/; PASTE the re-counted file total.
- [ ] Task 1: confirm EVERY file has valid frontmatter (PASTE `index --check` frontmatter result).
- [ ] Task 2: PASTE a migrated cohort (shared date/set/ordered NN) and a normalized model token.
- [ ] Task 3: PASTE the (empty) dangling-cite report and >=3 resolved sample cites.
- [ ] Task 4: confirm classification recorded and miscategorization flag empty; cite.
- [ ] Task 5: PASTE `aw research index --check` = exit 0; confirm INDEX.md bounded + archive-excluded.
- [ ] PASTE full-suite summary; before/after file count reconciles (all accounted for); leak-clean.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; else do not transition.

## Approval and execution gate

Proposal; human review + approval; not auto-executed. Requires Orders 01 to 05; if absent, STOP. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation item is verified with concrete evidence (including a clean `index --check` and an empty dangling report); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files (the research tree + the citation-bearing files it updates), path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown (external artifact CONTENT stays verbatim). STOP and report if execution exceeds scope (research migration + its citations only). Never create or push a tag / Release / PyPI upload.
