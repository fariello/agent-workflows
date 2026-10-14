#!/usr/bin/env python3
"""Worktree-isolated mutation probe.

Tests whether a test selection kills a named mutant, baseline-corrected and
isolated in a disposable git worktree outside the repository.
"""

from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence
import xml.etree.ElementTree as ET

OPERATORS: tuple[str, ...] = (
    "return-none",
    "return-true",
    "return-false",
    "negate-return",
    "raise",
)


@dataclass
class ProbeResult:
    head: str
    target: str
    operator: str
    selection: list[str]
    verdict: str
    reason: str | None
    baseline_failing: int | None
    mutant_failing: int | None
    newly_failing: list[str]
    newly_failing_total: int
    flaky: list[str]
    extra_tests_overwrote: list[str]
    wall_s: float
    checkout_status_changed: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


def apply_operator(source: str, qualname: str, operator: str) -> str | None:
    """Pure splice function that returns mutated module source or None."""
    if operator not in OPERATORS:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    parts = qualname.split(".")
    current: ast.AST = tree

    def find_child(parent: ast.AST, name: str, is_func_only: bool) -> ast.AST | None:
        for child in ast.iter_child_nodes(parent):
            if is_func_only:
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child.name == name
                ):
                    return child
            else:
                if (
                    isinstance(
                        child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                    )
                    and child.name == name
                ):
                    return child
        compound_nodes: tuple[type[ast.AST], ...] = (
            ast.If,
            ast.Try,
            ast.With,
            ast.ExceptHandler,
            ast.For,
            ast.While,
        ) + ((ast.Match,) if hasattr(ast, "Match") else ())
        for child in ast.iter_child_nodes(parent):
            if isinstance(child, compound_nodes):
                res = find_child(child, name, is_func_only)
                if res is not None:
                    return res
        return None

    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        found = find_child(current, part, is_func_only=is_last)
        if found is None:
            return None
        current = found

    target_node = current
    if not isinstance(target_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None

    mutated = copy.deepcopy(target_node)
    if operator == "return-none":
        mutated.body = [ast.Return(value=ast.Constant(value=None))]
    elif operator == "return-true":
        mutated.body = [ast.Return(value=ast.Constant(value=True))]
    elif operator == "return-false":
        mutated.body = [ast.Return(value=ast.Constant(value=False))]
    elif operator == "raise":
        mutated.body = [
            ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                    args=[ast.Constant(value="mutant")],
                    keywords=[],
                ),
                cause=None,
            )
        ]
    elif operator == "negate-return":
        count = 0

        def visit(n: ast.AST) -> None:
            nonlocal count
            for child in ast.iter_child_nodes(n):
                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
                ):
                    continue
                if isinstance(child, ast.Return) and child.value is not None:
                    child.value = ast.UnaryOp(op=ast.Not(), operand=child.value)
                    count += 1
                else:
                    visit(child)

        visit(mutated)
        if count == 0:
            return None

    start_line = (
        target_node.decorator_list[0].lineno
        if target_node.decorator_list
        else target_node.lineno
    )
    end_line = target_node.end_lineno
    if start_line is None or end_line is None:
        return None

    lines = source.splitlines(keepends=True)
    unparsed = ast.unparse(mutated)
    indent = " " * target_node.col_offset
    replacement_lines = [f"{indent}{line}\n" for line in unparsed.splitlines()]

    new_lines = lines[: start_line - 1] + replacement_lines + lines[end_line:]
    result = "".join(new_lines)
    try:
        compile(result, "<mutant>", "exec")
    except Exception:
        return None
    return result


def _parse_junit_xml(xml_path: str | Path) -> tuple[set[str], set[str]]:
    """Parse junit XML into (failing_or_erroring_node_ids, collection_error_node_ids)."""
    failing_ids: set[str] = set()
    collection_errors: set[str] = set()

    try:
        tree = ET.parse(xml_path)
    except Exception:
        return failing_ids, collection_errors

    for tc in tree.iter("testcase"):
        has_failure = tc.find("failure") is not None
        has_error = tc.find("error") is not None
        if not (has_failure or has_error):
            continue

        classname = tc.attrib.get("classname", "").strip()
        name = tc.attrib.get("name", "").strip()

        if classname:
            node_id = f"{classname}::{name}"
            failing_ids.add(node_id)
        else:
            if name.endswith(".py"):
                mod_path = name
            else:
                mod_path = name.replace(".", "/") + ".py"
            collection_errors.add(mod_path)
            failing_ids.add(mod_path)

    return failing_ids, collection_errors


