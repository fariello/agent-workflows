"""User configuration for the agent-workflows CLI (JSON, stdlib only).

The config remembers where a user keeps repos so `install all` / `setup` need no
re-interview. It lives at ``$XDG_CONFIG_HOME/agent-workflows/config.json`` (falling back
to ``~/.config/agent-workflows/config.json``); it is NEVER written directly under ``~/``
(DECISIONS D46 / spec Goal 4).

Schema (config_version 2) - a FIXED allowlist of NON-sensitive keys; no secret or
per-project sensitive data is ever stored (spec Non-goal; IPD-2 R-5). All repository
management settings are grouped under the single ``repos`` mapping:

    {
      "config_version": 2,
      "repos": {
        "search":    [ "~/src", ... ],   # dirs to discover repos under
        "installed": [ "~/src/foo", ... ],  # the explicit allowlist install-all uses
        "ignore":    [ "*/vendor/*", ... ], # fnmatch globs, discovery-only NOISE filter
        "exclude":   [ "~/src/legacy", "*/never-install/*", ... ] # deliberate NEVER-install blocklist
      },
      "defaults":     { "backup": true, "prune": true }
    }

``repos.ignore`` and ``repos.exclude`` are distinct: ``repos.ignore`` is a discovery-only
fnmatch NOISE filter (hide uninteresting paths from discovery), while ``repos.exclude`` is a
deliberate, user-curated blocklist of repos that must NEVER be installed into.
``repos.exclude`` is honored by discovery AND guards an explicitly targeted install
(interactive continue prompt; non-interactive skip).

Schema version 1 used flat top-level keys (``search_roots``, ``repos`` as a list, ``ignore``,
``exclude``). ``normalize()`` migrates a v1 config forward automatically, keyed on the SHAPE of
``repos`` rather than the recorded version, so a hand-edited file with a stale version still
migrates. A config whose ``config_version`` is NEWER than this module understands is never
normalized-and-dropped: ``load()`` returns it untouched and ``save()`` refuses to overwrite it
(fail closed), because normalizing an unknown shape would silently discard the user's search
roots, repo allowlist, and never-install blocklist.

Paths are stored ``~``-preserved (portable, human-readable) and expanded at use-time.
Writes are atomic (temp file + ``os.replace``) so an interrupted write cannot corrupt an
existing config.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

CONFIG_VERSION = 2
_APP_DIR = "agent-workflows"
_CONFIG_NAME = "config.json"

# The only keys ever persisted. Anything else on load is dropped (R-5). `normalize()`
# enforces this allowlist by rebuilding the output from `default_config()`.
_ALLOWED_TOP_KEYS = frozenset(
    {
        "config_version",
        "repos",
        "defaults",
        "aw_home",
    }
)
_ALLOWED_REPOS_KEYS = frozenset({"search", "installed", "exclude", "ignore"})
_ALLOWED_DEFAULT_KEYS = frozenset({"backup", "prune"})

# The v1 flat keys and the v2 nested subkeys they migrate into (E-02). Kept as an explicit
# mapping so the migration is data, not scattered conditionals.
_LEGACY_KEY_MAP = {
    "search_roots": "search",
    "repos": "installed",
    "exclude": "exclude",
    "ignore": "ignore",
}


class ConfigError(Exception):
    """Raised on invalid configuration key or value."""


@dataclass(frozen=True)
class ConfigKeySpec:
    key: str
    type_name: str
    description: str
    read_only: bool = False


CONFIG_SCHEMA: Dict[str, ConfigKeySpec] = {
    "config_version": ConfigKeySpec(
        key="config_version",
        type_name="int",
        description="Configuration schema version",
        read_only=True,
    ),
    "repos": ConfigKeySpec(
        key="repos",
        type_name="dict",
        description="Repository management settings mapping",
    ),
    "repos.search": ConfigKeySpec(
        key="repos.search",
        type_name="list[path]",
        description="Search root directories for repository discovery",
    ),
    "repos.installed": ConfigKeySpec(
        key="repos.installed",
        type_name="list[path]",
        description="Explicit repository allowlist for install operations",
    ),
    "repos.ignore": ConfigKeySpec(
        key="repos.ignore",
        type_name="list[str]",
        description="fnmatch globs to filter noisy discovery paths",
    ),
    "repos.exclude": ConfigKeySpec(
        key="repos.exclude",
        type_name="list[path|glob]",
        description="Deliberate never-install repository blocklist",
    ),
    "defaults": ConfigKeySpec(
        key="defaults",
        type_name="dict",
        description="Default operational flags mapping",
    ),
    "defaults.backup": ConfigKeySpec(
        key="defaults.backup",
        type_name="bool",
        description="Whether to create backups before modifying repositories",
    ),
    "defaults.prune": ConfigKeySpec(
        key="defaults.prune",
        type_name="bool",
        description="Whether to prune stale workflow shims on install",
    ),
    "aw_home": ConfigKeySpec(
        key="aw_home",
        type_name="path",
        description="Configured toolkit home directory",
    ),
}


def parse_set_args(tokens: Sequence[str]) -> Tuple[str, str]:
    """Parse flexible assignment syntax: 'var val', 'var=val', 'var = val', 'var to val'."""
    if not tokens:
        raise ConfigError(
            "Missing variable name and value. Usage: aw config set <varname> [to|=| = ] <value>"
        )
    first = str(tokens[0]).strip()
    if "=" in first:
        k, v = first.split("=", 1)
        rest = [v] + list(tokens[1:]) if v else list(tokens[1:])
        val_str = " ".join(str(x) for x in rest).strip()
        if not val_str:
            raise ConfigError(
                f"Missing value for '{k.strip()}'. Usage: aw config set {k.strip()} = <value>"
            )
        return k.strip(), val_str

    varname = first
    rest_tokens = list(tokens[1:])
    if not rest_tokens:
        raise ConfigError(
            f"Missing value for '{varname}'. Usage: aw config set {varname} <value>"
        )

    if rest_tokens[0] in ("=", "to", ":"):
        rest_tokens = rest_tokens[1:]
        if not rest_tokens:
            raise ConfigError(
                f"Missing value for '{varname}'. Usage: aw config set {varname} = <value>"
            )

    val_str = " ".join(str(x) for x in rest_tokens).strip()
    return varname, val_str


def parse_add_args(tokens: Sequence[str]) -> Tuple[str, str]:
    """Parse 'add <value> to <varname>', 'add <value> <varname>', or 'add <varname> <value>'."""
    if not tokens:
        raise ConfigError(
            "Missing value and variable name. Usage: aw config add <value> to <varname>"
        )
    toks = [str(x) for x in tokens]
    to_indices = [i for i, t in enumerate(toks) if t.lower() == "to"]
    if to_indices:
        idx = to_indices[-1]
        val_parts = toks[:idx]
        var_parts = toks[idx + 1 :]
        if not val_parts:
            raise ConfigError(
                "Missing value before 'to'. Usage: aw config add <value> to <varname>"
            )
        if not var_parts:
            raise ConfigError(
                "Missing variable name after 'to'. Usage: aw config add <value> to <varname>"
            )
        return " ".join(val_parts).strip(), " ".join(var_parts).strip()

    if len(toks) == 1:
        raise ConfigError(
            "Missing variable name. Usage: aw config add <value> to <varname>"
        )

    first = toks[0].strip().lower()
    last = toks[-1].strip().lower()
    if last in CONFIG_SCHEMA:
        return " ".join(toks[:-1]).strip(), toks[-1].strip()
    if first in CONFIG_SCHEMA:
        return " ".join(toks[1:]).strip(), toks[0].strip()

    return " ".join(toks[:-1]).strip(), toks[-1].strip()


def parse_remove_args(tokens: Sequence[str]) -> Tuple[str, str]:
    """Parse 'remove <value> from <varname>', 'remove <value> <varname>', or 'remove <varname> <value>'."""
    if not tokens:
        raise ConfigError(
            "Missing value and variable name. Usage: aw config remove <value> from <varname>"
        )
    toks = [str(x) for x in tokens]
    from_indices = [i for i, t in enumerate(toks) if t.lower() == "from"]
    if from_indices:
        idx = from_indices[-1]
        val_parts = toks[:idx]
        var_parts = toks[idx + 1 :]
        if not val_parts:
            raise ConfigError(
                "Missing value before 'from'. Usage: aw config remove <value> from <varname>"
            )
        if not var_parts:
            raise ConfigError(
                "Missing variable name after 'from'. Usage: aw config remove <value> from <varname>"
            )
        return " ".join(val_parts).strip(), " ".join(var_parts).strip()

    if len(toks) == 1:
        raise ConfigError(
            "Missing variable name. Usage: aw config remove <value> from <varname>"
        )

    first = toks[0].strip().lower()
    last = toks[-1].strip().lower()
    if last in CONFIG_SCHEMA:
        return " ".join(toks[:-1]).strip(), toks[-1].strip()
    if first in CONFIG_SCHEMA:
        return " ".join(toks[1:]).strip(), toks[0].strip()

    return " ".join(toks[:-1]).strip(), toks[-1].strip()


def parse_is_args(tokens: Sequence[str]) -> Tuple[str, str]:
    """Parse 'is <value> in <varname>' or 'is <value> <varname>'."""
    if not tokens:
        raise ConfigError(
            "Missing value and variable name. Usage: aw config is <value> in <varname>"
        )
    toks = [str(x) for x in tokens]
    in_indices = [i for i, t in enumerate(toks) if t.lower() == "in"]
    if in_indices:
        idx = in_indices[-1]
        val_parts = toks[:idx]
        var_parts = toks[idx + 1 :]
        if not val_parts:
            raise ConfigError(
                "Missing value before 'in'. Usage: aw config is <value> in <varname>"
            )
        if not var_parts:
            raise ConfigError(
                "Missing variable name after 'in'. Usage: aw config is <value> in <varname>"
            )
        return " ".join(val_parts).strip(), " ".join(var_parts).strip()

    if len(toks) == 1:
        raise ConfigError(
            "Missing variable name. Usage: aw config is <value> in <varname>"
        )

    first = toks[0].strip().lower()
    last = toks[-1].strip().lower()
    if last in CONFIG_SCHEMA:
        return " ".join(toks[:-1]).strip(), toks[-1].strip()
    if first in CONFIG_SCHEMA:
        return " ".join(toks[1:]).strip(), toks[0].strip()

    return " ".join(toks[:-1]).strip(), toks[-1].strip()


def _normalize_item_for_key(
    item_raw: str, spec: ConfigKeySpec
) -> Tuple[str, Optional[Path]]:
    """Return (stored_string, resolved_path_if_path)."""
    s = item_raw.strip()
    if spec.type_name in ("list[path]", "list[path|glob]"):
        stored = _preserve_home(s)
        try:
            expanded = expand_path(stored).resolve()
        except Exception:
            expanded = None
        return stored, expanded
    return s, None


def _item_matches(
    target_stored: str,
    target_expanded: Optional[Path],
    entry_stored: str,
    is_path: bool,
) -> bool:
    if target_stored == entry_stored:
        return True
    if is_path:
        try:
            entry_expanded = expand_path(entry_stored).resolve()
            if target_expanded is not None and entry_expanded == target_expanded:
                return True
        except Exception:
            pass
    return False


# --------------------------------------------------------------------------------------
# Nested-key resolution (E-04): ONE helper the mutators and readers share, so dotted-key
# handling is not reimplemented per verb.
# --------------------------------------------------------------------------------------


def _resolve_nested(cfg: Dict[str, Any], canon_key: str) -> Any:
    """Read a top-level or single-dotted key (``repos.search``, ``defaults.backup``).

    Returns None when the parent is absent or is not a mapping.
    """

    if "." not in canon_key:
        return cfg.get(canon_key)
    parent, child = canon_key.split(".", 1)
    container = cfg.get(parent)
    if not isinstance(container, dict):
        return None
    return container.get(child)


def _assign_nested(cfg: Dict[str, Any], canon_key: str, value: Any) -> None:
    """Write a top-level or single-dotted key, creating the parent mapping as needed."""

    if "." not in canon_key:
        cfg[canon_key] = value
        return
    parent, child = canon_key.split(".", 1)
    container = cfg.get(parent)
    if not isinstance(container, dict):
        container = {}
    else:
        container = dict(container)
    container[child] = value
    cfg[parent] = container


def _bare_repos_list_verb_error(action: str, example: str) -> "ConfigError":
    """Build the actionable error for a list verb aimed at the ``repos`` MAPPING (E-05).

    ``repos`` was a ``list[path]`` in schema v1, so ``aw config add <path> to repos`` used to
    work. It is now a mapping, and the generic "it is not a list" message would not tell the
    user where their path should go. Name the subkeys explicitly instead.
    """

    return ConfigError(
        f"Cannot {action} 'repos': it is now a group of settings, not a list. "
        "Use one of: repos.installed (the explicit repository allowlist, which is what the "
        "old flat 'repos' key was), repos.search (discovery search roots), "
        "repos.exclude (the never-install blocklist), or repos.ignore (discovery noise globs). "
        f"For example: {example}"
    )


def add_config_item(
    varname: str,
    item_raw: str,
    cfg: Optional[Dict[str, Any]] = None,
    auto_save: bool = True,
) -> Tuple[Dict[str, Any], str, List[str], bool, str]:
    """Add an item to a list-typed config key."""
    if cfg is None:
        cfg = load()
    else:
        cfg = dict(cfg)

    norm_key = varname.strip().lower()
    if norm_key not in CONFIG_SCHEMA:
        valid_keys = ", ".join(sorted(CONFIG_SCHEMA.keys()))
        raise ConfigError(f"Unknown config key '{varname}'. Valid keys: {valid_keys}")

    spec = CONFIG_SCHEMA[norm_key]
    if not spec.type_name.startswith("list["):
        if norm_key == "repos":
            raise _bare_repos_list_verb_error(
                "add item to", "aw config add <value> to repos.installed"
            )
        raise ConfigError(
            f"Cannot add item to '{norm_key}': it is not a list (type is {spec.type_name})."
        )
    if spec.read_only:
        raise ConfigError(
            f"Config key '{norm_key}' is read-only and cannot be modified."
        )

    stored, expanded = _normalize_item_for_key(item_raw, spec)
    current_list: List[str] = list(_resolve_nested(cfg, norm_key) or [])

    is_path = spec.type_name in ("list[path]", "list[path|glob]")
    already_present = any(
        _item_matches(stored, expanded, e, is_path) for e in current_list
    )

    if already_present:
        return cfg, norm_key, current_list, False, stored

    current_list.append(stored)
    _assign_nested(cfg, norm_key, current_list)
    normalized = normalize(cfg)
    if auto_save:
        save(normalized)
    return (
        normalized,
        norm_key,
        list(_resolve_nested(normalized, norm_key) or []),
        True,
        stored,
    )


def remove_config_item(
    varname: str,
    item_raw: str,
    cfg: Optional[Dict[str, Any]] = None,
    auto_save: bool = True,
) -> Tuple[Dict[str, Any], str, List[str], bool, str]:
    """Remove a matching item from a list-typed config key."""
    if cfg is None:
        cfg = load()
    else:
        cfg = dict(cfg)

    norm_key = varname.strip().lower()
    if norm_key not in CONFIG_SCHEMA:
        valid_keys = ", ".join(sorted(CONFIG_SCHEMA.keys()))
        raise ConfigError(f"Unknown config key '{varname}'. Valid keys: {valid_keys}")

    spec = CONFIG_SCHEMA[norm_key]
    if not spec.type_name.startswith("list["):
        if norm_key == "repos":
            raise _bare_repos_list_verb_error(
                "remove item from", "aw config remove <value> from repos.installed"
            )
        raise ConfigError(
            f"Cannot remove item from '{norm_key}': it is not a list (type is {spec.type_name})."
        )
    if spec.read_only:
        raise ConfigError(
            f"Config key '{norm_key}' is read-only and cannot be modified."
        )

    stored, expanded = _normalize_item_for_key(item_raw, spec)
    current_list: List[str] = list(_resolve_nested(cfg, norm_key) or [])
    is_path = spec.type_name in ("list[path]", "list[path|glob]")

    kept = []
    removed = False
    for e in current_list:
        if not removed and _item_matches(stored, expanded, e, is_path):
            removed = True
        else:
            kept.append(e)

    if not removed:
        return cfg, norm_key, current_list, False, stored

    _assign_nested(cfg, norm_key, kept)
    normalized = normalize(cfg)
    if auto_save:
        save(normalized)
    return (
        normalized,
        norm_key,
        list(_resolve_nested(normalized, norm_key) or []),
        True,
        stored,
    )


def is_config_item_present(
    varname: str,
    item_raw: str,
    cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bool, str]:
    """Check whether an item is present in a list-typed config key."""
    if cfg is None:
        cfg = load()
    norm_key = varname.strip().lower()
    if norm_key not in CONFIG_SCHEMA:
        valid_keys = ", ".join(sorted(CONFIG_SCHEMA.keys()))
        raise ConfigError(f"Unknown config key '{varname}'. Valid keys: {valid_keys}")

    spec = CONFIG_SCHEMA[norm_key]
    if not spec.type_name.startswith("list["):
        if norm_key == "repos":
            raise _bare_repos_list_verb_error(
                "check membership in", "aw config is <value> in repos.installed"
            )
        raise ConfigError(
            f"Cannot check membership in '{norm_key}': it is not a list (type is {spec.type_name})."
        )

    stored, expanded = _normalize_item_for_key(item_raw, spec)
    current_list: List[str] = list(_resolve_nested(cfg, norm_key) or [])
    is_path = spec.type_name in ("list[path]", "list[path|glob]")

    present = any(_item_matches(stored, expanded, e, is_path) for e in current_list)
    return norm_key, present, stored


def get_config_value(
    key: str,
    cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Any]:
    """Get the value of a config key (top-level or dotted)."""
    if cfg is None:
        cfg = load()
    norm_key = key.strip().lower()
    if norm_key in ("backup", "defaults.backup"):
        return "defaults.backup", cfg.get("defaults", {}).get("backup", True)
    if norm_key in ("prune", "defaults.prune"):
        return "defaults.prune", cfg.get("defaults", {}).get("prune", True)

    if norm_key not in CONFIG_SCHEMA:
        valid_keys = ", ".join(sorted(CONFIG_SCHEMA.keys()))
        raise ConfigError(f"Unknown config key '{key}'. Valid keys: {valid_keys}")

    if norm_key == "defaults":
        return "defaults", cfg.get("defaults", {"backup": True, "prune": True})
    if norm_key == "repos":
        value = cfg.get("repos")
        if not isinstance(value, dict):
            return "repos", default_config()["repos"]
        return "repos", value
    return norm_key, _resolve_nested(cfg, norm_key)


def set_config_value(
    key: str,
    raw_value: Any,
    cfg: Optional[Dict[str, Any]] = None,
    auto_save: bool = True,
) -> Tuple[Dict[str, Any], str, Any]:
    """Validate, coerce, set a config key, and optionally save config.json atomically."""
    if cfg is None:
        cfg = load()
    else:
        cfg = dict(cfg)

    norm_key = key.strip().lower()
    if norm_key in ("backup", "defaults.backup"):
        canon_key = "defaults.backup"
    elif norm_key in ("prune", "defaults.prune"):
        canon_key = "defaults.prune"
    else:
        canon_key = norm_key

    if canon_key not in CONFIG_SCHEMA:
        valid_keys = ", ".join(sorted(CONFIG_SCHEMA.keys()))
        raise ConfigError(f"Unknown config key '{key}'. Valid keys: {valid_keys}")

    spec = CONFIG_SCHEMA[canon_key]
    if spec.read_only:
        raise ConfigError(
            f"Config key '{canon_key}' is read-only and cannot be modified."
        )

    type_name = spec.type_name
    parsed_value: Any = None

    if type_name == "bool":
        if isinstance(raw_value, bool):
            parsed_value = raw_value
        elif isinstance(raw_value, str):
            s = raw_value.strip().lower()
            if s in ("true", "1", "yes", "on", "t", "y"):
                parsed_value = True
            elif s in ("false", "0", "no", "off", "f", "n"):
                parsed_value = False
            else:
                raise ConfigError(
                    f"Invalid boolean value for '{canon_key}': '{raw_value}'. Expected true/false, yes/no, 1/0."
                )
        else:
            raise ConfigError(f"Invalid boolean value for '{canon_key}': {raw_value}")
    elif type_name == "path":
        if raw_value is None or (
            isinstance(raw_value, str) and raw_value.strip() in ("", "none", "null")
        ):
            parsed_value = None
        elif isinstance(raw_value, (str, Path)):
            parsed_value = _preserve_home(str(raw_value).strip())
        else:
            raise ConfigError(f"Invalid path value for '{canon_key}': {raw_value}")
    elif type_name in ("list[path]", "list[str]", "list[path|glob]"):
        if isinstance(raw_value, list):
            items = raw_value
        elif isinstance(raw_value, str):
            s = raw_value.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    loaded = json.loads(s)
                    items = loaded if isinstance(loaded, list) else [s]
                except Exception:
                    items = [x.strip() for x in s[1:-1].split(",") if x.strip()]
            elif "," in s:
                items = [x.strip() for x in s.split(",") if x.strip()]
            elif s in ("", "[]", "none", "null"):
                items = []
            else:
                items = [s]
        else:
            raise ConfigError(f"Invalid list value for '{canon_key}': {raw_value}")

        if type_name in ("list[path]", "list[path|glob]"):
            parsed_value = [_preserve_home(str(x)) for x in items]
        else:
            parsed_value = [str(x) for x in items]
    elif type_name == "dict":
        if isinstance(raw_value, dict):
            parsed_value = raw_value
        elif isinstance(raw_value, str):
            try:
                loaded = json.loads(raw_value)
                if isinstance(loaded, dict):
                    parsed_value = loaded
                else:
                    raise ValueError
            except Exception:
                raise ConfigError(f"Invalid dict JSON for '{canon_key}': '{raw_value}'")
        else:
            raise ConfigError(f"Invalid dict value for '{canon_key}': {raw_value}")
    else:
        parsed_value = raw_value

    if canon_key == "repos":
        unknown = sorted(set(parsed_value) - _ALLOWED_REPOS_KEYS)
        if unknown:
            allowed = ", ".join(sorted(_ALLOWED_REPOS_KEYS))
            raise ConfigError(
                f"Unknown key(s) in 'repos': {', '.join(unknown)}. "
                f"Allowed keys: {allowed}."
            )

    if canon_key == "aw_home":
        if parsed_value is None:
            cfg.pop("aw_home", None)
        else:
            cfg["aw_home"] = parsed_value
    else:
        _assign_nested(cfg, canon_key, parsed_value)

    normalized = normalize(cfg)
    if auto_save:
        save(normalized)

    _, final_val = get_config_value(canon_key, normalized)
    return normalized, canon_key, final_val


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
        "repos": {
            "search": [],
            "installed": [],
            "exclude": [],
            "ignore": [],
        },
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


def _coerce_repo_list(subkey: str, value: Any) -> Optional[List[str]]:
    """Coerce one ``repos.*`` list value, or return None when it is not a list.

    Path-typed subkeys are stored ``~``-preserved; ``ignore`` holds plain fnmatch globs.
    """

    if not isinstance(value, list):
        return None
    if subkey == "ignore":
        return [str(v) for v in value]
    return [_preserve_home(str(v)) for v in value]


def normalize(config: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce an arbitrary mapping into a valid config, dropping unknown keys (R-5).

    Accepts EITHER the v2 nested shape or the legacy v1 flat shape and always returns the
    nested shape. Missing keys are filled from defaults; list values are coerced to lists of
    ``~``-preserved strings; ``defaults`` keeps only the allowed boolean keys.

    Migration (E-02) is decided by the SHAPE of ``repos``, not by ``config_version``, so a
    hand-edited file carrying a stale version still migrates. A legacy flat key is honored ONLY
    when its nested counterpart is absent, which makes the migration idempotent and keeps a
    partially migrated file from double-applying or losing the newer value.
    """

    out = default_config()
    if not isinstance(config, dict):
        return out

    raw_repos = config.get("repos")
    nested: Dict[str, Any] = raw_repos if isinstance(raw_repos, dict) else {}
    for subkey in _ALLOWED_REPOS_KEYS:
        coerced = _coerce_repo_list(subkey, nested.get(subkey))
        if coerced is not None:
            out["repos"][subkey] = coerced

    # Legacy v1 flat keys migrate in only where the nested counterpart is absent.
    for legacy_key, subkey in _LEGACY_KEY_MAP.items():
        if legacy_key == "repos" and not isinstance(raw_repos, list):
            # v2 `repos` is the mapping handled above; only a LIST is the v1 allowlist.
            continue
        if subkey in nested:
            continue
        coerced = _coerce_repo_list(subkey, config.get(legacy_key))
        if coerced is not None:
            out["repos"][subkey] = coerced

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

    # `_ALLOWED_TOP_KEYS` is the ACTUAL final allowlist (R-5), applied unconditionally rather
    # than relied on implicitly: `out` is built from `default_config()`, so today nothing can
    # slip through, but this keeps that guarantee true if a future edit adds a key to
    # `default_config()` without allowlisting it. Not an assert, which `-O` would strip.
    return {key: value for key, value in out.items() if key in _ALLOWED_TOP_KEYS}


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


