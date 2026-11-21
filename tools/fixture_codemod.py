#!/usr/bin/env python3
"""Detect, classify, rewrite, and prove equivalence for legacy test fixtures.

Implements IPD ``y3uowx`` (part 1 of ``653ndz``, spec ``4sd62s`` section 6).

This standalone maintenance tool parses Python test modules with ``ast``, locates
legacy fixture string-literal sites matching the F-01 pattern, classifies each
site as either a planned rewrite to ``tests.record_builder.RecordBuilder`` (with
``text_only=True``) or a refusal with one of seven reason codes and a disposition
(``hand`` or ``legacy-kept``), rewrites planned sites in place without altering
surrounding bytes, and proves per-module behavioral equivalence via pytest
(halving on discrepancy to isolate ``not-equivalent`` sites).

USAGE:
    python3 tools/fixture_codemod.py --dry-run [--format table|json] <paths...>
    python3 tools/fixture_codemod.py --apply [--format table|json] <paths...>
    python3 tools/fixture_codemod.py --census-markdown <paths...>
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import datetime
import fnmatch
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_workflows import artifact_core as _artifact_core  # noqa: E402
from agent_workflows import artifact_meta as _artifact_meta  # noqa: E402
from agent_workflows import backlog as _backlog_mod  # noqa: E402
from agent_workflows import plan_readiness as _plan_readiness  # noqa: E402
from agent_workflows import prompts as _prompts_mod  # noqa: E402
from agent_workflows import research_contract as _research_contract  # noqa: E402
from agent_workflows import review_findings as _review_findings  # noqa: E402
from tests import record_builder as _record_builder  # noqa: E402

# --------------------------------------------------------------------------------------
# Constants: F-01 pattern, 7 reason codes, 8 record types, legacy-subject globs
# --------------------------------------------------------------------------------------

F01_PATTERN = re.compile(
    r"- (Id|Status|Set|Kind|Blocks-Release|Readiness|Item-Dependencies|"
    r"Scope-Paths|From-Backlog|From-Spec|Work-Kind|Priority|Order|Date|"
    r"Gate-Kind|Gate-Ref|Approval|Subject-Id|Verdict|Graduated-To):|"
    r"## Workflow history"
)

_PROMPT_COMMENT_SITE_RE = re.compile(r"<!--\s*aw-prompt:")
_YAML_RESEARCH_SITE_RE = re.compile(
    r"\A---[ \t]*\n(?=[\s\S]*?\n(?:id|status|kind|outcome|topic):)[\s\S]*?\n---(?:\n|\Z)"
)

REASON_CODES: tuple[str, ...] = (
    "dynamic-construction",
    "unsupported-shape",
    "not-equivalent",
    "legacy-format subject",
    "displayed-output assertion",
    "setter-byte assertion",
    "body prose",
)

REASON_DISPOSITION: dict[str, str] = {
    "dynamic-construction": "hand",
    "unsupported-shape": "hand",
    "not-equivalent": "hand",
    "legacy-format subject": "legacy-kept",
    "displayed-output assertion": "legacy-kept",
    "setter-byte assertion": "legacy-kept",
    "body prose": "legacy-kept",
}

RECORD_TYPE_TO_METHOD: dict[str, str] = {
    "ipd": "plan",
    "spec": "spec",
    "backlog": "backlog",
    "research": "research",
    "release": "release",
    "prompt": "prompt",
    "walkthrough": "walkthrough",
    "review": "review",
}

_DIR_TO_RECORD_TYPE: dict[str, str] = {
    "plans": "ipd",
    "specs": "spec",
    "backlog": "backlog",
    "research": "research",
    "releases": "release",
    "prompts": "prompt",
    "walkthroughs": "walkthrough",
    "reviews": "review",
}

_EXT_TO_RECORD_TYPE: tuple[tuple[str, str], ...] = (
    (".ipd.md", "ipd"),
    (".spec.md", "spec"),
    (".backlog.md", "backlog"),
    (".release.md", "release"),
    (".prompt.md", "prompt"),
    (".walkthrough.md", "walkthrough"),
    (".review.md", "review"),
    (".research-report.md", "research"),
    (".research-prompt.md", "research"),
    (".findings.md", "research"),
    (".survey.md", "research"),
    (".research.md", "research"),
)

_HEADING_TO_RECORD_TYPE: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^#\s+IPD(?::\s*(.*)|\s*)$", re.IGNORECASE), "ipd"),
    (re.compile(r"^#\s+Spec(?::\s*(.*)|\s*)$", re.IGNORECASE), "spec"),
    (re.compile(r"^#\s+Release(?::\s*(.*)|\s*)$", re.IGNORECASE), "release"),
    (re.compile(r"^#\s+Walkthrough(?::\s*(.*)|\s*)$", re.IGNORECASE), "walkthrough"),
    (
        re.compile(r"^#\s+Review(?:\s+findings)?(?::\s*(.*)|\s*)$", re.IGNORECASE),
        "review",
    ),
    (re.compile(r"^#\s+Prompt(?::\s*(.*)|\s*)$", re.IGNORECASE), "prompt"),
    (
        re.compile(r"^#\s+Backlog(?:\s+item)?(?::\s*(.*)|\s+(.*)|\s*)$", re.IGNORECASE),
        "backlog",
    ),
)

_LEGACY_SUBJECT_MODULE_GLOBS: tuple[str, ...] = (
    # F-03 EXCLUDED list
    "test_artifact_meta_*.py",
    "test_writers_*.py",
    "test_m0001_*.py",
    "test_migrations_chain.py",
    # y3uowx reason-code table patterns
    "*legacy*",
    "*m0001*",
    "*migrat*",
    "test_front_matter_loose*",
    "test_selector_two_dialect*",
    "test_history_block_bounding*",
)

_LEGACY_SUBJECT_FUNC_MARKERS: tuple[str, ...] = (
    "legacy_format",
    "legacy_grammar",
    "m0001",
    "front_matter_loose",
    "selector_two_dialect",
    "history_block_bounding",
)

_PLACEHOLDER_PREFIX = "\x00AWEXPR_"
_PLACEHOLDER_SUFFIX = "\x00"
_PLACEHOLDER_RE = re.compile(r"\x00AWEXPR_(\d+)\x00")

_BULLET_LINE_RE = re.compile(r"^-\s+([A-Za-z][A-Za-z0-9 /-]*?)\s*:\s*(.*)$")
_OUTCOME_LINE_RE = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) ")

_DISPLAYED_OUTPUT_TOKENS: set[str] = {
    "stdout",
    "stderr",
    "out",
    "err",
    "output",
    "captured",
    "capsys",
    "capfd",
    "proc",
    "completed",
    "stdout_buf",
    "stderr_buf",
    "buf",
    "cli_out",
    "cmd_out",
    "printed",
    "display",
    "displayed",
    "output_text",
}

_SETTER_BYTE_TOKENS: set[str] = {
    "content",
    "file_text",
    "raw",
    "raw_text",
    "disk_text",
    "written",
    "stored_text",
    "updated_text",
    "new_text",
    "plan_text",
    "spec_text",
    "item_text",
    "record_text",
    "file_bytes",
    "body",
    "text",
    "md",
    "rendered",
}

_VALID_READINESS: set[str] = (
    set(_plan_readiness.VERDICTS.keys())
    | set(_plan_readiness.READINESS_TOKENS.keys())
    | {k.lower() for k in _plan_readiness.READINESS_TOKENS}
    | {"go", "caution", "hold", "replan", "go-pending-approval"}
)

_VALID_PLAN_SKELETON_ROLES: set[str] = {"child", "orchestrator"}

# Valid review fields (review_findings is outside artifact_meta.REGISTRY)
_REVIEW_FIELD_MAP: dict[str, str] = {
    "subject_id": "subject",
    "subject_type": "subject_type",
    "reviewed_at": "reviewed_at",
    "reviewer": "reviewer",
    "verdict": "verdict",
    "set": "set",
    "order": "order",
}


# --------------------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------------------


@dataclasses.dataclass
class ValueExpr:
    """Represents either a static literal string or a Python expression string."""

    is_static: bool
    static_value: str | None
    code: str


@dataclasses.dataclass
class SiteResult:
    """Classification result for one detected F-01 site in a test module."""

    line: int
    end_line: int
    col: int
    end_col: int
    action: str  # "rewrite" or "refuse"
    rewrite_class: str | None = None  # "standard", "invalid-input", or None
    record_type: str | None = None
    method: str | None = None
    kwargs: dict[str, str] = dataclasses.field(default_factory=dict)
    raw_fields: dict[str, str] = dataclasses.field(default_factory=dict)
    replacement: str | None = None
    reason: str | None = None
    disposition: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "line": self.line,
            "end_line": self.end_line,
            "col": self.col,
            "end_col": self.end_col,
            "action": self.action,
            "rewrite_class": self.rewrite_class,
            "record_type": self.record_type,
            "method": self.method,
            "kwargs": dict(self.kwargs),
            "raw_fields": dict(self.raw_fields),
            "replacement": self.replacement,
            "reason": self.reason,
            "disposition": self.disposition,
            "detail": self.detail,
        }


@dataclasses.dataclass
class ProofResult:
    """Equivalence proof outcome for one module in --apply mode."""

    before_hash: str | None = None
    after_hash: str | None = None
    equivalent: bool | None = None
    pytest_runs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "equivalent": self.equivalent,
            "pytest_runs": self.pytest_runs,
        }


@dataclasses.dataclass
class ModuleResult:
    """Analysis and optional rewrite/proof result for one Python test module."""

    module: str
    sites: list[SiteResult] = dataclasses.field(default_factory=list)
    applied: bool = False
    changed: bool = False
    proof: ProofResult = dataclasses.field(default_factory=ProofResult)

    def totals(self) -> dict[str, Any]:
        by_reason: dict[str, int] = {rc: 0 for rc in REASON_CODES}
        by_disposition: dict[str, int] = {"hand": 0, "legacy-kept": 0}
        rewrites = 0
        standard_rewrites = 0
        invalid_input_rewrites = 0
        refusals = 0
        for site in self.sites:
            if site.action == "rewrite":
                rewrites += 1
                if site.rewrite_class == "invalid-input":
                    invalid_input_rewrites += 1
                else:
                    standard_rewrites += 1
            else:
                refusals += 1
                if site.reason in by_reason:
                    by_reason[site.reason] += 1
                if site.disposition in by_disposition:
                    by_disposition[site.disposition] += 1
        return {
            "sites": len(self.sites),
            "rewrites": rewrites,
            "standard_rewrites": standard_rewrites,
            "invalid_input_rewrites": invalid_input_rewrites,
            "refusals": refusals,
            "by_reason": by_reason,
            "by_disposition": by_disposition,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "sites": [s.to_dict() for s in self.sites],
            "totals": self.totals(),
            "applied": self.applied,
            "changed": self.changed,
            "proof": self.proof.to_dict(),
        }


# --------------------------------------------------------------------------------------
# AST Helpers & Scope Context
# --------------------------------------------------------------------------------------


def _is_site_text(text: str) -> bool:
    """Return True when text matches F-01 or a structured prompt/research header."""
    if not text:
        return False
    if F01_PATTERN.search(text):
        return True
    if _PROMPT_COMMENT_SITE_RE.search(text):
        return True
    return bool(_YAML_RESEARCH_SITE_RE.search(text))


def _collect_docstring_nodes(tree: ast.AST) -> set[int]:
    """Return node ids of Python docstrings (first Expr(Constant(str)) in a scope)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ) and (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            ids.add(id(node.body[0].value))
    return ids


def _build_parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    return parents


def _enclosing_scope(
    node: ast.AST, parents: dict[int, ast.AST]
) -> tuple[ast.AST, str | None]:
    """Return (enclosing FunctionDef/AsyncFunctionDef/Module, enclosing func name)."""
    cur: ast.AST | None = parents.get(id(node))
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur, cur.name
        if isinstance(cur, ast.Module):
            return cur, None
        cur = parents.get(id(cur))
    return node, None


def _is_record_builder_call(node: ast.AST, rb_names: set[str]) -> bool:
    """Return True if node is RecordBuilder(...).<method>(...) or <rb>.<method>(...)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "RecordBuilder":
        return True
    if isinstance(func, ast.Attribute):
        owner = func.value
        if isinstance(owner, ast.Call):
            if isinstance(owner.func, ast.Name) and owner.func.id == "RecordBuilder":
                return True
            if (
                isinstance(owner.func, ast.Attribute)
                and owner.func.attr == "RecordBuilder"
            ):
                return True
        if isinstance(owner, ast.Name) and owner.id in rb_names:
            return True
        if (
            isinstance(owner, ast.Attribute)
            and owner.attr in rb_names
            and isinstance(owner.value, ast.Name)
            and owner.value.id == "self"
        ):
            return True
    return False


def _collect_record_builder_var_names(tree: ast.AST) -> set[str]:
    """Find variable or attribute names bound to RecordBuilder(...)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            callee = node.value.func
            is_rb = (isinstance(callee, ast.Name) and callee.id == "RecordBuilder") or (
                isinstance(callee, ast.Attribute) and callee.attr == "RecordBuilder"
            )
            if is_rb:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
                    elif isinstance(target, ast.Attribute):
                        names.add(target.attr)
    return names


def _is_dedent_call(node: ast.AST) -> bool:
    """Return True if node is dedent(<one-positional-str-arg>) or textwrap.dedent(...)."""
    if not isinstance(node, ast.Call):
        return False
    if len(node.args) != 1 or node.keywords:
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "dedent":
        return True
    return bool(isinstance(func, ast.Attribute) and func.attr == "dedent")


def _static_text_of_expr(node: ast.AST) -> str:
    """Concatenate static string literal parts inside an expression for F-01 probing."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                parts.append("{}")
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _static_text_of_expr(node.left) + _static_text_of_expr(node.right)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return _static_text_of_expr(node.left)
    if isinstance(node, ast.IfExp):
        return (
            _static_text_of_expr(node.body) + "\n" + _static_text_of_expr(node.orelse)
        )
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            return _static_text_of_expr(node.func.value)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            and len(node.args) == 1
            and isinstance(node.args[0], (ast.List, ast.Tuple))
        ):
            sep = _static_text_of_expr(node.func.value)
            return sep.join(_static_text_of_expr(elt) for elt in node.args[0].elts)
        if _is_dedent_call(node):
            return _static_text_of_expr(node.args[0])
    return ""


def _is_string_binop_add(node: ast.AST) -> bool:
    """Return True if a BinOp(Add) contains at least one string literal/f-string."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)):
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.JoinedStr):
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            return True
    return False


