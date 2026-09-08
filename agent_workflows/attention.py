"""The read-only cross-tree attention view (Set attnview, Order 03).

`aw attention` scans the tracked `.agents/` trees on demand, validates each artifact against its tree
contract, maps each native status onto the five-value attention class, and renders the result to
STDOUT as a human board or versioned JSON. It writes NOTHING to disk and never touches git. `--check`
(and `--check --agent`) fail closed on any contract violation.

Stdlib-only, Python 3.9 (D46). Reuses `artifact_core` (scan, Drift, render, exit code) and consumes
the Order 01 contracts (`attention_contract`) and the Order 02 specs validator (`specs.validate_spec`).

Determinism (spec Section 8.5): full scan every run; repo-relative POSIX paths; sort by class order,
then normalized path, then id; UTF-8; LF; one final newline; fixed JSON key order/indent/separators;
no timestamps/mtime/locale; `last_history_at` parsed from history, never mtime.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import attention_contract as A
from agent_workflows import ipd_schema as _schema
from agent_workflows import plans as plans_mod
from agent_workflows import research_contract
from agent_workflows import specs as specs_mod
from agent_workflows import term as T

# 3: items gained readiness + oqs + rqs (2 was priority + blocks_release).
SCHEMA_VERSION = 3
MAPPING_VERSION = 1


class Item(NamedTuple):
    id: str
    path: str  # repo-relative POSIX
    tree: str
    native_status: str
    attention_class: str
    gate: Optional[Dict[str, str]]
    last_history_at: Optional[str]
    # awdoctorfix Order 01: surface priority + release-blocker on the board. Optional + trailing so
    # the existing positional Item(...) constructions keep working; readers set them where they apply.
    priority: Optional[str] = None
    blocks_release: Optional[str] = None
    detail_kind: Optional[str] = None
    detail_text: Optional[str] = None
    readiness: Optional[str] = None
    oqs: int = 0
    rqs: int = 0
    # worksequence i6015i E-07: the artifact's DECLARED `Item-Dependencies` edges, in canonical token
    # form, so `aw next -o depth` can sequence prerequisites before dependents.
    #
    # WHY THE FIELD LIVES HERE rather than being looked up when sorting: `scan()` already holds each
    # artifact's full text (it reads it once and then discards it), whereas a sort-time lookup would
    # have to call `check_engine.build_dependency_index`, which re-reads EVERY artifact through
    # `status_set.inventory_all_artifacts`. That second full-tree pass is exactly what the
    # single-authority rule forbids (see `releases.py`: "a second scan could drift from the answer
    # `aw attention` and `aw doctor` give"), and it would be INVISIBLE in the output, so no assertion
    # on what the command prints could catch it. Extracting the edges during the one existing pass
    # keeps the order a pure function of the same scan result the view itself renders.
    #
    # Appended LAST with a default, matching the pattern `priority`/`blocks_release` used, so every
    # existing positional `Item(...)` construction (including the ones in the test suite and in
    # `releases.get_release_blockers`' callers) keeps working unchanged. `None` means "no
    # Item-Dependencies field present"; an empty tuple means the field was present and declared no
    # edges (`none`), a distinction `-o depth` does not need but which costs nothing to preserve.
    item_dependencies: Optional[Tuple[str, ...]] = None
    exec_progress: Optional[Tuple[int, int]] = None
    valid_progress: Optional[Tuple[int, int]] = None


_OQ_SECTION_RE = re.compile(
    r"^##\s+(?:[0-9]+\.\s*)?(?:Open|Resolved)\s+questions\b", re.IGNORECASE
)
_OQ_HEADING_RE = re.compile(
    r"^###\s+((?:OQ|RQ)-[0-9]+|(?:OQ|RQ)-[A-Za-z0-9_-]+):?\s*(.*)$", re.IGNORECASE
)
_OQ_STATUS_RE = re.compile(r"^-[ \t]*Status:[ \t]*(\S+)", re.IGNORECASE)


def count_question_stats(text: str) -> Tuple[int, int]:
    """Count (unresolved_oqs, resolved_rqs) in an artifact's '## Open questions' section."""
    if not text or "questions" not in text.lower():
        return 0, 0
    in_section = False
    unresolved_count = 0
    resolved_count = 0
    in_question_block = False
    is_resolved = False
    explicit_status = False

    def _flush_question():
        nonlocal \
            unresolved_count, \
            resolved_count, \
            in_question_block, \
            is_resolved, \
            explicit_status
        if in_question_block:
            if is_resolved:
                resolved_count += 1
            else:
                unresolved_count += 1
        in_question_block = False
        is_resolved = False
        explicit_status = False

    for line in text.splitlines():
        if line.startswith("## "):
            _flush_question()
            in_section = bool(_OQ_SECTION_RE.match(line.strip()))
            continue
        if not in_section:
            continue
        if line.startswith("### "):
            _flush_question()
            m_h = _OQ_HEADING_RE.match(line.strip())
            if m_h:
                in_question_block = True
                prefix = m_h.group(1).upper()
                rest = m_h.group(2)
                if prefix.startswith("RQ-") or re.search(
                    r"\bRESOLVED\b", rest, re.IGNORECASE
                ):
                    is_resolved = True
                else:
                    is_resolved = False
                explicit_status = False
            continue
        if in_question_block:
            m_s = _OQ_STATUS_RE.match(line.strip())
            if m_s and not explicit_status:
                status_val = m_s.group(1).lower().strip("[]().,")
                explicit_status = True
                is_resolved = status_val == "resolved"
            elif not explicit_status:
                if re.search(r"^-[ \t]*Blocking:.*\(resolved\)", line, re.IGNORECASE):
                    is_resolved = True
                elif re.search(
                    r"^-[ \t]*Resolution(?:\s+or\s+deferral\s+rationale)?:\s*RESOLVED\b",
                    line,
                    re.IGNORECASE,
                ):
                    is_resolved = True

    _flush_question()
    return unresolved_count, resolved_count


def read_readiness(text: str) -> Optional[str]:
    """The artifact's `- Readiness:` value normalized to the closed enum, or None.

    DELEGATES to `ipd_schema.read_readiness` rather than re-scanning, because that is the READ-path
    authority for this field and the enum (`go`/`go-pending-approval`/`no-go`) belongs to it. The
    four call sites here previously each ran their own `(\\S+)` scan, which stopped at the first
    space and so folded the workflow's documented multi-word spellings (`GO - PENDING HUMAN
    APPROVAL`, `go (pending human approval)`) down to a bare `go`. That is the one direction this
    field must never fail in: it renders and FILTERS as a clean `go` while the source says the plan
    still needs human approval. The schema reader returns None for anything out-of-vocabulary
    instead, which is the fail-closed answer the rest of the toolkit already relies on.

    Absent and unrecognized are deliberately the same answer (None), matching the schema reader; the
    board shows both as `-`. Pure.
    """
    return _schema.read_readiness(text)


def count_unresolved_open_questions(text: str) -> int:
    """Count open/unresolved questions in an artifact's '## Open questions' section."""
    oqs, _ = count_question_stats(text)
    return oqs


_E_LEAF_RE = re.compile(r"^-\s*\[([ xX])\]\s*E-[0-9]{2,}\b", re.MULTILINE)
_V_LEAF_RE = re.compile(r"^-\s*\[([ xX])\]\s*V-[0-9]{2,}\b", re.MULTILINE)


def _extract_checklist_progress(
    text: str,
) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
    """Extract (exec_progress, valid_progress) as ((checked, total), (checked, total)) for a plan.

    Returns (None, None) if no E or V items are present respectively.
    """
    if not text or ("E-" not in text and "V-" not in text):
        return None, None
    e_matches = _E_LEAF_RE.findall(text)
    v_matches = _V_LEAF_RE.findall(text)

    exec_prog = (
        (sum(1 for m in e_matches if m in ("x", "X")), len(e_matches))
        if e_matches
        else None
    )
    valid_prog = (
        (sum(1 for m in v_matches if m in ("x", "X")), len(v_matches))
        if v_matches
        else None
    )
    return exec_prog, valid_prog


def count_resolved_questions(text: str) -> int:
    """Count resolved questions in an artifact's '## Open questions' section."""
    _, rqs = count_question_stats(text)
    return rqs


_FIELD_PATTERNS = (
    ("summary", re.compile(r"(?mi)^-\s*Summary:\s*(.+)$")),
    ("scope", re.compile(r"(?mi)^-\s*Scope:\s*(.+)$")),
    ("concern", re.compile(r"(?mi)^-\s*Concern:\s*(.+)$")),
    ("question", re.compile(r"(?mi)^-\s*Question:\s*(.+)$")),
    ("title", re.compile(r"(?mi)^-\s*Title:\s*(.+)$")),
)
_H1_RX = re.compile(r"(?m)^#\s+(?:[A-Za-z0-9_-]+:\s*)?(.+)$")


