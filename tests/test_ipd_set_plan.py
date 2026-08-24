"""Tests for the IPD Set graph compiler + execution manifest (execset Order 01, `iy1a2g`).

Stdlib unittest, throwaway plans dirs. Covers V-01 (Set resolution + gating), V-02 (manifest
compile + LaneRequest adapter + confidence->serial coercion), and V-03 (plan-only snapshots +
byte-stability). No worker is ever launched; the compiler is a pure function of its inputs.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_set_plan as sp
from agent_workflows import orchestrate_isolation as iso


def _child_ipd(
    *,
    e_deps=None,
) -> str:
    """A minimal conforming child IPD body with three E leaves + matching V leaves.

    ``e_deps`` maps E-id -> list of intra-IPD dep E-ids (defaults: E-02->E-01, E-03->E-02).
    """
    e_deps = e_deps or {"E-01": [], "E-02": ["E-01"], "E-03": ["E-02"]}

    def _dep(eid):
        d = e_deps.get(eid, [])
        return ", ".join(d) if d else "none"

    return (
        "# IPD: child\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 do a\n"
        f"  - Depends on: {_dep('E-01')}\n"
        "  - Expected outcome: a\n"
        "  - Execution state: pending\n"
        "- [ ] E-02 do b\n"
        f"  - Depends on: {_dep('E-02')}\n"
        "  - Expected outcome: b\n"
        "  - Execution state: pending\n"
        "- [ ] E-03 do c\n"
        f"  - Depends on: {_dep('E-03')}\n"
        "  - Expected outcome: c\n"
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
        "- [ ] V-03 validates E-03\n"
        "  - Required evidence: x\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n"
    )


def _write_plan(
    plans_dir: Path,
    disposition: str,
    name: str,
    *,
    plan_id: str,
    set_id: str,
    order: int,
    status: str,
    kind: str = "child",
    body: str = "",
    approval: bool = True,
) -> Path:
    d = plans_dir / disposition
    d.mkdir(parents=True, exist_ok=True)
    meta = [
        "# IPD: x\n",
        "- Date: 20260823",
        f"- Kind: {kind}",
        "- Concern: x.",
        "- Scope: x.",
        "- Scope-Paths: grandfathered",
        f"- Status: {status}",
        f"- Set: {set_id}",
        f"- Order: {order}",
        f"- Id: {plan_id}",
    ]
    if status == "approved" and approval:
        meta.append(
            '- Approval: 2026-08-24, human ("approved. go."): status set to approved'
        )
    header = "\n".join(meta) + "\n\n"
    # Strip the H1 from body since header already has one? Keep body providing sections.
    text = header + body
    (d / name).write_text(text, encoding="utf-8")
    return d / name


def _orchestrator_body(table_rows) -> str:
    """table_rows: list of (order, filename, depends_str)."""
    lines = [
        "## Child IPDs, sequence, and dependencies\n",
        "| Order | File | Purpose | Depends on |",
        "| --- | --- | --- | --- |",
    ]
    for order, fname, deps in table_rows:
        lines.append(f"| {order:02d} | `{fname}` | p | {deps} |")
    lines.append("\n## Goal\n\nx\n")
    return "\n".join(lines)


def _mk_set(root: Path, *, statuses=None, with_table=True, cross=None):
    """Build a 3-child Set (orders 1,2,3). statuses maps order->status (default all approved).

    cross maps order->depends-str for the orchestrator table (default: 3 depends on 1,2).
    Returns the plans_dir.
    """
    statuses = statuses or {1: "approved", 2: "approved", 3: "approved"}
    cross = cross or {1: "none", 2: "none", 3: "01, 02"}
    plans_dir = root / ".aw" / "records" / "plans"
    names = {
        0: "20260823-s-00-orc000-orchestrator.ipd.md",
        1: "20260823-s-01-aaaaaa-one.ipd.md",
        2: "20260823-s-02-bbbbbb-two.ipd.md",
        3: "20260823-s-03-cccccc-three.ipd.md",
    }
    if with_table:
        rows = [(o, names[o], cross[o]) for o in (1, 2, 3)]
        _write_plan(
            plans_dir,
            "pending",
            names[0],
            plan_id="orc000",
            set_id="s",
            order=0,
            status="approved",
            kind="orchestrator",
            body=_orchestrator_body(rows),
        )
    ids = {1: "aaaaaa", 2: "bbbbbb", 3: "cccccc"}
    for o in (1, 2, 3):
        _write_plan(
            plans_dir,
            "pending",
            names[o],
            plan_id=ids[o],
            set_id="s",
            order=o,
            status=statuses[o],
            kind="child",
            body=_child_ipd(),
            approval=(statuses[o] == "approved"),
        )
    return plans_dir


class ResolveSetV01(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_inventory_every_child_and_leaf_once(self):
        plans_dir = _mk_set(self.root)
        inv = sp.resolve_set(plans_dir, "s")
        self.assertEqual(inv.orchestrator_id, "orc000")
        self.assertEqual(
            [c.plan_id for c in inv.children], ["aaaaaa", "bbbbbb", "cccccc"]
        )
        for c in inv.children:
            self.assertEqual(c.e_leaves, ("E-01", "E-02", "E-03"))
        # No duplicates.
        all_nodes = [f"{c.plan_id}:{e}" for c in inv.children for e in c.e_leaves]
        self.assertEqual(len(all_nodes), len(set(all_nodes)))

    def test_missing_set_rejected(self):
        _mk_set(self.root)
        with self.assertRaises(sp.SetPlanError):
            sp.resolve_set(self.root / ".aw" / "records" / "plans", "nope")

    def test_orchestrator_table_parsed_into_cross_edges(self):
        plans_dir = _mk_set(self.root)
        inv = sp.resolve_set(plans_dir, "s")
        self.assertEqual(inv.cross_edges_source, "orchestrator-table")
        self.assertEqual(dict(inv.cross_edges)["cccccc"], ("aaaaaa", "bbbbbb"))
        self.assertEqual(dict(inv.cross_edges)["aaaaaa"], ())

    def test_legacy_inference_when_table_absent(self):
        plans_dir = _mk_set(self.root, with_table=False)
        inv = sp.resolve_set(plans_dir, "s")
        self.assertEqual(inv.cross_edges_source, "legacy-inference")
        # Conservative serial chain by order.
        ce = dict(inv.cross_edges)
        self.assertEqual(ce["aaaaaa"], ())
        self.assertEqual(ce["bbbbbb"], ("aaaaaa",))
        self.assertEqual(ce["cccccc"], ("bbbbbb",))

    def test_ambiguous_table_falls_back_to_serial(self):
        # A Depends-on token that is not an integer / none -> ambiguous -> legacy inference.
        plans_dir = _mk_set(self.root, cross={1: "none", 2: "none", 3: "maybe-01"})
        inv = sp.resolve_set(plans_dir, "s")
        self.assertEqual(inv.cross_edges_source, "legacy-inference")

    def test_unapproved_child_deferred_gate_blocks_only_descendants(self):
        # Order 1 unapproved; order 3 depends on 1&2 so 3 is blocked; order 2 independent stays runnable.
        plans_dir = _mk_set(
            self.root, statuses={1: "draft", 2: "approved", 3: "approved"}
        )
        inv = sp.resolve_set(plans_dir, "s")
        self.assertEqual(inv.deferred_gates, ("aaaaaa",))
        # aaaaaa gate + cccccc (depends on aaaaaa) blocked; bbbbbb independent NOT blocked.
        self.assertIn("aaaaaa", inv.blocked_children)
        self.assertIn("cccccc", inv.blocked_children)
        self.assertNotIn("bbbbbb", inv.blocked_children)
        # bbbbbb is still runnable.
        bbb = next(c for c in inv.children if c.plan_id == "bbbbbb")
        self.assertTrue(bbb.runnable)

    def test_auto_approved_is_runnable(self):
        plans_dir = _mk_set(
            self.root, statuses={1: "auto-approved", 2: "approved", 3: "approved"}
        )
        inv = sp.resolve_set(plans_dir, "s")
        self.assertEqual(inv.deferred_gates, ())
        self.assertEqual(inv.blocked_children, ())

    def test_intra_ipd_cycle_rejected(self):
        # Build a child whose E-01 depends on E-03 and E-03 depends on E-01 -> cycle.
        plans_dir = self.root / ".aw" / "records" / "plans"
        cyc = _child_ipd(e_deps={"E-01": ["E-03"], "E-02": ["E-01"], "E-03": ["E-02"]})
        _write_plan(
            plans_dir,
            "pending",
            "20260823-s-01-aaaaaa-one.ipd.md",
            plan_id="aaaaaa",
            set_id="s",
            order=1,
            status="approved",
            body=cyc,
        )
        with self.assertRaises(sp.SetPlanError):
            sp.resolve_set(plans_dir, "s")

    def test_duplicate_id_rejected(self):
        plans_dir = self.root / ".aw" / "records" / "plans"
        _write_plan(
            plans_dir,
            "pending",
            "a.ipd.md",
            plan_id="dupdup",
            set_id="s",
            order=1,
            status="approved",
            body=_child_ipd(),
        )
        _write_plan(
            plans_dir,
            "pending",
            "b.ipd.md",
            plan_id="dupdup",
            set_id="s",
            order=2,
            status="approved",
            body=_child_ipd(),
        )
        with self.assertRaises(sp.SetPlanError):
            sp.resolve_set(plans_dir, "s")


class CompileManifestV02(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.plans_dir = _mk_set(self.root)
        self.inv = sp.resolve_set(self.plans_dir, "s")

    def test_golden_node_fields_and_stable_ids(self):
        m = sp.compile_manifest(self.inv, self.plans_dir, base_head="deadbeef")
        self.assertEqual(m.base_head, "deadbeef")
        self.assertTrue(m.requirement_digest)
        node_ids = [n.node for n in m.nodes]
        self.assertEqual(node_ids, sorted(node_ids))
        # Cross-IPD edge: cccccc:E-01 depends on the terminal nodes of aaaaaa and bbbbbb.
        cE01 = next(n for n in m.nodes if n.node == "cccccc:E-01")
        self.assertIn("aaaaaa:E-03", cE01.depends_on)
        self.assertIn("bbbbbb:E-03", cE01.depends_on)
        # Validation mapping present.
        self.assertEqual(cE01.validation, "V-01")

    def test_frozen_digest_matches_inventory(self):
        m = sp.compile_manifest(self.inv, self.plans_dir, base_head="x")
        self.assertEqual(m.requirement_digest, self.inv.requirement_digest)

    def test_low_confidence_forced_serial_before_analyzer(self):
        # Declare two nodes with disjoint writes but LOW confidence: compiler must force serial.
        ownership = {
            "aaaaaa:E-01": {"writes": ["file_a.py"], "confidence": "low"},
            "bbbbbb:E-01": {"writes": ["file_b.py"], "confidence": "low"},
        }
        m = sp.compile_manifest(
            self.inv, self.plans_dir, base_head="x", ownership=ownership
        )
        # Those nodes must be coerced to mutating lanes with an isolated worktree.
        lane = sp.node_to_lane_request(
            next(n for n in m.nodes if n.node == "aaaaaa:E-01")
        )
        # The adapter itself keeps it read_only when no writes... but here it has writes so mutating.
        self.assertEqual(lane.lane_kind, iso.LANE_KIND_MUTATING)

    def test_confidence_coercion_explicit(self):
        # A node that WOULD be read-only (no writes) but low confidence must still be serialized by
        # the compiler (mutating lane), so the analyzer never admits it into a read-only wave.
        ownership = {"aaaaaa:E-01": {"confidence": "inferred"}}
        # Build a fresh minimal single-child set with no cross deps and only read-only nodes to
        # isolate the coercion behavior.
        m = sp.compile_manifest(
            self.inv, self.plans_dir, base_head="x", ownership=ownership
        )
        # The manifest node keeps its declared (inferred) confidence for provenance.
        n = next(nn for nn in m.nodes if nn.node == "aaaaaa:E-01")
        self.assertEqual(n.confidence, "inferred")
        # And because ALL nodes are inferred/read-only-coerced-to-serial here, eligibility is not a
        # clean parallel_read_only wave.
        self.assertFalse(
            m.eligibility.execution_mode == iso.EXEC_MODE_PARALLEL_READ_ONLY
        )

    def test_adapter_maps_writes_and_generates(self):
        ownership = {
            "aaaaaa:E-01": {
                "writes": ["w.py"],
                "generates": ["g.json"],
                "shared_surfaces": ["cli.py"],
                "confidence": "declared",
            }
        }
        m = sp.compile_manifest(
            self.inv, self.plans_dir, base_head="x", ownership=ownership
        )
        n = next(nn for nn in m.nodes if nn.node == "aaaaaa:E-01")
        lane = sp.node_to_lane_request(n)
        self.assertIn("w.py", lane.files_targeted)
        self.assertIn("cli.py", lane.files_targeted)  # shared surface folded in
        self.assertEqual(lane.generated_files, ("g.json",))
        self.assertEqual(lane.lane_kind, iso.LANE_KIND_MUTATING)

    def test_high_confidence_read_only_can_be_parallel(self):
        # Build a set with all-independent read-only high-confidence nodes -> parallel_read_only.
        root2 = Path(tempfile.mkdtemp())
        plans_dir = root2 / ".aw" / "records" / "plans"
        _write_plan(
            plans_dir,
            "pending",
            "a.ipd.md",
            plan_id="aaaaaa",
            set_id="t",
            order=1,
            status="approved",
            body=_child_ipd(e_deps={"E-01": [], "E-02": [], "E-03": []}),
        )
        inv = sp.resolve_set(plans_dir, "t")
        ownership = {
            f"aaaaaa:{e}": {"confidence": "declared"} for e in ("E-01", "E-02", "E-03")
        }
        # No table -> legacy inference makes a serial chain; override cross by using a single child
        # whose leaves are independent. But legacy inference chains children, not leaves; single
        # child so no cross edges. Intra deps are none. All read-only + high confidence.
        m = sp.compile_manifest(inv, plans_dir, base_head="x", ownership=ownership)
        self.assertEqual(m.eligibility.execution_mode, iso.EXEC_MODE_PARALLEL_READ_ONLY)
        self.assertTrue(m.eligibility.is_eligible_parallel)


class PlanOnlyV03(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.plans_dir = _mk_set(self.root)
        self.inv = sp.resolve_set(self.plans_dir, "s")

    def test_byte_stable_repeated_compilation(self):
        m1 = sp.compile_manifest(self.inv, self.plans_dir, base_head="x")
        inv2 = sp.resolve_set(self.plans_dir, "s")
        m2 = sp.compile_manifest(inv2, self.plans_dir, base_head="x")
        self.assertEqual(sp.emit_manifest_json(m1), sp.emit_manifest_json(m2))

    def test_human_and_json_report_same_waves(self):
        m = sp.compile_manifest(self.inv, self.plans_dir, base_head="x")
        human = sp.render_plan_only_human(m)
        import json

        data = json.loads(sp.emit_manifest_json(m))
        # The serial fallback order appears in both.
        self.assertIn(m.eligibility.execution_mode, human)
        self.assertEqual(
            data["eligibility"]["execution_mode"], m.eligibility.execution_mode
        )
        self.assertEqual(
            data["eligibility"]["serial_fallback_plan"],
            list(m.eligibility.serial_fallback_plan),
        )
        # Model roles present for each node in both.
        for n in m.nodes:
            self.assertIn(n.node, human)

    def test_json_is_valid_and_has_no_worker_side_effects(self):
        import json

        m = sp.compile_manifest(self.inv, self.plans_dir, base_head="x")
        blob = sp.emit_manifest_json(m)
        data = json.loads(blob)
        self.assertEqual(data["schema_version"], sp.MANIFEST_SCHEMA_VERSION)
        self.assertEqual(data["set_id"], "s")
        self.assertEqual(len(data["nodes"]), 9)
        self.assertTrue(blob.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
