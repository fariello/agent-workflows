"""The single reference matcher/rewriter + dangling-citation policy for every artifact type.

IPD 3cmnfc (unifyfileio Order 03): before this module the three engines (`plans_refs`,
`research_refs`, `artifact_rename`) each re-implemented citation matching with DIFFERENT coverage -
research rewrote the full old filename ONLY, orphaning bare-stem citations a plans/generic rename
would have fixed - and the dangling checkers recognized different citation forms per type. This
module is the ONE place that:

* builds the ``RefEdit`` set for a rename/regroup ``name_map`` (old -> new), covering every
  FILENAME-derived citation form uniformly for every type:
    - the full filename (exact string),
    - the whole stem (the filename minus its trailing ``.md``; this also matches a range shorthand
      ``<stem>..NN`` because the stem is a hyphen-boundaried token), and
    - the legacy ``YYYYMMDD-HHMM-NN`` prefix stem when the old name carries one (preserving the
      pre-unification plans behavior for legacy plan names);
* applies those edits deterministically (full-name before stem);
* provides ONE dangling-citation matcher policy consumed by the shared
  ``artifact_core.find_dangling_citations`` engine: the explicit id6 handles (``PLAN-<id6>`` /
  ``RSCH-<id6>``) uniformly, plus a dead bare-filename citation (a filename that PARSES under the
  Order 01 grammar but no longer resolves via the Order 02 resolver). Per OQ-01 (human-resolved,
  option B) a setid citation is NOT treated as dangling.

INVARIANT (stable by design, never violated here): a bare ``<id6>`` token and a bare ``<setid>``
token are NEVER matched or rewritten - the id6 is carried into the new filename and ``- Id:`` /
``- Set:`` frontmatter is preserved, so those citations survive a rename unchanged.

Module placement (orchestrator ``g6mbht`` binding principle): this matcher imports the Order 01
naming authority (`artifact_naming`) to know what a stem IS and the Order 02 resolver (`selectors`)
to answer "does this cited name still exist?", so it MUST live in its OWN module, never in
`artifact_core` (which may be imported BY others but imports none of them). The import direction
flows toward core.

The stem-match uses the EXACT hyphen-aware negative lookaround from the pre-unification plans engine
(`(?<![0-9A-Za-z-])<escaped-stem>(?![0-9A-Za-z-])`), NOT a plain ``\\b``, so an embedded stem inside a
longer hyphenated token is never matched and byte-for-byte parity is preserved.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming

# ----------------------------------------------------------------------------------------------
# Reference rewriting (E-02): full-name + whole-stem + legacy-prefix stem, map-driven, no id6/setid.
# ----------------------------------------------------------------------------------------------

FULL_NAME = "full-name"
BARE_STEM = "bare-stem"

_SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}

# The legacy old-style plan stem prefix: YYYYMMDD-HHMM-NN.
_LEGACY_PREFIX_RE = re.compile(r"\A(\d{8}-\d{4}-\d{2})-")


class RefEdit(NamedTuple):
    """A planned reference rewrite in one file.

    ``kind`` is ``full-name`` or ``bare-stem``; ``old``/``new`` are the exact strings to rewrite;
    ``hits`` is the occurrence count.
    """

    file: Path
    kind: str
    old: str
    new: str
    hits: int


def _whole_stem(name: str) -> str:
    """The filename minus its trailing ``.md`` (the whole stem; keeps any ``.<facet>`` segment so a
    ``...-slug.ipd`` citation is caught)."""

    return name[:-3] if name.endswith(".md") else name


def _legacy_prefix_stem(name: str):
    """The legacy ``YYYYMMDD-HHMM-NN`` prefix of ``name`` if it has one, else None."""

    m = _LEGACY_PREFIX_RE.match(name)
    return m.group(1) if m else None


def _boundaried(stem: str) -> "re.Pattern[str]":
    """The hyphen-aware negative-lookaround matcher for a literal stem (exact plans-engine regex)."""

    return re.compile(r"(?<![0-9A-Za-z-])" + re.escape(stem) + r"(?![0-9A-Za-z-])")


# A URL pinned to a commit (`.../blob/<sha>/<path>`, also `tree`/`raw`) names a file AS IT WAS at that
# commit, so it stays correct after any later rename and must never be rewritten: a rewrite would point
# the pinned commit at a name that did not exist in it. A Markdown link to one is masked WHOLE, label
# included, since the label describes the same pinned file. The masked span is excluded from both the
# planning count and the substitution, so a permalink is invisible to every rename.
_PINNED_PERMALINK_RE = re.compile(
    # A whole Markdown link whose target is pinned (its label describes the pinned file too), else
    # a bare pinned URL token.
    r"\[[^\]\n]*\]\([^)\s]*/(?:blob|tree|raw)/[0-9a-f]{7,40}/[^)\s]*\)"
    r"|\S*/(?:blob|tree|raw)/[0-9a-f]{7,40}/\S*"
)


_FENCE_RE = re.compile(r"^(\s*)(```|~~~)")


def _mask_fenced_code(text: str):
    """Return (masked_text, restore) where every fenced code block is replaced by an inert token."""

    saved: List[str] = []
    lines = text.splitlines(keepends=True)
    out_parts: List[str] = []
    in_fence = False
    fence_marker = ""
    current_block: List[str] = []

    for line in lines:
        if not in_fence:
            m = _FENCE_RE.match(line)
            if m:
                in_fence = True
                fence_marker = m.group(2)
                current_block = [line]
            else:
                out_parts.append(line)
        else:
            current_block.append(line)
            m = _FENCE_RE.match(line)
            if m and m.group(2) == fence_marker:
                in_fence = False
                fence_marker = ""
                idx = len(saved)
                saved.append("".join(current_block))
                out_parts.append(f"\x00AWFENCEDCODE{idx}\x00")
                current_block = []

    if in_fence and current_block:
        idx = len(saved)
        saved.append("".join(current_block))
        out_parts.append(f"\x00AWFENCEDCODE{idx}\x00")

    masked = "".join(out_parts)

    def _restore(s: str) -> str:
        return re.sub(r"\x00AWFENCEDCODE(\d+)\x00", lambda m: saved[int(m.group(1))], s)

    return masked, _restore


def _mask_permalinks(text: str):
    """Return (masked_text, restore) where every pinned permalink is replaced by an inert token."""

    saved: List[str] = []

    def _hide(m: "re.Match[str]") -> str:
        saved.append(m.group(0))
        return f"\x00AWPERMALINK{len(saved) - 1}\x00"

    masked = _PINNED_PERMALINK_RE.sub(_hide, text)

    def _restore(s: str) -> str:
        return re.sub(r"\x00AWPERMALINK(\d+)\x00", lambda m: saved[int(m.group(1))], s)

    return masked, _restore


def count_legacy_prefix_records(repo_root: Path, prefix: str) -> int:
    """Count files under .aw/records/** starting with prefix + '-'."""
    records_dir = repo_root / ".aw" / "records"
    if not records_dir.is_dir():
        records_dir = repo_root / ".agents"
        if not records_dir.is_dir():
            return 0
    target_prefix = prefix + "-"
    ignored_dirs = _core.get_ignored_dirs(repo_root)
    count = 0
    for p in records_dir.rglob("*"):
        if not p.is_file():
            continue
        if _core.is_ignored_path(p, repo_root, ignored_dirs):
            continue
        if p.name.startswith(target_prefix):
            count += 1
    return count


def plan_reference_rewrites_with_warnings(
    repo_root: Path,
    name_map: Dict[str, str],
    scan_roots=_core.REFERENCE_SCAN_ROOTS,
    suffixes: Tuple[str, ...] = _core._REFERENCE_TEXT_SUFFIXES,
) -> Tuple[List[RefEdit], List[str]]:
    """Plan reference rewrites and collect warnings for skipped shared legacy prefixes.

    Returns (edits, warnings).
    """
    whole_stem_map: Dict[str, str] = {}
    legacy_stem_map: Dict[str, str] = {}
    warnings: List[str] = []

    for old_name, new_name in name_map.items():
        if old_name == new_name:
            continue
        o_whole, n_whole = _whole_stem(old_name), _whole_stem(new_name)
        if o_whole != old_name and len(o_whole) >= 6 and o_whole != n_whole:
            whole_stem_map[o_whole] = n_whole
        o_leg = _legacy_prefix_stem(old_name)
        if o_leg is not None:
            rec_count = count_legacy_prefix_records(repo_root, o_leg)
            if rec_count > 1:
                warn_msg = (
                    f"--- WARNING: legacy prefix '{o_leg}' is shared by {rec_count} artifacts; "
                    f"short-handle citations of it were NOT rewritten ---"
                )
                if warn_msg not in warnings:
                    warnings.append(warn_msg)
            else:
                m = _naming.parse_clustered_prefix(new_name)
                if m:
                    # Map a short legacy handle to the new short handle <date>-<set>-<nn>.
                    legacy_stem_map[o_leg] = (
                        f"{m.group('date')}-{m.group('set')}-{m.group('nn')}"
                    )

    edits: List[RefEdit] = []
    for f in _core.iter_scan_files(repo_root, scan_roots, suffixes=suffixes):
        # NEVER rewrite a GENERATED manifest (INDEX.md/README.md/STATUS.md). Doing so is both
        # pointless and harmful: the caller REGENERATES the manifest from the renamed corpus
        # immediately after this rewrite, so the edit is overwritten anyway, and meanwhile the
        # manifest lands in the caller's `touched_paths`, which is its COMMIT path-set. That put a
        # generated (now gitignored) file into a commit, which is what idxuntrack `4r0qp1` E-05
        # exists to eliminate. `_SKIP_NAMES` is already the module's name for "not a citing
        # document"; it was applied when COLLECTING names but not when SCANNING them.
        if f.name in _SKIP_NAMES:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        text, _restore_fenced = _mask_fenced_code(text)
        text, _restore_permalinks = _mask_permalinks(text)
        # (a) full filename.
        for old_name, new_name in name_map.items():
            if old_name != new_name and old_name in text:
                edits.append(
                    RefEdit(f, FULL_NAME, old_name, new_name, text.count(old_name))
                )
        # (b) whole stem (covers range shorthand); (c) legacy prefix stem. Both map-driven,
        # hyphen-boundaried. Merge so a stem is emitted once per (stem->new) mapping.
        for stem_map in (whole_stem_map, legacy_stem_map):
            for old_stem, new_stem in stem_map.items():
                n = len(_boundaried(old_stem).findall(text))
                if n:
                    edits.append(RefEdit(f, BARE_STEM, old_stem, new_stem, n))
    return edits, warnings


def plan_reference_rewrites(
    repo_root: Path,
    name_map: Dict[str, str],
    scan_roots=_core.REFERENCE_SCAN_ROOTS,
    suffixes: Tuple[str, ...] = _core._REFERENCE_TEXT_SUFFIXES,
) -> List[RefEdit]:
    """Plan every FILENAME-derived citation rewrite for a ``name_map`` (old filename -> new filename).

    Emits, per changed entry: (a) the full-name rewrite; (b) the whole-stem rewrite (old name minus
    ``.md`` -> new name minus ``.md``), which also covers the range shorthand ``<stem>..NN``; and
    (c) the legacy ``YYYYMMDD-HHMM-NN`` prefix-stem rewrite when the old name has that prefix. Stem
    rewrites are map-driven and hyphen-boundaried, so an unrelated same-grammar stem or an embedded
    stem inside a longer token is never matched. A bare id6/setid is never emitted.
    """
    edits, _ = plan_reference_rewrites_with_warnings(
        repo_root, name_map, scan_roots=scan_roots, suffixes=suffixes
    )
    return edits


def apply_reference_rewrites(edits: List[RefEdit], *, prefix: str = ".aw-ref-") -> None:
    """Apply planned rewrites per file: full-name first (most specific), then hyphen-boundaried stem."""

    by_file: Dict[Path, List[RefEdit]] = {}
    for e in edits:
        by_file.setdefault(e.file, []).append(e)
    for f, file_edits in by_file.items():
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        text, restore_fenced = _mask_fenced_code(text)
        text, restore_permalinks = _mask_permalinks(text)
        for e in sorted(file_edits, key=lambda x: 0 if x.kind == FULL_NAME else 1):
            if e.kind == FULL_NAME:
                text = text.replace(e.old, e.new)
            else:
                text = _boundaried(e.old).sub(e.new, text)
        restored = restore_fenced(restore_permalinks(text))
        _core.atomic_write(f, restored, prefix=prefix)


def is_test_path(path: Path, repo_root: Path) -> bool:
    """True iff path lies under tests/."""
    try:
        rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    return rel == "tests" or rel.startswith("tests/")


def filter_test_edits_interactive(
    repo_root: Path,
    ref_edits: List[RefEdit],
    *,
    yes: bool = False,
) -> List[RefEdit]:
    """Partition ref_edits into tests/ and non-tests; if interactive and not yes, prompt before rewriting tests."""
    from agent_workflows.artifact_adopt import leak_gate_is_interactive

    test_edits = [e for e in ref_edits if is_test_path(e.file, repo_root)]
    if not test_edits:
        return ref_edits

    if yes or not leak_gate_is_interactive():
        return ref_edits

    other_edits = [e for e in ref_edits if not is_test_path(e.file, repo_root)]
    affected_files = sorted(
        {
            (
                e.file.resolve().relative_to(repo_root.resolve()).as_posix()
                if repo_root.resolve() in e.file.resolve().parents
                else e.file.as_posix()
            )
            for e in test_edits
        }
    )
    for f in affected_files:
        print(f"  {f}")
    try:
        ans = input("Rewrite citations in these test files? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = "n"

    if ans in ("", "y", "yes"):
        return ref_edits

    print("Dropped test file citation rewrites.")
    return other_edits


# ----------------------------------------------------------------------------------------------
# Dangling-citation matcher policy (E-03): id6 handles + dead bare-filename (via Order 02 resolver).
# ----------------------------------------------------------------------------------------------

# A bare artifact-filename token candidate (a conservative superset tested with the naming authority).
_FILENAME_TOKEN_RE = re.compile(r"\d{8}-[a-z0-9.\-]+\.md")


def make_cite_matcher(handle_prefix: str):
    """Return a ``cite_matcher(line) -> [id6, ...]`` recognizing the explicit ``<PREFIX>-<id6>``
    handle uniformly (e.g. ``PLAN-`` or ``RSCH-``). Bare-filename EXISTENCE danglers are handled
    separately by :func:`dead_filename_citations` (which needs the resolver), so this matcher stays
    a pure, resolver-free id-handle extractor usable by ``artifact_core.find_dangling_citations``.
    """

    pat = re.compile(r"\b" + re.escape(handle_prefix) + r"-([0-9a-z]{6})\b")

    def _matcher(line: str) -> List[str]:
        return pat.findall(line)

    return _matcher


def dead_filename_citations(
    repo_root: Path,
    record_type: str,
    *,
    exclude_root: Optional[Path] = None,
    scan_roots=_core.SCAN_ROOTS,
) -> List[_core.Dangler]:
    """Return every bare artifact-FILENAME citation whose target no longer resolves (OQ-01 option B).

    A token is a candidate only if it PARSES under the Order 01 naming authority (clustered, legacy,
    or dated-slug); it is DANGLING only if it does not name an existing file of ``record_type`` (a
    crisp per-file yes/no, low false-positive risk). setid citations are NOT checked (option C
    deferred). Files under ``exclude_root`` are skipped.

    Performance: the set of existing names+stems for the type is computed ONCE via the Order 02
    resolver's record dirs, then membership is a cheap lookup - never a per-token filesystem scan.
    """

    from agent_workflows import research_contract as _rc
    from agent_workflows import selectors as _sel

    # One pass: the set of every existing filename (and its stem) across ALL record types, so a
    # valid CROSS-TYPE citation (a name that exists in some other tree) is never flagged (D2).
    all_types = (
        "plans",
        "specs",
        "prompts",
        "backlog",
        "releases",
        "research",
        "walkthroughs",
        "roadmaps",
    )
    existing: set = set()
    for rt in all_types:
        for d in _sel.record_dirs(repo_root, rt):
            for p in d.rglob("*.md"):
                if p.name in _SKIP_NAMES:
                    continue
                existing.add(p.name)
                existing.add(p.name[:-3])  # stem form (citation may drop the .md)

    facet = _rp_type_facet(record_type)

    def _type_appropriate(tok: str) -> bool:
        """True iff ``tok`` is a citation-shaped name that BELONGS to ``record_type`` (so a
        cross-type name is never treated as a citation of this type - the spec-only-stem safeguard)."""

        if record_type == "research":
            parsed, _err = _rc.parse_name(tok)
            return parsed is not None
        # Generic clustered/legacy/dated types: the facet (if any) must match this type's facet;
        # a bare `.md` clustered name or a legacy/dated form is accepted for the plans/generic case.
        m = _naming.parse_clustered(tok)
        if m is not None:
            t = m.groupdict().get("type")
            return t is None or t == facet
        # legacy YYYYMMDD-HHMM-NN or dated-slug forms carry no facet -> only meaningful for plans.
        if record_type == "plans":
            return bool(
                _naming._LEGACY_TIMESTAMP_RE.match(tok)
                or _naming._DATED_SLUG_FACET_RE.match(tok)
            )
        return False

    danglers: List[_core.Dangler] = []
    for f in _core.iter_scan_files(repo_root, scan_roots):
        if exclude_root is not None:
            try:
                f.relative_to(exclude_root)
                continue
            except ValueError:
                pass
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            for tok in _FILENAME_TOKEN_RE.findall(line):
                if not _type_appropriate(tok):
                    continue  # not a citation of THIS type (cross-type/prose) -> never dangling here
                stem = tok[:-3] if tok.endswith(".md") else tok
                if tok not in existing and stem not in existing:
                    danglers.append(_core.Dangler(f, i, tok, line.strip()[:120]))
    return danglers


def _rp_type_facet(record_type: str):
    """The canonical ``.<facet>`` token for a record type (from the naming authority), or None."""

    return _naming.TYPE_FACET.get(record_type)
