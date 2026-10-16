- Id: 5mnbaz
- Status: open
- Blocks-Release: next
- Set: cleantgt
- Priority: medium
- Work-Kind: bug
- Summary: tests/test_records_root_accessor.py has 2 failing tests at HEAD (runner_discovery, prompts_index)

## Workflow history
- 2026-10-16 created (aw backlog): tests/test_records_root_accessor.py has 2 failing tests at HEAD (runner_discovery, prompts_index)

Measured at HEAD 2e4e4c671 while authoring plan ki6t17 (backlog 4uw2a6): `python3 -m pytest -o addopts="" -q tests/test_records_root_accessor.py` fails two tests. (1) `test_home_records_runner_discovery` raises FileNotFoundError opening `.aw/records/plans/pending/20261015-cleantgt-01-kfnfji-...ipd.md`: plan kfnfji has since moved to `executed/`, so the test reads a lifecycle path that no longer exists. (2) `test_home_records_reproduction_prompts_index`: `aw index prompts --dir <target>` on a tracked repo with `records_backend: home` exits 2 with 'records directory records/prompts does not exist; nothing was written.', so the home-backed prompts index regression kfnfji fixed is red again (or the fixture no longer creates the directory). Determine which and fix.
