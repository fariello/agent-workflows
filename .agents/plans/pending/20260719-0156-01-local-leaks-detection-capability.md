# IPD: `local-leaks` detection capability (shippable scanner + `aw` command + assess lens + CI)

- Date: 2026-07-19
- Concern: privacy / identity-leak detection (durable, reusable) + regression prevention
- Scope: promote the one-off personal-path guard into a first-class, reusable capability: a shippable scanner module in `agent_workflows/`, an `aw check-local-leaks` subcommand, an `/assess local-leaks` lens, a CI workflow, working-tree + git-history + built-wheel scan modes, and auto-derived tokens + a repo-committed allowlist + a user-level personal-hints file. Does NOT re-run the one-time cleanup (D92) or touch PyPI/history.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-19 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after the D92 cleanup, when the human asked for a durable way to detect/mitigate this class of leak (which secret scanners miss). Human decisions captured at design time: name = `local-leaks`; promote to an assess lens AND an `aw` command (options 1+2); include a thin CI backstop; auto-derive tokens + split config (small repo-committed allowlist that travels + CI-deterministic, PLUS a never-committed user-level personal-hints file under `~/.config/agent-workflows/`); the lens should cover usernames + emails (enumerate emails and ask which to keep), not just paths. Grounded in an explore survey of the scanner, cli/config/assess/packaging structure.
- 2026-07-19 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed. Verified the load-bearing claims against source (config `normalize()` drops unknown keys -> justifies the separate hints file; `scan_secrets` `scan_text`/`scan_history` history parser + email rule; CLI dispatch pattern; packaging boundary; CI runs on ubuntu+macos+windows). Added LL7 (cross-platform: optional derivation sources, Windows paths) and LL8 (CI history-scan boundedness); pinned OQ3 as warn-only auto-derive + fail-only-on-structural/curated/hints so CI stays deterministic; set CI to working-tree default with bounded/manual `--history`; added checkpointed execution (PR-005). Resolved OQ1-OQ4 with the human. Status -> reviewed.

## Goal

Make "identifying info that must not live in a public artifact" a detectable, mitigable, reusable capability, so this never silently recurs and downstream repos benefit too.

Secret scanners (gitleaks, `git-secrets`, our `scan_secrets.py`) hunt credential SHAPES (keys, tokens, high-entropy strings); they do NOT flag a maintainer's home path, username, private sibling-repo names, hostnames, or machine/account ids. That gap is exactly what shipped a private repo name to PyPI (D92). The D92 fix was a repo-internal, working-tree-only, hand-token script. This IPD turns it into:
- a **shippable, importable scanner** (`agent_workflows/local_leaks.py`) so `aw check-local-leaks` works from an installed package and downstream repos get it;
- **three scan modes** - working tree (fast, default), full git history (the mode that would have caught the tag leak), and a built wheel (the shipped surface);
- **low-maintenance token sourcing** - auto-derive the obvious personal tokens at runtime, plus a small repo-committed allowlist for "public-OK here," plus an optional never-committed user-level hints file;
- an **interactive `/assess local-leaks` lens** that enumerates emails/usernames and asks which to keep, then records the decision in the allowlist so the automated guard stops re-flagging them.

