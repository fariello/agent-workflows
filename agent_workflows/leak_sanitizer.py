#!/usr/bin/env python3
"""Unified leak-sanitizer engine: detect (``--check``) and optionally rewrite (``--fix``)
identifying info that must not live in a public artifact.

This is the single deterministic source of truth (P8) behind every leak surface:
- the ``aw check-local-leaks`` CLI subcommand (and the broader ``aw sanitize`` alias),
- the pre-commit hook,
- the ``tests/test_local_leaks.py`` / ``tests/test_leak_sanitizer.py`` regression guards,
- the interactive ``/assess local-leaks`` lens.

It supersedes and absorbs the D92/D93 ``local_leaks`` detection engine (which now
re-exports from here) and folds in the peer ideas contributed by pubrun's
``sanitize_paths.py``: an opt-in ``--fix`` rewrite, hostname derivation, an
off-by-default IP ruleset, a staged-blob scan mode for the hook, and a layered config.
Credit: pubrun for ``--fix`` / hostname / off-by-default-IP / layered-config.

Severity split (D93, preserved):
- ``fail`` patterns fail the non-interactive gate (pre-commit + CI): STRUCTURAL patterns
  (home paths, the maintainer's local-checkout dir style, session ids, private repo
  names) plus curated repo-committed and user-level entries.
- ``warn`` patterns are ADVISORY only (auto-derived from the environment: hostname,
  ``$USER``/``$USERNAME``, git identity, sibling-dir names): surfaced for a human to
  confirm, never fail CI. Hostname stays warn-only unless a config ``[rules]`` entry
  raises it to fail (OQ4).

Scan modes: working tree (default, tracked files via ``git ls-files``), git history
(``git log -p -U0`` added lines, bounded), a built wheel (zip entries), and STAGED blob
content (``git show :<path>``) for the pre-commit hook.

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

# --- Fix rewrites (severity: fail patterns that CAN be auto-rewritten by --fix) --------------
# Map a matched leak class to a safe, portable replacement. Only home-style absolute paths are
# rewritten (the tail is preserved); identity/private-repo/session tokens are NOT auto-rewritten
# because there is no safe generic replacement (a human must decide). ``--fix`` reports those as
# "needs manual edit" rather than guessing.
_HOME_ANY_RE = re.compile(r"/home/[A-Za-z0-9._-]+(?=/|\b)")
_USERS_ANY_RE = re.compile(r"/Users/[A-Za-z0-9._-]+(?=/|\b)")

# --- IP rulesets (severity: fail, but CONFIG-GATED OFF by default, OQ4/E4) --------------------
# IPv4 and a conservative IPv6. Off unless config enables [ip] enabled = true. Loopback and the
# documentation/private placeholder ranges are never flagged (too noisy, rarely identifying).
_IP_PATTERNS: dict[str, re.Pattern[str]] = {
    "ipv4": re.compile(
        r"\b(?!0\.0\.0\.0\b)(?!127\.)(?!10\.)(?!192\.168\.)"
        r"(?:(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])\b"
    ),
    "ipv6": re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{1,4}\b"),
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
        "tests/test_leak_sanitizer.py",
        "agent_workflows/local_leaks.py",
        "agent_workflows/leak_sanitizer.py",
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
# ONE canonical config (plan-review PR-003 / OQ2/OQ3): the repo allowlist (public-OK-here,
# travels + CI-deterministic) lives at .agents/local-leaks-allowlist.toml; the user hints
# (personal, never committed) live at <config_dir>/local-leaks-hints.json. Neither is required;
# both are additive. The tracked file's schema is extended (this IPD) to also carry
# [rules] enabled = [...] / [ip] enabled = true / blacklist entries, read by the same minimal
# TOML reader below.
REPO_ALLOWLIST_REL = ".agents/local-leaks-allowlist.toml"
USER_HINTS_FILENAME = "local-leaks-hints.json"


def _parse_simple_toml_lists(text: str) -> dict[str, list[str]]:
    """Minimal TOML reader for flat ``key = ["a", "b"]`` arrays (3.9-safe, no tomllib).

    Only the shapes this allowlist needs are supported: string arrays, one per key, values
    may span lines. Comments (``#``) and other keys are ignored. This avoids a dependency on
    tomllib (3.11+) while the support floor is 3.9. Section headers ([rules], [ip]) are ignored
    for key extraction; a bare ``ip_enabled = true`` / ``key = true`` boolean is also read.

    String values may contain ``]`` (e.g. a regex character class ``[a-z]`` in
    ``fail_patterns``): the array terminator ``]`` is only recognized OUTSIDE a quoted string.
    A value delimited by one quote char may contain the other quote char. There is no escape
    syntax; the config writer selects a delimiter that avoids embedding its own quote and
    rejects a value containing both quote chars (DECISIONS D98 / OQ4).
    """
    result: dict[str, list[str]] = {}
    # Find each ``key = [`` opener, then scan the array body respecting quotes so a ``]`` or a
    # delimiter char inside a quoted string is not mistaken for structure.
    for opener in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*\[", text):
        key = opener.group(1)
        values: list[str] = []
        i = opener.end()  # first char after the '['
        n = len(text)
        while i < n:
            ch = text[i]
            if ch in "\"'":
                quote = ch
                j = i + 1
                while j < n and text[j] != quote:
                    j += 1
                # Unterminated quote: stop this array (malformed); keep what we have.
                if j >= n:
                    i = j
                    break
                values.append(text[i + 1 : j])
                i = j + 1
            elif ch == "]":
                break  # end of the array (we are outside any quoted string here)
            else:
                i += 1
        result[key] = values
    return result


def _parse_simple_toml_bools(text: str) -> dict[str, bool]:
    """Read flat ``key = true|false`` booleans (for [ip] enabled and [rules] toggles)."""
    result: dict[str, bool] = {}
    for m in re.finditer(r"(?m)^\s*([A-Za-z0-9_-]+)\s*=\s*(true|false)\b", text):
        result[m.group(1)] = m.group(2) == "true"
    return result


def load_repo_allowlist(repo_root: Path) -> dict[str, list[str]]:
    """Read the repo-committed allowlist TOML; return {} if absent/unreadable."""
    p = repo_root / REPO_ALLOWLIST_REL
    try:
        return _parse_simple_toml_lists(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def load_repo_config_bools(repo_root: Path) -> dict[str, bool]:
    """Read boolean toggles ([ip] enabled, [rules] hostname=fail-ish) from the allowlist file."""
    p = repo_root / REPO_ALLOWLIST_REL
    try:
        return _parse_simple_toml_bools(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def _config_dir() -> Path:
    try:
        from . import config as _config

        return _config.config_dir()
    except Exception:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        return Path(base).expanduser() / "agent-workflows"


def load_user_hints() -> dict[str, list[str]]:
    """Read the never-committed user hints JSON from the config dir; {} if absent."""
    import json

    p = _config_dir() / USER_HINTS_FILENAME
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


# --- Config writers (used by the interactive wizard; schema-cohesive with the loaders) -------
class ConfigValueError(ValueError):
    """A config value cannot be represented by the minimal TOML parser and was rejected."""


def _toml_quote(value: str) -> str:
    """Return ``value`` as a TOML-parser-round-trippable quoted string, or raise.

    The minimal reader (``_parse_simple_toml_lists``) has no escape syntax, so a value is
    delimited by the quote char it does NOT contain (dual-quote selection, DECISIONS D98).
    A value containing BOTH a single and a double quote cannot round-trip and is rejected
    with a named error rather than written and silently mis-read. ``]`` and other regex
    metacharacters are fine (the reader now respects quoting).
    """
    has_dq = '"' in value
    has_sq = "'" in value
    if has_dq and has_sq:
        raise ConfigValueError(
            "value contains both single and double quotes, which the leak-sanitizer config "
            f"format cannot store: {value!r}"
        )
    if has_dq:
        return "'" + value + "'"
    return '"' + value + '"'


def _atomic_write(path: Path, payload: str) -> Path:
    """Write ``payload`` to ``path`` atomically (temp in same dir + os.replace), mkdir parents.

    Mirrors ``config.save`` so a crash mid-write cannot corrupt an existing config file.
    """
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".leaks-cfg.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_name, str(path))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def _render_toml_array(key: str, values: list[str]) -> str:
    """Render ``key = ["a", "b"]`` (or ``key = []``) round-trippable by the minimal reader."""
    if not values:
        return f"{key} = []\n"
    quoted = ", ".join(_toml_quote(v) for v in values)
    return f"{key} = [{quoted}]\n"


def write_repo_allowlist(
    repo_root: Path,
    *,
    allow_line_substrings: list[str],
    fail_patterns: list[str],
    ip_enabled: bool,
    hostname_fail: bool,
) -> Path:
    """Write the tracked ``.agents/local-leaks-allowlist.toml`` atomically.

    Emits only shapes the minimal reader round-trips (flat string arrays + flat booleans).
    Raises ``ConfigValueError`` (before writing anything) if any list value cannot be stored.
    """
    # Validate every value first so we never write a partially-representable file.
    for v in list(allow_line_substrings) + list(fail_patterns):
        _toml_quote(v)  # raises ConfigValueError on an unrepresentable value
    header = (
        "# Leak-sanitizer repo allowlist (tracked, travels with the repo, CI-deterministic).\n"
        "# Managed by `aw sanitize --configure`; hand-edits are fine but keep values on one\n"
        "# line and avoid a value containing BOTH ' and \" (the minimal reader has no escape).\n\n"
    )
    body = (
        _render_toml_array("allow_line_substrings", allow_line_substrings)
        + _render_toml_array("fail_patterns", fail_patterns)
        + "\n"
        + f"ip_enabled = {'true' if ip_enabled else 'false'}\n"
        + f"hostname_fail = {'true' if hostname_fail else 'false'}\n"
    )
    return _atomic_write(repo_root / REPO_ALLOWLIST_REL, header + body)


def write_user_hints(tokens: list[str], patterns: list[str]) -> Path:
    """Write the never-committed user-hints JSON to the config dir atomically (never the repo)."""
    import json

    payload = (
        json.dumps(
            {"tokens": list(tokens), "patterns": list(patterns)},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return _atomic_write(_config_dir() / USER_HINTS_FILENAME, payload)


def derive_warn_tokens(repo_root: Path) -> dict[str, str]:
    """Auto-derive advisory (warn-only) personal tokens from the environment.

    Every source is OPTIONAL and cross-platform: a missing value yields no token (never an
    error). Returns {token: reason}. These NEVER fail the gate (unless raised via config); the
    lens surfaces them.
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
    # Hostname (FQDN + node + short label).
    try:
        add(socket.gethostname() or None, "hostname")
    except Exception:
        pass
    try:
        fqdn = socket.getfqdn() or None
        add(fqdn, "fqdn")
        if fqdn and "." in fqdn:
            add(fqdn.split(".", 1)[0] or None, "hostname short label")
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


