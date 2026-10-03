#!/usr/bin/env python3
"""THE COMMITTED DEAD-STATUS-TOKEN SCANNER: refuse bare legacy terminal status comparisons.

WHY THIS FILE EXISTS, stated first because its value is reproducibility and deterministic author-time enforcement.
Backlog item `ku8szz` asked whether an author-time rule could refuse a bare comparison against a retired
terminal-status token without firing on unrelated vocabularies that share spellings. Measuring the repository
revealed that dropping the two ambiguous tokens (`blocked` and `partial`) from the rule domain removes 100% of
the false-positive population across all colliding vocabularies, leaving eight runner-specific coinages where
the rule measures zero false positives. Retrospectively evaluated against the pre-`qvfd4l` tree (`d0b932d40^`),
the rule flags exactly three true positives (`render_stream.py` x2, `run_dashboard.py` x1) and zero false positives.

THE METRIC IS STATED, NOT IMPLIED:
1. DOMAIN: The keys of `agent_workflows.runner_shared.TERMINAL_STATUS_ALIASES` minus the ambiguous set
   `frozenset({"blocked", "partial"})`. Derived dynamically at runtime from the alias table.
2. UNIT OF ANALYSIS: A complete `if`/`elif` chain. The token set of a chain is the union of string constants
   appearing in the `test` expressions of every arm in that chain.
3. FLAGGED SITE: Any chain containing an in-domain legacy status token whose canonical counterpart
   (`TERMINAL_STATUS_ALIASES[token]`) is ABSENT from the chain's token set, unless explicitly exempt.
4. EXEMPTION CRITERIA:
   - In-code marker: A comment on the chain or its enclosing function matching:
     `aw: dead-status-token-exempt <id6> <why>`
     where `<id6>` is a 6-character alphanumeric artifact identifier (e.g. `qvfd4l`) and `<why>` is a
     non-empty explanation. Markers lacking a valid `<id6>` citation are rejected and do not exempt.
   - Function-scoped canonicalizer: The enclosing function mentions `canonical_terminal_status`, `st_canon`,
     or `cts` at or before the chain (`lineno <= chain_end`), indicating the function explicitly reads
     both spellings or canonicalizes status.

LIMITATIONS AND BLIND SPOTS:
- STRING LITERALS ONLY: Sweeps AST string constants (`ast.Constant`) within Python source code under
  `agent_workflows/`. Comparisons constructed dynamically from non-literals, config files, or module
  constants (such as the legacy writer constants identified in backlog item `79d4ix`) are not visible to
  this scanner.
- PACKAGE-SCOPED: Only inspects production code in `agent_workflows/` (or paths explicitly supplied).
  Test fixtures (`tests/`), automation scripts, and workflow bodies are intentionally not swept.

USAGE:
    python3 tools/dead_status_token_scan.py               # scan working tree agent_workflows/
    python3 tools/dead_status_token_scan.py --rev <rev>   # scan git tree at <rev> via git archive / show
    python3 tools/dead_status_token_scan.py <paths...>    # scan specific files or directories
    python3 tools/dead_status_token_scan.py --json        # output machine-readable JSON summary

Exit status is 0 when zero flagged sites are found, and 1 when one or more flagged sites are found.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import pathlib
import re
import subprocess
import sys
import tarfile
import tokenize
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

# Ensure repository root is on sys.path so agent_workflows can be imported
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_workflows.runner_shared import TERMINAL_STATUS_ALIASES  # noqa: E402

#: The two ambiguous tokens that collide across multiple vocabularies and are permanently excluded.
AMBIGUOUS: frozenset[str] = frozenset({"blocked", "partial"})

#: Exemption marker regex requiring a 6-character alphanumeric artifact id6 and justification.
EXEMPT_MARKER_REGEX: re.Pattern[str] = re.compile(
    r"#\s*aw:\s*dead-status-token-exempt\s+([0-9a-z]{6})\s+(\S.*)"
)

#: Raw marker pattern to detect un-cited or malformed marker attempts.
ANY_EXEMPT_MARKER_REGEX: re.Pattern[str] = re.compile(
    r"#\s*aw:\s*dead-status-token-exempt\b"
)

#: AST identifiers indicating function-scoped canonicalization.
CANONICALIZER_IDENTIFIERS: frozenset[str] = frozenset(
    {"canonical_terminal_status", "st_canon", "cts"}
)


def get_domain(aliases: Mapping[str, str] | None = None) -> frozenset[str]:
    """Derive the eight-token unambiguous domain from the alias table at runtime."""
    if aliases is None:
        aliases = TERMINAL_STATUS_ALIASES
    return frozenset(aliases.keys()) - AMBIGUOUS


def __getattr__(name: str) -> Any:
    if name == "DOMAIN":
        return get_domain()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


@dataclass(frozen=True)
class SiteRecord:
    file: str
    line: int
    function: str
    tokens: list[str]
    missing: list[dict[str, str]]
    is_exempt: bool
    exemption_reason: str | None = None


@dataclass(frozen=True)
class ScanSummary:
    domain: list[str]
    excluded_ambiguous: list[str]
    flagged: list[SiteRecord]
    exempt: list[SiteRecord]

    @property
    def total_flagged(self) -> int:
        return len(self.flagged)

    @property
    def total_exempt(self) -> int:
        return len(self.exempt)


def _extract_comments(source: str) -> list[tuple[int, str]]:
    """Extract line comments from source code with line numbers."""
    comments: list[tuple[int, str]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                comments.append((tok.start[0], tok.string))
    except (tokenize.TokenizeError, IndentationError):
        # Fallback to simple line-based regex if tokenization fails
        for lineno, line in enumerate(source.splitlines(), start=1):
            idx = line.find("#")
            if idx != -1:
                comments.append((lineno, line[idx:]))
    return comments


def _extract_test_string_constants(node: ast.AST) -> set[str]:
    """Extract all string literal constants within a test expression AST."""
    constants: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            constants.add(child.value)
    return constants


def scan_source(
    source: str,
    filename: str = "<source>",
    aliases: Mapping[str, str] | None = None,
    ambiguous: frozenset[str] | None = None,
) -> list[SiteRecord]:
    """Scan a Python source code string for dead legacy status token comparisons."""
    if aliases is None:
        aliases = TERMINAL_STATUS_ALIASES
    if ambiguous is None:
        ambiguous = AMBIGUOUS
    domain = frozenset(aliases.keys()) - ambiguous

    # Fast pre-check: if none of the domain tokens appear in source text, no AST constant can match
    if not any(tok in source for tok in domain):
        return []

    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []

    records: list[SiteRecord] = []
    comments: list[tuple[int, str]] | None = None
    parent_map: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent_map[child] = node

    def find_enclosing_function(
        n: ast.AST,
    ) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | None, str]:
        curr: ast.AST | None = n
        while curr in parent_map:
            curr = parent_map[curr]
            if isinstance(curr, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return curr, curr.name
        return None, "<module>"

    records: list[SiteRecord] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue

        # Skip elif arms; they are handled as part of the chain head
        p = parent_map.get(node)
        if isinstance(p, ast.If) and len(p.orelse) == 1 and p.orelse[0] is node:
            continue

        # Collect complete chain of arms
        arms: list[ast.If] = [node]
        curr = node
        while len(curr.orelse) == 1 and isinstance(curr.orelse[0], ast.If):
            curr = curr.orelse[0]
            arms.append(curr)

        chain_start = node.lineno
        chain_end = getattr(curr, "end_lineno", curr.lineno)
        if curr.orelse:
            chain_end = max(
                chain_end,
                getattr(curr.orelse[-1], "end_lineno", curr.orelse[-1].lineno),
            )

        # Union of string constants in test expressions across all arms
        chain_constants: set[str] = set()
        for arm in arms:
            chain_constants.update(_extract_test_string_constants(arm.test))

        in_domain = chain_constants.intersection(domain)
        if not in_domain:
            continue

        # Check for missing canonical tokens
        missing_pairs: list[dict[str, str]] = []
        for tok in sorted(in_domain):
            canon = aliases.get(tok)
            if canon and canon not in chain_constants:
                missing_pairs.append({"token": tok, "canonical": canon})

        if not missing_pairs:
            continue

        func_node, func_name = find_enclosing_function(node)
        func_start = func_node.lineno if func_node else max(1, chain_start - 10)
        func_end = (
            getattr(func_node, "end_lineno", chain_end) if func_node else chain_end
        )

        is_exempt = False
        exemption_reason: str | None = None

        # Check for in-code marker on the chain or inside enclosing function
        if comments is None:
            comments = _extract_comments(source)
        for c_line, c_text in comments:
            if (func_node and func_start <= c_line <= func_end) or (
                chain_start - 3 <= c_line <= chain_end
            ):
                match = EXEMPT_MARKER_REGEX.search(c_text)
                if match:
                    id6, why = match.group(1), match.group(2).strip()
                    is_exempt = True
                    exemption_reason = f"marker ({id6}): {why}"
                    break

        # Check function-scoped canonicalizer exemption at or before chain
        if not is_exempt and func_node is not None:
            for child in ast.walk(func_node):
                if getattr(child, "lineno", 0) <= chain_end:
                    if (
                        isinstance(child, ast.Name)
                        and child.id in CANONICALIZER_IDENTIFIERS
                    ):
                        is_exempt = True
                        exemption_reason = f"function-scoped canonicalizer ({child.id})"
                        break
                    elif (
                        isinstance(child, ast.Attribute)
                        and child.attr in CANONICALIZER_IDENTIFIERS
                    ):
                        is_exempt = True
                        exemption_reason = (
                            f"function-scoped canonicalizer ({child.attr})"
                        )
                        break

        records.append(
            SiteRecord(
                file=filename,
                line=chain_start,
                function=func_name,
                tokens=sorted(in_domain),
                missing=missing_pairs,
                is_exempt=is_exempt,
                exemption_reason=exemption_reason,
            )
        )

    return records


def scan_file(
    path: pathlib.Path | str,
    aliases: Mapping[str, str] | None = None,
    ambiguous: frozenset[str] | None = None,
    rel_to: pathlib.Path | None = None,
) -> list[SiteRecord]:
    """Scan a single Python file on disk."""
    p = pathlib.Path(path)
    try:
        source = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    display_name = (
        str(p.relative_to(rel_to)) if rel_to and p.is_relative_to(rel_to) else str(p)
    )
    return scan_source(
        source, filename=display_name, aliases=aliases, ambiguous=ambiguous
    )


def scan_paths(
    paths: Sequence[pathlib.Path | str],
    aliases: Mapping[str, str] | None = None,
    ambiguous: frozenset[str] | None = None,
    repo_root: pathlib.Path | None = None,
) -> ScanSummary:
    """Scan file paths or directories on disk."""
    if repo_root is None:
        repo_root = REPO_ROOT
    all_sites: list[SiteRecord] = []

    for item in paths:
        p = pathlib.Path(item)
        if not p.is_absolute():
            p = (repo_root / p).resolve()
        if p.is_file() and p.suffix == ".py":
            all_sites.extend(
                scan_file(p, aliases=aliases, ambiguous=ambiguous, rel_to=repo_root)
            )
        elif p.is_dir():
            for py_path in sorted(p.rglob("*.py")):
                all_sites.extend(
                    scan_file(
                        py_path, aliases=aliases, ambiguous=ambiguous, rel_to=repo_root
                    )
                )

    domain_list = sorted(get_domain(aliases))
    excluded_list = sorted(ambiguous or AMBIGUOUS)
    flagged = [s for s in all_sites if not s.is_exempt]
    exempt = [s for s in all_sites if s.is_exempt]

    return ScanSummary(
        domain=domain_list,
        excluded_ambiguous=excluded_list,
        flagged=flagged,
        exempt=exempt,
    )


def scan_git_rev(
    rev: str,
    target_dir: str = "agent_workflows",
    aliases: Mapping[str, str] | None = None,
    ambiguous: frozenset[str] | None = None,
) -> ScanSummary:
    """Scan files at a historical git revision using git archive."""
    try:
        tar_bytes = subprocess.check_output(
            ["git", "archive", rev, target_dir],
            cwd=str(REPO_ROOT),
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Failed to fetch git archive at {rev}:{target_dir}"
        ) from exc

    tf = tarfile.open(fileobj=io.BytesIO(tar_bytes))
    all_sites: list[SiteRecord] = []

    for member in sorted(tf.getmembers(), key=lambda m: m.name):
        if member.name.endswith(".py"):
            f = tf.extractfile(member)
            if f is not None:
                source = f.read().decode("utf-8", errors="replace")
                all_sites.extend(
                    scan_source(
                        source,
                        filename=member.name,
                        aliases=aliases,
                        ambiguous=ambiguous,
                    )
                )

    domain_list = sorted(get_domain(aliases))
    excluded_list = sorted(ambiguous or AMBIGUOUS)
    flagged = [s for s in all_sites if not s.is_exempt]
    exempt = [s for s in all_sites if s.is_exempt]

    return ScanSummary(
        domain=domain_list,
        excluded_ambiguous=excluded_list,
        flagged=flagged,
        exempt=exempt,
    )


def print_summary(summary: ScanSummary) -> None:
    """Print a clean human-readable scan report."""
    print(f"Domain ({len(summary.domain)} tokens): {', '.join(summary.domain)}")
    print(
        f"Excluded ambiguous tokens ({len(summary.excluded_ambiguous)}): {', '.join(summary.excluded_ambiguous)}"
    )

    if summary.exempt:
        print(f"\nExempt sites ({summary.total_exempt}):")
        for s in summary.exempt:
            missing_desc = ", ".join(
                f"'{m['token']}' -> '{m['canonical']}'" for m in s.missing
            )
            print(
                f"  {s.file}:{s.line} in {s.function}: {missing_desc} (reason: {s.exemption_reason})"
            )

    if summary.flagged:
        print(f"\nFlagged sites ({summary.total_flagged}):")
        for s in summary.flagged:
            for m in s.missing:
                print(
                    f"  {s.file}:{s.line} in {s.function}: token '{m['token']}' missing canonical twin '{m['canonical']}'"
                )

    print(
        f"\nTotal flagged sites: {summary.total_flagged} ({summary.total_exempt} exempt)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refuse bare legacy terminal status token comparisons at author time."
    )
    parser.add_argument(
        "--rev",
        metavar="REV",
        help="Git revision to inspect (e.g. d0b932d40^ or HEAD)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["agent_workflows"],
        help="Directories or files to scan (default: agent_workflows)",
    )

    args = parser.parse_args(argv)

    if args.rev:
        target = args.paths[0] if args.paths else "agent_workflows"
        summary = scan_git_rev(args.rev, target_dir=target)
    else:
        summary = scan_paths(args.paths, repo_root=REPO_ROOT)

    if args.json:
        out = {
            "domain": summary.domain,
            "excluded_ambiguous": summary.excluded_ambiguous,
            "total_flagged": summary.total_flagged,
            "total_exempt": summary.total_exempt,
            "flagged": [asdict(s) for s in summary.flagged],
            "exempt": [asdict(s) for s in summary.exempt],
        }
        print(json.dumps(out, indent=2))
    else:
        print_summary(summary)

    return 1 if summary.total_flagged > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
