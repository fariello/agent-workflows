"""OPT-IN local pre-commit gate: refuse a staged non-append or invalid change to `meta/*.jsonl`.

Spec `4sd62s` 4.8 requires a pre-commit hook that refuses a staged change to
`.aw/records/meta/*.jsonl` unless the staged bytes are the HEAD bytes plus whole new lines
that the `artifact_meta` loader accepts. Spec `4sd62s` 4.3 requires that no code outside
`artifact_meta` opens or parses a log file.

This module therefore inspects only staged paths under the repository's `meta/` directory
and delegates every byte and event check to `artifact_meta.check_staged_log_append(id6)`.
In phase B no log files exist in this repository, so the hook is a fast no-op here.

Honest limits: git hooks are local, not cloned by default, and bypassable with `--no-verify`.
This hook is opt-in local prevention; the portable authority is `aw check meta` and CI.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

_RULE = "check.meta-log-append"


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


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the staged metadata-log append gate.

    Returns ``(exit_code, messages)`` where ``exit_code == 0`` means acceptable or no-op
    and ``exit_code == 1`` means one or more staged `meta/*.jsonl` changes were refused.
    """
    from agent_workflows import artifact_core as _core
    from agent_workflows import artifact_meta as _meta
    from agent_workflows import check_engine as _ce
    from agent_workflows import project_context as _proj_ctx

    start = Path(repo_root).resolve() if repo_root is not None else Path(".").resolve()
    root = _repo_root(start)
    if not (root / ".git").exists():
        return 0, []

    ctx = _ce._git_read_at_context(root)
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
        repo_dir, ["diff", "--cached", "--name-status", "--", meta_dir]
    )
    if rc != 0 or not out.strip():
        return 0, []

    messages: List[str] = []
    seen_ids: set[str] = set()
    with _meta.ephemeral_if_uninitialized():
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            rel_path = parts[-1].strip().replace("\\", "/")
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
            messages.extend(_meta.check_staged_log_append(stem, project_context=ctx))

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
