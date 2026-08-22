#!/usr/bin/env python3
"""Unified multi-mode runner and skeptical validator for Antigravity (Gemini 3.7 Flash High).

Execute IPDs, author IPDs from specs, run prompt files, or execute raw prompts
using the Antigravity CLI, enforcing an automated two-turn skeptical validation
protocol to eliminate greenwashing and unverified completion claims.

Run this script from anywhere inside the target repository.

Supported execution modes:
  1. IPD Mode (--ipd): Executes a pending Implementation Plan Document (IPD),
     then performs a skeptical post-execution audit in the same conversation session.
  2. Spec Mode (--spec): Authors a conformant IPD from a specification document using
     repository IPD tooling, then performs a completeness and conformance audit.
  3. File Mode (--file / -f): Executes an external prompt file (e.g. under .agents/prompts/),
     then verifies task execution in the same session.
  4. Prompt Mode (--prompt / -p): Executes an inline prompt string (matching agy -c -p ergonomics),
     then verifies task execution in the same session.

Session continuity and isolation:
  - By default, Turn 1 resumes the project's most recent conversation session (--continue).
  - Pass --session-id / -s / -c to attach to a specific conversation ID.
  - Pass --new-session / -n to force a fresh, clean-slate session without inheriting context.
  - Turn 2 always runs in the exact session returned by Turn 1.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class ScriptError(RuntimeError):
    """A user-actionable script failure."""


_DEFAULT_MODEL = "gemini-3.7-flash-high"

_PROMPT_DIR = Path(__file__).resolve().parent / "awphysical"
_IPD_EXECUTION_PREAMBLE_FILE = _PROMPT_DIR / "agy-execution-preamble.md"
_IPD_SELF_AUDIT_PROMPT_FILE = _PROMPT_DIR / "agy-self-audit-prompt.md"
_SPEC_PREAMBLE_FILE = _PROMPT_DIR / "agy-spec-preamble.md"
_SPEC_AUDIT_PROMPT_FILE = _PROMPT_DIR / "agy-spec-audit-prompt.md"
_GENERAL_PREAMBLE_FILE = _PROMPT_DIR / "agy-general-preamble.md"
_GENERAL_AUDIT_PROMPT_FILE = _PROMPT_DIR / "agy-general-audit-prompt.md"


def _strip_html_comments(text: str) -> str:
    """Remove leading HTML-comment metadata blocks so only the prompt body is sent."""
    return re.sub(r"<!--.*?-->\s*", "", text, flags=re.S).strip()


def _load_prompt_file(path: Path) -> str | None:
    """Return the prompt body from a prompt file, or None if unavailable."""
    try:
        return _strip_html_comments(path.read_text(encoding="utf-8"))
    except OSError:
        return None


@dataclass(frozen=True)
class AgyResult:
    """Fields required from an agy stream-json execution result."""

    conversation_id: str
    response: str
    status: str


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agy_run.py",
        description=(
            "Unified multi-mode runner and skeptical validator for Antigravity (Gemini 3.7 Flash High).\n"
            "Runs a primary task turn with calibrated diligence framing, followed automatically by\n"
            "an evidence-backed skeptical validation turn in the same conversation session."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""EXAMPLES AND USAGE:

  1. Execute a pending IPD by 6-character ID or path (with 2-turn skeptical audit):
     python3 tools/agy_run.py 7cvh9t
     python3 tools/agy_run.py .agents/plans/pending/20260816-awphysical-15-7cvh9t-fresh-install-aw-target.md
     python3 tools/agy_run.py --ipd 7cvh9t

  2. Generate an IPD from a specification document:
     python3 tools/agy_run.py --spec .agents/docs/specs/20260810-1447-01-physical-aw-hierarchy.spec.md

  3. Execute an external prompt brief file:
     python3 tools/agy_run.py --file .agents/prompts/local/task-brief.md
     python3 tools/agy_run.py -f .agents/prompts/local/task-brief.md

  4. Run an inline prompt string (matching agy -c -p ergonomics):
     python3 tools/agy_run.py -p "refactor installer error handling in engine.py"
     python3 tools/agy_run.py --prompt "add unit tests for resolve_target_layout"

  5. Session continuity and isolation controls:
     python3 tools/agy_run.py -s 12345-67890 -p "fix the remaining edge cases"
     python3 tools/agy_run.py --new-session 7cvh9t
     python3 tools/agy_run.py --no-audit -p "quick exploratory lookup"

STREAMING LOGS AND MONITORING:
  Each turn flushes all stream-json events to tmp/antigravity/agy-<pid>-<timestamp>.jsonl.
  Monitor execution in another terminal using:
     tail -f tmp/antigravity/agy-<pid>-<timestamp>.jsonl
""",
    )

    # Positional target (optional; auto-detected if mode flags not passed)
    parser.add_argument(
        "target",
        nargs="?",
        help="Target IPD path/id6, spec path, prompt file path, or raw prompt text.",
    )

    # Explicit mode selectors
    mode_group = parser.add_argument_group(
        "Execution Modes (optional if target is auto-detectable)"
    )
    mode_group.add_argument(
        "--ipd",
        dest="ipd_target",
        metavar="IPD",
        help="Execute a pending IPD by path, filename, or 6-char stable ID.",
    )
    mode_group.add_argument(
        "--spec",
        dest="spec_target",
        metavar="SPEC",
        help="Generate a conformant IPD from a specification document.",
    )
    mode_group.add_argument(
        "--file",
        "-f",
        dest="file_target",
        metavar="FILE",
        help="Execute an external prompt file.",
    )
    mode_group.add_argument(
        "--prompt",
        "-p",
        dest="prompt_target",
        metavar="TEXT",
        help="Execute an inline prompt string.",
    )

    # Session management
    session_group = parser.add_argument_group("Session Continuity and Isolation")
    session_group.add_argument(
        "--session-id",
        "--conversation-id",
        "--conversation",
        "-s",
        "-c",
        dest="session_id",
        help=(
            "Existing Antigravity conversation ID to resume. If omitted, uses "
            "ANTIGRAVITY_CONVERSATION_ID if set, otherwise continues the project's "
            "latest conversation."
        ),
    )
    session_group.add_argument(
        "--continue",
        "-C",
        dest="continue_session",
        action="store_true",
        default=True,
        help="Continue the project's most recent conversation (default: True).",
    )
    session_group.add_argument(
        "--new-session",
        "-n",
        dest="new_session",
        action="store_true",
        help="Force a clean-slate session without inheriting prior context.",
    )
    session_group.add_argument(
        "--list-sessions",
        "-l",
        dest="list_sessions",
        action="store_true",
        help="List available Antigravity sessions for this workspace and exit.",
    )

    # Runtime options
    runtime_group = parser.add_argument_group("Runtime and Model Options")
    runtime_group.add_argument(
        "--model",
        dest="model",
        default=_DEFAULT_MODEL,
        help=f"Antigravity model ID (default: {_DEFAULT_MODEL}).",
    )
    runtime_group.add_argument(
        "--timeout",
        default="240m",
        help="Maximum timeout for each Antigravity turn (default: 240m).",
    )
    runtime_group.add_argument(
        "--agy",
        dest="agy_executable",
        help="Path to the agy executable (default: find agy on PATH).",
    )
    runtime_group.add_argument(
        "--dangerous",
        "--dangerously-skip-permissions",
        "--danger",
        "-d",
        dest="dangerous",
        action="store_true",
        help=(
            "Run agy with --dangerously-skip-permissions for all calls "
            "(auto-approves tool execution without interactive confirmation)."
        ),
    )
    runtime_group.add_argument(
        "--add-dir",
        dest="add_dirs",
        action="append",
        default=[],
        metavar="DIR",
        help="Add an external directory to the workspace (passed to agy --add-dir; repeatable).",
    )

    # Workflow controls
    flow_group = parser.add_argument_group("Validation and Turn Controls")
    flow_group.add_argument(
        "--no-audit",
        action="store_true",
        help="Execute Turn 1 only without running the Turn-2 skeptical validation audit.",
    )
    flow_group.add_argument(
        "--audit-only",
        action="store_true",
        help="Execute Turn-2 skeptical audit only on an existing conversation session.",
    )

    return parser.parse_args(argv)


