"""Release records (ship-gate anchors, awrelease). A release record is a thin `.release.md` file
under `.aw/records/releases/` naming a planned release + its status; items gate it via `Blocks-Release`
(awrelease Order 02). This module creates + validates release records. Pure (returns paths/Drift)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import List, Optional

from agent_workflows import artifact_core as _core

RELEASE_STATUSES = ("planned", "blocked", "shipped")

_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")
_VERSION_RE = re.compile(r"(?m)^- Version:\s*(\S+)\s*$")


def _releases_dir(repo_root: Path) -> Path:
    return Path(repo_root) / ".aw" / "records" / "releases"


def _existing_ids(repo_root: Path) -> set:
    ids: set = set()
    d = _releases_dir(repo_root)
    if d.is_dir():
        for p in d.rglob("*.release.md"):
            m = _ID_RE.search(p.read_text(encoding="utf-8"))
            if m:
                ids.add(m.group(1))
    return ids


def create_release(
    repo_root: Path, version: str, summary: str, status: str = "planned"
) -> Path:
    """Create a conformant `<YYYYMMDD>-<id6>-01-<id6>-<slug>.release.md` (setid = id6 for a standalone)
    and return its path. Status defaults to 'planned'."""
    repo_root = Path(repo_root)
    if status not in RELEASE_STATUSES:
        raise ValueError(
            f"release status must be one of {RELEASE_STATUSES}, got {status!r}"
        )
    id6 = _core.generate_id6(_existing_ids(repo_root))
    slug = _core.kebab(version) or "release"
    today = date.today().strftime("%Y%m%d")
    name = f"{today}-{id6}-01-{id6}-{slug}.release.md"
    d = _releases_dir(repo_root)
    d.mkdir(parents=True, exist_ok=True)
    body = (
        f"# Release: {version}\n\n"
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        f"- Version: {version}\n"
        f"- Summary: {summary}\n\n"
        "## Workflow history\n\n"
        f"- {date.today().strftime('%Y-%m-%d')} created (aw releases): {summary}\n"
    )
    path = d / name
    path.write_text(body, encoding="utf-8")
    return path


def validate_release(path: Path, text: str) -> List[_core.Drift]:
    """Validate a release record's front-matter. Returns Drift for a bad status, missing Version,
    or an invalid/missing id6."""
    loc = str(path)
    drift: List[_core.Drift] = []
    m = _ID_RE.search(text)
    if not m:
        drift.append(_core.Drift(loc, "release.id-missing", "no valid `- Id:` (id6)"))
    ms = _STATUS_RE.search(text)
    if ms is None:
        drift.append(_core.Drift(loc, "release.status-missing", "no `- Status:`"))
    elif ms.group(1) not in RELEASE_STATUSES:
        drift.append(
            _core.Drift(
                loc,
                "release.status-invalid",
                f"status {ms.group(1)!r} not in {RELEASE_STATUSES}",
            )
        )
    if _VERSION_RE.search(text) is None:
        drift.append(_core.Drift(loc, "release.version-missing", "no `- Version:`"))
    return drift


_BLOCKS_RELEASE_LINE_RE = re.compile(r"(?m)^- Blocks-Release:[ \t]*\S+[ \t]*$\n?")


def set_blocks_release_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Blocks-Release:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or the top of the bullet block)."""
    # Always strip any existing line first.
    text = _BLOCKS_RELEASE_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    new_line = f"- Blocks-Release: {value}\n"
    # Insert after the `- Status:` line if present, else after `- Id:`, else before the first blank.
    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
        m = re.search(anchor, text)
        if m:
            i = m.end()
            return text[:i] + new_line + text[i:]
    return text


def resolve_release(repo_root: Path, value: str) -> Optional[Path]:
    """Resolve a Blocks-Release value to a release record path: a release id6, or the literal `next`
    (the single release whose Status is 'planned'). Returns None if unresolved (incl. zero/many
    planned releases for `next`)."""
    repo_root = Path(repo_root)
    d = _releases_dir(repo_root)
    if not d.is_dir():
        return None
    if value == "next":
        planned = []
        for p in d.rglob("*.release.md"):
            ms = _STATUS_RE.search(p.read_text(encoding="utf-8"))
            if ms and ms.group(1) == "planned":
                planned.append(p)
        return planned[0] if len(planned) == 1 else None
    if _core.ID6_RE.match(value):
        for p in d.rglob("*.release.md"):
            m = _ID_RE.search(p.read_text(encoding="utf-8"))
            if m and m.group(1) == value:
                return p
    return None


_FROM_BACKLOG_LINE_RE = re.compile(r"(?m)^- From-Backlog:[ \t]*\S+[ \t]*$\n?")


