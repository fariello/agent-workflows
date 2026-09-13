- Id: o9inwt
- Status: done
- Blocks-Release: next
- Set: o9inwt
- Priority: high
- Work-Kind: bug
- Summary: Order 07's run-scratch relocation was never delivered to the shipped surface: 86 bare workflow-artifacts/ refs, the installer still creates a repo-root dir with a 'DO NOT gitignore' README, and 29 existing installs need migrating

## Workflow history
- 2026-09-13 done (aw set): Closed done per check.orphaned-live-blocker: the release gate is PRESERVED VIA HANDOFF, not dropped. All six wfartifacts plans (re772u, gzhd7t, vh14ku, 9x1rps, l1c1iz, y4pptx) carry From-Backlog: o9inwt and Blocks-Release: next, and the orchestrator re772u is approved, so 2.0.0 still cannot ship until the work lands. This closes the ITEM, not the work; I filed the plans earlier and left the item open, which is the bookkeeping gap the rule exists to catch.
- 2026-09-12 created (aw backlog): Order 07's run-scratch relocation was never delivered to the shipped surface: 86 bare workflow-artifacts/ refs, the installer still creates a repo-root dir with a 'DO NOT gitignore' README, and 29 existing installs need migrating

## Reported by the maintainer 2026-09-12

"Why are new installs still creating a `<repo-root>/workflow-artifacts/` directory with a README that
says 'DO NOT gitignore this folder'... I was 100% sure we said this needed to move under `.aw/` and
needed to be ignored." THE MAINTAINER IS CORRECT, and the decision exists; it was simply never
delivered to the shipped surface.

## The decision that was made

Spec `20260817-2124-01-records-taxonomy-cleanup` (Order 07, `u7xtni`), `Status: implemented`, history
line: "run-artifacts -> `.aw/workflow-artifacts/`". Run scratch (release-review / assess / advise /
verify run records) gets ONE home at `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` and stays UNTRACKED
because it holds local context, absolute home paths and session detail (D92). This repo's own root
`.gitignore:62-68` states exactly that and ignores both the new path and the legacy repo-root one.

## What actually shipped, measured at HEAD 2026-09-12

THE MIGRATION MOVED THIS REPO AND STOPPED THERE. Nothing that a TARGET repo receives was updated:

1. `engine.ARTIFACTS_DIR = "workflow-artifacts/"` (`engine.py:237`) is still the repo-root path.
2. The installer still CREATES the directory and writes a README into it
   (`engine.py:3292`, `:5141`, `:5150`), from template
   `.aw/system/workflows/templates/workflow-artifacts-README.md`, whose entire content is:
   "**DO NOT gitignore this folder.** These records represent the review and approval history of this
   repository and are intended to be committed" - the exact OPPOSITE of the ruling.
3. 86 BARE `workflow-artifacts/` references remain across 27 shipped workflow bodies, and ZERO say
   `.aw/workflow-artifacts/`. Counted with
   `grep -rhoP '(?<!\.aw/)workflow-artifacts' .aw/system/workflows | wc -l` -> 86, and
   `grep -rho '\.aw/workflow-artifacts' ... | wc -l` -> 0.
   `assess/assess.md` alone has 8, including `:139` and `:189` asserting the directory "is gitignored
   by default", which is FALSE in a target repo since the installer never ignores it.
4. `check_gitignore` (`engine.py:2664-2676`) only ADVISES about the repo-root dir and reports
   "workflow-artifacts/ is not ignored (advisory: working material will be tracked in git)". It
   never ignores it and never mentions `.aw/workflow-artifacts/`.
5. 29 repos on this machine already carry a repo-root `workflow-artifacts/`. Most track only the stray
   README, but some hold genuinely COMMITTED run records predating the decision (one repo with 11
   files across two assess runs; another with 3 including two advise session summaries). The repo
   names are deliberately omitted: they are private, and this item is a public artifact. A migration
   must `git mv` these, never delete them.

## Two further defects found while checking, both in THIS repo

6. `.aw/records/README.md` IS THE WRONG FILE. It contains the workflow-artifacts README text verbatim,
   "DO NOT gitignore this folder", while `.aw/records/` is the TRACKED durable-records tree (170
   `.review.md` files under `records/reviews/` alone). Landed by commit `f296f6f4`
   ("migrate(awphysical): move the framework repo to the physical .aw/ layout (Order 11)"), which
   evidently moved the README along with the content. It now tells every reader the opposite of the
   truth for that tree.
7. AN AGENT ALREADY MIS-RESOLVED THIS ONCE. Told about the problem, a repo agent moved run records into
   `.aw/records/reviews/untracked/`. That is WRONG: `records/reviews/` is a TRACKED tree of typed
   `.review.md` artifacts written by `/plan-review`, not the run-scratch home, and Order 07 named
   `.aw/workflow-artifacts/` precisely so run scratch would stop being mixed into `records/`. The
   correct home is `.aw/workflow-artifacts/<workflow>/<RUN_ID>/`. Whoever executes this should also
   decide what to do with those relocated files rather than leaving them stranded.

## Scope (a plan Set, per the maintainer's 2026-09-12 ruling)

Four separable deliverables plus a migration:
- RETARGET the code: `ARTIFACTS_DIR`, the README emission, and `check_gitignore`.
- REWRITE the 86 references in the shipped bodies to `.aw/workflow-artifacts/`, and fix the false
  "gitignored by default" claims so they are true.
- REPLACE both wrong READMEs (the workflow-artifacts template, which should say the opposite, and
  `.aw/records/README.md`, which should describe the tracked records tree).
- IGNORE the new path from the framework-owned `.aw/.gitignore` (template AND the
  `_ensure_aw_gitignore` back-fill, which is the only path that reaches an already-installed repo).
- MIGRATE existing installs on `aw install`: `git mv` repo-root `workflow-artifacts/` content into
  `.aw/workflow-artifacts/`, preserving committed history, never deleting.

DO NOT resolve this by keeping the repo-root directory and merely ignoring it: the spec chose ONE home
and the double-home inconsistency is what Order 07 existed to end.