def repository_root(start: Path) -> Path:
    """Locate the git or workspace root."""
    completed = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return Path(completed.stdout.strip()).resolve()

    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".agents" / "plans").is_dir() or (candidate / ".aw").is_dir():
            return candidate
    raise ScriptError(
        "Run this command from inside a repository with an agent-workflows layout."
    )


def _candidate_plans(root: Path, states: Iterable[str]) -> list[Path]:
    found: list[Path] = []
    for state in set(states):
        for plans_base in (
            root / ".agents" / "plans" / state,
            root / ".aw" / "records" / "plans" / state,
        ):
            if plans_base.is_dir():
                found.extend(plans_base.glob("*.md"))
    return sorted(set(found))


def _is_id6(value: str) -> bool:
    return len(value) == 6 and value.isalnum() and value.lower() == value


def resolve_ipd(root: Path, value: str, states: Iterable[str]) -> Path:
    """Resolve an IPD reference (path, filename, or ID6) within allowed lifecycle states."""
    supplied = Path(value)
    direct = supplied if supplied.is_absolute() else root / supplied
    if direct.is_file():
        resolved = direct.resolve()
        # Verify it is under a plans directory
        plans_roots = [
            (root / ".agents" / "plans").resolve(),
            (root / ".aw" / "records" / "plans").resolve(),
        ]
        matched_state = False
        for pr in plans_roots:
            try:
                rel = resolved.relative_to(pr)
                if rel.parts and rel.parts[0] in states:
                    matched_state = True
                    break
            except ValueError:
                continue
        if not matched_state:
            state_text = ", ".join(states)
            raise ScriptError(
                f"IPD {resolved} is not in an allowed plan state: {state_text}."
            )
        return resolved

    candidates = _candidate_plans(root, states)
    if value.endswith(".md") or "/" in value or "\\" in value:
        matches = [p for p in candidates if p.name == supplied.name]
    elif _is_id6(value):
        matches = [p for p in candidates if f"-{value}-" in p.name]
    else:
        matches = [p for p in candidates if p.name == value]

    if not matches:
        state_text = ", ".join(states)
        raise ScriptError(
            f"No IPD matching {value!r} found in plan states: {state_text}."
        )
    if len(matches) > 1:
        rendered = "\n".join(f"  - {p.relative_to(root)}" for p in matches)
        raise ScriptError(f"IPD reference {value!r} is ambiguous:\n{rendered}")
    return matches[0].resolve()


