- Id: tsfk8a
- Status: open
- Set: tsfk8a
- Priority: medium
- Work-Kind: bug
- Summary: reconcile_item_on_interrupt treats the _run_git 3-tuple as a string, so a non-isolated interrupted turn is always scored as holding no work

## Workflow history
- 2026-09-14 created (aw backlog): reconcile_item_on_interrupt treats the _run_git 3-tuple as a string, so a non-isolated interrupted turn is always scored as holding no work

MEASURED at HEAD 4234153f, and PRE-EXISTING (not introduced by defreport b7xarm, which merely surfaced it via a type checker while working in the same file).

WHERE: agent_workflows/runner_shared.py, in reconcile_item_on_interrupt (the non-isolated branch that decides whether an interrupted turn produced any work):

    status_out = _run_git(repo, ["status", "--porcelain"])
    holds_work = bool(status_out.strip())

WHAT IS WRONG: _run_git returns a 3-TUPLE (returncode, stdout, stderr), not a string (see its own signature and docstring one screen above). A tuple has no .strip(), so this line raises AttributeError whenever it is reached.

WHY IT MATTERS: this is the predicate that decides whether an interrupted, NON-isolated turn's work is preserved or its lane cleaned up as empty. The nearby isolated branch reads lane['holds_work'] instead, so the isolated path (the DEFAULT, since isolate_worktree defaults true) never reaches this line, which is why it has gone unnoticed.

SUSPECTED FIX: unpack the tuple, i.e. _rc, status_out, _err = _run_git(...), then bool(status_out.strip()). Adjacent code in the same module already uses the shared git_status wrapper for exactly this, which may be the better call.

NOT FIXED HERE because runner_shared.py is in b7xarm's Scope-Paths only for the defect-report schema/validator, and changing interrupt reconciliation is unrelated behavior that deserves its own test (there appears to be no test covering the non-isolated interrupt branch, which is the reason the defect survived).
