"""runorder (prpipy): the requested run order is authoritative, and every reordering is announced.

THE DEFECT THIS PINS. `aw oc run A B` recorded the operator's typed sequence as `position` and then
DISCARDED it at dispatch: `queue_sort_key` returned `(dependency_depth, setid, order, id6, position)`,
so two independent plans in different Sets tied at depth 0 and the SET ID decided, alphabetically.
Measured in run `run-20260901T042331Z-118022`: the maintainer typed `aw oc run m73aet 6lu3rq`, the
queue froze as `position 1 m73aet` / `position 2 6lu3rq`, and `events.jsonl` shows `6lu3rq` starting
at 04:23:31 and `m73aet` at 04:44:10, because `"runmixed" < "runtrail"`. Nothing announced it.

WHAT IS ASSERTED HERE:
  * the requested order decides among equally-ready nodes (the measured Set ids, not synthetic ones);
  * a DECLARED `Item-Dependencies` edge STILL outranks a contradicting requested order (spec 25kzda
    5.4 rule 5), which is the property the reordering fix must not break;
  * the order is ANNOUNCED at queue build on every run, is recorded durably, and a divergence warns
    with both orders plus a per-item cause that distinguishes a declared edge from a tiebreak;
  * the message never claims a TYPED order for an EXPANDED selector (`all`, a setid, `reviews`);
  * `--prepare-only` previews EXECUTION order rather than frozen identity order;
  * BOTH host drivers get the announcement and the preview, from ONE shared formatter.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd, render_stream

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


def _item(
    id6: str,
    *,
    setid: str = "demo",
    order: int = 1,
    position: int = 1,
    deps: list[str] | None = None,
    status: str = "queued",
) -> dict:
    return {
        "id6": id6,
        "setid": setid,
        "order": order,
        "position": position,
        "status": status,
        "action": "execute",
        "dependencies": list(deps or []),
    }


def _dispatch_order(queue: list[dict]) -> list[str]:
    """The order `run_queue` would SELECT in: the exact expression used at its single sort site."""
    by_id = {entry["id6"]: entry for entry in queue}
    return [
        item["id6"]
        for item in sorted(queue, key=lambda it: oc_runipd.queue_sort_key(it, by_id))
    ]


class RequestedOrderIsAuthoritativeTests(unittest.TestCase):
    """E-01/E-02: the typed sequence decides among equally-ready nodes."""

    def test_typed_order_beats_alphabetical_setid(self):
        """The MEASURED case: `aw oc run m73aet 6lu3rq` ran 6lu3rq first because runmixed < runtrail."""
        queue = [
            _item("m73aet", setid="runtrail", order=1, position=1),
            _item("6lu3rq", setid="runmixed", order=1, position=2),
        ]
        self.assertLess(
            "runmixed",
            "runtrail",
            "precondition: the Set ids sort OPPOSITE to the typed order, as in the real run",
        )
        self.assertEqual(
            _dispatch_order(queue),
            ["m73aet", "6lu3rq"],
            "the operator typed m73aet first; alphabetical Set id must not invert it",
        )

    def test_typed_order_beats_numeric_order_too(self):
        """`Order` is a WITHIN-set field; it must not reorder what the operator typed either."""
        queue = [
            _item("bbbbbb", setid="demo", order=2, position=1),
            _item("aaaaaa", setid="demo", order=1, position=2),
        ]
        self.assertEqual(_dispatch_order(queue), ["bbbbbb", "aaaaaa"])

    def test_declared_edge_still_beats_a_contradicting_typed_order(self):
        """spec 25kzda 5.4 rule 5: an explicit edge always wins. This must hold BEFORE and AFTER."""
        queue = [
            _item(
                "depend", setid="demo", order=1, position=1, deps=["executed:prereq"]
            ),
            _item("prereq", setid="demo", order=9, position=2),
        ]
        self.assertEqual(
            _dispatch_order(queue),
            ["prereq", "depend"],
            "the typed order said depend-first; the declared edge must still reorder it",
        )

    def test_transitive_chain_still_orders_by_depth_against_the_typed_order(self):
        queue = [
            _item("aaaaaa", position=1, deps=["executed:bbbbbb"]),
            _item("bbbbbb", position=2, deps=["executed:cccccc"]),
            _item("cccccc", position=3),
        ]
        self.assertEqual(_dispatch_order(queue), ["cccccc", "bbbbbb", "aaaaaa"])

    def test_position_stays_frozen_identity(self):
        """E-02 must not make `position` mutable: outcome/prompt/session filenames key on it."""
        queue = [
            _item("depend", position=1, deps=["executed:prereq"]),
            _item("prereq", position=2, order=9),
        ]
        _dispatch_order(queue)
        self.assertEqual([it["position"] for it in queue], [1, 2])

    def test_the_key_is_one_shared_object(self):
        self.assertIs(agy_runipd.queue_sort_key, oc_runipd.queue_sort_key)
        self.assertIs(agy_runipd.run_order_rationale, oc_runipd.run_order_rationale)


class RunOrderRationaleTests(unittest.TestCase):
    """E-04: the runner-side computation of requested vs executed order and the per-item cause."""

    def test_unreordered_queue_reports_no_divergence(self):
        queue = [
            _item("m73aet", setid="runtrail", position=1),
            _item("6lu3rq", setid="runmixed", position=2),
        ]
        r = oc_runipd.run_order_rationale(queue, selectors=["m73aet", "6lu3rq"])
        self.assertFalse(r["reordered"])
        self.assertEqual(r["requested"], ["m73aet", "6lu3rq"])
        self.assertEqual(r["executed"], ["m73aet", "6lu3rq"])
        self.assertEqual(r["causes"], {})
        self.assertEqual(r["request_kind"], "typed")

    def test_declared_edge_divergence_names_the_specific_edge(self):
        queue = [
            _item("depend", position=1, deps=["executed:prereq"]),
            _item("prereq", position=2),
        ]
        r = oc_runipd.run_order_rationale(queue, selectors=["depend", "prereq"])
        self.assertTrue(r["reordered"])
        self.assertEqual(r["executed"], ["prereq", "depend"])
        self.assertIn("prereq", r["causes"])
        self.assertIn("executed:prereq", r["causes"]["prereq"])
        self.assertTrue(
            r["causes"]["prereq"].startswith("declared dependency:"),
            f"a declared edge must be labelled as such, got {r['causes']['prereq']!r}",
        )

    def test_tiebreak_divergence_is_labelled_differently(self):
        """A hand-edited/legacy entry with no `position` falls back to the (Set, Order, id6) tiebreak."""
        legacy_b = {
            "id6": "bbbbbb",
            "setid": "zzzset",
            "status": "queued",
            "action": "execute",
            "dependencies": [],
        }
        legacy_a = {
            "id6": "aaaaaa",
            "setid": "aaaset",
            "status": "queued",
            "action": "execute",
            "dependencies": [],
        }
        r = oc_runipd.run_order_rationale([legacy_b, legacy_a], selectors=["all"])
        self.assertTrue(r["reordered"])
        self.assertEqual(r["executed"], ["aaaaaa", "bbbbbb"])
        for id6, cause in r["causes"].items():
            self.assertTrue(
                cause.startswith("tiebreak:"),
                f"{id6}: a move with NO declared edge must be labelled a tiebreak, got {cause!r}",
            )

    def test_expanded_selection_is_not_called_a_typed_order(self):
        queue = [_item("aaaaaa", position=1), _item("bbbbbb", position=2)]
        for selectors in (
            ["all"],
            ["demo"],
            ["reviews"],
            ["aaaaaa", "bbbbbb", "cccccc"],
        ):
            with self.subTest(selectors=selectors):
                r = oc_runipd.run_order_rationale(queue, selectors=selectors)
                self.assertEqual(r["request_kind"], "expanded")


class AnnouncementFormatterTests(unittest.TestCase):
    """E-04: the message TEXT lives once, in the pure renderer."""

    def _lines(self, rationale, **kw):
        return render_stream.format_run_order_announcement(rationale, **kw)

    def test_unreordered_run_still_announces_its_order(self):
        queue = [_item("aaaaaa", position=1), _item("bbbbbb", position=2)]
        lines = self._lines(
            oc_runipd.run_order_rationale(queue, selectors=["aaaaaa", "bbbbbb"])
        )
        text = "\n".join(lines)
        self.assertIn("Run order", text)
        self.assertIn("01 aaaaaa", text)
        self.assertIn("02 bbbbbb", text)
        self.assertNotIn("WARNING", text)

    def test_reordered_run_names_both_orders_and_the_cause(self):
        queue = [
            _item("depend", position=1, deps=["executed:prereq"]),
            _item("prereq", position=2),
        ]
        text = "\n".join(
            self._lines(
                oc_runipd.run_order_rationale(queue, selectors=["depend", "prereq"])
            )
        )
        self.assertIn("WARNING", text)
        self.assertIn("typed order", text)
        self.assertIn("execution order", text)
        self.assertIn("executed:prereq", text)
        self.assertIn("declared dependency", text)

    def test_expanded_selection_message_never_claims_a_typed_order(self):
        queue = [
            _item("depend", position=1, deps=["executed:prereq"]),
            _item("prereq", position=2),
        ]
        text = "\n".join(
            self._lines(oc_runipd.run_order_rationale(queue, selectors=["all"]))
        )
        self.assertIn("requested order", text)
        self.assertNotIn("typed order", text)
        self.assertIn("expanded from selector", text)

    def test_formatter_is_pure_and_imports_no_runner(self):
        src = Path(render_stream.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        offenders = [m for m in imported if "runipd" in m]
        self.assertEqual(
            offenders, [], f"the renderer must not import a runner: {offenders}"
        )
        self.assertEqual(
            inspect.getmodule(render_stream.format_run_order_announcement).__name__,
            "agent_workflows.render_stream",
        )

    def test_exactly_one_definition_in_the_package(self):
        pkg = Path(render_stream.__file__).parent
        definers = sorted(
            p.name
            for p in pkg.glob("*.py")
            if "def format_run_order_announcement(" in p.read_text(encoding="utf-8")
        )
        self.assertEqual(definers, ["render_stream.py"])

    def test_both_drivers_bind_the_same_formatter_object(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                self.assertIs(
                    mod.format_run_order_announcement,
                    render_stream.format_run_order_announcement,
                )


class PreviewShowsExecutionOrderTests(unittest.TestCase):
    """E-05/E-07: `--prepare-only` (and `status`) must preview EXECUTION order, on BOTH drivers."""

    def _state(self, run_dir: Path) -> dict:
        """A queue whose DECLARED EDGE makes execution order differ from position order."""
        queue = [
            _item("depend", setid="demo", position=1, deps=["executed:prereq"]),
            _item("prereq", setid="demo", position=2, order=9),
        ]
        state = {
            "run_id": "run-preview-test",
            "repo": str(run_dir),
            "created_at": "2026-09-04T10:00:00+00:00",
            "updated_at": "2026-09-04T10:00:00+00:00",
            "queue": queue,
            "run_order": oc_runipd.run_order_rationale(
                queue, selectors=["depend", "prereq"]
            ),
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return state

    def _rows(self, output: str) -> list[str]:
        """The id6 of each table row, in the order the table lists them."""
        found = []
        for line in output.splitlines():
            for id6 in ("depend", "prereq"):
                if f" {id6} " in render_stream._strip_ansi(line):
                    found.append(id6)
                    break
        return found

    def test_table_lists_rows_in_execution_order(self):
        with tempfile.TemporaryDirectory() as t:
            run_dir = Path(t)
            state = self._state(run_dir)
            out = render_stream.render_run_summary_table(
                state, run_dir, pal=render_stream.Palette(False)
            )
            self.assertEqual(
                self._rows(out),
                ["prereq", "depend"],
                "the table must list the order the run will EXECUTE in, not frozen identity order",
            )
            self.assertIn("Run", out, "the execution-sequence column must be labelled")
            self.assertIn(
                "Pos", out, "the frozen identity column must stay, and be labelled"
            )

    def test_table_falls_back_to_stored_order_without_a_recorded_run_order(self):
        """A run directory frozen before this change has no `run_order`; it must still render."""
        with tempfile.TemporaryDirectory() as t:
            run_dir = Path(t)
            state = self._state(run_dir)
            state.pop("run_order")
            out = render_stream.render_run_summary_table(
                state, run_dir, pal=render_stream.Palette(False)
            )
            self.assertEqual(self._rows(out), ["depend", "prereq"])

    def test_both_drivers_print_status_in_execution_order(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    run_dir = Path(t)
                    self._state(run_dir)
                    buf = io.StringIO()
                    import contextlib

                    with contextlib.redirect_stdout(buf):
                        mod.print_status(run_dir)
                    self.assertEqual(self._rows(buf.getvalue()), ["prereq", "depend"])


def _plan_text(id6: str, *, setid: str, order: int, deps: str | None = None) -> str:
    lines = [
        f"# IPD: {id6}",
        "",
        "- Date: 2026-09-04",
        "- Kind: child",
        "- Status: approved",
        f"- Set: {setid} (the {setid} set)",
        f"- Order: {order}",
        f"- Id: {id6}",
    ]
    if deps is not None:
        lines.append(f"- Item-Dependencies: {deps}")
    lines += ["", "## Goal", "", "Demo.", ""]
    return "\n".join(lines)


def _start_args(repo: Path, selectors: list[str]) -> argparse.Namespace:
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


class QueueBuildAnnouncementTests(unittest.TestCase):
    """E-04/E-07: the announcement happens at queue build, is printed, and is DURABLE."""

    def _repo(self, temp: Path) -> Path:
        repo = temp / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        return repo

    def _write(
        self, repo: Path, id6: str, setid: str, order: int, deps: str | None = None
    ) -> None:
        pending = repo / ".aw" / "records" / "plans" / "pending"
        (pending / f"20260904-{setid}-{order:02d}-{id6}-demo.ipd.md").write_text(
            _plan_text(id6, setid=setid, order=order, deps=deps), encoding="utf-8"
        )

    def _run(self, mod, repo: Path, selectors: list[str]) -> tuple[Path, str]:
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_dir = mod.initialize_run(_start_args(repo, selectors))
        return run_dir, buf.getvalue()

    def test_unreordered_run_announces_and_records_its_order(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t))
                    self._write(repo, "m73aet", "runtrail", 1)
                    self._write(repo, "6lu3rq", "runmixed", 1)
                    run_dir, out = self._run(mod, repo, ["m73aet", "6lu3rq"])
                    self.assertIn("Run order", out)
                    self.assertIn("01 m73aet", out)
                    self.assertNotIn("WARNING", out)
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        state["run_order"]["executed"], ["m73aet", "6lu3rq"]
                    )
                    self.assertEqual(
                        [it["id6"] for it in state["queue"]],
                        ["m73aet", "6lu3rq"],
                        "positions stay frozen in request order",
                    )
                    events = [
                        json.loads(ln)
                        for ln in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if ln.strip()
                    ]
                    order_events = [e for e in events if e.get("event") == "run-order"]
                    self.assertEqual(len(order_events), 1)
                    self.assertEqual(order_events[0]["executed"], ["m73aet", "6lu3rq"])

    def test_reordered_run_warns_and_records_the_cause(self):
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as t:
                    repo = self._repo(Path(t))
                    self._write(repo, "depend", "aaaset", 1, deps="executed:prereq")
                    self._write(repo, "prereq", "zzzset", 1)
                    run_dir, out = self._run(mod, repo, ["depend", "prereq"])
                    self.assertIn("WARNING", out)
                    self.assertIn("executed:prereq", out)
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        state["run_order"]["executed"], ["prereq", "depend"]
                    )
                    self.assertIn(
                        "declared dependency", state["run_order"]["causes"]["prereq"]
                    )
                    events = [
                        json.loads(ln)
                        for ln in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if ln.strip()
                    ]
                    order_events = [e for e in events if e.get("event") == "run-order"]
                    self.assertEqual(len(order_events), 1)
                    self.assertTrue(order_events[0]["reordered"])


if __name__ == "__main__":
    unittest.main()
