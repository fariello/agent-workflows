#!/usr/bin/env python3
"""rununify Order 08 (`ty3cj6`) E-02: CHARACTERIZE `run_queue` on BOTH hosts, as behavior.

WHY THIS FILE EXISTS, and why it asserts behavior rather than source text.

The parent Set forbids a child reconciling a symbol the characterization baseline has not pinned,
and `run_queue` is the dispatch loop both runners are built around. The ten existing pins that
reach it (see `tests/test_rununify_run_queue.py` for the inventory) all read its SOURCE TEXT
through `inspect.getsource`, an AST lookup by name, or a `split("def run_queue(")`. A source pin
has two problems this file is the answer to: a relocation destroys it even when behavior is
unchanged, and a COMMENT can satisfy it even when behavior is broken. So each test below drives
the host's real `run_queue` over a synthetic queue and asserts the OBSERVABLE result.

THE HARNESS follows the precedent of `tests/test_orchestrator_retirement.py::DispatchRunCase`:
`execute_item` is stubbed, which is not a shortcut around the thing under test but the
INSTRUMENT for it. What is under test is the LOOP: which items it selects, in what order, what
statuses it writes, when it stops, and what it publishes to the shutdown reporter. Stubbing the
turn is what makes those observable without spawning an agent.

AGY IS PRIORITIZED DELIBERATELY. The parent measured the two hosts' suites as asymmetric (95 oc
tests against 21 agy at the time), so an agy-side regression can hide behind a green suite. Every
test here runs against BOTH hosts through `subTest`, and the two branches plan `ty3cj6` F-9 names
as both uncovered and defective (the integration-ladder state reloads) get their own class.

WHAT THIS FILE DOES NOT CLAIM. It pins the loop's decisions, not the correctness of the work each
turn performs; that assurance lives in the host CLI suites and in `execute_item`'s own coverage.
It also does not drive a real signal, because a test that sends SIGINT to the test runner is not
safe under `-n auto`; the signal-report path is characterized through the state the handler would
publish, which is the property F-9 is actually about.
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from agent_workflows import agy_runipd, oc_runipd

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


class RunQueueCase(unittest.TestCase):
    """Drive a host's real `run_queue` over a synthetic queue, with the agent turn stubbed."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.turns: list[str] = []

    # ---- fixtures --------------------------------------------------------------------------
    def item(
        self,
        id6: str,
        *,
        setid: str = "synth",
        action: str = "execute",
        status: str = "queued",
        deps: tuple[str, ...] = (),
        position: int = 1,
        kind: str = "child",
        **extra,
    ) -> dict:
        entry = {
            "position": position,
            "id6": id6,
            "setid": setid,
            "action": action,
            "kind": kind,
            "status": status,
            "dependencies": list(deps),
            "attempts": [],
        }
        entry.update(extra)
        return entry

    def make_run(
        self, queue: list[dict], *, run_id: str = "run-char", options=None
    ) -> pathlib.Path:
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "repo": str(self.root),
            "created_at": "2026-09-17T00:00:00+00:00",
            "updated_at": "2026-09-17T00:00:00+00:00",
            "selectors": ["synthetic"],
            "options": dict(options or {}),
            "set_sessions": {},
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return run_dir

    # ---- driving ---------------------------------------------------------------------------
    def drive(
        self,
        module,
        run_dir: pathlib.Path,
        *,
        retry_incomplete: bool = False,
        on_turn=None,
        budget: int = 40,
        **kwargs,
    ):
        """Run the loop with `execute_item` stubbed. FAILS LOUDLY on a spin rather than hanging."""
        seen = {"n": 0}

        def fake_exec(rd, st, it, *a, **kw):
            seen["n"] += 1
            if seen["n"] > budget:
                raise AssertionError(
                    f"SPIN: {seen['n']} dispatches without the run terminating; the loop is not "
                    "converging on a terminal state for every item"
                )
            self.turns.append(str(it.get("id6")))
            if on_turn is not None:
                on_turn(it)
            else:
                it["status"] = "executed"
            module.save_state(rd, st)

        buf = io.StringIO()
        with patch.object(module, "execute_item", side_effect=fake_exec):
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc = module.run_queue(
                    run_dir, retry_incomplete=retry_incomplete, **kwargs
                )
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        return rc, state, buf.getvalue()

    # ---- reading ---------------------------------------------------------------------------
    def statuses(self, state: dict) -> dict[str, str]:
        return {it["id6"]: it["status"] for it in state["queue"]}

    def events(self, run_dir: pathlib.Path) -> list[dict]:
        path = run_dir / "events.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(ln)
            for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]

    # ---- the signal-report ledger -----------------------------------------------------------
    def published(self, module=None) -> dict | None:
        """Read the ledger `register_signal_report` writes.

        There is exactly ONE ledger: `_SIGNAL_REPORT_STATE` is defined in `oc_runipd` and agy
        reaches the SAME dict because it imports `register_signal_report` from oc
        (`agy_runipd.py:408`), so `oc.register_signal_report is agy.register_signal_report`. That is
        why this reads oc's module global for BOTH hosts rather than each host's own: agy has no
        `_SIGNAL_REPORT_STATE` attribute of its own, and asserting against a per-host copy would be
        asserting against something that does not exist.
        """
        del module  # one shared ledger; the parameter is kept for call-site symmetry
        return oc_runipd._SIGNAL_REPORT_STATE.get("state")

    def clear_published(self) -> None:
        """The ledger is a PROCESS global, so a prior test's run would otherwise leak into this one.

        This matters for correctness, not tidiness: without it, a staleness assertion could be
        satisfied by an EARLIER test's state object and the guard would not fail on broken code.
        """
        oc_runipd._SIGNAL_REPORT_STATE.clear()


