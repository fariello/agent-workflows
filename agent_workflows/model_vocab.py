"""Data-driven research model vocabulary loader and configuration manager.

Provides three-layer additive vocabulary resolution:
1. Shipped package default (`agent_workflows/data/research-models.toml`).
2. Target repository layer (`.aw/config/research-models.toml`).
3. User configuration layer (`<config_dir>/research-models.toml`).

Merging is strictly ADD-ONLY (a layer can add tokens and normalizations, but cannot delete
package tokens, preventing existing documents from becoming unparseable).

Per-repo-root caching is provided so hot scan loops avoid redundant disk stats.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple, Union

from agent_workflows import leak_sanitizer as _ls

# Path relative to package root
_PACKAGE_DATA_FILE = Path(__file__).resolve().parent / "data" / "research-models.toml"
REPO_CONFIG_REL = ".aw/config/research-models.toml"
LEGACY_REPO_CONFIG_REL = ".agents/research-models.toml"
USER_CONFIG_FILENAME = "research-models.toml"

_SYNTAX_RE = re.compile(r"^[a-z0-9-]+$")

# Process-level cache: resolved_repo_root_str_or_None -> (models, normalizations)
_CACHE: Dict[Optional[str], Tuple[FrozenSet[str], Dict[str, str]]] = {}
_PKG_CACHE: Optional[Tuple[List[str], Dict[str, str]]] = None


def _user_config_dir() -> Path:
    try:
        from agent_workflows import config as _config

        return _config.config_dir()
    except Exception:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        return Path(base).expanduser() / "agent-workflows"


def _cache_key(repo_root: Optional[Union[str, Path]]) -> Optional[str]:
    if repo_root is None:
        return None
    return str(Path(repo_root).resolve())


def invalidate_cache(repo_root: Optional[Union[str, Path]] = None) -> None:
    """Invalidate vocabulary cache for ``repo_root``, or clear entire cache if None."""
    global _PKG_CACHE
    if repo_root is None:
        _CACHE.clear()
        _PKG_CACHE = None
    else:
        key = _cache_key(repo_root)
        _CACHE.pop(key, None)


def _read_layer_file(path: Path) -> Tuple[List[str], Dict[str, str]]:
    """Parse a research-models.toml file using the minimal TOML reader."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], {}
    lists = _ls._parse_simple_toml_lists(text)
    pairs = _ls._parse_simple_toml_pairs(text, section="normalizations")
    return lists.get("models", []), pairs


def _get_pkg_defaults() -> Tuple[List[str], Dict[str, str]]:
    global _PKG_CACHE
    if _PKG_CACHE is None:
        _PKG_CACHE = _read_layer_file(_PACKAGE_DATA_FILE)
    return _PKG_CACHE


def load(
    repo_root: Optional[Union[str, Path]] = None,
    *,
    user_config_dir: Optional[Union[str, Path]] = None,
) -> Tuple[FrozenSet[str], Dict[str, str]]:
    """Load and merge the effective model vocabulary across layers.

    Precedence (additive):
    1. Package default: agent_workflows/data/research-models.toml
    2. Repo layer: <repo_root>/.aw/config/research-models.toml (if repo_root provided)
    3. User layer: <user_config_dir>/research-models.toml

    When ``repo_root`` is None, ONLY the package default is loaded (never a cwd climb).
    """
    key = _cache_key(repo_root)
    # If user_config_dir is explicitly specified (e.g. for testing), bypass cache
    if user_config_dir is None and key in _CACHE:
        return _CACHE[key]

    # Layer 1: Package default
    pkg_models, pkg_norms = _get_pkg_defaults()
    merged_models = {m.lower() for m in pkg_models}
    merged_norms = {k.lower(): v.lower() for k, v in pkg_norms.items()}

    # Layer 2: Target repository layer (only when repo_root is explicitly provided)
    if repo_root is not None:
        p_root = Path(repo_root)
        repo_cfg = p_root / REPO_CONFIG_REL
        if not repo_cfg.is_file():
            legacy_cfg = p_root / LEGACY_REPO_CONFIG_REL
            if legacy_cfg.is_file():
                repo_cfg = legacy_cfg
        if repo_cfg.is_file():
            r_models, r_norms = _read_layer_file(repo_cfg)
            merged_models.update(m.lower() for m in r_models)
            merged_norms.update({k.lower(): v.lower() for k, v in r_norms.items()})

    # Layer 3: User layer
    u_dir = Path(user_config_dir) if user_config_dir is not None else _user_config_dir()
    u_cfg = u_dir / USER_CONFIG_FILENAME
    if u_cfg.is_file():
        u_models, u_norms = _read_layer_file(u_cfg)
        merged_models.update(m.lower() for m in u_models)
        merged_norms.update({k.lower(): v.lower() for k, v in u_norms.items()})

    res = (frozenset(merged_models), merged_norms)
    if user_config_dir is None:
        _CACHE[key] = res
    return res


def _render_toml(models: List[str], normalizations: Dict[str, str]) -> str:
    lines = [
        "# Research model vocabulary overrides (tracked, travels with the repo).",
        "#",
        "# Layers are additive on top of the package default: models and normalizations",
        "# added here extend the recognized vocabulary for this repository.",
        "# Managed by `aw research add-model`.",
        "",
        "models = [",
    ]
    for m in sorted(set(models)):
        lines.append(f'  "{m}",')
    lines.append("]")
    lines.append("")
    lines.append("[normalizations]")
    for k in sorted(normalizations):
        lines.append(f'{k} = "{normalizations[k]}"')
    lines.append("")
    return "\n".join(lines)


def run_add_model(args: argparse.Namespace) -> int:
    """Implement `aw research add-model <token> [--normalize-from <spelling>] [--apply]`."""
    from agent_workflows import artifact_core as _core
    from agent_workflows.project_context import resolve_verb_repo_root

    raw_token = getattr(args, "token", "") or ""
    token = raw_token.strip().lower()
    if not token or not _SYNTAX_RE.match(token):
        print(f"error: malformed model token '{raw_token}'; must match [a-z0-9-]+")
        return 2

    raw_norm = getattr(args, "normalize_from", None)
    norm_from = None
    if raw_norm is not None:
        norm_from = raw_norm.strip().lower()
        if not norm_from or not _SYNTAX_RE.match(norm_from):
            print(
                f"error: malformed normalize-from token '{raw_norm}'; must match [a-z0-9-]+"
            )
            return 2

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    target_path = repo_root / REPO_CONFIG_REL

    existing_models: List[str] = []
    existing_norms: Dict[str, str] = {}
    if target_path.is_file():
        existing_models, existing_norms = _read_layer_file(target_path)

    models_list = list(existing_models)
    if token not in models_list:
        models_list.append(token)

    norms_map = dict(existing_norms)
    if norm_from:
        norms_map[norm_from] = token

    rendered = _render_toml(models_list, norms_map)

    if not getattr(args, "apply", False):
        print(f"Would write to {target_path}:")
        print(rendered)
        return 0

    _core.atomic_write(target_path, rendered)
    invalidate_cache(repo_root)
    print(f"blessed model '{token}' in {target_path}")
    return 0
