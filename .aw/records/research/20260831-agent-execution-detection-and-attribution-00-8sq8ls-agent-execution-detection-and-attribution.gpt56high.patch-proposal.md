---
id: 8sq8ls
created: 20260831
set: agent-execution-detection-and-attribution
order: 00
topic: [agent-detection, git-hooks, attribution]
model: gpt56high
kind: patch-proposal
status: todo
outcome: none-yet
summary: Proposed three-channel approach to detecting agent execution and attributing it: a normalized AW_* env contract, native tool markers, and process ancestry, plus a per-invocation context file for facts that change mid-session
consumed-by: []
priority: high
---

# Proposed AW Agent Execution Detection and Attribution Approach

- Source: authored by GPT 5.6 Sol High (high reasoning effort) and handed to this repo on 2026-08-31.
- Filed VERBATIM below the intake note; the original preamble it carried is reproduced here so nothing
  is lost, since the front matter above now owns status and scope:
  > **Status:** Proposed
  > **Research checked:** September 1, 2026
  > **Scope:** Git hooks and other tools that need to determine whether they were invoked by an agentic coding tool, whether AW was used, and whatever identity metadata is reliably available.
- NOT ADOPTED. This is a PROPOSAL under consideration, not a decision. The maintainer's assessment on
  filing was that it contains good ideas but need not be adopted wholesale. Consuming work should cite
  specific sections rather than treating the whole document as settled policy.
- TWO CORRECTIONS APPLIED AT FILING, both to the Hermes row and its code example, and both MEASURED
  against a real dump captured on this machine. The source claimed Hermes exports `HERMES_AGENT=true`
  and an `AI_AGENT` value; NEITHER is present in the build actually run here
  (`grep -cE '^(HERMES_AGENT|AI_AGENT)=' <dump>` returns 0). The observed markers are
  `HERMES_SESSION_ID`, `HERMES_INTERACTIVE`, `HERMES_QUIET`, `HERMES_KANBAN_BOARD` and
  `HERMES_REAL_HOME`. This matters because Hermes is one of the five hosts a commit guard would key
  on, so an unverified marker there would have produced a host that silently never matched. The
  document's own vendor-doc citation is retained at the end so the original claim can be re-checked
  against a newer Hermes build.
- The correction ALSO cleared a leak-sanitizer block: the source's Hermes value collided verbatim with
  a private sibling repo name, which the `private-repo` rule correctly refused. Fixing the FACT removed
  the collision as a side effect, which is why no allowlist exception was added (weakening a guard rule
  for a string that was also factually wrong would have been the worse trade).
- Related in-repo work: backlog `wjl471` (the agent-detecting commit guard) is the item this informs,
  and it already carries an independently MEASURED five-host environment matrix (OpenCode, Antigravity,
  Codex, Hermes, Claude Code, plus a plain-shell control) captured on this machine. Where this document
  and that matrix disagree, the local measurement is the evidence for THIS environment; this document is
  broader (it covers Gemini CLI, Goose, Copilot CLI, Aider, Amp, Cursor, Kiro) and correspondingly less
  verified here.

---

## Executive recommendation

Use three independent evidence channels, in this order:

1. **AW-declared context:** Every AW launcher, including `agy`, should inject a small normalized `AW_*` environment contract and an `AW_CONTEXT_FILE` path.
2. **Native tool evidence:** Detect stable variables deliberately exported by Codex, Claude Code, OpenCode, Gemini CLI, Hermes, Goose, GitHub Copilot CLI, and other tools.
3. **Process ancestry:** Inspect parent processes only when the first two channels are absent, incomplete, or contradictory.

Do not reduce the result to a single Boolean. Return structured evidence, confidence, conflicts, and the best-known values for:

- agentic tool
- tool version
- model and provider
- model variant or reasoning level
- AW session and native session
- agent PID and runner PID
- run and invocation identity
- agent depth

Environment variables are useful attribution hints, not an authorization boundary. A human can set them, an agent can unset them, and nested tools can inherit stale values. The goal is dependable behavioral guidance and audit correlation, not proof against a malicious process.

The most important design improvement over environment-only detection is the **per-invocation context file**. The environment carries immutable launch facts and a pointer. AW and tool-specific lifecycle adapters atomically update the file when a native session ID, actual PID, active model, model switch, or subagent identity becomes known.

## Why environment-only detection is insufficient

Several tools provide excellent native signals, but the ecosystem is inconsistent:

- Some export a current session ID, such as Codex, Claude Code, Hermes, Goose, and GitHub Copilot CLI.
- Some export only an execution marker, such as Gemini CLI.
- Some export a process PID, notably OpenCode.
- Some expose richer information only to hooks, not arbitrary shell subprocesses. Gemini hooks expose the session and per-request model. Claude hooks expose session, model, prompt, and subagent metadata. Kiro hooks expose a session in some modes.
- Some have no verified child-process marker, including Aider, Amp for ordinary shell commands, and Cursor Agent.
- Nested agents can inherit an outer agent's variables. A Codex bug report demonstrated a nested `codex exec` seeing its parent's `CODEX_THREAD_ID`, even though the nested invocation had a different thread ID.
- Models can switch during a session or be changed by routing and fallback. A launch-time environment variable cannot reliably describe the model used for the commit-producing turn.

For those reasons, detection should preserve all evidence and explicitly report disagreement.

## Native signal matrix

