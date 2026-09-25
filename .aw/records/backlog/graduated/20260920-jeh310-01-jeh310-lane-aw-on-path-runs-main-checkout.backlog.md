- Id: jeh310
- Status: graduated
- Graduated-To: laneawpin
- Blocks-Release: next
- Set: jeh310
- Priority: high
- Work-Kind: bug
- Summary: A lane agent's `aw` on PATH resolves the MAIN CHECKOUT's package, so an in-lane code change is invisible to every `aw <verb>` demo an executor runs as evidence

## Workflow history
- 2026-09-25 graduated (aw set): duplicate of lcmz33; folded into laneawpin plan wj5b53
- 2026-09-20 created (aw backlog): Found while executing plan 9iiqmm in lane worktree 9iiqmm: `aw attention` rendered the pre-change board while `python3 -m agent_workflows attention` rendered the new footer line, because the console script's shebang venv has agent-workflows installed editable against the MAIN checkout.

MEASURED in lane worktree `9iiqmm` at base bb714fd8 while executing plan 9iiqmm:

    $ cat /tmp/whichmod.py   # import agent_workflows.attention; print __file__ and hasattr(...,'inbox_waiting')
    $ <venv>/bin/python3 /tmp/whichmod.py
    <main-checkout>/agent_workflows/attention.py
    False
    $ python3 -m agent_workflows -c 'same probe'
    <lane-worktree>/agent_workflows/attention.py
    True

So the two invocations run DIFFERENT code. `aw` is a console script whose shebang pins an interpreter whose site-packages carries an EDITABLE install pointing at the main checkout, and that path does not depend on cwd. `python3 -m agent_workflows` from the lane resolves the lane copy because `-m` puts cwd first on sys.path.

WHY THIS IS A BUG AND NOT A CURIOSITY. Plans in this repository routinely demand pasted `aw <verb>` output as validation evidence (plan 9iiqmm's V-02/V-03/V-05 each say 'paste the rendered board' / 'paste exit codes'). Run inside a lane, those commands exercise the MAIN checkout, so:
  1. An executor can paste output that looks like a clean PASS for a feature its lane has not yet delivered, or, as happened here, a clean FAIL for a feature it HAS delivered. I hit the second and nearly recorded the feature as not working.
  2. Worse in the other direction: the evidence can silently attest to behavior from another party's uncommitted main-checkout state, which is exactly the cross-contamination lane isolation exists to prevent.

RELATION, and why this is NOT tfx39h (done). `tfx39h` is about the DRIVER's nested `aw` resolving the LANE's copy (cwd-first for `-m`) and was fixed by pinning the driver's own module. This is the MIRROR CASE one layer out: the AGENT's `aw` on PATH resolving the MAIN copy regardless of cwd. Both are 'control-plane identity derived from the wrong tree', and the fix for one does not touch the other. `dh0uno` is about which STATE FILES an inner `aw` reaches, not which CODE it is.

FIX SKETCH: (a) cheapest and portable: state in the lane prompt and in AGENTS.md that in-lane verb evidence must be gathered with `python3 -m agent_workflows <verb>` (or an explicitly lane-pinned entry point), never the ambient `aw`; (b) have the lane prompt export a `PATH` (or an `AW` variable) whose `aw` is pinned to the lane; (c) have `aw` itself warn when its resolved package root is not an ancestor-or-equal of the git toplevel of cwd, which catches every future instance including a human's.

TEST: from a lane worktree holding a one-line change to a rendered string, assert that the evidence-gathering path reports the LANE's text; and assert the mismatch warning fires when the resolved package root and the cwd repo root differ.
