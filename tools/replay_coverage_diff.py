#!/usr/bin/env python3
"""Coverage differential tool for deleted test audit.

Computes a baseline of production code covered by surviving tests (with test-function
dynamic contexts and subprocess tracing), and diffs replayed deleted test coverage
against that baseline to isolate exclusive and shared line reach.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence

# Verify coverage is installed before anything else
try:
    import coverage  # type: ignore
except (ImportError, Exception):
    sys.stderr.write("coverage is not installed; pip install coverage\n")
    # Immediate refusal exit 2 if invoked as script
    if __name__ == "__main__":
        sys.exit(2)

# Ensure parent directory is importable so tools.deleted_test_replay is found
_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

try:
    from tools import deleted_test_replay  # type: ignore
except ImportError:
    import deleted_test_replay  # type: ignore


def _make_rc_content(cov_file: str) -> str:
    return (
        "[run]\n"
        f"data_file = {cov_file}\n"
        "source = agent_workflows\n"
        "dynamic_context = test_function\n"
        "parallel = true\n"
        "patch = subprocess\n"
    )


@dataclass
class FunctionSpan:
    qualname: str
    body_start: int
    end: int
    depth: int


def _find_repo_root() -> Path:
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if res.returncode == 0 and res.stdout.strip():
        return Path(res.stdout.strip()).resolve()
    return Path.cwd().resolve()


def _get_head_sha(repo_root: Path | str) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    return res.stdout.strip() if res.returncode == 0 else ""


def extract_functions(source: str, filename: str) -> list[FunctionSpan]:
    """Parse python source and extract functions with their body spans."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []

    functions: list[FunctionSpan] = []

    def walk(node: ast.AST, scope: list[str], depth: int) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                walk(child, scope + [child.name], depth + 1)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = ".".join(scope + [child.name])
                if child.body:
                    body_start = child.body[0].lineno
                    end = getattr(child, "end_lineno", child.lineno)
                    functions.append(FunctionSpan(qualname, body_start, end, depth))
                walk(child, scope + [child.name], depth + 1)

    walk(tree, [], 0)
    return functions


def find_owning_function(
    functions: list[FunctionSpan], lineno: int
) -> FunctionSpan | None:
    """Find the innermost function whose body contains the given line number."""
    candidates = [fn for fn in functions if fn.body_start <= lineno <= fn.end]
    if not candidates:
        return None
    return max(candidates, key=lambda fn: fn.depth)


def _is_serial_args(args: Sequence[str]) -> bool:
    for i, a in enumerate(args):
        if a == "-p" and i + 1 < len(args) and args[i + 1] == "no:xdist":
            return True
        if a in ("-pno:xdist", "-p=no:xdist"):
            return True
    return False


def _build_pytest_cmd(
    rc_path: str, pytest_args: Sequence[str], force_serial: bool = False
) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--rcfile={rc_path}",
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-q",
        "-p",
        "no:randomly",
        "-p",
        "no:cacheprovider",
    ]
    is_serial = force_serial or _is_serial_args(pytest_args)
    if not is_serial:
        cmd.extend(["-n", "auto"])
    cmd.extend(["-m", "not slow and not livecorpus"])

    cleaned_args: list[str] = []
    i = 0
    while i < len(pytest_args):
        a = pytest_args[i]
        if force_serial and a == "-n" and i + 1 < len(pytest_args):
            i += 2
            continue
        if force_serial and a.startswith("-n"):
            i += 1
            continue
        cleaned_args.append(a)
        i += 1

    cmd.extend(cleaned_args)
    if force_serial and not _is_serial_args(cleaned_args):
        cmd.extend(["-p", "no:xdist"])
    return cmd


def _has_non_empty_contexts(cov_data: coverage.CoverageData) -> bool:
    for f in cov_data.measured_files():
        contexts_by_line = cov_data.contexts_by_lineno(f)
        for ctxs in contexts_by_line.values():
            if any(bool(c) for c in ctxs):
                return True
    return False


