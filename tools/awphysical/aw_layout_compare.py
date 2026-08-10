#!/usr/bin/env python3
"""Compare a frozen AW migration inventory and approved map with actual files.

This tool is intentionally read-only except for an explicitly requested JSON evidence file.
It does not repair differences. Every inventory item must appear exactly once in the migration
map, and exclusions require explicit approval plus a reason.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = 1
ALLOWED_DISPOSITIONS = frozenset({"copy", "deduplicate", "retain", "exclude"})


class CompareError(Exception):
    """Raised when evidence inputs are malformed or incomplete."""


def load_json(path: Path) -> Dict[str, Any]:
    """Load one JSON object or raise a precise input error."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompareError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CompareError(f"{path} must contain one JSON object")
    return payload


def parse_binding(value: str) -> Tuple[str, Path]:
    """Parse a root binding in the form ``NAME=PATH``."""

    if "=" not in value:
        raise CompareError(f"root binding requires NAME=PATH, got {value!r}")
    name, raw = value.split("=", 1)
    if not name or any(
        ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        for ch in name
    ):
        raise CompareError(f"unsafe root binding name: {name!r}")
    return name, Path(raw).expanduser().absolute()


def sha256_file(path: Path) -> str:
    """Hash a regular file in bounded chunks."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_path(path: Path) -> Dict[str, Any]:
    """Return comparable metadata without following symlinks."""

    if not path.exists() and not path.is_symlink():
        return {"exists": False}
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode):
        return {
            "exists": True,
            "kind": "symlink",
            "symlink_target": os.readlink(path),
            "mode": stat.S_IMODE(st.st_mode),
            "size": st.st_size,
        }
    if stat.S_ISREG(st.st_mode):
        return {
            "exists": True,
            "kind": "file",
            "sha256": sha256_file(path),
            "mode": stat.S_IMODE(st.st_mode),
            "size": st.st_size,
        }
    if stat.S_ISDIR(st.st_mode):
        return {
            "exists": True,
            "kind": "directory",
            "mode": stat.S_IMODE(st.st_mode),
            "size": st.st_size,
        }
    return {
        "exists": True,
        "kind": "unsupported",
        "mode": stat.S_IMODE(st.st_mode),
        "size": st.st_size,
    }


def _safe_join(root: Path, relpath: str) -> Path:
    """Join an inventory relative path without permitting traversal."""

    if relpath == ".":
        return root
    rel = Path(relpath)
    if rel.is_absolute() or ".." in rel.parts:
        raise CompareError(f"unsafe relative path: {relpath!r}")
    return root / rel


def _compare_expected(item: Mapping[str, Any], actual: Mapping[str, Any]) -> List[str]:
    """Return field names that do not match inventory expectations."""

    mismatches: List[str] = []
    if not actual.get("exists"):
        return ["exists"]
    for key in ("kind", "sha256", "symlink_target"):
        expected = item.get(key)
        if expected is not None and actual.get(key) != expected:
            mismatches.append(key)
    return mismatches


def compare(
    inventory: Mapping[str, Any],
    migration_map: Mapping[str, Any],
    sources: Mapping[str, Path],
    destinations: Mapping[str, Path],
) -> Dict[str, Any]:
    """Compare all inventory/map items and return a rule-based report."""

    findings: List[Dict[str, Any]] = []
    inv_items = inventory.get("items")
    map_items = migration_map.get("items")
    if not isinstance(inv_items, list) or not isinstance(map_items, list):
        raise CompareError("inventory and map must each contain an items array")
    if migration_map.get("inventory_id") != inventory.get("inventory_id"):
        findings.append(
            {
                "rule": "inventory-id-mismatch",
                "severity": "fail",
                "detail": "map does not bind this frozen inventory",
            }
        )

    inv_by_id: Dict[str, Mapping[str, Any]] = {}
    for item in inv_items:
        if not isinstance(item, dict) or not isinstance(item.get("item_id"), str):
            raise CompareError("every inventory item requires a string item_id")
        item_id = item["item_id"]
        if item_id in inv_by_id:
            findings.append(
                {
                    "rule": "duplicate-inventory-item",
                    "severity": "fail",
                    "item_id": item_id,
                }
            )
        inv_by_id[item_id] = item

    map_by_id: Dict[str, List[Mapping[str, Any]]] = {}
    for item in map_items:
        if not isinstance(item, dict) or not isinstance(item.get("item_id"), str):
            raise CompareError("every map item requires a string item_id")
        map_by_id.setdefault(item["item_id"], []).append(item)

    for unknown in sorted(set(map_by_id) - set(inv_by_id)):
        findings.append(
            {"rule": "unknown-map-item", "severity": "fail", "item_id": unknown}
        )

    checked: List[Dict[str, Any]] = []
    for item_id, inv_item in sorted(inv_by_id.items()):
        mappings = map_by_id.get(item_id, [])
        if len(mappings) != 1:
            findings.append(
                {
                    "rule": "missing-map-item"
                    if not mappings
                    else "duplicate-map-item",
                    "severity": "fail",
                    "item_id": item_id,
                    "count": len(mappings),
                }
            )
            continue
        mapping = mappings[0]
        disposition = mapping.get("disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            findings.append(
                {
                    "rule": "invalid-disposition",
                    "severity": "fail",
                    "item_id": item_id,
                    "value": disposition,
                }
            )
            continue

        source_root_name = inv_item.get("source_root")
        source_root = sources.get(str(source_root_name))
        if source_root is None:
            findings.append(
                {
                    "rule": "source-root-unbound",
                    "severity": "fail",
                    "item_id": item_id,
                    "root": source_root_name,
                }
            )
            continue
        source_path = _safe_join(source_root, str(inv_item.get("source_relpath", ".")))
        source_actual = inspect_path(source_path)

        if disposition == "exclude":
            if (
                mapping.get("approved") is not True
                or not str(mapping.get("reason", "")).strip()
            ):
                findings.append(
                    {
                        "rule": "unapproved-exclusion",
                        "severity": "fail",
                        "item_id": item_id,
                    }
                )
            checked.append(
                {
                    "item_id": item_id,
                    "disposition": disposition,
                    "source_exists": source_actual.get("exists", False),
                }
            )
            continue

        if disposition == "retain":
            mismatches = _compare_expected(inv_item, source_actual)
            if mismatches:
                findings.append(
                    {
                        "rule": "retained-source-mismatch",
                        "severity": "fail",
                        "item_id": item_id,
                        "fields": mismatches,
                    }
                )
            checked.append(
                {
                    "item_id": item_id,
                    "disposition": disposition,
                    "verified": not mismatches,
                }
            )
            continue

        destination_root_name = mapping.get("destination_root")
        destination_root = destinations.get(str(destination_root_name))
        destination_relpath = mapping.get("destination_relpath")
        if destination_root is None or not isinstance(destination_relpath, str):
            findings.append(
                {
                    "rule": "destination-unbound",
                    "severity": "fail",
                    "item_id": item_id,
                    "root": destination_root_name,
                }
            )
            continue
        destination_path = _safe_join(destination_root, destination_relpath)
        destination_actual = inspect_path(destination_path)
        mismatches = _compare_expected(inv_item, destination_actual)
        if mismatches:
            findings.append(
                {
                    "rule": "destination-mismatch",
                    "severity": "fail",
                    "item_id": item_id,
                    "fields": mismatches,
                }
            )
        if disposition == "copy" and not source_actual.get("exists"):
            findings.append(
                {
                    "rule": "source-missing-before-retention-release",
                    "severity": "fail",
                    "item_id": item_id,
                }
            )
        checked.append(
            {
                "item_id": item_id,
                "disposition": disposition,
                "verified": not mismatches,
                "source_retained": source_actual.get("exists", False),
            }
        )

    canonical = json.dumps(checked, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "inventory_id": inventory.get("inventory_id"),
        "comparison_id": hashlib.sha256(canonical).hexdigest(),
        "valid": not any(finding.get("severity") == "fail" for finding in findings),
        "counts": {
            "inventory": len(inv_items),
            "mapped": len(map_items),
            "checked": len(checked),
            "findings": len(findings),
        },
        "findings": findings,
        "checked": checked,
    }


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically write the requested evidence report."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def build_parser() -> argparse.ArgumentParser:
    """Create the command parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, help="Frozen inventory JSON.")
    parser.add_argument(
        "--map",
        required=True,
        dest="map_path",
        help="Human-approved migration map JSON.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Bind an inventory source root; repeatable.",
    )
    parser.add_argument(
        "--destination",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Bind a destination root; repeatable.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write report JSON atomically; otherwise print it.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run comparison and return nonzero for malformed or invalid evidence."""

    args = build_parser().parse_args(argv)
    try:
        inventory = load_json(Path(args.inventory).expanduser().absolute())
        migration_map = load_json(Path(args.map_path).expanduser().absolute())
        sources = dict(parse_binding(value) for value in args.source)
        destinations = dict(parse_binding(value) for value in args.destination)
        report = compare(inventory, migration_map, sources, destinations)
    except CompareError as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "findings": [
                {"rule": "input-error", "severity": "fail", "detail": str(exc)}
            ],
        }
    if args.output:
        _atomic_json(Path(args.output).expanduser().absolute(), report)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("valid") else 2


if __name__ == "__main__":
    sys.exit(main())
