# CLI output migration guide (2.0.0 hard cutover)

## Read this if you scrape `aw` output in a script

The 2.0.0 release changes what `aw` writes to a pipe. This is a HARD CUTOVER with NO
compatibility window. If any script, CI step, or agent parses `aw` output as text, it may break
until you update it. This guide names every byte-level break and gives you the recipe to fix it.

The full normative rules live in the [CLI Output Mode Contract](cli-output-contract.md); the
day-to-day references are the [Human TTY guide](cli-human-guide.md) and the
[Agent protocol reference](cli-agent-protocol.md).

## The break, stated loudly

Before 2.0.0, piping `aw` produced human-oriented plain text (and a few commands produced ad
hoc TSV). As of 2.0.0:

- When stdout is not a terminal (piped, redirected, captured, or agent-driven), `aw` emits
  `aw.agent/v1` JSONL, not plain text. This is automatic and immediate.
- Specifically, these three legacy byte forms are GONE and are now `aw.agent/v1`:
  1. Piped `aw status` JSON. The old shape is replaced by the `aw.agent/v1` result record.
  2. The `render_agent_drift` TSV lines (`location<TAB>rule<TAB>detail`) that check and doctor
     style commands used to print. They are now `aw.agent/v1` `diagnostics` inside a record.
  3. The `aw find` and `aw search` path lines (bare `path` or `path:line` text). They are now
     `aw.agent/v1` `item` records followed by a `summary` record.

If you depended on any of those three text shapes, you MUST migrate. There is no flag that
brings the old bytes back.

## Why a hard cutover

`agent-workflows` is pre-wide-adoption, and the maintainer chose one clean machine convention
over carrying legacy wire forms forever (recorded in the awcliux program open question OQ-01 and
consistent with the command-surface spec `20260818-1525-01`). One format, validated by a schema,
is cheaper to consume and impossible to silently diverge from.

## Migration recipes

### 1. "I just want the human text back at my terminal"

Nothing to do. At an interactive terminal you still get the human view. The cutover only affects
non-terminal stdout.

### 2. "My script parsed piped text"

Switch to the machine format explicitly and parse JSON:

```bash
# Before (fragile text scraping):
#   aw status | grep -i current

# After (robust, schema-tagged):
aw status --agent
```

Read stdout line by line, parse each line as JSON, confirm `schema` is `aw.agent/v1`, and read
the fields you need. See the [Agent protocol reference](cli-agent-protocol.md) for the envelope.

### 3. "My script read the TSV drift lines from check or doctor"

The findings are now structured. Parse the `diagnostics` array of the terminal record:

```bash
aw check plans --agent
# each line is a JSON record; the result record carries:
#   "diagnostics":[{"location":"a.md","rule":"check.name-nonconformant"}, ...]
```

Map the old three TSV columns like this: the old `location` and `rule` columns are the
`location` and `rule` keys; the old free-text `detail` column is available under `--verbose`
(compact records omit it to save tokens).

### 4. "My script read find or search path lines"

Consume the `item` records and stop at the `summary`:

```bash
aw find plans --agent
# item records:   {"schema":"aw.agent/v1","kind":"item","cmd":"find", ...}
# then a summary: {"schema":"aw.agent/v1","kind":"summary","cmd":"find","total":N, ...}
```

If you bounded output, the `summary` tells you `total`, `emitted`, `omitted`, `complete`, and a
`next` command to fetch the rest.

### 5. "I actually want pretty JSON for debugging"

Use `--json` for the full, pretty-printed structure (more verbose than `--agent`).

## Rollback

There is no in-CLI rollback to the old bytes; that is what "hard cutover" means. Your options
are:

- Update the consumer to parse `aw.agent/v1` (recommended, permanent).
- Pin to a pre-2.0.0 release of `agent-workflows` until you can update the consumer. Note that
  pre-2.0.0 predates the `.aw/` layout migration, so this is a stopgap, not a destination.

## Compatibility schedule

| Milestone | State |
| --- | --- |
| Before 2.0.0 | Piped output was human text and ad hoc TSV. |
| 2.0.0 (this release) | Hard cutover. Non-terminal stdout is `aw.agent/v1` JSONL. No legacy text or TSV on migrated commands. `--agent` and `--json` are the explicit overrides. |
| `aw.agent/v1` lifetime | Additive, optional fields only. Existing field names and meanings are stable. |
| A future `aw.agent/v2` | Reserved for any breaking record-shape change. It would ship with its own migration notes. Pin your parser to the `schema` string and tolerate unknown fields so an additive change never breaks you. |

## Verifying your migration

- Confirm the exit codes your script branches on still mean the same thing: `0` clean, `1`
  findings, `2` cannot run. That classification did not change.
- Confirm you read from stdout for results and ignore stderr (progress and cannot-start
  diagnostics live on stderr).
- Confirm you tolerate unknown JSON fields so future additive changes do not break you.
