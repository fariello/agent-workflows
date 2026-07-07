# Spec: pip-installable distribution + config-driven multi-repo setup

- Date: 2026-07-06
- Status: DRAFT, spec-editor pass complete 2026-07-06 (all open questions resolved). Ready to
  split into IPD-1 (versioning) + IPD-2 (distribution) and run /plan-review on each before build.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Problem / why

Today agent-workflows is usable only by cloning the repo and running
`python3 /path/to/agent-workflows/install-workflows.py` from each target repo. That is fine
for the maintainer but a real adoption barrier for anyone else: they must clone, remember a
path, and re-run it per repo with no memory of which repos they manage. To be widely
distributable it should be `pip`/`pipx`-installable, expose a real CLI, remember the user's
repos in a config file (never polluting `~/`), and guide a newcomer through setup, install,
and use. It must work on Linux, macOS, and Windows, verified in CI.

## Goals

1. **Installable from PyPI**: `pipx install agent-workflows` (or `pip install`) provides a
   CLI, with the workflow files shipped inside the wheel as package data.
2. **A guided first-run wizard** (`setup`) that: asks where the user keeps repos (one or more
   search roots and/or an explicit repo list), discovers git repos under those roots, offers
   to install/update agent-workflows in each (with per-repo consent), saves the answers to a
   config file, and walks the user through what the workflows are and how to run them.
3. **Fast operational verbs** for people already set up: `install <dir>` / `install all`
   (idempotent: one command handles both fresh install and update, like today's installer;
   there is NO separate `update` verb), `uninstall <dir>` (asks before removing; no `all`),
   `list`, and `status`. NO separate `doctor` command (see OQ5): its safety value lives as
   preflight warnings + confirmation inside `install`/`setup`, and its environment readout
   lives in `status`.
4. **A JSON config file under `~/.config/agent-workflows/`** (honoring `XDG_CONFIG_HOME`),
   storing `config_version`, search roots, an explicit repo allowlist, an `ignore` glob list,
   and defaults (backup/prune). No persisted opt-out (the `repos` allowlist + `ignore` list
   cover exclusion). NEVER writes to `~/` directly.
5. **Thorough setup that also degrades to quick**: the wizard is thorough (discovers repos,
   looks for stale/legacy layouts, asks questions) but if a repo is already configured the
   user can run a one-line install/update without the full interview.
6. **Cross-platform**: works and is regression-tested on Linux, macOS, and Windows via GitHub
   Actions on every push.
7. **Preserve the current per-repo model**: each repo still gets its own self-contained
   `.agents/workflows/` copy + generated shims (so bodies work in any agent, offline). The
   installer still stages-not-commits and never pushes.
8. **Move the deterministic setup artifacts into the CLI (conservative-to-moderate)**: the
   fixed-template, always-the-same artifacts that `/setup-repo` handles today move into the
   install engine so a repo is more useful out of the box - the plan/IPD lifecycle dirs
   (`.agents/plans/pending/` + `reusable/` + `executed/`), the `AGENTS.md` pointer block, a `.gitleaksignore`
   baseline, and the secret-scan CI workflow. The STACK-TAILORED and judgment/consent-heavy
   parts stay with the LLM `/setup-repo` (project-type detection, tailoring `.gitignore`/CI to
   the stack, reconciling existing conflicting config, the lifecycle contract prose). The CLI
   MUST tell the user to run `/setup-repo` for that judgment layer.
9. **Accessible, polished terminal UX**: the CLI uses ANSI color and formatting for a
   professional feel, held to the terminal-accessibility rubric in
   `.agents/workflows/assess/lenses/accessibility.md` (referenced, not restated): color is
   never the sole signal (status carries a word/symbol too), no load-bearing dim/blink, honor
   `NO_COLOR`/`FORCE_COLOR`/`TERM`/`isatty()` and degrade to plain text when piped or
   non-TTY. This is a requirement, not a nicety.

## Ship-vs-dev separation (meta-repo clarity)

This repo is a meta-repo: it both IS the product and is where the product is developed. Two
content classes, previously implicit (because "clone the repo" gave you everything), must
become explicit once we build a wheel:

- **Shipped product (goes in the wheel as package data):** the `.agents/workflows/` tree only
  (bodies, lenses, personas, tools, `index.md`, `VERSION`), plus the CLI/installer Python code.
