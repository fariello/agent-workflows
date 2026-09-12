# IPD: Ignore .aw/workflow-artifacts from the framework-owned gitignore, template and back-fill

- Date: 2026-09-12
- Kind: child
- Concern: `.aw/workflow-artifacts/` IS NOT IGNORED IN ANY TARGET REPO, so the moment anything writes run scratch there it becomes tracked working material carrying local context, absolute home paths and session detail (D92). This repo's own root `.gitignore:68` ignores it, but that file is NOT shipped; a target repo gets the framework-owned `.aw/.gitignore`, and `grep -n 'workflow-artifacts' agent_workflows/engine.py` shows the template (`_AW_GITIGNORE_TEMPLATE`, `engine.py:4321+`) has NO entry for it.
  THIS MUST LAND FIRST IN THE SET. Orders 01 and 03 both make the new path real (one by writing there, the other by TELLING agents it is "gitignored by default"), so landing either before this one opens a window where run scratch is written to a path nothing ignores, which is the exact failure this Set exists to end.
  THE BACK-FILL IS THE HALF THAT MATTERS FOR EXISTING REPOS, and it is easy to miss: `_ensure_aw_gitignore` (`engine.py:5397`) is the ONLY code path that reaches an ALREADY-INSTALLED repo, because a repo that already has a `.aw/.gitignore` never re-reads the template. Every prior pattern addition in that function carries a comment saying exactly this (`records/history.jsonl`, `system/layout.json`, the four `INDEX.*` manifests), each added after the template-only version silently missed installed repos.
- Scope: Add ONE anchored pattern for the run-scratch tree to the framework-owned `.aw/.gitignore`, in BOTH `_AW_GITIGNORE_TEMPLATE` (fresh installs) and the `_ensure_aw_gitignore` back-fill list (already-installed repos), with a comment recording why it is untracked. Re-sync this repo's own `.aw/.gitignore` to the template, which an existing guard test requires. EXCLUDES any change to the repo-root `workflow-artifacts/` path (Order 01), any change to a user's root `.gitignore`, and any file movement (Order 05).
- Scope-Paths: agent_workflows/engine.py, .aw/.gitignore, tests/test_engine_install.py
- Item-Dependencies: none
- Status: reviewed
- Priority: high
- Work-Kind: bug
- Readiness: go-pending-approval
- Blocks-Release: next
- From-Backlog: o9inwt
- Set: wfartifacts
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: vh14ku

## Workflow history
- 2026-09-12 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 all FIXED in place, none deferred, none REPLAN. aw ipd lint conformed at --phase author before semantic review and at --phase review-finalize after every revision. THE REVIEW RE-MEASURED EVERY NUMERIC CLAIM RATHER THAN TRUSTING IT, which is what produced the findings: the 86 occurrences, the 0 prefixed, the 29 repos, the 11-file and 3-file affected repos, the 170 reviews, the 42/10 test refs and all four engine.py citations re-verified EXACTLY, but the file count was 27 and is 25 (grep -rl without --include matched three __pycache__ binaries) and two per-file figures mixed grep -c lines with grep -o occurrences (18/11 vs the true 20/12). PR-002 found the riskiest gap: Order 05 described a MOVE where both trees are populated and three workflow names collide, so it is a MERGE; no RUN_ID collides because run ids are timestamps, but that is the data's property not the design's, so a merge test is now mandatory. PR-004 NARROWED Order 04 after finding the shipped agents-README.md template is already CORRECT and a fresh install receives it, so the wrong .aw/records/README.md is local drift from the Order 11 migration and the template must NOT be edited. PR-003 named the five tests that assert the defect. Also added, per the maintainer's instruction: an isolated-worktree clause to all six execution contracts, recording that aw oc run / aw agy run default isolate_worktree True and that a hand run must allocate its own lane. Typed review records written for all six. No product code was modified by this review. HUMAN APPROVAL IS STILL REQUIRED.
- 2026-09-12 to-review (aw set): Authored as Order 07 delivery (Set wfartifacts) from backlog o9inwt: the spec's run-scratch relocation was implemented in this repo but never delivered to the shipped surface (86 stale references, installer still creating a repo-root dir with a 'DO NOT gitignore' README, 29 repos affected). Review-ready: no TODO placeholders, E/V bijection complete, every V-item demands pasted evidence.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the run-scratch home ignored everywhere before anything starts writing to it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: ignore the run-scratch tree, on both code paths

