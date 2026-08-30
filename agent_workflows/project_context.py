"""Deterministic, side-effect-free AW project context resolver (IPD 20260809-awlayout-01).

This module implements the canonical context and logical-root resolver specified by
``.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`` Section 9 & 17.

Invariants:
- PURE: ZERO filesystem writes, directory creation, or Git mutation.
- FAIL-CLOSED: Rejects ambiguous/conflicting authoritative configs, path traversals, and symlink escapes.
- DETERMINISTIC: Repeated calls with identical inputs return byte-for-byte identical outputs.
- PROVENANCE: Tracks exact precedence level for every resolved field across all 6 precedence levels.
"""

from __future__ import annotations

import json
import functools
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_workflows.project_schema import (
    DELIVERY_MODES,
    RECORDS_BACKENDS,
    DeliveryMode,
    DurabilityState,
    GitPolicy,
    LogicalRoot,
    PrecedenceLevel,
    Preset,
    ProjectContext,
    ProjectRole,
    Provenance,
    RecordsBackend,
    RootClass,
    migrate_legacy_config,
)


class ProjectContextError(Exception):
    """Base exception for project context resolution failures."""

    pass


class ConflictingConfigurationError(ProjectContextError):
    """Raised when conflicting authoritative configurations exist at the same precedence level."""

    pass


class PathSecurityError(ProjectContextError):
    """Raised when path traversal, containment violation, or symlink escape is detected."""

    pass


# Explicit FLOOR only: the fallback framework version used when NO baked `.aw/system/VERSION` is
# present (see the resolution below - a real baked VERSION always wins). This is deliberately a
# static floor, NOT a second source of truth: the authoritative version is the git-tag resolver
# (`versioning.resolve_version`) baked into `.aw/system/VERSION` at release time (RELEASING.md
# bake-then-tag). Keep this floor at the last released MAJOR.MINOR baseline; do not chase the
# resolver here (importing `versioning` at module load would add a fragile import-time dependency
# for a value only used when the baked file is missing). Drift is bounded and harmless: it is a
# floor for an un-baked tree, overridden by the baked file in every real install. (Order 05 / S6-V02.)
DEFAULT_FRAMEWORK_VERSION = "1.2.1"
DEFAULT_ENABLED_HOSTS = ["opencode", "claude", "antigravity"]


