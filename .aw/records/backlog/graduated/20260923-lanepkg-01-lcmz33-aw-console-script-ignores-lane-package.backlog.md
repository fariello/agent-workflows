- Id: lcmz33
- Status: graduated
- Graduated-To: laneawpin
- Blocks-Release: next
- Set: lanepkg
- Priority: high
- Work-Kind: bug
- Summary: aw console script resolves the editable-install root, so a lane worktree silently validates the wrong code

## Workflow history
- 2026-09-25 graduated (aw set): graduated into laneawpin plan wj5b53 (to-review); plan also covers jeh310
- 2026-09-23 note (aw backlog): Related to cpun92, which covers the TEST-side half (subprocess CLI tests in a lane importing the main checkout). This item is the INTERACTIVE half: the aw console script itself, which cpun92 mentions as a measured aside without filing. Filed separately because the fixes differ: cpun92 pins PYTHONPATH in the test fixture, while this needs the runner or the CLI itself to notice the mismatch.
- 2026-09-23 created (aw backlog): aw console script resolves the editable-install root, so a lane worktree silently validates the wrong code

Measured 2026-09-23 while executing plan `bwgyum` in an isolated lane worktree.

WHAT HAPPENS. The `aw` console script on PATH is an EDITABLE install whose project location is the MAIN
checkout, so `aw <anything>` run from inside `.aw/worktrees/<lane>/` imports `agent_workflows` from the
main checkout, NOT from the lane. A bare `python3 -c "import agent_workflows"` in the lane resolves to the
lane copy (cwd precedence), so the two disagree about which code is under test.

WHY IT MATTERS, and it is not cosmetic. An agent validating its own change in a lane by running `aw check`
or `aw ipd lint` measures UNMODIFIED code and sees a clean or unchanged result. Measured concretely:
a newly added `aw check` rule reported ZERO findings via `aw check all` on a tree containing a deliberate
violation, and reported that violation correctly when the SAME sweep was invoked as
`python3 -c "from agent_workflows import cli; cli.main([...])"` from the lane root. An agent trusting the
first result would have recorded false evidence that a new rule fires, or that a fix works, when neither
was under test. The failure is SILENT and biased toward false confidence, which is the dangerous direction.

WORKAROUND USED. Invoke the CLI as a module from the lane root rather than through the console script, and
pin a genuine BEFORE by extracting HEAD with `git archive HEAD agent_workflows` into a scratch directory
and invoking from there.

POSSIBLE FIXES (not designed here). Have the runner point PATH/PYTHONPATH at the lane for the turn; or have
`aw` WARN when its resolved package root is not an ancestor of the cwd, which is the cheap detectable case
and would have turned this silent failure into one line of output.