class TheLoopDispatchesEveryRunnableItem(RunQueueCase):
    """The baseline behavior: an independent queue drains, on both hosts, in dependency order."""

    def test_an_independent_queue_drains_completely(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("aaa111", position=1),
                        self.item("bbb222", position=2),
                        self.item("ccc333", position=3),
                    ],
                    run_id=f"drain-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(rc, 0, f"{label}: a fully drained queue must exit 0")
                self.assertEqual(
                    self.statuses(state),
                    {"aaa111": "executed", "bbb222": "executed", "ccc333": "executed"},
                )
                self.assertEqual(sorted(self.turns), ["aaa111", "bbb222", "ccc333"])

    def test_a_dependency_is_dispatched_before_its_dependent(self):
        """Declared edges are authoritative; this is the property `queue_sort_key` exists for."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        # The DEPENDENT is listed first, so position order alone would get it wrong.
                        self.item("dep222", position=1, deps=("executed:pre111",)),
                        self.item("pre111", position=2),
                    ],
                    run_id=f"order-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(rc, 0)
                self.assertEqual(
                    self.statuses(state), {"pre111": "executed", "dep222": "executed"}
                )
                self.assertEqual(
                    self.turns,
                    ["pre111", "dep222"],
                    f"{label}: the dependency must be dispatched FIRST regardless of position",
                )


class AnUnsatisfiableDependencyBlocksRatherThanStalls(RunQueueCase):
    """The cascade, and the recovery hint attached to it. F-12: the hint DIFFERS per host."""

    def test_a_dependent_of_a_failed_item_is_marked_dependency_blocked(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("fail11", position=1),
                        self.item("dep222", position=2, deps=("executed:fail11",)),
                    ],
                    run_id=f"cascade-{label}",
                )

                def on_turn(item):
                    item["status"] = (
                        "failed-safely" if item["id6"] == "fail11" else "executed"
                    )

                rc, state, _ = self.drive(module, run_dir, on_turn=on_turn)
                statuses = self.statuses(state)
                self.assertEqual(statuses["fail11"], "failed-safely")
                self.assertEqual(
                    statuses["dep222"],
                    "dependency-blocked",
                    f"{label}: a dependent of a non-success terminal item must be blocked, "
                    "not left queued (which would stall the queue)",
                )
                self.assertEqual(
                    self.turns,
                    ["fail11"],
                    f"{label}: the blocked item must NOT spend an agent turn",
                )
                self.assertNotEqual(
                    rc, 0, f"{label}: a run leaving blocked work must not exit 0"
                )

    def test_the_blocked_item_carries_its_host_s_own_recovery_hint(self):
        """F-12: `DEPENDENCY_BLOCK_RECOVERY_HINT` is host-divergent BY DESIGN.

        A split that lifted this constant unchanged would print the wrong recovery command on one
        host, so the divergence is pinned here as behavior: the hint that lands in state must name
        THIS host's own resume verb.
        """
        expected = {
            "oc_runipd": "aw oc runipd resume",
            "agy_runipd": "aw agy runipd resume",
        }
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("dep222", position=1, deps=("executed:absent",))],
                    run_id=f"hint-{label}",
                )
                _, state, _ = self.drive(module, run_dir)
                entry = state["queue"][0]
                self.assertEqual(entry["status"], "dependency-blocked")
                self.assertIn(
                    expected[label],
                    entry["dependency_block_recovery"],
                    f"{label}: the recovery hint must name this host's OWN resume verb",
                )
                self.assertNotIn(
                    expected["agy_runipd" if label == "oc_runipd" else "oc_runipd"],
                    entry["dependency_block_recovery"],
                    f"{label}: the hint must not name the OTHER host's verb",
                )

    def test_an_unsatisfied_dependency_records_both_the_flat_list_and_the_reasons(self):
        """The additive companion key, whose shape existing consumers depend on."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("dep222", position=1, deps=("executed:absent",))],
                    run_id=f"reasons-{label}",
                )
                _, state, _ = self.drive(module, run_dir)
                entry = state["queue"][0]
                self.assertIsInstance(entry["unsatisfied_dependencies"], list)
                self.assertTrue(
                    all(isinstance(x, str) for x in entry["unsatisfied_dependencies"]),
                    f"{label}: the flat list must stay list[str] for existing consumers",
                )
                self.assertIn("unsatisfied_dependency_reasons", entry)


