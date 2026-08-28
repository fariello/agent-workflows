"""Tests for ipddeps Order mp88bl: the opt-in ipd-dependency-statement-gate pre-commit hook.

* V-01 - the hook refuses a staged malformed/dangling/cyclic Item-Dependencies (exit 1, matching
  check.ipd-dependency-* rule ID), passes a valid statement / unrelated commit / a pre-existing
  finding in an UNTOUCHED file (commit-scoping), and its rule IDs match what the shared evaluator
  (aw check) reports for the same fixture (delegation to the one predicate, no divergence).
* V-02 - engine.create_dependency_gate_hook is OPT-IN: default setup does not wire it; install=True
  wires it (create/append); a second install is idempotent; install=False and dry_run write nothing.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import engine
from agent_workflows import ipd_schema as S
from agent_workflows.hooks import ipd_dependency_statement_gate as HOOK


def _git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )


def _init_git(root: Path):
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@e.com")
    _git(root, "config", "user.name", "T")
    _git(root, "config", "commit.gpgsign", "false")


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_depgate_"))
    _init_git(d)
    (d / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (d / ".aw" / "config").mkdir(parents=True)
    # cutover active in the past so dependency mandatoriness applies to these plans
    (d / ".aw" / "config" / "project.json").write_text(
        '{"dependency_schema_cutover": {"date": "2020-01-01"}}', encoding="utf-8"
    )
    return d


def _plan_text(*, id6: str, order: int, item_deps: str, status: str = "draft") -> str:
    return (
        f"# IPD: {id6}\n\n- Date: 2026-08-27\n- Kind: child\n- Scope-Paths: x.py\n"
        f"- Item-Dependencies: {item_deps}\n- Status: {status}\n- Set: demo\n"
        f"- Order: {order}\n- Id: {id6}\n\n## Workflow history\n- 2026-08-27 draft (t): x\n\n## Goal\ng\n"
    )


def _write_plan(repo: Path, *, id6, order, item_deps, status="draft") -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20260827-demo-{order:02d}-{id6}-p.ipd.md"
    )
    p.write_text(
        _plan_text(id6=id6, order=order, item_deps=item_deps, status=status),
        encoding="utf-8",
    )
    return p


def _stage(repo: Path, *paths: Path):
    rels = [str(p.relative_to(repo)) for p in paths]
    _git(repo, "add", "--", *rels)


def _commit_all(repo: Path, msg="seed"):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


# --------------------------------------------------------------------------------------
# V-01: the hook
# --------------------------------------------------------------------------------------


class HookRefusalTests(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def test_refuses_staged_malformed(self):
        p = _write_plan(
            self.repo,
            id6="aaaaaa",
            order=1,
            item_deps="executed:aaaaaa, executed:aaaaaa",
        )
        _stage(self.repo, p)
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 1)
        self.assertTrue(any(S.RULE_IPD_DEP_MALFORMED in m for m in msgs), msgs)

    def test_refuses_staged_dangling(self):
        p = _write_plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        _stage(self.repo, p)
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 1)
        self.assertTrue(any(S.RULE_IPD_DEP_DANGLING in m for m in msgs), msgs)

    def test_refuses_staged_cycle(self):
        a = _write_plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:bbbbbb")
        b = _write_plan(self.repo, id6="bbbbbb", order=2, item_deps="executed:aaaaaa")
        _stage(self.repo, a, b)
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 1)
        self.assertTrue(any(S.RULE_IPD_DEP_CYCLE in m for m in msgs), msgs)

    def test_passes_valid_statement(self):
        p = _write_plan(self.repo, id6="aaaaaa", order=1, item_deps="none")
        _stage(self.repo, p)
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 0, msgs)

    def test_no_op_when_nothing_staged(self):
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 0)
        self.assertEqual(msgs, [])

    def test_unrelated_commit_passes(self):
        # stage a non-IPD file only
        (self.repo / "src.txt").write_text("hi\n", encoding="utf-8")
        _stage(self.repo, self.repo / "src.txt")
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 0, msgs)

    def test_commit_scoping_untouched_file_not_blocked(self):
        # A dangling IPD is COMMITTED (pre-existing, untouched by the next commit); then an unrelated
        # file is staged. The hook must NOT block on the pre-existing dangling finding.
        _write_plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        _commit_all(self.repo, "seed with a pre-existing dangling plan")
        (self.repo / "unrelated.txt").write_text("x\n", encoding="utf-8")
        _stage(self.repo, self.repo / "unrelated.txt")
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(
            rc, 0, f"pre-existing untouched dangling must not block: {msgs}"
        )

    def test_draft_unresolved_is_committable(self):
        # OQ-01: a plain draft carrying `unresolved` is a legitimate stub -> not blocked.
        p = _write_plan(
            self.repo, id6="aaaaaa", order=1, item_deps="unresolved", status="draft"
        )
        _stage(self.repo, p)
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 0, msgs)

    def test_unresolved_blocks_when_advancing(self):
        # OQ-01: `unresolved` blocks when the staged plan is advancing to a blocking phase.
        p = _write_plan(
            self.repo, id6="aaaaaa", order=1, item_deps="unresolved", status="approved"
        )
        _stage(self.repo, p)
        rc, msgs = HOOK.check(self.repo)
        self.assertEqual(rc, 1)
        self.assertTrue(any(S.RULE_IPD_DEP_UNRESOLVED in m for m in msgs), msgs)

    def test_rule_ids_match_aw_check(self):
        # Delegation to the one shared evaluator: the hook's rule IDs equal what the evaluator (aw
        # check) reports for the same dangling fixture.
        p = _write_plan(self.repo, id6="aaaaaa", order=1, item_deps="executed:zzzzzz")
        _stage(self.repo, p)
        _rc, hook_msgs = HOOK.check(self.repo)
        hook_rules = {m.split(": ")[1] for m in hook_msgs}
        # committing so the evaluator (which reads on-disk) sees the same content
        _commit_all(self.repo, "commit dangling for check parity")
        check_rules = {
            d.rule
            for d in ce.check_ipd_dependencies(self.repo)
            if "aaaaaa" in d.location
        }
        self.assertTrue(
            hook_rules.issubset(check_rules) or check_rules.issubset(hook_rules)
        )
        self.assertIn(S.RULE_IPD_DEP_DANGLING, hook_rules)
        self.assertIn(S.RULE_IPD_DEP_DANGLING, check_rules)

    def test_main_entry_exit_codes(self):
        # no-op repo -> 0
        self.assertEqual(HOOK.main([]), 0)


# --------------------------------------------------------------------------------------
# V-02: opt-in install writer
# --------------------------------------------------------------------------------------


class InstallWriterTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="aw_depgate_inst_"))
        _init_git(self.repo)

    def _config_text(self) -> str:
        pc = self.repo / ".pre-commit-config.yaml"
        return pc.read_text(encoding="utf-8") if pc.exists() else ""

    def test_default_setup_does_not_wire_hook(self):
        # install=False (the default posture) writes nothing.
        res = engine.create_dependency_gate_hook(
            self.repo, use_git=False, install=False
        )
        self.assertEqual(res["created"], [])
        self.assertNotIn("ipd-dependency-statement-gate", self._config_text())

    def test_optin_wires_hook_fresh_config(self):
        res = engine.create_dependency_gate_hook(self.repo, use_git=False, install=True)
        self.assertTrue(res["created"])
        self.assertIn("ipd-dependency-statement-gate", self._config_text())

    def test_reinstall_is_idempotent(self):
        engine.create_dependency_gate_hook(self.repo, use_git=False, install=True)
        res = engine.create_dependency_gate_hook(self.repo, use_git=False, install=True)
        self.assertEqual(res["created"], [])
        self.assertTrue(res["skipped"])
        # exactly one occurrence of the hook id
        self.assertEqual(
            self._config_text().count("id: ipd-dependency-statement-gate"), 1
        )

    def test_appends_to_existing_config_without_clobber(self):
        pc = self.repo / ".pre-commit-config.yaml"
        pc.write_text(
            "repos:\n  - repo: local\n    hooks:\n      - id: my-existing-hook\n"
            "        name: mine\n        entry: echo\n        language: system\n",
            encoding="utf-8",
        )
        res = engine.create_dependency_gate_hook(self.repo, use_git=False, install=True)
        text = self._config_text()
        self.assertIn("my-existing-hook", text)  # not clobbered
        self.assertIn("ipd-dependency-statement-gate", text)  # appended
        self.assertTrue(res["notes"])

    def test_dry_run_writes_nothing(self):
        res = engine.create_dependency_gate_hook(
            self.repo, use_git=False, install=True, dry_run=True
        )
        self.assertEqual(res["created"], [])
        self.assertNotIn("ipd-dependency-statement-gate", self._config_text())
        self.assertTrue(res["notes"])


if __name__ == "__main__":
    unittest.main()
