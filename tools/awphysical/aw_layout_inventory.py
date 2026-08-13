#!/usr/bin/env python3
"""Create a read-only content and Git inventory for an AW layout migration.

The tool deliberately does not infer that a file is safe to remove. It inventories every
entry under declared roots, does not follow symlinks, and gives unknown material an explicit
classification. Absolute root paths are omitted unless the operator opts in because an
inventory may itself become a durable migration record.

Examples:
    python3 tools/awphysical/aw_layout_inventory.py --repo . --output /tmp/inventory.json
    python3 tools/awphysical/aw_layout_inventory.py --repo . \
        --root old-records=/srv/private/records --include-root-paths
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


SCHEMA_VERSION = 1
DEFAULT_ROOTS: Tuple[Tuple[str, str], ...] = (
    ("agents", ".agents"),
    ("workflow-artifacts", "workflow-artifacts"),
    ("installer-backups", ".agent-workflows-installer-backups"),
    ("partial-aw", ".aw"),
    ("claude-adapters", ".claude"),
    ("opencode-adapters", ".opencode"),
    ("agents-pointer", "AGENTS.md"),
    ("claude-pointer", "CLAUDE.md"),
    ("gemini-pointer", "GEMINI.md"),
)
LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class InventoryError(Exception):
    """Raised when the inventory cannot be completed safely or completely."""


def _run_git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run one read-only Git command and return captured text output.

    Args:
        repo: Repository working tree.
        args: Arguments following ``git -C <repo>``.

    Returns:
        The completed process. Callers decide whether a nonzero status is fatal.
    """

    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _nul_paths(repo: Path, args: Sequence[str]) -> Set[str]:
    """Return normalized repo-relative paths from a NUL-delimited Git command."""

    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        return set()
    return {
        os.fsdecode(raw).replace(os.sep, "/") for raw in proc.stdout.split(b"\0") if raw
    }


