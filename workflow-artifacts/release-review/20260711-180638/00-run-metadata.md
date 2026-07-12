# 00 Run metadata

> **ABANDONED 2026-07-12.** This `/release-review` run never progressed past this metadata stub: the
> `section-summaries/` directory is empty and no findings/action registers, decisions, validation
> results, or push plan were produced. The session pivoted to the pending-IPD backlog burndown
> (Bucket A/B execution + verification) instead of completing a full release review. No review verdict
> was reached; do NOT treat this run as a release sign-off. Kept as a record of the abandoned run
> rather than deleted. If a release review is needed, start a fresh run.

- Run ID: 20260711-180638
- Workflow: release-review (full mode; controlling file `.agents/workflows/release-review/README.md`)
- Agent/model: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Repository: <repo-root>
- Subject: **the agent-workflows framework itself** (explicit-subject exception per
  00-run-protocol.md - the user maintains this framework and has repeatedly treated the repo as the
  review subject; prior run 20260706-112559 / D43 used the same exception). `.agents/workflows/` is
  IN scope as ordinary project code; `workflow-artifacts/` run records remain EXCLUDED.
- Invocation argument: `l` - treated as a stray keystroke (not a valid path/flag); full-repo review
  at HEAD.
- Git: branch `main`; HEAD `212273ed5f9a7fc3f747b0e9bef7c14d4c7bbb39`; remote
  `git@github.com:fariello/agent-workflows.git`; working tree CLEAN at start.
- Ahead/behind: 8 commits ahead of `origin/main`, 0 behind (unpushed doc/version/plan work).
- Tag state: `git describe` = `v1.1.0-4-g212273e` - HEAD is 4 commits past the annotated `v1.1.0`
  tag; those 4 are planning artifacts (doc-IPD move, VERSION 1.1.0 bake, two IPD stubs, plan-review),
  not product-code changes. VERSION file = 1.1.0.
- workflow-artifacts/: NOT git-ignored (verified) - run artifacts will be committed deliverables.
- Environment: Python 3.14.6; stdlib-only project (zero runtime deps); pre-commit hooks present
  (ruff, ruff-format, trailing-whitespace, gitleaks).
- Baseline: full test suite green at start (`python3 -m unittest discover -s tests -t .`).
- Release context: first PyPI release intended at v1.1.0 (never published; v1.0.0 was git-tag only).
  The actual `twine upload` is a separate, credentialed, user-gated step (Section 9 / out of this
  autonomous run unless explicitly approved).
