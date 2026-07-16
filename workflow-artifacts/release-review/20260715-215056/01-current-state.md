# Section 1 - Current state (release-review run 20260715-215056)

Mode: REPORT-ONLY (findings + IPDs; NO in-place fixes), framework-is-the-subject (agent-workflows is
the product being assessed for release), NO push/tag/publish. Auto-parallel audit lanes engaged for
Sections 2-6 (D84; >=2 independent surfaces).

## Baseline

- Branch `main`, HEAD `817cbb7`, 10 commits ahead of `origin/main` (unpushed). Remote
  `git@github.com:fariello/agent-workflows.git`.
- `.agents/workflows/VERSION` = `1.2.1`; latest tag `v1.2.0`; resolver reports `1.2.1.dev63+g817cbb7`
  (dirty/ahead-of-tag by design).
- Tests: `258 passed, 1 skipped` (full suite green).
- Pending IPDs: 0. Latest DECISION: D84. TODO "Known bugs": none open. TODO/FIXME markers in
  `agent_workflows/`: 0.
- 17 workflow dirs; 18 command shims per tool (opencode/claude).

## Pre-flight gate (00-run-protocol Section 1)

Cursory look at TODO + pending plans + staged prompts: **no blocking signal.** Queue empty, no known
bugs, no code markers, tree clean. Therefore the pre-flight ask does NOT fire (verdict-free skip). ONE
non-blocking signal recorded for Section 8: the CHANGELOG carries TWO pending release sections
(`1.2.1` patch + `1.3.0` features), i.e. a release-SCOPE decision (which to cut) is pending - that is a
human decision, not a defect, and belongs in the Section 8 Go/No-Go.

## Run-setup state issue found + resolved (pre-audit)

Run Setup found 7 STAGED-but-never-committed files (the `.agents/comms/` scaffold + two docs-bucket
`.gitkeep`s) left staged by earlier installs' own `git add` and never swept into a path-scoped commit.
Confirmed they were intended tracked files with the correct scaffold content. Committed as `817cbb7`
(housekeeping) with the maintainer's approval, so the review audits a clean release candidate. Recorded
as finding REL-000 (resolved).

## Scope

IN scope: `agent_workflows/` (engine, cli, comms, plans, versioning, config, discovery, term,
pypi_links), the workflow tools, packaging (`pyproject.toml`, `hatch_build.py`), root governance docs,
`.agents/workflows/` bodies + templates, tests. Framework-is-subject override is deliberate (per
maintainer): normally release-review excludes `.agents/workflows/`, but here it is the product. The
runbook itself (`release-review/`) and `workflow-artifacts/` run records are NOT modified during the run.
