# Review findings: plan 1suzlp

- Subject-Id: 1suzlp
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `a6132f2cc` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-151-1suzlp-pin-and-move-the-ipd-lint-metadata-reads-onto-artifact-meta.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). The baseline test suites passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_ipd_lint.py tests/test_readiness_absence_invariant.py tests/test_orchestrator_readiness.py tests/test_plan_priority_required.py` printed `138 passed in 73.16s (0:01:13)`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-004 | MD-15, Section 7.2 |
| `## Detailed Implementation Checklist` (E-01, E-03) | E-01 referenced bare `M105` and lacked explicit directory creation for `.aw/state/ffceq0/`; E-03 referenced bare `M105` | Standardized rule code to canonical `IPD-M105` and added explicit directory creation instruction (`mkdir -p .aw/state/ffceq0`) | PR-003, PR-004 |
| `## Proposed changes` | Ordered list of 3 steps, no diagram | Ordered list of 3 steps plus Mermaid `flowchart TD` | PR-002 (Requirement 12b) |
| `## Validation and cross-check` (V-01) | Referenced bare `M105` | Standardized to `IPD-M105` | PR-003 |
| `## Approval and execution gate` | Lacked scope fence section and conditional runner/executor finalize ownership | Added declaration scope fence with `--scope-reason`/`--scope-ack`, narrow prerequisite safety stop, and conditional runner/executor finalize ownership ("never a hand `git mv`") | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Changes internal module signatures (`ipd_lint.lint_text(text, *, state=None)` and internal `ipd_lint.parse`), maintaining `state=None` default for backwards compatibility with existing callers.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact plan with 3 execution items (E-01..E-03) in 1 task group across 3 work Scope-Paths (`agent_workflows/ipd_lint.py`, `agent_workflows/ipd_schema.py`, `tests/test_readers_ipd_lint.py`).
4. Yes. `- Scope-Paths:` explicitly declares all modified paths.
5. Yes. `ipd_lint` is the core structural linter across CI, pre-commit hooks, and runner lifecycle gates; defects in metadata parsing or state resolution would cascade across the entire repository.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/ipd_lint.py` (`parse`, `lint_text`, `lint_file`, `_structural_lines`, `check_readiness_attestation`, `check_readiness_required`, `check_coverage_record`, `_citation_anchor_applies`, `_CITATION_PLAN_DATE_RE`, `C_META_PATH`, `C_EXEC_HISTORY`, `C_READINESS_UNATTESTED`, `C_READINESS_REQUIRED`, `C_COVERAGE_RECORD`); `agent_workflows/ipd_schema.py` (`parse_metadata_block`); governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C5, Section 4.4 bullet "Gate IPD-S405", Section 7 step 5).
- Verified that `ipd_lint.py` currently parses `meta_slice` with `ipd_schema.parse_metadata_block` at line 396 and reads history lines manually for `IPD-S405`, `IPD-M107`, and `IPD-M112` (PR-001).
- Verified that `_CITATION_PLAN_DATE_RE` at line 1191 is an unused pattern (`_citation_anchor_applies` at line 1204 uses `re.match` on `doc.meta_fields.get("Date")`); moving date extraction to cached `State` cleanly retires it.
- Verified that `C_META_PATH = "IPD-M105"` is the registered code for path-status validation, and standardized bare `M105` references to `IPD-M105` (PR-003).

### Step R2

- Checked: 1:1 bijection between E-01..E-03 and V-01..V-03; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:r81uvz, executed:w1cs3p, executed:na188y, executed:i3b5zu, executed:ebrc4t`; and verification reachability.
- Added explicit directory creation in E-01 for gitignored `.aw/state/ffceq0/` to ensure clean saving of before-baseline outcome lists (PR-004).

### Step R3

- Checked: security, file paths, and temporary state isolation.
- Baselines are saved strictly under `.aw/state/ffceq0/` (gitignored), avoiding `/tmp` pollution and ensuring no untracked state is committed.

### Step R4

- Checked: conceptual density, right-sizing, anti-regression, and backward compatibility.
- The plan splits the metadata migration cleanly into three focused steps: pin current behavior (E-01), accept `State` in `lint_text` with string fallback (E-02), and migrate rule readers to `State` (E-03).
- Backward compatibility: maintaining `state: Optional[State] = None` with fallback to `artifact_meta.read_text(text)` preserves all 65 existing `lint_text` call sites without editing tests.

### Step S5

- Checked: no unresolved open questions; OQ-01 is resolved. All four review decisions (D-1..D-4) are recorded and verified (`Reversible: yes`).

### Pass 2

- Re-read all revised sections of `1suzlp`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | `.aw/records/plans/pending/20261109-metastore-151-1suzlp-pin-and-move-the-ipd-lint-metadata-reads-onto-artifact-meta.ipd.md:136-147`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:33-46` | The gate lacked an explicit scope fence declaration section, lacked conditional runner/executor finalize ownership ("never a hand `git mv`"), and lacked a narrow safety stop for missing prerequisite `artifact_meta` interfaces. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reconciled gate with standard execution contract: added declaration scope fence, narrow unsafe-condition prerequisite stop, and conditional runner/executor finalize ownership (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / R6 | `.aw/records/plans/pending/20261109-metastore-151-1suzlp-pin-and-move-the-ipd-lint-metadata-reads-onto-artifact-meta.ipd.md:82-87`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` (strong). |
| PR-003 | LOW | IN-SCOPE | References / Consistency | `.aw/records/plans/pending/20261109-metastore-151-1suzlp-pin-and-move-the-ipd-lint-metadata-reads-onto-artifact-meta.ipd.md:41,51,122`; `agent_workflows/ipd_lint.py:67` | Inconsistent naming of rule `IPD-M105` as bare `M105` across E-01, E-03, and V-01. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Normalized all occurrences to canonical identifier `IPD-M105` (strong). |
| PR-004 | LOW | IN-SCOPE | R2 / Executability | `.aw/records/plans/pending/20261109-metastore-151-1suzlp-pin-and-move-the-ipd-lint-metadata-reads-onto-artifact-meta.ipd.md:41-44` | E-01 directs saving baseline files to `.aw/state/ffceq0/` without an explicit directory creation step (`mkdir -p .aw/state/ffceq0`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/ffceq0` instruction in E-01 (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `ipd_lint.lint_text` receive plan metadata without breaking existing string callers? | Add optional `state: Optional[State] = None` keyword argument, falling back to `artifact_meta.read_text(text)` when `None` | Require all callers to pass `State` (breaks 58 test call sites and string callers); maintain a duplicate metadata parser in `ipd_lint` (violates spec `4sd62s` C5) | `4sd62s` C5; `1suzlp` E-02; `dqutt8` E-03 | yes |
| D-2 | How should `Approval and execution gate` be structured? | Add explicit scope fence declaration with `--scope-reason` and `--scope-ack`, narrow safety stop if prerequisite `artifact_meta.read_text` is missing, and conditional runner/executor finalize ownership | Omit scope fence or instruct stop on out-of-scope edits (violates 2026-09-01 maintainer ruling) | `.aw/system/workflows/plan-review/steps/s7-finalize.md:37-46` | yes |
| D-3 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in `Proposed changes` illustrating the pin, metadata input migration, and rule reader migration workflow | Omit diagram (violates Requirement 12b) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-4 | How should rule identifiers in E-01, E-03, and V-01 be standardized? | Use canonical registered rule code `IPD-M105` consistently throughout | Leave bare `M105` token | `agent_workflows/ipd_lint.py:67` (`C_META_PATH = "IPD-M105"`) | yes |
