"""Tests for typed queue entries, selector resolution, and dispatch seams (artdispatch 8l8dgb).

Covers:
- E-10: Selection and entry shape cases (1-6) on both hosts (oc and agy).
- E-11: Pre-queue seam cases (F-9 --action legality, F-10 mixed-type visibility).
- E-12: Queue-shape seam cases (F-11 birth status/exit code, F-12 conflict table, E-09 item-local refusal).
"""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    runner_shared,
)
from agent_workflows.runner_shared import DriverError, RunFlagRefusal
from agent_workflows.runner_stop import deliberate_stop_exit_code

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _make_test_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    return path


def _write_plan(
    repo: Path,
    *,
    id6: str,
    setid: str,
    order: int,
    status: str = "approved",
    kind: str | None = None,
    slug: str = "test",
    dependencies: list[str] | tuple[str, ...] | None = None,
) -> Path:
    bucket = "pending"
    if status in ("executed", "superseded", "not-executed", "reusable"):
        bucket = status
    dir_path = repo / ".aw" / "records" / "plans" / bucket
    dir_path.mkdir(parents=True, exist_ok=True)
    if kind == "orchestrator":
        order = 0
    file_path = dir_path / f"20260927-{setid}-{order:02d}-{id6}-{slug}.ipd.md"

    k = kind or "child"
    lines = [
        f"# IPD: Test {id6}",
        "",
        "- Date: 2026-09-27",
        f"- Id: {id6}",
        f"- Set: {setid}",
        f"- Order: {order}",
        f"- Status: {status}",
        f"- Kind: {k}",
        "- Concern: Test concern for typed queue entry tests.",
        "- Scope: Typed queue entry test scope.",
        "- Scope-Paths: none",
        "- Priority: medium",
        "- Work-Kind: feature",
        "- Author: test",
        "- Highest E allocated: 01",
    ]
    if status == "approved":
        lines.append("- Approval: 2026-09-27, test approved")
    if status in ("reviewed", "approved", "auto-approved"):
        lines.append("- Readiness: go-pending-approval")
    if dependencies:
        lines.append(f"- Item-Dependencies: {', '.join(dependencies)}")
    else:
        lines.append("- Item-Dependencies: none")
    lines.append("")
    lines.append("## Workflow history")
    lines.append("")
    lines.append(f"- 2026-09-27 {status} (test): created.")
    if status in ("reviewed", "approved", "auto-approved"):
        lines.append("- 2026-09-27 /plan-review (test): APPROVE")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append("A synthetic plan for typed queue entry tests.")
    lines.append("")
    lines.append("## Detailed Implementation Checklist (TODO)")
    lines.append("")
    if k == "orchestrator":
        lines.extend(
            [
                "- [ ] E-01 CONFIRM chld01 REACHED executed",
                "  - Depends on: none",
                "  - Expected outcome: done",
                "  - Execution state: pending",
                "",
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
                f"| 01 | chld01 | pending | .aw/records/plans/pending/20260927-{setid}-01-chld01-test.ipd.md | none |",
                "",
                "## Completion criteria (the whole Set is done only when)",
                "",
                "- None.",
                "",
                "## Cross-IPD validation",
                "",
                "- None.",
            ]
        )
    else:
        lines.extend(
            [
                "- [ ] E-01 Test item.",
                "  - Depends on: none",
                "  - Expected outcome: done",
                "  - Execution state: pending",
                "",
                "## Project conventions discovered (Step 0)",
                "",
                "- None.",
                "",
                "## Findings",
                "",
                "- None.",
                "",
                "## Proposed changes (ordered, validatable)",
                "",
                "- None.",
            ]
        )
    lines.extend(
        [
            "",
            "## Deferred / out of scope (with reason)",
            "",
            "- None.",
            "",
            "## Scope check",
            "",
            "- None.",
            "",
            "## Required tests / validation",
            "",
            "- None.",
        ]
    )
    if k != "orchestrator":
        lines.extend(
            [
                "",
                "## Spec / documentation sync",
                "",
                "- None.",
            ]
        )
    val_header = (
        "## Validation and cross-check (verify before reporting the Set complete)"
        if k == "orchestrator"
        else "## Validation and cross-check (verify before reporting done)"
    )
    lines.extend(
        [
            "",
            "## Open questions",
            "",
            "- None.",
            "",
            val_header,
            "",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: check.",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "",
            "- None.",
            "",
        ]
    )
    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def _write_spec(
    repo: Path,
    *,
    id6: str,
    status: str = "to-review",
    title: str = "Test Spec",
    slug: str = "test-spec",
) -> Path:
    specs_dir = repo / ".aw" / "records" / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    file_path = specs_dir / f"20260927-0001-01-{id6}-{slug}.spec.md"

    lines = [
        f"# Spec: {title}",
        "",
        "- Date: 2026-09-27",
        f"- Id: {id6}",
        f"- Status: {status}",
        "",
        "## Workflow history",
        "",
        f"- 2026-09-27 {status} (test): created.",
        "",
        "## Goal",
        "",
        "A synthetic spec for typed queue entry tests.",
        "",
    ]
    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def _write_backlog_item(
    repo: Path,
    *,
    id6: str,
    status: str = "open",
    setid: str = "test",
    title: str = "Test Backlog Item",
    slug: str = "test-item",
) -> Path:
    backlog_dir = repo / ".aw" / "records" / "backlog" / status
    backlog_dir.mkdir(parents=True, exist_ok=True)
    file_path = backlog_dir / f"20260927-{id6}-{slug}.backlog.md"

    sid = setid or "test"
    lines = [
        f"- Id: {id6}",
        f"- Set: {sid}",
        f"- Status: {status}",
        "- Work-Kind: feature",
        "- Priority: medium",
        f"- Summary: {title}",
        "",
        "## Workflow history",
        f"- 2026-09-27 created: {title}",
        "",
        "A synthetic backlog item for typed queue entry tests.",
        "",
    ]
    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


