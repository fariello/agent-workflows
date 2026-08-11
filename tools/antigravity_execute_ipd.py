#!/usr/bin/env python3
"""Execute an AW IPD with the Antigravity CLI, then audit the result.

Run this script from anywhere inside the target repository. The IPD argument
may be a repository-relative path, a filename, or the plan's six-character
stable ID. The script runs two headless ``agy`` turns and writes their streaming event
logs under the repository's ignored ``tmp/antigravity/`` directory:

1. execute the pending IPD; and
2. resume that exact conversation and perform a skeptical self-audit.

By default, the first turn continues the most recent Antigravity conversation
for the current repository. If no conversation exists, Antigravity creates a
new one. Pass ``--session-id`` to select a particular conversation instead.
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


# Durable, version-controlled prompt files that raise the diligence bar for the
# Antigravity/Gemini executor (see the awphysical orchestration lessons). If a file is
# missing, the tool falls back to a built-in default so it still runs.
_PROMPT_DIR = Path(__file__).resolve().parent / "awphysical"
_EXECUTION_PREAMBLE_FILE = _PROMPT_DIR / "agy-execution-preamble.md"
_SELF_AUDIT_PROMPT_FILE = _PROMPT_DIR / "agy-self-audit-prompt.md"


def _strip_html_comments(text: str) -> str:
    """Remove leading HTML-comment metadata blocks so only the prompt body is sent."""
    return re.sub(r"<!--.*?-->\s*", "", text, flags=re.S).strip()


def _load_prompt_file(path: Path) -> str | None:
    """Return the prompt body from a durable prompt file, or None if unavailable."""
    try:
        return _strip_html_comments(path.read_text(encoding="utf-8"))
    except OSError:
        return None


@dataclass(frozen=True)
class AgyResult:
    """The fields this workflow requires from an ``agy`` JSON result."""

    conversation_id: str
    response: str
    status: str


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute a pending AW IPD in Antigravity, wait for completion, "
            "then run a skeptical self-audit in the same session."
        )
    )
    parser.add_argument(
        "ipd",
        help="IPD path, filename, or six-character stable plan ID",
    )
    parser.add_argument(
        "--session-id",
        "--conversation-id",
        dest="session_id",
        help=(
            "Existing Antigravity conversation ID. If omitted, use "
            "ANTIGRAVITY_CONVERSATION_ID when set; otherwise continue the "
            "current project's most recent conversation or create a new one."
        ),
    )
    parser.add_argument(
        "--agy",
        dest="agy_executable",
        help="Path to the agy executable (default: find agy on PATH)",
    )
    parser.add_argument(
        "--timeout",
        default="120m",
        help="Maximum time for each Antigravity turn (default: 120m)",
    )
    parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help=(
            "Allow Antigravity to execute every requested tool without review. "
            "Prefer scoped permissions in Antigravity settings when practical."
        ),
    )
    return parser.parse_args(argv)


def repository_root(start: Path) -> Path:
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
        if (candidate / ".agents" / "plans").is_dir():
            return candidate
    raise ScriptError(
        "Run this command from inside a repository containing .agents/plans/."
    )


def _candidate_plans(root: Path, states: Iterable[str]) -> list[Path]:
    found: list[Path] = []
    for state in states:
        directory = root / ".agents" / "plans" / state
        if directory.is_dir():
            found.extend(sorted(directory.glob("*.md")))
    return found


def _is_id6(value: str) -> bool:
    return len(value) == 6 and value.isalnum() and value.lower() == value


def resolve_ipd(root: Path, value: str, states: Iterable[str]) -> Path:
    supplied = Path(value)
    direct = supplied if supplied.is_absolute() else root / supplied
    if direct.is_file():
        resolved = direct.resolve()
        plans_root = (root / ".agents" / "plans").resolve()
        try:
            relative = resolved.relative_to(plans_root)
        except ValueError as exc:
            raise ScriptError(f"IPD must be under {plans_root}: {resolved}") from exc
        if not relative.parts or relative.parts[0] not in states:
            state_text = ", ".join(states)
            raise ScriptError(
                f"IPD {resolved} is not in an allowed plan state: {state_text}."
            )
        return resolved

    candidates = _candidate_plans(root, states)
    if value.endswith(".md") or "/" in value or "\\" in value:
        matches = [path for path in candidates if path.name == supplied.name]
    elif _is_id6(value):
        matches = [path for path in candidates if f"-{value}-" in path.name]
    else:
        matches = [path for path in candidates if path.name == value]

    if not matches:
        state_text = ", ".join(states)
        raise ScriptError(
            f"No IPD matching {value!r} found in plan states: {state_text}."
        )
    if len(matches) > 1:
        rendered = "\n".join(f"  - {path.relative_to(root)}" for path in matches)
        raise ScriptError(f"IPD reference {value!r} is ambiguous:\n{rendered}")
    return matches[0].resolve()


def stable_id_from_filename(path: Path) -> str:
    match = re.match(r"^\d{8}-[^-]+-\d{2}-([a-z0-9]{6})-", path.name)
    if match is None:
        raise ScriptError(
            f"Cannot determine the six-character plan ID from {path.name}."
        )
    return match.group(1)


def relative_posix(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def resolve_agy(explicit_path: str | None) -> str:
    """Return an executable ``agy`` path or raise an actionable error."""
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


def run_agy(
    *,
    executable: str,
    root: Path,
    prompt: str,
    session_id: str | None,
    timeout: str,
    skip_permissions: bool,
) -> AgyResult:
    """Run one headless Antigravity turn, persist its stream, and validate it.

    Antigravity emits newline-delimited events with ``stream-json``. Every
    event is flushed to an ignored log below ``tmp/antigravity/``, allowing
    another terminal to follow a long-running turn without attaching to or
    disrupting the conversation. The terminal ``result`` event supplies the
    same fields previously read from the single JSON response.
    """
    command = [
        executable,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--print-timeout",
        timeout,
    ]
    if session_id:
        command.extend(("--conversation", session_id))
    else:
        command.append("--continue")
    if skip_permissions:
        command.append("--dangerously-skip-permissions")

    log_directory = root / "tmp" / "antigravity"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / f"agy-{os.getpid()}-{time.time_ns()}.jsonl"
    print(f"Antigravity event stream: {log_path}", file=sys.stderr, flush=True)

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
    with log_path.open("w", encoding="utf-8") as stream:
        for line in process.stdout:
            stream.write(line)
            stream.flush()
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "result" and isinstance(event.get("result"), dict):
                payload = event["result"]

    returncode = process.wait()
    if payload is None:
        raise ScriptError(
            f"Antigravity emitted no terminal result event (exit {returncode}); "
            f"inspect {log_path}."
        )

    status = str(payload.get("status", ""))
    error = str(payload.get("error", "")).strip()
    if returncode != 0 or status != "SUCCESS":
        detail = error or f"inspect {log_path}"
        raise ScriptError(
            f"Antigravity ended with status {status or 'UNKNOWN'} "
            f"(exit {returncode}): {detail}"
        )

    conversation_id = str(payload.get("conversation_id", "")).strip()
    if not conversation_id:
        raise ScriptError("Antigravity succeeded but returned no conversation_id.")
    return AgyResult(
        conversation_id=conversation_id,
        response=str(payload.get("response", "")),
        status=status,
    )


def audit_prompt(ipd_path: str) -> str:
    durable = _load_prompt_file(_SELF_AUDIT_PROMPT_FILE)
    if durable is not None:
        return durable.replace("{IPD_PATH}", ipd_path)
    return f"""Perform a skeptical post-execution audit of this executed Implementation Plan Document:

