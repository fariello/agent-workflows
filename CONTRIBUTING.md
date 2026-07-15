# Contributing

This repo's value is disciplined, honest documentation, so the one rule that matters
most is: keep the docs in sync with what the framework actually does.

## Adding a workflow: the guided way

The fastest path is the `/scaffold` wizard (`.agents/workflows/scaffold/scaffold.md`):
it asks what to create (an `assess-*` lens, a standalone workflow, or a command),
generates it from the existing pattern, wires the manifest, and regenerates the shims.
The manual checklist below is what `/scaffold` automates - follow it if you prefer to do
it by hand.

## Doc-sync checklist: when you add or rename a workflow

The authoritative rules for how workflows are structured live in `ARCHITECTURE.md`
(see its "Capability layout" section) and `.agents/workflows/index.md` (the manifest
format). Do not restate those here; follow them, and use this as the step list:

1. Add or rename the workflow subdirectory under `.agents/workflows/<capability>/`.
2. Update the manifest row(s) in `.agents/workflows/index.md` (keep the
   `command | body | lens | description` columns stable).
3. For an `assess-<concern>` concern, add the lens file under
   `.agents/workflows/assess/lenses/`; for an `advise-<persona>` persona, add the charter
   under `.agents/workflows/advise/personas/`. Add the catalog row and reference the file
   in the manifest `lens` column. These catalog rows collapse into the single `/assess`
   and `/advise` commands (they do not each get their own shim).
 4. Regenerate the per-tool slash-command shims by running the installer
    (`install-workflows.py`, at the repo root); do not hand-edit the generated shims in
    `.opencode/commands/` or `.claude/commands/`.
5. Confirm `README.md` and `ARCHITECTURE.md` still describe the current set accurately.
6. If a decision changed the design, add a dated entry to `DECISIONS.md`. Never rewrite
   existing dated entries to match a later layout; the log is history (see
   `GUIDING_PRINCIPLES.md` P4).

## Secret scanning

Committed secrets and PII/PHI must never enter this repo, including its git history.

- **CI enforces it:** `.github/workflows/secret-scan.yml` runs `gitleaks` (full history)
  on every push and pull request.
- **Scan locally before pushing:** run `gitleaks detect --source . --no-banner`, or the
  built-in `python3 .agents/workflows/assess/tools/scan_secrets.py --repo .` (a
  dependency-free safety net that also auto-uses gitleaks/detect-secrets if installed).
- **False positives:** add the finding's fingerprint (printed by gitleaks) to the
  `.gitleaksignore` baseline at the repo root. Do not suppress a real secret - rotate
  it at the provider first, then purge it from history (`git filter-repo`/BFG).
- For a deeper pass, run `/assess secrets`.

## Self-tests (run before pushing tool changes)

The framework's Python code has automated tests (stdlib `unittest`, zero dependencies -
consistent with the tools themselves). If you change any of the mechanical parts - the
`agent_workflows/` package (installer/CLI engine, config, discovery, versioning, term) or
the workflow tools (`scan_secrets.py`, `run_checks.py`, `bench_env.py`, `setup_tools.py`,
`normalize_plan_names.py`) - run the whole suite:

```
python3 -m unittest discover -s tests -t .
```

The suite covers the installer/CLI (fresh install, idempotent re-run, prune of
stale/legacy shims, legacy-layout migration, dry-run, the catalog-row collapse and the
`assess-all` prefix exception, `install`/`setup`/`uninstall`/`list`/`status`, `--version`),
the config and repo discovery, git-tag versioning, the accessible terminal helper, the
wheel packaging (ship-vs-dev), the secret scanner (planted secret in tree AND history,
redaction, clean-repo zero), the check runner (classification, the safety denylist under
`--yes`, honest pass/fail), the env tool, `setup_tools`, and the plan-filename normalizer
(parse/legacy shapes/earliest-evidence time/scan/apply/exclusions). The framework's own
`verify` workflow discovers and runs them. Test only the mechanical parts, not the
instruction prose (prose is reviewed by `/assess prose`, not unit-tested).

## Authoring conventions

- Match what the software does today; do not document aspirations
  (`GUIDING_PRINCIPLES.md` P2).
- Keep each policy or rule in exactly one canonical place and link to it, rather than
  duplicating it (P8).
- Do not use em or en dashes in authored Markdown; use hyphens or parenthetical dashes.
- The standing agent execution contract (commit only your own files path-scoped, never
  `git add -A`/bare/`-a`, never push; paste the actual runner output when you claim tests
  passed; review-means-read-only; no in-place edits to a plan already in `executed/`) lives
  in the managed `AGENT-WORKFLOWS` block in `AGENTS.md`. That block is the canonical home;
  this file and the `.agents/plans` README point at it (D69).

## Versioning

The framework uses git-tag-driven semantic versioning (baseline `v1.0.0`; DECISIONS
D44/D46). `.agents/workflows/VERSION` is a DERIVED artifact generated from the git tag by
`agent_workflows/versioning.py` (a top-level `versioning.py` re-export shim preserves the
old import path) - do NOT hand-edit it. To cut a new release, use the BAKE-THEN-TAG order
(DECISIONS D75): on a clean tree run `make version-file VERSION=<X.Y.Z>` to write the
resolved semver into `VERSION` (e.g. `1.2.1`) and stamp the `.agents/workflows/index.md`
version header from it, COMMIT that, and THEN create the annotated tag
(`git tag -a vX.Y.Z -m ...`) so the tagged tree already carries a `VERSION` matching its
tag. Do NOT tag first and regenerate afterward (that leaves the tagged tree stamped with the
previous version, the bug D75 fixed). See `RELEASING.md` for the
full release policy: the close-out / release-candidate / full-release consent tree, the
`vX.Y.Z-rc.N` pre-release convention (a bare `vX.Y.Z` means "intended for the registry"),
draft GitHub Releases, and the never-tag/release/publish-outside-Section-9 rule. A dirty or
ahead-of-release checkout resolves to a `X.Y.Z.devN+g<sha>` string on purpose, so a copy
that differs from a release is never reported as a clean version. The wheel's version is
computed by the same resolver via the `hatch_build.py` version source, so the packaged
version always matches.

## Packaging and the CLI (DECISIONS D46)

The distributable is a wheel built with `hatchling` (a dev/build-time dependency; there
are ZERO runtime dependencies). The importable package is `agent_workflows/`; the shipped
workflow tree (`.agents/workflows/`) is included as package data via `force-include`,
mapped into the wheel under `agent_workflows/_data/` (the tree is NOT moved in the repo).
The console scripts `agent-workflows` / `aw` / `agentwf` all point at
`agent_workflows.cli:main`.

- **Dev install:** `pip install -e .` exposes the `aw` CLI against your working tree.
- **Build a wheel:** `python -m build --wheel` (needs `pip install build`). The
  ship-vs-dev boundary is enforced by `tests/test_packaging.py`, which asserts the wheel
  contains only the package + `_data` tree and NONE of `tests/`, `workflow-artifacts/`,
  the source `.agents/` tree (docs, plans, prompts), or the meta docs, and that no runtime
  dependency is declared.
- **CLI vs the LLM `/setup-repo`:** the CLI does the deterministic, multi-repo, host-level
  work (install/update, config, discovery, the fixed setup artifacts); the LLM
  `/setup-repo` workflow does the stack-tailored, judgment layer. They complement each
  other, and `aw` points the user at `/setup-repo`.
- **Publishing to PyPI is a separate, credentialed, user-gated step** (`twine upload`); it
  is intentionally NOT part of the normal build/test flow.
