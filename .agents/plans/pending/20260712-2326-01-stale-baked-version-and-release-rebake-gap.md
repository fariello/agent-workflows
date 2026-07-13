# IPD: Stale baked VERSION (installer stamps 1.1.0 after the 1.2.0 release) + fix the release re-bake gap

- Date: 2026-07-12
- Concern: correctness / release process. `v1.2.0` shipped with a stale baked
  `.agents/workflows/VERSION` = `1.1.0` (verified: `git show v1.2.0:.agents/workflows/VERSION` -> 1.1.0).
  The PyPI wheel is CORRECT (hatch_build.py computes the wheel version from the tag-driven resolver),
  but the INSTALLER copies the baked `VERSION` file verbatim into each target repo (`read_version` /
  install flow), so every `aw install` and `aw install all` stamps targets with `1.1.0` and currency
  checks compare against the wrong number. Observed live: `aw install all` reported
  "version 1.1.0" installing into a-consuming-repo after 1.2.0 was released. Root cause: the release cut the
  `v1.2.0` tag WITHOUT re-baking + committing `VERSION` from the tag, so the tracked file drifted from
  the tag. This is TWO defects: (X) the stale artifact on `main`/at the tag, and (Y) the release process
  that permits the drift.
- Scope: (X) regenerate `.agents/workflows/VERSION` to match the release version and commit it;
  (Y) add a required "re-bake and commit VERSION from the tag" step to the release process
  (`RELEASING.md` + release-review `09-release-execution.md`) so the baked file can never again ship
  out of sync with the tag, INCLUDING resolving the bake-vs-tag ordering (below). Docs/DECISIONS.
  Ships in the 1.2.1 patch with IPDs `20260712-1837-01` and `20260712-2146-01`.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after `aw install all` stamped
  1.1.0 post-1.2.0-release. Root-caused against source + the v1.2.0 tag. Complete proposal; born
  to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- `.agents/workflows/VERSION` is a DERIVED artifact, regenerated from the tag via `make version-file`
  (Makefile:18-23: `resolve_version(.)` -> write to the VERSION file), never hand-edited (D44/D50).
- `read_version` (engine.py:143-170) uses the resolver WHEN the source is a git work tree of this
  project (so a clean tagged source reports the semver). BUT the installer copies the baked `VERSION`
  FILE verbatim into each TARGET; the target is not our git tree, so the installed copy reports whatever
  the baked file said. Therefore a stale baked file propagates to every target regardless of the
  resolver. This is why the wheel (resolver-computed) was right while installs (file-copied) were wrong.
- The `v1.2.0` tag's tree contains VERSION=1.1.0 (verified). So the stale file was released, not just a
  post-release drift.
- Ordering paradox (must be resolved by change Y): VERSION is baked FROM the tag
  (`resolve_version` needs the tag to exist to produce `1.2.0`), but committing the re-baked file
  creates a commit AFTER the tag, so the tag itself can never contain a VERSION equal to itself under a
  naive "tag then bake" order. Options: (i) bake VERSION to the INTENDED release version and commit
  BEFORE tagging, then tag that commit (so the tag contains the correct VERSION) - requires baking from
  the intended version string, not from `git describe`; or (ii) accept that the tag's VERSION is the
  PREVIOUS release and re-bake+commit immediately AFTER tagging on the release branch (tag lags by one
  commit, but `main` is correct and installs are correct). Decide in review (OQ1). Note `hatch_build.py`
  reads the resolver, so the WHEEL is correct either way; this ordering only affects the baked file's
  value AT the tag commit.
- release-review `09-release-execution.md` Step 1 (:47) says "confirm version metadata is bumped
  consistently (package manifest, __version__, CHANGELOG, docs)" but does NOT explicitly name re-baking
  `.agents/workflows/VERSION`; the tag step (:94) does not either. That omission is the process gap.
- RELEASING.md documents tag conventions but does not currently require re-baking VERSION at tag time.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **(X) Regenerate the baked VERSION now.** Run `make version-file` on the correct version and commit
   `.agents/workflows/VERSION` so it matches the release line. NOTE: on the current ahead-of-tag tree
   the resolver yields `1.2.1.devN`; the CORRECT baked value depends on OQ1 and the release flow. For
   the 1.2.1 patch this file is (re-)baked as part of cutting `v1.2.1` from a clean tag (so it becomes
   `1.2.1`), which is the natural moment to fix it. If a stopgap for the CURRENT stale `main` is wanted
   before 1.2.1 ships, bake to `1.2.0` and commit (matches the last real release) - decide in review
   (OQ2). Do NOT hand-edit the file; use `make version-file` (possibly with an intended-version input
   per change 2).
