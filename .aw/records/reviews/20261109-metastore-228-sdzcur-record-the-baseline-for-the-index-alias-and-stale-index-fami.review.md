# Review findings: plan sdzcur

- Subject-Id: sdzcur
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `dbb14c5fc` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` findings). Live inspection against governing spec `4sd62s` (section 4.5 and section 7 step 7), research `nj8zdp`, sibling finishing plan `q6epwc` (Order 41), sibling plans `tqknnc` (220), `lywgzs` (221), `mv0j4k` (222), `9eqgcl` (223), `w819as` (224), `f1yjlx` (225), `m8dblq` (226), `kkftwj` (227), and `6qh68x` (229), prerequisite plans `1ajqaa`, `59aiyh`, `dcerjg`, `ffceq0`, `g5hpbb`, and `t4gl15`, and live CLI probes of `aw check <type> --agent` uncovered one `HIGH`, three `MEDIUM`, and one `LOW` finding (`PR-001..PR-005`), all fixed in place. Pass 2 re-checked `E-01`, `E-02`, `V-01`, and `V-02`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted OQ-01 clearance, safety stop, scope fence declaration, staging and hand-mv prohibitions, and conditional finalize clause | Added OQ-01 clearance, prerequisite safety stop, Scope-Paths fence declaration, explicit staging/hand-mv prohibitions, and conditional runner/executor finalize clause | PR-001, steps/s7-finalize.md compliance. |
| E-01 and V-01 | Omitted `mkdir -p`, used raw `jq -r '.diagnostics[].rule'`, and left saved filenames unspecified | Added `mkdir -p .aw/state/sdzcur/before/`, switched to null-safe `jq -r '(.diagnostics // [])[].rule'`, named all saved files, and clarified empty `git status --porcelain` check | PR-002, preventing null iteration failure and directory missing error. |
| E-02, Findings F-28, V-02 | Instructed placing multi-line rule multisets inside pipe-table cell F-28 and omitted `aw sanitize --agent` | Kept F-28 as a single-line-per-row pipe table with `### F-28 rule-id multisets` fenced blocks below, and added bare `aw sanitize --agent` | PR-003, valid Markdown pipe-table syntax and leak prevention. |
| Spec sync and OQ-01 | `Spec / documentation sync` read `N/A`; `OQ-01` had `- Owner: none` | Cited spec `4sd62s` section 4.5 and section 7 step 7; set `- Owner: plan author` on `OQ-01` | PR-004, steps/s5-questions.md owner attestation standard. |
| Preamble, Conventions, Proposed changes, Front matter | Raw authoring instruction blockquote; bare symbol citations; 2-item list without diagram; missing readiness and review depth | Updated preamble blockquote, formatted code citations as `path::Symbol`, added Mermaid `flowchart TD` diagram, and added `- Readiness: go-pending-approval` and `- Review-Depth: complex` | PR-005, Technical Writing Standard Requirement 12(b) & Step S7. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Although `sdzcur` edits no Python module or CLI flag directly, it records and commits the normative `F-28` baseline (`aw check` rule-id multisets, `check.stale-index-*` counts, and core gate summary) that finishing plan `q6epwc` (Order 41, E-19/V-19) consumes as its regression contract.
2. No. `- Scope-Paths:` touches only `.aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md`.
3. No. It contains `2` execution items in `1` task group and `0` production/test Scope-Paths.
4. Yes. `- Scope-Paths:` explicitly names `.aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md`.
5. Yes. A malformed, truncated, or unparseable `F-28` baseline would break downstream comparisons in `q6epwc` across the entire `q6epwc` split family.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 4.5 and section 7 step 7); split parent `.aw/records/plans/pending/20261108-metastore-41-q6epwc-make-the-typed-aw-index-spellings-aliases-and-stop-index-reg.ipd.md`; research `.aw/records/research/20261108-plansize-01-nj8zdp-plan-size-calibration.findings.md`; sibling plans `tqknnc`, `lywgzs`, `mv0j4k`, `9eqgcl`, `w819as`, `f1yjlx`, `m8dblq`, `kkftwj`, and `6qh68x`; prerequisite plans `1ajqaa`, `59aiyh`, `dcerjg`, `ffceq0`, `g5hpbb`, and `t4gl15`; and `agent_workflows/check_engine.py::check_content`.
- Found owner attribution and spec-sync citation gaps (`PR-004`): `OQ-01` recorded `- Owner: none` on a resolved question (`steps/s5-questions.md` Section 3.1 item 5), and `Spec / documentation sync` read `N/A` despite `- From-Spec: 4sd62s`. Fixed in place.

