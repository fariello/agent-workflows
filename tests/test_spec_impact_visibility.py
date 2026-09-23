"""specvis (st5klo): declared spec edits are announced at run START and reported at run END, on BOTH hosts.

WHY THIS FILE EXISTS ALONGSIDE `test_spec_visibility.py`. That file tests the spec-impact PIECES:
`declared_spec_paths`, `spec_impacts_for_queue`, the renderer's wording and purity, and the fact that
both drivers bind the same objects. Every one of its cases either calls a helper directly or asserts
object identity. This file tests the BEHAVIOR instead: it drives the two drivers' real entry points and
asserts on captured output, because a symbol assertion cannot tell you whether a host actually calls
the thing it imports.

THAT DISTINCTION IS NOT ACADEMIC - IT HID A LIVE DEFECT, AND THIS FILE WAS WRITTEN AFTER FINDING IT.
The plan this file implements was authored, and then reviewed, on the belief that the start-of-run
announcement already worked on both hosts; the review pasted a captured `SPEC CHANGES: ...` line as
proof and instructed the executor NOT to write a test that fails on it. Driving the real entry points
shows it fired on NEITHER host:

  * `runner_shared.spec_impacts_for_queue` reads each item's plan location from `item["path"]` or
    `item["plan_path"]`;
  * a real runner queue entry has NEITHER. Both drivers freeze the location under
    `"configured_file"` (`oc_runipd.py`/`agy_runipd.py`, at their queue-append sites) and nothing ever
    assigns `"path"`;
  * so the announcement computed an EMPTY impact set for every item of every real run and printed
    nothing, on both hosts, while the suite stayed green because its fixtures hand-built queues
    carrying the key production never writes.

The review's captured line was therefore produced from a fixture, not from a run. Recorded here because
the lesson generalizes: the way to test an announcement is to make the program announce.

WHAT IS ASSERTED HERE:
  * START: a queue whose plan declares a `.spec.md` announces it, on BOTH hosts, from the real
    `initialize_run` (fails at pre-change HEAD on both);
  * START: a queue declaring none stays silent, and a FAILED computation says so and still starts, so
    the two are DISTINGUISHABLE (the old handler made them identical);
  * START: the announcement is ONE whole-queue event emitted BEFORE any dispatch, never per item;
  * END: both hosts report the run's spec edits with the summary, reconciled per item and aggregated;
  * END: the two asymmetries - a spec MODIFIED but not declared (the case that matters) and one
    DECLARED but not modified;
  * END: the three honesty cases - an item that never finalized, an empty-because-REFUSED
    reconciliation, and the per-item-to-per-queue aggregation counts;
  * END: the non-primary summary sites are labelled POSSIBLY INCOMPLETE.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd, render_stream, runner_shared

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

_SPEC_REL = ".aw/records/specs/20260826-0718-01-sp0001-demo.spec.md"

_PLAN = """# IPD: demo {id6}

- Date: 2026-09-07
- Kind: child
- Concern: demo
- Scope: demo
- Scope-Paths: {scope}
- Item-Dependencies: none
- Status: approved
- Set: {setid}
- Order: {order}
- Id: {id6}

## Goal

demo
"""


def _plan_text(id6: str, *, scope: str, setid: str = "demo", order: int = 1) -> str:
    return _PLAN.format(id6=id6, scope=scope, setid=setid, order=order)


def _start_args(repo: Path, selectors: list[str]) -> argparse.Namespace:
    """The same Namespace shape `test_run_order_announcement` uses to drive `initialize_run`."""
    return argparse.Namespace(
        repo=str(repo),
        selectors=selectors,
        manifest=None,
        runbook=None,
        session=None,
        run_id=None,
        full_auto=False,
        opencode="opencode",
        model=None,
        agent=None,
        auto=True,
        output_mode="clean",
        stall_timeout=600.0,
        validate=False,
        self_finalize=True,
        isolate_worktree=False,
        max_items_per_session=4,
    )


def _repo(temp: Path) -> Path:
    repo = temp / "repo"
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def _write_plan(
    repo: Path, id6: str, *, scope: str, setid: str = "demo", order: int = 1
) -> Path:
    path = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20260907-{setid}-{order:02d}-{id6}-demo.ipd.md"
    )
    path.write_text(_plan_text(id6, scope=scope, setid=setid, order=order), "utf-8")
    return path


def _initialize(mod, repo: Path, selectors: list[str]) -> tuple[Path, str]:
    """Drive the driver's REAL queue-freeze entry point and capture what it printed."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_dir = mod.initialize_run(_start_args(repo, selectors))
    return run_dir, buf.getvalue()


