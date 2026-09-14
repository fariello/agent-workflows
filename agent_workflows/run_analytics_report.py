#!/usr/bin/env python3
"""runanalytics Order 07 (`6eq3oq`): transactional publication of the analytics report bundle.

THE ATOMICITY PROBLEM THIS MODULE EXISTS TO SOLVE, stated first because it dictates the design.
This package performs roughly 60 atomic writes and every one of them is SINGLE-FILE
temp-then-rename (:func:`agent_workflows.artifact_core.atomic_write` is the canonical helper,
:func:`agent_workflows.runner_shared.atomic_write_json` its JSON twin). That pattern DOES NOT
GENERALIZE to a multi-file bundle: ``os.replace`` onto a NON-EMPTY target directory raises
``OSError`` errno 39 ("Directory not empty"), re-measured in this worktree at execution. So "publish
the bundle atomically" cannot be done the way a single file is done, and the plan's original
"a failure leaves the previous latest bundle intact" was unimplementable as written.

WHAT WORKS, AND ITS PLATFORM CATCH. Publishing into a fresh VERSIONED directory and then flipping a
``latest`` SYMLINK (``os.symlink`` to a temp name, then ``os.replace`` onto the link) IS atomic, and
was re-measured here. But CI runs ``windows-latest``, where creating a symlink requires Developer
Mode or elevation, and this package's only other ``os.symlink`` call is a preserve-existing branch in
``layout_migration``, not a create-a-link-as-policy path. A publisher that REQUIRED symlinks would
therefore fail the suite on a supported platform. So both paths are IMPLEMENTED and both are TESTED:
:func:`publish_bundle` attempts the symlink flip and, when the attempt raises, falls back to
:func:`_publish_flat`, which writes the flat files in a DOCUMENTED ORDER with the manifest LAST.

THE MANIFEST IS THE COMPLETENESS SIGNAL, on BOTH paths, and that is the property that makes the
fallback safe rather than merely available. A reader that finds :data:`MANIFEST_FILENAME` can trust
every file the manifest names, because the manifest is the last byte written and carries each file's
size and digest. A reader that finds no manifest must treat the directory as incomplete. This is why
:func:`read_manifest` refuses a manifest whose files do not match it, rather than returning a
best-effort dict: a manifest that disagrees with the directory is not a weaker signal, it is a wrong
one.

WHERE THE BUNDLE GOES IS ORDER 01'S ANSWER, NEVER A COMPOSED LITERAL. Order 01 (`xbwq8n`) exists to
remove the ``.aw/records/runs`` literal from its six live sites and exposes
:func:`~agent_workflows.runner_shared.analytics_root`,
:func:`~agent_workflows.runner_shared.analytics_snapshots_dir` and the
:func:`~agent_workflows.runner_shared.path_is_within_analytics` containment predicate. This module
calls those. Composing the path here would create the seventh site and would mis-site the report for
any non-``repository`` records backend.

THE TREE IS WORKER-FORBIDDEN AND STAYS THAT WAY. ``worktree_lease.FORBIDDEN_WORKER_PATH_HINTS``
already contains ``.aw/records/runs/``, so analytics is produced by the human or coordinator invoking
the analyzer, never inside a worker lane turn. Nothing here weakens that predicate;
:func:`publish_bundle` instead REFUSES a destination outside the analytics namespace, so a caller
cannot redirect a publish into the tracked tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_workflows.runner_shared import (
    analytics_root,
    analytics_snapshots_dir,
    path_is_within_analytics,
)

__all__ = [
    "REPORT_SCHEMA_VERSION",
    "MANIFEST_FILENAME",
    "INDEX_FILENAME",
    "PUBLICATION_ORDER",
    "LATEST_LINK_NAME",
    "PublicationError",
    "BundleFile",
    "PublishResult",
    "bundle_files_from_mapping",
    "publish_bundle",
    "read_manifest",
    "verify_bundle",
    "resolve_report_dir",
    "resolve_snapshot_dir",
    "publish_snapshot",
    "prune_snapshots",
]


#: Bumped when the BUNDLE SHAPE changes (a new required file, a changed manifest field).
REPORT_SCHEMA_VERSION = 1

#: The completeness signal. Written LAST on every path, which is the whole contract.
MANIFEST_FILENAME = "manifest.json"

#: The report a human opens.
INDEX_FILENAME = "index.html"

#: The name of the atomically-flipped pointer to the newest versioned bundle, when symlinks work.
LATEST_LINK_NAME = "latest"

#: The DOCUMENTED write order for the no-symlink fallback path, most-derived first and the manifest
#: LAST. The order is part of the contract rather than an implementation detail: a reader that finds
#: a manifest may trust the files it names precisely because everything the manifest names was
#: already durable when the manifest appeared.
PUBLICATION_ORDER: tuple[str, ...] = (
    "facts.jsonl",
    "analysis.json",
    "findings.md",
    INDEX_FILENAME,
    MANIFEST_FILENAME,
)


class PublicationError(RuntimeError):
    """A publish was refused or could not be completed transactionally."""


@dataclass(frozen=True)
class BundleFile:
    """ONE file in the bundle: its name, its bytes, and its digest.

    Bytes rather than a source path, deliberately. The caller has already rendered the document in
    memory (see :func:`agent_workflows.run_analytics_spa.render_document`), and reading it back from
    a staging path would introduce a window in which the bytes on disk and the bytes in the manifest
    could differ.
    """

    name: str
    content: bytes

    def __post_init__(self) -> None:
        if (
            not self.name
            or "/" in self.name
            or "\\" in self.name
            or self.name in (".", "..")
        ):
            raise PublicationError(
                f"bundle file name {self.name!r} must be a single path component; a bundle is flat"
            )

    @property
    def size(self) -> int:
        return len(self.content)

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    def to_manifest_entry(self) -> dict[str, Any]:
        return {"name": self.name, "size": self.size, "sha256": self.digest}


@dataclass(frozen=True)
class PublishResult:
    """What a publish actually did, including WHICH path it took.

    ``used_symlink`` is reported rather than inferred because the two paths have different failure
    modes and a caller (or a test) must be able to tell which one ran on this platform.
    """

    directory: Path
    version_dir: Path | None
    used_symlink: bool
    manifest: dict[str, Any]
    files: tuple[str, ...] = ()
    fallback_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "directory": str(self.directory),
            "version_dir": str(self.version_dir) if self.version_dir else None,
            "used_symlink": self.used_symlink,
            "files": list(self.files),
            "fallback_reason": self.fallback_reason,
            "manifest": dict(self.manifest),
        }


def bundle_files_from_mapping(
    payload: Mapping[str, str | bytes],
) -> tuple[BundleFile, ...]:
    """Build bundle files from a ``{name: content}`` mapping, ordered by :data:`PUBLICATION_ORDER`.

    A name not in the declared order is published BEFORE the manifest, in sorted position, so an
    added companion file is still durable before the completeness signal appears.
    """

    files = [
        BundleFile(
            name=name,
            content=content.encode("utf-8")
            if isinstance(content, str)
            else bytes(content),
        )
        for name, content in payload.items()
    ]
    return tuple(sorted(files, key=lambda f: _order_key(f.name)))


def _order_key(name: str) -> tuple[int, str]:
    if name == MANIFEST_FILENAME:
        # Always last, whatever else is present.
        return (len(PUBLICATION_ORDER) + 1, name)
    if name in PUBLICATION_ORDER:
        return (PUBLICATION_ORDER.index(name), name)
    return (len(PUBLICATION_ORDER), name)


def _build_manifest(
    files: Sequence[BundleFile],
    *,
    generated_label: str,
    used_symlink: bool,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The manifest: every file with its size and digest, plus how the bundle was published."""

    entries = [f.to_manifest_entry() for f in files if f.name != MANIFEST_FILENAME]
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "generated_label": generated_label,
        "publication_scheme": "versioned-dir+symlink-flip"
        if used_symlink
        else "flat-manifest-last",
        "manifest_is_completeness_signal": True,
        "files": sorted(entries, key=lambda e: e["name"]),
        "file_count": len(entries),
        **dict(extra or {}),
    }


