"""Attention-visible backlog tier (spec 20260813-1833-01; IPD backlogtier-01/crv40v).

A lightweight, tracked `records`-class sub-tree of backlog items so COMMITTED work surfaces in
`aw attention` (which feeds `/whatnext`) while uncommitted "maybes" stay quiet. Closes the
false-comprehensiveness gap where committed work living only in free-prose `TODO.md` was invisible
to the attention view.

Layout (dual-path like plans: `.agents/backlog/` pre-migration, `.aw/records/backlog/` post):

    <backlog-root>/
      open/      committed, actionable now        (attention: ready)
      blocked/   committed but gated              (attention: blocked; requires a typed gate)
      parked/    uncommitted "maybes"             (attention: parked; hidden from the default board)
      done/      completed/closed                 (attention: done)

One item is one file with `- Field:` BULLET metadata (consistent with specs/plans, and so the
existing attention `Gate-Kind`/`Gate-Ref` grammar is reused verbatim), then a prose body:

    - Id: <id6>
    - Status: open | blocked | parked | done
    - Set: <terse-id>
    - Priority: high | medium | low
    - Kind: bug | feature | chore | security | followup
    - Summary: <one line>
    - Gate-Kind: <artifact|decision|todo|issue|date|external>   # iff blocked
    - Gate-Ref: <ref>                                            # iff blocked

    ## Workflow history
    - YYYY-MM-DD <event> (<actor>): <one line>

    <free prose body>

Status is encoded BOTH by directory and by the `- Status:` bullet, and the two MUST agree.
`aw backlog new|set|check`: `new` creates a conformant item; `set` transitions status (moving the
file between the disposition dirs) and appends history; `check` validates the tree fail-closed with
the shared `Drift`/`--agent`/exit convention. Stdlib only; reuses `artifact_core` + `attention_contract`.
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from agent_workflows import artifact_core as core
from agent_workflows import attention_contract as A

BACKLOG_ROOTS = (".agents/backlog", ".aw/records/backlog")
STATUS_DIRS = ("open", "blocked", "parked", "done")
STATUSES = frozenset(STATUS_DIRS)
PRIORITIES = frozenset(("high", "medium", "low"))
KINDS = frozenset(("bug", "feature", "chore", "security", "followup"))

# Bullet-metadata field regexes (mirroring attention_contract's SPEC_STATUS_RE / GATE_*_RE style).
_ID_RE = re.compile(r"^- Id:[ \t]*(?P<value>\S+)[ \t]*$")
_STATUS_RE = re.compile(r"^- Status:[ \t]*(?P<value>\S+)[ \t]*$")
_SET_RE = re.compile(r"^- Set:[ \t]*(?P<value>\S+)[ \t]*$")
_PRIORITY_RE = re.compile(r"^- Priority:[ \t]*(?P<value>\S+)[ \t]*$")
_KIND_RE = re.compile(r"^- Kind:[ \t]*(?P<value>\S+)[ \t]*$")
_SUMMARY_RE = re.compile(r"^- Summary:[ \t]*(?P<value>.+?)[ \t]*$")
_BLOCKS_RELEASE_RE = re.compile(r"^- Blocks-Release:[ \t]*(?P<value>\S+)[ \t]*$")


class BacklogItem:
    """Parsed backlog item fields (from the leading `- Field:` bullet block)."""

    __slots__ = (
        "id",
        "status",
        "set",
        "priority",
        "kind",
        "summary",
        "gate_kind",
        "gate_ref",
        "blocks_release",
    )

    def __init__(self) -> None:
        self.id: Optional[str] = None
        self.status: Optional[str] = None
        self.set: Optional[str] = None
        self.priority: Optional[str] = None
        self.kind: Optional[str] = None
        self.summary: Optional[str] = None
        self.gate_kind: Optional[str] = None
        self.gate_ref: Optional[str] = None
        self.blocks_release: Optional[str] = None


def parse_item(text: str) -> BacklogItem:
    """Parse the leading bullet-metadata block. Missing fields stay None (validation reports them)."""

    item = BacklogItem()
    for line in text.split("\n"):
        if line.startswith("## ") or (line and not line.startswith("- ")):
            # metadata block ends at the first non-bullet, non-blank line or the first H2
            if line.startswith("## "):
                break
            # a non-bullet content line: metadata block is over
            if line.strip() and not line.startswith("- "):
                break
        for attr, rx in (
            ("id", _ID_RE),
            ("status", _STATUS_RE),
            ("set", _SET_RE),
            ("priority", _PRIORITY_RE),
            ("kind", _KIND_RE),
            ("summary", _SUMMARY_RE),
            ("blocks_release", _BLOCKS_RELEASE_RE),
        ):
            m = rx.match(line)
            if m and getattr(item, attr) is None:
                setattr(item, attr, m.group("value"))
        mk = A.GATE_KIND_RE.match(line)
        if mk and item.gate_kind is None:
            item.gate_kind = mk.group("value")
        mr = A.GATE_REF_RE.match(line)
        if mr and item.gate_ref is None:
            item.gate_ref = mr.group("value")
    return item


def _dir_status(path: Path) -> Optional[str]:
    """The disposition-directory status for an item path (its parent dir name), or None."""

    parent = path.parent.name
    return parent if parent in STATUSES else None


def validate_item(path: Path, text: str) -> List[core.Drift]:
    """Validate one backlog item fail-closed. Returns Drift records (empty == conformant)."""

    rel = path.name
    drift: List[core.Drift] = []
    item = parse_item(text)

    if not item.id or not core.is_valid_id6(item.id):
        drift.append(
            core.Drift(rel, "backlog.id-invalid", f"missing/invalid id6: {item.id!r}")
        )
    if item.status not in STATUSES:
        drift.append(
            core.Drift(
                rel,
                "backlog.status-invalid",
                f"status not in {sorted(STATUSES)}: {item.status!r}",
            )
        )
    else:
        d = _dir_status(path)
        if d is not None and d != item.status:
            drift.append(
                core.Drift(
                    rel,
                    "backlog.status-dir-mismatch",
                    f"status {item.status!r} != directory {d!r}",
                )
            )
    if item.priority not in PRIORITIES:
        drift.append(
            core.Drift(
                rel,
                "backlog.priority-invalid",
                f"priority not in {sorted(PRIORITIES)}: {item.priority!r}",
            )
        )
    if item.kind not in KINDS:
        drift.append(
            core.Drift(
                rel,
                "backlog.kind-invalid",
                f"kind not in {sorted(KINDS)}: {item.kind!r}",
            )
        )
    if not item.set:
        drift.append(core.Drift(rel, "backlog.set-missing", "missing - Set: bullet"))
    if not item.summary or not item.summary.strip():
        drift.append(
            core.Drift(rel, "backlog.summary-missing", "missing/empty - Summary:")
        )
    elif not A.is_safe_descriptive(item.summary):
        drift.append(
            core.Drift(
                rel,
                "backlog.summary-unsafe",
                "summary not a single bounded control-char-free line",
            )
        )

    # Gate present-and-valid IFF blocked; absent otherwise.
    has_gate = item.gate_kind is not None or item.gate_ref is not None
    if item.status == "blocked":
        if not item.gate_kind or not item.gate_ref:
            drift.append(
                core.Drift(
                    rel,
                    "backlog.gate-missing",
                    "blocked item requires - Gate-Kind: and - Gate-Ref:",
                )
            )
        else:
            if item.gate_kind not in A.GATE_KINDS:
                drift.append(
                    core.Drift(
                        rel,
                        "backlog.gate-kind-invalid",
                        f"Gate-Kind not in {sorted(A.GATE_KINDS)}: {item.gate_kind!r}",
                    )
                )
            elif not A.validate_gate_ref(item.gate_kind, item.gate_ref):
                drift.append(
                    core.Drift(
                        rel,
                        "backlog.gate-ref-invalid",
                        f"Gate-Ref invalid for kind {item.gate_kind!r}: {item.gate_ref!r}",
                    )
                )
    elif has_gate:
        drift.append(
            core.Drift(
                rel,
                "backlog.gate-unexpected",
                "gate fields present on a non-blocked item",
            )
        )

    return drift


def _iter_items(repo_root: Path) -> List[Path]:
    """Every backlog item file under either layout's status dirs (README excluded), sorted."""

    files: List[Path] = []
    for root_rel in BACKLOG_ROOTS:
        root = repo_root / root_rel
        for status in STATUS_DIRS:
            d = root / status
            if d.is_dir():
                for f in sorted(d.glob("*.md")):
                    if f.name != "README.md":
                        files.append(f)
    return sorted(set(files))


