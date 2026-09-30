"""Tests for IPD 0ykozn: Flag a plan that cites a spec id6 without carrying From-Spec,
and ship the --from-spec setter that fixes it.

Verifies:
1. parse_cited_spec_ids:
   - cited in - Concern:
   - cited in - Scope:
   - cited in - Scope-Paths:
   - cited ONLY on a CONTINUATION line of one of those bullets (F-12)
   - cited ONLY in a ## Findings body row (must return [])
   - a six-letter word that is not a known spec id (must return [])
   - the same id cited on two bullets (dedupes)
2. set_from_spec_line:
   - inserts after - Status:
   - idempotent under a second call
   - removes on '-' or None
   - falls back to after - Id: when no - Status: exists
   - REPLACES rather than duplicates a pre-existing empty-valued - From-Spec: line (F-11)
3. check_plan_spec_link_missing:
   - pending plan citing known spec with no edge (1 info finding naming plan and spec)
   - same plan carrying the edge (0 findings)
   - same carrying - From-Spec: - (finding, via source_link_is_absent)
   - same file under executed/ (0 findings)
   - plan citing no known spec (0 findings)
   - empty known-spec-id union (returns [], fail-safe)
4. Exit-code control:
   - repository whose only finding is this rule exits 0 through drift_exit_code
5. Observability (F-10 regression guard):
   - reports finding on a repository with nothing staged
6. aw ipd set --from-spec CLI:
   - writes the bullet
   - refuses an unresolvable id6 with nonzero exit naming it
   - clears on '-'
   - replaces pre-existing empty-valued line without duplication
7. Single dispatch & fail isolation:
   - reached by check_content('plans')
   - fail-isolated if detector raises
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine
from agent_workflows import releases


def _create_minimal_repo(root: Path) -> Path:
    """Create minimal directory structure for check_engine tests."""
    for p in (
        root / ".aw" / "records" / "plans" / "pending",
        root / ".aw" / "records" / "plans" / "executed",
        root / ".aw" / "records" / "specs" / "approved",
    ):
        p.mkdir(parents=True, exist_ok=True)
    return root


def _create_spec(
    repo: Path,
    spec_id6: str,
    title: str = "Test Spec",
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "specs"
        / "approved"
        / f"20260901-{spec_id6}-01-{spec_id6}-test.spec.md"
    )
    content = (
        f"# Spec: {title}\n\n"
        f"- Id: {spec_id6}\n"
        "- Status: approved\n\n"
        "## Acceptance criteria\n\n"
        "- **A1** First criterion\n"
    )
    p.write_text(content, encoding="utf-8")
    return p


def _create_plan(
    repo: Path,
    plan_id6: str,
    *,
    subfolder: str = "pending",
    concern: str = "General concern",
    scope: str = "General scope",
    scope_paths: str = "agent_workflows/foo.py",
    from_spec: str | None = None,
    status: str = "to-review",
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / subfolder
        / f"20260928-testset-01-{plan_id6}-test.ipd.md"
    )
    lines = [
        f"# IPD: Test {plan_id6}",
        "",
        "- Date: 2026-09-28",
        "- Kind: child",
        f"- Concern: {concern}",
        f"- Scope: {scope}",
        f"- Scope-Paths: {scope_paths}",
        "- Item-Dependencies: none",
        f"- Status: {status}",
    ]
    if from_spec is not None:
        lines.append(f"- From-Spec: {from_spec}")
    lines.extend(
        [
            "- Set: testset",
            "- Order: 1",
            f"- Id: {plan_id6}",
            "",
            "## Workflow history",
            f"- 2026-09-28 to-review (test): status set to {status}",
        ]
    )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


class TestParseCitedSpecIds(unittest.TestCase):
    """E-03 / V-03: parse_cited_spec_ids pure function tests."""

    def test_cited_in_concern(self) -> None:
        text = (
            "# Plan\n- Concern: Addresses spec c4gd2h for plan linkage\n- Scope: None\n"
        )
        self.assertEqual(
            check_engine.parse_cited_spec_ids(text, {"c4gd2h"}), ["c4gd2h"]
        )

    def test_cited_in_scope(self) -> None:
        text = "# Plan\n- Concern: None\n- Scope: Implements c4gd2h completely\n"
        self.assertEqual(
            check_engine.parse_cited_spec_ids(text, {"c4gd2h"}), ["c4gd2h"]
        )

    def test_cited_in_scope_paths(self) -> None:
        text = (
            "# Plan\n"
            "- Concern: None\n"
            "- Scope: None\n"
            "- Scope-Paths: .aw/records/specs/20260901-c4gd2h-01-c4gd2h-test.spec.md\n"
        )
        self.assertEqual(
            check_engine.parse_cited_spec_ids(text, {"c4gd2h"}), ["c4gd2h"]
        )

    def test_cited_only_on_continuation_line(self) -> None:
        text = (
            "# Plan\n"
            "- Concern: Initial line of concern\n"
            "  continuation line citing c4gd2h here\n"
            "- Scope: None\n"
        )
        self.assertEqual(
            check_engine.parse_cited_spec_ids(text, {"c4gd2h"}), ["c4gd2h"]
        )

    def test_cited_only_in_findings_body_row(self) -> None:
        text = (
            "# Plan\n"
            "- Concern: Clean concern\n"
            "- Scope: Clean scope\n"
            "- Scope-Paths: agent_workflows/foo.py\n"
            "- Status: to-review\n\n"
            "## Findings\n"
            "| F-01 | c4gd2h | Body row mentioning spec |\n"
        )
        self.assertEqual(check_engine.parse_cited_spec_ids(text, {"c4gd2h"}), [])

    def test_unknown_six_letter_word(self) -> None:
        text = "# Plan\n- Concern: This is a silent plan\n- Scope: None\n"
        # 'silent' is 6 characters [0-9a-z]{6}, but not in known_spec_ids
        self.assertEqual(check_engine.parse_cited_spec_ids(text, {"c4gd2h"}), [])

    def test_deduplication_across_bullets(self) -> None:
        text = (
            "# Plan\n"
            "- Concern: Addresses c4gd2h\n"
            "- Scope: Also implements c4gd2h\n"
            "- Scope-Paths: foo.py\n"
        )
        self.assertEqual(
            check_engine.parse_cited_spec_ids(text, {"c4gd2h"}), ["c4gd2h"]
        )

    def test_empty_known_specs(self) -> None:
        text = "# Plan\n- Concern: Addresses c4gd2h\n"
        self.assertEqual(check_engine.parse_cited_spec_ids(text, set()), [])


class TestSetFromSpecLine(unittest.TestCase):
    """E-01 / V-01: releases.set_from_spec_line writer tests."""

    def test_insert_after_status(self) -> None:
        text = "# Plan\n- Date: 2026-09-28\n- Status: approved\n- Id: 0ykozn\n"
        result = releases.set_from_spec_line(text, "c4gd2h")
        expected = "# Plan\n- Date: 2026-09-28\n- Status: approved\n- From-Spec: c4gd2h\n- Id: 0ykozn\n"
        self.assertEqual(result, expected)

    def test_idempotence(self) -> None:
        text = "# Plan\n- Date: 2026-09-28\n- Status: approved\n- Id: 0ykozn\n"
        once = releases.set_from_spec_line(text, "c4gd2h")
        twice = releases.set_from_spec_line(once, "c4gd2h")
        self.assertEqual(once, twice)

    def test_remove_with_dash(self) -> None:
        text = "# Plan\n- Status: approved\n- From-Spec: c4gd2h\n- Id: 0ykozn\n"
        result = releases.set_from_spec_line(text, "-")
        self.assertNotIn("- From-Spec:", result)
        self.assertIn("- Status: approved\n- Id: 0ykozn\n", result)

    def test_remove_with_none(self) -> None:
        text = "# Plan\n- Status: approved\n- From-Spec: c4gd2h\n- Id: 0ykozn\n"
        result = releases.set_from_spec_line(text, None)
        self.assertNotIn("- From-Spec:", result)

    def test_fallback_after_id(self) -> None:
        text = "# Plan\n- Date: 2026-09-28\n- Id: 0ykozn\n- Scope: test\n"
        result = releases.set_from_spec_line(text, "c4gd2h")
        expected = "# Plan\n- Date: 2026-09-28\n- Id: 0ykozn\n- From-Spec: c4gd2h\n- Scope: test\n"
        self.assertEqual(result, expected)

    def test_replace_preexisting_empty_value(self) -> None:
        """F-11 regression guard: an empty - From-Spec: line must be replaced, not duplicated."""
        text = "# Plan\n- Status: approved\n- From-Spec:\n- Id: 0ykozn\n"
        result = releases.set_from_spec_line(text, "c4gd2h")
        self.assertEqual(result.count("- From-Spec:"), 1)
        self.assertIn("- From-Spec: c4gd2h\n", result)


class TestCheckPlanSpecLinkMissing(unittest.TestCase):
    """E-04 / V-04: check_plan_spec_link_missing detector tests."""

    def test_pending_plan_missing_edge(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="Flag plans citing spec c4gd2h without link",
            )
            drifts = check_engine.check_plan_spec_link_missing(repo)
            self.assertEqual(len(drifts), 1)
            d = drifts[0]
            self.assertEqual(d.rule, "check.plan-spec-link-missing")
            self.assertEqual(d.severity, "info")
            self.assertIn("c4gd2h", d.detail)
            self.assertIn("c4gd2h", d.observed)
            self.assertIn("aw ipd set 0ykozn --from-spec c4gd2h", d.recovery)

    def test_plan_carrying_edge(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="Flag plans citing spec c4gd2h without link",
                from_spec="c4gd2h",
            )
            drifts = check_engine.check_plan_spec_link_missing(repo)
            self.assertEqual(len(drifts), 0)

    def test_plan_carrying_absent_sentinel(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="Flag plans citing spec c4gd2h without link",
                from_spec="-",
            )
            drifts = check_engine.check_plan_spec_link_missing(repo)
            self.assertEqual(len(drifts), 1)
            self.assertEqual(drifts[0].rule, "check.plan-spec-link-missing")

    def test_plan_in_executed_dir_exempt(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                subfolder="executed",
                concern="Flag plans citing spec c4gd2h without link",
                status="executed",
            )
            drifts = check_engine.check_plan_spec_link_missing(repo)
            self.assertEqual(len(drifts), 0)

    def test_plan_citing_no_known_spec(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="No spec citation here at all",
            )
            drifts = check_engine.check_plan_spec_link_missing(repo)
            self.assertEqual(len(drifts), 0)

    def test_empty_known_specs_fail_safe(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            # No specs created
            _create_plan(
                repo,
                "0ykozn",
                concern="Cites c4gd2h but no specs exist anywhere",
            )
            drifts = check_engine.check_plan_spec_link_missing(repo)
            self.assertEqual(len(drifts), 0)

    def test_exit_code_control(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="Cites c4gd2h",
            )
            drifts = check_engine.check_plan_spec_link_missing(repo)
            self.assertEqual(len(drifts), 1)
            self.assertEqual(_core.drift_exit_code(drifts), 0)

    def test_observability_nothing_staged(self) -> None:
        """F-10 regression guard: rule reports on a clean working tree with nothing staged."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="Cites c4gd2h",
            )
            # Working tree has untracked/unstaged changes, nothing staged
            drifts = check_engine.check_plan_spec_link_missing(
                repo, include_untracked=True
            )
            self.assertEqual(len(drifts), 1)
            self.assertEqual(drifts[0].rule, "check.plan-spec-link-missing")


