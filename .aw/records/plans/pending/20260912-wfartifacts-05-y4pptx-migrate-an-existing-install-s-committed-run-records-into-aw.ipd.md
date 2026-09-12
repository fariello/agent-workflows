# IPD: Migrate an existing install's committed run records into .aw/workflow-artifacts

- Date: 2026-09-12
- Kind: child
- Concern: 29 REPOS ON ONE MACHINE ALREADY CARRY THE RETIRED LAYOUT, AND SOME OF IT IS COMMITTED. Measured 2026-09-12: 29 repos under the maintainer's `VC/` tree have a repo-root `workflow-artifacts/`. Most track only the stray README, but REPO-A tracks 11 files across two assess runs (`assess-bugs/<RUN_ID>/`, `assess-testing/<RUN_ID>/`, each with `decisions.md`, `evidence.md`, `findings.csv`, `ipd-link.md`, `report.md`) and REPO-B tracks 3 including two advise session summaries. The two repositories are deliberately NOT named here: they are the maintainer's private repos, and a plan is a public artifact. Orders 01 through 04 fix what a FRESH install produces and change nothing for these.
  THE EXISTING TOOL DOES NOT DO THIS JOB. `tools/untrack-workflow-artifacts.py` UNTRACKS IN PLACE: it removes index entries, keeps the working tree, and writes an ignore rule for the repo-root path. It never moves anything under `.aw/`, and it is not wired into `aw install` (`grep -rn 'untrack_workflow_artifacts' agent_workflows/` -> nothing). So it leaves the double home Order 07 existed to end, and it must not be mistaken for this deliverable.
  THIS IS THE ONLY CHILD THAT TOUCHES A USER'S COMMITTED HISTORY, which is why it is last and why its bar is highest. Deleting a user's committed run records would destroy review history they chose to keep; silently committing a relocation into a tracked path would publish local context (D92). Both failure modes are worse than leaving the old directory alone, so the migration must be conservative and must refuse rather than guess.
- Scope: On `aw install`, relocate an existing repo's run records from the repo-root `workflow-artifacts/` into `.aw/workflow-artifacts/`, preserving committed history with `git mv`, never deleting user content, and refusing rather than guessing when the situation is ambiguous. EXCLUDES the fresh-install layout (Orders 01, 02), prose (Orders 03, 04), and any change to `tools/untrack-workflow-artifacts.py`'s in-place behavior, which stays available for a user who wants only to untrack.
- Scope-Paths: agent_workflows/engine.py, tests/test_engine_install.py
- Item-Dependencies: none
- Status: reviewed
- Priority: high
- Work-Kind: bug
- Readiness: go-pending-approval
- Blocks-Release: next
- From-Backlog: o9inwt
- Set: wfartifacts
- Order: 5
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: y4pptx

## Workflow history
- 2026-09-12 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 all FIXED in place, none deferred, none REPLAN. aw ipd lint conformed at --phase author before semantic review and at --phase review-finalize after every revision. THE REVIEW RE-MEASURED EVERY NUMERIC CLAIM RATHER THAN TRUSTING IT, which is what produced the findings: the 86 occurrences, the 0 prefixed, the 29 repos, the 11-file and 3-file affected repos, the 170 reviews, the 42/10 test refs and all four engine.py citations re-verified EXACTLY, but the file count was 27 and is 25 (grep -rl without --include matched three __pycache__ binaries) and two per-file figures mixed grep -c lines with grep -o occurrences (18/11 vs the true 20/12). PR-002 found the riskiest gap: Order 05 described a MOVE where both trees are populated and three workflow names collide, so it is a MERGE; no RUN_ID collides because run ids are timestamps, but that is the data's property not the design's, so a merge test is now mandatory. PR-004 NARROWED Order 04 after finding the shipped agents-README.md template is already CORRECT and a fresh install receives it, so the wrong .aw/records/README.md is local drift from the Order 11 migration and the template must NOT be edited. PR-003 named the five tests that assert the defect. Also added, per the maintainer's instruction: an isolated-worktree clause to all six execution contracts, recording that aw oc run / aw agy run default isolate_worktree True and that a hand run must allocate its own lane. Typed review records written for all six. No product code was modified by this review. HUMAN APPROVAL IS STILL REQUIRED.
- 2026-09-12 to-review (aw set): Authored as Order 07 delivery (Set wfartifacts) from backlog o9inwt: the spec's run-scratch relocation was implemented in this repo but never delivered to the shipped surface (86 stale references, installer still creating a repo-root dir with a 'DO NOT gitignore' README, 29 repos affected). Review-ready: no TODO placeholders, E/V bijection complete, every V-item demands pasted evidence.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Carry an existing repo's run records to the one real home without losing history and without publishing local context.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: relocate conservatively, and refuse when unsure

