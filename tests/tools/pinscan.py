"""Structure-pin candidate scanner (IPD qqrgv3).

Scans test modules for static structure-pin patterns:
- inspect.getsource*
- ast.parse/ast.walk over module __file__
- read_text of production source under agent_workflows/
- hasattr/not hasattr on production modules/classes
- assertIs between host-module attributes
- __module__/__doc__ assertions
- not in sys.modules / sys.modules checks
- len(<mod>.<CONST>) ==
- .md docs read for prose assertions

Usage:
  python3 -m tests.tools.pinscan [--json] [--out FILE]
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

PATTERNS: dict[str, re.Pattern[str]] = {
    "inspect_getsource": re.compile(
        r"\binspect\.(?:getsource|getsourcelines|getsourcefile)\b"
    ),
    "ast_parse_walk": re.compile(r"\bast\.(?:parse|walk|unparse)\b"),
    "read_prod_source": re.compile(
        r"(?:read_text|read_bytes)\(.*agent_workflows|agent_workflows.*(?:read_text|read_bytes)|Path\([a-zA-Z0-9_]+\.__file__\)|rglob\(.*\.py"
    ),
    "hasattr_prod": re.compile(r"\bhasattr\([^,]+,\s*['\"][a-zA-Z0-9_]+['\"]\)"),
    "assert_is_host_attr": re.compile(
        r"assertIs\([^)]*(?:oc_runipd|agy_runipd|runner_shared)|assert\s+.*(?:oc_runipd|agy_runipd)\.[a-zA-Z0-9_]+\s+is\s+.*runner_shared"
    ),
    "module_doc_assertion": re.compile(r"\.(?:__module__|__doc__)\b"),
    "sys_modules_check": re.compile(
        r"(?:not\s+in|in)\s+sys\.modules|sys\.modules\.pop"
    ),
    "len_const_eq": re.compile(r"len\([a-zA-Z0-9_]+\.[A-Z0-9_]+\)\s*=="),
    "md_doc_prose": re.compile(
        r"['\"][a-zA-Z0-9_/.-]+\.md['\"].*read_text|read_text.*['\"][a-zA-Z0-9_/.-]+\.md['\"]"
    ),
}

BASELINE_PATTERN_IDS: frozenset[str] = frozenset(
    {"inspect_getsource", "ast_parse_walk", "read_prod_source", "hasattr_prod"}
)

FUNC_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(")
CLASS_DEF_RE = re.compile(r"^\s*class\s+([a-zA-Z0-9_]+)\b")


def scan_pins(target_dir: Path | None = None) -> list[dict[str, Any]]:
    """Scan test files under target_dir (or tests/) for structure-pin candidate patterns."""
    root = target_dir if target_dir is not None else (_REPO_ROOT / "tests")
    test_files = sorted(
        set(glob.glob(str(root / "test_*.py")))
        | set(glob.glob(str(root / "**/test_*.py"), recursive=True))
    )

    candidates: list[dict[str, Any]] = []

    for fpath_str in test_files:
        fpath = Path(fpath_str)
        try:
            rel_file = fpath.resolve().relative_to(_REPO_ROOT).as_posix()
        except Exception:
            rel_file = fpath.name

        try:
            lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue

        current_class = ""
        current_func = ""

        for idx, line in enumerate(lines, start=1):
            c_match = CLASS_DEF_RE.match(line)
            if c_match:
                current_class = c_match.group(1)
                current_func = ""

            f_match = FUNC_DEF_RE.match(line)
            if f_match:
                fn_name = f_match.group(1)
                if current_class:
                    current_func = f"{current_class}::{fn_name}"
                else:
                    current_func = fn_name

            for pid, pat in PATTERNS.items():
                if pat.search(line):
                    candidates.append(
                        {
                            "file": rel_file,
                            "line": idx,
                            "pattern_id": pid,
                            "enclosing_func": current_func or "<module>",
                            "line_text": line.strip(),
                        }
                    )

    return candidates


def summarize_pins(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute per-pattern counts and file union counts."""
    files_by_pattern: dict[str, set[str]] = {pid: set() for pid in PATTERNS}
    hits_by_pattern: dict[str, int] = {pid: 0 for pid in PATTERNS}
    union_files: set[str] = set()
    baseline_files: set[str] = set()

    for c in candidates:
        pid = c["pattern_id"]
        f = c["file"]
        files_by_pattern[pid].add(f)
        hits_by_pattern[pid] += 1
        union_files.add(f)
        if pid in BASELINE_PATTERN_IDS:
            baseline_files.add(f)

    return {
        "total_hits": len(candidates),
        "union_files": len(union_files),
        "baseline_files": len(baseline_files),
        "pattern_file_counts": {pid: len(s) for pid, s in files_by_pattern.items()},
        "pattern_hit_counts": hits_by_pattern,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan test modules for structure-pin candidate patterns."
    )
    parser.add_argument("--json", action="store_true", help="Emit output as JSON")
    parser.add_argument("--out", type=Path, default=None, help="Output file path")
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=None,
        type=Path,
        help="Optional test directory to scan",
    )

    args = parser.parse_args(argv)
    candidates = scan_pins(args.target_dir)
    summary = summarize_pins(candidates)

    if args.json:
        out_content = json.dumps(
            {"summary": summary, "candidates": candidates}, indent=2
        )
        if args.out:
            args.out.write_text(out_content, encoding="utf-8")
        else:
            sys.stdout.write(out_content + "\n")
        return 0

    # Human-readable markdown summary
    out_lines = [
        "# Structure-Pin Candidate Scan Summary",
        "",
        f"- Total candidate hits: {summary['total_hits']}",
        f"- Total union files matched: {summary['union_files']}",
        f"- Baseline pattern set files matched: {summary['baseline_files']}",
        "",
        "## Per-Pattern File and Hit Counts",
        "",
        "| Pattern ID | Matching Files | Total Hits | Description |",
        "| --- | --- | --- | --- |",
    ]

    descriptions = {
        "inspect_getsource": "inspect.getsource / getsourcelines / getsourcefile",
        "ast_parse_walk": "ast.parse / ast.walk / ast.unparse",
        "read_prod_source": "read_text of package files under agent_workflows/",
        "hasattr_prod": "hasattr on production module or class",
        "assert_is_host_attr": "assertIs between host-module attributes",
        "module_doc_assertion": ".__module__ or .__doc__ assertions",
        "sys_modules_check": "not in sys.modules / sys.modules access",
        "len_const_eq": "len(<mod>.<CONST>) == assertions",
        "md_doc_prose": ".md documentation read for prose assertions",
    }

    for pid in PATTERNS:
        fcount = summary["pattern_file_counts"].get(pid, 0)
        hcount = summary["pattern_hit_counts"].get(pid, 0)
        desc = descriptions.get(pid, "")
        out_lines.append(f"| `{pid}` | {fcount} | {hcount} | {desc} |")

    report_text = "\n".join(out_lines) + "\n"
    if args.out:
        args.out.write_text(report_text, encoding="utf-8")
    else:
        sys.stdout.write(report_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