The table distinguishes a deliberate child-command contract from incidental configuration variables. "Strong agent execution" means the variable is set specifically in processes spawned for tool execution, not merely because a user configured the CLI.

| Tool | Best native child-process evidence | Session | Model | Version | PID | Assessment |
|---|---|---|---|---|---|---|
| **OpenCode** | `OPENCODE=1`, `AGENT=1`, `OPENCODE_PID=<pid>` | No verified child variable | No reliable active-model variable | No | `OPENCODE_PID` | Strong tool detection and PID. `AGENT=1` is generic and should not identify OpenCode without `OPENCODE`. |
| **OpenAI Codex CLI** | `CODEX_THREAD_ID=<uuid>` | `CODEX_THREAD_ID` | No verified active-model child variable | No | Ancestry | Strong session-bearing signal. Retain conflict detection because nested execution has previously leaked the outer thread ID. `AI_AGENT=codex` is proposed upstream but is not currently a contract. |
| **Claude Code** | `CLAUDE_CODE_CHILD_SESSION=1`, `CLAUDE_CODE_SESSION_ID=<id>`, `CLAUDECODE=1` | `CLAUDE_CODE_SESSION_ID` | Hook data and launch hints, not a universal active-model variable | No | Ancestry | Excellent. `CLAUDE_CODE_CHILD_SESSION=1` specifically distinguishes Claude-launched tool/hook processes from an IDE terminal. `CLAUDECODE=1` is broader. |
| **Gemini CLI** | `GEMINI_CLI=1` | Hook JSON `session_id` | `BeforeModel.llm_request.model` in hook JSON | No | Ancestry | Excellent execution marker. Hooks can enrich the AW context with session and actual request model. |
| **Hermes Agent** | CORRECTED AT FILING against a measured dump on this machine: the observed markers are `HERMES_SESSION_ID=<id>`, `HERMES_INTERACTIVE`, `HERMES_QUIET`, `HERMES_KANBAN_BOARD`, `HERMES_REAL_HOME`. The source document claimed a `HERMES_AGENT=true` flag and an `AI_AGENT` value, and NEITHER is present in the build actually run here (`grep -cE '^(HERMES_AGENT|AI_AGENT)=' -> 0`). Treat the session id as the reliable marker for this host. | `HERMES_SESSION_ID` | `HERMES_MODEL` or `HERMES_INFERENCE_MODEL` is a launch/config hint | No | Ancestry | Excellent and intentionally documented for child attribution. |
| **Goose** | `GOOSE_TERMINAL=1`, `AGENT=goose`, `AGENT_SESSION_ID=<id>` | `AGENT_SESSION_ID` in supported extension/shell contexts | `GOOSE_MODEL` and `GOOSE_PROVIDER` are configuration hints | No | Ancestry | Excellent. Goose documents this exact commit-hook use case. |
| **GitHub Copilot CLI** | `COPILOT_AGENT_SESSION_ID=<id>` | Same | No verified child variable | No | Ancestry | Excellent session-bearing signal, documented in the official changelog since 1.0.29. |
| **Kiro CLI / Amazon Q lineage** | Kiro hook JSON can contain `session_id`; `Q_TERM`, `QTERM_SESSION_ID`, and `Q_SET_PARENT_CHECK` identify Q terminal integration | Hook-dependent | Hook/config-dependent | `Q_TERM` is a terminal integration version, not necessarily the agent version | Ancestry | Native environment evidence is weak for agent execution. Do not treat `Q_TERM` alone as proof that an agent invoked the command. A Kiro issue documents missing hook session IDs in classic and non-interactive modes. |
| **Aider** | No verified general child-agent marker | No | `AIDER_*` values are configuration, not attribution | No | Ancestry | AW injection is the reliable path. Do not infer execution merely from an `AIDER_*` variable. |
| **Amp** | `TOOLBOX_ACTION=execute` is meaningful only inside an Amp toolbox executable | No verified general shell-child session | No verified child variable | No | Ancestry | No verified general marker for commands run by Amp. Do not rely on the previously reported but undocumented `AGENT=amp`. |
| **Cursor Agent CLI** | No verified general child-agent marker found | No verified child variable | CLI selection is known to the AW launcher | No | Ancestry, with executable path | AW injection is the reliable path. The binary name `agent` is too generic unless its executable path identifies Cursor. |
| **AW / `agy`** | Contract proposed below | AW owns this | AW owns launch selection and can be enriched later | AW can query the actual executable once | AW owns the child process | This should be the authoritative normalized channel. `agy` is the runner, while `AW_AGENT_TOOL` names the underlying tool when one exists. |

## Proposed `AW_*` environment contract

### Required variables

| Variable | Meaning | Example |
|---|---|---|
| `AW_ENV_SCHEMA_VERSION` | Version of the environment contract | `1` |
| `AW_AGENT` | `1` only when AW intentionally launched an agent execution | `1` |
| `AW_RUN_ID` | Durable identity of the overall AW run | `019d...` |
| `AW_INVOCATION_ID` | Identity of this particular launched agent process | `019d...` |
| `AW_RUNNER` | AW frontend or runner | `agy`, `oc`, `codex` |
| `AW_RUNNER_PID` | PID of the AW process that launched or supervises the agent | `48210` |
| `AW_AGENT_TOOL` | Canonical underlying agentic tool | `opencode`, `codex`, `claude-code`, `gemini`, `hermes`, `goose`, `copilot`, `kiro`, `aider`, `amp`, `cursor` |
| `AW_CONTEXT_FILE` | Absolute path to the per-invocation JSON context | `/.../invocations/<id>.json` |

