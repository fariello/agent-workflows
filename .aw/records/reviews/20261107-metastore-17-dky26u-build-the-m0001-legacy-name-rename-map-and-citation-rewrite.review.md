# Review findings: plan dky26u

- Subject-Id: dky26u
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `01c564538` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261107-metastore-17-dky26u-build-the-m0001-legacy-name-rename-map-and-citation-rewrite.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` with 0 errors, 0 warnings and 2 `IPD-C802` infos (em dashes in the validation preamble). After edits, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings. The plan adds no code; every measurement below was taken with the real repository functions (`artifact_refs.plan_reference_rewrites_with_warnings`, `artifact_core.iter_scan_files`, `artifact_naming._LEGACY_TIMESTAMP_RE`) against this worktree.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | 2,035 hits in 457 files only | Adds the review re-measure (2,067 hits in 472 files, 0 warnings) as context, bar re-derived at execution | PR-008. |
| Scope, Scope check | Three functions; `m0001_metadata_v2.py` "touched only to call the step-3 functions" with no item doing it | Adds `apply_step3` (E-04) and names it as the only `m0001_metadata_v2.py` edit; adds the `3g20ms` downstream-constant note and the AC-41 case 4 boundary | PR-004, PR-007. |
| E-01 | Collision refusal unspecified in extent; no journal reuse rule; no facet rule | Repository-wide (Set, order) refusal for collisions the step creates, report-only for pre-existing duplicates; duplicate legacy name and duplicate `id6` refusals; journal reuse and `journal=None` preview; `build_clustered_name` with a facet check | PR-003, PR-005. |
| E-02 | "Drop every edit inside a history line"; exemption list naming `artifact_refs`/`plans_refs`; 4 added roots | Records protected spans for apply-time masking; scratch-root guard; real exemption pairs; 7 added roots; per-location counts on masked text; `fenced-or-permalink` reason | PR-001, PR-002, PR-006. |
| E-04 (new, `aw ipd sync --apply`) | (absent) | Protected-span citation apply, byte-identity assertion, citations before moves, resumable moves, wiring into `m0001_metadata_v2.py` | PR-001, PR-004. |
| E-03 | Tests listed by topic | Tests listed by behaviour, including unmapped-plan collision, journal reuse, guard, byte-identical spans, idempotence; depends on E-04 | PR-007. |
| Findings | F-01..F-03 | Adds F-04..F-09 with review evidence; F-02 corrected | PR-001..PR-006. |
| Proposed changes | 3 bullets | 4 bullets plus a Mermaid `flowchart TD` of the step-3 data flow (rendered with `@mermaid-js/mermaid-cli` 12.2.0) | Technical writing standard requirement 12. |
| Validation preamble | Two em dashes (`IPD-C802`) | Commas | Proofreading. |
| V-01..V-04 | `-k` test-name filters as the bar; V-04 `TODO` | Behaviours named beside node ids; read-only live preview on this checkout (V-01); dry citation plan on a throwaway clone (V-02); V-04 byte-identity, idempotence, resume and the wiring diff | PR-007. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `m0001_renames.py` (`classify_name`, `build_rename_map`, `plan_citation_rewrites`, `apply_step3`) is consumed by `ghhzb6` (old path and `rename` event), `3g20ms` E-01 (replaces its constants with discovered inputs) and `dcerjg` V-15 (clone proof).
2. No. No authentication, secrets or network surface; the step writes only inside the scratch copy.
3. Yes. Four `E-*` items across the rename map, the citation planner, the scratch apply wired into the journaled run, and tests.
4. No. All four `- Scope-Paths:` entries are explicit files.
5. Yes. The cutover renames 34 records and rewrites about 2,000 citations in one irreversible commit; a wrong edit inside a `## Workflow history` section would corrupt the history that step 4 imports byte for byte (AC-10, AC-41 case 4).

AW-TIER: complex

### Step R1

