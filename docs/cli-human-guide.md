# Human TTY guide: reading `aw` output at the terminal

This is the operator-facing guide to what `aw` prints when you run it interactively in a
terminal. For the machine-facing wire format that agents parse, see the
[Agent protocol reference](cli-agent-protocol.md). For the full normative rules that both
audiences share, see the [CLI Output Mode Contract](cli-output-contract.md).

## Output mode and audience

By default, `aw` emits human-readable text whether stdout is a terminal, a pipe, or a file.
The earlier proposal for an automatic non-TTY hard cutover to machine JSONL was RETRACTED
(maintainer ruling, 2026-09-10): piped output remains human text, and `--agent` is the explicit
way to select machine JSONL. Non-TTY stdout affects color only.

You can select the format and styling with flags:

- `aw <command>` (default): human-readable output (ANSI-colored on a TTY, uncolored when piped).
- `aw <command> --agent`: machine-readable `aw.agent/v1` JSONL (one compact JSON record per line).
- `aw <command> --json`: pretty-printed structured JSON.
- `aw <command> --no-color`: human view without ANSI color (also honored via the `NO_COLOR`
  environment variable).
- `FORCE_COLOR=1`: preserves ANSI color even when piped.

## Anatomy of a human render

A typical human result is laid out top to bottom as fixed-width, scannable sections:

```text
AW check  plans
X FINDINGS  2 findings across 41 checked

Findings:
  Issue: Filename does not match artifact naming grammar
  - a.md [ERROR]
    Fix: run 'aw rename <type>' or rename to match the naming grammar.

Evidence
  checked: 41

Next  aw group plans x --set y (regroup)
Agent output: --agent (automatic when piped)
```

1. Title banner: `AW <command>  <target>` and, for timed operations, an elapsed time on the
   right.
2. Outcome banner: a glyph plus an uppercase STATUS word plus a one-line summary. The word is
   always present so meaning survives monochrome terminals and screen readers; color is only a
   redundant cue.
3. Findings: grouped by issue, each with a bracketed severity label (`[ERROR]`, `[WARN ]`,
   `[INFO ]`) and, where known, a concrete `Fix:` line.
4. Changes: for mutations, a preview of what would change (or did change).
5. Evidence: the receipts that back the outcome (what was checked, counts, verification state).
6. Next: the single most useful follow-up command.
7. A one-line hint that machine output is available with `--agent`.

## Color and accessibility

Color and glyphs are never the sole carrier of meaning:

- Every status prints a WORD (OK, FINDINGS, FAIL, WARN, PREVIEW, ...), so a monochrome or
  redirected view is complete on its own.
- Terminal styling uses an xterm-256 color palette on capable terminals, degrading through 16-color
  ANSI and then no-color monochrome. Users can pin their preferred color depth, and `NO_COLOR`
  outranks the depth pin.
- Unicode glyphs (check mark, cross, arrow) degrade to ASCII (`OK`, `FAIL`, `->`) when the
  terminal cannot render them, or when you set `AW_ASCII_ONLY=1` or `FORCE_ASCII=1`, or when
  `TERM=dumb`.
- Run `aw --help` to see the canonical lifecycle legend, which details every lifecycle stage, its
  Unicode glyph, and its ASCII fallback.

Environment precedence for color: `NO_COLOR` disables color and is only overridden by
`FORCE_COLOR`; otherwise color is on only for a real terminal with a capable `TERM`.

## Exit codes you can rely on

Every `aw` command uses the same three-way exit classification:

- `0`: clean. The command ran and found nothing wrong (or completed a preview).
- `1`: findings or domain failure. The command ran fine but found real issues (for example
  `aw check` or `aw doctor` found nonconformant records).
- `2`: cannot run. A usage error, a missing argument, conflicting flags, or an unmet
  precondition. Nothing meaningful was produced.

A common pitfall: `aw check` finding problems returns `1`, which is not a crash. Reserve `2`
in your own scripts for "the command could not run at all".

## Empty states and progress cues

- **Empty results**: When a search or list command matches zero items, it never fails silently or prints blank lines.
  It renders `OK CLEAN` / `✓ CLEAN`, echoes your active filters/selectors, and gives a `Next` follow-up command
  to broaden your search (e.g. `aw find`).
- **Progress step-cues**: Synchronous commands emit transient progress indicators (`[INFO ] ...ing...`) strictly to
  `stderr`. No spinners or async terminal animation machinery is used.
- For normative specifications, see the [CLI Output Mode Contract](cli-output-contract.md#11-empty-loading-and-error-state-ux-convention).

## Streams

- stdout carries the final result only (the human view, or the machine records).
- stderr carries progress lines, transient status, and cannot-start diagnostics. It is safe to
  discard stderr when you only want the result.
- Broken pipes (for example `aw doctor | head`) terminate cleanly with no Python traceback.

## Quick reference

| You want | Run |
| --- | --- |
| The styled interactive view | `aw status` (at a terminal) |
| The canonical lifecycle legend | `aw --help` |
| Machine JSONL, even at a terminal | `aw status --agent` |
| Pretty structured JSON | `aw status --json` |
| Human view without color | `aw status --no-color` |
| A repository health sweep | `aw doctor` |
| The cross-tree board of what to work on | `aw next` (aliases `aw attention`, `aw att`, `aw todo`) |
| That board ordered by dependency, prerequisites first | `aw next -o depth` |
| Only the fields you care about (agent) | `aw find plans --agent --fields findings` |
| Bounded output with a continuation hint | `aw find plans --agent --limit 20` |
| Launch an IPD with a saved model alias | `aw run as gem <selector>` |

## Naming a model once instead of on every run

If you keep retyping `--model <provider/model> --variant high`, save it as a named RUNNER
PROFILE and run `aw run as gem <selector>` instead. Profiles are user-local, never created or
made default for you, and `aw setup` offers to set one up with a question that defaults to No.

[Runner profiles](runner-profiles.md) is the complete reference: every command form, the exact
per-field override precedence, storage and privacy, and what happens on a bad or missing
profile.