- **Development / meta content (stays in the git repo, EXCLUDED from the wheel):** `docs/`
  (incl. `docs/specs/`), `prompts/` (origin/reference material), `tests/`, `workflow-artifacts/`
  (this repo's own review runs), and the meta docs (`DECISIONS.md`, `ARCHITECTURE.md`,
  `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`, `CITATION.cff`, `NOTICE`). `README.md` and
  `LICENSE` are included in the sdist/wheel metadata as usual.

Keeping `docs/specs/` and `prompts/` at the repo root is CORRECT (the `spec` workflow itself
names `docs/specs/` as a valid home; `prompts/README.md` already marks that dir as historical
reference). It is not a convention violation. The packaging config MUST explicitly include only
the shipped product and exclude the dev/meta content, so a user's `pip install` never drags in
development cruft. This is an acceptance criterion, not a nicety.

## Non-goals

- NOT changing what the workflows DO or their content (this is distribution/packaging + a
  wizard, not a workflow-behavior change).
- NOT a central/symlinked single copy shared across repos (each repo stays self-contained).
- NOT auto-committing or auto-pushing in target repos (unchanged safety posture).
- NOT a GUI/TUI; the wizard is a terminal CLI (agent-executable prose wizard stays too).
- NOT publishing to PyPI as part of this work by default (build + test the wheel; the actual
  `twine upload` is a separate, credentialed, user-gated release step).
- NOT storing any secret or per-project sensitive data in the config.

## Users

- **New adopter** (primary): has never used the toolkit; wants `pipx install ...` then a
  wizard that sets up their repos and teaches them the basics.
- **Existing maintainer** (the current user): many repos under one or more roots; wants
  `install all` and a saved repo list, no ~/ pollution.
- **CI / non-interactive**: must be able to install into a named repo non-interactively
  (flags, no prompts) for scripting.

## Acceptance criteria (testable)

1. `pip install .` (from a build) yields a console-script command that runs; `--version`
   prints the framework VERSION read from packaged data (not a filesystem-relative guess).
2. Running the CLI from an arbitrary directory (NOT the source checkout) can install the
   workflow files into a target repo: the target gets `.agents/workflows/` (all bodies,
   lenses, personas, tools, index.md, VERSION) + regenerated shims, identical in content to
   today's installer output. Verified by a test that installs into a temp git repo and
   asserts the tree + a shim + VERSION match.
3. `setup` (non-interactive mode, flags supplied) writes a JSON config file to
   `$XDG_CONFIG_HOME/agent-workflows/config.json` (or `~/.config/...` when XDG unset) with the
   given roots/repo list; nothing is written directly under `~/`. Verified by a test that
   points XDG_CONFIG_HOME at a temp dir and asserts the file lands there and `~/` is untouched.
4. `install all` installs/updates every repo in the config `repos` allowlist (idempotent; one
   verb, no separate `update`), and reports per-repo installed/skipped(submodule|not-git)/
   ignored/failed (nothing silently passed over). Verified in a test with multiple temp repos.
5. `list` shows configured/discovered repos with each repo's installed framework version and
   its currency (not-installed / stale / current / ahead|dev) vs. the packaged VERSION, using
   the IPD-1 version resolver's state mapping. `status` summarizes currency AND carries the
   environment readout (Python version, git presence, config location, packaged VERSION) - the
   info that a separate `doctor` would have shown (there is no `doctor` command).
6. All existing self-tests still pass, refactored to target the packaged layout (no reliance
   on `install-workflows.py` sitting at the repo root). New tests cover config read/write,
   discovery, and the package-data source lookup.
7. GitHub Actions runs the suite on ubuntu/macos/windows and builds+imports the wheel; green
   on all three. Windows-specific issues (python vs python3, path separators, exec bit, line
   endings) are handled.
8. Source-tree lookup uses `importlib.resources` to locate the packaged `.agents/workflows/`
   tree so the CLI works from `site-packages` (no reliance on a sibling source dir). The four
   COPIED-OUT tools keep reading their neighboring `VERSION` file (they are loose files in a
   user repo, not importable package modules); VERSION values come from the IPD-1 resolver.
   The CLI works both as an installed package AND (back-compat) from a clone.
9. Docs (README quick-start/install, CONTRIBUTING) describe the pip install + CLI as the
   primary path; the clone-and-run path remains documented as the dev/source path.
10. Non-interactive `setup --root <tmp> --yes` (the automatable core of first-run) produces a
    config file and installs into the git repos discovered under `<tmp>`, skipping submodules
    and `ignore` matches. Verified by a test. (The full `pipx`-on-a-fresh-machine walkthrough
    is a release-checklist item, NOT a spec acceptance criterion, since it needs manual steps.)
