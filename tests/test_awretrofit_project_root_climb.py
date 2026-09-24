"""Regression tests for IPD awretrofit Order 06: repo-scoped verbs climb to the project root.

Maintainer report (release-review run 20260817-153418): `aw att` from a repo SUBDIRECTORY printed
nothing (repo-scoped verbs resolved bare cwd with no upward climb), and from a markerless dir the
empty output was indistinguishable from a clean project. This adds a git-style `find_project_root`
climb + a verbose no-project message, and these tests lock both behaviors (fail-before/pass-after).
"""

from __future__ import annotations

import argparse
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import project_context as pc


def _make_project(root: Path) -> None:
    """Materialize a minimal AW project root (a `.aw/` with a durable class dir)."""
    (root / ".aw" / "records" / "plans").mkdir(parents=True)
    (root / ".aw" / "system").mkdir(parents=True)


class FindProjectRootTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp) / "repo"
        _make_project(self.repo)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_from_repo_root(self):
        self.assertEqual(pc.find_project_root(self.repo), self.repo.resolve())

    def test_from_nested_subdir(self):
        nested = self.repo / ".aw" / "records" / "plans"
        self.assertEqual(pc.find_project_root(nested), self.repo.resolve())
        deep = self.repo / "a" / "b" / "c"
        deep.mkdir(parents=True)
        self.assertEqual(pc.find_project_root(deep), self.repo.resolve())

    def test_markerless_returns_none(self):
        bare = Path(self.tmp) / "nowhere"
        bare.mkdir()
        self.assertIsNone(pc.find_project_root(bare))

    def test_legacy_agents_marker(self):
        legacy = Path(self.tmp) / "legacyrepo"
        (legacy / ".agents" / "plans").mkdir(parents=True)
        self.assertEqual(
            pc.find_project_root(legacy / ".agents" / "plans"), legacy.resolve()
        )

    def test_stray_nested_aw_is_not_a_root(self):
        """A bare `.aw/` that holds only runtime state (no durable class) must NOT be a root -
        prevents the false positive where a stray `.aw/state/.aw/` shadows the real root."""
        stray = self.repo / ".aw" / "state" / ".aw" / "state"
        stray.mkdir(parents=True)
        # Climbing from inside the stray still resolves the REAL repo root, not the stray dir.
        self.assertEqual(
            pc.find_project_root(self.repo / ".aw" / "state"), self.repo.resolve()
        )

    def test_bare_git_ancestor_is_not_a_root(self):
        """A `.git` dir with no AW marker is not an AW project root (OQ-01)."""
        gitonly = Path(self.tmp) / "gitonly"
        (gitonly / ".git").mkdir(parents=True)
        self.assertIsNone(pc.find_project_root(gitonly))


class AttentionClimbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp) / "repo"
        _make_project(self.repo)
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_attention(self, extra=None):
        from agent_workflows import attention

        args = argparse.Namespace(
            dir=None, check=False, agent=False, format=None, all=False, no_color=True
        )
        if extra:
            for k, v in extra.items():
                setattr(args, k, v)
        # capture stdout + stderr + exit code
        import sys

        out, err = io.StringIO(), io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            rc = attention.run(args)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return rc, out.getvalue(), err.getvalue()

    def test_subdir_resolves_same_as_top(self):
        """`aw attention` from a repo subdir produces the same board as from the top."""
        os.chdir(self.repo)
        rc_top, out_top, _ = self._run_attention()
        sub = self.repo / ".aw" / "records" / "plans"
        os.chdir(sub)
        rc_sub, out_sub, _ = self._run_attention()
        self.assertEqual(rc_top, rc_sub)
        self.assertEqual(out_top, out_sub)

    def test_markerless_prints_no_project_message(self):
        """From a markerless dir, attention emits the verbose no-project guidance (not empty)."""
        bare = Path(self.tmp) / "nowhere"
        bare.mkdir()
        os.chdir(bare)
        rc, out, err = self._run_attention()
        self.assertEqual(rc, 3)
        self.assertIn("no AW project found", err)
        self.assertIn("--dir", err)
        self.assertEqual(out, "")

    def test_explicit_dir_bypasses_climb(self):
        """An explicit --dir is honored verbatim (no climb) even from a markerless cwd."""
        bare = Path(self.tmp) / "nowhere2"
        bare.mkdir()
        os.chdir(bare)
        rc, out, err = self._run_attention(extra={"dir": str(self.repo)})
        # With an explicit project --dir, it runs normally (no no-project message).
        self.assertNotIn("no AW project found", err)

    def test_check_on_markerless_is_valid(self):
        """--check stays fail-closed-valid (exit 0) when there is no project (nothing to violate)."""
        bare = Path(self.tmp) / "nowhere3"
        bare.mkdir()
        os.chdir(bare)
        rc, out, err = self._run_attention(extra={"check": True})
        self.assertEqual(rc, 0)
        self.assertIn("valid", out)


