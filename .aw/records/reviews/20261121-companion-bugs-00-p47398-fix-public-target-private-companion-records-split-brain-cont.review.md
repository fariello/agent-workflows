# Review findings: ipd p47398

- Subject-Id: p47398
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T141636Z-2560095`) for Order-00 orchestrator `p47398` (Set `companion-bugs`). The target plan `.aw/records/plans/pending/20261121-companion-bugs-00-p47398-fix-public-target-private-companion-records-split-brain-cont.ipd.md` was committed and unchanged, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` `IPD-C802` info advisories on Validation boilerplate line 102) and `aw ipd coverage p47398` returned `Orchestrator p47398 is ready for review.`. Check T was skipped per `plan-review.md` step 3 and spec `k3yx72` Section 5.1 (Order-00 orchestrators are not rated by T; `- Review-Depth: orchestrator`). Inspection of backlog `rvxmzz` and all three executed children of Set `companion-bugs` (`mnsbzt`, `pbdtss`, `v8tqje`) surfaced two `MEDIUM` and one `LOW` finding (`PR-001..PR-003`), all fixed in place. After revisions, `aw ipd coverage p47398 --no-commit` re-verified semantic coverage (`pass`, fingerprint `3f7e83a807d0`, `Orchestrator p47398 is ready for review.`). Pass 2 re-checked the full revised orchestrator, confirmed `3/3` `E-*`/`V-*` bijection, `IPD-S407` row conformance, `IPD-S408` coverage readiness, and clean `aw ipd lint --phase review-finalize --agent` (`0` errors, `0` warnings, `0` advisories), clearing `p47398` for human approval (`go-pending-approval`).

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Scope`, `Mermaid`, `E-02`, `Child IPDs`, `Completion criteria`, `Cross-IPD validation`, `Required tests / validation` | Listed stale `.aw/records/plans/pending/...` child paths, omitted `agent_workflows/placement_switch.py` (`mnsbzt`) and `agent_workflows/artifact_core.py` (`pbdtss`), omitted companion durability/evidence specifics, and listed only 3 of the 6 test suites executed in `v8tqje` `V-05` | Updated child `File` column paths to `.aw/records/plans/executed/...`, standardized module citations to repository paths (`agent_workflows/...`), added `placement_switch.py` and `artifact_core.py`, synced `E-02` / `Completion criteria` / Mermaid, and listed all 6 whole-Set verification test suites executed by `v8tqje` | PR-001, PR-003, technical writing standard Req 12(d)-(e) |
| `Validation and cross-check` boilerplate | Carried two em dashes on line 102 (`IPD-C802`) | Replaced the two em dashes with commas | PR-003 |
| `Approval and execution gate` | Described automatic runner retirement without stating approval precondition, no-hand-`git mv` rule, or never-push rule | Added `- Status: approved` and resolved-blocking-OQ precondition, prohibited hand-rolled `git mv` and unrequested pushes, and stated conditional runner retirement vs standalone `aw ipd finalize p47398` | PR-002, `steps/r2-executability.md`, `steps/s7-finalize.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261121-companion-bugs-01-rvxmzz-companion-records-split-brain.backlog.md`, orchestrator `p47398`, and all three executed child plans on disk: `.aw/records/plans/executed/20261121-companion-bugs-01-mnsbzt-companion-storage-layout-git-detection-target-containment-an.ipd.md`, `.aw/records/plans/executed/20261121-companion-bugs-02-pbdtss-unified-companion-records-resolution-across-doctor-check-eng.ipd.md`, and `.aw/records/plans/executed/20261121-companion-bugs-03-v8tqje-companion-safe-runner-prompts-record-routing-and-public-targ.ipd.md`.
- Confirmed all three children reached `- Status: executed` in `.aw/records/plans/executed/` with all `V-*` items passing (including `v8tqje` `V-05`: `189 passed` across the 6 whole-Set/anti-regression suites, `2661 passed` in `aw suite`, `0` mypy issues, `0` leak findings).
- Found stale `pending/` paths in `## Child IPDs`, omitted `agent_workflows/placement_switch.py` (`mnsbzt`) and `agent_workflows/artifact_core.py` (`pbdtss`), and omitted 3 anti-regression test suites run by `v8tqje` (`PR-001`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), `IPD-S407` orchestrator checklist row conformance (`CONFIRM <id6> REACHED executed` for `mnsbzt`, `pbdtss`, `v8tqje`), `IPD-S408` orchestrator coverage (`aw ipd coverage p47398` passed both before edits and after revisions with fresh fingerprint `3f7e83a807d0`), `- Item-Dependencies: executed:mnsbzt, executed:pbdtss, executed:v8tqje` (all three satisfied on disk), `- Scope-Paths:` (orchestrator file only), and `Approval and execution gate` (`PR-002`).

### Step R7

