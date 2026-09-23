- Id: uin96r
- Status: graduated
- Graduated-To: lanecli
- Blocks-Release: next
- Set: uin96r
- Priority: high
- Work-Kind: bug
- Summary: The aw console script resolves agent_workflows from the main checkout, so a lane worktree's edits are invisible to CLI evidence

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to IPD lhjsu0 (lanecli Order 01). These three items are ONE defect with three victims (CLI, agent, suite), so one plan carries all three. VERIFIED LIVE at HEAD 22cf67d9 rather than trusting the filings: from a lane worktree with a NEUTRAL cwd, 'import agent_workflows' resolves to the MAIN checkout's __init__.py, because the editable install pins an absolute path there and the aw console script runs under a fixed interpreter shebang. THE MEASUREMENT THAT EXPLAINS WHY THIS SURVIVED: from the lane ROOT the cwd precedes the editable path, so the lane's own package wins and everything looks correct; only a neutral cwd or a subprocess flips it to main. Any fix or guard tested only from the lane root cannot distinguish fixed from broken, which the plan makes a hard requirement (E-04 must run from a NON-root cwd). ALSO MEASURED, and stronger than the filings claim: importing from a lane SUBDIRECTORY loaded MAIN's __init__.py while the LANE's agent_workflows/selectors.py shadowed the stdlib selectors module, crashing inside subprocess with AttributeError: module 'selectors' has no attribute 'SelectSelector'. That is two trees' code executing in one interpreter, not merely the wrong tree winning.
- 2026-09-22 created (aw backlog): The aw console script resolves agent_workflows from the main checkout, so a lane worktree's edits are invisible to CLI evidence

FOUND WHILE EXECUTING `d91i3e` (runrecon Order 01). Filed as `bug` because it is a correctness
trap that silently produces FALSE EVIDENCE, and as a release blocker per the live-bug policy.

WHAT IS WRONG. Inside an isolated lane worktree the `aw` console script imports
`agent_workflows` from the MAIN CHECKOUT, not from the worktree it is invoked in. Measured at HEAD
23dfbf2d from a lane worktree:

    $ python3 -c "import agent_workflows; print(agent_workflows.__file__)"
    <lane-worktree>/agent_workflows/__init__.py          # correct

    $ <venv>/bin/python3 -c "import sys; print(sys.path[:3])"
    ['', '<main-checkout>', '<other>', ...]              # the MAIN checkout is on sys.path

So `python3 -m agent_workflows <args>` and an in-process `cli.main([...])` both exercise the lane's
code, while bare `aw <args>` exercises the MAIN checkout's code. The mechanism is an installed
path entry pointing at the main checkout (an editable/`.pth`-style install), which wins over the
worktree because the console script's `sys.path[0]` is the script directory rather than the cwd.

WHY THIS IS A BUG AND NOT A LOCAL MISCONFIGURATION. Every plan in this repository asks an executor
to paste CLI output as validation evidence, and the runner executes plans in isolated lane
worktrees BY DEFAULT. The composition of those two facts means the default way to gather evidence
in the default execution environment reads the WRONG CODE, and it does so SILENTLY: the command
succeeds, prints plausible output, and simply reflects a different tree. During `d91i3e` this
produced a concrete false negative - a freshly implemented change appeared to have had NO EFFECT
across ten CLI leaves, and the first plausible explanation (a stale bytecode cache) was wrong. Only
comparing `aw` against `python3 -m agent_workflows` revealed it.

THE FAILURE MODE RUNS IN BOTH DIRECTIONS, which is what makes it worth a release gate:
  * FALSE NEGATIVE, as measured: the lane's own change looks absent, and an executor may "fix" a
    working implementation or report the work as incomplete.
  * FALSE POSITIVE, the dangerous one: a lane can paste evidence that a behaviour WORKS when that
    behaviour exists only in the main checkout and not in the lane's own diff. Nothing in the
    evidence text distinguishes the two, so a reviewer cannot catch it downstream.

WORKAROUND USED IN `d91i3e` (so this is not a blocker for that plan): prefix every evidence command
with `PYTHONPATH=$(pwd)`, or call `python3 -m agent_workflows` / in-process `cli.main` instead of
the console script. Tests are unaffected: pytest runs with the worktree on `sys.path`, so the suite
always exercised the lane's code.

SUGGESTED FIX, not prescribed. Options: (a) have the runner export `PYTHONPATH=<lane worktree>`
(or a `VIRTUAL_ENV`-equivalent shim) into every lane turn's environment, which fixes it for all
plans at once and needs no change to how anyone writes evidence; (b) have `aw` detect that its cwd
is inside a DIFFERENT checkout than the package it imported and warn loudly on stderr, which is
cheap and catches the case even outside the runner; (c) document it in the execution contract so
executors reach for `python3 -m` in a lane. (a) plus (b) is the durable pair, since (b) is what
makes a future regression visible instead of silent.

NOTE ON SCOPE. This is about the ENVIRONMENT a lane turn runs in, not about `d91i3e`'s subject
matter (a refusal message in `run_cli.py`). It is filed separately for that reason.
