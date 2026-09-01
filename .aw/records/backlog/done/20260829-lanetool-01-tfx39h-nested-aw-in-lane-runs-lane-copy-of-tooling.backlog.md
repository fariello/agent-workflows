- Id: tfx39h
- Status: done
- Blocks-Release: next
- Set: lanetool
- Priority: high
- Work-Kind: bug
- Summary: Nested aw invoked inside a lane worktree executes the LANE BRANCH's copy of agent_workflows, so lifecycle fixes are void in lanes and unreviewed lane tool code runs the driver's own transitions

## Workflow history
- 2026-09-01 done (aw set): Design shipped: plan af7i6p is executed (From-Backlog: tfx39h). Verified on main: oc_runipd carries 19 pinned_module_argv/pinned_child_env references, so a nested aw in a lane runs the RUNNER's tooling, not the lane copy.
- 2026-08-30 graduated (aw set): design handed off to plan af7i6p (lanetruth-01, approved, carries From-Backlog: tfx39h and Blocks-Release: next); gate preserved via handoff, code not yet written so NOT done
- 2026-08-29 open (aw set): status set to open
- 2026-08-29 created (aw backlog): Filed from run-20260829T153858Z-3207626: the 18:06:42Z finalize scope prompt was NOT a g40w37 regression (6332a04 landed 17:55:25Z); the lane ran a pre-fix copy of the tool. Measured in .aw/worktrees/8zgybk: -m resolves to the lane package, version g5e78e33, AW_NONINTERACTIVE guard absent

ROOT CAUSE (tool-integrity hole, verified): under `isolate_worktree` the driver runs nested `aw` with `cwd` set to the LANE WORKTREE, invoked as `[sys.executable, "-m", "agent_workflows", ...]`. Python puts the cwd first on `sys.path` for `-m`, so `agent_workflows` resolves to the LANE BRANCH's checked-out copy of the package, NOT the installed/main-tree one the driver itself is running. `oc_runipd.driver_finalize` (oc_runipd.py:425-446) builds that argv and passes `cwd=str(repo)`, and the caller hands it `finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo` (oc_runipd.py:2198, called at :2212-2214). Same shape at the other nested-`aw` call sites (oc_runipd.py:248, :317, :356; agy_runipd.py:421, :481, :548).

MEASURED (in .aw/worktrees/8zgybk, lane base 5e78e33):
  $ python3 -c "import sys,importlib.util; print(repr(sys.path[0])); print(importlib.util.find_spec('agent_workflows').origin)"
  sys.path[0]= ''
  resolved  = <repo-root>/.aw/worktrees/8zgybk/agent_workflows/__init__.py   <- the LANE's copy
  $ python3 -m agent_workflows --version
  agent-workflows 1.3.0rc2.dev1429+g5e78e33                                  <- the LANE's version
  $ grep -c AW_NONINTERACTIVE agent_workflows/ipd_lifecycle.py
  0                                                                          <- the g40w37 fix is ABSENT
Main tree by contrast resolves `agent_workflows` to the checkout it is running and DOES contain the guard.

HOW IT SURFACED (and a correction to the record): run-20260829T153858Z-3207626 recorded
  events.jsonl 18:06:42  event=ipd-finalize-refused id6=8zgybk exit_code=-15
  detail="These paths were DECLARED in Scope-Paths but NOT modified. Acknowledge each ..."
i.e. an interactive `input()` scope prompt from a driver-spawned finalize. That was initially read as the g40w37 TTY-wedge fix having failed. It had not: commit 6332a04 landed 2026-08-29T17:55:25Z, 11 minutes BEFORE the 18:06:42Z refusal, and main contains both the callee guard (`ipd_lifecycle.py:1954-1970`, interactivity now also requires stdout to be a TTY plus honours AW_NONINTERACTIVE/CI) and the caller's `stdin=subprocess.DEVNULL`. The fix was BYPASSED because the lane executed a pre-fix copy of the tool. `exit_code=-15` is the SIGTERM the driver delivered, consistent with the prompt blocking until it was killed rather than with the fix's sub-second refusal.

WHY IT MATTERS (this is the general bug, not a finalize bug): every nested `aw` the driver runs inside a lane silently runs the LANE BRANCH's version of the lifecycle tooling against the real repository. Consequences:
  1. Any fix to `ipd_lifecycle`/finalize/begin is VOID in lanes until every lane rebases onto it, so a fix can be verified green in main and still not apply where it matters.
  2. Behaviour becomes a function of the lane's base commit, so two lanes in one run can enforce different lifecycle rules, and older-based lanes silently enforce older gates.
  3. Worse, a lane whose plan legitimately EDITS `agent_workflows/` (routine here) has the driver execute that lane's UNREVIEWED, in-progress tool code to perform the very transition that is supposed to gate it, i.e. the control plane is supplied by the thing it controls. A broken mid-edit lifecycle module would take the driver's own state transitions with it.
This also explains why the g40w37 validation could pass end-to-end and yet the wedge shape still appear in a real run.

RELATION: a fourth facet of the driver-owned-control-plane problem alongside dh0uno (state roots resolved relative to the lane), xmqv5l (frozen begin digest), and qyaime (external_directory deadlock). dh0uno is about which STATE FILES an inner `aw` reaches; this item is about which CODE an inner `aw` IS. Both point at research x03wgn's conclusion that control-plane identity must not be derived from cwd.

FIX SKETCH: the driver must pin the tool it invokes to ITSELF, not to the tree it is operating on. Options, roughly in order of preference: (a) invoke nested `aw` with the driver's own package location forced ahead of cwd (e.g. run with `cwd` = main repo and pass `--dir <worktree>` where the verb already supports it, which is the existing dh0uno-shaped answer); (b) launch with `-P`/`PYTHONSAFEPATH` or an explicit `PYTHONPATH`/`-c` bootstrap so cwd is never prepended to `sys.path`; (c) resolve the module file from the running driver (`agent_workflows.__file__`) and execute that path explicitly. Add a startup assertion that a nested `aw`'s reported version/module path equals the driver's, and fail closed on mismatch, so this cannot regress silently.

REPRO: with `isolate_worktree` on, allocate a lane whose base predates a change to `agent_workflows/`, then have the driver run any nested `aw` in that lane: `python3 -m agent_workflows --version` inside the worktree reports the LANE's version, and the pre-change behaviour executes.

TEST: (a) a nested `aw` invoked by the driver for a lane reports the DRIVER's module path and version, not the lane's, even when the lane's checked-out `agent_workflows/` differs; (b) a lane based before a lifecycle fix still gets the fixed behaviour (regression-pin the g40w37 case: a driver-spawned finalize in such a lane refuses non-interactively in under a second instead of prompting); (c) a mismatch between driver and nested tool identity is detected and fails closed rather than proceeding.
