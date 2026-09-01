- Id: okm6e6
- Status: open
- Set: nogitmsg
- Priority: medium
- Work-Kind: bug
- Summary: aw attention's no-project message never checks whether cwd is a git repo, so it reports where it looked but cannot offer the install that would fix it

## Workflow history
- 2026-09-01 created (aw backlog): aw attention's no-project message never checks whether cwd is a git repo, so it reports where it looked but cannot offer the install that would fix it

OBSERVED (maintainer, 2026-09-01), run in a git repo with no AW layout:

    % aw att
    aw attention: no AW project found here.
    Checked /path/to/repo and its parents for a .aw/ (or legacy .agents/) project directory.
    Are you inside your repository? cd into the repo (or a subdirectory of it), or pass --dir <repo>.

The maintainer noted the message is genuinely helpful about WHERE it looked, and then said what it is
missing: "It would be super awesome if it actually knew that this was in fact a repo (it has a .git/)
and that it suggested maybe installing into this repo."

WHERE IT IS BUILT. `agent_workflows/project_context.py:330-342` (`no_project_message(verb)`) composes
the three lines above. It is emitted by `aw attention`/`att` at `agent_workflows/attention.py:1008`
(agent/JSON, `status="cannot-run"`, exit 3) and `:1011` (stderr, exit 3), guarded at `:983`.

THE FIX IS MESSAGE-ONLY, AND THE HELPER ALREADY EXISTS. `project_context._find_git_root(start_dir)` at
`:262-270` already walks up looking for `.git`; today only `resolve_project_context` (`:439`) calls it,
to pick a default `target_repo`. So the change is: when the AW climb fails, ALSO probe for a `.git`
ancestor, and when one is found, name that root and offer the install. Sketch of the added lines:

    Note: /path/to/repo IS a git repository, but agent-workflows is not installed in it.
    To install:  aw install /path/to/repo

For the `--agent`/`--json` path the same fact must be machine-readable, i.e. a
`NextAction(command="aw install <root>", description="install agent-workflows in this repo")` on the
`CommandResult` at `attention.py:1004-1009`, not only prose in `summary`.

EXPLICITLY OUT OF SCOPE: CHANGING ROOT DETECTION. `find_project_root` (`:273-292`) is DELIBERATELY
git-blind. Its own docstring (`:278-281`) states it: "git presence is NOT a marker: a `.aw/` tree can
exist without git, and a bare `.git` ancestor with no AW marker is NOT an AW project (IPD awretrofit
Order 06, OQ-01)". It is locked by `tests/test_awretrofit_project_root_climb.py:71-75`
(`test_bare_git_ancestor_is_not_a_root`). That rule is correct and must stay: this item changes only
what the FAILURE MESSAGE says, never what counts as a project.

SCOPE DECISION (kept narrow on purpose): fix `no_project_message` itself, so every current and future
caller inherits the hint from one place.

NOTED FOR A SUCCESSOR, NOT THIS ITEMS SCOPE: only TWO verbs emit this guidance at all. `aw attention`
(`attention.py:1008`/`:1011`) and `aw plans`/`aw ipd board` (`cli.py:6244`/`:6247`) call
`no_project_message`. Roughly twenty other repo-scoped verbs call `resolve_verb_repo_root` (`:314-327`)
and then SILENTLY fall back to cwd, so run outside a project they produce an empty or misplaced result
with no explanation: `backlog.py:341/474/653`, `specs.py:415/866`, `releases.py:600`,
`research_cmd.py:290`, `research_index.py:536`, `research_archive.py:292`, `plans_index.py:314`,
`plans_archive.py:191`, `plans_refs.py:395`, `artifact_rename.py:22`, `prompts.py:180`,
`reviews.py:236`, `run_cli.py:97`, `status_set.py:1101/1438`, `work_cmd.py:126`, and
`cli.py:7138/7390/9296`. Whether they should all emit the same guidance is a separate design question
(some may legitimately want to operate on a bare directory); it is recorded here so the asymmetry is
not rediscovered from scratch.

ALSO SEEN IN THE SAME SESSION, DELIBERATELY NOT FILED: the maintainer asked whether bare `aw` should
likewise suggest installing when run inside an unmanaged repo. That was investigated and DROPPED by
maintainer decision, because the cause turned out to be documented non-recursive discovery behavior
(a container directory holding nested repos, resolved with
`aw conf add <container> to repos.search`), not a defect. Recorded so it is not re-filed.
