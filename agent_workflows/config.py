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
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

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
        "color_depth",
    }
)
_ALLOWED_REPOS_KEYS = frozenset({"search", "installed", "exclude", "ignore"})
_ALLOWED_DEFAULT_KEYS = frozenset({"backup", "prune"})

#: The tiers a user may pin ``color_depth`` to, in ladder order (spec `uonrjg` R9.3a.1/R9.3a.4).
#:
#: DUPLICATED AS LITERALS RATHER THAN IMPORTED FROM ``term``, and that is the one deliberate
#: duplication here. ``term`` resolves the depth and therefore reads this config store
#: (``term._configured_color_depth``), so importing ``term`` here would close an import cycle
#: between the two modules. The direction chosen keeps the DEPENDENCY one-way (term -> config) and
#: is the direction that cannot deadlock at import. The duplication is made SAFE rather than merely
#: accepted: ``tests/test_term.py`` asserts this tuple equals ``term.COLOR_DEPTHS`` exactly, so the
#: two cannot drift silently, which is the only real cost of duplicating a three-element enum.
COLOR_DEPTH_VALUES: Tuple[str, ...] = ("none", "16", "256")

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
    """One declarative config key: its name, type, help text, and value constraint.

    ``allowed_values`` CONSTRAINS AN ENUM-VALUED KEY, and it is declarative rather than a check
    hand-written at the setter (plan `pow5sj` OQ-01, route chosen at execution). Two reasons decided
    it. FIRST, the alternative already exists here in its hand-rolled form and shows the cost:
    ``_ALLOWED_REPOS_KEYS`` is validated by a bespoke ``if canon_key == "repos"`` branch inside
    ``set_config_value``, so every future enum key would add another branch to one function and the
    constraint would live away from the key it constrains. SECOND, a declarative field is READABLE BY
    OTHER SURFACES: ``aw config show`` and shell completion can offer the accepted values without
    re-deriving them, which a setter-local ``if`` cannot expose.

    ``None`` means unconstrained, which is every pre-existing key, so no existing entry changes
    behavior. An empty tuple would mean "no value is acceptable" and is refused as a schema defect.
    """

    key: str
    type_name: str
    description: str
    read_only: bool = False
    allowed_values: Optional[Tuple[str, ...]] = None


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
    "color_depth": ConfigKeySpec(
        key="color_depth",
        type_name="str",
        description=(
            "Pin the terminal color depth (256, 16, or none) instead of detecting it. "
            "NO_COLOR still disables color regardless of this setting."
        ),
        allowed_values=COLOR_DEPTH_VALUES,
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

    # The DECLARATIVE value constraint (`ConfigKeySpec.allowed_values`). Applied to every key that
    # declares one, so an enum key is constrained by its own schema entry rather than by a branch
    # added here. The message NAMES THE ACCEPTED SET because a bare "invalid value" leaves the user
    # guessing, and criterion A12c of spec `uonrjg` requires the set be named.
    allowed_values = spec.allowed_values
    if allowed_values is not None:
        candidate = (
            str(parsed_value if parsed_value is not None else "").strip().lower()
        )
        if candidate not in allowed_values:
            allowed = ", ".join(allowed_values)
            raise ConfigError(
                f"Invalid value for '{canon_key}': '{raw_value}'. Accepted values: {allowed}."
            )
        parsed_value = candidate

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

    # `color_depth` survives normalization ONLY when it is one of the accepted tiers. An
    # out-of-enum value (reachable only by hand-editing past `set_config_value`'s refusal) is
    # DROPPED rather than kept or raised, which is the same fail-open direction
    # `term._configured_color_depth` takes: a presentation preference must never be the reason a
    # command cannot load its config. It is absent from `default_config()` on purpose, so "unset"
    # is a real state distinct from "pinned", and detection stays the default path.
    depth_val = config.get("color_depth")
    if isinstance(depth_val, str) and depth_val.strip().lower() in COLOR_DEPTH_VALUES:
        out["color_depth"] = depth_val.strip().lower()

    # config_version is managed by migrate(); keep the current version on write.
    out["config_version"] = CONFIG_VERSION

    # `_ALLOWED_TOP_KEYS` is the ACTUAL final allowlist (R-5), applied unconditionally rather
    # than relied on implicitly: `out` is built from `default_config()`, so today nothing can
    # slip through, but this keeps that guarantee true if a future edit adds a key to
    # `default_config()` without allowlisting it. Not an assert, which `-O` would strip.
    return {key: value for key, value in out.items() if key in _ALLOWED_TOP_KEYS}


def get_color_depth(cfg: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Return the user's PINNED color depth, or ``None`` when unset or unreadable.

    THE ONE READER of the ``color_depth`` pin, called by ``term.resolve_color_depth``'s pin rung.
    It returns ``None`` (never raises, never a default tier) for every failure mode, because the
    caller is a STYLING decision: the correct response to an unreadable config is to fall through
    to detection, not to crash a command or to force a tier the user did not ask for.

    Note what this function deliberately does NOT do: it does not consult ``NO_COLOR`` and it does
    not decide whether color is on at all. Those sit ABOVE the pin in R9.3a.2's precedence chain and
    belong to ``term``; a config reader that second-guessed them would be a second definition of the
    color decision.
    """

    try:
        source = load() if cfg is None else cfg
    except Exception:
        return None
    if not isinstance(source, dict):
        return None
    value = source.get("color_depth")
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    return token if token in COLOR_DEPTH_VALUES else None


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

    out: List[str] = []
    for e in repo_setting(config, "exclude"):
        raw = str(e)
        expanded = os.path.expandvars(os.path.expanduser(raw))
        # An entry that expansion CHANGED is a path: normalize it so `~/src/x` does not come back
        # with mixed separators on Windows (a backslash home joined to `/src/x`). An unexpanded entry is left
        # byte-for-byte, since it may be an fnmatch glob.
        out.append(os.path.normpath(expanded) if expanded != raw else raw)
    return out


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
CUTOVERS_KEY = "cutovers"

# ---- TWO DIFFERENT DATES, AND CONFUSING THEM IS THE RECURRING MISTAKE ----------------------------
#
# Written out because the distinction has now cost two review round trips (most recently plan `x75obw`
# OQ-03, 2026-09-21, which was escalated to the maintainer as a contradiction and turned out not to be
# one). A cutover involves TWO dates that look alike and are not the same quantity:
#
#   1. THE FEATURE INTRODUCTION DATE - the value in this dict. It is a fact about THE TOOLKIT: "the
#      rule began to exist on this date." It is the SAME for every repository, it is history rather
#      than policy, and it CANNOT be discovered at runtime - no repository contains a record of when
#      some other codebase gained a rule. That is precisely why it is hardcoded here.
#
#   2. THE ENFORCEMENT BOUNDARY - the value stamped into `.aw/config/project.json` under
#      `cutovers.<feature>`. It is a fact about ONE REPOSITORY: "artifacts older than this are
#      grandfathered HERE." It DIFFERS per repository and it is what `check`/`lint` actually read to
#      pick the `error` tier over the advisory one.
#
# DATE 1 IS THE INPUT TO A SEARCH, NOT THE BOUNDARY, which is the part that gets misread.
# `_find_install_history_cutover` walks the target repo's `installs.jsonl` and returns the FIRST
# install at or after date 1; that RESULT becomes date 2. Worked example from this very repository:
# `spec_id6` is introduced at `2026-08-28` here, while this repo's stamped boundary is `2026-08-29`,
# because that is when this repo first installed a toolkit carrying the rule. A repository that first
# installed in October gets an October boundary from the identical `2026-08-28`.
#
# SO "the cutover must not be a hardcoded calendar date, it must be stamped into project.json
# dynamically" IS SATISFIED by adding an entry here. The enforcement boundary remains dynamic and
# per-repository; registration only supplies the one fact that cannot be computed.
#
# WHAT GOES WRONG IF YOU DO NOT REGISTER A FEATURE: `resolve_cutover_date` falls through to its
# tier-3 fail-open `None`, so the `error` tier is unreachable and the rule ships as DECORATION - it
# warns forever and never refuses. `check_engine.CARRIER_CUTOVER_DATE`'s own comment records this same
# exposure in the opposite direction.
#
# AND WHAT GOES WRONG IF YOU "FIX" THIS BY STAMPING THE CURRENT INSTALL DATE INSTEAD (rejected as
# option (b) of `x75obw` OQ-03): the boundary becomes TODAY for every existing repository, which
# permanently grandfathers every artifact that already violates the new rule. The install-history
# search exists specifically to avoid that, so replacing it with "now" is strictly worse than the
# hardcoded date it removes, not merely more literal.
#
# TO ADD A FEATURE: put its introduction date here, and let `sync_cutovers_on_install` stamp the
# per-repo boundary. Do not invent a second mechanism; three shipped features use this one.
KNOWN_FEATURE_CUTOVERS: Dict[str, str] = {
    "spec_id6": "2026-08-28",
    "dependency_schema": "2026-09-01",
    "carrier_obligations": "2026-09-19",
    # setidlen `x75obw` E-02. Registered per OQ-03's maintainer resolution (option (a)): the value
    # here is the FEATURE INTRODUCTION date (date 1 above), never the enforcement boundary, so the
    # directive "the cutover must be stamped into project.json dynamically" is satisfied by this
    # registration rather than violated by it. Leaving it OUT is the failure mode the block comment
    # above names: `resolve_cutover_date` would fail open to `None` forever, the `error` tier would
    # be unreachable, and the length rule would ship as decoration.
    "setid_length": "2026-09-23",
    # promptid6 `ubac5n` E-03. The prompts id6-in-filename adoption, the exact twin of `spec_id6`
    # above. Registered for the reason the block comment gives: WITHOUT the entry
    # `resolve_cutover_date` falls through to its tier-3 `None` in any repository that has not hand
    # written the key, and `check_engine._prompt_requires_id6` would then lean on its module fallback
    # forever instead of a per-repo stamped boundary. The value is the FEATURE INTRODUCTION date, not
    # the enforcement boundary; `sync_cutovers_on_install` stamps the per-repo boundary from it.
    "prompt_id6": "2026-09-21",
}


def _format_date(date_str: str, compact: bool = True) -> str:
    """Format a date string (ISO YYYY-MM-DD or timestamp or compact YYYYMMDD)."""
    clean = date_str.split("T")[0].strip()
    digits = clean.replace("-", "")
    if len(digits) >= 8:
        yyyy = digits[:4]
        mm = digits[4:6]
        dd = digits[6:8]
        if compact:
            return f"{yyyy}{mm}{dd}"
        return f"{yyyy}-{mm}-{dd}"
    return date_str


def _find_install_history_cutover(repo_root: Path, feature: str) -> Optional[str]:
    """Find the first install date in installs.jsonl on or after the feature introduction."""
    intro_date = KNOWN_FEATURE_CUTOVERS.get(feature)
    if not intro_date:
        return None
    intro_compact = _format_date(intro_date, compact=True)

    history_paths = [
        repo_root / ".aw" / "state" / "history" / "installs.jsonl",
        repo_root / ".aw" / "state" / "durable" / "history" / "installs.jsonl",
    ]
    entries: List[str] = []
    for hpath in history_paths:
        if hpath.is_file():
            try:
                for line in hpath.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        ts = record.get("timestamp") or record.get("last_installed_at")
                        if isinstance(ts, str) and ts.strip():
                            entries.append(ts.strip())
                    except Exception:
                        continue
            except OSError:
                pass
            if entries:
                break

    if not entries:
        return None

    # Sort timestamps chronologically
    sorted_dates = sorted(set(_format_date(e, compact=True) for e in entries))
    for d in sorted_dates:
        if d >= intro_compact:
            return d
    return None


def resolve_cutover_date(
    repo_root: "os.PathLike[str] | str",
    feature: str,
    compact: bool = True,
) -> Optional[str]:
    """Resolve the cutover date for a feature in the target repository.

    Precedence:
    (1) `.aw/config/project.json` under `cutovers.<feature>` or legacy keys.
    (2) target repository install history in `installs.jsonl` matching the install that introduced the feature.
    (3) fail-open `None`.
    """
    root = Path(repo_root)
    project_file = root / ".aw" / "config" / "project.json"
    data: Dict[str, Any] = {}
    if project_file.is_file():
        try:
            parsed = json.loads(project_file.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                data = parsed
        except (OSError, ValueError):
            data = {}

    # (1) Check cutovers.<feature>
    cutovers = data.get(CUTOVERS_KEY)
    if isinstance(cutovers, dict) and feature in cutovers:
        val = cutovers[feature]
        if isinstance(val, dict):
            val = val.get("date")
        if isinstance(val, str) and val.strip():
            return _format_date(val.strip(), compact=compact)

    # Legacy fallback for dependency_schema
    if feature == "dependency_schema" and DEPENDENCY_SCHEMA_CUTOVER_KEY in data:
        marker = data[DEPENDENCY_SCHEMA_CUTOVER_KEY]
        date = None
        if isinstance(marker, dict):
            date = marker.get("date")
        elif isinstance(marker, str):
            date = marker
        if isinstance(date, str) and date.strip():
            return _format_date(date.strip(), compact=compact)

    # (2) Check install history
    hist_cutover = _find_install_history_cutover(root, feature)
    if hist_cutover:
        return _format_date(hist_cutover, compact=compact)

    # (3) Fail-open None
    return None


def sync_cutovers_on_install(
    repo_root: "os.PathLike[str] | str",
    install_timestamp: Optional[str] = None,
) -> Dict[str, str]:
    """Stamp missing cutover dates into `.aw/config/project.json` during install or update.

    Preserves existing dates so a subsequent install/update never alters previously established
    cutover boundaries.
    """
    root = Path(repo_root)
    project_file = root / ".aw" / "config" / "project.json"
    data: Dict[str, Any] = {}
    if project_file.is_file():
        try:
            parsed = json.loads(project_file.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                data = parsed
        except (OSError, ValueError):
            data = {}

    if not data and not project_file.exists():
        return {}

    cutovers = data.get(CUTOVERS_KEY)
    if not isinstance(cutovers, dict):
        cutovers = {}
        data[CUTOVERS_KEY] = cutovers

    now_iso = _format_date(
        install_timestamp or time.strftime("%Y-%m-%d", time.gmtime()), compact=False
    )
    modified = False

    for feature, intro_date in KNOWN_FEATURE_CUTOVERS.items():
        if feature not in cutovers or not cutovers[feature]:
            # Check legacy key
            legacy_date = None
            if feature == "dependency_schema" and DEPENDENCY_SCHEMA_CUTOVER_KEY in data:
                marker = data[DEPENDENCY_SCHEMA_CUTOVER_KEY]
                if isinstance(marker, dict):
                    legacy_date = marker.get("date")
                elif isinstance(marker, str):
                    legacy_date = marker

            if legacy_date:
                cutovers[feature] = _format_date(legacy_date, compact=False)
                modified = True
            else:
                # Check history
                hist_date = _find_install_history_cutover(root, feature)
                if hist_date:
                    cutovers[feature] = _format_date(hist_date, compact=False)
                    modified = True
                else:
                    # Stamped with current install date
                    cutovers[feature] = now_iso
                    modified = True

    if modified:
        project_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_project = project_file.with_name(".tmp_project.json")
        with open(tmp_project, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp_project, project_file)

    return {k: str(v) for k, v in cutovers.items()}


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
    # Check new cutovers section first
    cutovers = data.get(CUTOVERS_KEY)
    if isinstance(cutovers, dict) and "dependency_schema" in cutovers:
        val = cutovers["dependency_schema"]
        if isinstance(val, dict):
            return val
        if isinstance(val, str) and val.strip():
            return {"date": _format_date(val.strip(), compact=False)}
    marker = data.get(DEPENDENCY_SCHEMA_CUTOVER_KEY)
    if isinstance(marker, dict):
        return marker
    # Tolerate a bare date string for convenience.
    if isinstance(marker, str) and marker.strip():
        return {"date": marker.strip()}
    return None


def dependency_cutover_date(repo_root: "os.PathLike[str] | str") -> Optional[str]:
    """Return the cutover `date` (YYYY-MM-DD) if a marker is set, else None (no cutover)."""
    resolved = resolve_cutover_date(repo_root, "dependency_schema", compact=False)
    if resolved:
        return resolved
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


# --------------------------------------------------------------------------------------
# gatekinds Order 01 (kxawm4) E-01: repository-policy release gating work kinds.
#
# Work kinds whose live items automatically carry `- Blocks-Release:` (e.g. `bug`, `security`).
# Defaults to `bug` alone, preserving existing behavior when unconfigured.
# Recorded in `.aw/config/project.json` under `release_gate_work_kinds`.
# Accepted shapes:
#   - `{"kinds": ["bug", "security"]}`
#   - `["bug", "security"]` (bare list)
#   - `"bug"` (bare string)
# Explicit empty list `[]` or `{"kinds": []}` disables auto-gating.
#
# Deliberately NOT registered in `CONFIG_SCHEMA`: `project_schema.parse_portable_policy`
# preserves unrecognized keys in `unknown_fields` and writes them BACK on serialization,
# so the key round-trips safely without a schema change (same precedent as `review_findings_gate`).
#
# Posture follows `policy_retry_budget`: malformed values or unknown kinds emit a warning
# and fall back to the default (or drop the unknown kind), never raising.
# --------------------------------------------------------------------------------------

RELEASE_GATE_WORK_KINDS_KEY = "release_gate_work_kinds"

#: Legal work kinds for release gating. Mirrored from `backlog.KINDS` to avoid importing
#: `agent_workflows.backlog` from `config` (following the `REVIEW_GATE_THRESHOLDS` precedent above,
#: which mirrors `review_findings.SEVERITIES`).
RELEASE_GATE_VALID_KINDS: FrozenSet[str] = frozenset(
    {"bug", "feature", "chore", "security", "followup"}
)

RELEASE_GATE_WORK_KINDS_DEFAULT: FrozenSet[str] = frozenset({"bug"})


def release_gate_work_kinds(
    repo_root: "os.PathLike[str] | str",
    *,
    warn: Any = None,
    allowed_kinds: Optional[Iterable[str]] = None,
) -> FrozenSet[str]:
    """Return the configured set of release-gating work kinds, or the default `frozenset({'bug'})`.

    Reads `.aw/config/project.json` under `release_gate_work_kinds`.
    Accepted shapes:
      - `{"kinds": ["bug", "security"]}`
      - `["bug", "security"]`
      - `"bug"` (or any single kind string)
    An explicit empty list `[]` (or `{"kinds": []}`) is legal and returns `frozenset()`.

    Values are lowercased, stripped, and validated against legal kinds.
    Unknown kinds are dropped with a warning naming the key, the offending kind, and the file.
    Non-list/non-dict garbage warns and falls back to `RELEASE_GATE_WORK_KINDS_DEFAULT`.
    """
    import sys as _sys

    def _emit(message: str) -> None:
        if warn is None:
            print(message, file=_sys.stderr)
        else:
            warn(message)

    project_file = Path(repo_root) / ".aw" / "config" / "project.json"
    try:
        data = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return RELEASE_GATE_WORK_KINDS_DEFAULT
    if not isinstance(data, dict):
        return RELEASE_GATE_WORK_KINDS_DEFAULT

    if RELEASE_GATE_WORK_KINDS_KEY not in data:
        return RELEASE_GATE_WORK_KINDS_DEFAULT

    raw = data.get(RELEASE_GATE_WORK_KINDS_KEY)
    if raw is None:
        return RELEASE_GATE_WORK_KINDS_DEFAULT

    valid_kinds = (
        frozenset(allowed_kinds)
        if allowed_kinds is not None
        else RELEASE_GATE_VALID_KINDS
    )

    items_to_process: List[Any]
    if isinstance(raw, dict):
        if "kinds" not in raw:
            _emit(
                f"WARNING: {RELEASE_GATE_WORK_KINDS_KEY} in {project_file} is missing 'kinds' list: {raw!r}. "
                f"Using default {sorted(RELEASE_GATE_WORK_KINDS_DEFAULT)} instead."
            )
            return RELEASE_GATE_WORK_KINDS_DEFAULT
        kinds_val = raw.get("kinds")
        if not isinstance(kinds_val, list):
            _emit(
                f"WARNING: {RELEASE_GATE_WORK_KINDS_KEY}.kinds in {project_file} is {kinds_val!r}, which is not a list. "
                f"Using default {sorted(RELEASE_GATE_WORK_KINDS_DEFAULT)} instead."
            )
            return RELEASE_GATE_WORK_KINDS_DEFAULT
        items_to_process = kinds_val
    elif isinstance(raw, list):
        items_to_process = raw
    elif isinstance(raw, str):
        token = raw.strip()
        if not token:
            _emit(
                f"WARNING: {RELEASE_GATE_WORK_KINDS_KEY} in {project_file} is empty string. "
                f"Using default {sorted(RELEASE_GATE_WORK_KINDS_DEFAULT)} instead."
            )
            return RELEASE_GATE_WORK_KINDS_DEFAULT
        items_to_process = [token]
    else:
        _emit(
            f"WARNING: {RELEASE_GATE_WORK_KINDS_KEY} in {project_file} is {raw!r}, which is not a dict, list, or string. "
            f"Using default {sorted(RELEASE_GATE_WORK_KINDS_DEFAULT)} instead."
        )
        return RELEASE_GATE_WORK_KINDS_DEFAULT

    # Explicit empty list is legal: "no kind auto-gates"
    if not items_to_process:
        return frozenset()

    result_kinds = set()
    unknown_kinds = []

    for item in items_to_process:
        if not isinstance(item, str):
            unknown_kinds.append(repr(item))
            continue
        cleaned = item.strip().lower()
        if cleaned in valid_kinds:
            result_kinds.add(cleaned)
        else:
            unknown_kinds.append(item)

    if unknown_kinds:
        for unk in unknown_kinds:
            _emit(
                f"WARNING: {RELEASE_GATE_WORK_KINDS_KEY} in {project_file} contains unknown kind {unk!r}. "
                "Dropping it."
            )

    if not result_kinds and not items_to_process:
        return frozenset()

    if not result_kinds and unknown_kinds:
        # If all specified kinds were unknown, fall back to default
        _emit(
            f"WARNING: {RELEASE_GATE_WORK_KINDS_KEY} in {project_file} has no valid kinds left after dropping unknown kinds. "
            f"Using default {sorted(RELEASE_GATE_WORK_KINDS_DEFAULT)} instead."
        )
        return RELEASE_GATE_WORK_KINDS_DEFAULT

    return frozenset(result_kinds)


# --------------------------------------------------------------------------------------
# retrytier Order 01 (y4adch) E-01/E-02: the ONE repository-policy retry budget.
#
# Spec 25kzda 2.1/5.5 declares a THREE-TIER precedence for the correction budget - CLI over
# repository policy over the default of 2 - and this key is the MIDDLE tier's home. Spec 5.5 names
# it `run.retry_budget`, so it is read as the `retry_budget` member of a `run` object rather than as
# a bare top-level key: the spec is `approved` and names a nested path, so honoring it is not a
# style choice. A bare top-level integer is ALSO tolerated for convenience, exactly as both
# precedents below tolerate a bare string, so a repository that writes the obvious flat form is not
# silently ignored.
#
# Recorded in the COMMITTED, portable project policy (`.aw/config/project.json`), read HERE and not
# via the XDG user config (which drops unknown keys). Deliberately NOT registered in `CONFIG_SCHEMA`,
# for the same documented reason the two precedents above are not: `project_schema.parse_portable_policy`
# preserves unrecognized keys in `unknown_fields` and writes them BACK on serialization, so the key
# round-trips safely without a schema change.
#
# THE FAILURE POSTURE IS A THIRD ONE, AND IT IS WRITTEN DOWN HERE SO THE NEXT KEY FOLLOWS IT RATHER
# THAN RE-DERIVING THE QUESTION (maintainer decision, 2026-09-10, recorded verbatim in plan `y4adch`
# OQ-01): "FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE."
# The cutover marker is fail-OPEN and silent; `review_findings_gate` falls back to a SAFE default and
# is also silent; NEITHER refuses and neither warns. This key falls back AND WARNS, because a retry
# budget has no safe side (a higher and a lower budget are merely different, not safer), so a silent
# fallback would override a repository that believes it set a policy with no signal anywhere.
#
# IT MUST NOT REFUSE, and the asymmetry with the CLI is DELIBERATE rather than an inconsistency to
# be tidied later: an out-of-range `--retry-budget` raises `RunFlagRefusal` and stops ONE invocation
# that typed it, whereas `.aw/config/project.json` is TRACKED and SHARED, so one typo refusing would
# break EVERY run for every human and agent in the checkout until someone fixed and committed it.
# A per-invocation mistake refuses; a shared-file mistake warns and continues.
#
# THE BOUND IS NOT DEFINED HERE. It is `run_recovery.validate_retry_budget`'s single definition
# (0..10 inclusive, executed plan `sq61qd`), reached by the caller
# (`runner_shared.resolve_retry_budget`). This accessor deliberately returns the RAW value and never
# range-checks it, so the bound cannot acquire a second copy in this file.
# --------------------------------------------------------------------------------------

RUN_POLICY_KEY = "run"

#: The member of the `run` object holding spec 5.5's repository-policy correction budget.
RUN_RETRY_BUDGET_MEMBER = "retry_budget"

#: The member of the `run` object holding the active runner conflict policy.
RUN_ON_CONFLICT_MEMBER = "on_conflict"

#: The canonical conflict resolution policies accepted in configuration.
VALID_ON_CONFLICT_POLICIES: Tuple[str, ...] = ("drop", "refuse", "force", "prompt")


def read_run_policy(
    repo_root: "os.PathLike[str] | str",
) -> Optional[Dict[str, Any]]:
    """Return the `run` policy object from `.aw/config/project.json`, or None if unset.

    Never raises: a missing file, unparseable JSON, a non-object document, or a missing key returns
    None (the caller then applies its own default). Pure read; never writes.
    """
    project_file = Path(repo_root) / ".aw" / "config" / "project.json"
    try:
        data = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    raw = data.get(RUN_POLICY_KEY)
    return raw if isinstance(raw, dict) else None


def policy_retry_budget(
    repo_root: "os.PathLike[str] | str",
    *,
    warn: Any = None,
) -> Optional[int]:
    """Spec 5.5's repository-policy retry budget, or None when this repository sets no policy.

    Returns the RAW integer as written. The 0..10 bound is NOT applied here: it has a single
    definition in `run_recovery.validate_retry_budget` and the caller
    (`runner_shared.resolve_retry_budget`) reaches it, so this layer cannot grow a second copy of it.

    READ FROM `run.retry_budget`, which is the path spec 25kzda 5.5 names. A BARE top-level integer
    under the same member name is also accepted, because a repository owner writing the obvious flat
    form should not be silently ignored; both precedents in this file tolerate a convenience shape
    the same way.

    FALLS BACK AND WARNS ON A MALFORMED VALUE, never raising (maintainer decision, 2026-09-10; see
    the section comment above for the full reasoning and for why the asymmetry with the refusing CLI
    flag is deliberate). A non-integer, a `bool`, or an unparseable value returns None, so the caller
    applies the default, AND emits one warning naming the key, the offending value, and the file, so
    the override is visible rather than silent. `warn` exists for tests and defaults to stderr.
    """
    import sys as _sys

    def _emit(message: str) -> None:
        if warn is None:
            print(message, file=_sys.stderr)
        else:
            warn(message)

    project_file = Path(repo_root) / ".aw" / "config" / "project.json"
    run_policy = read_run_policy(repo_root)
    if run_policy is not None and RUN_RETRY_BUDGET_MEMBER in run_policy:
        raw = run_policy.get(RUN_RETRY_BUDGET_MEMBER)
        where = f"{RUN_POLICY_KEY}.{RUN_RETRY_BUDGET_MEMBER}"
    else:
        try:
            data = json.loads(project_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or RUN_RETRY_BUDGET_MEMBER not in data:
            return None
        raw = data.get(RUN_RETRY_BUDGET_MEMBER)
        where = RUN_RETRY_BUDGET_MEMBER

    if raw is None:
        # An explicit null is "no policy set", which is a normal way to clear a key, not an error.
        return None
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw
    _emit(
        f"WARNING: {where} in {project_file} is {raw!r}, which is not an integer. "
        f"Ignoring it and using the default retry budget instead. "
        f"Fix the value in that file to make the repository policy take effect."
    )
    return None


def policy_on_conflict(
    repo_root: "os.PathLike[str] | str",
    *,
    warn: Any = None,
) -> Optional[str]:
    """The repository or user policy for handling active runner conflicts, or None if unset.

    Precedence:
    1. Project policy: ``.aw/config/project.json`` at ``run.on_conflict``
    2. Project policy (flat): ``.aw/config/project.json`` at ``on_conflict``
    3. User config: ``$XDG_CONFIG_HOME/agent-workflows/config.json`` at ``run.on_conflict``,
       ``defaults.on_conflict``, or ``on_conflict``

    Returns one of ('drop', 'refuse', 'force', 'prompt') or None. Normalizes 'ask' to 'prompt'.
    Warns on malformed values and returns None so the default ('drop') applies.
    """
    import sys as _sys

    def _emit(message: str) -> None:
        if warn is None:
            print(message, file=_sys.stderr)
        else:
            warn(message)

    project_file = Path(repo_root) / ".aw" / "config" / "project.json"
    run_policy = read_run_policy(repo_root)
    raw = None
    where = None

    if run_policy is not None and RUN_ON_CONFLICT_MEMBER in run_policy:
        raw = run_policy.get(RUN_ON_CONFLICT_MEMBER)
        where = f"{RUN_POLICY_KEY}.{RUN_ON_CONFLICT_MEMBER} in {project_file}"
    else:
        try:
            data = json.loads(project_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and RUN_ON_CONFLICT_MEMBER in data:
                raw = data.get(RUN_ON_CONFLICT_MEMBER)
                where = f"{RUN_ON_CONFLICT_MEMBER} in {project_file}"
        except (OSError, ValueError):
            pass

    if raw is None:
        try:
            upath = config_path()
            if upath.is_file():
                udata = json.loads(upath.read_text(encoding="utf-8"))
                if isinstance(udata, dict):
                    if (
                        isinstance(udata.get("run"), dict)
                        and RUN_ON_CONFLICT_MEMBER in udata["run"]
                    ):
                        raw = udata["run"].get(RUN_ON_CONFLICT_MEMBER)
                        where = f"run.{RUN_ON_CONFLICT_MEMBER} in {upath}"
                    elif (
                        isinstance(udata.get("defaults"), dict)
                        and RUN_ON_CONFLICT_MEMBER in udata["defaults"]
                    ):
                        raw = udata["defaults"].get(RUN_ON_CONFLICT_MEMBER)
                        where = f"defaults.{RUN_ON_CONFLICT_MEMBER} in {upath}"
                    elif RUN_ON_CONFLICT_MEMBER in udata:
                        raw = udata.get(RUN_ON_CONFLICT_MEMBER)
                        where = f"{RUN_ON_CONFLICT_MEMBER} in {upath}"
        except (OSError, ValueError):
            pass

    if raw is None:
        return None

    if not isinstance(raw, str):
        _emit(
            f"WARNING: {where} is {raw!r}, which is not a string. "
            f"Ignoring it and using the default conflict policy ('drop') instead. "
            f"Fix the value in that file to make the policy take effect."
        )
        return None

    val = raw.strip().lower()
    if val == "ask":
        val = "prompt"

    if val in VALID_ON_CONFLICT_POLICIES:
        return val

    _emit(
        f"WARNING: {where} is {raw!r}, which is not one of {VALID_ON_CONFLICT_POLICIES}. "
        f"Ignoring it and using the default conflict policy ('drop') instead. "
        f"Fix the value in that file to make the policy take effect."
    )
    return None


# --------------------------------------------------------------------------------------
# setidlen Order 01 (x75obw) E-01: the ONE setid LENGTH policy.
#
# TWO SEPARATE THINGS LIVE IN TWO SEPARATE PLACES, and keeping them apart is the whole point of this
# section. The THRESHOLDS (how long a setid may be) are POLICY and live under the optional `setids`
# object in `.aw/config/project.json`. The ENFORCEMENT BOUNDARY (which artifacts the error tier may
# refuse) is a CUTOVER and lives under `cutovers.setid_length`, resolved by the ONE generic
# `resolve_cutover_date` above. There is deliberately NO `setids.cutover_date`: a second place for a
# cutover date is how the two drift, and only `cutovers.<feature>` is resolvable by the shipped
# resolver (plan `x75obw` review, finding PR-401).
#
# THERE IS ALSO NO SECOND STAMPER. `sync_cutovers_on_install` above already stamps every feature in
# `KNOWN_FEATURE_CUTOVERS` (where `setid_length` is now registered), already preserves an existing
# date, and already writes atomically, so a `stamp_setid_cutover_if_missing` helper would be a second
# writer to one JSON file. Do not add one.
#
# THE ERROR THRESHOLD HAS ZERO MARGIN, which is the single most consequential fact about these
# numbers. The longest setid in this repository is `research-prompt-pipeline` at EXACTLY 24
# characters (re-measured at execution 2026-09-23 over 749 unique declared setids: 713 at <= 14, 36
# in the 15-24 band, 0 over 24). So 24 was chosen to sit exactly AT the existing maximum, not with
# room to spare, and the comparison must be `> max_length` rather than `>=`: an off-by-one hard-fails
# a live record. The tests pin 24-conforms / 25-errors for that reason.
#
# Deliberately NOT registered in `CONFIG_SCHEMA` (the XDG user config), for the reason all three
# precedents above record: this is COMMITTED, PORTABLE project policy, and
# `project_schema.parse_portable_policy` round-trips the key through `unknown_fields` regardless.
# `ProjectPolicySchema` does recognize `setids` explicitly (E-01), so a repository that sets it keeps
# it through a policy rewrite rather than relying on the unknown-field path.
# --------------------------------------------------------------------------------------

SETID_POLICY_KEY = "setids"

#: The setid length a Set id is strongly PREFERRED to stay within. Longer is a WARNING, not a refusal.
SETID_WARN_LENGTH_DEFAULT = 14

#: The setid length above which a post-cutover artifact is REFUSED (`error`). See the zero-margin
#: paragraph above: this equals the longest setid that exists, so the comparison is strictly `>`.
SETID_MAX_LENGTH_DEFAULT = 24

#: Whether the length rules apply to PRE-cutover artifacts too. Default False (grandfather history).
SETID_STRICT_DEFAULT = False


@dataclass(frozen=True)
class SetidPolicy:
    """The effective setid length policy for one repository.

    ``cutover_date`` is the compact ``YYYYMMDD`` ENFORCEMENT BOUNDARY resolved through the generic
    :func:`resolve_cutover_date`, or None when this repository has none (fail-OPEN: every artifact is
    grandfathered, so the `error` tier is unreachable until an install stamps the date). ``strict``
    overrides that grandfathering.
    """

    warn_length: int = SETID_WARN_LENGTH_DEFAULT
    max_length: int = SETID_MAX_LENGTH_DEFAULT
    strict: bool = SETID_STRICT_DEFAULT
    cutover_date: Optional[str] = None

    def tier_for(self, setid: str) -> Optional[str]:
        """The severity tier a setid's LENGTH alone earns: ``"error"``, ``"warning"``, or None.

        Pure length judgement with NO date/grandfathering in it: the caller owns the cutover
        decision, because a setid is a SHARED label spanning artifacts with different dates and only
        the caller knows which ARTIFACT it is judging (plan `x75obw` OQ-04).
        """
        length = len(setid or "")
        if length > self.max_length:
            return "error"
        if length > self.warn_length:
            return "warning"
        return None

    def applies_to_artifact_date(self, artifact_date: Optional[str]) -> bool:
        """True when the length rules apply to an artifact carrying this compact ``YYYYMMDD`` date.

        ``strict`` applies them to EVERYTHING. Otherwise an absent cutover grandfathers everything
        (fail-open), and an artifact with no parseable date is treated as PRE-cutover, which mirrors
        `_spec_requires_id6` and `_citation_anchor_applies`: a missing date is its own defect owned by
        another rule, never a second consequence invented here.
        """
        if self.strict:
            return True
        if not self.cutover_date:
            return False
        if not artifact_date:
            return False
        return str(artifact_date) >= str(self.cutover_date)


def read_setid_policy_object(
    repo_root: "os.PathLike[str] | str",
) -> Optional[Dict[str, Any]]:
    """Return the raw `setids` object from `.aw/config/project.json`, or None if unset.

    Never raises: a missing file, unparseable JSON, a non-object document, or a missing key returns
    None (the caller then applies the documented defaults). Pure read; never writes.
    """
    project_file = Path(repo_root) / ".aw" / "config" / "project.json"
    try:
        data = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    raw = data.get(SETID_POLICY_KEY)
    return raw if isinstance(raw, dict) else None


def get_setid_policy(repo_root: "os.PathLike[str] | str") -> SetidPolicy:
    """The effective :class:`SetidPolicy` for a repository (thresholds + resolved cutover boundary).

    Thresholds come from the optional `setids` object, defaulting to
    (:data:`SETID_WARN_LENGTH_DEFAULT`, :data:`SETID_MAX_LENGTH_DEFAULT`,
    :data:`SETID_STRICT_DEFAULT`). A malformed threshold falls back to its default SILENTLY, which
    follows the cutover/`review_findings_gate` precedents rather than `policy_retry_budget`'s warning
    posture: both fallbacks here land on the SAFE side (the shipped, documented contract), so there is
    no override of a repository's intent to announce.

    The cutover is DELEGATED to :func:`resolve_cutover_date` with the ``setid_length`` feature key.
    This function adds NO second reader and the module adds NO second stamper.
    """
    raw = read_setid_policy_object(repo_root) or {}

    def _int(key: str, default: int) -> int:
        value = raw.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            return default
        return value

    strict_raw = raw.get("strict", SETID_STRICT_DEFAULT)
    strict = strict_raw if isinstance(strict_raw, bool) else SETID_STRICT_DEFAULT

    warn_length = _int("warn_length", SETID_WARN_LENGTH_DEFAULT)
    max_length = _int("max_length", SETID_MAX_LENGTH_DEFAULT)
    if max_length < warn_length:
        # An inverted pair would make the WARNING band empty and the error tier fire inside it; the
        # documented contract is warn <= max, so fall back to the shipped pair rather than enforcing
        # a policy nobody can have meant.
        warn_length, max_length = SETID_WARN_LENGTH_DEFAULT, SETID_MAX_LENGTH_DEFAULT

    return SetidPolicy(
        warn_length=warn_length,
        max_length=max_length,
        strict=strict,
        cutover_date=resolve_cutover_date(repo_root, "setid_length", compact=True),
    )


def validate_setid_length_for_authoring(
    repo_root: "os.PathLike[str] | str",
    setid: Optional[str],
    *,
    verb: str,
) -> Tuple[Optional[str], Optional[str]]:
    """The ONE authoring-time setid length guard. Returns ``(error, warning)``, either may be None.

    setidlen `x75obw` E-06. ONE validator, called by every `--set`-taking creation/regrouping verb
    (`aw ipd scaffold`, `aw backlog new`, `aw research new`, `aw group`), rather than a length
    comparison copied into each. That is not tidiness: the maximum has ZERO MARGIN (the longest real
    setid is exactly 24), so four independent comparisons are four chances to disagree about whether
    24 conforms, and only one of those four disagreements has to be wrong to refuse a live record.

    NO CUTOVER IS CONSULTED, DELIBERATELY. A cutover exists to grandfather artifacts that ALREADY
    EXIST; this guard runs when a human or agent is choosing a NEW setid, which is by definition
    post-cutover whatever the boundary says. Applying the boundary here would let a repository with no
    stamped date mint unbounded setids forever, which is the decoration failure mode
    `KNOWN_FEATURE_CUTOVERS` documents.

    ``error`` is a refusal (over `max_length`); ``warning`` is advice (over `warn_length`) and the verb
    MUST still proceed. An empty/None setid returns `(None, None)`: whether `--set` is required is each
    verb's own business, and several legitimately default it.

    NOTE `aw specs new` is EXCLUDED and has no call site, which is correct rather than an omission: it
    takes no `--set` flag at all (`specs.run_new` passes `set_id=id6`, so a standalone spec's setid is
    ALWAYS its own 6-character id6) and a guard there would be unreachable code.
    """
    token = (setid or "").strip()
    if not token:
        return None, None
    policy = get_setid_policy(repo_root)
    length = len(token)
    if length > policy.max_length:
        return (
            f"{verb}: --set {token!r} is {length} characters, over the "
            f"{policy.max_length}-character maximum for a setid "
            f"(<= {policy.warn_length} is strongly preferred); choose a shorter Set id",
            None,
        )
    if length > policy.warn_length:
        return (
            None,
            f"{verb}: --set {token!r} is {length} characters; a setid of "
            f"<= {policy.warn_length} characters is strongly preferred "
            f"(over {policy.max_length} is refused)",
        )
    return None, None
