"""Release records (ship-gate anchors, awrelease). A release record is a thin `.release.md` file
under `.aw/records/releases/` naming a planned release + its status; items gate it via `Blocks-Release`
(awrelease Order 02). This module creates + validates release records. Pure (returns paths/Drift).

IPD w0ln4q added the `aw releases` OWNER VERB layer on top of that core: the `ReleaseRecord` reader
(`list_releases`/`get_release`), the blocker query (`get_release_blockers`, which DELEGATES to
`attention.release_blockers` rather than re-walking `- Blocks-Release:` a second time), and the three
command runners (`run_list`/`run_show`/`run_new`). There is deliberately NO `run_check`: `aw check
releases` already validates release records through `check_engine` -> `validate_release`, and a second
validation entry point would duplicate a canonical path.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core

RELEASE_STATUSES = ("planned", "blocked", "shipped")

_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")
_VERSION_RE = re.compile(r"(?m)^- Version:\s*(\S+)\s*$")
# A release's Summary lives either as a `- Summary:` bullet (the shape `create_release` writes) or as
# a `## Summary` prose section (the shape the hand-authored 2.0.0 record uses). The reader accepts both
# so `aw releases` describes every conformant record, not just the CLI-minted shape.
_SUMMARY_RE = re.compile(r"(?m)^- Summary:[ \t]*(.*?)[ \t]*$")


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


def plan_release(
    repo_root: Path, version: str, summary: str, status: str = "planned"
) -> Tuple[Path, str]:
    """Compute (path, text) for a NEW conformant release record WITHOUT touching the filesystem.

    Factored out of `create_release` (IPD w0ln4q E-02) so `aw releases new` can PREVIEW the exact
    bytes it would write without a second renderer that could drift from the real one. `create_release`
    is this function plus the write, so the previewed text is by construction the written text."""
    repo_root = Path(repo_root)
    if status not in RELEASE_STATUSES:
        raise ValueError(
            f"release status must be one of {RELEASE_STATUSES}, got {status!r}"
        )
    id6 = _core.generate_id6(_existing_ids(repo_root))
    slug = _core.kebab(version) or "release"
    today = date.today().strftime("%Y%m%d")
    name = f"{today}-{id6}-01-{id6}-{slug}.release.md"
    body = (
        f"# Release: {version}\n\n"
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        f"- Version: {version}\n"
        f"- Summary: {summary}\n\n"
        "## Workflow history\n\n"
        f"- {date.today().strftime('%Y-%m-%d')} created (aw releases): {summary}\n"
    )
    return _releases_dir(repo_root) / name, body


def create_release(
    repo_root: Path, version: str, summary: str, status: str = "planned"
) -> Path:
    """Create a conformant `<YYYYMMDD>-<id6>-01-<id6>-<slug>.release.md` (setid = id6 for a standalone)
    and return its path. Status defaults to 'planned'."""
    path, body = plan_release(repo_root, version, summary, status=status)
    path.parent.mkdir(parents=True, exist_ok=True)
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


def describe_planned_release(repo_root: Path) -> Optional[Tuple[str, str]]:
    """Return (id6, version) of THE single planned release, or None if there is not
    exactly one. Used to name the release in surfacing UI (attention/status) so the
    thing that `Blocks-Release: next` gates is visible, not just a blocker count."""
    p = resolve_release(repo_root, "next")
    if p is None:
        return None
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return None
    mid = _ID_RE.search(text)
    mver = _VERSION_RE.search(text)
    return (
        mid.group(1) if mid else "?",
        mver.group(1) if mver else "?",
    )


class ActiveRelease(NamedTuple):
    """The single planned ('active') release, as id6 + version + record path."""

    id6: str
    version: str
    path: Path


def load_active_release(repo_root: Path) -> Optional[ActiveRelease]:
    """Return the single planned release as an ActiveRelease (id6/version/path), or
    None if there is not exactly one. Used by `aw doctor` to name the release line."""
    p = resolve_release(repo_root, "next")
    if p is None:
        return None
    desc = describe_planned_release(repo_root)
    if desc is None:
        return None
    return ActiveRelease(id6=desc[0], version=desc[1], path=p)


# ======================================================================================
# IPD w0ln4q E-01: release query / listing primitives backing the `aw releases` owner verb.
#
# These are READERS over the same `.release.md` files `create_release` writes and `resolve_release`
# resolves. They add NO second source of truth: `get_release` delegates the `next` sentinel to
# `resolve_release`, and `get_release_blockers` delegates the blocker set to
# `attention.release_blockers` (the function `aw attention` and `aw doctor` already consume), so the
# owner verb and the board can never disagree about what gates a release.
# ======================================================================================


class ReleaseRecord(NamedTuple):
    """One release record, read from its `.release.md` file.

    `summary` is the `- Summary:` bullet when present, else the first paragraph of a `## Summary`
    prose section (both shapes exist in the wild). `history` is the `## Workflow history` bullet
    lines, oldest-first as written. Fields are best-effort: a malformed record still yields a
    ReleaseRecord (with `None`/empty fields) so listing never hides a file - `aw check releases` is
    the validator that fails closed on it.
    """

    id6: Optional[str]
    version: Optional[str]
    status: Optional[str]
    summary: Optional[str]
    path: Path
    history: Tuple[str, ...] = ()


def _summary_section(text: str) -> Optional[str]:
    """The first nonempty paragraph under a `## Summary` heading, collapsed to one line."""
    m = re.search(r"(?m)^##[ \t]+Summary[ \t]*$", text)
    if m is None:
        return None
    rest = text[m.end() :]
    out: List[str] = []
    for line in rest.split("\n"):
        if line.startswith("#"):
            break
        if not line.strip():
            if out:
                break
            continue
        out.append(line.strip())
    joined = " ".join(out).strip()
    return joined or None


def _history_lines(text: str) -> Tuple[str, ...]:
    """The `- ` bullet lines under `## Workflow history` (in file order)."""
    m = re.search(r"(?m)^##[ \t]+Workflow history[ \t]*$", text)
    if m is None:
        return ()
    out: List[str] = []
    for line in text[m.end() :].split("\n"):
        if line.startswith("#"):
            break
        s = line.strip()
        if s.startswith("- "):
            out.append(s[2:].strip())
    return tuple(out)


def parse_release(path: Path, text: str) -> ReleaseRecord:
    """Parse one release record's text into a ReleaseRecord (pure; never raises on bad content)."""
    mid = _ID_RE.search(text)
    mver = _VERSION_RE.search(text)
    mst = _STATUS_RE.search(text)
    msum = _SUMMARY_RE.search(text)
    summary = msum.group(1).strip() if msum else None
    if not summary:
        summary = _summary_section(text)
    return ReleaseRecord(
        id6=mid.group(1) if mid else None,
        version=mver.group(1) if mver else None,
        status=mst.group(1) if mst else None,
        summary=summary or None,
        path=Path(path),
        history=_history_lines(text),
    )


