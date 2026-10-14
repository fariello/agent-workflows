"""Behavioral tests for `agent_workflows.suite_cache` and `aw suite` (IPD `0o0wt2` E-08).

All tests use isolated `git init` fixture repositories with their own `pytest.ini`,
`AW_NO_REEXEC=1`, and `PYTHONPATH` pointing at this checkout, so cache records are
written only under the fixture's `<git-common-dir>/aw-suite-cache` and never touch
this checkout's cache or working tree.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import runner_shared, suite_cache

REPO_ROOT = Path(__file__).resolve().parent.parent


def _fixture_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["AW_NO_REEXEC"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_CURRENT_TEST", None)
    if extra:
        env.update(extra)
    return env


def _init_fixture_repo(path: Path, *, test_body: str | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Suite Cache Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "suite-cache@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    (path / ".gitignore").write_text(
        "*.ignored\n.pytest_cache/\n__pycache__/\n",
        encoding="utf-8",
    )
    (path / "pytest.ini").write_text(
        "[pytest]\naddopts = -q\ntestpaths = tests\n",
        encoding="utf-8",
    )
    tests_dir = path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    body = (
        test_body
        if test_body is not None
        else (
            "from pathlib import Path\n\n"
            "def test_ok():\n"
            "    Path('ran.ignored').write_text('1', encoding='utf-8')\n"
            "    assert 1 + 1 == 2\n"
        )
    )
    (tests_dir / "test_sample.py").write_text(body, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial fixture"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


def _count_git_objects(repo: Path) -> int:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--git-path", "objects"],
        check=True,
        capture_output=True,
        text=True,
    )
    obj_dir = (repo / proc.stdout.strip()).resolve()
    if not obj_dir.is_dir():
        return 0
    return sum(1 for p in obj_dir.rglob("*") if p.is_file())


def _run_aw_suite(
    repo: Path,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "agent_workflows", "suite", *args]
    return subprocess.run(
        cmd,
        cwd=repo,
        env=_fixture_env(extra_env),
        capture_output=True,
        text=True,
        check=False,
    )


def test_suite_key_stability_sensitivity_and_zero_side_effects(tmp_path: Path) -> None:
    """E-02 / E-08: key matches across clean checkouts, changes on tracked/untracked/env edits,
    ignores ignored files and -n flags, and leaves real index and object store untouched.
    """
    repo_a = _init_fixture_repo(tmp_path / "repo_a")
    repo_b = tmp_path / "repo_b"
    subprocess.run(
        ["git", "clone", "-q", str(repo_a), str(repo_b)],
        check=True,
        capture_output=True,
    )

    env = _fixture_env()
    status_before = subprocess.run(
        ["git", "-C", str(repo_a), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    objects_before = _count_git_objects(repo_a)

    key_a = suite_cache.suite_key(repo_a, env=env)
    key_b = suite_cache.suite_key(repo_b, env=env)
    assert key_a.cacheable is True
    assert key_a.digest is not None
    assert key_a.digest == key_b.digest
    assert key_a.components["tree"] == key_b.components["tree"]

    # Varying -n / --numprocesses in argv does not change the key
    key_n2 = suite_cache.suite_key(
        repo_a, [sys.executable, "-m", "pytest", "-n", "2"], env=env
    )
    key_n8 = suite_cache.suite_key(
        repo_a, [sys.executable, "-m", "pytest", "--numprocesses=8"], env=env
    )
    assert key_n2.digest == key_a.digest
    assert key_n8.digest == key_a.digest

    # Adding a gitignored file does not change the key
    (repo_a / "scratch.ignored").write_text("ignored content\n", encoding="utf-8")
    key_ignored = suite_cache.suite_key(repo_a, env=env)
    assert key_ignored.digest == key_a.digest

    status_mid = subprocess.run(
        ["git", "-C", str(repo_a), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    objects_mid = _count_git_objects(repo_a)
    assert status_mid == status_before
    assert objects_mid == objects_before

    # One-byte edit to a tracked file changes the key
    sample = repo_a / "tests" / "test_sample.py"
    orig_text = sample.read_text(encoding="utf-8")
    sample.write_text(orig_text + "\n", encoding="utf-8")
    key_tracked_edit = suite_cache.suite_key(repo_a, env=env)
    assert key_tracked_edit.digest != key_a.digest
    assert key_tracked_edit.components["tree"] != key_a.components["tree"]
    sample.write_text(orig_text, encoding="utf-8")
    assert suite_cache.suite_key(repo_a, env=env).digest == key_a.digest

    # Untracked non-ignored test file changes the key without mutating the real object store
    extra_test = repo_a / "tests" / "test_untracked.py"
    extra_test.write_text("def test_extra():\n    assert True\n", encoding="utf-8")
    objects_pre_untracked = _count_git_objects(repo_a)
    key_untracked = suite_cache.suite_key(repo_a, env=env)
    objects_post_untracked = _count_git_objects(repo_a)
    assert key_untracked.digest != key_a.digest
    assert key_untracked.components["tree"] != key_a.components["tree"]
    assert objects_post_untracked == objects_pre_untracked
    extra_test.unlink()

    # Setting PYTEST_ADDOPTS changes the key and does not persist raw env values
    env_with_addopts = dict(env)
    env_with_addopts["PYTEST_ADDOPTS"] = "-k test_ok --maxfail=1"
    key_env = suite_cache.suite_key(repo_a, env=env_with_addopts)
    assert key_env.digest != key_a.digest
    assert key_env.components["env"] != key_a.components["env"]
    assert "maxfail" not in json.dumps(key_env.components)

    # Non-git directory returns uncacheable SuiteKey(None, reason)
    non_git = tmp_path / "not_a_repo"
    non_git.mkdir()
    key_non_git = suite_cache.suite_key(non_git, env=env)
    assert key_non_git.cacheable is False
    assert key_non_git.digest is None
    assert key_non_git.reason != ""


def test_pass_stored_and_served(tmp_path: Path) -> None:
    """E-03 / E-04 / E-05 / E-08: passing suite is stored under <git-common-dir>/aw-suite-cache
    and served on the second call without executing pytest again.
    """
    repo = _init_fixture_repo(tmp_path / "repo")
    marker = repo / "ran.ignored"
    assert not marker.exists()

    first = _run_aw_suite(repo, "--agent")
    assert first.returncode == 0, f"First run failed: {first.stderr}\n{first.stdout}"
    rec1 = json.loads(first.stdout.strip())
    assert rec1["schema"] == "aw.agent/v1"
    assert rec1["passed"] is True
    assert rec1["cached"] is False
    assert rec1["digest"]
    assert marker.exists(), "First run must have executed pytest and written marker"

    cache_dir = suite_cache.suite_cache_dir(repo)
    assert cache_dir is not None and cache_dir.is_dir()
    cache_files = list(cache_dir.glob("*.json"))
    assert len(cache_files) == 1
    assert not (repo / "aw-suite-cache").exists()

    # Remove marker and run again: must serve from cache without running pytest
    marker.unlink()
    second = _run_aw_suite(repo, "--agent")
    assert second.returncode == 0
    rec2 = json.loads(second.stdout.strip())
    assert rec2["passed"] is True
    assert rec2["cached"] is True
    assert rec2["digest"] == rec1["digest"]
    assert not marker.exists(), "Cached second run must not execute pytest"

    # Human mode on a cache hit prints the cached result line
    human_hit = _run_aw_suite(repo)
    assert human_hit.returncode == 0
    assert "aw suite: cached result for tree" in human_hit.stdout
    assert not marker.exists()

    # --no-cache forces a fresh run and still stores
    forced = _run_aw_suite(repo, "--no-cache", "--agent")
    assert forced.returncode == 0
    rec_forced = json.loads(forced.stdout.strip())
    assert rec_forced["cached"] is False
    assert marker.exists()

    # --explain reports hit on unchanged tree and differing component 'tree' after tracked edit
    explain_hit = _run_aw_suite(repo, "--explain", "--agent")
    assert explain_hit.returncode == 0
    exp_rec = json.loads(explain_hit.stdout.strip())
    assert exp_rec["cached"] is True
    assert exp_rec["digest"] == rec1["digest"]

    sample = repo / "tests" / "test_sample.py"
    sample.write_text(sample.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    explain_miss = _run_aw_suite(repo, "--explain", "--agent")
    assert explain_miss.returncode == 0
    exp_miss_rec = json.loads(explain_miss.stdout.strip())
    assert exp_miss_rec["cached"] is False
    assert exp_miss_rec["compared_digest"] == rec1["digest"]
    assert exp_miss_rec["differing_components"] == ["tree"]


def test_flaky_failure_not_stored(tmp_path: Path) -> None:
    """E-03 / E-08: a failure that passes on its confirming re-run is returned as failed
    but never stored in the cache.
    """
    flaky_body = (
        "from pathlib import Path\n\n"
        "def test_flaky():\n"
        "    marker = Path('flake_once.ignored')\n"
        "    if not marker.exists():\n"
        "        marker.write_text('failed_once', encoding='utf-8')\n"
        "        assert False, 'transient failure'\n"
        "    assert True\n"
    )
    repo = _init_fixture_repo(tmp_path / "flaky_repo", test_body=flaky_body)

    res = _run_aw_suite(repo, "--agent")
    assert res.returncode == 1
    rec = json.loads(res.stdout.strip())
    assert rec["passed"] is False
    assert rec["cached"] is False
    assert rec["confirmed"] is False

    cache_dir = suite_cache.suite_cache_dir(repo)
    assert cache_dir is not None
    assert list(cache_dir.glob("*.json")) == []


def test_reproducible_failure_stored_and_not_served_to_seam(tmp_path: Path) -> None:
    """E-03 / E-06 / E-08: a reproducible failure is stored with confirmed=True after one
    confirming re-run, served to advisory `aw suite`, and NEVER served to a seam call
    (`serve_failures=False`).
    """
    fail_body = (
        "from pathlib import Path\n\n"
        "def test_always_fails():\n"
        "    p = Path('count.ignored')\n"
        "    n = int(p.read_text(encoding='utf-8')) if p.exists() else 0\n"
        "    p.write_text(str(n + 1), encoding='utf-8')\n"
        "    assert False, 'deterministic failure'\n"
    )
    repo = _init_fixture_repo(tmp_path / "fail_repo", test_body=fail_body)
    counter = repo / "count.ignored"

    first = _run_aw_suite(repo, "--agent")
    assert first.returncode == 1
    rec1 = json.loads(first.stdout.strip())
    assert rec1["passed"] is False
    assert rec1["cached"] is False
    assert rec1["confirmed"] is True
    # Ran once in full suite + once in confirming re-run of failing node id
    assert int(counter.read_text(encoding="utf-8")) == 2

    cache_dir = suite_cache.suite_cache_dir(repo)
    assert cache_dir is not None
    stored_files = list(cache_dir.glob("*.json"))
    assert len(stored_files) == 1
    stored_json = json.loads(stored_files[0].read_text(encoding="utf-8"))
    assert stored_json["passed"] is False
    assert stored_json["confirmed"] is True

    # Advisory CLI (`serve_failures=True`) serves the cached confirmed failure without running
    second = _run_aw_suite(repo, "--agent")
    assert second.returncode == 1
    rec2 = json.loads(second.stdout.strip())
    assert rec2["passed"] is False
    assert rec2["cached"] is True
    assert int(counter.read_text(encoding="utf-8")) == 2

    # Seam call (`serve_failures=False`) refuses to serve cached failure and runs again
    seam_res = suite_cache.run_full_suite(
        repo,
        serve_failures=False,
        env=_fixture_env(),
    )
    assert seam_res.passed is False
    assert seam_res.cached is False
    assert int(counter.read_text(encoding="utf-8")) > 2


def test_collection_error_and_corrupt_or_expired_records(tmp_path: Path) -> None:
    """E-03: collection errors with no node ids are never stored; corrupt records are ignored
    and overwritten; records older than 14 days are pruned; read-only cache dir fails open.
    """
    broken_body = "def test_broken(\n"
    broken_repo = _init_fixture_repo(tmp_path / "broken_repo", test_body=broken_body)
    res_broken = _run_aw_suite(broken_repo, "--agent")
    assert res_broken.returncode == 1
    cache_dir_broken = suite_cache.suite_cache_dir(broken_repo)
    assert cache_dir_broken is not None
    assert list(cache_dir_broken.glob("*.json")) == []

    # Corrupt and expired record handling on a passing repo
    repo = _init_fixture_repo(tmp_path / "clean_repo")
    env = _fixture_env()
    key = suite_cache.suite_key(repo, env=env)
    assert key.digest is not None
    cache_dir = suite_cache.suite_cache_dir(repo)
    assert cache_dir is not None
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Plant a corrupt record at key.digest and an expired (>14d) record beside it
    corrupt_path = cache_dir / f"{key.digest}.json"
    corrupt_path.write_text("{not valid json", encoding="utf-8")
    expired_path = cache_dir / ("0" * 64 + ".json")
    expired_path.write_text(
        json.dumps(
            {
                "digest": "0" * 64,
                "passed": True,
                "exit_code": 0,
                "summary": "1 passed",
                "failures": [],
                "recorded_at": "2020-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    old_ts = time.time() - (20 * 24 * 60 * 60)
    os.utime(expired_path, (old_ts, old_ts))

    assert suite_cache.read_cached_record(repo, key.digest) is None
    run_res = suite_cache.run_full_suite(repo, env=env)
    assert run_res.passed is True
    assert run_res.cached is False
    assert not expired_path.exists(), "Expired >14d record must be pruned on write"
    repaired = suite_cache.read_cached_record(repo, key.digest)
    assert repaired is not None and repaired["passed"] is True

    # Read-only cache dir fails open with one stderr note without failing the suite
    corrupt_path.unlink()
    cache_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        ro_res = _run_aw_suite(repo, "--no-cache", "--agent")
        assert ro_res.returncode == 0
        assert "aw suite: cache write skipped" in ro_res.stderr
    finally:
        cache_dir.chmod(stat.S_IRWXU)


def test_narrowed_selection_refused(tmp_path: Path) -> None:
    """E-09 / E-08: narrowed selections exit 2 with SUITE_REFUSAL_MESSAGE and write no cache."""
    repo = _init_fixture_repo(tmp_path / "refusal_repo")
    cache_dir = suite_cache.suite_cache_dir(repo)
    assert cache_dir is not None

    for bad_args in (
        ("tests/x.py",),
        ("-k", "x"),
        ("-m", "slow"),
        ("t.py::test_a",),
    ):
        res = _run_aw_suite(repo, *bad_args)
        assert (
            res.returncode == 2
        ), f"Expected exit 2 for {bad_args}, got {res.returncode}"
        assert suite_cache.SUITE_REFUSAL_MESSAGE in res.stderr
        assert not cache_dir.exists() or list(cache_dir.glob("*.json")) == []


def test_worker_bound_from_aw_suite_slots(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """E-04 / E-08: AW_SUITE_SLOTS=3 with cpu_count=12 yields worker_count=4 and -n 4 in PYTEST_ADDOPTS."""
    monkeypatch.setattr(os, "cpu_count", lambda: 12)
    child_env, workers = suite_cache.build_suite_child_env(
        {"AW_SUITE_SLOTS": "3", "PYTEST_ADDOPTS": "-q"}
    )
    assert workers == 4
    assert child_env["PYTEST_ADDOPTS"] == "-q -n 4"

    # Default slots on 12 CPUs is max(1, 12 // 6) == 2 -> workers == 6
    default_env, default_workers = suite_cache.build_suite_child_env({})
    assert default_workers == 6
    assert "-n 6" in default_env["PYTEST_ADDOPTS"]

    # Invalid AW_SUITE_SLOTS warns once on stderr and falls back to default
    bad_env, bad_workers = suite_cache.build_suite_child_env(
        {"AW_SUITE_SLOTS": "not-an-int"}
    )
    captured = capsys.readouterr()
    assert bad_workers == 6
    assert "-n 6" in bad_env["PYTEST_ADDOPTS"]
    assert "invalid AW_SUITE_SLOTS" in captured.err


def test_runner_seams_cache_hit_miss_and_failure_rerun(tmp_path: Path) -> None:
    """E-06 / V-06: run_suite_check, start_suite_baseline, and make_integration_validation_runner
    route through run_full_suite, recording cached: True on a stored PASS, cached: False on a miss,
    and re-running (`cached: False`) when the stored record is a confirmed FAILURE.
    """
    repo = _init_fixture_repo(tmp_path / "seam_repo")
    base_commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with mock.patch.dict(os.environ, _fixture_env(), clear=False):
        # 1. Seam 1 (`run_suite_check`): first call is a miss (`cached=False`), second is a hit (`cached=True`)
        sc_miss = runner_shared.run_suite_check(repo, "run-seamtest01")
        assert sc_miss.passing is True
        assert sc_miss.cached is False
        assert sc_miss.digest is not None

        sc_hit = runner_shared.run_suite_check(repo, "run-seamtest01")
        assert sc_hit.passing is True
        assert sc_hit.cached is True
        assert sc_hit.digest == sc_miss.digest

        # 2. Seam 2 (`start_suite_baseline`): detached baseline checkout at the same commit hits the shared cache
        run_obj, absent_obj = runner_shared.start_suite_baseline(
            repo,
            id6="0o0wt2",
            attempt=1,
            base_commit=base_commit,
            argv=list(runner_shared.SUITE_CHECK_ARGV),
            extract_failures=runner_shared.extract_suite_failures,
            parse_summary=runner_shared.parse_suite_summary,
        )
        assert absent_obj is None
        assert run_obj is not None
        try:
            baseline = run_obj.collect(wait_seconds=30.0)
        finally:
            runner_shared.remove_suite_baseline_checkout(repo, run_obj.checkout)
        assert baseline.state == runner_shared.SUITE_BASELINE_COMPLETED
        assert baseline.exit_code == 0
        assert baseline.cached is True
        assert baseline.digest == sc_miss.digest
        assert baseline.as_record()["cached"] is True
        assert baseline.as_record()["digest"] == sc_miss.digest

        # 3. Seam 3 (`make_integration_validation_runner`): hits the shared cache on the same tree
        run_dir = tmp_path / "run_dir"
        run_dir.mkdir(parents=True, exist_ok=True)
        state: dict[str, object] = {
            "repo": str(repo),
            "run_id": "run-seamtest01",
            "options": {"validate": False},
        }
        item: dict[str, object] = {
            "id6": "0o0wt2",
            "base_commit": base_commit,
            "lane_head": base_commit,
            "attempts": [],
        }
        reval_runner = runner_shared.make_integration_validation_runner(
            state,
            run_dir,
            item,
            suite_check=runner_shared.run_suite_check,
        )
        assert reval_runner("", ["tests/test_sample.py"]) is True
        reval_rec = item["post_merge_revalidation"]  # type: ignore[index]
        assert reval_rec["passed"] is True
        assert reval_rec["cached"] is True
        assert reval_rec["digest"] == sc_miss.digest

        # 4. Stored confirmed FAILURE is NEVER served to any of the 3 seams (`cached: False`)
        (repo / "tests" / "test_sample.py").write_text(
            "def test_fail():\n    assert False\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-am", "fail"],
            check=True,
            capture_output=True,
        )
        fail_commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Populate a confirmed FAILURE record in the cache
        adv_fail = suite_cache.run_full_suite(
            repo,
            use_cache=True,
            serve_failures=True,
            stream=False,
        )
        assert adv_fail.passed is False
        assert adv_fail.cached is False
        adv_fail_hit = suite_cache.run_full_suite(
            repo,
            use_cache=True,
            serve_failures=True,
            stream=False,
        )
        assert adv_fail_hit.passed is False
        assert adv_fail_hit.cached is True

        # Seam 1 re-runs (`cached: False`)
        sc_fail = runner_shared.run_suite_check(repo, "run-seamtest02")
        assert sc_fail.passing is False
        assert sc_fail.cached is False
        assert sc_fail.digest == adv_fail.digest

        # Seam 2 re-runs (`cached: False`)
        run_fail, absent_fail = runner_shared.start_suite_baseline(
            repo,
            id6="0o0wt2",
            attempt=2,
            base_commit=fail_commit,
            argv=list(runner_shared.SUITE_CHECK_ARGV),
            extract_failures=runner_shared.extract_suite_failures,
            parse_summary=runner_shared.parse_suite_summary,
        )
        assert absent_fail is None
        assert run_fail is not None
        try:
            baseline_fail = run_fail.collect(wait_seconds=30.0)
        finally:
            runner_shared.remove_suite_baseline_checkout(repo, run_fail.checkout)
        assert baseline_fail.state == runner_shared.SUITE_BASELINE_COMPLETED
        assert baseline_fail.exit_code != 0
        assert baseline_fail.cached is False
        assert baseline_fail.digest == adv_fail.digest

        # Seam 3 re-runs (`cached: False`)
        item_fail: dict[str, object] = {
            "id6": "0o0wt2",
            "base_commit": fail_commit,
            "lane_head": fail_commit,
            "attempts": [],
        }
        reval_fail_runner = runner_shared.make_integration_validation_runner(
            state,
            run_dir,
            item_fail,
            suite_check=runner_shared.run_suite_check,
        )
        assert reval_fail_runner("", ["tests/test_sample.py"]) is False
        reval_fail_rec = item_fail["post_merge_revalidation"]  # type: ignore[index]
        assert reval_fail_rec["passed"] is False
        assert reval_fail_rec["cached"] is False
        assert reval_fail_rec["digest"] == adv_fail.digest


def test_rendered_prompts_contain_aw_suite(tmp_path: Path) -> None:
    """E-07 / V-07 / E-08: rendered execute, verify, and audit prompts each instruct running
    narrowed checks with `python3 -m pytest <test_file>` and the full suite with `aw suite`.
    """
    run_dir = tmp_path / "run"
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "plan.ipd.md"
    plan_path.write_text("# Plan\n", encoding="utf-8")

    item = {
        "position": 1,
        "id6": "0o0wt2",
        "setid": "suiteeff",
        "status": "in-progress",
        "configured_file": "plan.ipd.md",
        "attempts": [],
    }
    state = {
        "run_id": "run-prompttest",
        "repo": str(tmp_path),
        "options": {"self_finalize": True},
    }

    exec_prompt = runner_shared.build_prompt(
        item,
        state,
        run_dir,
        plan_path,
        recovery=False,
        lane_root=tmp_path,
        labels=runner_shared.OC_HOST_LABELS,
    )
    verify_prompt = runner_shared.build_verifier_prompt(
        item,
        state,
        run_dir,
        plan_path,
        labels=runner_shared.OC_HOST_LABELS,
    )
    audit_prompt = runner_shared.build_verifier_prompt(
        item,
        state,
        run_dir,
        plan_path,
        labels=runner_shared.OC_HOST_LABELS,
        audit=True,
        diff_basis="HEAD~1..HEAD",
    )

    for label, text in (
        ("execute", exec_prompt),
        ("verify", verify_prompt),
        ("audit", audit_prompt),
    ):
        assert "aw suite" in text, f"{label} prompt missing 'aw suite'"
        assert (
            "python3 -m pytest <test_file>" in text
        ), f"{label} prompt missing narrowed pytest guidance"
