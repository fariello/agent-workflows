- Id: phjr9f
- Status: done
- Blocks-Release: next
- Set: homeleak
- Priority: high
- Work-Kind: bug
- Summary: The test suite wrote the developer's real user config and AW_HOME: DeclarativeAllowedValuesTests set aw_home to ~/allowed in ~/.config/agent-workflows/config.json, and analytics tests left hundreds of dirs under ~/.aw/projects

## Workflow history
- 2026-09-25 done (aw set): fixed: conftest sandbox + autouse restore; traced 0 home writes on a bare suite
- 2026-09-24 created (aw backlog): The test suite wrote the developer's real user config and AW_HOME: DeclarativeAllowedValuesTests set aw_home to ~/allowed in ~/.config/agent-workflows/config.json, and analytics tests left hundreds of dirs under ~/.aw/projects

MEASURED 2026-09-24 with a Python audit hook on a bare python3 -m pytest: the only writes under the real home were 2 mkdir+rename pairs into ~/.config/agent-workflows/ from tests/test_config.py::DeclarativeAllowedValuesTests (set_config_value saves config.json; the class had no XDG_CONFIG_HOME sandbox; added 2df4b271). Earlier, the run-analytics tests (deleted by 19313eed) left 294 dirs under ~/allowed/projects and ~550 under ~/.aw/projects. ROOT CAUSE: tests/__init__.py sandboxed AW_HOME/XDG_CONFIG_HOME only when the caller had NOT exported them, and ~20 tests clean up with os.environ.pop(...), which deletes the sandbox for every later test in the same xdist worker under randomized order. FIX: root conftest.py installs the sandbox unconditionally and an autouse fixture restores it after every test; the offending class sandboxes itself; tests/test_home_isolation.py guards both halves (verified failing with the fixture disabled). Re-traced after the fix: 0 home writes, also with XDG_CONFIG_HOME/AW_HOME exported to the real dirs.
