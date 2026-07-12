# IPD: PyPI publish support - absolute doc links + latest-version check for /release-review

- Date: 2026-07-12
- Concern: release / distribution correctness. Projects published to PyPI render a long-description
  (almost always `README.md`) with NO repo context, so relative Markdown links (to the CLI docs,
  functional specs, other `.md`) 404 on PyPI while working on GitHub. Also, `/release-review` has no
  awareness of the currently-published PyPI version, so it cannot assert the "next" version is a
  valid `>=` bump.
- Scope: a build-time link rewriter (hatch build hook, operating on a COPY of the long-description;
  source untouched), the packaging config that wires it, a PyPI latest-version lookup helper, and a
  `/release-review` hook that consumes it. Docs + DECISIONS. `.md` only (PyPI renders the
  long-description file; HTML/other docs are not published to PyPI - confirmed).
- Status: draft
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-01). Key decision taken: build-time rewrite via a hatch build hook on a COPY so the source
  README keeps GitHub-correct relative links and only the published artifact gets absolute tagged
  URLs. Awaiting flesh-out.

## Goal

1. **Working links on PyPI.** At build time, rewrite relative Markdown links in the long-description
   to absolute `https://github.com/<owner>/<repo>/blob/<tag>/<path>` (and `.../raw/<tag>/...` for
   images/binary assets), pinned to the release tag/version. Operate on a COPY used for the
   wheel/sdist metadata; NEVER modify the source `README.md` (its relative links are correct for
   GitHub browsing). Derive owner/repo from the git remote (or `pyproject` project URLs) and the tag
   from the release version.
2. **Version awareness for /release-review.** A small helper queries the latest version published on
   PyPI (JSON API / `pip index versions`), so `/release-review` (and release-notes) can confirm the
   proposed next version is `>= current published` and suggest the next candidate. Degrade gracefully
   when offline / the package is unpublished / no network.

## Decisions taken (maintainer, 2026-07-12)

1. **Build-time hook on a COPY (source untouched).** Rewrite happens in a hatchling build hook (we
   already ship `hatch_build.py`); the source tree is never rewritten. Deterministic, no manual step,
   nothing incorrect ever committed.
2. **Scope is the rendered long-description (`.md` for our repos).** No HTML/other docs (PyPI does
   not publish a docs tree). Keep general: whatever file is declared as the long-description.

## Open questions (to resolve during flesh-out / review)

1. Exactly which links to rewrite: relative repo-internal links only (leave absolute/`http(s)`/anchor
   links alone); how to treat links that point OUTSIDE the packaged tree.
2. Owner/repo/tag derivation precedence (git remote vs `[project.urls]` vs explicit config) and
   behavior when the remote is not GitHub.
3. `blob` vs `raw`: image/asset detection (extensions) vs doc links.
4. Where the PyPI version check lives (a `versioning`/new helper) and how `/release-review` surfaces
   it (Section 1 baseline? the CI/version area? the final DECISION block?).
5. Testing: unit-test the rewriter (mechanical) on fixture Markdown; how to test the build hook and
   the network lookup (mock).

## Approval and execution gate

Proposal (`draft`). Flesh out -> `to-review` -> `/plan-review` -> resolve OQs -> human approve ->
execute -> validate (suite green) -> commit (never push) -> `git mv` to executed/. Not auto-executed.
