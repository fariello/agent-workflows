#!/usr/bin/env python3
"""Survey every agent-workflows repository on this machine and write an UNMASKED inventory.

WHY THIS EXISTS. Plan `9vf2iv` builds migration fixtures, one per repository layout the metadata
migration must handle. Its evidence came from this public repository's history and from counts
recorded once by hand. This script gathers the same facts from every repository on a server, raw,
so the data can be inspected before anyone decides how to analyze, anonymize, or record it.

THE OUTPUT IS NOT ANONYMIZED. It contains absolute paths, hostnames, remote URLs and file names.
Keep it out of any tracked tree and do not share it. No masking is done here on purpose.

STANDALONE. Python 3.9+ standard library only; it never imports `agent_workflows`, so it runs on a
server with an old toolkit or none. The name grammars below are copies of the toolkit's
(`agent_workflows/artifact_naming.py`) and may drift from it; the per-file records let a reader see
what each name was classified as.

READ-ONLY. It runs only read-only git commands (`rev-parse`, `ls-files`, `status`, `log`,
`for-each-ref`, `rev-list`, `worktree list`, and `ls-remote`, which asks the remote for its branch
tips over the network without fetching or writing anything locally) and reads files. It writes
nothing except the output file. `--offline` skips `ls-remote`.

AW DIAGNOSTICS. By default it also runs `aw check --agent`, `aw attention --format json` and
`aw doctor --json` in each repository, using whatever `aw` is on PATH (or `--aw PATH`), and stores
their exit codes and parsed findings. These commands are meant to be read-only; the survey checks
that by comparing `git status` and file modification times under `.aw/`, `.agents/`, any companion
and `~/.aw` before and after, and records anything that changed. `--no-run-aw` skips them.

Usage:
    python3 aw_repo_survey.py [PATH ...] [--scan DIR ...] [--no-registry] [--offline]
                              [--no-run-aw] [-o OUT.json]

Each PATH is surveyed when it is a repository with `.aw/` or `.agents/`. Each `--scan DIR` is
searched (to `--max-depth`) for such repositories. Repositories listed in the toolkit's user config
(`~/.config/agent-workflows/config.json`) and registry (`~/.aw/config/registry.json`) are added
unless `--no-registry` is given. With no arguments at all, the registry plus `--scan ~` is used.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SCHEMA = "aw-repo-survey/v2"

# Name grammars, copied from agent_workflows/artifact_naming.py.
_CLUSTERED_PREFIX_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2,3})-(?P<id6>[0-9a-z]{6})-"
)
_CORE_FACET_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2,3})-(?P<id6>[0-9a-z]{6})-"
    r"(?P<slug>[a-z0-9-]+?)(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)
_LEGACY_TIMESTAMP_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<hhmm>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9-]+?)"
    r"(?:\.(?P<facet>[a-z0-9.-]+))?\.md\Z"
)
_WALKTHROUGH_DATED_RE = re.compile(r"\A\d{8}-[a-z0-9-]+-walkthrough\.md\Z")
_WALKTHROUGH_BARE_RE = re.compile(r"\A[a-z0-9-]+-walkthrough\.md\Z")
_DATED_SLUG_RE = re.compile(r"\A\d{8}-[a-z0-9-]+(?:\.[a-z0-9.-]+)?\.md\Z")

_BULLET_RE = re.compile(r"^-[ \t]+(?P<key>[A-Z][A-Za-z-]*):[ \t]*(?P<val>.*?)[ \t]*$")
_ID6_RE = re.compile(r"\A[0-9a-z]{6}\Z")
_YAML_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$")

# Bullets recorded per file (presence and value). Others are counted by key only.
_KEY_BULLETS = (
    "Id",
    "Status",
    "Set",
    "Order",
    "Kind",
    "Date",
    "Target-Id",
    "Subject-Id",
    "Subject-Type",
    "Work-Kind",
    "Verdict",
)

# Directories whose files are counted but not listed one by one (large, machine-written).
_BULK_DIRS = {
    "runs",
    "state",
    "worktrees",
    "workflow-artifacts",
    "__pycache__",
    "inbox",
}
# Directories never descended into while scanning for repositories.
_SCAN_SKIP = {
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".cache",
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "site-packages",
    "worktrees",
    ".npm",
    ".cargo",
    ".rustup",
    "snap",
}
_CONFIG_FILES = (
    ".aw/config/project.json",
    ".aw/config/local.json",
    ".aw/config/config.json",
    ".aw/config.json",
    ".agents/config.json",
    ".aw/system/VERSION",
    ".aw/system/layout.json",
    ".agents/VERSION",
    ".aw/system/managed-sections.json",
    ".pre-commit-config.yaml",
)
_MAX_CONFIG_BYTES = 64 * 1024
_AGENT_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
)
_AGENT_DIRS = (
    ".opencode",
    ".claude",
    ".gemini",
    ".codex",
    ".cursor",
    ".github/workflows",
)
_AW_COMMANDS = (
    ("check", ("check", "--agent")),
    ("attention", ("attention", "--format", "json")),
    ("doctor", ("doctor", "--json")),
)
_GIT_OPS = {
    "MERGE_HEAD": "merge",
    "rebase-merge": "rebase",
    "rebase-apply": "rebase-or-am",
    "CHERRY_PICK_HEAD": "cherry-pick",
    "REVERT_HEAD": "revert",
    "BISECT_LOG": "bisect",
}


def _git(
    repo: Path, *args: str, timeout: float = 120, env: dict[str, str] | None = None
) -> tuple[int, str]:
    try:
        res = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return res.returncode, res.stdout


def _git_out(repo: Path, *args: str) -> str | None:
    rc, out = _git(repo, *args)
    return out.strip() if rc == 0 else None


def _remote_env() -> dict[str, str]:
    """Environment for network git calls: never prompt for a password or a host key."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    if "GIT_SSH_COMMAND" not in env:
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o ConnectTimeout=15"
    return env


