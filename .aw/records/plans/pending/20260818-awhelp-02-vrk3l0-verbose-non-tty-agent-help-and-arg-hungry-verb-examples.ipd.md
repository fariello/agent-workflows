# IPD: verbose non-TTY agent help and arg-hungry verb examples

- Date: 2026-08-18
- Kind: child
- Concern: awhelp Order 02 (spec 20260818-1525-01 goal G6; TODO items 4, 10, 13, 14, 29, 31). A coding agent (no TTY, cannot explore interactively) reaches for `aw --help` first, but the top-level parser (cli.py:378-383) has a one-line `description` and NO epilog, so `aw --help` never tells an agent WHEN or WHY to reach for `aw` versus doing the work by hand, and shows no worked examples. Separately, the "arg-hungry" verbs (`ipd`, `show`, `storage`) fail unhelpfully when a required argument is missing: argparse prints a bare `error: the following arguments are required: ...` usage line with no example of a correct invocation, which is exactly the moment an agent needs a copy-pasteable example. This Order adds a verbose, agent-oriented top-level epilog with a "when/why to use aw" block plus common examples, and enriches the arg-hungry verbs so a missing-arg or `--help` prints a usage-plus-examples block instead of a bare error. Text-only: verb behavior is unchanged.
- Scope: `agent_workflows/cli.py` (the top-level `argparse.ArgumentParser(...)` at cli.py:378-383 - add an `epilog=` and `formatter_class` retention; the `ipd`/`show`/`storage` subparsers - add `epilog=`/richer `description` and/or a friendly missing-arg message) plus a new test `tests/test_help_verbose.py`. IN: a top-level epilog with a "when/why to use aw" block and 4-6 worked examples aimed at a non-TTY agent; an examples/usage block on the arg-hungry verbs' `--help`; a friendlier missing-required-arg path that surfaces the examples. OUT: rewriting the per-verb `_DESCRIPTIONS` jargon (awhelp Order 01); `--json`/exit-code documentation (awhelp Order 03); any change to argument parsing semantics or dispatch (a missing required arg still fails with a nonzero exit - only the MESSAGE improves).
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awhelp
- Order: 2
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: vrk3l0

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO items 4,10,13,14,29,31 (Set awhelp).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Verbose non-TTY --help epilog + arg-hungry-verb examples; top parser has no epilog today (verified); text-only; no findings.

## Goal

Make `aw --help` genuinely useful to a non-TTY coding agent by adding a top-level epilog that explains
when and why to use `aw` and shows common worked examples, and make the arg-hungry verbs (`ipd`, `show`,
`storage`) show a usage-plus-examples block on `--help` (and on a missing required argument) instead of a
bare argparse error. Text/help-only: the verbs behave exactly as before; only the help and error MESSAGES
change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Edit ONLY `agent_workflows/cli.py` and add ONLY `tests/test_help_verbose.py`. Make the
top-level and subparser changes at the exact anchors below. When you add an `epilog=`, you MUST also pass
`formatter_class=argparse.RawDescriptionHelpFormatter` (or keep the existing `_AlphaHelpFormatter` and
subclass it to inherit RawDescription behavior) so argparse does NOT re-wrap the multi-line epilog and
mangle the examples - the top-level parser currently uses `_AlphaHelpFormatter` (cli.py:382), so create a
`_AlphaRawHelpFormatter(_AlphaHelpFormatter, argparse.RawDescriptionHelpFormatter)` and use it for any
parser that gets a multi-line epilog, to keep BOTH the alphabetical subcommand listing AND the verbatim
epilog. Do NOT change any `add_argument` `required`/`nargs` setting; a missing required arg must still
exit nonzero - only its printed message improves.

### Task group 1: verbose top-level epilog for agents

