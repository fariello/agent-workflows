# IPD: migrate the existing research files onto the convention (Set `research-org`, Order 6)

- Date: 2026-07-30
- Kind: child
- Concern: apply the convention to this repo's existing research corpus (the dogfood): back-fill frontmatter + `<id6>`, group cohorts into sets, normalize model-token drift, classify initial status/outcome, generate the index, and preserve all citations.
- Scope: a one-time, reviewed data migration of `.agents/docs/research/**` using the Order 02 to 05 tools. Requires Orders 01 to 05 executed; if their tools are absent, STOP. Migratable = authored research `*.md` content files; EXCLUDED are nav/index files (`README.md`, `INDEX.json`, `INDEX.md`, `00-README-index.md`), `*template*.md`, `.gitkeep`, and non-`.md` artifacts under `research/**/prototype/` (`.ts`/`.py`/`.json`/`MANIFEST.json`), which stay VERBATIM in place under their parent set and receive no frontmatter/id6.
- Status: executed
- Set: research-org
- Order: 6
- Highest E allocated: 08
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the accepted one-time cost that proves the convention on real data.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (pytest->unittest), PR-002 (stale "78" removed; count re-counted at execution), PR-C06-6/E-07 (mandatory dry-run mapping + STOP gate before apply), PR-C06-2 (explicit migratable include/exclude list), PR-C06-4/E-08 (prompt-lineage per spec 4.6), PR-C06-5 (moves verified as git renames). Two new leaves E-07/E-08 assigned via `aw ipd sync`.
- 2026-08-07 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): recounted 71 migratable content files (16 excluded); produced the full dry-run mapping and STOPPED for human review; on approval applied the migration (frontmatter back-fill + id6 + set/NN grouping + model-token normalization + reviewed status/outcome; 10 superseded planrev drafts sharded to archive/202607-W28/; 67 citations rewritten across 22 files; INDEX regenerated). Moves are tracked git renames (69 R). Product commit 6735f3b; full suite green (Ran 627 tests OK, skipped=1); index --check clean; leak-clean; no em/en dashes in authored frontmatter. All E-01..E-08 performed and V-01..V-08 pass. The two pending plans from another agent were left untouched.

## Goal

Every migratable existing research file (the exact content-file total is re-counted at execution; the survey observed roughly seventy, and the count is anchored ONLY by the re-count, never by a hardcoded number) ends up: named to the grammar, carrying valid frontmatter with a stable `<id6>`, grouped into its set (or a singleton), classified with a reviewed `status`/`outcome`, indexed, and with all in-repo citations updated. Excluded files (nav/index/template/`.gitkeep`/prototype code, per Scope) stay verbatim in place. `aw research index --check` passes clean afterward. Spec Section 9.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: back-fill and regroup

- [x] E-01 confirm Orders 01 to 05 are executed and their tools are present, else STOP; then re-count the migratable research content files per the Scope include/exclude rule and record that exact before-total (do NOT rely on any hardcoded number).
  - Depends on: none
  - Expected outcome: the Order 02 to 05 tools are usable; a re-counted before-total (migratable content files only) is recorded.
  - Execution state: performed
- [x] E-07 produce a full DRY-RUN migration mapping (every migratable old path -> new grammar name + assigned `<id6>` + set/NN) AND the citation-rewrite diff, verify 1:1 completeness against the E-01 before-total, then STOP for review BEFORE any apply.
  - Depends on: E-01
  - Expected outcome: a reviewable mapping accounting for every migratable file with no gaps/dupes; nothing is moved or rewritten yet.
  - Execution state: performed
- [x] E-02 back-fill frontmatter + `<id6>` for every migratable research doc (created from git-first-commit; topic/kind/model inferred; consumed-by inferred from existing cites).
  - Depends on: E-07
  - Expected outcome: every migratable file has valid frontmatter; the `index --check` frontmatter stage is clean.
  - Execution state: performed
- [x] E-03 group cohorts into sets via `set-assign` and normalize names/model-token drift (`gpt-56`->`gpt56`, prefix->suffix); apply moves as tracked git renames.
  - Depends on: E-02
  - Expected outcome: each named cohort shares a date/set + ordered NN; singletons are well-formed; git tracks the moves as renames (R), not delete+add.
  - Execution state: performed
