"""Tests for unsafe descriptive field validation in research index (attention.unsafe-field).

Pins Section 8.8 bounded descriptive field requirements for research artifacts
(summary, topic tokens, consumed-by tokens).
Also pins the non-destruction property (F-06: doc remains indexed, never dropped),
honest limits (newline injection F-05 and no sanitization), and non-regressions.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import check_engine
from agent_workflows import research_cmd as C
from agent_workflows import research_contract as R
from agent_workflows import research_index as I

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestResearchUnsafeField(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / ".aw" / "records" / "research"
        self.rroot.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _regen(self):
        entries, _ = I._scan_docs(self.rroot, repo_root=self.root)
        (self.rroot / I.INDEX_JSON).write_text(
            I.build_index_json(entries), encoding="utf-8"
        )
        (self.rroot / I.INDEX_MD).write_text(
            I.build_index_md(entries), encoding="utf-8"
        )

    def _write_doc(
        self,
        id6: str = "abc001",
        slug: str = "test-doc",
        summary: str = "Valid summary",
        topic: list[str] | None = None,
        consumed_by: list[str] | None = None,
        extra_fm_lines: list[str] | None = None,
        body: str = "Body text",
        custom_frontmatter: str | None = None,
    ) -> Path:
        name = R.format_name(
            R.ResearchName(
                date="20261002",
                set_id="test",
                order="01",
                id6=id6,
                slug=slug,
                model=None,
                kind="notes",
            )
        )
        doc_path = self.rroot / name
        if custom_frontmatter is not None:
            raw = custom_frontmatter + (f"\n\n{body}\n" if body else "\n")
        else:
            base_fm = C.build_frontmatter(
                id6=id6,
                created="20261002",
                set_id="test",
                order="01",
                topic=topic if topic is not None else ["t1"],
                model=None,
                kind="notes",
                status="todo",
                outcome="none-yet",
                summary=summary,
                consumed_by=consumed_by if consumed_by is not None else [],
            )
            if extra_fm_lines:
                lines = base_fm.splitlines()
                injected = lines[:-1] + extra_fm_lines + ["---"]
                raw = "\n".join(injected) + (f"\n\n{body}\n" if body else "\n")
            else:
                raw = base_fm + (f"\n\n{body}\n" if body else "\n")
        doc_path.write_text(raw, encoding="utf-8")
        return doc_path

    def test_summary_unsafe_shapes(self):
        shapes = {
            "over-length": "x" * 301,
            "bel-control": "sum\x07value",
            "ansi-esc": "sum\x1b[31minjected\x1b[0m",
            "c1-control": "sum\x90value",
        }
        for shape_name, val in shapes.items():
            # Clear fixture directory for clean isolated check
            shutil.rmtree(self.rroot, ignore_errors=True)
            self.rroot.mkdir(parents=True, exist_ok=True)
            doc_path = self._write_doc(id6="sh0001", summary=val)
            self._regen()

            # F-06: Non-destruction property - entries list must still contain doc
            entries, scan_drift = I._scan_docs(self.rroot, repo_root=self.root)
            self.assertEqual(
                len(entries),
                1,
                f"Doc with {shape_name} summary must remain indexed (F-06)",
            )
            self.assertEqual(entries[0].id6, "sh0001")
            self.assertNotIn("frontmatter-invalid", [d.rule for d in scan_drift])

            # Contract function validate_frontmatter returns [] for unsafe summary (placement in check_drift)
            fm = R.parse_frontmatter(doc_path.read_text(encoding="utf-8"))
            self.assertEqual(
                R.validate_frontmatter(fm),
                [],
                "validate_frontmatter must remain unchanged",
            )

            # Check drift emits attention.unsafe-field with severity error
            drifts = I.check_drift(self.root, self.rroot)
            unsafe_drifts = [d for d in drifts if d.rule == "attention.unsafe-field"]
            self.assertEqual(
                len(unsafe_drifts),
                1,
                f"Summary {shape_name} should yield exactly one attention.unsafe-field, got {[d.rule for d in drifts]}",
            )
            d = unsafe_drifts[0]
            self.assertEqual(d.severity, "error")
            self.assertIn("Summary", d.detail)
            # Detail must not echo the untrusted value or raw control bytes (OQ-04)
            self.assertNotIn(val, d.detail)
            self.assertNotIn("\x07", d.detail)
            self.assertNotIn("\x1b", d.detail)
            self.assertNotIn("\x90", d.detail)

    def test_summary_boundary_300_and_301(self):
        # 300 characters is conforming
        self._write_doc(id6="bnd300", summary="x" * 300)
        self._regen()
        drifts_300 = I.check_drift(self.root, self.rroot)
        unsafe_300 = [d for d in drifts_300 if d.rule == "attention.unsafe-field"]
        self.assertEqual(
            unsafe_300, [], "300-char summary must not yield attention.unsafe-field"
        )

        # 301 characters is refused
        shutil.rmtree(self.rroot, ignore_errors=True)
        self.rroot.mkdir(parents=True, exist_ok=True)
        self._write_doc(id6="bnd301", summary="x" * 301)
        self._regen()
        drifts_301 = I.check_drift(self.root, self.rroot)
        unsafe_301 = [d for d in drifts_301 if d.rule == "attention.unsafe-field"]
        self.assertEqual(
            len(unsafe_301), 1, "301-char summary must yield attention.unsafe-field"
        )
        self.assertEqual(unsafe_301[0].severity, "error")

    def test_topic_token_unsafe_shape(self):
        self._write_doc(id6="top001", topic=["valid-token", "topic\x07control"])
        self._regen()
        entries, scan_drift = I._scan_docs(self.rroot, repo_root=self.root)
        self.assertEqual(
            len(entries), 1, "Doc with unsafe topic token must remain indexed (F-06)"
        )
        self.assertNotIn("frontmatter-invalid", [d.rule for d in scan_drift])

        drifts = I.check_drift(self.root, self.rroot)
        unsafe_drifts = [d for d in drifts if d.rule == "attention.unsafe-field"]
        self.assertEqual(len(unsafe_drifts), 1)
        self.assertEqual(unsafe_drifts[0].severity, "error")
        self.assertIn("Topic", unsafe_drifts[0].detail)
        self.assertNotIn("\x07", unsafe_drifts[0].detail)

    def test_consumed_by_token_unsafe_shape(self):
        self._write_doc(id6="con001", consumed_by=["c\x1b[31mbad\x1b[0m"])
        self._regen()
        entries, scan_drift = I._scan_docs(self.rroot, repo_root=self.root)
        self.assertEqual(
            len(entries),
            1,
            "Doc with unsafe consumed-by token must remain indexed (F-06)",
        )
        self.assertNotIn("frontmatter-invalid", [d.rule for d in scan_drift])

        drifts = I.check_drift(self.root, self.rroot)
        unsafe_drifts = [d for d in drifts if d.rule == "attention.unsafe-field"]
        self.assertEqual(len(unsafe_drifts), 1)
        self.assertEqual(unsafe_drifts[0].severity, "error")
        self.assertIn("Consumed-by", unsafe_drifts[0].detail)
        self.assertNotIn("\x1b", unsafe_drifts[0].detail)

    def test_rule_registry_entry(self):
        spec = check_engine.rule_spec("attention.unsafe-field")
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.assurance, check_engine.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, check_engine.DET_DETERMINISTIC)
        self.assertEqual(spec.invariant, "")
        self.assertIn("attention.unsafe-field", check_engine.RULE_REGISTRY)

    def test_limit_one_newline_injection_and_last_wins(self):
        # LIMIT ONE (F-05): A research doc produced by newline injection.
        # Carrier deftzy closes the write path. A checker cannot see the unsplit text.
        # Executed plan jnpl08 catches repeated status key, but unreported blocks-release remains.
        injected_block = (
            "---\n"
            "id: nl0001\n"
            "created: 20261002\n"
            "set: test\n"
            "order: 01\n"
            "topic: [t1]\n"
            "model: gpt56\n"
            "kind: notes\n"
            "status: todo\n"
            "summary: legit\n"
            "status: reference\n"
            "blocks-release: next\n"
            "outcome: none-yet\n"
            "consumed-by: []\n"
            "---"
        )
        doc_path = self._write_doc(id6="nl0001", custom_frontmatter=injected_block)
        self._regen()

        raw_text = doc_path.read_text(encoding="utf-8")
        fm = R.parse_frontmatter(raw_text)

        # parse_frontmatter splits line-by-line; summary is clean
        self.assertEqual(fm.get("summary"), "legit")
        self.assertTrue(A.is_safe_descriptive(fm.get("summary")))
        self.assertEqual(R.validate_frontmatter(fm), [])

        # Last-wins override: smuggled status: reference overrides status: todo
        self.assertEqual(fm.get("status"), "reference")
        self.assertEqual(fm.get("blocks-release"), "next")

        drifts = I.check_drift(self.root, self.rroot)
        rules = [d.rule for d in drifts]

        # 1. NO attention.unsafe-field drift
        self.assertNotIn("attention.unsafe-field", rules)
        # 2. Exactly one research.frontmatter-key-repeated drift naming status
        repeated = [d for d in drifts if d.rule == "research.frontmatter-key-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertIn("status", repeated[0].detail)
        # 3. NO drift of any rule naming blocks-release
        self.assertFalse(any("blocks-release" in d.detail for d in drifts))

        entries, _ = I._scan_docs(self.rroot, repo_root=self.root)
        self.assertEqual(len(entries), 1, "Doc remains indexed")

    def test_limit_two_no_sanitization_bytes_unchanged(self):
        # LIMIT TWO: check_drift reports but does NOT sanitize (carrier llnvwj handles rendering)
        unsafe_val = "sum\x1b[31minjected\x1b[0m"
        doc_path = self._write_doc(id6="san001", summary=unsafe_val)
        self._regen()

        bytes_before = doc_path.read_bytes()
        I.check_drift(self.root, self.rroot)
        bytes_after = doc_path.read_bytes()

        self.assertEqual(
            bytes_before, bytes_after, "check_drift must leave file bytes unchanged"
        )
        entries, _ = I._scan_docs(self.rroot, repo_root=self.root)
        self.assertEqual(
            entries[0].summary, unsafe_val, "Index entry carries exact unchanged value"
        )

    def test_non_regression_live_research_tree_clean(self):
        # Repaired research tree in repository produces ZERO attention.unsafe-field findings
        live_rroot = REPO_ROOT / ".aw" / "records" / "research"
        drifts = I.check_drift(REPO_ROOT, live_rroot, limit=1000)
        unsafe = [d for d in drifts if d.rule == "attention.unsafe-field"]
        self.assertEqual(
            unsafe,
            [],
            f"Live research tree must have 0 attention.unsafe-field findings, got {unsafe}",
        )

    def test_non_regression_existing_four_drift_rules(self):
        # 1. adopted-without-consumer
        self._write_doc(id6="adp001", slug="adopted-no-consumer")
        # Update frontmatter to outcome: adopted and consumed-by: []
        p = self.rroot / "20261002-test-01-adp001-adopted-no-consumer.notes.md"
        p.write_text(
            C.build_frontmatter(
                id6="adp001",
                created="20261002",
                set_id="test",
                order="01",
                topic=["t1"],
                model=None,
                kind="notes",
                status="reference",
                outcome="adopted",
                summary="Adopted summary",
                consumed_by=[],
            )
            + "\n\nBody\n",
            encoding="utf-8",
        )
        self._regen()
        drifts = I.check_drift(self.root, self.rroot)
        self.assertIn("adopted-without-consumer", [d.rule for d in drifts])

        # 2. dangling-consumed-by
        shutil.rmtree(self.rroot, ignore_errors=True)
        self.rroot.mkdir(parents=True, exist_ok=True)
        self._write_doc(id6="dng001", consumed_by=["nonexistent123"])
        self._regen()
        drifts = I.check_drift(self.root, self.rroot)
        self.assertIn("dangling-consumed-by", [d.rule for d in drifts])

        # 3. unrecognized-model
        shutil.rmtree(self.rroot, ignore_errors=True)
        self.rroot.mkdir(parents=True, exist_ok=True)
        p = self.rroot / "20261002-test-01-mod001-unrecognized-model.notes.md"
        p.write_text(
            C.build_frontmatter(
                id6="mod001",
                created="20261002",
                set_id="test",
                order="01",
                topic=["t1"],
                model="completely-unrecognized-model-xyz",
                kind="notes",
                status="todo",
                outcome="none-yet",
                summary="Model test summary",
                consumed_by=[],
            )
            + "\n\nBody\n",
            encoding="utf-8",
        )
        self._regen()
        drifts = I.check_drift(self.root, self.rroot)
        self.assertIn("unrecognized-model", [d.rule for d in drifts])

    def test_non_regression_empty_lists_no_fault(self):
        self._write_doc(id6="emp001", topic=[], consumed_by=[])
        self._regen()
        drifts = I.check_drift(self.root, self.rroot)
        unsafe = [d for d in drifts if d.rule == "attention.unsafe-field"]
        self.assertEqual(unsafe, [])

    def test_non_regression_validate_frontmatter_unchanged(self):
        fm = {
            "id": "tst001",
            "created": "20261002",
            "set": "test",
            "order": "01",
            "topic": ["t1"],
            "model": "gpt56",
            "kind": "notes",
            "status": "todo",
            "outcome": "none-yet",
            "summary": "x" * 301,
            "consumed-by": [],
        }
        self.assertEqual(
            R.validate_frontmatter(fm),
            [],
            "validate_frontmatter does not validate summary safety; check_drift owns the rule",
        )
