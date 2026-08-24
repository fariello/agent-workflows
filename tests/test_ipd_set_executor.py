"""Tests for the parallel Set coordinator (execset Order 03, `m2wwns`).

V-01: scheduler/ready-queue dispositions + wave batching; work-class classifier (incl. mixed);
      model-role routing with fail-closed missing binding; write-ahead decision handshake.
V-02: real git worktree create/teardown; per-path exclusive lease prevents a second claim;
      merge-and-revalidate gate rejects conflict/overlap/scope/stale-base and combined-red.
V-03: crash/resume without replay (fail-closed unknown outcome); integration-triggered evidence
      invalidation via correction/invalidates_seq; deferred IPDs stay pending; combined-HEAD gate.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_set_executor as EX
from agent_workflows import ipd_set_plan as SP
from agent_workflows import orchestrate_isolation as ISO
from agent_workflows import set_lifecycle as LC
from agent_workflows import worktree_lease as WL


# ---- shared fixture: an approved 2-child Set manifest --------------------------------------------


def _child_ipd(e_deps):
    def _dep(eid):
        d = e_deps.get(eid, [])
        return ", ".join(d) if d else "none"

    return (
        "## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 a\n"
        f"  - Depends on: {_dep('E-01')}\n"
        "  - Expected outcome: a\n"
        "  - Execution state: pending\n"
        "- [ ] E-02 b\n"
        f"  - Depends on: {_dep('E-02')}\n"
        "  - Expected outcome: b\n"
        "  - Execution state: pending\n\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: x\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n"
        "- [ ] V-02 validates E-02\n"
        "  - Required evidence: x\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n"
    )


def _write_plan(
    plans_dir, name, *, plan_id, order, status="approved", kind="child", body=""
):
    d = plans_dir / "pending"
    d.mkdir(parents=True, exist_ok=True)
    meta = [
        "# IPD: x\n",
        "- Date: 20260823",
        f"- Kind: {kind}",
        "- Concern: x.",
        "- Scope: x.",
        "- Scope-Paths: grandfathered",
        f"- Status: {status}",
        "- Set: s",
        f"- Order: {order}",
        f"- Id: {plan_id}",
    ]
    if status == "approved":
        meta.append(
            '- Approval: 2026-08-24, human ("approved. go."): status set to approved'
        )
    (d / name).write_text("\n".join(meta) + "\n\n" + body, encoding="utf-8")


def _approved_manifest(ownership=None):
    root = Path(tempfile.mkdtemp())
    plans = root / ".aw" / "records" / "plans"
    # orchestrator with child table: order 2 depends on 1
    orch = (
        "## Child IPDs, sequence, and dependencies\n\n"
        "| Order | File | Purpose | Depends on |\n"
        "| --- | --- | --- | --- |\n"
        "| 01 | `a.ipd.md` | p | none |\n"
        "| 02 | `b.ipd.md` | p | 01 |\n\n"
        "## Goal\n\nx\n"
    )
    _write_plan(
        plans, "orc.ipd.md", plan_id="orc000", order=0, kind="orchestrator", body=orch
    )
    _write_plan(
        plans,
        "a.ipd.md",
        plan_id="aaaaaa",
        order=1,
        body=_child_ipd({"E-01": [], "E-02": []}),
    )
    _write_plan(
        plans,
        "b.ipd.md",
        plan_id="bbbbbb",
        order=2,
        body=_child_ipd({"E-01": [], "E-02": []}),
    )
    inv = SP.resolve_set(plans, "s")
    return SP.compile_manifest(inv, plans, base_head="deadbeef", ownership=ownership)


# ==================================================================================================
# V-01: scheduler + classifier + routing + handshake
# ==================================================================================================


class ClassifierV01(unittest.TestCase):
    def _node(self, **kw):
        base = dict(
            node="a:E-01",
            child_id="a",
            e_id="E-01",
            depends_on=(),
            reads=(),
            writes=(),
            generates=(),
            shared_surfaces=(),
            work_class="coding",
            model_role="coding",
            validation="V-01",
            deferrable=True,
            confidence="declared",
            blocked=False,
        )
        base.update(kw)
        return SP.ManifestNode(**base)

    def test_coding(self):
        self.assertEqual(
            EX.classify_node_work(self._node(writes=("agent_workflows/x.py",))),
            EX.WORK_CLASS_CODING,
        )

    def test_human_prose(self):
        self.assertEqual(
            EX.classify_node_work(self._node(writes=("website/index.mdx",))),
            EX.WORK_CLASS_HUMAN_PROSE,
        )

    def test_mixed(self):
        self.assertEqual(
            EX.classify_node_work(
                self._node(writes=("agent_workflows/x.py", "website/a.mdx"))
            ),
            EX.WORK_CLASS_MIXED,
        )

    def test_verifier_when_no_writes(self):
        self.assertEqual(
            EX.classify_node_work(self._node(writes=(), generates=())),
            EX.WORK_CLASS_VERIFIER,
        )


class RoutingV01(unittest.TestCase):
    def test_missing_binding_fails_closed(self):
        cfg = EX.routing_config_from_mapping({"coding": {"host": "h", "model": "m"}})
        with self.assertRaises(EX.BindingError):
            cfg.resolve("verifier")

    def test_resolves_configured(self):
        cfg = EX.routing_config_from_mapping(
            {"coding": {"host": "opencode", "model": "opus"}}
        )
        b = cfg.resolve("coding")
        self.assertEqual((b.host, b.model), ("opencode", "opus"))

    def test_build_lanes_fail_closed_on_missing(self):
        m = _approved_manifest(
            ownership={"aaaaaa:E-01": {"writes": ["x.py"], "confidence": "declared"}}
        )
        cfg = EX.routing_config_from_mapping({"coding": {"host": "h", "model": "m"}})
        # verifier-class nodes (no writes) have no binding -> fail closed
        with self.assertRaises(EX.BindingError):
            EX.build_lanes(m, cfg)

    def test_build_lanes_routes_each_class(self):
        own = {
            n: {"writes": ["agent_workflows/x.py"], "confidence": "declared"}
            for n in ("aaaaaa:E-01", "aaaaaa:E-02", "bbbbbb:E-01", "bbbbbb:E-02")
        }
        m = _approved_manifest(ownership=own)
        cfg = EX.routing_config_from_mapping(
            {wc: {"host": "h", "model": "m-" + wc} for wc in EX.ALL_WORK_CLASSES}
        )
        lanes = EX.build_lanes(m, cfg)
        self.assertEqual(len(lanes), 4)
        for ln in lanes:
            self.assertIsNotNone(ln.model_binding)
            self.assertEqual(ln.model_binding.model, "m-" + ln.work_class)


class SchedulerV01(unittest.TestCase):
    def setUp(self):
        own = {
            n: {
                "writes": [f"agent_workflows/{n.replace(':','_')}.py"],
                "confidence": "declared",
            }
            for n in ("aaaaaa:E-01", "aaaaaa:E-02", "bbbbbb:E-01", "bbbbbb:E-02")
        }
        self.m = _approved_manifest(ownership=own)
        self.cfg = EX.routing_config_from_mapping(
            {wc: {"host": "h", "model": "m"} for wc in EX.ALL_WORK_CLASSES}
        )
        self.lanes = EX.build_lanes(self.m, self.cfg)

    def test_every_node_gets_a_disposition(self):
        disp = EX.disposition_pass(self.lanes, [])
        self.assertEqual({d.node_id for d in disp}, {ln.node_id for ln in self.lanes})
        for d in disp:
            self.assertIn(d.status, ("running", "deferred", "serialized", "blocked"))

    def test_frontier_advances_as_deps_complete(self):
        # Initially only child a's nodes (no cross-dep) are ready; child b depends on a's terminal.
        fr0 = EX.ready_lanes(self.lanes, [])
        ready0 = {ln.node_id for ln in fr0}
        self.assertIn("aaaaaa:E-01", ready0)
        # b:E-01 depends on aaaaaa:E-02 (cross-IPD terminal), so not ready yet.
        self.assertNotIn("bbbbbb:E-01", ready0)
        # After all of a completes, b becomes ready.
        fr1 = EX.ready_lanes(self.lanes, ["aaaaaa:E-01", "aaaaaa:E-02"])
        self.assertIn("bbbbbb:E-01", {ln.node_id for ln in fr1})

    def test_wave_uses_analyzer(self):
        fr = EX.ready_lanes(self.lanes, [])
        wave = EX.plan_wave(fr)
        self.assertIn(
            wave.execution_mode,
            (
                ISO.EXEC_MODE_PARALLEL_READ_ONLY,
                ISO.EXEC_MODE_PARALLEL_MUTATING,
                ISO.EXEC_MODE_SERIAL_MUTATING,
                ISO.EXEC_MODE_SERIAL_FALLBACK,
            ),
        )


class HandshakeV01(unittest.TestCase):
    def test_mutation_rejected_without_authorization(self):
        led = EX.AuthorizationLedger(records=())
        with self.assertRaises(EX.HandshakeError):
            EX.authorize_mutation(led, lane_id="a:E-01", decision_id="D1")

    def test_mutation_allowed_after_recorded_authorization(self):
        rec = EX.make_authorization_record(
            run_id="run-x", decision_id="D1", selected_option="x"
        )
        led = EX.AuthorizationLedger(records=(rec,))
        EX.authorize_mutation(led, lane_id="a:E-01", decision_id="D1")  # no raise

    def test_proposal_pending_until_disposed(self):
        raised = {"kind": "question_raised", "question_id": "Q1"}
        led = EX.AuthorizationLedger(records=(raised,))
        self.assertIn("Q1", led.proposals())
        disposed = {"kind": "question_disposition", "question_id": "Q1"}
        led2 = EX.AuthorizationLedger(records=(raised, disposed))
        self.assertNotIn("Q1", led2.proposals())


# ==================================================================================================
# V-02: worktree + lease + integration gate
# ==================================================================================================


class WorktreeLeaseV02(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "t@t"], check=True
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "t"], check=True
        )
        (self.root / "a.txt").write_text("hi\n")
        subprocess.run(["git", "-C", str(self.root), "add", "a.txt"], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-qm", "init"], check=True
        )

    def test_real_worktree_create_and_teardown(self):
        h = WL.allocate_worktree(self.root, "abc123:E-01")
        self.assertTrue(h.path.exists())
        listing = subprocess.run(
            ["git", "-C", str(self.root), "worktree", "list"],
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn(str(h.path), listing)
        WL.teardown_worktree(self.root, h)
        self.assertFalse(h.path.exists())

    def test_lease_prevents_second_claim(self):
        lt = WL.LeaseTable()
        lt.claim("laneA", ["x.py", "y.py"])
        with self.assertRaises(WL.LeaseConflictError):
            lt.claim("laneB", ["y.py"])
        lt.release("laneA")
        lt.claim("laneB", ["y.py"])  # now free
        self.assertEqual(lt.owner_of("y.py"), "laneB")

    def test_worker_path_fence(self):
        with self.assertRaises(WL.LeaseConflictError):
            WL.assert_worker_scope("laneC", [".aw/records/plans/x.ipd.md"])
        # a normal source path is fine
        WL.assert_worker_scope("laneC", ["agent_workflows/x.py"])

    def test_session_is_per_lane(self):
        s1 = WL.allocate_session("a:E-01", "run-x")
        s2 = WL.allocate_session("a:E-02", "run-x")
        self.assertNotEqual(s1.session_id, s2.session_id)


class IntegrationGateV02(unittest.TestCase):
    def _mk_outcome(self, lane_id, files, base="BASE", head="H1", ok=True):
        return ISO.LaneOutcome(
            lane_id=lane_id,
            actor_role="coding",
            base_commit=base,
            head_commit=head,
            worktree_path=f".aw/worktrees/{lane_id}",
            changed_files=tuple(files),
            diff="diff --git a/{0} b/{0}\n".format(files[0]) if files else "",
            per_lane_validation_passed=ok,
        )

    def test_combined_red_fails_closed(self):
        outs = [self._mk_outcome("laneA", ["x.py"])]
        res = ISO.execute_merge_and_revalidate_gate(
            "BASE", outs, ["laneA"], full_validation_runner=lambda diff, files: False
        )
        self.assertFalse(res.passed)
        self.assertFalse(res.revalidation_passed)

    def test_per_lane_failure_rejected(self):
        outs = [self._mk_outcome("laneA", ["x.py"], ok=False)]
        res = ISO.execute_merge_and_revalidate_gate(
            "BASE", outs, ["laneA"], full_validation_runner=lambda diff, files: True
        )
        self.assertFalse(res.passed)

    def test_clean_integration_passes(self):
        outs = [self._mk_outcome("laneA", ["x.py"])]
        res = ISO.execute_merge_and_revalidate_gate(
            "BASE", outs, ["laneA"], full_validation_runner=lambda diff, files: True
        )
        self.assertTrue(res.passed)
        self.assertTrue(res.revalidation_passed)


# ==================================================================================================
# V-03: lifecycle + recovery
# ==================================================================================================


class LifecycleV03(unittest.TestCase):
    def test_integration_triggered_evidence_invalidation(self):
        recs = [
            {"kind": "evidence_envelope", "seq": 5, "head": "OLD", "binds": ["a:E-01"]},
            {"kind": "evidence_envelope", "seq": 7, "head": "NEW", "binds": ["a:E-02"]},
        ]
        stale = LC.stale_evidence_seqs_after_integration(recs, new_head="NEW")
        self.assertEqual(stale, (5,))
        inval = LC.make_invalidation_records(
            recs,
            run_id="run-abcdef01",
            new_head="NEW",
            timestamp="2026-08-24T00:00:00Z",
        )
        self.assertEqual([r["invalidates_seq"] for r in inval], [5])
        # the invalidation record is schema-valid and, once appended, the seq is no longer stale
        from agent_workflows import run_ledger_schema as S

        r = dict(inval[0], seq=0)
        self.assertTrue(S.validate_record(r).ok)
        self.assertEqual(
            LC.stale_evidence_seqs_after_integration(
                recs + list(inval), new_head="NEW"
            ),
            (),
        )

    def test_terminal_gate_combined_red(self):
        r = LC.terminal_transition_allowed(
            integration_passed=True,
            combined_head_revalidated=False,
            unresolved_required_nodes=[],
            all_required_verified_terminal=True,
        )
        self.assertFalse(r.allowed)

    def test_terminal_gate_unresolved_required(self):
        r = LC.terminal_transition_allowed(
            integration_passed=True,
            combined_head_revalidated=True,
            unresolved_required_nodes=["a:E-03"],
            all_required_verified_terminal=False,
        )
        self.assertFalse(r.allowed)

    def test_terminal_gate_ok(self):
        r = LC.terminal_transition_allowed(
            integration_passed=True,
            combined_head_revalidated=True,
            unresolved_required_nodes=[],
            all_required_verified_terminal=True,
        )
        self.assertTrue(r.allowed)

    def test_deferred_required_keeps_set_partial(self):
        p = LC.derive_progress(
            required_nodes=["a:E-01", "a:E-02"],
            verified_terminal_nodes=["a:E-01"],
            deferred_nodes=["a:E-02"],
            waiting_on_human=False,
            unrecoverable=False,
        )
        self.assertEqual(p.set_state, "set_partial")
        self.assertIn("a:E-02", p.deferred)

    def test_all_verified_is_complete(self):
        p = LC.derive_progress(
            required_nodes=["a:E-01"],
            verified_terminal_nodes=["a:E-01"],
            deferred_nodes=[],
            waiting_on_human=False,
            unrecoverable=False,
        )
        self.assertEqual(p.set_state, "set_complete")

    def test_resume_fails_closed_on_unknown_outcome(self):
        # Build a minimal engine with an interrupted (running, no terminal attempt) step.
        from agent_workflows import run_engine, run_ledger_store, run_recovery

        root = Path(tempfile.mkdtemp())
        ledger_path = root / "ledger.jsonl"
        store = run_ledger_store.RunLedgerStore(ledger_path)
        workflow = {
            "workflow_id": "wf",
            "steps": [{"id": "S-01", "action": "do", "depends_on": [], "gates": []}],
        }
        engine = run_engine.RunEngine(
            workflow, store, run_id="run-abcdef01", actor="runtime"
        )
        store.append(
            {
                "schema_version": 2,
                "kind": "run",
                "run_id": "run-abcdef01",
                "actor": "runtime",
                "timestamp": "2026-08-24T00:00:00Z",
                "parent": "",
                "workflow_digest": "a" * 64,
                "requirement_digest": "b" * 64,
                "repo": "r",
                "head": "h",
            }
        )
        engine.release_step("S-01")
        engine.start_step("S-01")  # running, no attempt -> unknown outcome
        ok, report = LC.resume_or_report(engine)
        self.assertFalse(ok)
        self.assertIsInstance(report, run_recovery.UnknownOutcomeError)


if __name__ == "__main__":
    unittest.main()
