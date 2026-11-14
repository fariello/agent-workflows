# Review findings: plan 87rvs2

- Subject-Id: 87rvs2
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `43b38f1ee` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (0 findings across all severities). Unmodified baseline test suites across the 8 target test modules passed with `123 passed in 32.20s` (128 collected across all 8 modules: `tests/test_backlog_set_adapter.py`: 8, `tests/test_backlog_transition_authority.py`: 8, `tests/test_backlog_transition_gate.py`: 14, `tests/test_clean_target_zero_delta_e2e.py`: 2, `tests/test_doctor.py`: 38, `tests/test_gate_pair_validation_parity.py`: 12, `tests/test_gradcover_end_to_end.py`: 5, `tests/test_group_verb_policy.py`: 41). Live inspection against governing spec `4sd62s` (C10a, Section 6, Section 7 step 9, AC-1b), orchestrator `63ib9r` (row 59, `E-39`/`V-39`), parent split plan `iog3cw` (Order 44), sibling setter-byte batch plans (`j5fqax`, `rdg0qv`, `aqc3m6`, `wdz2l9`), and all 8 target test modules uncovered findings `PR-001..PR-006`, all fixed in place. Pass 2 re-checked `E-01..E-04` and `V-01..V-04`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with 0 findings across all severities.

### Proofreading

Checked `.aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted `never a hand git mv`, conditional runner/executor finalize ownership, and prerequisite/concurrent-edit safety stop | Added `never a hand git mv`, conditional runner/executor finalize clause, and narrow safety stop for concurrent edits or missing prerequisite field helper/builder | PR-001, `steps/s7-finalize.md` execution-contract rules. |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002, Technical Writing Standard Requirement 12(b). |
| Batch rule step 1 and `E-01` | Redirected output to `.aw/state/87rvs2/<batch>-before.txt` without ensuring directory creation | Added explicit `mkdir -p .aw/state/87rvs2` and baseline capture instruction into `E-01` and Batch rule step 1 | PR-003, R2 executability in fresh lane worktrees. |
| Open questions (`OQ-01`, `OQ-02`) | Recorded `- Owner: none` on resolved open questions | Updated to `- Owner: plan author` and logged decisions `D-1` and `D-2` in `### Decisions` | PR-004, `steps/s5-questions.md` owner attestation rule. |
| Front matter, line 20, `Step 0` | Retained template prompt blockquote, bare symbol citations in Step 0, lacked `Readiness` and `Review-Depth` | Replaced blockquote with compliance statement; qualified `Step 0` citations to `path::Symbol`; added `- Readiness: go-pending-approval`, `- Review-Depth: standard`, `- Status: reviewed`, and review history entry | PR-005, Technical Writing Standard Requirement 1, Section 11.1, and Step S7. |
| `## Findings` and `## Required tests / validation` | Omitted measured pre-conversion test characterization baseline for the 8 test modules and left `AC-1b` unqualified | Added context baseline (`123 passed in 32.20s`, 128 collected across all 8 modules at `43b38f1ee`), documented per-module test counts, and qualified `4sd62s` AC-1b | PR-006, R4 engineering rubric and R2 spec-citation clarity. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Converts setter-byte test assertions in batches S05, S06, and S07 to use the format-aware field helper `assert_field` / `assert_no_field` from `j5fqax`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes. Touches only test modules under `tests/` and the plan itself.
3. No. Compact child plan with 4 execution items across 2 task groups and 8 test modules in `- Scope-Paths:`.
4. Yes. `- Scope-Paths:` explicitly declares all 8 test modules and the plan itself.
5. Yes. An incorrect test conversion could weaken an assertion or miss exact-spelling cases, guarded by the batch rule requiring zero diff in outcome lists before and after.