def _is_join_of_strings(node: ast.AST) -> bool:
    """Return True for '<sep>'.join([...]) where elements include string literals."""
    if not isinstance(node, ast.Call):
        return False
    if not (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "join"
        and isinstance(node.func.value, ast.Constant)
        and isinstance(node.func.value.value, str)
    ):
        return False
    return not (
        len(node.args) != 1 or not isinstance(node.args[0], (ast.List, ast.Tuple))
    )


def _is_format_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
        and isinstance(node.func.value, (ast.Constant, ast.JoinedStr))
    )


def _is_percent_format(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mod)
        and isinstance(node.left, ast.Constant)
        and isinstance(node.left.value, str)
    )


def _is_string_ifexp(node: ast.AST) -> bool:
    if not isinstance(node, ast.IfExp):
        return False
    for branch in (node.body, node.orelse):
        if isinstance(branch, ast.JoinedStr) or (
            isinstance(branch, ast.Constant) and isinstance(branch.value, str)
        ):
            return True
        if _is_string_binop_add(branch):
            return True
    return False


def _collect_candidate_sites(
    tree: ast.AST,
    docstrings: set[int],
    rb_names: set[str],
) -> list[tuple[ast.AST, str]]:
    """Walk AST in source order and collect (node, kind) candidate F-01 sites.

    Kinds:
      - 'literal': plain Constant(str) or JoinedStr (possibly wrapped in dedent(...))
      - 'dynamic': BinOp(Add), BinOp(Mod), IfExp, .format(), .join()
    """
    candidates: list[tuple[ast.AST, str]] = []

    def visit(node: ast.AST) -> None:
        if id(node) in docstrings:
            return
        # Skip calls into RecordBuilder so already-converted code is idempotent.
        if _is_record_builder_call(node, rb_names):
            return

        # dedent("...") or textwrap.dedent(f"...")
        if _is_dedent_call(node):
            assert isinstance(node, ast.Call)
            arg = node.args[0]
            if (
                isinstance(arg, (ast.JoinedStr,))
                or (isinstance(arg, ast.Constant) and isinstance(arg.value, str))
            ) and _is_site_text(_static_text_of_expr(arg)):
                candidates.append((node, "literal"))
                return

        # Composite dynamic string expressions: treat topmost node as one site.
        if (
            _is_string_binop_add(node)
            or _is_percent_format(node)
            or _is_format_call(node)
            or _is_join_of_strings(node)
            or _is_string_ifexp(node)
        ) and _is_site_text(_static_text_of_expr(node)):
            candidates.append((node, "dynamic"))
            return

        # Single f-string literal (do not recurse into its nested parts).
        if isinstance(node, ast.JoinedStr):
            if _is_site_text(_static_text_of_expr(node)):
                candidates.append((node, "literal"))
            return

        # Plain string constant.
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _is_site_text(node.value):
                candidates.append((node, "literal"))
            return

        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    candidates.sort(
        key=lambda pair: (
            getattr(pair[0], "lineno", 0),
            getattr(pair[0], "col_offset", 0),
        )
    )
    return candidates


# --------------------------------------------------------------------------------------
# Scope Analysis: assignments, write_text bindings, assertion classification
# --------------------------------------------------------------------------------------


class _ScopeIndex:
    """Indexes variable definitions and write_text() calls in a single scope."""

    def __init__(self, scope_node: ast.AST) -> None:
        self.var_defs: dict[str, list[ast.AST]] = {}
        self.var_written_to: dict[str, list[ast.AST]] = {}
        self._index(scope_node)

    def _index(self, scope_node: ast.AST) -> None:
        for node in ast.walk(scope_node):
            # Do not cross into nested function defs unless scope_node is that def.
            if node is not scope_node and isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                continue
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_defs.setdefault(target.id, []).append(node.value)
                    elif (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        self.var_defs.setdefault(f"self.{target.attr}", []).append(
                            node.value
                        )
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                if isinstance(node.target, ast.Name):
                    self.var_defs.setdefault(node.target.id, []).append(node.value)
            elif isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "write_text"
                and node.args
            ):
                arg0 = node.args[0]
                if isinstance(arg0, ast.Name):
                    self.var_written_to.setdefault(arg0.id, []).append(node.func.value)


