"""Tests for IPD 3dexf1: Cross-check spec acceptance criteria against plan coverage.

Verifies:
1. Criteria parser: four letter-prefixed row shapes (bold bullet, bare enumerated,
   table cell, dash enumerated), heading depth handling, non-goal exclusion, bare-digit exclusion.
2. Plan-side search space: valid_leaves + subfields + ## Required tests / validation, fence-aware.
3. Namespace-in-use gate: silences foreign namespaces, accepts false negative on 0-matched plans.
4. Finding emission: one Drift per spec at severity `info`, detail under 60 chars, recovery naming child plan.
5. All required test cases from E-06:
   (a) clean fixture (zero findings, drift_exit_code == 0)
   (b) positive control (fires when criterion missing)
   (c) negative control (reader not broken into total silence)
   (d) From-Spec sentinels treated as absent with real spec Id
   (e) bare-digit criteria yield no findings
   (f) criterion inside code fence does not count as coverage
   (g) namespace-gate test
   (h) counterfactual pin matching {A1, A4, A6, A19, A21}
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine
from agent_workflows import ipd_lint


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
    criteria_lines: str,
    heading: str = "## Acceptance criteria",
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
        f"# Spec: Test {spec_id6}\n\n"
        f"- Id: {spec_id6}\n"
        "- Status: approved\n\n"
        f"{heading}\n\n"
        f"{criteria_lines}\n"
    )
    p.write_text(content, encoding="utf-8")
    return p


def _create_plan(
    repo: Path,
    plan_id6: str,
    from_spec: str,
    valid_lines: str = "",
    required_tests_lines: str = "",
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20260901-set001-01-{plan_id6}-test.ipd.md"
    )
    req_section = ""
    if required_tests_lines:
        req_section = f"\n## Required tests / validation\n\n{required_tests_lines}\n"
    v_section = ""
    if valid_lines:
        v_section = f"\n## Validation and cross-check (verify before reporting done)\n\n{valid_lines}\n"
    content = (
        f"# IPD: Test {plan_id6}\n\n"
        f"- Id: {plan_id6}\n"
        "- Status: approved\n"
        f"- From-Spec: {from_spec}\n"
        "- Set: set001\n"
        "- Scope: Fix\n"
        "- Scope-Paths: foo.py\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 Work\n"
        f"{req_section}"
        f"{v_section}"
    )
    p.write_text(content, encoding="utf-8")
    return p


class CheckEngineSpecCriteriaTests(unittest.TestCase):
    """Tests for spec criteria coverage cross-checking."""

    def test_rule_spec_registration(self) -> None:
        """E-04: check.spec-criteria-uncovered is registered info, repository assurance, deterministic."""
        spec = check_engine.rule_spec("check.spec-criteria-uncovered")
        self.assertEqual(spec.severity, "info")
        self.assertEqual(spec.assurance, check_engine.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, check_engine.DET_DETERMINISTIC)
        self.assertEqual(spec.invariant, "")

    def test_drift_exit_code_info_versus_warning(self) -> None:
        """E-04 / V-04: drift_exit_code returns 0 for info and 1 for warning."""
        info_drift = [
            _core.Drift(
                "path/spec.md",
                "check.spec-criteria-uncovered",
                "detail",
                severity="info",
            )
        ]
        warn_drift = [
            _core.Drift(
                "path/spec.md",
                "check.spec-criteria-uncovered",
                "detail",
                severity="warning",
            )
        ]
        self.assertEqual(_core.drift_exit_code(info_drift), 0)
        self.assertEqual(_core.drift_exit_code(warn_drift), 1)

    def test_rule_id_contains_neither_graduation_nor_duplicate(self) -> None:
        """E-04 / V-04: Rule id avoids substrings graduation and duplicate."""
        rule_id = check_engine._SPEC_CRITERIA_UNCOVERED_RULE
        self.assertNotIn("graduation", rule_id)
        self.assertNotIn("duplicate", rule_id)
        forbidden = [
            k
            for k in check_engine.RULE_REGISTRY
            if "graduation" in k or "duplicate" in k
        ]
        self.assertEqual(forbidden, [])

    def test_parser_four_row_shapes(self) -> None:
        """E-01: Parser recognizes all 4 letter-prefixed shapes and handles headings."""
        spec_text = (
            "# Spec: Shapes\n\n"
            "## 3b. Acceptance criteria (testable)\n\n"
            "- **A12b** bold bullet\n"
            "A5. bare enumerated\n"
            "| AC-1 | table cell |\n"
            "- A1. dash-plus-enumerated\n"
            "1. bare digit ignored\n"
            "- 2. bare digit bullet ignored\n"
            "## 4. Non-goals and acceptance considerations\n"
            "- **B1** inside non-goal heading ignored\n"
            "## Next Section\n"
            "- **C1** outside section ignored\n"
        )
        criteria = check_engine.parse_spec_acceptance_criteria(spec_text)
        self.assertEqual(criteria, ["A12b", "A5", "AC-1", "A1"])

    def test_clean_fixture_yields_zero_findings_and_exit_code_zero(self) -> None:
        """E-06(a): Clean fixture yields 0 findings and drift_exit_code == 0."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "spc001", "- **A1** First\n- **A2** Second\n")
            _create_plan(
                repo,
                "pln001",
                "spc001",
                valid_lines="- [ ] V-01 validates E-01\n  - Required evidence: Test A1 and A2\n  - Result: pending\n",
            )
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(findings, [])
            self.assertEqual(_core.drift_exit_code(findings), 0)

    def test_positive_control_fires_when_criterion_missing(self) -> None:
        """E-06(b): Positive control fires when a criterion is missing (3 declared, 2 named)."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            spec_path = _create_spec(
                repo, "spc001", "- **A1** First\n- **A2** Second\n- **A3** Third\n"
            )
            _create_plan(
                repo,
                "pln001",
                "spc001",
                valid_lines="- [ ] V-01 validates E-01\n  - Required evidence: Test A1 and A2\n  - Result: pending\n",
            )
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.rule, "check.spec-criteria-uncovered")
            self.assertEqual(f.location, str(spec_path))
            self.assertEqual(f.severity, "info")
            self.assertIn("A3", f.detail)
            self.assertNotIn("A1", f.detail)
            self.assertNotIn("A2", f.detail)

    def test_negative_control_reader_not_silently_broken(self) -> None:
        """E-06(c): Negative control proves reader is not broken into total silence."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            spec_path = _create_spec(
                repo, "spc001", "- **A1** First\n- **A2** Second\n"
            )
            _create_plan(
                repo,
                "pln001",
                "spc001",
                valid_lines="- [ ] V-01 validates E-01\n  - Required evidence: Only A1 is covered\n  - Result: pending\n",
            )
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertTrue(
                len(findings) > 0,
                "Reader must not silently return empty on unmet criteria",
            )
            self.assertEqual(findings[0].rule, "check.spec-criteria-uncovered")
            self.assertEqual(findings[0].location, str(spec_path))

    def test_sentinel_links_treated_as_absent(self) -> None:
        """E-06(d): From-Spec: -, none, unresolved are treated as absent, fixture spec carries real - Id:."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "spc001", "- **A1** First\n- **A2** Second\n")
            for sentinel in ("-", "none", "unresolved", '"none"'):
                _create_plan(repo, f"p_{sentinel.strip('\"-') or 'dash'}", sentinel)
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(findings, [])

    def test_bare_digit_criteria_yield_no_findings(self) -> None:
        """E-06(e): A spec whose criteria are all bare digits yields no findings."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(
                repo,
                "spc001",
                "1. First criterion\n2. Second criterion\n3. Third criterion\n",
            )
            _create_plan(
                repo,
                "pln001",
                "spc001",
                valid_lines="- [ ] V-01 validates E-01\n  - Required evidence: none\n  - Result: pending\n",
            )
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(findings, [])

    def test_code_fence_criterion_not_counted_as_coverage(self) -> None:
        """E-06(f): Criterion id mentioned only inside a code fence does not count as coverage."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            _create_spec(repo, "spc001", "- **A1** First\n- **A2** Second\n")
            # Plan mentions A1 in real validation, but A2 is only inside a code fence in Required tests
            _create_plan(
                repo,
                "pln001",
                "spc001",
                valid_lines="- [ ] V-01 validates E-01\n  - Required evidence: Test A1\n  - Result: pending\n",
                required_tests_lines="```\n# example output mentioning A2\nfoo\n```\n",
            )
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(len(findings), 1)
            self.assertIn("A2", findings[0].detail)

    def test_namespace_gate_silences_foreign_namespace(self) -> None:
        """E-06(g): Plan set citing a foreign namespace (0 criteria matched) is silent."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            # Spec defines A-01..A-03, but plan cites R-01..R-03
            _create_spec(
                repo,
                "spc001",
                "- **A-01** (R-01) First\n- **A-02** (R-02) Second\n- **A-03** (R-03) Third\n",
            )
            _create_plan(
                repo,
                "pln001",
                "spc001",
                valid_lines="- [ ] V-01 validates E-01\n  - Required evidence: Test R-01 and R-02\n  - Result: pending\n",
            )
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(findings, [])

    def test_seven_uncovered_criteria_detail_and_recovery(self) -> None:
        """E-04 / V-04: 7 uncovered criteria fixture shows 1 Drift, detail < 60 chars, child plan recovery."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            criteria_text = "\n".join(f"- **A{i}** Criterion {i}" for i in range(1, 9))
            spec_path = _create_spec(repo, "spc001", criteria_text)
            # Plan covers only A1, leaving 7 uncovered: A2..A8
            _create_plan(
                repo,
                "pln001",
                "spc001",
                valid_lines="- [ ] V-01 validates E-01\n  - Required evidence: Test A1\n  - Result: pending\n",
            )
            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.location, str(spec_path))
            self.assertLess(len(f.detail), 60)
            self.assertIn("(and 2 more)", f.detail)
            self.assertIn("child plan", f.recovery)
            self.assertIn("Order-0 parent", f.recovery)

    def test_counterfactual_pin_matches_motivating_defect_set(self) -> None:
        """E-06(h) / V-06: Motivating defect shape reproduces exact uncovered set {A1, A4, A6, A19, A21}."""
        # Load from commit 516eb661 if available in git history
        commit = "516eb661"
        try:
            res = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", commit],
                capture_output=True,
                text=True,
                check=True,
            )
            plan_paths = [
                p
                for p in res.stdout.splitlines()
                if "lifeglyph" in p and p.endswith(".ipd.md")
            ]
            spec_paths = [
                p
                for p in res.stdout.splitlines()
                if "uonrjg" in p and p.endswith(".spec.md")
            ]
        except Exception:
            self.skipTest(
                f"Commit {commit} not available in this shallow git environment"
            )

        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for p in plan_paths + spec_paths:
                dest = repo / p
                dest.parent.mkdir(parents=True, exist_ok=True)
                content = subprocess.run(
                    ["git", "show", f"{commit}:{p}"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                dest.write_text(content, encoding="utf-8")

            findings = check_engine.check_spec_criteria_uncovered(repo)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].rule, "check.spec-criteria-uncovered")
            # Uncovered set from detail/observed
            expected_uncovered = {"A1", "A4", "A6", "A19", "A21"}
            # Check criteria in uonrjg
            spec_text = (repo / spec_paths[0]).read_text(encoding="utf-8")
            criteria = check_engine.parse_spec_acceptance_criteria(spec_text)
            self.assertEqual(len(criteria), 25)

            plans = [
                (repo / p, (repo / p).read_text(encoding="utf-8")) for p in plan_paths
            ]
            space = "\n".join(
                check_engine.extract_plan_validation_space(t) for _p, t in plans
            )
            uncovered = {
                c
                for c in criteria
                if not re.search(
                    rf"(?<![0-9A-Za-z-]){re.escape(c)}(?![0-9A-Za-z])", space
                )
            }
            self.assertEqual(uncovered, expected_uncovered)

            # MUTATION CHECK: narrowing search space back to valid_leaves-only must FAIL
            valid_leaves_only_space = []
            for _p, t in plans:
                doc = ipd_lint.parse(t)
                for leaf in doc.valid_leaves:
                    valid_leaves_only_space.append(leaf.text)
                    for v in leaf.fields.values():
                        valid_leaves_only_space.append(v)
            vl_space_text = "\n".join(valid_leaves_only_space)
            uncovered_mutated = {
                c
                for c in criteria
                if not re.search(
                    rf"(?<![0-9A-Za-z-]){re.escape(c)}(?![0-9A-Za-z])", vl_space_text
                )
            }
            # The mutated space has 9 uncovered (false positives: A12b, A12c, A12d, A16)
            self.assertNotEqual(uncovered_mutated, expected_uncovered)
            self.assertEqual(
                uncovered_mutated,
                {"A1", "A4", "A6", "A12b", "A12c", "A12d", "A16", "A19", "A21"},
            )

    def test_isolated_try_except_in_check_content(self) -> None:
        """E-05 / V-05: check_content catches check_spec_criteria_uncovered exceptions without aborting."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            with mock.patch(
                "agent_workflows.check_engine.check_spec_criteria_uncovered",
                side_effect=RuntimeError("simulated unexpected explosion"),
            ):
                # Should not raise
                drift = check_engine.check_content(repo, "plans")
                self.assertIsInstance(drift, list)


if __name__ == "__main__":
    unittest.main()