AW-TIER: standard

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C10a, Section 6, Section 7 step 9, AC-1b); orchestrator `63ib9r` (row 59, `E-39`/`V-39`); parent split plan `iog3cw` (Order 44); predecessor and prerequisite plans in `- Item-Dependencies:` (`1ajqaa`, `59aiyh`, `90iqr1`, `dcerjg`, `g5hpbb`, `iog3cw`, `ya4ee4`); sibling setter-byte batch plans (`j5fqax`, `rdg0qv`, `aqc3m6`, `wdz2l9`); and all 8 target test modules on disk at HEAD `43b38f1ee` (`tests/test_backlog_set_adapter.py`, `tests/test_backlog_transition_authority.py`, `tests/test_backlog_transition_gate.py`, `tests/test_clean_target_zero_delta_e2e.py`, `tests/test_doctor.py`, `tests/test_gate_pair_validation_parity.py`, `tests/test_gradcover_end_to_end.py`, `tests/test_group_verb_policy.py`).
- Checked: candidate setter-byte assertion lines across all 8 modules match F-28 (57 lines total: S05 13 lines, S06 17 lines, S07 27 lines).
- Checked: all 7 prerequisite plans in `- Item-Dependencies:` (`1ajqaa`, `59aiyh`, `90iqr1`, `dcerjg`, `g5hpbb`, `iog3cw`, `ya4ee4`) resolve under `.aw/records/plans/` and match `63ib9r` row 59 verbatim.
- Found bare symbol citations in `Step 0` (`PR-005`), `- Owner: none` on resolved `OQ-01` and `OQ-02` (`PR-004`), and unqualified `AC-1b` (`PR-006`). Fixed all in place.

### Step R2

- Checked: 1:1 `E-*`/`V-*` bijection (`E-01..E-04` <-> `V-01..V-04`, `- Highest E allocated: 04`), task ordering (`E-01, E-02, E-03 -> E-04`), `- Scope-Paths:` completeness (all 8 target test files plus the plan), live-artifact re-derivation (batch rule outcome lists compared before and after), and reachability of every `V-*` demand.
- Found missing conditional runner/executor finalize ownership, `never a hand git mv` guard, and prerequisite/concurrent-edit safety stop in `## Approval and execution gate` (`PR-001`), plus missing `mkdir -p .aw/state/87rvs2` in Batch rule step 1 and `E-01` (`PR-003`). Fixed both in place.

### Step R3

- Checked: security, privacy, isolation, and trust boundaries. Edits are confined to test files under `tests/` and planning records; no production code under `agent_workflows/` or `tools/` is modified. The format-aware field helper asserts against the active format without reading production source files, preserving behavioral verification integrity and sandbox constraints.

### Step R4

- Checked: engineering rubric (`A` correctness/atomicity, `C` architecture/operability, `D` anti-regression, `E` testing/verification, `F` KISS/principles, right-sizing/conceptual density, and spec/doc sync).
- Sized cleanly: 4 E-items (3 independent batch items covering 13, 17, and 27 candidate lines, plus 1 union finishing item) across 8 test modules, each strictly bounded by the 30-conversion right-sizing guideline.
- Measured unmodified baseline across all 8 test modules at HEAD `43b38f1ee` (`123 passed in 32.20s`, 128 collected across all 8 modules) and recorded per-module counts as context in `## Findings` and `## Required tests / validation` (`PR-006`).

### Step R5

- Checked: eight reviewer personas by reference to `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas` (QA/QC: deterministic sorted per-batch outcome-list `diff` before and after; Testing/Regression: 128 collected tests preserved with zero regressions; Architect: decouples test assertions from active format prior to cutover commit `cxxmyv` C10a; Software Engineer: format-aware field helper `assert_field` prevents test churn at cutover; Novice/Executor: explicit `mkdir -p .aw/state/87rvs2` and Mermaid diagram eliminate ambiguity; UI/UX, Power User, Stakeholder: zero runtime disruption).

### Step R6

- Checked: decomposition and splitting (`steps/r6-decomposition.md` and research `nj8zdp`). `87rvs2` is already a dedicated chunk of `iog3cw` (Order 44), holding batches S05, S06, and S07 (4 E-items, 8 work test paths, 57 candidate lines). Right-sized and requires no further decomposition.

### Step R7

- Checked: cross-plan consistency across Set `metastore`: orchestrator `63ib9r` row 59 and `E-39`/`V-39`, parent `iog3cw` (Order 44, F-28), helper provider `j5fqax` (Order 261, batches S01..S04), sibling batch plans `rdg0qv` (Order 60, batches S08..S10), `aqc3m6` (Order 61, batches S15..S17), and `wdz2l9` (Order 270), and cutover plan `cxxmyv` (Order 13, E-07). Module partitions and dependency edges align across all plans.

### Step S5

- Checked: pre-existing `OQ-01` and `OQ-02` (`Blocking: no`, `Status: resolved`) and all review findings `PR-001..PR-006`. Updated both open questions from `- Owner: none` to `- Owner: plan author` and logged `D-1..D-5` in `### Decisions` (all `Reversible: yes`). All findings are `FIXED`; zero open or deferred findings and zero human-gated questions remain (`questions: []`).

### Pass 2