### Optional variables, set only when known

| Variable | Meaning |
|---|---|
| `AW_RUNNER_VERSION` | AW runner version or source revision |
| `AW_AGENT_TOOL_VERSION` | Version reported by the exact resolved executable |
| `AW_AGENT_MODEL` | Model selected at launch, or last model known before launch |
| `AW_AGENT_MODEL_PROVIDER` | Provider or gateway, when distinct from the model |
| `AW_AGENT_VARIANT` | Reasoning level, model variant, profile, or analogous selection |
| `AW_AGENT_SESSION_ID` | AW's stable logical session identity |
| `AW_AGENT_NATIVE_SESSION_ID` | Tool-native session/thread ID, only when actually known |
| `AW_AGENT_PID` | Agent process PID, when it can be established before child tools run |
| `AW_AGENT_DEPTH` | Zero-based AW-controlled agent nesting depth |
| `AW_AGENT_LAUNCH_MODE` | `interactive`, `headless`, `exec`, `resume`, or another canonical mode |

### Naming and value rules

1. Unset unknown optional values. Do not export empty strings, `unknown`, or guessed values.
2. `AW_RUNNER=agy` and `AW_AGENT_TOOL=opencode` are different facts. Do not collapse the wrapper and the actual agent tool.
3. `AW_AGENT_SESSION_ID` is AW's logical identity. `AW_AGENT_NATIVE_SESSION_ID` is the tool's identity. They may match, but neither should silently impersonate the other.
4. `AW_AGENT_MODEL` is the launch-time or best-known model. The context file should distinguish `requested_model`, `active_model`, and `last_model` when adapters can observe them.
5. Treat the context file as authoritative over launch-time optional variables because models and native sessions can change after process creation.
6. Never put prompts, credentials, API keys, full command lines, or unrestricted environment dumps in this contract.
7. Store context under AW's user-state directory, never in the repository or worktree. The detector should not create untracked repository files.

### Scrub inherited attribution before nested launches

When AW launches a new agent from inside another agent, remove the outer agent's attribution-only variables before spawning the child, then add the new `AW_*` contract. This prevents an outer Codex thread, Claude session, or generic `AI_AGENT` value from being mistaken for the new agent. Do not scrub credentials, provider configuration, proxy settings, or unrelated environment values.

The reference `make_aw_environment()` function below implements this with `NATIVE_ATTRIBUTION_KEYS`. This is particularly useful for tools that set a generic marker only when an outer harness has not already set it.

## Context-file schema

Suggested JSON shape:

```json
{
  "schema_version": 1,
  "run_id": "019d...",
  "invocation_id": "019d...",
  "created_at": "2026-09-01T03:20:00Z",
  "updated_at": "2026-09-01T03:20:02Z",
  "runner": {
    "name": "agy",
    "version": "0.8.0",
    "pid": 48210
  },
  "agent": {
    "tool": "opencode",
    "tool_version": "1.2.3",
    "pid": 48214,
    "pid_start": "platform-specific-start-token",
    "depth": 0,
    "launch_mode": "interactive",
    "session_id": "aw-session-id",
    "native_session_id": null,
    "requested_model": "anthropic/claude-opus-5",
    "active_model": null,
    "last_model": null,
    "provider": "openrouter",
    "variant": "high"
  },
  "native_evidence": [],
  "ended_at": null
}
```

Write this file atomically and with user-only permissions where supported. Record a process-start token as well as a PID so stale files and PID reuse can be detected. On Linux, `/proc/<pid>/stat` field 22 is suitable. With `psutil`, use `Process(pid).create_time()`.

The file is not a security boundary. Its advantages are consistency, late enrichment, debuggability, bounded data, and protection against stale environment values.

## Capturing information that is not initially available

### Session IDs

- **Codex:** Read `CODEX_THREAD_ID` in the hook, but record a conflict if the AW context or nearest agent ancestor indicates a nested Codex invocation with a different ID.
- **Claude Code:** Read `CLAUDE_CODE_SESSION_ID`. A Claude `SessionStart` hook can also update the context from hook JSON and can persist variables through `CLAUDE_ENV_FILE` when needed.
- **Gemini CLI:** A `SessionStart` hook receives `session_id` and can update `AW_CONTEXT_FILE`.
- **Hermes:** Read `HERMES_SESSION_ID`.
- **Goose:** Read `AGENT_SESSION_ID` where exported.
- **GitHub Copilot CLI:** Read `COPILOT_AGENT_SESSION_ID`.
- **Kiro:** Use an `agentSpawn` or other lifecycle hook when the selected mode supplies `session_id`. Preserve an AW session even when the native ID is absent.
- **OpenCode:** Use an OpenCode plugin/event adapter if a stable session event is available in the installed version. Do not scrape TUI output as the primary design.

### Models

Prefer information in this order:

1. Per-model-call hook or structured event, such as Gemini `BeforeModel` or Claude model-switch/session hooks.
2. Structured output from a headless runner.
3. The exact model argument selected by AW.
4. A tool configuration variable, labeled as a requested/configured hint rather than the active model.

Do not claim that `ANTHROPIC_MODEL`, `GOOSE_MODEL`, or `HERMES_MODEL` proves which model produced a particular tool call. Session switches, fallbacks, aliases, and gateways make that unsafe.

### Versions