def resolve_spec(root: Path, value: str) -> Path:
    """Resolve a specification document path."""
    supplied = Path(value)
    direct = supplied if supplied.is_absolute() else root / supplied
    if direct.is_file():
        return direct.resolve()

    # Search common specs directories
    candidates: list[Path] = []
    for d in (root / ".agents" / "docs" / "specs", root / ".aw" / "records" / "specs"):
        if d.is_dir():
            candidates.extend(d.glob("*.md"))
    candidates = sorted(set(candidates))

    matches = [p for p in candidates if p.name == supplied.name or value in p.name]
    if not matches:
        raise ScriptError(f"No specification matching {value!r} found.")
    if len(matches) > 1:
        rendered = "\n".join(f"  - {p.relative_to(root)}" for p in matches)
        raise ScriptError(
            f"Specification reference {value!r} is ambiguous:\n{rendered}"
        )
    return matches[0].resolve()


def resolve_prompt_file(root: Path, value: str) -> Path:
    """Resolve an external prompt brief file."""
    supplied = Path(value)
    direct = supplied if supplied.is_absolute() else root / supplied
    if direct.is_file():
        return direct.resolve()
    raise ScriptError(f"Prompt file not found: {value}")


def stable_id_from_filename(path: Path) -> str:
    match = re.match(r"^\d{8}-[^-]+-\d{2}-([a-z0-9]{6})-", path.name)
    if match is None:
        raise ScriptError(f"Cannot determine six-character plan ID from {path.name}.")
    return match.group(1)