def _is_legacy_subject_module(module_path: Path, func_name: str | None) -> bool:
    name = module_path.name
    for glob in _LEGACY_SUBJECT_MODULE_GLOBS:
        if fnmatch.fnmatch(name, glob):
            return True
    if func_name:
        low = func_name.lower()
        for marker in _LEGACY_SUBJECT_FUNC_MARKERS:
            if marker in low:
                return True
    return False


def _find_enclosing_assertion(
    node: ast.AST, parents: dict[int, ast.AST]
) -> ast.AST | None:
    """Return the enclosing Assert or assert*() / pytest.raises(match=...) node, if any."""
    cur: ast.AST | None = parents.get(id(node))
    while cur is not None:
        if isinstance(
            cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
        ):
            return None
        if isinstance(cur, ast.Assert):
            return cur
        if isinstance(cur, ast.Call):
            func = cur.func
            if isinstance(func, ast.Attribute) and func.attr.startswith("assert"):
                return cur
            if isinstance(func, ast.Name) and func.id.startswith("assert"):
                return cur
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "raises"
                and any(kw.arg == "match" for kw in cur.keywords)
            ):
                return cur
        cur = parents.get(id(cur))
    return None


def _tokens_in_expr(node: ast.AST) -> tuple[set[str], set[str]]:
    """Return (identifiers/attrs, method_calls) present in an expression."""
    names: set[str] = set()
    calls: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            names.add(sub.id.lower())
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr.lower())
        elif isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Attribute):
                calls.add(sub.func.attr.lower())
            elif isinstance(sub.func, ast.Name):
                calls.add(sub.func.id.lower())
    return names, calls


def _classify_assertion(
    site_node: ast.AST,
    assert_node: ast.AST,
    scope_index: _ScopeIndex,
) -> str:
    """Distinguish 'displayed-output assertion' from 'setter-byte assertion'."""
    # Gather sibling expressions in the assertion (excluding site_node itself).
    siblings: list[ast.AST] = []
    if isinstance(assert_node, ast.Assert):
        test = assert_node.test
        if isinstance(test, ast.Compare):
            for part in [test.left, *test.comparators]:
                if part is not site_node and not _contains_node(part, site_node):
                    siblings.append(part)
        else:
            siblings.append(test)
    elif isinstance(assert_node, ast.Call):
        for arg in assert_node.args:
            if arg is not site_node and not _contains_node(arg, site_node):
                siblings.append(arg)
        for kw in assert_node.keywords:
            if kw.value is not site_node and not _contains_node(kw.value, site_node):
                siblings.append(kw.value)

    output_score = 0
    byte_score = 0

    def inspect_expr(expr: ast.AST, depth: int = 0) -> None:
        nonlocal output_score, byte_score
        names, calls = _tokens_in_expr(expr)
        if "read_text" in calls or "read_bytes" in calls:
            byte_score += 5
        if any(
            c.startswith(("set_", "write_", "update_", "patch_", "render_"))
            for c in calls
        ):
            byte_score += 3
        if "readouterr" in calls or "getvalue" in calls or "run_cli" in calls:
            output_score += 5
        if "stdout" in names or "stderr" in names:
            output_score += 5
        for n in names:
            if n in _DISPLAYED_OUTPUT_TOKENS or any(
                tok in n for tok in ("stdout", "stderr", "capsys", "capfd", "output")
            ):
                output_score += 2
            if n in _SETTER_BYTE_TOKENS or any(
                tok in n
                for tok in ("read_text", "file_text", "disk", "stored", "written")
            ):
                byte_score += 2
        if depth < 2:
            for sub in ast.walk(expr):
                if isinstance(sub, ast.Name) and sub.id in scope_index.var_defs:
                    for rhs in scope_index.var_defs[sub.id]:
                        inspect_expr(rhs, depth + 1)

    for sib in siblings:
        inspect_expr(sib, 0)

    if output_score > byte_score:
        return "displayed-output assertion"
    return "setter-byte assertion"


def _contains_node(root: ast.AST, target: ast.AST) -> bool:
    for sub in ast.walk(root):
        if sub is target:
            return True
    return False


def _infer_type_from_path_expr(
    path_expr: ast.AST, scope_index: _ScopeIndex, depth: int = 0
) -> str | None:
    """Infer record type from a path expression's records directory or filename suffix."""
    strings: list[str] = []
    for sub in ast.walk(path_expr):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            strings.append(sub.value)
        elif isinstance(sub, ast.JoinedStr):
            strings.append(_static_text_of_expr(sub))

    # First pass: explicit file suffix (.ipd.md, .spec.md, .backlog.md, ...)
    for s in strings:
        low = s.lower()
        for ext, rtype in _EXT_TO_RECORD_TYPE:
            if low.endswith(ext) or ext in low:
                return rtype

    # Second pass: records directory segment (plans, specs, backlog, ...)
    for s in strings:
        parts = [p.lower() for p in re.split(r"[/\\]+", s) if p]
        for part in parts:
            if part in _DIR_TO_RECORD_TYPE:
                return _DIR_TO_RECORD_TYPE[part]

    # Follow simple variable definitions (e.g. done_path = repo / '.aw' / 'records' / 'backlog' / ...)
    if depth < 3:
        for sub in ast.walk(path_expr):
            if isinstance(sub, ast.Name) and sub.id in scope_index.var_defs:
                for rhs in scope_index.var_defs[sub.id]:
                    inferred = _infer_type_from_path_expr(rhs, scope_index, depth + 1)
                    if inferred:
                        return inferred
            elif (
                isinstance(sub, ast.Attribute)
                and isinstance(sub.value, ast.Name)
                and sub.value.id == "self"
            ):
                key = f"self.{sub.attr}"
                if key in scope_index.var_defs:
                    for rhs in scope_index.var_defs[key]:
                        inferred = _infer_type_from_path_expr(
                            rhs, scope_index, depth + 1
                        )
                        if inferred:
                            return inferred
    return None


def _find_written_path_expr(
    site_node: ast.AST, parents: dict[int, ast.AST], scope_index: _ScopeIndex
) -> ast.AST | None:
    """Find the Path receiver of <path>.write_text(site) if the site is written to disk."""
    parent = parents.get(id(site_node))
    # Direct argument to path.write_text(site, ...)
    if isinstance(parent, ast.Call) and (
        isinstance(parent.func, ast.Attribute)
        and parent.func.attr == "write_text"
        and parent.args
        and parent.args[0] is site_node
    ):
        return parent.func.value
    # Assigned to a variable that is passed to path.write_text(var, ...)
    if isinstance(parent, ast.Assign):
        for target in parent.targets:
            if isinstance(target, ast.Name) and target.id in scope_index.var_written_to:
                return scope_index.var_written_to[target.id][0]
    if (
        isinstance(parent, ast.AnnAssign)
        and isinstance(parent.target, ast.Name)
        and parent.target.id in scope_index.var_written_to
    ):
        return scope_index.var_written_to[parent.target.id][0]
    return None