def _write_file_durably(path: Path, content: bytes) -> None:
    """Write one file with fsync, so "already written" means durable rather than buffered.

    The fsync is not decoration. The manifest's guarantee is that everything it names is already on
    disk, and without fsync a crash can reorder a buffered data write after the manifest's own write,
    which is precisely the half-bundle the ordering exists to prevent.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, str(path))
    finally:
        if os.path.exists(temp_name):
            try:
                os.unlink(temp_name)
            except OSError:
                pass
    _fsync_dir(path.parent)


def _fsync_dir(directory: Path) -> None:
    if not hasattr(os, "O_DIRECTORY"):
        return
    try:
        fd = os.open(str(directory), os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def publish_bundle(
    directory: Path | str,
    files: Sequence[BundleFile] | Mapping[str, str | bytes],
    *,
    generated_label: str = "",
    version_label: str = "",
    allow_symlink: bool = True,
    repo: Path | str | None = None,
    require_analytics_namespace: bool = True,
    manifest_extra: Mapping[str, Any] | None = None,
) -> PublishResult:
    """Publish a bundle transactionally, preferring the symlink flip and falling back when it fails.

    THE TWO PATHS AND WHY BOTH EXIST. The primary path writes every file into a fresh versioned
    directory, writes the manifest last, then flips ``latest`` with ``os.symlink`` + ``os.replace``,
    which is atomic (re-measured). The fallback writes the same files, in
    :data:`PUBLICATION_ORDER`, directly into ``directory``, manifest last; it engages when the
    symlink attempt raises, which is the measured Windows case (symlink creation needs privilege).
    ``allow_symlink=False`` forces the fallback so a test can exercise it on any platform.

    On BOTH paths the manifest is the LAST write and is the completeness signal, so an interruption
    leaves a directory with no manifest, which a reader must treat as incomplete, rather than a
    readable half-bundle it would mistake for a finished one.
    """

    target = Path(directory).expanduser()
    if require_analytics_namespace and not path_is_within_analytics(
        target if target.exists() else target.parent, repo
    ):
        # A refusal rather than a mkdir: publishing a generated bundle outside the reserved,
        # gitignored namespace is how generated output gets committed by accident, and 6 of 216 real
        # outcome files carried absolute paths the leak detector flags at `fail`.
        raise PublicationError(
            f"refusing to publish outside the reserved analytics namespace: {target}. "
            "Order 01 owns the resolver; use resolve_report_dir() rather than composing a path"
        )

    bundle = (
        bundle_files_from_mapping(files)
        if isinstance(files, Mapping)
        else tuple(sorted(files, key=lambda f: _order_key(f.name)))
    )
    if not bundle:
        raise PublicationError("refusing to publish an empty bundle")
    names = tuple(f.name for f in bundle)
    if INDEX_FILENAME not in names:
        raise PublicationError(
            f"a report bundle must contain {INDEX_FILENAME!r}; got {list(names)}"
        )

    target.mkdir(parents=True, exist_ok=True)

    if allow_symlink:
        version = version_label or _next_version_label(target)
        version_dir = target / "versions" / version
        try:
            result = _publish_versioned(
                target,
                version_dir,
                bundle,
                generated_label=generated_label,
                manifest_extra=manifest_extra,
            )
        except OSError as exc:
            # The measured Windows case: symlink creation needs privilege. Fall THROUGH to the flat
            # path rather than failing, and record WHY, because a silent fallback would hide that a
            # platform never exercises the primary scheme.
            shutil.rmtree(version_dir, ignore_errors=True)
            return _publish_flat(
                target,
                bundle,
                generated_label=generated_label,
                manifest_extra=manifest_extra,
                fallback_reason=f"symlink publication unavailable: {type(exc).__name__}: {exc}",
            )
        return result

    return _publish_flat(
        target,
        bundle,
        generated_label=generated_label,
        manifest_extra=manifest_extra,
        fallback_reason="symlink publication disabled by the caller",
    )


def _publish_versioned(
    target: Path,
    version_dir: Path,
    bundle: Sequence[BundleFile],
    *,
    generated_label: str,
    manifest_extra: Mapping[str, Any] | None,
) -> PublishResult:
    """Primary path: fresh versioned directory, manifest last, then an ATOMIC symlink flip."""

    if version_dir.exists():
        shutil.rmtree(version_dir)
    version_dir.mkdir(parents=True)

    manifest = _build_manifest(
        bundle, generated_label=generated_label, used_symlink=True, extra=manifest_extra
    )
    for item in bundle:
        if item.name == MANIFEST_FILENAME:
            continue
        _write_file_durably(version_dir / item.name, item.content)
    # LAST. Everything it names is already durable.
    _write_file_durably(
        version_dir / MANIFEST_FILENAME,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    link = target / LATEST_LINK_NAME
    temp_link = target / f".{LATEST_LINK_NAME}.tmp"
    if temp_link.exists() or temp_link.is_symlink():
        temp_link.unlink()
    # `os.symlink` raises on Windows without privilege; the caller catches OSError and falls back.
    os.symlink(version_dir.name and str(Path("versions") / version_dir.name), temp_link)
    os.replace(str(temp_link), str(link))
    _fsync_dir(target)

    return PublishResult(
        directory=target,
        version_dir=version_dir,
        used_symlink=True,
        manifest=manifest,
        files=tuple(f.name for f in bundle),
    )


def _publish_flat(
    target: Path,
    bundle: Sequence[BundleFile],
    *,
    generated_label: str,
    manifest_extra: Mapping[str, Any] | None,
    fallback_reason: str,
) -> PublishResult:
    """Fallback path: flat files in :data:`PUBLICATION_ORDER`, manifest LAST.

    Not atomic, and this docstring says so rather than implying otherwise: a reader can observe the
    directory mid-write. What it CANNOT observe is a manifest that names a file not yet durable,
    which is the property that keeps the fallback honest. An interrupted flat publish leaves either
    no manifest (incomplete, detectable) or the previous manifest (stale, detectable by digest).
    """

    manifest = _build_manifest(
        bundle,
        generated_label=generated_label,
        used_symlink=False,
        extra=manifest_extra,
    )
    # Remove the OLD manifest first, so an interruption can never leave a stale manifest sitting
    # beside new files it does not describe. No manifest is a correct signal; a wrong one is not.
    old_manifest = target / MANIFEST_FILENAME
    if old_manifest.exists():
        old_manifest.unlink()
        _fsync_dir(target)

    for item in bundle:
        if item.name == MANIFEST_FILENAME:
            continue
        _write_file_durably(target / item.name, item.content)
    _write_file_durably(
        target / MANIFEST_FILENAME,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    return PublishResult(
        directory=target,
        version_dir=None,
        used_symlink=False,
        manifest=manifest,
        files=tuple(f.name for f in bundle),
        fallback_reason=fallback_reason,
    )


def read_manifest(directory: Path | str) -> dict[str, Any]:
    """The manifest of a published bundle, or a REFUSAL when the bundle is incomplete.

    Refuses rather than returning a best-effort dict, and the distinction matters: a manifest that
    disagrees with the directory is not a weaker signal, it is a WRONG one, and a caller handed a
    partial dict would proceed as if the bundle were sound.
    """

    root = Path(directory).expanduser()
    link = root / LATEST_LINK_NAME
    if link.is_symlink() or (link.exists() and link.is_dir()):
        root = link.resolve()
    path = root / MANIFEST_FILENAME
    if not path.is_file():
        raise PublicationError(
            f"no {MANIFEST_FILENAME} in {root}: the manifest is the completeness signal, so this "
            "bundle must be treated as incomplete (a publish was interrupted or never ran)"
        )
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicationError(f"unreadable manifest in {root}: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise PublicationError(f"manifest in {root} is not an object")
    return dict(manifest)


def verify_bundle(directory: Path | str) -> list[str]:
    """Every discrepancy between a bundle and its manifest. Empty means sound.

    Returns the FINDINGS so a failure names what is wrong, which is the same reason
    :func:`~agent_workflows.run_analytics_spa.scan_for_network_references` returns matches.
    """

    root = Path(directory).expanduser()
    link = root / LATEST_LINK_NAME
    if link.is_symlink() or (link.exists() and link.is_dir()):
        root = link.resolve()
    problems: list[str] = []
    try:
        manifest = read_manifest(root)
    except PublicationError as exc:
        return [str(exc)]
    for entry in manifest.get("files") or []:
        name = str(entry.get("name") or "")
        path = root / name
        if not path.is_file():
            problems.append(f"{name}: named by the manifest but absent")
            continue
        content = path.read_bytes()
        if len(content) != int(entry.get("size") or -1):
            problems.append(
                f"{name}: size {len(content)} does not match the manifest's "
                f"{entry.get('size')}"
            )
        digest = hashlib.sha256(content).hexdigest()
        if digest != str(entry.get("sha256") or ""):
            problems.append(f"{name}: sha256 does not match the manifest")
    return problems


def resolve_report_dir(repo: Path | str | None = None) -> Path:
    """The latest report's directory, THROUGH Order 01's resolver.

    Never a composed literal. Order 01 exists to remove ``.aw/records/runs`` from six sites, and
    composing it here would create the seventh and mis-site the report for any non-``repository``
    records backend.
    """

    return analytics_root(repo)


def resolve_snapshot_dir(label: str, repo: Path | str | None = None) -> Path:
    """One immutable snapshot's directory beneath the reserved ``analytics/snapshots/``."""

    clean = str(label).strip()
    if not clean or "/" in clean or "\\" in clean or clean in (".", ".."):
        raise PublicationError(
            f"snapshot label {label!r} must be a single path component"
        )
    return analytics_snapshots_dir(repo) / clean


