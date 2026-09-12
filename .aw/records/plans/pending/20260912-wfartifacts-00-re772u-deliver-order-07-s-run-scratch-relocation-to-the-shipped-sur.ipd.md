# IPD: Deliver Order 07's run-scratch relocation to the shipped surface

- Date: 2026-09-12
- Kind: orchestrator
- Concern: ORDER 07 DECIDED WHERE RUN SCRATCH LIVES AND THE DECISION WAS NEVER DELIVERED TO ANY TARGET REPO. Spec `20260817-2124-01-records-taxonomy-cleanup` (Order 07, `u7xtni`) carries `Status: implemented` and a history line reading "run-artifacts -> `.aw/workflow-artifacts/`", and this repo's root `.gitignore:62-68` encodes exactly that: run records hold local context, absolute home paths and session detail (D92), so they get ONE home at `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` and stay UNTRACKED. The migration moved THIS repository's own content and stopped there.
  MEASURED AT HEAD 2026-09-12, NOTHING A TARGET REPO RECEIVES WAS UPDATED. `engine.ARTIFACTS_DIR` (`engine.py:237`) is still `"workflow-artifacts/"`; the installer still CREATES that directory and writes a README into it (`engine.py:3292`, `:5141`); that README's entire content is "**DO NOT gitignore this folder.** These records represent the review and approval history of this repository and are intended to be committed", the exact OPPOSITE of the ruling; and `check_gitignore` (`:2664-2676`) merely ADVISES, reporting "workflow-artifacts/ is not ignored (advisory: working material will be tracked in git)" while never ignoring it and never naming `.aw/workflow-artifacts/`.
  THE SHIPPED BODIES STILL SEND AGENTS TO THE WRONG PLACE, 86 TIMES. `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows | wc -l` -> 86 across 27 files, while `grep -rho '\.aw/workflow-artifacts' ... | wc -l` -> ZERO. `assess/assess.md` alone has 8, and two of them (`:139`, `:189`) assert the directory "is gitignored by default", which is FALSE in a target repo precisely because item 1 above never ignores it. So an agent following the shipped instructions writes run scratch to a tracked repo-root directory and is told that is safe.
  THE COST IS ALREADY BANKED IN 29 REPOS on this machine. Most track only the stray README, but some hold genuinely COMMITTED run records predating the decision (one repo with 11 files across two assess runs, another with 3 including two advise session summaries; deliberately unnamed, being private), so a migration must `git mv` and never delete.
  AND AN AGENT HAS ALREADY MIS-RESOLVED IT ONCE, which is why the correct target must be stated unambiguously rather than left to inference: told about the problem, a repo agent moved run records into `.aw/records/reviews/untracked/`. That is wrong. `records/reviews/` is a TRACKED tree of typed `.review.md` artifacts written by `/plan-review` (170 files at HEAD), and Order 07 named `.aw/workflow-artifacts/` specifically so run scratch would stop being mixed into `records/`.
- Scope: Deliver the Order 07 relocation to the shipped surface, so a FRESH install writes run scratch to `.aw/workflow-artifacts/` and ignores it, an EXISTING install is migrated without losing committed history, and no shipped instruction or README still points at the repo-root directory. Covers the installer code path, the framework-owned `.aw/.gitignore` (template AND back-fill), the 86 stale references, the two READMEs that state the opposite of the rule, and an install-time migration. EXCLUDES re-litigating WHERE run scratch belongs (Order 07 settled it), any change to the tracked `.aw/records/` trees other than replacing one wrong README, and any deletion of a user's committed run records.
- Scope-Paths: agent_workflows/engine.py, .aw/system/workflows/, .aw/records/README.md, tests/
- Item-Dependencies: none
- Status: reviewed
- Priority: high
- Work-Kind: bug
- Readiness: go-pending-approval
- Blocks-Release: next
- From-Backlog: o9inwt
- Set: wfartifacts
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: re772u

