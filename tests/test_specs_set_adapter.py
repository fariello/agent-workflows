"""Tests for specs.run_set adapter delegating to status_set.run_set_command (IPD m94eht).

Covers:
1. Hand-built Namespace shapes used by existing tests across direct callers.
2. The --date override pass-through on specs.
3. The validate_spec refusal leaving the file byte-identical on disk.
4. The confirmation gate behavior (rc 2 for agent/JSON caller without --yes).
5. Selector widening (id6 / setid resolution).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import specs


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SpecsSetAdapterTests(unittest.TestCase):
    """Test suite for specs.run_set adapter delegation."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_adapter_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.tmp,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Runner"],
            cwd=self.tmp,
            check=True,
        )

    def _create_spec(
        self,
        *,
        id6: str = "sp0001",
        status: str = "draft",
        slug: str = "fixture",
        body_extra: str = "",
    ) -> Path:
        spec_dir = self.tmp / ".aw" / "records" / "specs" / status
        spec_dir.mkdir(parents=True, exist_ok=True)
        p = spec_dir / f"20261009-{id6}-01-{id6}-{slug}.spec.md"
        text = (
            f"# Spec: Fixture Spec {id6}\n\n"
            f"- Date: 2026-10-09\n"
            f"- Status: {status}\n"
            f"- Id: {id6}\n"
            f"- Author: tester\n"
            f"- Priority: low\n"
            f"- Work-Kind: chore\n"
            f"- Scope: Fixture scope\n"
            f"{body_extra}\n"
            f"## Workflow history\n\n"
            f"- 2026-10-09 {status} (tester): initial\n"
        )
        p.write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp, check=True)
        subprocess.run(["git", "commit", "-m", f"add {id6}"], cwd=self.tmp, check=True)
        return p

    def test_hand_built_namespace_shape_path_attribute(self) -> None:
        """Callers constructing Namespace(path=...) transition successfully."""
        p = self._create_spec(id6="sh0001", status="draft")
        args = argparse.Namespace(
            path=str(p),
            status="to-review",
            message="ready for review",
            yes=True,
            no_commit=True,
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = specs.run_set(args)

        self.assertEqual(rc, 0, f"Expected rc=0, got {rc}: {err.getvalue()}")
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20261009-sh0001-01-sh0001-fixture.spec.md"
        )
        self.assertTrue(dest.exists(), f"Destination spec {dest} does not exist")
        self.assertIn("- Status: to-review", dest.read_text(encoding="utf-8"))

    def test_hand_built_namespace_shape_args_list(self) -> None:
        """Callers constructing Namespace(args=[...]) transition successfully."""
        p = self._create_spec(id6="sh0002", status="draft")
        args = argparse.Namespace(
            args=[str(p)],
            status="to-review",
            message="ready for review",
            yes=True,
            no_commit=True,
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = specs.run_set(args)

        self.assertEqual(rc, 0, f"Expected rc=0, got {rc}: {err.getvalue()}")
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20261009-sh0002-01-sh0002-fixture.spec.md"
        )
        self.assertTrue(dest.exists())
        self.assertIn("- Status: to-review", dest.read_text(encoding="utf-8"))

    def test_date_override_passthrough_on_specs(self) -> None:
        """Explicit --date override passes through to history, falling back to UTC history date."""
        # 1. With --date override
        p1 = self._create_spec(id6="dt0001", status="draft")
        args1 = argparse.Namespace(
            path=str(p1),
            status="to-review",
            date="2020-01-15",
            message="dated transition",
            yes=True,
            no_commit=True,
        )
        rc1 = specs.run_set(args1)
        self.assertEqual(rc1, 0)
        dest1 = (
            self.tmp
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20261009-dt0001-01-dt0001-fixture.spec.md"
        )
        text1 = dest1.read_text(encoding="utf-8")
        self.assertIn("- 2020-01-15 to-review (aw specs): dated transition", text1)

        # 2. Without --date override: defaults to utc_history_date()
        utc_today = core.utc_history_date()
        p2 = self._create_spec(id6="dt0002", status="draft")
        args2 = argparse.Namespace(
            path=str(p2),
            status="to-review",
            message="undated transition",
            yes=True,
            no_commit=True,
        )
        rc2 = specs.run_set(args2)
        self.assertEqual(rc2, 0)
        dest2 = (
            self.tmp
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20261009-dt0002-01-dt0002-fixture.spec.md"
        )
        text2 = dest2.read_text(encoding="utf-8")
        self.assertIn(f"- {utc_today} to-review (aw specs): undated transition", text2)

    def test_validate_spec_refusal_leaves_file_byte_identical(self) -> None:
        """Refusal from validate_spec backstop rejects non-conforming result byte-identically."""
        # A spec that would not conform if transitioned because of an invalid priority field
        p = self._create_spec(
            id6="cf0001", status="draft", body_extra="- Priority: bogus"
        )
        before_hash = _sha256(p)
        args = argparse.Namespace(
            path=str(p),
            status="to-review",
            yes=True,
            no_commit=True,
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = specs.run_set(args)

        self.assertNotEqual(rc, 0)
        self.assertEqual(_sha256(p), before_hash)
        self.assertTrue(p.exists())
        self.assertIn("conform", err.getvalue().lower() + out.getvalue().lower())

    def test_confirmation_gate_for_agent_and_json_callers(self) -> None:
        """Machine-readable (--agent / --json) callers require --yes or refuse with exit 2."""
        p = self._create_spec(id6="cg0001", status="draft")
        before_hash = _sha256(p)

        # 1. --agent without --yes refuses with exit 2
        args_agent = argparse.Namespace(
            path=str(p),
            status="to-review",
            agent=True,
            yes=False,
            no_commit=True,
        )
        rc_agent = specs.run_set(args_agent)
        self.assertEqual(rc_agent, 2)
        self.assertEqual(_sha256(p), before_hash)
        self.assertTrue(p.exists())

        # 2. --json without --yes refuses with exit 2
        args_json = argparse.Namespace(
            path=str(p),
            status="to-review",
            json=True,
            yes=False,
            no_commit=True,
        )
        rc_json = specs.run_set(args_json)
        self.assertEqual(rc_json, 2)
        self.assertEqual(_sha256(p), before_hash)
        self.assertTrue(p.exists())

        # 3. --agent with --yes succeeds with exit 0
        args_yes = argparse.Namespace(
            path=str(p),
            status="to-review",
            agent=True,
            yes=True,
            no_commit=True,
        )
        rc_yes = specs.run_set(args_yes)
        self.assertEqual(rc_yes, 0)
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20261009-cg0001-01-cg0001-fixture.spec.md"
        )
        self.assertTrue(dest.exists())
        self.assertIn("- Status: to-review", dest.read_text(encoding="utf-8"))

    def test_selector_widening_resolves_id6(self) -> None:
        """specs.run_set now accepts an id6 selector (widening per wy9aru Section 4.5)."""
        self._create_spec(id6="wd0001", status="draft")
        args = argparse.Namespace(
            path="wd0001",
            status="to-review",
            message="widened selector",
            dir=str(self.tmp),
            yes=True,
            no_commit=True,
        )
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = specs.run_set(args)

        self.assertEqual(rc, 0, f"Expected rc=0, got {rc}: {err.getvalue()}")
        dest = (
            self.tmp
            / ".aw"
            / "records"
            / "specs"
            / "to-review"
            / "20261009-wd0001-01-wd0001-fixture.spec.md"
        )
        self.assertTrue(dest.exists())
        self.assertIn("- Status: to-review", dest.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
