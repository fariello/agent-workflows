"""Adoption tests for the shared self-commit helper across records-mutating verbs (selfcommit jgcm68).

Covers the child-02 validation items:

* V-01 - the shared ``--commit``/``--no-commit`` arg group is registered on every records-mutating
  parser (archive/group/rename/set/research set-assign-mv) and reaches the backend namespace.
* V-02 - ``research_archive.run_archive`` / ``plans_archive.run_archive`` commit exactly the moved
  paths with ``--commit``; ``--no-commit`` skips; non-interactive-without-commit
  is a no-op; an unrelated dirty file is never folded in.
* V-03 - each group/rename backend RETURNS a ``MutationResult`` whose touched paths match the
  files it moved, and commits NOTHING itself.

BOTH HALVES OF THE GENERATED-MANIFEST CONTRACT ARE PINNED HERE (idxuntrack `4r0qp1`): the
INDEX.json/INDEX.md manifests are still REGENERATED on disk by every mutating verb, and are NEVER
part of a commit path-set. A test that stops asserting either half would let the pair drift.
Plus the shared ``offer_commit`` ignored-path guard (E-06), which is what makes a MISSED
contributor degrade to "the manifest was not committed" instead of "nothing was committed at all".
* V-04 - ``aw research set-assign``/``mv`` AND ``aw group/rename research`` (the SAME shared backend
  reached by two entry points) each fire EXACTLY ONE offer - no double-commit (PR-012).
* V-05 - the shared ``status_set.run_set_command`` offers once for a single-target transition and a
  whole-Set transition; ``--no-commit`` skips; non-interactive is a no-op; unrelated dirty untouched.
* V-06 - both ``aw specs set <id6>`` (status_set path) and ``aw specs set --status <X> <path>``
  (specs.py path) fire EXACTLY ONE offer each - no double-offer, no missed path (PR-004).
* V-07 - the ``_run_noun_verb`` group/rename dispatch offers exactly once per invocation for plans,
  research, AND one artifact_rename type (specs), proving non-plans coverage (PR-003).
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    artifact_rename,
    cli,
    git_commit_helper,
    plans_archive,
    plans_refs,
    research_archive,
    research_refs,
    status_set,
)
from tests.support import git, init_repo


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------


def _commit_seed(repo: Path) -> None:
    (repo / ".seed").write_text("seed\n", encoding="utf-8")
    git(repo, "add", "--", ".seed")
    git(repo, "commit", "-q", "-m", "seed")


def _head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def _committed_files(repo: Path, sha: str) -> set:
    out = git(repo, "show", "--name-only", "--pretty=format:", sha).stdout
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


class _OfferSpy:
    """Monkeypatch ``git_commit_helper.offer_commit`` to record every call (paths + kwargs).

    Used where we assert EXACTLY-ONCE / which-paths without needing a real commit. Each adopting
    module imports the helper module and calls ``_gch.offer_commit`` at call time, so patching the
    single function object on the module is observed by all of them.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._real = git_commit_helper.offer_commit

    def __enter__(self):
        def _fake(repo_root, paths, **kwargs):
            self.calls.append({"paths": list(paths), "kwargs": kwargs})
            return git_commit_helper.CommitOutcome(
                git_commit_helper.STATUS_SKIPPED, None, (), "spy: skipped"
            )

        git_commit_helper.offer_commit = _fake  # type: ignore[assignment]
        return self

    def __exit__(self, *exc):
        git_commit_helper.offer_commit = self._real  # type: ignore[assignment]

    @property
    def count(self) -> int:
        return len(self.calls)

    def all_paths(self) -> set:
        out: set = set()
        for c in self.calls:
            out.update(c["paths"])
        return out


def _write_research(root: Path, *, set_id, order, id6, slug, status, created):
    from agent_workflows import research_cmd as C
    from agent_workflows import research_contract as R

    rroot = root / R.RESEARCH_ROOT
    rroot.mkdir(parents=True, exist_ok=True)
    name = R.format_name(
        R.ResearchName(
            date=created,
            set_id=set_id,
            order=f"{order:02d}",
            id6=id6,
            slug=slug,
            model=None,
            kind="notes",
        )
    )
    content = C.build_frontmatter(
        id6=id6,
        created=created,
        set_id=set_id,
        order=f"{order:02d}",
        topic=["t"],
        model=None,
        kind="notes",
        status=status,
        outcome="none-yet",
        summary="s",
        consumed_by=None,
    )
    p = rroot / name
    p.write_text(content, encoding="utf-8")
    return p