class TheRetryIncompleteFlagRequeuesTheStatesItDeclares(RunQueueCase):
    """`--retry-incomplete`'s status set, as behavior. F-3: oc requires the argument, agy defaults it."""

    REQUEUED = (
        "interrupted",
        "substantially-complete",
        "partial",
        "failed-safely",
        "blocked",
        "dependency-blocked",
        "integration-blocked",
        "merge-conflict",
        "integration-deferred",
    )

    def test_every_declared_non_terminal_state_is_requeued_and_dispatched(self):
        for label, module in HOSTS:
            for status in self.REQUEUED:
                with self.subTest(host=label, status=status):
                    self.turns.clear()
                    run_dir = self.make_run(
                        [self.item("rty111", position=1, status=status)],
                        run_id=f"retry-{label}-{status}",
                    )
                    rc, state, _ = self.drive(module, run_dir, retry_incomplete=True)
                    self.assertEqual(
                        self.statuses(state)["rty111"],
                        "executed",
                        f"{label}: --retry-incomplete must re-queue a {status!r} item",
                    )
                    self.assertEqual(self.turns, ["rty111"])
                    self.assertEqual(rc, 0)

    def test_a_requeued_item_is_dispatched_in_recovery_mode(self):
        """`recovery=True` is what tells the turn it is a retry rather than a first attempt.

        The flag reaches the turn as the KEYWORD, not as the item key: the loop `pop`s
        `recovery_next` off the item and passes `recovery=` (`oc_runipd.py:8870`). Asserting on the
        item key would therefore always see `None` and the test would be vacuous.
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("recovery"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("rty111", position=1, status="partial")],
                    run_id=f"recovery-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=True)
                self.assertEqual(
                    seen,
                    [True],
                    f"{label}: a re-queued item must be dispatched with recovery=True",
                )

    def test_a_first_attempt_is_not_dispatched_in_recovery_mode(self):
        """The inverse, so the assertion above cannot pass on a hardcoded True."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("recovery"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("fst111", position=1)], run_id=f"firstattempt-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(
                    seen,
                    [False],
                    f"{label}: a first attempt must not claim recovery mode",
                )

    def test_without_the_flag_an_incomplete_item_is_left_alone(self):
        """The inverse: the flag is the ONLY thing that re-queues these, so absence must be inert."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("rty111", position=1, status="partial")],
                    run_id=f"noretry-{label}",
                )
                _, state, _ = self.drive(module, run_dir, retry_incomplete=False)
                self.assertEqual(self.statuses(state)["rty111"], "partial")
                self.assertEqual(
                    self.turns,
                    [],
                    f"{label}: without the flag nothing may be re-dispatched",
                )

    def test_an_indeterminate_item_is_refused_even_under_the_flag(self):
        """runstop `m0z0ti` R19: a force-interrupted item's outcome was never established, so a
        broader retry flag is NOT permission to re-run it. This is the SECOND route into the requeue
        and it must agree with the first."""
        from agent_workflows import runner_stop

        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                item = self.item("ind111", position=1, status="interrupted")
                run_dir = self.make_run([item], run_id=f"indet-{label}")
                with patch.object(runner_stop, "is_indeterminate", return_value=True):
                    _, state, _ = self.drive(module, run_dir, retry_incomplete=True)
                self.assertEqual(
                    self.statuses(state)["ind111"],
                    "interrupted",
                    f"{label}: an indeterminate item must NOT be re-queued by --retry-incomplete",
                )
                self.assertEqual(self.turns, [])


class TheDisplayOptionsAreFrozenOnceAndTogether(RunQueueCase):
    """The `output_mode`/`verbosity` re-choice, and its ONE `save_state`.

    The shared persist is deliberate (`WrapperTests::test_no_call_site_was_rewritten` counts
    `save_state` sites per runner), so this pins the OBSERVABLE half: both land, and `None` means
    "operator did not pass the flag" and must leave a frozen value alone.
    """

    def test_both_display_options_are_persisted_when_supplied(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                run_dir = self.make_run([], run_id=f"display-{label}")
                self.drive(module, run_dir, output_mode="plain", verbosity=2)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(state["options"]["output_mode"], "plain")
                self.assertEqual(state["options"]["verbosity"], 2)

    def test_none_leaves_a_frozen_value_untouched(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                run_dir = self.make_run(
                    [],
                    run_id=f"frozen-{label}",
                    options={"output_mode": "json", "verbosity": 3},
                )
                self.drive(module, run_dir, output_mode=None, verbosity=None)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(state["options"]["output_mode"], "json")
                self.assertEqual(state["options"]["verbosity"], 3)

    def test_verbosity_is_coerced_to_int(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                run_dir = self.make_run([], run_id=f"coerce-{label}")
                self.drive(module, run_dir, verbosity=True)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertIsInstance(state["options"]["verbosity"], int)


class TheSignalReporterSeesPostReloadState(RunQueueCase):
    """F-9, THE DEFECT THIS PLAN REPAIRS, pinned as behavior on BOTH hosts.

    `run_queue` publishes its live `state` for the shutdown reporter through
    `register_signal_report`. `state` is REBOUND by every `load_state` inside the loop, so the
    published reference is stale until it is refreshed. `oc_runipd.py`'s own comment states the
    invariant: "`register_signal_report` is called again after each state reload so the report never
    runs off a stale snapshot".

    Measured at plan-execution HEAD, oc called it FIVE times inside the loop and agy THREE: agy
    omitted the refresh after BOTH integration-ladder reloads. So on `aw agy run`, a signal arriving
    there reported PRE-reload item states.

    THE TEST IS BEHAVIORAL, not a call count: it asserts that the object the reporter would read is
    the SAME object the loop is currently working with, at every point the loop reloads state. That
    property is what the call sites exist to produce, and it survives a relocation.
    """

    def test_the_published_state_is_the_live_object_at_the_end_of_the_run(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"pub-{label}"
                )
                _, state, _ = self.drive(module, run_dir)
                published = self.published(module)
                assert isinstance(published, dict), f"{label}: nothing was published"
                self.assertEqual(
                    {it["id6"]: it["status"] for it in published["queue"]},
                    {"aaa111": "executed"},
                    f"{label}: the reporter must see the FINAL statuses, not a pre-turn snapshot",
                )

    def test_the_published_state_is_refreshed_after_every_reload_in_the_loop(self):
        """The invariant, asserted at each reload rather than only at the end.

        `load_state` is wrapped so that immediately AFTER the loop takes a fresh state object, the
        published reference is compared. A refresh that the host omits shows up as the published
        object being a DIFFERENT dict from the one the loop just loaded, which is exactly the
        staleness F-9 describes. Only reloads that happen while a report could fire are checked, so
        the pre-loop initial load is excluded by construction (it is followed immediately by the
        first registration).
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"refresh-{label}",
                )
                real_load = module.load_state
                stale: list[int] = []
                loads = {"n": 0}

                def tracking_load(rd, *a, **kw):
                    loaded = real_load(rd, *a, **kw)
                    loads["n"] += 1
                    return loaded

                def fake_exec(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    # At the moment a turn ends, the reporter must be able to see THIS item's status.
                    pub = self.published(module)
                    if not isinstance(pub, dict):
                        stale.append(-1)
                        return
                    seen = {e["id6"]: e["status"] for e in pub["queue"]}
                    if seen.get(str(it.get("id6"))) is None:
                        stale.append(len(self.turns))

                buf = io.StringIO()
                with patch.object(module, "load_state", side_effect=tracking_load):
                    with patch.object(module, "execute_item", side_effect=fake_exec):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            module.run_queue(run_dir, retry_incomplete=False)

                self.assertGreater(
                    loads["n"], 2, f"{label}: the loop must reload state per iteration"
                )
                self.assertEqual(
                    stale,
                    [],
                    f"{label}: the reporter saw a snapshot missing an item the loop had already "
                    "processed; register_signal_report was not refreshed after a reload",
                )

    def test_the_reporter_is_published_before_the_first_turn_runs(self):
        """An interrupt at any point must report from real state, including before turn one."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                observed: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    observed.append(self.published(module))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"prepub-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertTrue(observed, f"{label}: the turn never ran")
                self.assertIsInstance(
                    observed[0],
                    dict,
                    f"{label}: state must be published BEFORE the first turn starts",
                )


class TheIntegrationLadderIsReachedFromTheLoop(RunQueueCase):
    """The two F-9 branches, which were BOTH uncovered on agy and both missing the refresh.

    RUNG 1 fires at the top of the loop for any deferred item. RUNGS 2/3 fire when `runnable is
    None`, which covers both the last-item case and the all-deferred case.
    """

    def test_rung_one_reattempts_a_deferred_integration_at_the_top_of_the_loop(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                calls: list[dict] = []

                def retry(rd, st, *a, **kw):
                    calls.append(dict(kw))
                    for entry in st["queue"]:
                        if entry["status"] == "integration-deferred":
                            entry["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [
                        self.item("def111", position=1, status="integration-deferred"),
                        self.item("aaa222", position=2),
                    ],
                    run_id=f"rung1-{label}",
                )
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    rc, state, _ = self.drive(module, run_dir)
                self.assertTrue(
                    calls, f"{label}: rung 1 never fired for a deferred item"
                )
                self.assertEqual(
                    calls[0].get("poll"),
                    None,
                    f"{label}: rung 1 must be the FREE re-attempt (no poll)",
                )
                self.assertEqual(self.statuses(state)["def111"], "executed")
                self.assertEqual(rc, 0)

    def test_rungs_two_and_three_fire_when_nothing_else_is_runnable(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                polled: list[dict] = []

                def retry(rd, st, *a, **kw):
                    polled.append(dict(kw))
                    if kw.get("poll"):
                        for entry in st["queue"]:
                            if entry["status"] == "integration-deferred":
                                entry["status"] = "executed"
                        module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("def111", position=1, status="integration-deferred")],
                    run_id=f"rung23-{label}",
                )
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    rc, state, _ = self.drive(module, run_dir)
                self.assertTrue(
                    any(kw.get("poll") for kw in polled),
                    f"{label}: rungs 2/3 must fire once `runnable is None`",
                )
                self.assertTrue(
                    any(kw.get("ask") for kw in polled),
                    f"{label}: rung 3 passes ask=True unconditionally (the SHARED ladder resolves "
                    "the interactive predicate itself, so an unattended run cannot stop on it)",
                )
                self.assertEqual(self.statuses(state)["def111"], "executed")

    def test_the_reporter_sees_post_ladder_state_at_both_reload_points(self):
        """F-9 STATED AS THE PROPERTY IT IS ABOUT, at the ladder reloads, on both hosts.

        Each ladder rung mutates state, saves it, and RELOADS it, rebinding `state`. If the host
        omits the refresh, the published object is the pre-ladder dict and a signal arriving there
        reports the item as still deferred after it has actually integrated.

        THE ASSERTION IS OBJECT IDENTITY, and the first version of this test was VACUOUS without it,
        which is worth recording. Comparing published STATUSES passes on the broken host too,
        because a test stub mutates the very dict the loop is holding, so the pre-reload snapshot
        and the live object are the same object and agree by construction. What actually
        distinguishes a refreshed host from a stale one is whether the dict the reporter would read
        IS the dict the loop is now working with. Measured at this HEAD that probe returns True on
        oc and False on agy, so it FAILS on the defect and passes after the repair, which is the
        whole requirement for a guard.
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                identity: list[bool] = []

                def retry(rd, st, *a, **kw):
                    for entry in st["queue"]:
                        if entry["status"] == "integration-deferred":
                            entry["status"] = "executed"
                    module.save_state(rd, st)
                    return []

                def fake_exec(rd, st, it, *a, **kw):
                    # `st` is the object the loop is holding RIGHT NOW, after the ladder's reload.
                    identity.append(self.published() is st)
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [
                        self.item("def111", position=1, status="integration-deferred"),
                        # A second runnable item is what keeps the loop alive past rung 1, so the
                        # probe fires AFTER the ladder reload rather than at the summary.
                        self.item("aaa222", position=2),
                    ],
                    run_id=f"ladderpub-{label}",
                )
                buf = io.StringIO()
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    with patch.object(module, "execute_item", side_effect=fake_exec):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            module.run_queue(run_dir, retry_incomplete=False)

                self.assertTrue(identity, f"{label}: no turn ran after the ladder")
                self.assertTrue(
                    all(identity),
                    f"{label}: after the integration ladder reloaded state, the object the "
                    "shutdown reporter would read is NOT the object the loop is working with, so "
                    "a signal arriving here reports a PRE-reload snapshot. oc calls "
                    "register_signal_report after each reload for exactly this reason "
                    "(oc_runipd.py:8645 states the invariant); the missing calls are agy's.",
                )

    def test_the_published_snapshot_matches_the_live_statuses_after_the_ladder(self):
        """The operator-visible consequence of the identity property above.

        Kept as a SEPARATE test with a deliberately different instrument: this one lets the ladder
        write through `save_state` and then compares the reporter's view of a LATER item against
        the live one. On a stale host the reporter reports the second item as still `queued` after
        it has executed.
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                self.clear_published()
                snapshots: list[dict] = []

                def retry(rd, st, *a, **kw):
                    for entry in st["queue"]:
                        if entry["status"] == "integration-deferred":
                            entry["status"] = "executed"
                    module.save_state(rd, st)
                    return []

                def fake_exec(rd, st, it, *a, **kw):
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    pub = self.published()
                    if isinstance(pub, dict):
                        snapshots.append({e["id6"]: e["status"] for e in pub["queue"]})

                run_dir = self.make_run(
                    [
                        self.item("def111", position=1, status="integration-deferred"),
                        self.item("aaa222", position=2),
                    ],
                    run_id=f"laddersnap-{label}",
                )
                buf = io.StringIO()
                with patch.object(
                    module, "retry_deferred_integrations", side_effect=retry
                ):
                    with patch.object(module, "execute_item", side_effect=fake_exec):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            module.run_queue(run_dir, retry_incomplete=False)

                self.assertTrue(snapshots, f"{label}: no turn ran after the ladder")
                self.assertEqual(
                    snapshots[-1].get("aaa222"),
                    "executed",
                    f"{label}: the reporter reports an item as unfinished AFTER its turn "
                    "completed, because the published reference predates the ladder's reload",
                )


class AnOrchestratorSpendsNoAgentTurn(RunQueueCase):
    """The `orchestrate` short-circuit, on both hosts, as behavior rather than as an AST shape.

    `tests/test_orchestrator_retirement.py:3575` asserts agy's BRANCH exists by parsing its AST.
    This asserts the consequence: an orchestrate item reaches `dispatch_orchestrator_item` and
    never reaches `execute_item`.
    """

    def test_an_orchestrate_item_never_reaches_execute_item(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                dispatched: list[str] = []

                # The real call is positional `(repo, run_dir, state, item, ...)`, so the item is
                # the FOURTH argument. Getting this wrong silently mis-binds `state` and the
                # failure surfaces far from the cause, which is why it is spelled out.
                def dispatch(repo, rd, st, it, *a, **kw):
                    dispatched.append(str(it.get("id6")))
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    return True

                run_dir = self.make_run(
                    [
                        self.item(
                            "orc111",
                            position=1,
                            action="orchestrate",
                            kind="orchestrator",
                        )
                    ],
                    run_id=f"orch-{label}",
                )
                with patch.object(
                    module, "dispatch_orchestrator_item", side_effect=dispatch
                ):
                    rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(
                    dispatched,
                    ["orc111"],
                    f"{label}: the orchestrator must reach the SHARED dispatcher",
                )
                self.assertEqual(
                    self.turns,
                    [],
                    f"{label}: an orchestrator must spend NO agent turn (that is the whole point "
                    "of the branch)",
                )
                self.assertEqual(rc, 0)

    def test_the_dispatcher_receives_both_state_sets_from_its_host(self):
        """The two EQUAL constants are passed here, and they are NOT interchangeable.

        `terminal_states=TERMINAL_STATES` and `success_states=EXECUTION_SUCCESS_STATES`. A split
        that swapped them would compile and would change which children count as done, so the
        binding is pinned at the call rather than left to a source substring.
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[dict] = []

                def dispatch(repo, rd, st, it, *a, **kw):
                    seen.append(dict(kw))
                    it["status"] = "executed"
                    module.save_state(rd, st)
                    return True

                run_dir = self.make_run(
                    [
                        self.item(
                            "orc222",
                            position=1,
                            action="orchestrate",
                            kind="orchestrator",
                        )
                    ],
                    run_id=f"orchargs-{label}",
                )
                with patch.object(
                    module, "dispatch_orchestrator_item", side_effect=dispatch
                ):
                    self.drive(module, run_dir)
                self.assertTrue(seen, f"{label}: the dispatcher was never called")
                self.assertEqual(
                    set(seen[0]["terminal_states"]), set(module.TERMINAL_STATES)
                )
                self.assertEqual(
                    set(seen[0]["success_states"]), set(module.EXECUTION_SUCCESS_STATES)
                )
                self.assertNotEqual(
                    set(seen[0]["success_states"]),
                    set(seen[0]["terminal_states"]),
                    f"{label}: the two sets must not be the same object or the swap is undetectable",
                )