Why it matters: it closes the class of defect D92 was a single instance of, makes the check discoverable (`/assess`, `aw`, CI, pre-commit), and keeps the guard self-adjusting instead of a hand-maintained list that rots.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P8 single source of truth - one scanner engine feeds tool+lens+CI+hook; P5 externalize state; P10 safety). No em/en dashes in authored Markdown.
- Pending-plans location/format: `.agents/plans/pending/YYYYMMDD-HHMM-NN-<slug>.md`; readiness `Status:` (D52). Execution contract in `.agents/plans/README.md`.
- Stack / relevant context (verified):
  - Existing guard: `tools/check_personal_paths.py` - `git ls-files` tracked-only scan, fragment-assembled patterns (history-rewrite-safe), `PATTERNS`/`ALLOWED_LINE_SUBSTRINGS`/`ALLOWED_PATHS`, `scan()`/`main()`. Does NOT ship (top-level `tools/` not in `pyproject.toml`).
  - Reusable engine shape: `.agents/workflows/assess/tools/scan_secrets.py` already has multi-mode (tree + `git log -p -U0` history at 484-546), redaction (290-304), and multi-format `emit` (json/csv/text, 639-724), AND already enumerates emails (rule `email`, 156-161) + other PII. Reuse this engine shape; do NOT re-implement email detection - cross-reference it.
  - CLI: `agent_workflows/cli.py` `_build_parser()` (31-219) + `_dispatch()` (896-938) + `_run_<x>` handlers; 7 existing subcommands (`install/setup/uninstall/list/status/plans/plan-names`). Package submodule pattern: `cli.py` imports `from . import config, engine, plans, ...`; new module `agent_workflows/local_leaks.py` fits here.
  - Config: `agent_workflows/config.py` `config_dir()` (43-51, XDG-aware) -> `~/.config/agent-workflows/`. CRITICAL CONSTRAINT: `normalize()` (104-132) DROPS any key not in `_ALLOWED_TOP_KEYS` (37-39), and D46/R-5 says `config.json` stores NO sensitive data. So personal token hints must NOT go in `config.json`; they go in a SEPARATE user-level file resolved via `config_dir()` (e.g. `~/.config/agent-workflows/local-leaks-hints.json`), never committed, never normalized.
  - Assess lens: `.agents/workflows/assess/lenses/<concern>.md` (H1, focus, Lead personas, Rubric, IPD emphasis) + a manifest row in `.agents/workflows/index.md` between the MANIFEST markers. `scaffold` workflow is the meta-tool for adding a lens.
  - CI: `.github/workflows/secret-scan.yml` shape (push/PR triggers, `fetch-depth: 0`, `permissions: contents: read`). `tests.yml` already uses `fetch-depth: 0`.
  - Packaging: `packages = ["agent_workflows"]`; `.agents/workflows/` ships as DATA under `_data/`. `tests/test_packaging.py` asserts the shipped surface and already has a `test_wheel_has_no_personal_path_leak` (129-152).

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| LL1 | HIGH | Low | maintainer / user | discoverability | The D92 guard is a loose repo-internal script; it is not a workflow, not an `aw` command, not shipped, so it is undiscoverable and does not protect downstream repos that install agent-workflows. | `tools/check_personal_paths.py` (top-level, not in `pyproject.toml`) |
| LL2 | HIGH | Medium | maintainer | coverage (history) | The guard scans only the working tree (`git ls-files`). The exact failure that bit us (a leak reachable only via an old tag/commit) is invisible to a working-tree scan; only a HISTORY scan catches it. | `tools/check_personal_paths.py` `tracked_files()`; D92 workflow history (v1.2.0 tag) |
| LL3 | MEDIUM | Low | maintainer | coverage (wheel) | The shipped-surface check exists only as a one-off test assertion, not a runnable mode; there is no `aw`/CI way to grep a built wheel on demand. | `tests/test_packaging.py:129-152` |
| LL4 | MEDIUM | Medium | maintainer | maintainability | The token list is hand-maintained; a new machine/username/private-repo will not be caught until someone edits the script. No auto-derivation. | `tools/check_personal_paths.py:30-38` |
| LL5 | MEDIUM | Low | maintainer | usability (emails) | Emails are ambiguous (author email intended; a stray committer or third-party email is a leak). There is no interactive way to enumerate emails and record which are approved; the guard can only hard-allow a fixed list. | `scan_secrets.py:156-161` (email rule exists but non-interactive) |
| LL6 | LOW | Low | contributor | backstop | Pre-commit hooks are bypassable (`--no-verify`) and machine-local; there is no CI enforcement of the personal-leak check as a push-time backstop (unlike `secret-scan.yml` for credentials). | `.github/workflows/` (no local-leaks workflow) |
| LL7 | MEDIUM | Medium | maintainer | cross-platform (plan-review PR-001) | The auto-derivation (LL4/Step 1) and the guard run on the full CI matrix (ubuntu + macos + windows; `tests.yml:24,66`) and `test_no_personal_paths.py` executes on all three. `$USER` is frequently unset on Windows, `git config user.*` may be unset in CI, and Windows home paths are `C:\Users\...` not `/home` or `/Users`. Without explicit cross-platform handling, auto-derivation and tests go flaky/red off-Linux. | `tools/check_personal_paths.py:44,46`; `.github/workflows/tests.yml:24,66` |
| LL8 | MEDIUM | Low | maintainer | CI determinism (plan-review PR-002) | A CI `--history` scan (Step 7) is O(all commits) and would fail every future push if ANY old commit still holds a token. Post-D92 history is clean, but an unbounded full-history CI scan on every push is slow and brittle. | Step 7; `scan_secrets.py:484` (`max_commits` bound exists) |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | LL1,LL4,LL7 | Create the shippable engine `agent_workflows/local_leaks.py`: the identity rule set (fragment-assembled, history-rewrite-safe) merged with a scan_secrets-style text/location core. Add AUTO-DERIVATION of personal tokens at runtime: `$HOME` basename, `git config user.name`/`user.email`, `$USER`/`$USERNAME`, the repo's parent-directory sibling names, and the hostname; each becomes a pattern unless allowlisted. CROSS-PLATFORM (PR-001): every derivation source is OPTIONAL - a missing `$USER`/`$USERNAME`, unset `git config`, or absent hostname yields no pattern (never an error); also recognize Windows home paths (`C:\\Users\\<name>`) alongside `/home` and `/Users`. Keep patterns assembled so the module never contains a plain leak literal. | `agent_workflows/local_leaks.py` (new) | Medium | unit tests (run on the ubuntu+macos+windows matrix): auto-derivation from a synthetic env; missing-source degrades to no-pattern (no crash); fragment self-scan clean; a Windows-style path is recognized |
| 2 | LL1,LL4,LL5 | Config split: (a) read a small REPO-COMMITTED allowlist file (public-OK values + path exemptions; e.g. `.agents/local-leaks-allowlist.toml` - NOT `config.json`, and NOT under a home dir); (b) read an OPTIONAL user-level personal-hints file via `config_dir()` (`~/.config/agent-workflows/local-leaks-hints.json`), never committed, never passed through `config.py normalize()`. Do NOT add hints to `config.json` (D46/R-5: it drops unknown keys and stores no sensitive data). | `agent_workflows/local_leaks.py`, new committed allowlist file | Medium | tests: allowlisted value not flagged; a hint from the user file IS flagged; a missing user file is a no-op |
| 3 | LL2,LL3 | Implement three scan modes in the engine: `--working-tree` (default, `git ls-files`), `--history` (reuse the `git log -p -U0` added-line parser from scan_secrets, reporting `commit:path:line`), `--wheel PATH` (open the zip, grep entries). One `scan(...)` core fed by three source adapters. | `agent_workflows/local_leaks.py` | Medium | tests: planted leak in HEAD flagged (tree); planted leak in an older commit flagged only by `--history`; a wheel entry with a token flagged by `--wheel` |
| 4 | LL1 | Wire `aw check-local-leaks` subcommand: parser (`dir` positional, `--history`, `--wheel PATH`, `--format text|json`, `--max-commits N`), `_run_check_local_leaks(args, term)` handler importing `from . import local_leaks`, dispatch line, and add to the bare-`aw` hint. | `agent_workflows/cli.py` | Low | `aw check-local-leaks .` exits 0 on the clean repo; `--history` runs; a CLI test asserts exit codes |
| 5 | LL1,LL2 | Migrate the D92 guard onto the new module: repoint `tests/test_no_personal_paths.py` to import the package module (not path-load `tools/`); update `.pre-commit-config.yaml` hook to `python3 -m agent_workflows check-local-leaks`; keep a thin `tools/check_personal_paths.py` shim (source-checkout pre-commit before install) OR delete it (OQ1). Update `tests/test_packaging.py` to expect `agent_workflows/local_leaks.py` in the wheel. | `tests/test_no_personal_paths.py`, `.pre-commit-config.yaml`, `tests/test_packaging.py`, `tools/` | Medium | full suite green; pre-commit still blocks a planted leak |
| 6 | LL5 | Author `.agents/workflows/assess/lenses/local-leaks.md` (interactive lens): scans tree + history + optionally the wheel via the shared engine; SURFACES the warn-only auto-derived candidates (OQ3) for human confirmation; ENUMERATES all distinct emails/usernames and ASKS the human which to keep; writes approved values into the repo-committed allowlist (`.agents/local-leaks-allowlist.toml`); proposes a scrub IPD for the rest. References `secrets.md` (credentials/PII, incl. its existing email pass) and `privacy.md` (product PII) to bound scope and avoid contradiction (OQ4). Register a manifest row `assess-local-leaks` in `index.md` and regenerate shims (via `scaffold` conventions). | `.agents/workflows/assess/lenses/local-leaks.md` (new), `.agents/workflows/index.md` | Low | lens file present; `test_dir_readmes`/manifest parse pass; a temp `aw install` generates no shim for the catalog row (assess-* rows are catalog, not commands) |
| 7 | LL6,LL8 | Add `.github/workflows/local-leaks.yml` (thin backstop mirroring `secret-scan.yml`): push/PR triggers, `permissions: contents: read`, one step running the packaged scanner in WORKING-TREE mode by default (`python -m agent_workflows check-local-leaks .`). CI does NOT run an unbounded full-history scan on every push (PR-002): history scanning is a manual/release-time invocation (`--history`, optionally `--max-commits`), documented in the lens/CONTRIBUTING. Lower priority; drop if review judges it redundant for a solo repo. | `.github/workflows/local-leaks.yml` (new) | Low | workflow YAML valid; runs the packaged scanner working-tree mode; completes in seconds |
| 8 | LL1 | Docs/decision sync: DECISIONS **D93** (pin) recording the capability + the config split + auto-derivation; update `CONTRIBUTING.md` (point at the command/lens); CHANGELOG 1.3.0 "Added" bullet; update the D92 references that named the old script path. | `DECISIONS.md`, `CONTRIBUTING.md`, `CHANGELOG.md` | Low | links resolve; scanner still clean; no em/en dashes |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Medium | complexity | Merging `scan_secrets.py` and the new engine into ONE unified scanner. They share machinery but have different threat models and output contracts; unifying now is a larger refactor. Reuse the SHAPE, keep them separate for this IPD. | A later consolidation IPD if the duplication proves costly. |
| n/a | Low | functionality | Auto-FIXING leaks (rewriting to placeholders). The lens PROPOSES a scrub IPD; automatic rewriting of arbitrary tracked files is riskier and belongs to the human-reviewed scrub path (D92 pattern). | Keep scrubbing human-reviewed via an IPD. |
| LL6 | Low | complexity | (If review drops CI) the pre-commit hook + local `aw`/lens already cover the solo-maintainer case; CI is a backstop. | Add `local-leaks.yml` when contributors join. |

