"""Global append-only workflow-history sidecar (spec 20260818-1525-02, Section 3).

ONE file per repo: `.aw/records/history.jsonl`, keyed by id6. Each line is a JSON object
`{id6, date, tree, workflow, actor, message}`. Append-only, so line order is irrelevant and
concurrent-append git merges rarely conflict. Pure (no CLI, no argparse). Consumed by the status
writers (Order 02) and the migration + read verb (Order 03).

The sidecar ALSO carries an additive, non-authoritative RENAME/regroup ledger (IPD 52zgqr,
unifyfileio Order 04): every applied `aw rename`/`aw group` that changes a name appends ONE record
via `record_rename`/`append_rename`. A rename record is a SUPERSET of a status record - it reuses the
same key order/shape and adds `verb` (rename|group), `from_name`/`to_name` (basenames), and
`key_kind` (id6|synthetic). Status readers/migration key only on id6/date/message and ignore the
extra keys, so the addition is backward-compatible. The ledger is NON-AUTHORITATIVE: no aw command's
correctness depends on it (deleting the sidecar changes only what an audit query can report), and the
emit is failure-isolated so a ledger problem never breaks a rename. Endpoint cases (OQ-01): id6->id6
and id6-less->id6 key on the (new) id6; both-id6-less uses a deterministic synthetic key tagged
`key_kind:"synthetic"` for a future id6-rollout to reconcile."""

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
# Additive rename/regroup ledger (IPD 52zgqr, unifyfileio Order 04).
#
# A RENAME record is a SUPERSET of a status record: it reuses the exact {id6,date,tree,workflow,
# actor,message} key order/shape and adds optional `verb` (rename|group), `from_name`/`to_name`
# (basenames), and `key_kind` (id6|synthetic). Status records carry none of the extra keys, so
# `read_all`/`read_for`/`migrate_inline_history` (which key only on id6/date/message and ignore
# unknown keys) are unaffected. The ledger is strictly ADDITIVE and NON-AUTHORITATIVE: no aw
# command's correctness depends on it (deleting the sidecar changes only what an audit query can
# report, never whether a rename/citation-rewrite/check succeeds), so every writer here is
# failure-isolated by its callers.
#
# Endpoint cases (OQ-01, human-resolved): Case 1 (id6->id6) and Case 2 (id6-less->id6) key on the
# real (new) id6 via append_rename's id6 path; Case 3 (id6-less->id6-less) uses a deterministic
# SYNTHETIC key (a normalized earliest-known-name token) tagged `key_kind:"synthetic"` so a future
# id6-rollout can reconcile it.
# --------------------------------------------------------------------------------------

# A synthetic key normalizes an id6-less name to a stable token: strip a trailing `.md`/facet and any
# leading date, lowercase-kebab the remainder. Deterministic for the same artifact's earliest name.
_SYNTH_STRIP_RE = _re.compile(r"[^a-z0-9]+")


def _synthetic_key(name: str) -> str:
    """A deterministic synthetic key for an id6-less artifact, derived from a filename basename.

    Drops a trailing `.md` and any `.<facet>`, drops a leading `YYYYMMDD-` (or `YYYYMMDD-HHMM-NN-`)
    date/order prefix, then lowercase-kebabs the slug remainder. Prefixed `synthetic:` so it can
    never collide with a real 6-char id6 key. Stable for the same slug across re-slugs is NOT
    guaranteed (a re-slug changes the slug); the key is stable for a GIVEN name, which is what
    ``read_renames_for`` needs to retrieve a specific synthetic record."""

    base = name[:-3] if name.endswith(".md") else name
    base = base.split(".")[0]  # drop any dotted facet(s)
    # Drop a leading date (YYYYMMDD) and an optional -HHMM-NN.
    base = _re.sub(r"\A\d{8}(?:-\d{4}-\d{2})?-", "", base)
    slug = _SYNTH_STRIP_RE.sub("-", base.lower()).strip("-")
    return "synthetic:" + (slug or "unknown")


