"""End-to-end behavioral tests for linked-worktree companion context inheritance,
companion doctor diagnostics, and unified companion carrier/evidence resolution.

Covers IPD pbdtss (Set companion-bugs, Order 02; backlog rvxmzz items 3 and 6).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    artifact_core,
    check_engine,
    cli,
    config,
    doctor,
    project_context,
    storage,
)
from agent_workflows.project_schema import DurabilityState, LogicalRoot, RecordsBackend
from tests import support
from tests.support import init_repo


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
    env["AW_CONFIG_DIR"] = str(home / ".config" / "agent-workflows")
    env["GIT_AUTHOR_NAME"] = "Test Author"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"
    env["GIT_COMMITTER_NAME"] = "Test Committer"
    env["GIT_COMMITTER_EMAIL"] = "test@example.com"
    return env


@contextlib.contextmanager
def _patched_env(env: dict[str, str]):
    keys = (
        "HOME",
        "AW_HOME",
        "XDG_CONFIG_HOME",
        "AW_CONFIG_DIR",
        "AW_NO_REEXEC",
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    )
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ[k] = env[k]
    project_context._RESOLVE_CTX_CACHE.clear()
    project_context._resolve_stored_physical_classes_cached.cache_clear()
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        project_context._RESOLVE_CTX_CACHE.clear()
        project_context._resolve_stored_physical_classes_cached.cache_clear()


def _run_aw_inproc(args: list[str], *, env: dict[str, str]) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with _patched_env(env):
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                rc = int(cli.main(args))
            except SystemExit as exc:
                rc = int(exc.code) if isinstance(exc.code, int) else 1
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _install_companion_repo(
    td_path: Path,
    *,
    companion_name: str = "companion_repo",
    commit_project_json: bool = False,
) -> tuple[Path, Path, dict[str, str]]:
    """Provision real target + companion Git repositories using public-target-private-companion."""
    target = td_path / "target_repo"
    companion = td_path / companion_name
    init_repo(target)
    (target / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    support.git(target, "add", "app.py")
    support.git(target, "commit", "-m", "initial target commit")

    env = _make_env(td_path)
    rc, out, err = _run_aw_inproc(
        [
            "install",
            str(target),
            "--preset",
            "public-target-private-companion",
            "--companion-dir",
            str(companion),
            "-y",
            "--no-interactive",
        ],
        env=env,
    )
    if rc != 0:
        raise AssertionError(
            f"Companion install failed (exit {rc}):\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        )

    # Stamp durable_carrier cutover in project.json so carrier checks run at error severity
    proj_json = target / ".aw" / "config" / "project.json"
    if proj_json.is_file():
        data = json.loads(proj_json.read_text(encoding="utf-8"))
        cutovers = data.setdefault("cutovers", {})
        cutovers.setdefault("durable_carrier", "2026-01-01")
        proj_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    stage_paths = [".aw/.gitignore", "AGENTS.md"]
    if commit_project_json and proj_json.is_file():
        stage_paths.append(".aw/config/project.json")
    subprocess.run(
        ["git", "-C", str(target), "add", "-f", *stage_paths],
        env=env,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["git", "-C", str(target), "commit", "-m", "commit aw target install files"],
        env=env,
        capture_output=True,
        check=False,
    )
    return target, companion, env


def _provision_lightweight_companion_repo(
    td_path: Path,
    *,
    commit_project_json: bool = False,
) -> tuple[Path, Path, dict[str, str]]:
    """Provision real target + companion Git repos with companion config (without copying all workflow docs)."""
    target = td_path / "target_repo"
    companion = td_path / "companion_repo"
    init_repo(target)
    init_repo(companion)
    (target / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    support.git(target, "add", "app.py")
    support.git(target, "commit", "-m", "initial target commit")

    env = _make_env(td_path)
    (target / ".aw" / "config").mkdir(parents=True, exist_ok=True)
    (target / ".aw" / "system").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "specs").mkdir(parents=True, exist_ok=True)

    proj_data = {
        "schema_version": 2,
        "preset": "public-target-private-companion",
        "delivery_mode": "tracked",
        "records_backend": "companion",
        "cutovers": {"durable_carrier": "2026-01-01"},
    }
    proj_json = target / ".aw" / "config" / "project.json"
    proj_json.write_text(json.dumps(proj_data, indent=2) + "\n", encoding="utf-8")
    local_json = target / ".aw" / "config" / "local.json"
    local_json.write_text(
        json.dumps({"companion_dir": companion.resolve().as_posix()}, indent=2) + "\n",
        encoding="utf-8",
    )
    storage.write_local_attachment_record(
        target, companion, "test-proj", ["config", "durable_state", "records"]
    )
    (target / ".aw" / ".gitignore").write_text(
        "/config/local.json\n/state/\n/records/\n", encoding="utf-8"
    )
    stage_paths = [".aw/.gitignore"]
    if commit_project_json:
        stage_paths.append(".aw/config/project.json")
    subprocess.run(
        ["git", "-C", str(target), "add", "-f", *stage_paths],
        env=env,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["git", "-C", str(target), "commit", "-m", "commit companion target config"],
        env=env,
        capture_output=True,
        check=False,
    )
    return target, companion, env


def _add_linked_worktree(
    primary: Path, wt_path: Path, branch: str, env: dict[str, str]
) -> Path:
    res = subprocess.run(
        ["git", "-C", str(primary), "worktree", "add", "-b", branch, str(wt_path)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise AssertionError(
            f"git worktree add failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )
    return wt_path


def _write_plan(
    plans_root: Path,
    bucket: str,
    *,
    id6: str,
    setid: str,
    order: int,
    slug: str,
    status: str,
    deferred_block: str = "None.",
) -> Path:
    p = plans_root / bucket / f"20261121-{setid}-{order:02d}-{id6}-{slug}.ipd.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    text = (
        f"# IPD: {slug}\n\n"
        f"- Date: 2026-11-21\n"
        f"- Kind: child\n"
        f"- Concern: {slug}\n"
        f"- Scope: `app.py`\n"
        f"- Scope-Paths: app.py\n"
        f"- Status: {status}\n"
        f"- Short-Description: Test plan {id6}\n"
        f"- Work-Kind: bug\n"
        f"- Priority: high\n"
        f"- Set: {setid}\n"
        f"- Order: {order}\n"
        f"- Highest E allocated: 01\n"
        f"- Author: Test\n"
        f"- Id: {id6}\n\n"
        f"## Goal\n\nTest plan.\n\n"
        f"## Detailed Implementation Checklist (TODO)\n\n"
        f"- [ ] E-01 Do work\n"
        f"  - Depends on: none\n"
        f"  - Expected outcome: Done.\n"
        f"  - Execution state: pending\n\n"
        f"## Deferred / out of scope (with reason)\n\n"
        f"{deferred_block}\n\n"
        f"## Open questions\n\nNone.\n\n"
        f"## Validation and cross-check (verify before reporting done)\n\n"
        f"- [ ] V-01 validates E-01\n"
        f"  - Required evidence: Done.\n"
        f"  - Observed evidence:\n"
        f"  - Result: pending\n"
    )
    p.write_text(text, encoding="utf-8")
    return p


class TestLinkedWorktreeCompanionContext(unittest.TestCase):
    """E-01/V-01: Linked worktree companion context inheritance, durability, and cache invalidation."""

    def setUp(self) -> None:
        self.enterContext(support.execution_role(None))

    def test_committed_project_json_with_gitignored_local_and_attachment(self) -> None:
        """Linked worktree with committed project.json inherits primary local.json,
        companion_attachment.json, and companion Git durability state."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _install_companion_repo(
                td_path, commit_project_json=True
            )
            wt = _add_linked_worktree(target, td_path / "wt_committed", "feat/wt1", env)

            self.assertTrue((wt / ".aw" / "config" / "project.json").is_file())
            self.assertFalse((wt / ".aw" / "config" / "local.json").exists())
            self.assertFalse(
                (
                    wt / ".aw" / "state" / "durable" / "companion_attachment.json"
                ).exists()
            )

            expected_records = (companion / "records").resolve().as_posix()
            with _patched_env(env):
                ctx_primary = project_context.resolve_project_context(
                    target_repo=str(target)
                )
                ctx_wt = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(
                    ctx_primary.records_backend, RecordsBackend.COMPANION.value
                )
                self.assertEqual(
                    ctx_primary.logical_roots[LogicalRoot.RECORDS.value],
                    expected_records,
                )
                self.assertEqual(
                    ctx_primary.durability_state, DurabilityState.LOCAL_GIT.value
                )

                self.assertEqual(ctx_wt.records_backend, RecordsBackend.COMPANION.value)
                self.assertEqual(
                    ctx_wt.logical_roots[LogicalRoot.RECORDS.value], expected_records
                )
                self.assertEqual(
                    ctx_wt.durability_state, DurabilityState.LOCAL_GIT.value
                )
                self.assertEqual(
                    project_context.project_records_dir(wt).resolve().as_posix(),
                    expected_records,
                )
                ident = project_context.read_project_identity(wt)
                self.assertEqual(ident["preset"], "public-target-private-companion")
                self.assertEqual(ident["records_backend"], "companion")

    def test_absent_project_json_in_worktree_inherits_primary_config(self) -> None:
        """Linked worktree lacking .aw/config/ inherits primary project.json, local.json,
        identity, cutover date, and companion records root."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _install_companion_repo(
                td_path, commit_project_json=False
            )
            wt = _add_linked_worktree(target, td_path / "wt_absent", "feat/wt2", env)

            self.assertFalse((wt / ".aw" / "config" / "project.json").exists())
            self.assertFalse((wt / ".aw" / "config" / "local.json").exists())

            expected_records = (companion / "records").resolve().as_posix()
            with _patched_env(env):
                cfg_dir = project_context.project_config_dir(wt)
                self.assertEqual(
                    cfg_dir.resolve(), (target / ".aw" / "config").resolve()
                )
                ctx_wt = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(ctx_wt.records_backend, RecordsBackend.COMPANION.value)
                self.assertEqual(
                    ctx_wt.logical_roots[LogicalRoot.RECORDS.value], expected_records
                )
                self.assertEqual(
                    ctx_wt.durability_state, DurabilityState.LOCAL_GIT.value
                )
                self.assertEqual(
                    project_context.project_records_dir(wt).resolve().as_posix(),
                    expected_records,
                )
                ident = project_context.read_project_identity(wt)
                self.assertEqual(ident["preset"], "public-target-private-companion")
                self.assertEqual(ident["records_backend"], "companion")
                self.assertEqual(
                    config.resolve_cutover_date(wt, "durable_carrier"), "20260101"
                )

    def test_attachment_only_default_fallback_user_repos_and_security(self) -> None:
        """Tests attachment-only companion resolution, default <primary>.aw anchor,
        user_cfg repos primary fallback, and path-security rejection."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _install_companion_repo(
                td_path, commit_project_json=True
            )
            wt = _add_linked_worktree(target, td_path / "wt_att", "feat/wt3", env)

            local_json = target / ".aw" / "config" / "local.json"
            att_json = (
                target / ".aw" / "state" / "durable" / "companion_attachment.json"
            )

            # 1. Remove local.json so companion_attachment.json supplies companion_dir
            if local_json.exists():
                local_json.unlink()
            custom_comp = td_path / "attached_custom_comp"
            (custom_comp / "records").mkdir(parents=True, exist_ok=True)
            init_repo(custom_comp)
            storage.write_local_attachment_record(
                target, custom_comp, "proj-1", ["records"]
            )

            with _patched_env(env):
                ctx_wt = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(
                    ctx_wt.logical_roots[LogicalRoot.RECORDS.value],
                    (custom_comp / "records").resolve().as_posix(),
                )
                self.assertEqual(
                    ctx_wt.durability_state, DurabilityState.LOCAL_GIT.value
                )

                # 2. Traversal in companion_attachment.json raises PathSecurityError
                att_json.write_text(
                    json.dumps({"companion_dir": str(td_path / ".." / "escape")}),
                    encoding="utf-8",
                )
                with self.assertRaises(project_context.PathSecurityError):
                    project_context.resolve_project_context(target_repo=str(wt))

                # 3. Nesting companion inside target repo raises PathSecurityError
                att_json.write_text(
                    json.dumps({"companion_dir": str(target / "nested_comp")}),
                    encoding="utf-8",
                )
                with self.assertRaises(project_context.PathSecurityError):
                    project_context.resolve_project_context(target_repo=str(wt))

                # 4. Nesting target repo inside companion raises PathSecurityError
                att_json.write_text(
                    json.dumps({"companion_dir": str(td_path)}),
                    encoding="utf-8",
                )
                with self.assertRaises(project_context.PathSecurityError):
                    project_context.resolve_project_context(target_repo=str(wt))

                # 5. Remove attachment -> default fallback anchors to <primary>.aw (not <wt>.aw)
                att_json.unlink()
                ctx_default = project_context.resolve_project_context(
                    target_repo=str(wt)
                )
                expected_default = f"{target.resolve().as_posix()}.aw/records"
                self.assertEqual(
                    ctx_default.logical_roots[LogicalRoot.RECORDS.value],
                    expected_default,
                )
                self.assertNotIn("wt_att.aw", ctx_default.logical_roots["records"])

                # 6. user_cfg_data["repos"] matches primary_abs when repo_abs is absent
                user_cfg_path = Path(env["AW_CONFIG_DIR"]) / "config.json"
                user_cfg_path.parent.mkdir(parents=True, exist_ok=True)
                user_comp = td_path / "user_bound_comp"
                (user_comp / "records").mkdir(parents=True, exist_ok=True)
                user_cfg_path.write_text(
                    json.dumps(
                        {
                            "repos": {
                                target.resolve().as_posix(): {
                                    "companion_dir": user_comp.resolve().as_posix()
                                }
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                ctx_user = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(
                    ctx_user.logical_roots[LogicalRoot.RECORDS.value],
                    (user_comp / "records").resolve().as_posix(),
                )

    def test_cache_invalidation_on_attachment_and_companion_git_changes(self) -> None:
        """Cached context and project_records_dir invalidate immediately when companion
        attachment or companion .git state changes."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _install_companion_repo(
                td_path, commit_project_json=True
            )
            wt = _add_linked_worktree(target, td_path / "wt_cache", "feat/wt4", env)

            with _patched_env(env):
                ctx1 = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(ctx1.durability_state, DurabilityState.LOCAL_GIT.value)
                self.assertEqual(
                    project_context.project_records_dir(wt).resolve(),
                    (companion / "records").resolve(),
                )

                # Removing <companion>/.git immediately invalidates durability_state
                shutil.rmtree(companion / ".git")
                ctx2 = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(
                    ctx2.durability_state, DurabilityState.UNVERSIONED.value
                )

                # Re-initializing <companion>/.git restores local-git immediately
                init_repo(companion)
                ctx3 = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(ctx3.durability_state, DurabilityState.LOCAL_GIT.value)

                # Switching companion_dir via attachment (removing local.json) invalidates both caches
                local_json = target / ".aw" / "config" / "local.json"
                if local_json.exists():
                    local_json.unlink()
                companion2 = td_path / "companion_repo_v2"
                (companion2 / "records").mkdir(parents=True, exist_ok=True)
                storage.write_local_attachment_record(
                    target, companion2, ctx1.project_id, ["records"]
                )
                ctx4 = project_context.resolve_project_context(target_repo=str(wt))
                self.assertEqual(
                    ctx4.logical_roots[LogicalRoot.RECORDS.value],
                    (companion2 / "records").resolve().as_posix(),
                )
                self.assertEqual(
                    project_context.project_records_dir(wt).resolve(),
                    (companion2 / "records").resolve(),
                )

    def test_non_worktree_and_submodule_isolation(self) -> None:
        """Standalone nested repos and registered submodules do NOT inherit companion
        config via linked-worktree fallback."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, _companion, env = _install_companion_repo(
                td_path, commit_project_json=True
            )

            # Standalone nested Git repo inside target
            nested = target / "vendor" / "standalone_repo"
            init_repo(nested)

            # Registered submodule gitfile shape: gitdir under parent .git/modules/<name>, no commondir
            submod = target / "libs" / "submod"
            submod.mkdir(parents=True, exist_ok=True)
            mod_admin = target / ".git" / "modules" / "submod"
            mod_admin.mkdir(parents=True, exist_ok=True)
            (submod / ".git").write_text(
                f"gitdir: {mod_admin.resolve().as_posix()}\n", encoding="utf-8"
            )

            with _patched_env(env):
                self.assertIsNone(project_context._linked_worktree_primary(nested))
                self.assertIsNone(project_context._linked_worktree_primary(submod))
                self.assertEqual(
                    project_context.project_config_dir(nested).resolve(),
                    (nested / ".aw" / "config").resolve(),
                )
                self.assertEqual(
                    project_context.project_config_dir(submod).resolve(),
                    (submod / ".aw" / "config").resolve(),
                )
                ctx_sub = project_context.resolve_project_context(
                    target_repo=str(submod)
                )
                self.assertNotEqual(
                    ctx_sub.records_backend, RecordsBackend.COMPANION.value
                )


class TestCompanionDoctorDiagnostics(unittest.TestCase):
    """E-02/V-02: Companion doc-reference remapping, path-leak prevention, and stray-records warning."""

    def setUp(self) -> None:
        self.enterContext(support.execution_role(None))

    def test_fresh_companion_install_has_zero_dangling_doc_refs_and_no_abs_leak(
        self,
    ) -> None:
        """Fresh companion install yields zero doctor.dangling-doc-reference findings;
        a real dangling ref in a companion README normalizes location to .aw/records/...
        and rejects .. traversal outside records_root."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _install_companion_repo(
                td_path, commit_project_json=True
            )

            with _patched_env(env):
                doc_drifts = doctor.probe_installed_doc_references(target)
                self.assertEqual(
                    doc_drifts,
                    [],
                    f"Expected zero dangling doc references on fresh companion install, got: {doc_drifts}",
                )

                # Add a real dangling ref AND a .. traversal ref to a companion README
                comp_readme = companion / "records" / "plans" / "README.md"
                comp_readme.parent.mkdir(parents=True, exist_ok=True)
                orig = (
                    comp_readme.read_text(encoding="utf-8")
                    if comp_readme.is_file()
                    else "# Plans\n"
                )
                comp_readme.write_text(
                    orig
                    + "\nBroken ref: `.aw/records/plans/does-not-exist.md`\n"
                    + "Traversal ref: `.aw/records/../../app.py`\n",
                    encoding="utf-8",
                )
                drifts_after = doctor.probe_installed_doc_references(target)
                details = {d.detail: d for d in drifts_after}
                self.assertIn(".aw/records/plans/does-not-exist.md", details)
                self.assertIn(".aw/records/../../app.py", details)
                for d in drifts_after:
                    self.assertEqual(d.location, ".aw/records/plans/README.md")
                    self.assertNotIn(str(companion), d.location)
                    self.assertFalse(Path(d.location).is_absolute())

    def test_stray_target_records_warning_for_dir_file_and_symlinks(self) -> None:
        """Companion mode emits doctor.companion-stray-target-records (warning, command=None)
        for stray dir, file, live symlink, and broken symlink; non-companion never emits it."""
        self.assertEqual(
            check_engine.rule_spec("doctor.companion-stray-target-records").severity,
            "warning",
        )

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_lightweight_companion_repo(
                td_path, commit_project_json=True
            )
            stray = target / ".aw" / "records"
            if stray.is_symlink() or stray.is_file():
                stray.unlink()
            elif stray.is_dir():
                shutil.rmtree(stray)

            with _patched_env(env):
                # Clean companion repo has no stray warning
                clean_res = doctor.inspect_repo(target)
                clean_stray = [
                    d
                    for d in clean_res.diagnostics
                    if d.rule == "doctor.companion-stray-target-records"
                ]
                self.assertEqual(clean_stray, [])

                cases: list[tuple[str, object]] = [
                    ("dir", lambda: stray.mkdir(parents=True, exist_ok=True)),
                    ("file", lambda: stray.write_text("stray\n", encoding="utf-8")),
                    ("live_symlink", lambda: os.symlink(companion / "records", stray)),
                    (
                        "broken_symlink",
                        lambda: os.symlink(td_path / "missing_target", stray),
                    ),
                ]
                for label, creator in cases:
                    with self.subTest(stray_shape=label):
                        if stray.is_symlink() or stray.is_file():
                            stray.unlink()
                        elif stray.is_dir():
                            shutil.rmtree(stray)
                        creator()  # type: ignore[operator]

                        res = doctor.inspect_repo(target)
                        stray_diags = [
                            d
                            for d in res.diagnostics
                            if d.rule == "doctor.companion-stray-target-records"
                        ]
                        self.assertEqual(
                            len(stray_diags),
                            1,
                            f"Expected 1 stray warning for {label}, got: {res.diagnostics}",
                        )
                        diag = stray_diags[0]
                        self.assertEqual(diag.severity, "warning")
                        self.assertEqual(diag.location, ".aw/records")
                        self.assertIn(".aw/records", diag.detail)
                        self.assertIn("aw path records", diag.detail)
                        self.assertIsNotNone(diag.fix)
                        self.assertIn(".aw/records", diag.fix or "")
                        self.assertIn("aw path records", diag.fix or "")

                        rem = doctor.build_remediation(
                            artifact_core.Drift(
                                ".aw/records",
                                "doctor.companion-stray-target-records",
                                diag.detail,
                                severity="warning",
                            ),
                            target,
                        )
                        self.assertIsNone(rem.command)
                        self.assertIn(".aw/records", rem.summary_fix)
                        self.assertIn("aw path records", rem.summary_fix)
                        self.assertIn("aw path records", rem.detailed_fix)

            # Non-companion private-target repo NEVER emits doctor.companion-stray-target-records
            priv_target = td_path / "private_repo"
            init_repo(priv_target)
            (priv_target / "app.py").write_text("X = 1\n", encoding="utf-8")
            (priv_target / ".aw" / "config").mkdir(parents=True, exist_ok=True)
            (priv_target / ".aw" / "records").mkdir(parents=True, exist_ok=True)
            (priv_target / ".aw" / "config" / "project.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "preset": "private-target",
                        "delivery_mode": "tracked",
                        "records_backend": "repository",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            support.git(priv_target, "add", "app.py", ".aw/config/project.json")
            support.git(priv_target, "commit", "-m", "init private")
            self.assertTrue((priv_target / ".aw" / "records").is_dir())
            with _patched_env(env):
                priv_res = doctor.inspect_repo(priv_target)
                priv_stray = [
                    d
                    for d in priv_res.diagnostics
                    if d.rule == "doctor.companion-stray-target-records"
                ]
                self.assertEqual(priv_stray, [])


class TestCompanionCarriersAndEvidence(unittest.TestCase):
    """E-03/V-03: Companion carrier resolution, evidence containment, and stray-dir non-blindness."""

    def setUp(self) -> None:
        self.enterContext(support.execution_role(None))

    def test_carriers_evidence_finished_remedy_and_stray_dir_from_primary_and_worktree(
        self,
    ) -> None:
        """Exercises evaluate_durable_carrier, check_durable_carrier, resolve_evidence_artifact,
        and _iter_type_files identically from primary checkout and linked worktree."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_lightweight_companion_repo(
                td_path, commit_project_json=False
            )
            wt = _add_linked_worktree(target, td_path / "wt_check", "feat/wt5", env)

            comp_records = companion / "records"
            comp_plans = comp_records / "plans"
            comp_specs = comp_records / "specs"

            # 1. Valid sibling pending carrier plan (id6: sib111)
            _write_plan(
                comp_plans,
                "pending",
                id6="sib111",
                setid="compcheck",
                order=2,
                slug="sibling-carrier",
                status="pending",
            )
            # 2. Executed companion plan (id6: exe222)
            exec_plan = _write_plan(
                comp_plans,
                "executed",
                id6="exe222",
                setid="compcheck",
                order=1,
                slug="executed-work",
                status="executed",
            )
            exec_logical = f".aw/records/plans/executed/{exec_plan.name}"
            pending_logical = ".aw/records/plans/pending/20261121-compcheck-02-sib111-sibling-carrier.ipd.md"

            # 3. Companion specs: one implemented, one draft
            impl_spec = (
                comp_specs / "implemented" / "20261121-spc333-01-spc333-done.spec.md"
            )
            impl_spec.parent.mkdir(parents=True, exist_ok=True)
            impl_spec.write_text(
                "# Spec: Done\n\n- Id: spc333\n- Status: implemented\n",
                encoding="utf-8",
            )
            draft_spec = (
                comp_specs / "draft" / "20261121-spc444-01-spc444-draft.spec.md"
            )
            draft_spec.parent.mkdir(parents=True, exist_ok=True)
            draft_spec.write_text(
                "# Spec: Draft\n\n- Id: spc444\n- Status: draft\n",
                encoding="utf-8",
            )

            # 4. Outside file and symlink escape inside companion records
            outside_file = td_path / "outside.md"
            outside_file.write_text("# Outside\n", encoding="utf-8")
            symlink_escape = comp_plans / "executed" / "escape.ipd.md"
            os.symlink(outside_file, symlink_escape)

            # 5. Plans exercising each carrier / evidence case
            valid_carrier_plan = _write_plan(
                comp_plans,
                "pending",
                id6="okp555",
                setid="compcheck",
                order=3,
                slug="valid-carrier",
                status="to-review",
                deferred_block=(
                    "- Followup handled by sibling.\n"
                    "  - Carrier: sib111\n"
                    "- Already shipped work.\n"
                    f"  - Carrier-Evidence: {exec_logical}\n"
                    "- Already shipped spec.\n"
                    f"  - Carrier-Evidence: .aw/records/specs/implemented/{impl_spec.name}\n"
                ),
            )
            bad_carrier_plan = _write_plan(
                comp_plans,
                "pending",
                id6="bad666",
                setid="compcheck",
                order=4,
                slug="nonexistent-carrier",
                status="to-review",
                deferred_block="- Missing carrier.\n  - Carrier: zzzzzz\n",
            )
            unshipped_ev_plan = _write_plan(
                comp_plans,
                "pending",
                id6="unp777",
                setid="compcheck",
                order=5,
                slug="unshipped-evidence",
                status="to-review",
                deferred_block=(
                    "- Pending plan evidence.\n"
                    f"  - Carrier-Evidence: {pending_logical}\n"
                    "- Draft spec evidence.\n"
                    f"  - Carrier-Evidence: .aw/records/specs/draft/{draft_spec.name}\n"
                ),
            )
            traversal_ev_plan = _write_plan(
                comp_plans,
                "pending",
                id6="trv888",
                setid="compcheck",
                order=6,
                slug="traversal-evidence",
                status="to-review",
                deferred_block=(
                    "- Traversal evidence.\n"
                    "  - Carrier-Evidence: .aw/records/../../outside.md\n"
                    "- Symlink escape evidence.\n"
                    "  - Carrier-Evidence: .aw/records/plans/executed/escape.ipd.md\n"
                ),
            )
            finished_carrier_plan = _write_plan(
                comp_plans,
                "pending",
                id6="fin999",
                setid="compcheck",
                order=7,
                slug="finished-carrier",
                status="to-review",
                deferred_block="- Handed off to executed plan.\n  - Carrier: exe222\n",
            )

            # Create a stray <target>/.aw/records/plans/pending/stray.ipd.md (gitignored by /records/)
            stray_plan = (
                target
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261121-stray-01-str000-stray.ipd.md"
            )
            stray_plan.parent.mkdir(parents=True, exist_ok=True)
            stray_plan.write_text("# Stray\n", encoding="utf-8")

            with _patched_env(env):
                for label, root in (("primary", target), ("worktree", wt)):
                    with self.subTest(checkout=label):
                        # Stray <target>/.aw/records/ never blinds companion _iter_type_files,
                        # while built-in ignored dirs like <companion>/records/runs stay ignored.
                        self.assertFalse(
                            artifact_core.is_ignored_path(valid_carrier_plan, root)
                        )
                        self.assertTrue(
                            artifact_core.is_ignored_path(comp_records / "runs", root)
                        )
                        iter_plans = list(check_engine._iter_type_files(root, "plans"))
                        iter_resolved = {p.resolve() for p in iter_plans}
                        self.assertIn(valid_carrier_plan.resolve(), iter_resolved)
                        self.assertIn(bad_carrier_plan.resolve(), iter_resolved)
                        self.assertNotIn(stray_plan.resolve(), iter_resolved)

                        # Evidence resolver accepts shipped companion evidence and rejects traversal/symlink
                        self.assertTrue(
                            check_engine.resolve_evidence_artifact(root, exec_logical)
                        )
                        self.assertFalse(
                            check_engine._evidence_plan_unshipped(root, exec_logical)
                        )
                        self.assertTrue(
                            check_engine.resolve_evidence_artifact(
                                root, pending_logical
                            )
                        )
                        self.assertTrue(
                            check_engine._evidence_plan_unshipped(root, pending_logical)
                        )
                        self.assertFalse(
                            check_engine._evidence_spec_unshipped(
                                root, f".aw/records/specs/implemented/{impl_spec.name}"
                            )
                        )
                        self.assertTrue(
                            check_engine._evidence_spec_unshipped(
                                root, f".aw/records/specs/draft/{draft_spec.name}"
                            )
                        )
                        self.assertFalse(
                            check_engine.resolve_evidence_artifact(
                                root, ".aw/records/../../outside.md"
                            )
                        )
                        self.assertFalse(
                            check_engine.resolve_evidence_artifact(
                                root, ".aw/records/plans/executed/escape.ipd.md"
                            )
                        )

                        # Valid sibling carrier + shipped companion evidence -> 0 findings
                        drifts_valid = check_engine.evaluate_durable_carrier(
                            root,
                            plan_path=valid_carrier_plan,
                            plan_text=valid_carrier_plan.read_text(encoding="utf-8"),
                        )
                        self.assertEqual(drifts_valid, [])

                        # Nonexistent carrier -> fails at error severity via primary cutover
                        drifts_bad = check_engine.evaluate_durable_carrier(
                            root,
                            plan_path=bad_carrier_plan,
                            plan_text=bad_carrier_plan.read_text(encoding="utf-8"),
                        )
                        self.assertEqual(len(drifts_bad), 1)
                        self.assertEqual(
                            drifts_bad[0].rule, "check.ipd-uncarried-obligation"
                        )
                        self.assertEqual(drifts_bad[0].severity, "error")

                        # Unshipped pending plan / draft spec evidence -> fails at error severity
                        drifts_unshipped = check_engine.evaluate_durable_carrier(
                            root,
                            plan_path=unshipped_ev_plan,
                            plan_text=unshipped_ev_plan.read_text(encoding="utf-8"),
                        )
                        self.assertEqual(len(drifts_unshipped), 1)
                        self.assertEqual(
                            drifts_unshipped[0].rule, "check.ipd-uncarried-obligation"
                        )
                        self.assertEqual(drifts_unshipped[0].severity, "error")

                        # Traversal & symlink escape evidence -> fails at error severity
                        drifts_trav = check_engine.evaluate_durable_carrier(
                            root,
                            plan_path=traversal_ev_plan,
                            plan_text=traversal_ev_plan.read_text(encoding="utf-8"),
                        )
                        self.assertEqual(len(drifts_trav), 1)
                        self.assertEqual(
                            drifts_trav[0].rule, "check.ipd-uncarried-obligation"
                        )
                        self.assertEqual(drifts_trav[0].severity, "error")

                        # Finished companion carrier -> info finding with logical .aw/records/plans/executed/... remedy
                        drifts_fin = check_engine.evaluate_durable_carrier(
                            root,
                            plan_path=finished_carrier_plan,
                            plan_text=finished_carrier_plan.read_text(encoding="utf-8"),
                        )
                        self.assertEqual(len(drifts_fin), 1)
                        self.assertEqual(
                            drifts_fin[0].rule, "check.ipd-carrier-finished-unverified"
                        )
                        self.assertEqual(drifts_fin[0].severity, "info")
                        self.assertIn(exec_logical, drifts_fin[0].detail)
                        self.assertIn(exec_logical, drifts_fin[0].recovery)
                        self.assertNotIn(str(companion), drifts_fin[0].detail)

                        # Full check_durable_carrier sweep passes valid plan and catches bad/unshipped/traversal
                        sweep = check_engine.check_durable_carrier(root)
                        by_path = {}
                        for d in sweep:
                            by_path.setdefault(Path(d.location).resolve(), []).append(d)
                        self.assertNotIn(valid_carrier_plan.resolve(), by_path)
                        self.assertIn(bad_carrier_plan.resolve(), by_path)
                        self.assertIn(unshipped_ev_plan.resolve(), by_path)
                        self.assertIn(traversal_ev_plan.resolve(), by_path)
                        self.assertIn(finished_carrier_plan.resolve(), by_path)


if __name__ == "__main__":
    unittest.main()
