"""Behavioral tests for attributable type checking (basegate, run-20261107T023507Z-1895321).

Covers the three consumers of `agent_workflows.typecheck_gate`:

1. lane integration (`runner_shared.check_lane_type_safety`) refuses only errors a lane ADDS
   relative to its base, so an error inherited from main no longer strands every lane;
2. the commit-time hook (`python3 -m agent_workflows.typecheck_gate staged`) judges the STAGED tree
   against HEAD, ignoring unstaged working-tree edits and inherited errors;
3. the run-start gate (`runner_shared.enforce_main_typecheck_gate`) refuses unattended, asks on a
   TTY, and accepts `--allow-failed-checks '<why>'`, recording the outcome.

Every test drives real `git` and real `mypy` over a tiny throwaway `agent_workflows` package, and
asserts on exit codes, returned verdicts, and recorded run state; nothing reads production source.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import render_stream, runner_shared, typecheck_gate, worktree_lease

# Core marks are per test. The bare core tier carries the two load-bearing behaviors (a lane from a
# red main is not refused; an unattended run on a red main refuses), the two cheap gate branches, and
# the flag surface. The rest each spend real mypy runs and live in the thorough tier, so the core
# wall-time budget is not spent on them.

CLEAN = "def f(x: int) -> int:\n    return x\n"
# A no-redef error: the exact class of error that stranded the run.
INHERITED = "def g() -> None:\n    text = 1\n    text: str = ''\n"
# A different, new error a lane introduces.
ADDED = "def h() -> int:\n    return 'nope'\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


class _RepoCase(unittest.TestCase):
    """A throwaway repo whose `agent_workflows` package mypy can check in well under a second."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q", "-b", "main")
        _git(self.repo, "config", "user.email", "t@example.invalid")
        _git(self.repo, "config", "user.name", "t")
        _git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "pyproject.toml").write_text(
            "[tool.mypy]\nignore_missing_imports = true\n", encoding="utf-8"
        )
        self.write("__init__.py", "")
        self.write("a.py", CLEAN)
        self.commit("base")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, name: str, body: str, *, repo: Path | None = None) -> None:
        p = (repo or self.repo) / "agent_workflows" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    def commit(self, msg: str, *, repo: Path | None = None) -> str:
        r = repo or self.repo
        _git(r, "add", "-A")
        _git(r, "commit", "-qm", msg)
        return _git(r, "rev-parse", "HEAD")

    def lane(self, id6: str, files: dict[str, str]):
        base = _git(self.repo, "rev-parse", "HEAD")
        branch = f"aw/lane/{id6}"
        wt = self.root / f"wt-{id6}"
        _git(self.repo, "worktree", "add", "-q", "-b", branch, str(wt))
        for name, body in files.items():
            self.write(name, body, repo=wt)
        self.commit(f"lane {id6}", repo=wt)
        return worktree_lease.WorktreeHandle(
            lane_id=id6, path=wt, branch=branch, base_commit=base
        )


class CompareTreesTests(_RepoCase):
    def test_clean_head_is_ok(self) -> None:
        cmp = typecheck_gate.compare_trees(self.repo, "HEAD", "HEAD")
        self.assertTrue(cmp.ok, cmp)
        self.assertEqual(cmp.new_errors, [])

    def test_error_present_in_base_is_inherited_even_when_its_line_moves(self) -> None:
        self.write("b.py", INHERITED)
        base = self.commit("main breaks types")
        # Insert lines ABOVE the error so its line number (and the "line N" in its message) moves.
        self.write("b.py", "# pad\n# pad\n# pad\n" + INHERITED)
        head = self.commit("shift lines")
        cmp = typecheck_gate.compare_trees(self.repo, base, head)
        self.assertTrue(cmp.ok, cmp.new_errors)
        self.assertEqual(cmp.inherited_count, 1)

    def test_a_new_error_is_reported_and_an_inherited_one_is_not(self) -> None:
        self.write("b.py", INHERITED)
        base = self.commit("main breaks types")
        self.write("c.py", ADDED)
        head = self.commit("lane adds an error")
        cmp = typecheck_gate.compare_trees(self.repo, base, head)
        self.assertFalse(cmp.ok)
        self.assertEqual(len(cmp.new_errors), 1, cmp.new_errors)
        self.assertIn("c.py", cmp.new_errors[0])
        self.assertEqual(cmp.inherited_count, 1)

    def test_a_second_copy_of_an_inherited_error_counts_as_new(self) -> None:
        self.write("b.py", INHERITED)
        base = self.commit("one copy")
        self.write("b.py", INHERITED + "\n\n" + INHERITED.replace("def g", "def g2"))
        head = self.commit("two copies")
        cmp = typecheck_gate.compare_trees(self.repo, base, head)
        self.assertEqual(len(cmp.new_errors), 1, cmp.new_errors)


