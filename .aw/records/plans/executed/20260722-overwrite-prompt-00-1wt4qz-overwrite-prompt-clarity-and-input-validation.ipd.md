# IPD: clear, self-documenting overwrite prompt with input validation

- Date: 2026-07-22
- Concern: installer UX / self-documenting + naive-user guidelines (the interactive overwrite prompt)
- Scope: the interactive "overwrite?" prompt in the installer (`agent_workflows/engine.py` `write_file`), plus the sibling delete prompt, and tests. Product code. Standalone (not part of a Set).
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1wt4qz
- Set: overwrite-prompt (overwrite prompt clarity and input validation)
- Order: 0
- Approval: 2026-07-22, human ("approved. Go!") after /plan-review (APPROVE WITH REVISIONS APPLIED; O4 added; OQ1/OQ2 resolved).

## Workflow history

- 2026-07-22 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Steps 1-5. Added the shared `prompt_choice` helper to `engine.py` (validate/re-ask, legend on help + invalid, `EOFError` -> default, `KeyboardInterrupt` re-raised, `on_diff` callback); rewired the overwrite prompt to `[y/N/d/help]` and the stale-shim delete prompt to `[y/N/help]` to use it. During execution a real bug was caught by the existing prompt tests: binding `input_fn=input` as a DEFAULT ARG captured the real builtin, so `mock.patch("builtins.input")` was bypassed and the Ctrl-C/EOF/diff tests failed; fixed by defaulting `input_fn`/`print_fn` to None and resolving to the builtins at CALL time. Added `PromptChoiceTests` (8 cases incl. KeyboardInterrupt-propagates and EOF-default) + an end-to-end invalid-then-overwrite test. DECISIONS D101 + CHANGELOG. Validation: no em/en dashes, `aw check-local-leaks .` clean, `python -m pytest -q` = 351 passed, 1 skipped (was 343; +8). Status approved -> executed; moved to `executed/`.
- 2026-07-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; O1-O4 (O4 added). Verified the prompt code (`engine.py:819-863`), the delete prompt (`:1040-1065`; confirmed it has NO loop today, single `input`), and the test harness (`test_installer.py:532-586`, incl. `test_diff_option_re_prompts`, `test_ctrl_c_aborts_install` exit 130, `test_eof_declines_install`). O4 (MEDIUM, FIXED): named the anti-regression invariant that the shared helper MUST re-raise `KeyboardInterrupt` (Ctrl-C aborts 130) and return the safe default on `EOFError` (never re-ask on EOF), so a naive catch-all does not break the two existing prompt tests; folded into Steps 3/4, Under-scope, and Required tests. O3 clarified (delete prompt has no loop today). OQ1/OQ2 resolved (accept `h`/`help`/`?` and `d`/`diff`; additive, no genuine trade-off, not escalated). No open questions remain. Readiness: GO - PENDING HUMAN APPROVAL.
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
| O3 | LOW | Low | naive user | consistency | The sibling delete prompt (`engine.py:1055`, `[y/N]`) has the same silent-coercion behavior and no help; it should be consistent (validate + re-ask; it has no diff, so no `d`). NOTE: unlike the overwrite prompt (which has a `while True` loop), the delete prompt has NO loop today (a single `input`, `:1053-1058`), so adding re-ask introduces a loop there - the shared helper (Step 3) provides it. | `engine.py:1053-1058` |
| O4 | MEDIUM | Low | maintainer | anti-regression | The re-ask loop / shared helper MUST preserve the two behaviors the existing tests pin: Ctrl-C (`KeyboardInterrupt`) PROPAGATES to abort the run with exit 130 (`test_ctrl_c_aborts_install`, `test_installer.py:538-558`), and EOF (`EOFError`) resolves to the SAFE DEFAULT (preserve/keep) and continues (`test_eof_declines_install`, `:562-581`). A naive "catch all exceptions and re-ask" helper would swallow `KeyboardInterrupt` and break abort-on-Ctrl-C. Raised by plan-review (PR-001). | `test_installer.py:538-581`; `engine.py:845-848` (current EOF handling) |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | O1,O2 | Rewrite the overwrite prompt to `Do you want to overwrite it? [y/N/d/help]: ` and add strict validation: accept ONLY blank (-> default No/preserve), `y`/`yes` (overwrite), `n`/`no` (preserve), `d`/`diff` (show differences, then re-ask), `h`/`help`/`?` (print the legend, then re-ask). ANY OTHER input reprints the legend and RE-ASKS (never coerced to a decision). The legend, shown on `help` and on invalid input, is exactly: `Y = Yes, OVERWRITE` / `N = No, do not overwrite (default)` / `D = Show me the differences` / `help = show this help`. Preserve the safe default (blank/EOFError -> No) and the non-interactive/`--yes` bypass unchanged. | `agent_workflows/engine.py` (`write_file`, `:836-863`) | Low | prompt string is `[y/N/d/help]`; `y`/`yes` overwrites; blank/`n` preserves; `d` shows diff + re-asks; `help`/`?`/invalid prints the legend + re-asks (no silent coerce); EOFError -> preserve; `--yes`/non-interactive path unchanged |
| 2 | O3 | Apply the same validation to the sibling delete prompt (`engine.py:1055`): `Do you want to delete it? [y/N/help]: ` (no `d`, nothing to diff), accept blank/`y`/`yes`/`n`/`no`/`h`/`help`/`?`, reject-and-re-ask on anything else, print a matching legend (`Y = Yes, DELETE` / `N = No, keep it (default)` / `help = show this help`). Safe default keep/no unchanged. | `agent_workflows/engine.py` (delete prompt, `:1055`) | Low | delete prompt is `[y/N/help]`; validates + re-asks; default keep; help legend shown; `--yes`/non-interactive unchanged |
| 3 | O1,O2,O4 | Refactor the input-legend-validate loop into ONE small shared helper (e.g. `_prompt_choice(question, choices, legend, *, default, on_diff=None)`) used by both prompts (P8, no divergent copies), returning the normalized choice. Keep it stdlib-only and testable (accept an injected input function or drive via monkeypatched `input`, matching the existing test style). PRESERVE INVARIANTS (O4/PR-001): `EOFError` -> return the safe default (do NOT re-ask on EOF, else a closed stdin loops forever); `KeyboardInterrupt` -> RE-RAISE (never caught/swallowed), so Ctrl-C still propagates to `main()` and aborts with exit 130. Only UNRECOGNIZED STRING input triggers the legend + re-ask. | `agent_workflows/engine.py` | Low | one helper backs both prompts; EOF returns the default (no infinite loop); KeyboardInterrupt propagates (abort 130 preserved); unit-tested directly (valid, invalid-then-valid, diff-then-choice, blank-default, EOF-default, Ctrl-C-propagates); both call sites use it |
| 4 | O1,O2,O3,O4 | Tests: extend the installer tests (`tests/test_installer.py`, which already forces interactivity via `mock.patch("agent_workflows.engine.is_interactive_session", return_value=True)` and scripts `input` via `mock_input.side_effect=[...]`; there is already a `test_diff_option_re_prompts` at `:585` to model). Cover: invalid input is re-asked, not treated as no (side_effect `["blah", "y"]` overwrites; `["blah", ""]` preserves); `help`/`?` prints the legend then re-asks; `d` shows the diff then re-asks; `y`/`yes` overwrites; blank/`n` preserves. PRESERVE the existing `test_ctrl_c_aborts_install` (exit 130) and `test_eof_declines_install` (preserve) - they MUST still pass unchanged (O4). Add analogous delete-prompt cases. | `tests/test_installer.py` | Low | full suite green; new cases pin validate/re-ask/legend; the Ctrl-C (130) and EOF (preserve) tests still pass unchanged; paste actual output |
| 5 | O1 | Docs/decision sync: a short DECISIONS entry (pin at execution) recording the clearer prompt + strict validation as a self-documenting-UX fix; CHANGELOG 1.3.0. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| Changing WHICH files prompt (e.g. prompting for non-shim framework files, which currently overwrite-with-backup by default) | Medium | functionality | That is a behavior change to the install model, not a prompt-clarity fix; out of scope here. | A separate IPD if desired. |
| A full TUI / arrow-key selector | Low | complexity | KISS: a validated text prompt meets the self-documenting bar; no new dependency. | n/a. |