2. **(Y) Fix the release process so VERSION can never drift from the tag.** Add an explicit, required
   step to `09-release-execution.md` (Step 1 / the tag step) and to `RELEASING.md`: when cutting a
   release, RE-BAKE `.agents/workflows/VERSION` from the release version and COMMIT it as part of the
   release, resolving the ordering paradox per OQ1 (recommended lean: bake VERSION to the intended
   `vX.Y.Z` and commit it in the release commit, THEN tag that commit, so the tag contains a VERSION
   equal to itself and installs from any tagged checkout are correct). This likely needs
   `make version-file` to accept an explicit intended-version (rather than only `git describe`), OR a
   documented "tag, re-bake, amend/commit, move tag" dance - pick the simpler correct one in review.
3. **Validation guard (regression).** Add a test asserting the baked `.agents/workflows/VERSION` is not
   stale relative to the resolver on a clean tagged tree - i.e. on a clean checkout of a release tag,
   `read_version` from a copied-out (non-git) source equals the tag's semver. If a fully faithful test
   is impractical (needs a tag + copy-out), at minimum add a test/CI check that VERSION parses as a
   valid release version and, when HEAD is exactly a release tag, equals it. This is the guard that
   would have caught the 1.1.0 drift.
4. **Docs + DECISIONS.** DECISIONS entry (next free number at execution) recording the stale-VERSION
   bug, that the wheel was unaffected (resolver) but installs were (baked file), the ordering-paradox
   resolution, and the new required re-bake step. Note in CHANGELOG under 1.2.1
   ("installer stamped the wrong version; VERSION now re-baked at release and guarded").

## Deferred / out of scope

- Changing HOW the installer determines a target's version (copying the baked file is the intended
  design; the fix is keeping that file correct, not changing the mechanism).
- The wheel/pyproject version path (already correct via the resolver; untouched).
- Retroactively fixing the `v1.2.0` TAG's tree (immutable release; the fix lands in 1.2.1, and 1.2.0
  installs stamping 1.1.0 is documented as a known issue fixed in 1.2.1).

## Open questions (v1 leans for review)

1. Ordering: bake-then-tag (tag contains correct VERSION; needs an intended-version bake) vs.
   tag-then-rebake (tag lags one commit; `main` correct). Lean: bake-then-tag - it makes any tagged
   checkout install-correct, which is the whole point. Confirm the mechanism (an intended-version arg
   to `make version-file`).
2. Stopgap for current stale `main` before 1.2.1 ships: bake to `1.2.0` and commit now, or wait and let
   the 1.2.1 cut fix it? Lean: since 1.2.1 is imminent and will re-bake to `1.2.1` anyway, wait unless
   you plan more `aw install`s meanwhile - if so, a `1.2.0` stopgap commit is cheap and stops the wrong
   stamp. Maintainer decides.
3. How strict should the regression guard be given it needs a tag+copy-out to be fully faithful?
   Lean: a pragmatic check (VERSION is a valid release string; equals the tag when HEAD==tag) over a
   heavy end-to-end fixture.

## Dependencies / sequencing

- Ships in the 1.2.1 patch with `20260712-1837-01` (CLI/`_install_all` diagnostics parity) and
  `20260712-2146-01` (diagnostics false alarm). Independent of `20260712-1901-01` (orchestrator
  unification, 1.3.0).
- Interacts with release-review Section 9: change 2 edits that workflow, so executing this IPD updates
  the very process the 1.2.1 release will then follow (bootstrap: the 1.2.1 cut should USE the new
  re-bake step, validating it).

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY: `.agents/workflows/VERSION` (re-bake via `make version-file`, never
   hand-edit), `Makefile` (only if an intended-version input is needed for bake-then-tag),
   `.agents/workflows/release-review/09-release-execution.md` + `RELEASING.md` (the required re-bake
   step), a test file for the guard, `CHANGELOG.md`, and `DECISIONS.md` (next free number). Do NOT
   change the installer's version-copy mechanism or the wheel/hatch path. If a change seems to need
   more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Demonstrate that a clean tagged
   checkout stamps the correct version into a target (or the pragmatic equivalent per OQ3). Confirm
   `aw plan-names` clean.
4. COMMIT only this IPD's touched files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: ships in the 1.2.1 patch via release-review Section 9 after a human rung choice; the 1.2.1
   cut should EXERCISE the new re-bake step (change 2), proving it works.

HARD MUST: paste the real test output; use `make version-file` (never hand-edit VERSION); stay inside
the scope fence; never push. Not auto-executed; requires human approval.
