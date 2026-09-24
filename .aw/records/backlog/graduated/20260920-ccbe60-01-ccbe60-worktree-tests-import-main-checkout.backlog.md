- Id: ccbe60
- Status: graduated
- Graduated-To: lanecli
- Blocks-Release: next
- Set: ccbe60
- Priority: high
- Work-Kind: bug
- Summary: Subprocess CLI tests run from a worktree silently exercise the MAIN checkout, because the editable install pins an absolute path

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to IPD lhjsu0 (lanecli Order 01). These three items are ONE defect with three victims (CLI, agent, suite), so one plan carries all three. VERIFIED LIVE at HEAD 22cf67d9 rather than trusting the filings: from a lane worktree with a NEUTRAL cwd, 'import agent_workflows' resolves to the MAIN checkout's __init__.py, because the editable install pins an absolute path there and the aw console script runs under a fixed interpreter shebang. THE MEASUREMENT THAT EXPLAINS WHY THIS SURVIVED: from the lane ROOT the cwd precedes the editable path, so the lane's own package wins and everything looks correct; only a neutral cwd or a subprocess flips it to main. Any fix or guard tested only from the lane root cannot distinguish fixed from broken, which the plan makes a hard requirement (E-04 must run from a NON-root cwd). ALSO MEASURED, and stronger than the filings claim: importing from a lane SUBDIRECTORY loaded MAIN's __init__.py while the LANE's agent_workflows/selectors.py shadowed the stdlib selectors module, crashing inside subprocess with AttributeError: module 'selectors' has no attribute 'SelectSelector'. That is two trees' code executing in one interpreter, not merely the wrong tree winning.
- 2026-09-20 created (aw backlog): Filed while executing plan e3hzyc: discovered when a CLI-level regression test PASSED against unfixed code in a lane.

FOUND WHILE EXECUTING PLAN e3hzyc IN AN ISOLATED LANE WORKTREE, and it is a validation-integrity defect rather than a cosmetic one: a test can report PASS while measuring code the change never touched.

WHAT HAPPENS. The repository is installed editable, and the installed `.pth`/finder names an ABSOLUTE path to the MAIN checkout (`site-packages/_editable_impl_agent_workflows.pth` -> `/.../agent-workflows/agent_workflows`). Many tests assert through a SUBPROCESS CLI (`subprocess.run([sys.executable, "-m", "agent_workflows", ...])`) and pass no PYTHONPATH, e.g. `_RepoBackendCLIFixture._run_cli` in tests/test_awnaming_grammar_and_producers.py. When pytest runs from a worktree, the IN-PROCESS imports resolve to the worktree (rootdir is on sys.path) but the SUBPROCESS imports resolve to the MAIN checkout.

MEASURED, TWICE, ON THE SAME COMMIT. Two new CLI-level regression tests for the `aw group plans` Order clobber failed before the fix and, after the fix was written IN THE LANE, still failed, because the subprocess kept running the main checkout's unfixed `plans_refs.py`. Conversely, once the fix was present in the main checkout the same tests would pass in a lane whose source was unfixed. Both directions are wrong: the test result is independent of the tree under test.

WHY IT MATTERS BEYOND THIS ONE FILE. Every lane-isolated execution (`aw oc run` / `aw agy run` default `isolate_worktree`) validates through this path, so a plan whose only evidence is a subprocess CLI assertion can be validated against the wrong source, in either direction: a real regression can pass, and a real fix can appear broken.

THE LOCAL WORKAROUND APPLIED IN e3hzyc: that plan's own test class overrides `_run_cli` to prepend its file's `REPO_ROOT` to the child's PYTHONPATH (a no-op in the main checkout). That is deliberately narrow, because e3hzyc's Scope-Paths fenced one test file.

THE REAL FIX is repo-wide and is what this item asks for: give the shared fixtures ONE helper that builds the child environment with the test tree's own root prepended to PYTHONPATH, and use it everywhere a test shells out to `-m agent_workflows`. Enumerate the call sites first: `rg -n 'sys.executable.*-m.*agent_workflows' tests/` and check which set PYTHONPATH (a few already do, e.g. tests/test_color_output.py and tests/test_executed_transition_gate.py, which is evidence the hazard is already known piecemeal). Consider a guard test that asserts a subprocess CLI resolves `agent_workflows.__file__` under the test tree.
