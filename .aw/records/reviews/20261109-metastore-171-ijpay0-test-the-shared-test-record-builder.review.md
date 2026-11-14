# Review findings: plan ijpay0

- Subject-Id: ijpay0
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `5fc5d3e27` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-171-ijpay0-test-the-shared-test-record-builder.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` (sections 6 and 7 step 6), research `nj8zdp`, sibling plans `j6o96i` (Order 170), `7yr827` (Order 21), `xexn45` (Order 07), `tve77h` (Order 02), `g5hpbb` (Order 14), `59aiyh` (Order 10), and `9rgn2w` (Order 37), and `tests/support.py` uncovered one `HIGH`, two `MEDIUM`, and two `LOW` findings (`PR-001..PR-005`), all fixed in place. Pass 2 re-checked `E-02`, `E-18`, `E-19`, `E-20`, `E-21` and `V-02`, `V-18`, `V-19`, `V-20`, `V-21`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted narrow unsafe-condition safety stop, hand `git mv` prohibition, and conditional finalize clause | Added explicit safety stop for missing prerequisites or `tests/record_builder.py`, `never a hand git mv`, and conditional runner/executor ownership clause | PR-001, Technical Writing Standard Requirement 1. |
| Front matter, Step 0, OQ-01 | Omitted `7yr827` from dependencies and cited `xexn45` for `write_legacy` and `render_legacy_text` | Added `executed:7yr827` to `- Item-Dependencies:` and Gate, and updated Step 0 and OQ-01 citations to reference `7yr827` E-01 (and `xexn45` finishing part) | PR-002, alignment with Order 21 split. |
| E-18, E-19, E-20 | Contained stray unmatched `)` tokens: `) VISIBILITY.`, `) GOLDEN.`, `) PARITY.` | Restored complete test group identifiers `(c) VISIBILITY.`, `(d) GOLDEN.`, and `(e) PARITY.` | PR-003, fixing split truncation defect. |
| Proposed changes (ordered, validatable) | Three-item numbered list without process diagram | Added Mermaid `flowchart TD` diagram illustrating test implementation flow from E-02 -> E-18..E-20 -> E-21 | PR-004, Technical Writing Standard Requirement 12(b). |
| Preamble, Front matter | Raw authoring instruction blockquote; lacked readiness and review-depth fields | Updated preamble compliance blockquote, and added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | PR-005, Technical Writing Standard Requirement 1, Step S7 review output requirements. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `ijpay0` adds `tests/test_record_builder.py` (`pytestmark = pytest.mark.core`), the comprehensive behavioral test module for `RecordBuilder` (`tests/record_builder.py`) across all eight record types, verifying round-trip fidelity, lint compliance, repository reader visibility (`aw find`, `aw attention`, `aw check`), golden byte reproduction for `support.ready_plan_text`, and parity against production CLI creating commands.
2. No. It modifies only test code (`tests/test_record_builder.py`, `tests/slow_allowlist.txt`) and this plan file; no production modules under `agent_workflows/` or `tools/` are touched.
3. No. It has 5 E-items in 2 task groups across 2 declared Scope-Paths (plus at most one moved slow module in `tests/slow_allowlist.txt`).
4. Yes. `- Scope-Paths:` explicitly declares `tests/test_record_builder.py`, `tests/slow_allowlist.txt`, and this plan file.
5. Low. Scope is restricted to new test code in `tests/test_record_builder.py`.

AW-TIER: standard

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (sections 6 and 7 step 6); parent split plan `9rgn2w` (Order 37); prerequisite plans `j6o96i` (Order 170, builds `RecordBuilder`), `7yr827` (Order 21, provides `write_legacy` and `render_legacy_text`), `xexn45` (Order 07, finishing writer part), `tve77h` (Order 02, core registry), and `g5hpbb` (Order 14, universal migration); and test infrastructure in `tests/support.py`.
- Step 0 and OQ-01 citations updated to cite `7yr827` E-01 for `write_legacy` and `render_legacy_text` (`PR-002`), aligning with `j6o96i` PR-001.

### Step R2

- Checked: E/V bijection (`5/5`: `E-02, E-18, E-19, E-20, E-21` <-> `V-02, V-18, V-19, V-20, V-21`), `- Highest E allocated: 21`, `- Item-Dependencies:` (`executed:g5hpbb, executed:tve77h, executed:7yr827, executed:xexn45, executed:j6o96i`), and isolated-lane reachability of every `V-*` demand.
- Fixed stray unmatched `)` tokens in E-18, E-19, and E-20 (`PR-003`).
- Added narrow safety stop for missing prerequisites or absent `tests/record_builder.py`, `never a hand git mv`, and conditional runner/executor finalize ownership clause to `Approval and execution gate` (`PR-001`).

### Step R3

- Checked: tests execute cleanly in isolated fixture repositories created via `tests/support.py` or `tests/repo_template.py`; no writes to shared state or outside the authorized worktree lane.

### Step R4

- A (Correctness and data integrity): Test suite covers round-trip fidelity through `artifact_meta.read`, pre-execution linting, and exact error raises for invalid fields, illegal statuses, and oversized descriptions.
- C (Architecture and operability): Parity test group (e) guarantees that `RecordBuilder` outputs match production creating commands (`aw ipd scaffold`, `aw specs new`, `aw backlog new`, etc.).
- D and E (Anti-regression and testing): E-19 asserts byte reproduction against tracked `tests/fixtures/record_builder/ready_plan_text_golden.json`, and E-21 enforces strict 10 s wall time budget under `-n 0` with slow allowlist fallback.
- Executability and right-sizing: 5 E-items in 2 task groups across 2 work Scope-Paths; cohesive and focused.

### Step R5

- Checked: QA/QC (strict 10 s duration check and core gate run), Testing and regression (golden fixtures and parity tests), Architect (single builder test suite verifying Phase B invariant), and Modest Executor (discrete test groups).

### Step R6

- Checked: 5 E-items in 2 task groups across 2 Scope-Paths (`- Size assessment: standard`). Already split from `9rgn2w` per research `nj8zdp`. No further decomposition needed.

### Step R7

- Checked: alignment with prior builder plan `j6o96i` (Order 170, creates `RecordBuilder` and golden fixture), sibling codemod plans `y3uowx` (Order 172) and `j2xjtt` (Order 173), fixture conversion plans `7fpc8v` through `wirc2e` (Orders 174-179), and switch-point plan `59aiyh` (Order 10).

### Step S5

- Checked: OQ-01 is resolved and non-blocking. Attested owner set and decisions D-1 through D-4 recorded in `### Decisions`. Zero questions belong to the human (`questions: []`).