The AW adapter should resolve the exact executable and query its version once before launch. Cache by resolved path plus file identity or modification time. Do not run arbitrary `--version` commands from every Git hook. Each adapter should own the correct version command and parser because version flags and output differ.

### PIDs

AW knows the `Popen.pid` immediately after spawning. It should atomically update the context file. On Unix, an optional tiny exec wrapper can set `AW_AGENT_PID` before replacing itself with the agent binary, but the context file avoids making correctness depend on platform-specific exec behavior.

## Detection and enforcement policy

Use these outcomes:

| Outcome | Hook behavior |
|---|---|
| AW context present and valid | Apply the AW protocol normally. |
| High-confidence native agent evidence, but no AW context | Block or redirect with precise instructions for the detected tool. |
| Medium-confidence evidence only | Warn or log during rollout; do not hard-block by default. |
| Conflicting strong evidence | Explain the conflict, log it, and use the nearest recognized process or AW declaration for guidance. Do not silently choose. |
| No agent evidence | Treat as probably human and avoid agent-specific friction. |

Recommended rollout:

1. Audit-only logging with no full environment or command capture.
2. Agent-facing warning for high-confidence bypasses.
3. Blocking only for high-confidence native evidence without AW.
4. Keep a documented human escape hatch such as `AW_HOOK_BYPASS=1`, optionally requiring a reason in a separate `AW_HOOK_BYPASS_REASON` value.

## Reference Python implementation

The following module is dependency-free on Linux. It uses `psutil` when available for stronger cross-platform ancestry and falls back to `ps` on other POSIX systems. On Windows without `psutil`, environment and context-file detection still work, while ancestry is omitted. This is preferable to launching a slow PowerShell/CIM inventory from every commit hook.