- [ ] E-01 In `agent_workflows/cli.py`, add an `epilog=` to the top-level parser (cli.py:378-383) containing a "When and why to use aw" block plus common worked examples, and switch that parser's `formatter_class` to a raw-preserving alphabetical formatter so the epilog renders verbatim. Add the formatter class near `_AlphaHelpFormatter` (cli.py:347):
  ```python
  class _AlphaRawHelpFormatter(_AlphaHelpFormatter, argparse.RawDescriptionHelpFormatter):
      """Alphabetical subcommand listing (from _AlphaHelpFormatter) PLUS a verbatim, un-rewrapped
      description/epilog (from RawDescriptionHelpFormatter), so a multi-line agent-oriented epilog
      keeps its formatting."""
  ```
  Then set the top-level parser to `formatter_class=_AlphaRawHelpFormatter` and add:
  ```python
      epilog=(
          "WHEN AND WHY TO USE aw:\n"
          "  aw is the entry point to this repo's agent-workflows toolkit. Prefer it over doing the\n"
          "  work by hand for anything that touches .aw/ records: authoring/linting plans (IPDs),\n"
          "  managing specs and backlog, checking naming/leak conformity, and seeing what needs\n"
          "  attention. It is deterministic, machine-friendly (most read verbs take --json or\n"
          "  --agent), and safe (it never pushes). A coding agent with no TTY should start here.\n"
          "\n"
          "COMMON EXAMPLES:\n"
          "  aw attention --format json      # what needs attention across the repo (machine-readable)\n"
          "  aw ipd lint --phase author FILE # structurally lint a plan before proposing it\n"
          "  aw ipd scaffold --kind child --title T --set S --order N --author A  # new plan skeleton\n"
          "  aw specs check                  # validate every spec against the contract\n"
          "  aw backlog check --agent        # validate the backlog tree, tab-separated drift output\n"
          "  aw sanitize --agent             # scan for leaked local/identifying info\n"
          "\n"
          "EXIT CODES (read/check verbs): 0 = clean, 1 = findings, 2 = could-not-run.\n"
      ),
  ```
  - Depends on: none
  - Expected outcome: `aw --help` prints the "WHEN AND WHY TO USE aw" block and the COMMON EXAMPLES block verbatim (line breaks preserved), while the subcommand list stays alphabetical.
  - Execution state: pending

### Task group 2: usage-plus-examples for arg-hungry verbs

- [ ] E-02 In `agent_workflows/cli.py`, for the arg-hungry verbs `ipd`, `show`, and `storage`, make a missing required argument (or `--help`) surface a usage-plus-examples block rather than a bare argparse error. Do this WITHOUT changing parsing semantics: add an `epilog=` (using `_AlphaRawHelpFormatter` from E-01) to each of those subparsers with 2-3 concrete examples, AND improve the missing-arg experience by giving the subparser a friendly error - either (a) set the subparser's `formatter_class` and a fuller `description`/`epilog` so `--help` shows the examples, and additionally (b) where the verb requires a positional (e.g. `show` requires an action id, `ipd`/`storage` require a subcommand), detect the missing value at dispatch and print the subparser's help (via `parser.print_help()`/the captured subparser) before returning a nonzero exit, instead of letting argparse emit only the bare `error: the following arguments are required` line. Example epilog text for `show`:
  ```python
          epilog=(
              "EXAMPLES:\n"
              "  aw show ACTION_ID            # print one action's full state\n"
              "  aw show ACTION_ID@2          # a specific generation of that action\n"
          ),
  ```
  For `ipd` and `storage`, list their subcommands with a one-line example each (e.g. `aw ipd lint --phase author FILE`, `aw storage status --json`). Keep the change text-only: a genuinely missing arg still exits nonzero; only the message becomes a helpful usage+examples block.
  - Depends on: E-01
  - Expected outcome: `aw ipd --help`, `aw show --help`, and `aw storage --help` each show an EXAMPLES block; invoking one of these verbs with a missing required argument prints a usage-plus-examples block (not just the bare `error: the following arguments are required` line) and exits nonzero.
  - Execution state: pending

### Task group 3: test the verbose help

- [ ] E-03 Add `tests/test_help_verbose.py` that: (a) builds the parser via `agent_workflows.cli._build_parser()` and captures `aw --help` output (e.g. `parser.format_help()`), asserting it contains "WHEN AND WHY TO USE aw" and at least two of the COMMON EXAMPLES lines (e.g. "aw attention --format json" and "aw ipd scaffold"); (b) captures the `ipd`, `show`, and `storage` subparsers' help and asserts each contains an "EXAMPLES:" block with a concrete `aw ...` example; (c) invokes the CLI for one arg-hungry verb with a missing required arg (capturing stdout/stderr and the exit code) and asserts the output contains the EXAMPLES block AND the exit code is nonzero (behavior unchanged, message improved). Run the full serial suite and paste the tail.
  - Depends on: E-01,E-02
  - Expected outcome: `tests/test_help_verbose.py` passes; `aw --help` and the arg-hungry verbs' `--help` show the when/why and examples blocks; a missing-arg invocation shows examples and still exits nonzero; the full serial suite is green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The top-level parser (cli.py:378-383) sets `description=` but no `epilog=`, and uses `formatter_class=_AlphaHelpFormatter` (cli.py:382), which sorts the subcommand listing alphabetically (cli.py:347-366) but does NOT preserve multi-line text - a raw-preserving mixin is needed for a verbatim epilog.