def _ls_remote(repo: Path, remote: str) -> dict[str, Any]:
    """The remote's branch tips and default branch, read live; nothing is fetched or written."""
    t0 = time.monotonic()
    try:
        res = subprocess.run(
            ["git", "-C", str(repo), "ls-remote", "--symref", remote],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            env=_remote_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"reachable": False, "error": str(exc)[-500:]}
    out: dict[str, Any] = {"seconds": round(time.monotonic() - t0, 2)}
    if res.returncode != 0:
        out.update(reachable=False, error=res.stderr.strip()[-500:])
        return out
    heads: dict[str, str] = {}
    default = None
    tags = 0
    for line in res.stdout.splitlines():
        if line.startswith("ref: ") and line.endswith("\tHEAD"):
            default = line[5:].split("\t")[0].removeprefix("refs/heads/")
            continue
        sha, _, ref = line.partition("\t")
        if ref.startswith("refs/heads/"):
            heads[ref[len("refs/heads/") :]] = sha
        elif ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            tags += 1
    out.update(reachable=True, default_branch=default, heads=heads, tag_count=tags)
    return out


def _compare(repo: Path, local_sha: str, remote_sha: str | None) -> dict[str, Any]:
    """Where a local tip stands against a live remote tip."""
    if remote_sha is None:
        return {"state": "upstream-gone"}
    if local_sha == remote_sha:
        return {"state": "up-to-date", "ahead": 0, "behind": 0}
    rc, _ = _git(repo, "cat-file", "-e", f"{remote_sha}^{{commit}}")
    if rc != 0:
        # The remote moved to a commit this clone has never fetched, so it is behind by an
        # unknown number. Ahead is counted against what the clone knows of that remote.
        return {"state": "behind-unfetched", "remote_sha": remote_sha}
    counts = _git_out(
        repo, "rev-list", "--left-right", "--count", f"{local_sha}...{remote_sha}"
    )
    ahead, behind = (int(x) for x in (counts or "0 0").split())
    state = (
        "diverged"
        if ahead and behind
        else "ahead"
        if ahead
        else "behind"
        if behind
        else "up-to-date"
    )
    return {"state": state, "ahead": ahead, "behind": behind, "remote_sha": remote_sha}


