# Review findings: ipd 9zcuyh

- Subject-Id: 9zcuyh
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `94b265b77` in an isolated runner review-sweep lane worktree. The lane-input copy is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize` was clean after them. Pass 1 and Pass 2 verified the plan against governing spec `4sd62s` (Section 6, Section 7 step 6), orchestrator `63ib9r` (row 214), origin plan `9rgn2w` (E-10), research guidance `nj8zdp`, prerequisite `7fpc8v` (Order 174), and prerequisite `z4x192` (Order 213).

### Proofreading

Checked `.aw/records/plans/pending/20261109-metastore-214-9zcuyh-retire-four-converted-attnview-spec-fixtures-and-update-the.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Line 20, front matter | Scaffold blockquote instruction; missing `Review-Depth:` and `Readiness:`; status `to-review` | Replaced line 20 with standard compliance blockquote; added `- Review-Depth: standard` and `- Readiness: go-pending-approval`; updated status to `reviewed` | PR-001. |
| `E-29`, `E-30`, `V-29`, `V-30` | Demanded `rg -n "specs-valid" tests` (no reader), which matches `tests/fixtures/attnview/README.md` and literal `review-pilot/` fixtures | Clarified reader check to target test files `tests/test_*.py`, noting `tests/fixtures/attnview/README.md` is updated in `E-31` and `tests/fixtures/review-pilot/` is kept literal | PR-002. |
| `E-31`, `V-31`, `Findings`, `Required tests / validation` | Referenced batch-rule step-2 command without providing exact pipeline; lacked baseline test counts | Explicitly specified batch-rule step-2 command pipeline and added baseline test measurements (27 passed in `tests/test_attention_contract.py`, 20 in `tests/test_specs_verbs.py`, 14 in `tests/test_specs_releases_unsafe_field.py`, 61 passed total) in `F-43` and `Required tests / validation` | PR-003. |
| `Proposed changes` | Numbered list without Mermaid diagram | Added Requirement 12 `flowchart TD` Mermaid diagram | PR-001. |
| `Approval and execution gate` | Execution rules without stop condition | Added standard stop-and-report safety clause for unexpected failures or unresolvable conflicts | PR-004. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Deletes 4 test fixture files (`tests/fixtures/attnview/specs-valid/*.md`) that are no longer referenced by test modules after Order 174 (`7fpc8v`) and updates `tests/fixtures/attnview/README.md`.
2. No. Touches no code guarding private data, commits, worktree isolation, merges to main, or the sandbox.
3. No. 3 E-items across 2 task groups, deleting 4 fixture files and updating 1 README.
4. No. Lists 6 Scope-Paths (4 fixture files to delete, README.md, and the plan itself).
5. No. Test fixture files and documentation only, no production code touched, easily reversible via git.

AW-TIER: standard

### Step R1

- Checked: `tests/fixtures/attnview/specs-valid/` contains the 4 files to delete (`parked.md`, `reviewed.md`, `superseded.md`, `to-review.md`).
- Checked: `tests/fixtures/attnview/README.md` exists and describes the fixtures.
- Checked: `tests/test_attention_contract.py`, `tests/test_specs_verbs.py`, and `tests/test_specs_releases_unsafe_field.py` exist on disk and will be converted by prerequisite `7fpc8v` (Order 174).
- Checked: Prerequisite `z4x192` (Order 213) retires the other 5 fixtures (`approved.md`, `deferred.md`, `draft.md`, `implemented.md`, `implementing.md`).
- Checked: All dependencies in `- Item-Dependencies:` (`g5hpbb`, `tve77h`, `xexn45`, `j6o96i`, `7fpc8v`, `z4x192`) resolve in `.aw/records/plans/` and match orchestrator `63ib9r` row 214.

### Step R2

- Checked: 1:1 `E-*`/`V-*` bijection is exact (`E-29..E-31` <-> `V-29..V-31`), and `- Highest E allocated: 31` matches.
- Reachability: `V-29` and `V-30` verify deleted fixtures via `git status --short` and absence of test readers via `rg`; `V-31` verifies diff of `tests/fixtures/attnview/README.md`, test counts of all three consumer modules (27, 20, 14; 61 passed), runs the core gate `python3 -m pytest`, and checks path-scoped commits.

### Step R3

- Checked: No production code or credentials touched. Fixture deletions and doc updates cannot leak private data or compromise worktree isolation.
- Commits are path-scoped to `- Scope-Paths:`. `aw sanitize --agent` runs clean.

### Step R4

- A (State & atomicity): Fixture deletions and README updates are tracked via git; commits are path-scoped.
- C (Architecture & operability): Retires dead legacy fixtures in phase B per spec `4sd62s` Section 6 and Section 7 step 6, preventing unnecessary format conversion at cutover.
- D & E (Anti-regression & verification): Validated by running the three consumer test suites and the bare core gate `python3 -m pytest`.
- Spec sync: Directly implements the fixture retirement and README update part of `4sd62s` section 6.