def list_releases(repo_root: Path) -> List[ReleaseRecord]:
    """Every `.release.md` record under `.aw/records/releases/`, as ReleaseRecords sorted by path.

    Uses the SAME discovery glob as `resolve_release`/`_existing_ids` (`rglob("*.release.md")` under
    `_releases_dir`), so the listing and the resolver see exactly one set of files. Unreadable files
    are skipped (a listing must not blow up on an I/O error)."""
    d = _releases_dir(Path(repo_root))
    if not d.is_dir():
        return []
    out: List[ReleaseRecord] = []
    for p in sorted(d.rglob("*.release.md")):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        out.append(parse_release(p, text))
    return out


def get_release(repo_root: Path, selector: str) -> Optional[ReleaseRecord]:
    """Resolve one release by id6, exact version string, filename (or stem), or the `next` sentinel.

    The `next` sentinel and the id6 lookup are DELEGATED to `resolve_release` (the single resolver
    `Blocks-Release` values already go through), so `aw releases show next` and
    `Blocks-Release: next` can never point at different records. Version/filename matching is the
    only additional lookup this verb adds, and it is applied after the canonical resolver misses.
    Returns None when the selector resolves to nothing (incl. an ambiguous `next`)."""
    repo_root = Path(repo_root)
    selector = (selector or "").strip()
    if not selector:
        return None
    # 1. Canonical resolver first (handles `next` + id6).
    p = resolve_release(repo_root, selector)
    if p is not None:
        try:
            return parse_release(p, p.read_text(encoding="utf-8"))
        except OSError:
            return None
    # 2. Version string / filename / stem (the verb's own convenience selectors).
    records = list_releases(repo_root)
    for rec in records:
        if rec.version == selector:
            return rec
    for rec in records:
        name = rec.path.name
        if selector in (name, name[: -len(".release.md")]):
            return rec
    return None


