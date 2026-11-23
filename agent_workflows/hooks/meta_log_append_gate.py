"""OPT-IN local pre-commit gate: refuse a staged non-append or invalid change to `meta/*.jsonl`.

Spec `4sd62s` 4.8 requires a pre-commit hook that refuses a staged change to
`.aw/records/meta/*.jsonl` unless the staged bytes are the HEAD bytes plus whole new lines
that the `artifact_meta` loader accepts. Spec `4sd62s` 4.3 requires that no code outside
`artifact_meta` opens or parses a log file.

This module therefore inspects only staged paths under the repository's `meta/` directory
and delegates every byte and event check to `artifact_meta.check_staged_log_append(id6)`.
In phase B no log files exist in this repository, so the hook is a fast no-op here.

TERMINAL-LOG RULES (IPD `6jd6mh` E-04, spec `4sd62s` 5.2 step 4a, OQ-30, AC-16 case 2). Once a
plan's log has reached a terminal status (`plans.TERMINAL`) at HEAD, an append that passes the loader
is still refused unless every event in it is one a terminal log accepts: `note`, `review`, `turn`
(once spec `37am1y` registers it), `rename` with a verb in `artifact_meta.RENAME_VERBS` (with a `set`
of `set`/`order` in the same append), and a `set`/`unset` of `short_description`. Status, the
attestations (`readiness`, `approval`, `coverage`), `scope_result`, `blocks_release` and every other
field stay frozen. The one exception is an append whose `transition` carries the recorded
`allow-terminal-reopen` override, which leaves the terminal status by the documented escape hatch
(the loader already requires that override for the edge). The rules read only events that
`artifact_meta.read_at` decoded, so this module still never opens a log itself. They apply only to a
staged `meta/*.jsonl` path, so they are dormant in a repository with no logs.

Honest limits: git hooks are local, not cloned by default, and bypassable with `--no-verify`.
This hook is opt-in local prevention; the portable authority is `aw check meta` and CI.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_RULE = "check.meta-log-append"

# Ops a terminal log accepts with no further condition (OQ-30). `turn` is reserved today
# (`artifact_meta.RESERVED_OPS`), so the loader refuses it before this rule runs; it is listed so the
# rule needs no edit once spec `37am1y` registers it.
_TERMINAL_FREE_OPS = frozenset(("note", "review", "turn"))
_TERMINAL_SHORT_DESCRIPTION = frozenset(("short_description",))
_TERMINAL_RENAME_SET_FIELDS = frozenset(("set", "order"))
_TERMINAL_REOPEN_OVERRIDE = "allow-terminal-reopen"


def _git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _repo_root(start: Path) -> Path:
    rc, out, _err = _git(start, ["rev-parse", "--show-toplevel"])
    if rc == 0 and out.strip():
        return Path(out.strip())
    return start.resolve()


def _terminal_statuses(record_type: Optional[str]) -> frozenset:
    """The statuses whose log is frozen to the OQ-30 appends (plans only; see DECISION 6jd6mh-D3)."""
    if record_type != "ipd":
        return frozenset()
    from agent_workflows import plans as _plans

    return frozenset(_plans.TERMINAL)


def _terminal_append_refusal(
    rel_log: str, status: str, events: List[Dict[str, Any]]
) -> Optional[str]:
    """Return a refusal for ONE append on a log whose status is terminal, or None if OQ-30 allows it."""
    from agent_workflows import artifact_meta as _meta

    trans = next((e for e in events if e.get("op") == "transition"), None)
    if trans is not None:
        if _TERMINAL_REOPEN_OVERRIDE in (trans.get("overrides") or []):
            return None
        return (
            f"{rel_log}: append {events[0].get('append')} transitions a terminal "
            f"{status!r} log to {trans.get('to')!r}; a terminal log's status is frozen "
            "(spec 4sd62s OQ-30). Reopen only through `aw ipd set <status> <id6> "
            "--allow-terminal-reopen`, which records the override."
        )
    has_rename = any(
        e.get("op") == "rename" and e.get("verb") in _meta.RENAME_VERBS for e in events
    )
    for ev in events:
        op = ev.get("op")
        if op == "review" and ev.get("readiness"):
            # A gate review's `readiness` is replayed into the field OQ-30 freezes (DECISION 6jd6mh-D4).
            return (
                f"{rel_log}: append {ev.get('append')} records a review carrying `readiness` on a "
                f"terminal {status!r} log; a terminal log accepts a `review` but its `readiness` "
                "attestation stays frozen (spec 4sd62s OQ-30)."
            )
        if op in _TERMINAL_FREE_OPS:
            continue
        if op == "rename" and ev.get("verb") in _meta.RENAME_VERBS:
            continue
        if op in ("set", "unset"):
            raw = ev.get("fields")
            keys = set(raw.keys() if isinstance(raw, dict) else (raw or []))
            allowed = set(_TERMINAL_SHORT_DESCRIPTION)
            if op == "set" and has_rename:
                allowed |= _TERMINAL_RENAME_SET_FIELDS
            frozen = sorted(keys - allowed)
            if not frozen:
                continue
            return (
                f"{rel_log}: append {ev.get('append')} {op}s frozen field(s) "
                f"{', '.join(frozen)} on a terminal {status!r} log; a terminal log accepts only "
                "`note`, `review`, `turn`, `rename` (verb archive, rename or group, with a `set` of "
                "`set`/`order` in the same append) and a `set`/`unset` of `short_description` "
                "(spec 4sd62s OQ-30)."
            )
        return (
            f"{rel_log}: append {ev.get('append')} adds a `{op}` event to a terminal {status!r} "
            "log; a terminal log accepts only `note`, `review`, `turn`, `rename` (verb archive, "
            "rename or group) and a `set`/`unset` of `short_description` (spec 4sd62s OQ-30)."
        )
    return None


def terminal_log_refusals(id6: str, rel_log: str, *, project_context: Any) -> List[str]:
    """OQ-30 refusals for the events a staged ``meta/<id6>.jsonl`` appends after HEAD.

    Call only after ``artifact_meta.check_staged_log_append`` accepted the log, so HEAD's events are
    a prefix of the staged ones. Walks the appended events append by append, tracking the status
    each append starts from, so an append that follows a transition into a terminal status in the
    same commit is held to the same rules as one appended in a later commit.
    """
    from agent_workflows import artifact_meta as _meta

    head = _meta.read_at(id6, "HEAD", project_context=project_context)
    if head.kind != "ok" or head.state is None:
        return []
    staged = _meta.read_at(id6, ":0:", project_context=project_context)
    if staged.kind != "ok" or staged.state is None:
        return []
    terminal = _terminal_statuses(staged.state.type)
    if not terminal:
        return []
    head_seq = int(head.state.last_seq or 0)
    appended = [e for e in staged.history if int(e.get("seq", 0)) > head_seq]
    groups: Dict[Any, List[Dict[str, Any]]] = {}
    for ev in appended:
        groups.setdefault(ev.get("append"), []).append(ev)
    status = head.state.status
    refusals: List[str] = []
    for _app, evs in groups.items():
        if status in terminal:
            reason = _terminal_append_refusal(rel_log, status, evs)
            if reason is not None:
                refusals.append(reason)
        for ev in evs:
            if ev.get("op") == "transition" and ev.get("to"):
                status = ev["to"]
    return refusals


def _staged_meta_logs(root: Path, ctx: Any) -> Tuple[Path, str, List[str]]:
    """Return ``(repo_dir, meta_prefix, staged meta paths)`` for the staged `meta/` changes."""
    from agent_workflows import project_context as _proj_ctx

    records_root = Path(ctx.logical_roots["records"])
    repo_dir = _proj_ctx.record_git_root(records_root) or root
    try:
        rel_records = str(
            records_root.resolve().relative_to(repo_dir.resolve())
        ).replace("\\", "/")
    except Exception:
        rel_records = ".aw/records"

    meta_dir = (
        "meta" if not rel_records or rel_records == "." else f"{rel_records}/meta"
    )
    meta_prefix = f"{meta_dir}/"

    rc, out, _err = _git(
        repo_dir,
        [
            "-c",
            "core.quotepath=false",
            "diff",
            "--cached",
            "--no-renames",
            "--name-status",
            "--",
            meta_dir,
        ],
    )
    if rc != 0 or not out.strip():
        return repo_dir, meta_prefix, []
    paths: List[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        paths.append(parts[-1].strip().replace("\\", "/"))
    return repo_dir, meta_prefix, paths


def staged_log_messages(root: Path, ctx: Any = None) -> List[str]:
    """Every refusal for the staged `meta/*.jsonl` changes under ``root`` (shared with `aw check`).

    The ONE predicate behind both this hook and `check_engine.check_staged_meta_log_append`, so
    the local hook and the portable check cannot disagree. Empty when no `meta/` path is staged.
    """
    from agent_workflows import artifact_core as _core
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import check_engine as _ce

    ctx = ctx or _ce._git_read_at_context(root)
    _repo_dir, meta_prefix, paths = _staged_meta_logs(root, ctx)
    if not paths:
        return []

    messages: List[str] = []
    seen_ids: set[str] = set()
    with _meta.ephemeral_if_uninitialized():
        for rel_path in paths:
            if not (rel_path.startswith(meta_prefix) and rel_path.endswith(".jsonl")):
                continue
            stem = rel_path[len(meta_prefix) : -len(".jsonl")]
            if "/" in stem or not _core.ID6_RE.fullmatch(stem):
                messages.append(
                    f"{rel_path}: staged metadata log filename must be `<id6>.jsonl` directly "
                    f"under `{meta_prefix}` (got {stem!r})."
                )
                continue
            if stem in seen_ids:
                continue
            seen_ids.add(stem)
            reasons = _meta.check_staged_log_append(stem, project_context=ctx)
            if not reasons:
                reasons = terminal_log_refusals(stem, rel_path, project_context=ctx)
            messages.extend(reasons)
    return messages


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the staged metadata-log append gate.

    Returns ``(exit_code, messages)`` where ``exit_code == 0`` means acceptable or no-op
    and ``exit_code == 1`` means one or more staged `meta/*.jsonl` changes were refused.
    """
    start = Path(repo_root).resolve() if repo_root is not None else Path(".").resolve()
    root = _repo_root(start)
    if not (root / ".git").exists():
        return 0, []

    messages = staged_log_messages(root)
    if messages:
        return 1, messages
    return 0, []


