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

from dataclasses import dataclass
from enum import Enum
import json
import functools
import os
import re
import sys
import tempfile
import types
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

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


def _config_dir() -> Path:
    """Return the user config directory via config.config_dir() with lazy fail-open fallback."""
    try:
        from . import config as _config

        return _config.config_dir()
    except Exception:
        raw_override = os.environ.get("AW_CONFIG_DIR")
        if raw_override and raw_override.strip():
            candidate = Path(raw_override.strip()).expanduser()
            if candidate.is_absolute() and candidate != Path.home():
                return candidate
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        return Path(base).expanduser() / "agent-workflows"


def _resolve_effective_aw_home(
    aw_home: Optional[str | Path] = None,
    user_config_dir: Optional[str | Path] = None,
) -> tuple[str, PrecedenceLevel, str]:
    """Determine effective AW_HOME and its provenance (pure, side-effect-free)."""
    if aw_home:
        aw_home_abs = _check_path_security(str(aw_home), "aw_home")
        return (
            aw_home_abs,
            PrecedenceLevel.EXPLICIT_FLAGS,
            f"--aw-home flag ({aw_home})",
        )
    if os.environ.get("AW_HOME"):
        aw_home_abs = _check_path_security(os.environ["AW_HOME"], "AW_HOME env")
        return (
            aw_home_abs,
            PrecedenceLevel.MACHINE_LOCAL_BINDING,
            "AW_HOME environment variable",
        )
    user_cfg_path = str(user_config_dir) if user_config_dir else str(_config_dir())
    user_cfg = _read_json_file(os.path.join(user_cfg_path, "config.json"))
    if user_cfg and user_cfg.get("aw_home"):
        aw_home_abs = _check_path_security(str(user_cfg["aw_home"]), "user_cfg aw_home")
        return (
            aw_home_abs,
            PrecedenceLevel.GLOBAL_DEFAULTS,
            f"global config ({user_cfg_path}/config.json)",
        )
    aw_home_abs = get_default_aw_home()
    return (
        aw_home_abs,
        PrecedenceLevel.BUILTIN_DEFAULTS,
        "platform default path",
    )


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


def _project_climb_ceilings() -> set[Path]:
    """Return resolved canonical paths that act as ceilings for project-root and git-root climbs.

    Candidate ceilings include tempfile.gettempdir(), POSIX shared temp roots (/tmp and /var/tmp
    when present on disk), paths named by TMPDIR, TEMP, or TMP in os.environ, and any
    os.pathsep-separated path in os.environ.get("AW_PROJECT_CEILING", "").
    """
    candidates: list[str | Path] = [tempfile.gettempdir()]
    for posix_root in ("/tmp", "/var/tmp"):
        try:
            cand = Path(posix_root)
            if cand.exists():
                candidates.append(cand)
        except (OSError, RuntimeError):
            pass
    for env_var in ("TMPDIR", "TEMP", "TMP"):
        val = os.environ.get(env_var)
        if val:
            candidates.append(val)
    ceiling_env = os.environ.get("AW_PROJECT_CEILING", "")
    if ceiling_env:
        for entry in ceiling_env.split(os.pathsep):
            entry = entry.strip()
            if entry:
                candidates.append(entry)

    ceilings: set[Path] = set()
    for candidate in candidates:
        try:
            p = Path(candidate).expanduser().resolve()
            ceilings.add(p)
        except (OSError, RuntimeError):
            continue
    return ceilings


def _find_git_root(start_dir: str) -> Optional[str]:
    """Find the Git root directory by walking up from start_dir without subprocess.

    Upward walk stops and returns None when reaching a temporary root container or
    configured project ceiling (see ``_project_climb_ceilings``).
    """
    ceilings = _project_climb_ceilings()
    curr = Path(start_dir).resolve()
    while True:
        if curr in ceilings:
            return None
        git_dir = curr / ".git"
        if git_dir.exists():
            return curr.as_posix()
        if curr == curr.parent:
            return None
        curr = curr.parent


def _is_registered_submodule(dot_git: Path) -> bool:
    """True if dot_git is a submodule gitfile whose gitdir sits under .git/modules/ with no commondir.

    Rule 1 (IPD ivq0nr OQ-01 maintainer decision):
    Detects a registered submodule without spawning git: its .git is a file whose gitdir sits under
    the parent's .git/modules/, and that admin dir has no commondir (distinguishing it from a worktree).
    """
    if not dot_git.is_file():
        return False
    try:
        content = dot_git.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    gitdir_str = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("gitdir:"):
            gitdir_str = line[len("gitdir:") :].strip()
            break
    if not gitdir_str:
        return False
    gitdir = (dot_git.parent / gitdir_str).resolve()
    if not gitdir.is_dir():
        return False
    if (gitdir / "commondir").exists():
        return False
    dot_git_parent = dot_git.parent.resolve()
    for parent_candidate in dot_git_parent.parents:
        modules_dir = parent_candidate / ".git" / "modules"
        if modules_dir.is_dir():
            try:
                gitdir.relative_to(modules_dir)
                return True
            except ValueError:
                pass
    parts = gitdir.parts
    for i in range(len(parts) - 1):
        if parts[i] == ".git" and parts[i + 1] == "modules":
            return True
    return False


def checkout_main_root(path: str | Path) -> Optional[Path]:
    """Find the main worktree root of a git checkout without spawning git (IPD fnnwj3).

    Pure, file-based resolver: walks up from ``path`` to the first ancestor holding a ``.git``
    entry. If that entry is a directory, returns that ancestor (a main worktree is its own
    main root). If it is a file whose first line is ``gitdir: <dir>``, resolves ``<dir>``, reads
    ``<dir>/commondir`` (relative to ``<dir>``) to find the common git directory, and returns
    the common directory's parent iff the common directory is named ``.git`` and ``<dir>`` sits
    under ``<common>/worktrees/`` (a linked worktree). Returns ``None`` for anything else,
    including a submodule gitfile (``gitdir: ../.git/modules/<name>``, which has no ``commondir``
    file), a bare repository worktree, a ``--separate-git-dir`` layout, or a non-git directory.

    File-based and subprocess-free because it is called in per-command hot paths (such as
    ``find_project_root`` and ``project_config_dir``) that must stay pure, fast, and side-effect
    free. Intentionally agrees with ``ipd_lifecycle.checkout_control_root``'s rule:
    a common dir named ``.git`` maps to its parent worktree. Total: any OSError or RuntimeError
    returns None.
    """
    try:
        curr = Path(path).resolve()
    except (OSError, RuntimeError):
        return None

    while True:
        try:
            dot_git = curr / ".git"
            if dot_git.is_dir():
                return curr
            if dot_git.is_file():
                try:
                    content = dot_git.read_text(encoding="utf-8")
                except OSError:
                    return None
                gitdir_line = None
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("gitdir:"):
                        gitdir_line = line[len("gitdir:") :].strip()
                        break
                if not gitdir_line:
                    return None
                gitdir = (curr / gitdir_line).resolve()
                commondir_file = gitdir / "commondir"
                if not commondir_file.is_file():
                    return None
                try:
                    common_rel = commondir_file.read_text(encoding="utf-8").strip()
                except OSError:
                    return None
                common_dir = (gitdir / common_rel).resolve()
                if common_dir.name != ".git":
                    return None
                worktrees_dir = (common_dir / "worktrees").resolve()
                try:
                    gitdir.relative_to(worktrees_dir)
                except ValueError:
                    return None
                main_root = common_dir.parent.resolve()
                if main_root.is_dir():
                    return main_root
                return None
            if curr == curr.parent:
                return None
            curr = curr.parent
        except (OSError, RuntimeError):
            return None


