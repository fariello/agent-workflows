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

import contextvars
import functools
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Collection,
    Dict,
    FrozenSet,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

from agent_workflows import artifact_core as core
from agent_workflows import artifact_naming as _naming
from agent_workflows.artifact_types import EXIT_CANNOT_RUN
from agent_workflows import attention_contract as A
from agent_workflows import check_engine as _ce
from agent_workflows import ipd_schema as _schema
from agent_workflows import lifecycle_style as LS
from agent_workflows import plans as plans_mod
from agent_workflows import research_contract
from agent_workflows import selectors as _sel
from agent_workflows import specs as specs_mod
from agent_workflows import term as T

# 3: items gained readiness + oqs + rqs (2 was priority + blocks_release).
# 4 (lanestrand-01 `pr5b0t` E-05): the payload gained the top-level `stranded_lanes` key. BUMPED
# rather than added silently, on this payload's OWN precedent: both earlier bumps were purely ADDITIVE
# too (items gained fields; nothing was removed or renamed), so "additive" has never been this
# repository's reason to skip a bump. The decisive argument is that a consumer must be able to tell
# whether `stranded_lanes` is ABSENT because this repository has no stranded lane or because the
# producer predates the key, and only the version distinguishes those. Every pre-existing key keeps its
# name, its position and its value.
# 5 (rereview `ygngc2` E-04): items gained the `review_stale` field (list of reasons). BUMPED on the
# same additive precedent so consumers can distinguish absence from pre-dating the field.
SCHEMA_VERSION = 5
# MAPPING_VERSION is deliberately UNCHANGED at 1. It versions the native-status -> attention-class
# mapping, and no existing `(tree, native_status)` pair maps anywhere new: `attention_contract`'s new
# `lanes` fragment adds a SYNTHETIC tree whose states never previously had a class at all, and no
# scanned artifact's class changed. Bumping it would tell every consumer to re-derive a mapping that is
# byte-identical for every artifact they can see.
MAPPING_VERSION = 1

# attsel `fqnj8k` E-06: THE EXIT CODE FOR A SELECTOR THAT MATCHED NO ARTIFACT.
#
# THE DECISION, WITH THE REJECTED ALTERNATIVES NAMED, so a later reader sees this was decided rather
# than defaulted. `aw attention <selector>` used to print an empty view and exit 0 for a token that
# matched nothing, byte-identical to a token that matched and was then narrowed away downstream, so an
# operator could not tell a typo from a quiet repository and a machine consumer recorded a typo as a
# clean audit.
#
# CHOSEN: 2, with outcome `cannot-run` on the machine surfaces. FOLLOWING THE PRECEDENT spec `25kzda`
# (`Status: approved`) Section 2.3 sets: "Zero matches return exit 2", with the single Section 2.4a
# exemption for STATUS selectors because such a token is "a standing question about repository state
# rather than an assertion that a named item exists", closing "A misspelled id6 still exits 2; only
# the status selectors are exempt". That spec governs `aw <host> run` rather than this verb, so it is
# PRECEDENT and not binding contract; it is adopted because `aw runs` already implements exactly it for
# the identical condition (an unresolvable read-only target: `run_viewer.py`
# `emit_unresolvable_target_refusal`, exit 2, `cannot-run`, `unresolved_targets`).
#
# REJECTED, exit 1 folded into the drift/findings code: `agent_schema.validate_agent_record`'s parity
# rule makes `exit:1` incompatible with `cannot-run`, so this would force a `findings` outcome for a
# request that was never answered - the same greenwash the fix exists to remove - and it would be
# indistinguishable from a genuine contract violation.
#
# REJECTED, exit 0 with a message only, which is the live `aw find` convention (`aw find plans zzzzzz`
# prints `no matching plans` and exits 0): a script that greps for an id6 and gets exit 0 with empty
# output concludes "nothing to do", which is exactly the wrong conclusion, and this plan's execution
# contract mandates the fail-closed form. OQ-01 leaves the relaxation to the maintainer; it is one
# constant and its pinning tests.
#
# IT COMPOSES WITH DRIFT rather than masking it (F12). 2 dominates `core.drift_exit_code`'s 0/1, so a
# no-match on a drifty view can never be read as a clean view, and the drift findings are still carried
# in the record's diagnostics and in the human message, so neither code hides the other.
EXIT_UNRESOLVED_SELECTOR = 2


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
    review_stale: Tuple[str, ...] = ()
    # metastore wilgfy E-02 (spec 4sd62s 4.4): `time` when `last_history_at` is a post-cutover event
    # `at`, `day` when it is the checkpoint `last_history_day`. Set only on log-format records at
    # metadata_schema 2, and emitted only when set, so legacy output keeps its bytes.
    last_history_precision: Optional[str] = None


_OQ_SECTION_RE = re.compile(
    r"^##\s+(?:[0-9]+\.\s*)?(?:Open|Resolved)\s+questions\b", re.IGNORECASE
)
_OQ_SECTION_SEARCH_RE = re.compile(
    r"(?m)^##\s+(?:[0-9]+\.\s*)?(?:Open|Resolved)\s+questions\b", re.IGNORECASE
)
_OQ_HEADING_RE = re.compile(
    r"^###\s+((?:OQ|RQ)-[0-9]+|(?:OQ|RQ)-[A-Za-z0-9_-]+):?\s*(.*)$", re.IGNORECASE
)
_OQ_STATUS_RE = re.compile(r"^-[ \t]*Status:[ \t]*(\S+)", re.IGNORECASE)


def _find_oq_section_span(text: str) -> Optional[Tuple[int, int]]:
    """Return ``(start, end)`` of the first Open/Resolved questions H2 heading line, or None.

    Uses C-level ``str.find`` to jump directly between ``##`` headings instead of scanning the
    entire document with a case-insensitive multiline regex.
    """
    pos = 0 if text.startswith("##") else text.find("\n##")
    while pos != -1:
        line_start = pos if pos == 0 else pos + 1
        nl = text.find("\n", line_start)
        line = text[line_start:] if nl == -1 else text[line_start:nl]
        m = _OQ_SECTION_RE.match(line)
        if m:
            return line_start, line_start + m.end()
        pos = text.find("\n##", line_start + 2)
    return None


def count_question_stats(text: str) -> Tuple[int, int]:
    """Count (unresolved_oqs, resolved_rqs) in an artifact's '## Open questions' section."""
    if not text:
        return 0, 0
    span = _find_oq_section_span(text)
    if span is None:
        return 0, 0
    start_idx, end_idx = span
    next_h2 = re.search(r"(?m)^##\s+", text[end_idx:])
    if next_h2:
        section_text = text[start_idx : end_idx + next_h2.start()]
    else:
        section_text = text[start_idx:]

    sec_lower = section_text.lower()
    if "oq-" not in sec_lower and "rq-" not in sec_lower:
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

    for line in section_text.splitlines():
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
                if status_val in ("resolved", "closed", "done", "answered"):
                    is_resolved = True
                elif status_val in ("open", "deferred", "pending", "unresolved"):
                    is_resolved = False
                explicit_status = True
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


def _normalize_readiness_value(raw: Any) -> Optional[str]:
    """Normalize a cached readiness string against the closed schema enum, or None."""
    if raw is None:
        return None
    val = str(raw).strip().lower()
    return val if val in _schema.READINESS_VALUES else None


def read_readiness(text: str) -> Optional[str]:
    """The artifact's `- Readiness:` value normalized to the closed enum, or None.

    Reads through `artifact_meta.read_text` and validates against `ipd_schema.READINESS_VALUES`
    so absent and out-of-vocabulary values both fail closed to None. Pure.
    """
    if not text or "readiness:" not in text.lower():
        return None
    from agent_workflows import artifact_meta as _meta

    st = _meta.read_text(text, record_type="ipd")
    return _normalize_readiness_value(st.fields.get("readiness"))


def _readiness_from_state(state: Any, text: str) -> Optional[str]:
    """Read normalized readiness from cached `artifact_meta.State` (with read_text for non-IPD)."""
    if state is not None:
        raw = state.fields.get("readiness")
        if raw is not None:
            return _normalize_readiness_value(raw)
        if state.type == "ipd":
            return None
        if state.type in ("spec", "backlog") and text and "readiness:" in text.lower():
            from agent_workflows import artifact_meta as _meta

            return _normalize_readiness_value(
                _meta.read_text(text, record_type=state.type).fields.get("readiness")
            )
    return None


def _detail_from_state(state: Any, text: str) -> Tuple[Optional[str], Optional[str]]:
    """Return `(detail_kind, detail_text)`: cached `short_description` wins (D-3), else `_extract_detail`."""
    if state is not None:
        sd = getattr(state, "short_description", None)
        if isinstance(sd, str) and sd.strip():
            return "summary", sd.strip()
    return _extract_detail(text)


def _last_history_at_for_state(
    state: Any, *, project_context: Any = None
) -> Optional[str]:
    """Derive `last_history_at` from `artifact_meta` state and `artifact_meta.history`."""
    if state is None:
        return None
    # Log-format record (replayed from meta/<id6>.jsonl): query artifact_meta.history via the
    # artifact_meta history grammar.
    if (
        getattr(state, "updated_at", None) is not None
        or getattr(state, "created_at", None) is not None
    ):
        id6 = getattr(state, "id6", None)
        if id6 and project_context is not None:
            from agent_workflows import artifact_meta as _meta

            try:
                events = _meta.history(id6, project_context=project_context)
            except Exception:
                events = []
            # Phase B: prefer legacy history lines through the unchanged newest-record rule,
            # then checkpoint last_history_day, then newest event date.
            legacy_lines = [
                ev["line"]
                for ev in events
                if isinstance(ev, dict)
                and isinstance(ev.get("line"), str)
                and ev["line"]
            ]
            if legacy_lines:
                return _meta._last_history_at(legacy_lines)
            if state.last_history_day:
                return state.last_history_day
            return _meta._last_history_at(events)
        return state.last_history_day
    # Legacy .md record: last_history_day is the cached projection of the newest-record date over
    # artifact_meta's parsed history lines.
    return state.last_history_day


def _with_post_cutover_history(it: Item, state: Any, project_context: Any) -> Item:
    """Spec 4.4: a log-format record's `last_history_at` is its newest post-cutover event `at`
    (precision `time`), else the checkpoint `last_history_day` (precision `day`)."""
    from agent_workflows import artifact_meta as _meta

    id6 = getattr(state, "id6", None)
    if not id6 or project_context is None:
        return it
    try:
        records_root = Path(project_context.logical_roots["records"])
        if _meta._storage_format(records_root, id6) != "log":
            return it
        value, precision = _meta.last_history(
            id6, project_context=project_context, state=state
        )
    except Exception:
        return it
    return it._replace(last_history_at=value, last_history_precision=precision)


def _post_cutover_history_applies(repo_root: Path) -> bool:
    from agent_workflows.migrations import chain as _chain

    try:
        return (_chain.read_metadata_schema(repo_root) or 0) >= 2
    except Exception:
        return False


def _item_dict(it: Item) -> Dict[str, Any]:
    d = it._asdict()
    if d.get("last_history_precision") is None:
        d.pop("last_history_precision", None)
    return d


def count_unresolved_open_questions(text: str) -> int:
    """Count open/unresolved questions in an artifact's '## Open questions' section."""
    oqs, _ = count_question_stats(text)
    return oqs


_EV_LEAF_RE = re.compile(r"^-\s*\[([ xX])\]\s*([EV])-[0-9]{2,}\b", re.MULTILINE)
_EV_LINE_RE = re.compile(r"^-\s*\[([ xX])\]\s*([EV])-[0-9]{2,}\b")


def _extract_checklist_progress(
    text: str,
) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
    """Extract (exec_progress, valid_progress) as ((checked, total), (checked, total)) for a plan.

    Returns (None, None) if no E or V items are present respectively.
    """
    if not text or ("E-" not in text and "V-" not in text):
        return None, None
    e_checked = 0
    e_total = 0
    v_checked = 0
    v_total = 0
    pos = text.find("[")
    n = len(text)
    last_ls = -1
    while pos != -1:
        if pos + 2 < n and text[pos + 2] == "]" and text[pos + 1] in " xX":
            ls = text.rfind("\n", 0, pos) + 1
            if ls != last_ls and text[ls] == "-":
                last_ls = ls
                nl = text.find("\n", pos)
                line = text[ls:] if nl == -1 else text[ls:nl]
                m = _EV_LINE_RE.match(line)
                if m:
                    mark, kind = m.group(1), m.group(2)
                    if kind == "E":
                        e_total += 1
                        if mark != " ":
                            e_checked += 1
                    else:
                        v_total += 1
                        if mark != " ":
                            v_checked += 1
                if nl == -1:
                    break
                pos = text.find("[", nl + 1)
                continue
        pos = text.find("[", pos + 1)

    exec_prog = (e_checked, e_total) if e_total else None
    valid_prog = (v_checked, v_total) if v_total else None
    return exec_prog, valid_prog


def count_resolved_questions(text: str) -> int:
    """Count resolved questions in an artifact's '## Open questions' section."""
    _, rqs = count_question_stats(text)
    return rqs


_H1_RX = re.compile(r"(?m)^#\s+(?:[A-Za-z0-9_-]+:\s*)?(.+)$")


