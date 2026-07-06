# 00 Run metadata

- Run ID: 20260706-112559
- Workflow: release-review (full)
- Agent/model: opencode, its_direct/pt3-claude-opus-4.8-1m-us
- Repository: <repo-root>
- Subject: THIS repository (the agent-workflows framework itself). Explicit-subject
  exception per 00-run-protocol.md line 30 is IN EFFECT: `.agents/workflows/` (release-review,
  assess, advise, verify, benchmark, setup-repo, scaffold, spec, incident, release-notes,
  migrate, list-workflows, getting-started, assess-all, index.md), the installer, tools, tests,
  shims, and root docs are all in scope as ordinary project code.
- Out of scope regardless: `workflow-artifacts/` run records (this run and prior runs). Read
  as input only; no findings filed about them.
- Git: branch main, head a7cf5c3, remote git@github.com:fariello/agent-workflows.git
- Initial working tree: clean
- workflow-artifacts/ gitignored: NO (correct; committed deliverables)
- Environment: Python 3.14.4, git 2.53.0, Linux 6.18 (WSL2)
- Framework VERSION under review: 20260704-05

## Self-review caveat (honesty)

The agent conducting this review is the same author that built and recently modified much of
this repository (D38-D42 in DECISIONS). This is a rigorous self-check tied to file:line
evidence and executable validation (46 self-tests, installer dry-runs), NOT an independent
audit. Findings are grounded in evidence, not self-assessment. Where independent verification
would matter (e.g. cross-tool behavior, real HPC/NFS), it is called out.
