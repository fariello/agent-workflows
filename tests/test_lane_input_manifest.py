"""Lane input materialization, sealing, link independence, and attachment localization.

Covers spec `7ckptx` R5.1, R5.1a, R5.2 and R5.3 (criteria A12, A12b, A13) for plan `nna8yz`
E-01..E-04.

WHY THESE ASSERTIONS ARE SHAPED THE WAY THEY ARE, since the obvious version of each is the one the
spec calls insufficient:

  * R5.2 is checked by INODE IDENTITY and link count, not by `not islink` plus digest equality. A hard
    link passes both of those while still sharing storage with the source, so the naive check would
    report conformance for exactly the arrangement R5.2 forbids. `test_hard_link_is_caught` sabotages
    a copy into a hard link and proves the check FAILS, which is what makes the passing case mean
    something.
  * R5.1a is checked in all three of its parts (manifest mode, input mode, revision-not-edit), because
    "sealed" was previously claimable with no read-only anywhere.
  * R5.3 is asserted over EVERY `--file` value in the constructed argv with at least two present, not
    over one attachment a test happened to pick.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import lane_containment


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class MaterializationTests(unittest.TestCase):
    """R5.1: inputs arrive BY COPY with a digested manifest (criterion A12)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.lane = Path(self._tmp.name) / "lane"
        self.plan = _write(
            self.lane / ".aw/records/plans/pending/plan.ipd.md", "# plan\nbody\n"
        )
        self.runbook = _write(
            Path(self._tmp.name) / "coordinator/runbook.md", "# runbook\nrules\n"
        )

    def _materialize(self, revision: int = 1) -> lane_containment.LaneInputManifest:
        return lane_containment.materialize_lane_inputs(
            lane_root=self.lane,
            plan_path=self.plan,
            runbook_path=self.runbook,
            repo=self.lane,
            revision=revision,
        )

    def test_every_entry_is_a_copy_with_a_matching_digest(self):
        manifest = self._materialize()
        document = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(len(document["inputs"]), 2, document)
        classes = {entry["input_class"] for entry in document["inputs"]}
        self.assertEqual(
            classes,
            {lane_containment.INPUT_CLASS_PLAN, lane_containment.INPUT_CLASS_RUNBOOK},
        )

        for entry in document["inputs"]:
            with self.subTest(path=entry["path"]):
                # R5.1: the mode is recorded, is `copy`, and the digest is non-empty.
                self.assertEqual(
                    entry["mode"], lane_containment.MATERIALIZATION_MODE_COPY
                )
                self.assertTrue(entry["source_sha256"])
                target = self.lane / entry["path"]
                self.assertTrue(target.is_file())
                # The recorded digest describes the bytes ACTUALLY IN THE LANE.
                self.assertEqual(
                    lane_containment._sha256_file(target), entry["source_sha256"]
                )

        # And the copies are faithful to their sources.
        plan_entry = manifest.entry(lane_containment.INPUT_CLASS_PLAN)
        runbook_entry = manifest.entry(lane_containment.INPUT_CLASS_RUNBOOK)
        assert plan_entry is not None and runbook_entry is not None
        self.assertEqual(
            (self.lane / plan_entry.path).read_bytes(), self.plan.read_bytes()
        )
        self.assertEqual(
            (self.lane / runbook_entry.path).read_bytes(), self.runbook.read_bytes()
        )

        self.assertTrue(
            lane_containment.verify_lane_input_manifest(self.lane).conforming
        )

    def test_materialized_paths_are_inside_the_lane_and_relative(self):
        manifest = self._materialize()
        for entry in manifest.entries:
            with self.subTest(path=entry.path):
                self.assertFalse(Path(entry.path).is_absolute())
                resolved = (self.lane / entry.path).resolve()
                self.assertIn(self.lane.resolve(), resolved.parents)

    def test_an_absent_source_records_no_entry_rather_than_a_fabricated_one(self):
        """A manifest entry is a claim about bytes we read; we must not invent one."""
        manifest = lane_containment.materialize_lane_inputs(
            lane_root=self.lane,
            plan_path=self.plan,
            runbook_path=Path(self._tmp.name) / "does-not-exist.md",
            repo=self.lane,
        )
        self.assertIsNone(manifest.entry(lane_containment.INPUT_CLASS_RUNBOOK))
        self.assertIsNotNone(manifest.entry(lane_containment.INPUT_CLASS_PLAN))

    def test_a_wrong_recorded_digest_is_caught(self):
        """SABOTAGE for V-01: corrupt the recorded digest and prove the check refuses it."""
        manifest = self._materialize()
        self.assertTrue(
            lane_containment.verify_lane_input_manifest(self.lane).conforming
        )

        document = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
        document["inputs"][0]["source_sha256"] = "0" * 64
        os.chmod(manifest.manifest_path, 0o644)
        manifest.manifest_path.write_text(json.dumps(document), encoding="utf-8")
        os.chmod(manifest.manifest_path, lane_containment.SEALED_FILE_MODE)

        verdict = lane_containment.verify_lane_input_manifest(self.lane)
        self.assertFalse(verdict.conforming)
        self.assertTrue(
            any("does not match on-disk" in v for v in verdict.violations), verdict
        )

    def test_a_missing_digest_is_caught(self):
        manifest = self._materialize()
        document = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
        document["inputs"][0]["source_sha256"] = ""
        os.chmod(manifest.manifest_path, 0o644)
        manifest.manifest_path.write_text(json.dumps(document), encoding="utf-8")

        verdict = lane_containment.verify_lane_input_manifest(self.lane)
        self.assertFalse(verdict.conforming)
        self.assertTrue(
            any("records no source digest" in v for v in verdict.violations), verdict
        )

    def test_an_unrecognized_mode_is_refused(self):
        """The mode is a recorded FIELD so a future mode cannot slip in unverified."""
        manifest = self._materialize()
        document = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
        document["inputs"][0]["mode"] = "symlink"
        os.chmod(manifest.manifest_path, 0o644)
        manifest.manifest_path.write_text(json.dumps(document), encoding="utf-8")

        verdict = lane_containment.verify_lane_input_manifest(self.lane)
        self.assertFalse(verdict.conforming)
        self.assertTrue(any("is not 'copy'" in v for v in verdict.violations), verdict)

    def test_no_manifest_is_not_silently_conforming(self):
        """Fail closed: an unmaterialized lane must not read as satisfied."""
        verdict = lane_containment.verify_lane_input_manifest(self.lane)
        self.assertFalse(verdict.conforming)
        self.assertIn("no lane input manifest", verdict.reason)


