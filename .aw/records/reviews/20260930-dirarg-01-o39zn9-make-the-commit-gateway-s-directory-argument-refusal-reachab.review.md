# Review findings: plan o39zn9

- Subject-Id: o39zn9
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (HIGH, fixed), PR-702 (HIGH, fixed), PR-703 (MEDIUM, fixed), PR-704 (MEDIUM, fixed), PR-705 (MEDIUM, fixed), PR-706 (LOW, fixed), PR-707 (LOW, fixed)

## Round 1

Reviewed at HEAD `d194bdd0` in an isolated review lane. The plan file was already committed and
byte-identical to the lane input, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize --agent` reports `conforming` after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

EVERY ONE OF THE PLAN'S OWN CLAIMS REPRODUCED, and I drove the real functions rather than reading
them, because the plan's central assertion is that a shipped fix changed what the backlog item
measured. F-01: `offer_commit(r, ['sub'], assume_yes=True)` returns `error` with
`refusing directory argument(s): sub; name explicit file path(s) instead: sub/a.md, sub/b.md`,
`git status --porcelain` byte-identical at ` M sub/a.md\n M sub/b.md\n` before and after, `git log`
showing only the seed commit. F-02: the same call with `no_commit=True` returns
`skipped: --no-commit requested`, and through the REAL `cli.main` the preview prints
`aw commit: skipped: skipped: --no-commit requested` where the real run prints
`aw commit: error: refusing directory argument(s): sub; ...`. F-03: `commit_isolated(r, ['sub'])`
raises `IsADirectoryError`, with F-04's no-residue property holding (`git worktree list` shows only
the fixture's own worktree, the `.aw-isocommit-*` glob is empty). F-05 reproduced to the character:
434-char message, 31 files, `'sub/ig' in message` is `False`. F-06 reproduced both arms. So the
plan's diagnosis is right, its narrowing of the backlog item is honest and correct, and E-02 is the
right fix at the right site; I PROTOTYPED E-02 exactly as specified and the whole bare suite stayed
green at `3387 passed, 2 skipped` (F-13), then reverted clean.

WHAT REVIEW FOUND IS THAT THE PLAN'S PREDICATE IS WRONG, AND BOTH OF ITS FIXES INHERIT THE ERROR.
Every directory test in the plan and in the shipped code keys on `Path.is_dir()`, which asks the
FILESYSTEM. A directory whose files were all deleted or moved away does not exist on disk, so
`is_dir()` is `False` and the refusal never fires. That is not a corner case: emptying a directory
by moving its contents out is precisely the records-move shape `hv9gar` was written for. Two
distinct defects follow, each measured, and NEITHER was in the plan.

THE FIRST IS WORSE THAN THE DEFECT THE PLAN WAS FILED TO FIX (PR-701). With `sub/` removed and
`file.md` modified, `offer_commit(r, ['sub', 'file.md'], ...)` returns `committed`, commits
`file.md` alone, reports `(1 path(s) had nothing to commit: sub)` and LEAVES `D sub/a.md` and
`D sub/b.md` STAGED in the shared index. The `residue` rollback the plan relies on in F-01 cannot
save it, because that arm runs only when `our_staged` is EMPTY and `file.md` made it non-empty; the
all-directories variant does self-clean, which is exactly why only the MIXED shape leaks and why
reading the code without driving it misses this. The significance is contractual, not cosmetic:
`AGENTS.md` instructs every agent in this shared checkout to commit through `aw commit` BECAUSE it
"commits only the intersection of those paths with what it itself staged, and on any failure resets
ONLY its own paths". Here the verb reports SUCCESS while leaving staged deletions a co-worker's next
commit would sweep in. A release-gating bug plan that leaves a worse bug live in the same function
is not narrow, it is incomplete, so E-04 and V-04 were added.

THE SECOND MEANS E-03 AS WRITTEN DOES NOT FIX WHAT IT CLAIMS (PR-702). I prototyped E-03's
`is_dir()`-keyed guard and re-measured: `commit_isolated` on a DELETED directory STILL RAISES
`IsADirectoryError`, now from `dst.unlink()` on the deletion arm rather than from `shutil.copy2`.
The mechanism is the mirror image of the first defect: the shared tree no longer has `sub/` so the
guard misses, but the throwaway worktree is checked out at HEAD where `sub/` still exists, so
`dst.exists()` is true and `unlink()` on a directory raises. The plan names only the `copy2` site
and would have shipped a guard that reads complete and covers half the function. E-05 and V-05 were
added, and E-05 must use `commit_lock._git` (which already delegates to the canonical runner inside
the function body) rather than importing upward, which the plan correctly identified as a cycle.

THE HARD CONSTRAINT ON BOTH FIXES, and the reason the widened predicate needed measuring rather than
asserting: `commit_isolated` DELIBERATELY supports a deleted path. `_content_hash`'s docstring
records that its `None` sentinel is "load-bearing, not defensive" because the finalize caller really
passes a path that no longer exists, and `offer_commit` carries the matching `or _in_index(...)`
clause in its `add_paths` filter. A predicate widened carelessly would refuse a deleted FILE and
break committed deletions, which is one of the two defects `hv9gar` shipped to fix. I therefore
measured a candidate predicate across six cases (live directory, live file, untracked-only
directory, deleted directory, deleted plain file, nonexistent path) and it answers correctly on all
six; both E-items now require that table and a NEGATIVE CONTROL, and V-04/V-05 demand the control's
evidence. I also confirmed a tracked symlink to a directory is ALREADY refused and that this
repository contains zero tracked symlinks (F-15), so no symlink clause is owed.

I ALSO MEASURED THE LIMIT OF E-02'S CLAIM (PR-703). The plan asks the docstring to record that the
preview now agrees with the real run. THREE OTHER OUTCOME CLASSES STILL DIVERGE under `no_commit`:
an all-gitignored path-set previews `skipped` and really returns `nothing-to-commit` (confirmed
through `cli.main` too); an unrelated-staged set under `on_unrelated_staged="refuse"` previews
`skipped` and really returns `refused-dirty`; and a non-interactive call without `assume_yes`
previews `skipped: --no-commit requested` where the real run gives a different reason. Each would
require moving a DIFFERENT check ahead of the short-circuit and two of them read the index, so they
are correctly out of scope; but writing the general claim would put a false sentence in the
gateway's own docstring, which is where the next author looks. Confined to the directory class.

TWO SMALLER CORRECTIONS. The plan's suite baseline had already gone stale (`3246` authored,
`3387` measured one day later), and since a count of a live growing population is exactly what the
repository's own live-artifact convention says must be re-derived, the bar is now re-derivation with
both numbers kept as dated history. And the gate carried a "STOP and report" directive for a scope
question, which the 2026-09-01 maintainer ruling specifically forbids: an out-of-scope edit is to be
made and JUSTIFIED at finalize. I kept the one legitimate stop (the prerequisite `dir_paths` block
being absent, meaning `hv9gar` is not in history) and removed the scope stop. My own first gate
rewrite then tripped `IPD-M108` by naming a hand-rolled terminal move; the linter caught it and it
is corrected to `aw ipd finalize` with conditional runner/executor ownership.

OQ-01 I RESOLVED RATHER THAN DEFERRING, on independently measured grounds (D-1). It carried
`- Owner: reviewer` and the author's recommendation was to keep the refusal. I agree, but not on the
author's grounds of deference to `hv9gar`'s prior review, because deferring to a prior review is how
a wrong decision becomes permanent. Three measurements decide it, and the second is new to this
review: the refusal already hands back a complete copy-pasteable file list at scale (F-05), so the
ergonomic cost is one paste; expansion would have to decide the deleted-directory case, where the
"contained files" are DELETIONS of paths the caller never named, which is precisely the silent
widening `AGENTS.md` forbids; and `_contained_files` enumerates BEFORE the `git add`, so a directory
is an open set in time as well as extent, and nothing in the gateway can close that window. The
ergonomic case for expansion is real and is recorded in the question rather than dismissed, with the
right shape for it named (an explicit opt-in expansion where the caller still names a closed set).

NO SPEC AMENDMENT IS OWED and I checked rather than accepting the claim: no `.spec.md` under
`.aw/records/specs/` governs `offer_commit`'s predicate or `commit_isolated`'s mirror loop, and E-04
WIDENS a refusal without weakening one. The cross-plan boundary with `c8ioct` is clean but needed
stating, since that plan is now `reviewed` and declares the same FILE: its surface is
`coordinator_worktree`, `land_worktree_commit` and `_finalize_transaction`, it names `commit_isolated`
as explicitly out of its scope, and this plan touches only `commit_isolated`, so the symbol sets are
disjoint and no dependency edge is owed.

Bare suite at review HEAD before any probe: `3387 passed, 2 skipped, 3 warnings in 60.27s`. Under
the E-02 prototype: `3387 passed, 2 skipped, 3 warnings in 61.46s`. Both production files restored
byte-identical and `git status --short` empty after every probe.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression (a success-reporting call that mutates a shared index) | Review measurement on a scratch fixture with `sub/a.md`, `sub/b.md`, `file.md` committed, then `shutil.rmtree(repo/'sub')` and `file.md` modified: `offer_commit(r, ['sub','file.md'], message='mixed dir del', assume_yes=True)` -> `STATUS: committed`, `MSG: committed 1 path(s) as b56a7c92... (1 path(s) had nothing to commit: sub)`, commit contents `M file.md` only, `git status --porcelain` afterwards `D  sub/a.md` / `D  sub/b.md`, `git diff --cached --name-status` `D sub/a.md` / `D sub/b.md`. The predicate is `dir_paths = [p for p in rel_paths if (repo_root / p).is_dir()]` in `git_commit_helper.offer_commit`, and `(repo_root/'sub').is_dir()` is `False` once the directory is emptied | **The whole plan keys on `Path.is_dir()`, which is FALSE for a directory whose files were all deleted or moved away, so the gateway's refusal SKIPS it and a MIXED call reports SUCCESS while leaving staged deletions in a shared index.** The `residue` rollback F-01 relies on cannot fire, because that arm runs only when `our_staged` is EMPTY and the accompanying file makes it non-empty (the all-directories variant DOES self-clean, which is why only the mixed shape leaks). This is a worse outcome than the preview mismatch the plan was filed to fix: `AGENTS.md` tells every agent to commit through `aw commit` precisely because it resets only its own paths, and emptying a directory by moving its contents out is the exact records-move shape `hv9gar` was written for | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | New F-11 records the full transcript including the self-cleaning all-directories variant and the deleted-plain-file control. New E-04 widens the predicate to "is or was a directory", deriving the second half from git (`_contained_files` already returns the deletions, measured), keeping the existing `STATUS_ERROR` and message, and requiring a NEGATIVE CONTROL so a deleted plain FILE still commits. New V-04 demands the pre-fix failure show the F-11 shape rather than a bare assertion error, and demands `git diff --cached` before/after as the load-bearing assertion. `- Scope:` widened to five changes, Goal and `- Concern:` restated, `Highest E allocated` raised to 05 |
| PR-702 | HIGH | IN-SCOPE | A. Correctness (a guard that reads complete and covers half the function) | Review prototype of E-03's `is_dir()`-keyed refusal, then re-measurement on a deleted-directory fixture: `commit_isolated(r, ['sub'], message='m')` STILL RAISES `IsADirectoryError: [Errno 21] Is a directory: <worktree>/sub`, traceback's final frame `dst.unlink()  # propagate a deletion`, NOT `shutil.copy2`. Mechanism: the shared tree lacks `sub/` so the guard misses, while the throwaway worktree is checked out at HEAD where `sub/` exists, making `dst.exists()` true | **E-03's guard does not fix what it claims, because `commit_isolated` has a SECOND raise site the plan never names.** The plan's F-03 identifies only the `shutil.copy2` arm and E-03's guard is keyed on the same filesystem predicate, so a deleted directory escapes both and crashes on the deletion branch instead. A guard whose unreachability the plan asks to be documented would then be documented as covering a case it does not cover | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-10 records both raise sites with the prototype re-measurement that proves E-03 alone is insufficient. New E-05 widens the same pre-worktree guard using `commit_lock._git` (which already delegates to the canonical runner inside the function body, so no upward import is added, preserving E-03's own cycle constraint), and requires the DELETION-ARM control so a deleted plain FILE still reaches `dst.unlink()`. New V-05 demands the pre-fix failure quote the `dst.unlink()` frame, since a failure at `shutil.copy2` would mean the fixture is not the shape the item is about. New conventions bullet records that `commit_isolated` deliberately supports a deleted path, citing `_content_hash`'s "load-bearing, not defensive" docstring |
| PR-703 | MEDIUM | IN-SCOPE | F. Honest documentation (a docstring claim wider than the behavior) | Review measurements, same path-set with and without `no_commit=True`. All-gitignored: preview `skipped: --no-commit requested` vs real `nothing-to-commit: ... every requested path is gitignored: ig` (also through `cli.main`). Unrelated-staged under `on_unrelated_staged="refuse"`: preview `skipped` vs real `refused-dirty: refusing to commit: unrelated staged changes present: tracked.md`. Non-interactive without `assume_yes`: preview `skipped: --no-commit requested` vs real `skipped: non-interactive; pass --commit to commit these changes` | **E-02 asks the docstring to record that the preview now agrees with the real run, and THREE other outcome classes still diverge under `no_commit`.** Each would need a DIFFERENT check moved ahead of the short-circuit and two of them read the index, so they are correctly out of scope; but the general claim would put a false sentence in the shared gateway's own docstring, which is exactly where the next author looks before changing this ordering | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-12 records all three divergences with measured statuses and messages. E-02 now forbids the general claim, requires the docstring to scope agreement to the directory class, and requires one sentence saying the short-circuit still precedes the other checks so a preview is not a general oracle. V-02 now demands that scoping sentence be quoted and FAILS the item on a general assertion. The scope check's "deliberately NOT widened" bullet names the three classes so a later executor does not absorb them as a free extension |
| PR-704 | MEDIUM | IN-SCOPE | G. Plan executability (a scope-stop directive the maintainer ruling forbids) | Plan gate and scope check as authored: "if E-02's relocation turns out to require touching the index snapshot or the locking (both over-scope above), STOP and report rather than proceeding" | **The plan instructs the executor to STOP over a scope question, which the 2026-09-01 maintainer ruling specifically forbids** (the correct requirement is that an out-of-scope edit be MADE and then JUSTIFIED, which `aw ipd finalize` already enforces via `--scope-reason`). The earlier mandate propagated this wording into 224 executed plans and it contradicts the work done to stop runs stranding unfinished turns | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The scope-stop converted to "report it and proceed under `--scope-reason` at finalize", with the ONE legitimate stop preserved and named explicitly: the prerequisite `dir_paths` block being ABSENT at the executor's HEAD, which means `hv9gar` is not in history and every E-item is premised on absent code. The gate restates the same distinction. (My own first rewrite of the gate then tripped `IPD-M108` by naming a hand-rolled `git mv` to `executed/`; the linter caught it and it now reads `aw ipd finalize` with conditional runner/executor ownership) |
| PR-705 | MEDIUM | IN-SCOPE | G. Plan executability (a live-population count used as an acceptance bar) | BARE `python3 -m pytest` at review HEAD `d194bdd0` before any edit: `3387 passed, 2 skipped, 3 warnings in 60.27s (0:01:00)`, 207 deselected. The plan's F-07 and its required-tests bullet both compare against `3246 passed, 2 skipped` | **The suite baseline is used as the comparison BAR and is already 141 tests stale after one day of merges.** The repository's own live-artifact convention requires a criterion counting a live population to state the property and re-derive at execution; a stale target invites an executor to read ordinary growth as unexplained divergence, or to "reconcile" it by guessing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14 records the re-measurement and names F-07's number as history. F-07 retitled to say the number is history and not a bar. The required-tests bullet now demands a BEFORE-first-edit run and an AFTER run, both pasted, with the difference accounted for by the tests added and any second-run-only failure treated as the executor's own. V-05 carries the same instruction and explicitly forbids comparing to either recorded count |
| PR-706 | LOW | IN-SCOPE | Evidence accuracy (a reachability claim measured false) | Plan E-03 as authored: "THIS ARM IS CURRENTLY UNREACHABLE FROM `offer_commit` AND THAT IS FINE; say so in the docstring". F-10's measurement: for a DELETED directory the gateway's refusal does not fire, so `commit_isolated` IS reached and raises | **E-03 asks for a flat "unreachable from `offer_commit`" sentence to be written into the shipped docstring, and review measured that claim false** for the deleted-directory case. It becomes true only once E-04 widens the gateway's predicate, so writing it as specified would put a false statement in the code and, worse, would justify a later reader deleting the guard as dead | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now forbids the flat claim, explains that E-04 is what makes it true, and specifies the honest wording ("defense for a direct caller, since `offer_commit` refuses a directory first"). V-03 requires the sentence be quoted AND that it not assert flat unreachability. The `- Concern:` field and the spec-sync section carry the same correction |
| PR-707 | LOW | IN-SCOPE | G. Plan executability (an under-specified cross-plan boundary and a thin test list) | `c8ioct` front matter reads `- Status: reviewed` and `- Scope-Paths: agent_workflows/commit_lock.py, agent_workflows/ipd_lifecycle.py, tests/test_commit_lock.py, tests/test_ipd_lifecycle_cli.py`; its `- Scope:` names `commit_isolated` as out of its scope. `tests/test_git_commit_helper.py` contains `test_untracked_destination_shape_commits_both_halves_when_naming_explicit_files` and `test_committed_outcome_reports_shortfall_for_unchanged_paths` | **The plan's deferral row treats `c8ioct` as touching a different area when both plans declare the same FILE, and its must-stay-green list names only two of the four existing tests that pin this surface.** The two omitted tests are exactly the move and shortfall shapes E-04's widened predicate could break, so the list was thinnest where the new risk is highest | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A conventions bullet now states the shared file explicitly, names both plans' disjoint SYMBOL sets, and records why no `- Item-Dependencies:` edge is owed (with the runner's worktree isolation and merge gate handling the textual overlap). The required-tests list raised to all FOUR pre-existing tests, with the reason the two added ones matter for E-04 stated. `commit_lock._git`'s in-body delegation recorded as a convention so E-05's git access is not mistaken for a new dependency |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 (`- Owner: reviewer`): should a directory argument be EXPANDED to its contained files rather than refused, overturning `hv9gar`'s reviewed OQ-01? | KEEP THE REFUSAL; resolve the question, and record the ergonomic case with the right shape for addressing it separately | (a) Overturn and adopt expansion, which is what backlog `5m43v9` asks for ("so a directory argument behaves as a caller reasonably expects"); (b) leave the question `open` for the maintainer; (c) uphold it purely by deference to `hv9gar`'s prior review, which is what the plan's own rationale did | Decided on measurement, deliberately NOT on deference, since deferring to a prior review is how a wrong decision becomes permanent. Three grounds, the second new to this review. (1) F-05 measured that the refusal already returns a complete copy-pasteable file list at scale (31 files, 434 chars, gitignored sibling correctly absent), so refusing costs one paste rather than a re-derivation. (2) PR-701's deleted-directory case shows expansion would have to expand into DELETIONS of paths that no longer exist and the caller never named, which is precisely the silent widening `AGENTS.md` forbids; refusal needs no such decision. (3) `_contained_files` enumerates BEFORE the `git add`, so a directory is an open set in TIME as well as extent and nothing in the gateway can close that window, which in a concurrently shared checkout means a commit whose contents were decided by a race. Option (b) was rejected because the question is answerable from repository evidence and the workflow forbids asking the human what the repository answers; option (a)'s ergonomic case is real and is preserved in the question with the correct shape named (an explicit opt-in expansion where the caller still names a closed set, as a separate plan) | yes |
| D-2 | PR-701/PR-702: the predicate must widen. Which predicate, given that a deleted plain FILE must keep working? | "`is_dir()` OR the path's changed-file set is non-empty and is not exactly `[p]` itself", derived from git, with the six-case table required as evidence and an executor free to substitute any shape that demonstrates the same table | (a) `git ls-files -- <p>` returning entries that are not exactly `[p]`, which is what E-05 uses inside `commit_lock`; (b) `git cat-file -t HEAD:<p> == tree`, which is clean but blind to an UNTRACKED new directory; (c) prescribe nothing and let the executor invent a predicate; (d) test whether the path has a trailing slash, which is what the caller typed | Measured across six cases rather than reasoned: live directory True, live file False, untracked-only directory True, DELETED directory True, DELETED plain file False, nonexistent False. `_contained_files` already computes the set with `git status --porcelain -z -uall` and already returns `['sub/a.md','sub/b.md']` for the emptied directory and `['file.md']` for a modified file, which is why the "not exactly `[p]`" clause is the part that keeps a FILE out. Option (b) fails the untracked-directory case, which `hv9gar`'s own `-uall` note exists for. Option (c) is how PR-701 happened in the first place and would leave the deleted-FILE regression risk unbounded. Option (d) is not a property of the repository at all: `_normalize` has already processed the path and the caller's typing is not evidence of anything. Option (a) is correct INSIDE `commit_lock`, where `_contained_files` is unreachable without a cycle, and is specified there for exactly that reason. The E-items specify the shape as a demonstrated table rather than as a mandated line, so an executor who finds a better predicate may use it | yes |
| D-3 | PR-701: should the widened predicate be a NEW refusal or reuse the existing `dir_paths` block? | REUSE the existing block; change only what it tests | (a) Add a second refusal specifically for the emptied-directory case, with its own message naming the deletions; (b) leave the existing block and add a post-`add` residue sweep that resets any staged path not in `rel_paths` | Option (b) is tempting because it would catch other residue shapes too, and it is wrong here: it acts AFTER staging, so it abandons the "a refused call mutates nothing" property that `hv9gar` established and that two existing tests assert by byte-comparing `git status --porcelain`; it also edges toward the "widen the commit to everything staged" shape the backlog item explicitly forbids. Option (a) doubles the surface and would emit two messages for one concept, and the existing message is already correct for the deleted case: `_contained_files` returns the deletions, which ARE the paths the caller should have named. Reusing the block keeps the status, the wording and the two pinning tests intact, which is what makes the change reviewable as a predicate change | yes |
| D-4 | PR-703: the three other `no_commit` divergences. Fix them here, or scope them out? | SCOPE THEM OUT and confine the docstring claim; do not file a carrier | (a) Fix all four classes in E-02 so the preview genuinely agrees with the real run; (b) fix them and say nothing, silently widening E-02; (c) file a backlog carrier for the remaining three | Option (a) is a different plan, not a bigger E-item: the gitignored check and the unrelated-staged check both READ THE INDEX (`_ignored_paths`, `_staged_paths`, the `pre_staged` snapshot), so moving them ahead of the short-circuit means a preview starts doing index work, which is a design decision about what a dry run is allowed to touch and is squarely in the "index snapshot" region this plan's own over-scope fence protects. Option (b) is the failure mode the fence exists to stop. Option (c) was weighed and declined because the three divergences are not agreed defects: the non-interactive one is arguably correct as-is (same status, more specific reason), so filing a carrier would assert a repository intent to change behavior that nobody has decided. Recording them in F-12 makes them discoverable to whoever does decide | yes |
| D-5 | PR-705: the stale suite baseline. Delete the number, or keep it as history? | KEEP both numbers as dated history and make the BAR re-derivation | (a) Delete F-07 and say nothing about the baseline; (b) update F-07 to `3387` and keep comparing against it | Option (b) rots again by the same mechanism, and faster than it looks: it went stale by 141 tests in ONE day, and this plan executes after further merges. Option (a) throws away a useful signal, since knowing the baseline was green on a stated date is what tells an executor a new failure is probably theirs. Recording the number as HISTORY while making the bar "run it before your first edit and after your last, and account for the difference" keeps the signal without the rot, which is how the repository handles other live-population counts and matches the same precedent applied in plan `hlv737`'s review | yes |
