# IPD: interactive leak-sanitizer config wizard (Set: leak-sanitizer, Order 2)

- Date: 2026-07-21
- Concern: usability / config authoring for the leak-sanitizer (D96); make the layered config discoverable and safe to edit without hand-writing TOML/JSON
- Scope: a new deterministic, re-runnable interactive CLI wizard that reads and writes the leak-sanitizer's TWO existing config surfaces (the tracked `.agents/local-leaks-allowlist.toml` and the gitignored user-hints JSON), plus tests and docs. Product code (`agent_workflows/`). Order 2 of the `leak-sanitizer` Set. Depends on Order 1 (D96, executed): the engine, the config schema, and the loaders already exist; this wizard only authors what the engine already reads.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored as Order 2 of the leak-sanitizer Set. Form decided by the human: a deterministic CLI wizard (like `aw setup`), not a prose runbook, consistent with GUIDING_PRINCIPLES P11 (deterministic work belongs in scripts). Order 3 (agent/workflow rewire + optional setup-repo install) is explicitly deferred and will be authored AFTER this wizard is reviewed (human asked to pause between Order 2 and Order 3).

## Goal

Give a maintainer a safe, guided, re-runnable way to author the leak-sanitizer's layered config, so they never have to hand-edit TOML/JSON or guess key names. The wizard reads the current config, explains each control in plain language (the tracked allowlist, the IP and hostname toggles, and the never-committed personal hints), collects changes interactively, shows a diff, and writes ONLY on confirmation, using an atomic write that produces output the engine's minimal parser can round-trip.

Why it matters: Order 1 (D96) shipped a powerful layered config but the only way to configure it today is to hand-write `.agents/local-leaks-allowlist.toml` (read by a MINIMAL regex TOML parser with sharp edges) and a `~/.config`-style JSON. That is exactly the deterministic, no-judgment authoring task P11 says belongs in a tested script, not in a human's head or an LLM re-derivation. It also lowers the risk of writing a file the minimal parser silently mis-reads.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P8 single source of truth; P10 safety/reversibility; P11 deterministic checks belong in scripts; zero runtime deps, stdlib only). No em/en dashes.
- The wizard is a deterministic CLI (human decision), mirroring the `aw setup` interactive pattern.
- Existing config surfaces the wizard authors (verified, D96 / Order 1):
  - TRACKED `.agents/local-leaks-allowlist.toml` (`leak_sanitizer.REPO_ALLOWLIST_REL`, `leak_sanitizer.py:153`). Schema (all flat): `allow_line_substrings` (string array), `fail_patterns` (string array), `ip_enabled` (bool), `hostname_fail` (bool). Read by `load_repo_allowlist` + `load_repo_config_bools` (`leak_sanitizer.py:182-197`).
  - GITIGNORED user-hints JSON (`leak_sanitizer.USER_HINTS_FILENAME` = `local-leaks-hints.json`) under `_config_dir()` (XDG-aware, `leak_sanitizer.py:200-207`). Schema: `tokens` (string array of literals), `patterns` (string array of regexes). Read by `load_user_hints` (`leak_sanitizer.py:210-225`).
- CLI conventions to reuse (verified):
  - Interactive pattern `_run_setup` (`cli.py:715-821`): interactivity = `args.<flag> is None and sys.stdin.isatty()`; refuse to interview when non-interactive without an arg.
  - Shared `_confirm(term, prompt, assume_yes)` (`cli.py:288-303`): auto-declines when non-interactive without `--yes`; catches `EOFError`.
  - Output via `Term` (`term.py`): `term.heading/line/status/kv`. `--no-color` honored.
  - Ctrl-C / EOF handled centrally in `main()` (`cli.py:1041-1056`), returning 130; the wizard uses bare `input(...)` and does NOT catch those locally.
  - Subcommand registration in `_build_parser` (`cli.py:31-274`) with `parents=[common]`; dispatch in the `_dispatch` if-chain (`cli.py:1020-1038`).
