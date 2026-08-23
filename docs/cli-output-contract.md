# Normative CLI Output Mode Contract and Token-Efficient Agent Protocol

awcliux Order 01 (`hd3kln`) E-03 / V-03, Order 03 (`8su0r3`) E-01 / E-02 / E-03.

This document defines the normative contract governing audience selection, output modes,
stream conventions, exit code semantics, the `aw.agent/v1` machine protocol, evidence receipts,
anti-greenwashing outcome invariants, token-control budgets, and reconciliation with legacy
formats across the `agent-workflows` (`aw`) CLI surface.

---

## 1. Audience Modes and Precedence

Every invocation of an `aw` command resolves its output destination and formatting through a
single deterministic precedence rule:

```text
explicit (--json / --format <fmt>)  >  --agent  >  non-TTY stdout (pipe/redirect) => agent  >  TTY stdout => human
```

1. **Explicit format flags** (`--json`, `--format json`, `--format <fmt>`):
   Selects the specified explicit serialization mode (`OutputMode.JSON`). Overrides TTY
   detection and `--agent`. Color is disabled (`color=False`).
2. **Agent flag or non-TTY stdout**:
   If `--agent` is passed or `stdout.isatty()` is False (e.g. piped to another command, subshell,
   or redirected to a file), `OutputMode.AGENT` is selected. Output is emitted as compact,
   ANSI-free `aw.agent/v1` JSONL records. Color is disabled (`color=False`).
   *Note*: `stdin.isatty()` controls interactive prompting (such as confirmation dialogs or wizards),
   NOT the output audience or mode.
3. **Interactive Human TTY**:
   When stdout is a TTY and no agent/explicit format flags are given, `OutputMode.HUMAN` is selected.
4. **Color and Styling Flags**:
   `--no-color`, `NO_COLOR`, and `FORCE_COLOR` control ANSI styling within human mode only. They
   never alter the audience mode itself (i.e. `--no-color` on a TTY emits monochrome human text,
   never machine JSONL).

---

## 2. Standard Result Types and Renderer Boundary

Command logic and presentation are strictly decoupled. Domain handlers compute a single typed
`CommandResult` containing standard stdlib outcome facts:

- `CommandResult`: `command`, `status` (`clean`, `findings`, `fail`, `preview`, `stale`, `error`, `skipped`, `partial`, `unverified`),
  `exit_code` (`0`, `1`, `2`), `summary`, `diagnostics`, `changes`, `evidence`, `next_actions`, `target`, `applied`, `data`.
- `Diagnostic`: `location`, `rule`, `detail`, `severity` (`error`, `warning`, `info`), `fix`.
- `Change`: `path`, `kind` (`modify`, `create`, `delete`, `rename`), `detail`, `applied`.
- `Evidence`: `key`, `value`, `status` (`verified`, `unverified`, `pass`, `fail`, `clean`), `detail`.
- `NextAction`: `command`, `description`.

Renderers (`HumanRenderer`, `AgentRenderer`, `JsonRenderer`) consume the same `CommandResult`.
Both renderers expose identical facts (counts, paths, evidence, exit code) with zero domain drift.

---

## 3. Exit Code Semantics

The CLI enforces a uniform three-state exit classification across all verbs:

- `0` (**Clean / Success**): Command completed cleanly with no negative domain findings or violations.
- `1` (**Domain Findings / Negative Result**): Command completed execution, but detected actionable
  findings, policy violations, contract drift, uncommitted conflicts, or failed assertions.
- `2` (**Usage Error / Cannot-Run / Fatal**): Invalid arguments, conflicting flags, missing required
  environment dependencies, or fatal execution errors preventing domain inspection.

---

## 4. The `aw.agent/v1` JSONL Protocol and Closed Record Kinds

All agent output conforms to the `aw.agent/v1` newline-terminated JSONL protocol.
Every record belongs to a closed set of record kinds:

### Record Kinds

1. `result`: Bounded single command execution record.
2. `summary`: Summary record terminating a stream of items under pagination or token limits.
3. `item`: An individual item in a multi-item stream sequence.
4. `error`: A fatal or cannot-run execution diagnostic (exit code 2).

### Protocol Invariants and Anti-Greenwashing Rules

Agents (GPT, Gemini, Opus, GLM, etc.) and CI runners must **consume structured records and never infer completion from prose**.

- **Anti-Greenwashing Invariant**: A record MUST NEVER report a positive outcome (`clean`, `ok`, `conforms`) for work that was `skipped`, `partial`, `unverified`, or `cannot-run`.
- **Completeness and Verification**:
  - If `verified=False`, the outcome is `unverified` and exit code is `1`.
  - If `complete=False` (and not a non-destructive preview), the outcome is `partial` or `skipped`.
  - If `exit=2`, kind is `error` and outcome is `cannot-run` or `error`.
