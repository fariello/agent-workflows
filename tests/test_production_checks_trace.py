"""Unit tests for the requirement-ID parser and SPEC-PLAN-TRACE verifier.

Covers:
- IPD rtvdak E-03, E-04, E-05, E-06, E-08
- Spec 89xjll AC-1, AC-2, AC-3, AC-5, AC-6, AC-7, AC-9
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import config
from agent_workflows import production_checks as pc


class TestSpecRequirementIdParser(unittest.TestCase):
    """Unit tests for the pure spec-side requirement-ID parser (E-03 / E-04 / AC-1 / AC-2)."""

    def test_shape_7ckptx(self):
        """Cover 7ckptx shape: R<n>.<n> requirements with bare unpadded A<n>. acceptance IDs."""
        text = """# Spec: 7ckptx fixture
## 1. Requirements
R1.1 For an isolated turn, cwd is workspace.
R1.2 The prompt MUST NOT contain absolute paths.
R2.1 Collection MUST be a copy.
- R3.3a AMENDED maintainer decision.

## 2. Acceptance Criteria
- A1. Build an isolated prompt from BOTH drivers.
- A2. Build a NON-isolated prompt.
- A5b. COLLECTION IS RECORDED.
- A7b-1. Test with no target.
- A10. Unanswered permission request.
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        self.assertEqual(
            req_ids,
            {"R1.1", "R1.2", "R2.1", "R3.3a"},
        )
        self.assertEqual(
            ac_ids,
            {"A1", "A2", "A5b", "A7b-1", "A10"},
        )
        # Disjoint sets (AC-1)
        self.assertTrue(req_ids.isdisjoint(ac_ids))

    def test_shape_6m4kow(self):
        """Cover 6m4kow shape: hyphenated, zero-padded acceptance IDs (- **A-01**)."""
        text = """# Spec: 6m4kow fixture
- R-01 Review findings subject types.
- R-02 Conforming review.

## Acceptance Criteria
- **A-01** (R-06) A spec at to-review can be reviewed.
- **A-02** (R-03) aw check all reports no dangling.
- **A-11** (R-10) Workflow shape decision is recorded.
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        self.assertEqual(req_ids, {"R-01", "R-02"})
        self.assertEqual(ac_ids, {"A-01", "A-02", "A-11"})
        self.assertTrue(req_ids.isdisjoint(ac_ids))

    def test_shape_w15vzb(self):
        """Cover w15vzb shape: hyphenated, unpadded acceptance IDs (- **A-1**)."""
        text = """# Spec: w15vzb fixture
- R-1 Role name outside vocabulary is refused.
- R-2 Inline model string.

## Acceptance Criteria
- **A-1** (R-1, R-2) A role name outside vocabulary is refused.
- **A-2** (R-3) A role value is invalid.
- **A-12** (Section 6) Populated role map.
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        self.assertEqual(req_ids, {"R-1", "R-2"})
        self.assertEqual(ac_ids, {"A-1", "A-2", "A-12"})
        self.assertTrue(req_ids.isdisjoint(ac_ids))

    def test_shape_z7nbn1(self):
        """Cover z7nbn1 shape: bare dotted paragraph numbers (FORM B) -> empty req set (OQ-04)."""
        text = """# Spec: z7nbn1 fixture
## 1. The architecture
1.1 There is ONE universal artifact selector.
1.2 There is ONE action table.
1.3 A runner MUST check every selected artifact.
1.4 A runner MUST verify declared dependencies.
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        self.assertEqual(req_ids, set())
        self.assertEqual(ac_ids, set())

    def test_shape_25kzda(self):
        """Cover 25kzda shape: section-addressed handles (FORM C) -> empty req set (OQ-04)."""
        text = """# Spec: 25kzda fixture
