- Id: n8adhb
- Status: open
- Set: n8adhb
- Priority: medium
- Work-Kind: chore
- Summary: tools/test_agy_run.py is not collected by any gate

## Workflow history
- 2026-10-01 created (aw backlog): tools/test_agy_run.py is not collected by any gate

`tools/test_agy_run.py` contains 44 passing tests that NO GATE RUNS.

Measured at HEAD `e132c1f43`:
- `pyproject.toml` sets `testpaths = ["tests"]`.
- `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -rfEs` and `python -m pytest tests/ -n auto -m slow`.
- `Makefile`'s `test` target runs `python3 -m pytest tests/`.
- A bare `python3 -m pytest --collect-only` matching `test_agy_run` returns only `tests/test_agy_runipd_cli.py`; the `tools/` module does not appear.
- Run explicitly: `python3 -m pytest tools/test_agy_run.py -o addopts="" -q` reports `44 passed in 1.50s`.

So the module is green but unenforced: a regression in `agy_run` argument parsing, target resolution, or mode detection would not turn CI red.

This was HALF THE CAUSAL STORY of bug `8jl0rx` (non-recursive spec resolution in `agy_run.resolve_spec`, which broke Spec Mode for every spec in the repository and went undetected). That item attributes the miss to an incomplete grep plus `resolve_spec` having zero coverage; the collection gap is the second mechanism, because it means coverage-shaped tests in that module provide no assurance. Plan `a6ootg` records this as its F-04 and routes its own new module to `tests/` for exactly this reason, deliberately leaving the existing module in place (relocating 44 tests is a separate change with its own regression surface).

Open question for whoever takes this: are there OTHER uncollected test modules under `tools/`? The fix should probably be either (a) move/merge the module into `tests/`, or (b) add a gate that FAILS when a `test_*.py` exists outside `testpaths`, which prevents recurrence rather than fixing one instance. Option (b) is the one that generalizes, and it should be checked against whatever documented workflow currently invokes the `tools/` module by name.