_run_counter = 0


def _build_queue_for_selector(
    module,
    repo: Path,
    *selectors: str,
    action: str | None = None,
    types: tuple[str, ...] | None = None,
    allow_mixed: bool = False,
    with_dependencies: bool = False,
) -> dict[str, Any]:
    global _run_counter
    _run_counter += 1
    cmd = [
        "start",
        *selectors,
        "--repo",
        str(repo),
        "--prepare-only",
        "--unattended",
        "--run-id",
        f"run-test-{_run_counter:06d}",
    ]
    if action:
        cmd.extend(["--action", action])
    if types:
        for t in types:
            cmd.extend(["--type", t])
    if allow_mixed:
        cmd.append("--allow-mixed")
    if with_dependencies:
        cmd.append("--with-dependencies")
    args = module.build_parser().parse_args(cmd)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        run_dir = module.initialize_run(args)
    state_file = Path(run_dir) / "state.json"
    data = json.loads(state_file.read_text(encoding="utf-8"))
    data["run_dir"] = str(run_dir)
    return data


class TestSelectionAndEntryShape(unittest.TestCase):
    """E-10: Selection and entry shape cases (1-6)."""

    def test_spec_5_9_both_hosts_both_shadowing_classes(self):
        """Case (1): spec and backlog id6s resolve to themselves, not plans, on both hosts.

        Tests both F-4 shadowing classes:
        - Exact setid: backlog faov03 vs plan in Set faov03.
        - Unique Set prefix: backlog 8t5ghs vs plan in Set 8t5ghsgi.
        - Plan filename substring: spec spc001 vs plan whose filename contains 'spc001'.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))

                    # Exact setid shadowing: backlog item faov03 and plan wja06w with Set faov03
                    _write_backlog_item(
                        repo, id6="faov03", status="open", title="Backlog faov03"
                    )
                    _write_plan(
                        repo,
                        id6="wja06w",
                        setid="faov03",
                        order=1,
                        slug="plan-in-faov03",
                    )

                    # Prefix shadowing: backlog item 8t5ghs and plan s2ufeo in Set 8t5ghsgi
                    _write_backlog_item(
                        repo, id6="8t5ghs", status="open", title="Backlog 8t5ghs"
                    )
                    _write_plan(
                        repo,
                        id6="s2ufeo",
                        setid="8t5ghsgi",
                        order=1,
                        slug="plan-in-prefix-set",
                    )

                    # Plan filename substring: spec spc001 and plan whose filename has spc001
                    _write_spec(
                        repo, id6="spc001", status="to-review", title="Spec spc001"
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="setone",
                        order=1,
                        slug="plan-for-spc001",
                    )

                    # 1. Exact setid class: faov03 selects backlog item faov03
                    data_faov = _build_queue_for_selector(mod, repo, "faov03")
                    q_faov = data_faov["queue"]
                    self.assertEqual(len(q_faov), 1)
                    self.assertEqual(q_faov[0]["id6"], "faov03")
                    self.assertEqual(q_faov[0]["artifact_type"], "backlog")
                    self.assertIn("records/backlog", q_faov[0]["configured_file"])
                    self.assertNotEqual(q_faov[0]["id6"], "wja06w")

                    # 2. Prefix class: 8t5ghs selects backlog item 8t5ghs
                    data_8t5 = _build_queue_for_selector(mod, repo, "8t5ghs")
                    q_8t5 = data_8t5["queue"]
                    self.assertEqual(len(q_8t5), 1)
                    self.assertEqual(q_8t5[0]["id6"], "8t5ghs")
                    self.assertEqual(q_8t5[0]["artifact_type"], "backlog")
                    self.assertIn("records/backlog", q_8t5[0]["configured_file"])
                    self.assertNotEqual(q_8t5[0]["id6"], "s2ufeo")

                    # 3. Filename substring: spc001 selects spec spc001
                    data_spc = _build_queue_for_selector(mod, repo, "spc001")
                    q_spc = data_spc["queue"]
                    self.assertEqual(len(q_spc), 1)
                    self.assertEqual(q_spc[0]["id6"], "spc001")
                    self.assertEqual(q_spc[0]["artifact_type"], "spec")
                    self.assertIn("records/specs", q_spc[0]["configured_file"])
                    self.assertNotEqual(q_spc[0]["id6"], "pln001")

    def test_accessor_returns_right_path_per_type_and_raises(self):
        """Case (2): queue_artifact_path returns right path per type and raises on missing/mismatch."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            p_plan = _write_plan(repo, id6="pln001", setid="s1", order=1)
            p_spec = _write_spec(repo, id6="spc001")
            p_bk = _write_backlog_item(repo, id6="bkl001")

            # Correct resolution
            item_plan = {
                "artifact_type": "ipd",
                "id6": "pln001",
                "configured_file": str(p_plan.relative_to(repo)),
            }
            self.assertEqual(
                runner_shared.queue_artifact_path(repo, item_plan).resolve(),
                p_plan.resolve(),
            )

            item_spec = {"artifact_type": "spec", "id6": "spc001"}
            self.assertEqual(
                runner_shared.queue_artifact_path(repo, item_spec).resolve(),
                p_spec.resolve(),
            )

            item_bk = {"artifact_type": "backlog", "id6": "bkl001"}
            self.assertEqual(
                runner_shared.queue_artifact_path(repo, item_bk).resolve(),
                p_bk.resolve(),
            )

            # Missing spec
            with self.assertRaises(runner_shared.DriverError) as ctx:
                runner_shared.queue_artifact_path(
                    repo, {"artifact_type": "spec", "id6": "nonex1"}
                )
            self.assertIn("nonex1", str(ctx.exception))

            # Missing backlog
            with self.assertRaises(runner_shared.DriverError) as ctx:
                runner_shared.queue_artifact_path(
                    repo, {"artifact_type": "backlog", "id6": "nonex2"}
                )
            self.assertIn("nonex2", str(ctx.exception))

    def test_entry_lacking_artifact_type_defaults_to_ipd(self):
        """Case (3): queue_entry_type defaults absent or empty artifact_type to 'ipd'."""
        self.assertEqual(runner_shared.queue_entry_type({}), "ipd")
        self.assertEqual(runner_shared.queue_entry_type({"artifact_type": None}), "ipd")
        self.assertEqual(runner_shared.queue_entry_type({"artifact_type": ""}), "ipd")
        self.assertEqual(runner_shared.queue_entry_type({"id6": "p1"}), "ipd")
        self.assertEqual(
            runner_shared.queue_entry_type({"artifact_type": "spec"}), "spec"
        )
        self.assertEqual(
            runner_shared.queue_entry_type({"artifact_type": "backlog"}), "backlog"
        )

    def test_ipd_only_run_queue_entries_and_manifest(self):
        """Case (4): an IPD-only run's queue has only artifact_type added, and manifest has no typed maps."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo, id6="pln001", setid="s1", order=1, status="approved"
                    )

                    data = _build_queue_for_selector(mod, repo, "pln001")
                    q = data["queue"]
                    self.assertEqual(len(q), 1)
                    entry = q[0]
                    self.assertEqual(entry["artifact_type"], "ipd")
                    self.assertEqual(entry["id6"], "pln001")

                    manifest_file = Path(data["run_dir"]) / "manifest.json"
                    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                    self.assertNotIn("specs", manifest)
                    self.assertNotIn("backlog", manifest)

    def test_sweep_selectors_type_scoping(self):
        """Case (5): all --type spec queues specs; all --type backlog admitted; reviews --type backlog refused."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc001", status="to-review")
                    _write_backlog_item(repo, id6="bkl001", status="open")
                    _write_plan(repo, id6="pln001", setid="s1", order=1)

                    # all --type spec queues specs only
                    data_spec = _build_queue_for_selector(
                        mod, repo, "all", types=("spec",)
                    )
                    q_spec = data_spec["queue"]
                    self.assertEqual([e["id6"] for e in q_spec], ["spc001"])
                    self.assertEqual(q_spec[0]["artifact_type"], "spec")

                    # all --type backlog is NOT refused by sweep gate
                    data_bk = _build_queue_for_selector(
                        mod, repo, "all", types=("backlog",)
                    )
                    q_bk = data_bk["queue"]
                    self.assertEqual([e["id6"] for e in q_bk], ["bkl001"])
                    self.assertEqual(q_bk[0]["artifact_type"], "backlog")

                    # reviews --type backlog is refused with reason
                    cmd = [
                        "start",
                        "reviews",
                        "--repo",
                        str(repo),
                        "--prepare-only",
                        "--type",
                        "backlog",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    with self.assertRaises(RunFlagRefusal) as ctx:
                        mod.initialize_run(args)
                    self.assertIn(
                        "needs-review sweep can enumerate only", str(ctx.exception)
                    )
                    self.assertIn("backlog", str(ctx.exception))

    def test_plan_only_helper_raises_for_non_ipd(self):
        """Case (6): queue_plan_path_for handed a spec or backlog entry raises DriverError naming the type."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            with self.assertRaises(runner_shared.DriverError) as ctx_spec:
                runner_shared.queue_plan_path_for(
                    repo, {"id6": "spc001", "artifact_type": "spec"}
                )
            self.assertIn("spc001 is a spec, not an IPD plan", str(ctx_spec.exception))

            with self.assertRaises(runner_shared.DriverError) as ctx_bk:
                runner_shared.queue_plan_path_for(
                    repo, {"id6": "bkl001", "artifact_type": "backlog"}
                )
            self.assertIn("bkl001 is a backlog, not an IPD plan", str(ctx_bk.exception))


class TestPreQueueSeams(unittest.TestCase):
    """E-11: Pre-queue seam cases (F-9 --action legality, F-10 mixed-type visibility)."""

    def test_action_legality_preflight_on_both_hosts(self):
        """F-9: --action review on to-review spec freezes action: review; --action execute refuses."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc001", status="to-review")

                    # --action review succeeds and freezes action: review
                    data = _build_queue_for_selector(
                        mod, repo, "spc001", action="review"
                    )
                    q = data["queue"]
                    self.assertEqual(len(q), 1)
                    self.assertEqual(q[0]["id6"], "spc001")
                    self.assertEqual(q[0]["action"], "review")

                    # --action execute refuses, naming its REAL status (to-review -> review)
                    cmd = [
                        "start",
                        "spc001",
                        "--repo",
                        str(repo),
                        "--prepare-only",
                        "--unattended",
                        "--action",
                        "execute",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    with self.assertRaises(runner_shared.DriverError) as ctx:
                        mod.initialize_run(args)
                    msg = str(ctx.exception)
                    self.assertIn("--action execute is illegal", msg)
                    self.assertIn("spc001", msg)
                    self.assertIn("status 'to-review' -> action 'review'", msg)
                    self.assertNotIn("status 'approved'", msg)

    def test_mixed_type_visibility(self):
        """F-10: spec named without --type contributes path and triggers [RUN-MIXED-TYPES] with plan."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            p_spec = _write_spec(repo, id6="spc001")
            _write_plan(repo, id6="pln001", setid="s1", order=1)

            manifest = runner_shared.build_dynamic_manifest(
                repo, runner_shared.discover_plans(repo)
            )
            runner_shared.populate_manifest_specs(manifest, repo)

            # Spec named with NO --type resolves to path in selection.all_paths
            selection = runner_shared.resolve_selected_artifact_paths(
                repo, manifest, ["spc001"], ("ipd",)
            )
            self.assertEqual(selection.unresolved, ())
            self.assertIn(p_spec.resolve(), [p.resolve() for p in selection.all_paths])

            # Selection of spec + plan without --allow-mixed raises [RUN-MIXED-TYPES]
            cmd = [
                "start",
                "spc001",
                "pln001",
                "--repo",
                str(repo),
                "--prepare-only",
                "--unattended",
            ]
            args = oc_runipd.build_parser().parse_args(cmd)
            with self.assertRaises(DriverError) as ctx:
                oc_runipd.initialize_run(args)
            self.assertIn("[RUN-MIXED-TYPES]", str(ctx.exception))

    def test_manifest_absent_queue_id_refuses_ahead_of_durable_state_on_both_hosts(
        self,
    ):
        """E-01: expanded selection containing manifest-absent id6 refuses with DriverError naming id6; no run dir."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo, id6="pln001", setid="s1", order=1, status="approved"
                    )

                    real_expand = mod.expand_selectors

                    def fake_expand(manifest, selectors, **kwargs):
                        res = real_expand(manifest, selectors, **kwargs)
                        return list(res) + ["gho001"]

                    cmd = [
                        "start",
                        "pln001",
                        "--repo",
                        str(repo),
                        "--prepare-only",
                        "--unattended",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    with patch.object(mod, "expand_selectors", side_effect=fake_expand):
                        with self.assertRaises(runner_shared.DriverError) as ctx:
                            mod.initialize_run(args)
                    self.assertIn("gho001", str(ctx.exception))
                    runs_root = runner_shared.state_root(repo)
                    created_runs = (
                        list(runs_root.iterdir()) if runs_root.exists() else []
                    )
                    self.assertEqual(created_runs, [])

    def test_manifest_file_outside_plans_trees_refuses_on_both_hosts(self):
        """E-03: IPD manifest file outside plans trees refuses ahead of durable state; skip action passes."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    p = _write_plan(
                        repo, id6="pln002", setid="s2", order=1, status="approved"
                    )
                    docs_dir = repo / "docs"
                    docs_dir.mkdir(parents=True, exist_ok=True)
                    outside_path = docs_dir / p.name
                    p.rename(outside_path)
                    rel_path = str(outside_path.relative_to(repo))

                    manifest = {
                        "schema_version": runner_shared.SCHEMA_VERSION,
                        "plans": {
                            "pln002": {
                                "file": rel_path,
                                "set": "s2",
                                "order": 1,
                                "status": "approved",
                                "dependencies": [],
                            }
                        },
                        "sets": {"s2": {"order": ["pln002"]}},
                    }
                    mf_path = repo / "manifest.json"
                    mf_path.write_text(json.dumps(manifest), encoding="utf-8")

                    cmd = [
                        "start",
                        "pln002",
                        "--repo",
                        str(repo),
                        "--manifest",
                        str(mf_path),
                        "--prepare-only",
                        "--unattended",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    with self.assertRaises(runner_shared.DriverError) as ctx:
                        mod.initialize_run(args)
                    msg = str(ctx.exception)
                    self.assertIn("pln002", msg)
                    self.assertIn(rel_path, msg)
                    self.assertIn("outside the plans trees", msg)
                    self.assertIn(
                        "No work started, and nothing durable was created", msg
                    )
                    runs_root = runner_shared.state_root(repo)
                    created_runs = (
                        list(runs_root.iterdir()) if runs_root.exists() else []
                    )
                    self.assertEqual(created_runs, [])

                # Negative case: same misfiled path with status 'executed' (action 'skip') must NOT refuse
                with tempfile.TemporaryDirectory() as td_neg:
                    repo_neg = _make_test_repo(Path(td_neg))
                    p_neg = _write_plan(
                        repo_neg, id6="pln002", setid="s2", order=1, status="executed"
                    )
                    docs_dir_neg = repo_neg / "docs"
                    docs_dir_neg.mkdir(parents=True, exist_ok=True)
                    outside_path_neg = docs_dir_neg / p_neg.name
                    p_neg.rename(outside_path_neg)
                    rel_path_neg = str(outside_path_neg.relative_to(repo_neg))

                    manifest_neg = {
                        "schema_version": runner_shared.SCHEMA_VERSION,
                        "plans": {
                            "pln002": {
                                "file": rel_path_neg,
                                "set": "s2",
                                "order": 1,
                                "status": "executed",
                                "dependencies": [],
                            }
                        },
                        "sets": {"s2": {"order": ["pln002"]}},
                    }
                    mf_path_neg = repo_neg / "manifest.json"
                    mf_path_neg.write_text(json.dumps(manifest_neg), encoding="utf-8")

                    cmd_neg = [
                        "start",
                        "pln002",
                        "--repo",
                        str(repo_neg),
                        "--manifest",
                        str(mf_path_neg),
                        "--prepare-only",
                        "--unattended",
                    ]
                    args_neg = mod.build_parser().parse_args(cmd_neg)
                    run_dir = mod.initialize_run(args_neg)
                    runs_root_neg = runner_shared.state_root(repo_neg)
                    created_runs_neg = (
                        list(runs_root_neg.iterdir()) if runs_root_neg.exists() else []
                    )
                    self.assertEqual(len(created_runs_neg), 1)
                    self.assertEqual(created_runs_neg[0], Path(run_dir))


class TestQueueShapeSeams(unittest.TestCase):
    """E-12: Queue-shape seam cases (F-11, F-12) plus item-local refusal (E-09)."""

    def test_birth_status_and_exit_code(self):
        """F-11: backlog open item born queued; plan success bar exits 0; refusal exits nonzero."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl001", status="open")

            data = _build_queue_for_selector(oc_runipd, repo, "bkl001")
            q = data["queue"]
            self.assertEqual(len(q), 1)
            # Born queued (not reviewed)
            self.assertEqual(q[0]["status"], "queued")
            self.assertEqual(q[0]["action"], "plan")

        # Exit code predicate:
        # (i) completed production turn (status 'reviewed', action 'plan') exits 0
        queue_success = [{"action": "plan", "status": "reviewed", "id6": "bkl001"}]
        proj_success = runner_shared.exit_code_statuses(queue_success)
        self.assertEqual(proj_success, [runner_shared.EXIT_SUCCESS_TOKEN])
        rc_success = deliberate_stop_exit_code(
            proj_success,
            success_states=frozenset({runner_shared.EXIT_SUCCESS_TOKEN}),
            stopped=False,
        )
        self.assertEqual(rc_success, 0)

        # (ii) item-local refusal (status 'failed-safely', action 'plan') exits nonzero
        queue_refusal = [{"action": "plan", "status": "failed-safely", "id6": "bkl001"}]
        proj_refusal = runner_shared.exit_code_statuses(queue_refusal)
        self.assertEqual(proj_refusal, ["failed-safely"])
        rc_refusal = deliberate_stop_exit_code(
            proj_refusal,
            success_states=frozenset({runner_shared.EXIT_SUCCESS_TOKEN}),
            stopped=False,
        )
        self.assertNotEqual(rc_refusal, 0)

        # (iii) substantially-complete execute item still exits nonzero
        queue_sub = [
            {"action": "execute", "status": "substantially-complete", "id6": "pln001"}
        ]
        proj_sub = runner_shared.exit_code_statuses(queue_sub)
        self.assertEqual(proj_sub, ["substantially-complete"])
        rc_sub = deliberate_stop_exit_code(
            proj_sub,
            success_states=frozenset({runner_shared.EXIT_SUCCESS_TOKEN}),
            stopped=False,
        )
        self.assertNotEqual(rc_sub, 0)

    def test_conflict_table_typed_entry(self):
        """F-12: conflicting typed entry in conflict table appears with real path and real status."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_spec(repo, id6="spc001", status="to-review")
            manifest = runner_shared.build_dynamic_manifest(
                repo, runner_shared.discover_plans(repo)
            )
            runner_shared.populate_manifest_specs(manifest, repo)

            out_buf = io.StringIO()
            with patch(
                "agent_workflows.attention.get_active_runs_map",
                return_value={"spc001": "running"},
            ):
                with self.assertRaises(runner_shared.DriverError) as ctx:
                    runner_shared.enforce_no_active_runner_conflict(
                        repo,
                        ["spc001"],
                        [],
                        manifest=manifest,
                        on_conflict="refuse",
                        stream=out_buf,
                    )
            table_output = str(ctx.exception)
            # Must show real type and real status, not empty path or fabricated to-review
            self.assertIn("spc001", table_output)
            self.assertIn("spec", table_output)
            self.assertIn("to-revie", table_output)

    def test_item_local_refusal_on_both_hosts(self):
        """E-09: queued undispatchable entry run through run_queue ends refused; plan executes."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkg001", status="open")
                    _write_plan(
                        repo, id6="pln001", setid="s1", order=1, status="approved"
                    )

                    # Initialize run with both backlog item and plan, using --allow-mixed
                    data = _build_queue_for_selector(
                        mod, repo, "bkg001", "pln001", allow_mixed=True
                    )
                    run_dir = Path(data["run_dir"])
                    state_file = run_dir / "state.json"

                    # Mutate bkg001 in state to simulate an undispatchable action (e.g. 'review')
                    st = json.loads(state_file.read_text(encoding="utf-8"))
                    for it in st["queue"]:
                        if it["id6"] == "bkg001":
                            it["action"] = "review"
                    state_file.write_text(json.dumps(st), encoding="utf-8")

                    # Mock host spawn function to fail if called for undispatchable entry, succeed for plan
                    def mock_spawn(rd, st, runnable, **kwargs):
                        if runnable["id6"] == "bkg001":
                            raise AssertionError(
                                "Host spawn must NEVER be called for undispatchable entry!"
                            )
                        runnable["status"] = "executed"
                        # The real execute_item PERSISTS its outcome, and run_queue reloads state
                        # from disk each iteration; a fake that only mutates memory leaves the item
                        # `queued` on disk and the loop re-dispatches it forever.
                        mod.save_state(rd, st)

                    spawn_target = (
                        "agent_workflows.oc_runipd.execute_item"
                        if mod is oc_runipd
                        else "agent_workflows.agy_runipd.execute_item"
                    )

                    with patch(spawn_target, side_effect=mock_spawn):
                        mod.run_queue(run_dir, False)

                    # Reload state and verify
                    final_state = json.loads(state_file.read_text(encoding="utf-8"))
                    items_by_id = {item["id6"]: item for item in final_state["queue"]}

                    # Backlog entry was refused ahead of execute_item for undispatchable action 'review'
                    bkg_item = items_by_id["bkg001"]
                    self.assertEqual(bkg_item["status"], "failed-safely")
                    refusal = bkg_item.get("refusal") or {}
                    self.assertIn(
                        "missing-dispatcher-backlog-review",
                        refusal.get("reason", "") + refusal.get("code", ""),
                    )

                    # Independent plan was executed
                    plan_item = items_by_id["pln001"]
                    self.assertEqual(plan_item["status"], "executed")


