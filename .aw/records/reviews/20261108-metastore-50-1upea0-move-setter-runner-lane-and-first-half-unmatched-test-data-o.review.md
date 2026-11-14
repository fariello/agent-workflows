# Review findings: plan 1upea0

- Subject-Id: 1upea0
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `2f210f95f` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), and the reference baseline suite (`pytest` on all 8 target test modules) passed (`73 passed in 15.79s`). Live inspection against governing spec `4sd62s` section 6 and section 7 step 6, predecessor plans `653ndz` (Order 49) and `9rgn2w` (Order 37), the 7 chunk plans (`2ll84l`, `9hk3rh`, `5mg9g1`, `1cgrgp`, `z8hu7r`, `tsonlq`, `erulw3`), the 8 kept test modules in `tests/`, and the batch rule uncovered findings `PR-001..PR-006`, all fixed in place. Pass 2 re-checked `E-03`, `E-05`, `E-04` and `V-03`, `V-05`, `V-04`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

Checked `.aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted explicit hand-mv guard, conditional runner/executor finalize clause, and safety rule | Added explicit `never a hand git mv`, conditional runner/executor ownership clause, and standard safety rule | PR-001, Technical Writing Standard Requirement 1. |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Updated to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) | PR-002, `steps/s5-questions.md` owner attestation standard. |
| Proposed changes (ordered, validatable) | Numbered list without process diagram | Added Mermaid `flowchart TD` diagram showing batch progression and task flow | PR-003, Technical Writing Standard Requirement 12(b). |
| Line 20, front matter | Unremoved authoring template prompt blockquote; missing `Review-Depth:` and `Readiness:`; status `to-review` | Replaced template line with standard compliance blockquote; added `- Review-Depth: complex` and `- Readiness: go-pending-approval`; updated status to `reviewed` and updated workflow history | PR-004, Step S7 review output requirements. |
| Batch rule step 1 | Piped directly into `.aw/state/59aiyh/<batch>-files.txt` without ensuring directory exists | Added `mkdir -p .aw/state/59aiyh` to guarantee directory existence on fresh worktrees | PR-005, R2 executability. |
| Findings & Required tests | Missing characterization test baseline counts for the 8 target test modules | Added F-42 baseline row (73 passed in 15.79s at HEAD `2f210f95f`) and documented baseline summary in `## Required tests / validation` | PR-006, R4 engineering rubric. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `1upea0` converts 8 unmatched test modules of subset G7a to use `tests/record_builder.py` via the Order-49 codemod (`653ndz`), catches any late partition modules for subsets G3a/G5a/G7a, and closes those subsets.
2. No. Standalone test fixture conversion; touches test files only.
3. No. Right-sized after the round-3 split at 3 E-items in 2 task groups across 8 test files.
4. Yes. `- Scope-Paths:` explicitly declares all 8 test module paths plus the plan itself.
5. Yes. Test outcome preservation: per-test outcomes must remain identical before and after conversion.

AW-TIER: complex

### Step R1

