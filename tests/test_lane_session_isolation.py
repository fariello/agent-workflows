#!/usr/bin/env python3
"""lanesess (xd9sll): an isolated lane turn must never inherit a session bound to another tree.

Sessions were keyed per SET while worktrees are allocated per ITEM, so lanes 2..N of a set were
launched with lane 1's session id. An opencode/Antigravity session carries its own project/directory
binding, which OVERRIDES the `--dir`/cwd the driver passes, so the turn silently executed in the
PREVIOUS lane's worktree. Every main-repo path is then "external", the external_directory gate
(qyaime) asks with no answerer, and the turn dies at the stall watchdog.

Evidence this reproduces (run-20260829T153858Z-3207626): qcqhj7's turn created its instance in its
own lane, then re-bootstrapped 8zgybk's lane 1s later and streamed under 8zgybk's session id; four
consecutive lanes were lost to 600s stalls.

The fix must hold in BOTH drivers, so a symmetry test asserts a one-driver-only fix cannot pass.
"""

import ast
import inspect
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd
from agent_workflows import oc_runipd as driver


def _base_state(repo: str, session: str | None = None) -> dict:
    state: dict = {
        "repo": repo,
        "run_id": "run-test",
        "set_sessions": {},
        "options": {"opencode": "/bin/false", "auto": True},
    }
    if session is not None:
        state["session_id"] = session
        state["set_sessions"]["demo"] = session
    return state


def _item(id6: str = "bbbbbb") -> dict:
    return {"id6": id6, "setid": "demo", "position": 2, "action": "execute"}


def _argv_for(work_dir: str | None, session: str | None = "ses_LANE1") -> list[str]:
    """Build the child argv the driver would launch, without running anything."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        run_dir = root / "run"
        (run_dir / "sessions").mkdir(parents=True)
        plan = root / "plan.ipd.md"
        plan.write_text("- Id: bbbbbb\n", encoding="utf-8")
        prompt = root / "prompt.md"
        prompt.write_text("do the thing\n", encoding="utf-8")

        captured: dict = {}

        def fake_popen(argv, **kwargs):  # pragma: no cover - we raise before use
            captured["argv"] = list(argv)
            raise RuntimeError("stop-before-launch")

        import subprocess as _sp

        real_popen = _sp.Popen
        _sp.Popen = fake_popen  # type: ignore[assignment]
        try:
            driver.run_opencode(
                _base_state(str(root), session),
                run_dir,
                _item(),
                plan,
                prompt,
                1,
                work_dir=work_dir,
            )
        except Exception:
            pass
        finally:
            _sp.Popen = real_popen  # type: ignore[assignment]
        return captured.get("argv", [])


class LaneSessionIsolationTests(unittest.TestCase):
    def test_isolated_turn_does_not_inherit_a_session(self):
        """An isolated lane gets a FRESH session: no --session flag is passed."""
        argv = _argv_for(work_dir="/tmp/lane-qcqhj7")
        self.assertNotIn(
            "--session",
            argv,
            "an isolated lane turn must not inherit a session bound to another tree; "
            f"argv was {argv!r}",
        )

    def test_isolated_turn_still_targets_its_own_worktree(self):
        """The fix must not disturb --dir: the lane still runs in its OWN tree."""
        argv = _argv_for(work_dir="/tmp/lane-qcqhj7")
        self.assertIn("--dir", argv)
        self.assertEqual(
            argv[argv.index("--dir") + 1],
            "/tmp/lane-qcqhj7",
            f"argv was {argv!r}",
        )

    def test_non_isolated_turn_still_reuses_the_session(self):
        """No regression: without isolation, session continuity is preserved."""
        argv = _argv_for(work_dir=None)
        self.assertIn(
            "--session",
            argv,
            f"a non-isolated turn must still reuse its set session; argv was {argv!r}",
        )
        self.assertEqual(argv[argv.index("--session") + 1], "ses_LANE1")

    def test_promotion_of_a_lane_session_is_gated_on_work_dir(self):
        """The post-turn writeback must not promote an isolated lane's session to the set.

        Promoting it would re-arm the carryover AND make the set-consistency check fire on every
        lane after the first ("changed session unexpectedly"), aborting the whole run.
        """
        src = inspect.getsource(driver.execute_item)
        tree = ast.parse(ast.unparse(ast.parse(src)))
        promotes_set_sessions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Subscript)
            and isinstance(node.value.slice, ast.Constant)
            and node.value.slice.value == "set_sessions"
        ]
        self.assertTrue(
            promotes_set_sessions,
            "expected execute_item to still write state['set_sessions'][...] somewhere",
        )
        guarded = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.If)
            and "work_dir" in ast.unparse(node.test)
            and "set_sessions" in ast.unparse(node)
        ]
        self.assertTrue(
            guarded,
            "the set_sessions promotion must sit under a work_dir guard so an isolated "
            "lane's fresh session is never promoted to the set",
        )

    def test_both_drivers_are_fixed_symmetrically(self):
        """A one-driver-only fix must FAIL: agy and oc must both drop the inherited session."""
        for name, func in (
            ("oc_runipd.run_opencode", driver.run_opencode),
            ("agy_runipd.execute_item", agy_runipd.execute_item),
        ):
            src = inspect.getsource(func)
            self.assertIn(
                "xd9sll",
                src,
                f"{name} must carry the lanesess fix (traceable to backlog xd9sll)",
            )

    def test_agy_isolated_lane_clears_session_and_continue(self):
        """agy must ALSO not fall back to --continue, which resumes the prior conversation."""
        src = inspect.getsource(agy_runipd.execute_item)
        tree = ast.parse(ast.unparse(ast.parse(src)))
        clears = {
            "session_id": False,
            "use_continue": False,
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in clears:
                    value = ast.unparse(node.value)
                    if value in ("None", "False"):
                        clears[target.id] = True
        self.assertTrue(
            clears["session_id"],
            "agy must clear the inherited session_id for an isolated lane",
        )
        self.assertTrue(
            clears["use_continue"],
            "agy must clear use_continue for an isolated lane; otherwise --continue "
            "resumes the previous lane's conversation and reintroduces the carryover",
        )


if __name__ == "__main__":
    unittest.main()
