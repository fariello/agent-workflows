"""Unified check engine: compose the existing per-type validators into one Drift list per record
type. Pure (returns Drift, never prints). Consumed by the `aw check <type>` verb (awcmdsurf)."""

from __future__ import annotations

import importlib.util
import re as _re
from pathlib import Path
from typing import Dict, List

from agent_workflows import artifact_core as _core
from agent_workflows import engine as _engine
from agent_workflows import record_producers as _rp

# Which check kinds each type supports today. "names" = filename-grammar conformity;
# "content" = front-matter/status/contract; "refs" = reference integrity (via the index drift).
SUPPORTED: Dict[str, tuple] = {
    "plans": ("names", "content", "refs"),
    "specs": ("content",),
    "backlog": ("names", "content"),
    "research": ("names", "content", "refs"),
    "prompts": ("names",),
    "walkthroughs": ("names",),
    "roadmaps": ("names",),
    "releases": ("names", "content"),
}

_SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}
_TYPE_FACET = {
    "plans": "ipd",
    "specs": "spec",
    "backlog": "backlog",
    "prompts": "prompt",
    "walkthroughs": "walkthrough",
    "roadmaps": "roadmap",
    "releases": "release",
}


def _type_dirs(repo_root: Path, record_type: str) -> List[Path]:
    """Existing dirs to scan for a record type.

    `resolve_record_read_paths` only accepts the RecordClass values {plans, specs, research,
    prompts, comms, walkthroughs} and RAISES for `backlog`/`roadmaps`; those resolve directly.
    Also includes the literal `.aw/records/<type>` (+ legacy `.agents/<type>`) so a bare/unregistered
    repo resolves. De-duplicated by resolved path; unknown types yield [].
    """
    repo_root = Path(repo_root)
    out: List[Path] = []
    seen: set = set()

    def _add(p: Path) -> None:
        try:
            key = str(p.resolve())
        except OSError:
            return
        if key not in seen and p.is_dir():
            seen.add(key)
            out.append(p)

    if record_type == "backlog":
        for rel in (".aw/records/backlog", ".agents/backlog"):
            _add(repo_root / rel)
    elif record_type == "roadmaps":
        _add(repo_root / ".aw" / "records" / "roadmaps")
    else:
        try:
            for p in _rp.resolve_record_read_paths(
                record_type, target_repo=str(repo_root)
            ):
                _add(p)
        except Exception:
            pass
    # Literal fallback (bare repo, or types the resolver rejects).
    _add(repo_root / ".aw" / "records" / record_type)
    _add(repo_root / ".agents" / record_type)
    return out


def _iter_type_files(repo_root: Path, record_type: str):
    """Yield each non-index *.md path for the type, de-duplicated by resolved path."""
    seen: set = set()
    for d in _type_dirs(repo_root, record_type):
        for p in d.rglob("*.md"):
            if p.name in _SKIP_NAMES:
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            yield p


def _load_normalizer():
    """Load the shipped plan-name normalizer layout-agnostically (source checkout AND installed
    wheel), mirroring cli.py:2890. Returns the module or None if it cannot be located."""
    try:
        root = _engine.resolve_source_root(None)
    except SystemExit:
        return None
    script = root / "setup-repo" / "tools" / "normalize_plan_names.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("awcheck_npn", script)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_names(
    repo_root: Path, record_type: str, legacy: bool = False
) -> List[_core.Drift]:
    """Filename-grammar conformity for a type's files. Research is skipped (own grammar). If the
    normalizer cannot be located, returns [] (names simply not checked)."""
    facet = _TYPE_FACET.get(record_type)
    if facet is None:
        return []  # research + any type without a clustered facet
    npn = _load_normalizer()
    if npn is None:
        return []
    drift: List[_core.Drift] = []
    for p in _iter_type_files(repo_root, record_type):
        if npn.is_conformant(p.name, expected_type=facet):
            continue
        # legacy=True allows a name that FAILS is_conformant but is a RECOGNIZED legacy shape
        # (parse_name non-None) - e.g. hyphenated-date YYYY-MM-DD-<slug>.md. The classic
        # YYYYMMDD-HHMM-NN form is already is_conformant, so it never reaches here.
        if legacy and npn.parse_name(p.name) is not None:
            continue
        drift.append(
            _core.Drift(
                str(p),
                "check.name-nonconformant",
                f"filename does not match the {record_type} grammar",
            )
        )
    return drift


def check_content(
    repo_root: Path, record_type: str, legacy: bool = False
) -> List[_core.Drift]:
    """Front-matter/status/contract validation, delegated to the existing per-type validators."""
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    if record_type == "specs":
        from agent_workflows import specs as _specs

        # Discover files via _type_dirs (robust for a bare repo), validate each with validate_spec.
        for p in _iter_type_files(repo_root, "specs"):
            try:
                drift.extend(_specs.validate_spec(p, p.read_text(encoding="utf-8")))
            except OSError:
                continue
    elif record_type == "backlog":
        from agent_workflows import backlog as _backlog

        for p in _iter_type_files(repo_root, "backlog"):
            try:
                drift.extend(_backlog.validate_item(p, p.read_text(encoding="utf-8")))
            except OSError:
                continue
    elif record_type == "plans":
        from agent_workflows import plans_index as _pidx

        dirs = _type_dirs(repo_root, "plans")
        if dirs:
            drift.extend(_pidx.check_drift(repo_root, dirs[0]))
    elif record_type == "research":
        from agent_workflows import research_index as _ridx

        dirs = _type_dirs(repo_root, "research")
        if dirs:
            drift.extend(_ridx.check_drift(repo_root, dirs[0]))
    elif record_type == "releases":
        from agent_workflows import releases as _releases

        for p in _iter_type_files(repo_root, "releases"):
            try:
                drift.extend(
                    _releases.validate_release(p, p.read_text(encoding="utf-8"))
                )
            except OSError:
                continue
    # prompts / walkthroughs / roadmaps: no content validator today -> []
    return drift


