"""Behavioral tests for ``tests.record_builder.assert_field`` and ``assert_no_field`` (IPD ``j5fqax``)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pytest

from tests import record_builder, repo_template
from tests.record_builder import RecordBuilder, assert_field, assert_no_field

pytestmark = pytest.mark.core


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


class AssertFieldByRecordTypeTests(unittest.TestCase):
    """Pass and fail cases for ``assert_field`` and ``assert_no_field`` across every record type."""

    def _check_present_and_absent(
        self,
        *,
        present_path: Path,
        absent_path: Path,
        field: str,
        expected: object,
        wrong: object,
    ) -> None:
        # Passes on Path and str for the matching record.
        assert_field(present_path, field, expected)
        assert_field(str(present_path), field, expected)

        # Fails when the expected value differs, naming field, expected, and observed.
        with self.assertRaises(AssertionError) as wrong_ctx:
            assert_field(present_path, field, wrong)
        wrong_msg = str(wrong_ctx.exception)
        self.assertIn(field, wrong_msg)
        self.assertIn(str(wrong), wrong_msg)
        self.assertIn(str(expected), wrong_msg)

        # assert_no_field fails on the record carrying the field, naming field and observed.
        with self.assertRaises(AssertionError) as present_ctx:
            assert_no_field(present_path, field)
        present_msg = str(present_ctx.exception)
        self.assertIn(field, present_msg)
        self.assertIn("absent", present_msg)
        self.assertIn(str(expected), present_msg)

        # assert_no_field passes on Path and str when the field is absent.
        assert_no_field(absent_path, field)
        assert_no_field(str(absent_path), field)

        # assert_field fails on the absent record, naming field, expected, and observed (None).
        with self.assertRaises(AssertionError) as absent_ctx:
            assert_field(absent_path, field, expected)
        absent_msg = str(absent_ctx.exception)
        self.assertIn(field, absent_msg)
        self.assertIn(str(expected), absent_msg)
        self.assertIn("None", absent_msg)

    def test_ipd_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(
                rb.plan(id6="p10001", status="approved", blocks_release="next")
            )
            without_field = Path(rb.plan(id6="p10002", status="draft"))
            assert_field(with_field, "status", "approved")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="blocks_release",
                expected="next",
                wrong="rl9999",
            )

    def test_spec_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(
                rb.spec(id6="s10001", status="to-review", blocks_release="next")
            )
            without_field = Path(rb.spec(id6="s10002", status="draft"))
            assert_field(with_field, "status", "to-review")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="blocks_release",
                expected="next",
                wrong="rl9999",
            )

    def test_backlog_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(
                rb.backlog(
                    id6="b10001",
                    status="open",
                    priority="high",
                    work_kind="bug",
                    blocks_release="next",
                )
            )
            without_field = Path(
                rb.backlog(
                    id6="b10002",
                    status="open",
                    priority="low",
                    work_kind="chore",
                )
            )
            assert_field(with_field, "status", "open")
            assert_field(with_field, "work_kind", "bug")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="blocks_release",
                expected="next",
                wrong="rl9999",
            )

    def test_research_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(
                rb.research(id6="q10001", status="active", priority="high")
            )
            without_field = Path(rb.research(id6="q10002", status="reference"))
            assert_field(with_field, "status", "active")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="priority",
                expected="high",
                wrong="low",
            )

    def test_release_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(
                rb.release(
                    id6="l10001",
                    version="2.0.0",
                    status="planned",
                    summary="Planned release",
                )
            )
            without_field = Path(
                rb.release(
                    id6="l10002",
                    version="2.1.0",
                    status="planned",
                    summary="",
                )
            )
            assert_field(with_field, "version", "2.0.0")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="short_description",
                expected="Planned release",
                wrong="Other summary",
            )

    def test_prompt_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(
                rb.prompt(
                    id6="m10001",
                    prompt_kind="research",
                    status="pending",
                    author="alice",
                )
            )
            without_field = Path(
                rb.prompt(
                    id6="m10002",
                    prompt_kind="run-once",
                    status="pending",
                )
            )
            assert_field(with_field, "status", "pending")
            assert_field(with_field, "prompt_kind", "research")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="author",
                expected="alice",
                wrong="bob",
            )

    def test_walkthrough_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(
                rb.walkthrough(
                    id6="w10001",
                    target_id="p10001",
                    raw_fields={"Short-Description": "Walkthrough note"},
                )
            )
            without_field = Path(rb.walkthrough(id6="w10002", target_id="p10002"))
            assert_field(with_field, "target_id", "p10001")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="short_description",
                expected="Walkthrough note",
                wrong="Different note",
            )

    def test_review_with_and_without_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            with_field = Path(rb.review("p10001", verdict="APPROVE"))
            without_field = Path(rb.review("p10002", verdict="APPROVE"))
            # Remove - Verdict: line from without_field to verify absent-field behavior.
            stripped = "\n".join(
                ln
                for ln in without_field.read_text(encoding="utf-8").splitlines()
                if not ln.startswith("- Verdict:")
            )
            without_field.write_text(stripped + "\n", encoding="utf-8")
            assert_field(with_field, "subject_id", "p10001")
            self._check_present_and_absent(
                present_path=with_field,
                absent_path=without_field,
                field="verdict",
                expected="APPROVE",
                wrong="REJECT",
            )


class AssertFieldStrictnessAndEdgeCaseTests(unittest.TestCase):
    """Loose-spelling rejection, duplicate rejection, path inference, and refusal guards."""

    def test_loose_bullet_double_space_after_dash_fails_assert_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            path = Path(rb.plan(id6="p20001", status="approved"))
            loose_text = path.read_text(encoding="utf-8").replace(
                "- Status: approved", "-  Status: approved", 1
            )
            path.write_text(loose_text, encoding="utf-8")

            with self.assertRaises(AssertionError) as ctx:
                assert_field(path, "status", "approved")
            msg = str(ctx.exception)
            self.assertIn("status", msg)
            self.assertIn("approved", msg)
            self.assertIn("-  Status: approved", msg)

    def test_loose_bullet_double_space_after_colon_fails_exact_line_half(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            path = Path(rb.backlog(id6="b20001", status="done"))
            loose_text = path.read_text(encoding="utf-8").replace(
                "- Status: done", "- Status:  done", 1
            )
            path.write_text(loose_text, encoding="utf-8")

            with self.assertRaises(AssertionError) as ctx:
                assert_field(path, "status", "done")
            msg = str(ctx.exception)
            self.assertIn("status", msg)
            self.assertIn("- Status: done", msg)
            self.assertIn("- Status:  done", msg)

    def test_loose_bullet_fails_assert_no_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            path = Path(rb.backlog(id6="b20002", status="open", blocks_release="next"))
            loose_text = path.read_text(encoding="utf-8").replace(
                "- Blocks-Release: next", "-  Blocks-Release: next", 1
            )
            path.write_text(loose_text, encoding="utf-8")

            with self.assertRaises(AssertionError) as ctx:
                assert_no_field(path, "blocks_release")
            msg = str(ctx.exception)
            self.assertIn("blocks_release", msg)
            self.assertIn("-  Blocks-Release: next", msg)

    def test_duplicate_bullet_fails_assert_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            path = Path(rb.backlog(id6="b20003", status="open", graduated_to="bar"))
            dup_text = path.read_text(encoding="utf-8").replace(
                "- Graduated-To: bar",
                "- Graduated-To: bar\n- Graduated-To: foo",
                1,
            )
            path.write_text(dup_text, encoding="utf-8")

            with self.assertRaises(AssertionError) as ctx:
                assert_field(path, "graduated_to", "bar")
            msg = str(ctx.exception)
            self.assertIn("graduated_to", msg)
            self.assertIn("- Graduated-To: foo", msg)

    def test_legacy_agents_backlog_md_filename_infers_backlog_type(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            legacy_dir = Path(td) / ".agents" / "backlog" / "open"
            legacy_dir.mkdir(parents=True)
            path = legacy_dir / "20260824-s-01-b20004-item.md"
            path.write_text(
                RecordBuilder().backlog(
                    id6="b20004",
                    status="open",
                    priority="high",
                    work_kind="bug",
                    text_only=True,
                ),
                encoding="utf-8",
            )
            assert_field(path, "status", "open")
            assert_field(path, "work_kind", "bug")
            assert_no_field(path, "blocks_release")

    def test_unknown_field_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            path = Path(rb.plan(id6="p20002", status="draft"))
            with self.assertRaises(ValueError):
                assert_field(path, "not_a_real_field", "x")
            with self.assertRaises(ValueError):
                assert_no_field(path, "not_a_real_field")

    def test_unknown_record_format_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _fresh_records_repo(Path(td) / "repo")
            rb = RecordBuilder(repo)
            path = Path(rb.plan(id6="p20003", status="draft"))
            with mock.patch.object(record_builder, "RECORD_FORMAT", "unknown-format"):
                with self.assertRaises(ValueError):
                    assert_field(path, "status", "draft")
                with self.assertRaises(ValueError):
                    assert_no_field(path, "blocks_release")


if __name__ == "__main__":
    unittest.main()