def _extract_detail(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract (detail_kind, detail_text) using the fallback cascade:
    Summary -> Scope -> Concern -> Question -> Title -> H1 header.

    Delegates metadata field extraction (bulleted `- Key: value` over leading YAML front-matter
    `key: value`) to `artifact_meta.extract_detail_fields`, then falls back to the first H1 heading.
    """
    from agent_workflows import artifact_meta as _meta

    kind, val = _meta.extract_detail_fields(text)
    if kind is not None and val:
        return kind, val
    if "# " in text:
        m = _H1_RX.search(text)
        if m:
            val = m.group(1).strip()
            if val:
                return "title", val
    return None, None


def _safe_detail(text: str) -> str:
    """Neutralize control characters and escape Markdown metacharacters for detail display.

    Applies neutralize_control_characters first and escape_markdown_inline second,
    ensuring that raw control characters (C0, C1, DEL, bidi controls) are replaced
    with U+FFFD before any escape backslashes are inserted.
    """
    return A.escape_markdown_inline(A.neutralize_control_characters(text))


def _rel_posix(repo_root: Path, p: Path) -> str:
    """Return ``p`` relative to ``repo_root`` (POSIX).

    Delegates to :func:`artifact_core.repo_relative_posix` (IPD ``61lsze``) so out-of-root
    inputs, relative inputs when ``os.getcwd() != repo_root``, and in-root symlinked files
    under a symlinked root return a leak-free string instead of raising ``ValueError``,
    allowing ``attention.item_for_path`` to return ``None`` via ``_classify_tree`` on
    out-of-root inputs.
    """
    return core.repo_relative_posix(p, repo_root)


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


def _format_structured_dependency(entry: Any) -> Optional[str]:
    """Format one cached structured dependency entry into canonical token form."""
    if isinstance(entry, str):
        edge, err = _schema._parse_item_dependency_edge(entry)
        return edge.canonical() if (not err and edge is not None) else None
    if isinstance(entry, dict):
        cond = entry.get("condition")
        target = entry.get("target_raw") or entry.get("target_id6") or entry.get("id6")
        ttype = entry.get("target_type")
        req_status = entry.get("required_status")
        if cond == "state" and ttype and req_status and target:
            raw = f"state:{ttype}:{req_status}:{target}"
        elif cond == "exists" and ttype and target:
            raw = f"exists:{ttype}:{target}"
        elif cond and target:
            raw = f"{cond}:{target}"
        else:
            return None
        edge, err = _schema._parse_item_dependency_edge(raw)
        return edge.canonical() if (not err and edge is not None) else None
    return None


def _extract_item_dependencies(
    text: str = "", *, state: Any = None
) -> Optional[Tuple[str, ...]]:
    """The artifact's declared `Item-Dependencies` edges in canonical token form, or None.

    Reads the cached `item_dependencies` field from `artifact_meta.State` (falling back to
    `artifact_meta.read_text(text)` when called without a `State`). Returns None when the field
    is ABSENT, and a (possibly empty) tuple when it is present. Reuses
    `ipd_schema.parse_item_dependencies` so the edge grammar, sentinels, target types, and
    canonical token spelling all come from the one owning module. Pure.
    """
    if state is None:
        if "Item-Dependencies:" not in text and "item-dependencies:" not in text:
            return None
        from agent_workflows import artifact_meta as _meta

        state = _meta.read_text(text)
    raw = state.fields.get("item_dependencies")
    if raw is None:
        dep_decl = state.fields.get("dependency_declaration")
        if dep_decl in ("none", "unresolved"):
            return ()
        return None
    if isinstance(raw, str):
        edges, _ready, err = _schema.parse_item_dependencies(raw)
        if err:
            return ()
        return tuple(e.canonical() for e in edges)
    if isinstance(raw, (list, tuple)):
        out = []
        for entry in raw:
            tok = _format_structured_dependency(entry)
            if tok is not None:
                out.append(tok)
        return tuple(out)
    return ()


def _plans_id(text: str) -> Optional[str]:
    """Return the plan's declared `- Id:` value via `artifact_meta.read_text`, or None."""
    if not text:
        return None
    from agent_workflows import artifact_meta as _meta

    st = _meta.read_text(text, record_type="ipd")
    return st.id6 or st.loose_id or None


_TREE_TO_SCAN_ROOTS: Dict[str, Tuple[str, ...]] = {
    "plans": (".aw/records/plans", ".agents/plans"),
    "specs": (".aw/records/specs", ".agents/docs/specs"),
    "research": (".aw/records/research", ".agents/docs/research"),
    "backlog": (".aw/records/backlog", ".agents/backlog"),
    "releases": (".aw/records/releases", ".agents/releases"),
    "walkthroughs": (".aw/records/walkthroughs", ".agents/docs/walkthroughs"),
    "roadmaps": (".aw/records/roadmaps", ".agents/docs/roadmaps"),
    "prompts": (
        ".aw/records/prompt-library",
        ".agents/docs/prompts",
        ".aw/records/prompts",
        ".agents/prompts",
    ),
    "prompt-library": (".aw/records/prompt-library", ".agents/docs/prompts"),
    "comms": (".aw/records/comms", ".agents/comms"),
}


#: The fatal status-parse drift rules that cause an artifact to fail its per-tree status
#: parse. When one of these fires and no Item was produced, attention.scan synthesizes a
#: degraded Item so the broken artifact is visible across CLI surfaces.
FATAL_STATUS_PARSE_RULES: FrozenSet[str] = frozenset(
    {"attention.missing-status", "attention.unknown-status"}
)


#: Framework-owned non-record top-level directories under legacy `.agents/` layouts.
#: Shallow uninventoried-tree discovery skips these names only when `scan()` falls back
#: to `.agents/` because `project_records_dir(repo_root)` does not exist on disk:
#: - `workflows`: legacy system workflow bundle (modern counterpart: `.aw/system/workflows/`).
#: - `skills`: host skill packages (modern counterpart: `.agents/skills/`, also present
#:   on modern installs before `.aw/records/` exists).
#: - `agent-workflows`: legacy install manifest directory holding `managed-sections.json`
#:   (modern counterpart: `.aw/system/managed-sections.json`).
#: - `inbox`: legacy raw-drop inbox (modern counterpart: `.aw/inbox/`).
#: - `runs`: legacy run history (modern counterpart: `.aw/runs/`).
#: - `state`: legacy durable runtime state (modern counterpart: `.aw/state/`).
_LEGACY_AGENTS_NON_RECORD_DIRS: FrozenSet[str] = frozenset(
    {"workflows", "skills", "agent-workflows", "inbox", "runs", "state"}
)


_TREE_TO_META_TYPE: Dict[str, str] = {
    "plans": "ipd",
    "specs": "spec",
    "backlog": "backlog",
    "research": "research",
    "releases": "release",
    "prompts": "prompt",
}


_ACTIVE_META_CTX: contextvars.ContextVar[Optional[Tuple[Any, Any]]] = (
    contextvars.ContextVar("_ACTIVE_META_CTX", default=None)
)


def _filename_id6(name: str) -> Optional[str]:
    """Extract an id6 from an attributed or clustered artifact filename, or None."""
    m_attr = _naming.parse_attributed(name)
    if m_attr is not None:
        return m_attr.id6
    m = _naming.parse_clustered(name)
    if m is None:
        m = _naming.parse_clustered_prefix(name)
    return m.group("id6") if m else None


def scan(
    repo_root: Path, type_filters: Optional[Collection[str]] = None
) -> Tuple[List[Item], List[core.Drift]]:
    """Full deterministic scan of the tracked trees via `artifact_meta.query`. Pure read."""

    from agent_workflows import artifact_meta as _meta

    items: List[Item] = []
    drift: List[core.Drift] = []
    seen_ids: Dict[str, str] = {}
    seen_paths: set = set()

    scan_roots = None
    query_type: Optional[str] = None
    if type_filters:
        collected = []
        meta_types = []
        for t in type_filters:
            if t in _TREE_TO_SCAN_ROOTS:
                collected.extend(_TREE_TO_SCAN_ROOTS[t])
            else:
                collected = None
                break
            mt = _TREE_TO_META_TYPE.get(t)
            if mt:
                meta_types.append(mt)
        if collected is not None and collected:
            scan_roots = tuple(dict.fromkeys(collected))
        unique_mt = tuple(dict.fromkeys(meta_types))
        if len(unique_mt) == 1 and len(type_filters) == 1:
            query_type = unique_mt[0]

    ctx = _meta.legacy_context(repo_root)
    records_root = Path(ctx.logical_roots["records"])
    scan_repo = _meta._scan_repo_root(ctx, records_root)

    with _meta.scan_once(), _meta.ephemeral_if_uninitialized():
        q_kwargs: Dict[str, Any] = {"project_context": ctx, "include_fields": True}
        if query_type is not None:
            q_kwargs["type"] = query_type
        qres = _meta.query(**q_kwargs)

        state_by_rel: Dict[str, Any] = {}
        for st in qres:
            if not st.path:
                continue
            try:
                abs_p = _meta.source_path(st.path, records_root, scan_repo)
                st_rel = _rel_posix(repo_root, abs_p)
            except Exception:
                continue
            state_by_rel[st_rel] = st

        incomplete_ids: List[str] = list(getattr(qres, "incomplete", ()) or ())
        incomplete_set = set(incomplete_ids)
        handled_incomplete: set = set()

        scan_files = (
            core.iter_scan_files(repo_root, scan_roots=scan_roots)
            if scan_roots
            else core.iter_scan_files(repo_root)
        )

        for f in scan_files:
            rel = _rel_posix(repo_root, f)
            # only artifacts under an inventoried tree matter; the four root docs + READMEs are not artifacts
            pol = _classify_tree(rel)
            if pol is None:
                if not A.is_exempt_unclassified(rel):
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

            # IPD mtdxiu E-06 (Set rescomp): companion files belonging to a research document
            # companion directory (<doc-stem>.data/) are not artifacts and are not tracked by
            # attention (an orphaned companion is policed by check.research-companion-orphaned).
            if pol.name == "research":
                from agent_workflows import research_contract as _rc

                if _rc.companion_owner_stem(f, repo_root) is not None:
                    continue

            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                drift.append(
                    core.Drift(rel, "attention.unreadable", "cannot read/decode")
                )
                unr_id = _filename_id6(f.name)
                if unr_id and unr_id in incomplete_set:
                    handled_incomplete.add(unr_id)
                continue

            if rel in seen_paths:
                drift.append(
                    core.Drift(
                        rel, "attention.duplicate-path", "duplicate normalized path"
                    )
                )
                continue
            seen_paths.add(rel)

            meta_type = _TREE_TO_META_TYPE.get(pol.name, "ipd")
            state = state_by_rel.get(rel)
            if state is None:
                cand_id = _filename_id6(f.name)
                if not cand_id:
                    st_probe = _meta.read_text(text, record_type=meta_type)
                    cand_id = st_probe.id6 or st_probe.loose_id
                if cand_id and cand_id in incomplete_set:
                    handled_incomplete.add(cand_id)
                    drift.append(
                        core.Drift(
                            rel,
                            "attention.missing-status",
                            f"incomplete metadata record {cand_id}",
                        )
                    )
                    items.append(
                        Item(
                            id=cand_id,
                            path=rel,
                            tree=pol.name,
                            native_status="-",
                            attention_class=A.BLOCKED,
                            gate=None,
                            last_history_at=None,
                        )
                    )
                    continue
                state = _meta.read_text(text, record_type=meta_type)

            tok = _ACTIVE_META_CTX.set((state, ctx))
            try:
                rec, rec_drift = _record_for(pol.name, rel, f, text)
            finally:
                _ACTIVE_META_CTX.reset(tok)
            drift.extend(rec_drift)
            if rec is None:
                if any(d.rule in FATAL_STATUS_PARSE_RULES for d in rec_drift):
                    deg_id = _filename_id6(f.name) or ""
                    items.append(
                        Item(
                            id=deg_id,
                            path=rel,
                            tree=pol.name,
                            native_status="-",
                            attention_class=A.BLOCKED,
                            gate=None,
                            last_history_at=None,
                        )
                    )
                continue

            deps = _extract_item_dependencies(text, state=state)
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

        # Report any remaining invalid/incomplete records from artifact_meta.query() so an
        # invalid record is never silently dropped (dqutt8 E-02).
        for inc_id in incomplete_ids:
            if inc_id in handled_incomplete:
                continue
            log_path = records_root / "meta" / f"{inc_id}.jsonl"
            loc = _rel_posix(repo_root, log_path) if log_path.exists() else inc_id
            drift.append(
                core.Drift(
                    loc,
                    "attention.missing-status",
                    f"incomplete metadata record {inc_id}",
                )
            )

    # E-04 (IPD 1qt1u3): shallow discovery of uninventoried records trees.
    # When a tree exists on disk but has no entry in SCAN_ROOTS, iter_scan_files never opens it,
    # so no per-file check can see it. A shallow listing of the records root surfaces such trees.
    if not type_filters:
        from agent_workflows.project_context import project_records_dir

        records_dir = project_records_dir(repo_root)
        using_legacy_agents_fallback = False
        if not records_dir.is_dir():
            records_dir = repo_root / ".agents"
            using_legacy_agents_fallback = True
        if records_dir.is_dir():
            for entry in sorted(records_dir.iterdir(), key=lambda p: p.name):
                if not entry.is_dir():
                    continue
                if (
                    using_legacy_agents_fallback
                    and entry.name in _LEGACY_AGENTS_NON_RECORD_DIRS
                ):
                    continue
                if core.is_ignored_path(entry, repo_root):
                    continue
                rel_dir = _rel_posix(repo_root, entry)
                if _classify_tree(rel_dir) is None and not any(
                    pol.root.startswith(rel_dir + "/") for pol in A.TREE_POLICY
                ):
                    drift.append(
                        core.Drift(
                            rel_dir,
                            "attention.uninventoried-tree",
                            "tree directory under records root matching no policy",
                        )
                    )

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

    # rereview ygngc2 E-04: bulk-resolve review staleness for candidate reviewed/approved plans in one call.
    # Only plans in reviewed/approved/auto-approved can ever be review-stale; skipping terminal and
    # draft/to-review plans avoids reading and parsing ~1,900 executed plans on every attention scan.
    plan_items = [
        it
        for it in items
        if it.tree == "plans"
        and it.native_status in ("reviewed", "approved", "auto-approved")
    ]
    if plan_items:
        try:
            from agent_workflows.plan_readiness import review_staleness_index

            stale_map = review_staleness_index(
                repo_root, [repo_root / it.path for it in plan_items]
            )
            if stale_map:
                items = [
                    (
                        it._replace(review_stale=stale_map[it.path].reasons)
                        if it.tree == "plans" and it.path in stale_map
                        else it
                    )
                    for it in items
                ]
        except Exception:
            pass

    # worksequence i6015i E-04: the default order is unchanged. `sort_items` with the default key
    # reproduces exactly the `(class order, path, id)` tuple this line always used, which is what makes
    # `aw next` byte-identical to the pre-rename `aw attention`.
    if _post_cutover_history_applies(repo_root):
        with _meta.scan_once(), _meta.ephemeral_if_uninitialized():
            items = [
                _with_post_cutover_history(it, state_by_rel.get(it.path), ctx)
                for it in items
            ]

    items = sort_items(items)
    drift.sort(key=lambda d: (d.location, d.rule))
    return items, drift


# --------------------------------------------------------------------------------------
# Ordering (worksequence i6015i, E-04 .. E-08)
# --------------------------------------------------------------------------------------

# The filename grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>`, from which `-o set` and `-o order` read.
#
# `set` and `order` are legitimately PARTIAL keys: a name that does not match sorts as ABSENT rather
# than raising. The non-matching population is the RESEARCH corpus, whose grammar is the shared
# clustered CORE followed by its own `.<model>.<kind>.md` facets (see `research_contract.parse_name`),
# plus genuinely grandfathered pre-cutover names.
#
# THE COMMENT THAT USED TO SIT HERE WAS WRONG ABOUT WHY, and attcor `rkn8ya` E-08 corrects it rather
# than preserving a misleading attribution. It blamed all 156 non-matching names on "grandfathered
# pre-cutover names"; re-measured on this tree, 103 of them were FULLY CONFORMANT modern names that
# this module's own regex rejected because it spelled the set id `[A-Za-z0-9]+`, excluding the HYPHEN
# that `artifact_naming.build_clustered_name` PRODUCES (it kebab-cases the set id) and that
# `artifact_naming._CLUSTERED_RE` accepts. Those 103 (88 plans, 15 backlog) all sorted as absent under
# `-o set` and `-o order`, so the defect was a second private copy of a shared grammar, not history.
#
# THE FIX IS DELEGATION to `artifact_naming`, the SINGLE naming authority, so a third copy of the
# grammar cannot drift from it again. NO REGEX IS WRITTEN IN THIS MODULE: the full-name reading uses
# `parse_clustered`, and the prefix reading uses `parse_clustered_prefix`, which is DEFINED IN THE
# AUTHORITY for this purpose. A prefix reading is needed at all because `parse_clustered` anchors at
# the tail with a CLOSED facet enum and therefore rejects a research name like
# `...-<id6>-<slug>.gpt5.survey.md` whose PREFIX is nonetheless perfectly parseable. (Re-encoding that
# prefix here would have re-created the very duplication this item removes, which
# `tests/test_naming_authority_single_source.py` (deleted in `19313eed`; no live guard currently
# asserts this structural property) formerly refused.)
#
# MEASURED AFTER THE FIX on this tree: 0 disagreements with `parse_clustered` across all 1148
# clustered-conformant items, and 127 items that previously sorted as absent now sort under their true
# set, with 0 items losing a key they previously had.

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
_RUN_SORT_RANK = {
    name: i
    for i, name in enumerate(
        getattr(
            A,
            "RUN_SORT_ORDER",
            (
                "running",
                "merge-retry",
                "interrupted",
                "merge-unchecked",
                "queued",
                "reviewed",
                "approved",
                "executed",
                "already-landed",
                "fail-gate",
                "fail-depend",
                "fail-lane",
                "fail-begin",
                "fail-merge",
                "fail-verify",
                "failed",
                "not-run",
                "retired",
            ),
        )
    )
}

# The sentinel for "this item has no value for the selected key". Sorting is done on a
# `(absent_flag, value, default_tail...)` tuple, where `absent_flag` is 1 for a missing value, so
# absent items land LAST under EVERY key without their value ever being compared (which also avoids
# comparing None with str on Python 3).
_ABSENT = 1
_PRESENT = 0


def _name_grammar_fields(path: str) -> Tuple[Optional[str], Optional[int]]:
    """(set_id, order) parsed from an artifact's FILENAME, or (None, None) when it does not match.

    DELEGATES to the single naming authority first (`artifact_naming.parse_clustered`), so `-o set`
    and `-o order` can never again disagree with the grammar that BUILDS these names (attcor
    `rkn8ya` E-08). Falls back to the authority's clustered PREFIX only for a name whose tail the
    authority's closed facet enum rejects but whose prefix is well-formed, which is the research
    corpus's `.<model>.<kind>.md` shape.
    """

    name = path.rsplit("/", 1)[-1]
    m = _naming.parse_clustered(name)
    if m is not None:
        try:
            return m.group("set"), int(m.group("nn"))
        except ValueError:  # pragma: no cover - the grammar already pins two digits
            return m.group("set"), None
    m = _naming.parse_clustered_prefix(name)
    if m is None:
        return None, None
    try:
        return m.group("set"), int(m.group("nn"))
    except ValueError:  # pragma: no cover - the grammar already pins two digits
        return m.group("set"), None


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
    run_map: Optional[Dict[str, str]] = None,
) -> Tuple:
    """The PRIMARY sort component for one item under ``order_by``.

    Every branch returns ``(absent_flag, value)`` where ``absent_flag`` is `_ABSENT` for an item that
    carries no value for this key, which is what places it LAST (maintainer ruling: absent is never
    hidden and never defaulted, matching the `xprio` ruling that an absent Priority renders as
    UNPRIORITIZED rather than being defaulted to `medium`). Values are made directly comparable
    (ints/strs, never None), so no branch can raise a TypeError on a mixed comparison.
    """
    if order_by in ("runs", "run"):
        st = _item_run_status(it, run_map)
        if st and st != "-":
            rank = _RUN_SORT_RANK.get(st.lower())
            if rank is not None:
                return (_PRESENT, rank)
            return (_PRESENT, len(_RUN_SORT_RANK))
        return (_ABSENT, len(_RUN_SORT_RANK))
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
        #
        # attcor `rkn8ya` E-09: `"-"` means ABSENT, not "gated on a release named '-'". A bare
        # truthiness test sorted the literal string as PRESENT, and `-` (0x2D) collates below every
        # alphanumeric, so an item DECLARING ITSELF A NON-BLOCKER sorted ABOVE every real blocker.
        # This aligns the one reader of four that omitted the guard: `matches_blocking`,
        # `release_blockers`, `_resolve_release_version` and the render-time flag all exclude `"-"`.
        #
        # LATENT, recorded so nobody over-claims the impact: the `artifact_meta` writer
        # (`artifact_meta.append_legacy`) REMOVES the line for value `-`, and 0 artifacts in this
        # tree carry `Blocks-Release: -`, so only a hand-edit produces the condition. It is a
        # consistency fix, not an observed outage.
        blk = it.blocks_release
        return (_PRESENT, blk) if (blk and blk != "-") else (_ABSENT, "")
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
    run_map: Optional[Dict[str, str]] = None,
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
    ordered, _notices = sort_items_with_notices(
        items, order_by, repo_root=repo_root, run_map=run_map
    )
    return ordered


def sort_items_with_notices(
    items: Sequence[Item],
    order_by: str = A.ORDER_CLASS,
    repo_root: Optional[Path] = None,
    run_map: Optional[Dict[str, str]] = None,
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

    if any(k in ("runs", "run") for k in keys) and run_map is None:
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
        run_map = get_active_runs_map(repo_root) if repo_root else {}

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
            tuple(_order_key(it, k, depths, repo_root, run_map) for k in keys),
            A.ATTENTION_CLASS_ORDER.index(it.attention_class),
            it.path,
            it.id,
        )

    return sorted(items, key=key), notices


def _reclassify_stale_research(repo_root: Path, items: List[Item]) -> List[Item]:
    """Return ``items`` with STALE research ``todo`` rows moved from READY to PARKED,
    and statusless prompts classified by derived pipeline position (or DONE if absent).

    Shelf status outranks position: prompts with reference/archive keep their class.
    """

    research_items = [it for it in items if it.tree == "research"]
    if not research_items:
        return items
    needs_reclass = any(
        (it.native_status == "todo" and it.attention_class == A.READY)
        or (not it.native_status)
        for it in research_items
    )
    if not needs_reclass:
        return items

    try:
        from agent_workflows import research_index as _ridx

        research_root = research_contract.resolve_research_root(repo_root)
        entries, _drift = _ridx._scan_docs(research_root)
        positions = _ridx.derive_pipeline_positions(entries)
        run_sets = _ridx.run_prompt_set_ids(entries)
        by_id = {e.id6: e for e in entries}
        # Only scan executed plans/specs/backlog for research citations when at least one
        # ready `todo` research doc is not already covered by `run_sets`.
        candidate_todo_ids = {
            it.id
            for it in research_items
            if it.native_status == "todo"
            and it.attention_class == A.READY
            and it.id in by_id
            and by_id[it.id].set_id not in run_sets
        }
        cited_exec = (
            _ridx.cited_by_executed_ids(
                repo_root, research_root, candidate_ids=candidate_todo_ids
            )
            if candidate_todo_ids
            else set()
        )
    except Exception:
        return items

    out: List[Item] = []
    for it in items:
        if it.tree != "research":
            out.append(it)
            continue

        # 1. Statusless prompts: classified by pipeline position (shelf outranks position)
        if not it.native_status:
            entry = by_id.get(it.id)
            if (
                entry is not None
                and entry.kind == "research-prompt"
                and not entry.status
            ):
                pos = positions.get(entry.set_id)
                if pos in A._PROMPT_PIPELINE_MAP:
                    cls = A._PROMPT_PIPELINE_MAP[pos]
                else:
                    # Statusless prompt whose set has NO position (provenance/absent) -> DONE
                    cls = A.DONE
                out.append(it._replace(attention_class=cls))
                continue

        # 2. Todo answer docs: stale if set is RUN or cited by executed artifact -> PARKED
        if it.native_status == "todo" and it.attention_class == A.READY:
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
    tree: str,
    rel: str,
    path: Path,
    text: str,
) -> Tuple[Optional[Item], List[core.Drift]]:
    meta_pair = _ACTIVE_META_CTX.get()
    state, project_context = meta_pair if meta_pair is not None else (None, None)
    if tree == "specs":
        return _spec_record(
            rel, path, text, state=state, project_context=project_context
        )
    if tree == "plans":
        return _plans_record(
            rel, path, text, state=state, project_context=project_context
        )
    if tree == "research":
        return _research_record(
            rel, path, text, state=state, project_context=project_context
        )
    if tree == "backlog":
        return _backlog_record(
            rel, path, text, state=state, project_context=project_context
        )
    if tree == "releases":
        return _release_record(
            rel, path, text, state=state, project_context=project_context
        )
    if tree == "prompts":
        return _prompts_record(
            rel, path, text, state=state, project_context=project_context
        )
    return None, []


def item_for_path(path: Path, repo_root: Optional[Path] = None) -> Optional[Item]:
    """Build an Item for a single artifact file path via `artifact_meta`."""
    if repo_root is None:
        try:
            from agent_workflows.project_context import resolve_verb_repo_root

            repo_root = resolve_verb_repo_root(None)
        except Exception:
            repo_root = Path(".")
    rel = _rel_posix(repo_root, path)
    pol = _classify_tree(rel)
    if pol is None or not pol.tracked:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    from agent_workflows import artifact_meta as _meta

    meta_type = _TREE_TO_META_TYPE.get(pol.name, "ipd")
    ctx = _meta.legacy_context(repo_root)
    records_root = Path(ctx.logical_roots["records"])
    scan_repo = _meta._scan_repo_root(ctx, records_root)

    state = None
    with _meta.scan_once(), _meta.ephemeral_if_uninitialized():
        try:
            qres = _meta.query(type=meta_type, project_context=ctx, include_fields=True)
            for st in qres:
                if not st.path:
                    continue
                if (
                    _rel_posix(
                        repo_root, _meta.source_path(st.path, records_root, scan_repo)
                    )
                    == rel
                ):
                    state = st
                    break
        except Exception:
            state = None
        if state is None:
            state = _meta.read_text(text, record_type=meta_type)
        tok = _ACTIVE_META_CTX.set((state, ctx))
        try:
            rec, _ = _record_for(pol.name, rel, path, text)
        finally:
            _ACTIVE_META_CTX.reset(tok)
    if rec is not None:
        if rec.tree == "research":
            reclassed = _reclassify_stale_research(repo_root, [rec])
            if reclassed:
                rec = reclassed[0]
        deps = _extract_item_dependencies(text, state=state)
        if deps is not None:
            rec = rec._replace(item_dependencies=deps)
        if _post_cutover_history_applies(repo_root):
            with _meta.scan_once(), _meta.ephemeral_if_uninitialized():
                rec = _with_post_cutover_history(rec, state, ctx)
    return rec


def format_plan_detail_line(
    plan_path: Path, term: Optional[T.Term] = None
) -> Optional[str]:
    """Format the detail line for a plan identically to `aw att -d`."""
    try:
        text = plan_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    from agent_workflows import artifact_meta as _meta

    st = _meta.read_text(text, record_type="ipd")
    d_kind, d_text = _detail_from_state(st, text)
    if not d_text:
        return None
    safe_text = _safe_detail(d_text)
    tag = d_kind or "summary"
    if term is not None and getattr(term, "color", False):
        tag_txt = term.color256(f"{tag}:", 244)
        detail_txt = term.color256(safe_text, 250)
        return f"      {tag_txt} {detail_txt}"
    return f"      {tag}: {safe_text}"


_PROMPTS_DIR_PREFIXES = (".aw/records/prompts/", ".agents/prompts/")


def _prompt_disposition_from_rel(rel: str) -> str:
    """The prompt's lifecycle DISPOSITION (``pending``/``executed``/...) from its repo-relative path.

    Recognizes both modern `.aw/records/prompts/<disp>/...` and legacy `.agents/prompts/<disp>/...`.
    Returns `""` when the path names no disposition directory.
    Takes the first component under the prompts dir (sharding-safe).
    """
    norm = rel.replace("\\", "/")
    for prefix in _PROMPTS_DIR_PREFIXES:
        if norm.startswith(prefix):
            tail = norm[len(prefix) :]
            return tail.split("/", 1)[0] if "/" in tail else ""
    return ""


