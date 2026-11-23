"""Outcome tests for bounding the six sibling metadata value writes to the metadata region.

Covers IPD nrdrv6 (E-01 through E-08), now driven through ``artifact_meta.render_legacy_text``
(the in-memory form of the single metadata writer) for these fields:
- Priority
- Work-Kind
- From-Backlog
- From-Spec
- Item-Dependencies
- Graduated-To

Tests behavioral outcomes and contracts only; no source inspection or AST (P16).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional, Tuple

from agent_workflows import artifact_meta, releases, selectors
from tests.record_builder import RecordBuilder
from tests.support import run_cli

WriterTuple = Tuple[str, str, str, str]

WRITERS: List[WriterTuple] = [
    ("priority", "Priority", "low", "high"),
    ("work_kind", "Work-Kind", "chore", "feature"),
    ("from_backlog", "From-Backlog", "src001", "src002"),
    ("from_spec", "From-Spec", "spc001", "spc002"),
    (
        "item_dependencies",
        "Item-Dependencies",
        "none",
        "executed:abc123",
    ),
    ("graduated_to", "Graduated-To", "seta", "setb"),
]

_RENDER = artifact_meta.LegacyRender(
    "same-status", "2026-10-12", "aw set", history=False
)


def _write(text: str, key: str, value: Optional[str], record_type: str = "ipd") -> str:
    """Render one field set (or, for '-'/None, one unset) through ``artifact_meta``."""
    event = (
        {"op": "unset", "fields": [key]}
        if value in (None, "-")
        else {"op": "set", "fields": {key: value}}
    )
    return artifact_meta.render_legacy_text(
        text, [event], record_type=record_type, render=_RENDER
    )


def _make_fixture(field: str, val: str) -> str:
    return RecordBuilder().plan(
        title="Plan Title",
        id6="pln111",
        status="draft",
        scope_paths="agent_workflows/releases.py",
        set="testset",
        body=(
            "## Description\n"
            "Here is a quoted configuration bullet in the body:\n"
            f"- {field}: {val}\n"
            "Trailing body text."
        ),
        raw_fields={field: val},
        text_only=True,
    )


def _make_fixture_no_field(field: str) -> str:
    return RecordBuilder().plan(
        title="Plan Title",
        id6="pln111",
        status="draft",
        scope_paths="agent_workflows/releases.py",
        set="testset",
        body=(
            "## Description\n"
            "Here is a quoted configuration bullet in the body:\n"
            f"- {field}: quote_val\n"
            "Trailing body text."
        ),
        raw_fields={field: None},
        text_only=True,
    )


class TestReleasesSiblingLineWritersBounding(unittest.TestCase):
    """Behavioral outcome tests for bounding the six sibling line writers."""

    def test_setting_value_preserves_body(self) -> None:
        """(a) Setting a value replaces the front-matter line and leaves the body after

        ## Description byte-identical.
        """
        for key, field, old_val, new_val in WRITERS:
            with self.subTest(writer=key, field=field):
                fixture = _make_fixture(field, old_val)
                body_before = fixture.partition("## Description")[2]
                res = _write(fixture, key, new_val)
                body_after = res.partition("## Description")[2]
                self.assertEqual(body_after, body_before)
                self.assertIn(f"- {field}: {old_val}\n", body_after)

    def test_writer_idempotence(self) -> None:
        """(b) Applying the writer twice yields identical text (idempotence)."""
        for key, field, old_val, new_val in WRITERS:
            with self.subTest(writer=key, field=field):
                fixture = _make_fixture(field, old_val)
                once = _write(fixture, key, new_val)
                twice = _write(once, key, new_val)
                self.assertEqual(once, twice)

    def test_clear_dash_and_none_preserves_body(self) -> None:
        """(c) '-' and None remove the FRONT-MATTER line only and the body quote survives."""
        for key, field, old_val, _ in WRITERS:
            with self.subTest(writer=key, field=field):
                fixture = _make_fixture(field, old_val)
                body_before = fixture.partition("## Description")[2]

                for clear_val in ("-", None):
                    res = _write(fixture, key, clear_val)
                    body_after = res.partition("## Description")[2]
                    self.assertEqual(body_after, body_before)
                    self.assertIn(f"- {field}: {old_val}\n", body_after)
                    region = selectors.metadata_region(res)
                    self.assertNotIn(f"- {field}:", region)

    def test_no_front_matter_line_adds_one_and_preserves_body(self) -> None:
        """(d) On a fixture with NO front-matter line for the field, exactly one line is

        added and the body is byte-identical.
        """
        for key, field, _, new_val in WRITERS:
            with self.subTest(writer=key, field=field):
                fixture = _make_fixture_no_field(field)
                body_before = fixture.partition("## Description")[2]
                res = _write(fixture, key, new_val)
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
        for key, field, old_val, new_val in WRITERS:
            with self.subTest(writer=key, field=field):
                fixture = _make_fixture(field, old_val)
                res = _write(fixture, key, new_val)
                region = selectors.metadata_region(res)
                self.assertEqual(region.count(f"- {field}:"), 1)
                self.assertIn(f"- {field}: {new_val}\n", region)
                self.assertNotIn(f"- {field}: {old_val}\n", region)

    def test_anchor_in_body_does_not_divert_insertion(self) -> None:
        """(e2) ANCHOR-IN-BODY: a fixture whose region carries - Id: but NOT the writer's

        preferred anchor (- Status:, or - Scope-Paths: for Item-Dependencies) while
        the body quotes that anchor bullet: the new line lands inside selectors.metadata_region
        of the output (or, with no in-region anchor at all, the text is returned unchanged)
        and the body is byte-identical.
        """
        # Part 1: the Item-Dependencies write's preferred anchor is - Scope-Paths:, fallback is - Status:
        # Region has - Status: and - Id:, but NO - Scope-Paths:. Body quotes - Scope-Paths:.
        text_deps = RecordBuilder().plan(
            title="Plan Title",
            id6="pln111",
            status="draft",
            set="testset",
            body=(
                "## Description\n"
                "Quoted scope in body:\n"
                "- Scope-Paths: agent_workflows/releases.py\n"
                "Trailing body."
            ),
            raw_fields={"Scope-Paths": None, "Item-Dependencies": None},
            text_only=True,
        )
        body_before_deps = text_deps.partition("## Description")[2]
        res_deps = _write(text_deps, "item_dependencies", "executed:abc123")
        body_after_deps = res_deps.partition("## Description")[2]
        self.assertEqual(body_after_deps, body_before_deps)
        region_deps = selectors.metadata_region(res_deps)
        self.assertIn("- Item-Dependencies: executed:abc123\n", region_deps)
        self.assertEqual(region_deps.count("- Item-Dependencies:"), 1)

        # Part 2: The other 5 writers preferred anchor is - Status:, fallback is - Id:.
        # Region has - Id:, but NO - Status:. Body quotes - Status:.
        for key, field, _, new_val in WRITERS:
            if key == "item_dependencies":
                continue
            with self.subTest(writer=key, field=field, case="anchor_fallback"):
                text_stat = RecordBuilder().plan(
                    title="Plan Title",
                    id6="pln111",
                    status="draft",
                    set="testset",
                    body=(
                        "## Description\n"
                        "Quoted status in body:\n"
                        "- Status: draft\n"
                        "Trailing body."
                    ),
                    raw_fields={"Status": None, "Priority": None, "Work-Kind": None},
                    text_only=True,
                )
                body_before = text_stat.partition("## Description")[2]
                res = _write(text_stat, key, new_val)
                body_after = res.partition("## Description")[2]
                self.assertEqual(body_after, body_before)
                region = selectors.metadata_region(res)
                self.assertIn(f"- {field}: {new_val}\n", region)
                self.assertEqual(region.count(f"- {field}:"), 1)

        # Part 3: No in-region anchor at all (- Status: and - Id: both absent in region).
        # Body quotes - Status:. Bounded writer must return text unchanged without searching body.
        for key, field, _, new_val in WRITERS:
            with self.subTest(writer=key, field=field, case="no_anchor"):
                text_no_anchor = RecordBuilder().plan(
                    title="Plan Title",
                    when="2026-10-12",
                    id6="pln111",
                    status="draft",
                    set="testset",
                    body=(
                        "## Description\n"
                        "Quoted status in body:\n"
                        "- Status: draft\n"
                        "- Id: pln111\n"
                        "Trailing body."
                    ),
                    raw_fields={
                        "Status": None,
                        "Id": None,
                        "Scope-Paths": None,
                        "Priority": None,
                        "Work-Kind": None,
                        "Item-Dependencies": None,
                    },
                    text_only=True,
                )
                res = _write(text_no_anchor, key, new_val)
                self.assertEqual(res, text_no_anchor)

    def test_graduated_to_multi_value_replacement_and_body_preservation(self) -> None:
        """(f) For the Graduated-To write: a front-matter - Graduated-To: aaa, bbb replaced

        by ccc leaves exactly one front-matter Graduated-To line, while a body
        - Graduated-To: aaa, bbb survives.
        """
        text = RecordBuilder().backlog(
            id6="bkl001",
            status="open",
            graduated_to="aaa, bbb",
            set="testset",
            body="## Description\nBody quoting graduation:\n- Graduated-To: aaa, bbb\nEnd of description.",
            text_only=True,
        )
        res = _write(text, "graduated_to", "ccc", "backlog")
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
        for key, field, _, new_val in WRITERS:
            with self.subTest(writer=key, field=field):
                yaml_text = RecordBuilder().research(
                    id6="rsc001",
                    status="active",
                    body=f"\n# Research Document\n\nBody bullet quote:\n- {field}: quote_val\nMore text.\n",
                    text_only=True,
                )
                res = _write(yaml_text, key, new_val, "research")
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
                RecordBuilder().backlog(
                    id6="bkl111",
                    status="open",
                    set="testset",
                    priority="low",
                    work_kind="chore",
                    summary="Demo item",
                    history=["- 2026-10-12 open (tester): created"],
                    body="## Description\nQuoted configuration line in body:\n- Work-Kind: chore\nEnd of description.",
                    text_only=True,
                ),
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
