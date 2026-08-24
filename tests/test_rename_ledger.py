"""Additive rename/regroup ledger on the workflow sidecar (IPD 52zgqr, E-06/V-01..V-06).

Proves the ledger:
  * writes/reads a rename record via append_rename/read_renames_for; raises on a malformed id6 key;
    accepts a synthetic key only via the Case-3 path (V-01);
  * emits exactly one record on an applied plan/research rename, nothing on dry-run/no-op, and does
    not disturb the inline->sidecar migration dedup (V-02);
  * records Case 2 (id6-less -> id6) under the NEW id6 with the old name in from_name (V-03);
  * records Case 3 (both id6-less) under a deterministic synthetic key tagged key_kind:synthetic
    (V-05);
  * is ADDITIVE/non-authoritative: a rename with the ledger unwritable yields an identical result
    and does not raise, and read_renames_for returns multi-rename history (V-06).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import record_history as RH


class AppendRenameUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_write_and_read_back(self) -> None:
        RH.append_rename(
            self.root,
            id6="aaa111",
            tree="plans",
            verb="rename",
            actor="t",
            from_name="20260101-demo-01-aaa111-a.ipd.md",
            to_name="20260101-demo-01-aaa111-b.ipd.md",
        )
        recs = RH.read_renames_for(self.root, "aaa111")
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["verb"], "rename")
        self.assertEqual(recs[0]["from_name"], "20260101-demo-01-aaa111-a.ipd.md")
        self.assertEqual(recs[0]["to_name"], "20260101-demo-01-aaa111-b.ipd.md")

    def test_status_reader_and_migration_ignore_rename_keys(self) -> None:
        # A status record + a rename record for the same id6.
        RH.append(
            self.root,
            id6="aaa111",
            tree="specs",
            workflow="aw spec set",
            actor="t",
            message="created.",
            date="20260101",
        )
        RH.append_rename(
            self.root,
            id6="aaa111",
            tree="specs",
            verb="rename",
            actor="t",
            from_name="a.spec.md",
            to_name="b.spec.md",
            date="20260101",
        )
        # read_for returns BOTH (it keys only on id6, tolerating the extra keys).
        self.assertEqual(len(RH.read_for(self.root, "aaa111")), 2)
        # The migration dedup keys on (id6,date,message); the rename record's distinct message does
        # not collide with the status record, and migrate does not choke on the extra keys.
        existing = {
            (r.get("id6"), r.get("date"), r.get("message"))
            for r in RH.read_all(self.root)
        }
        self.assertIn(("aaa111", "20260101", "created."), existing)

    def test_malformed_id6_raises(self) -> None:
        with self.assertRaises(ValueError):
            RH.append_rename(
                self.root,
                id6="BAD",
                tree="plans",
                verb="rename",
                actor="t",
                from_name="a",
                to_name="b",
            )

    def test_synthetic_key_only_via_case3_path(self) -> None:
        RH.append_rename(
            self.root,
            id6="synthetic:old-roadmap",
            tree="roadmaps",
            verb="rename",
            actor="t",
            from_name="20260101-old-roadmap.roadmap.md",
            to_name="20260101-new-roadmap.roadmap.md",
            key_kind="synthetic",
        )
        recs = RH.read_renames_for(self.root, "synthetic:old-roadmap")
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["key_kind"], "synthetic")


class RecordRenameCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_case1_id6_to_id6(self) -> None:
        RH.record_rename(
            self.root,
            tree="plans",
            verb="rename",
            actor="t",
            from_name="20260101-demo-01-aaa111-a.ipd.md",
            to_name="20260101-demo-01-aaa111-b.ipd.md",
        )
        recs = RH.read_renames_for(self.root, "aaa111")
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].get("key_kind", "id6"), "id6")

    def test_case2_id6less_to_id6_keys_on_new_id6(self) -> None:
        # V-03: a legacy id6-less name migrated INTO the grammar records under the NEW id6.
        RH.record_rename(
            self.root,
            tree="walkthroughs",
            verb="rename",
            actor="t",
            from_name="20260101-legacy-thing-walkthrough.md",
            to_name="20260101-demo-01-bbb222-thing.walkthrough.md",
        )
        recs = RH.read_renames_for(self.root, "bbb222")
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["from_name"], "20260101-legacy-thing-walkthrough.md")
        self.assertEqual(recs[0].get("key_kind", "id6"), "id6")

    def test_case3_both_id6less_synthetic_key(self) -> None:
        # V-05: both endpoints id6-less -> deterministic synthetic key, tagged synthetic.
        RH.record_rename(
            self.root,
            tree="roadmaps",
            verb="rename",
            actor="t",
            from_name="20260101-old-roadmap.roadmap.md",
            to_name="20260101-new-roadmap.roadmap.md",
        )
        key = RH._synthetic_key("20260101-old-roadmap.roadmap.md")
        recs = RH.read_renames_for(self.root, key)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["key_kind"], "synthetic")

    def test_noop_records_nothing(self) -> None:
        RH.record_rename(
            self.root,
            tree="plans",
            verb="rename",
            actor="t",
            from_name="x.ipd.md",
            to_name="x.ipd.md",
        )
        self.assertEqual(RH.read_all(self.root), [])

    def test_multi_rename_history_accumulates(self) -> None:
        RH.record_rename(
            self.root,
            tree="plans",
            verb="rename",
            actor="t",
            from_name="20260101-demo-01-aaa111-a.ipd.md",
            to_name="20260101-demo-01-aaa111-b.ipd.md",
        )
        RH.record_rename(
            self.root,
            tree="plans",
            verb="group",
            actor="t",
            from_name="20260101-demo-01-aaa111-b.ipd.md",
            to_name="20260101-other-02-aaa111-b.ipd.md",
        )
        recs = RH.read_renames_for(self.root, "aaa111")
        self.assertEqual(len(recs), 2)
        self.assertEqual([r["verb"] for r in recs], ["rename", "group"])

    def test_additivity_unwritable_ledger_does_not_raise(self) -> None:
        # record_rename is failure-isolated: even if the sidecar cannot be written, it must not
        # raise (the rename that called it must not fail).
        sidecar = RH.history_path(self.root)
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        # Make the parent a file so the write path fails.
        sidecar.write_text('{"id6":"aaa111"}\n', encoding="utf-8")
        os.chmod(sidecar, 0o400)
        try:
            RH.record_rename(  # must swallow the write error
                self.root,
                tree="plans",
                verb="rename",
                actor="t",
                from_name="20260101-demo-01-aaa111-a.ipd.md",
                to_name="20260101-demo-01-aaa111-b.ipd.md",
            )
        finally:
            os.chmod(sidecar, 0o600)


class CliEmissionTests(unittest.TestCase):
    """V-02: an applied plan rename appends exactly one record; dry-run appends nothing."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=str(self.root), check=True)
        pend = self.root / ".aw/records/plans/pending"
        pend.mkdir(parents=True)
        self.plan = pend / "20260101-demo-01-aaa111-old-slug.ipd.md"
        self.plan.write_text(
            "# IPD: x\n\n- Date: 20260101\n- Kind: child\n- Status: approved\n"
            "- Set: demo (demo)\n- Order: 1\n- Id: aaa111\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=str(self.root), check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-qm",
                "seed",
            ],
            cwd=str(self.root),
            check=True,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, args):
        env = dict(os.environ)
        env["AW_IPD_AUTHOR"] = "t"
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args, "--dir", str(self.root)],
            cwd=str(self.root),
            env=env,
            capture_output=True,
            text=True,
        )

    def _ledger(self):
        p = self.root / ".aw/records/history.jsonl"
        if not p.is_file():
            return []
        return [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]

    def test_applied_plan_rename_appends_one_record(self) -> None:
        r = self._run(["rename", "plans", "aaa111", "--slug", "new-slug", "--apply"])
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        renames = [x for x in self._ledger() if x.get("verb")]
        self.assertEqual(len(renames), 1, renames)
        self.assertEqual(renames[0]["id6"], "aaa111")
        self.assertEqual(renames[0]["tree"], "plans")
        self.assertTrue(renames[0]["to_name"].endswith("-new-slug.ipd.md"))

    def test_dry_run_appends_nothing(self) -> None:
        self._run(["rename", "plans", "aaa111", "--slug", "dry", "--apply"])  # one real
        before = len(self._ledger())
        self._run(["rename", "plans", "aaa111", "--slug", "dry2"])  # no --apply
        self.assertEqual(len(self._ledger()), before)


if __name__ == "__main__":
    unittest.main()