### Step R2

- Checked: `1:1` `E-*`/`V-*` bijection (`E-01, E-02` <-> `V-01, V-02`; `- Highest E allocated: 02`), `- Scope-Paths:` completeness, `- Item-Dependencies:` coverage, live CLI envelope shapes (`aw check <type> --agent`), and `ipd_lint.lint_text` validation of `### F-28 ...` subsections under `## Findings`.
- Found missing gate contract clauses (`PR-001`), directory-creation / `jq` null-iteration / filename hazards in `E-01` and `V-01` (`PR-002`), and Markdown pipe-table syntax break from multi-line multisets in `E-02` / `F-28` / `V-02` (`PR-003`). Fixed in place.

### Step R3

- Checked: workspace containment (`.aw/state/sdzcur/before/` inside the lane worktree, never `/tmp`), read-only command safety, and local-leak protection when committing CLI outputs into a tracked IPD.
- Added bare `aw sanitize --agent` in `E-02` and `V-02` (`PR-003`) so no machine-local path or identifier can be committed into `F-28`.

### Step R4

- A (Correctness and data integrity): Null-safe multiset extraction (`jq -r '(.diagnostics // [])[].rule' \| sort \| uniq -c`) handles both clean and finding envelopes without nonzero exits.
- C (Architecture and operability): Committing `F-28` in this plan preserves cross-lane reproducibility across isolated runner worktrees where `.aw/state/` is gitignored.
- D and E (Anti-regression and testing): Table F-28 and its `### F-28 rule-id multisets` fenced blocks capture the exact baseline required by `q6epwc` E-19 to verify that only `check.stale-index-*` findings are eliminated.
- Executability and right-sizing: 2 E-items in 1 task group across 0 work Scope-Paths; cohesive and focused.

### Step R5

- Checked: QA/QC (per-command exit codes and multiset verification), Testing and regression (exact rule-id multisets before index alias/stale-index refactoring), Architect (committed cross-lane baseline replacing gitignored `.aw/state/`), Software Engineer (null-safe `jq` filter and deterministic filenames in `.aw/state/sdzcur/before/`), and Modest Executor (two focused sequential passes).

### Step R6

- Checked: 2 E-items in 1 task group with 0 work Scope-Paths (plan file only; `- Size assessment: standard`). Already split from `q6epwc` on 2026-11-09 per research `nj8zdp`. No further decomposition needed.

### Step R7

