# IPD: clear, self-documenting overwrite prompt with input validation

- Date: 2026-07-22
- Concern: installer UX / self-documenting + naive-user guidelines (the interactive overwrite prompt)
- Scope: the interactive "overwrite?" prompt in the installer (`agent_workflows/engine.py` `write_file`), plus the sibling delete prompt, and tests. Product code. Standalone (not part of a Set).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-22 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer request. The prompt `Do you want to overwrite it? [y/N/d]:` is unclear (what is `d`?), and any input other than blank/y/n/d is silently coerced to "no" instead of being rejected and re-asked - a self-documenting / intuitive / naive-user guideline violation.

## Goal

Make the installer's overwrite prompt self-documenting and strict: the option letters are explained, a `help` option shows what each letter does, and any unrecognized input is rejected and the question re-asked (never silently coerced to a decision). The safe default (no / preserve) is unchanged.

Why it matters: `[y/N/d]` gives no clue that `d` means "show differences", and today a typo like `yes please` or `overwrite` falls through to "no" silently (`engine.py:857-858`), so a user who thinks they said yes actually preserved the file. That violates the self-documenting and naive-user principles and can surprise a user into the wrong outcome.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` P3 (self-documenting and learn-as-you-go), P9 (design instructions for the reader), P10 (safety: preserve is the safe default), P12 (self-contained prompts). No em/en dashes.
- Current prompt (verified): `engine.py:838-863`, inside `write_file`, fires only for a CUSTOMIZED command shim in an interactive session (`is_shim_customized_vs_expected` at `:827`, `is_interactive_session` at `:835`). Loop: reads `input("Do you want to overwrite it? [y/N/d]: ").strip().lower()`; `d` -> `print_shim_diff(...)` then re-prompt; EOFError -> treated as `n`; ANY OTHER input -> `break` and is then treated as not-yes (preserve) at `:858`. So invalid input is silently coerced to no, and `d` is undocumented.
- Sibling prompt (verified): `engine.py:1055` `input("Do you want to delete it? [y/N]: ")` - a delete prompt with the same silent-coercion shape and no `help`.
- The safe default is preserve/no (capital `N`), and non-interactive / `--yes` / CI paths do NOT prompt (`is_interactive_session` returns False); this IPD does not change those paths.
- `print_shim_diff` (`engine.py:1723-1748`) renders the colorized unified diff `d` shows.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| O1 | MEDIUM | Low | naive user | self-documenting | `[y/N/d]` does not say what `d` does; a first-time user cannot tell `d` = show differences. | `engine.py:841` |
| O2 | MEDIUM | Low | any user | correctness / surprise | Any input other than blank/`y`/`yes`/`d` is silently coerced to "no/preserve" (`:857-858`), so a mistyped affirmative silently preserves; input is not validated or re-asked. | `engine.py:857-858` |
| O3 | LOW | Low | naive user | consistency | The sibling delete prompt (`engine.py:1055`, `[y/N]`) has the same silent-coercion behavior and no help; it should be consistent (validate + re-ask; it has no diff, so no `d`). | `engine.py:1055` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | O1,O2 | Rewrite the overwrite prompt to `Do you want to overwrite it? [y/N/d/help]: ` and add strict validation: accept ONLY blank (-> default No/preserve), `y`/`yes` (overwrite), `n`/`no` (preserve), `d`/`diff` (show differences, then re-ask), `h`/`help`/`?` (print the legend, then re-ask). ANY OTHER input reprints the legend and RE-ASKS (never coerced to a decision). The legend, shown on `help` and on invalid input, is exactly: `Y = Yes, OVERWRITE` / `N = No, do not overwrite (default)` / `D = Show me the differences` / `help = show this help`. Preserve the safe default (blank/EOFError -> No) and the non-interactive/`--yes` bypass unchanged. | `agent_workflows/engine.py` (`write_file`, `:836-863`) | Low | prompt string is `[y/N/d/help]`; `y`/`yes` overwrites; blank/`n` preserves; `d` shows diff + re-asks; `help`/`?`/invalid prints the legend + re-asks (no silent coerce); EOFError -> preserve; `--yes`/non-interactive path unchanged |
| 2 | O3 | Apply the same validation to the sibling delete prompt (`engine.py:1055`): `Do you want to delete it? [y/N/help]: ` (no `d`, nothing to diff), accept blank/`y`/`yes`/`n`/`no`/`h`/`help`/`?`, reject-and-re-ask on anything else, print a matching legend (`Y = Yes, DELETE` / `N = No, keep it (default)` / `help = show this help`). Safe default keep/no unchanged. | `agent_workflows/engine.py` (delete prompt, `:1055`) | Low | delete prompt is `[y/N/help]`; validates + re-asks; default keep; help legend shown; `--yes`/non-interactive unchanged |
| 3 | O1,O2 | Refactor the input-legend-validate loop into ONE small shared helper (e.g. `_prompt_choice(question, choices, legend, *, default, on_diff=None)`) used by both prompts (P8, no divergent copies), returning the normalized choice. Keep it stdlib-only and testable (accept an injected input function or drive via monkeypatched `input`, matching the existing test style). | `agent_workflows/engine.py` | Low | one helper backs both prompts; unit-tested directly (valid, invalid-then-valid, diff-then-choice, blank-default, EOF); both call sites use it |
| 4 | O1,O2,O3 | Tests: extend the installer tests (`tests/test_installer.py`, which already forces interactivity and scripts `input`) to cover: invalid input is re-asked (not treated as no); `help`/`?` prints the legend then re-asks; `d` shows the diff then re-asks; `y`/`yes` overwrites; blank/`n` preserves; EOFError preserves; the delete prompt likewise. | `tests/test_installer.py` | Low | full suite green; the new cases pin the validate/re-ask/legend behavior; paste actual output |
| 5 | O1 | Docs/decision sync: a short DECISIONS entry (pin at execution) recording the clearer prompt + strict validation as a self-documenting-UX fix; CHANGELOG 1.3.0. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| Changing WHICH files prompt (e.g. prompting for non-shim framework files, which currently overwrite-with-backup by default) | Medium | functionality | That is a behavior change to the install model, not a prompt-clarity fix; out of scope here. | A separate IPD if desired. |
| A full TUI / arrow-key selector | Low | complexity | KISS: a validated text prompt meets the self-documenting bar; no new dependency. | n/a. |

## Scope check

- Over-scope: none. Two prompts + one shared helper + tests + docs. No change to what gets installed, the safe default, or the non-interactive/`--yes` paths.
- Under-scope: the fix MUST reject invalid input by re-asking (never coerce to a decision, O2); MUST keep the safe default (blank/EOF -> preserve/keep); MUST NOT change the `--yes`/CI/non-tty bypass; and the two prompts MUST share one helper (P8).

## Required tests / validation

- `tests/test_installer.py` (forces a TTY + scripts `input`, per the existing pattern): overwrite prompt - `y`/`yes` overwrites; blank and `n`/`no` preserve; `d` shows diff then re-asks; `help`/`?` and any invalid token print the legend and re-ask (assert the file is NOT silently preserved on a bare invalid token without a subsequent explicit choice); EOFError preserves. Delete prompt - analogous without `d`.
- Full suite `python -m pytest -q` GREEN; paste ACTUAL output (baseline this session 343 passed, 1 skipped; expect additions).
- `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- DECISIONS (the clearer-prompt + validation fix), CHANGELOG 1.3.0. No user-facing doc lists the prompt text verbatim, so no other sync; if any does, update it.

## Open questions

- OQ1 (help token): prompt as `[y/N/d/help]` (spelled-out `help`, per the maintainer's suggestion) - confirmed by the request. Also accept `h` and `?` as aliases for help? Lean: yes, accept `h`/`help`/`?` all as help (cheap, friendly); the displayed hint stays `[y/N/d/help]`. Confirm at review.
- OQ2 (diff verb alias): also accept `diff` as a synonym for `d`? Lean: yes, accept `d`/`diff`. Confirm at review.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
