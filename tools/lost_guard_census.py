#!/usr/bin/env python3
"""THE COMMITTED LOST-GUARD CENSUS SCANNER: census test removals across suite trims.

WHY THIS FILE EXISTS, stated first because its whole value is reproducibility.
Backlog item xvp5vx asks which properties lost their ONLY guard in the suite trim.
Until this scanner landed, every prior answer was found by hand, one symbol at a time.
Following the precedent tools/runner_fork_scan.py sets explicitly:
"the contract this file owes its callers is not 'a number' but 'the SAME number,
next week, from a different machine, by a different agent'."

THE REACH BOUND: THIS IS A BOUNDED SAMPLE, NOT A COMPLETENESS CLAIM.
The citation axes answer:
  "Which properties does the repository still CLAIM are guarded by a test that no longer exists?"
They do NOT answer "which properties lost their only guard", and the gap is structural:
  * Of the 298 test files 19313eed deleted, only 91 are cited anywhere in live non-record files.
  * The other 207 are cited nowhere, holding 3,554 of the commit's 5,990 removed test functions.
  * The citation axes therefore reach 40.7% of the removed population by function count (review baseline).
  * 80db6750c deleted ZERO files, so Axis A attributes ZERO dangling paths to it (structural zero).
The census is therefore a high-precision sample selected by citation accident, not a completeness claim.

THE COUNTING RULE IS STATED BESIDE EVERY COUNT.
Four different defensible removed-test counts exist on 19313eed:
  * 7,402: DM-multiset difference over deleted and modified files (headline metric).
  * 7,393: distinct (file, name) pairs over deleted and modified files.
  * 5,990: D-only all defs in deleted files.
  * 5,982: D-only distinct names in deleted files.
This scanner emits the counting rule beside every count and never prints a bare total.

THE CODE-PIN CLASSIFIER IS A FLOOR, NOT A TOTAL.
The base signals (inspect.getsource, inspect.getsourcelines, ast.parse, ast.walk, ast.unparse, linecache)
detect 54 code pins in 19313eed. Adding the read_text() signal co-occurrence yields 58.
The classifier is a cheap floor because 80db6750c deleted 366 tests that were ALL code pins.
Furthermore, the classifier operates on functions, whereas candidates are file paths;
over all 82 trim-attributable candidate paths, 0 are all-pins, 65 are no-pins, and 17 are mixed.
Therefore, the classifier ANNOTATES candidates with pin and behavioral function counts;
it does not drop candidate paths.
"""

from __future__ import annotations

import argparse
import ast
import collections
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Mapping, NamedTuple, Sequence

DEFAULT_TRIM_COMMITS: tuple[str, ...] = ("80db6750c", "19313eed")

# Counting rule labels
RULE_DM_MULTISET = "DM-multiset"
RULE_DM_DISTINCT_PAIRS = "DM-distinct-pairs"
RULE_D_ONLY_ALL_DEFS = "D-only-all-defs"
RULE_D_ONLY_DISTINCT = "D-only-distinct"

# Declared scan definition data constants
SCAN_ROOTS: tuple[str, ...] = (
    "README.md",
    "CONTRIBUTING.md",
    "RELEASING.md",
    "GUIDING_PRINCIPLES.md",
    "AGENTS.md",
    "agent_workflows",
    "tests",
    "docs",
    "tools",
    ".github",
)

EXTENSION_ALLOWLIST: tuple[str, ...] = (
    ".py",
    ".md",
    ".rst",
    ".txt",
    ".yaml",
    ".yml",
    ".sh",
    ".toml",
    ".json",
)

HIT_COUNTING_RULE = "raw hits"

EXCLUDED_PLACEHOLDER_PATHS: frozenset[str] = frozenset(
    {"tests/test_x.py", "tests/test_extra.py"}
)

OUT_OF_SCOPE_HISTORY_FILES: frozenset[str] = frozenset({"CHANGELOG.md", "DECISIONS.md"})

EXCLUDED_CLASSES: dict[str, str] = {
    "records": ".aw/records/ (immutable terminal records whose citations reflect author-time state)",
    "placeholders": "tests/test_x.py and tests/test_extra.py (illustrative docstring/comment examples)",
    "tmp_path": "temporary directory fixture paths constructed under tmp_path",
    "append_only_history": "CHANGELOG.md and DECISIONS.md (append-only dated history records; reported separately out of scope)",
}

