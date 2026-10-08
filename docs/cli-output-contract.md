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
explicit (--json / --format <fmt>)  >  --agent  >  human
```

1. **Explicit format flags** (`--json`, `--format json`, `--format <fmt>`):
   Selects the specified explicit serialization mode (`OutputMode.JSON`). Overrides `--agent`.
   Color is disabled (`color=False`).
2. **Agent flag**:
   If `--agent` is passed, `OutputMode.AGENT` is selected. Output is emitted as compact,
   ANSI-free `aw.agent/v1` JSONL records. Color is disabled (`color=False`).
3. **Human (the default, TTY or not)**:
   With no agent/explicit format flag, `OutputMode.HUMAN` is selected. THE TTY-NESS OF STDOUT
   DOES NOT AFFECT THE MODE: a piped, redirected or captured invocation still emits
   human-readable text, and `--agent` is the only way to obtain `aw.agent/v1` JSONL. TTY-ness
   affects COLOR only (see section 1.1).
   *Note*: `stdin.isatty()` controls interactive prompting (such as confirmation dialogs or
   wizards), NOT the output audience or mode. See section 9 for why those two axes stay separate.
4. **Color and Styling Flags**:
   `--color`, `--no-color`, `NO_COLOR`, and `FORCE_COLOR` control ANSI styling within human mode
   only. They never alter the audience mode itself (i.e. `--no-color` on a TTY emits monochrome
   human text, never machine JSONL; `--color` on a pipe emits colored human text, never JSONL).

### 1.1 Color Precedence: flag beats env beats detection

The styling decision is a separate, single chain, resolved once in `term.should_color`. Highest
precedence first:

```text
--color / --no-color  >  NO_COLOR / FORCE_COLOR  >  TERM capability  >  stdout.isatty()
```

| # | Layer | Rule |
| --- | --- | --- |
| 1 | Flag | `--color` forces ANSI on; `--no-color` forces it off. Passing BOTH is a usage error (exit 2), never a silent winner, so a scripted invocation never depends on argument order. |
| 2 | Env | `NO_COLOR` (any value, including empty) disables, unless `FORCE_COLOR` is set to a forcing value. `FORCE_COLOR` enables when set to a forcing value. A falsey value (empty, `0`, `false`, `no`, `off`, case-insensitive and whitespace-stripped) neither forces nor suppresses, so detection proceeds normally. Both `FORCE_COLOR` readings route through `term._force_color_is_forcing`. |
| 3 | Capability | `TERM=dumb` or an unset `TERM` disables. |
| 4 | Detection | Otherwise ANSI is on only when the target stream is a real TTY. |

Worked cases, each pinned by a test in `tests/test_term.py`:

| Invocation | Result |
| --- | --- |
| `NO_COLOR=1 aw <cmd> --color` | colored (flag beats env) |
| `FORCE_COLOR=1 aw <cmd> --no-color` | monochrome (flag beats env) |
| `FORCE_COLOR=1 aw <cmd> \| cat` | colored (env beats detection) |
| `aw <cmd> \| cat` | monochrome (detection alone) |
| `aw <cmd> --color \| cat` | colored (flag beats detection) |
| `FORCE_COLOR=0 aw <cmd> \| cat` | monochrome (falsey value does not force) |
| `FORCE_COLOR=off aw <cmd> \| cat` | monochrome (falsey value does not force) |
| `FORCE_COLOR=false aw <cmd> \| cat` | monochrome (falsey value does not force) |
| `NO_COLOR=1 FORCE_COLOR=0 aw <cmd> \| cat` | monochrome (falsey value does not cancel NO_COLOR) |
| `NO_COLOR=1 FORCE_COLOR=0 aw <cmd>` | monochrome (falsey value does not cancel NO_COLOR) |
| `FORCE_COLOR=0 aw <cmd>` | colored (falsey value does not suppress; detection proceeds) |

Two invariants hold across all of it. FIRST, a flag NEVER reaches the engine by mutating
`os.environ`: the override is passed as an argument, because this package spawns nested `aw`
processes and an environment variable would be inherited, silently restyling a child's output.
SECOND, the flags are STYLING ONLY: `--agent` and `--json` payloads are byte-identical under
every combination of them and contain no ANSI escapes (section 6).

### 1.2 Interactivity Precedence: asymmetric safety ladder

The interactivity decision (may this process prompt a human?) is resolved once in `term.is_interactive`.
Unlike the color ladder, interactivity follows an ASYMMETRIC ladder: a wrong refusal is recoverable,
an unbounded wait is not. Highest precedence first:

```text
--no-interactive  >  AW_NONINTERACTIVE / CI  >  --interactive  >  stdin_is_interactive  >  output_stream.isatty()
```

| # | Layer | Rule |
| --- | --- | --- |
| 1 | Negative Flag | `--no-interactive` (or `override=False`) disables interactive prompting immediately, beating all other rungs. Passing BOTH `--interactive` and `--no-interactive` is a usage error (exit 2), never a silent winner. |
| 2 | Env | `AW_NONINTERACTIVE` or `CI` set to a truthy value (any value not in `("", "0", "false", "no")`) forces non-interactive (`False`). This takes precedence over `--interactive` to ensure automated CI pipelines and runner signal handlers holding locks never hang on an unattended prompt. |
| 3 | Positive Flag | `--interactive` (or `override=True` passed to `term.is_interactive`) forces interactive mode on when not in a forced non-interactive environment, beating stream detection rungs. |
| 4 | Stdin | `stdin` must be interactive per `term.stdin_is_interactive()` (validates terminal and Windows console handle). |
| 5 | Output | Target output stream (defaults to `sys.stdout`, or `sys.stderr` when specified) must also be a TTY. |

Fail-safe invariant: when the process is non-interactive, commands fail closed (auto-decline or take documented safe non-interactive defaults), never hanging waiting for human input.

Programmatic arguments vs. flags: the ladder above governs `term.is_interactive` and the CLI flag pair. A module-local predicate holding a direct programmatic argument (such as `git_commit_helper._is_interactive`) may honor an explicit boolean ahead of the environment rung, because a programmatic caller that already knows its channel is not an operator's ambient flag wish that CI must be allowed to veto.

Worked cases, each pinned by tests in `tests/test_interactivity_resolver.py`:

| Invocation / Context | Result |
| --- | --- |
| `aw <cmd> --no-interactive` on real TTY | non-interactive (negative flag beats detection) |
| `CI=1 aw <cmd> --interactive` | non-interactive (env beats positive flag for safety) |
| `AW_NONINTERACTIVE=1 aw <cmd> --interactive` | non-interactive (env beats positive flag for safety) |
| `CI=0 aw <cmd> --interactive \| cat` | interactive (positive flag beats detection when env is not forcing) |
| `aw <cmd> --no-interactive --interactive` | usage error (exit 2) |
| `AW_NONINTERACTIVE=1` with TTY streams | non-interactive (env beats detection) |
| `CI=1` with TTY streams | non-interactive (env beats detection) |
| `CI=0` or `CI=false` with TTY streams | interactive (CI truthiness parsed) |
| `stdin` TTY + `stdout` pipe | non-interactive (rung 5 prevents pipe hang) |
| `is_interactive(override=True)` on non-TTY | interactive (positive override beats detection) |
| `is_interactive(override=False)` on TTY | non-interactive (negative override beats all) |
| `git_commit_helper._is_interactive(True)` under CI | interactive (direct programmatic argument beats environment rung) |

### 1.3 Flag Availability: uniform across every subcommand

`--color`/`--no-color` and `--interactive`/`--no-interactive` work on EVERY subcommand, nested ones included.
That uniformity is the contract: a flag that works on one verb and is a usage error on another cannot be
scripted around. It is reached two ways, and the difference is visible only in `--help`:

1. **By declaration.** `--color`, `--no-color`, `--interactive`, `--no-interactive`, `--agent`, and `--json`
   are declared ONCE on shared argparse parents (`presentation` and `common`) and inherited by every subcommand
   that `aw` itself handles.
2. **By consumption.** The host-driver leaves that forward their argv VERBATIM to another program
   (`aw oc run`, `aw agy run`, the `review`/`integrate` aliases, `aw run as`, `aw run ipd`,
   `aw agy sessions|view|exec`) deliberately declare NO flags of their own, so that the downstream
   parser owns every flag and its `--help` and the two spellings cannot drift. `aw` therefore
   CONSUMES `--color`/`--no-color` and `--interactive`/`--no-interactive` from the raw argv before forwarding it.
   The flags work; they are simply absent from that leaf's own `--help`, which renders the driver's help rather
   than `aw`'s.

`--agent` and `--json` are NOT provided on the forwarded leaves, by either route. `aw` does not
render their output, and on `aw oc run start` a downstream `--agent` is an OpenCode AGENT NAME rather
than a machine-output flag, so honoring it at the `aw` layer would change what the operator asked
for. Use the driver's own flags there.

`tests/test_flag_surface_uniformity.py` enforces both pairs across the CLI surface: it tests observable command
execution and behavioral dispatch, verifying flag acceptance on parsed commands, pre-dispatch consumption on
forwarded driver commands without unrecognized argument errors, exit 2 mutual exclusion on both operator and
parser backstop paths, and `--` token passthrough.

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
All three renderers expose identical domain facts (counts, paths, evidence, exit code) with zero domain drift; across both machine surfaces (`--agent` and `--json`), path-valued and free-text envelope fields share the same home-path redaction posture.

---

## 3. Exit Code Semantics

The CLI enforces a three-state exit classification across the vast majority of verbs:

- `0` (**Clean / Success**): Command completed cleanly with no negative domain findings or violations.
- `1` (**Domain Findings / Negative Result**): Command completed execution, but detected actionable
  findings, policy violations, contract drift, uncommitted conflicts, or failed assertions.
- `2` (**Usage Error / Cannot-Run / Fatal**): Invalid arguments, conflicting flags, missing required
  environment dependencies, or fatal execution errors preventing domain inspection.

A condition is classified by its nature and not by its audience, so every audience surface of one condition returns the same code. In particular, "no AW project found at the working directory or any ancestor" is classified as cannot-run and returns exit 2 on the human, `--agent`, and `--json` surfaces alike.

The boundary governing this three-state classification is defined strictly by the record format a verb emits:

- **Verbs emitting `aw.agent/v1` records**: Strictly bound to `{0, 1, 2}`. Mechanically enforced by `agent_schema.validate_agent_record`, which rejects any `exit` value outside `{0, 1, 2}` with a validation error, and by `agent_schema.render_jsonl_record`, which refuses to render non-conforming records. The exit parity rule in Section 4 requires the embedded `exit` field to equal the process exit code, confining any condition reachable on an agent machine surface to these three states.
- **Verbs emitting bare JSON or non-agent payloads**: Verbs that do not emit `aw.agent/v1` records (such as `run_cli._emit_error` machine payloads on `aw runs` commands, which emit bare JSON dictionaries without envelope fields) are not bound by the three-state rule. Across the 164 command declarations in the inventory, 10 declarations declare exit codes outside `{0, 1, 2}`, all belonging to the run-execution and lifecycle family (`aw run`, `aw runs`, `aw oc runipd`, `aw agy runipd`, and `aw ipd execute-set`). These commands carry a separate, wider exit vocabulary documented in Section 3.1 below. The two vocabularies are not unified into a single schema.

Readers can inspect `artifact_types.EXIT_CANNOT_RUN` for the shared cannot-run constant and `command_surface.CommandDeclaration.exit_contract` for each command's normative declaration. That declaration enumerates codes the command returns on its own path and deliberately does not enumerate signal-derived codes; an interrupted command exits 130 (or is killed by its signal) without that code appearing in any declaration. The interrupt path emits no `aw.agent/v1` record at all, so Section 4's exit-parity requirement has nothing to pair a signal code with.

### 3.1 Run-Execution Exit Vocabulary

Commands in the run-execution family (`aw run`, `aw runs`, `aw oc runipd`, `aw agy runipd`, and `aw ipd execute-set`) manage and inspect multi-step orchestration runs, ledgers, and execution queues. These commands emit bare JSON dictionaries or execution manifests rather than `aw.agent/v1` records, and they use a wider exit code vocabulary to distinguish operational, corruption, and workflow states.

Two distinct live exit tables govern these verbs and disagree on the meaning of codes `3` and `4`. They are not reconciled into a single table:

1. **The `aw runs` inspection and step lifecycle table** (defined by constants `run_cli.EXIT_OK` through `run_cli.EXIT_NOT_A_LEDGER` in `agent_workflows/run_cli.py`):
   - `0`: Clean / success. Run completed cleanly or inspection succeeded.
   - `1`: Incomplete run. Run finished with unsatisfied predicates or pending steps (`runs status`, `run finalize`).
   - `2`: Invalid invocation or usage error. Missing ledger, invalid flags, or command syntax error (`run start`, `runs next`, `run record`, `runs resume`, `run cancel`, `runs status`, `run finalize`).
   - `3`: Blocked. Run execution cannot proceed due to an unknown outcome, exhausted retry budget, or non-runnable state (`run start`, `runs next`, `run record`, `runs resume`, `runs status`).
   - `4`: Invalid evidence. Captured step evidence is invalid or rejected by completion checks (`run finalize`).
   - `5`: Ledger corruption. Hash chain break, schema mismatch, or torn record in ledger (`run start`, `runs next`, `run record`, `runs resume`, `run cancel`, `runs status`).
   - `6`: Operational failure. Process lock contention, illegal lifecycle transition, or unauthorized state mutation (`run start`, `run record`, `run cancel`, `run finalize`).
   - `7`: Not a ledger. Target path exists and contains valid JSONL, but lacks mandatory ledger envelope fields (`runs next`, `runs resume`, `runs status`).

2. **The host driver and queue aggregate table** (defined by spec `25kzda` Section 5.6 and implemented by `run_evidence.aggregate_run_exit` and `runner_shared.run_exit_code` for `oc runipd`, `agy runipd`, and `ipd execute-set`):
   - `0`: Clean. Every actionable item in the queue verified cleanly; remaining items were benign skips.
   - `1`: Queue findings or stranded work. At least one item failed, ended with unsatisfied dependencies, or finished with unintegrated work.
   - `2`: Invalid invocation, invalid selector, or unknown action type.
   - `3`: Human input required (`AGGREGATE_NEEDS_INPUT`). A human approval gate or review gate stopped execution, requiring operator action.
   - `4`: Run-wide abort class. Enumerated in spec `25kzda` 5.6 for run-wide integrity failures; not returned by current driver `run_queue` dispatch.

#### Disagreement on Codes 3 and 4

Callers and scripts must note the divergence between these two tables:
- **Code 3**: In `run_cli`, code 3 means execution is blocked (`EXIT_BLOCKED`, unknown outcome or exhausted retries). In `oc runipd` and `agy runipd`, code 3 means human input or approval is required (`AGGREGATE_NEEDS_INPUT`).
- **Code 4**: In `run_cli`, code 4 means invalid evidence (`EXIT_INVALID_EVIDENCE`). In spec `25kzda` 5.6, code 4 represents run-wide abort classes.

A third internal table exists as `compat_migration.EXIT_CODES` in `agent_workflows/compat_migration.py` (which maps `gate_failed` to 3 and `compatibility_break` to 4), but it is an unconsumed internal constant with zero callers across the repository and does not represent an observable CLI exit surface.

### 3.2 Severity Tier Contract and Gate Semantics

The `Diagnostic` type defines three severity levels: `error`, `warning`, and `info` (Section 2). While this vocabulary suggests a three-level scale of seriousness, its effect on process exit codes is strictly two-level.

#### The Exit-Code Contract (Findings Gates)

For `--check` invocations, CI checks, and finding reports, `info` is the ONLY severity tier that does not contribute to exit 1. The authority governing this mapping is `artifact_core.drift_exit_code`, together with rule declarations in `check_engine.RULE_REGISTRY`:

- `info`: Evaluates to clean (`0`). A lone `info` finding or an empty finding list returns exit code `0`.
- `warning`: Evaluates to failing (`1`). A `warning` finding fails the exit-code gate exactly as an `error` does.
- `error`: Evaluates to failing (`1`).
- Absent, empty, or unrecognized severity: Evaluates to failing (`1`). The check engine fails closed. If a diagnostic carries an empty severity string `""`, an unknown label such as `"advisory"` or `"warn"`, or wrong casing like `"INFO"`, `artifact_core.drift_exit_code` treats it as failing.
- Unregistered rules: Stamped with severity `error` by `check_engine._DEFAULT_RULESPEC`. Forgetting to register a rule in `check_engine.RULE_REGISTRY` yields the strictest behavior rather than the laxest.

#### The Second Contract: Per-Gate Lifecycle Behavior

The exit-code rule above is not uniform across all repository gates. Two distinct lifecycle gates apply narrower contracts, and they must be understood individually rather than merged:

1. **Commit and work-begin gates (`aw commit` and `aw work begin`)**:
   Enforced in `work_cmd._validate_plan_via_engine`. Here, `error` findings refuse the operation, `warning` findings print as non-blocking advisories, and `info` findings are dropped silently.

   *Rule-ID override*: At this gate, severity is not the only decision input. `work_cmd._validate_plan_via_engine` routes `check_engine._SCOPE_DRIFT_RULE` (`check.scope-drift`) to the advisory list by rule ID even though it is registered as `error`. This override is intentional: lowering the registered severity of `check.scope-drift` would weaken `aw check`, CI, and pre-commit hooks, while the commit gate handles path validation through its own staged-path check and defers execution-wide scope reconciliation to `aw ipd finalize`.

2. **Durable-carrier merge gate (`aw ipd lint`)**:
   At `aw ipd lint`'s durable-carrier merge, only `info` is advisory. A `warning` blocks the gate, adhering to the exit-code contract rather than the commit-gate contract.

#### Summary for Rule Authors

In summary, `info` is advisory everywhere, whereas `warning` is advisory at exactly two gates (`aw commit` and `aw work begin`) and failing everywhere else (including `aw check`, CI, and `aw ipd lint`).

Practical consequence: to author a rule that reports diagnostics without ever failing any gate or check, register the rule with severity `info`.

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
- **Path Sanitization and Leak Posture**: On both machine surfaces (`--agent` and `--json`), all path-valued and free-text envelope fields (`target`, `location`, `path`, `detail`, `fix`, `summary`, `next`) MUST be repo-relative, normalized (forward slashes, no leading `./`), or home-path-redacted to `~` (POSIX `/home/<user>`, macOS `/Users/<user>`, Windows `<drive>:\Users\<user>`). All records pass `aw sanitize --agent` with zero findings. The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths. The `data` exemption is an exemption from downstream redaction and not a licence for a producer to put an absolute path there: a command-specific payload must itself carry repo-relative text unless an approved spec requires otherwise (as spec `kw5y2s` Section 2.4 does for `data.logical_roots`). Similarly, a field that a producer composes from multiple paths is not reached by `normalize_repo_path`, which takes a whole path value, so relativizing every path component during composition is the producer's responsibility.
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

### Stream Summary with Truncation (`exit: 0`)
```json
{"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"partial","exit":0,"total":4,"emitted":2,"omitted":2,"complete":false,"next":"aw runs query findings --limit 4"}
```

### Cannot-Run Error (`exit: 2`)
```json
{"schema":"aw.agent/v1","kind":"error","cmd":"check","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"next":"aw check --help"}
```

---

## 6. Token Control and Escape Hatches

To minimize token usage during agent orchestration while preserving complete decision facts:

- **Compact Defaults**: By default, agent records emit concise identifiers (check names in evidence receipts, count of changes when large, minimal diagnostic fields) rather than verbose text paragraphs.
- **`--fields <list>`**: Projects records down to explicitly requested fields while preserving mandatory envelope metadata (`schema`, `kind`, `cmd`, `exit`, `outcome`, `complete`, `verified`). Projections additionally retain whatever the record kind requires to remain valid, including a summary's `total`, `emitted`, and `omitted` counts and a preview result's `applied` flag. Projections also preserve `next` whenever present: a continuation or recovery command cannot be reconstructed by the caller, so retaining it ensures the MUST requirements in Section 11.1 (broadening or fallback commands on empty results) and Section 11.4 (recovery commands on cannot-run error records) hold under `--fields` too. A projection never yields a record that fails validation, so `--fields` is safe to pass on any command.
- **`--limit <N>`**: Bounds payload emission to at most `N` items. For streaming commands (such as `runs query`), it bounds item emission and includes total counts, omitted counts, and a continuation command in the terminating `summary` record; for single-record commands (`check`, `search`), it bounds the in-record payload (`diagnostics`, `matches`) with total, emitted, and omitted counts, setting `complete: false` when truncated; for index generation (`index`, `research index`), it configures the recent-item hot window.
- **`--verbose` / `--json`**:
  - `--verbose` in agent mode includes full nested diagnostics, change details, and evidence dicts.
  - `--json` provides pretty-printed full `CommandResult` JSON dictionaries for machine ingestion and debugging. Its envelope fields (`summary`, `diagnostics`, `changes`, `evidence`, `next_actions`) are home-path redacted, while `data` is an unredacted passthrough (exempt per spec `kw5y2s` Section 2.4).

---

## 7. Stream Separation and Broken-Pipe Policy

- **`stdout`**: Reserved strictly for final structured results (the interactive human view or machine JSONL records).
- **`stderr`**: Reserved for interactive progress indicators, transient status updates, cannot-start errors, and usage diagnostics. Diagnostics are never duplicated across both streams.
- **Broken Pipes**: A top-level guard at the single process entry point `cli.main` catches `BrokenPipeError` when writing or flushing stdout, redirecting stdout to `os.devnull` to ensure the process exits cleanly within Section 3's three-state vocabulary (`0`, `1`, `2`) without dumping Python stack traces or shutdown flush errors (exit 120). When the command completed dispatch and only the final stdout flush failed, the command's computed verdict (`rc`) is preserved and returned unchanged. When the command was interrupted mid-write during dispatch, the guard returns `0`; in that case output is truncated and the exit code describes the closed pipe rather than repository findings, so callers requiring an authoritative domain verdict must consume the full stream or use machine surfaces (`--agent` / `--json`). The guard catches `BrokenPipeError` specifically and never bare `OSError`, ensuring genuine write failures such as `ENOSPC` (no space left on device) are not suppressed.

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

## 9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19

**This policy is RETRACTED. It is recorded here rather than deleted so a reader can tell that it
was reversed deliberately, and not lost in an edit.**

The retracted text read: "Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1` JSONL
immediately upon release with no deprecation window. Any external script parsing legacy plain-text
or TSV pipe output must migrate to `aw.agent/v1` or use explicit `--format` flags."

**What is true instead.** Piping or redirecting `aw` emits HUMAN-READABLE TEXT. `--agent` is the
explicit and only way to obtain `aw.agent/v1` JSONL, and `--json` the only way to obtain the full
structured JSON. Non-TTY stdout affects COLOR only (section 1.1).

**Why it was retracted** (maintainer ruling, ttyflags `yaxr4i` OQ-01, 2026-09-10):

1. **The promise never shipped.** No release ever implemented it. `select_output` has never
   consulted `stdout.isatty()` for mode selection; the only TTY consultation is the color one.
   So this section described behavior that did not exist, in a document published as normative.
2. **Nothing can depend on behavior that never existed**, while an unknown number of consumers
   (external scripts, log captures, CI steps that pipe `aw` and read prose) depend on the actual
   behavior. Implementing the promise would break them, with no compensating gain.
3. **The capability was never missing.** `--agent` already emits the JSONL, and this
   repository's own CI uses the explicit flag rather than relying on an automatic switch, so the
   auto-switch would have been convenience, not capability.

**What this does NOT say.** It does not rule that non-TTY detection is unwanted, and it does not
foreclose a future proposal to make piped output machine-readable. It retracts one AUTO-SWITCH
promise that was never implemented. Any such future change needs its own decision and a migration
story this section never had (it specified a hard cutover with no deprecation window).

### 9.1 Design constraint on a future `--tty` flag and shipped flag pair

No `--tty` flag exists, deliberately. This section records the constraint and the shipped architecture,
so a successor inherits the analysis instead of rediscovering it.

**TTY-ness controls two unrelated things, through two different streams.**

| Axis | Keyed on | Governs | Where |
| --- | --- | --- | --- |
| Presentation | `stdout` | whether ANSI escapes are emitted | `term.should_color` |
| Interactivity | `stdin` + `stdout`/`stderr` | whether the process may PROMPT a human | `term.is_interactive` |

**So a single undifferentiated `--tty` boolean MUST NOT be added.** Conflating the axes would let
a request for color silently re-enable prompting, which would weaken a real fail-safe: today
`cli._confirm`, `git_commit_helper._is_interactive`, and all CLI prompt sites DECLINE rather than prompt when
streams are non-interactive, which is what keeps an unattended runner from wedging forever on a question nobody can
answer. Two requirements follow, both now fulfilled:

1. **Two axes, never one flag.** The two axes are separate flags: `--color/--no-color` for presentation
   and `--interactive/--no-interactive` for interactivity. No combined or undifferentiated `--tty` spelling
   exists.
2. **One resolver for interactivity.** The interactivity override routes through a SINGLE
   originating resolver (`term.is_interactive`) with an asymmetric safety ladder (`--no-interactive` >
   `AW_NONINTERACTIVE`/`CI` > `--interactive` > `term.stdin_is_interactive` > output stream TTY detection)
   and a fail-closed default, rather than per-site flag checks. Every call site consults this resolver,
   so an operator override applies uniformly.

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

---

## 11. Empty, Loading, and Error State UX Convention

highpbacklog0822 Order 04 (`89bby9`) E-02 / V-02.

This section defines the uniform UX convention governing empty results, transient progress step-cues,
mutation feedback, and error states across all `aw` verbs.

### 11.1 Empty Result Convention (Read and List Verbs)
When a query, find, search, or list verb matches zero records or produces an empty result set:
- **Discriminator (Standing Question vs. Named-Artifact Assertion)**:
  The convention distinguishes between two kinds of zero-match requests:
  - **Standing questions about repository state**: A query asking about a category of artifacts (a tree name, an attention class, an artifact status, a priority, a run state, or a bare invocation with no selector at all) is a standing question. A zero-match result indicates the repository currently has zero artifacts in that state; this is a clean empty result and is **not refused**.
  - **Assertions that a named artifact exists**: A query specifying an artifact identifier (an id6, a setid, or a filename fragment) asserts that a specific artifact exists. If that selector matches zero records, the invocation is treated under Section 11.4 as an unresolved selector refusal and exits 2 (`attention.EXIT_UNRESOLVED_SELECTOR`) with `outcome: "cannot-run"`, `verified: false`, and `complete: false`.
- **Precedent and Scope**:
  Spec `25kzda` Sections 2.3 and 2.4a established the precedent for this distinction, observing that an empty status query such as `reviews` matching nothing is a successful answer rather than an error, while a misspelled id6 exits 2. Spec `25kzda` specifically governs the runner verbs `aw oc run` and `aw agy run` rather than read verbs generally, so its status-selector carve-out serves as precedent rather than a binding contract. The read verb `aw attention` follows and extends this pattern by deriving its exempt vocabulary via `attention.selector_vocabulary` and evaluating `attention.SelectorMatchFacts.refusable`, following the shipped precedent in `run_viewer.emit_unresolvable_target_refusal`.
- **Not Refused vs. Exit Codes (Drift Separation)**:
  The standing-question exemption is worded as **not refused** rather than flatly "exits 0". The exemption skips the refusal predicate, after which the verb's ordinary exit classification still applies. In a repository without drift or findings, the exempt query yields `outcome: "clean"` with exit 0. However, if the repository concurrently contains contract drift or policy violations, a concurrent drift finding still reports itself normally and exits 1 through the drift path. Conversely, a selector refusal is a separate condition from a contract finding: it neither appends a drift record nor flips the `--json` `valid` flag, ensuring an operator typo is never misreported as repository damage.
- **List-Mode Stream Rule (Pipe Safety)**:
  For list modes targeting machine ingestion (`-id`, `--paths`, `--filenames`), a selector refusal emits its diagnostic message to `stderr` while `stdout` remains strictly empty (0 bytes). This prevents error text from corrupting shell pipes or downstream tool consumers.
- **Never Fail Silently / Blank**: For non-refused empty results, the handler MUST NOT print blank output or an uninformative raw string.
- **Interactive Human TTY**: For non-refused empty queries, handlers MUST use `Term.empty_result(summary, filters=..., next_action=...)`.
  The render displays:
  1. Outcome line with clean status (e.g. `✓ CLEAN  no matching <type>`).
  2. `Active filters:` section echoing all applied selectors, types, sets, or flags.
  3. `Next` recommendation offering a broadening query (e.g. searching without selectors) or helpful navigation.
- **Agent Protocol (`aw.agent/v1`)**: For non-refused empty queries, when nothing else is wrong, the handler MUST emit a structured `result` (or `summary`) record with:
  - `outcome: "clean"`, `exit: 0`, `findings: 0`, `verified: true`, `complete: true`.
  - Evidence/data carrying the zero count and active filter dictionary.
  - `next`: the suggested broadening or fallback command.

### 11.2 Loading and Step-Cue Convention (Progress State)
- **Transient `stderr` Step-Cues**: Handlers performing synchronous multi-step operations (e.g. `doctor`, `index`, `check`)
  MUST emit progress step-cues to `stderr` formatted with bracketed info severity labels:
  `[INFO ] <Action>ing...` (via `Term.step_cue()` or `Term.severity_label("info")`).
- **Stream Segregation**: Progress cues MUST NEVER be written to `stdout`.
- **KISS Philosophy**: Synchronous CLI verbs MUST NOT implement spinners, background worker threads, or cursor-hiding ANSI machinery.

### 11.3 Mutation Feedback Convention
- **Consistent Outcome Feedback**: Every mutation verb (`apply`, `create`, `rename`, `archive`, `set`, etc.) MUST report
  its outcome clearly.
- **Human TTY**:
  - Applied mutations display `✓ EXECUTED` (or `✓ OK`), followed by `Changes:` and the modified paths.
  - Dry-run / preview invocations display `! PREVIEW`, followed by `Would change:` and a `Next` command with `--apply`.
- **Agent Mode**:
  - Applied mutations emit `applied: true`, `complete: true`, `changes: [...]`.
  - Previews emit `outcome: "preview"`, `applied: false`, `complete: true`, `changes: [...]`, and a `next` command with `--apply`.

### 11.4 Error States and No-Silent-Failure Rule
- **No Silent Failures**: Handlers MUST NEVER catch and swallow unexpected exceptions or return exit code `0` on fatal failure.
- **Usage / Cannot-Run Errors (`exit: 2`)**:
  - Missing mandatory arguments, unknown subcommands, or invalid selectors MUST exit `2`.
  - Human TTY: prints diagnostic message and usage help to `stderr`.
  - Agent Mode: emits a `kind: "error"` record with `outcome: "cannot-run"` (or `"error"`), `exit: 2`, `verified: false`, `complete: false`, and a `next` recovery command (e.g. `aw <cmd> --help`).
- **Domain Findings / Violations (`exit: 1`)**:
  - Verification failures, policy drift, or schema nonconformance MUST exit `1`.
  - Emits diagnostic findings with actionable `Fix:` hints and appropriate follow-up `next` actions.

---

## 12. Path Discovery and Resolution vs. Verification Receipts

Commands whose primary purpose is path discovery and artifact lookup (e.g. `aw find <selector>`, `aw find <type> <selector> --paths`) are strictly distinguished from verification, check, or mutation commands:

- **Token-Efficient Bare Paths**: When an agent searches for an artifact (e.g. by `id6`, Set, status, or slug fragment), the optimal output is pure, newline-delimited, repo-relative file paths (e.g. `.aw/records/plans/pending/...`). Wrapping file paths in multi-field JSON envelopes imposes unnecessary LLM parsing overhead and token consumption.
- **`--paths` (`-p`) Flag**: Query and discovery verbs support `--paths` to emit bare repo-relative file paths on `stdout`, one per line, with no column headers, ANSI formatting, or summary boilerplate.
- **`--agent` Mode for Discovery**: When `--agent` is passed to `aw find`, it emits a canonical `aw.agent/v1` stream: one `item` record per match followed by a terminal `summary` record. This allows token-bounded queries via `--limit` and field projection via `--fields`. While full unconstrained listings cost more than bare paths (measured on this repository at 1329 plans: 158031 bytes for bare paths versus 239238 bytes for path-only items (1.51x) or 329319 bytes for five-field records (2.08x)), bounded queries dramatically reduce token consumption (for example, `--limit 20` requires only 4809 bytes, or 3.0 percent of the bare full listing). Callers requiring bare paths use `--paths`, while callers requiring the full unstreamed dictionary use explicit `--json`.
- **Exit Classification**: If one or more matching paths are found, the command exits `0`. If a specific selector matches zero paths, the command exits `1` (or exits `0` when listing empty unfiltered sets in human mode).
