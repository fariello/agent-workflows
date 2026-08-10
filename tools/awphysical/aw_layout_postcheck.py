#!/usr/bin/env python3
"""Perform read-only structural and Git checks after an AW layout migration.

The planning tool consumes a saved context evidence document. It never trusts a migration
summary and never repairs findings. The production implementation may extend the schema, but
must preserve the rule IDs and fail-closed behavior represented here.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


SCHEMA_VERSION = 1
REQUIRED_ROOTS = (
    "system",
    "config_project",
    "config_local",
    "state_durable",
    "state_runtime",
    "records",
)
LEGACY_WRITE_PREFIXES = (
    ".agents/plans",
    ".agents/prompts",
    ".agents/docs",
    ".agents/comms",
    "workflow-artifacts",
)


class PostcheckError(Exception):
    """Raised when postcheck evidence cannot be parsed safely."""


def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON object from an evidence file."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PostcheckError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PostcheckError(f"{path} must contain one JSON object")
    return payload


def _is_within(path: Path, parent: Path) -> bool:
    """Return whether an absolute lexical path is within another path."""

    try:
        path.absolute().relative_to(parent.absolute())
        return True
    except ValueError:
        return False


def _git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run a read-only Git command."""

    return subprocess.run(
        ["git", "-C", str(repo), *args], check=False, capture_output=True, text=True
    )


def _tracked(repo: Path, path: Path) -> Optional[bool]:
    """Return tracked status, or ``None`` when path is outside/not in a Git worktree."""

    if not _is_within(path, repo):
        return None
    rel = path.absolute().relative_to(repo.absolute()).as_posix()
    proc = _git(repo, ["ls-files", "--error-unmatch", "--", rel])
    return proc.returncode == 0


def _ignored(repo: Path, path: Path) -> Optional[bool]:
    """Return ignore status, or ``None`` for paths outside the Git worktree."""

    if not _is_within(path, repo):
        return None
    rel = path.absolute().relative_to(repo.absolute()).as_posix()
    proc = _git(repo, ["check-ignore", "-q", "--", rel])
    return proc.returncode == 0


def _finding(
    rule: str, detail: str, root: Optional[str] = None, severity: str = "fail"
) -> Dict[str, str]:
    """Build one stable finding record."""

    result = {"rule": rule, "severity": severity, "detail": detail}
    if root is not None:
        result["root"] = root
    return result