# --------------------------------------------------------------------------------------
# CLI verbs: new | set | check
# --------------------------------------------------------------------------------------


def _resolve_backlog_root(repo_root: Path) -> Path:
    """Prefer an existing `.aw/records/backlog`, else the pre-migration `.agents/backlog` default."""

    new = repo_root / ".aw" / "records" / "backlog"
    if new.exists():
        return new
    return repo_root / ".agents" / "backlog"


def _render_item(item: BacklogItem, body: str) -> str:
    lines = [
        f"- Id: {item.id}",
        f"- Status: {item.status}",
        f"- Set: {item.set}",
        f"- Priority: {item.priority}",
        f"- Kind: {item.kind}",
        f"- Summary: {item.summary}",
    ]
    if item.status == "blocked":
        lines.append(f"- Gate-Kind: {item.gate_kind}")
        lines.append(f"- Gate-Ref: {item.gate_ref}")
    today = datetime.date.today().isoformat()
    lines.append("")
    lines.append("## Workflow history")
    lines.append(f"- {today} created (aw backlog): {item.summary}")
    lines.append("")
    lines.append(body.rstrip() + "\n" if body.strip() else "")
    return "\n".join(lines).rstrip() + "\n"


def run_new(args) -> int:
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    status = getattr(args, "status", None) or "open"
    if status not in STATUSES:
        sys.stderr.write(
            f"aw backlog new: --status must be one of {sorted(STATUSES)}\n"
        )
        return 2
    item = BacklogItem()
    existing_ids = set()
    for f in _iter_items(repo_root):
        pid = parse_item(f.read_text(encoding="utf-8")).id
        if pid:
            existing_ids.add(pid)
    item.id = core.generate_id6(existing_ids)
    item.status = status
    item.set = getattr(args, "set", None) or item.id  # singleton set defaults to the id
    item.priority = getattr(args, "priority", None) or "medium"
    item.kind = getattr(args, "kind", None) or "chore"
    item.summary = (getattr(args, "summary", None) or "").strip()
    item.gate_kind = getattr(args, "gate_kind", None)
    item.gate_ref = getattr(args, "gate_ref", None)
    if item.priority not in PRIORITIES:
        sys.stderr.write(
            f"aw backlog new: --priority must be one of {sorted(PRIORITIES)}\n"
        )
        return 2
    if item.kind not in KINDS:
        sys.stderr.write(f"aw backlog new: --kind must be one of {sorted(KINDS)}\n")
        return 2
    if not (item.summary or "").strip():
        sys.stderr.write("aw backlog new: --summary is required\n")
        return 2
    if status == "blocked" and (not item.gate_kind or not item.gate_ref):
        sys.stderr.write(
            "aw backlog new: a blocked item requires --gate-kind and --gate-ref\n"
        )
        return 2

    today = datetime.date.today().strftime("%Y%m%d")
    slug = (
        core.kebab(getattr(args, "slug", None) or item.summary or "item")[:50] or "item"
    )
    filename = f"{today}-{item.set}-01-{item.id}-{slug}.backlog.md"
    dest = _resolve_backlog_root(repo_root) / status / filename
    body = getattr(args, "body", None) or ""
    rendered = _render_item(item, body)

    if not getattr(args, "apply", False):
        sys.stdout.write(f"--- would write {dest} ---\n{rendered}")
        return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    core.atomic_write(dest, rendered)
    sys.stdout.write(f"aw backlog new: wrote {dest}\n")
    return 0