- Checked: full Set `companion-bugs` roll-up (`p47398` Order 00, `mnsbzt` Order 01, `pbdtss` Order 02, `v8tqje` Order 03) against backlog `rvxmzz` (all 9 defects and all 7 acceptance criteria).
- Verified complete, non-overlapping ownership across the Set: `mnsbzt` (`rvxmzz` items 1, 2, 4, 5, 9 / AC-1, AC-2, AC-3, AC-5), `pbdtss` (`rvxmzz` items 3, 6 + `mnsbzt`'s carried `project_context.py` step 8 durability fix / AC-4), and `v8tqje` (`rvxmzz` items 6, 7, 8 + whole-Set validation / AC-6, AC-7), with zero overlap against concurrent `metastore` (`agent_workflows/artifact_meta.py`).
- Synced `p47398` child paths, module lists, and whole-Set test suite inventory with the executed children (`PR-001`).

### Step S5

- Checked: `## Open questions` (`None.`), all findings `PR-001..PR-003` (all Low Remediation Risk, fixed in place), and askme three-way sort. Zero human-owned or blocking questions remain; zero self-resolved `Reversible: no` decisions were taken.

### Pass 2

- Re-checked: full revised orchestrator `.aw/records/plans/pending/20261121-companion-bugs-00-p47398-fix-public-target-private-companion-records-split-brain-cont.ipd.md` after child-table, scope, validation-suite, and gate updates.
- Swept superseded tokens (stale `.aw/records/plans/pending/20261121-companion-bugs-0[123]-`, em dashes): zero stale occurrences remain.
- Confirmed `3/3` `E-*`/`V-*` bijection, `- Highest E allocated: 03`, `- Readiness: go-pending-approval`, `- Review-Depth: orchestrator`, `- Status: reviewed`, current `- Coverage: pass` (`3f7e83a807d0`), `aw ipd coverage p47398` ready, and clean `aw ipd lint --phase review-finalize --agent` (`0` errors, `0` warnings, `0` advisories).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | R1 / R7 / Cross-Plan Rollup Consistency | `.aw/records/plans/pending/20261121-companion-bugs-00-p47398-fix-public-target-private-companion-records-split-brain-cont.ipd.md:6,68-70,81,94`, `.aw/records/plans/executed/20261121-companion-bugs-01-mnsbzt-companion-storage-layout-git-detection-target-containment-an.ipd.md:6`, `.aw/records/plans/executed/20261121-companion-bugs-02-pbdtss-unified-companion-records-resolution-across-doctor-check-eng.ipd.md:6`, `.aw/records/plans/executed/20261121-companion-bugs-03-v8tqje-companion-safe-runner-prompts-record-routing-and-public-targ.ipd.md:127` | `## Child IPDs` listed stale `.aw/records/plans/pending/...` paths for all three already-executed children (`mnsbzt`, `pbdtss`, `v8tqje`); `Scope` and `Child IPDs` omitted `agent_workflows/placement_switch.py` (`mnsbzt`) and `agent_workflows/artifact_core.py` (`pbdtss`); `E-02` / `Completion criteria` omitted companion durability and evidence resolution; and `Cross-IPD validation` / `Required tests` listed only 3 of the 6 test suites executed by `v8tqje` (`V-05`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Scope`, `Mermaid`, `E-02`, `Child IPDs`, `Completion criteria`, `Cross-IPD validation`, and `Required tests / validation` to reflect executed child paths, full module scope, and all 6 verification test suites, and re-verified `aw ipd coverage p47398` (`pass`, fingerprint `3f7e83a807d0`). Recommendation strength: very strong. |
| PR-002 | MEDIUM | IN-SCOPE | R2 / S7 / Approval and execution gate | `.aw/records/plans/pending/20261121-companion-bugs-00-p47398-fix-public-target-private-companion-records-split-brain-cont.ipd.md:124`, `.aw/system/workflows/plan-review/steps/r2-executability.md:57-60`, `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | `Approval and execution gate` described runner retirement but omitted the `- Status: approved` and resolved-blocking-OQ precondition, the prohibition against hand-rolling `git mv` to `.aw/records/plans/executed/`, and the never-push rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Approval and execution gate` with explicit approval/resolved-OQ precondition, no-hand-`git mv` and never-push prohibitions, and conditional runner retirement vs standalone `aw ipd finalize p47398` ownership. Recommendation strength: very strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical Writing Standard | `.aw/records/plans/pending/20261121-companion-bugs-00-p47398-fix-public-target-private-companion-records-split-brain-cont.ipd.md:6,68-70,102`, `.aw/system/workflows/plan-review/steps/p-proofread.md:19-28` | `Validation and cross-check` line 102 carried two em dashes triggering `2` `IPD-C802` info advisories, and `Scope` / `Child IPDs` cited bare module names instead of repository paths (`agent_workflows/...`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced the two em dashes on line 102 with commas and qualified module paths in `Scope` and `Child IPDs`. Recommendation strength: strong. |