### Step S6

- Re-review check: No new `E-*` or `V-*` items added or removed; `- Scope-Paths:` unchanged; all edits are surgical hardening.
- Re-run `aw ipd lint --phase review-finalize --agent` confirmed clean (0 errors, 0 warnings, 0 advisories).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-171-ijpay0-test-the-shared-test-record-builder.ipd.md:174 | Approval and execution gate omitted explicit narrow unsafe-condition safety stop, hand git mv prohibition, and conditional runner/executor finalize clause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added narrow safety stop for missing prerequisites or tests/record_builder.py, never a hand git mv, and conditional runner/executor finalize ownership clause to Gate (recommendation strength: strong). |
| PR-002 | MEDIUM | IN-SCOPE | R1 / R2 / Dependencies, Step 0, OQ-01 | .aw/records/plans/pending/20261109-metastore-171-ijpay0-test-the-shared-test-record-builder.ipd.md:8 | Plan omitted executed:7yr827 from Item-Dependencies and Gate, and Step 0 and OQ-01 cited xexn45 for write_legacy and render_legacy_text rather than 7yr827 E-01. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added executed:7yr827 to Item-Dependencies and Gate, and updated Step 0 and OQ-01 citations to cite 7yr827 E-01 and xexn45 finishing part (recommendation strength: strong). |
| PR-003 | MEDIUM | IN-SCOPE | R2 / R4 / E-18, E-19, E-20 | .aw/records/plans/pending/20261109-metastore-171-ijpay0-test-the-shared-test-record-builder.ipd.md:50 | Items E-18, E-19, and E-20 contained stray unmatched closing parentheses () VISIBILITY., ) GOLDEN., ) PARITY.) from an incomplete split from 9rgn2w E-02. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Restored complete group identifiers (c) VISIBILITY., (d) GOLDEN., and (e) PARITY. in E-18, E-19, and E-20 (recommendation strength: very strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Requirement 12(b) | .aw/records/plans/pending/20261109-metastore-171-ijpay0-test-the-shared-test-record-builder.ipd.md:94 | Proposed changes lacked a Mermaid diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram under Proposed changes illustrating test implementation flow (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | Proofreading / Step S7 | .aw/records/plans/pending/20261109-metastore-171-ijpay0-test-the-shared-test-record-builder.ipd.md:22 | Preamble retained raw authoring instruction blockquote, and front matter lacked readiness and review depth. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated preamble blockquote to standard compliance text, and added - Readiness: go-pending-approval and - Review-Depth: standard to front matter (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which plan provides `write_legacy` and `render_legacy_text` for the Phase B record builder tested here? | Depend directly on `7yr827` E-01 (Order 21) and `xexn45` (finishing part). | Depend on `tve77h` only (rejected: does not provide legacy renderer); keep stale `xexn45` E-01/E-11 citations (rejected: items moved to `7yr827`). | `7yr827` E-01, `j6o96i` PR-001/D-1, `4sd62s` section 7 step 4/6 | yes |
| D-2 | How should test group identifiers in E-18, E-19, and E-20 be formatted? | Restore `(c) VISIBILITY.`, `(d) GOLDEN.`, and `(e) PARITY.` matching the test groups declared in E-02. | Leave unmatched `) VISIBILITY.` etc. (rejected: ungrammatical and broken formatting). | `9rgn2w` E-02, `ijpay0` E-02 | yes |
| D-3 | How is module test duration budgeted and enforced? | Enforce strict 10 s wall time budget under `-n 0` in E-21; if exceeded, move subprocess-heavy groups (c) and (e) to a separate module listed in `tests/slow_allowlist.txt`. | Omit execution time bound (rejected: subprocess tests could cause test suite timeout regressions). | `9rgn2w` E-02, `ijpay0` E-21 | yes |
| D-4 | Which argument sets must golden test (d) cover? | Cover all argument sets captured in `tests/fixtures/record_builder/ready_plan_text_golden.json` (30 call expressions at review). | Test only default arguments (rejected: does not protect existing call sites across 15+ test modules). | `j6o96i` E-13, `tests/support.py::ready_plan_text` | yes |