def config_version_of(config: Any) -> int:
    """Return a config mapping's declared ``config_version``, defaulting to 1.

    A missing or non-integer version is treated as the original schema version 1, which is
    what an un-versioned hand-written file effectively is. ``bool`` is rejected because it is
    an ``int`` subclass and a ``true`` there is a typo, not a version.
    """

    if not isinstance(config, dict):
        return CONFIG_VERSION
    raw = config.get("config_version")
    if isinstance(raw, bool) or not isinstance(raw, int):
        return 1
    return raw


def is_future_version(config: Any) -> bool:
    """True when the config was written by a NEWER aw than this one (E-03).

    Such a config must never be normalized-and-written: ``normalize()`` rebuilds from
    ``default_config()`` and drops keys it does not recognize, so persisting the result would
    silently destroy settings this version cannot see, including ``repos.exclude``, the
    never-install blocklist that guards ``aw install``.
    """

    return config_version_of(config) > CONFIG_VERSION


def migrate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate an older-versioned config forward to the current schema.

    Version 1 (flat repository keys) migrates into version 2 (the nested ``repos`` mapping)
    inside ``normalize()``, which keys the migration on shape so an unversioned or
    stale-versioned file is handled too. A config from a FUTURE version is returned UNCHANGED
    rather than normalized, so nothing is dropped; ``save()`` then refuses to overwrite it.
    Future versions add ordered upgrade steps here.
    """

    if is_future_version(config):
        return config
    return normalize(config)


def load() -> Dict[str, Any]:
    """Load the config, returning a fresh default if none exists or it is unreadable.

    Normally returns a normalized config (unknown/sensitive keys dropped, R-5). A config
    written by a NEWER aw is returned as-is (passthrough) so its settings are visible rather
    than silently emptied; ``save()`` refuses to write over it (E-03).
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

    Fails closed (E-03) when the config in hand, or the file already on disk, declares a
    ``config_version`` newer than this aw understands: refusing to write is strictly safer
    than normalizing an unknown shape and destroying settings this version cannot see.
    """

    path = config_path()

    if is_future_version(config):
        raise ConfigError(
            f"Refusing to write {path}: the configuration in memory declares "
            f"config_version {config_version_of(config)}, but this aw understands up to "
            f"{CONFIG_VERSION}. Nothing was changed. Upgrade aw "
            "(for example 'pip install --upgrade agent-workflows') to manage this config."
        )

    if path.is_file():
        try:
            on_disk = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            on_disk = None
        if is_future_version(on_disk):
            raise ConfigError(
                f"Refusing to overwrite {path}: it was written by a newer aw "
                f"(config_version {config_version_of(on_disk)}; this aw understands up to "
                f"{CONFIG_VERSION}). Nothing was changed. Upgrade aw "
                "(for example 'pip install --upgrade agent-workflows') to manage this config."
            )

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


def repo_setting(config: Dict[str, Any], subkey: str) -> List[str]:
    """Return one ``repos.*`` list from a config mapping, or [] when absent/malformed.

    The single read path for the nested layout, so callers never index the raw mapping and a
    hand-broken config degrades to empty rather than raising.
    """

    repos = config.get("repos")
    if not isinstance(repos, dict):
        return []
    value = repos.get(subkey)
    return list(value) if isinstance(value, list) else []


def set_repo_setting(
    config: Dict[str, Any], subkey: str, values: Sequence[str]
) -> Dict[str, Any]:
    """Write one ``repos.*`` list into a config mapping in place and return it.

    The single write path for the nested layout, so callers never have to create or repair the
    ``repos`` container themselves. Raises on an unknown subkey rather than writing a key that
    ``normalize()`` would silently drop on save.
    """

    if subkey not in _ALLOWED_REPOS_KEYS:
        allowed = ", ".join(sorted(_ALLOWED_REPOS_KEYS))
        raise ConfigError(f"Unknown repos subkey '{subkey}'. Allowed keys: {allowed}.")
    repos = config.get("repos")
    if not isinstance(repos, dict):
        repos = {}
        config["repos"] = repos
    repos[subkey] = list(values)
    return config


def is_configured() -> bool:
    """True if a config file exists with at least one search root or installed repo.

    Tests the nested LISTS, never the ``repos`` container: the default mapping is a non-empty
    dict, so a container truthiness check would report every brand-new user as configured and
    suppress the smart-default setup path.
    """

    if not config_path().is_file():
        return False
    cfg = load()
    return bool(repo_setting(cfg, "search") or repo_setting(cfg, "installed"))


def expanded_search_roots(config: Dict[str, Any]) -> List[Path]:
    """Return the config's search roots (``repos.search``) expanded to absolute Paths."""

    return [expand_path(p) for p in repo_setting(config, "search")]