class TheRunSummaryNamesItsOwnDriver(RunQueueCase):
    """F-6: `driver_label` is the ONE genuine host string in this function.

    Asserted as OUTPUT rather than as a source literal, so a split that bound the wrong label
    fails here even though `inspect.getsource` of a thin caller would contain neither string.
    """

    def test_the_summary_table_is_rendered_with_this_host_s_label(self):
        expected = {"oc_runipd": "opencode", "agy_runipd": "antigravity"}
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[str] = []
                real = module.render_run_summary_table

                def capture(*a, **kw):
                    seen.append(str(kw.get("driver_label")))
                    return real(*a, **kw)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"label-{label}"
                )
                with patch.object(
                    module, "render_run_summary_table", side_effect=capture
                ):
                    self.drive(module, run_dir)
                self.assertEqual(
                    seen,
                    [expected[label]],
                    f"{label}: the run summary must be labelled with THIS driver's name",
                )


class TheContinuationHintNamesItsOwnHost(RunQueueCase):
    """F-7: the STYLE resolves to oc, but `render_continuation_hint` itself is host-divergent.

    So the hint is a hook input in substance. Pinned as printed OUTPUT.
    """

    def test_the_printed_hint_names_this_host(self):
        expected = {"oc_runipd": "OpenCode", "agy_runipd": "Antigravity"}
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"hint2-{label}"
                )
                _, _, out = self.drive(module, run_dir)
                self.assertIn(
                    expected[label],
                    out,
                    f"{label}: the continuation hint must name THIS host's session continuity",
                )


