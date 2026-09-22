#!/usr/bin/env python3
"""THE COMMITTED RUNNER-FORK SCANNER: census the duplication between the host runners.

WHY THIS FILE EXISTS, stated first because its whole value is reproducibility. Every plan in the
`hostdedup` Set (and `rununify` before it) quotes a fork count, and until this file landed NONE of
those numbers could be re-derived: the authoring scans were ad hoc, run in a shell and thrown away.
The `hostdedup` orchestrator (`a5wdne`) records the consequence as its PR-006 -- "the same AST scan
that produced the baseline" does not exist in-tree -- and its Order 04 acceptance plan (`04vf1h`)
refuses to improvise one, requiring THIS scanner by path. So the contract this file owes its callers
is not "a number" but "the SAME number, next week, from a different machine, by a different agent".

THE METRIC IS STATED, NOT IMPLIED, and that is load-bearing. Three different line metrics circulated
in the Set's plans and they differ by more than 2x on the same symbol set (review of `li44r9`
measured the 17 identical symbols at 583 lines by SPAN, 408 by span-minus-docstrings and 196 by
`ast.unparse`), which is how a plan came to quote "380 lines" that reproduces under no metric at
all. This scanner therefore:

  * reports the SYMBOL COUNT as its headline, because that is what reproduced exactly at every
    measurement in the Set's history, and
  * reports all three LINE metrics side by side, labelled, so a reader can never mistake one for
    another or quote a figure without its metric.

WHAT "IDENTICAL" MEANS HERE, precisely. Two co-defined top-level symbols are IDENTICAL when their
`ast.unparse` normalizations are equal after docstrings are stripped from every nested scope. That
normalization deliberately erases comments, formatting and docstrings, because those are exactly the
differences that do not affect behavior. It equally deliberately does NOT erase NAMES, which is the
scanner's most important limitation and is why `--closure` exists: two bodies that both read
`FULL_AUTO_ACTOR` compare EQUAL while resolving to different strings per host. That is not a
hypothetical, it is the measured state of `set_plan_approved` (`"aw oc run --full-auto"` on oc,
`"aw agy run --full-auto"` on agy), and a lift performed on the identity verdict alone would have
misattributed every Antigravity auto-approval in permanent plan history. READ THE CLOSURE REPORT
BEFORE ACTING ON THE IDENTITY REPORT.

THE THREE-WAY CASE THE IDENTITY REPORT ALONE ALSO HIDES. A symbol can be defined in BOTH runners and
ALSO ALREADY in `runner_shared`, with the hosts ignoring the shared copy. That is strictly worse than
a two-way fork (three bodies to keep in step, and the shared one is dead), so `--triples` names them
rather than letting them hide inside the identical count.

USAGE

    python3 tools/runner_fork_scan.py                  # the census
    python3 tools/runner_fork_scan.py --closure        # + per-symbol module-level closure
    python3 tools/runner_fork_scan.py --hazards        # + __file__ / host-token scan
    python3 tools/runner_fork_scan.py --triples        # + symbols ALSO defined in runner_shared
    python3 tools/runner_fork_scan.py --all            # every section
    python3 tools/runner_fork_scan.py --json           # machine-readable
    python3 tools/runner_fork_scan.py --symbols A B C   # restrict to named symbols

Exit status is 0 whenever the scan completed; this is a MEASURING instrument and not a gate, so it
does not fail on a count it dislikes. The gates that consume it live in the test suite.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import json
import pathlib
import re
import sys
from typing import Any, Iterable

#: The two host runners this scanner compares, and the shared library they should be collapsing into.
OC = "oc_runipd"
AGY = "agy_runipd"
SHARED = "runner_shared"

#: The five large functions deliberately EXCLUDED from the `hostdedup` Set's target population. They
#: carry their own approved plans (`rununify` 07-11) and the Set's completion criterion is the fork
#: count falling "to the five large functions alone", so a reader needs to see them named rather than
#: silently folded into the remainder. Two of them (`initialize_run`, `execute_item`) have since been
#: unified; that is reported rather than assumed, so this tuple is the AUTHORED five and the scan says
#: which of them are still forked.
LARGE_FUNCTIONS = (
    "execute_item",
    "run_queue",
    "initialize_run",
    "build_parser",
    "main",
)

#: Tokens that name ONE host. A shared body containing one of these in CODE is a latent bug (it binds
#: one host's identity for every host); in PROSE it is merely misleading, and the scanner reports the
#: two cases separately because the remedy differs (fix versus re-word).
#:
#: MATCHED ON WORD BOUNDARIES, which is not a nicety: the bare host abbreviations `oc` and `agy` are
#: the spellings a docstring actually uses ("the agy twin"), and a substring search for them matches
#: almost every English word, while omitting them misses real contamination. A review of this Set
#: counted "exactly two" prose mentions and the true figure was three, precisely because the scan it
#: used could not see `agy` standing alone.
HOST_TOKENS = (
    "opencode",
    "OpenCode",
    "oc_runipd",
    "antigravity",
    "Antigravity",
    "agy_runipd",
    "run_opencode",
    "run_agy_turn",
    "agy",
    "oc",
)

_BUILTINS = frozenset(dir(builtins))


def package_dir() -> pathlib.Path:
    """The `agent_workflows` package directory, resolved from THIS file's location.

    Resolved rather than taken from the cwd so the scanner produces the same census whether it is run
    from the repository root, from a lane worktree, or by absolute path from elsewhere.
    """
    return pathlib.Path(__file__).resolve().parent.parent / "agent_workflows"


def _strip_docstrings(node: ast.AST) -> ast.AST:
    """Remove the docstring from every scope in `node`, in place, and return it.

    A scope emptied by the removal gets an explicit `pass`, because an empty body is not
    unparseable-safe and a one-line docstring-only function is a real shape here.
    """
    for scope in ast.walk(node):
        if not isinstance(
            scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
        ):
            continue
        body = scope.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            scope.body = body[1:] or [ast.Pass()]
    return node


def normalize(node: ast.stmt) -> str:
    """The comparison form: `ast.unparse` with every docstring stripped.

    Round-tripped through `ast.parse(ast.unparse(...))` before stripping so the input node is never
    mutated: callers reuse the same tree for the line metrics and for the closure scan, and an
    in-place strip would silently change what those later measurements see.
    """
    return ast.unparse(_strip_docstrings(ast.parse(ast.unparse(node))))


def module_tree(name: str) -> ast.Module:
    return ast.parse((package_dir() / f"{name}.py").read_text(encoding="utf-8"))


def top_level_defs(tree: ast.Module) -> dict[str, ast.stmt]:
    """Every top-level function/class definition, LAST definition winning on a redefinition."""
    out: dict[str, ast.stmt] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = node
    return out


def module_index(tree: ast.Module) -> dict[str, str]:
    """Every name bound at module scope, mapped to how it was bound.

    Conditional and `try`-guarded imports are walked, because an optional import is still a
    module-level binding a lifted body can resolve, and treating it as unresolved would report a
    false closure dependency.
    """
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = "def"
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = "assign"
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = "assign"
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                out[alias.asname or alias.name.split(".")[0]] = "import"
        elif isinstance(node, (ast.If, ast.Try)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.ImportFrom):
                    for alias in sub.names:
                        out.setdefault(alias.asname or alias.name, "import")
                elif isinstance(sub, ast.Import):
                    for alias in sub.names:
                        out.setdefault(
                            alias.asname or alias.name.split(".")[0], "import"
                        )
    return out


def free_names(node: ast.stmt) -> set[str]:
    """Names `node` LOADS without binding anywhere inside itself.

    Subtracts every local binding form a runner body actually uses: assignment targets, parameters
    (positional, keyword-only, positional-only, `*args`, `**kwargs`), nested def/class names, import
    aliases, `except ... as`, `with ... as` (an `ast.Name` store, already covered) and comprehension
    targets (likewise stores). Builtins are removed by the caller, not here, so this function stays a
    pure syntactic question.

    HONEST LIMIT, because a closure scan that overstates is as misleading as one that understates:
    this is a SCOPE-FLATTENING approximation. It does not model Python's scope nesting, so a name
    bound in one nested function and loaded in a sibling is treated as bound. That direction produces
    FALSE NEGATIVES, never false positives, which is the correct bias for a scanner whose output is
    read as "these dependencies definitely exist". Anything it reports IS reached.
    """
    loads: set[str] = set()
    bound: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            if isinstance(sub.ctx, ast.Load):
                loads.add(sub.id)
            else:
                bound.add(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = sub.args
            for arg in list(args.args) + list(args.kwonlyargs) + list(args.posonlyargs):
                bound.add(arg.arg)
            if args.vararg:
                bound.add(args.vararg.arg)
            if args.kwarg:
                bound.add(args.kwarg.arg)
            if sub is not node:
                bound.add(sub.name)
        elif isinstance(sub, ast.ClassDef) and sub is not node:
            bound.add(sub.name)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for alias in sub.names:
                bound.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            bound.add(sub.name)
    return loads - bound - _BUILTINS


def is_pure_delegation(node: ast.stmt) -> bool:
    """The SANCTIONED wrapper shape: one statement calling a single `runner_shared.X(...)`.

    Deliberately the same predicate the four `test_rununify_*` pin files carry, so this scanner's
    "real fork" count and those guards' tables cannot disagree about what a wrapper is. A wrapper is
    NOT duplication: the maintainer's `818uru` OQ-02 ruling makes it the target form, so counting one
    as a fork would overstate the remaining work.
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    body = [
        stmt
        for stmt in node.body
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    if len(body) != 1:
        return False
    stmt = body[0]
    value = stmt.value if isinstance(stmt, (ast.Return, ast.Expr)) else None
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == SHARED
    )