def expanded_repos(config: Dict[str, Any]) -> List[Path]:
    """Return the config's repo allowlist (``repos.installed``) expanded to absolute Paths."""

    return [expand_path(p) for p in repo_setting(config, "installed")]


def ignore_patterns(config: Dict[str, Any]) -> List[str]:
    """Return the config's discovery noise globs (``repos.ignore``) as plain strings.

    These are fnmatch globs, never paths, so they are returned unexpanded.
    """

    return repo_setting(config, "ignore")


def expanded_excludes(config: Dict[str, Any]) -> List[str]:
    """Return the config's ``repos.exclude`` entries with ``~``/vars expanded, as strings.

    Entries may be absolute repo paths OR fnmatch globs (a deliberate NEVER-install
    blocklist), so this returns expanded STRINGS (not resolved ``Path`` objects) suitable
    for both exact-path comparison and ``fnmatch`` matching by the discovery/install guard.
    A leading ``~`` (or ``$VAR``) is expanded; a glob with no ``~`` is returned unchanged.
    """

    return [
        os.path.expandvars(os.path.expanduser(str(e)))
        for e in repo_setting(config, "exclude")
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


# --------------------------------------------------------------------------------------
# revgate Order 01 (15zvu6) E-05: the ONE review-findings gate threshold.
#
# Recorded in the COMMITTED, portable project policy (`.aw/config/project.json`) as the
# `review_findings_gate` key, read HERE and not via the XDG user config (which drops unknown keys).
# Shape `{"block_at": "high"}`, with a bare string tolerated for convenience. Deliberately NOT
# registered in `CONFIG_SCHEMA`: `project_schema.parse_portable_policy` preserves unknown keys in
# `unknown_fields` and writes them BACK on serialization, so the key round-trips safely, and the
# `dependency_schema_cutover` precedent above is likewise absent from the schema.
#
# THE DEFAULT DIVERGES FROM THAT PRECEDENT ON PURPOSE (maintainer decision, 2026-08-29). The cutover
# marker is fail-OPEN (absent means "no cutover, grandfather everything"); this key is fail-CLOSED:
# an ABSENT key means the gate is ACTIVE at `high`, so a repo gets the protection without having to
# opt in. Opting OUT is explicit, via `{"block_at": "off"}`.
# --------------------------------------------------------------------------------------

REVIEW_FINDINGS_GATE_KEY = "review_findings_gate"

#: Legal `block_at` values: a severity from `review_findings.SEVERITIES`, or `off` to disable.
REVIEW_GATE_THRESHOLDS = ("medium", "high", "blocker", "off")

#: The threshold in force when the key is absent, unreadable, or malformed (fail-CLOSED at `high`).
REVIEW_GATE_DEFAULT = "high"


def read_review_findings_gate(
    repo_root: "os.PathLike[str] | str",
) -> Optional[Dict[str, Any]]:
    """Return the `review_findings_gate` object from `.aw/config/project.json`, or None if unset.

    Never raises: a missing file, unparseable JSON, or a missing key returns None (the caller then
    applies :data:`REVIEW_GATE_DEFAULT`). A bare string is tolerated and normalized to
    ``{"block_at": <string>}``.
    """
    project_file = Path(repo_root) / ".aw" / "config" / "project.json"
    try:
        data = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    raw = data.get(REVIEW_FINDINGS_GATE_KEY)
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        return {"block_at": raw.strip()}
    return None


def findings_gate_threshold(repo_root: "os.PathLike[str] | str") -> str:
    """Return the effective gate threshold: one of :data:`REVIEW_GATE_THRESHOLDS`.

    Falls back to :data:`REVIEW_GATE_DEFAULT` (``high``) when the key is absent OR carries a value
    outside the vocabulary. A typo therefore lands on the SAFE side (still gating) rather than
    silently disabling the gate, which is the whole point of a fail-closed default; only an explicit,
    correctly spelled ``off`` disables it.
    """
    marker = read_review_findings_gate(repo_root)
    if marker is None:
        return REVIEW_GATE_DEFAULT
    value = marker.get("block_at")
    if not isinstance(value, str):
        return REVIEW_GATE_DEFAULT
    token = value.strip().lower()
    return token if token in REVIEW_GATE_THRESHOLDS else REVIEW_GATE_DEFAULT
