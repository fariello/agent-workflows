# IPD: Assess self-documentation - make the `aw` CLI teach at the point of use

- Date: 2026-07-20
- Concern: self-documentation
- Scope: the in-product learn-as-you-go surface, i.e. the `aw` (`agent-workflows`) CLI: `--help`/usage text, first-run/onboarding, error messages, and discoverability. Excludes repository prose docs (that is the `documentation` lens) and the framework's own `.agents/workflows/` content.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-20 /assess self-documentation (opencode its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 4 changes.

## Goal

Make the product teach a naive user WHILE they use it, without reaching for external docs. The `aw` CLI is the in-product surface. It is already good (clear command list, per-subcommand help with defaults, a first-run "Not configured, run 'aw setup'" nudge, and unknown-command errors that list valid choices). This assessment finds the specific places a user would still have to guess or look something up, and proposes making the CLI itself teach them (better help text, an actionable error, less internal jargon), which the lens says is almost always low Remediation Risk and high value.

## Project conventions discovered (Step 0)

- Project intent/stack: portable AI-agent workflow framework + pip/PyPI package `agent_workflows`, CLI `aw` (also `agent-workflows`, `agentwf`), Python 3.9+ stdlib-only. The user-facing product IS the CLI plus the installed workflow files.
- Guiding principles: `GUIDING_PRINCIPLES.md` (esp. self-documenting, KISS).
- Plans lifecycle: `.agents/plans/pending/` + `YYYYMMDD-HHMM-NN-<slug>.md`; IPD born `to-review`.
- Contributor contract: `AGENTS.md`, `CONTRIBUTING.md`. No em/en dashes in authored Markdown.
- Run-record home `workflow-artifacts/` is now gitignored (D92/D93), so this run's record is written there LOCAL-ONLY, not committed (the same convention conflict recorded as F5 in the documentation-assessment IPD 20260719-2354-01; not re-raised here).
- CLI structure: `agent_workflows/cli.py` `_build_parser()` (argparse subparsers) + `_dispatch()`; message output via `Term.status(level, msg)`.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Lead personas: complete novice (primary), UI/UX engineer, power user. All are in-product clarity gaps; fixes are Low Remediation Risk.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| S1 | MEDIUM | Low | novice | errors that teach + discoverability | `aw plans --status <bogus>` silently prints "No plans found" (or an empty board) - it neither reports that the value was unrecognized nor lists the valid readiness statuses. A user who mistypes (`pendign`, `approve`) gets a misleading empty result and learns nothing. `--status` has no `choices=` and `normalize_status` maps unknown tokens to a group silently. | `agent_workflows/cli.py:148-152` (no `choices=`), `:828-831` (`normalize_status` then filter) |
| S2 | LOW | Low | novice | assumed domain knowledge (jargon) | The user-facing help for `check-local-leaks` ends with "(D93)" - an internal DECISIONS-log reference that means nothing to a user and reads as unexplained jargon in `aw --help` and `aw check-local-leaks --help`. | `agent_workflows/cli.py:220-224` (`help=`/`description=` string contains `(D93)`) |
| S3 | LOW | Low | novice / power user | discoverability | `aw install`'s `targets` help mentions `'all'`, but bare `aw --help`'s command list shows only `install` with no hint that `install all` (batch) exists; the batch capability is discoverable only by reading the `install` subcommand help or the README. A one-line pointer in the top-level `install` description would surface it. | `aw --help` command list vs `cli.py` install `targets` help |
| S4 | LOW | Low | novice | errors that teach / next step | `aw check-local-leaks` on a leak prints the findings and a remediation hint (good), but the SUCCESS/empty path prints nothing (silent exit 0). A brief "no local leaks found" confirmation would teach the user the check ran and passed (consistency with `aw plans`/`status` which always say something). | `agent_workflows/local_leaks.py` `main()` (returns 0 with no message when clean) |

## Proposed changes (ordered, validatable)

