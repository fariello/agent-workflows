"""User configuration for the agent-workflows CLI (JSON, stdlib only).

The config remembers where a user keeps repos so `install all` / `setup` need no
re-interview. It lives at ``$XDG_CONFIG_HOME/agent-workflows/config.json`` (falling back
to ``~/.config/agent-workflows/config.json``); it is NEVER written directly under ``~/``
(DECISIONS D46 / spec Goal 4).

Schema (config_version 1) - a FIXED allowlist of NON-sensitive keys; no secret or
per-project sensitive data is ever stored (spec Non-goal; IPD-2 R-5):

    {
      "config_version": 1,
      "search_roots": [ "~/src", ... ],   # dirs to discover repos under
      "repos":        [ "~/src/foo", ... ],  # the explicit allowlist install-all uses
      "ignore":       [ "*/vendor/*", ... ], # fnmatch globs, discovery-only NOISE filter
      "exclude":      [ "~/src/legacy", "*/never-install/*", ... ], # deliberate NEVER-install blocklist
      "defaults":     { "backup": true, "prune": true }
    }

``ignore`` and ``exclude`` are distinct: ``ignore`` is a discovery-only fnmatch NOISE filter
(hide uninteresting paths from discovery), while ``exclude`` is a deliberate, user-curated
blocklist of repos that must NEVER be installed into. ``exclude`` is honored by discovery AND
guards an explicitly targeted install (interactive continue prompt; non-interactive skip).

Paths are stored ``~``-preserved (portable, human-readable) and expanded at use-time.
Writes are atomic (temp file + ``os.replace``) so an interrupted write cannot corrupt an
existing config.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONFIG_VERSION = 1
_APP_DIR = "agent-workflows"
_CONFIG_NAME = "config.json"

# The only keys ever persisted. Anything else on load is dropped (R-5).
_ALLOWED_TOP_KEYS = frozenset(
    {
        "config_version",
        "search_roots",
        "repos",
        "ignore",
        "exclude",
        "defaults",
        "aw_home",
    }
)
_ALLOWED_DEFAULT_KEYS = frozenset({"backup", "prune"})


def config_dir() -> Path:
    """Return the config directory, honoring XDG_CONFIG_HOME, else ~/.config.

    Never returns ``~/`` itself; always ``.../agent-workflows/``.
    """

    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / _APP_DIR


def config_path() -> Path:
    """Return the full path to config.json."""

    return config_dir() / _CONFIG_NAME


def default_config() -> Dict[str, Any]:
    """Return a fresh, empty config at the current schema version."""

    return {
        "config_version": CONFIG_VERSION,
        "search_roots": [],
        "repos": [],
        "ignore": [],
        "exclude": [],
        "defaults": {"backup": True, "prune": True},
    }


def _preserve_home(path: str) -> str:
    """Store an absolute path ``~``-preserved when it is under the home dir.

    ``/home/u/src`` -> ``~/src`` (portable); paths outside home are left absolute.
    """

    try:
        home = str(Path.home())
    except (RuntimeError, OSError):
        return path
    norm = os.path.normpath(path)
    if norm == home:
        return "~"
    prefix = home + os.sep
    if norm.startswith(prefix):
        rel = norm[len(prefix) :]
        # Store with forward slashes so the config is portable across OSes; both
        # os.path.expanduser and pathlib.Path accept "/" on Windows at expand-time.
        return "~/" + rel.replace(os.sep, "/")
    # Normalize separators in stored absolute paths too, for a portable, stable config.
    return norm.replace(os.sep, "/")


def expand_path(stored: str) -> Path:
    """Expand a stored path (``~`` and environment vars) at use-time.

    Handles the tilde and Windows-style ``%VAR%``/``$VAR`` via expandvars.
    """

    return Path(os.path.expandvars(os.path.expanduser(stored)))


def normalize(config: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce an arbitrary mapping into a valid config, dropping unknown keys (R-5).

    Missing keys are filled from defaults; list values are coerced to lists of
    ``~``-preserved strings; ``defaults`` keeps only the allowed boolean keys.
    """

    out = default_config()
    if not isinstance(config, dict):
        return out

    for key in ("search_roots", "repos", "exclude"):
        value = config.get(key)
        if isinstance(value, list):
            out[key] = [_preserve_home(str(v)) for v in value]

    ignore = config.get("ignore")
    if isinstance(ignore, list):
        out["ignore"] = [str(v) for v in ignore]

    defaults = config.get("defaults")
    if isinstance(defaults, dict):
        for k in _ALLOWED_DEFAULT_KEYS:
            if isinstance(defaults.get(k), bool):
                out["defaults"][k] = defaults[k]

    aw_home_val = config.get("aw_home")
    if isinstance(aw_home_val, str) and aw_home_val.strip():
        out["aw_home"] = _preserve_home(aw_home_val.strip())

    # config_version is managed by migrate(); keep the current version on write.
    out["config_version"] = CONFIG_VERSION
    return out


