# Review findings: plan jutivt

- Subject-Id: jutivt
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `702959857` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-182-jutivt-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `0` advisories), and the reference baseline suite (`pytest` on all 8 target test modules) passed (`123 passed in 18.60s`). During revision, `mkdir -p .aw/state/59aiyh` was added to batch rule step 1, code citations were standardized to repo-relative `path::Symbol` identifiers, Behavior decisions were added to document `D-1` through `D-5`, a Mermaid `flowchart TD` diagram was added under `## Proposed changes`, `OQ-01` owner was updated to `plan author`, and `Approval and execution gate` was updated with the standard hand-mv restriction, conditional runner/executor ownership clause, and narrow unsafe-condition stop rule. Pass 2 re-checked the complete revised plan against `4sd62s`, `7qxey9`, `653ndz`, `9rgn2w`, and `cxxmyv`, and `aw ipd lint --phase review-finalize --agent` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted hand-mv restriction, conditional runner/executor finalize clause, and narrow stop rule | Added explicit `never a hand git mv`, conditional runner/executor ownership clause, and narrow unsafe-condition stop rule | PR-001, Technical Writing Standard Requirement 1. |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Updated to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) | PR-002, steps/s5-questions.md owner attestation standard. |
| Proposed changes (ordered, validatable) | Two-line description without process diagram | Added Mermaid `flowchart TD` diagram showing batch progression | PR-003, Technical Writing Standard Requirement 12(b). |
| Step 0 & Batch rule step 1 | Code citations used unqualified `module.function` symbols and batch rule lacked directory initialization | Standardized citations to `path::Symbol` and added `mkdir -p .aw/state/59aiyh` | PR-004, Technical Writing Standard Requirement 7, IPD-C801. |
| Front matter, Workflow history | Omitted review output fields and review history record | Added `- Readiness: go-pending-approval`, `- Review-Depth: complex`, and recorded review history | PR-005, Step S7 review output requirements. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `jutivt` converts 8 spec and spec-review test modules to use the shared record builder `tests/record_builder.py::RecordBuilder` via the Order-49 fixture codemod `tools/fixture_codemod.py`.
2. No. Standalone test fixture conversion; touches test files only.
3. No. Right-sized at 3 E-items (2 batch items of 4 modules each and 1 finishing item) across 8 test files.
4. Yes. `- Scope-Paths:` explicitly lists all 8 test module paths plus the plan itself.
5. Yes. Test outcome preservation: per-test outcomes must remain identical before and after conversion.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and section 7 step 6); parent plan `7qxey9` (Order 38); predecessor builder `9rgn2w` and codemod `653ndz`; and the 8 test modules in `tests/`.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, with `- Highest E allocated: 03` preserved), dependency chain (`E-01, E-02 -> E-03`), `- Scope-Paths:` completeness (all 8 target modules and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause, hand-mv guard, and stop rule in Approval and execution gate (`PR-001`). Fixed in Gate.

### Step R3

- Checked: safety, test outcome invariance, refusal count threshold (at most 25 hand conversions before stop), and rollback semantics. Verified that outcome list diffs must be empty and that `raw_fields=` is used only for deliberate invalid-input tests.

### Step R4

- Checked: conformance with spec `4sd62s` section 6, batch rule structure, pytest determinism (`-p no:randomly -n 0`), right-sizing (`3` `E-*` items, `8` work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs before and after), Architect (shared record builder decoupling test data from storage layout changes), Software Engineer (codemod automation with static refusal classification), and Modest Executor (bounded batch items of at most 4 modules each).

### Step R6

- Checked: `3` `E-*` items in `2` task groups across `8` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `7qxey9` on 2026-11-09 per `nj8zdp`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45` (all verified in `metastore`), split parent `7qxey9`, and cutover plan `cxxmyv`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded five engineering decisions (`D-1..D-5`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-03` and `V-01..V-03` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, state directory initialization, and formatting decisions.
- Verified 3-to-3 `E-*`/`V-*` bijection, `- Highest E allocated: 03`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-182-jutivt-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md:176 | Approval and execution gate omitted explicit hand-mv guard, conditional runner/executor finalize clause, and narrow unsafe-condition stop rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction, conditional runner/executor ownership clause, and narrow stop rule to Gate (recommendation strength: strong). |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-182-jutivt-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md:150 | OQ-01 recorded `- Owner: none` on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `- Owner: plan author` in OQ-01 and recorded the decision in `### Decisions` (D-1) (recommendation strength: strong). |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12(b) | .aw/records/plans/pending/20261109-metastore-182-jutivt-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md:107 | Proposed changes lacked a Mermaid diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes with branches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram under `Proposed changes` showing batch progression (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Requirement 7 / Step 0 / Batch rule | .aw/records/plans/pending/20261109-metastore-182-jutivt-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md:38, .aw/records/plans/pending/20261109-metastore-182-jutivt-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md:65 | `Step 0` cited code using unqualified `module.function` symbols instead of repo-relative `path::Symbol` identifiers (`IPD-C801`), and `Batch rule` step 1 lacked directory initialization (`mkdir -p .aw/state/59aiyh`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Standardized code citations to `path::Symbol` identifiers in `Step 0` and added `mkdir -p .aw/state/59aiyh` to batch rule step 1 (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-182-jutivt-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-1.ipd.md:9 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: complex`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can Chunk 1 execute in any order relative to other chunk plans? | Yes. Module sets are disjoint, each chunk depends on builder and codemod, and none edits `tests/support.py` (which runs in `59aiyh` E-09). | Impose strict serial ordering across all chunk plans (rejected: unnecessary serialization of independent test files). | OQ-01, research `nj8zdp` | yes |
| D-2 | How are private test helpers handled in target modules? | Delete private record-building helpers (`tests/test_spec_id6_filenames.py`: `_write_spec`; `tests/test_spec_production.py`: `_write_spec`, `_write_plan_content`; `tests/test_spec_review_attestation.py`: `_write_spec`, `_write_record`; `tests/test_spec_review_dispatch.py`: `_write_plan`, `_write_spec`, `_write_review_record`) when all internal callers move to the record builder; list any surviving helper with justification. | Keep dead helper functions (rejected: leaves redundant untested code paths); delete without caller check (rejected: risk of breaking unmigrated tests). | `jutivt` E-01, E-02 | yes |
| D-3 | What is the threshold for halting hand conversions? | Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting. | Attempt unbounded manual conversions (rejected: high risk of agent mistakes and drift). | `jutivt` Batch rule step 4, research `nj8zdp` | yes |
| D-4 | How should test fixtures with deliberately invalid values be constructed? | Use `RecordBuilder` with `raw_fields=` to inject invalid metadata bullets while maintaining structured generation. | Use raw markdown string literals or heredocs (rejected: bypasses builder pattern established for phase B). | `jutivt` Batch rule step 4, spec `4sd62s` section 6 | yes |
| D-5 | How is `.aw/state/59aiyh/` initialized across lane worktrees? | Create `.aw/state/59aiyh/` via `mkdir -p .aw/state/59aiyh` at step 1 before recording test outcome lists in each lane worktree. | Rely on preexisting state directory (fails in isolated git worktrees where `.aw/state/` is gitignored and not shared). | `jutivt` Batch rule step 1, isolated lane environment | yes |
