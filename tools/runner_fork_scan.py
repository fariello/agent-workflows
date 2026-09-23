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

AND THE CASE EVERY PAIRWISE SECTION ABOVE IS STRUCTURALLY BLIND TO, which is why `--repo-wide`
exists. Each report above compares the two runners against each other and against `runner_shared`,
so a third copy sitting in SOME OTHER module is invisible to all of them: the comparison never looks
there. That blindness is MEASURED HISTORY in this repository rather than a hypothetical. The
`rununify` orchestrator records it as its F10 -- a one-sided guard over `render_stream` let
`agy_runipd` re-fork `Palette`, `_one_line` and `_strip_ansi`, and let `Heartbeat` actually DRIFT, so
a display fix in the owning module silently never reached `aw agy run`. Its E-03 therefore requires
the single-implementation check to be "AST-level and REPO-WIDE across `agent_workflows/*.py`, not a
pairwise check of the two runners". `--repo-wide` is that sweep, and plan `40it5e` E-01 consumes it.

READ THE REPO-WIDE SECTION'S OWN WARNING BEFORE ACTING ON IT. A name collision is NOT a re-fork, and
by NAME this sweep "finds" nine that do not exist: nine different modules define a `main`, and
`build_parser`, `terminate_process` and `validate_manifest` collide the same way. `tvnq50` records an
executor making exactly that error. So the sweep classifies by NORMALIZED BODY and reports a
CO-DEFINED-ELSEWHERE symbol with its similarity, never as a verdict.

USAGE

    python3 tools/runner_fork_scan.py                  # the census
    python3 tools/runner_fork_scan.py --closure        # + per-symbol module-level closure
    python3 tools/runner_fork_scan.py --hazards        # + __file__ / host-token scan
    python3 tools/runner_fork_scan.py --triples        # + symbols ALSO defined in runner_shared
    python3 tools/runner_fork_scan.py --repo-wide      # + the sweep over ALL agent_workflows/*.py
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
import difflib
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


def references_module(node: ast.stmt, module: str) -> bool:
    """Does `node` reach `module` ANYWHERE in its body, by attribute or by import?

    THE BROAD QUESTION, deliberately, and it is a DIFFERENT question from
    :func:`is_pure_delegation`'s. That predicate asks "is this body NOTHING BUT a delegation?"; this
    one asks "does this body delegate AT ALL?". The two disagree on a body that computes host values
    and then calls one shared helper, and that disagreement is the whole residue question `gqo6if`
    exists to settle, so both are reported rather than one standing in for the other.

    Matches an `ast.Attribute` on the module name (`runner_shared.x`), a `from ... import` naming it,
    and a bare `ast.Name` load of it, because a lazily-imported delegation (`from
    agent_workflows.oc_runipd import f as _shared; return _shared(...)`) is a real delegation that an
    attribute-only scan cannot see. That form is not hypothetical: it is how `agy_runipd` binds
    `route_recovery_turn`, `classify_recovery_disposition` and `build_verify_and_continue_notice`.
    """
    for sub in ast.walk(node):
        if (
            isinstance(sub, ast.Attribute)
            and isinstance(sub.value, ast.Name)
            and sub.value.id == module
        ):
            return True
        if isinstance(sub, ast.ImportFrom) and (sub.module or "").endswith(module):
            return True
        if isinstance(sub, ast.Name) and sub.id == module:
            return True
    return False


def residue_class(oc_node: ast.stmt, agy_node: ast.stmt) -> str:
    """Which delegation class a co-defined symbol is in: the STRICT test, per side.

    Three values, and the middle one is the finding rather than a rounding error:

      * ``BOTH-DELEGATE``     - each side reaches `runner_shared` somewhere. There may still be
        substantial per-host body around that call, which is why this is NOT the same as "shared".
      * ``ONE-SIDE-DELEGATES``- exactly one side does. The other carries a real body.
      * ``NEITHER-DELEGATES`` - no side does. This is the STRICT residue, and it is the class a
        symbol must LEAVE to count as shared.
    """
    oc_delegates = references_module(oc_node, SHARED)
    agy_delegates = references_module(agy_node, SHARED)
    if oc_delegates and agy_delegates:
        return "BOTH-DELEGATE"
    if oc_delegates or agy_delegates:
        return "ONE-SIDE-DELEGATES"
    return "NEITHER-DELEGATES"


