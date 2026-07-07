# IPD-2: pip distribution + CLI + config + multi-repo wizard + cross-OS CI

- Date: 2026-07-07
- Concern: distribution / packaging / developer-experience (the main deliverable; IPD-1
  versioning was its prerequisite and is DONE)
- Scope: package the framework as a pip/pipx-installable wheel with a real CLI
  (`agent-workflows` / `aw` / `agentwf`), a JSON config under `~/.config/agent-workflows/`,
  a guided multi-repo setup wizard, deterministic setup-artifact creation on install, an
  accessible ANSI terminal UX, and a cross-OS CI matrix. Does NOT change what any workflow
  DOES, nor the per-repo self-contained install model, nor the stage-not-commit safety posture.
- Status: PENDING (plan-reviewed 2026-07-07, R-1..R-6 fixed; all 6 open questions resolved
  interactively 2026-07-07; awaiting final human go to execute; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Source spec: `docs/specs/2026-07-06-pip-distribution-and-multi-repo-setup.md` (this IPD
  expands that spec's 12-point IPD-2 checklist; all listed decisions are already resolved there).

## Goal

Make agent-workflows widely adoptable: today it is usable only by cloning the repo and running
`python3 /path/to/install-workflows.py` per target repo, with no memory of which repos a user
manages. After this IPD a newcomer can `pipx install agent-workflows`, run `aw setup` once, and
be guided through configuring their repo roots, installing the framework into each repo, and
learning how to run the workflows. An existing maintainer gets `aw install all` against a saved
repo list. It works on Linux, macOS, and Windows, verified in CI, with zero runtime dependencies.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md`. Binding here: P2 (honest docs), P3
  (self-documenting/learn-as-you-go - the CLI teaches), P4 (durable knowledge / DECISIONS),
  P6 (KISS + guard scope creep), P7 (solve the general case), P9 (design for the runner),
  P10 (safety/reversibility - stage-not-commit, ask-before-change).
- Zero-runtime-dependency is a documented de-facto standard (CONTRIBUTING, DECISIONS D-Q3, and
  reaffirmed by IPD-1 / D44). Build/dev tooling (`build`, a backend like `hatchling`) is
  dev-only and allowed.
- Plan lifecycle (D45): `.agents/plans/pending/` -> `reusable/` -> `executed/`; files named
  `YYYYMMDD-<slug>.md`. This IPD lands in `pending/`.
- Versioning (D44): git-tag-driven semver via `versioning.py:resolve_version`; baseline tag
  `v1.0.0` exists; `.agents/workflows/VERSION` is DERIVED (`make version-file`). `status`
  currency uses `versioning.py:status()` / `compare()` (the IPD-1 state mapping:
  not-installed / stale / current / ahead / dev / unknown).
- Current code to refactor:
  - `install-workflows.py` (repo root, ~1150 lines): the whole install engine. Key seams:
    `resolve_source_root()` at `:242` (SIBLING-source assumption to replace with
    `importlib.resources`), `build_install_plan()` `:269`, `parse_manifest()` `:286`,
    `collect_source_members()` `:332`, `generate_shim_members()` `:470`, `install_all()`
    `:684`, `read_version()` (already git-aware via IPD-1), `main()` `:1109`.
  - `install-workflows.sh` (root wrapper), `versioning.py` (root; IPD-1 resolver).
  - `tests/support.py`: `REPO_ROOT`, `INSTALLER`, `SCANNER`, ... are repo-root-relative and
    assume `install-workflows.py` at the root; 75 tests currently green.
  - No `pyproject.toml` and no `agent_workflows/` package exist yet.
- Type-annotation floor: the code uses `list[str]`, `Path | None`, etc. These are safe on 3.8
  ONLY because of `from __future__ import annotations` (stringized). Every new module MUST
  include that import to hold the 3.8 floor (Constraint).

## Key design decisions (already resolved in the spec; restated so plan-review can judge)

1. **Package layout: `agent_workflows/` importable package + `.agents/workflows/` as package
   data.** The CLI/engine code moves into an installable package `agent_workflows/`; the shipped
   workflow tree is included as package data and located at runtime via `importlib.resources`, so
   the CLI works from `site-packages` with no sibling-source assumption. The four COPIED-OUT
   tools still read their neighboring `VERSION` (they are loose files in a user repo, not
   importable) - unchanged.
2. **Three console scripts, one entry point** (spec OQ1, collision research resolved):
   `agent-workflows`, `aw`, `agentwf`, all -> `agent_workflows.cli:main`. Console-script names
   are independent of the PyPI dist name (`agent-workflows`).
3. **Zero runtime deps; JSON config; Python floor 3.8** (best-effort below CI). No TOML
   (`tomllib` is 3.11+). Build backend (`hatchling`) is dev-only.
4. **Two distinct verbs, one engine:** `install <dir>|all` (idempotent workhorse; NO `update`
   verb) and `setup` (guided front door) share ONE install engine. `uninstall <dir>` asks
   first, no `all`. `list` / `status`. NO `doctor` (its safety = preflight-warn+confirm in
   install/setup; its info folded into `status`). Bare `aw` = smart default (setup if
   unconfigured, else status + hints).
5. **Config** at `$XDG_CONFIG_HOME/agent-workflows/config.json` (fallback `~/.config/...`; never
   under `~/` directly): `{config_version:1, search_roots:[], repos:[], ignore:[],
   defaults:{backup:true, prune:true}}`. Paths stored `~`-preserved, expanded at use-time
   (tilde + Windows). `ignore` = fnmatch globs, discovery-only; `repos` is the allowlist; no
   persisted opt-out.
6. **Ship-vs-dev:** the wheel contains ONLY `.agents/workflows/` package data + the
   `agent_workflows/` CLI code. It EXCLUDES `docs/`, `prompts/`, `tests/`,
   `workflow-artifacts/`, and the meta docs (DECISIONS/ARCHITECTURE/CONTRIBUTING/
   GUIDING_PRINCIPLES/CITATION.cff/NOTICE). README + LICENSE ride in metadata as usual.
7. **Move deterministic setup artifacts into the engine** (Goal 8): plan lifecycle dirs, the
   `AGENTS.md` pointer block (already done by the installer), a `.gitleaksignore` baseline, and
   the secret-scan CI workflow. Stack-tailored `.gitignore`/CI and the lifecycle-contract prose
   stay with the LLM `/setup-repo`; the CLI MUST tell the user to run it.
8. **Back-compat:** keep `install-workflows.py` / `.sh` at the root as thin DEPRECATED shims that
   call the packaged CLI, so existing muscle-memory and any downstream automation still work.

## Findings (why each change; this is a build-out, so most are UNDER-SCOPE gaps the spec requires)

Severity = impact if the capability is missing; Remediation Risk = the Fix-Bar gate.

| ID | Sev | RR | Persona | Area | Finding |
|----|-----|----|---------|------|---------|
| P-1 | High | Low | stakeholder | packaging | No `pyproject.toml` / wheel exists; the tool is clone-only, a real adoption barrier (spec Problem). Under-scope: add packaging that ships `.agents/workflows/` as package data + the CLI, wired to IPD-1's resolver, zero runtime deps. |
| P-2 | High | Medium | architect | source lookup | `resolve_source_root()` (`install-workflows.py:242`) assumes the source sits next to the script (`Path(__file__).parent/.agents/workflows`). That breaks from `site-packages`. Under-scope: locate package data via `importlib.resources`, keep clone/`--source` back-compat. RR Medium: touches the core source-resolution path used by every install; mitigated by preserving both paths + tests. |
| P-3 | High | Medium | software-engineer | refactor | The whole engine is one root script; a package + CLI needs it importable as `agent_workflows`. Under-scope: move the engine into the package WITHOUT behavior change; leave root shims. RR Medium: a large move; mitigated by keeping functions/signatures stable and re-pointing tests, asserting identical install output (AC-2). |
| P-4 | Medium | Low | power-user | config | No config; the tool cannot remember a user's repos. Under-scope: JSON config module (read/write/migrate `config_version`), XDG-honoring, never under `~/`. |
| P-5 | Medium | Low | novice | wizard | No guided first-run. Under-scope: `setup` wizard (roots -> save config -> discover -> install -> teach + point to `/setup-repo`); idempotent/smart on re-run. |
| P-6 | Medium | Low | power-user | discovery | No multi-repo discovery. Under-scope: discovery per OQ4 (configured path with non-submodule `.git` = target, no descent; else immediate children; submodules skipped; recursive opt-in; report skipped/ignored). |
| P-7 | Medium | Low | stakeholder | currency | No `list`/`status`. Under-scope: `list` (per-repo installed version + currency via `versioning.status()`); `status` (currency summary + environment readout: Python, git, config location, packaged VERSION). |
| P-8 | Medium | Low | QA/QC | uninstall | No clean removal path. Under-scope: `uninstall <dir>` (ask-first, stage deletions of framework + our shims + AGENTS block + config entry; never touch user content; no `all`). |
| P-9 | Medium | Low | novice | setup-artifacts | Deterministic setup artifacts require the LLM `/setup-repo` today. Under-scope (Goal 8): the engine creates plan dirs + `.gitleaksignore` + secret-scan CI + AGENTS pointer on install, and prints "run `/setup-repo` for stack-tailored conformance." |
| P-10 | High | Medium | UI/UX (accessibility) | terminal UX | The CLI needs accessible ANSI output. Under-scope: a tiny color helper held to `assess/lenses/accessibility.md` (color never sole signal; honor NO_COLOR/FORCE_COLOR/TERM/isatty; degrade when piped/non-TTY). RR Medium on the usability axis: getting degradation wrong harms accessibility; mitigated by a NO_COLOR/non-TTY test (AC-15). |
| P-11 | High | Medium | testing/regression | cross-OS | No Windows/macOS verification. Under-scope: CI matrix ubuntu/macos/windows; build+import the wheel; fix Windows assumptions (python vs python3, path seps, exec bit, line endings). RR Medium (functionality): Windows path/exec-bit behavior may surface real bugs; that is the value of doing it, so do it, gated by CI. |
| P-12 | Medium | Low | software-engineer | test refactor | `tests/support.py` assumes the root script layout. Under-scope: re-point constants to the packaged layout + add tests for config, discovery, importlib.resources lookup, uninstall, NO_COLOR/non-TTY, ignore/skip reporting, artifact-move, wheel-file-list. |
| P-13 | Low | Low | novice | docs | README/CONTRIBUTING describe only clone-and-run. Under-scope: pipx + CLI as primary path (clone kept as dev path); `aw`-collision caveat; DECISIONS entry. |
| P-14 | Medium | Low | architect | ship-vs-dev gate | Nothing enforces that dev/meta content stays out of the wheel. Under-scope: a test that inspects the built wheel's file list and FAILS if docs/prompts/tests/workflow-artifacts/meta-docs are present (AC-11), and asserts empty runtime `dependencies` (AC-12). |
| P-15 | Medium | Medium | power-user | preflight safety | Naive users can foot-gun a batch install. Under-scope (ex-`doctor`): `install`/`setup` warn + confirm before changing anything (uncommitted changes in a target, non-git target, large batch, would-downgrade an `ahead` repo). RR Medium (usability): over-prompting annoys; mitigated by a `--yes` non-interactive escape and only warning on genuinely risky states. |
| R-1 | BLOCKER | Low | architect (plan-review) | 3.8 floor vs stdlib API | `importlib.resources.files()` (planned in A2/AC-8) was ADDED IN PYTHON 3.9; the plan's own floor is 3.8. On 3.8 `.files()` does not exist, so the CLI would crash on import/source-lookup - a normal-path crash on the declared floor, and a self-contradiction between two decided constraints. A backport (`importlib_resources`) is a runtime third-party dep, forbidden by the zero-dep rule. Fixed: A2 now uses `importlib.resources.files()` on 3.9+ with a 3.8-safe fallback (legacy `importlib.resources` path API, or resolving the package `__file__`-relative data dir), OR the floor is honestly stated. Verified live: `.files` present on this 3.14, absent on 3.8. |
| R-2 | Low | Low | software-engineer (plan-review) | artifact provenance | Batch E creates a `.gitleaksignore` baseline + secret-scan CI in TARGET repos; this repo already HAS its own `.gitleaksignore` and `.github/workflows/secret-scan.yml`. The plan did not say where the target templates come from. Fixed: E1 now specifies the templates are generated content / package data distinct from this repo's own files, and the ship-vs-dev test must not confuse them. |
| R-3 | Low | Low | software-engineer (plan-review) | layering | The engine's `install_all()` returns a per-FILE `(installed, skipped, conflicted)` 3-tuple (`install-workflows.py:684-689`), NOT the per-REPO installed/skipped/ignored/failed the CLI `install all` reports (AC-4/13). The plan conflated the two layers. Fixed: distinguished the engine's per-file result from the CLI's per-repo aggregation in D4. |
| R-4 | Medium | Low | QA/QC (plan-review) | partial-failure | `install all` over N repos did not specify behavior when one repo fails mid-batch. Silent abort-all or an ambiguous partial state would violate the "nothing silently passed over" criterion. Fixed: D4 now requires per-repo isolation - a failure is recorded and reported, the batch CONTINUES, and the exit code reflects any failure. |
| R-5 | Low | Low | security (plan-review) | secrets in config | Spec Non-goal: the config must never store secrets/sensitive data. The plan did not guard it. Fixed: C1 notes the schema is a fixed allowlist of non-sensitive keys (roots/repos/ignore/defaults) and a test asserts no unexpected/sensitive keys are persisted. |
| R-6 | Medium | Low | anti-regression (plan-review) | refactor safety | Batch A moves the entire behavior-critical install engine. The plan implied but did not NAME the regression gate. Fixed: A1/A4 now require the existing 75 tests act as the characterization pin - they must be green BEFORE the move (baseline) and green AFTER with identical behavior; any behavior diff is a blocker unless explicitly approved. |

## Proposed changes (ordered into buildable, independently-committable batches)

Each batch ends green (full suite passes) and is committed separately. Behavior-preserving
refactors (Batch A) come first so later batches build on stable seams. Every new module includes
`from __future__ import annotations` (3.8 floor).

### Batch A - package the engine (no behavior change)

| Step | Src | Change | Files | RR | Validation |
|------|-----|--------|-------|----|-----------|
| A1 | P-3,R-6 | FIRST confirm the existing 75 tests are green (the characterization baseline). Then create `agent_workflows/` package (`__init__.py` exporting `__version__` via the resolver). Move the install-engine functions from `install-workflows.py` into `agent_workflows/engine.py` (or split: `engine.py`, `manifest.py`) with UNCHANGED signatures/behavior. Move `versioning.py` -> `agent_workflows/versioning.py` (OQ4 resolved) and leave a 1-line root `versioning.py` re-export shim (`from agent_workflows.versioning import *`) so the build hook, `Makefile`, and any tests importing the old path still work. | new `agent_workflows/*`, moved `versioning.py` + root shim, moved engine code | Med | the same 75 tests green after re-point (A4), asserting identical behavior; any behavior diff is a blocker unless explicitly approved. |
| A2 | P-2,R-1 | Replace `resolve_source_root()`'s sibling assumption: add `packaged_source_root()` that locates the shipped `.agents/workflows/` from the installed package. 3.8-FLOOR-SAFE lookup: `importlib.resources.files()` is 3.9+; on 3.8 it does not exist and a backport is a forbidden runtime dep, so use a compatibility helper - prefer `importlib.resources.files("agent_workflows")` when available (3.9+), else resolve the data dir relative to the package `__file__` (`Path(agent_workflows.__file__).parent / "_data" / ".agents" / "workflows"`), which is 3.8-safe and works for a normal (non-zip) wheel install. Fall back to a clone/`--source` path for dev. (If a zipimport/zip-safe install must be supported, that raises the floor or needs the backport - call it out; default is the `__file__`-relative dir, and the wheel is not zip-safe.) The `.agents/workflows/` tree is included as package data (see Batch B). | `agent_workflows/engine.py`, `agent_workflows/_compat.py` | Med | a test installs from a simulated installed layout (no sibling source) and gets the full tree (AC-2, AC-8); the source-lookup helper is unit-tested; CI floor job (or a 3.8-syntax guard) exercises the non-`.files()` branch. |
| A3 | P-3 | Add `agent_workflows/cli.py:main(argv=None)` with an argparse subcommand skeleton (`install`, `setup`, `uninstall`, `list`, `status`; bare = smart default). For Batch A it wires ONLY `install <dir>` + `--version` to the moved engine (parity with today), so the package is runnable end-to-end early. | `agent_workflows/cli.py` | Low | `python -m agent_workflows --version` and `... install <tmp repo>` behave like today's installer. |
| A4 | P-12,P-3,R-6 | Re-point `tests/support.py` to import `agent_workflows.engine`/`cli` instead of loading `install-workflows.py` by path; the existing 75 tests are the regression gate and must assert IDENTICAL behavior (same install tree, shims, VERSION, staging). | `tests/support.py`, minor test edits | Low | the same 75 tests green against the package with no behavior diff. |
| A5 | P-3,#11 | Turn root `install-workflows.py` / `.sh` into thin DEPRECATED shims that print a one-line deprecation note (once) and delegate to `agent_workflows.cli:main(["install", ...])`, preserving today's flags. | `install-workflows.py`, `install-workflows.sh` | Low | old invocation still installs; deprecation note shown; installer tests (subprocess) still pass. |

### Batch B - packaging + ship-vs-dev gate

| Step | Src | Change | Files | RR | Validation |
|------|-----|--------|-------|----|-----------|
| B1 | P-1 | Add `pyproject.toml`, backend `hatchling` (dev-only). `[project]`: name `agent-workflows`, `requires-python = ">=3.8"`, EMPTY `dependencies`, `dynamic = ["version"]`. Version via a CUSTOM hatchling version-source/build hook that calls `agent_workflows.versioning.resolve_version(".")` and bakes the resolved value (matches `make version-file`; OQ2 resolved - reuse IPD-1's resolver, no `hatch-vcs`). `[project.scripts]`: `agent-workflows`/`aw`/`agentwf` = `agent_workflows.cli:main`. Ship the workflow tree via `[tool.hatch.build.force-include]` mapping the repo-root `.agents/workflows` -> `agent_workflows/_data/.agents/workflows` (OQ5 resolved; NO repo file move). EXCLUDE docs/prompts/tests/workflow-artifacts/meta-docs from the wheel. Non-zip-safe wheel (so the `__file__`/`_data/` lookup in A2 works). | `pyproject.toml`, `agent_workflows/_build_version.py` (hook) | Med | `python -m build` produces a wheel; `pip install <wheel>` in a fresh venv exposes `aw --version` printing the packaged VERSION (AC-1). |
| B2 | P-14 | Add a test that builds (or inspects a prebuilt) wheel and asserts its file list contains `agent_workflows/_data/.agents/workflows/...` + `agent_workflows/*.py` and does NOT contain `docs/`, `prompts/`, `tests/`, `workflow-artifacts/`, DECISIONS/ARCHITECTURE/etc.; and asserts runtime `dependencies` is empty/absent. | `tests/test_packaging.py` | Low | test passes on a built wheel; fails if dev content leaks (AC-11, AC-12). |

### Batch C - config + discovery

| Step | Src | Change | Files | RR | Validation |
|------|-----|--------|-------|----|-----------|
| C1 | P-4,R-5 | `agent_workflows/config.py`: `config_path()` (XDG-honoring, never `~/`), `load()`/`save()` (JSON, atomic write via temp-file + `os.replace`, create parent dirs), `migrate(config_version)`, path store-as-`~` / expand-at-use (tilde + Windows via `os.path.expanduser` + `expandvars`). Schema is a FIXED allowlist of non-sensitive keys `{config_version:1, search_roots, repos, ignore, defaults:{backup,prune}}`; no secret/sensitive field is ever persisted (spec Non-goal) and unknown keys on load are dropped or rejected. | `agent_workflows/config.py` | Low | test points `XDG_CONFIG_HOME` at a temp dir; save writes there; `~/` untouched; round-trip load == save (AC-3); a test asserts only the allowlisted keys are persisted (R-5). |
| C2 | P-6 | `agent_workflows/discovery.py`: per OQ4 - a configured path with a non-submodule `.git` is the target (no descent); else immediate children with a non-submodule `.git`; submodules (in the parent `.gitmodules`) skipped; recursive is an opt-in flag; `ignore` fnmatch globs applied to the env/`~`-expanded absolute path, discovery-only. Returns installed/skipped(reason)/ignored lists. | `agent_workflows/discovery.py` | Low | tests with a target repo, a submodule, and an ignore-matched dir assert correct classification (AC-13). |

### Batch D - CLI verbs + accessible UX + preflight

| Step | Src | Change | Files | RR | Validation |
|------|-----|--------|-------|----|-----------|
| D1 | P-10 | `agent_workflows/term.py`: a tiny ANSI helper. `should_color()` honors `NO_COLOR` (disable), `FORCE_COLOR` (enable), `TERM=dumb`, and `sys.stdout.isatty()`. Every status carries a WORD/symbol (OK/SKIP/FAIL/WARN), never color-only; no load-bearing dim/blink. Held to `assess/lenses/accessibility.md` (referenced). | `agent_workflows/term.py` | Med | test with `NO_COLOR=1` and with piped stdout asserts no ANSI escapes and that status words are present in plain text (AC-15). |
| D2 | P-7 | Wire `list` (configured/discovered repos + each repo's installed VERSION + currency via `versioning.status()` against the packaged VERSION) and `status` (currency summary + environment readout: Python version, git presence, config location, packaged VERSION). | `agent_workflows/cli.py` | Low | tests over temp repos assert the six currency states render with plain-text labels (AC-5). |
| D3 | P-5 | `setup` wizard: prompt for search roots (or `--root` non-interactively), save config, discover, drive the shared engine per-repo with consent (or `--yes`), then print orientation + "run `/setup-repo`". Re-run when configured = summarize + offer next action, no re-interview. | `agent_workflows/cli.py`, `agent_workflows/wizard.py` | Low | `setup --root <tmp> --yes` writes config and installs into discovered repos, skipping submodules/ignored (AC-10, AC-3). |
| D4 | P-7,#4,R-3,R-4 | `install all` drives the engine over the config `repos` allowlist (idempotent; one verb). NOTE the layering (R-3): the engine's `install_all()` returns a per-FILE `(installed, skipped, conflicted)` per repo; the CLI aggregates that into a per-REPO report of installed/skipped(submodule/not-git)/ignored/failed - nothing silent. Partial-failure (R-4): per-repo isolation - if one repo fails, record it, CONTINUE the batch, and set a non-zero exit code; never abort-all or leave an ambiguous partial state unreported. `install <dir>` with no config OFFERS `setup`. | `agent_workflows/cli.py` | Low | multi-temp-repo test asserts the per-repo report, idempotent re-run, and that a single repo failing does not stop the others and yields a non-zero exit (AC-4). |
| D5 | P-8 | `uninstall <dir>`: preflight-confirm (or `--yes`), stage removal of `.agents/workflows/`, the shims we generated, the `AGENTS.md` pointer block, and the repo's config entry; never touch user content; no `all`. | `agent_workflows/cli.py`, engine helper | Low | test (confirmation via flag) asserts framework gone, user files intact, config entry removed, staged-not-committed (AC-14). |
| D6 | P-15 | Preflight safety in `install`/`setup`: warn + confirm before changing anything on uncommitted changes in a target, a non-git target, a large batch, or a would-downgrade-an-`ahead`-repo. `--yes` bypasses for automation. | `agent_workflows/cli.py` | Med | tests assert a warning+abort without `--yes` on a would-downgrade / non-git case, and proceed with `--yes`. |
| D7 | P-5 | Bare `aw` (no subcommand) = smart default: run `setup` if unconfigured, else print `status` + short usage hints. | `agent_workflows/cli.py` | Low | test: bare invocation with no config routes to setup guidance; with config prints status. |

### Batch E - move deterministic setup artifacts into the engine

| Step | Src | Change | Files | RR | Validation |
|------|-----|--------|-------|----|-----------|
| E1 | P-9,R-2 | On install, the engine also creates in the TARGET repo (staged, idempotent): the plan lifecycle dirs `.agents/plans/{pending,reusable,executed}/` each with a `.gitkeep`; a `.gitleaksignore` baseline; the secret-scan CI workflow; (the `AGENTS.md` pointer already exists). The baseline/CI CONTENT is generated content or package-data templates authored for targets - distinct from THIS repo's own `.gitleaksignore` / `.github/workflows/secret-scan.yml` (R-2), which must not be shipped verbatim if they contain repo-specific entries. If a target already has any of these, do not overwrite (idempotent, respect existing). It does NOT do stack-tailored `.gitignore`/CI. The CLI prints "run `/setup-repo` for stack-tailored conformance." | `agent_workflows/engine.py`, template data | Low | post-install test asserts the artifacts exist, existing files are not clobbered, and the guidance string is emitted; re-run is quiet/idempotent (AC-16). |

### Batch F - cross-OS CI + docs + DECISIONS

| Step | Src | Change | Files | RR | Validation |
|------|-----|--------|-------|----|-----------|
| F1 | P-11 | Extend `.github/workflows/tests.yml` to a matrix ubuntu/macos/windows (reduced Python combos, floor-aware), run the suite, and `python -m build` + import the wheel on each OS. Fix Windows-specific test assumptions surfaced (python vs python3, path seps, exec bit, CRLF). | `.github/workflows/tests.yml`, tests | Med | CI green on all three OSes; wheel builds+imports (AC-7). |
| F2 | P-13 | Docs: README quick-start/install -> `pipx install agent-workflows` + CLI as the primary path (clone-and-run kept as the dev/source path); add the `aw`-collision caveat ("if `aw` is taken, use `agentwf` or `agent-workflows`"); update CONTRIBUTING (dev install `pip install -e .`, build, ship-vs-dev). | README.md, CONTRIBUTING.md | Low | grep: pipx/CLI documented; caveat present; em-dash sweep 0 (AC-9). |
| F3 | - | DECISIONS D46: record the packaging/CLI/config/wizard/CI decisions and the ship-vs-dev boundary. | DECISIONS.md | Low | entry present, dated, em-dash-free. |

## Deferred / out of scope (with reason)

| Item | RR | Axis | Reason | Later step |
|------|----|------|--------|-----------|
| Actual `twine upload` to PyPI | High | security/functionality | Publishing is a credentialed, irreversible, user-gated release action (spec Non-goal). This IPD builds + tests the wheel only. | A separate release-checklist step with credentials. |
| Central/symlinked shared copy across repos | n/a | - | Explicit spec Non-goal; each repo stays self-contained. | none |
| GUI/TUI wizard | n/a | - | Spec Non-goal; terminal CLI only. | none |
| Auto-commit/auto-push in targets | n/a | - | Spec Non-goal; stage-not-commit preserved. | none |
| Per-OS `command -v aw` / `Get-Alias aw` manual checks | Med | functionality | Needs real Mac/Windows shells; cannot be a unit test. | Pre-release checklist item; append to collision findings. |
| Full `pipx`-on-a-fresh-machine walkthrough | Med | functionality | Needs manual steps; spec says this is a release-checklist item, not an AC. | Release checklist. |
| Rolling the wheel/CLI conventions to the 27 downstream repos | Med | functionality | Downstream rollout is separate and user-gated (unchanged posture). | Post-release rollout. |

## Scope check

- **Over-scope guard:** NO `update` verb (install is idempotent), NO `doctor` (folded into
  status + preflight), NO third-party runtime deps, NO TOML, NO PyPI publish, NO central shared
  copy. Each avoided item is traceable to KISS/zero-dep/safety.
- **Under-scope guard:** the accessible-UX degradation (P-10), the ship-vs-dev wheel gate
  (P-14), the preflight safety (P-15), and the cross-OS CI (P-11) are REQUIRED acceptance
  criteria, not nice-to-haves, so they are in.

## Required tests / validation (mapped to the spec's 16 acceptance criteria)

- AC-1: `pip install <wheel>` in a fresh venv -> `aw --version` prints the packaged VERSION.
- AC-2: install from a simulated installed layout (no sibling source) into a temp git repo;
  assert the tree + a shim + VERSION match today's installer output.
- AC-3: `setup --root <tmp> --yes` (or config save) with `XDG_CONFIG_HOME` at a temp dir writes
  the config there; `~/` untouched.
- AC-4/13: `install all` over multiple temp repos (incl. a submodule and an ignore-matched dir)
  reports installed/skipped(reason)/ignored/failed; idempotent re-run.
- AC-5: `list`/`status` render the six currency states with plain-text labels + the environment
  readout.
- AC-6: all existing self-tests pass against the packaged layout.
- AC-7: CI green on ubuntu/macos/windows; wheel builds + imports on each.
- AC-8: source lookup works from an installed package (3.9+ via `importlib.resources.files()`;
  3.8-safe via the package-`__file__`-relative data dir - R-1); the compat helper is unit-tested.
- AC-9: docs describe pipx + CLI as primary; clone as dev.
- AC-10: non-interactive `setup --root <tmp> --yes` produces config + installs discovered repos,
  skipping submodules/ignored.
- AC-11: built-wheel file-list test excludes docs/prompts/tests/workflow-artifacts/meta-docs.
- AC-12: built-metadata runtime `dependencies` is empty/absent.
- AC-14: `uninstall <dir> --yes` removes framework + shims + AGENTS block + config entry, stages
  not commits, leaves user content.
- AC-15: `NO_COLOR=1` and piped-stdout runs emit no ANSI escapes; status words present in plain
  text.
- AC-16: post-install the deterministic artifacts exist and the "run `/setup-repo`" guidance is
  emitted.
- Full suite `python3 -m unittest discover -s tests -t .` green (grows substantially); em-dash
  sweep 0 on changed authored docs.

## Spec / documentation sync

README + CONTRIBUTING updated (F2). DECISIONS D46 (F3). ARCHITECTURE gains a short
packaging/CLI/config subsection and the ship-vs-dev boundary. The spec's Status advances to
"IPD-2 executed" on completion (append a note, do not rewrite history). No user-visible WORKFLOW
behavior changes (only distribution/UX).

## Open questions (all RESOLVED interactively 2026-07-07)

1. **Build backend - RESOLVED (user): `hatchling`** (dev-only). Clean dynamic-version hook and
   simple package-data include/force-include for our shape.
2. **Dynamic-version mechanism - RESOLVED (user): reuse IPD-1's resolver via a custom hatchling
   build/version hook** that calls `resolve_version` and bakes the same `VERSION` into the wheel
   at build time (matches `make version-file`). No `hatch-vcs`/`setuptools-scm`, no new build dep,
   single source of versioning truth.
3. **Import package name - RESOLVED (user): `agent_workflows`** (underscore; matches the
   `agent-workflows` dist name normalized, and `[project.scripts]` -> `agent_workflows.cli:main`).
4. **`versioning.py` relocation - RESOLVED (user): move to `agent_workflows/versioning.py` in
   Batch A, keeping a 1-line root re-export shim** (`from agent_workflows.versioning import *`) so
   the build hook, Makefile, and any tests importing the old path still work.
5. **`.agents/workflows/` package-data - RESOLVED (user): keep the tree at the repo root and
   `force-include` it into the wheel under `agent_workflows/_data/.agents/workflows/`.** No repo
   file moves; the dev/clone layout is unchanged; matches R-1's 3.8-safe `__file__`/`_data/`
   lookup.
6. **Batch granularity - RESOLVED (user): one commit per batch (A-F), full suite green at each
   boundary, do NOT push without asking** (same rhythm as IPD-1).

## Plan-review revisions applied (2026-07-07)

Hardened by `plan-review` before approval. The architecture (package + `.agents/workflows/` as
package data + one shared engine + three console scripts + JSON config, all zero-runtime-dep) was
verified sound against the source (`resolve_source_root:242`, `AGENTS_BEGIN:124`,
`install_all:684` returning a per-file 3-tuple, `main:1109`; no `pyproject.toml`/`agent_workflows/`
yet; this repo already has its own `.gitleaksignore` + `secret-scan.yml`). Findings fixed in place:

- R-1 (BLOCKER, Low RR): `importlib.resources.files()` is 3.9+ but the floor is 3.8; a backport is
  a forbidden runtime dep. A2 now uses `.files()` on 3.9+ with a 3.8-safe package-`__file__`-relative
  `_data/` fallback (non-zip wheel), the compat helper is unit-tested, and CI exercises the fallback.
- R-2 (Low): E1 clarifies target-repo `.gitleaksignore`/CI templates are generated/package-data
  content distinct from this repo's own files, and existing target files are not clobbered.
- R-3 (Low): D4 distinguishes the engine's per-file `install_all()` 3-tuple from the CLI's
  per-repo aggregation.
- R-4 (Medium, Low RR): D4 requires per-repo isolation on `install all` (a failure is recorded,
  the batch continues, exit code reflects failure).
- R-5 (Low): C1 pins a non-sensitive fixed-key schema and a no-secrets-persisted test.
- R-6 (Medium, Low RR): A1/A4 name the existing 75 tests as the pre/post characterization gate for
  the engine move; behavior diffs are blockers.

No scope or approach changed; the review made the source-lookup floor, the config safety, the
partial-failure semantics, and the refactor regression gate precise. Reviewing is not executing.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution (run
`/plan-review` on it first), and it is NOT auto-executed. On approval: execute batches A-F in
order, running the full suite green at each batch boundary, commit per batch (do NOT push without
asking), then move this IPD to `.agents/plans/executed/` and record DECISIONS D46. The actual
PyPI publish remains a separate, credentialed, user-gated step.
