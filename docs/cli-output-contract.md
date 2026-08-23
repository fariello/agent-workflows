# Normative CLI Output Mode Contract and Renderer Boundary

awcliux Order 01 (`hd3kln`) E-03 / V-03.

This document defines the normative contract governing audience selection, output modes,
stream conventions, exit code semantics, schema versioning, broken-pipe behavior, and
reconciliation with legacy machine formats across the `agent-workflows` (`aw`) CLI surface.

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

- `CommandResult`: `command`, `status` (`clean`, `findings`, `fail`, `preview`, `stale`, `error`),
  `exit_code` (`0`, `1`, `2`), `summary`, `diagnostics`, `changes`, `evidence`, `next_actions`, `data`.
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

## 4. Stream Separation and Broken-Pipe Policy

- **`stdout`**: Reserved strictly for final structured results (the interactive human view or machine
  JSONL records).
- **`stderr`**: Reserved for interactive progress indicators, transient status updates, cannot-start
  errors, and usage diagnostics. Diagnostics are never duplicated across both streams.
- **Broken Pipes**: All handlers catch `BrokenPipeError` / `EPIPE` when writing to stdout and exit
  cleanly without dumping Python stack traces.

---

## 5. Schema Versioning

The canonical agent machine format is tagged with:
```json
{"schema":"aw.agent/v1", ...}
```

- **Record Kinds**: `result`, `summary`, `error`.
- **Evolution Contract**: Additive, optional fields within `aw.agent/v1` are backward compatible.
  Any breaking modification to record schema or field semantics requires a version bump
  (`aw.agent/v2`).

---

## 6. Automatic Non-TTY Migration Policy (Hard Cutover)

Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1` JSONL immediately upon release
with no deprecation window. Any external script parsing legacy plain-text or TSV pipe output
must migrate to `aw.agent/v1` or use explicit `--format` flags.

---

## 7. Relationship to Legacy `Drift` Convention and Spec Reconciliation

Spec `20260818-1525-01` G6 previously required commands to reuse the TSV `Drift` / `render_agent_drift`
convention from `artifact_core.py:247-266`.

**Normative Decision**:
- `CommandResult` and `aw.agent/v1` **SUBSUMES and REPLACES** the legacy `Drift` TSV wire format.
- The `0`/`1`/`2` exit classification of `drift_exit_code` carries over unchanged.
- `Diagnostic` provides bidirectional helpers (`from_drift()` and `to_drift()`) for internal code
  compatibility.
- This contract formally supersedes the TSV requirement in spec `20260818-1525-01` G6. Exactly one
  canonical machine format (`aw.agent/v1`) is active.
