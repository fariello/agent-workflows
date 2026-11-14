# Review findings: plan r81uvz

- Subject-Id: r81uvz
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `46849d9eb` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), the baseline test suites (`tests/test_status_set_metadata_region.py`, `tests/test_selector_resolver_matrix.py`, `tests/test_check_engine_metadata_region.py`) passed (`27 passed in 1.84s`), and the related status_set/bounding suites (`tests/test_blocks_release_reader_bounding.py`, `tests/test_status_set.py`, `tests/test_status_set_descriptive_safety.py`, `tests/test_artifact_meta_loader_parity.py`) passed (`139 passed in 16.28s`). During revision, `mkdir -p .aw/state/ffceq0 .aw/state/r81uvz` was added to the PIN-FIRST rule, code citations were converted to `path::Symbol` identifiers, Behavior decisions were expanded to document `D-1` through `D-6`, a Mermaid `flowchart TD` diagram was added under `## Proposed changes`, class-qualified pytest node IDs were specified in `E-04`, `E-05`, `V-04`, and `V-05`, and a narrow unsafe-condition stop rule was added to `Approval and execution gate`. Pass 2 re-checked the complete revised plan against `4sd62s`, `ffceq0`, and `cdglt1`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter, Workflow history | Omitted review output fields and review history record | Adds `- Readiness: go-pending-approval`, `- Review-Depth: complex`, and records review history | PR-002, Step S7 review output requirements. |
| Detailed Implementation Checklist (PIN-FIRST RULE, E-04, E-05) | Assumed `.aw/state/ffceq0/` already existed without directory creation, lacked class-qualified test node IDs, and used unqualified symbols | Adds `mkdir -p .aw/state/ffceq0 .aw/state/r81uvz`, specifies exact test node IDs in `E-04` and `E-05`, and converts citations to `path::Symbol` | PR-001, PR-002, PR-003. |
| Project conventions discovered (Step 0) | Cited code with unqualified `module.function` references | Cites `path::Symbol` identifiers for `artifact_meta.py`, `plans.py`, `selectors.py`, `attention_contract.py`, `plans_index.py`, `cli.py`, and `layout.py` | Technical Writing Standard Requirement 7, PR-002. |
| Findings (F-03..F-11) and Behavior decisions (D-1..D-6) | Stated baseline test counts without non-binding framing and listed only D-6, omitting D-1 through D-5 despite stating they were copied from `ffceq0` | Marks baseline counts non-binding and documents `D-1` through `D-6` covering multi-word plan status (`D-1`), loose whitespace/YAML (`D-2`), detail text fallback (`D-3`), region-bounded reading (`D-4`), skip lists (`D-5`), and filename Set derivation (`D-6`) | PR-004. |
| Proposed changes (ordered, validatable) | One-line description without process diagram | One-line description with Mermaid `flowchart TD` diagram | Technical Writing Standard Requirement 12(b), PR-002. |
| Validation and cross-check (V-04, V-05) and Approval and execution gate | V-04 and V-05 lacked exact class-qualified pytest node IDs and used coarse `-k` filter; Approval and execution gate lacked an unsafe-condition stop rule | Specifies exact class-qualified pytest node IDs in `V-04` and `V-05` and adds a narrow unsafe-condition stop rule and scope fence declaration in `Approval and execution gate` | PR-003, PR-005. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `r81uvz` moves `status_set.py`'s `read_artifact_record`, `inventory_all_artifacts`, `_format_status_transition_line`, `plan_priority_work_kind_problems`, `read_item_dependencies_value`, and status change preparation onto `artifact_meta`, changing inventory resolution and Set matching for records without in-file `- Set:` bullets (D-6).
2. Yes. Governs lifecycle status transitions, release blocks, gate enforcement, and attestation handling across all tracked artifacts in the repository.
3. No (`2` right-sized `E-*` items in `1` task group across `3` `- Scope-Paths:` entries), though `agent_workflows/status_set.py` (4,443 lines) is a critical core module pinned against 166 existing tests across seven suites.
4. No. `- Scope-Paths:` explicitly names `agent_workflows/status_set.py`, `tests/test_artifact_meta_loader_parity.py`, and the plan file itself.
5. Yes. A bug in status transition validation or inventory parsing could cause improper status transitions, corrupted lifecycle headers, or broken `aw set` commands.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Sections 4.3, 4.4, 4.5, 5, 7, and Criteria C1, C5, C10); parent plan `ffceq0` (Order 08); predecessor plan `cdglt1` (Order 142); prerequisite plans `tve77h` (Order 02), `xexn45` (Order 07), and `g5hpbb` (Order 14); and production modules `agent_workflows/status_set.py`, `agent_workflows/artifact_meta.py`, `agent_workflows/selectors.py`, and `agent_workflows/plans.py`.
- Verified that `status_set.py` contains 5 working-tree metadata regex parsers (`_ID_RE`, `_STATUS_RE`, `_SET_RE`, and 2 inline YAML regexes in `read_artifact_record`) to delete, and 4 transition metadata read sites (`_format_status_transition_line`, `plan_priority_work_kind_problems`, `read_item_dependencies_value`, and `_prepare_status_change`) to route onto `artifact_meta`.

