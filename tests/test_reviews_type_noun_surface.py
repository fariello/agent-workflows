"""Behavioral tests verifying 'reviews' is an accepted type noun with no backend and no status lifecycle.

Guards that:
1. 'reviews' is accepted as a type noun (normalize_type, is_type_token, find).
2. 'reviews' has no backend in TYPE_BACKENDS for any routed verb, and routed verbs refuse with exit 2
   leaving records untouched.
3. 'reviews' is not in selectors.KNOWN_PRIMARY_TYPES and not claimed by 'other', so primary-type
   consumers do not treat reviews as IPD work items.
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
from typing import Any
from unittest import mock

import pytest

from agent_workflows import artifact_types as at, cli, runner_shared, selectors


@pytest.fixture
def repo_with_review(tmp_path: Path) -> tuple[Path, Path]:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    reviews_dir = tmp_path / ".aw" / "records" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    review_path = reviews_dir / "20260929-demo-01-ab12cd-x.review.md"
    content = "# Review: x\n\n- Subject-Id: ab12cd\n"
    review_path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)
    return tmp_path, review_path


def _run_cli(cmd: list[str]) -> tuple[int, str]:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    try:
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = cli.main(cmd)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 0
    return rc, buf_out.getvalue() + buf_err.getvalue()


@pytest.mark.parametrize(
    ("verb", "extra_args"),
    [
        ("rename", lambda p: [str(p), "--slug", "zz"]),
        ("group", lambda _p: ["x"]),
        ("index", lambda _p: []),
    ],
    ids=["rename", "group", "index"],
)
def test_reviews_backend_routed_verbs_refuse_with_exit_2(
    repo_with_review: tuple[Path, Path],
    verb: str,
    extra_args: Any,
):
    repo, review_path = repo_with_review
    reviews_dir = review_path.parent
    original_bytes = review_path.read_bytes()
    original_listing = sorted(p.name for p in reviews_dir.iterdir())

    cmd = [
        "--no-interactive",
        verb,
        "reviews",
        *extra_args(review_path),
        "--dir",
        str(repo),
    ]
    rc, out = _run_cli(cmd)

    assert rc == 2, f"Expected rc=2 for {verb}, got {rc}. Output: {out}"
    assert f"'{verb}' is not supported for reviews." in out
    assert review_path.exists(), f"Review file {review_path} was removed!"
    assert review_path.read_bytes() == original_bytes, "Review file bytes changed!"
    assert (
        sorted(p.name for p in reviews_dir.iterdir()) == original_listing
    ), "Directory listing changed!"


def test_reviews_has_no_backend_for_any_routed_verb():
    routed_verbs = {
        v
        for t in at.ARTIFACT_TYPES
        for v in ("new", "index", "find", "rename", "group", "archive", "check")
        if at.backend_name(t, v)
    }
    assert routed_verbs, "Expected non-empty union of routed verbs"
    assert at.backend_name("plans", "rename") is not None, "Positive control failed"
    for verb in routed_verbs:
        assert at.backend_name("reviews", verb) is None
        assert at.resolve_backend("reviews", verb) is None


def test_reviews_type_backends_non_vacuity_patch(
    repo_with_review: tuple[Path, Path],
):
    repo, review_path = repo_with_review
    cmd = [
        "--no-interactive",
        "rename",
        "reviews",
        str(review_path),
        "--slug",
        "zz",
        "--dir",
        str(repo),
    ]
    with mock.patch.dict(
        at.TYPE_BACKENDS,
        {"reviews": {"rename": "artifact_rename.run_rename_other"}},
    ):
        assert at.backend_name("reviews", "rename") is not None
        rc, out = _run_cli(cmd)
        assert "is not supported for reviews." not in out


def test_reviews_type_noun_accepted_positive_control(
    repo_with_review: tuple[Path, Path],
):
    repo, review_path = repo_with_review
    assert at.normalize_type("reviews") == "reviews"
    assert at.normalize_type("review") == "reviews"
    assert at.is_type_token("reviews") is True

    rel_review_path = review_path.relative_to(repo).as_posix()
    find_cmd = [
        "--no-interactive",
        "find",
        "reviews",
        "ab12cd",
        "--dir",
        str(repo),
    ]
    rc, out = _run_cli(find_cmd)
    assert rc == 0, f"Expected rc=0 for find reviews, got {rc}. Output: {out}"
    assert rel_review_path in out

    contrast_cmd = [
        "--no-interactive",
        "rename",
        "nosuchtype",
        "x",
        "--slug",
        "zz",
        "--dir",
        str(repo),
    ]
    rc_contrast, out_contrast = _run_cli(contrast_cmd)
    assert (
        rc_contrast == 2
    ), f"Expected rc=2 for unknown noun, got {rc_contrast}. Output: {out_contrast}"
    assert "unknown artifact type 'nosuchtype'" in out_contrast
    assert "is not supported for" not in out_contrast


def test_reviews_has_no_status_lifecycle_and_not_in_known_primary_types(
    repo_with_review: tuple[Path, Path],
):
    repo, _ = repo_with_review
    specs_dir = repo / ".aw" / "records" / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    spec_path = specs_dir / "20260929-qq12cd-01-qq12cd-y.spec.md"
    spec_path.write_text(
        "# Spec: y\n\n- Id: qq12cd\n- Status: draft\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add spec"], cwd=repo, check=True)

    msg_rev = runner_shared.describe_unresolved_plan_selector(
        repo, "20260929-demo-01-ab12cd-x.review"
    )
    assert "not an IPD plan" not in msg_rev
    assert "reviews record" not in msg_rev

    msg_spec = runner_shared.describe_unresolved_plan_selector(
        repo, "20260929-qq12cd-01-qq12cd-y.spec"
    )
    assert "is a spec" in msg_spec
    assert "not an IPD plan" in msg_spec

    res_rev = selectors.resolve(repo, "reviews", "20260929-demo-01-ab12cd-x.review")
    assert res_rev.is_match is True

    res_other = selectors.resolve(repo, "other", "20260929-demo-01-ab12cd-x.review")
    assert res_other.is_match is False

    assert "reviews" not in selectors.KNOWN_PRIMARY_TYPES
    assert "reviews" in selectors.NON_PRIMARY_RECORD_DIRS


def test_known_primary_types_non_vacuity_patch(
    repo_with_review: tuple[Path, Path],
):
    repo, _ = repo_with_review
    with mock.patch.object(
        selectors,
        "KNOWN_PRIMARY_TYPES",
        selectors.KNOWN_PRIMARY_TYPES | {"reviews"},
    ):
        msg = runner_shared.describe_unresolved_plan_selector(
            repo, "20260929-demo-01-ab12cd-x.review"
        )
        assert "is a reviews record" in msg
        assert "not an IPD plan" in msg
