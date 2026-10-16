"""Behavioral regression tests for slug slice trailing hyphens in backlog filenames.

Validates that fixed-length slug slicing in hand-formatted backlog filename builders
(backlog.run_new and set_records.promote_question_to_backlog) strips trailing hyphens
when a kebab slice boundary ends with a hyphen (IPD 1i2kgq).
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import backlog
from agent_workflows import check_engine
from agent_workflows import set_records
from tests import support


class SlugSliceTrailingHyphenTests(unittest.TestCase):
    """Behavioral tests verifying backlog filenames do not retain trailing hyphens after slug slicing."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = support.init_repo(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_run_new_strips_trailing_hyphen_after_slug_slice(self) -> None:
        summary = "a" * 49 + " tail words"
        args = argparse.Namespace(
            dir=str(self.repo),
            summary=summary,
            set="s",
            priority="high",
            kind="bug",
            apply=True,
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = backlog.run_new(args)

        self.assertEqual(rc, 0)
        items = list(self.repo.rglob("*.backlog.md"))
        self.assertEqual(len(items), 1)
        filename = items[0].name
        self.assertFalse(
            filename.endswith("-.backlog.md"),
            f"backlog filename {filename} ends with trailing hyphen before extension",
        )
        drifts = [
            d
            for d in check_engine.check_names(self.repo, "backlog")
            if d.rule == "check.name-nonconformant"
        ]
        self.assertEqual(
            drifts,
            [],
            f"check_names reported name-nonconformant drift: {drifts}",
        )

    def test_promote_question_to_backlog_strips_trailing_hyphen_after_slug_slice(
        self,
    ) -> None:
        summary = "a" * 49 + " tail words"
        result = set_records.promote_question_to_backlog(
            self.repo,
            decision_number=1,
            summary=summary,
            resume_command="aw oc run",
        )
        self.assertTrue(
            result.path.is_file(), f"promoted file {result.path} does not exist"
        )
        self.assertFalse(
            result.path.name.endswith("-.backlog.md"),
            f"promoted backlog filename {result.path.name} ends with trailing hyphen before extension",
        )
        drifts = [
            d
            for d in check_engine.check_names(self.repo, "backlog")
            if d.rule == "check.name-nonconformant"
        ]
        self.assertEqual(
            drifts,
            [],
            f"check_names reported name-nonconformant drift: {drifts}",
        )


if __name__ == "__main__":
    unittest.main()
