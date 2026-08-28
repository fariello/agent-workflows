# Contributing

This repo's value is disciplined, honest documentation, so the one rule that matters
most is: keep the docs in sync with what the framework actually does.

## Adding a workflow: the guided way

The fastest path is the `/scaffold` wizard (`.aw/system/workflows/scaffold/scaffold.md`):
it asks what to create (an `assess-*` lens, a standalone workflow, or a command),
generates it from the existing pattern, wires the manifest, and regenerates the shims.
The manual checklist below is what `/scaffold` automates: follow it if you prefer to do
it by hand.

## Doc-sync checklist: when you add or rename a workflow

The authoritative rules for how workflows are structured live in `ARCHITECTURE.md`
(see its "Capability layout" section) and `.aw/system/workflows/index.md` (the manifest
format). Do not restate those here; follow them, and use this as the step list:

1. Add or rename the workflow subdirectory under `.aw/system/workflows/<capability>/`.
2. Update the manifest row(s) in `.aw/system/workflows/index.md` (keep the
   `command | body | lens | description` columns stable).
3. For an `assess-<concern>` concern, add the lens file under
   `.aw/system/workflows/assess/lenses/`; for an `advise-<persona>` persona, add the charter
   under `.aw/system/workflows/advise/personas/`. Add the catalog row and reference the file
   in the manifest `lens` column. These catalog rows collapse into the single `/assess`
   and `/advise` commands (they do not each get their own shim).
4. Regenerate the per-tool slash-command shims by running the installer
   (`install-workflows.py`, at the repo root); do not hand-edit the generated shims in
   `.opencode/commands/` or `.claude/commands/`.
5. Confirm `README.md` and `ARCHITECTURE.md` still describe the current set accurately.
6. If a decision changed the design, add a dated entry to `DECISIONS.md`. Never rewrite
   existing dated entries to match a later layout; the log is history (see
   `GUIDING_PRINCIPLES.md` P4).

## File Classification and Ownership

To keep the repository clean and avoid accidental commits or drift, every file belongs to a defined category and owner tool:

| Category | Locations | Git Policy | Managing Tool |
|---|---|---|---|
| **Source** | `agent_workflows/`, `tools/`, `.aw/system/workflows/`, `tests/` | Tracked | Developers / git |
| **Generated** | `.opencode/commands/`, `.claude/commands/`, `.aw/system/VERSION`, `.aw/records/plans/INDEX.*`, `.aw/records/research/INDEX.*` | Tracked | `aw install`, `aw index plans`, `aw index research`, `make version-file` |
| **Records** | `.aw/records/` (`plans/`, `specs/`, `research/`, `backlog/`, `comms/`, `prompts/`) | Tracked (or companion-routed) | `aw ipd`, `aw backlog`, `aw research`, `aw specs` |
| **Config** | `.aw/config/config.json`, `.aw/config/local-leaks-allowlist.toml` | Tracked | `aw config`, `aw sanitize --configure` |
| **Local Config** | `.aw/config/local.json`, `~/.config/agent-workflows/` | Gitignored | `aw config`, user edits |
| **Runtime / State** | `.aw/state/` (`scratch/`, `durable/`, migration journals) | Strictly gitignored | `aw migrate-layout`, `aw install` |

### Regenerating Derivative Artifacts

Never hand-edit generated files. Use the owning CLI verb:

- **Command Shims (`.opencode/commands/`, `.claude/commands/`)**: `aw install .` or `python3 install-workflows.py`.
- **Plans Manifest (`.aw/records/plans/INDEX.json`, `INDEX.md`)**: `aw index plans`.
- **Research Manifest (`.aw/records/research/INDEX.json`, `INDEX.md`)**: `aw research index`.
- **IPD Checklists and Verification IDs (`E-*`, `V-*`)**: `aw ipd sync <plan.md>`.
- **Version Metadata (`.aw/system/VERSION`)**: `make version-file VERSION=<X.Y.Z>`.

## Secret scanning

Committed secrets and PII/PHI must never enter this repo, including its git history.

- **CI enforces it:** `.github/workflows/secret-scan.yml` runs `gitleaks` (full history)
  on every push and pull request.
- **Scan locally before pushing:** run `gitleaks detect --source . --no-banner`, or the
  built-in `python3 .aw/system/workflows/assess/tools/scan_secrets.py --repo .` (a
  dependency-free safety net that also auto-uses gitleaks/detect-secrets if installed).
- **False positives:** add the finding's fingerprint (printed by gitleaks) to the
  `.gitleaksignore` baseline at the repo root. Do not suppress a real secret: rotate
  it at the provider first, then purge it from history (`git filter-repo`/BFG).
- For a deeper pass, run `/assess secrets`.

## No local leaks in tracked files (DECISIONS D92, D93)

