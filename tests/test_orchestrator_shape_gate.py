"""orchtyped Order 03 (`0xmk4e`): wire the shape check into both runners ahead of the probe.

Validates:
E-01 / V-01: One shared pre-queue shape gate in runner_shared, reused queued_orchestrator_targets,
             no host re-exports added, getattr fallback object identity.
E-02 / V-02: Early siting before run_dir / agent turns / sessions; --prepare-only integration.
E-03 / V-03: Batch reporting across every queued orchestrator before exiting (R8).
E-04 / V-04: Probe coexistence on bare indented prose obligations; distinguishable rule IDs
             (IPD-S407 vs orchestrator-uncovered-work); both-hosts behavioural refusal.
E-05 / V-05: Zero model calls / probe invocations on shape refusal (criterion 11).
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
import unittest.mock

from agent_workflows import agy_runipd, oc_runipd
from agent_workflows import ipd_lint as lint
from agent_workflows import runner_shared as rs

BOTH_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))

# ==================================================================================================
# FIXTURES
# ==================================================================================================

_ORCH_TAIL_ONE_ITEM = """\
## Completion criteria (the whole Set is done only when)

- None.

## Cross-IPD validation

- None.

## Deferred / out of scope (with reason)

- None.

## Scope check

- None.

## Required tests / validation

- None.

## Open questions

- None.

## Validation and cross-check (verify before reporting the Set complete)

- [ ] V-01 validates E-01
  - Required evidence: check baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- None.
"""

CONFORMING_ORCH_TEXT = """# IPD: Conforming orchestrator fixture

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Priority: medium
- Work-Kind: chore
- Status: approved
- Set: fixconf
- Order: 0
- Highest E allocated: 02
- Author: fixture
- Id: fix001
- Approval: 2026-09-24, fixture
- Readiness: go-pending-approval

## Workflow history

- 2026-09-24 approved (fixture): created.
- 2026-09-24 /plan-review (fixture): APPROVE

## Goal

Fixture.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  - Depends on: none
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending
- [ ] E-02 CONFIRM chd002 REACHED executed
  - Depends on: E-01
  - Expected outcome: chd002 reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixconf-01-chd001.ipd.md | none |
| 02 | chd002 | pending | .aw/records/plans/pending/20260924-fixconf-02-chd002.ipd.md | 01 |

## Completion criteria (the whole Set is done only when)

- None.

## Cross-IPD validation

- None.

## Deferred / out of scope (with reason)

- None.

## Scope check

- None.

## Required tests / validation

- None.

## Open questions

- None.

## Validation and cross-check (verify before reporting the Set complete)

- [ ] V-01 validates E-01
  - Required evidence: check status.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: check status.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- None.
"""

NON_CONFORMING_ORCH_1_TEXT = f"""# IPD: Non-conforming orchestrator 1 (untyped prose row)

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Priority: medium
- Work-Kind: chore
- Status: approved
- Set: fixbad
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: bad001
- Approval: 2026-09-24, fixture
- Readiness: go-pending-approval

## Workflow history

- 2026-09-24 approved (fixture): created.
- 2026-09-24 /plan-review (fixture): APPROVE

## Goal

Fixture.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 Establish the characterization baseline before any child runs
  - Depends on: none
  - Expected outcome: baseline established.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixbad-01-chd001.ipd.md | none |

{_ORCH_TAIL_ONE_ITEM}"""

NON_CONFORMING_ORCH_2_TEXT = f"""# IPD: Non-conforming orchestrator 2 (unknown child id6)

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Priority: medium
- Work-Kind: chore
- Status: approved
- Set: fixbad2
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: bad002
- Approval: 2026-09-24, fixture
- Readiness: go-pending-approval

## Workflow history

- 2026-09-24 approved (fixture): created.
- 2026-09-24 /plan-review (fixture): APPROVE

## Goal

Fixture.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM unk999 REACHED executed
  - Depends on: none
  - Expected outcome: unk999 reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixbad2-01-chd001.ipd.md | none |

{_ORCH_TAIL_ONE_ITEM}"""

NON_CONFORMING_ORCH_3_TEXT = f"""# IPD: Non-conforming orchestrator 3 (missing depends on)

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Priority: medium
- Work-Kind: chore
- Status: approved
- Set: fixbad3
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: bad003
- Approval: 2026-09-24, fixture
- Readiness: go-pending-approval

## Workflow history

- 2026-09-24 approved (fixture): created.
- 2026-09-24 /plan-review (fixture): APPROVE