def _write_plan(
    plans_dir: Path, *, id6, set_id, order, slug, status="to-review"
) -> Path:
    pend = plans_dir / "pending"
    pend.mkdir(parents=True, exist_ok=True)
    p = pend / f"20260823-{set_id}-{order:02d}-{id6}-{slug}.ipd.md"
    p.write_text(
        f"""# IPD: Sample

- Date: 2026-08-23
- Kind: child
- Status: {status}
- Set: {set_id}
- Order: {order}
- Author: Test
- Id: {id6}

## Workflow history
- 2026-08-23 {status} (test): created

## Goal
g
""",
        encoding="utf-8",
    )
    return p


def _write_spec(repo: Path, *, id6, slug, status="draft") -> Path:
    d = repo / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260823-1200-01-{id6}-{slug}.spec.md"
    p.write_text(
        f"""# Spec: Sample {id6}

- Id: {id6}
- Status: {status}

## Summary
s

## Workflow history
- 2026-08-23 {status} (test): created
""",
        encoding="utf-8",
    )
    return p


# --------------------------------------------------------------------------------------
# V-01: flags exist on every records-mutating parser
# --------------------------------------------------------------------------------------


class FlagRegistrationTests(unittest.TestCase):
    def _parse(self, argv):
        parser = cli._build_parser()
        return parser.parse_args(argv)

    def test_flags_present_on_all_records_mutating_parsers(self):
        # archive, group, rename, set, and research set-assign all accept --commit / --no-commit.
        for argv in (
            ["archive", "research", "--commit"],
            ["archive", "plans", "--no-commit"],
            ["group", "plans", "abc123", "--set", "x", "--commit"],
            ["rename", "plans", "abc123", "--slug", "y", "--no-commit"],
            ["set", "approved", "abc123", "--commit"],
            ["research", "set-assign", "abc123", "--set", "x", "--commit"],
            ["research", "mv", "abc123", "--slug", "z", "--no-commit"],
            ["ipd", "set", "approved", "abc123", "--commit"],
            ["spec", "set", "reviewed", "abc123", "--no-commit"],
        ):
            ns = self._parse(argv)
            self.assertTrue(
                hasattr(ns, "commit") and hasattr(ns, "no_commit"),
                f"missing commit flags on: {argv}",
            )

    def test_commit_and_no_commit_are_mutually_exclusive(self):
        parser = cli._build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["set", "approved", "abc123", "--commit", "--no-commit"])


# --------------------------------------------------------------------------------------
# V-02: archive commits exactly its touched paths
# --------------------------------------------------------------------------------------


