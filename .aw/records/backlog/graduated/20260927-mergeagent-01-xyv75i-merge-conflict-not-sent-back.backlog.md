- Id: xyv75i
- Status: graduated
- Graduated-To: mergeagent
- Blocks-Release: next
- Set: mergeagent
- Priority: high
- Work-Kind: bug
- Summary: A merge-back conflict fails the item (fail-merge, terminal) instead of sending it back to the agent to resolve in its lane

## Workflow history
- 2026-09-27 graduated (aw set): Graduated 2026-09-27 into to-review plan ounhsn (Set mergeagent).
- 2026-09-27 created (aw backlog): A merge-back conflict fails the item (fail-merge, terminal) instead of sending it back to the agent to resolve in its lane

Measured 2026-09-27: run-20260927T051110Z-3282017 item k4vi7z (finalized on its lane) was fail-merge on an additive-only CHANGELOG.md conflict, and btth0a's lane conflicted with sbo3hl in upgrade_rehearsal.py and its test file; both were keep-both resolutions a human did by hand. runner_shared.integrate_lane_branch aborts on any real conflict and returns fail-merge ('Nothing is RETRIED'); TURN_RETRY_CLASSIFICATION marks fail-merge not retryable; no path hands the conflict to the agent. Maintainer ruling 2026-09-27: on a merge conflict it must go back to the agent to fix.