This is a public package and repo. No tracked file may embed the maintainer's local
filesystem layout, other local accounts, private repo names, hostnames, session ids, or
personal handles: use a portable placeholder, a repo-relative path, or `$HOME`/a config
value instead. The only tolerated personal identifiers are the public author email and the
public repo origin URL. This class of leak is NOT caught by secret scanners (gitleaks etc.).

- **Check it yourself:** `aw check-local-leaks .` (working tree),
  `aw check-local-leaks . --history` (git history, bounded with `--max-commits N`),
  `aw check-local-leaks . --wheel dist/<built>.whl` (the shipped surface). Without the CLI:
  `python3 -m agent_workflows check-local-leaks .`. For an interactive pass that enumerates
  emails/usernames and asks which are intended-public, run `/assess local-leaks`.
- **Fix helper:** `aw sanitize . --fix --dry-run` previews rewriting home-style absolute paths
  to `~` (drop `--dry-run` to apply; interactive per file unless `--yes`). Identity/private-repo/
  session tokens have no safe generic rewrite and are reported for manual editing, never auto-changed.
- **Enforced:** a pre-commit hook and `tests/test_local_leaks.py` run the same unified
  `agent_workflows.leak_sanitizer` engine (`local_leaks` re-exports it, DECISIONS D96); the
  `local-leaks` CI workflow is the push-time backstop.
- **Allowlist:** add genuinely-public values to `.aw/config/local-leaks-allowlist.toml` (committed,
  travels, CI-deterministic). Your own machine-specific tokens go in the never-committed
  `~/.config/agent-workflows/local-leaks-hints.json`. Never weaken the patterns to hide a real leak.
- **Configure interactively:** `aw sanitize --configure` walks you through both files (allowlist,
  the IP and hostname toggles, and your personal hints), explains each control, shows a diff, and
  writes only on confirmation. Re-runnable and safe; needs an interactive terminal.

## Self-tests (run before pushing tool changes)

The framework's Python code has automated tests written as stdlib `unittest.TestCase`
(consistent with the tools themselves). If you change any of the mechanical parts, the
`agent_workflows/` package (installer/CLI engine, config, discovery, versioning, term, comms, plans,
layout migration, pypi_links) or the workflow tools (`scan_secrets.py`, `run_checks.py`, `bench_env.py`, `setup_tools.py`,
`normalize_plan_names.py`), run the whole suite. The canonical command is:

```bash
make test
```

`make test` runs the suite in parallel via `pytest -n auto` (the tests are subprocess/IO
bound and independent, so this cuts wall time roughly 5-8x, e.g. ~4:20 serial to ~0:40 on a
12-core machine) after `pip install '.[test]'`; it falls back automatically to the serial
stdlib runner when `pytest-xdist` is not installed. pytest/pytest-xdist are TEST-ONLY
dependencies (the `test` extra), never imported at runtime and never shipped (D138). The
parallel run returns identical results to the serial one; prefer it as the evidence command.

If you need the guaranteed no-dependency serial runner (for a minimal environment, or to
debug a test-ordering/isolation issue), use:

```bash
make test-serial   # i.e. python3 -m unittest discover -s tests -t .
```

The suite covers the installer/CLI (fresh install, idempotent re-run, prune of
stale/legacy shims, legacy-layout migration, dry-run, the catalog-row collapse and the
`assess-all` prefix exception, `install`/`setup`/`uninstall`/`list`/`status`, `--version`),
the config and repo discovery, git-tag versioning, the accessible terminal helper, the
wheel packaging (ship-vs-dev), the secret scanner (planted secret in tree AND history,
redaction, clean-repo zero), the check runner (classification, the safety denylist under
`--yes`, honest pass/fail), the env tool, `setup_tools`, the layout migration engine,
and the plan-filename normalizer. The framework's own
`verify` workflow discovers and runs them. Test only the mechanical parts, not the
instruction prose (prose is reviewed by `/assess prose`, not unit-tested).

## Authoring conventions

- Match what the software does today; do not document aspirations
  (`GUIDING_PRINCIPLES.md` P2).
- Keep each policy or rule in exactly one canonical place and link to it, rather than
  duplicating it (P8).
- Do not use em or en dashes in USER-FACING prose you author (READMEs, CHANGELOG, and
  docs meant for end users); use hyphens or parenthetical dashes. The point is to keep
  user-facing text from reading as machine-written. This does NOT apply to internal or
  AI-facing artifacts (IPDs/plans, research findings, prompts, specs, walkthroughs, commit
  messages, code comments); spend no effort avoiding dashes there.
- The standing agent execution contract (commit only your own files path-scoped, never
  `git add -A`/bare/`-a`, never push; paste the actual runner output when you claim tests
  passed; review-means-read-only; no in-place edits to a plan already in `executed/`) lives
  in the managed `AGENT-WORKFLOWS` block in `AGENTS.md`. That block is the canonical home;
  this file and the `.aw/records/plans` README point at it (D69).
