- Id: 61qk4a
- Status: done
- Set: awrenamebug
- Priority: high
- Kind: bug
- Summary: aw backlog set --blocks-release does not persist the Blocks-Release field on a no-op (same-status) transition
- Blocks-Release: next

## Workflow history
- 2026-08-25 done (aw set): Verified fixed: --blocks-release now persists on a no-op (same-status) transition; write hoisted out of the status branch (status_set.py:449-461). Executed IPD efnn74; regression test_backlog_positional_status_persists_blocks_release_61qk4a.
- 2026-08-24 renumber+blocks-release-set (opencode its_direct/pt3-claude-opus-4.8-1m-us): renamed awrenamebug-01 -> awrenamebug-02 via `aw rename backlog --order 02` to resolve the NN collision with dcla4g (both were `awrenamebug-01-`, differing only by id6). Added `Blocks-Release: next` (gates 2.0.0 / f33nrj) by HAND-EDIT - justified exception: this bug (the no-op non-persist) is precisely why `aw backlog set --blocks-release` cannot set it; a tool that is broken cannot set its own release-gate. Re-verify/re-set via the tool once this bug is fixed.
- 2026-08-23 created (aw backlog): aw backlog set --blocks-release does not persist the Blocks-Release field on a no-op (same-status) transition

BUG: 'aw backlog set open <id6> --blocks-release next --yes' on an item ALREADY in 'open' reports outcome:clean/complete:true but never writes the '- Blocks-Release:' line. Observed 2026-08-23 trying to gate the 2.0.0 release (f33nrj) on the rename-slug-mangle bug (item dcla4g): repeated invocations (human + --agent, with --yes, with 'next' and explicit 'f33nrj') all succeeded yet the field stayed absent. ROOT CAUSE (likely): the Blocks-Release write lives inside apply_status_change's status-change branch (status_set.py:447-453), which is skipped when the target status equals the current status (a no-op transition), so --blocks-release is silently dropped unless the status actually changes. IMPACT: release-gating (AGENTS.md 'Blocks-Release' convention) silently fails for any item already at the target status - a caller believes they gated a release when they did not. FIX: apply --blocks-release/--clear regardless of whether the status value changes (make the field mutation independent of the status-transition branch), and add a regression test: 'backlog set <same-status> <id> --blocks-release next' persists the field. RELATED: filed while attaching the release-blocker to dcla4g (rename --order slug-mangle); dcla4g SHOULD block release f33nrj/2.0.0 but the field could not be set via the tool because of THIS bug.
