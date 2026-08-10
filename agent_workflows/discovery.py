"""Discover git repositories to install the framework into (spec OQ4).

Rules (decided in the spec, DECISIONS D46):

- A configured path that is ITSELF a non-submodule git repo is the target; we do NOT
  descend into it.
- Otherwise we scan its immediate children for non-submodule git repos (opt-in
  ``recursive`` walks deeper).
- Submodules (listed in the parent's ``.gitmodules``) are SKIPPED; an independent nested
  repo (a real ``.git`` not listed as a submodule) under a non-git root is a valid target.
- The config ``ignore`` list holds ``fnmatch``-style globs matched against the expanded
  absolute path; ``ignore`` applies to DISCOVERY ONLY (never to an explicit
  ``install <dir>``) and is a NOISE filter (hide uninteresting paths).
- The config ``exclude`` list is a DELIBERATE never-install blocklist (paths and/or
  fnmatch globs). An excluded repo is dropped from discovery targets and recorded in
  ``Discovery.excluded`` (kept DISTINCT from ``ignored`` so the two intents do not blur).
  Unlike ``ignore``, ``exclude`` also guards an explicit ``install <dir>`` (the caller's
  interactive/non-interactive guard), but that guard lives at the call site, not here.

Discovery classifies each candidate as a target, skipped (with a reason), ignored, or
excluded, so the caller (``install all`` / ``setup``) can report everything and pass
nothing over silently (AC-4/AC-13).
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class Discovery:
    """The outcome of a discovery pass."""

    targets: List[Path] = field(default_factory=list)
    # path -> reason ("not-a-git-repo", "submodule", "missing")
    skipped: Dict[Path, str] = field(default_factory=dict)
    ignored: List[Path] = field(default_factory=list)
    # deliberate never-install blocklist matches (distinct from the ignore noise filter)
    excluded: List[Path] = field(default_factory=list)


def is_git_repo(path: Path) -> bool:
    """True if ``path`` is a git working tree root (has a ``.git`` dir OR file).

    A ``.git`` FILE (not dir) is how a submodule or a worktree records its gitdir; we
    still treat the directory as a repo root here, and submodule-ness is decided
    separately via the parent's ``.gitmodules``.
    """

    if not path.is_dir():
        return False
    dot_git = path / ".git"
    return dot_git.is_dir() or dot_git.is_file()


def submodule_paths(parent: Path) -> List[Path]:
    """Return absolute paths of submodules declared in ``parent/.gitmodules``.

    Parses only the ``path = <rel>`` entries (stdlib, no git call). Missing or malformed
    ``.gitmodules`` yields an empty list.
    """

    gm = parent / ".gitmodules"
    try:
        text = gm.read_text(encoding="utf-8")
    except OSError:
        return []
    out: List[Path] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("path") and "=" in stripped:
            rel = stripped.split("=", 1)[1].strip()
            if rel:
                out.append((parent / rel).resolve())
    return out


def _is_ignored(path: Path, ignore: List[str]) -> bool:
    """True if the absolute path matches any fnmatch glob in ``ignore``."""

    p = str(path)
    return any(fnmatch.fnmatch(p, pattern) for pattern in ignore)


def _is_excluded(path: Path, exclude: List[str]) -> bool:
    """True if the absolute path is on the never-install blocklist.

    An ``exclude`` entry matches either by exact absolute-path equality (after resolving)
    or as an ``fnmatch`` glob against the absolute path, so both a concrete repo path and
    a glob like ``*/never-install/*`` work.
    """

    p = str(path)
    for entry in exclude:
        try:
            if os.path.abspath(os.path.expanduser(entry)) == p:
                return True
        except (OSError, ValueError):
            pass
        if fnmatch.fnmatch(p, entry):
            return True
    return False


def discover(
    roots,
    ignore=None,
    recursive: bool = False,
    exclude=None,
) -> Discovery:
    """Discover install targets under the given roots.

    Args:
        roots: iterable of already-expanded absolute directory Paths (search roots or a
            single explicit path).
        ignore: fnmatch globs (discovery-only NOISE filter); a matching path is recorded
            as ignored, not installed.
        recursive: if True, walk subdirectories when a root is not itself a repo (opt-in);
            otherwise only immediate children are scanned. Descent stops at a repo root
            (we never descend into a discovered repo) and skips submodules.
        exclude: deliberate never-install blocklist (expanded paths and/or fnmatch globs);
            a matching repo is recorded in ``excluded`` (distinct from ``ignored``) and
            never becomes a target. Defaults to none.

    Returns:
        A ``Discovery`` with targets / skipped(reason) / ignored / excluded (deduped,
        order-stable).
    """

    ignore = list(ignore or [])
    exclude = list(exclude or [])
    result = Discovery()
    seen = set()

    def add_target(path: Path) -> None:
        rp = path.resolve()
        if rp in seen:
            return
        seen.add(rp)
        # Exclusion (deliberate blocklist) takes precedence over the ignore noise filter.
        if _is_excluded(rp, exclude):
            result.excluded.append(rp)
        elif _is_ignored(rp, ignore):
            result.ignored.append(rp)
        else:
            result.targets.append(rp)

    for root in roots:
        root = Path(root)
        rroot = root.resolve()
        if not root.is_dir():
            result.skipped[rroot] = "missing"
            continue

        # A configured path that is itself a repo IS the target; do not descend.
        if is_git_repo(root):
            add_target(root)
            continue

        subs = set(submodule_paths(root))
        _scan_children(root, subs, ignore, recursive, result, seen, add_target, exclude)

    return result


def _scan_children(
    parent: Path,
    parent_submodules,
    ignore,
    recursive: bool,
    result: Discovery,
    seen: set,
    add_target,
    exclude=None,
) -> None:
    """Scan immediate children (or recurse) of a non-repo parent for target repos."""

    exclude = list(exclude or [])
    try:
        children = sorted(p for p in parent.iterdir() if p.is_dir())
    except OSError:
        return

    for child in children:
        rchild = child.resolve()
        if rchild in parent_submodules:
            result.skipped[rchild] = "submodule"
            continue
        # Exclusion (deliberate blocklist) takes precedence over the ignore noise filter.
        if _is_excluded(rchild, exclude):
            if rchild not in seen:
                seen.add(rchild)
                result.excluded.append(rchild)
            continue
        if _is_ignored(rchild, ignore):
            if rchild not in seen:
                seen.add(rchild)
                result.ignored.append(rchild)
            continue
        if is_git_repo(child):
            add_target(child)
            # Never descend into a discovered repo.
            continue
        if recursive:
            _scan_children(
                child,
                set(submodule_paths(child)),
                ignore,
                recursive,
                result,
                seen,
                add_target,
                exclude,
            )
        else:
            # An immediate child that is not a repo: report it so nothing is silent.
            result.skipped[rchild] = "not-a-git-repo"
