# Review findings: plan qtvk2q

- Subject-Id: qtvk2q
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `4defb077b` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-263-qtvk2q-move-setter-byte-assertions-of-batch-s11-except-question-vis.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_production_baseline_same_commit.py tests/test_production_correction_turn.py tests/test_production_resume_handoff.py tests/test_production_set_check.py tests/test_prompts_set_surface.py tests/test_question_drain.py tests/test_question_parking.py tests/test_question_preflight.py` printed `86 passed in 89.25s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-004 | MD-15, Section 7.2 |
| Batch rule step 1 | Piped directly into `.aw/state/qtvk2q/<batch>-before.txt` | Prepended `mkdir -p .aw/state/qtvk2q/ && ` to guarantee directory existence on fresh worktrees | PR-002 |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-003 (Requirement 12b) |
| `## Open questions` | OQ-01 had `- Owner: none` | Updated `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite metastore symbols from `1ajqaa`, `59aiyh`, `90iqr1`, `dcerjg`, `g5hpbb`, `iog3cw`, or `ya4ee4` are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No public interface or spec is changed. The plan converts setter-byte assertions across 8 test modules (`tests/test_production_baseline_same_commit.py`, `tests/test_production_correction_turn.py`, `tests/test_production_resume_handoff.py`, `tests/test_production_set_check.py`, `tests/test_prompts_set_surface.py`, `tests/test_question_drain.py`, `tests/test_question_parking.py`, `tests/test_question_preflight.py`) to use the format-aware field helper (`assert_field`/`assert_no_field`).
2. No. It touches only test modules under `tests/`; no production or security/isolation guard code is modified.
3. No. Sized cleanly: 3 E-items in 1 task group across 8 test modules and the plan file itself.
4. Yes. `- Scope-Paths:` explicitly declares all 8 test modules and the plan itself.
5. Low. Test conversion only; deterministic before/after per-test outcome lists verify parity (`diff` prints nothing).

AW-TIER: standard

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and 7 step 9, C10a); parent split plan `w13bkp` (Order 44); research `nj8zdp` guidance; prerequisite helper plan `j5fqax`/`iog3cw`; and target assertions in the 8 test modules.
- Found owner violation in OQ-01 (`PR-004`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-4 in `### Decisions`.

### Step R2

- Checked: 1:1 bijection between E-01..E-03 and V-01..V-03; `- Scope-Paths:` completeness; `- Item-Dependencies:` resolution (`executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:ya4ee4`); and verification reachability.
- Verified that V-01..V-03 demand verifiable evidence (empty diff of `.aw/state/qtvk2q/S11a-{before,after}.txt` and `S11b-{before,after}.txt`, before and after F-28 `rg -c` counts, empty union diff, F-28 and F-29 tables, clean sanitize output, and path-scoped commits).

### Step R3

- Checked: Security and privacy lens. Test assertion refactoring touches no trust boundaries, secrets, credentials, or sandboxes.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density.
- Conformance with spec `4sd62s` C10a (main keeps one metadata format at each commit; converted tests assert through active format and continue asserting exact bullet lines under legacy format), determinism (`-p no:randomly -n 0` PIN rule across all 8 test modules), right-sizing (3 E-items, 8 test Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step S5

- Checked: Open questions. OQ-01 resolved. Review decisions (D-1..D-4) recorded and verified (`Reversible: yes`). No blocking questions remain.

### Pass 2

- Re-read all revised sections of `qtvk2q`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | `.aw/records/plans/pending/20261109-metastore-263-qtvk2q-move-setter-byte-assertions-of-batch-s11-except-question-vis.ipd.md:138-143`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | The execution gate in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`") and lacked a narrow safety stop for missing prerequisite metastore symbols from `1ajqaa`, `59aiyh`, `90iqr1`, `dcerjg`, `g5hpbb`, `iog3cw`, or `ya4ee4`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize qtvk2q` itself"), clarified declaration-based scope fence with `--scope-ack`, and added narrow safety stop if prerequisite metastore symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Executability / Environment | `.aw/records/plans/pending/20261109-metastore-263-qtvk2q-move-setter-byte-assertions-of-batch-s11-except-question-vis.ipd.md:35-37` | Batch rule step 1 redirected output to `.aw/state/qtvk2q/<batch>-before.txt` without ensuring directory exists, which fails with `No such file or directory` in fresh isolated worktrees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/qtvk2q/ && ` to batch rule step 1 command (strong). |
| PR-003 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | `.aw/records/plans/pending/20261109-metastore-263-qtvk2q-move-setter-byte-assertions-of-batch-s11-except-question-vis.ipd.md:73-77`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the batch execution flow across E-01..E-03 (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | `.aw/records/plans/pending/20261109-metastore-263-qtvk2q-move-setter-byte-assertions-of-batch-s11-except-question-vis.ipd.md:112-117` | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should the plan execution gate specify lifecycle transition ownership and safety stops? | Add conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize qtvk2q` itself"), clarify scope fence declaration, and add a narrow safety stop if prerequisite metastore symbols from `1ajqaa`, `59aiyh`, `90iqr1`, `dcerjg`, `g5hpbb`, `iog3cw`, or `ya4ee4` are absent | Leave unconditional finalize instruction (violates `s7-finalize.md`); omit prerequisite safety stop | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`; `AGENTS.md` "Agent execution contract" | yes |
| D-2 | How should directory creation for `.aw/state/qtvk2q/` be handled in fresh isolated worktrees? | Prepend `mkdir -p .aw/state/qtvk2q/ && ` to the baseline capture instruction in batch rule step 1 | Assume `.aw/state/qtvk2q/` exists from earlier tasks | `.aw/records/plans/pending/20261109-metastore-263-qtvk2q-move-setter-byte-assertions-of-batch-s11-except-question-vis.ipd.md:35-37` | yes |
| D-3 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in `Proposed changes` illustrating the batch execution flow across E-01..E-03 | Omit diagram (violates Requirement 12b) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-4 | How should OQ-01's owner field be attributed? | Update `- Owner: plan author` | Leave `- Owner: none` (violates Check S5 attribution guidance) | `.aw/system/workflows/plan-review/steps/s5-questions.md:20-22` | yes |