def check_context(context: Mapping[str, Any]) -> Dict[str, Any]:
    """Check root placement, tracking, authority, and producer evidence."""

    findings: List[Dict[str, str]] = []
    roots = context.get("roots")
    if not isinstance(roots, dict):
        raise PostcheckError("context requires a roots object")
    target_raw = context.get("target_repo")
    if not isinstance(target_raw, str):
        raise PostcheckError("context requires target_repo")
    target = Path(target_raw).expanduser().absolute()

    paths: Dict[str, Path] = {}
    policies: Dict[str, str] = {}
    for name in REQUIRED_ROOTS:
        entry = roots.get(name)
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            findings.append(
                _finding("root-missing", "required root/class is absent", name)
            )
            continue
        paths[name] = Path(entry["path"]).expanduser().absolute()
        policies[name] = str(entry.get("git_policy", "unknown"))

    # Physical target roots must use their canonical .aw prefixes. Local/runtime classes
    # may be elsewhere, but if target-resident they still require their exact subtrees.
    expected_target_suffixes = {
        "system": Path(".aw/system"),
        "config_project": Path(".aw/config"),
        "config_local": Path(".aw/config/local.json"),
        "state_durable": Path(".aw/state/durable"),
        "state_runtime": Path(".aw/state/runtime"),
        "records": Path(".aw/records"),
    }
    for name, path in paths.items():
        if _is_within(path, target):
            expected = target / expected_target_suffixes[name]
            if name in {"config_project", "state_durable", "state_runtime"}:
                # A class may point to a descendant of its canonical subtree.
                if not _is_within(path, expected):
                    findings.append(
                        _finding(
                            "target-root-noncanonical",
                            f"{path} is not under {expected}",
                            name,
                        )
                    )
            elif path != expected:
                findings.append(
                    _finding("target-root-noncanonical", f"{path} != {expected}", name)
                )

    # System, records, and durable state must not overlap. Runtime may be beneath state but
    # must not contain durable state. Config local may be a file within the config subtree.
    separated = ("system", "state_durable", "records")
    for index, left in enumerate(separated):
        for right in separated[index + 1 :]:
            if (
                left in paths
                and right in paths
                and (
                    _is_within(paths[left], paths[right])
                    or _is_within(paths[right], paths[left])
                )
            ):
                findings.append(_finding("root-overlap", f"{left} and {right} overlap"))
    if (
        "state_runtime" in paths
        and "state_durable" in paths
        and _is_within(paths["state_durable"], paths["state_runtime"])
    ):
        findings.append(
            _finding(
                "durable-inside-runtime",
                "durable state is nested beneath runtime state",
            )
        )

    for name in ("config_local", "state_runtime"):
        if name not in paths:
            continue
        if policies.get(name) == "tracked":
            findings.append(
                _finding(
                    "prohibited-tracking-policy", f"{name} may never be tracked", name
                )
            )
        if _is_within(paths[name], target):
            tracked = _tracked(target, paths[name])
            ignored = _ignored(target, paths[name])
            if tracked:
                findings.append(
                    _finding(
                        "prohibited-path-tracked", f"{paths[name]} is tracked", name
                    )
                )
            if paths[name].exists() and ignored is False:
                findings.append(
                    _finding(
                        "prohibited-path-not-ignored",
                        f"{paths[name]} exists but is not ignored",
                        name,
                    )
                )

    authoritative = context.get("authoritative_layout")
    if authoritative != "physical-aw-v2":
        findings.append(
            _finding(
                "authority-invalid",
                f"unexpected authoritative_layout: {authoritative!r}",
            )
        )
    migration = context.get("migration")
    if isinstance(migration, dict):
        phase = migration.get("phase")
        if phase not in {"verified", "independently-reviewed", "not-required"}:
            findings.append(
                _finding("migration-not-verified", f"migration phase is {phase!r}")
            )
        if migration.get("legacy_writer_enabled") is True:
            findings.append(
                _finding("legacy-writer-enabled", "legacy writer remains enabled")
            )
        if migration.get("rollback_ready") is not True and phase != "not-required":
            findings.append(
                _finding("rollback-not-ready", "migration is not rollback-ready")
            )
    else:
        findings.append(
            _finding("migration-evidence-missing", "context has no migration evidence")
        )

    producer_routes = context.get("producer_routes")
    if not isinstance(producer_routes, list):
        findings.append(
            _finding(
                "producer-evidence-missing", "context has no producer_routes array"
            )
        )
    else:
        seen = set()
        for route in producer_routes:
            if not isinstance(route, dict):
                findings.append(
                    _finding(
                        "producer-route-malformed", "producer route is not an object"
                    )
                )
                continue
            producer = str(route.get("producer", ""))
            destination = str(route.get("logical_destination", ""))
            if not producer or producer in seen:
                findings.append(
                    _finding(
                        "producer-route-duplicate",
                        f"invalid or duplicate producer {producer!r}",
                    )
                )
            seen.add(producer)
            if destination.startswith(LEGACY_WRITE_PREFIXES):
                findings.append(
                    _finding(
                        "producer-legacy-write", f"{producer} routes to {destination}"
                    )
                )
            if route.get("verified") is not True:
                findings.append(
                    _finding(
                        "producer-unverified", f"{producer} lacks a verified route"
                    )
                )

    return {
        "schema_version": SCHEMA_VERSION,
        "valid": not any(item["severity"] == "fail" for item in findings),
        "finding_count": len(findings),
        "findings": findings,
        "checked_roots": sorted(paths),
    }


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically write a postcheck evidence file."""

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
    parser.add_argument(
        "--context", required=True, help="Saved resolved-context evidence JSON."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write report JSON atomically; otherwise print it.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run postcheck and return nonzero for any missing, invalid, or failed evidence."""

    args = build_parser().parse_args(argv)
    try:
        context = load_json(Path(args.context).expanduser().absolute())
        report = check_context(context)
    except PostcheckError as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "finding_count": 1,
            "findings": [_finding("input-error", str(exc))],
        }
    if args.output:
        _atomic_json(Path(args.output).expanduser().absolute(), report)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("valid") else 2


if __name__ == "__main__":
    sys.exit(main())