class StartAnnouncementIsBehavioralOnBothHostsTests(unittest.TestCase):
    """E-01/E-02: the START announcement must fire from the REAL entry point, on BOTH hosts.

    Fails at pre-change HEAD on both drivers. That is deliberate and contradicts the plan's own
    instruction: see this module's docstring for the measurement that overturned it.
    """

    def test_declared_spec_edit_is_announced_from_the_real_entry_point(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    _write_plan(
                        repo, "sp0001", scope=f"agent_workflows/cli.py, {_SPEC_REL}"
                    )
                    _run_dir, out = _initialize(mod, repo, ["sp0001"])
                    self.assertIn("SPEC CHANGES", out)
                    self.assertIn(_SPEC_REL, out)
                    self.assertIn("sp0001", out)

    def test_a_queue_declaring_no_spec_says_nothing(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    _write_plan(repo, "sp0002", scope="agent_workflows/cli.py")
                    _run_dir, out = _initialize(mod, repo, ["sp0002"])
                    self.assertNotIn("SPEC CHANGES", out)

    def test_the_real_queue_entry_carries_no_path_key_which_is_why_this_needed_fixing(
        self,
    ):
        """The ROOT CAUSE, pinned so a refactor cannot quietly restore the broken shape.

        The shared helper documents its input as carrying `path`/`plan_path`; a real queue entry
        carries `configured_file` instead. If a future change makes the announcement read the raw
        queue again, this test says exactly why the output went silent.
        """
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    _write_plan(repo, "sp0003", scope=_SPEC_REL)
                    run_dir, _out = _initialize(mod, repo, ["sp0003"])
                    state = json.loads((run_dir / "state.json").read_text("utf-8"))
                    item = state["queue"][0]
                    self.assertNotIn("path", item)
                    self.assertNotIn("plan_path", item)
                    self.assertTrue(item["configured_file"])
                    # Raw queue -> nothing. Adapted queue -> the impact. Both, in one assertion pair,
                    # so the fix's necessity is visible rather than argued.
                    self.assertEqual(
                        runner_shared.spec_impacts_for_queue(repo, state["queue"]), []
                    )
                    adapted = mod.queue_with_plan_paths(repo, state["queue"])
                    self.assertEqual(
                        runner_shared.spec_impacts_for_queue(repo, adapted),
                        [{"id6": "sp0003", "setid": "demo", "specs": [_SPEC_REL]}],
                    )

    def test_announcement_is_one_whole_queue_event_before_any_dispatch(self):
        """E-01's placement regression guard (maintainer requirement 2026-09-08).

        The assertion that specs will be edited is made at the start of the RUNNER, covering the whole
        queue, BEFORE anything is dispatched - NOT at the start of each IPD. Asserted three ways: the
        header appears exactly ONCE for a three-plan queue, it names every declaring plan in that one
        block, and it is printed by the queue-freeze call itself, which returns before any item runs.
        """
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    _write_plan(repo, "sp0010", scope=_SPEC_REL, order=1)
                    _write_plan(repo, "sp0011", scope=_SPEC_REL, order=2)
                    _write_plan(repo, "sp0012", scope="agent_workflows/cli.py", order=3)
                    run_dir, out = _initialize(
                        mod, repo, ["sp0010", "sp0011", "sp0012"]
                    )
                    self.assertEqual(
                        out.count("SPEC CHANGES"),
                        1,
                        "one whole-queue announcement, not one per item",
                    )
                    self.assertIn("2 queued plan(s)", out)
                    self.assertIn("sp0010", out)
                    self.assertIn("sp0011", out)
                    # Pre-dispatch: no item has been attempted at the moment this was printed.
                    state = json.loads((run_dir / "state.json").read_text("utf-8"))
                    for item in state["queue"]:
                        self.assertEqual(item["attempts"], [])
                        self.assertEqual(item["status"], "queued")


class StartAnnouncementFailureIsVisibleTests(unittest.TestCase):
    """E-01: a computation failure prints a named advisory and the run still starts.

    THE LOAD-BEARING PROPERTY IS DISTINGUISHABILITY. The old handler was `except Exception: pass`, so
    "this run declares no spec edits" and "the computation crashed" rendered identically and an
    operator could not tell a clean run from a broken announcer.
    """

    def _raise(self, *_a, **_k):
        raise RuntimeError("synthetic impact failure")

    def test_failure_prints_a_named_advisory_and_the_run_still_starts(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    _write_plan(repo, "sp0004", scope=_SPEC_REL)
                    # PATCH WHERE `announce_run_order` RESOLVES THE NAME, which is `runner_shared`
                    # and no longer `oc_runipd` (runnerlayer Order 02 `1f7xno`): the announcer moved
                    # out of the host driver into the shared module, so its body now resolves
                    # `spec_impacts_for_queue` in `runner_shared`'s globals. Patching the host
                    # attribute would no longer intercept anything, and this test would pass
                    # VACUOUSLY on an announcer that never crashed. Both hosts call the one shared
                    # object, so this still covers agy without patching agy.
                    original = runner_shared.spec_impacts_for_queue
                    runner_shared.spec_impacts_for_queue = self._raise
                    try:
                        run_dir, out = _initialize(mod, repo, ["sp0004"])
                    finally:
                        runner_shared.spec_impacts_for_queue = original
                    self.assertIn("could not be computed", out)
                    self.assertIn("RuntimeError", out)
                    self.assertIn("UNREPORTED, not absent", out)
                    # The run still started: state was frozen and the run directory exists.
                    self.assertTrue((run_dir / "state.json").is_file())
                    # And the run-order announcement itself was unaffected.
                    self.assertIn("Run order", out)

    def test_failure_output_differs_from_the_empty_case(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    _write_plan(repo, "sp0005", scope="agent_workflows/cli.py")
                    _run_dir, empty_out = _initialize(mod, repo, ["sp0005"])
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    _write_plan(repo, "sp0005", scope="agent_workflows/cli.py")
                    # Same relocation as the sibling test above: the announcer lives in
                    # `runner_shared` now, so that is where the name resolves.
                    original = runner_shared.spec_impacts_for_queue
                    runner_shared.spec_impacts_for_queue = self._raise
                    try:
                        _run_dir, fail_out = _initialize(mod, repo, ["sp0005"])
                    finally:
                        runner_shared.spec_impacts_for_queue = original
                self.assertNotEqual(
                    empty_out,
                    fail_out,
                    "a crashed announcer must not render identically to a clean run",
                )
                self.assertNotIn("could not be computed", empty_out)
                self.assertIn("could not be computed", fail_out)


class EndOfRunReportTests(unittest.TestCase):
    """E-03: both hosts report, at run END, what was declared and what was actually changed."""

    def _state(self, repo: Path, queue: list[dict]) -> dict:
        return {"repo": str(repo), "queue": queue}

    def _item(self, id6: str, plan: Path, repo: Path, **extra) -> dict:
        item = {
            "id6": id6,
            "setid": "demo",
            "status": "executed",
            "action": "execute",
            "configured_file": str(plan.relative_to(repo)),
        }
        item.update(extra)
        return item

    def _report(self, mod, state: dict, *, partial: bool = False) -> str:
        buf = io.StringIO()
        mod.report_run_spec_edits(state, stream=buf, partial=partial)
        return buf.getvalue()

    def test_a_modified_but_undeclared_spec_is_reported_on_both_hosts(self):
        """The case that MATTERS: an undeclared contract change."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    plan = _write_plan(repo, "sp0006", scope="agent_workflows/cli.py")
                    item = self._item(
                        "sp0006",
                        plan,
                        repo,
                        spec_edits={
                            "state": mod.SPEC_RECONCILED,
                            "declared": [],
                            "modified_not_declared": [_SPEC_REL],
                            "declared_not_modified": [],
                        },
                    )
                    out = self._report(mod, self._state(repo, [item]))
                    self.assertIn("SPEC EDITS THIS RUN", out)
                    self.assertIn("UNDECLARED SPEC CHANGE", out)
                    self.assertIn(_SPEC_REL, out)

    def test_a_declared_but_unmodified_spec_is_reported_on_both_hosts(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    plan = _write_plan(repo, "sp0007", scope=_SPEC_REL)
                    item = self._item(
                        "sp0007",
                        plan,
                        repo,
                        spec_edits={
                            "state": mod.SPEC_RECONCILED,
                            "declared": [_SPEC_REL],
                            "modified_not_declared": [],
                            "declared_not_modified": [_SPEC_REL],
                        },
                    )
                    out = self._report(mod, self._state(repo, [item]))
                    self.assertIn("DECLARED BUT NOT MODIFIED", out)
                    self.assertIn(_SPEC_REL, out)

    def test_an_item_that_never_finalized_is_not_rendered_as_clean(self):
        """F-9 honesty case 1: no reconciliation exists, so no clean delta may be claimed."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    plan = _write_plan(repo, "sp0008", scope=_SPEC_REL)
                    item = self._item("sp0008", plan, repo, status="partial")
                    out = self._report(mod, self._state(repo, [item]))
                    self.assertIn("NOT FINALIZED", out)
                    self.assertIn("sp0008", out)
                    self.assertIn("1 never finalized", out)
                    self.assertNotIn("UNDECLARED SPEC CHANGE", out)

    def test_an_empty_because_refused_reconciliation_is_not_an_all_clear(self):
        """F-9 honesty case 2: a refused precheck returns ({}, {}) exactly as a clean delta does."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    plan = _write_plan(repo, "sp0009", scope=_SPEC_REL)
                    item = self._item(
                        "sp0009",
                        plan,
                        repo,
                        spec_edits={
                            "state": mod.SPEC_RECONCILE_REFUSED,
                            "declared": [_SPEC_REL],
                            "modified_not_declared": [],
                            "declared_not_modified": [],
                        },
                    )
                    out = self._report(mod, self._state(repo, [item]))
                    self.assertIn("UNVERIFIED", out)
                    self.assertIn("is NOT an all-clear", out)
                    self.assertIn("sp0009", out)
                    self.assertIn("could NOT be reconciled", out)

    def test_the_aggregation_counts_all_three_states(self):
        """F-9 honesty case 3: per-ITEM data aggregated to a per-RUN statement."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    good = _write_plan(repo, "sp0020", scope=_SPEC_REL, order=1)
                    bad = _write_plan(repo, "sp0021", scope=_SPEC_REL, order=2)
                    none = _write_plan(repo, "sp0022", scope=_SPEC_REL, order=3)
                    queue = [
                        self._item(
                            "sp0020",
                            good,
                            repo,
                            spec_edits={
                                "state": mod.SPEC_RECONCILED,
                                "declared": [_SPEC_REL],
                                "modified_not_declared": [],
                                "declared_not_modified": [],
                            },
                        ),
                        self._item(
                            "sp0021",
                            bad,
                            repo,
                            spec_edits={
                                "state": mod.SPEC_RECONCILE_REFUSED,
                                "declared": [_SPEC_REL],
                                "modified_not_declared": [],
                                "declared_not_modified": [],
                            },
                        ),
                        self._item("sp0022", none, repo, status="queued"),
                    ]
                    out = self._report(mod, self._state(repo, queue))
                    self.assertIn("Reconciled 1 item(s)", out)
                    self.assertIn("1 could NOT be reconciled", out)
                    self.assertIn("1 never finalized", out)
                    # And the whole-queue DECLARED set is still reported beside the per-item view.
                    self.assertIn("3 plan(s) declared edits", out)

    def test_the_non_primary_sites_label_the_report_possibly_incomplete(self):
        """OQ-01's resolution: all sites wired, the non-primary ones LABELLED."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    plan = _write_plan(repo, "sp0030", scope=_SPEC_REL)
                    state = self._state(repo, [self._item("sp0030", plan, repo)])
                    normal = self._report(mod, state, partial=False)
                    aborted = self._report(mod, state, partial=True)
                    self.assertIn("POSSIBLY INCOMPLETE", aborted)
                    self.assertNotIn("POSSIBLY INCOMPLETE", normal)

    def test_a_run_touching_no_spec_reports_nothing(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = _repo(Path(t))
                    plan = _write_plan(repo, "sp0031", scope="agent_workflows/cli.py")
                    item = self._item(
                        "sp0031",
                        plan,
                        repo,
                        spec_edits={
                            "state": mod.SPEC_RECONCILED,
                            "declared": [],
                            "modified_not_declared": [],
                            "declared_not_modified": [],
                        },
                    )
                    out = self._report(mod, self._state(repo, [item]))
                    self.assertEqual(out, "")

    def test_the_report_reports_its_own_failure_rather_than_vanishing(self):
        """The E-01 lesson applied to the new surface: silence must not mean two things here either."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                buf = io.StringIO()
                # No "repo" key -> the summary computation raises inside the guard.
                mod.report_run_spec_edits({"queue": []}, stream=buf)
                self.assertIn("could not be computed", buf.getvalue())


class EndOfRunReportIsWiredAtEverySummarySiteTests(unittest.TestCase):
    """E-03: all THREE summary sites per host call the report, and the non-primary two label it.

    Asserted against the SOURCE because two of the three sites are exception handlers reachable only
    by interrupting or failing a real run. The assertion is deliberately structural rather than a
    grep for a name: it counts call sites and checks the `partial=True` argument, which is the part
    OQ-01 actually turned on.
    """

    def test_each_driver_calls_the_report_three_times_with_two_labelled_partial(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                src = Path(str(mod.__file__)).read_text("utf-8")
                calls = src.count("report_run_spec_edits(state")
                self.assertEqual(
                    calls,
                    3,
                    f"{name} must call the end-of-run report at all 3 summary sites",
                )
                self.assertEqual(
                    src.count("report_run_spec_edits(state, partial=True)"),
                    2,
                    f"{name}'s two non-primary sites must label the report possibly-incomplete",
                )


class OneSharedDefinitionTests(unittest.TestCase):
    """Anti-re-fork: the end-of-run report has ONE definition, reached by both hosts.

    Object identity is asserted here as a STRUCTURAL claim (that neither driver holds its own copy),
    which is a legitimate use of it. It is NOT offered as evidence that either host CALLS the thing:
    the behavioral classes above do that, for the reason this module's docstring records.
    """

    def test_both_drivers_bind_the_same_objects(self):
        for symbol in (
            "report_run_spec_edits",
            "spec_edit_summary",
            "spec_edit_record",
            "record_item_spec_edits",
            "queue_plan_path",
            "queue_with_plan_paths",
        ):
            with self.subTest(symbol=symbol):
                self.assertIs(
                    getattr(agy_runipd, symbol),
                    getattr(oc_runipd, symbol),
                    "a second copy in the other driver is the drift this Set guards against",
                )

    def test_the_wording_lives_in_the_shared_renderer(self):
        self.assertTrue(hasattr(render_stream, "format_spec_edit_report"))
        self.assertTrue(hasattr(render_stream, "format_spec_impact_failure"))
        self.assertEqual(
            render_stream.format_spec_edit_report.__module__,
            "agent_workflows.render_stream",
        )

    def test_exactly_one_definition_of_each_new_formatter_package_wide(self):
        root = Path(render_stream.__file__).parent
        for symbol in ("format_spec_edit_report", "format_spec_impact_failure"):
            with self.subTest(symbol=symbol):
                defining = [
                    p.name
                    for p in root.glob("*.py")
                    if f"def {symbol}(" in p.read_text("utf-8")
                ]
                self.assertEqual(defining, ["render_stream.py"])

    def test_the_renderers_are_pure(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            render_stream.format_spec_edit_report(
                {
                    "declared": {"a": ["x.spec.md"]},
                    "reconciled": [],
                    "refused": [],
                    "not_finalized": ["a"],
                }
            )
            render_stream.format_spec_impact_failure(RuntimeError("x"))
        self.assertEqual(buf.getvalue(), "")


class QueuePlanPathTests(unittest.TestCase):
    """The resolver E-01's fix rests on: how a real queue entry finds its plan file."""

    def test_prefers_an_explicit_path_then_falls_back_through_to_configured_file(self):
        with tempfile.TemporaryDirectory() as t:
            repo = _repo(Path(t))
            plan = _write_plan(repo, "sp0040", scope=_SPEC_REL)
            rel = str(plan.relative_to(repo))
            self.assertEqual(
                oc_runipd.queue_plan_path(repo, {"path": rel, "id6": "sp0040"}), plan
            )
            self.assertEqual(
                oc_runipd.queue_plan_path(
                    repo, {"configured_file": rel, "id6": "sp0040"}
                ),
                plan,
            )
            # last_plan_path is what stays correct after a finalize MOVED the plan.
            self.assertEqual(
                oc_runipd.queue_plan_path(
                    repo, {"last_plan_path": str(plan), "id6": "sp0040"}
                ),
                plan,
            )

    def test_falls_back_to_the_authoritative_resolver_when_the_frozen_path_is_stale(
        self,
    ):
        with tempfile.TemporaryDirectory() as t:
            repo = _repo(Path(t))
            plan = _write_plan(repo, "sp0041", scope=_SPEC_REL)
            moved = repo / ".aw" / "records" / "plans" / "executed" / plan.name
            moved.parent.mkdir(parents=True, exist_ok=True)
            plan.rename(moved)
            stale = str(plan.relative_to(repo))
            found = oc_runipd.queue_plan_path(
                repo, {"configured_file": stale, "id6": "sp0041"}
            )
            self.assertEqual(found, moved.resolve())

    def test_returns_none_rather_than_raising_when_nothing_resolves(self):
        with tempfile.TemporaryDirectory() as t:
            repo = _repo(Path(t))
            self.assertIsNone(oc_runipd.queue_plan_path(repo, {"id6": "zzzzzz"}))
            self.assertIsNone(oc_runipd.queue_plan_path(repo, {}))


class RecordItemSpecEditsTests(unittest.TestCase):
    """E-03: the per-item record, including the refused-vs-clean disambiguation."""

    def test_a_refused_reconciliation_is_recorded_as_refused_not_clean(self):
        with tempfile.TemporaryDirectory() as t:
            repo = _repo(Path(t))
            plan = _write_plan(repo, "sp0050", scope=_SPEC_REL)
            item: dict = {"id6": "sp0050"}
            # An empty pair with NO begin receipt in the tree: the precheck refuses, so this must be
            # recorded as `refused` rather than as a clean delta.
            record = oc_runipd.record_item_spec_edits(
                repo, plan, item, reconcile=lambda _r, _p: ({}, {})
            )
            self.assertEqual(record["state"], oc_runipd.SPEC_RECONCILE_REFUSED)
            self.assertEqual(item["spec_edits"], record)

    def test_a_reconciliation_that_raises_is_recorded_as_refused(self):
        with tempfile.TemporaryDirectory() as t:
            repo = _repo(Path(t))
            plan = _write_plan(repo, "sp0051", scope=_SPEC_REL)
            item: dict = {"id6": "sp0051"}

            def _boom(_r, _p):
                raise RuntimeError("reconciliation exploded")

            record = oc_runipd.record_item_spec_edits(repo, plan, item, reconcile=_boom)
            self.assertEqual(record["state"], oc_runipd.SPEC_RECONCILE_REFUSED)

    def test_a_nonempty_delta_is_recorded_reconciled_and_filtered_to_specs(self):
        with tempfile.TemporaryDirectory() as t:
            repo = _repo(Path(t))
            plan = _write_plan(repo, "sp0052", scope=_SPEC_REL)
            item: dict = {"id6": "sp0052"}
            record = oc_runipd.record_item_spec_edits(
                repo,
                plan,
                item,
                reconcile=lambda _r, _p: (
                    {"other.spec.md": "changed", "src/app.py": "changed"},
                    {_SPEC_REL: "unmodified", "tests/t.py": "unmodified"},
                ),
            )
            self.assertEqual(record["state"], oc_runipd.SPEC_RECONCILED)
            self.assertEqual(record["modified_not_declared"], ["other.spec.md"])
            self.assertEqual(record["declared_not_modified"], [_SPEC_REL])
            self.assertEqual(record["declared"], [_SPEC_REL])


if __name__ == "__main__":
    unittest.main()