11. The built wheel contains ONLY the shipped product: `.agents/workflows/` package data + the
    CLI code. It does NOT contain `docs/`, `prompts/`, `tests/`, `workflow-artifacts/`, or the
    meta docs. Verified by a test that inspects the built wheel's file list (ship-vs-dev gate).
12. Config is JSON (stdlib only); no runtime third-party dependency is declared in the wheel
    (verified by asserting an empty/omitted `dependencies` list in the built metadata).
13. `install all` reports every repo it installed, skipped (submodule / not-a-git-repo), or
    ignored (matched `ignore`), so nothing is silently passed over. Verified by a test with a
    target repo, a submodule, and an `ignore`-matched repo.
14. `uninstall <dir>` removes the framework from a repo (`.agents/workflows/`, the shims we
    generated, the `AGENTS.md` pointer block) and the repo from the config `repos` list, ONLY
    after an explicit confirmation; it stages deletions and never commits; user content is
    untouched. Verified by a test (with the confirmation auto-supplied via a flag).
15. The CLI honors `NO_COLOR` and non-TTY output (plain text, no ANSI escapes) and never uses
    color/dim as the sole carrier of meaning. Verified by a test that runs a command with
    `NO_COLOR=1` and with stdout piped, asserting no raw escape sequences and that status words
    (e.g. OK/SKIP/FAIL) are present in plain text.
16. Installing into a repo also creates the deterministic setup artifacts (plan lifecycle
    dirs, `AGENTS.md` pointer, `.gitleaksignore` baseline, secret-scan CI) per Goal 8, and the
    CLI output points the user to run `/setup-repo` for stack-tailored conformance. Verified by
    a test asserting the artifacts exist post-install and the guidance string is emitted.

## Constraints

- **Zero-dependency, stdlib-only, everywhere (DECIDED).** No runtime dependencies for the CLI
  host OR the shipped workflow tools. Config is **JSON** (stdlib `json`, works on the whole
  floor; hand-editable enough), NOT TOML (tomllib is 3.11+ and adding `tomli` would break the
  zero-dep promise). Build/dev tooling (`build`, a backend like `hatchling`) is dev-only, fine.
- **Python floor 3.8 (DECIDED), best-effort below CI.** The floor is 3.8. CI verifies the
  lowest version the runners provide (likely 3.9); 3.8 is EOL (Oct 2024) so it is claimed as
  expected-but-untested, the same honesty pattern already used for the current claim. The
  shipped tools already avoid runtime 3.9+/3.10+/3.11+ features (annotations are stringized via
  `from __future__ import annotations`); the CLI host must hold the same 3.8-safe bar.
- No dependency additions for the shipped runtime unless explicitly accepted (packaging/build
  deps like `build`/`hatchling` are dev-only, fine).
- Honor `XDG_CONFIG_HOME`; fall back to `~/.config`; never write under `~/` directly.
- Preserve installer safety: stage-not-commit, backups, dry-run, prune-scoped-to-namespace.
- Preserve the VERSION single-source-of-truth and the manifest-driven shim generation.
- No em dashes in authored Markdown (house rule).

## Open questions (for spec-editor / plan-review)

1. **CLI command name - RESOLVED** (independent collision research: GPT-5.5, 2026-07-06;
   raw findings in the untracked `tmp/cli-aw-name-collision-findings.md`). Ship THREE
   `[project.scripts]` aliases, all -> `agent_workflows.cli:main`:
   - `agent-workflows` (canonical, unambiguous, tab-completes, never collides),
   - `aw` (ergonomic daily driver),
   - `agentwf` (short fallback).
   Findings that settled it:
   - ActivityWatch is NOT a hard collision (it ships `aw-qt`/`aw-server`/`aw-cli`/`aw-watcher-*`,
     never a naked `aw`); only a soft namespace association. My earlier ActivityWatch worry was
     wrong.
   - The one verified hard collision is niche: npm `@williambeto/ai-workflow` documents `aw` as
     a binary alias. Rare install base; fully mitigated by the two fallback aliases.
   - Soft/terminology notes (not command clashes): a PyPI package literally named `aw` (no
     verified console-script), and GitHub's "Agentic Workflows" shipped as the `gh aw`
     subcommand - a terminology overlap in our exact space, worth awareness for naming/SEO but
     not a naked-command collision.
   - No verified default-OS or default-PowerShell-alias collision; still run `Get-Alias aw` /
     `command -v aw` on each real OS before public release.
   REQUIRED docs caveat (README + CLI help): "If `aw` is already used by another tool on your
   system, use `agentwf` or `agent-workflows`."
