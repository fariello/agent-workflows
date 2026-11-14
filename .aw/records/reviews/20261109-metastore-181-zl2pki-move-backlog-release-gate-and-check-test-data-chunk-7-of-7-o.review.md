# Review findings: ipd zl2pki

- Subject-Id: zl2pki
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `466d15eb7` in an isolated runner review-sweep lane worktree. The lane-input
copy is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review
snapshot was needed. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize`
was clean after them. Pass 1 and Pass 2 verified the plan against governing spec `4sd62s` (Section 6, Section 7 step 6),
orchestrator `63ib9r` (row 181), split origin plan `x05v02` (E-04), research guidance `nj8zdp`, and prerequisite
plans `653ndz` (Order 49) and `9rgn2w` (Order 37).

### Proofreading

Checked `.aw/records/plans/pending/20261109-metastore-181-zl2pki-move-backlog-release-gate-and-check-test-data-chunk-7-of-7-o.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Line 20, front matter | Scaffold blockquote instruction; missing `Review-Depth:` and `Readiness:` | Replaced line 20 with standard compliance blockquote; added `- Review-Depth: standard` and `- Readiness: go-pending-approval` | PR-001. |
| Batch rule step 1 | Redirected to `.aw/state/59aiyh/<batch>-files.txt` without directory creation | Added `mkdir -p .aw/state/59aiyh && ` before output redirection | PR-002. |
| `OQ-01` | `- Owner: none` on resolved question | Updated `- Owner:` to `plan author (carried from x05v02)` | PR-003. |
| `Approval and execution gate` | Omitted explicit hand-mv guard and conditional runner/executor finalize clause | Added standard hand-mv restriction and conditional runner/executor ownership clause | PR-004. |
| `Proposed changes` | Numbered list without Mermaid diagram | Added Requirement 12 `flowchart TD` Mermaid diagram | PR-001. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Converts test fixture data in 7 internal backlog, release-gate and check test modules to `RecordBuilder` calls; touches no public interface or CLI contract.
2. No. Modifies no authorization gates, commit locks, sandbox boundaries, or worktree isolation logic.
3. No. 3 E-items in 2 task groups, bounded to 7 test modules of subset G2b.
4. No. Lists 8 Scope-Paths (the 7 test modules and the plan itself).
5. No. Test code only; batch rule requires identical per-test outcome lists before and after; easily reversible via git.

AW-TIER: standard

### Step R1

- Checked: All 7 test modules exist on disk at HEAD `466d15eb7` (`tests/test_check_ci_local_parity.py`, `tests/test_check_finding_path_relativity.py`, `tests/test_check_recovery_fidelity.py`, `tests/test_check_severity_tally.py`, `tests/test_decision_ref_resolution.py`, `tests/test_production_baseline_same_commit.py`, `tests/test_production_checks_trace.py`).
- Checked: Private record-building helpers cited in E-01 (`_seed_plans`, `_seed_releases`, `_seed_backlog`, `_seed_release_gates` in `tests/test_check_ci_local_parity.py`) exist in code at split.
- Checked: All dependencies in `- Item-Dependencies:` (`653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`) resolve in `.aw/records/plans/` and match orchestrator `63ib9r` row 181.
- Checked: Live test suite run of all 7 modules confirmed 63 passing tests in 26.49s.

### Step R2

- Checked: 1:1 `E-*`/`V-*` bijection is exact (`E-01..E-03` <-> `V-01..V-03`), with `- Highest E allocated: 03`.
- Reachability: `V-01` and `V-02` verify empty diff of per-batch outcome lists, remaining match reason classes, codemod reports, hand counts <= 25, and helper deletions; `V-03` verifies empty diff of sorted concatenation against `zl2pki-union-after.txt`, runs bare `python3 -m pytest`, checks `aw sanitize --agent`, and verifies path-scoped commits.

### Step R3

- Checked: Test modules only, no production code touched.
- Commits are path-scoped to `- Scope-Paths:`. `aw sanitize --agent` runs clean.

### Step R4

- A (State & atomicity): Out-of-tree state files under `.aw/state/59aiyh/` ensure before/after outcome lists are compared deterministically.
- C (Architecture & operability): Moves test data onto `tests/record_builder.py` in phase B per spec `4sd62s` section 6 and section 7 step 6, preparing for format cutover in Order 13.
- D & E (Anti-regression & verification): Batch rule enforces identical per-test outcome lists before and after; hand conversions are capped at 25 per item; dead private helpers removed cleanly.
- Spec sync: Implements test data conversion for 7 backlog, release-gate and check test modules under `4sd62s` section 6.