def get_release_blockers(repo_root: Path, selector: str) -> List[Dict[str, Any]]:
    """The LIVE items gating the release named by `selector`, as plain dicts.

    REUSES `attention.scan` + `attention.release_blockers` verbatim: this function does NOT
    re-implement a `- Blocks-Release:` walk, because a second scan could drift from the answer
    `aw attention` and `aw doctor` give. It only (a) resolves `selector` to a release, and (b) keeps
    the blockers whose own `Blocks-Release` value points at THAT release (its id6, or `next` when the
    release is the single planned one). Returns [] when the release does not resolve.

    Each dict carries `id`, `path`, `tree`, `native_status`, `attention_class`, `priority`, and
    `blocks_release` (the raw declared value), which is what the human/JSON/agent views render."""
    repo_root = Path(repo_root)
    rec = get_release(repo_root, selector)
    if rec is None:
        return []
    from agent_workflows import attention as _attention

    items, _drift = _attention.scan(repo_root)
    blockers = _attention.release_blockers(items, repo_root)
    # `next` is a legitimate alias for THIS release only when this release is the single planned one.
    planned = resolve_release(repo_root, "next")
    next_is_this = planned is not None and Path(planned) == Path(rec.path)
    accepted = {rec.id6} if rec.id6 else set()
    if next_is_this:
        accepted.add("next")
    out: List[Dict[str, Any]] = []
    for it in blockers:
        declared = it.blocks_release
        if declared is None:
            # The Item reader does not populate `blocks_release` for every tree; fall back to the
            # file the shared scan already validated (same paths `release_blockers` probed).
            declared = _declared_blocks_release(repo_root, it.path)
        if declared is None or declared not in accepted:
            continue
        out.append(
            {
                "id": it.id,
                "path": it.path,
                "tree": it.tree,
                "native_status": it.native_status,
                "attention_class": it.attention_class,
                "priority": it.priority,
                "blocks_release": declared,
            }
        )
    return out


def _declared_blocks_release(repo_root: Path, rel_path: str) -> Optional[str]:
    """Read an item's own `- Blocks-Release:` value from disk, trying the same two bases
    `attention.release_blockers` probes (repo-relative, then `.aw/records/`-relative)."""
    for base in (
        Path(repo_root) / rel_path,
        Path(repo_root) / ".aw" / "records" / rel_path,
    ):
        try:
            if base.is_file():
                m = _ITEM_BLOCKS_RELEASE_RE.search(base.read_text(encoding="utf-8"))
                if m:
                    return m.group(1)
        except OSError:
            continue
    return None


_PRIORITY_LINE_RE = re.compile(r"(?m)^- Priority:[ \t]*[^\n]*$\n?")


def set_priority_line(text: str, value: Optional[str]) -> str:
    """Return `text` with the `- Priority:` metadata line set to `value`, or removed when `value` is
    '-' or None. Idempotent: replaces an existing line or inserts one after `- Status:` (falling back
    to after `- Id:`, or leaving unchanged). xprio Order 1b45el; mirrors `set_from_backlog_line`. The
    ENUM check (value in backlog.PRIORITIES) is enforced by `aw check`, not here (this is a pure
    idempotent line writer). Tolerates any value so an existing malformed line is still replaced."""
    text = _PRIORITY_LINE_RE.sub("", text)
    if value in (None, "-"):
        return text
    new_line = f"- Priority: {value}\n"
    for anchor in (r"(?m)^- Status:[^\n]*\n", r"(?m)^- Id:[^\n]*\n"):
        m = re.search(anchor, text)
        if m:
            i = m.end()
            return text[:i] + new_line + text[i:]
    return text


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
    ignored_dirs = _core.get_ignored_dirs(repo_root)
    drift: List[_core.Drift] = []
    for sub in ("backlog", "specs", "plans"):
        for base in (repo_root / ".aw" / "records" / sub, repo_root / ".agents" / sub):
            if not base.is_dir() or _core.is_ignored_path(
                base, repo_root, ignored_dirs
            ):
                continue
            for p in base.rglob("*.md"):
                if p.name in (
                    "README.md",
                    "INDEX.md",
                    "STATUS.md",
                ) or _core.is_ignored_path(p, repo_root, ignored_dirs):
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
    ignored_dirs = _core.get_ignored_dirs(repo_root)
    drift: List[_core.Drift] = []
    known = _backlog.existing_backlog_ids(repo_root)
    for sub in ("plans", "specs", "backlog"):
        for base in (repo_root / ".aw" / "records" / sub, repo_root / ".agents" / sub):
            if not base.is_dir() or _core.is_ignored_path(
                base, repo_root, ignored_dirs
            ):
                continue
            for p in base.rglob("*.md"):
                if p.name in (
                    "README.md",
                    "INDEX.md",
                    "STATUS.md",
                ) or _core.is_ignored_path(p, repo_root, ignored_dirs):
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