- Output conventions (`GUIDING_PRINCIPLES.md` P14): human TTY output is concise, aligned,
  and scannable via the `Term` helper (bold-colored words, bracketed fixed-width severity
  labels `[ERROR]`, `[WARN ]`, `[INFO ]`); non-TTY machine output routes through universal
  machine flags (`--agent` / `--json`) for parseable stream output.

## Adding a CLI command: the output-contract checklist

Every leaf command MUST honor the dual-audience output contract. Before you land a new leaf,
walk this list (the conformance harness in `tests/test_cli_conformance_matrix.py` enforces it,
and an undeclared or uncovered leaf fails CI):

1. Route through the boundary. Resolve the audience with `select_output(args)` and render the
   typed `CommandResult` through `get_renderer(context)`. Do not `print` results directly.
2. Populate a `CommandResult`. Set `status`, `exit_code` (0 clean / 1 findings / 2 cannot-run),
   `summary`, and the fact lists (`diagnostics`, `changes`, `evidence`, `next_actions`). Never
   claim a positive outcome with `verified=False` or an incomplete non-preview state.
3. Declare the leaf. Add a `CommandDeclaration` to `COMMAND_INVENTORY` in
   `agent_workflows/command_surface.py` (command class, human recipe, agent record kind,
   mutation gate, legacy flags, exit contract). The harness asserts zero undeclared leaves.
4. Support the flags. Read verbs support `--agent` and, where a machine consumer benefits,
   `--json`; all verbs honor `--no-color`. Conflicting explicit format flags exit 2.
5. Streams. Write results to stdout; write progress and cannot-start diagnostics to stderr;
   catch `BrokenPipeError` and exit cleanly.
6. If the leaf is safe to run read-only in the repo, add it to `LIVE_SAFE_LEAVES` in
   `tests/conformance_matrix.py` so the harness exercises it live (ANSI-free agent stream,
   exit-code parity, fact-parity, help, usage error, no-color).
7. Docs. If the leaf introduces a new output shape, note it in the
   [Human TTY guide](docs/cli-human-guide.md) and the
   [Agent protocol reference](docs/cli-agent-protocol.md); the contract itself is in
   [docs/cli-output-contract.md](docs/cli-output-contract.md).
8. Empty, Loading, and Error States. Query, search, and list verbs MUST use
    on zero matches to echo active
   filters and suggest a next step; mutation verbs MUST report applied changes or dry-run
   previews clearly with non-silent errors (see
   [docs/cli-output-contract.md#11-empty-loading-and-error-state-ux-convention](docs/cli-output-contract.md#11-empty-loading-and-error-state-ux-convention)).

## Versioning

The framework uses git-tag-driven semantic versioning (baseline `v1.0.0`; DECISIONS
D44/D46). `.aw/system/VERSION` is a DERIVED artifact generated from the git tag by
`agent_workflows/versioning.py`. Do NOT hand-edit it. To cut a new release, use the BAKE-THEN-TAG order
(DECISIONS D75): on a clean tree run `make version-file VERSION=<X.Y.Z>` to write the
resolved semver into `VERSION` (e.g. `1.2.1`) and stamp the `.aw/system/workflows/index.md`
version header from it, COMMIT that, and THEN create the annotated tag
(`git tag -a vX.Y.Z -m ...`) so the tagged tree already carries a `VERSION` matching its
tag. Do NOT tag first and regenerate afterward. See `RELEASING.md` for the
full release policy.

## Packaging and the CLI (DECISIONS D46)

The distributable is a wheel built with `hatchling` (a dev/build-time dependency; there
are ZERO runtime dependencies). The importable package is `agent_workflows/`; the shipped
workflow tree (`.aw/system/`) is included as package data via `force-include`,
mapped into the wheel under `agent_workflows/_data/`.
The console scripts `agent-workflows` / `aw` / `agentwf` all point at
`agent_workflows.cli:main`.

- **Dev install:** `pip install -e .` exposes the `aw` CLI against your working tree.
- **Build a wheel:** `python -m build --wheel` (needs `pip install build`). The
  ship-vs-dev boundary is enforced by `tests/test_packaging.py`, which asserts the wheel
  contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,
  the source `.aw/records/` tree (docs, plans, prompts), or the meta docs, and that no runtime
  dependency is declared.
- **CLI vs the LLM `/setup-repo`:** the CLI does the deterministic, multi-repo, host-level
  work (install/update, config, discovery, fixed setup artifacts); the LLM
  `/setup-repo` workflow does the stack-tailored, judgment layer. They complement each
  other, and `aw` points the user at `/setup-repo`.
- **Publishing to PyPI is a separate, credentialed, user-gated step** (`twine upload`); it
  is intentionally NOT part of the normal build/test flow.
