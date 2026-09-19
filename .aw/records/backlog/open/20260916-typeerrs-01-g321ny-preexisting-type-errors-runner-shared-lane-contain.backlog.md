- Id: g321ny
- Status: open
- Blocks-Release: next
- Set: typeerrs
- Priority: low
- Work-Kind: bug
- Summary: Two pre-existing type errors in runner_shared and lane_containment (unpacked git-runner tuple; reaper call arity)

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-16 created (aw backlog): Found while executing dirtygates Order 01 (d7qoxv); pre-existing at commit 4350ebc and NOT introduced by that plan.

TWO STATIC TYPE ERRORS PRESENT BEFORE ANY d7qoxv EDIT, verified by reading the same lines at the baseline commit 4350ebc.

1. `agent_workflows/runner_shared.py:1914` calls `status_out = _run_git(repo, ["status", "--porcelain"])` then `bool(status_out.strip())`. `_run_git` returns a `tuple[int, str, str]`, so `.strip()` is not an attribute of the value bound. Either the tuple is meant to be unpacked (`rc, out, _err = ...`) or a different helper was intended. RUNTIME IMPACT NOT ESTABLISHED: this is on a cleanup path that decides `holds_work`, and a non-empty tuple is always truthy, so the branch may be taking the wrong side silently rather than raising. Worth a real look, because `holds_work` gates whether a lane is cleaned up.

2. `agent_workflows/lane_containment.py:1208` calls `reaper(process, run_dir=run_dir)` and the checker reports one missing positional argument.

NEITHER WAS TOUCHED BY d7qoxv: that plan's diff in these files is confined to the clean-base rule (around `:2556-2700` in lane_containment) and the run-start report plus the launch decision (around `:3040-3300` in runner_shared). Reported rather than fixed because both are outside that plan's declared scope and item 1 needs a behavioral decision about which side of the branch is correct.