- **Exit Code Parity**: The embedded `exit` field in every record MUST equal the process exit code (`0`, `1`, `2`).
- **Path Sanitization**: All path-valued fields (`target`, `location`, `path`, etc.) MUST be repo-relative, normalized (forward slashes, no leading `./`), and free of user home paths (`/home/<user>/`, `/Users/<user>/`), usernames, or hostnames. All records pass `aw sanitize --agent` with zero findings.
- **ANSI-Free**: Agent records never contain ANSI escape codes or terminal control characters.

---

## 5. Record Examples

### Clean Bounded Result (`exit: 0`)
```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check plans","outcome":"clean","exit":0,"checked":17,"findings":0,"verified":true,"complete":true,"evidence":["ipd-lint:author"],"next":null}
```

### Mutation Preview Result (`exit: 0`)
```json
{"schema":"aw.agent/v1","kind":"result","cmd":"rename plans","outcome":"preview","exit":0,"applied":false,"complete":false,"verified":true,"changes":[{"kind":"rename","path":"plans/old-slug.ipd.md"}],"target":"plans/6psux0","next":"aw rename plans 6psux0 --slug new-slug --apply"}
```

### Domain Findings Result (`exit: 1`)
```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check specs","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":2,"diagnostics":[{"location":"specs/01.md","rule":"spec.draft"},{"location":"specs/02.md","rule":"spec.title"}],"next":"aw check specs --fix"}
```

### Stream Summary with Truncation (`exit: 1`)
```json
{"schema":"aw.agent/v1","kind":"summary","cmd":"attention","outcome":"findings","exit":1,"total":49,"emitted":20,"omitted":29,"complete":false,"next":"aw attention --agent --limit 50"}
```

### Cannot-Run Error (`exit: 2`)
```json
{"schema":"aw.agent/v1","kind":"error","cmd":"check","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"next":"aw check --help"}
```

---

## 6. Token Control and Escape Hatches

To minimize token usage during agent orchestration while preserving complete decision facts:

- **Compact Defaults**: By default, agent records emit concise identifiers (check names in evidence receipts, count of changes when large, minimal diagnostic fields) rather than verbose text paragraphs.
- **`--fields <list>`**: Projects records down to explicitly requested fields while preserving mandatory envelope metadata (`schema`, `kind`, `cmd`, `exit`, `outcome`, `complete`, `verified`).
- **`--limit <N>`**: Bounds stream item emission to at most `N` items and includes total counts, omitted counts, and a continuation command in the terminating `summary` record.
- **`--verbose` / `--json`**:
  - `--verbose` in agent mode includes full nested diagnostics, change details, and evidence dicts.
  - `--json` provides pretty-printed full `CommandResult` JSON dictionaries for human debugging.

---

## 7. Stream Separation and Broken-Pipe Policy

- **`stdout`**: Reserved strictly for final structured results (the interactive human view or machine JSONL records).
- **`stderr`**: Reserved for interactive progress indicators, transient status updates, cannot-start errors, and usage diagnostics. Diagnostics are never duplicated across both streams.
- **Broken Pipes**: All handlers catch `BrokenPipeError` / `EPIPE` when writing to stdout and exit cleanly without dumping Python stack traces.

---

## 8. Schema Versioning

The canonical agent machine format is tagged with:
```json
{"schema":"aw.agent/v1", ...}
```

- **Record Kinds**: `result`, `summary`, `item`, `error`.
- **Evolution Contract**: Additive, optional fields within `aw.agent/v1` are backward compatible.
  Any breaking modification to record schema or field semantics requires a version bump
  (`aw.agent/v2`).

---

## 9. Automatic Non-TTY Migration Policy (Hard Cutover)

Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1` JSONL immediately upon release
with no deprecation window. Any external script parsing legacy plain-text or TSV pipe output
must migrate to `aw.agent/v1` or use explicit `--format` flags.

---

## 10. Relationship to Legacy `Drift` Convention and Spec Reconciliation

Spec `20260818-1525-01` G6 previously required commands to reuse the TSV `Drift` / `render_agent_drift`
convention from `artifact_core.py:247-266`.

**Normative Decision**:
- `CommandResult` and `aw.agent/v1` **SUBSUMES and REPLACES** the legacy `Drift` TSV wire format.
- The `0`/`1`/`2` exit classification of `drift_exit_code` carries over unchanged.
- `Diagnostic` provides bidirectional helpers (`from_drift()` and `to_drift()`) for internal code
  compatibility.
- This contract formally supersedes the TSV requirement in spec `20260818-1525-01` G6. Exactly one
  canonical machine format (`aw.agent/v1`) is active.
