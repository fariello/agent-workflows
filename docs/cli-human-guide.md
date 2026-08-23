# Human TTY guide: reading `aw` output at the terminal

This is the operator-facing guide to what `aw` prints when you run it interactively in a
terminal. For the machine-facing wire format that agents parse, see the
[Agent protocol reference](cli-agent-protocol.md). For the full normative rules that both
audiences share, see the [CLI Output Mode Contract](cli-output-contract.md).

## The one rule that surprises people first

`aw` decides its output audience from whether stdout is a terminal, not from a flag:

- stdout is a terminal (you are looking at it): you get the HUMAN view (styled, scannable).
- stdout is a pipe or a file (redirected, captured, or run by an agent): you get the AGENT
  view (`aw.agent/v1` JSONL, one compact JSON record per line).

So `aw status` at your prompt looks different from `aw status | cat`. That is intentional and
it is a HARD CUTOVER as of the 2.0.0 release: piped output is now machine JSONL, not the old
plain text. See the [migration guide](cli-migration.md) if you have scripts that scrape the
old text.

You can always override the automatic choice:

- `aw status --agent` forces the machine JSONL view even at a terminal.
- `aw status --json` forces pretty-printed structured JSON.
- `aw status --no-color` keeps the human view but disables ANSI color (also honored via the
  `NO_COLOR` environment variable).
- `FORCE_COLOR=1` keeps color even when piped.

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
- Only the sixteen named colors and the terminal default background are used; there is no
  assumed background, no truecolor, and no blink.
- Unicode glyphs (check mark, cross, arrow) degrade to ASCII (`OK`, `FAIL`, `->`) when the
  terminal cannot render them, or when you set `AW_ASCII_ONLY=1` or `FORCE_ASCII=1`, or when
  `TERM=dumb`.

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

## Streams

- stdout carries the final result only (the human view, or the machine records).
- stderr carries progress lines, transient status, and cannot-start diagnostics. It is safe to
  discard stderr when you only want the result.
- Broken pipes (for example `aw doctor | head`) terminate cleanly with no Python traceback.

## Quick reference

| You want | Run |
| --- | --- |
| The styled interactive view | `aw status` (at a terminal) |
| Machine JSONL, even at a terminal | `aw status --agent` |
| Pretty structured JSON | `aw status --json` |
| Human view without color | `aw status --no-color` |
| A repository health sweep | `aw doctor` |
| The cross-tree attention board | `aw attention` |
| Only the fields you care about (agent) | `aw find plans --agent --fields findings` |
| Bounded output with a continuation hint | `aw find plans --agent --limit 20` |
