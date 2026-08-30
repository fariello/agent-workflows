- Id: h1ksy6
- Status: blocked
- Blocks-Release: next
- Set: mergedirty
- Priority: high
- Work-Kind: bug
- Summary: driver pre-merge dirty check scopes to the lane's changed files, so a non-ff merge touching other paths reports a confusing merge-conflict instead of integration-blocked
- Gate-Kind: artifact
- Gate-Ref: 2c122z

## Workflow history
- 2026-08-29 created (aw backlog): driver pre-merge dirty check scopes to the lane's changed files, so a non-ff merge touching other paths reports a confusing merge-conflict instead of integration-blocked

THE BUG. `oc_runipd.dirty_tree_overlap(repo, changed_files)` (oc_runipd.py:516-545) is called at
:578 with `lane.changed_files`, so it only checks main's dirty paths against files THE LANE changed.
A non-fast-forward merge can also write files the lane never touched (commits that landed on main
since the lane base). Those are outside the check, so the guard can report "clear" and the merge then
fails anyway.

WHAT ACTUALLY BREAKS: only the error message. Verified experimentally that git fails closed on its own
in every dangerous case, so nothing is lost or overwritten:

```
main dirty on a path the lane also changed:
  error: Your local changes to the following files would be overwritten by merge: a.txt
  -> merge refused, dirty content preserved verbatim

co-worker's STAGED index on a non-overlapping path:
  error: Your local changes to the following files would be overwritten by merge: b.txt
  Merge with strategy ort failed.  rc=2
  -> no merge commit created, nothing swept

main dirty on a genuinely non-overlapping path:
  -> merge succeeds and the dirty edit is untouched (correct: git only writes paths in the diff)
```

Also verified the driver never does anything destructive on failure: the only recovery in that path is
`git merge --abort` (oc_runipd.py:~627), with no `reset`, `checkout -f`, `stash`, or `clean` anywhere.

So the defect is COSMETIC/DIAGNOSTIC: the operator gets the lower-quality `merge-conflict` disposition
and git's raw stderr instead of the accurate, actionable `integration-blocked` ("main tree has un-owned
dirty paths overlapping the incoming change: <paths>"). It is NOT a data-safety bug. Do not describe it
as one.

FIX: compute the dirty check against the full set of paths the merge would touch (e.g. the diff between
the merge base and both tips), not just `lane.changed_files`.

WHY BLOCKED, NOT OPEN: the owning implementation is `wtiso` Phase 5 (`2c122z`, "real candidate-merge
integration + integration lock + expected-tip recheck"), which already owns this code path. Gate is
`Gate-Kind: artifact` / `Gate-Ref: 2c122z`, so the dependency is machine-readable and one-way (this
item -> that plan). Fix it THERE rather than patching `dirty_tree_overlap` separately, to avoid two
merge-safety mechanisms (GUIDING_PRINCIPLES P8).

KNOWN ASYMMETRY (recorded deliberately, 2026-08-29): this item carries `Blocks-Release: next` but
`2c122z` does NOT, so nothing currently stops 2.0.0 shipping before the owning plan lands. The
maintainer asked for the gate on both; `2c122z` was NOT edited because it is `queued` for execution in
a LIVE run (`run-20260829T153858Z-3207626`, pid 3207626 confirmed live), and editing a plan mid-flight
would both mutate another session's work and risk the begin-receipt content-digest staleness defect
(`xmqv5l`). ACTION NEEDED: once that run finishes, add `- Blocks-Release: next` to `2c122z` via
`aw ipd set <status> 2c122z --blocks-release next` so the gate is symmetric.