## Scope check

- Over-scope: do NOT re-run the D92 one-time cleanup, and do NOT touch PyPI/history here (separate human-gated actions). The CI step (Step 7) is explicitly optional/low-priority.
- Under-scope: confirm the auto-derivation does not FALSE-POSITIVE on the repo's own legitimate content (the package name `agent-workflows`, the public author email, the public remote URL). The allowlist must cover these and a test must assert they are not flagged.

## Required tests / validation

- New `tests/test_local_leaks.py` (stdlib unittest, must pass on the ubuntu+macos+windows matrix): auto-derivation from a synthetic env; a MISSING derivation source (`$USER`/`$USERNAME` unset, no `git config`, no hostname) degrades to no-pattern without error (PR-001); a Windows-style `C:\\Users\\<name>` path is recognized; repo-committed allowlist honored; user-hints file honored (and absent = no-op); the 3 scan modes (tree/history/wheel) each catch a runtime-synthesized planted leak in their respective source and pass clean otherwise; a bounded `--max-commits` history scan stops at the bound; public identifiers (package name, author email, remote URL) NOT flagged; the module's own source is self-clean.
- Repoint `tests/test_no_personal_paths.py` (or fold into the new test) to the package module.
- `tests/test_packaging.py`: assert `agent_workflows/local_leaks.py` ships and the wheel remains token-free.
- CLI test: `aw check-local-leaks .` exit 0 on the clean tree; nonzero on a planted leak (temp repo).
- Full suite `python -m pytest -q` stays green; paste ACTUAL output (baseline 271 passed, 1 skipped; expect more).
- Manual: `aw check-local-leaks . --history` on this repo returns clean (post-D92); `--wheel dist/*.whl` on a built wheel returns clean.