```python
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence


MAX_CONTEXT_BYTES = 64 * 1024
TRUE_VALUES = {"1", "true", "yes", "on"}
AW_MANAGED_KEYS = {
    "AW_ENV_SCHEMA_VERSION",
    "AW_AGENT",
    "AW_RUN_ID",
    "AW_INVOCATION_ID",
    "AW_RUNNER",
    "AW_RUNNER_PID",
    "AW_RUNNER_VERSION",
    "AW_AGENT_TOOL",
    "AW_AGENT_TOOL_VERSION",
    "AW_AGENT_MODEL",
    "AW_AGENT_MODEL_PROVIDER",
    "AW_AGENT_VARIANT",
    "AW_AGENT_SESSION_ID",
    "AW_AGENT_NATIVE_SESSION_ID",
    "AW_AGENT_PID",
    "AW_AGENT_DEPTH",
    "AW_AGENT_LAUNCH_MODE",
    "AW_CONTEXT_FILE",
}
NATIVE_ATTRIBUTION_KEYS = {
    "AGENT",
    "AGENT_SESSION_ID",
    "AI_AGENT",
    "OPENCODE",
    "OPENCODE_PID",
    "CODEX_THREAD_ID",
    "CLAUDECODE",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_BRIDGE_SESSION_ID",
    "GEMINI_CLI",
    "HERMES_AGENT",
    "HERMES_SESSION_ID",
    "GOOSE_TERMINAL",
    "COPILOT_AGENT_SESSION_ID",
    "TOOLBOX_ACTION",
}


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    ppid: int | None
    name: str
    executable: str | None = None
    start_token: str | None = None
    distance: int = 0


@dataclass(frozen=True)
class Evidence:
    channel: str
    tool: str | None
    signal: str
    value: str | None
    weight: int
    detail: str = ""


@dataclass
class Detection:
    agent_detected: bool
    under_aw: bool
    tool: str | None
    confidence: str
    session_id: str | None = None
    native_session_id: str | None = None
    model: str | None = None
    model_provider: str | None = None
    variant: str | None = None
    tool_version: str | None = None
    agent_pid: int | None = None
    runner: str | None = None
    runner_pid: int | None = None
    run_id: str | None = None
    invocation_id: str | None = None
    depth: int | None = None
    launch_mode: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _nonempty(env: Mapping[str, str], key: str) -> str | None:
    value = env.get(key)
    return value if value is not None and value != "" else None


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in TRUE_VALUES


def _int_or_none(value: object) -> int | None:
    try:
        return int(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def new_aw_id(prefix: str) -> str:
    maker = getattr(uuid, "uuid7", uuid.uuid4)
    return f"{prefix}-{maker()}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_aw_environment(
    *,
    base: Mapping[str, str] | None,
    context_file: Path,
    run_id: str,
    invocation_id: str,
    runner: str,
    runner_pid: int,
    agent_tool: str,
    runner_version: str | None = None,
    tool_version: str | None = None,
    model: str | None = None,
    model_provider: str | None = None,
    variant: str | None = None,
    session_id: str | None = None,
    native_session_id: str | None = None,
    agent_pid: int | None = None,
    depth: int | None = None,
    launch_mode: str | None = None,
    scrub_inherited_attribution: bool = True,
) -> dict[str, str]:
    """Build the environment AW passes to an agent process."""
    env = dict(os.environ if base is None else base)
    for key in AW_MANAGED_KEYS:
        env.pop(key, None)
    if scrub_inherited_attribution:
        for key in NATIVE_ATTRIBUTION_KEYS:
            env.pop(key, None)
    values: dict[str, object] = {
        "AW_ENV_SCHEMA_VERSION": "1",
        "AW_AGENT": "1",
        "AW_RUN_ID": run_id,
        "AW_INVOCATION_ID": invocation_id,
        "AW_RUNNER": runner,
        "AW_RUNNER_PID": runner_pid,
        "AW_AGENT_TOOL": agent_tool,
        "AW_CONTEXT_FILE": str(context_file.resolve()),
        "AW_RUNNER_VERSION": runner_version,
        "AW_AGENT_TOOL_VERSION": tool_version,
        "AW_AGENT_MODEL": model,
        "AW_AGENT_MODEL_PROVIDER": model_provider,
        "AW_AGENT_VARIANT": variant,
        "AW_AGENT_SESSION_ID": session_id,
        "AW_AGENT_NATIVE_SESSION_ID": native_session_id,
        "AW_AGENT_PID": agent_pid,
        "AW_AGENT_DEPTH": depth,
        "AW_AGENT_LAUNCH_MODE": launch_mode,
    }
    env.update({key: str(value) for key, value in values.items() if value is not None})
    return env


def write_context_atomic(path: Path, context: Mapping[str, object]) -> None:
    """Atomically write bounded, non-secret AW context."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(context, indent=2, sort_keys=True) + "\n"
    if len(payload.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise ValueError("AW context exceeds size limit")

    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            fd = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def read_aw_context(env: Mapping[str, str]) -> tuple[dict | None, str | None]:
    raw_path = _nonempty(env, "AW_CONTEXT_FILE")
    if not raw_path:
        return None, None
    path = Path(raw_path)
    try:
        if path.stat().st_size > MAX_CONTEXT_BYTES:
            return None, "AW context file exceeds size limit"
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"AW context file could not be read: {type(exc).__name__}"
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return None, "AW context schema is missing or unsupported"
    env_run_id = _nonempty(env, "AW_RUN_ID")
    if env_run_id and data.get("run_id") != env_run_id:
        return None, "AW context run_id does not match AW_RUN_ID"
    return data, None


def _linux_process_chain(pid: int, limit: int) -> list[ProcessInfo]:
    chain: list[ProcessInfo] = []
    seen: set[int] = set()
    current = pid
    for distance in range(limit):
        if current <= 0 or current in seen:
            break
        seen.add(current)
        proc = Path("/proc") / str(current)
        try:
            stat = (proc / "stat").read_text(encoding="utf-8")
            close = stat.rfind(")")
            fields = stat[close + 2 :].split()
            ppid = int(fields[1])
            start_token = fields[19]
            name = (proc / "comm").read_text(encoding="utf-8").strip()
            try:
                executable = os.readlink(proc / "exe")
            except OSError:
                executable = None
        except (OSError, ValueError, IndexError):
            break
        chain.append(ProcessInfo(current, ppid, name, executable, start_token, distance))
        current = ppid
    return chain


def _psutil_process_chain(pid: int, limit: int) -> list[ProcessInfo]:
    import psutil  # type: ignore[import-not-found]

    chain: list[ProcessInfo] = []
    current = psutil.Process(pid)
    for distance in range(limit):
        try:
            ppid = current.ppid()
            try:
                executable = current.exe()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                executable = None
            chain.append(
                ProcessInfo(
                    current.pid,
                    ppid,
                    current.name(),
                    executable,
                    str(current.create_time()),
                    distance,
                )
            )
            if ppid <= 0:
                break
            current = current.parent()
            if current is None:
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            break
    return chain


def _posix_ps_process_chain(pid: int, limit: int) -> list[ProcessInfo]:
    try:
        completed = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,comm="],
            check=True,
            capture_output=True,
            text=True,
            timeout=1.0,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    table: dict[int, tuple[int, str]] = {}
    for line in completed.stdout.splitlines():
        parts = line.strip().split(maxsplit=2)
        if len(parts) != 3:
            continue
        try:
            table[int(parts[0])] = (int(parts[1]), parts[2])
        except ValueError:
            continue
    chain: list[ProcessInfo] = []
    seen: set[int] = set()
    current = pid
    for distance in range(limit):
        if current in seen or current not in table:
            break
        seen.add(current)
        ppid, command = table[current]
        chain.append(ProcessInfo(current, ppid, Path(command).name, command, None, distance))
        current = ppid
    return chain


def process_chain(pid: int | None = None, limit: int = 16) -> list[ProcessInfo]:
    pid = os.getpid() if pid is None else pid
    try:
        return _psutil_process_chain(pid, limit)
    except (ImportError, OSError):
        pass
    if sys.platform.startswith("linux"):
        return _linux_process_chain(pid, limit)
    if os.name == "posix":
        return _posix_ps_process_chain(pid, limit)
    return []


def classify_process(proc: ProcessInfo) -> str | None:
    name = proc.name.lower().removesuffix(".exe")
    executable = (proc.executable or "").lower().replace("\\", "/")
    exact = {
        "opencode": "opencode",
        "codex": "codex",
        "claude": "claude-code",
        "gemini": "gemini",
        "hermes": "hermes",
        "goose": "goose",
        "copilot": "copilot",
        "kiro-cli": "kiro",
        "aider": "aider",
        "aider-chat": "aider",
        "amp": "amp",
    }
    if name in exact:
        return exact[name]
    if name == "agent" and "/.cursor/" in executable:
        return "cursor"
    if name in {"q", "qterm"} and any(token in executable for token in ("amazon-q", "/kiro/")):
        return "kiro"
    return None


def _add(
    evidence: list[Evidence],
    channel: str,
    tool: str | None,
    signal: str,
    value: str | None,
    weight: int,
    detail: str = "",
) -> None:
    evidence.append(Evidence(channel, tool, signal, value, weight, detail))


def detect_agent(
    env: Mapping[str, str] | None = None,
    *,
    pid: int | None = None,
    inspect_processes: bool = True,
) -> Detection:
    env = os.environ if env is None else env
    evidence: list[Evidence] = []
    conflicts: list[str] = []
    context, context_error = read_aw_context(env)
    if context_error:
        conflicts.append(context_error)

    aw_declared = _truthy(_nonempty(env, "AW_AGENT"))
    aw_tool = _nonempty(env, "AW_AGENT_TOOL")
    if aw_declared:
        _add(evidence, "aw-env", aw_tool, "AW_AGENT", "1", 100)

    context_agent = context.get("agent", {}) if isinstance(context, dict) else {}
    context_runner = context.get("runner", {}) if isinstance(context, dict) else {}
    if not isinstance(context_agent, dict):
        context_agent = {}
    if not isinstance(context_runner, dict):
        context_runner = {}
    context_tool = context_agent.get("tool") if isinstance(context_agent.get("tool"), str) else None
    if context_tool:
        _add(evidence, "aw-context", context_tool, "agent.tool", context_tool, 105)

    # Session-bearing native evidence.
    native_sessions = {
        "codex": _nonempty(env, "CODEX_THREAD_ID"),
        "claude-code": _nonempty(env, "CLAUDE_CODE_SESSION_ID"),
        "hermes": _nonempty(env, "HERMES_SESSION_ID"),
        "copilot": _nonempty(env, "COPILOT_AGENT_SESSION_ID"),
    }
    if _nonempty(env, "AGENT_SESSION_ID") and env.get("AGENT") == "goose":
        native_sessions["goose"] = env["AGENT_SESSION_ID"]
    for tool, session in native_sessions.items():
        if session:
            _add(evidence, "native-env", tool, "session", session, 92)

    # Tool-execution markers.
    if _truthy(_nonempty(env, "CLAUDE_CODE_CHILD_SESSION")):
        _add(evidence, "native-env", "claude-code", "CLAUDE_CODE_CHILD_SESSION", "1", 90)
    if env.get("HERMES_AGENT", "").lower() == "true":
        _add(evidence, "native-env", "hermes", "HERMES_AGENT", env.get("HERMES_AGENT"), 88)
    if env.get("GOOSE_TERMINAL") == "1":
        _add(evidence, "native-env", "goose", "GOOSE_TERMINAL", "1", 86)
    if env.get("GEMINI_CLI") == "1":
        _add(evidence, "native-env", "gemini", "GEMINI_CLI", "1", 86)
    if env.get("OPENCODE") == "1":
        _add(evidence, "native-env", "opencode", "OPENCODE", "1", 84)
    if env.get("AGENT") == "goose":
        _add(evidence, "native-env", "goose", "AGENT", "goose", 80)
    if env.get("TOOLBOX_ACTION") == "execute":
        _add(evidence, "native-env", "amp", "TOOLBOX_ACTION", "execute", 60,
             "Specific to an Amp toolbox execution, not every Amp shell command")

    # Broader markers.
    if env.get("CLAUDECODE") == "1":
        _add(evidence, "native-env", "claude-code", "CLAUDECODE", "1", 70)
    ai_agent = _nonempty(env, "AI_AGENT")
    if ai_agent:
        # NOTE (corrected at filing): the source mapped a Hermes `AI_AGENT` value that is not
        # present in the build measured on this machine, so only the `claude` alias is kept here.
        aliases = {"claude": "claude-code"}
        _add(evidence, "generic-env", aliases.get(ai_agent, ai_agent), "AI_AGENT", ai_agent, 65)
    if env.get("AGENT") == "1" and env.get("OPENCODE") != "1":
        _add(evidence, "generic-env", None, "AGENT", "1", 30)

    # Q terminal variables identify a terminal integration, not necessarily an agent tool call.
    if _nonempty(env, "Q_TERM") or _nonempty(env, "QTERM_SESSION_ID"):
        _add(evidence, "weak-env", "kiro", "Q_TERM/QTERM_SESSION_ID",
             _nonempty(env, "QTERM_SESSION_ID"), 35)

    ancestry: list[ProcessInfo] = []
    if inspect_processes:
        ancestry = process_chain(pid)
        for proc in ancestry:
            tool = classify_process(proc)
            if tool:
                weight = max(55, 89 - proc.distance * 3)
                _add(evidence, "process", tool, "ancestor", str(proc.pid), weight,
                     f"distance={proc.distance}, name={proc.name}")

    scores: defaultdict[str, int] = defaultdict(int)
    strongest: defaultdict[str, int] = defaultdict(int)
    for item in evidence:
        if item.tool:
            # Multiple channels help, but cap accumulation so repeated inherited markers do not dominate.
            scores[item.tool] += min(item.weight, 100)
            strongest[item.tool] = max(strongest[item.tool], item.weight)

    nearest_agent = next(
        ((proc, classify_process(proc)) for proc in ancestry if classify_process(proc)),
        None,
    )
    if context_tool:
        selected_tool = context_tool
    elif aw_tool:
        selected_tool = aw_tool
    elif nearest_agent:
        selected_tool = nearest_agent[1]
    elif scores:
        selected_tool = max(scores, key=lambda tool: (strongest[tool], scores[tool]))
    else:
        selected_tool = None

    strong_tools = sorted({item.tool for item in evidence if item.tool and item.weight >= 80})
    if len(strong_tools) > 1:
        conflicts.append("Conflicting strong tool evidence: " + ", ".join(strong_tools))

    max_weight = max((item.weight for item in evidence), default=0)
    confidence = "high" if max_weight >= 80 else "medium" if max_weight >= 50 else "low"

    context_native_session = context_agent.get("native_session_id")
    environment_native_session = native_sessions.get(selected_tool or "")
    if (
        context_native_session not in (None, "")
        and environment_native_session
        and str(context_native_session) != environment_native_session
    ):
        conflicts.append(
            "Context native_session_id disagrees with the selected tool's native environment session"
        )
    native_session = (
        str(context_native_session)
        if context_native_session not in (None, "")
        else environment_native_session
    )
    aw_session = _nonempty(env, "AW_AGENT_SESSION_ID")
    if context_agent.get("session_id") not in (None, ""):
        aw_session = str(context_agent["session_id"])

    nearest_selected = next(
        (proc for proc in ancestry if classify_process(proc) == selected_tool),
        None,
    )
    context_pid = _int_or_none(context_agent.get("pid"))
    env_pid = _int_or_none(_nonempty(env, "AW_AGENT_PID"))
    if selected_tool == "opencode" and env_pid is None:
        env_pid = _int_or_none(_nonempty(env, "OPENCODE_PID"))

    model = context_agent.get("active_model") or context_agent.get("last_model")
    model = model or context_agent.get("requested_model") or _nonempty(env, "AW_AGENT_MODEL")
    if not model and selected_tool == "goose":
        model = _nonempty(env, "GOOSE_MODEL")
    if not model and selected_tool == "hermes":
        model = _nonempty(env, "HERMES_INFERENCE_MODEL") or _nonempty(env, "HERMES_MODEL")
    if not model and selected_tool == "claude-code":
        model = _nonempty(env, "ANTHROPIC_MODEL")

    tool_version = context_agent.get("tool_version") or _nonempty(env, "AW_AGENT_TOOL_VERSION")
    runner = context_runner.get("name") or _nonempty(env, "AW_RUNNER")
    runner_pid = _int_or_none(context_runner.get("pid")) or _int_or_none(
        _nonempty(env, "AW_RUNNER_PID")
    )

    return Detection(
        agent_detected=bool(evidence),
        under_aw=aw_declared or context is not None,
        tool=selected_tool,
        confidence=confidence,
        session_id=aw_session,
        native_session_id=native_session,
        model=str(model) if model not in (None, "") else None,
        model_provider=(context_agent.get("provider") or _nonempty(env, "AW_AGENT_MODEL_PROVIDER")),
        variant=(context_agent.get("variant") or _nonempty(env, "AW_AGENT_VARIANT")),
        tool_version=str(tool_version) if tool_version not in (None, "") else None,
        agent_pid=context_pid or env_pid or (nearest_selected.pid if nearest_selected else None),
        runner=str(runner) if runner not in (None, "") else None,
        runner_pid=runner_pid,
        run_id=(context.get("run_id") if context else None) or _nonempty(env, "AW_RUN_ID"),
        invocation_id=(context.get("invocation_id") if context else None)
        or _nonempty(env, "AW_INVOCATION_ID"),
        depth=_int_or_none(context_agent.get("depth"))
        if context_agent.get("depth") is not None
        else _int_or_none(_nonempty(env, "AW_AGENT_DEPTH")),
        launch_mode=(context_agent.get("launch_mode") or _nonempty(env, "AW_AGENT_LAUNCH_MODE")),
        evidence=evidence,
        conflicts=conflicts,
    )


def commit_hook_decision(
    detection: Detection,
    *,
    guidance: str,
    env: Mapping[str, str] | None = None,
) -> tuple[bool, str | None]:
    """Return (allow, message). Block only high-confidence non-AW agent execution."""
    env = os.environ if env is None else env
    if _truthy(_nonempty(env, "AW_HOOK_BYPASS")):
        return True, None
    if detection.under_aw or not detection.agent_detected:
        return True, None
    if detection.confidence != "high":
        return True, f"Possible agent execution detected ({detection.tool or 'unknown'}); audit only."
    label = detection.tool or "an agentic tool"
    session = f", session {detection.native_session_id}" if detection.native_session_id else ""
    return False, f"Commit appears to have been invoked by {label}{session} outside AW. {guidance}"


if __name__ == "__main__":
    print(json.dumps(detect_agent().to_dict(), indent=2, sort_keys=True))
```

