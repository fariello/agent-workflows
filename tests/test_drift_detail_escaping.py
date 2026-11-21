"""Tests for drift detail escaping behavior (Set 4ep6mp, IPD 8cu5ml).

Validates that drift detail producers do not double-escape values that have
already been escaped by repr (F-03), that provable-identity call sites return
the literal unescaped detail (F-04), and that end-to-end JSON payloads decode
to the single-repr form (F-03 / E-02).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention as att
from agent_workflows import releases
from agent_workflows import research_cmd as C
from agent_workflows import research_index as I
from agent_workflows import specs
from tests.record_builder import RecordBuilder


class TestReprWrappedSites(unittest.TestCase):
    """(a) REPR-WRAPPED sites (F-03).

    A hostile value containing backslash/tab yields a detail EQUAL to the
    producer's message formatted with a single repr and no raw control bytes.
    On the unmodified tree, escape_detail doubles backslashes, causing failure.
    """

    def test_prompts_record_bucket_escaping(self):
        """attention._prompts_record: prompt disposition {disp!r}."""
        bucket = "unknown\tbucket"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            pdir = root / ".aw" / "records" / "prompts" / bucket
            try:
                pdir.mkdir(parents=True, exist_ok=True)
            except OSError:
                bucket = "unknown_bucket"
                pdir = root / ".aw" / "records" / "prompts" / bucket
                pdir.mkdir(parents=True, exist_ok=True)
            p = pdir / "20260101-prm-01-test.prompt.md"
            p.write_text(
                RecordBuilder().prompt(id6="prm001", text_only=True), encoding="utf-8"
            )

            items, drift = att.scan(root)
            unknown = [d for d in drift if d.rule == "attention.unknown-status"]
            self.assertEqual(len(unknown), 1)
            detail = unknown[0].detail
            self.assertNotIn("\t", detail)
            self.assertNotIn("\n", detail)
            self.assertNotIn("\r", detail)
            expected = f"prompt disposition {bucket!r}"
            self.assertEqual(detail, expected)

    def test_release_record_status_escaping(self):
        """attention._release_record: release status {status!r}."""
        status = "we\\ird"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rdir = root / ".aw" / "records" / "releases"
            rdir.mkdir(parents=True, exist_ok=True)
            p = rdir / "20260101-rel-01-rel-test.release.md"
            p.write_text(
                RecordBuilder().release(
                    id6="rel001",
                    version="1.0.0",
                    raw_fields={"Status": status},
                    text_only=True,
                ),
                encoding="utf-8",
            )

            items, drift = att.scan(root)
            unknown = [d for d in drift if d.rule == "attention.unknown-status"]
            self.assertEqual(len(unknown), 1)
            detail = unknown[0].detail
            self.assertNotIn("\t", detail)
            self.assertNotIn("\n", detail)
            self.assertNotIn("\r", detail)
            expected = f"release status {status!r}"
            self.assertEqual(detail, expected)

    def test_plans_record_status_escaping(self):
        """attention._plans_record: plan status {status!r}."""
        status = "we\\ird"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            pdir = root / ".aw" / "records" / "plans" / "pending"
            pdir.mkdir(parents=True, exist_ok=True)
            p = pdir / "20260101-set-01-p10001-test.ipd.md"
            p.write_text(
                RecordBuilder().plan(
                    title="test",
                    id6="p10001",
                    set="set",
                    order=1,
                    raw_fields={"Status": status},
                    text_only=True,
                ),
                encoding="utf-8",
            )

            items, drift = att.scan(root)
            unknown = [d for d in drift if d.rule == "attention.unknown-status"]
            self.assertEqual(len(unknown), 1)
            detail = unknown[0].detail
            self.assertNotIn("\t", detail)
            self.assertNotIn("\n", detail)
            self.assertNotIn("\r", detail)
            # plans_mod.read_status normalizes unrecognized status to 'legacy/unknown'
            expected = f"plan status {'legacy/unknown'!r}"
            self.assertEqual(detail, expected)

    def test_research_record_status_escaping(self):
        """attention._research_record: research status {raw_status_str!r}."""
        status = "we\\ird"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rdir = root / ".aw" / "records" / "research"
            rdir.mkdir(parents=True, exist_ok=True)
            p = rdir / "20260101-01-test.research.md"
            p.write_text(
                RecordBuilder().research(
                    id6="res001",
                    body="# Research\n",
                    raw_fields={"status": status},
                    text_only=True,
                ),
                encoding="utf-8",
            )

            items, drift = att.scan(root)
            unknown = [d for d in drift if d.rule == "attention.unknown-status"]
            self.assertEqual(len(unknown), 1)
            detail = unknown[0].detail
            self.assertNotIn("\t", detail)
            self.assertNotIn("\n", detail)
            self.assertNotIn("\r", detail)
            expected = f"research status {status!r}"
            self.assertEqual(detail, expected)

    def test_backlog_record_status_escaping(self):
        """attention._backlog_record: backlog status {status!r}."""
        status = "we\\ird"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True, exist_ok=True)
            p = bdir / "20260101-b10001-01-b10001-test.backlog.md"
            p.write_text(
                RecordBuilder().backlog(
                    id6="b10001",
                    priority="high",
                    work_kind="feature",
                    summary="test",
                    raw_fields={"Status": status},
                    text_only=True,
                ),
                encoding="utf-8",
            )

            items, drift = att.scan(root)
            unknown = [d for d in drift if d.rule == "attention.unknown-status"]
            self.assertEqual(len(unknown), 1)
            detail = unknown[0].detail
            self.assertNotIn("\t", detail)
            self.assertNotIn("\n", detail)
            self.assertNotIn("\r", detail)
            expected = f"backlog status {status!r}"
            self.assertEqual(detail, expected)

    def test_specs_validate_spec_status_escaping(self):
        """specs.validate_spec: status {status!r} not in the spec enum."""
        status = "we\\ird"
        text = RecordBuilder().spec(
            title="test",
            id6="s10001",
            history=["- 2026-01-01 draft (t): init"],
            raw_fields={"Status": status},
            text_only=True,
        )
        drift = specs.validate_spec(Path("test.spec.md"), text)
        unknown = [d for d in drift if d.rule == "attention.unknown-status"]
        self.assertEqual(len(unknown), 1)
        detail = unknown[0].detail
        self.assertNotIn("\t", detail)
        self.assertNotIn("\n", detail)
        self.assertNotIn("\r", detail)
        expected = f"status {status!r} not in the spec enum"
        self.assertEqual(detail, expected)

    def test_specs_validate_spec_unknown_gate_kind_escaping(self):
        """specs.validate_spec: unknown Gate-Kind {kind!r}."""
        kind = "we\\ird"
        text = RecordBuilder().spec(
            title="test",
            id6="s10001",
            status="deferred",
            gate_kind=kind,
            gate_ref="ref",
            history=["- 2026-01-01 draft (t): init"],
            text_only=True,
        )
        drift = specs.validate_spec(Path("test.spec.md"), text)
        malformed = [d for d in drift if d.rule == "attention.gate-malformed"]
        self.assertEqual(len(malformed), 1)
        detail = malformed[0].detail
        self.assertNotIn("\t", detail)
        self.assertNotIn("\n", detail)
        self.assertNotIn("\r", detail)
        expected = f"unknown Gate-Kind {kind!r}"
        self.assertEqual(detail, expected)

    def test_specs_validate_spec_invalid_gate_ref_escaping(self):
        """specs.validate_spec: invalid Gate-Ref for {kind}: {ref!r}."""
        ref = "we\\ird\tx"
        text = RecordBuilder().spec(
            title="test",
            id6="s10001",
            status="deferred",
            gate_kind="external",
            history=["- 2026-01-01 draft (t): init"],
            raw_fields={"Gate-Ref": ref},
            text_only=True,
        )
        drift = specs.validate_spec(Path("test.spec.md"), text)
        malformed = [d for d in drift if d.rule == "attention.gate-malformed"]
        self.assertEqual(len(malformed), 1)
        detail = malformed[0].detail
        self.assertNotIn("\t", detail)
        self.assertNotIn("\n", detail)
        self.assertNotIn("\r", detail)
        expected = f"invalid Gate-Ref for external: {ref!r}"
        self.assertEqual(detail, expected)


class TestProvableIdentitySites(unittest.TestCase):
    """(b) PROVABLE-IDENTITY sites (F-04).

    These call sites pass constants or bounded strings containing no backslash,
    tab, newline or carriage return. They must equal the literal message exactly.
    """

    def test_specs_validate_spec_duplicate_bullet(self):
        """specs.validate_spec: metadata bullet - {k}: appears {count} times."""
        text = RecordBuilder().spec(
            title="test",
            id6="s10001",
            status="draft",
            author="alice",
            history=["- 2026-01-01 draft (t): init"],
            raw_fields={"Author": "alice\n- Author: bob"},
            text_only=True,
        )
        drift = specs.validate_spec(Path("test.spec.md"), text)
        repeated = [d for d in drift if d.rule == "spec.metadata-bullet-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertEqual(
            repeated[0].detail, "metadata bullet - Author: appears 2 times"
        )

    def test_specs_validate_spec_scope_over_length(self):
        """specs.validate_spec: Scope is over-length or has control chars/newlines."""
        text = RecordBuilder().spec(
            title="test",
            id6="s10001",
            status="draft",
            history=["- 2026-01-01 draft (t): init"],
            raw_fields={"Scope": "x" * 4301},
            text_only=True,
        )
        drift = specs.validate_spec(Path("test.spec.md"), text)
        unsafe = [d for d in drift if d.rule == "attention.unsafe-field"]
        self.assertEqual(len(unsafe), 1)
        self.assertEqual(
            unsafe[0].detail, "Scope is over-length or has control chars/newlines"
        )

    def test_specs_validate_spec_summary_over_length(self):
        """specs.validate_spec: Summary is over-length or has control chars/newlines."""
        text = RecordBuilder().spec(
            title="test",
            id6="s10001",
            status="draft",
            history=["- 2026-01-01 draft (t): init"],
            raw_fields={"Summary": "x" * 301},
            text_only=True,
        )
        drift = specs.validate_spec(Path("test.spec.md"), text)
        unsafe = [d for d in drift if d.rule == "attention.unsafe-field"]
        self.assertEqual(len(unsafe), 1)
        self.assertEqual(
            unsafe[0].detail, "Summary is over-length or has control chars/newlines"
        )

    def test_research_index_summary_over_length(self):
        """research_index.check_drift: Summary is over-length or has control chars/newlines."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rroot = root / ".aw" / "records" / "research"
            rroot.mkdir(parents=True, exist_ok=True)
            doc = rroot / "20261002-test-01-sh0001-doc1.notes.md"
            doc.write_text(
                C.build_frontmatter(
                    id6="sh0001",
                    created="20261002",
                    set_id="test",
                    order="01",
                    topic=["t1"],
                    model=None,
                    kind="notes",
                    status="todo",
                    outcome="none-yet",
                    summary="x" * 301,
                    consumed_by=[],
                )
                + "\n\nbody\n",
                encoding="utf-8",
            )
            drifts = I.check_drift(root, rroot)
            unsafe = [d for d in drifts if d.rule == "attention.unsafe-field"]
            self.assertEqual(len(unsafe), 1)
            self.assertEqual(
                unsafe[0].detail, "Summary is over-length or has control chars/newlines"
            )

    def test_research_index_topic_over_length(self):
        """research_index.check_drift: Topic is over-length or has control chars/newlines."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rroot = root / ".aw" / "records" / "research"
            rroot.mkdir(parents=True, exist_ok=True)
            doc = rroot / "20261002-test-01-sh0001-doc1.notes.md"
            doc.write_text(
                C.build_frontmatter(
                    id6="sh0001",
                    created="20261002",
                    set_id="test",
                    order="01",
                    topic=["x" * 301],
                    model=None,
                    kind="notes",
                    status="todo",
                    outcome="none-yet",
                    summary="valid",
                    consumed_by=[],
                )
                + "\n\nbody\n",
                encoding="utf-8",
            )
            drifts = I.check_drift(root, rroot)
            unsafe = [d for d in drifts if d.rule == "attention.unsafe-field"]
            self.assertEqual(len(unsafe), 1)
            self.assertEqual(
                unsafe[0].detail, "Topic is over-length or has control chars/newlines"
            )

    def test_research_index_consumed_by_over_length(self):
        """research_index.check_drift: Consumed-by is over-length or has control chars/newlines."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rroot = root / ".aw" / "records" / "research"
            rroot.mkdir(parents=True, exist_ok=True)
            doc = rroot / "20261002-test-01-sh0001-doc1.notes.md"
            doc.write_text(
                C.build_frontmatter(
                    id6="sh0001",
                    created="20261002",
                    set_id="test",
                    order="01",
                    topic=["t1"],
                    model=None,
                    kind="notes",
                    status="todo",
                    outcome="none-yet",
                    summary="valid",
                    consumed_by=["x" * 301],
                )
                + "\n\nbody\n",
                encoding="utf-8",
            )
            drifts = I.check_drift(root, rroot)
            unsafe = [d for d in drifts if d.rule == "attention.unsafe-field"]
            self.assertEqual(len(unsafe), 1)
            self.assertEqual(
                unsafe[0].detail,
                "Consumed-by is over-length or has control chars/newlines",
            )

    def test_releases_validate_release_summary_bullet_over_length(self):
        """releases.validate_release: Summary bullet is over-length or has control chars/newlines."""
        text = RecordBuilder().release(
            id6="rel001",
            status="planned",
            version="1.0.0",
            summary="",
            raw_fields={"Summary": "x" * 301},
            text_only=True,
        )
        drift = releases.validate_release(Path("test.release.md"), text)
        unsafe = [d for d in drift if d.rule == "attention.unsafe-field"]
        self.assertEqual(len(unsafe), 1)
        self.assertEqual(
            unsafe[0].detail,
            "Summary bullet is over-length or has control chars/newlines",
        )

    def test_releases_validate_release_summary_prose_control_char(self):
        """releases.validate_release: Summary prose contains control characters."""
        text = RecordBuilder().release(
            id6="rel001",
            status="planned",
            version="1.0.0",
            summary="",
            body="# Release 1.0.0\n\n## Summary\n\nProse with \x07 control char.\n",
            text_only=True,
        )
        drift = releases.validate_release(Path("test.release.md"), text)
        unsafe = [d for d in drift if d.rule == "attention.unsafe-field"]
        self.assertEqual(len(unsafe), 1)
        self.assertEqual(unsafe[0].detail, "Summary prose contains control characters")

    def test_attention_plans_record_dir_vs_status(self):
        """attention._plans_record: dir {disp} vs status {status}."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            pdir = root / ".aw" / "records" / "plans" / "executed"
            pdir.mkdir(parents=True, exist_ok=True)
            p = pdir / "20260101-set-01-p10001-test.ipd.md"
            p.write_text(
                RecordBuilder().plan(
                    title="test",
                    id6="p10001",
                    status="superseded",
                    set="set",
                    order=1,
                    text_only=True,
                ),
                encoding="utf-8",
            )
            items, drift = att.scan(root)
            mismatch = [d for d in drift if d.rule == "attention.disposition-mismatch"]
            self.assertEqual(len(mismatch), 1)
            self.assertEqual(mismatch[0].detail, "dir executed vs status superseded")


class TestEndToEndSubprocess(unittest.TestCase):
    """(c) End-to-end subprocess case (E-02 / F-03).

    python -m agent_workflows.cli attention --check --json --dir <temp repo>
    asserting data.drift[].detail and diagnostics[].detail decode to the single-repr form.
    """

    def test_cli_attention_check_json_backlog_hostile_status(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True, exist_ok=True)
            p = bdir / "20260101-b10001-01-b10001-test.backlog.md"
            p.write_text(
                RecordBuilder().backlog(
                    id6="b10001",
                    priority="high",
                    work_kind="feature",
                    summary="test",
                    raw_fields={"Status": "we\\ird"},
                    text_only=True,
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows.cli",
                    "attention",
                    "--check",
                    "--json",
                    "--dir",
                    str(root),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            payload = json.loads(proc.stdout)

            rel_loc = (
                ".aw/records/backlog/open/20260101-b10001-01-b10001-test.backlog.md"
            )
            drifts = [
                d
                for d in payload.get("data", {}).get("drift", [])
                if d.get("location") == rel_loc
            ]
            self.assertEqual(len(drifts), 1)
            expected = "backlog status " + repr("we\\ird")
            self.assertEqual(drifts[0]["detail"], expected)

            diags = [
                d
                for d in payload.get("diagnostics", [])
                if d.get("location") == rel_loc
            ]
            self.assertEqual(len(diags), 1)
            self.assertEqual(diags[0]["detail"], expected)


if __name__ == "__main__":
    unittest.main()
