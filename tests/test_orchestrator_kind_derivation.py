#!/usr/bin/env python3
"""Behavioral tests for approved-orchestrator derivation and legacy manifest kind fallback.

Restores the behavioral coverage lost when tests/test_rununify_record.py was deleted in 19313eed
(backlog 8ww1zo / IPD 33wan5), asserting:
1. Approved orchestrator derives 'orchestrate' end-to-end on both hosts through
   discover_plans -> build_dynamic_manifest -> action_for.
2. Legacy hand-written manifest omitting 'kind' falls back to the plan file on both hosts via
   resolve_manifest_kind / plan_kind_from_file.
3. Real queue build (initialize_run with --manifest) on both hosts derives 'orchestrate'
   and 'kind == "orchestrator"' for a legacy manifest entry without 'kind'.
4. In-process non-vacuity control proving the queue-build derivation depends on the fallback.

All tests exercise observable outcomes and behaviors without source-reading pins.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
import subprocess
import tempfile
import unittest
import unittest.mock

from agent_workflows import agy_runipd, coverage_record, oc_runipd, runner_shared

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


def _write_synthetic_plan_file(
    pending_dir: pathlib.Path,
    id6: str,
    kind: str,
    order: int,
    status: str = "approved",
    setid: str = "recset",
) -> pathlib.Path:
    path = pending_dir / f"20261014-{setid}-{order:02d}-{id6}-synthetic.ipd.md"
    content = (
        f"# IPD: synthetic {id6}\n\n"
        f"- Date: 2026-10-14\n"
        f"- Kind: {kind}\n"
        f"- Id: {id6}\n"
        f"- Set: {setid}\n"
        f"- Order: {order}\n"
        f"- Status: {status}\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def _repo_with_synthetic_plans(
    tmp: str | pathlib.Path, setid: str = "recset"
) -> pathlib.Path:
    root = pathlib.Path(tmp)
    pending_dir = root / ".aw" / "records" / "plans" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    _write_synthetic_plan_file(
        pending_dir,
        id6="orcrec",
        kind="orchestrator",
        order=0,
        status="approved",
        setid=setid,
    )
    _write_synthetic_plan_file(
        pending_dir,
        id6="chirec",
        kind="child",
        order=1,
        status="approved",
        setid=setid,
    )
    return root


def _run_legacy_manifest_queue_build(
    host_module, test_case: unittest.TestCase | None = None
) -> dict:
    """Helper for E-03 and E-04: creates temp repo, legacy manifest, and runs initialize_run."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)

        d_pending = root / ".aw" / "records" / "plans" / "pending"
        d_pending.mkdir(parents=True, exist_ok=True)
        orc_path = d_pending / "20260906-qbuild-00-orcq01-synthetic.ipd.md"
        orc_path.write_text(
            "# IPD: synthetic\n\n"
            "- Date: 2026-09-06\n- Kind: orchestrator\n- Concern: synthetic.\n- Scope: synthetic.\n"
            "- Scope-Paths: none\n- Priority: medium\n- Work-Kind: chore\n- Status: approved\n"
            "- Set: qbuild\n- Order: 0\n- Highest E allocated: 01\n- Author: synthetic\n- Id: orcq01\n"
            "- Approval: 2026-09-06, synthetic\n- Readiness: go-pending-approval\n\n"
            "## Workflow history\n\n- 2026-09-06 approved (synthetic): created.\n"
            "- 2026-09-06 /plan-review (synthetic): APPROVE\n\n"
            "## Goal\n\nSynthetic goal.\n\n"
            "## Detailed Implementation Checklist (TODO)\n\n"
            "- [ ] E-01 CONFIRM chiq01 REACHED executed\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending\n\n"
            "## Child IPDs, sequence, and dependencies\n\n"
            "| Order | Id | Status | Plan | Depends on |\n|---|---|---|---|---|\n"
            "| 01 | chiq01 | executed | .aw/records/plans/executed/20260906-qbuild-01-chiq01-synthetic.ipd.md | none |\n\n"
            "## Completion criteria (the whole Set is done only when)\n\n- None.\n\n"
            "## Cross-IPD validation\n\n- None.\n\n"
            "## Deferred / out of scope (with reason)\n\n- None.\n\n"
            "## Scope check\n\n- None.\n\n"
            "## Required tests / validation\n\n- None.\n\n"
            "## Open questions\n\n- None.\n\n"
            "## Validation and cross-check (verify before reporting the Set complete)\n\n"
            "- [ ] V-01 validates E-01\n  - Required evidence: check.\n  - Observed evidence:\n  - Result: pending\n\n"
            "## Approval and execution gate\n\n- None.\n",
            encoding="utf-8",
        )
        d_exec = root / ".aw" / "records" / "plans" / "executed"
        d_exec.mkdir(parents=True, exist_ok=True)
        (d_exec / "20260906-qbuild-01-chiq01-synthetic.ipd.md").write_text(
            "# IPD: synthetic child\n\n"
            "- Date: 2026-09-06\n- Kind: child\n- Id: chiq01\n- Set: qbuild\n- Order: 1\n- Status: executed\n",
            encoding="utf-8",
        )
        coverage_record.write(orc_path, "pass", model="synthetic", tool="test")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "s"], cwd=root, check=True)

        manifest_file = root / "manifest.json"
        manifest_data = {
            "schema_version": runner_shared.SCHEMA_VERSION,
            "plans": {
                "orcq01": {
                    "set": "qbuild",
                    "file": str(orc_path.relative_to(root)),
                    "status": "approved",
                    "order": 0,
                    "dependencies": [],
                }
            },
            "sets": {"qbuild": {"order": ["orcq01"]}},
        }
        manifest_raw = json.dumps(manifest_data)
        manifest_check = json.loads(manifest_raw)
        if test_case is not None:
            test_case.assertNotIn(
                "kind",
                manifest_check["plans"]["orcq01"],
                "manifest fixture must omit the kind key",
            )
            test_case.assertEqual(
                manifest_check["schema_version"],
                runner_shared.SCHEMA_VERSION,
            )
        else:
            assert "kind" not in manifest_check["plans"]["orcq01"]
            assert manifest_check["schema_version"] == runner_shared.SCHEMA_VERSION

        manifest_file.write_text(manifest_raw, encoding="utf-8")

        args = argparse.Namespace(
            repo=str(root),
            selectors=["qbuild"],
            manifest=str(manifest_file),
            runbook=None,
            model=None,
            agent=None,
            variant=None,
            opencode="opencode",
            antigravity="antigravity",
            full_auto=False,
            action=None,
            isolate_worktree=True,
            validate=None,
            retry_budget=None,
            prepare_only=True,
            profile=None,
            output_mode=None,
            new_session=False,
            verify=False,
            timeout=None,
            stall_timeout=None,
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            run_dir = host_module.initialize_run(args)
        state = json.loads(
            (pathlib.Path(run_dir) / "state.json").read_text(encoding="utf-8")
        )
        return next(it for it in state["queue"] if it["id6"] == "orcq01")


class ApprovedOrchestratorDerivesOrchestrateEndToEnd(unittest.TestCase):
    """E-01: Approved orchestrator derives orchestrate end-to-end on both hosts."""

    def test_an_approved_orchestrator_derives_orchestrate_and_child_derives_execute_on_both_hosts(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with_synthetic_plans(tmp)
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    found = mod.discover_plans(root)
                    manifest = mod.build_dynamic_manifest(root, found)
                    orc_entry = manifest["plans"]["orcrec"]
                    chi_entry = manifest["plans"]["chirec"]
                    self.assertEqual(
                        mod.action_for(orc_entry["kind"], orc_entry["status"]),
                        "orchestrate",
                        f"{label} failed to derive orchestrate for approved orchestrator",
                    )
                    self.assertEqual(
                        mod.action_for(chi_entry["kind"], chi_entry["status"]),
                        "execute",
                        f"{label} failed to derive execute for approved child",
                    )

    def test_both_hosts_produce_equal_manifests_for_the_same_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with_synthetic_plans(tmp)
            oc_found = oc_runipd.discover_plans(root)
            agy_found = agy_runipd.discover_plans(root)
            self.assertEqual(oc_found, agy_found)
            self.assertEqual(
                oc_runipd.build_dynamic_manifest(root, oc_found),
                agy_runipd.build_dynamic_manifest(root, agy_found),
            )


class LegacyManifestKindFallback(unittest.TestCase):
    """E-02: Legacy hand-written manifest kind fallback on both hosts."""

    def _legacy_manifest(self, root: pathlib.Path, id6: str, rel: str) -> dict:
        manifest = {
            "schema_version": runner_shared.SCHEMA_VERSION,
            "plans": {
                id6: {
                    "set": "recset",
                    "file": rel,
                    "status": "approved",
                    "order": 0,
                    "dependencies": [],
                }
            },
            "sets": {"recset": {"order": [id6]}},
        }
        self.assertNotIn(
            "kind",
            manifest["plans"][id6],
            "this fixture is only meaningful if it OMITS the key",
        )
        return manifest

    def test_a_manifest_without_kind_still_derives_orchestrate_on_both_hosts(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with_synthetic_plans(tmp)
            plan_path = next(
                (root / ".aw" / "records" / "plans" / "pending").glob("*orcrec*.ipd.md")
            )
            rel = str(plan_path.relative_to(root))
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    manifest = self._legacy_manifest(root, "orcrec", rel)
                    entry = manifest["plans"]["orcrec"]
                    kind = mod.resolve_manifest_kind(entry, plan_path)
                    self.assertEqual(
                        mod.action_for(kind, entry["status"]),
                        "orchestrate",
                        f"{label} derived wrong ACTION for approved orchestrator in legacy manifest",
                    )
                    self.assertEqual(
                        kind,
                        "orchestrator",
                        f"{label} failed to resolve orchestrator kind from file",
                    )

    def test_a_manifest_with_kind_is_trusted_and_no_file_is_read(self):
        for label, mod in HOSTS:
            with self.subTest(host=label):
                entry = {"kind": "child", "status": "approved"}
                self.assertEqual(
                    mod.resolve_manifest_kind(
                        entry, pathlib.Path("/nonexistent/plan.ipd.md")
                    ),
                    "child",
                )

    def test_an_unreadable_plan_file_fails_to_the_safe_direction(self):
        missing = pathlib.Path("/nonexistent/definitely-not-here.ipd.md")
        for label, mod in HOSTS:
            with self.subTest(host=label):
                self.assertIsNone(mod.plan_kind_from_file(missing))
                self.assertIsNone(mod.resolve_manifest_kind({}, missing))
                self.assertEqual(
                    mod.action_for(mod.resolve_manifest_kind({}, missing), "approved"),
                    "execute",
                )

    def test_both_hosts_resolve_a_legacy_manifest_identically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with_synthetic_plans(tmp)
            pending = root / ".aw" / "records" / "plans" / "pending"
            for id6 in ("orcrec", "chirec"):
                plan_path = next(pending.glob(f"*{id6}*.ipd.md"))
                entry = {
                    "set": "recset",
                    "file": str(plan_path.relative_to(root)),
                }
                with self.subTest(plan=id6):
                    self.assertEqual(
                        oc_runipd.resolve_manifest_kind(entry, plan_path),
                        agy_runipd.resolve_manifest_kind(entry, plan_path),
                    )


class LegacyManifestQueueBuild(unittest.TestCase):
    """E-03: Real queue build with legacy manifest derives orchestrate on both hosts."""

    def test_legacy_manifest_queue_build_derives_orchestrate_on_both_hosts(
        self,
    ):
        for label, mod in HOSTS:
            with self.subTest(host=label):
                entry = _run_legacy_manifest_queue_build(mod, test_case=self)
                self.assertEqual(entry["action"], "orchestrate")
                self.assertEqual(entry["kind"], "orchestrator")


class LegacyManifestQueueBuildNonVacuityControl(unittest.TestCase):
    """E-04: Non-vacuity control proving E-03 queue derivation depends on fallback."""

    def test_queue_build_derivation_depends_on_fallback_on_both_hosts(self):
        with unittest.mock.patch.object(
            runner_shared,
            "resolve_manifest_kind",
            lambda entry, _p: entry.get("kind"),
        ):
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    entry = _run_legacy_manifest_queue_build(mod, test_case=self)
                    self.assertEqual(entry["action"], "execute")
                    self.assertIsNone(entry["kind"])


if __name__ == "__main__":
    unittest.main()
