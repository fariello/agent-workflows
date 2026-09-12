# IPD: Retarget the installer and stop creating a repo-root run-scratch directory

- Date: 2026-09-12
- Kind: child
- Concern: THE INSTALLER STILL CREATES THE DIRECTORY THE DECISION RETIRED, AND ADVERTISES IT AS TRACKED. `engine.ARTIFACTS_DIR` is `"workflow-artifacts/"` (`engine.py:237`), `_ensure_artifacts_readme` (`:5139`) does `artifacts_dir.mkdir(parents=True, exist_ok=True)` at the REPO ROOT and writes a README there, and `:3292` adds the same path to the proposed-file set. So every fresh install materializes a repo-root directory whose README says "DO NOT gitignore this folder", which is the opposite of Order 07's ruling and the reason the maintainer noticed on 2026-09-12.
  `check_gitignore` COMPOUNDS IT BY REPORTING THE WRONG THING. At `:2664-2676` it inspects only the repo-root path and prints either "workflow-artifacts/ is ignored (correct, recommended for local working material)" or "workflow-artifacts/ is not ignored (advisory: working material will be tracked in git)". Both sentences are now wrong: the correct state is that the repo-root directory does not exist and `.aw/workflow-artifacts/` is ignored by the framework-owned file. An installer that keeps reporting on a retired path teaches the user the retired layout.
  THE FALLBACK LITERAL IS A SECOND COPY OF THE BAD PROSE. `_ensure_artifacts_readme` carries an inline `readme_content` fallback (`:5153-5162`) duplicating the "DO NOT gitignore this folder" text for when the template cannot be read, so fixing only the template file would leave a live copy that still ships on any OSError.
- Scope: Stop creating a repo-root run-scratch directory on install, retarget `ARTIFACTS_DIR` and the README emission to `.aw/workflow-artifacts/`, and make `check_gitignore` report the path that now matters. EXCLUDES the gitignore pattern itself (Order 02, which must land first), the README's CONTENT (Order 04), the shipped body references (Order 03), and migrating existing content (Order 05).
- Scope-Paths: agent_workflows/engine.py, tests/test_installer.py, tests/test_engine_install.py
- Item-Dependencies: none
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- From-Backlog: o9inwt
- Set: wfartifacts
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: gzhd7t

## Workflow history
- 2026-09-12 to-review (aw set): Authored as Order 07 delivery (Set wfartifacts) from backlog o9inwt: the spec's run-scratch relocation was implemented in this repo but never delivered to the shipped surface (86 stale references, installer still creating a repo-root dir with a 'DO NOT gitignore' README, 29 repos affected). Review-ready: no TODO placeholders, E/V bijection complete, every V-item demands pasted evidence.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a fresh install produce the layout Order 07 chose, and stop advertising the retired one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: retarget the code, then prove a fresh install is clean

- [ ] E-01 RETARGET `ARTIFACTS_DIR` AND EVERY WRITE SITE TO `.aw/workflow-artifacts/`, and REMOVE the repo-root `mkdir`.
  THE THREE SITES, located by name rather than by the line numbers cited here: the `ARTIFACTS_DIR` constant (`engine.py:237`), the proposed-file entry (`:3292`), and `_ensure_artifacts_readme` (`:5139`), which is the one that actually creates the directory.
  DO NOT LEAVE A REPO-ROOT `mkdir` BEHIND. The maintainer's report is specifically that the directory APPEARS; a run that merely stops writing the README but still creates an empty directory has not fixed the reported defect.
  KEEP `LEGACY_ARTIFACTS_DIR` AND THE PRE-D19 MIGRATION INTACT (`:238`, `:2608-2613`). That code moves `repository-review/` into the artifacts tree and is a DIFFERENT, older migration; retargeting its destination is correct, deleting it is not.
  - Depends on: none
  - Expected outcome: `ARTIFACTS_DIR` is the `.aw/` path, no repo-root directory is created by any install path, and the pre-D19 migration still runs with its destination retargeted.
  - Execution state: pending

- [ ] E-02 FIX `check_gitignore` TO REPORT THE PATH THAT MATTERS, or remove the advisory if it no longer says anything true.
  WHAT IT SAYS TODAY IS MISLEADING IN BOTH BRANCHES: "workflow-artifacts/ is ignored (correct, recommended...)" and "...is not ignored (advisory: working material will be tracked in git)". After Order 02 the framework-owned `.aw/.gitignore` ignores the real path unconditionally, so an advisory about the user's ROOT gitignore and a retired path is noise that contradicts the installer's own behavior.
  DECIDE EXPLICITLY AND SAY WHY IN THE CODE: either report on `.aw/workflow-artifacts/` (and then it should essentially always read "ignored"), or drop the line and its `gitignore_status` plumbing. Do NOT leave a branch that can print advice about a directory the installer no longer creates.
  NOTE THE PLUMBING REACHES THE SUMMARY at `:3729` (`print(f"Gitignore (workflow-artifacts): {gitignore_status}")`) and through `install_into_repo`'s returned dict, so removing it is a small API change to check for callers, not a one-line delete.
  - Depends on: E-01
  - Expected outcome: no installer output describes the retired repo-root path, and whatever remains is true of a repo installed after Order 02.
  - Execution state: pending