- Re-checked the revised plan after applying `PR-001..PR-006`, verifying structural preservation (`E-01..E-04` <-> `V-01..V-04`, `- Highest E allocated: 04`, unchanged `- Scope-Paths:` and `- Item-Dependencies:`), consistent citations across `Step 0`, `Findings`, `Proposed changes`, `V-01..V-04`, and Gate, and `0` findings from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md:160-166 | Approval and execution gate instructed `aw ipd finalize` unconditionally without conditional runner/executor ownership or an explicit `never a hand git mv` guard, and omitted the narrow safety stop for concurrent-edit conflicts or absent prerequisite field helper from `j5fqax` or builder from `59aiyh`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `never a hand git mv`, conditional runner/executor finalize ownership, and the narrow safety rule to `## Approval and execution gate`. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing / Requirement 12b | .aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md:82-99 | `## Proposed changes (ordered, validatable)` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `## Proposed changes (ordered, validatable)`. Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Executability / Environment / Batch rule | .aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md:39,44 | Batch rule step 1 and E-01 instructed saving baseline outputs to `.aw/state/87rvs2/<batch>-before.txt` without ensuring directory creation, which fails on fresh lane worktrees where `.aw/state/` is gitignored and absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/87rvs2` instruction into Batch rule step 1 and `E-01`. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | R1 / S5 / OQ-01 & OQ-02 | .aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md:124,131 | `OQ-01` and `OQ-02` carried `- Owner: none` on `- Status: resolved` questions, violating the owner attestation standard in `steps/s5-questions.md` Section 3.1 item 5. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `OQ-01` and `OQ-02` to `- Owner: plan author` and recorded decisions `D-1` and `D-2` in `### Decisions`. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Proofreading / S7 / Requirement 1 & Section 11.1 | .aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md:9-11,22,68-73 | Plan retained the authoring template prompt blockquote at line 20, used bare symbol citations in `Step 0` without path qualification, and lacked S7 front-matter outputs (`- Readiness:`, `- Review-Depth:`, `- Status: reviewed`, review history). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template prompt blockquote with technical writing compliance statement, qualified `Step 0` citations to `path::Symbol` (`tests/record_builder.py::RecordBuilder`, `agent_workflows/artifact_meta.py::read_text`), and wrote S7 front-matter fields and review history entry. Recommendation strength: very strong. |
| PR-006 | LOW | IN-SCOPE | R4 Engineering Rubric / Characterization baseline | .aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md:78-79,114-118 | Plan omitted measured pre-conversion test characterization baseline for its 8 target test modules as context for step-4 outcome verification and left `AC-1b` unqualified without spec id `4sd62s`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added measured context baseline (`123 passed in 32.20s`, 128 collected across all 8 modules at HEAD `43b38f1ee`) to `## Findings` and `## Required tests / validation`, and qualified `4sd62s` AC-1b. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Why does this part run so late? | It carries `cxxmyv`'s dependencies, including `90iqr1` which depends on `9o83cr` and all phase-B deletion parts; running after them ensures earlier deletion retargets land first and no assertion is converted twice. | Run earlier in metastore schedule (rejected: would risk duplicate retargets on modules shared with `k6jd6l` E-08). | `87rvs2` `OQ-02`, orchestrator `63ib9r` row 59 | yes |
| D-2 | Can this run before the cutover without breaking C10a? | Yes: the format-aware field helper asserts through the active format and validates exact bullet spelling on the legacy format, preserving single-format invariants on `main`. | Defer all setter conversions to cutover commit (rejected: would hide hundreds of steps in an atomic cutover). | `87rvs2` `OQ-01`, spec `4sd62s` C10a | yes |
| D-3 | How should the plan execution gate specify lifecycle transition ownership and safety stops? | Add conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 87rvs2` itself"), clarify scope fence, and add a narrow safety stop if prerequisite field helper from `j5fqax` or builder from `59aiyh` is absent. | Leave unconditional finalize instruction (violates `s7-finalize.md`); omit prerequisite safety stop. | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`, `AGENTS.md` "Agent execution contract" | yes |
| D-4 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in Proposed changes illustrating the 3-step pipeline (independent batch conversions feeding union verification, F-28 compilation, and path-scoped commit). | Omit diagram (violates Requirement 12b). | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-5 | How should baseline directory creation be handled? | Add explicit `mkdir -p .aw/state/87rvs2` instruction into Batch rule step 1 and `E-01`. | Rely on ambient existence of directory (would fail on fresh worktrees where `.aw/state/` is gitignored). | `.aw/records/plans/pending/20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md:34-36` | yes |
