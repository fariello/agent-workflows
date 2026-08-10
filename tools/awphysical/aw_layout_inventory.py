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


def git_sets(repo: Path) -> Tuple[Set[str], Set[str], Set[str], Optional[str]]:
    """Collect tracked, untracked, ignored paths and the Git common directory."""

    inside = _run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return set(), set(), set(), None
    tracked = _nul_paths(repo, ["ls-files", "-z"])
    untracked = _nul_paths(repo, ["ls-files", "--others", "--exclude-standard", "-z"])
    ignored = _nul_paths(
        repo, ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"]
    )
    common = _run_git(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    common_dir = common.stdout.strip() if common.returncode == 0 else None
    return tracked, untracked, ignored, common_dir


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
    rel: Optional[str], tracked: Set[str], untracked: Set[str], ignored: Set[str]
) -> str:
    """Classify one repo-relative entry using exact or descendant Git membership."""

    if rel is None:
        return "external"
    prefix = rel.rstrip("/") + "/"
    groups = (("tracked", tracked), ("untracked", untracked), ("ignored", ignored))
    matched = [
        name
        for name, paths in groups
        if rel in paths or any(p.startswith(prefix) for p in paths)
    ]
    if len(matched) == 1:
        return matched[0]
    if len(matched) > 1:
        return "mixed:" + ",".join(matched)
    return "not-listed"


def _walk(root: Path) -> Iterable[Path]:
    """Yield root and descendants deterministically without following symlinks."""

    yield root
    if not root.is_dir() or root.is_symlink():
        return
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        current_path = Path(current)
        for name in dirnames:
            yield current_path / name
        for name in sorted(filenames):
            yield current_path / name


def inventory(
    repo: Path, roots: Sequence[Tuple[str, Path]], include_paths: bool
) -> Dict[str, Any]:
    """Build a complete JSON-serializable inventory for declared roots."""

    tracked, untracked, ignored, common_dir = git_sets(repo)
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
            for path in _walk(root):
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
                item: Dict[str, Any] = {
                    "item_id": hashlib.sha256(
                        identity_material.encode("utf-8", "surrogateescape")
                    ).hexdigest(),
                    "source_root": label,
                    "source_relpath": rel,
                    "kind": kind,
                    "legacy_class": _legacy_class(label, rel),
                    "size": st.st_size,
                    "mode": stat.S_IMODE(st.st_mode),
                    "sha256": digest,
                    "symlink_target": link_target,
                    "git_state": _git_state(repo_rel, tracked, untracked, ignored),
                    "repo_relpath": repo_rel,
                }
                items.append(item)
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
        result = inventory(repo, roots, args.include_root_paths)
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
