"""Canonical workflow SOURCE layout + package contract (build-time only).

awoptimize Order 01 (`nmwy3m`) E-02. This module defines the on-disk LAYOUT of a canonical workflow
package and the progressive-disclosure resource convention, and it computes the package SEMANTIC
DIGEST over the authoritative source bytes. It is the layout half of the schema (E-01 owns the typed
semantic contract); the strict loader (E-03) uses this module to know what is authoritative, what is
generated, and how to hash a package.

Per ADR DECISIONS D139, the canonical source is authored in YAML and consumed ONLY at
build/authoring time. This module therefore MAY parse YAML, but it does so behind a lazily-imported
build-time boundary: the YAML import lives inside the one function that needs it, so simply importing
`workflow_source` never pulls a YAML parser into a runtime path. If a YAML parser is unavailable, the
build-time functions raise a clear, actionable error rather than silently degrading (fail closed).

Layout of a canonical workflow package (a directory named for the workflow id):

    <workflows-src>/<workflow-id>/
      workflow.yaml            # AUTHORITATIVE entry file (typed per E-01) + resource references
      protocol.md              # AUTHORITATIVE progressive-disclosure resource (optional)
      steps/*.md               # AUTHORITATIVE just-in-time step bodies (optional)
      rubrics/*.md             # AUTHORITATIVE (optional)
      templates/*              # AUTHORITATIVE (optional)
      examples/*               # AUTHORITATIVE (optional)
      scripts/*.py             # AUTHORITATIVE deterministic helpers (optional)
      _generated/              # GENERATED projections (NEVER hand-edited; owned by the compiler)

Authoritative vs generated: everything EXCEPT the `_generated/` subtree is authoritative source and
contributes to the semantic digest. `_generated/` is compiler output; it is excluded from the digest
so regenerating it does not appear to change the source, and the compiler's drift check (E-06) is
what proves it matches. The entry file's `resources:` block enumerates the authoritative resources by
relative path so the loader can prove closure (every referenced resource exists; no resource escapes
the package).

The semantic digest is a SHA-256 over a deterministic serialization of (relative-path, content-hash)
pairs for every authoritative file, sorted by path. It changes iff any authoritative byte changes,
and is stable across filesystem enumeration order and across machines.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Tuple

# The entry file name and the generated-subtree name are fixed parts of the layout contract.
ENTRY_FILENAME = "workflow.yaml"
GENERATED_DIRNAME = "_generated"

# Authoritable resource categories (directories under the package that hold authoritative source).
# The entry file is authoritative on its own; these are the optional progressive-disclosure buckets.
RESOURCE_DIRS: Tuple[str, ...] = (
    "steps",
    "rubrics",
    "templates",
    "examples",
    "scripts",
)

# Files that are metadata/cruft and never part of the authoritative source or the digest.
_IGNORED_NAMES = frozenset((".DS_Store",))
_IGNORED_SUFFIXES = frozenset((".pyc", ".pyo"))
_IGNORED_DIR_PARTS = frozenset(("__pycache__", GENERATED_DIRNAME))


class SourceError(Exception):
    """Raised for a structurally invalid or unsafe canonical source package (fail closed)."""


class PackagePaths(NamedTuple):
    """Resolved, safety-checked paths for one canonical workflow package."""

    root: Path
    entry: Path


def is_ignored_rel(rel_parts: Tuple[str, ...]) -> bool:
    """True for a package-relative path that is cruft or generated output (excluded from the digest)."""

    if not rel_parts:
        return True
    if any(part in _IGNORED_DIR_PARTS for part in rel_parts):
        return True
    name = rel_parts[-1]
    if name in _IGNORED_NAMES:
        return True
    return any(name.endswith(suf) for suf in _IGNORED_SUFFIXES)


def resolve_package(root: Any) -> PackagePaths:
    """Resolve and safety-check a package root. Raises :class:`SourceError` if the entry file is
    missing. Does not read or parse the entry file (that is the loader's job, E-03)."""

    root_path = Path(root)
    if not root_path.is_dir():
        raise SourceError(
            "workflow package root is not a directory: {0}".format(root_path)
        )
    entry = root_path / ENTRY_FILENAME
    if not entry.is_file():
        raise SourceError(
            "missing entry file {0} in package {1}".format(ENTRY_FILENAME, root_path)
        )
    return PackagePaths(root=root_path, entry=entry)


def _iter_authoritative_files(root: Path) -> List[Path]:
    """Return every authoritative file under ``root`` (entry + resources), excluding generated/cruft,
    following NO symlinks (a symlink is refused, see :func:`assert_no_symlink_escape`). Deterministic
    (sorted)."""

    out: List[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if is_ignored_rel(rel_parts):
            continue
        out.append(path)
    return out


def assert_no_symlink_escape(root: Path) -> None:
    """Refuse any symlink inside the package, and any path that resolves outside the package root.

    This is a build-time safety guard (E-03 traversal/symlink-escape rejection lives here so both the
    loader and the digest use one check). Fail closed with :class:`SourceError`."""

    root_resolved = root.resolve()
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if is_ignored_rel(rel_parts):
            continue
        if path.is_symlink():
            raise SourceError(
                "symlink not permitted in a canonical package: {0}".format(path)
            )
        # Defense in depth: even without a symlink flag, refuse anything that resolves outside root.
        try:
            resolved = path.resolve()
        except OSError as exc:  # pragma: no cover - unusual FS error
            raise SourceError("cannot resolve {0}: {1}".format(path, exc))
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            raise SourceError("path escapes the package root: {0}".format(path))


def semantic_digest(root: Any) -> str:
    """Compute the package semantic digest: SHA-256 over sorted (relative-posix-path, sha256(content))
    pairs for every authoritative file. Excludes the generated subtree and cruft. Deterministic and
    machine-independent. Refuses symlinks first (fail closed)."""

    paths = resolve_package(root)
    assert_no_symlink_escape(paths.root)
    hasher = hashlib.sha256()
    for path in _iter_authoritative_files(paths.root):
        rel = path.relative_to(paths.root).as_posix()
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        # length-prefixed to avoid any ambiguity between the path and the hash boundary
        record = "{0}\x00{1}\n".format(rel, content_hash)
        hasher.update(record.encode("utf-8"))
    return hasher.hexdigest()


def parse_entry(root: Any) -> Dict[str, Any]:
    """Parse the package entry file (YAML) into a plain mapping. BUILD-TIME ONLY.

    The YAML parser is imported INSIDE this function so importing this module never adds a YAML
    dependency to a runtime path (D139). If no YAML parser is installed, raise an actionable
    :class:`SourceError` (fail closed) rather than returning a degraded result.
    """

    paths = resolve_package(root)
    try:
        import yaml  # type: ignore  # build-time-only dependency (D139); not a runtime import
    except ImportError as exc:
        raise SourceError(
            "PyYAML is required at build/authoring time to parse {0} (install the dev/build extra); "
            "it is never a runtime dependency (D139). Original error: {1}".format(
                ENTRY_FILENAME, exc
            )
        )
    try:
        text = paths.entry.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001 - surface any parse error as a SourceError, fail closed
        raise SourceError("failed to parse {0}: {1}".format(paths.entry, exc))
    if not isinstance(data, dict):
        raise SourceError(
            "entry file {0} must parse to a mapping, got {1}".format(
                paths.entry, type(data).__name__
            )
        )
    return data


def referenced_resources(entry_data: Dict[str, Any]) -> List[str]:
    """Return the list of package-relative resource paths the entry file declares under `resources:`.
    Missing/empty is allowed (a package MAY be entry-only). Non-string entries are ignored here; the
    loader (E-03) validates closure and reports precise findings."""

    res = entry_data.get("resources")
    if not isinstance(res, list):
        return []
    return [r for r in res if isinstance(r, str)]
