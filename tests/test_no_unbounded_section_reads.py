"""Guard test refusing marker-located unbounded section reads in test modules (IPD jj5ju1).

SCOPE: tests/test_*.py and named helpers (tests/support.py, tests/conformance_matrix.py).
Excludes the guard's own file structurally (by Path(__file__).resolve() identity) because
the detector itself parses and walks ASTs.
Excludes fixture modules under tests/fixtures/ and tests/benchmark_fixtures/,
as these contain synthetic sample code for external repository scenarios rather than
this suite's own assertions.

EXEMPTIONS: Typed per-site comments spelled `# aw-unbounded-ok: <reason>`.
The exemption mechanism is self-cleaning: every exemption comment in the discovery set
must sit on a line that the detector would otherwise flag when exemptions are ignored,
and must carry a non-empty reason.

BOUNDS AND KNOWN HOLES:
(a) INTERPROCEDURAL BOUND:
    Marker index tracking is bounded to within a single function body (ast.FunctionDef or
    ast.AsyncFunctionDef). An index computed in one function and consumed in an unbounded
    slice in another function evades this analyzer. The census of all live sites in the
    repository confirmed that 100% of live instances bind and consume within a single
    function, so single-function tracking resolves the design problem without interprocedural
    complexity (F-02, GUIDING_PRINCIPLES.md P6).

(b) NON-MARKER-OFFSET BOUND:
    Unbounded reads that obtain a start offset through mechanisms other than marker search
    (such as regex match.end(), an enumerate/startswith loop, a partition() tail, or a
    hard-coded constant integer) evade this syntactic check. For evasive patterns,
    GUIDING_PRINCIPLES.md P16 and /plan-review provide standing human review coverage.

(c) FIXTURE DIRECTORIES EXCLUDED:
    Fixture modules under tests/fixtures/ and tests/benchmark_fixtures/ are excluded from
    the discovery set as synthetic sample code.

(d) SEMANTIC MARKER CORRECTNESS:
    A syntactic check cannot decide whether a bounded section read uses the correct marker
    or bounds to the intended section.
"""

from __future__ import annotations

import ast
import io
from pathlib import Path
import re
import tokenize
from typing import NamedTuple

SEARCH_ATTRS: set[str] = {"find", "rfind", "index", "rindex"}
EXEMPTION_RE = re.compile(r"^#\s*aw-unbounded-ok(?::\s*(.*))?$")


class UnboundedSectionReadViolation(NamedTuple):
    file_path: str
    lineno: int
    expr: str
    arm: str
    remedy: str = (
        "use support.section for a bounded read, support.final_section to declare a terminal one, "
        "or '# aw-unbounded-ok: <reason>' if unboundedness is the assertion."
    )
    stmt_lineno: int = 0
    stmt_end_lineno: int = 0

    def render(self) -> str:
        return (
            f"{self.file_path}:{self.lineno}: unbounded section read via {self.expr} [{self.arm}]. "
            f"Remedy: {self.remedy}"
        )