def _prompts_record(
    rel: str,
    path: Path,
    text: str,
    *,
    state: Any = None,
    project_context: Any = None,
) -> Tuple[Optional[Item], List[core.Drift]]:
    """Attention record for a staged prompt (plan dx0u4s). Reads id and history from `artifact_meta`."""
    drift: List[core.Drift] = []
    disp = _prompt_disposition_from_rel(rel)
    if not disp:
        drift.append(
            core.Drift(
                rel, "attention.missing-status", "prompt has no bucket directory"
            )
        )
        return None, drift
    status = "executed" if disp == "done" else disp
    try:
        cls = A.class_of("prompts", status)
    except A.UnknownNativeStatus:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                f"prompt disposition {disp!r}",
            )
        )
        return None, drift
    if state is None:
        from agent_workflows import artifact_meta as _meta

        state = _meta.read_text(text, record_type="prompt")
    id6 = "" if getattr(state, "id_derived", False) else (state.id6 or "")
    lha = _last_history_at_for_state(state, project_context=project_context)
    d_kind, d_text = _detail_from_state(state, text)
    oqs, rqs = count_question_stats(text)
    return Item(
        id6,
        rel,
        "prompts",
        status,
        cls,
        None,
        lha,
        detail_kind=d_kind,
        detail_text=d_text,
        oqs=oqs,
        rqs=rqs,
    ), drift


def _release_record(
    rel: str,
    path: Path,
    text: str,
    *,
    state: Any = None,
    project_context: Any = None,
) -> Tuple[Optional[Item], List[core.Drift]]:
    """Attention record for a release record (ship-gate anchor, awrelease). Reads cached fields via `artifact_meta`."""
    if state is None:
        from agent_workflows import artifact_meta as _meta

        state = _meta.read_text(text, record_type="release")
    drift: List[core.Drift] = []
    raw_status = (
        state.legacy_raw_status if state.legacy_raw_status is not None else state.status
    )
    status = (
        raw_status.strip()
        if (raw_status is not None and len(str(raw_status).split()) == 1)
        else None
    )
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
                f"release status {status!r}",
            )
        )
        return None, drift
    rid = "" if getattr(state, "id_derived", False) else (state.id6 or "")
    lha = _last_history_at_for_state(state, project_context=project_context)
    d_kind, d_text = _detail_from_state(state, text)
    oqs, rqs = count_question_stats(text)
    return Item(
        rid,
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
    rel: str,
    path: Path,
    text: str,
    *,
    state: Any = None,
    project_context: Any = None,
) -> Tuple[Optional[Item], List[core.Drift]]:
    if state is None:
        from agent_workflows import artifact_meta as _meta

        state = _meta.read_text(text, record_type="spec")
    is_log_backed = False
    if project_context is not None:
        if getattr(state, "id6", None) and not getattr(state, "id_derived", False):
            from agent_workflows import artifact_meta as _meta

            records_root = Path(project_context.logical_roots["records"])
            is_log_backed = _meta._storage_format(records_root, state) == "log"
    else:
        is_log_backed = bool(
            getattr(state, "created_at", None) or getattr(state, "updated_at", None)
        )
    lha = _last_history_at_for_state(state, project_context=project_context)
    if is_log_backed:
        drift = specs_mod.validate_spec_state(path, state, has_history=bool(lha))
    else:
        drift = specs_mod.validate_spec(path, text)
    raw_status = (
        state.status
        if is_log_backed
        else (
            state.legacy_raw_status
            if state.legacy_raw_status is not None
            else state.status
        )
    )
    status = (
        str(raw_status).strip()
        if (raw_status is not None and len(str(raw_status).split()) == 1)
        else None
    )
    if status is None or status not in A.SPEC_STATUSES:
        return (
            None,
            drift,
        )  # violations already recorded by validate_spec / validate_spec_state
    kind = state.fields.get("gate_kind") or None
    ref = state.fields.get("gate_ref") or None
    summary = state.fields.get("gate_summary") or None
    gate = None
    if status == "deferred" and kind and ref:
        gate = {"kind": kind, "ref": ref}
        if summary:
            gate["summary"] = summary
    br_val = state.fields.get("blocks_release")
    br = str(br_val).strip() if br_val not in (None, "") else None
    pr_val = state.fields.get("priority")
    pr = str(pr_val).strip().split()[0] if pr_val and str(pr_val).strip() else None
    d_kind, d_text = _detail_from_state(state, text)
    rd = _readiness_from_state(state, text)
    oqs, rqs = count_question_stats(text)
    sid = "" if getattr(state, "id_derived", False) else (state.id6 or "")
    return Item(
        sid,
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


_PLANS_DIR_PREFIXES = (".aw/records/plans/", ".agents/plans/")


def _plan_disposition_from_rel(rel: str) -> str:
    """The plan's lifecycle DISPOSITION (``executed``/``superseded``/...) from its repo-relative path.

    attcor `rkn8ya` E-05. Recognizes BOTH layouts: the modern `.aw/records/plans/<disp>/...` and the
    legacy `.agents/plans/<disp>/...`. Returns ``""`` when the path names no disposition directory
    (a plan sitting directly in the plans dir, or a path under neither prefix).

    THE FIRST COMPONENT UNDER THE PLANS DIR, deliberately, NOT the parent directory name: `aw archive
    plans` shards a terminal plan into ``<disposition>/YYYYMM/``, so a `parent.name` test would read
    ``202609`` and silently stop recognizing every sharded plan. This is the derivation
    `check_engine._plan_disposition` and `plans_index.scan_plans` already use, reused rather than
    invented a third time.
    """

    norm = rel.replace("\\", "/")
    for prefix in _PLANS_DIR_PREFIXES:
        if norm.startswith(prefix):
            tail = norm[len(prefix) :]
            return tail.split("/", 1)[0] if "/" in tail else ""
    return ""


def _plans_record(
    rel: str,
    path: Path,
    text: str,
    *,
    state: Any = None,
    project_context: Any = None,
) -> Tuple[Optional[Item], List[core.Drift]]:
    if state is None:
        from agent_workflows import artifact_meta as _meta

        state = _meta.read_text(text, record_type="ipd")
    drift: List[core.Drift] = []
    raw_status = (
        state.legacy_raw_status if state.legacy_raw_status is not None else state.status
    )
    if raw_status is None:
        raw_status = getattr(state, "loose_status", None)
    if raw_status and str(raw_status).strip():
        status = plans_mod.normalize_status(str(raw_status).strip().split()[0])
    else:
        status = None
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no plan Status"))
        return None, drift
    if status not in plans_mod.RECOGNIZED:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                f"plan status {status!r}",
            )
        )
        return None, drift
    disp = _plan_disposition_from_rel(rel)
    if (
        disp in plans_mod.DIR_TERMINAL
        and plans_mod.DIR_TERMINAL[disp] != status
        and status in plans_mod.TERMINAL
    ):
        drift.append(
            core.Drift(
                rel,
                "attention.disposition-mismatch",
                f"dir {disp} vs status {status}",
            )
        )
    pid = (
        ""
        if getattr(state, "id_derived", False)
        else (state.id6 or getattr(state, "loose_id", None) or "")
    )
    lha = _last_history_at_for_state(state, project_context=project_context)
    br_raw = state.fields.get("blocks_release") or getattr(
        state, "loose_blocks_release", None
    )
    br = str(br_raw).strip() if br_raw not in (None, "") else None
    pr_val = state.fields.get("priority")
    pr = str(pr_val).strip().split()[0] if pr_val and str(pr_val).strip() else None
    d_kind, d_text = _detail_from_state(state, text)
    rd = _readiness_from_state(state, text)
    oqs, rqs = count_question_stats(text)
    exec_prog, valid_prog = _extract_checklist_progress(text)
    return Item(
        pid,
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
    rel: str,
    path: Path,
    text: str,
    *,
    state: Any = None,
    project_context: Any = None,
) -> Tuple[Optional[Item], List[core.Drift]]:
    from agent_workflows import artifact_meta as _meta

    if state is None:
        state = _meta.read_text(text, record_type="research")
    drift: List[core.Drift] = []
    is_log = bool(
        getattr(state, "created_at", None) or getattr(state, "updated_at", None)
    )
    has_yaml = is_log or (
        text.startswith("---") and bool(_meta.front_matter_mapping(text))
    )
    if not has_yaml:
        drift.append(
            core.Drift(
                rel, "attention.missing-status", "no research frontmatter status"
            )
        )
        return None, drift

    is_prompt = state.fields.get("research_kind") == "research-prompt"
    raw_status = (
        state.legacy_raw_status if state.legacy_raw_status is not None else state.status
    )

    if raw_status in (None, ""):
        if is_prompt:
            # Two-axis research: prompts carry no hot status. Native status is empty,
            # and initial class is READY (reclassified by pipeline position in post-scan).
            status = ""
            cls = A.READY
        else:
            drift.append(
                core.Drift(
                    rel, "attention.missing-status", "no research frontmatter status"
                )
            )
            return None, drift
    else:
        raw_status_str = str(raw_status)
        norm = research_contract.normalize_status(raw_status_str)
        if not norm.ok:
            drift.append(
                core.Drift(
                    rel,
                    "attention.unknown-status",
                    f"research status {raw_status_str!r}",
                )
            )
            return None, drift
        status = norm.value or raw_status_str
        cls = A.class_of("research", status)

    rid = "" if getattr(state, "id_derived", False) else (state.id6 or "")
    lha = _last_history_at_for_state(state, project_context=project_context)
    pr_val = state.fields.get("priority")
    pr = str(pr_val).strip() if pr_val not in (None, "") else None
    br_val = state.fields.get("blocks_release")
    br = str(br_val).strip() if br_val not in (None, "") else None
    d_kind, d_text = _detail_from_state(state, text)
    rd = _readiness_from_state(state, text)
    oqs, rqs = count_question_stats(text)
    return Item(
        rid,
        rel,
        "research",
        status,
        cls,
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
    rel: str,
    path: Path,
    text: str,
    *,
    state: Any = None,
    project_context: Any = None,
) -> Tuple[Optional[Item], List[core.Drift]]:
    """Attention record for a backlog item. Reads cached fields via `artifact_meta`."""

    from agent_workflows import backlog as backlog_mod

    if state is None:
        from agent_workflows import artifact_meta as _meta

        state = _meta.read_text(text, record_type="backlog")
    drift: List[core.Drift] = []
    raw_status = (
        state.legacy_raw_status if state.legacy_raw_status is not None else state.status
    )
    status = (
        str(raw_status).strip()
        if (raw_status is not None and len(str(raw_status).split()) == 1)
        else None
    )
    if status is None:
        drift.append(core.Drift(rel, "attention.missing-status", "no backlog Status"))
        return None, drift
    if status not in backlog_mod.STATUSES:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                f"backlog status {status!r}",
            )
        )
        return None, drift
    gate = None
    g_kind = state.fields.get("gate_kind") or None
    g_ref = state.fields.get("gate_ref") or None
    if status == "blocked" and g_kind and g_ref:
        gate = {"kind": g_kind, "ref": g_ref}
    lha = _last_history_at_for_state(state, project_context=project_context)
    d_kind, d_text = _detail_from_state(state, text)
    rd = _readiness_from_state(state, text)
    oqs, rqs = count_question_stats(text)
    bid = "" if getattr(state, "id_derived", False) else (state.id6 or "")
    pr_val = state.fields.get("priority")
    pr = str(pr_val).strip() if pr_val not in (None, "") else None
    br_val = state.fields.get("blocks_release")
    br = str(br_val).strip() if br_val not in (None, "") else None
    return Item(
        bid,
        rel,
        "backlog",
        status,
        A.class_of("backlog", status),
        gate,
        lha,
        priority=pr,
        blocks_release=br,
        detail_kind=d_kind,
        detail_text=d_text,
        readiness=rd,
        oqs=oqs,
        rqs=rqs,
    ), drift


# --------------------------------------------------------------------------------------
# Stranded lanes (lanestrand-01 `pr5b0t` E-04/E-05/E-06)
# --------------------------------------------------------------------------------------
#
# THE ONE CROSS-TREE VIEW COULD NOT SEE UNINTEGRATED WORK. Measured before this landed: `aw attention
# --check` exited 0 while dozens of `aw/lane/*` branches held commits that had never reached main, and
# plan `03ie04` was paid for TWICE ($16.59 then $32.83) because the first lane stranded silently.
#
# THE VERDICT COMES FROM THE RUN RECORD, NEVER FROM A FILESYSTEM WALK, and `SCAN_ROOTS` is deliberately
# UNCHANGED. `.aw/worktrees` and `.aw/records/runs` stay outside the scan set: a verdict derived from
# today's filesystem reports a RECOVERED run clean and rewrites history, which is what `xtklpd`'s
# review measured. So lanes join at RENDER time from the run records, not as scanned files.
#
# THE PREDICATE IS NOT DEFINED HERE. `runner_shared.classify_lane_integration` owns it (one reader; see
# its docstring for why `holds_work` alone cannot answer "did it land"), and this module only renders
# and gates on the result.

#: The stable rule id for a stranded lane, in the house `location<TAB>rule<TAB>detail` form (spec F4).
#: STABLE because tests and agent remediation key on it.
LANE_STRANDED_RULE = "attention.lane-stranded"

#: The stable rule id for a lane whose landing question could not be answered. Separate from the
#: stranded rule so a consumer can tell "provably unintegrated" from "unprovable", which are different
#: human actions even though both fail the gate.
LANE_UNKNOWN_RULE = "attention.lane-unknown"

#: The stable rule id for a SUPERSEDED lane: its own commits never landed, but its plan reached a
#: terminal directory, so a later attempt redid the work. SEPARATE from the stranded rule because the
#: operator action differs ("prune this husk" vs "recover this work"), and because a consumer keying on
#: `attention.lane-stranded` must not start matching lanes that hold nothing at risk. Graded `info` by
#: `lane_drift_severity`, so it reports without failing `--check`.
LANE_SUPERSEDED_RULE = "attention.lane-superseded"


def lane_drift_severity(lane_state: str) -> str:
    """The `Drift` severity for a lane state. STRANDED and UNKNOWN FAIL the gate; SUPERSEDED does not.

    FAIL CLOSED, on `nuanaw` ask 3 and on the spec's G3. `artifact_core.drift_exit_code` exempts
    exactly `info`, so an `info` severity would report the lane and still exit 0, which is the
    self-contradiction (`valid: true` beside lost work) this whole surface exists to remove. UNKNOWN
    fails too rather than warning: a landing question we cannot answer is not evidence the work landed.

    SUPERSEDED IS THE ONE EXEMPTION, AND IT IS NOT A WEAKENING. It means the lane's own commits did not
    reach the target AND its plan has since reached a terminal lifecycle directory, so the work was
    redone by a later attempt and landed another way (see `runner_shared.LANE_SUPERSEDED` for the
    measurement: ten such lanes on 2026-09-22, all with live, tested deliverables on `main`). Nothing
    is at risk, so failing the gate on it would assert a loss that did not happen.
    THE REASON THIS MATTERS RATHER THAN BEING COSMETIC: those ten held the board at `VIEW INVALID`
    indefinitely, and a gate that reds forever on landed work is precisely what teaches an operator to
    stop reading it - the failure mode that lets the NEXT real stranding through. It stays REPORTED at
    `info` (the lane still exists and should still be pruned), so this trades a false failure for a true
    notice and never hides a lane.
    ONLY AN EXPLICIT SUPERSEDED VERDICT QUALIFIES. `classify_lane_integration` sets it only when the
    plan is PROVABLY in a terminal directory; an unresolvable plan leaves the state STRANDED, so an
    unreadable record can never buy a lane an exemption.
    """
    if lane_state == rs_lane_superseded():
        return "info"
    return "error"


def rs_lane_superseded() -> str:
    """The `SUPERSEDED` lane-state token, read from its owner rather than re-spelled here.

    ONE DEFINITION. `runner_shared` owns the lane-state vocabulary and this module only renders and
    gates on it, so the literal lives there; a copy here is the F-4 drift class this repository has
    already paid for (a renderer reading one spelling while the producer writes another). Imported
    lazily for the reason every `runner_shared` reference in this module is lazy: `attention` must stay
    importable without pulling the runner in.
    """

    try:
        from agent_workflows import runner_shared as rs

        return str(rs.LANE_SUPERSEDED)
    except (
        Exception
    ):  # pragma: no cover - defensive; an unimportable runner cannot grant an exemption
        # FAIL CLOSED: returning a token nothing matches means every lane keeps `error`, which is the
        # pre-existing behavior rather than a silent exemption.
        return "\x00-unavailable"


def stranded_lane_drift(repo_root: Path) -> List[core.Drift]:
    """Every stranded (or unprovable) lane, as `Drift` records. Read-only; never touches git state.

    WHY A `Drift` AND NOT AN `Item`, which is the whole implementation question for E-05/E-06 and is
    settled by MEASUREMENT rather than taste. `render_json` computes `valid` as `len(drift) == 0`, and
    every `--check` exit path returns `core.drift_exit_code(drift)`. So emitting a stranded lane as a
    non-`info` `Drift` makes the payload's honesty and the gate's exit code follow AUTOMATICALLY and by
    the SAME mechanism, with no second definition of validity; an `Item`-only design would leave
    `valid: true` and `--check` at 0 beside a stranded lane.

    NO ABSOLUTE PATH REACHES EITHER SURFACE. `location` is the lane BRANCH (a git ref such as
    `aw/lane/03ie04`, safe by construction) and the worktree is rendered repository-relative through
    `runner_shared.lane_worktree_display`, which returns None rather than an absolute path. The
    recorded `preserved_worktree` is an absolute home path in most run items, and `integration_detail`
    embeds an absolute repository path, so NEITHER is printed. A worktree omitted from display has
    three distinct causes (never recorded, absent from disk, or existing outside the repository); only
    the provably absent case reports an explicit 'no worktree remains' marker, while the other two
    remain omitted.

    Returns `[]` on any failure to read the run records, which is the honest answer for a repository
    that has never run a driver: absence of run records is not evidence of a stranded lane.
    """
    try:
        from agent_workflows import run_viewer
        from agent_workflows import runner_shared as rs
    except Exception:
        return []

    target_root = _resolve_runs_repo_root(repo_root)
    try:
        run_dirs = run_viewer.discover_run_dirs(target_root)
    except Exception:
        return []
    if not run_dirs:
        return []

    states: List[Dict] = []
    for run_dir in run_dirs:
        state_file = run_dir / "state.json"
        if not state_file.is_file():
            continue
        # A LIVE run's lanes must not fail the gate: a driver in progress legitimately owns them, and a
        # check that reds during every normal run is a check that gets bypassed. The lane classifier
        # ALSO excludes a live-owned lane on `owner_live`, so this is belt and braces on the cheaper
        # signal (`driver.lock` holder liveness, the same one `get_active_runs_map` consumes).
        try:
            if run_viewer.driver_holder_state(run_dir) == run_viewer.HOLDER_LIVE:
                continue
        except Exception:
            continue
        try:
            states.append(json.loads(state_file.read_text(encoding="utf-8")))
        except Exception:
            continue
    if not states:
        return []

    try:
        from agent_workflows import worktree_lease

        with worktree_lease.memoize_worktrees(target_root):
            records = rs.stranded_lane_records(target_root, states)
    except Exception:
        return []

    out: List[core.Drift] = []
    for rec in records:
        branch = str(rec.get("branch") or rec.get("lane_id") or "(unnamed lane)")
        state = str(rec.get("lane_state") or rs.LANE_UNKNOWN)
        if state == rs.LANE_STRANDED:
            rule = LANE_STRANDED_RULE
        elif state == rs.LANE_SUPERSEDED:
            rule = LANE_SUPERSEDED_RULE
        else:
            rule = LANE_UNKNOWN_RULE
        bits = ["{0} lane".format(state)]
        if rec.get("id6"):
            bits.append("plan {0}".format(rec["id6"]))
        if rec.get("commits_ahead"):
            bits.append("{0} commit(s) beyond base".format(rec["commits_ahead"]))
        if rec.get("dirty"):
            bits.append("uncommitted changes")
        if rec.get("integration_signal"):
            bits.append("integration_signal={0}".format(rec["integration_signal"]))
        display = rs.lane_worktree_display(target_root, rec.get("worktree"))
        if display:
            bits.append("worktree {0}".format(display))
        elif rs.lane_worktree_is_absent(target_root, rec.get("worktree")):
            bits.append("no worktree remains")
        if rec.get("run_id"):
            # ONE ROW PER LANE, so the row must say how many runs touched it: the per-branch collapse in
            # `stranded_lane_records` replaced N identical-in-substance rows with one, and dropping the
            # count would lose the fact that the lane recurred rather than merely reformat it.
            try:
                run_count = int(rec.get("run_count") or 1)
            except (TypeError, ValueError):
                run_count = 1
            if run_count > 1:
                bits.append(
                    "newest run {0} of {1} runs".format(rec["run_id"], run_count)
                )
            else:
                bits.append("run {0}".format(rec["run_id"]))
        if state == rs.LANE_SUPERSEDED:
            remedy = "Prune worktree + branch." if display else "Prune branch."
        else:
            remedy = lane_remedy_hint(str(rec["id6"]) if rec.get("id6") else None)
        detail = "{0}: {1}. {2}".format(
            "; ".join(bits),
            rec.get("why") or "",
            remedy,
        )
        out.append(
            core.Drift(
                branch,
                rule,
                A.escape_detail(detail),
                severity=lane_drift_severity(state),
            )
        )
    out.sort(key=lambda d: (d.location, d.rule))
    return out