## Workflow history
- 2026-09-12 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 all FIXED in place, none deferred, none REPLAN. aw ipd lint conformed at --phase author before semantic review and at --phase review-finalize after every revision. THE REVIEW RE-MEASURED EVERY NUMERIC CLAIM RATHER THAN TRUSTING IT, which is what produced the findings: the 86 occurrences, the 0 prefixed, the 29 repos, the 11-file and 3-file affected repos, the 170 reviews, the 42/10 test refs and all four engine.py citations re-verified EXACTLY, but the file count was 27 and is 25 (grep -rl without --include matched three __pycache__ binaries) and two per-file figures mixed grep -c lines with grep -o occurrences (18/11 vs the true 20/12). PR-002 found the riskiest gap: Order 05 described a MOVE where both trees are populated and three workflow names collide, so it is a MERGE; no RUN_ID collides because run ids are timestamps, but that is the data's property not the design's, so a merge test is now mandatory. PR-004 NARROWED Order 04 after finding the shipped agents-README.md template is already CORRECT and a fresh install receives it, so the wrong .aw/records/README.md is local drift from the Order 11 migration and the template must NOT be edited. PR-003 named the five tests that assert the defect. Also added, per the maintainer's instruction: an isolated-worktree clause to all six execution contracts, recording that aw oc run / aw agy run default isolate_worktree True and that a hand run must allocate its own lane. Typed review records written for all six. No product code was modified by this review. HUMAN APPROVAL IS STILL REQUIRED.
- 2026-09-12 to-review (aw set): Authored as Order 07 delivery (Set wfartifacts) from backlog o9inwt: the spec's run-scratch relocation was implemented in this repo but never delivered to the shipped surface (86 stale references, installer still creating a repo-root dir with a 'DO NOT gitignore' README, 29 repos affected). Review-ready: no TODO placeholders, E/V bijection complete, every V-item demands pasted evidence.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the shipped surface agree with the decision the repository already made: one home for run scratch, under `.aw/`, ignored, with existing installs carried across rather than stranded.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: run the children in order and prove the Set landed

- [ ] E-01 EXECUTE THE FIVE CHILDREN IN ORDER AND THEN PROVE THE END-TO-END OUTCOME ON A REAL REPO, which is the one check no child can make alone: each child owns one surface, and the defect being fixed is precisely that the surfaces DISAGREED.
  THE ORDER IS LOAD-BEARING, not merely tidy. Order 02 (ignore the new path) must land BEFORE Order 01 stops creating the old directory, so no window exists where run scratch is written to a path nothing ignores. Order 03 (rewrite the bodies) must land AFTER Order 02, or its claim that the directory is gitignored would still be false at the moment it is written. Order 05 (migrate) comes last because it depends on the ignore rule existing to avoid re-tracking what it moves.
  THE END-TO-END PROOF, on a scratch clone and NOT on a user's repo: install into a fresh repo and confirm no repo-root `workflow-artifacts/` is created, `.aw/workflow-artifacts/` is ignored via real `git check-ignore`, and a simulated run record written there does not appear in `git status`. Then install into a repo seeded with a COMMITTED repo-root run record and confirm it is relocated with its history intact and nothing is deleted.
  - Depends on: none
  - Expected outcome: all five children `executed`, plus pasted evidence from a fresh-install repo and a seeded legacy repo showing the new path ignored, the old path absent, and committed records preserved.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | `20260912-wfartifacts-01-gzhd7t-...ipd.md` | Retarget `ARTIFACTS_DIR` and the README emission; stop creating a repo-root run-scratch directory | Order 02 |
| 02 | `20260912-wfartifacts-02-vh14ku-...ipd.md` | Ignore `.aw/workflow-artifacts/` from the framework-owned `.aw/.gitignore`, in BOTH the template and the `_ensure_aw_gitignore` back-fill | none |
| 03 | `20260912-wfartifacts-03-9x1rps-...ipd.md` | Rewrite the 86 stale references in the shipped workflow bodies, and make the "gitignored by default" claims true | Order 02 |
| 04 | `20260912-wfartifacts-04-l1c1iz-...ipd.md` | Replace the workflow-artifacts README template and this repo's wrong `.aw/records/README.md` | none |
| 05 | `20260912-wfartifacts-05-y4pptx-...ipd.md` | Migrate an existing install's committed run records into `.aw/workflow-artifacts/` on `aw install` | Orders 01, 02 |

SEQUENCING RATIONALE, since the dependency column alone understates it: 02 FIRST so the ignore rule exists before anything writes to the new path; then 01 and 03 in either order (both merely need 02 landed); 04 is independent prose and may land any time; 05 LAST because it moves files into a path that must already be ignored, or the migration would immediately re-track what it relocated.

## Completion criteria (the whole Set is done only when)