### Step R2

- Checked: `E-*`/`V-*` 1:1 bijection (`E-04` <-> `V-04`, `E-05` <-> `V-05`), `- Highest E allocated: 05`, dependency order (`E-05` depends on `E-04`), `- Scope-Paths:` completeness (`3` paths, including the plan itself), and PIN-FIRST directory creation (`mkdir -p .aw/state/ffceq0 .aw/state/r81uvz`).
- Verified that `tests/test_artifact_meta_loader_parity.py` is properly included in `- Scope-Paths:` as the D-6 parity pin, and replaced vague test descriptions in `E-04`, `E-05`, `V-04`, and `V-05` with exact class-qualified pytest node IDs (`PR-003`).

### Step R3

- Checked: Security, access control, and query safety. Ensured that `status_set.py`'s transition validation continues to enforce gate validity, attestation integrity, and release-blocking checks using cached metadata without bypassing string safety or leak sanitization checks.
- Verified that `_sel.metadata_region` bounding is preserved (`D-4`) to prevent false-positive metadata extraction from markdown quotes or walk-through body text.

### Step R4

- Checked: Behavioral decisions and invariant preservation:
  1. `D-1`: Multi-word plan status normalization (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise); non-plan records retain exact single-token status.
  2. `D-2`: Preservation of strict internal reader grammar while tolerating loose whitespace in public readers.
  3. `D-3`: `short_description` precedence over `_extract_detail` fallback (`4sd62s` 4.4).
  4. `D-4`: Region-bounded reading; status bullets outside metadata regions are ignored.
  5. `D-5`: Record walkers skip `README.md`, `INDEX.md`, `STATUS.md`, and `records/meta/`.
  6. `D-6`: Filename-derived Set for records without in-file `- Set:` bullet, pinned by `tests/test_artifact_meta_loader_parity.py`.

### Step R5