# ======================================================================================
# IPD w0ln4q E-02: the `aw releases` command runners (list / show / new).
#
# Output contract (matching every other owner verb): human-formatted output on a TTY, `--json` for the
# full structured JSON, `--agent` for aw.agent/v1 JSONL, exit 0 clean / 2 usage-or-cannot-run. All
# three go through `result_types.select_output` + `renderers.get_renderer`, so there is no verb-local
# formatter.
#
# There is NO `run_check` here BY DESIGN. `aw check releases` already validates release records
# (check_engine -> `validate_release`); a `releases check` subcommand would be a second entry point to
# the same validator and could drift from it.
# ======================================================================================


def _release_repo_root(args) -> Path:
    from agent_workflows.project_context import resolve_verb_repo_root

    return resolve_verb_repo_root(getattr(args, "dir", None))


def _record_dict(repo_root: Path, rec: ReleaseRecord) -> Dict[str, Any]:
    """A ReleaseRecord as a JSON-ready dict with a repo-relative path when possible."""
    try:
        rel = Path(rec.path).resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except (ValueError, OSError):
        rel = str(rec.path)
    return {
        "id": rec.id6,
        "version": rec.version,
        "status": rec.status,
        "summary": rec.summary,
        "path": rel,
        "history": list(rec.history),
    }


def run_list(args) -> int:
    """`aw releases list` (also the bare `aw releases`): every release record as a table.

    Human view is a fixed-width table (Id / Status / Version / Summary) via `term.format_table`;
    `--json`/`--agent` carry the same records plus the resolved `next` release. Exit 0 always (an
    empty tree is a legitimate clean answer, rendered as the shared empty-result guidance)."""
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import CommandResult, Evidence, select_output
    from agent_workflows.term import Term

    repo_root = _release_repo_root(args)
    ctx = select_output(args)
    records = list_releases(repo_root)
    planned = describe_planned_release(repo_root)
    data = {
        "repo_root": str(repo_root),
        "releases": [_record_dict(repo_root, r) for r in records],
        "count": len(records),
        "next": {"id": planned[0], "version": planned[1]} if planned else None,
    }
    summary = f"{len(records)} release record(s)"
    if planned:
        summary += f"; next = {planned[1]} ({planned[0]})"

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="releases list",
            status="clean",
            exit_code=0,
            summary=summary,
            evidence=[
                Evidence(
                    key="releases",
                    value={"count": len(records)},
                    status="clean",
                )
            ],
            data=data,
        )
        return get_renderer(ctx).emit(res, ctx)

    term = Term(color=False if getattr(args, "no_color", False) else None)
    if not records:
        from agent_workflows.result_types import NextAction

        term.empty_result(
            summary="no release records",
            next_action=NextAction(
                command='aw releases new --version <v> --summary "<why>" --apply',
                description="create the ship-gate anchor",
            ),
        )
        return 0
    rows = []
    for rec in records:
        rows.append(
            [
                rec.id6 or "??????",
                rec.status or "-",
                rec.version or "-",
                (rec.summary or "-")[:60],
            ]
        )
    sys.stdout.write(
        term.format_table(["ID", "STATUS", "VERSION", "SUMMARY"], rows) + "\n"
    )
    if planned:
        sys.stdout.write(f"\nnext -> {planned[1]} ({planned[0]})\n")
    return 0


