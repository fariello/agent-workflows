"""Subprocess CLI visibility and parity tests for ``tests.record_builder.RecordBuilder`` (IPD ``ijpay0`` E-18, E-20, E-21)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import (
    artifact_meta as _meta,
)
from agent_workflows import (
    attention_contract as _attention_contract,
)
from tests import repo_template, support
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.slow


def _fresh_records_repo(base: Path) -> Path:
    """Create a minimal isolated git repository with ``.aw/records/`` directories."""
    repo = repo_template.copy_template_repo(base)
    for sub in (
        "plans/pending",
        "specs/draft",
        "backlog/open",
        "research",
        "releases",
        "prompts/pending",
        "walkthroughs",
        "reviews",
    ):
        (repo / ".aw" / "records" / sub).mkdir(parents=True, exist_ok=True)
    return repo


class RecordBuilderVisibilityTests(unittest.TestCase):
    """Test group (c): one fixture repo with all 8 types visible to find/attention/check."""

    def test_visibility_find_attention_check(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            rb.plan(id6="p10001", set="vis", order=1, status="draft")
            rb.spec(id6="s10001", set="vis", order=1, status="draft")
            rb.backlog(id6="b10001", set="vis", order=1, status="open")
            rb.research(id6="q10001", set="vis", order=1, status="reference")
            rb.release(id6="l10001", set="vis", order=1, status="planned")
            rb.prompt(id6="m10001", set="vis", order=1, status="pending")
            rb.walkthrough(id6="w10001", set="vis", order=1, target_id="p10001")
            rb.review("p10001", set="vis", order=1)

            res_find = support.run_cli("find", "-p", cwd=repo)
            self.assertEqual(res_find.returncode, 0, res_find.stderr)
            find_paths = [
                ln.strip() for ln in res_find.stdout.splitlines() if ln.strip()
            ]
            self.assertEqual(len(find_paths), 8, find_paths)

            res_attn = support.run_cli("attention", "--format", "json", cwd=repo)
            self.assertEqual(res_attn.returncode, 0, res_attn.stderr)
            attn_payload = json.loads(res_attn.stdout)
            self.assertTrue(attn_payload["valid"], attn_payload)
            self.assertEqual(attn_payload["violations"], [])
            attn_trees = {item["tree"] for item in attn_payload["items"]}
            expected_attn_trees = set(_attention_contract.TRACKED_TREES)
            self.assertEqual(attn_trees, expected_attn_trees)
            self.assertEqual(len(attn_payload["items"]), len(expected_attn_trees))

            res_check = support.run_cli(
                "check", "all", "--agent", "--verbose", cwd=repo
            )
            self.assertEqual(res_check.returncode, 0, res_check.stderr)
            check_payload = json.loads(res_check.stdout.strip().splitlines()[-1])
            self.assertEqual(check_payload["outcome"], "conforms", check_payload)
            self.assertEqual(check_payload["findings"], 0, check_payload)
            ev_map = {e["key"]: e["value"] for e in check_payload["evidence"]}
            inventory = ev_map["inventory"]
            eight_types = (
                "plans",
                "specs",
                "prompts",
                "research",
                "backlog",
                "walkthroughs",
                "releases",
                "reviews",
            )
            for key in eight_types:
                self.assertEqual(inventory[key], 1, inventory)
            eight_total = sum(inventory[k] for k in eight_types)
            print(
                f"visibility counts: aw_find={len(find_paths)} "
                f"aw_attention_tracked={len(attn_payload['items'])} "
                f"aw_check_inventory_eight={eight_total} ({inventory})"
            )


class RecordBuilderParityTests(unittest.TestCase):
    """Test group (e): builder output matches production creating commands via artifact_meta.read."""

    @staticmethod
    def _assert_state_equal(
        case: unittest.TestCase, cli_st: _meta.State, rb_st: _meta.State
    ) -> None:
        for attr in (
            "type",
            "status",
            "title",
            "short_description",
            "set_id",
            "order_nn",
            "disposition",
            "valid",
            "defect",
        ):
            case.assertEqual(
                getattr(rb_st, attr),
                getattr(cli_st, attr),
                f"mismatch on State.{attr}",
            )
        all_keys = sorted(set(cli_st.fields) | set(rb_st.fields))
        for key in all_keys:
            case.assertEqual(
                rb_st.fields.get(key),
                cli_st.fields.get(key),
                f"mismatch on State.fields[{key!r}]",
            )

    def _single_state(self, repo: Path, record_type: str) -> _meta.State:
        ctx = _meta.legacy_context(repo)
        rows = _meta.query(type=record_type, project_context=ctx).rows
        self.assertEqual(len(rows), 1, f"expected 1 {record_type} row, got {rows}")
        return _meta.read(rows[0].id6, project_context=ctx)

    def test_parity_plan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r_cli = _fresh_records_repo(Path(td) / "cli")
            r_rb = _fresh_records_repo(Path(td) / "rb")
            res = support.run_cli(
                "ipd",
                "scaffold",
                "--kind",
                "child",
                "--title",
                "Parity Plan",
                "--set",
                "demo",
                "--order",
                "1",
                "--author",
                "tester",
                "--priority",
                "medium",
                "--work-kind",
                "chore",
                "--summary",
                "Plan summary",
                "--apply",
                cwd=r_cli,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            cli_st = self._single_state(r_cli, "ipd")
            RecordBuilder(r_rb).plan(
                id6=cli_st.id6,
                kind="child",
                title="Parity Plan",
                set="demo",
                order=1,
                author="tester",
                priority="medium",
                work_kind="chore",
                scope_paths="TODO (comma-separated repo-relative paths or pathspecs)",
                item_dependencies="unresolved",
                short_description="Plan summary",
                status="draft",
            )
            rb_st = self._single_state(r_rb, "ipd")
            self._assert_state_equal(self, cli_st, rb_st)

    def test_parity_spec(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r_cli = _fresh_records_repo(Path(td) / "cli")
            r_rb = _fresh_records_repo(Path(td) / "rb")
            res = support.run_cli(
                "specs",
                "new",
                "--title",
                "Parity Spec",
                "--slug",
                "parity-spec",
                "--summary",
                "Spec summary",
                "--date",
                "2026-08-24",
                "--apply",
                cwd=r_cli,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            cli_st = self._single_state(r_cli, "spec")
            RecordBuilder(r_rb).spec(
                id6=cli_st.id6,
                title="Parity Spec",
                slug="parity-spec",
                short_description="Spec summary",
                when="2026-08-24",
                status="draft",
            )
            rb_st = self._single_state(r_rb, "spec")
            self._assert_state_equal(self, cli_st, rb_st)

    def test_parity_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r_cli = _fresh_records_repo(Path(td) / "cli")
            r_rb = _fresh_records_repo(Path(td) / "rb")
            res = support.run_cli(
                "backlog",
                "new",
                "--summary",
                "Parity Backlog",
                "--set",
                "demo",
                "--priority",
                "medium",
                "--work-kind",
                "chore",
                "--slug",
                "parity-backlog",
                "--apply",
                cwd=r_cli,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            cli_st = self._single_state(r_cli, "backlog")
            RecordBuilder(r_rb).backlog(
                id6=cli_st.id6,
                summary="Parity Backlog",
                short_description="Parity Backlog",
                set="demo",
                priority="medium",
                work_kind="chore",
                slug="parity-backlog",
                status="open",
            )
            rb_st = self._single_state(r_rb, "backlog")
            self._assert_state_equal(self, cli_st, rb_st)

    def test_parity_research(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r_cli = _fresh_records_repo(Path(td) / "cli")
            r_rb = _fresh_records_repo(Path(td) / "rb")
            res = support.run_cli(
                "research",
                "new",
                "--kind",
                "research-report",
                "--slug",
                "parity-research",
                "--summary",
                "Parity summary",
                "--set",
                "demo",
                "--topic",
                "testing",
                "--date",
                "20260824",
                "--order",
                "1",
                "--apply",
                cwd=r_cli,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            cli_st = self._single_state(r_cli, "research")
            RecordBuilder(r_rb).research(
                id6=cli_st.id6,
                research_kind="research-report",
                slug="parity-research",
                summary="Parity summary",
                short_description="Parity summary",
                set="demo",
                topic="testing",
                when="2026-08-24",
                order=1,
                status="todo",
                outcome="none-yet",
                body="",
            )
            rb_st = self._single_state(r_rb, "research")
            self._assert_state_equal(self, cli_st, rb_st)

    def test_parity_release(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r_cli = _fresh_records_repo(Path(td) / "cli")
            r_rb = _fresh_records_repo(Path(td) / "rb")
            res = support.run_cli(
                "releases",
                "new",
                "--version",
                "1.2.3",
                "--summary",
                "Parity release",
                "--status",
                "planned",
                "--apply",
                cwd=r_cli,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            cli_st = self._single_state(r_cli, "release")
            RecordBuilder(r_rb).release(
                id6=cli_st.id6,
                version="1.2.3",
                summary="Parity release",
                status="planned",
            )
            rb_st = self._single_state(r_rb, "release")
            self._assert_state_equal(self, cli_st, rb_st)

    def test_parity_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            r_cli = _fresh_records_repo(Path(td) / "cli")
            r_rb = _fresh_records_repo(Path(td) / "rb")
            res = support.run_cli(
                "prompts",
                "new",
                "--slug",
                "parity-prompt",
                "--set",
                "demo",
                "--kind",
                "run-once",
                "--status",
                "pending",
                "--summary",
                "Parity prompt",
                "--date",
                "2026-08-24",
                "--apply",
                cwd=r_cli,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            cli_st = self._single_state(r_cli, "prompt")
            RecordBuilder(r_rb).prompt(
                id6=cli_st.id6,
                slug="parity-prompt",
                set="demo",
                prompt_kind="run-once",
                status="pending",
                short_description="Parity prompt",
                when="2026-08-24",
                body="",
            )
            rb_st = self._single_state(r_rb, "prompt")
            self._assert_state_equal(self, cli_st, rb_st)
