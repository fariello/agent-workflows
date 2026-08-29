- Id: l6rh0z
- Status: open
- Blocks-Release: next
- Set: lanebegin
- Priority: high
- Kind: bug
- Summary: begin's in-scope-dirty gate measures the MAIN tree for an isolated lane, so another agent's uncommitted edit to a commonly-scoped file (cli.py) withholds execution authority from an unrelated lane that would run clean at its frozen base

## Workflow history
- 2026-08-29 created (aw backlog): Filed from live evidence in run-20260829T184625Z-3940528: rchpms begin refused on agent_workflows/cli.py, dirty from a CONCURRENT session; the lane worktree would have been clean. Begin-end twin of 077yqc's ownership blindness

ROOT CAUSE: for an isolated lane the driver runs `aw ipd begin` against the MAIN repo (deliberately: the receipt must live under the main repo's `.aw/state/`), so `begin`'s in-scope-dirty gate measures the MAIN working tree. `check_begin` calls `dirty_within(str(repo_root), scope_paths, _scope_match)` and refuses when any path inside the plan's frozen `Scope-Paths` is dirty (ipd_lifecycle.py:702-722). But under `isolate_worktree` the turn will NOT execute in that tree: it runs in a freshly-created worktree at the frozen base commit, where those paths are by construction clean. So the gate refuses on the basis of a tree whose dirtiness cannot affect the lane's frozen base.

The comment directly above the check states the intent (ipd_lifecycle.py:700-701): "Disjoint uncommitted work elsewhere is intentionally ignored so a concurrent multi-agent workflow is not thrashed." That intent is correct and is exactly what breaks here: in a SHARED CHECKOUT another agent's in-flight edit to a common file (e.g. `agent_workflows/cli.py`) is not disjoint from a broad Scope-Paths list, so it thrashes the lane anyway.

OBSERVED (live, `aw oc run wtiso`, run-20260829T184625Z-3940528):
  events.jsonl 18:46:28  event=ipd-begin-refused  id6=rchpms
  console: "IPD 04/8 rchpms begin refused (no execution authority); not launching.
    error: refusing to begin: uncommitted changes to paths INSIDE this plan's Scope-Paths make the
    frozen base ambiguous: agent_workflows/cli.py."
`rchpms` declares `agent_workflows/cli.py` in Scope-Paths (plan line 7). At that moment a CONCURRENT session had uncommitted edits to `cli.py` in the main tree (confirmed: `git status --porcelain` showed `M agent_workflows/cli.py` alongside `run_cli.py`, `run_ledger_store.py`, `ipd_set_plan.py` and two new backlog files, none of them this lane's). The lane worktree that would have been created for `rchpms` would have been clean at its base.

WHY IT MATTERS: `cli.py` is in the Scope-Paths of many plans, and in a shared checkout it is almost always dirty for someone. The result is that ANY concurrent agent editing a commonly-scoped file silently withholds execution authority from unrelated lanes, and the run reports `begin refused (no execution authority)` with no path to proceed except asking an unrelated party to commit or stash. The operator's remedy is not even available to them: the dirty work is someone else's, and per the shared-checkout contract they must NOT commit or stash it.

DISTINCT FROM: 17gydk (orphaned lane branches / non-idempotent allocation, which produced the OTHER three failures in this same run), dh0uno (state roots resolved relative to the lane), and 077yqc (finalize scope attribution ignoring ownership). 077yqc is the closest relative: it is the same ownership-blindness defect at the FINALIZE end (`_paths_changed_by_this_execution` unions the whole porcelain with no ownership filter). This item is that blindness at the BEGIN end, and it fails CLOSED (refuses to start) rather than misattributing.

FIX SKETCH: the dirty gate must measure the tree the turn will actually execute in. For an isolated run, evaluate in-scope dirtiness against the LANE worktree (clean at the frozen base) while still writing the receipt to the main repo's state, i.e. separate "where state lives" from "which tree is the baseline". Equivalently, the driver can pass the intended execution tree to `begin`, and `begin` can skip the check when the baseline is a fresh worktree pinned to an explicit commit, since the frozen base is then unambiguous BY CONSTRUCTION and the check has nothing to protect. If a main-tree check is retained for the non-isolated path, it should be ownership-aware (see 077yqc) so another agent's files do not count.

REPRO: in a shared checkout, dirty any file that appears in a plan's Scope-Paths (e.g. `agent_workflows/cli.py`), then `aw oc run <set>` with isolation on for a plan declaring that path: begin refuses with "frozen base ambiguous" even though the lane worktree would be clean.

TEST: (a) with an in-scope path dirty in the MAIN tree, an isolated lane for a plan declaring that path still receives execution authority, and its worktree is verified clean at the frozen base; (b) the receipt still records the correct frozen base commit in that scenario; (c) the non-isolated path retains a dirty-tree refusal (no regression of the ambiguity protection where it genuinely applies).