def _extract_detail(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract (detail_kind, detail_text) using the fallback cascade:
    Summary -> Scope -> Concern -> Question -> Title -> H1 header.
    """
    for tag, rx in _FIELD_PATTERNS:
        m = rx.search(text)
        if m:
            val = m.group(1).strip()
            if val:
                return tag, val
    m = _H1_RX.search(text)
    if m:
        val = m.group(1).strip()
        if val:
            return "title", val
    return None, None


def _rel_posix(repo_root: Path, p: Path) -> str:
    return p.resolve().relative_to(repo_root.resolve()).as_posix()


def _classify_tree(rel_posix: str) -> Optional[A.TreePolicy]:
    """Return the TreePolicy whose root is a path-prefix of the file, or None (unclassified)."""

    norm_rel = rel_posix
    if norm_rel.startswith(".aw/records/"):
        tail = norm_rel[len(".aw/records/") :]
        # Order 07 flattened the doc-family types out of docs/ in the .aw/ layout, but the
        # TreePolicy keys (and legacy .agents/) keep the docs/ grouping. Re-insert docs/ for those
        # types so the flat .aw/records/<type> classifies under the same policy as .agents/docs/<type>.
        _DOCS_FAMILY = (
            "specs",
            "research",
            "walkthroughs",
            "roadmaps",
            "prompt-library",
        )
        first = tail.split("/", 1)[0]
        if first in _DOCS_FAMILY:
            # prompt-library maps to the legacy docs/prompts policy key (renamed in Order 07).
            legacy_type = "prompts" if first == "prompt-library" else first
            tail = "docs/" + legacy_type + tail[len(first) :]
        norm_rel = ".agents/" + tail

    best: Optional[A.TreePolicy] = None
    for pol in A.TREE_POLICY:
        root = pol.root.replace("\\", "/")
        if norm_rel == root or norm_rel.startswith(root + "/"):
            # choose the longest matching root (specs under docs, etc.)
            if best is None or len(pol.root) > len(best.root):
                best = pol
    return best


def _history_section_lines(text: str) -> List[str]:
    out: List[str] = []
    in_hist = False
    for line in text.split("\n"):
        if line.strip() == "## Workflow history":
            in_hist = True
            continue
        if in_hist:
            if line.startswith("## "):
                break
            out.append(line)
    return out


# worksequence i6015i E-07: the `- Item-Dependencies:` front-matter bullet. Only the bullet is matched
# here; the VALUE grammar is parsed by `ipd_schema.parse_item_dependencies`, the shipped authority for
# this field, rather than by a second regex that would drift from it.
_ITEM_DEPS_RE = re.compile(r"(?m)^-[ \t]*Item-Dependencies:[ \t]*(.+?)[ \t]*$")


def _extract_item_dependencies(text: str) -> Optional[Tuple[str, ...]]:
    """The artifact's declared `Item-Dependencies` edges in canonical token form, or None.

    Returns None when the field is ABSENT, and a (possibly empty) tuple when it is present. Reuses
    `ipd_schema.parse_item_dependencies` so the edge grammar, the `none`/`unresolved` sentinels, the
    accepted target types (`ipd`/`spec`/`backlog`) and the canonical token spelling all come from the
    one owning module. A malformed value yields an empty tuple rather than raising: this is a pure
    READ on a display/ordering path, and the fail-closed contract violation for a bad edge already
    belongs to `aw check`, which must stay the single authority for that finding. Pure.
    """
    m = _ITEM_DEPS_RE.search(text)
    if m is None:
        return None
    edges, _ready, err = _schema.parse_item_dependencies(m.group(1))
    if err:
        return ()
    return tuple(e.canonical() for e in edges)


def _plans_id(text: str) -> Optional[str]:
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("- Id:"):
            return s[len("- Id:") :].strip()
    return None


def scan(repo_root: Path) -> Tuple[List[Item], List[core.Drift]]:
    """Full deterministic scan of the tracked trees. Returns (items, violations). Pure read."""

    items: List[Item] = []
    drift: List[core.Drift] = []
    seen_ids: Dict[str, str] = {}
    seen_paths: set = set()

    for f in core.iter_scan_files(repo_root):
        rel = _rel_posix(repo_root, f)
        # only artifacts under an inventoried tree matter; the four root docs + READMEs are not artifacts
        pol = _classify_tree(rel)
        if pol is None:
            # a file under no inventoried tree, but only flag it if it is under .agents/ (not a root doc)
            if (
                rel.startswith(".agents/")
                and not rel.endswith("/README.md")
                and Path(rel).name != "README.md"
            ):
                drift.append(
                    core.Drift(
                        rel,
                        "attention.unclassified-tree",
                        "file under no inventoried tree",
                    )
                )
            continue
        if not pol.tracked:
            continue
        if A.is_nonartifact_name(Path(rel).name):
            continue

        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            drift.append(core.Drift(rel, "attention.unreadable", "cannot read/decode"))
            continue

        if rel in seen_paths:
            drift.append(
                core.Drift(rel, "attention.duplicate-path", "duplicate normalized path")
            )
            continue
        seen_paths.add(rel)

        rec, rec_drift = _record_for(pol.name, rel, f, text)
        drift.extend(rec_drift)
        if rec is None:
            continue

        # worksequence i6015i E-07: extract the declared dependency edges HERE, while `text` is still
        # in hand, so `-o depth` needs no second artifact-reading pass. Applied uniformly to every
        # tracked type rather than inside the five per-tree `_*_record` builders: the field's grammar is
        # type-agnostic (`ipd_schema.ITEM_DEP_TYPES` accepts `ipd`/`spec`/`backlog` TARGETS) and one
        # call site cannot drift from four others.
        deps = _extract_item_dependencies(text)
        if deps is not None:
            rec = rec._replace(item_dependencies=deps)

        if rec.id:
            if rec.id in seen_ids:
                drift.append(
                    core.Drift(
                        rel,
                        "attention.duplicate-id",
                        A.escape_detail(f"id {rec.id} also on {seen_ids[rec.id]}"),
                    )
                )
            else:
                seen_ids[rec.id] = rel
        items.append(rec)

    # setupmarker Order 01: the operational-action ledger was DELETED (it was redundant with backlog
    # and its eager mkdir made this read path stamp `.aw/state/` into every scanned repo - write-on-
    # read). "Setup pending" is now DERIVED read-only from the `.aw/setup-repo-needed.md` marker
    # (see `setup_needed`), not scanned as an action tree here.

    # IPD h40usm E-02: reclassify STALE research so finished-but-unpromoted `todo` no longer
    # masquerades as `ready`. The RUN/cited-by-executed signal is manifest-level + cross-tree, so it
    # cannot live in the status-only, pure/total `class_of`; instead we apply it here as a post-scan
    # pass keyed by research id6 (the lower-drift option per the IPD WIRING note + OQ-01). A RUN or
    # cited-by-executed `todo` doc is reclassed READY -> PARKED (dropped from the default actionable
    # board; child 01's `aw check`/`aw research index --check` owns the fail-closed stale-state drift,
    # so attention does NOT re-emit it). `active` is a genuine live state and is NOT touched; a
    # genuinely-unrun `todo` prompt stays READY (actionable). No new attention class is introduced.
    # (rstodo p3o9je: the hot state was renamed `intake` -> `todo`; native_status is normalized to the
    # canonical `todo` at the scanner, so a legacy `intake` doc is handled identically here.)
    items = _reclassify_stale_research(repo_root, items)

    # worksequence i6015i E-04: the default order is unchanged. `sort_items` with the default key
    # reproduces exactly the `(class order, path, id)` tuple this line always used, which is what makes
    # `aw next` byte-identical to the pre-rename `aw attention`.
    items = sort_items(items)
    drift.sort(key=lambda d: (d.location, d.rule))
    return items, drift


# --------------------------------------------------------------------------------------
# Ordering (worksequence i6015i, E-04 .. E-08)
# --------------------------------------------------------------------------------------

# The filename grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>`, from which `-o set` and `-o order` read.
# MEASURED at execution time on this tree: 602 of 758 items (79%) match it; 156 do not, concentrated in
# plans (97), research (25), specs (19) and backlog (15), largely grandfathered pre-cutover names. So
# `set` and `order` are legitimately PARTIAL keys, and a non-matching name sorts as absent (E-05)
# instead of raising.
_NAME_GRAMMAR_RE = re.compile(
    r"^\d{8}-(?P<setid>[A-Za-z0-9]+)-(?P<order>\d{2})-[0-9a-z]{6}-"
)

# `-o priority` ranks high > medium > low. DERIVED from the one shared vocabulary
# (`attention_contract.PRIORITY_ORDER`, itself aligned with `backlog.PRIORITIES` and
# `check_engine._PRIORITY_RANK`) rather than a second hardcoded rank table, which is the mistake
# `ipd_schema` recorded when a duplicated status copy desynced.
_PRIORITY_SORT_RANK = {name: i for i, name in enumerate(A.PRIORITY_ORDER)}
_READINESS_SORT_RANK = {
    name: i
    for i, name in enumerate(
        getattr(A, "READINESS_ORDER", ("go", "go-pending-approval", "no-go"))
    )
}

# The sentinel for "this item has no value for the selected key". Sorting is done on a
# `(absent_flag, value, default_tail...)` tuple, where `absent_flag` is 1 for a missing value, so
# absent items land LAST under EVERY key without their value ever being compared (which also avoids
# comparing None with str on Python 3).
_ABSENT = 1
_PRESENT = 0


def _name_grammar_fields(path: str) -> Tuple[Optional[str], Optional[int]]:
    """(set_id, order) parsed from an artifact's FILENAME, or (None, None) when it does not match."""
    m = _NAME_GRAMMAR_RE.match(path.rsplit("/", 1)[-1])
    if m is None:
        return None, None
    try:
        return m.group("setid"), int(m.group("order"))
    except ValueError:  # pragma: no cover - the regex already pins two digits
        return m.group("setid"), None


def dependency_depths(items: Sequence[Item]) -> Tuple[Dict[str, int], List[List[str]]]:
    """Longest declared prerequisite chain ending at each item, plus any cycles found.

    Returns ``(depth_by_id6, cycles)``. Depth 0 means the item declares no prerequisite that is
    itself present in the view, so roots sort first and a dependent always follows what it depends
    on: the ordering the work must actually be done in (spec 25kzda 5.4 rule 4, and the same
    direction `oc_runipd.queue_sort_key` puts `dependency_depth` first in).

    Type-agnostic BY CONSTRUCTION: the edges carry their own target type, and this view holds plans,
    specs, backlog items, research and releases together keyed by id6, so a plan declaring a
    `backlog` target orders against that backlog item without any per-type special case. It differs
    from the runner's `dependency_depth` in exactly one way, deliberately: the runner restricts edges
    to QUEUE MEMBERS (`edge.id6 not in by_id` is skipped) because its queue is homogeneous IPDs,
    whereas here every tracked artifact is in scope.

    Cycle-safe and non-recursive-on-the-caller's-behalf: a node already on the current path
    contributes 0 rather than recursing forever, so a hand-edited cyclic edge set cannot hang the
    view. Cycles are DETECTED and returned so the caller can REPORT them (E-08) instead of silently
    reordering around a real defect that `aw check` has its own rule for. Pure.
    """
    # Only edges whose target is IN THE VIEW can order the view; an edge to an artifact outside it
    # (or a typo'd id6) is a leaf and contributes no ordering, exactly as an out-of-queue edge does
    # for the runner.
    present: Dict[str, Item] = {it.id: it for it in items if it.id}
    edges_by_id: Dict[str, List[str]] = {}
    for it in items:
        if not it.id:
            continue
        targets: List[str] = []
        for token in it.item_dependencies or ():
            edge, err = _schema._parse_item_dependency_edge(token)
            if err or edge is None:
                continue
            if edge.id6 in present and edge.id6 != it.id:
                targets.append(edge.id6)
        edges_by_id[it.id] = sorted(set(targets))

    # Cycle detection is DELEGATED to the shipped pure helper rather than re-implemented here.
    cycles = _schema.item_dependency_cycles(edges_by_id)
    in_cycle = {node for cyc in cycles for node in cyc}

    depths: Dict[str, int] = {}

    def _depth(node: str, on_path: frozenset) -> int:
        if node in on_path:
            return 0
        cached = depths.get(node)
        if cached is not None:
            return cached
        best = 0
        for target in edges_by_id.get(node, ()):
            best = max(best, 1 + _depth(target, on_path | {node}))
        # Only memoize a value computed off the recursion path, so a cycle cannot poison the cache
        # for nodes reached through it.
        if not (on_path & in_cycle) and node not in in_cycle:
            depths[node] = best
        return best

    out: Dict[str, int] = {}
    for node in sorted(edges_by_id):
        out[node] = _depth(node, frozenset())
    return out, cycles


def _order_key(
    it: Item,
    order_by: str,
    depths: Optional[Dict[str, int]],
    repo_root: Optional[Path] = None,
) -> Tuple:
    """The PRIMARY sort component for one item under ``order_by``.

    Every branch returns ``(absent_flag, value)`` where ``absent_flag`` is `_ABSENT` for an item that
    carries no value for this key, which is what places it LAST (maintainer ruling: absent is never
    hidden and never defaulted, matching the `xprio` ruling that an absent Priority renders as
    UNPRIORITIZED rather than being defaulted to `medium`). Values are made directly comparable
    (ints/strs, never None), so no branch can raise a TypeError on a mixed comparison.
    """
    if order_by == "priority":
        rank = _PRIORITY_SORT_RANK.get((it.priority or "").lower())
        # PRIORITY_ORDER is high-first, so its index is already the descending position.
        return (_PRESENT, rank) if rank is not None else (_ABSENT, 0)
    if order_by == "date":
        # Newest first: ISO dates sort lexicographically, so reverse the string order by negating
        # via a descending comparison on the inverted key. Using the raw string with a reversed
        # comparator would flip the whole tuple, so invert only this component.
        return (
            (_PRESENT, _invert_str(it.last_history_at))
            if it.last_history_at
            else (_ABSENT, "")
        )
    if order_by in ("set", "setid"):
        set_id, _order = _name_grammar_fields(it.path)
        return (_PRESENT, set_id) if set_id else (_ABSENT, "")
    if order_by == "order":
        _set_id, order = _name_grammar_fields(it.path)
        return (_PRESENT, order) if order is not None else (_ABSENT, 0)
    if order_by == "blocking":
        # Release blockers first, then everything else. `blocks_release` is the DECLARED gate field.
        return (_PRESENT, it.blocks_release) if it.blocks_release else (_ABSENT, "")
    if order_by == "depth":
        if depths is None:
            return (_ABSENT, 0)
        return (_PRESENT, depths.get(it.id, 0)) if it.id else (_ABSENT, 0)
    if order_by == "id6":
        return (_PRESENT, it.id) if it.id else (_ABSENT, "")
    if order_by == "path":
        return (_PRESENT, it.path) if it.path else (_ABSENT, "")
    if order_by == "file":
        return (_PRESENT, Path(it.path).name) if it.path else (_ABSENT, "")
    if order_by == "status":
        return (_PRESENT, it.native_status) if it.native_status else (_ABSENT, "")
    if order_by in ("tree", "type"):
        return (_PRESENT, it.tree) if it.tree else (_ABSENT, "")
    if order_by == "readiness":
        rank = _READINESS_SORT_RANK.get((it.readiness or "").lower())
        return (
            (_PRESENT, rank)
            if rank is not None
            else (_ABSENT, len(_READINESS_SORT_RANK))
        )
    if order_by == "oqs":
        oqs = getattr(it, "oqs", 0) or 0
        return (_PRESENT, -oqs) if oqs > 0 else (_ABSENT, 0)
    if order_by == "rqs":
        rqs = getattr(it, "rqs", 0) or 0
        return (_PRESENT, -rqs) if rqs > 0 else (_ABSENT, 0)
    if order_by in ("ctime", "mtime"):
        if repo_root is None:
            try:
                from agent_workflows.project_context import (
                    is_project_dir,
                    resolve_verb_repo_root,
                )

                cand = resolve_verb_repo_root(None)
                if is_project_dir(cand):
                    repo_root = cand
            except Exception:
                pass
        f = (repo_root / it.path) if repo_root else Path(it.path)
        try:
            st = f.stat()
            ts = st.st_ctime if order_by == "ctime" else st.st_mtime
            return (_PRESENT, -ts)
        except OSError:
            return (_ABSENT, 0.0)
    # `class` (the default) adds no primary component; the default tail alone decides.
    return ()


def _invert_str(value: str) -> Tuple[int, ...]:
    """Map a string to a key that sorts in DESCENDING order under an ascending sort.

    Used by `-o date` so the newest `last_history_at` comes first WITHOUT reversing the whole sort
    tuple (which would also reverse the default `(class, path, id)` tail and so break determinism
    expectations). Negating each code point is exact and locale-free, honoring this module's stated
    determinism contract (no locale, no timestamps).
    """
    return tuple(-ord(ch) for ch in value)


def sort_items(
    items: Sequence[Item],
    order_by: str = A.ORDER_CLASS,
    repo_root: Optional[Path] = None,
) -> List[Item]:
    """Return ``items`` ordered by ``order_by``. Never filters: the result is a PERMUTATION.

    The DEFAULT (`class`) reproduces the historical `(class order, path, id)` tuple exactly, byte for
    byte, because that order is a pinned contract (`xprio`) and not merely a default. Every other key
    prepends its own component and then FALLS THROUGH to that same tail, so every order is TOTAL and
    stable across runs, with no timestamps, mtime or locale involved.

    `-o depth` needs the whole item set to compute a graph, so the depths are computed ONCE here
    rather than per comparison. Cycles are reported through `sort_items_with_notices`; this function
    keeps the plain signature for callers that only want the order.
    """
    ordered, _notices = sort_items_with_notices(items, order_by, repo_root=repo_root)
    return ordered


def sort_items_with_notices(
    items: Sequence[Item],
    order_by: str = A.ORDER_CLASS,
    repo_root: Optional[Path] = None,
) -> Tuple[List[Item], List[str]]:
    """`sort_items` plus any human-facing notices the ordering produced (E-08).

    A notice is currently emitted only for a dependency CYCLE under `-o depth`. A cycle degrades to
    the default order for the affected nodes and is REPORTED rather than silently absorbed, because a
    view that quietly reorders around a cycle hides a defect `aw check` has a rule for. Notices are
    advisory and never change the exit code, which stays owned by the drift set.
    """
    keys = [k.strip() for k in order_by.split(",") if k.strip()]
    if not keys:
        keys = [A.ORDER_CLASS]

    for k in keys:
        if k not in A.ORDER_KEYS:
            # An out-of-vocabulary key cannot reach here through the CLI (argparse `choices` refuses it),
            # so this is a programming error rather than user input; fail loudly instead of silently
            # falling back to an order the caller did not ask for.
            raise ValueError(
                "unknown order key {0!r}; valid keys: {1}".format(
                    k, ", ".join(A.ORDER_KEYS)
                )
            )

    notices: List[str] = []
    depths: Optional[Dict[str, int]] = None
    if "depth" in keys:
        depths, cycles = dependency_depths(items)
        for cyc in cycles:
            notices.append(
                "dependency cycle: "
                + " -> ".join(cyc)
                + " (those items keep the default order; run `aw check plans` for the fail-closed finding)"
            )

    def key(it: Item) -> Tuple:
        return (
            tuple(_order_key(it, k, depths, repo_root) for k in keys),
            A.ATTENTION_CLASS_ORDER.index(it.attention_class),
            it.path,
            it.id,
        )

    return sorted(items, key=key), notices


def _reclassify_stale_research(repo_root: Path, items: List[Item]) -> List[Item]:
    """Return ``items`` with STALE research ``todo`` rows moved from READY to PARKED.

    A research ``todo`` doc is stale when its SET is a RUN prompt-set OR it is cited by an executed
    artifact (child 01's derivations). Such a doc is finished-but-unpromoted, not actionable, so it is
    reclassed to PARKED (hidden from the default board). A genuinely-unrun ``todo`` prompt keeps its
    READY class. Only ``todo`` is considered; ``active`` (a live state -> ACTIVE) is left untouched.
    Failure-isolated: any error in deriving the signal leaves the items unchanged (never breaks the
    view). ``class_of`` is not involved and stays status-only/total. (rstodo p3o9je: native_status is
    already normalized to canonical ``todo`` at the scanner, so a legacy ``intake`` doc is included.)
    """

    research_todo = [
        it for it in items if it.tree == "research" and it.native_status == "todo"
    ]
    if not research_todo:
        return items
    try:
        from agent_workflows import research_index as _ridx

        research_root = research_contract.resolve_research_root(repo_root)
        entries, _drift = _ridx._scan_docs(research_root)
        run_sets = _ridx.run_prompt_set_ids(entries)
        cited_exec = _ridx.cited_by_executed_ids(repo_root, research_root)
        by_id = {e.id6: e for e in entries}
    except Exception:
        return items

    out: List[Item] = []
    for it in items:
        if (
            it.tree == "research"
            and it.native_status == "todo"
            and it.attention_class == A.READY
        ):
            entry = by_id.get(it.id)
            stale = entry is not None and (
                entry.set_id in run_sets or it.id in cited_exec
            )
            if stale:
                out.append(it._replace(attention_class=A.PARKED))
                continue
        out.append(it)
    return out


def _record_for(
    tree: str, rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    if tree == "specs":
        return _spec_record(rel, path, text)
    if tree == "plans":
        return _plans_record(rel, path, text)
    if tree == "research":
        return _research_record(rel, path, text)
    if tree == "backlog":
        return _backlog_record(rel, path, text)
    if tree == "releases":
        return _release_record(rel, path, text)
    return None, []


def _release_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    """Attention record for a release record (ship-gate anchor, awrelease). Reads `- Status:` +
    `- Id:` and maps via the releases CLASS_MAP (planned->ready, blocked->blocked, shipped->done)."""
    import re as _re

    drift: List[core.Drift] = []
    ms = _re.search(r"(?m)^- Status:\s*(\S+)\s*$", text)
    status = ms.group(1) if ms else None
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no release Status"))
        return None, drift
    try:
        cls = A.class_of("releases", status)
    except A.UnknownNativeStatus:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"release status {status!r}"),
            )
        )
        return None, drift
    mid = _re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", text)
    lha = A.last_history_at(_history_section_lines(text))
    d_kind, d_text = _extract_detail(text)
    oqs, rqs = count_question_stats(text)
    return Item(
        mid.group(1) if mid else "",
        rel,
        "releases",
        status,
        cls,
        None,
        lha,
        detail_kind=d_kind,
        detail_text=d_text,
        oqs=oqs,
        rqs=rqs,
    ), drift


