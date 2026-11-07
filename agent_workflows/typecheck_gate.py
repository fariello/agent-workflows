"""Attributable static type checking: judge a change by the mypy errors it ADDS, not the ones it inherits.

WHY THIS EXISTS (run `run-20261107T023507Z-1895321`). A hand commit put one mypy `no-redef` error on
`main`. Every lane of the next unattended run branched from that broken `main`, and the integration
gate ran `mypy agent_workflows` on each lane's tip and refused all five verified lanes over an error
none of them had introduced; sixteen dependents were then never attempted. A lane-tip-only check
cannot distinguish "this lane broke the types" from "the types were already broken", so it blamed
every lane for `main`'s defect.

THREE CALLERS SHARE THIS ONE MODULE so they cannot disagree about what counts as a new error:

* the lane integration gate (`runner_shared.check_lane_type_safety`) compares the lane's committed
  tip against the lane's base commit;
* the pre-commit hook (`python3 -m agent_workflows.typecheck_gate staged`) compares the STAGED tree
  against `HEAD`, so it judges exactly what is being committed and never a co-worker's unstaged edit
  in a shared checkout;
* the run-start gate (`runner_shared.enforce_main_typecheck_gate`) checks the committed `HEAD` every
  lane will branch from, and refuses (or asks) before any agent turn is spent.

EVERYTHING IS CHECKED FROM A COMMITTED TREE, extracted into a private temporary directory with
`git archive`, never from a working tree. That is what makes the answer a property of a commit (or
of the index) rather than of whatever happens to be on disk.

A SHARED MYPY CACHE under `<git-common-dir>/aw-mypy-cache` keeps this cheap. Measured on this
repository (2026-11-07): a cold `mypy agent_workflows` takes about 21s; a second run of the same
tree extracted into a DIFFERENT temporary directory takes about 0.24s, so the per-directory
extraction does not defeat the cache.

ERRORS ARE COMPARED AS A MULTISET WITH LINE NUMBERS REMOVED. A lane that inserts lines above a
pre-existing error moves that error's line number (measured: the same `no-redef` was reported at
40271 on one lane and 40289 on another), and the message itself can carry one ("already defined on
line 40234"). Keying on `(path, message-with-line-numbers-normalized)` keeps an inherited error
inherited, and counting occurrences means a lane that adds a SECOND copy of an existing error is
still caught.
"""

from __future__ import annotations

import argparse
import collections
import io
import re
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

#: The package mypy is run over. The gate is specific to this toolkit's own package: a repository
#: without it never reaches a type check (every caller first asks :func:`applies`).
MYPY_TARGET = "agent_workflows"

#: Paths extracted alongside the package so mypy reads the same configuration it reads in a checkout.
CONFIG_PATHS: tuple[str, ...] = ("pyproject.toml", "setup.cfg", "mypy.ini", ".mypy.ini")

#: Wall-clock limit for one mypy run. A cold run of this repository measured about 21s.
MYPY_TIMEOUT_SECONDS = 600

_ERROR_LINE_RE = re.compile(
    r"^(?P<path>[^:\n]+):(?P<line>\d+)(?::\d+)?: error: (?P<msg>.*)$"
)
_LINE_REF_RE = re.compile(r"\bline \d+\b")


@dataclass
class MypyRun:
    """The outcome of one mypy run over one extracted tree."""

    #: True when mypy ran and reported no errors.
    ok: bool
    #: The `error:` lines mypy printed, verbatim.
    errors: list[str] = field(default_factory=list)
    #: Set when the check could not be performed at all (extraction failed, mypy missing, crashed,
    #: timed out, or exited non-zero without printing a parsable error). Callers fail closed on it.
    failure: str | None = None


@dataclass
class Comparison:
    """The errors a head tree carries that its base tree does not."""

    #: The head tree's `error:` lines that are NOT accounted for by the base tree.
    new_errors: list[str]
    #: How many head errors were inherited from the base and therefore ignored.
    inherited_count: int
    #: The base run, kept so a caller can report what the base already carried.
    base: MypyRun
    #: The head run.
    head: MypyRun
    #: Set when either side could not be checked. ``new_errors`` is then meaningless.
    failure: str | None = None

    @property
    def ok(self) -> bool:
        return self.failure is None and not self.new_errors


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=check,
    )


def mypy_cache_dir(repo: Path) -> Path | None:
    """`<git-common-dir>/aw-mypy-cache`, shared by every worktree of `repo`, or None outside git."""

    try:
        proc = _git(Path(repo), "rev-parse", "--git-common-dir", check=False)
    except OSError:
        return None
    out = proc.stdout.decode("utf-8", "replace").strip()
    if proc.returncode != 0 or not out:
        return None
    return (Path(repo) / out).resolve() / "aw-mypy-cache"


