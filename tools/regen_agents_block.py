#!/usr/bin/env python3
"""Repo-local developer tool to regenerate AGENTS.md managed block and reconcile section records.

This module is developer tooling for the agent-workflows framework's own repository checkout
and is not shipped as part of the distributed agent-workflows package (pyproject.toml
packages = ["agent_workflows"]).

In this repository, AGENTS.md changes often land as joint generator-plus-AGENTS.md commits
where the full installer (aw install .) is deliberately not run because of broad sync and
self-commit side effects. This script provides a focused, safe path that rewrites only the
<!-- aw:block --> region of AGENTS.md and re-records section hashes in
.aw/system/managed-sections.json through engine.merge_aw_block, never touching GEMINI.md or
unrelated manifest entries.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

from agent_workflows import engine, manifest


def reconcile(repo_root: Path, *, check: bool = False) -> dict[str, Any]:
    """Reconcile AGENTS.md managed block and manifest section records.

    Args:
        repo_root: Path to the repository root.
        check: If True, check for staleness without writing any files.

    Returns:
        A dict with keys:
            - file: relative path to the agents file (e.g. "AGENTS.md")
            - stale: True if text or records were stale / changed
            - text_changed: True if on-disk managed block differed from generator
            - records_changed: list of section keys whose recorded hashes were updated
            - refused: string reason if reconciliation was refused, else None
    """
    repo_root = Path(repo_root).resolve()
    layout = engine.resolve_target_layout(repo_root)
    rel_file = engine.resolve_agents_file(repo_root)
    agents_path = repo_root / rel_file
    manifest_path = manifest.resolve_manifest_path(repo_root)

    result: dict[str, Any] = {
        "file": rel_file,
        "stale": False,
        "text_changed": False,
        "records_changed": [],
        "refused": None,
    }

    if not agents_path.is_file():
        result["refused"] = f"Agents file not found: {rel_file}"
        return result

    existing = agents_path.read_text(encoding="utf-8")
    m = manifest.load(manifest_path)

    # Refusal checks:
    if engine.AGENTS_BEGIN in existing or engine.AGENTS_END in existing:
        result["refused"] = "Legacy AGENT-WORKFLOWS marker present"
        return result

    parsed = engine.parse_aw_block(existing)
    if not parsed.found:
        result["refused"] = "No aw:block found in agents file"
        return result
    if parsed.ambiguous:
        result["refused"] = "Ambiguous aw:block markers in agents file"
        return result
    if parsed.drift:
        result["refused"] = "Missing /aw:block closing marker (drift)"
        return result

    desired = engine.agents_managed_sections(layout)
    desired_slugs = {s.slug for s in desired}

    for sec in parsed.sections:
        if sec.slug not in desired_slugs:
            result["refused"] = (
                f"On-disk section slug {sec.slug!r} is not in desired managed sections"
            )
            return result

    for slug in desired_slugs:
        key = f"{rel_file}#aw:{slug}"
        if m.is_declined(key):
            result["refused"] = f"Manifest record {key} carries a decline tombstone"
            return result

    # Compute desired new text with manifest=None to bypass stale hash blocks
    new_text, _ = engine.merge_aw_block(existing, desired, manifest=None)
    text_changed = new_text != existing

    if text_changed:
        on_disk_by_slug = {s.slug: s.body for s in parsed.sections}
        changed_slugs = [
            s.slug
            for s in desired
            if s.slug not in on_disk_by_slug
            or manifest.hash_content(on_disk_by_slug[s.slug])
            != manifest.hash_content(s.body)
        ]
        if changed_slugs:
            print(f"Changed sections in {rel_file}: {', '.join(changed_slugs)}")

    # Snapshot recorded hashes for desired sections before recording
    hashes_before = {
        f"{rel_file}#aw:{s.slug}": m.recorded_hash(f"{rel_file}#aw:{s.slug}")
        for s in desired
    }

    # Record hashes through engine.merge_aw_block (consent case 1)
    m_work = copy.deepcopy(m) if check else m
    warnings: list[str] = []
    engine.merge_aw_block(
        new_text, desired, manifest=m_work, file_key=rel_file, warnings=warnings
    )
    assert not warnings, f"Unexpected warnings during hash recording: {warnings}"

    records_changed = [
        k for k in hashes_before if hashes_before[k] != m_work.recorded_hash(k)
    ]

    stale = text_changed or bool(records_changed)
    result["stale"] = stale
    result["text_changed"] = text_changed
    result["records_changed"] = records_changed

    if not check:
        if text_changed:
            agents_path.write_text(new_text, encoding="utf-8")
        if records_changed:
            manifest.save(m_work, manifest_path)

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate AGENTS.md managed block and reconcile section hash records."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether AGENTS.md or its manifest section records are stale without writing.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory (default: current working directory).",
    )
    args = parser.parse_args(argv)

    res = reconcile(args.dir, check=args.check)
    if res.get("refused") is not None:
        print(f"Refused: {res['refused']}", file=sys.stderr)
        return 2

    if args.check:
        if res["stale"]:
            details = []
            if res["text_changed"]:
                details.append("text changed")
            if res["records_changed"]:
                details.append(f"records stale: {', '.join(res['records_changed'])}")
            print(f"Stale: {res['file']} ({'; '.join(details)})")
            return 1
        print(f"Up to date: {res['file']} managed block and section records.")
        return 0

    if res["stale"]:
        changes = []
        if res["text_changed"]:
            changes.append("rewrote managed block")
        if res["records_changed"]:
            changes.append(f"re-recorded {', '.join(res['records_changed'])}")
        print(f"Reconciled {res['file']}: {'; '.join(changes)}")
    else:
        print(f"Already up to date: {res['file']} managed block and section records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