### Step R5

- Checked through review personas:
  - QA / QC: Verified that Order 174 and Order 213 prerequisites ensure no test fails from premature fixture deletion.
  - Test Engineer: Verified test counts (61 passed across the 3 consumer modules).
  - Technical Writer: Replaced template boilerplate with standard compliance blockquote, added Requirement 12 Mermaid diagram, added standard safety clause.

### Step R6

- Decomposition check: 3 E-items in 2 task groups, 5 work Scope-Paths. Partitioned cleanly from parent `9rgn2w` under research `nj8zdp` guidance (plans of at most 8 files). No further split needed.

### Step R7

- Cross-plan consistency: Verified coordination across Set metastore:
  - Prerequisite `7fpc8v` (Order 174) converts consumers.
  - Prerequisite `z4x192` (Order 213) deletes 5 fixtures.
  - Current plan `9zcuyh` (Order 214) deletes the remaining 4 fixtures and updates `tests/fixtures/attnview/README.md`.
  - Orchestrator `63ib9r` rows 174, 213, and 214 reflect this exact sequence.

### Step S5

- Checked: OQ-01 carried from `59aiyh` is resolved. No open questions remain. All findings `FIXED` in place. No human decision needed (`questions: []`).

### Pass 2

- Verified `aw ipd lint --phase author --agent` clean (0 findings).
- Verified `aw ipd lint --phase review-finalize --agent` clean (0 findings).
- Verified zero em or en dashes, zero absolute file paths, zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | LOW | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261109-metastore-214-9zcuyh-retire-four-converted-attnview-spec-fixtures-and-update-the.ipd.md:20` | Authoring template prompt blockquote present; missing front-matter metadata (`- Review-Depth: standard`, `- Readiness: go-pending-approval`); `Proposed changes` lacked a Requirement 12 Mermaid diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template line with standard compliance blockquote, added `- Review-Depth: standard` and `- Readiness: go-pending-approval` to front matter, updated status to `reviewed`, and added `flowchart TD` Mermaid diagram to `Proposed changes`. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / R2 Executability | `.aw/records/plans/pending/20261109-metastore-214-9zcuyh-retire-four-converted-attnview-spec-fixtures-and-update-the.ipd.md:38,43,115,120` | `E-29`, `E-30`, `V-29`, and `V-30` demanded `rg -n "specs-valid" tests (no reader)`, which matches `tests/fixtures/attnview/README.md` (updated in E-31) and literal `review-pilot/` fixtures (kept literal), creating an apparent verification failure for executors. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Clarified reader verification in `E-29`, `E-30`, `V-29`, and `V-30` to target test files `tests/test_*.py`, noting that non-test occurrences in literal `tests/fixtures/review-pilot/` fixtures are kept literal and `tests/fixtures/attnview/README.md` is updated in `E-31`. |
| PR-003 | LOW | IN-SCOPE | R1 / R2 Executability | `.aw/records/plans/pending/20261109-metastore-214-9zcuyh-retire-four-converted-attnview-spec-fixtures-and-update-the.ipd.md:50,125` | `E-31` and `V-31` referenced the batch-rule step-2 command without providing the exact command line, and the plan lacked baseline test outcome counts for the three consumer modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Explicitly documented the batch-rule step-2 pytest command pipeline in `E-31` and `Required tests / validation`, and recorded baseline counts (27 passed in `tests/test_attention_contract.py`, 20 in `tests/test_specs_verbs.py`, 14 in `tests/test_specs_releases_unsafe_field.py`, 61 passed total) in `Findings` (`F-43`) and `Required tests / validation`. |
| PR-004 | LOW | IN-SCOPE | S7 Contract / Safety | `.aw/records/plans/pending/20261109-metastore-214-9zcuyh-retire-four-converted-attnview-spec-fixtures-and-update-the.ipd.md:136-141` | Approval gate lacked an explicit stop-and-report safety clause for unexpected test failures or unresolvable concurrent-edit conflicts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard stop-and-report safety clause to the approval gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should the non-reader check in `E-29`, `E-30`, `V-29`, and `V-30` be specified? | Target test modules (`tests/test_*.py`) and acknowledge non-test matches in `tests/fixtures/attnview/README.md` (updated in E-31) and `tests/fixtures/review-pilot/` (kept literal) | Keep bare unqualified `rg -n "specs-valid" tests (no reader)` or modify `tests/fixtures/review-pilot/` | Plan scope exclusions, Order 214 scope ownership, and `tests/fixtures/attnview/README.md` contents | yes |
| D-2 | How should the batch-rule step-2 command and consumer test expectations be documented? | Explicitly specify the deterministic pytest command pipeline and record measured baseline counts (61 passed across the 3 modules) | Leave command and test counts implicit | `y3uowx` E-03 definition and live measured test suite execution at HEAD `94b265b77` | yes |