## Goal

Fixture.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixbad3-01-chd001.ipd.md | none |

{_ORCH_TAIL_ONE_ITEM}"""

CONFORMING_WITH_BARE_INDENTED_PROSE_TEXT = f"""# IPD: Conforming rows with bare indented prose obligation

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Priority: medium
- Work-Kind: chore
- Status: approved
- Set: fixprose
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: prs001
- Approval: 2026-09-24, fixture
- Readiness: go-pending-approval

## Workflow history

- 2026-09-24 approved (fixture): created.
- 2026-09-24 /plan-review (fixture): APPROVE

## Goal

Fixture.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  Establish the characterization baseline before any child runs and produce the inventory report.
  - Depends on: none
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixprose-01-chd001.ipd.md | none |

{_ORCH_TAIL_ONE_ITEM}"""


class BothHostsShareOneDefinition(unittest.TestCase):
    """E-01 / V-01: Object identity through getattr fallback, no host re-export, no oc-to-agy import growth."""

    def test_each_host_resolves_the_gate_to_the_SAME_object(self):
        shared = getattr(rs, "enforce_orchestrator_shape_gate")
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                reached = getattr(
                    module,
                    "enforce_orchestrator_shape_gate",
                    getattr(module.runner_shared, "enforce_orchestrator_shape_gate"),
                )
                self.assertIs(reached, shared)

    def test_no_new_host_attribute_is_added(self):
        """PR-304: direct hasattr is False on both hosts; hosts share via initialize_run_core."""
        self.assertFalse(hasattr(oc_runipd, "enforce_orchestrator_shape_gate"))
        self.assertFalse(hasattr(agy_runipd, "enforce_orchestrator_shape_gate"))


class TheGateIsSitedBeforeRunDirAndPrepareOnlyRefuses(unittest.TestCase):
    """E-02 / V-02: Gate sited before run_dir creation; --prepare-only integration verified."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self._seq = 0

    def make_repo(
        self, text: str, filename: str = "20260924-fixbad-00-bad001.ipd.md"
    ) -> Path:
        self._seq += 1
        repo = self.root / f"repo-{self._seq}"
        plans = repo / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (plans / filename).write_text(text, encoding="utf-8")
        return repo

    def run_initialize(self, module, repo: Path, extra: list[str] | None = None):
        args = module.build_parser().parse_args(
            ["start", "bad001", "--repo", str(repo), *(extra or [])]
        )
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run_dir = module.initialize_run(args)
        return run_dir, out.getvalue(), err.getvalue()

    def test_non_conforming_run_leaves_no_run_dir_no_session_no_worktree(self):
        """On shape refusal, state_root(repo) gains no new run directory."""
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(NON_CONFORMING_ORCH_1_TEXT)
                state_dir = rs.state_root(repo)
                with self.assertRaises(rs.DriverError) as cm:
                    self.run_initialize(module, repo)
                self.assertIn("IPD-S407", str(cm.exception))
                # Zero run directories created under state_root(repo)
                if state_dir.exists():
                    run_dirs = [
                        d
                        for d in state_dir.iterdir()
                        if d.is_dir() and d.name.startswith("run-")
                    ]
                    self.assertEqual(
                        run_dirs, [], f"Expected no run dir, found {run_dirs}"
                    )

    def test_prepare_only_refuses_non_conforming_queue(self):
        """--prepare-only refuses non-conforming queues instead of silently passing."""
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(NON_CONFORMING_ORCH_1_TEXT)
                with self.assertRaises(rs.DriverError) as cm:
                    self.run_initialize(module, repo, ["--prepare-only"])
                self.assertIn("IPD-S407", str(cm.exception))
                self.assertIn("bad001", str(cm.exception))

    def test_prepare_only_succeeds_on_conforming_queue(self):
        """--prepare-only succeeds on a conforming queue, creating run_dir and skipping probe."""
        from tests.test_ipd_lint import _conforming_child
        from agent_workflows import coverage_record

        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(
                    CONFORMING_ORCH_TEXT, "20260924-fixconf-00-fix001.ipd.md"
                )
                p_dir = repo / ".aw" / "records" / "plans" / "pending"
                c1_text = (
                    _conforming_child()
                    .replace("- Set: x", "- Set: fixconf")
                    .replace("- Order: 1", "- Order: 1")
                    .replace("- Id: abc123", "- Id: chd001")
                )
                c2_text = (
                    _conforming_child()
                    .replace("- Set: x", "- Set: fixconf")
                    .replace("- Order: 1", "- Order: 2")
                    .replace("- Id: abc123", "- Id: chd002")
                )
                (p_dir / "20260924-fixconf-01-chd001.ipd.md").write_text(
                    c1_text, encoding="utf-8"
                )
                (p_dir / "20260924-fixconf-02-chd002.ipd.md").write_text(
                    c2_text, encoding="utf-8"
                )
                coverage_record.write(
                    p_dir / "20260924-fixconf-00-fix001.ipd.md",
                    "pass",
                    model="fixture",
                    tool="test",
                )
                args = module.build_parser().parse_args(
                    ["start", "fix001", "--repo", str(repo), "--prepare-only"]
                )
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    run_dir = module.initialize_run(args)
                self.assertIsNotNone(run_dir)
                self.assertTrue((run_dir / "state.json").is_file())
                self.assertIn("SKIPPED under --prepare-only", err.getvalue())