def extract_exemptions(source: str) -> tuple[dict[int, str], list[tuple[int, str]]]:
    """Extract valid and invalid exemption comments from source text using tokenize.

    Returns:
        (valid_exemptions_by_line, invalid_exemptions_list)
        where invalid_exemptions contains (lineno, raw_reason) for malformed or empty-reason comments.
    """
    valid_exemptions: dict[int, str] = {}
    invalid_exemptions: list[tuple[int, str]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comment_text = tok.string.strip()
                if "aw-unbounded-ok" in comment_text:
                    m = EXEMPTION_RE.match(comment_text)
                    if m and m.group(1) is not None and m.group(1).strip():
                        valid_exemptions[tok.start[0]] = m.group(1).strip()
                    else:
                        reason = m.group(1).strip() if (m and m.group(1)) else ""
                        invalid_exemptions.append((tok.start[0], reason))
    except (tokenize.TokenError, IndentationError):
        pass
    return valid_exemptions, invalid_exemptions


def attach_parents(tree: ast.AST) -> None:
    """Attach parent reference to each child node in AST for upwards navigation."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent  # type: ignore[attr-defined]


def find_enclosing_statement(node: ast.AST) -> ast.AST:
    """Find the enclosing statement node for an expression."""
    curr = node
    while hasattr(curr, "parent") and not isinstance(curr, ast.stmt):
        curr = curr.parent  # type: ignore[attr-defined]
    return curr


def has_search_call(node: ast.AST) -> bool:
    """Return True if any Call node in subtree invokes find/rfind/index/rindex."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
            if sub.func.attr in SEARCH_ATTRS:
                return True
    return False


def is_complementary_reconstruction(subscript_node: ast.Subscript) -> bool:
    """Check if tail slice is an operand in a string concatenation with a matching head slice.

    Recognizes lossless text rejoining such as `t[:idx] + block + t[idx:]` or `t[:idx] + t[idx:]`,
    comparing subject and index expressions by unparsed syntax (E-04).
    """
    curr: ast.AST = subscript_node
    while (
        hasattr(curr, "parent")
        and isinstance(curr.parent, ast.BinOp)  # type: ignore[attr-defined]
        and isinstance(curr.parent.op, ast.Add)  # type: ignore[attr-defined]
    ):
        curr = curr.parent  # type: ignore[attr-defined]

    if curr is subscript_node:
        return False

    def flatten_adds(n: ast.AST) -> list[ast.AST]:
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            return flatten_adds(n.left) + flatten_adds(n.right)
        return [n]

    operands = flatten_adds(curr)
    subj_str = ast.unparse(subscript_node.value)
    idx_str = (
        ast.unparse(subscript_node.slice.lower)  # type: ignore[attr-defined]
        if subscript_node.slice.lower  # type: ignore[attr-defined]
        else ""
    )

    for op in operands:
        if op is subscript_node:
            continue
        if isinstance(op, ast.Subscript) and isinstance(op.slice, ast.Slice):
            if op.slice.upper is not None and (
                op.slice.lower is None
                or (
                    isinstance(op.slice.lower, ast.Constant)
                    and op.slice.lower.value == 0
                )
            ):
                if (
                    ast.unparse(op.value) == subj_str
                    and ast.unparse(op.slice.upper) == idx_str
                ):
                    return True
    return False


def scan_source_for_unbounded_section_reads(
    source: str, filename: str = "<string>", *, ignore_exemptions: bool = False
) -> list[UnboundedSectionReadViolation]:
    """Parse python source and return any unbounded section read violations (IPD jj5ju1)."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []

    attach_parents(tree)
    valid_exemptions, _ = extract_exemptions(source)
    violations: list[UnboundedSectionReadViolation] = []

    # Arms A and B: evaluate per function definition
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Collect variable names assigned from marker-search calls within fn body
        marker_bound_vars: set[str] = set()
        for node in ast.walk(fn):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node is not fn
            ):
                continue
            if isinstance(node, ast.Assign):
                if has_search_call(node.value):
                    for target in node.targets:
                        for n in ast.walk(target):
                            if isinstance(n, ast.Name):
                                marker_bound_vars.add(n.id)
            elif isinstance(node, ast.AnnAssign):
                if node.value and has_search_call(node.value):
                    for n in ast.walk(node.target):
                        if isinstance(n, ast.Name):
                            marker_bound_vars.add(n.id)
            elif isinstance(node, ast.NamedExpr):
                if has_search_call(node.value):
                    for n in ast.walk(node.target):
                        if isinstance(n, ast.Name):
                            marker_bound_vars.add(n.id)

        # Scan for unbounded slices
        for node in ast.walk(fn):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node is not fn
            ):
                continue

            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
                if node.slice.upper is None and node.slice.lower is not None:
                    arm: str | None = None
                    if has_search_call(node.slice.lower):
                        arm = "A-inline"
                    else:
                        for n in ast.walk(node.slice.lower):
                            if isinstance(n, ast.Name) and n.id in marker_bound_vars:
                                arm = "B-bound"
                                break

                    if arm:
                        if not is_complementary_reconstruction(node):
                            stmt = find_enclosing_statement(node)
                            stmt_start = getattr(stmt, "lineno", node.lineno)
                            stmt_end = getattr(stmt, "end_lineno", stmt_start)
                            is_exempt = not ignore_exemptions and any(
                                ln in valid_exemptions
                                for ln in range(stmt_start, stmt_end + 1)
                            )
                            if not is_exempt:
                                violations.append(
                                    UnboundedSectionReadViolation(
                                        file_path=filename,
                                        lineno=node.lineno,
                                        expr=ast.unparse(node),
                                        arm=arm,
                                        stmt_lineno=stmt_start,
                                        stmt_end_lineno=stmt_end,
                                    )
                                )

    # Split arm: evaluate all Subscript nodes across the module
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            if (
                isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, int)
                and node.slice.value >= 1
            ):
                if (
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr in {"split", "rsplit"}
                ):
                    if node.value.args:
                        first_arg = node.value.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(
                            first_arg.value, str
                        ):
                            val = first_arg.value.lstrip("\r\n")
                            if val.startswith("#"):
                                stmt = find_enclosing_statement(node)
                                stmt_start = getattr(stmt, "lineno", node.lineno)
                                stmt_end = getattr(stmt, "end_lineno", stmt_start)
                                is_exempt = not ignore_exemptions and any(
                                    ln in valid_exemptions
                                    for ln in range(stmt_start, stmt_end + 1)
                                )
                                if not is_exempt:
                                    violations.append(
                                        UnboundedSectionReadViolation(
                                            file_path=filename,
                                            lineno=node.lineno,
                                            expr=ast.unparse(node),
                                            arm="split-heading",
                                            stmt_lineno=stmt_start,
                                            stmt_end_lineno=stmt_end,
                                        )
                                    )

    return violations


def discover_test_modules(repo_root: Path) -> list[Path]:
    """Discover test modules and named shared helpers, excluding fixture directories."""
    tests_dir = repo_root / "tests"
    modules: list[Path] = []
    own_path = Path(__file__).resolve()

    for p in sorted(tests_dir.rglob("test_*.py")):
        if "fixtures" in p.parts or "benchmark_fixtures" in p.parts:
            continue
        if p.resolve() == own_path:
            continue
        modules.append(p)

    for helper_name in ("support.py", "conformance_matrix.py"):
        helper_path = tests_dir / helper_name
        if helper_path.is_file() and helper_path.resolve() != own_path:
            modules.append(helper_path)

    return modules


def test_no_unbounded_section_reads_in_test_modules() -> None:
    """Scan test modules in discovery set and assert zero unexempted unbounded section reads."""
    repo_root = Path(__file__).resolve().parent.parent
    test_modules = discover_test_modules(repo_root)

    all_violations: list[UnboundedSectionReadViolation] = []
    for mod_path in test_modules:
        rel_path = str(mod_path.relative_to(repo_root))
        source = mod_path.read_text(encoding="utf-8")
        violations = scan_source_for_unbounded_section_reads(source, filename=rel_path)
        all_violations.extend(violations)

    assert not all_violations, (
        f"Found {len(all_violations)} unexempted unbounded section read(s) in tests:\n"
        + "\n".join(v.render() for v in all_violations)
    )


def test_exemption_comments_are_valid_and_non_stale() -> None:
    """Every # aw-unbounded-ok comment must have a non-empty reason and match a raw violation.

    Calls the pure detector with ignore_exemptions=True so the check is non-vacuous.
    A stale exemption (line converted or removed) or an empty reason fails loudly.
    """
    repo_root = Path(__file__).resolve().parent.parent
    test_modules = discover_test_modules(repo_root)

    for mod_path in test_modules:
        rel_path = str(mod_path.relative_to(repo_root))
        source = mod_path.read_text(encoding="utf-8")

        valid_exemptions, invalid_exemptions = extract_exemptions(source)
        assert not invalid_exemptions, (
            f"Found malformed exemption comment(s) with empty or missing reason in {rel_path}:\n"
            + "\n".join(
                f"  line {ln}: '# aw-unbounded-ok: {r}'" for ln, r in invalid_exemptions
            )
        )

        if not valid_exemptions:
            continue

        raw_violations = scan_source_for_unbounded_section_reads(
            source, filename=rel_path, ignore_exemptions=True
        )
        flagged_lines: set[int] = set()
        for v in raw_violations:
            start = v.stmt_lineno if v.stmt_lineno else v.lineno
            end = v.stmt_end_lineno if v.stmt_end_lineno else v.lineno
            flagged_lines.update(range(start, end + 1))

        for ln, reason in valid_exemptions.items():
            assert ln in flagged_lines, (
                f"Stale or misplaced exemption comment at {rel_path}:{ln}: "
                f"no unbounded section read detected on this line (reason: {reason}). "
                f"Remove dead exemption comment."
            )


# ======================================================================================
# Positive Fixtures (prove each detector arm fires)
# ======================================================================================


def test_positive_arm_a_inline_slice() -> None:
    src = "def test_fn():\n    return out[out.index('## Sets'):]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_pos.py")
    assert len(v) == 1
    assert v[0].arm == "A-inline"
    assert "out.index('## Sets')" in v[0].expr
    assert "support.section" in v[0].render()


def test_positive_arm_b_bound_slice() -> None:
    src = "def test_fn():\n    start = prompt.find('## Heading')\n    return prompt[start:]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_pos.py")
    assert len(v) == 1
    assert v[0].arm == "B-bound"
    assert "prompt[start:]" in v[0].expr


def test_positive_split_arm_index_one() -> None:
    src = "def test_fn():\n    return text.split('## Workflow history', 1)[1]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_pos.py")
    assert len(v) == 1
    assert v[0].arm == "split-heading"
    assert "split('## Workflow history', 1)[1]" in v[0].expr


def test_positive_split_arm_index_two() -> None:
    src = "def test_fn():\n    return text.split('## Section', 2)[2]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_pos.py")
    assert len(v) == 1
    assert v[0].arm == "split-heading"


def test_positive_slice_not_in_reconstruction() -> None:
    src = (
        "def test_fn():\n    start = prompt.find('M')\n    x = prompt[start:] + '\\n'\n"
    )
    v = scan_source_for_unbounded_section_reads(src, filename="test_pos.py")
    assert len(v) == 1
    assert v[0].arm == "B-bound"


def test_positive_mismatched_rejoin_is_flagged() -> None:
    src = "def test_fn():\n    i = t.index('a')\n    j = u.index('b')\n    return t[:i] + u[j:]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_pos.py")
    assert len(v) == 1
    assert v[0].arm == "B-bound"


# ======================================================================================
# Negative Fixtures (prove bounded shapes and exclusions are silent)
# ======================================================================================


def test_negative_bounded_slice_silent() -> None:
    src = "def test_fn():\n    return x[x.index('a'):x.index('b')]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_bare_tail_slice_silent() -> None:
    src = "def test_fn():\n    return lines[1:]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_search_derived_upper_bound_silent() -> None:
    src = "def test_fn():\n    return x[:x.index('## End')]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_split_field_delimiter_colon_silent() -> None:
    src = "def test_fn():\n    return text.split(':')[1]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_split_field_delimiter_dot_space_silent() -> None:
    src = "def test_fn():\n    return text.split('. ')[1]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_split_non_literal_separator_silent() -> None:
    src = "def test_fn():\n    sep = compute_sep()\n    return text.split(sep)[1]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_split_heading_index_zero_silent() -> None:
    src = "def test_fn():\n    return text.split('## Workflow history')[0]\n"
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_complementary_reconstruction_three_operand_silent() -> None:
    src = (
        "def test_fn():\n"
        "    idx = t.index('marker')\n"
        "    return t[:idx] + block + t[idx:]\n"
    )
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0


def test_negative_complementary_reconstruction_two_operand_silent() -> None:
    src = (
        "def test_fn():\n"
        "    idx = t.index('marker')\n"
        "    return t[:idx] + t[idx:]\n"
    )
    v = scan_source_for_unbounded_section_reads(src, filename="test_neg.py")
    assert len(v) == 0
