"""End-to-end behavioral tests for companion storage layout, Git detection, target containment, and guidance.

Covers IPD mnsbzt (Set companion-bugs, Order 01; backlog rvxmzz items 1, 2, 4, 5, 9).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli, engine, work_cmd
from agent_workflows.project_schema import DurabilityState
from agent_workflows.storage import get_storage_status, init_records_storage
from tests import support
from tests.support import REPO_ROOT, init_repo

WORKFLOWS_SOURCE = REPO_ROOT / ".aw" / "system" / "workflows"


def _make_env(tmp_root: Path) -> dict[str, str]:
    home = tmp_root / "home"
    aw_home = tmp_root / "aw_home"
    home.mkdir(parents=True, exist_ok=True)
    aw_home.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["AW_NO_REEXEC"] = "1"
    env["HOME"] = str(home)
    env["AW_HOME"] = str(aw_home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["GIT_AUTHOR_NAME"] = "Test Author"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"
    env["GIT_COMMITTER_NAME"] = "Test Committer"
    env["GIT_COMMITTER_EMAIL"] = "test@example.com"
    return env


def _run_aw(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_head(repo: Path) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _extract_managed_block(text: str) -> str:
    open_m = re.search(r"<!--\s*aw:block\s*-->", text)
    close_m = re.search(r"<!--\s*/aw:block\s*-->", text)
    if open_m and close_m:
        return text[open_m.end() : close_m.start()]
    return ""


def _run_aw_inproc(
    args: list[str],
    *,
    env: dict[str, str],
) -> tuple[int, str, str]:
    """Run ``aw`` CLI in-process with isolated env, returning (rc, stdout, stderr)."""
    saved = {
        k: os.environ.get(k)
        for k in ("HOME", "AW_HOME", "XDG_CONFIG_HOME", "AW_NO_REEXEC")
    }
    for k in saved:
        os.environ[k] = env[k]
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                rc = int(cli.main(args))
            except SystemExit as exc:
                rc = int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _run_commit_inproc(
    target: Path,
    argv_after_commit: list[str],
    *,
    env: dict[str, str],
) -> tuple[int, str, str]:
    """Invoke ``work_cmd.run_commit`` directly with isolated env."""
    saved = {
        k: os.environ.get(k)
        for k in ("HOME", "AW_HOME", "XDG_CONFIG_HOME", "AW_NO_REEXEC")
    }
    for k in saved:
        os.environ[k] = env[k]
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    ns = argparse.Namespace(
        dir=str(target),
        no_plan=False,
        message=None,
        no_commit=False,
        commit=True,
        scope_reason=[],
        path_argv=list(argv_after_commit),
    )
    try:
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            rc = work_cmd.run_commit(ns)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _install_companion_fixture(
    td_path: Path,
    *,
    commit_install: bool = True,
    subprocess_install: bool = False,
) -> tuple[Path, Path, dict[str, str]]:
    """Provision real target + companion Git repos using public-target-private-companion."""
    target = td_path / "target_repo"
    companion = td_path / "companion_repo"
    init_repo(target)
    (target / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    support.git(target, "add", "app.py")
    support.git(target, "commit", "-m", "initial target commit")

    env = _make_env(td_path)
    install_argv = [
        "install",
        str(target),
        "--preset",
        "public-target-private-companion",
        "--companion-dir",
        str(companion),
        "-y",
        "--no-interactive",
    ]
    if subprocess_install:
        install_res = _run_aw(install_argv, cwd=REPO_ROOT, env=env)
        rc, out, err = install_res.returncode, install_res.stdout, install_res.stderr
    else:
        rc, out, err = _run_aw_inproc(install_argv, env=env)
    if rc != 0:
        raise AssertionError(
            f"Companion install failed (exit {rc}):\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        )

    if commit_install:
        subprocess.run(
            ["git", "-C", str(target), "add", ".aw/.gitignore", "AGENTS.md"],
            env=env,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "-C", str(target), "commit", "-m", "commit aw install files"],
            env=env,
            capture_output=True,
            check=False,
        )

    return target, companion, env


class TestCompanionContainmentAndStorage(unittest.TestCase):
    """End-to-end tests for companion layout, Git detection, containment, and guidance."""

    def setUp(self) -> None:
        self.enterContext(support.execution_role(None))

    def test_a_and_b_companion_layout_and_git_detection(self) -> None:
        """(a)-(b) Companion creates <companion>/records/ (no decoy .aw/records/), detects <companion>/.git,
        distinguishes unborn HEAD vs committed repo, and avoids nesting <companion>/records/.git."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _install_companion_fixture(td_path)

            # (a) Real records dir exists; empty decoy .aw/records does NOT exist.
            self.assertTrue((companion / "records").is_dir())
            self.assertFalse((companion / ".aw" / "records").exists())
            self.assertTrue((companion / ".git").exists())
            self.assertFalse((companion / "records" / ".git").exists())

            # (b1) Companion Git repo initialized with zero commits (unborn HEAD)
            res_json_zero = _run_aw(
                ["storage", "status", "--repo", str(target), "--json"],
                cwd=REPO_ROOT,
                env=env,
            )
            self.assertEqual(
                res_json_zero.returncode,
                0,
                f"storage status --json failed:\n{res_json_zero.stdout}\n{res_json_zero.stderr}",
            )
            payload_zero = json.loads(res_json_zero.stdout)
            data_zero = payload_zero.get("data", payload_zero)
            self.assertEqual(data_zero["records_backend"], "companion")
            self.assertTrue(data_zero["has_git"])
            self.assertEqual(
                data_zero["durability_state"], DurabilityState.LOCAL_GIT.value
            )
            rec_zero = data_zero["recommendation"]
            self.assertIn("no commits", rec_zero.lower())

            rc_human_zero, out_human_zero, _ = _run_aw_inproc(
                ["storage", "status", "--repo", str(target)],
                env=env,
            )
            self.assertEqual(rc_human_zero, 0)
            self.assertRegex(out_human_zero, r"Has Git:\s+True")
            self.assertIn("local-git", out_human_zero)

            # (b2) Commit inside companion repo -> recommendation distinguishes committed history
            (companion / "records" / "note.md").write_text("# Note\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(companion), "config", "user.name", "Test Author"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(companion),
                    "config",
                    "user.email",
                    "test@example.com",
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(companion), "add", "records/note.md"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(companion),
                    "commit",
                    "-m",
                    "initial companion commit",
                ],
                check=True,
                capture_output=True,
                env=env,
            )

            rc_json_committed, out_json_committed, _ = _run_aw_inproc(
                ["storage", "status", "--repo", str(target), "--json"],
                env=env,
            )
            self.assertEqual(rc_json_committed, 0)
            payload_committed = json.loads(out_json_committed)
            data_committed = payload_committed.get("data", payload_committed)
            self.assertTrue(data_committed["has_git"])
            self.assertEqual(
                data_committed["durability_state"], DurabilityState.LOCAL_GIT.value
            )
            rec_committed = data_committed["recommendation"]
            self.assertNotEqual(rec_zero, rec_committed)
            self.assertNotIn("no commits", rec_committed.lower())
            self.assertIn("local git history", rec_committed.lower())

            rc_human_committed, out_human_committed, _ = _run_aw_inproc(
                ["storage", "status", "--repo", str(target)],
                env=env,
            )
            self.assertEqual(rc_human_committed, 0)
            self.assertRegex(out_human_committed, r"Has Git:\s+True")

            # (b3) init_records_storage does NOT create nested <companion>/records/.git
            st_init = init_records_storage(
                repo_path=str(target), aw_home=env["AW_HOME"], git_init=True
            )
            self.assertTrue(st_init.has_git)
            self.assertFalse((companion / "records" / ".git").exists())

            # (b4) Remote on <companion>/.git is detected via resolved Git root
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(companion),
                    "remote",
                    "add",
                    "origin",
                    "https://example.invalid/companion.git",
                ],
                check=True,
                capture_output=True,
            )
            with patch("agent_workflows.storage._remote_reachable", return_value=False):
                st_remote = get_storage_status(
                    repo_path=str(target), aw_home=env["AW_HOME"]
                )
            self.assertTrue(st_remote.has_git)
            self.assertEqual(st_remote.remote_url, "example.invalid/companion")
            self.assertEqual(
                st_remote.durability_state, DurabilityState.UNACKNOWLEDGED_REMOTE.value
            )

            # (b5) If <companion>/.git is absent, init_records_storage initializes <companion>/.git (not records/.git)
            shutil.rmtree(companion / ".git")
            st_unversioned = get_storage_status(
                repo_path=str(target), aw_home=env["AW_HOME"]
            )
            self.assertFalse(st_unversioned.has_git)
            self.assertEqual(
                st_unversioned.durability_state, DurabilityState.UNVERSIONED.value
            )
            st_reinit = init_records_storage(
                repo_path=str(target), aw_home=env["AW_HOME"], git_init=True
            )
            self.assertTrue(st_reinit.has_git)
            self.assertTrue((companion / ".git").is_dir())
            self.assertFalse((companion / "records" / ".git").exists())

    def test_c_target_aw_gitignore_ignores_records_on_fresh_and_reinstall(self) -> None:
        """(c) Fresh install and re-install both ensure target .aw/.gitignore ignores .aw/records/,
        while dry-run makes no writes."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, _companion, env = _install_companion_fixture(td_path)

            aw_gi = target / ".aw" / ".gitignore"
            self.assertTrue(aw_gi.is_file())
            gi_lines = [
                ln.strip() for ln in aw_gi.read_text(encoding="utf-8").splitlines()
            ]
            self.assertIn("/records/", gi_lines)

            stray = target / ".aw" / "records" / "plans" / "pending" / "stray.ipd.md"
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_text("# Stray\n", encoding="utf-8")

            ci_fresh = subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "check-ignore",
                    "-v",
                    ".aw/records/plans/pending/stray.ipd.md",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(ci_fresh.returncode, 0, f"Not ignored: {ci_fresh.stderr}")
            self.assertIn(".aw/.gitignore", ci_fresh.stdout)
            self.assertIn("/records/", ci_fresh.stdout)

            # Simulate an already-installed companion repo whose .aw/.gitignore predates /records/
            stripped = (
                "\n".join(
                    ln
                    for ln in aw_gi.read_text(encoding="utf-8").splitlines()
                    if ln.strip() != "/records/" and "companion backend:" not in ln
                )
                + "\n"
            )
            aw_gi.write_text(stripped, encoding="utf-8")
            support.git(target, "add", ".aw/.gitignore")
            support.git(target, "commit", "-m", "strip /records/ from .aw/.gitignore")

            ci_before = subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "check-ignore",
                    ".aw/records/plans/pending/stray.ipd.md",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(
                ci_before.returncode,
                0,
                "Precondition failed: stray file should not be ignored after stripping /records/",
            )

            # Dry-run re-install must NOT modify .aw/.gitignore
            prev_aw_home = os.environ.get("AW_HOME")
            os.environ["AW_HOME"] = env["AW_HOME"]
            try:
                engine.install_into_repo(
                    target, WORKFLOWS_SOURCE, dry_run=True, yes=True, no_color=True
                )
            finally:
                if prev_aw_home is None:
                    os.environ.pop("AW_HOME", None)
                else:
                    os.environ["AW_HOME"] = prev_aw_home
            self.assertEqual(aw_gi.read_text(encoding="utf-8"), stripped)

            # Real re-install must restore anchored /records/ and stage .aw/.gitignore
            rc_re, out_re, err_re = _run_aw_inproc(
                [
                    "install",
                    str(target),
                    "-y",
                    "--no-interactive",
                ],
                env=env,
            )
            self.assertEqual(
                rc_re,
                0,
                f"Re-install failed:\n{out_re}\n{err_re}",
            )
            re_lines = [
                ln.strip() for ln in aw_gi.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(re_lines.count("/records/"), 1)

            ci_after = subprocess.run(
                [
                    "git",
                    "-C",
                    str(target),
                    "check-ignore",
                    "-v",
                    ".aw/records/plans/pending/stray.ipd.md",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                ci_after.returncode,
                0,
                f"Not ignored after reinstall: {ci_after.stderr}",
            )
            self.assertIn(".aw/.gitignore", ci_after.stdout)
            self.assertIn("/records/", ci_after.stdout)

    def test_d1_aw_commit_refuses_target_records_in_companion_mode(self) -> None:
        """(d1) aw commit refuses .aw/records/** across all bypass attempts in companion mode
        while permitting normal code commits once staged records are cleared."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _install_companion_fixture(td_path)

            # Create a real plan and a grandfathered plan in the companion records root.
            plan_id = "ab12cd"
            plan_name = f"20261121-test-01-{plan_id}-sample.ipd.md"
            comp_plan = companion / "records" / "plans" / "pending" / plan_name
            comp_plan.parent.mkdir(parents=True, exist_ok=True)
            comp_plan.write_text(
                f"# IPD: Sample companion plan\n\n"
                f"- Date: 2026-11-21\n"
                f"- Kind: child\n"
                f"- Concern: sample\n"
                f"- Scope: `app.py`\n"
                f"- Scope-Paths: app.py, .aw/records/plans/pending/leak.ipd.md\n"
                f"- Status: approved\n"
                f"- Short-Description: Sample plan\n"
                f"- Work-Kind: bug\n"
                f"- Priority: medium\n"
                f"- Set: test\n"
                f"- Order: 1\n"
                f"- Highest E allocated: 01\n"
                f"- Id: {plan_id}\n\n"
                f"## Detailed Implementation Checklist (TODO)\n\n"
                f"- [ ] E-01 Update app\n"
                f"  - Depends on: none\n"
                f"  - Expected outcome: Updated\n"
                f"  - Execution state: pending\n\n"
                f"## Validation and cross-check\n\n"
                f"- [ ] V-01 validates E-01\n"
                f"  - Required evidence: diff\n"
                f"  - Observed evidence:\n"
                f"  - Result: pending\n",
                encoding="utf-8",
            )
            gf_id = "ef34gh"
            gf_plan = (
                companion
                / "records"
                / "plans"
                / "pending"
                / f"20261121-test-02-{gf_id}-grandfathered.ipd.md"
            )
            gf_plan.write_text(
                f"# IPD: Grandfathered companion plan\n\n"
                f"- Date: 2026-11-21\n"
                f"- Status: approved\n"
                f"- Id: {gf_id}\n",
                encoding="utf-8",
            )

            # Plant a stray file under target-local .aw/records/
            stray_rel = ".aw/records/plans/pending/leak.ipd.md"
            stray_abs = target / stray_rel
            stray_abs.parent.mkdir(parents=True, exist_ok=True)
            stray_abs.write_text("# Private leak\n", encoding="utf-8")

            # Also plant a symlink in target root pointing into .aw/records/
            sym_path = target / "sneaky_link.md"
            sym_path.symlink_to(stray_abs)

            head_before = _git_head(target)

            # 1. --no-plan direct path (real CLI subprocess E2E)
            res_no_plan = _run_aw(
                ["commit", "--no-plan", "-m", "leak test", "--", stray_rel],
                cwd=target,
                env=env,
            )
            self.assertEqual(
                res_no_plan.returncode, 1, res_no_plan.stdout + res_no_plan.stderr
            )
            self.assertIn("aw path records", res_no_plan.stdout)
            self.assertIn(str(companion.resolve()), res_no_plan.stdout)
            self.assertIn(stray_rel, res_no_plan.stdout)
            self.assertEqual(_git_head(target), head_before)

            # 2. Plan-governed commit (even when Scope-Paths lists .aw/records/...)
            rc_plan, out_plan, err_plan = _run_commit_inproc(
                target, [plan_id, "-m", "plan leak", "--", stray_rel], env=env
            )
            self.assertEqual(rc_plan, 1, out_plan + err_plan)
            self.assertIn("aw path records", out_plan)
            self.assertEqual(_git_head(target), head_before)

            # 3. Grandfathered plan (no Scope-Paths)
            rc_gf, out_gf, err_gf = _run_commit_inproc(
                target, [gf_id, "-m", "gf leak", "--", stray_rel], env=env
            )
            self.assertEqual(rc_gf, 1, out_gf + err_gf)
            self.assertIn("aw path records", out_gf)
            self.assertEqual(_git_head(target), head_before)

            # 4. With --scope-reason supplied
            rc_reason, out_reason, err_reason = _run_commit_inproc(
                target,
                [
                    plan_id,
                    "--scope-reason",
                    f"{stray_rel}=attempt bypass",
                    "-m",
                    "bypass",
                    "--",
                    stray_rel,
                ],
                env=env,
            )
            self.assertEqual(rc_reason, 1, out_reason + err_reason)
            self.assertIn("aw path records", out_reason)
            self.assertEqual(_git_head(target), head_before)

            # 5. Normalized paths: ./ prefix, .. segment, backslashes, absolute path, symlink
            variant_paths = [
                f"./{stray_rel}",
                f"sub/../{stray_rel}",
                stray_rel.replace("/", "\\"),
                str(stray_abs),
                "sneaky_link.md",
            ]
            for variant in variant_paths:
                with self.subTest(variant=variant):
                    rc_v, out_v, err_v = _run_commit_inproc(
                        target,
                        ["--no-plan", "-m", "variant", "--", variant],
                        env=env,
                    )
                    self.assertEqual(
                        rc_v,
                        1,
                        f"Variant {variant!r} was not refused:\n{out_v}\n{err_v}",
                    )
                    self.assertIn("aw path records", out_v)
                    self.assertEqual(_git_head(target), head_before)

            # Remove symlink before testing normal commits
            sym_path.unlink()

            # 6. Directory target `.aw` when `.aw/records` has an unignored file
            aw_gi = target / ".aw" / ".gitignore"
            saved_gi = aw_gi.read_text(encoding="utf-8")
            aw_gi.write_text(
                "\n".join(
                    ln for ln in saved_gi.splitlines() if ln.strip() != "/records/"
                )
                + "\n",
                encoding="utf-8",
            )
            rc_dir, out_dir, err_dir = _run_commit_inproc(
                target, ["--no-plan", "-m", "dir target", "--", ".aw"], env=env
            )
            self.assertEqual(rc_dir, 1, out_dir + err_dir)
            self.assertIn("aw path records", out_dir)
            self.assertEqual(_git_head(target), head_before)
            aw_gi.write_text(saved_gi, encoding="utf-8")

            # 7. Pre-staged .aw/records/** file must refuse even when requesting a normal code file
            support.git(target, "add", "-f", stray_rel)
            (target / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
            rc_staged, out_staged, err_staged = _run_commit_inproc(
                target,
                ["--no-plan", "-m", "code with staged leak", "--", "app.py"],
                env=env,
            )
            self.assertEqual(rc_staged, 1, out_staged + err_staged)
            self.assertIn("aw path records", out_staged)
            self.assertIn(f"git restore --staged {stray_rel}", out_staged)
            self.assertEqual(_git_head(target), head_before)

            # Unstage the stray file -> normal code commit in companion mode succeeds!
            support.git(target, "restore", "--staged", stray_rel)
            rc_code, out_code, err_code = _run_commit_inproc(
                target,
                ["--no-plan", "-m", "legit code change", "--", "app.py"],
                env=env,
            )
            self.assertEqual(rc_code, 0, out_code + err_code)
            self.assertNotEqual(_git_head(target), head_before)

    def test_d2_aw_commit_permits_records_in_private_target_mode(self) -> None:
        """(d2) Non-companion private-target repo still permits committing .aw/records/**."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            env = _make_env(td_path)
            priv_target = td_path / "private_target"
            init_repo(priv_target)
            (priv_target / "app.py").write_text("X = 1\n", encoding="utf-8")
            support.git(priv_target, "add", "app.py")
            support.git(priv_target, "commit", "-m", "init private")
            priv_rc, priv_out, priv_err = _run_aw_inproc(
                [
                    "install",
                    str(priv_target),
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
            )
            self.assertEqual(priv_rc, 0, priv_out + priv_err)
            priv_rec = (
                priv_target / ".aw" / "records" / "plans" / "pending" / "ok.ipd.md"
            )
            priv_rec.parent.mkdir(parents=True, exist_ok=True)
            priv_rec.write_text("# Private-target plan\n", encoding="utf-8")
            priv_head_before = _git_head(priv_target)
            rc_priv, out_priv, err_priv = _run_commit_inproc(
                priv_target,
                [
                    "--no-plan",
                    "-m",
                    "commit plan in private-target",
                    "--",
                    ".aw/records/plans/pending/ok.ipd.md",
                ],
                env=env,
            )
            self.assertEqual(rc_priv, 0, out_priv + err_priv)
            self.assertNotEqual(_git_head(priv_target), priv_head_before)

    def test_e_agents_md_companion_guidance_and_non_companion_invariance(self) -> None:
        """(e) Companion AGENTS.md names aw path records and authoring verbs without AW-only tokens
        or em/en dashes; non-companion AGENTS.md omits the companion note and keeps 1-arg callers."""
        aw_only_tokens = [
            "python3 -m pytest",
            "pyproject.toml",
            "RELEASING.md",
            "CONTRIBUTING.md",
            "GUIDING_PRINCIPLES",
            "oc_runipd.py",
            "runner_shared.py",
            "ipd-spec",
        ]

        # 1-argument callers remain backwards-compatible and omit companion note.
        default_prose = engine.agents_pointer_prose("aw")
        default_sections = engine.agents_managed_sections("aw")
        self.assertNotIn("Companion records storage", default_prose)
        self.assertEqual(
            default_sections[0].lines,
            default_prose.splitlines(),
        )

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, _companion, env = _install_companion_fixture(td_path)
            agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
            managed_comp = _extract_managed_block(agents_text)

            self.assertIn("aw path records", managed_comp)
            self.assertIn("aw ipd scaffold", managed_comp)
            self.assertIn("aw backlog new", managed_comp)
            self.assertIn("aw specs new", managed_comp)
            self.assertIn("aw research new", managed_comp)
            self.assertIn("public-target-private-companion", managed_comp)
            self.assertNotIn("\u2014", managed_comp)  # no em dash
            self.assertNotIn("\u2013", managed_comp)  # no en dash
            for tok in aw_only_tokens:
                self.assertNotIn(tok, managed_comp)

            # Non-companion private-target install omits the companion note.
            priv_target = td_path / "private_target"
            init_repo(priv_target)
            (priv_target / "app.py").write_text("X = 1\n", encoding="utf-8")
            support.git(priv_target, "add", "app.py")
            support.git(priv_target, "commit", "-m", "init private")
            priv_rc, priv_out, priv_err = _run_aw_inproc(
                [
                    "install",
                    str(priv_target),
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
            )
            self.assertEqual(priv_rc, 0, priv_out + priv_err)
            managed_priv = _extract_managed_block(
                (priv_target / "AGENTS.md").read_text(encoding="utf-8")
            )
            self.assertNotIn("Companion records storage", managed_priv)
            self.assertNotIn("public-target-private-companion", managed_priv)


if __name__ == "__main__":
    unittest.main()