`{ipd_path}`

Assume your prior implementation may be incomplete, superficially compliant, or based on mistaken assumptions. Do not trust your prior checkmarks, status changes, workflow history, summaries, commit messages, memory, or claims that tests passed. Treat them only as assertions requiring independent evidence.

Determine whether the implementation actually fulfills the IPD's intent, objectives, scope, every `E-*` execution item, every `V-*` validation item, safety requirements, integration obligations, and controlling specification.

Do not search for defects merely to produce findings. Do not fabricate issues, reinterpret clear requirements unreasonably, or recommend unnecessary redesign. A finding is valid only when supported by concrete repository evidence.

Required procedure:

1. Read `AGENTS.md` and every applicable repository instruction governing IPDs, validation, corrective work, commits, and executed plans.
2. Re-read the entire IPD and its controlling specification and decisions. Reconstruct the intended behavior, safety properties, interfaces, serialized fields, fail-closed cases, and downstream dependencies before judging the implementation.
3. Identify the commits and files that purportedly executed the IPD. Inspect their actual diffs and the current code. Do not infer implementation from filenames or commit messages.
4. Build an evidence table with exactly one row for every `E-*` and every `V-*`. Include the precise requirement, files and symbols inspected, relevant tests, commands actually run, result (`satisfied`, `partially satisfied`, `not satisfied`, or `not independently verifiable`), and reasoning.
5. Trace each required behavior end to end through schema, implementation, CLI or workflow surface, serialization, error behavior, and tests. Look specifically for shallow tests, mocked-away behavior, missing negative cases, hidden fallback paths, side effects in read-only operations, duplicated policy vocabulary, and integrations that bypass the intended shared API.
6. Run every required validation command yourself and any additional focused test needed to prove a requirement. Record actual output and exit status. Prior output is not evidence.
7. Evaluate diligence, precision, accuracy, thoroughness, fail-closed safety, completeness of integration, and strength of evidence against the IPD's intent, not merely the presence of code.
8. Classify substantiated gaps as HIGH, MEDIUM, or LOW based on actual impact. Fix every safely correctable in-scope gap. Follow repository scope and commit rules. Do not rewrite an executed IPD if repository instructions require a corrective IPD.
9. After corrections, re-run focused and complete validation, applicable IPD lint, plan-index, parity, leak, and formatting checks. Inspect the final diff and prove each finding resolved without unrelated changes.
10. If a fix exceeds scope, conflicts with an approved specification, requires a human decision, or requires unavailable authority, stop that part and report the exact blocker instead of inventing policy.

