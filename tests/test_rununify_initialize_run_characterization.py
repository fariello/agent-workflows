#!/usr/bin/env python3
"""rununify Order 09 (`orziju`) E-02: pin the DRIVER-IDENTITY contract, then characterize the
branches a split of `initialize_run` would move. Both hosts, as BEHAVIOR.

## Why the driver-identity half exists, and why it comes first

`initialize_run` freezes each run's own provenance:

    state["driver"] = {"path": str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__))}

`__file__` is evaluated in the module where that code is DEFINED, not where it is called from. So a
shared core relocated into `runner_shared` would write `runner_shared.py` for BOTH hosts, and two
consumers read that value's BASENAME as the host discriminator:

* `run_analytics_sources.driver_generation` maps the basename through `DRIVER_GENERATIONS`, and its
  own docstring records that "the basename is the ONLY discriminator that works";
* `run_viewer.load_run_summary` substring-matches `oc_runipd` / `agy_runipd` to label a run
  `OpenCode` / `Antigravity`.

Both would silently return `unknown` for every run created after such a split, permanently losing
host attribution in run analytics, and **no test covered the runners' end of that contract**, so the
whole suite would have stayed green. The plan calls this its F-9 and it is the sharpest hazard in the
`rununify` Set. The classes below are that missing test: they drive each host's REAL `initialize_run`
and assert the basename, the generation label, the host label, and the viewer's rendered driver name.

`test_a_core_relocated_to_runner_shared_would_be_caught` is the NON-VACUITY control: it constructs
the exact state a naive relocation would write and shows every one of those assertions failing. A
guard that has never been shown failing pins nothing.

## Why the characterization half exists

The parent Set forbids a child reconciling a symbol whose behavior no baseline has pinned, and every
existing pin on this function reads its SOURCE TEXT (14 sites across 6 files; see
the retired source-pin sibling held the inventory). A source pin dies on relocation even when
behavior is unchanged, and can be satisfied by a comment even when behavior is broken. So each test
here drives the real function and asserts the OBSERVABLE result: what it refuses and in what order,
what it freezes, and what it records.

AGY IS COVERED DELIBERATELY EVERYWHERE. The parent measured the hosts' suites as asymmetric (95 oc
tests against 21 agy at the time), so an agy-side regression can hide behind a green suite. Every
test runs against BOTH hosts through `subTest`.

## What this file does NOT claim

It pins what `initialize_run` DECIDES and FREEZES. It does not pin the correctness of the work the
run later performs, which stays with `run_queue`'s and `execute_item`'s own coverage. It does not
drive a real `opencode`/`agy` binary: `--prepare-only` is set so the function returns after freezing
state, which is precisely the seam under test.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    run_analytics_sources,
    run_viewer,
    runner_shared,
)

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

#: host -> the driver module basename that host must record, the generation label
#: `run_analytics_sources` must infer from it, the host label, and the name `run_viewer` renders.
DRIVER_IDENTITY = {
    "oc_runipd": {
        "basename": "oc_runipd.py",
        "generation": "oc_runipd",
        "host": "opencode",
        "viewer_label": "OpenCode",
    },
    "agy_runipd": {
        "basename": "agy_runipd.py",
        "generation": "agy_runipd",
        "host": "agy",
        "viewer_label": "Antigravity",
    },
}

_PLAN = """# IPD: {title}

- Date: 2026-09-17
- Kind: {kind}
- Status: {status}
- Set: {setid} (the {setid} set)
- Order: {order}
- Id: {id6}
- Item-Dependencies: {deps}
{extra}
## Goal