# Which auto-derived reasons map to which rule name (so a config toggle can raise one to fail).
_HOSTNAME_REASONS = frozenset({"hostname", "fqdn", "hostname short label"})


def build_ruleset(
    repo_root: Path,
    *,
    include_warn: bool = False,
) -> Ruleset:
    """Assemble the active ruleset: structural fail patterns + curated allowlist + hints,
    and (when include_warn) the advisory auto-derived tokens as warn patterns.

    Config (OQ4): [ip] enabled = true adds the IP patterns as fail; a hostname_fail = true
    toggle promotes the derived hostname tokens from warn to fail. Defaults: home + identity
    fail-rules on; hostname warn-only; IP off.
    """
    rs = Ruleset(
        fail=dict(_FAIL_PATTERNS), allow_line_substrings=_ALLOWED_LINE_SUBSTRINGS
    )

    repo_cfg = load_repo_allowlist(repo_root)
    bools = load_repo_config_bools(repo_root)
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

    # IP ruleset: OFF by default, opt-in via config `ip_enabled = true` (OQ4/E4). When on it is
    # fail-severity.
    if bools.get("ip_enabled"):
        for name, pat in _IP_PATTERNS.items():
            rs.fail[name] = pat

    hostname_fail = bool(bools.get("hostname_fail"))

    if include_warn or hostname_fail:
        for tok, reason in derive_warn_tokens(repo_root).items():
            is_host = reason in _HOSTNAME_REASONS
            if is_host and hostname_fail:
                rs.fail[f"hostname:{tok}"] = re.compile(re.escape(tok))
            elif include_warn:
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
    """Scan text line-by-line against the ruleset; return findings.

    Binary content is scanned too (E4): a leak inside a binary blob is still flagged rather
    than skipped, so a human can decide.
    """
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