def tree_has_target(repo: Path, treeish: str) -> bool:
    """Whether `treeish` contains the type-checked package at all."""

    proc = _git(Path(repo), "ls-tree", "--name-only", treeish, check=False)
    if proc.returncode != 0:
        return False
    names = proc.stdout.decode("utf-8", "replace").splitlines()
    return MYPY_TARGET in names


def _tree_declares_mypy(repo: Path, treeish: str) -> bool:
    """Whether `treeish` carries a mypy configuration (a `[tool.mypy]` table or a mypy ini file)."""

    for name in CONFIG_PATHS:
        proc = _git(Path(repo), "show", f"{treeish}:{name}", check=False)
        if proc.returncode != 0:
            continue
        if name in ("mypy.ini", ".mypy.ini"):
            return True
        text = proc.stdout.decode("utf-8", "replace")
        header = "[tool.mypy]" if name == "pyproject.toml" else "[mypy]"
        if any(line.strip() == header for line in text.splitlines()):
            return True
    return False


def applies(repo: Path, treeish: str = "HEAD") -> bool:
    """Whether the run-start gate applies to `repo` at `treeish`.

    BOTH the package AND a committed mypy configuration must be present. The configuration
    requirement is what makes this a statement about a repository that TYPE-CHECKS ITSELF: a
    target repo that merely vendors or copies an `agent_workflows/` directory, without the
    configuration that makes `mypy agent_workflows` meaningful there, would otherwise be judged by
    mypy's strict defaults and refused for hundreds of errors no one there has opted into (measured:
    575 on a config-less copy of this package).
    """

    return tree_has_target(repo, treeish) and _tree_declares_mypy(repo, treeish)


def materialize(repo: Path, treeish: str, dest: Path) -> None:
    """Extract the package and its mypy configuration from `treeish` into `dest`.

    Uses `git archive` so the result is exactly the committed (or staged, via a tree id) content and
    never the working tree. Raises `RuntimeError` naming the git failure.
    """

    repo = Path(repo)
    listing = _git(repo, "ls-tree", "--name-only", treeish, check=False)
    if listing.returncode != 0:
        raise RuntimeError(
            f"cannot read tree {treeish!r}: "
            + listing.stderr.decode("utf-8", "replace").strip()
        )
    present = set(listing.stdout.decode("utf-8", "replace").splitlines())
    paths = [p for p in (MYPY_TARGET, *CONFIG_PATHS) if p in present]
    if MYPY_TARGET not in paths:
        raise RuntimeError(f"tree {treeish!r} has no {MYPY_TARGET}/ package")
    proc = _git(repo, "archive", "--format=tar", treeish, "--", *paths, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"git archive {treeish!r} failed: "
            + proc.stderr.decode("utf-8", "replace").strip()
        )
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as tar:
        members = [
            m
            for m in tar.getmembers()
            if not (m.name.startswith("/") or ".." in Path(m.name).parts)
        ]
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, members=members, filter="data")
        else:  # pragma: no cover - Python without PEP 706 filters
            tar.extractall(dest, members=members)