#: The symbol whose presence PROVES `aw <host> integrate` is really wired, probed by
#: :func:`lane_remedy_hint`. NAMED AS A CONSTANT so the probe is observable: the previous probe was a
#: bare `hasattr` against `cmd_integrate`, a name NOTHING ELSE IN THE REPOSITORY REFERENCES, so when the
#: verb shipped under a different name the conditional froze in its pre-`rl67b0` state and kept printing
#: "no `aw integrate` verb exists yet" for a verb that existed. That UNOBSERVABILITY was the defect, not
#: the wrong string, which is why a test pins this name (plan `0ta5vg` E-06).
LANE_INTEGRATE_PROBE_SYMBOL = "handle_integrate_command"


def lane_remedy_hint(id6: Optional[str] = None) -> str:
    """The remedy to print beside a stranded lane. An alarm with no route trains its own dismissal.

    NAMES ONLY A VERB THAT EXISTS AT RUNTIME, which is the rule that survived unchanged; what changed is
    that the probe now names a symbol that is really there. `rl67b0` shipped the verb as
    `handle_integrate_command` (the CLI forwards `aw oc integrate` as REMAINDER args rather than binding
    a `cmd_*` function), so the old `cmd_integrate` probe could never be True. Do not print a verb that
    does not exist, and do not probe a name nothing else references.

    HOST-NEUTRAL BY DEFAULT: both hosts carry the verb (`oc_runipd` and `agy_runipd` both define
    `handle_integrate_command`), so the hint names `aw oc integrate` as the concrete route rather than
    claiming only one host has it.

    ``id6`` is OPTIONAL so the no-argument call keeps working; when given, the hint names the concrete
    command instead of a `<id6>` placeholder the reader must substitute.
    """
    try:
        from agent_workflows import cli as _cli  # noqa: F401
    except Exception:
        return "Recover it by hand: inspect the branch, then merge it."
    integrate_exists = False
    try:
        from agent_workflows import oc_runipd as _oc

        integrate_exists = hasattr(_oc, LANE_INTEGRATE_PROBE_SYMBOL)
    except Exception:
        integrate_exists = False
    if integrate_exists:
        return "Recover it with `aw oc integrate {0}`.".format(id6 if id6 else "<id6>")
    return (
        "Recover it by hand: `git log main..<branch>` to see the work, then merge that branch "
        "(no `aw integrate` verb exists yet)."
    )


def render_stranded_lane_section(drift: List[core.Drift]) -> str:
    """The LOUD human section for stranded lanes, or `""` when none. One row per lane."""
    from agent_workflows import runner_shared as rs

    lanes = [
        d
        for d in drift
        if d.rule in (LANE_STRANDED_RULE, LANE_UNKNOWN_RULE, LANE_SUPERSEDED_RULE)
    ]
    if not lanes:
        return ""
    # THE HEADER MUST NOT OVER-CLAIM. It used to hardcode `STRANDED ... work that never reached the
    # integration target`, which is FALSE for a SUPERSEDED lane: that lane's work DID reach the target,
    # by a later attempt. So the words follow the states actually present, and the at-risk sentence is
    # printed only when an at-risk state is among them.
    at_risk = [d for d in lanes if d.rule != LANE_SUPERSEDED_RULE]
    if at_risk and len(at_risk) != len(lanes):
        title = "{0} + {1} LANES".format(rs.LANE_STRANDED, rs.LANE_SUPERSEDED)
        gloss = "some hold work that never reached the integration target; superseded ones were redone and can be pruned"
    elif at_risk:
        title = "{0} LANES".format(rs.LANE_STRANDED)
        gloss = "work that never reached the integration target"
    else:
        title = "{0} LANES".format(rs.LANE_SUPERSEDED)
        gloss = "redone by a later attempt and already landed; safe to prune, nothing at risk"
    header = "## {0} ({1}): {2}\n".format(title, len(lanes), gloss)
    body = "".join("- {0}: {1}\n".format(d.location, d.detail) for d in lanes)
    return header + body


# --------------------------------------------------------------------------------------
# Renderers (deterministic)
# --------------------------------------------------------------------------------------


def render_json(
    items: List[Item],
    drift: List[core.Drift],
    repo_root: Path | None = None,
    parked_questions: List[Dict[str, Any]] | None = None,
) -> str:
    if parked_questions is None:
        if repo_root is not None:
            pq_map = get_parked_question_counts(repo_root)
            parked_questions = [
                {"run_id": rid, "count": cnt} for rid, cnt in sorted(pq_map.items())
            ]
        else:
            parked_questions = []

    obj = {
        "schema_version": SCHEMA_VERSION,
        "mapping_version": MAPPING_VERSION,
        # THE SAME CONVENTION AS THE EXIT CODE, deliberately. `core.drift_exit_code` exempts exactly
        # `info`, so computing `valid` from the raw LENGTH would report `valid: false` beside an exit 0
        # for an advisory-only run. That is the same payload/gate contradiction this surface exists to
        # remove, pointing the other way. Any non-`info` drift still makes this false.
        "valid": core.drift_exit_code(drift) == 0,
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
                "review_stale": list(it.review_stale),
                **(
                    {"last_history_precision": it.last_history_precision}
                    if it.last_history_precision is not None
                    else {}
                ),
            }
            for it in items
        ],
        "violations": [
            {"location": d.location, "rule": d.rule, "detail": d.detail} for d in drift
        ],
        # lanestrand-01 (`pr5b0t`) E-05: the machine-readable stranded-lane set. APPENDED, never a
        # repurposed key, so an existing consumer parsing this payload is byte-unchanged in every
        # pre-existing field and every pre-existing key keeps its position.
        #
        # DERIVED FROM `drift`, NOT RE-COMPUTED. That is what makes `valid` (computed as
        # `len(drift) == 0` above) unable to contradict this list by construction: a stranded lane is
        # in the payload if and only if it is in the drift set that decided `valid` and decides the
        # `--check` exit code. A second derivation here could disagree, and only one of them would be
        # wrong at a time.
        #
        # `location` is a git BRANCH and never a path, so nothing absolute can reach this payload.
        "stranded_lanes": [
            {"branch": d.location, "rule": d.rule, "detail": d.detail}
            for d in drift
            if d.rule in (LANE_STRANDED_RULE, LANE_UNKNOWN_RULE, LANE_SUPERSEDED_RULE)
        ],
        # qchan-06 (`y1vjzp`) E-05: live runs holding parked questions. APPENDED, never a
        # repurposed key, [] when none.
        "parked_questions": parked_questions if parked_questions is not None else [],
    }
    # canonical: fixed key order (insertion order above), 2-space indent, sorted item keys off, LF, final newline
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


# xterm-256 palette indices for the five ATTENTION CLASSES. This is NOT a lifecycle status table
# and it is deliberately RETAINED (plan `f9t5hz` E-02): its keys are the `A.*` cross-tree attention
# class constants, and spec `uonrjg` Section 3 lists "attention classes" as an explicit NON-GOAL,
# so R10.3's "local `_STATUS_COLOR_256` lifecycle tables MUST be removed" does not reach it. It
# colors the section HEADERS (`## ready (12)`) by class and nothing else.
#
# THE OBVIOUS CHECK ON THIS TABLE IS A TRAP, recorded because an agent reading only the keys draws
# the wrong conclusion. All five `A.*` constants are BARE STRINGS whose values (`'active'`,
# `'ready'`, `'blocked'`, `'done'`, `'parked'`) are ALSO native status words in several trees, so a
# "do the keys look like statuses?" test answers YES for all five and deletes a vocabulary the spec
# protects. Trace the keys to the `A.*` constants, never pattern-match them.
#
# NO LIFECYCLE SITE CONSULTS THIS TABLE ANY MORE (E-02). It used to sit as the second rung of every
# lifecycle fallback chain (`_STATUS_COLOR_256.get(status, _CLASS_COLOR_256.get(cls, 244))`), which
# was invisible while the two palettes agreed and became a silent re-introduction of the class
# palette into lifecycle rendering the moment they diverged - which spec Section 5 makes them do
# (`active` moves to 220, `blocked` to 208, `done` to 46). The shared resolver now owns every
# lifecycle color, and an unrecognized status resolves `unknown` with a diagnostic (R10.4) rather
# than borrowing a class color.
_CLASS_COLOR_256 = {
    A.ACTIVE: 39,  # bright azure
    A.READY: 40,  # green
    A.BLOCKED: 203,  # salmon/red
    A.DONE: 244,  # gray
    A.PARKED: 244,  # gray
}

#: Bold blue for the tree-name SEGMENT OF A PATH. This is the "existing independent convention"
#: spec `uonrjg` Section 11 item 5 exempts, and the exemption is scoped to a PATH: coloring one
#: directory segment inside `.aw/records/backlog/open/x.md` adds no width and identifies the tree
#: within a longer string. It is NOT a licence to color a bare artifact TYPE word in a row, which
#: Section 9.1 says does not inherit lifecycle color and criterion A10 tests for directly; see
#: `_render_item_row` / `_render_table_row`, where the type column is now plain (E-03).
_TREE_COLOR_256 = 33  # bold blue for the tree-name path segment

#: The `lifecycle_style` FAMILY for each attention tree. The names already coincide (both vocabularies
#: use `plans`/`specs`/`backlog`/`research`/`releases`), so this is an explicit identity map rather
#: than a translation: naming it makes the coincidence a CHECKED fact instead of an assumption, and
#: gives a tree that is not a lifecycle family somewhere to be absent from.
_LIFECYCLE_FAMILY_BY_TREE = {
    # The five TRACKED trees (`A.TRACKED_TREES`), i.e. every tree that actually builds an `Item`.
    "plans": LS.FAMILY_PLANS,
    "specs": LS.FAMILY_SPECS,
    "backlog": LS.FAMILY_BACKLOG,
    "research": LS.FAMILY_RESEARCH,
    "releases": LS.FAMILY_RELEASES,
    # Trees `TREE_POLICY` EXCLUDES today, mapped anyway so that if one is ever tracked it resolves
    # through the shared table rather than through this module's unknown branch. `walkthroughs` and
    # `roadmaps` are `lifecycle_style`'s NO-LIFECYCLE families and therefore resolve `none` (`·`),
    # which is the spec Section 6.7 answer and NOT the same thing as `unknown` (R10.4).
    "prompts": LS.FAMILY_PROMPTS,
    "walkthroughs": LS.FAMILY_WALKTHROUGHS,
    "roadmaps": LS.FAMILY_ROADMAPS,
}


def _resolve_item_lifecycle(tree: str, native_status: str) -> LS.Resolved:
    """Resolve one item's lifecycle presentation through the SHARED resolver (spec R10.3).

    THE ONE LIFECYCLE RESOLUTION PATH IN THIS MODULE. Every rendered status word, id6, date, SetID
    and Order number takes its color from the `Resolved` this returns, so Section 9.1's "the glyph,
    id6, and status word use the same lifecycle color and weight" holds by CONSTRUCTION rather than
    by three call sites agreeing on a lookup.

    A TREE THAT IS NOT A LIFECYCLE FAMILY RESOLVES `unknown`, NOT A BORROWED CLASS COLOR. R10.4 makes
    that distinction load-bearing, and `term.resolve_lifecycle` RAISES `UnknownFamily` for a family it
    has no policy for, which would be a crash in a read-only view. So an unmapped tree is translated
    into the `unknown` stage here (`?`, gray 244, plus the resolver's own diagnostic shape) instead of
    propagating: a view that cannot classify a row must say so, not fail.
    """

    family = _LIFECYCLE_FAMILY_BY_TREE.get(tree)
    if family is None:
        return LS.Resolved(
            stage=LS.UNKNOWN,
            style=LS.style_for(LS.UNKNOWN),
            family=tree,
            native_status=native_status or None,
            diagnostic="attention tree {0!r} is not a lifecycle family".format(tree),
        )
    return T.resolve_lifecycle(family, native_status)


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


# READ-SIDE priority aliases, normalized at the PARSE boundary only (attcor `rkn8ya` E-06).
#
# `--priority` carries no argparse `choices`, and `matches_priority` does exact membership, so
# `aw att --priority med` silently returned 0 items instead of erroring: a filter that answers
# "nothing matches" to a typo is worse than one that refuses. `med` is already accepted by
# `PRIORITY_RANK` in this same module and appears in the board's own table docstring, so accepting it
# here REMOVES an internal inconsistency rather than inventing a new vocabulary.
#
# NORMALIZED AT PARSE TIME, DELIBERATELY, so exactly ONE vocabulary survives downstream:
# `attention_contract.PRIORITY_ORDER` stays the single vocabulary and `_PRIORITY_SORT_RANK` stays
# DERIVED from it (the comment at its definition records that a hardcoded second copy is the mistake
# `ipd_schema` already made). Neither is touched.
#
# READ-SIDE ONLY: `aw ipd set` / `aw specs set` / `aw backlog set` keep their argparse `choices`, so
# `med` can never be WRITTEN into an artifact. The alias is a convenience for asking a question, not
# a second spelling of a stored value.
# EXACTLY ONE ENTRY, and no speculative additions: `med` is the alias this module already accepts
# elsewhere (`PRIORITY_RANK`), which is the whole justification for accepting it. Inventing further
# spellings (`hi`, `lo`) would create vocabulary this repository uses nowhere else.
_PRIORITY_FILTER_ALIASES = {"med": "medium"}


def parse_priority_filters(raw_priorities: Sequence[str] | None) -> set[str]:
    """Parse priority filter arguments, normalizing the read-side aliases (e.g. `med` -> `medium`)."""
    tokens = parse_filter_tokens(raw_priorities)
    return {_PRIORITY_FILTER_ALIASES.get(t, t) for t in tokens}


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


_RUN_STATUS_ALIASES = {
    # Canonical runner item statuses (identity mappings so selector_vocabulary and filters see them)
    "running": "running",
    "awaiting-human": "awaiting-human",
    "question": "awaiting-human",
    "queued": "queued",
    "failed": "failed",
    "executed": "executed",
    "approved": "approved",
    "reviewed": "reviewed",
    "already-landed": "already-landed",
    "interrupted": "interrupted",
    "merge-retry": "merge-retry",
    "fail-gate": "fail-gate",
    "fail-begin": "fail-begin",
    "fail-lane": "fail-lane",
    "fail-verify": "fail-verify",
    "fail-depend": "fail-depend",
    "fail-merge": "fail-merge",
    "not-run": "not-run",
    "retired": "retired",
    # Legacy terminal status aliases (spec uonrjg Section 7.2)
    "substantially-complete": "fail-gate",
    "partial": "fail-verify",
    "failed-safely": "fail-gate",
    "blocked": "fail-gate",
    "dependency-blocked": "fail-depend",
    "integration-blocked": "fail-merge",
    "merge-conflict": "fail-merge",
    "merge-needs-human": "fail-merge",
    "merge-refused": "fail-merge",
    "not-attempted": "not-run",
    # Legacy integration status aliases
    "integration-deferred": "merge-retry",
    "integration-unmeasured": "merge-unchecked",
    # Legacy completion synonyms
    "completed": "executed",
    "done": "executed",
}


def parse_run_status_filters(raw_run_statuses: Sequence[str] | None) -> set[str]:
    """Parse run status filter arguments, normalizing hyphens, underscores, and synonyms."""
    tokens = parse_filter_tokens(raw_run_statuses)
    result: set[str] = set()
    for t in tokens:
        result.add(t)
        if "_" in t:
            result.add(t.replace("_", "-"))
        elif "-" in t:
            result.add(t.replace("-", "_"))
        t_norm = t.replace("_", "-")
        if t_norm in _RUN_STATUS_ALIASES:
            result.add(_RUN_STATUS_ALIASES[t_norm])
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


@functools.lru_cache(maxsize=32)
def _get_planned_release_info(repo_root: Optional[Path]) -> Tuple[str, str]:
    if not repo_root:
        return "", ""
    try:
        from agent_workflows import releases as _releases

        desc = _releases.describe_planned_release(repo_root)
        if desc:
            return (desc[0] or "").lower(), (desc[1] or "").lower()
    except (AttributeError, OSError, ValueError):
        pass
    return "", ""


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
    planned_id, planned_ver = _get_planned_release_info(repo_root)

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
                # attcor `rkn8ya` E-04: `next` RESOLVES against the PLANNED release; it used to
                # `return True` unconditionally, so `--blocking next` matched every gated item no
                # matter which release it named (a shipped or a past one included).
                #
                # `next` is the SYMBOL for "the single planned release", which is exactly what
                # `releases.resolve_blocks_release`/`describe_planned_release` mean by it, so the
                # correct predicate is "this item gates the planned release". The reasoning below for
                # a version/id6 token already did this; only the `next` branch bypassed it.
                #
                # WHEN THERE IS NO PLANNED RELEASE, `next` MATCHES NOTHING, and that is the honest
                # answer rather than a behavior-preserving dodge: `next` names a release record that
                # does not exist, so no item can gate it. (`--blocking any` remains the way to ask
                # "gated on anything at all".)
                if not (planned_id or plan_clean):
                    continue
                if raw_blk == "next":
                    return True
                if planned_id and raw_blk == planned_id:
                    return True
                if plan_clean and res_clean == plan_clean:
                    return True
                continue
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


def matches_run_status(
    it: Item, run_status_filters: set[str], run_map: Optional[Dict[str, str]]
) -> bool:
    """Return True if item matches any of the given run status filters."""
    if not run_status_filters:
        return True
    st = _item_run_status(it, run_map)
    st = (st or "").lower()
    has_run = bool(st and st != "-")
    if not has_run:
        return bool(run_status_filters & {"-", "none", "no", "false"})
    if "any" in run_status_filters:
        return True
    candidates = {
        st,
        st.replace("_", "-"),
        st.replace("-", "_"),
    }
    return bool(candidates & run_status_filters)


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
        from agent_workflows.engine import setup_marker_path

        return setup_marker_path(repo_root).is_file()
    except Exception:
        return False


_INBOX_BOOKKEEPING_NAMES = frozenset({"README.md", ".gitkeep"})


def inbox_waiting(repo_root: Path) -> int:
    """awinbox Order 03 (`olmvgw`, recovering `9iiqmm`): how many RAW drops are waiting in `<repo>/.aw/inbox/`.

    Structural twin of `setup_needed` above: DERIVED on demand, read-only, swallows its own
    exceptions, NEVER creates anything (in particular it must not create `.aw/inbox/` by looking
    for it), and feeds one advisory footer nudge that touches neither the item list nor the exit
    code.

    LISTS DIRECTORY ENTRIES ONLY; OPENS NO FILE, EVER. Inbox drops are VISIBLE AS FILES here and
    are NEVER INTERPRETED AS RECORDS, and that distinction is the whole safety property of this
    function rather than a style preference. `.aw/inbox/` holds unvetted third-party text, and
    `selectors._ID_RE` is position-unanchored (`(?m)^- Id:\\s*([0-9a-z]{6})\\s*$` applied with
    `.search()` over a whole body), so a `- Id:` line anywhere in a drop - INCLUDING one merely
    QUOTED inside an external report as an example - is harvested as an identity claim and can
    collide with a real artifact's id6, making that artifact unresolvable to `aw set`/`aw show`
    (see `.aw/.gitignore`, which records exactly this hazard as the reason the inbox sits OUTSIDE
    `.aw/records/`). Listing a directory cannot forge an identity; parsing a drop can. So do NOT
    "improve" this by reading front matter, sniffing a body, or classifying a drop by type: use
    `os.scandir`, which yields names without opening anything.

    A MISSING DIRECTORY MEANS ZERO. `.aw/inbox/` is gitignored and therefore per-checkout, so it
    is simply absent in a fresh worktree; absent must not raise, and the caller must print nothing
    for zero, because a nudge that fires when there is nothing to nudge about is noise that trains
    readers to ignore it.

    ONE ANCHORED PATH, NEVER A SEARCH BY NAME. Resolves exactly `<repo>/.aw/inbox/` and never looks
    for directories called `inbox` anywhere else: `.aw/records/comms/*/inbox/` is the TRACKED
    inter-agent comms lane and is unrelated (an unanchored `inbox/` gitignore pattern once
    threatened exactly that path and would have broken `aw install`).

    A NESTED DIRECTORY COUNTS AS ONE ENTRY AND IS NOT WALKED (OQ-02). The number's job is to be
    nonzero and roughly right, not exact; counting a directory as one entry keeps the whole
    operation a single shallow `scandir` that cannot recurse unboundedly.

    BUT THE TREE'S OWN BOOKKEEPING FILES ARE EXCLUDED (`README.md`, `.gitkeep`), because they are
    not waiting for anyone. `.aw/inbox/README.md` is committed scaffolding that documents the lane
    (`git ls-files .aw/inbox` shows it tracked), so counting it would make this nudge fire FOREVER
    on a fully drained inbox on every machine, defeating the silent-when-empty rule above. Every
    other entry counts, including hidden files and non-`.md` drops: a genuine hidden drop (say
    `.report.md`) must not be missed.
    """
    try:
        inbox = Path(repo_root) / ".aw" / "inbox"
        with os.scandir(inbox) as entries:
            return sum(1 for e in entries if e.name not in _INBOX_BOOKKEEPING_NAMES)
    except Exception:
        return 0