- A FRESH install creates NO repo-root `workflow-artifacts/` directory, proven by its absence on disk.
- `.aw/workflow-artifacts/` is ignored in a target repo, proven by `git check-ignore -v` ATTRIBUTED TO `.aw/.gitignore` (not to any root `.gitignore`, which is not shipped).
- Zero bare `workflow-artifacts` references remain in the shipped tree except deliberate legacy mentions, each named with its reason; the `.aw/`-prefixed count is at least the original 86.
- Neither shipped README, nor the `engine.py` fallback literal, still tells a reader to commit run scratch or not to ignore it.
- An existing repo's COMMITTED run records are relocated with `git log --follow` still reaching their original commits, and the before/after path sets are equal modulo the prefix.
- Nothing a user committed was deleted anywhere in the Set.
- `python3 -m pytest` BARE with an empty failure-SET delta, and `aw sanitize --agent` clean.

## Cross-IPD validation

- THE ORDER HELD: confirm Order 02 landed BEFORE Orders 01, 03 and 05, by commit order. If 03 landed first, its "gitignored by default" claim was FALSE when written, which is the exact defect this Set fixes, so that sequence is a failure even if every test passes.
- NO CHILD REINTRODUCED THE RETIRED PATH: re-run the bare-reference grep AFTER all five, not only after Order 03, since Orders 01 and 05 also edit code that names the path.
- THE THREE SURFACES NOW AGREE, which is the Set's whole premise: the installer writes where the bodies say, the bodies claim the tracking state the gitignore actually enforces, and the READMEs describe that same state. Check all three against one freshly installed repo rather than against each plan's own evidence.
- NO DOUBLED PREFIX anywhere: `grep -rn '\.aw/\.aw/'` over the tree returns nothing.
- THE `2812t3` AND `ttr3b9` FIXES STILL HOLD, since Orders 01/02/05 all edit `engine.py` near them: `.aw/state/` and `.aw/config/local.json` still ignored, and the installer's commit still succeeds on an already-current repo.

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this Set does not re-decide where run scratch lives, does not change `tools/untrack-workflow-artifacts.py`, does not touch the tracked `.aw/records/` trees beyond replacing one wrong README, does not alter any user's root `.gitignore`, and does not delete any committed run record.

## Required tests / validation

- THE END-TO-END PROOF ON A FRESH REPO: no repo-root `workflow-artifacts/` exists after install; `.aw/workflow-artifacts/` is ignored per real `git check-ignore -v` attributed to `.aw/.gitignore`; a file written there does not appear in `git status`.
- THE END-TO-END PROOF ON A SEEDED LEGACY REPO: a COMMITTED repo-root run record is relocated, `git log --follow` still reaches its original commit, and the before/after run-record path sets are equal modulo the prefix.
- EVERY CHILD'S OWN `V-*` ITEMS verified with pasted output; this orchestrator does not re-verify them, it confirms all five reached `executed`.
- `python3 -m pytest` BARE, failure-SET delta empty.
- `aw sanitize --agent` clean.

## Open questions

### OQ-01: Should the repo-root `workflow-artifacts/` directory be removed entirely once migrated, or left as an ignored empty shell?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: REMOVE IT WHEN IT IS EMPTY, KEEP IT WHEN IT IS NOT, and never delete user content to make it empty. Resolved from Order 07's own reasoning rather than asked: the spec chose ONE home precisely to end a double-home inconsistency, so leaving an ignored empty directory would preserve the confusion the ruling exists to remove, and the maintainer's report is specifically that the directory APPEARS. But a directory still holding content the migration refused to move (a same-path conflict, per Order 05) must stay, because the alternative is data loss. Order 05 owns the mechanics; Order 01 owns simply not creating it. NOT BLOCKING: both halves are already implied by the invariants each child states, so no execution decision is stranded on this.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `- Status:` line of all five children showing `executed`. THEN paste the end-to-end evidence from TWO scratch repos, which is what no child can produce alone. Fresh repo: `ls -d <repo>/workflow-artifacts` failing, `git check-ignore -v` on a file under `.aw/workflow-artifacts/` attributed to `.aw/.gitignore`, and `git status --porcelain` empty after writing one. Seeded legacy repo with a COMMITTED run record: the file at its new path, the ACTUAL `git log --follow` output reaching the pre-migration commit, and a before/after path-set comparison. Also paste the commit order proving Order 02 preceded Orders 01, 03 and 05. Use scratch clones, NEVER a user's repo.
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
