#!/usr/bin/env python3
"""Rehearse an agent-workflows install/update/migrate against a DISPOSABLE copy of a real repo.

WHY THIS EXISTS
---------------
Every install test in ``tests/`` starts from a fresh ``git init`` or a hand-seeded legacy
tree. No test has ever installed OVER a previous version's real on-disk state, which is the
only path an actual user takes: nobody gets a fresh install, they get an upgrade over a tree
that a prior version wrote, plus whatever drift accumulated since (hand-edited managed
blocks, half-finished migrations, stale backups, untracked working material). Review
``8fhjjc`` recorded that gap as HIGH ("THE UPGRADE PATH WAS NEVER VALIDATED, ONLY THE FRESH
PATH") and it is still open. This harness closes it EMPIRICALLY: it copies a real repo, runs
the real installer against the copy, and leaves the result on disk to explore.

WHAT IT IS NOT
--------------
This is a MAINTAINER REHEARSAL RIG, not part of the shipped surface and not a pytest suite.
It deliberately makes no assertions about what a correct upgrade looks like; it produces
evidence a human or agent then judges. ``tests/test_aw_upgrade_test.py`` tests THIS FILE's
safety invariants, not the upgrade outcomes it observes.

THE FOUR SAFETY INVARIANTS
--------------------------
A tool that copies real repositories and runs a mutating installer on them can damage real
work in four distinct ways. Each is closed HERE, by construction, and each is covered by a
test, because "be careful" is not a safety mechanism:

1. NEVER MUTATE THE SOURCE. The source repo is only ever read. The copy is made with
   ``cp -a`` (or ``git clone --local``), never with a hardlink copy: ``cp -al`` would be
   cheap, but any in-place truncation by the installer would then corrupt the original.
   Hardlink copying is not offered at all, not merely defaulted off.
2. NEVER PUSH. A ``cp -a`` copy carries ``.git`` verbatim, INCLUDING remotes, so an
   installer or agent that pushed would push to the real upstream. Every sandbox has its
   remotes REMOVED immediately after the copy and before any install runs, and the removal
   is verified. ``git config --local`` also gets a poisoned push URL so a re-added remote
   still cannot reach a network.
3. NEVER POLLUTE THE REAL INVENTORY. ``aw`` discovers repos by scanning configured search
   roots, and writes an ``installed`` list to the user's real
   XDG config. A sandbox created inside a scanned root would become a managed repo and could
   be swept into a later ``aw install all``. So sandboxes live OUTSIDE the scan roots by
   default, and every ``aw`` invocation runs with ``XDG_CONFIG_HOME`` and ``AW_HOME``
   redirected into the sandbox, so the real config file is never opened for writing.
4. NEVER DELETE ANYTHING BUT OUR OWN SANDBOXES. ``clean`` refuses any path that does not
   carry the sandbox marker file, so a mistyped path cannot delete a real repo.

USAGE
-----
    tools/aw_upgrade_test.py list                     # candidate source repos + versions
    tools/aw_upgrade_test.py new <repo>             # copy + upgrade + report
    tools/aw_upgrade_test.py new <repo> --no-run    # copy only, upgrade by hand later
    tools/aw_upgrade_test.py new <repo> --strategy clone   # cheap copy for a huge repo
    tools/aw_upgrade_test.py new <repo> -- --to-aw --preset private-target
    tools/aw_upgrade_test.py sandboxes                # what sandboxes exist
    tools/aw_upgrade_test.py probe <sandbox>          # re-probe state (idempotent, read-only)
    tools/aw_upgrade_test.py env <sandbox>            # shell exports to explore it safely
    tools/aw_upgrade_test.py clean --all              # remove sandboxes (marker-gated)

Everything after a bare ``--`` is passed through to ``aw install`` verbatim, so any install
flag combination can be rehearsed without this tool needing to know about it.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Marker written at the root of every sandbox. ``clean`` refuses to delete a directory that
#: does not carry it, which is what makes a mistyped path a no-op instead of a catastrophe.
MARKER_NAME = ".aw-upgrade-test.json"

#: Suffix used to build the sandbox directory name: ``<repo>.aw-upgrade-test.<timestamp>``.
SANDBOX_INFIX = "aw-upgrade-test"

#: Name of the sandbox root directory, created under the resolved sandbox BASE.
SANDBOX_ROOT_NAME = "aw-upgrade-tests"


def default_sandbox_root() -> Path:
    """Resolve the default sandbox root, OUTSIDE any configured discovery search root.

    A sandbox placed directly under a search root would be discovered as a managed repo and
    could be swept into a later ``aw install all`` (invariant 3). The default therefore nests
    it one level deeper, under a ``tmp/`` subdirectory of the first search root, which the
    non-recursive immediate-children scan cannot reach. ``AW_UPGRADE_TEST_ROOT`` overrides it,
    and ``--dest`` overrides that.

    Deliberately COMPUTED rather than hardcoded: a literal path here would bake one machine's
    directory layout into a tracked file, which is both wrong elsewhere and exactly what the
    leak-sanitizer rejects.
    """

    env_root = os.environ.get("AW_UPGRADE_TEST_ROOT")
    if env_root:
        return Path(env_root).expanduser()
    roots = search_roots(fallback_to_home=False)
    base = roots[0] if roots else Path(tempfile.gettempdir())
    return base / "tmp" / SANDBOX_ROOT_NAME


#: Locations an installed VERSION file can occupy, newest layout first. Mirrors
#: ``engine.read_installed_version`` so this tool reports the same number the installer does.
VERSION_LOCATIONS = (
    ".aw/system/VERSION",
    ".aw/system/workflows/VERSION",
    ".agents/workflows/VERSION",
)

#: An unroutable push URL. Belt to the remote-removal braces: if anything re-adds a remote
#: inside a sandbox, a push still cannot reach the real upstream.
BLACKHOLE_PUSH_URL = "file:///dev/null/aw-upgrade-test-refuses-to-push"


class HarnessError(RuntimeError):
    """A rehearsal cannot proceed safely. Always fail closed, never half-do the work."""


# ---------------------------------------------------------------------------
# Small process helpers
# ---------------------------------------------------------------------------


def run(
    cmd: Sequence[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Run a command capturing output; raise HarnessError on failure when check."""

    proc = subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise HarnessError(
            f"command failed ({proc.returncode}): {' '.join(shlex.quote(c) for c in cmd)}\n"
            f"{proc.stdout}"
        )
    return proc


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return run(["git", *args], cwd=repo, check=check)


