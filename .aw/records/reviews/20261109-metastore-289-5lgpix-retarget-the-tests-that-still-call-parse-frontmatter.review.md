# Review findings: plan 5lgpix

- Subject-Id: 5lgpix
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `575f14540` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-289-5lgpix-retarget-the-tests-that-still-call-parse-frontmatter.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` C5 and 4.3, split parent `k6jd6l`, prerequisite `sq6v7i`, and affected test modules in `tests/` uncovered one `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-003`), all fixed in place. Pass 2 re-checked `E-01..E-05` and `V-01..V-05`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted Scope fence hand-mv restriction and conditional runner/executor finalize clause | Added explicit `never a hand git mv` and conditional runner/executor ownership clause ("When `aw oc run` or `aw agy run` executes the plan...") | PR-001. |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Updated to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) | PR-002. |
| Proposed changes | Lacked Requirement 12 Mermaid diagram | Added Mermaid `flowchart TD` diagram to `Proposed changes` showing execution dependency flow | Proofreading, PR-003. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No public interface or production code is changed. The plan retargets eight test modules from `research_contract.parse_frontmatter` to `artifact_meta.read_text`, preserving all test cases and preparing for `bxupy8` to delete `parse_frontmatter`.
2. No. It touches only test modules under `tests/`, not commit locks or isolation machinery.
3. No, it is right-sized at 5 E-items in 1 task group across 8 test modules.
4. Yes. `- Scope-Paths:` explicitly lists all 8 test files plus the plan itself.
5. Yes. Mistakes in test retargeting could drop test coverage or assertions on research front-matter handling (clock parity, unsafe fields, dialect readers, archive moves).

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section C5 single metadata reader invariant and section 4.3); parent plan `k6jd6l` (Order 43); research `nj8zdp` guidance; prerequisite `sq6v7i` (Order 288); and call sites across the eight test modules.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`, with `- Highest E allocated: 05` preserved), dependency chain (`E-01 -> E-02 -> E-03 -> E-04 -> E-05`), `- Scope-Paths:` completeness (all 8 changed test modules and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause in Approval and execution gate (`PR-001`): gate lacked explicit `never a hand git mv` guard and omitted conditional runner/executor finalize clause required by `steps/s7-finalize.md`. Fixed in Gate.

### Step R3

- Checked: security, test execution isolation, leak sanitizer awareness, no mock leakage, no test-pinning of source structure (`AGENTS.md`). Verified that tests execute observable behavior and outcome assertions against `artifact_meta.read_text`.

### Step R4

- Checked: conformance with spec `4sd62s` C5 and 4.3, test retargeting preserving 100% of input cases across all 8 modules (156 passing tests total), determinism (`-p no:randomly -n 0` PIN rule), right-sizing (5 E-items, 8 work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs and per-test mapping), Architect (retargeting all remaining test front-matter parsing onto unified `artifact_meta.read_text`), Software Engineer (mapping dict lookups to typed State attributes), and Modest Executor (linear sequential flow with four large modules isolated and four small modules bundled).

### Step R6

- Checked: right-sizing at 5 E-items in 1 task group across 8 work `- Scope-Paths:` entries (`- Size assessment: standard`). Cleanly decoupled split from `k6jd6l`. No further decomposition needed.

### Step R7

- Checked: `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sq6v7i, executed:t4gl15` (all verified present under `.aw/records/plans/`), split parent `k6jd6l`, and downstream deletion plan `bxupy8` (Order 290). All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded three engineering decisions (`D-1..D-3`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-05` and `V-01..V-05` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and owner update.
- Verified 5-to-5 `E-*`/`V-*` bijection, `- Highest E allocated: 05`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-289-5lgpix-retarget-the-tests-that-still-call-parse-frontmatter.ipd.md:160 | Approval and execution gate omitted the explicit hand-mv guard and conditional runner/executor finalize clause, required by steps/s7-finalize.md and rubric G. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction and conditional runner/executor ownership clause to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-289-5lgpix-retarget-the-tests-that-still-call-parse-frontmatter.ipd.md:123 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261109-metastore-289-5lgpix-retarget-the-tests-that-still-call-parse-frontmatter.ipd.md:79 | Proposed changes lacked a Mermaid diagram required by requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing execution dependency flow. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Some tests assert on `parse_frontmatter` returning None for a malformed block; how is that kept? | Assert on the matching `artifact_meta.read_text` outcome (a defect or empty fields) and keep the case; if the observable differs, report it rather than weakening the test. | Delete malformed-block test cases (rejected: loses regression coverage on malformed front-matter handling). | `5lgpix` OQ-01, `4sd62s` 4.3 | yes |
| D-2 | How should test modules inspect parsed fields from `artifact_meta.read_text`? | Read through `artifact_meta.State` typed attributes or `State.fields` dictionary, ensuring parity with the previous dictionary-based assertions without coupling to private parsing internals. | Use low-level YAML or regex parsing directly in tests (rejected: violates spec `4sd62s` C5 single-reader invariant). | `5lgpix` Detailed Implementation Checklist, `4sd62s` C5 | yes |
| D-3 | Grouping of the eight test modules across execution items: | Allocate one E-item to each of the four high-volume modules (`test_research_cmd_create.py`, `test_research_rename_frontmatter.py`, `test_research_archive.py`, `test_research_descriptive_safety.py`) and group the four low-volume modules into E-05. | Split into eight separate child plans (rejected: unnecessary fragmentation for small 1-3 reference test modules; plan stays within right-sizing bounds at 5 E-items). | `5lgpix` Scope check, `IPD-Z603` | yes |
