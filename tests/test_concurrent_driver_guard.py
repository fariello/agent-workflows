#!/usr/bin/env python3

"""THE REGRESSION SUITE for the repository-scoped concurrent-driver guard (runconcur-01, `vddpml`).

WHAT THIS FILE EXISTS TO FALSIFY. On 2026-09-22 two unattended drivers ran in ONE working tree for
hours, each integrating verified lanes to `main` with nothing arbitrating between them. The measured
cost was paid twice in one session: a peer advanced `main` by five commits (landing `fduoj4`) during a
completed full-suite validation, forcing a rebuild; after the rebuild it landed `vhbvwz` and a prepared
`--ff-only` publish refused, forcing a third. The existing `driver.lock` could not help, because it
lives in each RUN's own directory, so two runs hold two different locks and never contend.

THE HARM IS WASTED VALIDATION AND A REFUSED PUBLISH, NOT CORRUPTION, and that matters for what these
tests assert. A stale merge CANNOT silently revert a peer's `pending/` -> `executed/` transition: an
editing stale side CONFLICTS loudly and a non-editing one leaves the transition intact. So nothing here
tests for a silent-revert that git demonstrably prevents; what is tested is that the publish is
serialized, that the serialization cannot hang or wedge, and that a peer is VISIBLE.

FIVE WAYS A PLAUSIBLE IMPLEMENTATION WOULD HAVE BEEN WRONG, each with a test below:

 1. THE LANE-WORKTREE BLIND SPOT (F-7). An execute item runs in a lane worktree by DEFAULT, and a lane
    resolves `state_root` to its OWN nonexistent runs root, so the obvious peer query
    (`run_viewer.discover_run_dirs(Path("."))`) returns ZERO from exactly the place the guard matters
    most. Measured at authoring time: 0 from the lane versus 246 from the resolved root. Pinned by
    `LaneWorktreeResolutionTests`.
 2. COLLAPSING UNKNOWN INTO NONE. `platform_lock.probe_free` is three-valued on purpose; reporting an
    unprobeable lock as "no peer" would assert a fact the probe refused to give. Pinned by
    `PeerQueryTests`.
 3. WEDGING THE REPOSITORY ON A CRASHED RUN. A leftover lock file whose holder is gone must read as NO
    peer, or one crash blocks every future integration forever. Pinned by `PeerQueryTests`.
 4. AN UNBOUNDED, SILENT WAIT. `platform_lock` warns that "an accidental block would HANG a driver
    rather than fail it", and an integration runs a full suite, so a silent block is indistinguishable
    from a hang. The wait must be bounded, must report, and on expiry must DEFER (a deferrable kind with
    the lane preserved) rather than FAIL the lane, because a lane failed on a lock timeout discards the
    completed validation this whole mechanism exists to protect. Pinned by `BoundedWaitTests`.
 5. A ONE-SIDED GUARD. A per-host copy would leave `aw agy run` able to race `aw oc run`. Pinned
    structurally by `SharedImplementationTests`.

THE E-05 ASSERTION FORM IS OBJECT IDENTITY, AND THAT CHOICE IS MEASURED RATHER THAN ASSUMED. Measured
at authoring: `oc_runipd.integrate_lane_branch is agy_runipd.integrate_lane_branch` is FALSE, because
each host binds a thin WRAPPER supplying `host_label`/`action_kind`; by contrast the re-export
`state_root` IS identical across both hosts and `runner_shared`. Everything this plan ships is
host-NEUTRAL (a lock path, a peer query, a serializer - none of them carry a host label), so it is bound
as a RE-EXPORT and identity is the correct, stronger assertion. An identity test against a wrapper would
fail a correct implementation, which is worse than no test; that is why the form is stated here.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    cli,
    oc_runipd,
    platform_lock,
    run_viewer,
    runner_shared,
)
from tests.support import init_repo

#: The two hosts, as a table column. Every property here is about the two AGREEING, so a per-host test
#: class would let a property hold on one host and not the other while both classes stayed green.
BOTH = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

#: The symbols this plan ships. Bound as RE-EXPORTS in both hosts, so object identity holds; see the
#: module docstring for why that form and not delegation.
SHARED_SYMBOLS = (
    "peer_drivers",
    "format_peer_driver_report",
    "integration_lock",
    "integration_lock_path",
    "integrate_under_repository_lock",
    "runs_repo_root",
)


def _run_dir(root: Path, name: str, *, selectors=("abc123",), pid=None) -> Path:
    """A minimal run directory with a `state.json` and (optionally) a `driver.lock` file."""

    d = root / ".aw" / "records" / "runs" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.json").write_text(
        json.dumps({"run_id": name, "selectors": list(selectors), "queue": []}),
        encoding="utf-8",
    )
    if pid is not None:
        (d / "driver.lock").write_text(f"pid={pid} started=2026-09-22T00:00:00+00:00\n")
    return d


class PeerQueryTests(unittest.TestCase):
    """E-01 / V-01: the read-only peer query, including the two answers it must NOT collapse."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        (self.repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_no_run_at_all_reports_no_peer(self):
        self.assertEqual(runner_shared.peer_drivers(self.repo), [])

    def test_a_run_with_NO_lock_file_is_not_a_peer(self):
        _run_dir(self.repo, "run-a")
        self.assertEqual(runner_shared.peer_drivers(self.repo), [])

    def test_a_STALE_lock_whose_holder_is_gone_reports_NO_peer(self):
        """A crashed run must not block the repository forever (E-06's dead-holder case).

        THE OS DROPS AN `flock` WHEN ITS HOLDER DIES, so the leftover FILE is all that remains and
        `probe_free` correctly reports it free. This test pins that the query believes the probe rather
        than the file's existence; the opposite reading would make one crash permanently unpublishable.
        """

        _run_dir(self.repo, "run-dead", pid=999999)
        self.assertEqual(runner_shared.peer_drivers(self.repo), [])

    def test_a_LIVE_holder_is_reported_with_its_identity(self):
        """The holder's identity is reported, and the `pid=` is written the way a REAL driver writes it.

        THE ORDERING IS LOAD-BEARING IN THIS TEST, and getting it wrong cost a false failure while
        authoring. `filelock` opens with `O_CREAT | O_TRUNC`, so a SUCCESSFUL acquire BLANKS the file
        (measured directly: `pid=4242 started=x` became `''`). `runner_shared.run_lock` therefore writes
        the `pid=` line AFTER acquiring, through a stream `dup`ed from the LOCKED descriptor. A fixture
        that writes the line first and then acquires is testing a state no driver is ever in.
        """

        run = _run_dir(self.repo, "run-live", selectors=("setid-x", "abc123"))
        with platform_lock.acquire(run / "driver.lock") as handle:
            stream = handle.dup_stream()
            stream.seek(0)
            stream.truncate()
            stream.write("pid=4242 started=2026-09-22T00:00:00+00:00\n")
            stream.flush()
            peers = runner_shared.peer_drivers(self.repo)
            stream.close()
        self.assertEqual([p.run_id for p in peers], ["run-live"])
        self.assertEqual(peers[0].state, runner_shared.PEER_LIVE)
        self.assertEqual(peers[0].pid, 4242)
        self.assertEqual(peers[0].selectors, ("setid-x", "abc123"))

    def test_an_UNPROBEABLE_lock_is_UNKNOWN_and_never_NONE(self):
        """The three-valued probe is preserved end to end.

        Simulated by making the probe UNANSWERABLE (`None`), which is what a non-POSIX host returns. A
        run reported `none` here would assert that nothing holds the lock, which the probe explicitly
        refused to say.
        """

        _run_dir(self.repo, "run-unknown", pid=7)
        with mock.patch.object(platform_lock, "probe_free", return_value=None):
            peers = runner_shared.peer_drivers(self.repo)
        self.assertEqual([p.state for p in peers], [runner_shared.PEER_UNKNOWN])

    def test_the_query_MUTATES_NOTHING(self):
        """Read-only, asserted by BYTES and mtime rather than by inspection.

        A probe through `filelock` would open with `O_CREAT | O_TRUNC` and blank the live driver's own
        `pid=` record; this asserts the query does not.
        """

        run = _run_dir(self.repo, "run-live", pid=4242)
        lock = run / "driver.lock"
        before_bytes = lock.read_bytes()
        before_stat = lock.stat()
        runner_shared.peer_drivers(self.repo)
        self.assertEqual(lock.read_bytes(), before_bytes)
        self.assertEqual(lock.stat().st_mtime_ns, before_stat.st_mtime_ns)
        self.assertEqual(lock.stat().st_size, before_stat.st_size)

    def test_a_run_EXCLUDES_ITSELF(self):
        run = _run_dir(self.repo, "run-self", pid=1)
        with platform_lock.held(run / "driver.lock"):
            self.assertEqual(
                runner_shared.peer_drivers(self.repo, exclude_run_dir=run), []
            )
            self.assertEqual(len(runner_shared.peer_drivers(self.repo)), 1)


