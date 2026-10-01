"""Tests for IPD 3qxuw1: derive rename hint type from where the record lives."""

from __future__ import annotations

import contextlib
import io
import pathlib
import shlex
import subprocess
import tempfile
import unittest

from agent_workflows import check_engine
from agent_workflows import cli


def _run_hint(cmd: str, repo: pathlib.Path) -> tuple[int, str, str]:
    """Execute an emitted hint command against a repo, substituting templates and suppressing interactive prompts."""
    parts = shlex.split(cmd)
    if parts and parts[0] == "aw":
        parts = parts[1:]
    parts = ["newset" if p == "<setid>" else p for p in parts]
    if "--apply" in parts and "--no-commit" not in parts:
        parts.append("--no-commit")
    parts.extend(["--dir", str(repo)])
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cli.main(parts)
    return rc, out.getvalue(), err.getvalue()


def _init_repo(root: pathlib.Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.com"], cwd=str(root), check=True
    )
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(root), check=True)


class TestIdentityRenameHint(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        _init_repo(self.repo)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_roadmap_tree_legacy_id_rename_hint_resolves(self) -> None:
        """Case (a): roadmaps/ legacy roadmap firing Id branch emits a command that resolves."""
        rdir = self.repo / ".aw" / "records" / "roadmaps"
        rdir.mkdir(parents=True)
        doc = (
            "- Id: zz9zz9\n"
            "- Status: draft\n"
            "- Priority: low\n"
            "- Work-Kind: feature\n\n"
            "## Workflow history\n"
            "- 2026-07-12 created: initial\n"
        )
        (rdir / "20260712-1200-01-a-roadmap-for-things.roadmap.md").write_text(
            doc, encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=str(self.repo), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(self.repo), check=True)

        findings = check_engine.check_name_identity(self.repo)
        self.assertEqual(
            len(findings), 1, f"Expected 1 finding, got {len(findings)}: {findings}"
        )
        finding = findings[0]
        self.assertEqual(finding.rule, "check.identity-absent-from-name")
        self.assertTrue(finding.recovery, "Finding must have recovery command")

        rc, out, err = _run_hint(finding.recovery, self.repo)
        self.assertEqual(
            rc,
            0,
            f"Suggested command {finding.recovery!r} refused with rc={rc}:\n{out}\n{err}",
        )

    def test_roadmap_tree_conforming_set_group_hint_resolves(self) -> None:
        """Case (b): roadmaps/ conforming roadmap firing Set branch emits aw group that resolves."""
        rdir = self.repo / ".aw" / "records" / "roadmaps"
        rdir.mkdir(parents=True)
        doc = (
            "- Id: bbb222\n"
            "- Set: otherset\n"
            "- Status: draft\n"
            "- Priority: low\n"
            "- Work-Kind: feature\n\n"
            "## Workflow history\n"
            "- 2026-07-12 created: initial\n"
        )
        (rdir / "20260712-mytopic-01-bbb222-a-roadmap.roadmap.md").write_text(
            doc, encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=str(self.repo), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(self.repo), check=True)

        findings = check_engine.check_name_identity(self.repo)
        self.assertEqual(
            len(findings), 1, f"Expected 1 finding, got {len(findings)}: {findings}"
        )
        finding = findings[0]
        self.assertEqual(finding.rule, "check.identity-absent-from-name")
        self.assertTrue(finding.recovery, "Finding must have recovery command")
        self.assertIn(
            "group",
            finding.recovery,
            f"Expected aw group command, got {finding.recovery}",
        )

        rc, out, err = _run_hint(finding.recovery, self.repo)
        self.assertEqual(
            rc,
            0,
            f"Suggested command {finding.recovery!r} refused with rc={rc}:\n{out}\n{err}",
        )

    def test_research_tree_conforming_set_group_hint_resolves(self) -> None:
        """Case (c) Control: research/ conforming roadmap firing Set branch resolves (already passes at HEAD)."""
        rdir = self.repo / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        doc = (
            "---\n"
            "id: aaa111\n"
            "set: otherset\n"
            "status: reference\n"
            "---\n"
            "# Roadmap Doc\n"
        )
        (rdir / "20260713-occomms-09-aaa111-another-roadmap.roadmap.md").write_text(
            doc, encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=str(self.repo), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(self.repo), check=True)

        findings = check_engine.check_name_identity(self.repo)
        self.assertEqual(
            len(findings), 1, f"Expected 1 finding, got {len(findings)}: {findings}"
        )
        finding = findings[0]
        self.assertEqual(finding.rule, "check.identity-absent-from-name")
        self.assertTrue(finding.recovery, "Finding must have recovery command")
        self.assertIn(
            "group",
            finding.recovery,
            f"Expected aw group command, got {finding.recovery}",
        )

        rc, out, err = _run_hint(finding.recovery, self.repo)
        self.assertEqual(
            rc,
            0,
            f"Suggested command {finding.recovery!r} refused with rc={rc}:\n{out}\n{err}",
        )

    def test_all_other_mapped_types_hints_resolve(self) -> None:
        """E-03: Every mapped type's hint resolves, including aw rename and aw group shapes."""
        # Seed records for all eight mapped types:
        # 1. plans (both rename and group)
        (self.repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (
            self.repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260712-1200-01-a-plan.ipd.md"
        ).write_text("- Id: pl0001\n- Status: draft\n", encoding="utf-8")
        (
            self.repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260712-myset-02-pl0002-group-plan.ipd.md"
        ).write_text(
            "- Id: pl0002\n- Set: othergroup\n- Status: draft\n", encoding="utf-8"
        )

        # 2. specs
        (self.repo / ".aw" / "records" / "specs").mkdir(parents=True)
        (
            self.repo / ".aw" / "records" / "specs" / "20260712-1200-01-a-spec.spec.md"
        ).write_text("- Id: sp0001\n- Status: draft\n", encoding="utf-8")

        # 3. backlog
        (self.repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
        (
            self.repo
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260712-1200-01-a-backlog.backlog.md"
        ).write_text(
            "- Id: bk0001\n- Status: open\n- Priority: high\n- Work-Kind: bug\n- Summary: x\n",
            encoding="utf-8",
        )

        # 4. prompts
        (self.repo / ".aw" / "records" / "prompts" / "pending").mkdir(parents=True)
        (
            self.repo
            / ".aw"
            / "records"
            / "prompts"
            / "pending"
            / "20260712-1200-01-a-prompt.prompt.md"
        ).write_text("- Id: pr0001\n- Status: draft\n", encoding="utf-8")

        # 5. walkthroughs
        (self.repo / ".aw" / "records" / "walkthroughs").mkdir(parents=True)
        (
            self.repo
            / ".aw"
            / "records"
            / "walkthroughs"
            / "20260712-1200-01-a-walk.walkthrough.md"
        ).write_text("- Id: wk0001\n- Status: draft\n", encoding="utf-8")

        # 6. releases
        (self.repo / ".aw" / "records" / "releases").mkdir(parents=True)
        (
            self.repo
            / ".aw"
            / "records"
            / "releases"
            / "20260712-1200-01-a-release.release.md"
        ).write_text("- Id: rl0001\n- Status: draft\n", encoding="utf-8")

        # 7. roadmaps
        (self.repo / ".aw" / "records" / "roadmaps").mkdir(parents=True)
        (
            self.repo
            / ".aw"
            / "records"
            / "roadmaps"
            / "20260712-1200-01-a-roadmap.roadmap.md"
        ).write_text("- Id: rm0001\n- Status: draft\n", encoding="utf-8")

        # 8. research
        (self.repo / ".aw" / "records" / "research").mkdir(parents=True)
        (
            self.repo
            / ".aw"
            / "records"
            / "research"
            / "20260713-occomms-09-rs0001-research.roadmap.md"
        ).write_text(
            "---\nid: rs0001\nset: otherset\nstatus: reference\n---\n# Doc\n",
            encoding="utf-8",
        )

        subprocess.run(["git", "add", "-A"], cwd=str(self.repo), check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=str(self.repo), check=True)

        old_static_noun = {
            "plans": "plans",
            "specs": "specs",
            "backlog": "backlog",
            "prompts": "prompts",
            "walkthroughs": "walkthroughs",
            "roadmaps": "research",
            "releases": "releases",
            "research": "research",
        }

        findings = check_engine.check_name_identity(self.repo)
        seen_nouns = set()
        seen_verbs = set()
        differing_types = set()

        for f in findings:
            self.assertTrue(f.recovery, f"Finding {f.location} must have recovery")
            parts = shlex.split(f.recovery)
            self.assertEqual(parts[0], "aw")
            verb = parts[1]
            noun = parts[2]
            seen_nouns.add(noun)
            seen_verbs.add(verb)

            # Determine record type from file path
            loc = str(f.location)
            rtype = next(t for t in old_static_noun if f"/{t}/" in loc)
            if noun != old_static_noun[rtype]:
                differing_types.add(rtype)

            rc, out, err = _run_hint(f.recovery, self.repo)
            self.assertEqual(
                rc, 0, f"Hint {f.recovery!r} refused with rc={rc}:\n{out}\n{err}"
            )

        # Assert all 8 types are covered
        expected_types = {
            "plans",
            "specs",
            "backlog",
            "prompts",
            "walkthroughs",
            "roadmaps",
            "releases",
            "research",
        }
        self.assertEqual(
            seen_nouns, expected_types, f"Expected all 8 types, got {seen_nouns}"
        )
        self.assertIn(
            "group", seen_verbs, "Must cover at least one non-roadmap aw group shape"
        )
        self.assertIn("rename", seen_verbs, "Must cover aw rename shape")
        # Exactly ONE type differs from old static entry: roadmaps
        self.assertEqual(
            differing_types,
            {"roadmaps"},
            f"Expected only roadmaps to differ from old static, got {differing_types}",
        )
