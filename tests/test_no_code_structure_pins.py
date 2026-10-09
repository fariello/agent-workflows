"""Guard test refusing production-source reads and code-structure pins in test modules.

SCOPE: tests/test_*.py and named helpers (tests/support.py, tests/conformance_matrix.py).
Excludes the guard's own file structurally (by Path(__file__).resolve() identity) because
the detector itself calls ast.parse and ast.walk to inspect ASTs.
Excludes fixture modules under tests/fixtures/ and tests/benchmark_fixtures/ (13 files),
as these contain synthetic sample code for external repository scenarios rather than
this suite's own assertions.

ALLOWLIST: Exactly one typed entry with documented rationale:
  - tests/test_carrier_scan_single_item_contract.py (quadratic-performance hazard scanner)
The allowlist is self-cleaning: every entry must exist on disk and contain at least one
flagged call, or the suite fails.

BOUNDS AND KNOWN HOLES:
(a) DOES NOT FLAG read_text():
    While GUIDING_PRINCIPLES.md P16 prohibits reading production source with read_text(),
    this guard does not flag read_text(). In tests, read_text() is predominantly used to
    read test fixtures created in temporary directories (141 test files call read_text while
    mentioning agent_workflows). Distinguishing fixture reads from production package reads
    in general requires dataflow analysis. The syntactically decidable subset where the
    receiver expression itself names the package resolves to exactly three live call sites:
      - tests/test_leak_sanitizer.py:100 (REPO_ROOT / "agent_workflows" / "leak_sanitizer.py")
      - tests/test_local_leaks.py:118 (REPO_ROOT / "agent_workflows" / "local_leaks.py")
      - tests/test_artifact_adopt.py:672 (Path(__file__).read_text)
    All three are legitimate self-scan or engine-self-clean tests that a read_text rule
    would have to allowlist anyway. Thus, flagging read_text would cost an allowlist and
    buy nothing today.

(b) DOES NOT FLAG COUNT-SHAPED ASSERTIONS:
    Asserting on counts (e.g. assertEqual(len(x), 3)) is syntactically indistinguishable
    from legitimate assertions on behavioral outputs. Furthermore, the repository has
    legitimate literal censuses (such as subcommands in tests/test_releases_cli.py or flag
    surfaces in tests/test_runner_shared.py) that must not be broken. The guard instead
    closes the source-reading route through inspect and ast that pins used to inspect
    source structure in the first place.

(c) NOT A PROOF OF ABSENCE:
    A pin written through importlib, bare-name imports (from inspect import getsource),
    __code__ introspection, or compile() over source text evades this attribute-call guard.
    In particular, compile() is live at two legitimate sites in the suite:
      - tests/test_platform_lock.py:763
      - tests/test_host_sandbox_profile.py:977
    Each compiles strings constructed within the test itself rather than production source.
    P16 as a written rule and human /plan-review cover evasive mechanisms.

(d) DOES NOT COVER FIXTURE MODULES:
    Fixture modules under tests/fixtures/ and tests/benchmark_fixtures/ are excluded from
    the discovery set. Those files represent synthetic sample code rather than suite
    assertions. The 13 fixture modules hold zero flagged calls today.

STANDING COVERAGE:
For what this guard does not cover, GUIDING_PRINCIPLES.md P16 stands as the canonical
written rule, and /plan-review serves as the human evaluation pass.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import NamedTuple

FLAGGED_CALLS: dict[str, set[str]] = {
    "inspect": {"getsource", "getsourcelines", "getsourcefile"},
    "ast": {"parse", "walk", "unparse"},
}


class StructurePinViolation(NamedTuple):
    file_path: str
    lineno: int
    call_form: str

    def render(self) -> str:
        return (
            f"{self.file_path}:{self.lineno}: prohibited code-structure pin via {self.call_form} "
            f"(violates GUIDING_PRINCIPLES.md P16: exercise the code and assert observable outputs instead)"
        )


class AllowlistEntry(NamedTuple):
    path: str
    reason: str


ALLOWLIST: tuple[AllowlistEntry, ...] = (
    AllowlistEntry(
        path="tests/test_carrier_scan_single_item_contract.py",
        reason=(
            "Quadratic-performance hazard scanner for per-item carrier scan calls with no "
            "behavioral proxy (file header forbids timing assertions as flaky); "
            "asserts zero violations as invariant with a >= non-vacuity floor, and documents "
            "its own scope and known hole."
        ),
    ),
    AllowlistEntry(
        path="tests/test_runner_shared.py",
        reason=(
            "find_dead_codefined_symbols sweeps runner modules for dead def-or-class symbols "
            "in runner_shared that neither host reaches (plan vbhat9 E-02/E-03)."
        ),
    ),
    AllowlistEntry(
        path="tests/test_no_unbounded_section_reads.py",
        reason=(
            "AST analyzer refusing marker-located unbounded section reads in test modules "
            "(plan jj5ju1); inspects test source ASTs and documents its own scope and known holes."
        ),
    ),
)


def scan_source_for_structure_pins(
    source: str, filename: str = "<string>"
) -> list[StructurePinViolation]:
    """Parse python source and return any code-structure pin call violations."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []

    violations: list[StructurePinViolation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                recv = node.func.value.id
                attr = node.func.attr
                if recv in FLAGGED_CALLS and attr in FLAGGED_CALLS[recv]:
                    violations.append(
                        StructurePinViolation(
                            file_path=filename,
                            lineno=node.lineno,
                            call_form=f"{recv}.{attr}",
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


def test_no_code_structure_pins_in_test_modules() -> None:
    """Scan all test modules under tests/ for prohibited code-structure pin calls."""
    repo_root = Path(__file__).resolve().parent.parent
    allowlist_map = {entry.path: entry.reason for entry in ALLOWLIST}
    test_modules = discover_test_modules(repo_root)

    all_violations: list[StructurePinViolation] = []
    for mod_path in test_modules:
        rel_path = str(mod_path.relative_to(repo_root))
        if rel_path in allowlist_map:
            continue
        source = mod_path.read_text(encoding="utf-8")
        violations = scan_source_for_structure_pins(source, filename=rel_path)
        all_violations.extend(violations)

    assert not all_violations, (
        f"Found {len(all_violations)} prohibited code-structure pin call(s) in tests:\n"
        + "\n".join(v.render() for v in all_violations)
    )


def test_allowlist_entries_exist_and_contain_flagged_calls() -> None:
    """Every allowlisted entry must exist on disk and contain at least one flagged call.

    A stale entry (file deleted, renamed, or cleaned of pins) fails loudly.
    The detector is called directly on the file's source rather than through
    the allowlist-filtered walk, so the self-cleaning check is non-vacuous.
    """
    repo_root = Path(__file__).resolve().parent.parent
    for entry in ALLOWLIST:
        target_path = repo_root / entry.path
        assert target_path.is_file(), f"Allowlisted file {entry.path} does not exist. Remove stale entry from ALLOWLIST."
        source = target_path.read_text(encoding="utf-8")
        violations = scan_source_for_structure_pins(source, filename=entry.path)
        assert len(violations) > 0, (
            f"Allowlisted file {entry.path} no longer contains any flagged calls. "
            f"Reason was: {entry.reason}. Remove stale entry from ALLOWLIST."
        )


def test_carrier_scan_contract_allowlist_entry_is_non_vacuous() -> None:
    """Verify that the single live allowlist entry contains its known flagged calls."""
    repo_root = Path(__file__).resolve().parent.parent
    target_path = repo_root / "tests/test_carrier_scan_single_item_contract.py"
    source = target_path.read_text(encoding="utf-8")
    violations = scan_source_for_structure_pins(
        source, filename="tests/test_carrier_scan_single_item_contract.py"
    )
    assert len(violations) >= 7, (
        f"Expected at least 7 flagged calls in tests/test_carrier_scan_single_item_contract.py, "
        f"found {len(violations)}"
    )
    flagged_forms = {v.call_form for v in violations}
    assert "ast.parse" in flagged_forms
    assert "ast.walk" in flagged_forms


# ======================================================================================
# Positive Fixtures (prove each of the six detected call forms is caught)
# ======================================================================================


def test_guard_flags_inspect_getsource() -> None:
    src = "import inspect\ns = inspect.getsource(fn)\n"
    violations = scan_source_for_structure_pins(src, filename="test_pos.py")
    assert len(violations) == 1
    assert violations[0].call_form == "inspect.getsource"
    assert violations[0].lineno == 2
    assert "GUIDING_PRINCIPLES.md P16" in violations[0].render()


def test_guard_flags_inspect_getsourcelines() -> None:
    src = "import inspect\nlines, _ = inspect.getsourcelines(cls)\n"
    violations = scan_source_for_structure_pins(src, filename="test_pos.py")
    assert len(violations) == 1
    assert violations[0].call_form == "inspect.getsourcelines"
    assert violations[0].lineno == 2


def test_guard_flags_inspect_getsourcefile() -> None:
    src = "import inspect\nf = inspect.getsourcefile(mod)\n"
    violations = scan_source_for_structure_pins(src, filename="test_pos.py")
    assert len(violations) == 1
    assert violations[0].call_form == "inspect.getsourcefile"
    assert violations[0].lineno == 2


def test_guard_flags_ast_parse() -> None:
    src = "import ast\ntree = ast.parse(code)\n"
    violations = scan_source_for_structure_pins(src, filename="test_pos.py")
    assert len(violations) == 1
    assert violations[0].call_form == "ast.parse"
    assert violations[0].lineno == 2


def test_guard_flags_ast_walk() -> None:
    src = "import ast\nfor node in ast.walk(tree):\n    pass\n"
    violations = scan_source_for_structure_pins(src, filename="test_pos.py")
    assert len(violations) == 1
    assert violations[0].call_form == "ast.walk"
    assert violations[0].lineno == 2


def test_guard_flags_ast_unparse() -> None:
    src = "import ast\ns = ast.unparse(tree)\n"
    violations = scan_source_for_structure_pins(src, filename="test_pos.py")
    assert len(violations) == 1
    assert violations[0].call_form == "ast.unparse"
    assert violations[0].lineno == 2


# ======================================================================================
# Negative Fixtures (prove legitimate inspection shapes are NOT caught)
# ======================================================================================


def test_guard_silent_on_inspect_signature() -> None:
    """Negative fixture: inspect.signature(...) is a legitimate API inspection, not source inspection."""
    src = "import inspect\nsig = inspect.signature(func)\n"
    violations = scan_source_for_structure_pins(src, filename="test_neg.py")
    assert len(violations) == 0


def test_guard_silent_on_same_named_attributes_on_different_receivers() -> None:
    """Negative fixture: parse/walk on non-ast receivers must not be flagged."""
    src = """
parser = CustomParser()
doc = CustomDocument()
generator = CustomGenerator()
manager = CustomManager()
tree = parser.parse(content)
nodes = doc.walk()
code = generator.unparse(tree)
src_file = manager.getsourcefile(mod)
"""
    violations = scan_source_for_structure_pins(src, filename="test_neg.py")
    assert len(violations) == 0