## 1. Introduction
### 1.1 Scope
### 1.2 Verification
## 2. Deterministic execution
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        self.assertEqual(req_ids, set())
        self.assertEqual(ac_ids, set())

    def test_shape_77tr3o(self):
        """Cover 77tr3o shape: requirements declared, but NO acceptance section."""
        text = """# Spec: 77tr3o fixture
- R-1 Set completeness is evaluated on disk.
- R-2 Retirement is gated on children executed.
- R-13 Orchestrator readiness check.
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        self.assertEqual(req_ids, {"R-1", "R-2", "R-13"})
        self.assertEqual(ac_ids, set())

    def test_shape_89xjll_and_all_admitted_families(self):
        """Cover all admitted FORM A families (R, F, G, I, C, P, T, B, H) and AC prefixes (AC, A)."""
        text = """# Spec: All admitted families
| ID | Requirement | Detail |
| R-1 | Requirement one | detail |
| F-01 | Functional requirement | detail |
| G1 | Goal requirement | detail |
| I-1 | Invariant requirement | detail |
| C-1 | Constraint requirement | detail |
| P-1 | Policy requirement | detail |
| T1 | Technical requirement | detail |
| B1 | Behavioral requirement | detail |
| H1 | Hygiene requirement | detail |
| N1 | Normative item should be excluded from TRACE | detail |

| ID | Covers | Criterion | Evidence |
| AC-1 | R-1 | Acceptance criterion 1 | ev |
| AC-2 | F-01 | Acceptance criterion 2 | ev |
| A-01 | G1 | Acceptance criterion 3 | ev |
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        # N1 must be EXCLUDED per OQ-04
        self.assertNotIn("N1", req_ids)
        self.assertEqual(
            req_ids,
            {"R-1", "F-01", "G1", "I-1", "C-1", "P-1", "T1", "B1", "H1"},
        )
        self.assertEqual(ac_ids, {"AC-1", "AC-2", "A-01"})
        self.assertTrue(req_ids.isdisjoint(ac_ids))

    def test_declaration_site_negatives(self):
        """Negative tests for mentions vs declarations (spec 89xjll Section 4.1 / AC-2)."""
        text = """# Spec: Mentions test
- R-1 Declared requirement.

This paragraph mentions R-2 mid-sentence, which must not be extracted.
Also mentions (see R-3 in parens) and (AC-1 in parens).
Referencing `77tr3o` R-5 is an external citation.
Another external citation: spec 25kzda A1 resolution.

Paragraph line 1 is introductory.
R-4 is at the start of paragraph line 2, so it is a continuation mention!

```markdown
- R-5 inside a fenced code block
- AC-2 inside code block
```

And table cell references:
| ID | Requirement |
| R-6 | Citations like R-7 and AC-3 in the text cell are mentions |
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        self.assertEqual(req_ids, {"R-1", "R-6"})
        self.assertEqual(ac_ids, set())
        for mention in ["R-2", "R-3", "R-4", "R-5", "R-7", "AC-1", "AC-2", "AC-3"]:
            self.assertNotIn(mention, req_ids)
            self.assertNotIn(mention, ac_ids)

    def test_marker_parsing(self):
        """Test parsing of [Should], [Optional], and [Deferred] markers (spec 89xjll Section 3.3 / AC-9)."""
        text = """# Spec: Markers test
- R-1 `[Optional]` Optional requirement.
- R-2 [Should] Should requirement.
- R-3 [Deferred] Staged requirement.
- **R-4** `[Deferred]` Another staged requirement.
- R-5 Mandatory requirement.
| R-6 | [Deferred] Table staged requirement |
| R-7 | A requirement mentioning [Deferred] in description is NOT deferred |

