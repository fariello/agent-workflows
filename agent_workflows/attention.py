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
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as core
from agent_workflows import attention_contract as A
from agent_workflows import plans as plans_mod
from agent_workflows import research_contract
from agent_workflows import specs as specs_mod
from agent_workflows import term as T

SCHEMA_VERSION = 1
MAPPING_VERSION = 1


class Item(NamedTuple):
    id: str
    path: str  # repo-relative POSIX
    tree: str
    native_status: str
    attention_class: str
    gate: Optional[Dict[str, str]]
    last_history_at: Optional[str]


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

    # External AW operational actions scan (spec Section 12.7 & E-01)
    try:
        from agent_workflows.actions import ActionManager, ActionDocument

        mgr = ActionManager(target_repo=str(repo_root))
        actions_root = mgr.actions_dir
        for status in ("open", "completed", "dismissed", "superseded"):
            status_dir = actions_root / status
            if not status_dir.is_dir():
                continue
            for action_file in status_dir.glob("*-v*.md"):
                if action_file.name.startswith(".tmp_"):
                    continue
                logical_path = f"aw-state/actions/{status}/{action_file.name}"
                try:
                    text = action_file.read_text(encoding="utf-8")
                    doc = ActionDocument.from_markdown(text)
                    cls_name = A.class_of("actions", doc.status)
                    item = Item(
                        id=doc.id,
                        path=logical_path,
                        tree="actions",
                        native_status=doc.status,
                        attention_class=cls_name,
                        gate=None,
                        last_history_at=None,
                    )
                    items.append(item)
                except Exception as exc:
                    drift.append(
                        core.Drift(
                            logical_path,
                            "attention.external-state-invalid",
                            A.escape_detail(f"invalid action document: {exc}"),
                        )
                    )
    except Exception as exc:
        drift.append(
            core.Drift(
                "aw-state/actions",
                "attention.external-state-invalid",
                A.escape_detail(f"external state root error: {exc}"),
            )
        )

    items.sort(
        key=lambda it: (
            A.ATTENTION_CLASS_ORDER.index(it.attention_class),
            it.path,
            it.id,
        )
    )
    drift.sort(key=lambda d: (d.location, d.rule))
    return items, drift


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
    return None, []


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
    return Item("", rel, "specs", status, A.class_of("specs", status), gate, lha), drift


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
    return Item(
        pid or "", rel, "plans", status, A.class_of("plans", status), None, lha
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
    status = str(data["status"])
    if status not in research_contract.STATUSES:
        drift.append(
            core.Drift(
                rel,
                "attention.unknown-status",
                A.escape_detail(f"research status {status!r}"),
            )
        )
        return None, drift
    rid = str(data.get("id", "")) if data.get("id") else ""
    lha = A.last_history_at(_history_section_lines(text))
    return Item(
        rid, rel, "research", status, A.class_of("research", status), None, lha
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
        item.id or "", rel, "backlog", status, A.class_of("backlog", status), gate, lha
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
    "intake": 44,  # teal (research not-yet-active)
    "open": 40,
    "ready": 40,
    "approved": 46,  # bright green (cleared to go)
    "reviewed": 226,  # yellow (progressed, awaiting approval)
    "to-review": 214,  # orange (needs a review pass)
    "draft": 245,  # gray (not ready)
    "implementing": 51,  # cyan
    "implemented": 46,
    "blocked": 203,
    "deferred": 208,  # orange-red (gated)
    "done": 244,
    "parked": 244,
    "superseded": 240,
    "not-executed": 240,
}
_TREE_COLOR_256 = 33  # bold blue for the tree-name path segment


def _colorize_tree_segment(term: "T.Term", path: str, tree: str) -> str:
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


def render_board(
    items: List[Item],
    drift: List[core.Drift],
    show_all: bool = False,
    term: "T.Term | None" = None,
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
        lines.append(f"## {cls} ({len(group)}){header_extra}")

        for it in group:
            status_word = it.native_status
            if colored:
                code = _STATUS_COLOR_256.get(
                    it.native_status, _CLASS_COLOR_256.get(cls, 244)
                )
                status_txt = term.color256(status_word, code, bold=True)
                # Human view: no [tree] bracket and no trailing tag (keeps the line narrow).
                # The tree identity is signaled IN PLACE by coloring the tree-name path
                # segment (e.g. the `backlog` in `.agents/backlog/open/...`) bold blue, so no
                # width is added. Gate is folded into the header above; if an item's gate
                # artifact differs from the folded one, still show it inline.
                path_txt = _colorize_tree_segment(term, it.path, it.tree)
                inline_gate = ""
                if it.gate and cls != A.BLOCKED:
                    g = it.gate
                    inline_gate = (
                        f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
                    )
                lines.append(f"- {path_txt} ({status_txt}){inline_gate}")
            else:
                suffix = ""
                if it.gate:
                    g = it.gate
                    suffix = (
                        f"  [gate {g.get('kind')}: {A.escape_detail(g.get('ref', ''))}]"
                    )
                lines.append(f"- [{it.tree}] {it.path} ({status_word}){suffix}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# --------------------------------------------------------------------------------------
# CLI entrypoint
# --------------------------------------------------------------------------------------


def run(args) -> int:
    repo_root = Path(getattr(args, "dir", None) or ".")
    try:
        items, drift = scan(repo_root)
    except (
        Exception
    ) as exc:  # a could-not-run condition (missing contract symbol, etc.)
        sys.stderr.write(f"aw attention: could not run: {exc}\n")
        return 2

    check = getattr(args, "check", False)
    agent = getattr(args, "agent", False)
    fmt = getattr(args, "format", None)

    if check:
        if agent:
            sys.stdout.write(core.render_agent_drift(drift))
        else:
            if drift:
                for d in drift:
                    sys.stdout.write(f"{d.location}: {d.rule}: {d.detail}\n")
            else:
                sys.stdout.write("aw attention --check: the view is valid.\n")
        return core.drift_exit_code(drift)

    if fmt == "json":
        sys.stdout.write(render_json(items, drift))
    else:
        # Color only for a real TTY (should_color honors NO_COLOR/FORCE_COLOR/TERM/isatty);
        # --no-color forces plain, which also yields the machine-readable [tree] form.
        color = False if getattr(args, "no_color", False) else None
        term = T.Term(stream=sys.stdout, color=color)
        sys.stdout.write(
            render_board(items, drift, show_all=getattr(args, "all", False), term=term)
        )
    # a plain view still fails closed if invalid, so consumers cannot treat an invalid view as authoritative
    return core.drift_exit_code(drift)