class TestNonPlanDependencyClosureDefects(unittest.TestCase):
    """E-01: Pin non-plan dependency closure defects on both hosts."""

    def test_case_a_satisfied_spec_edge_bare_and_with_dependencies(self):
        """Case (a): plan with exists:spec:<id6> on existing spec freezes bare and with --with-dependencies."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc001", status="to-review")
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["exists:spec:spc001"],
                    )
                    # Bare invocation freezes successfully
                    bare_data = _build_queue_for_selector(mod, repo, "pln001")
                    self.assertEqual(len(bare_data["queue"]), 1)
                    self.assertEqual(bare_data["queue"][0]["id6"], "pln001")

                    # With --with-dependencies invocation must also freeze successfully
                    with_deps_data = _build_queue_for_selector(
                        mod, repo, "pln001", with_dependencies=True
                    )
                    self.assertEqual(len(with_deps_data["queue"]), 1)
                    self.assertEqual(with_deps_data["queue"][0]["id6"], "pln001")

    def test_case_b_backlog_target_with_dependencies_allow_mixed(self):
        """Case (b): plan with state:backlog:graduated:<id6> against open backlog item."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkg001", status="open")
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["state:backlog:graduated:bkg001"],
                    )
                    data = _build_queue_for_selector(
                        mod,
                        repo,
                        "pln001",
                        with_dependencies=True,
                        allow_mixed=True,
                    )
                    queue_ids = [entry["id6"] for entry in data["queue"]]
                    self.assertIn("pln001", queue_ids)
                    self.assertIn("bkg001", queue_ids)


