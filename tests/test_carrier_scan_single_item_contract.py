"""Tests enforcing the single-item-only contract for per-item carrier scanners (IPD jpn6hy).

SCOPE: agent_workflows/ AND OVER THAT DIRECTORY ONLY.
This scope is a load-bearing architectural requirement, not an incidental boundary.
Pointing this AST analyzer at tests/ flags two legitimate calls in
tests/test_check_engine_release_gate.py (lines 1023 and 1217), where a sentinel-handling
test deliberately loops over the sentinel values ('-', 'none', 'unresolved') and asks
find_from_backlog_artifacts about each against a synthetic temporary repository to assert
sentinel absence. That is correct test code (three cheap calls on a synthetic two-file repo),
so widening this guard to tests/ turns the suite red with only bad remedies: an allowlist
or degrading a valid test to satisfy a guard about production call shapes.

KNOWN HOLE (F-06):
Rebinding a loop variable to a temporary (e.g. `tmp = i` followed by
`find_from_backlog_artifacts(repo, tmp)`) evades this analyzer. The guard is syntactic
and does no dataflow analysis. This trade-off is deliberate: the direct loop variable
and comprehension bindings are the shapes that have bitten the repository in practice,
while tracking arbitrary dataflow would add complex analysis machinery without practical
gain.

NOTE: Do not add wall-clock timing assertions to this file; timing thresholds are flaky
across different machines and execution environments.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, NamedTuple, Set, Tuple


TARGET_FUNCTIONS: Set[str] = {
    "find_from_backlog_plans",
    "find_from_backlog_specs",
    "find_from_backlog_artifacts",
}


class CallSiteViolation(NamedTuple):
    file_path: str
    lineno: int
    func_name: str
    offending_names: Set[str]

    def render(self) -> str:
        names_str = ", ".join(sorted(self.offending_names))
        return f"{self.file_path}:{self.lineno}: call to {self.func_name} uses loop-derived variable(s): {names_str}"


def attach_parents(tree: ast.AST) -> None:
    """Attach .parent reference to every child node in an AST."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent


def extract_target_names(target_node: ast.AST) -> Set[str]:
    """Extract all variable names bound by a target (Name, Tuple, List, etc.)."""
    names: Set[str] = set()
    for node in ast.walk(target_node):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def extract_arg_names(call_node: ast.Call) -> Set[str]:
    """Extract all variable names appearing in args or keywords of a Call."""
    names: Set[str] = set()
    for arg in call_node.args:
        for node in ast.walk(arg):
            if isinstance(node, ast.Name):
                names.add(node.id)
    for kw in call_node.keywords:
        for node in ast.walk(kw.value):
            if isinstance(node, ast.Name):
                names.add(node.id)
    return names


def get_enclosing_loop_bound_names(call_node: ast.Call) -> Set[str]:
    """Collect names bound by every enclosing loop or generator target.

    Crucially, calls in the `iter` position of a `for`/`async for` loop or comprehension
    are NOT considered inside the loop body, because `iter` is evaluated before any
    loop target variables are bound. Exclude `iter` expressions by comparing node
    identity while climbing upward.
    """
    bound_names: Set[str] = set()
    curr: ast.AST = call_node
    while hasattr(curr, "parent"):
        parent = curr.parent
        if isinstance(parent, (ast.For, ast.AsyncFor)):
            # If curr is in parent.iter, it evaluates before loop targets are bound
            if curr is not parent.iter:
                bound_names.update(extract_target_names(parent.target))
        elif isinstance(parent, ast.comprehension):
            # If curr is in comprehension.iter, it evaluates outside target binding
            if curr is not parent.iter:
                bound_names.update(extract_target_names(parent.target))
        elif isinstance(parent, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            if curr is parent.elt:
                for gen in parent.generators:
                    bound_names.update(extract_target_names(gen.target))
            elif curr in parent.generators:
                idx = parent.generators.index(curr)
                for gen in parent.generators[:idx]:
                    bound_names.update(extract_target_names(gen.target))
        elif isinstance(parent, ast.DictComp):
            if curr is parent.key or curr is parent.value:
                for gen in parent.generators:
                    bound_names.update(extract_target_names(gen.target))
            elif curr in parent.generators:
                idx = parent.generators.index(curr)
                for gen in parent.generators[:idx]:
                    bound_names.update(extract_target_names(gen.target))
        curr = parent
    return bound_names


def inspect_ast_for_carrier_calls(
    tree: ast.AST, filename: str = "<unknown>"
) -> Tuple[
    List[CallSiteViolation], List[Tuple[str, int, str, Set[str], Set[str], Set[str]]]
]:
    """Inspect AST for carrier scanner calls, returning (violations, inspected_calls)."""
    attach_parents(tree)
    violations: List[CallSiteViolation] = []
    inspected_calls: List[Tuple[str, int, str, Set[str], Set[str], Set[str]]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name) and node.func.id in TARGET_FUNCTIONS:
                func_name = node.func.id
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in TARGET_FUNCTIONS
            ):
                func_name = node.func.attr

            if func_name:
                bound = get_enclosing_loop_bound_names(node)
                args = extract_arg_names(node)
                intersect = bound.intersection(args)
                inspected_calls.append(
                    (filename, node.lineno, func_name, args, bound, intersect)
                )
                if intersect:
                    violations.append(
                        CallSiteViolation(
                            file_path=filename,
                            lineno=node.lineno,
                            func_name=func_name,
                            offending_names=intersect,
                        )
                    )
    return violations, inspected_calls