def run_set(args) -> int:
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    target = getattr(args, "path", None)
    new_status = getattr(args, "status", None)
    if not target or new_status not in STATUSES:
        sys.stderr.write(
            f"aw backlog set: --status must be one of {sorted(STATUSES)} and a path is required\n"
        )
        return 2
    src = Path(target)
    if not src.is_absolute():
        src = repo_root / target
    if not src.is_file():
        sys.stderr.write(f"aw backlog set: no such item: {target}\n")
        return 2
    text = src.read_text(encoding="utf-8")
    item = parse_item(text)
    item.status = new_status
    if new_status == "blocked":
        gk = getattr(args, "gate_kind", None)
        gr = getattr(args, "gate_ref", None)
        if not gk or not gr:
            sys.stderr.write(
                "aw backlog set: moving to blocked requires --gate-kind and --gate-ref\n"
            )
            return 2
        item.gate_kind, item.gate_ref = gk, gr
    else:
        item.gate_kind = item.gate_ref = None

    # Rewrite metadata bullets in place; move file to the new status dir; append history.
    body = _strip_metadata_and_history(text)
    rendered = _render_item(item, body)
    # append a transition history record (in addition to the created line _render_item emits,
    # preserve prior history by re-emitting it):
    rendered = _reattach_history(
        text, rendered, f"{new_status}", getattr(args, "message", "") or ""
    )
    # awhistory Order 02: append this transition to the GLOBAL sidecar (full log lives there; the
    # inline block now keeps only the latest record). id6 = item.id.
    if item.id:
        try:
            from agent_workflows import record_history as _rh

            _rh.append(
                repo_root,
                id6=item.id,
                tree="backlog",
                workflow="aw backlog",
                actor="aw backlog",
                message=(
                    getattr(args, "message", "") or f"status -> {new_status}"
                ).strip(),
            )
        except Exception:
            pass
    # awrelease Order 02: set/clear the Blocks-Release gate field when requested (a release id6,
    # 'next', or '-' to clear). Applied after render so _render_item stays untouched. If the item
    # already carries one and --blocks-release is not given, preserve it.
    br = getattr(args, "blocks_release", None)
    if br is not None:
        from agent_workflows import releases as _releases

        rendered = _releases.set_blocks_release_line(rendered, br)
    elif item.blocks_release:
        from agent_workflows import releases as _releases

        rendered = _releases.set_blocks_release_line(rendered, item.blocks_release)

    dest_dir = _resolve_backlog_root(repo_root) / new_status
    dest = dest_dir / src.name
    if not getattr(args, "apply", True):  # set applies by default
        sys.stdout.write(f"--- would move {src} -> {dest} (status {new_status}) ---\n")
        return 0
    dest_dir.mkdir(parents=True, exist_ok=True)
    core.atomic_write(dest, rendered)
    if dest.resolve() != src.resolve():
        src.unlink()
    sys.stdout.write(f"aw backlog set: {src.name} -> {new_status}\n")
    return 0