def _collect_function_coverage(
    cov_data: coverage.CoverageData,
    run_root: Path | str,
    source_root: Path | str,
) -> dict[str, dict[str, Any]]:
    """Map measured coverage data to functions keyed by agent_workflows/<m>.py::<qualname>."""
    run_root_path = Path(run_root).resolve()
    source_root_path = Path(source_root).resolve()

    func_data: dict[str, dict[str, Any]] = {}
    cached_functions: dict[str, list[FunctionSpan]] = {}

    for measured_f in cov_data.measured_files():
        try:
            rel_f = os.path.relpath(measured_f, run_root_path)
        except ValueError:
            continue

        if rel_f.startswith("..") or os.path.isabs(rel_f):
            continue

        norm_rel = rel_f.replace("\\", "/")
        if not norm_rel.startswith("agent_workflows/") or not norm_rel.endswith(".py"):
            continue

        source_file = source_root_path / norm_rel
        if not source_file.is_file():
            continue

        if norm_rel not in cached_functions:
            try:
                content = source_file.read_text(encoding="utf-8")
                cached_functions[norm_rel] = extract_functions(content, norm_rel)
            except Exception:
                cached_functions[norm_rel] = []

        spans = cached_functions[norm_rel]
        if not spans:
            continue

        lines_covered = cov_data.lines(measured_f) or []
        contexts_by_line = cov_data.contexts_by_lineno(measured_f) or {}

        for lineno in lines_covered:
            owner = find_owning_function(spans, lineno)
            if owner is None:
                continue

            fkey = f"{norm_rel}::{owner.qualname}"
            if fkey not in func_data:
                func_data[fkey] = {"lines": set(), "contexts": set()}

            func_data[fkey]["lines"].add(lineno)
            for ctx in contexts_by_line.get(lineno, []):
                if ctx:
                    func_data[fkey]["contexts"].add(ctx)

    result: dict[str, dict[str, Any]] = {}
    for fkey, d in func_data.items():
        sorted_lines = sorted(d["lines"])
        sorted_contexts = sorted(d["contexts"])
        result[fkey] = {
            "lines": sorted_lines,
            "contexts": sorted_contexts,
            "subprocess_only": len(sorted_contexts) == 0,
        }
    return result