def _spec_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    drift = specs_mod.validate_spec(path, text)
    lines = text.split("\n")
    status = specs_mod._read_status(lines)
    if status is None or status not in A.SPEC_STATUSES:
        return None, drift  # violations already recorded by validate_spec
    kind, ref, summary = specs_mod._read_gate(lines)
    gate = None
    if status == "deferred" and kind and ref:
        gate = {"kind": kind, "ref": ref}
        if summary:
            gate["summary"] = summary
    lha = A.last_history_at(_history_section_lines(text))
    # awdoctorfix Order 01: read Blocks-Release from the spec's front-matter so the board can surface it.
    br = specs_mod._read_blocks_release(lines)
    # xprio rp859c E-03: populate Item.priority from the spec's `- Priority:` line so the board LABELS
    # a spec's priority via the existing renderer (absent = None = no label). Shared sort key unchanged.
    pr = specs_mod._read_priority(lines)
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    return Item(
        "",
        rel,
        "specs",
        status,
        A.class_of("specs", status),
        gate,
        lha,
        blocks_release=br,
        priority=pr,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
    ), drift


def _plans_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    drift: List[core.Drift] = []
    status = plans_mod.read_status(path)
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no plan Status"))
        return None, drift
    if status not in plans_mod.RECOGNIZED:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"plan status {status!r}"),
            )
        )
        return None, drift
    # disposition vs terminal-status consistency
    disp = (
        rel.split("/")[2]
        if rel.startswith(".agents/plans/") and len(rel.split("/")) > 3
        else ""
    )
    if (
        disp in plans_mod.DIR_TERMINAL
        and plans_mod.DIR_TERMINAL[disp] != status
        and status in plans_mod.TERMINAL
    ):
        drift.append(
            core.Drift(
                rel,
                "attention.disposition-mismatch",
                A.escape_detail(f"dir {disp} vs status {status}"),
            )
        )
    pid = _plans_id(text)
    lha = A.last_history_at(_history_section_lines(text))
    # IPD 7mw7m5 E-02: populate Item.blocks_release for a release-blocking plan so it renders with
    # the `>` glyph / `[blocking]` label like specs/backlog blockers (the release_blockers SET scan
    # already re-reads the file, so set-membership does not depend on this; display parity does).
    br_m = re.search(r"(?m)^- Blocks-Release:\s*(\S+)\s*$", text)
    br = br_m.group(1) if br_m else None
    # xprio 1b45el E-03: populate Item.priority from the plan's `- Priority:` line so the board LABELS
    # a plan's priority via the existing type-agnostic renderer (absent = None = no label). This does
    # NOT alter the shared attention sort key (core), which excludes priority for all trees today.
    pr_m = re.search(r"(?m)^- Priority:[ \t]*(\S+)[ \t]*$", text)
    pr = pr_m.group(1) if pr_m else None
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    exec_prog, valid_prog = _extract_checklist_progress(text)
    return Item(
        pid or "",
        rel,
        "plans",
        status,
        A.class_of("plans", status),
        None,
        lha,
        blocks_release=br,
        priority=pr,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
        exec_progress=exec_prog,
        valid_progress=valid_prog,
    ), drift


def _research_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    drift: List[core.Drift] = []
    data = research_contract.parse_frontmatter(text)
    if not data or "status" not in data:
        drift.append(
            core.Drift(
                rel, "attention.missing-status", "no research frontmatter status"
            )
        )
        return None, drift
    # rstodo p3o9je: normalize the RAW frontmatter status to canonical (a legacy `intake` -> `todo`)
    # BEFORE the STATUSES membership check, native_status storage, and class_of lookup, so an
    # unmigrated `intake` doc classifies exactly as `todo` (READY, stale-reclass, color) through the
    # migration window and never raises attention.unknown-status.
    raw_status = str(data["status"])
    norm = research_contract.normalize_status(raw_status)
    if not norm.ok:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"research status {raw_status!r}"),
            )
        )
        return None, drift
    status = norm.value or raw_status
    rid = str(data.get("id", "")) if data.get("id") else ""
    lha = A.last_history_at(_history_section_lines(text))
    # xprio 6vgd0k E-04: populate Item.priority from the doc's `priority:` frontmatter key so the
    # board LABELS a research doc's priority via the existing renderer (absent = None = no label).
    # Shared sort key unchanged.
    pr_val = data.get("priority")
    pr = str(pr_val) if pr_val not in (None, "") else None
    br_val = (
        data.get("blocks-release")
        or data.get("blocks_release")
        or data.get("Blocks-Release")
    )
    br = str(br_val).strip() if br_val not in (None, "") else None
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    return Item(
        rid,
        rel,
        "research",
        status,
        A.class_of("research", status),
        None,
        lha,
        priority=pr,
        blocks_release=br,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
    ), drift


def _backlog_record(
    rel: str, path: Path, text: str
) -> Tuple[Optional[Item], List[core.Drift]]:
    """Attention record for a backlog item. A `blocked` item carries its typed gate so the board
    renders `[gate kind: ref]` and the JSON includes it (IPD crv40v PR-002)."""

    from agent_workflows import backlog as backlog_mod

    drift: List[core.Drift] = []
    item = backlog_mod.parse_item(text)
    status = item.status
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no backlog Status"))
        return None, drift
    if status not in backlog_mod.STATUSES:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"backlog status {status!r}"),
            )
        )
        return None, drift
    gate = None
    if status == "blocked" and item.gate_kind and item.gate_ref:
        gate = {"kind": item.gate_kind, "ref": item.gate_ref}
    lha = A.last_history_at(_history_section_lines(text))
    d_kind, d_text = _extract_detail(text)
    rd = read_readiness(text)
    oqs, rqs = count_question_stats(text)
    return Item(
        item.id or "",
        rel,
        "backlog",
        status,
        A.class_of("backlog", status),
        gate,
        lha,
        priority=item.priority,
        blocks_release=item.blocks_release,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
    ), drift


