- Id: t5ycse
- Status: open
- Set: trailerdoc
- Priority: low
- Work-Kind: chore
- Summary: work_cmd._trailers_from_args cites a runbook directive that y9vpvv removed: agent commits are no longer instructed to use raw git commit

## Workflow history
- 2026-09-23 created (aw backlog): Found by commitguard-03 (2s0iym) E-02 while judging Order 02's shipped prose surface.

agent_workflows/work_cmd.py:422-423 (in `_trailers_from_args`) states that an agent's own code commits "are made by the agent running raw `git commit -m msg -- <path>` per the runbook directive, pass through no `offer_commit` call, and so cannot be reached by wiring one".

THE PREMISE IS STALE. Plan y9vpvv (commitguard Order 02, executed, commit 12ecd491) E-09 replaced the raw-`git commit` instruction at all four driver-prompt sites with the tooled form. Measured at 22cf67d9: `grep -rc 'git commit -m msg' agent_workflows/{oc_runipd,agy_runipd,runner_shared,engine}.py` returns 0 for every file, while the four sites now read `aw commit <plan> -- <paths>` (oc_runipd.py:2178, agy_runipd.py:2118, runner_shared.py:22223, runner_shared.py:22316).

WHY IT MATTERS AND WHY IT IS SMALL. The deferred attribution gap the comment documents is still genuinely open (agent commits are still not trailered, because an agent choosing the tooled path still passes no run/item ids), so the CONCLUSION stands. What is false is the stated CAUSE: the runner no longer instructs raw `git commit`, so a reader reasoning about how to close the gap is pointed at a directive that no longer exists. The fix is to re-word the paragraph to say the runner now instructs `aw commit` but supplies no trailer ids, which is a docstring edit with no behavior change.

NOT A commitguard SET HONESTY VIOLATION. It describes no bypassable guard as an authority boundary (it is an under-claim about tooling reach), so it was reported rather than corrected by 2s0iym, whose Scope-Paths deliberately excludes work_cmd.py.
