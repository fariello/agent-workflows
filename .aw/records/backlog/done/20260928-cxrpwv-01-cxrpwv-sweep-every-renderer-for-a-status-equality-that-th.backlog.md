- Id: cxrpwv
- Status: done
- Graduated-To: cxrpwv
- Set: cxrpwv
- Priority: medium
- Work-Kind: followup
- Summary: Sweep every renderer for a status equality that the statusvocab rename left dead, the class that silenced render_stream's dependency diagnostics arm

## Workflow history
- 2026-10-01 set (aw backlog): closed by aw oc run: IPD qvfd4l executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-cxrpwv-01-qvfd4l-sweep-the-status-token-readers-for-a-dead-comparison-the-sta.ipd.md); evidence .aw/records/plans/executed/20260930-cxrpwv-01-qvfd4l-sweep-the-status-token-readers-for-a-dead-comparison-the-sta.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: qvfd4l
- 2026-09-28 created (aw backlog): Sweep every renderer for a status equality that the statusvocab rename left dead, the class that silenced render_stream's dependency diagnostics arm

MEASURED 2026-09-28 while authoring plan `5o1jye` from backlog item `fvsyqk`. Commit `6b94a4d9` (statusvocab `cyamvi`, 2026-09-25) renamed the terminal status vocabulary so the runner writes `fail-depend` where it once wrote `dependency-blocked`, and `TERMINAL_STATUS_ALIASES` keeps the legacy token readable. That commit widened THREE status tuples in `render_stream.py` but left at least two bare EQUALITY comparisons against the retired token behind: `render_stream.render_run_summary_table`s diagnostics arm (`elif st == "dependency-blocked"`) and `runner_shared.write_report`s `## Dependency blocks (why)` gate (`item.get("status") == "dependency-blocked"`). Both are consequently DEAD in a live run: rendering a real queue whose items carry the canonical `fail-depend` produced NO diagnostic lines and NO report section at all, while the same queue under the legacy token rendered both. Plan `5o1jye` fixes exactly those two sites because they are the ones its own defect reaches.

THE RESIDUAL WORK IS THE CLASS, NOT THE INSTANCE. Nobody has swept the codebase for other renderers, viewers, or gates that compare a status by equality (or by a hardcoded tuple) against a token the runner no longer writes. The failure mode is silent by construction: the surface renders nothing, no exception is raised, and the suite stays green, which is how these two survived. A sweep should enumerate every comparison against each key of `TERMINAL_STATUS_ALIASES` across `agent_workflows/`, decide per site whether it should accept both spellings (the correct answer wherever the site READS frozen run directories, per spec `25kzda`s 2026-09-25 amendment that legacy tokens remain readable forever) or route through `canonical_terminal_status`, and pin the canonical spelling behaviorally so the next rename fails a test instead of silencing a surface.

Filed `followup` rather than `bug` because no specific user-perceptible defect is measured here beyond the two instances `5o1jye` already fixes; this item carries the unaudited remainder. Should the sweep measure a further dead surface an operator reads, that instance should be filed `bug` on its own measurement.
