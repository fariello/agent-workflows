# Review findings: plan y3uowx

- Subject-Id: y3uowx
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `47e620415` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), and the reference baseline suite (`tests/test_backlog_handoff_close.py`) passed (`40 passed in 2.98s`). During revision, `mkdir -p .aw/state/y3uowx` and scratch fixture isolation were added to E-02, E-03, V-02, and V-03 to prevent mutating repository test modules ahead of pilot plan `653ndz`, code citations were converted to `path::Symbol` identifiers, Behavior decisions were expanded to document `D-1` through `D-5`, a Mermaid `flowchart TD` diagram was added under `## Proposed changes`, and a narrow unsafe-condition stop rule was added to `Approval and execution gate`. Pass 2 re-checked the complete revised plan against `4sd62s`, `653ndz`, `9rgn2w`, and `j2xjtt`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter, Workflow history | Omitted review output fields and review history record | Adds `- Readiness: go-pending-approval`, `- Review-Depth: complex`, and records review history | PR-005, Step S7 review output requirements. |
| Detailed Implementation Checklist (E-01..E-03) | Relied on unqualified symbols and lacked explicit scratch fixture isolation for `--apply` verification | Converts citations to `path::Symbol` and specifies scratch fixture isolation under `.aw/state/y3uowx/` | PR-002, PR-003. |
| Project conventions discovered (Step 0) | Cited code with unqualified `module.function` references | Cites `path::Symbol` identifiers for `tools/gate_drop_audit.py`, `tests/record_builder.py::RecordBuilder`, `agent_workflows/artifact_meta.py::registry_fields`, and `agent_workflows/artifact_meta.py::read_text` | Technical Writing Standard Requirement 7, PR-002. |
| Findings (F-01, F-29) and Behavior decisions (D-1..D-5) | Stated site and module counts without non-binding framing and lacked a documented decisions section | Marks counts non-binding and documents `D-1` through `D-5` covering per-module equivalence proof (`D-1`), invalid input handling (`D-2`), AST boundary preservation (`D-3`), scratch fixture isolation (`D-4`), and idempotence (`D-5`) | PR-002, PR-003. |
| Proposed changes (ordered, validatable) | Two-line description without process diagram | Two-line description with Mermaid `flowchart TD` process diagram | Technical Writing Standard Requirement 12(b), PR-001. |
| Validation and cross-check (V-02, V-03) and Approval and execution gate | V-02 and V-03 vaguely named "one fixture module"; Approval and execution gate lacked an unsafe-condition stop rule | Specifies scratch fixture modules in `.aw/state/y3uowx/` in `V-02` and `V-03` and adds a narrow unsafe-condition stop rule in `Approval and execution gate` | PR-003, PR-004. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `y3uowx` introduces the standalone maintenance tool `tools/fixture_codemod.py` with CLI flags (`--dry-run`, `--apply`, `--format table|json`, `<paths>`), 7 reason codes, and structured output schemas relied upon by downstream test conversion plans.
2. No. Standalone AST rewriting tool for test files.
3. No (`4` right-sized `E-*` items in `2` task groups across `2` `- Scope-Paths:` entries).
4. No. `- Scope-Paths:` explicitly names `tools/fixture_codemod.py` and the plan file itself.
5. Yes. A bug in AST node replacement, import insertion, or equivalence bisection could corrupt test assertions or alter test execution across 318 test files.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Section 6 and Section 7 step 6); parent plan `653ndz` (Order 49); predecessor plan `9rgn2w` (Order 37); downstream test plans `j2xjtt` (Order 173) and `n0li9v` (Order 216); and reference test suite `tests/test_backlog_handoff_close.py`.
- Verified that `tools/fixture_codemod.py` is structured to parse test files via Python standard library `ast`, map metadata fields through `agent_workflows/artifact_meta.py::registry_fields`, and emit canonical `tests/record_builder.py::RecordBuilder` invocations with `text_only=True`.

### Step R2

- Checked: `E-*`/`V-*` 1:1 bijection (`E-01..E-03`, `E-07` <-> `V-01..V-03`, `V-07`), `- Highest E allocated: 07`, dependency order (`E-01` -> `E-02` -> `E-03` -> `E-07`), `- Scope-Paths:` completeness (`2` paths), and scratch directory creation (`mkdir -p .aw/state/y3uowx`).
- Verified that verification of `--apply` and equivalence halving in `V-02` and `V-03` uses scratch fixture files created under `.aw/state/y3uowx/`, preventing premature mutations to repository test files before the pilot plan `653ndz` executes (`PR-003`).

### Step R3

- Checked: Test suite semantic preservation and equivalence safety. The equivalence proof in `E-03` runs per-module pytest comparisons before and after rewriting and isolates regressions via bisection, guaranteeing that test suite outcomes remain byte-for-byte identical.
- Verified that assertion sites matching expected command output or file bytes remain classified as refusals (`displayed-output assertion`, `setter-byte assertion`) with legacy form kept.

### Step R4

- Checked: Behavioral decisions and invariant preservation:
  1. `D-1`: Per-module equivalence proof with bisection on failure, minimizing pytest execution overhead.
  2. `D-2`: Handling deliberately invalid inputs via `raw_fields=` rather than refusal.
  3. `D-3`: Precise AST node coordinate replacement preserving whitespace and comments.
  4. `D-4`: Scratch fixture isolation under `.aw/state/y3uowx/` for validation.
  5. `D-5`: Idempotent behavior on second `--apply` execution.

### Step R5