class TestRestoredClosureBehavioralCoverage(unittest.TestCase):
    """E-05: Restored behavioral coverage for --with-dependencies closure."""

    def test_flag_absent_changes_nothing(self):
        """1. The flag absent changes nothing (identity function on queue)."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo,
                        id6="pln002",
                        setid="s2",
                        order=1,
                        status="executed",
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln002"],
                    )
                    # Bare run without --with-dependencies leaves pln002 out
                    data = _build_queue_for_selector(mod, repo, "pln001")
                    self.assertEqual(
                        [entry["id6"] for entry in data["queue"]], ["pln001"]
                    )

    def test_transitive_plan_closure_still_enqueues(self):
        """2. A transitive plan-only closure still enqueues all targets."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo, id6="pln003", setid="s3", order=1, status="approved"
                    )
                    _write_plan(
                        repo,
                        id6="pln002",
                        setid="s2",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln003"],
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln002"],
                    )
                    data = _build_queue_for_selector(
                        mod, repo, "pln001", with_dependencies=True
                    )
                    queue_ids = [entry["id6"] for entry in data["queue"]]
                    self.assertEqual(sorted(queue_ids), ["pln001", "pln002", "pln003"])

    def test_cycle_and_diamond_terminate_and_enqueue_once(self):
        """3. A cycle and a diamond each terminate and enqueue every target once."""
        # Diamond shape
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label, shape="diamond"):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo, id6="pln004", setid="s4", order=1, status="approved"
                    )
                    _write_plan(
                        repo,
                        id6="pln002",
                        setid="s2",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln004"],
                    )
                    _write_plan(
                        repo,
                        id6="pln003",
                        setid="s3",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln004"],
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln002", "executed:pln003"],
                    )
                    data = _build_queue_for_selector(
                        mod, repo, "pln001", with_dependencies=True
                    )
                    queue_ids = [entry["id6"] for entry in data["queue"]]
                    self.assertEqual(
                        sorted(queue_ids), ["pln001", "pln002", "pln003", "pln004"]
                    )
                    self.assertEqual(queue_ids.count("pln004"), 1)

        # Cycle shape: must terminate and raise cycle refusal at preflight, not hang
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label, shape="cycle"):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo,
                        id6="pln002",
                        setid="s2",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln001"],
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln002"],
                    )
                    with self.assertRaises(runner_shared.DriverError) as ctx:
                        _build_queue_for_selector(
                            mod, repo, "pln001", with_dependencies=True
                        )
                    self.assertIn("cycle", str(ctx.exception).lower())

    def test_terminal_disposition_target_is_skipped(self):
        """4. A terminal-disposition target is skipped and not enqueued."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo,
                        id6="pln002",
                        setid="s2",
                        order=1,
                        status="executed",
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["executed:pln002"],
                    )
                    data = _build_queue_for_selector(
                        mod, repo, "pln001", with_dependencies=True
                    )
                    queue_ids = [entry["id6"] for entry in data["queue"]]
                    self.assertEqual(queue_ids, ["pln001"])
                    self.assertNotIn("pln002", queue_ids)

    def test_unresolvable_plan_target_refuses_and_leaves_no_run_directory(self):
        """5. An unresolvable plan target refuses and leaves NO run directory."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["executed:zzz999"],
                    )
                    with self.assertRaises(runner_shared.ClosureRefusal) as ctx:
                        _build_queue_for_selector(
                            mod, repo, "pln001", with_dependencies=True
                        )
                    self.assertIn("zzz999", str(ctx.exception))
                    # Proof that runs root contains NO run directory
                    runs_root = repo / ".aw" / "records" / "runs"
                    run_dirs = (
                        list(runs_root.glob("run-*")) if runs_root.exists() else []
                    )
                    self.assertEqual(run_dirs, [])


