- Id: ylvzct
- Status: open
- Blocks-Release: next
- Set: ylvzct
- Priority: low
- Work-Kind: bug
- Summary: check.scope-drift flags gitignored __pycache__/*.pyc inside new directories during aw commit

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-19 same-status (aw set): Gate next release for live bug
- 2026-11-17 created (aw backlog): check.scope-drift flags gitignored __pycache__/*.pyc inside new directories during aw commit

Observed during g8na48 commit of new package agent_workflows/migrations/: although .gitignore ignores __pycache__/, aw commit reported advisory check.scope-drift for agent_workflows/migrations/__pycache__/__init__.cpython-314.pyc and agent_workflows/migrations/__pycache__/chain.cpython-314.pyc.