## Scope check

- Over-scope: none. Two prompts + one shared helper + tests + docs. No change to what gets installed, the safe default, or the non-interactive/`--yes` paths.
- Under-scope: the fix MUST reject invalid input by re-asking (never coerce to a decision, O2); MUST keep the safe default (blank/EOF -> preserve/keep) and MUST re-raise `KeyboardInterrupt` so Ctrl-C still aborts with 130 (O4/PR-001); MUST NOT change the `--yes`/CI/non-tty bypass; and the two prompts MUST share one helper (P8).

## Required tests / validation

- `tests/test_installer.py` (forces a TTY via `mock.patch("agent_workflows.engine.is_interactive_session", return_value=True)` + scripts `input` via `mock_input.side_effect`, per the existing `test_diff_option_re_prompts` at `:585`): overwrite prompt - `y`/`yes` overwrites; blank and `n`/`no` preserve; `d` shows diff then re-asks; `help`/`?` and any invalid token print the legend and re-ask (assert the file is NOT silently preserved on a bare invalid token without a subsequent explicit choice); the existing EOF-preserve (`:562`) and Ctrl-C-abort-130 (`:538`) tests still pass unchanged (O4). Delete prompt - analogous without `d`.
- Full suite `python -m pytest -q` GREEN; paste ACTUAL output (baseline this session 343 passed, 1 skipped; expect additions).
- `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- DECISIONS (the clearer-prompt + validation fix), CHANGELOG 1.3.0. No user-facing doc lists the prompt text verbatim, so no other sync; if any does, update it.

## Open questions

- OQ1 (help token): RESOLVED (plan-review, toward the maintainer request + naive-user goal). Displayed hint is `[y/N/d/help]` (spelled-out `help`, as requested); the parser ALSO accepts `h` and `?` as help aliases (cheap, friendly, serves the self-documenting driver). No genuine trade-off; not escalated.
- OQ2 (diff verb alias): RESOLVED (plan-review). Accept both `d` and `diff` for show-differences (additive convenience, consistent with the clarity goal). No genuine trade-off; not escalated.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