## AW launcher integration example

The launcher should create context before spawn, pass the environment, then add the actual PID immediately after `Popen` returns:

```python
from pathlib import Path
import os
import subprocess

run_id = new_aw_id("run")
invocation_id = new_aw_id("inv")
context_path = Path(state_root) / "invocations" / f"{invocation_id}.json"

context = {
    "schema_version": 1,
    "run_id": run_id,
    "invocation_id": invocation_id,
    "created_at": utc_now(),
    "updated_at": utc_now(),
    "runner": {"name": "agy", "version": aw_version, "pid": os.getpid()},
    "agent": {
        "tool": "opencode",
        "tool_version": opencode_version,
        "pid": None,
        "pid_start": None,
        "depth": 0,
        "launch_mode": "interactive",
        "session_id": aw_session_id,
        "native_session_id": None,
        "requested_model": selected_model,
        "active_model": None,
        "last_model": None,
        "provider": selected_provider,
        "variant": selected_variant,
    },
    "native_evidence": [],
    "ended_at": None,
}
write_context_atomic(context_path, context)

child_env = make_aw_environment(
    base=os.environ,
    context_file=context_path,
    run_id=run_id,
    invocation_id=invocation_id,
    runner="agy",
    runner_pid=os.getpid(),
    runner_version=aw_version,
    agent_tool="opencode",
    tool_version=opencode_version,
    model=selected_model,
    model_provider=selected_provider,
    variant=selected_variant,
    session_id=aw_session_id,
    depth=0,
    launch_mode="interactive",
)

process = subprocess.Popen(opencode_argv, env=child_env)
context["agent"]["pid"] = process.pid
context["updated_at"] = utc_now()
write_context_atomic(context_path, context)
exit_code = process.wait()
context["ended_at"] = utc_now()
context["updated_at"] = context["ended_at"]
write_context_atomic(context_path, context)
```

