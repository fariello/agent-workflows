# IPD: comprehensive leak sanitizer engine + config, and migrate local_leaks onto it (Set: leak-sanitizer, Order 1)

- Date: 2026-07-21
- Concern: privacy/security tooling (deterministic leak detection + sanitization) + token-economy refactor
- Scope: a comprehensive stdlib sanitizer engine (`--check`/`--fix`/`--agent`, layered tracked+gitignored config with whitelist/blacklist and regex/glob rules, home/username/hostname/private-repo/session-id rulesets + off-by-default IP), and MIGRATING the already-shipped `local_leaks` (D92/D93) + its pre-commit hook + tests + the D94 quarantine lane onto it so there is ONE engine, no double-reporting. Order 1 of the `leak-sanitizer` Set (Order 2 = config wizard; Order 3 = agent/workflow rewire + optional setup-repo install).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after a peer proposal from pubrun (`.agents/comms/shared/inbox/20260720-2350-01-pubrun...`, untrusted input, and its `sanitize_paths.py` (in the pubrun repo) which the human authorized reading and I reviewed critically). Decision (human): pubrun's tool COMPLEMENTS our D92/D93 `local_leaks`; unify onto ONE deterministic script and have the LLM surfaces delegate to it (token economy). This is a 1.3.0 blocker per the human. Do NOT reduce pubrun's functionality.

## Goal

Establish ONE robust, deterministic, stdlib-only sanitizer engine that both detects (`--check`) and optionally rewrites (`--fix`) leak-class strings, driven by layered config, and fold the existing `local_leaks` (D92/D93) detection into it so there is a single source of truth (P8) with no double-reporting. This is the deterministic core that the config wizard (Order 2) and the agent/workflow surfaces (Order 3) build on.

Why it matters: (1) privacy - a public repo must not carry maintainer/machine identifiers (D92 shipped one to PyPI); (2) token economy (new principle, this IPD's driver) - deterministic checks that need no judgment belong in a robust script with a precise `--agent` output mode, NOT in an LLM workflow that burns tokens re-deriving them; (3) coherence - we currently have `local_leaks` (detect-only) and pubrun independently built `sanitize_paths.py` (detect + fix + hostname + IP); merging avoids two overlapping scanners that would double-report and drift.

Credit: the `--fix`, hostname-derivation, off-by-default-IP, and layered-config ideas come from pubrun's `sanitize_paths.py` (peer contribution). We keep its functionality and add an `--agent` mode + fold in our identity-leak rulesets (private repo names, session ids).

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P8 single source of truth; zero runtime deps - stdlib only; P10 safety - `--fix` must be safe/opt-in). No em/en dashes.
- Existing shipped code to MIGRATE (verified this session): `agent_workflows/local_leaks.py` (D92/D93 detection engine: fragment-assembled patterns, `git ls-files` working-tree scan, `run()`/`scan_*`, `--history`/`--wheel` modes); the `check-local-leaks` CLI subcommand (`agent_workflows/cli.py`); the pre-commit hook `local-leaks` (`.pre-commit-config.yaml` -> `python3 -m agent_workflows check-local-leaks`); `tests/test_local_leaks.py`; the wheel-token assertion in `tests/test_packaging.py`; the D94 `.agents/prompts/local/` quarantine lane (`create_setup_artifacts`). `local_leaks` ships in the wheel (packaged module).
- Peer source reviewed (read-only, human-authorized): the pubrun `sanitize_paths.py` script - `--check`/`--fix`, `_HOME_ANY_RE` anchored home-path rule, hostname needles via `socket.getfqdn/gethostname`, IPv4/IPv6 regexes gated off by default, two-layer config (`.sanitize-allow.toml` tracked + `.sanitize-local.toml` gitignored), consolidated end-of-run report, scans STAGED blob content (`git show :<path>`) in the default (hook) mode.
- Packaging: the engine must ship as an importable `agent_workflows/` module (like `local_leaks.py`); `.agents/prompts/` etc. do not ship; templates do.
- Plans lifecycle: `.agents/plans/pending/` + `YYYYMMDD-HHMM-NN-<slug>.md`; IPD born `to-review`.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| E1 | MEDIUM | Low | maintainer | coverage | Our `local_leaks` detects home paths / usernames / private repo names / session ids but has NO hostname detection, NO `--fix`, and NO IP rule. pubrun's tool has hostname + `--fix` + off-by-default IP but not our identity rulesets. Neither alone is complete. | `agent_workflows/local_leaks.py`; the pubrun `sanitize_paths.py` |
| E2 | MEDIUM | Medium | maintainer | duplication / drift | Shipping BOTH tools would double-report overlapping home/username matches and drift. There must be ONE engine (P8). | two scanners with overlapping home/username rules |
| E3 | MEDIUM | Low | agent / token economy | efficiency | Deterministic leak-checking that needs no judgment currently has no agent-tailored output mode; an LLM surface either re-derives it or parses verbose human output, burning tokens. | no `--agent`/`--llm` mode in either tool |
| E4 | LOW | Low | maintainer | correctness | pubrun's `--check` SKIPS binary blobs (`_looks_binary` = `\x00`); a leak inside a binary should still be FLAGGED (human decision). | the pubrun `sanitize_paths.py` `_looks_binary`/`scan_text` |
| E5 | LOW | Low | maintainer | safety | `--fix` auto-rewriting `/home/<any>/...` -> `~/...` inside code/test fixtures can change behavior. It must be OPT-IN and interactive-confirm by default (`--yes`/`--force` to batch), NEVER wired into the pre-commit hook. | pubrun lesson #2; hook risk |
| E6 | LOW | Low | maintainer | self-cleanliness | The engine ships in the repo; it must not bake leak literals into its own source (our `local_leaks` uses fragment-assembly; pubrun derives needles at runtime). Keep runtime-derivation / fragment approach so the engine file is self-clean. | `local_leaks.py` fragment note; pubrun runtime needles |

