# IPD: Assess self-documentation - make the `aw` CLI teach at the point of use

- Date: 2026-07-20
- Concern: self-documentation
- Scope: the in-product learn-as-you-go surface, i.e. the `aw` (`agent-workflows`) CLI: `--help`/usage text, first-run/onboarding, error messages, and discoverability. Excludes repository prose docs (that is the `documentation` lens) and the framework's own `.agents/workflows/` content.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-20 /assess self-documentation (opencode its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 4 changes.
- 2026-07-20 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed. Verified all S1-S4 claims against source (`--status` has no `choices=` and `normalize_status` maps unknowns to `LEGACY_GROUP`; `(D93)` in the check-local-leaks help; `local_leaks.main` clean path silent). Broadened S2's sweep + test to include the runtime `print(...)` jargon at `local_leaks.py:463` (PR-001/002). Resolved OQ2 from evidence (handler-side validation, not `choices=`, to preserve legacy-token tolerance). Resolved OQ1 with the human (always print the clean-path confirmation, one line to stderr). Status -> reviewed.

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
| 1 | S1 | Make `aw plans --status` teach: when the given value is not a recognized readiness status, print a clear message naming the valid set (draft, to-review, reviewed, approved, auto-approved, executed, superseded, not-executed, reusable) via `term.status("warn", ...)` and exit without silently returning an empty board. Surface the recognized vocabulary from `plans.RECOGNIZED` (single source, `plans.py:28`), not a hardcoded list. Validate HANDLER-SIDE (not argparse `choices=`), because `normalize_status` (`plans.py:101-114`) intentionally tolerates legacy/alias tokens and a hard `choices=` would regress that (OQ2, resolved from evidence). | `agent_workflows/cli.py` | Low | `aw plans . --status bogus` prints the valid-status list; a valid status still filters correctly; unit/CLI test asserts the message |
| 2 | S2 | Remove the internal `(D93)` reference from the user-facing `check-local-leaks` help/description; keep the plain-language capability sentence (decision provenance stays in DECISIONS.md/CHANGELOG, not in `--help`). Sweep for any other `(D<n>)` in ALL user-facing strings: argparse `help=`/`description=`, `Term.status` messages, AND runtime `print(...)` messages - note the confirmed extra instance at `agent_workflows/local_leaks.py:463` ("Local-leak(s) found (D92/D93):") which is a `print`, not a `Term` string (plan-review PR-001). | `agent_workflows/cli.py`, `agent_workflows/local_leaks.py` | Low | `aw --help` and `aw check-local-leaks --help` contain no `(D..)`; the local-leaks fail-message and confirmation contain no `(D..)`; a test asserts no `(D<digits>)` in BOTH the parser help output AND the local_leaks user-facing message strings (plan-review PR-002) |
| 3 | S3 | Add a short discoverability hint to the top-level `install` command description so `aw --help` reveals the batch form, e.g. "Install or update the framework in a repo (idempotent); `install all` does every configured repo." | `agent_workflows/cli.py` | Low | `aw --help` install line mentions `install all` |
| 4 | S4 | Print a brief positive confirmation on the clean path of `check-local-leaks`, ALWAYS, one line to stderr (OQ1 resolved: no TTY gating, no `--quiet`), e.g. `No local leaks found.`. Keep exit code 0. | `agent_workflows/local_leaks.py` (and/or the CLI handler) | Low | `aw check-local-leaks .` on a clean repo prints the one-line confirmation to stderr and exits 0; the pre-commit hook + CI still show a clean pass |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | n/a | No findings deferred; all are Low Remediation Risk and proposed. | n/a |

Scope note (Complexity axis): deliberately NOT proposing shell autocompletion, an interactive TUI, or a `--examples` system - those are larger and the current help + first-run nudge already meet the novice bar. This IPD only closes the specific teach-at-point-of-use gaps found.

## Scope check

- Over-scope: none. Each step traces to a found gap. Autocompletion/TUI explicitly excluded.
- Under-scope: none outstanding. Step 4's clean-path confirmation is one line to stderr, always (OQ1 resolved); it does not hide the fail case (fails still print findings + a nonzero exit).

## Required tests / validation

- CLI/unit tests (stdlib unittest, run on the 3.9-3.14 matrix): `aw plans --status <bogus>` emits the valid-status list and does not silently return empty (S1); no `(D<n>)` remains in user-facing strings (S2 - assert over BOTH the parser help output AND the `local_leaks` runtime message strings, per PR-002); `aw --help` install description mentions `install all` (S3); `aw check-local-leaks .` on a clean temp repo prints a confirmation and exits 0 (S4).
- Manual: eyeball `aw --help`, `aw plans --help`, `aw check-local-leaks --help`, and the S1 error path for tone/clarity.
- Full suite `python -m pytest -q` stays green; paste ACTUAL output (baseline 282 passed, 1 skipped; expect a few more from the new assertions).
- `aw check-local-leaks .` stays clean on the edited sources (no new leaks).

## Spec / documentation sync

- Behavior change is user-facing CLI text/help only (no API/format change). If Step 3's wording or Step 1's error text changes what the README describes, sync the README `aw` command section (small). No DECISIONS entry required (these are clarity fixes applying existing principles); add one only if review judges the `--status` validation a notable behavior change.

## Open questions

- OQ1 (S4 quietness): RESOLVED (human, 2026-07-20 /plan-review) - ALWAYS print the clean-path confirmation, one line to stderr, on every run (interactive and under pre-commit/CI). No TTY gating and no `--quiet` flag. Encoded in Step 4.
- OQ2 (S1 mechanism): RESOLVED from repo evidence (plan-review, PR-003) - validate HANDLER-SIDE, not via argparse `choices=`. Evidence: `plans.normalize_status` (`agent_workflows/plans.py:101-114`) deliberately lowercases and legacy-maps a raw token, returning `LEGACY_GROUP` for unrecognized tokens; a hard `choices=` set would REJECT legacy/alias tokens that `aw plans` currently accepts, a behavior regression. So Step 1 validates in the handler against `plans.RECOGNIZED` (the single-source vocabulary, `plans.py:28`) and prints the valid set on a miss. No human decision needed; recorded here.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review this IPD (optionally run `plan-review`; sets `Status: reviewed`). Resolve OQ1-OQ2.
2. On human approval, set `Status: approved` (+ `Approval:`), execute the ordered changes, run validation, sync the README if wording changed; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