class LaneIntegrationTypecheckTests(_RepoCase):
    @pytest.mark.core
    def test_lane_branched_from_a_red_main_is_NOT_refused_for_mains_error(self) -> None:
        self.write("b.py", INHERITED)
        self.commit("hand commit breaks main")
        handle = self.lane("lan001", {"d.py": CLEAN.replace("def f", "def d")})
        ok, reason = runner_shared.check_lane_type_safety(
            self.repo, handle, ["agent_workflows/d.py"]
        )
        self.assertTrue(ok, reason)
        self.assertEqual(reason, "")

    def test_lane_that_adds_an_error_is_refused_naming_only_its_error(self) -> None:
        self.write("b.py", INHERITED)
        self.commit("hand commit breaks main")
        handle = self.lane("lan002", {"c.py": ADDED})
        ok, reason = runner_shared.check_lane_type_safety(
            self.repo, handle, ["agent_workflows/c.py"]
        )
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("type check failed:"), reason)
        self.assertIn("c.py", reason)
        self.assertNotIn("b.py", reason)

    def test_full_integration_merges_a_lane_over_an_inherited_error(self) -> None:
        self.write("b.py", INHERITED)
        self.commit("hand commit breaks main")
        handle = self.lane("lan003", {"d.py": CLEAN.replace("def f", "def d")})
        integrated, reason, _kind = runner_shared.integrate_lane_branch(
            self.repo,
            handle,
            "lan003",
            lambda _diff, _files: True,
            host_label="test",
            run_checked=lambda cmd, **kw: (
                subprocess.run(
                    cmd, check=True, capture_output=True, text=True, **kw
                ).stdout
            ),
            action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
        )
        self.assertNotIn("aw-integration-cause=typecheck", reason)
        self.assertTrue(integrated, reason)
        self.assertTrue((self.repo / "agent_workflows" / "d.py").is_file())