def get_aw_home(explicit_flag: Optional[str] = None) -> Tuple[Path, str]:
    """Resolve effective AW_HOME and explain the source without side effects (spec Section 7.1).

    Precedence:
      1. explicit_flag (--aw-home flag)
      2. AW_HOME environment variable
      3. saved XDG config value (~/.config/agent-workflows/config.json)
      4. platform default (~/.aw)
    """
    if explicit_flag:
        p = Path(os.path.expandvars(os.path.expanduser(explicit_flag))).resolve()
        return p, f"--aw-home flag ({explicit_flag})"

    env_val = os.environ.get("AW_HOME")
    if env_val:
        p = Path(os.path.expandvars(os.path.expanduser(env_val))).resolve()
        return p, "AW_HOME environment variable"

    cfg = load()
    saved_home = cfg.get("aw_home")
    if saved_home:
        p = expand_path(saved_home).resolve()
        return p, f"saved user config ({config_path()})"

    default_home = Path.home() / ".aw"
    return default_home.resolve(), "platform default (~/.aw)"


def migrate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate an older-versioned config forward to the current schema.

    Currently only version 1 exists, so this normalizes and stamps the version. Future
    versions add ordered upgrade steps here.
    """

    return normalize(config)


def load() -> Dict[str, Any]:
    """Load the config, returning a fresh default if none exists or it is unreadable.

    Always returns a normalized config (unknown/sensitive keys dropped, R-5).
    """

    path = config_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default_config()
    return migrate(raw)


def save(config: Dict[str, Any]) -> Path:
    """Atomically write the config (normalized) and return its path.

    Creates the config directory as needed. Never writes under ``~/`` directly. Uses a
    temp file in the same directory + ``os.replace`` so a crash mid-write cannot corrupt
    an existing config.
    """

    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(normalize(config), indent=2, sort_keys=True) + "\n"

    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".config.", suffix=".tmp"
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


def is_configured() -> bool:
    """True if a config file exists with at least one search root or repo."""

    if not config_path().is_file():
        return False
    cfg = load()
    return bool(cfg.get("search_roots") or cfg.get("repos"))


def expanded_search_roots(config: Dict[str, Any]) -> List[Path]:
    """Return the config's search roots expanded to absolute Paths."""

    return [expand_path(p) for p in config.get("search_roots", [])]


def expanded_repos(config: Dict[str, Any]) -> List[Path]:
    """Return the config's repo allowlist expanded to absolute Paths."""

    return [expand_path(p) for p in config.get("repos", [])]


def expanded_excludes(config: Dict[str, Any]) -> List[str]:
    """Return the config's exclude entries with ``~``/vars expanded, as strings.

    Entries may be absolute repo paths OR fnmatch globs (a deliberate NEVER-install
    blocklist), so this returns expanded STRINGS (not resolved ``Path`` objects) suitable
    for both exact-path comparison and ``fnmatch`` matching by the discovery/install guard.
    A leading ``~`` (or ``$VAR``) is expanded; a glob with no ``~`` is returned unchanged.
    """

    return [
        os.path.expandvars(os.path.expanduser(str(e)))
        for e in config.get("exclude", [])
    ]


# --------------------------------------------------------------------------------------
# ipddeps Order ovbnyq (spec 25kzda 2.11): the ONE dependency-schema cutover marker.
#
# Recorded in the COMMITTED, portable project policy (`.aw/config/project.json`) as the
# `dependency_schema_cutover` key. It is read here (not via the XDG user config, which drops
# unknown keys) with a fail-open default: an ABSENT or unreadable marker means "no cutover in
# effect", so EVERY existing plan is grandfathered and the corpus is NEVER mass-failed. When the
# marker IS set, only IPDs authored on/after its `date` (YYYY-MM-DD) must carry a resolved
# Item-Dependencies statement; older plans stay grandfathered (advisory).
# --------------------------------------------------------------------------------------

DEPENDENCY_SCHEMA_CUTOVER_KEY = "dependency_schema_cutover"


def read_dependency_schema_cutover(
    repo_root: "os.PathLike[str] | str",
) -> Optional[Dict[str, Any]]:
    """Return the dependency-schema cutover marker dict from `.aw/config/project.json`, or None.

    The marker (when present) is a small object like ``{"date": "2026-09-01", "commit": "<sha>"}``.
    Fail-open: any read/parse error, a missing file, or a missing key returns None (no cutover ->
    grandfather everything). Pure read; never writes.
    """
    project_file = Path(repo_root) / ".aw" / "config" / "project.json"
    try:
        data = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    marker = data.get(DEPENDENCY_SCHEMA_CUTOVER_KEY)
    if isinstance(marker, dict):
        return marker
    # Tolerate a bare date string for convenience.
    if isinstance(marker, str) and marker.strip():
        return {"date": marker.strip()}
    return None


def dependency_cutover_date(repo_root: "os.PathLike[str] | str") -> Optional[str]:
    """Return the cutover `date` (YYYY-MM-DD) if a marker is set, else None (no cutover)."""
    marker = read_dependency_schema_cutover(repo_root)
    if marker is None:
        return None
    date = marker.get("date")
    return date if isinstance(date, str) and date.strip() else None
