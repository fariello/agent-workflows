#!/usr/bin/env python3
"""Survey every agent-workflows repository on this machine and write an UNMASKED inventory.

WHY THIS EXISTS. Plan `9vf2iv` builds migration fixtures, one per repository layout the metadata
migration must handle. Its evidence came from this public repository's history and from counts
recorded once by hand. This script gathers the same facts from every repository on a server, raw,
so the data can be inspected before anyone decides how to analyze, anonymize, or record it.

THE OUTPUT IS NOT ANONYMIZED. It contains absolute paths, hostnames, remote URLs and file names.
Keep it out of any tracked tree and do not share it. No masking is done here on purpose.

STANDALONE. Python 3.8+ standard library only; it never imports `agent_workflows`, so it runs on a
server with an old toolkit or none. The name grammars below are copies of the toolkit's
(`agent_workflows/artifact_naming.py`) and may drift from it; the per-file records let a reader see
what each name was classified as.

READ-ONLY. It runs only read-only git commands (`rev-parse`, `ls-files`, `remote -v`, `status`,
`worktree list`) and reads files. It writes nothing except the output file.

Usage:
    python3 aw_repo_survey.py [PATH ...] [--scan DIR ...] [--no-registry] [-o OUT.json]

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
import socket
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SCHEMA = "aw-repo-survey/v1"

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
)
_MAX_CONFIG_BYTES = 64 * 1024


def _git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        res = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return res.returncode, res.stdout


def _is_candidate(path: Path) -> bool:
    return (path / ".git").exists() and (
        (path / ".aw").is_dir() or (path / ".agents").is_dir()
    )


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p))).resolve()


def registry_paths(home: Path) -> list[tuple[Path, str]]:
    """Repository paths the toolkit's user config and registry list on this machine."""
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


def survey_repo(repo: Path, sources: list[str]) -> dict[str, Any]:
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
        if entry["exists"] or why != "default:<repo>.aw":
            out["companions"].append(entry)
    return out


def _summary(repo: dict[str, Any]) -> str:
    parts = []
    for name, tree in repo["trees"].items():
        md = [f for f in tree["files"] if f["path"].endswith(".md")]
        parts.append(f"{name}: {len(md)} .md")
    for c in repo.get("companions") or []:
        if c.get("tree"):
            parts.append(f"companion {c['path']}: {len(c['tree']['files'])} files")
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
        "--no-registry",
        action="store_true",
        help="do not add repositories from the toolkit's config and registry",
    )
    ap.add_argument(
        "-o",
        "--output",
        help="output JSON path (default ~/aw-survey/<host>-<utc>.json)",
    )
    args = ap.parse_args(argv)

    home = Path.home()
    host = socket.gethostname()
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    scans = list(args.scan)
    if not args.paths and not scans:
        scans = [str(home)]

    candidates: dict[Path, list[str]] = {}
    missing: list[dict[str, str]] = []
    for p in args.paths:
        rp = _expand(p)
        candidates.setdefault(rp, []).append("argument")
    if not args.no_registry:
        for rp, src in registry_paths(home):
            candidates.setdefault(rp, []).append(src)
    for s in scans:
        for rp in scan_for_repos(_expand(s), args.max_depth):
            candidates.setdefault(rp, []).append(f"scan:{s}")

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
            r = survey_repo(rp, srcs)
        except Exception as exc:  # noqa: BLE001 - keep going; record the failure
            repos.append({"path": str(rp), "found_via": srcs, "error": repr(exc)})
            continue
        repos.append(r)
        print(f"  {_summary(r)}", file=sys.stderr, flush=True)

    aw_home = Path(os.environ.get("AW_HOME") or home / ".aw")
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
        "argv": sys.argv,
        "home": str(home),
        "scans": scans,
        "aw_home": str(aw_home),
        "repos": repos,
        "home_projects": home_projects,
        "skipped": missing,
    }
    out = (
        Path(args.output) if args.output else home / "aw-survey" / f"{host}-{now}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"wrote {out} ({len(repos)} repositories, {len(missing)} skipped)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
