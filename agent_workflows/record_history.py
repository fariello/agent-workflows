"""Global append-only workflow-history sidecar (spec 20260818-1525-02, Section 3).

ONE file per repo: `.aw/records/history.jsonl`, keyed by id6. Each line is a JSON object
`{id6, date, tree, workflow, actor, message}`. Append-only, so line order is irrelevant and
concurrent-append git merges rarely conflict. Pure (no CLI, no argparse). Consumed by the status
writers (Order 02) and the migration + read verb (Order 03)."""

from __future__ import annotations

import json
import re as _re
from datetime import date as _date
from pathlib import Path
from typing import List, Optional, Tuple as _Tuple

from agent_workflows import artifact_core as _core
from agent_workflows.attention_contract import HISTORY_RECORD_RE as _HISTORY_RECORD_RE

SIDECAR_RELPATH = ".aw/records/history.jsonl"

# Front-matter directive the managed record files carry (spec G4); Order 03 / templates write it.
MANAGED_BY_DIRECTIVE = "- Managed-by: aw (status + history are managed by the aw CLI; do not hand-edit them)"


def history_path(repo_root) -> Path:
    """The ONE GLOBAL history sidecar path for a repo root: `.aw/records/history.jsonl`."""
    return Path(repo_root) / SIDECAR_RELPATH


def append(
    repo_root,
    *,
    id6: str,
    tree: str,
    workflow: str,
    actor: str,
    message: str,
    date: Optional[str] = None,
) -> None:
    """Append ONE history record line to the global sidecar (creating file + parent dir if absent).

    `id6` MUST match `artifact_core.ID6_RE` (else ValueError). `date` defaults to today as YYYYMMDD.
    Fixed key order; utf-8; one JSON object per line followed by `\\n`. Append-only, so order is
    irrelevant."""
    if not _core.ID6_RE.match(id6 or ""):
        raise ValueError(f"record_history.append: {id6!r} is not a valid id6")
    if date is None:
        date = _date.today().strftime("%Y%m%d")
    rec = {
        "id6": id6,
        "date": date,
        "tree": tree,
        "workflow": workflow,
        "actor": actor,
        "message": message,
    }
    p = history_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=True) + "\n")


def read_for(repo_root, id6: str) -> List[dict]:
    """Every history record for `id6`, in file (chronological append) order. `[]` if the sidecar is
    missing; skips any line that is not valid JSON."""
    return [r for r in read_all(repo_root) if r.get("id6") == id6]


def read_all(repo_root) -> List[dict]:
    """Every history record in the sidecar (all id6s), in file order. `[]` when missing; skips any
    line that fails `json.loads`."""
    p = history_path(repo_root)
    if not p.is_file():
        return []
    out: List[dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


# --------------------------------------------------------------------------------------
# awhistory Order 03: one-time idempotent inline->sidecar migration + slim (spec R4, AC3)
# --------------------------------------------------------------------------------------

# id6 line + the record trees to walk (first path segment under .aw/records/ is the sidecar `tree`).
_ID_LINE_RE = _re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_HIST_HEADING = "## Workflow history"
# CRITICAL: `plans` is DELIBERATELY EXCLUDED. IPDs keep their FULL inline `## Workflow history`
# because `ipd_lint` IPD-S405 REQUIRES an inline `executed` entry at post-transition; folding+slimming
# plan history would delete that entry across every executed plan and break the whole plans tree's
# lint. The IPD lifecycle owns plan history; the sidecar covers the other record types only.
_RECORD_TREES = (
    "specs",
    "research",
    "backlog",
    "prompts",
    "walkthroughs",
    "roadmaps",
    "releases",
)
# Parse "workflow" + "actor" out of the free tail when it matches "<workflow> (<actor>): <message>".
_TAIL_RE = _re.compile(r"^(?P<workflow>\S+)\s*\((?P<actor>[^)]*)\):\s*(?P<message>.*)$")


def _record_id6(text: str):
    m = _ID_LINE_RE.search(text)
    return m.group(1) if m else None


def _inline_history_records(text: str) -> List[str]:
    """Return the raw '- YYYY-MM-DD ...' record lines inside the file's ## Workflow history block."""
    out: List[str] = []
    in_hist = False
    for line in text.split("\n"):
        if line.strip() == _HIST_HEADING:
            in_hist = True
            continue
        if in_hist:
            if line.startswith("## "):
                break
            if _HISTORY_RECORD_RE.match(line):
                out.append(line)
    return out


def _parse_record_line(line: str) -> _Tuple[str, str, str, str]:
    """(date, workflow, actor, message) from one record line. date is guaranteed by the caller."""
    m = _HISTORY_RECORD_RE.match(line)
    date = m.group("date")
    tail = line[len("- " + date) :].strip()
    tm = _TAIL_RE.match(tail)
    if tm:
        return (
            date,
            tm.group("workflow"),
            tm.group("actor"),
            tm.group("message").strip(),
        )
    return date, "", "", tail


def _iter_record_files(repo_root: Path):
    """Yield every record .md file across the known trees (skips index/readme sentinels)."""
    base = Path(repo_root) / ".aw" / "records"
    for tree in _RECORD_TREES:
        d = base / tree
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.md")):
            if p.name in ("README.md", "INDEX.md", "STATUS.md"):
                continue
            yield tree, p


def _slim_inline_history(path: Path, text: str, records: List[str]) -> None:
    """Rewrite path's ## Workflow history block to keep ONLY the latest (last-in-order) record line.
    No-op if <=1 record. Preserves everything outside the block (spec OQ-2: keep the latest one)."""
    if len(records) <= 1:
        return
    keep = records[-1]
    lines = text.split("\n")
    out: List[str] = []
    in_hist = False
    wrote_keep = False
    for line in lines:
        if line.strip() == _HIST_HEADING:
            in_hist = True
            out.append(line)
            continue
        if in_hist:
            if line.startswith("## "):
                in_hist = False
                out.append(line)
                continue
            if _HISTORY_RECORD_RE.match(line):
                if not wrote_keep:
                    out.append(keep)
                    wrote_keep = True
                continue
            out.append(line)
            continue
        out.append(line)
    path.write_text("\n".join(out), encoding="utf-8")


def migrate_inline_history(repo_root: Path, apply: bool = False) -> int:
    """Fold every inline ## Workflow history record across the record trees (EXCEPT plans) into the
    global sidecar (idempotent, keyed on id6+date+message), then slim each file's inline block to its
    latest ONE record. apply=False (default) previews and writes nothing; returns the count of records
    that WOULD be (apply=False) or WERE (apply=True) newly folded."""
    repo_root = Path(repo_root)
    existing = {
        (r.get("id6"), r.get("date"), r.get("message")) for r in read_all(repo_root)
    }
    folded = 0
    for tree, path in _iter_record_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        id6 = _record_id6(text)
        if not id6:
            continue
        records = _inline_history_records(text)
        if not records:
            continue
        for line in records:
            date, workflow, actor, message = _parse_record_line(line)
            key = (id6, date, message)
            if key in existing:
                continue
            if apply:
                append(
                    repo_root,
                    id6=id6,
                    date=date,
                    tree=tree,
                    workflow=workflow,
                    actor=actor,
                    message=message,
                )
            existing.add(key)
            folded += 1
        if apply:
            _slim_inline_history(path, text, records)
    return folded
