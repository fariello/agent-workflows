"""Tests for bklggrad Order 03 (f1dhht): the opt-in backlog-blocking-close pre-commit hook and its
installer wiring.

Covers:
- V-02 the hook (agent_workflows.hooks.backlog_blocking_close_gate.check) refuses (exit 1) a STAGED
  hand-edit-to-done of a release-blocking item with no gate, and passes (exit 0) for HANDOFF and
  DE-GATED (both reconstructable from the staged tree) and for a non-blocking close / unrelated commit.
- V-03 the installer writer (engine.create_backlog_close_gate_hook) is OPT-IN (install=False writes
  nothing), wires the hook on opt-in, is idempotent on re-run, appends to an existing config without
  clobbering it, and is dry-run aware.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine
from agent_workflows.hooks import backlog_blocking_close_gate as HOOK


def _git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )


def _init_git(root: Path):
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@e.com")
    _git(root, "config", "user.name", "T")
    _git(root, "config", "commit.gpgsign", "false")


def _write_item(
    root: Path,
    id6: str,
    *,
    status="done",
    blocks_release: "str | None" = "next",
    setid="demo",
) -> Path:
    d = root / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        f"- Set: {setid}",
        "- Priority: high",
        "- Kind: chore",
        "- Summary: x",
    ]
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += ["", "## Workflow history", "- 2026-01-01 created (t): x", ""]
    p = d / f"20260101-{setid}-01-{id6}-x.backlog.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _write_plan(
    root: Path, id6: str, *, from_backlog: str, blocks_release: str, setid="demo"
) -> Path:
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# IPD: {id6}",
        "",
        "- Date: 2026-08-25",
        "- Kind: child",
        "- Status: approved",
        f"- Set: {setid}",
        "- Order: 1",
        f"- Id: {id6}",
        f"- From-Backlog: {from_backlog}",
        f"- Blocks-Release: {blocks_release}",
        "",
        "## Workflow history",
        "- 2026-08-25 draft (t): x.",
        "",
        "## Goal",
        "x",
    ]
    p = d / f"20260825-{setid}-01-{id6}-x.ipd.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


class HookBehaviorTests(unittest.TestCase):
    """V-02: the hook refuses a staged hand-edit-to-done bypass; passes the legitimacy paths."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _stage(self, p: Path):
        _git(self.root, "add", str(p.relative_to(self.root)))

    def test_refuses_staged_hand_edit_to_done_without_gate(self):
        p = _write_item(self.root, "aaa111", status="done", blocks_release="next")
        self._stage(p)
        rc, msgs = HOOK.check(self.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("aaa111" in m for m in msgs))

    def test_passes_handoff(self):
        p = _write_item(self.root, "aaa111", status="done", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        self._stage(p)
        rc, msgs = HOOK.check(self.root)
        self.assertEqual(rc, 0, msgs)

    def test_passes_degated(self):
        # staged item carries NO Blocks-Release -> DE-GATED -> pass
        p = _write_item(self.root, "aaa111", status="done", blocks_release=None)
        self._stage(p)
        rc, _msgs = HOOK.check(self.root)
        self.assertEqual(rc, 0)

    def test_non_blocking_close_unaffected(self):
        p = _write_item(self.root, "aaa111", status="done", blocks_release=None)
        self._stage(p)
        rc, _msgs = HOOK.check(self.root)
        self.assertEqual(rc, 0)

    def test_no_op_when_nothing_staged(self):
        # a done+blocking item present but NOT staged -> commit-scoped no-op (grandfathered history)
        _write_item(self.root, "aaa111", status="done", blocks_release="next")
        rc, _msgs = HOOK.check(self.root)
        self.assertEqual(rc, 0)

    def test_main_entry_exit_codes(self):
        # exit 0 on a clean tree
        self.assertEqual(HOOK.main([]), 0)


class InstallerWiringTests(unittest.TestCase):
    """V-03: opt-in installer writer (create_backlog_close_gate_hook)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _cfg(self) -> Path:
        return self.root / engine.PRE_COMMIT_CONFIG

    def test_default_setup_does_not_wire_hook(self):
        engine.create_setup_artifacts(self.root, use_git=False)
        # the opt-in hook is NOT wired by the default path (no config, or a config without our hook)
        if self._cfg().exists():
            self.assertNotIn(
                "backlog-blocking-close-gate", self._cfg().read_text(encoding="utf-8")
            )

    def test_optout_writes_nothing(self):
        res = engine.create_backlog_close_gate_hook(
            self.root, use_git=False, install=False
        )
        self.assertEqual(res["created"], [])
        self.assertFalse(self._cfg().exists())

    def test_optin_wires_hook(self):
        res = engine.create_backlog_close_gate_hook(
            self.root, use_git=False, install=True
        )
        self.assertIn(engine.PRE_COMMIT_CONFIG, res["created"])
        txt = self._cfg().read_text(encoding="utf-8")
        self.assertIn("id: backlog-blocking-close-gate", txt)
        self.assertIn("python3 -m agent_workflows backlog-blocking-close-gate", txt)
        self.assertIn("pass_filenames: false", txt)

    def test_reinstall_is_idempotent(self):
        engine.create_backlog_close_gate_hook(self.root, use_git=False, install=True)
        res = engine.create_backlog_close_gate_hook(
            self.root, use_git=False, install=True
        )
        self.assertEqual(res["created"], [])
        self.assertTrue(any("already wired" in s for s in res["skipped"]))
        # exactly one occurrence of the hook id
        self.assertEqual(
            self._cfg()
            .read_text(encoding="utf-8")
            .count("id: backlog-blocking-close-gate"),
            1,
        )

    def test_appends_to_existing_config_without_clobber(self):
        self._cfg().write_text(
            "repos:\n  - repo: local\n    hooks:\n      - id: other\n        name: other\n"
            "        entry: echo\n        language: system\n",
            encoding="utf-8",
        )
        res = engine.create_backlog_close_gate_hook(
            self.root, use_git=False, install=True
        )
        txt = self._cfg().read_text(encoding="utf-8")
        self.assertIn("id: other", txt)  # user's hook preserved
        self.assertIn("id: backlog-blocking-close-gate", txt)  # ours appended
        self.assertTrue(any("appended" in n for n in res["notes"]))

    def test_dry_run_writes_nothing(self):
        res = engine.create_backlog_close_gate_hook(
            self.root, use_git=False, install=True, dry_run=True
        )
        self.assertEqual(res["created"], [])
        self.assertFalse(self._cfg().exists())
        self.assertTrue(res["notes"])


if __name__ == "__main__":
    unittest.main()