def line_metrics(node: ast.stmt) -> dict[str, int]:
    """All THREE line metrics for one symbol, each named.

    Reported together on purpose. Quoting one of these without saying which is how the Set acquired a
    "380 lines" figure that matches none of them.
    """
    span = (node.end_lineno or node.lineno) - node.lineno + 1
    unparsed = len(normalize(node).splitlines())
    with_docstrings = len(ast.unparse(node).splitlines())
    return {
        "span": span,
        "unparse": unparsed,
        "unparse_with_docstrings": with_docstrings,
    }


def _mentions(text: str, token: str) -> bool:
    """Does `text` name `token` as a WORD rather than as a substring?

    `re.escape` plus `\\b` on both ends, so `oc` matches "the oc twin" and does NOT match "process",
    "block" or "docstring". A substring search here would report a host token in almost every symbol
    and make the hazard report worthless; omitting the bare abbreviations instead under-reports, which
    is the error a review of this Set actually made.
    """
    return re.search(rf"\b{re.escape(token)}\b", text) is not None


def scan_hazards(node: ast.stmt, source_segment: str) -> dict[str, Any]:
    """The two relocation hazards, with a CODE/PROSE split on the second.

    `__file__` is reported as a plain count because it has no benign form here: it evaluates in the
    module where the code is DEFINED, so relocating a body that reads it silently changes its value,
    which is the defect that blocked `orziju`'s relocation (two analytics consumers key on the driver
    path's basename, so a relocated `__file__` makes runs host-unattributable).

    A host TOKEN is split, because the two cases need different remedies. In CODE it binds one host's
    identity into shared logic and must be PARAMETERIZED. In PROSE (a docstring or comment) it is
    merely misleading to the next reader and must be RE-WORDED. Collapsing the two is how a review
    came to report "exactly two" prose mentions when there were three.
    """
    reads_file = sum(
        1
        for sub in ast.walk(node)
        if isinstance(sub, ast.Name) and sub.id == "__file__"
    )
    # CODE tokens: string/bytes constants and attribute/name identifiers, i.e. everything that is not
    # a docstring or a comment. Docstrings are removed first by `normalize`.
    code_only = normalize(node)
    code_tokens = sorted({t for t in HOST_TOKENS if _mentions(code_only, t)})
    prose_tokens = sorted(
        {
            t
            for t in HOST_TOKENS
            if _mentions(source_segment, t) and t not in code_tokens
        }
    )
    return {
        "file_reads": reads_file,
        "host_tokens_in_code": code_tokens,
        "host_tokens_in_prose": prose_tokens,
    }