class ToolIdentityIsRunFatalNotItemLocal(RunQueueCase):
    """The ordering `tests/test_lane_tool_identity.py:733` pins by SOURCE OFFSET, as behavior.

    `ToolIdentityError` subclasses `DriverError`. If the item-local `except DriverError` caught it
    first, the abort would be recorded as ONE item `failed-safely` while the remaining items kept
    running under the same wrong control plane. The INTENDED observable property is: the run
    ABORTS and the later items are NOT dispatched.

    READ `ADocumentedDefectInTheToolIdentityHandler` BELOW BEFORE TRUSTING THAT SENTENCE. Measured
    at this plan's execution HEAD, the intended property DOES NOT HOLD on either host: the handler
    swallows the exception. This class therefore pins only the half that does hold (the clause is
    reached at all, and a PLAIN `DriverError` stays item-local, which is what makes the ordering
    assertion non-vacuous), and the broken half is pinned separately and named as a defect.
    """

    def test_the_dedicated_clause_is_reached_rather_than_the_item_local_one(self):
        """The half that DOES hold: the identity error is not recorded as one item `failed-safely`.

        A plain `DriverError` marks the item `failed-safely` (see the test below). If the
        item-local clause were catching `ToolIdentityError` too, the item would carry that status.
        With the run-fatal `raise` restored, run_queue raises ToolIdentityError and terminates.
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()

                def boom(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    it["status"] = "running"
                    module.save_state(rd, st)
                    raise module.ToolIdentityError("tool-identity mismatch (synthetic)")

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"identity-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=boom):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        with self.assertRaises(module.ToolIdentityError):
                            module.run_queue(run_dir, retry_incomplete=False)
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertNotEqual(
                    self.statuses(state)["aaa111"],
                    "failed-safely",
                    f"{label}: a ToolIdentityError recorded as `failed-safely` means the "
                    "item-local DriverError clause caught it and the run-fatal abort was "
                    "silently downgraded (af7i6p OQ-02)",
                )

    def test_a_plain_driver_error_is_item_local(self):
        """The inverse, which is what makes the test above meaningful: an ordinary DriverError must
        NOT abort the run, or the ordering assertion would be vacuous."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()

                def boom(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    if it["id6"] == "aaa111":
                        raise module.DriverError("synthetic item-local failure")
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"driverr-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=boom):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(
                    self.turns,
                    ["aaa111", "bbb222"],
                    f"{label}: an item-local DriverError must not stop the queue",
                )
                state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
                self.assertEqual(
                    self.statuses(state)["aaa111"],
                    "failed-safely",
                    f"{label}: an item-local DriverError is recorded as failed-safely; this is "
                    "the status the ToolIdentityError test above proves is NOT used",
                )


