# IPD: migrate the existing 78 research files onto the convention (Set `research-org`, Order 6)

- Date: 2026-07-30
- Kind: child
- Concern: apply the convention to this repo's existing research corpus (the dogfood): back-fill frontmatter + `<id6>`, group cohorts into sets, normalize model-token drift, classify initial status/outcome, generate the index, and preserve all citations.
- Scope: a one-time, reviewed data migration of `.agents/docs/research/**` using the Order 02 to 05 tools. Requires Orders 01 to 05 executed; if their tools are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 6
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the accepted one-time cost that proves the convention on real data.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.

## Goal

Every existing research file (78 at survey time; re-count at execution) ends up: named to the grammar, carrying valid frontmatter with a stable `<id6>`, grouped into its set (or a singleton), classified with a reviewed `status`/`outcome`, indexed, and with all in-repo citations updated. `aw research index --check` passes clean afterward. Spec Section 9.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: back-fill and regroup

- [ ] E-01 confirm Orders 01 to 05 are executed and their tools are present, else STOP, and re-count the research files (survey said 78).
  - Depends on: none
  - Expected outcome: the Order 02 to 05 tools are usable; a re-counted before-total is recorded.
  - Execution state: pending
- [ ] E-02 back-fill frontmatter + `<id6>` for every research doc (created from git-first-commit; topic/kind/model inferred; consumed-by inferred from existing cites).
  - Depends on: E-01
  - Expected outcome: every file has valid frontmatter; the `index --check` frontmatter stage is clean.
  - Execution state: pending
- [ ] E-03 group cohorts into sets via `set-assign` and normalize names/model-token drift (`gpt-56`->`gpt56`, prefix->suffix).
  - Depends on: E-02
  - Expected outcome: each named cohort shares a date/set + ordered NN; singletons are well-formed.
  - Execution state: pending

### Task group 2: citations, classification, index

- [ ] E-04 update in-repo citations (DECISIONS/plans/TODO/docs) via the Order 04 reference updater; report + resolve danglers.
  - Depends on: E-03
  - Expected outcome: the dangling-cite report is empty after `--apply`; sample cites resolve.
  - Execution state: pending
- [ ] E-05 classify initial `status`/`outcome` as a REVIEWED pass (cited -> reference; uncited/dead-end -> archive candidate), then shard per Order 05.
  - Depends on: E-03
  - Expected outcome: classification is recorded per doc; the miscategorization flag is empty.
  - Execution state: pending
- [ ] E-06 generate `INDEX.json`+`INDEX.md` and run `aw research index --check`; paste the check result, dangling report, suite summary, and before/after count.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: `index --check` exits 0; INDEX.md is bounded + archive-excluded; the full suite stays green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Use the Order 02 to 05 tools; do NOT hand-edit names/frontmatter where a tool exists.
- Existing cohorts to preserve as sets: the two dated bundles (`20260726-0054-aw-delivery-*`, `20260726-1045-host-probe-*`), the `plan-review/` set (14 files), the `opencode/` and `opencode-security/` groups, the `suggested-future-skill-usage.*` set. Standalone advisories/findings become singletons.
- `created` derives from git-first-commit (earliest-evidence rule already used by the normalizer).
- Citations to update: DECISIONS.md (10 refs), executed plans (14 files), TODO.md/roadmaps.
- External research artifacts stay VERBATIM in content (only names/frontmatter are added); the no-dash rule applies to what WE author.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C6-1 | HIGH | Medium | maintainer | dogfood | The convention is unproven until applied to the real corpus; migration is the proof + the value delivery. | spec 9 |
| C6-2 | HIGH | Medium | integrity | citations | 10 DECISIONS + 14 plan cites must survive the renames. | measured refs |
| C6-3 | MEDIUM | Medium | curation | classification | Initial reference-vs-archive is a reviewed judgment, not a blind default. | spec 4.5/9 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 9.1 | Back-fill frontmatter + `<id6>` for every research doc (created from git-first-commit; topic/kind/model inferred; consumed-by inferred from existing cites). | `.agents/docs/research/**` | Medium | E-02 |
| 2 | 9.2/9.3 | Group cohorts into sets via `set-assign` and normalize names/model-token drift (`gpt-56`->`gpt56`, prefix->suffix). | `.agents/docs/research/**` | Medium | E-03 |
| 3 | 9.5 | Update in-repo citations (DECISIONS/plans/TODO/docs) via the Order 04 reference updater; report + resolve danglers. | `DECISIONS.md`, `.agents/plans/**`, `TODO.md`, docs | Medium | E-04 |
| 4 | 9.4 | Classify initial `status`/`outcome` as a REVIEWED pass (cited -> reference; uncited/dead-end -> archive candidate), then shard per Order 05. | `.agents/docs/research/**` | Medium | E-05 |
| 5 | 9 | Generate `INDEX.json`+`INDEX.md`; run `aw research index --check`. | `.agents/docs/research/INDEX.*` | Low | E-06 |

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

### OQ-01: set-id names for existing cohorts

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: the existing cohorts adopt short set-ids (e.g. `awdeliv`, `hostprobe`, `planrev`, `occomms`, `ocsec`, `skills`). Confirm the exact names at review; if they change, only this child changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01 to 05 in `executed/` and paste the re-counted file total.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: confirm EVERY file has valid frontmatter (paste the `index --check` frontmatter result).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a migrated cohort (shared date/set/ordered NN) and a normalized model token.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the (empty) dangling-cite report and >=3 resolved sample cites.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm classification is recorded and the miscategorization flag is empty; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `aw research index --check` = exit 0; confirm INDEX.md bounded + archive-excluded; paste the full-suite summary; the before/after file count reconciles (all accounted for); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01 to 05; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including a clean `index --check` and an empty dangling report); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files (the research tree + the citation-bearing files it updates), path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown (external artifact CONTENT stays verbatim). STOP and report if execution exceeds scope (research migration + its citations only). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