def scan_source_for_contract_violations(
    source: str, filename: str = "<string>"
) -> List[CallSiteViolation]:
    """Parse python source and return any single-item carrier contract violations."""
    tree = ast.parse(source, filename=filename)
    violations, _ = inspect_ast_for_carrier_calls(tree, filename=filename)
    return violations


def test_carrier_scan_single_item_contract_in_package() -> None:
    """Scan agent_workflows/ for any calls passing loop-derived variables to carrier scanners."""
    repo_root = Path(__file__).resolve().parent.parent
    package_dir = repo_root / "agent_workflows"
    assert package_dir.is_dir(), f"agent_workflows directory not found at {package_dir}"

    all_violations: List[CallSiteViolation] = []
    all_inspected_calls: List[Tuple[str, int, str, Set[str], Set[str], Set[str]]] = []

    for py_path in sorted(package_dir.rglob("*.py")):
        content = py_path.read_text(encoding="utf-8")
        rel_path = str(py_path.relative_to(repo_root))
        tree = ast.parse(content, filename=rel_path)
        violations, calls = inspect_ast_for_carrier_calls(tree, filename=rel_path)
        all_violations.extend(violations)
        all_inspected_calls.extend(calls)

    assert not all_violations, (
        f"Found {len(all_violations)} carrier scan single-item contract violation(s):\n"
        + "\n".join(v.render() for v in all_violations)
    )

    # Prove the scan is non-vacuous by checking that the 4 known call sites exist
    assert (
        len(all_inspected_calls) >= 4
    ), f"Expected at least 4 carrier scan calls in agent_workflows/, found {len(all_inspected_calls)}"

    call_funcs = {c[2] for c in all_inspected_calls}
    assert "find_from_backlog_plans" in call_funcs
    assert "find_from_backlog_specs" in call_funcs
    assert "find_from_backlog_artifacts" in call_funcs


# ======================================================================================
# Positive Fixtures (prove the analyzer flags all 5 quadratic spellings on source strings)
# ======================================================================================


def test_guard_flags_direct_loop_variable() -> None:
    """Positive fixture 1: direct loop variable passed to scanner."""
    src = """
for i in items:
    find_from_backlog_artifacts(repo, i)
"""
    violations = scan_source_for_contract_violations(src)
    assert len(violations) == 1
    assert violations[0].offending_names == {"i"}
    assert violations[0].func_name == "find_from_backlog_artifacts"


def test_guard_flags_dict_comprehension() -> None:
    """Positive fixture 2: dict comprehension calling scanner per item."""
    src = """
carriers = {i: find_from_backlog_artifacts(repo, i) for i in items}
"""
    violations = scan_source_for_contract_violations(src)
    assert len(violations) == 1
    assert violations[0].offending_names == {"i"}


def test_guard_flags_attribute_of_loop_variable() -> None:
    """Positive fixture 3: attribute of loop variable (`it.id`) passed to scanner."""
    src = """
for it in items:
    find_from_backlog_artifacts(repo, it.id)
"""
    violations = scan_source_for_contract_violations(src)
    assert len(violations) == 1
    assert violations[0].offending_names == {"it"}


def test_guard_flags_nested_loop_inner_variable() -> None:
    """Positive fixture 4: nested loop's inner variable passed to scanner."""
    src = """
for x in outer:
    for y in inner:
        find_from_backlog_artifacts(repo, y)
"""
    violations = scan_source_for_contract_violations(src)
    assert len(violations) == 1
    assert violations[0].offending_names == {"y"}


def test_guard_flags_keyword_argument_spelling() -> None:
    """Positive fixture 5: loop variable passed via keyword argument `item_id6=i`."""
    src = """
for i in items:
    find_from_backlog_artifacts(repo, item_id6=i)
"""
    violations = scan_source_for_contract_violations(src)
    assert len(violations) == 1
    assert violations[0].offending_names == {"i"}


# ======================================================================================
# Negative Fixtures (prove the analyzer does NOT flag legitimate single-item shapes)
# ======================================================================================


def test_guard_silent_on_bare_single_item_calls() -> None:
    """Negative fixture 1: bare single-item calls with literal or parameter."""
    src = """
# Constant literal
c1 = find_from_backlog_artifacts(repo, "abc123")
# Variable passed in as parameter
c2 = find_from_backlog_plans(repo, item_id6)
# Attribute call spelling
c3 = _ce.find_from_backlog_specs(repo, item_id6)
"""
    violations = scan_source_for_contract_violations(src)
    assert len(violations) == 0


def test_guard_silent_on_iter_position_shapes() -> None:
    """Negative fixture 2: calls in `iter` position of loops or comprehensions."""
    src = """
# For loop iter position (evaluate_blocking_close shape)
for p, br in find_from_backlog_artifacts(repo, item_id6):
    pass

# Comprehension iter position with _ce. attribute spelling (evaluate_backlog_close shape)
res = [Path(p) for p, _br in _ce.find_from_backlog_artifacts(repo, item_id6)]
"""
    violations = scan_source_for_contract_violations(src)
    assert len(violations) == 0


# ======================================================================================
# Known Hole Demonstration (F-06)
# ======================================================================================


def test_guard_known_hole_temporary_variable_rebinding() -> None:
    """Known hole: rebinding loop variable to a temporary evades the syntactic guard."""
    src = """
for i in items:
    tmp = i
    find_from_backlog_artifacts(repo, tmp)
"""
    violations = scan_source_for_contract_violations(src)
    # The analyzer is syntactic and does not perform dataflow analysis, so tmp is not flagged.
    assert len(violations) == 0