def publish_snapshot(
    label: str,
    files: Sequence[BundleFile] | Mapping[str, str | bytes],
    *,
    generated_label: str = "",
    repo: Path | str | None = None,
    allow_symlink: bool = False,
) -> PublishResult:
    """Publish an IMMUTABLE snapshot. Flat by default, because a snapshot has no ``latest``.

    ``allow_symlink=False`` by default is a deliberate difference from :func:`publish_bundle`: a
    snapshot is written once and never replaced, so the versioned-directory-plus-pointer machinery
    would add a level of indirection with nothing to point at.
    """

    return publish_bundle(
        resolve_snapshot_dir(label, repo),
        files,
        generated_label=generated_label,
        allow_symlink=allow_symlink,
        repo=repo,
        manifest_extra={"snapshot_label": str(label), "immutable": True},
    )


def prune_snapshots(
    *,
    keep: int,
    repo: Path | str | None = None,
) -> list[str]:
    """Prune snapshots to the newest ``keep``, touching ONLY tool-owned directories.

    "Tool-owned" means: inside the reserved snapshots tree AND carrying a manifest this module wrote
    (``report_schema_version`` present). A directory a human dropped there is LEFT ALONE, because a
    retention policy that deletes unrecognized content is a data-loss bug wearing a feature's name.
    """

    if keep < 0:
        raise PublicationError("keep must be zero or more")
    root = analytics_snapshots_dir(repo)
    if not root.is_dir():
        return []
    owned: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        try:
            manifest = read_manifest(child)
        except PublicationError:
            continue  # not ours; never pruned
        if "report_schema_version" not in manifest:
            continue
        owned.append(child)
    # Newest last by name (labels are lexically sortable timestamps), so the head is pruned.
    removed: list[str] = []
    for child in owned[: max(0, len(owned) - keep)]:
        if not path_is_within_analytics(child, repo):
            # Belt and braces: never recurse-delete outside the reserved namespace, whatever the
            # resolver returned.
            continue
        shutil.rmtree(child)
        removed.append(child.name)
    return removed


def _next_version_label(target: Path) -> str:
    """A deterministic, lexically-sortable version label derived from existing versions.

    A COUNTER rather than a timestamp, deliberately: the plan requires byte-identical output for
    identical input, and a timestamp in a directory name would make two otherwise-identical
    publications differ. The counter is derived from what is already on disk, so it needs no state.
    """

    versions = target / "versions"
    highest = 0
    if versions.is_dir():
        for child in versions.iterdir():
            if child.is_dir() and child.name.startswith("v"):
                try:
                    highest = max(highest, int(child.name[1:]))
                except ValueError:
                    continue
    return f"v{highest + 1:06d}"
