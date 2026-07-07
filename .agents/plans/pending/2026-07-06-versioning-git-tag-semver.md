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
path settled with IPD-2's package layout) exposing `resolve_version(repo_root) -> str`:

1. If `git` is available AND `repo_root` is inside a git work tree of THIS project:
   run `git describe --tags --always --dirty --long`.
   - Exact tag, clean tree -> normalize `v1.0.0` -> `1.0.0`.
   - N commits after the tag, or dirty -> a PEP 440 local/dev version:
     `1.0.1.dev<N>+g<shortsha>` and, if dirty, append `.d<YYYYMMDD>` (e.g.
     `1.0.1.dev3+g5a1b2c3.d20260706`). (`1.0.1` = tag's next patch; dev of the UPCOMING release.)
   - No tags at all -> `0.0.0+g<shortsha>` (pre-baseline; should not happen after v1.0.0).
2. Else (no git, e.g. installed wheel or copied-out files) -> read the baked `VERSION` file.
3. `_framework_version()` in each tool = step 2 ONLY (read the neighboring `VERSION`). The
   resolver's git branch (step 1) is used by the build/release step and by the installer/CLI
   when they run from a git checkout, NOT by the copied-out tools.

State mapping for later `status` (IPD-2 consumes this; defined here for consistency):
`no VERSION file` -> not-installed; target `<` packaged -> stale; `==` -> current; `>` or a
`.dev`/`+local` version -> `ahead`/`dev`. PEP 440 ordering (packaging is stdlib-adjacent; we
implement a minimal, dependency-free compare of our own `MAJOR.MINOR.PATCH[.devN][+local]`
forms, since we control the format - no third-party `packaging` needed).

## Findings (why each change)

| ID | Sev | RR | Area | Finding |
|----|-----|----|----|---------|
| V-1 | Medium | Low | versioning | Hand-maintained `YYYYMMDD-NN` can be forgotten/stale; it is not PEP 440 valid (blocks PyPI); it cannot express "this clone differs from a release" (the clone-bug). |
| V-2 | Low | Low | consistency | `scan_secrets.py:462-463` docstring says VERSION is "two directories up"; the code is three (`.parent.parent.parent`). Doc bug; fix while here. |
| V-3 | Low | Low | docs | `YYYYMMDD-NN` scheme is described in README/ARCHITECTURE/index.md/release-notes workflow/installer; must migrate to semver (forward-facing docs only). |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | RR | Validation |
|------|--------|--------|-------|----|-----------|
| 1 | V-1 | Add the version resolver `resolve_version(repo_root)` with the algorithm above; dependency-free; unit-tested against faked `git describe` outputs (exact tag, N-ahead, dirty, no-tag, no-git). | new `versioning.py` + `tests/test_versioning.py` | Low | new tests pass; each described state maps to the specified string. |
| 2 | V-1 | Make `install-workflows.py:read_version` prefer the resolver when run from this project's git tree, else read the source `VERSION` file (back-compat). `--version` and summary use it. | `install-workflows.py` | Low | `install-workflows.py --version` prints resolved semver in a clean checkout; still prints the file value when run from a copied tree. |
| 3 | V-1 | Add a `regenerate VERSION from tag` step: a `make version-file` target (and later the build backend) that writes `resolve_version(.)` into `.agents/workflows/VERSION`. VERSION stays tracked but is now derived, not hand-edited. Document that maintainers do not hand-edit it. | `Makefile`, `.agents/workflows/VERSION` | Low | running it on a clean tagged tree writes `1.0.0`; on a dirty tree writes a `.devN` string. |
| 4 | V-2 | Fix the `scan_secrets.py` docstring "two" -> "three directories up". Tools otherwise UNCHANGED (still read neighboring `VERSION`). | `scan_secrets.py` | Low | grep shows "three"; tools' `--version` still works. |
| 5 | V-1 | Tag the baseline `v1.0.0` at the current clean `HEAD` as part of execution (after steps 1-4 land, so the tag includes the new machinery). Regenerate `VERSION` -> `1.0.0`. Update the `index.md` stamp to `1.0.0` and change the scheme note from `YYYYMMDD-NN` to semver. | git tag; `.agents/workflows/VERSION`; `index.md` | Low | `git describe` -> `v1.0.0`; VERSION == `1.0.0`; index stamp == `1.0.0`. |
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

- `tests/test_versioning.py`: resolve_version maps each faked `git describe` output (exact-tag,
  ahead-by-N, dirty, no-tag, no-git subprocess failure) to the exact specified string; the
  minimal PEP 440-ish comparator orders `1.0.0 < 1.0.1 < 1.0.1.dev3 < 1.1.0` correctly and
  classifies not-installed/stale/current/ahead.
- All existing `test_version_flag`s stay green (tools read neighboring VERSION; unchanged).
- `install-workflows.py --version` in a clean tagged checkout prints `1.0.0`.
- Full suite: `python3 -m unittest discover -s tests -t .` green (grows by the new file).
- Docs: no `YYYYMMDD-NN` scheme claim remains in forward-facing docs; historical untouched;
  em-dash sweep = 0 on changed files.

## Spec / documentation sync

Forward-facing docs migrate to semver (Step 6). DECISIONS gets D44 (Step 8). `VERSION` becomes
a derived artifact; CONTRIBUTING documents "do not hand-edit VERSION; it is generated from the
git tag." No user-visible workflow behavior changes.

## Open questions

1. Module home for the resolver: a top-level `versioning.py` now (imported by the installer),
   or wait for IPD-2's `agent_workflows/` package and put it there? Recommend a top-level
   `versioning.py` now; IPD-2 moves it into the package. (Assumption for execution.)
2. Baseline tag exactly `v1.0.0` at current `HEAD` after steps 1-4 land - confirm. (Spec says
   yes.)
3. Minimal comparator vs. vendoring nothing: confirmed we implement our own tiny compare over
   our controlled `MAJOR.MINOR.PATCH[.devN][+local]` format (no `packaging` dep). Flag if you'd
   rather accept the `packaging` dep (it is widely installed) - default is no dep.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution (run
`/plan-review` on it first), and it is NOT auto-executed. On approval: execute steps 1-8, run
validation, tag `v1.0.0`, then move this IPD to `.agents/plans/done/`. IPD-2 (distribution)
follows.