def git_sets(
    repo: Path,
) -> Tuple[Set[str], Set[str], Set[str], Set[str], Optional[str]]:
    """Collect tracked, untracked, ignored, unmerged paths and Git common dir."""

    inside = _run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return set(), set(), set(), set(), None
    tracked = _nul_paths(repo, ["ls-files", "-z"])
    untracked = _nul_paths(repo, ["ls-files", "--others", "--exclude-standard", "-z"])
    ignored = _nul_paths(
        repo, ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"]
    )
    unmerged_raw = _nul_paths(repo, ["ls-files", "-u", "-z"])
    # -u records contain metadata, a tab, then the path.
    unmerged = {item.split("\t", 1)[-1] for item in unmerged_raw}
    common = _run_git(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    common_dir = common.stdout.strip() if common.returncode == 0 else None
    return tracked, untracked, ignored, unmerged, common_dir


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a regular file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_root(value: str, repo: Path) -> Tuple[str, Path]:
    """Parse ``LABEL=PATH`` and resolve a relative path against the repository."""

    if "=" not in value:
        raise InventoryError(f"--root requires LABEL=PATH, got: {value!r}")
    label, raw_path = value.split("=", 1)
    if not LABEL_RE.fullmatch(label):
        raise InventoryError(f"unsafe root label: {label!r}")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = repo / path
    return label, path.absolute()


def _default_roots(repo: Path) -> List[Tuple[str, Path]]:
    """Return existing default legacy roots without inventing absent entries."""

    return [
        (label, (repo / rel).absolute())
        for label, rel in DEFAULT_ROOTS
        if (repo / rel).exists() or (repo / rel).is_symlink()
    ]


def classify_item(
    label: str, relpath: str, repo_relpath: Optional[str] = None
) -> Dict[str, str]:
    """Classify legacy item into ownership, lifecycle, destination class, and disposition (E-01/E-03)."""
    posix = relpath.strip("/")
    if not posix or posix == ".":
        if label == "agents":
            return {
                "ownership": "system",
                "lifecycle_class": "system",
                "expected_destination_class": "system",
                "disposition": "migrate",
            }
        if label == "workflow-artifacts":
            return {
                "ownership": "records",
                "lifecycle_class": "records",
                "expected_destination_class": "records",
                "disposition": "migrate",
            }
        if label == "installer-backups":
            return {
                "ownership": "state-runtime",
                "lifecycle_class": "state-runtime",
                "expected_destination_class": "durable_state",
                "disposition": "preserve",
            }
        if label == "partial-aw":
            return {
                "ownership": "config",
                "lifecycle_class": "config",
                "expected_destination_class": "config",
                "disposition": "migrate",
            }
        if (
            label.startswith("ext-")
            or label.startswith("old-")
            or label.startswith("extra-")
        ):
            return {
                "ownership": "records",
                "lifecycle_class": "records",
                "expected_destination_class": "records",
                "disposition": "migrate",
            }
        if label.endswith("adapters") or label.endswith("pointer"):
            return {
                "ownership": "host-adapter-candidate",
                "lifecycle_class": "host-adapter-candidate",
                "expected_destination_class": "host_adapters",
                "disposition": "migrate",
            }

    if label == "agents":
        first = posix.split("/", 1)[0] if posix else ""
        if first == "workflows":
            return {
                "ownership": "system",
                "lifecycle_class": "system",
                "expected_destination_class": "system",
                "disposition": "migrate",
            }
        if first in {"plans", "prompts", "docs", "comms", "research"}:
            return {
                "ownership": "records",
                "lifecycle_class": "records",
                "expected_destination_class": "records",
                "disposition": "migrate",
            }
        # Infrastructure files every standard install carries (E-03). Without these the
        # inventory fails closed with unknown-owner on real repos. Dispositions match the
        # awphysical Order 11 decision record.
        # 1) The per-repo self-install manifest + its explanatory README -> .aw/system
        #    (the new-layout code already reads the manifest at <system_root>/managed-sections.json).
        if first == "agent-workflows":
            return {
                "ownership": "system",
                "lifecycle_class": "system",
                "expected_destination_class": "system",
                "disposition": "migrate",
                # Drop the legacy "agent-workflows/" wrapper so it lands directly under system/.
                "destination_relpath_override": "system/"
                + (posix.split("/", 1)[1] if "/" in posix else ""),
            }
        # 2) The tracked leak-sanitizer allowlist + its example -> .aw/config (project config).
        if posix in {"local-leaks-allowlist.toml", "local-leaks-hints.json.example"}:
            return {
                "ownership": "config",
                "lifecycle_class": "config",
                "expected_destination_class": "config",
                "disposition": "migrate",
            }
        # 3) The human-facing layout README -> regenerated as .aw/README.md (doc; not a record).
        if posix == "README.md":
            return {
                "ownership": "doc",
                "lifecycle_class": "doc",
                "expected_destination_class": "doc",
                "disposition": "regenerate",
                "destination_relpath_override": "README.md",
            }
        return {
            "ownership": "unknown",
            "lifecycle_class": "review-required",
            "expected_destination_class": "unknown",
            "disposition": "block-unknown",
        }
    if label == "workflow-artifacts":
        return {
            "ownership": "records",
            "lifecycle_class": "records",
            "expected_destination_class": "records",
            "disposition": "migrate",
        }
    if label == "installer-backups":
        return {
            "ownership": "state-runtime",
            "lifecycle_class": "state-runtime",
            "expected_destination_class": "durable_state",
            "disposition": "preserve",
        }
    if label == "partial-aw":
        first = posix.split("/", 1)[0] if posix else ""
        if first in {"config", "policy"}:
            return {
                "ownership": "config",
                "lifecycle_class": "config",
                "expected_destination_class": "config",
                "disposition": "migrate",
            }
        if first in {"state", "durable", "runtime"}:
            return {
                "ownership": "state-runtime",
                "lifecycle_class": "state-runtime",
                "expected_destination_class": "durable_state",
                "disposition": "migrate",
            }
        if first == "records":
            return {
                "ownership": "records",
                "lifecycle_class": "records",
                "expected_destination_class": "records",
                "disposition": "migrate",
            }
        return {
            "ownership": "unknown",
            "lifecycle_class": "review-required",
            "expected_destination_class": "unknown",
            "disposition": "block-unknown",
        }
    if label.endswith("adapters") or label.endswith("pointer"):
        return {
            "ownership": "host-adapter-candidate",
            "lifecycle_class": "host-adapter-candidate",
            "expected_destination_class": "host_adapters",
            "disposition": "migrate",
        }
    if (
        label.startswith("ext-")
        or label.startswith("old-")
        or label.startswith("extra-")
    ):
        first = posix.split("/", 1)[0] if posix else ""
        if first in {"records", "plans", "docs", "prompts"}:
            return {
                "ownership": "records",
                "lifecycle_class": "records",
                "expected_destination_class": "records",
                "disposition": "migrate",
            }
        if first in {"config", "state"}:
            return {
                "ownership": "config",
                "lifecycle_class": "config",
                "expected_destination_class": "config",
                "disposition": "migrate",
            }
        return {
            "ownership": "records",
            "lifecycle_class": "records",
            "expected_destination_class": "records",
            "disposition": "migrate",
        }
    return {
        "ownership": "unknown",
        "lifecycle_class": "unknown",
        "expected_destination_class": "unknown",
        "disposition": "block-unknown",
    }


def _legacy_class(label: str, relpath: str) -> str:
    """Conservatively classify a legacy item for human migration review."""

    posix = relpath.strip("/")
    if label == "agents":
        first = posix.split("/", 1)[0] if posix else ""
        if first == "workflows":
            return "system"
        if first in {"plans", "prompts", "docs", "comms"}:
            return "records"
        if first == "agent-workflows":
            return "mixed-system-state-review-required"
        return "unknown-agents-content"
    if label == "workflow-artifacts":
        return "records"
    if label == "installer-backups":
        return "state-runtime"
    if label == "partial-aw":
        return "partial-new-layout-review-required"
    if label.endswith("adapters") or label.endswith("pointer"):
        return "host-adapter-candidate"
    return "explicit-extra-root-review-required"


def _repo_relative(path: Path, repo: Path) -> Optional[str]:
    """Return a repo-relative POSIX path without resolving symlinks, or ``None``."""

    try:
        return path.absolute().relative_to(repo.absolute()).as_posix()
    except ValueError:
        return None


def _git_state(
    rel: Optional[str],
    tracked: Set[str],
    untracked: Set[str],
    ignored: Set[str],
    unmerged: Set[str],
) -> str:
    """Classify one repo-relative entry using exact or descendant Git membership."""

    if rel is None:
        return "external"
    prefix = rel.rstrip("/") + "/"
    if rel in unmerged:
        return "unmerged"
    groups = (
        ("tracked", tracked),
        ("untracked", untracked),
        ("ignored", ignored),
        ("unmerged", unmerged),
    )
    matched = [
        name
        for name, paths in groups
        if rel in paths or any(p.startswith(prefix) for p in paths)
    ]
    if len(matched) == 1:
        return matched[0]
    if len(matched) > 1:
        return "mixed:" + ",".join(sorted(matched))
    return "not-listed"


def _ignored_dirs(repo: Path) -> Set[str]:
    """Return repo-relative POSIX paths of gitignored DIRECTORIES.

    ``git ls-files --others --ignored --exclude-standard`` enumerates ignored FILES only,
    so a large ignored subtree (e.g. ``node_modules``) is thousands of file entries with no
    directory to prune on. Asking Git for the ignored directories (``--directory``) lets the
    walk prune the whole subtree WITHOUT descending into or hashing its files. Trailing
    slashes are stripped so the values compare cleanly against ``os.walk`` dir paths.
    """

    raw = _nul_paths(
        repo,
        [
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--directory",
            "-z",
        ],
    )
    return {p.rstrip("/") for p in raw}


def _walk(
    root: Path, ignored_dirs: Optional[Set[str]] = None, repo: Optional[Path] = None
) -> Iterable[Path]:
    """Yield root and descendants deterministically without following symlinks.

    Prunes ``.git`` and any gitignored DIRECTORY subtree (via ``ignored_dirs``, repo-relative
    POSIX paths) so dependency/runtime noise such as ``node_modules`` is never descended into
    or hashed. Individual gitignored files are filtered by the caller (item loop) using the
    ignored file set; this pruning is the coarse, cheap cut for whole ignored subtrees.
    """

    ignored_dirs = ignored_dirs or set()
    yield root
    if not root.is_dir() or root.is_symlink():
        return
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)

        def _is_ignored_dir(name: str) -> bool:
            if repo is None:
                return False
            rel = _repo_relative(current_path / name, repo)
            return rel is not None and rel in ignored_dirs

        dirnames[:] = sorted(
            d for d in dirnames if d != ".git" and not _is_ignored_dir(d)
        )
        for name in dirnames:
            yield current_path / name
        for name in sorted(filenames):
            yield current_path / name