def relative_posix(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def resolve_agy(explicit_path: str | None) -> str:
    """Return an executable agy path or raise an actionable error."""
    if explicit_path:
        candidate = Path(explicit_path).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        raise ScriptError(f"The --agy path is not executable: {candidate}")

    discovered = shutil.which("agy")
    if discovered:
        return discovered
    raise ScriptError(
        "Cannot find 'agy' on PATH. Install Antigravity CLI or pass --agy PATH."
    )


def _compact(value: object, limit: int = 180) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _is_test_command(command: str) -> bool:
    return (
        re.search(
            r"(?:^|\s)(?:pytest|py\.test|unittest|tox|nox|cargo\s+test|"
            r"go\s+test|npm\s+(?:run\s+)?test|pnpm\s+(?:run\s+)?test|"
            r"yarn\s+(?:run\s+)?test)(?:\s|$)",
            command,
            flags=re.I,
        )
        is not None
    )


def _progress_messages(event: dict[str, object], phase: str) -> list[tuple[str, str]]:
    event_type = str(event.get("event", ""))
    if event_type == "init":
        return [("init", f"[{phase}] Antigravity initialized")]

    if event_type == "result":
        result = event.get("result")
        status = (
            str(result.get("status", "UNKNOWN"))
            if isinstance(result, dict)
            else "UNKNOWN"
        )
        return [(f"result:{status}", f"[{phase}] completed: {status}")]

    if event_type != "step_update":
        return []
    step = event.get("step_update")
    if not isinstance(step, dict):
        return []

    step_index = str(step.get("step_index", "?"))
    state = str(step.get("state", "")).upper()
    state_word = {
        "ACTIVE": "started",
        "DONE": "finished",
        "ERROR": "failed",
        "CANCELED": "canceled",
    }.get(state, state.lower() or "updated")
    messages: list[tuple[str, str]] = []

    tool = step.get("tool_info")
    if isinstance(tool, dict):
        name = _compact(tool.get("name", "tool"), 60)
        parameters = tool.get("parameters")
        command = ""
        if isinstance(parameters, dict):
            candidate = parameters.get("command", parameters.get("cmd", ""))
            if isinstance(candidate, list):
                command = " ".join(str(part) for part in candidate)
            else:
                command = str(candidate)
        if command:
            kind = "tests" if _is_test_command(command) else "command"
            message = f"[{phase}] {kind} {state_word}: {_compact(command)}"
        else:
            message = f"[{phase}] tool {state_word}: {name}"
        messages.append((f"step:{step_index}:{state}:tool:{name}", message))

    subagent = step.get("subagent_info")
    if isinstance(subagent, dict):
        subagents = subagent.get("subagents")
        count = len(subagents) if isinstance(subagents, list) else 1
        noun = "subagent" if count == 1 else "subagents"
        messages.append(
            (
                f"step:{step_index}:{state}:subagents:{count}",
                f"[{phase}] {count} {noun} {state_word}",
            )
        )

    step_type = str(step.get("step_type", ""))
    if not messages and step_type == "agent_response" and state == "DONE":
        messages.append(
            (
                f"step:{step_index}:agent-response",
                f"[{phase}] agent response finished",
            )
        )
    return messages


def run_agy(
    *,
    executable: str,
    root: Path,
    prompt: str,
    phase: str,
    session_id: str | None,
    use_continue: bool,
    timeout: str,
    skip_permissions: bool,
    add_dirs: list[str] | None = None,
    model: str | None = None,
) -> AgyResult:
    """Run one headless Antigravity turn, persist its stream, and validate output."""
    command = [
        executable,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--print-timeout",
        timeout,
    ]
    if model:
        command.extend(("--model", model))
    if session_id:
        command.extend(("--conversation", session_id))
    elif use_continue:
        command.append("--continue")
    if skip_permissions:
        command.append("--dangerously-skip-permissions")
    if add_dirs:
        for d in add_dirs:
            command.extend(("--add-dir", str(d)))

    log_directory = root / "tmp" / "antigravity"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / f"agy-{os.getpid()}-{time.time_ns()}.jsonl"
    print(
        f"[{phase}] Antigravity turn started. Event stream logged to:",
        file=sys.stderr,
        flush=True,
    )
    print(f"  tail -f {log_path}", file=sys.stderr, flush=True)

    process = subprocess.Popen(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    if process.stdout is None:
        process.kill()
        raise ScriptError("Antigravity stdout stream was not available.")

    payload: dict[str, object] | None = None
    reported: set[str] = set()
    with log_path.open("w", encoding="utf-8") as stream:
        for line in process.stdout:
            stream.write(line)
            stream.flush()
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            for key, message in _progress_messages(event, phase):
                if key not in reported:
                    print(message, file=sys.stderr, flush=True)
                    reported.add(key)
            if event.get("event") == "result" and isinstance(event.get("result"), dict):
                payload = event["result"]

    returncode = process.wait()
    if payload is None:
        raise ScriptError(
            f"Antigravity emitted no terminal result event (exit {returncode}); inspect {log_path}."
        )

    status = str(payload.get("status", ""))
    error = str(payload.get("error", "")).strip()
    if returncode != 0 or status != "SUCCESS":
        detail = error or f"inspect {log_path}"
        raise ScriptError(
            f"Antigravity ended with status {status or 'UNKNOWN'} (exit {returncode}): {detail}"
        )

    conversation_id = str(payload.get("conversation_id", "")).strip()
    if not conversation_id:
        raise ScriptError("Antigravity succeeded but returned no conversation_id.")
    return AgyResult(
        conversation_id=conversation_id,
        response=str(payload.get("response", "")),
        status=status,
    )


def build_turn1_prompt(mode: str, target: str) -> str:
    """Build the calibrated Turn-1 prompt for the selected mode."""
    if mode == "ipd":
        preamble = _load_prompt_file(_IPD_EXECUTION_PREAMBLE_FILE)
        instruction = f"read and execute `{target}`"
        return f"{preamble}\n\n{instruction}" if preamble else instruction
    elif mode == "spec":
        preamble = _load_prompt_file(_SPEC_PREAMBLE_FILE)
        instruction = (
            f"Author a conformant Implementation Plan Document (IPD) from specification `{target}`. "
            f"Use `aw ipd scaffold`, assign IDs with `aw ipd sync`, and verify with `aw ipd lint`."
        )
        return f"{preamble}\n\n{instruction}" if preamble else instruction
    elif mode == "file":
        preamble = _load_prompt_file(_GENERAL_PREAMBLE_FILE)
        instruction = f"read and execute `{target}`"
        return f"{preamble}\n\n{instruction}" if preamble else instruction
    else:  # prompt
        preamble = _load_prompt_file(_GENERAL_PREAMBLE_FILE)
        return f"{preamble}\n\n{target}" if preamble else target


def build_turn2_prompt(mode: str, target: str, extra: str = "") -> str:
    """Build the calibrated Turn-2 skeptical audit prompt for the selected mode."""
    if mode == "ipd":
        durable = _load_prompt_file(_IPD_SELF_AUDIT_PROMPT_FILE)
        if durable is not None:
            return durable.replace("{IPD_PATH}", target)
        return f"Perform a skeptical post-execution audit of executed IPD: `{target}`."
    elif mode == "spec":
        durable = _load_prompt_file(_SPEC_AUDIT_PROMPT_FILE)
        if durable is not None:
            prompt = durable.replace("{IPD_PATH}", target)
            return prompt.replace("{SPEC_PATH}", extra)
        return f"Perform a skeptical completeness audit of IPD `{target}` against spec `{extra}`."
    else:  # file or prompt
        durable = _load_prompt_file(_GENERAL_AUDIT_PROMPT_FILE)
        if durable is not None:
            return durable
        return "Perform a skeptical verification of the task completed in this session."


def resolve_mode_and_target(
    root: Path, args: argparse.Namespace
) -> tuple[str, str, str]:
    """Determine the active mode, resolved target, and secondary metadata."""
    if args.ipd_target:
        ipd_path = resolve_ipd(
            root,
            args.ipd_target,
            ("pending", "executed" if args.audit_only else "pending"),
        )
        return "ipd", relative_posix(root, ipd_path), ""
    if args.spec_target:
        spec_path = resolve_spec(root, args.spec_target)
        return "spec", relative_posix(root, spec_path), ""
    if args.file_target:
        file_path = resolve_prompt_file(root, args.file_target)
        return "file", relative_posix(root, file_path), ""
    if args.prompt_target:
        return "prompt", args.prompt_target, ""

    # Auto-detection from positional target
    if not args.target:
        raise ScriptError("No target specified. Pass an IPD, spec, file, or prompt.")

    target_str = args.target.strip()
    target_path = Path(target_str)
    direct = target_path if target_path.is_absolute() else root / target_path

    if direct.is_file():
        if target_str.endswith(".spec.md"):
            return "spec", relative_posix(root, direct), ""
        if (
            ".agents/plans" in direct.as_posix()
            or ".aw/records/plans" in direct.as_posix()
        ):
            return "ipd", relative_posix(root, direct), ""
        return "file", relative_posix(root, direct), ""

    # Try IPD resolution by ID or pending name
    try:
        ipd_path = resolve_ipd(
            root, target_str, ("pending", "executed" if args.audit_only else "pending")
        )
        return "ipd", relative_posix(root, ipd_path), ""
    except ScriptError:
        pass

    # Try spec resolution
    try:
        spec_path = resolve_spec(root, target_str)
        return "spec", relative_posix(root, spec_path), ""
    except ScriptError:
        pass

    # Fallback: treat positional string as inline prompt
    return "prompt", target_str, ""


def main(argv: Iterable[str] | None = None) -> int:
    try:
        return run(argv)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except ScriptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = repository_root(Path.cwd())

    if args.list_sessions:
        import agy_sessions

        return agy_sessions.main([str(root)])

    executable = resolve_agy(args.agy_executable)
    mode, target_rel, extra = resolve_mode_and_target(root, args)

    # Session setup
    initial_session = args.session_id or os.environ.get("ANTIGRAVITY_CONVERSATION_ID")
    use_continue = (
        False if args.new_session else (True if not initial_session else False)
    )

    execution_session_id = initial_session

    if not args.audit_only:
        print(
            f"Executing [{mode} mode] {target_rel} in Antigravity...",
            file=sys.stderr,
            flush=True,
        )
        turn1_prompt = build_turn1_prompt(mode, target_rel)
        execution = run_agy(
            executable=executable,
            root=root,
            prompt=turn1_prompt,
            phase="execution",
            session_id=initial_session,
            use_continue=use_continue,
            timeout=args.timeout,
            skip_permissions=args.dangerous,
            add_dirs=args.add_dirs,
            model=args.model,
        )
        print("\n=== Antigravity Execution Report ===\n")
        print(execution.response.rstrip())
        execution_session_id = execution.conversation_id

    if args.no_audit:
        return 0

    # Prepare audited target for Turn 2
    audited_target = target_rel
    audit_extra = extra
    if mode == "ipd":
        # Resolve executed copy if moved during turn 1
        plan_id = stable_id_from_filename(root / target_rel)
        try:
            audited = resolve_ipd(root, plan_id, ("executed",))
        except ScriptError:
            audited = resolve_ipd(root, plan_id, ("pending",))
        audited_target = relative_posix(root, audited)
    elif mode == "spec":
        audit_extra = target_rel

    print(
        f"\nAuditing [{mode} mode] in the same session...", file=sys.stderr, flush=True
    )
    turn2_prompt = build_turn2_prompt(mode, audited_target, audit_extra)
    audit = run_agy(
        executable=executable,
        root=root,
        prompt=turn2_prompt,
        phase="audit",
        session_id=execution_session_id,
        use_continue=False,  # Always use exact conversation ID for turn 2
        timeout=args.timeout,
        skip_permissions=args.dangerous,
        add_dirs=args.add_dirs,
        model=args.model,
    )
    print("\n=== Antigravity Skeptical Audit Report ===\n")
    print(audit.response.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
