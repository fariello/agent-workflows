- Id: okm6e6
- Status: graduated
- Blocks-Release: next
- Set: nogitmsg
- Priority: medium
- Work-Kind: bug
- Summary: aw attention's no-project message never checks whether cwd is a git repo, so it reports where it looked but cannot offer the install that would fix it

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan quqyc4 (Set nogitmsg, .aw/records/plans/pending/20260908-nogitmsg-01-quqyc4-...ipd.md), which carries From-Backlog: okm6e6 and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done: no code is written yet. NOTHING IN THIS ITEM IS OBSOLETE, but EVERY EMIT-SITE LINE NUMBER HAD DRIFTED and was re-located by SYMBOL at HEAD 44d4950d: this item cites attention.py:1008 and :1011 for the two emit sites, which are now :2200 and :2203 (a ~1190-line drift), guarded at :2174. Its other citations verify unchanged: no_project_message at project_context.py:330-342, _find_git_root at :262-270 with its single existing caller at :439, find_project_root at :273-292 with the git-blind rationale in its own docstring at :279-281, and the locking test test_bare_git_ancestor_is_not_a_root at tests/test_awretrofit_project_root_climb.py:71-75. Also corrected: this item's aw plans spelling is NOT a registered command (aw plans --agent exits 2 from argparse with an invalid-choice error), so the cli.py:6244/:6247 citation belongs to aw ipd board, whose emit sites are now cli.py:7203/:7206. The scope decision (fix no_project_message itself, in one place) is preserved, and the OUT-OF-SCOPE rule is preserved and reinforced: find_project_root stays git-blind and its locking test must pass UNMODIFIED, which the plan makes an explicit checklist item rather than an assumption. NEW DEFECT FOUND WHILE REPRODUCING THIS ITEM, and it is more serious than the item's own concern, so the plan absorbs it rather than deferring it: on the --agent path this condition CRASHES rather than degrading. Measured in a bare git init directory with no AW layout: aw attention (human) exits 3 correctly; aw attention --json exits 3 correctly; but aw attention --agent exits 1 with an unhandled ValueError('Invalid aw.agent/v1 record: Field exit must be an integer in (0, 1, 2), got 3; Error record must carry exit=2, got exit=3') and a full traceback, raised from agent_schema.assert_valid_agent_record (agent_schema.py:315-319) via result_types.to_agent_record (:451) via renderers.py:195. aw ipd board --agent reproduces it identically (exit 1). It is IN SCOPE here rather than a separate item because this item REQUIRES the new git fact to be machine-readable as a NextAction on that same CommandResult, and there is no point attaching a NextAction to a record that cannot be emitted. The cause is a contradiction between two shipped contracts (the verbs use exit 3 for cannot-run; the schema admits only 0/1/2 and demands exactly 2 for an error record), so the direction of the fix is a maintainer decision and is carried as the plan's BLOCKING open question OQ-01. The NOTED-FOR-A-SUCCESSOR asymmetry (only two verbs emit this guidance while ~20 others silently fall back to cwd) is carried into the plan as a documentation-only item with an instruction to spot-check the cited call sites rather than copy them on faith, given how far this item's own citations had moved.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

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