- [x] E-08 link each in-research `*-prompt.md` file to its research output as `NN=00` of that output's set (prompt lineage, spec 4.6); a prompt with no run output becomes a singleton.
  - Depends on: E-03
  - Expected outcome: every in-research prompt file is either the `NN=00` member of its cohort or a well-formed singleton; none is orphaned.
  - Execution state: performed

### Task group 2: citations, classification, index

- [x] E-04 update in-repo citations (DECISIONS/plans/TODO/docs) via the Order 04 reference updater; report + resolve danglers.
  - Depends on: E-03
  - Expected outcome: the dangling-cite report is empty after `--apply`; sample cites resolve.
  - Execution state: performed
- [x] E-05 classify initial `status`/`outcome` as a REVIEWED pass (cited -> reference; uncited/dead-end -> archive candidate), then shard per Order 05.
  - Depends on: E-03
  - Expected outcome: classification is recorded per doc; the miscategorization flag is empty.
  - Execution state: performed
- [x] E-06 generate `INDEX.json`+`INDEX.md` and run `aw research index --check`; paste the check result, dangling report, suite summary, and before/after count.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: `index --check` exits 0; INDEX.md is bounded + archive-excluded; the full suite stays green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Use the Order 02 to 05 tools; do NOT hand-edit names/frontmatter where a tool exists.
- Existing cohorts to preserve as sets: the two dated bundles (`20260726-0054-aw-delivery-*`, `20260726-1045-host-probe-*`), the `plan-review/` set (14 files), the `opencode/` and `opencode-security/` groups, the `suggested-future-skill-usage.*` set. Standalone advisories/findings become singletons.
- `created` derives from git-first-commit (earliest-evidence rule already used by the normalizer).
- Citations to update: DECISIONS.md, executed plans, TODO.md/roadmaps (the exact per-source counts are re-counted at execution, not hardcoded; the survey observed roughly ten DECISIONS refs and about fourteen plan files).
- In-research `*-prompt.md` files carry prompt lineage (spec 4.6): each becomes `NN=00` of its research output's set, or a singleton if it has no run output.
- Excluded (per Scope): nav/index/template/`.gitkeep`/prototype non-`.md` code stay verbatim in place and are NOT counted as migratable.
- External research artifacts stay VERBATIM in content (only names/frontmatter are added); the no-dash rule applies to what WE author.
- Moves are applied as tracked git renames (prefer `git mv`, staged not committed) so history is preserved.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C6-1 | HIGH | Medium | maintainer | dogfood | The convention is unproven until applied to the real corpus; migration is the proof + the value delivery. | spec 9 |
| C6-2 | HIGH | Medium | integrity | citations | Every DECISIONS + plan citation must survive the renames (per-source counts re-counted at execution, not hardcoded). | measured refs |
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

Migration is data, validated by the tools: after execution, `aw research index --check` exits 0; the dangling-cite report (Order 04) is empty; a spot-check of >=3 previously-cited docs shows their DECISIONS/plan cites still resolve; a sample of moved files shows as git renames (`git log --follow` / `git status` reports `R`, not delete+add); the full suite `python3 -m unittest discover -s tests -t .` stays green (PASTE the `Ran N tests ... OK` summary). Record a before/after file count (every migratable file accounted for, per the Scope include/exclude rule). Leak-clean; no em/en dashes in authored frontmatter/README.

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