- Checked: governing spec `4sd62s` (section 6 and section 7 step 6); parent orchestrator `63ib9r` (row 50); research `nj8zdp` guidance; all 7 chunk plans (`2ll84l`, `9hk3rh`, `5mg9g1`, `1cgrgp`, `z8hu7r`, `tsonlq`, `erulw3`); and the 8 target test modules in `tests/`.
- Checked: All 8 test modules exist on disk at HEAD `2f210f95f` (`tests/test_generators_writing_standard_pointer.py`, `tests/test_generic_color_depth.py`, `tests/test_id6_global_mint.py`, `tests/test_identity_rename_hint.py`, `tests/test_index_check_agent_records.py`, `tests/test_index_rebuild.py`, `tests/test_index_write_agent_records.py`, `tests/test_inlane_retirement_lands.py`).
- Checked: All dependencies in `- Item-Dependencies:` (`653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `2ll84l`, `9hk3rh`, `5mg9g1`, `1cgrgp`, `z8hu7r`, `tsonlq`, `erulw3`) resolve under `.aw/records/plans/` and match orchestrator `63ib9r` row 50.
- Checked: Baseline pytest run across all 8 target modules confirmed 73 passed in 15.79s.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-03, E-05, E-04` <-> `V-03, V-05, V-04`, with `- Highest E allocated: 05` preserved), dependency chain (`E-03, E-05 -> E-04`), `- Scope-Paths:` completeness (all 8 target modules and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause, hand-mv guard, and safety rule in Approval and execution gate (`PR-001`). Fixed in Gate.
- Found missing state directory initialization in Batch rule step 1 (`PR-005`). Fixed by adding `mkdir -p .aw/state/59aiyh`.

### Step R3

- Checked: safety, test outcome invariance, refusal count threshold (at most 25 hand conversions before stop), and rollback semantics. Verified that outcome list diffs must be empty and that `raw_fields=` is used only for deliberate invalid-input tests.
- Commits are path-scoped to `- Scope-Paths:`. `aw sanitize --agent` runs clean.

### Step R4

- A (State & atomicity): Out-of-tree state files under `.aw/state/59aiyh/` ensure before/after outcome lists are compared deterministically.
- C (Architecture & operability): Moves test data onto `tests/record_builder.py` in phase B per spec `4sd62s` section 6 and section 7 step 6, preparing for format cutover in Order 13 (`cxxmyv`).
- D & E (Anti-regression & verification): Batch rule enforces identical per-test outcome lists before and after; hand conversions are capped at 25 per item; late partition modules caught in E-04. Added baseline characterization measurements (`PR-006`).
- Spec sync: Implements test data conversion for 8 unmatched test modules under `4sd62s` section 6.

### Step R5

- Checked through review personas:
  - QA / QC: Verified identical per-test outcome lists guarantee zero test regressions across all 73 tests.
  - Test Engineer: Verified clean helper cleanup and format-independent record building.
  - Technical Writer: Added Requirement 12 Mermaid flowchart and replaced authoring prompt boilerplate with standard compliance blockquote.

### Step R6

- Decomposition check: 3 E-items in 2 task groups, 8 work Scope-Paths. Cleanly chunked from original 57 modules across 7 chunk plans and this finishing plan per research `nj8zdp` guidance. Right-sized, no further decomposition needed.

### Step R7

- Checked: `- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:2ll84l, executed:9hk3rh, executed:5mg9g1, executed:1cgrgp, executed:z8hu7r, executed:tsonlq, executed:erulw3` (all verified under `.aw/records/plans/`), and cutover plan `cxxmyv`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded four engineering decisions (`D-1..D-4`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain (`questions: []`).

### Pass 2

- Re-reviewed `E-03`, `E-05`, `E-04` and `V-03`, `V-05`, `V-04` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and formatting decisions.
- Verified 3-to-3 `E-*`/`V-*` bijection, `- Highest E allocated: 05`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md:188-200 | Approval and execution gate omitted the explicit hand-mv guard, conditional runner/executor finalize clause, and safety rule, required by steps/s7-finalize.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction, conditional runner/executor ownership clause, and safety rule to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md:160 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md:112 | Proposed changes lacked a Mermaid diagram required by requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing batch flow. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / Front Matter | .aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md:20 | Unremoved authoring template prompt blockquote and missing front-matter metadata (- Review-Depth: complex, - Readiness: go-pending-approval). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template line with standard compliance blockquote, added - Review-Depth: complex and - Readiness: go-pending-approval, set Status: reviewed, and updated history. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | R2 / R4 Batch Rule | .aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md:40 | Batch rule step 1 redirected output to .aw/state/59aiyh/<batch>-files.txt without ensuring directory exists, which fails on clean/fresh worktrees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added mkdir -p .aw/state/59aiyh to batch rule step 1 command. Recommendation strength: strong. |
| PR-006 | LOW | IN-SCOPE | R4 Engineering Rubric / Characterization baseline | .aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md:88 | Plan lacked explicit characterization test baseline counts for the 8 target test modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-42 characterization baseline row (73 passed in 15.79s at HEAD 2f210f95f) and documented baseline summary in ## Required tests / validation. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Can 1upea0 execute in any order relative to other batch parts? | Yes. Kept modules and chunk plans are disjoint; depends on chunk plans only so E-04 catch-up sees their conversions. | Impose strict serial ordering across all chunk plans (rejected: unnecessary serialization of independent test files). | OQ-01, research `nj8zdp` | yes |
| D-2 | What is the threshold for halting hand conversions? | Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting. | Attempt unbounded manual conversions (rejected: high risk of agent mistakes and drift). | `1upea0` Batch rule step 4, research `nj8zdp` | yes |
| D-3 | How should directory creation be handled for `.aw/state/59aiyh/` in fresh lane worktrees? | Prepend `mkdir -p .aw/state/59aiyh && ` in step 1 of the batch rule. | Assume pre-existing directory (rejected: causes bash redirection failure in clean worktrees). | `1upea0` Batch rule step 1, clean worktree directory verification | yes |
| D-4 | Why are E-items numbered E-03, E-05, E-04? | Preserves round-3 split allocation integrity (`- Highest E allocated: 05`) where E-01 and E-02 moved to chunk plans, E-03 was retained and partitioned into E-03 and E-05, and E-04 is the finishing item. | Renumber items to E-01..E-03 (rejected: breaks historical traceability with predecessor plan nbfg7w). | `1upea0` Split note, `63ib9r` row 50 | yes |
