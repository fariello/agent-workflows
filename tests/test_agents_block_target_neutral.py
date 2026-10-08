"""Behavior tests for target-neutral managed AGENTS.md block and dangling reference probe.

Covers IPD ka0g86 requirements E-05 (a)-(e).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import doctor, engine
from tests import support
from tests.support import REPO_ROOT, init_repo

pytestmark = pytest.mark.slow


def _extract_managed_block(text: str) -> str:
    open_m = re.search(r"<!--\s*aw:block\s*-->", text)
    close_m = re.search(r"<!--\s*/aw:block\s*-->", text)
    if open_m and close_m:
        return text[open_m.end() : close_m.start()]
    return ""


class AgentsBlockTargetNeutralTests(unittest.TestCase):
    """Test suite ensuring installed AGENTS.md is target-neutral and probes detect dangling paths."""

    def setUp(self):
        self.enterContext(support.execution_role(None))

    def _make_env(self, tmp_home: Path) -> dict[str, str]:
        env = dict(os.environ)
        env["AW_NO_REEXEC"] = "1"
        env["HOME"] = str(tmp_home)
        env["GIT_AUTHOR_NAME"] = "Test Author"
        env["GIT_AUTHOR_EMAIL"] = "test@example.com"
        env["GIT_COMMITTER_NAME"] = "Test Committer"
        env["GIT_COMMITTER_EMAIL"] = "test@example.com"
        return env

    def test_fresh_install_managed_block_contains_no_aw_only_tokens(self):
        """(a) Assert installed managed block contains none of the AW-only tokens in either layout."""
        aw_only_tokens = [
            "python3 -m pytest",
            "pyproject.toml",
            "RELEASING.md",
            "CONTRIBUTING.md",
            "GUIDING_PRINCIPLES",
            "oc_runipd.py",
            "runner_shared.py",
            "ipd-spec",
        ]

        for layout in ("aw", "legacy"):
            with self.subTest(layout=layout):
                with tempfile.TemporaryDirectory() as td:
                    td_path = Path(td)
                    target = td_path / f"target-{layout}"
                    init_repo(target)
                    (target / "package.json").write_text("{}\n", encoding="utf-8")

                    cmd = [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "install",
                        str(target),
                        "--preset",
                        "private-target",
                        "-y",
                        "--no-interactive",
                    ]

                    if layout == "legacy":
                        wf_dir = target / ".agents" / "workflows"
                        wf_dir.mkdir(parents=True)
                        (wf_dir / "index.md").write_text(
                            "# Workflows\n", encoding="utf-8"
                        )
                        support.git(target, "add", ".")
                        support.git(target, "commit", "-m", "init legacy")
                        cmd.append("--keep-legacy")
                    else:
                        support.git(target, "add", "package.json")
                        support.git(target, "commit", "-m", "init modern")

                    env = self._make_env(td_path / "home")
                    (td_path / "home").mkdir(parents=True, exist_ok=True)
                    res = subprocess.run(
                        cmd, env=env, capture_output=True, text=True, check=False
                    )
                    self.assertEqual(
                        res.returncode,
                        0,
                        f"Install failed for layout {layout}:\n{res.stdout}\n{res.stderr}",
                    )

                    agents_file = target / "AGENTS.md"
                    self.assertTrue(
                        agents_file.is_file(), "AGENTS.md must be installed"
                    )
                    content = agents_file.read_text(encoding="utf-8")
                    parsed = engine.parse_aw_block(content)
                    self.assertTrue(
                        parsed.found, "aw:block must exist in installed AGENTS.md"
                    )
                    managed_block = _extract_managed_block(content)

                    for tok in aw_only_tokens:
                        self.assertNotIn(
                            tok,
                            managed_block,
                            f"AW-only token {tok!r} found in installed managed block for layout {layout}",
                        )

    def test_fresh_install_doctor_zero_dangling_doc_references(self):
        """(b) Run aw doctor --json on fresh target of each layout and assert zero dangles."""
        for layout in ("aw", "legacy"):
            with self.subTest(layout=layout):
                with tempfile.TemporaryDirectory() as td:
                    td_path = Path(td)
                    target = td_path / f"target-{layout}"
                    init_repo(target)
                    (target / "package.json").write_text("{}\n", encoding="utf-8")

                    cmd = [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "install",
                        str(target),
                        "--preset",
                        "private-target",
                        "-y",
                        "--no-interactive",
                    ]

                    if layout == "legacy":
                        wf_dir = target / ".agents" / "workflows"
                        wf_dir.mkdir(parents=True)
                        (wf_dir / "index.md").write_text(
                            "# Workflows\n", encoding="utf-8"
                        )
                        support.git(target, "add", ".")
                        support.git(target, "commit", "-m", "init legacy")
                        cmd.append("--keep-legacy")
                    else:
                        support.git(target, "add", "package.json")
                        support.git(target, "commit", "-m", "init modern")

                    env = self._make_env(td_path / "home")
                    (td_path / "home").mkdir(parents=True, exist_ok=True)
                    subprocess.run(
                        cmd, env=env, capture_output=True, text=True, check=True
                    )

                    doc_cmd = [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        "doctor",
                        "--json",
                        "--dir",
                        str(target),
                    ]
                    doc_res = subprocess.run(
                        doc_cmd, env=env, capture_output=True, text=True, check=False
                    )
                    doc_data = json.loads(doc_res.stdout)
                    dangles = [
                        d
                        for d in doc_data.get("diagnostics", [])
                        if d.get("rule") == "doctor.dangling-doc-reference"
                    ]
                    self.assertEqual(
                        dangles,
                        [],
                        f"Expected 0 dangling doc references for layout {layout}, got {dangles}",
                    )

    def test_planted_missing_path_reported(self):
        """(c) Append backticked missing path to installed README and assert probe reports it."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target = td_path / "target"
            init_repo(target)
            (target / "package.json").write_text("{}\n", encoding="utf-8")
            support.git(target, "add", "package.json")
            support.git(target, "commit", "-m", "init")

            env = self._make_env(td_path / "home")
            (td_path / "home").mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "install",
                    str(target),
                    "--preset",
                    "private-target",
                    "-y",
                    "--no-interactive",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

            readme = target / ".aw" / "records" / "plans" / "README.md"
            self.assertTrue(readme.is_file())
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\nSee `docs/missing.md` for background.\n",
                encoding="utf-8",
            )

            findings = doctor.probe_installed_doc_references(target)
            planted = [d for d in findings if d.detail == "docs/missing.md"]
            self.assertEqual(len(planted), 1)
            f = planted[0]
            self.assertEqual(f.location, ".aw/records/plans/README.md")
            self.assertEqual(f.rule, "doctor.dangling-doc-reference")
            self.assertEqual(f.severity, "info")

    def test_probe_filtering_and_edge_cases(self):
        """(d) Call probe on tmp tree with .aw/nope/README.md and verify noise filtering."""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            init_repo(target)

            agents_text = (
                "# AGENTS\n\n"
                "<!-- aw:block -->\n"
                "Refers to missing `.aw/nope/README.md`.\n"
                "Contains placeholder `<id6>` and glob `*.py`.\n"
                "Contains slash command `/setup-repo`.\n"
                "Contains allowlisted `TODO.md` and `INDEX.md`.\n"
                "<!-- /aw:block -->\n"
            )
            (target / "AGENTS.md").write_text(agents_text, encoding="utf-8")

            findings = doctor.probe_installed_doc_references(target)
            details = [d.detail for d in findings]
            self.assertIn(".aw/nope/README.md", details)
            self.assertEqual(
                len(findings),
                1,
                f"Expected exactly 1 finding for .aw/nope/README.md, got findings: {findings}",
            )

    def test_this_repo_agents_md_has_suite_in_repo_local_region_only(self):
        """(e) Assert this repo's AGENTS.md has HOW TO RUN THE SUITE after aw:block, not inside."""
        agents_content = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        parsed = engine.parse_aw_block(agents_content)
        self.assertTrue(parsed.found, "AGENTS.md in repo must contain aw:block")
        managed_block = _extract_managed_block(agents_content)

        self.assertNotIn(
            "HOW TO RUN THE SUITE",
            managed_block,
            "Managed block in this repository must not contain HOW TO RUN THE SUITE",
        )
        self.assertIn(
            "HOW TO RUN THE SUITE",
            parsed.after,
            "Repo-local region after <!-- /aw:block --> must contain HOW TO RUN THE SUITE",
        )


if __name__ == "__main__":
    unittest.main()