Do the thing.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 do it
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: output
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: small
- Cohesion rationale: one concern.
"""


class InitializeRunCase(unittest.TestCase):
    """Drive a host's REAL `initialize_run` over a synthetic repository."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self._repo_seq = 0

    # ---- fixtures ---------------------------------------------------------------------------
    def plan_text(
        self,
        id6: str,
        *,
        kind: str = "child",
        status: str = "approved",
        setid: str = "probe",
        order: int = 1,
        deps: str = "none",
        from_backlog: str | None = None,
    ) -> str:
        extra = f"- From-Backlog: {from_backlog}\n" if from_backlog else ""
        return _PLAN.format(
            title=id6,
            kind=kind,
            status=status,
            setid=setid,
            order=order,
            id6=id6,
            deps=deps,
            extra=extra,
        )

    def make_repo(
        self, plans: dict[str, str] | None = None, *, git: bool = True
    ) -> Path:
        """A git repository with the given `filename -> text` plans under `pending/`.

        A FRESH DIRECTORY PER CALL, deliberately. A test that drives both hosts over one repository
        hits `initialize_run`'s own "Run already exists" refusal, because `new_run_id` is derived
        from a whole-second timestamp plus the pid and the two calls land inside the same second.
        That refusal is real behavior (and is characterized in
        `ARunIdCollisionRefusesRatherThanOverwrites`), so the fixture must not provoke it
        incidentally.
        """
        self._repo_seq += 1
        repo = self.root / f"repo-{self._repo_seq}"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        if git:
            for cmd in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.invalid"],
                ["git", "config", "user.name", "Test"],
            ):
                subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        for name, text in (
            plans or {"20260917-probe-01-aaa111-probe.ipd.md": self.plan_text("aaa111")}
        ).items():
            (pending / name).write_text(text, encoding="utf-8")
        if git:
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def initialize(
        self, mod, repo: Path, argv: list[str] | None = None
    ) -> tuple[Path, dict, str, str]:
        """`initialize_run` on `repo`; returns (run_dir, state, stdout, stderr)."""
        args = mod.build_parser().parse_args(
            ["start", *(argv or ["all"]), "--repo", str(repo)]
        )
        args.prepare_only = True
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            run_dir = mod.initialize_run(args)
        return (
            run_dir,
            runner_shared.load_state(run_dir),
            out.getvalue(),
            err.getvalue(),
        )

    def events(self, run_dir: Path) -> list[dict]:
        raw = (run_dir / "events.jsonl").read_text(encoding="utf-8")
        return [json.loads(line) for line in raw.splitlines() if line.strip()]


# ==================================================================================================
# THE DRIVER-IDENTITY CONTRACT. F-9. No test covered this before this file.
# ==================================================================================================


