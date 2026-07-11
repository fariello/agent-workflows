# Evidence - assess documentation (20260711-173843)

Read-only assessment. What was inspected and how, so it is reproducible.

## Docs read in full

- `README.md` (292 lines), `ARCHITECTURE.md` (431), `CONTRIBUTING.md` (110), `AGENTS.md` (18),
  `.agents/workflows/index.md` (209).
- `.agents/workflows/assess/assess.md` (Step 0 + operating mode + the Write-the-IPD step),
  `.agents/workflows/assess/templates/ipd.md`, `.agents/workflows/setup-repo/setup-repo.md`
  (lifecycle + normalizer sections), `.agents/workflows/setup-repo/README.md`.
- `.agents/workflows/setup-repo/tools/normalize_plan_names.py` docstring + argparse.
- `pyproject.toml`, `agent_workflows/cli.py`, `install-workflows.py`, `agent_workflows/versioning.py`.

## Ground-truth commands

- `git describe --tags` -> `v1.0.0-40-gf613346`; `cat .agents/workflows/VERSION` -> `1.0.0`.
- `ls .agents/plans/` -> `executed pending reusable` (missing `superseded`, `not-executed`).
- `sed -n '9p' README.md` -> "two small Python helpers".
- `grep -n "four Python tools" ARCHITECTURE.md` -> line 382.
- `sed -n '3,4p' .agents/workflows/index.md` -> `WORKFLOWS-VERSION: 1.0.0` / `Version: 1.0.0`.
- `sed -n '124,126p' .agents/workflows/assess/assess.md` -> the `YYYY-MM-DD-assess-<concern>.md` example.
- `grep -n requires-python pyproject.toml` -> `>=3.8`; README floor "Python 3.9+" at :17,:200.
- Tool inventory: `.agents/workflows/**/tools/*.py` = scan_secrets, run_checks, bench_env,
  setup_tools, normalize_plan_names (5); plus install-workflows.py, hatch_build.py, versioning.py
  (root) and the `agent_workflows/` package (cli, engine, config, discovery, versioning, term,
  _compat).
- Counts cross-checked: 29 assess lenses, 7 advise personas, 16 command shims per tool dir, 14
  test modules under `tests/`. These match the docs except where noted (D-9).
- The `engine.py` type diagnostics (X-1) were observed as editor/LSP diagnostics while writing files
  in the repo (lines 734/935/1326/1454/1531/1607/1613/2282); not a doc concern, routed onward.

## Method

A subagent gathered the doc-vs-code cross-check across items 1-8 of the tasking (lifecycle states,
filename convention, normalizer tool, directory READMEs, tool counts, workflow/command counts,
versioning/CLI/packaging, other drift). The lead agent then re-verified the sharpest claims
first-hand (README:9, ARCHITECTURE four-tools, the plan-dir self-conformance gap, the index stamp,
the assess.md example, the Python-floor mismatch) before writing the IPD.

## Coverage / limits

- Focus was forward-facing docs + the assess-harness instruction that produces filenames. Individual
  lens/persona body prose was not line-audited (spot-checked counts + existence only).
- `workflow-artifacts/` and DECISIONS dated entries were treated as append-only history, not assessed
  as current docs.
- No files were modified during this assessment.