2. **Config format / floor - RESOLVED:** JSON (stdlib), zero-dep, floor 3.8 (best-effort
   below CI). See Constraints.
3. **Python floor - RESOLVED:** 3.8 (see Constraints).
4. **Discovery + ignore - RESOLVED.** Per configured path: if it has a non-submodule `.git`,
   that dir is the target and we do NOT descend; else scan immediate children with a
   non-submodule `.git`. Submodules (listed in the parent `.gitmodules`) are skipped;
   independent nested repos (real `.git` dir, not in `.gitmodules`) under a non-git root are
   valid targets. Recursive is an opt-in flag, not default. The config `ignore` list uses
   `fnmatch`-style glob patterns (`*`, `?`, `[seq]`) matched against the `~`/env-expanded
   absolute path; `ignore` applies to discovery only, not to an explicit `install <dir>`.
   `install all` MUST report every repo it skipped or ignored (so the user sees what was not
   touched). No persisted opt-out state: the config `repos` list IS the allowlist.
5. **Keep `install-workflows.py`/`.sh` at the root** as a thin back-compat shim that calls the
   packaged CLI. RESOLVED: keep as a deprecated shim.
6. **Doctor - RESOLVED (naive-user-first):** NO separate `doctor` command. `install`/`setup`
   run preflight sanity checks and warn + confirm before changing anything (uncommitted
   changes, non-git target, large batch, would-downgrade-an-`ahead`-repo); `status` carries
   the environment readout (Python version, git presence, config location, packaged version).
7. **CLI setup vs LLM `/setup-repo` - RESOLVED (complement, with a shared engine).** Design:
   `install` and `setup` are DISTINCT commands sharing ONE install engine.
   - `install <dir>|all` = the per-repo workhorse (idempotent install+update). If run with no
     config, it OFFERS to run `setup`.
   - `setup` = the guided front door: ask for search roots, save config, discover repos, then
     drive the same install engine, then print orientation (what the workflows are, how to run
     them, and to run the LLM `/setup-repo` for stack-tailored conformance). Re-running `setup`
     when already configured is idempotent/smart: summarize existing config and offer the next
     useful action, do not re-interview.
   - Bare `aw` (no subcommand) = smart default: run `setup` if unconfigured, else show `status`
     + short usage hints. This is the lost-user rescue.
   - The CLI (host-level, deterministic, multi-repo) and the LLM `/setup-repo` (in-agent,
     stack-tailored, judgment) COMPLEMENT each other; the CLI cross-references `/setup-repo`.

## Sequencing: two IPDs (decided during spec-editor session 2026-07-06)

