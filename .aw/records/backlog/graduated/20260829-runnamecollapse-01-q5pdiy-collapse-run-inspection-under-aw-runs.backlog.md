- Id: q5pdiy
- Status: graduated
- Set: runnamecollapse
- Priority: medium
- Work-Kind: chore
- Summary: aw run list duplicates aw runs byte-for-byte; collapse run inspection under aw runs and retire the aw run noun

## Workflow history
- 2026-08-29 graduated (aw set): Graduated into plan 0soncw (.aw/records/plans/pending/20260829-runnamecollapse-01-0soncw-...ipd.md), which carries - From-Backlog: q5pdiy and is to-review with an 8-item E/V bijection. Design handed off; no code written yet.
- 2026-08-29 created (aw backlog): aw run list duplicates aw runs byte-for-byte; collapse run inspection under aw runs and retire the aw run noun

DEFECT (verified live at HEAD 477569a). `aw run list` and `aw runs` emit BYTE-IDENTICAL output: both
dispatch to the same renderer (`run_cli.run_cli` maps `list`/`runs`/`summary`/`viewer` straight to
`run_viewer.run_viewer_cli`, agent_workflows/run_cli.py:49-52). Measured:

    $ python3 -m agent_workflows run list > a.txt; python3 -m agent_workflows runs > b.txt
    $ diff a.txt b.txt && echo BYTE-IDENTICAL
    BYTE-IDENTICAL          # 967 lines, zero diff

Two names, one job. This is a naming defect, not user error: it is why the two get misremembered.

Compounding it, `aw run` RUNS NOTHING. It is purely ledger/run inspection plus the ledger transaction
verbs (show/evidence/verify-ledger/start/next/record/resume/cancel/status/finalize/decisions/questions).
The name that reads like 'run an agent' is held by a read-only inspector, while the actual drivers are
`aw oc run` / `aw agy run`.

DIRECTION (maintainer decision, 2026-08-29): COLLAPSE INSPECTION UNDER `aw runs` and retire the
`aw run` noun, freeing the name. `aw runs` already won: it is the invested surface and it reads the
format the runner actually writes.

The migration is CHEAP (checked, contrary to an earlier assessment that called it a breaking migration
needing its own spec): no production code shells `aw run <sub>` (hits under agent_workflows/ are
docstrings; benchmark_runners.py:273 is `opencode run`; agy_runipd.py:2641 is the driver `run` after
`agy`), it is ONE parser site (cli.py:1390-1560), ~4 test files, one doc (exec-set.md), and zero
shims or hooks.

SCOPE NOTE / NON-GOAL: actually making `aw run <selector>` MEAN 'run on the default host' additionally
requires a default-host concept, which does NOT exist anywhere (project_schema.py has `enabled_hosts`
but no default/preferred host, and nothing is in the pipeline for it). That resolution must be designed
separately; freeing the name can land WITHOUT it. Do not conflate the two.
