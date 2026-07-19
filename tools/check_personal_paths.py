#!/usr/bin/env python3
"""Guard: fail if any TRACKED file embeds a personal-path / identity leak (D92).

`agent-workflows` is a publicly published package with a public repo. Tracked files must
not embed the maintainer's local filesystem layout, usernames, other local accounts, or
private repo names. This scanner is the durable regression guard behind the one-time
cleanup: it runs in a pre-commit hook and in `tests/test_no_personal_paths.py`.

It scans TRACKED CONTENT ONLY (via `git ls-files`), so untracked scratch (e.g. an
out-of-repo plan copy) and gitignored files are never scanned. Matches are reported with
`path:line`. An explicit allowlist covers legitimate public identifiers.

Exit code: 0 = clean, 1 = leak(s) found, 2 = usage/environment error.

This module has no third-party dependencies (stdlib only), matching the framework's
zero-runtime-dependency stance.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# --- Leak patterns ---------------------------------------------------------------------------
# Each is a compiled regex. Keep these conservative and specific so the guard does not produce
# false positives on ordinary prose; the allowlist below carves out the known-good exceptions.
PATTERNS: dict[str, re.Pattern[str]] = {
    # Any user's real home dir. Generic doc placeholders (u, alice, user, USER, <...>) are allowed.
    "home-path": re.compile(r"/home/(?!u/|alice/|user/|USER/|<)[A-Za-z0-9._-]+"),
    # macOS home dirs.
    "users-path": re.compile(r"/Users/(?!<|user/)[A-Za-z0-9._-]+"),
    # The maintainer's local checkout layout.
    "vc-home": re.compile(r"a local checkout dir(?:/|\b)"),
    # Private / sibling repo names that must never appear in tracked files.
    "private-repo": re.compile(r"\b(?:a-reference-agent|a-private-repo|a-consuming-repo)\b"),
    # A second local account used in the security test.
    "other-account": re.compile(r"\bvictim-user\b"),
    # Real captured session ids (opencode `ses_` + a long token). `ses_<redacted>` is allowed.
    "session-id": re.compile(r"\bses_(?!<redacted>)[0-9A-Za-z]{8,}"),
    # A bare `attacker-user` handle that is NOT the public author email and NOT the public remote URL.
    "handle": re.compile(r"attacker-user(?!@fariel\.com)"),
}

# --- Allowlist -------------------------------------------------------------------------------
# (substring) exceptions: if a matched LINE contains any of these, the match on that line is
# ignored. These are legitimate, public, load-bearing identifiers.
ALLOWED_LINE_SUBSTRINGS: tuple[str, ...] = (
    "gfariello@fariel.com",  # public author email (pyproject.toml, CITATION.cff, CHANGELOG)
    "git@github.com:fariello/agent-workflows.git",  # public repo origin (OQ5)
    "/home/u/src",  # documented portable example in config.py docstring
    "/home/alice/data",  # test fixture
)

# Path globs (relative to repo root) that are entirely exempt (this guard's own definition and
# tests necessarily name the tokens). Keep this list minimal and explicit.
ALLOWED_PATHS: tuple[str, ...] = (
    "tools/check_personal_paths.py",
    "tests/test_no_personal_paths.py",
    "tests/test_packaging.py",  # constructs leak tokens at runtime to assert the wheel is clean
)


def tracked_files(repo_root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def scan(repo_root: Path) -> list[str]:
    """Return a list of `path:line: <rule>` violation strings (empty when clean)."""
    violations: list[str] = []
    for rel in tracked_files(repo_root):
        if rel in ALLOWED_PATHS:
            continue
        p = repo_root / rel
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # binary or unreadable; skip
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(allowed in line for allowed in ALLOWED_LINE_SUBSTRINGS):
                continue
            for rule, pat in PATTERNS.items():
                if pat.search(line):
                    violations.append(f"{rel}:{lineno}: {rule}: {line.strip()[:120]}")
    return violations


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    repo_root = Path(argv[0]).resolve() if argv else Path.cwd()
    try:
        violations = scan(repo_root)
    except subprocess.CalledProcessError:
        print(
            "check_personal_paths: not a git repository or git unavailable",
            file=sys.stderr,
        )
        return 2
    if violations:
        print(
            "Personal-path / identity leak(s) found in tracked files (D92):",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(
            "\nRemove or abstract these (portable placeholder / repo-relative path), "
            "or add a justified allowlist entry if genuinely public.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