## Proposed changes (ordered, validatable; checkpointed)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | E1,E6 | Create the unified engine `agent_workflows/leak_sanitizer.py` (stdlib only, self-clean via runtime-derivation + fragment-assembly): rulesets = home-user, home-any (anchored, keeps tail), hostname (FQDN + node + short label, runtime-derived), private-repo names, session-id, plus IP (v4/v6) available but CONFIG-GATED OFF by default (human: permissive IP is fine, opt-in). Modes: `--check` (report, exit nonzero), `--fix` (rewrite; INTERACTIVE-confirm per file/match by default, `--yes`/`--force` to batch, `--dry-run`), and `--agent` (precise, concise, machine-parseable output for an LLM caller - one line per finding `path:line:rule`, no prose footer). Scan modes preserved from local_leaks: working tree, `--history`, `--wheel`; plus pubrun's staged-blob scan for the hook. FLAG matches in binary blobs too (drop the binary skip, E4). | `agent_workflows/leak_sanitizer.py` (new) | Medium | unit tests: each ruleset matches/does-not-match fixtures; `--fix` rewrites + is interactive unless `--yes`; `--agent` emits parseable lines; IP off by default; binary match flagged; engine self-scan clean |
| 2 | E1 | Layered config: a TRACKED `.agents/leak-sanitizer-allow.toml` (committed baseline whitelist/blacklist that travels + is CI-deterministic; ships an allowlist for the public author email + repo origin + generic placeholders) and a GITIGNORED user config (`~/.config/agent-workflows/leak-sanitizer.<...>` or a repo-local `.leak-sanitizer-local.toml` - decide at review, OQ2) for machine-specific rules + `[rules] enabled`, `[ip] enabled`, and whitelist/blacklist entries each accepting regex OR glob OR literal. Missing config = safe defaults (home + hostname + identity on, IP off). Reuse the D93 config-split rationale. | `agent_workflows/leak_sanitizer.py`, new tracked allow file + `.example` | Medium | tests: allow entry exempts a line; blacklist adds a scrub; missing config = safe defaults; the local file is gitignored |
| 3 | E2,E3 | MIGRATE `local_leaks` onto the engine: make `agent_workflows/local_leaks.py` a thin shim that delegates to `leak_sanitizer` (or re-point `cli.py check-local-leaks` at the engine and keep `local_leaks` as a compatibility alias), so there is ONE code path and NO double-reporting. Preserve the existing `check-local-leaks` CLI surface + exit codes. The pre-commit hook now runs the engine in `--check` (staged-blob) mode. | `agent_workflows/local_leaks.py`, `agent_workflows/cli.py`, `.pre-commit-config.yaml` | Medium | `aw check-local-leaks` still works (same exit codes); pre-commit still blocks a planted leak; no double-report; the repo tree stays clean |
| 4 | E2 | Migrate tests + packaging: fold `tests/test_local_leaks.py` onto the engine (or add `tests/test_leak_sanitizer.py` and repoint), keep the wheel-token assertion in `test_packaging.py`, assert `agent_workflows/leak_sanitizer.py` ships. Ensure the engine self-scan (no baked literals) is tested. | `tests/*`, `tests/test_packaging.py` | Medium | full suite green; the guard still catches a planted leak; wheel token-free + engine module ships |
| 5 | - | Docs/decision sync: DECISIONS entry (pin at execution) recording the unified engine + the deterministic-checks-into-scripts principle (D-... ); update `.agents/prompts/README.md` / CONTRIBUTING references from "check-local-leaks" to note the unified sanitizer; CHANGELOG 1.3.0. Add a GUIDING_PRINCIPLES line for the deterministic-checks principle. Add a TODO item to AUDIT all workflows for deterministic work that can move to agent-friendly scripts (with `--agent`/`--llm` modes). | `DECISIONS.md`, `GUIDING_PRINCIPLES.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `TODO.md` | Low | entries present; links resolve; no em/en dashes |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Medium | complexity | The re-runnable CONFIG WIZARD (interactive setup that exposes existing config, explains pros/cons, walks whitelist/blacklist). Substantial interactive-UX + config-authoring work. | Order 2 of this Set (its own IPD), depends on this engine + config schema. |
| n/a | Medium | functionality | The AGENT/workflow rewire (thin orchestration consuming `--agent` output) + the OPTIONAL setup-repo install of the hook+CI (off by default) + making agents AWARE of the script even without hooks. | Order 3 of this Set (its own IPD), depends on this engine. |

## Scope check

- Over-scope: none. The wizard (Order 2) and the setup-repo/agent integration (Order 3) are explicitly deferred to their own IPDs. This IPD is the engine + config + migration only.
- Under-scope: the migration MUST NOT regress D92/D93/D94 (the leak guard, the hook, the quarantine lane) - all must still pass. Confirm the engine keeps the working-tree + `--history` + `--wheel` modes local_leaks had.

## Required tests / validation

- New `tests/test_leak_sanitizer.py`: per-ruleset match/no-match; `--fix` interactive-vs-`--yes`; `--agent` parseable output; IP off-by-default + opt-in on; binary-match flagged; config allow/blacklist/local-vs-tracked; engine source self-clean.
- Migrated guard: the pre-commit `--check` still blocks a planted leak; `aw check-local-leaks` unchanged exit codes; NO double-reporting.
- `tests/test_packaging.py`: wheel token-free AND `agent_workflows/leak_sanitizer.py` ships.
- Full suite `python -m pytest -q` GREEN; paste ACTUAL output (baseline 295 passed, 1 skipped; expect more with the engine tests, and the D92/D93 tests migrated not deleted).
- Cross-platform: engine derivation (hostname, $HOME, $USER/$USERNAME) degrades safely when a source is absent (CI matrix ubuntu/macos/windows).

## Spec / documentation sync

- DECISIONS (unified engine + deterministic-checks principle), GUIDING_PRINCIPLES (the principle), CONTRIBUTING (the sanitizer command), CHANGELOG 1.3.0, TODO (the workflow-audit follow-up).

## Open questions

- OQ1 (naming/shim): keep the `check-local-leaks` command name (delegating to the engine) and add a broader `aw sanitize` (or `aw leaks`) alias, or rename? Lean: keep `check-local-leaks` for continuity + add the engine; decide the public command name at review.
- OQ2 (gitignored config location): repo-local `.leak-sanitizer-local.toml` (like pubrun) vs `~/.config/agent-workflows/` (like our D93 hints). Lean: repo-local gitignored file for per-repo whitelist/blacklist (matches pubrun + travels with the checkout) PLUS the tracked allow file; a user-global layer can come later. Confirm.
- OQ3 (config filename): finalize the tracked/gitignored config filenames + `.example`.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

CHECKPOINTED EXECUTION: (1) engine + config; (2) tests for the engine; (3) migrate local_leaks/cli/hook onto it; (4) migrate tests + packaging; (5) docs/decision. Re-run the full suite at each checkpoint; pause and report if a checkpoint's scope grows (esp. the migration of shipped D92/D93 code).

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ3. Pin the DECISIONS number(s) at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute in checkpoints, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. Then Order 2 (wizard) and Order 3 (agent/install) IPDs follow.