class ArchiveCommitTests(unittest.TestCase):
    def setUp(self):
        self.repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_arch_")))
        self.addCleanup(lambda: shutil.rmtree(self.repo, ignore_errors=True))
        from agent_workflows import research_contract as R

        self.rroot = self.repo / R.RESEARCH_ROOT
        _write_research(
            self.repo,
            set_id="beta",
            order=0,
            id6="bbbbbb",
            slug="b",
            status="active",
            created="20260705",
        )
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "seed research")

    def _args(self, **kw):
        base = dict(
            target="bbbbbb",
            dir=str(self.repo),
            keep=None,
            apply=True,
            commit=False,
            no_commit=False,
        )
        base.update(kw)
        return argparse.Namespace(**base)

    def test_commit_flag_commits_exactly_the_moved_doc_and_not_the_index(self):
        # an unrelated dirty file must NOT be folded in
        (self.repo / "unrelated.txt").write_text("dirty\n", encoding="utf-8")
        before = _head(self.repo)
        rc = research_archive.run_archive(self._args(commit=True))
        self.assertEqual(rc, 0)
        after = _head(self.repo)
        self.assertNotEqual(before, after, "a commit should have been made")
        files = _committed_files(self.repo, after)
        # The moved doc (old + new path) is committed; unrelated.txt is not.
        self.assertTrue(any("bbbbbb" in f for f in files))
        self.assertNotIn("unrelated.txt", files)
        # The GENERATED manifests are NOT committed (idxuntrack `4r0qp1` E-07), ...
        self.assertEqual(
            [f for f in files if f.endswith(("INDEX.json", "INDEX.md"))],
            [],
            f"generated manifests must not be committed; got {sorted(files)}",
        )
        # ... but they ARE still refreshed on disk, which is the half that must survive.
        from agent_workflows import research_index as RI

        idx = self.rroot / RI.INDEX_JSON
        self.assertTrue(idx.is_file(), "the manifest must still be regenerated on disk")
        self.assertIn("bbbbbb", idx.read_text(encoding="utf-8"))

    def test_no_commit_skips(self):
        before = _head(self.repo)
        rc = research_archive.run_archive(self._args(no_commit=True))
        self.assertEqual(rc, 0)
        self.assertEqual(before, _head(self.repo), "no commit should be made")

    def test_non_interactive_without_commit_is_noop(self):
        # commit=False, no_commit=False, non-interactive stdin (pytest) -> offer_commit no-ops.
        before = _head(self.repo)
        rc = research_archive.run_archive(self._args())
        self.assertEqual(rc, 0)
        self.assertEqual(before, _head(self.repo))


class PlansArchiveCommitTests(unittest.TestCase):
    def setUp(self):
        self.repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_parch_")))
        self.addCleanup(lambda: shutil.rmtree(self.repo, ignore_errors=True))
        self.plans_dir = self.repo / ".aw" / "records" / "plans"
        # A terminal-root (executed) plan is what `aw archive plans <target>` shelves.
        ex = self.plans_dir / "executed"
        ex.mkdir(parents=True, exist_ok=True)
        self.plan = ex / "20260101-oldset-01-pl1234-old-plan.ipd.md"
        self.plan.write_text(
            "# IPD\n\n- Id: pl1234\n- Set: oldset\n- Status: executed\n",
            encoding="utf-8",
        )
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "seed plan")

    def test_commit_flag_commits_moved_plan(self):
        before = _head(self.repo)
        rc = plans_archive.run_archive(
            argparse.Namespace(
                type_or_target=None,
                target="pl1234",
                dir=str(self.repo),
                age=None,
                keep=None,
                apply=True,
                commit=True,
                no_commit=False,
            )
        )
        self.assertEqual(rc, 0)
        after = _head(self.repo)
        if before != after:
            files = _committed_files(self.repo, after)
            self.assertTrue(any("pl1234" in f for f in files))


# --------------------------------------------------------------------------------------
# V-03: backends RETURN a MutationResult and commit nothing themselves
# --------------------------------------------------------------------------------------


