- Id: cpun92
- Status: open
- Set: setidlen
- Priority: low
- Work-Kind: chore
- Summary: a subprocess CLI test in a lane imports the main checkout unless it pins PYTHONPATH, and only one test file does

## Workflow history
- 2026-09-23 note (aw backlog): Related to lcmz33 (filed 2026-09-23 while executing bwgyum): the INTERACTIVE half of this same root cause. The aw console script resolves the editable-install root, so aw check / aw ipd lint run by an agent inside a lane measure the main checkout. Measured there: a new check rule reported zero findings on a tree containing a deliberate violation via the console script, and fired correctly when invoked as a module.
- 2026-09-23 created (aw backlog): a subprocess CLI test in a lane imports the main checkout unless it pins PYTHONPATH, and only one test file does

## What is wrong

The repository is installed EDITABLE, so the `.pth` names an ABSOLUTE path to the main checkout. A
test that shells out with `[sys.executable, "-m", "agent_workflows", ...]` from a lane worktree
therefore imports the MAIN checkout's modules, and every CLI-level assertion in it measures code the
change under test never touched.

`tests/test_awnaming_grammar_and_producers.py` already knows this and documents it verbatim: its
`SetAssignOrderTests._run_cli` prepends `REPO_ROOT` to `PYTHONPATH` with the comment "Measured while
executing e3hzyc ... a CLI-level assertion silently tests code the change never touched". But the
SHARED fixture in the same file, `_RepoBackendCLIFixture._run_cli`, does NOT pin it, and neither do
the other subprocess-CLI call sites elsewhere in the suite.

## Why it matters, measured

Hit twice while executing plan `x75obw` (2026-09-23). First, an interactive check of the new
`aw check --strict-setid-length` flag reported `unrecognized arguments` because the `aw` entry point
resolved to the main checkout, which does not have the flag; the flag was in fact registered
correctly. Second, the same effect would have made the new authoring-guard tests pass vacuously had
they used the unpinned shared fixture, so they define their own pinned runner instead. A test that
passes against the wrong tree is worse than no test.

## Suggested direction (not a design decision)

Pin `PYTHONPATH` in ONE place (the shared fixture, or a `tests/support` helper every subprocess CLI
test uses) rather than per test class, so a new CLI test cannot forget. It is a no-op when the suite
runs from the main checkout, which is why the omission is invisible there and only bites in a lane.