- [ ] E-01 ADD THE PATTERN TO `_AW_GITIGNORE_TEMPLATE` AND TO THE `_ensure_aw_gitignore` BACK-FILL LIST, as one anchored line with a comment stating why.
  USE THE ANCHORED FORM `/workflow-artifacts/`, not a bare `workflow-artifacts/`. The template's own `/inbox/` comment records the measured reason: a bare pattern matches a directory of that name at ANY depth, and the bare `inbox/` form once silently swallowed the TRACKED `records/comms/shared/inbox/` lane and broke `aw install` on a fresh repo. Patterns in this file are `.aw/`-relative, so `/workflow-artifacts/` resolves to `.aw/workflow-artifacts/` exactly.
  MATCH THE EXISTING BACK-FILL SHAPE rather than inventing one: a line-anchored `re.search(r"(?m)^{0}[ \t]*$", ...)` presence test then an append, which is what the `system/layout.json` and `records/plans/INDEX.json` additions already do. That shape is what makes repeated calls idempotent, and `_ensure_aw_gitignore` is called several times per install.
  RECORD THE REASON IN THE COMMENT, since this file is read by users: run records hold local context, absolute home paths and session detail (D92), and Order 07 (spec `20260817-2124-01`) gave them one untracked home. A future reader who does not know that will "helpfully" remove the line.
  - Depends on: none
  - Expected outcome: `/workflow-artifacts/` present in the template AND in the back-fill list, appended idempotently, with a comment citing D92 and Order 07.
  - Execution state: pending

- [ ] E-02 RE-SYNC THIS REPO'S OWN `.aw/.gitignore` TO THE TEMPLATE, because a guard test requires them byte-identical and will otherwise fail.
  THE TEST IS `tests/test_engine_install.py::ManifestIndexGitignoreTests::test_template_and_this_repos_own_gitignore_agree`, which exists so the next install does not re-diff this repo against its own template. It caught exactly this omission on 2026-09-12 during an unrelated pattern addition, so treat it as the mechanism rather than a surprise.
  NOTE THE ROOT `.gitignore` ALREADY IGNORES `.aw/workflow-artifacts/` (line 68) and is a DIFFERENT file that this plan does not touch; ignoring the path twice from two files is harmless and the root entry is what protects this repo today.
  - Depends on: E-01
  - Expected outcome: `.aw/.gitignore` byte-identical to `_AW_GITIGNORE_TEMPLATE`, with that guard test green.
  - Execution state: pending

- [ ] E-03 PROVE THE IGNORE IS EFFECTIVE ON BOTH PATHS WITH REAL `git check-ignore`, and prove the anchoring guard, following the three sibling classes already in `tests/test_engine_install.py`.
  THE FOUR CASES: a FRESH install ignores `.aw/workflow-artifacts/<workflow>/<RUN_ID>/some-file.md`; an ALREADY-INSTALLED repo (one whose `.aw/.gitignore` has the line stripped, so only the append branch runs) gains it from the back-fill; repeated `_ensure_aw_gitignore` calls do not duplicate the line; and a nested `.aw/records/workflow-artifacts/keep.md` is NOT swallowed, which is the anchoring guard.
  ATTRIBUTE THE RULE TO THE RIGHT FILE, as the sibling classes do via `git check-ignore -v`: it must come from `.aw/.gitignore`, not from the user's root `.gitignore`, or the test would pass in this repo for the wrong reason and fail in a target repo.
  - Depends on: E-02
  - Expected outcome: a test class covering fresh, back-fill, idempotency and anchoring, each proven with real `git check-ignore` and attributed to `.aw/.gitignore`.
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
| F-1 | HIGH | the shipped gitignore has no entry for the run-scratch tree | `_AW_GITIGNORE_TEMPLATE` covers `records/*/untracked/`, `records/runs/`, `/inbox/`, `system/layout*.json` and four `INDEX.*` paths, but nothing for `workflow-artifacts`. | `engine.py:4321+` |
| F-2 | HIGH | this must precede Orders 01 and 03 | both make the new path real; landing either first leaves a window where run scratch is written to an unignored path. | the Set's sequencing rationale |
| F-3 | HIGH | the template alone never reaches an installed repo | a repo with an existing `.aw/.gitignore` takes only the append branch; every prior pattern carries a comment recording this. | `_ensure_aw_gitignore`, `engine.py:5397+` |
| F-4 | MEDIUM | a bare pattern is a measured hazard | the bare `inbox/` form matched at any depth and swallowed the TRACKED `records/comms/shared/inbox/` lane, breaking `aw install`. | the template's own `/inbox/` comment |
| F-5 | MEDIUM | a guard test requires this repo's copy stay in sync | `test_template_and_this_repos_own_gitignore_agree` fails if the template changes without re-syncing `.aw/.gitignore`; it caught exactly that on 2026-09-12. | `tests/test_engine_install.py` |

