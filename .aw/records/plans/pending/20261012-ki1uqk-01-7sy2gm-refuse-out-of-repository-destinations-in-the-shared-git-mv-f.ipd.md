# IPD: Refuse out-of-repository destinations in the shared git_mv fallback

- Date: 2026-10-12
- Kind: child
- Concern: `artifact_core.git_mv` runs `git mv`, and on ANY nonzero exit falls back to `shutil.move`. `git mv` exits nonzero both for an untracked source (the case the fallback exists for) and for a destination outside the repository (exit 128, `fatal: ... is outside repository`), so the helper overrides git's own refusal and moves a TRACKED file out of the tree, leaving the index listing the old path while the worktree shows an unstaged deletion. Re-measured in this lane (F-01, F-02). The helper also runs `(repo_root / dst_rel).parent.mkdir(parents=True, exist_ok=True)` BEFORE git is consulted, so an escaping destination creates directories outside the repository even when nothing is moved (F-03). `engine._git_mv` is a second, byte-for-byte equivalent copy of the same fallback (F-04).
- Scope: Add a BOUNDARY-CROSSING guard to `artifact_core.git_mv` that resolves both the source and the destination against the resolved repository root (the `relative_to`/`ValueError` idiom of `check_engine.resolve_evidence_artifact`) and raises a dedicated `ValueError` subclass BEFORE the `mkdir` and before any subprocess when exactly ONE of the two is inside the repository (or the destination is the root itself), so nothing on disk changes on refusal; a move whose source and destination are BOTH outside the repository (the companion and home records backends, F-07) keeps today's behavior, and the `shutil.move` fallback is unchanged for an in-repository untracked source. Make `engine._git_mv` delegate to the shared helper so the installer moves get the same guard. Add behavioral tests. NOT covered: other nonzero `git mv` failures for a tracked in-repository source (see Deferred).
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/engine.py, tests/test_artifact_core_git_mv_containment.py, tests/test_research_set_assign_date_containment.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ki1uqk
- Blocks-Release: next
- Set: ki1uqk
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7sy2gm
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record `.aw/records/reviews/20261012-ki1uqk-01-7sy2gm-refuse-out-of-repository-destinations-in-the-shared-git-mv-f.review.md`). PR-001 narrowed the guard to boundary-crossing moves after a review prototype showed the authored both-inside rule crashes `aw set` on a companion-backend repository (F-07, OQ-02).
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `ki1uqk`. Reproduced the escape via the helper itself against a nested scratch repo (F-01, F-02). Two findings the item does not state: the `mkdir` runs before git is consulted, so it creates directories outside the repo even on a refused move (F-03), and `engine._git_mv` is an independent copy of the same fallback rather than a caller of the shared helper (F-04), so fixing only `artifact_core` would leave the installer path open.
- 2026-10-12 draft (opencode): created.

## Goal

Make the toolkit's shared move primitive fail closed when either path resolves outside the repository, so git's own "outside repository" refusal can no longer be overridden by the untracked-file fallback, while untracked in-repository moves keep working exactly as today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Guard the shared helper

- [ ] E-01 In `agent_workflows/artifact_core.py`, add `class MoveOutsideRepositoryError(ValueError)` and, at the top of `git_mv` (before the `mkdir` and before the `git mv` subprocess), resolve `repo_root`, `repo_root / src_rel` and `repo_root / dst_rel` with `Path.resolve()` and classify each path as inside (`.relative_to(resolved_root)` succeeds and the path is not the root itself) or outside. Raise `MoveOutsideRepositoryError` naming both paths and the root when the source is inside and the destination is outside, when the source is outside and the destination is inside, or when the destination resolves to the root itself. When BOTH are outside, do NOT raise: that is the companion/home records backend, where `status_set._apply_transition` deliberately passes absolute record paths outside `repo_root` (F-07) and `aw set` works today; leave that path exactly as it is. Leave the existing `git mv` then `shutil.move` fallback unchanged for every non-refused move, and update the docstring to state the boundary contract and why the both-outside case is allowed.
  - Depends on: none
  - Expected outcome: a move from inside the repository to outside it, or from outside into it (relative `../` traversal, absolute path, or a symlinked parent that resolves outside), raises before anything on disk changes; an in-repository untracked source is still moved by the fallback; a both-outside move (companion records) still succeeds. A review prototype of exactly this rule refused an escaping tracked move with the source intact and no directory created, moved an untracked in-repo file, and let `aw set to-review` succeed on a companion-backend spec, while the authored "both must be inside" rule made the same `aw set` die with an uncaught `ValueError` ("is not in the subpath of").
  - Execution state: pending

