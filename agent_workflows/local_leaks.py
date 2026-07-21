#!/usr/bin/env python3
"""Detect "local leaks": identifying info that must not live in a public artifact.

Secret scanners (gitleaks, git-secrets) hunt credential SHAPES; they do NOT flag a
maintainer's home path, username, other local accounts, private sibling-repo names,
hostnames, or captured session ids. This module is the shippable engine behind that
distinct check (DECISIONS D92 introduced the one-off guard; D93 promoted it here).

Surfaces fed by this one engine (P8 single source of truth):
- the ``aw check-local-leaks`` CLI subcommand,
- the pre-commit hook (``python -m agent_workflows check-local-leaks``),
- the ``tests/test_local_leaks.py`` regression guard,
- the interactive ``/assess local-leaks`` lens.

Severity split (D93 / plan OQ3):
- ``fail``  patterns fail the non-interactive gate (pre-commit + CI): STRUCTURAL patterns
  (home paths, the maintainer's local-checkout dir style, session ids), the curated
  repo-committed allowlist misses, and the user-level personal hints.
- ``warn``  patterns are ADVISORY only (auto-derived from the environment): surfaced by the
  interactive lens for a human to confirm, but never fail CI (kept deterministic).

Scan modes: working tree (default, tracked files via ``git ls-files``), git history
(``git log -p -U0`` added lines, bounded), and a built wheel (zip entries).

Sensitive literals are ASSEMBLED FROM FRAGMENTS so this source never contains a plain
copy of a leak token (keeps the module off its own leak list and immune to a
history-rewrite replace-map). Stdlib only (zero runtime deps).

Exit code (CLI): 0 = clean, 1 = fail-severity leak(s), 2 = usage/environment error.
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# --- Fragment-assembled sensitive literals ---------------------------------------------------
# Never write these tokens as plain substrings; assemble them so this file is self-clean.
_H = "gfa" + "riello"  # the maintainer's username fragment
_ACCT = (
    "test_" + "user_1"
)  # a second local account used in the cross-user security test
_R1 = "her" + "mes-agent"
_R2 = "uri" + "-ai-info"
_R3 = "rho" + "dy-pact"
_VC = "~/" + "VC"
_EMAIL = _H + "@fariel.com"  # the PUBLIC author email (allowed)
_REMOTE = (
    "git@github.com:fa" + "riello/agent-workflows.git"
)  # PUBLIC repo origin (allowed)

# --- Structural + curated patterns (severity: fail) ------------------------------------------
# These fail the non-interactive gate. Conservative and specific to avoid false positives.
_FAIL_PATTERNS: dict[str, re.Pattern[str]] = {
    # Any user's real POSIX home dir. Generic doc placeholders (u, alice, user, USER, <...>) allowed.
    "home-path": re.compile(r"/home/(?!u/|alice/|user/|USER/|<)[A-Za-z0-9._-]+"),
    # macOS home dirs.
    "users-path": re.compile(r"/Users/(?!<|user/)[A-Za-z0-9._-]+"),
    # Windows home dirs (C:\Users\<name>), both slash forms.
    "windows-home": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!<)[A-Za-z0-9._-]+"),
    # The maintainer's local-checkout dir style.
    "vc-home": re.compile(re.escape(_VC) + r"(?:/|\b)"),
    # Private / sibling repo names that must never appear in tracked files.
    "private-repo": re.compile(
        r"\b(?:" + "|".join(map(re.escape, (_R1, _R2, _R3))) + r")\b"
    ),
    # A second local account used in the security test.
    "other-account": re.compile(r"\b" + re.escape(_ACCT) + r"\b"),
    # Real captured session ids (opencode `ses_` + a long token). `ses_<redacted>` is allowed.
    "session-id": re.compile(r"\bses_(?!<redacted>)[0-9A-Za-z]{8,}"),
    # A bare maintainer handle that is NOT the public author email/remote.
    "handle": re.compile(re.escape(_H) + r"(?!@fariel\.com)"),
}

# Line-level allowlist: if a matched LINE contains any of these public identifiers, ignore it.
_ALLOWED_LINE_SUBSTRINGS: tuple[str, ...] = (
    _EMAIL,  # public author email
    _REMOTE,  # public repo origin
    "/home/u/src",  # documented portable example in config.py docstring
    "/home/alice/data",  # test fixture
)

# Paths (repo-relative) exempt from scanning: files that assemble leak fragments at runtime.
_ALLOWED_PATHS: frozenset[str] = frozenset(
    {
        "tests/test_packaging.py",
        "tests/test_local_leaks.py",
    }
)

# The load-bearing PUBLIC package/repo name is never a leak on its own.
_PACKAGE_NAME = "agent-workflows"


@dataclass
class Finding:
    location: str  # "path:line" or "commit:path:line" or "wheel:entry"
    rule: str
    severity: str  # "fail" | "warn"
    snippet: str


@dataclass
class Ruleset:
    """The compiled patterns used for a scan, split by severity."""

    fail: dict[str, re.Pattern[str]] = field(default_factory=dict)
    warn: dict[str, re.Pattern[str]] = field(default_factory=dict)
    allow_line_substrings: tuple[str, ...] = ()


# --- Config: repo-committed allowlist + user-level hints -------------------------------------
# The repo allowlist (public-OK-here, travels + CI-deterministic) lives at
# .agents/local-leaks-allowlist.toml. The user hints (personal, never committed) live at
# <config_dir>/local-leaks-hints.json. Neither is required; both are additive.
REPO_ALLOWLIST_REL = ".agents/local-leaks-allowlist.toml"
USER_HINTS_FILENAME = "local-leaks-hints.json"


def _parse_simple_toml_lists(text: str) -> dict[str, list[str]]:
    """Minimal TOML reader for flat ``key = ["a", "b"]`` arrays (3.9-safe, no tomllib).

    Only the shapes this allowlist needs are supported: string arrays, one per key, values
    may span lines. Comments (``#``) and other keys are ignored. This avoids a dependency on
    tomllib (3.11+) while the support floor is 3.9.
    """
    result: dict[str, list[str]] = {}
    # Join into one string; find `key = [ ... ]` blocks.
    for m in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*\[(.*?)\]", text, re.DOTALL):
        key = m.group(1)
        body = m.group(2)
        values = re.findall(r"""["']([^"']*)["']""", body)
        result[key] = values
    return result


def load_repo_allowlist(repo_root: Path) -> dict[str, list[str]]:
    """Read the repo-committed allowlist TOML; return {} if absent/unreadable."""
    p = repo_root / REPO_ALLOWLIST_REL
    try:
        return _parse_simple_toml_lists(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def load_user_hints() -> dict[str, list[str]]:
    """Read the never-committed user hints JSON from the config dir; {} if absent.

    Resolved via the same XDG-aware dir as the rest of the tool config. This file is NOT
    part of config.json (which drops unknown keys and stores no sensitive data, D46/R-5).
    """
    import json

    try:
        from . import config as _config

        cfg_dir = _config.config_dir()
    except Exception:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        cfg_dir = Path(base).expanduser() / "agent-workflows"
    p = Path(cfg_dir) / USER_HINTS_FILENAME
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, list[str]] = {}
    for k, v in data.items():
        if isinstance(v, list):
            out[k] = [str(x) for x in v]
    return out


def derive_warn_tokens(repo_root: Path) -> dict[str, str]:
    """Auto-derive advisory (warn-only) personal tokens from the environment.

    Every source is OPTIONAL and cross-platform: a missing value yields no token (never an
    error). Returns {token: reason}. These NEVER fail the gate; the lens surfaces them.
    """
    tokens: dict[str, str] = {}

    def add(val: str | None, reason: str) -> None:
        if val and len(val) >= 3 and val not in (_PACKAGE_NAME,):
            tokens[val] = reason

    # Home dir basename.
    try:
        add(Path.home().name, "current $HOME basename")
    except Exception:
        pass
    # Username (POSIX $USER, Windows $USERNAME).
    add(os.environ.get("USER"), "$USER")
    add(os.environ.get("USERNAME"), "$USERNAME")
    # Git identity (optional; may be unset in CI).
    for key, why in (("user.name", "git user.name"), ("user.email", "git user.email")):
        try:
            out = subprocess.run(
                ["git", "-C", str(repo_root), "config", "--get", key],
                capture_output=True,
                text=True,
                check=False,
            )
            add(out.stdout.strip() or None, why)
        except Exception:
            pass
    # Hostname.
    try:
        add(socket.gethostname() or None, "hostname")
    except Exception:
        pass
    # Sibling directory names of the repo (the local-checkout layout).
    try:
        parent = repo_root.resolve().parent
        for sib in parent.iterdir():
            if sib.is_dir() and sib.name != repo_root.name:
                add(sib.name, "sibling checkout dir name")
    except Exception:
        pass
    return tokens


def build_ruleset(
    repo_root: Path,
    *,
    include_warn: bool = False,
) -> Ruleset:
    """Assemble the active ruleset: structural fail patterns + curated allowlist + hints,
    and (when include_warn) the advisory auto-derived tokens as warn patterns."""
    rs = Ruleset(
        fail=dict(_FAIL_PATTERNS), allow_line_substrings=_ALLOWED_LINE_SUBSTRINGS
    )

    # Curated repo allowlist: extra fail patterns + extra allowed line substrings.
    repo_cfg = load_repo_allowlist(repo_root)
    extra_allow = tuple(repo_cfg.get("allow_line_substrings", []))
    if extra_allow:
        rs.allow_line_substrings = rs.allow_line_substrings + extra_allow
    for i, pat in enumerate(repo_cfg.get("fail_patterns", [])):
        try:
            rs.fail[f"repo-pattern-{i}"] = re.compile(pat)
        except re.error:
            continue

    # User hints (personal, never committed): additional fail patterns (literal tokens).
    hints = load_user_hints()
    for i, tok in enumerate(hints.get("tokens", [])):
        if tok:
            rs.fail[f"user-hint-{i}"] = re.compile(re.escape(tok))
    for i, pat in enumerate(hints.get("patterns", [])):
        try:
            rs.fail[f"user-pattern-{i}"] = re.compile(pat)
        except re.error:
            continue

    if include_warn:
        for tok, _reason in derive_warn_tokens(repo_root).items():
            rs.warn[f"derived:{tok}"] = re.compile(re.escape(tok))

    return rs


# --- Text scanning core ----------------------------------------------------------------------
def scan_text(
    text: str,
    location_prefix: str,
    ruleset: Ruleset,
    *,
    include_warn: bool = False,
) -> list[Finding]:
    """Scan text line-by-line against the ruleset; return findings."""
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if any(sub in line for sub in ruleset.allow_line_substrings):
            continue
        for rule, pat in ruleset.fail.items():
            if pat.search(line):
                findings.append(
                    Finding(
                        f"{location_prefix}:{lineno}", rule, "fail", line.strip()[:120]
                    )
                )
        if include_warn:
            for rule, pat in ruleset.warn.items():
                if pat.search(line):
                    findings.append(
                        Finding(
                            f"{location_prefix}:{lineno}",
                            rule,
                            "warn",
                            line.strip()[:120],
                        )
                    )
    return findings


# --- Scan modes ------------------------------------------------------------------------------
def _tracked_files(repo_root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def scan_working_tree(repo_root: Path, *, include_warn: bool = False) -> list[Finding]:
    ruleset = build_ruleset(repo_root, include_warn=include_warn)
    findings: list[Finding] = []
    for rel in _tracked_files(repo_root):
        if rel in _ALLOWED_PATHS:
            continue
        try:
            text = (repo_root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings.extend(scan_text(text, rel, ruleset, include_warn=include_warn))
    return findings


def scan_history(
    repo_root: Path, *, max_commits: int | None = None, include_warn: bool = False
) -> list[Finding]:
    """Scan added lines across git history via `git log -p -U0`. Bounded by max_commits."""
    ruleset = build_ruleset(repo_root, include_warn=include_warn)
    cmd = ["git", "-C", str(repo_root), "log", "-p", "-U0", "--no-color"]
    if max_commits:
        cmd += [f"-n{max_commits}"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    findings: list[Finding] = []
    commit = ""
    path = ""
    for line in out.stdout.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1][:10]
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            added = line[1:]
            if any(sub in added for sub in ruleset.allow_line_substrings):
                continue
            for rule, pat in ruleset.fail.items():
                if pat.search(added):
                    findings.append(
                        Finding(f"{commit}:{path}", rule, "fail", added.strip()[:120])
                    )
            if include_warn:
                for rule, pat in ruleset.warn.items():
                    if pat.search(added):
                        findings.append(
                            Finding(
                                f"{commit}:{path}", rule, "warn", added.strip()[:120]
                            )
                        )
    return findings


def scan_wheel(
    wheel_path: Path, repo_root: Path, *, include_warn: bool = False
) -> list[Finding]:
    """Scan the entries of a built wheel/zip for leak tokens."""
    ruleset = build_ruleset(repo_root, include_warn=include_warn)
    findings: list[Finding] = []
    z = zipfile.ZipFile(wheel_path)
    for name in z.namelist():
        try:
            text = z.read(name).decode("utf-8", "replace")
        except Exception:
            continue
        # For binary-ish content there are no line numbers that matter; scan lines anyway.
        for f in scan_text(
            text, f"{wheel_path.name}!{name}", ruleset, include_warn=include_warn
        ):
            findings.append(f)
    return findings


# --- CLI -------------------------------------------------------------------------------------
def run(
    repo_root: Path,
    *,
    history: bool = False,
    max_commits: int | None = None,
    wheel: Path | None = None,
    include_warn: bool = False,
) -> tuple[list[Finding], list[Finding]]:
    """Run the requested scan; return (fail_findings, warn_findings)."""
    findings: list[Finding] = []
    if wheel is not None:
        findings = scan_wheel(wheel, repo_root, include_warn=include_warn)
    elif history:
        findings = scan_history(
            repo_root, max_commits=max_commits, include_warn=include_warn
        )
    else:
        findings = scan_working_tree(repo_root, include_warn=include_warn)
    fails = [f for f in findings if f.severity == "fail"]
    warns = [f for f in findings if f.severity == "warn"]
    return fails, warns


def main(argv: list[str] | None = None) -> int:
    import argparse

    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="check-local-leaks",
        description="Detect identifying info (paths, usernames, private repo names, hostnames, "
        "session ids) that must not appear in a public artifact.",
    )
    parser.add_argument("dir", nargs="?", default=".", help="Repo root (default: cwd).")
    parser.add_argument(
        "--history", action="store_true", help="Scan git history (bounded)."
    )
    parser.add_argument(
        "--max-commits", type=int, default=None, help="Bound --history to N commits."
    )
    parser.add_argument(
        "--wheel", default=None, help="Scan a built wheel/zip at this path."
    )
    parser.add_argument(
        "--warn",
        action="store_true",
        help="Also report advisory auto-derived candidates.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.dir).resolve()
    wheel = Path(args.wheel).resolve() if args.wheel else None
    try:
        fails, warns = run(
            repo_root,
            history=args.history,
            max_commits=args.max_commits,
            wheel=wheel,
            include_warn=args.warn,
        )
    except subprocess.CalledProcessError:
        print(
            "check-local-leaks: not a git repository or git unavailable",
            file=sys.stderr,
        )
        return 2
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"check-local-leaks: {exc}", file=sys.stderr)
        return 2

    if warns:
        print(
            "Advisory (auto-derived) candidates - confirm via /assess local-leaks:",
            file=sys.stderr,
        )
        for w in warns:
            print(f"  [warn] {w.location}: {w.rule}: {w.snippet}", file=sys.stderr)
    if fails:
        print("Local-leak(s) found:", file=sys.stderr)
        for f in fails:
            print(f"  {f.location}: {f.rule}: {f.snippet}", file=sys.stderr)
        print(
            "\nRemove or abstract these (portable placeholder / repo-relative path), "
            "or add a justified entry to .agents/local-leaks-allowlist.toml if genuinely public.",
            file=sys.stderr,
        )
        return 1
    # Positive confirmation on the clean path so a passing run is not silent
    # (assess-self-documentation S4). One line to stderr, always.
    print("No local leaks found.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