def normalized_similarity(oc_node: ast.stmt, agy_node: ast.stmt) -> float:
    """`difflib` ratio of the two normalized bodies AFTER host tokens are erased.

    Normalizing the host tokens first is what makes the number mean "how much of this is the same
    logic" rather than "how differently are the two hosts spelled". Without it, two byte-identical
    bodies that merely name their own host score below 1.0 and look like a real divergence.

    A SIMILARITY IS NOT A DECISION, and this scanner deliberately does not threshold it. `gqo6if`
    E-02 records the measured counter-examples in both directions: a near-1.0 pair can be a genuine
    per-host capability (nothing forces duplication to be spelled differently), and a low-scoring
    pair can be pure duplication one side has merely reformatted.
    """
    return difflib.SequenceMatcher(
        None,
        _erase_host_tokens(normalize(oc_node)),
        _erase_host_tokens(normalize(agy_node)),
    ).ratio()


def _erase_host_tokens(text: str) -> str:
    """Replace every host token with one placeholder, on word boundaries.

    Word-bounded for the reason `_mentions` gives: a substring replacement of the bare `oc` would
    mangle most English words and make the similarity figure meaningless.
    """
    for token in HOST_TOKENS:
        text = re.sub(rf"\b{re.escape(token)}\b", "HOST", text)
    return text


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


