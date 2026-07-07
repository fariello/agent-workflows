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
      "ignore":       [ "*/vendor/*", ... ], # fnmatch globs, discovery-only
      "defaults":     { "backup": true, "prune": true }
    }

Paths are stored ``~``-preserved (portable, human-readable) and expanded at use-time.
Writes are atomic (temp file + ``os.replace``) so an interrupted write cannot corrupt an
existing config.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

CONFIG_VERSION = 1
_APP_DIR = "agent-workflows"
_CONFIG_NAME = "config.json"

# The only keys ever persisted. Anything else on load is dropped (R-5).
_ALLOWED_TOP_KEYS = frozenset(
    {"config_version", "search_roots", "repos", "ignore", "defaults"}
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
        return "~" + os.sep + norm[len(prefix):]
    return norm


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

    for key in ("search_roots", "repos"):
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

    # config_version is managed by migrate(); keep the current version on write.
    out["config_version"] = CONFIG_VERSION
    return out


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

    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".config.", suffix=".tmp")
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
