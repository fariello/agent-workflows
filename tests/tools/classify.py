"""Test classifier and decision table builder (IPD qqrgv3).

Joins percov.json, junit.xml durations, markers (core, slow, livecorpus),
defect citations (backlog/plan id6 or incident/run id), and pinscan hits.
Applies fixed rules and precedence to propose keep, consolidate, speed-up,
or delete-candidate per test and per module.

Usage:
  python3 -m tests.tools.classify DIR [--out OUT_DIR]
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

from tests.tools.pinscan import scan_pins

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Explicit, reviewable list of protected module families (requirement E-05)
PROTECTED_FAMILIES: tuple[str, ...] = (
    "tests/test_agent_surface_conformance.py",
    "tests/test_backlog_transition_gate.py",
    "tests/test_check_engine_release_gate.py",
    "tests/test_config_release_gate_kinds.py",
    "tests/test_conformance_matrix_structure.py",
    "tests/test_executed_transition_gate.py",
    "tests/test_executed_transition_gate_e2e.py",
    "tests/test_exit_contract_conformance.py",
    "tests/test_family_root_agent_conformance.py",
    "tests/test_ipd_lifecycle_backward_edges.py",
    "tests/test_ipd_lifecycle_cli.py",
    "tests/test_json_surface_leak_posture.py",
    "tests/test_leak_sanitizer.py",
    "tests/test_leak_sanitizer_machine_flags.py",
    "tests/test_live_conformance_sweep.py",
    "tests/test_local_leaks.py",
    "tests/test_plan_transition_gate.py",
    "tests/test_release_gate_one_way_mismatch.py",
    "tests/test_staged_illegal_backlog_transition_gate.py",
)

DEFECT_CITE_RE = re.compile(
    r"\b(?:backlog|plan|spec|ipd|incident|bug|issue)\s*[:#=\-\s]?\s*([0-9a-z]{6})\b|\b(run-\d{8}T\d{6}Z)\b|\bincident[-_][a-zA-Z0-9]+\b",
    re.IGNORECASE,
)


def _load_known_id6s() -> set[str]:
    """Scan .aw/records/ for all known artifact id6s."""
    id6s: set[str] = set()
    records_dir = _REPO_ROOT / ".aw" / "records"
    if records_dir.is_dir():
        for p in glob.glob(str(records_dir / "**/*.md"), recursive=True):
            for cand in re.findall(r"\b([0-9a-z]{6})\b", p):
                id6s.add(cand)
    return id6s


def _load_junit_durations(junit_file: Path) -> dict[str, float]:
    """Extract call duration per test from junit.xml."""
    durations: dict[str, float] = {}
    if not junit_file.is_file():
        return durations

    try:
        tree = ET.parse(junit_file)
        for tc in tree.findall(".//testcase"):
            t_str = tc.attrib.get("time", "0.0")
            try:
                dur = float(t_str)
            except ValueError:
                dur = 0.0

            file_attr = tc.attrib.get("file", "")
            name = tc.attrib.get("name", "")
            classname = tc.attrib.get("classname", "")

            if file_attr and name:
                node = f"{file_attr}::{name}"
                durations[node] = dur

            # Also key by classname::name
            durations[f"{classname}::{name}"] = dur
    except Exception:
        pass
    return durations


def _scan_test_text_for_defects(
    test_file: Path, known_id6s: set[str]
) -> dict[str, list[str]]:
    """Scan test functions in a file for defect citations."""
    citations_by_func: dict[str, list[str]] = defaultdict(list)
    try:
        content = test_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return citations_by_func

    # Match functions
    lines = content.splitlines()
    curr_func = "<module>"
    for line in lines:
        m_def = re.match(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(", line)
        if m_def:
            curr_func = m_def.group(1)

        for m in DEFECT_CITE_RE.finditer(line):
            id6 = m.group(1)
            run_id = m.group(2)
            if id6 and id6.lower() in known_id6s:
                citations_by_func[curr_func].append(id6.lower())
            elif run_id:
                citations_by_func[curr_func].append(run_id)
            elif m.group(0):
                citations_by_func[curr_func].append(m.group(0))

    return citations_by_func


def classify_suite(
    dir_path: Path,
    test_dir: Path | None = None,
    pin_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    percov_file = dir_path / "percov.json"
    if not percov_file.is_file():
        raise FileNotFoundError(f"percov.json not found in {dir_path}")

    with open(percov_file, encoding="utf-8") as f:
        percov_data = json.load(f)

    junit_file = dir_path / "junit.xml"
    durations = _load_junit_durations(junit_file)

    markers_file = dir_path / "markers.json"
    markers_map: dict[str, list[str]] = {}
    if markers_file.is_file():
        try:
            with open(markers_file, encoding="utf-8") as f:
                markers_map = json.load(f)
        except Exception:
            pass

    known_id6s = _load_known_id6s()

    # Structure-pin candidates
    if pin_candidates is None:
        pin_candidates = scan_pins(test_dir)
    pins_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pins_by_func: dict[tuple[str, str], list[str]] = defaultdict(list)
    for p in pin_candidates:
        pins_by_file[p["file"]].append(p)
        func_name = p["enclosing_func"].split("::")[-1]
        pins_by_func[(p["file"], func_name)].append(p["pattern_id"])

    # File-level defect citations cache
    defects_by_file: dict[str, dict[str, list[str]]] = {}

    test_records: dict[str, Any] = {}
    modules_tests: dict[str, list[str]] = defaultdict(list)

    # Classify each test
    for nodeid, t_info in percov_data.get("tests", {}).items():
        parts = nodeid.split("::")
        mod = parts[0]
        func = parts[-1]
        if "[" in func:
            func = func.split("[")[0]

        modules_tests[mod].append(nodeid)

        if mod not in defects_by_file:
            mod_path = _REPO_ROOT / mod
            defects_by_file[mod] = (
                _scan_test_text_for_defects(mod_path, known_id6s)
                if mod_path.is_file()
                else {}
            )

        test_markers = markers_map.get(nodeid, [])
        is_core = "core" in test_markers
        is_livecorpus = "livecorpus" in test_markers or "livecorpus" in mod
        is_protected_family = mod in PROTECTED_FAMILIES
        is_protected = is_core or is_livecorpus or is_protected_family

        cites_defect = defects_by_file[mod].get(func, []) or defects_by_file[mod].get(
            "<module>", []
        )

        # Duration
        dur = durations.get(nodeid, 0.0)
        if dur == 0.0 and len(parts) >= 2:
            # fallback match by classname
            cls_name = mod.replace("/", ".").rstrip(".py")
            dur = durations.get(f"{cls_name}::{parts[-1]}", 0.0)

        pin_hits = pins_by_func.get((mod, func), [])
        if not pin_hits and (mod in pins_by_file):
            # check if module-level pin
            pin_hits = [
                p["pattern_id"]
                for p in pins_by_file[mod]
                if p["enclosing_func"] == "<module>"
            ]

        # Collect rule triggers
        rules_fired: list[str] = []
        if is_core:
            rules_fired.append("protected (core)")
        if is_livecorpus:
            rules_fired.append("protected (livecorpus)")
        if is_protected_family:
            rules_fired.append("protected (family)")
        if cites_defect:
            rules_fired.append(f"defect-cited ({', '.join(sorted(set(cites_defect)))})")
        if t_info.get("no_coverage"):
            rules_fired.append("read-required (no-coverage)")
        if pin_hits:
            rules_fired.append(
                f"read-required (pin: {', '.join(sorted(set(pin_hits)))})"
            )
        if dur > 2.0:
            rules_fired.append(f"speed-up (duration {dur:.2f}s > 2s)")
        if (
            t_info.get("unique_lines", 0) == 0
            and t_info.get("unique_arcs", 0) == 0
            and len(t_info.get("identical_group", [])) > 0
        ):
            rules_fired.append("consolidate (identical peer)")
        elif t_info.get("unique_lines", 0) == 0 and t_info.get("unique_arcs", 0) == 0:
            rules_fired.append("delete-candidate (0 unique)")

        # Determine disposition following fixed rules and precedence:
        # protected > read-required > speed-up > consolidate > delete-candidate > keep
        proposed: str
        owner: str

        if is_protected:
            # Never delete-candidate
            if dur > 2.0:
                proposed = "speed-up"
                owner = "c8bfp9"
            elif (
                t_info.get("unique_lines", 0) == 0
                and t_info.get("unique_arcs", 0) == 0
                and len(t_info.get("identical_group", [])) > 0
            ):
                proposed = "consolidate"
                owner = "83nnyn"
            else:
                proposed = "keep"
                owner = "keep"
        elif t_info.get("no_coverage") or pin_hits:
            proposed = "read-required"
            owner = "tv72xy"
        elif dur > 2.0:
            proposed = "speed-up"
            owner = "c8bfp9"
        elif cites_defect:
            # Defect citation is consolidate at most
            if (
                t_info.get("unique_lines", 0) == 0
                and t_info.get("unique_arcs", 0) == 0
                and len(t_info.get("identical_group", [])) > 0
            ):
                proposed = "consolidate"
                owner = "83nnyn"
            else:
                proposed = "keep"
                owner = "keep"
        elif (
            t_info.get("unique_lines", 0) == 0
            and t_info.get("unique_arcs", 0) == 0
            and len(t_info.get("identical_group", [])) > 0
        ):
            proposed = "consolidate"
            owner = "83nnyn"
        elif t_info.get("unique_lines", 0) == 0 and t_info.get("unique_arcs", 0) == 0:
            proposed = "delete-candidate"
            owner = "tv72xy"
        else:
            proposed = "keep"
            owner = "keep"

        test_records[nodeid] = {
            "module": mod,
            "duration": dur,
            "is_core": is_core,
            "is_livecorpus": is_livecorpus,
            "is_protected": is_protected,
            "cites_defect": cites_defect,
            "pin_hits": pin_hits,
            "proposed_disposition": proposed,
            "reason": "; ".join(rules_fired) if rules_fired else "unique coverage",
            "owner": owner,
        }

    # Module rollups
    module_rows: list[dict[str, Any]] = []
    percov_mods = percov_data.get("modules", {})

    for mod, test_ids in sorted(modules_tests.items()):
        m_tests = [test_records[tid] for tid in test_ids]
        mod_info = percov_mods.get(mod, {})

        total_wall = sum(t["duration"] for t in m_tests)
        u_lines = mod_info.get("union_unique_lines", 0)
        u_arcs = mod_info.get("union_unique_arcs", 0)

        is_mod_protected = (
            mod in PROTECTED_FAMILIES
            or any(t["is_livecorpus"] for t in m_tests)
            or all(t["is_core"] for t in m_tests)
        )

        disp_counts: dict[str, int] = defaultdict(int)
        for t in m_tests:
            disp_counts[t["proposed_disposition"]] += 1

        mod_disp: str
        mod_owner: str
        mod_reason: str

        if is_mod_protected:
            # Cannot be delete-candidate
            if disp_counts["speed-up"] > 0:
                mod_disp = "speed-up"
                mod_owner = "c8bfp9"
                mod_reason = f"protected family/livecorpus/core; {disp_counts['speed-up']} tests > 2s"
            elif disp_counts["consolidate"] > 0:
                mod_disp = "consolidate"
                mod_owner = "83nnyn"
                mod_reason = f"protected family/livecorpus/core; {disp_counts['consolidate']} candidate consolidate tests"
            else:
                mod_disp = "keep"
                mod_owner = "keep"
                mod_reason = "protected family/livecorpus/core; keep"
        else:
            if disp_counts["delete-candidate"] == len(m_tests) and len(m_tests) > 0:
                mod_disp = "delete-candidate"
                mod_owner = "tv72xy"
                mod_reason = f"all {len(m_tests)} tests are 0-unique delete candidates"
            elif disp_counts["read-required"] > 0:
                mod_disp = "read-required"
                mod_owner = "tv72xy"
                mod_reason = f"{disp_counts['read-required']} tests require reading (pinscan or no-coverage)"
            elif disp_counts["speed-up"] > 0:
                mod_disp = "speed-up"
                mod_owner = "c8bfp9"
                mod_reason = f"{disp_counts['speed-up']} tests > 2s"
            elif disp_counts["consolidate"] > 0:
                mod_disp = "consolidate"
                mod_owner = "83nnyn"
                mod_reason = (
                    f"{disp_counts['consolidate']} tests with identical coverage peers"
                )
            else:
                mod_disp = "keep"
                mod_owner = "keep"
                mod_reason = "provides unique coverage; keep"

        module_rows.append(
            {
                "module": mod,
                "tests": len(test_ids),
                "wall_seconds": round(total_wall, 2),
                "unique_lines": u_lines,
                "unique_arcs": u_arcs,
                "proposed_disposition": mod_disp,
                "reason": mod_reason,
                "owner": mod_owner,
            }
        )

    return {
        "protected_families": list(PROTECTED_FAMILIES),
        "module_rows": module_rows,
        "test_records": test_records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify tests and build decision table."
    )
    parser.add_argument(
        "dir", type=Path, help="Directory containing percov.json and junit.xml"
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="Optional output directory for results"
    )

    args = parser.parse_args(argv)
    target_dir = args.dir.resolve()
    out_dir = args.out.resolve() if args.out else target_dir

    result = classify_suite(target_dir)
    module_rows = result["module_rows"]
    test_records = result["test_records"]

    # Write per-test classification JSON
    tests_json_path = out_dir / "classification_tests.json"
    tests_json_path.write_text(json.dumps(test_records, indent=2), encoding="utf-8")

    # Write markdown table per module
    table_lines = [
        "# Test Prune Decision Table",
        "",
        "## Explicit Protected Module Families",
        "",
    ]
    for p in result["protected_families"]:
        table_lines.append(f"- `{p}`")

    table_lines.extend(
        [
            "",
            "## Per-Module Decision Table",
            "",
            "| Module | Tests | Wall (s) | Unique Lines | Unique Arcs | Proposed Disposition | Reason | Owner |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    disp_counts: dict[str, int] = defaultdict(int)
    for row in module_rows:
        disp_counts[row["proposed_disposition"]] += 1
        table_lines.append(
            f"| `{row['module']}` | {row['tests']} | {row['wall_seconds']:.2f} | "
            f"{row['unique_lines']} | {row['unique_arcs']} | `{row['proposed_disposition']}` | "
            f"{row['reason']} | `{row['owner']}` |"
        )

    table_path = out_dir / "decision_table.md"
    table_text = "\n".join(table_lines) + "\n"
    table_path.write_text(table_text, encoding="utf-8")

    # Print summary to stdout
    sys.stdout.write("=== Classification Summary ===\n")
    sys.stdout.write(f"Total collected modules: {len(module_rows)}\n")
    sys.stdout.write("Module disposition counts:\n")
    for d, c in sorted(disp_counts.items()):
        sys.stdout.write(f"  {d:20s}: {c}\n")

    test_disp_counts: dict[str, int] = defaultdict(int)
    for t in test_records.values():
        test_disp_counts[t["proposed_disposition"]] += 1
    sys.stdout.write("Test disposition counts:\n")
    for d, c in sorted(test_disp_counts.items()):
        sys.stdout.write(f"  {d:20s}: {c}\n")

    sys.stdout.write(f"\nWrote {tests_json_path} and {table_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
