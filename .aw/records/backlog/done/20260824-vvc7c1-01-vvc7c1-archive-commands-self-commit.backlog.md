- Id: vvc7c1
- Status: done
- Set: vvc7c1
- Priority: medium
- Work-Kind: feature
- Summary: Records-mutating commands (aw archive, and likely group/rename/research regroup) should offer to commit their own path-scoped changes when run interactively

## Workflow history
- 2026-09-08 done (aw set): OBSOLETE: every requirement was delivered by the executed selfcommit Set (88h0h8 / cv1rfd the shared helper / jgcm68 the adoption). Verified at HEAD fac69fbd: git_commit_helper.offer_commit:381 does TTY detection (:282), prompting (:298), path-scoped git add -- <paths>, an index snapshot before staging, and scoped rollback; cli._add_commit_flags:726 attaches --commit/--no-commit to all eight verb parsers the item names; seven production call sites cover archive/group/rename/research set-assign+mv/ipd set/specs set/backlog set. Requirement 5's per-verb messages exist. The item's 'include the regenerated index' clause was deliberately REVERSED by executed plan 4r0qp1, not left undone, so no work survives. No release gate to transfer.
- 2026-08-24 created (aw backlog): Records-mutating commands (aw archive, and likely group/rename/research regroup) should offer to commit their own path-scoped changes when run interactively

OBSOLETE 2026-09-08, VERIFIED AT HEAD `fac69fbd`. DO NOT GRADUATE THIS ITEM: everything it asks for
was built and executed by the `selfcommit` Set, which is entirely in `.aw/records/plans/executed/`
(orchestrator `88h0h8`, child `cv1rfd` the shared helper, child `jgcm68` the adoption across verbs).
The item's own closing question, "evaluate whether this belongs as shared plumbing in a single
'commit-what-I-changed' helper reused by all records-mutating verbs", was answered YES and built that
way.

WHERE EACH OF THE FIVE NUMBERED REQUIREMENTS NOW LIVES, each checked by reading the source:
  1. "Commit ONLY files the command itself touched." DONE. `git_commit_helper.offer_commit`
     (`agent_workflows/git_commit_helper.py:381`) takes an explicit `paths` sequence and stages with
     `git add -- <paths>`, never `-A` and never `-a`. Every caller passes the paths IT touched.
  2. "Interactive-only by default (TTY), an explicit `--commit` for non-interactive, and a
     `--no-commit` escape hatch." DONE, all three. TTY detection is `_is_interactive` (`:282`),
     prompting is `_prompt` (`:298`), and a non-interactive call without `assume_yes` returns
     `STATUS_SKIPPED` rather than committing. The flag PAIR is one shared registrar,
     `cli._add_commit_flags` (`agent_workflows/cli.py:726`), attached to eight parsers: `aw ipd set`
     (`:1358`), `aw research set-assign` (`:2259`), `aw research mv` (`:2278`), `aw group`/`aw rename`
     (`:3156`), `aw set` (`:3287`), `aw backlog set` (`:4103`), `aw specs set` (`:4369`), and
     `aw archive` (`:4578`). Verified: `aw backlog set --help` renders `--commit | --no-commit`.
  3. "Path-scoped, no push, no hook bypass." DONE. The helper commits through
     `commit_lock.commit_isolated` and never passes `--no-verify` and never pushes.
  4. "Do not fold in unrelated staged/unstaged changes." DONE, and hardened past the ask: the helper
     snapshots the index BEFORE staging (`pre_staged`), computes the unrelated set, and offers
     `on_unrelated_staged="scope"|"refuse"`; every failure path rolls back with
     `git reset --quiet HEAD -- <paths>`, scoped to its own paths only.
  5. "A good default commit message per verb." DONE, per verb: `chore(plans): archive aged artifacts
     and regenerate index` (`plans_archive.py:296`), `chore(research): archive ...`
     (`research_archive.py:401`), `refactor(<types>): <verb> ... and rewrite refs` (`cli.py:8656`),
     `chore(<label>): set status <status>` (`status_set.py:1148`), `chore(specs): set status <status>`
     (`specs.py:700`).

EVERY VERB THE ITEM NAMES IS WIRED. `offer_commit` has seven production call sites
(`cli.py:4830`, `plans_archive.py:294`, `research_archive.py:399`, `specs.py:697`,
`status_set.py:1146`, `work_cmd.py:470`, `oc_runipd.py:1414`), covering `aw archive` (plans and
research), `aw group`/`aw rename`, `aw research set-assign`/`mv`, `aw ipd set`, `aw specs set`,
`aw backlog set`, plus `aw commit`/`aw finish` and the runner finalize. None of the item's named verbs
is missing. Tests: `tests/test_git_commit_helper.py` and `tests/test_selfcommit_adoption.py` (a
per-verb adoption spy).

ONE PART OF THE ITEM'S PREMISE WAS DELIBERATELY REVERSED, not implemented, and this is the only
divergence worth recording. The item asks that the commit include "the regenerated index". It does
NOT, by a later decision: executed plan `4r0qp1` (idxuntrack E-02/E-03/E-07) made `INDEX.json` and
`INDEX.md` generated output that no `aw` verb commits. See the explicit comments at
`status_set.py:1134-1136` and `plans_archive.py:282-283`. That is a superseding decision rather than
an unmet requirement, so it leaves no surviving work here.

WHY `done` AND NOT `parked`: nothing awaits a decision or a future opportunity. The capability exists
in the tree and is under test, so the item is satisfied rather than shelved. Evidence is the executed
`selfcommit` Set plus the source above.

ORIGINAL ITEM TEXT FOLLOWS.

When a records-mutating verb (starting with 'aw archive', and probably its siblings 'aw group', 'aw rename', 'aw research set-assign/mv', 'aw ipd set', 'aw specs set') moves/renames files and regenerates an INDEX, it currently leaves the resulting changeset uncommitted. The user then has to notice and hand-commit a large, coherent set of renames + index updates (e.g. the 23-file 'aw archive' research changeset). Instead, when run interactively (a TTY), the command should PROMPT to commit the change it just made, and on yes create a path-scoped commit of ONLY the files it changed (the moved/renamed paths plus the regenerated index), never 'git add -A'/'-a', never push, with a descriptive default message. Requirements/constraints: (1) commit ONLY files the command itself touched - track them explicitly rather than committing whatever is dirty; (2) interactive-only by default (TTY): non-interactive/CI runs must NOT auto-commit unless an explicit flag like --commit is passed, and there should be a --no-commit escape hatch; (3) respect the repo contract (path-scoped, no push, no hook bypass); (4) if the tree already has unrelated staged/unstaged changes, do not fold them in - stage only this command's own paths; (5) a good default commit message per verb (e.g. 'chore(research): archive aged artifacts and regenerate index'). Evaluate whether this belongs as shared plumbing in a single 'commit-what-I-changed' helper reused by all records-mutating verbs. Origin: user request after 'aw archive' left a 23-file research changeset uncommitted.