class StagedHookTests(_RepoCase):
    def _run_hook(self) -> subprocess.CompletedProcess:
        """Run the hook's real entry point, exactly as `.pre-commit-config.yaml` invokes it.

        The fixture repo has its OWN `agent_workflows/` directory (the package mypy checks), which
        would shadow the toolkit on `sys.path[0]`; so the toolkit is loaded by path and `cwd` is the
        fixture repo, which is what the hook runs in.
        """
        import os

        toolkit = str(Path(typecheck_gate.__file__).resolve().parents[1])
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from agent_workflows import typecheck_gate as t; "
            "raise SystemExit(t.main(['--repo', '.', 'staged']))"
        )
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        return subprocess.run(
            [sys.executable, "-c", code, toolkit],
            cwd=self.repo,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_staging_a_new_error_refuses_the_commit(self) -> None:
        self.write("c.py", ADDED)
        _git(self.repo, "add", "agent_workflows/c.py")
        proc = self._run_hook()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("adds 1 mypy error", proc.stdout)
        self.assertIn("c.py", proc.stdout)

    def test_an_unstaged_broken_edit_does_not_block_a_clean_staged_change(self) -> None:
        self.write("d.py", CLEAN.replace("def f", "def d"))
        _git(self.repo, "add", "agent_workflows/d.py")
        # A co-worker's broken, UNSTAGED edit in the same checkout.
        self.write("a.py", ADDED)
        proc = self._run_hook()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_an_error_already_on_HEAD_does_not_block_an_unrelated_commit(self) -> None:
        self.write("b.py", INHERITED)
        self.commit("red HEAD")
        self.write("d.py", CLEAN.replace("def f", "def d"))
        _git(self.repo, "add", "agent_workflows/d.py")
        proc = self._run_hook()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("HEAD already carries 1", proc.stdout)

    def test_no_package_file_staged_skips_without_running_mypy(self) -> None:
        (self.repo / "notes.txt").write_text("x\n", encoding="utf-8")
        _git(self.repo, "add", "notes.txt")
        out = io.StringIO()
        self.assertEqual(typecheck_gate.staged_main(self.repo, out=out), 0)
        self.assertEqual(out.getvalue(), "")


class MainTypecheckGateTests(_RepoCase):
    def make_run(self, action: str = "execute"):
        run_dir = self.root / "run"
        run_dir.mkdir()
        state = {
            "run_id": "run-test",
            "queue": [
                {"id6": "itm001", "action": action, "status": "pending", "attempts": []}
            ],
            "options": {},
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return run_dir, state

    def events(self, run_dir: Path) -> list[dict]:
        p = run_dir / "events.jsonl"
        return [
            e
            for e in (
                json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x
            )
            if e.get("event") == "main-typecheck-gate"
        ]

    def gate(self, run_dir, state, **kw):
        return runner_shared.enforce_main_typecheck_gate(
            run_dir,
            state,
            repo=self.repo,
            write_report_fn=lambda *_a: None,
            **kw,
        )

    def break_main(self) -> None:
        self.write("b.py", INHERITED)
        self.commit("red main")

    def test_clean_main_proceeds_silently(self) -> None:
        run_dir, state = self.make_run()
        d = self.gate(run_dir, state, interactive=False)
        self.assertTrue(d.proceed)
        self.assertTrue(d.applied)
        self.assertEqual(self.events(run_dir)[-1]["errors"], 0)

    @pytest.mark.core
    def test_red_main_unattended_REFUSES_and_records_it(self) -> None:
        self.break_main()
        run_dir, state = self.make_run()
        d = self.gate(run_dir, state, interactive=False)
        self.assertFalse(d.proceed)
        self.assertIn("already FAILS", d.message)
        self.assertIn("--allow-failed-checks", d.message)
        refusal = render_stream.refusal_of_item(state["queue"][0])
        self.assertEqual(refusal.code, runner_shared.MAIN_TYPECHECK_REFUSAL_CODE)
        self.assertFalse(self.events(run_dir)[-1]["proceed"])
        on_disk = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        self.assertIn("main_typecheck_refusal", on_disk)

    def test_red_main_with_flag_proceeds_and_records_the_justification(self) -> None:
        self.break_main()
        run_dir, state = self.make_run()
        d = self.gate(
            run_dir, state, interactive=False, justification="fixing it in Order 01"
        )
        self.assertTrue(d.proceed)
        self.assertEqual(d.override, "flag")
        self.assertEqual(
            state["options"]["allow_failed_checks"], "fixing it in Order 01"
        )
        ev = self.events(run_dir)[-1]
        self.assertEqual(ev["justification"], "fixing it in Order 01")
        self.assertTrue(ev["proceed"])

    def test_red_main_interactive_warns_and_y_proceeds(self) -> None:
        self.break_main()
        run_dir, state = self.make_run()
        asked: list[str] = []
        d = self.gate(
            run_dir, state, interactive=True, prompt=lambda q: asked.append(q) or "y"
        )
        self.assertTrue(d.proceed)
        self.assertEqual(d.override, "interactive")
        self.assertEqual(len(asked), 1)
        self.assertIn("WARNING", asked[0])
        self.assertIn("b.py", asked[0])

    def test_red_main_interactive_default_is_NO(self) -> None:
        self.break_main()
        for answer in ("", None, "n"):
            with self.subTest(answer=answer):
                run_dir, state = self.make_run()
                d = self.gate(
                    run_dir, state, interactive=True, prompt=lambda _q, a=answer: a
                )
                self.assertFalse(d.proceed)
                import shutil

                shutil.rmtree(run_dir)

    def test_a_repo_without_mypy_configuration_is_not_gated(self) -> None:
        self.break_main()
        (self.repo / "pyproject.toml").write_text(
            "[project]\nname = 'x'\n", encoding="utf-8"
        )
        self.commit("drop mypy config")
        run_dir, state = self.make_run()
        d = self.gate(run_dir, state, interactive=False)
        self.assertTrue(d.proceed)
        self.assertFalse(d.applied)

    @pytest.mark.core
    def test_review_only_queue_is_not_gated(self) -> None:
        self.break_main()
        run_dir, state = self.make_run(action="review")
        d = self.gate(run_dir, state, interactive=False)
        self.assertTrue(d.proceed)
        self.assertFalse(d.applied)

    @pytest.mark.core
    def test_an_unavailable_checker_warns_and_proceeds(self) -> None:
        self.break_main()
        run_dir, state = self.make_run()
        d = self.gate(
            run_dir,
            state,
            interactive=False,
            check_tree_fn=lambda *_a, **_k: typecheck_gate.MypyRun(
                ok=False, failure="mypy missing"
            ),
        )
        self.assertTrue(d.proceed)
        self.assertEqual(self.events(run_dir)[-1]["unavailable"], "mypy missing")


@pytest.mark.core
class FlagSurfaceTests(unittest.TestCase):
    def test_flag_is_registered_on_both_hosts_and_refuses_an_empty_reason(self) -> None:
        import contextlib

        from agent_workflows import agy_runipd, oc_runipd

        for host in (oc_runipd, agy_runipd):
            with self.subTest(host=host.__name__):
                parser = host.build_parser()
                args = parser.parse_args(
                    ["start", "sel", "--allow-failed-checks", " why "]
                )
                frozen = runner_shared.freeze_run_policy_flags(args)
                self.assertEqual(frozen["allow_failed_checks"], "why")
                for bad in (["--allow-failed-checks"], ["--allow-failed-checks", "  "]):
                    err = io.StringIO()
                    with (
                        self.assertRaises(SystemExit) as cm,
                        contextlib.redirect_stderr(err),
                    ):
                        parser.parse_args(["start", "sel", *bad])
                    self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