# --------------------------------------------------------------------------------------
# Renderers (deterministic)
# --------------------------------------------------------------------------------------


def render_json(items: List[Item], drift: List[core.Drift]) -> str:
    obj = {
        "schema_version": SCHEMA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "valid": len(drift) == 0,
        "items": [
            {
                "id": it.id,
                "path": it.path,
                "tree": it.tree,
                "native_status": it.native_status,
                "attention_class": it.attention_class,
                "gate": it.gate,
                "last_history_at": it.last_history_at,
                "priority": it.priority,
                "blocks_release": it.blocks_release,
                "readiness": it.readiness,
                "oqs": it.oqs,
                "rqs": it.rqs,
                "detail_kind": it.detail_kind,
                "detail_text": it.detail_text,
            }
            for it in items
        ],
        "violations": [
            {"location": d.location, "rule": d.rule, "detail": d.detail} for d in drift
        ],
    }
    # canonical: fixed key order (insertion order above), 2-space indent, sorted item keys off, LF, final newline
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


# xterm-256 palette indices for native statuses. Chosen for legibility on both light and
# dark backgrounds; a status not listed falls back to the class color. Color is decorative
# only: the status WORD is always printed, so meaning survives NO_COLOR / piping / a screen
# reader (the readiness class name in the section header carries the same meaning too).
_CLASS_COLOR_256 = {
    A.ACTIVE: 39,  # bright azure
    A.READY: 40,  # green
    A.BLOCKED: 203,  # salmon/red
    A.DONE: 244,  # gray
    A.PARKED: 244,  # gray
}
_STATUS_COLOR_256 = {
    "active": 39,
    "todo": 44,  # teal (research not-yet-active; rstodo p3o9je, renamed from `intake`)
    "open": 40,
    "ready": 40,
    "pending": 40,
    "approved": 46,  # bright green (cleared to go)
    "reviewed": 226,  # yellow (progressed, awaiting approval)
    "to-review": 214,  # orange (needs a review pass)
    "draft": 245,  # gray (not ready)
    "implementing": 51,  # cyan
    "implemented": 46,
    "executed": 46,  # bright green (implemented and verified)
    "reusable": 39,  # bright azure
    "planned": 40,
    "shipped": 46,
    "reference": 244,
    "archived": 240,
    "blocked": 203,
    "deferred": 208,  # orange-red (gated)
    "done": 244,
    "parked": 244,
    "superseded": 240,
    "not-executed": 240,
}
_TREE_COLOR_256 = 33  # bold blue for the tree-name path segment

_SINGULAR_TYPE = {
    "plans": "plan",
    "specs": "spec",
    "prompts": "prompt",
    "research": "research",
    "backlog": "backlog",
    "walkthroughs": "walkthrough",
    "roadmaps": "roadmap",
    "comms": "comms",
    "actions": "action",
}

TYPE_ALIASES: dict[str, str] = {
    "plan": "plans",
    "plans": "plans",
    "ipd": "plans",
    "spec": "specs",
    "specs": "specs",
    "backlog": "backlog",
    "bk": "backlog",
    "research": "research",
    "survey": "research",
    "findings": "research",
    "release": "releases",
    "releases": "releases",
    "roadmap": "roadmaps",
    "roadmaps": "roadmaps",
    "walkthrough": "walkthroughs",
    "walkthroughs": "walkthroughs",
    "walkthr": "walkthroughs",
    "prompt": "prompts",
    "prompts": "prompts",
    "prompt-library": "prompts",
    "comms": "comms",
    "actions": "actions",
}


def parse_type_filters(raw_types: Sequence[str] | None) -> set[str]:
    """Parse a sequence of type arguments (supporting comma-separated strings and repeated flags)
    into a set of normalized canonical tree names (e.g. 'plans', 'specs', 'backlog').
    """
    if not raw_types:
        return set()
    result: set[str] = set()
    for raw in raw_types:
        if not raw:
            continue
        parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
        for p in parts:
            canonical = TYPE_ALIASES.get(p, p)
            result.add(canonical)
    return result


def parse_filter_tokens(raw_values: Sequence[str] | None) -> set[str]:
    """Parse a sequence of filter arguments (supporting comma-separated strings and repeated flags)
    into a set of normalized lowercase tokens.
    """
    if not raw_values:
        return set()
    result: set[str] = set()
    for raw in raw_values:
        if not raw:
            continue
        parts = [p.strip().lower() for p in str(raw).split(",") if p.strip()]
        result.update(parts)
    return result


def parse_status_filters(raw_statuses: Sequence[str] | None) -> set[str]:
    """Parse status filter arguments, normalizing hyphens and underscores."""
    tokens = parse_filter_tokens(raw_statuses)
    result: set[str] = set()
    for t in tokens:
        result.add(t)
        if "_" in t:
            result.add(t.replace("_", "-"))
        elif "-" in t:
            result.add(t.replace("-", "_"))
    return result


def parse_priority_filters(raw_priorities: Sequence[str] | None) -> set[str]:
    """Parse priority filter arguments."""
    return parse_filter_tokens(raw_priorities)


def parse_blocking_filters(raw_blocking: Sequence[str] | None) -> set[str]:
    """Parse blocking filter arguments."""
    return parse_filter_tokens(raw_blocking)


def parse_readiness_filters(raw_readiness: Sequence[str] | None) -> set[str]:
    """Parse readiness filter arguments, normalizing hyphens and underscores."""
    tokens = parse_filter_tokens(raw_readiness)
    result: set[str] = set()
    for t in tokens:
        result.add(t)
        if "_" in t:
            result.add(t.replace("_", "-"))
        elif "-" in t:
            result.add(t.replace("-", "_"))
    return result


def matches_status(it: Item, status_filters: set[str]) -> bool:
    """Return True if item matches any of the given status filters."""
    if not status_filters:
        return True
    ns = (it.native_status or "").lower()
    ac = (it.attention_class or "").lower()
    candidates = {
        ns,
        ns.replace("_", "-"),
        ns.replace("-", "_"),
        ac,
        ac.replace("_", "-"),
        ac.replace("-", "_"),
    }
    return bool(candidates & status_filters)


def matches_priority(it: Item, priority_filters: set[str]) -> bool:
    """Return True if item matches any of the given priority filters."""
    if not priority_filters:
        return True
    p = (it.priority or "").lower()
    if not p or p == "-":
        return "-" in priority_filters or "none" in priority_filters
    return p in priority_filters


def matches_blocking(
    it: Item, blocking_filters: set[str], repo_root: Path | None = None
) -> bool:
    """Return True if item matches any of the given blocking filters."""
    if not blocking_filters:
        return True
    is_blk = bool(it.blocks_release and it.blocks_release != "-")
    raw_blk = (it.blocks_release or "").lower()
    resolved_ver = (
        _resolve_release_version(repo_root, it.blocks_release).lower() if is_blk else ""
    )
    planned_ver = ""
    planned_id = ""
    if repo_root:
        try:
            from agent_workflows import releases as _releases

            desc = _releases.describe_planned_release(repo_root)
            if desc:
                planned_id = (desc[0] or "").lower()
                planned_ver = (desc[1] or "").lower()
        except (AttributeError, OSError, ValueError):
            pass

    for tok in blocking_filters:
        if tok in ("true", "yes", "1", "any", "blocking"):
            if is_blk:
                return True
        elif tok in ("false", "no", "0", "none", "-", "non-blocking"):
            if not is_blk:
                return True
        elif is_blk:
            tok_clean = tok.lstrip("v")
            raw_clean = raw_blk.lstrip("v")
            res_clean = resolved_ver.lstrip("v")
            plan_clean = planned_ver.lstrip("v")

            if tok == "next":
                # 'next' shows what's blocking the next release regardless of tag/number
                return True
            if tok in (raw_blk, resolved_ver) or tok_clean in (raw_clean, res_clean):
                return True
            if plan_clean and tok_clean == plan_clean:
                if raw_blk in ("next", planned_id) or raw_clean == plan_clean:
                    return True
            if planned_id and tok == planned_id:
                if raw_blk in ("next", planned_id) or raw_clean == plan_clean:
                    return True
    return False


def matches_readiness(it: Item, readiness_filters: set[str]) -> bool:
    """Return True if item matches any of the given readiness filters."""
    if not readiness_filters:
        return True
    r = (it.readiness or "").lower()
    if not r or r == "-":
        return "-" in readiness_filters or "none" in readiness_filters
    r_norm = r.replace("_", "-")
    for tok in readiness_filters:
        tok_norm = tok.replace("_", "-")
        if tok_norm in (r, r_norm):
            return True
    return False


def _colorize_tree_segment(term: T.Term, path: str, tree: str) -> str:
    """Color the tree-name directory segment WITHIN ``path`` bold blue, in place.

    e.g. ``.agents/backlog/open/x.md`` with tree ``backlog`` colors just the ``backlog``
    segment (slashes stay uncolored), adding no width. If the tree name is not a distinct
    ``/tree/`` path segment (some logical trees live under a differently-named directory),
    the path is returned uncolored rather than mis-coloring a partial match.
    """
    seg = f"/{tree}/"
    idx = path.find(seg)
    if idx == -1:
        return path
    start = idx + 1  # first char of the tree name (after the leading slash)
    end = start + len(tree)
    return path[:start] + term.color256(tree, _TREE_COLOR_256, bold=True) + path[end:]


def setup_needed(repo_root: Path) -> bool:
    """setupmarker Order 01 (was awdoctor Order 02): True iff the per-repo reminder marker
    `.aw/setup-repo-needed.md` is present (written by `aw install`, cleared by the `/setup-repo`
    workflow's successful terminal pass or by the user deleting it; NOT by `aw setup`, which is the
    machine-wide install wizard and never touches the marker). DERIVED read-only from the marker;
    NEVER creates anything. Replaces the old open-`setup-repo`-action check (the ledger was
    deleted)."""
    try:
        return (Path(repo_root) / ".aw" / "setup-repo-needed.md").is_file()
    except Exception:
        return False


def release_blockers(items: List[Item], repo_root: Path) -> List[Item]:
    """awdoctor Order 02: items carrying a `- Blocks-Release: next|<id6>` field that are still LIVE.
    Reads the field from each item's file (the awrelease Set defines it). Returns the blocking items.

    Both TERMINAL classes are excluded, not just ``DONE``. A retired artifact keeps its
    ``Blocks-Release`` field on purpose, because the field records what the artifact was FOR and
    erasing it would falsify the record; but a superseded plan or a parked backlog item cannot gate a
    release, since nobody is going to do it. Skipping only ``DONE`` counted a plan retired to
    ``superseded/`` as an outstanding blocker, which is how a split plan kept appearing in the
    release-blocker list after its replacements were filed."""
    import re as _re

    rx = _re.compile(r"(?m)^- Blocks-Release:\s*(\S+)\s*$")
    out: List[Item] = []
    for it in items:
        if it.attention_class in (A.DONE, A.PARKED):
            continue
        if it.blocks_release and it.blocks_release != "-":
            out.append(it)
            continue
        if it.blocks_release is None and it.tree in ("specs", "plans", "backlog"):
            for base in (repo_root / it.path, repo_root / ".aw" / "records" / it.path):
                try:
                    if base.is_file() and rx.search(base.read_text(encoding="utf-8")):
                        out.append(it)
                        break
                except OSError:
                    continue
    return out


_STEM_RE = re.compile(r"^(\d{8}-[a-z0-9-]+?-\d{2}-[0-9a-z]{6})")
_FACET_STRIP_RE = re.compile(r"(\.[a-z0-9-]+)*\.md$")


def _identity_stem(path: str) -> str:
    """awdoctorfix Order 02: the compact, tree-independent identity of a board line's file:
    `YYYYMMDD-<setid>-NN-<id6>` when the basename matches the clustering grammar, else the basename
    with its trailing `.md` / `.<type>.md` facet(s) stripped (e.g. `setup-repo-v1`)."""
    base = path.replace("\\", "/").rsplit("/", 1)[-1]
    m = _STEM_RE.match(base)
    if m:
        return m.group(1)
    return _FACET_STRIP_RE.sub("", base)