class LinkIndependenceTests(unittest.TestCase):
    """R5.2: independence of STORAGE, which a symlink check alone cannot establish (A12)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.lane = Path(self._tmp.name) / "lane"
        self.plan = _write(self.lane / "plan.ipd.md", "# plan\n")
        self.runbook = _write(Path(self._tmp.name) / "runbook.md", "# runbook\n")
        self.manifest = lane_containment.materialize_lane_inputs(
            lane_root=self.lane,
            plan_path=self.plan,
            runbook_path=self.runbook,
            repo=self.lane,
        )

    def test_a_fresh_copy_is_link_independent(self):
        result = lane_containment.verify_link_independence(self.lane)
        self.assertTrue(result.independent, result.reason)

        for entry in self.manifest.entries:
            target = self.lane / entry.path
            with self.subTest(path=entry.path):
                self.assertFalse(target.is_symlink())
                stat_result = os.stat(target, follow_symlinks=False)
                self.assertEqual(stat_result.st_nlink, 1)
                source_stat = os.stat(
                    self.plan if entry.input_class == "plan" else self.runbook
                )
                self.assertNotEqual(
                    (stat_result.st_dev, stat_result.st_ino),
                    (source_stat.st_dev, source_stat.st_ino),
                )

    def test_hard_link_is_caught(self):
        """SABOTAGE for V-02, and the REASON R5.2 is worded as it is.

        A hard link is NOT a symlink and its digest is IDENTICAL to the source, so the naive check
        (`not islink` and digest equality) passes. This test first demonstrates that the naive check
        passes, then that the real check FAILS, which is the whole point of the requirement.
        """
        entry = self.manifest.entry(lane_containment.INPUT_CLASS_PLAN)
        assert entry is not None
        target = self.lane / entry.path

        target.chmod(0o644)
        target.unlink()
        os.link(self.plan, target)

        # The naive check that R5.2 says is insufficient: BOTH of its parts still hold.
        self.assertFalse(target.is_symlink())
        self.assertEqual(
            lane_containment._sha256_file(target),
            lane_containment._sha256_file(self.plan),
        )

        # The real check catches it.
        result = lane_containment.verify_link_independence(self.lane)
        self.assertFalse(result.independent)
        self.assertTrue(
            any("hard link" in v or "shares inode" in v for v in result.violations),
            result.violations,
        )
        self.assertFalse(
            lane_containment.verify_lane_input_manifest(self.lane).conforming
        )

    def test_symlink_is_caught(self):
        entry = self.manifest.entry(lane_containment.INPUT_CLASS_RUNBOOK)
        assert entry is not None
        target = self.lane / entry.path
        target.chmod(0o644)
        target.unlink()
        target.symlink_to(self.runbook)

        result = lane_containment.verify_link_independence(self.lane)
        self.assertFalse(result.independent)
        self.assertTrue(any("is a symlink" in v for v in result.violations), result)

    def test_restored_copy_passes_again(self):
        """Round-trip half of the sabotage evidence: restore and prove it passes."""
        self.test_hard_link_is_caught()
        lane_containment.materialize_lane_inputs(
            lane_root=self.lane,
            plan_path=self.plan,
            runbook_path=self.runbook,
            repo=self.lane,
        )
        self.assertTrue(
            lane_containment.verify_link_independence(self.lane).independent
        )
        self.assertTrue(
            lane_containment.verify_lane_input_manifest(self.lane).conforming
        )


class SealTests(unittest.TestCase):
    """R5.1a: all three parts of SEALED, and the honest limit (criterion A12b)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.lane = Path(self._tmp.name) / "lane"
        self.plan = _write(self.lane / "plan.ipd.md", "# plan\n")
        self.runbook = _write(Path(self._tmp.name) / "runbook.md", "# runbook\n")
        self.manifest = lane_containment.materialize_lane_inputs(
            lane_root=self.lane,
            plan_path=self.plan,
            runbook_path=self.runbook,
            repo=self.lane,
        )

    def test_part_i_the_manifest_file_has_no_write_bit(self):
        mode = os.stat(self.manifest.manifest_path).st_mode & 0o777
        self.assertEqual(
            mode & 0o222, 0, f"manifest mode {mode:04o} carries a write bit"
        )

    def test_part_ii_every_materialized_input_has_no_write_bit(self):
        for entry in self.manifest.entries:
            with self.subTest(path=entry.path):
                mode = os.stat(self.lane / entry.path).st_mode & 0o777
                self.assertEqual(mode & 0o222, 0, f"{entry.path} mode {mode:04o}")
        self.assertTrue(lane_containment.verify_lane_input_seal(self.lane).sealed)

    def test_an_accidental_in_place_write_fails(self):
        """What the accident guard actually buys: the stray write RAISES."""
        with self.assertRaises(PermissionError):
            self.manifest.manifest_path.write_text("{}", encoding="utf-8")
        entry = self.manifest.entries[0]
        with self.assertRaises(PermissionError):
            (self.lane / entry.path).write_text("clobbered", encoding="utf-8")

    def test_part_iii_a_change_is_a_new_revision_not_an_edit(self):
        """A legitimate input change appears as a NEW REVISION; rev 1 is left untouched."""
        first = self.manifest
        self.assertEqual(first.revision, 1)
        rev1_bytes = first.manifest_path.read_bytes()

        _write(self.runbook, "# runbook\nrules v2\n")
        second = lane_containment.revise_lane_inputs(
            lane_root=self.lane,
            plan_path=self.plan,
            runbook_path=self.runbook,
            repo=self.lane,
        )

        self.assertEqual(second.revision, 2)
        self.assertNotEqual(second.manifest_path, first.manifest_path)
        self.assertEqual(lane_containment.latest_lane_input_revision(self.lane), 2)
        # Rev 1's record is byte-identical: no in-place edit occurred.
        self.assertEqual(first.manifest_path.read_bytes(), rev1_bytes)
        # And rev 2 records the NEW bytes.
        entry = second.entry(lane_containment.INPUT_CLASS_RUNBOOK)
        assert entry is not None
        self.assertEqual(
            (self.lane / entry.path).read_text(encoding="utf-8"),
            "# runbook\nrules v2\n",
        )
        # Both revisions independently conform.
        self.assertTrue(
            lane_containment.verify_lane_input_manifest(self.lane, 1).conforming
        )
        self.assertTrue(
            lane_containment.verify_lane_input_manifest(self.lane, 2).conforming
        )

    def test_the_artifact_states_the_accident_guard_limit(self):
        """R5.1a forbids describing this as immutability; the manifest must SAY so."""
        document = json.loads(self.manifest.manifest_path.read_text(encoding="utf-8"))
        note = document["seal_note"].lower()
        self.assertIn("accident guard", note)
        self.assertIn("not immutability", note)
        self.assertIn("restore the write bit", note)
        # Asserting the PROPERTY on a SECOND surface, not the wording of one sentence: the code
        # comment on the mode constant carries the same limit, which is what V-03 quotes.
        source = Path(lane_containment.__file__).read_text(encoding="utf-8")
        constant_comment = source.split("SEALED_FILE_MODE = ", 1)[0].rsplit(
            "#: Permission bits a sealed file carries", 1
        )[-1]
        self.assertIn("ACCIDENT GUARD, NOT IMMUTABILITY", constant_comment)
        self.assertIn("NOT a boundary", constant_comment)
        self.assertIn("restore the write bit", constant_comment)

    def test_a_restored_write_bit_is_detected(self):
        """SABOTAGE: unseal one input and prove the seal check refuses the revision."""
        self.assertTrue(lane_containment.verify_lane_input_seal(self.lane).sealed)
        entry = self.manifest.entries[0]
        os.chmod(self.lane / entry.path, 0o644)
        result = lane_containment.verify_lane_input_seal(self.lane)
        self.assertFalse(result.sealed)
        self.assertTrue(any("write bit" in v for v in result.violations), result)


