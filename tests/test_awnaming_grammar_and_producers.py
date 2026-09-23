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
        self.assertIn("- Set: demo", text)
        self.assertIn("- Order: 1", text)

    def test_ipd_scaffold_without_set_or_order_rejected(self) -> None:
        r = self._run_cli_no_dir(
            [
                "ipd",
                "scaffold",
                "--kind",
                "child",
                "--title",
                "Sample thing",
                "--apply",
            ]
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(
            "the following arguments are required" in r.stderr or "required" in r.stderr
        )

    def test_ipd_scaffold_explicit_nonconforming_path_rejected(self) -> None:
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
        self.assertEqual(r.returncode, 2)
        self.assertIn("clustering grammar", r.stdout + r.stderr)
        self.assertFalse((self.repo / rel).exists())

    def test_ipd_scaffold_honors_explicit_path_with_legacy_name(self) -> None:
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
                "--legacy-name",
                "--apply",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertTrue((self.repo / rel).is_file())

    def test_ipd_scaffold_conforming_explicit_path_reconciles_id6(self) -> None:
        rel = ".aw/records/plans/pending/20260819-demo-01-v1rj3p-foo.ipd.md"
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
                "Foo",
                "--path",
                rel,
                "--apply",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        created = self.repo / rel
        self.assertTrue(created.is_file())
        text = created.read_text(encoding="utf-8")
        self.assertIn("- Id: v1rj3p", text)
        self.assertIn("- Set: demo", text)
        self.assertIn("- Order: 1", text)


class PlansMvPreservesOrderAndDateTests(_RepoBackendCLIFixture):
    """Regression for vf03z3: a bare `aw rename plans <id6> --slug X` must not clobber Order or Date
    (awcmdsurf Order 05 renamed the old `plans mv` verb to `rename plans`)."""

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
        r = self._run_cli(
            ["rename", "plans", "zzz111", "--slug", "new-slug", "--apply"]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        created = list(self.pending.glob("*.md"))
        self.assertEqual(len(created), 1, [p.name for p in created])
        name = created[0].name
        self.assertTrue(name.endswith(".ipd.md"), name)
        self.assertTrue(name.startswith("20260810-demo-03-zzz111-"), name)
        text = created[0].read_text(encoding="utf-8")
        self.assertIn("- Order: 3", text)
        self.assertIn("- Date: 20260810", text)


class PlansGroupPreservesOrderTests(_RepoBackendCLIFixture):
    """Regression for e3hzyc: `aw group plans <id6> --set X [--rename] --apply` with NO `--order`
    must PRESERVE each plan's own Order instead of renumbering every named plan from zero.

    The sibling verb already guarantees this (`PlansMvPreservesOrderAndDateTests` above, vf03z3),
    so the two verbs' guarantees now sit side by side. Both `group` branches are covered, because
    the bug fires on BOTH: the `--rename` branch clobbered the front matter AND the filename `NN`
    slot, while the metadata-only branch clobbered the front matter and left the filename, so the
    file contradicted its own name. An EXPLICIT `--order` must still renumber sequentially, which
    is the legitimate Set-assembly use the `+ i` arithmetic exists for.
    """

    def setUp(self) -> None:
        super().setUp()
        self.pending = self.repo / ".aw/records/plans/pending"
        self._seed(
            "20260908-probeset-00-aaa000-probe-orchestrator.ipd.md",
            kind="orchestrator",
            order=0,
            id6="aaa000",
        )
        self._seed(
            "20260908-probeset-01-bbb222-probe-child-one.ipd.md",
            kind="child",
            order=1,
            id6="bbb222",
        )
        self._seed(
            "20260908-probeset-02-ccc333-probe-child-two.ipd.md",
            kind="child",
            order=2,
            id6="ccc333",
        )
        self._git_commit()

    def _seed(
        self,
        name: str,
        *,
        kind: str,
        order: object,
        id6: str,
        date: str = "20260908",
    ) -> Path:
        meta = [
            f"- Date: {date}",
            f"- Kind: {kind}",
            "- Concern: x.",
            "- Scope: x.",
            "- Status: approved",
            "- Set: probeset (probe)",
        ]
        if order is not None:
            meta.append(f"- Order: {order}")
        meta.append("- Author: t")
        meta.append(f"- Id: {id6}")
        path = self.pending / name
        path.write_text(
            "# IPD: probe\n\n" + "\n".join(meta) + "\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        return path

    def _git_commit(self) -> None:
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

    def _run_cli(self, args):
        """Like the shared helper, but PINS the subprocess to THIS tree via ``PYTHONPATH``.

        Measured while executing e3hzyc: the repository is installed editable, so that `.pth` names
        an ABSOLUTE path to the main checkout. A `-m agent_workflows` subprocess launched from a
        worktree therefore imports the MAIN checkout's modules and a CLI-level assertion silently
        tests code the change never touched. Prepending ``REPO_ROOT`` (this test file's own tree)
        makes the assertion measure the tree under test, and is a no-op when run from the main
        checkout.
        """

        env = dict(os.environ)
        env["AW_IPD_AUTHOR"] = "tester"
        env["AW_HOME"] = str(self.aw_home)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(REPO_ROOT), *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
        )
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args, "--dir", str(self.repo)],
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
        )

    def _lint(self, path: Path):
        """`aw ipd lint` on one plan, pinned to this tree the same way ``_run_cli`` is."""

        env = dict(os.environ)
        env["AW_IPD_AUTHOR"] = "tester"
        env["AW_HOME"] = str(self.aw_home)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(REPO_ROOT), *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
        )
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "ipd",
                "lint",
                path.relative_to(self.repo).as_posix(),
            ],
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
        )

    def _only(self, id6: str) -> Path:
        found = list(self.pending.glob(f"*-{id6}-*.md"))
        self.assertEqual(len(found), 1, [p.name for p in found])
        return found[0]

    def test_bare_rename_regroup_preserves_a_child_order(self) -> None:
        """E-01/E-04(a): the `--rename` branch. Front matter AND filename slot must both survive."""
        r = self._run_cli(
            ["group", "plans", "bbb222", "--set", "newset", "--rename", "--apply"]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        moved = self._only("bbb222")
        # (1) the front-matter Order is preserved...
        self.assertIn("- Order: 1", moved.read_text(encoding="utf-8"))
        # (2) ...and so is the filename's NN slot, which the naming grammar reserves 00 for an
        # orchestrator. Asserted separately: a half fix keeps one and clobbers the other.
        m = refs._CLUSTERED_RE.match(moved.name)
        self.assertIsNotNone(m, moved.name)
        self.assertEqual(m.group("nn"), "01", moved.name)
        self.assertEqual(m.group("set"), "newset", moved.name)

    def test_bare_metadata_only_regroup_preserves_a_child_order(self) -> None:
        """E-01/E-04(b): the metadata-only branch, the worse half. The filename is untouched by
        construction here, so a clobbered `- Order:` makes the file CONTRADICT ITS OWN NAME."""
        r = self._run_cli(["group", "plans", "bbb222", "--set", "metaset", "--apply"])
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        kept = self._only("bbb222")
        # The filename is unchanged (no --rename), still carrying the -01- slot.
        self.assertEqual(
            kept.name, "20260908-probeset-01-bbb222-probe-child-one.ipd.md", kept.name
        )
        text = kept.read_text(encoding="utf-8")
        self.assertIn("- Set: metaset", text)
        # ...so the front matter must AGREE with it rather than reading `- Order: 0`.
        self.assertIn("- Order: 1", text)
        m = refs._CLUSTERED_RE.match(kept.name)
        self.assertIsNotNone(m, kept.name)
        order_line = refs._ORDER_LINE_RE.search(text)
        self.assertIsNotNone(order_line, text)
        self.assertEqual(
            int(order_line.group(1)),
            int(m.group("nn")),
            f"filename NN {m.group('nn')} disagrees with front matter {order_line.group(1)}",
        )

    def test_explicit_order_still_renumbers_sequentially(self) -> None:
        """E-04(c): the one legitimate reason the `+ i` arithmetic exists. An EXPLICIT `--order`
        assembles a Set out of scattered plans, so preserving unconditionally would BREAK it. This
        is the behavior a careless fix destroys, so it stands alone."""
        r = self._run_cli(
            [
                "group",
                "plans",
                "bbb222",
                "ccc333",
                "--set",
                "asmset",
                "--order",
                "1",
                "--rename",
                "--apply",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        first = self._only("bbb222")
        second = self._only("ccc333")
        self.assertTrue(first.name.startswith("20260908-asmset-01-bbb222-"), first.name)
        self.assertIn("- Order: 1", first.read_text(encoding="utf-8"))
        self.assertTrue(
            second.name.startswith("20260908-asmset-02-ccc333-"), second.name
        )
        self.assertIn("- Order: 2", second.read_text(encoding="utf-8"))

    def test_bare_regroup_falls_back_to_the_filename_slot(self) -> None:
        """E-04(d): with no `- Order:` line to read, the plan's own filename `NN` is the next tier,
        mirroring `run_mv`'s three-tier fallback rather than dropping to zero."""
        self._seed(
            "20260908-probeset-04-ddd444-probe-no-order-line.ipd.md",
            kind="child",
            order=None,
            id6="ddd444",
        )
        self._git_commit()
        seeded = self._only("ddd444")
        self.assertNotIn("- Order:", seeded.read_text(encoding="utf-8"))
        r = self._run_cli(
            ["group", "plans", "ddd444", "--set", "fbset", "--rename", "--apply"]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        moved = self._only("ddd444")
        self.assertTrue(moved.name.startswith("20260908-fbset-04-ddd444-"), moved.name)
        self.assertIn("- Order: 4", moved.read_text(encoding="utf-8"))

    def test_bare_regroup_keeps_an_orchestrator_at_zero(self) -> None:
        """E-04(e): 0 is CORRECT for a `Kind: orchestrator`, so "preserve" must mean preserve and
        not "move off zero"."""
        r = self._run_cli(
            ["group", "plans", "aaa000", "--set", "orchset", "--rename", "--apply"]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        moved = self._only("aaa000")
        self.assertTrue(
            moved.name.startswith("20260908-orchset-00-aaa000-"), moved.name
        )
        self.assertIn("- Order: 0", moved.read_text(encoding="utf-8"))

    def test_explicit_order_zero_is_still_reachable(self) -> None:
        """E-04(f): the direct test of the sentinel change. `None` now means "preserve", so an
        EXPLICIT `--order 0` must still land at 0 rather than becoming unreachable."""
        r = self._run_cli(
            [
                "group",
                "plans",
                "ccc333",
                "--set",
                "zeroset",
                "--order",
                "0",
                "--rename",
                "--apply",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        moved = self._only("ccc333")
        self.assertTrue(
            moved.name.startswith("20260908-zeroset-00-ccc333-"), moved.name
        )
        self.assertIn("- Order: 0", moved.read_text(encoding="utf-8"))

    def test_lint_no_longer_reports_ipd_m104_after_a_bare_regroup(self) -> None:
        """The end-to-end proof: `aw ipd lint` reported `IPD-M104` ("child Order must be an integer
        >= 1") on the regrouped child, while `aw check plans` saw nothing in the same tree. Assert on
        the ABSENCE OF THAT CODE, not on a clean exit: a probe plan legitimately emits unrelated
        `IPD-H2xx` structural codes, so an exit-0 assertion could never pass."""
        before = self._lint(self._only("bbb222"))
        self.assertNotIn("IPD-M104: Order:", before.stdout + before.stderr)
        r = self._run_cli(
            ["group", "plans", "bbb222", "--set", "lintset", "--rename", "--apply"]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        after = self._lint(self._only("bbb222"))
        out = after.stdout + after.stderr
        self.assertNotIn("IPD-M104: Order:", out, out)
        # ...and the probe file's unrelated structural findings are still reported, proving the
        # linter actually ran rather than the assertion passing on empty output.
        self.assertIn("IPD-H202", out, out)


class SetidLengthAuthoringGuardTests(_RepoBackendCLIFixture):
    """setidlen x75obw E-06 (catalog I-17): the FOUR `--set`-taking verbs refuse an over-length setid.

    THE VERB LIST IS EXACTLY FOUR, verified by `--help`: `aw ipd scaffold`, `aw backlog new`,
    `aw research new`, `aw group`. `aw specs new` is DELIBERATELY ABSENT and one row below pins why:
    it takes no `--set` flag at all (`specs.run_new` passes `set_id=id6`, so a standalone spec's setid
    is always its own 6-character id6), so a guard there would be unreachable code and a test asserting
    it aborts on a 25-character `--set` would have to invent a flag that does not exist.

    THE BOUNDARY ROWS MATTER MOST. 24 must PASS (with a note) and 25 must REFUSE, because the longest
    setid in the real repository is exactly 24 characters; a single verb disagreeing by one would refuse
    a live record. That is also why all four share ONE validator rather than four comparisons.
    """

    #: Exactly at the maximum, so it must be ACCEPTED. 25 of the same character must be refused.
    AT_MAX = "a" * 24
    OVER_MAX = "a" * 25
    IN_WARN_BAND = "a" * 16

    def _pin_cutover(self):
        """Stamp a boundary, proving the guard does not depend on one (it must refuse either way)."""
        cfg = self.repo / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text(
            json.dumps(
                {"schema_version": 2, "cutovers": {"setid_length": "2026-09-23"}}
            ),
            encoding="utf-8",
        )

    def _run_pinned(self, args, *, with_dir=True):
        """`_run_cli`, but pinned to THIS tree so the assertion measures the code under test.

        ``with_dir=False`` for a verb that takes no ``--dir`` (``aw ipd scaffold``), which resolves its
        repository from the CWD instead; passing the flag there makes argparse refuse the whole
        invocation and every assertion below it measures the parser rather than the guard.
        """
        env = dict(os.environ)
        env["AW_IPD_AUTHOR"] = "tester"
        env["AW_HOME"] = str(self.aw_home)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(REPO_ROOT), *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
        )
        cmd = [sys.executable, "-m", "agent_workflows", *args]
        if with_dir:
            cmd += ["--dir", str(self.repo)]
        return subprocess.run(
            cmd,
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
        )

    def _scaffold(self, setid):
        return self._run_pinned(
            [
                "ipd",
                "scaffold",
                "--kind",
                "child",
                "--title",
                "T",
                "--set",
                setid,
                "--order",
                "1",
                "--author",
                "tester",
            ],
            with_dir=False,
        )

    def _backlog_new(self, setid):
        return self._run_pinned(["backlog", "new", "--set", setid, "--summary", "s"])

    def _research_new(self, setid):
        return self._run_pinned(
            [
                "research",
                "new",
                "--kind",
                "research-prompt",
                "--slug",
                "sl",
                "--summary",
                "s",
                "--set",
                setid,
            ],
            with_dir=False,
        )

    def _group(self, setid):
        return self._run_pinned(["group", "specs", "aaa111", "--set", setid])

    def test_every_set_taking_verb_refuses_an_over_max_setid(self):
        self._pin_cutover()
        failures = []
        for name, fn in (
            ("aw ipd scaffold", self._scaffold),
            ("aw backlog new", self._backlog_new),
            ("aw research new", self._research_new),
            ("aw group", self._group),
        ):
            r = fn(self.OVER_MAX)
            out = r.stdout + r.stderr
            if r.returncode == 0:
                failures.append(f"{name}: exit 0, expected a refusal. output:\n{out}")
            elif "25 characters" not in out or "24" not in out:
                failures.append(
                    f"{name}: refused but did not name the length and the limit:\n{out}"
                )
        self.assertEqual(
            failures,
            [],
            "a verb that does not refuse an over-length setid is an unguarded authoring path; all "
            "four must route through `config.validate_setid_length_for_authoring`.\n"
            + "\n".join(failures),
        )

    def test_a_setid_at_exactly_the_maximum_is_accepted(self):
        """ZERO MARGIN: the longest real setid is exactly this long, so refusing here breaks it."""
        self._pin_cutover()
        r = self._scaffold(self.AT_MAX)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_warn_band_warns_and_still_proceeds(self):
        self._pin_cutover()
        r = self._scaffold(self.IN_WARN_BAND)
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, out)
        self.assertIn("16 characters", out, out)
        self.assertIn("preferred", out, out)

    def test_a_conformant_setid_draws_no_note_at_all(self):
        self._pin_cutover()
        r = self._scaffold("a" * 14)
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, out)
        self.assertNotIn("characters", out, out)

    def test_the_refusal_does_not_require_a_stamped_cutover(self):
        """A setid being CHOSEN now is post-cutover whatever the boundary says."""
        r = self._scaffold(self.OVER_MAX)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_aw_specs_new_has_no_set_flag_so_it_cannot_violate_the_bound(self):
        """Pins the EXCLUSION: `--set` is rejected by the parser, so no guard belongs there."""
        r = self._run_pinned(
            ["specs", "new", "--title", "T", "--slug", "sl", "--set", self.OVER_MAX]
        )
        out = r.stdout + r.stderr
        self.assertNotEqual(r.returncode, 0, out)
        self.assertIn("unrecognized arguments", out, out)


if __name__ == "__main__":
    unittest.main()
