#!/usr/bin/env python3
"""Worktree-isolated deleted-test replay harness.

Replays trim-deleted test files against committed HEAD inside a throwaway
detached git worktree, reporting machine-readable verdicts and per-test outcomes.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence
import xml.etree.ElementTree as ET

ALL_VERDICTS: tuple[str, ...] = (
    "pass",
    "fail",
    "error-import",
    "error-collect",
    "no-tests",
    "timeout",
    "error",
)


@dataclass
class ReplayResult:
    commit: str
    path: str
    head: str
    verdict: str
    exit_code: int | None
    tests: list[tuple[str, str]]
    counts: dict[str, int]
    error_line: str | None
    overwrote_head_path: bool
    replay_root: str
    wall_s: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


def _extract_error_line(error_text: str) -> str | None:
    """Extract the first line of the error text that names the exception."""
    lines = error_text.splitlines()
    for line in lines:
        trimmed = line.strip()
        if trimmed.startswith("E "):
            candidate = trimmed[2:].strip()
            if any(err in candidate for err in ("Error", "Exception")):
                return candidate
    for line in lines:
        trimmed = line.strip()
        if trimmed.startswith("ImportError while importing test module"):
            continue
        if any(err in trimmed for err in ("Error", "Exception")) and ":" in trimmed:
            return trimmed.removeprefix("E ").strip()
    for line in lines:
        trimmed = line.strip()
        if trimmed.startswith("ImportError while importing test module"):
            continue
        if any(err in trimmed for err in ("Error", "Exception")):
            return trimmed.removeprefix("E ").strip()
    return None


def _parse_junit_xml(
    xml_path: str | Path,
) -> tuple[bool, list[tuple[str, str]], dict[str, int], list[str]]:
    """Parse junit XML into (parsed_ok, tests, counts, error_texts)."""
    empty_counts = {"error": 0, "failed": 0, "passed": 0, "skipped": 0}
    if not os.path.exists(xml_path):
        return False, [], empty_counts, []

    try:
        tree = ET.parse(xml_path)
    except Exception:
        return False, [], empty_counts, []

    tests: list[tuple[str, str]] = []
    error_texts: list[str] = []

    for tc in tree.iter("testcase"):
        classname = tc.attrib.get("classname", "").strip()
        name = tc.attrib.get("name", "").strip()
        nodeid = f"{classname}::{name}" if classname else name

        err_elem = tc.find("error")
        fail_elem = tc.find("failure")
        skip_elem = tc.find("skipped")

        if err_elem is not None:
            outcome = "error"
            if err_elem.text:
                error_texts.append(err_elem.text)
        elif fail_elem is not None:
            outcome = "failed"
        elif skip_elem is not None:
            outcome = "skipped"
        else:
            outcome = "passed"

        tests.append((nodeid, outcome))

    for err in tree.findall(".//error"):
        if err.text and err.text not in error_texts:
            error_texts.append(err.text)

    tests.sort(key=lambda x: x[0])
    counts = {
        "error": sum(1 for _, o in tests if o == "error"),
        "failed": sum(1 for _, o in tests if o == "failed"),
        "passed": sum(1 for _, o in tests if o == "passed"),
        "skipped": sum(1 for _, o in tests if o == "skipped"),
    }
    return True, tests, counts, error_texts


def replay_file(
    repo_root: str | Path,
    commit: str,
    rel_path: str,
    timeout_s: int = 300,
    python_prefix: Sequence[str] | None = None,
    extra_env: dict[str, str] | None = None,
) -> ReplayResult:
    """Execute a single trim-deleted test file in a detached worktree of HEAD."""
    start_time = time.monotonic()
    repo_root_path = Path(repo_root).resolve()
    repo_root_str = str(repo_root_path)
    clean_rel_path = str(Path(rel_path))

    head_res = subprocess.run(
        ["git", "-C", repo_root_str, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    head_sha = head_res.stdout.strip() if head_res.returncode == 0 else ""

    tmp_dir = tempfile.mkdtemp(prefix="deleted_test_replay_")
    wt_dir = os.path.join(tmp_dir, "wt")
    overwrote_head_path = False

    try:
        add_res = subprocess.run(
            ["git", "-C", repo_root_str, "worktree", "add", "--detach", wt_dir, "HEAD"],
            capture_output=True,
            text=True,
        )
        if add_res.returncode != 0:
            wall_s = round(time.monotonic() - start_time, 2)
            return ReplayResult(
                commit=commit,
                path=clean_rel_path,
                head=head_sha,
                verdict="error",
                exit_code=None,
                tests=[],
                counts={"error": 0, "failed": 0, "passed": 0, "skipped": 0},
                error_line=f"git worktree add failed: {add_res.stderr.strip()}",
                overwrote_head_path=False,
                replay_root=wt_dir,
                wall_s=wall_s,
            )

        dest = os.path.join(wt_dir, clean_rel_path)
        overwrote_head_path = os.path.exists(dest)

        show_res = subprocess.run(
            ["git", "-C", repo_root_str, "show", f"{commit}^:{clean_rel_path}"],
            capture_output=True,
        )
        if show_res.returncode != 0:
            wall_s = round(time.monotonic() - start_time, 2)
            return ReplayResult(
                commit=commit,
                path=clean_rel_path,
                head=head_sha,
                verdict="error",
                exit_code=None,
                tests=[],
                counts={"error": 0, "failed": 0, "passed": 0, "skipped": 0},
                error_line=f"git show {commit}^:{clean_rel_path} failed",
                overwrote_head_path=overwrote_head_path,
                replay_root=wt_dir,
                wall_s=wall_s,
            )

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(show_res.stdout)

        env = dict(os.environ)
        env["PYTHONPATH"] = wt_dir + (
            os.pathsep + env["PYTHONPATH"]
            if "PYTHONPATH" in env and env["PYTHONPATH"]
            else ""
        )
        if extra_env:
            env.update(extra_env)

        junit_xml_path = os.path.join(tmp_dir, "junit.xml")
        prefix = list(python_prefix) if python_prefix is not None else [sys.executable]
        cmd = prefix + [
            "-m",
            "pytest",
            "-o",
            "addopts=",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:randomly",
            "--junitxml",
            junit_xml_path,
            clean_rel_path,
        ]

        proc = subprocess.Popen(
            cmd,
            cwd=wt_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )

        timed_out = False
        try:
            proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.communicate()

        wall_s = round(time.monotonic() - start_time, 2)
        exit_code = proc.returncode

        if timed_out:
            return ReplayResult(
                commit=commit,
                path=clean_rel_path,
                head=head_sha,
                verdict="timeout",
                exit_code=exit_code,
                tests=[],
                counts={"error": 0, "failed": 0, "passed": 0, "skipped": 0},
                error_line=None,
                overwrote_head_path=overwrote_head_path,
                replay_root=wt_dir,
                wall_s=wall_s,
            )

        parsed_ok, tests, counts, error_texts = _parse_junit_xml(junit_xml_path)

        if not parsed_ok:
            return ReplayResult(
                commit=commit,
                path=clean_rel_path,
                head=head_sha,
                verdict="error",
                exit_code=exit_code,
                tests=[],
                counts={"error": 0, "failed": 0, "passed": 0, "skipped": 0},
                error_line=None,
                overwrote_head_path=overwrote_head_path,
                replay_root=wt_dir,
                wall_s=wall_s,
            )

        error_line: str | None = None
        if exit_code == 0:
            verdict = "pass"
        elif exit_code == 1:
            verdict = "fail"
        elif exit_code == 2:
            if not error_texts:
                verdict = "error"
            else:
                has_import_err = any(
                    ("ModuleNotFoundError" in text or "ImportError" in text)
                    for text in error_texts
                )
                if has_import_err:
                    verdict = "error-import"
                else:
                    verdict = "error-collect"
                for text in error_texts:
                    extracted = _extract_error_line(text)
                    if extracted:
                        error_line = extracted
                        break
        elif exit_code == 5:
            verdict = "no-tests"
        else:
            verdict = "error"

        return ReplayResult(
            commit=commit,
            path=clean_rel_path,
            head=head_sha,
            verdict=verdict,
            exit_code=exit_code,
            tests=tests,
            counts=counts,
            error_line=error_line,
            overwrote_head_path=overwrote_head_path,
            replay_root=wt_dir,
            wall_s=wall_s,
        )

    finally:
        if os.path.exists(wt_dir):
            subprocess.run(
                ["git", "-C", repo_root_str, "worktree", "remove", "--force", wt_dir],
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", repo_root_str, "worktree", "prune"],
                capture_output=True,
            )
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _find_repo_root() -> Path:
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if res.returncode == 0 and res.stdout.strip():
        return Path(res.stdout.strip()).resolve()
    return Path.cwd().resolve()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay trim-deleted test files in detached worktrees of HEAD."
    )
    parser.add_argument("commit", help="Commit hash that deleted the test files")
    parser.add_argument("paths", nargs="*", help="Test file path(s) to replay")
    parser.add_argument(
        "--from-json",
        help="Path to JSON inventory of deleted tests (e.g. from lost_guard_census.py)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (text or json, default: text)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-file timeout in seconds (default: 300)",
    )

    args = parser.parse_args(argv)

    paths: list[str] = list(args.paths)
    if args.from_json:
        try:
            with open(args.from_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "path" in item:
                        paths.append(item["path"])
                    elif isinstance(item, str):
                        paths.append(item)
        except Exception as e:
            parser.error(f"failed to read --from-json file: {e}")

    if not paths:
        parser.error(
            "at least one test path must be specified via positional arguments or --from-json"
        )

    repo_root = _find_repo_root()
    results: list[ReplayResult] = []

    for p in paths:
        res = replay_file(
            repo_root=repo_root,
            commit=args.commit,
            rel_path=p,
            timeout_s=args.timeout,
        )
        results.append(res)

    if args.format == "json":
        json_output = [r.to_dict() for r in results]
        print(json.dumps(json_output, indent=2, sort_keys=True))
    else:
        for r in results:
            count_parts = [f"{v} {k}" for k, v in r.counts.items() if v > 0]
            counts_str = ", ".join(count_parts) if count_parts else "0 tests"
            print(f"{r.path}: {r.verdict} ({counts_str})")

        totals = {v: 0 for v in ALL_VERDICTS}
        for r in results:
            totals[r.verdict] = totals.get(r.verdict, 0) + 1
        totals_str = ", ".join(f"{totals[v]} {v}" for v in ALL_VERDICTS)
        print(f"Totals: {totals_str}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