def run_mypy(tree_dir: Path, *, cache_dir: Path | None = None) -> MypyRun:
    """Run `mypy agent_workflows` inside `tree_dir` and parse its `error:` lines."""

    cmd = [sys.executable, "-m", "mypy", MYPY_TARGET]
    if cache_dir is not None:
        cmd += ["--cache-dir", str(cache_dir)]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(tree_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=MYPY_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return MypyRun(
            ok=False, failure=f"mypy timed out after {MYPY_TIMEOUT_SECONDS}s"
        )
    except OSError as exc:
        return MypyRun(ok=False, failure=f"failed to execute mypy: {exc}")
    errors = [
        ln.rstrip()
        for ln in proc.stdout.splitlines()
        if _ERROR_LINE_RE.match(ln.rstrip())
    ]
    if proc.returncode == 0:
        return MypyRun(ok=True)
    if not errors:
        detail = proc.stdout.strip() or f"exit {proc.returncode}"
        return MypyRun(
            ok=False, failure=f"mypy did not report parsable errors: {detail}"
        )
    return MypyRun(ok=False, errors=errors)


def check_tree(repo: Path, treeish: str, *, cache_dir: Path | None = None) -> MypyRun:
    """Extract `treeish` to a private temporary directory and type-check it."""

    if cache_dir is None:
        cache_dir = mypy_cache_dir(repo)
    with tempfile.TemporaryDirectory(prefix="aw-typecheck-") as tmp:
        try:
            materialize(repo, treeish, Path(tmp))
        except RuntimeError as exc:
            return MypyRun(ok=False, failure=str(exc))
        return run_mypy(Path(tmp), cache_dir=cache_dir)


def error_key(line: str) -> tuple[str, str]:
    """The identity of an error with its position removed: `(path, message)`.

    Line numbers are stripped from the location AND normalized inside the message, because both move
    when unrelated lines are inserted above the error.
    """

    m = _ERROR_LINE_RE.match(line.rstrip())
    if not m:
        return ("", _LINE_REF_RE.sub("line N", line.strip()))
    return (m.group("path"), _LINE_REF_RE.sub("line N", m.group("msg").strip()))


def new_errors(base_errors: Sequence[str], head_errors: Sequence[str]) -> list[str]:
    """Head errors not accounted for by the base, compared as a multiset of :func:`error_key`."""

    remaining = collections.Counter(error_key(e) for e in base_errors)
    added: list[str] = []
    for err in head_errors:
        key = error_key(err)
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            added.append(err)
    return added


def compare_trees(
    repo: Path,
    base_treeish: str,
    head_treeish: str,
    *,
    cache_dir: Path | None = None,
) -> Comparison:
    """Type-check `head_treeish` and report only the errors it adds relative to `base_treeish`.

    The base is checked ONLY when the head has errors, so the common clean case costs one run.
    """

    if cache_dir is None:
        cache_dir = mypy_cache_dir(repo)
    head = check_tree(repo, head_treeish, cache_dir=cache_dir)
    empty = MypyRun(ok=True)
    if head.failure:
        return Comparison([], 0, empty, head, failure=head.failure)
    if head.ok:
        return Comparison([], 0, empty, head)
    if not tree_has_target(repo, base_treeish):
        # The base predates the package, so every error is new.
        return Comparison(list(head.errors), 0, empty, head)
    base = check_tree(repo, base_treeish, cache_dir=cache_dir)
    if base.failure:
        return Comparison(
            [],
            0,
            base,
            head,
            failure=f"cannot type-check base {base_treeish}: {base.failure}",
        )
    added = new_errors(base.errors, head.errors)
    return Comparison(added, len(head.errors) - len(added), base, head)


def staged_tree(repo: Path) -> str:
    """The tree id of the index (`git write-tree`). Raises `RuntimeError` on an unmerged index."""

    proc = _git(Path(repo), "write-tree", check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            "git write-tree failed: " + proc.stderr.decode("utf-8", "replace").strip()
        )
    return proc.stdout.decode("utf-8").strip()


def _staged_touches_target(repo: Path) -> bool:
    proc = _git(
        Path(repo),
        "diff",
        "--cached",
        "--name-only",
        "--diff-filter=ACMRD",
        check=False,
    )
    names = proc.stdout.decode("utf-8", "replace").splitlines()
    return any(
        n.startswith(MYPY_TARGET + "/") and n.endswith(".py") for n in names
    ) or any(n in CONFIG_PATHS for n in names)


def staged_main(repo: Path, *, out=None) -> int:
    """Pre-commit entry: refuse a commit whose STAGED tree adds mypy errors relative to `HEAD`."""

    out = out or sys.stdout
    repo = Path(repo)
    if not _staged_touches_target(repo):
        return 0
    try:
        tree = staged_tree(repo)
    except RuntimeError as exc:
        print(f"typecheck: {exc}", file=out)
        return 1
    head_ok = (
        _git(repo, "rev-parse", "--verify", "-q", "HEAD", check=False).returncode == 0
    )
    if not head_ok:
        # First commit: nothing to inherit from, so check the staged tree outright.
        run = check_tree(repo, tree)
        cmp = Comparison(
            list(run.errors), 0, MypyRun(ok=True), run, failure=run.failure
        )
    else:
        cmp = compare_trees(repo, "HEAD", tree)
    if cmp.failure:
        print(
            f"typecheck: could not type-check the staged tree: {cmp.failure}", file=out
        )
        return 1
    if cmp.new_errors:
        print(
            f"typecheck: the staged change adds {len(cmp.new_errors)} mypy error(s) "
            "relative to HEAD:",
            file=out,
        )
        for err in cmp.new_errors:
            print(f"  {err}", file=out)
        return 1
    if cmp.inherited_count:
        print(
            f"typecheck: no new errors; HEAD already carries {cmp.inherited_count} mypy "
            "error(s), which this commit does not add to (fix them separately).",
            file=out,
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m agent_workflows.typecheck_gate",
        description=(
            "Attributable mypy checks. 'staged' refuses a commit whose staged tree adds mypy errors "
            "relative to HEAD (errors HEAD already has are reported, not blamed). 'tree' type-checks "
            "one committed tree-ish."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "staged", help="check the staged tree against HEAD (pre-commit hook)"
    )
    p_tree = sub.add_parser("tree", help="type-check one committed tree-ish")
    p_tree.add_argument("treeish", nargs="?", default="HEAD")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    if args.cmd == "staged":
        return staged_main(repo)
    run = check_tree(repo, args.treeish)
    if run.failure:
        print(f"typecheck: {run.failure}")
        return 1
    for err in run.errors:
        print(err)
    print("typecheck: clean" if run.ok else f"typecheck: {len(run.errors)} error(s)")
    return 0 if run.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