def repo_wide_sweep() -> dict[str, Any]:
    """Every runner symbol against ALL of `agent_workflows/*.py`: the class (d) question.

    THE QUESTION THIS ANSWERS, and it is a DIFFERENT one from every section above. Those compare the
    two runners with each other and with `runner_shared`, which cannot see a third copy living in
    another module; `rununify` F10 records that blindness costing a real drift (`Heartbeat` fixed in
    `render_stream` and silently not reaching `aw agy run`). So this walks the whole package.

    IT REPORTS, IT DOES NOT RULE, and the distinction is load-bearing because the naive form of this
    sweep is actively misleading. Matching on NAME alone reports eleven re-forks of which nine are
    mere collisions (nine modules define a `main`), and `tvnq50` records the method correction after an
    executor hit exactly that. So each co-definition carries the normalized-body similarity and the
    identity verdict, and the caller reads them.

    Keys: `runner_symbols` (every top-level symbol in either runner), `single_definition` (those
    defined in NO OTHER module), `single_definition_repo_wide` (those defined in EXACTLY ONE module
    counting the runners, which is the only class that is provably one implementation), and
    `co_defined_elsewhere` mapping symbol -> the per-module records, each carrying `identical` and
    `similarity`.

    THE TWO SINGLE-DEFINITION KEYS ARE NOT THE SAME QUESTION and conflating them would restate this
    Set's original error in a new place. A symbol defined in BOTH runners and nowhere else has NO
    third copy, and it is still forked; only `single_definition_repo_wide` means one body exists.
    """
    modules: dict[str, dict[str, ast.stmt]] = {}
    for path in sorted(package_dir().glob("*.py")):
        try:
            modules[path.stem] = top_level_defs(
                ast.parse(path.read_text(encoding="utf-8"))
            )
        except (
            SyntaxError
        ):  # pragma: no cover - a broken module is not this tool's business
            continue

    runner_symbols = sorted(set(modules.get(OC, {})) | set(modules.get(AGY, {})))
    co_defined: dict[str, list[dict[str, Any]]] = {}
    for name in runner_symbols:
        # The runner body to compare against. Prefer oc, which the maintainer's 2026-09-14 ruling
        # makes the preferred version, and fall back to agy for an agy-only symbol.
        host_node = modules.get(OC, {}).get(name) or modules[AGY][name]
        host_norm = normalize(host_node)
        elsewhere: list[dict[str, Any]] = []
        for mod, defs in modules.items():
            if mod in (OC, AGY) or name not in defs:
                continue
            other = defs[name]
            elsewhere.append(
                {
                    "module": mod,
                    "identical": normalize(other) == host_norm,
                    "similarity": round(
                        difflib.SequenceMatcher(
                            None,
                            _erase_host_tokens(host_norm),
                            _erase_host_tokens(normalize(other)),
                        ).ratio(),
                        3,
                    ),
                    "lines": line_metrics(other),
                }
            )
        if elsewhere:
            co_defined[name] = sorted(elsewhere, key=lambda rec: rec["module"])

    return {
        "test": (
            "REPO-WIDE: every top-level symbol of either runner compared, by NORMALIZED BODY, "
            "against every module in agent_workflows/. A NAME collision is NOT a re-fork"
        ),
        "modules_scanned": len(modules),
        "runner_symbols": runner_symbols,
        "single_definition": sorted(n for n in runner_symbols if n not in co_defined),
        "single_definition_repo_wide": sorted(
            n
            for n in runner_symbols
            if n not in co_defined
            and not (n in modules.get(OC, {}) and n in modules.get(AGY, {}))
        ),
        "co_defined_elsewhere": co_defined,
        # The subset that is NOT explained by the sanctioned `runner_shared` extraction, i.e. the
        # class (d) candidate set a reader must actually judge.
        "outside_shared": sorted(
            name
            for name, recs in co_defined.items()
            if any(rec["module"] != SHARED for rec in recs)
        ),
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
            # `gqo6if` E-01: the two defensible residue tests, reported SEPARATELY with the test that
            # produced each named in the output, because the authoring measurement of this Set quoted
            # one number without its test and it reproduced under neither.
            "residue_class": residue_class(oc_node, agy_node),
            "strict_residue": residue_class(oc_node, agy_node) == "NEITHER-DELEGATES",
            "loose_residue": not wrapper,
            "similarity": round(normalized_similarity(oc_node, agy_node), 3),
            "agy_lines": line_metrics(agy_node),
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
        # `gqo6if` E-01/V-01: the two tests stated IN THE OUTPUT, so a figure can never be quoted
        # without the test that produced it, and the LINE METRIC named beside them for the same
        # reason (three metrics circulate here and differ by more than 2x on one symbol).
        "strict_test": (
            "STRICT: neither side references `runner_shared` ANYWHERE in its body "
            "(residue_class == NEITHER-DELEGATES)"
        ),
        "loose_test": (
            "LOOSE: neither side is a single-statement `runner_shared` delegation "
            "(i.e. not a sanctioned thin wrapper)"
        ),
        "line_metric": "ast.unparse lines with docstrings stripped, measured on the AGY side",
        "strict_residue": sorted(n for n, r in records.items() if r["strict_residue"]),
        "loose_residue": sorted(n for n, r in records.items() if r["loose_residue"]),
        "strict_residue_agy_lines": sum(
            r["agy_lines"]["unparse"] for r in records.values() if r["strict_residue"]
        ),
        "loose_residue_agy_lines": sum(
            r["agy_lines"]["unparse"] for r in records.values() if r["loose_residue"]
        ),
        "by_residue_class": {
            cls: sorted(n for n, r in records.items() if r["residue_class"] == cls)
            for cls in ("BOTH-DELEGATE", "ONE-SIDE-DELEGATES", "NEITHER-DELEGATES")
        },
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
        # The repo-wide sweep travels WITH the census rather than beside it, so `--json` carries the
        # class (d) answer too and a consumer cannot get the pairwise numbers without the sweep that
        # bounds them (`rununify` E-03 requires the check be repo-wide, not pairwise).
        "repo_wide": repo_wide_sweep(),
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


def render_repo_wide(data: dict[str, Any]) -> list[str]:
    """The class (d) section: what the pairwise sections above cannot see.

    Ordered so the REASSURING number comes first and the JUDGEMENT SET second, because the set is
    what a reader must act on and it is small enough to print whole.
    """
    sweep = data["repo_wide"]
    out = [
        "REPO-WIDE SWEEP (the class (d) question the pairwise sections cannot answer)"
    ]
    out.append(f"  {sweep['test']}")
    out.append(f"  modules scanned              : {sweep['modules_scanned']}")
    out.append(f"  runner symbols               : {len(sweep['runner_symbols'])}")
    out.append(
        f"  defined in NO OTHER module   : {len(sweep['single_definition'])} "
        "(no THIRD copy; says nothing about the two-runner fork, which is the pairwise sections' "
        "question)"
    )
    out.append(
        f"  ONE definition repo-wide     : {len(sweep['single_definition_repo_wide'])} "
        "(defined in exactly one module, runners included: the only class that is provably "
        "single-implementation)"
    )
    out.append(
        f"  co-defined in another module : {len(sweep['co_defined_elsewhere'])} "
        f"(of which {len(sweep['outside_shared'])} outside `runner_shared`)"
    )
    out.append("")
    out.append(
        "  CO-DEFINED OUTSIDE runner_shared -- READ, DO NOT COUNT: a NAME collision is not a "
        "re-fork, and by name this sweep 'finds' nine that do not exist"
    )
    if not sweep["outside_shared"]:
        out.append("    none")
    for name in sweep["outside_shared"]:
        for rec in sweep["co_defined_elsewhere"][name]:
            if rec["module"] == SHARED:
                continue
            verdict = (
                "AST-IDENTICAL -> a real re-fork"
                if rec["identical"]
                else "different body"
            )
            out.append(
                f"    {name:34s} also in {rec['module']:22s} "
                f"sim={rec['similarity']:6.3f}  {verdict}"
            )
    out.append("")
    return out


def render(
    data: dict[str, Any],
    *,
    closure: bool,
    hazards: bool,
    triples: bool,
    repo_wide: bool = False,
) -> str:
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
    # `gqo6if` E-01: THE RESIDUE, under BOTH tests, each printed WITH ITS DEFINITION and the line
    # metric named. Never print one of these counts alone: the two disagree by design, and the
    # disagreement is the per-symbol question, not a rounding error to pick a winner from.
    out.append("RESIDUE, UNDER TWO TESTS (both reported; neither is 'the' number)")
    out.append(f"  line metric: {data['line_metric']}")
    out.append(f"  {data['strict_test']}")
    out.append(
        f"    -> {len(data['strict_residue'])} symbols, "
        f"{data['strict_residue_agy_lines']} lines"
    )
    out.append(f"  {data['loose_test']}")
    out.append(
        f"    -> {len(data['loose_residue'])} symbols, "
        f"{data['loose_residue_agy_lines']} lines"
    )
    out.append("")
    out.append("  by delegation class:")
    for cls, names in data["by_residue_class"].items():
        out.append(f"    {cls:20s} {len(names):3d}  {', '.join(names) or '-'}")
    out.append("")
    out.append(
        "  PER-SYMBOL (loose residue only; similarity is host-token-normalised and is NOT a decision)"
    )
    out.append(
        f"    {'symbol':42s} {'class':20s} {'S':>2s} {'oc':>4s} {'agy':>4s} {'sim':>6s}"
    )
    for name in sorted(
        data["loose_residue"], key=lambda n: (-data["symbols"][n]["similarity"], n)
    ):
        rec = data["symbols"][name]
        out.append(
            f"    {name:42s} {rec['residue_class']:20s} "
            f"{'Y' if rec['strict_residue'] else '.':>2s} "
            f"{rec['lines']['unparse']:4d} {rec['agy_lines']['unparse']:4d} "
            f"{rec['similarity']:6.3f}" + ("  LARGE" if rec["large_function"] else "")
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

    if repo_wide:
        out.extend(render_repo_wide(data))

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
    parser.add_argument(
        "--repo-wide",
        action="store_true",
        help=(
            "sweep every runner symbol against ALL of agent_workflows/*.py. REQUIRED to answer the "
            "single-implementation question: every other section is pairwise and cannot see a third "
            "copy in another module (`rununify` F10 records that blindness costing a real drift)."
        ),
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
            repo_wide=args.repo_wide or args.all,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