- [ ] E-01 WRITE THE MIGRATION AS A SEPARATE, TESTABLE FUNCTION BEFORE WIRING IT INTO INSTALL, taking a repo root and returning what it did.
  THREE CASES, EACH DISTINCT: (a) files TRACKED under the repo-root path -> `git mv` into `.aw/workflow-artifacts/` so history follows; (b) files present but UNTRACKED (already ignored, or never committed) -> a plain filesystem move, since git has nothing to preserve; (c) the stray README ALONE and nothing else -> remove it rather than relocate it, because Order 04 replaces its content and a copy of the retired prose is exactly what should not survive.
  PRESERVE THE RUN-DIRECTORY STRUCTURE: `workflow-artifacts/assess-bugs/20260726-115243/report.md` must land at `.aw/workflow-artifacts/assess-bugs/20260726-115243/report.md`. Flattening or renaming a `<RUN_ID>` would break the `<workflow>/<RUN_ID>/` shape Order 07 specified and make the records harder to read than leaving them alone.
  THE DESTINATION IS OFTEN ALREADY POPULATED, SO THIS IS A MERGE AND NOT A MOVE (F-7, found at review). Measured in THIS repository: `workflow-artifacts/` holds 5 entries and `.aw/workflow-artifacts/` holds 10, and three workflow names exist in BOTH (`assess-bugs`, `assess-documentation`, `release-review`). A move that assumes an empty or absent destination will either fail on the existing directory or, worse, replace it. MERGE PER `<workflow>/<RUN_ID>/` LEAF: create the workflow directory if absent, then move each run directory into it.
  RUN-ID COLLISION IS UNLIKELY BUT NOT IMPOSSIBLE, AND THE REASON MATTERS. Measured here, ZERO `<RUN_ID>`s collide across those three shared workflows, because a `<RUN_ID>` is a timestamp (`20260817-135746`) and two runs of the same workflow in the same second is the only way to collide. So the common case is a clean merge; do NOT conclude from that measurement that collision handling is unnecessary, since the refusal rule below is what makes the rare case safe rather than destructive.
  REFUSE, DO NOT GUESS, when the destination already holds a file at the same relative path with different bytes: report it and leave BOTH in place. A silent overwrite of a run record is unrecoverable for the user.
  DO NOT DELETE USER CONTENT IN ANY CASE except (c), and state that as an invariant in the code.
  - Depends on: none
  - Expected outcome: a standalone function handling the tracked, untracked, and README-only cases, MERGING into an already-populated destination per `<workflow>/<RUN_ID>/` leaf, preserving that structure, refusing on a conflicting destination, and never deleting user content outside case (c).
  - Execution state: pending

- [ ] E-02 WIRE IT INTO THE INSTALL PATH SO IT REACHES EVERY ENTRY POINT, NOT JUST ONE.
  CALL IT FROM `install_into_repo`, the SHARED CHOKEPOINT. `emit_layout_artifacts`'s docstring records the measured reason: `install_into_repo` is reached by `aw install` via `engine.run()`, by `aw setup` via `cli._run_setup` -> `cli._install_one`, and by library callers, so wiring into `run()` instead would leave `aw setup` silently doing nothing.
  REPORT WHAT MOVED in the installer's normal output, as a migration and not as an install. A user whose committed files were relocated must see that it happened; a silent `git mv` of tracked content is the kind of surprise that erodes trust in the installer.
  THE RELOCATED FILES MUST END UP IGNORED, which is why this depends on Order 02 having landed. Verify in the test rather than assuming: a migration that moves files into a path nothing ignores has converted a visible problem into an invisible one.
  RESPECT `dry_run`: report what WOULD move and touch nothing.
  - Depends on: E-01
  - Expected outcome: the migration runs from `install_into_repo` on every entry point, reports what it moved, honors dry-run, and leaves the relocated files ignored.
  - Execution state: pending

