"""Regression test for full-path spec citations in package source.

This test scans tracked package source (agent_workflows/**/*.py) for full-path
`.aw/records/specs/...spec.md` citations and verifies that every cited specification
exists on disk.

Scope boundary justification:
The test is strictly bounded to `agent_workflows/**/*.py` and carries no `livecorpus`
marker so that it runs in the default test suite. This boundary is necessary and
justified by three repository facts:
(i) `tests/` holds paths that are deliberate `tmp_path` fixture names which MUST NOT
    resolve in the real tree (for example, the string `.aw/records/specs/x.spec.md` in
    `tests/test_scope_match.py`, line 31; and `.aw/records/specs/draft/20260925-1111-01-test.spec.md`
    in `tests/test_doctor.py`, line 553), so scanning `tests/` would assert a falsehood.
(ii) The record trees hold hundreds of such paths that are IMMUTABLE HISTORY, correct as
     of writing, so failing on them would demand forbidden edits.
(iii) `tools/` holds zero full-path `.aw/records/specs/...spec.md` citations in shipped
      scripts, but holds test files whose spec citations are deliberately unresolvable
      fixture names (`tools/test_agy_run.py` cites fixture specs), so scanning `tools/`
      adds no coverage while introducing false-positive risk.
"""

from __future__ import annotations

import re
from pathlib import Path

SPEC_PATH_PATTERN = re.compile(r"(\.aw/records/specs/[a-zA-Z0-9_./-]+\.spec\.md)")


def test_package_source_spec_path_citations_resolve() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    package_dir = repo_root / "agent_workflows"
    assert package_dir.is_dir(), f"Expected package directory at {package_dir}"

    dangling: list[str] = []
    for py_file in sorted(package_dir.rglob("*.py")):
        rel_py_path = py_file.relative_to(repo_root)
        content = py_file.read_text(encoding="utf-8")
        for match in SPEC_PATH_PATTERN.finditer(content):
            spec_rel_path = match.group(1)
            target_path = repo_root / spec_rel_path
            if not target_path.is_file():
                dangling.append(f"{rel_py_path}: cites nonexistent '{spec_rel_path}'")

    assert not dangling, (
        f"Found {len(dangling)} dangling spec path citation(s) in package source:\n"
        + "\n".join(dangling)
    )