def _canonical_path(path: str | Path) -> str:
    """Resolve symlinks and normalize to a canonical absolute posix string without mutating fs."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    try:
        resolved = p.resolve()
        return resolved.as_posix()
    except Exception:
        return os.path.abspath(p.as_posix()).replace("\\", "/")


def _is_safe_subpath(child_path: str, parent_path: str) -> bool:
    """Check if child_path is strictly inside parent_path or equal to it."""
    c = Path(_canonical_path(child_path))
    p = Path(_canonical_path(parent_path))
    try:
        c.relative_to(p)
        return True
    except ValueError:
        return False


def _git_index_stamp(repo_abs: str) -> tuple:
    """Cheap fingerprint of the Git index: (mtime_ns, size) of .git/index, or () if absent.

    This is the CACHE KEY for the tracked-file listing. `git add` rewrites .git/index, so the
    stamp changes and the cache misses -- which is why the policy gate still fires on a newly
    staged forbidden file (tests/test_project_layout.py::test_e01 asserts exactly that).
    """
    idx = os.path.join(repo_abs, ".git", "index")
    try:
        st = os.stat(idx)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return ()


@functools.lru_cache(maxsize=32)
def _git_cached_entries(repo_abs: str, _stamp: tuple):
    """Parsed `git ls-files -s --cached` as [(rel_path, is_symlink)], or None if git failed.

    PERF (awfindperf): the policy gate runs ~30x per command (once per artifact type per
    read-path lookup) and each run forked a `git ls-files` subprocess -- ~0.9s of `aw find`.
    The listing is identical for an unchanged index, so it is cached on the index stamp.
    `_stamp` participates in the cache KEY only, to force invalidation; the body ignores it.
    `-s` yields the mode so symlinks (120000) are identifiable: a symlink may resolve to a
    forbidden target under an unrelated basename and must always be canonicalized.
    """
    import subprocess

    res = subprocess.run(
        ["git", "ls-files", "-s", "--cached"],
        cwd=repo_abs,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return None
    entries: List[tuple] = []
    for line in res.stdout.splitlines():
        if not line:
            continue
        meta, sep, path_part = line.partition(chr(9))
        if not path_part:
            entries.append((line, True))
            continue
        mode = meta.split(" ", 1)[0] if meta else ""
        entries.append((path_part, mode == "120000"))
    return entries


def validate_physical_git_policy(
    target_repo: str, physical_classes: Dict[str, str]
) -> None:
    """Enforce physical Git policy invariants (spec Section 4.1 & 5.2).
    config_local (config/local.json) and state_runtime (state/runtime/) MUST NOT
    be tracked or staged in any Git repository.
    Raises PathSecurityError if any forbidden path is tracked or staged in target Git.
    """
    repo_abs = _canonical_path(target_repo)
    git_dir = os.path.join(repo_abs, ".git")
    if not os.path.exists(git_dir):
        return

    try:
        cached_entries = _git_cached_entries(repo_abs, _git_index_stamp(repo_abs))
        if cached_entries is not None:
            # PERF (awfindperf): canonicalize the two forbidden TARGETS once, then compare each
            # tracked file by string. The previous form called _canonical_path()
            # (Path.resolve() -> lstat) and _is_safe_subpath() for EVERY tracked file; on a
            # ~1,400-file repo that cost >1M lstat calls per `aw find` (the resolver runs ~30x
            # per command), which was ~90% of its runtime.
            #
            # Semantics are preserved exactly: config_local must match exactly; state_runtime
            # matches itself or any descendant. Comparison is done on CANONICAL absolute paths
            # (same basis as before), so a symlinked repo or tmpdir behaves identically -- we
            # canonicalize each tracked path only when a cheap basename prefilter says it could
            # possibly match, so the expensive call happens O(candidates) not O(tracked files).
            config_local_path = physical_classes.get(RootClass.CONFIG_LOCAL.value)
            state_runtime_path = physical_classes.get(RootClass.STATE_RUNTIME.value)
            if not config_local_path and not state_runtime_path:
                return
            cl_canon = _canonical_path(config_local_path) if config_local_path else None
            sr_canon = (
                _canonical_path(state_runtime_path) if state_runtime_path else None
            )
            # Cheap prefilter: only a tracked path whose basename matches the forbidden file's
            # basename (config_local), or which lies under the runtime dir's basename, can match.
            cl_base = os.path.basename(cl_canon) if cl_canon else None
            sr_base = os.path.basename(sr_canon.rstrip("/")) if sr_canon else None
            for rel_path, is_symlink in cached_entries:
                rel_norm = rel_path.replace(os.sep, "/")
                base = rel_norm.rsplit("/", 1)[-1]
                may_be_config = cl_base is not None and base == cl_base
                may_be_runtime = sr_base is not None and (
                    f"/{sr_base}/" in f"/{rel_norm}" or rel_norm.endswith(f"/{sr_base}")
                )
                # A SYMLINK can resolve to a forbidden target under any basename, so the cheap
                # basename prefilter is not sound for it: always canonicalize a symlink. Regular
                # files cannot alias another path, so the prefilter is sound for them.
                if not is_symlink and not may_be_config and not may_be_runtime:
                    continue
                abs_path = _canonical_path(os.path.join(repo_abs, rel_path))
                if cl_canon and abs_path == cl_canon:
                    raise PathSecurityError(
                        f"Git policy violation: local config file '{rel_path}' is tracked or staged in Git"
                    )
                if sr_canon and (
                    abs_path == sr_canon or _is_safe_subpath(abs_path, sr_canon)
                ):
                    raise PathSecurityError(
                        f"Git policy violation: runtime state path '{rel_path}' is tracked or staged in Git"
                    )
    except PathSecurityError:
        raise
    except Exception:
        pass


def _check_path_security(path_str: str, label: str) -> str:
    """Validate path against path traversal attacks."""
    if ".." in path_str.split("/") or ".." in path_str.split("\\"):
        raise PathSecurityError(
            f"Path security error in {label}: traversal '..' detected in {path_str}"
        )
    return _canonical_path(path_str)


def get_default_aw_home() -> str:
    """Determine platform default AW_HOME (spec Section 7.1)."""
    env_home = os.environ.get("AW_HOME")
    if env_home:
        return _canonical_path(env_home)
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return _canonical_path(Path(xdg_config) / "agent-workflows")
    return _canonical_path(Path.home() / ".aw")


def _read_json_file(path_str: str) -> Optional[Dict[str, Any]]:
    """Safe read of JSON file; returns None if missing or unreadable."""
    p = Path(path_str)
    if not p.is_file():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return None


def _is_repos_schema_mapping(value: Dict[str, Any]) -> bool:
    """True when a dict-valued user-config ``repos`` is the schema mapping, not a binding table.

    User config schema version 2 nests repository settings under ``repos`` as
    ``{search, installed, exclude, ignore}``. Every key of the schema mapping is one of those
    four names, whereas a per-repo binding table is keyed by ABSOLUTE REPO PATH, so the two are
    distinguishable without importing the config module (this file reads raw JSON by design).
    An empty dict is treated as the schema mapping: it carries no bindings either way.
    """

    from agent_workflows.config import _ALLOWED_REPOS_KEYS

    return all(key in _ALLOWED_REPOS_KEYS for key in value)


def _find_git_root(start_dir: str) -> Optional[str]:
    """Find the Git root directory by walking up from start_dir without subprocess."""
    curr = Path(start_dir).resolve()
    while curr != curr.parent:
        git_dir = curr / ".git"
        if git_dir.exists():
            return curr.as_posix()
        curr = curr.parent
    return None


def find_project_root(start: Optional[str | Path] = None) -> Optional[Path]:
    """Climb from ``start`` (default cwd) for the nearest ancestor that IS an AW project root.

    Returns the first directory (``start`` itself or an ancestor) that contains a ``.aw/`` or a
    legacy ``.agents/`` marker directory, else ``None``. Git-style upward walk (like
    ``_find_git_root``), so a repo-scoped ``aw`` verb works from any subdirectory. Pure and
    side-effect-free; symlink-safe (paths are resolved). git presence is NOT a marker: a ``.aw/``
    tree can exist without git, and a bare ``.git`` ancestor with no AW marker is NOT an AW project
    (IPD awretrofit Order 06, OQ-01).
    """

    curr = Path(start).resolve() if start is not None else Path.cwd().resolve()
    while True:
        if _is_project_marker(curr / ".aw") or _is_project_marker(
            curr / ".agents", legacy=True
        ):
            return curr
        if curr == curr.parent:  # reached the filesystem root
            return None
        curr = curr.parent


def _is_project_marker(marker: Path, legacy: bool = False) -> bool:
    """True if ``marker`` is a REAL AW project root dir, not a stray nested one.

    A genuine ``.aw/`` project root holds at least one DURABLE class dir (``system``/``records``/
    ``config``); a stray runtime ``.aw/`` (e.g. one accidentally scaffolded under ``.aw/state/``)
    typically holds only ``state`` and MUST NOT be mistaken for the root. The legacy ``.agents/``
    root holds ``workflows``/``plans``/``docs``. Requiring a durable child avoids the false positive
    where a bare ``.aw`` dir appears nested inside the tree (IPD awretrofit Order 06).
    """

    if not marker.is_dir():
        return False
    if legacy:
        anchors = ("workflows", "plans", "docs", "prompts", "comms", "backlog")
    else:
        anchors = ("system", "records", "config")
    return any((marker / a).is_dir() for a in anchors)


def resolve_verb_repo_root(explicit_dir: Optional[str] = None) -> Path:
    """Resolve the repo root a repo-scoped ``aw`` verb should operate on (IPD awretrofit Order 06).

    - An EXPLICIT ``--dir`` is honored verbatim (resolved, no climb) - the operator asked for it.
    - Otherwise CLIMB from cwd via ``find_project_root``; if an AW project root is found, use it (so
      the verb works from any subdirectory, git-style).
    - If no project root is found, fall through to cwd (the caller then emits the no-project message
      via ``no_project_message`` rather than printing a silent empty result).
    """

    if explicit_dir:
        return Path(explicit_dir).expanduser().resolve()
    root = find_project_root()
    return root if root is not None else Path.cwd().resolve()


def no_project_message(verb: str) -> str:
    """The verbose 'no AW project found' message a repo-scoped verb prints instead of empty output.

    Emitted when the operator did not pass ``--dir`` and no ``.aw/``/``.agents/`` marker exists at cwd
    or any ancestor (IPD awretrofit Order 06). Names the verb, what was checked, and the two fixes.
    """

    return (
        f"aw {verb}: no AW project found here.\n"
        f"Checked {Path.cwd()} and its parents for a .aw/ (or legacy .agents/) project directory.\n"
        f"Are you inside your repository? cd into the repo (or a subdirectory of it), "
        f"or pass --dir <repo>."
    )


def is_project_dir(repo_root: str | Path) -> bool:
    """True if ``repo_root`` is (or contains) an AW project marker - i.e. a real project, not a bare
    directory with nothing to survey. Used by repo-scoped verbs to decide between running and
    emitting ``no_project_message`` (IPD awretrofit Order 06)."""

    p = Path(repo_root)
    return _is_project_marker(p / ".aw") or _is_project_marker(
        p / ".agents", legacy=True
    )


def _derive_project_id(target_repo: str) -> str:
    """Derive deterministic project ID from target_repo path."""
    repo_name = Path(target_repo).name or "project"
    clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", repo_name).strip("-").lower()
    import hashlib

    path_hash = hashlib.sha256(target_repo.encode("utf-8")).hexdigest()[:6]
    return f"{clean_slug}-{path_hash}"


def redact_public_context(ctx_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Redact absolute machine-local paths and sensitive data from context dictionary (spec Section 9 & Order 02 E-05)."""
    import copy

    d = copy.deepcopy(ctx_dict)

    if "target_repo" in d:
        d["target_repo"] = "<REDACTED_LOCAL_PATH>"
    if "effective_aw_home" in d:
        d["effective_aw_home"] = "<REDACTED_LOCAL_PATH>"

    if "logical_roots" in d and isinstance(d["logical_roots"], dict):
        for k in d["logical_roots"]:
            d["logical_roots"][k] = "<REDACTED_LOCAL_PATH>"

    if "physical_classes" in d and isinstance(d["physical_classes"], dict):
        for k in d["physical_classes"]:
            d["physical_classes"][k] = "<REDACTED_LOCAL_PATH>"

    if "permitted_commit_destinations" in d and isinstance(
        d["permitted_commit_destinations"], dict
    ):
        for k, v in d["permitted_commit_destinations"].items():
            if v:
                d["permitted_commit_destinations"][k] = "<REDACTED_LOCAL_PATH>"

    if "provenance" in d and isinstance(d["provenance"], dict):
        for field, prov in d["provenance"].items():
            if isinstance(prov, dict) and "detail" in prov:
                val = str(prov["detail"])
                if (
                    "/" in val
                    or "\\" in val
                    or "~" in val
                    or "home" in val.lower()
                    or "user" in val.lower()
                ):
                    prov["detail"] = "<REDACTED_LOCAL_PATH>"

    return d