- [ ] E-03 TEST THE THREE CASES PLUS THE REFUSAL, WITH REAL GIT AND REAL COMMITTED HISTORY.
  THE TRACKED CASE IS THE ONE THAT MATTERS MOST: seed a repo, COMMIT a run record under the repo-root path, run the install, then assert the file is at the new path AND that `git log --follow` still reaches the original commit. History preservation is the claim; asserting only the new location would pass for a copy-and-delete that lost it.
  ALSO ASSERT NOTHING WAS LOST: compare the set of run-record relative paths before and after, and assert equality modulo the prefix. A test that checks one file cannot catch a partial move.
  COVER THE REFUSAL with a same-path/different-bytes conflict, asserting both files still exist and the run reported rather than overwrote.
  RUN THE SUITE BARE and compare the failure SET.
  - Depends on: E-02
  - Expected outcome: passing tests for tracked (with `git log --follow` proof), untracked, README-only, and the refusal case, plus a before/after path-set equality check and an empty bare-suite failure-set delta.
  - Execution state: pending

- [ ] E-04 DECIDE AND RECORD WHAT HAPPENS TO RUN RECORDS AN AGENT ALREADY MIS-RELOCATED, rather than leaving them stranded.
  THE OBSERVED CASE: after the maintainer raised this, a repo agent moved run records into `.aw/records/reviews/untracked/`. That is a TRACKED typed tree's path with an `untracked/` lane bolted on, not the run-scratch home, and `records/reviews/` holds 170 `.review.md` artifacts written by `/plan-review`.
  DO NOT SILENTLY SWEEP IT UP. Whether the migration should also relocate from that path is a judgement about someone else's repo state; investigate whether it exists anywhere reachable, and either handle it explicitly with a stated rule or REPORT it for a human. Say which you chose and why.
  IF YOU HANDLE IT, the same invariants apply: preserve structure, never delete, refuse on conflict.
  - Depends on: E-03
  - Expected outcome: an explicit, recorded decision on mis-relocated records, either implemented with the same invariants or reported for a human with the reason it was not automated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ORDER 07 IS THE AUTHORITY AND IT IS ALREADY `implemented`: spec `20260817-2124-01-records-taxonomy-cleanup` (`u7xtni`), history line "run-artifacts -> `.aw/workflow-artifacts/`". This Set DELIVERS that decision; it does not revisit it.
