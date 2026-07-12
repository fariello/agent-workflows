# Changelog

All notable changes to `agent-workflows` are recorded here. Versions are git-tag-driven
semantic versioning (see `RELEASING.md`); the authoritative "why" for decisions lives in
`DECISIONS.md`.

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
