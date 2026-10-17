"""Runner for per-test coverage measurement with subprocess attribution (IPD qqrgv3).

Executes the test suite under coverage run with ctrace, branch coverage,
patch=subprocess, and covctx_plugin context propagation, then combines
and dumps metadata and collected node IDs.

Usage:
  python3 -m tests.tools.percov_run --out DIR [-- pytest-args]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import coverage

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _available_workers() -> int:
    """Determine xdist worker count matching conftest pytest_xdist_auto_num_workers."""
    cpus = (
        len(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else (os.cpu_count() or 2)
    )
    limit = min(6, max(1, cpus // 2))
    env_var = os.environ.get("PYTEST_XDIST_AUTO_NUM_WORKERS")
    if env_var:
        try:
            return min(limit, max(1, int(env_var)))
        except ValueError:
            pass
    return limit


def _extract_failing_nodeids(junit_path: Path, stdout_text: str) -> list[str]:
    """Extract list of failing test node IDs from stdout and junit.xml."""
    failing: list[str] = []
    for line in stdout_text.splitlines():
        if line.startswith("FAILED "):
            part = line[len("FAILED ") :].split()[0]
            if part and part not in failing:
                failing.append(part)

    if junit_path.is_file():
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(junit_path)
            for tc in tree.findall(".//testcase"):
                if tc.find("failure") is not None or tc.find("error") is not None:
                    file_attr = tc.attrib.get("file", "")
                    name = tc.attrib.get("name", "")
                    classname = tc.attrib.get("classname", "")
                    if file_attr and name:
                        cand = f"{file_attr}::{name}"
                    else:
                        cand = f"{classname}::{name}"
                    if cand not in failing:
                        failing.append(cand)
        except Exception:
            pass
    return sorted(failing)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run test suite under per-test coverage."
    )
    parser.add_argument(
        "--out", required=True, type=Path, help="Output directory for coverage data"
    )
    parser.add_argument(
        "pytest_args", nargs="*", default=[], help="Optional pytest arguments"
    )

    args, unknown = parser.parse_known_args(argv)
    pytest_args = list(args.pytest_args) + unknown

    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cov_file = out_dir / ".coverage"
    rc_file = out_dir / ".coveragerc"
    junit_file = out_dir / "junit.xml"
    meta_file = out_dir / "meta.json"
    collected_file = out_dir / "collected.txt"
    markers_file = out_dir / "markers.json"
    totals_file = out_dir / "cov_totals.json"

    source_dir = (_REPO_ROOT / "agent_workflows").resolve()

    rc_content = (
        "[run]\n"
        f"data_file = {cov_file}\n"
        f"source = {source_dir}\n"
        "branch = true\n"
        "parallel = true\n"
        "patch = subprocess\n"
    )
    rc_file.write_text(rc_content, encoding="utf-8")

    env = dict(os.environ)
    env["COVERAGE_CORE"] = "ctrace"
    env["COVERAGE_FILE"] = str(cov_file)
    env["COVERAGE_PROCESS_START"] = str(rc_file)
    env["PYTHONPATH"] = f"{_REPO_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"

    # Distinguish test paths/targets from flags in pytest_args
    targets: list[str] = []
    extra_flags: list[str] = []
    for arg in pytest_args:
        if arg.startswith("-"):
            extra_flags.append(arg)
        else:
            targets.append(arg)

    if not targets:
        targets = ["tests/"]

    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--rcfile={rc_file}",
        "-m",
        "pytest",
        *targets,
        "-m",
        "",
        "-o",
        "addopts=-q -n auto --dist=worksteal",
        "-p",
        "tests.tools.covctx_plugin",
        "-p",
        "no:cov",
        "--durations=0",
        f"--junitxml={junit_file}",
        *extra_flags,
    ]

    env["PYTHONUNBUFFERED"] = "1"
    worker_count = _available_workers()
    sys.stderr.write(
        f"[percov_run] Running {len(targets)} target(s) with {worker_count} workers...\n"
    )
    sys.stderr.write(f"[percov_run] Command: {' '.join(cmd)}\n")
    sys.stderr.flush()

    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=_REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    stdout_lines: list[str] = []
    if proc.stdout is not None:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            stdout_lines.append(line)
    retcode = proc.wait()
    wall_time = time.perf_counter() - t0
    stdout_text = "".join(stdout_lines)

    clean_env = dict(os.environ)
    clean_env.pop("COVERAGE_PROCESS_START", None)
    clean_env.pop("COVERAGE_FILE", None)
    clean_env.pop("COVERAGE_PROCESS_CONFIG", None)
    clean_env["PYTHONPATH"] = env["PYTHONPATH"]

    # Combine coverage data
    combine_cmd = [sys.executable, "-m", "coverage", "combine", f"--rcfile={rc_file}"]
    sys.stderr.write("[percov_run] Combining coverage files...\n")
    subprocess.run(
        combine_cmd, cwd=out_dir, env=clean_env, check=False, capture_output=True
    )

    # Generate coverage json totals
    json_cmd = [
        sys.executable,
        "-m",
        "coverage",
        "json",
        f"--rcfile={rc_file}",
        "-o",
        str(totals_file),
    ]
    subprocess.run(
        json_cmd, cwd=out_dir, env=clean_env, check=False, capture_output=True
    )

    # Collect-only node ids and markers
    collect_env = dict(clean_env)
    collect_env["AW_MARKERS_DUMP"] = str(markers_file)
    collect_cmd = [
        sys.executable,
        "-m",
        "pytest",
        *targets,
        "-m",
        "",
        "-o",
        "addopts=",
        "--collect-only",
        "-q",
        "-p",
        "no:randomly",
        "-p",
        "tests.tools.markers_dump",
        *extra_flags,
    ]
    collect_res = subprocess.run(
        collect_cmd, cwd=_REPO_ROOT, env=collect_env, capture_output=True, text=True
    )
    collected_file.write_text(collect_res.stdout, encoding="utf-8")

    # Git HEAD
    try:
        git_head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT, text=True
        ).strip()
    except Exception:
        git_head = "unknown"

    failing_nodeids = _extract_failing_nodeids(junit_file, stdout_text)

    meta: dict[str, Any] = {
        "git_head": git_head,
        "python_version": sys.version,
        "coverage_version": coverage.__version__,
        "core": "ctrace",
        "worker_count": worker_count,
        "wall_time": round(wall_time, 2),
        "pytest_exit": retcode,
        "failing_nodeids": failing_nodeids,
    }
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    sys.stderr.write(
        f"[percov_run] Finished in {wall_time:.2f}s, pytest exit: {retcode}, "
        f"data: {cov_file.stat().st_size if cov_file.exists() else 0} bytes\n"
    )
    return retcode


if __name__ == "__main__":
    sys.exit(main())