- RUN SCRATCH IS UNTRACKED BECAUSE OF D92: run records carry local context, absolute home paths and session detail, so committing them publishes machine identity into permanent history. That is the reason, and it is why "just track it" is not an option.
- THIS REPO'S ROOT `.gitignore:62-68` ALREADY ENCODES THE TARGET STATE and is the best statement of intent in the tree, but it is NOT shipped: a target repo receives the framework-owned `.aw/.gitignore` instead. Never cite the root file as evidence that a target repo is protected.
- PATTERNS IN `.aw/.gitignore` ARE `.aw/`-RELATIVE AND MUST BE ANCHORED. The template's own `/inbox/` comment records the measured reason: a bare `inbox/` matched at any depth and silently swallowed the TRACKED `records/comms/shared/inbox/` lane, breaking `aw install`.
- `_ensure_aw_gitignore` IS THE ONLY PATH THAT REACHES AN ALREADY-INSTALLED REPO, because a repo that already has a `.aw/.gitignore` never re-reads the template. Every prior addition in that function carries a comment saying exactly this.
- `install_into_repo` IS THE SHARED CHOKEPOINT for every entry point (`aw install` via `engine.run()`, `aw setup` via `cli._run_setup` -> `cli._install_one`, and library callers). Wiring into `run()` reaches only one of them.
- `.aw/records/` IS TRACKED DURABLE RECORDS, NOT SCRATCH: `records/reviews/` alone holds 170 typed `.review.md` files. An agent already mistook it for the scratch home and moved run records into `.aw/records/reviews/untracked/`.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | committed run records exist in user repos | One repo tracks 11 files across two assess runs; another tracks 3 including two advise session summaries. Names omitted (private repos; a plan is a public artifact). | `git ls-files workflow-artifacts` in each |
| F-2 | HIGH | 29 repos carry the retired layout | measured across the maintainer's `VC/` tree; Orders 01-04 change nothing for any of them. | per-repo directory check |
| F-3 | HIGH | the existing tool does NOT do this job | `tools/untrack-workflow-artifacts.py` untracks IN PLACE, keeps the working tree, writes a repo-root ignore rule, moves nothing under `.aw/`, and has no caller in `agent_workflows/`. | the tool; grep for callers |
| F-4 | HIGH | this is the only child touching committed history | so deletion is unrecoverable and a silent relocation into a tracked path would publish local context (D92). | scope of the change |
| F-5 | MEDIUM | most repos hold only the stray README | so the common case is a removal, not a relocation, and treating every repo as a migration would leave copies of the retired prose behind. | the same per-repo scan |
| F-6 | MEDIUM | an agent already mis-relocated records | into `.aw/records/reviews/untracked/`, a TRACKED typed tree rather than the scratch home. | maintainer report 2026-09-12 |
| F-7 | HIGH | THE DESTINATION IS OFTEN ALREADY POPULATED, so this is a MERGE and the plan described only a move | In this repository `workflow-artifacts/` has 5 entries and `.aw/workflow-artifacts/` has 10, sharing three workflow names (`assess-bugs`, `assess-documentation`, `release-review`). An implementation assuming an absent destination fails on the existing directory or replaces it. ZERO `<RUN_ID>`s collide because run ids are timestamps, so the merge itself is clean here. | `ls` + `comm` per workflow, at review |

## Proposed changes (ordered, validatable)

1. Write the migration as a standalone function handling tracked / untracked / README-only, preserving `<workflow>/<RUN_ID>/`, refusing on conflict, never deleting (E-01).
2. Wire it into `install_into_repo`, report what moved, honor dry-run (E-02).
3. Test all three cases plus the refusal, with real git and `git log --follow` proof (E-03).
4. Decide and record what happens to already-mis-relocated records (E-04).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan does not change the fresh-install layout (Orders 01, 02), any prose (Orders 03, 04), or `tools/untrack-workflow-artifacts.py`'s in-place behavior. It does not rewrite git history (no filter-branch); it relocates files in a new commit. It does not touch repos other than the one being installed into.

## Required tests / validation

- THE TRACKED CASE WITH HISTORY PROOF: a COMMITTED repo-root run record is relocated and `git log --follow` still reaches its original commit. Asserting only the new location would pass for a copy-and-delete that lost history.
- THE MERGE CASE, which is the common case rather than an edge (F-7): a destination that ALREADY holds other runs of the same workflow keeps them, and gains the relocated one. Seed both trees with different `<RUN_ID>`s under one workflow name and assert the union survives.
- NOTHING LOST: the before/after set of run-record relative paths is equal modulo the prefix.
- THE UNTRACKED CASE: a plain move, no git operation attempted.
- THE README-ONLY CASE: removed rather than relocated, since Order 04 replaces its content.
- THE REFUSAL: a same-path/different-bytes destination leaves BOTH files in place and is reported, never overwritten.
- DRY-RUN touches nothing, proven by identical `git status` before and after.
- RELOCATED FILES ARE IGNORED, proven with `git check-ignore -v` attributed to `.aw/.gitignore`.
- `python3 -m pytest` BARE, failure-SET delta empty.

## Spec / documentation sync

No spec change: Order 07 specified the destination and this plan carries existing content to it.