def census(symbols: Iterable[str] | None = None) -> dict[str, Any]:
    """The whole measurement, as data. Every report below is a rendering of this.

    Returned as a plain dict so `--json` and the human report are provably the same numbers rather
    than two code paths that can drift.
    """
    trees = {name: module_tree(name) for name in (OC, AGY, SHARED)}
    defs = {name: top_level_defs(tree) for name, tree in trees.items()}
    index = {name: module_index(tree) for name, tree in trees.items()}
    sources = {
        name: (package_dir() / f"{name}.py").read_text(encoding="utf-8")
        for name in (OC, AGY, SHARED)
    }

    co_defined = sorted(set(defs[OC]) & set(defs[AGY]))
    if symbols is not None:
        wanted = set(symbols)
        co_defined = [name for name in co_defined if name in wanted]

    records: dict[str, dict[str, Any]] = {}
    for name in co_defined:
        oc_node, agy_node = defs[OC][name], defs[AGY][name]
        oc_norm, agy_norm = normalize(oc_node), normalize(agy_node)
        wrapper = is_pure_delegation(oc_node) and is_pure_delegation(agy_node)
        segment = ast.get_source_segment(sources[OC], oc_node) or ""
        closure = sorted(dep for dep in free_names(oc_node) if dep in index[OC])
        records[name] = {
            "identical": oc_norm == agy_norm,
            "wrapper": wrapper,
            "large_function": name in LARGE_FUNCTIONS,
            "also_in_shared": name in defs[SHARED],
            "shared_identical": (
                normalize(defs[SHARED][name]) == oc_norm
                if name in defs[SHARED]
                else None
            ),
            "lines": line_metrics(oc_node),
            "hazards": scan_hazards(oc_node, segment),
            "closure": [
                {
                    "name": dep,
                    "bound_as": index[OC][dep],
                    "in_shared": dep in index[SHARED],
                    "value_differs": _value_differs(dep, trees),
                }
                for dep in closure
            ],
        }

    identical = [n for n, r in records.items() if r["identical"] and not r["wrapper"]]
    divergent = [
        n for n, r in records.items() if not r["identical"] and not r["wrapper"]
    ]
    wrappers = [n for n, r in records.items() if r["wrapper"]]
    return {
        "metric": (
            "identity: ast.unparse with docstrings stripped from every scope; "
            "a thin runner_shared delegation is NOT counted as a fork"
        ),
        "co_defined": len(records),
        "real_forks": sorted(identical + divergent),
        "identical_forks": sorted(identical),
        "divergent_forks": sorted(divergent),
        "sanctioned_wrappers": sorted(wrappers),
        "large_functions_still_forked": sorted(
            n for n in identical + divergent if n in LARGE_FUNCTIONS
        ),
        # A WRAPPER over a shared definition is the TARGET form, not a triple: of course the symbol
        # is also defined in `runner_shared`; that is the whole point. A triple is the pathological
        # case where BOTH hosts keep a REAL body while a shared definition also exists, so there are
        # three bodies to keep in step and the shared one is dead code.
        "triples": sorted(
            n for n, r in records.items() if r["also_in_shared"] and not r["wrapper"]
        ),
        "symbols": records,
    }


