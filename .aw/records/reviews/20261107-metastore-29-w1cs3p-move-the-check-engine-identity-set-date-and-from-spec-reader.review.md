# Review findings: ipd w1cs3p

- Subject-Id: w1cs3p
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `3f4739758` in an isolated runner review-sweep lane worktree (non-interactive). The lane-input copy is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize` was clean after them. Baseline tests passed (`97 passed in 5.21s`).

### Proofreading

Checked `.aw/records/plans/pending/20261107-metastore-29-w1cs3p-move-the-check-engine-identity-set-date-and-from-spec-reader.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter, lines 7, 19-20 | Missing self plan path in `Scope-Paths:`; template instruction blockquote at line 20; missing `Review-Depth:` and `Readiness:` | Added self plan file to `Scope-Paths:`; removed scaffold blockquote; added `- Review-Depth: complex` and `- Readiness: go-pending-approval`; updated workflow history | PR-001. |
| `Detailed Implementation Checklist`, line 37 | Bash baseline redirect without ensuring parent directory exists | Prepended `mkdir -p .aw/state/ffceq0 && ` to command line | PR-002. |
| `Proposed changes` | Numbered list without diagram | Added Requirement 12 `flowchart TD` Mermaid diagram | PR-003. |
| `Approval and execution gate` | Execution rules without stop condition | Added standard stop-and-report safety clause for unexpected failures or unresolvable conflicts | PR-004. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: modifies `agent_workflows/check_engine.py` working-tree metadata reading across 16 core validation functions (26 site lines).
2. Yes: directly affects repository validation checks run by `aw check` (`check.id-missing`, `check_collisions`, `_identity_declared_values`, `check_id_outside_metadata_region`, `check_setid_length`, `find_lifecycle_placement_conflicts`, `is_retired`, `validate_prompt_content`, `build_plan_setid_index`, plan-date readers, `known_spec_ids`, `find_from_spec_plans`, `check_from_spec_dangling`, `check_plan_spec_link_missing`, `check_spec_criteria_uncovered`).
3. Cross-cutting across 16 validation functions in `check_engine.py` and Set `metastore` split parts Orders 29 to 32.
4. No: 6 Scope-Paths (including plan), 2 E-items, 1 task group (split under maintainer step-complexity rule).
5. Yes: a regression in `check_engine` identity, Set, or From-Spec readers could mask ID collisions, illegal transitions, or broken spec linkages across the repository.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/check_engine.py`, `tests/test_check_engine.py`, `tests/test_check_engine_metadata_region.py`, `tests/test_check_engine_from_spec_missing.py`, spec `4sd62s` section 7 step 5, sibling split plans `na188y` (Order 30), `i3b5zu` (Order 31), `ebrc4t` (Order 32), split parent `ffceq0` (Order 08), and prerequisites `g5hpbb`, `tve77h`, `xexn45`.
- Confirmed all 26 working-tree metadata read site lines across the 16 named functions in `agent_workflows/check_engine.py` at HEAD `3f4739758`:
  - `is_retired`: 1 site (`_read_plan_status`)
  - `validate_prompt_content`: 1 site (`_read_item_id`)
  - `check_collisions`: 2 sites (`_read_declared_id`, `_read_item_id`)
  - `find_lifecycle_placement_conflicts`: 2 sites (`_read_declared_id`, `_read_plan_status`)
  - `_artifact_compact_date`: 1 site (`_DATE_LINE_RE`)
  - `check_setid_length`: 1 site (`_parse_setid`)
  - `check_id_outside_metadata_region`: 1 site (`_ID_LINE_RE`)
  - `_identity_declared_values`: 3 sites (`_identity_metadata_region`, bullets / YAML values)
  - `find_from_spec_plans`: 2 sites (`_read_declared_id`, `_FROM_SPEC_LINE_RE`)
  - `build_plan_setid_index`: 3 sites (`_parse_setid`, `_read_declared_id`, `_read_plan_status`)
  - `_plan_date`: 1 site (`_DATE_LINE_RE`)
  - `known_spec_ids`: 1 site (`_read_declared_id`)
  - `check_from_spec_dangling`: 1 site (`_FROM_SPEC_LINE_RE`)
  - `check_plan_spec_link_missing`: 3 sites (`_read_declared_id`, `_read_plan_status`, `_FROM_SPEC_LINE_RE`)
  - `check_spec_criteria_uncovered`: 2 sites (`_read_declared_id`, `_read_plan_status`)
  - `_plan_date_compact`: 1 site (`_DATE_LINE_RE`)
- Empirically ran baseline suites `tests/test_check_engine.py`, `tests/test_check_engine_metadata_region.py`, and `tests/test_check_engine_from_spec_missing.py` (97 passed in 5.21s).
- Verified `tests/test_readers_check_engine.py` is newly created by this first partition plan (Order 29), and subsequent parts (Orders 30 to 32) append to it.

### Step R2

- Checked: 1:1 `E-*`/`V-*` bijection (`E-01..E-02` <-> `V-01..V-02`, `- Highest E allocated: 02`).
- Reachability: `V-01` verifies empty diff on `check_engine.py`, all passed in `tests/test_readers_check_engine.py`, line count of baseline output, and baseline rule counts in `.aw/state/ffceq0/`; `V-02` verifies zero diff between before and after test outcomes and rule counts.

### Step R3

- Checked security, isolation, and containment: reads go through `artifact_meta.read`, `query`, and `history`. No write side is touched.
- Test module uses `tmp_path` fixtures through public CLI `aw check <type> --agent` without modifying repository history or primary checkouts.
- Baseline state directory `.aw/state/ffceq0/` is gitignored and survives lane integration.

### Step R4

- Verified reader contracts against `4sd62s` section 7 step 5.
- Confirmed body-prose bullet scanning (`Concern`, `Scope`, `Scope-Paths`, `Carrier*` bullets) is excluded from `artifact_meta` and remains unperturbed in `check_engine.py` per N3 and `ffceq0` E-14.
- Confirmed status normalization follows `D-1` (`plans.normalize_status`) and region-bounded reading follows `D-4`.

### Step R5

- Evaluated against the eight reviewer personas:
  - QA/QC & Testing: verified baseline suite runtimes and 97-test count; verified `mkdir -p .aw/state/ffceq0` prevents lane failures.
  - Performance & Budget: baseline test execution completes in 5.21s, well within budgets.
  - Architect & Software Engineer: verified all 26 site lines across 16 functions map directly to `artifact_meta` query and read operations.
  - Technical Writer: eliminated instructional blockquote, added Requirement 12 Mermaid diagram, added standard safety clause.

### Step R6

- Decomposition check: 2 `E-*` items in 1 task group, 26 site lines, 6 Scope-Paths (including plan). Well within `IPD-Z603` limits (exit 0 from `aw ipd lint`). No further split needed.

### Step R7

- Cross-plan consistency: checked against sibling split plans `na188y` (Order 30, 24 site lines), `i3b5zu` (Order 31, 23 site lines), `ebrc4t` (Order 32, 23 site lines), split parent `ffceq0` (Order 08, 93 working-tree site lines total), git-reader plan `t4gl15` (Order 09), and orchestrator `63ib9r`. All 93 working-tree site lines are accounted for across Orders 29 to 32 without gaps or overlaps.

### Step S5

- Evaluated `OQ-01` (resolved, step complexity fits). Zero open questions remain. All findings `FIXED` in place. No human decision required (`questions: []`).

### Pass 2

- Verified `aw ipd lint --phase author --agent` clean (0 findings).
- Verified `aw ipd lint --phase review-finalize --agent` clean (0 findings).
- Verified zero em or en dashes, zero absolute paths, zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | LOW | IN-SCOPE | Proofreading / Front Matter | `.aw/records/plans/pending/20261107-metastore-29-w1cs3p-move-the-check-engine-identity-set-date-and-from-spec-reader.ipd.md:7,19-20` | Plan omitted itself from `Scope-Paths:` (which would trigger out-of-scope refusal during `aw commit w1cs3p`); line 20 contained scaffold blockquote; front matter lacked `- Review-Depth: complex` and `- Readiness: go-pending-approval` | Low | FIXED | Added self plan file to `Scope-Paths:`; removed scaffold blockquote; added `- Review-Depth: complex` and `- Readiness: go-pending-approval`; updated workflow history. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / R2 | `.aw/records/plans/pending/20261107-metastore-29-w1cs3p-move-the-check-engine-identity-set-date-and-from-spec-reader.ipd.md:37` | Baseline saving recipe redirected output to `.aw/state/ffceq0/<E>-before.txt` without ensuring directory exists, causing shell redirection failure in clean/isolated worktrees | Low | FIXED | Prepended `mkdir -p .aw/state/ffceq0 && ` to command line in checklist. |
| PR-003 | LOW | IN-SCOPE | Technical Writing Requirement 12 | `.aw/records/plans/pending/20261107-metastore-29-w1cs3p-move-the-check-engine-identity-set-date-and-from-spec-reader.ipd.md:99-103` | `Proposed changes` lacked a Mermaid diagram illustrating the execution sequence | Low | FIXED | Added a `flowchart TD` Mermaid diagram showing `E01 -> E02`. |
| PR-004 | LOW | IN-SCOPE | S7 Contract / Safety | `.aw/records/plans/pending/20261107-metastore-29-w1cs3p-move-the-check-engine-identity-set-date-and-from-spec-reader.ipd.md:153-164` | Approval gate lacked an explicit stop-and-report clause for unexpected test failures or unresolvable concurrent-edit conflicts | Low | FIXED | Added standard stop-and-report safety clause to the approval gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-001 | How should plan status normalization behave in `check_engine` readers? | Adhere to `plans.normalize_status` for plan records, raw single-token for other types | Universal normalization or raw token across all types | Preserves behavior across non-plan record types (`ffceq0` D-1, `plans.py:normalize_status`) | yes |
| D-002 | How should baseline redirection handle the state directory in fresh worktrees? | Prepend `mkdir -p .aw/state/ffceq0 && ` to output redirection command | Require prior manual directory creation | Ensures automated test baseline capture succeeds in clean/isolated worktrees | yes |