def append_rename(
    repo_root,
    *,
    id6: str,
    tree: str,
    verb: str,
    actor: str,
    from_name: str,
    to_name: str,
    message: Optional[str] = None,
    date: Optional[str] = None,
    key_kind: str = "id6",
) -> None:
    """Append ONE rename/regroup record to the global sidecar (additive, non-authoritative).

    `id6` is the record key. For the default ``key_kind="id6"`` it MUST match ``artifact_core.ID6_RE``
    (else ValueError - identical to ``append``'s contract; never silently write a malformed record).
    ``key_kind="synthetic"`` (Case 3 ONLY) accepts a synthetic key token (produced by
    :func:`_synthetic_key`) and skips the id6 validation, tagging the record so it is distinguishable
    from real-id6 records. `verb` is ``rename`` or ``group``; `from_name`/`to_name` are basenames.
    """

    if key_kind == "id6":
        if not _core.ID6_RE.match(id6 or ""):
            raise ValueError(
                f"record_history.append_rename: {id6!r} is not a valid id6"
            )
    elif key_kind != "synthetic":
        raise ValueError(f"record_history.append_rename: bad key_kind {key_kind!r}")
    if date is None:
        date = _date.today().strftime("%Y%m%d")
    # Preserve the status-record key order, then append the rename-only keys (superset).
    rec = {
        "id6": id6,
        "date": date,
        "tree": tree,
        "workflow": f"aw {verb}",
        "actor": actor,
        "message": message or f"{verb} {from_name} -> {to_name}",
        "verb": verb,
        "from_name": from_name,
        "to_name": to_name,
    }
    if key_kind != "id6":
        rec["key_kind"] = key_kind
    p = history_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=True) + "\n")


def read_renames_for(repo_root, key: str) -> List[dict]:
    """Every RENAME record (has a `from_name`) for `key` (a real id6 OR a synthetic key), in file
    order. Status records (no `from_name`) are excluded."""
    return [r for r in read_all(repo_root) if r.get("id6") == key and "from_name" in r]


def _endpoint_id6(name: str) -> Optional[str]:
    """The id6 of an artifact filename endpoint via the Order 01 naming authority (clustered slot)
    or research grammar, else None (an id6-less legacy name)."""

    from agent_workflows import artifact_naming as _naming

    m = _naming.parse_clustered(name)
    if m is not None:
        return m.group("id6")
    # Research names carry the id6 in the same core position but with `.<model>.<kind>` facets.
    try:
        from agent_workflows import research_contract as _rc

        parsed, _err = _rc.parse_name(name)
        if parsed is not None:
            return parsed.id6
    except Exception:
        pass
    return None


def record_rename(
    repo_root,
    *,
    tree: str,
    verb: str,
    actor: str,
    from_name: str,
    to_name: str,
    message: Optional[str] = None,
    date: Optional[str] = None,
) -> None:
    """Record a rename/regroup by endpoint case (OQ-01), FAILURE-ISOLATED (never raises to the
    caller, so a ledger problem can never fail or roll back the rename).

    Case 1 (id6 -> id6) and Case 2 (id6-less -> id6): key on the NEW id6 (Case 2 preserves the old
    id6-less name in `from_name` - the highest-value migration record). Case 3 (both id6-less): a
    deterministic synthetic key tagged `key_kind:"synthetic"`. A no-op (from==to) records nothing.
    """

    try:
        if from_name == to_name:
            return
        new_id6 = _endpoint_id6(to_name)
        if new_id6 is not None:
            # Case 1 or 2: the new name has an id6 -> key on it.
            append_rename(
                repo_root,
                id6=new_id6,
                tree=tree,
                verb=verb,
                actor=actor,
                from_name=from_name,
                to_name=to_name,
                message=message,
                date=date,
                key_kind="id6",
            )
            return
        # Case 3: both endpoints id6-less -> synthetic key from the EARLIEST known name (from_name).
        append_rename(
            repo_root,
            id6=_synthetic_key(from_name),
            tree=tree,
            verb=verb,
            actor=actor,
            from_name=from_name,
            to_name=to_name,
            message=message,
            date=date,
            key_kind="synthetic",
        )
    except Exception:
        # Additive, non-authoritative: a ledger failure must NEVER break the rename.
        pass


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