def _shared_gate_ref(items: Sequence["Item"], *, long: bool) -> str:
    """The ONE gate ref shared by every gated item in ``items``, or '' when there is no single one.

    THE FOLD DECISION, in one place, because the section header and the item rows must agree: the
    header hoists this ref only when it is shared, and each row suppresses its own gate suffix only
    when the header hoisted it. Deriving that twice is how the two drifted before, with the header
    folding while every row still repeated the ref, so the hoist added a line instead of removing
    noise.

    Returns '' when the group has no gate, only ONE gated item, several distinct refs, or a mix of
    gated and ungated items. Two of those bear explaining. A SINGLE item is not folded because the
    hoist trades one row suffix for one header line and saves nothing, while moving the ref away from
    the row it describes. The MIXED case is excluded because hoisting a ref into a header that also
    covers ungated rows would attribute a gate to items that do not have one.
    """
    gated = [it for it in items if it.gate]
    if len(gated) < 2 or len(gated) != len(items):
        return ""
    refs = {
        _gate_ref_display(A.escape_detail((it.gate or {}).get("ref", "")), long=long)
        for it in gated
    }
    refs.discard("")
    return next(iter(refs)) if len(refs) == 1 else ""


def _gate_ref_display(ref: str, *, long: bool) -> str:
    """A gate ref shortened for the compact board, or returned verbatim.

    The board's identity column already honors `--long` (compact `_identity_stem` by default, full
    path with `--long`), and the gate ref did NOT: it always printed the raw `Gate-Ref:` value, so a
    row showing a 30-char compact identity carried a 110-char repo-relative path for its gate. This
    applies the SAME rule to the ref so one flag governs both.

    ONLY a ref that is actually a path inside the records tree is compacted, which is why this is not
    just `_identity_stem`. A gate ref is a TYPED reference whose kind may be `todo`, `issue`, `date`,
    `decision`, or `external`, so most refs are not paths at all: `TODO.md` must stay `TODO.md` (a
    stem would render it as a bare `TODO`, naming a file that does not exist) and an issue reference
    or a date must survive byte-for-byte. The test is a directory separator, so only a genuinely
    nested path is shortened.
    """
    text = (ref or "").strip()
    if long or "/" not in text.replace("\\", "/"):
        return text
    return _identity_stem(text)


def _common_dir_prefix(paths: List[str]) -> str:
    """The common directory prefix (posix, trailing '/') shared by all paths, or '' if none.
    awdoctor Order 01: folded into a colored section header so per-item lines can be bare names."""
    if not paths:
        return ""
    import posixpath

    norm = [p.replace("\\", "/") for p in paths]
    dirs = [p.rsplit("/", 1)[0] if "/" in p else "" for p in norm]
    common = posixpath.commonpath(dirs) if all(dirs) else ""
    return (common + "/") if common else ""


# awdoctorfix Order 03: trees with no workflow-history lifecycle (research is commonly at todo with
# no history; actions carry status, not a history block) - a None last_history_at is NORMAL there, so
# suppress the `?` unknown-age marker rather than showing noise.
_HISTORYLESS_TREES = {"actions", "research"}


def _age_marker(last_history_at: Optional[str], tree: str = "") -> str:
    """awdoctor Order 01 + awdoctorfix Order 03: a compact staleness marker from last_history_at.
    '!' when older than ~30 days, '?' when unknown (None) EXCEPT on a history-less tree (returns ''),
    else '' (recent). Deterministic: compares ISO dates only."""
    if last_history_at is None:
        return "" if tree in _HISTORYLESS_TREES else "?"
    try:
        from datetime import date

        y, m, d = (int(x) for x in last_history_at.split("-")[:3])
        age_days = (date.today() - date(y, m, d)).days
        return "!" if age_days > 30 else ""
    except (ValueError, TypeError):
        return "?"


def _render_item_row(
    it: Item,
    cls: str,
    term: T.Term,
    colored: bool,
    long: bool,
    details: bool = False,
    gate_in_header: bool = False,
    runs_mode: bool = False,
    run_state: Optional[str] = None,
) -> str:
    """Render ONE board row for an item, in the compact columnar human form (colored) or the
    stable machine form (uncolored). Extracted so the release-blockers section renders items
    identically to the active/ready/blocked sections, not as raw paths.

    ``gate_in_header`` is True only when the caller ALREADY hoisted this group's single shared gate
    ref into the section header, in which case repeating it on every row is the noise the hoist
    exists to remove. It is passed explicitly rather than re-derived from ``cls`` because the two
    conditions are different: the hoist requires the whole group to share ONE ref, so a blocked group
    with several distinct refs is not folded and each row must still name its own gate.
    """
    status_word = it.native_status
    if colored:
        code = _STATUS_COLOR_256.get(it.native_status, _CLASS_COLOR_256.get(cls, 244))
        status_txt = term.color256(status_word, code, bold=True)
        status_padded = status_txt + (" " * max(0, 12 - len(status_word)))
        age = _age_marker(it.last_history_at, it.tree)
        gate_glyph = "#" if it.gate else ""
        rb_glyph = ">" if it.blocks_release else ""
        blk = (age + gate_glyph + rb_glyph).strip()
        lead = f"{blk:<3}" if blk else "   "
        if long:
            path_txt = _colorize_tree_segment(term, it.path, it.tree)
            type_prefix = ""
        else:
            path_txt = _identity_stem(it.path)
            type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
            type_txt = term.color256(type_word, _TREE_COLOR_256, bold=True)
            type_prefix = type_txt + (" " * max(0, 10 - len(type_word))) + "  "
        inline_gate = ""
        if it.gate and not gate_in_header:
            g = it.gate
            ref_txt = _gate_ref_display(
                A.escape_detail(g.get("ref", "")), long=bool(long)
            )
            inline_gate = f"  [gate {g.get('kind')}: {ref_txt}]"
        run_txt = ""
        if runs_mode and run_state and run_state != "-":
            run_code = {
                "running": 51,
                "queued": 220,
                "merging": 201,
                "done": 40,
                "failed": 196,
                "blocked": 214,
            }.get(run_state, 244)
            run_txt = "  " + term.color256(f"[run:{run_state}]", run_code, bold=True)
        prio = ""
        if it.priority:
            pcode = {"high": 196, "medium": 214, "low": 244}.get(it.priority, 244)
            prio = "  " + term.color256(f"[{it.priority}]", pcode, bold=True)
        blocking = ""
        if it.blocks_release:
            blocking = "  " + term.color256("[blocking]", 196, bold=True)
        line = f"- {lead}{status_padded}  {type_prefix}{path_txt}{run_txt}{prio}{blocking}{inline_gate}"
        if details and it.detail_text:
            tag = it.detail_kind or "summary"
            tag_txt = term.color256(f"{tag}:", 244)
            detail_txt = term.color256(it.detail_text, 250)
            line += f"\n      {tag_txt} {detail_txt}"
        return line
    suffix = ""
    if it.gate:
        g = it.gate
        suffix = f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
    run_sfx = ""
    if runs_mode and run_state and run_state != "-":
        run_sfx = f"  [run: {run_state}]"
    line = f"- [{it.tree}] {it.path} ({status_word}){run_sfx}{suffix}"
    if details and it.detail_text:
        tag = it.detail_kind or "summary"
        line += f"\n      {tag}: {it.detail_text}"
    return line


def _resolve_release_version(repo_root: Optional[Path], val: Optional[str]) -> str:
    """Resolve a Blocks-Release value to a concrete release version string (e.g. '2.0.0'),
    or '-' if absent/None."""
    if not val or val == "-":
        return "-"
    if repo_root:
        try:
            from agent_workflows import releases as _releases

            p = _releases.resolve_release(repo_root, val)
            if p and p.is_file():
                m = _releases._VERSION_RE.search(p.read_text(encoding="utf-8"))
                if m:
                    return m.group(1)
            if val == "next":
                desc = _releases.describe_planned_release(repo_root)
                if desc and desc[1] and desc[1] != "?":
                    return desc[1]
            rec = _releases.get_release(repo_root, val)
            if rec and rec.version:
                return rec.version
        except Exception:
            pass
    return val


PRIORITY_RANK = {"": 0, "-": 0, "none": 0, "low": 1, "medium": 2, "med": 2, "high": 3}


_ID6_IN_NAME_RE = re.compile(r"-([0-9a-z]{6})-")
_IDENTITY_PARTS_RE = re.compile(
    r"^(\d{8})-([a-z0-9-]+?)-(\d{2})-([0-9a-z]{6})(?:-|\.|$)"
)
_LEGACY_SPEC_RE = re.compile(r"^(\d{8})-\d{4}-\d{2}-([a-z0-9-]+)")


def _extract_identity_parts(it: Item) -> Tuple[str, str, str]:
    """Extract (Date, SetID, ID6) from an Item's path and metadata."""
    base = it.path.replace("\\", "/").rsplit("/", 1)[-1]
    m = _IDENTITY_PARTS_RE.match(base)
    if m:
        return m.group(1), m.group(2), it.id or m.group(4)
    m_leg = _LEGACY_SPEC_RE.match(base)
    if m_leg:
        return m_leg.group(1), m_leg.group(2), it.id or "-"
    date = base[:8] if len(base) >= 8 and base[:8].isdigit() else "-"
    raw_stem = _FACET_STRIP_RE.sub("", base)
    set_id = raw_stem if raw_stem else "-"
    id6 = it.id if it.id else "-"
    return date, set_id, id6


def _color_dep_id(dep: str, target: Optional[Item], term: T.Term, colored: bool) -> str:
    """Color a dependency id6 to match the color of its target's Status.
    Unknown/unmatched dependencies are colored neutral gray (244).
    """
    if not colored:
        return dep
    if target is None:
        return term.color256(dep, 244)
    code = _STATUS_COLOR_256.get(
        target.native_status, _CLASS_COLOR_256.get(target.attention_class, 244)
    )
    return term.color256(dep, code, bold=True)


def _extract_dependency_id6s(it: Item) -> List[str]:
    """Extract ordered unique dependency id6 strings for an item."""
    ids: List[str] = []
    seen: set = set()

    def _add(cand: str):
        if core.is_valid_id6(cand) and cand not in seen:
            seen.add(cand)
            ids.append(cand)

    if it.item_dependencies:
        for dep in it.item_dependencies:
            cand = dep.rsplit(":", 1)[-1].strip()
            _add(cand)
    if it.gate and isinstance(it.gate, dict):
        ref = str(it.gate.get("ref", "")).strip()
        if core.is_valid_id6(ref):
            _add(ref)
        else:
            m = _ID6_IN_NAME_RE.search(ref)
            if m:
                _add(m.group(1))

    return ids


def _resolve_runs_repo_root(repo_root: Path) -> Path:
    """Resolve the repository root that owns .aw/records/runs (handling git worktrees)."""
    if (repo_root / ".aw" / "records" / "runs").is_dir():
        return repo_root
    git_ref = repo_root / ".git"
    if git_ref.is_file():
        try:
            txt = git_ref.read_text(encoding="utf-8").strip()
            if txt.startswith("gitdir:"):
                gdir = Path(txt.split(":", 1)[1].strip()).resolve()
                candidate = gdir.parent.parent.parent
                if (candidate / ".aw" / "records" / "runs").is_dir():
                    return candidate
        except Exception:
            pass
    if ".aw/worktrees" in str(repo_root.resolve()):
        for parent in repo_root.resolve().parents:
            if (parent / ".aw" / "records" / "runs").is_dir():
                return parent
    return repo_root


