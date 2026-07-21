#!/usr/bin/env python3
"""Interactive configuration wizard for the leak-sanitizer (DECISIONS D98).

This is the interactive surface that authors the leak-sanitizer's two config files without a
human hand-writing TOML/JSON. The SCHEMA and the atomic writers live in ``leak_sanitizer``
(one module owns read AND write); this module only orchestrates the interview, so the engine
module stays scan-focused.

The core ``configure()`` takes INJECTED ``prompt`` and ``confirm`` callables so tests can drive
it without touching stdin (mirroring ``leak_sanitizer.fix_working_tree(confirm=...)``). The CLI
layer supplies real stdin-backed callables.

Stdlib only (zero runtime deps).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import leak_sanitizer as ls

# A prompt returns the user's line for a question (already stripped by the caller is fine).
PromptFn = Callable[[str], str]
# A confirm returns True/False for a yes/no question.
ConfirmFn = Callable[[str], bool]


@dataclass
class ConfigState:
    """The full editable config across both files."""

    allow_line_substrings: list[str]
    fail_patterns: list[str]
    ip_enabled: bool
    hostname_fail: bool
    tokens: list[str]
    patterns: list[str]

    def copy(self) -> "ConfigState":
        return ConfigState(
            list(self.allow_line_substrings),
            list(self.fail_patterns),
            self.ip_enabled,
            self.hostname_fail,
            list(self.tokens),
            list(self.patterns),
        )


def load_state(repo_root: Path) -> ConfigState:
    """Read the current config from disk into a ConfigState (safe defaults when absent)."""
    lists = ls.load_repo_allowlist(repo_root)
    bools = ls.load_repo_config_bools(repo_root)
    hints = ls.load_user_hints()
    return ConfigState(
        allow_line_substrings=list(lists.get("allow_line_substrings", [])),
        fail_patterns=list(lists.get("fail_patterns", [])),
        ip_enabled=bool(bools.get("ip_enabled", False)),
        hostname_fail=bool(bools.get("hostname_fail", False)),
        tokens=list(hints.get("tokens", [])),
        patterns=list(hints.get("patterns", [])),
    )


def _edit_list(
    label: str,
    current: list[str],
    prompt: PromptFn,
    emit: Callable[[str], None],
) -> list[str]:
    """Add/remove/keep loop for a list-valued control (the ``aw setup`` blank-to-finish idiom).

    Enter (blank) finishes; ``-<value>`` removes an existing value; any other line adds a value.
    Returns the new list (order preserved, de-duplicated on add).
    """
    values = list(current)
    emit(f"{label} (current: {values if values else 'none'})")
    emit("  blank to finish; '-<value>' to remove; any other text adds a value.")
    while True:
        entry = prompt(f"  {label}> ").strip()
        if not entry:
            break
        if entry.startswith("-"):
            target = entry[1:]
            if target in values:
                values.remove(target)
                emit(f"  removed: {target}")
            else:
                emit(f"  not present: {target}")
            continue
        if entry in values:
            emit(f"  already present: {entry}")
            continue
        # Reject unrepresentable values interactively (both quote chars) instead of at write.
        try:
            ls._toml_quote(entry)
        except ls.ConfigValueError as exc:
            emit(f"  cannot store this value: {exc}")
            continue
        values.append(entry)
        emit(f"  added: {entry}")
    return values


def _ask_bool(
    label: str,
    current: bool,
    consequence: str,
    confirm: ConfirmFn,
    emit: Callable[[str], None],
) -> bool:
    emit(f"{label} (current: {'on' if current else 'off'}). {consequence}")
    return confirm(f"  Enable {label}?")


def _diff_lines(before: ConfigState, after: ConfigState) -> list[str]:
    """Human-readable diff of the two states (only changed fields)."""
    out: list[str] = []

    def line_list(name: str, a: list[str], b: list[str]) -> None:
        if a != b:
            out.append(f"  {name}:")
            for v in a:
                if v not in b:
                    out.append(f"    - {v}")
            for v in b:
                if v not in a:
                    out.append(f"    + {v}")

    def line_bool(name: str, a: bool, b: bool) -> None:
        if a != b:
            out.append(f"  {name}: {'on' if a else 'off'} -> {'on' if b else 'off'}")

    line_list(
        "allow_line_substrings",
        before.allow_line_substrings,
        after.allow_line_substrings,
    )
    line_list("fail_patterns", before.fail_patterns, after.fail_patterns)
    line_bool("ip_enabled", before.ip_enabled, after.ip_enabled)
    line_bool("hostname_fail", before.hostname_fail, after.hostname_fail)
    line_list("user tokens (personal, never committed)", before.tokens, after.tokens)
    line_list(
        "user patterns (personal, never committed)", before.patterns, after.patterns
    )
    return out


def configure(
    repo_root: Path,
    *,
    prompt: PromptFn,
    confirm: ConfirmFn,
    emit: Optional[Callable[[str], None]] = None,
) -> dict:
    """Interactively edit the leak-sanitizer config; write only on confirmation.

    ``prompt(question) -> str`` and ``confirm(question) -> bool`` are injected so this is
    testable without stdin. ``emit(line)`` prints guidance (defaults to ``print``).

    Returns a summary dict: ``{"changed": bool, "wrote": [paths], "diff": [lines]}``. The survey
    itself never writes; only the confirmed final step calls the writers. Re-running with no
    changes writes nothing (idempotent).
    """
    if emit is None:
        emit = print

    before = load_state(repo_root)
    after = before.copy()

    emit(
        "Leak-sanitizer configuration. Edit each control; nothing is written until you confirm."
    )
    emit("")
    emit("Repo allowlist (tracked, travels with the repo):")
    after.allow_line_substrings = _edit_list(
        "allow_line_substrings", after.allow_line_substrings, prompt, emit
    )
    after.fail_patterns = _edit_list("fail_patterns", after.fail_patterns, prompt, emit)
    after.ip_enabled = _ask_bool(
        "ip_enabled",
        after.ip_enabled,
        "IP matching is noisy and rarely identifying; loopback/private ranges are never flagged. Default off.",
        confirm,
        emit,
    )
    after.hostname_fail = _ask_bool(
        "hostname_fail",
        after.hostname_fail,
        "Promotes the derived hostname from advisory warn to a hard FAIL; a shared CI-runner hostname could then fail builds. Default off (warn-only).",
        confirm,
        emit,
    )
    emit("")
    emit("Personal hints (never committed; stored in your user config dir):")
    after.tokens = _edit_list("tokens", after.tokens, prompt, emit)
    after.patterns = _edit_list("patterns", after.patterns, prompt, emit)

    diff = _diff_lines(before, after)
    if not diff:
        emit("No changes; nothing to write.")
        return {"changed": False, "wrote": [], "diff": []}

    emit("")
    emit("Proposed changes:")
    for line in diff:
        emit(line)

    if not confirm("Write these changes?"):
        emit("Declined; nothing was written.")
        return {"changed": True, "wrote": [], "diff": diff}

    wrote: list[str] = []
    repo_changed = (
        before.allow_line_substrings != after.allow_line_substrings
        or before.fail_patterns != after.fail_patterns
        or before.ip_enabled != after.ip_enabled
        or before.hostname_fail != after.hostname_fail
    )
    hints_changed = before.tokens != after.tokens or before.patterns != after.patterns
    if repo_changed:
        p = ls.write_repo_allowlist(
            repo_root,
            allow_line_substrings=after.allow_line_substrings,
            fail_patterns=after.fail_patterns,
            ip_enabled=after.ip_enabled,
            hostname_fail=after.hostname_fail,
        )
        wrote.append(str(p))
    if hints_changed:
        p = ls.write_user_hints(tokens=after.tokens, patterns=after.patterns)
        wrote.append(str(p))
    emit("Wrote: " + ", ".join(wrote))
    return {"changed": True, "wrote": wrote, "diff": diff}