## Proposed changes (ordered, validatable)

1. Add anchored `/workflow-artifacts/` to the template AND the back-fill list, with a comment citing D92 and Order 07 (E-01).
2. Re-sync this repo's `.aw/.gitignore` to the template (E-02).
3. Prove fresh, back-fill, idempotency and anchoring with real `git check-ignore` (E-03).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan does not stop the repo-root directory being created (Order 01), does not touch the shipped bodies (Order 03) or READMEs (Order 04), does not move any file (Order 05), and does not modify any user's root `.gitignore`.

## Required tests / validation

- `git check-ignore -v` on `.aw/workflow-artifacts/<workflow>/<RUN_ID>/file.md` in a FRESH install, ATTRIBUTED to `.aw/.gitignore`.
- The same on an ALREADY-INSTALLED repo whose `.aw/.gitignore` had the line stripped, proving the back-fill branch.
- Exactly ONE occurrence of the pattern after repeated `_ensure_aw_gitignore` calls.
- `git check-ignore` FAILING (nonzero) for `.aw/records/workflow-artifacts/keep.md`, the anchoring guard.
- `.aw/.gitignore` byte-identical to the template, with the guard test green.
- `python3 -m pytest` BARE, failure-SET delta empty.

## Spec / documentation sync

No spec change: Order 07 already specifies the untracked home. The gitignore comment added by E-01 is the durable documentation, and it must cite D92 and the spec so a future reader does not remove the line as unexplained.

## Open questions

### OQ-01: Should the legacy repo-root `workflow-artifacts/` also be ignored by the framework-owned file?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: NO, AND DELIBERATELY. Resolved from the spec's intent: `.aw/.gitignore` patterns are `.aw/`-relative, so it CANNOT express a repo-root path at all, and reaching outside `.aw/` would mean editing the user's own root `.gitignore`, which this installer explicitly does not do (`engine.py` module docstring: "Does NOT silently edit user gitignores"). Order 01 removes the reason the repo-root path exists and Order 05 empties it, so ignoring it is unnecessary; a user who wants it ignored has `tools/untrack-workflow-artifacts.py`. NOT BLOCKING: nothing in this plan or the Set depends on the answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `engine.py` diff showing `/workflow-artifacts/` added to BOTH `_AW_GITIGNORE_TEMPLATE` and the `_ensure_aw_gitignore` back-fill list, with the comment citing D92 and Order 07. Quote the anchored form and state explicitly that it is `/workflow-artifacts/` and NOT a bare `workflow-artifacts/`. A bare pattern is a FAILED validation, not a style nit: the template's own `/inbox/` comment records that a bare form once swallowed the tracked `records/comms/shared/inbox/` lane.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the output of a comparison proving `.aw/.gitignore` is byte-identical to `_AW_GITIGNORE_TEMPLATE` (e.g. a Python `==` check or an empty `diff`), and paste the passing line for `ManifestIndexGitignoreTests::test_template_and_this_repos_own_gitignore_agree`. An unequal comparison is a FAILED validation even if every other test passes, because the next install would then re-diff this repo against its own template.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ACTUAL passing output of the new test class, then paste for EACH of the four cases the real command and result: `git check-ignore -v` on a file under `.aw/workflow-artifacts/` in a FRESH install, the same on a repo whose `.aw/.gitignore` had the line STRIPPED and was then back-filled, a count proving one line after repeated `_ensure_aw_gitignore` calls, and a `git check-ignore` that FAILS (exit nonzero) for `.aw/records/workflow-artifacts/keep.md`. Every `check-ignore -v` must attribute the rule to `.aw/.gitignore`; attribution to the root `.gitignore` is a FAILED validation, since that file is not shipped and the test would then prove nothing about a target repo.
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
