# 00 Run metadata

- Run ID: 20260712-173338 (local)
- Workflow: release-review (full mode; controlling file `.agents/workflows/release-review/README.md`)
- Agent/model: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Repository: <repo-root>
- Subject: **the agent-workflows framework itself** (explicit-subject exception per 00-run-protocol.md:30;
  the user explicitly invoked release-review on this repo, which maintains the runbook; prior runs
  20260706-112559 / D43 used the same exception). Framework directory IN scope as ordinary project
  code; `workflow-artifacts/` EXCLUDED.
- Git: branch `main`; HEAD `03c4c7c685d5b028c2a7f4a48b821ced1ca529b2`; remote
  `git@github.com:fariello/agent-workflows.git`; working tree clean except one untracked file (below).
- Ahead/behind: 20 commits ahead of `origin/main`, 0 behind (unpushed session work: contracts,
  release consent tree, docs consolidation, pre-flight gate fix).
- Tag state: `git describe` = `v1.1.0-116-g03c4c7c`. Never published to PyPI (v1.1.0 git-tag only, D51).
- Untracked: `.agents/docs/roadmaps/20260712-1426-...-roadmap-for-consideration.md` (a consideration
  doc in the deferred `roadmaps/` bucket).
- workflow-artifacts/: NOT git-ignored (verified).
- Environment: Python 3.14.6; stdlib-only runtime (zero deps); pre-commit (ruff, ruff-format,
  trailing-whitespace, end-of-file-fixer, gitleaks). 212 tests.

## Section 1 pre-flight gate (applied - the FIXED gate, D72)

- Discovery: NO pending plans, NO staged prompts, NO TODO/backlog files, NO code TODO/FIXME markers,
  NO true status/location mismatch (older uppercase `EXECUTED` plans in `executed/` are an
  old-vocabulary cosmetic inconsistency vs. the current lowercase `executed`, correctly located - noted
  as a candidate Section-5 finding, NOT a mismatch).
- Signals NAMED verdict-free (per the fixed gate): (1) 20 unpushed commits + never-on-PyPI; (2) one
  untracked roadmap-for-consideration doc in the deferred `roadmaps/` bucket.
- Interactive ask: fired (a real, if soft, signal existed). Framed verdict-free (no readiness claim).
  User answer: **PROCEED** with the full audit.
- Disposition: proceed; both signals folded into Section 6/8, not treated as pre-flight blockers.
