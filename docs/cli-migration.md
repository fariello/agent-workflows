# CLI output migration guide (2.0.0 machine output)

> [!NOTE]
> **POLICY RETRACTED (2026-09-10)**: The automatic non-TTY switch to JSONL announced for
> 2.0.0 was retracted by maintainer ruling (ttyflags `yaxr4i` OQ-01). Piped output stays human
> text. Explicit flags (`--agent` for `aw.agent/v1` JSONL, `--json` for full structured JSON)
> are the only way to obtain machine output. See section 9 of the
> [CLI Output Mode Contract](cli-output-contract.md).

## Read this if you scrape `aw` output in a script

The 2.0.0 release introduces the canonical `aw.agent/v1` machine format. An earlier proposal for
an automatic non-TTY hard cutover to JSONL was RETRACTED (maintainer ruling, 2026-09-10): piped
output remains human text. If any script, CI step, or agent parses `aw` output, update it to pass
`--agent` explicitly instead of scraping text. This guide explains how to migrate scrapers to
`--agent`.

The full normative rules live in the [CLI Output Mode Contract](cli-output-contract.md); the
day-to-day references are the [Human TTY guide](cli-human-guide.md) and the
[Agent protocol reference](cli-agent-protocol.md).

## The break, stated loudly

Before 2.0.0, piping `aw` produced human-oriented plain text (and a few commands produced ad
hoc TSV). The earlier proposal for an automatic non-TTY switch was retracted; piped output
remains human text. Passing `--agent` selects the canonical machine format.

Under `--agent`, legacy byte forms are replaced by `aw.agent/v1` JSONL:

- Specifically, these three legacy byte forms are GONE and are now `aw.agent/v1`:
  1. Piped `aw status` JSON. The old shape is replaced by the `aw.agent/v1` result record.
  2. The `render_agent_drift` TSV lines (`location<TAB>rule<TAB>detail`) that check and doctor
     style commands used to print. They are now `aw.agent/v1` `diagnostics` inside a record.
  3. The `aw find` and `aw search` path lines (bare `path` or `path:line` text). They are now
     `aw.agent/v1` `item` records followed by a `summary` record.
If you depended on text scraping, you should migrate to `--agent`. There is no flag that
restores legacy shapes under `--agent`.

## Why a hard cutover: RETRACTED

> Historical rationale (retracted):
> "`agent-workflows` is pre-wide-adoption, and the maintainer chose one clean machine convention
> over carrying legacy wire forms forever (recorded in the awcliux program open question OQ-01 and
> consistent with the command-surface spec `20260818-1525-01`). One format, validated by a schema,
> is cheaper to consume and impossible to silently diverge from."

This policy was retracted on 2026-09-10 (maintainer ruling, ttyflags `yaxr4i` OQ-01) because the
automatic switch never shipped, existing scripts relied on human text in pipes, and switching would
break them with no gain; see [CLI Output Mode Contract](cli-output-contract.md) section 9.

## Migration recipes

### 1. "I just want the human text back"

Nothing to do. Interactive terminals and pipes both default to human-readable text. The proposed
automatic non-TTY switch was retracted (maintainer ruling, 2026-09-10).

### 2. "My script parsed piped text"

Piped stdout is still human text, but human text is not a stable programmatic contract. Switch to
the machine format explicitly and parse JSON:

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

There is no in-CLI rollback to legacy byte formats under `--agent`. Your options are:

- Update the consumer to parse `aw.agent/v1` (recommended, permanent).
- Pin to a pre-2.0.0 release of `agent-workflows` until you can update the consumer. Note that
  pre-2.0.0 predates the `.aw/` layout migration, so this is a stopgap, not a destination.

## Compatibility schedule

| Milestone | State |
| --- | --- |
| Before 2.0.0 | Piped output was human text and ad hoc TSV. |
| 2.0.0 (this release) | Automatic non-TTY switch RETRACTED 2026-09-10. Piped output remains human text. `--agent` and `--json` select machine output. |
| `aw.agent/v1` lifetime | Additive, optional fields only. Existing field names and meanings are stable. |
| A future `aw.agent/v2` | Reserved for any breaking record-shape change. It would ship with its own migration notes. Pin your parser to the `schema` string and tolerate unknown fields so an additive change never breaks you. |

## Verifying your migration

- Confirm the exit codes your script branches on still mean the same thing: `0` clean, `1`
  findings, `2` cannot run. That classification did not change.
- Confirm you read from stdout for results and ignore stderr (progress and cannot-start
  diagnostics live on stderr).
- Confirm you tolerate unknown JSON fields so future additive changes do not break you.