In production, put context updates behind one locked read-modify-write helper because lifecycle hooks, subagents, and the runner may update the same file concurrently. Use the repository's cross-platform locking abstraction rather than `fcntl` directly.

## Tool-specific enrichment adapters

Implement these after the base AW contract is working:

1. **Claude Code adapter:** Read `CLAUDE_CODE_SESSION_ID` directly. Use `SessionStart`, `PreModelSwitch`, and subagent hooks to update native session, active model, and depth where helpful.
2. **Gemini adapter:** Use `SessionStart` for session identity and `BeforeModel` for the actual request model. Do not update the context on every streamed `AfterModel` chunk.
3. **Kiro adapter:** Use hook JSON where session data exists, but preserve missing values in classic/headless modes rather than inventing them.
4. **OpenCode adapter:** Subscribe to stable session/model events through its plugin interface if the installed release exposes them. Keep `OPENCODE_PID` as native corroboration.
5. **Codex adapter:** Capture structured `thread.started.thread_id` from `codex exec --json` when AW owns the invocation, compare it with `CODEX_THREAD_ID`, and record any mismatch.
6. **Goose, Hermes, and Copilot:** Native variables already provide strong session attribution. Enrich model/version only from runner selection or structured events.

## Tests that should gate implementation

1. Human `git commit` with no agent evidence is not interrupted.
2. Every supported native marker is classified correctly.
3. An agent marker without AW is redirected to the AW instructions.
4. `AW_AGENT=1` plus a valid matching context is accepted.
5. A missing, oversized, malformed, or mismatched context file is reported without crashing the hook.
6. Unknown optional fields remain unset rather than becoming guessed strings.
7. Nested Codex with a stale outer `CODEX_THREAD_ID` records a conflict.
8. Nested different tools preserve both native evidence sources and prefer AW declaration or the nearest recognized ancestor.
9. OpenCode PID, context PID, and nearest ancestor disagreements are visible.
10. PID reuse is rejected when a stored start token does not match the live process.
11. Model switches update the context file without pretending that launch-time environment variables changed.
12. Concurrent context updates are atomic and do not lose fields.
13. Windows without `psutil` degrades to environment/context detection without delay or failure.
14. The hook never logs secrets, full environment contents, prompts, or unrestricted command lines.
15. `AW_HOOK_BYPASS=1` works for a human and is visible in audit metadata if auditing is enabled.