def release_blockers(items: List[Item], repo_root: Path) -> List[Item]:
    """awdoctor Order 02: items carrying a `- Blocks-Release: next|<id6>` field that are still LIVE.
    Reads the field from each item's file (the awrelease Set defines it). Returns the blocking items.

    Both TERMINAL classes are excluded, not just ``DONE``. A retired artifact keeps its
    ``Blocks-Release`` field on purpose, because the field records what the artifact was FOR and
    erasing it would falsify the record; but a superseded plan or a parked backlog item cannot gate a
    release, since nobody is going to do it. Skipping only ``DONE`` counted a plan retired to
    ``superseded/`` as an outstanding blocker, which is how a split plan kept appearing in the
    release-blocker list after its replacements were filed."""
    out: List[Item] = []
    for it in items:
        if it.attention_class in (A.DONE, A.PARKED):
            continue
        if it.blocks_release and it.blocks_release != "-":
            out.append(it)
    return out


_FACET_STRIP_RE = re.compile(r"(\.[a-z0-9-]+)*\.md$")


def _identity_stem(path: str) -> str:
    """awdoctorfix Order 02: the compact, tree-independent identity of a board line's file:
    `YYYYMMDD-<setid>-NN-<id6>` when the basename matches the clustering grammar, else the basename
    with its trailing `.md` / `.<type>.md` facet(s) stripped (e.g. `setup-repo-v1`)."""
    base = path.replace("\\", "/").rsplit("/", 1)[-1]
    parts = _naming.identity_parts(base)
    if parts:
        return "-".join(parts)
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


def _age_marker(
    last_history_at: Optional[str],
    tree: str = "",
    today: Optional[date] = None,
) -> str:
    """awdoctor Order 01 + awdoctorfix Order 03: a compact staleness marker from last_history_at.
    '!' when older than ~30 days, '?' when unknown (None) EXCEPT on a history-less tree (returns ''),
    else '' (recent). Reads the UTC clock per spec 4sd62s Section 4.2b so verdicts are invariant under reader timezone."""
    if last_history_at is None:
        return "" if tree in _HISTORYLESS_TREES else "?"
    try:
        ref_date = today if today is not None else datetime.now(timezone.utc).date()
        y, m, d = (int(x) for x in last_history_at[:10].split("-")[:3])
        age_days = (ref_date - date(y, m, d)).days
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
        # THE SHARED RESOLVER, not a local table (spec `uonrjg` R10.3). The lifecycle marker, the
        # status word and (below) the identity columns all take their color and weight from this ONE
        # `Resolved`, which is what makes Section 9.1's "same lifecycle color and weight" structural.
        resolved = _resolve_item_lifecycle(it.tree, it.native_status)
        marker = term.format_lifecycle_marker(resolved, width=2)
        status_txt = term.style_lifecycle_text(status_word, resolved)
        # PADDED BY VISIBLE COLUMNS (Section 9.4), never by `len()` on styled text.
        status_padded = T.pad_visible(status_txt, 12)
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
            # THE ARTIFACT TYPE CARRIES NO COLOR (criterion A10; Section 9.1 "The artifact type and
            # title do not inherit lifecycle color"). It used to be painted `_TREE_COLOR_256` bold,
            # and Section 11 item 5's "existing independent convention" exemption does NOT stretch to
            # cover it: that convention is for the tree SEGMENT OF A PATH (`_colorize_tree_segment`),
            # and a bare type word in a row is not a path. Coloring it made A10 untestable here.
            type_prefix = type_word + (" " * max(0, 10 - len(type_word))) + "  "
        inline_gate = ""
        if it.gate and not gate_in_header:
            g = it.gate
            ref_txt = _gate_ref_display(
                A.escape_detail(g.get("ref", "")), long=bool(long)
            )
            inline_gate = f"  [gate {g.get('kind')}: {ref_txt}]"
        run_txt = ""
        if runs_mode and run_state and run_state != "-":
            run_resolved = _resolve_run_lifecycle(run_state)
            run_txt = "  " + term.style_lifecycle_text(
                f"[run:{run_state}]", run_resolved
            )
        prio = ""
        if it.priority:
            pcode = {"high": 196, "medium": 214, "low": 244}.get(it.priority, 244)
            prio = "  " + term.color256(f"[{it.priority}]", pcode, bold=True)
        blocking = ""
        if it.blocks_release:
            blocking = "  " + term.color256("[blocking]", 196, bold=True)
        stale_review = ""
        if it.review_stale:
            stale_review = "  " + term.color256("[stale-review]", 214, bold=True)
        # The GLYPH IMMEDIATELY PRECEDES THE STATUS WORD (Section 9.1: "glyph MUST immediately
        # precede either id6 or status so its referent is obvious"), and it is padded by RENDERED
        # width by `format_lifecycle_marker`, so the two glyphs carrying U+FE0E (`⚠︎`, `↩︎`) occupy
        # the same column count as the single-codepoint ones.
        line = f"- {lead}{marker} {status_padded}  {type_prefix}{path_txt}{run_txt}{prio}{blocking}{stale_review}{inline_gate}"
        if details and it.detail_text:
            tag = it.detail_kind or "summary"
            tag_txt = term.color256(f"{tag}:", 244)
            safe_text = _safe_detail(it.detail_text)
            detail_txt = term.color256(safe_text, 250)
            line += f"\n      {tag_txt} {detail_txt}"
        return line
    suffix = ""
    if it.gate:
        g = it.gate
        suffix = f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
    run_sfx = ""
    if runs_mode and run_state and run_state != "-":
        run_sfx = f"  [run: {run_state}]"
    stale_sfx = ""
    if it.review_stale:
        stale_sfx = "  [stale-review]"
    line = f"- [{it.tree}] {it.path} ({status_word}){run_sfx}{stale_sfx}{suffix}"
    if details and it.detail_text:
        tag = it.detail_kind or "summary"
        line += f"\n      {tag}: {_safe_detail(it.detail_text)}"
    return line


@functools.lru_cache(maxsize=256)
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
                version = _releases.parse_release(
                    p, p.read_text(encoding="utf-8")
                ).version
                if version:
                    return version
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


def extract_id6(it: Item) -> Optional[str]:
    """Extract id6 for an item, from it.id or filename."""
    if it.id and it.id != "-":
        return it.id
    _, _, _, id6 = _extract_identity_parts(it)
    if id6 and id6 != "-":
        return id6
    return None


def _extract_identity_parts(it: Item) -> Tuple[str, str, str, str]:
    """Extract (Date, SetID, Num, ID6) from an Item's path and metadata."""
    base = it.path.replace("\\", "/").rsplit("/", 1)[-1]
    # The ONE file-name library reads the identity (maintainer ruling 2026-11-09: no private grammar).
    leg = _naming.legacy_identity_parts(base)
    if leg:
        return leg[0], leg[2], leg[1], it.id or "-"
    parts = _naming.identity_parts(base)
    if parts:
        return parts[0], parts[1], parts[2], it.id or parts[3]
    date = base[:8] if len(base) >= 8 and base[:8].isdigit() else "-"
    raw_stem = _FACET_STRIP_RE.sub("", base)
    set_id = raw_stem if raw_stem else "-"
    num = "-"
    id6 = it.id if it.id else "-"
    return date, set_id, num, id6


def _item_run_status(it: Item, run_map: Optional[Dict[str, str]]) -> Optional[str]:
    """Look up an item's run status in run_map using id, id6 stem, path, or filename."""
    if not run_map:
        return None
    _, _, _, it_id6 = _extract_identity_parts(it)
    for cand in (it.id, it_id6, it.path, Path(it.path).name):
        if cand and cand in run_map:
            return run_map[cand]
    return None


def _color_dep_id(dep: str, target: Optional[Item], term: T.Term, colored: bool) -> str:
    """Color a dependency id6 to match the lifecycle color of its TARGET's status.

    THIS IS A COMPACT id6 REFERENCE (spec Section 9.2): an id6 standing alone, carrying its
    artifact's lifecycle stage, and it takes the SAME treatment the target's own row gives its
    status word, through the shared resolver (R10.3).

    An UNMATCHED dependency stays neutral gray, and that is deliberately NOT the `unknown` stage:
    `unknown` means "this artifact has a lifecycle I could not read", whereas an unmatched id6 means
    no artifact was found at all, so there is no lifecycle to report and painting `?` here would
    claim there is.
    """
    if not colored:
        return dep
    if target is None:
        return term.color256(dep, 244)
    resolved = _resolve_item_lifecycle(target.tree, target.native_status)
    return term.style_lifecycle_text(dep, resolved)


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
    """Resolve the repository root that owns runs (handling git worktrees)."""
    from agent_workflows.runner_shared import state_root

    if state_root(repo_root).is_dir():
        return repo_root
    git_ref = repo_root / ".git"
    if git_ref.is_file():
        try:
            txt = git_ref.read_text(encoding="utf-8").strip()
            if txt.startswith("gitdir:"):
                gdir = Path(txt.split(":", 1)[1].strip()).resolve()
                candidate = gdir.parent.parent.parent
                if state_root(candidate).is_dir() or (candidate / ".git").is_dir():
                    return candidate
        except Exception:
            pass
    if ".aw/worktrees" in str(repo_root.resolve()):
        for parent in repo_root.resolve().parents:
            if state_root(parent).is_dir():
                return parent
    return repo_root


def canonical_run_status(status: Any) -> str:
    """Canonicalize a runner status token through legacy integration and terminal aliases."""
    from agent_workflows import runner_shared as rs

    return rs.canonical_run_status(status)


def _resolve_run_lifecycle(run_state: str | None) -> LS.Resolved:
    """Resolve a runner item status (spec Section 7.2) through the shared lifecycle resolver."""
    token = (run_state or "").strip().lower()
    activity = None
    if token == "merging":
        activity = "merging"
    return T.resolve_lifecycle(LS.FAMILY_RUNNER_ITEM, run_state, activity=activity)


_RUN_PRIORITY_ORDER: Dict[str, int] = {
    "running": 20,
    "awaiting-human": 19,
    "merge-retry": 18,
    "interrupted": 17,
    "merge-unchecked": 16,
    "queued": 15,
    "reviewed": 14,
    "approved": 13,
    "executed": 12,
    "already-landed": 11,
    "fail-gate": 10,
    "fail-depend": 9,
    "fail-lane": 8,
    "fail-begin": 7,
    "fail-merge": 6,
    "fail-verify": 5,
    "failed": 4,
    "not-run": 3,
    "retired": 2,
}


def get_active_runs_map(
    repo_root: Path, *, exclude_run_id: Optional[str] = None
) -> Dict[str, str]:
    """Scan active runner sessions and return a mapping of id6/path to runner state.

    Only live runs (whose driver process currently holds driver.lock) are inspected.
    States are emitted in the runner's canonical item status vocabulary.
    Pass ``exclude_run_id`` to omit a caller's own run directory (for example a
    ``--poll-for-deps`` reservation re-checking dependencies on its next tick).
    """
    from agent_workflows import run_viewer

    run_map: Dict[str, str] = {}
    target_root = _resolve_runs_repo_root(repo_root)
    try:
        runs = run_viewer.discover_run_dirs(target_root)
    except Exception:
        return run_map

    live_runs = [
        r
        for r in runs
        if (exclude_run_id is None or r.name != exclude_run_id)
        and run_viewer.driver_holder_state(r) == run_viewer.HOLDER_LIVE
    ]
    if not live_runs:
        return run_map

    priority_order = _RUN_PRIORITY_ORDER

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

                if raw_st:
                    mapped = canonical_run_status(raw_st) or raw_st
                else:
                    mapped = "-"

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


def get_parked_question_counts(repo_root: Path) -> Dict[str, int]:
    """Scan active runner sessions and return a mapping of run id to parked question count.

    Only live runs (whose driver process currently holds driver.lock) are inspected (spec 6kwd2e R4a.6, qchan-06 y1vjzp E-05).
    Runs with zero parked questions are omitted.
    """
    from agent_workflows import run_viewer
    from agent_workflows import runner_shared

    counts: Dict[str, int] = {}
    target_root = _resolve_runs_repo_root(repo_root)
    try:
        runs = run_viewer.discover_run_dirs(target_root)
    except Exception:
        return counts

    live_runs = [
        r for r in runs if run_viewer.driver_holder_state(r) == run_viewer.HOLDER_LIVE
    ]
    if not live_runs:
        return counts

    for run_dir in live_runs:
        state_file = run_dir / "state.json"
        if not state_file.is_file():
            continue
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            cnt = runner_shared.parked_question_count(state_data)
            if cnt > 0:
                run_id = state_data.get("run_id") or run_dir.name
                counts[str(run_id)] = cnt
        except Exception:
            continue

    return counts


# Status words whose 8-character TRUNCATION collides with another real status, mapped to a distinct
# 8-character abbreviation (attcor `rkn8ya` E-11a).
#
# THE COLLISION: `implementing` and `implemented` both slice to `implemen`, so the table could not
# distinguish ACTIVE work from FINISHED work. Color does distinguish them (`_resolve_item_lifecycle`
# gives them different lifecycle stages), but ONLY on a color TTY: `--no-color` and every piped or
# machine read saw one identical word for two opposite states.
#
# ABBREVIATED RATHER THAN WIDENED, deliberately. The Status column's width is pinned at 8 by the
# header (`"Status".ljust(8)`) and by an exact-line table snapshot test; widening it would shift every
# column in every row. Only the COLLIDING pair is remapped, so `not-exec`, `supersed`, `to-revie`,
# `reviewed`, `approved`, `executed`, `graduate` and every other truncation are byte-unchanged.
# The two abbreviations share the stem `implmnt` and differ in the FINAL LETTER, which carries the
# grammatical distinction the full words carry: `g` for the gerund (implementinG, in progress) and `d`
# for the past participle (implementeD, finished).
_STATUS_ABBREV = {
    "implementing": "implmntg",
    "implemented": "implmntd",
}


def _abbrev_status(native_status: str) -> str:
    """The <=8-character Status-column word for a native status, disambiguating 8-char collisions."""

    st = native_status or ""
    return _STATUS_ABBREV.get(st.lower(), st[:8])


# The readiness word that collides at the column's 9-character width (attcor `rkn8ya` E-11b).
# `go-pending-approval` sliced to `go-pendin`, indistinguishable from a cleared `go` to a reader and
# (before this fix) identically colored. The `?` marks the approval as still OUTSTANDING.
_READINESS_ABBREV = {"go-pending-approval": "go-pend?"}


def _abbrev_readiness(readiness: Optional[str]) -> str:
    """The <=9-character Readiness-column word, disambiguating the 9-char collision. `-` when absent."""

    rd = readiness or "-"
    return _READINESS_ABBREV.get(rd.lower(), rd[:9])


def _render_table_row(
    it: Item,
    term: T.Term,
    colored: bool,
    long: bool,
    details: bool = False,
    repo_root: Optional[Path] = None,
    gate_in_header: bool = False,
    set_w: int = 5,
    num_w: int = 2,
    oq_w: int = 3,
    exec_w: int = 4,
    valid_w: int = 5,
    id_map: Optional[Dict[str, Item]] = None,
    runs_mode: bool = False,
    run_state: Optional[str] = None,
) -> str:
    st_raw = _abbrev_status(it.native_status)
    # ONE resolution per row, from the shared resolver (R10.3). Computed even when `colored` is
    # False so the uncolored path takes the SAME glyph, which keeps the plain table a
    # character-for-character strip of the colored one (a property `test_attention` asserts).
    resolved = _resolve_item_lifecycle(it.tree, it.native_status)
    if colored:
        st_styled = term.style_lifecycle_text(st_raw, resolved)
    else:
        st_styled = st_raw
    # THE GLYPH LIVES INSIDE THE STATUS COLUMN, immediately preceding the status word (Section 9.1:
    # "glyph MUST immediately precede either id6 or status so its referent is obvious"). Folded into
    # the existing column rather than added as a new one so Section 12's "existing column order MUST
    # be preserved" holds literally: the column COUNT and their order are unchanged, and only the
    # Status column's width grows from 8 to 10. `format_lifecycle_marker` pads by RENDERED width, so
    # `⚠︎` (2 code points, 1 column) occupies the same 2 columns as `◕` (1 and 1).
    st_marker = term.format_lifecycle_marker(resolved, width=2, style=colored)
    st_col = st_marker + T.pad_visible(st_styled, 8)

    if runs_mode:
        run_raw = (run_state or "-")[:14]
        if run_raw == "-":
            run_marker = "  "
            if colored:
                run_styled = term.color256("-", 244)
            else:
                run_styled = "-"
        else:
            run_resolved = _resolve_run_lifecycle(run_raw)
            run_marker = term.format_lifecycle_marker(
                run_resolved, width=2, style=colored
            )
            if colored:
                run_styled = term.style_lifecycle_text(run_raw, run_resolved)
            else:
                run_styled = run_raw
        run_col = f"{run_marker}{T.pad_visible(run_styled, 14)}"

    type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
    tp_raw = type_word[:8]
    # THE TYPE COLUMN CARRIES NO COLOR (criterion A10). See `_render_item_row` for the full reasoning:
    # Section 9.1 says the artifact type does not inherit lifecycle color, and Section 11 item 5's
    # "existing independent convention" exemption covers `_TREE_COLOR_256` on a PATH SEGMENT, not a
    # bare type word in a row.
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

    # attcor `rkn8ya` E-11b: the readiness cell, fixed in BOTH its text and its color.
    #
    # TEXT: `go-pending-approval` used to slice to `go-pendin`, which reads as a truncated `go`. It now
    # renders the distinct abbreviation `go-pend?`, whose trailing `?` says an approval is still
    # OUTSTANDING. The width stays 9 so no column moves.
    #
    # COLOR: the old code ran a SUBSTRING test over the 9-char slice (`"go" in lower and "no" not in
    # lower`), so `go-pendin` took 114 - the SAME green as a cleared `go`. An UNAPPROVED plan therefore
    # rendered as approved, which misreports an approval state and is the more serious half of this
    # fix. The colour now comes from the SHARED resolver (`lifecycle_style.resolve_readiness`), which
    # already maps the three readiness words to three DISTINCT stages (`go` -> ready,
    # `go-pending-approval` -> authority-queued, `no-go` -> blocked), so the distinction cannot be
    # re-lost by a heuristic and the readiness cell agrees with every other lifecycle colour in the row.
    rd_raw = _abbrev_readiness(it.readiness)
    if colored:
        if rd_raw != "-":
            rd_styled = term.style_lifecycle_text(
                rd_raw, LS.resolve_readiness(it.readiness)
            )
        else:
            rd_styled = term.color256(rd_raw, 244)
    else:
        rd_styled = rd_raw
    rd_col = T.pad_visible(rd_styled, 9)

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

    date, set_id, num, id6 = _extract_identity_parts(it)

    # THE FOUR IDENTITY COLUMNS TAKE THE SAME `resolved` AS THE STATUS WORD AND THE GLYPH, which is
    # what makes criterion A10's "glyph, id6, and status use the same resolved color and bold flag"
    # true by construction here: all three route through the one `style_lifecycle_text` call shape
    # with the one `Resolved`, so they cannot diverge.
    #
    # DATE, SetID AND N ARE KEPT ON THAT TREATMENT rather than being neutralized with the type column,
    # and the distinction is the spec's own. Section 9.1 and criterion A10 name the artifact TYPE,
    # TITLE and PATH as the cells that must NOT be lifecycle-colored, and these three are none of
    # those: they are FACETS OF THE ARTIFACT'S IDENTITY parsed out of the same filename the id6 comes
    # from (`_extract_identity_parts`), displayed as separate columns only because this table splits
    # the identity. Coloring them with the id6 is the "existing independent convention" Section 11
    # item 5 permits, it is a shipped contract (`tests/test_attention.py` asserts Date, SetID and ID6
    # all carry the status color), and Section 12 requires an existing stable contract be preserved
    # absent a separately reviewed interface change. The `-` sentinel stays neutral gray because an
    # absent facet has no lifecycle to report.
    date_raw = date[:8]
    if colored and date_raw == "-":
        date_styled = term.color256("-", 244)
    elif colored:
        date_styled = term.style_lifecycle_text(date_raw, resolved)
    else:
        date_styled = date_raw
    date_pad = " " * (8 - len(date_raw))
    date_col = f"{date_styled}{date_pad}"

    set_val = it.path if long else set_id
    if colored and long:
        # Under `--long` this column holds the PATH, which A10 says is not lifecycle-colored; the
        # tree SEGMENT keeps its own independent convention (Section 11 item 5).
        set_styled = _colorize_tree_segment(term, it.path, it.tree)
    elif colored and set_val == "-":
        set_styled = term.color256("-", 244)
    elif colored:
        set_styled = term.style_lifecycle_text(set_val, resolved)
    else:
        set_styled = set_val
    set_pad = " " * max(0, set_w - len(set_val))
    set_col = f"{set_styled}{set_pad}"

    num_raw = num[:num_w]
    if colored and num_raw == "-":
        num_styled = term.color256("-", 244)
    elif colored:
        num_styled = term.style_lifecycle_text(num_raw, resolved)
    else:
        num_styled = num_raw
    num_pad = " " * max(0, num_w - len(num_raw))
    num_col = f"{num_styled}{num_pad}"

    id6_raw = id6[:6]
    if colored and id6_raw == "-":
        id6_styled = term.color256("-", 244)
    elif colored:
        id6_styled = term.style_lifecycle_text(id6_raw, resolved)
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

    stale_marker = ""
    if it.review_stale:
        stale_marker = (
            "  " + term.color256("[stale-review]", 214, bold=True)
            if colored
            else "  [stale-review]"
        )

    if runs_mode:
        row_line = (
            f"{st_col} {run_col} {tp_col} {blk_col} {prio_col} {rd_col} {oq_col} "
            f"{exec_col} {valid_col} {date_col} {set_col} {num_col} {id6_col} {deps_col}{inline_gate}{stale_marker}"
        )
    else:
        row_line = (
            f"{st_col} {tp_col} {blk_col} {prio_col} {rd_col} {oq_col} "
            f"{exec_col} {valid_col} {date_col} {set_col} {num_col} {id6_col} {deps_col}{inline_gate}{stale_marker}"
        )
    if details and it.detail_text:
        tag = it.detail_kind or "summary"
        safe_text = _safe_detail(it.detail_text)
        tag_txt = term.color256(f"{tag}:", 244) if colored else f"{tag}:"
        detail_txt = term.color256(safe_text, 250) if colored else safe_text
        row_line += f"\n      {tag_txt} {detail_txt}"

    return row_line