class PeerReportTests(unittest.TestCase):
    """E-02 / V-02: UNKNOWN must RENDER differently from NONE, not merely be modelled differently."""

    def _peer(self, state):
        return runner_shared.PeerDriver(
            run_id="run-x",
            run_dir=Path("/nope"),
            state=state,
            pid=11,
            selectors=("setid",),
        )

    def test_no_peer_prints_NOTHING(self):
        self.assertEqual(runner_shared.format_peer_driver_report([]), [])

    def test_a_live_peer_names_its_run_pid_and_selectors(self):
        lines = runner_shared.format_peer_driver_report(
            [self._peer(runner_shared.PEER_LIVE)]
        )
        joined = "\n".join(lines)
        self.assertIn("run-x", joined)
        self.assertIn("pid 11", joined)
        self.assertIn("setid", joined)
        self.assertIn("LIVE", joined)

    def test_an_unknown_peer_renders_DISTINCTLY_from_both_none_and_live(self):
        unknown = "\n".join(
            runner_shared.format_peer_driver_report(
                [self._peer(runner_shared.PEER_UNKNOWN)]
            )
        )
        live = "\n".join(
            runner_shared.format_peer_driver_report(
                [self._peer(runner_shared.PEER_LIVE)]
            )
        )
        self.assertIn("UNKNOWN", unknown)
        self.assertNotIn("UNKNOWN", live)
        self.assertNotEqual(unknown, live)
        self.assertNotEqual(unknown, "")
        # It must not overclaim: an unprobeable lock is not evidence of absence.
        self.assertIn("NOT proof", unknown)


