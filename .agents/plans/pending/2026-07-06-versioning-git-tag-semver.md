# IPD-1: versioning migration - git-tag-driven semver (baseline v1.0.0)

- Date: 2026-07-06
- Concern: versioning / release engineering (prerequisite for pip distribution, IPD-2)
- Scope: the version SCHEME and how it is produced/consumed. Touches the four tools'
  `_framework_version()`, the installer's `read_version`, `VERSION`, `index.md` stamp, a new
  version resolver, and forward-facing docs. Does NOT touch workflow behavior, the CLI/config/
  wizard (that is IPD-2), or historical records.
- Status: PENDING (awaiting human approval + plan-review; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Source spec: `docs/specs/2026-07-06-pip-distribution-and-multi-repo-setup.md` (Sequencing:
  this is IPD-1, first, before IPD-2 distribution).

## Goal

Replace the hand-maintained `YYYYMMDD-NN` version string with a git-tag-driven semantic
version (baseline `v1.0.0`), resolved dirty/distance-aware so a checkout that DIFFERS from a
release can never silently report a clean version, baked into the shipped `VERSION` file that
the tools already read. This is safer than a hand string (cannot be forgotten or go stale),
user- and PyPI-friendly (real semver), and it is the prerequisite the distribution work
(IPD-2: `list`/`status` currency, wheel-baked version) builds on. It also fixes the observed
clone-bug where a stale hand-string masked uncommitted/ahead-of-release changes.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md`. Binding here: P2 (honest docs), P4 (durable
  knowledge / append-only DECISIONS), P6 (KISS), P8 (single source of truth), P9 (design for
  the runner). Zero-runtime-dependency is a documented de-facto standard (CONTRIBUTING,
  DECISIONS D-Q3); build/dev tooling may add dev-only deps.
- Plan lifecycle: `.agents/plans/pending/` -> `.agents/plans/done/` (repo uses `done/`).
- VERSION single source of truth: `.agents/workflows/VERSION` (currently tracked, hand-edited,
  value `20260704-06`), mirrored as a comment in `index.md:3-4`.
- Runtime version consumers (must keep working): the four tools' `_framework_version()` at
  `scan_secrets.py:459/467`, `run_checks.py:497/504`, `setup_tools.py:41/49`,
  `bench_env.py:165/173` - all read `Path(__file__).resolve().parent.parent.parent / "VERSION"`
  (3 dirs up). Installer `read_version(source_root)` at `install-workflows.py:133-149`; used at
  `:1006` (summary) and `:1074` (`--version`).
- Self-tests: `tests/` stdlib unittest; each tool has a `test_version_flag` asserting stdout ==
  `(.agents/workflows/VERSION).read_text().strip()`.
- No tags exist yet (`git describe` returns a bare sha). `v1.0.0` is the baseline (toolkit has
  been in production across 27+ repos, well past 0.x).

## Key design decision (the "why", so a later reader/plan-review can judge it)

**The tools stay dumb; the intelligence lives in build/install.** Once copied into a user's
repo, a tool is a loose file with no git and no package metadata, so it MUST get its version
from the `VERSION` file sitting next to it (the existing 3-dirs-up read). We keep that. What
changes is only how `VERSION` gets its VALUE: instead of hand-editing, a **version resolver**
computes it from `git describe` at build/release time and writes it into `VERSION`. So:

- `VERSION` remains the runtime source of truth read by tools and by clone-users. It stays
  tracked (so a plain `git clone` and the file-copy install both have a value with no build
  step), but it becomes DERIVED: a release/build step regenerates it from the tag, and it is no
  longer hand-edited.
- The tools do NOT gain git/importlib/`setuptools-scm` logic (that would bloat 4 files and
  break when copied out). Only the resolver (one new helper) knows about git.

This keeps the change KISS and confined, and preserves the file-copy install model.

## The version resolver (concrete algorithm, so it is testable)

Add `agent_workflows/_versioning.py` (or a top-level `versioning.py` for now; final module
path settled with IPD-2's package layout) exposing `resolve_version(repo_root) -> str`.

**Parse the ACTUAL `git describe --tags --always --dirty --long` output** (verified against
real git during plan-review; the `--long` form ALWAYS includes the distance and gsha, even at
the exact tag):

- Tagged commit, clean tree: `v1.0.0-0-gd644d2d` (distance is `-0-`). "Exact release" is
  detected by **distance == 0 AND not dirty** -> normalize the tag `v1.0.0` -> `1.0.0`.
- Tagged commit, DIRTY (uncommitted edits at the release commit): `v1.0.0-0-gd644d2d-dirty`.
  distance == 0 BUT dirty -> NOT a clean release -> a dev version (this is the clone-bug case:
  a release checkout with local edits must not report `1.0.0`).
- N>0 commits after the tag: `v1.0.0-2-g49f2bdc` (and `-dirty` suffix if also dirty).
- No tags at all: `--long` degrades to a bare short sha `d644d2d` (no `v`, no `-N-g`). If the
  tree is ALSO dirty, git appends `-dirty` to the bare sha, e.g. `9042038-dirty` (verified live
  on this repo during plan-review, 2026-07-06). Handle this shape separately AND strip/detect the
  trailing `-dirty` so the bare-sha branch does not mis-read `9042038-dirty` as the sha.

Resolution rules (produce PEP 440-valid strings):

1. If `git` is available AND `repo_root` is inside a git work tree of THIS project, run the
   describe command and branch on the parsed (tag, distance, sha, dirty):
   - **distance == 0 and not dirty** -> `<tag without leading v>` (e.g. `1.0.0`). Clean release.
   - **distance > 0, or dirty (at any distance)** -> a PEP 440 dev+local version:
     `<next-patch>.dev<N>+g<shortsha>[.dYYYYMMDD]` where:
       - `<next-patch>` = the tag with PATCH incremented by 1 (e.g. tag `1.0.0` -> `1.0.1`),
         because this is the dev of the UPCOMING release, and this deliberately-chosen bump is
         recorded so it is not ambiguous;
       - `<N>` = the commit distance (use `0` for the distance==0-but-dirty case);
       - `+g<shortsha>` local segment from the describe sha;
       - `.dYYYYMMDD` appended (inside the local segment) ONLY when dirty, using UTC date.
     Examples: `1.0.1.dev2+g49f2bdc` (2 ahead, clean); `1.0.1.dev0+gd644d2d.d20260706`
     (at the tag but dirty); `1.0.1.dev2+g49f2bdc.d20260706` (2 ahead and dirty).
   - **no tags at all** (bare-sha shape): first strip a trailing `-dirty` if present and set the
     dirty flag from it, then -> `0.0.0+g<shortsha>` when clean, or `0.0.0+g<shortsha>.dYYYYMMDD`
     when dirty (pre-baseline; should not occur after v1.0.0 is tagged, but must not crash and
     must not silently drop the dirty signal). NOTE: the real dirty-no-tags form is
     `<shortsha>-dirty` (e.g. `9042038-dirty`), NOT `g<shortsha>` - prefix the `g` ourselves.
2. Else (git missing, the `git describe` subprocess raises OR exits non-zero - e.g. `fatal: not a
   git repository` on an installed wheel or the copied-out files in a user repo) -> read the
   baked `VERSION` file (existing behavior). Both the exception and the non-zero-exit paths route
   here.
3. `_framework_version()` in each tool = step 2 ONLY (read the neighboring `VERSION`). The
   resolver's git branch (step 1) is used by the build/release step and by the installer/CLI
   when they run from a git checkout, NOT by the copied-out tools.

**Comparator + state mapping** for later `status` (IPD-2 consumes this; defined here so the
format and its ordering are fixed at the source). We control the version format, so we
implement a small, dependency-free comparator over exactly our own shape - NOT a general PEP
440 parser (that would need the third-party `packaging` lib, which the zero-dep rule forbids).
Precise rules:

- Parse a version into `(release_tuple, dev, is_local)` where `release_tuple` = `(MAJOR, MINOR,
  PATCH)` as ints, `dev` = the `.devN` integer or `None`, and `is_local` = whether a `+...`
  segment is present. The `+local` segment (gsha, `.dDATE`) is **compared as presence only, not
  parsed** - two dev builds of the same base are both simply "dev", we do not order by sha/date.
- Ordering for currency: compare `release_tuple` first; if equal, a version WITH `.dev` sorts
  BEFORE the same release without dev (PEP 440 semantics: `1.0.1.dev2 < 1.0.1`). This matters so
  a `1.0.1.dev2` dev build is not mistaken for the released `1.0.1`.
- `status(target, packaged)` states:
  - target has no `VERSION` file / unreadable -> **not-installed**
  - target `release_tuple` < packaged (or equal release but target `.dev` and packaged clean)
    -> **stale**
  - target `is_local` OR target has `.dev` (a dev/dirty build, regardless of comparison) ->
    **dev** (reported distinctly; it is "not a clean release," which is the honest signal for a
    clone-installed copy)
  - target > packaged (newer release) -> **ahead**
  - otherwise equal clean release -> **current**
- Edge: if EITHER side is a `0.0.0+...` pre-baseline or an unparseable legacy `YYYYMMDD-NN`
  string (a repo installed before this migration), report **unknown** rather than guessing, so
  a pre-migration target is never falsely called stale/current.

## Findings (why each change)

| ID | Sev | RR | Area | Finding |
|----|-----|----|----|---------|
| V-1 | Medium | Low | versioning | Hand-maintained `YYYYMMDD-NN` can be forgotten/stale; it is not PEP 440 valid (blocks PyPI); it cannot express "this clone differs from a release" (the clone-bug). |
| V-2 | Low | Low | consistency | `scan_secrets.py:462-463` docstring says VERSION is "two directories up"; the code is three (`.parent.parent.parent`). Doc bug; fix while here. Verified during plan-review. |
| V-3 | Low | Low | docs | `YYYYMMDD-NN` scheme is described in README/ARCHITECTURE/index.md/release-notes workflow/installer; must migrate to semver (forward-facing docs only). Note: release-notes.md already partly mentions SemVer (line 27-28); make semver the primary scheme there. |
| V-4 | Medium | Low | correctness (plan-review) | The resolver algorithm was underspecified against REAL `git describe --long` output: (a) `--long` always emits `-0-g<sha>` at the exact tag, so "exact" = distance==0, not "no suffix"; (b) the tagged-but-dirty case (`-0-...-dirty`, the clone-bug) had no defined output; (c) no-tags degrades to a bare sha with a different shape. Fixed: the algorithm now parses the real forms with all cases pinned (see resolver section). |
| V-5 | Medium | Low | correctness (plan-review) | The `status` comparator over `.devN+local` was hand-waved as "PEP 440 ordering." A full PEP 440 parse would need the `packaging` dep (forbidden). Fixed: defined a minimal comparator over our OWN controlled format (`+local` compared as presence only; `.devN` sorts before the release; explicit not-installed/stale/dev/ahead/current/unknown mapping incl. legacy `YYYYMMDD-NN` -> unknown). |
| V-6 | Low | Low | release hygiene (plan-review) | Step 5 said "tag" without specifying annotated vs lightweight. Fixed: use an ANNOTATED tag (`git tag -a`), and commit steps 1-4 before tagging so the tree is clean (else describe reports -dirty). |
| V-7 | Medium | Low | correctness (plan-review, 2nd pass) | The no-tags branch was specified for a plain bare sha `d644d2d`, but the REAL dirty-no-tags `git describe --long` form appends `-dirty` (verified live: `9042038-dirty` on this repo before v1.0.0 exists). A parser keying off `-g` or treating the whole token as the sha would crash or mis-parse `9042038-dirty` and, worse, DROP the dirty signal - the exact clone-bug this IPD exists to fix, in the pre-baseline window. Fixed: bare-sha branch strips/detects trailing `-dirty`, emits `0.0.0+g<sha>.dYYYYMMDD` when dirty; test matrix grows to 7 inputs. |
| V-8 | Low | Low | correctness (plan-review, 2nd pass) | Fallback trigger was "no git / subprocess fails," ambiguous about a non-zero `git describe` exit (`fatal: not a git repository`). Fixed: both the raised-exception and the non-zero-exit paths explicitly route to the VERSION-file fallback (step 2). |
| V-9 | Low | Low | anti-regression (plan-review, 2nd pass) | Step 2 makes `install-workflows.py:read_version` git-aware; the installer tests run in a non-git temp dir and rely on the file value. Fixed: pinned a characterization requirement - `read_version` from a non-git tree MUST still return the file value (copied-tree path must not regress). |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | RR | Validation |
|------|--------|--------|-------|----|-----------|
| 1 | V-1,V-7,V-8 | Add the version resolver `resolve_version(repo_root)` with the algorithm above; dependency-free; unit-tested by FEEDING the parser the exact real `git describe --long` strings (do not shell out in the unit test). Seven inputs: `v1.0.0-0-gd644d2d` (clean release -> `1.0.0`); `v1.0.0-0-gd644d2d-dirty` (release+dirty -> `1.0.1.dev0+gd644d2d.dYYYYMMDD`); `v1.0.0-2-g49f2bdc` (2 ahead -> `1.0.1.dev2+g49f2bdc`); `v1.0.0-2-g49f2bdc-dirty` (2 ahead + dirty -> `1.0.1.dev2+g49f2bdc.dYYYYMMDD`); bare sha `d644d2d` (no tags, clean -> `0.0.0+gd644d2d`); bare sha + dirty `9042038-dirty` (no tags, dirty -> `0.0.0+g9042038.dYYYYMMDD`) [V-7]; and a stubbed subprocess raising/non-zero-exit -> falls back to reading VERSION [V-8]. | new `versioning.py` + `tests/test_versioning.py` | Low | new tests pass; each of the seven inputs maps to the specified string; the `.dYYYYMMDD` cases assert the prefix/shape (inject or tolerate the date), not a literal date. |
| 2 | V-1,V-9 | Make `install-workflows.py:read_version` prefer the resolver when run from this project's git tree, else read the source `VERSION` file (back-compat). `--version` and summary use it. Preserve the copied-tree/non-git path: from a non-git dir it MUST still return the file value [V-9 characterization]. | `install-workflows.py` | Low | `install-workflows.py --version` prints resolved semver in a clean checkout; still prints the file value when run from a copied/non-git tree (existing installer tests stay green). |
| 3 | V-1 | Add a `regenerate VERSION from tag` step: a `make version-file` target (and later the build backend) that writes `resolve_version(.)` into `.agents/workflows/VERSION`. VERSION stays tracked but is now derived, not hand-edited. Document that maintainers do not hand-edit it. | `Makefile`, `.agents/workflows/VERSION` | Low | running it on a clean tagged tree writes `1.0.0`; on a dirty tree writes a `.devN` string. |
| 4 | V-2 | Fix the `scan_secrets.py` docstring "two" -> "three directories up". Tools otherwise UNCHANGED (still read neighboring `VERSION`). | `scan_secrets.py` | Low | grep shows "three"; tools' `--version` still works. |
| 5 | V-1 | Tag the baseline as an ANNOTATED tag `git tag -a v1.0.0 -m "v1.0.0"` at the clean commit that includes steps 1-4 (annotated, not lightweight: carries date/message and is what IPD-2's build backend prefers). Regenerate `VERSION` -> `1.0.0`. Update the `index.md` stamp to `1.0.0` and change the scheme note from `YYYYMMDD-NN` to semver. NOTE: tagging requires a committed, clean tree (commit steps 1-4 first), else describe reports `-dirty`. | git tag; `.agents/workflows/VERSION`; `index.md` | Low | `git describe --tags` -> `v1.0.0-0-g...`; resolver -> `1.0.0`; VERSION == `1.0.0`; index stamp == `1.0.0`. |
| 6 | V-3 | Migrate forward-facing docs from `YYYYMMDD-NN` to semver: README (install/versioning), ARCHITECTURE (versioning section), CONTRIBUTING (note VERSION is tag-derived, not hand-edited), the `release-notes` workflow body (it decides version bumps - point it at semver + tags). Leave DECISIONS dated entries and `.agents/plans/done/*` UNTOUCHED (append-only history, P4). | README, ARCHITECTURE, CONTRIBUTING, release-notes.md | Low | grep: no `YYYYMMDD-NN` scheme claim in forward-facing docs; historical records unchanged; em-dash sweep 0. |
| 7 | V-1 | Update tests: each tool's `test_version_flag` still asserts stdout == neighboring `VERSION` (unchanged mechanism); add `tests/test_versioning.py`; adjust any test that hard-codes `20260704-06` to read `VERSION` instead. | `tests/*` | Low | full suite green. |
| 8 | - | Add DECISIONS entry (D44) recording the scheme change, the resolver algorithm, `v1.0.0` baseline, and why tags over hand-string/SHA. | DECISIONS.md | Low | entry present, dated, em-dash-free. |

## Deferred / out of scope

- The actual `setuptools-scm`/`hatch-vcs` build-backend wiring and `pyproject.toml`: DEFERRED to
  IPD-2 (packaging). IPD-1 delivers the resolver + tag + derived VERSION so IPD-2 can wire the
  backend to it. Rationale: keep IPD-1 shippable without introducing the packaging surface.
  (Not a Remediation-Risk deferral; a scoping/sequencing choice, recorded so it is not dropped.)
- `list`/`status` currency UI: DEFERRED to IPD-2 (this IPD only defines the state mapping the
  resolver enables).

## Scope check

- Over-scope guard: deliberately NOT adding a third-party `packaging` dep (we implement a tiny
  compare over our own controlled format), NOT teaching the four tools git (they stay file
  readers), NOT wiring the build backend yet. Each avoided item is traceable to KISS/zero-dep.
- Under-scope guard: the resolver's dirty/dev states and the no-git fallback are REQUIRED (they
  are the whole point - fixing the clone-bug and surviving packaging), so they are in.

## Required tests / validation

- `tests/test_versioning.py`:
  - resolve_version maps each of the seven real `git describe --long` inputs (Step 1) to the
    exact specified string, INCLUDING the dirty-no-tags `9042038-dirty` -> `0.0.0+g9042038.dDATE`
    case [V-7] and a stubbed subprocess raising/exiting non-zero -> VERSION fallback [V-8];
  - the comparator orders `1.0.1.dev2 < 1.0.1 < 1.1.0` (dev sorts before its release) and
    ignores the `+local` segment for ordering;
  - `status(target, packaged)` returns the specified state for each case: no-file ->
    not-installed; older release -> stale; a `.dev`/`+local` target -> dev; newer -> ahead;
    equal clean -> current; a legacy `YYYYMMDD-NN` target -> unknown.
- All existing `test_version_flag`s stay green (tools read neighboring VERSION; unchanged).
- Installer characterization [V-9]: `read_version` invoked with a non-git source root still
  returns the file value (the existing installer tests, which run in a temp dir, must stay green);
  the git-aware branch only activates inside this project's real git tree.
- `install-workflows.py --version` in a clean tagged checkout prints `1.0.0`.
- Full suite: `python3 -m unittest discover -s tests -t .` green (grows by the new file).
- Docs: no `YYYYMMDD-NN` scheme claim remains in forward-facing docs; historical untouched;
  em-dash sweep = 0 on changed files.

## Spec / documentation sync

Forward-facing docs migrate to semver (Step 6). DECISIONS gets D44 (Step 8). `VERSION` becomes
a derived artifact; CONTRIBUTING documents "do not hand-edit VERSION; it is generated from the
git tag." No user-visible workflow behavior changes.

## Open questions

1. Module home for the resolver: **RESOLVED (user, 2026-07-06): top-level `versioning.py` now**
   (imported by the installer). IPD-2 relocates it into the `agent_workflows/` package.
2. **RESOLVED (user, 2026-07-06): tag `v1.0.0`**, annotated, on `main` at the commit that lands
   steps 1-4, message `"v1.0.0 - first tagged release; git-tag-driven versioning"`.
3. **RESOLVED (user, 2026-07-06): our own tiny comparator, NO `packaging` dependency** (preserves
   the zero-runtime-dependency promise; the format is fully controlled).

## Plan-review revisions applied (2026-07-06)

Hardened by `plan-review` before approval. The architecture (tools-stay-dumb + one resolver)
was verified sound - the tools' 3-dirs-up VERSION read and the file-copy install model make it
the correct, low-risk shape. Fixes applied in place (all Low Remediation Risk):

- V-4: rewrote the resolver algorithm against REAL `git describe --tags --always --dirty --long`
  output (captured live during review). The `--long` form always includes `-<distance>-g<sha>`,
  so "exact release" = distance==0 AND not dirty; the tagged-but-dirty case (the clone-bug) now
  has a defined `1.0.1.dev0+g<sha>.dDATE` output; the no-tags bare-sha shape is handled.
- V-5: replaced "PEP 440 ordering" hand-wave with a concrete, dependency-free comparator over
  our own format (`+local` = presence only; `.devN` sorts before its release) and an explicit
  state mapping including a legacy-`YYYYMMDD-NN` -> unknown guard, so a pre-migration target is
  never falsely classified.
- V-6: Step 5 now specifies an ANNOTATED tag and requires committing steps 1-4 first (clean tree
  before tagging).
- Tightened Step 1 and the validation section to test the six exact describe strings and the
  comparator/state cases (feed strings to the parser; do not shell out in unit tests).

No scope or approach changed; the review only made the resolver and comparator precise enough to
build and test unambiguously. Reviewing is not executing.

### Second pass (2026-07-06, after open-question resolution)

Re-reviewed once all three open questions were resolved. All plan claims re-verified against
source (`versioning.py` absent; VERSION == `20260704-06`; `scan_secrets.py:463` docstring says
"two" while the other three tools correctly say "three"; no tags). Live-captured
`git describe --tags --always --dirty --long` on the current dirty, untagged tree = `9042038-dirty`.
Findings fixed in place (all Low Remediation Risk):

- V-7: the dirty-no-tags describe form appends `-dirty` to the bare sha (`9042038-dirty`), which
  the prior spec did not account for; a naive parse would crash or silently drop the dirty signal
  (the clone-bug, in the pre-baseline window). Resolver bare-sha branch now strips/detects
  `-dirty` and emits `0.0.0+g<sha>.dDATE` when dirty; test matrix grew from six to seven inputs.
- V-8: the VERSION-file fallback now explicitly covers BOTH a raised subprocess exception AND a
  non-zero `git describe` exit.
- V-9: pinned an installer characterization requirement so the git-aware `read_version` change
  cannot regress the copied-tree/non-git path (must still return the file value there).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution (run
`/plan-review` on it first), and it is NOT auto-executed. On approval: execute steps 1-8, run
validation, tag `v1.0.0`, then move this IPD to `.agents/plans/done/`. IPD-2 (distribution)
follows.