class EachHostRecordsItsOwnDriverIdentity(InitializeRunCase):
    """A run must be attributable to the host that created it, through `state['driver']['path']`.

    Asserted at FOUR levels, because the value passes through four independent readers and a naive
    relocation breaks all four at once with no other symptom.
    """

    def test_the_recorded_driver_path_basename_is_this_hosts_runner_module(self):
        """The load-bearing assertion. `__file__` must be evaluated in the RUNNER, not in a shared
        module, so a relocated core has to be handed the caller's module path explicitly."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                recorded = state["driver"]["path"]
                self.assertEqual(
                    Path(recorded).name,
                    DRIVER_IDENTITY[name]["basename"],
                    f"{name} recorded driver path {recorded!r}. If this now names a SHARED module, "
                    "every run created by either host is host-unattributable in run analytics: "
                    "`run_analytics_sources.driver_generation` and `run_viewer` both key on this "
                    "BASENAME. A shared core must receive the caller's module path as a parameter",
                )

    def test_the_recorded_driver_sha256_is_that_same_modules_digest(self):
        """The digest and the path must describe the SAME file. Relocating one and not the other
        would produce a record that looks intact and attributes the run to a file whose contents it
        does not carry."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                module_file = Path(str(mod.__file__)).resolve()
                self.assertEqual(Path(state["driver"]["path"]), module_file)
                self.assertEqual(
                    state["driver"]["sha256"],
                    runner_shared.sha256_file(module_file),
                    f"{name}'s frozen driver digest is not this module's digest",
                )

    def test_run_analytics_infers_this_hosts_generation_and_not_unknown(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                generation = run_analytics_sources.driver_generation(state)
                self.assertEqual(generation, DRIVER_IDENTITY[name]["generation"])
                self.assertNotEqual(
                    generation,
                    run_analytics_sources.GENERATION_UNKNOWN,
                    f"{name}'s runs are no longer attributable to a driver generation",
                )
                self.assertEqual(
                    run_analytics_sources.generation_host(generation),
                    DRIVER_IDENTITY[name]["host"],
                )

    def test_the_run_viewer_labels_the_run_with_this_hosts_product_name(self):
        """The operator-visible half: `aw runs` names the host. A relocated core makes this render
        the shared module's stem (`runner_shared`) instead of `OpenCode` / `Antigravity`."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(mod, self.make_repo())
                summary = run_viewer.load_run_summary(run_dir, repo_root=run_dir)
                self.assertIsNotNone(summary)
                assert summary is not None
                self.assertEqual(
                    summary.driver,
                    DRIVER_IDENTITY[name]["viewer_label"],
                    f"{name}'s run no longer renders its host name in `aw runs`",
                )

    def test_the_two_hosts_record_DIFFERENT_driver_paths(self):
        """The property the discriminator exists for, asserted directly rather than inferred from
        the two per-host assertions above."""
        recorded = {}
        for name, mod in HOSTS:
            _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
            recorded[name] = Path(state["driver"]["path"]).name
        self.assertNotEqual(
            recorded["oc_runipd"],
            recorded["agy_runipd"],
            "both hosts now record the SAME driver path, so no consumer can tell their runs "
            f"apart: {recorded}",
        )

    def test_a_core_relocated_to_runner_shared_would_be_caught(self):
        """NON-VACUITY, and the whole reason this class exists (F-9).

        Construct the state a naive relocation WOULD write - `runner_shared.py` as the driver path
        for both hosts - and show that every consumer assertion above fails on it. Without this, the
        class above is four assertions that have never been demonstrated capable of failing.
        """
        shared_module = Path(str(runner_shared.__file__)).resolve()
        naive = {
            "driver": {
                "path": str(shared_module),
                "sha256": runner_shared.sha256_file(shared_module),
            }
        }
        self.assertEqual(Path(naive["driver"]["path"]).name, "runner_shared.py")

        generation = run_analytics_sources.driver_generation(naive)
        self.assertEqual(
            generation,
            run_analytics_sources.GENERATION_UNKNOWN,
            "a shared-module driver path must be UNRECOGNIZED, which is exactly the silent "
            "analytics loss F-9 names",
        )
        self.assertEqual(
            run_analytics_sources.generation_host(generation),
            run_analytics_sources.GENERATION_UNKNOWN,
        )
        for name in DRIVER_IDENTITY:
            with self.subTest(host=name):
                self.assertNotEqual(
                    Path(naive["driver"]["path"]).name,
                    DRIVER_IDENTITY[name]["basename"],
                )

        # And the viewer's label: it substring-matches, so a shared path falls through to the stem.
        run_dir = self.root / "naive-run"
        run_dir.mkdir()
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "naive-run",
                    "driver": naive["driver"],
                    "queue": [],
                    "selectors": [],
                }
            ),
            encoding="utf-8",
        )
        summary = run_viewer.load_run_summary(run_dir, repo_root=run_dir)
        assert summary is not None
        self.assertEqual(summary.driver, "runner_shared")
        self.assertNotIn(
            summary.driver,
            {v["viewer_label"] for v in DRIVER_IDENTITY.values()},
            "the viewer must NOT be able to name a host from a shared driver path",
        )


# ==================================================================================================
# CHARACTERIZATION: the refusals, and the ORDER two spec-stated pins assert as source text.
# ==================================================================================================


class ARefusalLeavesNoDurableState(InitializeRunCase):
    """Spec 25kzda 2.5a's shape, as BEHAVIOR rather than as a source offset.

    Two existing pins (`tests/test_run_flag_surface.py:745`, `:1340`) express this by splitting the
    source on the literal `run_dir = state_root` and requiring a call to appear in the PREFIX. That
    encodes the guarantee "a refusal happens before any durable state exists" as a textual fact
    about one function's body, which relocation destroys. Here it is the observable property: after
    a refusal, `state_root(repo)` contains NO run directory.
    """

    def run_dirs(self, repo: Path) -> list[Path]:
        root = runner_shared.state_root(repo)
        return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []

    def test_an_unimplemented_flag_refuses_before_any_run_directory_exists(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                # The shared table's own unimplemented rows, read from the table rather than
                # hard-coded, so a row changing state cannot make this test silently vacuous.
                unimplemented = [
                    row for row in runner_shared.RUN_POLICY_FLAGS if not row.implemented
                ]
                self.assertTrue(
                    unimplemented, "no unimplemented policy flag remains to test with"
                )
                setattr(args, unimplemented[0].dest, True)
                with self.assertRaises(runner_shared.RunFlagRefusal):
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertEqual(
                    self.run_dirs(repo),
                    [],
                    f"{name} created durable run state despite refusing the invocation; the "
                    "refusal must precede the run directory (spec 25kzda 2.5a)",
                )

    def test_an_out_of_range_retry_budget_refuses_before_any_run_directory_exists(self):
        """The bound is `run_recovery.validate_retry_budget`'s and is re-raised at the flag layer as
        `RunFlagRefusal`, so the OPERATOR-FACING type is asserted here and the bound's own message is
        asserted through it rather than re-stated."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                args.retry_budget = 11
                with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertIn("--retry-budget", str(ctx.exception))
                self.assertEqual(self.run_dirs(repo), [])

    def test_a_non_repository_refuses_before_any_run_directory_exists(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                bare = self.root / f"not-a-repo-{name}"
                bare.mkdir()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(bare)]
                )
                args.prepare_only = True
                with self.assertRaises(runner_shared.DriverError) as ctx:
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertIn("Not a Git repository", str(ctx.exception))
                self.assertEqual(self.run_dirs(bare), [])

    def test_the_control_a_valid_invocation_DOES_create_exactly_one_run_directory(self):
        """The non-vacuity control for this whole class: without it, a function that refused
        EVERYTHING would pass every test above."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo()
                run_dir, state, _out, _err = self.initialize(mod, repo)
                self.assertEqual(self.run_dirs(repo), [run_dir])
                self.assertEqual([i["id6"] for i in state["queue"]], ["aaa111"])


class TheDraftAdmissionGateExcludesRatherThanRefuses(InitializeRunCase):
    """Spec 2.5a bullet 4, as behavior: an ungated complete draft is WITHHELD and the rest runs.

    This is the behavioral equivalent of the ordering pin at `tests/test_run_flag_surface.py:1340`,
    which asserts textually that `expand_selectors` precedes `enforce_draft_admission_gate` and that
    both precede `run_dir = state_root`. The guarantee is that the exclusion decision is made
    against a RESOLVED queue and leaves nothing durable behind for the excluded item, and that is
    what is asserted here.
    """

    def repo_with_a_draft_and_a_reviewable(self) -> Path:
        return self.make_repo(
            {
                "20260917-probe-01-drf001-draft.ipd.md": self.plan_text(
                    "drf001", status="draft", order=1
                ),
                "20260917-probe-02-rev003-ordinary.ipd.md": self.plan_text(
                    "rev003", status="to-review", order=3
                ),
            }
        )

    def test_the_draft_is_excluded_and_the_reviewable_still_runs(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, state, _out, _err = self.initialize(
                    mod, self.repo_with_a_draft_and_a_reviewable(), ["reviews"]
                )
                queued = [item["id6"] for item in state["queue"]]
                self.assertNotIn("drf001", queued, "the ungated draft was admitted")
                self.assertIn("rev003", queued, "the rest of the queue did not proceed")
                # ... and the exclusion is DURABLY recorded, which is the half a source pin cannot
                # express at all.
                gate = [
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "draft-admission-gate"
                ]
                self.assertEqual(
                    len(gate), 1, f"{name}: expected one gate event, got {gate}"
                )
                self.assertIn("drf001", gate[0]["excluded_complete"])

    def test_the_gate_decision_is_made_against_the_RESOLVED_queue(self):
        """The ordering property the textual pin encodes: the gate sees expanded selectors, so its
        excluded set is drawn from the resolved ids rather than from the raw selector tokens."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(
                    mod, self.repo_with_a_draft_and_a_reviewable(), ["reviews"]
                )
                gate = next(
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "draft-admission-gate"
                )
                considered = set(gate["excluded_complete"]) | set(
                    gate.get("skipped_incomplete", [])
                )
                self.assertIn(
                    "drf001",
                    considered,
                    "the gate did not see the resolved id, so it ran before selector expansion",
                )

    def test_a_drafts_only_selection_freezes_NO_run_directory(self):
        """The strongest form of "the exclusion leaves nothing durable": when every selected item is
        an ungated draft, the run refuses rather than freezing an empty queue."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-drf001-draft.ipd.md": self.plan_text(
                            "drf001", status="draft"
                        )
                    }
                )
                args = mod.build_parser().parse_args(
                    ["start", "reviews", "--repo", str(repo)]
                )
                args.prepare_only = True
                with self.assertRaises(runner_shared.EmptyStatusSelection):
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                root = runner_shared.state_root(repo)
                self.assertEqual(
                    [p for p in root.iterdir() if p.is_dir()] if root.is_dir() else [],
                    [],
                    f"{name} froze a run directory for a selection it then refused",
                )


class TheMixedTypeGateIsReachedExactlyOnce(InitializeRunCase):
    """`tests/test_run_flag_surface.py:1564` asserts the CALL SITE COUNT is exactly one, in source.

    The behavioral equivalent is that the ledger carries exactly one `mixed-type-gate` record per
    run: two call sites would produce two records (or, worse, two decisions), and zero would produce
    none, which is the dead-gate defect `uyeko5` was written to fix.
    """

    def test_exactly_one_gate_record_per_run_on_both_hosts(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(mod, self.make_repo())
                records = [
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "mixed-type-gate"
                ]
                self.assertEqual(
                    len(records),
                    1,
                    f"{name} recorded {len(records)} mixed-type-gate events; the gate must have "
                    "exactly ONE reached call site",
                )

    def test_the_gate_does_not_APPLY_to_a_single_type_selection(self):
        """The honest limit `uyeko5` recorded, pinned so a future `--type` cannot change it
        silently: the gate is REACHED on every run and correctly does not apply today."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, _state, _out, _err = self.initialize(mod, self.make_repo())
                record = next(
                    e
                    for e in self.events(run_dir)
                    if e.get("event") == "mixed-type-gate"
                )
                self.assertFalse(record["gate_applied"])
                self.assertTrue(record["proceed"])


