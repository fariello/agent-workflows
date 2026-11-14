# Review findings: plan 545ag7

- Subject-Id: 545ag7
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated runner review-sweep lane worktree. Working tree was clean at turn start (`pre-review snapshot: skipped unchanged`). Pass 1 and Pass 2 verified the plan against governing spec `4sd62s` (C10a, AC-1b), orchestrator `63ib9r` (row 262, E-184), origin plan `iog3cw`, and sibling plan `j5fqax`.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Line 20, front matter | Scaffold blockquote instruction; missing `Review-Depth:` and `Readiness:` | Removed scaffold line; added `- Review-Depth: standard` and `- Readiness: go-pending-approval` | PR-001. |
| Batch rule step 1 | Piped directly into `.aw/state/545ag7/<batch>-before.txt` | Prepended `mkdir -p .aw/state/545ag7 && ` to guarantee directory existence on fresh worktrees | PR-002. |
| `Proposed changes` | Numbered list without diagram | Added Requirement 12 `flowchart TD` Mermaid diagram | PR-003. |
| `Open questions` | Resolved `OQ-01` had `- Owner: none` | Changed to `- Owner: plan author` | PR-004. |
| `Approval and execution gate` | Standard gate without explicit stop conditions or runner ownership | Added explicit stop-and-report clause, shared-checkout safety, and conditional runner/executor `aw ipd finalize` ownership (`never a hand git mv`) | PR-005. |
| `Project conventions discovered` | Omitted candidate assertion classification breakdown | Documented 23 convertible setter-byte assertions vs 5 unconverted legacy-format subject assertions | PR-006. |

#### Issues

- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`. Zero em or en dashes appear in the plan or this review record (`IPD-C802`). Recommendation strength for remaining prose conformance: strong.

### Step T

1. No. The plan converts internal test assertions to use the format-aware field helper; it does not alter a public interface, schema, or system contract.
2. No. It changes no authorization gate, permission check, policy predicate, sandbox boundary, or lock protocol.
3. No. It has 3 `E-*` items in 1 task group (`E-01` S01a, `E-02` S01b, `E-03` finish and assemble).
4. No. It declares 8 work Scope-Paths, all test modules in `tests/`.
5. No. Only test code is touched. If a test assertion is wrong, pytest catches it during the batch before/after diff.

AW-TIER: standard

### Step R1

- Checked: All eight test modules in `- Scope-Paths:` exist on disk and pass under pytest (`221 passed in 17.17s` at HEAD).
- Checked: The 28 candidate assertion lines matching the F-28 pattern at `ac76110f4` break down into:
  - 23 convertible setter-byte assertions across 6 modules (`tests/test_agy_runipd_cli.py`: 1, `tests/test_artifact_group.py`: 12, `tests/test_artifact_rename.py`: 1, `tests/test_awcmdsurf_mutation_verbs.py`: 2, `tests/test_backlog_already_complete.py`: 1, `tests/test_backlog_close_evidence_plan_disposition.py`: 6).
  - 5 `legacy-format subject` assertions that test the legacy grammar or parser directly: `tests/test_attention_priority_blocker.py` (4 lines testing `attention.read_readiness` parser on literal strings) and `tests/test_attention.py` (line 3509 testing synthetic string buffer index offsets for chunk window straddling). These remain unconverted per batch rule step 2.
- Checked: All dependencies in `- Item-Dependencies:` (`1ajqaa`, `59aiyh`, `90iqr1`, `dcerjg`, `g5hpbb`, `ya4ee4`, `j5fqax`) resolve in `.aw/records/plans/` and match orchestrator `63ib9r` row 262.
- Checked: All carriers in `Deferred / out of scope` (`j5fqax`, `iog3cw`, `x1mmdp`) resolve in `.aw/records/plans/` and match their split roles (`j5fqax` adds helper and batch S04; `iog3cw` owns S02, S03, and F-28 assembly; `x1mmdp` owns the cutover switch to log format).

### Step R2

- Checked: E/V bijection is 3/3 (`E-01..E-03` to `V-01..V-03`), and `- Highest E allocated: 03` matches.
- Reachability: `V-01` verifies empty diff of `S01a` outcome lists under `.aw/state/545ag7/S01a-{before,after}.txt` and per-module `rg -c` counts; `V-02` verifies `S01b`; `V-03` verifies the empty union diff, F-28/F-29 tables, clean sanitize output, and path-scoped commits.

### Step R3

- Checked: No production code is modified. Test helpers and test modules do not inspect production ASTs or source code. `aw sanitize --agent` runs before commit, and commits are strictly path-scoped.

### Step R4

- A (State & atomicity): Outcomes are verified before and after each conversion; commits are path-scoped to `Scope-Paths`.
- C (Helper contract): `assert_field` and `assert_no_field` (from prerequisite `j5fqax`) assert through the active format (legacy in Phase B), reading both via `artifact_meta.read_text` and asserting the exact bullet line exists (or is absent), ensuring test assertions are never weakened.
- D & E (Regression & test safety): Deterministic pytest flags (`-o addopts="" -m "" -p no:randomly -n 0 -rA`) guarantee reproducible outcome lists; the empty diff invariant ensures zero behavioral regression across all 221 test cases in the eight modules.
- Spec sync: Implements the test-data preparation half of `4sd62s` Section 6 and Section 7 Step 9 without altering on-disk formats before the cutover commit.

### Step R5

- Checked through review personas:
  - QA / Regression: Batch rule guarantees identical outcome lists before and after.
  - Test Engineer: Decoupling setter-byte assertions from physical file format enables `cxxmyv` to switch builder output to log format without massive cross-module test failures.
  - Auditor: F-28 remaining-match classification records every non-convertible line (displayed-output, legacy-grammar subject, exact spelling) with its reason.

### Step R6

- Checked: Right-sizing is standard (3 E-items, 1 task group, 8 work Scope-Paths). Splitting `iog3cw` into `j5fqax` (helper + S04) and `545ag7` (S01) followed research `nj8zdp` guidance. No further decomposition is needed.

### Step R7

- Checked: `545ag7` integrates cleanly with parent `iog3cw`, prerequisite `j5fqax`, and orchestrator `63ib9r`.
- Dependencies in `63ib9r` row 262 match `- Item-Dependencies:` exactly. `545ag7` declares `executed:j5fqax`. `iog3cw` declares `executed:j5fqax` and `executed:545ag7`.

### Step S5

- Checked: OQ-01 is resolved and non-blocking. All 6 findings (`PR-001..PR-006`) are technical and procedural refinements resolved directly from repository evidence and standards. No human decision is required (`questions: []`).

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-262-545ag7-move-setter-byte-assertions-of-batch-s01-onto-the-format-awa.ipd.md` top to bottom after applying revisions.
- Verified batch rule `mkdir -p`, `Project conventions discovered` classification, Mermaid flowchart, `OQ-01` owner, and gate safety clauses.
- Ran `aw ipd lint --phase review-finalize --agent --verbose`: `outcome: clean`, 0 errors, 0 warnings.
- Ran `aw sanitize --agent`: `outcome: clean`, 0 findings.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Proofreading / P-Proofread | `545ag7.ipd.md:20` (`> Write and proofread this plan...`); lines 1-19 | Unremoved authoring template prompt blockquote and missing front-matter metadata (`- Review-Depth: standard`, `- Readiness: go-pending-approval`). | Low | FIXED | Removed template line, added `- Review-Depth: standard` and `- Readiness: go-pending-approval`. |
| PR-002 | MEDIUM | IN-SCOPE | R2 / R4 Batch Rule | `545ag7.ipd.md:39` (`> .aw/state/545ag7/<batch>-before.txt`) | Batch rule step 1 redirected output to `.aw/state/545ag7/<batch>-before.txt` without creating the gitignored directory first, which fails on fresh lane worktrees. | Low | FIXED | Added `mkdir -p .aw/state/545ag7 && ` to batch rule step 1 command. |
| PR-003 | LOW | IN-SCOPE | Technical Writing Requirement 12 | `545ag7.ipd.md:76-80` (`Proposed changes`) | Proposed changes lacked a Mermaid diagram illustrating the execution sequence. | Low | FIXED | Added a `flowchart TD` Mermaid diagram showing `E-01` and `E-02` converging into `E-03`. |
| PR-004 | LOW | IN-SCOPE | S5 Questions | `545ag7.ipd.md:119` (`OQ-01`) | Resolved open question `OQ-01` had `- Owner: none` instead of `- Owner: plan author`. | Low | FIXED | Updated `OQ-01` `- Owner:` to `plan author`. |
| PR-005 | MEDIUM | IN-SCOPE | S7 Contract / Safety | `545ag7.ipd.md:145-150` (`Approval and execution gate`) | Approval gate lacked explicit stop-and-report clause, shared-checkout safety, and conditional runner/executor `aw ipd finalize 545ag7` ownership (`never a hand git mv`). | Low | FIXED | Added safety stops, shared checkout safety, and conditional runner-vs-hand `aw ipd finalize` ownership (`never a hand git mv`). |
| PR-006 | MEDIUM | IN-SCOPE | R1 / R4 Assertions | `545ag7.ipd.md:62` (`Project conventions discovered`) | Candidate assertion analysis was not documented: 23 convertible setter-byte assertions across 6 modules, and 5 unconverted `legacy-format subject` assertions (4 in `test_attention_priority_blocker.py` and 1 in `test_attention.py`). | Low | FIXED | Documented the candidate line breakdown (23 convertible, 5 legacy-format subject) in `Project conventions discovered`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-001 | How should candidate lines in `test_attention_priority_blocker.py` and `test_attention.py` be treated? | Classify them as `legacy-format subject` and leave them unconverted | Convert them to `assert_field` | Lines 239-258 in `test_attention_priority_blocker.py` test `read_readiness` parser on literal strings; line 3509 in `test_attention.py` tests string buffer index offsets for chunk window straddling | yes |
| D-002 | How should directory creation be handled for `.aw/state/545ag7/` in isolated worktrees? | Prepend `mkdir -p .aw/state/545ag7 && ` to the batch rule step 1 command | Require a separate manual shell step | Ensures non-interactive and automated runners do not fail on an uncreated gitignored directory | yes |