- Checked: spec `4sd62s` 5.2 step 3 (OQ-26, OQ-27, OQ-28), AC-41, AC-34 case 5; `artifact_refs.RefEdit`, `plan_reference_rewrites_with_warnings`, `apply_reference_rewrites`, `_mask_fenced_code`, `_mask_permalinks`; `artifact_core.iter_scan_files`, `is_ignored_path`, `mint_id6`; `artifact_naming.build_clustered_name`, `ARTIFACT_TYPE_FACETS`; `record_history._inline_history_records`, `history_path`; `project_context.project_records_dir`.
- Found PR-001: `RefEdit` is one row per (file, kind, old) and `apply_reference_rewrites` substitutes every occurrence in the file, so "drop every edit inside a history line" cannot be implemented by filtering edits; a file citing an old name in both body and history would have its history rewritten.
- Found PR-002: the exemption list named `artifact_refs` and `plans_refs`, which hold 0 legacy citations, and missed `selectors.py` (4 hits) and `check_engine.py` (2 hits) that use the `wvlk84` legacy name as the `parse_clustered` misparse example; the `artifact_naming`/`artifact_rename` hits are spec citations, not old-grammar examples.
- Found PR-006: `project_records_dir` honours a stored records placement, so a scratch copy could resolve records outside itself; a probe confirmed a scratch root under gitignored `.aw/state/` is still scanned.

### Step R2

- Checked: `E-*`/`V-*` bijection (4/4 after `aw ipd sync --apply`), dependency order (E-01 -> E-02 -> E-04 -> E-03), `- Scope-Paths:` against item text, runtime reachability of each `V-*`.
- Found PR-004: `m0001_metadata_v2.py` was declared but no item edited it, and no plan in the Set owned the step-3 file moves or the scratch citation apply (`vxevph` E-03 owns the journal and scratch-to-checkout apply; `ghhzb6` E-01 owns the `rename` event).
- Found that 18 of the 34 renamed records cite a legacy name, so citations must be applied before moves (now ordered in E-04).

### Step R3

- Checked: refusal paths (collision, duplicate name, duplicate `id6`, unknown facet, records outside scratch, edits outside scratch, any warning, changed protected span, both old and new path present) and that every refusal precedes writes; safety section forbidding any apply on this checkout.
- No further findings.

### Step R4

- Checked: idempotence (journal reuse of minted ids, skip of already-moved files, second call changes nothing), resume via journal, outcome-based tests only, `core` tier budget rule.
- Found PR-005: without journal reuse a second dry run would mint different ids and produce a different map; added.

### Step R5

- Checked: QA (behaviour-named V evidence, byte comparison of protected spans), architect (step-3 boundary versus `vxevph`, `ghhzb6`, `3g20ms`, `dcerjg`), reliability (atomic writes, resumability), maintainability (repository facts in named constants for `3g20ms`).
- Found PR-007: V-01..V-03 used `-k` test-name filters as the bar and V-04 was a `TODO`; rewritten to demand behaviours, a read-only live map preview and a dry citation plan on a throwaway clone.

### Step R6

- Checked: 4 `E-*` items in 2 task groups, 3 work `- Scope-Paths:` entries; `aw ipd lint` density advisories cleared (`IPD-Z602` 0). E-02 and E-04 are each one concern (plan versus apply). No split needed.

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:vxevph` (`tve77h` executed; `vxevph` pending `to-review`, so the runner holds this plan at dispatch); downstream `ghhzb6`, `hpedmn`, `o19353`, `dcerjg` depend on `executed:dky26u`; `3g20ms` Scope-Paths include `m0001_renames.py`.
- Found PR-003: the collision check must include unmapped plans (for example `awphysical` Order 1 is `cwjnj0`), but this repository already has 22 (Set, Order) pairs shared among existing plans; a blanket repository refusal would refuse every run. Refusal now covers only collisions the step creates; existing duplicates are reported.

### Step S5

- Checked: OQ-02 (resolved, carried from `dcerjg`) and the HOW choices behind PR-001..PR-006.
- All choices were engineering HOW decisions resolvable from repository evidence and are recorded in `### Decisions` (D-1..D-5). Zero human-owned questions remain.

### Pass 2