def git_state(repo: Path, online: bool) -> dict[str, Any]:
    """Working tree, branches, stashes and remote sync state of one repository."""
    out: dict[str, Any] = {}
    _, st = _git(
        repo, "status", "--porcelain=v2", "--branch", "--untracked-files=normal"
    )
    counts = {"staged": 0, "unstaged": 0, "untracked": 0, "conflicted": 0}
    for line in st.splitlines():
        if line.startswith("# branch.ab "):
            n_ahead, n_behind = line.split()[2:4]
            out["tracking_ahead_behind_at_last_fetch"] = [int(n_ahead), -int(n_behind)]
        elif line.startswith("# branch.upstream "):
            out["upstream"] = line.split(" ", 2)[2]
        elif line[:2] in ("1 ", "2 "):
            xy = line[2:4]
            counts["staged"] += xy[0] != "."
            counts["unstaged"] += xy[1] != "."
        elif line.startswith("u "):
            counts["conflicted"] += 1
        elif line.startswith("? "):
            counts["untracked"] += 1
    out["working_tree"] = counts
    out["dirty"] = any(counts.values())
    out["detached"] = _git_out(repo, "symbolic-ref", "-q", "HEAD") is None
    stash = _git_out(repo, "rev-list", "--walk-reflogs", "--count", "refs/stash")
    out["stash_count"] = int(stash) if stash and stash.isdigit() else 0
    gitdir = _git_out(repo, "rev-parse", "--absolute-git-dir")
    common = (
        _git_out(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
        or gitdir
    )
    if gitdir:
        out["in_progress"] = [
            op for f, op in _GIT_OPS.items() if (Path(gitdir) / f).exists()
        ]
    if common:
        fh = Path(common) / "FETCH_HEAD"
        out["last_fetch"] = (
            _dt.datetime.fromtimestamp(fh.stat().st_mtime, _dt.timezone.utc).isoformat()
            if fh.exists()
            else None
        )
        hooks = Path(common) / "hooks"
        out["hooks"] = sorted(
            e.name
            for e in (os.scandir(hooks) if hooks.is_dir() else [])
            if not e.name.endswith(".sample")
        )
    out["hooks_path"] = _git_out(repo, "config", "--get", "core.hooksPath")
    out["pre_commit_config"] = (repo / ".pre-commit-config.yaml").exists()
    out["shallow"] = _git_out(repo, "rev-parse", "--is-shallow-repository") == "true"
    out["submodules"] = (repo / ".gitmodules").exists()
    out["commit_count"] = int(_git_out(repo, "rev-list", "--count", "HEAD") or 0)
    last = _git_out(repo, "log", "-1", "--format=%cI%x00%an")
    if last:
        out["last_commit_at"], _, out["last_commit_author"] = last.partition("\0")
    first = _git_out(repo, "log", "--reverse", "--max-parents=0", "--format=%cI")
    out["first_commit_at"] = first.splitlines()[0] if first else None
    rec = _git_out(repo, "log", "--format=%cI", "--", ".aw", ".agents") or ""
    dates = rec.splitlines()
    out["record_tree_commits"] = {
        "count": len(dates),
        "first": dates[-1] if dates else None,
        "last": dates[0] if dates else None,
    }
    objs = _git_out(repo, "count-objects", "-v") or ""
    kib = {
        k: int(v)
        for k, _, v in (ln.partition(": ") for ln in objs.splitlines())
        if v.isdigit()
    }
    out["git_size_kib"] = kib.get("size", 0) + kib.get("size-pack", 0)

    _, refs = _git(
        repo,
        "for-each-ref",
        "--format=%(refname:short)%00%(objectname)%00%(upstream:remotename)%00"
        "%(upstream:remoteref)%00%(upstream:track)%00%(committerdate:iso-strict)",
        "refs/heads",
    )
    branches = []
    for line in refs.splitlines():
        parts = line.split("\0")
        if len(parts) != 6:
            continue
        name, sha, rname, rref, track, date = parts
        b: dict[str, Any] = {
            "name": name,
            "sha": sha,
            "upstream_remote": rname or None,
            "upstream_branch": rref.removeprefix("refs/heads/") or None,
            "track_at_last_fetch": track or None,
            "last_commit_at": date,
        }
        if not rname:
            on_remote = _git_out(repo, "branch", "-r", "--contains", sha)
            b["on_any_remote_branch"] = bool(on_remote)
        branches.append(b)
    out["branches"] = branches

    remotes: dict[str, Any] = {}
    for name in (_git_out(repo, "remote") or "").split():
        r: dict[str, Any] = {"url": _git_out(repo, "remote", "get-url", name)}
        if online:
            r.update(_ls_remote(repo, name))
        remotes[name] = r
    out["remotes"] = remotes
    out["online_checked"] = online

    for b in branches:
        rem = remotes.get(b["upstream_remote"] or "")
        if not b["upstream_remote"]:
            b["live"] = {
                "state": "local-only"
                if not b.get("on_any_remote_branch")
                else "no-upstream"
            }
        elif not online:
            b["live"] = {"state": "not-checked"}
        elif not rem or not rem.get("reachable"):
            b["live"] = {"state": "remote-unreachable"}
        else:
            b["live"] = _compare(repo, b["sha"], rem["heads"].get(b["upstream_branch"]))
    current = _git_out(repo, "rev-parse", "--abbrev-ref", "HEAD")
    cur = next((b for b in branches if b["name"] == current), None)
    out["current_branch_state"] = (
        cur["live"]["state"] if cur else ("detached" if out["detached"] else None)
    )
    head = _git_out(repo, "rev-parse", "HEAD")
    for name, rem in remotes.items():
        dflt = rem.get("default_branch")
        if rem.get("reachable") and dflt and head:
            rem["head_vs_default_branch"] = _compare(repo, head, rem["heads"].get(dflt))
        if rem.get("reachable"):
            local = {
                b["upstream_branch"] for b in branches if b["upstream_remote"] == name
            }
            rem["remote_branches_not_tracked_locally"] = len(set(rem["heads"]) - local)
    needs = []
    if out["dirty"]:
        needs.append("commit-or-clean")
    for b in branches:
        s = b["live"]["state"]
        if s in ("ahead", "diverged", "local-only"):
            needs.append(f"push:{b['name']}")
        if s in ("behind", "behind-unfetched", "diverged"):
            needs.append(f"pull:{b['name']}")
        if s == "upstream-gone":
            needs.append(f"upstream-gone:{b['name']}")
    if out["stash_count"]:
        needs.append(f"stashes:{out['stash_count']}")
    if out.get("in_progress"):
        needs.append("in-progress:" + ",".join(out["in_progress"]))
    out["needs"] = needs
    return out


def _mtime_snapshot(roots: list[Path]) -> dict[str, int]:
    """`path -> mtime_ns` for files under `roots` (skips `.git` and `.aw/worktrees`)."""
    snap: dict[str, int] = {}
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames[:] = [
                n
                for n in dirnames
                if n != ".git" and not (n == "worktrees" and dirpath.endswith(".aw"))
            ]
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                try:
                    snap[fp] = os.lstat(fp).st_mtime_ns
                except OSError:
                    continue
    return snap


def _changed(before: dict[str, int], after: dict[str, int]) -> list[str]:
    """Paths created, modified or deleted between two snapshots."""
    keys = set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k))