- [x] V-01 validates E-01
  - Required evidence: cite Orders 01 to 05 in `executed/` and paste the re-counted MIGRATABLE-content file total (per the Scope include/exclude rule).
  - Observed evidence: Orders 01-05 are all executed in `.agents/plans/executed/`. Recount per the include/exclude rule: 71 migratable `.md` content files; 16 excluded (nav/index READMEs, `conformance-results-template.md` + a report template, `.gitkeep`, and the `opencode/.../prototype/` non-`.md` code + MANIFEST/schemas/json).
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste the full dry-run mapping (old path -> new name + id6 + set/NN) and confirm its row count equals the E-01 before-total with no gaps or duplicates, and that nothing was moved/rewritten before review.
  - Observed evidence: The full 71-row dry-run mapping was produced (old path -> new name + id6 + set + NN + status/outcome + model + kind) and reviewed with the human BEFORE any apply; row count == 71 == the E-01 before-total, ids unique. The human approved applying it (shard the archive-status drafts, rewrite citations). Nothing moved until `--apply`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: confirm EVERY migratable file has valid frontmatter (paste the `index --check` frontmatter result).
  - Observed evidence: after `--apply`, `aw research index` reported `index regenerated (71 docs)` with NO frontmatter/name drift (the migration's post-apply `_scan_docs` returned zero drift; `index --check` reports no `frontmatter-*` or `name-*` classes, only one illustrative example-cite in the executed Order-01 plan and the now-resolved stale-index).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste a migrated cohort (shared date/set/ordered NN) and a normalized model token; paste `git status`/`git log --follow` for a sample showing the moves are renames (R), not delete+add.
  - Observed evidence: the `awdeliv` cohort migrated to `20260726-awdeliv-00..04-<id6>-aw-delivery-and-clean-delta.<model>.research-report.md` (shared date 20260726, ordered NN 00-04, models gpt56/gemini36flash/gemini31pro/sonnet5 + reconciliation); `gpt-56` normalized to `gpt56`. `git status --porcelain` shows 69 `R` (rename) entries, 0 delete+add for moved files (history preserved).
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: cite each in-research `*-prompt.md` file and show it is `NN=00` of its set or a well-formed singleton; confirm none is orphaned.
  - Observed evidence: every prompt file is ordered FIRST within its set (prompts sorted ahead of reports): singleton prompts are `NN=00` (e.g. `...-cli-name-collision-research-prompt-00-...`, `...-agent-instruction-file-discovery-prompt-00-...`); the `occomms` set has three prompt files ordered `NN=00,01,02` ahead of its reports (a multi-prompt set cannot make all prompts 00, so lineage is preserved by ordering prompts before reports); the `chkplace`/`planrev` synthesis prompts are `NN=00`. None is orphaned (all are members of a set).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the (empty) dangling-cite report and >=3 resolved sample cites.
  - Observed evidence: `aw research check-refs --agent` reports only ONE match, an illustrative `k7m2xq` example inside the executed Order-01 plan (a documentation example, not a real citation). Real rewritten cites resolve: e.g. DECISIONS.md now cites `20260714-same-box-agent-wakeup-mechanisms-00-j2000q-...`, `20260716-opencode-unauthenticated-local-server-advisory-00-kams1a-...`, and `20260716-broker-feasibility-confirmation-00-xawbsa-...` (all present on disk).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: confirm classification is recorded and the miscategorization flag is empty; cite.
  - Observed evidence: each migrated file records a reviewed `status`/`outcome` in frontmatter (reference for kept/cited docs; archive/rejected for the 10 superseded plan-review iteration drafts). `aw research check-miscategorized` returns no archived-but-cited docs (the archive drafts are dead-end iterations with no `consumed-by` and no resolving citation).
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `aw research index --check` = exit 0; confirm INDEX.md bounded + archive-excluded; paste the full-suite summary; the before/after file count reconciles (all accounted for); leak-clean.
  - Observed evidence: `aw research index --check` exits 0 (the only reported line is the one illustrative example-cite noted in V-04; INDEX.json/INDEX.md are current). `INDEX.md` excludes the 10 archive-status drafts (they live in `archive/202607-W28/`). Full suite `python3 -m unittest discover -s tests -t .` -> `Ran 627 tests in 152.046s / OK (skipped=1)`. Before/after: 71 migratable in, 71 indexed (all accounted for). `aw sanitize --agent` exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01 to 05; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence (including a clean `index --check` and an empty dangling report); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files (the research tree + the citation-bearing files it updates), path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown (external artifact CONTENT stays verbatim). STOP and report if execution exceeds scope (research migration + its citations only). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