class LaneWorktreeResolutionTests(unittest.TestCase):
    """F-7 / V-01: the blind spot a naive `discover_run_dirs` would have left in every lane.

    THE MEASUREMENT THIS PINS, taken in a real lane worktree at authoring time:
    `run_viewer.discover_run_dirs(Path("."))` returned 0 while the RESOLVED root returned 246. Since
    every execute item runs in a lane by default, a query built on the bare call would report NO PEER
    from precisely where the guard matters.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.main = init_repo(Path(self._tmp.name) / "main")
        (self.main / "f.txt").write_text("x\n")
        subprocess.run(["git", "add", "f.txt"], cwd=self.main, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "init"],
            cwd=self.main,
            check=True,
            capture_output=True,
        )
        (self.main / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
        self.lane = self.main / ".aw" / "worktrees" / "lane1"
        subprocess.run(
            ["git", "worktree", "add", "-q", str(self.lane), "-b", "lane1"],
            cwd=self.main,
            check=True,
            capture_output=True,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_a_bare_discover_run_dirs_finds_NOTHING_from_the_lane(self):
        """The DEFECT, asserted, so the resolver requirement is not mistaken for decoration.

        If this ever starts finding runs, the resolver below became unnecessary and this file should say
        so rather than keeping a requirement nothing needs.
        """

        _run_dir(self.main, "run-live", pid=1)
        self.assertEqual(run_viewer.discover_run_dirs(self.lane), [])
        self.assertEqual(len(run_viewer.discover_run_dirs(self.main)), 1)

    def test_the_resolver_makes_the_lane_and_the_main_checkout_AGREE(self):
        self.assertEqual(
            runner_shared.runs_repo_root(self.lane).resolve(),
            self.main.resolve(),
        )

    def test_the_peer_query_finds_the_SAME_peer_from_the_lane_as_from_main(self):
        run = _run_dir(self.main, "run-live", pid=1)
        with platform_lock.held(run / "driver.lock"):
            from_main = [p.run_id for p in runner_shared.peer_drivers(self.main)]
            from_lane = [p.run_id for p in runner_shared.peer_drivers(self.lane)]
        self.assertEqual(from_main, ["run-live"])
        self.assertEqual(from_lane, from_main)

    def test_the_LOCK_PATH_is_identical_from_the_lane_and_from_main(self):
        """Two paths would mean the two mechanisms contend over nothing (F-4's defect, relocated)."""

        self.assertEqual(
            runner_shared.integration_lock_path(self.lane),
            runner_shared.integration_lock_path(self.main),
        )


def _hold_then_signal(lock_dir: str, held_evt, release_evt) -> None:
    """Child process: hold the repository integration lock, then release on the parent's signal."""

    with runner_shared.integration_lock(
        Path(lock_dir), holder_label="child"
    ) as outcome:
        held_evt.set()
        assert outcome.acquired
        release_evt.wait(30)


class RealTwoProcessContentionTests(unittest.TestCase):
    """E-03 / V-03: a REAL second process, because a mocked lock cannot prove mutual exclusion."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        (self.repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED(self):
        ctx = multiprocessing.get_context("fork")
        held, release = ctx.Event(), ctx.Event()
        child = ctx.Process(
            target=_hold_then_signal, args=(str(self.repo), held, release)
        )
        child.start()
        try:
            self.assertTrue(held.wait(30), "the child never acquired the lock")
            # MUTUAL EXCLUSION, observed rather than assumed.
            self.assertIs(
                platform_lock.probe_free(
                    runner_shared.integration_lock_path(self.repo)
                ),
                False,
            )
            # THE HOLDER IS NAMED, which is what makes a wait actionable instead of opaque.
            self.assertIn(
                "child", runner_shared.read_integration_lock_holder(self.repo)
            )
            # And the bounded wait EXPIRES rather than blocking forever.
            progress: list[str] = []
            with runner_shared.integration_lock(
                self.repo,
                holder_label="waiter",
                timeout=0.5,
                progress=progress.append,
            ) as outcome:
                self.assertFalse(outcome.acquired)
                self.assertIn("child", outcome.holder)
            self.assertTrue(
                any("child" in line for line in progress),
                f"the expiry must NAME the holder; got {progress}",
            )
        finally:
            release.set()
            child.join(30)

    def test_the_lock_is_reacquirable_after_the_holder_exits(self):
        ctx = multiprocessing.get_context("fork")
        held, release = ctx.Event(), ctx.Event()
        child = ctx.Process(
            target=_hold_then_signal, args=(str(self.repo), held, release)
        )
        child.start()
        self.assertTrue(held.wait(30))
        release.set()
        child.join(30)
        with runner_shared.integration_lock(
            self.repo, holder_label="after", timeout=5
        ) as outcome:
            self.assertTrue(outcome.acquired)

    def test_a_KILLED_holder_does_not_strand_the_lock(self):
        """V-07's interrupted case, and what it does and does not prove.

        The OS drops an `flock` when its holder dies, so a subsequent acquire succeeding is EXPECTED
        even with no cleanup code at all. What a kill can genuinely strand is the lock FILE and its
        recorded holder line, so this asserts BOTH that the next acquire succeeds AND that the stale
        holder line does not survive into the next hold.
        """

        ctx = multiprocessing.get_context("fork")
        held, release = ctx.Event(), ctx.Event()
        child = ctx.Process(
            target=_hold_then_signal, args=(str(self.repo), held, release)
        )
        child.start()
        self.assertTrue(held.wait(30))
        os.kill(child.pid, 9)
        child.join(30)
        with runner_shared.integration_lock(
            self.repo, holder_label="after-kill", timeout=5
        ) as outcome:
            self.assertTrue(outcome.acquired, "a killed holder must not wedge the repo")
            self.assertIn(
                "after-kill", runner_shared.read_integration_lock_holder(self.repo)
            )

    def test_the_lock_file_is_NEVER_UNLINKED_on_release(self):
        """THE MEASURED HAZARD THIS FILE GUARDS, and it is the opposite of `driver.lock`'s rule.

        Unlinking a HELD `flock` path lets the next process create a FRESH INODE at the same name and
        acquire it while the first holder still holds the orphaned one, so both believe they hold the
        lock. Reproduced directly with `filelock` 3.29.7 while authoring: a second acquire was correctly
        REFUSED before the unlink and SUCCEEDED after it, with the first holder still holding. For THIS
        lock that is exactly the concurrent publish it exists to prevent.

        `runner_shutdown.RunLockHandle` MAY unlink `driver.lock` because that lock has exactly ONE
        acquirer and every other party merely probes it. This one is contended by construction.
        """

        path = runner_shared.integration_lock_path(self.repo)
        with runner_shared.integration_lock(self.repo, holder_label="x") as outcome:
            self.assertTrue(outcome.acquired)
        self.assertTrue(
            path.is_file(),
            "the lock file must SURVIVE release; unlinking it breaks mutual exclusion",
        )
        # The holder SIDECAR is the thing cleared, so a stale name cannot outlive the hold.
        self.assertEqual(runner_shared.read_integration_lock_holder(self.repo), "")

    def test_the_holder_line_SURVIVES_a_competing_failed_acquire(self):
        """The `O_TRUNC` hazard, measured and pinned.

        `filelock` opens with `O_CREAT | O_TRUNC`, so a FAILED acquire truncates the lock file. With the
        holder line stored INSIDE the lock file, a waiter's own failed attempt blanked the record it was
        about to read, and the wait then reported "an unrecorded holder" one second after a live holder
        wrote its name (observed while authoring). The sidecar is what fixes it.
        """

        with runner_shared.integration_lock(self.repo, holder_label="recorded-holder"):
            with self.assertRaises(platform_lock.LockBusy):
                platform_lock.acquire(runner_shared.integration_lock_path(self.repo))
            self.assertIn(
                "recorded-holder",
                runner_shared.read_integration_lock_holder(self.repo),
            )


class BoundedWaitTests(unittest.TestCase):
    """E-03 / V-03: the wait's EXPIRY arm, which is the one that would be under-tested."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        (self.repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_the_default_bound_is_FINITE(self):
        """A guard that hangs is worse than no guard, because no guard at least makes progress."""

        self.assertIsInstance(runner_shared.INTEGRATION_LOCK_TIMEOUT_SECONDS, float)
        self.assertGreater(runner_shared.INTEGRATION_LOCK_TIMEOUT_SECONDS, 0)
        self.assertLess(runner_shared.INTEGRATION_LOCK_TIMEOUT_SECONDS, 24 * 3600)

    def test_expiry_DEFERS_rather_than_FAILING_the_lane(self):
        """A lane failed on a lock timeout would DISCARD a completed validation.

        That is the very cost this mechanism exists to avoid, so the timeout arm must return a kind
        `classify_integration_refusal` treats as deferrable, and must NOT call the integration at all.
        """

        item: dict = {}
        called: list[bool] = []

        def _never(_item, _handle):
            called.append(True)
            return True, "should not happen", "integrated"

        with runner_shared.integration_lock(self.repo, holder_label="blocker"):
            integrated, reason, kind = runner_shared.integrate_under_repository_lock(
                self.repo,
                item,
                object(),
                state={"run_id": "run-waiter"},
                holder_label="run=run-waiter",
                integrate=_never,
                timeout=0.2,
            )

        self.assertFalse(integrated)
        self.assertEqual(
            called, [], "the integration must NOT run when the lock expired"
        )
        self.assertEqual(kind, runner_shared.INTEGRATION_REFUSAL_TRANSIENT)
        self.assertTrue(
            runner_shared.classify_integration_refusal(kind),
            "the expiry kind must be DEFERRABLE, or the lane's verified work is thrown away",
        )
        self.assertIn("deferred", reason.lower())
        self.assertFalse(item["integration_serialization"]["acquired"])

    def test_the_wait_REPORTS_rather_than_going_silent(self):
        """A silent block is operationally identical to the hang `platform_lock` warns about."""

        progress: list[str] = []
        with runner_shared.integration_lock(self.repo, holder_label="blocker"):
            with runner_shared.integration_lock(
                self.repo,
                holder_label="waiter",
                timeout=0.2,
                progress=progress.append,
            ) as outcome:
                self.assertFalse(outcome.acquired)
        self.assertTrue(progress, "a bounded wait must emit progress, not go silent")


class SerializationTests(unittest.TestCase):
    """E-03 / V-03: the uncontended, serialized and consented paths through the shared seam."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        (self.repo / "f.txt").write_text("x\n")
        subprocess.run(["git", "add", "f.txt"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "init"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        (self.repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_an_UNCONTENDED_integration_is_behaviorally_UNCHANGED(self):
        item: dict = {}
        sentinel = (True, "fast-forward integrated to main", "integrated")
        result = runner_shared.integrate_under_repository_lock(
            self.repo,
            item,
            object(),
            state={"run_id": "run-a"},
            holder_label="run=run-a",
            integrate=lambda _i, _h: sentinel,
        )
        self.assertEqual(result, sentinel)
        self.assertTrue(item["integration_serialization"]["acquired"])

    def test_MAIN_S_TIP_is_re_resolved_INSIDE_the_lock(self):
        """A tip read BEFORE acquiring is exactly the stale read this plan exists to stop.

        Asserted behaviorally: the tip is recorded, it equals the REAL current HEAD, and it was read
        while the lock was held (proven by the integration observing a held lock at the same moment).
        """

        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        held_during: list[bool] = []
        item: dict = {}

        def _observe(_i, _h):
            held_during.append(
                platform_lock.probe_free(runner_shared.integration_lock_path(self.repo))
                is False
            )
            return True, "ok", "integrated"

        runner_shared.integrate_under_repository_lock(
            self.repo,
            item,
            object(),
            state={"run_id": "run-a"},
            holder_label="run=run-a",
            integrate=_observe,
        )
        self.assertEqual(item["integration_serialization"]["main_tip_in_lock"], head)
        self.assertEqual(
            held_during,
            [True],
            "the merge must run INSIDE the held lock, or the tip can move under it",
        )

    def test_CONSENT_skips_the_lock_and_RECORDS_the_justification(self):
        """E-04: no silent override. The record must answer WHY, not merely THAT."""

        item: dict = {}
        with runner_shared.integration_lock(self.repo, holder_label="peer"):
            integrated, _reason, _kind = runner_shared.integrate_under_repository_lock(
                self.repo,
                item,
                object(),
                state={
                    "run_id": "run-b",
                    "options": {"allow_concurrent_driver": "disjoint Sets, measured"},
                },
                holder_label="run=run-b",
                integrate=lambda _i, _h: (True, "ok", "integrated"),
                timeout=0.2,
            )
        self.assertTrue(integrated, "consent must proceed even with a peer holding")
        self.assertFalse(item["integration_serialization"]["serialized"])
        self.assertEqual(
            item["integration_serialization"]["consent"], "disjoint Sets, measured"
        )

    def test_consent_is_READ_FROM_ONE_PLACE(self):
        self.assertEqual(runner_shared.concurrent_driver_consent(None), "")
        self.assertEqual(runner_shared.concurrent_driver_consent({}), "")
        self.assertEqual(
            runner_shared.concurrent_driver_consent({"options": {}}),
            "",
        )
        self.assertEqual(
            runner_shared.concurrent_driver_consent(
                {"options": {"allow_concurrent_driver": " why "}}
            ),
            "why",
        )


class EscapeHatchFlagTests(unittest.TestCase):
    """E-04 / V-04: the flag is in the SHARED table, takes a justification, and cannot be bare."""

    def test_the_flag_is_a_row_in_the_SHARED_table(self):
        row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG["--allow-concurrent-driver"]
        self.assertEqual(row.kind, "str")
        self.assertTrue(row.implemented)
        self.assertEqual(row.owner, "runner_shared.integrate_under_repository_lock")

    def test_BOTH_hosts_inherit_it_from_that_one_row(self):
        for name, module in BOTH:
            for subcommand in ("start", "resume"):
                with self.subTest(host=name, subcommand=subcommand):
                    parser = module.build_parser()
                    action = next(
                        a
                        for sub in parser._actions
                        if hasattr(sub, "choices") and sub.choices
                        for a in sub.choices[subcommand]._actions
                        if "--allow-concurrent-driver" in (a.option_strings or [])
                    )
                    self.assertIsNotNone(action)

    def test_passing_it_BARE_is_refused_by_argparse(self):
        for name, module in BOTH:
            with self.subTest(host=name):
                parser = module.build_parser()
                with self.assertRaises(SystemExit):
                    parser.parse_args(["start", "sel", "--allow-concurrent-driver"])

    def test_the_justification_is_FROZEN_as_TEXT_not_coerced_to_a_bool(self):
        """A bare boolean would record that somebody clicked past a gate and nothing about whether
        they should have, which is the whole content of this row."""

        for name, module in BOTH:
            with self.subTest(host=name):
                args = module.build_parser().parse_args(
                    ["start", "sel", "--allow-concurrent-driver", "two disjoint Sets"]
                )
                frozen = runner_shared.freeze_run_policy_flags(args)
                self.assertEqual(frozen["allow_concurrent_driver"], "two disjoint Sets")

    def test_omitting_it_freezes_NO_consent(self):
        for name, module in BOTH:
            with self.subTest(host=name):
                args = module.build_parser().parse_args(["start", "sel"])
                frozen = runner_shared.freeze_run_policy_flags(args)
                self.assertEqual(frozen["allow_concurrent_driver"], "")


class SharedImplementationTests(unittest.TestCase):
    """E-05 / V-05: ONE implementation, so `aw agy run` cannot race `aw oc run`.

    THE FORM IS OBJECT IDENTITY, because everything here is bound as a RE-EXPORT rather than as a
    per-host wrapper; see the module docstring for the measurement that makes this the right form (the
    integration wrappers are NOT identical across hosts, while re-exports like `state_root` are).
    """

    def test_every_shared_symbol_IS_the_same_object_on_both_hosts(self):
        for symbol in SHARED_SYMBOLS:
            shared = getattr(runner_shared, symbol)
            for name, module in BOTH:
                with self.subTest(symbol=symbol, host=name):
                    self.assertTrue(
                        hasattr(module, symbol), f"{name} does not carry {symbol}"
                    )
                    self.assertIs(
                        getattr(module, symbol),
                        shared,
                        f"{name}.{symbol} is a COPY, not the shared object",
                    )


class OperatorVerbTests(unittest.TestCase):
    """E-07 / V-07: the lock reachable by a human, over the SAME path the driver uses."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        (self.repo / "f.txt").write_text("x\n")
        subprocess.run(["git", "add", "f.txt"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "init"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        (self.repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *argv) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", "integration-lock", *argv],
            cwd=str(Path(runner_shared.__file__).parent.parent),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_the_verb_is_a_declared_parser_leaf(self):
        from agent_workflows.command_surface import (
            discover_parser_leaves,
            get_declaration,
        )

        leaves = discover_parser_leaves(cli._build_parser())
        self.assertIn("integration-lock", leaves)
        self.assertIsNotNone(get_declaration("integration-lock"))

    def test_status_reports_FREE_then_HELD_and_acquires_nothing(self):
        free = self._run("--status", "--dir", str(self.repo))
        self.assertEqual(free.returncode, 0, free.stderr)
        self.assertIn("FREE", free.stdout)
        with runner_shared.integration_lock(self.repo, holder_label="driver-side"):
            held = self._run("--status", "--dir", str(self.repo))
        self.assertEqual(held.returncode, 0, held.stderr)
        self.assertIn("HELD", held.stdout)
        self.assertIn("driver-side", held.stdout)

    def test_status_ACQUIRES_NOTHING(self):
        """A read-only question must not take the thing it asks about."""

        self._run("--status", "--dir", str(self.repo))
        self.assertIs(
            platform_lock.probe_free(runner_shared.integration_lock_path(self.repo)),
            True,
        )

    def test_the_verb_WAITS_for_a_driver_and_gives_up_bounded(self):
        with runner_shared.integration_lock(self.repo, holder_label="driver-side"):
            result = self._run(
                "--dir", str(self.repo), "--timeout", "0.4", "--", "git", "status"
            )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("driver-side", result.stderr)
        self.assertIn("DEFERRED", result.stderr)

    def test_the_verb_runs_its_command_and_forwards_its_EXIT_CODE(self):
        ok = self._run("--dir", str(self.repo), "--", "git", "rev-parse", "HEAD")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        bad = self._run("--dir", str(self.repo), "--", "git", "rev-parse", "nope-nope")
        self.assertNotEqual(bad.returncode, 0)

    def test_the_verb_and_the_driver_genuinely_CONTEND(self):
        """The property that makes this more than documentation."""

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "integration-lock",
                "--dir",
                str(self.repo),
                "--",
                sys.executable,
                "-c",
                "import time; print('held', flush=True); time.sleep(20)",
            ],
            cwd=str(Path(runner_shared.__file__).parent.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(proc.stdout.readline().strip(), "held")
            # The DRIVER side must now be excluded by the HAND side's lock.
            with runner_shared.integration_lock(
                self.repo, holder_label="driver", timeout=0.4
            ) as outcome:
                self.assertFalse(
                    outcome.acquired,
                    "the driver must be excluded by the operator verb's lock",
                )
        finally:
            proc.kill()
            proc.wait(30)


class ManagedBlockProtocolTests(unittest.TestCase):
    """E-08 / V-08: the protocol is GENERATED, names real spellings, and is honest about `--ff-only`."""

    def _block(self) -> str:
        from agent_workflows import engine

        return engine.agents_managed_block(target_layout="aw")

    def test_the_protocol_is_in_the_GENERATED_managed_block(self):
        block = self._block()
        self.assertIn("hold the integration lock", block)
        self.assertIn("aw integration-lock", block)

    def test_it_names_the_SHIPPED_verb_spellings(self):
        """A protocol naming a verb that does not exist is worse than none."""

        block = self._block()
        self.assertIn("aw integration-lock --status", block)
        from agent_workflows.command_surface import discover_parser_leaves

        self.assertIn("integration-lock", discover_parser_leaves(cli._build_parser()))

    def test_it_states_the_ff_only_LIMIT_rather_than_selling_it_as_sufficient(self):
        """F-11/PR-005: a reader who takes `--ff-only` as sufficient will skip the lock, which is the
        behavior that caused the incident."""

        block = self._block()
        self.assertIn("--ff-only", block)
        self.assertIn("NOT a substitute", block)
        self.assertIn("PROTOCOL, NOT AN ENFORCEMENT BOUNDARY", block)

    def test_the_managed_block_carries_NO_em_or_en_dashes(self):
        """The managed block is user-facing prose (AGENTS.md execution contract)."""

        block = self._block()
        self.assertNotIn("\u2014", block)
        self.assertNotIn("\u2013", block)

    def test_the_repository_s_OWN_agents_file_carries_the_regenerated_block(self):
        from tests.support import REPO_ROOT

        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("hold the integration lock", text)
        self.assertIn("aw integration-lock --status", text)


if __name__ == "__main__":
    unittest.main()
