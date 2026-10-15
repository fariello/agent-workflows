# Review findings: plan fnnwj3

- Subject-Id: fnnwj3
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane.

- The plan was committed and unchanged at `937eb74d1`, so no snapshot was needed.
- `aw ipd lint` was clean at `author` before the edits and at `review-finalize` after them.
- All 21 cited symbols and quoted strings resolve, and all 7 E-07 test modules exist.

### Fixture

Built with temp `HOME`/`AW_HOME`/`XDG_CONFIG_HOME` under `/tmp/opencode/fn3`:

1. `aw install --preset completely-clean-target -y --no-interactive`, which exited 0.
2. `.aw` and the other residue removed from the index and HEAD.
3. A linked worktree added under `<AW_HOME>/projects/<id>/worktrees/abc123`.

The installer also stores `delivery_mode: clean-delta` for `--preset local-only`, which supports OQ-01.

### Probes

F-01 to F-03 reproduced:

- The root, `sub/deep` and the lane are all `no-project`, and the lane derives `abc123-<hash>` as `tracked`.
- With `<AW_HOME>/config/` present, `find_project_root(<lane>)` returns `$HOME` (`inside-project`).

When only the working-tree `.aw` was deleted, the lane checked out the committed `.aw` and read `is-project-root` with id `abc123-<hash>`, `tracked`.

A prototype of E-02..E-04 (kept at `.aw/state/rev-fnnwj3/proto.py`, gitignored):

| Case | `find_project_root(<root>/sub/deep)` | `find_project_root(<lane>/x)` |
|---|---|---|
| As written | `<root>/sub/deep` | `<lane>/x` |
| With a `.git`-exists guard | `<root>` | `<lane>` |

With the guard, `home_configured_root` is False for both subdirectories and True for the root and the lane.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | E-03(1) "derive the home `project_id` from `checkout_main_root(repo) or repo`"; E-02 "walk up from `path` to the first ancestor holding a `.git` entry"; the prototype table above | `checkout_main_root` climbs, so the unguarded anchor maps every subdirectory to its root. `home_configured_root(<root>/sub/deep)` therefore becomes True and `find_project_root` stops AT the subdirectory, which breaks E-04's own expected outcome ("`<root>/sub/deep` -> `find_project_root` = root") and treats any cwd as the project root. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The anchor and `home_configured_root` now apply only when `path/.git` exists. The prototype shows this fixes both subdirectory cases. Added F-09, E-03 expected outcomes, an E-06(c) assertion, and the Proposed changes text. |
| PR-002 | MEDIUM | IN-SCOPE | E. Test fixture validity | Installer commit `a1bfc04`-style (irjoga F-01); probe: a lane checked out from HEAD carries `.aw/` | Deleting only the working-tree `.aw` leaves `.aw/` committed, so `git worktree add` restores it into the lane. The lane cases would then pass or fail for the wrong reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and E-06 now remove the residue from the index and HEAD (`git rm -r --cached .`, commit, `git clean -fdx`). |
| PR-003 | MEDIUM | IN-SCOPE | E. Reachability | `cli._run_status` `if not repos:` guards the cwd fallback; `cli._repos_for_report` reads the user config | The lane `aw status` demand reaches the edited fallback only when no repos are registered. The fixture install registers the target, so the edited code could go unexercised. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05, E-06(e) and V-05 now require a user config that registers no repos, and name the fallback path. |
| PR-004 | LOW | IN-SCOPE | E. Command accuracy | `aw attention --help` offers `--format`/`--agent`/`--json`; other plans in this Set use `--format json` | E-06(f) spelling was inconsistent with the rest of the Set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now `aw attention --format json`. |
| PR-005 | LOW | IN-SCOPE | G. Verification checklist | E-06 expected outcome names two mutations; V-06 demanded only one | The anchor mutation could be claimed without evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 now demands both mutation runs and a clean restore. |
| PR-006 | LOW | UNDER-SCOPE | G. Dependencies | `20261014-nj13xp-01-ivq0nr-...ipd.md` `Readiness: no-go`, OQ-01 `Blocking: yes`, `Owner: maintainer` | The gate did not say that the `ivq0nr` dependency is currently held by a maintainer question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the note to the execution contract, cross-referenced with orchestrator `ucr3h8`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the identity anchor avoid capturing subdirectories? | Apply `checkout_main_root` and `home_configured_root` only when `path/.git` exists | Make `checkout_main_root` non-climbing (also correct, but it changes E-02's documented contract and its subdirectory test row); leave as written (breaks E-04) | Review prototype table; `find_project_root` loop in `project_context.py:315` tests each climbed dir | yes |