def main(argv: Optional[List[str]] = None, *, args: Optional[object] = None) -> int:
    """CLI entry for `aw meta-log-append-gate`.

    Emits an `aw.agent/v1` envelope on `--agent` or JSON on `--json`. In human mode,
    prints refusals to stderr and returns exit code 0 (acceptable/no-op) or 1 (refused).
    """
    import sys
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        select_output,
    )

    if args is None and argv:
        import types

        args = types.SimpleNamespace(
            agent="--agent" in argv,
            json="--json" in argv,
        )

    ctx = select_output(args)
    exit_code, messages = check()

    if ctx.is_agent or ctx.is_json:
        diagnostics: List[Diagnostic] = []
        for m in messages:
            loc = "meta-log-append-gate"
            det = m
            if ": " in m:
                loc, det = m.split(": ", 1)
            diagnostics.append(Diagnostic(location=loc, rule=_RULE, detail=det))
        if exit_code != 0 and not diagnostics:
            diagnostics.append(
                Diagnostic(
                    location="meta-log-append-gate",
                    rule=_RULE,
                    detail="gate refused",
                )
            )
        res = CommandResult(
            command="meta-log-append-gate",
            status="clean" if exit_code == 0 else "findings",
            exit_code=exit_code,
            summary=(
                "meta-log-append-gate: gate passed"
                if exit_code == 0
                else f"meta-log-append-gate: refused ({len(messages)} finding(s))"
            ),
            diagnostics=diagnostics,
        )
        return get_renderer(ctx).emit(res, ctx)

    if messages:
        sys.stderr.write(
            "aw meta-log-append gate REFUSED this commit (local prevention; a staged "
            "`meta/*.jsonl` change is not a valid append-only event addition):\n"
        )
        for m in messages:
            sys.stderr.write(f"  - {m}\n")
        sys.stderr.write(
            "(This is a LOCAL best-effort OPT-IN hook; `--no-verify` bypasses it, it is not "
            "cloned by default, and `aw check meta` / CI is the portable authority.)\n"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