def _strip_metadata_and_history(text: str) -> str:
    """Return only the free prose body (after the `## Workflow history` section)."""

    parts = text.split("\n## Workflow history", 1)
    if len(parts) < 2:
        return ""
    after = parts[1]
    # body is whatever follows the history block (the next paragraph after the history bullets)
    out_lines: List[str] = []
    in_hist = True
    for line in after.split("\n")[1:]:
        if in_hist and (line.startswith("- ") or not line.strip()):
            continue
        in_hist = False
        out_lines.append(line)
    return "\n".join(out_lines).strip()


def _reattach_history(
    old_text: str, rendered: str, new_status: str, message: str
) -> str:
    """Preserve prior `## Workflow history` records and append one transition record."""

    today = datetime.date.today().isoformat()
    msg = message.strip() or f"status -> {new_status}"
    new_record = f"- {today} set (aw backlog): {msg}"
    # rebuild: metadata block from `rendered` up to its history header, then ONLY the new record, then body.
    # awhistory Order 02: the inline block keeps only the LATEST record; the full chronological log lives
    # in the global .aw/records/history.jsonl sidecar (attention last_history_at reads this latest line).
    head = rendered.split("\n## Workflow history", 1)[0]
    body = ""
    if "\n## Workflow history" in rendered:
        tail = rendered.split("\n## Workflow history", 1)[1]
        body_parts = tail.split("\n\n", 1)
        body = body_parts[1] if len(body_parts) > 1 else ""
    hist_block = new_record
    result = head + "\n## Workflow history\n" + hist_block
    if body.strip():
        result += "\n\n" + body.rstrip()
    return result.rstrip() + "\n"


def run_check(args) -> int:
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    drift: List[core.Drift] = []
    seen_ids: Dict[str, str] = {}
    for f in _iter_items(repo_root):
        text = f.read_text(encoding="utf-8")
        item_drift = validate_item(f, text)
        drift.extend(item_drift)
        pid = parse_item(text).id
        if pid and core.is_valid_id6(pid):
            if pid in seen_ids:
                drift.append(
                    core.Drift(
                        f.name,
                        "backlog.id-duplicate",
                        f"id {pid} also in {seen_ids[pid]}",
                    )
                )
            else:
                seen_ids[pid] = f.name
    if getattr(args, "agent", False):
        sys.stdout.write(core.render_agent_drift(drift))
    else:
        if drift:
            for d in drift:
                sys.stdout.write(f"{d.location}: {d.rule}: {d.detail}\n")
            sys.stdout.write(f"aw backlog check: {len(drift)} violation(s).\n")
        else:
            sys.stdout.write("aw backlog check: all backlog items conform.\n")
    return core.drift_exit_code(drift)