- Checked: Architect (clean delegation of file-based inventory walks to `artifact_meta` SQLite query and cached states; preservation of `ArtifactRecord.raw_text` for body-prose consumers), Security/Integrity Reviewer (no bypass of release-blocking or gate validation during status transitions; region-bounded parsing), QA/QC Engineer (exact class-qualified pytest node IDs across 7 suites; PIN-FIRST regression coverage with empty outcome diff), Software Engineer (preservation of `_format_status_transition_line`'s `ArtifactRecord` signature for backward compatibility with existing tests; clean typing), and Modest Executor (two right-sized `E-*` items in a single task group, each within `IPD-Z603` bounds).

### Step R6

- Checked: `2` `E-*` items across `3` `- Scope-Paths:` entries (`2` work paths plus the plan file; `- Size assessment: standard`), satisfying `nj8zdp` and `IPD-Z603` bounds (`<=5` E-items, `<=8` work Scope-Paths, `0` advisories).

### Step R7

- Checked: `- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:cdglt1` (`tve77h` verified executed; `g5hpbb`, `xexn45`, and `cdglt1` verified in `metastore`), parent `ffceq0` (Order 08), sibling `cdglt1` (Order 142), orchestrator `63ib9r` (Order 00, H1 title kept exact to match row 27), and downstream plans `dqutt8` (Order 28) and `a5ijjx` (Order 140).
- Verified clean composition with `cdglt1` (which moves `selectors` and `aw find` reads ahead of this plan) and `ffceq0` (which keeps the final cache-parity and residual-audit checks).

### Step S5

- Checked: `OQ-01` (step-complexity limits satisfied at 11 and 14 units) and five technical decisions (`D-1`..`D-5` in `### Decisions` below, all `Reversible: yes`).
- Resolved all from repository code, `status_set.py`, and approved spec `4sd62s`. Zero questions belong to the human under the `askme` three-way sort.

### Pass 2

- Re-reviewed the complete revised plan per `steps/s6-rereview.md` rules 1 and 2 because `mkdir -p .aw/state/ffceq0 .aw/state/r81uvz` was added to `PIN-FIRST RULE`, `D-1` through `D-6` were documented, `V-04` and `V-05` gained exact test node IDs, and a Mermaid flowchart TD diagram was added.
- Verified `E-04..E-05` <-> `V-04..V-05` 1:1 bijection, `- Highest E allocated: 05`, dependency order (`E-04` -> `E-05`), `- Scope-Paths:` (`3` files), compliance with all 12 requirements of `.aw/system/workflows/technical-writing/technical-writing.md`, and `aw ipd lint --phase review-finalize --agent` (`outcome: clean`, `findings: 0`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | R1 / R4 / PIN-FIRST | `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md:36` | `PIN-FIRST RULE` redirected output to `.aw/state/ffceq0/` without explicitly running `mkdir -p .aw/state/ffceq0 .aw/state/r81uvz`, which would fail on fresh worktrees where the directory has not yet been created. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `mkdir -p .aw/state/ffceq0 .aw/state/r81uvz` to `PIN-FIRST RULE` (recommendation strength: very strong). |
| PR-002 | LOW | IN-SCOPE | Proofreading / Requirement 12(b) / Step 0 | `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md:57`, `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md:86` | `Proposed changes` lacked the Mermaid diagram required by Technical Writing Standard Requirement 12(b), and `Step 0` cited code using unqualified `module.function` symbols instead of repo-relative `path::Symbol` identifiers (`IPD-C801`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` diagram under `Proposed changes` and converted code citations to `path::Symbol` identifiers (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R4 / E-04, E-05, V-04, V-05 | `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md:133`, `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md:138` | `V-04` and `V-05` did not name specific class-qualified test node IDs, and `V-05` passed a blanket `-k "priority or bidirectional or deps"` filter across three test files that deselected 131 of 134 tests without naming the target methods. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified exact class-qualified pytest node IDs across `tests/test_status_set_metadata_region.py`, `tests/test_artifact_meta_loader_parity.py`, `tests/test_blocks_release_reader_bounding.py`, `tests/test_status_set.py`, and `tests/test_status_set_descriptive_safety.py` (recommendation strength: very strong). |
| PR-004 | MEDIUM | IN-SCOPE | R1 / R4 / Behavior decisions | `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md:82` | `## Findings` stated that decisions D-1 through D-6 were copied verbatim from `ffceq0`, but omitted D-1 through D-5, leaving the rules governing multi-word status, whitespace/YAML, detail text, region bounding, and skip lists unstated in this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expanded `## Findings` to document `D-1` through `D-6` with precise query and field mapping contracts (recommendation strength: very strong). |
| PR-005 | LOW | IN-SCOPE | R7 / S7 / Approval and execution gate | `.aw/records/plans/pending/20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md:148` | `Approval and execution gate` lacked a narrow stop directive if prerequisite symbols from `cdglt1`, `xexn45`, or `tve77h` (`artifact_meta.read`, `artifact_meta.query`, `artifact_meta.resolve`) are absent on HEAD, or if baseline test suites fail before the move, and lacked the explicit scope fence declaration wording. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a narrow unsafe-condition stop rule and scope fence declaration in `Approval and execution gate` (recommendation strength: strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `status_set.read_artifact_record` normalize plan status when reading from `artifact_meta`? | For PLAN records only, match `plans.normalize_status` of the FIRST token of the cached raw value (`executed` for `EXECUTED`/`DONE`, `legacy/unknown` otherwise); all other record types use exact single-token matching. | Use raw unnormalized status across all readers (preserves 24 multi-word plan disagreement); normalize all types through `plans.normalize_status` (corrupts non-plan vocabulary). | `agent_workflows/plans.py:normalize_status`, `agent_workflows/status_set.py:read_artifact_record`, `ffceq0` D-1, `4sd62s` Section 4.3 | yes |
| D-2 | How should `status_set.read_artifact_record` handle records with no in-file `- Set:` bullet? | Use the cache's filename-derived Set (from `artifact_meta`), matching `4sd62s` C1/C10 and maintainer decision on backlog `suth7l`. | Return `None` for Set when no in-file bullet exists (leaves 242 records unmatched by `aw set <setid>` and `aw find <setid>`). | `4sd62s` C1/C10, `tests/test_artifact_meta_loader_parity.py`, backlog `suth7l` | yes |
| D-3 | How should status bullets outside the metadata region be handled? | Region-bounded reading: bullets outside the metadata region are ignored. | Search entire file text for `- Status:` bullets (misidentifies quotes in review and walkthrough bodies). | `agent_workflows/selectors.py:metadata_region`, `ffceq0` D-4 | yes |
| D-4 | Should `_format_status_transition_line` change its parameter signature from `ArtifactRecord` to `State`? | Keep the `ArtifactRecord` signature for `_format_status_transition_line` (reading cached fields for `rec` internally), changing only internal text-taking helpers (`plan_priority_work_kind_problems`, `read_item_dependencies_value`) to accept `State`. | Change `_format_status_transition_line` to take `State` directly (breaks external callers like `tests/test_blocks_release_reader_bounding.py` and requires rewrites across transition callers). | `agent_workflows/status_set.py:_format_status_transition_line`, `tests/test_blocks_release_reader_bounding.py:101` | yes |
| D-5 | Where should PIN-FIRST baseline test outcomes be stored? | Keep `.aw/state/ffceq0/` as the baseline directory (with `mkdir -p .aw/state/ffceq0 .aw/state/r81uvz`), because split parent `ffceq0` retains the final cache-parity, residual-audit, and finishing comparisons against these files. | Divert baselines to `.aw/state/r81uvz/` (breaks parent `ffceq0`'s downstream residual audit and cache-parity comparisons). | `ffceq0` Task group 1, `20261102-metastore-08-ffceq0-...ipd.md` | yes |
