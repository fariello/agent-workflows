"""Restored docs_check test coverage.

Plan t9lcdu / Set gzmr54.
Restores test coverage deleted in 19313eed for agent_workflows/docs_check.py.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import docs_check as dc
from tests.support import REPO_ROOT


class DocCheckFalsifiabilityTests(unittest.TestCase):
    def test_detects_em_dash(self):
        findings = dc.check_no_unicode_dashes("a \u2014 b", "x.md")
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f.doc, "x.md")
        self.assertEqual(f.line, 1)
        self.assertEqual(f.check, "no-unicode-dashes")
        self.assertIn("em dash (U+2014)", f.message)
        self.assertEqual(
            str(f), "x.md:1: [no-unicode-dashes] em dash (U+2014) in user-facing prose"
        )

    def test_detects_en_dash(self):
        findings = dc.check_no_unicode_dashes("a \u2013 b", "x.md")
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f.doc, "x.md")
        self.assertEqual(f.line, 1)
        self.assertEqual(f.check, "no-unicode-dashes")
        self.assertIn("en dash (U+2013)", f.message)
        self.assertEqual(
            str(f), "x.md:1: [no-unicode-dashes] en dash (U+2013) in user-facing prose"
        )

    def test_allows_ascii_hyphens(self):
        findings = dc.check_no_unicode_dashes("a - b -- c --- d", "x.md")
        self.assertEqual(findings, [])

    def test_detects_broken_link(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            doc = base / "a.md"
            doc.write_text("see [missing](./nope.md)\n", encoding="utf-8")
            findings = dc.check_internal_links(doc.read_text(encoding="utf-8"), doc)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.doc, "a.md")
            self.assertEqual(f.line, 1)
            self.assertEqual(f.check, "internal-link")
            self.assertEqual(f.message, "link target './nope.md' does not exist")
            self.assertEqual(
                str(f), "a.md:1: [internal-link] link target './nope.md' does not exist"
            )

    def test_allows_valid_internal_link(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            doc = base / "a.md"
            target = base / "target.md"
            target.write_text("target content\n", encoding="utf-8")
            doc.write_text("see [target](./target.md)\n", encoding="utf-8")
            findings = dc.check_internal_links(doc.read_text(encoding="utf-8"), doc)
            self.assertEqual(findings, [])

    def test_allows_external_anchor_and_mailto_links(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            doc = base / "a.md"
            text = (
                "see [http](http://example.com)\n"
                "see [https](https://example.com)\n"
                "see [anchor](#section)\n"
                "see [mail](mailto:test@example.com)\n"
            )
            doc.write_text(text, encoding="utf-8")
            findings = dc.check_internal_links(text, doc)
            self.assertEqual(findings, [])

    def test_detects_unknown_command(self):
        findings = dc.check_aw_commands("run `aw florb` please", ["run", "ipd"], "x.md")
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f.doc, "x.md")
        self.assertEqual(f.line, 1)
        self.assertEqual(f.check, "aw-command")
        self.assertEqual(f.message, "'aw florb' is not a known subcommand")
        self.assertEqual(
            str(f), "x.md:1: [aw-command] 'aw florb' is not a known subcommand"
        )

    def test_allows_known_command(self):
        findings = dc.check_aw_commands(
            "run `aw ipd` and `aw run` please", ["run", "ipd"], "x.md"
        )
        self.assertEqual(findings, [])

    def test_ignores_plain_prose_command_reference(self):
        findings = dc.check_aw_commands(
            "## The aw router skill", ["run", "ipd"], "x.md"
        )
        self.assertEqual(findings, [])

    def test_detects_unknown_command_in_fenced_block(self):
        text = "```bash\naw florb\n```"
        findings = dc.check_aw_commands(text, ["run", "ipd"], "x.md")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line, 2)
        self.assertEqual(findings[0].check, "aw-command")
        self.assertEqual(findings[0].message, "'aw florb' is not a known subcommand")

    def test_allows_known_command_in_fenced_block(self):
        text = "```bash\naw run\naw ipd\n```"
        findings = dc.check_aw_commands(text, ["run", "ipd"], "x.md")
        self.assertEqual(findings, [])

    def test_check_doc_drives_all_checks(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            clean_doc = base / "clean.md"
            clean_doc.write_text(
                "# Clean doc\n\nLink to [clean](#clean) and `aw run`.\n",
                encoding="utf-8",
            )
            self.assertEqual(dc.check_doc(clean_doc, subcommands=["run"]), [])

            bad_doc = base / "bad.md"
            bad_doc.write_text(
                "Em dash \u2014 here\n[bad link](./absent.md)\n`aw bogus`\n",
                encoding="utf-8",
            )
            findings = dc.check_doc(bad_doc, subcommands=["run"])
            self.assertEqual(len(findings), 3)
            checks = [f.check for f in findings]
            self.assertIn("no-unicode-dashes", checks)
            self.assertIn("internal-link", checks)
            self.assertIn("aw-command", checks)

    def test_check_doc_requires_path(self):
        with self.assertRaises((AttributeError, TypeError)):
            dc.check_doc("not a path", ["run", "ipd"])  # type: ignore[arg-type]


DOCS_DIR = REPO_ROOT / "docs"


class DocCheckTests(unittest.TestCase):
    def test_no_findings_across_docs(self):
        # FALSIFIABLE: any broken link, unknown `aw` subcommand, or em/en dash is a finding.
        findings = dc.check_docs_dir(DOCS_DIR)
        self.assertEqual(findings, [], "\n".join(str(f) for f in findings))

    def test_check_docs_dir_respects_ignored_directories(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            ignored_dir = base / "node_modules"
            ignored_dir.mkdir()
            bad_doc = ignored_dir / "bad.md"
            bad_doc.write_text("Em dash \u2014 here\n`aw bogus`\n", encoding="utf-8")
            findings = dc.check_docs_dir(base)
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
