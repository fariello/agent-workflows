# Review findings: plan zgyna1

- Subject-Id: zgyna1
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `cc9a3a3e1` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (0 findings across all severities). Unmodified baseline test suites across the 3 target test modules passed with `117 passed in 13.04s` (`tests/test_status_set.py`: 110 passed, `tests/test_walkthrough_id6.py`: 4 passed, `tests/test_work_begin_plan_path_outside_root.py`: 3 passed). Live inspection against governing spec `4sd62s` (C10a, Section 6, Section 7 step 9, AC-1b), orchestrator `63ib9r` (row 62, `E-42`/`V-42`), parent split plan `iog3cw` (Order 44), sibling setter-byte batch plans (`j5fqax`, `87rvs2`, `rdg0qv`, `aqc3m6`, `wdz2l9`), and all 3 target test modules uncovered findings `PR-001..PR-006`, all fixed in place. Pass 2 re-checked `E-01..E-04` and `V-01..V-04`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with 0 findings across all severities.

### Proofreading

Checked `.aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted `never a hand git mv`, conditional runner/executor finalize ownership, and prerequisite/concurrent-edit safety stop | Added `never a hand git mv`, conditional runner/executor finalize clause, and narrow safety stop for concurrent edits or missing prerequisite field helper/builder | PR-001, `steps/s7-finalize.md` execution-contract rules. |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002, Technical Writing Standard Requirement 12(b). |
| Batch rule step 1 and `E-01` | Redirected output to `.aw/state/zgyna1/<batch>-before.txt` without ensuring directory creation | Added explicit `mkdir -p .aw/state/zgyna1` and baseline capture instruction into `E-01` and Batch rule step 1 | PR-003, R2 executability in fresh lane worktrees. |
| Open questions (`OQ-01`, `OQ-02`) | Recorded `- Owner: none` on resolved open questions | Updated to `- Owner: plan author` and logged decisions `D-1` and `D-2` in `### Decisions` | PR-004, `steps/s5-questions.md` owner attestation rule. |
| Front matter, line 20, `Step 0` | Retained template prompt blockquote, bare symbol citations in Step 0, lacked `Readiness` and `Review-Depth` | Replaced blockquote with compliance statement; qualified `Step 0` citations to `path::Symbol`; added `- Readiness: go-pending-approval`, `- Review-Depth: standard`, `- Status: reviewed`, and review history entry | PR-005, Technical Writing Standard Requirement 1, Section 11.1, and Step S7. |
| `## Findings` and `## Required tests / validation` | Omitted measured pre-conversion test characterization baseline for the 3 test modules and left `AC-1b` unqualified | Added context baseline (`117 passed in 13.04s` across all 3 modules at `cc9a3a3e1`), documented per-module test counts, and qualified `4sd62s` AC-1b | PR-006, R4 engineering rubric and R2 spec-citation clarity. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Converts setter-byte test assertions in batches S18, S19, and S20 to use the format-aware field helper `assert_field` / `assert_no_field` from `j5fqax`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes. Touches only test modules under `tests/` and the plan itself.
3. No. Compact child plan with 4 execution items across 2 task groups and 3 test modules in `- Scope-Paths:`.
4. Yes. `- Scope-Paths:` explicitly declares all 3 test modules and the plan itself.
5. Yes. An incorrect test conversion could weaken an assertion or miss exact-spelling cases, guarded by the batch rule requiring zero diff in outcome lists.

AW-TIER: standard

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C10a, Section 6, Section 7 step 9, AC-1b); orchestrator `63ib9r` (row 62, `E-42`/`V-42`); parent split plan `iog3cw` (Order 44); sibling setter-byte batch plans (`j5fqax`, `87rvs2`, `rdg0qv`, `aqc3m6`, `wdz2l9`); and all 3 target test modules in `tests/`.
- Checked: all 7 prerequisite plans in `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:ya4ee4`.
- Verified candidate setter-byte assertion sites across the 3 target modules and confirmed baseline tests pass (`117 passed in 13.04s`).

### Step R2

- Checked: 1:1 bijection between E-01..E-04 and V-01..V-04; `- Scope-Paths:` completeness; `- Item-Dependencies:`; and verification reachability.
- Added explicit directory creation in Batch rule step 1 and E-01 for gitignored `.aw/state/zgyna1/` to ensure clean saving of before-baseline outcome lists (PR-003).

### Step R3

- Checked: security, file paths, and temporary state isolation.
- Baselines are saved strictly under `.aw/state/zgyna1/` (gitignored), avoiding `/tmp` pollution and ensuring no untracked state is committed.
- Test-only changes; no production code or credentials touched.

### Step R4

- Checked: conceptual density, right-sizing, anti-regression, and backward compatibility.
- Right-sized: 82 candidate assertion lines divided into three focused batches (E-01 S18, E-02 S19, E-03 S20), followed by union verification, F-28 remaining match classification, and gate completion (E-04).
- Preserves exact test outcomes before and after across all 3 modules.