- Atomic write pattern to mirror: `config.save` (`config.py:159-183`): `mkdir(parents=True, exist_ok=True)`, write to a `tempfile.mkstemp` temp in the same dir, `os.replace` (atomic), unlink on failure.
- Testing conventions: `tests/test_cli.py` harness (`:25-56`): `_run(argv)` capturing stdout, temp `XDG_CONFIG_HOME`, `NO_COLOR=1`; force interactivity with a `_FakeTTY` whose `isatty()` returns True and script `builtins.input` from an iterator (`:372-397`); Ctrl-C/EOF returns 130 (`:330-366`). Prefer an INJECTABLE prompt/confirm callback in the wizard core (like `fix_working_tree(confirm=...)`, `leak_sanitizer.py:524-536`) so tests drive it without monkeypatching stdin.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C1 | MEDIUM | Low | maintainer / novice | usability | The only way to configure the sanitizer today is hand-editing TOML/JSON; key names, the `ip_enabled`/`hostname_fail` toggles, and the whitelist/blacklist semantics are undiscoverable without reading the engine source. | `leak_sanitizer.py:304-338`; no wizard exists |
| C2 | MEDIUM | Medium | maintainer | correctness / safety | The tracked TOML is read by a MINIMAL parser with sharp edges: only flat `key = [..]` string arrays and flat `key = true|false` bools; a value containing a quote is TRUNCATED (`_parse_simple_toml_lists` uses `["']([^"']*)["']`); section headers are ignored so bare key names must be globally unique. A hand-authored file can be silently mis-read. A wizard-authored file must be guaranteed round-trippable. | `leak_sanitizer.py:157-179` |
| C3 | LOW | Low | operator | privacy | The personal-hints file is machine-specific and MUST stay out of git; a wizard writing it must target the gitignored user config dir, never the repo. | `leak_sanitizer.py:210-225`, `_config_dir` `:200-207` |

## Proposed changes (ordered, validatable; checkpointed)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | C2 | Add a config WRITER to `agent_workflows/leak_sanitizer.py` (co-located with the loaders, one module owns the schema, P8): `write_repo_allowlist(repo_root, *, allow_line_substrings, fail_patterns, ip_enabled, hostname_fail)` and `write_user_hints(tokens, patterns)`. Both write ATOMICALLY (temp + `os.replace`, mirroring `config.save`), create parent dirs, and emit ONLY parser-round-trippable output: flat string arrays (one key per line or wrapped), flat booleans, a leading comment header. REJECT (or safely escape) any value containing a quote char that the minimal parser would truncate, with a clear error naming the offending value (do not silently write an un-round-trippable file). The user-hints writer targets `_config_dir()`, never the repo (C3). | `agent_workflows/leak_sanitizer.py` | Medium | round-trip tests: what `write_*` writes, the matching `load_*` reads back identically; a value with a quote is rejected with a named error; user-hints lands under the (test-redirected) XDG dir, not the repo |
| 2 | C1,C2 | Add the wizard CORE as a pure function (testable, no argparse): `configure(repo_root, *, prompt, confirm, assume_yes) -> summary`. It (a) loads current config via the existing loaders, (b) walks each control in plain language - repo allowlist substrings, repo fail patterns, `ip_enabled`, `hostname_fail`, then the personal `tokens`/`patterns` - showing current values and letting the user add/remove/keep, (c) explains each toggle's consequence (e.g. "IP matching is noisy and rarely identifying; default OFF"; "hostname as FAIL can fail CI on a shared runner; default warn-only"), (d) builds the proposed new config, (e) shows a DIFF of both files, (f) writes via Step 1 only on `confirm`. `prompt`/`confirm` are INJECTED callables (default to stdin/`_confirm`) so tests drive it without monkeypatching. Re-runnable + idempotent: re-running with no changes writes nothing. | `agent_workflows/leak_sanitizer.py` (or a small `leak_sanitizer_config.py` sibling; decide at review, OQ2) | Medium | unit tests via injected prompt/confirm: add/remove an allowlist entry; flip a toggle; add a personal token; decline -> nothing written; no-change re-run -> nothing written; diff shown before write |
| 3 | C1 | Wire the wizard to the CLI. Register it following `aw setup`: EITHER a `--configure` flag on the existing `check-local-leaks`/`sanitize` command (short-circuits before the scan) OR a dedicated `aw leaks-config` subcommand (decide at review, OQ1). Add a `dir` positional (default `.`), reuse `--yes` for non-interactive accept-defaults, honor `--no-color`, refuse to interview when non-interactive without `--yes` (print the guidance), and add the `_dispatch` branch + handler `_run_*` mirroring `_run_setup`. End with a short teaching line (where the files are, that re-running is safe). | `agent_workflows/cli.py` | Low | `aw sanitize --configure` (or `aw leaks-config`) launches the wizard; non-interactive without `--yes` prints guidance and exits nonzero; `--no-color` clean; Ctrl-C returns 130 via main() |
| 4 | C1,C2 | Tests: a `LeaksConfigTests(CliTestBase)` in `tests/test_cli.py` (CLI-level: forced `_FakeTTY` + scripted `input`, assert the written TOML round-trips through `load_repo_allowlist`/`load_repo_config_bools` and hints through `load_user_hints`) PLUS core-level unit tests in `tests/test_leak_sanitizer.py` using the injected prompt/confirm (no stdin). Cover: writer round-trip + quote rejection (Step 1); wizard add/remove/toggle/decline/no-change (Step 2); CLI wiring + non-interactive guard (Step 3). | `tests/test_cli.py`, `tests/test_leak_sanitizer.py` | Low | full suite green; new tests cover writer + core + CLI paths; paste actual output |
| 5 | C1 | Docs/decision sync: a DECISIONS entry (pin at execution) for the wizard + writer (one module owns read AND write of the schema, P8/P11); update `CONTRIBUTING.md` (the "No local leaks" section) and the `/assess local-leaks` lens to mention `aw sanitize --configure` (or `aw leaks-config`) as the way to author config; CHANGELOG 1.3.0; if a `--configure` flag or a new subcommand is added, ensure it is documented in `aw --help` and, if a slash-command is ever wanted, note it as Order 3 scope (NOT here). | `DECISIONS.md`, `CONTRIBUTING.md`, `.agents/workflows/assess/lenses/local-leaks.md`, `CHANGELOG.md` | Low | entries present; links resolve; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| Agent/workflow rewire to CONSUME `--agent` output; the OPTIONAL setup-repo install of the hook+CI (off by default); making agents AWARE of the script without hooks; any `/`-slash-command surface for the wizard | Medium | functionality | Order 3 of this Set. The human asked to PAUSE after Order 2 and review before Order 3 is authored. | Order 3 IPD (authored after this wizard is reviewed). |
| A full TOML library / nested-table support | Low | complexity | The engine's minimal parser is intentionally stdlib-only (zero deps); the wizard writes to ITS constraints, it does not upgrade the parser. If richer TOML is ever needed, that is a separate engine change. | n/a - deliberate. |