- [ ] E-03 PROVE A FRESH INSTALL PRODUCES NO REPO-ROOT DIRECTORY AND UPDATE THE TESTS THAT PIN THE OLD BEHAVIOR.
  EXPECT EXISTING TESTS TO FAIL, and treat that as the signal rather than a nuisance: 42 references to `workflow-artifacts`/`ARTIFACTS_DIR` exist across 10 test files (`test_installer.py`, `test_awretrofit_install_selfheal.py`, `test_acceptance_matrix.py`, `test_packaging.py` and others). Each must be re-pointed or deliberately re-scoped, and any that asserts the repo-root README is INSTALLED is asserting the defect and must be inverted.
  THE NEW ASSERTION THAT MATTERS: after `install_into_repo` on a fresh repo, `(repo / "workflow-artifacts").exists()` is FALSE. That single line is the maintainer's report turned into a test.
  RUN THE SUITE BARE and compare the FAILURE SET, not counts.
  - Depends on: E-02
  - Expected outcome: a test asserting no repo-root directory after a fresh install, every pre-existing reference re-pointed or re-scoped with a stated reason, and an empty bare-suite failure-set delta.
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
| F-1 | HIGH | the installer creates the retired directory | `_ensure_artifacts_readme` calls `artifacts_dir.mkdir(parents=True, exist_ok=True)` on a REPO-ROOT path and writes a README into it. | `engine.py:5141`, `:5168` |
| F-2 | HIGH | the constant still points at the repo root | `ARTIFACTS_DIR = "workflow-artifacts/"`. | `engine.py:237` |
| F-3 | MEDIUM | the advisory is wrong in both branches | `check_gitignore` reports either "is ignored (correct...)" or "is not ignored (advisory...)" about a path that should not exist. | `engine.py:2664-2676`, printed at `:3729` |
| F-4 | MEDIUM | a third copy of the bad prose is inline | `_ensure_artifacts_readme`'s OSError fallback duplicates the README text, so fixing the template alone leaves live bad prose. | `engine.py:5153-5162` |
| F-5 | MEDIUM | 42 test references pin the old behavior | across 10 files; some assert the repo-root README IS installed, i.e. they assert the defect. | grep over `tests/` |
| F-6 | LOW | the pre-D19 migration must survive | `LEGACY_ARTIFACTS_DIR` moves `repository-review/` into the artifacts tree; it needs retargeting, not deletion. | `engine.py:238`, `:2608-2613` |

## Proposed changes (ordered, validatable)

1. Retarget `ARTIFACTS_DIR`, the proposed-file entry, and `_ensure_artifacts_readme`; remove the repo-root `mkdir` (E-01).
2. Make `check_gitignore` true or remove it with its plumbing (E-02).
3. Re-point or re-scope the 42 pinning test references and add the no-repo-root-directory assertion (E-03).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan does not add the gitignore pattern (Order 02), does not change README CONTENT (Order 04), does not touch the shipped bodies (Order 03), and does not move existing content (Order 05). It also does not delete the pre-D19 `repository-review/` migration.

## Required tests / validation

- A FRESH `install_into_repo` INTO A SCRATCH REPO: assert `(repo / "workflow-artifacts").exists()` is FALSE. This single assertion is the maintainer's report turned into a test.
- THE INSTALLER SUMMARY names no repo-root `workflow-artifacts/` path.
- EVERY PRE-EXISTING TEST re-pointed or re-scoped, each named with a one-line reason; a DELETED test must be justified.
- `python3 -m pytest` BARE, failure-SET delta empty.
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change: Order 07's spec already specifies the target layout and is `implemented`. This plan makes the code match it.

`engine.py`'s module docstring (`:39`, `:42`, `:47`) describes `workflow-artifacts/` run records and D17/D19 behavior; update those lines so the file's own front matter does not contradict its code. That is documentation inside a declared Scope-Path, not a spec amendment.

## Open questions

### OQ-01: Should `check_gitignore` be retargeted or removed outright?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: EXECUTOR'S CHOICE, WITH THE REASON RECORDED IN CODE, and E-02 requires the decision be explicit either way. Resolved rather than asked because both options are defensible and neither is risky: after Order 02 the framework-owned gitignore ignores the real path unconditionally, so a retargeted advisory would essentially always print "ignored" and carries little information, while removing it is a small API change (`gitignore_status` appears in `install_into_repo`'s returned dict and the summary at `:3729`) that needs a caller check. What is NOT acceptable is leaving a branch that can advise about a directory the installer no longer creates. NOT BLOCKING: E-02 states the constraint that actually matters, and V-02 demands evidence for whichever path is taken.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `engine.py` diff for all three sites and quote the new `ARTIFACTS_DIR` value. Then paste, from a REAL fresh install into a scratch repo, the output of `ls -d <repo>/workflow-artifacts` showing it does NOT exist, and `ls -d <repo>/.aw/workflow-artifacts` if the README now lands there. An existing repo-root directory, even an empty one, is a FAILED validation: the reported defect is that the directory appears.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the full installer summary block from a fresh install and show that NO line mentions a repo-root `workflow-artifacts/`. If the advisory was kept, quote the exact new sentence and show it is true for that repo by pasting `git check-ignore -v` on the path it names; if it was removed, paste the diff showing the `gitignore_status` plumbing removed from both the summary and `install_into_repo`'s returned dict, plus a grep proving no caller still reads that key.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new assertion and its passing output, then paste the BARE `python3 -m pytest` summary lines BEFORE and AFTER and state the failure-SET delta explicitly (criterion: empty). For every pre-existing test you changed, name it and say in one line whether it was re-pointed or re-scoped and why; a test deleted rather than re-pointed must be justified, since deleting a test that asserted the old path is how the guarantee silently disappears.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