def get_active_runs_map(repo_root: Path) -> Dict[str, str]:
    """Scan active runner sessions and return a mapping of id6/path to runner state.

    Only live runs (whose driver process currently holds driver.lock) are inspected.
    States are mapped to: 'running', 'queued', 'merging', 'done', 'failed', 'blocked'.
    """
    from agent_workflows import run_viewer

    run_map: Dict[str, str] = {}
    target_root = _resolve_runs_repo_root(repo_root)
    try:
        runs = run_viewer.discover_run_dirs(target_root)
    except Exception:
        return run_map

    live_runs = [
        r for r in runs if run_viewer.driver_holder_state(r) == run_viewer.HOLDER_LIVE
    ]
    if not live_runs:
        return run_map

    priority_order = {
        "running": 6,
        "merging": 5,
        "queued": 4,
        "done": 3,
        "blocked": 2,
        "failed": 1,
    }

    for run_dir in live_runs:
        state_file = run_dir / "state.json"
        if not state_file.is_file():
            continue
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            queue = state_data.get("queue") or []
            for item in queue:
                id6 = item.get("id6")
                cfg_file = item.get("configured_file")
                raw_st = (item.get("status") or "").lower()

                if raw_st == "running":
                    mapped = "running"
                elif raw_st == "merging":
                    mapped = "merging"
                elif raw_st == "queued":
                    mapped = "queued"
                elif raw_st in (
                    "executed",
                    "reviewed",
                    "substantially-complete",
                    "done",
                    "completed",
                ):
                    mapped = "done"
                elif raw_st in ("failed", "failed-safely", "interrupted"):
                    mapped = "failed"
                elif raw_st in (
                    "blocked",
                    "dependency-blocked",
                    "integration-blocked",
                    "merge-conflict",
                ):
                    mapped = "blocked"
                else:
                    mapped = raw_st[:7] if raw_st else "-"

                new_prio = priority_order.get(mapped, 0)

                keys_to_update = []
                if id6:
                    keys_to_update.append(id6)
                if cfg_file:
                    keys_to_update.append(cfg_file)
                    keys_to_update.append(Path(cfg_file).name)

                for k in keys_to_update:
                    curr = run_map.get(k)
                    curr_prio = priority_order.get(curr, 0) if curr else -1
                    if new_prio >= curr_prio:
                        run_map[k] = mapped
        except Exception:
            continue

    return run_map


def _render_table_row(
    it: Item,
    term: T.Term,
    colored: bool,
    long: bool,
    details: bool = False,
    repo_root: Optional[Path] = None,
    gate_in_header: bool = False,
    set_w: int = 5,
    oq_w: int = 3,
    exec_w: int = 4,
    valid_w: int = 5,
    id_map: Optional[Dict[str, Item]] = None,
    runs_mode: bool = False,
    run_state: Optional[str] = None,
) -> str:
    st_raw = it.native_status[:8]
    if colored:
        code = _STATUS_COLOR_256.get(
            it.native_status, _CLASS_COLOR_256.get(it.attention_class, 244)
        )
        st_styled = term.color256(st_raw, code, bold=True)
    else:
        st_styled = st_raw
    st_col = st_styled + (" " * (8 - len(st_raw)))

    if runs_mode:
        run_raw = (run_state or "-")[:7]
        if colored:
            if run_raw == "-":
                run_styled = term.color256("-", 244)
            elif run_raw == "running":
                run_styled = term.color256(run_raw, 51, bold=True)
            elif run_raw == "queued":
                run_styled = term.color256(run_raw, 220, bold=False)
            elif run_raw == "merging":
                run_styled = term.color256(run_raw, 201, bold=True)
            elif run_raw == "done":
                run_styled = term.color256(run_raw, 40, bold=True)
            elif run_raw == "failed":
                run_styled = term.color256(run_raw, 196, bold=True)
            elif run_raw == "blocked":
                run_styled = term.color256(run_raw, 214, bold=False)
            else:
                run_styled = term.color256(run_raw, 244)
        else:
            run_styled = run_raw
        run_pad = " " * (7 - len(run_raw))
        run_col = f"{run_styled}{run_pad}"

    type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
    tp_raw = type_word[:8]
    if colored:
        tp_styled = term.color256(tp_raw, _TREE_COLOR_256, bold=True)
    else:
        tp_styled = tp_raw
    tp_col = tp_styled + (" " * (8 - len(tp_raw)))

    blk_ver = _resolve_release_version(repo_root, it.blocks_release)
    blk_raw = blk_ver[:6]
    left_pad = " " * (6 - len(blk_raw))
    if colored:
        if blk_raw != "-":
            blk_styled = term.color256(blk_raw, 196, bold=True)
        else:
            blk_styled = term.color256(blk_raw, 244)
    else:
        blk_styled = blk_raw
    blk_col = f"{left_pad}{blk_styled}"

    prio_raw = (it.priority or "-")[:8]
    if colored:
        if prio_raw != "-":
            pcode = {"high": 196, "medium": 214, "low": 244}.get(
                (it.priority or "").lower(), 244
            )
            prio_styled = term.color256(prio_raw, pcode, bold=True)
        else:
            prio_styled = term.color256(prio_raw, 244)
    else:
        prio_styled = prio_raw
    prio_col = prio_styled + (" " * (8 - len(prio_raw)))

    rd_raw = (it.readiness or "-")[:9]
    if colored:
        if rd_raw != "-":
            lower = rd_raw.lower()
            rcode = (
                114
                if ("go" in lower and "no" not in lower)
                else (196 if "no" in lower else 244)
            )
            rd_styled = term.color256(rd_raw, rcode, bold=True)
        else:
            rd_styled = term.color256(rd_raw, 244)
    else:
        rd_styled = rd_raw
    rd_col = rd_styled + (" " * (9 - len(rd_raw)))

    oq_cnt = getattr(it, "oqs", 0) or 0
    rq_cnt = getattr(it, "rqs", 0) or 0
    tot_q = oq_cnt + rq_cnt
    if tot_q > 0:
        oq_raw = f"{oq_cnt}/{tot_q}"
        if colored:
            if oq_cnt == 0:
                oq_styled = term.color256(oq_raw, 40, bold=True)
            else:
                oq_styled = term.color256(oq_raw, 214, bold=True)
        else:
            oq_styled = oq_raw
    else:
        oq_raw = "-"
        oq_styled = term.color256("-", 244) if colored else "-"
    oq_left_pad = " " * max(0, oq_w - len(oq_raw))
    oq_col = f"{oq_left_pad}{oq_styled}"

    exec_prog = getattr(it, "exec_progress", None)
    if exec_prog and exec_prog[1] > 0:
        exec_raw = f"{exec_prog[0]}/{exec_prog[1]}"
        if colored:
            if exec_prog[0] == exec_prog[1]:
                exec_styled = term.color256(exec_raw, 40, bold=True)
            elif exec_prog[0] > 0:
                exec_styled = term.color256(exec_raw, 214, bold=True)
            else:
                exec_styled = term.color256(exec_raw, 244)
        else:
            exec_styled = exec_raw
    else:
        exec_raw = "-"
        exec_styled = term.color256("-", 244) if colored else "-"
    exec_left_pad = " " * max(0, exec_w - len(exec_raw))
    exec_col = f"{exec_left_pad}{exec_styled}"

    valid_prog = getattr(it, "valid_progress", None)
    if valid_prog and valid_prog[1] > 0:
        valid_raw = f"{valid_prog[0]}/{valid_prog[1]}"
        if colored:
            if valid_prog[0] == valid_prog[1]:
                valid_styled = term.color256(valid_raw, 40, bold=True)
            elif valid_prog[0] > 0:
                valid_styled = term.color256(valid_raw, 214, bold=True)
            else:
                valid_styled = term.color256(valid_raw, 244)
        else:
            valid_styled = valid_raw
    else:
        valid_raw = "-"
        valid_styled = term.color256("-", 244) if colored else "-"
    valid_left_pad = " " * max(0, valid_w - len(valid_raw))
    valid_col = f"{valid_left_pad}{valid_styled}"

    date, set_id, id6 = _extract_identity_parts(it)

    date_raw = date[:8]
    if colored and date_raw == "-":
        date_styled = term.color256("-", 244)
    elif colored:
        date_styled = term.color256(date_raw, code, bold=True)
    else:
        date_styled = date_raw
    date_pad = " " * (8 - len(date_raw))
    date_col = f"{date_styled}{date_pad}"

    set_val = it.path if long else set_id
    if colored and long:
        set_styled = _colorize_tree_segment(term, it.path, it.tree)
    elif colored and set_val == "-":
        set_styled = term.color256("-", 244)
    elif colored:
        set_styled = term.color256(set_val, code, bold=True)
    else:
        set_styled = set_val
    set_pad = " " * max(0, set_w - len(set_val))
    set_col = f"{set_styled}{set_pad}"

    id6_raw = id6[:6]
    if colored and id6_raw == "-":
        id6_styled = term.color256("-", 244)
    elif colored:
        id6_styled = term.color256(id6_raw, code, bold=True)
    else:
        id6_styled = id6_raw
    id6_pad = " " * (6 - len(id6_raw))
    id6_col = f"{id6_styled}{id6_pad}"

    dep_ids = _extract_dependency_id6s(it)
    if dep_ids:
        deps_styled_parts = [
            _color_dep_id(dep, id_map.get(dep) if id_map else None, term, colored)
            for dep in dep_ids
        ]
        deps_col = ", ".join(deps_styled_parts)
    else:
        deps_col = term.color256("-", 244) if colored else "-"

    inline_gate = ""
    if it.gate and not gate_in_header:
        ref_txt = _gate_ref_display(
            A.escape_detail(it.gate.get("ref", "")), long=bool(long)
        )
        inline_gate = f"  [gate {it.gate.get('kind')}: {ref_txt}]"

    if runs_mode:
        row_line = (
            f"{st_col} {run_col} {tp_col} {blk_col} {prio_col} {rd_col} {oq_col} "
            f"{exec_col} {valid_col} {date_col} {set_col} {id6_col} {deps_col}{inline_gate}"
        )
    else:
        row_line = (
            f"{st_col} {tp_col} {blk_col} {prio_col} {rd_col} {oq_col} "
            f"{exec_col} {valid_col} {date_col} {set_col} {id6_col} {deps_col}{inline_gate}"
        )
    if details and it.detail_text:
        tag = it.detail_kind or "summary"
        tag_txt = term.color256(f"{tag}:", 244) if colored else f"{tag}:"
        detail_txt = term.color256(it.detail_text, 250) if colored else it.detail_text
        row_line += f"\n      {tag_txt} {detail_txt}"

    return row_line


def is_explicit_order(order_by: Optional[str]) -> bool:
    """Return True if ``order_by`` requests an explicit sort order (not None and not ORDER_CLASS)."""
    return bool(order_by and order_by != A.ORDER_CLASS)


