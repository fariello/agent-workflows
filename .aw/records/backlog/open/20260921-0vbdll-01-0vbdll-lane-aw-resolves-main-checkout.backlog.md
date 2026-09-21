- Id: 0vbdll
- Status: open
- Blocks-Release: next
- Set: 0vbdll
- Priority: high
- Work-Kind: bug
- Summary: A lane worktree's own code is invisible to the installed 'aw', so an agent measures the main checkout and reports the wrong result

## Workflow history
- 2026-09-21 created (aw backlog): Filed by the i1hlgx execution turn, which hit it live.

MEASURED 2026-09-21 in lane worktree for plan i1hlgx.

WHAT IS WRONG. The installed `aw` console script resolves `agent_workflows` from the MAIN checkout even when invoked with a lane worktree as the working directory, because a console script's `sys.path` carries no CWD entry. So an agent executing a plan inside an isolated lane, following its plan's instruction to run `aw <verb>` and paste the output, silently measures code it did NOT change.

WHY IT IS A BUG AND NOT A CHORE, by the AGENTS.md user-perceptible test. This does not merely waste work: it produces FALSE EVIDENCE that a human then trusts. In this turn, after correctly editing the lane's `run_cli.py`, every `aw runs ...` invocation kept printing the OLD message. The natural readings are all wrong ('my edit did not take', 'a stale bytecode cache', 'the code path differs'), and each costs a debugging cycle; the failure mode a plan-executing agent is being STEERED toward is worse, namely concluding the change does not work and either reverting it or pasting a 'still broken' observation into a plan's validation evidence. An E/V checkpoint whose pasted evidence came from the wrong tree is indistinguishable from real evidence.

REPRODUCTION. In a lane worktree, edit any packaged module's user-visible output, then run the corresponding `aw` verb: the OLD behavior prints. Confirm the cause by emulating the console script's path:

    python3 -c "import sys,os;sys.path=[p for p in sys.path if p not in ('', os.getcwd())];import agent_workflows;print(agent_workflows.__file__)"

It prints the MAIN checkout's `__init__.py`, not the lane's.

THE WORKAROUND this turn used for every measurement:

    python3 -c "import sys;sys.path.insert(0,'<lane>');from agent_workflows.cli import main;sys.exit(main(sys.argv[1:]))" <argv>

WHERE. The lane/worktree launch path (`oc_runipd.py` / `agy_runipd.py` `isolate_worktree`) versus the `aw` console-script entry point.

POSSIBLE FIXES, not chosen here. Have the runner export a `PYTHONPATH` pinned to the lane for the turn's environment; or ship a lane-local `aw` shim on `PATH` that prepends the lane; or have the CLI warn loudly when its own package directory is not under the CWD's repository root. The third is attractive because it converts a silent wrong answer into a visible one even outside a managed lane.

SCOPE NOTE. Any turn that pastes `aw` output as E/V evidence from a lane is affected, so the blast radius is every isolated-lane execution, not just this plan.