class TheFrozenQueueEntryShapeIsIdenticalOnBothHosts(InitializeRunCase):
    """F-2's resume hazard, measured rather than assumed.

    The plan's F-2 warned that a shared writer could change the queue-entry key set a RESUME reads.
    Measured at review and again here: both hosts write the IDENTICAL twelve keys, differing only in
    the source-order of `kind` and `order`, which JSON round-trips do not preserve as significant.
    So the hazard is LOW, and this class is what keeps it low.
    """

    EXPECTED_KEYS = frozenset(
        {
            "position",
            "id6",
            "setid",
            "configured_file",
            "dependencies",
            "kind",
            "order",
            "from_backlog",
            "initial_status",
            "action",
            "status",
            "attempts",
        }
    )

    def test_both_hosts_freeze_the_same_twelve_keys(self):
        seen = {}
        for name, mod in HOSTS:
            _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
            seen[name] = frozenset(state["queue"][0])
            with self.subTest(host=name):
                self.assertEqual(
                    seen[name],
                    self.EXPECTED_KEYS,
                    f"{name}'s queue entry shape changed; a RESUME of an in-flight run reads this "
                    "shape, so a key added or removed here is a compatibility change",
                )
        self.assertEqual(seen["oc_runipd"], seen["agy_runipd"])

    def test_the_from_backlog_link_is_frozen_on_the_entry(self):
        """`tests/test_runner_backlog_close.py:255` asserts the literal `"from_backlog"` appears in
        the source. The behavioral equivalent: the LINK actually reaches the frozen entry."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-aaa111-linked.ipd.md": self.plan_text(
                            "aaa111", from_backlog="bbbbbb"
                        )
                    }
                )
                _run_dir, state, _out, _err = self.initialize(mod, repo)
                self.assertEqual(state["queue"][0]["from_backlog"], "bbbbbb")

    def test_an_absent_link_freezes_None_rather_than_a_placeholder(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                self.assertIsNone(state["queue"][0]["from_backlog"])

    def test_an_orchestrators_kind_is_frozen_so_a_resume_rederives_its_action(self):
        """Both hosts must freeze `kind`, by DIFFERENT routes: oc reads `PlanRecord.kind`, agy falls
        back to `_plan_kind(path)` because its record lacks the field (the plan's F-4). The frozen
        RESULT must be the same, which is what a resume depends on."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-00-orc001-parent.ipd.md": self.plan_text(
                            "orc001", kind="orchestrator", order=0
                        ),
                        "20260917-probe-01-aaa111-child.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                _run_dir, state, _out, _err = self.initialize(mod, repo)
                by_id = {item["id6"]: item for item in state["queue"]}
                self.assertEqual(by_id["orc001"]["kind"], "orchestrator")
                self.assertEqual(by_id["orc001"]["action"], "orchestrate")
                self.assertEqual(by_id["aaa111"]["kind"], "child")
                self.assertEqual(by_id["aaa111"]["action"], "execute")


class TheFrozenOptionsCarryEachHostsOwnPolicy(InitializeRunCase):
    """The `options` dict is where the two hosts genuinely diverge (13 host-specific keys of 34
    live), so its per-host content is characterized rather than assumed symmetric.

    `tests/test_run_flag_surface.py:874` asserts the `full_auto` args-fallback SPELLING is `False`
    on both hosts, by regex over the source. The behavioral equivalent is that a Namespace WITHOUT
    the attribute freezes `False`, which is the property the spelling exists to produce.
    """

    def test_the_shared_policy_keys_are_frozen_by_the_one_shared_function(self):
        """The keys `freeze_run_policy_flags` owns must all be present on both hosts, read from the
        shared table rather than listed, so a new policy flag cannot land on one host only."""
        expected = {row.dest for row in runner_shared.RUN_POLICY_FLAGS if row.freeze}
        self.assertTrue(expected)
        for name, mod in HOSTS:
            with self.subTest(host=name):
                _run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                missing = sorted(expected - set(state["options"]))
                self.assertEqual(
                    missing,
                    [],
                    f"{name} did not freeze {missing}; spec 2.1 requires resume to use the "
                    "original options",
                )

    def test_full_auto_defaults_to_False_on_both_hosts_when_the_attribute_is_absent(
        self,
    ):
        """The behavioral form of the site-2 spelling pin. Deleting the attribute is what makes the
        `getattr` default observable: a caller that builds a Namespace by hand is the case the
        `uyeko5` E-07 change was about."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo()
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                delattr(args, "full_auto")
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    run_dir = mod.initialize_run(args)
                state = runner_shared.load_state(run_dir)
                self.assertIs(
                    state["options"]["full_auto"],
                    False,
                    f"{name} defaulted full_auto to True for a Namespace lacking the attribute; "
                    "that is the opt-in/opt-out divergence `uyeko5` E-07 closed",
                )

    def test_each_host_freezes_its_own_verification_key_with_its_own_polarity(self):
        """oc freezes `validate` (positive) plus a derived `no_audit`; agy freezes `no_verify`
        (negated). Opposite spellings of one concept, and getting the polarity wrong would make
        "verify" mean "do not verify" with no error anywhere (`ybkmzp` E-04)."""
        _run_dir, oc_state, _o, _e = self.initialize(oc_runipd, self.make_repo())
        self.assertIn("validate", oc_state["options"])
        self.assertNotIn("no_verify", oc_state["options"])
        self.assertIs(
            oc_state["options"]["no_audit"], not oc_state["options"]["validate"]
        )

        _run_dir, agy_state, _o, _e = self.initialize(agy_runipd, self.make_repo())
        self.assertIn("no_verify", agy_state["options"])
        self.assertNotIn("validate", agy_state["options"])
        self.assertNotIn("no_audit", agy_state["options"])

    def test_only_oc_freezes_a_launch_profile_because_only_oc_has_one(self):
        """F-11's capability asymmetry, pinned in BOTH directions. `agy_runipd` contains zero
        `runner_profiles` references, so a shared writer emitting `launch_profile` for agy would
        fabricate provenance the host cannot supply, and one emitting it for neither would break
        `tests/test_runner_profiles_e2e.py`."""
        _run_dir, oc_state, _o, _e = self.initialize(oc_runipd, self.make_repo())
        self.assertIn("launch_profile", oc_state["options"])
        self.assertIn("config_digest", oc_state["options"]["launch_profile"])

        _run_dir, agy_state, _o, _e = self.initialize(agy_runipd, self.make_repo())
        self.assertNotIn(
            "launch_profile",
            agy_state["options"],
            "agy froze a launch profile, but this host has NO launch-profile subsystem to have "
            "resolved one from; the value is fabricated provenance",
        )

    def test_each_host_freezes_its_own_executable_key(self):
        _run_dir, oc_state, _o, _e = self.initialize(oc_runipd, self.make_repo())
        _run_dir, agy_state, _o, _e = self.initialize(agy_runipd, self.make_repo())
        self.assertIn("opencode", oc_state["options"])
        self.assertNotIn("agy_executable", oc_state["options"])
        self.assertIn("agy_executable", agy_state["options"])
        self.assertNotIn("opencode", agy_state["options"])


class TheRunOrderRationaleIsFrozenBesideTheQueue(InitializeRunCase):
    """Both hosts call the SAME `run_order_rationale`, so the frozen record must have one shape.

    Characterized because a shared writer is the most likely place for this to be silently dropped
    on one host: nothing else reads it at creation time, so its absence would surface only later, in
    `aw runs`.
    """

    def test_the_rationale_is_present_and_names_the_executed_order(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-02-bbb222-second.ipd.md": self.plan_text(
                            "bbb222", order=2
                        ),
                        "20260917-probe-01-aaa111-first.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                _run_dir, state, _out, _err = self.initialize(mod, repo)
                self.assertIn("run_order", state)
                self.assertIsInstance(state["run_order"], dict)

    def test_the_run_created_event_is_the_first_ledger_record(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, state, _out, _err = self.initialize(mod, self.make_repo())
                events = self.events(run_dir)
                self.assertEqual(events[0]["event"], "run-created")
                self.assertEqual(events[0]["run_id"], state["run_id"])


class TheUntrackedDirtReportFiresOncePerRun(InitializeRunCase):
    """`tests/test_dirty_base_gate.py:179`/`:191` assert the call's PRESENCE and its POSITION in the
    source. The behavioral equivalents: the operator sees the notice exactly once, and it cannot
    fail the run.
    """

    def test_untracked_content_is_reported_and_does_not_refuse_the_run(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo()
                (repo / "unexpected.txt").write_text("dirt\n", encoding="utf-8")
                run_dir, state, out, err = self.initialize(mod, repo)
                combined = out + err
                self.assertIn(
                    "unexpected.txt",
                    combined,
                    f"{name} did not report the untracked path at run start",
                )
                # The report must NOT refuse: the run directory exists and the queue is frozen.
                self.assertTrue((run_dir / "state.json").is_file())
                self.assertEqual([i["id6"] for i in state["queue"]], ["aaa111"])

    def test_the_notice_is_emitted_ONCE_not_once_per_queue_entry(self):
        """The property `test_dirty_base_gate.py`'s position pin protects: placed beside the
        per-item guard it would repeat N times, so N is varied here rather than fixed at one."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-aaa111-one.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                        "20260917-probe-02-bbb222-two.ipd.md": self.plan_text(
                            "bbb222", order=2
                        ),
                        "20260917-probe-03-ccc333-three.ipd.md": self.plan_text(
                            "ccc333", order=3
                        ),
                    }
                )
                (repo / "unexpected.txt").write_text("dirt\n", encoding="utf-8")
                _run_dir, state, out, err = self.initialize(mod, repo)
                self.assertEqual(len(state["queue"]), 3)
                self.assertEqual(
                    (out + err).count("unexpected.txt"),
                    1,
                    f"{name} reported the untracked path once per ITEM rather than once per RUN",
                )


