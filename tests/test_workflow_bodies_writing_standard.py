"""Tests asserting installed workflow bodies point to the technical writing standard (IPD e4n4p3)."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
import pytest

from tests.support import git, init_repo, run_cli

pytestmark = pytest.mark.core

WORKFLOW_BODIES = [
    "spec/spec.md",
    "spec-review/spec-review.md",
    "plan-review/plan-review.md",
    "plan-review/steps/p-proofread.md",
    "plan-review/steps/_kernel.md",
    "plan-review-long/plan-review-long.md",
    "plan-review-long/02-review-and-revise.md",
    "plan-review-long/review-rubric.md",
    "ipd-lifecycle/ipd-lifecycle.md",
    "advise/personas/spec-editor.md",
    "research-prompt/research-prompt.md",
]


@pytest.fixture(scope="module")
def installed_repo():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        repo = init_repo(tmp_dir / "target")
        (repo / "README.md").write_text("initial\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "initial")

        env = os.environ.copy()
        env["HOME"] = str(tmp_dir)
        env["AW_NO_REEXEC"] = "1"

        proc = run_cli("install", "-y", str(repo), env=env)
        assert proc.returncode == 0, f"aw install failed: {proc.stderr}\n{proc.stdout}"

        yield repo


def test_workflow_bodies_writing_standard_pointers(installed_repo: Path) -> None:
    """For each of the eleven installed workflow bodies in Scope-Paths, find every backticked

    reference ending in technical-writing/technical-writing.md, resolve it relative to that
    body's directory, and assert that at least one reference exists and that every one resolves
    to an existing file.
    """
    assert (
        len(WORKFLOW_BODIES) == 11
    ), f"Expected 11 workflow bodies, got {len(WORKFLOW_BODIES)}"
    workflows_dir = installed_repo / ".aw" / "system" / "workflows"

    for rel_body in WORKFLOW_BODIES:
        body_file = workflows_dir / rel_body
        assert body_file.is_file(), f"Installed workflow body missing: {body_file}"

        content = body_file.read_text(encoding="utf-8")
        refs = re.findall(r"`([^`]*technical-writing/technical-writing\.md)`", content)
        assert (
            len(refs) >= 1
        ), f"No backticked technical-writing/technical-writing.md reference found in {rel_body}"

        for ref in refs:
            target = (body_file.parent / ref).resolve()
            assert target.is_file(), f"Reference {ref!r} in {rel_body} did not resolve to a file (resolved to {target})"
