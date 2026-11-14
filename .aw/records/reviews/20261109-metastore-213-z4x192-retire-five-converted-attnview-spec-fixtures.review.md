# Review findings: ipd z4x192

- Subject-Id: z4x192
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8fef56647` in an isolated runner review-sweep lane worktree. The lane-input
copy is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review
snapshot was needed. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize`
was clean after them. Pass 1 and Pass 2 verified the plan against governing spec `4sd62s` (Section 6, Section 7 step 6), orchestrator `63ib9r` (row 213), origin plan `9rgn2w` (E-10), research guidance `nj8zdp`, prerequisite `7fpc8v` (Order 174), and successor `9zcuyh` (Order 214).

### Proofreading

Checked `.aw/records/plans/pending/20261109-metastore-213-z4x192-retire-five-converted-attnview-spec-fixtures.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Line 20, front matter | Scaffold blockquote instruction; missing `Review-Depth:` and `Readiness:` | Replaced line 20 with standard compliance blockquote; added `- Review-Depth: standard` and `- Readiness: go-pending-approval` | PR-001. |
| `E-26`, `E-27`, `V-26`, `V-27` | Demanded `rg -n "specs-valid" tests` (no reader), which matches non-test documentation and literal fixtures | Clarified reader check to target test files `tests/test_*.py`, noting `tests/fixtures/attnview/README.md` is owned by Order 214 (`9zcuyh`) and `tests/fixtures/review-pilot/` is kept literal | PR-002. |
| `E-28`, `V-28`, `Findings`, `Required tests / validation` | Referenced batch-rule step-2 command without providing exact pipeline; lacked baseline test counts | Explicitly specified batch-rule step-2 command pipeline and added baseline test measurements (27 passed in `test_attention_contract.py`, 20 in `test_specs_verbs.py`, 14 in `test_specs_releases_unsafe_field.py`, 61 passed total) in `F-43` and `Required tests / validation` | PR-003. |
| `Proposed changes` | Numbered list without Mermaid diagram | Added Requirement 12 `flowchart TD` Mermaid diagram | PR-001. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Deletes 5 test fixture files (`tests/fixtures/attnview/specs-valid/*.md`) that are no longer referenced by test modules after Order 174 (`7fpc8v`).
2. No. Touches no code guarding private data, commits, worktree isolation, merges to main, or the sandbox.
3. No. 3 E-items across 2 task groups, deleting 5 fixture files in `tests/fixtures/attnview/specs-valid/`.
4. No. Lists 6 Scope-Paths (5 fixture files to delete and the plan itself).
5. No. Test fixture files only, no production code touched, easily reversible via git.

AW-TIER: standard

### Step R1

- Checked: `tests/fixtures/attnview/specs-valid/` contains 9 files (`approved.md`, `deferred.md`, `draft.md`, `implemented.md`, `implementing.md`, `parked.md`, `reviewed.md`, `superseded.md`, `to-review.md`).
- Checked: The 5 files to be deleted in `z4x192` (`approved.md`, `deferred.md`, `draft.md`, `implemented.md`, `implementing.md`) exist on disk at HEAD `8fef56647`.
- Checked: The remaining 4 files (`parked.md`, `reviewed.md`, `superseded.md`, `to-review.md`) and `tests/fixtures/attnview/README.md` are scheduled for deletion/update in Order 214 (`9zcuyh`).
- Checked: Prerequisite `7fpc8v` (Order 174) converts consumers in `tests/test_attention_contract.py`, `tests/test_specs_verbs.py`, and `tests/test_specs_releases_unsafe_field.py` to use `RecordBuilder.spec(...)`.
- Checked: All dependencies in `- Item-Dependencies:` (`g5hpbb`, `tve77h`, `xexn45`, `j6o96i`, `7fpc8v`) resolve in `.aw/records/plans/` and match orchestrator `63ib9r` row 213.

### Step R2

- Checked: 1:1 `E-*`/`V-*` bijection is exact (`E-26..E-28` <-> `V-26..V-28`), and `- Highest E allocated: 28` matches.
- Reachability: `V-26` and `V-27` verify deleted fixtures via `git status --short` and absence of test readers via `rg`; `V-28` verifies test counts of all three consumer modules, runs the core gate `python3 -m pytest`, and checks path-scoped commits.

### Step R3

- Checked: No production code or credentials touched. Fixture deletions under `tests/fixtures/attnview/specs-valid/` cannot leak private data or compromise worktree isolation.
- Commits are path-scoped to `- Scope-Paths:`. `aw sanitize --agent` runs clean.

### Step R4

- A (State & atomicity): Fixture deletions are tracked via git; commits are path-scoped.
- C (Architecture & operability): Retires dead legacy fixtures in phase B per spec `4sd62s` Section 6 and Section 7 step 6, preventing unnecessary format conversion at cutover.
- D & E (Anti-regression & verification): Validated by running the three consumer test suites and the bare core gate `python3 -m pytest`.
- Spec sync: Directly implements the fixture retirement part of `4sd62s` section 6.

### Step R5

- Checked through review personas:
  - QA / QC: Verified that Order 174 prerequisite ensures no test fails from premature fixture deletion.
  - Test Engineer: Verified test counts (61 passed across the 3 consumer modules).
  - Technical Writer: Replaced template boilerplate with standard compliance blockquote and added Requirement 12 Mermaid diagram.

### Step R6

- Decomposition check: 3 E-items in 2 task groups, 5 work Scope-Paths. Partitioned cleanly from parent `9rgn2w` under research `nj8zdp` guidance (plans of at most 8 files). No further split needed.

### Step R7

- Cross-plan consistency: Verified coordination across Set metastore:
  - Prerequisite `7fpc8v` (Order 174) converts consumers.
  - Current plan `z4x192` (Order 213) deletes 5 fixtures.
  - Successor plan `9zcuyh` (Order 214) deletes the remaining 4 fixtures and updates `tests/fixtures/attnview/README.md`.
  - Orchestrator `63ib9r` row 213 and row 214 reflect this exact sequence.

### Step S5

- Checked: OQ-01 carried from `59aiyh` is resolved. No open questions remain. All findings `FIXED` in place. No human decision needed.

### Pass 2

- Verified `aw ipd lint --phase author --agent` clean (0 findings).
- Verified `aw ipd lint --phase review-finalize --agent` clean (0 findings).
- Verified zero em or en dashes, zero absolute file paths, zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | LOW | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261109-metastore-213-z4x192-retire-five-converted-attnview-spec-fixtures.ipd.md:20` | Authoring template prompt blockquote present; missing front-matter metadata (`- Review-Depth: standard`, `- Readiness: go-pending-approval`); `Proposed changes` lacked a Requirement 12 Mermaid diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template line with standard compliance blockquote, added `- Review-Depth: standard` and `- Readiness: go-pending-approval` to front matter, and added `flowchart TD` Mermaid diagram to `Proposed changes`. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / R2 Executability | `.aw/records/plans/pending/20261109-metastore-213-z4x192-retire-five-converted-attnview-spec-fixtures.ipd.md:38,43,115,120` | `E-26`, `E-27`, `V-26`, and `V-27` demanded `rg -n "specs-valid" tests (no reader)`, which matches `tests/fixtures/attnview/README.md` (updated in Order 214 `9zcuyh`) and literal `review-pilot/` fixtures (kept literal), creating an apparent verification failure for executors. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Clarified reader verification in `E-26`, `E-27`, `V-26`, and `V-27` to target test files `tests/test_*.py`, noting that fixture README updates are owned by Order 214 (`9zcuyh`) and `tests/fixtures/review-pilot/` is kept literal. |
| PR-003 | LOW | IN-SCOPE | R1 / R2 Executability | `.aw/records/plans/pending/20261109-metastore-213-z4x192-retire-five-converted-attnview-spec-fixtures.ipd.md:50,125` | `E-28` and `V-28` referenced the batch-rule step-2 command without providing the exact command line, and the plan lacked baseline test outcome counts for the three consumer modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Explicitly documented the batch-rule step-2 pytest command pipeline in `E-28` and `Required tests / validation`, and recorded baseline counts (27 passed in `test_attention_contract.py`, 20 in `test_specs_verbs.py`, 14 in `test_specs_releases_unsafe_field.py`, 61 passed total) in `Findings` (`F-43`) and `Required tests / validation`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should the non-reader check in `E-26`, `E-27`, `V-26`, and `V-27` be specified? | Target test modules (`tests/test_*.py`) and acknowledge non-test matches in `tests/fixtures/attnview/README.md` (owned by Order 214 `9zcuyh`) and `tests/fixtures/review-pilot/` (kept literal) | Keep bare unqualified `rg -n "specs-valid" tests (no reader)` or modify `tests/fixtures/attnview/README.md` in this plan | Plan scope exclusions, Order 214 scope ownership, and `tests/fixtures/attnview/README.md` contents | yes |
| D-2 | How should the batch-rule step-2 command and consumer test expectations be documented? | Explicitly specify the deterministic pytest command pipeline and record measured baseline counts (61 passed across the 3 modules) | Leave command and test counts implicit | `y3uowx` E-03 definition and live measured test suite execution at HEAD `8fef56647` | yes |