def set_from_backlog_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- From-Backlog:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:`
    (falling back to after `- Id:`, or the top of the bullet block). Mirrors
    `set_blocks_release_line` exactly (bklggrad Order ku93tn)."""
    # Always strip any existing line first.
    text = _FROM_BACKLOG_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    new_line = f"- From-Backlog: {value}\n"
    # Insert after the `- Status:` line if present, else after `- Id:`, else before the first blank.
    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
        m = re.search(anchor, text)
        if m:
            i = m.end()
            return text[:i] + new_line + text[i:]
    return text


_ITEM_DEPENDENCIES_LINE_RE = re.compile(r"(?m)^- Item-Dependencies:[^\n]*\n?")


def set_item_dependencies_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Item-Dependencies:` metadata line set to `value`, or removed when
    `value` is '-' or None. Idempotent: replaces an existing line or inserts one.

    ANCHOR (ipddeps Order g69y23 E-02): spec 25kzda 2.7 mandates this field live IMMEDIATELY AFTER
    `- Scope-Paths:` (and before `Blocks-Release`/`From-Backlog`). This is DELIBERATELY DIFFERENT
    from `set_blocks_release_line`/`set_from_backlog_line`, which anchor after `- Status:` - in the
    real block order (`... Scope-Paths, Status, Set, Order ...`) that would be the WRONG position
    for this field. So anchor after `- Scope-Paths:`; when absent, fall back to inserting BEFORE
    `- Status:` (keeping the field ahead of Status/Set/Order), then after `- Id:`, then top of the
    bullet block. Unlike the release/backlog line regex (which requires a `\\S+` value), this regex
    tolerates any value so an existing malformed line is still replaced idempotently."""
    # Always strip any existing line first (idempotent replace).
    text = _ITEM_DEPENDENCIES_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    new_line = f"- Item-Dependencies: {value}\n"
    # Preferred anchor: immediately AFTER `- Scope-Paths:` (spec 2.7 position).
    m = re.search(r"(?m)^- Scope-Paths:[^\n]*\n", text)
    if m:
        i = m.end()
        return text[:i] + new_line + text[i:]
    # No Scope-Paths line: insert BEFORE `- Status:` so the field stays ahead of Status/Set/Order.
    m = re.search(r"(?m)^- Status:[^\n]*\n", text)
    if m:
        i = m.start()
        return text[:i] + new_line + text[i:]
    # Fallbacks: after `- Id:`, else top of the bullet block (before the first blank/heading).
    m = re.search(r"(?m)^- Id:[^\n]*\n", text)
    if m:
        i = m.end()
        return text[:i] + new_line + text[i:]
    return text


_ITEM_BLOCKS_RELEASE_RE = re.compile(r"(?m)^- Blocks-Release:\s*(\S+)\s*$")
_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^- From-Backlog:\s*(\S+)\s*$")


def check_blocks_release(repo_root: Path) -> List[_core.Drift]:
    """Scan backlog + specs + plans items for a `Blocks-Release` value and flag any that does not
    resolve to an existing release record or 'next' (awrelease Order 02; folds into the awcheck
    engine seam). IPD 7mw7m5 (OQ-01 option a) added `plans` so a plan carrying a dangling
    `- Blocks-Release:` is validated the same as backlog/specs; `rglob` recurses through the
    disposition subdirs (pending/executed/...). This runs in the full cross-tree sweep (`aw check
    all`), not a type-scoped `aw check plans`."""
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    for sub in ("backlog", "specs", "plans"):
        for base in (repo_root / ".aw" / "records" / sub, repo_root / ".agents" / sub):
            if not base.is_dir():
                continue
            for p in base.rglob("*.md"):
                if p.name in ("README.md", "INDEX.md", "STATUS.md"):
                    continue
                try:
                    text = p.read_text(encoding="utf-8")
                except OSError:
                    continue
                m = _ITEM_BLOCKS_RELEASE_RE.search(text)
                if m and resolve_release(repo_root, m.group(1)) is None:
                    drift.append(
                        _core.Drift(
                            str(p),
                            "check.blocks-release-dangling",
                            f"Blocks-Release {m.group(1)!r} does not resolve to a release record",
                        )
                    )
    return drift


def check_from_backlog(repo_root: Path) -> List[_core.Drift]:
    """Scan plans (and, symmetrically, specs/backlog) for a `From-Backlog` value and flag any that
    does not resolve to an existing backlog item id6 (bklggrad Order ku93tn; folds into the awcheck
    cross-tree sweep the same way `check_blocks_release` does). The graduation link's primary home is
    the plan; the scan tolerates it anywhere for symmetry. `rglob` recurses the disposition subdirs
    (pending/executed/...)."""
    from agent_workflows import (
        backlog as _backlog,
    )  # local import avoids an import cycle

    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    known = _backlog.existing_backlog_ids(repo_root)
    for sub in ("plans", "specs", "backlog"):
        for base in (repo_root / ".aw" / "records" / sub, repo_root / ".agents" / sub):
            if not base.is_dir():
                continue
            for p in base.rglob("*.md"):
                if p.name in ("README.md", "INDEX.md", "STATUS.md"):
                    continue
                try:
                    text = p.read_text(encoding="utf-8")
                except OSError:
                    continue
                m = _ITEM_FROM_BACKLOG_RE.search(text)
                if m and m.group(1) not in known:
                    drift.append(
                        _core.Drift(
                            str(p),
                            "check.from-backlog-dangling",
                            f"From-Backlog {m.group(1)!r} does not resolve to a backlog item",
                        )
                    )
    return drift