def render_table(
    items: List[Item],
    drift: List[core.Drift],
    show_all: bool = False,
    term: Optional[T.Term] = None,
    long: bool = False,
    details: bool = False,
    repo_root: Optional[Path] = None,
    order_by: Optional[str] = None,
    legend: bool = True,
    id_map: Optional[Dict[str, Item]] = None,
    runs_mode: bool = False,
    run_map: Optional[Dict[str, str]] = None,
) -> str:
    """Render items in a compact columnar table for interactive/TTY viewing.

    Columns: Status (8), [Run (7)], Type (8), Blocks (6), Priority (8), Readiness (9), OQs (3), Exec (4), Valid (5), Date (8), SetID, ID6 (6), Deps.
    Sorted by Type, Blocking (non-blocking first), Priority (none first, then low, med, high), name.
    """
    if term is None:
        term = T.Term(color=True)
    colored = bool(getattr(term, "color", False))

    if repo_root is None:
        try:
            from agent_workflows.project_context import (
                is_project_dir,
                resolve_verb_repo_root,
            )

            cand = resolve_verb_repo_root(None)
            if is_project_dir(cand):
                repo_root = cand
        except Exception:
            pass

    if runs_mode and run_map is None and repo_root is not None:
        run_map = get_active_runs_map(repo_root)
    elif run_map is None:
        run_map = {}

    lines: List[str] = []
    if drift:
        lines.append(
            "VIEW INVALID: contract violations must be resolved before this board is authoritative."
        )
        for d in drift:
            lines.append(f"  ! {d.location}: {d.rule}: {d.detail}")
        lines.append("")

    if not show_all:
        visible = [it for it in items if it.attention_class not in (A.DONE, A.PARKED)]
    else:
        visible = list(items)

    if not visible:
        return "\n".join(lines).rstrip("\n") + "\n" if lines else ""

    if id_map is None:
        id_map = {it.id: it for it in items if it.id}

    if not is_explicit_order(order_by):

        def _sort_key(it: Item) -> Tuple:
            type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
            blk_ver = _resolve_release_version(repo_root, it.blocks_release)
            is_blocking = 0 if (blk_ver == "-" or not it.blocks_release) else 1
            prio_rank = PRIORITY_RANK.get((it.priority or "").lower(), 0)
            name = _identity_stem(it.path)
            return (type_word, is_blocking, prio_rank, name, it.path)

        visible.sort(key=_sort_key)
    # The table is ONE flat list, not per-class sections, so there is no section header to hoist a
    # shared gate ref into. When every visible row is gated by the SAME ref, say it once above the
    # table and drop it from the rows; otherwise each row keeps its own (now `--long`-aware) ref.
    shared_gate = _shared_gate_ref(visible, long=long)
    if shared_gate:
        note = f"all {len(visible)} gated by {shared_gate}"
        lines.append(term.color256(note, 244) if colored else note)

    col_title = "Path" if long else "SetID"
    visible_set_vals = [
        it.path if long else _extract_identity_parts(it)[1] for it in visible
    ]
    set_w = max(len(col_title), max((len(s) for s in visible_set_vals), default=0))

    visible_oq_lens = []
    visible_exec_lens = []
    visible_valid_lens = []
    for it in visible:
        oq_cnt = getattr(it, "oqs", 0) or 0
        rq_cnt = getattr(it, "rqs", 0) or 0
        tot_q = oq_cnt + rq_cnt
        if tot_q > 0:
            visible_oq_lens.append(len(f"{oq_cnt}/{tot_q}"))
        exec_prog = getattr(it, "exec_progress", None)
        if exec_prog and exec_prog[1] > 0:
            visible_exec_lens.append(len(f"{exec_prog[0]}/{exec_prog[1]}"))
        valid_prog = getattr(it, "valid_progress", None)
        if valid_prog and valid_prog[1] > 0:
            visible_valid_lens.append(len(f"{valid_prog[0]}/{valid_prog[1]}"))

    oq_w = max(len("OQs"), max(visible_oq_lens, default=1))
    exec_w = max(len("Exec"), max(visible_exec_lens, default=1))
    valid_w = max(len("Valid"), max(visible_valid_lens, default=1))

    st_hdr = "Status".ljust(8)
    tp_hdr = "Type".ljust(8)
    blk_hdr = "Blocks"
    prio_hdr = "Priority"
    rd_hdr = "Readiness"
    oq_hdr = "OQs".rjust(oq_w)
    exec_hdr = "Exec".rjust(exec_w)
    valid_hdr = "Valid".rjust(valid_w)
    date_hdr = "Date".ljust(8)
    set_hdr = col_title.ljust(set_w)
    id6_hdr = "ID6".ljust(6)

    if runs_mode:
        run_hdr = "Run".ljust(7)
        header = (
            f"{st_hdr} {run_hdr} {tp_hdr} {blk_hdr} {prio_hdr} {rd_hdr} {oq_hdr} "
            f"{exec_hdr} {valid_hdr} {date_hdr} {set_hdr} {id6_hdr} Deps"
        )
    else:
        header = (
            f"{st_hdr} {tp_hdr} {blk_hdr} {prio_hdr} {rd_hdr} {oq_hdr} "
            f"{exec_hdr} {valid_hdr} {date_hdr} {set_hdr} {id6_hdr} Deps"
        )
    lines.append(term.colorize(header, "bold") if colored else header)

    for it in visible:
        run_st = None
        if runs_mode:
            _, _, it_id6 = _extract_identity_parts(it)
            for cand in (it.id, it_id6, it.path, Path(it.path).name):
                if cand and cand in run_map:
                    run_st = run_map[cand]
                    break
        lines.append(
            _render_table_row(
                it,
                term=term,
                colored=colored,
                long=long,
                details=details,
                repo_root=repo_root,
                gate_in_header=bool(shared_gate),
                set_w=set_w,
                oq_w=oq_w,
                exec_w=exec_w,
                valid_w=valid_w,
                id_map=id_map,
                runs_mode=runs_mode,
                run_state=run_st,
            )
        )

    if legend:
        oqs_lbl = term.colorize("OQs", "bold") if colored else "OQs"
        exec_lbl = term.colorize("Exec", "bold") if colored else "Exec"
        valid_lbl = term.colorize("Valid", "bold") if colored else "Valid"
        deps_lbl = term.colorize("Deps", "bold") if colored else "Deps"
        if runs_mode:
            run_lbl = term.colorize("Run", "bold") if colored else "Run"
            lines.append(
                f"{run_lbl} = Active runner state, {oqs_lbl} = Open Questions (open/total), {exec_lbl} = Executed items, "
                f"{valid_lbl} = Validated items, {deps_lbl} = Dependencies"
            )
        else:
            lines.append(
                f"{oqs_lbl} = Open Questions (open/total), {exec_lbl} = Executed items, "
                f"{valid_lbl} = Validated items, {deps_lbl} = Dependencies"
            )

    return "\n".join(lines).rstrip("\n") + "\n"


def render_board(
    items: List[Item],
    drift: List[core.Drift],
    show_all: bool = False,
    term: T.Term | None = None,
    long: bool = False,
    details: bool = False,
    legend: bool | None = None,
    repo_root: Path | None = None,
    order_by: Optional[str] = None,
    id_map: Optional[Dict[str, Item]] = None,
    runs_mode: bool = False,
    run_map: Optional[Dict[str, str]] = None,
) -> str:
    """Render the attention board.

    When ``term`` is colored (a real TTY / FORCE_COLOR), the human view renders the columnar
    table (Status, [Run], Type, Blocks, Priority, Readiness, OQs, Exec, Valid, Date, SetID, ID6, Deps). When color is OFF
    (piped / agent / NO_COLOR / no ``term``), it emits the stable machine-readable
    ``- [tree] path (status){gate}`` form so agents and grep keep a fixed, parseable shape. Under an
    explicit order, the non-colored board emits a single flat, globally-ordered list (sections are
    absent by design); under the default order, items are partitioned into attention class sections.
    """
    if term is None:
        term = T.Term(color=False)
    colored = bool(getattr(term, "color", False))
    if colored:
        return render_table(
            items,
            drift,
            show_all=show_all,
            term=term,
            long=long,
            details=details,
            repo_root=repo_root,
            order_by=order_by,
            legend=True if legend is None else legend,
            id_map=id_map,
            runs_mode=runs_mode,
            run_map=run_map,
        )
    if legend is None:
        legend = colored

    lines: List[str] = []
    if drift:
        lines.append(
            "VIEW INVALID: contract violations must be resolved before this board is authoritative."
        )
        for d in drift:
            lines.append(f"  ! {d.location}: {d.rule}: {d.detail}")
        lines.append("")

    if is_explicit_order(order_by):
        # Under an explicit order, emit ONE globally-ordered list instead of class-partitioned sections.
        # Items were already sorted upstream by cmd_attention; do not re-sort here.
        # Preserve the done/parked suppression unless show_all is True.
        if not show_all:
            visible = [
                it for it in items if it.attention_class not in (A.DONE, A.PARKED)
            ]
        else:
            visible = list(items)

        for it in visible:
            run_st = None
            if runs_mode and run_map:
                _, _, it_id6 = _extract_identity_parts(it)
                for cand in (it.id, it_id6, it.path, Path(it.path).name):
                    if cand and cand in run_map:
                        run_st = run_map[cand]
                        break
            lines.append(
                _render_item_row(
                    it,
                    it.attention_class,
                    term,
                    colored,
                    long,
                    details=details,
                    gate_in_header=False,
                    runs_mode=runs_mode,
                    run_state=run_st,
                )
            )
        return "\n".join(lines).rstrip("\n") + "\n" if lines else ""

    by_class: Dict[str, List[Item]] = {}
    for it in items:
        by_class.setdefault(it.attention_class, []).append(it)
    for cls in A.ATTENTION_CLASS_ORDER:
        group = by_class.get(cls, [])
        if not group:
            continue

        # Section header. In the colored human view, fold a shared gate artifact into the
        # header (e.g. "blocked (2) in TODO.md") instead of repeating it on every line.
        header_extra = ""
        shared_gate = ""
        if colored and cls == A.BLOCKED:
            shared_gate = _shared_gate_ref(group, long=long)
            if shared_gate:
                header_extra = f" in {shared_gate}"

        if cls in (A.DONE, A.PARKED) and not show_all:
            if not colored:
                lines.append(f"## {cls} ({len(group)}) [hidden; use --all]")
            continue

        # awdoctorfix Order 02: the colored default view shows a compact identity stem per item
        # (tree-independent), so no directory prefix is folded into the header. `--long` restores
        # full paths (rendered per-item below); either way the header carries no path prefix.
        header_title = f"{cls} ({len(group)}){header_extra}"
        if colored:
            code = _CLASS_COLOR_256.get(cls, 244)
            lines.append(term.color256(header_title, code, bold=True))
        else:
            lines.append(f"## {header_title}")

        for it in group:
            run_st = None
            if runs_mode and run_map:
                _, _, it_id6 = _extract_identity_parts(it)
                for cand in (it.id, it_id6, it.path, Path(it.path).name):
                    if cand and cand in run_map:
                        run_st = run_map[cand]
                        break
            lines.append(
                _render_item_row(
                    it,
                    cls,
                    term,
                    colored,
                    long,
                    details=details,
                    gate_in_header=bool(shared_gate),
                    runs_mode=runs_mode,
                    run_state=run_st,
                )
            )
    if colored and legend:
        lines.append(
            "legend: ! stale(>30d)  ? unknown-age  # blocked-by-gate  > release-blocker  [priority]"
        )
    return "\n".join(lines).rstrip("\n") + "\n" if lines else ""


# --------------------------------------------------------------------------------------
# CLI entrypoint
# --------------------------------------------------------------------------------------


def filter_items_by_selectors(
    items: List[Item], selectors_list: Sequence[str], repo_root: Path
) -> List[Item]:
    """Filter scanned attention items by one or more selector tokens (id6, setid, path, tree, status, etc.)."""
    tokens = [str(t).strip() for t in selectors_list if str(t).strip()]
    if not tokens:
        return items

    from agent_workflows import selectors

    record_types = (
        "plans",
        "specs",
        "research",
        "backlog",
        "prompts",
        "walkthroughs",
        "roadmaps",
        "releases",
    )
    matched_paths: set = set()
    for tok in tokens:
        for rt in record_types:
            try:
                for p in selectors.resolve_selectors(repo_root, rt, [tok]):
                    matched_paths.add(p.resolve())
            except Exception:
                pass

    filtered: List[Item] = []
    for it in items:
        p_resolved = (repo_root / it.path).resolve()
        matches = False
        if p_resolved in matched_paths:
            matches = True
        else:
            for tok in tokens:
                tok_lower = tok.lower()
                if it.id and it.id.lower() == tok_lower:
                    matches = True
                    break
                if it.tree and it.tree.lower() == tok_lower:
                    matches = True
                    break
                if it.attention_class and it.attention_class.lower() == tok_lower:
                    matches = True
                    break
                if it.native_status and it.native_status.lower() == tok_lower:
                    matches = True
                    break
                if it.priority and it.priority.lower() == tok_lower:
                    matches = True
                    break
                if tok_lower in it.path.lower():
                    matches = True
                    break
        if matches:
            filtered.append(it)
    return filtered


