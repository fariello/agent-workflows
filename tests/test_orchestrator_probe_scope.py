"""Tests for IPD 5etev3: orchestrator probe scope and retirement re-check.

Validates:
(a) a queue of one review orchestrator plus children makes zero asker calls and proceeds;
(b) a queue with one orchestrate orchestrator calls the asker once;
(c) the event records skipped id6s;
(d) dispatch_orchestrator_item over a fixture Set whose children are all executed and whose
    orchestrator text was edited after a recorded pass refuses retirement and records a refusal
    quoting the new passage;
(e) the same with unchanged text retires with zero asker calls;
(f) the override flag does not change (d);
(g) a could-not-ask at retirement refuses and names `aw ipd coverage <id6>`;
(h) both hosts' run_queue reach the re-check with their own host string;
(i) a Set with one superseded/ child and one executed/ child and a current pass record still retires
    (the 31y86f property; it fails if E-02 lets a condition 1 to 3 finding refuse).
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, coverage_record, oc_runipd, runner_shared
from agent_workflows import ipd_lifecycle as LC


def _make_plan_text(
    *,
    id6: str,
    setid: str,
    order: int,
    status: str,
    kind: str = "child",
    declared_children: tuple[tuple[str, str], ...] = (),
    goal: str = "Standard test goal.",
) -> str:
    if kind == "orchestrator":
        table_rows = []
        e_items = []
        for idx, (ch_order, ch_id6) in enumerate(declared_children, start=1):
            table_rows.append(
                f"| {ch_order} | {ch_id6} | pending | .aw/records/plans/pending/20261004-{setid}-{ch_order}-{ch_id6}-synthetic.ipd.md | none |"
            )
            e_items.append(
                f"- [ ] E-{idx:02d} CONFIRM {ch_id6} REACHED executed\n"
                f"  - Depends on: none\n"
                f"  - Expected outcome: {ch_id6} reads `- Status: executed` on disk.\n"
                f"  - Execution state: pending"
            )
        child_table = (
            "## Child IPDs, sequence, and dependencies\n\n"
            "| Order | Id | Status | Plan | Depends on |\n"
            "| --- | --- | --- | --- | --- |\n" + "\n".join(table_rows) + "\n\n"
        )
        e_section = (
            "\n".join(e_items)
            if e_items
            else "- [ ] E-01 Synthetic step\n  - Execution state: pending"
        )
    else:
        child_table = ""
        e_section = "- [ ] E-01 Synthetic step\n" "  - Execution state: pending"

    return (
        f"# IPD: synthetic {kind} {id6}\n\n"
        "- Date: 2026-10-04\n"
        f"- Kind: {kind}\n"
        "- Concern: synthetic fixture.\n"
        "- Scope: synthetic fixture.\n"
        "- Scope-Paths: tests/**\n"
        f"- Status: {status}\n"
        f"- Set: {setid}\n"
        f"- Order: {order}\n"
        f"- Id: {id6}\n\n"
        "## Goal\n\n"
        f"{goal}\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        f"{e_section}\n\n"
        f"{child_table}"
    )


class OrchestratorProbeScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        # Initialize bare git repository
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(self.repo),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(self.repo),
            check=True,
        )

    def write_plan(
        self,
        *,
        bucket: str,
        id6: str,
        order: int,
        status: str,
        kind: str,
        setid: str,
        declared_children: tuple[tuple[str, str], ...] = (),
        declared_rows: tuple[str, ...] = (),
        goal: str = "Standard test goal.",
    ) -> Path:
        d = self.repo / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        children = declared_children
        if not children and declared_rows:
            children = tuple((tok, f"chi{tok}") for tok in declared_rows)
        path = d / f"20261004-{setid}-{order:02d}-{id6}-synthetic.ipd.md"
        path.write_text(
            _make_plan_text(
                id6=id6,
                setid=setid,
                order=order,
                status=status,
                kind=kind,
                declared_children=children,
                goal=goal,
            ),
            encoding="utf-8",
        )
        return path

    def _read_probe_gate_events(self, run_dir: Path) -> list[dict]:
        events_path = run_dir / "events.jsonl"
        if not events_path.is_file():
            return []
        events = []
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                ev = json.loads(line)
                if ev.get("event") == "orchestrator-probe-gate":
                    events.append(ev)
        return events

    def test_case_a_queue_of_review_orchestrator_plus_children_makes_zero_asker_calls_and_proceeds(
        self,
    ) -> None:
        """(a) a queue of one review orchestrator plus children makes zero asker calls and proceeds."""
        self.write_plan(
            bucket="pending",
            id6="orc001",
            order=0,
            status="to-review",
            kind="orchestrator",
            setid="seta",
            declared_children=(("01", "chi001"),),
        )
        self.write_plan(
            bucket="pending",
            id6="chi001",
            order=1,
            status="to-review",
            kind="child",
            setid="seta",
        )
        subprocess.run(["git", "add", "."], cwd=str(self.repo), check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init plans"],
            cwd=str(self.repo),
            check=True,
        )

        parser = oc_runipd.build_parser()
        args = parser.parse_args(
            [
                "start",
                "seta",
                "--action",
                "review",
                "--repo",
                str(self.repo),
                "--unattended",
                "--run-id",
                "run-case-a",
            ]
        )

        asker_calls = 0

        def spy_ask(*a, **kw):
            nonlocal asker_calls
            asker_calls += 1
            return (runner_shared.PROBE_ANSWER_NO_EXECUTIONS, "clean", ())

        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(
                runner_shared, "enforce_freeze_time_refusal", return_value=None
            ),
            mock.patch.object(
                runner_shared, "ask_orchestrator_probe", side_effect=spy_ask
            ),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            run_dir = oc_runipd.initialize_run(args)

        self.assertIsNotNone(run_dir)
        self.assertTrue((run_dir / "state.json").is_file())
        self.assertEqual(
            asker_calls, 0, "review orchestrator must not trigger probe calls"
        )
        events = self._read_probe_gate_events(run_dir)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertTrue(ev.get("proceed"))
        self.assertEqual(ev.get("probed"), [])
        self.assertEqual(ev.get("calls"), 0)
        self.assertIn("orc001", ev.get("skipped", []))
        self.assertIn("skipped 1 queued orchestrator (orc001)", err.getvalue())

    def test_case_b_queue_with_orchestrate_orchestrator_calls_asker_once(self) -> None:
        """(b) a queue with one orchestrate orchestrator calls the asker once."""
        self.write_plan(
            bucket="pending",
            id6="orc002",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="setb",
            declared_children=(("01", "chi002"),),
        )
        self.write_plan(
            bucket="pending",
            id6="chi002",
            order=1,
            status="approved",
            kind="child",
            setid="setb",
        )
        subprocess.run(["git", "add", "."], cwd=str(self.repo), check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init plans"],
            cwd=str(self.repo),
            check=True,
        )

        parser = oc_runipd.build_parser()
        args = parser.parse_args(
            [
                "start",
                "setb",
                "--repo",
                str(self.repo),
                "--unattended",
                "--run-id",
                "run-case-b",
            ]
        )

        asker_calls = 0

        def spy_ask(*a, **kw):
            nonlocal asker_calls
            asker_calls += 1
            return (runner_shared.PROBE_ANSWER_NO_EXECUTIONS, "clean", ())

        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(
                runner_shared, "enforce_freeze_time_refusal", return_value=None
            ),
            mock.patch.object(
                runner_shared, "ask_orchestrator_probe", side_effect=spy_ask
            ),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            run_dir = oc_runipd.initialize_run(args)

        self.assertIsNotNone(run_dir)
        self.assertEqual(
            asker_calls, 1, "orchestrate orchestrator must call asker once"
        )
        events = self._read_probe_gate_events(run_dir)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertTrue(ev.get("proceed"))
        self.assertEqual(ev.get("probed"), ["orc002"])
        self.assertEqual(ev.get("calls"), 1)

    def test_case_c_event_records_skipped_id6s(self) -> None:
        """(c) the event records skipped id6s."""
        # Setup: queue containing one review orchestrator and one orchestrate orchestrator
        self.write_plan(
            bucket="pending",
            id6="orc03a",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="setca",
            declared_children=(("01", "chi03a"),),
        )
        self.write_plan(
            bucket="pending",
            id6="chi03a",
            order=1,
            status="approved",
            kind="child",
            setid="setca",
        )
        self.write_plan(
            bucket="pending",
            id6="orc03b",
            order=0,
            status="to-review",
            kind="orchestrator",
            setid="setcb",
            declared_children=(("01", "chi03b"),),
        )
        self.write_plan(
            bucket="pending",
            id6="chi03b",
            order=1,
            status="to-review",
            kind="child",
            setid="setcb",
        )
        subprocess.run(["git", "add", "."], cwd=str(self.repo), check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init plans"],
            cwd=str(self.repo),
            check=True,
        )

        run_dir = self.repo / ".aw" / "records" / "runs" / "run-case-c"
        run_dir.mkdir(parents=True)
        state = {
            "queue": [
                {
                    "id6": "orc03a",
                    "kind": "orchestrator",
                    "action": "orchestrate",
                    "position": 1,
                },
                {"id6": "chi03a", "kind": "child", "action": "execute", "position": 2},
                {
                    "id6": "orc03b",
                    "kind": "orchestrator",
                    "action": "review",
                    "position": 3,
                },
                {"id6": "chi03b", "kind": "child", "action": "review", "position": 4},
            ]
        }

        def mock_ask(*a, **kw):
            return (runner_shared.PROBE_ANSWER_NO_EXECUTIONS, "clean", ())

        decision = runner_shared.enforce_orchestrator_probe_gate(
            run_dir,
            state,
            repo=self.repo,
            host="oc",
            interactive=False,
            write_report_fn=lambda *a, **k: None,
            asker=mock_ask,
        )
        self.assertTrue(decision.proceed)
        events = self._read_probe_gate_events(run_dir)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.get("probed"), ["orc03a"])
        self.assertEqual(ev.get("skipped"), ["orc03b"])

    def test_case_d_retirement_recheck_refuses_when_orchestrator_text_changed(
        self,
    ) -> None:
        """(d) dispatch_orchestrator_item over a fixture Set whose children are all executed and whose
        orchestrator text was edited after a recorded pass refuses retirement and records a refusal
        quoting the new passage.
        """
        orc_path = self.write_plan(
            bucket="pending",
            id6="orc004",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="setd",
            declared_children=(("01", "chi004"),),
        )
        self.write_plan(
            bucket="executed",
            id6="chi004",
            order=1,
            status="executed",
            kind="child",
            setid="setd",
        )
        # Write pass coverage record
        coverage_record.write(
            orc_path, verdict=coverage_record.COVERAGE_PASS, commit=False
        )

        # Now edit orchestrator text in an allowlisted section (## Goal)
        uncovered_quote = (
            "the database must be migrated manually before child execution"
        )
        content = orc_path.read_text(encoding="utf-8")
        orc_path.write_text(
            content + f"\n\n## Goal\nUncovered obligation: {uncovered_quote}\n",
            encoding="utf-8",
        )

        run_dir = self.repo / ".aw" / "records" / "runs" / "run-case-d"
        run_dir.mkdir(parents=True)
        item = {
            "id6": "orc004",
            "setid": "setd",
            "kind": "orchestrator",
            "action": "orchestrate",
            "status": "queued",
        }
        state = {
            "run_id": "run-case-d",
            "repo": str(self.repo),
            "queue": [item],
            "options": {},
        }

        retire_spy = mock.MagicMock()

        def fail_asker(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (
                runner_shared.PROBE_ANSWER_EXECUTIONS,
                f"uncovered: {uncovered_quote}",
                (uncovered_quote,),
            )

        with mock.patch.object(LC, "retire_orchestrator", retire_spy):
            decision = runner_shared.dispatch_orchestrator_item(
                self.repo,
                run_dir,
                state,
                item,
                actor="test-actor",
                terminal_states=oc_runipd.TERMINAL_STATES,
                success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                host="oc",
                asker=fail_asker,
            )

        self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
        self.assertEqual(decision.reason, runner_shared.ORCH_REASON_FINALIZE_REFUSED)
        self.assertEqual(
            item.get("orchestrator_refusal_reason"),
            runner_shared.ORCH_REASON_FINALIZE_REFUSED,
        )
        refusal_detail = item.get("orchestrator_refusal_detail", "")
        self.assertIn("retirement re-check refused:", refusal_detail)
        self.assertIn(uncovered_quote, refusal_detail)
        self.assertEqual(item.get("status"), "fail-depend")
        self.assertEqual(
            retire_spy.call_count,
            0,
            "retire_orchestrator must NOT be called on refusal",
        )

    def test_case_e_retirement_recheck_with_unchanged_text_retires_with_zero_asker_calls(
        self,
    ) -> None:
        """(e) the same with unchanged text retires with zero asker calls."""
        orc_path = self.write_plan(
            bucket="pending",
            id6="orc005",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="sete",
            declared_children=(("01", "chi005"),),
        )
        self.write_plan(
            bucket="executed",
            id6="chi005",
            order=1,
            status="executed",
            kind="child",
            setid="sete",
        )
        coverage_record.write(
            orc_path, verdict=coverage_record.COVERAGE_PASS, commit=False
        )

        run_dir = self.repo / ".aw" / "records" / "runs" / "run-case-e"
        run_dir.mkdir(parents=True)
        item = {
            "id6": "orc005",
            "setid": "sete",
            "kind": "orchestrator",
            "action": "orchestrate",
            "status": "queued",
        }
        state = {
            "run_id": "run-case-e",
            "repo": str(self.repo),
            "queue": [item],
            "options": {},
        }

        asker_calls = 0

        def exploding_asker(*a, **kw):
            nonlocal asker_calls
            asker_calls += 1
            raise AssertionError(
                "asker must not be called when coverage record is current"
            )

        class _Ok:
            exit_code = 0
            message = "retired"

        with mock.patch.object(LC, "retire_orchestrator", return_value=_Ok()):
            decision = runner_shared.dispatch_orchestrator_item(
                self.repo,
                run_dir,
                state,
                item,
                actor="test-actor",
                terminal_states=oc_runipd.TERMINAL_STATES,
                success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                host="oc",
                asker=exploding_asker,
            )

        self.assertEqual(asker_calls, 0)
        self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_RETIRE)
        self.assertEqual(item.get("status"), "executed")

        events = []
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                ev = json.loads(line)
                if ev.get("event") == "orchestrator-finalized":
                    events.append(ev)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].get("id6"), "orc005")

    def test_case_f_override_flag_does_not_bypass_retirement_recheck(self) -> None:
        """(f) the override flag does not change (d)."""
        orc_path = self.write_plan(
            bucket="pending",
            id6="orc006",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="setf",
            declared_children=(("01", "chi006"),),
        )
        self.write_plan(
            bucket="executed",
            id6="chi006",
            order=1,
            status="executed",
            kind="child",
            setid="setf",
        )
        coverage_record.write(
            orc_path, verdict=coverage_record.COVERAGE_PASS, commit=False
        )

        uncovered_quote = "must deploy secrets before child turns run"
        content = orc_path.read_text(encoding="utf-8")
        orc_path.write_text(
            content + f"\n\n## Goal\nUncovered obligation: {uncovered_quote}\n",
            encoding="utf-8",
        )

        run_dir = self.repo / ".aw" / "records" / "runs" / "run-case-f"
        run_dir.mkdir(parents=True)
        item = {
            "id6": "orc006",
            "setid": "setf",
            "kind": "orchestrator",
            "action": "orchestrate",
            "status": "queued",
        }
        state = {
            "run_id": "run-case-f",
            "repo": str(self.repo),
            "queue": [item],
            "options": {"allow_uncovered_orchestrator_work": "accepted risk at launch"},
        }

        retire_spy = mock.MagicMock()

        def fail_asker(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (
                runner_shared.PROBE_ANSWER_EXECUTIONS,
                f"uncovered: {uncovered_quote}",
                (uncovered_quote,),
            )

        with mock.patch.object(LC, "retire_orchestrator", retire_spy):
            decision = runner_shared.dispatch_orchestrator_item(
                self.repo,
                run_dir,
                state,
                item,
                actor="test-actor",
                terminal_states=oc_runipd.TERMINAL_STATES,
                success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                host="oc",
                asker=fail_asker,
            )

        self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
        self.assertEqual(decision.reason, runner_shared.ORCH_REASON_FINALIZE_REFUSED)
        refusal_detail = item.get("orchestrator_refusal_detail", "")
        self.assertIn("retirement re-check refused:", refusal_detail)
        self.assertIn(uncovered_quote, refusal_detail)
        self.assertEqual(retire_spy.call_count, 0)

    def test_case_g_could_not_ask_at_retirement_refuses_and_names_command(self) -> None:
        """(g) a could-not-ask at retirement refuses and names aw ipd coverage <id6>."""
        self.write_plan(
            bucket="pending",
            id6="orc007",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="setg",
            declared_children=(("01", "chi007"),),
        )
        self.write_plan(
            bucket="executed",
            id6="chi007",
            order=1,
            status="executed",
            kind="child",
            setid="setg",
        )
        # Plan has no coverage record (needs to ask)
        run_dir = self.repo / ".aw" / "records" / "runs" / "run-case-g"
        run_dir.mkdir(parents=True)
        item = {
            "id6": "orc007",
            "setid": "setg",
            "kind": "orchestrator",
            "action": "orchestrate",
            "status": "queued",
        }
        state = {
            "run_id": "run-case-g",
            "repo": str(self.repo),
            "queue": [item],
            "options": {},
        }

        def unavail_asker(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (
                runner_shared.PROBE_ANSWER_COULD_NOT_ASK,
                "probe host timed out",
                (),
            )

        retire_spy = mock.MagicMock()
        with mock.patch.object(LC, "retire_orchestrator", retire_spy):
            decision = runner_shared.dispatch_orchestrator_item(
                self.repo,
                run_dir,
                state,
                item,
                actor="test-actor",
                terminal_states=oc_runipd.TERMINAL_STATES,
                success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                host="oc",
                asker=unavail_asker,
            )

        self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_TERMINATE)
        self.assertEqual(decision.reason, runner_shared.ORCH_REASON_FINALIZE_REFUSED)
        refusal_detail = item.get("orchestrator_refusal_detail", "")
        self.assertIn("aw ipd coverage orc007", refusal_detail)
        self.assertEqual(retire_spy.call_count, 0)

    def test_case_h_both_hosts_run_queue_reach_recheck_with_own_host_string(
        self,
    ) -> None:
        """(h) both hosts' run_queue reach the re-check with their own host string."""
        recorded_hosts: list[tuple[str, str]] = []

        class _Ok:
            exit_code = 0
            message = "retired"

        real_ask = runner_shared.ask_orchestrator_probe

        def spy_ask(state, excerpt, *, host, repo, runner=None):
            recorded_token = ""

            def recording_runner(argv, cwd, timeout):
                nonlocal recorded_token
                recorded_token = argv[0]
                return (0, runner_shared.PROBE_SENTINEL_NO_EXECUTIONS, "")

            ans, det, quotes = real_ask(
                state, excerpt, host=host, repo=repo, runner=recording_runner
            )
            recorded_hosts.append((host, recorded_token))
            return ans, det, quotes

        for label, module, expected_token in [
            ("oc", oc_runipd, "opencode"),
            ("agy", agy_runipd, "agy"),
        ]:
            with self.subTest(host=label):
                setid = f"seth{label}"
                orc_id6 = f"orc8{label}"
                chi_id6 = f"chi8{label}"
                self.write_plan(
                    bucket="pending",
                    id6=orc_id6,
                    order=0,
                    status="approved",
                    kind="orchestrator",
                    setid=setid,
                    declared_children=(("01", chi_id6),),
                )
                self.write_plan(
                    bucket="executed",
                    id6=chi_id6,
                    order=1,
                    status="executed",
                    kind="child",
                    setid=setid,
                )
                # No coverage record, so re-check must ask probe
                run_dir = self.repo / ".aw" / "records" / "runs" / f"run-case-h-{label}"
                run_dir.mkdir(parents=True)
                item = {
                    "id6": orc_id6,
                    "setid": setid,
                    "kind": "orchestrator",
                    "action": "orchestrate",
                    "status": "queued",
                    "position": 1,
                }
                state = {
                    "schema_version": 1,
                    "run_id": f"run-case-h-{label}",
                    "repo": str(self.repo),
                    "queue": [item],
                    "options": {},
                    "host_capabilities": {
                        "host": "antigravity" if label == "agy" else "opencode"
                    },
                }
                (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
                (run_dir / "events.jsonl").touch()

                buf = io.StringIO()
                with (
                    mock.patch.object(LC, "retire_orchestrator", return_value=_Ok()),
                    mock.patch.object(
                        runner_shared, "ask_orchestrator_probe", side_effect=spy_ask
                    ),
                    contextlib.redirect_stdout(buf),
                    contextlib.redirect_stderr(buf),
                ):
                    module.run_queue(run_dir, retry_incomplete=False)

                st = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(st["queue"][0]["status"], "executed")

        self.assertEqual(len(recorded_hosts), 2)
        self.assertEqual(recorded_hosts[0], ("oc", "opencode"))
        self.assertEqual(recorded_hosts[1], ("agy", "agy"))

    def test_case_i_superseded_child_with_current_pass_record_still_retires(
        self,
    ) -> None:
        """(i) a Set with one superseded/ child and one executed/ child and a current pass record
        still retires (the 31y86f property; it fails if E-02 lets a condition 1 to 3 finding refuse).
        """
        orc_path = self.write_plan(
            bucket="pending",
            id6="orc009",
            order=0,
            status="approved",
            kind="orchestrator",
            setid="seti",
            declared_children=(("01", "chi09a"), ("02", "chi09b")),
        )
        self.write_plan(
            bucket="executed",
            id6="chi09a",
            order=1,
            status="executed",
            kind="child",
            setid="seti",
        )
        self.write_plan(
            bucket="superseded",
            id6="chi09b",
            order=2,
            status="superseded",
            kind="child",
            setid="seti",
        )
        coverage_record.write(
            orc_path, verdict=coverage_record.COVERAGE_PASS, commit=False
        )

        run_dir = self.repo / ".aw" / "records" / "runs" / "run-case-i"
        run_dir.mkdir(parents=True)
        item = {
            "id6": "orc009",
            "setid": "seti",
            "kind": "orchestrator",
            "action": "orchestrate",
            "status": "queued",
        }
        state = {
            "run_id": "run-case-i",
            "repo": str(self.repo),
            "queue": [item],
            "options": {},
        }

        class _Ok:
            exit_code = 0
            message = "retired"

        retire_spy = mock.MagicMock(return_value=_Ok())
        with mock.patch.object(LC, "retire_orchestrator", retire_spy):
            decision = runner_shared.dispatch_orchestrator_item(
                self.repo,
                run_dir,
                state,
                item,
                actor="test-actor",
                terminal_states=oc_runipd.TERMINAL_STATES,
                success_states=oc_runipd.EXECUTION_SUCCESS_STATES,
                host="oc",
            )

        self.assertEqual(decision.outcome, runner_shared.ORCH_DISPATCH_RETIRE)
        self.assertEqual(item.get("status"), "executed")
        self.assertEqual(retire_spy.call_count, 1)

        events = []
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                ev = json.loads(line)
                if ev.get("event") == "orchestrator-finalized":
                    events.append(ev)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].get("id6"), "orc009")