## Acceptance Criteria
- AC-1 [Deferred] Deferred acceptance.
- AC-2 [Should] Should has no effect on acceptance criterion.
- AC-3 Mandatory acceptance.
"""
        req_ids, ac_ids = pc.parse_spec_requirement_ids(text)
        markers = pc.parse_spec_id_markers(text)

        self.assertEqual(markers.get("R-1"), "Optional")
        self.assertEqual(markers.get("R-2"), "Should")
        self.assertEqual(markers.get("R-3"), "Deferred")
        self.assertEqual(markers.get("R-4"), "Deferred")
        self.assertIsNone(markers.get("R-5"))
        self.assertEqual(markers.get("R-6"), "Deferred")
        # R-7 description mentioned [Deferred], but marker was not immediately after ID:
        self.assertIsNone(markers.get("R-7"))

        # For acceptance, only Deferred is valid; Should has no effect
        self.assertEqual(markers.get("AC-1"), "Deferred")
        self.assertIsNone(markers.get("AC-2"))
        self.assertIsNone(markers.get("AC-3"))


class TestCutoverAndGrandfathering(unittest.TestCase):
    """Unit tests for the cutover mechanism and grandfathering (E-06 / AC-3)."""

    def test_cutover_date_comparison(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # Before cutover -> grandfathered
            self.assertFalse(
                pc.spec_requires_requirement_ids(
                    "20260930-old-01-old-spec.spec.md", repo_root=repo
                )
            )
            # On cutover -> bound
            self.assertTrue(
                pc.spec_requires_requirement_ids(
                    "20261001-new-01-new-spec.spec.md", repo_root=repo
                )
            )
            # After cutover -> bound
            self.assertTrue(
                pc.spec_requires_requirement_ids(
                    "20261015-new-01-new-spec.spec.md", repo_root=repo
                )
            )
            # No date in filename -> grandfathered
            self.assertFalse(
                pc.spec_requires_requirement_ids(
                    "legacy-spec-without-date.spec.md", repo_root=repo
                )
            )

    def test_module_fallback_when_config_and_installs_absent(self):
        """Demonstrate module fallback constant is reached in a fresh clone (PR-003 / AC-3)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # repo has no .aw/config/project.json and no installs.jsonl
            cutover_resolved = config.resolve_cutover_date(repo, "spec_requirement_ids")
            self.assertIsNone(cutover_resolved)

            # spec_requires_requirement_ids uses module fallback constant
            self.assertEqual(pc.SPEC_REQUIREMENT_IDS_CUTOVER_DATE, "20261001")
            self.assertTrue(
                pc.spec_requires_requirement_ids(
                    "20261001-spec-01-spec.spec.md", repo_root=repo
                )
            )
            self.assertFalse(
                pc.spec_requires_requirement_ids(
                    "20260920-spec-01-spec.spec.md", repo_root=repo
                )
            )