## Spec / documentation sync

- `DECISIONS.md`: D93 (pinned) - the capability, config split (repo allowlist vs user hints vs auto-derive), and why hints are NOT in `config.json`.
- `.agents/workflows/index.md`: `assess-local-leaks` manifest row.
- `CONTRIBUTING.md`: replace the D92 script reference with the `aw check-local-leaks` command + `/assess local-leaks` lens.
- `CHANGELOG.md`: 1.3.0 "Added" bullet (worded without leak tokens).
- The lens file + committed allowlist file are themselves spec for downstream repos.

## Open questions

All resolved at review (human, 2026-07-19); no open questions remain.

- OQ1 (tools shim): RESOLVED - pre-commit hook calls `python3 -m agent_workflows check-local-leaks` (works from repo root via the local package); DELETE the `tools/check_personal_paths.py` shim. Encoded in Step 5.
- OQ2 (repo-committed allowlist location): RESOLVED - `.agents/local-leaks-allowlist.toml` (small tracked TOML file under `.agents/`, reviewable, CI-deterministic). Encoded in Step 2.
- OQ3 (auto-derivation strictness): RESOLVED - auto-derived tokens are WARN-ONLY (surfaced by the interactive lens for the human to confirm); the NON-INTERACTIVE gate (pre-commit + CI) fails ONLY on the curated allowlist-miss + user-hints patterns + STRUCTURAL patterns (home paths, local-checkout-dir style, session ids). This keeps CI deterministic and non-flaky (addresses PR-001/PR-002). The engine must therefore distinguish a `warn` severity (advisory, lens-only) from a `fail` severity (gate). Encoded in Steps 1, 3, 6, 7.
- OQ4 (assess-secrets email overlap): RESOLVED (lean) - `/assess local-leaks` references `assess-secrets` for the credential/PII angle and runs its OWN OK-to-keep email/username enumeration for the identity angle; the lens notes the overlap so the two do not contradict. Encoded in Step 6.
- PR-005 (IPD size): RESOLVED - keep as ONE IPD but execute in CHECKPOINTS (engine+tests -> command -> guard migration -> lens -> CI -> docs), pausing and reporting if scope grows beyond the plan. Recorded in the execution gate.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

CHECKPOINTED EXECUTION (PR-005): although this is one IPD, execute in checkpoints and re-run the full suite at each - (1) engine `local_leaks.py` + config split + tests; (2) `aw check-local-leaks` command; (3) guard migration (pre-commit + test repoint + packaging test + delete `tools/` shim); (4) the `/assess local-leaks` lens + manifest; (5) the CI workflow; (6) docs/DECISIONS D93. Pause and report if any checkpoint's scope grows beyond what is written here.

Recommended next steps:
1. Review this IPD (optionally `/plan-review`; sets `Status: reviewed`). Pin D93. Resolve OQ1-OQ4.
2. On human approval, set `Status: approved` (+ `Approval:`), execute the ordered steps, run validation, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