class TheGateReportsEveryFindingAcrossEveryQueuedOrchestrator(unittest.TestCase):
    """E-03 / V-03: Collect-then-partition batch reporting across all queued orchestrators."""

    def test_queue_with_three_non_conforming_orchestrators_reports_all_findings_in_one_exit(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)

            p1 = plans_dir / "20260924-fixbad-00-bad001.ipd.md"
            p2 = plans_dir / "20260924-fixbad2-00-bad002.ipd.md"
            p3 = plans_dir / "20260924-fixbad3-00-bad003.ipd.md"
            p1.write_text(NON_CONFORMING_ORCH_1_TEXT, encoding="utf-8")
            p2.write_text(NON_CONFORMING_ORCH_2_TEXT, encoding="utf-8")
            p3.write_text(NON_CONFORMING_ORCH_3_TEXT, encoding="utf-8")

            state = {
                "queue": [
                    {
                        "id6": "bad001",
                        "kind": "orchestrator",
                        "position": 1,
                        "setid": "fixbad",
                        "configured_file": str(p1),
                    },
                    {
                        "id6": "bad002",
                        "kind": "orchestrator",
                        "position": 2,
                        "setid": "fixbad2",
                        "configured_file": str(p2),
                    },
                    {
                        "id6": "bad003",
                        "kind": "orchestrator",
                        "position": 3,
                        "setid": "fixbad3",
                        "configured_file": str(p3),
                    },
                ]
            }

            with self.assertRaises(rs.DriverError) as cm:
                rs.enforce_orchestrator_shape_gate(state, repo=repo)

            msg = str(cm.exception)
            self.assertIn("IPD-S407", msg)
            self.assertIn("bad001", msg)
            self.assertIn("bad002", msg)
            self.assertIn("bad003", msg)
            self.assertIn("3 queued orchestrators", msg)


