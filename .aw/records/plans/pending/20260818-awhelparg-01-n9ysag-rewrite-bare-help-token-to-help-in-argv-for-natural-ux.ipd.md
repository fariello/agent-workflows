# IPD: rewrite bare help token to --help in argv for natural UX

- Date: 2026-08-18
- Kind: child
- Concern: awhelparg Order 01 (TODO item #3). Users naturally type `aw help`, `aw ipd help`, or `aw plans help`, but argparse only understands `--help`, so those bare-`help` invocations error ("invalid choice", "unrecognized arguments") or behave unexpectedly instead of showing help. There is already a pre-parse argv rewriting stage in `_dispatch` (cli.py:4023-4031, the plans shim runs BEFORE `parser.parse_args`). The concern is to rewrite a standalone bare `help` token to `--help` at the position it appears, in that same pre-parse stage, so `help` in a command/subcommand position naturally shows help - WITHOUT clobbering a legitimate positional/option VALUE that happens to equal the string "help" (e.g. `aw backlog set x --message help`).
- Scope: `agent_workflows/cli.py` `_dispatch` pre-parse stage ONLY, plus a test. IN: a `_rewrite_help_token(argv)` helper near the existing plans shim (cli.py:4023) that converts a standalone `help` token to `--help` in place per a documented, guarded rule; wiring it into `_dispatch` before `parse_args` alongside the plans-shim rewrite; a test (`tests/test_help_token.py`) proving `aw help` / `aw ipd help` / `aw <noun> help` all yield help output and that a `help` value bound to a value-taking option is NOT clobbered. OUT: no change to argparse's own help formatting/content; no new first-class `help` subcommand object; no rewrite of a token that is a value bound to a value-taking option.
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awhelparg
- Order: 1
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: n9ysag

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO item 3 (bare help token -> --help).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Verified the pre-parse argv stage exists at cli.py:4023 (before parse_args) where _rewrite_help_token is placed. The guard errs conservatively (leaves a token untouched when unsure), so the residual ambiguity (store_true flag followed by `help`) is at worst a benign false-negative, not a clobber; acceptable. No blocking findings.

## Goal

Let users type `help` anywhere it reads naturally (`aw help`, `aw ipd help`, `aw plans help`) by
rewriting a standalone bare `help` token to `--help` in the same position, in the pre-parse argv stage
(alongside the existing plans shim), guarded by an explicit rule so a legitimate value equal to "help"
that is bound to a value-taking option is never clobbered.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: edit ONLY `agent_workflows/cli.py` and add ONE test file. The rewrite lives in the
pre-parse stage of `_dispatch` (cli.py:4023-4031), BEFORE `parser.parse_args`, next to the plans shim.
Do NOT touch the parser definitions or argparse's help machinery.

### Task group 1: argv rewrite helper (documented rule)

- [ ] E-01 In `agent_workflows/cli.py`, add a module-level helper `_rewrite_help_token(argv)` near the plans shim (cli.py:4023) that rewrites a standalone `help` token to `--help` in place. THE DOCUMENTED RULE: walk the argv list left to right; rewrite a token to `--help` when and only when the token is exactly `"help"` AND it is NOT immediately preceded by a value-taking option (i.e. the previous token is not one of the known value-taking option flags, and the previous token is not an unterminated short/long option that consumes the next word). Concretely, guard against clobbering an option value: if the immediately preceding argv token starts with `-` and is NOT a bare `--` and is NOT itself a `--flag=value` form, treat the current `help` as that option's value and leave it untouched; otherwise rewrite it to `--help`. This is the conservative "not preceded by a value-expecting option token" heuristic named in the concern. Use this exact implementation (keep the name + signature):
  ```python
  def _rewrite_help_token(argv: List[str]) -> List[str]:
      """Rewrite a standalone bare ``help`` token to ``--help`` in-position.

      Natural-UX shim: ``aw help``, ``aw ipd help``, ``aw <noun> help`` should all
      show the corresponding help, but argparse only understands ``--help``. We
      rewrite a bare ``help`` word to ``--help`` at the position it appears, in the
      pre-parse stage (alongside the plans shim), BEFORE ``parse_args``.

      Guard (documented rule): a token equal to ``"help"`` is rewritten to
      ``--help`` UNLESS it is immediately preceded by a value-taking option token -
      i.e. the previous token starts with ``-``, is not the bare ``--`` separator,
      and is not a ``--flag=value`` self-contained form. In that case the ``help``
      is the option's VALUE (e.g. ``--message help``) and is left untouched. This
      is the conservative "not preceded by a value-expecting option" heuristic, so
      command/subcommand-position ``help`` (position 0, or after a noun/verb bare
      word) is rewritten while a legitimate option value equal to "help" is not.
      """
      out: List[str] = []
      for idx, tok in enumerate(argv):
          if tok == "help":
              prev = argv[idx - 1] if idx > 0 else None
              preceded_by_value_option = (
                  prev is not None
                  and prev.startswith("-")
                  and prev != "--"
                  and "=" not in prev
              )
              if not preceded_by_value_option:
                  out.append("--help")
                  continue
          out.append(tok)
      return out
  ```
  - Depends on: none
  - Expected outcome: `_rewrite_help_token(["help"])` -> `["--help"]`; `_rewrite_help_token(["ipd", "help"])` -> `["ipd", "--help"]`; `_rewrite_help_token(["plans", "help"])` -> `["plans", "--help"]`; `_rewrite_help_token(["backlog", "set", "x", "--message", "help"])` -> unchanged (the `help` is `--message`'s value); `_rewrite_help_token(["backlog", "set", "x", "--message=help"])` -> unchanged.
  - Execution state: pending

### Task group 2: wire into the pre-parse stage

- [ ] E-02 In `_dispatch` (cli.py:4018), immediately AFTER the existing plans-shim rewrite block that produces `argv_list`/`argv` (cli.py:4023-4030) and BEFORE `args = parser.parse_args(argv)` (cli.py:4031), apply the helper so both rewrites compose. Insert:
  ```python
      argv_list = _rewrite_help_token(argv_list)
      argv = argv_list
  ```
  This runs after the plans shim has already normalized `argv_list`, and reassigns `argv` so `parser.parse_args(argv)` sees the `help` -> `--help` rewrite. The plans shim only sets `argv = argv_list` inside its `if`, so ensure `argv_list` is always assigned to `argv` before parse (it is: `argv_list` is built unconditionally at cli.py:4023 and the two new lines run unconditionally). Confirm `List` is imported in cli.py's typing imports (it is used elsewhere); if not, add it to the existing `from typing import ...` line.
  - Depends on: E-01
  - Expected outcome: `aw help`, `aw ipd help`, and `aw plans help` all display the corresponding help text (exit 0, help body printed); the plans shim continues to work (e.g. `aw plans index` still routes to `plans-index`); a `help` bound to an option value is passed through untouched to argparse.
  - Execution state: pending

### Task group 3: test

- [ ] E-03 Add `tests/test_help_token.py` with a `unittest.TestCase` `HelpTokenTests`. Cover BOTH the pure-function guard and the end-to-end dispatch:
  (a) Unit the helper directly: `from agent_workflows.cli import _rewrite_help_token` and assert the five outcomes listed in E-01's expected outcome (bare `help` -> `--help`; `ipd help` -> `ipd --help`; `plans help` -> `plans --help`; `--message help` unchanged; `--message=help` unchanged).
  (b) End-to-end: invoke the CLI in-process via `main([...])` (import `from agent_workflows.cli import main`), capturing stdout with `contextlib.redirect_stdout(io.StringIO())`. argparse prints `--help` to stdout and raises `SystemExit(0)`, so wrap each in `with self.assertRaises(SystemExit) as cm:` and assert `cm.exception.code in (0, None)` AND the captured text is non-empty / contains a usage marker (e.g. `"usage"`). Cover `main(["help"])`, `main(["ipd", "help"])`, and `main(["plans", "help"])`.
  (c) Guard end-to-end: prove a value literally "help" is NOT clobbered - assert that `_rewrite_help_token(["backlog", "set", "x", "--message", "help"])` leaves the trailing `help` intact (already in (a)); this pins the "not clobbered" contract without needing a live backlog fixture.
  Run the full serial suite and paste the tail.
  - Depends on: E-01,E-02
  - Expected outcome: all assertions pass; the three `help` forms print usage/help and exit 0; the option-value `help` is preserved verbatim; full serial suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Pre-parse argv rewriting is an established pattern here: the plans shim already mutates argv before argparse in `_dispatch` (cli.py:4023-4031), which builds `argv_list = list(sys.argv[1:] if argv is None else argv)` and, for `plans <verb>`, rewrites to the `plans-<verb>` parser. `parser.parse_args(argv)` follows at cli.py:4031. The help rewrite belongs in the SAME stage, not deeper in argparse.
- `main` (cli.py:4244) simply calls `_dispatch(argv)` inside a KeyboardInterrupt/EOFError guard and RETURNS the int (does not `sys.exit`), so in-process test callers reading the return value keep working. But argparse's `--help` action itself raises `SystemExit(0)` before `_dispatch` returns, so end-to-end help tests must catch `SystemExit`.
- argparse's own `-h/--help` is the target form; the rewrite converts the bare word to the flag argparse already understands, so NO new subparser or action is needed. `aw <noun> help` maps to the noun's subparser `--help` because the rewrite preserves position.
- Option-value positions must be respected: the guard must not rewrite a `help` that follows a value-taking option (e.g. `--message help`). The chosen conservative heuristic (E-01) treats a `help` immediately preceded by a `-`-prefixed non-`--`, non-`=`-bearing token as that option's value and leaves it alone.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | argv is already rewritten pre-parse for plans (cli.py:4023-4031). | The help rewrite is a small addition to an existing, proven stage - low risk; compose after the plans shim. |
| F2 | argparse understands `--help` everywhere a parser/subparser exists. | Rewriting `help` -> `--help` in-position makes `aw <noun> help` work without per-parser wiring. |
| F3 | A value equal to "help" is legitimate (e.g. `--message help`). | A position guard is required so the rewrite only fires for command/subcommand-position tokens, not option values. |
| F4 | `--help` raises `SystemExit(0)`; `main` otherwise returns an int. | End-to-end help tests must catch `SystemExit` and assert exit code 0/None + non-empty usage output. |

## Proposed changes (ordered, validatable)

1. Add the guarded `_rewrite_help_token(argv)` helper with the documented rule (E-01). 2. Wire it into `_dispatch` after the plans shim and before `parse_args` (E-02). 3. Add `tests/test_help_token.py` covering the three help forms + the option-value guard, plus the full serial suite (E-03).

## Deferred / out of scope (with reason)

- A first-class `help` subcommand object (e.g. `aw help <noun>` with semantics richer than argparse's `--help`): out of scope; the natural-UX goal is met by the flag rewrite.
- Changing argparse's help text formatting/content: out of scope.
- Handling every exotic guard corner (e.g. a value-taking option whose value legitimately equals "help" AND appears in `--flag=help` form): the `=`-bearing form is already left untouched by the rule; a separate `--flag help` form is guarded by the preceding-token check. No further heuristic added.

## Scope check

- Over-scope: none - a single guarded helper plus two wiring lines in an existing stage, plus one test file.
- Under-scope: none - all natural `help` positions (top-level, noun-level, verb-level) work and the option-value guard is tested both as a pure function and end-to-end.

## Required tests / validation

`tests/test_help_token.py` (E-03: helper unit cases + three end-to-end help forms + the option-value guard) plus the full serial suite to confirm the new argv rewrite does not perturb existing command dispatch (notably the plans shim). Each V-item pins one E.

## Spec / documentation sync

Behavior is discoverable via `aw --help` (the top-level help still renders). Optionally mention in usage that `help` is accepted as a synonym for `--help`; no separate spec doc transition is required for this Order (an orchestrator, if any, advances any owning spec). No AGENTS.md change.

## Open questions

### OQ-01: should ALL occurrences of a bare `help` token be rewritten, or only the first command/subcommand-position one?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: Rewrite EACH standalone `help` token at the position it appears (subject to the E-01 guard), not just the first. The first `--help` argparse encounters short-circuits parsing anyway, so rewriting all guarded occurrences is simplest and harmless, and the guard already prevents clobbering option values. Non-blocking; implemented as the per-token loop in `_rewrite_help_token`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python/REPL or pytest run of `_rewrite_help_token` showing the five documented outcomes: `["help"]`->`["--help"]`, `["ipd","help"]`->`["ipd","--help"]`, `["plans","help"]`->`["plans","--help"]`, `["backlog","set","x","--message","help"]` unchanged, `["backlog","set","x","--message=help"]` unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw help`, `aw ipd help`, and `aw plans help` runs each showing the expected help output (exit 0), plus one `aw plans index --help`-style or `aw plans index` run proving the plans shim still composes with the new rewrite.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `pytest tests/test_help_token.py -p no:xdist -q` (passing) including the guard assertion proving a `help` value bound to an option is not rewritten, plus the full serial suite tail (no regressions).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the changed
`agent_workflows/cli.py` + the new `tests/test_help_token.py` path-scoped (never `git add -A`), never
pushes, and transitions the plan into `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 01 of awhelparg; depends on
nothing.