def git_out(repo: Path, *args: str) -> str:
    return git(repo, *args, check=False).stdout.strip()


def is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


# ---------------------------------------------------------------------------
# Source repo inspection (read-only)
# ---------------------------------------------------------------------------


def installed_version(repo: Path) -> Tuple[Optional[str], Optional[str]]:
    """Return (version, relative_path) for the repo's installed framework, or (None, None).

    Probes the same locations, in the same order, as ``engine.read_installed_version``.
    """

    for rel in VERSION_LOCATIONS:
        candidate = repo / rel
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8").strip(), rel
            except OSError:
                return None, rel
    return None, None


def has_files(path: Path) -> bool:
    """True if ``path`` is a directory containing at least one FILE at any depth.

    Distinguishing this from mere directory existence matters: a finished migration was
    observed leaving 9 EMPTY directories under ``.agents/workflows``. Treating an empty
    directory as live framework material would report a split-brain layout that is really
    directory litter, which is a different defect with a different fix.
    """

    if not path.is_dir():
        return False
    for _root, _dirs, filenames in os.walk(path, onerror=lambda _e: None):
        if filenames:
            return True
    return False


def detect_layout(repo: Path) -> str:
    """Classify the on-disk framework layout by LIVE content, not by directory existence.

    Returns one of:
      ``aw``          canonical layout only;
      ``legacy``      legacy layout only;
      ``dual``        genuine split-brain: BOTH trees hold real files (the state the
                      installer's own guard refuses, and a legitimate rehearsal INPUT);
      ``aw+litter``   migrated, but empty legacy directories were left behind;
      ``none``        no framework installed.
    """

    aw_dir = repo / ".aw" / "system"
    legacy_dir = repo / ".agents" / "workflows"
    aw_live = has_files(aw_dir)
    legacy_live = has_files(legacy_dir)

    if aw_live and legacy_live:
        return "dual"
    if aw_live:
        return "aw+litter" if legacy_dir.is_dir() else "aw"
    if legacy_live:
        return "legacy"
    if aw_dir.is_dir():
        return "aw"
    if legacy_dir.is_dir():
        return "legacy"
    return "none"


def dir_size_bytes(path: Path) -> int:
    """Best-effort recursive size. Used only to warn about an expensive copy."""

    total = 0
    for root, dirnames, filenames in os.walk(path, onerror=lambda _e: None):
        for name in filenames:
            try:
                total += (Path(root) / name).lstat().st_size
            except OSError:
                pass
        del dirnames  # walked implicitly
    return total


def human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "K", "M", "G", "T"):
        if size < 1024 or unit == "T":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}T"


@dataclass
class SourceRepo:
    """A candidate source repository for a rehearsal (never mutated)."""

    path: Path
    version: Optional[str] = None
    version_path: Optional[str] = None
    layout: str = "none"
    dirty: bool = False
    branch: Optional[str] = None
    remotes: List[str] = field(default_factory=list)

    @classmethod
    def inspect(cls, path: Path) -> "SourceRepo":
        path = path.expanduser().resolve()
        version, version_path = installed_version(path)
        info = cls(
            path=path,
            version=version,
            version_path=version_path,
            layout=detect_layout(path),
        )
        if is_git_repo(path):
            info.branch = git_out(path, "rev-parse", "--abbrev-ref", "HEAD") or None
            info.dirty = bool(git_out(path, "status", "--porcelain"))
            remotes = git_out(path, "remote")
            info.remotes = [r for r in remotes.splitlines() if r.strip()]
        return info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "name": self.path.name,
            "version": self.version,
            "version_path": self.version_path,
            "layout": self.layout,
            "dirty": self.dirty,
            "branch": self.branch,
            "remotes": self.remotes,
        }


def search_roots(fallback_to_home: bool = True) -> List[Path]:
    """Resolve candidate search roots, preferring the user's configured ones.

    Reads the real user config READ-ONLY (never writes it) so ``list`` shows the repos the
    operator actually manages. Falls back to the home directory when the config is absent.
    """

    roots: List[Path] = []
    try:
        from agent_workflows import config as aw_config  # type: ignore

        cfg = aw_config.load()
        for entry in aw_config.repo_setting(cfg, "search") or []:
            # A "." search root means "the cwd", which is the framework CHECKOUT when this
            # tool is run from it (or a worktree of it). That is never a useful rehearsal
            # SOURCE, and including it makes the harness offer itself as a target, so the
            # relative entry is dropped rather than resolved.
            if str(entry).strip() in {".", "./", ""}:
                continue
            roots.append(aw_config.expand_path(entry))
    except Exception:
        pass
    if not roots and fallback_to_home:
        roots = [Path.home()]
    out: List[Path] = []
    for root in roots:
        try:
            rp = root.expanduser().resolve()
        except OSError:
            continue
        if rp.is_dir() and rp not in out:
            out.append(rp)
    return out


def is_worktree(path: Path) -> bool:
    """True if ``path`` is a git WORKTREE rather than a normal checkout.

    A worktree's ``.git`` is a FILE pointing into its parent repository, so it shares that
    repository's object store and administrative files. Installing into one would write
    through to state the parent owns, which is neither a realistic user scenario nor a safe
    rehearsal, so worktrees are excluded as sources.
    """

    dot_git = path / ".git"
    return dot_git.is_file()


def discover_sources(roots: Optional[Sequence[Path]] = None) -> List[SourceRepo]:
    """Find candidate source repos: immediate git-repo children of each search root.

    Sandboxes are skipped, so a rehearsal is never run on a rehearsal.
    """

    roots = list(roots) if roots else search_roots()
    found: List[SourceRepo] = []
    seen: set = set()
    for root in roots:
        if is_git_repo(root):
            candidates = [root]
        else:
            try:
                candidates = sorted(p for p in root.iterdir() if p.is_dir())
            except OSError:
                continue
        for cand in candidates:
            if SANDBOX_INFIX in cand.name or (cand / MARKER_NAME).is_file():
                continue
            if not is_git_repo(cand) or is_worktree(cand):
                continue
            rp = cand.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            found.append(SourceRepo.inspect(rp))
    return found