- Re-reviewed E-01..E-04 and V-01..V-04 because E-04 and V-04 were added via `aw ipd sync --apply` (`steps/s6-rereview.md` rule 1). Added the scratch-root-builder handoff (E-04 step 0) so the widened roots exist in the scratch copy, the already-moved skip rule, and the gitignored-scratch guard test. Lint `clean`, 0 findings.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / E-02, E-04 | `agent_workflows/artifact_refs.py` `RefEdit`, `apply_reference_rewrites` (`text.replace(e.old, e.new)`) | History-line protection by dropping edits is impossible at `RefEdit` granularity; the authored plan would rewrite `## Workflow history` text that step 4 must import byte for byte. | C:Med; U:Low; S:Low; F:High; overall Medium | FIXED | E-02 records protected spans; E-04 masks them, substitutes, restores and asserts byte identity, without calling `apply_reference_rewrites`. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / E-02, F-02 | review run of the real tool: `selectors.py` 4, `check_engine.py` 2, `artifact_naming.py` 2, `artifact_rename.py` 1, `artifact_refs.py` 0, `plans_refs.py` 0 | Exemption list named files with no legacy citation and missed the two files that use a legacy name as a deliberate example. | Low | FIXED | Exemptions are three (path, legacy name) pairs; spec citations in comments are rewritten. |
| PR-003 | MEDIUM | IN-SCOPE | R7 / E-01 | review probe: 1,920 plans, 22 pre-existing duplicate (Set, Order) pairs; `cwjnj0` is `awphysical` 1 | Collision refusal's extent was unstated; map-only misses unmapped plans, repository-wide refuses this repository. | Low | FIXED | Refuse collisions the step creates against any plan; report pre-existing duplicates; add duplicate-name and duplicate-id6 refusals. |
| PR-004 | HIGH | UNDER-SCOPE | R2 / Scope, E-04 | `vxevph` E-03, `ghhzb6` E-01, spec 5.2 step 3 "Step 3 moves the files" | No item owned the scratch file moves or citation apply, and `m0001_metadata_v2.py` was in Scope-Paths with no item editing it. | Low | FIXED | Added E-04 (`apply_step3`, wired into the step-3 slot) and V-04. |
| PR-005 | MEDIUM | IN-SCOPE | R4 / E-01 | spec 5.2 step 3 "recording each minted value in the migration journal so that every dry run and the apply use the same one" | Map did not reuse journaled ids, so repeated dry runs could disagree. | Low | FIXED | Reuse from journal, mint with `existing=` pool, `journal=None` preview writes nothing. |
| PR-006 | MEDIUM | IN-SCOPE | R1 / E-02 | `project_context.project_records_dir` (stored placement), `artifact_core.iter_scan_files`; `TODO.md`, `.gitignore`, `.aw/.gitignore` legacy hits | Scratch copy could resolve records outside itself; three files citing legacy names were outside the widened roots. | Low | FIXED | Scratch-root and edits-inside-scratch guards; roots widened by three file roots. |
| PR-007 | MEDIUM | IN-SCOPE | R5 / V-01..V-04, E-03 | plan text before review | V items used test-name filters as the bar and V-04 was a `TODO`. | Low | FIXED | Behaviour-named evidence, a read-only preview, a dry plan on a throwaway clone, byte-identity and idempotence checks. |
| PR-008 | LOW | IN-SCOPE | Proofreading / Concern, preamble, Proposed changes | `IPD-C802` x2; stale count | Em dashes, stale count without date, no diagram for a branching multi-step flow. | Low | FIXED | Commas, dated re-measure as context, Mermaid flowchart. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How are history and verdict text protected? | Mask spans at apply time in this module's own loop, restore, assert byte identity | Filter `RefEdit` rows (impossible); add a hook to `artifact_refs.apply_reference_rewrites` (widens a shared API outside Scope-Paths) | `RefEdit` granularity, `apply_reference_rewrites` body | yes |
| D-2 | Which collisions refuse? | Collisions the step creates, against any plan; pre-existing duplicates reported | Map-internal only; refuse any duplicate | 22 measured pre-existing pairs; spec example `cwjnj0` | yes |
| D-3 | What is exempt? | Three (path, legacy name) pairs that are deliberate examples | The authored five-entry list | Real-tool hits per file | yes |
| D-4 | Who moves files in scratch, and when? | E-04, after citations, with `Path.rename`, resumable | Leave to `vxevph`/`ghhzb6` (neither owns it); move first (stale `RefEdit.file` paths) | Sibling plan text; 18 renamed records cite legacy names | yes |
| D-5 | Are fenced code blocks and permalinks rewritten? | No; the tool's existing masks stay and those occurrences are reported as unchanged | Unmask to reach every occurrence (would alter pasted evidence bytes) | 2,194 unmasked versus 1,472 masked hits; old names stay resolvable through path history (OQ-28) | yes |
