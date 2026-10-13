- Id: pex4pv
- Status: open
- Blocks-Release: next
- Set: pex4pv
- Priority: high
- Work-Kind: bug
- Summary: commit_spec_transition_output fails git add on renamed spec path

## Workflow history
- 2026-10-13 created (aw backlog): commit_spec_transition_output fails git add on renamed spec path

## Problem Description

When a spec transitions from `approved/` to `implementing/`, `specs set --no-commit` renames the spec file across directories using `git mv`.
In `agent_workflows/runner_shared.py:commit_spec_transition_output`, `status_paths` parses `git status --porcelain` and extracts all changed paths (both the deleted old path and the newly created path).
The function executed:
```python
rc, _out, _err = _run_git(wt, ["add", "--", *allowed])
```
Because the old path no longer exists on disk, `git add` fails with:
`fatal: pathspec '<old_path>' did not match any files` (rc 128).
This causes `commit_spec_transition_output` to abort and return `None, ()`, so the spec transition is never committed to the lane branch.

## Solution

Filter paths to only those that exist on disk before calling `git add`:
```python
add_paths = [p for p in allowed if (wt / p).exists()]
if add_paths:
    rc, _out, _err = _run_git(wt, ["add", "--", *add_paths])
    if rc != 0:
        return None, ()
```
This mirrors `commit_backlog_transition_output`.