- Checked: finishing plan `q6epwc` (`E-19`/`V-19`) and all nine sibling plans (`Orders 220-227, 229`). Every sibling and `q6epwc` depends on `sdzcur` having executed, and `q6epwc` E-19 explicitly compares post-edit rule multisets against `sdzcur` F-28.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated `- Owner: none` to `- Owner: plan author`; recorded four self-resolved engineering decisions (`D-1..D-4`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain (`questions: []`).

### Step S6

- Re-reviewed `E-01`, `E-02`, `V-01`, `V-02`, `## Findings`, `## Proposed changes`, and `## Approval and execution gate` per `steps/s6-rereview.md`.
- Verified `2/2` `E-*`/`V-*` bijection, `- Highest E allocated: 02`, unchanged `- Scope-Paths:` and `- Item-Dependencies:`, zero em or en dashes, and `0` findings from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md:120 | Approval and execution gate omitted OQ-01 clearance, prerequisite safety stop, Scope-Paths fence declaration (--scope-reason / --scope-ack), explicit git add -A / -a and hand git mv prohibitions, and conditional runner/executor aw ipd finalize ownership required by steps/s7-finalize.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added OQ-01 clearance, prerequisite safety stop, scope fence declaration, staging and hand-mv prohibitions, and conditional runner/executor finalize clause to Gate (recommendation strength: strong). |
| PR-002 | MEDIUM | IN-SCOPE | R2 / R4 / E-01, V-01 | .aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md:42 | E-01 omitted mkdir -p .aw/state/sdzcur/before/ (failing in fresh worktrees), used jq -r '.diagnostics[].rule' (which exits 5 when findings == 0 omits diagnostics), and left saved filenames unspecified while V-01 required one file per command. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added mkdir -p .aw/state/sdzcur/before/, changed jq filter to (.diagnostics // [])[].rule, named all saved files in E-01 and V-01, and clarified empty git status --porcelain output (recommendation strength: very strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R3 / R4 / E-02, Findings F-28, V-02 | .aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md:47 | E-02 and F-28 instructed placing multi-line multisets inside Markdown pipe-table cells (breaking GFM pipe-table syntax) and omitted aw sanitize --agent before committing CLI outputs into a tracked plan file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Structured F-28 as a single-line-per-row pipe table followed by ### F-28 rule-id multisets fenced blocks, added bare aw sanitize --agent, and updated V-02 (recommendation strength: strong). |
| PR-004 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01, Spec sync | .aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md:99 | Resolved question OQ-01 recorded - Owner: none (violating steps/s5-questions.md Section 3.1 item 5), and Spec / documentation sync read N/A without citing governing spec 4sd62s. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set - Owner: plan author on OQ-01, clarified eight sibling plans plus q6epwc, recorded D-1 in Decisions, and cited spec 4sd62s section 4.5 and section 7 step 7 in Spec / documentation sync (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | Proofreading / Requirement 12 & Conventions | .aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md:22 | Preamble retained raw authoring instruction blockquote, Project conventions used bare symbols instead of path::Symbol, and Proposed changes lacked a Requirement 12 Mermaid flowchart. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated preamble blockquote, formatted code citations as path::Symbol, added a Mermaid flowchart TD diagram in Proposed changes, and added readiness and review depth to front matter (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Why commit the `q6epwc` family baseline in a separate child plan (`sdzcur`) rather than saving only under `.aw/state/`? | Commit `F-28` and its subsections inside `sdzcur` before Orders 220-227, 229, and `q6epwc` run, attributing `OQ-01` to `plan author`. | Keep baseline only in gitignored `.aw/state/` (rejected: isolated runner lane worktrees do not share gitignored state). | `sdzcur` OQ-01, research `nj8zdp`, `steps/s5-questions.md:21` | yes |
| D-2 | How should `E-02` store multi-line rule-id multisets in `## Findings` without breaking Markdown pipe-table syntax? | Keep `F-28` as a single-line-per-row Markdown pipe table holding scalar metrics, and write the full multisets into fenced `text` blocks directly below `F-28` under `### F-28 rule-id multisets`. | Inline multi-line fenced blocks inside pipe-table cells (rejected: invalid GFM table syntax). | `q6epwc` E-19, verified `conforming` via `ipd_lint.lint_text` | yes |
| D-3 | What `jq` expression should `E-01` use to extract rule-id multisets from `aw check`? | Use `jq -r '(.diagnostics // [])[].rule' \| sort \| uniq -c`. | Keep `jq -r '.diagnostics[].rule'` (rejected: exits `5` with `Cannot iterate over null` when `findings == 0` omits `"diagnostics"`). | Live probe on `aw check <type> --agent` (`findings=0`, `diagnostics` absent) | yes |
| D-4 | How should `V-01` and `V-02` verify baseline files and cleanliness? | Explicitly name all 10 files under `.aw/state/sdzcur/before/`, check empty `git status --porcelain`, and require clean `aw sanitize --agent`. | Leave file names unspecified (rejected: uncheckable by executor). | `steps/r2-executability.md:7`, `sdzcur` E-01/V-01 | yes |