class TestSpecPlanTraceVerifier(unittest.TestCase):
    """Direct unit tests for spec_plan_trace verifier (E-05 / E-08 / AC-4..AC-9)."""

    def _create_spec(
        self, repo: Path, id6: str, content: str, filename_date: str = "20261001"
    ) -> Path:
        specs_dir = repo / ".aw" / "records" / "specs" / "approved"
        specs_dir.mkdir(parents=True, exist_ok=True)
        spec_path = specs_dir / f"{filename_date}-{id6}-01-{id6}-test.spec.md"
        spec_path.write_text(content, encoding="utf-8")
        return spec_path

    def _create_plan(
        self,
        repo: Path,
        plan_id6: str,
        spec_id6: str,
        e_items: list[str],
        v_items: list[str],
        bucket: str = "pending",
        kind: str = "child",
    ) -> Path:
        plans_dir = repo / ".aw" / "records" / "plans" / bucket
        plans_dir.mkdir(parents=True, exist_ok=True)
        plan_path = plans_dir / f"20261001-set-01-{plan_id6}-test.ipd.md"

        e_lines = []
        for i, text in enumerate(e_items, 1):
            e_lines.append(
                f"- [ ] E-{i:02d} {text}\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"
            )

        v_lines = []
        for i, text in enumerate(v_items, 1):
            v_lines.append(
                f"- [ ] V-{i:02d} {text}\n  - Required evidence: check\n  - Observed evidence:\n  - Result: pending"
            )

        e_section = "\n\n".join(e_lines) if e_lines else "- [ ] E-01 placeholder"
        v_section = "\n\n".join(v_lines) if v_lines else "- [ ] V-01 placeholder"

        content = f"""# IPD: Test Plan {plan_id6}

- Date: 2026-10-01
- Kind: {kind}
- Scope-Paths: README.md
- Status: to-review
- From-Spec: {spec_id6}
- Set: set01
- Id: {plan_id6}

## Goal
Goal for {plan_id6}

## Detailed Implementation Checklist (TODO)
### Task group 1
{e_section}

## Validation and cross-check (verify before reporting done)
{v_section}
"""
        plan_path.write_text(content, encoding="utf-8")
        return plan_path

    def test_full_coverage_passes(self):
        """Case (i): Produced plan cites every mandatory requirement and acceptance criterion -> PASS."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spc001
- Status: approved

- R-1 First requirement.
- R-2 Second requirement.

## Acceptance Criteria
- AC-1 First acceptance criterion.
"""
            self._create_spec(repo, "spc001", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spc001",
                e_items=[
                    "Implements `spc001` R-1",
                    "Implements spc001 R-2",
                ],
                v_items=[
                    "Validates `spc001` AC-1",
                ],
            )
            findings = pc.spec_plan_trace(
                repo, "spc001", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])
            self.assertIsNone(pc.spec_plan_trace_vacuity(repo, "spc001"))

    def test_missing_requirement_fails(self):
        """Case (ii): Produced plan omits one mandatory requirement -> FAILS with SPEC-PLAN-TRACE."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spc001
- Status: approved

- R-1 First requirement.
- R-2 Second requirement.

## Acceptance Criteria
- AC-1 First acceptance criterion.
"""
            self._create_spec(repo, "spc001", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spc001",
                e_items=[
                    "Implements `spc001` R-1 only",
                ],
                v_items=[
                    "Validates `spc001` AC-1",
                ],
            )
            findings = pc.spec_plan_trace(
                repo, "spc001", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(len(findings), 1)
            code, target, msg = findings[0]
            self.assertEqual(code, "SPEC-PLAN-TRACE")
            self.assertEqual(target, "pln001")
            self.assertIn("R-2", msg)
            self.assertIn(
                "[SPEC-PLAN-TRACE] Generated IPD pln001 does not cover spec items: R-2",
                msg,
            )
            self.assertIn("aw oc run resume run123", msg)

    def test_missing_acceptance_criterion_fails(self):
        """Produced plan omits one acceptance criterion -> FAILS with SPEC-PLAN-TRACE."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spc001
- Status: approved

- R-1 First requirement.

## Acceptance Criteria
- AC-1 First acceptance criterion.
- AC-2 Second acceptance criterion.
"""
            self._create_spec(repo, "spc001", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spc001",
                e_items=[
                    "Implements `spc001` R-1",
                ],
                v_items=[
                    "Validates `spc001` AC-1 only",
                ],
            )
            findings = pc.spec_plan_trace(
                repo, "spc001", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(len(findings), 1)
            self.assertIn("AC-2", findings[0][2])

    def test_grandfathered_spec_passes_vacuously(self):
        """Case (iii): Grandfathered spec predating cutover PASSES even with uncovered ids."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-09-15
- Id: spcold
- Status: approved

- R-1 Requirement.
- AC-1 Criterion.
"""
            # Dated 20260915 < 20261001 cutover
            self._create_spec(repo, "spcold", spec_content, filename_date="20260915")
            plan = self._create_plan(
                repo,
                "pln001",
                "spcold",
                e_items=["Does unrelated work"],
                v_items=["Validates unrelated work"],
            )
            findings = pc.spec_plan_trace(
                repo, "spcold", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])
            self.assertEqual(
                pc.spec_plan_trace_vacuity(repo, "spcold"), "grandfathered"
            )

    def test_no_declared_ids_passes_vacuously(self):
        """Post-cutover spec declaring no traceable IDs PASSES vacuously."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcnoid
- Status: approved

Prose description with no requirement IDs.
"""
            self._create_spec(repo, "spcnoid", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spcnoid",
                e_items=["Does work"],
                v_items=["Validates work"],
            )
            findings = pc.spec_plan_trace(
                repo, "spcnoid", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])
            self.assertEqual(pc.spec_plan_trace_vacuity(repo, "spcnoid"), "no-ids")

    def test_no_acceptance_section_passes_with_requirements_only(self):
        """Spec declaring requirements but no acceptance section cannot fail acceptance half."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcnoac
- Status: approved

- R-1 Requirement one.
"""
            self._create_spec(repo, "spcnoac", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spcnoac",
                e_items=["Implements `spcnoac` R-1"],
                v_items=["General validation"],
            )
            findings = pc.spec_plan_trace(
                repo, "spcnoac", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])

    def test_optional_and_deferred_requirements(self):
        """[Optional] and [Deferred] requirements are excluded from coverage (AC-9)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcopt
- Status: approved

- R-1 Mandatory requirement.
- R-2 `[Optional]` Optional requirement.
- R-3 [Deferred] Staged requirement.

## Acceptance Criteria
- AC-1 Mandatory acceptance.
- AC-2 [Deferred] Staged acceptance.
"""
            self._create_spec(repo, "spcopt", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spcopt",
                e_items=["Implements `spcopt` R-1 and cites `spcopt` R-3"],
                v_items=["Validates `spcopt` AC-1"],
            )
            findings = pc.spec_plan_trace(
                repo, "spcopt", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])
            # Citing deferred R-3 is not an unknown reference
            # Vacuity is None (it is a real pass, marked partial)
            self.assertIsNone(pc.spec_plan_trace_vacuity(repo, "spcopt"))
            # spec_plan_trace_deferred lists both deferred IDs
            self.assertEqual(
                pc.spec_plan_trace_deferred(repo, "spcopt"), ["AC-2", "R-3"]
            )

    def test_unknown_reference_fails(self):
        """Case (vii): Plan cites an id not declared by the producing spec -> fails (3rd conjunct)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spc001
- Status: approved

- R-1 First requirement.

## Acceptance Criteria
- AC-1 First acceptance criterion.
"""
            self._create_spec(repo, "spc001", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spc001",
                e_items=[
                    "Implements `spc001` R-1 and `spc001` R-99",
                ],
                v_items=[
                    "Validates `spc001` AC-1",
                ],
            )
            findings = pc.spec_plan_trace(
                repo, "spc001", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(len(findings), 1)
            self.assertIn("R-99", findings[0][2])

    def test_other_spec_mention_and_unqualified_token_ignored(self):
        """Plan citing another spec or unqualified tokens does NOT trigger unknown reference."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spc001
- Status: approved

- R-1 First requirement.

## Acceptance Criteria
- AC-1 First acceptance criterion.
"""
            self._create_spec(repo, "spc001", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spc001",
                e_items=[
                    "Implements `spc001` R-1. Mentions `77tr3o` R-5 and plan finding F-03 and P16.",
                ],
                v_items=[
                    "Validates `spc001` AC-1. Mentions AC-99 unqualified.",
                ],
            )
            findings = pc.spec_plan_trace(
                repo, "spc001", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])

    def test_unqualified_citation_of_real_requirement_does_not_cover(self):
        """Unqualified token naming a real requirement does not cover it (Section 6.2b)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spc001
- Status: approved

- R-1 First requirement.
"""
            self._create_spec(repo, "spc001", spec_content)
            plan = self._create_plan(
                repo,
                "pln001",
                "spc001",
                e_items=[
                    "Implements R-1 without qualifying with spec id6",
                ],
                v_items=["Validation"],
            )
            findings = pc.spec_plan_trace(
                repo, "spc001", [plan], host="oc", run_id="run123"
            )
            self.assertEqual(len(findings), 1)
            self.assertIn("R-1", findings[0][2])

    def test_orchestrator_child_tracking_rows_contribute_no_failure(self):
        """Orchestrator plan in the set with child-tracking rows does not cause failure."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcorch
- Status: approved

- R-1 Requirement one.

## Acceptance Criteria
- AC-1 Acceptance one.
"""
            self._create_spec(repo, "spcorch", spec_content)
            # Orchestrator plan
            orch_plan = self._create_plan(
                repo,
                "orch01",
                "spcorch",
                e_items=["CONFIRM child1 REACHED executed"],
                v_items=["Check child1 status"],
                kind="orchestrator",
            )
            # Child plan covering R-1 and AC-1
            child_plan = self._create_plan(
                repo,
                "chld01",
                "spcorch",
                e_items=["Implements `spcorch` R-1"],
                v_items=["Validates `spcorch` AC-1"],
            )
            findings = pc.spec_plan_trace(
                repo, "spcorch", [orch_plan, child_plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])

    def test_pooled_coverage_across_plans(self):
        """Coverage pooled across multiple plans: plan 1 covers R-1, plan 2 covers R-2 (AC-4)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcpool
- Status: approved

- R-1 Requirement one.
- R-2 Requirement two.

## Acceptance Criteria
- AC-1 Acceptance one.
"""
            self._create_spec(repo, "spcpool", spec_content)
            plan1 = self._create_plan(
                repo,
                "pln001",
                "spcpool",
                e_items=["Implements `spcpool` R-1"],
                v_items=["No AC"],
            )
            plan2 = self._create_plan(
                repo,
                "pln002",
                "spcpool",
                e_items=["Implements `spcpool` R-2"],
                v_items=["Validates `spcpool` AC-1"],
            )
            findings = pc.spec_plan_trace(
                repo, "spcpool", [plan1, plan2], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])

    def test_executed_linked_plan_contributes_coverage(self):
        """A previously executed linked plan in executed/ contributes coverage (AC-4)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcexec
- Status: approved

- R-1 Requirement one.
- R-2 Requirement two.
"""
            self._create_spec(repo, "spcexec", spec_content)
            # Create an executed linked plan covering R-1
            self._create_plan(
                repo,
                "px0001",
                "spcexec",
                e_items=["Implements `spcexec` R-1"],
                v_items=["Validation"],
                bucket="executed",
            )
            # New plan covers only R-2
            new_plan = self._create_plan(
                repo,
                "pn0001",
                "spcexec",
                e_items=["Implements `spcexec` R-2"],
                v_items=["Validation"],
                bucket="pending",
            )
            findings = pc.spec_plan_trace(
                repo, "spcexec", [new_plan], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])

    def test_superseded_linked_plan_does_not_contribute_coverage(self):
        """A superseded linked plan does NOT contribute coverage (AC-4)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcsup
- Status: approved

- R-1 Requirement one.
- R-2 Requirement two.
"""
            self._create_spec(repo, "spcsup", spec_content)
            # Superseded plan covering R-1
            self._create_plan(
                repo,
                "ps0001",
                "spcsup",
                e_items=["Implements `spcsup` R-1"],
                v_items=["Validation"],
                bucket="superseded",
            )
            # New plan covers only R-2
            new_plan = self._create_plan(
                repo,
                "pn0001",
                "spcsup",
                e_items=["Implements `spcsup` R-2"],
                v_items=["Validation"],
                bucket="pending",
            )
            findings = pc.spec_plan_trace(
                repo, "spcsup", [new_plan], host="oc", run_id="run123"
            )
            self.assertEqual(len(findings), 1)
            self.assertIn("R-1", findings[0][2])

    def test_subfield_citation_is_recognized(self):
        """A citation in Expected outcome sub-field counts as covering the requirement (PR-002)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec_content = """# Spec
- Date: 2026-10-01
- Id: spcsub
- Status: approved

- R-1 Requirement one.
"""
            self._create_spec(repo, "spcsub", spec_content)
            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True, exist_ok=True)
            plan_path = plans_dir / "20261001-set-01-psub01-test.ipd.md"
            # Place citation in Expected outcome sub-field, not in the first line
            plan_path.write_text(
                """# IPD: Test Plan psub01

- Date: 2026-10-01
- Kind: child
- Scope-Paths: README.md
- Status: to-review
- From-Spec: spcsub
- Set: set01
- Id: psub01

## Goal
Goal

## Detailed Implementation Checklist (TODO)
### Task group 1
- [ ] E-01 Perform implementation
  - Depends on: none
  - Expected outcome: Satisfies `spcsub` R-1 completely
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 Validate
  - Required evidence: check
  - Observed evidence:
  - Result: pending
""",
                encoding="utf-8",
            )
            findings = pc.spec_plan_trace(
                repo, "spcsub", [plan_path], host="oc", run_id="run123"
            )
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