def run_baseline(
    repo_root: Path,
    out_dir: str | None,
    pytest_args: Sequence[str],
) -> tuple[int, str]:
    """Run baseline coverage and write baseline.json."""
    start_time = time.monotonic()
    head_sha = _get_head_sha(repo_root)

    is_user_serial = _is_serial_args(pytest_args)
    force_serial = is_user_serial

    tmp_data_dir = tempfile.mkdtemp(prefix="cov_baseline_data_")
    cov_file = os.path.join(tmp_data_dir, ".coverage")
    rc_path = os.path.join(tmp_data_dir, "coveragerc")
    with open(rc_path, "w", encoding="utf-8") as f:
        f.write(_make_rc_content(cov_file))

    try:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["COVERAGE_FILE"] = cov_file
        env["COVERAGE_PROCESS_START"] = rc_path
        env["PYTHONPATH"] = (
            f"{repo_root}{os.pathsep}{env['PYTHONPATH']}"
            if "PYTHONPATH" in env and env["PYTHONPATH"]
            else str(repo_root)
        )

        cmd = _build_pytest_cmd(rc_path, pytest_args, force_serial=force_serial)
        subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
        )

        combine_cmd = [
            sys.executable,
            "-m",
            "coverage",
            "combine",
            f"--rcfile={rc_path}",
            "-q",
            tmp_data_dir,
        ]
        subprocess.run(
            combine_cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
        )

        cov_data = coverage.CoverageData(basename=cov_file)
        if os.path.exists(cov_file):
            cov_data.read()

        xdist_used = not force_serial
        # Xdist check: if xdist was used but yielded no non-empty contexts, retry serially
        if xdist_used and not _has_non_empty_contexts(cov_data):
            shutil.rmtree(tmp_data_dir, ignore_errors=True)
            tmp_data_dir = tempfile.mkdtemp(prefix="cov_baseline_data_")
            cov_file = os.path.join(tmp_data_dir, ".coverage")
            rc_path = os.path.join(tmp_data_dir, "coveragerc")
            with open(rc_path, "w", encoding="utf-8") as f:
                f.write(_make_rc_content(cov_file))
            env["COVERAGE_FILE"] = cov_file
            env["COVERAGE_PROCESS_START"] = rc_path
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            retry_cmd = _build_pytest_cmd(rc_path, pytest_args, force_serial=True)
            subprocess.run(
                retry_cmd,
                cwd=str(repo_root),
                env=env,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coverage",
                    "combine",
                    f"--rcfile={rc_path}",
                    "-q",
                    tmp_data_dir,
                ],
                cwd=str(repo_root),
                env=env,
                capture_output=True,
                text=True,
            )
            cov_data = coverage.CoverageData(basename=cov_file)
            if os.path.exists(cov_file):
                cov_data.read()
            xdist_used = False

        func_coverage = _collect_function_coverage(
            cov_data, run_root=repo_root, source_root=repo_root
        )

        wall_s = round(time.monotonic() - start_time, 2)
        selection = ["-m", "not slow and not livecorpus"] + list(pytest_args)

        payload = {
            "functions": func_coverage,
            "head": head_sha,
            "selection": selection,
            "wall_s": wall_s,
            "xdist": xdist_used,
        }

        printed_dir = False
        if out_dir is not None:
            target_out_dir = out_dir
            os.makedirs(target_out_dir, exist_ok=True)
        else:
            target_out_dir = tempfile.mkdtemp(prefix="cov_baseline_out_")
            printed_dir = True

        baseline_file = os.path.join(target_out_dir, "baseline.json")
        with open(baseline_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

        if printed_dir:
            print(target_out_dir)

        subp_count = sum(1 for v in func_coverage.values() if v["subprocess_only"])
        summary_tail = (
            f"Baseline recorded to {baseline_file}\n"
            f"head: {head_sha}\n"
            f"xdist: {xdist_used}\n"
            f"functions: {len(func_coverage)}\n"
            f"subprocess_only: {subp_count}\n"
            f"wall_s: {wall_s:.2f}"
        )
        print(summary_tail)
        return 0, baseline_file
    finally:
        if out_dir is None or os.path.abspath(tmp_data_dir) != os.path.abspath(out_dir):
            shutil.rmtree(tmp_data_dir, ignore_errors=True)


def run_diff(
    repo_root: Path,
    commit: str,
    paths: list[str],
    baseline_dir: str,
    output_format: str,
    timeout: int,
) -> int:
    """Run coverage replay diff against baseline.json."""
    if (
        os.path.isfile(baseline_dir)
        and os.path.basename(baseline_dir) == "baseline.json"
    ):
        baseline_file = baseline_dir
    else:
        baseline_file = os.path.join(baseline_dir, "baseline.json")

    if not os.path.isfile(baseline_file):
        sys.stderr.write(f"error: baseline dir '{baseline_dir}' lacks baseline.json\n")
        return 2

    try:
        with open(baseline_file, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
    except Exception as e:
        sys.stderr.write(f"error: failed to read baseline.json: {e}\n")
        return 2

    current_head = _get_head_sha(repo_root)
    baseline_head = baseline_data.get("head", "")
    if baseline_head != current_head:
        sys.stderr.write(
            f"error: baseline head '{baseline_head}' differs from current HEAD '{current_head}'\n"
        )
        return 2

    baseline_functions: dict[str, dict[str, Any]] = baseline_data.get("functions", {})
    records: list[dict[str, Any]] = []

    for rel_path in paths:
        clean_rel_path = str(Path(rel_path))
        per_path_tmp = tempfile.mkdtemp(prefix="cov_diff_")
        cov_file = os.path.join(per_path_tmp, ".coverage")
        rc_path = os.path.join(per_path_tmp, "coveragerc")
        with open(rc_path, "w", encoding="utf-8") as f:
            f.write(_make_rc_content(cov_file))

        diff_env = dict(os.environ)
        diff_env["COVERAGE_FILE"] = cov_file
        diff_env["COVERAGE_PROCESS_START"] = rc_path

        try:
            replay_res = deleted_test_replay.replay_file(
                repo_root=repo_root,
                commit=commit,
                rel_path=clean_rel_path,
                timeout_s=timeout,
                python_prefix=[
                    sys.executable,
                    "-m",
                    "coverage",
                    "run",
                    f"--rcfile={rc_path}",
                ],
                extra_env={
                    "COVERAGE_FILE": cov_file,
                    "COVERAGE_PROCESS_START": rc_path,
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coverage",
                    "combine",
                    f"--rcfile={rc_path}",
                    "-q",
                    per_path_tmp,
                ],
                cwd=str(repo_root),
                env=diff_env,
                capture_output=True,
                text=True,
            )

            replay_cov = coverage.CoverageData(basename=cov_file)
            if os.path.exists(cov_file):
                replay_cov.read()

            replay_functions = _collect_function_coverage(
                replay_cov,
                run_root=replay_res.replay_root,
                source_root=repo_root,
            )

            diff_functions: dict[str, dict[str, Any]] = {}
            for fkey, rdata in sorted(replay_functions.items()):
                replay_lines = set(rdata["lines"])
                if fkey in baseline_functions:
                    bdata = baseline_functions[fkey]
                    b_lines = set(bdata.get("lines", []))
                    excl_lines = sorted(replay_lines - b_lines)
                    shared_lines = sorted(replay_lines & b_lines)
                    b_contexts = len(bdata.get("contexts", []))
                    b_subp = bool(bdata.get("subprocess_only", False))
                else:
                    excl_lines = sorted(replay_lines)
                    shared_lines = []
                    b_contexts = 0
                    b_subp = False

                diff_functions[fkey] = {
                    "baseline_contexts": b_contexts,
                    "baseline_subprocess_only": b_subp,
                    "exclusive_lines": excl_lines,
                    "shared_lines": shared_lines,
                }

            record = {
                "commit": commit,
                "functions": diff_functions,
                "path": clean_rel_path,
                "tests_count": len(replay_res.tests),
                "verdict": replay_res.verdict,
            }
            records.append(record)
        finally:
            shutil.rmtree(per_path_tmp, ignore_errors=True)

    if output_format == "json":
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        for r in records:
            count_str = f"{r['tests_count']} tests"
            print(f"{r['path']}: {r['verdict']} ({count_str})")
            if not r["functions"]:
                print("  no production functions reached")
            else:
                for fkey, finfo in sorted(r["functions"].items()):
                    excl_len = len(finfo["exclusive_lines"])
                    shared_len = len(finfo["shared_lines"])
                    b_ctx = finfo["baseline_contexts"]
                    subp_str = (
                        ", subprocess_only" if finfo["baseline_subprocess_only"] else ""
                    )
                    print(
                        f"  {fkey}: {excl_len} exclusive, {shared_len} shared "
                        f"(baseline: {b_ctx} contexts{subp_str})"
                    )

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        import coverage  # noqa: F401
    except (ImportError, Exception):
        sys.stderr.write("coverage is not installed; pip install coverage\n")
        return 2

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Coverage differential tool for deleted test replay audit.",
        prog="replay_coverage_diff.py",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: baseline
    parser_base = subparsers.add_parser(
        "baseline",
        description="Run baseline coverage over surviving tests and save baseline.json.",
    )
    parser_base.add_argument(
        "--out",
        type=str,
        default=None,
        help="Directory to save baseline.json (defaults to a fresh temp directory)",
    )
    parser_base.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Additional pytest arguments after -- (e.g. -p no:xdist, test paths)",
    )

    # Subcommand: diff
    parser_diff = subparsers.add_parser(
        "diff",
        description="Replay deleted tests with coverage and diff against baseline.json.",
    )
    parser_diff.add_argument(
        "commit",
        help="Commit hash that deleted the test files",
    )
    parser_diff.add_argument(
        "paths",
        nargs="*",
        help="Test file path(s) to replay",
    )
    parser_diff.add_argument(
        "--from-json",
        help="Path to JSON inventory of deleted tests (e.g. from lost_guard_census.py)",
    )
    parser_diff.add_argument(
        "--baseline",
        required=True,
        help="Directory containing baseline.json",
    )
    parser_diff.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (text or json, default: text)",
    )
    parser_diff.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-file timeout in seconds (default: 300)",
    )

    args = parser.parse_args(argv)
    repo_root = _find_repo_root()

    if args.subcommand == "baseline":
        pytest_args = list(args.pytest_args)
        if pytest_args and pytest_args[0] == "--":
            pytest_args.pop(0)
        code, _ = run_baseline(
            repo_root=repo_root,
            out_dir=args.out,
            pytest_args=pytest_args,
        )
        return code

    elif args.subcommand == "diff":
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

        return run_diff(
            repo_root=repo_root,
            commit=args.commit,
            paths=paths,
            baseline_dir=args.baseline,
            output_format=args.format,
            timeout=args.timeout,
        )

    return 2


if __name__ == "__main__":
    sys.exit(main())
