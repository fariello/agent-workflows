"""Measurement tooling for test tiers (IPD hguae9).

Runs core (bare pytest) and thorough (tests/ -m '') under coverage run
with branch coverage and prints a per-module table (statements, core %, thorough %).

Usage:
  python3 -m tests.tools.core_measure [--out DIR] [--tier {both,core,thorough}] [--baseline-json FILE]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_coverage_tier(
    pytest_args: list[str],
    out_dir: Path,
    tier_name: str,
) -> dict[str, Any]:
    tier_tmp = out_dir / tier_name
    tier_tmp.mkdir(parents=True, exist_ok=True)
    cov_file = tier_tmp / ".coverage"
    rc_file = tier_tmp / "coveragerc"

    rc_file.write_text(
        f"[run]\n"
        f"data_file = {cov_file}\n"
        f"source = agent_workflows\n"
        f"branch = true\n"
        f"parallel = true\n"
        f"patch = subprocess\n"
        f"concurrency = multiprocessing\n",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["COVERAGE_FILE"] = str(cov_file)
    env["COVERAGE_PROCESS_START"] = str(rc_file)

    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--rcfile={rc_file}",
        "-m",
        "pytest",
        *pytest_args,
    ]
    sys.stderr.write(f"[{tier_name}] Running: {' '.join(cmd)}\n")
    sys.stderr.flush()
    res = subprocess.run(cmd, cwd=_REPO_ROOT, env=env, check=False)
    if res.returncode != 0:
        sys.stderr.write(f"[{tier_name}] pytest exited with code {res.returncode}\n")

    combine_cmd = [sys.executable, "-m", "coverage", "combine", f"--rcfile={rc_file}"]
    subprocess.run(combine_cmd, cwd=tier_tmp, env=env, check=False, capture_output=True)

    json_path = tier_tmp / f"{tier_name}_coverage.json"
    json_cmd = [
        sys.executable,
        "-m",
        "coverage",
        "json",
        f"--rcfile={rc_file}",
        "-o",
        str(json_path),
    ]
    subprocess.run(json_cmd, cwd=tier_tmp, env=env, check=True, capture_output=True)

    with open(json_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def format_table(
    core_data: dict[str, Any] | None,
    thorough_data: dict[str, Any] | None,
) -> str:
    # Key modules by repo-relative path e.g. agent_workflows/foo.py or foo.py
    modules: dict[str, dict[str, Any]] = {}

    def ingest(data: dict[str, Any], tier: str) -> None:
        for full_path, finfo in data.get("files", {}).items():
            try:
                rel = str(Path(full_path).relative_to(_REPO_ROOT))
            except ValueError:
                rel = os.path.basename(full_path)
            if not rel.startswith("agent_workflows/"):
                mod_name = os.path.basename(rel)
            else:
                mod_name = rel[len("agent_workflows/") :]
            if mod_name not in modules:
                modules[mod_name] = {
                    "rel_path": rel,
                    "statements": finfo["summary"]["num_statements"],
                    "core_pct": None,
                    "thorough_pct": None,
                    "core_covered": 0,
                    "thorough_covered": 0,
                }
            cov_pct = finfo["summary"]["percent_covered"]
            modules[mod_name][f"{tier}_pct"] = cov_pct
            modules[mod_name][f"{tier}_covered"] = finfo["summary"]["covered_lines"]

    if core_data:
        ingest(core_data, "core")
    if thorough_data:
        ingest(thorough_data, "thorough")

    lines: list[str] = []
    header = f"{'Module':<40} {'Statements':>10} {'Core %':>10} {'Thorough %':>12}"
    lines.append(header)
    lines.append("-" * len(header))

    zero_core_count = 0
    zero_core_full_covered = 0

    sorted_mods = sorted(modules.keys())
    for mod in sorted_mods:
        info = modules[mod]
        stmts = info["statements"]
        cpct_str = f"{info['core_pct']:.1f}%" if info["core_pct"] is not None else "N/A"
        tpct_str = (
            f"{info['thorough_pct']:.1f}%"
            if info["thorough_pct"] is not None
            else "N/A"
        )

        cpct = info["core_pct"] or 0.0
        tpct = info["thorough_pct"] or 0.0
        if cpct == 0.0:
            zero_core_count += 1
            if tpct > 0.0:
                zero_core_full_covered += 1

        lines.append(f"{mod:<40} {stmts:>10} {cpct_str:>10} {tpct_str:>12}")

    lines.append("-" * len(header))

    # Totals
    if core_data:
        ctot = core_data["totals"]
        lines.append(
            f"Core totals: {ctot['covered_lines']}/{ctot['num_statements']} lines "
            f"({ctot['percent_covered']:.1f}%), {ctot.get('covered_branches', 0)}/{ctot.get('num_branches', 0)} branches "
            f"({ctot.get('percent_branches_covered', 0):.1f}%)"
        )
    if thorough_data:
        ttot = thorough_data["totals"]
        lines.append(
            f"Thorough totals: {ttot['covered_lines']}/{ttot['num_statements']} lines "
            f"({ttot['percent_covered']:.1f}%), {ttot.get('covered_branches', 0)}/{ttot.get('num_branches', 0)} branches "
            f"({ttot.get('percent_branches_covered', 0):.1f}%)"
        )
    lines.append(
        f"Zero core coverage modules: {zero_core_count}/{len(modules)} "
        f"({zero_core_full_covered} covered by thorough)"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure test tier coverage per module."
    )
    parser.add_argument("--out", default=None, help="Directory to save coverage data.")
    parser.add_argument(
        "--tier",
        choices=["both", "core", "thorough"],
        default="both",
        help="Which tier to run.",
    )
    parser.add_argument(
        "--baseline-json",
        default=None,
        help="Path to pre-existing thorough coverage JSON to avoid re-running thorough tier.",
    )
    args = parser.parse_args(argv)

    temp_dir: str | None = None
    if args.out:
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        temp_dir = tempfile.mkdtemp(prefix="aw_cov_")
        out_dir = Path(temp_dir)

    try:
        core_data: dict[str, Any] | None = None
        thorough_data: dict[str, Any] | None = None

        if args.baseline_json:
            with open(args.baseline_json, encoding="utf-8") as f:
                thorough_data = json.load(f)

        if args.tier in ("both", "core"):
            core_data = _run_coverage_tier([], out_dir, "core")

        if args.tier in ("both", "thorough") and not thorough_data:
            thorough_data = _run_coverage_tier(
                ["tests/", "-m", ""], out_dir, "thorough"
            )

        table = format_table(core_data, thorough_data)
        print(table)

        summary_file = out_dir / "tier_coverage_summary.txt"
        summary_file.write_text(table + "\n", encoding="utf-8")
        return 0
    finally:
        if temp_dir and os.path.exists(temp_dir) and not args.out:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