class ARunIdCollisionRefusesRatherThanOverwrites(InitializeRunCase):
    """The one destructive failure mode in this function: a second run freezing over the first.

    Characterized because a shared core reorders nothing else about the durable writes, but this
    check sits between the `run_id` resolution and the `mkdir`, and it is the only thing standing
    between a re-used `--run-id` and a clobbered run.
    """

    def test_reusing_a_run_id_refuses_and_leaves_the_first_run_intact(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo()
                first_dir, first_state, _o, _e = self.initialize(mod, repo)
                run_id = first_state["run_id"]

                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                args.run_id = run_id
                with self.assertRaises(runner_shared.DriverError) as ctx:
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                self.assertIn("Run already exists", str(ctx.exception))
                self.assertEqual(
                    runner_shared.load_state(first_dir)["created_at"],
                    first_state["created_at"],
                    f"{name} overwrote an existing run's frozen state",
                )


class TheDependencyPreflightRefusesAnInvalidGraphBeforeFreezing(InitializeRunCase):
    """Fail-closed on a bad dependency graph, before any durable state (`8guhs0` E-02).

    Behavioral, because the source pins on this function do not cover it at all: the closest thing
    is the ORDER pins, and neither names `enforce_dependency_preflight`.
    """

    def test_an_unresolvable_dependency_token_refuses_the_whole_run(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-01-aaa111-dependent.ipd.md": self.plan_text(
                            "aaa111", deps="unresolved"
                        )
                    }
                )
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(repo)]
                )
                args.prepare_only = True
                with self.assertRaises(runner_shared.DriverError):
                    with (
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        mod.initialize_run(args)
                root = runner_shared.state_root(repo)
                self.assertEqual(
                    [p for p in root.iterdir() if p.is_dir()] if root.is_dir() else [],
                    [],
                    f"{name} froze a run whose dependency graph it then refused",
                )


class TheManifestAndRunbookAreFrozenWithTheirDigests(InitializeRunCase):
    """A run's inputs are recorded by content, not only by path, so a later edit cannot silently
    change what the run was started from. Pinned because a shared writer computes four values here
    (`manifest`, `manifest_sha256`, `runbook`, `runbook_sha256`) from local variables, which is the
    easiest place for a relocation to drop one.
    """

    def test_a_discovered_manifest_is_written_into_the_run_and_digested(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, state, _o, _e = self.initialize(mod, self.make_repo())
                manifest_path = Path(state["manifest"])
                self.assertEqual(manifest_path.parent, run_dir)
                self.assertTrue(manifest_path.is_file())
                self.assertEqual(
                    state["manifest_sha256"],
                    runner_shared.sha256_file(manifest_path),
                    f"{name}'s frozen manifest digest does not match the file it names",
                )

    def test_a_default_runbook_is_written_into_the_run_and_digested(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, state, _o, _e = self.initialize(mod, self.make_repo())
                runbook_path = Path(state["runbook"])
                self.assertEqual(runbook_path.parent, run_dir)
                self.assertEqual(
                    state["runbook_sha256"], runner_shared.sha256_file(runbook_path)
                )

    def test_the_run_scaffold_directories_and_register_exist(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                run_dir, _state, _o, _e = self.initialize(mod, self.make_repo())
                for sub in ("sessions", "outcomes", "prompts"):
                    self.assertTrue((run_dir / sub).is_dir(), f"{name} missing {sub}/")
                self.assertTrue((run_dir / "decisions-and-questions.md").is_file())
                self.assertTrue((run_dir / "execution-report.md").is_file())


class TheFrozenStateSurvivesAResume(InitializeRunCase):
    """F-2's resume proof, from BOTH hosts.

    The plan asks for it as cheap confirmation rather than discovery (the queue-entry key sets are
    identical). What it establishes is that state frozen by `initialize_run` is READABLE by the
    resume path's own loader and carries everything a resume re-derives its actions from.
    """

    def test_a_frozen_run_reloads_with_its_queue_actions_re_derivable(self):
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-00-orc001-parent.ipd.md": self.plan_text(
                            "orc001", kind="orchestrator", order=0
                        ),
                        "20260917-probe-01-aaa111-child.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                run_dir, frozen, _o, _e = self.initialize(mod, repo)
                reloaded = runner_shared.load_state(run_dir)
                self.assertEqual(reloaded["queue"], frozen["queue"])
                for item in reloaded["queue"]:
                    with self.subTest(item=item["id6"]):
                        self.assertEqual(
                            mod.action_for(item["kind"], item["initial_status"]),
                            item["action"],
                            "a resume re-derives the action from the frozen kind+status, so the "
                            "two must agree with what was frozen",
                        )

    def test_the_frozen_queue_sorts_the_same_way_after_a_reload(self):
        """`queue_sort_key` is shared, so the ORDER a resume computes must not depend on anything
        the freeze dropped."""
        for name, mod in HOSTS:
            with self.subTest(host=name):
                repo = self.make_repo(
                    {
                        "20260917-probe-02-bbb222-second.ipd.md": self.plan_text(
                            "bbb222", order=2
                        ),
                        "20260917-probe-01-aaa111-first.ipd.md": self.plan_text(
                            "aaa111", order=1
                        ),
                    }
                )
                run_dir, frozen, _o, _e = self.initialize(mod, repo)
                reloaded = runner_shared.load_state(run_dir)
                # `queue_sort_key` is ONE object reached by both hosts (agy imports oc's), so the
                # host module's attribute is deliberately what is called here.
                self.assertIs(mod.queue_sort_key, oc_runipd.queue_sort_key)

                def order(queue: list[dict]) -> list[str]:
                    by_id = {i["id6"]: i for i in queue}
                    return [
                        i["id6"]
                        for i in sorted(
                            queue, key=lambda it: mod.queue_sort_key(it, by_id)
                        )
                    ]

                self.assertEqual(order(frozen["queue"]), order(reloaded["queue"]))


if __name__ == "__main__":
    unittest.main()