def inventory(
    repo: Path, roots: Sequence[Tuple[str, Path]], include_paths: bool
) -> Dict[str, Any]:
    """Build a complete JSON-serializable inventory for declared roots."""

    tracked, untracked, ignored, unmerged, common_dir = git_sets(repo)
    ignored_dirs = _ignored_dirs(repo)
    items: List[Dict[str, Any]] = []
    root_docs: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    seen_paths: Dict[str, str] = {}

    for label, root in roots:
        root_key = str(root.absolute())
        if root_key in seen_paths:
            errors.append(
                {
                    "rule": "duplicate-root",
                    "detail": f"{label} aliases {seen_paths[root_key]}",
                }
            )
            continue
        seen_paths[root_key] = label
        root_doc: Dict[str, Any] = {
            "name": label,
            "exists": root.exists() or root.is_symlink(),
            "within_repo": _repo_relative(root, repo) is not None,
        }
        if include_paths:
            root_doc["path"] = str(root)
        root_docs.append(root_doc)
        if not root_doc["exists"]:
            continue
        try:
            for path in _walk(root, ignored_dirs=ignored_dirs, repo=repo):
                rel = "." if path == root else path.relative_to(root).as_posix()
                repo_rel = _repo_relative(path, repo)
                st = path.lstat()
                if stat.S_ISLNK(st.st_mode):
                    kind = "symlink"
                    digest = None
                    link_target = os.readlink(path)
                elif stat.S_ISREG(st.st_mode):
                    kind = "file"
                    digest = sha256_file(path)
                    link_target = None
                elif stat.S_ISDIR(st.st_mode):
                    kind = "directory"
                    digest = None
                    link_target = None
                else:
                    kind = "unsupported"
                    digest = None
                    link_target = None
                identity_material = (
                    f"{label}\0{rel}\0{kind}\0{digest or ''}\0{link_target or ''}"
                )
                item_id = hashlib.sha256(
                    identity_material.encode("utf-8", "surrogateescape")
                ).hexdigest()
                cls_info = classify_item(label, rel, repo_rel)
                git_st = _git_state(repo_rel, tracked, untracked, ignored, unmerged)

                item: Dict[str, Any] = {
                    "item_id": item_id,
                    "source_root": label,
                    "source_relpath": rel,
                    "kind": kind,
                    "legacy_class": _legacy_class(label, rel),
                    "ownership": cls_info["ownership"],
                    "lifecycle_class": cls_info["lifecycle_class"],
                    "expected_destination_class": cls_info[
                        "expected_destination_class"
                    ],
                    "disposition": cls_info["disposition"],
                    "size": st.st_size,
                    "mode": stat.S_IMODE(st.st_mode),
                    "sha256": digest,
                    "symlink_target": link_target,
                    "git_state": git_st,
                    "repo_relpath": repo_rel,
                }
                if cls_info.get("destination_relpath_override") is not None:
                    item["destination_relpath_override"] = cls_info[
                        "destination_relpath_override"
                    ]
                items.append(item)

                if kind == "unsupported":
                    errors.append(
                        {
                            "rule": "unsupported-type",
                            "detail": f"{label}:{rel} has unsupported file type",
                            "item_id": item_id,
                        }
                    )
                if (
                    item["ownership"] == "unknown"
                    or item["disposition"] == "block-unknown"
                ):
                    errors.append(
                        {
                            "rule": "unknown-owner",
                            "detail": f"{label}:{rel} has unknown owner/disposition",
                            "item_id": item_id,
                        }
                    )
                if kind == "symlink" and link_target:
                    target_path = (path.parent / link_target).resolve()
                    try:
                        target_path.relative_to(repo.resolve())
                    except ValueError:
                        errors.append(
                            {
                                "rule": "unsafe-symlink",
                                "detail": f"Symlink {label}:{rel} targets outside repository: {link_target}",
                                "item_id": item_id,
                            }
                        )
                if git_st == "unmerged":
                    errors.append(
                        {
                            "rule": "unmerged-git-state",
                            "detail": f"Git file {label}:{rel} is in unmerged state",
                            "item_id": item_id,
                        }
                    )
        except (OSError, ValueError) as exc:
            errors.append(
                {"rule": "inventory-read-failed", "detail": f"{label}: {exc}"}
            )

    items.sort(
        key=lambda item: (item["source_root"], item["source_relpath"], item["kind"])
    )
    canonical = json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "inventory_id": hashlib.sha256(canonical).hexdigest(),
        "repository": {
            "git": common_dir is not None,
            "git_common_dir_present": common_dir is not None,
        },
        "roots": root_docs,
        "items": items,
        "errors": errors,
        "valid": not errors and all(item["kind"] != "unsupported" for item in items),
    }
    if include_paths and common_dir is not None:
        result["repository"]["git_common_dir"] = common_dir
    return result


