#!/usr/bin/env python3
"""Execute an AW IPD with Antigravity, then make it audit its own work.

This script targets the Antigravity session bridge API:

    import antigravity
    agent = antigravity.get_agent(conversation_id="...")
    result = agent.execute("...")

Run it from anywhere inside the target repository. The IPD argument may be a
repository-relative path, a filename, or the plan's six-character stable ID.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import inspect
import os
from pathlib import Path
import re
import subprocess
import sys
import sysconfig
from typing import Any, Iterable


PLAN_STATES = ("pending", "executed")


class ScriptError(RuntimeError):
    """A user-actionable script failure."""


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
            "ANTIGRAVITY_CONVERSATION_ID, then the bridge's current project "
            "session, or lease a new session for the repository."
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
            resolved.relative_to(plans_root)
        except ValueError as exc:
            raise ScriptError(f"IPD must be under {plans_root}: {resolved}") from exc
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


def load_session_bridge() -> Any:
    spec = importlib.util.find_spec("antigravity")
    if spec is None or spec.origin is None:
        raise ScriptError(
            "No Antigravity session bridge is importable in this Python environment."
        )
    stdlib_module = Path(sysconfig.get_path("stdlib")) / "antigravity.py"
    if Path(spec.origin).resolve() == stdlib_module.resolve():
        raise ScriptError(
            "Python resolves 'antigravity' to its unrelated standard-library novelty "
            f"module at {spec.origin}. Run the script in the Antigravity environment "
            "that provides the session bridge used by your get_agent/execute example."
        )
    module = importlib.import_module("antigravity")
    if callable(getattr(module, "get_agent", None)):
        return module
    origin = getattr(module, "__file__", "unknown location")
    raise ScriptError(
        "The imported 'antigravity' module does not provide get_agent(). "
        f"Imported: {origin}. This is commonly Python's unrelated standard-library "
        "antigravity module. Run the script in the Antigravity environment that "
        "provides the session bridge used by your get_agent/execute example."
    )


def get_project_agent(bridge: Any, root: Path, session_id: str | None) -> Any:
    selected_session = session_id or os.environ.get("ANTIGRAVITY_CONVERSATION_ID")
    if selected_session:
        return bridge.get_agent(conversation_id=selected_session)

    # The supplied bridge contract is expected to bind a no-argument call to the
    # current project, selecting its most recent session or creating one. Run from
    # the repository root so that project discovery has an unambiguous cwd.
    os.chdir(root)
    try:
        agent = bridge.get_agent()
    except TypeError:
        agent = None
    if agent is not None:
        return agent

    lease_agent = getattr(bridge, "lease_agent", None)
    if callable(lease_agent):
        agent = lease_agent(workspace=str(root))
        if agent is not None:
            return agent

    raise ScriptError(
        "No current project session was available and this bridge could not lease "
        "a new one. Pass --session-id or set ANTIGRAVITY_CONVERSATION_ID."
    )


async def maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def wait_for_completion(value: Any) -> Any:
    """Wait for common blocking, async, or job-handle execute results."""
    value = await maybe_await(value)

    wait = getattr(value, "wait", None)
    if callable(wait):
        waited = await maybe_await(wait())
        if waited is not None:
            value = waited

    result = getattr(value, "result", None)
    if callable(result):
        completed = await maybe_await(result())
        if completed is not None:
            value = completed
    return value


async def execute_and_wait(agent: Any, prompt: str) -> Any:
    execute = getattr(agent, "execute", None)
    if not callable(execute):
        raise ScriptError("The selected Antigravity agent does not provide execute().")
    return await wait_for_completion(execute(prompt))


async def result_text(value: Any) -> str:
    if value is None:
        return ""
    text_member = getattr(value, "text", None)
    if callable(text_member):
        rendered = await maybe_await(text_member())
        return str(rendered)
    if text_member is not None:
        return str(text_member)
    output_text = getattr(value, "output_text", None)
    if output_text is not None:
        return str(output_text)
    return str(value)


def audit_prompt(ipd_path: str) -> str:
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


async def async_main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = repository_root(Path.cwd())
    pending = resolve_ipd(root, args.ipd, ("pending",))
    plan_id = stable_id_from_filename(pending)
    pending_rel = relative_posix(root, pending)

    bridge = load_session_bridge()
    agent = get_project_agent(bridge, root, args.session_id)

    print(f"Executing {pending_rel} in Antigravity...", file=sys.stderr, flush=True)
    await execute_and_wait(agent, f"read and execute `{pending_rel}`")

    # A successful IPD lifecycle normally moves the plan from pending to executed.
    # Resolve it again rather than assuming the first filename or disposition.
    audited = resolve_ipd(root, plan_id, ("executed", "pending"))
    audited_rel = relative_posix(root, audited)

    print(f"Auditing {audited_rel} in the same session...", file=sys.stderr, flush=True)
    audit_result = await execute_and_wait(agent, audit_prompt(audited_rel))
    print(await result_text(audit_result))
    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except ScriptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