def _staged_files(repo_root: Path) -> list[str]:
    out = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACM",
        ],
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
            # Binary/unreadable on disk: try the tracked blob so binaries are still scanned (E4).
            try:
                blob = subprocess.run(
                    ["git", "-C", str(repo_root), "show", f"HEAD:{rel}"],
                    capture_output=True,
                    check=False,
                )
                text = blob.stdout.decode("utf-8", "replace")
            except Exception:
                continue
        findings.extend(scan_text(text, rel, ruleset, include_warn=include_warn))
    return findings


def scan_staged(repo_root: Path, *, include_warn: bool = False) -> list[Finding]:
    """Scan STAGED blob content (``git show :<path>``) for the pre-commit hook (pubrun idea)."""
    ruleset = build_ruleset(repo_root, include_warn=include_warn)
    findings: list[Finding] = []
    for rel in _staged_files(repo_root):
        if rel in _ALLOWED_PATHS:
            continue
        try:
            blob = subprocess.run(
                ["git", "-C", str(repo_root), "show", f":{rel}"],
                capture_output=True,
                check=False,
            )
            text = blob.stdout.decode("utf-8", "replace")
        except Exception:
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
        for f in scan_text(
            text, f"{wheel_path.name}!{name}", ruleset, include_warn=include_warn
        ):
            findings.append(f)
    return findings


