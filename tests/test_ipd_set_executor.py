"""Tests for the parallel Set coordinator (execset Order 03, `m2wwns`).

V-01: scheduler/ready-queue dispositions + wave batching; work-class classifier (incl. mixed);
      model-role routing with fail-closed missing binding; write-ahead decision handshake.
V-02: real git worktree create/teardown; per-path exclusive lease prevents a second claim;
      merge-and-revalidate gate rejects conflict/overlap/scope/stale-base and combined-red.
V-03: crash/resume without replay (fail-closed unknown outcome); integration-triggered evidence
      invalidation via correction/invalidates_seq; deferred IPDs stay pending; combined-HEAD gate.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: hand one pure function
one input and assert one returned constant. The tables group by SUBJECT (the work-class classifier,
the terminal gate, the Set-state derivation, the integration gate) rather than by which V-item asked
for the case, because a V-item is provenance and not a property of the subject.

WHAT WAS A TEST PER OUTCOME IS NOW A ROW, AND WHAT WAS AN OUTCOME IS NOW A COLUMN: the classifier's
four work classes, the terminal gate's four refusal reasons plus its one permit, the seven derived
Set states, and the integration gate's typed statuses. Each of those is a CLOSED SET the rest of the
system dispatches on, so a table that lists the set makes a renumbering or a dropped branch report as
ONE failure naming every member that moved.

THE RETURNED CONSTANTS ARE ASSERTED THROUGH THE MODULE'S OWN SYMBOLS where the symbol is the
published contract (`EX.WORK_CLASS_*`, `ISO.INTEGRATION_FAILED_*`) and as LITERAL STRINGS where the
string itself is the interface consumed elsewhere (the disposition words, the `set_*` state names),
so a rename that should be a breaking change fails here.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the assertion is `assertRaises`; the setup is materially different (a real git repository on
disk, a run engine plus a ledger store); the claim is a sequence of state transitions rather than one
input-to-output mapping; or the claim is a relationship BETWEEN two calls rather than about either.
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


ALL_NODES = ("aaaaaa:E-01", "aaaaaa:E-02", "bbbbbb:E-01", "bbbbbb:E-02")


# ==================================================================================================
# V-01: scheduler + classifier + routing + handshake
# ==================================================================================================


class ClassifierV01(unittest.TestCase):
    """Which work class a node's TOUCHED PATHS put it in.

    ONE table replaces four tests. Each built a node differing only in its `writes` tuple and
    asserted one `EX.WORK_CLASS_*` constant, so the paths and the expected class are the only two
    things that ever varied: a (paths -> class) table is the natural shape.

    Why the table beats the four: the four classes are a CLOSED SET the scheduler dispatches on
    (`build_lanes` resolves a model binding per class and FAILS CLOSED on a missing one), and the
    classifier is one function whose branches are ordered `verifier` -> `mixed` -> `human_prose` ->
    `coding`. The realistic regression is a branch order change or a suffix/hint list edit, which
    moves SEVERAL rows at once: four separate tests report that as four unrelated `'coding' !=
    'human_prose'` lines, while the table reports one failure whose grouping names the branch.

    Rows go well beyond the four cases they replace, because the classifier's real decisions live in
    the hint lists and the branch order, which no single-path-per-class test can reach. Specifically:
    the ROUTING FIELD is a column (`writes` versus `generates` versus `shared_surfaces`), because
    `verifier` is decided by `writes`/`generates` ALONE while the prose/coding split reads
    `shared_surfaces` too, and that asymmetry is exactly the kind of thing a refactor flattens. Two
    rows also pin the UNINTUITIVE answers measured from real behavior: a bare filename with no
    directory is `coding`, and `docs/README.md` is `coding` while `website/guide.md` is
    `human_prose`, because `.md` counts as coding UNLESS a prose hint matches the directory.

    Every row is a positive claim about some class, so there is no vacuity risk in the usual sense;
    the anti-vacuity property here is that a classifier collapsing to ONE constant fails every row
    except the ones expecting that constant, which the failure count states directly.
    """

    #: (case, the field the paths arrive on, the paths, the expected work class, why this row exists)
    CLASSES = (
        (
            "a python source write",
            "writes",
            ("agent_workflows/x.py",),
            EX.WORK_CLASS_CODING,
            "THE BASE CASE for `coding`: a code suffix under a code directory is the overwhelmingly "
            "common lane, and it routes to the coding model",
        ),
        (
            "an .mdx write under website/",
            "writes",
            ("website/index.mdx",),
            EX.WORK_CLASS_HUMAN_PROSE,
            "THE BASE CASE for `human_prose`: this surface is read by HUMANS, so it routes to a "
            "prose model and (per the no-dash convention) is held to the user-facing prose rules. "
            "Routing it to a coding model is how machine-sounding marketing copy ships",
        ),
        (
            "a .md write under website/",
            "writes",
            ("website/guide.md",),
            EX.WORK_CLASS_HUMAN_PROSE,
            "THE DIRECTORY HINT BEATS THE SUFFIX, which is the classifier's subtler half: `.md` is "
            "treated as coding by default (see the `docs/README.md` row), so this row is what proves "
            "a prose HINT on the directory overrides that. Without it the hint list could be "
            "narrowed to `.mdx` alone and only this case would notice",
        ),
        (
            "a .md write under docs/",
            "writes",
            ("docs/README.md",),
            EX.WORK_CLASS_CODING,
            "THE COUNTER-ROW to the one above, and an UNINTUITIVE answer pinned deliberately: "
            "ordinary in-repo markdown is `coding`, because it is developer documentation living "
            "beside the code. Only the prose HINT directories (`website/`, `marketing/`, `policy/`, "
            "`blog/`, ...) flip it. Adjacent rows are the only way to state that boundary",
        ),
        (
            "a bare filename with no directory",
            "writes",
            ("Makefile",),
            EX.WORK_CLASS_CODING,
            "A REPO-ROOT FILE IS `coding`, via the explicit `'/' not in path` branch rather than by "
            "accident: a root-level `Makefile` or `Dockerfile` has no recognised suffix, and without "
            "that branch it would fall through. This row is what keeps the branch honest",
        ),
        (
            "a python write AND an .mdx write",
            "writes",
            ("agent_workflows/x.py", "website/a.mdx"),
            EX.WORK_CLASS_MIXED,
            "THE GENUINE BLEND, which the scheduler splits into a technical-fact lane then a prose "
            "lane. It must NOT collapse to either side: routed as `coding` the prose is written by a "
            "code model, and routed as `human_prose` the code is written by a prose model",
        ),
        (
            "a python write with a prose SHARED SURFACE",
            "shared_surfaces",
            ("website/a.mdx",),
            EX.WORK_CLASS_MIXED,
            "SHARED SURFACES COUNT AS TOUCHED, so a lane writing code that shares a prose surface is "
            "`mixed` even though its `writes` are pure code. The field is a COLUMN precisely so this "
            "case sits beside the `verifier` row below, which proves the SAME field does NOT count "
            "for the verifier decision",
        ),
        (
            "no writes and no generates",
            "writes",
            (),
            EX.WORK_CLASS_VERIFIER,
            "THE READ-ONLY LANE, and the FIRST branch: a node that touches nothing is a validation "
            "lane. It is checked before the path logic, so an empty path set can never fall through "
            "to `coding`",
        ),
        (
            "no writes, no generates, but a prose SHARED SURFACE",
            "shared_surfaces",
            (),
            EX.WORK_CLASS_VERIFIER,
            "THE ASYMMETRY ROW, and the reason the field is a column at all: `verifier` is decided "
            "by `writes`/`generates` ALONE, so a shared surface does NOT make a read-only lane a "
            "prose lane, even though the row above shows a shared surface DOES influence the "
            "prose/coding split. A refactor that folded `shared_surfaces` into the emptiness test "
            "would break this row and nothing else",
        ),
        (
            "generates (not writes) a python file",
            "generates",
            ("build/out.py",),
            EX.WORK_CLASS_CODING,
            "GENERATED OUTPUT IS STILL OUTPUT: a node that only `generates` is not a verifier, and "
            "its paths classify by the same rules. Without this row the emptiness test could read "
            "`writes` alone and every generate-only lane would be routed to the verifier model",
        ),
        (
            "generates (not writes) an .mdx file",
            "generates",
            ("website/a.mdx",),
            EX.WORK_CLASS_HUMAN_PROSE,
            "the prose half of the row above, kept so the `generates` field is shown to reach the "
            "FULL path logic and not just the emptiness test",
        ),
        (
            "a write under policy/",
            "writes",
            ("policy/terms.txt",),
            EX.WORK_CLASS_HUMAN_PROSE,
            "a NON-markdown, NON-mdx prose surface: `.txt` matches no suffix list at all, so this "
            "row can only pass via the directory hint. It also documents that the prose hints are "
            "about AUDIENCE (policy text is read by humans and lawyers) and not about file type",
        ),
    )

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

    def test_every_touched_path_set_lands_in_its_work_class(self):
        wrong = []
        by_expected = {}
        for case, field, paths, expected, why in self.CLASSES:
            kw = {field: paths}
            if field == "shared_surfaces":
                # The two shared-surface rows differ in whether there is any write at all, which is
                # the verifier boundary; `writes` carries that distinction.
                kw["writes"] = ("agent_workflows/x.py",) if paths else ()
            actual = EX.classify_node_work(self._node(**kw))
            by_expected.setdefault(expected, []).append(actual)
            if actual != expected:
                wrong.append(
                    f"  {case} ({field}={paths!r}):\n"
                    f"    - expected {expected!r}, got {actual!r}\n"
                    f"    this row exists because: {why}"
                )
        collapsed = ""
        seen = {a for actuals in by_expected.values() for a in actuals}
        if len(seen) == 1 and len(by_expected) > 1:
            note = seen.pop()
            collapsed = (
                f" NOTE: EVERY row returned {note!r}, so the classifier has collapsed to a single "
                "constant. Every lane would then resolve the same model binding, and a Set of mixed "
                "work would be written entirely by one model."
            )
        self.assertEqual(
            wrong,
            [],
            f"`classify_node_work` was wrong for {len(wrong)} of {len(self.CLASSES)} path sets."
            f"{collapsed} The four classes are a CLOSED SET and one branch-ordered function decides "
            "them (`verifier` first, then `mixed`, then `human_prose`, then `coding`), so read the "
            "grouping rather than the rows: every PROSE row going `coding` means a hint or suffix "
            "list was narrowed; the two SHARED-SURFACE rows disagreeing means the emptiness test and "
            "the path test no longer read the same fields; a `mixed` row collapsing to one side "
            "means the blend branch was reordered below one of the pure branches. FIX: the class is "
            "what `build_lanes` resolves a MODEL BINDING from, so a misclassification silently "
            "routes work to the wrong model (prose written by a code model, or code written by a "
            f"prose model) instead of erroring.\n" + "\n".join(wrong),
        )


class RoutingV01(unittest.TestCase):
    """Model-role routing, whose three surviving tests make structurally different claims."""

    def test_missing_binding_fails_closed(self):
        """Kept separate: an assertRaises. The claim is that resolution RAISES, not what it returns."""
        cfg = EX.routing_config_from_mapping({"coding": {"host": "h", "model": "m"}})
        with self.assertRaises(EX.BindingError):
            cfg.resolve("verifier")

    def test_build_lanes_fail_closed_on_missing(self):
        """Kept separate: an assertRaises, and at a different layer than the one above.

        `cfg.resolve` raising is necessary but not sufficient: `build_lanes` must PROPAGATE it rather
        than leaving the lane unbound, so a Set with a verifier node and no verifier binding refuses
        to start instead of launching a lane with no model.
        """
        m = _approved_manifest(
            ownership={"aaaaaa:E-01": {"writes": ["x.py"], "confidence": "declared"}}
        )
        cfg = EX.routing_config_from_mapping({"coding": {"host": "h", "model": "m"}})
        # verifier-class nodes (no writes) have no binding -> fail closed
        with self.assertRaises(EX.BindingError):
            EX.build_lanes(m, cfg)

    def test_every_lane_resolves_the_binding_for_its_own_class(self):
        """Kept separate: the claim is a PER-LANE CORRESPONDENCE, not one input-to-output mapping.

        Merged from `test_resolves_configured` and `test_build_lanes_routes_each_class`, which were
        the same claim at two layers: a configured binding comes back, and every built lane carries
        the binding belonging to ITS OWN class. Asserting the correspondence (model name derived from
        the lane's class) is what catches a router that resolves one binding and reuses it for every
        lane, which a fixed expected value cannot see.
        """
        cfg = EX.routing_config_from_mapping(
            {wc: {"host": "opencode", "model": "m-" + wc} for wc in EX.ALL_WORK_CLASSES}
        )
        b = cfg.resolve(EX.WORK_CLASS_CODING)
        self.assertEqual((b.host, b.model), ("opencode", "m-" + EX.WORK_CLASS_CODING))

        own = {
            n: {"writes": ["agent_workflows/x.py"], "confidence": "declared"}
            for n in ALL_NODES
        }
        lanes = EX.build_lanes(_approved_manifest(ownership=own), cfg)
        self.assertEqual(len(lanes), len(ALL_NODES))
        for ln in lanes:
            self.assertIsNotNone(ln.model_binding)
            self.assertEqual(ln.model_binding.model, "m-" + ln.work_class)


class SchedulerV01(unittest.TestCase):
    """The ready frontier, the per-node disposition, and the wave, on one shared manifest."""

    def setUp(self):
        own = {
            n: {
                "writes": [f"agent_workflows/{n.replace(':', '_')}.py"],
                "confidence": "declared",
            }
            for n in ALL_NODES
        }
        self.m = _approved_manifest(ownership=own)
        self.cfg = EX.routing_config_from_mapping(
            {wc: {"host": "h", "model": "m"} for wc in EX.ALL_WORK_CLASSES}
        )
        self.lanes = EX.build_lanes(self.m, self.cfg)

    #: (case, the nodes already completed, node ids that MUST be in the frontier, node ids that must
    #: NOT be, why this row exists)
    FRONTIERS = (
        (
            "nothing completed yet",
            (),
            ("aaaaaa:E-01",),
            ("bbbbbb:E-01",),
            "THE INITIAL FRONTIER. Child a has no cross-IPD dependency so its first node is ready, "
            "while child b's first node depends on a's TERMINAL node and must not be. Both halves "
            "matter: a frontier that admitted everything would satisfy the must-be-present half on "
            "its own, and it would run b before the work it depends on",
        ),
        (
            "all of child a completed",
            ("aaaaaa:E-01", "aaaaaa:E-02"),
            ("bbbbbb:E-01",),
            ("aaaaaa:E-01", "aaaaaa:E-02"),
            "THE FRONTIER ADVANCES, which is the property a single-state check cannot state: the "
            "same lane set yields a DIFFERENT frontier once the dependency is satisfied. The "
            "must-NOT half also pins that a completed node leaves the frontier, so a scheduler "
            "cannot re-dispatch work it already ran",
        ),
        (
            "only the FIRST of child a completed",
            ("aaaaaa:E-01",),
            ("aaaaaa:E-02",),
            ("bbbbbb:E-01",),
            "THE PARTIAL-DEPENDENCY ROW: b waits on a's terminal node, so completing HALF of a must "
            "not release b. Without this row the edge could be read as 'any of a' and the whole "
            "cross-IPD ordering would be one completed node deep",
        ),
    )

    def test_the_frontier_admits_exactly_the_dependency_satisfied_nodes(self):
        wrong = []
        for case, completed, must, must_not, why in self.FRONTIERS:
            ready = {ln.node_id for ln in EX.ready_lanes(self.lanes, list(completed))}
            problems = []
            absent = [n for n in must if n not in ready]
            if absent:
                problems.append(
                    f"{absent!r} should be READY here and is not; the frontier was {sorted(ready)!r}"
                )
            leaked = [n for n in must_not if n in ready]
            if leaked:
                problems.append(
                    f"{leaked!r} must NOT be ready here and is; the frontier was {sorted(ready)!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (completed={list(completed)!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`ready_lanes` was wrong for {len(wrong)} of {len(self.FRONTIERS)} completion states. "
            "One predicate (`all(dep in done)`) decides every row over the SAME lane set, so read "
            "the grouping: every row leaking `bbbbbb:E-01` means the cross-IPD edge is not being "
            "read at all and child b can run before child a; every row missing its expected node "
            "means the frontier is over-restrictive and the Set would stall with work available. "
            "FIX: the leak direction is the dangerous one, because a lane dispatched before its "
            "dependency produces evidence against a tree state that never existed, and the "
            f"merge-and-revalidate gate cannot detect ordering after the fact.\n"
            + "\n".join(wrong),
        )

    def test_every_node_gets_a_disposition(self):
        """Kept separate: the claim is TOTALITY over the lane set, not a per-input mapping.

        `disposition_pass` must leave NO node unaccounted for (that is its whole contract: a node is
        never silently ignored), and every disposition must be one of the four recorded words. A
        table row asserting one node's disposition cannot state totality, and the four words are
        literals here because they are what the run ledger records and a human reads.
        """
        disp = EX.disposition_pass(self.lanes, [])
        self.assertEqual({d.node_id for d in disp}, {ln.node_id for ln in self.lanes})
        for d in disp:
            self.assertIn(d.status, ("running", "deferred", "serialized", "blocked"))

    def test_wave_uses_analyzer(self):
        """Kept separate: asserts the wave DELEGATES, which is a claim about provenance.

        The coordinator must never override the eligibility analyzer toward more concurrency, so the
        only assertable property here is that the mode came from the analyzer's closed set. A row
        pinning one specific mode would pin the ANALYZER's current decision, which is not this
        function's contract.
        """
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
    """The write-ahead decision handshake; all three claims are structurally different."""

    def test_mutation_rejected_without_authorization(self):
        """Kept separate: an assertRaises, and the fail-closed half of the handshake."""
        led = EX.AuthorizationLedger(records=())
        with self.assertRaises(EX.HandshakeError):
            EX.authorize_mutation(led, lane_id="a:E-01", decision_id="D1")

    def test_mutation_allowed_after_recorded_authorization(self):
        """Kept separate: the assertion is the ABSENCE of a raise, which has no return value to
        tabulate against the row above."""
        rec = EX.make_authorization_record(
            run_id="run-x", decision_id="D1", selected_option="x"
        )
        led = EX.AuthorizationLedger(records=(rec,))
        EX.authorize_mutation(led, lane_id="a:E-01", decision_id="D1")  # no raise

    def test_proposal_pending_until_disposed(self):
        """Kept separate: a before/after pair over an APPENDED ledger, not one mapping.

        The content is that the same question id is pending with only its `question_raised` record
        and stops being pending once a disposition is appended, so both states must be computed from
        two ledgers built from the same first record.
        """
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
    """Isolation primitives. Every one has materially different setup or an assertRaises."""

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
        """Kept separate: drives REAL git against a real repository on disk, and the claim is a
        create/teardown LIFECYCLE (git knows about it, then the directory is gone)."""
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
        """Kept separate: an assertRaises plus a claim/release/re-claim SEQUENCE over one mutable
        lease table, which is exactly the state a table row cannot carry."""
        lt = WL.LeaseTable()
        lt.claim("laneA", ["x.py", "y.py"])
        with self.assertRaises(WL.LeaseConflictError):
            lt.claim("laneB", ["y.py"])
        lt.release("laneA")
        lt.claim("laneB", ["y.py"])  # now free
        self.assertEqual(lt.owner_of("y.py"), "laneB")

    def test_worker_path_fence(self):
        """Kept separate: an assertRaises, paired with its no-raise counter-case."""
        with self.assertRaises(WL.LeaseConflictError):
            WL.assert_worker_scope("laneC", [".aw/records/plans/x.ipd.md"])
        # a normal source path is fine
        WL.assert_worker_scope("laneC", ["agent_workflows/x.py"])

    def test_session_is_per_lane(self):
        """Kept separate: the claim is a RELATIONSHIP between two calls (their ids differ), not what
        either returns; pinning either id would pin the id scheme instead of the property."""
        s1 = WL.allocate_session("a:E-01", "run-x")
        s2 = WL.allocate_session("a:E-02", "run-x")
        self.assertNotEqual(s1.session_id, s2.session_id)


class IntegrationGateV02(unittest.TestCase):
    """What the merge-and-revalidate gate does with a set of lane outcomes.

    ONE table replaces three tests. Each built one lane outcome, ran the gate, and asserted
    `passed` (and sometimes `revalidation_passed`), differing only in whether the lane's own
    validation passed and what the full-validation runner returned.

    Why the table beats the three: the gate returns a TYPED STATUS from a closed set
    (`ISO.INTEGRATION_FAILED_*` plus `INTEGRATED_PASSED`), and the old tests asserted only the
    BOOLEAN, which cannot tell a conflict from a stale base from a combined-red. Every row here names
    the exact status, so a gate that starts refusing for the WRONG REASON fails rather than passing
    silently: that matters because the status is what tells an operator which remedy to apply, and
    "it refused" is not actionable.

    THE REFUSAL REASONS ARE COLUMNS, NOT CLASSES, and the extra rows are the point of tabulating.
    Rows now cover the four refusals the old file's docstring CLAIMED to cover but never asserted
    (conflict, overlap, scope, stale base) plus a timed-out lane and a missing lane. Each is
    reachable only by varying one field of the outcome set, so they were cheap once the shape was a
    table and invisible while it was three hand-written tests.

    THE CLEAN ROWS ARE IN THE SAME TABLE, and they are load-bearing: a gate that refused everything
    would satisfy every refusing row on its own. Two clean rows exist because "passes" has two
    distinct shapes worth pinning, one lane and two DISJOINT lanes, and the second is what shows
    parallel lanes are allowed at all rather than serialized by the gate.
    """

    #: (case, lane specs as (lane_id, changed files, per-lane pass, status override, diff override),
    #: the merge order, the declared scope or None, what the full-validation runner returns, the
    #: expected typed status, whether `passed` must be True, why this row exists)
    GATES = (
        (
            "one lane, everything green",
            ((("laneA", ("x.py",), True, None, None)),),
            ("laneA",),
            None,
            True,
            ISO.INTEGRATED_PASSED,
            True,
            "THE POSITIVE ROW. Every refusing row below is vacuous while this one is broken, because "
            "a gate that rejects everything satisfies all of them, and a gate that rejects "
            "everything also makes every Set unable to finish",
        ),
        (
            "two lanes touching DISJOINT files",
            (
                ("laneA", ("x.py",), True, None, None),
                ("laneB", ("y.py",), True, None, None),
            ),
            ("laneA", "laneB"),
            None,
            True,
            ISO.INTEGRATED_PASSED,
            True,
            "THE SECOND POSITIVE ROW, and it is what makes the overlap row below meaningful: "
            "PARALLEL lanes must be allowed to merge when their file sets do not intersect. Without "
            "it the collision rule could be 'more than one lane is a conflict' and the overlap row "
            "would still pass",
        ),
        (
            "one lane green locally, combined validation RED",
            ((("laneA", ("x.py",), True, None, None)),),
            ("laneA",),
            None,
            False,
            ISO.INTEGRATION_FAILED_COMBINED_RED,
            False,
            "PER-LANE GREEN IS NOT ENOUGH, which is the entire reason a merge-and-revalidate gate "
            "exists: each lane validated its own worktree in isolation, so only the combined HEAD "
            "can show interactions. A gate that trusted per-lane results would ship a broken merge "
            "with every lane reporting success",
        ),
        (
            "a lane whose OWN validation failed",
            ((("laneA", ("x.py",), False, None, None)),),
            ("laneA",),
            None,
            True,
            ISO.INTEGRATION_FAILED_LANE_FAILURE,
            False,
            "the gate must refuse BEFORE revalidating, so a red lane is never merged in the hope "
            "that the suite passes anyway. The status distinguishes this from combined-red, and the "
            "distinction is the remedy: fix the lane versus fix the interaction",
        ),
        (
            "a lane that TIMED OUT",
            ((("laneA", ("x.py",), True, ISO.STATUS_TIMED_OUT, None)),),
            ("laneA",),
            None,
            True,
            ISO.INTEGRATION_FAILED_LANE_FAILURE,
            False,
            "A TIMEOUT IS STRICTLY A FAILURE, even with `per_lane_validation_passed` TRUE, which is "
            "the trap this row exists for: a timed-out lane's local result is meaningless because it "
            "never finished. It shares the lane-failure status with the row above deliberately, and "
            "the two rows together prove a truthy local pass cannot rescue it",
        ),
        (
            "two lanes modifying the SAME file",
            (
                ("laneA", ("x.py",), True, None, None),
                ("laneB", ("x.py",), True, None, None),
            ),
            ("laneA", "laneB"),
            None,
            True,
            ISO.INTEGRATION_FAILED_CONFLICT,
            False,
            "OWNERSHIP COLLISION: the per-path lease is supposed to prevent this before execution, "
            "so reaching the gate means the lease was bypassed. The gate is the backstop, and it "
            "must refuse rather than merge one lane's version over another's silently",
        ),
        (
            "a lane whose diff carries CONFLICT MARKERS",
            (
                (
                    "laneA",
                    ("x.py",),
                    True,
                    None,
                    "<<<<<<< HEAD\nfoo\n=======\nbar\n>>>>>>> other\n",
                ),
            ),
            ("laneA",),
            None,
            True,
            ISO.INTEGRATION_FAILED_CONFLICT,
            False,
            "TEXTUAL CONFLICT MARKERS in a lane's diff mean an unresolved merge is being handed "
            "over as work product. Committing it would leave `<<<<<<<` in a source file, which no "
            "later gate reliably catches",
        ),
        (
            "a lane writing OUTSIDE the declared scope",
            ((("laneA", ("x.py", "outside/y.py"), True, None, None)),),
            ("laneA",),
            ("x.py",),
            True,
            ISO.INTEGRATION_FAILED_SCOPE_VIOLATION,
            False,
            "THE SCOPE GATE, and the only row where `declared_scope` is not None, which is why the "
            "column exists: a lane must not smuggle in changes its plan never declared. This is the "
            "mechanism behind the Scope-Paths reconciliation a run reports at the end",
        ),
        (
            "a lane based on the WRONG commit",
            ((("laneA", ("x.py",), True, None, None)),),
            ("laneA",),
            None,
            True,
            ISO.INTEGRATION_FAILED_STALE_BASE,
            False,
            "STALE BASE: the first lane's base must equal the integration base, or the lane's "
            "validation ran against a tree that no longer exists. This row is built by declaring a "
            "different integration base, so it needs no second fixture shape",
        ),
        (
            "a merge order naming a lane with no outcome",
            ((("laneA", ("x.py",), True, None, None)),),
            ("laneA", "laneB"),
            None,
            True,
            ISO.INTEGRATION_FAILED_MISSING_LANE,
            False,
            "FAIL CLOSED ON AN ABSENT LANE: a lane in the merge order with no outcome means the run "
            "lost track of work, so the gate must refuse rather than integrate the lanes it happens "
            "to have. Silently merging the subset is how a Set reports success having executed part "
            "of itself",
        ),
    )

    def _lane_outcome(self, lane_id, files, ok, status, diff, base="BASE"):
        kw = dict(
            lane_id=lane_id,
            actor_role="coding",
            base_commit=base,
            head_commit="H1",
            worktree_path=f".aw/worktrees/{lane_id}",
            changed_files=tuple(files),
            diff=(
                diff
                if diff is not None
                else ("diff --git a/{0} b/{0}\n".format(files[0]) if files else "")
            ),
            per_lane_validation_passed=ok,
        )
        if status is not None:
            kw["status"] = status
        return ISO.LaneOutcome(**kw)

    def test_every_lane_outcome_set_gets_its_own_typed_verdict(self):
        wrong = []
        clean_row_broken = False
        for (
            case,
            lane_specs,
            order,
            scope,
            reval,
            expected_status,
            expected_passed,
            why,
        ) in self.GATES:
            stale = expected_status == ISO.INTEGRATION_FAILED_STALE_BASE
            outs = [
                self._lane_outcome(*spec, base=("OTHER" if stale else "BASE"))
                for spec in lane_specs
            ]
            res = ISO.execute_merge_and_revalidate_gate(
                "BASE",
                outs,
                list(order),
                full_validation_runner=lambda diff, files, _r=reval: _r,
                declared_scope=(list(scope) if scope is not None else None),
            )
            problems = []
            if res.status != expected_status:
                problems.append(
                    f"expected status {expected_status!r}, got {res.status!r}. The status is what "
                    "tells an operator WHICH remedy applies, so a refusal for the wrong reason is "
                    "not merely cosmetic"
                )
            if res.passed is not expected_passed:
                problems.append(
                    f"expected passed={expected_passed}, got {res.passed} (message: "
                    f"{res.message!r})"
                )
            if expected_passed:
                if not res.revalidation_passed:
                    problems.append(
                        "a passing gate must record `revalidation_passed`; the combined HEAD result "
                        "is the evidence the whole gate exists to produce"
                    )
                if res.findings:
                    problems.append(
                        f"a passing gate must report no findings; it reported "
                        f"{[(f.check_name, f.lane_id) for f in res.findings]!r}"
                    )
            else:
                if res.revalidation_passed:
                    problems.append(
                        "a REFUSING gate must not claim `revalidation_passed`, or a caller reading "
                        "that field alone would treat the combined HEAD as validated"
                    )
                if not res.findings:
                    problems.append(
                        "a refusing gate must report at least one finding naming the check that "
                        "refused; it reported none, so the refusal is unexplainable to a human"
                    )
            if problems:
                if expected_passed and problems:
                    clean_row_broken = True
                wrong.append(
                    f"  {case} (lanes={[s[0] for s in lane_specs]!r}, order={list(order)!r}, "
                    f"scope={scope!r}, revalidation={reval}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if clean_row_broken:
            note = (
                " NOTE: a PASSING row is among the failures, so the gate is now refusing work it "
                "must accept. That makes every refusing row vacuous and means no Set can reach a "
                "terminal transition at all."
            )
        self.assertEqual(
            wrong,
            [],
            f"the integration gate was wrong for {len(wrong)} of {len(self.GATES)} outcome sets."
            f"{note} The gate is an ORDERED sequence of checks (lane presence, lane status, stale "
            "base, conflict/collision, scope, then full revalidation) each returning its own typed "
            "status, so read the grouping: several rows returning the SAME wrong status means an "
            "earlier check now short-circuits later ones (reordering, not N broken checks); a row "
            "returning `integrated_passed` where a refusal was expected means that check was "
            "dropped entirely. FIX: a dropped check is the dangerous direction, because the gate is "
            "the ONLY place a lane's isolated work is reconciled against the combined tree, and "
            f"nothing downstream re-derives it.\n" + "\n".join(wrong),
        )


# ==================================================================================================
# V-03: lifecycle + recovery
# ==================================================================================================


class TerminalGateV03(unittest.TestCase):
    """Which precondition combinations permit a Set's terminal transition.

    ONE table replaces three tests. Each called `terminal_transition_allowed` with four keyword
    booleans and asserted `allowed`, differing only in which precondition was falsified.

    Why the table beats the three: the gate is a conjunction of FOUR named preconditions evaluated in
    a fixed order, each with its own refusal REASON, and the old tests asserted the boolean only. A
    boolean cannot tell WHICH precondition refused, so a gate whose checks got reordered or whose
    reason text stopped naming the cause passed unchanged. Every row here pins a substring of the
    reason, which is what an operator reads to know what to fix.

    Each precondition gets its own row with the OTHERS SATISFIED, so a row isolates one conjunct.
    That is the property the three old tests only partly had: they left `all_required_verified_terminal`
    False alongside the unresolved-nodes case, so the two conjuncts could not be distinguished.

    THE PERMITTING ROW IS IN THE SAME TABLE and it is not decoration: a gate that refused
    unconditionally would satisfy all four refusing rows, and it would also make every Set
    permanently unfinishable, which is a worse failure than the one the gate prevents.
    """

    #: (case, integration_passed, combined_head_revalidated, unresolved nodes,
    #: all_required_verified_terminal, expected allowed, substrings required in the reason, why this
    #: row exists)
    GATES = (
        (
            "every precondition satisfied",
            True,
            True,
            (),
            True,
            True,
            ("all terminal preconditions satisfied",),
            "THE POSITIVE ROW. Every refusing row is vacuous while this is broken, and a gate that "
            "refuses unconditionally leaves every Set permanently unfinishable, which is worse than "
            "the failure the gate prevents",
        ),
        (
            "integration itself did not pass",
            False,
            True,
            (),
            True,
            False,
            ("integration did not pass",),
            "THE FIRST CONJUNCT, and the one the old tests never covered: if the merge-and-"
            "revalidate gate refused, nothing downstream may proceed. It is checked FIRST because "
            "the later preconditions are meaningless when no integration happened",
        ),
        (
            "integration passed but the combined HEAD failed revalidation",
            True,
            False,
            (),
            True,
            False,
            ("combined HEAD failed revalidation", "per-lane green is not enough"),
            "THE PER-LANE-GREEN-BUT-COMBINED-RED REFUSAL, restated at the Set level: the reason text "
            "must SAY that per-lane green is not enough, because an operator seeing every lane green "
            "will otherwise read the refusal as a tooling fault and look for a way around it",
        ),
        (
            "a required node is still unresolved",
            True,
            True,
            ("a:E-03",),
            True,
            False,
            ("unresolved required nodes remain", "a:E-03"),
            "THE CONJUNCT ISOLATED, which the old test could not do: it passed "
            "`all_required_verified_terminal=False` at the same time, so either check could have "
            "produced the refusal. Here everything else is satisfied, and the reason must NAME the "
            "offending node or the operator cannot tell which work is outstanding",
        ),
        (
            "no unresolved node, but a required child is not verified terminal",
            True,
            True,
            (),
            False,
            False,
            ("not every required child reached verified terminal",),
            "THE FOURTH CONJUNCT, isolated for the same reason. It is genuinely distinct from the "
            "row above: a node can be resolved (dispatched and finished) without its child plan "
            "having reached a verified terminal lifecycle state, and only that state means the work "
            "was validated",
        ),
    )

    def test_each_precondition_refuses_on_its_own_and_says_why(self):
        wrong = []
        positive_row_broken = False
        for (
            case,
            integration,
            revalidated,
            unresolved,
            verified,
            expected,
            needles,
            why,
        ) in self.GATES:
            r = LC.terminal_transition_allowed(
                integration_passed=integration,
                combined_head_revalidated=revalidated,
                unresolved_required_nodes=list(unresolved),
                all_required_verified_terminal=verified,
            )
            problems = []
            if r.allowed is not expected:
                if expected:
                    positive_row_broken = True
                problems.append(
                    f"expected allowed={expected}, got {r.allowed} (reason: {r.reason!r})"
                )
            missing = [n for n in needles if n not in r.reason]
            if missing:
                problems.append(
                    f"the reason never mentions {missing!r}, so a human cannot tell what refused; "
                    f"it said {r.reason!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (integration={integration}, revalidated={revalidated}, "
                    f"unresolved={list(unresolved)!r}, verified={verified}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if positive_row_broken:
            note = (
                " NOTE: the PERMITTING row is among the failures, so the gate now refuses a Set "
                "that satisfied every precondition. That makes all four refusing rows vacuous and "
                "leaves every Set unfinishable."
            )
        self.assertEqual(
            wrong,
            [],
            f"the terminal gate was wrong for {len(wrong)} of {len(self.GATES)} precondition "
            f"combinations.{note} It is a conjunction of four ORDERED checks, each row falsifying "
            "exactly one, so read the grouping: several rows returning the SAME reason means an "
            "earlier check now swallows later ones; a refusing row returning allowed=True means "
            "that conjunct was dropped and a Set can now transition over it. FIX: the gate is what "
            "stops a Set reaching a terminal state while claiming success nobody demonstrated, so a "
            f"dropped conjunct is a validation requirement that silently stopped existing.\n"
            + "\n".join(wrong),
        )


class SetProgressV03(unittest.TestCase):
    """Which Set state the coordinator derives from lane progress.

    ONE table replaces two tests (`test_deferred_required_keeps_set_partial` and
    `test_all_verified_is_complete`), and extends them to every state the derivation can produce.
    Both old tests called `derive_progress` and asserted one `set_state`, differing only in the
    deferred/verified split, so a (progress -> state) table is the natural shape.

    Why the table beats the two: the `set_*` states are a CLOSED SET with declared transition rules,
    ACTIVE and TERMINAL subsets, and consumers that route on them, and the realistic regression is a
    precedence change in the derivation (does `cancelled` beat `unrecoverable`? does
    `waiting_on_human` beat an otherwise complete Set?). Two tests covering the two happiest states
    cannot see any of that. The five added rows are the states a partial derivation would silently
    collapse into `set_running`, which is the value that looks harmless in a status view.

    THE STATE NAMES ARE LITERAL STRINGS, deliberately: they are what the run ledger records and what
    `aw runs` prints, so a rename is a breaking change and must fail here rather than track the
    constants.

    The UNRESOLVED and DEFERRED tuples are asserted beside the state because they are what a human
    acts on: a Set that is `set_partial` without naming the deferred node tells nobody what to
    revisit.
    """

    #: (case, required nodes, verified-terminal nodes, deferred nodes, waiting_on_human,
    #: unrecoverable, started, cancelled, expected state, expected unresolved, expected deferred,
    #: why this row exists)
    PROGRESS = (
        (
            "every required node verified terminal",
            ("a:E-01",),
            ("a:E-01",),
            (),
            False,
            False,
            True,
            False,
            "set_complete",
            (),
            (),
            "THE ONLY STATE THAT MAY CLAIM SUCCESS, so it must be reachable ONLY here: every "
            "required node verified terminal, nothing deferred, nothing waiting. A derivation that "
            "reached `set_complete` too easily is a Set reporting done over unfinished work",
        ),
        (
            "one required node verified, the other DEFERRED",
            ("a:E-01", "a:E-02"),
            ("a:E-01",),
            ("a:E-02",),
            False,
            False,
            True,
            False,
            "set_partial",
            (),
            ("a:E-02",),
            "A DEFERRAL IS RESOLVED, NOT OUTSTANDING (so `unresolved` is EMPTY), yet the Set is "
            "`set_partial` and NOT `set_complete`. That pair of facts is the whole distinction: the "
            "deferred node must still be NAMED in `deferred`, or the Set says it is partial without "
            "saying what was left",
        ),
        (
            "nothing verified and nothing deferred yet",
            ("a:E-01",),
            (),
            (),
            False,
            False,
            True,
            False,
            "set_running",
            ("a:E-01",),
            (),
            "THE ORDINARY IN-FLIGHT STATE, and the value every other row must be distinguishable "
            "FROM. It is the default a broken derivation collapses into, which is dangerous "
            "precisely because a running Set looks unremarkable in a status view",
        ),
        (
            "a question is waiting on a human",
            ("a:E-01",),
            (),
            (),
            True,
            False,
            True,
            False,
            "set_waiting_input",
            ("a:E-01",),
            (),
            "WAITING ON A HUMAN IS ITS OWN STATE, not a flavour of running, because it is the one "
            "state that will never advance on its own. Collapsed into `set_running` an unattended "
            "run appears to be making progress while it is blocked on an unanswered question",
        ),
        (
            "the run hit an unrecoverable fault",
            ("a:E-01",),
            (),
            (),
            False,
            True,
            True,
            False,
            "set_failed",
            ("a:E-01",),
            (),
            "TERMINAL AND UNSUCCESSFUL, which must be distinct from `set_cancelled` below: a failure "
            "needs investigation, a cancellation does not. Conflating them loses that difference in "
            "every later report",
        ),
        (
            "the Set was cancelled",
            ("a:E-01",),
            (),
            (),
            False,
            False,
            True,
            True,
            "set_cancelled",
            ("a:E-01",),
            (),
            "a deliberate stop is terminal but is NOT a fault. Keeping it beside `set_failed` is "
            "what states that the derivation distinguishes intent from breakage",
        ),
        (
            "the Set has not started",
            ("a:E-01",),
            (),
            (),
            False,
            False,
            False,
            False,
            "set_planned",
            ("a:E-01",),
            (),
            "THE PRE-RUN STATE: a compiled but unstarted Set has every required node unresolved and "
            "must NOT read as running, or a queue view shows work in flight that no lane has "
            "claimed",
        ),
    )

    def test_every_progress_shape_derives_its_own_set_state(self):
        wrong = []
        seen_states = []
        for (
            case,
            required,
            verified,
            deferred,
            waiting,
            unrecoverable,
            started,
            cancelled,
            expected_state,
            expected_unresolved,
            expected_deferred,
            why,
        ) in self.PROGRESS:
            p = LC.derive_progress(
                required_nodes=list(required),
                verified_terminal_nodes=list(verified),
                deferred_nodes=list(deferred),
                waiting_on_human=waiting,
                unrecoverable=unrecoverable,
                started=started,
                cancelled=cancelled,
            )
            seen_states.append(p.set_state)
            problems = []
            if p.set_state != expected_state:
                problems.append(
                    f"expected set_state {expected_state!r}, got {p.set_state!r}"
                )
            if p.unresolved_required != expected_unresolved:
                problems.append(
                    f"expected unresolved_required {expected_unresolved!r}, got "
                    f"{p.unresolved_required!r}; this tuple is what a human is told to go and finish"
                )
            if p.deferred != expected_deferred:
                problems.append(
                    f"expected deferred {expected_deferred!r}, got {p.deferred!r}; an unnamed "
                    "deferral is work nobody knows to revisit"
                )
            if problems:
                wrong.append(
                    f"  {case} (required={list(required)!r}, verified={list(verified)!r}, "
                    f"deferred={list(deferred)!r}, waiting={waiting}, unrecoverable="
                    f"{unrecoverable}, started={started}, cancelled={cancelled}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        collapsed = ""
        if len(set(seen_states)) == 1:
            collapsed = (
                f" NOTE: EVERY row derived {seen_states[0]!r}, so the derivation has collapsed to "
                "one state and every distinction the Set lifecycle makes is gone."
            )
        self.assertEqual(
            wrong,
            [],
            f"`derive_progress` was wrong for {len(wrong)} of {len(self.PROGRESS)} progress shapes."
            f"{collapsed} The seven `set_*` states are a CLOSED SET decided by one precedence "
            "ordering, so read the grouping: several rows all returning `set_running` means the "
            "flags feeding the decision stopped being consulted (that is the default they collapse "
            "into, and a running Set looks unremarkable in a status view); `set_complete` appearing "
            "where it should not is the worst single outcome, because a Set claiming completion is "
            "what permits the terminal transition. FIX: check the PRECEDENCE, not the individual "
            "branches, whenever `cancelled`/`unrecoverable`/`waiting_on_human` rows move "
            f"together.\n" + "\n".join(wrong),
        )


class LifecycleV03(unittest.TestCase):
    """The two lifecycle claims that are sequences rather than mappings."""

    def test_integration_triggered_evidence_invalidation(self):
        """Kept separate: a multi-step round trip, not one input-to-output mapping.

        It computes the stale seqs, builds invalidation records, validates one against the ledger
        SCHEMA, then re-computes staleness over the APPENDED ledger to show the seq is no longer
        stale. The property is that the emitted record actually closes the hole it describes, which
        needs all four steps in order.
        """
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

    def test_resume_fails_closed_on_unknown_outcome(self):
        """Kept separate: materially different setup (a real run engine over a ledger store on disk)
        and the assertion is the TYPE of a returned error object, not a value."""
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