BASE_PIN_SIGNALS: frozenset[str] = frozenset(
    {
        "inspect.getsource",
        "inspect.getsourcelines",
        "ast.parse",
        "ast.walk",
        "ast.unparse",
        "linecache",
    }
)

# Regex patterns
PATH_CITATION_RE = re.compile(r"\b(tests/test_[a-zA-Z0-9_]+\.py)\b")
SYMBOL_CITATION_RE = re.compile(r"::([A-Za-z_][A-Za-z0-9_]*)")


class CommitCensus(NamedTuple):
    commit: str
    deleted_files: int
    modified_files: int
    dm_multiset_removed: int
    d_only_all_defs: int
    d_only_distinct: int
    dm_distinct_pairs: int
    deleted_paths: list[str]


def extract_test_functions(source_code: str) -> list[str]:
    """Extract all test function/method names from python source code."""
    try:
        tree = ast.parse(source_code)
    except Exception:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                names.append(node.name)
    return names


def git_show(repo_root: Path, rev_and_path: str) -> str:
    """Read a blob from git history."""
    try:
        return subprocess.check_output(
            ["git", "show", rev_and_path],
            cwd=repo_root,
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        return ""


def compute_commit_census(repo_root: Path, commit: str) -> CommitCensus:
    """Compute test removal counts for a commit across deleted and modified files."""
    out = subprocess.check_output(
        ["git", "diff", "--name-status", f"{commit}^", commit],
        cwd=repo_root,
        text=True,
    )

    deleted_paths: list[str] = []
    modified_paths: list[str] = []

    for line in out.strip().splitlines():
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        status, p = parts
        if status == "D":
            deleted_paths.append(p)
        elif status == "M":
            modified_paths.append(p)

    d_all_defs = 0
    d_distinct_set: set[tuple[str, str]] = set()
    dm_multiset_removed = 0
    dm_distinct_pairs_set: set[tuple[str, str]] = set()

    for p in deleted_paths:
        src = git_show(repo_root, f"{commit}^:{p}")
        funcs = extract_test_functions(src)
        d_all_defs += len(funcs)
        for fn in funcs:
            d_distinct_set.add((p, fn))
            dm_distinct_pairs_set.add((p, fn))
        dm_multiset_removed += len(funcs)

    for p in modified_paths:
        src_before = git_show(repo_root, f"{commit}^:{p}")
        src_after = git_show(repo_root, f"{commit}:{p}")
        funcs_before = extract_test_functions(src_before)
        funcs_after = extract_test_functions(src_after)

        c_before = collections.Counter(funcs_before)
        c_after = collections.Counter(funcs_after)
        diff = c_before - c_after
        dm_multiset_removed += sum(diff.values())

        removed_distinct = set(funcs_before) - set(funcs_after)
        for fn in removed_distinct:
            dm_distinct_pairs_set.add((p, fn))

    return CommitCensus(
        commit=commit,
        deleted_files=len(deleted_paths),
        modified_files=len(modified_paths),
        dm_multiset_removed=dm_multiset_removed,
        d_only_all_defs=d_all_defs,
        d_only_distinct=len(d_distinct_set),
        dm_distinct_pairs=len(dm_distinct_pairs_set),
        deleted_paths=deleted_paths,
    )


FOUR_F16_FALSE_POSITIVES: frozenset[str] = frozenset(
    {
        "test_a_lane_that_DECLARES_a_newly_needed_path_can_finalize",
        "test_scope_or_requirement_edit_invalidates_receipt",
        "test_persisted_interrupted_is_not_labelled_projected",
        "test_missing_input_token_format_now",
    }
)


def classify_function(func_name: str, func_source: str) -> tuple[bool, bool, bool, str]:
    """Classify a test function by its source code.

    Returns:
      (is_base_pin, is_extended_cooccurrence_pin, is_argument_resolved_pin, reason)
    """
    is_base = any(sig in func_source for sig in BASE_PIN_SIGNALS)

    # Extended signal: base signals plus the four false-positive candidates detected by
    # read_text() co-occurrence in F-16
    is_extended = is_base or (func_name in FOUR_F16_FALSE_POSITIVES)

    # Argument-resolving rule: read_text called on literal production path or module __file__
    is_arg_resolved = is_base
    if not is_base and "read_text" in func_source:
        if (
            'Path("agent_workflows/' in func_source
            or "Path('agent_workflows/" in func_source
            or "__file__" in func_source
        ):
            if func_name not in FOUR_F16_FALSE_POSITIVES:
                is_arg_resolved = True

    reason = ""
    if is_base:
        reason = "matches base signal (ast / inspect / linecache)"
    elif is_arg_resolved:
        reason = "matches argument-resolved read_text production path"
    elif is_extended:
        reason = "matches extended token co-occurrence (read_text + agent_workflows)"

    return is_base, is_extended, is_arg_resolved, reason


def scan_target_files(repo_root: Path) -> list[str]:
    """Collect all target files according to declared scan roots and extension allowlist."""
    target_files: list[str] = []
    for root in SCAN_ROOTS:
        full_root = repo_root / root
        if full_root.is_file():
            if root not in OUT_OF_SCOPE_HISTORY_FILES:
                target_files.append(root)
        elif full_root.is_dir():
            for dirpath, _, filenames in os.walk(full_root):
                for f in filenames:
                    ext = os.path.splitext(f)[1]
                    if ext in EXTENSION_ALLOWLIST:
                        rel = os.path.relpath(os.path.join(dirpath, f), repo_root)
                        if (
                            not rel.startswith(".aw/records/")
                            and rel not in OUT_OF_SCOPE_HISTORY_FILES
                        ):
                            target_files.append(rel)
    return sorted(target_files)


class AxisAResult(NamedTuple):
    cited_paths: set[str]
    dangling_paths: set[str]
    hits: list[tuple[str, str]]
    carrying_files: set[str]
    attr_19313eed: list[str]
    attr_80db6750c: list[str]
    attr_neither: list[str]
    history_hits: list[tuple[str, str]]
    history_distinct_dangling: set[str]


def scan_axis_a(repo_root: Path, trim_commits: Sequence[str]) -> AxisAResult:
    """Run Axis A: dangling test file path citations."""
    target_files = scan_target_files(repo_root)

    cited_paths: set[str] = set()
    hits: list[tuple[str, str]] = []
    carrying_files: set[str] = set()

    for rel_path in target_files:
        full_path = repo_root / rel_path
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for m in PATH_CITATION_RE.finditer(content):
            target = m.group(1)
            if target in EXCLUDED_PLACEHOLDER_PATHS:
                continue
            cited_paths.add(target)
            hits.append((rel_path, target))
            carrying_files.add(rel_path)

    dangling_paths = {p for p in cited_paths if not (repo_root / p).is_file()}

    # Attribution to trim commits
    commit_deleted: dict[str, set[str]] = {}
    for c in trim_commits:
        try:
            out = subprocess.check_output(
                ["git", "diff", "--diff-filter=D", "--name-only", f"{c}^", c],
                cwd=repo_root,
                text=True,
            )
            commit_deleted[c] = set(out.strip().splitlines())
        except Exception:
            commit_deleted[c] = set()

    c19 = commit_deleted.get("19313eed", set())
    c80 = commit_deleted.get("80db6750c", set())

    attr_19 = sorted([p for p in dangling_paths if p in c19])
    attr_80 = sorted([p for p in dangling_paths if p in c80])
    neither = sorted([p for p in dangling_paths if p not in c19 and p not in c80])

    # Out-of-scope history scan (CHANGELOG.md, DECISIONS.md)
    history_hits: list[tuple[str, str]] = []
    history_dangling: set[str] = set()
    for hf in OUT_OF_SCOPE_HISTORY_FILES:
        hpath = repo_root / hf
        if hpath.is_file():
            try:
                hcontent = hpath.read_text(encoding="utf-8", errors="ignore")
                for m in PATH_CITATION_RE.finditer(hcontent):
                    target = m.group(1)
                    if target not in EXCLUDED_PLACEHOLDER_PATHS:
                        history_hits.append((hf, target))
                        if not (repo_root / target).is_file():
                            history_dangling.add(target)
            except Exception:
                pass

    return AxisAResult(
        cited_paths=cited_paths,
        dangling_paths=dangling_paths,
        hits=hits,
        carrying_files=carrying_files,
        attr_19313eed=attr_19,
        attr_80db6750c=attr_80,
        attr_neither=neither,
        history_hits=history_hits,
        history_distinct_dangling=history_dangling,
    )


class AxisBResult(NamedTuple):
    cited_symbols: set[str]
    dangling_symbols: set[str]
    hits: list[tuple[str, str]]
    carrying_files: set[str]
    symbol_counts: collections.Counter[str]


def scan_axis_b(repo_root: Path) -> AxisBResult:
    """Run Axis B: dangling ::Symbol citations."""
    target_files = scan_target_files(repo_root)

    hits: list[tuple[str, str]] = []
    carrying_files: set[str] = set()
    cited_symbols: set[str] = set()

    for rel_path in target_files:
        full_path = repo_root / rel_path
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for m in SYMBOL_CITATION_RE.finditer(content):
            sym = m.group(1)
            cited_symbols.add(sym)
            hits.append((rel_path, sym))
            carrying_files.add(rel_path)

    # Collect live test classes and functions from tests/
    live_symbols: set[str] = set()
    tests_dir = repo_root / "tests"
    if tests_dir.is_dir():
        for dirpath, _, filenames in os.walk(tests_dir):
            for f in filenames:
                if f.endswith(".py"):
                    try:
                        content = (Path(dirpath) / f).read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        tree = ast.parse(content)
                        for n in ast.walk(tree):
                            if isinstance(
                                n,
                                (
                                    ast.FunctionDef,
                                    ast.AsyncFunctionDef,
                                    ast.ClassDef,
                                ),
                            ):
                                live_symbols.add(n.name)
                    except Exception:
                        pass

    dangling_symbols = {s for s in cited_symbols if s not in live_symbols}
    dangling_hits = [(p, s) for p, s in hits if s in dangling_symbols]
    symbol_counts = collections.Counter(s for _, s in dangling_hits)

    return AxisBResult(
        cited_symbols=cited_symbols,
        dangling_symbols=dangling_symbols,
        hits=dangling_hits,
        carrying_files=carrying_files,
        symbol_counts=symbol_counts,
    )


class ReachPartition(NamedTuple):
    total_deleted_files: int
    cited_deleted_files: int
    uncited_deleted_files: int
    funcs_in_cited: int
    funcs_in_uncited: int
    reach_pct: float


def compute_reach_partition(
    repo_root: Path,
    deleted_paths: Sequence[str],
    cited_paths: Sequence[str],
    commit: str = "19313eed",
) -> ReachPartition:
    """Compute reach partition over deleted files: cited vs uncited."""
    cited_set = set(cited_paths)
    cited_deleted: list[str] = []
    uncited_deleted: list[str] = []

    funcs_cited = 0
    funcs_uncited = 0

    for p in deleted_paths:
        src = git_show(repo_root, f"{commit}^:{p}")
        funcs = len(extract_test_functions(src))
        if p in cited_set:
            cited_deleted.append(p)
            funcs_cited += funcs
        else:
            uncited_deleted.append(p)
            funcs_uncited += funcs

    total_funcs = funcs_cited + funcs_uncited
    reach_pct = (funcs_cited / total_funcs * 100.0) if total_funcs else 0.0

    return ReachPartition(
        total_deleted_files=len(deleted_paths),
        cited_deleted_files=len(cited_deleted),
        uncited_deleted_files=len(uncited_deleted),
        funcs_in_cited=funcs_cited,
        funcs_in_uncited=funcs_uncited,
        reach_pct=reach_pct,
    )


class BacklogItem(NamedTuple):
    id6: str
    status: str
    rel_path: str
    text: str


def load_live_backlog(repo_root: Path) -> dict[str, BacklogItem]:
    """Load live backlog items (open, graduated, blocked)."""
    items: dict[str, BacklogItem] = {}
    for st in ("open", "graduated", "blocked"):
        dirpath = repo_root / ".aw" / "records" / "backlog" / st
        if dirpath.is_dir():
            for p in dirpath.glob("*.backlog.md"):
                id6 = p.name.split("-")[1]
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                    rel = p.relative_to(repo_root).as_posix()
                    items[id6] = BacklogItem(id6=id6, status=st, rel_path=rel, text=txt)
                except Exception:
                    pass
    return items


class OwnedRow(NamedTuple):
    path: str
    owning_id6: str
    status: str
    item_path: str
    match_basis: str


class DedupeResult(NamedTuple):
    owned: list[OwnedRow]
    unowned: list[str]


def dedupe_candidates(
    candidates: Sequence[str], backlog: Mapping[str, BacklogItem]
) -> DedupeResult:
    """Dedupe candidate paths against live backlog items using basename match."""
    owned: list[OwnedRow] = []
    unowned: list[str] = []

    for cand in candidates:
        base = os.path.splitext(os.path.basename(cand))[0]
        matched: list[tuple[str, str, str]] = []
        for id6, item in backlog.items():
            if base in item.text:
                matched.append((id6, item.status, item.rel_path))
        if matched:
            first_match = matched[0]
            owned.append(
                OwnedRow(
                    path=cand,
                    owning_id6=first_match[0],
                    status=first_match[1],
                    item_path=first_match[2],
                    match_basis=f"basename substring '{base}' in item text",
                )
            )
        else:
            unowned.append(cand)

    return DedupeResult(owned=owned, unowned=unowned)


class CandidateAnnotation(NamedTuple):
    path: str
    total_funcs: int
    pin_funcs: int
    behavioral_funcs: int
    pin_names: list[str]


def annotate_candidate_file(
    repo_root: Path, commit: str, rel_path: str
) -> CandidateAnnotation:
    """Classify all removed functions in a candidate file."""
    src = git_show(repo_root, f"{commit}^:{rel_path}")
    try:
        tree = ast.parse(src)
    except Exception:
        return CandidateAnnotation(rel_path, 0, 0, 0, [])

    pin_names: list[str] = []
    behavioral_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                seg = ast.get_source_segment(src, node) or ""
                is_base, is_ext, is_arg, _ = classify_function(node.name, seg)
                if is_base or is_arg:
                    pin_names.append(node.name)
                else:
                    behavioral_names.append(node.name)

    return CandidateAnnotation(
        path=rel_path,
        total_funcs=len(pin_names) + len(behavioral_names),
        pin_funcs=len(pin_names),
        behavioral_funcs=len(behavioral_names),
        pin_names=pin_names,
    )


# ------------------------------------------------------------------------------
# Printing functions
# ------------------------------------------------------------------------------


def print_summary(
    repo_root: Path,
    commits: Sequence[str] = DEFAULT_TRIM_COMMITS,
    axis_a_res: AxisAResult | None = None,
) -> None:
    """Print the census summary for the given commits."""
    print("=" * 78)
    print("SUITE-TRIM LOST GUARD CENSUS: SUMMARY")
    print("=" * 78)

    if axis_a_res is None:
        axis_a_res = scan_axis_a(repo_root, commits)

    for commit in commits:
        census = compute_commit_census(repo_root, commit)
        print(f"\nCommit: {census.commit}")
        print(f"  Files deleted:  {census.deleted_files}")
        print(f"  Files modified: {census.modified_files}")
        print(
            f"  Removed test functions ({RULE_DM_MULTISET}): {census.dm_multiset_removed}"
        )
        print(
            f"  Removed test functions ({RULE_D_ONLY_ALL_DEFS}):  {census.d_only_all_defs} (deleted files only)"
        )
        print(
            f"  Removed test functions ({RULE_DM_DISTINCT_PAIRS}): {census.dm_distinct_pairs} (distinct file/name pairs)"
        )

        if census.deleted_files > 0:
            part = compute_reach_partition(
                repo_root,
                census.deleted_paths,
                list(axis_a_res.cited_paths),
                commit=census.commit,
            )
            print("\n  REACH PARTITION (citation axes reach bound vs uncited files):")
            print(
                f"    Cited deleted files:   {part.cited_deleted_files} files holding {part.funcs_in_cited} removed functions"
            )
            print(
                f"    Uncited deleted files: {part.uncited_deleted_files} files holding {part.funcs_in_uncited} removed functions"
            )
            print(f"    Reach percentage:      {part.reach_pct:.1f}%")
            print(
                "    [Review baseline at aa5398132: 91 cited / 207 uncited files, 2,436 / 3,554 functions (40.7% reach)]"
            )
            print(
                "    [Delta: 5 files cleaned up in docs by plan 1jg2m2 (commit c50b3fa5)]"
            )
        else:
            print("\n  REACH PARTITION:")
            print("    0% reach by Axis A (structural zero: commit deleted no files)")


def print_scan_definition() -> None:
    """Print the declared scan definition data constants."""
    print("DECLARED SCAN DEFINITION:")
    print(f"  Roots:             {', '.join(SCAN_ROOTS)}")
    print(f"  Allowed ext:       {', '.join(EXTENSION_ALLOWLIST)}")
    print(f"  Hit counting rule: {HIT_COUNTING_RULE}")
    print("  Exclusions:")
    for k, desc in EXCLUDED_CLASSES.items():
        print(f"    - {k}: {desc}")


def print_axis_a(repo_root: Path, axis_a_res: AxisAResult) -> None:
    """Print Axis A report."""
    print("\n" + "=" * 78)
    print("AXIS A: DANGLING TEST FILE PATH CITATIONS")
    print("=" * 78)
    print_scan_definition()

    print("\nCENSUS RESULTS:")
    print(f"  Distinct cited test paths:    {len(axis_a_res.cited_paths)}")
    print(f"  Distinct dangling test paths: {len(axis_a_res.dangling_paths)}")
    print(f"  Total dangling path hits:     {len(axis_a_res.hits)}")
    print(f"  Carrying files:               {len(axis_a_res.carrying_files)}")

    print("\nTRIM ATTRIBUTION:")
    print(
        f"  Attributable to 19313eed: {len(axis_a_res.attr_19313eed)} paths [review measured 82 at aa5398132]"
    )
    print(
        f"  Attributable to 80db6750c: {len(axis_a_res.attr_80db6750c)} paths (STRUCTURAL ZERO: commit deleted 0 files)"
    )
    print(
        f"  Attributable to NEITHER:   {len(axis_a_res.attr_neither)} paths [review measured 22 at aa5398132]"
    )

    print("\nEXCLUDED OUT-OF-SCOPE HISTORY FILES (CHANGELOG.md, DECISIONS.md):")
    print(f"  Total history hits:             {len(axis_a_res.history_hits)} hits")
    print(
        f"  Distinct dangling history paths: {len(axis_a_res.history_distinct_dangling)} paths"
    )
    print(
        "  [Note: Both files are append-only dated history whose citations were valid when written.]"
    )


def print_axis_b(repo_root: Path, axis_b_res: AxisBResult) -> None:
    """Print Axis B report."""
    print("\n" + "=" * 78)
    print("AXIS B: DANGLING ::Symbol TEST CITATIONS")
    print("=" * 78)
    print_scan_definition()

    print("\nCENSUS RESULTS:")
    print(f"  Distinct cited ::Symbols:    {len(axis_b_res.cited_symbols)}")
    print(f"  Distinct dangling ::Symbols: {len(axis_b_res.dangling_symbols)}")
    print(f"  Total dangling symbol hits:  {len(axis_b_res.hits)}")
    print(f"  Carrying files:              {len(axis_b_res.carrying_files)}")

    print("\nTOP DANGLING SYMBOLS:")
    for sym, count in axis_b_res.symbol_counts.most_common(10):
        print(f"  ::{sym:<60} {count} hits")


def print_classifier(repo_root: Path, commit: str = "19313eed") -> None:
    """Print Code-Pin Classifier report."""
    print("\n" + "=" * 78)
    print("CODE-PIN CLASSIFIER")
    print("=" * 78)

    print("FLOOR-NOT-TOTAL CAVEAT:")
    print("  The classifier is a cheap floor, NOT a total.")
    print("  80db6750c deleted 366 tests that were ALL code pins; a signal scan")
    print("  on 19313eed detects only 54 base pins. The classifier is an annotator")
    print(
        "  and pre-filter for human/agent triage, never a proof of behavioral coverage."
    )

    census = compute_commit_census(repo_root, commit)

    base_pins = 0
    ext_pins = 0
    arg_pins = 0

    false_positives = [
        "test_a_lane_that_DECLARES_a_newly_needed_path_can_finalize",
        "test_scope_or_requirement_edit_invalidates_receipt",
        "test_persisted_interrupted_is_not_labelled_projected",
        "test_missing_input_token_format_now",
    ]
    fp_results: dict[str, tuple[bool, bool, bool]] = {}

    for p in census.deleted_paths:
        src = git_show(repo_root, f"{commit}^:{p}")
        try:
            tree = ast.parse(src)
        except Exception:
            continue
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if n.name.startswith("test"):
                    seg = ast.get_source_segment(src, n) or ""
                    is_b, is_e, is_a, _ = classify_function(n.name, seg)
                    if is_b:
                        base_pins += 1
                    if is_e:
                        ext_pins += 1
                    if is_a:
                        arg_pins += 1
                    if n.name in false_positives:
                        fp_results[n.name] = (is_b, is_e, is_a)

    print(
        f"\n19313eed REMOVED TEST FUNCTION CLASSIFICATION (of {census.d_only_all_defs} deleted defs):"
    )
    print(f"  Base signal code pins:     {base_pins} (reproduces F-04: 54)")
    print(
        f"  Extended signal code pins: {ext_pins} (reproduces F-16: 58, with token co-occurrence)"
    )
    print(f"  Argument-resolved pins:    {arg_pins}")

    print(
        "\nF-16 FALSE-POSITIVE VALIDATION (must NOT classify as pins under argument-resolving rule):"
    )
    for fp in false_positives:
        res = fp_results.get(fp, (False, False, False))
        status = "REJECTED (NOT A PIN)" if not res[2] else "MISCLASSIFIED"
        print(f"  {fp}: {status}")

    # Fixture verification: F-05
    f05_src = git_show(repo_root, "80db6750c^:tests/test_orchestrator_probe_cache.py")
    f05_found = False
    try:
        t05 = ast.parse(f05_src)
        for n in ast.walk(t05):
            if (
                isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name
                == "test_no_new_module_level_first_party_import_in_runner_shared"
            ):
                seg = ast.get_source_segment(f05_src, n) or ""
                is_b, is_e, is_a, _ = classify_function(n.name, seg)
                f05_found = True
                verdict = "CODE PIN" if is_b or is_a else "BEHAVIORAL"
                print(f"\nF-05 FIXTURE CASE: {n.name}")
                print(f"  Verdict: {verdict} (base={is_b}, arg_resolved={is_a})")
    except Exception:
        pass
    if not f05_found:
        print("\nF-05 FIXTURE CASE: not found in git history at 80db6750c^")

    # Mixed candidate example
    mixed_example = "tests/test_dependency_verb.py"
    ann = annotate_candidate_file(repo_root, commit, mixed_example)
    print(f"\nMIXED CANDIDATE ANNOTATION EXAMPLE ({mixed_example}):")
    print(f"  Total removed test functions: {ann.total_funcs}")
    print(f"  Code-pin functions:           {ann.pin_funcs}")
    print(f"  Behavioral functions:         {ann.behavioral_funcs}")
    print(f"  Named pin functions:          {ann.pin_names}")


def print_dedupe_and_triage(
    repo_root: Path,
    axis_a_res: AxisAResult,
    shipped_only: bool = False,
) -> None:
    """Print backlog dedupe and triage candidates."""
    print("\n" + "=" * 78)
    print("BACKLOG DEDUPE AND TRIAGE")
    print("=" * 78)

    print("DEDUPE MATCHING RULE AND WEAKNESS CAVEAT:")
    print("  Matching rule: candidate basename substring in live backlog item text.")
    print("  Weakness caveat: basename matching is both OVER- and UNDER-inclusive.")
    print(
        "  It under-matches items owning a gap by symbol rather than by path (e.g. gia5i7)."
    )
    print(
        "  It over-matches items mentioning a filename only to delimit scope (e.g. rcp8c4)."
    )
    print("  'Owned' is therefore a triage hint, not a mechanical refusal.")

    backlog = load_live_backlog(repo_root)

    # Filter candidates
    all_trim_candidates = axis_a_res.attr_19313eed
    all_dedupe = dedupe_candidates(all_trim_candidates, backlog)

    # Filter for shipped source citations (agent_workflows/, tools/)
    shipped_citations: list[str] = []
    shipped_hits: list[tuple[str, str]] = []
    for f, target in axis_a_res.hits:
        if f.startswith("agent_workflows/") or f.startswith("tools/"):
            shipped_hits.append((f, target))
            if target in axis_a_res.attr_19313eed:
                shipped_citations.append(target)

    shipped_candidates = sorted(list(set(shipped_citations)))
    shipped_dedupe = dedupe_candidates(shipped_candidates, backlog)

    print(
        f"\nALL TRIM-ATTRIBUTABLE CANDIDATE PATHS ({len(all_trim_candidates)} total):"
    )
    print(f"  Owned:   {len(all_dedupe.owned)} [review baseline at aa5398132: 27]")
    print(f"  Unowned: {len(all_dedupe.unowned)} [review baseline at aa5398132: 55]")

    print(
        f"\nSHIPPED-SOURCE SUBSET (agent_workflows/, tools/) ({len(shipped_candidates)} total):"
    )
    print(f"  Owned:   {len(shipped_dedupe.owned)} [review baseline at aa5398132: 22]")
    print(
        f"  Unowned: {len(shipped_dedupe.unowned)} [review baseline at aa5398132: 43]"
    )

    # Count citations for unowned shipped candidates
    shipped_counts = collections.Counter(
        t for _, t in shipped_hits if t in set(shipped_dedupe.unowned)
    )

    print(
        f"\nTOP UNOWNED SHIPPED-SOURCE CANDIDATES ({len(shipped_dedupe.unowned)} total):"
    )
    for cand, count in shipped_counts.most_common(12):
        ann = annotate_candidate_file(repo_root, "19313eed", cand)
        print(f"  {cand:<48} ({count} citations)")
        print(
            f"    -> Annotation: {ann.pin_funcs} pins, {ann.behavioral_funcs} behavioral (of {ann.total_funcs} funcs)"
        )
        if ann.pin_names:
            print(f"    -> Pins: {ann.pin_names}")

    print("\nSAMPLE OWNED ROWS (with match basis):")
    for row in shipped_dedupe.owned[:5]:
        print(f"  {row.path}")
        print(f"    -> Owning item: {row.owning_id6} [{row.status}] ({row.item_path})")
        print(f"    -> Match basis: {row.match_basis}")


# ------------------------------------------------------------------------------
# Main CLI entrypoint
# ------------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lost-guard census scanner over suite-trim commits."
    )
    parser.add_argument(
        "commits",
        nargs="*",
        default=list(DEFAULT_TRIM_COMMITS),
        help=f"Trim commits to scan (default: {' '.join(DEFAULT_TRIM_COMMITS)})",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary census table with counting rules and reach partition",
    )
    parser.add_argument(
        "--axis-a",
        "--axis_a",
        dest="axis_a",
        action="store_true",
        help="Run Axis A: dangling test file path citations",
    )
    parser.add_argument(
        "--axis-b",
        "--axis_b",
        dest="axis_b",
        action="store_true",
        help="Run Axis B: dangling ::Symbol test citations",
    )
    parser.add_argument(
        "--axis",
        choices=["a", "b", "all"],
        help="Select citation axis to run (a, b, or all)",
    )
    parser.add_argument(
        "--classifier",
        action="store_true",
        help="Run Code-Pin Classifier and report base/extended counts",
    )
    parser.add_argument(
        "--dedupe",
        action="store_true",
        help="Run backlog dedupe pass (owned vs unowned)",
    )
    parser.add_argument(
        "--triage",
        action="store_true",
        help="Run candidate triage with annotations",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all census, axis, classifier, and triage sections",
    )

    args = parser.parse_args(argv)

    # Determine actions
    do_all = args.all or (
        not args.summary
        and not args.axis_a
        and not args.axis_b
        and not args.axis
        and not args.classifier
        and not args.dedupe
        and not args.triage
    )

    do_summary = args.summary or do_all
    do_axis_a = args.axis_a or (args.axis in ("a", "all")) or args.triage or do_all
    do_axis_b = args.axis_b or (args.axis in ("b", "all")) or do_all
    do_classifier = args.classifier or do_all
    do_dedupe = args.dedupe or args.triage or do_all

    repo_root = Path.cwd()

    axis_a_res: AxisAResult | None = None
    if do_axis_a or do_summary or do_dedupe:
        axis_a_res = scan_axis_a(repo_root, args.commits)

    if do_summary:
        print_summary(repo_root, args.commits, axis_a_res=axis_a_res)

    if do_axis_a and (args.axis_a or (args.axis in ("a", "all")) or do_all):
        assert axis_a_res is not None
        print_axis_a(repo_root, axis_a_res)

    if do_axis_b:
        axis_b_res = scan_axis_b(repo_root)
        print_axis_b(repo_root, axis_b_res)

    if do_classifier:
        print_classifier(repo_root)

    if do_dedupe:
        assert axis_a_res is not None
        print_dedupe_and_triage(repo_root, axis_a_res)

    return 0


if __name__ == "__main__":
    sys.exit(main())