# --- Fix (opt-in, interactive by default, NEVER in the hook; E5) -----------------------------
def _rewrite_line(line: str) -> str:
    """Return the line with home-style absolute paths rewritten to a portable ~ form.

    Only home/Users paths are auto-rewritten (safe, generic). Identity, private-repo and
    session tokens are NOT rewritten (no safe generic replacement) and are reported for manual
    editing instead.
    """
    line = _HOME_ANY_RE.sub("~", line)
    line = _USERS_ANY_RE.sub("~", line)
    return line


def fix_working_tree(
    repo_root: Path,
    *,
    assume_yes: bool = False,
    dry_run: bool = False,
    confirm=None,
) -> tuple[list[str], list[Finding]]:
    """Rewrite auto-fixable leaks in tracked files. Interactive-confirm per file by default.

    Returns (changed_paths, unfixable_findings). ``confirm(path, preview)`` -> bool decides a
    file when not assume_yes; a None confirm with not assume_yes prompts on stdin. Unfixable
    findings (identity/private-repo/session) are returned for the caller to report; they are
    never silently rewritten.
    """
    ruleset = build_ruleset(repo_root)
    changed: list[str] = []
    unfixable: list[Finding] = []
    for rel in _tracked_files(repo_root):
        if rel in _ALLOWED_PATHS:
            continue
        p = repo_root / rel
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        file_findings = scan_text(text, rel, ruleset)
        if not file_findings:
            continue
        new_text_lines = []
        file_changed = False
        for line in text.splitlines(keepends=True):
            stripped = line.rstrip("\n")
            rewritten = _rewrite_line(stripped)
            if rewritten != stripped:
                file_changed = True
                new_text_lines.append(rewritten + ("\n" if line.endswith("\n") else ""))
            else:
                new_text_lines.append(line)
        # Record findings that the rewrite did NOT resolve (need a human).
        remaining = scan_text("".join(new_text_lines), rel, ruleset)
        unfixable.extend(remaining)
        if not file_changed:
            continue
        if dry_run:
            changed.append(rel)
            continue
        ok = True
        if not assume_yes:
            preview = "".join(new_text_lines)
            if confirm is not None:
                ok = bool(confirm(rel, preview))
            else:
                ok = _prompt_stdin(rel)
        if ok:
            p.write_text("".join(new_text_lines), encoding="utf-8")
            changed.append(rel)
    return changed, unfixable