- [ ] E-02 In `agent_workflows/engine.py`, replace the body of `engine._git_mv` with a delegation to `artifact_core.git_mv` (import locally or at module top; `artifact_core` imports nothing from `agent_workflows`, so no cycle), keeping the `_git_mv` name and signature so its two installer call sites are unchanged.
  - Depends on: E-01
  - Expected outcome: there is a single implementation of the fallback; installer moves get the guard.
  - Execution state: pending

### Task group 2: Tests and records

- [ ] E-03 Add `tests/test_artifact_core_git_mv_containment.py`, using a scratch git repo nested at least three directories below a `tempfile` base (so an escape lands somewhere writable, per the item's measurement note), exercising `artifact_core.git_mv` and `engine._git_mv` directly. Cases: (a) tracked source with `../` escaping destination raises `MoveOutsideRepositoryError`, the source is still on disk, `git status --short` is empty, and no file or directory was created anywhere under the temp base outside the repo; (b) absolute destination outside the repo raises the same way; (c) source outside the repo with an in-repo destination raises; (c2) source AND destination both outside the repo (a sibling `<repo>.aw/records` directory, the companion layout) do NOT raise and the file is moved; (d) destination under an in-repo symlink pointing outside raises (skip on platforms without symlink support); (e) untracked in-repo source is still moved into a new in-repo subdirectory (fallback preserved); (f) tracked in-repo move is staged as a rename (`git status --short` shows `R`); (g) END-TO-END: in a scratch repo whose `.aw/config/project.json` sets `{"records_backend": "companion"}` (with `HOME` and `XDG_CONFIG_HOME` pinned to the temp base), `aw specs new --title T --slug t --apply` then `aw set to-review <spec> --no-commit` driven through `cli.main` exits 0 and the spec lands under the companion `specs/to-review/` directory, pinning F-07 so a future tightening of the guard cannot silently break companion repos.
  - Depends on: E-01, E-02
  - Expected outcome: every case passes; cases (a), (b), (c) and (d) fail against the pre-change helper, and (c2), (e), (f) and (g) pass both before and after.
  - Execution state: pending

- [ ] E-04 In `tests/test_research_set_assign_date_containment.py`, update the docstring of `test_mechanism_git_mv_refusal_and_shutil_fallback` that calls the fallback "a deliberately unfixed live defect whose scope is carried by backlog item ki1uqk" so it no longer claims the defect is unfixed; the test body (driving raw `git mv` and asserting exit 128) is unchanged and still valid.
  - Depends on: E-01
  - Expected outcome: no test text claims the helper still swallows the refusal.
  - Execution state: pending

- [ ] E-05 Add a `CHANGELOG.md` entry under the pending 2.0.0 section describing the fix in user-facing terms (no em or en dashes).
  - Depends on: E-01
  - Expected outcome: the change is recorded for release notes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Containment idiom: `check_engine.resolve_evidence_artifact` resolves the candidate and calls `candidate.relative_to(repo_root)` inside `try/except ValueError`; `research_refs._refuse_uncontained_destination` (plan `plb8jx`) does the same and additionally refuses a destination equal to the root.
- `artifact_core` imports only the standard library (its `import` block: `datetime`, `functools`, `os`, `re`, `secrets`, `stat`, `subprocess`, `tempfile`, `pathlib`, `typing`), so `engine` may import it without a cycle.
- Suite command: bare `python3 -m pytest` (repo-local development contract in `AGENTS.md`).
- Tests must exercise behavior, not source text (GUIDING_PRINCIPLES P16).
- Commits through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | `artifact_core.git_mv(repo, "a/t.md", "a/../../ESC.md")` on a TRACKED file moves it outside the repo. | Measured 2026-10-12 in this lane against a scratch repo at `/tmp/opencode/ki1/n1/n2/n3/repo`: `tracked escaped: True`. |
| F-02 | The index and worktree then disagree. | Same run: `git status --short` printed ` D a/t.md`, `git ls-files` still printed `a/t.md`. Matches the backlog item's measurement. |
| F-03 | The helper's first statement is `(repo_root / dst_rel).parent.mkdir(parents=True, exist_ok=True)`, executed before `git mv`, so an escaping destination's parent directories are created outside the repo regardless of the outcome. The guard must therefore precede the `mkdir`, not merely the `shutil.move`. | Source of `artifact_core.git_mv`. |
| F-04 | `engine._git_mv` ("git mv with parent creation; falls back to filesystem move if needed") is a separate copy with the same `if result.returncode != 0: shutil.move(...)` arm, called from the installer's legacy-artifact relocation and tracked-file relocation loops. | Source of `engine._git_mv` and its two `_git_mv(repo, rel_src, rel_dst)` call sites. |
| F-05 | The untracked fallback is legitimately needed: the same run moved untracked `a/u.md` to `b/u.md` (`untracked moved in-repo: True`, `?? b/`). | Measured 2026-10-12. |
| F-07 | `git_mv` is ALSO called with BOTH paths outside `repo_root`, legitimately. `status_set._apply_transition` computes `rel_src`/`rel_dst` with `relative_to(repo_root)` and, on `ValueError`, falls back to the ABSOLUTE record paths; for the companion backend those resolve under the sibling `<repo>.aw/records/` (`project_context` `records_root = ... os.path.join(eff_companion_dir, "records")`, default `f"{repo_abs}.aw"`). | Measured at review HEAD `1bcf4518f`: with `{"records_backend":"companion"}`, `record_producers.resolve_record_path("backlog", ...)` returned `<base>/repo.aw/records/backlog` (inside repo: False); `aw set to-review <spec>` called `git_mv(<repo>, "<base>/repo.aw/records/specs/draft/...", "<base>/repo.aw/records/specs/to-review/...")` and exited 0. |
| F-06 | Callers of the shared helper: `research_refs._apply_renames` (via `_git_mv = _core.git_mv`), `research_archive.apply_moves` (via `RF._git_mv`), `plans_refs`, `plans_archive`, `artifact_rename` (two sites), `status_set`. All but `status_set` compute both paths with `relative_to(repo_root)` and so pass only in-repo paths; `status_set` additionally passes both-outside absolute paths for companion/home records (F-07); `research_refs` already refuses uncontained destinations upstream (`_refuse_uncontained_destination`). None wraps the call in `except ValueError`, so a raised refusal surfaces as an error rather than being silently absorbed; for every in-repo destination behavior is unchanged. | `grep -n "git_mv(" agent_workflows/*.py`. |

## Proposed changes (ordered, validatable)

1. Guard in `artifact_core.git_mv` before any side effect (E-01, validated by V-01 and V-03).
2. `engine._git_mv` delegates to the guarded helper (E-02, V-02).
3. Behavioral tests for escape, absolute, source escape, symlink escape, and preserved in-repo moves (E-03, V-03).
4. Stale docstring correction (E-04, V-04) and changelog (E-05, V-05).

## Deferred / out of scope (with reason)

- A TRACKED in-repository source whose `git mv` fails for another reason (for example an existing destination) still falls through to `shutil.move`. That is a different defect shape with different callers' expectations (some check `exists()` first); narrowing it is a broader behavior change than this item asks for and is not measured here. Not filed as a new item in this authoring turn; the reviewer may request one.
  - Carrier-Declined: no harm is measured for this shape (no review measurement shows a caller reaching a tracked in-repo `git mv` failure; the installer's legacy relocation, for one, pre-checks `(repo / rel_dst).exists()` and skips), so filing would schedule unmeasured work; the review report surfaces it to the maintainer for a decision.
- The detection blindness (`index --check` reporting clean after a record leaves the tree) is owned elsewhere, as recorded in plan `plb8jx`.
  - Carrier-Declined: executed plan `plb8jx` already declined a carrier for the detection half with a recorded rationale (its Deferred section), and this plan's guard removes the out-of-tree write that the blindness would hide, so nothing new is owed here.

## Scope check

- Over-scope: none. E-02 is in scope because the backlog item names "`engine`'s installer moves" as a consumer of this fallback.
- Under-scope: none known; every caller listed in F-06 benefits from the single guarded helper without per-caller edits, and case (g) pins the both-outside companion path (F-07) the authored guard would have broken.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_artifact_core_git_mv_containment.py tests/test_research_set_assign_date_containment.py` passes (V-03, V-04).
- Bare `python3 -m pytest` passes with no new failures, run before the terminal transition per the execution gate below.
- `aw ipd lint` on this plan conforms at `pre-transition`.

## Spec / documentation sync

N/A for specs: no spec describes the `git_mv` fallback contract (the helper's docstring is the contract and is updated in E-01). `CHANGELOG.md` is updated in E-05.

## Open questions

### OQ-01: Raise versus return an error from git_mv

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Raise a `ValueError` subclass. `git_mv` returns `None` and every caller ignores its result (F-06), so a return-code channel would be silently dropped; raising fails closed, and subclassing `ValueError` matches the idiom the containment checks already use. A raised refusal surfaces as an uncaught exception in the CLI verbs (no caller catches it), which is acceptable for a case that only a caller BUG can produce once the verbs refuse bad destinations upstream; it is not reachable through any normal companion/home path because the both-outside case is allowed (F-07).

### OQ-02: Refuse any out-of-repository path, or only a move that crosses the boundary?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: Only a boundary crossing (revised at review, PR-001). The authored "both paths must resolve inside the repo" rule breaks `aw set` for any repository using the companion (or home) records backend, because `status_set._apply_transition` passes both-outside absolute paths there (F-07). DEMONSTRATED at review with a prototype: the authored rule made `aw set to-review` on a companion-backend spec raise an uncaught `ValueError` and leave the spec in `draft/`, while the boundary-crossing rule let the same transition succeed and still refused the measured escape (`a/t.md` -> `a/../../../ESC/x.md`) with the source intact and no directory created. The defect the item names (git's refusal overridden for an in-repo source, F-01/F-02) is fully closed by the boundary rule, because every escaping move it describes starts inside the repository.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` of `agent_workflows/artifact_core.py` showing the guard precedes both the `mkdir` and the `git mv` subprocess, plus pasted output of a direct `python3 -c` call of `artifact_core.git_mv` against a nested scratch repo with an escaping destination showing the `MoveOutsideRepositoryError` message and that the source file still exists (code path: `artifact_core.git_mv`, created by E-01).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` of `engine._git_mv` showing delegation to `artifact_core.git_mv`, and the pasted passing output of the E-03 test case that calls `engine._git_mv` with an escaping destination.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the actual runner output of `python3 -m pytest -o addopts="" -q tests/test_artifact_core_git_mv_containment.py` showing all cases passed, AND pasted output showing cases (a), (b), (c) and (d) FAIL, and cases (c2), (e), (f) and (g) PASS, when E-01's guard is temporarily reverted (by copying the new test file into a scratch `git worktree add` of the pre-change commit and running it there; never stash or revert the working checkout), proving the tests discriminate.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff` of `tests/test_research_set_assign_date_containment.py` (docstring only) and the passing runner output of that file.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `git diff` of `CHANGELOG.md` and the output of a search confirming the added lines contain no em or en dash characters.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). All open questions are resolved (OQ-02 at review). Begin with `aw ipd begin`. Follow the agent execution contract in `AGENTS.md`: commit only the Scope-Paths files through `aw commit 7sy2gm -- <paths>` and verify the staged set with `git diff --cached --name-only` first; never `git add -A`, never push; paste the ACTUAL runner output for every test claim; run the full bare suite (`python3 -m pytest`) before the terminal transition and, for any failure, re-run that selection at the unmodified base commit and state whether it is pre-existing. `- Scope-Paths:` is a declaration, not a stop condition: an out-of-scope edit the work genuinely needs is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. Do not claim done while any `V-*` is pending. Every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms before the plan moves to `executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize; executed by hand, the executor runs `aw ipd finalize`. Never hand-roll a `git mv` of this plan. Backlog `ki1uqk` is already `graduated`; this plan inherits its `- Blocks-Release: next`, and the item closes `done` through the From-Backlog handoff once this plan is executed.
