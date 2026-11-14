# Review findings: plan 3g20ms

- Subject-Id: 3g20ms
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `0491f968a` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-104-3g20ms-make-m0001-discover-its-inputs-and-convert-id-less-records.ipd.md` was committed and unmodified, so no pre-review snapshot was needed. Before edits, `aw ipd lint --phase author --agent` returned clean (0 findings, 2 advisory dash notices). Baseline existing migration tests passed on unmodified code: `python3 -m pytest tests/test_command_surface_declarations.py tests/test_layout_migration.py tests/test_migrate_layout_cli.py` printed `69 passed in 3.55s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned clean with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| Blockquote line 20 | Authoring template prompt blockquote | Replaced with standard technical writing compliance blockquote | Requirement 12, standard compliance |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-004 | MD-15, Section 7.2 |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-001 (Requirement 12b) |
| `## Validation and cross-check` | Contained two prose em-dashes `—` | Replaced em-dashes with parentheses to eliminate `IPD-C802` advisories | PR-002 |
| `## Approval and execution gate` | Lacked explicit prerequisite safety stop | Added narrow safety stop if prerequisite metastore symbols from `dcerjg`, `9vf2iv`, or `6oi2nu` are absent | PR-004 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Changes `m0001` metadata migration discovery logic and id-less record conversion contract under spec `4sd62s` 5.2a.
2. No. It edits migration modules under `agent_workflows/migrations/`, touching no private data or isolation guards.
3. No. Compact plan with 2 execution items across 1 task group and 5 migration modules.
4. Yes. `- Scope-Paths:` explicitly declares all files to modify.
5. Yes. Migration logic mistakes could corrupt records during repository migration.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/migrations/`; spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Section 5.2a items 1 and 4, C12 shape c); prerequisite plans `dcerjg`, `9vf2iv`, `6oi2nu`; origin plan `g5hpbb`.
- Verified that all prerequisite references, citations, and split heritage resolve correctly.

### Step R2

- Checked: 1:1 bijection between E-01..E-02 and V-01..V-02; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:dcerjg, executed:9vf2iv, executed:6oi2nu`; and verification reachability.
- Verified that V-01 and V-02 demand concrete verifiable evidence (rg check for absence of id6 literals/corpus counts, discovery reproducing measured values, dry-run census and log for idless_prose fixture with unclassifiable file check).

### Step R3

- Checked: Security, isolation, and privacy. The execution gate explicitly requires that `aw migrate metadata --apply` never run against live checkouts and execute solely against temporary test fixtures. Collision-free id minting is backed by `artifact_core.mint_id6`.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density.
- Sized cleanly (2 items, 1 task group, 5 work paths). Universal discovery eliminates fragile hardcoded repository constants.

### Step S5

- Checked: Open questions. No open questions remain. Review decisions (D-1..D-4) recorded and verified (`Reversible: yes`).

### Pass 2

- Re-read all revised sections of `3g20ms`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | LOW | IN-SCOPE | Proofreading / Technical Writing | `.aw/records/plans/pending/20261109-metastore-104-3g20ms-make-m0001-discover-its-inputs-and-convert-id-less-records.ipd.md:20` | Authoring template prompt blockquote present; missing front-matter metadata (`- Review-Depth: standard`, `- Readiness: go-pending-approval`); `Proposed changes` lacked a Requirement 12 Mermaid diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template prompt blockquote with standard compliance blockquote, added `- Review-Depth: standard` and `- Readiness: go-pending-approval` to front matter, and added `flowchart TD` Mermaid diagram to `Proposed changes`. |
| PR-002 | LOW | IN-SCOPE | Proofreading / Prose style | `.aw/records/plans/pending/20261109-metastore-104-3g20ms-make-m0001-discover-its-inputs-and-convert-id-less-records.ipd.md:88` | Line 88 contained two prose em-dashes `—` triggering `IPD-C802` advisory findings. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced prose em-dashes with parentheses. |
| PR-003 | LOW | IN-SCOPE | S5 Questions & Governance | `.aw/records/plans/pending/20261109-metastore-104-3g20ms-make-m0001-discover-its-inputs-and-convert-id-less-records.ipd.md:83` | No open questions section issues; verified zero open questions remain. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Confirmed empty question set is valid and verified. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / S7 / Approval and execution gate | `.aw/records/plans/pending/20261109-metastore-104-3g20ms-make-m0001-discover-its-inputs-and-convert-id-less-records.ipd.md:104` | Approval and execution gate lacked an explicit narrow safety stop if prerequisite metastore symbols from `dcerjg`, `9vf2iv`, or `6oi2nu` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added narrow safety stop for prerequisite metastore symbols to execution gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in `Proposed changes` illustrating universal discovery, id-less conversion, and dual validation tracks | Omit diagram (violates Requirement 12b) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-2 | How should front matter metadata and template prompt be updated? | Add `- Readiness: go-pending-approval` and `- Review-Depth: standard` to front matter, and replace template blockquote with standard compliance blockquote | Leave incomplete metadata | `steps/s7-finalize.md:61-78`; MD-15, Section 7.2 | yes |
| D-3 | How should prose em-dashes on line 88 be handled? | Replace em-dashes with parentheses to eliminate `IPD-C802` advisories | Leave em-dashes in place | `agent_workflows/ipd_lint.py:1347` (IPD-C802) | yes |
| D-4 | How should prerequisite symbol presence be guarded at the execution gate? | Add an explicit narrow safety stop if prerequisite metastore symbols from `dcerjg`, `9vf2iv`, or `6oi2nu` are absent | Rely solely on item-dependency metadata | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | yes |
