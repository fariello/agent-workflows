"""Analyzer for per-test coverage data (IPD qqrgv3).

Reads combined coverage data (.coverage), builds per-context and per-module
line and arc sets in one pass, computes unique lines/arcs, identical/subset
coverage groups, and no_coverage flags, and writes DIR/percov.json.
Supports --compare OTHER_DIR to detect lost lines and arcs.

Usage:
  python3 -m tests.tools.percov_analyze DIR [--compare OTHER_DIR]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import coverage

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _rel_path(full_path: str) -> str:
    """Normalize file path to repo-relative posix path."""
    try:
        return Path(full_path).resolve().relative_to(_REPO_ROOT).as_posix()
    except (ValueError, OSError, RuntimeError):
        return full_path.replace("\\", "/")


def extract_coverage_sets(
    cov_path: Path,
) -> tuple[
    bool,
    dict[str, set[tuple[str, int]]],
    dict[str, set[tuple[str, int, int]]],
]:
    """Extract line and arc sets per context in one pass from .coverage.

    Returns:
      (has_arcs, ctx_lines, ctx_arcs)
    """
    ctx_lines: dict[str, set[tuple[str, int]]] = defaultdict(set)
    ctx_arcs: dict[str, set[tuple[str, int, int]]] = defaultdict(set)

    # Fast path: query underlying sqlite database directly without reading full CoverageData
    try:
        with sqlite3.connect(str(cov_path)) as conn:
            meta_row = conn.execute(
                "SELECT value FROM meta WHERE key = 'has_arcs'"
            ).fetchone()
            if meta_row and meta_row[0] in ("1", "True", "true", 1):
                has_arcs = True
            else:
                arc_row = conn.execute("SELECT 1 FROM arc LIMIT 1").fetchone()
                has_arcs = bool(arc_row)

            # Pre-cache file paths and contexts
            file_map = {
                row[0]: _rel_path(row[1])
                for row in conn.execute("SELECT id, path FROM file")
            }
            context_map = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT id, context FROM context WHERE context != ''"
                )
            }

            if has_arcs:
                cur = conn.execute("SELECT file_id, context_id, fromno, tono FROM arc")
                for file_id, context_id, fromno, tono in cur:
                    ctx = context_map.get(context_id)
                    if not ctx:
                        continue
                    rel = file_map.get(file_id, "")
                    ctx_arcs[ctx].add((rel, fromno, tono))
                    if fromno > 0:
                        ctx_lines[ctx].add((rel, fromno))
                    if tono > 0:
                        ctx_lines[ctx].add((rel, tono))
            else:
                from coverage.numbits import numbits_to_nums

                cur = conn.execute("SELECT file_id, context_id, numbits FROM line_bits")
                for file_id, context_id, numbits in cur:
                    ctx = context_map.get(context_id)
                    if not ctx:
                        continue
                    rel = file_map.get(file_id, "")
                    for lineno in numbits_to_nums(numbits):
                        ctx_lines[ctx].add((rel, lineno))
            return has_arcs, ctx_lines, ctx_arcs
    except (sqlite3.Error, OSError, KeyError):
        # Fallback to CoverageData API
        cov_data = coverage.CoverageData(str(cov_path))
        cov_data.read()
        has_arcs = cov_data.has_arcs()
        for f in cov_data.measured_files():
            rel = _rel_path(f)
            for ctx in cov_data.measured_contexts():
                if not ctx:
                    continue
                cov_data.set_query_context(ctx)
                if has_arcs:
                    arcs = cov_data.arcs(f)
                    if arcs:
                        for fromno, tono in arcs:
                            ctx_arcs[ctx].add((rel, fromno, tono))
                            if fromno > 0:
                                ctx_lines[ctx].add((rel, fromno))
                            if tono > 0:
                                ctx_lines[ctx].add((rel, tono))
                else:
                    lines = cov_data.lines(f)
                    if lines:
                        for lineno in lines:
                            ctx_lines[ctx].add((rel, lineno))
        return has_arcs, ctx_lines, ctx_arcs


def analyze_directory(dir_path: Path) -> dict[str, Any]:
    cov_file = dir_path / ".coverage"
    if not cov_file.is_file():
        raise FileNotFoundError(f"Coverage data file not found: {cov_file}")

    has_arcs, ctx_lines, ctx_arcs = extract_coverage_sets(cov_file)

    collected_file = dir_path / "collected.txt"
    collected_nodeids: list[str] = []
    if collected_file.is_file():
        for line in collected_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if (
                line
                and "::" in line
                and not line.endswith("collected")
                and "collected in" not in line
            ):
                collected_nodeids.append(line)

    if collected_nodeids:
        all_nodeids = sorted(set(collected_nodeids))
    else:
        all_nodeids = sorted(set(ctx_lines.keys()) | set(ctx_arcs.keys()))

    all_nodeids_set = set(all_nodeids)
    line_to_ctxs: dict[tuple[str, int], list[str]] = defaultdict(list)
    arc_to_ctxs: dict[tuple[str, int, int], list[str]] = defaultdict(list)

    for ctx, lines in ctx_lines.items():
        if ctx not in all_nodeids_set:
            continue
        for ln in lines:
            line_to_ctxs[ln].append(ctx)

    for ctx, arcs in ctx_arcs.items():
        if ctx not in all_nodeids_set:
            continue
        for a in arcs:
            arc_to_ctxs[a].append(ctx)

    ctx_unique_lines: dict[str, int] = defaultdict(int)
    ctx_unique_arcs: dict[str, int] = defaultdict(int)

    for ln, ctx_list in line_to_ctxs.items():
        if len(ctx_list) == 1:
            ctx_unique_lines[ctx_list[0]] += 1

    for a, ctx_list in arc_to_ctxs.items():
        if len(ctx_list) == 1:
            ctx_unique_arcs[ctx_list[0]] += 1

    def _mod_of(nodeid: str) -> str:
        return nodeid.split("::")[0]

    # Module-level unique lines and arcs
    mod_unique_lines: dict[str, int] = defaultdict(int)
    mod_unique_arcs: dict[str, int] = defaultdict(int)

    for ln, ctx_list in line_to_ctxs.items():
        covering_mods = {_mod_of(c) for c in ctx_list}
        if len(covering_mods) == 1:
            mod_unique_lines[next(iter(covering_mods))] += 1

    for a, ctx_list in arc_to_ctxs.items():
        covering_mods = {_mod_of(c) for c in ctx_list}
        if len(covering_mods) == 1:
            mod_unique_arcs[next(iter(covering_mods))] += 1

    # Identical and subset groupings
    # Hash each context's (lines, arcs) signature
    hash_to_ctxs: dict[int, list[str]] = defaultdict(list)
    ctx_signature: dict[
        str, tuple[frozenset[tuple[str, int]], frozenset[tuple[str, int, int]]]
    ] = {}

    for nodeid in all_nodeids:
        lines = frozenset(ctx_lines.get(nodeid, set()))
        arcs = frozenset(ctx_arcs.get(nodeid, set()))
        ctx_signature[nodeid] = (lines, arcs)
        if lines or arcs:
            sig_hash = hash((lines, arcs))
            hash_to_ctxs[sig_hash].append(nodeid)

    identical_groups: dict[str, list[str]] = defaultdict(list)
    for sig_hash, members in hash_to_ctxs.items():
        if len(members) > 1:
            for m in members:
                identical_groups[m] = [other for other in members if other != m]

    subset_groups: dict[str, list[str]] = defaultdict(list)
    for nodeid in all_nodeids:
        u_l = ctx_unique_lines[nodeid]
        u_a = ctx_unique_arcs[nodeid]
        lines, arcs = ctx_signature[nodeid]
        if not lines and not arcs:
            continue
        # If it has unique lines/arcs, no other test can strictly contain it
        if u_l > 0 or u_a > 0:
            continue

        # Find candidate supersets using the line with fewest covering tests
        candidate_supersets: list[str] | None = None
        if lines:
            min_l = min(lines, key=lambda ln: len(line_to_ctxs[ln]))
            candidate_supersets = line_to_ctxs[min_l]
        elif arcs:
            min_a = min(arcs, key=lambda a: len(arc_to_ctxs[a]))
            candidate_supersets = arc_to_ctxs[min_a]

        if candidate_supersets:
            contained_by = []
            for cand in candidate_supersets:
                if cand == nodeid or cand in identical_groups.get(nodeid, []):
                    continue
                cand_lines, cand_arcs = ctx_signature[cand]
                if (
                    len(cand_lines) >= len(lines)
                    and len(cand_arcs) >= len(arcs)
                    and lines.issubset(cand_lines)
                    and arcs.issubset(cand_arcs)
                ):
                    contained_by.append(cand)
                    if len(contained_by) >= 10:  # cap per test
                        break
            if contained_by:
                subset_groups[nodeid] = contained_by

    # Assemble per-test records
    tests_record: dict[str, Any] = {}
    modules_record: dict[str, Any] = {}
    no_cov_count = 0
    modules_tests: dict[str, list[str]] = defaultdict(list)

    for nodeid in all_nodeids:
        mod = _mod_of(nodeid)
        modules_tests[mod].append(nodeid)
        lines = ctx_lines.get(nodeid, set())
        arcs = ctx_arcs.get(nodeid, set())
        no_cov = len(lines) == 0 and len(arcs) == 0
        if no_cov:
            no_cov_count += 1

        tests_record[nodeid] = {
            "line_count": len(lines),
            "arc_count": len(arcs),
            "unique_lines": ctx_unique_lines[nodeid],
            "unique_arcs": ctx_unique_arcs[nodeid],
            "identical_group": identical_groups.get(nodeid, []),
            "subset_group": subset_groups.get(nodeid, []),
            "no_coverage": no_cov,
        }

    for mod, mod_tests in modules_tests.items():
        zero_u_lines = sum(1 for t in mod_tests if ctx_unique_lines[t] == 0)
        zero_u_arcs = sum(1 for t in mod_tests if ctx_unique_arcs[t] == 0)
        no_cov_tests = sum(1 for t in mod_tests if tests_record[t]["no_coverage"])

        modules_record[mod] = {
            "test_count": len(mod_tests),
            "zero_unique_line_count": zero_u_lines,
            "zero_unique_arc_count": zero_u_arcs,
            "no_coverage_count": no_cov_tests,
            "union_unique_lines": mod_unique_lines[mod],
            "union_unique_arcs": mod_unique_arcs[mod],
        }

    # Load cov_totals.json if available
    totals_file = dir_path / "cov_totals.json"
    num_statements: int | None = None
    num_branches: int | None = None
    pct_statements: float | None = None
    pct_branches: float | None = None

    if totals_file.is_file():
        try:
            with open(totals_file, encoding="utf-8") as f:
                cov_tot = json.load(f).get("totals", {})
            num_statements = cov_tot.get("num_statements")
            num_branches = cov_tot.get("num_branches")
            pct_statements = cov_tot.get("percent_statements_covered")
            pct_branches = cov_tot.get("percent_branches_covered")
        except (OSError, json.JSONDecodeError, KeyError):
            pass

    union_lines = len(line_to_ctxs)
    union_arcs = len(arc_to_ctxs)

    if num_statements and pct_statements is None:
        pct_statements = round((union_lines / num_statements) * 100.0, 2)
    if num_branches and pct_branches is None:
        pct_branches = round((union_arcs / num_branches) * 100.0, 2)

    meta_file = dir_path / "meta.json"
    metadata: dict[str, Any] = {}
    if meta_file.is_file():
        try:
            metadata = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    metadata["has_arcs"] = has_arcs

    result: dict[str, Any] = {
        "metadata": metadata,
        "totals": {
            "num_tests": len(all_nodeids),
            "num_no_coverage": no_cov_count,
            "union_lines": union_lines,
            "union_arcs": union_arcs,
            "num_statements": num_statements,
            "num_branches": num_branches,
            "percent_statements": pct_statements,
            "percent_branches": pct_branches,
        },
        "modules": modules_record,
        "tests": tests_record,
    }

    percov_json = dir_path / "percov.json"
    percov_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def compare_directories(
    current_dir: Path, baseline_dir: Path
) -> tuple[set[tuple[str, int]], set[tuple[str, int, int]]]:
    """Compare baseline (before) against current (after) coverage.

    Returns:
      (lost_lines, lost_arcs)
    """
    if current_dir.resolve() == baseline_dir.resolve():
        return set(), set()

    _, base_lines_map, base_arcs_map = extract_coverage_sets(baseline_dir / ".coverage")
    _, curr_lines_map, curr_arcs_map = extract_coverage_sets(current_dir / ".coverage")

    base_union_lines = (
        set().union(*base_lines_map.values()) if base_lines_map else set()
    )
    base_union_arcs = set().union(*base_arcs_map.values()) if base_arcs_map else set()

    curr_union_lines = (
        set().union(*curr_lines_map.values()) if curr_lines_map else set()
    )
    curr_union_arcs = set().union(*curr_arcs_map.values()) if curr_arcs_map else set()

    lost_lines = base_union_lines - curr_union_lines
    lost_arcs = base_union_arcs - curr_union_arcs
    return lost_lines, lost_arcs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze per-test coverage data.")
    parser.add_argument("dir", type=Path, help="Target coverage directory")
    parser.add_argument(
        "--compare",
        type=Path,
        default=None,
        help="Baseline directory to compare against",
    )
    parser.add_argument(
        "--reuse",
        action="store_true",
        help="Reuse existing percov.json in target dir if present",
    )

    args = parser.parse_args(argv)
    target_dir = args.dir.resolve()

    percov_json = target_dir / "percov.json"
    if args.reuse and percov_json.is_file():
        data = json.loads(percov_json.read_text(encoding="utf-8"))
    else:
        data = analyze_directory(target_dir)
    totals = data["totals"]

    sys.stdout.write("=== Percov Analysis Summary ===\n")
    sys.stdout.write(f"Total collected tests: {totals['num_tests']}\n")
    sys.stdout.write(f"No-coverage tests:     {totals['num_no_coverage']}\n")
    sys.stdout.write(f"Union covered lines:   {totals['union_lines']}\n")
    sys.stdout.write(f"Union covered arcs:    {totals['union_arcs']}\n")
    if totals.get("num_statements"):
        sys.stdout.write(
            f"Statements covered:    {totals['union_lines']}/{totals['num_statements']} "
            f"({totals.get('percent_statements', 0):.2f}%)\n"
        )
    if totals.get("num_branches"):
        sys.stdout.write(
            f"Branches covered:      {totals['union_arcs']}/{totals['num_branches']} "
            f"({totals.get('percent_branches', 0):.2f}%)\n"
        )

    zero_u_line_tests = sum(1 for t in data["tests"].values() if t["unique_lines"] == 0)
    zero_u_arc_tests = sum(1 for t in data["tests"].values() if t["unique_arcs"] == 0)
    sys.stdout.write(f"Tests with 0 unique lines: {zero_u_line_tests}\n")
    sys.stdout.write(f"Tests with 0 unique arcs:  {zero_u_arc_tests}\n")

    if args.compare:
        baseline_dir = args.compare.resolve()
        lost_lines, lost_arcs = compare_directories(target_dir, baseline_dir)
        sys.stdout.write("\n=== Coverage Comparison ===\n")
        sys.stdout.write(f"Current:  {target_dir}\n")
        sys.stdout.write(f"Baseline: {baseline_dir}\n")
        if not lost_lines and not lost_arcs:
            sys.stdout.write("zero lost lines and zero lost arcs\n")
        else:
            sys.stdout.write(f"Lost lines count: {len(lost_lines)}\n")
            for lost_ln in sorted(lost_lines):
                sys.stdout.write(f"  {lost_ln[0]}:{lost_ln[1]}\n")
            sys.stdout.write(f"Lost arcs count: {len(lost_arcs)}\n")
            for a in sorted(lost_arcs):
                sys.stdout.write(f"  {a[0]}:({a[1]}, {a[2]})\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