def _value_differs(dep: str, trees: dict[str, ast.Module]) -> bool | None:
    """Does module-level `dep` hold a DIFFERENT literal in the two runners?

    This is the check the identity comparison structurally cannot make, and the reason the closure
    report exists: `ast.unparse` matches on the NAME, so two bodies reading `FULL_AUTO_ACTOR` compare
    equal while resolving to `"aw oc run --full-auto"` and `"aw agy run --full-auto"`.

    Returns None where the question does not apply (the name is not a simple module-level assignment
    in both runners, e.g. a function or an import), True where both assign it and the unparsed values
    differ, False where they agree. None therefore means "not answerable by literal comparison", NOT
    "safe": a dep bound as a `def` may still be a per-host binding wrapper, which is exactly what
    `_detect_driver_command` is, so the report labels that case separately.
    """
    values: dict[str, str] = {}
    for host in (OC, AGY):
        for node in trees[host].body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == dep:
                        values[host] = ast.unparse(node.value)
            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == dep
                and node.value is not None
            ):
                values[host] = ast.unparse(node.value)
    if len(values) != 2:
        return None
    return values[OC] != values[AGY]


def _sum_lines(data: dict[str, Any], names: Iterable[str], metric: str) -> int:
    return sum(data["symbols"][name]["lines"][metric] for name in names)