def run_show(args) -> int:
    """`aw releases show [<selector>]`: one release record plus every LIVE item gating it.

    The selector defaults to `next` (OQ-01). The blocker list comes from `get_release_blockers`, i.e.
    from `attention.release_blockers`, so it is the SAME set the board shows. Exit 2 when the selector
    resolves to no release (a usage error, not an empty result)."""
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )
    from agent_workflows.term import Term

    repo_root = _release_repo_root(args)
    ctx = select_output(args)
    selector = (getattr(args, "selector", None) or "next").strip()
    rec = get_release(repo_root, selector)
    if rec is None:
        msg = (
            f"aw releases show: {selector!r} does not resolve to a release record "
            f"(try an id6, a version, a filename, or 'next')"
        )
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="releases show",
                status="cannot-run",
                exit_code=2,
                summary=msg,
                next_actions=[NextAction(command="aw releases list")],
                data={"repo_root": str(repo_root), "selector": selector},
                verified=False,
                complete=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write(msg + "\n")
        return 2

    blockers = get_release_blockers(repo_root, selector)
    record = _record_dict(repo_root, rec)
    data = {
        "repo_root": str(repo_root),
        "selector": selector,
        "release": record,
        "blockers": blockers,
        "blocker_count": len(blockers),
    }
    summary = (
        f"{rec.version or '?'} ({rec.id6 or '??????'}) {rec.status or '?'}; "
        f"{len(blockers)} release blocker(s)"
    )

    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="releases show",
            status="clean",
            exit_code=0,
            summary=summary,
            evidence=[
                Evidence(
                    key="release",
                    value={"id": rec.id6, "blockers": len(blockers)},
                    status="clean",
                )
            ],
            data=data,
        )
        return get_renderer(ctx).emit(res, ctx)

    term = Term(color=False if getattr(args, "no_color", False) else None)
    out: List[str] = []
    out.append(
        term.format_section(f"release {rec.version or '?'} ({rec.id6 or '??????'})")
    )
    out.append(f"  Status:  {rec.status or '-'}")
    out.append(f"  Version: {rec.version or '-'}")
    out.append(f"  Id:      {rec.id6 or '-'}")
    out.append(f"  Path:    {record['path']}")
    if rec.summary:
        out.append(f"  Summary: {rec.summary}")
    out.append("")
    out.append(term.format_section(f"release-blockers ({len(blockers)})"))
    if not blockers:
        out.append("  none outstanding")
    else:
        rows = [
            [
                b["id"] or "??????",
                b["tree"],
                b["native_status"],
                b["priority"] or "-",
                b["path"],
            ]
            for b in blockers
        ]
        out.append(
            term.format_table(["ID", "TREE", "STATUS", "PRIORITY", "PATH"], rows)
        )
    if rec.history:
        out.append("")
        out.append(term.format_section("workflow history"))
        for line in rec.history:
            out.append(f"  - {line}")
    sys.stdout.write("\n".join(out) + "\n")
    return 0


def run_new(args) -> int:
    """`aw releases new --version <v> --summary <s> [--status planned] [--apply]`.

    A thin CLI wrapper around `plan_release`/`create_release` (no second renderer). PREVIEW BY DEFAULT
    like every other `new` verb: without `--apply` it writes NOTHING and prints the exact bytes it
    would write. Exit 2 on a missing/invalid `--version`, `--summary`, or `--status`."""
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        Change,
        CommandResult,
        select_output,
    )

    repo_root = _release_repo_root(args)
    ctx = select_output(args)
    version = (getattr(args, "version", None) or "").strip()
    summary = (getattr(args, "summary", None) or "").strip()
    status = (getattr(args, "status", None) or "planned").strip()

    def _usage(msg: str) -> int:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="releases new",
                status="cannot-run",
                exit_code=2,
                summary=msg,
                data={"repo_root": str(repo_root)},
                verified=False,
                complete=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write(f"aw releases new: {msg}\n")
        return 2

    if not version:
        return _usage("--version is required")
    if not summary:
        return _usage("--summary is required")
    if status not in RELEASE_STATUSES:
        return _usage(
            f"--status must be one of {list(RELEASE_STATUSES)}, got {status!r}"
        )

    dest, body = plan_release(repo_root, version, summary, status=status)
    applied = bool(getattr(args, "apply", False))
    if applied:
        dest.parent.mkdir(parents=True, exist_ok=True)
        _core.atomic_write(dest, body)

    rec = parse_release(dest, body)
    data = {
        "repo_root": str(repo_root),
        "release": _record_dict(repo_root, rec),
        "applied": applied,
    }
    verb = "wrote" if applied else "would write"
    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command="releases new",
            status="clean" if applied else "preview",
            exit_code=0,
            summary=f"{verb} {dest}",
            changes=[
                Change(path=str(dest), kind="create", applied=applied),
            ],
            data=data,
            applied=applied,
        )
        return get_renderer(ctx).emit(res, ctx)

    if applied:
        sys.stdout.write(f"aw releases new: wrote {dest}\n")
    else:
        sys.stdout.write(f"--- would write {dest} ---\n{body}")
    return 0
