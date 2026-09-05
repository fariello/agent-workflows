#!/usr/bin/env python3
"""R2 closed loop and idempotency (spec `7ckptx` A3, A4, A5, A5b, A18; plan `cqx5v7` V-03, V-04, V-06).

PARAMETERIZED OVER BOTH DRIVERS, never copied, for the reason spec 0.3 gives: a containment rule that
lands in one host and not the other is a defect, and a copied test drifts.

WHY THIS FILE MATTERS MORE THAN IT LOOKS. Spec R2.1 records the failure mode it prevents: with
lane-relative prompt paths (R1) and NO collection, the worker writes its outcome inside the lane,
`reconcile_disposition` reads `<run_dir>/outcomes/<NN>-<id6>.json`, finds nothing, and scores the turn
from the empty-outcome fallback; that disposition sits outside the set that gates verification and
self-finalize, so a fully successful turn silently never finalizes. That is WORSE than the
contradiction R1 removes, which is why the two must ship together.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from agent_workflows import agy_runipd, lane_containment, oc_runipd

DRIVERS = pytest.mark.parametrize(
    "driver", (oc_runipd, agy_runipd), ids=("oc_runipd", "agy_runipd")
)

RUN_ID = "run-20260901T000000Z-1"


def _item(**over) -> dict:
    item = {
        "id6": "aaaaaa",
        "setid": "lanectn",
        "position": 1,
        "configured_file": "x.ipd.md",
        "attempts": [{"number": 1}],
        "action": "execute",
    }
    item.update(over)
    return item


class Fixture:
    """One lane + one run directory, with helpers to act as the WORKER writing submissions."""

    def __init__(self, tmp_path: Path, *, id6: str = "aaaaaa", position: int = 1):
        self.repo = tmp_path / "repo"
        self.lane = self.repo / ".aw" / "worktrees" / id6
        self.lane.mkdir(parents=True, exist_ok=True)
        self.run_dir = self.repo / ".aw" / "records" / "runs" / RUN_ID
        (self.run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (self.run_dir / lane_containment.DECISIONS_NAME).write_text(
            f"# Decisions and Questions for {RUN_ID}\n\n", encoding="utf-8"
        )
        self.plan = self.lane / "x.ipd.md"
        self.plan.write_text("# IPD: fixture\n", encoding="utf-8")
        self.item = _item(id6=id6, position=position)
        self.state = {"run_id": RUN_ID, "repo": str(self.repo), "options": {}}

    def paths(self, attempt: int = 1):
        return lane_containment.project_worker_paths(
            item=self.item,
            run_id=RUN_ID,
            run_dir=self.run_dir,
            plan_path=self.plan,
            lane_root=self.lane,
        )._replace()

    def worker_writes_outcome(
        self, disposition: str = "executed", attempt: int = 1
    ) -> Path:
        """Act as an OBEDIENT worker: write the outcome at the LANE-RELATIVE path it was given."""
        root = lane_containment.lane_submission_root(
            self.lane, RUN_ID, self.item, attempt
        )
        target = root / "outcomes" / f"{lane_containment.item_slug(self.item)}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": RUN_ID,
                    "position": self.item["position"],
                    "id6": self.item["id6"],
                    "setid": self.item["setid"],
                    "disposition": disposition,
                    "summary": "worker wrote this inside its lane",
                    "pushed": False,
                }
            ),
            encoding="utf-8",
        )
        return target

    def worker_writes_decisions(self, text: str, attempt: int = 1) -> Path:
        root = lane_containment.lane_submission_root(
            self.lane, RUN_ID, self.item, attempt
        )
        root.mkdir(parents=True, exist_ok=True)
        target = root / lane_containment.DECISIONS_NAME
        target.write_text(text, encoding="utf-8")
        return target

    def collect(self, attempt: int = 1):
        return lane_containment.collect_lane_submissions(
            run_dir=self.run_dir,
            item=self.item,
            run_id=RUN_ID,
            lane_root=self.lane,
            plan_path=self.plan,
            attempt=attempt,
        )

    @property
    def driver_outcome(self) -> Path:
        return (
            self.run_dir / "outcomes" / f"{lane_containment.item_slug(self.item)}.json"
        )

    @property
    def register(self) -> Path:
        return self.run_dir / lane_containment.DECISIONS_NAME


# ---- A3 / R2.1: the loop actually closes -----------------------------------------------------------


@DRIVERS
def test_collected_lane_outcome_yields_the_workers_disposition(driver, tmp_path):
    """A3, R2.1. The assertion is on `reconcile_disposition`'s RESULT, not on a file existing.

    `substantially-complete` is the CORRECT expectation for a worker-claimed `executed` while the plan
    is still in `pending/`: `reconcile_disposition` deliberately downgrades a self-claimed `executed`,
    and the self-finalize gate triggers on `{executed, substantially-complete}`. The empty-outcome
    fallback would be `partial`, which is OUTSIDE that gate; that difference is the whole defect.
    """
    fx = Fixture(tmp_path)
    fx.worker_writes_outcome("executed")
    assert not fx.driver_outcome.exists(), "precondition: nothing collected yet"

    fx.collect()

    assert fx.driver_outcome.is_file()
    disposition, outcome = driver.reconcile_disposition(fx.repo, fx.item, fx.run_dir, 0)
    assert (
        disposition == "substantially-complete"
    ), f"{driver.__name__} scored a collected successful turn as {disposition!r}"
    assert outcome is not None and outcome["disposition"] == "executed"


@DRIVERS
def test_without_collection_the_disposition_degrades(driver, tmp_path):
    """THE SABOTAGE (plan rule 2): with collection SKIPPED, the same turn degrades to the fallback.

    This is what makes the test above meaningful. If the assertion passed with and without the
    collection step, it would be proving nothing about collection.
    """
    fx = Fixture(tmp_path)
    fx.worker_writes_outcome("executed")
    # Deliberately do NOT collect.
    disposition, outcome = driver.reconcile_disposition(fx.repo, fx.item, fx.run_dir, 0)
    assert disposition == "partial", (
        "the uncollected case must reconcile to the empty-outcome fallback; got "
        f"{disposition!r}"
    )
    assert outcome is None
    assert (
        disposition not in ("executed", "substantially-complete")
    ), "the fallback must sit OUTSIDE the gating set, which is why the turn would never finalize"


@DRIVERS
def test_a_turn_that_submitted_nothing_reconciles_without_raising(driver, tmp_path):
    """A5, R2.4. Absence is a legitimate observation."""
    fx = Fixture(tmp_path)
    receipt = fx.collect()  # the worker wrote nothing at all
    assert receipt is not None
    assert receipt["collected"] == []
    assert all(s["result"] == "absent" for s in receipt["submissions"])
    disposition, outcome = driver.reconcile_disposition(fx.repo, fx.item, fx.run_dir, 0)
    assert disposition == "partial"
    assert outcome is None


@DRIVERS
def test_a_non_isolated_turn_collects_nothing_and_writes_no_receipt(driver, tmp_path):
    """R1.3-adjacent: the non-isolated path must be untouched by this feature."""
    fx = Fixture(tmp_path)
    assert (
        lane_containment.collect_lane_submissions(
            run_dir=fx.run_dir,
            item=fx.item,
            run_id=RUN_ID,
            lane_root=None,
            plan_path=fx.plan,
            attempt=1,
        )
        is None
    )
    assert not (fx.run_dir / "collections").exists()


# ---- A18 / R2.2: copy, never move -----------------------------------------------------------------


@DRIVERS
def test_collection_copies_and_the_lane_keeps_its_evidence(driver, tmp_path):
    """A18, R2.2. The lane must retain its own copy so R5.5 retention has something to classify."""
    fx = Fixture(tmp_path)
    lane_side = fx.worker_writes_outcome("executed")
    fx.collect()
    assert lane_side.is_file(), "collection MOVED the submission; R2.2 requires a copy"
    assert (
        lane_side.read_bytes() == fx.driver_outcome.read_bytes()
    ), "the collected copy differs from the lane's"


# ---- the ordering claim, which is a source-level property -----------------------------------------


@DRIVERS
def test_collection_is_called_before_reconcile_disposition(driver):
    """R2.1's "BEFORE the disposition is computed", asserted STRUCTURALLY inside `execute_item`.

    By AST rather than by line-number arithmetic over the whole file: find the `execute_item` body,
    then compare the source offsets of the `collect_lane_submissions` call and the
    `reconcile_disposition` call that assigns the turn's disposition. A test that merely asserted both
    calls exist would pass with the order reversed, which is the exact defect.
    """
    import ast

    source = Path(str(driver.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "execute_item"
    )
    collect_lines = [
        n.lineno
        for n in ast.walk(func)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "collect_lane_submissions"
    ]
    assert (
        collect_lines
    ), f"{driver.__name__}.execute_item never collects lane submissions"
    # The disposition-computing call is the one whose result is unpacked into a 2-tuple assignment
    # named `disposition`.
    reconcile_lines = [
        n.lineno
        for n in ast.walk(func)
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Tuple)
        and any(
            isinstance(e, ast.Name) and e.id == "disposition" for e in n.targets[0].elts
        )
    ]
    assert reconcile_lines, "could not locate the disposition assignment"
    assert min(collect_lines) < max(reconcile_lines), (
        f"{driver.__name__} collects AFTER computing the disposition (collect at "
        f"{collect_lines}, disposition at {reconcile_lines})"
    )


# ---- A4 / R2.3: idempotency of the run-wide register ------------------------------------------------


@DRIVERS
def test_running_the_same_attempts_collection_twice_is_idempotent(driver, tmp_path):
    """A4, R2.3. The defect only appears on the SECOND run, so a single-run test cannot see it."""
    fx = Fixture(tmp_path)
    fx.worker_writes_outcome("executed")
    fx.worker_writes_decisions(
        "## DECISION 01-aaaaaa-D1\n- Question: which mechanism?\n- Selected approach: attempt-keyed\n"
    )

    fx.collect()
    once = fx.register.read_text(encoding="utf-8")
    fx.collect()
    twice = fx.register.read_text(encoding="utf-8")

    assert once == twice, "a second collection of the same attempt changed the register"
    assert (
        twice.count("## DECISION 01-aaaaaa-D1") == 1
    ), "the lane's contribution appears more than once after re-collection"
    # The run's own preamble is untouched.
    assert twice.startswith(f"# Decisions and Questions for {RUN_ID}")


@DRIVERS
def test_a_siblings_contribution_survives_both_runs(driver, tmp_path):
    """A4's second half: idempotency must not be implemented by truncating the shared register."""
    fx = Fixture(tmp_path)
    sibling = Fixture(tmp_path, id6="bbbbbb", position=2)
    # Same run directory for both lanes: the register is RUN-WIDE.
    sibling.run_dir = fx.run_dir
    sibling.item = _item(id6="bbbbbb", position=2)

    fx.worker_writes_decisions("## DECISION 01-aaaaaa-D1\n- Question: mine\n")
    sibling.worker_writes_decisions("## DECISION 02-bbbbbb-D1\n- Question: theirs\n")
    fx.collect()
    sibling.collect()
    fx.collect()  # the retry

    text = fx.register.read_text(encoding="utf-8")
    assert text.count("## DECISION 01-aaaaaa-D1") == 1
    assert (
        text.count("## DECISION 02-bbbbbb-D1") == 1
    ), "the sibling lane's contribution was removed by the retry"