def run(args) -> int:
    # Climb to the project root so `aw attention` works from any subdirectory; an explicit --dir is
    # honored verbatim (IPD awretrofit Order 06).
    from agent_workflows.project_context import (
        is_project_dir,
        no_project_message,
        resolve_verb_repo_root,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
        select_output,
    )

    explicit_dir = getattr(args, "dir", None)
    repo_root = resolve_verb_repo_root(explicit_dir)
    check = getattr(args, "check", False)
    ctx = select_output(args)

    # No AW project at cwd or any ancestor (and none named via --dir): emit the verbose guidance
    # instead of a silent empty board. --check stays fail-closed-valid (nothing to violate).
    if not explicit_dir and not is_project_dir(repo_root):
        if check:
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command="attention",
                    status="clean",
                    exit_code=0,
                    summary="the view is valid",
                    evidence=[
                        Evidence(
                            key="attention",
                            value={"items": 0, "drift": 0},
                            status="clean",
                        )
                    ],
                    data={"items": [], "drift": []},
                )
                return get_renderer(ctx).emit(res, ctx)
            sys.stdout.write("aw attention --check: the view is valid.\n")
            return 0
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="attention",
                status="cannot-run",
                exit_code=3,
                summary=no_project_message("attention"),
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write(no_project_message("attention") + "\n")
        return 3
        return 3

    try:
        items, drift = scan(repo_root)
    except (
        Exception
    ) as exc:  # a could-not-run condition (missing contract symbol, etc.)
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="attention",
                status="cannot-run",
                exit_code=2,
                summary=f"could not run: {exc}",
                diagnostics=[
                    Diagnostic(
                        location=str(repo_root),
                        rule="attention.scan_error",
                        detail=str(exc),
                        severity="error",
                    )
                ],
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write(f"aw attention: could not run: {exc}\n")
        return 2

    all_items_by_id = {it.id: it for it in items if it.id}

    # worksequence i6015i E-04/E-09: apply the requested ORDER to the items the ONE existing scan
    # produced. Read through `getattr` with the contract default, matching how every other option on
    # this path is read, so a narrower caller (a test harness, or an alias parser) still works.
    #
    # ORDERING IS APPLIED AFTER the filters below, deliberately: sorting first and filtering second
    # would give the same sequence but would sort rows that are about to be discarded. The set of items
    # is decided ONLY by the filters, never by the order, which is what makes "ordering never filters"
    # true by construction rather than by assertion.
    order_by = getattr(args, "order_by", None) or A.ORDER_CLASS
    order_notices: List[str] = []

    type_filters = parse_type_filters(getattr(args, "types", None))
    if type_filters:
        items = [it for it in items if it.tree in type_filters]
        if drift:
            selected_paths = {(repo_root / it.path).resolve() for it in items}
            drift = [
                d for d in drift if (repo_root / d.location).resolve() in selected_paths
            ]

    selectors_arg = getattr(args, "selectors", None) or []
    if selectors_arg:
        items = filter_items_by_selectors(items, selectors_arg, repo_root)
        if drift:
            selected_paths = {(repo_root / it.path).resolve() for it in items}
            drift = [
                d for d in drift if (repo_root / d.location).resolve() in selected_paths
            ]

    status_filters = parse_status_filters(getattr(args, "status", None))
    has_terminal_status = any(
        s
        in (
            "done",
            "parked",
            "superseded",
            "not-executed",
            "implemented",
            "shipped",
            "abandoned",
        )
        for s in status_filters
    )
    if status_filters:
        items = [it for it in items if matches_status(it, status_filters)]

    priority_filters = parse_priority_filters(getattr(args, "priority", None))
    if priority_filters:
        items = [it for it in items if matches_priority(it, priority_filters)]

    blocking_filters = parse_blocking_filters(getattr(args, "blocking", None))
    if blocking_filters:
        items = [
            it for it in items if matches_blocking(it, blocking_filters, repo_root)
        ]

    readiness_filters = parse_readiness_filters(getattr(args, "readiness", None))
    if readiness_filters:
        items = [it for it in items if matches_readiness(it, readiness_filters)]

    open_questions_filter = getattr(args, "open_questions", False)
    if open_questions_filter:
        items = [it for it in items if (getattr(it, "oqs", 0) or 0) > 0]
        if not (
            getattr(args, "all", False) or bool(selectors_arg) or has_terminal_status
        ):
            items = [it for it in items if it.attention_class not in (A.DONE, A.PARKED)]

    if (
        any(
            (
                status_filters,
                priority_filters,
                blocking_filters,
                readiness_filters,
                open_questions_filter,
            )
        )
        and drift
    ):
        selected_paths = {(repo_root / it.path).resolve() for it in items}
        drift = [
            d for d in drift if (repo_root / d.location).resolve() in selected_paths
        ]

    # Re-order the (possibly filtered) items. `scan()` already returned them in the default order, so
    # for `-o class` this is a no-op re-sort of an already-sorted list and the output is unchanged.
    if order_by != A.ORDER_CLASS:
        items, order_notices = sort_items_with_notices(
            items, order_by, repo_root=repo_root
        )

    fmt = getattr(args, "format", None)

    if check:
        exit_code = core.drift_exit_code(drift)
        status = "clean" if exit_code == 0 else "findings"
        summary = (
            f"{len(items)} items checked, 0 violations"
            if exit_code == 0
            else f"{len(drift)} finding(s) detected across {len(items)} items"
        )
        if ctx.is_agent or ctx.is_json:
            diagnostics = [
                Diagnostic(
                    location=d.location,
                    rule=d.rule,
                    detail=d.detail,
                    severity="error",
                )
                for d in drift
            ]
            evidence = [
                Evidence(
                    key="attention",
                    value={"items": len(items), "drift": len(drift)},
                    status=status,
                )
            ]
            res = CommandResult(
                command="attention",
                status=status,
                exit_code=exit_code,
                summary=summary,
                diagnostics=diagnostics,
                evidence=evidence,
                data={
                    "items": [it._asdict() for it in items],
                    "drift": [d._asdict() for d in drift],
                },
            )
            return get_renderer(ctx).emit(res, ctx)

        if drift:
            for d in drift:
                sys.stdout.write(f"{d.location}: {d.rule}: {d.detail}\n")
        else:
            sys.stdout.write("aw attention --check: the view is valid.\n")
        return exit_code

    if ctx.is_agent:
        exit_code = core.drift_exit_code(drift)
        status = "clean" if exit_code == 0 else "findings"
        summary = f"{len(items)} attention item(s)"
        # worksequence i6015i E-08: an ordering notice must reach an AGENT too, not only the human
        # board, or `--agent -o depth` would silently absorb a cycle. Emitted as a WARNING diagnostic
        # so it is visible without affecting the exit code (which `core.drift_exit_code(drift)` above
        # has already decided from the drift set alone).
        notice_diagnostics = [
            Diagnostic(
                location=str(repo_root),
                rule="attention.order-notice",
                detail=notice,
                severity="warning",
            )
            for notice in order_notices
        ]
        diagnostics = notice_diagnostics + [
            Diagnostic(
                location=d.location,
                rule=d.rule,
                detail=d.detail,
                severity="error",
            )
            for d in drift
        ]
        evidence = [
            Evidence(
                key="attention",
                value={"items": len(items), "drift": len(drift)},
                status=status,
            )
        ]
        res = CommandResult(
            command="attention",
            status=status,
            exit_code=exit_code,
            summary=summary,
            diagnostics=diagnostics,
            evidence=evidence,
            data={
                "items": [it._asdict() for it in items],
                "drift": [d._asdict() for d in drift],
            },
        )
        return get_renderer(ctx).emit(res, ctx)

    if fmt == "json" or ctx.is_json:
        sys.stdout.write(render_json(items, drift))
    else:
        # Color only for a real TTY (should_color honors NO_COLOR/FORCE_COLOR/TERM/isatty);
        # --no-color forces plain, which also yields the machine-readable [tree] form.
        color = False if getattr(args, "no_color", False) else None
        term = T.Term(stream=sys.stdout, color=color)
        colored = bool(getattr(term, "color", False))
        long = getattr(args, "long", False)
        show_all = (
            getattr(args, "all", False) or bool(selectors_arg) or has_terminal_status
        )
        details = getattr(args, "details", False)
        runs_arg = getattr(args, "runs", False)
        run_map = get_active_runs_map(repo_root) if (runs_arg and repo_root) else {}

        if not colored:
            if is_explicit_order(order_by):
                board = render_board(
                    items,
                    drift,
                    show_all=show_all,
                    term=term,
                    long=long,
                    details=details,
                    legend=False,
                    repo_root=repo_root,
                    order_by=order_by,
                    runs_mode=bool(runs_arg),
                    run_map=run_map,
                )
            else:
                blockers = release_blockers(items, repo_root)
                blocker_keys = {(repo_root / it.path).resolve() for it in blockers}
                main_items = [
                    it
                    for it in items
                    if (repo_root / it.path).resolve() not in blocker_keys
                ]

                board = render_board(
                    main_items,
                    drift,
                    show_all=show_all,
                    term=term,
                    long=long,
                    details=details,
                    legend=False,
                    repo_root=repo_root,
                    order_by=order_by,
                    runs_mode=bool(runs_arg),
                    run_map=run_map,
                )
                if blockers:
                    # Name the release the blockers gate (id6 + version), not just a count, so the
                    # planned release is visible during ordinary tool use - not only a hidden record.
                    try:
                        from agent_workflows import releases as _releases

                        _rel = _releases.describe_planned_release(repo_root)
                    except Exception:
                        _rel = None
                    _rel_label = f" for {_rel[1]} ({_rel[0]})" if _rel else ""
                    rel_header = f"release-blockers{_rel_label} ({len(blockers)})"
                    board += f"## {rel_header}\n"
                    # Render each blocker in the SAME compact columnar form as active/ready/blocked
                    # (not a raw absolute path), so the section reads consistently with the board.
                    for it in blockers:
                        run_st = None
                        if runs_arg and run_map:
                            _, _, it_id6 = _extract_identity_parts(it)
                            for cand in (it.id, it_id6, it.path, Path(it.path).name):
                                if cand and cand in run_map:
                                    run_st = run_map[cand]
                                    break
                        board += (
                            _render_item_row(
                                it,
                                it.attention_class,
                                term,
                                colored,
                                long,
                                details=details,
                                runs_mode=bool(runs_arg),
                                run_state=run_st,
                            )
                            + "\n"
                        )
        else:
            board = render_board(
                items,
                drift,
                show_all=show_all,
                term=term,
                long=long,
                details=details,
                legend=True,
                repo_root=repo_root,
                order_by=order_by,
                id_map=all_items_by_id,
                runs_mode=bool(runs_arg),
                run_map=run_map,
            )
        # bklggrad orb9zb E-06: advisory release-gate warnings (human view only; NEVER affect the
        # exit code). Surfaces orphaned-live-blocker (an open blocking item already handed off to a
        # plan) with a de-gate/close hint.
        try:
            from agent_workflows import check_engine as _ce

            gate_warnings = _ce.release_gate_warnings(repo_root)
            if selectors_arg and gate_warnings:
                selected_paths = {(repo_root / it.path).resolve() for it in items}
                gate_warnings = [
                    w
                    for w in gate_warnings
                    if (repo_root / w.location).resolve() in selected_paths
                ]
        except Exception:
            gate_warnings = []
        if gate_warnings:
            gw_header = f"release-gate-warnings ({len(gate_warnings)})"
            if colored:
                board += term.color256(gw_header, 214, bold=True) + "\n"
            else:
                board += f"## {gw_header}\n"
            # Consistent identity-stem form + an indented, cut-and-paste Fix: line (the detail
            # carries a '\n    Fix: <cmd>' suffix). Uncolored/agent view keeps the full path.
            for w in gate_warnings:
                detail, _, fix = w.detail.partition("\n    Fix:")
                ident = (
                    _identity_stem(w.location) if colored and not long else w.location
                )
                board += f"- {ident}: {w.rule}: {detail}\n"
                if fix.strip():
                    board += f"    Fix: {fix.strip()}\n"

        # worksequence i6015i E-08: surface an ordering notice (currently a dependency cycle under
        # `-o depth`) VISIBLY rather than absorbing it. Advisory only: it never affects the exit code,
        # which stays owned by the drift set, because the fail-closed finding for a cyclic edge set
        # belongs to `aw check`, not to a display option.
        if order_notices:
            oc_header = f"order-notices ({len(order_notices)})"
            if colored:
                board += term.color256(oc_header, 214, bold=True) + "\n"
            else:
                board += f"## {oc_header}\n"
            for notice in order_notices:
                board += f"- {notice}\n"

        footer_lines: list[str] = []
        has_hidden = (
            any(it.attention_class in (A.DONE, A.PARKED) for it in items)
            and not show_all
        )
        needs_setup = setup_needed(repo_root)
        if needs_setup and has_hidden:
            footer_lines.append(
                "TODO: Run `/aw setup-repo` to set up this repo. Use `aw att --all` to see old stuff."
            )
        elif needs_setup:
            footer_lines.append("TODO: Run `/aw setup-repo` to set up this repo.")
        elif has_hidden and colored:
            footer_lines.append("Use `aw att --all` to see old stuff.")

        if footer_lines:
            board = board.rstrip("\n") + "\n" + "\n".join(footer_lines) + "\n"
        else:
            board = board.rstrip("\n") + "\n"
        sys.stdout.write(board)
    # a plain view still fails closed if invalid, so consumers cannot treat an invalid view as authoritative
    return core.drift_exit_code(drift)