class ToolIdentityHandlerRepairedAndRunFatal(RunQueueCase):
    """Pins the restored run-fatal behavior of ToolIdentityError on both hosts (hp9rot E-04 / BUG-02)."""

    def test_the_handler_raises_and_aborts_queue_execution(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()

                def boom(rd, st, it, *a, **kw):
                    self.turns.append(str(it.get("id6")))
                    it["status"] = "running"
                    module.save_state(rd, st)
                    raise module.ToolIdentityError("tool-identity mismatch (synthetic)")

                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"identdefect-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=boom):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        with self.assertRaises(module.ToolIdentityError):
                            module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(
                    self.turns,
                    ["aaa111"],
                    f"{label}: ToolIdentityError must abort immediately; second item must not run",
                )

    def test_the_source_contains_the_raise_statement(self):
        import ast
        import inspect

        for label, module in HOSTS:
            with self.subTest(host=label):
                src = inspect.getsource(module.run_queue)
                self.assertIn("except ToolIdentityError", src)
                self.assertLess(
                    src.index("except ToolIdentityError"),
                    src.index("except DriverError"),
                )
                handler = None
                for node in ast.walk(ast.parse(src.lstrip())):
                    if (
                        isinstance(node, ast.ExceptHandler)
                        and node.type is not None
                        and "ToolIdentityError" in ast.unparse(node.type)
                    ):
                        handler = node
                        break
                assert (
                    handler is not None
                ), f"{label}: no ToolIdentityError handler found"
                self.assertTrue(
                    any(isinstance(n, ast.Raise) for n in ast.walk(handler)),
                    f"{label}: the `raise` must be present in except ToolIdentityError",
                )


class TheBetweenItemStopCheckpointPrecedesSelection(RunQueueCase):
    """What `tests/test_runner_stop.py:607` pins by string offset, as behavior.

    The observable property: the poll happens BEFORE the next item is chosen, so a stop request
    written between two turns prevents the next dispatch rather than arriving too late.
    """

    def test_a_stop_request_between_turns_prevents_the_next_dispatch(self):
        from agent_workflows import runner_stop

        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [
                        self.item("aaa111", position=1),
                        self.item("bbb222", position=2, setid="other"),
                    ],
                    run_id=f"stop-{label}",
                )
                # Level 2 = stop after the current set. The second item is in ANOTHER set, so the
                # wind-down must refuse to start it and leave it `queued` (spec R22: no fabricated
                # disposition).
                polls = {"n": 0}
                real_poll = runner_stop.poll_stop

                def poll(rd, *a, **kw):
                    polls["n"] += 1
                    if polls["n"] == 1:
                        return real_poll(rd, *a, **kw)
                    return 2

                with patch.object(runner_stop, "poll_stop", side_effect=poll):
                    _, state, _ = self.drive(module, run_dir)
                statuses = self.statuses(state)
                self.assertEqual(statuses["aaa111"], "executed")
                self.assertEqual(
                    statuses["bbb222"],
                    "queued",
                    f"{label}: an out-of-boundary item must be left `queued`, never relabelled",
                )
                self.assertNotIn(
                    "bbb222",
                    self.turns,
                    f"{label}: the between-item poll must precede selection, or the stop arrives "
                    "after the dispatch it was meant to prevent",
                )