Fix by default; keep edits concise (Complexity axis - do not over-build).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | S1 | Make `aw plans --status` teach: when the given value is not a recognized readiness status, print a clear message naming the valid set (draft, to-review, reviewed, approved, auto-approved, executed, superseded, not-executed, reusable) via `term.status("warn", ...)` and exit without silently returning an empty board. Prefer surfacing the recognized vocabulary from `plans` (single source) over hardcoding. Consider `choices=` only if it does not break the legacy-token/alias handling; otherwise validate in the handler. | `agent_workflows/cli.py` | Low | `aw plans . --status bogus` prints the valid-status list; a valid status still filters correctly; unit/CLI test asserts the message |
| 2 | S2 | Remove the internal `(D93)` reference from the user-facing `check-local-leaks` help/description; keep the plain-language capability sentence (decision provenance stays in DECISIONS.md/CHANGELOG, not in `--help`). Sweep for any other `(D<n>)` in user-facing `help=`/`description=`/`Term` message strings and strip them. | `agent_workflows/cli.py`, `agent_workflows/local_leaks.py` | Low | `aw --help` and `aw check-local-leaks --help` contain no `(D..)`; a test greps user-facing help for `(D<digits>)` and finds none |
| 3 | S3 | Add a short discoverability hint to the top-level `install` command description so `aw --help` reveals the batch form, e.g. "Install or update the framework in a repo (idempotent); `install all` does every configured repo." | `agent_workflows/cli.py` | Low | `aw --help` install line mentions `install all` |
| 4 | S4 | Print a brief positive confirmation on the clean path of `check-local-leaks` (e.g. `term.status("ok", "No local leaks found.")` to stderr/stdout consistent with other commands), so a passing run is not silent. Keep exit code 0. | `agent_workflows/local_leaks.py` (and/or the CLI handler) | Low | `aw check-local-leaks .` on a clean repo prints a confirmation and exits 0; the pre-commit/CI invocation stays quiet-enough (confirm it does not break the hook's expectations) |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | n/a | No findings deferred; all are Low Remediation Risk and proposed. | n/a |

Scope note (Complexity axis): deliberately NOT proposing shell autocompletion, an interactive TUI, or a `--examples` system - those are larger and the current help + first-run nudge already meet the novice bar. This IPD only closes the specific teach-at-point-of-use gaps found.

## Scope check

- Over-scope: none. Each step traces to a found gap. Autocompletion/TUI explicitly excluded.
- Under-scope: confirm Step 4's confirmation message does not make the pre-commit hook / CI output noisy in a way that hides the fail case; if quiet-by-default is preferred for the hook, gate the confirmation behind an interactive/TTY check or a `--quiet` default for the hook invocation (decide at review, OQ1).

## Required tests / validation

- CLI/unit tests (stdlib unittest, run on the 3.9-3.14 matrix): `aw plans --status <bogus>` emits the valid-status list and does not silently return empty (S1); no `(D<n>)` remains in user-facing help strings (S2 - a grep-style test over the parser's help output); `aw --help` install description mentions `install all` (S3); `aw check-local-leaks .` on a clean temp repo prints a confirmation and exits 0 (S4).
- Manual: eyeball `aw --help`, `aw plans --help`, `aw check-local-leaks --help`, and the S1 error path for tone/clarity.
- Full suite `python -m pytest -q` stays green; paste ACTUAL output (baseline 282 passed, 1 skipped; expect a few more from the new assertions).
- `aw check-local-leaks .` stays clean on the edited sources (no new leaks).

## Spec / documentation sync

- Behavior change is user-facing CLI text/help only (no API/format change). If Step 3's wording or Step 1's error text changes what the README describes, sync the README `aw` command section (small). No DECISIONS entry required (these are clarity fixes applying existing principles); add one only if review judges the `--status` validation a notable behavior change.

## Open questions

- OQ1 (S4 quietness): should the clean-path confirmation always print, or be suppressed when invoked non-interactively (pre-commit/CI) to keep those logs quiet? Lean: print to stderr and keep it one line; the hook already tolerates the warn/advisory lines. Confirm.
- OQ2 (S1 mechanism): validate `--status` via argparse `choices=` (rejects before dispatch, uniform error) or in the handler (allows alias/legacy-token tolerance with a custom teaching message)? Lean: handler-side, to preserve any alias tolerance and give a friendlier message. Confirm.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review this IPD (optionally run `plan-review`; sets `Status: reviewed`). Resolve OQ1-OQ2.
2. On human approval, set `Status: approved` (+ `Approval:`), execute the ordered changes, run validation, sync the README if wording changed; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