def resolve_source(spec: str) -> SourceRepo:
    """Resolve a source given a path or a bare repo name found under the search roots."""

    direct = Path(spec).expanduser()
    if direct.is_dir():
        if not is_git_repo(direct):
            raise HarnessError(f"not a git repository: {direct}")
        return SourceRepo.inspect(direct)

    matches = [s for s in discover_sources() if s.path.name == spec]
    if not matches:
        near = sorted(
            s.path.name
            for s in discover_sources()
            if spec.lower() in s.path.name.lower()
        )
        hint = f" Did you mean: {', '.join(near[:8])}?" if near else ""
        raise HarnessError(f"no repo named {spec!r} under the search roots.{hint}")
    if len(matches) > 1:
        paths = ", ".join(str(m.path) for m in matches)
        raise HarnessError(f"ambiguous repo name {spec!r}: {paths}")
    return matches[0]


# ---------------------------------------------------------------------------
# Sandbox creation
# ---------------------------------------------------------------------------


def sandbox_name(source_name: str, stamp: Optional[str] = None) -> str:
    stamp = stamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{source_name}.{SANDBOX_INFIX}.{stamp}"


def copy_full(source: Path, dest: Path) -> None:
    """Faithful copy including .git, untracked, and gitignored material.

    ``cp -a`` is used when available because it is markedly faster than ``shutil.copytree``
    on trees of this size and preserves modes/times/links exactly. NOTE the deliberate
    absence of ``-l``: a hardlink copy would let an in-place truncation inside the sandbox
    corrupt the SOURCE repo (invariant 1).
    """

    if shutil.which("cp"):
        run(["cp", "-a", "--", str(source), str(dest)])
        return
    shutil.copytree(source, dest, symlinks=True, ignore_dangling_symlinks=True)


def copy_clone(source: Path, dest: Path) -> None:
    """Cheap copy: local clone (hardlinked git OBJECTS, safe: git never rewrites them)
    plus a real copy of the framework state a clone would otherwise omit.

    A clone reproduces only COMMITTED state, so on its own it would rehearse an upgrade of a
    repo that does not exist. The framework's own trees are therefore copied afterwards,
    including untracked and gitignored parts, since those are exactly what an upgrade reads
    (``.aw/state``, backups, manifests).
    """

    run(["git", "clone", "--local", "--no-hardlinks", "--", str(source), str(dest)])
    for rel in (".aw", ".agents", "AGENTS.md", ".opencode", ".claude", ".gitignore"):
        src = source / rel
        if not src.exists():
            continue
        dst = dest / rel
        if src.is_dir():
            if dst.exists():
                _rmtree_sandbox(dst)
            shutil.copytree(src, dst, symlinks=True, ignore_dangling_symlinks=True)
        else:
            shutil.copy2(src, dst)


def neutralize_git(sandbox: Path) -> Dict[str, Any]:
    """Make it impossible for the sandbox to reach the real upstream (invariant 2).

    Three independent measures, because one is a single point of failure:
      1. every remote is REMOVED;
      2. a blackhole ``pushurl`` is configured so a re-added ``origin`` still cannot push;
      3. removal is VERIFIED and a non-empty remote list is a hard error.
    """

    if not is_git_repo(sandbox):
        return {"git": False, "remotes_removed": [], "verified": True}

    removed: List[str] = []
    for name in [r for r in git_out(sandbox, "remote").splitlines() if r.strip()]:
        git(sandbox, "remote", "remove", name, check=False)
        removed.append(name)

    git(
        sandbox,
        "config",
        "--local",
        "remote.pushDefault",
        "aw-upgrade-test-blackhole",
        check=False,
    )
    git(
        sandbox,
        "config",
        "--local",
        "remote.aw-upgrade-test-blackhole.url",
        BLACKHOLE_PUSH_URL,
        check=False,
    )
    git(
        sandbox,
        "config",
        "--local",
        "remote.aw-upgrade-test-blackhole.pushurl",
        BLACKHOLE_PUSH_URL,
        check=False,
    )
    # A sandbox commit must never be attributed to the operator's identity.
    git(sandbox, "config", "--local", "user.name", "aw-upgrade-test", check=False)
    git(
        sandbox,
        "config",
        "--local",
        "user.email",
        "aw-upgrade-test@invalid.localhost",
        check=False,
    )
    git(sandbox, "config", "--local", "commit.gpgsign", "false", check=False)

    leftover = [
        r
        for r in git_out(sandbox, "remote").splitlines()
        if r.strip() and r.strip() != "aw-upgrade-test-blackhole"
    ]
    if leftover:
        raise HarnessError(
            f"refusing to continue: sandbox still has real remotes {leftover}. "
            "A rehearsal must not be able to reach a real upstream."
        )
    return {"git": True, "remotes_removed": removed, "verified": True}


