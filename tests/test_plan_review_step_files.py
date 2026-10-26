"""Tests asserting on installed plan-review step files and workflow contracts (IPD 3bwrfx)."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
import pytest

from agent_workflows import plan_readiness
from tests.support import git, init_repo, run_cli

pytestmark = pytest.mark.core


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


def test_installed_plan_review_step_files_exist(installed_repo: Path) -> None:
    """Property (a): every step file named in installed plan-review.md exists under plan-review/steps/."""
    workflows_dir = installed_repo / ".aw" / "system" / "workflows"
    plan_review_file = workflows_dir / "plan-review" / "plan-review.md"
    assert plan_review_file.is_file(), f"Missing installed {plan_review_file}"

    content = plan_review_file.read_text(encoding="utf-8")
    step_refs = re.findall(r"steps/([a-z0-9_-]+\.md)", content)
    assert (
        len(step_refs) > 0
    ), "No step file references found in installed plan-review.md"

    unique_steps = sorted(set(step_refs))
    steps_dir = workflows_dir / "plan-review" / "steps"
    assert steps_dir.is_dir(), f"Missing steps directory {steps_dir}"

    for step_file in unique_steps:
        target_path = steps_dir / step_file
        assert (
            target_path.is_file()
        ), f"Named step file {step_file} not found at {target_path}"


def test_installed_tier_and_rereview_markers(installed_repo: Path) -> None:
    """Property (b): steps/t-tier.md ends with AW-TIER: and steps/s6-rereview.md names both AW-REVIEW markers."""
    workflows_dir = installed_repo / ".aw" / "system" / "workflows"
    t_tier = workflows_dir / "plan-review" / "steps" / "t-tier.md"
    assert t_tier.is_file(), f"Missing {t_tier}"
    tier_content = t_tier.read_text(encoding="utf-8").strip()
    assert re.search(
        r"AW-TIER:\s*<simple\|standard\|complex>", tier_content
    ), f"AW-TIER marker format not found in {t_tier}"

    s6_rereview = workflows_dir / "plan-review" / "steps" / "s6-rereview.md"
    assert s6_rereview.is_file(), f"Missing {s6_rereview}"
    rereview_content = s6_rereview.read_text(encoding="utf-8")
    assert (
        "AW-REVIEW: AGAIN" in rereview_content
    ), f"AW-REVIEW: AGAIN marker not found in {s6_rereview}"
    assert (
        "AW-REVIEW: DONE" in rereview_content
    ), f"AW-REVIEW: DONE marker not found in {s6_rereview}"


def test_installed_finalize_contains_verdicts(installed_repo: Path) -> None:
    """Property (c): steps/s7-finalize.md contains each token of plan_readiness.VERDICTS."""
    workflows_dir = installed_repo / ".aw" / "system" / "workflows"
    s7_finalize = workflows_dir / "plan-review" / "steps" / "s7-finalize.md"
    assert s7_finalize.is_file(), f"Missing {s7_finalize}"
    finalize_content = s7_finalize.read_text(encoding="utf-8")

    for verdict_token in plan_readiness.VERDICTS:
        assert (
            verdict_token in finalize_content
        ), f"Verdict token {verdict_token!r} from plan_readiness.VERDICTS not found in {s7_finalize}"


def test_installed_askme_contains_five_level_recommendations(
    installed_repo: Path,
) -> None:
    """Property (d): installed askme/askme.md contains very weak and very strong."""
    workflows_dir = installed_repo / ".aw" / "system" / "workflows"
    askme_file = workflows_dir / "askme" / "askme.md"
    assert askme_file.is_file(), f"Missing {askme_file}"
    askme_content = askme_file.read_text(encoding="utf-8")

    assert "very weak" in askme_content, f"'very weak' not found in {askme_file}"
    assert "very strong" in askme_content, f"'very strong' not found in {askme_file}"