- `argparse.RawDescriptionHelpFormatter` preserves description/epilog line breaks; combining it with `_AlphaHelpFormatter` via multiple inheritance keeps both the sorted listing and the verbatim epilog.
- `show` requires an action id positional; `ipd` and `storage` are noun parsers whose subcommands are required to do anything - a bare `aw ipd` / `aw storage` / `aw show` with nothing else is the arg-hungry failure case an agent hits.
- Verb dispatch is downstream of `_build_parser()`; the missing-arg friendly-message work is a help/error-text change and MUST NOT alter `required`/`nargs` (a genuinely missing arg still exits nonzero).
- `_apply_descriptions` (cli.py:326-344) sets each subparser's `.description` from `_DESCRIPTIONS`; an `epilog=` is orthogonal (argparse renders description then arguments then epilog), so adding an epilog does not conflict with the Order-01 description edits.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | The top-level parser has no epilog and a terse one-line description. | `aw --help` gives an agent no "when/why" guidance or examples; E-01 adds an epilog. |
| F2 | `_AlphaHelpFormatter` re-wraps text; a multi-line epilog would be mangled. | E-01 introduces `_AlphaRawHelpFormatter` (alpha listing + raw epilog). |
| F3 | Missing required args on `ipd`/`show`/`storage` produce a bare argparse error with no example. | E-02 adds EXAMPLES epilogs and a friendly missing-arg path (message-only; exit code unchanged). |
| F4 | Epilog is orthogonal to `_DESCRIPTIONS`. | No conflict with awhelp Order 01; the two Orders are independent text edits. |

## Proposed changes (ordered, validatable)

1. Add `_AlphaRawHelpFormatter` and a top-level epilog with a when/why block + common examples (E-01).
2. Add EXAMPLES epilogs to `ipd`/`show`/`storage` and a friendly missing-arg message (E-02).
3. Add `tests/test_help_verbose.py` asserting the blocks appear and missing-arg still exits nonzero; run the suite (E-03).

## Deferred / out of scope (with reason)

- Rewriting the per-verb `_DESCRIPTIONS` jargon: awhelp Order 01.
- `--json` on read verbs and documented exit codes in each verb's help: awhelp Order 03 (E-01's epilog mentions the 0/1/2 convention at the top level, but per-verb documentation is Order 03).
- Any change to argument parsing (`required`/`nargs`) or dispatch: out of scope; only messages change.
- Epilogs/examples for the NEW cross-cutting verbs: Set awcmdsurf owns those verbs.

## Scope check

- Over-scope: none - only the top-level parser, three subparsers, a formatter class, and one new test file.
- Under-scope: none - the non-TTY agent guidance (when/why + examples) and arg-hungry-verb examples for items 4, 10, 13, 14, 29, 31 are covered with a test.

## Required tests / validation

`tests/test_help_verbose.py` (E-03): top-level when/why + examples present, arg-hungry verbs show EXAMPLES, a missing-arg invocation shows examples and exits nonzero; plus the full serial suite. Each V pins one E.

## Spec / documentation sync

Implements spec 20260818-1525-01 goal G6 (agent-usable help) for the existing top-level surface. No AGENTS.md change. No spec status transition (the Set orchestrator advances the spec).

## Open questions

### OQ-01: friendly missing-arg via dispatch-time print_help or via a custom argparse error?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: use a dispatch-time `print_help()` on the relevant subparser before returning a nonzero exit for the missing-positional case (deterministic, keeps argparse's `required`/`nargs` untouched, and reuses the epilog we already added). Subclassing `argparse.ArgumentParser` to override `error()` is more invasive and risks changing behavior for every parser; the targeted dispatch-time path is smaller and safer. Resolved per E-02.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw --help` output showing the verbatim "WHEN AND WHY TO USE aw" block and the COMMON EXAMPLES block (line breaks preserved), with the subcommand list still alphabetical.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw ipd --help`, `aw show --help`, and `aw storage --help` each showing an EXAMPLES block, plus one arg-hungry verb invoked with a missing required argument showing the usage-plus-examples block and its nonzero exit code.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `tests/test_help_verbose.py` passing and the full serial suite tail (no regressions).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` plus an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification and path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the two touched
paths (`agent_workflows/cli.py` and `tests/test_help_verbose.py`) path-scoped (never `git add -A`), and
never pushes. Transition to executed only after `aw ipd lint --phase pre-transition` conforms and every V
is `pass`. Second Order of Set awhelp; independent of Orders 01/03 (all three are text-only). On Set
completion the orchestrator advances spec 20260818-1525-01 accordingly.