## Scope check

- Over-scope: none. This is the config-authoring wizard + its writer + tests + docs only. The agent rewire and the optional hook/CI install are explicitly Order 3.
- Under-scope: the writer MUST guarantee round-trippability against the EXISTING minimal parser (C2), or it defeats its own purpose; the personal-hints file MUST land in the gitignored user config dir, never the repo (C3). Both are called out in Steps 1 and are test-covered in Step 4.

## Required tests / validation

- `tests/test_leak_sanitizer.py`: writer round-trip (write -> load reads back identically) for both files; quote-containing value is rejected with a named error, not silently truncated; wizard core via injected prompt/confirm (add/remove allowlist entry, flip `ip_enabled`/`hostname_fail`, add a personal token, decline writes nothing, no-change re-run writes nothing).
- `tests/test_cli.py`: `LeaksConfigTests` drives the CLI with a forced TTY + scripted input; asserts the written config round-trips through the loaders and the user-hints file landed under the redirected `XDG_CONFIG_HOME` (not the repo); non-interactive without `--yes` prints guidance and exits nonzero; Ctrl-C returns 130.
- Full suite `python -m pytest -q` GREEN; paste ACTUAL output (baseline this session 316 passed, 1 skipped; expect additions).
- `aw check-local-leaks .` clean; no em/en dashes.
- Round-trip sanity: after the wizard writes, `aw check-local-leaks .` still parses the config and behaves per the chosen toggles (e.g. enabling `ip_enabled` then scanning a fixture flags an IP).

## Spec / documentation sync

- DECISIONS (the wizard + the writer owning schema read/write), CONTRIBUTING (the config-authoring command), the `/assess local-leaks` lens (mention the wizard), CHANGELOG 1.3.0.

## Open questions

- OQ1 (CLI surface): a `--configure` flag on the existing `check-local-leaks`/`sanitize` command, or a dedicated `aw leaks-config` subcommand? Lean: `--configure` on `sanitize` (fewer top-level commands; the config wizard is clearly part of the sanitizer). A dedicated subcommand is more discoverable in `aw --help`. Confirm at review.
- OQ2 (module placement): put `configure`/`write_*` in `leak_sanitizer.py` (one module owns the schema, simplest) or a sibling `leak_sanitizer_config.py` (keeps the engine lean; the wizard is a distinct concern)? Lean: keep the WRITERS in `leak_sanitizer.py` next to the loaders (schema cohesion, P8) and the interactive WIZARD core in a sibling so the engine module stays scan-focused. Confirm at review.
- OQ3 (add/remove UX): for list-valued controls (allowlist substrings, fail patterns, tokens), what editing model - re-enter the whole list, or an add/remove/keep loop per entry? Lean: show current entries, then an add/remove loop (enter to keep, `-<value>` to remove, plain value to add), matching the `aw setup` "blank to finish" idiom. Confirm at review.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. The human has asked to PAUSE after this IPD (Order 2) and review before Order 3 is authored.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

CHECKPOINTED EXECUTION: (1) writer functions + their tests; (2) wizard core + its tests; (3) CLI wiring + its tests; (4) docs/decision. Re-run the full suite at each checkpoint; pause and report if a checkpoint's scope grows.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ3. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute in checkpoints, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. Then PAUSE for the human before authoring Order 3 (agent rewire + optional setup-repo install).