class BackendReturnShapeTests(unittest.TestCase):
    def test_plans_backend_returns_touched_paths(self):
        repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_pb_")))
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        plans_dir = repo / ".aw" / "records" / "plans"
        _write_plan(plans_dir, id6="pl1234", set_id="oldset", order=1, slug="s")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        before = _head(repo)
        mr = plans_refs.run_set_assign(
            argparse.Namespace(
                dir=str(repo),
                ids=["pl1234"],
                set="newset",
                order=0,
                rename=True,
                apply=True,
                no_refs=True,
            )
        )
        self.assertIsInstance(mr, plans_refs.MutationResult)
        self.assertEqual(mr.rc, 0)
        self.assertTrue(mr.touched_paths, "expected touched paths")
        self.assertTrue(any("pl1234" in p for p in mr.touched_paths))
        # The generated manifests are NOT part of the commit path-set the backend returns, and the
        # `index_paths` field that used to carry them is gone (idxuntrack `4r0qp1` E-03).
        self.assertFalse(
            hasattr(mr, "index_paths"),
            "MutationResult must no longer carry an index_paths commit contribution",
        )
        self.assertEqual(
            [p for p in mr.touched_paths if p.endswith(("INDEX.json", "INDEX.md"))],
            [],
            f"generated manifests must not be in the commit path-set; got {mr.touched_paths}",
        )
        # But the manifest IS still refreshed on disk by the backend.
        idx = plans_dir / "INDEX.json"
        self.assertTrue(idx.is_file(), "the manifest must still be regenerated on disk")
        self.assertIn("pl1234", idx.read_text(encoding="utf-8"))
        # The backend itself made NO commit.
        self.assertEqual(before, _head(repo), "backend must not commit")

    def test_research_backend_returns_touched_paths(self):
        repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_rb_")))
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        _write_research(
            repo,
            set_id="s",
            order=0,
            id6="rr1111",
            slug="a",
            status="intake",
            created="20260101",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        before = _head(repo)
        mr = research_refs.run_mv(
            argparse.Namespace(
                dir=str(repo),
                id="rr1111",
                slug="newslug",
                kind=None,
                model=None,
                apply=True,
            )
        )
        self.assertIsInstance(mr, plans_refs.MutationResult)
        self.assertEqual(mr.rc, 0)
        self.assertTrue(any("rr1111" in p for p in mr.touched_paths))
        self.assertEqual(before, _head(repo), "backend must not commit")

    def test_artifact_rename_specs_backend_returns_touched_paths(self):
        repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_ar_")))
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        _write_spec(repo, id6="sp1234", slug="a")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        before = _head(repo)
        mr = artifact_rename.run_group_specs(
            argparse.Namespace(
                dir=str(repo),
                ids=["sp1234"],
                selector=None,
                id=None,
                set="newset",
                order=0,
                apply=True,
                no_refs=True,
                rename=True,
                force=False,
            )
        )
        self.assertIsInstance(mr, plans_refs.MutationResult)
        self.assertEqual(mr.rc, 0)
        self.assertTrue(any("sp1234" in p for p in mr.touched_paths))
        self.assertEqual(before, _head(repo), "backend must not commit")


# --------------------------------------------------------------------------------------
# V-04: research shared backend - each entry point offers EXACTLY ONCE
# --------------------------------------------------------------------------------------


class ResearchExactlyOnceTests(unittest.TestCase):
    def _repo_with_doc(self, id6="rr2222"):
        repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_r1_")))
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        _write_research(
            repo,
            set_id="s",
            order=0,
            id6=id6,
            slug="a",
            status="intake",
            created="20260101",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        return repo

    def test_research_mv_command_branch_fires_one_offer(self):
        repo = self._repo_with_doc("rr2222")
        with _OfferSpy() as spy:
            cli._dispatch(
                [
                    "research",
                    "mv",
                    "rr2222",
                    "--slug",
                    "newslug",
                    "--apply",
                    "--dir",
                    str(repo),
                ]
            )
        self.assertEqual(spy.count, 1, "aw research mv must fire exactly one offer")

    def test_group_research_dispatch_fires_one_offer(self):
        repo = self._repo_with_doc("rr3333")
        with _OfferSpy() as spy:
            cli._dispatch(
                [
                    "group",
                    "research",
                    "rr3333",
                    "--set",
                    "newset",
                    "--rename",
                    "--apply",
                    "--dir",
                    str(repo),
                ]
            )
        self.assertEqual(
            spy.count,
            1,
            "aw group research must fire exactly one offer (not double via backend)",
        )


# --------------------------------------------------------------------------------------
# V-05: status_set single-target + whole-Set
# --------------------------------------------------------------------------------------


class StatusSetCommitTests(unittest.TestCase):
    def setUp(self):
        self.repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_ss_")))
        self.addCleanup(lambda: shutil.rmtree(self.repo, ignore_errors=True))
        self.plans_dir = self.repo / ".aw" / "records" / "plans"

    def _run_set(self, raw_args, **flags):
        ns = argparse.Namespace(
            args=raw_args,
            dir=str(self.repo),
            message="m",
            dry_run=False,
            yes=True,
            commit=flags.get("commit", False),
            no_commit=flags.get("no_commit", False),
        )
        return status_set.run_set_command(raw_args, scoped_type="plans", args=ns)

    def test_single_target_offers_once_and_commits_one_file(self):
        _write_plan(self.plans_dir, id6="pl0001", set_id="s", order=1, slug="a")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "seed")
        with _OfferSpy() as spy:
            rc = self._run_set(["approved", "pl0001"])
        self.assertEqual(rc, 0)
        self.assertEqual(spy.count, 1)
        self.assertTrue(any("pl0001" in p for p in spy.all_paths()))

    def test_whole_set_offers_once_and_commits_set_files(self):
        _write_plan(self.plans_dir, id6="pl0002", set_id="grp", order=1, slug="a")
        _write_plan(self.plans_dir, id6="pl0003", set_id="grp", order=2, slug="b")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "seed")
        with _OfferSpy() as spy:
            rc = self._run_set(["approved", "grp"])
        self.assertEqual(rc, 0)
        self.assertEqual(spy.count, 1, "one offer for the whole-Set transition")
        paths = spy.all_paths()
        self.assertTrue(any("pl0002" in p for p in paths))
        self.assertTrue(any("pl0003" in p for p in paths))

    def test_no_commit_real_skips(self):
        _write_plan(self.plans_dir, id6="pl0004", set_id="s", order=1, slug="a")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "seed")
        before = _head(self.repo)
        rc = self._run_set(["approved", "pl0004"], no_commit=True)
        self.assertEqual(rc, 0)
        self.assertEqual(before, _head(self.repo))

    def test_commit_flag_does_not_fold_unrelated_dirty(self):
        _write_plan(self.plans_dir, id6="pl0005", set_id="s", order=1, slug="a")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "seed")
        (self.repo / "unrelated.txt").write_text("x\n", encoding="utf-8")
        rc = self._run_set(["approved", "pl0005"], commit=True)
        self.assertEqual(rc, 0)
        files = _committed_files(self.repo, _head(self.repo))
        self.assertNotIn("unrelated.txt", files)
        self.assertTrue(any("pl0005" in f for f in files))