## Conclusions

The native environment ecosystem is better than it first appeared. Claude Code now has both a precise child-execution marker and a current session variable. Hermes and Goose intentionally support attribution. Gemini has a precise shell marker plus rich hooks. GitHub Copilot CLI exports a session ID. Codex and OpenCode offer strong, useful signals.

It is still not consistent enough to serve as AW's primary contract. AW should own normalized identity and preserve native evidence alongside it. The combination of `AW_*` launch variables, an atomically updated per-invocation context file, native markers, and ancestry fallback should capture almost every cooperative agent while keeping false positives low for humans.

## Primary sources

- OpenCode source setting `AGENT`, `OPENCODE`, and `OPENCODE_PID`: <https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/index.ts>
- Codex nested `CODEX_THREAD_ID` report: <https://github.com/openai/codex/issues/15527>
- Codex `AI_AGENT=codex` proposal and current Codex-specific-signal statement: <https://github.com/openai/codex/issues/36883>
- Claude Code environment-variable reference: <https://code.claude.com/docs/en/env-vars>
- Claude Code hook reference: <https://code.claude.com/docs/en/hooks>
- Gemini CLI shell environment marker: <https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/shell.md>
- Gemini CLI hook reference: <https://geminicli.com/docs/hooks/reference/>
- Hermes Agent environment-variable reference: <https://hermes-agent.nousresearch.com/docs/reference/environment-variables>
- Goose environment-variable reference: <https://github.com/aaif-goose/goose/blob/main/documentation/docs/guides/environment-variables.md>
- GitHub Copilot CLI changelog: <https://github.com/github/copilot-cli/blob/main/changelog.md>
- Kiro missing-session hook report across modes: <https://github.com/kirodotdev/Kiro/issues/8430>
- Amp toolbox execution contract: <https://ampcode.com/news/toolboxes>
- Cursor Agent CLI configuration reference: <https://cursor.com/docs/cli/reference/configuration.md>
