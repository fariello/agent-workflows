# Review findings: plan 1bshrb

- Subject-Id: 1bshrb
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `747a38810` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-215-1bshrb-delete-orphaned-record-building-helpers-in-test-modules-outs.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), and the reference baseline suite (`pytest` on all 8 target test modules) passed (`82 passed in 4.84s`). During revision, code citations were standardized to repo-relative `path::Symbol` identifiers, Behavior decisions were added to document `D-1` through `D-5`, a Mermaid `flowchart TD` diagram was added under `## Proposed changes`, `OQ-01` owner was updated to `plan author`, and `Approval and execution gate` was updated with the standard hand-mv restriction, conditional runner/executor ownership clause, and narrow unsafe-condition stop rule. Pass 2 re-checked the complete revised plan against `4sd62s`, `59aiyh`, `j6o96i`, `9rgn2w`, and `cxxmyv`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted hand-mv restriction, conditional runner/executor finalize clause, and narrow stop rule | Added explicit `never a hand git mv`, conditional runner/executor ownership clause, and narrow unsafe-condition stop rule | PR-001, Technical Writing Standard Requirement 1. |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Updated to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) | PR-002, steps/s5-questions.md owner attestation standard. |
| Proposed changes (ordered, validatable) | Two-line description without process diagram | Added Mermaid `flowchart TD` diagram showing deletion progression | PR-003, Technical Writing Standard Requirement 12(b). |
| Step 0 | Code citations used unqualified `module.function` symbols | Standardized citations to `path::Symbol` identifiers | PR-004, Technical Writing Standard Requirement 7, IPD-C801. |
| Front matter, Workflow history | Omitted review output fields and review history record | Added `- Readiness: go-pending-approval`, `- Review-Depth: complex`, and recorded review history | PR-005, Step S7 review output requirements. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `1bshrb` cleans up private test record-building helpers across 8 test modules outside every batch in favor of the shared record builder `tests/record_builder.py::RecordBuilder`.
2. No. Standalone test helper cleanup; touches test files only.
3. No. Right-sized at 3 E-items across 8 test files.
4. Yes. `- Scope-Paths:` explicitly lists all 8 test module paths plus the plan itself.
5. Yes. Test outcome preservation: per-test outcomes must remain identical before and after deletion/conversion.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6); parent plan `59aiyh` (Order 38 split); predecessor builder `j6o96i` and `9rgn2w`; and the 8 test modules in `tests/`.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-36..E-38` <-> `V-36..V-38`, with `- Highest E allocated: 38` preserved), dependency chain (`E-36 -> E-37 -> E-38`), `- Scope-Paths:` completeness (all 8 target modules and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause, hand-mv guard, and stop rule in Approval and execution gate (`PR-001`). Fixed in Gate.

### Step R3

- Checked: safety, test outcome invariance, and rollback semantics. Verified that outcome list diffs for any modified module must be empty.

### Step R4

- Checked: conformance with spec `4sd62s` section 6, pytest determinism (`-p no:randomly -n 0`), right-sizing (`3` `E-*` items, `8` work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs before and after), Architect (shared record builder decoupling test data from storage layout changes), Software Engineer (census verification against baseline), and Modest Executor (bounded deletion items across 4 modules each).

### Step R6

- Checked: `3` `E-*` items in `2` task groups across `8` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `59aiyh` on 2026-11-09 per `nj8zdp`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:1upea0, executed:7qxey9, executed:9rgn2w, executed:g5hpbb, executed:nbfg7w, executed:tve77h, executed:x05v02, executed:xexn45, executed:653ndz, executed:j6o96i` (all verified in `metastore`), parent `59aiyh`, and cutover plan `cxxmyv`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded five engineering decisions (`D-1..D-5`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-36..E-38` and `V-36..V-38` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and formatting decisions.
- Verified 3-to-3 `E-*`/`V-*` bijection, `- Highest E allocated: 38`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-215-1bshrb-delete-orphaned-record-building-helpers-in-test-modules-outs.ipd.md:147 | Approval and execution gate omitted explicit hand-mv guard, conditional runner/executor finalize clause, and narrow unsafe-condition stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction, conditional runner/executor ownership clause, and narrow stop rule to Gate (recommendation strength: strong). |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-215-1bshrb-delete-orphaned-record-building-helpers-in-test-modules-outs.ipd.md:121 | OQ-01 recorded `- Owner: none` on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `- Owner: plan author` in OQ-01 and recorded the decision in `### Decisions` (D-1) (recommendation strength: strong). |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12(b) | .aw/records/plans/pending/20261109-metastore-215-1bshrb-delete-orphaned-record-building-helpers-in-test-modules-outs.ipd.md:85 | Proposed changes lacked a Mermaid diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes with branches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram under `Proposed changes` showing deletion progression (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Requirement 7 / Step 0 | .aw/records/plans/pending/20261109-metastore-215-1bshrb-delete-orphaned-record-building-helpers-in-test-modules-outs.ipd.md:58 | `Step 0` cited code using unqualified `module.function` symbols instead of repo-relative `path::Symbol` identifiers (`IPD-C801`, Technical Writing Standard Requirement 7). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Standardized code citations to `path::Symbol` identifiers in `Step 0` (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-215-1bshrb-delete-orphaned-record-building-helpers-in-test-modules-outs.ipd.md:9 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: complex`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Why does this part wait for the batch plans? | Inherit batch dependencies from 59aiyh split; waiting ensures the final census in E-38 reflects true survivor counts after all batches finish. | Execute immediately without waiting for batches (rejected: census would include unmigrated helpers from other plans). | OQ-01, research `nj8zdp` | yes |
| D-2 | How are private test helpers handled in target modules? | Delete uncalled private helpers directly; for helpers with callers, replace with `RecordBuilder` only if per-test outcome lists remain identical, otherwise list as surviving with justification. | Force deletion without caller check (rejected: breaks existing tests); keep uncalled helpers (rejected: leaves dead code). | `1bshrb` E-36, E-37 | yes |
| D-3 | How is the helper census verified? | Run the helper regex pattern over `tests/` and compare count against F-10 baseline from Order 170 (`j6o96i`). | Skip cross-tree census (rejected: loses verification of overall migration progress). | `1bshrb` E-38 | yes |
| D-4 | What validates helper deletions or replacements? | Require identical per-test outcome list before and after in each changed test module. | Rely only on module pass/fail exit code (rejected: masked regressions). | `1bshrb` Required tests / validation | yes |
| D-5 | Can production code be modified to remove a helper? | No. Production code under `agent_workflows/` and `tools/` is out of scope; if a helper requires production changes to remove, it survives and is listed. | Modify production code (rejected: violates scope fence). | `1bshrb` Scope fence | yes |