def find_project_root(start: Optional[str | Path] = None) -> Optional[Path]:
    """Climb from ``start`` (default cwd) for the nearest ancestor that IS an AW project root.

    Returns the first directory (``start`` itself or an ancestor) that contains a ``.aw/`` or a
    legacy ``.agents/`` marker directory, or is an installed home-configured clean-target root
    (IPD fnnwj3, via ``home_configured_root``), else ``None``. Git-style upward walk (like
    ``_find_git_root``), so a repo-scoped ``aw`` verb works from any subdirectory. Pure and
    side-effect-free (except for one notice line when resolving a submodule to its parent project);
    symlink-safe (paths are resolved). A linked lane worktree is recognized as its own worktree root
    while sharing identity with its main checkout via ``checkout_main_root`` (IPD fnnwj3).
    git presence is NOT a marker: a ``.aw/`` tree can exist without git, and a bare ``.git`` ancestor
    with no AW marker is NOT an AW project (IPD awretrofit Order 06, OQ-01).

    Git boundaries and ceilings (IPD ivq0nr OQ-01 maintainer decision 2026-10-15):
    - An enclosing ``.git`` boundary that lacks an AW marker is a CEILING for project discovery:
      upward discovery stops at the git boundary and returns None, rather than escaping into an outer
      directory's ``.aw/`` marker (such as ``$HOME``, ``/tmp``, or a parent checkout).
    - Registered submodule exception: A registered git submodule without its own ``.aw/`` resolves
      to its enclosing parent project. Detect it without spawning git: its ``.git`` is a file whose
      gitdir sits under the parent's ``.git/modules/``, and that admin dir has no ``commondir``. Prints
      one notice line to stderr saying the parent project was used.
    - Submodules with their own ``.aw/`` use themselves (unchanged). Linked worktrees carry their own ``.aw/``
      or are recognized via home configuration (IPD fnnwj3).
    - Any other nested git repository without ``.aw/`` (its own ``.git`` directory, a vendored or scratch
      clone) stops at its own boundary and never binds to an outer project.

    Temporary root containers and project ceilings (IPD i44j8w):
    - Shared temporary roots (/tmp, /var/tmp, tempfile.gettempdir(), TMPDIR/TEMP/TMP) and any paths
      listed in AW_PROJECT_CEILING are ceilings for project discovery: upward discovery stops and
      returns None when reaching any ceiling container (neither treating the ceiling itself as a
      project root nor escaping above it into ancestor directories).
    """

    curr = Path(start).resolve() if start is not None else Path.cwd().resolve()
    ceilings = _project_climb_ceilings()
    submodule_encountered = False
    while True:
        if curr in ceilings:
            return None
        if (
            _is_project_marker(curr / ".aw")
            or _is_project_marker(curr / ".agents", legacy=True)
            or home_configured_root(curr)
        ):
            if submodule_encountered:
                sys.stderr.write(f"notice: parent project was used at {curr}\n")
            return curr
        dot_git = curr / ".git"
        if dot_git.exists():
            if _is_registered_submodule(dot_git):
                submodule_encountered = True
            else:
                return None
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
      THIS IS A DECIDED RULE (IPD ci9kx2-02 `lmyeas` OQ-01, from backlog `5gmi12`), not an oversight.
      The resolver is shared across both read-class and write-class callers, and a uniform upward climb
      is unsafe for multiple load-bearing reasons:
      1. Shared write-class callers: Of the resolver's call sites, roughly 19 invocations are
         WRITE-class operations (e.g., `work_cmd` allocating a git worktree and committing,
         `status_set.run_set_command` and `backlog.run_set` moving records between lifecycle dirs,
         five `git_mv` helpers, and seven record-authoring verbs). An upward climb would silently retarget
         those file mutations and lifecycle transitions at an ancestor project.
      2. Recursive delete hazard: `workflow_artifacts_prune.run_archive` resolves its target root and
         its delete helper executes ``shutil.rmtree(target, ignore_errors=False)``. A non-project `--dir`
         is today a safe no-op returning 0; under an ancestor climb it would delete the ancestor
         project's run-artifacts subtree.
      3. `$HOME` is commonly a project root: Measured on developer machines, `is_project_dir(Path.home())`
         is frequently True because home contains a `.aw/` with durable children (`config` and `projects`).
         A climb from an arbitrary scratch directory under home would resolve to `$HOME`, causing write
         verbs to target the user's home records tree.
      4. Lane-ancestry hazard: Isolated lane worktrees allocated by the test/execution runners live at
         `.aw/worktrees/<id6>` under a project root by construction. The first project-root ancestor of a
         lane is the shared checkout (and then `$HOME`), which runners deliberately avoid modifying mid-run.
         Climbing would risk retargeting lane-scoped writes and release-gate scans at the shared checkout.
      The remedy for a verb that cannot survey an explicit subdirectory is to REFUSE AND NAME THE ROOT
      (as `aw attention` and `aw ipd board` do via `no_project_message`), never to climb silently.
    - Otherwise CLIMB from cwd via ``find_project_root``; if an AW project root is found, use it (so
      the verb works from any subdirectory, git-style).
    - If no project root is found, fall through to cwd (the caller then emits the no-project message
      via ``no_project_message`` rather than printing a silent empty result).

    THAT LAST BULLET DESCRIBES AN INTENTION, NOT WHAT MOST CALLERS DO, and the asymmetry is recorded
    here so it is not rediscovered from scratch (IPD nogitmsg `quqyc4` E-07; reasoning in backlog
    item `okm6e6`). Only TWO verbs pair this resolver with ``is_project_dir`` and then emit
    ``no_project_message``: ``aw attention`` and ``aw ipd board``. Every other caller takes the cwd
    fallback SILENTLY, so run outside a project it produces an empty or misplaced result with no
    explanation of why.

    RE-DERIVE THE SURFACE, DO NOT TRUST A TRANSCRIBED LIST. Measured 2026-10-01 on this file's HEAD:
    87 call sites across 25 modules (including this definition; 44 AST invocations across 24 modules),
    counted with

        grep -rn --include=*.py resolve_verb_repo_root agent_workflows/

    Not every call site is a distinct user-facing verb. A line-number list is deliberately NOT written
    here: `quqyc4`'s own citations for these sites drifted twice before execution and again during it
    (9 of 10 sampled lines no longer held the call), which is the whole argument for a derivation
    command over an enumeration.

    WHETHER THE SILENT CALLERS SHOULD ALL GUIDE IS A SEPARATE DESIGN QUESTION, deliberately NOT
    settled here: some may legitimately operate on a bare directory. This note records the gap; it
    does not license converting them on the way past.
    """

    if explicit_dir:
        return Path(explicit_dir).expanduser().resolve()
    root = find_project_root()
    return root if root is not None else Path.cwd().resolve()


def no_project_message(
    verb: str, start_dir: Optional[str | Path] = None, explicit: bool = False
) -> str:
    """The verbose 'no AW project found' message a repo-scoped verb prints instead of empty output.

    Emitted when the operator did not pass ``--dir`` and no ``.aw/``/``.agents/`` marker exists at
    ``start_dir`` (default cwd) or any ancestor (IPD awretrofit Order 06). Names the verb, what was
    checked, and the fixes.

    WHEN ``explicit=True`` (IPD ci9kx2-01 `bjgqez` E-01), the operator passed an explicit ``--dir``
    naming a directory that is not an AW project. The message states that the directory named on the
    command line was checked and is not an AW project, that only that directory was checked with no
    upward climb (honored verbatim), and does not suggest passing ``--dir``.

    WHEN ``start_dir`` IS INSIDE A REAL AW PROJECT (IPD ci9kx2-02 `lmyeas` E-03), the refusal names
    the enclosing project root and provides the literal corrected command (`aw <verb> --dir <root>`).
    It explains that `--dir` does not climb, and does NOT claim that agent-workflows is not installed
    in the project.

    WHEN ``start_dir`` IS INSIDE A GIT REPOSITORY WITH NO AW PROJECT the message gains a FOURTH fact
    and an offer: it names the git root and prints the literal ``aw install <root>`` that would fix
    the condition (IPD nogitmsg `quqyc4` E-01, from backlog `okm6e6`). The commonest way to reach
    this message is to stand in a real repository that simply has no agent-workflows installed, and
    without this the message could describe the problem but never name the one action that resolves
    it.

    ``start_dir`` IS A PARAMETER RATHER THAN A ``Path.cwd()`` READ ON PURPOSE. Both call sites have
    already resolved a root via ``resolve_verb_repo_root``, so a ``cwd()`` read here would let the
    message describe one directory while the verb operated on another. Today those agree only
    because both callers guard this branch with ``not explicit_dir``; passing the resolved root makes
    the agreement a property of the inputs instead of an accident of the callers (`quqyc4` F-19).
    The default preserves every pre-existing caller's behavior.

    Per IPD ivq0nr OQ-01 maintainer decision (2026-10-15), upward discovery in ``find_project_root``
    is bounded at enclosing ``.git`` boundaries (acting as ceilings, with an exception for
    registered submodules resolving to their parent project). A bare ``.git`` ancestor with no AW
    marker remains NOT an AW project, but stops upward walk from escaping to an outer project.
    This function decides what to SAY once that climb has failed; it never decides what counts as a project.
    """

    where = Path(start_dir) if start_dir is not None else Path.cwd()
    if explicit:
        msg = (
            f"aw {verb}: no AW project found at {where}.\n"
            f"Checked only {where} (explicit --dir is honored verbatim with no upward climb) for a .aw/ (or legacy .agents/) project directory.\n"
            f"Specify your repository root, or run without --dir to search upward from cwd."
        )
    else:
        msg = (
            f"aw {verb}: no AW project found here.\n"
            f"Checked {where} and its parents for a .aw/ (or legacy .agents/) project directory.\n"
            f"Are you inside your repository? cd into the repo (or a subdirectory of it), "
            f"or pass --dir <repo>."
        )
    classification = classify_project_dir(where)
    if classification.is_inside_project and explicit:
        msg += (
            f"\n{classification.root} IS an agent-workflows project root, but explicit --dir is honored verbatim with no upward climb.\n"
            f"Run with: aw {verb} --dir {classification.root}"
        )
    else:
        git_root = _find_git_root(str(where))
        if git_root is not None and not is_project_dir(git_root):
            git_root_path = Path(git_root)
            msg += (
                f"\n{git_root_path} IS a git repository, but agent-workflows is not installed in it.\n"
                f"Install it there with: aw install {git_root_path}"
            )
    return msg


def git_root_for_message(start_dir: Optional[str | Path] = None) -> Optional[str]:
    """The git root ``no_project_message`` would name, or ``None`` when there is no git ancestor.

    Exposed so a caller building a MACHINE record can attach the same install offer as a structured
    ``NextAction`` without re-deriving (or re-implementing) the probe, and without parsing prose out
    of the human message (`quqyc4` E-04; updated per IPD ivq0nr OQ-01 maintainer decision).
    This answers "what should we SAY", never "is this an AW project".
    """

    where = Path(start_dir) if start_dir is not None else Path.cwd()
    if find_project_root(where) is not None:
        return None
    return _find_git_root(str(where))


def is_project_dir(repo_root: str | Path) -> bool:
    """True if ``repo_root`` is (or contains) an AW project marker - i.e. a real project, not a bare
    directory with nothing to survey. Used by repo-scoped verbs to decide between running and
    emitting ``no_project_message`` (IPD awretrofit Order 06). Also returns True for an installed
    home-configured clean-target root or linked worktree (IPD fnnwj3, via ``home_configured_root``).

    Returns False immediately if ``repo_root`` resolves to a temporary root container or
    configured project ceiling (see ``_project_climb_ceilings``).
    """

    try:
        p = Path(repo_root).expanduser().resolve()
    except (OSError, RuntimeError):
        p = Path(repo_root)

    if p in _project_climb_ceilings():
        return False

    return (
        _is_project_marker(p / ".aw")
        or _is_project_marker(p / ".agents", legacy=True)
        or home_configured_root(p)
    )


class ProjectLocationCase(str, Enum):
    """The three cases a resolved directory can have with respect to an AW project."""

    IS_PROJECT_ROOT = "is-project-root"
    IS_ROOT = "is-project-root"  # alias
    INSIDE_PROJECT = "inside-project"
    NO_PROJECT = "no-project"


@dataclass(frozen=True)
class ProjectClassification:
    """Classification of a directory with respect to AW project roots.

    Pure, read-only, and side-effect-free.
    - ``case``: one of ``ProjectLocationCase``.
    - ``root``: the enclosing AW project root when inside an AW project (or the directory itself
      when it is a project root), or None when in no project.
    """

    case: ProjectLocationCase
    root: Optional[Path] = None

    @property
    def is_root(self) -> bool:
        """True if the classified directory is itself an AW project root."""
        return self.case == ProjectLocationCase.IS_PROJECT_ROOT

    @property
    def is_inside_project(self) -> bool:
        """True if the classified directory is strictly inside an AW project (ancestor is root)."""
        return self.case == ProjectLocationCase.INSIDE_PROJECT

    @property
    def is_no_project(self) -> bool:
        """True if the classified directory is not in or under any AW project."""
        return self.case == ProjectLocationCase.NO_PROJECT

    @property
    def enclosing_root(self) -> Optional[Path]:
        """The enclosing AW project root if inside a project, else None."""
        return self.root if self.case == ProjectLocationCase.INSIDE_PROJECT else None


def classify_project_dir(path: Optional[str | Path] = None) -> ProjectClassification:
    """Classify a directory as a project root, inside a project, or in no project.

    Composes the existing ``is_project_dir`` and ``find_project_root`` predicates without
    re-implementing root detection or walking the filesystem independently. Pure, read-only,
    and side-effect-free. Per IPD ivq0nr OQ-01 maintainer decision (2026-10-15), root detection in
    ``find_project_root`` bounds upward discovery at enclosing git repository ceilings.
    Recognizes home-configured clean-target projects and linked lane worktrees via
    ``home_configured_root`` and ``checkout_main_root`` (IPD fnnwj3).

    Returns a ``ProjectClassification`` with:
    - ``case=ProjectLocationCase.IS_PROJECT_ROOT`` if ``path`` is itself an AW project root.
    - ``case=ProjectLocationCase.INSIDE_PROJECT`` and ``root=<enclosing_root>`` if ``path`` is
      inside an AW project whose root is an ancestor.
    - ``case=ProjectLocationCase.NO_PROJECT`` and ``root=None`` if ``path`` is not in any AW project.
    """
    p = Path(path).resolve() if path is not None else Path.cwd().resolve()
    if is_project_dir(p):
        return ProjectClassification(case=ProjectLocationCase.IS_PROJECT_ROOT, root=p)
    enclosing = find_project_root(p)
    if enclosing is not None:
        return ProjectClassification(
            case=ProjectLocationCase.INSIDE_PROJECT, root=enclosing
        )
    return ProjectClassification(case=ProjectLocationCase.NO_PROJECT, root=None)


@dataclass(frozen=True)
class RefusalNextAction:
    """The machine NextAction inputs produced by a refusal."""

    command: str
    description: str


@dataclass(frozen=True)
class RootRefusal:
    """Outcome of evaluating a resolved repository root for a verb.

    Pure, read-only, and side-effect-free data structure carrying everything
    a repo-scoped verb needs to proceed or refuse honestly.
    """

    may_proceed: bool
    human_message: Optional[str] = None
    summary: Optional[str] = None
    next_action: Optional[RefusalNextAction] = None

    @property
    def can_proceed(self) -> bool:
        """Alias for may_proceed."""
        return self.may_proceed

    @property
    def human_text(self) -> Optional[str]:
        """Alias for human_message."""
        return self.human_message

    @property
    def message(self) -> Optional[str]:
        """Alias for human_message."""
        return self.human_message

    @property
    def next_action_command(self) -> Optional[str]:
        """The next action command string, or None."""
        return self.next_action.command if self.next_action is not None else None

    @property
    def next_action_description(self) -> Optional[str]:
        """The next action description string, or None."""
        return self.next_action.description if self.next_action is not None else None

    @property
    def next_actions(self) -> List[RefusalNextAction]:
        """List containing the next_action if present, else empty list."""
        return [self.next_action] if self.next_action is not None else []


def nonsurveyable_root_refusal(
    verb: str,
    repo_root: Optional[str | Path] = None,
    explicit_dir: bool = False,
) -> RootRefusal:
    """Turn a resolved root and explicit-dir flag into a complete, honest refusal.

    Converts a resolved root plus the explicit-dir flag into everything a verb
    needs to refuse honestly when the resolved directory is not an AW project root:
    the human stderr text, the path-free machine summary, and the structured next action.
    Pure, read-only, and side-effect-free: writes no output to stdout or stderr,
    builds no CommandResult, and imports neither renderers nor result_types.

    Call shape for a converting verb:
        repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
        explicit_dir = bool(getattr(args, "dir", None))
        refusal = nonsurveyable_root_refusal(verb, repo_root, explicit_dir=explicit_dir)
        if not refusal.may_proceed:
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command=verb,
                    status="cannot-run",
                    exit_code=2,
                    summary=refusal.summary,
                    next_actions=(
                        [
                            NextAction(
                                command=refusal.next_action_command,
                                description=refusal.next_action_description,
                            )
                        ]
                        if refusal.next_action is not None
                        else []
                    ),
                )
                return get_renderer(ctx).emit(res, ctx)
            sys.stderr.write(refusal.human_message + "\\n")
            return EXIT_CANNOT_RUN

    Reference implementation:
        See ``attention.run`` (in ``agent_workflows/attention.py``) as the reference
        implementation demonstrating this exact emission block in production.

    Traps:
        1. PATH-FREE MACHINE SUMMARY: A machine record must never carry an absolute path.
           This is enforced rather than stylistic: the schema (``agent_schema``) refuses
           an absolute home path in any string field and raises ValueError in the renderer
           before a byte is emitted, causing an empty stdout and breaking the protocol.
           The machine summary returned here is strictly path-free; only the human message
           names paths.
        2. EXIT CODE CONTRACT: A ``cannot-run`` record must carry exit 2, never 3.
           ``aw.agent/v1`` admits only integer exit codes in (0, 1, 2); an ``exit_code=3``
           record cannot serialize and raises in the renderer. Both human and machine
           surfaces return exit 2 for this condition (retiring the earlier human exit 3
           so one condition has one uniform exit code across all surfaces; there is no
           split between human and machine exit codes). No site in the package builds
           an ``exit_code=3`` record.

    Policy:
        Whether a given verb should refuse is the verb's policy, not this primitive's.
        A read-class verb surveying nothing produces a false clean claim (an
        anti-greenwashing invariant violation) and should refuse. A write-class verb
        targets an operator's explicit destination and fails loudly and locally without
        touching the real records tree (IPD lmyeas OQ-01). The primitive serves both
        and chooses neither.

    No-climb rule:
        An explicit ``--dir`` still NEVER climbs upward to find an enclosing project root.
        See ``resolve_verb_repo_root``'s docstring for the recorded decision, rationale,
        and write-class safety hazards that govern why explicit ``--dir`` is honored verbatim.
    """
    where = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    classification = classify_project_dir(where)
    if classification.is_root:
        return RootRefusal(may_proceed=True)

    human_msg = no_project_message(verb, where, explicit=bool(explicit_dir))

    if classification.is_inside_project and explicit_dir:
        summary = (
            "the specified directory is inside an AW project but is not its root; "
            "--dir is honored verbatim with no upward climb"
        )
        next_action = None
    else:
        if explicit_dir:
            summary = (
                "no AW project found at the specified directory; "
                "--dir is honored verbatim with no upward climb"
            )
        else:
            summary = (
                "no AW project found at the working directory or any ancestor; "
                "cd into the repository or pass --dir <repo>"
            )

        git_root = git_root_for_message(where)
        if git_root is not None and not is_project_dir(git_root):
            next_action = RefusalNextAction(
                command="aw install .",
                description="install agent-workflows in this repo",
            )
        else:
            next_action = None

    return RootRefusal(
        may_proceed=False,
        human_message=human_msg,
        summary=summary,
        next_action=next_action,
    )


def _derive_project_id(target_repo: str) -> str:
    """Derive deterministic project ID from target_repo path."""
    repo_name = Path(target_repo).name or "project"
    clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", repo_name).strip("-").lower()
    import hashlib

    path_hash = hashlib.sha256(target_repo.encode("utf-8")).hexdigest()[:6]
    return f"{clean_slug}-{path_hash}"


def project_config_dir(
    repo_root: str | Path,
    aw_home: Optional[str | Path] = None,
) -> Path:
    """Return the configuration directory for a repository.

    Pure and side-effect free (spec 20260810-1447-01 Section 7).

    Rules, in order:
    1. If <repo>/.aw/config/project.json or <repo>/.aw/config/local.json
       (or legacy config.json / policy.json) exists, return <repo>/.aw/config.
    2. Else compute aw_home (explicit, AW_HOME env, user config aw_home,
       or default) and, if <aw_home>/projects/<project_id>/config/project.json
       exists, return that directory.
       When ``repo / ".git"`` exists (a worktree root, main or linked), the home
       ``project_id`` is derived from ``checkout_main_root(repo)`` as the identity
       anchor (IPD fnnwj3), so a linked lane worktree shares its main checkout's
       home config. For subdirectories (where ``.git`` does not exist directly),
       ``repo`` is retained without climb to prevent subdirectories from claiming
       the root's home config (PR-001).
    3. Else return <repo>/.aw/config.
    """
    repo = Path(repo_root)
    target_config = repo / ".aw" / "config"
    for candidate in (
        target_config / "project.json",
        target_config / "local.json",
        target_config / "config.json",
        target_config / "policy.json",
    ):
        if candidate.exists():
            return target_config

    eff_aw_home, _, _ = _resolve_effective_aw_home(aw_home=aw_home)
    anchor = repo
    try:
        if (repo / ".git").exists():
            anchor = checkout_main_root(repo) or repo
    except (OSError, RuntimeError):
        anchor = repo
    anchor_abs = _canonical_path(anchor)
    project_id = _derive_project_id(anchor_abs)
    home_config = Path(eff_aw_home) / "projects" / project_id / "config"
    if (home_config / "project.json").exists():
        return home_config

    return target_config


def home_configured_root(
    path: str | Path,
    aw_home: Optional[str | Path] = None,
) -> bool:
    """True if ``path`` is an installed clean-target AW project root (IPD fnnwj3).

    True iff:
    1. ``path / ".git"`` exists (the path is a git worktree root, main or linked; never
       a subdirectory, avoiding PR-001 false-positives on subdirectories).
    2. ``project_config_dir(path, aw_home)`` is not ``<path>/.aw/config`` (its configuration
       is home-stored rather than in-tree).
    3. The home configuration directory's ``project.json`` is a file.
    4. The stored ``project.json`` has ``delivery_mode == "clean-delta"`` (read directly;
       never re-derived from preset name).

    A linked lane worktree keeps its own working-tree root (so git operations within the lane
    target the lane worktree) and shares only configuration identity with the main checkout,
    mirroring ``ipd_lifecycle.checkout_control_root``. Total: returns False on any OSError.
    """
    try:
        p = Path(path).resolve()
        if not (p / ".git").exists():
            return False
        cfg = project_config_dir(p, aw_home=aw_home)
        target_cfg = p / ".aw" / "config"
        if _canonical_path(cfg) == _canonical_path(target_cfg):
            return False
        proj_json = cfg / "project.json"
        if not proj_json.is_file():
            return False
        data = _read_json_file(str(proj_json))
        if not data or not isinstance(data, dict):
            return False
        mode = data.get("delivery_mode")
        return mode == DeliveryMode.CLEAN_DELTA.value or mode == "clean-delta"
    except (OSError, RuntimeError):
        return False


def clean_delta_project_dir(
    main_root: str | Path,
    aw_home: Optional[str | Path] = None,
) -> Optional[Path]:
    """Return the <AW_HOME>/projects/<project_id> dir for a clean-delta repo, else None (IPD qk0ew6).

    Pure and side-effect free. When home_configured_root(main_root) holds, returns
    project_config_dir(main_root, aw_home).parent (<AW_HOME>/projects/<project_id>,
    the directory whose config/project.json was just read), else None.
    Total: no writes, no subprocesses.
    """
    try:
        if home_configured_root(main_root, aw_home=aw_home):
            return project_config_dir(main_root, aw_home=aw_home).parent
        return None
    except (OSError, RuntimeError, ValueError):
        return None


def _config_stat_stamp(
    cfg: Path, home_cfg_file: Path, user_cfg_file: Path | str
) -> tuple:
    """Cheap stat fingerprint for configuration files."""
    entries = []
    for name in ("project.json", "local.json", "config.json", "policy.json"):
        p = cfg / name
        try:
            st = os.stat(p)
            entries.append((name, st.st_mtime_ns, st.st_size, st.st_ino))
        except OSError:
            entries.append((name, None))
    try:
        st = os.stat(home_cfg_file)
        entries.append(("home_project_json", st.st_mtime_ns, st.st_size, st.st_ino))
    except OSError:
        entries.append(("home_project_json", None))
    try:
        st = os.stat(user_cfg_file)
        entries.append(("user_config", st.st_mtime_ns, st.st_size, st.st_ino))
    except OSError:
        entries.append(("user_config", None))
    return tuple(entries)


@functools.lru_cache(maxsize=128)
def _resolve_stored_physical_classes_cached(
    repo_abs: str,
    eff_aw_home: str,
    _stamp: tuple,
) -> tuple[Mapping[str, str], Mapping[str, Any], str]:
    """Cached resolution of physical classes, provenance, and delivery mode."""
    ctx = resolve_project_context(target_repo=repo_abs, aw_home=eff_aw_home)
    delivery_mode_val = (
        ctx.delivery_mode.value
        if hasattr(ctx.delivery_mode, "value")
        else str(ctx.delivery_mode)
    )
    return (
        types.MappingProxyType(dict(ctx.physical_classes)),
        types.MappingProxyType(dict(ctx.provenance)),
        delivery_mode_val,
    )


def _stored_physical_classes(
    repo_root: str | Path,
    aw_home: Optional[str | Path] = None,
    *,
    root_class: str = RootClass.RECORDS.value,
) -> Optional[Mapping[str, str]]:
    """Return physical classes mapping if repository has stored placement for root_class, else None."""
    repo = Path(repo_root)
    eff_aw_home, _, _ = _resolve_effective_aw_home(aw_home=aw_home)
    cfg = project_config_dir(repo, aw_home=eff_aw_home)
    has_config = any(
        (cfg / name).exists()
        for name in ("project.json", "local.json", "config.json", "policy.json")
    )
    if not has_config:
        return None

    repo_abs = _canonical_path(repo)
    user_cfg_file = os.path.expanduser("~/.config/agent-workflows/config.json")
    project_id = _derive_project_id(repo_abs)
    home_cfg_file = (
        Path(eff_aw_home) / "projects" / project_id / "config" / "project.json"
    )
    stamp = _config_stat_stamp(cfg, home_cfg_file, user_cfg_file)

    physical_classes, provenance, delivery_mode_val = (
        _resolve_stored_physical_classes_cached(repo_abs, eff_aw_home, stamp)
    )

    if root_class in (RootClass.SYSTEM.value, "system"):
        del_prov = provenance.get("delivery_mode", {})
        del_src = (
            del_prov.get("source")
            if isinstance(del_prov, dict)
            else getattr(del_prov, "source", None)
        )
        sys_prov = provenance.get("system_root", {})
        sys_src = (
            sys_prov.get("source")
            if isinstance(sys_prov, dict)
            else getattr(sys_prov, "source", None)
        )
        is_stored = (
            del_src in ("project_durable_config", "machine_local_binding")
            or sys_src == "machine_local_binding"
        )
        if not is_stored:
            return None
        return physical_classes

    # Default: records_backend
    rec_prov = provenance.get("records_backend", {})
    src = (
        rec_prov.get("source")
        if isinstance(rec_prov, dict)
        else getattr(rec_prov, "source", None)
    )
    is_stored = (
        src in ("project_durable_config", "machine_local_binding")
        or delivery_mode_val == "clean-delta"
    )
    if not is_stored:
        return None
    return physical_classes


def has_stored_records_placement(
    repo_root: str | Path,
    aw_home: Optional[str | Path] = None,
) -> bool:
    """Return True if repository has a stored records placement policy."""
    return (
        _stored_physical_classes(
            repo_root, aw_home=aw_home, root_class=RootClass.RECORDS.value
        )
        is not None
    )


def project_records_dir(
    repo_root: str | Path,
    aw_home: Optional[str | Path] = None,
) -> Path:
    """Return the records directory for a repository.

    Pure and side-effect free (spec 20260810-1447-01 Section 4 & 7).
    """
    repo = Path(repo_root)
    stored = _stored_physical_classes(
        repo, aw_home=aw_home, root_class=RootClass.RECORDS.value
    )
    if stored is None:
        return repo / ".aw" / "records"
    records_path = stored.get(RootClass.RECORDS.value, stored.get("records"))
    if not records_path:
        return repo / ".aw" / "records"
    if _canonical_path(records_path) == _canonical_path(repo / ".aw" / "records"):
        return repo / ".aw" / "records"
    return Path(records_path)


def record_owner_root(
    path: str | Path,
    aw_home: Optional[str | Path] = None,
) -> Optional[Path]:
    """Reverse-map a record file under AW_HOME to its owning repository root (backlog 4uw2a6).

    Pure, safe, and verification-backed:
    For a record path located under <effective AW_HOME>/projects/<pid>/records/,
    this resolver identifies the owning repository root by evaluating three candidates in order:
      1. CWD-anchored candidate: find_project_root(Path.cwd()), followed by checkout_main_root
         when inside a linked worktree.
      2. Home local.json back-pointer: the parent of common_dir from
         <aw_home>/projects/<pid>/config/local.json when common_dir is a non-empty string naming
         an existing directory called '.git'.
      3. Project registry target paths: each existing directory in target_paths from the project's
         entry in <aw_home>/config/registry.json.

    Verification rule:
    Every candidate is accepted ONLY when
    _canonical_path(project_records_dir(candidate, aw_home=eff_aw_home)) == _canonical_path(<aw_home>/projects/<pid>/records).
    Returns the first verified candidate as a Path, or None if no candidate matches or if the
    path does not lie under AW_HOME projects records.

    Companion-root limit:
    Records under a companion records root (records_backend: companion) are not handled by this
    resolver and remain out of scope (backlog miq4mi).
    """
    # FAST PATH (performance, F-11): before resolving AW_HOME or canonicalizing anything,
    # return None when the path's parts contain no 'projects' component followed later by 'records',
    # a pure string check with no I/O, so an in-tree record pays only this check.
    try:
        parts = Path(path).parts
    except Exception:
        return None

    try:
        idx_projects = parts.index("projects")
    except ValueError:
        return None

    if "records" not in parts[idx_projects + 1 :]:
        return None

    try:
        canon_path = Path(_canonical_path(path))
        eff_aw_home, _, _ = _resolve_effective_aw_home(aw_home=aw_home)
        canon_aw_home = Path(_canonical_path(eff_aw_home))

        projects_dir = canon_aw_home / "projects"
        try:
            rel = canon_path.relative_to(projects_dir)
        except ValueError:
            return None

        # Path must be under <aw_home>/projects/<pid>/records/
        # The second component after projects must be exactly 'records'
        if len(rel.parts) < 2 or rel.parts[1] != "records":
            return None

        pid = rel.parts[0]
        expected_records_dir = projects_dir / pid / "records"

        def _accepts(cand: str | Path) -> Optional[Path]:
            try:
                cand_p = Path(cand).resolve()
                if not cand_p.is_dir():
                    return None
                rec_dir = project_records_dir(cand_p, aw_home=eff_aw_home)
                if _canonical_path(rec_dir) == _canonical_path(expected_records_dir):
                    return cand_p
            except (
                OSError,
                ValueError,
                RuntimeError,
                ProjectContextError,
                json.JSONDecodeError,
                TypeError,
            ):
                return None
            return None

        # Candidate 1: cwd-anchored candidate
        cwd_root = find_project_root(Path.cwd())
        if cwd_root is not None:
            main_root = checkout_main_root(cwd_root)
            cand1 = main_root if main_root is not None else cwd_root
            accepted1 = _accepts(cand1)
            if accepted1 is not None:
                return accepted1

        # Candidate 2: common_dir back-pointer in local.json
        local_json_path = projects_dir / pid / "config" / "local.json"
        local_data = _read_json_file(str(local_json_path))
        if isinstance(local_data, dict):
            common_dir = local_data.get("common_dir")
            if isinstance(common_dir, str) and common_dir.strip():
                p_common = Path(common_dir)
                if p_common.is_dir() and p_common.name == ".git":
                    cand2 = p_common.parent
                    accepted2 = _accepts(cand2)
                    if accepted2 is not None:
                        return accepted2

        # Candidate 3: registry.json target_paths
        from agent_workflows import project_registry

        reg_path = project_registry.get_registry_path(eff_aw_home)
        reg_data = project_registry.load_registry(reg_path)
        if isinstance(reg_data, dict):
            projects = reg_data.get("projects", {})
            if isinstance(projects, dict):
                entry_raw = projects.get(pid)
                if isinstance(entry_raw, dict):
                    target_paths = entry_raw.get("target_paths", [])
                    if isinstance(target_paths, list):
                        for tp in target_paths:
                            if isinstance(tp, str) and tp.strip():
                                accepted3 = _accepts(tp)
                                if accepted3 is not None:
                                    return accepted3

        return None
    except (
        OSError,
        ValueError,
        RuntimeError,
        ProjectContextError,
        json.JSONDecodeError,
        TypeError,
    ):
        return None


def has_stored_system_placement(
    repo_root: str | Path,
    aw_home: Optional[str | Path] = None,
) -> bool:
    """Return True if repository has a stored system placement policy."""
    return (
        _stored_physical_classes(
            repo_root, aw_home=aw_home, root_class=RootClass.SYSTEM.value
        )
        is not None
    )


def project_system_dir(
    repo_root: str | Path,
    aw_home: Optional[str | Path] = None,
) -> Path:
    """Return the system directory for a repository.

    Pure and side-effect free (spec 20260810-1447-01 Section 4 & 7).
    """
    repo = Path(repo_root)
    stored = _stored_physical_classes(
        repo, aw_home=aw_home, root_class=RootClass.SYSTEM.value
    )
    if stored is None:
        return repo / ".aw" / "system"
    system_path = stored.get(RootClass.SYSTEM.value, stored.get("system"))
    if not system_path:
        return repo / ".aw" / "system"
    if _canonical_path(system_path) == _canonical_path(repo / ".aw" / "system"):
        return repo / ".aw" / "system"
    return Path(system_path)


def read_project_identity(repo_root: str | Path) -> Dict[str, Optional[str]]:
    """Return ``{"preset": ..., "records_backend": ...}`` as RECORDED IN THE REPOSITORY.

    THE ONE READER for the two fields `aw doctor` and `aw status` report, so those two commands
    cannot give different answers (IPD h90ij1 E-02/E-05). Both previously hand-rolled their own
    read of ``.aw/config.json`` / ``.agents/config.json``, a file NEITHER layout ever creates, so
    both reported ``None`` for every correctly installed repo.

    PRECEDENCE, explicit rather than incidental, because ``records_backend`` legitimately appears
    in more than one file and "whichever I find first" is how the two answers drift apart:

      1. ``.aw/config/project.json``  - the canonical COMMITTED project policy. It is what
         `install_wizard.resolve_existing_policy` treats as authoritative and what
         `resolve_project_context` reads as Level 3 PROJECT_DURABLE_CONFIG, and it is the only
         one of these files that carries BOTH keys. It therefore wins.
      2. ``.aw/config/config.json``   - the LEGACY pre-split config, migrated forward by
         `project_schema.migrate_legacy_config`. Consulted per KEY, so a legacy file can still
         supply a field the canonical file omits, but it never overrides the canonical file.
      3. ``.agents/config.json``      - the pre-`.aw` layout, retained for an un-migrated repo.

    Deliberately NOT ``resolve_project_context``: that resolver LAYERS machine-local and global
    state (``.aw/config/local.json``, the user config, a named profile) and FALLS BACK to a
    built-in default, so it always yields a value and can never answer "is this repo configured,
    and as what?". These two commands report the repo's own recorded state, so an unconfigured
    repo must read back ``None`` and not a fabricated default.

    Read-only, exception-free, and layout-agnostic: an unreadable or non-JSON file contributes
    nothing rather than raising, exactly as the hand-rolled reads it replaces behaved.
    """

    root = Path(repo_root)
    cfg_dir = project_config_dir(root)
    resolved: Dict[str, Optional[str]] = {"preset": None, "records_backend": None}
    for candidate in (
        cfg_dir / "project.json",
        cfg_dir / "config.json",
        root / ".agents" / "config.json",
    ):
        data = _read_json_file(str(candidate))
        if not data:
            continue
        for key in ("preset", "records_backend"):
            if resolved[key] is None:
                value = data.get(key)
                if isinstance(value, str) and value:
                    resolved[key] = value
    return resolved


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
    companion_dir: Optional[str] = None,
) -> ProjectContext:
    """Pure, side-effect-free resolver for AW project context (spec Section 9 & 17).

    Six Precedence Levels (spec Section 17):
      1. EXPLICIT_FLAGS (explicit arguments passed to invocation)
      2. MACHINE_LOCAL_BINDING (.aw/config/local.json in target repo or user repo binding)
      3. PROJECT_DURABLE_CONFIG (.aw/config/project.json in target repo)
      4. NAMED_GLOBAL_PROFILE (profiles/<profile>.json in user config dir via config.config_dir())
      5. GLOBAL_DEFAULTS (config.json default keys in user config dir via config.config_dir())
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
    aw_home_abs, aw_home_prec, aw_home_detail = _resolve_effective_aw_home(
        aw_home=aw_home, user_config_dir=user_config_dir
    )
    provenance_map["effective_aw_home"] = Provenance(
        source=aw_home_prec.value,
        detail=aw_home_detail,
    )

    # Read configuration layers
    user_cfg_dir_effective = (
        str(user_config_dir) if user_config_dir else str(_config_dir())
    )
    user_cfg_file = os.path.join(user_cfg_dir_effective, "config.json")
    user_cfg_data = _read_json_file(user_cfg_file) or {}

    cfg_dir = project_config_dir(repo_abs, aw_home=aw_home_abs)

    # Level 2: Machine-local binding per-repo (.aw/config/local.json or user config repo section)
    local_binding_file = str(cfg_dir / "local.json")
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
        if candidate is None:
            # `repo_abs` is canonical (symlinks resolved), but a user-written key may name
            # the repo through a symlink (macOS /var -> /private/var) or a Windows 8.3
            # short path; compare canonical forms so such a binding is not silently lost.
            for key, value in user_repos.items():
                if isinstance(key, str) and _canonical_path(key) == repo_abs:
                    candidate = value
                    break
        if isinstance(candidate, dict):
            repo_cfg_in_user = candidate

    # Merge local_binding_data with repo_cfg_in_user (local_binding_file takes priority for Level 2)
    merged_local_binding = dict(repo_cfg_in_user)
    merged_local_binding.update(local_binding_data)

    # Level 3: Project durable config (.aw/config/project.json or legacy config.json / policy.json)
    project_policy_file = str(cfg_dir / "project.json")
    legacy_config_file = str(cfg_dir / "config.json")
    legacy_policy_file = str(cfg_dir / "policy.json")

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
        and resolved_records_backend
        in (
            RecordsBackend.REPOSITORY.value,
            RecordsBackend.REPOSITORY_UNTRACKED.value,
        )
    ):
        raise PathSecurityError(
            "Invalid configuration: clean-delta delivery mode MUST NOT use 'repository' records backend."
        )

    # 6. Project ID Resolution
    local_pid = merged_local_binding.get("project_id")
    policy_pid = project_policy_data.get("project_id")
    if isinstance(local_pid, str) and local_pid.strip():
        project_id = local_pid.strip()
        pid_source = PrecedenceLevel.MACHINE_LOCAL_BINDING.value
    elif isinstance(policy_pid, str) and policy_pid.strip():
        project_id = policy_pid.strip()
        pid_source = PrecedenceLevel.PROJECT_DURABLE_CONFIG.value
    else:
        anchor_repo = Path(repo_abs)
        try:
            if (anchor_repo / ".git").exists():
                anchor_repo = checkout_main_root(anchor_repo) or anchor_repo
        except (OSError, RuntimeError):
            pass
        project_id = _derive_project_id(_canonical_path(anchor_repo))
        pid_source = PrecedenceLevel.BUILTIN_DEFAULTS.value

    provenance_map["project_id"] = Provenance(
        source=pid_source,
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
        provenance_map["system_root"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail=f"user local binding system_root ({system_root})",
        )
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
    if resolved_records_backend in (
        RecordsBackend.REPOSITORY.value,
        RecordsBackend.REPOSITORY_UNTRACKED.value,
    ):
        records_root = _canonical_path(os.path.join(repo_abs, ".aw", "records"))
    elif resolved_records_backend == RecordsBackend.COMPANION.value:
        eff_companion_dir = (
            companion_dir
            or merged_local_binding.get("companion_dir")
            or f"{repo_abs}.aw"
        )
        records_root = _canonical_path(os.path.join(eff_companion_dir, "records"))
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
        # .aw/.gitignore ignores /state/ (engine._AW_GITIGNORE_TEMPLATE, D92 leak containment)
        RootClass.STATE_DURABLE.value: (
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
            else (
                GitPolicy.IGNORED.value
                if resolved_records_backend == RecordsBackend.REPOSITORY_UNTRACKED.value
                else GitPolicy.UNTRACKED.value
            )
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
    if enabled_hosts is not None:
        resolved_hosts = list(enabled_hosts)
        provenance_map["enabled_hosts"] = Provenance(
            source=PrecedenceLevel.EXPLICIT_FLAGS.value,
            detail=f"enabled third-party hosts ({','.join(resolved_hosts)})",
        )
    elif isinstance(merged_local_binding.get("enabled_hosts"), list) and all(
        isinstance(x, str) for x in merged_local_binding["enabled_hosts"]
    ):
        resolved_hosts = list(merged_local_binding["enabled_hosts"])
        provenance_map["enabled_hosts"] = Provenance(
            source=PrecedenceLevel.MACHINE_LOCAL_BINDING.value,
            detail=f"machine-local binding ({','.join(resolved_hosts)})",
        )
    elif isinstance(project_policy_data.get("enabled_hosts"), list) and all(
        isinstance(x, str) for x in project_policy_data["enabled_hosts"]
    ):
        resolved_hosts = list(project_policy_data["enabled_hosts"])
        provenance_map["enabled_hosts"] = Provenance(
            source=PrecedenceLevel.PROJECT_DURABLE_CONFIG.value,
            detail=f"portable project policy ({','.join(resolved_hosts)})",
        )
    else:
        resolved_hosts = list(DEFAULT_ENABLED_HOSTS)
        provenance_map["enabled_hosts"] = Provenance(
            source=PrecedenceLevel.BUILTIN_DEFAULTS.value,
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