class TheProbeSurvivesAndRefusalsAreDistinct(unittest.TestCase):
    """E-04 / V-04: Probe coexistence on bare indented prose; distinct rule IDs; both hosts refuse."""

    def test_conforming_rows_with_bare_indented_obligation_is_refused_by_probe(self):
        """Conforming rows pass shape check, while bare indented obligation is caught by the probe."""
        res = lint.orchestrator_row_conformance(
            CONFORMING_WITH_BARE_INDENTED_PROSE_TEXT
        )
        self.assertTrue(
            res.conforming,
            "Shape check must pass conforming rows with continuation lines",
        )

        # The probe excerpt includes the bare indented continuation line
        excerpt = rs.orchestrator_probe_excerpt(
            CONFORMING_WITH_BARE_INDENTED_PROSE_TEXT
        )
        self.assertIn("Establish the characterization baseline", excerpt)

        # Injected probe double returning EXECUTIONS (uncovered work)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            p = plans_dir / "20260924-fixprose-00-prs001.ipd.md"
            p.write_text(CONFORMING_WITH_BARE_INDENTED_PROSE_TEXT, encoding="utf-8")

            state = {
                "queue": [
                    {
                        "id6": "prs001",
                        "kind": "orchestrator",
                        "position": 1,
                        "setid": "fixprose",
                        "configured_file": str(p),
                    },
                ]
            }

            # Shape gate passes cleanly
            outcomes = rs.enforce_orchestrator_shape_gate(state, repo=repo)
            self.assertEqual(len(outcomes), 1)

            # Probe gate refuses with probe refusal code
            run_dir = rs.state_root(repo) / "run-test"
            run_dir.mkdir(parents=True)
            (run_dir / "events.jsonl").touch()

            def double_asker(*args, **kwargs):
                return (
                    rs.PROBE_ANSWER_EXECUTIONS,
                    "uncovered work found in bare continuation line",
                )

            decision = rs.enforce_orchestrator_probe_gate(
                run_dir,
                state,
                repo=repo,
                host="oc",
                interactive=False,
                write_report_fn=lambda *a: None,
                asker=double_asker,
            )
            self.assertFalse(decision.proceed)
            self.assertIn(
                "orchestrator coverage probe reports that prs001", decision.message
            )

    def test_rule_ids_differ_between_shape_and_probe_refusals(self):
        """Shape refusal names IPD-S407; probe refusal names orchestrator-uncovered-work."""
        shape_code = lint.C_ORCH_ROW
        probe_code = rs.PROBE_REFUSAL_CODE
        self.assertEqual(shape_code, "IPD-S407")
        self.assertEqual(probe_code, "orchestrator-uncovered-work")
        self.assertNotEqual(shape_code, probe_code)

    def test_both_hosts_behaviourally_refuse_non_conforming_orchestrators(self):
        """Both oc and agy initialize_run refuse non-conforming orchestrators with IPD-S407."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label, module in BOTH_HOSTS:
                with self.subTest(host=label):
                    repo = root / f"repo-{label}"
                    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
                    plans_dir.mkdir(parents=True)
                    subprocess.run(["git", "init", "-q", str(repo)], check=True)
                    (plans_dir / "20260924-fixbad-00-bad001.ipd.md").write_text(
                        NON_CONFORMING_ORCH_1_TEXT, encoding="utf-8"
                    )

                    args = module.build_parser().parse_args(
                        ["start", "bad001", "--repo", str(repo)]
                    )
                    with self.assertRaises(rs.DriverError) as cm:
                        module.initialize_run(args)
                    self.assertIn("IPD-S407", str(cm.exception))


class TheShapeRefusalSpendsZeroModelCalls(unittest.TestCase):
    """E-05 / V-05: Shape refusal spends zero probe invocations."""

    def test_shape_refusal_spends_zero_probe_invocations(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (plans_dir / "20260924-fixbad-00-bad001.ipd.md").write_text(
                NON_CONFORMING_ORCH_1_TEXT, encoding="utf-8"
            )

            counter: list[str] = []

            def probe_double(*args, **kwargs):
                counter.append("called")
                return rs.PROBE_ANSWER_EXECUTIONS, "double"

            with unittest.mock.patch.object(rs, "ask_orchestrator_probe", probe_double):
                args = oc_runipd.build_parser().parse_args(
                    ["start", "bad001", "--repo", str(repo)]
                )
                with self.assertRaises(rs.DriverError):
                    oc_runipd.initialize_run(args)

            self.assertEqual(
                counter, [], "Probe double must not be invoked on shape refusal"
            )


class TestOrchestratorProbeFormatting(unittest.TestCase):
    """Observable behavior tests for orchestrator coverage probe refusal formatting and bold yellow id6 highlighting."""

    def test_format_orchestrator_probe_refusal_plain(self):
        """Plain-text formatting structures problem, remedy steps, and override instructions."""
        formatted = rs.format_orchestrator_probe_refusal(
            rs.OC_HOST_LABELS, ["1u4olp"], color=False
        )
        # Structured problem statement
        self.assertIn(
            "The orchestrator coverage probe reports that 1u4olp carries work no child covers.",
            formatted,
        )
        self.assertIn("SKIPS the\npre-transition E/V checkpoint", formatted)
        # Structured remedy steps
        self.assertIn("ADD A CHILD for the uncovered work:", formatted)
        self.assertIn("1. Author a child plan of 1u4olp's Set that owns it.", formatted)
        self.assertIn(
            "2. Add its row to the orchestrator's `## Child IPDs` table.", formatted
        )
        self.assertIn("3. Leave the parent's existing checklist in place.", formatted)
        self.assertIn(
            "4. Re-run `aw oc run`; the coverage answer recorded in the plan is re-checked automatically",
            formatted,
        )
        # Override option
        self.assertIn(
            "--allow-uncovered-orchestrator-work '<why you accept it>'", formatted
        )
        # No ANSI codes present when color=False
        self.assertNotIn("\033[", formatted)

    def test_format_orchestrator_probe_refusal_bold_yellow_id6(self):
        """When color is enabled, references to id6 are highlighted in bold yellow."""
        formatted = rs.format_orchestrator_probe_refusal(
            rs.OC_HOST_LABELS, ["1u4olp"], color=True
        )
        bold_yellow_id6 = "\033[1;33m1u4olp\033[0m"
        # Highlighted in finding
        self.assertIn(f"reports that {bold_yellow_id6} carries", formatted)
        # Highlighted in remedy step 1
        self.assertIn(f"child plan of {bold_yellow_id6}'s Set", formatted)
        # Stripped of ANSI, matches plain text
        from agent_workflows.term import strip_ansi

        plain = rs.format_orchestrator_probe_refusal(
            rs.OC_HOST_LABELS, ["1u4olp"], color=False
        )
        self.assertEqual(strip_ansi(formatted), plain)

    def test_format_orchestrator_probe_refusal_multiple_orchestrators(self):
        """Plural verb and multiple bold yellow id6 tokens when multiple orchestrators block."""
        formatted = rs.format_orchestrator_probe_refusal(
            rs.OC_HOST_LABELS, ["1u4olp", "xhr0dj"], color=True
        )
        bold_yellow_1 = "\033[1;33m1u4olp\033[0m"
        bold_yellow_2 = "\033[1;33mxhr0dj\033[0m"
        self.assertIn(
            f"reports that {bold_yellow_1}, {bold_yellow_2} carry work", formatted
        )
        self.assertIn(
            f"the affected Set(s) ({bold_yellow_1}, {bold_yellow_2})", formatted
        )

    def test_format_orchestrator_probe_prompt(self):
        """Interactive prompt has clean line separation and confirm phrase."""
        prompt_text = rs.format_orchestrator_probe_prompt(
            rs.OC_HOST_LABELS, ["1u4olp"], color=True
        )
        self.assertTrue(prompt_text.startswith("\n"))
        self.assertTrue(
            prompt_text.endswith(
                f"\n\nType '{rs.PROBE_CONFIRM_PHRASE}' to launch anyway, anything else to refuse: "
            )
        )
        bold_yellow_id6 = "\033[1;33m1u4olp\033[0m"
        self.assertIn(bold_yellow_id6, prompt_text)

    def test_enforce_orchestrator_probe_gate_color_integration(self):
        """enforce_orchestrator_probe_gate integrates color for prompt and decision.message."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plans_dir = repo / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)
            p = plans_dir / "20260924-fixprose-00-prs001.ipd.md"
            p.write_text(CONFORMING_WITH_BARE_INDENTED_PROSE_TEXT, encoding="utf-8")
            state = {
                "queue": [
                    {
                        "id6": "prs001",
                        "kind": "orchestrator",
                        "position": 1,
                        "setid": "fixprose",
                        "configured_file": str(p),
                    }
                ]
            }
            run_dir = rs.state_root(repo) / "run-test"
            run_dir.mkdir(parents=True)
            (run_dir / "events.jsonl").touch()

            def double_asker(*args, **kwargs):
                return (rs.PROBE_ANSWER_EXECUTIONS, "uncovered work found")

            captured_prompts: list[str] = []

            def mock_prompt(q):
                captured_prompts.append(q)
                return None  # refuse

            # Test with color=True
            decision_color = rs.enforce_orchestrator_probe_gate(
                run_dir,
                state,
                repo=repo,
                host="oc",
                interactive=True,
                write_report_fn=lambda *a: None,
                asker=double_asker,
                prompt=mock_prompt,
                color=True,
            )
            self.assertFalse(decision_color.proceed)
            bold_yellow_id6 = "\033[1;33mprs001\033[0m"
            self.assertIn(bold_yellow_id6, decision_color.message)
            self.assertEqual(len(captured_prompts), 1)
            self.assertIn(bold_yellow_id6, captured_prompts[0])

            # Test with color=False
            captured_prompts.clear()
            decision_plain = rs.enforce_orchestrator_probe_gate(
                run_dir,
                state,
                repo=repo,
                host="oc",
                interactive=True,
                write_report_fn=lambda *a: None,
                asker=double_asker,
                prompt=mock_prompt,
                color=False,
            )
            self.assertFalse(decision_plain.proceed)
            self.assertNotIn("\033[", decision_plain.message)
            self.assertIn("prs001", decision_plain.message)
            self.assertEqual(len(captured_prompts), 1)
            self.assertNotIn("\033[", captured_prompts[0])
            self.assertIn("prs001", captured_prompts[0])


if __name__ == "__main__":
    unittest.main()