def _parse_json_output(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass
    # JSONL (aw.agent/v1): keep the last `result` record, else the last parseable line.
    last = None
    for line in text.splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        last = rec
        if isinstance(rec, dict) and rec.get("kind") == "result":
            return rec
    return last


def _summarize_aw(key: str, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"parsed": data is not None}
    if key == "attention":
        items = data.get("items") or []
        return {
            "valid": data.get("valid"),
            "schema_version": data.get("schema_version"),
            "violations": data.get("violations"),
            "stranded_lanes": len(data.get("stranded_lanes") or []),
            "parked_questions": len(data.get("parked_questions") or []),
            "item_count": len(items),
            "items": [
                {
                    k: i.get(k)
                    for k in ("id", "path", "tree", "native_status", "attention_class")
                }
                for i in items
                if isinstance(i, dict)
            ],
        }
    if key == "doctor":
        out = {k: v for k, v in data.items() if k != "data"}
        out["data_keys"] = (
            sorted(data["data"]) if isinstance(data.get("data"), dict) else None
        )
        return out
    return dict(data)


def run_aw(
    repo: Path, aw: str, timeout: float, extra_roots: list[Path], aw_home: Path
) -> dict[str, Any]:
    """Run the aw diagnostics in `repo` and record what each reported and whether anything changed."""
    _, before = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    roots = [repo / ".aw", repo / ".agents", *extra_roots]
    files_before = _mtime_snapshot(roots)
    home_before = _mtime_snapshot([aw_home / "config"])
    projects = aw_home / "projects"
    projects_before = (
        {e.name for e in os.scandir(projects)} if projects.is_dir() else set()
    )
    runs: dict[str, Any] = {}
    env = dict(os.environ, NO_COLOR="1")
    for key, args in _AW_COMMANDS:
        start = time.monotonic()
        try:
            res = subprocess.run(
                [aw, *args],
                cwd=repo,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired:
            runs[key] = {
                "argv": list(args),
                "exit": None,
                "timed_out": True,
                "timeout": timeout,
            }
            continue
        except OSError as exc:
            runs[key] = {"argv": list(args), "exit": None, "error": str(exc)}
            continue
        data = _parse_json_output(res.stdout)
        entry: dict[str, Any] = {
            "argv": list(args),
            "exit": res.returncode,
            "seconds": round(time.monotonic() - start, 1),
            "stdout_bytes": len(res.stdout),
            "result": _summarize_aw(key, data),
        }
        if data is None:
            entry["stdout_head"] = res.stdout[:4000]
        if res.stderr.strip():
            entry["stderr_tail"] = res.stderr[-4000:]
        runs[key] = entry
    _, after = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    b, a = set(before.splitlines()), set(after.splitlines())
    projects_after = (
        {e.name for e in os.scandir(projects)} if projects.is_dir() else set()
    )
    return {
        "commands": runs,
        "side_effects": {
            "git_status_added": sorted(a - b),
            "git_status_removed": sorted(b - a),
            "files_modified": _changed(files_before, _mtime_snapshot(roots))[:500],
            "aw_home_files_modified": _changed(
                home_before, _mtime_snapshot([aw_home / "config"])
            )[:200],
            "aw_home_projects_added": sorted(projects_after - projects_before),
        },
    }


def linked_worktree_of(path: Path) -> str | None:
    """The main repository's git dir when `path` is a linked worktree, else None.

    A linked worktree's `.git` is a FILE reading `gitdir: <main>/.git/worktrees/<name>`. A submodule
    also has a `.git` file, but its gitdir is under `.git/modules/`, so it is not treated as one.
    """
    git = path / ".git"
    if not git.is_file():
        return None
    try:
        line = git.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None
    gitdir = line[len("gitdir:") :].strip().replace("\\", "/")
    marker = "/.git/worktrees/"
    if marker in gitdir:
        return gitdir.split(marker, 1)[0]
    return None


def _is_candidate(path: Path) -> bool:
    return (path / ".git").exists() and (
        (path / ".aw").is_dir() or (path / ".agents").is_dir()
    )


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p))).resolve()


