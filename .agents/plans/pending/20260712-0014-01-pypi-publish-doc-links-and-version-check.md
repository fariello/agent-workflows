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
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-01). Key decision taken: build-time rewrite via a hatch build hook on a COPY so the source
  README keeps GitHub-correct relative links and only the published artifact gets absolute tagged
  URLs. Awaiting flesh-out.
- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): fleshed out against the real packaging
  setup (hatchling; readme=README.md static; [project.urls] Repository; version resolver). Chose the
  hatchling metadata-hook mechanism + a testable pure-function rewriter. OQs leaned. Promoted to
  to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- `pyproject.toml`: `readme = "README.md"` (:9) is the PyPI long-description; `dynamic = ["version"]`
  (:7); `[project.urls] Repository = "https://github.com/fariello/agent-workflows"` (:30-31) gives
  owner/repo without parsing a git remote. `[tool.hatch.version] source = "code", path =
  "hatch_build.py"` (:42) - `hatch_build.py` today is ONLY a version source (exposes `VERSION`).
- To rewrite the long-description at build time, use a hatchling **metadata hook**
  (`hatchling.metadata.plugin.interface.MetadataHookInterface`, registered via
  `[tool.hatch.metadata.hooks.custom]`): move `readme` to `dynamic` and have the hook compute the
  long-description = rewrite(README.md text). This transforms only the built artifact's metadata; the
  source `README.md` file on disk is untouched. The hook can reuse the same repo (`hatch_build.py`
  can host both the version `VERSION` and the metadata hook class, or a sibling module).
- Version + tag: `agent_workflows/versioning.resolve_version()` yields the build version; the release
  TAG for links is `v<version>` (annotated tags are `v1.1.0` per D44). The rewriter pins links to
  that tag.
- PyPI latest-version lookup: no runtime deps allowed (D46), so use stdlib `urllib` against the JSON
  API `https://pypi.org/pypi/<name>/json` (or the simple index), parse `info.version` /
  `releases`. Must degrade gracefully (offline, unpublished 404, timeout).
- House rule: no em dashes in authored Markdown.

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

1. Build-time rewrite via a hatchling metadata hook on the long-description COPY; source `README.md`
   untouched. 2. Scope = the rendered long-description (`.md`); no HTML/docs tree.

## Proposed changes (ordered, validatable)

1. **Pure-function link rewriter** in a new module (e.g. `agent_workflows/pypi_links.py`, stdlib
   only): `rewrite_relative_links(markdown: str, owner: str, repo: str, ref: str) -> str`. Rewrites
   ONLY relative, repo-internal Markdown links/images to absolute GitHub URLs pinned to `ref`:
   - doc/link targets -> `https://github.com/<owner>/<repo>/blob/<ref>/<path>`
   - image targets (by extension: png/jpg/jpeg/gif/svg/webp) -> `.../raw/<ref>/<path>`
   Leave untouched: absolute `http(s)://` links, `mailto:`, pure `#anchor` links, and protocol-
   relative `//` links. Normalize `./` and resolve `../` against the README's location; a link that
   escapes the repo root is left as-is and noted. Pure and side-effect-free -> unit-testable.
2. **Hatchling metadata hook** (`MetadataHookInterface` in `hatch_build.py` or a sibling, registered
   via `[tool.hatch.metadata.hooks.custom]`): set `readme`/long-description dynamically to
   `rewrite_relative_links(read(README.md), owner, repo, ref="v"+VERSION)`. Owner/repo parsed from
   `[project.urls] Repository`; `ref` from the resolved version's tag. The source README file is never
   modified. Move `readme` into `[project] dynamic` accordingly.
3. **PyPI latest-version helper** in `agent_workflows/versioning.py` (or a small `pypi.py`):
   `latest_pypi_version(name, timeout=...) -> Optional[str]` via stdlib `urllib` against
   `https://pypi.org/pypi/<name>/json`. Returns None on offline/404/timeout/parse-failure (never
   raises). A helper `next_version_ok(proposed, published) -> bool` (proposed must be `>= published`).
4. **Wire the version check into `/release-review`** (Section 6 compatibility-packaging-release, which
   already owns packaging/release): when the repo publishes to PyPI (detected via pyproject
   `[project] name` + a PyPI hit), report the currently-published version and assert the proposed next
   version is `>= published`, surfacing a finding if not. Degrade gracefully / skip when offline or
   unpublished. (Prose wiring; the helper does the lookup.)
5. **Tests + docs + DECISIONS.** Unit-test the rewriter on fixture Markdown (relative doc -> blob,
   image -> raw, absolute/anchor/mailto left alone, `../` escape left alone, deterministic); test the
   PyPI helper with a mocked `urllib` (success, 404, timeout -> None); optionally a build smoke test
   asserting the built long-description contains an absolute URL. Document the behavior (README /
   ARCHITECTURE packaging section); DECISIONS entry (Dnn).

## Open questions (v1 leans for review)

1. **Which links: RESOLVED lean** - only relative repo-internal links/images; leave
   absolute/anchor/mailto/protocol-relative alone; a `../`-escaping link is left as-is and noted.
   Confirm.
2. **Owner/repo/ref derivation: RESOLVED lean** - owner/repo from `[project.urls] Repository`
   (fallback to git remote), ref = `v<resolved-version>`. If Repository is not a GitHub URL, SKIP
   rewriting (leave links) and note it. Confirm.
3. **blob vs raw: RESOLVED lean** - image extensions -> `/raw/<ref>/`; everything else -> `/blob/<ref>/`.
   Confirm the extension set.
4. **Where the version check surfaces: RESOLVED lean** - Section 6 (compatibility/packaging/release),
   which already owns release readiness; also feed the "next version" candidate to the release-notes /
   Section 9 version bump. Confirm vs the final DECISION block.
5. **Build-copy vs metadata hook: RESOLVED** - a hatchling METADATA HOOK computing the dynamic
   long-description is the clean "on a copy" mechanism (no source file rewritten, no separate build/
   dir to manage). Confirm this is acceptable vs. a pre-build script writing a temp file.
6. Should the rewriter also fix links in additional bundled `.md` if a project sets a multi-file long
   description? (Lean: v1 handles the single declared long-description file only; PyPI renders one.)

## Approval and execution gate

Proposal (`draft`). Flesh out -> `to-review` -> `/plan-review` -> resolve OQs -> human approve ->
execute -> validate (suite green) -> commit (never push) -> `git mv` to executed/. Not auto-executed.
