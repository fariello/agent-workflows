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

import ast
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
from tests.support import REPO_ROOT

BOTH_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))

# ==================================================================================================
# FIXTURES
# ==================================================================================================

CONFORMING_ORCH_TEXT = """# IPD: Conforming orchestrator fixture

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Status: approved
- Set: fixconf
- Order: 0
- Highest E allocated: 02
- Author: fixture
- Id: fix001
- Approval: 2026-09-24, fixture

## Workflow history

- 2026-09-24 approved (fixture): created.

## Goal

Fixture.

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixconf-01-chd001.ipd.md | none |
| 02 | chd002 | pending | .aw/records/plans/pending/20260924-fixconf-02-chd002.ipd.md | 01 |

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  - Depends on: none
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending
- [ ] E-02 CONFIRM chd002 REACHED executed
  - Depends on: E-01
  - Expected outcome: chd002 reads `- Status: executed` on disk.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: check status.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: check status.
  - Observed evidence:
  - Result: pending
"""

NON_CONFORMING_ORCH_1_TEXT = """# IPD: Non-conforming orchestrator 1 (untyped prose row)

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Status: approved
- Set: fixbad
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: bad001
- Approval: 2026-09-24, fixture

## Workflow history

- 2026-09-24 approved (fixture): created.

## Goal

Fixture.

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixbad-01-chd001.ipd.md | none |

## Detailed Implementation Checklist (TODO)

- [ ] E-01 Establish the characterization baseline before any child runs
  - Depends on: none
  - Expected outcome: baseline established.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: check baseline.
  - Observed evidence:
  - Result: pending
"""

NON_CONFORMING_ORCH_2_TEXT = """# IPD: Non-conforming orchestrator 2 (unknown child id6)

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Status: approved
- Set: fixbad2
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: bad002
- Approval: 2026-09-24, fixture

## Workflow history

- 2026-09-24 approved (fixture): created.

## Goal

Fixture.

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixbad2-01-chd001.ipd.md | none |

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM unk999 REACHED executed
  - Depends on: none
  - Expected outcome: unk999 reads `- Status: executed` on disk.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: check status.
  - Observed evidence:
  - Result: pending
"""

NON_CONFORMING_ORCH_3_TEXT = """# IPD: Non-conforming orchestrator 3 (missing depends on)

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Status: approved
- Set: fixbad3
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: bad003
- Approval: 2026-09-24, fixture

## Workflow history

- 2026-09-24 approved (fixture): created.

## Goal

Fixture.

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixbad3-01-chd001.ipd.md | none |

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: check status.
  - Observed evidence:
  - Result: pending
"""

CONFORMING_WITH_BARE_INDENTED_PROSE_TEXT = """# IPD: Conforming rows with bare indented prose obligation

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Status: approved
- Set: fixprose
- Order: 0
- Highest E allocated: 01
- Author: fixture
- Id: prs001
- Approval: 2026-09-24, fixture

## Workflow history

- 2026-09-24 approved (fixture): created.

## Goal

Fixture.

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixprose-01-chd001.ipd.md | none |

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  Establish the characterization baseline before any child runs and produce the inventory report.
  - Depends on: none
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: check status.
  - Observed evidence:
  - Result: pending
"""


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

    def test_oc_to_agy_import_count_did_not_increase(self):
        """No symbols flow from oc_runipd to agy_runipd for this gate."""
        tree = ast.parse(
            (REPO_ROOT / "agent_workflows" / "agy_runipd.py").read_text(
                encoding="utf-8"
            )
        )
        oc_imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "agent_workflows.oc_runipd"
            for alias in node.names
        ]
        self.assertLessEqual(len(oc_imports), 4)

    def test_queued_orchestrator_targets_is_reused(self):
        """Assert enforce_orchestrator_shape_gate reuses queued_orchestrator_targets."""
        tree = ast.parse(
            (REPO_ROOT / "agent_workflows" / "runner_shared.py").read_text(
                encoding="utf-8"
            )
        )
        calls = [
            inner.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "enforce_orchestrator_shape_gate"
            for inner in ast.walk(node)
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
        ]
        self.assertIn("queued_orchestrator_targets", calls)


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

    def test_siting_comment_names_both_invariants(self):
        """Code comment in initialize_run_core explains siting, no durable writes, and --prepare-only."""
        src = (REPO_ROOT / "agent_workflows" / "runner_shared.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("THE PRE-QUEUE ORCHESTRATOR SHAPE GATE", src)
        self.assertIn("--prepare-only", src)
        self.assertIn("NO DURABLE WRITE", src)

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
        for label, module in BOTH_HOSTS:
            with self.subTest(host=label):
                repo = self.make_repo(
                    CONFORMING_ORCH_TEXT, "20260924-fixconf-00-fix001.ipd.md"
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


if __name__ == "__main__":
    unittest.main()
