#!/usr/bin/env python3
"""
normalize_plan_names.py - check and (on request) normalize plan filenames to the
canonical convention `YYYYMMDD-HHMM-NN-<slug>.md` (DECISIONS D48).

This is the deterministic, mechanical layer the agent-driven `setup-repo` wizard
orchestrates. `--check` (default) reports which plan files in the lifecycle dirs do NOT
conform and what they would be renamed to; `--apply` performs the renames with `git mv`
(staged, never committed) after the wizard has shown the preview and the user has agreed.

Convention:
  YYYYMMDD-HHMM-NN-<slug>.md
    YYYYMMDD  creation date (UTC)
    HHMM      creation time, 24h (UTC)
    NN        two-digit sequence within that exact YYYYMMDD-HHMM. 00 is reserved (by
              convention, not enforced) for an orchestrator plan; ordinary plans use 01+.
    <slug>    lowercase kebab-case, [a-z0-9-]+, no leading/trailing hyphen.

Legacy `YYYYMMDD-<slug>.md` files are normalized: HHMM is derived from the file's first
git-commit (author) time in UTC (fallback 0000), NN is assigned by same-minute collision
order (never 00), and the slug is lowercased/kebabed.

Usage:
  python3 normalize_plan_names.py --repo .                 # check (text), exit 1 if any nonconforming
  python3 normalize_plan_names.py --repo . --format json   # machine-readable check
  python3 normalize_plan_names.py --repo . --apply         # perform staged git mv renames
  python3 normalize_plan_names.py --version

Exit codes: 0 = clean (or --apply succeeded); 1 = nonconforming files found (--check) or a
            rename conflict occurred (--apply); 2 = usage error.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path
from typing import NamedTuple, Optional

# The plan lifecycle dirs governed by the convention. Mirrors engine.PLAN_LIFECYCLE_SUBDIRS
# plus the `done/` alias; kept as a local constant so this tool stays standalone (it is
# copied into target repos with no import path back to the package).
LIFECYCLE_SUBDIRS = (
    "pending",
    "executed",
    "superseded",
    "not-executed",
    "reusable",
    "done",
)

PLANS_DIR = ".agents/plans"

# New canonical form: YYYYMMDD-HHMM-NN-<slug>.md
_NEW_RE = re.compile(
    r"^(?P<date>\d{8})-(?P<time>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
# Legacy form: YYYYMMDD-<slug>.md  (slug may be any non-space-ish text we will normalize)
_LEGACY_RE = re.compile(r"^(?P<date>\d{8})-(?P<slug>.+)\.md$")


def _framework_version() -> str:
    """Return the framework version from the neighboring VERSION file (three dirs up)."""

    version_path = Path(__file__).resolve().parent.parent.parent / "VERSION"
    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


class Parsed(NamedTuple):
    date: str
    time: Optional[str]  # None for legacy (no HHMM)
    nn: Optional[str]  # None for legacy
    slug: str
    conformant: bool


def normalize_slug(raw: str) -> str:
    """Lowercase kebab-case a slug: [a-z0-9] runs joined by single hyphens.

    An empty result (e.g. all-punctuation) falls back to 'untitled'.
    """

    s = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return s or "untitled"


def parse_name(filename: str) -> Optional[Parsed]:
    """Parse a plan filename in the new or legacy form; None if unrecognized."""

    m = _NEW_RE.match(filename)
    if m:
        return Parsed(
            m.group("date"), m.group("time"), m.group("nn"), m.group("slug"), True
        )
    m = _LEGACY_RE.match(filename)
    if m:
        # A legacy match is only "recognized" if the date is a plausible YYYYMMDD.
        return Parsed(m.group("date"), None, None, m.group("slug"), False)
    return None


def is_conformant(filename: str) -> bool:
    """True only for a fully valid new-format name with a clean lowercase-kebab slug."""

    m = _NEW_RE.match(filename)
    if not m:
        return False
    # Slug must already be normalized (no double hyphens, no leading/trailing hyphen,
    # only [a-z0-9-]); the regex enforces this shape.
    return True


def _utc_now_hhmm() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%H%M")


def git_first_commit_hhmm(repo_root: Path, rel_path: str) -> Optional[str]:
    """Return the file's first-commit author time as UTC 'YYYYMMDD-HHMM', or None.

    Uses `--follow` so a file renamed by earlier migrations traces back to its ORIGINAL
    creation, and takes the OLDEST such author time. Converts to UTC via TZ=UTC +
    --date=format-local. Returns None on any failure (non-git, untracked, git missing).
    """

    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "log",
                "--follow",
                "--diff-filter=A",
                "--date=format-local:%Y%m%d-%H%M",
                "--format=%ad",
                "--",
                rel_path,
            ],
            capture_output=True,
            text=True,
            env={**_utc_env()},
        )
    except (OSError, ValueError):
        return None
    if proc.returncode != 0:
        return None
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    # The last line is the oldest commit (git log is newest-first).
    return lines[-1]


def _utc_env() -> dict:
    import os

    env = dict(os.environ)
    env["TZ"] = "UTC"
    return env


class Rename(NamedTuple):
    old: str  # repo-relative posix path
    new: str  # repo-relative posix path
    reason: str  # "legacy", "slug", or "conflict"


def _time_and_date_for(repo_root: Path, rel_path: str, parsed: Parsed) -> str:
    """Return 'YYYYMMDD-HHMM' for a file being normalized."""

    git_stamp = git_first_commit_hhmm(repo_root, rel_path)
    if git_stamp is not None:
        return git_stamp
    # Fallback: keep the legacy date, time 0000.
    return f"{parsed.date}-0000"


def scan(repo_root: Path, subdirs=LIFECYCLE_SUBDIRS) -> list:
    """Return the list of Rename actions for every nonconforming plan file.

    Conformant files are excluded (idempotent). NN is assigned per YYYYMMDD-HHMM over the
    whole batch, counting already-present conformant files at that timestamp, and never
    using 00. A computed target that already exists advances NN; if still colliding, the
    file is recorded as a conflict (reason="conflict") and not moved.
    """

    repo_root = Path(repo_root)
    # taken[(date,time)] = set of NN ints already used (by conformant files + planned).
    taken: dict = {}
    # Seed with existing conformant files so we do not collide with them.
    existing_paths = set()
    candidates = []  # (rel_path, parsed) for nonconforming files needing rename

    for sub in subdirs:
        d = repo_root / PLANS_DIR / sub
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.md")):
            rel = path.relative_to(repo_root).as_posix()
            existing_paths.add(rel)
            name = path.name
            if is_conformant(name):
                p = parse_name(name)
                if p is not None and p.nn is not None:
                    taken.setdefault((p.date, p.time), set()).add(int(p.nn))
                continue
            parsed = parse_name(name)
            if parsed is None:
                # Unrecognized (not even a legacy date prefix): report as conflict so it
                # is surfaced, but do not guess a rename.
                candidates.append((rel, None))
            else:
                candidates.append((rel, parsed))

    renames = []
    for rel, parsed in candidates:
        if parsed is None:
            renames.append(Rename(rel, rel, "conflict"))
            continue
        sub = Path(rel).parent.as_posix()  # e.g. .agents/plans/pending
        stamp = _time_and_date_for(repo_root, rel, parsed)  # YYYYMMDD-HHMM
        date, time = stamp.split("-")
        slug = normalize_slug(parsed.slug)
        used = taken.setdefault((date, time), set())
        # Assign the next free NN starting at 01 (never 00).
        nn = 1
        while nn in used:
            nn += 1
        candidate_name = f"{date}-{time}-{nn:02d}-{slug}.md"
        candidate_rel = f"{sub}/{candidate_name}"
        # Target-collision guard against files on disk not in our taken set.
        guard = 0
        while (
            (repo_root / candidate_rel).exists()
            and candidate_rel != rel
            and guard < 100
        ):
            nn += 1
            while nn in used:
                nn += 1
            candidate_name = f"{date}-{time}-{nn:02d}-{slug}.md"
            candidate_rel = f"{sub}/{candidate_name}"
            guard += 1
        if (repo_root / candidate_rel).exists() and candidate_rel != rel:
            renames.append(Rename(rel, rel, "conflict"))
            continue
        used.add(nn)
        reason = "legacy" if parsed.time is None else "slug"
        renames.append(Rename(rel, candidate_rel, reason))

    return renames


def _git_tracked(repo_root: Path, rel: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", rel],
            capture_output=True,
            text=True,
        )
    except (OSError, ValueError):
        return False
    return proc.returncode == 0


def apply(renames, repo_root: Path, use_git: bool = True) -> list:
    """Perform the renames (git mv when tracked, else filesystem mv). Staged, not committed.

    Skips (and reports) any Rename whose reason is "conflict" or whose target already
    exists, so nothing is ever clobbered. Returns a list of human-readable action strings.
    """

    repo_root = Path(repo_root)
    actions = []
    for r in renames:
        if r.reason == "conflict" or r.old == r.new:
            actions.append(f"CONFLICT (skipped): {r.old}")
            continue
        dest = repo_root / r.new
        if dest.exists():
            actions.append(f"CONFLICT (target exists, skipped): {r.old} -> {r.new}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if use_git and _git_tracked(repo_root, r.old):
            proc = subprocess.run(
                ["git", "-C", str(repo_root), "mv", "--", r.old, r.new],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                # Fall back to filesystem move + stage.
                (repo_root / r.old).rename(dest)
                subprocess.run(
                    ["git", "-C", str(repo_root), "add", "--", r.new, r.old],
                    capture_output=True,
                    text=True,
                )
        else:
            (repo_root / r.old).rename(dest)
        actions.append(f"renamed [{r.reason}]: {r.old} -> {r.new}")
    return actions


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Check/normalize plan filenames to YYYYMMDD-HHMM-NN-<slug>.md."
    )
    ap.add_argument(
        "--version", action="store_true", help="Print framework version and exit."
    )
    ap.add_argument(
        "--repo", default=".", help="Repository root (default: current dir)."
    )
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Perform the staged git-mv renames (default is check-only).",
    )
    args = ap.parse_args(argv)

    if args.version:
        print(_framework_version())
        return 0

    repo_root = Path(args.repo).expanduser().resolve()
    renames = scan(repo_root)
    nonconforming = [r for r in renames if r.old != r.new or r.reason == "conflict"]

    if args.apply:
        actions = apply(renames, repo_root)
        conflicts = [a for a in actions if a.startswith("CONFLICT")]
        if args.format == "json":
            print(json.dumps({"actions": actions, "conflicts": conflicts}, indent=2))
        else:
            for a in actions:
                print(a)
            print(
                f"\n{len(actions) - len(conflicts)} renamed (staged), {len(conflicts)} conflict(s)."
            )
        return 1 if conflicts else 0

    # Check mode.
    if args.format == "json":
        print(
            json.dumps(
                {
                    "nonconforming": [
                        {"old": r.old, "new": r.new, "reason": r.reason}
                        for r in nonconforming
                    ]
                },
                indent=2,
            )
        )
    else:
        if not nonconforming:
            print("All plan filenames conform to YYYYMMDD-HHMM-NN-<slug>.md.")
        else:
            print("Plan files that do not conform (old -> proposed new):")
            for r in nonconforming:
                if r.reason == "conflict":
                    print(f"  CONFLICT (cannot auto-name): {r.old}")
                else:
                    print(f"  {r.old}  ->  {r.new}  [{r.reason}]")
            print(
                f"\n{len(nonconforming)} file(s) need normalizing. "
                "Run with --apply to perform staged git-mv renames."
            )
    return 1 if nonconforming else 0


if __name__ == "__main__":
    raise SystemExit(main())
