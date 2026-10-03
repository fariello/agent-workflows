"""Regression test for test-file citations in published documentation.

This test scans published prose documentation for `tests/test_*.py` path citations
and verifies that every cited test file exists on disk, unless the citation is an
explicitly exempted deliberate historical reference.

Scope boundary justification:
The test is strictly bounded to `docs/**/*.md` plus five enumerated root prose
documents: `CONTRIBUTING.md`, `README.md`, `RELEASING.md`, `AGENTS.md`, and
`GUIDING_PRINCIPLES.md`. It carries no `livecorpus` marker so that it runs in the
default test suite. This boundary is necessary and justified by three repository facts:
(i) `CHANGELOG.md` and `DECISIONS.md` are append-only dated history records whose
    citations were correct when written (e.g. 2026-07 entries naming suites deleted
    during subsequent trims). Rewriting them would falsify historical records. They
    are excluded by name and not scanned via root globbing.
(ii) `.aw/records/` holds immutable terminal records (plans, reviews, specs) whose
     historical citations must not be rewritten. Tests asserting over `.aw/records/`
     are required to carry `livecorpus` and are deselected by default.
(iii) `tests/` holds test fixtures and mock paths (e.g. temporary directory paths
      constructed by test harnesses) that must not resolve to real files on disk.

Exemption rule (present-tense vs past-tense):
A citation is a defect when it is a PRESENT-TENSE pointer a reader is invited to
follow or verify. It is NOT a defect when it is PAST-TENSE history whose surrounding
prose already announces that the suite was retired or deleted. Historical mentions
are permitted only via narrow, keyed exemptions specifying both the document and the
exact citation, rather than blanket file-level skips.
"""

from __future__ import annotations

import re
from pathlib import Path

# Explicit enumerated literal list of root prose documents.
# DO NOT glob *.md at repo root, which would pick up append-only history files.
ROOT_PROSE_DOCS: list[str] = [
    "CONTRIBUTING.md",
    "README.md",
    "RELEASING.md",
    "AGENTS.md",
    "GUIDING_PRINCIPLES.md",
]

# Explicitly excluded append-only history documents:
# - CHANGELOG.md: Dated release notes; citations were accurate at release time.
# - DECISIONS.md: Dated architecture decision records; citations reflect tree state at decision time.
EXCLUDED_HISTORY_DOCS: list[str] = [
    "CHANGELOG.md",
    "DECISIONS.md",
]

# Narrow, keyed exemptions for deliberate past-tense historical mentions.
# Key format: (document_relpath, citation_relpath) -> rationale.
HISTORICAL_EXEMPTIONS: dict[tuple[str, str], str] = {
    (
        "docs/wtiso-state-taxonomy.md",
        "tests/test_wtiso_characterization.py",
    ): (
        "Deliberate past-tense historical mention. The surrounding prose explicitly "
        "announces 'THESE DEFECTS ARE NO LONGER PINNED BY A TEST' and documents that "
        "the suite was retired on 2026-09-18 (commit d4dd6b88)."
    ),
}

TEST_CITATION_PATTERN = re.compile(r"\b(tests/test_[a-zA-Z0-9_]+\.py)\b")


def test_published_docs_test_citations_exist() -> None:
    repo_root = Path(__file__).resolve().parent.parent

    # Collect target files
    target_files: list[Path] = []

    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        target_files.extend(sorted(docs_dir.rglob("*.md")))

    for name in ROOT_PROSE_DOCS:
        file_path = repo_root / name
        assert file_path.is_file(), f"Expected enumerated root doc at {file_path}"
        target_files.append(file_path)

    dangling: list[str] = []

    for file_path in target_files:
        rel_path = file_path.relative_to(repo_root).as_posix()
        content = file_path.read_text(encoding="utf-8")

        for line_no, line in enumerate(content.splitlines(), 1):
            for match in TEST_CITATION_PATTERN.finditer(line):
                cited_path_str = match.group(1)
                key = (rel_path, cited_path_str)
                if key in HISTORICAL_EXEMPTIONS:
                    continue

                target_file = repo_root / cited_path_str
                if not target_file.is_file():
                    dangling.append(
                        f"{rel_path}:{line_no}: cites nonexistent '{cited_path_str}'"
                    )

    assert not dangling, (
        f"Found {len(dangling)} dangling test citation(s) in published docs:\n"
        + "\n".join(dangling)
    )