def render(data: dict[str, Any], *, closure: bool, hazards: bool, triples: bool) -> str:
    out: list[str] = []
    out.append("RUNNER FORK CENSUS")
    out.append(f"  metric: {data['metric']}")
    out.append("")
    out.append(f"  co-defined in both runners : {data['co_defined']}")
    out.append(
        f"  sanctioned thin wrappers   : {len(data['sanctioned_wrappers'])} (NOT forks)"
    )
    out.append(f"  REAL FORKS                 : {len(data['real_forks'])}")
    out.append(f"    byte-identical           : {len(data['identical_forks'])}")
    out.append(f"    divergent                : {len(data['divergent_forks'])}")
    out.append(
        "  large functions still forked: "
        f"{len(data['large_functions_still_forked'])} of {len(LARGE_FUNCTIONS)} "
        f"({', '.join(data['large_functions_still_forked']) or 'none'})"
    )
    out.append("")
    for label, key in (
        ("IDENTICAL FORKS", "identical_forks"),
        ("DIVERGENT FORKS", "divergent_forks"),
    ):
        names = data[key]
        out.append(
            f"{label} ({len(names)}): "
            f"span={_sum_lines(data, names, 'span')} "
            f"unparse={_sum_lines(data, names, 'unparse')} "
            f"unparse+docstrings={_sum_lines(data, names, 'unparse_with_docstrings')}"
        )
        for name in names:
            metrics = data["symbols"][name]["lines"]
            out.append(
                f"    {name:42s} span={metrics['span']:4d} "
                f"unparse={metrics['unparse']:4d} "
                f"unparse+doc={metrics['unparse_with_docstrings']:4d}"
            )
        out.append("")

    if triples:
        out.append(
            "ALSO DEFINED IN runner_shared (a THREE-way fork; the hosts ignore the shared copy):"
        )
        if not data["triples"]:
            out.append("    none")
        for name in data["triples"]:
            same = data["symbols"][name]["shared_identical"]
            out.append(f"    {name:42s} shared copy identical to the hosts': {same}")
        out.append("")

    if hazards:
        out.append("RELOCATION HAZARDS")
        any_hazard = False
        for name in data["real_forks"]:
            haz = data["symbols"][name]["hazards"]
            if (
                haz["file_reads"]
                or haz["host_tokens_in_code"]
                or haz["host_tokens_in_prose"]
            ):
                any_hazard = True
                out.append(f"    {name}")
                if haz["file_reads"]:
                    out.append(f"        __file__ reads      : {haz['file_reads']}")
                if haz["host_tokens_in_code"]:
                    out.append(
                        f"        host tokens in CODE : {', '.join(haz['host_tokens_in_code'])}"
                    )
                if haz["host_tokens_in_prose"]:
                    out.append(
                        f"        host tokens in PROSE: {', '.join(haz['host_tokens_in_prose'])}"
                    )
        if not any_hazard:
            out.append("    none")
        out.append("")

    if closure:
        out.append(
            "MODULE-LEVEL CLOSURE (a dep ABSENT from runner_shared must move or be injected; a dep "
            "whose VALUE differs per host must be carried by descriptor)"
        )
        for name in data["real_forks"]:
            deps = data["symbols"][name]["closure"]
            out.append(f"    {name}")
            if not deps:
                out.append("        (no module-level dependencies)")
            for dep in deps:
                flags = []
                if not dep["in_shared"]:
                    flags.append("ABSENT-FROM-SHARED")
                if dep["value_differs"] is True:
                    flags.append("VALUE-DIFFERS-PER-HOST")
                out.append(
                    f"        {dep['name']:40s} {dep['bound_as']:7s} "
                    f"{' '.join(flags) or 'ok'}"
                )
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Census the duplication between the two host runners. Reports the SYMBOL COUNT as the "
            "headline and all three line metrics side by side, because quoting a line figure "
            "without its metric is how this Set acquired numbers nobody could reproduce."
        )
    )
    parser.add_argument(
        "--closure",
        action="store_true",
        help=(
            "per-symbol module-level closure. READ THIS BEFORE LIFTING: a byte-identical body can "
            "read a module-level name whose VALUE differs per host."
        ),
    )
    parser.add_argument(
        "--hazards",
        action="store_true",
        help="__file__ reads and host tokens, split CODE versus PROSE",
    )
    parser.add_argument(
        "--triples",
        action="store_true",
        help="symbols ALSO defined in runner_shared while both hosts keep their own copy",
    )
    parser.add_argument("--all", action="store_true", help="every section")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--symbols",
        nargs="+",
        metavar="NAME",
        help="restrict the census to these symbols",
    )
    args = parser.parse_args(argv)

    data = census(args.symbols)
    if args.json:
        json.dump(data, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    print(
        render(
            data,
            closure=args.closure or args.all,
            hazards=args.hazards or args.all,
            triples=args.triples or args.all,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
