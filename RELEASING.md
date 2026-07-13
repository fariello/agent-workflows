# Releasing

How releases are cut in this repository. The version is git-tag-driven (DECISIONS D44/D46):
`agent_workflows/versioning.py` derives the version from `git describe`; `VERSION` is a
generated artifact, never hand-edited. This document is the single source of truth for the
tag/release/publish conventions; the workflows point at it (D71).

## A git tag is not a release

Three separate, independently-gated things are often conflated. Keep them distinct:

1. **A git tag** just labels a commit. It does not publish anything, reserve a name, or
   trigger an install.
2. **A GitHub Release** is the visible entry on the repo's Releases tab that notifies
   watchers. It is created only from rung C, and only as a DRAFT the human publishes.
3. **A PyPI publish** (`twine upload`) is the only step that puts the package on the index.
   It is a separate, credentialed, user-gated step.

## The release consent decision tree (release-review Section 8/9)

The reviewer's recommendation stays `GO` / `CONDITIONAL GO` / `NO-GO`. On approval of a
GO / CONDITIONAL GO, you choose exactly one rung; the safe rung is the default:

- **(A) Close out the review only [default].** Nothing is tagged, pushed, released, or
  published. Fully reversible.
- **(B) Cut a release CANDIDATE.** Create an annotated `vX.Y.Z-rc.N` pre-release tag only
  (pushing it is a separate, default-NO confirmation). Not a GitHub Release; not published.
- **(C) FULL RELEASE.** Section 9 confirms each externally-visible action (tag, push, GitHub
  Release, publish) separately, default-NO. Only a bare final `vX.Y.Z` is used here.

On a `NO-GO`, no rungs are offered.

## Tag conventions

- A **bare `vX.Y.Z`** tag means "this is intended for a registry release". Use it only for a
  full release (rung C).
- Anything not yet registry-bound MUST be a **`vX.Y.Z-rc.N`** candidate (or left untagged,
  in which case the resolver reports a `.devN` version). The resolver emits an rc tag as PEP
  440 `X.Y.ZrcN`, so pip treats it as a pre-release and does not install it without `--pre`.
- Tags are ALWAYS annotated (signed if the project signs tags), never lightweight, and are
  created on a clean, CI-green tree.
- **Bake-then-tag.** The tracked `.agents/workflows/VERSION` is a derived artifact the installer
  copies into every target repo. At release time, re-bake it to the intended version and commit it
  BEFORE tagging: `make version-file VERSION=<X.Y.Z>`, commit, then `git tag -a vX.Y.Z ...` on that
  commit. This keeps the tag's tree carrying a VERSION equal to its own tag, so installs from any
  tagged checkout stamp the correct number. Tag-then-rebake is wrong: it leaves the tag carrying the
  previous release's version. (The wheel version is computed by the resolver and is unaffected either
  way; this rule is specifically about the baked file the installer distributes.)
- Never create or push a tag, a GitHub Release, or a registry upload outside release-review
  Section 9 after an explicit human GO. No ad-hoc `git tag`; no `git push --follow-tags` of
  release tags.

## PyPI publish

Publishing to PyPI is a separate, credentialed, user-gated `twine upload` step, performed
only under rung C with authorized credentials, or handed off to the maintainer with exact
steps. The first PyPI release is `1.1.0` (DECISIONS D51); `1.0.0` was git-tag only.