class ClimbMutationProbe(unittest.TestCase):
    """Falsifiable: with the climb reverted to bare-cwd, a subdir run finds no project (the pre-fix
    bug), proving the climb is load-bearing."""

    def test_reverting_climb_breaks_subdir(self):
        tmp = tempfile.mkdtemp()
        try:
            repo = Path(tmp) / "repo"
            _make_project(repo)
            sub = repo / ".aw" / "records" / "plans"
            # Real resolver: climbs to the repo root from the subdir.
            with mock.patch(
                "agent_workflows.project_context.Path.cwd", return_value=sub
            ):
                self.assertEqual(pc.resolve_verb_repo_root(None), repo.resolve())
            # Mutated (pre-fix bare-cwd): would return the subdir, which is_project_dir() rejects.
            with mock.patch.object(pc, "find_project_root", lambda start=None: None):
                with mock.patch(
                    "agent_workflows.project_context.Path.cwd", return_value=sub
                ):
                    self.assertEqual(pc.resolve_verb_repo_root(None), sub.resolve())
                    self.assertFalse(pc.is_project_dir(sub))
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


class GitAwareNoProjectMessageTests(unittest.TestCase):
    """IPD nogitmsg `quqyc4` E-06, the message layer (cases (a) and (b)).

    The message used to tell the operator WHERE it looked but never checked whether cwd was a git
    repository, so in the commonest case - a real repo with agent-workflows simply not installed - it
    could not offer the one action that fixes it.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _gitonly(self, name="gitonly"):
        d = Path(self.tmp) / name
        (d / ".git").mkdir(parents=True)
        return d

    def test_a_git_repo_is_named_and_the_install_is_offered(self):
        d = self._gitonly()
        msg = pc.no_project_message("attention", d)
        self.assertIn("IS a git repository, but agent-workflows is not installed", msg)
        self.assertIn(f"aw install {d.resolve().as_posix()}", msg)

    def test_a_git_SUBDIRECTORY_names_the_ROOT_not_the_subdir(self):
        """The probe walks up, so the offered install target is the repo root."""
        d = self._gitonly()
        sub = d / "a" / "b"
        sub.mkdir(parents=True)
        msg = pc.no_project_message("attention", sub)
        self.assertIn(f"aw install {d.resolve().as_posix()}", msg)
        self.assertIn(f"Checked {sub}", msg)

    def test_b_a_NON_git_directory_gets_the_UNCHANGED_three_line_message(self):
        """Byte-for-byte the pre-change text: the three original lines and nothing more."""
        bare = Path(self.tmp) / "nogit"
        bare.mkdir()
        expected = (
            f"aw attention: no AW project found here.\n"
            f"Checked {bare} and its parents for a .aw/ (or legacy .agents/) project directory.\n"
            f"Are you inside your repository? cd into the repo (or a subdirectory of it), "
            f"or pass --dir <repo>."
        )
        self.assertEqual(pc.no_project_message("attention", bare), expected)
        self.assertNotIn("git repository", pc.no_project_message("attention", bare))

    def test_the_three_original_lines_are_PRESERVED_and_the_git_fact_is_APPENDED(self):
        """The maintainer called the original three lines genuinely helpful; this ADDS a fourth
        fact, it does not rewrite them."""
        d = self._gitonly()
        lines = pc.no_project_message("attention", d).splitlines()
        self.assertEqual(lines[0], "aw attention: no AW project found here.")
        self.assertIn("and its parents for a .aw/", lines[1])
        self.assertIn("--dir <repo>", lines[2])
        self.assertEqual(len(lines), 5)

    def test_start_dir_DEFAULTS_to_cwd_so_existing_callers_are_unaffected(self):
        bare = Path(self.tmp) / "defaulting"
        bare.mkdir()
        cwd = os.getcwd()
        os.chdir(bare)
        try:
            self.assertEqual(
                pc.no_project_message("attention"),
                pc.no_project_message("attention", Path.cwd()),
            )
        finally:
            os.chdir(cwd)

    def test_git_root_for_message_answers_the_same_probe(self):
        """E-04 reads the structured answer from here rather than parsing the prose."""
        d = self._gitonly()
        bare = Path(self.tmp) / "nogit2"
        bare.mkdir()
        self.assertEqual(pc.git_root_for_message(d), d.resolve().as_posix())
        self.assertIsNone(pc.git_root_for_message(bare))

    def test_E02_GUARD_the_probe_did_NOT_leak_into_root_detection(self):
        """`find_project_root` stays git-blind (IPD awretrofit Order 06 OQ-01). A message-layer probe
        must never be promoted into the definition of a project."""
        d = self._gitonly()
        self.assertIsNone(pc.find_project_root(d))
        self.assertFalse(pc.is_project_dir(d))


class NoProjectSubprocessMatrixTests(unittest.TestCase):
    """IPD nogitmsg `quqyc4` E-06, the CLI matrix, measured in a REAL subprocess.

    THE CRASH REGRESSION TEST IS THE MOST IMPORTANT ONE HERE. `aw ipd board --agent` outside a
    project used to exit 1 with an unhandled `ValueError` from the `aw.agent/v1` validator, because
    the record carried `exit_code=3` while the schema admits only 0/1/2 and requires an error record
    to carry exactly 2 (backlog `5x195l`). A subprocess is used deliberately: the exit code must be
    the PROCESS code and a traceback must be provably absent from stderr, neither of which an
    in-process call to the handler can demonstrate.
    """

    VERBS = (["attention"], ["ipd", "board"])

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gitonly = Path(self.tmp) / "gitonly"
        (self.gitonly / ".git").mkdir(parents=True)
        self.nogit = Path(self.tmp) / "nogit"
        self.nogit.mkdir()
        self.project = Path(self.tmp) / "repo"
        _make_project(self.project)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, cwd, argv):
        import subprocess
        import sys

        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        env.pop("NO_COLOR", None)
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *argv],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
        )

    def _assert_no_traceback(self, proc, label):
        self.assertNotIn("Traceback", proc.stderr, f"{label} CRASHED:\n{proc.stderr}")
        self.assertNotIn("ValueError", proc.stderr, f"{label} CRASHED:\n{proc.stderr}")

    def test_case_a_human_names_the_git_root_and_offers_the_install(self):
        for argv in self.VERBS:
            with self.subTest(verb=argv):
                p = self._run(self.gitonly, argv)
                self.assertEqual(p.returncode, 3)
                self.assertIn("IS a git repository", p.stderr)
                self.assertIn(
                    f"aw install {self.gitonly.resolve().as_posix()}", p.stderr
                )
                self._assert_no_traceback(p, f"{argv} human")

    def test_case_a_the_verb_NAMES_ITSELF_never_the_nonexistent_aw_plans(self):
        """F-18: `aw ipd board` used to print 'aw plans: no AW project found here.' while `aw plans`
        is not a registered command, misdirecting the operator from inside the help text."""
        p = self._run(self.gitonly, ["ipd", "board"])
        self.assertIn("aw ipd board: no AW project found here.", p.stderr)
        self.assertNotIn("aw plans:", p.stderr)

    def test_case_a_the_named_command_aw_plans_really_is_NOT_registered(self):
        """Pins WHY the previous test matters: the old message named an invalid choice."""
        p = self._run(self.gitonly, ["plans"])
        self.assertEqual(p.returncode, 2)
        self.assertIn("invalid choice", (p.stderr + p.stdout))

    def test_case_b_a_non_git_directory_offers_no_install(self):
        for argv in self.VERBS:
            with self.subTest(verb=argv):
                p = self._run(self.nogit, argv)
                self.assertEqual(p.returncode, 3)
                self.assertIn("no AW project found", p.stderr)
                self.assertNotIn("git repository", p.stderr)
                self.assertNotIn("aw install", p.stderr)

    def test_case_c_inside_a_real_project_the_message_is_NEVER_emitted(self):
        for argv in self.VERBS:
            with self.subTest(verb=argv):
                p = self._run(self.project, argv)
                self.assertNotIn("no AW project found", p.stderr)
                self.assertNotIn("IS a git repository", p.stderr)
                self._assert_no_traceback(p, f"{argv} in project")

    def test_case_d1_explicit_dir_at_a_real_project_works_unchanged(self):
        for argv in self.VERBS:
            with self.subTest(verb=argv):
                p = self._run(self.nogit, [*argv, "--dir", str(self.project)])
                self.assertNotIn("no AW project found", p.stderr)
                self._assert_no_traceback(p, f"{argv} --dir project")

    def test_case_d2_CHARACTERIZES_the_silent_explicit_dir_gap_it_does_NOT_fix_it(self):
        """F-17, PINNED AS-IS, NOT FIXED. Both message branches are guarded by `not explicit_dir`, so
        an operator who explicitly names a git-but-not-AW directory gets NO output and a SUCCESS exit
        code. That is arguably worse than the path this plan fixes, but changing the guard would
        change which inputs produce a cannot-run, which is a contract decision of its own. This test
        is a BASELINE for that later fix, and it must be UPDATED (not deleted) when it lands."""
        p = self._run(self.nogit, ["attention", "--dir", str(self.gitonly)])
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(p.stderr.strip(), "")

    def test_case_e_the_agent_surface_EMITS_A_VALID_RECORD_AND_DOES_NOT_CRASH(self):
        """THE CRASH REGRESSION TEST. Fails against pre-change code for `ipd board`: exit 1, empty
        stdout, `ValueError: ... Field 'exit' must be an integer in (0, 1, 2), got '3'`."""
        import json

        from agent_workflows import agent_schema

        for argv in self.VERBS:
            with self.subTest(verb=argv):
                p = self._run(self.gitonly, [*argv, "--agent"])
                self._assert_no_traceback(p, f"{argv} --agent")
                self.assertEqual(p.returncode, 2)
                self.assertTrue(p.stdout.strip(), "STDOUT WAS EMPTY")
                rec = json.loads(p.stdout.splitlines()[0])
                self.assertEqual(rec["schema"], "aw.agent/v1")
                self.assertEqual(rec["outcome"], "cannot-run")
                self.assertEqual(rec["exit"], 2)
                self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_case_e_the_install_offer_is_STRUCTURED_in_the_next_field(self):
        """E-04. `aw install .` and NOT the absolute root: `agent_schema` refuses an absolute home
        path in any string field, so the absolute form would raise in the renderer and reintroduce
        the crash (decision 03-quqyc4-D2). `aw install` defaults to cwd, so `.` is runnable."""
        import json

        for argv in self.VERBS:
            with self.subTest(verb=argv):
                rec = json.loads(
                    self._run(self.gitonly, [*argv, "--agent"]).stdout.splitlines()[0]
                )
                self.assertEqual(rec["next"], "aw install .")

    def test_case_e_a_NON_git_directory_leaves_next_NULL(self):
        import json

        for argv in self.VERBS:
            with self.subTest(verb=argv):
                rec = json.loads(
                    self._run(self.nogit, [*argv, "--agent"]).stdout.splitlines()[0]
                )
                self.assertIsNone(rec["next"])

    def test_case_e_the_machine_payload_carries_NO_absolute_path(self):
        """The human message names the directory (which is what helps an operator); the machine
        payload must not, or the record is refused outright."""
        for argv in self.VERBS:
            for flag in ("--agent", "--json"):
                with self.subTest(verb=argv, flag=flag):
                    out = self._run(self.gitonly, [*argv, flag]).stdout
                    self.assertNotIn(str(self.gitonly), out)
                    self.assertNotIn("/home/", out)

    def test_case_f_the_json_surface_agrees_with_the_agent_surface(self):
        """The two machine renderers must not diverge on this condition: `--json` used to exit 3
        while `--agent` died, and now both answer 2."""
        import json

        for argv in self.VERBS:
            with self.subTest(verb=argv):
                p = self._run(self.gitonly, [*argv, "--json"])
                self._assert_no_traceback(p, f"{argv} --json")
                self.assertEqual(p.returncode, 2)
                obj = json.loads(p.stdout)
                self.assertEqual(obj["status"], "cannot-run")
                self.assertEqual(obj["exit_code"], 2)
                self.assertEqual(
                    obj["next_actions"][0]["command"],
                    "aw install .",
                )

    def test_case_g_attention_check_outside_a_project_is_STILL_fail_closed_valid(self):
        """That branch precedes the message and deliberately answers 'nothing to violate'. It must
        not regress to a cannot-run."""
        p = self._run(self.gitonly, ["attention", "--check"])
        self.assertEqual(p.returncode, 0)
        self.assertIn("valid", p.stdout)


if __name__ == "__main__":
    unittest.main()