# --------------------------------------------------------------------------------------
# V-06: specs dual path each fires exactly once
# --------------------------------------------------------------------------------------


class SpecsDualPathTests(unittest.TestCase):
    def _repo_with_spec(self, id6="sp9999", status="draft"):
        repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_sp_")))
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        self._spec = _write_spec(repo, id6=id6, slug="a", status=status)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        return repo

    def test_status_set_path_no_status_flag_fires_one_offer(self):
        repo = self._repo_with_spec("sp9999", status="draft")
        with _OfferSpy() as spy:
            cli._dispatch(
                ["spec", "set", "to-review", "sp9999", "--yes", "--dir", str(repo)]
            )
        self.assertEqual(
            spy.count, 1, "no-flag specs set (status_set path) fires exactly once"
        )

    def test_specs_py_path_with_status_flag_fires_one_offer(self):
        repo = self._repo_with_spec("sp8888", status="draft")
        with _OfferSpy() as spy:
            cli._dispatch(
                [
                    "spec",
                    "set",
                    "--status",
                    "to-review",
                    str(self._spec),
                    "--message",
                    "m",
                    "--dir",
                    str(repo),
                ]
            )
        self.assertEqual(
            spy.count,
            1,
            "--status specs set (specs.py path) fires exactly once, no double-offer",
        )


# --------------------------------------------------------------------------------------
# V-07: dispatch coverage across types (plans, research, specs)
# --------------------------------------------------------------------------------------