def sandbox_env(sandbox: Path) -> Dict[str, str]:
    """Environment that keeps every ``aw`` call inside the sandbox (invariant 3).

    ``XDG_CONFIG_HOME`` redirects the user config that ``aw install`` WRITES its
    ``repos.installed`` list into; ``AW_HOME`` redirects the home records backend. Verified
    empirically: with the override in place, ``config.config_path()`` resolves under the
    sandbox, so the operator's real config file is never opened for writing.
    """

    env = dict(os.environ)
    cfg_home = sandbox / ".aw-upgrade-test" / "xdg-config"
    aw_home = sandbox / ".aw-upgrade-test" / "aw-home"
    cfg_home.mkdir(parents=True, exist_ok=True)
    aw_home.mkdir(parents=True, exist_ok=True)
    env["XDG_CONFIG_HOME"] = str(cfg_home)
    env["AW_HOME"] = str(aw_home)
    env["NO_COLOR"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    # Never let a sandbox commit be signed with the operator's key or identity.
    env["GIT_AUTHOR_NAME"] = "aw-upgrade-test"
    env["GIT_AUTHOR_EMAIL"] = "aw-upgrade-test@invalid.localhost"
    env["GIT_COMMITTER_NAME"] = "aw-upgrade-test"
    env["GIT_COMMITTER_EMAIL"] = "aw-upgrade-test@invalid.localhost"
    return env


def write_marker(sandbox: Path, payload: Dict[str, Any]) -> None:
    (sandbox / MARKER_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_marker(sandbox: Path) -> Optional[Dict[str, Any]]:
    marker = sandbox / MARKER_NAME
    if not marker.is_file():
        return None
    try:
        return json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def snapshot_tree(repo: Path) -> List[str]:
    """Sorted repo-relative file list, excluding ``.git`` and our own sandbox scaffolding.

    This is the before/after basis for the file-level delta, which is the single most
    informative signal about what an upgrade actually did.
    """

    out: List[str] = []
    skip_top = {".git", ".aw-upgrade-test", MARKER_NAME}
    for root, dirnames, filenames in os.walk(repo, onerror=lambda _e: None):
        rel_root = Path(root).relative_to(repo)
        parts = rel_root.parts
        if parts and parts[0] in skip_top:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not (not parts and d in skip_top)]
        for name in filenames:
            if not parts and name in skip_top:
                continue
            out.append(str(rel_root / name) if parts else name)
    return sorted(out)


# ---------------------------------------------------------------------------
# Probing (read-only state capture)
# ---------------------------------------------------------------------------


def manifest_summary(repo: Path) -> Dict[str, Any]:
    """Summarize the install manifest, including the row-count-vs-disk drift.

    Row drift is called out because it is a KNOWN upgrade defect (``manifest.py`` has no
    row-deletion API and ``prune_stale`` never retires a row), measured at 135 rows against
    90 files on disk. Reporting it makes the defect visible in every rehearsal.
    """

    for rel in (
        ".aw/system/managed-sections.json",
        ".agents/workflows/managed-sections.json",
    ):
        path = repo / rel
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {"path": rel, "error": str(exc)}
        files = data.get("files")
        rows = len(files) if isinstance(files, (dict, list)) else None
        return {
            "path": rel,
            "schema_version": data.get("schema_version"),
            "installed_version": data.get("installed_version"),
            "installer": data.get("installer"),
            "rows": rows,
        }
    return {"path": None}


def git_state(repo: Path) -> Dict[str, Any]:
    if not is_git_repo(repo):
        return {"git": False}
    porcelain = git_out(repo, "status", "--porcelain")
    lines = [ln for ln in porcelain.splitlines() if ln.strip()]
    counts: Dict[str, int] = {}
    for line in lines:
        counts[line[:2].strip() or "??"] = counts.get(line[:2].strip() or "??", 0) + 1
    return {
        "git": True,
        "branch": git_out(repo, "rev-parse", "--abbrev-ref", "HEAD") or None,
        "head": git_out(repo, "rev-parse", "HEAD") or None,
        "remotes": [r for r in git_out(repo, "remote").splitlines() if r.strip()],
        "changed_paths": len(lines),
        "change_kinds": counts,
        "recent_commits": git_out(repo, "log", "--oneline", "-5").splitlines(),
    }


def probe(sandbox: Path) -> Dict[str, Any]:
    """Capture the sandbox's current framework state. Read-only and idempotent."""

    version, version_path = installed_version(sandbox)
    marker = read_marker(sandbox) or {}
    state: Dict[str, Any] = {
        "sandbox": str(sandbox),
        "probed_at": datetime.now().isoformat(timespec="seconds"),
        "source": marker.get("source", {}).get("path"),
        "baseline_version": marker.get("source", {}).get("version"),
        "baseline_layout": marker.get("source", {}).get("layout"),
        "installed_version": version,
        "installed_version_path": version_path,
        "layout": detect_layout(sandbox),
        "manifest": manifest_summary(sandbox),
        "git": git_state(sandbox),
    }
    legacy = sandbox / ".agents"
    state["legacy_files_remaining"] = (
        sum(1 for _ in legacy.rglob("*") if _.is_file()) if legacy.is_dir() else 0
    )
    # Break the leftovers down: an orphaned SKILL tree and empty directory litter are
    # different defects with different fixes, so a single count would hide both.
    state["legacy_breakdown"] = legacy_breakdown(sandbox)
    state["empty_dirs"] = count_empty_dirs(sandbox / ".agents")
    state["observations"] = derive_observations(state)
    return state


def legacy_breakdown(repo: Path) -> Dict[str, int]:
    """File counts per top-level subtree under ``.agents/``, so leftovers are attributable."""

    legacy = repo / ".agents"
    out: Dict[str, int] = {}
    if not legacy.is_dir():
        return out
    for path in legacy.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(legacy)
        key = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        out[key] = out.get(key, 0) + 1
    return out


def count_empty_dirs(root: Path) -> int:
    """Count directories containing no files at any depth (migration litter)."""

    if not root.is_dir():
        return 0
    total = 0
    for dirpath, _dirnames, _filenames in os.walk(root, onerror=lambda _e: None):
        if not has_files(Path(dirpath)):
            total += 1
    return total


def derive_observations(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """Flag states worth a human's attention. Descriptive, never a pass/fail verdict.

    Deliberately NOT assertions: this rig's job is to surface evidence, and calling a state
    a "failure" here would bake in an opinion about correct upgrade behavior that belongs in
    a spec, not in a rehearsal tool.
    """

    obs: List[Dict[str, str]] = []
    if state.get("layout") == "dual":
        obs.append(
            {
                "kind": "dual-layout",
                "note": "Both .aw/system and .agents/workflows hold real files (split-brain). "
                "Expected mid-migration; a finished migration should not leave it.",
            }
        )
    if state.get("layout") == "aw+litter":
        obs.append(
            {
                "kind": "empty-legacy-dirs",
                "note": f"Migrated to .aw, but {state.get('empty_dirs') or '?'} empty "
                "directory(ies) remain under .agents/. Directory litter, not a "
                "split-brain layout, though 'aw doctor' may still call it dual.",
            }
        )
    breakdown = state.get("legacy_breakdown") or {}
    remaining = state.get("legacy_files_remaining") or 0
    # Leftovers are only a FINDING when the run actually migrated. A non-interactive install
    # deliberately KEEPS a legacy layout in place (``--keep-legacy`` is the default without
    # ``--to-aw``), so flagging its intact .agents/ tree would report correct behavior as a
    # defect and train the reader to ignore the observation list.
    migrated = state.get("baseline_layout") in {"legacy", "dual"} and state.get(
        "layout"
    ) in {"aw", "aw+litter", "dual"}
    if remaining and migrated:
        detail = ", ".join(f"{k}={v}" for k, v in sorted(breakdown.items()))
        obs.append(
            {
                "kind": "legacy-leftovers",
                "note": f"{remaining} file(s) still under .agents/ after a MIGRATING run "
                f"({detail}). Check whether they are deferred leftovers or missed "
                "material.",
            }
        )
    if migrated and breakdown.get("skills"):
        obs.append(
            {
                "kind": "orphaned-skills",
                "note": f"{breakdown['skills']} file(s) remain under .agents/skills/ while the "
                "framework now installs skills under the .aw layout, so the old copies "
                "are unreferenced duplicates a host may still discover.",
            }
        )
    if remaining and not migrated and state.get("baseline_layout") == "legacy":
        obs.append(
            {
                "kind": "legacy-kept",
                "note": "The run kept the legacy .agents/ layout in place (the non-interactive "
                "default without --to-aw), so the legacy tree is intact BY DESIGN. "
                "Re-run with '-- --to-aw' to rehearse the migration.",
            }
        )
    baseline = state.get("baseline_version")
    now = state.get("installed_version")
    if baseline and now and baseline == now:
        obs.append(
            {
                "kind": "version-unchanged",
                "note": f"Installed VERSION is still {now} after the upgrade. The stamped "
                "VERSION comes from the source tree's baked file, not the running "
                "package, so an unbumped source VERSION stamps the old number.",
            }
        )
    manifest = state.get("manifest") or {}
    if manifest.get("installed_version") and baseline:
        if manifest["installed_version"] == baseline:
            obs.append(
                {
                    "kind": "manifest-version-unchanged",
                    "note": f"Manifest still records installed_version="
                    f"{manifest['installed_version']}.",
                }
            )
    git_info = state.get("git") or {}
    if git_info.get("remotes"):
        real = [r for r in git_info["remotes"] if r != "aw-upgrade-test-blackhole"]
        if real:
            obs.append(
                {
                    "kind": "remote-present",
                    "note": f"SAFETY: sandbox has remotes {real}; it should have none.",
                }
            )
    return obs


# ---------------------------------------------------------------------------
# The rehearsal
# ---------------------------------------------------------------------------


def create_sandbox(
    source: SourceRepo,
    dest_root: Path,
    strategy: str = "full",
    stamp: Optional[str] = None,
    sibling: bool = False,
) -> Path:
    """Create and neutralize a sandbox copy. Raises before mutating anything on failure."""

    root = source.path.parent if sibling else dest_root.expanduser()
    root.mkdir(parents=True, exist_ok=True)
    sandbox = root / sandbox_name(source.path.name, stamp)
    if sandbox.exists():
        raise HarnessError(f"sandbox already exists: {sandbox}")

    if strategy == "full":
        copy_full(source.path, sandbox)
    elif strategy == "clone":
        copy_clone(source.path, sandbox)
    else:
        raise HarnessError(f"unknown strategy {strategy!r} (expected full or clone)")

    neutral = neutralize_git(sandbox)
    write_marker(
        sandbox,
        {
            "tool": "tools/aw_upgrade_test.py",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "strategy": strategy,
            "source": source.to_dict(),
            "git_neutralized": neutral,
        },
    )
    return sandbox


def run_install(
    sandbox: Path,
    install_args: Sequence[str] = (),
    aw_cmd: Optional[Sequence[str]] = None,
    timeout: int = 1800,
) -> Dict[str, Any]:
    """Run the real installer against the sandbox and capture the full transcript."""

    cmd = list(aw_cmd) if aw_cmd else default_aw_cmd()
    argv = [*cmd, "install", str(sandbox), "-y", *install_args]
    env = sandbox_env(sandbox)
    started = time.time()
    proc = subprocess.run(
        argv,
        cwd=str(sandbox),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )
    return {
        "argv": argv,
        "exit_code": proc.returncode,
        "duration_s": round(time.time() - started, 2),
        "output": proc.stdout,
    }


def default_aw_cmd() -> List[str]:
    """Prefer running the checkout's own package, so a rehearsal tests THIS code.

    Falls back to whatever ``aw`` is on PATH. Running the installed console script would
    silently rehearse a DIFFERENT (possibly older) version than the checkout under test,
    which is the one mistake that would invalidate every result this tool produces.
    """

    repo_root = Path(__file__).resolve().parent.parent
    if (repo_root / "agent_workflows" / "cli.py").is_file():
        return [sys.executable, "-m", "agent_workflows"]
    found = shutil.which("aw")
    return [found] if found else [sys.executable, "-m", "agent_workflows"]


def rehearse(
    source_spec: str,
    dest_root: Optional[Path] = None,
    strategy: str = "full",
    install_args: Sequence[str] = (),
    run_it: bool = True,
    rerun: bool = False,
    sibling: bool = False,
    aw_cmd: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Full rehearsal: copy, neutralize, snapshot, install, snapshot, probe."""

    source = resolve_source(source_spec)
    sandbox = create_sandbox(
        source, dest_root or default_sandbox_root(), strategy, sibling=sibling
    )

    before = snapshot_tree(sandbox)
    result: Dict[str, Any] = {
        "sandbox": str(sandbox),
        "source": source.to_dict(),
        "strategy": strategy,
        "files_before": len(before),
        "runs": [],
    }

    if run_it:
        result["runs"].append(run_install(sandbox, install_args, aw_cmd=aw_cmd))
        if rerun:
            # An idempotency check is the cheapest high-value signal available: a second
            # identical run must not keep changing the tree.
            result["runs"].append(run_install(sandbox, install_args, aw_cmd=aw_cmd))

    after = snapshot_tree(sandbox)
    before_set, after_set = set(before), set(after)
    result["files_after"] = len(after)
    result["added"] = sorted(after_set - before_set)
    result["removed"] = sorted(before_set - after_set)
    result["state"] = probe(sandbox)

    marker = read_marker(sandbox) or {}
    marker["rehearsal"] = {k: v for k, v in result.items() if k not in {"state"}}
    marker["last_probe"] = result["state"]
    write_marker(sandbox, marker)
    return result


def find_sandboxes(roots: Optional[Sequence[Path]] = None) -> List[Path]:
    """Locate sandboxes by MARKER, not by name, so a renamed one is still found."""

    search: List[Path] = [default_sandbox_root().expanduser()]
    if roots:
        search = [Path(r).expanduser() for r in roots]
    else:
        search.extend(search_roots())
    out: List[Path] = []
    seen: set = set()
    for root in search:
        if not root.is_dir():
            continue
        try:
            children = sorted(p for p in root.iterdir() if p.is_dir())
        except OSError:
            continue
        for child in children:
            if not (child / MARKER_NAME).is_file():
                continue
            rp = child.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(rp)
    return out


def clean(paths: Sequence[Path], force: bool = False) -> List[Dict[str, Any]]:
    """Delete sandboxes, refusing anything without the marker (invariant 4).

    The marker gate is the entire safety mechanism: a mistyped or wrong path is REFUSED
    rather than deleted, so this command cannot destroy a real repository. ``force`` does
    NOT bypass the gate; nothing does.
    """

    results: List[Dict[str, Any]] = []
    for path in paths:
        p = Path(path).expanduser().resolve()
        if not p.is_dir():
            results.append(
                {"path": str(p), "action": "skip", "reason": "not a directory"}
            )
            continue
        if not (p / MARKER_NAME).is_file():
            results.append(
                {
                    "path": str(p),
                    "action": "refuse",
                    "reason": f"no {MARKER_NAME} marker; refusing to delete a non-sandbox",
                }
            )
            continue
        _rmtree_sandbox(p)
        results.append({"path": str(p), "action": "removed"})
    del force  # accepted for CLI symmetry; the marker gate is never bypassable
    return results


def _rmtree_sandbox(path: Path) -> None:
    """``shutil.rmtree`` that also removes READ-ONLY files, which a sandbox always contains.

    A sandbox is a ``git clone``, and git writes its object files read-only. POSIX lets the owner
    unlink a read-only file in a writable directory, but WINDOWS refuses (``WinError 5``, measured on
    the Windows CI runner), so ``aw upgrade-test clean`` failed on every real sandbox there. On a
    refusal, clear the read-only attribute and retry that one path; any other error propagates.
    """

    import stat

    def _clear_and_retry(func, target, _exc) -> None:
        try:
            os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
        except OSError:
            pass
        func(target)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_clear_and_retry)
    else:  # pragma: no cover - onerror is deprecated from 3.12
        shutil.rmtree(path, onerror=_clear_and_retry)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _emit_agent(
    command: str,
    data: Any,
    exit_code: int = 0,
    summary: str = "",
    status: str = "clean",
) -> int:
    try:
        from agent_workflows.renderers import get_renderer
        from agent_workflows.result_types import CommandResult, select_output

        ctx = select_output(
            argparse.Namespace(agent=True, json=False, no_color=False, color=False)
        )
        res = CommandResult(
            command=command,
            status=status,
            exit_code=exit_code,
            summary=summary,
            data=data if isinstance(data, dict) else {"items": data},
            verified=(exit_code == 0),
            complete=(exit_code == 0),
        )
        return get_renderer(ctx).emit(res, ctx)
    except Exception:
        return exit_code


def cmd_list(args: argparse.Namespace) -> int:
    sources = discover_sources()
    if args.installed_only:
        sources = [s for s in sources if s.version]
    if getattr(args, "json", False):
        print(json.dumps([s.to_dict() for s in sources], indent=2))
        return 0
    if getattr(args, "agent", False):
        return _emit_agent(
            "upgrade-test list",
            {"sources": [s.to_dict() for s in sources]},
            summary=f"Candidate source repos ({len(sources)})",
        )
    if not sources:
        print("No candidate source repos found.")
        return 0
    print(f"Candidate source repos ({len(sources)}):")
    print(f"  {'NAME':<32} {'VERSION':<12} {'LAYOUT':<8} {'GIT':<7} SIZE")
    for s in sources:
        size = human_bytes(dir_size_bytes(s.path)) if args.size else "-"
        print(
            f"  {s.path.name:<32} {(s.version or 'none'):<12} {s.layout:<8} "
            f"{('dirty' if s.dirty else 'clean'):<7} {size}"
        )
    print("\nRehearse one with: aw upgrade-test new <NAME>")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    source = resolve_source(args.repo)
    if not args.yes and args.strategy == "full":
        size = dir_size_bytes(source.path)
        if size > args.warn_bytes:
            print(
                f"Note: {source.path.name} is {human_bytes(size)}; a full copy will use "
                f"that much disk. Use --strategy clone for a cheaper copy, or -y to skip "
                f"this note."
            )
    result = rehearse(
        args.repo,
        dest_root=Path(args.dest) if args.dest else None,
        strategy=args.strategy,
        install_args=args.install_args,
        run_it=not args.no_run,
        rerun=args.rerun,
        sibling=args.sibling,
    )
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
        return 0
    if getattr(args, "agent", False):
        exit_code = 0 if all(r["exit_code"] == 0 for r in result["runs"]) else 1
        return _emit_agent(
            "upgrade-test new",
            result,
            exit_code=exit_code,
            status="clean" if exit_code == 0 else "findings",
            summary=f"Rehearsal completed with exit {exit_code}",
        )
    report(result, verbose=args.verbose)
    return 0 if all(r["exit_code"] == 0 for r in result["runs"]) else 1


def report(result: Dict[str, Any], verbose: bool = False) -> None:
    state = result["state"]
    src = result["source"]
    print(f"\nSandbox:  {result['sandbox']}")
    print(f"Source:   {src['path']}")
    print(f"Strategy: {result['strategy']}")
    print(
        f"Baseline: version={src['version'] or 'none'} layout={src['layout']} "
        f"({'dirty' if src['dirty'] else 'clean'})"
    )
    for i, r in enumerate(result["runs"], 1):
        label = "install" if i == 1 else f"install (re-run {i - 1})"
        print(f"\n{label}: exit={r['exit_code']} in {r['duration_s']}s")
        if verbose or r["exit_code"] != 0:
            print(indent(r["output"]))

    print(
        f"\nFiles: {result['files_before']} -> {result['files_after']} "
        f"(+{len(result['added'])} / -{len(result['removed'])})"
    )
    if verbose:
        for path in result["added"][:40]:
            print(f"  + {path}")
        for path in result["removed"][:40]:
            print(f"  - {path}")

    print(
        f"\nAfter:    version={state['installed_version'] or 'none'} "
        f"({state['installed_version_path'] or 'n/a'}) layout={state['layout']}"
    )
    manifest = state.get("manifest") or {}
    if manifest.get("path"):
        print(
            f"Manifest: installed_version={manifest.get('installed_version')} "
            f"rows={manifest.get('rows')} schema={manifest.get('schema_version')}"
        )
    git_info = state.get("git") or {}
    if git_info.get("git"):
        print(
            f"Git:      {git_info.get('changed_paths')} changed path(s) "
            f"{git_info.get('change_kinds')} remotes={git_info.get('remotes')}"
        )
    if state.get("legacy_files_remaining"):
        breakdown = state.get("legacy_breakdown") or {}
        detail = ", ".join(f"{k}={v}" for k, v in sorted(breakdown.items()))
        print(
            f"Legacy:   {state['legacy_files_remaining']} file(s) still under .agents/"
            + (f" ({detail})" if detail else "")
        )

    obs = state.get("observations") or []
    if obs:
        print("\nObservations (evidence, not verdicts):")
        for o in obs:
            print(f"  [{o['kind']}] {o['note']}")

    print("\nExplore it safely with:")
    print(f"  eval \"$(tools/aw_upgrade_test.py env {result['sandbox']})\"")
    print(f"  tools/aw_upgrade_test.py probe {result['sandbox']}")


def indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.rstrip().splitlines())


def cmd_sandboxes(args: argparse.Namespace) -> int:
    boxes = find_sandboxes(args.root)
    if getattr(args, "json", False):
        print(
            json.dumps(
                [{"path": str(b), "marker": read_marker(b)} for b in boxes], indent=2
            )
        )
        return 0
    if getattr(args, "agent", False):
        boxes_data = [{"path": str(b), "marker": read_marker(b)} for b in boxes]
        return _emit_agent(
            "upgrade-test sandboxes",
            {"sandboxes": boxes_data},
            summary=f"Sandboxes ({len(boxes)})",
        )
    if not boxes:
        print("No sandboxes found.")
        return 0
    print(f"Sandboxes ({len(boxes)}):")
    for b in boxes:
        marker = read_marker(b) or {}
        src = (marker.get("source") or {}).get("path", "?")
        created = marker.get("created_at", "?")
        print(f"  {b}\n      from {src} at {created}")
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    sandbox = Path(args.sandbox).expanduser().resolve()
    if not (sandbox / MARKER_NAME).is_file():
        raise HarnessError(f"not a sandbox (no {MARKER_NAME}): {sandbox}")
    state = probe(sandbox)
    if getattr(args, "json", False):
        print(json.dumps(state, indent=2))
        return 0
    if getattr(args, "agent", False):
        return _emit_agent(
            "upgrade-test probe",
            state,
            summary=f"Probed sandbox at {state.get('sandbox', '')}",
        )
    print(f"Sandbox:  {state['sandbox']}")
    print(
        f"Baseline: version={state['baseline_version']} layout={state['baseline_layout']}"
    )
    print(f"Now:      version={state['installed_version']} layout={state['layout']}")
    manifest = state.get("manifest") or {}
    if manifest.get("path"):
        print(
            f"Manifest: installed_version={manifest.get('installed_version')} "
            f"rows={manifest.get('rows')}"
        )
    git_info = state.get("git") or {}
    if git_info.get("git"):
        print(
            f"Git:      branch={git_info.get('branch')} "
            f"changed={git_info.get('changed_paths')} remotes={git_info.get('remotes')}"
        )
    for o in state.get("observations") or []:
        print(f"  [{o['kind']}] {o['note']}")
    return 0


def cmd_env(args: argparse.Namespace) -> int:
    """Print shell exports so a human can explore a sandbox under the same isolation."""

    sandbox = Path(args.sandbox).expanduser().resolve()
    if not (sandbox / MARKER_NAME).is_file():
        raise HarnessError(f"not a sandbox (no {MARKER_NAME}): {sandbox}")
    env = sandbox_env(sandbox)
    if getattr(args, "agent", False):
        return _emit_agent(
            "upgrade-test env",
            {"sandbox": str(sandbox), "env": env},
            summary=f"Environment exports for {sandbox}",
        )
    for key in ("XDG_CONFIG_HOME", "AW_HOME", "GIT_TERMINAL_PROMPT"):
        print(f"export {key}={shlex.quote(env[key])}")
    print(f"cd {shlex.quote(str(sandbox))}")
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    if args.all:
        targets = find_sandboxes(args.root)
    else:
        targets = [Path(p) for p in args.paths]
    if not targets:
        if getattr(args, "agent", False):
            return _emit_agent(
                "upgrade-test clean",
                {"results": []},
                summary="Nothing to clean.",
            )
        print("Nothing to clean.")
        return 0
    if not args.yes:
        if getattr(args, "agent", False):
            return _emit_agent(
                "upgrade-test clean",
                {"would_remove": [str(t) for t in targets]},
                summary=f"Would remove {len(targets)} sandbox(es). Re-run with -y.",
                status="preview",
            )
        print("Would remove:")
        for t in targets:
            print(f"  {t}")
        print("\nRe-run with -y to actually remove them.")
        return 0
    results = clean(targets)
    if getattr(args, "json", False):
        print(json.dumps(results, indent=2))
        return 0
    if getattr(args, "agent", False):
        exit_code = 0 if all(r["action"] != "refuse" for r in results) else 1
        return _emit_agent(
            "upgrade-test clean",
            {"results": results},
            exit_code=exit_code,
            status="clean" if exit_code == 0 else "findings",
            summary=f"Cleaned {len([r for r in results if r['action'] == 'remove'])} sandbox(es)",
        )
    for r in results:
        print(
            f"  [{r['action']}] {r['path']}"
            + (f" ({r['reason']})" if r.get("reason") else "")
        )
    return 0 if all(r["action"] != "refuse" for r in results) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aw_upgrade_test.py",
        description=(
            "Rehearse an agent-workflows install/update/migrate against a disposable copy "
            "of a real repo. Never mutates the source, never pushes, never touches the "
            "real aw config."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "EXAMPLES\n"
            "  tools/aw_upgrade_test.py list --size\n"
            "  tools/aw_upgrade_test.py new <repo> --rerun\n"
            "  tools/aw_upgrade_test.py new <repo> -- --to-aw\n"
            "  tools/aw_upgrade_test.py new <big-repo> --strategy clone\n"
            "  tools/aw_upgrade_test.py probe <sandbox> --json\n"
            "  tools/aw_upgrade_test.py clean --all -y\n"
        ),
    )
    # --json is accepted on BOTH sides of the subcommand, because `list --json` is the
    # natural way to type it while `--json list` is what the top-level help implies. Both
    # write the SAME dest with default None, so whichever side supplies it wins and the
    # subparser's default cannot silently clobber a global value with False.
    parser.add_argument(
        "--json",
        action="store_const",
        const=True,
        default=None,
        help="Machine-readable output.",
    )
    common = argparse.ArgumentParser(add_help=False)
    # SUPPRESS is load-bearing: a subparser APPLIES its own defaults over the namespace the
    # top-level parse already populated, so any concrete default here (None or False) would
    # silently erase a global `--json` given BEFORE the subcommand. SUPPRESS leaves the
    # attribute untouched when the flag is absent.
    common.add_argument(
        "--json",
        action="store_const",
        const=True,
        default=argparse.SUPPRESS,
        help="Machine-readable output.",
    )
    common.add_argument(
        "--agent",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Machine-readable output (aw.agent/v1 JSONL).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser(
        "list",
        parents=[common],
        help="List candidate source repos and their versions.",
    )
    p_list.add_argument(
        "--installed-only",
        action="store_true",
        help="Only repos with the framework already installed.",
    )
    p_list.add_argument(
        "--size", action="store_true", help="Compute directory sizes (slower)."
    )
    p_list.set_defaults(func=cmd_list)

    p_new = sub.add_parser(
        "new", parents=[common], help="Create a sandbox copy and run the upgrade."
    )
    p_new.add_argument("repo", help="Source repo name (under search roots) or a path.")
    p_new.add_argument(
        "--dest",
        default=None,
        help="Sandbox root (default: a 'tmp/aw-upgrade-tests' directory "
        "under your first configured search root, outside the "
        "discovery scan; override with AW_UPGRADE_TEST_ROOT).",
    )
    p_new.add_argument(
        "--sibling",
        action="store_true",
        help="Place the sandbox beside its source instead of under --dest.",
    )
    p_new.add_argument(
        "--strategy",
        choices=("full", "clone"),
        default="full",
        help="full: cp -a, faithful (default). clone: cheap, committed "
        "state plus the framework trees.",
    )
    p_new.add_argument(
        "--no-run", action="store_true", help="Copy only; do not run the installer."
    )
    p_new.add_argument(
        "--rerun",
        action="store_true",
        help="Run the installer twice to check idempotency.",
    )
    p_new.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show full installer output and the file delta.",
    )
    p_new.add_argument(
        "-y", "--yes", action="store_true", help="Skip the large-copy note."
    )
    p_new.add_argument(
        "--warn-bytes",
        type=int,
        default=512 * 1024 * 1024,
        help="Size above which a full copy prints a note.",
    )
    p_new.add_argument(
        "install_args",
        nargs="*",
        metavar="-- INSTALL_ARGS",
        help="Args passed verbatim to 'aw install' after a bare --.",
    )
    p_new.set_defaults(func=cmd_new)

    p_boxes = sub.add_parser(
        "sandboxes", parents=[common], help="List existing sandboxes."
    )
    p_boxes.add_argument(
        "--root", action="append", help="Extra root to search (repeatable)."
    )
    p_boxes.set_defaults(func=cmd_sandboxes)

    p_probe = sub.add_parser(
        "probe", parents=[common], help="Re-probe a sandbox's state (read-only)."
    )
    p_probe.add_argument("sandbox")
    p_probe.set_defaults(func=cmd_probe)

    p_env = sub.add_parser(
        "env", parents=[common], help="Print shell exports to explore a sandbox safely."
    )
    p_env.add_argument("sandbox")
    p_env.set_defaults(func=cmd_env)

    p_clean = sub.add_parser(
        "clean", parents=[common], help="Remove sandboxes (marker-gated)."
    )
    p_clean.add_argument("paths", nargs="*", help="Sandbox paths to remove.")
    p_clean.add_argument(
        "--all", action="store_true", help="Remove every found sandbox."
    )
    p_clean.add_argument(
        "--root", action="append", help="Extra root to search (repeatable)."
    )
    p_clean.add_argument("-y", "--yes", action="store_true", help="Actually remove.")
    p_clean.set_defaults(func=cmd_clean)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    parser = build_parser()
    args = parser.parse_args(argv)
    # argparse keeps the bare "--" separator in a nargs="*" tail; drop it so the pass-through
    # args reach `aw install` verbatim.
    if getattr(args, "install_args", None):
        args.install_args = [a for a in args.install_args if a != "--"]
    if not getattr(args, "json", False):
        args.json = False
    try:
        return args.func(args)
    except HarnessError as exc:
        if getattr(args, "agent", False):
            return _emit_agent(
                f"upgrade-test {getattr(args, 'command', '')}".strip(),
                {"error": str(exc)},
                exit_code=2,
                status="cannot-run",
                summary=str(exc),
            )
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