def test_the_chosen_mechanism_is_recorded_in_the_code():
    """Plan E-04 requires the CHOSEN mechanism be stated in a code comment, so a reader is not guessing."""
    src = Path(str(lane_containment.__file__)).read_text(encoding="utf-8")
    assert "MECHANISM CHOSEN: ATTEMPT-KEYED DEDUP" in src


def test_merge_is_pure_and_replaces_rather_than_appends():
    """The unit-level invariant behind R2.3, independent of any filesystem."""
    base = "# header\n\n"
    once = lane_containment.merge_decisions_block(base, "k1", "BODY")
    twice = lane_containment.merge_decisions_block(once, "k1", "BODY")
    assert once == twice
    with_sibling = lane_containment.merge_decisions_block(once, "k2", "OTHER")
    again = lane_containment.merge_decisions_block(with_sibling, "k1", "BODY")
    assert "OTHER" in again and again.count("BODY") == 1
    assert again.startswith("# header")


# ---- A5b / R2.5: the receipt, in all four states ---------------------------------------------------


@DRIVERS
def test_receipt_distinguishes_all_four_states(driver, tmp_path):
    """A5b, R2.5. Distinguishable WITHOUT inspecting run-directory CONTENTS.

    The four states and how each is read from the RECEIPT alone:
      * COLLECTED      -> receipt exists, status `complete`, that submission `result == "collected"`,
                          with its `source_sha256` and `destination`.
      * UNCOLLECTED    -> NO receipt at all. Absence means not collected and must never be inferred
                          from a file existing somewhere.
      * INTERRUPTED    -> receipt exists with status `in-progress` (written before the first copy).
      * REPEATED       -> `collection_runs` > 1.
    """
    fx = Fixture(tmp_path)

    # UNCOLLECTED: no receipt.
    assert lane_containment.read_collection_receipt(fx.run_dir, fx.item, 1) is None

    fx.worker_writes_outcome("executed")
    fx.worker_writes_decisions("## DECISION 01-aaaaaa-D1\n- Question: x\n")
    first = fx.collect()

    # COLLECTED.
    assert first is not None and first["status"] == lane_containment.RECEIPT_COMPLETE
    by_name = {s["name"]: s for s in first["submissions"]}
    assert by_name["outcome"]["result"] == "collected"
    assert (
        by_name["outcome"]["source_sha256"]
        and len(by_name["outcome"]["source_sha256"]) == 64
    )
    assert by_name["outcome"]["destination"] == str(fx.driver_outcome)
    assert by_name["decisions"]["result"] == "collected"
    assert by_name["report"]["result"] == "absent"  # the worker wrote no report
    assert first["collection_runs"] == 1

    # REPEATED.
    second = fx.collect()
    assert second is not None and second["collection_runs"] == 2

    # INTERRUPTED mid-collection: the in-progress receipt is on disk before any copy happens.
    other = Fixture(tmp_path / "other")
    other.worker_writes_outcome("executed")
    boom = RuntimeError("interrupted mid-collection")
    real_copy = lane_containment._copy_file

    def exploding_copy(source, destination):
        raise boom

    lane_containment._copy_file = exploding_copy  # type: ignore[assignment]
    try:
        with pytest.raises(RuntimeError):
            other.collect()
    finally:
        lane_containment._copy_file = real_copy  # type: ignore[assignment]
    interrupted = lane_containment.read_collection_receipt(other.run_dir, other.item, 1)
    assert interrupted is not None
    assert (
        interrupted["status"] == lane_containment.RECEIPT_IN_PROGRESS
    ), "an interruption mid-collection must be distinguishable from a lane that wrote nothing"


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root ignores the directory mode this test uses to provoke a real write failure",
)
@DRIVERS
def test_a_failed_collection_is_recorded_as_failed_not_omitted(driver, tmp_path):
    """A5b's sabotage half: a silently omitted failure is indistinguishable from writing nothing."""
    fx = Fixture(tmp_path)
    fx.worker_writes_outcome("executed")
    # Make the DESTINATION directory unwritable so the copy genuinely fails.
    dest_dir = fx.run_dir / "outcomes"
    original_mode = stat.S_IMODE(dest_dir.stat().st_mode)
    os.chmod(dest_dir, 0o500)
    try:
        receipt = fx.collect()
    finally:
        os.chmod(dest_dir, original_mode)

    assert receipt is not None
    by_name = {s["name"]: s for s in receipt["submissions"]}
    assert (
        by_name["outcome"]["result"] == "failed"
    ), "a failed collection must be recorded as failed, never omitted"
    assert by_name["outcome"]["reason"], "a failure must carry its reason"
    assert receipt["failed"] == ["outcome"]
    assert receipt["status"] == lane_containment.RECEIPT_COMPLETE
    # And the consumer can tell this apart from "the lane wrote nothing" (which is `absent`).
    assert by_name["outcome"]["result"] != "absent"


