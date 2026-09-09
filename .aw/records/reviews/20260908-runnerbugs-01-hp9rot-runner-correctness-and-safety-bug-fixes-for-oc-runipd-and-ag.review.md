# Review: Runner correctness and safety bug fixes for oc_runipd and agy_runipd

- Subject-Id: hp9rot
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: Codex/GPT-5
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Structural preflight `aw ipd lint --phase author --agent` conformed before review. The current tree was re-measured rather than trusting the assessment findings. The plan remains an executable, bounded runner-correctness repair after removing two stale items and the conflicting broad success-state change.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | A. Correctness / ownership | `.aw/records/plans/pending/20260908-finalback-01-zzcrlo-send-a-refused-finalize-back-to-the-same-agent-with-the-gate.ipd.md:49-53,215` | E-02 removed `substantially-complete` from the global success set, but the owning `finalback` plan establishes that this would alter legitimate non-refusal behavior and requires discriminating on recorded finalize refusal instead. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Removed E-02, BUG-09, its validation row, and its resolved question. The reviewed plan does not claim `rwibaz` ownership. |
| PR-002 | MEDIUM | OVER-SCOPE | A. Correctness / evidence | `agent_workflows/runner_stop.py:888-904`; `tests/test_runner_stop_level3.py:556-582` | E-05 and BUG-03 asserted a live Agy schema mismatch, but the implementation and regression coverage already use and prove `type: step_update`; the claimed `event` shape is not the current contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed E-05, BUG-03, and V-05 rather than implementing a second unsupported event schema. |
| PR-003 | HIGH | UNDER-SCOPE | E. Testing / G. Executability | original `Scope-Paths`; required-test matrix naming `test_runner_backlog_close.py`, `test_runner_item_dependencies.py`, `test_runner_shared.py`, and `test_stall_progress.py` | The plan required focused tests outside its declared scope and lacked the required execution contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added every named test path, narrowed scope to active work, and added scope fence, isolated-worktree, staged-path, never-push, actual-output, and lifecycle requirements. |
| PR-004 | MEDIUM | UNDER-SCOPE | C. Concurrency | `agent_workflows/oc_runipd.py:5941-5958,6441-6467`; `agent_workflows/agy_runipd.py:3070-3075,3518-3544` | BUG-12 was assessed Low risk but deferred, contrary to the Fix Bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-13/V-13 through `aw ipd sync`; it requires one ordered timeout-termination owner in both runners. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should E-02 change the global success-state vocabulary or leave that concern to its owner? | Leave it to `finalback` and remove it here. | Keep the broad set mutation. Rejected because `finalback` demonstrates it changes refusal-free behavior and owns the narrower refusal discriminator. | `zzcrlo:49-53,215` | yes |
| D-2 | Should the Agy checkpoint parser accept both `event` and `type` shapes? | Preserve the established `type` contract and remove the unsupported change. | Add the extra shape. Rejected because current source and tests identify `type` as the real schema, so the claimed defect is stale. | `runner_stop.py:888-904`; `test_runner_stop_level3.py:556-582` | yes |

No `Reversible: no` decision was taken in this round.
