"""`aw doctor`: a read-only deep repo inspector that AGGREGATES existing check signals (attention
validity incl. malformed names + status-vs-location + duplicate-id + unclassified-tree, git state,
version drift) into one Drift-based report. Composes existing checks; reimplements none; writes
nothing. Reuses the shared Drift / --agent / drift_exit_code convention (artifact_core)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from agent_workflows import artifact_core as core
from agent_workflows import attention as attention_mod


def run_doctor(repo_root: Path) -> List[core.Drift]:
    """Aggregate every existing check signal into one List[Drift]. Read-only, deterministic (sorted
    by (location, rule)). Each probe is wrapped so one failing probe degrades to a single
    `doctor.probe-failed` drift, never aborting the report."""
    drift: List[core.Drift] = []
    drift.extend(_attention_drift(repo_root))
    drift.extend(_git_drift(repo_root))
    drift.extend(_version_drift(repo_root))
    return sorted(drift, key=lambda d: (d.location, d.rule))


def _attention_drift(repo_root: Path) -> List[core.Drift]:
    """Reuse attention.scan: it already emits malformed-name, status-vs-location, duplicate-id, and
    unclassified-tree drift. The attention view's validity == (no drift)."""
    try:
        _items, drift = attention_mod.scan(repo_root)
        return list(drift)
    except Exception as exc:
        return [core.Drift("<attention>", "doctor.probe-failed", str(exc)[:120])]


def _git_drift(repo_root: Path) -> List[core.Drift]:
    """Reuse engine.classify_git_state over `git status --porcelain`. Read-only: no pull, no
    interactive path."""
    import subprocess

    from agent_workflows import engine

    try:
        if not engine.git_available(repo_root):
            return []
        porc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            shell=False,
        ).stdout
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            shell=False,
        ).stdout.strip()
        state = engine.classify_git_state(
            porc, behind=0, has_tracking=True, branch=branch, tracking_branch=""
        )
        out: List[core.Drift] = []
        if getattr(state, "tracked_dirty", 0):
            out.append(
                core.Drift(
                    "<git>",
                    "doctor.git-dirty",
                    f"{state.tracked_dirty} uncommitted tracked change(s)",
                )
            )
        if getattr(state, "untracked", 0):
            out.append(
                core.Drift(
                    "<git>",
                    "doctor.git-untracked",
                    f"{state.untracked} untracked file(s)",
                )
            )
        return out
    except Exception as exc:
        return [core.Drift("<git>", "doctor.probe-failed", str(exc)[:120])]


def _version_drift(repo_root: Path) -> List[core.Drift]:
    """Reuse versioning.status comparing the installed VERSION to the packaged (source) version.
    'stale'/'dev'/'unknown'/'not-installed' become one `doctor.version-*` drift; else none."""
    try:
        from agent_workflows import engine, versioning

        vfile = repo_root / ".aw" / "VERSION"
        if not vfile.is_file():
            vfile = repo_root / ".agents" / "VERSION"
        target = vfile.read_text(encoding="utf-8").strip() if vfile.is_file() else None
        try:
            packaged = versioning.resolve_version(engine.resolve_source_root(None))
        except Exception:
            packaged = ""
        st = versioning.status(target, packaged)
        # 'dev' is normal on a development checkout (not drift the user must fix); only flag genuine
        # currency problems.
        if st in ("stale", "unknown", "not-installed"):
            return [
                core.Drift(
                    "<version>",
                    f"doctor.version-{st}",
                    f"installed={target!r} packaged={packaged!r}",
                )
            ]
        return []
    except Exception as exc:
        return [core.Drift("<version>", "doctor.probe-failed", str(exc)[:120])]


def run(args) -> int:
    """`aw doctor` entrypoint: run every probe, print findings (or `no findings`), return the
    standard 0/1 exit code. `--agent` emits tab-separated `location\\trule\\tdetail`."""
    import os

    repo_root = Path(getattr(args, "dir", None) or os.getcwd())
    drift = run_doctor(repo_root)
    if getattr(args, "agent", False) or getattr(args, "as_agent", False):
        sys.stdout.write(core.render_agent_drift(drift))
    elif not drift:
        sys.stdout.write("aw doctor: no findings.\n")
    else:
        for d in drift:
            sys.stdout.write(f"- {d.location}: {d.rule} {d.detail}\n")
    return core.drift_exit_code(drift)