def resolve_project_context(
    target_repo: Optional[str] = None,
    aw_home: Optional[str] = None,
    delivery_mode: Optional[str] = None,
    records_backend: Optional[str] = None,
    enabled_hosts: Optional[List[str]] = None,
    profile: Optional[str] = None,
    user_config_dir: Optional[str] = None,
    preset: Optional[str] = None,
    role: Optional[str] = None,
) -> ProjectContext:
    """Pure, side-effect-free resolver for AW project context (spec Section 9 & 17).

    Six Precedence Levels (spec Section 17):
      1. EXPLICIT_FLAGS (explicit arguments passed to invocation)
      2. MACHINE_LOCAL_BINDING (.aw/config/local.json in target repo or user repo binding)
      3. PROJECT_DURABLE_CONFIG (.aw/config/project.json in target repo)
      4. NAMED_GLOBAL_PROFILE (~/.config/agent-workflows/profiles/<profile>.json)
      5. GLOBAL_DEFAULTS (~/.config/agent-workflows/config.json default keys)
      6. BUILTIN_DEFAULTS (built-in fallbacks)
    """
    provenance_map: Dict[str, Provenance] = {}

    # 1. Target Repo Resolution & Security Check
    if target_repo:
        repo_abs = _check_path_security(target_repo, "target_repo")
        provenance_map["target_repo"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--repo flag ({target_repo})",
        )
    else:
        git_root = _find_git_root(os.getcwd())
        repo_abs = git_root if git_root else _canonical_path(os.getcwd())
        provenance_map["target_repo"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="discovered working tree directory",
        )

    # 2. AW_HOME Resolution
    if aw_home:
        aw_home_abs = _check_path_security(aw_home, "aw_home")
        provenance_map["effective_aw_home"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--aw-home flag ({aw_home})",
        )
    elif os.environ.get("AW_HOME"):
        aw_home_abs = _check_path_security(os.environ["AW_HOME"], "AW_HOME env")
        provenance_map["effective_aw_home"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail="AW_HOME environment variable",
        )
    else:
        user_cfg_path = (
            user_config_dir
            if user_config_dir
            else os.path.expanduser("~/.config/agent-workflows")
        )
        user_cfg = _read_json_file(os.path.join(user_cfg_path, "config.json"))
        if user_cfg and user_cfg.get("aw_home"):
            aw_home_abs = _check_path_security(user_cfg["aw_home"], "user_cfg aw_home")
            provenance_map["effective_aw_home"] = Provenance(
                source=PrecedenceLevel.GLOBAL_DEFAULTS.value,
                detail=f"global config ({user_cfg_path}/config.json)",
            )
        else:
            aw_home_abs = get_default_aw_home()
            provenance_map["effective_aw_home"] = Provenance(
                source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
                detail="platform default path",
            )

    # Read configuration layers
    user_cfg_dir_effective = (
        user_config_dir
        if user_config_dir
        else os.path.expanduser("~/.config/agent-workflows")
    )
    user_cfg_file = os.path.join(user_cfg_dir_effective, "config.json")
    user_cfg_data = _read_json_file(user_cfg_file) or {}

    # Level 2: Machine-local binding per-repo (.aw/config/local.json or user config repo section)
    local_binding_file = os.path.join(repo_abs, ".aw", "config", "local.json")
    local_binding_data = _read_json_file(local_binding_file) or {}

    # `repos` in the USER config (config_version 2) is the schema mapping of repository
    # settings: exactly the keys search/installed/exclude/ignore. It has ONE meaning, and it is
    # NOT a per-repo binding table keyed by absolute repo path. This read bypasses
    # `config.normalize()` on purpose (raw JSON), so it must reject the schema mapping itself
    # rather than probe it with a path key and quietly get nothing back.
    user_repos = user_cfg_data.get("repos")
    repo_cfg_in_user: Dict[str, Any] = {}
    if isinstance(user_repos, dict) and not _is_repos_schema_mapping(user_repos):
        candidate = user_repos.get(repo_abs)
        if isinstance(candidate, dict):
            repo_cfg_in_user = candidate

    # Merge local_binding_data with repo_cfg_in_user (local_binding_file takes priority for Level 2)
    merged_local_binding = dict(repo_cfg_in_user)
    merged_local_binding.update(local_binding_data)

    # Level 3: Project durable config (.aw/config/project.json or legacy config.json / policy.json)
    project_policy_file = os.path.join(repo_abs, ".aw", "config", "project.json")
    legacy_config_file = os.path.join(repo_abs, ".aw", "config", "config.json")
    legacy_policy_file = os.path.join(repo_abs, ".aw", "config", "policy.json")

    is_configured = False
    project_policy_data: Dict[str, Any] = {}

    if os.path.exists(project_policy_file):
        is_configured = True
        project_policy_data = _read_json_file(project_policy_file) or {}
    elif os.path.exists(legacy_policy_file):
        is_configured = True
        leg_data = _read_json_file(legacy_policy_file) or {}
        port, loc = migrate_legacy_config(leg_data)
        project_policy_data = port
        merged_local_binding.update(loc)
    elif os.path.exists(legacy_config_file):
        is_configured = True
        leg_data = _read_json_file(legacy_config_file) or {}
        port, loc = migrate_legacy_config(leg_data)
        project_policy_data = port
        merged_local_binding.update(loc)
    elif os.path.exists(local_binding_file):
        is_configured = True

    if project_policy_data.get("schema_version", 2) > 2:
        raise ValueError(
            f"Unsupported schema_version {project_policy_data.get('schema_version')}"
        )

    # Check for conflicting settings at same precedence level
    if project_policy_data and merged_local_binding:
        if (
            project_policy_data.get("delivery_mode")
            and merged_local_binding.get("delivery_mode")
            and project_policy_data["delivery_mode"]
            != merged_local_binding["delivery_mode"]
        ):
            raise ConflictingConfigurationError(
                f"Conflicting delivery_mode settings between durable config ({project_policy_data['delivery_mode']}) "
                f"and user local binding ({merged_local_binding['delivery_mode']})"
            )

    # Level 4: Named Global Profile
    selected_profile_name = (
        profile
        or merged_local_binding.get("profile")
        or project_policy_data.get("profile")
        or user_cfg_data.get("profile")
    )
    profile_cfg_data: Dict[str, Any] = {}
    if selected_profile_name:
        profile_file = os.path.join(
            user_cfg_dir_effective, "profiles", f"{selected_profile_name}.json"
        )
        profile_cfg_data = _read_json_file(profile_file) or {}

    # 3. Preset & Role Resolution
    if preset:
        resolved_preset = preset
        provenance_map["preset"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--preset flag ({preset})",
        )
    elif merged_local_binding.get("preset"):
        resolved_preset = merged_local_binding["preset"]
        provenance_map["preset"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail="machine-local binding",
        )
    elif project_policy_data.get("preset"):
        resolved_preset = project_policy_data["preset"]
        provenance_map["preset"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail="portable project policy",
        )
    elif profile_cfg_data.get("preset"):
        resolved_preset = profile_cfg_data["preset"]
        provenance_map["preset"] = Provenance(
            source=PrecedenceLevel.NAMED_GLOBAL_PROFILE.value,
            detail=f"named profile ({selected_profile_name})",
        )
    else:
        resolved_preset = Preset.PRIVATE_TARGET.value
        provenance_map["preset"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="built-in default (private-target)",
        )

    if role:
        resolved_role = role
        provenance_map["role"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--role flag ({role})",
        )
    elif merged_local_binding.get("role"):
        resolved_role = merged_local_binding["role"]
        provenance_map["role"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail="machine-local binding",
        )
    elif project_policy_data.get("role"):
        resolved_role = project_policy_data["role"]
        provenance_map["role"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail="portable project policy",
        )
    else:
        resolved_role = ProjectRole.TARGET.value
        provenance_map["role"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="built-in default (target)",
        )

    # 4. Delivery Mode Resolution
    if delivery_mode:
        if delivery_mode not in DELIVERY_MODES:
            raise ProjectContextError(f"Invalid delivery_mode: {delivery_mode}")
        resolved_delivery_mode = delivery_mode
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--delivery-mode flag ({delivery_mode})",
        )
    elif merged_local_binding.get("delivery_mode"):
        resolved_delivery_mode = merged_local_binding["delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail=f"user local binding for {repo_abs}",
        )
    elif project_policy_data.get("delivery_mode"):
        resolved_delivery_mode = project_policy_data["delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail=f"durable config ({project_policy_file})",
        )
    elif resolved_preset == Preset.COMPLETELY_CLEAN_TARGET.value:
        resolved_delivery_mode = DeliveryMode.CLEAN_DELTA.value
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail="derived from completely-clean-target preset",
        )
    elif profile_cfg_data.get("delivery_mode"):
        resolved_delivery_mode = profile_cfg_data["delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.NAMED_GLOBAL_PROFILE.value,
            detail=f"named global profile ({selected_profile_name})",
        )
    elif user_cfg_data.get("default_delivery_mode"):
        resolved_delivery_mode = user_cfg_data["default_delivery_mode"]
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.GLOBAL_DEFAULTS.value,
            detail="user global default",
        )
    else:
        resolved_delivery_mode = DeliveryMode.TRACKED.value
        provenance_map["delivery_mode"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="built-in default (tracked)",
        )

    # 5. Records Backend Resolution
    if records_backend:
        if records_backend not in RECORDS_BACKENDS:
            raise ProjectContextError(f"Invalid records_backend: {records_backend}")
        resolved_records_backend = records_backend
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"--records-backend flag ({records_backend})",
        )
    elif merged_local_binding.get("records_backend"):
        resolved_records_backend = merged_local_binding["records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail=f"user local binding for {repo_abs}",
        )
    elif project_policy_data.get("records_backend"):
        resolved_records_backend = project_policy_data["records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail=f"durable config ({project_policy_file})",
        )
    elif resolved_preset == Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value:
        resolved_records_backend = RecordsBackend.COMPANION.value
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail="derived from public-target-private-companion preset",
        )
    elif profile_cfg_data.get("records_backend"):
        resolved_records_backend = profile_cfg_data["records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.NAMED_GLOBAL_PROFILE.value,
            detail=f"named global profile ({selected_profile_name})",
        )
    elif user_cfg_data.get("default_records_backend"):
        resolved_records_backend = user_cfg_data["default_records_backend"]
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.GLOBAL_DEFAULTS.value,
            detail="user global default",
        )
    else:
        resolved_records_backend = RecordsBackend.HOME.value
        provenance_map["records_backend"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
            detail="built-in default (home)",
        )

    # Clean-delta security invariant check
    if (
        resolved_delivery_mode == DeliveryMode.CLEAN_DELTA.value
        and resolved_records_backend == RecordsBackend.REPOSITORY.value
    ):
        raise PathSecurityError(
            "Invalid configuration: clean-delta delivery mode MUST NOT use 'repository' records backend."
        )

    # 6. Project ID Resolution
    project_id = merged_local_binding.get(
        "project_id",
        project_policy_data.get("project_id", _derive_project_id(repo_abs)),
    )
    provenance_map["project_id"] = Provenance(
        source=(
            PrecedenceLevel.MACHINE_LOCAL_BINDING.value
            if "project_id" in merged_local_binding
            else (
                PrecedenceLevel.PROJECT_DURABLE_CONFIG.value
                if "project_id" in project_policy_data
                else PrecedenceLevel.BUILTIN_DEFAULTS.value
            )
        ),
        detail=f"project identity ({project_id})",
    )
    provenance_map["is_configured"] = Provenance(
        source=(
            PrecedenceLevel.PROJECT_DURABLE_CONFIG.value
            if is_configured
            else PrecedenceLevel.BUILTIN_DEFAULTS.value
        ),
        detail=f"persisted policy configured={is_configured}",
    )

    # 7. Physical Classes & Logical Roots Resolution
    project_aw_dir = os.path.join(aw_home_abs, "projects", project_id)

    # system root
    if merged_local_binding.get("system_root"):
        system_root = _canonical_path(merged_local_binding["system_root"])
    elif resolved_delivery_mode == DeliveryMode.TRACKED.value:
        system_root = _canonical_path(os.path.join(repo_abs, ".aw", "system"))
    else:
        system_root = _canonical_path(os.path.join(project_aw_dir, "system"))

    # config root
    if merged_local_binding.get("config_root"):
        config_root = _canonical_path(merged_local_binding["config_root"])
    elif resolved_delivery_mode == DeliveryMode.TRACKED.value:
        config_root = _canonical_path(os.path.join(repo_abs, ".aw", "config"))
    else:
        config_root = _canonical_path(os.path.join(project_aw_dir, "config"))

    config_project_path = _canonical_path(os.path.join(config_root, "project.json"))
    config_local_path = _canonical_path(os.path.join(config_root, "local.json"))

    # state root
    if merged_local_binding.get("state_root"):
        state_root = _canonical_path(merged_local_binding["state_root"])
    elif resolved_delivery_mode == DeliveryMode.TRACKED.value:
        state_root = _canonical_path(os.path.join(repo_abs, ".aw", "state"))
    else:
        state_root = _canonical_path(os.path.join(project_aw_dir, "state"))

    state_durable_path = _canonical_path(os.path.join(state_root, "durable"))
    state_runtime_path = _canonical_path(os.path.join(state_root, "runtime"))

    # records root
    if resolved_records_backend == RecordsBackend.REPOSITORY.value:
        records_root = _canonical_path(os.path.join(repo_abs, ".aw", "records"))
    elif resolved_records_backend == RecordsBackend.COMPANION.value:
        companion_dir = merged_local_binding.get("companion_dir") or f"{repo_abs}.aw"
        records_root = _canonical_path(os.path.join(companion_dir, "records"))
    else:  # HOME
        records_root = _canonical_path(os.path.join(project_aw_dir, "records"))

    physical_classes = {
        RootClass.SYSTEM.value: system_root,
        RootClass.CONFIG_PROJECT.value: config_project_path,
        RootClass.CONFIG_LOCAL.value: config_local_path,
        RootClass.STATE_DURABLE.value: state_durable_path,
        RootClass.STATE_RUNTIME.value: state_runtime_path,
        RootClass.RECORDS.value: records_root,
    }

    logical_roots = {
        LogicalRoot.SYSTEM.value: system_root,
        LogicalRoot.CONFIG.value: config_root,
        LogicalRoot.STATE.value: state_root,
        LogicalRoot.RECORDS.value: records_root,
    }

    # Same-path alias detection (spec Section 4.1 & E-03)
    # Distinct physical classes or logical roots MUST NOT alias each other unless explicitly permitted
    all_class_paths = list(physical_classes.items()) + list(logical_roots.items())
    local_aliases = merged_local_binding.get("local_aliases", {})
    for i in range(len(all_class_paths)):
        for j in range(i + 1, len(all_class_paths)):
            name_a, path_a = all_class_paths[i]
            name_b, path_b = all_class_paths[j]
            if (
                path_a == path_b
                and name_a != name_b
                and not (name_a.startswith("config") and name_b.startswith("config"))
            ):
                if (
                    local_aliases.get(name_a) != path_a
                    and local_aliases.get(name_b) != path_b
                ):
                    raise PathSecurityError(
                        f"Unlawful class aliasing detected between '{name_a}' and '{name_b}': {path_a}"
                    )
    provenance_map["logical_roots"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail="resolved physical roots mapping",
    )

    # Git Policies calculation per physical class
    git_policies = {
        RootClass.SYSTEM.value: GitPolicy.TARGET_GIT.value
        if resolved_preset
        in (Preset.PRIVATE_TARGET.value, ProjectRole.SOURCE_CHECKOUT.value)
        and resolved_delivery_mode == DeliveryMode.TRACKED.value
        else GitPolicy.IGNORED.value,
        RootClass.CONFIG_PROJECT.value: GitPolicy.TARGET_GIT.value
        if resolved_preset
        in (Preset.PRIVATE_TARGET.value, ProjectRole.SOURCE_CHECKOUT.value)
        and resolved_delivery_mode == DeliveryMode.TRACKED.value
        else GitPolicy.IGNORED.value,
        RootClass.CONFIG_LOCAL.value: GitPolicy.IGNORED.value,
        RootClass.STATE_DURABLE.value: GitPolicy.TARGET_GIT.value
        if resolved_preset
        in (Preset.PRIVATE_TARGET.value, ProjectRole.SOURCE_CHECKOUT.value)
        and resolved_delivery_mode == DeliveryMode.TRACKED.value
        else (
            GitPolicy.COMPANION_GIT.value
            if resolved_preset == Preset.PUBLIC_TARGET_PRIVATE_COMPANION.value
            else GitPolicy.IGNORED.value
        ),
        RootClass.STATE_RUNTIME.value: GitPolicy.IGNORED.value,
        RootClass.RECORDS.value: GitPolicy.TARGET_GIT.value
        if resolved_records_backend == RecordsBackend.REPOSITORY.value
        else (
            GitPolicy.COMPANION_GIT.value
            if resolved_records_backend == RecordsBackend.COMPANION.value
            else GitPolicy.UNTRACKED.value
        ),
    }

    # Containment check: clean-delta mode MUST NOT route ANY root into target repo
    if resolved_delivery_mode == DeliveryMode.CLEAN_DELTA.value:
        for root_name, root_path in logical_roots.items():
            if _is_safe_subpath(root_path, repo_abs):
                raise PathSecurityError(
                    f"Clean-delta security violation: {root_name} root ({root_path}) is inside target repository ({repo_abs})"
                )

    # Enforce physical Git policy invariants
    validate_physical_git_policy(repo_abs, physical_classes)

    # 8. Durability State
    if resolved_records_backend == RecordsBackend.REPOSITORY.value:
        durability_state = DurabilityState.REPOSITORY_MANAGED.value
    elif os.path.exists(os.path.join(records_root, ".git")):
        durability_state = DurabilityState.LOCAL_GIT.value
    else:
        durability_state = DurabilityState.UNVERSIONED.value
    provenance_map["durability_state"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail=f"observable records repository state ({durability_state})",
    )

    # 9. Framework Version
    # Canonical placement is the system-root SIBLING `.aw/system/VERSION` (OQ-02/IPD 20260816
    # xzuxet: VERSION is a system-root sibling, not inside the workflows/ bundle). Fall back to
    # the legacy in-bundle `.aw/system/workflows/VERSION` only if the sibling is absent, so a
    # partially-migrated or older tree still resolves.
    framework_version = DEFAULT_FRAMEWORK_VERSION
    version_file = os.path.join(system_root, "VERSION")
    if not os.path.isfile(version_file):
        version_file = os.path.join(system_root, "workflows", "VERSION")
    if os.path.isfile(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as vf:
                framework_version = vf.read().strip()
        except Exception:
            pass
    provenance_map["effective_framework_version"] = Provenance(
        source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
        detail=f"framework version ({framework_version})",
    )

    # 10. Enabled Hosts
    resolved_hosts = (
        enabled_hosts if enabled_hosts is not None else DEFAULT_ENABLED_HOSTS
    )
    provenance_map["enabled_hosts"] = Provenance(
        source=(
            PrecedenceLevel.EXPLICIT_FLAGS.value
            if enabled_hosts is not None
            else PrecedenceLevel.BUILTIN_DEFAULTS.value
        ),
        detail=f"enabled third-party hosts ({','.join(resolved_hosts)})",
    )

    # 11. Permitted Commit Destinations
    product_dest = (
        repo_abs if resolved_delivery_mode == DeliveryMode.TRACKED.value else None
    )
    if resolved_records_backend == RecordsBackend.REPOSITORY.value:
        records_dest = repo_abs
    elif resolved_records_backend == RecordsBackend.COMPANION.value:
        records_dest = records_root
    else:
        records_dest = None
    commit_destinations = {"product": product_dest, "records": records_dest}
    provenance_map["permitted_commit_destinations"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail="permitted commit targets based on delivery mode and backend",
    )

    # 12. Root Accessibility
    accessibility = {
        "system": os.access(
            system_root if os.path.exists(system_root) else repo_abs, os.R_OK
        ),
        "config": os.access(
            config_root if os.path.exists(config_root) else repo_abs, os.R_OK
        ),
        "state": os.access(
            state_root if os.path.exists(state_root) else repo_abs, os.R_OK
        ),
        "records": os.access(
            records_root if os.path.exists(records_root) else repo_abs, os.R_OK
        ),
    }
    provenance_map["root_accessibility"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail="filesystem readability checks for resolved roots",
    )

    # 13. Open AW Actions
    open_actions: List[Dict[str, Any]] = []
    open_actions_dir = os.path.join(state_root, "actions", "open")
    if os.path.isdir(open_actions_dir):
        for fname in sorted(os.listdir(open_actions_dir)):
            if fname.endswith(".md"):
                action_id = fname[:-3]
                open_actions.append(
                    {
                        "action_id": action_id,
                        "file_name": fname,
                        "path": os.path.join(open_actions_dir, fname),
                    }
                )
    provenance_map["open_aw_actions"] = Provenance(
        source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
        detail=f"open actions discovery ({len(open_actions)} open)",
    )

    return ProjectContext(
        target_repo=repo_abs,
        project_id=project_id,
        delivery_mode=resolved_delivery_mode,
        effective_aw_home=aw_home_abs,
        logical_roots=logical_roots,
        records_backend=resolved_records_backend,
        durability_state=durability_state,
        effective_framework_version=framework_version,
        enabled_hosts=resolved_hosts,
        permitted_commit_destinations=commit_destinations,
        root_accessibility=accessibility,
        open_aw_actions=open_actions,
        provenance={k: v.to_dict() for k, v in provenance_map.items()},
        physical_classes=physical_classes,
        git_policies=git_policies,
        project_role=resolved_role,
        preset=resolved_preset,
        is_configured=is_configured,
    )
