- Id: aluots
- Status: done
- Graduated-To: agentident
- Set: aluots
- Priority: medium
- Work-Kind: feature
- Summary: Mark every aw-made commit as agent-made: author stays the user, committer becomes 'AW Agent (<model>) <user+aw@...>', plus runner trailers on every commit

## Workflow history
- 2026-10-14 done (aw backlog): closed by aw agy run: IPD yr3d4o executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-agentident-01-yr3d4o-mark-every-aw-made-commit-as-agent-made-with-an-agent-commit.ipd.md); evidence .aw/records/plans/executed/20261012-agentident-01-yr3d4o-mark-every-aw-made-commit-as-agent-made-with-an-agent-commit.ipd.md
- 2026-10-12 graduated (aw set): graduated to plan yr3d4o (Set agentident) on the maintainer's instruction
- 2026-10-11 created (aw backlog): Mark every aw-made commit as agent-made: author stays the user, committer becomes 'AW Agent (<model>) <user+aw@...>', plus runner trailers on every commit

MAINTAINER DECISION 2026-10-11: agent commits must be distinguishable from the maintainer's own, without new accounts or GitHub setup (the toolkit must stay zero-setup for other users). Chosen design, and ONLY this (separate keys, bot accounts, credential hiding and PR requirements were considered and declined):

1. AUTHOR stays the user's own git identity (unchanged, so GitHub attribution and contribution stats are unaffected).
2. COMMITTER becomes `AW Agent (<model>) <local+aw@domain>`, derived from the user's own email by plus-addressing (e.g. `gabriele.fariello+aw@gmail.com`), so no new address or account is needed. `<model>` is the model that produced the work (the run's resolved model, or the interactive session's when known); when unknown, say `unknown`, never guess.
3. TRAILERS are kept and extended: `AW-Run` / `AW-Item` as today, plus the runner that made the commit (e.g. `AW-Runner: aw oc run` / `aw agy run`, or `aw commit` for an interactive session) when relevant.

MEASURED STATE (2026-10-11): every commit is authored by the user; only 2,509 of 9,520 commits on main carry an `AW-Run` trailer, and only 127 of the last 300. Commits WITHOUT any marker include runner-made `integrate(...)` merges, `lifecycle(...)` finalize commits, some runner-made `work(...)` commits (e.g. 0dd8c3a3e), and every commit an interactive agent session makes through `aw commit`. So `git log` cannot tell agent work from the user's.

WHERE IT PLUGS IN: git honors `GIT_COMMITTER_NAME` / `GIT_COMMITTER_EMAIL` from the environment for commits AND merges. Both runners already build the agent child env in one place (`oc_runipd` / `agy_runipd`, where they set `git_commit_helper.RUN_ID_ENV` / `ITEM_ID6_ENV`); the driver's own commits go through `git_commit_helper._git` (via `commit_lock.commit_isolated`, `ipd_lifecycle._git`) and `runner_shared._run_git` (merges). One shared helper should compute the committer identity and the trailer set, and every aw commit and merge path should use it.

HONEST LIMIT: this LABELS commits made through aw's tooling. It is not tamper-proof: an agent running raw `git commit` outside aw still gets the user's identity. Accepted as sufficient for telling agent work from the user's own at a glance.

ACCEPTANCE: driving `aw commit`, a runner work commit, a lifecycle finalize and an integrate merge in a fixture repo each yields author = the repo's user identity, committer = `AW Agent (<model>) <user+aw@...>`, and the trailers; a commit the user makes with plain `git commit` is unchanged.
