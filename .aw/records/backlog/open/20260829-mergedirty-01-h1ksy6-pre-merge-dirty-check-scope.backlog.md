- Id: h1ksy6
- Status: open
- Blocks-Release: next
- Set: mergedirty
- Priority: high
- Work-Kind: bug
- Summary: driver pre-merge dirty check scopes to the lane's changed files, so a non-ff merge touching other paths reports a confusing merge-conflict instead of integration-blocked

## Workflow history
- 2026-09-02 open (aw set): Gate retargeted: owner 2c122z was retired to superseded/ in 70b5338a (wtiso Set retirement), so the artifact gate pointed at a plan that will never land. The defect is still real and now UNOWNED: dirty_tree_overlap remains in main in two copies (oc_runipd.py:1923, agy_runipd.py:1156) and lanectn did not inherit this fix. Reopening so it is actionable rather than blocked forever.
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

WHY THIS WAS BLOCKED, AND WHY IT IS NOW OPEN (updated 2026-09-02). It was gated
`Gate-Kind: artifact` / `Gate-Ref: 2c122z` because `wtiso` Phase 5 owned this code path, so the fix
belonged there rather than in a second merge-safety mechanism (GUIDING_PRINCIPLES P8).

THAT OWNER NO LONGER EXISTS. `70b5338a` retired the entire `wtiso` Set to `superseded/`, `2c122z`
included, after all three failures it targeted were closed on `main` by cheaper routes. The gate
therefore pointed at a plan that will never land, which would have left this item blocked forever.
Reopened, and the gate fields cleared, so it is actionable again.

THE DEFECT IS STILL REAL AND NOW UNOWNED, verified 2026-09-02:
  - `dirty_tree_overlap` is still in `main`, in TWO copies: `agent_workflows/oc_runipd.py:1923` and
    `agent_workflows/agy_runipd.py:1156`. The duplication matters: fixing one leaves the other driver
    with the worse diagnostic, the same drift `plan_readiness.py` was created to end for the
    readiness predicate.
  - `lanectn` (the Set that PORTED wtiso's containment design) did NOT inherit this fix; grepped its
    seven plans for `dirty_tree_overlap` / `integration-blocked` and found no mention.
So P8 still applies, but it now means "one shared implementation across both drivers", not "wait for
2c122z".

ALSO RESOLVED BY THE RETIREMENT: the KNOWN ASYMMETRY recorded below is moot. It asked for
`- Blocks-Release: next` to be added to `2c122z` once a live run finished, so the gate would be
symmetric. `2c122z` is now superseded and unexecutable, so there is nothing to make symmetric; this
item keeps its own `Blocks-Release: next` and is the sole carrier.

KNOWN ASYMMETRY (recorded deliberately, 2026-08-29): this item carries `Blocks-Release: next` but
`2c122z` does NOT, so nothing currently stops 2.0.0 shipping before the owning plan lands. The
maintainer asked for the gate on both; `2c122z` was NOT edited because it is `queued` for execution in
a LIVE run (`run-20260829T153858Z-3207626`, pid 3207626 confirmed live), and editing a plan mid-flight
would both mutate another session's work and risk the begin-receipt content-digest staleness defect
(`xmqv5l`). ACTION NEEDED: once that run finishes, add `- Blocks-Release: next` to `2c122z` via
`aw ipd set <status> 2c122z --blocks-release next` so the gate is symmetric.
