"""Behavioral tests for ``tests.record_builder.RecordBuilder`` (IPD ``ijpay0``)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pytest

from agent_workflows import (
    artifact_meta as _meta,
)
from agent_workflows import (
    ipd_lint as _ipd_lint,
)
from agent_workflows import (
    research_contract as _research_contract,
)
from agent_workflows import (
    review_findings as _review_findings,
)
from tests import record_builder, repo_template, support
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core

_GOLDEN_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "record_builder"
    / "ready_plan_text_golden.json"
)


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


class RecordBuilderRoundTripTests(unittest.TestCase):
    """Test group (a): every built record type round-trips with equal fields."""

    def test_round_trip_ipd(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.plan(
                id6="p10001",
                kind="child",
                title="Round Trip Plan",
                author="alice",
                when="2026-08-24",
                set="rtset",
                order=2,
                status="approved",
                scope_paths="agent_workflows/demo.py, tests/test_demo.py",
                item_dependencies="executed:abc123",
                priority="high",
                work_kind="feature",
                approval="2026-08-24, human: approved",
                readiness="go-pending-approval",
                short_description="Plan round trip",
                from_backlog="bl0001",
                from_spec="sp0001",
                blocks_release="next",
            )
            self.assertTrue(Path(dest).is_file())
            st = _meta.read("p10001", project_context=_meta.legacy_context(repo))
            self.assertEqual(st.id6, "p10001")
            self.assertEqual(st.type, "ipd")
            self.assertEqual(st.status, "approved")
            self.assertEqual(st.set_id, "rtset")
            self.assertEqual(st.order_nn, 2)
            self.assertEqual(st.title, "IPD: Round Trip Plan")
            self.assertEqual(st.short_description, "Plan round trip")
            self.assertEqual(st.fields["plan_role"], "child")
            self.assertEqual(st.fields["author"], "alice")
            self.assertEqual(
                st.fields["scope_paths"],
                "agent_workflows/demo.py, tests/test_demo.py",
            )
            self.assertEqual(st.fields["item_dependencies"], "executed:abc123")
            self.assertEqual(st.fields["priority"], "high")
            self.assertEqual(st.fields["work_kind"], "feature")
            self.assertEqual(st.fields["approval"], "2026-08-24, human: approved")
            self.assertEqual(st.fields["readiness"], "go-pending-approval")
            self.assertEqual(st.fields["from_backlog"], "bl0001")
            self.assertEqual(st.fields["from_spec"], "sp0001")
            self.assertEqual(st.fields["blocks_release"], "next")

    def test_round_trip_spec(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.spec(
                id6="s10001",
                title="Round Trip Spec",
                author="bob",
                when="2026-08-24",
                set="rtset",
                order=3,
                status="to-review",
                short_description="Spec round trip",
                priority="high",
                work_kind="feature",
                from_backlog="bl0001",
                blocks_release="next",
            )
            self.assertTrue(Path(dest).is_file())
            st = _meta.read("s10001", project_context=_meta.legacy_context(repo))
            self.assertEqual(st.id6, "s10001")
            self.assertEqual(st.type, "spec")
            self.assertEqual(st.status, "to-review")
            self.assertEqual(st.set_id, "rtset")
            self.assertEqual(st.order_nn, 3)
            self.assertEqual(st.title, "Spec: Round Trip Spec")
            self.assertEqual(st.short_description, "Spec round trip")
            self.assertEqual(st.fields["author"], "bob")
            self.assertEqual(st.fields["priority"], "high")
            self.assertEqual(st.fields["work_kind"], "feature")
            self.assertEqual(st.fields["from_backlog"], "bl0001")
            self.assertEqual(st.fields["blocks_release"], "next")

    def test_round_trip_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.backlog(
                id6="b10001",
                summary="Backlog round trip summary",
                priority="high",
                work_kind="bug",
                status="blocked",
                when="2026-08-24",
                set="rtset",
                order=4,
                gate_kind="artifact",
                gate_ref="p10001",
                blocks_release="next",
                short_description="Backlog short desc",
            )
            self.assertTrue(Path(dest).is_file())
            st = _meta.read("b10001", project_context=_meta.legacy_context(repo))
            self.assertEqual(st.id6, "b10001")
            self.assertEqual(st.type, "backlog")
            self.assertEqual(st.status, "blocked")
            self.assertEqual(st.set_id, "rtset")
            self.assertEqual(st.order_nn, 4)
            self.assertEqual(st.short_description, "Backlog short desc")
            self.assertEqual(st.fields["summary"], "Backlog round trip summary")
            self.assertEqual(st.fields["priority"], "high")
            self.assertEqual(st.fields["work_kind"], "bug")
            self.assertEqual(st.fields["gate_kind"], "artifact")
            self.assertEqual(st.fields["gate_ref"], "p10001")
            self.assertEqual(st.fields["blocks_release"], "next")

    def test_round_trip_research(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.research(
                id6="q10001",
                topic="topic-alpha",
                research_kind="findings",
                status="active",
                outcome="adopted",
                when="2026-08-24",
                set="rtset",
                order=5,
                model="opus46high",
                summary="Research round trip summary",
                consumed_by=[],
                priority="medium",
                short_description="Research short desc",
            )
            dest_path = Path(dest)
            self.assertTrue(dest_path.is_file())
            parsed_name, name_err = _research_contract.parse_name(dest_path.name)
            self.assertIsNone(name_err)
            self.assertIsNotNone(parsed_name)
            fm = _research_contract.parse_frontmatter(
                dest_path.read_text(encoding="utf-8")
            )
            self.assertIsNotNone(fm)
            self.assertEqual(_research_contract.validate_frontmatter(fm), [])

            st = _meta.read("q10001", project_context=_meta.legacy_context(repo))
            self.assertEqual(st.id6, "q10001")
            self.assertEqual(st.type, "research")
            self.assertEqual(st.status, "active")
            self.assertEqual(st.set_id, "rtset")
            self.assertEqual(st.order_nn, 5)
            self.assertEqual(st.short_description, "Research short desc")
            self.assertEqual(st.fields["research_kind"], "findings")
            self.assertEqual(st.fields["outcome"], "adopted")
            self.assertEqual(st.fields["created"], "20260824")
            self.assertEqual(st.fields["model"], "opus46high")
            self.assertEqual(st.fields["summary"], "Research round trip summary")
            self.assertEqual(st.fields["consumed_by"], [])
            self.assertEqual(st.fields["priority"], "medium")
            self.assertEqual(st.fields["topic"], "[topic-alpha]")

    def test_round_trip_release(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.release(
                id6="l10001",
                version="2.3.4",
                status="blocked",
                summary="Release round trip summary",
                when="2026-08-24",
                set="rtset",
                order=6,
            )
            self.assertTrue(Path(dest).is_file())
            st = _meta.read("l10001", project_context=_meta.legacy_context(repo))
            self.assertEqual(st.id6, "l10001")
            self.assertEqual(st.type, "release")
            self.assertEqual(st.status, "blocked")
            self.assertEqual(st.set_id, "rtset")
            self.assertEqual(st.order_nn, 6)
            self.assertEqual(st.title, "Release: 2.3.4")
            self.assertEqual(st.short_description, "Release round trip summary")
            self.assertEqual(st.fields["version"], "2.3.4")

    def test_round_trip_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.prompt(
                id6="m10001",
                prompt_kind="research",
                status="executed",
                short_description="Prompt round trip",
                when="2026-08-24",
                set="rtset",
                order=7,
                author="carol",
                targets="agent_workflows/demo.py",
                concerns="round-trip",
                goal="verify prompt fields",
            )
            self.assertTrue(Path(dest).is_file())
            st = _meta.read("m10001", project_context=_meta.legacy_context(repo))
            self.assertEqual(st.id6, "m10001")
            self.assertEqual(st.type, "prompt")
            self.assertEqual(st.status, "executed")
            self.assertEqual(st.set_id, "rtset")
            self.assertEqual(st.order_nn, 7)
            self.assertEqual(st.short_description, "Prompt round trip")
            self.assertEqual(st.fields["author"], "carol")
            self.assertEqual(st.fields["targets"], "agent_workflows/demo.py")
            self.assertEqual(st.fields["concerns"], "round-trip")
            self.assertEqual(st.fields["goal"], "verify prompt fields")
            self.assertEqual(st.fields["prompt_kind"], "research")
            self.assertEqual(st.fields["created_day"], "2026-08-24")

    def test_round_trip_walkthrough(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.walkthrough(
                id6="w10001",
                target_id="p10001",
                when="2026-08-24",
                set="rtset",
                order=8,
            )
            self.assertTrue(Path(dest).is_file())
            st = _meta.read("w10001", project_context=_meta.legacy_context(repo))
            self.assertEqual(st.id6, "w10001")
            self.assertEqual(st.type, "walkthrough")
            self.assertIsNone(st.status)
            self.assertEqual(st.set_id, "rtset")
            self.assertEqual(st.order_nn, 8)
            self.assertEqual(st.fields["target_id"], "p10001")

    def test_round_trip_review(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            rounds = [
                {
                    "number": 1,
                    "findings": [
                        {
                            "id": "PR-001",
                            "severity": "low",
                            "scope": "tests",
                            "area": "builder",
                            "evidence": "observed",
                            "finding": "Sample finding",
                            "remediation_risk": "low",
                            "decision": "fixed",
                            "resolution": "Resolved in test",
                        }
                    ],
                    "decisions": [
                        {
                            "id": "D-01",
                            "question": "Check rounds?",
                            "chosen": "Yes",
                            "alternatives": "None",
                            "basis": "Test requirement",
                            "reversible": "yes",
                        }
                    ],
                }
            ]
            dest = rb.review(
                "p10001",
                rounds=rounds,
                subject_type="ipd",
                reviewed_at="2026-08-24",
                reviewer="opencode/test-model",
                verdict="APPROVE WITH REVISIONS APPLIED",
                set="rtset",
                order=9,
            )
            dest_path = Path(dest)
            self.assertTrue(dest_path.is_file())
            text = dest_path.read_text(encoding="utf-8")
            doc = _review_findings.parse_review_text(text)
            self.assertEqual(doc.subject_id, "p10001")
            self.assertEqual(doc.subject_type, "ipd")
            self.assertEqual(doc.reviewed_at, "2026-08-24")
            self.assertEqual(doc.reviewer, "opencode/test-model")
            self.assertEqual(doc.verdict, "APPROVE WITH REVISIONS APPLIED")
            self.assertEqual(len(doc.rounds), 1)
            self.assertEqual(doc.rounds[0].number, 1)
            self.assertEqual(len(doc.rounds[0].findings), 1)
            self.assertEqual(doc.rounds[0].findings[0].id, "PR-001")
            self.assertEqual(doc.rounds[0].findings[0].decision, "fixed")
            self.assertEqual(len(doc.rounds[0].decisions), 1)
            self.assertEqual(doc.rounds[0].decisions[0].id, "D-01")


class RecordBuilderLintAndRefusalTests(unittest.TestCase):
    """Test groups (b) lint and (f) refusals."""

    def test_lint_ready_plan_conforms(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            dest = rb.plan(
                id6="p20001",
                status="approved",
                approval="2026-08-24, human: approved",
                readiness="go-pending-approval",
            )
            res = _ipd_lint.lint_file(Path(dest), checkpoint="pre-execution")
            self.assertEqual(res.disposition, "conforming")
            self.assertTrue(res.passing)

            text_res = _ipd_lint.lint_text(
                support.ready_plan_text(), checkpoint="pre-execution"
            )
            self.assertEqual(text_res.disposition, "conforming")
            self.assertTrue(text_res.passing)

    def test_refuses_unknown_field(self) -> None:
        rb = RecordBuilder()
        with self.assertRaises(ValueError) as ctx:
            rb.plan(stauts="approved", text_only=True)
        self.assertIn("stauts", str(ctx.exception))

    def test_refuses_illegal_status(self) -> None:
        rb = RecordBuilder()
        with self.assertRaises(ValueError) as ctx:
            rb.plan(status="not-a-real-status", text_only=True)
        self.assertIn("not-a-real-status", str(ctx.exception))

    def test_refuses_long_short_description(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with self.assertRaises(ValueError) as ctx:
                rb.plan(id6="p20002", short_description="x" * 301)
            self.assertIn("300", str(ctx.exception))


class RecordBuilderGoldenTests(unittest.TestCase):
    """Test group (d): golden parity across all captured ready_plan_text calls."""

    def test_golden_ready_plan_text(self) -> None:
        cases = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))
        self.assertGreater(len(cases), 0)
        for idx, entry in enumerate(cases):
            got = support.ready_plan_text(**entry["args"])
            self.assertEqual(
                got,
                entry["text"],
                f"ready_plan_text mismatch at golden index {idx}: {entry['args']!r}",
            )


class RecordBuilderSwitchPointTests(unittest.TestCase):
    """Single-switch-point proof (IPD ``59aiyh`` E-11 / V-11)."""

    def test_switch_point_unknown_record_format_raises_for_every_method(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb_disk = RecordBuilder(repo)
            rb_text = RecordBuilder()

            raw_methods = (
                ("plan", (), {"id6": "sw0001"}),
                ("spec", (), {"id6": "sw0002"}),
                ("backlog", (), {"id6": "sw0003"}),
                ("research", (), {"id6": "sw0004"}),
                ("release", (), {"id6": "sw0005"}),
                ("prompt", (), {"id6": "sw0006"}),
                ("walkthrough", (), {"id6": "sw0007"}),
            )

            with mock.patch.object(record_builder, "RECORD_FORMAT", "unknown-format"):
                for method_name, args, kwargs in raw_methods:
                    with self.subTest(method=method_name, mode="disk"):
                        with self.assertRaises(ValueError) as ctx:
                            getattr(rb_disk, method_name)(*args, **kwargs)
                        self.assertIn("unknown-format", str(ctx.exception))

                    with self.subTest(method=method_name, mode="text_only"):
                        with self.assertRaises(ValueError) as ctx:
                            getattr(rb_text, method_name)(
                                *args, text_only=True, **kwargs
                            )
                        self.assertIn("unknown-format", str(ctx.exception))

                    with self.subTest(method=method_name, mode="disk_raw_fields"):
                        with self.assertRaises(ValueError) as ctx:
                            getattr(rb_disk, method_name)(
                                *args,
                                raw_fields={"Status": "EXECUTED"},
                                **kwargs,
                            )
                        self.assertIn("unknown-format", str(ctx.exception))

                    with self.subTest(method=method_name, mode="text_only_raw_fields"):
                        with self.assertRaises(ValueError) as ctx:
                            getattr(rb_text, method_name)(
                                *args,
                                raw_fields={"Status": "EXECUTED"},
                                text_only=True,
                                **kwargs,
                            )
                        self.assertIn("unknown-format", str(ctx.exception))

                with self.subTest(method="review", mode="disk"):
                    with self.assertRaises(ValueError) as ctx:
                        rb_disk.review("sw0001")
                    self.assertIn("unknown-format", str(ctx.exception))

                with self.subTest(method="review", mode="text_only"):
                    with self.assertRaises(ValueError) as ctx:
                        rb_text.review("sw0001", text_only=True)
                    self.assertIn("unknown-format", str(ctx.exception))