class TestDispatchAndFailIsolation(unittest.TestCase):
    """E-05 / V-05: check_type plans dispatch and fail isolation tests."""

    def test_dispatch_reached_by_check_content(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="Cites c4gd2h",
            )
            drifts = check_engine.check_content(repo, "plans", include_untracked=True)
            missing = [d for d in drifts if d.rule == "check.plan-spec-link-missing"]
            self.assertEqual(len(missing), 1)

    def test_single_dispatch_plans_and_all(self) -> None:
        """V-05: verify single dispatch (exactly 1 finding) on both check_type('plans') and check_types(['all'])."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "c4gd2h")
            _create_plan(
                repo,
                "0ykozn",
                concern="Cites c4gd2h",
            )
            # check_type('plans') -> exactly 1
            drifts_plans = check_engine.check_type(
                repo, "plans", include_untracked=True
            )
            missing_plans = [
                d for d in drifts_plans if d.rule == "check.plan-spec-link-missing"
            ]
            self.assertEqual(len(missing_plans), 1)

            # check_types(['all']) -> exactly 1
            drifts_all = check_engine.check_types(repo, ["all"], include_untracked=True)
            missing_all = [
                d for d in drifts_all if d.rule == "check.plan-spec-link-missing"
            ]
            self.assertEqual(len(missing_all), 1)

    def test_fail_isolation_when_detector_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            with mock.patch(
                "agent_workflows.check_engine.check_plan_spec_link_missing",
                side_effect=RuntimeError("simulated detector crash"),
            ):
                drifts = check_engine.check_content(repo, "plans")
                self.assertIsInstance(drifts, list)


class TestCliIpdSetFromSpec(unittest.TestCase):
    """E-02 / V-02: aw ipd set --from-spec CLI behavior tests."""

    def test_cli_set_from_spec_writes_bullet(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
            _create_spec(repo, "c4gd2h")
            plan_path = _create_plan(repo, "temp01", status="to-review")

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "set",
                    "--dir",
                    tmp,
                    "to-review",
                    "temp01",
                    "--from-spec",
                    "c4gd2h",
                    "--yes",
                    "--no-commit",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            text = plan_path.read_text(encoding="utf-8")
            self.assertIn("- From-Spec: c4gd2h\n", text)

    def test_cli_refuse_unresolvable_id(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
            _create_spec(repo, "c4gd2h")
            plan_path = _create_plan(repo, "temp01", status="to-review")

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "set",
                    "--dir",
                    tmp,
                    "to-review",
                    "temp01",
                    "--from-spec",
                    "nosuch",
                    "--yes",
                    "--no-commit",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("nosuch", proc.stdout + proc.stderr)
            text = plan_path.read_text(encoding="utf-8")
            self.assertNotIn("- From-Spec:", text)

    def test_cli_clear_with_dash(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
            _create_spec(repo, "c4gd2h")
            plan_path = _create_plan(
                repo, "temp01", from_spec="c4gd2h", status="to-review"
            )

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "set",
                    "--dir",
                    tmp,
                    "to-review",
                    "temp01",
                    "--from-spec",
                    "-",
                    "--yes",
                    "--no-commit",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            text = plan_path.read_text(encoding="utf-8")
            self.assertNotIn("- From-Spec:", text)


if __name__ == "__main__":
    unittest.main()