class DispatchCoverageTests(unittest.TestCase):
    def _repo(self):
        repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_disp_")))
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        return repo

    def _run_group(self, repo, artifact_type, selector, extra=None):
        argv = [
            "group",
            artifact_type,
            selector,
            "--set",
            "newset",
            "--rename",
            "--apply",
            "--dir",
            str(repo),
        ]
        if extra:
            argv += extra
        with _OfferSpy() as spy:
            cli._dispatch(argv)
        return spy

    def test_group_plans_offers_once(self):
        repo = self._repo()
        _write_plan(
            repo / ".aw" / "records" / "plans",
            id6="dp0001",
            set_id="s",
            order=1,
            slug="a",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        spy = self._run_group(repo, "plans", "dp0001")
        self.assertEqual(spy.count, 1)

    def test_group_research_offers_once(self):
        repo = self._repo()
        _write_research(
            repo,
            set_id="s",
            order=0,
            id6="dr0001",
            slug="a",
            status="intake",
            created="20260101",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        spy = self._run_group(repo, "research", "dr0001")
        self.assertEqual(spy.count, 1)

    def test_group_specs_offers_once_nonplans_coverage(self):
        # Guards PR-003: a non-plans artifact_rename type IS covered by the single dispatch wiring.
        repo = self._repo()
        _write_spec(repo, id6="ds0001", slug="a")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        spy = self._run_group(repo, "specs", "ds0001")
        self.assertEqual(spy.count, 1)


# --------------------------------------------------------------------------------------
# idxuntrack `4r0qp1` E-06: the shared ignored-path guard in offer_commit
# --------------------------------------------------------------------------------------


class IgnoredPathsAreFilteredNotFatal(unittest.TestCase):
    """A gitignored path in the set must not take the REAL artifact's commit down with it.

    MEASURED (2026-09-06) before the guard existed: ``git add -- <ignored>`` exits 1 and stages
    NOTHING, including the non-ignored paths in the same invocation, so ``offer_commit`` returned
    ``error``, created NO commit, and the real artifact silently went uncommitted. That is the
    failure mode this guard converts into a reported skip, and it is what makes a commit-path
    contributor that anyone MISSED non-destructive.
    """

    def _repo(self) -> Path:
        repo = init_repo(Path(tempfile.mkdtemp(prefix="aw_sc_ign_")))
        self.addCleanup(lambda: shutil.rmtree(repo, ignore_errors=True))
        _commit_seed(repo)
        (repo / ".gitignore").write_text("GEN.json\n", encoding="utf-8")
        git(repo, "add", "--", ".gitignore")
        git(repo, "commit", "-q", "-m", "ignore GEN.json")
        return repo

    def test_a_mixed_set_commits_the_real_path_and_skips_the_ignored_one(self):
        repo = self._repo()
        (repo / "real.md").write_text("real\n", encoding="utf-8")
        (repo / "GEN.json").write_text("{}\n", encoding="utf-8")
        before = _head(repo)
        out = git_commit_helper.offer_commit(
            repo, ["real.md", "GEN.json"], message="mixed", assume_yes=True
        )
        self.assertEqual(out.status, git_commit_helper.STATUS_COMMITTED, out.message)
        self.assertEqual(out.staged, ("real.md",))
        self.assertNotEqual(before, _head(repo), "the real artifact must be committed")
        self.assertEqual(_committed_files(repo, _head(repo)), {"real.md"})

    def test_an_all_ignored_set_is_nothing_to_commit_not_error(self):
        repo = self._repo()
        (repo / "GEN.json").write_text("{}\n", encoding="utf-8")
        before = _head(repo)
        out = git_commit_helper.offer_commit(
            repo, ["GEN.json"], message="all ignored", assume_yes=True
        )
        self.assertEqual(
            out.status, git_commit_helper.STATUS_NOTHING_TO_COMMIT, out.message
        )
        self.assertIn("GEN.json", out.message, "the skipped path must be named")
        self.assertEqual(before, _head(repo), "no commit should be made")

    def test_a_TRACKED_file_matching_an_ignore_pattern_is_still_committed(self):
        """The guard must not over-reach: git honors the index over .gitignore, and so must we."""
        repo = self._repo()
        (repo / "GEN.json").write_text("v1\n", encoding="utf-8")
        git(repo, "add", "-f", "--", "GEN.json")
        git(repo, "commit", "-q", "-m", "force-track GEN.json")
        (repo / "GEN.json").write_text("v2\n", encoding="utf-8")
        out = git_commit_helper.offer_commit(
            repo, ["GEN.json"], message="tracked ignored", assume_yes=True
        )
        self.assertEqual(out.status, git_commit_helper.STATUS_COMMITTED, out.message)
        self.assertEqual(out.staged, ("GEN.json",))

    def test_no_force_add_was_introduced(self):
        """Force-adding an ignored path is the exact behavior this Set exists to REMOVE."""
        src = Path(git_commit_helper.__file__).read_text(encoding="utf-8")
        self.assertNotIn('"-f"', src)
        self.assertNotIn('"--force"', src)


if __name__ == "__main__":
    unittest.main()