class TheStreamTrackerIsWiredThroughToTheTurn(RunQueueCase):
    """What both host CLI pins assert as three source substrings, as behavior.

    `tests/test_oc_runipd_cli.py:233` and `tests/test_agy_runipd_cli.py:1569` require the literal
    `"tracker = StreamTracker()"` and the exact `execute_item(...)` call string. The property is
    that a tracker instance is CREATED by the loop and REACHES the turn, which survives a split.
    """

    def test_a_stream_tracker_instance_reaches_execute_item(self):
        from agent_workflows.render_stream import StreamTracker

        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("tracker"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"tracker-{label}"
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertTrue(seen, f"{label}: the turn never ran")
                self.assertIsInstance(
                    seen[0],
                    StreamTracker,
                    f"{label}: the loop must create a StreamTracker and pass it to the turn",
                )

    def test_the_same_tracker_instance_is_reused_across_items(self):
        """One tracker per RUN, not per item: the summary table aggregates over the whole run."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                seen: list[object] = []

                def fake_exec(rd, st, it, *a, **kw):
                    seen.append(kw.get("tracker"))
                    it["status"] = "executed"
                    module.save_state(rd, st)

                run_dir = self.make_run(
                    [self.item("aaa111", position=1), self.item("bbb222", position=2)],
                    run_id=f"tracker2-{label}",
                )
                buf = io.StringIO()
                with patch.object(module, "execute_item", side_effect=fake_exec):
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        module.run_queue(run_dir, retry_incomplete=False)
                self.assertEqual(len(seen), 2)
                self.assertIs(
                    seen[0], seen[1], f"{label}: one tracker per run, not per item"
                )


class TheExitCodeReflectsTheRealOutcome(RunQueueCase):
    """The loop's return value, per state, on both hosts."""

    def test_a_fully_executed_queue_exits_zero(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"rc0-{label}"
                )
                rc, _, _ = self.drive(module, run_dir)
                self.assertEqual(rc, 0)

    def test_a_queue_with_a_non_success_terminal_item_exits_nonzero(self):
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()

                def on_turn(item):
                    item["status"] = "failed-safely"

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"rc1-{label}"
                )
                rc, _, _ = self.drive(module, run_dir, on_turn=on_turn)
                self.assertNotEqual(
                    rc, 0, f"{label}: a failed item must not be reported as a clean run"
                )

    def test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES(self):
        """The two EQUAL-valued constants are NOT interchangeable, and the loop uses each for a
        different job. Worth pinning because a split that passed the wrong one would be invisible:
        both are module constants with identical values across hosts, so no host-token diff shows it.

        `SUCCESS_STATES` = {reviewed, approved, executed} decides the EXIT CODE.
        `EXECUTION_SUCCESS_STATES` = {executed, substantially-complete} is handed to the
        orchestrator dispatcher to decide whether a CHILD counts as done.

        So `substantially-complete` is an execution success for retirement purposes and still exits
        NONZERO, which is the behavior asserted here.
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.assertEqual(
                    set(module.SUCCESS_STATES), {"reviewed", "approved", "executed"}
                )
                self.assertEqual(
                    set(module.EXECUTION_SUCCESS_STATES),
                    {"executed", "substantially-complete"},
                )
                self.turns.clear()

                def on_turn(item):
                    item["status"] = "substantially-complete"

                run_dir = self.make_run(
                    [self.item("aaa111", position=1)], run_id=f"rcsub-{label}"
                )
                rc, _, _ = self.drive(module, run_dir, on_turn=on_turn)
                self.assertNotEqual(
                    rc,
                    0,
                    f"{label}: the exit code is computed from SUCCESS_STATES, which does NOT "
                    "contain substantially-complete; a 0 here means the wrong constant was used",
                )


class AnApprovalBlockedQueueIsNotASilentSuccess(RunQueueCase):
    """`runnoop` Order 01 (`zz5yxq`) E-05: the MEASURED incident, and the control a naive fix breaks.

    THE INCIDENT (backlog `em0z50`, 2026-08-29). `aw oc run wtiso` was launched with all 8 `wtiso`
    plans at `- Status: reviewed`. It printed the run id, the state dir, and "No OpenCode session was
    captured for this run.", then EXITED 0. `aw runs <id>` showed `8 steps: 8 reviewed`,
    `action=execute`, `Attempts: 0` on every row, an empty `outcomes/`, and a single `run-created`
    event. The operator believed 8 plans were queued. The cause was that one status carried two
    contradictory meanings: `action_for('child','reviewed')` -> `'execute'` (a ROUTING decision, "run
    this") while `'reviewed' in SUCCESS_STATES` -> True (a COMPLETION decision, "this succeeded"), and
    the queue builder froze such an item as queue status `reviewed` rather than `queued`, so it was
    never dispatched AND was counted as a success.

    THE CONTROL IS THE LOAD-BEARING HALF OF THIS CLASS, not a courtesy. The tempting one-line fix is
    to remove `reviewed` from `SUCCESS_STATES`, and that is WRONG: `cascade_dependency_blocked`'s
    in-tree docstring records run `run-20260904T042705Z-1025943`, a 6-item all-`review` run of the
    `wslayout` Set that reviewed Orders 00 and 01 and then killed Orders 02-05 the instant Order 01
    reached `reviewed`, because that site hardcoded the execution bar. A review pass legitimately
    SUCCEEDS at `reviewed`. A suite covering only the execute case would pass over a re-broken
    review-mode Set run, so both cases are asserted here, on both hosts.
    """

    def test_a_reviewed_EXECUTE_item_is_not_counted_as_a_success(self):
        """The incident itself: an item the loop never dispatches must not produce exit 0."""
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()
                # `status="reviewed"` is what the REAL queue builder freezes for a `reviewed`-but-
                # unapproved plan (`runner_shared.initial_queue_status`: `reviewed` is absent from
                # `NON_TERMINAL_QUEUE_STATUSES`, so the entry is born NOT `queued`), paired with
                # `action="execute"` from `action_for`. Asserted against those two real functions
                # below, so this fixture cannot drift from what the builder actually writes.
                self.assertEqual(module.action_for("child", "reviewed"), "execute")
                self.assertEqual(
                    module.runner_shared.initial_queue_status("reviewed"), "reviewed"
                )
                run_dir = self.make_run(
                    [
                        self.item(
                            "aaa111", position=1, action="execute", status="reviewed"
                        ),
                        self.item(
                            "bbb222", position=2, action="execute", status="reviewed"
                        ),
                    ],
                    run_id=f"needsapproval-{label}",
                )
                rc, state, _ = self.drive(module, run_dir)
                self.assertEqual(
                    self.turns,
                    [],
                    f"{label}: neither item is dispatchable, so no turn may run; if one did, the "
                    "admission tuple changed and this test is measuring the wrong thing",
                )
                self.assertNotEqual(
                    rc,
                    0,
                    f"{label}: a queue of `reviewed`-but-unapproved EXECUTE items did NO WORK, so "
                    "exit 0 would report a silent success (backlog em0z50)",
                )
                self.assertEqual(
                    rc,
                    1,
                    f"{label}: zz5yxq OQ-02 resolved to 1 from this site. Spec 25kzda 5.6's exit 3 "
                    "for `needs_input` is reachable only by wiring the drivers to "
                    "`run_evidence.aggregate_run_exit`, which they do not call today.",
                )
                self.assertEqual(
                    self.statuses(state),
                    {"aaa111": "reviewed", "bbb222": "reviewed"},
                    f"{label}: no status may be REWRITTEN to produce the nonzero exit (spec R22); "
                    "the bar changed, the record did not",
                )

    def test_a_reviewed_REVIEW_item_is_still_a_success(self):
        """The control. A review pass ending `reviewed` is a COMPLETED review and must still exit 0.

        This is the case the docstring on `cascade_dependency_blocked` records as having been broken
        once by exactly the shape of fix this plan makes (run `run-20260904T042705Z-1025943`).
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                self.turns.clear()

                def on_turn(item):
                    item["status"] = "reviewed"

                run_dir = self.make_run(
                    [
                        self.item("aaa111", position=1, action="review"),
                        self.item("bbb222", position=2, action="review"),
                    ],
                    run_id=f"reviewmode-{label}",
                )
                rc, state, _ = self.drive(module, run_dir, on_turn=on_turn)
                self.assertEqual(
                    sorted(self.turns),
                    ["aaa111", "bbb222"],
                    f"{label}: both review items must actually be dispatched",
                )
                self.assertEqual(
                    rc,
                    0,
                    f"{label}: a completed REVIEW run must still exit 0. A nonzero here means the "
                    "execute-action fix was applied to the review action too, which is the "
                    "regression that made a review-mode Set run impossible to complete "
                    "(run-20260904T042705Z-1025943)",
                )
                self.assertEqual(
                    self.statuses(state), {"aaa111": "reviewed", "bbb222": "reviewed"}
                )

    def test_a_review_run_that_reached_reviewed_and_an_execute_one_get_OPPOSITE_verdicts(
        self,
    ):
        """The two halves stated as ONE assertion, so the distinction cannot be lost by editing one.

        Identical statuses, different actions, opposite verdicts. Driven through the SHARED predicate
        rather than the loop, because this is a claim about the bar itself.
        """
        for label, module in HOSTS:
            with self.subTest(host=label):
                bar = module.item_reached_success
                self.assertFalse(bar({"action": "execute", "status": "reviewed"}))
                self.assertTrue(bar({"action": "review", "status": "reviewed"}))
                # And the unambiguous cases still behave: a real execution success, and a failure.
                self.assertTrue(bar({"action": "execute", "status": "executed"}))
                self.assertFalse(bar({"action": "review", "status": "failed-safely"}))
                # THE NARROWING IS EXACTLY ONE STATUS FOR EXACTLY ONE ACTION. `substantially-complete`
                # must STILL be a non-success for reporting, on BOTH actions: the sibling test
                # `test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` pins that as a
                # deliberate contract, and it is what rules out reusing the DEPENDENCY bar
                # (`EXECUTION_SUCCESS_STATES`, which contains it) for this question.
                self.assertFalse(
                    bar({"action": "execute", "status": "substantially-complete"})
                )
                self.assertEqual(
                    set(module.runner_shared.EXECUTE_REPORTING_SUCCESS_STATES),
                    {"executed", "approved"},
                    f"{label}: the execute reporting bar must be SUCCESS_STATES minus `reviewed` "
                    "and nothing else",
                )


if __name__ == "__main__":
    unittest.main()