### Step R5

- Checked through review personas:
  - QA / QC: Verified identical per-test outcome lists guarantee zero test regressions across all 63 tests.
  - Test Engineer: Verified clean helper cleanup and format-independent record building.
  - Technical Writer: Added Requirement 12 Mermaid flowchart and replaced authoring prompt boilerplate with standard compliance blockquote.

### Step R6

- Decomposition check: 3 E-items in 2 task groups, 7 work Scope-Paths. Cleanly chunked from `x05v02` per research `nj8zdp` guidance (at most 5 E-items, 8 work Scope-Paths). No further split needed.

### Step R7

- Cross-plan consistency: Verified coordination across Set metastore:
  - Prerequisite `653ndz` (Order 49) builds the codemod.
  - Prerequisite `9rgn2w` (Order 37) builds the shared record builder.
  - Origin plan `x05v02` (Order 38) coordinates subset G1a/G1b/G2a/G2b.
  - Chunk 7 is `zl2pki` (Order 181).
  - All chunk module lists are disjoint.
  - Orchestrator `63ib9r` row 181 aligns with this exact decomposition.

### Step S5

- Checked: OQ-01 attribution updated from `none` to `plan author (carried from x05v02)`. Zero open questions remain. All findings `FIXED` in place. No human decision needed.

### Pass 2

- Verified `aw ipd lint --phase author --agent` clean (0 findings).
- Verified `aw ipd lint --phase review-finalize --agent` clean (0 findings).
- Verified zero em or en dashes, zero absolute file paths, zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | LOW | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261109-metastore-181-zl2pki-move-backlog-release-gate-and-check-test-data-chunk-7-of-7-o.ipd.md:22` | Authoring template prompt blockquote present; missing front-matter metadata (`- Review-Depth: standard`, `- Readiness: go-pending-approval`); `Proposed changes` lacked a Requirement 12 Mermaid diagram. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template line with standard compliance blockquote, added `- Review-Depth: standard` and `- Readiness: go-pending-approval` to front matter, and added `flowchart TD` Mermaid diagram to `Proposed changes`. |
| PR-002 | MEDIUM | IN-SCOPE | R2 Executability / Batch Rule | `.aw/records/plans/pending/20261109-metastore-181-zl2pki-move-backlog-release-gate-and-check-test-data-chunk-7-of-7-o.ipd.md:39` | Batch rule step 1 redirects output to `.aw/state/59aiyh/<batch>-files.txt` without creating the gitignored directory first, which fails with `No such file or directory` in fresh isolated worktrees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `mkdir -p .aw/state/59aiyh && ` to batch rule step 1 command. |
| PR-003 | LOW | IN-SCOPE | S5 Questions & Governance | `.aw/records/plans/pending/20261109-metastore-181-zl2pki-move-backlog-release-gate-and-check-test-data-chunk-7-of-7-o.ipd.md:143` | Resolved open question `OQ-01` carried `- Owner: none`, leaving ownership unattributed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `- Owner:` on `OQ-01` to `plan author (carried from x05v02)`. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / S7 / Approval and execution gate | `.aw/records/plans/pending/20261109-metastore-181-zl2pki-move-backlog-release-gate-and-check-test-data-chunk-7-of-7-o.ipd.md:178` | Approval and execution gate omitted the explicit hand-mv guard and conditional runner/executor finalize clause, required by `steps/s7-finalize.md` and rubric G. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction and conditional runner/executor ownership clause to Gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should directory creation for `.aw/state/59aiyh/` be handled in fresh isolated worktrees? | Prepend `mkdir -p .aw/state/59aiyh && ` to batch rule step 1 command | Assume `.aw/state/59aiyh/` exists from earlier plans | Prevents shell redirection failure in fresh isolated worktree lanes where `.aw/state/59aiyh/` does not yet exist | yes |
| D-2 | How should ownership of resolved open question `OQ-01` be attributed? | Update `- Owner: none` to `- Owner: plan author (carried from x05v02)` to reflect who authored the resolution | Leave `- Owner: none` | `steps/s5-questions.md` Section 3.1 and `x05v02` split provenance | yes |
| D-3 | How should runner versus hand finalize execution be distinguished in the lifecycle transition clause? | Add conditional runner/executor ownership clause explicitly noting runner finalizes on automated runs and hand executor runs `aw ipd finalize zl2pki` | Leave generic finalize mention | `steps/s7-finalize.md` Section 4 and rubric G | yes |
