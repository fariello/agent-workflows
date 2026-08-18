"""Tests for IPD awnaming Order 01: the uniform artifact-naming grammar `<...>.<type>.md`
(spec 20260817-2147-01).

Covers:
- both filename-grammar sites accept the optional `.<type>` facet AND a bare `.md` (permanent
  dual-read), with a closed-enum facet so an unknown `.foo.md` is not treated as a facet;
- `plans_refs.clustered_name` emits the facet only when an `artifact_type` is given;
- `aw backlog new` writes a `.backlog.md` file and `aw backlog check` accepts it;
- `aw ipd scaffold` derives a canonical `.ipd.md` name when `--path` is omitted, and still honors
  an explicit `--path` (backward compatibility);
- `aw plan-names` (via the shipped normalizer) reports a mistyped facet (`.spec.md` on a plan) as
  nonconformant;
- `aw plans mv` preserves the plan's Order and Date while renaming to the `.type.md` grammar
  (regression for vf03z3).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import plans_refs as refs
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend


REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZER = (
    REPO_ROOT
    / ".aw"
    / "system"
    / "workflows"
    / "setup-repo"
    / "tools"
    / "normalize_plan_names.py"
)


def _load_normalizer():
    spec = importlib.util.spec_from_file_location("awn_npn", NORMALIZER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GrammarRegexTests(unittest.TestCase):
    FACETED = "20260818-awnaming-01-f8e6y7-grammar-and-producers.ipd.md"
    BARE = "20260818-awnaming-01-f8e6y7-grammar-and-producers.md"

    def test_plans_refs_clustered_re_accepts_facet_and_bare(self) -> None:
        mf = refs._CLUSTERED_RE.match(self.FACETED)
        mb = refs._CLUSTERED_RE.match(self.BARE)
        self.assertIsNotNone(mf)
        self.assertIsNotNone(mb)
        keys = ("date", "set", "nn", "id6", "slug")
        self.assertEqual(mf.group(*keys), mb.group(*keys))
        self.assertEqual(mf.group("type"), "ipd")

    def test_plans_refs_clustered_re_rejects_unknown_facet(self) -> None:
        m = refs._CLUSTERED_RE.match(
            "20260818-awnaming-01-f8e6y7-grammar-and-producers.foo.md"
        )
        # Either it does not match at all, or it matched without a recognized facet.
        self.assertTrue(m is None or m.groupdict().get("type") is None)

    def test_normalizer_conformance_and_parse_equal(self) -> None:
        npn = _load_normalizer()
        self.assertTrue(npn.is_conformant(self.FACETED))
        self.assertTrue(npn.is_conformant(self.BARE))
        self.assertEqual(npn.parse_name(self.FACETED), npn.parse_name(self.BARE))

    def test_normalizer_flags_mistyped_facet(self) -> None:
        npn = _load_normalizer()
        self.assertFalse(
            npn.is_conformant(
                "20260818-awnaming-01-f8e6y7-grammar-and-producers.spec.md"
            )
        )


class ClusteredNameTests(unittest.TestCase):
    def test_emits_facet_only_when_type_given(self) -> None:
        with_type = refs.clustered_name(
            date="20260818",
            set_id="demo",
            order=1,
            id6="abc123",
            slug="x",
            artifact_type="ipd",
        )
        no_type = refs.clustered_name(
            date="20260818", set_id="demo", order=1, id6="abc123", slug="x"
        )
        self.assertEqual(with_type, "20260818-demo-01-abc123-x.ipd.md")
        self.assertEqual(no_type, "20260818-demo-01-abc123-x.md")

    def test_unknown_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            refs.clustered_name(
                date="20260818",
                set_id="demo",
                order=1,
                id6="abc123",
                slug="x",
                artifact_type="nope",
            )


class _RepoBackendCLIFixture(unittest.TestCase):
    """A repository-backend AW project (records under `.aw/records/`) with a scoped AW_HOME, so the
    record-path resolver points verbs at the local `.aw/records/` tree rather than the home store."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.repo = base / "repo"
        self.repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=str(self.repo), check=True)
        (self.repo / ".aw/records/plans/pending").mkdir(parents=True)
        (self.repo / ".aw/records/backlog/open").mkdir(parents=True)
        self.aw_home = base / "aw_home"
        self.aw_home.mkdir(parents=True)
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)
        register_or_update_project(
            str(self.repo), str(self.aw_home), project_id="awnaming-test"
        )
        cfg = self.repo / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "config.json").write_text(
            json.dumps(
                {
                    "delivery_mode": DeliveryMode.TRACKED.value,
                    "records_backend": RecordsBackend.REPOSITORY.value,
                    "aw_home": str(self.aw_home),
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        self._tmp.cleanup()

    def _run_cli(self, args):
        env = dict(os.environ)
        env["AW_IPD_AUTHOR"] = "tester"
        env["AW_HOME"] = str(self.aw_home)
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args, "--dir", str(self.repo)],
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
        )


class ProducerTests(_RepoBackendCLIFixture):
    def _run_cli_no_dir(self, args):
        env = dict(os.environ)
        env["AW_IPD_AUTHOR"] = "tester"
        env["AW_HOME"] = str(self.aw_home)
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args],
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_backlog_new_emits_backlog_facet(self) -> None:
        r = self._run_cli(
            ["backlog", "new", "--summary", "test item", "--set", "demo", "--apply"]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        created = list((self.repo / ".aw/records/backlog/open").glob("*.md"))
        self.assertEqual(len(created), 1)
        self.assertTrue(created[0].name.endswith(".backlog.md"), created[0].name)
        chk = self._run_cli(["backlog", "check"])
        self.assertEqual(chk.returncode, 0, chk.stderr + chk.stdout)

    def test_ipd_scaffold_derives_ipd_name_without_path(self) -> None:
        # scaffold has no --dir; it derives the root from cwd (the repo).
        r = self._run_cli_no_dir(
            [
                "ipd",
                "scaffold",
                "--kind",
                "child",
                "--set",
                "demo",
                "--order",
                "1",
                "--title",
                "Sample thing",
                "--apply",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        created = list((self.repo / ".aw/records/plans/pending").glob("*.ipd.md"))
        self.assertEqual(len(created), 1, [p.name for p in created])
        name = created[0].name
        self.assertTrue(name.endswith("-sample-thing.ipd.md"), name)
        # Filename id6 must equal front-matter Id.
        m = refs._CLUSTERED_RE.match(name)
        self.assertIsNotNone(m)
        text = created[0].read_text(encoding="utf-8")
        self.assertIn(f"- Id: {m.group('id6')}", text)

    def test_ipd_scaffold_honors_explicit_path(self) -> None:
        rel = ".aw/records/plans/pending/explicit.md"
        r = self._run_cli_no_dir(
            [
                "ipd",
                "scaffold",
                "--kind",
                "child",
                "--set",
                "demo",
                "--order",
                "1",
                "--title",
                "X",
                "--path",
                rel,
                "--apply",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertTrue((self.repo / rel).is_file())


class PlansMvPreservesOrderAndDateTests(_RepoBackendCLIFixture):
    """Regression for vf03z3: a bare `aw plans mv --slug X` must not clobber Order or Date."""

    def setUp(self) -> None:
        super().setUp()
        self.pending = self.repo / ".aw/records/plans/pending"
        self.old = self.pending / "20260810-demo-03-zzz111-old-slug.md"
        self.old.write_text(
            "# IPD: x\n\n"
            "- Date: 20260810\n"
            "- Kind: child\n"
            "- Status: approved\n"
            "- Set: demo (demo)\n"
            "- Order: 3\n"
            "- Id: zzz111\n\n"
            "## Goal\n\nx\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=str(self.repo), check=True)
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
            cwd=str(self.repo),
            check=True,
        )

    def test_mv_preserves_order_date_and_adds_facet(self) -> None:
        r = self._run_cli(["plans", "mv", "zzz111", "--slug", "new-slug", "--apply"])
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        created = list(self.pending.glob("*.md"))
        self.assertEqual(len(created), 1, [p.name for p in created])
        name = created[0].name
        self.assertTrue(name.endswith(".ipd.md"), name)
        self.assertTrue(name.startswith("20260810-demo-03-zzz111-"), name)
        text = created[0].read_text(encoding="utf-8")
        self.assertIn("- Order: 3", text)
        self.assertIn("- Date: 20260810", text)


if __name__ == "__main__":
    unittest.main()
