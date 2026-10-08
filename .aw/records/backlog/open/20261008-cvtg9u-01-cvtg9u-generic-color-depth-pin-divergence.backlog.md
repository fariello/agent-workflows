- Id: cvtg9u
- Status: open
- Set: cvtg9u
- Priority: medium
- Work-Kind: followup
- Summary: Generic color axis ignores color_depth pin at pin none

## Workflow history
- 2026-10-08 created (aw backlog): Generic color axis ignores color_depth pin at pin none

## Context and Measured Evidence

Measured in plan `y2ge26` (backlog `o53joz`, finding F-08):
The `color_depth` config pin is documented in `config.CONFIG_SCHEMA` as:
"Pin the terminal color depth (256, 16, or none) instead of detecting it."

However, at pin `none` on a capable TTY, the generic color axis ignores the depth pin entirely:
- `Term.status_256("up to date")` returns `'\x1b[1;38;5;46mup to date\x1b[0m'`
- `Term.path("a/b")` returns `'\x1b[38;5;33ma/b\x1b[0m'`
- `Term.colorize("x", "bold")` returns `'\x1b[1mx\x1b[0m'`

Across real CLI commands driven with `--color` at pin `none`:
- `aw index plans` prints `'\x1b[1;38;5;46mup to date\x1b[0m   \x1b[38;5;33m.aw/records/plans/\x1b[0m...'`
- `aw check`, `aw doctor`, `aw ipd lint`, `aw ipd board`, `aw backlog check`, `aw specs check`, `aw attention` all emit 256-color escapes at pin `none`.

## Open Scope Conflict

Two repository sources conflict on whether this is within the ladder's scope:
1. Spec `uonrjg` Section 3 lists "generic command outcome icons that are not lifecycle states" as an explicit NON-GOAL. Under this reading, the ladder governs only lifecycle states.
2. DECISIONS D42 states the ladder as a general accessibility obligation ("honor `NO_COLOR`/`FORCE_COLOR`/`TERM`/`isatty()` and degrade through 256/16/none") without restricting it to lifecycle styling, and `config.CONFIG_SCHEMA`'s user-facing description makes no lifecycle-only qualification.

Resolving this conflict requires a maintainer decision, as fixing it would change user-visible styling across all non-lifecycle surfaces in the package.

## Provisional Classification

Per PR-004 and plan `y2ge26`, `- Work-Kind: followup` is PROVISIONAL pending the maintainer's ruling on this scope question.
Filing as `followup` avoids prematurely attaching a release gate to an unresolved scope decision.
If the maintainer rules that `color_depth` was intended to govern the generic axis, this item is to be reclassified as `bug` with `- Blocks-Release: next` via `aw backlog set`.

## Provenance
- From-Plan: y2ge26
- Related-Set: o53joz
