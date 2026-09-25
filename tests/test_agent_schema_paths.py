"""`agent_schema.normalize_repo_path` must relativize regardless of how the repo root is SPELLED.

Measured on the Windows CI runner: `tempfile` hands out the home dir as an 8.3 short
name while `Path.resolve()` yields the long name, so a string-prefix comparison failed,
the absolute path leaked into an `aw.agent/v1` record, and the validator raised "Unsanitized absolute
home path". A symlinked root is the portable proxy for the same class of mismatch.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agent_schema as S


class NormalizeRepoPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.real = Path(self._td.name) / "real"
        (self.real / ".aw" / "records").mkdir(parents=True)
        self.target = self.real / ".aw" / "records" / "Item.md"
        self.target.write_text("x", encoding="utf-8")

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_symlinked_root_relativizes_a_resolved_path(self) -> None:
        link = Path(self._td.name) / "link"
        try:
            os.symlink(self.real, link, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:  # unprivileged Windows
            self.skipTest(f"cannot create a symlink here: {exc}")
        cases = (
            (self.target.resolve(), link),
            (link / ".aw" / "records" / "Item.md", self.real),
            (str(self.target.resolve()).replace(os.sep, "\\"), str(link)),
        )
        for path, root in cases:
            with self.subTest(path=str(path), root=str(root)):
                self.assertEqual(
                    S.normalize_repo_path(path, root), ".aw/records/Item.md"
                )

    def test_relative_path_is_taken_relative_to_root(self) -> None:
        self.assertEqual(
            S.normalize_repo_path(".aw/records/Item.md", self.real),
            ".aw/records/Item.md",
        )

    def test_windows_drive_path_without_root_never_leaks(self) -> None:
        p = (
            "C:/"
            + "Users"
            + "/someone/AppData/Local/Temp/tmpx/.aw/records/backlog/a.md"
        )  # split: leak guard
        out = S.normalize_repo_path(p)
        self.assertEqual(out, ".aw/records/backlog/a.md")
        self.assertIsNone(S._HOME_PATH_RE.search(out))
        out2 = S.normalize_repo_path(p.replace("/", "\\"))
        self.assertEqual(out2, ".aw/records/backlog/a.md")

    def test_path_outside_root_is_not_relativized_upward(self) -> None:
        out = S.normalize_repo_path(
            Path(self._td.name) / "elsewhere" / "f.md", self.real
        )
        self.assertFalse(out.startswith(".."), out)


if __name__ == "__main__":
    unittest.main()