@DRIVERS
def test_the_receipt_is_attempt_keyed_so_a_retry_does_not_overwrite_history(
    driver, tmp_path
):
    """R2.5 + R2.3: attempt 2's record must not destroy attempt 1's."""
    fx = Fixture(tmp_path)
    fx.worker_writes_outcome("partial", attempt=1)
    fx.collect(attempt=1)
    fx.item["attempts"] = [{"number": 1}, {"number": 2}]
    fx.worker_writes_outcome("executed", attempt=2)
    fx.collect(attempt=2)

    first = lane_containment.read_collection_receipt(fx.run_dir, fx.item, 1)
    second = lane_containment.read_collection_receipt(fx.run_dir, fx.item, 2)
    assert first is not None and second is not None
    assert first["attempt"] == 1 and second["attempt"] == 2
    assert (
        first["lane_submission_root"] != second["lane_submission_root"]
    ), "attempt 2 read attempt 1's submission directory; a retry would re-report the old outcome"
    # The driver-side outcome now holds attempt 2's claim.
    assert json.loads(fx.driver_outcome.read_text())["disposition"] == "executed"


# ---- twin parity, the thing a copied test cannot prove --------------------------------------------


def test_both_drivers_reach_the_same_shared_functions():
    """CID-3: the SAME objects, not merely equivalent behavior."""
    assert oc_runipd.lane_containment is agy_runipd.lane_containment
    assert oc_runipd.build_isolation_notice(
        Path("/tmp/x")
    ) == agy_runipd.build_isolation_notice(Path("/tmp/x"))
    assert oc_runipd.build_isolation_notice(None) == ""
    assert agy_runipd.build_isolation_notice(None) == ""


def test_these_tests_are_parameterized_rather_than_duplicated():
    """The plan's V-05 asks for evidence of PARAMETERIZATION, not two similar functions.

    Asserted mechanically so it cannot rot: every test taking a `driver` argument in this module and in
    the R1 module must be reached through the shared `DRIVERS` parametrize mark, and no function name
    may be suffixed with a host name (the shape a copy-paste takes).
    """
    import ast

    for module_name in ("test_lane_submission_collection", "test_lane_prompt_purity"):
        path = Path(__file__).with_name(module_name + ".py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith(
                "test_"
            ):
                continue
            takes_driver = any(a.arg == "driver" for a in node.args.args)
            marked = any(
                isinstance(d, ast.Name) and d.id == "DRIVERS"
                for d in node.decorator_list
            )
            assert (
                takes_driver == marked
            ), f"{module_name}.{node.name} must take `driver` iff it carries @DRIVERS"
            assert not node.name.endswith(
                ("_oc", "_agy", "_opencode", "_antigravity")
            ), f"{module_name}.{node.name} looks host-specific; parameterize instead of copying"