THE INSTALLER'S OUTPUT IS THE USER-FACING DOCUMENTATION of this behavior, and E-02 requires it report what moved. A `git mv` of a user's committed files that happens silently is the kind of surprise that makes an installer untrustworthy, so the reporting is a deliverable rather than a nicety.

## Open questions

### OQ-01: Should the migration run on every install, or only when it has something to do?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: ONLY WHEN IT HAS SOMETHING TO DO, AND SILENTLY OTHERWISE. Resolved from the surrounding code's convention rather than asked: every other back-fill in `engine.py` (the layout artifacts, the four INDEX manifests, the gitignore patterns) is written to be a cheap no-op on an already-correct repo and to print nothing in that case, because an installer that narrates work it did not do trains users to ignore its output. So: detect the repo-root path, return immediately when it is absent, and report ONLY when files actually moved. NOT BLOCKING: E-02 already requires reporting what moved, which implies silence when nothing did.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the function and quote the invariant comment stating it never deletes user content outside the README-only case. Show the three cases are distinguished in code, and quote the refusal branch. Paste a worked example of a preserved path mapping (`workflow-artifacts/assess-bugs/<RUN_ID>/report.md` -> `.aw/workflow-artifacts/assess-bugs/<RUN_ID>/report.md`). Quote the code that MERGES into an existing destination workflow directory rather than replacing or failing on it (F-7); an implementation that only handles an absent destination is a FAILED validation, since the populated case is the common one.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff showing the call site is inside `install_into_repo`, plus the installer output from a real migration run showing what moved. Paste a dry-run showing it reports and touches nothing (prove with `git status` before and after being identical). Paste `git check-ignore -v` on a relocated file showing it is ignored by `.aw/.gitignore`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the passing tests. For the tracked case, paste the ACTUAL `git log --follow` output for a relocated file showing it reaches the pre-migration commit; absence of that output is a FAILED validation even if the file exists at the new path. Paste the before/after path-set comparison showing equality modulo the prefix. Paste the MERGE case showing a pre-existing destination run SURVIVED alongside the relocated one. Paste the refusal case showing both files still present and the reported message. Then paste BARE `python3 -m pytest` summary lines before and after with the failure-SET delta stated.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: state the decision explicitly and quote where it is recorded. If implemented, paste the passing test and show the same invariants hold; if reported instead, paste the report text and the evidence of whether such a path exists anywhere reachable. "Not applicable" is acceptable ONLY with pasted evidence that no such path exists.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

ISOLATE THE WORKTREE (maintainer instruction 2026-09-12). If you run this plan through `aw oc run` / `aw agy run` you already have this: `isolate_worktree` DEFAULTS TRUE (`oc_runipd.py:3048`, `:6106`; `agy_runipd.py:2055`, `:3254`), so the agent turn, verifier and finalize happen on an `aw/lane/<id6>` branch in a fresh worktree while the main tree stays untouched, and changes return through the merge-and-revalidate gate. Do NOT pass `--no-isolate-worktree`.
IF YOU EXECUTE BY HAND, ALLOCATE ONE YOURSELF rather than editing the main checkout: `git worktree add ../aw-lane-<id6> -b aw/lane/<id6>`, work and commit there, then merge back. THIS SET MAKES THAT PARTICULARLY IMPORTANT for two measured reasons. FIRST, Order 03 rewrites 25 shipped files and Orders 01/02/05 all edit `engine.py`, so a half-finished hand run leaves the installer and the shipped bodies DISAGREEING, which is the exact defect state this Set exists to end. SECOND, this is a SHARED CHECKOUT with concurrent agents and humans, and an isolated lane is what keeps a partial rewrite of `.aw/system/workflows/` from being visible to (or swept into a commit by) someone else mid-run.
NOTE THE ONE THING ISOLATION DOES NOT COVER: Order 05 must be TESTED against scratch clones, never against a user's real repository. A worktree isolates THIS repo's tree; it does nothing to protect the OTHER repositories on the machine whose committed run records that plan is designed to move (the two counted in Order 05's findings).

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