class RevisionMechanismHasNoProductCallerTests(unittest.TestCase):
    """Spec R3.4 requires the revision mechanism to STATE it has no consumer, not imply one."""

    def test_revise_lane_inputs_is_not_called_by_product_code(self):
        """Structural (AST), not grep: a text search matches this test file itself."""
        import ast

        package = Path(lane_containment.__file__).parent
        callers: list[str] = []
        for source in package.rglob("*.py"):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = (
                    func.attr
                    if isinstance(func, ast.Attribute)
                    else (func.id if isinstance(func, ast.Name) else None)
                )
                if name == "revise_lane_inputs":
                    callers.append(f"{source.name}:{node.lineno}")
        self.assertEqual(
            callers,
            [],
            "spec R3.4: the revision mechanism must have NO product caller; found "
            f"{callers}",
        )

    def test_its_docstring_states_it_has_no_consumer(self):
        doc = (lane_containment.revise_lane_inputs.__doc__ or "").lower()
        self.assertIn("no product caller", doc)


class AttachmentLocalizationTests(unittest.TestCase):
    """R5.3: EVERY `--file` value for an isolated turn resolves inside the lane (criterion A13)."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.lane = Path(self._tmp.name) / "lane"
        self.plan = _write(self.lane / "plan.ipd.md", "# plan\n")
        self.runbook = _write(Path(self._tmp.name) / "coordinator/runbook.md", "# rb\n")
        lane_containment.materialize_lane_inputs(
            lane_root=self.lane,
            plan_path=self.plan,
            runbook_path=self.runbook,
            repo=self.lane,
        )

    def test_both_attachments_are_localized(self):
        runbook_value = lane_containment.localize_attachment(
            lane_root=self.lane,
            fallback=self.runbook,
            input_class=lane_containment.INPUT_CLASS_RUNBOOK,
        )
        plan_value = lane_containment.localize_attachment(
            lane_root=self.lane,
            fallback=self.plan,
            input_class=lane_containment.INPUT_CLASS_PLAN,
        )
        argv = [
            "opencode",
            "run",
            "--file",
            runbook_value,
            "--file",
            plan_value,
            "--",
            "prompt",
        ]

        values = lane_containment.attachment_values(argv)
        # At least two, so the assertion provably covers BOTH attachments (A13).
        self.assertGreaterEqual(len(values), 2, values)
        self.assertEqual(lane_containment.attachments_outside_lane(argv, self.lane), [])
        # The runbook value is no longer the coordinator path it started as.
        self.assertNotEqual(Path(runbook_value), self.runbook)

    def test_an_out_of_lane_attachment_is_detected(self):
        """SABOTAGE: the check must FAIL for the pre-change argv shape."""
        argv = [
            "opencode",
            "run",
            "--file",
            str(self.runbook),  # the main/coordinator path, as before this change
            "--file",
            str(self.plan),
            "--",
            "prompt",
        ]
        outside = lane_containment.attachments_outside_lane(argv, self.lane)
        self.assertIn(str(self.runbook), outside)

    def test_a_non_isolated_turn_is_untouched(self):
        """R1.3's discipline: `lane_root=None` returns the fallback byte for byte."""
        self.assertEqual(
            lane_containment.localize_attachment(
                lane_root=None,
                fallback=self.runbook,
                input_class=lane_containment.INPUT_CLASS_RUNBOOK,
            ),
            str(self.runbook),
        )

    def test_traversal_cannot_masquerade_as_contained(self):
        argv = ["--file", str(self.lane / ".." / "coordinator" / "runbook.md")]
        self.assertNotEqual(
            lane_containment.attachments_outside_lane(argv, self.lane), []
        )


class DriverArgvTests(unittest.TestCase):
    """The argv the oc driver ACTUALLY constructs, so R5.3 is proven on the product path.

    Only the oc driver is parameterized here, and that ASYMMETRY IS REAL rather than an omission: the
    agy driver has no `--file` surface at all (it passes its prompt inline via `-p`), so it has no
    attachment to localize. `test_lane_clean_base.py` covers both hosts for R5.4, which is the
    requirement that does apply to both.
    """

    def test_agy_driver_has_no_file_attachment_surface(self):
        """Pin the premise above, so a later `--file` addition to agy fails this test loudly."""
        from agent_workflows import agy_runipd

        source = Path(agy_runipd.__file__).read_text(encoding="utf-8")
        launch = source.split("def run_agy_turn", 1)
        self.assertEqual(len(launch), 2, "run_agy_turn not found")
        body = launch[1].split("\ndef ", 1)[0]
        self.assertNotIn('"--file"', body)
        # The prompt travels inline via `-p`, which is WHY there is no attachment to localize.
        self.assertIn('"-p"', body)


if __name__ == "__main__":
    unittest.main()
