"""Shared selector resolver: turn selector tokens (id6 | setid | filename fragment | status)
into concrete record file paths for a record type. Pure (no CLI, no writes). Consumed by
`aw show` and the cross-cutting verbs (awselect Order 02 + awcmdsurf)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from agent_workflows import artifact_core as _core
from agent_workflows import record_producers as _rp

_SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}

_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^- Status:\s*(\S+)\s*$")
_SET_RE = re.compile(r"(?m)^- Set:\s*(.+?)\s*$")


def record_dirs(repo_root: Path, record_type: str) -> List[Path]:
    """Directories to search for a record type (primary + any legacy read path).

    Combines the project-context resolver (`resolve_record_read_paths`, which honors a registered
    project/home backend) with the DIRECT literal layout under `repo_root` (`.aw/records/<type>` +
    legacy `.agents/<type>`), so this works for a bare/unregistered repo too. De-duplicated; only
    existing dirs. Returns [] for an unknown/unresolvable type rather than raising.
    """
    repo_root = Path(repo_root)
    out: List[Path] = []
    seen: set = set()

    def _add(p: Path) -> None:
        try:
            rp = p.resolve()
        except OSError:
            return
        key = str(rp)
        if key not in seen and p.is_dir():
            seen.add(key)
            out.append(p)

    try:
        for p in _rp.resolve_record_read_paths(record_type, target_repo=str(repo_root)):
            _add(p)
    except Exception:
        pass
    # Direct literal layout (covers a bare/unregistered repo, and backlog/roadmaps/releases which
    # the RecordClass resolver rejects).
    _add(repo_root / ".aw" / "records" / record_type)
    _add(repo_root / ".agents" / record_type)
    return out


def _read_id(text: str) -> str | None:
    m = _ID_RE.search(text)
    return m.group(1) if m else None


def _read_status(text: str) -> str | None:
    m = _STATUS_RE.search(text)
    return m.group(1) if m else None


def _read_setid(text: str) -> str | None:
    m = _SET_RE.search(text)
    if not m:
        return None
    # The set-id is the first whitespace token before any '(' (mirrors plans_index.set_terse_id).
    return m.group(1).split("(")[0].strip().split()[0] if m.group(1).strip() else None


def _iter_files(repo_root: Path, record_type: str):
    """Yield (path, text) for every non-index *.md record file of the type, de-duplicated by path."""
    seen: set = set()
    for d in record_dirs(repo_root, record_type):
        for p in d.rglob("*.md"):
            if p.name in _SKIP_NAMES:
                continue
            rp = str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            yield p, text


def resolve_one(repo_root: Path, record_type: str, token: str) -> List[Path]:
    """Resolve ONE token against one type's record dirs, via a fallback chain:
    id6 -> status -> setid -> filename-substring. The FIRST rule that yields any match wins.
    """
    files = list(_iter_files(repo_root, record_type))

    # Rule 1: exact id6.
    if _core.ID6_RE.match(token):
        hits = [p for p, text in files if _read_id(text) == token]
        if hits:
            return hits

    # Rule 2: status match.
    hits = [p for p, text in files if _read_status(text) == token]
    if hits:
        return hits

    # Rule 3: setid match.
    hits = [p for p, text in files if _read_setid(text) == token]
    if hits:
        return hits

    # Rule 4: filename fragment.
    hits = [p for p, _text in files if token in p.name]
    return hits


def resolve_selectors(
    repo_root: Path, record_type: str, tokens: List[str]
) -> List[Path]:
    """The public API: OR-union of resolve_one over every token, de-duplicated, sorted by path.
    An empty tokens list returns []."""
    seen: dict = {}
    for tok in tokens:
        for p in resolve_one(repo_root, record_type, tok):
            seen[str(p)] = p
    return [seen[k] for k in sorted(seen)]
