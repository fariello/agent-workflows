# 01 Repository inventory

## Project type and intent
- A portable framework of AI-agent workflows (Markdown "runbooks" under `.agents/workflows/`) PLUS a
  pip/PyPI-installable Python package + CLI (`agent-workflows` / `aw`) that installs the workflows into
  target repos, generates per-tool slash-command shims, and scaffolds the plan/docs lifecycle.
- Audience: engineers/maintainers running coding agents (OpenCode, Claude Code, Gemini/Antigravity)
  across many repos; the maintainer runs it across ~27 downstream repos.
- Intent/goals/philosophy: well documented (README intent, ARCHITECTURE, GUIDING_PRINCIPLES 10
  principles, DECISIONS D1-D73 dated rationale). Strong cold-start orientation surface.

## Structure / stack
- Package `agent_workflows/` (~4805 LOC, 11 modules): `engine.py` (2672, the installer), `cli.py`
  (874), `versioning.py` (369, tag-driven semver + rc), `config.py`, `discovery.py`, `plans.py`,
  `pypi_links.py`, `term.py`, `_compat.py`, `__init__/__main__`.
- Zero runtime dependencies (stdlib only). Python 3.14 in this env.
- Tests: 17 files, 212 tests (stdlib unittest, run via pytest). Covers installer, cli, versioning,
  packaging, plans board/status, normalizer, discovery, scan-secrets, setup artifacts, term, config.
- Build: `pyproject.toml` + `hatch_build.py` (version from the resolver; README link rewrite for PyPI).
  `Makefile` (test, version, version-file).
- CI: `.github/workflows/tests.yml`, `secret-scan.yml`.
- Workflows (~16): release-review, plan-review, plan-review-long, assess (+lenses), assess-all, advise,
  verify, verify-execution, benchmark, setup-repo, scaffold, spec, incident, release-notes, migrate,
  list-workflows, getting-started.

## Public contracts
- CLI: `install`, `setup`, `uninstall`, `list`, `status`, `plans`, `plan-names`, `-V/--version`.
- The installed `.agents/` tree + generated shims (`.opencode/commands/`, `.claude/commands/`) + the
  managed `AGENT-WORKFLOWS` pointer block written to `AGENTS.md` (and existing CLAUDE.md/GEMINI.md).
- The version string (tag-driven, PEP 440, incl. `-rc.N`).

## Guiding principles doc
- `GUIDING_PRINCIPLES.md` (10 principles: fix-by-default, honest docs, self-documenting, durable
  cold-start knowledge, KISS, general-case, single-source, ...). Binding contract for this review.

## Backlog / pending / durable-knowledge inventory
- No `TODO.md`/backlog files; no code TODO/FIXME markers; no pending plans; no staged prompts.
- Durable knowledge homes: README, ARCHITECTURE, DECISIONS (D1-D73), GUIDING_PRINCIPLES, RELEASING.md
  (new this session), `.agents/docs/` (research/walkthroughs/specs/prompts/roadmaps).
- One untracked consideration doc under `.agents/docs/roadmaps/` (deferred bucket).

## Release context
- 20 commits ahead of origin, unpushed. Never on PyPI (v1.1.0 git-tag only, D51). First PyPI publish
  intended at 1.1.0, still a separate user-gated step.

## Initial drift/quality signals to probe in the audit (candidate IDs assigned in later sections)
- Old-vocabulary `Status: EXECUTED` (uppercase, parenthetical) in ~18 older `executed/` plans vs. the
  current lowercase `executed` (D52) - cosmetic consistency; append-only history so likely leave-as-is.
- Pre-existing `Term(<bool>)` type-checker (pyright/LSP) diagnostics in `engine.py` (noted repeatedly
  during session executions; deferred as out-of-scope then). Worth a real look this run.
- ARCHITECTURE shim count claim ("16") vs. actual generated shim count - verify not stale.