def _is_body_or_oq_kwarg(site_node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    parent = parents.get(id(site_node))
    return bool(
        isinstance(parent, ast.keyword) and parent.arg in ("open_questions", "body")
    )


# --------------------------------------------------------------------------------------
# Template Extraction for Constant / JoinedStr and Body-Prose Detection
# --------------------------------------------------------------------------------------


def _extract_template(
    node: ast.AST,
) -> tuple[str, list[ast.FormattedValue], bool]:
    """Extract (template_str, formatted_values, was_dedented) from Constant/JoinedStr/dedent."""
    was_dedented = False
    target = node
    if _is_dedent_call(node):
        assert isinstance(node, ast.Call)
        target = node.args[0]
        was_dedented = True

    if isinstance(target, ast.Constant) and isinstance(target.value, str):
        text = textwrap.dedent(target.value) if was_dedented else target.value
        return text, [], was_dedented

    if isinstance(target, ast.JoinedStr):
        fvs: list[ast.FormattedValue] = []
        parts: list[str] = []
        for item in target.values:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                parts.append(item.value)
            elif isinstance(item, ast.FormattedValue):
                idx = len(fvs)
                fvs.append(item)
                parts.append(f"{_PLACEHOLDER_PREFIX}{idx}{_PLACEHOLDER_SUFFIX}")
        raw = "".join(parts)
        if was_dedented:
            raw = textwrap.dedent(raw)
        return raw, fvs, was_dedented

    raise TypeError(f"unexpected literal node {type(node).__name__}")


def _template_to_value_expr(
    raw_segment: str, fvs: list[ast.FormattedValue], *, strip_val: bool = True
) -> ValueExpr | None:
    """Convert a template segment (possibly containing placeholders) to a ValueExpr.

    Returns None if a placeholder uses unsupported formatting or cannot be represented.
    """
    seg = raw_segment.strip() if strip_val else raw_segment
    matches = list(_PLACEHOLDER_RE.finditer(seg))
    if not matches:
        return ValueExpr(is_static=True, static_value=seg, code=repr(seg))

    # Entire value is a single placeholder: emit the bare expression (e.g. status=status).
    if len(matches) == 1 and matches[0].start() == 0 and matches[0].end() == len(seg):
        fv = fvs[int(matches[0].group(1))]
        if fv.conversion != -1:
            return None
        if fv.format_spec is not None:
            spec_text = _static_text_of_expr(fv.format_spec)
            if spec_text not in ("", "d", "02d", "s"):
                return None
        expr_code = ast.unparse(fv.value)
        return ValueExpr(is_static=False, static_value=None, code=expr_code)

    # Mixed literal + placeholder(s): reconstruct a Python f-string expression.
    pieces: list[str] = []
    pos = 0
    for m in matches:
        lit = seg[pos : m.start()]
        if lit:
            pieces.append(_escape_fstring_literal(lit))
        fv = fvs[int(m.group(1))]
        conv = ""
        if fv.conversion == 114:
            conv = "!r"
        elif fv.conversion == 115:
            conv = "!s"
        elif fv.conversion == 97:
            conv = "!a"
        spec = ""
        if fv.format_spec is not None:
            spec = ":" + _static_text_of_expr(fv.format_spec)
        expr_src = ast.unparse(fv.value)
        pieces.append("{" + expr_src + conv + spec + "}")
        pos = m.end()
    tail = seg[pos:]
    if tail:
        pieces.append(_escape_fstring_literal(tail))
    inner = "".join(pieces)
    # Choose quote style cleanly using repr-style escaping on newlines/quotes.
    escaped = (
        inner.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace('"', '\\"')
    )
    return ValueExpr(is_static=False, static_value=None, code=f'f"{escaped}"')


def _escape_fstring_literal(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")


def _is_body_prose_text(template: str) -> bool:
    """Return True when F-01 matches occur solely in body prose (e.g. OQ rows, inline text)."""
    lines = template.splitlines()
    if not lines:
        return False

    # Structured prompt or YAML research frontmatter is never body prose.
    if _PROMPT_COMMENT_SITE_RE.search(template) or _YAML_RESEARCH_SITE_RE.search(
        template
    ):
        return False

    # Check whether any line starts with a record heading or top-level metadata bullet
    # BEFORE any ## / ### body heading.
    saw_body_heading = False
    saw_oq_marker = False
    top_bullets: list[tuple[str, str]] = []
    body_f01_matches = False
    inline_only_f01 = False

    first_nonempty: str | None = None
    for line in lines:
        s = line.strip()
        if s and first_nonempty is None:
            first_nonempty = s
        if re.match(r"^###\s+OQ-", s) or re.match(r"^##\s+Open [Qq]uestions\s*$", s):
            saw_oq_marker = True
            saw_body_heading = True
            continue
        if re.match(r"^#{2,6}\s+", s):
            if re.match(r"^##\s+Workflow history\s*$", s):
                # Workflow history heading itself is a record section, not body prose.
                return False
            saw_body_heading = True
            continue
        if not saw_body_heading:
            m = _BULLET_LINE_RE.match(s)
            if m:
                top_bullets.append((m.group(1), m.group(2)))
            elif F01_PATTERN.search(s):
                # F-01 matched inline inside a sentence (not a leading '- Key:').
                inline_only_f01 = True
        else:
            if F01_PATTERN.search(s):
                body_f01_matches = True

    if not top_bullets and (saw_oq_marker or body_f01_matches or inline_only_f01):
        return True

    # Open-question block without a record heading (e.g. - Blocking: yes / - Status: open / - Owner: ...)
    top_keys = {k.strip().lower() for k, _ in top_bullets}
    oq_keys = {"blocking", "owner", "resolution or deferral rationale", "resolution"}
    if (
        top_bullets
        and (top_keys & oq_keys)
        and not any(
            pat.match(first_nonempty or "") for pat, _ in _HEADING_TO_RECORD_TYPE
        )
        and "id" not in top_keys
    ):
        return True

    # If the text starts with ordinary prose (not a heading and not a bullet) and only
    # mentions bullets later in body text (no - Id:), treat as body prose.
    return bool(
        first_nonempty
        and not first_nonempty.startswith("#")
        and not first_nonempty.startswith("-")
        and not first_nonempty.startswith(">")
        and "id" not in top_keys
    )


# --------------------------------------------------------------------------------------
# Record Parsing & Field Mapping (through artifact_meta.registry_fields)
# --------------------------------------------------------------------------------------


def _registry_field_map(record_type: str) -> tuple[set[str], dict[str, str]]:
    """Build (allowed_registry_fields, legacy_label_lower -> registry_field) from artifact_meta."""
    if record_type == "review":
        return set(_REVIEW_FIELD_MAP.values()), dict(_REVIEW_FIELD_MAP)

    allowed = set(_artifact_meta.registry_fields(record_type))
    label_map: dict[str, str] = {}

    # Derive canonical mappings from artifact_meta single-authority dicts.
    for reg_name, label in _artifact_meta._LEGACY_BULLET_LABEL.items():
        if reg_name in allowed:
            label_map[label.lower()] = reg_name
            label_map[label.lower().replace("-", "_").replace(" ", "_")] = reg_name
    if record_type == "research":
        for reg_name, ykey in _artifact_meta._RESEARCH_YAML_KEY.items():
            if reg_name in allowed:
                label_map[ykey.lower()] = reg_name
                label_map[ykey.lower().replace("-", "_")] = reg_name
    if record_type == "prompt":
        for reg_name, pkey in _artifact_meta._PROMPT_COMMENT_KEY.items():
            if reg_name in allowed:
                label_map[pkey.lower()] = reg_name
                label_map[pkey.lower().replace("-", "_")] = reg_name

    # Every registry field maps directly from its hyphen/space-normalized label.
    for reg_name in allowed:
        label_map[reg_name] = reg_name
        label_map[reg_name.replace("_", "-")] = reg_name
        label_map[reg_name.replace("_", " ")] = reg_name

    return allowed, label_map


def _validate_static_field_value(
    record_type: str,
    reg_field: str,
    value: str,
) -> bool:
    """Return True if a static literal value is valid for RecordBuilder, False if invalid-input."""
    if reg_field == "id6":
        return bool(_artifact_core.ID6_RE.fullmatch(value))

    if reg_field == "target_id":
        return bool(_artifact_core.ID6_RE.fullmatch(value))

    if reg_field == "when":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return False
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            return False
        return True

    if reg_field == "order":
        return bool(re.fullmatch(r"\d+", value))

    if reg_field == "status":
        valid = _record_builder._VALID_STATUSES.get(record_type)
        if valid is not None:
            return value in valid
        return True

    if reg_field == "priority":
        return value in _backlog_mod.PRIORITIES

    if reg_field == "work_kind":
        return value in _backlog_mod.KINDS

    if reg_field == "plan_role":
        return value in _VALID_PLAN_SKELETON_ROLES

    if reg_field == "research_kind":
        return value in _research_contract.KINDS

    if reg_field == "outcome":
        return value in _research_contract.OUTCOMES

    if reg_field == "prompt_kind":
        return value in _prompts_mod.PROMPT_KINDS

    if reg_field == "readiness":
        return value in _VALID_READINESS or value.lower() in _VALID_READINESS

    if record_type == "review":
        if reg_field == "subject":
            return bool(_artifact_core.ID6_RE.fullmatch(value))
        if reg_field == "subject_type":
            return value in _review_findings.SUBJECT_TYPES
        if reg_field == "reviewed_at":
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                return False
            try:
                datetime.date.fromisoformat(value)
            except ValueError:
                return False
            return True
        if reg_field in ("reviewer", "verdict"):
            return bool(value.strip())
        return True

    fdef = _artifact_meta.get_field_def(record_type, reg_field)
    if fdef is not None and fdef.allowed_values is not None:
        return value in fdef.allowed_values
    return True


def _is_known_ipd_non_skeleton_role(value: str) -> bool:
    """Return True for valid IPD plan_role values that build_skeleton rejects (e.g. tool-defect)."""
    fdef = _artifact_meta.get_field_def("ipd", "plan_role")
    if fdef is None or fdef.allowed_values is None:
        return False
    return value in fdef.allowed_values and value not in _VALID_PLAN_SKELETON_ROLES


def _infer_type_from_template(template: str) -> tuple[str | None, str | None]:
    """Return (record_type, heading_title_template) from text markers/headings."""
    if _YAML_RESEARCH_SITE_RE.search(template):
        return "research", None
    if _PROMPT_COMMENT_SITE_RE.search(template):
        return "prompt", None

    lines = template.splitlines()
    for line in lines:
        s = line.strip()
        if not s:
            continue
        for pat, rtype in _HEADING_TO_RECORD_TYPE:
            m = pat.match(s)
            if m:
                title_part = next((g for g in m.groups() if g is not None), "")
                return rtype, title_part.strip()
        # Only check the first non-empty line for an H1 heading.
        break

    # Review records may omit H1 but carry Subject-Id + Subject-Type/Verdict.
    if re.search(r"(?m)^-\s+Subject-Id:", template) and (
        re.search(r"(?m)^-\s+Subject-Type:", template)
        or re.search(r"(?m)^-\s+Verdict:", template)
    ):
        return "review", None

    return None, None


def _parse_yaml_research_site(
    template: str, fvs: list[ast.FormattedValue]
) -> tuple[dict[str, tuple[str, ValueExpr]] | None, str | None, str | None]:
    """Parse YAML frontmatter research fixture.

    Returns (fields_map, body_template, failure_reason_code).
    """
    m = re.match(r"\A---[ \t]*\n(.*?)\n---(?:\n(.*))?\Z", template, re.DOTALL)
    if not m:
        return None, None, "unsupported-shape"
    fm_block = m.group(1)
    body = m.group(2) if m.group(2) is not None else ""

    fields: dict[str, tuple[str, ValueExpr]] = {}
    for raw_line in fm_block.splitlines():
        s = raw_line.strip()
        if not s or s.startswith("#"):
            continue
        # Whole-line placeholder -> dynamic-construction
        if _PLACEHOLDER_RE.fullmatch(s):
            return None, None, "dynamic-construction"
        if ":" not in s:
            return None, None, "unsupported-shape"
        key_part, val_part = s.split(":", 1)
        if _PLACEHOLDER_RE.search(key_part):
            return None, None, "dynamic-construction"
        ykey = key_part.strip()
        vstr = val_part.strip()
        if ykey in fields:
            return None, None, "unsupported-shape"
        # Strip matching single/double quotes on static YAML scalars
        if (
            not _PLACEHOLDER_RE.search(vstr)
            and len(vstr) >= 2
            and vstr[0] == vstr[-1]
            and vstr[0] in ("'", '"')
        ):
            vstr = vstr[1:-1]
        vexpr = _template_to_value_expr(vstr, fvs)
        if vexpr is None:
            return None, None, "dynamic-construction"
        fields[ykey] = (ykey, vexpr)

    return fields, body, None


def _parse_prompt_comment_site(
    template: str, fvs: list[ast.FormattedValue]
) -> tuple[dict[str, tuple[str, ValueExpr]] | None, str | None, str | None]:
    """Parse <!-- aw-prompt: ... --> prompt fixture."""
    lines = template.splitlines()
    if not lines:
        return None, None, "unsupported-shape"
    first = lines[0].strip()
    m = re.match(r"\A<!--\s*aw-prompt:\s*(.*?)\s*-->\Z", first)
    if not m:
        return None, None, "unsupported-shape"
    inner = m.group(1)
    for marker in (
        f" . {_prompts_mod._METADATA_TRAILER}",
        " . This HTML comment is",
        _prompts_mod._METADATA_TRAILER,
    ):
        if marker in inner:
            inner = inner.split(marker, 1)[0].strip()
            break
    fields: dict[str, tuple[str, ValueExpr]] = {}
    for seg in inner.split("|"):
        s = seg.strip()
        if not s:
            continue
        if _PLACEHOLDER_RE.fullmatch(s):
            return None, None, "dynamic-construction"
        if ":" not in s:
            return None, None, "unsupported-shape"
        k_part, v_part = s.split(":", 1)
        if _PLACEHOLDER_RE.search(k_part):
            return None, None, "dynamic-construction"
        pkey = k_part.strip()
        if pkey in fields:
            return None, None, "unsupported-shape"
        vexpr = _template_to_value_expr(v_part, fvs)
        if vexpr is None:
            return None, None, "dynamic-construction"
        fields[pkey] = (pkey, vexpr)
    body = "\n".join(lines[1:]).lstrip("\n")
    return fields, body, None


def _parse_bullet_site(
    template: str,
    fvs: list[ast.FormattedValue],
    has_h1: bool,
) -> tuple[
    dict[str, tuple[str, ValueExpr]] | None,
    list[ValueExpr] | None,
    str | None,
    str | None,
    str | None,
]:
    """Parse a bullet-metadata record fixture.

    Returns (bullets_map, history_entries, open_questions_text, body_text, failure_reason).
    """
    lines = template.splitlines()
    idx = 0
    # Skip leading blank lines.
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    # Skip leading H1 heading if present (whether matched by prefix or arbitrary title).
    if idx < len(lines) and lines[idx].strip().startswith("# "):
        idx += 1

    bullets: dict[str, tuple[str, ValueExpr]] = {}
    while idx < len(lines):
        raw = lines[idx]
        s = raw.strip()
        if not s:
            idx += 1
            continue
        if s.startswith("## "):
            break
        if s.startswith("> "):
            idx += 1
            continue
        # Check for whole-line or multi-placeholder line in metadata region (e.g. f"{br_line}").
        if _PLACEHOLDER_RE.search(s) and not s.startswith("- "):
            return None, None, None, None, "dynamic-construction"
        m = _BULLET_LINE_RE.match(s)
        if not m:
            # Non-bullet line before any ## heading inside a record fixture.
            return None, None, None, None, "unsupported-shape"
        label = m.group(1).strip()
        val_raw = m.group(2)
        if _PLACEHOLDER_RE.search(label):
            return None, None, None, None, "dynamic-construction"
        if label.lower() in bullets:
            return None, None, None, None, "unsupported-shape"
        vexpr = _template_to_value_expr(val_raw, fvs)
        if vexpr is None:
            return None, None, None, None, "dynamic-construction"
        bullets[label.lower()] = (label, vexpr)
        idx += 1

    # Parse remaining sections (## Workflow history, ## Open questions, other body sections).
    history_entries: list[ValueExpr] | None = None
    open_questions: str | None = None
    body_sections: list[str] = []

    while idx < len(lines):
        line = lines[idx]
        if line.strip() == "## Workflow history":
            idx += 1
            hist: list[ValueExpr] = []
            while idx < len(lines) and not lines[idx].startswith("## "):
                hline = lines[idx].strip()
                if hline:
                    if _PLACEHOLDER_RE.fullmatch(hline):
                        return None, None, None, None, "dynamic-construction"
                    if not hline.startswith("- "):
                        return None, None, None, None, "dynamic-construction"
                    vexpr = _template_to_value_expr(hline, fvs)
                    if vexpr is None:
                        return None, None, None, None, "dynamic-construction"
                    hist.append(vexpr)
                idx += 1
            history_entries = hist
            continue

        if re.match(r"^##\s+Open [Qq]uestions\s*$", line.strip()):
            idx += 1
            oq_lines: list[str] = []
            while idx < len(lines) and not lines[idx].startswith("## "):
                oq_lines.append(lines[idx])
                idx += 1
            open_questions = "\n".join(oq_lines).strip("\n")
            continue

        sec_lines = [line]
        idx += 1
        while idx < len(lines) and not lines[idx].startswith("## "):
            sec_lines.append(lines[idx])
            idx += 1
        body_sections.append("\n".join(sec_lines).rstrip("\n"))

    body_text = "\n\n".join(s for s in body_sections if s.strip())
    return bullets, history_entries, open_questions, body_text, None


def _parse_yaml_list_literal(text: str) -> list[str] | None:
    """Parse inline YAML list like '[]' or '[a, b]'."""
    s = text.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return None
    inner = s[1:-1].strip()
    if not inner:
        return []
    items: list[str] = []
    for part in inner.split(","):
        p = part.strip()
        if len(p) >= 2 and p[0] == p[-1] and p[0] in ("'", '"'):
            p = p[1:-1]
        if p:
            items.append(p)
    return items


# --------------------------------------------------------------------------------------
# Planning a Site Rewrite
# --------------------------------------------------------------------------------------


def _plan_site(
    node: ast.AST,
    site_kind: str,
    module_path: Path,
    parents: dict[int, ast.AST],
    scope_index: _ScopeIndex,
    func_name: str | None,
) -> SiteResult:
    """Classify one detected site as a planned rewrite or a refusal with reason code."""
    line = getattr(node, "lineno", 0)
    end_line = getattr(node, "end_lineno", line)
    col = getattr(node, "col_offset", 0)
    end_col = getattr(node, "end_col_offset", col)

    def refuse(reason: str, detail: str = "") -> SiteResult:
        return SiteResult(
            line=line,
            end_line=end_line,
            col=col,
            end_col=end_col,
            action="refuse",
            reason=reason,
            disposition=REASON_DISPOSITION[reason],
            detail=detail,
        )

    # 1. Module/test subject is the legacy grammar -> legacy-format subject.
    if _is_legacy_subject_module(module_path, func_name):
        return refuse(
            "legacy-format subject", "module or test subject is legacy grammar"
        )

    # 2. Assertion context -> displayed-output assertion or setter-byte assertion.
    assert_node = _find_enclosing_assertion(node, parents)
    if assert_node is not None:
        assert_reason = _classify_assertion(node, assert_node, scope_index)
        return refuse(assert_reason, "expected value in assertion")

    # 3. Dynamic composite expressions (+, %, .format, .join, ternary if-else).
    if site_kind == "dynamic":
        return refuse("dynamic-construction", "text built dynamically by expression")

    # 4. Extract template and check body prose.
    template, fvs, _ = _extract_template(node)
    if _is_body_or_oq_kwarg(node, parents) or _is_body_prose_text(template):
        return refuse(
            "body prose", "bullets appear in body prose rather than record metadata"
        )

    # 5. Infer record type from heading/format marker or written path.
    inferred_type, heading_title = _infer_type_from_template(template)
    written_path_expr = _find_written_path_expr(node, parents, scope_index)
    if inferred_type is None and written_path_expr is not None:
        inferred_type = _infer_type_from_path_expr(written_path_expr, scope_index)

    if inferred_type is None or inferred_type not in RECORD_TYPE_TO_METHOD:
        return refuse(
            "unsupported-shape",
            "record type cannot be inferred from heading or written path",
        )

    method_name = RECORD_TYPE_TO_METHOD[inferred_type]
    method_params = set(
        inspect.signature(
            getattr(_record_builder.RecordBuilder, method_name)
        ).parameters
    )

    # 6. Parse fields according to record dialect (YAML / prompt comment / bullets).
    history_entries: list[ValueExpr] | None = None
    open_questions_tpl: str | None = None
    body_tpl: str | None = None

    if inferred_type == "research" and _YAML_RESEARCH_SITE_RE.search(template):
        parsed_fields, body_tpl, fail_rc = _parse_yaml_research_site(template, fvs)
        if fail_rc:
            return refuse(fail_rc, "could not statically map YAML research frontmatter")
    elif inferred_type == "prompt" and _PROMPT_COMMENT_SITE_RE.search(template):
        parsed_fields, body_tpl, fail_rc = _parse_prompt_comment_site(template, fvs)
        if fail_rc:
            return refuse(fail_rc, "could not statically map aw-prompt comment")
    else:
        parsed_fields, history_entries, open_questions_tpl, body_tpl, fail_rc = (
            _parse_bullet_site(template, fvs, has_h1=(heading_title is not None))
        )
        if fail_rc:
            return refuse(fail_rc, "could not statically map bullet metadata lines")

    assert parsed_fields is not None
    if not parsed_fields:
        return refuse("unsupported-shape", "no metadata fields found in record site")

    # 7. Map fields through artifact_meta.registry_fields (no second table).
    allowed_fields, label_map = _registry_field_map(inferred_type)

    kwargs_code: dict[str, str] = {}
    raw_fields_code: dict[str, str] = {}
    has_invalid_input = False

    # Heading title handling
    if heading_title:
        title_vexpr = _template_to_value_expr(heading_title, fvs)
        if title_vexpr is None:
            return refuse("dynamic-construction", "unsupported heading expression")
        if inferred_type in ("ipd", "spec"):
            kwargs_code["title"] = title_vexpr.code
        elif inferred_type == "release":
            # Version from heading if Version bullet is absent
            kwargs_code.setdefault("version", title_vexpr.code)

    for orig_label, vexpr in parsed_fields.values():
        norm = orig_label.strip().lower().replace("-", "_").replace(" ", "_")

        # Resolve contextual aliases to canonical RecordBuilder / registry parameter names.
        reg_name: str | None = None
        if inferred_type == "review":
            reg_name = _REVIEW_FIELD_MAP.get(norm)
            if norm == "findings":
                # Summary bullet on review records is not writable via RecordBuilder.review
                return refuse(
                    "unsupported-shape",
                    "review Findings summary bullet is not supported by RecordBuilder.review",
                )
        else:
            if norm == "id":
                reg_name = "id6"
            elif (
                norm == "date"
                or norm == "created"
                and inferred_type in ("research", "prompt")
            ):
                reg_name = "when"
            elif norm == "kind":
                if inferred_type == "ipd":
                    reg_name = "plan_role"
                elif inferred_type == "backlog":
                    reg_name = "work_kind"
                elif inferred_type == "research":
                    reg_name = "research_kind"
                elif inferred_type == "prompt":
                    reg_name = "prompt_kind"
            elif norm in ("concern", "scope") and inferred_type == "ipd":
                # Template-owned IPD skeleton bullets (not in REGISTRY["ipd"]).
                continue
            elif norm == "summary" and "summary" in method_params:
                reg_name = "summary"
            elif orig_label.strip().lower() in label_map:
                reg_name = label_map[orig_label.strip().lower()]
            elif norm in label_map:
                reg_name = label_map[norm]
            elif norm in allowed_fields:
                reg_name = norm

        if reg_name is None:
            return refuse(
                "unsupported-shape",
                f"unknown field {orig_label!r} for record type {inferred_type!r}",
            )

        # Normalize research YYYYMMDD created dates to YYYY-MM-DD for RecordBuilder.when.
        effective_static = vexpr.static_value
        effective_code = vexpr.code
        if (
            reg_name == "when"
            and inferred_type == "research"
            and vexpr.is_static
            and effective_static is not None
            and re.fullmatch(r"\d{8}", effective_static)
        ):
            effective_static = f"{effective_static[0:4]}-{effective_static[4:6]}-{effective_static[6:8]}"
            effective_code = repr(effective_static)

        # Convert YAML inline lists for research topic / consumed_by.
        if (
            inferred_type == "research"
            and reg_name in ("topic", "consumed_by")
            and vexpr.is_static
            and effective_static is not None
        ):
            parsed_list = _parse_yaml_list_literal(effective_static)
            if parsed_list is not None:
                kwargs_code[reg_name] = repr(parsed_list)
                continue

        # Validate static values; deliberately invalid inputs route through raw_fields=.
        if vexpr.is_static and effective_static is not None:
            if not _validate_static_field_value(
                inferred_type, reg_name, effective_static
            ):
                if inferred_type == "review":
                    return refuse(
                        "unsupported-shape",
                        f"invalid review field {orig_label!r}={effective_static!r} "
                        "and RecordBuilder.review has no raw_fields escape",
                    )
                if (
                    inferred_type == "ipd"
                    and reg_name == "plan_role"
                    and _is_known_ipd_non_skeleton_role(effective_static)
                ):
                    raw_fields_code[orig_label] = repr(effective_static)
                    continue
                raw_fields_code[orig_label] = repr(effective_static)
                has_invalid_input = True
                continue
            if reg_name == "order":
                kwargs_code["order"] = str(int(effective_static))
                continue
            kwargs_code[reg_name] = effective_code
        else:
            kwargs_code[reg_name] = effective_code

    # Review records with non-empty body/findings tables are refused (RecordBuilder.review
    # takes structured Round objects, not raw markdown tables).
    if inferred_type == "review":
        if "subject" not in kwargs_code:
            return refuse("unsupported-shape", "review record missing Subject-Id")
        if body_tpl and re.search(r"(?m)^\|\s*[A-Z]", body_tpl):
            return refuse(
                "unsupported-shape",
                "review record with structured findings/decisions table",
            )

    # History section
    if history_entries is not None and "history" in method_params:
        kwargs_code["history"] = "[" + ", ".join(h.code for h in history_entries) + "]"

    # Open questions section (IPD)
    if open_questions_tpl is not None and "open_questions" in method_params:
        oq_vexpr = _template_to_value_expr(open_questions_tpl, fvs, strip_val=False)
        if oq_vexpr is None:
            return refuse(
                "dynamic-construction", "unsupported expression in Open questions"
            )
        kwargs_code["open_questions"] = oq_vexpr.code

    # Body sections
    if body_tpl and body_tpl.strip() and "body" in method_params:
        body_for_builder = body_tpl
        if inferred_type == "release":
            ver_expr = kwargs_code.get("version", "'1.0.0'")
            # Prepend heading when custom body is passed to RecordBuilder.release
            if not body_for_builder.lstrip().startswith("# "):
                if ver_expr.startswith(("'", '"')) and ver_expr.endswith(("'", '"')):
                    ver_plain = ast.literal_eval(ver_expr)
                    body_for_builder = f"# Release: {ver_plain}\n\n{body_for_builder}"
                else:
                    return refuse(
                        "unsupported-shape",
                        "release with custom body and dynamic version",
                    )
        elif (
            inferred_type == "walkthrough"
            and not body_for_builder.lstrip().startswith("# ")
        ):
            set_expr = kwargs_code.get("set", "'demo'")
            if set_expr.startswith(("'", '"')) and set_expr.endswith(("'", '"')):
                set_plain = ast.literal_eval(set_expr)
                body_for_builder = f"# Walkthrough: {set_plain}\n\n{body_for_builder}"
        body_vexpr = _template_to_value_expr(body_for_builder, fvs, strip_val=False)
        if body_vexpr is None:
            return refuse("dynamic-construction", "unsupported expression in body")
        kwargs_code["body"] = body_vexpr.code

    # Emit raw_fields= if populated.
    if raw_fields_code:
        rf_items = ", ".join(f"{k!r}: {v}" for k, v in raw_fields_code.items())
        kwargs_code["raw_fields"] = "{" + rf_items + "}"

    # Build final replacement expression: RecordBuilder().<method>(..., text_only=True)
    call_args: list[str] = []
    if inferred_type == "review":
        call_args.append(f"subject={kwargs_code['subject']}")
    for k, v in kwargs_code.items():
        if inferred_type == "review" and k == "subject":
            continue
        call_args.append(f"{k}={v}")
    call_args.append("text_only=True")
    replacement = f"RecordBuilder().{method_name}(" + ", ".join(call_args) + ")"

    # Validate generated expression syntax before accepting it as a planned rewrite.
    try:
        ast.parse(replacement, mode="eval")
    except SyntaxError as exc:
        return refuse("unsupported-shape", f"generated call invalid syntax: {exc}")

    return SiteResult(
        line=line,
        end_line=end_line,
        col=col,
        end_col=end_col,
        action="rewrite",
        rewrite_class="invalid-input" if has_invalid_input else "standard",
        record_type=inferred_type,
        method=method_name,
        kwargs=kwargs_code,
        raw_fields=raw_fields_code,
        replacement=replacement,
        reason=None,
        disposition=None,
        detail="",
    )


def analyze_module(module_path: Path) -> tuple[ModuleResult, str, ast.Module]:
    """Parse and analyze one test module without mutating it."""
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    docstrings = _collect_docstring_nodes(tree)
    parents = _build_parent_map(tree)
    rb_names = _collect_record_builder_var_names(tree)
    candidates = _collect_candidate_sites(tree, docstrings, rb_names)

    scope_cache: dict[int, _ScopeIndex] = {}
    sites: list[SiteResult] = []
    for node, site_kind in candidates:
        scope_node, func_name = _enclosing_scope(node, parents)
        sid = id(scope_node)
        if sid not in scope_cache:
            scope_cache[sid] = _ScopeIndex(scope_node)
        site = _plan_site(
            node,
            site_kind,
            module_path,
            parents,
            scope_cache[sid],
            func_name,
        )
        sites.append(site)

    rel_label = _display_path(module_path)
    return ModuleResult(module=rel_label, sites=sites), source, tree


def _display_path(path: Path) -> str:
    """Render path relative to current working directory when inside it."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# --------------------------------------------------------------------------------------
# E-02: In-Place AST Span Rewriter and Import Insertion
# --------------------------------------------------------------------------------------


def _has_record_builder_import(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "tests.record_builder":
            for alias in node.names:
                if alias.name == "RecordBuilder" and alias.asname is None:
                    return True
    return False


def _import_insert_line(tree: ast.Module, lines: list[bytes]) -> int:
    """Return 0-based line index after which to insert RecordBuilder import."""
    last_import_end: int | None = None
    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            end_ln = getattr(stmt, "end_lineno", stmt.lineno)
            last_import_end = end_ln
        elif last_import_end is not None:
            break
    if last_import_end is not None:
        return last_import_end

    # No top-level imports: insert after module docstring if present, else after shebang/comments.
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        return getattr(tree.body[0], "end_lineno", tree.body[0].lineno)

    idx = 0
    while idx < len(lines) and (lines[idx].startswith(b"#") or not lines[idx].strip()):
        idx += 1
    return idx


def _line_byte_offsets(raw_bytes: bytes) -> list[int]:
    """Return 1-indexed start byte offsets for every line in raw_bytes."""
    offsets: list[int] = [0, 0]  # index 0 unused, line 1 starts at byte 0
    pos = 0
    for ln in raw_bytes.splitlines(keepends=True):
        pos += len(ln)
        offsets.append(pos)
    return offsets


def apply_rewrites_to_source(
    source: str,
    tree: ast.Module,
    rewrites: Sequence[SiteResult],
) -> str:
    """Apply exact AST-span replacements and add RecordBuilder import when needed.

    Touches only the selected AST node byte spans and (if missing) a single import line.
    """
    if not rewrites:
        return source

    raw = source.encode("utf-8")
    line_offsets = _line_byte_offsets(raw)

    # Convert each SiteResult's (lineno, col_offset, end_lineno, end_col_offset) to byte spans.
    edits: list[tuple[int, int, bytes]] = []
    for site in rewrites:
        assert site.replacement is not None
        start_b = line_offsets[site.line] + site.col
        end_b = line_offsets[site.end_line] + site.end_col
        edits.append((start_b, end_b, site.replacement.encode("utf-8")))

    # Add import insertion edit if module lacks it.
    if not _has_record_builder_import(tree):
        raw_lines = raw.splitlines(keepends=True)
        insert_after = _import_insert_line(tree, raw_lines)
        insert_byte = (
            line_offsets[insert_after + 1]
            if (insert_after + 1) < len(line_offsets)
            else len(raw)
        )
        import_line = b"from tests.record_builder import RecordBuilder\n"
        if insert_byte > 0 and not raw[:insert_byte].endswith(b"\n"):
            import_line = b"\n" + import_line
        edits.append((insert_byte, insert_byte, import_line))

    # Apply edits from highest byte offset to lowest so earlier offsets stay exact.
    edits.sort(key=lambda e: (e[0], e[1]), reverse=True)
    buf = bytearray(raw)
    for start_b, end_b, repl_b in edits:
        buf[start_b:end_b] = repl_b
    return buf.decode("utf-8")


# --------------------------------------------------------------------------------------
# E-03: Mandatory Equivalence Proof & Halving Bisection
# --------------------------------------------------------------------------------------


def _pytest_workdir_and_env() -> tuple[Path, dict[str, str]]:
    """Choose a working directory and PYTHONPATH where tests.record_builder imports."""
    cwd = Path.cwd().resolve()
    if (cwd / "tests" / "record_builder.py").is_file():
        run_root = cwd
    else:
        run_root = REPO_ROOT
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    parts = [str(run_root)] + ([existing] if existing else [])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return run_root, env


def record_module_outcomes(module_path: Path) -> tuple[list[str], str]:
    """Run the batch-rule pytest command in-process and return (sorted outcomes, sha256)."""
    run_root, env = _pytest_workdir_and_env()
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-m",
        "",
        "-p",
        "no:randomly",
        "-n",
        "0",
        "-rA",
        str(module_path.resolve()),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(run_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    outcomes: list[str] = []
    for raw_line in proc.stdout.splitlines():
        if _OUTCOME_LINE_RE.match(raw_line):
            outcomes.append(re.sub(r" - .*", "", raw_line))
    outcomes.sort()
    # Guard against collection/syntax/import failures producing no outcome lines.
    if proc.returncode in (2, 3, 4) and not any(
        line.startswith("ERROR ") for line in outcomes
    ):
        outcomes.append(f"__PYTEST_COLLECTION_ERROR_RC_{proc.returncode}__")
    digest = hashlib.sha256("\n".join(outcomes).encode("utf-8")).hexdigest()
    return outcomes, digest


def apply_and_prove_module(module_path: Path) -> ModuleResult:
    """Rewrite planned sites in module_path and prove outcome-list equivalence.

    Equivalence proof cannot be disabled. Any site whose rewrite alters the
    module's sorted pytest outcome list is isolated by halving, reverted, and
    reported with reason ``not-equivalent`` (disposition ``hand``).
    """
    result, original_source, tree = analyze_module(module_path)
    result.applied = True
    planned = [s for s in result.sites if s.action == "rewrite"]

    if not planned:
        result.changed = False
        result.proof = ProofResult(
            before_hash=None,
            after_hash=None,
            equivalent=True,
            pytest_runs=0,
        )
        return result

    original_bytes = module_path.read_bytes()
    pytest_runs = 0

    def _run_outcomes() -> tuple[list[str], str]:
        nonlocal pytest_runs
        pytest_runs += 1
        return record_module_outcomes(module_path)

    def _write_subset(subset: Sequence[SiteResult]) -> str:
        if not subset:
            module_path.write_bytes(original_bytes)
            return original_source
        new_src = apply_rewrites_to_source(original_source, tree, subset)
        module_path.write_text(new_src, encoding="utf-8")
        return new_src

    try:
        before_outcomes, before_hash = _run_outcomes()

        # First attempt: apply all planned rewrites at once.
        _write_subset(planned)
        after_outcomes, after_hash = _run_outcomes()

        if after_outcomes == before_outcomes:
            result.changed = module_path.read_bytes() != original_bytes
            result.proof = ProofResult(
                before_hash=before_hash,
                after_hash=after_hash,
                equivalent=True,
                pytest_runs=pytest_runs,
            )
            return result

        # Outcome list differed: restore and isolate breaking sites by halving.
        module_path.write_bytes(original_bytes)
        confirmed: list[SiteResult] = []
        not_equivalent: list[SiteResult] = []
        last_verified_subset: tuple[int, ...] | None = ()
        last_verified_hash = before_hash

        def _mark_not_equiv(site: SiteResult) -> None:
            site.action = "refuse"
            site.rewrite_class = None
            site.reason = "not-equivalent"
            site.disposition = REASON_DISPOSITION["not-equivalent"]
            site.detail = "rewriting this site altered the module pytest outcome list"
            not_equivalent.append(site)

        def _prove_subset(candidates: list[SiteResult]) -> None:
            nonlocal last_verified_subset, last_verified_hash
            if not candidates:
                return
            trial = confirmed + candidates
            _write_subset(trial)
            trial_outcomes, trial_hash = _run_outcomes()
            if trial_outcomes == before_outcomes:
                confirmed.extend(candidates)
                last_verified_subset = tuple(id(s) for s in confirmed)
                last_verified_hash = trial_hash
                return
            if len(candidates) == 1:
                _mark_not_equiv(candidates[0])
                return
            mid = len(candidates) // 2
            _prove_subset(candidates[:mid])
            _prove_subset(candidates[mid:])

        if len(planned) == 1:
            _mark_not_equiv(planned[0])
        else:
            mid = len(planned) // 2
            _prove_subset(planned[:mid])
            _prove_subset(planned[mid:])

        # Write final confirmed subset (or restore original bytes if none survived).
        _write_subset(confirmed)
        confirmed_key = tuple(id(s) for s in confirmed)
        if last_verified_subset == confirmed_key:
            final_hash = last_verified_hash
            final_eq = final_hash == before_hash
        else:
            final_outcomes, final_hash = _run_outcomes()
            final_eq = final_outcomes == before_outcomes
            if not final_eq:
                # Fail closed: never keep an unproved edit.
                module_path.write_bytes(original_bytes)
                for site in confirmed:
                    _mark_not_equiv(site)
                final_hash = before_hash
                final_eq = True

        result.changed = module_path.read_bytes() != original_bytes
        result.proof = ProofResult(
            before_hash=before_hash,
            after_hash=final_hash,
            equivalent=final_eq,
            pytest_runs=pytest_runs,
        )
        return result
    except BaseException:
        # Never leave a module partially mutated on interruption or unexpected error.
        module_path.write_bytes(original_bytes)
        raise


# --------------------------------------------------------------------------------------
# Aggregation & Formatting (table, json, census-markdown)
# --------------------------------------------------------------------------------------


def aggregate_results(
    mode: str, module_results: Sequence[ModuleResult]
) -> dict[str, Any]:
    by_reason: dict[str, int] = {rc: 0 for rc in REASON_CODES}
    by_disposition: dict[str, int] = {"hand": 0, "legacy-kept": 0}
    total_sites = 0
    total_rewrites = 0
    total_standard = 0
    total_invalid = 0
    total_refusals = 0
    outcome_hashes: list[dict[str, Any]] = []

    for mod in module_results:
        t = mod.totals()
        total_sites += t["sites"]
        total_rewrites += t["rewrites"]
        total_standard += t["standard_rewrites"]
        total_invalid += t["invalid_input_rewrites"]
        total_refusals += t["refusals"]
        for rc in REASON_CODES:
            by_reason[rc] += t["by_reason"][rc]
        for disp in ("hand", "legacy-kept"):
            by_disposition[disp] += t["by_disposition"][disp]
        if mode == "apply":
            outcome_hashes.append(
                {
                    "module": mod.module,
                    "before_hash": mod.proof.before_hash,
                    "after_hash": mod.proof.after_hash,
                    "equivalent": mod.proof.equivalent,
                }
            )

    return {
        "mode": mode,
        "modules": [m.to_dict() for m in module_results],
        "totals": {
            "modules": len(module_results),
            "sites": total_sites,
            "rewrites": total_rewrites,
            "standard_rewrites": total_standard,
            "invalid_input_rewrites": total_invalid,
            "refusals": total_refusals,
            "by_reason": by_reason,
            "by_disposition": by_disposition,
        },
        "outcome_hashes": outcome_hashes,
    }


def format_table(report: dict[str, Any]) -> str:
    lines: list[str] = []
    mode = report["mode"]
    for mod in report["modules"]:
        lines.append(f"Module: {mod['module']}")
        if not mod["sites"]:
            lines.append("  (no F-01 sites detected)")
        else:
            lines.append(
                f"  {'Line':<6} {'Action':<8} {'Target / Reason':<28} {'Disposition':<12} Details"
            )
            lines.append("  " + "-" * 86)
            for s in mod["sites"]:
                if s["action"] == "rewrite":
                    target = f"{s['record_type']} ({s['rewrite_class']})"
                    disp = "-"
                    kw_summary = ", ".join(sorted(s["kwargs"].keys()))
                    if s["raw_fields"]:
                        kw_summary += f" | raw_fields={sorted(s['raw_fields'].keys())}"
                    details = f"RecordBuilder().{s['method']}({kw_summary})"
                else:
                    target = s["reason"] or "unknown"
                    disp = s["disposition"] or "-"
                    details = s["detail"]
                lines.append(
                    f"  {s['line']:<6} {s['action']:<8} {target:<28} {disp:<12} {details}"
                )
        mt = mod["totals"]
        reason_parts = (
            ", ".join(
                f"{rc}={mt['by_reason'][rc]}"
                for rc in REASON_CODES
                if mt["by_reason"][rc] > 0
            )
            or "none"
        )
        lines.append(
            f"  Totals: sites={mt['sites']} rewrites={mt['rewrites']} "
            f"(standard={mt['standard_rewrites']}, invalid-input={mt['invalid_input_rewrites']}) "
            f"refusals={mt['refusals']} [{reason_parts}]"
        )
        lines.append(
            f"  Dispositions: hand={mt['by_disposition']['hand']} "
            f"legacy-kept={mt['by_disposition']['legacy-kept']}"
        )
        lines.append("")

    gt = report["totals"]
    lines.append("Overall totals:")
    lines.append(
        f"  modules={gt['modules']} sites={gt['sites']} rewrites={gt['rewrites']} "
        f"(standard={gt['standard_rewrites']}, invalid-input={gt['invalid_input_rewrites']}) "
        f"refusals={gt['refusals']}"
    )
    lines.append("  Refusals by reason:")
    for rc in REASON_CODES:
        lines.append(
            f"    {rc:<28} ({REASON_DISPOSITION[rc]:<11}): {gt['by_reason'][rc]}"
        )
    lines.append(
        f"  Per-disposition totals: hand={gt['by_disposition']['hand']} "
        f"legacy-kept={gt['by_disposition']['legacy-kept']}"
    )

    if mode == "apply":
        lines.append("")
        lines.append("Outcome-list hashes:")
        for entry in report["outcome_hashes"]:
            bh = entry["before_hash"] or "unchanged"
            ah = entry["after_hash"] or "unchanged"
            eq = "yes" if entry["equivalent"] else "no"
            lines.append(f"  {entry['module']}: before={bh} after={ah} equivalent={eq}")

    return "\n".join(lines)


def format_census_markdown(report: dict[str, Any]) -> str:
    header = (
        "| Module | Sites | Rewrites | Invalid-Input | dynamic-construction | "
        "unsupported-shape | not-equivalent | legacy-format subject | "
        "displayed-output assertion | setter-byte assertion | body prose | "
        "Hand | Legacy-Kept |"
    )
    sep = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    rows: list[str] = [header, sep]
    for mod in report["modules"]:
        t = mod["totals"]
        br = t["by_reason"]
        bd = t["by_disposition"]
        rows.append(
            f"| `{mod['module']}` | {t['sites']} | {t['rewrites']} | "
            f"{t['invalid_input_rewrites']} | {br['dynamic-construction']} | "
            f"{br['unsupported-shape']} | {br['not-equivalent']} | "
            f"{br['legacy-format subject']} | {br['displayed-output assertion']} | "
            f"{br['setter-byte assertion']} | {br['body prose']} | "
            f"{bd['hand']} | {bd['legacy-kept']} |"
        )
    gt = report["totals"]
    gbr = gt["by_reason"]
    gbd = gt["by_disposition"]
    rows.append(
        f"| **Total ({gt['modules']} modules)** | {gt['sites']} | {gt['rewrites']} | "
        f"{gt['invalid_input_rewrites']} | {gbr['dynamic-construction']} | "
        f"{gbr['unsupported-shape']} | {gbr['not-equivalent']} | "
        f"{gbr['legacy-format subject']} | {gbr['displayed-output assertion']} | "
        f"{gbr['setter-byte assertion']} | {gbr['body prose']} | "
        f"{gbd['hand']} | {gbd['legacy-kept']} |"
    )
    return "\n".join(rows)


# --------------------------------------------------------------------------------------
# CLI Entry Point
# --------------------------------------------------------------------------------------


def _expand_paths(raw_paths: Sequence[str]) -> list[Path]:
    resolved: list[Path] = []
    seen: set[Path] = set()
    for raw in raw_paths:
        p = Path(raw)
        if p.is_dir():
            for child in sorted(p.rglob("*.py")):
                rp = child.resolve()
                if rp not in seen:
                    seen.add(rp)
                    resolved.append(child)
        else:
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                resolved.append(p)
    return resolved


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Detect, rewrite, and prove behavioral equivalence for legacy test "
            "fixture string literals using tests.record_builder.RecordBuilder."
        )
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze modules and print planned rewrites and refusals without writing.",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Rewrite planned sites in place and prove per-module pytest outcome "
            "equivalence (always enabled; isolates breaking sites as not-equivalent)."
        ),
    )
    mode_group.add_argument(
        "--census-markdown",
        action="store_true",
        help="Run dry-run analysis and emit a Markdown census table.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for --dry-run and --apply (default: table).",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more Python test module paths (or directories of .py files).",
    )

    args = parser.parse_args(argv)
    targets = _expand_paths(args.paths)

    for target in targets:
        if not target.is_file():
            print(f"error: file not found: {target}", file=sys.stderr)
            return 2

    mode = "apply" if args.apply else "dry-run"
    results: list[ModuleResult] = []

    for target in targets:
        if args.apply:
            mod_res = apply_and_prove_module(target)
        else:
            mod_res, _, _ = analyze_module(target)
        results.append(mod_res)

    report = aggregate_results(mode, results)

    if args.census_markdown:
        print(format_census_markdown(report))
    elif args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_table(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