Report back with:

- Verdict: `CONFORMING`, `CONFORMING AFTER CORRECTIONS`, or `NOT CONFORMING`
- Reconstructed intent and objectives
- Complete E/V evidence table
- Substantiated findings and evidence
- Fixes made, files and symbols changed, and why
- Validation commands with actual results
- Remaining blockers or unverifiable claims
- Final diff and commit summary
- An explicit statement that you did not invent findings to satisfy this skeptical-review instruction

The audit is incomplete until every E-item and V-item has an evidence-backed disposition. "The code looks right," your prior memory, prior checkmarks, and a generally green test suite are insufficient evidence."""


def main(argv: Iterable[str] | None = None) -> int:
    """Resolve the IPD, execute it, audit it, and print both agent reports."""
    try:
        return run(argv)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except ScriptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def run(argv: Iterable[str] | None = None) -> int:
    """Implement the command after top-level exception handling."""
    args = parse_args(argv)
    root = repository_root(Path.cwd())
    pending = resolve_ipd(root, args.ipd, ("pending",))
    plan_id = stable_id_from_filename(pending)
    pending_rel = relative_posix(root, pending)

    executable = resolve_agy(args.agy_executable)
    initial_session = args.session_id or os.environ.get("ANTIGRAVITY_CONVERSATION_ID")

    print(f"Executing {pending_rel} in Antigravity...", file=sys.stderr, flush=True)
    preamble = _load_prompt_file(_EXECUTION_PREAMBLE_FILE)
    execute_instruction = f"read and execute `{pending_rel}`"
    execute_prompt = (
        f"{preamble}\n\n{execute_instruction}" if preamble else execute_instruction
    )
    execution = run_agy(
        executable=executable,
        root=root,
        prompt=execute_prompt,
        session_id=initial_session,
        timeout=args.timeout,
        skip_permissions=args.dangerously_skip_permissions,
    )
    print("\n=== Antigravity execution report ===\n")
    print(execution.response.rstrip())

    # A successful IPD lifecycle normally moves the plan from pending to executed.
    # Prefer the executed location, but audit the pending copy when execution did
    # not move it. Resolving states separately also avoids false ambiguity if a
    # broken execution accidentally leaves copies in both locations.
    try:
        audited = resolve_ipd(root, plan_id, ("executed",))
    except ScriptError:
        audited = resolve_ipd(root, plan_id, ("pending",))
    audited_rel = relative_posix(root, audited)

    print(f"Auditing {audited_rel} in the same session...", file=sys.stderr, flush=True)
    audit = run_agy(
        executable=executable,
        root=root,
        prompt=audit_prompt(audited_rel),
        # Always pin the second turn to the ID returned by the first. This avoids
        # a race with any other process that changes the project's latest session.
        session_id=execution.conversation_id,
        timeout=args.timeout,
        skip_permissions=args.dangerously_skip_permissions,
    )
    print("\n=== Antigravity self-audit report ===\n")
    print(audit.response.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