def _prompt_stdin(rel: str) -> bool:
    try:
        ans = input(f"Rewrite leak-class paths in {rel}? [y/N] ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


# --- Runner ----------------------------------------------------------------------------------
def run(
    repo_root: Path,
    *,
    history: bool = False,
    max_commits: int | None = None,
    wheel: Path | None = None,
    staged: bool = False,
    include_warn: bool = False,
) -> tuple[list[Finding], list[Finding]]:
    """Run the requested scan; return (fail_findings, warn_findings)."""
    if wheel is not None:
        findings = scan_wheel(wheel, repo_root, include_warn=include_warn)
    elif history:
        findings = scan_history(
            repo_root, max_commits=max_commits, include_warn=include_warn
        )
    elif staged:
        findings = scan_staged(repo_root, include_warn=include_warn)
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
        "--staged",
        action="store_true",
        help="Scan STAGED blob content (for the pre-commit hook).",
    )
    parser.add_argument(
        "--warn",
        action="store_true",
        help="Also report advisory auto-derived candidates.",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Machine-parseable output for an LLM caller: one 'path:line\\trule\\tseverity' "
        "per finding, no prose.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite auto-fixable home-style paths to ~ (interactive-confirm per file unless "
        "--yes; identity/private tokens are reported, never auto-rewritten).",
    )
    parser.add_argument(
        "--yes",
        "--force",
        dest="assume_yes",
        action="store_true",
        help="With --fix, apply changes without per-file confirmation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --fix, show what would change without writing.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.dir).resolve()
    wheel = Path(args.wheel).resolve() if args.wheel else None

    if args.fix:
        try:
            changed, unfixable = fix_working_tree(
                repo_root, assume_yes=args.assume_yes, dry_run=args.dry_run
            )
        except subprocess.CalledProcessError:
            print(
                "check-local-leaks: not a git repository or git unavailable",
                file=sys.stderr,
            )
            return 2
        verb = "would rewrite" if args.dry_run else "rewrote"
        for rel in changed:
            print(f"{verb}: {rel}", file=sys.stderr)
        if unfixable:
            print("Needs manual edit (no safe auto-fix):", file=sys.stderr)
            for f in unfixable:
                print(f"  {f.location}: {f.rule}: {f.snippet}", file=sys.stderr)
            return 1
        if not changed:
            print("No auto-fixable local leaks found.", file=sys.stderr)
        return 0

    try:
        # --agent stays fail-focused by default (deterministic, low-noise); pass --warn to
        # also include advisory auto-derived candidates.
        fails, warns = run(
            repo_root,
            history=args.history,
            max_commits=args.max_commits,
            wheel=wheel,
            staged=args.staged,
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

    if args.agent:
        # Precise, concise, machine-parseable: one tab-separated record per finding, no prose.
        for f in (*fails, *warns):
            print(f"{f.location}\t{f.rule}\t{f.severity}")
        return 1 if fails else 0

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
            "or add a justified entry to .agents/local-leaks-allowlist.toml if genuinely public. "
            "'--fix' can rewrite home-style paths.",
            file=sys.stderr,
        )
        return 1
    print("No local leaks found.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
