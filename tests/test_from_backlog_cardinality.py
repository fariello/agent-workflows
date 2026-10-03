"""Tests for From-Backlog single-valued cardinality enforcement (IPD okp2o4 E-06).

Covers:
  (1) Cross-reader parity matrix over real inputs:
      'dstnso, 8hx3g3', 'dstnso,8hx3g3', sentinels ('-', 'none', 'unresolved', '"-"', 'NONE'),
      and a valid id6 ('dstnso'). Asserts check_engine._from_backlog_value,
      runner_shared._read_from_backlog, production_checks._read_from_backlog, and
      check_engine.build_graduation_reverse_index all agree.
  (2) Multi-bullet preservation: an artifact with two valid-id6 From-Backlog bullets
      remains indexed under both keys in build_graduation_reverse_index.
  (3) Operator surface: check_engine.graduation_cluster attributes no artifact to the junk token.
  (4) Writer idempotency: releases.set_from_backlog_line called twice on text already carrying
      a multi-token value leaves 1 line with clean metadata parse; clearing with '-' removes it.
  (5) Malformed rule reachability: releases.check_from_backlog reports check.from-backlog-malformed
      on spaced and no-space multi-token values and does not report -dangling for them;
      reports -dangling only for well-formed non-existent id6; corpus independence when no
      backlog items exist.
  (6) Regression reproduction of F-1: fixture plan carrying two source ids does not pass
      silently clean; carrier index does not link it and check_from_backlog flags it.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    check_engine,
    ipd_schema,
    production_checks,
    releases,
    runner_shared,
)


def _create_minimal_repo(root: Path) -> Path:
    """Create a minimal conformant repository structure."""
    for p in (
        root / ".aw" / "records" / "releases",
        root / ".aw" / "records" / "backlog" / "open",
        root / ".aw" / "records" / "backlog" / "done",
        root / ".aw" / "records" / "backlog" / "graduated",
        root / ".aw" / "records" / "plans" / "pending",
        root / ".aw" / "records" / "plans" / "executed",
        root / ".aw" / "records" / "specs" / "approved",
    ):
        p.mkdir(parents=True, exist_ok=True)
    return root


class TestFromBacklogCardinality(unittest.TestCase):
    """Behavioral parity and cardinality tests for From-Backlog readers and checkers."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = _create_minimal_repo(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_cross_reader_parity_matrix(self) -> None:
        """Matrix over spaced multi-token, no-space multi-token, sentinels, and valid id6.

        All readers must agree on whether a usable link exists, and build_graduation_reverse_index
        must never index a junk token key.
        """
        cases = [
            ("dstnso, 8hx3g3", False, None),
            ("dstnso,8hx3g3", False, None),
            ("-", False, None),
            ("none", False, None),
            ("unresolved", False, None),
            ('"-"', False, None),
            ("NONE", False, None),
            ("dstnso", True, "dstnso"),
        ]

        for val, is_usable, expected_id in cases:
            with self.subTest(val=val):
                text = (
                    f"# IPD: Test\n\n"
                    f"- Id: tstpln\n"
                    f"- Status: to-review\n"
                    f"- From-Backlog: {val}\n"
                    f"- Set: tstset\n"
                    f"- Scope: Test\n"
                    f"- Scope-Paths: foo.py\n\n"
                    f"## Goal\n"
                )
                plan_file = (
                    self.root
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20260901-tstset-01-tstpln-test.ipd.md"
                )
                plan_file.write_text(text, encoding="utf-8")

                # Reader 1: check_engine._from_backlog_value
                ce_val = check_engine._from_backlog_value(text)
                self.assertEqual(
                    ce_val,
                    expected_id,
                    f"check_engine._from_backlog_value({val!r}) expected {expected_id!r}, got {ce_val!r}",
                )

                # Reader 2: runner_shared._read_from_backlog
                rs_val = runner_shared._read_from_backlog(text)
                self.assertEqual(
                    rs_val,
                    expected_id,
                    f"runner_shared._read_from_backlog({val!r}) expected {expected_id!r}, got {rs_val!r}",
                )

                # Reader 3: production_checks._read_from_backlog
                pc_val = production_checks._read_from_backlog(text)
                self.assertEqual(
                    pc_val,
                    expected_id,
                    f"production_checks._read_from_backlog({val!r}) expected {expected_id!r}, got {pc_val!r}",
                )

                # Reader 4: check_engine.build_graduation_reverse_index
                r_idx = check_engine.build_graduation_reverse_index(self.root)
                if is_usable:
                    self.assertIn(
                        ("backlog", expected_id),
                        r_idx,
                        f"build_graduation_reverse_index missing ('backlog', {expected_id!r})",
                    )
                else:
                    self.assertNotIn(
                        ("backlog", val),
                        r_idx,
                        f"build_graduation_reverse_index indexed junk key ('backlog', {val!r})",
                    )
                    # Specifically ensure comma tokens are not keys
                    self.assertNotIn(("backlog", "dstnso,8hx3g3"), r_idx)
                    self.assertNotIn(("backlog", "dstnso, 8hx3g3"), r_idx)

                # Clean up plan file for next iteration
                plan_file.unlink()

    def test_multi_bullet_preservation(self) -> None:
        """Artifact carrying two valid-id6 From-Backlog bullets indexes under BOTH keys."""
        plan_text = (
            "# IPD: Test Multi Bullet\n\n"
            "- Id: mblt01\n"
            "- Status: to-review\n"
            "- From-Backlog: aaaaaa\n"
            "- From-Backlog: bbbbbb\n"
            "- Set: testset\n"
            "- Scope: Test\n"
            "- Scope-Paths: foo.py\n\n"
            "## Goal\n"
        )
        plan_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260901-testset-01-mblt01-multi.ipd.md"
        )
        plan_file.write_text(plan_text, encoding="utf-8")

        r_idx = check_engine.build_graduation_reverse_index(self.root)
        self.assertIn(
            ("backlog", "aaaaaa"),
            r_idx,
            "build_graduation_reverse_index failed to index first From-Backlog bullet",
        )
        self.assertIn(
            ("backlog", "bbbbbb"),
            r_idx,
            "build_graduation_reverse_index failed to index second From-Backlog bullet",
        )
        self.assertEqual(len(r_idx[("backlog", "aaaaaa")]), 1)
        self.assertEqual(len(r_idx[("backlog", "bbbbbb")]), 1)
        self.assertEqual(r_idx[("backlog", "aaaaaa")][0].id6, "mblt01")
        self.assertEqual(r_idx[("backlog", "bbbbbb")][0].id6, "mblt01")

    def test_operator_surface_graduation_cluster(self) -> None:
        """graduation_cluster attributes no artifact to a junk token on the no-space form."""
        plan_text = (
            "# IPD: Junk Token Test\n\n"
            "- Id: jnktok\n"
            "- Status: to-review\n"
            "- From-Backlog: dstnso,8hx3g3\n"
            "- Set: testset\n"
            "- Scope: Test\n"
            "- Scope-Paths: foo.py\n\n"
            "## Goal\n"
        )
        plan_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260901-testset-01-jnktok-test.ipd.md"
        )
        plan_file.write_text(plan_text, encoding="utf-8")

        cluster_junk = check_engine.graduation_cluster(self.root, "dstnso,8hx3g3")
        self.assertEqual(
            list(cluster_junk.artifacts),
            [],
            "graduation_cluster attributed artifacts to junk token 'dstnso,8hx3g3'",
        )

        cluster_src = check_engine.graduation_cluster(self.root, "dstnso")
        self.assertEqual(
            list(cluster_src.artifacts),
            [],
            "graduation_cluster attributed artifacts to 'dstnso' when link was malformed",
        )

    def test_writer_idempotency_and_metadata_parse(self) -> None:
        """releases.set_from_backlog_line is idempotent on multi-token lines and clears with '-'."""
        text = (
            "# IPD: Writer Test\n\n"
            "- Id: wrtpln\n"
            "- Status: to-review\n"
            "- From-Backlog: aaaaaa, bbbbbb\n"
            "- Set: testset\n"
            "- Scope: Test\n"
            "- Scope-Paths: foo.py\n\n"
            "## Goal\n"
        )
        # First write: overwrite multi-token value with single token
        written_1 = releases.set_from_backlog_line(text, "cccccc")
        self.assertEqual(written_1.count("- From-Backlog:"), 1)
        self.assertIn("- From-Backlog: cccccc", written_1)

        # Second write: overwrite single token with another single token
        written_2 = releases.set_from_backlog_line(written_1, "dddddd")
        self.assertEqual(written_2.count("- From-Backlog:"), 1)
        self.assertIn("- From-Backlog: dddddd", written_2)

        # Verify ipd_schema.parse_metadata_block on metadata lines
        meta_lines = [
            line
            for line in written_2.split("## Goal")[0].splitlines()
            if line.startswith("- ")
        ]
        fields, errors = ipd_schema.parse_metadata_block(meta_lines)
        self.assertEqual(errors, [])
        self.assertEqual(fields.get("From-Backlog"), "dddddd")

        # Verify clearing with '-'
        cleared = releases.set_from_backlog_line(written_2, "-")
        self.assertNotIn("- From-Backlog:", cleared)

    def test_malformed_rule_reachability_and_separation(self) -> None:
        """releases.check_from_backlog reports check.from-backlog-malformed for spaced and no-space

        multi-token values and check.from-backlog-dangling only for valid non-resolving id6.
        """
        # Create one valid backlog item so known corpus is non-empty
        bkl_item = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-bkl001-01-valid1-test.backlog.md"
        )
        bkl_item.write_text(
            "- Id: valid1\n- Status: open\n- Set: bkl001\n- Priority: medium\n- Work-Kind: bug\n",
            encoding="utf-8",
        )

        plans_spec = [
            ("spaced", "aaaaaa, bbbbbb", "check.from-backlog-malformed"),
            ("nospace", "aaaaaa,bbbbbb", "check.from-backlog-malformed"),
            ("dangling", "dddddd", "check.from-backlog-dangling"),
            ("valid", "valid1", None),
            ("sentinel", "-", None),
        ]

        for name, val, expected_rule in plans_spec:
            p_file = (
                self.root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / f"20260901-set001-01-{name[:6]}-test.ipd.md"
            )
            p_file.write_text(
                f"# IPD: {name}\n\n- Id: {name[:6]}\n- Status: to-review\n- From-Backlog: {val}\n- Set: set001\n",
                encoding="utf-8",
            )

        findings = releases.check_from_backlog(self.root)
        rules_by_loc = {Path(f.location).name: f.rule for f in findings}

        # spaced -> malformed, not dangling
        self.assertEqual(
            rules_by_loc.get("20260901-set001-01-spaced-test.ipd.md"),
            "check.from-backlog-malformed",
        )
        # nospace -> malformed, not dangling
        self.assertEqual(
            rules_by_loc.get("20260901-set001-01-nospac-test.ipd.md"),
            "check.from-backlog-malformed",
        )
        # dangling -> dangling, not malformed
        self.assertEqual(
            rules_by_loc.get("20260901-set001-01-dangli-test.ipd.md"),
            "check.from-backlog-dangling",
        )
        # valid and sentinel -> no findings
        self.assertNotIn("20260901-set001-01-valid-test.ipd.md", rules_by_loc)
        self.assertNotIn("20260901-set001-01-sentin-test.ipd.md", rules_by_loc)

    def test_malformed_rule_corpus_independence(self) -> None:
        """check.from-backlog-malformed fires even when the backlog corpus is completely empty."""
        plan_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260901-set001-01-malf01-test.ipd.md"
        )
        plan_file.write_text(
            "# IPD: Malformed\n\n- Id: malf01\n- Status: to-review\n- From-Backlog: aaaaaa, bbbbbb\n- Set: set001\n",
            encoding="utf-8",
        )

        findings = releases.check_from_backlog(self.root)
        malformed = [f for f in findings if f.rule == "check.from-backlog-malformed"]
        self.assertEqual(len(malformed), 1)
        self.assertEqual(
            Path(malformed[0].location).name, "20260901-set001-01-malf01-test.ipd.md"
        )

    def test_regression_reproduction_f1(self) -> None:
        """F-1 reproduction: plan carrying two source ids is not silently ignored.

        _from_backlog_carrier_index does not index it as a carrier, and check_from_backlog
        flags it as check.from-backlog-malformed.
        """
        # Create two source items
        for item_id, status in [("dstnso", "done"), ("8hx3g3", "open")]:
            target_dir = (
                self.root
                / ".aw"
                / "records"
                / "backlog"
                / ("done" if status == "done" else "open")
            )
            f = target_dir / f"20260901-bkl001-01-{item_id}-item.backlog.md"
            f.write_text(
                f"- Id: {item_id}\n- Status: {status}\n- Set: bkl001\n- Priority: high\n- Work-Kind: bug\n- Blocks-Release: next\n",
                encoding="utf-8",
            )

        plan_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260917-test01-01-plnf01-test.ipd.md"
        )
        plan_file.write_text(
            "# IPD: Two sources\n\n"
            "- Id: plnf01\n"
            "- Status: pending\n"
            "- From-Backlog: dstnso, 8hx3g3\n"
            "- Set: test01\n"
            "- Blocks-Release: next\n"
            "- Scope: Test\n"
            "- Scope-Paths: foo.py\n\n"
            "## Goal\n",
            encoding="utf-8",
        )

        # Carrier index does NOT map dstnso or 8hx3g3 to this plan
        c_idx = check_engine._from_backlog_carrier_index(self.root)
        self.assertNotIn("dstnso", c_idx)
        self.assertNotIn("8hx3g3", c_idx)

        # Evaluating close legitimacy on 8hx3g3 fails (not closed by carrier)
        item_path = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-bkl001-01-8hx3g3-item.backlog.md"
        )
        verdict = check_engine.evaluate_blocking_close(self.root, item_path, "done")
        self.assertFalse(verdict.legitimate)

        # But crucially: check_from_backlog does NOT remain silent
        findings = releases.check_from_backlog(self.root)
        malformed = [f for f in findings if f.rule == "check.from-backlog-malformed"]
        self.assertEqual(len(malformed), 1)
        self.assertEqual(
            Path(malformed[0].location).name, "20260917-test01-01-plnf01-test.ipd.md"
        )


if __name__ == "__main__":
    unittest.main()