def check_refs(repo_root: Path, record_type: str) -> List[_core.Drift]:
    """Reference integrity. For plans/research this is already delivered via check_content
    (their check_drift covers dangling citations), so this returns [] today to avoid
    double-counting. It is the documented SEAM for future per-type ref checks (e.g. the
    awrelease Blocks-Release dangling check folds in here)."""
    return []


_ID_LINE_RE = _re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_SET_LINE_RE = _re.compile(r"(?m)^- Set:\s*(.+?)\s*$")


def _parse_setid(text: str):
    """Return (setid, descriptive-or-None) from a `- Set: <terse> (<descriptive>)` line, or
    (None, None). The setid is the first whitespace token before any '('."""
    m = _SET_LINE_RE.search(text)
    if not m:
        return None, None
    raw = m.group(1).strip()
    if not raw:
        return None, None
    setid = raw.split("(")[0].strip().split()[0] if raw.split("(")[0].strip() else None
    desc = None
    if "(" in raw and ")" in raw:
        desc = raw[raw.index("(") + 1 : raw.rindex(")")].strip() or None
    return setid, desc


def check_collisions(repo_root: Path) -> List[_core.Drift]:
    """Cross-tree id6 AND setid uniqueness. Runs ONCE over every SUPPORTED type (collisions are
    global, not per-type). id6: a valid id6 appearing on two different resolved files.
    setid: the same setid under two different types, or the same setid with two different
    non-None descriptives."""
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    seen_ids: Dict[str, str] = {}
    # setid -> (type, descriptive-or-None, first-path)
    seen_sets: Dict[str, tuple] = {}
    for record_type in SUPPORTED:
        for p in _iter_type_files(
            repo_root, record_type
        ):  # already deduped by resolved path
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            m = _ID_LINE_RE.search(text)
            if m:
                id6 = m.group(1)
                if id6 in seen_ids:
                    drift.append(
                        _core.Drift(
                            str(p),
                            "check.id6-collision",
                            f"id6 {id6} also on {seen_ids[id6]}",
                        )
                    )
                else:
                    seen_ids[id6] = str(p)
            sid, desc = _parse_setid(text)
            if sid:
                if sid in seen_sets:
                    prev_type, prev_desc, prev_path = seen_sets[sid]
                    if prev_type != record_type:
                        drift.append(
                            _core.Drift(
                                str(p),
                                "check.setid-collision",
                                f"setid {sid} conflicts with {prev_path} (different type: {prev_type} vs {record_type})",
                            )
                        )
                    elif (
                        desc is not None and prev_desc is not None and desc != prev_desc
                    ):
                        drift.append(
                            _core.Drift(
                                str(p),
                                "check.setid-collision",
                                f"setid {sid} conflicts with {prev_path} (descriptive: {prev_desc!r} vs {desc!r})",
                            )
                        )
                else:
                    seen_sets[sid] = (record_type, desc, str(p))
    return drift


def check_type(
    repo_root: Path,
    record_type: str,
    names_only: bool = False,
    legacy: bool = False,
    _from_all: bool = False,
) -> List[_core.Drift]:
    """Compose the supported sub-checks for one type into a single Drift list."""
    kinds = SUPPORTED.get(record_type)
    if kinds is None:
        if _from_all:
            return []
        return [
            _core.Drift(
                record_type, "check.type-unsupported", "no checks for this type"
            )
        ]
    drift: List[_core.Drift] = []
    if names_only:
        if "names" in kinds:
            drift.extend(check_names(repo_root, record_type, legacy=legacy))
        return drift
    if "names" in kinds:
        drift.extend(check_names(repo_root, record_type, legacy=legacy))
    if "content" in kinds:
        drift.extend(check_content(repo_root, record_type, legacy=legacy))
    if "refs" in kinds:
        drift.extend(check_refs(repo_root, record_type))
    return drift


def check_types(
    repo_root: Path,
    types: List[str],
    names_only: bool = False,
    legacy: bool = False,
    collisions: bool = False,
) -> List[_core.Drift]:
    """Fan out check_type over the given types (or every SUPPORTED type for the ['all'] sentinel),
    concatenating Drift; unsupported types are skipped. The ['all'] sentinel implies
    collisions=True; the cross-tree collision scan is appended exactly ONCE (never per type)."""
    if types == ["all"]:
        target = list(SUPPORTED.keys())
        collisions = True
    else:
        target = types
    drift: List[_core.Drift] = []
    for t in target:
        drift.extend(
            check_type(
                repo_root, t, names_only=names_only, legacy=legacy, _from_all=True
            )
        )
    if collisions:
        drift.extend(check_collisions(repo_root))
        # awrelease Order 02: dangling Blocks-Release references are a cross-tree ref check, run once
        # alongside collisions in the full sweep.
        try:
            from agent_workflows import releases as _releases

            drift.extend(_releases.check_blocks_release(repo_root))
        except Exception:
            pass
    return drift
