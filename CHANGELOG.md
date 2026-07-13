# Changelog

All notable changes to `agent-workflows` are recorded here. Versions are git-tag-driven
semantic versioning (see `RELEASING.md`); the authoritative "why" for decisions lives in
`DECISIONS.md`.

## 1.2.1 (pending) - install pre-flight and versioning fixes

Patch release fixing install-path bugs found by using 1.2.0. Not yet cut.

- Fixed: the installer stamped the wrong version into target repos. `.agents/workflows/VERSION`
  was baked at `1.1.0` even in the `v1.2.0` release, and the installer copies that file into each
  target. The baked VERSION is now re-baked from the intended release version and committed before
  tagging (bake-then-tag), and a test guards against a stale/dev baked value. (The 1.2.0 PyPI wheel
  was unaffected; its version is resolver-computed.)
- (Pending in this patch) `aw install` now runs the full git-diagnostics pre-flight (parity with the
  deprecated installer), and the diagnostics no longer offer a no-op "git pull" for a repo that is
  merely dirty from untracked files and already in sync.
- Internal: fixed wall-clock-proximity flakiness in the plan-filename normalizer tests (they now use
  today-relative dates); no product behavior change.

## 1.2.0 - first PyPI publish

This is the first release of `agent-workflows` published to PyPI. The project has been
git-tag-released since `v1.0.0` and used across multiple repositories before this publish, so
the PyPI history begins mid-story at `1.2.0` (continuing the existing `v1.0.0` -> `v1.1.0` tag
line) rather than at `1.0.0`. Numbering it `1.0.0` would make `1.0.0` refer to two different
trees (the existing git `v1.0.0` tag and a much newer PyPI build), which the project's
versioning decisions (DECISIONS D44/D50/D51/D74) deliberately avoid.

Highlights since `v1.1.0` (all backward-compatible, hence a MINOR bump):

- Release consent decision tree (close-out / release-candidate / full release) and a
  release-candidate version convention (`vX.Y.Z-rc.N`), with an rc-aware version resolver.
- A standing agent execution contract in the managed pointer block, plus enforcement in the
  plan-review workflows; MUST-mirror rules for private "brain"-dir plans and walkthroughs.
- Mirroring of the workflow pointer into existing `CLAUDE.md` / `GEMINI.md` so it reaches
  Claude Code and default Gemini.
- A new `data-modeling` assess lens and sharpened UX/data-modeling guiding principles.
- A `.agents/docs/` bucket standard (research / walkthroughs / specs / prompts / roadmaps);
  the reference prompt library and design specs were consolidated under `.agents/docs/`.
- A `/verify-execution` workflow and an `auto-approved` plan-readiness status.

## Earlier (git tags, not on PyPI)

- `v1.1.0`, `v1.0.0` - git-tagged releases prior to PyPI publication. See `git log` and
  `DECISIONS.md` for the full history.