def registry_paths(
    home: Path, search_roots: list[tuple[str, str]] | None = None
) -> list[tuple[Path, str]]:
    """Repository paths the toolkit's user config and registry list on this machine.

    The config's `repos.search` entries are appended to `search_roots` (when given) as
    `(entry, source)` pairs, for the caller to scan.
    """
    out: list[tuple[Path, str]] = []
    cfg_dirs = []
    if os.environ.get("AW_CONFIG_DIR"):
        cfg_dirs.append(Path(os.environ["AW_CONFIG_DIR"]))
    if os.environ.get("XDG_CONFIG_HOME"):
        cfg_dirs.append(Path(os.environ["XDG_CONFIG_HOME"]) / "agent-workflows")
    cfg_dirs.append(home / ".config" / "agent-workflows")
    for d in cfg_dirs:
        try:
            data = json.loads((d / "config.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        repos = data.get("repos") if isinstance(data, dict) else None
        if isinstance(repos, dict):
            for key in ("installed", "ignore", "exclude"):
                for p in repos.get(key) or []:
                    if isinstance(p, str):
                        out.append((_expand(p), f"user-config:{key}"))
            if search_roots is not None:
                for p in repos.get("search") or []:
                    if isinstance(p, str):
                        search_roots.append(
                            (p, f"user-config:search ({d / 'config.json'})")
                        )
    try:
        reg = json.loads(
            (home / ".aw" / "config" / "registry.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        reg = None
    projects = reg.get("projects") if isinstance(reg, dict) else None
    items: Iterable[Any] = (
        projects.values() if isinstance(projects, dict) else (projects or [])
    )
    for entry in items:
        if not isinstance(entry, dict):
            continue
        for key in ("target_path", "target_paths", "path", "repo"):
            val = entry.get(key)
            for p in val if isinstance(val, list) else [val]:
                if isinstance(p, str):
                    out.append((_expand(p), "registry"))
    return out


def scan_for_repos(root: Path, max_depth: int) -> list[Path]:
    """Repositories under `root`: a directory with `.git` and `.aw/` or `.agents/`.

    The walk does not descend into a repository it found. Linked worktrees are returned too; the
    caller decides whether to survey them.
    """
    found: list[Path] = []
    root = root.resolve()
    stack = [(root, 0)]
    while stack:
        d, depth = stack.pop()
        try:
            if _is_candidate(d):
                found.append(d)
                continue
        except OSError:
            continue
        if depth >= max_depth:
            continue
        try:
            children = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            continue
        for e in children:
            try:
                if e.is_dir(follow_symlinks=False) and e.name not in _SCAN_SKIP:
                    stack.append((Path(e.path), depth + 1))
            except OSError:
                continue
    return found


def classify_name(name: str) -> dict[str, Any]:
    m = _CORE_FACET_RE.match(name)
    if m:
        return {
            "grammar": "clustered",
            "id6": m.group("id6"),
            "set": m.group("set"),
            "nn": m.group("nn"),
            "facet": m.group("facet"),
        }
    m = _CLUSTERED_PREFIX_RE.match(name)
    if m:
        return {
            "grammar": "clustered-prefix-only",
            "id6": m.group("id6"),
            "set": m.group("set"),
            "nn": m.group("nn"),
            "facet": None,
        }
    m = _LEGACY_TIMESTAMP_RE.match(name)
    if m:
        return {
            "grammar": "legacy-timestamp",
            "id6": None,
            "set": None,
            "nn": m.group("nn"),
            "facet": m.group("facet"),
        }
    if _WALKTHROUGH_DATED_RE.match(name) or _WALKTHROUGH_BARE_RE.match(name):
        return {
            "grammar": "walkthrough-suffix",
            "id6": None,
            "set": None,
            "nn": None,
            "facet": None,
        }
    if _DATED_SLUG_RE.match(name):
        return {
            "grammar": "dated-slug",
            "id6": None,
            "set": None,
            "nn": None,
            "facet": None,
        }
    if name in ("README.md", "INDEX.md", "index.md"):
        return {
            "grammar": "readme-or-index",
            "id6": None,
            "set": None,
            "nn": None,
            "facet": None,
        }
    return {"grammar": "other", "id6": None, "set": None, "nn": None, "facet": None}


def read_bullets(text: str) -> dict[str, Any]:
    """Bullets in the metadata region (before the first `## ` heading) and anywhere else."""
    head: dict[str, str] = {}
    head_keys: list[str] = []
    later_ids: list[str] = []
    yaml: dict[str, str] = {}
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 200)):
            if lines[i].strip() == "---":
                for ln in lines[1:i]:
                    m = _YAML_KEY_RE.match(ln)
                    if m:
                        yaml.setdefault(m.group(1), m.group(2).strip())
                start = i + 1
                break
    in_head = True
    for line in lines[start:]:
        if line.startswith("## "):
            in_head = False
        m = _BULLET_RE.match(line)
        if not m:
            continue
        key, val = m.group("key"), m.group("val")
        if in_head:
            head_keys.append(key)
            head.setdefault(key, val)
        elif key == "Id":
            later_ids.append(val)
    return {
        "head": {k: head[k] for k in _KEY_BULLETS if k in head},
        "head_keys": sorted(set(head_keys)),
        "duplicate_head_keys": sorted({k for k in head_keys if head_keys.count(k) > 1}),
        "ids_after_head": later_ids,
        "yaml_front_matter": yaml or None,
    }


def _sha256(path: Path) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def survey_tree(tree_root: Path, repo_root: Path, tracked: set[str]) -> dict[str, Any]:
    """Inventory one records tree (`.aw/`, `.agents/`, or a companion root)."""
    files: list[dict[str, Any]] = []
    bulk: dict[str, dict[str, int]] = {}
    dirs: dict[str, dict[str, int]] = {}
    for dirpath, dirnames, filenames in os.walk(tree_root, followlinks=False):
        d = Path(dirpath)
        rel_dir = d.relative_to(tree_root).as_posix()
        dirnames[:] = sorted(n for n in dirnames if n != ".git")
        parts = d.relative_to(tree_root).parts
        bulk_key = next((p for p in parts if p in _BULK_DIRS), None)
        if bulk_key is not None:
            top = "/".join(parts[: parts.index(bulk_key) + 1])
            b = bulk.setdefault(top, {"files": 0, "bytes": 0, "dirs": 0})
            b["dirs"] += 1
            for fn in filenames:
                b["files"] += 1
                try:
                    b["bytes"] += (d / fn).stat().st_size
                except OSError:
                    pass
            continue
        dstat = dirs.setdefault(rel_dir or ".", {})
        for fn in sorted(filenames):
            p = d / fn
            ext = p.suffix or "(none)"
            dstat[ext] = dstat.get(ext, 0) + 1
            try:
                rel_repo = p.relative_to(repo_root).as_posix()
            except ValueError:
                rel_repo = p.as_posix()
            entry: dict[str, Any] = {
                "path": p.relative_to(tree_root).as_posix(),
                "bytes": p.stat().st_size if p.exists() else None,
                "tracked": rel_repo in tracked,
                "symlink": p.is_symlink(),
                "sha256": _sha256(p),
            }
            if fn.endswith(".md"):
                name = classify_name(fn)
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    text = ""
                bl = read_bullets(text)
                head_id = bl["head"].get("Id") or (bl["yaml_front_matter"] or {}).get(
                    "id"
                )
                entry.update(name)
                entry["bullets"] = bl
                entry["title"] = next(
                    (ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")),
                    None,
                )
                entry["id_valid"] = bool(head_id and _ID6_RE.match(head_id))
                entry["id_matches_name"] = (
                    None if not name["id6"] else (head_id == name["id6"])
                )
            elif fn.endswith(".jsonl"):
                try:
                    with open(p, "rb") as f:
                        entry["lines"] = sum(1 for _ in f)
                except OSError:
                    entry["lines"] = None
            files.append(entry)
    return {
        "root": str(tree_root),
        "files": files,
        "dir_ext_counts": dirs,
        "bulk_dirs": bulk,
    }


def _read_small(path: Path) -> dict[str, Any]:
    try:
        st = path.stat()
    except OSError:
        return {"exists": False}
    out: dict[str, Any] = {
        "exists": True,
        "bytes": st.st_size,
        "symlink": path.is_symlink(),
    }
    if st.st_size <= _MAX_CONFIG_BYTES:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            out["error"] = str(exc)
            return out
        out["text"] = raw
        try:
            out["json"] = json.loads(raw)
        except ValueError:
            pass
    return out


def _records_backend(configs: dict[str, Any]) -> str | None:
    for key in (
        ".aw/config/local.json",
        ".aw/config/project.json",
        ".aw/config/config.json",
        ".agents/config.json",
    ):
        data = configs.get(key, {}).get("json")
        if isinstance(data, dict) and isinstance(data.get("records_backend"), str):
            return data["records_backend"]
    return None


def _companion_candidates(
    repo: Path, configs: dict[str, Any]
) -> list[tuple[Path, str]]:
    """Companion locations: an explicit `companion_dir` binding and the default `<repo>.aw`."""
    out: list[tuple[Path, str]] = []
    for key in (
        ".aw/config/local.json",
        ".aw/config/project.json",
        ".aw/config/config.json",
    ):
        data = configs.get(key, {}).get("json")
        if isinstance(data, dict) and isinstance(data.get("companion_dir"), str):
            c = Path(os.path.expanduser(data["companion_dir"]))
            out.append(
                ((repo / c).resolve() if not c.is_absolute() else c, f"config:{key}")
            )
    out.append((Path(f"{repo}.aw"), "default:<repo>.aw"))
    return out


def survey_repo(
    repo: Path, sources: list[str], opts: argparse.Namespace
) -> dict[str, Any]:
    rc, top = _git(repo, "rev-parse", "--show-toplevel")
    out: dict[str, Any] = {
        "path": str(repo),
        "found_via": sorted(set(sources)),
        "git_toplevel": top.strip() if rc == 0 else None,
    }
    out["head"] = _git(repo, "rev-parse", "HEAD")[1].strip()
    _, br = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    out["branch"] = br.strip()
    _, remotes = _git(repo, "remote", "-v")
    out["remotes"] = sorted(set(remotes.split("\n")) - {""})
    _, status = _git(repo, "status", "--porcelain", "--untracked-files=normal")
    out["dirty_entries"] = len([ln for ln in status.splitlines() if ln.strip()])
    _, wts = _git(repo, "worktree", "list", "--porcelain")
    out["worktrees"] = [ln[9:] for ln in wts.splitlines() if ln.startswith("worktree ")]
    _, ls = _git(repo, "ls-files", "-z")
    tracked = {p for p in ls.split("\0") if p}
    out["tracked_file_count"] = len(tracked)
    out["top_level"] = sorted(
        e.name + ("/" if e.is_dir() else "") for e in os.scandir(repo)
    )
    out["git"] = git_state(repo, online=not opts.offline)
    out["agent_files"] = {
        f: {
            "exists": True,
            "bytes": (repo / f).stat().st_size,
            "aw_block": "<!-- aw:block -->"
            in (repo / f).read_text(encoding="utf-8", errors="replace"),
        }
        for f in _AGENT_FILES
        if (repo / f).is_file()
    }
    out["agent_dirs"] = [d for d in _AGENT_DIRS if (repo / d).is_dir()]
    configs = {k: _read_small(repo / k) for k in _CONFIG_FILES}
    out["configs"] = {k: v for k, v in configs.items() if v.get("exists")}
    out["gitignore"] = _read_small(repo / ".gitignore").get("text")
    out["trees"] = {}
    for name in (".aw", ".agents"):
        if (repo / name).is_dir():
            out["trees"][name] = survey_tree(repo / name, repo, tracked)
    out["records_backend"] = _records_backend(configs)
    out["companions"] = []
    seen: set[Path] = set()
    for cpath, why in _companion_candidates(repo, configs):
        if cpath in seen:
            continue
        seen.add(cpath)
        entry: dict[str, Any] = {
            "path": str(cpath),
            "source": why,
            "exists": cpath.is_dir(),
        }
        if cpath.is_dir():
            _, cls = _git(cpath, "ls-files", "-z")
            ctracked = {p for p in cls.split("\0") if p}
            _, chead = _git(cpath, "rev-parse", "HEAD")
            entry["is_git"] = (cpath / ".git").exists()
            entry["head"] = chead.strip()
            entry["top_level"] = sorted(
                e.name + ("/" if e.is_dir() else "") for e in os.scandir(cpath)
            )
            entry["tree"] = survey_tree(cpath, cpath, ctracked)
            if entry["is_git"]:
                entry["git"] = git_state(cpath, online=not opts.offline)
        if entry["exists"] or why != "default:<repo>.aw":
            out["companions"].append(entry)
    if opts.aw:
        comp_roots = [Path(c["path"]) for c in out["companions"] if c["exists"]]
        out["aw_runs"] = run_aw(
            repo, opts.aw, opts.aw_timeout, comp_roots, opts.aw_home
        )
    return out


def _summary(repo: dict[str, Any]) -> str:
    parts = []
    for name, tree in repo["trees"].items():
        md = [f for f in tree["files"] if f["path"].endswith(".md")]
        parts.append(f"{name}: {len(md)} .md")
    for c in repo.get("companions") or []:
        if c.get("tree"):
            parts.append(f"companion {c['path']}: {len(c['tree']['files'])} files")
    g = repo.get("git") or {}
    if g:
        parts.append(
            f"git: {g.get('current_branch_state')}"
            + (f" needs {','.join(g['needs'])}" if g.get("needs") else "")
        )
    for k, v in ((repo.get("aw_runs") or {}).get("commands") or {}).items():
        parts.append(f"aw {k}: exit {v.get('exit')}")
    se = (repo.get("aw_runs") or {}).get("side_effects") or {}
    if any(se.values()):
        parts.append("AW CHANGED FILES")
    return ", ".join(parts) or "no trees"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", help="repository paths to survey")
    ap.add_argument(
        "--scan",
        action="append",
        default=[],
        metavar="DIR",
        help="search DIR for repositories (repeatable)",
    )
    ap.add_argument("--max-depth", type=int, default=4, help="--scan depth (default 4)")
    ap.add_argument(
        "--include-worktrees",
        action="store_true",
        help="also survey linked git worktrees (skipped by default: each is a second checkout "
        "of a repository that is surveyed already, so its records would be counted twice)",
    )
    ap.add_argument(
        "--no-registry",
        action="store_true",
        help="do not add repositories or search roots from the toolkit's config and registry",
    )
    ap.add_argument(
        "--offline",
        action="store_true",
        help="do not contact remotes (skips the live `git ls-remote` up-to-date check)",
    )
    ap.add_argument(
        "--no-run-aw",
        action="store_true",
        help="do not run `aw check`, `aw attention` and `aw doctor` in each repository",
    )
    ap.add_argument("--aw", help="the aw executable to run (default: `aw` on PATH)")
    ap.add_argument(
        "--aw-timeout",
        type=float,
        default=900,
        help="seconds allowed per aw command per repository (default 900)",
    )
    ap.add_argument(
        "-o",
        "--output",
        help="output JSON path (default ~/aw-survey/aw-repo-survey-<YYYYMMDD>-<host>-<HHMMSS>.json, UTC)",
    )
    args = ap.parse_args(argv)

    home = Path.home()
    host = socket.gethostname()
    stamp = _dt.datetime.now(_dt.timezone.utc)
    now = stamp.strftime("%Y%m%dT%H%M%SZ")
    args.aw_home = Path(os.environ.get("AW_HOME") or home / ".aw")
    aw_info: dict[str, Any] = {"requested": not args.no_run_aw}
    if args.no_run_aw:
        args.aw = None
    else:
        args.aw = args.aw or shutil.which("aw")
        aw_info["path"] = args.aw
        if args.aw:
            try:
                v = subprocess.run(
                    [args.aw, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                    stdin=subprocess.DEVNULL,
                )
                aw_info["version"] = (v.stdout or v.stderr).strip()[:300]
            except (OSError, subprocess.TimeoutExpired) as exc:
                aw_info["version_error"] = str(exc)
        else:
            print(
                "warning: `aw` not found on PATH; aw diagnostics skipped (use --aw PATH)",
                file=sys.stderr,
            )
    scans = [(s, "--scan") for s in args.scan]
    if not args.paths and not scans:
        scans = [(str(home), "default (no paths or --scan given)")]

    candidates: dict[Path, list[str]] = {}
    missing: list[dict[str, str]] = []
    ignored_search_roots: list[dict[str, str]] = []
    for p in args.paths:
        rp = _expand(p)
        candidates.setdefault(rp, []).append("argument")
    if not args.no_registry:
        config_search: list[tuple[str, str]] = []
        for rp, src in registry_paths(home, config_search):
            candidates.setdefault(rp, []).append(src)
        for entry, src in config_search:
            # A relative entry would resolve against whatever directory the script runs from,
            # which is not what the config author meant; record it instead of guessing.
            if not os.path.isabs(os.path.expanduser(os.path.expandvars(entry))):
                ignored_search_roots.append(
                    {"entry": entry, "source": src, "reason": "relative path"}
                )
                continue
            scans.append((entry, src))
    scanned: list[dict[str, Any]] = []
    by_root: dict[Path, dict[str, Any]] = {}
    for s, src in scans:
        root = _expand(s)
        if root in by_root:
            by_root[root]["source"] += f"; {src}"
            continue
        if not root.is_dir():
            by_root[root] = {
                "root": str(root),
                "source": src,
                "exists": False,
                "found": 0,
            }
            scanned.append(by_root[root])
            continue
        found = scan_for_repos(root, args.max_depth)
        by_root[root] = {
            "root": str(root),
            "source": src,
            "exists": True,
            "found": len(found),
        }
        scanned.append(by_root[root])
        for rp in found:
            candidates.setdefault(rp, []).append(f"scan:{root}")

    repos: list[dict[str, Any]] = []
    for rp in sorted(candidates):
        srcs = candidates[rp]
        if not rp.is_dir():
            missing.append(
                {
                    "path": str(rp),
                    "found_via": ",".join(sorted(set(srcs))),
                    "reason": "not a directory",
                }
            )
            continue
        main_repo = linked_worktree_of(rp)
        if main_repo is not None and not args.include_worktrees:
            missing.append(
                {
                    "path": str(rp),
                    "found_via": ",".join(sorted(set(srcs))),
                    "reason": f"linked worktree of {main_repo} (use --include-worktrees)",
                }
            )
            continue
        if not _is_candidate(rp):
            missing.append(
                {
                    "path": str(rp),
                    "found_via": ",".join(sorted(set(srcs))),
                    "reason": "no .git with .aw/ or .agents/",
                }
            )
            continue
        print(f"surveying {rp} ...", file=sys.stderr, flush=True)
        try:
            r = survey_repo(rp, srcs, args)
        except Exception as exc:  # noqa: BLE001 - keep going; record the failure
            repos.append({"path": str(rp), "found_via": srcs, "error": repr(exc)})
            continue
        repos.append(r)
        print(f"  {_summary(r)}", file=sys.stderr, flush=True)

    aw_home = args.aw_home
    home_projects: list[dict[str, Any]] = []
    proj_root = aw_home / "projects"
    if proj_root.is_dir():
        for e in sorted(os.scandir(proj_root), key=lambda x: x.name):
            if not e.is_dir():
                continue
            pp = Path(e.path)
            print(f"surveying home project {pp} ...", file=sys.stderr, flush=True)
            home_projects.append(
                {
                    "path": str(pp),
                    "top_level": sorted(
                        x.name + ("/" if x.is_dir() else "") for x in os.scandir(pp)
                    ),
                    "tree": survey_tree(pp, pp, set()),
                }
            )

    doc = {
        "schema": SCHEMA,
        "masked": False,
        "generated_at": now,
        "host": host,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "git_version": (_git(home, "--version")[1] or "").strip(),
        "aw": aw_info,
        "offline": args.offline,
        "argv": sys.argv,
        "home": str(home),
        "scans": scanned,
        "ignored_search_roots": ignored_search_roots,
        "include_worktrees": args.include_worktrees,
        "aw_home": str(aw_home),
        "repos": repos,
        "home_projects": home_projects,
        "skipped": missing,
    }
    out = (
        Path(args.output)
        if args.output
        else home
        / "aw-survey"
        / f"aw-repo-survey-{stamp:%Y%m%d}-{host}-{stamp:%H%M%S}.json"
    )
    created: list[str] = []
    missing_dirs = [d for d in [out.parent, *out.parent.parents] if not d.exists()]
    out.parent.mkdir(parents=True, exist_ok=True)
    created += [f"{d}/ (directory)" for d in reversed(missing_dirs)]
    existed = out.exists()
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    created.append(
        f"{out}{' (overwritten)' if existed else ''} ({out.stat().st_size:,} bytes)"
    )
    worktrees = sum(1 for m in missing if m["reason"].startswith("linked worktree"))
    print(
        f"\n{len(repos)} repositories surveyed, {len(missing)} skipped "
        f"({worktrees} linked worktrees), {len(home_projects)} home projects.",
        file=sys.stderr,
    )
    attention = [r for r in repos if (r.get("git") or {}).get("needs")]
    if attention:
        print("Repositories needing attention:", file=sys.stderr)
        for r in attention:
            print(f"  {r['path']}: {', '.join(r['git']['needs'])}", file=sys.stderr)
    changed = [
        r["path"]
        for r in repos
        if any(((r.get("aw_runs") or {}).get("side_effects") or {}).values())
    ]
    if changed:
        print("WARNING: aw commands changed files in:", file=sys.stderr)
        for p in changed:
            print(f"  {p}", file=sys.stderr)
    print("Files created (UNMASKED; do not commit or share):", file=sys.stderr)
    for c in created:
        print(f"  {c}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