def _node_id_to_selector(node_id: str, wt_dir: str) -> str:
    """Map a JUnit node id (<classname>::<name> or <module path>) to a pytest selector."""
    if "::" not in node_id:
        return node_id
    cls_name, test_name = node_id.split("::", 1)
    parts = cls_name.split(".")
    for i in range(len(parts), 0, -1):
        rel_file = os.path.join(*parts[:i]) + ".py"
        if os.path.exists(os.path.join(wt_dir, rel_file)):
            rest = parts[i:]
            if rest:
                return f"{rel_file}::{'::'.join(rest)}::{test_name}"
            return f"{rel_file}::{test_name}"
    return node_id


def probe(
    repo_root: str | Path,
    target: str,
    operator: str,
    pytest_args: Sequence[str] | None = None,
    extra_tests: Sequence[str] = (),
    timeout_s: int = 1800,
) -> ProbeResult:
    """Execute a worktree-isolated mutation probe against committed HEAD."""
    start_time = time.monotonic()
    repo_root_path = Path(repo_root).resolve()
    repo_root_str = str(repo_root_path)

    head_res = subprocess.run(
        ["git", "-C", repo_root_str, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    head_sha = head_res.stdout.strip()

    if pytest_args is not None:
        selection = list(pytest_args)
    else:
        selection = ["-n", "auto", "-m", "not slow and not livecorpus"]

    if "::" not in target:
        raise ValueError(f"target must be <path.py>::<qualname>, got: {target}")
    rel_target_path, qualname = target.split("::", 1)

    status_before = subprocess.run(
        ["git", "-C", repo_root_str, "status", "--porcelain"],
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    tmp_parent = tempfile.mkdtemp(prefix="mutation_probe_")
    wt_dir = os.path.join(tmp_parent, "wt")
    checkout_status_changed: list[str] = []

    def make_result(
        verdict: str,
        reason: str | None,
        baseline_failing: int | None,
        mutant_failing: int | None,
        newly_failing: list[str],
        newly_failing_total: int,
        flaky: list[str],
        extra_tests_overwrote: list[str],
    ) -> ProbeResult:
        wall_s = round(time.monotonic() - start_time, 2)
        return ProbeResult(
            head=head_sha,
            target=target,
            operator=operator,
            selection=selection,
            verdict=verdict,
            reason=reason,
            baseline_failing=baseline_failing,
            mutant_failing=mutant_failing,
            newly_failing=newly_failing,
            newly_failing_total=newly_failing_total,
            flaky=flaky,
            extra_tests_overwrote=extra_tests_overwrote,
            wall_s=wall_s,
            checkout_status_changed=checkout_status_changed,
        )

    try:
        add_res = subprocess.run(
            ["git", "-C", repo_root_str, "worktree", "add", "--detach", wt_dir, "HEAD"],
            capture_output=True,
            text=True,
        )
        if add_res.returncode != 0:
            return make_result(
                verdict="error",
                reason=f"failed to add worktree: {add_res.stderr.strip()}",
                baseline_failing=None,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=[],
            )

        extra_tests_overwrote: list[str] = []
        for item in extra_tests:
            if ":" not in item:
                return make_result(
                    verdict="error",
                    reason=f"malformed extra test spec {item!r}, expected COMMIT:PATH",
                    baseline_failing=None,
                    mutant_failing=None,
                    newly_failing=[],
                    newly_failing_total=0,
                    flaky=[],
                    extra_tests_overwrote=extra_tests_overwrote,
                )
            commit, test_path = item.split(":", 1)
            dest = os.path.join(wt_dir, test_path)
            if os.path.exists(dest):
                extra_tests_overwrote.append(test_path)
            show_res = subprocess.run(
                ["git", "-C", repo_root_str, "show", f"{commit}^:{test_path}"],
                capture_output=True,
            )
            if show_res.returncode != 0:
                return make_result(
                    verdict="error",
                    reason=f"extra test blob {commit}^:{test_path} not found",
                    baseline_failing=None,
                    mutant_failing=None,
                    newly_failing=[],
                    newly_failing_total=0,
                    flaky=[],
                    extra_tests_overwrote=extra_tests_overwrote,
                )
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(show_res.stdout)

        target_full_path = os.path.join(wt_dir, rel_target_path)
        if not os.path.exists(target_full_path):
            return make_result(
                verdict="invalid",
                reason="target file not found",
                baseline_failing=None,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        with open(target_full_path, "r", encoding="utf-8") as f:
            original_source = f.read()

        mutated_source = apply_operator(original_source, qualname, operator)
        if mutated_source is None:
            return make_result(
                verdict="invalid",
                reason="operator not applicable or qualname absent",
                baseline_failing=None,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        first_comp = Path(rel_target_path).parts[0]
        pkg_name = first_comp[:-3] if first_comp.endswith(".py") else first_comp

        env = dict(os.environ)
        env["PYTHONPATH"] = wt_dir + (
            os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else ""
        )

        preflight_res = subprocess.run(
            [sys.executable, "-c", f"import {pkg_name}; print({pkg_name}.__file__)"],
            cwd=wt_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        if preflight_res.returncode != 0:
            return make_result(
                verdict="error",
                reason="isolation",
                baseline_failing=None,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        imported_path = os.path.realpath(preflight_res.stdout.strip())
        wt_real = os.path.realpath(wt_dir)
        if not (imported_path == wt_real or imported_path.startswith(wt_real + os.sep)):
            return make_result(
                verdict="error",
                reason="isolation",
                baseline_failing=None,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        base_xml = os.path.join(tmp_parent, "baseline.xml")
        base_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-o",
            'addopts=""',
            "-q",
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--continue-on-collection-errors",
            "--junitxml",
            base_xml,
        ] + selection

        try:
            subprocess.run(
                base_cmd,
                cwd=wt_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return make_result(
                verdict="timeout",
                reason=f"baseline run timed out after {timeout_s}s",
                baseline_failing=None,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        if not os.path.exists(base_xml):
            return make_result(
                verdict="error",
                reason="baseline run could not produce junit XML",
                baseline_failing=None,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        base_fail, base_coll = _parse_junit_xml(base_xml)
        baseline_failing_count = len(base_fail)

        with open(target_full_path, "w", encoding="utf-8") as f:
            f.write(mutated_source)

        mut_xml = os.path.join(tmp_parent, "mutant.xml")
        mut_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-o",
            'addopts=""',
            "-q",
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--continue-on-collection-errors",
            "--junitxml",
            mut_xml,
        ] + selection

        try:
            subprocess.run(
                mut_cmd,
                cwd=wt_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return make_result(
                verdict="timeout",
                reason=f"mutant run timed out after {timeout_s}s",
                baseline_failing=baseline_failing_count,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        if not os.path.exists(mut_xml):
            return make_result(
                verdict="error",
                reason="mutant run could not produce junit XML",
                baseline_failing=baseline_failing_count,
                mutant_failing=None,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        mut_fail, mut_coll = _parse_junit_xml(mut_xml)
        mutant_failing_count = len(mut_fail)

        with open(target_full_path, "w", encoding="utf-8") as f:
            f.write(original_source)

        candidate_newly_failing = mut_fail - base_fail

        if not candidate_newly_failing:
            return make_result(
                verdict="survived",
                reason=None,
                baseline_failing=baseline_failing_count,
                mutant_failing=mutant_failing_count,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        selectors = [
            _node_id_to_selector(nid, wt_dir) for nid in sorted(candidate_newly_failing)
        ]
        rerun_xml = os.path.join(tmp_parent, "rerun.xml")
        rerun_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-o",
            'addopts=""',
            "-q",
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--continue-on-collection-errors",
            "--junitxml",
            rerun_xml,
        ] + selectors

        try:
            subprocess.run(
                rerun_cmd,
                cwd=wt_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return make_result(
                verdict="timeout",
                reason=f"rerun confirmation timed out after {timeout_s}s",
                baseline_failing=baseline_failing_count,
                mutant_failing=mutant_failing_count,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        if not os.path.exists(rerun_xml):
            return make_result(
                verdict="error",
                reason="rerun confirmation could not produce junit XML",
                baseline_failing=baseline_failing_count,
                mutant_failing=mutant_failing_count,
                newly_failing=[],
                newly_failing_total=0,
                flaky=[],
                extra_tests_overwrote=extra_tests_overwrote,
            )

        rerun_fail, _ = _parse_junit_xml(rerun_xml)
        flaky_set = candidate_newly_failing & rerun_fail
        confirmed = candidate_newly_failing - flaky_set
        flaky_sorted = sorted(flaky_set)
        confirmed_sorted = sorted(confirmed)
        newly_failing_slice = confirmed_sorted[:20]
        newly_failing_total = len(confirmed_sorted)

        if newly_failing_total == 0:
            verdict = "survived"
        elif all(nid in mut_coll for nid in confirmed):
            verdict = "killed-by-import"
        else:
            verdict = "killed"

        return make_result(
            verdict=verdict,
            reason=None,
            baseline_failing=baseline_failing_count,
            mutant_failing=mutant_failing_count,
            newly_failing=newly_failing_slice,
            newly_failing_total=newly_failing_total,
            flaky=flaky_sorted,
            extra_tests_overwrote=extra_tests_overwrote,
        )

    finally:
        subprocess.run(
            ["git", "-C", repo_root_str, "worktree", "remove", "--force", wt_dir],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", repo_root_str, "worktree", "prune"],
            capture_output=True,
        )
        if os.path.exists(tmp_parent):
            shutil.rmtree(tmp_parent, ignore_errors=True)

        status_after = subprocess.run(
            ["git", "-C", repo_root_str, "status", "--porcelain"],
            capture_output=True,
            text=True,
        ).stdout.splitlines()

        diff_status = sorted(set(status_after) ^ set(status_before))
        if diff_status:
            sys.stderr.write(
                f"Warning: checkout status changed during probe: {diff_status}\n"
            )
            checkout_status_changed.extend(diff_status)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for mutation_probe.py."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Worktree-isolated mutation probe",
        prog="mutation_probe.py",
    )
    parser.add_argument(
        "target",
        help="Target function as <path.py>::<qualname>",
    )
    parser.add_argument(
        "--op",
        required=True,
        choices=OPERATORS,
        help="Mutation operator",
    )
    parser.add_argument(
        "--extra-test",
        action="append",
        default=[],
        dest="extra_tests",
        metavar="COMMIT:PATH",
        help="Extra test blob to read from COMMIT^:PATH",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        dest="timeout_s",
        help="Timeout in seconds for each pytest run (default: 1800)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Pytest arguments to select tests (after --)",
    )

    argv_list = list(argv)
    if "--" in argv_list:
        sep_idx = argv_list.index("--")
        pre_sep = argv_list[:sep_idx]
        post_sep = argv_list[sep_idx + 1 :]
    else:
        pre_sep = argv_list
        post_sep = []

    if hasattr(parser, "parse_intermixed_args"):
        args = parser.parse_intermixed_args(pre_sep)
    else:
        args = parser.parse_args(pre_sep)

    if "::" not in args.target:
        parser.error(f"target must be <path.py>::<qualname>, got: {args.target}")
    rel_path, _ = args.target.split("::", 1)
    if not rel_path.endswith(".py"):
        parser.error(f"target file must end in .py, got: {rel_path}")

    try:
        rev_res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_root = rev_res.stdout.strip()
    except Exception:
        parser.error("must be run inside a git repository")

    combined_pytest_args = list(args.pytest_args) + post_sep
    pytest_args = combined_pytest_args if combined_pytest_args else None

    result = probe(
        repo_root=repo_root,
        target=args.target,
        operator=args.op,
        pytest_args=pytest_args,
        extra_tests=args.extra_tests,
        timeout_s=args.timeout_s,
    )

    if args.format == "json":
        print(json.dumps(result.to_dict(), sort_keys=True))
    else:
        lines = [
            f"head: {result.head}",
            f"target: {result.target}",
            f"operator: {result.operator}",
            f"selection: {' '.join(result.selection)}",
            f"verdict: {result.verdict}",
        ]
        if result.reason:
            lines.append(f"reason: {result.reason}")
        lines.append(f"baseline_failing: {result.baseline_failing}")
        lines.append(f"mutant_failing: {result.mutant_failing}")
        lines.append(f"newly_failing ({result.newly_failing_total} total):")
        for nf in result.newly_failing:
            lines.append(f"  {nf}")
        if result.flaky:
            lines.append(f"flaky ({len(result.flaky)} total):")
            for fl in result.flaky:
                lines.append(f"  {fl}")
        if result.extra_tests_overwrote:
            lines.append(
                f"extra_tests_overwrote: {', '.join(result.extra_tests_overwrote)}"
            )
        lines.append(f"wall_s: {result.wall_s}")
        if result.checkout_status_changed:
            lines.append(f"checkout_status_changed: {result.checkout_status_changed}")
        print("\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