The versioning migration is a big, cross-cutting, prerequisite lift (it touches all four
tools' `_framework_version()`, the installer's `read_version`, and ~9 docs, and the
distribution work's `list`/`status` currency depends on it). It is therefore split out as its
OWN, FIRST IPD so the distribution work builds on a settled version scheme rather than a
moving target.

- **IPD-1 (first): versioning migration.** Replace the hand-maintained `YYYYMMDD-NN` string
  with git-tag-driven semantic versions (baseline tag `v1.0.0`, since the toolkit has been in
  production use across 27+ repos), via `setuptools-scm`/`hatch-vcs` (dev/build-time only,
  zero runtime deps for users). Version resolution is dirty/distance-aware: a clean tagged
  commit reports `1.0.0`; a working tree ahead-of-tag or with local edits reports a
  `1.0.1.devN+g<sha>[.dYYYYMMDD]` local version, so a clone that differs from a release can
  never silently report a clean version (this fixes the observed clone-bug where a stale tag
  masked uncommitted changes). At build time the resolved version is baked into the shipped
  `VERSION`/`_version.py`; at runtime `_framework_version()` returns the baked value and MAY
  recompute live when running from a git working tree (the dev/clone case). `status` compares
  PEP 440 versions (ordered: not-installed / stale / current / ahead|dev). Independently
  shippable and valuable on its own. Its own plan-review + tests.
- **IPD-2 (after IPD-1): pip distribution + CLI + config + multi-repo wizard + cross-OS CI**,
  i.e. the rest of THIS spec. Builds on the version scheme IPD-1 establishes.

### IPD-2 scope checklist (the crux, consolidated - draft IPD-2 by expanding each bullet)

This is the authoritative one-place summary of IPD-2 so it can be drafted fresh against the
post-IPD-1 code without reconstructing decisions. Every bullet is already decided above; this
is the index.

1. **Packaging.** `pyproject.toml` (hatchling or setuptools) that ships `.agents/workflows/`
   as PACKAGE DATA and the CLI code; wires the build backend to IPD-1's version resolver so the
   wheel bakes the semver. Three `[project.scripts]`: `agent-workflows`, `aw`, `agentwf`, all
   -> `agent_workflows.cli:main`. Zero runtime deps declared. Ship-vs-dev: wheel contains ONLY
   the shipped product (exclude docs/prompts/tests/workflow-artifacts/meta-docs); a test
   inspects the built wheel's file list.
2. **Source lookup via importlib.resources.** The installer/CLI locates the packaged
   `.agents/workflows/` tree from `site-packages` (replacing `install-workflows.py:218`'s
   sibling assumption). Copied-out tools keep reading their neighboring `VERSION` (unchanged).
3. **Config** at `$XDG_CONFIG_HOME/agent-workflows/config.json` (fallback `~/.config/...`;
   NEVER under `~/`). JSON schema: `{config_version:1, search_roots:[...], repos:[...],
   ignore:[...], defaults:{backup,prune}}`. Paths stored `~`-preserved, expanded at use-time
   (tilde + Windows). `ignore` = fnmatch globs, discovery-only. No persisted opt-out; `repos`
   is the allowlist.
4. **CLI command set + design (OQ7 synthesis):** `install`, `setup`, `uninstall`, `list`,
   `status`; NO `update`, NO `doctor`. One shared install engine. `install <dir>|all` =
   workhorse (idempotent install+update); with no config it OFFERS setup. `setup` = guided
   front door (roots -> save config -> discover -> install -> teach + point to `/setup-repo`);
   idempotent/smart on re-run. `uninstall <dir>` asks first, stages, removes framework + shims
   + AGENTS block + config entry; no `all`. Bare `aw` = smart default (setup if unconfigured,
   else status + hints). Bidirectional handoff (setup<->install).
5. **Discovery (OQ4):** configured path with non-submodule `.git` = target, no descent; else
   immediate children with non-submodule `.git`; submodules (in parent `.gitmodules`) skipped;
   recursive opt-in flag. `install all` reports installed/skipped/ignored.
6. **Move deterministic setup artifacts into the install engine (Goal 8):** plan dirs,
   AGENTS pointer, `.gitleaksignore`, secret-scan CI. Stack-tailored `.gitignore`/CI +
   judgment stay in LLM `/setup-repo`; CLI tells the user to run it.
7. **Preflight safety (naive-user, ex-`doctor`):** `install`/`setup` warn + confirm before
   changing anything (uncommitted changes, non-git target, large batch, would-downgrade-an-
   ahead-repo).
8. **Accessible ANSI CLI (Goal 9):** color/format held to `assess/lenses/accessibility.md`
   (color never sole signal, honor NO_COLOR/FORCE_COLOR/TERM/isatty, no load-bearing dim,
   degrade when piped/non-TTY).
9. **Cross-OS CI:** GitHub Actions matrix ubuntu/macos/windows (reduced Python combos), builds
   + imports the wheel, runs the suite; fix Windows-specific test assumptions (python vs
   python3, path seps, exec bit, line endings). Wheel-file-list ship-vs-dev test.
10. **Test refactor:** `tests/support.py` constants (INSTALLER/SCANNER/... REPO_ROOT-relative)
    move to target the packaged layout, not `install-workflows.py` at the repo root; new tests
    for config, discovery, importlib.resources lookup, uninstall, NO_COLOR/non-TTY output,
    ignore/skip reporting, artifact-move.
11. **Back-compat:** keep `install-workflows.py`/`.sh` at the root as a thin deprecated shim
    that calls the packaged CLI.
12. **Docs:** README quick-start/install -> pipx + CLI as primary path (clone-and-run kept as
    dev path); CONTRIBUTING; the `aw`-collision caveat; DECISIONS entry.

## Next steps

1. (done) `/advise spec-editor` interrogation of this spec.
2. Write IPD-1 (versioning); `/plan-review`; implement; tag `v1.0.0`.
3. Write IPD-2 (distribution/CLI/config/wizard/CI); `/plan-review`; implement in batches.