### Step S5

- Checked: no unresolved open questions; `OQ-01` and `OQ-02` are resolved and owned by `plan author` (PR-004). All five review decisions (D-1..D-5) are recorded and verified (`Reversible: yes`).

### Pass 2

- Re-read all revised sections of `zgyna1`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent --verbose` returned clean (`0` findings across all severities).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md:155-165; .aw/system/workflows/plan-review/steps/s7-finalize.md:33-46 | Approval and execution gate omitted "never a hand `git mv`", conditional runner/executor finalize ownership ("When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize zgyna1` itself"), and prerequisite field helper/builder safety stop. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added "never a hand `git mv`", conditional runner/executor finalize clause, and narrow prerequisite safety stop to gate. Recommendation strength: very strong. |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / R6 | .aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md:78-82; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | `## Proposed changes` contained only an ordered text list without the Mermaid flowchart diagram required by Technical Writing Standard Requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram in `## Proposed changes`. Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | R2 / Batch rule step 1 | .aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md:35,43 | Batch rule step 1 and E-01 directed saving baseline outputs to `.aw/state/zgyna1/<batch>-before.txt` without ensuring directory creation, which fails on fresh lane worktrees where `.aw/state/` is gitignored and absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/zgyna1` instruction into Batch rule step 1 and `E-01`. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | R1 / S5 / OQ-01 & OQ-02 | .aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md:107-119 | `OQ-01` and `OQ-02` carried `- Owner: none` on `- Status: resolved` questions, violating the owner attestation standard in `steps/s5-questions.md` Section 3.1 item 5. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `OQ-01` and `OQ-02` to `- Owner: plan author` and recorded decisions `D-1` and `D-2` in `### Decisions`. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Proofreading / S7 / Requirement 1 & Section 11.1 | .aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md:9-11,20,67-69 | Plan retained the authoring template prompt blockquote at line 20, used bare symbol citations in `Step 0` without path qualification, and lacked S7 front-matter outputs (`- Readiness:`, `- Review-Depth:`, `- Status: reviewed`, review history). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template prompt blockquote with technical writing compliance statement, qualified `Step 0` citations to `path::Symbol` (`tests/record_builder.py::RecordBuilder`, `agent_workflows/artifact_meta.py::read_text`), and wrote S7 front-matter fields and review history entry. Recommendation strength: very strong. |
| PR-006 | LOW | IN-SCOPE | R4 Engineering Rubric / Characterization baseline | .aw/records/plans/pending/20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md:76,99 | Plan omitted measured pre-conversion test characterization baseline for its 3 target test modules as context for step-4 outcome verification and left `AC-1b` unqualified without spec id `4sd62s`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added measured context baseline (`117 passed in 13.04s` across all 3 modules at HEAD `cc9a3a3e1`) to `## Findings` and `## Required tests / validation`, and qualified `4sd62s` AC-1b. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Why does this part run so late? | It carries `cxxmyv`'s dependencies, including `90iqr1` which depends on `9o83cr` and all phase-B deletion parts; running after them ensures earlier deletion retargets land first and no assertion is converted twice. | Run earlier in metastore schedule (rejected: would risk duplicate retargets on modules shared with `k6jd6l` E-08). | `zgyna1` `OQ-02`, orchestrator `63ib9r` row 62 | yes |
| D-2 | Can this run before the cutover without breaking C10a? | Yes: the format-aware field helper asserts through the active format and validates exact bullet spelling on the legacy format, preserving single-format invariants on `main`. | Defer all setter conversions to cutover commit (rejected: would hide hundreds of steps in an atomic cutover). | `zgyna1` `OQ-01`, spec `4sd62s` C10a | yes |
| D-3 | How should the plan execution gate specify lifecycle transition ownership and safety stops? | Add conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize zgyna1` itself"), clarify scope fence declaration with `--scope-reason`/`--scope-ack`, and add a narrow safety stop if prerequisite field helper from `j5fqax` or builder from `59aiyh` is absent. | Leave unconditional finalize instruction (violates `s7-finalize.md`); omit prerequisite safety stop. | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`, `AGENTS.md` | yes |
| D-4 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in Proposed changes illustrating the 4-step pipeline (independent batch conversions S18, S19, S20 feeding union verification, F-28 compilation, and path-scoped commit). | Omit diagram (violates Requirement 12b). | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-5 | How should baseline directory creation be handled? | Add explicit `mkdir -p .aw/state/zgyna1` instruction into Batch rule step 1 and `E-01`. | Rely on ambient existence of directory (would fail on fresh worktrees where `.aw/state/` is gitignored). | `zgyna1` Batch rule step 1, clean worktree check | yes |
