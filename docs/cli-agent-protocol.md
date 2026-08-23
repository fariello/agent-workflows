# Agent protocol reference: parsing `aw.agent/v1`

This is the reference for programs and agents that consume `aw` output as data. It summarizes
the wire format and links to the full normative rules in the
[CLI Output Mode Contract](cli-output-contract.md). For the interactive terminal view, see the
[Human TTY guide](cli-human-guide.md).

## When you get machine output

`aw` emits the machine format whenever stdout is not a terminal (piped, redirected, or driven
by an agent), and whenever you pass `--agent` explicitly. This is a HARD CUTOVER as of the
2.0.0 release: there is no compatibility window and no legacy plain-text or TSV form on the
migrated commands. If you previously scraped text, read the [migration guide](cli-migration.md).

- `--agent`: compact `aw.agent/v1` JSONL (one record per line). This is the default when piped.
- `--json`: pretty-printed full `CommandResult` JSON (a debugging view, more verbose).
- `--agent` and `--json` (or `--format`) together is a usage error and exits `2`.

## The record envelope

Every `aw.agent/v1` record is a single line of compact JSON. The mandatory envelope fields:

| Field | Meaning |
| --- | --- |
| `schema` | Always `aw.agent/v1`. Check this before trusting the record. |
| `kind` | One of `result`, `summary`, `item`, `error`. |
| `cmd` | The command that produced the record. |
| `exit` | The process exit classification: `0`, `1`, or `2`. |
| `outcome` | The semantic outcome word (see below). |
| `verified` | Boolean: was the claim actually verified? |
| `complete` | Boolean: was the work complete (not truncated or partial)? |

A single-shot command emits one `result` (or `error`) record. A stream emits zero or more
`item` records followed by exactly one `summary` record.

## Outcomes and exit codes

The outcome vocabulary is a closed set. The positive outcomes (`clean`, `ok`, `conforms`) may
NEVER appear with `verified: false` or with an incomplete non-preview state; the schema
validator rejects such greenwashing. Exit code parity is enforced:

- `exit: 0` pairs with a positive or neutral outcome (`clean`, `ok`, `conforms`, `preview`,
  `stale`, `skipped`).
- `exit: 1` pairs with `findings` or `fail`.
- `exit: 2` pairs with `error` or `cannot-run` (and the record `kind` is `error`).

Parse the terminal record's `exit` and compare it to the process return code; they must agree.

## Stream truncation is honest

When a stream is bounded (for example with `--limit`), the terminating `summary` record retains
the full accounting so you never silently lose data:

- `total`: how many items existed.
- `emitted`: how many were printed.
- `omitted`: how many were withheld (`emitted + omitted == total`).
- `complete`: `false` when anything was omitted.
- `next`: a ready-to-run command that would fetch the rest.

## Token control

The machine format is compact by default (short identifiers, counts instead of long lists).
Two escape hatches tune the token cost:

- `--fields <a,b,c>`: project each record down to the requested fields. The mandatory envelope
  (`schema`, `kind`, `cmd`, `exit`, `outcome`, `verified`, `complete`) is always retained.
- `--verbose`: include full nested diagnostics, change details, and evidence dictionaries.

## Example records

Clean result (`exit: 0`):

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"status","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"next":null}
```

Domain findings (`exit: 1`):

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":2,"diagnostics":[{"location":"a.md","rule":"check.name-nonconformant"}],"next":"aw group plans x --set y"}
```

Truncated stream summary:

```json
{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":10,"emitted":3,"omitted":7,"complete":false,"next":"aw find plans --agent --limit 10"}
```

Cannot-run error (`exit: 2`):

```json
{"schema":"aw.agent/v1","kind":"error","cmd":"project","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"next":"aw project status"}
```

## Recommended consumption pattern

1. Read stdout line by line; parse each line as JSON.
2. Confirm `schema == "aw.agent/v1"`.
3. Route on `kind`. Accumulate `item` records until the `summary`.
4. Trust the terminal record's `outcome`, `exit`, `verified`, and `complete` for the verdict.
5. Never treat `exit: 1` as a crash; it means real findings.
6. If `complete` is `false`, follow `next` to fetch the remainder.

## Stability

Additive, optional fields within `aw.agent/v1` are backward compatible. Any breaking change to
record shape or field meaning bumps the version to `aw.agent/v2`. Pin your parser to the
`schema` string and tolerate unknown fields.
