#!/usr/bin/env python3
"""THE COMMITTED LIFT-DRIFT SCANNER: audit lifted symbols against pre-lift host bodies.

Reuses primitives from tools/runner_fork_scan.py to compare pre-lift host bodies at <commit>^
against the HEAD shared body in agent_workflows/runner_shared.py, check resolved-call arity
within runner_shared, and verify deliberate-stop handler verbs in execute_item_core.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import pathlib
import re
import subprocess
import sys

# Import shared primitives from runner_fork_scan by path
TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import runner_fork_scan  # noqa: E402


def package_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent / "agent_workflows"


def normalize(node: ast.stmt) -> str:
    return runner_fork_scan.normalize(node)


def top_level_defs(tree: ast.Module) -> dict[str, ast.stmt]:
    return runner_fork_scan.top_level_defs(tree)


def free_names(node: ast.stmt) -> set[str]:
    return runner_fork_scan.free_names(node)


def is_pure_delegation(node: ast.stmt) -> bool:
    return runner_fork_scan.is_pure_delegation(node)


def _erase_qualifiers(text: str) -> str:
    """Erase oc_runipd, agy_runipd, and runner_shared module qualifiers."""
    return re.sub(r"\b(oc_runipd|agy_runipd|runner_shared)\.", "", text)


def get_git_file_content(commit: str, rel_path: str) -> str | None:
    """Get file content from git at a given revision, or None if absent."""
    try:
        res = subprocess.run(
            ["git", "show", f"{commit}:{rel_path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout
    except subprocess.CalledProcessError:
        return None


def get_signature_requirements(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[list[str], list[str], list[str]]:
    """Return (required_pos_args, all_pos_args, required_kwonly_args)."""
    pos_args = [a.arg for a in node.args.posonlyargs + node.args.args]
    num_defaults = len(node.args.defaults)
    req_pos = pos_args[: len(pos_args) - num_defaults]
    req_kwonly = [
        a.arg for a, d in zip(node.args.kwonlyargs, node.args.kw_defaults) if d is None
    ]
    return req_pos, pos_args, req_kwonly


def find_local_bindings(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Find all names locally bound inside a function definition."""
    bound: set[str] = set()
    for arg in (
        list(node.args.args) + list(node.args.kwonlyargs) + list(node.args.posonlyargs)
    ):
        bound.add(arg.arg)
    if node.args.vararg:
        bound.add(node.args.vararg.arg)
    if node.args.kwarg:
        bound.add(node.args.kwarg.arg)
    for sub in ast.walk(node):
        if sub is node:
            continue
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            bound.add(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(sub.name)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for alias in sub.names:
                bound.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            bound.add(sub.name)
    return bound


def scan_arity_violations(
    tree: ast.Module, exclude: set[str] | None = None
) -> list[tuple[str, str, list[str], int]]:
    """Check bare Name calls in runner_shared top-level defs against top-level signatures.

    Returns list of (caller_name, callee_name, missing_parameters, lineno).
    """
    excluded = exclude or set()
    funcs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {
        n.name: n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    sigs = {k: get_signature_requirements(v) for k, v in funcs.items()}

    violations: list[tuple[str, str, list[str], int]] = []
    for fname, fnode in funcs.items():
        if fname in excluded:
            continue
        bound = find_local_bindings(fnode)
        for sub in ast.walk(fnode):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                tname = sub.func.id
                if tname in funcs and tname not in bound and tname not in excluded:
                    # Skip calls using *args or **kwargs
                    if any(isinstance(a, ast.Starred) for a in sub.args) or any(
                        kw.arg is None for kw in sub.keywords
                    ):
                        continue
                    req_pos, pos_args, req_kwonly = sigs[tname]
                    supplied_pos = len(sub.args)
                    supplied_kw = {kw.arg for kw in sub.keywords if kw.arg is not None}
                    missing = []
                    for i, p in enumerate(req_pos):
                        if i >= supplied_pos and p not in supplied_kw:
                            missing.append(p)
                    for k in req_kwonly:
                        if k not in supplied_kw:
                            missing.append(k)
                    if missing:
                        violations.append(
                            (
                                fname,
                                tname,
                                sorted(missing),
                                getattr(sub, "lineno", 0),
                            )
                        )
    return violations


def extract_handlers(
    func_node: ast.AST,
) -> dict[tuple[str, str], list[tuple[str, str]]]:
    """Extract except handlers from a function node.

    Returns dict mapping (caught_type, mapped_first_call) -> list of (verb, status_style).
    verb is 'raise' | 'return' | 'fall'.
    status_style is 'via-call' | 'direct' | '-'.
    """
    handlers: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for node in ast.walk(func_node):
        if isinstance(node, ast.Try):
            first_call = "<no-call>"
            is_verify_call = False
            for stmt in node.body:
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.Call):
                        cname = None
                        if isinstance(sub.func, ast.Name):
                            cname = sub.func.id
                        elif isinstance(sub.func, ast.Attribute):
                            cname = sub.func.attr
                        if cname:
                            first_call = cname
                            call_str = ast.unparse(sub)
                            if "v_prompt" in call_str or "spawn_verifier" in call_str:
                                is_verify_call = True
                            break
                if first_call != "<no-call>":
                    break
            if first_call in ("run_opencode", "run_agy_turn", "spawn_executor"):
                first_call = "spawn_verifier" if is_verify_call else "spawn_executor"
            for h in node.handlers:
                caught_type = ast.unparse(h.type) if h.type else "Exception"
                key = (caught_type, first_call)
                verb = "fall"
                if h.body:
                    if isinstance(h.body[-1], ast.Raise):
                        verb = "raise"
                    elif isinstance(h.body[-1], ast.Return):
                        verb = "return"
                style = "-"
                for hstmt in h.body:
                    for sub in ast.walk(hstmt):
                        if isinstance(sub, ast.Assign):
                            for target in sub.targets:
                                if (
                                    isinstance(target, ast.Subscript)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "item"
                                    and isinstance(target.slice, ast.Constant)
                                    and target.slice.value == "status"
                                ):
                                    style = (
                                        "via-call"
                                        if isinstance(sub.value, ast.Call)
                                        else "direct"
                                    )
                                elif isinstance(target, ast.Tuple):
                                    for elt in target.elts:
                                        if (
                                            isinstance(elt, ast.Subscript)
                                            and isinstance(elt.value, ast.Name)
                                            and elt.value.id == "item"
                                            and isinstance(elt.slice, ast.Constant)
                                            and elt.slice.value == "status"
                                        ):
                                            style = (
                                                "via-call"
                                                if isinstance(sub.value, ast.Call)
                                                else "direct"
                                            )
                handlers.setdefault(key, []).append((verb, style))
    return handlers


def get_spawn_path_stop_handlers(
    tree: ast.Module,
) -> dict[str, tuple[str, str]]:
    """Return spawn-path StopNowForce / StopAtCheckpoint handler verbs for execute_item_core."""
    funcs = top_level_defs(tree)
    core = funcs.get("execute_item_core")
    if not core:
        return {}
    handlers = extract_handlers(core)
    out = {}
    for caught_type in ("runner_stop.StopNowForce", "runner_stop.StopAtCheckpoint"):
        key = (caught_type, "spawn_executor")
        if key in handlers and handlers[key]:
            out[caught_type] = handlers[key][0]
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit lifted symbols against pre-lift host bodies and check for drift/defects."
    )
    parser.add_argument(
        "commits",
        nargs="*",
        default=["70a2059f", "12a5c05b"],
        help="Lift commits to audit (default: 70a2059f, 12a5c05b)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        metavar="SYMBOL",
        help="Symbols to exclude from check",
    )
    args = parser.parse_args(argv)
    excluded = set(args.exclude)

    # 1. Enumerate lifted symbols across commits
    lifted_by_commit: dict[str, list[str]] = {}
    all_lifted: list[str] = []
    for commit in args.commits:
        c_content = get_git_file_content(commit, "agent_workflows/runner_shared.py")
        parent_content = get_git_file_content(
            f"{commit}^", "agent_workflows/runner_shared.py"
        )
        if c_content is None:
            continue
        c_defs = set(top_level_defs(ast.parse(c_content)))
        p_defs = (
            set(top_level_defs(ast.parse(parent_content))) if parent_content else set()
        )
        new_defs = sorted(c_defs - p_defs)
        lifted_by_commit[commit] = new_defs
        for s in new_defs:
            if s not in all_lifted:
                all_lifted.append(s)

    head_path = package_dir() / "runner_shared.py"
    head_content = head_path.read_text(encoding="utf-8")
    head_tree = ast.parse(head_content)
    head_defs = top_level_defs(head_tree)

    print("LIFT DRIFT AUDIT")
    print(f"Auditing lift commits: {', '.join(args.commits)}")
    print(f"Excluded symbols: {', '.join(sorted(excluded)) or 'none'}")
    print()

    # 2. Body Diffs
    diff_count = 0
    print("BODY DIFFS (normalized pre-lift host vs HEAD runner_shared)")
    for commit in args.commits:
        oc_content = get_git_file_content(f"{commit}^", "agent_workflows/oc_runipd.py")
        agy_content = get_git_file_content(
            f"{commit}^", "agent_workflows/agy_runipd.py"
        )
        oc_defs = top_level_defs(ast.parse(oc_content)) if oc_content else {}
        agy_defs = top_level_defs(ast.parse(agy_content)) if agy_content else {}

        for sym in lifted_by_commit.get(commit, []):
            if sym in excluded:
                continue
            if sym not in head_defs:
                continue
            head_norm = _erase_qualifiers(normalize(head_defs[sym]))

            # Compare against oc and agy definitions at commit^
            for host_name, host_defs in (
                ("oc_runipd", oc_defs),
                ("agy_runipd", agy_defs),
            ):
                host_sym = (
                    "execute_item"
                    if sym == "execute_item_core" and "execute_item" in host_defs
                    else sym
                )
                if host_sym not in host_defs:
                    continue
                pre_norm = _erase_qualifiers(normalize(host_defs[host_sym]))
                if pre_norm != head_norm:
                    diff_count += 1
                    diff_lines = list(
                        difflib.unified_diff(
                            pre_norm.splitlines(keepends=True),
                            head_norm.splitlines(keepends=True),
                            fromfile=f"pre-lift {commit}^:{host_name}:{host_sym}",
                            tofile=f"HEAD runner_shared:{sym}",
                        )
                    )
                    print(f"--- DIFF: {sym} vs {host_name}:{host_sym} ---")
                    sys.stdout.writelines(diff_lines)
                    print()
    if diff_count == 0:
        print("  no body differences found (modulo erased qualifiers)")
    print()

    # 3. Resolved-Signature Check
    arity_violations = scan_arity_violations(head_tree, exclude=excluded)
    print("RESOLVED-SIGNATURE CHECK (arity violations in runner_shared)")
    for caller, callee, missing, lineno in arity_violations:
        print(f"  {caller} -> {callee}(...) missing {missing} (line {lineno})")
    print(f"arity violations: {len(arity_violations)}")
    print()

    # 4. Handler-Verb Check
    print(
        "HANDLER-VERB CHECK (execute_item_core vs pre-lift execute_item at 70a2059f^)"
    )
    stop_handler_diffs = 0
    if "execute_item_core" in head_defs and "execute_item_core" not in excluded:
        head_handlers = extract_handlers(head_defs["execute_item_core"])
        for host_name in ("oc_runipd", "agy_runipd"):
            host_pre = get_git_file_content(
                "70a2059f^", f"agent_workflows/{host_name}.py"
            )
            if host_pre:
                host_defs = top_level_defs(ast.parse(host_pre))
                if "execute_item" in host_defs:
                    pre_handlers = extract_handlers(host_defs["execute_item"])
                    all_keys = sorted(set(pre_handlers) | set(head_handlers))
                    for key in all_keys:
                        pre_v = pre_handlers.get(key, [])
                        head_v = head_handlers.get(key, [])
                        caught_type, call_name = key
                        is_stop = (
                            "StopNowForce" in caught_type
                            or "StopAtCheckpoint" in caught_type
                        )
                        if is_stop:
                            if set(pre_v) != set(head_v):
                                stop_handler_diffs += 1
                                print(
                                    f"  DIFF {host_name} {caught_type} @ {call_name}: "
                                    f"pre={pre_v} head={head_v}"
                                )
                        elif pre_v != head_v:
                            print(
                                f"  DIFF {host_name} {caught_type} @ {call_name}: "
                                f"pre={pre_v} head={head_v}"
                            )
    print(f"handler verb diffs: {stop_handler_diffs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
