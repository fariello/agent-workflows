"""Outcome tests for bounding the six sibling releases line writers to the metadata region.

Covers IPD nrdrv6 (E-01 through E-08):
- set_priority_line
- set_work_kind_line
- set_from_backlog_line
- set_from_spec_line
- set_item_dependencies_line
- set_graduated_to_line

Tests behavioral outcomes and contracts only; no source inspection or AST (P16).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from agent_workflows import releases, selectors
from tests.support import run_cli

WriterTuple = Tuple[Callable[[str, Optional[str]], str], str, str, str]

WRITERS: List[WriterTuple] = [
    (releases.set_priority_line, "Priority", "low", "high"),
    (releases.set_work_kind_line, "Work-Kind", "chore", "feature"),
    (releases.set_from_backlog_line, "From-Backlog", "src001", "src002"),
    (releases.set_from_spec_line, "From-Spec", "spc001", "spc002"),
    (
        releases.set_item_dependencies_line,
        "Item-Dependencies",
        "none",
        "executed:abc123",
    ),
    (releases.set_graduated_to_line, "Graduated-To", "seta", "setb"),
]


def _make_fixture(field: str, val: str) -> str:
    return (
        "# Plan Title\n\n"
        "- Id: pln111\n"
        "- Status: draft\n"
        "- Scope-Paths: agent_workflows/releases.py\n"
        f"- {field}: {val}\n"
        "- Set: testset\n\n"
        "## Description\n"
        "Here is a quoted configuration bullet in the body:\n"
        f"- {field}: {val}\n"
        "Trailing body text.\n"
    )


def _make_fixture_no_field(field: str) -> str:
    return (
        "# Plan Title\n\n"
        "- Id: pln111\n"
        "- Status: draft\n"
        "- Scope-Paths: agent_workflows/releases.py\n"
        "- Set: testset\n\n"
        "## Description\n"
        "Here is a quoted configuration bullet in the body:\n"
        f"- {field}: quote_val\n"
        "Trailing body text.\n"
    )


class TestReleasesSiblingLineWritersBounding(unittest.TestCase):
    """Behavioral outcome tests for bounding the six sibling line writers."""

    def test_setting_value_preserves_body(self) -> None:
        """(a) Setting a value replaces the front-matter line and leaves the body after

        ## Description byte-identical.
        """
        for writer, field, old_val, new_val in WRITERS:
            with self.subTest(writer=writer.__name__, field=field):
                fixture = _make_fixture(field, old_val)
                body_before = fixture.partition("## Description")[2]
                res = writer(fixture, new_val)
                body_after = res.partition("## Description")[2]
                self.assertEqual(body_after, body_before)
                self.assertIn(f"- {field}: {old_val}\n", body_after)

    def test_writer_idempotence(self) -> None:
        """(b) Applying the writer twice yields identical text (idempotence)."""
        for writer, field, old_val, new_val in WRITERS:
            with self.subTest(writer=writer.__name__, field=field):
                fixture = _make_fixture(field, old_val)
                once = writer(fixture, new_val)
                twice = writer(once, new_val)
                self.assertEqual(once, twice)

    def test_clear_dash_and_none_preserves_body(self) -> None:
        """(c) '-' and None remove the FRONT-MATTER line only and the body quote survives."""
        for writer, field, old_val, _ in WRITERS:
            with self.subTest(writer=writer.__name__, field=field):
                fixture = _make_fixture(field, old_val)
                body_before = fixture.partition("## Description")[2]

                for clear_val in ("-", None):
                    res = writer(fixture, clear_val)
                    body_after = res.partition("## Description")[2]
                    self.assertEqual(body_after, body_before)
                    self.assertIn(f"- {field}: {old_val}\n", body_after)
                    region = selectors.metadata_region(res)
                    self.assertNotIn(f"- {field}:", region)

    def test_no_front_matter_line_adds_one_and_preserves_body(self) -> None:
        """(d) On a fixture with NO front-matter line for the field, exactly one line is

        added and the body is byte-identical.
        """
        for writer, field, _, new_val in WRITERS:
            with self.subTest(writer=writer.__name__, field=field):
                fixture = _make_fixture_no_field(field)
                body_before = fixture.partition("## Description")[2]
                res = writer(fixture, new_val)
                body_after = res.partition("## Description")[2]
                self.assertEqual(body_after, body_before)
                self.assertIn(f"- {field}: quote_val\n", body_after)
                region = selectors.metadata_region(res)
                self.assertEqual(region.count(f"- {field}:"), 1)
                self.assertIn(f"- {field}: {new_val}\n", region)

    def test_control_front_matter_line_is_replaced(self) -> None:
        """(e) CONTROL asserting the front-matter line IS replaced (exactly one occurrence

        of the new value in the region), so no assertion can pass by a writer that strips nothing.
        """
        for writer, field, old_val, new_val in WRITERS:
            with self.subTest(writer=writer.__name__, field=field):
                fixture = _make_fixture(field, old_val)
                res = writer(fixture, new_val)
                region = selectors.metadata_region(res)
                self.assertEqual(region.count(f"- {field}:"), 1)
                self.assertIn(f"- {field}: {new_val}\n", region)
                self.assertNotIn(f"- {field}: {old_val}\n", region)

    def test_anchor_in_body_does_not_divert_insertion(self) -> None:
        """(e2) ANCHOR-IN-BODY: a fixture whose region carries - Id: but NOT the writer's

        preferred anchor (- Status:, or - Scope-Paths: for set_item_dependencies_line) while
        the body quotes that anchor bullet: the new line lands inside selectors.metadata_region
        of the output (or, with no in-region anchor at all, the text is returned unchanged)
        and the body is byte-identical.
        """
        # Part 1: set_item_dependencies_line preferred anchor is - Scope-Paths:, fallback is - Status:
        # Region has - Status: and - Id:, but NO - Scope-Paths:. Body quotes - Scope-Paths:.
        text_deps = (
            "# Plan Title\n\n"
            "- Id: pln111\n"
            "- Status: draft\n"
            "- Set: testset\n\n"
            "## Description\n"
            "Quoted scope in body:\n"
            "- Scope-Paths: agent_workflows/releases.py\n"
            "Trailing body.\n"
        )
        body_before_deps = text_deps.partition("## Description")[2]
        res_deps = releases.set_item_dependencies_line(text_deps, "executed:abc123")
        body_after_deps = res_deps.partition("## Description")[2]
        self.assertEqual(body_after_deps, body_before_deps)
        region_deps = selectors.metadata_region(res_deps)
        self.assertIn("- Item-Dependencies: executed:abc123\n", region_deps)
        self.assertEqual(region_deps.count("- Item-Dependencies:"), 1)

        # Part 2: The other 5 writers preferred anchor is - Status:, fallback is - Id:.
        # Region has - Id:, but NO - Status:. Body quotes - Status:.
        for writer, field, _, new_val in WRITERS:
            if writer is releases.set_item_dependencies_line:
                continue
            with self.subTest(
                writer=writer.__name__, field=field, case="anchor_fallback"
            ):
                text_stat = (
                    "# Plan Title\n\n"
                    "- Id: pln111\n"
                    "- Set: testset\n\n"
                    "## Description\n"
                    "Quoted status in body:\n"
                    "- Status: draft\n"
                    "Trailing body.\n"
                )
                body_before = text_stat.partition("## Description")[2]
                res = writer(text_stat, new_val)
                body_after = res.partition("## Description")[2]
                self.assertEqual(body_after, body_before)
                region = selectors.metadata_region(res)
                self.assertIn(f"- {field}: {new_val}\n", region)
                self.assertEqual(region.count(f"- {field}:"), 1)

        # Part 3: No in-region anchor at all (- Status: and - Id: both absent in region).
        # Body quotes - Status:. Bounded writer must return text unchanged without searching body.
        for writer, field, _, new_val in WRITERS:
            with self.subTest(writer=writer.__name__, field=field, case="no_anchor"):
                text_no_anchor = (
                    "# Plan Title\n\n"
                    "- Date: 2026-10-12\n"
                    "- Set: testset\n\n"
                    "## Description\n"
                    "Quoted status in body:\n"
                    "- Status: draft\n"
                    "- Id: pln111\n"
                    "Trailing body.\n"
                )
                res = writer(text_no_anchor, new_val)
                self.assertEqual(res, text_no_anchor)

    def test_graduated_to_multi_value_replacement_and_body_preservation(self) -> None:
        """(f) For set_graduated_to_line: a front-matter - Graduated-To: aaa, bbb replaced

        by ccc leaves exactly one front-matter Graduated-To line, while a body
        - Graduated-To: aaa, bbb survives.
        """
        text = (
            "# Backlog Title\n\n"
            "- Id: bkl001\n"
            "- Status: open\n"
            "- Graduated-To: aaa, bbb\n"
            "- Set: testset\n\n"
            "## Description\n"
            "Body quoting graduation:\n"
            "- Graduated-To: aaa, bbb\n"
            "End of description.\n"
        )
        res = releases.set_graduated_to_line(text, "ccc")
        body_orig = text.partition("## Description")[2]
        body_res = res.partition("## Description")[2]
        self.assertEqual(body_res, body_orig)
        self.assertIn("- Graduated-To: aaa, bbb\n", body_res)

        region = selectors.metadata_region(res)
        self.assertEqual(region.count("- Graduated-To:"), 1)
        self.assertIn("- Graduated-To: ccc\n", region)
        self.assertNotIn("- Graduated-To: aaa", region)

    def test_yaml_fenced_fixture_body_bullet_survives(self) -> None:
        """(g) A YAML-fenced fixture (leading --- fence then body bullets) asserting a body

        bullet survives each writer.
        """
        for writer, field, _, new_val in WRITERS:
            with self.subTest(writer=writer.__name__, field=field):
                yaml_text = (
                    "---\n"
                    "id: rsc001\n"
                    "status: active\n"
                    "---\n\n"
                    "# Research Document\n\n"
                    "Body bullet quote:\n"
                    f"- {field}: quote_val\n"
                    "More text.\n"
                )
                res = writer(yaml_text, new_val)
                body_orig = yaml_text.partition("# Research Document")[2]
                body_res = res.partition("# Research Document")[2]
                self.assertEqual(body_res, body_orig)
                self.assertIn(f"- {field}: quote_val\n", body_res)

    def test_cli_backlog_set_work_kind_preserves_body(self) -> None:
        """(h) One CLI-level test driving aw backlog set open <id6> --work-kind feature

        --no-commit --dir <root> via tests.support.run_cli on a fixture backlog item with
        front-matter - Work-Kind: chore whose ## Description body quotes - Work-Kind: chore,
        asserting exit 0, the front matter carries - Work-Kind: feature, and the body quote
        line is still present in the written file.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.name", "Tester"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "tester@example.com"],
                cwd=root,
                check=True,
                capture_output=True,
            )

            releases.create_release(root, "2.0.0", "planned release")

            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True, exist_ok=True)
            item_path = bdir / "20261012-bkl111-01-bkl111-demo.backlog.md"
            item_path.write_text(
                "- Id: bkl111\n"
                "- Status: open\n"
                "- Set: testset\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: Demo item\n\n"
                "## Description\n"
                "Quoted configuration line in body:\n"
                "- Work-Kind: chore\n"
                "End of description.\n\n"
                "## Workflow history\n"
                "- 2026-10-12 open (tester): created\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "-A"], cwd=root, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "init repo"],
                cwd=root,
                check=True,
                capture_output=True,
            )

            proc = run_cli(
                "backlog",
                "set",
                "open",
                "bkl111",
                "--work-kind",
                "feature",
                "--no-commit",
                "--dir",
                str(root),
                cwd=root,
            )
            self.assertEqual(
                proc.returncode, 0, f"stderr: {proc.stderr}\nstdout: {proc.stdout}"
            )
            written = item_path.read_text(encoding="utf-8")
            region = selectors.metadata_region(written)
            body = written.partition("## Description")[2]

            self.assertIn("- Work-Kind: feature\n", region)
            self.assertIn("- Work-Kind: chore\n", body)


if __name__ == "__main__":
    unittest.main()