def is_explicit_order(order_by: Optional[str]) -> bool:
    """Return True if ``order_by`` requests an explicit sort order (not None and not ORDER_CLASS)."""
    return bool(order_by and order_by != A.ORDER_CLASS)


def _is_item_visible(
    it: Item,
    *,
    show_all: bool,
    directly_named: Collection[str] = (),
) -> bool:
    """Return whether ``it`` is visible under default terminal-item hiding.

    Terminal (``done`` / ``parked``) items stay hidden unless ``show_all`` is True or the item
    was directly addressed by identity (its own ID or exact path/filename).
    """
    if show_all:
        return True
    if it.attention_class not in (A.DONE, A.PARKED):
        return True
    return it.path in directly_named


def _terminal_status_tokens() -> frozenset[str]:
    """Return all status/class tokens that map to terminal (``done`` / ``parked``) attention classes."""
    tokens = {A.DONE, A.PARKED, "abandoned", "synthesized"}
    for mapping in A.CLASS_MAPS.values():
        for status, cls in mapping.items():
            if cls in (A.DONE, A.PARKED):
                tokens.add(status.lower().replace("_", "-"))
    return frozenset(tokens)


def directly_named_item_paths(
    items: Sequence[Item],
    selectors_list: Sequence[str],
    repo_root: Path,
) -> set[str]:
    """Return the ``it.path`` set of items directly addressed by a selector token's identity.

    An item is directly addressed when a selector token matches:
    - the item's own ``it.id`` (case-insensitive exact match), OR
    - the item's exact repo-relative path, resolved path, filename, or stem.

    Collection/group selectors (set IDs, trees, priorities, substrings, or a legacy spec ID
    shared as a ``Set:`` by child plans) do NOT mark other items as directly named.
    """
    tokens = [str(t).strip() for t in selectors_list if str(t).strip()]
    if not tokens:
        return set()

    token_lowers: set[str] = set()
    token_norm_paths: set[str] = set()
    token_resolved_paths: set[Path] = set()
    for tok in tokens:
        low = tok.lower()
        token_lowers.add(low)
        norm = tok.replace("\\", "/").lstrip("./").lower()
        token_norm_paths.add(norm)
        if "/" in tok or "\\" in tok or "." in tok:
            try:
                cand = Path(tok)
                resolved = (
                    cand.resolve()
                    if cand.is_absolute()
                    else (repo_root / cand).resolve()
                )
                token_resolved_paths.add(resolved)
            except (OSError, ValueError):
                pass

    direct: set[str] = set()
    for it in items:
        if it.id and it.id.lower() in token_lowers:
            direct.add(it.path)
            continue
        it_path_norm = it.path.replace("\\", "/").lstrip("./").lower()
        if it_path_norm in token_norm_paths:
            direct.add(it.path)
            continue
        it_name = Path(it.path).name.lower()
        if it_name in token_norm_paths:
            direct.add(it.path)
            continue
        it_stem = Path(it.path).stem.lower()
        if it_stem in token_norm_paths:
            direct.add(it.path)
            continue
        # Also match compound artifact stems (e.g. foo.ipd.md -> foo)
        if it_name.endswith(".md"):
            compound_stem = it_name[:-3]
            for suffix in (
                ".ipd",
                ".spec",
                ".backlog",
                ".research",
                ".research-report",
                ".prompt",
                ".review",
                ".release",
                ".roadmap",
                ".walkthrough",
            ):
                if compound_stem.endswith(suffix):
                    compound_stem = compound_stem[: -len(suffix)]
                    break
            if compound_stem in token_norm_paths:
                direct.add(it.path)
                continue
        if token_resolved_paths:
            try:
                if (repo_root / it.path).resolve() in token_resolved_paths:
                    direct.add(it.path)
                    continue
            except (OSError, ValueError):
                pass
    return direct


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
    directly_named: Optional[Collection[str]] = None,
) -> str:
    """Render items in a compact columnar table for interactive/TTY viewing.

    Columns: Status (8), [Run (14)], Type (8), Blocks (6), Priority (8), Readiness (9), OQs (3), Exec (4), Valid (5), Date (8), SetID, N, ID6 (6), Deps.
    Sorted by Type, Blocking (non-blocking first), SetID, N, ID6, Priority (none first, then low, med, high), name.
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
    # Match `render_json`'s `valid` and `core.drift_exit_code`: advisory `info` drift (such as
    # `attention.lane-superseded`) must NOT mark the human board `VIEW INVALID`.
    blocking_drift = [d for d in drift if d.severity != "info"]
    if blocking_drift:
        lines.append(
            "VIEW INVALID: contract violations must be resolved before this board is authoritative."
        )
        for d in blocking_drift:
            lines.append(f"  ! {d.location}: {d.rule}: {d.detail}")
        lines.append("")

    direct_set = set(directly_named) if directly_named else set()
    visible = [
        it
        for it in items
        if _is_item_visible(it, show_all=show_all, directly_named=direct_set)
    ]

    if not visible:
        return "\n".join(lines).rstrip("\n") + "\n" if lines else ""

    if id_map is None:
        id_map = {it.id: it for it in items if it.id}

    if not is_explicit_order(order_by):

        def _sort_key(it: Item) -> Tuple:
            type_word = _SINGULAR_TYPE.get(it.tree, it.tree)
            blk_ver = _resolve_release_version(repo_root, it.blocks_release)
            is_blocking = 0 if (blk_ver == "-" or not it.blocks_release) else 1
            date, set_id, num, id6 = _extract_identity_parts(it)
            prio_rank = PRIORITY_RANK.get((it.priority or "").lower(), 0)
            name = _identity_stem(it.path)
            if num.isdigit():
                return (
                    type_word,
                    is_blocking,
                    0,
                    date,
                    set_id,
                    int(num),
                    id6 if id6 != "-" else (it.id or ""),
                    prio_rank,
                    name,
                    it.path,
                )
            return (
                type_word,
                is_blocking,
                1,
                prio_rank,
                name,
                it.path,
            )

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

    visible_num_lens = [len(_extract_identity_parts(it)[2]) for it in visible]
    num_w = max(len("N"), max(visible_num_lens, default=2), 2)

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

    # WIDENED FROM 8 TO 10 to match `_render_table_row`'s Status column, which now carries the
    # lifecycle glyph in its first two columns ahead of the status word. Two leading spaces rather
    # than a `ljust(10)` so the word `Status` still sits above the WORD it labels rather than above
    # the glyph. The column ORDER and COUNT are unchanged (Section 12).
    st_hdr = "  " + "Status".ljust(8)
    tp_hdr = "Type".ljust(8)
    blk_hdr = "Blocks"
    prio_hdr = "Priority"
    rd_hdr = "Readiness"
    oq_hdr = "OQs".rjust(oq_w)
    exec_hdr = "Exec".rjust(exec_w)
    valid_hdr = "Valid".rjust(valid_w)
    date_hdr = "Date".ljust(8)
    set_hdr = col_title.ljust(set_w)
    num_hdr = "N".ljust(num_w)
    id6_hdr = "ID6".ljust(6)

    if runs_mode:
        run_hdr = "  " + "Run".ljust(14)
        header = (
            f"{st_hdr} {run_hdr} {tp_hdr} {blk_hdr} {prio_hdr} {rd_hdr} {oq_hdr} "
            f"{exec_hdr} {valid_hdr} {date_hdr} {set_hdr} {num_hdr} {id6_hdr} Deps"
        )
    else:
        header = (
            f"{st_hdr} {tp_hdr} {blk_hdr} {prio_hdr} {rd_hdr} {oq_hdr} "
            f"{exec_hdr} {valid_hdr} {date_hdr} {set_hdr} {num_hdr} {id6_hdr} Deps"
        )
    lines.append(term.colorize(header, "bold") if colored else header)

    for it in visible:
        run_st = _item_run_status(it, run_map) if runs_mode else None
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
                num_w=num_w,
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
    directly_named: Optional[Collection[str]] = None,
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
            directly_named=directly_named,
        )
    if legend is None:
        legend = colored

    direct_set = set(directly_named) if directly_named else set()
    lines: List[str] = []
    # Match `render_json`'s `valid` and `core.drift_exit_code`: advisory `info` drift (such as
    # `attention.lane-superseded`) must NOT mark the human board `VIEW INVALID`.
    blocking_drift = [d for d in drift if d.severity != "info"]
    if blocking_drift:
        lines.append(
            "VIEW INVALID: contract violations must be resolved before this board is authoritative."
        )
        for d in blocking_drift:
            lines.append(f"  ! {d.location}: {d.rule}: {d.detail}")
        lines.append("")

    if is_explicit_order(order_by):
        # Under an explicit order, emit ONE globally-ordered list instead of class-partitioned sections.
        # Items were already sorted upstream by cmd_attention; do not re-sort here.
        # Preserve the done/parked suppression unless show_all is True or the item was directly named.
        visible = [
            it
            for it in items
            if _is_item_visible(it, show_all=show_all, directly_named=direct_set)
        ]

        for it in visible:
            run_st = _item_run_status(it, run_map) if runs_mode else None
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
            direct_group = [it for it in group if it.path in direct_set]
            hidden_in_cls = len(group) - len(direct_group)
            if direct_group:
                lines.append(f"## {cls} ({len(direct_group)})")
                for it in direct_group:
                    run_st = _item_run_status(it, run_map) if runs_mode else None
                    lines.append(
                        _render_item_row(
                            it,
                            cls,
                            term,
                            colored,
                            long,
                            details=details,
                            gate_in_header=False,
                            runs_mode=runs_mode,
                            run_state=run_st,
                        )
                    )
            if hidden_in_cls > 0 and not colored:
                lines.append(f"## {cls} ({hidden_in_cls}) [hidden; use --all]")
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
            run_st = _item_run_status(it, run_map) if runs_mode else None
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


def prune_drift_to_selection(
    drift: List[core.Drift],
    items: Sequence[Item],
    repo_root: Path,
    selected_trees: Optional[set[str]] = None,
) -> List[core.Drift]:
    """Narrow ``drift`` alongside a narrowed ``items`` set WITHOUT dropping a contract violation.

    THE ONE PRUNE, called from every filter site (attcor `rkn8ya` E-01). Three byte-identical copies
    of this five-line prune existed inline (the `--types` site, the selector site, and the combined
    status/priority/blocking/readiness/open-questions/run-status site); fixing one left two live, so
    the logic is defined once here.

    WHY A PLAIN `location in selected_item_paths` TEST IS WRONG, which is the bug this replaces. A
    file that FAILS TO PARSE yields drift and NO item: `_plans_record` returns ``(None, drift)`` and
    `scan` does ``if rec is None: continue`` AFTER extending drift. Its violation therefore matched
    no surviving item path and was silently DELETED by every narrowing, so `aw attention --check`
    exited 0 on a genuine violation under `-t plans`, under a selector, and under a status filter.
    That contradicts the spec's normative fail-closed rule (Section 8.6: `--check` "never silently
    skips a malformed included artifact").

    THE RETENTION RULE is by SELECTED TREE, not "retain everything". A drift record whose location
    lies under a tree the caller selected is retained even when it produced no item; drift from an
    unselected tree is still pruned, and a NON-PATH location (a stranded lane's git BRANCH) is still
    pruned under an explicit narrowing, preserving the deliberate suppression the lane join relies
    on. Retaining all drift unconditionally would resurrect stranded-lane rows under `--types`,
    contradicting spec F3a's normative exclusions.

    ``selected_trees`` is the ACTIVE `--types` filter, or ``None`` meaning EVERY TRACKED TREE. It is
    deliberately NOT derived from the surviving items' trees: a tree whose only offending file fails
    to parse contributes no item, so keying on the items would delete precisely the violation this
    function exists to keep. A selector or status narrowing states nothing about types, so under it
    every tracked tree stays selected and only the non-path (lane) locations are pruned.
    """

    if not drift:
        return drift

    selected_paths = {(repo_root / it.path).resolve() for it in items}
    trees = (
        set(selected_trees)
        if selected_trees
        else {pol.name for pol in A.TREE_POLICY if pol.tracked}
    )
    tree_roots: List[str] = []
    for pol in A.TREE_POLICY:
        if pol.name in trees:
            root = pol.root.replace("\\", "/").rstrip("/")
            tree_roots.append(root + "/")
            # The `.aw/` layout root for the same policy key: TREE_POLICY still spells the legacy
            # `.agents/` roots, and `_classify_tree` maps `.aw/records/<type>` onto them (re-inserting
            # the `docs/` grouping for the doc family). Derive both spellings so a modern-layout
            # location is recognized by the same membership test.
            legacy_prefix = ".agents/docs/"
            if root.startswith(legacy_prefix):
                tail = root[len(legacy_prefix) :]
                # `prompts` is the legacy key for the renamed `prompt-library` tree.
                modern = "prompt-library" if tail == "prompts" else tail
                tree_roots.append(f".aw/records/{modern}/")
            elif root.startswith(".agents/"):
                tree_roots.append(".aw/records/" + root[len(".agents/") :] + "/")

    def _keep(d: core.Drift) -> bool:
        loc = str(d.location).replace("\\", "/")
        try:
            if (repo_root / loc).resolve() in selected_paths:
                return True
        except (OSError, ValueError):
            pass
        # RETAINED: a violation from a SELECTED TREE whose file produced no item (unparseable,
        # missing status, unreadable). This is the fail-closed half.
        return any(loc.startswith(r) for r in tree_roots)

    return [d for d in drift if _keep(d)]


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


def selector_vocabulary() -> frozenset:
    """The set of selector tokens that are a STANDING QUESTION about repository state.

    attsel `fqnj8k` E-08. A token in this set legitimately matches nothing (a repository may simply
    contain no `reusable` plan and no `releases` record), so a zero-match on it is a SUCCESSFUL answer
    and is exempt from the `EXIT_UNRESOLVED_SELECTOR` refusal. A token OUTSIDE it that matches nothing
    is an assertion that a named artifact exists, which is a refusal.

    THE DISTINCTION IS NOT INVENTED HERE. Spec `25kzda` Section 2.4a already draws it, for exactly this
    reason: an empty status-selector result "is a success, not an error ... because `reviews` is a
    standing question about repository state rather than an assertion that a named item exists. A
    misspelled id6 still exits 2; only the status selectors are exempt."

    DERIVED FROM THE CONTRACT SYMBOLS, NEVER A LITERAL LIST, which is the whole point: a tree, class,
    status or priority added to `attention_contract` (or to `backlog.PRIORITIES`) later joins this
    vocabulary automatically and so cannot silently become an "error" for an operator who asked a
    perfectly reasonable question about it.

    TWO SOURCES ARE INCLUDED THAT `TRACKED_TREES` AND `CLASS_MAPS` ALONE WOULD MISS, and each was
    found by MEASURING rather than by reading the enums, so neither is a guess:

    * TYPE NAMES THIS VERB ACCEPTS BUT DOES NOT SCAN. `TYPE_ALIASES` accepts `roadmaps`,
      `walkthroughs`, `prompts`, `comms` and `actions`, while `TRACKED_TREES` is five trees and the
      live scan yields four. So `aw att roadmaps` is a type question the CLI invites and the scanner
      can never answer with an item, and refusing it would call the operator wrong for using a name
      the verb's own `-t` flag documents. (The deeper gap - that `releases` records and every
      `roadmaps`/`walkthroughs` file are invisible to the view at all - is owned by approved plan
      `m867ox`, which declares `attention_contract.py`; this function deliberately does NOT edit that
      file and only stops those tokens being reported as typos.)
    * RUN-STATUS WORDS. `abandoned` reaches this verb through `--arcive-state`/`-as`, whose alias
      table is `_RUN_STATUS_ALIASES` and whose canonical values `matches_run_status` consumes. Asking
      "what is abandoned?" and hearing "nothing" is a successful answer, exactly like asking about an
      empty tree, so these join the vocabulary too. Sourced from the alias table and the `lanes`
      `CLASS_MAPS` fragment, never typed out here.
    """
    from agent_workflows import backlog as backlog_mod

    vocab: set = set()
    # Tree names (`-t`-style tokens used positionally): `specs`, `plans`, `research`, ...
    vocab |= {str(t).lower() for t in A.TRACKED_TREES}
    # Every type name the CLI accepts, INCLUDING the ones the scanner does not (see the docstring).
    vocab |= {str(k).lower() for k in TYPE_ALIASES}
    vocab |= {str(v).lower() for v in TYPE_ALIASES.values()}
    # Cross-tree attention classes: `ready`, `active`, `blocked`, `done`, `parked`.
    vocab |= {str(c).lower() for c in A.ATTENTION_CLASSES}
    # Every per-tree NATIVE status enum, read from the mapping that defines them.
    for _tree, class_map in A.CLASS_MAPS.items():
        vocab |= {str(s).lower() for s in class_map.keys()}
    # Priorities, whose owner is the backlog module.
    vocab |= {str(p).lower() for p in backlog_mod.PRIORITIES}
    # Run-status words, from the alias table this module already owns.
    vocab |= {str(k).lower() for k in _RUN_STATUS_ALIASES}
    vocab |= {str(v).lower() for v in _RUN_STATUS_ALIASES.values()}
    # The run-status words the runner writes that are not aliases (`abandoned` is the measured case).
    try:
        from agent_workflows import run_viewer as _run_viewer

        vocab.add(str(_run_viewer.ABANDONED).lower().rstrip("?"))
    except Exception:
        # A missing optional symbol must never make a legitimate question into an error, so the only
        # failure mode here is that ONE token loses its exemption, never a crash.
        pass
    return frozenset(vocab)


class ExcludedTreeMatch(NamedTuple):
    """An artifact in a deliberately excluded records tree matched by a selector token (uxb0tz E-02)."""

    token: str
    path: str  # repo-relative POSIX path
    policy: A.TreePolicy

    @property
    def name(self) -> str:
        return self.policy.name

    @property
    def reason(self) -> str:
        return self.policy.reason


def resolve_excluded_tree_matches(
    token: str, repo_root: Path
) -> List[ExcludedTreeMatch]:
    """Pure helper answering does this token resolve to an artifact under an EXCLUDED TreePolicy.

    treegap `uxb0tz` E-02.

    DERIVES TYPES FROM TREE_POLICY, NOT A HARD-CODED TUPLE (F-15, PR-04).
    Composes selectors.resolve_selectors and _classify_tree. If the token resolves
    to an artifact in a TRACKED tree, returns empty (the attention view already shows it).
    """
    tok = (token or "").strip()
    if not tok:
        return []

    # If the token resolves in any tracked tree, it is an artifact the view already shows;
    # do not treat it as an excluded-tree artifact.
    for pol in A.TREE_POLICY:
        if pol.tracked:
            try:
                if _sel.resolve_selectors(repo_root, pol.name, [tok]):
                    return []
            except Exception:
                pass

    matches: List[ExcludedTreeMatch] = []
    seen: set = set()
    for pol in A.TREE_POLICY:
        if pol.tracked:
            continue
        try:
            paths = _sel.resolve_selectors(repo_root, pol.name, [tok])
        except Exception:
            continue
        for p in paths:
            rel = _rel_posix(repo_root, p)
            cpol = _classify_tree(rel)
            if cpol is not None and not cpol.tracked and (rel, cpol.name) not in seen:
                seen.add((rel, cpol.name))
                matches.append(ExcludedTreeMatch(token=tok, path=rel, policy=cpol))
    return matches


def resolve_excluded_tree_policy(token: str, repo_root: Path) -> List[A.TreePolicy]:
    """Pure helper answering does this token resolve to an artifact under an EXCLUDED TreePolicy.

    treegap `uxb0tz` E-02. Returns the matching TreePolicy objects (name + reason) or empty.
    """
    return [m.policy for m in resolve_excluded_tree_matches(token, repo_root)]


class SelectorMatchFacts(NamedTuple):
    """Per-token answers to "did this selector match anything, and is it even a valid selector?".

    attsel `fqnj8k` E-03 / treegap `uxb0tz` E-03. Three facts are kept SEPARATE because they are
    different messages and conflating them would trade one ambiguity for another (F3):

    * ``unmatched`` - the token is a well-formed selector that matched NO artifact in the unfiltered
      scan. This is the typo case.
    * ``invalid``  - resolving the token RAISED for every record type. `filter_items_by_selectors`
      swallows that in a bare `except Exception: pass`, so today a malformed selector is as silent as
      a merely-absent one. A token here is also in ``unmatched`` when it matched nothing, because a
      malformed token that somehow matched by path substring is still a match.
    * ``excluded_tree`` - the token resolved to an artifact in an excluded records tree (E-03).
    """

    matched: Tuple[str, ...]
    unmatched: Tuple[str, ...]
    invalid: Tuple[str, ...]
    vocabulary: Tuple[str, ...]
    excluded_tree: Tuple[ExcludedTreeMatch, ...] = ()

    @property
    def refusable(self) -> Tuple[str, ...]:
        """The unmatched tokens that are NOT a standing vocabulary question or an excluded-tree artifact."""
        vocab = set(self.vocabulary)
        excluded_tokens = {m.token.lower() for m in self.excluded_tree}
        return tuple(
            t
            for t in self.unmatched
            if t.lower() not in vocab and t.lower() not in excluded_tokens
        )


def selector_match_facts(
    items: List[Item],
    selectors_list: Sequence[str],
    repo_root: Path,
    drift: Optional[Sequence[core.Drift]] = None,
) -> SelectorMatchFacts:
    """Answer, PER TOKEN, whether it matched at least one artifact in the ``items`` given.

    attsel `fqnj8k` E-03.

    THE CALLER MUST PASS THE UNFILTERED SCAN, and this is the single most important property of this
    function. `run()` applies `--type` BEFORE the selector filter, so a token matching a backlog
    artifact under `-t plans` reaches the selector filter with its artifact already gone: a match fact
    computed from what the filter RECEIVED would report that token as a typo (measured at review: the
    same filter matches `sv0sf3` over the full 1063-item scan and 0 items over the `-t plans` 661-item
    scan). Reporting a FALSE no-match is a worse defect than the silence this fix removes, so the fact
    is pinned to the scan before any filter narrowed it.

    IT KEYS ON "MATCHED", NOT ON "RESOLVED" (F4). `filter_items_by_selectors`' last rung is a SUBSTRING
    test on `it.path`, so a token can legitimately match an artifact without resolving as any
    identifier; a no-match report keyed on the resolver alone would fire on every substring query. This
    function therefore re-uses the SAME matcher the view itself uses, one token at a time, so the two
    can never disagree about what a match is.

    A MALFORMED ARTIFACT YIELDS DRIFT AND NO ITEM, so ``drift`` must be passed or a token naming a real
    but unparseable file is reported as a typo. FOUND BY THIS PLAN'S OWN E-06 TEST rather than
    predicted: a plan carrying no `Status:` produces one `attention.missing-status` violation and ZERO
    items, so `aw att <its-id6>` saw an empty match set and refused, telling the operator their id6 does
    not exist when the file is sitting in `pending/` and is precisely what they need to go fix. That is
    the F4 false-no-match class arriving by a third route, and it is the worst instance of it, because
    the one artifact you most need to find is the broken one. A token matching a drift LOCATION
    therefore counts as MATCHED.

    `filter_items_by_selectors`' own signature, return value and behavior are UNTOUCHED: this is a
    separate pure function, not a mutation of that contract.
    """
    from agent_workflows import selectors

    tokens = [str(t).strip() for t in selectors_list if str(t).strip()]
    matched: List[str] = []
    unmatched: List[str] = []
    invalid: List[str] = []

    # The drift LOCATIONS, matched the same two ways the item rungs match: by resolved path and by
    # path substring. An id6 embedded in a filename is caught by the substring rung, which is what
    # makes `aw att bad001` find a plan too broken to have become an item.
    drift_locations = [str(d.location) for d in (drift or [])]

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
    excluded_matches: List[ExcludedTreeMatch] = []
    for tok in tokens:
        # Ask the ONE matcher the view uses, for this token alone. Calling it per token is what turns
        # its set-valued answer into a per-token fact without duplicating any matching rung.
        hit = bool(filter_items_by_selectors(items, [tok], repo_root))
        if not hit and drift_locations:
            tok_lower = tok.lower()
            hit = any(tok_lower in loc.lower() for loc in drift_locations)
        if hit:
            matched.append(tok)
        else:
            unmatched.append(tok)
            # treegap `uxb0tz` E-03: check if unmatched token resolves into an excluded records tree
            ex_matches = resolve_excluded_tree_matches(tok, repo_root)
            if ex_matches:
                excluded_matches.extend(ex_matches)
        # Independently: did the resolver raise for EVERY record type? That is the malformed-selector
        # fact, which the filter's bare `except Exception: pass` currently hides. Raising for every
        # type is the test, not raising for one: most tokens raise for the types they are not.
        raised_everywhere = True
        for rt in record_types:
            try:
                selectors.resolve_selectors(repo_root, rt, [tok])
                raised_everywhere = False
            except Exception:
                continue
        if raised_everywhere:
            invalid.append(tok)

    return SelectorMatchFacts(
        matched=tuple(matched),
        unmatched=tuple(unmatched),
        invalid=tuple(invalid),
        vocabulary=tuple(sorted(selector_vocabulary())),
        excluded_tree=tuple(excluded_matches),
    )


def format_unresolved_selector_message(
    facts: SelectorMatchFacts, *, term: Optional[T.Term] = None
) -> str:
    """The human report for selector tokens that matched no artifact.

    attsel `fqnj8k` E-04. REUSES `term.Term.format_empty_result`, the house empty-state primitive
    (`aw find` renders its own empty result with it), rather than inventing a second message shape the
    operator would have to learn. It renders the outcome line, an `Active filters:` block echoing the
    offending token(s), and a `Next` action.

    EACH UNMATCHED TOKEN IS NAMED INDIVIDUALLY, never collapsed into one message, because a
    multi-token invocation is exactly where a single typo hides.

    NO "DID YOU MEAN" GUESS. A wrong guess is worse than a clean negative and the operator knows what
    they typed; fuzzy matching is a separate feature with its own design question.
    """
    from agent_workflows import agent_schema as _agent_schema

    if term is None:
        term = T.Term(stream=sys.stderr, color=False)
    toks = [_agent_schema.redact_home_paths(t) for t in facts.refusable]
    noun = "selector" if len(toks) == 1 else "selectors"
    quoted = ", ".join(repr(t) for t in toks)
    summary = f"no artifact matched {noun} {quoted}"
    filters: List[Tuple[str, Any]] = [
        (f"unmatched {noun}", list(toks)),
        ("searched trees", ", ".join(sorted(str(t) for t in A.TRACKED_TREES))),
    ]
    if facts.matched:
        # Say which tokens DID match, so a mixed invocation reads as "these worked, that one did not".
        filters.append(
            (
                "matched selectors",
                [_agent_schema.redact_home_paths(t) for t in facts.matched],
            )
        )
    if facts.invalid:
        # F3: "this token is not a valid selector at all" is a DIFFERENT message from "this valid
        # token matched nothing", and reporting only the second would trade one ambiguity for another.
        filters.append(
            (
                "not a valid selector",
                [_agent_schema.redact_home_paths(t) for t in facts.invalid],
            )
        )
    return term.format_empty_result(
        summary,
        filters=filters,
        next_action=(
            "aw next",
            "show the whole board, then copy an id6 from it",
        ),
        status="fail",
    )


def unresolved_selector_agent_record(facts: SelectorMatchFacts) -> Dict[str, Any]:
    """The `aw.agent/v1` error record for selector tokens that matched no artifact.

    attsel `fqnj8k` E-05/E-09.

    SHAPED ON THE SHIPPED PRECEDENT, not invented. `aw runs <bogus>` already refuses an unresolvable
    read-only target with `kind:error, outcome:cannot-run, exit:2, verified:false, complete:false,
    findings:N, unresolved_targets:[...]` (`run_viewer.emit_unresolvable_target_refusal`), and that
    shape validates today. Copying it means one convention across the two verbs rather than a third.

    WHY `verified:false` AND `complete:false` ARE THE HONEST VALUES, and this is the half that matters
    most for automation. The old record said `outcome:clean, verified:true, complete:true, findings:0`
    for a token that matched nothing, so a consumer recorded a typo as a CLEAN AUDIT. Both booleans
    were false in substance: nothing was verified, and the answer is not complete, it is ABSENT.

    BOTH FIELD NAMES ARE EMITTED (decision D2). `unresolved_selectors` is this verb's own noun (its
    CLI positional is `selectors`), and `unresolved_targets` carries the identical list so a consumer
    already written against the `aw runs` precedent reads it unchanged. One extra key removes the only
    way a consumer could be surprised.

    NO SCHEMA BUMP IS NEEDED OR MADE. `render_json`'s `SCHEMA_VERSION` payload is not involved at all,
    because this refusal is emitted BEFORE the surface branches and so a no-match invocation never
    reaches `render_json` (decision D6).
    """
    from agent_workflows import agent_schema as _agent_schema

    toks = [_agent_schema.redact_home_paths(t) for t in facts.refusable]
    noun = "selector" if len(toks) == 1 else "selectors"
    quoted = ", ".join(repr(t) for t in toks)
    error_msg = _agent_schema.redact_home_paths(
        f"no artifact matched {noun} {quoted}; searched the tracked record trees "
        + ", ".join(sorted(str(t) for t in A.TRACKED_TREES))
    )
    record: Dict[str, Any] = {
        "schema": _agent_schema.SCHEMA_VERSION,
        "kind": "error",
        "cmd": "attention",
        "outcome": "cannot-run",
        "exit": EXIT_UNRESOLVED_SELECTOR,
        "verified": False,
        "complete": False,
        "findings": len(toks),
        "unresolved_selectors": toks,
        # D2: the precedent's own field name, same list, for a consumer written against `aw runs`.
        "unresolved_targets": toks,
        "error": error_msg,
        "next": "aw next",
    }
    if facts.matched:
        record["matched_selectors"] = [
            _agent_schema.redact_home_paths(t) for t in facts.matched
        ]
    if facts.invalid:
        # F3: kept distinct from merely-unmatched, since they are different messages.
        record["invalid_selectors"] = [
            _agent_schema.redact_home_paths(t) for t in facts.invalid
        ]
    if facts.excluded_tree:
        record["excluded_selectors"] = [
            _agent_schema.redact_home_paths(m.token) for m in facts.excluded_tree
        ]
        record["excluded_tree_selectors"] = [
            _agent_schema.redact_home_paths(m.token) for m in facts.excluded_tree
        ]
    # Fail closed on our OWN record rather than trusting it by eye (the plan forbids asserting schema
    # validity without the validator).
    _agent_schema.assert_valid_agent_record(record)
    return record


def _emit_unresolved_selector_refusal(
    facts: SelectorMatchFacts, *, args, ctx, repo_root: Path
) -> int:
    """Emit the no-match refusal on whichever surface is active, and return its exit code.

    attsel `fqnj8k` E-04/E-05/E-09/E-10. ONE function for all eight surfaces, because the defect it
    fixes was five surfaces having no report at all while two were thought to be the whole problem.

    THE CHANNEL IS PER SURFACE (decision D5), and the split is not cosmetic:

    * STDOUT for `--agent`, `--json`/`--format json` and `--check --agent`, because on those surfaces
      the record IS the payload and the consumer reads stdout.
    * STDERR for the human board, `--check`'s human path, and all three list modes. A list mode exists
      to be piped into another command, so a diagnostic on ITS stdout would corrupt the pipe; keeping
      stdout byte-identical there is a hard requirement, not a preference. This also matches the
      shipped `aw runs` refusal, which goes to stderr "so a refusal never lands in a report a caller
      is parsing on stdout".
    """
    if ctx.is_agent or ctx.is_json or getattr(args, "format", None) == "json":
        record = unresolved_selector_agent_record(facts)
        # `--json` (and `--format json`) pretty-print; `--agent` is one compact line. This mirrors how
        # `run_viewer.emit_unresolvable_target_refusal` chooses its indent.
        indent = 2 if (ctx.is_json or getattr(args, "format", None) == "json") else None
        sys.stdout.write(json.dumps(record, indent=indent, ensure_ascii=False) + "\n")
        return EXIT_UNRESOLVED_SELECTOR

    color = False if getattr(args, "no_color", False) else None
    term = T.Term(stream=sys.stderr, color=color)
    sys.stderr.write(format_unresolved_selector_message(facts, term=term) + "\n")
    return EXIT_UNRESOLVED_SELECTOR


def format_excluded_tree_message(
    facts: SelectorMatchFacts, *, term: Optional[T.Term] = None
) -> str:
    """The human report for selector tokens that resolved into an excluded records tree.

    treegap `uxb0tz` E-04. Reuses `term.Term.format_empty_result`.
    """
    if term is None:
        term = T.Term(stream=sys.stderr, color=False)

    matches = facts.excluded_tree
    tokens = [m.token for m in matches]
    noun = "selector" if len(tokens) == 1 else "selectors"
    quoted = ", ".join(repr(t) for t in tokens)
    trees = ", ".join(sorted({m.policy.name for m in matches}))
    summary = f"artifact matched {noun} {quoted} in excluded tree {trees}"
    if len(matches) == 1:
        m = matches[0]
        filters: List[Tuple[str, Any]] = [
            ("excluded selector", m.token),
            ("resolved path", m.path),
            ("excluded tree", m.policy.name),
            ("exclusion reason", m.policy.reason),
        ]
    else:
        filters = []
        for m in matches:
            filters.append(("excluded selector", m.token))
            filters.append((f"resolved path ({m.token})", m.path))
            filters.append((f"excluded tree ({m.token})", m.policy.name))
            filters.append((f"exclusion reason ({m.token})", m.policy.reason))

    next_cmd = f"aw find {' '.join(tokens)}"
    return term.format_empty_result(
        summary,
        filters=filters,
        next_action=(
            next_cmd,
            "show the artifact directly",
        ),
        status="clean",
    )


def excluded_tree_agent_record(
    facts: SelectorMatchFacts, repo_root: Path
) -> Dict[str, Any]:
    """The `aw.agent/v1` result record for selector tokens that resolved into an excluded tree.

    treegap `uxb0tz` E-04 (F-13, PR-02). Emits kind: "result" with outcome: "clean",
    verified: true, complete: true, exit: 0. Names excluded tokens in a dedicated field.
    """
    from agent_workflows import agent_schema as _agent_schema

    matches = facts.excluded_tree
    tokens = [m.token for m in matches]
    quoted = ", ".join(repr(t) for t in tokens)
    trees = ", ".join(sorted({m.policy.name for m in matches}))

    if len(matches) == 1:
        summary = f"artifact matched selector {quoted} in excluded tree {trees}"
    else:
        summary = f"artifacts matched selectors {quoted} in excluded trees: {trees}"

    record: Dict[str, Any] = {
        "schema": _agent_schema.SCHEMA_VERSION,
        "kind": "result",
        "cmd": "attention",
        "outcome": "clean",
        "exit": 0,
        "verified": True,
        "complete": True,
        "excluded_selectors": tokens,
        "excluded_tree_selectors": tokens,
        "excluded_artifacts": [
            {
                "selector": m.token,
                "path": m.path,
                "tree": m.policy.name,
                "reason": m.policy.reason,
            }
            for m in matches
        ],
        "summary": summary,
        "next": f"aw find {' '.join(tokens)}",
    }
    if facts.matched:
        record["matched_selectors"] = list(facts.matched)
    if facts.invalid:
        record["invalid_selectors"] = list(facts.invalid)

    _agent_schema.assert_valid_agent_record(record)
    return record


def _emit_excluded_tree_explanation(
    facts: SelectorMatchFacts, *, args, ctx, repo_root: Path
) -> None:
    """Emit the excluded-tree explanation on whichever surface is active.

    treegap `uxb0tz` E-04. Channel split:
    - stdout for --agent, --json/--format json, and --check
    - stderr for human board and list modes
    """
    is_json = ctx.is_json or getattr(args, "format", None) == "json"
    is_agent = ctx.is_agent
    check = getattr(args, "check", False)

    if not facts.refusable and (is_agent or is_json):
        record = excluded_tree_agent_record(facts, repo_root=repo_root)
        indent = 2 if is_json else None
        sys.stdout.write(json.dumps(record, indent=indent, ensure_ascii=False) + "\n")
        return

    color = False if getattr(args, "no_color", False) else None
    stream = sys.stdout if (check and not facts.refusable) else sys.stderr
    term = T.Term(stream=stream, color=color)
    msg = format_excluded_tree_message(facts, term=term) + "\n"
    stream.write(msg)


def run(args) -> int:
    # Climb to the project root so `aw attention` works from any subdirectory; an explicit --dir is
    # honored verbatim (IPD awretrofit Order 06).
    from agent_workflows.project_context import (
        nonsurveyable_root_refusal,
        resolve_verb_repo_root,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Evidence,
        NextAction,
        select_output,
    )

    explicit_dir = getattr(args, "dir", None)
    repo_root = resolve_verb_repo_root(explicit_dir)
    check = getattr(args, "check", False)
    ctx = select_output(args)

    refusal = nonsurveyable_root_refusal(
        "attention", repo_root, explicit_dir=bool(explicit_dir)
    )
    if not refusal.may_proceed:
        # ci9kx2-01 (`bjgqez`) E-03: --check is valid only for a climb that found no project (nothing
        # to violate); an explicitly named non-project directory fails closed with cannot-run
        # (spec Section 8.1: could-not-run is exit 2 / fail closed; human 3).
        if check and not explicit_dir:
            # rolswj/akhwp7: one local carries the examined count to both surfaces.
            no_project_items = 0
            if ctx.is_agent or ctx.is_json:
                res = CommandResult(
                    command="attention",
                    status="clean",
                    exit_code=0,
                    summary="the view is valid",
                    evidence=[
                        Evidence(
                            key="attention",
                            value={"items": no_project_items, "drift": 0},
                            status="clean",
                        )
                    ],
                    data={"items": [], "drift": []},
                )
                return get_renderer(ctx).emit(res, ctx)
            sys.stdout.write(
                "aw attention --check: the view is valid. "
                f"{no_project_items} items checked, 0 violations.\n"
            )
            return 0
        if ctx.is_agent or ctx.is_json:
            next_actions = (
                [
                    NextAction(
                        command=refusal.next_action_command,
                        description=refusal.next_action_description,
                    )
                ]
                if refusal.next_action is not None
                else []
            )
            res = CommandResult(
                command="attention",
                status="cannot-run",
                exit_code=2,
                summary=refusal.summary,
                next_actions=next_actions,
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write((refusal.human_message or "") + "\n")
        return EXIT_CANNOT_RUN

    type_filters = parse_type_filters(getattr(args, "types", None))

    from agent_workflows import artifact_meta as _att_meta
    from agent_workflows import selectors as _att_sel

    with (
        _att_meta.scan_once(),
        _att_meta.ephemeral_if_uninitialized(),
        _att_sel.scan_once(),
    ):
        return _run_with_scan_once(args, repo_root, check, ctx, type_filters)


def _run_with_scan_once(args, repo_root, check, ctx, type_filters) -> int:
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        Evidence,
    )

    try:
        items, drift = scan(repo_root, type_filters=type_filters)
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

    # attsel `fqnj8k` E-03: HOLD THE UNNARROWED SCAN RESULT for the selector match facts. `items` and
    # `drift` are both rebound by the filters below, and the match fact must be answered against what
    # the scan actually found rather than against what a filter left. Captured here, immediately after
    # the ONE scan, so no filter can have touched it and no second scan is needed in the common case.
    unnarrowed_items = list(items)
    unnarrowed_drift = list(drift)

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
        # attcor `rkn8ya` E-01: prune through the ONE shared helper, which retains a violation from a
        # SELECTED TREE even when the offending file produced no item. `selected_trees` is the
        # REQUESTED filter, not the surviving items' trees: a tree whose every file fails to parse has
        # no surviving item, and keying on the items would delete exactly the violations that matter.
        drift = prune_drift_to_selection(
            drift, items, repo_root, selected_trees=type_filters
        )

    selectors_arg = getattr(args, "selectors", None) or []
    selector_facts: Optional[SelectorMatchFacts] = None
    if selectors_arg:
        # attsel `fqnj8k` E-03: THE MATCH FACT IS COMPUTED AGAINST THE UNFILTERED SCAN, and that is
        # the load-bearing detail of this whole fix.
        #
        # `--type` narrowed `items` fifteen lines above, so asking "did this token match?" of the list
        # the selector filter RECEIVES answers NO for a token whose artifact `--type` already removed.
        # Measured at review: the same filter matches `sv0sf3` over the full 1063-item scan and 0 items
        # over the `-t plans` 661-item scan, so `aw att sv0sf3 -t plans` would be reported as a TYPO.
        # Reporting a FALSE no-match is a WORSE defect than the silence this change removes, so the
        # fact is pinned to a scan that no filter has narrowed.
        #
        # A SECOND SCAN IS PAID ONLY WHEN `--type` COULD HAVE HIDDEN A MATCH. `scan()` itself honors
        # `type_filters`, so under `--type` even `unnarrowed_items` never saw the other trees and the
        # only way to know whether a token matches one of them is to scan them. Without `--type`,
        # `unnarrowed_items` IS the complete scan and re-scanning would buy nothing: a full scan of this
        # repository measures about 1.3s against about 0.65s narrowed, and paying that on every plain
        # `aw att <id6>` would be a user-perceptible slowdown for no change in output.
        fact_items = unnarrowed_items
        fact_drift = unnarrowed_drift
        if type_filters:
            try:
                fact_items, fact_drift = scan(repo_root)
            except Exception:
                # A scan that fails here must not break the view: fall back to the narrowed result,
                # which can only ever UNDER-report a match. Under-reporting means the refusal does not
                # fire, i.e. the pre-change behavior, never a false accusation.
                fact_items, fact_drift = unnarrowed_items, unnarrowed_drift
        selector_facts = selector_match_facts(
            fact_items, selectors_arg, repo_root, drift=fact_drift
        )
        items = filter_items_by_selectors(items, selectors_arg, repo_root)
        drift = prune_drift_to_selection(
            drift, items, repo_root, selected_trees=type_filters or None
        )

    # attsel `fqnj8k` E-04/E-05/E-06/E-09/E-10: THE REFUSAL, EVALUATED ONCE, BEFORE EVERY
    # SURFACE-SPECIFIC BRANCH.
    #
    # WHY HERE AND NOT IN THE RENDERERS (decision D4, answering OQ-02). `--check` returns before the
    # board is composed, and so do `-id`/`--paths`/`--filenames`; a message appended to the board
    # reaches NEITHER, which is precisely how five output surfaces stayed silent while the defect was
    # thought to be about two. Evaluating the ONE predicate here is what makes all eight surfaces agree
    # without eight copies of it.
    #
    # AND IT IS A SEPARATE CONDITION FROM DRIFT, deliberately. A `Drift` record is a repository-CONTRACT
    # finding about an artifact; an unmatched token is an OPERATOR INPUT error. Routing the refusal
    # through the drift set would get the `--check` behavior for free but would make `--json`'s `valid`
    # flag mean "you typed wrong", and would leave the maintainer unable to relax OQ-02 without
    # touching the drift path.
    # treegap `uxb0tz` E-04: THE EXCLUDED-TREE EXPLANATION, EVALUATED BEFORE THE REFUSAL GUARD.
    # Evaluated immediately before the refusal guard, keyed on the excluded-tree fact rather than
    # on refusable, so it fires for an excluded token even when a second token in the same
    # invocation is refusable (ordering matters; mixed case emits explanation first, then refuses).
    if selector_facts is not None and selector_facts.excluded_tree:
        _emit_excluded_tree_explanation(
            selector_facts, args=args, ctx=ctx, repo_root=repo_root
        )
        if not selector_facts.refusable:
            return 0

    if selector_facts is not None and selector_facts.refusable:
        return _emit_unresolved_selector_refusal(
            selector_facts, args=args, ctx=ctx, repo_root=repo_root
        )

    terminal_tokens = _terminal_status_tokens()
    status_filters = parse_status_filters(getattr(args, "status", None))
    has_terminal_status = any(s in terminal_tokens for s in status_filters)
    if status_filters:
        items = [it for it in items if matches_status(it, status_filters)]

    status_not_filters = parse_status_filters(getattr(args, "status_not", None))
    if status_not_filters:
        items = [it for it in items if not matches_status(it, status_not_filters)]

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
        # attcor `rkn8ya` E-07: the FILTER, and ONLY the filter. The second narrowing that used to sit
        # here (dropping DONE/PARKED when `--all`/a selector/a terminal status was absent) has moved
        # to where every other default-visibility decision is already made: the RENDER stage.
        #
        # WHY THE MOVE, in one measurement: `--priority high --format json` kept 90 `done` + 2
        # `parked` items while `--open-questions --format json` kept 0 of either, because this was the
        # ONE filter applying default visibility in the filter stage. The JSON and `--agent` renderers
        # deliberately apply NO visibility narrowing, so the payload silently disagreed with every
        # other filter's payload.
        #
        # IT ALSO POISONED `--check`: the shrunken item set shrank `selected_paths`, so a contract
        # violation on a `done` artifact carrying open questions was pruned out of the drift set and
        # `--check` exited 0 on it.
        #
        # THE DEFAULT HUMAN BOARD IS UNCHANGED, and that is by construction rather than by care: the
        # render stage recomputes the SAME predicate (`args.all or selectors or has_terminal_status`)
        # and passes it as `show_all`, which `render_board`/`render_table`/`--id6-only` already honor.
        items = [it for it in items if (getattr(it, "oqs", 0) or 0) > 0]

    active_flag = getattr(args, "active", False)
    not_active_flag = getattr(args, "not_active", False)

    if active_flag:
        run_status_filters = {"any"}
    elif not_active_flag:
        run_status_filters = {"-", "none", "no", "false"}
    else:
        raw_run_st = (
            getattr(args, "run_status", None)
            or getattr(args, "arcive_state", None)
            or getattr(args, "active_state", None)
        )
        run_status_filters = parse_run_status_filters(raw_run_st)

    has_terminal_run_status = any(
        s in ("done", "failed", "completed", "executed", "any")
        for s in run_status_filters
    )
    if has_terminal_run_status:
        has_terminal_status = True

    order_keys = [k.strip() for k in order_by.split(",") if k.strip()]
    runs_in_order = any(k in ("runs", "run") for k in order_keys)
    runs_arg = getattr(args, "runs", False)
    runs_needed = (
        bool(runs_arg)
        or bool(run_status_filters)
        or runs_in_order
        or active_flag
        or not_active_flag
    )

    run_map = get_active_runs_map(repo_root) if (runs_needed and repo_root) else {}

    if run_status_filters:
        items = [
            it for it in items if matches_run_status(it, run_status_filters, run_map)
        ]

    if (
        any(
            (
                status_filters,
                status_not_filters,
                priority_filters,
                blocking_filters,
                readiness_filters,
                open_questions_filter,
                run_status_filters,
            )
        )
        and drift
    ):
        # attcor `rkn8ya` E-01, the third of the three formerly-duplicated prune sites. A status,
        # priority, blocking, readiness, open-questions or run-status narrowing says nothing about
        # TYPES, so the tree selection passed through is whatever `--types` asked for (or every
        # tracked tree), and a malformed artifact's violation survives instead of being deleted with
        # the item it never produced.
        drift = prune_drift_to_selection(
            drift, items, repo_root, selected_trees=type_filters or None
        )

    # lanestrand-01 (`pr5b0t`) E-04/E-05/E-06: JOIN THE STRANDED LANES AT RENDER TIME, after the
    # artifact filters and before anything consumes `drift`.
    #
    # AFTER THE FILTERS DELIBERATELY. Each filter above prunes `drift` down to the SELECTED artifact
    # paths, and a lane's `Drift` location is a git BRANCH that matches no path, so adding lanes before
    # the filters would have every filter silently delete them. Adding them here also means one thing
    # for both surfaces: `render_json` derives its `stranded_lanes` list from this same set, and
    # `core.drift_exit_code` reads it for the exit code, so the payload's `valid` flag and the gate can
    # never disagree.
    #
    # SUPPRESSED UNDER AN EXPLICIT NARROWING, matching what the filters above already do to artifact
    # drift: a user who asked for `--types specs` asked about specs, and a lane belongs to no tree they
    # selected. The DEFAULT invocation (what CI and an agent run) is the one that must fail closed, and
    # it does.
    if not type_filters and not selectors_arg:
        drift = drift + stranded_lane_drift(repo_root)
        drift.sort(key=lambda d: (d.location, d.rule))

    # Re-order the (possibly filtered) items. `scan()` already returned them in the default order, so
    # for `-o class` this is a no-op re-sort of an already-sorted list and the output is unchanged.
    if order_by != A.ORDER_CLASS:
        items, order_notices = sort_items_with_notices(
            items, order_by, repo_root=repo_root, run_map=run_map
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
            # nwcf8j E-03: Read each drift's real severity via check_engine.enrich_drift(d).severity or "error".
            # Note: all eleven attention.* rules are currently unregistered in RULE_REGISTRY (deferred to 1urnej),
            # so artifact drift enriches to "error". The enriched read queries the central authority, preserving
            # stamped non-error severities (such as attention.lane-superseded -> "info") and making future rule
            # registrations a registry edit rather than a code change here.
            diagnostics = [
                Diagnostic(
                    location=d.location,
                    rule=d.rule,
                    detail=d.detail,
                    severity=_ce.enrich_drift(d).severity or "error",
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
                    "items": [_item_dict(it) for it in items],
                    "drift": [d._asdict() for d in drift],
                },
            )
            return get_renderer(ctx).emit(res, ctx)

        if drift:
            for d in drift:
                sys.stdout.write(f"{d.location}: {d.rule}: {d.detail}\n")
            sys.stdout.write(f"aw attention --check: {summary}.\n")
        else:
            sys.stdout.write(f"aw attention --check: the view is valid. {summary}.\n")
        return exit_code

    has_terminal_selector = any(
        str(tok).strip().lower().replace("_", "-") in terminal_tokens
        for tok in selectors_arg
    )
    directly_named = (
        directly_named_item_paths(items, selectors_arg, repo_root)
        if selectors_arg
        else set()
    )
    effective_show_all = (
        getattr(args, "all", False) or has_terminal_status or has_terminal_selector
    )

    id6_only = getattr(args, "id6_only", False)
    paths_only = getattr(args, "paths", False)
    filenames_only = getattr(args, "filenames", False)

    if id6_only or paths_only or filenames_only:
        visible = [
            it
            for it in items
            if _is_item_visible(
                it, show_all=effective_show_all, directly_named=directly_named
            )
        ]

        if id6_only:
            for it in visible:
                val = extract_id6(it)
                if val:
                    sys.stdout.write(f"{val}\n")
        elif paths_only:
            for it in visible:
                sys.stdout.write(f"{it.path}\n")
        elif filenames_only:
            for it in visible:
                name = Path(it.path).name
                sys.stdout.write(f"{name}\n")
        return core.drift_exit_code(drift)

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
        # nwcf8j E-03: Read each drift's real severity via check_engine.enrich_drift(d).severity or "error".
        diagnostics = notice_diagnostics + [
            Diagnostic(
                location=d.location,
                rule=d.rule,
                detail=d.detail,
                severity=_ce.enrich_drift(d).severity or "error",
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
        waiting = inbox_waiting(repo_root)
        if waiting:
            # awinbox Order 04 (`qp8fn1`): emit the waiting-drops count as a scalar Evidence key
            # so it survives compact agent sanitization (f"{key}:{val}") with zero finding inflation.
            # Default status="verified" indicates an observation, not a finding/verdict.
            evidence.append(
                Evidence(
                    key="inbox-waiting",
                    value=waiting,
                )
            )
        try:
            from agent_workflows import checkup as _chk

            _rec = _chk.read_checkup_record(repo_root)
            if _rec is not None:
                _chk_line = _chk.format_checkup_line(_rec, repo_root=repo_root)
                _is_warn = _chk.is_checkup_warning(_rec, repo_root)
                evidence.append(
                    Evidence(
                        key="checkup",
                        value={"line": _chk_line, "record": _rec},
                        status="warning" if _is_warn else "clean",
                    )
                )
                if _is_warn:
                    diagnostics.append(
                        Diagnostic(
                            location=str(repo_root),
                            rule="attention.ci-checkup",
                            detail=_chk_line,
                            severity="warning",
                        )
                    )
        except Exception:
            pass

        res = CommandResult(
            command="attention",
            status=status,
            exit_code=exit_code,
            summary=summary,
            diagnostics=diagnostics,
            evidence=evidence,
            data={
                "items": [_item_dict(it) for it in items],
                "drift": [d._asdict() for d in drift],
            },
        )
        return get_renderer(ctx).emit(res, ctx)

    if fmt == "json" or ctx.is_json:
        sys.stdout.write(render_json(items, drift, repo_root=repo_root))
    else:
        # Color only for a real TTY (should_color honors NO_COLOR/FORCE_COLOR/TERM/isatty);
        # --no-color forces plain, which also yields the machine-readable [tree] form.
        # --format markdown is a color-free surface per spec Section 8.1 / 8.8 (plan qpw45x).
        color = (
            False if (getattr(args, "no_color", False) or fmt == "markdown") else None
        )
        term = T.Term(stream=sys.stdout, color=color)
        colored = bool(getattr(term, "color", False))
        long = getattr(args, "long", False)
        show_all = effective_show_all
        details = getattr(args, "details", False)
        runs_mode = runs_needed

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
                    runs_mode=runs_mode,
                    run_map=run_map,
                    directly_named=directly_named,
                )
            else:
                blockers = release_blockers(items, repo_root)
                blocker_keys = {it.path for it in blockers}
                main_items = [it for it in items if it.path not in blocker_keys]

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
                    runs_mode=runs_mode,
                    run_map=run_map,
                    directly_named=directly_named,
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
                        run_st = _item_run_status(it, run_map) if runs_mode else None
                        board += (
                            _render_item_row(
                                it,
                                it.attention_class,
                                term,
                                colored,
                                long,
                                details=details,
                                runs_mode=runs_mode,
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
                runs_mode=runs_mode,
                run_map=run_map,
                directly_named=directly_named,
            )

        total_matching = len(items)
        visible_count = sum(
            1
            for it in items
            if _is_item_visible(it, show_all=show_all, directly_named=directly_named)
        )
        hidden_count = total_matching - visible_count

        # Lead with what is ON SCREEN. `737 matching artifacts (723 hidden)` above a 14-row table
        # read as a row count and was wrong at a glance (maintainer, 2026-09-24).
        shown_count = total_matching - hidden_count
        count_noun = "artifact" if shown_count == 1 else "artifacts"
        if hidden_count > 0:
            count_line = (
                f"{shown_count} {count_noun} shown ({hidden_count} done or parked hidden;"
                f" {total_matching} total matched; use --all)"
            )
        else:
            count_line = f"{shown_count} {count_noun} shown"

        if board.strip():
            board = board.rstrip("\n") + "\n" + count_line + "\n"
        else:
            board = count_line + "\n"

        # bklggrad orb9zb E-06: advisory release-gate warnings (human view only; NEVER affect the
        # exit code). Surfaces orphaned-live-blocker (an open blocking item already handed off to a
        # plan) with a de-gate/close hint.
        run_gate_warnings = not type_filters or "backlog" in type_filters
        gate_warnings = []
        if run_gate_warnings:
            try:
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

        # isnqja E-04: advisory graduated-closable warnings (human view only; NEVER affect the exit
        # code). Surfaces graduated items whose carriers have all reached a terminal state.
        run_closable_warnings = not type_filters or "backlog" in type_filters
        closable_warnings = []
        if run_closable_warnings:
            try:
                closable_warnings = _ce.graduated_closable_warnings(repo_root)
                if selectors_arg and closable_warnings:
                    selected_paths = {(repo_root / it.path).resolve() for it in items}
                    closable_warnings = [
                        w
                        for w in closable_warnings
                        if (repo_root / w.location).resolve() in selected_paths
                    ]
            except Exception:
                closable_warnings = []
        if closable_warnings:
            cw_header = f"graduated-closable ({len(closable_warnings)})"
            if colored:
                board += term.color256(cw_header, 214, bold=True) + "\n"
            else:
                board += f"## {cw_header}\n"
            for w in closable_warnings:
                detail, _, fix = w.detail.partition("\n    Fix:")
                ident = (
                    _identity_stem(w.location) if colored and not long else w.location
                )
                board += f"- {ident}: {w.rule}: {detail}\n"
                if fix.strip():
                    board += f"    Fix: {fix.strip()}\n"

        # lanestrand-01 (`pr5b0t`) E-04: the LOUD stranded-lane section. It is deliberately DUPLICATED
        # information: the same lanes already appear in the board's `VIEW INVALID` violation block
        # (because they are `Drift` records, which is what makes `--check` fail), and this section
        # restates them under a heading naming the condition, with the remedy, so an operator reading a
        # long board cannot mistake unintegrated work for one more contract nit. NOT advisory, unlike
        # the two sections around it: these findings DO drive the exit code, through the drift set.
        lane_section = render_stranded_lane_section(drift)
        if lane_section:
            if colored:
                first, _, rest = lane_section.partition("\n")
                has_at_risk_lanes = any(
                    d.rule in (LANE_STRANDED_RULE, LANE_UNKNOWN_RULE) for d in drift
                )
                header_color = 203 if has_at_risk_lanes else 214
                board += (
                    term.color256(first.lstrip("# "), header_color, bold=True)
                    + "\n"
                    + rest
                )
            else:
                board += lane_section

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
        try:
            from agent_workflows import checkup as _chk

            _rec = _chk.read_checkup_record(repo_root)
            _chk_line = _chk.format_checkup_line(_rec, repo_root=repo_root)
            _is_warn = _chk.is_checkup_warning(_rec, repo_root)
            if _is_warn and colored:
                footer_lines.append(term.color256(_chk_line, 214, bold=True))
            else:
                footer_lines.append(_chk_line)
        except Exception:
            pass

        try:
            parked_counts = get_parked_question_counts(repo_root)
            for rid, cnt in sorted(parked_counts.items()):
                q_noun = "question" if cnt == 1 else "questions"
                footer_lines.append(
                    f"run {rid}: {cnt} {q_noun} waiting; answer with aw runs answer {rid}"
                )
        except Exception:
            pass

        # awinbox Order 03 (`olmvgw`, recovering `9iiqmm`): the waiting-inbox-drops nudge.
        waiting = inbox_waiting(repo_root)
        if waiting:
            noun = "file" if waiting == 1 else "files"
            footer_lines.append(
                f"TODO: {waiting} {noun} waiting in `.aw/inbox/`. Run `aw adopt <path>` to file one."
            )

        needs_setup = setup_needed(repo_root)
        if needs_setup:
            # The --all hint lives on the count line now; do not repeat it here.
            footer_lines.append(
                'TODO: Run `/aw setup-repo` (or ask your agent to "run setup-repo") to set up this repo.'
            )

        if footer_lines:
            board = board.rstrip("\n") + "\n" + "\n".join(footer_lines) + "\n"
        else:
            board = board.rstrip("\n") + "\n"
        sys.stdout.write(board)
    # a plain view still fails closed if invalid, so consumers cannot treat an invalid view as authoritative
    return core.drift_exit_code(drift)
