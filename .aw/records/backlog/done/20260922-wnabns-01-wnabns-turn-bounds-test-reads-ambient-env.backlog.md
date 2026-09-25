- Id: wnabns
- Status: done
- Set: wnabns
- Priority: medium
- Work-Kind: bug
- Summary: test_the_permission_policy_by_contrast_IS_isolation_scoped reads the ambient env, so it fails inside an OpenCode-driven turn

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by plan heglfv (executed); tests/test_turn_bounds.py deleted in 19313eed
- 2026-09-22 created (aw backlog): Found while executing skn8uk. tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped asserts OPENCODE_CONFIG_CONTENT is absent from a non-isolated turn's child env, but the env it inspects inherits the CURRENT process environment. An agent turn launched by 'aw oc run' exports OPENCODE_CONFIG_CONTENT itself, so the test fails for every agent executing a plan from inside a lane, while passing in a clean shell and in CI. Measured at HEAD ee20e831 with no product change: bare 'python3 -m pytest' fails it; 'env -u OPENCODE_CONFIG_CONTENT python3 -m pytest' passes 8085. The fix is for the fixture to build the child env from a controlled base rather than from os.environ, so the assertion measures what the runner sets.