- Checked: Architect (clean separation between codemod tool authoring in `y3uowx` and test module authoring in `j2xjtt`; strict reuse of `agent_workflows/artifact_meta.py::registry_fields`), Security/Integrity Reviewer (equivalence proof ensures no test asserts an altered outcome; strict AST bounding), QA/QC Engineer (40 baseline tests in `tests/test_backlog_handoff_close.py` verified green; clean scratch fixture testing for bisection), Software Engineer (UTF-8 character-offset replacement instead of AST unparsing), and Modest Executor (4 single-concern E-items, within `IPD-Z603` bounds).

### Step R6

- Checked: `4` `E-*` items in `2` task groups across `2` `- Scope-Paths:` entries (`1` work path plus the plan file; `- Size assessment: standard`), satisfying `nj8zdp` and `IPD-Z603` bounds (`<=5` E-items, `<=8` work Scope-Paths, `0` advisories).

### Step R7

- Checked: `- Item-Dependencies: executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45` (`tve77h` verified executed; `9rgn2w`, `g5hpbb`, and `xexn45` verified in `metastore`), parent `653ndz` (Order 49), test plan `j2xjtt` (Order 173), and orchestrator `63ib9r` (Order 00, H1 title kept exact to match row 172).

### Step S5

- Checked: `OQ-01` (per-module proof justification) and `OQ-02` (static census justification), both resolved with recommendation strength: strong.
- Documented five technical decisions (`D-1`..`D-5` in `### Decisions` below, all `Reversible: yes`). Zero questions belong to the human under the `askme` three-way sort.

### Pass 2

- Re-reviewed the complete revised plan per `steps/s6-rereview.md` rules 1 and 2 because scratch fixture isolation was added to E-02, E-03, V-02, and V-03, `D-1` through `D-5` were documented, code citations were standardized, and a Mermaid flowchart TD diagram was added.
- Verified `E-01..E-03, E-07` <-> `V-01..V-03, V-07` 1:1 bijection, `- Highest E allocated: 07`, dependency order (`E-01` -> `E-02` -> `E-03` -> `E-07`), `- Scope-Paths:` (`2` files), compliance with all 12 requirements of `.aw/system/workflows/technical-writing/technical-writing.md`, and `aw ipd lint --phase review-finalize --agent` (`outcome: clean`, `findings: 0`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Proofreading / Requirement 12(b) | .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md:93 | `Proposed changes` lacked the Mermaid diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes with branches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart TD` diagram under `Proposed changes` illustrating the detection, refusal, rewriting, and equivalence bisection workflow (recommendation strength: strong). |
| PR-002 | LOW | IN-SCOPE | Proofreading / Requirement 7 / Step 0 | .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md:76 | `Step 0` and the checklist cited code using unqualified `module.function` symbols instead of repo-relative `path::Symbol` identifiers (`IPD-C801`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Standardized code citations to `path::Symbol` identifiers across `Step 0` and `E-01..E-03` (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R4 / E-02, E-03, V-02, V-03 | .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md:57, .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md:143 | `V-02` and `V-03` referred vaguely to "one fixture module" without establishing scratch fixture isolation, creating the risk that an executor would rewrite tracked test modules ahead of pilot plan `653ndz`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added scratch directory rule under Task group 1 (`mkdir -p .aw/state/y3uowx`) and specified scratch fixture modules in `.aw/state/y3uowx/` for `V-02` and `V-03` (recommendation strength: very strong). |
| PR-004 | LOW | IN-SCOPE | R7 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md:163 | `Approval and execution gate` lacked a narrow stop directive if prerequisite symbols from `9rgn2w` (`RecordBuilder`) or `artifact_meta` (`registry_fields`, `read_text`) are absent on HEAD, or if baseline test suites fail before starting. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a narrow unsafe-condition stop rule in `Approval and execution gate` (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md:9 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: complex`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the pytest equivalence proof run per module or per site? | Per module with bisection (halving) on failure to isolate breaking sites. | Per site (running pytest after every individual literal rewrite, requiring 3,272 pytest runs). | OQ-01, spec `4sd62s` Section 6, `y3uowx:120` | yes |
| D-2 | How should the codemod handle deliberately invalid field values or unknown statuses in test fixtures (e.g. `- Status: EXECUTED`)? | Emit them via `RecordBuilder`'s `raw_fields=` escape argument rather than refusing them, classifying them as `invalid-input` planned rewrites. | Refuse with `unsupported-shape` for hand conversion (forces hundreds of negative tests to be hand-converted). | `y3uowx:48`, `9rgn2w` E-01, spec `4sd62s` Section 6 | yes |
| D-3 | How should AST rewriting replace fixture expressions without altering formatting or comments in surrounding code? | Replace the AST node's exact character span (`lineno`, `col_offset`, `end_lineno`, `end_col_offset`) in UTF-8 source text in place, adding one `from tests.record_builder import RecordBuilder` import if missing. | Full AST unparsing via `ast.unparse()` (destroys comments, whitespace, and formatting across the entire test file); regex substitution. | `tools/fixture_codemod.py::Rewriter`, Python 3.8+ AST position attributes | yes |
| D-4 | How should `y3uowx` validate `--apply` and equivalence bisection without permanently altering or dirtying existing repository test modules ahead of the pilot in `653ndz`? | Use scratch fixture test files created under `.aw/state/y3uowx/` during execution for V-02 and V-03 validation, leaving tracked test modules untouched in this plan. | Modify `tests/test_backlog_handoff_close.py` directly (risks committing modified test files before the pilot plan `653ndz` runs). | `- Scope: Excludes converting any test module`, `tools/` tool execution contract | yes |
| D-5 | What should `--apply` do when executed a second time over an already-rewritten module? | Idempotence: a second `--apply` run detects that all sites already use `RecordBuilder` calls and makes zero changes, exiting 0. | Error on already converted files; re-wrap existing `RecordBuilder` expressions. | E-02 expected outcome, `y3uowx:59` | yes |