class TestNewOrderingAndRefusalCases(unittest.TestCase):
    """E-06: New ordering and refusal cases on both hosts."""

    def test_unsatisfiable_non_plan_status_refuses_with_named_statuses_and_no_run_dir(
        self,
    ):
        """Unsatisfiable non-plan target (state:spec:approved on to-review spec) refuses naming both statuses."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc001", status="to-review")
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["state:spec:approved:spc001"],
                    )
                    with self.assertRaises(runner_shared.ClosureRefusal) as ctx:
                        _build_queue_for_selector(
                            mod,
                            repo,
                            "pln001",
                            with_dependencies=True,
                            allow_mixed=True,
                        )
                    err_msg = str(ctx.exception)
                    # Names current status and demanded status
                    self.assertIn("to-review", err_msg)
                    self.assertIn("approved", err_msg)
                    # Proof that runs root contains NO run directory
                    runs_root = repo / ".aw" / "records" / "runs"
                    run_dirs = (
                        list(runs_root.glob("run-*")) if runs_root.exists() else []
                    )
                    self.assertEqual(run_dirs, [])

    def test_e04_ordering_and_control_edge(self):
        """E-04 ordering property: in-queue non-plan prerequisite dispatches ahead of dependent."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkg001", status="open")
                    _write_plan(
                        repo,
                        id6="pln001",
                        setid="s1",
                        order=1,
                        status="approved",
                        dependencies=["state:backlog:graduated:bkg001"],
                    )
                    # Dependent requested FIRST so position alone would invert it
                    data = _build_queue_for_selector(
                        mod, repo, "pln001", with_dependencies=True, allow_mixed=True
                    )
                    queue = data["queue"]
                    self.assertEqual([e["id6"] for e in queue], ["pln001", "bkg001"])
                    self.assertEqual(queue[0]["position"], 1)
                    self.assertEqual(queue[1]["position"], 2)

                    by_id = {item["id6"]: item for item in queue}
                    depth_pln = runner_shared.dependency_depth("pln001", by_id)
                    depth_bkg = runner_shared.dependency_depth("bkg001", by_id)
                    self.assertEqual(depth_pln, 1)
                    self.assertEqual(depth_bkg, 0)

                    # simulate_dispatch_order puts target first
                    order = runner_shared.simulate_dispatch_order(queue)
                    self.assertEqual(order, ["bkg001", "pln001"])

                    # IPD control: verify canonical token spelling and ordering
                    parsed_tok = runner_shared.parse_dependency_token("executed:pln012")
                    self.assertIsNotNone(parsed_tok)
                    self.assertEqual(parsed_tok.canonical(), "executed:pln012")

                    _write_plan(
                        repo, id6="pln012", setid="s2", order=1, status="approved"
                    )
                    _write_plan(
                        repo,
                        id6="pln011",
                        setid="s2",
                        order=2,
                        status="approved",
                        dependencies=["executed:pln012"],
                    )
                    data_ipd = _build_queue_for_selector(
                        mod, repo, "pln011", with_dependencies=True
                    )
                    queue_ipd = data_ipd["queue"]
                    by_id_ipd = {item["id6"]: item for item in queue_ipd}
                    depth_pln11 = runner_shared.dependency_depth("pln011", by_id_ipd)
                    depth_pln12 = runner_shared.dependency_depth("pln012", by_id_ipd)
                    self.assertEqual(depth_pln11, 1)
                    self.assertEqual(depth_pln12, 0)
                    order_ipd = runner_shared.simulate_dispatch_order(queue_ipd)
                    self.assertEqual(order_ipd, ["pln012", "pln011"])
