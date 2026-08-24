"""Unified check engine: compose the existing per-type validators into one Drift list per record
type. Pure (returns Drift, never prints). Consumed by the `aw check <type>` verb (awcmdsurf)."""

from __future__ import annotations

import importlib.util
import re as _re
from pathlib import Path
from typing import Dict, List

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
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
# The type->facet map is defined ONCE in the naming authority (IPD o6b8l3). check_names only checks
# clustered-facet types, so `comms` (no clustered check today) is intentionally omitted here.
_TYPE_FACET = {
    t: _naming.TYPE_FACET[t]
    for t in (
        "plans",
        "specs",
        "backlog",
        "prompts",
        "walkthroughs",
        "roadmaps",
        "releases",
    )
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
    """Reference integrity. DELEGATES to per-type ``check_drift`` (IPD 3cmnfc E-04): the dangling-
    citation detection for plans and research is delivered by ``plans_index.check_drift`` /
    ``research_index.check_drift`` (invoked via ``check_content``), both of which now consume the
    ONE unified dangling policy in ``artifact_refs`` (id6 handles + dead bare-filename via the
    resolver, OQ-01 option B; setid citations not checked). This stub returns [] to avoid
    double-counting and remains the documented SEAM for future per-type ref checks (e.g. the
    awrelease Blocks-Release dangling check folds in here)."""
    return []


_ID_LINE_RE = _re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_SET_LINE_RE = _re.compile(r"(?m)^- Set:\s*(.+?)\s*$")
_HHMM_RE = _re.compile(r"\A\d{4}\Z")
_HAS_DIGIT_RE = _re.compile(r"\d")


def _identity_slot_token(filename: str) -> "str | None":
    """Return the raw ``<id6>`` token in a filename's identity slot, or None.

    Uses the naming authority's clustered parse (single source, IPD o6b8l3). Excludes the legacy
    ``YYYYMMDD-HHMM-NN-<slug>`` shape, whose 4-digit HHMM coincidentally matches the ``<setid>``
    segment (mirrors ``plans_index.check_drift``): a real clustered set-id is kebab, never exactly
    4 digits. The returned token may still be a slug word (e.g. ``assess``); the caller applies the
    real-id6 discriminator once the global set of declared ids is known."""

    m = _naming.parse_clustered(filename)
    if not m or _HHMM_RE.match(m.group("set")):
        return None
    return m.group("id6")


def _is_real_id6(token: str, declared_ids: set) -> bool:
    """A slot token is a REAL id6 (not a slug's first word) iff it is declared as some file's
    frontmatter Id, OR it visibly mixes digits and letters (mirrors ``tmp/find_id6_dupes.py``'s
    oracle: slug words like ``assess``/``agents`` are all-letters, so this excludes them)."""

    return token in declared_ids or bool(_HAS_DIGIT_RE.search(token))


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
    """Cross-tree id6 AND setid uniqueness, PLUS the filename identity-slot invariant (D140).

    Runs ONCE over every SUPPORTED type (collisions are global, not per-type):

    * frontmatter ``- Id:`` id6: a valid id6 declared on two different resolved files
      (``check.id6-collision``);
    * setid: the same setid under two different types, or the same setid with two different
      non-None descriptives (``check.setid-collision``);
    * filename IDENTITY-SLOT id6 (DECISIONS.md D140): the ``<id6>`` in a file's
      ``YYYYMMDD-<setid>-NN-<id6>-<slug>`` filename slot is that file's UNIQUE IDENTITY. It is
      validated by the precise rule (so it flags a foreign id6 in the slot but never mass-flags
      conformant files): (a) if the file DECLARES a frontmatter ``- Id:``, its slot id6 MUST EQUAL
      that declared ``- Id:``; (b) if the file declares NO ``- Id:``, its slot id6 MUST NOT equal
      any OTHER file's declared ``- Id:`` NOR any other file's slot id6 (it must be the sole holder
      of that id6). A violation emits ``check.id6-identity-slot`` naming the offending path AND the
      file that actually owns that id6. Legacy ``YYYYMMDD-HHMM-NN-<slug>`` names (no id6 slot) are
      exempt - only a filename whose slot parses as a real id6 via the naming authority is checked.
    """
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    seen_ids: Dict[str, str] = {}
    # setid -> (type, descriptive-or-None, first-path)
    seen_sets: Dict[str, tuple] = {}

    # First gather, for every file, its declared frontmatter Id and its filename identity-slot id6,
    # so the identity-slot rule (below) can be evaluated with global knowledge of who OWNS each id6.
    # A file "record": (path-str, declared_id-or-None, slot_id6-or-None).
    records: List[tuple] = []
    for record_type in SUPPORTED:
        for p in _iter_type_files(
            repo_root, record_type
        ):  # already deduped by resolved path
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            m = _ID_LINE_RE.search(text)
            declared_id = m.group(1) if m else None
            slot_id6 = _identity_slot_token(p.name)
            records.append((str(p), declared_id, slot_id6))

            if declared_id:
                id6 = declared_id
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

    drift.extend(_check_identity_slots(records))
    return drift


def _check_identity_slots(records: List[tuple]) -> List[_core.Drift]:
    """Validate the filename identity-slot id6 invariant (D140) over pre-gathered file records.

    ``records`` is a list of ``(path_str, declared_id_or_None, slot_id6_or_None)``. Returns
    ``check.id6-identity-slot`` Drift for each file whose filename identity slot holds an id6 that
    is not that file's own unique identity. See ``check_collisions`` for the precise (a)/(b) rule.
    """
    drift: List[_core.Drift] = []
    # The set of all frontmatter-declared ids drives the real-id6 discriminator (a slot token that
    # is some file's declared Id is definitely a real id6; a slug word like "assess" is not).
    declared_ids = {declared_id for _p, declared_id, _s in records if declared_id}

    # Who OWNS each REAL id6? A file owns an id6 if it DECLARES it in frontmatter (declared_id), or -
    # for the sole-holder test - carries it as a REAL id6 in its own identity slot. Build both.
    declared_owner: Dict[str, str] = {}
    slot_holders: Dict[str, List[str]] = {}
    for path_str, declared_id, slot_id6 in records:
        if declared_id:
            # First declarer wins as the canonical owner (the id6-collision check above already
            # flags a second declarer); we only need one owner name for the message.
            declared_owner.setdefault(declared_id, path_str)
        if slot_id6 and _is_real_id6(slot_id6, declared_ids):
            slot_holders.setdefault(slot_id6, []).append(path_str)

    for path_str, declared_id, slot_id6 in records:
        if slot_id6 is None:
            continue  # legacy / no identity slot -> exempt
        if declared_id is not None:
            # Rule (a): the slot must equal the file's own declared identity. A file that DECLARES
            # an Id asserts a clustered identity, so its slot is compared unconditionally (the slot
            # token need not independently "look like" a real id6 - the declared Id proves intent).
            if slot_id6 != declared_id:
                owner = declared_owner.get(slot_id6)
                owner_str = (
                    f"; id6 {slot_id6} is owned by {owner}"
                    if owner and owner != path_str
                    else ""
                )
                drift.append(
                    _core.Drift(
                        path_str,
                        "check.id6-identity-slot",
                        f"filename identity-slot id6 {slot_id6} != this file's declared Id {declared_id}{owner_str}",
                    )
                )
        else:
            # Rule (b): no declared Id -> the slot id6 must be owned by NO ONE else (neither another
            # file's declared Id nor another file's slot). This is the p7dqwz reuse case. Guard with
            # the real-id6 discriminator so a legacy name whose slug's first word happens to match
            # [0-9a-z]{6} (e.g. "assess"/"agents") is NOT mass-flagged.
            if not _is_real_id6(slot_id6, declared_ids):
                continue
            owner = declared_owner.get(slot_id6)
            other_slot_holders = [
                h for h in slot_holders.get(slot_id6, []) if h != path_str
            ]
            if owner is not None and owner != path_str:
                drift.append(
                    _core.Drift(
                        path_str,
                        "check.id6-identity-slot",
                        f"filename identity-slot id6 {slot_id6} is another file's identity (declared by {owner}); this file declares no Id",
                    )
                )
            elif other_slot_holders:
                drift.append(
                    _core.Drift(
                        path_str,
                        "check.id6-identity-slot",
                        f"filename identity-slot id6 {slot_id6} is also in the identity slot of {other_slot_holders[0]}; this file declares no Id",
                    )
                )
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