def build_migration_map(
    repo: Path,
    inv_doc: Dict[str, Any],
    target_backend: str = "repository",
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate deterministic source-to-destination migration map (E-04)."""
    items = inv_doc.get("items", [])
    map_items: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = list(inv_doc.get("errors", []))
    dest_seen: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for item in items:
        source_id = item["item_id"]
        source_root = item["source_root"]
        source_relpath = item["source_relpath"]
        dest_class = item.get("expected_destination_class", "unknown")

        override = item.get("destination_relpath_override")
        if override is not None:
            dest_relpath = override
        elif dest_class == "system":
            dest_relpath = f"system/{source_relpath}"
        elif dest_class == "records":
            dest_relpath = f"records/{source_relpath}"
        elif dest_class == "durable_state":
            dest_relpath = f"state/durable/{source_relpath}"
        elif dest_class == "config":
            dest_relpath = f"config/{source_relpath}"
        elif dest_class == "host_adapters":
            dest_relpath = f"adapters/{source_relpath}"
        elif dest_class == "doc":
            # Layout README regenerated at the .aw root (not under a subclass).
            dest_relpath = source_relpath
        else:
            dest_relpath = f"unknown/{source_relpath}"

        dest_key = (dest_class, dest_relpath)
        collision_policy = "fail_on_collision"
        if dest_key in dest_seen:
            prev = dest_seen[dest_key]
            if prev["sha256"] == item["sha256"] and item["sha256"] is not None:
                collision_policy = "deduplicate_identical"
            else:
                errors.append(
                    {
                        "rule": "destination-collision",
                        "detail": f"Destination collision at {dest_class}:{dest_relpath} between {prev['source_root']}:{prev['source_relpath']} and {source_root}:{source_relpath}",
                        "item_id": source_id,
                    }
                )

        dest_seen[dest_key] = item

        map_item: Dict[str, Any] = {
            "item_id": source_id,
            "source_root": source_root,
            "source_relpath": source_relpath,
            "target_git_boundary": target_backend,
            "destination_root_class": dest_class,
            "destination_relpath": dest_relpath,
            "copy_method": "copy"
            if item.get("disposition") == "migrate"
            else "preserve",
            "track_ignore_expectation": "tracked"
            if item.get("git_state") == "tracked"
            else "untracked",
            "collision_policy": collision_policy,
            "compatibility_retention": "pointer"
            if source_root.endswith("pointer")
            else "none",
            "rollback_source": source_relpath,
            "disposition": item.get("disposition", "unknown"),
        }
        map_items.append(map_item)

    map_items.sort(key=lambda m: (m["source_root"], m["source_relpath"]))
    canonical = json.dumps(map_items, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "map_id": hashlib.sha256(canonical).hexdigest(),
        "inventory_id": inv_doc.get("inventory_id"),
        "target_backend": target_backend,
        "items": map_items,
        "errors": errors,
        "valid": not errors,
    }


def analyze_migration_risks(
    repo: Path,
    inv_doc: Dict[str, Any],
    map_doc: Optional[Dict[str, Any]] = None,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Analyze migration preflight risks and return structured report (E-05)."""
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    for err in inv_doc.get("errors", []):
        if err not in errors:
            errors.append(err)
    if map_doc:
        for err in map_doc.get("errors", []):
            if err not in errors:
                errors.append(err)

    for root in inv_doc.get("roots", []):
        if not root.get("exists", False):
            warnings.append(
                {
                    "rule": "inaccessible-root",
                    "detail": f"Root {root.get('name')} does not exist or is inaccessible",
                }
            )

    total_bytes = sum(item.get("size", 0) for item in inv_doc.get("items", []))
    try:
        usage = shutil.disk_usage(repo)
        available = usage.free
        if total_bytes > available:
            errors.append(
                {
                    "rule": "insufficient-space",
                    "detail": f"Insufficient disk space: required {total_bytes} bytes, available {available} bytes",
                }
            )
    except Exception:
        pass

    target_aw = repo / ".aw"
    if target_aw.exists() and not os.access(target_aw, os.W_OK):
        errors.append(
            {
                "rule": "permission-failure",
                "detail": f"Target directory is not writable: {target_aw}",
            }
        )

    item_counts = {
        "total": len(inv_doc.get("items", [])),
        "files": sum(
            1 for item in inv_doc.get("items", []) if item.get("kind") == "file"
        ),
        "directories": sum(
            1 for item in inv_doc.get("items", []) if item.get("kind") == "directory"
        ),
        "symlinks": sum(
            1 for item in inv_doc.get("items", []) if item.get("kind") == "symlink"
        ),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "item_counts": item_counts,
        "total_bytes": total_bytes,
        "no_write_proven": True,
    }


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON atomically to the explicitly requested evidence path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=".",
        help="Target repository root (default: current directory).",
    )
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Additional or replacement root to inventory; repeatable.",
    )
    parser.add_argument(
        "--no-default-roots",
        action="store_true",
        help="Inventory only roots supplied with --root.",
    )
    parser.add_argument(
        "--include-root-paths",
        action="store_true",
        help="Include absolute root and Git paths in private evidence output.",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Generate migration map and risk analysis in addition to inventory.",
    )
    parser.add_argument(
        "--target-backend",
        default="repository",
        choices=["repository", "companion", "home"],
        help="Target backend for migration map generation.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write JSON atomically to this path; otherwise print to stdout.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the inventory CLI and return 0 only for a complete valid inventory."""

    args = build_parser().parse_args(argv)
    repo = Path(args.repo).expanduser().absolute()
    if not repo.is_dir():
        print(
            json.dumps(
                {
                    "valid": False,
                    "errors": [{"rule": "repo-missing", "detail": str(repo)}],
                }
            )
        )
        return 2
    try:
        roots = [] if args.no_default_roots else _default_roots(repo)
        roots.extend(parse_root(value, repo) for value in args.root)
        if not roots:
            raise InventoryError(
                "no existing default roots and no --root values were supplied"
            )
        inv_res = inventory(repo, roots, args.include_root_paths)
        if args.plan:
            map_res = build_migration_map(
                repo, inv_res, target_backend=args.target_backend
            )
            risk_res = analyze_migration_risks(repo, inv_res, map_res)
            result = {
                "schema_version": SCHEMA_VERSION,
                "inventory": inv_res,
                "migration_map": map_res,
                "risk_analysis": risk_res,
                "valid": inv_res.get("valid", False)
                and map_res.get("valid", False)
                and risk_res.get("valid", False),
            }
        else:
            result = inv_res
    except InventoryError as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "errors": [{"rule": "argument-error", "detail": str(exc)}],
        }
    if args.output:
        _atomic_json(Path(args.output).expanduser().absolute(), result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid") else 2


if __name__ == "__main__":
    sys.exit(main())
