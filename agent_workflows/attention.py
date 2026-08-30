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
from agent_workflows import plans as plans_mod
from agent_workflows import research_contract
from agent_workflows import specs as specs_mod
from agent_workflows import term as T

SCHEMA_VERSION = 2  # awdoctorfix Order 01: items gained priority + blocks_release
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

    items.sort(
        key=lambda it: (
            A.ATTENTION_CLASS_ORDER.index(it.attention_class),
            it.path,
            it.id,
        )
    )
    drift.sort(key=lambda d: (d.location, d.rule))
    return items, drift


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
    return Item(
        mid.group(1) if mid else "", rel, "releases", status, cls, None, lha
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
    br = specs_mod._read_blocks_release(lines)
    # xprio rp859c E-03: populate Item.priority from the spec's `- Priority:` line so the board LABELS
    # a spec's priority via the existing renderer (absent = None = no label). Shared sort key unchanged.
    pr = specs_mod._read_priority(lines)
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
    return Item(
        rid,
        rel,
        "research",
        status,
        A.class_of("research", status),
        None,
        lha,
        priority=pr,
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
    `.aw/setup-repo-needed.md` is present (written by `aw install`, cleared by `aw setup` / the
    `/setup-repo` workflow / the user deleting it). DERIVED read-only from the marker; NEVER creates
    anything. Replaces the old open-`setup-repo`-action check (the ledger was deleted)."""
    try:
        return (Path(repo_root) / ".aw" / "setup-repo-needed.md").is_file()
    except Exception:
        return False


def release_blockers(items: List[Item], repo_root: Path) -> List[Item]:
    """awdoctor Order 02: items carrying a `- Blocks-Release: next|<id6>` field that are NOT done.
    Reads the field from each item's file (the awrelease Set defines it). Returns the blocking items."""
    import re as _re

    rx = _re.compile(r"(?m)^- Blocks-Release:\s*(\S+)\s*$")
    out: List[Item] = []
    for it in items:
        if it.attention_class == A.DONE:
            continue
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
) -> str:
    """Render ONE board row for an item, in the compact columnar human form (colored) or the
    stable machine form (uncolored). Extracted so the release-blockers section renders items
    identically to the active/ready/blocked sections, not as raw paths."""
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
        if it.gate and cls != A.BLOCKED:
            g = it.gate
            inline_gate = (
                f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
            )
        prio = ""
        if it.priority:
            pcode = {"high": 196, "medium": 214, "low": 244}.get(it.priority, 244)
            prio = "  " + term.color256(f"[{it.priority}]", pcode, bold=True)
        blocking = ""
        if it.blocks_release:
            blocking = "  " + term.color256("[blocking]", 196, bold=True)
        return f"- {lead}{status_padded}  {type_prefix}{path_txt}{prio}{blocking}{inline_gate}"
    suffix = ""
    if it.gate:
        g = it.gate
        suffix = f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
    return f"- [{it.tree}] {it.path} ({status_word}){suffix}"


def render_board(
    items: List[Item],
    drift: List[core.Drift],
    show_all: bool = False,
    term: T.Term | None = None,
    long: bool = False,
) -> str:
    """Render the attention board.

    When ``term`` is colored (a real TTY / FORCE_COLOR), the human view drops the ``[tree]``
    bracket, colors the tree name (bold blue) and the native status (bold, status-specific
    256-color), and folds a blocked item's gate artifact into its section header. When color
    is OFF (piped / agent / NO_COLOR / no ``term``), it emits the stable machine-readable
    ``- [tree] path (status){gate}`` form so agents and grep keep a fixed, parseable shape.
    """
    if term is None:
        term = T.Term(color=False)
    colored = bool(getattr(term, "color", False))

    lines: List[str] = []
    if drift:
        lines.append(
            "VIEW INVALID: contract violations must be resolved before this board is authoritative."
        )
        for d in drift:
            lines.append(f"  ! {d.location}: {d.rule}: {d.detail}")
        lines.append("")
    # awdoctorfix Order 01: a legend for the compact markers, colored HUMAN view only.
    if colored:
        lines.append(
            "legend: ! stale(>30d)  ? unknown-age  # blocked-by-gate  > release-blocker  [priority]"
        )
        lines.append("")
    by_class: Dict[str, List[Item]] = {}
    for it in items:
        by_class.setdefault(it.attention_class, []).append(it)
    for cls in A.ATTENTION_CLASS_ORDER:
        group = by_class.get(cls, [])
        if not group:
            continue

        # Section header. In the colored human view, fold a shared gate artifact into the
        # header (e.g. "## blocked (2) in TODO.md") instead of repeating it on every line.
        header_extra = ""
        if colored and cls == A.BLOCKED:
            artifacts = {
                A.escape_detail((it.gate or {}).get("ref", ""))
                for it in group
                if it.gate
            }
            artifacts.discard("")
            if len(artifacts) == 1:
                header_extra = f" in {next(iter(artifacts))}"

        if cls in (A.DONE, A.PARKED) and not show_all:
            lines.append(f"## {cls} ({len(group)}) [hidden; use --all]")
            continue

        # awdoctorfix Order 02: the colored default view shows a compact identity stem per item
        # (tree-independent), so no directory prefix is folded into the header. `--long` restores
        # full paths (rendered per-item below); either way the header carries no path prefix.
        lines.append(f"## {cls} ({len(group)}){header_extra}")

        for it in group:
            lines.append(_render_item_row(it, cls, term, colored, long))
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


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

    selectors_arg = getattr(args, "selectors", None) or []
    if selectors_arg:
        items = filter_items_by_selectors(items, selectors_arg, repo_root)
        if drift:
            selected_paths = {(repo_root / it.path).resolve() for it in items}
            drift = [
                d for d in drift if (repo_root / d.location).resolve() in selected_paths
            ]

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

    if fmt == "json" or ctx.is_json:
        sys.stdout.write(render_json(items, drift))
    else:
        # Color only for a real TTY (should_color honors NO_COLOR/FORCE_COLOR/TERM/isatty);
        # --no-color forces plain, which also yields the machine-readable [tree] form.
        color = False if getattr(args, "no_color", False) else None
        term = T.Term(stream=sys.stdout, color=color)
        # awdoctor Order 02: human-view-only notices (never in JSON/--check).
        if setup_needed(repo_root):
            sys.stdout.write(
                "NOTE: setup not complete - run `aw setup` to configure this repo.\n\n"
            )
        show_all = getattr(args, "all", False) or bool(selectors_arg)
        board = render_board(
            items,
            drift,
            show_all=show_all,
            term=term,
            long=getattr(args, "long", False),
        )
        colored = bool(getattr(term, "color", False))
        long = getattr(args, "long", False)
        blockers = release_blockers(items, repo_root)
        if blockers:
            # Name the release the blockers gate (id6 + version), not just a count, so the
            # planned release is visible during ordinary tool use - not only a hidden record.
            try:
                from agent_workflows import releases as _releases

                _rel = _releases.describe_planned_release(repo_root)
            except Exception:
                _rel = None
            _rel_label = f" for {_rel[1]} ({_rel[0]})" if _rel else ""
            board += f"\n## release-blockers{_rel_label} ({len(blockers)})\n"
            # Render each blocker in the SAME compact columnar form as active/ready/blocked
            # (not a raw absolute path), so the section reads consistently with the board.
            for it in blockers:
                board += (
                    _render_item_row(it, it.attention_class, term, colored, long) + "\n"
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
            board += f"\n## release-gate-warnings ({len(gate_warnings)})\n"
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
        sys.stdout.write(board)
    # a plain view still fails closed if invalid, so consumers cannot treat an invalid view as authoritative
    return core.drift_exit_code(drift)
