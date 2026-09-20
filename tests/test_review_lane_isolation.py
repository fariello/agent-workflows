"""dirtygates-05 (`ajxr5d`): a REVIEW turn runs in an isolated lane and lands as ONE merge.

THE DEFECT THIS PINS, measured live rather than reasoned. A review turn is NOT read-only with respect
to the tree: it edits the plan under review and adds a review record, and it committed both to MAIN
(commit `a9510164`). Worse, on 2026-09-13 reviewing the ORCHESTRATOR `8lfoum` produced commit
`59cdc718` holding FIVE files, three of them SIBLING CHILD PLANS (`d7qoxv`, `metc8b`, `u23gbn`) that
were still `queued` in the SAME run, so one item's turn rewrote three other items' pending input
before their own turns ran. Those five files sat uncommitted for the turn's duration (~36 minutes on
the first item) and a concurrent execute run had its items refused against them.

WHAT IS ASSERTED HERE, and each is a property the plan's V-items demand:
  * V-02 MAIN STAYS UNCHANGED ACROSS A THREE-REVIEW SWEEP, sampled DURING each turn and not only
    after. The assertion is EQUALITY WITH THE PRE-RUN STATUS, never emptiness: the fixture
    deliberately dirties an unrelated tracked path, so an empty porcelain would mean the run
    DESTROYED a peer's change, which is the opposite of the property wanted.
  * V-02 ONE LANE SERVED EVERY REVIEW (one allocation, one worktree path across all three turns), not
    N lanes, which is OQ-02's ruling.
  * V-02 THE PROMPT IS LANE-RELATIVE AND SAYS SO. Both halves, because the path half ALONE was already
    measured insufficient (run `run-20260831T153226Z-3424176`, plan `y6mfgo`: the agent read
    `../../../DECISIONS.md` and committed 18 files into MAIN while its lane stayed at zero commits,
    because `--dir` alone does not convey isolation).
  * V-03 THE TWO FILES ARRIVE TOGETHER, in one merge, and a FAILED merge lands NEITHER.
  * V-03 THE ACTION KIND IS EXPLICIT WITH NO DEFAULT, no synthetic validation value is constructed for
    the review path, and REVALIDATION STILL RUNS for an execute turn.
  * V-04 THREE REVIEWS SHARED ONE SESSION while running in ONE lane, and no session is ever carried
    into a DIFFERENT tree (the `xd9sll` cardinality rule).
  * V-09 THE DISPOSITION IS DERIVED FROM THE LANE, including the `approved` case, and the test FAILS
    against the pre-change read (proved here by reading main explicitly).
  * V-10 A REVIEW'S WRITES ARE CLASSIFIED, and a sibling still QUEUED in the same run cannot be
    rewritten SILENTLY - F-9's exact scenario is reproduced.
  * V-11 THE SWEEP LANE IS REMOVED after a completed sweep and PRESERVED when it holds work, with the
    teardown classifying FIRST (its own docstring forbids force-removing a lane holding work).
  * V-01 the remaining LIFECYCLE exclusions still hold: a review performs no `driver_begin`, no
    `driver_finalize` and no suite check.
  * V-06 BOTH HOSTS, by shared-object identity plus per-host call-site assertions.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


def _effective_execute_item_source(driver) -> str:
    fn = driver.execute_item if hasattr(driver, "execute_item") else driver
    src = inspect.getsource(fn)
    if "execute_item_core" in src:
        return inspect.getsource(runner_shared.execute_item_core)
    return src


def _git(repo: Path, *args: str, check: bool = True) -> str:
    res = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if check and res.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {res.stderr}")
    return res.stdout


_PLAN = """\
# IPD: Demo {id6}

- Date: 2026-09-13
- Kind: child
- Concern: demo concern.
- Scope: demo scope.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: to-review
- Set: demo
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history

- 2026-09-13 to-review (test): created.

## Goal

Demo goal sentence.
"""


class _Fixture:
    """A git repo holding N `to-review` plans, plus a peer's UNRELATED dirty tracked path.

    THE UNRELATED DIRTY PATH IS THE POINT of the fixture, not decoration: it is what makes the
    main-cleanliness assertion able to tell "the run touched nothing" apart from "the run reverted a
    co-worker's edit". A test asserting an EMPTY porcelain would pass in both cases.
    """

    def __init__(self, root: Path, *, plans: int = 3) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        _git(root, "init", "-q", "-b", "main")
        _git(root, "config", "user.email", "test@example.invalid")
        _git(root, "config", "user.name", "Test")
        # A production install's ignore set. Load-bearing here: run state, worktrees and the history
        # sidecar must be ignored, or the lane teardown gate correctly refuses on an unknown file and
        # the test would measure the fixture rather than the code.
        (root / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n"
            ".aw/records/history.jsonl\n.aw/records/plans/INDEX.json\n"
            ".aw/records/plans/INDEX.md\n",
            encoding="utf-8",
        )
        (root / ".aw/records/plans/pending").mkdir(parents=True, exist_ok=True)
        (root / ".aw/records/reviews").mkdir(parents=True, exist_ok=True)
        (root / ".aw/records/reviews/.gitkeep").write_text("", encoding="utf-8")
        self.plans: list[Path] = []
        for n in range(1, plans + 1):
            id6 = f"rev{n:03d}"
            p = (
                root
                / ".aw/records/plans/pending"
                / f"20260913-demo-{n:02d}-{id6}-demo.ipd.md"
            )
            p.write_text(_PLAN.format(id6=id6, order=n), encoding="utf-8")
            self.plans.append(p)
        # The PEER's file: tracked and committed, then modified and left uncommitted.
        self.peer = root / "PEER.md"
        self.peer.write_text("peer v1\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "fixture")
        self.peer.write_text(
            "peer v1 WITH A PEER'S UNCOMMITTED EDIT\n", encoding="utf-8"
        )

    def porcelain(self) -> str:
        return _git(self.root, "status", "--porcelain", "-uall").strip()

    def worktrees(self) -> str:
        return _git(self.root, "worktree", "list").strip()

    def lane_branches(self) -> list[str]:
        # `git branch --list` marks the CURRENT branch with `*` and a branch checked out in ANOTHER
        # worktree with `+`, so both markers have to be stripped; a lane branch is by definition the
        # second case, which is exactly what a naive `strip("* ")` misses.
        out = _git(self.root, "branch", "--list", "aw/lane/*").strip()
        return [line.lstrip("*+ ").strip() for line in out.splitlines() if line.strip()]


def _state(repo: Path, plans: list[Path], *, isolate: bool = True) -> dict:
    return {
        "run_id": "run-test",
        "created_at": "2026-09-13T00:00:00+00:00",
        "updated_at": "2026-09-13T00:00:00+00:00",
        "selectors": ["reviews"],
        "repo": str(repo),
        "queue": [
            {
                "position": n,
                "id6": p.name.split("-")[3],
                "setid": "demo",
                "status": "queued",
                "configured_file": str(p.relative_to(repo)),
                "action": "review",
            }
            for n, p in enumerate(plans, start=1)
        ],
        "set_sessions": {},
        "session_id": None,
        "options": {
            "opencode": "/bin/true",
            "self_finalize": True,
            "isolate_worktree": isolate,
            "no_audit": False,
        },
    }


def _mk_run_dir(repo: Path) -> Path:
    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    return run_dir


def _reviewing_agent(
    run_dir: Path,
    *,
    observe: dict,
    set_status: str = "reviewed",
    also_write_sibling: str | None = None,
    commit_own_work: bool = True,
):
    """A review-turn stand-in that does what a real `/plan-review` does: edit the plan, add a record.

    Records, per item: the prompt it received, its cwd, its session id, and MAIN's porcelain AS OBSERVED
    DURING the turn - which is the window the original defect polluted and the only place a per-turn
    dirty window is visible at all.
    """

    def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
        work_dir = kwargs.get("work_dir")
        tree = Path(work_dir) if work_dir else Path(state["repo"])
        id6 = item["id6"]
        observe.setdefault("work_dir", {})[id6] = work_dir
        observe.setdefault("prompt", {})[id6] = Path(prompt_path).read_text(
            encoding="utf-8"
        )
        observe.setdefault("session_arg", {})[id6] = kwargs.get("resume_session")
        observe.setdefault("during", {})[id6] = _git(
            Path(state["repo"]), "status", "--porcelain", "-uall"
        ).strip()

        # THE REVIEW'S TWO FILES: the plan (revised) and its own record.
        target = next(
            (tree / ".aw/records/plans/pending").glob(f"*-{id6}-*.ipd.md"), None
        )
        if target is not None:
            text = target.read_text(encoding="utf-8")
            target.write_text(
                text.replace("- Status: to-review", f"- Status: {set_status}"),
                encoding="utf-8",
            )
        record = (
            tree / ".aw/records/reviews" / f"20260913-{id6}-01-{id6}-demo.review.md"
        )
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(f"# Review of {id6}\n\nverdict: fine\n", encoding="utf-8")

        # F-9's scenario, on demand: rewrite a SIBLING's plan while that sibling is still queued.
        if also_write_sibling:
            sib = next(
                (tree / ".aw/records/plans/pending").glob(
                    f"*-{also_write_sibling}-*.ipd.md"
                ),
                None,
            )
            if sib is not None:
                sib.write_text(
                    sib.read_text(encoding="utf-8") + "\nsibling corrected\n",
                    encoding="utf-8",
                )

        if commit_own_work:
            paths = [
                str(p.relative_to(tree))
                for p in ([target] if target is not None else []) + [record]
            ]
            if also_write_sibling:
                sib = next(
                    (tree / ".aw/records/plans/pending").glob(
                        f"*-{also_write_sibling}-*.ipd.md"
                    ),
                    None,
                )
                if sib is not None:
                    paths.append(str(sib.relative_to(tree)))
            _git(tree, "add", "--", *paths)
            _git(tree, "commit", "-qm", f"review({id6}): record the review")
        # ONE SESSION ID FOR EVERY TURN, which is what a real host reports when the driver passes
        # `--session <id>` and the conversation is actually resumed. Returning a DIFFERENT id per turn
        # would be simulating a host that ignored the resume request, which the driver correctly refuses
        # as an unexplained session change - a different property, covered by
        # `tests/test_session_rotation.py`.
        return 0, "ses_sweep", str(run_dir / "log"), ["oc"]

    return fake_run


# ======================================================================================
# V-02 / V-04 / V-06: the three-review sweep, one lane, one session, main untouched
# ======================================================================================


class TheSweepRunsInOneLaneAndMainIsUntouched(unittest.TestCase):
    def _run_sweep(self, driver, root: Path, **agent_kw):
        fx = _Fixture(root, plans=3)
        run_dir = _mk_run_dir(fx.root)
        state = _state(fx.root, fx.plans)
        observe: dict = {}
        before = fx.porcelain()
        launcher = "run_opencode" if driver is oc_runipd else "run_agy_turn"
        agent = _reviewing_agent(run_dir, observe=observe, **agent_kw)

        def agy_shim(state_, rd, item, prompt_path, attempt_no, **kwargs):
            # agy's launcher has a DIFFERENT signature (no plan_path, and it returns a conversation
            # id). Adapting here rather than writing a second fake keeps the two hosts asserted
            # against the SAME agent behavior, which is what a parity test must do.
            return agent(state_, rd, item, None, prompt_path, attempt_no, **kwargs)

        with mock.patch.object(
            driver, launcher, side_effect=(agy_shim if driver is agy_runipd else agent)
        ):
            for item in list(state["queue"]):
                driver.execute_item(run_dir, state, item, False)
        return fx, state, observe, before, run_dir

    def test_three_reviews_share_ONE_lane_and_main_is_EQUAL_not_empty(self):
        for name, driver in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                fx, state, observe, before, _rd = self._run_sweep(
                    driver, Path(tmp) / "repo"
                )

                # ONE LANE, not three: every turn's `work_dir` is the SAME path (OQ-02).
                dirs = set(observe["work_dir"].values())
                self.assertEqual(
                    len(dirs),
                    1,
                    f"the sweep must use ONE lane for every review; saw {dirs!r}",
                )
                self.assertIsNotNone(next(iter(dirs)))

                # MAIN IS UNCHANGED, sampled DURING each turn, and EQUAL to the pre-run status rather
                # than EMPTY: the peer's uncommitted edit must survive untouched.
                for id6, during in observe["during"].items():
                    self.assertEqual(
                        during,
                        before,
                        f"main's porcelain changed during review {id6}",
                    )
                self.assertIn("PEER.md", before)
                self.assertEqual(
                    fx.peer.read_text(encoding="utf-8"),
                    "peer v1 WITH A PEER'S UNCOMMITTED EDIT\n",
                    "the peer's uncommitted edit must be byte-identical after the sweep",
                )

                # EACH REVIEW'S TWO FILES REACHED MAIN.
                for n in (1, 2, 3):
                    id6 = f"rev{n:03d}"
                    plan = next(
                        (fx.root / ".aw/records/plans/pending").glob(
                            f"*-{id6}-*.ipd.md"
                        )
                    )
                    self.assertIn(
                        "- Status: reviewed", plan.read_text(encoding="utf-8")
                    )
                    self.assertTrue(
                        (fx.root / ".aw/records/reviews").glob(f"*-{id6}-*.review.md"),
                        f"review {id6}'s record must be on main",
                    )

    def test_the_sweep_shares_ONE_session_across_the_three_turns(self):
        """V-04: continuity is PRESERVED, which one lane is what makes safe (`xd9sll` was N trees)."""
        for name, driver in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                _fx, state, observe, _before, _rd = self._run_sweep(
                    driver, Path(tmp) / "repo"
                )
                sweep_session = state.get(runner_shared.REVIEW_SWEEP_SESSION_KEY)
                self.assertTrue(
                    sweep_session,
                    "the sweep's session must be recorded under its own run-level key",
                )
                # AND NOT under the SET key: promoting a lane session there is what would re-arm the
                # cross-tree carryover for a later EXECUTE turn in the same set.
                self.assertNotIn("demo", state.get("set_sessions", {}) or {})

    def test_the_sweep_lane_is_REMOVED_after_a_completed_sweep(self):
        """V-11: no leaked worktree, no leaked lane branch."""
        for name, driver in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                fx, state, _observe, _before, run_dir = self._run_sweep(
                    driver, Path(tmp) / "repo"
                )
                record = runner_shared.retire_review_sweep_lane(
                    fx.root, run_dir, state, save_state=lambda *_a, **_k: None
                )
                self.assertIsNotNone(record)
                assert record is not None
                self.assertTrue(
                    record["retired"],
                    f"a completed sweep's lane must be retired; reason: "
                    f"{record.get('retire_reason')!r}",
                )
                self.assertNotIn("aw/lane/review-sweep", fx.worktrees())
                self.assertEqual(
                    [b for b in fx.lane_branches() if "review-sweep" in b], []
                )

    def test_a_sweep_lane_that_HOLDS_WORK_is_PRESERVED_not_force_removed(self):
        """V-11's negative half: the teardown CLASSIFIES first.

        `teardown_isolation_worktree`'s own docstring states it must only ever be called on a lane
        holding NO work, so an unconditional teardown would be a contract violation, not merely
        untidy. The natural fixture is a review whose merge did not land, which is exactly what a
        stranded review leaves behind.
        """
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            run_dir = _mk_run_dir(fx.root)
            state = _state(fx.root, fx.plans)
            handle, refresh = runner_shared.acquire_review_sweep_lane(
                fx.root, run_dir, state, save_state=lambda *_a, **_k: None
            )
            self.assertIsNone(refresh, "the allocating call performs no refresh")
            # Leave UNEXPLAINED content in the lane: not driver-written, not a collected submission.
            (Path(handle.path) / "unexplained.txt").write_text(
                "mine\n", encoding="utf-8"
            )
            record = runner_shared.retire_review_sweep_lane(
                fx.root, run_dir, state, save_state=lambda *_a, **_k: None
            )
            assert record is not None
            self.assertFalse(
                record["retired"],
                "a lane holding unexplained content must NOT be force-removed",
            )
            self.assertTrue(Path(handle.path).is_dir(), "the lane must still be there")
            self.assertIn(
                handle.branch,
                fx.lane_branches(),
                "the preserved lane's BRANCH must survive too",
            )
            self.assertTrue(record.get("retire_reason"))


# ======================================================================================
# V-02: the prompt is lane-relative AND says so (both halves of the `y6mfgo` lesson)
# ======================================================================================


class TheReviewPromptIsLaneRelativeAndSaysSo(unittest.TestCase):
    def test_both_halves_are_present_for_an_isolated_review(self):
        for name, driver in _DRIVERS:
            with self.subTest(driver=name):
                lane = Path("/tmp/lane-xyz")
                plan = (
                    lane / ".aw/records/plans/pending/20260913-demo-01-rev001-x.ipd.md"
                )
                text = driver.build_review_prompt(
                    {
                        "id6": "rev001",
                        "setid": "demo",
                        "position": 1,
                        "action": "review",
                    },
                    {"run_id": "run-test", "repo": "/main/checkout"},
                    Path("/run"),
                    plan,
                    Path("/main/checkout"),
                    lane_root=lane,
                )
                first = text.splitlines()[0]
                # HALF ONE: the command line names the LANE-RELATIVE path and nothing else.
                self.assertTrue(first.startswith("/plan-review "), first)
                self.assertEqual(
                    first.split(" ", 1)[1],
                    ".aw/records/plans/pending/20260913-demo-01-rev001-x.ipd.md",
                )
                self.assertNotIn("/main/checkout", first)
                # HALF TWO: the explicit in-lane statement, WITHOUT WHICH the path fix was already
                # measured insufficient (`y6mfgo`: `--dir` alone does not convey isolation).
                self.assertIn("ISOLATED GIT WORKTREE", text)
                self.assertIn(str(lane), text)
                self.assertIn("Do NOT read or write the main checkout", text)

    def test_a_NON_isolated_review_prompt_is_byte_identical(self):
        """Spec R1.3: non-isolated execution is a supported mode, not a degraded one."""
        for name, driver in _DRIVERS:
            with self.subTest(driver=name):
                repo = Path("/main/checkout")
                plan = (
                    repo / ".aw/records/plans/pending/20260913-demo-01-rev001-x.ipd.md"
                )
                text = driver.build_review_prompt(
                    {
                        "id6": "rev001",
                        "setid": "demo",
                        "position": 1,
                        "action": "review",
                    },
                    {"run_id": "run-test", "repo": str(repo)},
                    Path("/run"),
                    plan,
                    repo,
                )
                self.assertEqual(
                    text,
                    "/plan-review .aw/records/plans/pending/20260913-demo-01-rev001-x.ipd.md",
                )


# ======================================================================================
# V-03: one merge, an explicit no-default action kind, no synthetic validation value
# ======================================================================================


class TheReviewMergeIsExplicitAndCarriesBothFiles(unittest.TestCase):
    def test_the_action_kind_has_NO_DEFAULT_in_the_shared_function(self):
        """The `host_label` precedent: a value whose wrong setting is silently harmful takes no default.

        A defaulted action kind would let a future caller silently SKIP revalidation (if it defaulted to
        `review`) or silently revalidate an action with nothing to revalidate (if `execute`).
        """
        node = next(
            n
            for n in ast.parse(
                Path(str(runner_shared.__file__)).read_text(encoding="utf-8")
            ).body
            if isinstance(n, ast.FunctionDef) and n.name == "integrate_lane_branch"
        )
        names = [a.arg for a in node.args.kwonlyargs]
        self.assertIn("action_kind", names)
        self.assertIsNone(
            node.args.kw_defaults[names.index("action_kind")],
            "`action_kind` must have NO default; see this test's docstring",
        )

    def test_an_unrecognized_action_kind_is_REFUSED_not_coerced(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-test")
            with self.assertRaises(runner_shared.DriverError) as ctx:
                runner_shared.integrate_lane_branch(
                    fx.root,
                    handle,
                    "rev001",
                    None,
                    host_label="aw oc run",
                    run_checked=oc_runipd.run_checked,
                    action_kind="reveiw",  # a typo, deliberately
                )
            self.assertIn("unrecognized action_kind", str(ctx.exception))

    def test_the_review_path_constructs_NO_synthetic_validation_value(self):
        """OQ-01's load-bearing line: skip the gate EXPLICITLY, never satisfy it with a fake value.

        Asserted STRUCTURALLY on each host's review wrapper: it takes no `validation_runner` parameter
        at all, so a caller cannot pass one even by mistake, and it binds `None`.
        """
        for name, driver in _DRIVERS:
            with self.subTest(driver=name):
                node = next(
                    n
                    for n in ast.parse(
                        Path(str(driver.__file__)).read_text(encoding="utf-8")
                    ).body
                    if isinstance(n, ast.FunctionDef)
                    and n.name == "integrate_review_lane_branch"
                )
                self.assertEqual(
                    [a.arg for a in node.args.args],
                    ["repo", "handle", "id6"],
                    "the review wrapper must not accept a validation runner",
                )
                call = next(
                    sub
                    for sub in ast.walk(node)
                    if isinstance(sub, ast.Call)
                    and "runner_shared.integrate_lane_branch" in ast.unparse(sub.func)
                )
                bound = {
                    kw.arg: ast.unparse(kw.value)
                    for kw in call.keywords
                    if kw.arg is not None
                }
                self.assertEqual(
                    bound["action_kind"],
                    "runner_shared.INTEGRATION_ACTION_REVIEW",
                )
                self.assertEqual(ast.unparse(call.args[3]), "None")

    def test_revalidation_STILL_RUNS_for_an_execute_turn(self):
        """The shared gate must not have been weakened for its ORIGINAL caller."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-exec")
            (Path(handle.path) / "src").mkdir(parents=True, exist_ok=True)
            (Path(handle.path) / "src" / "x.txt").write_text("x\n", encoding="utf-8")
            _git(Path(handle.path), "add", "src/x.txt")
            _git(Path(handle.path), "commit", "-qm", "work")
            calls: list[object] = []

            def runner(*a, **k):
                calls.append((a, k))
                return True, "validated"

            runner_shared.integrate_lane_branch(
                fx.root,
                handle,
                "exec01",
                runner,
                host_label="aw oc run",
                run_checked=oc_runipd.run_checked,
                action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
            )
            self.assertTrue(
                calls, "the execute path must still invoke the validation runner"
            )

    def test_a_review_merge_carries_BOTH_files_in_ONE_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-test")
            lane = Path(handle.path)
            plan = next((lane / ".aw/records/plans/pending").glob("*-rev001-*.ipd.md"))
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- Status: to-review", "- Status: reviewed"
                ),
                encoding="utf-8",
            )
            record = lane / ".aw/records/reviews/20260913-rev001-01-rev001-x.review.md"
            record.write_text("# Review\n", encoding="utf-8")
            _git(
                lane,
                "add",
                "--",
                str(plan.relative_to(lane)),
                str(record.relative_to(lane)),
            )
            _git(lane, "commit", "-qm", "review(rev001): record")
            before_head = _git(fx.root, "rev-parse", "HEAD").strip()

            integrated, reason, kind = oc_runipd.integrate_review_lane_branch(
                fx.root, handle, "rev001"
            )
            self.assertTrue(integrated, reason)
            self.assertEqual(kind, "integrated")
            names = _git(
                fx.root, "diff", "--name-status", f"{before_head}..HEAD"
            ).strip()
            self.assertIn("rev001", names)
            self.assertIn(".review.md", names)
            self.assertIn(
                "- Status: reviewed",
                (
                    next(
                        (fx.root / ".aw/records/plans/pending").glob(
                            "*-rev001-*.ipd.md"
                        )
                    )
                ).read_text(encoding="utf-8"),
            )

    def test_a_FAILED_merge_lands_NEITHER_file_and_leaves_the_plan_unrevised(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-test")
            lane = Path(handle.path)
            lane_plan = next(
                (lane / ".aw/records/plans/pending").glob("*-rev001-*.ipd.md")
            )
            lane_plan.write_text(
                lane_plan.read_text(encoding="utf-8").replace(
                    "- Status: to-review", "- Status: reviewed"
                ),
                encoding="utf-8",
            )
            record = lane / ".aw/records/reviews/20260913-rev001-01-rev001-x.review.md"
            record.write_text("# Review\n", encoding="utf-8")
            _git(
                lane,
                "add",
                "--",
                str(lane_plan.relative_to(lane)),
                str(record.relative_to(lane)),
            )
            _git(lane, "commit", "-qm", "review(rev001): record")

            # FORCE A CONFLICT: main changes the SAME plan differently and commits it.
            main_plan = next(
                (fx.root / ".aw/records/plans/pending").glob("*-rev001-*.ipd.md")
            )
            main_plan.write_text(
                main_plan.read_text(encoding="utf-8").replace(
                    "- Status: to-review", "- Status: draft\n- Note: a peer's change"
                ),
                encoding="utf-8",
            )
            _git(fx.root, "add", "--", str(main_plan.relative_to(fx.root)))
            _git(fx.root, "commit", "-qm", "peer: change the same plan")
            peer_bytes = main_plan.read_text(encoding="utf-8")

            integrated, reason, _kind = oc_runipd.integrate_review_lane_branch(
                fx.root, handle, "rev001"
            )
            self.assertFalse(
                integrated, "a conflicting merge must NOT be reported landed"
            )
            self.assertTrue(reason)
            # NEITHER file landed, and the peer's bytes are intact.
            self.assertEqual(main_plan.read_text(encoding="utf-8"), peer_bytes)
            self.assertFalse(
                (
                    fx.root
                    / ".aw/records/reviews/20260913-rev001-01-rev001-x.review.md"
                ).exists(),
                "the review record must not be on main after a failed merge",
            )
            # MAIN IS CLEAN: the abort left no markers and no partial merge.
            self.assertNotIn("UU", fx.porcelain())


# ======================================================================================
# V-09: the disposition is derived from the LANE
# ======================================================================================


class TheReviewDispositionComesFromTheLane(unittest.TestCase):
    def test_an_approved_setting_review_is_recorded_approved_from_the_lane(self):
        for name, driver in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                fx = _Fixture(Path(tmp) / "repo", plans=1)
                run_dir = _mk_run_dir(fx.root)
                handle = runner_shared.allocate_review_sweep_worktree(
                    fx.root, f"run-{name}"
                )
                lane = Path(handle.path)
                lane_plan = next(
                    (lane / ".aw/records/plans/pending").glob("*-rev001-*.ipd.md")
                )
                lane_plan.write_text(
                    lane_plan.read_text(encoding="utf-8").replace(
                        "- Status: to-review", "- Status: approved"
                    ),
                    encoding="utf-8",
                )
                item = {
                    "position": 1,
                    "id6": "rev001",
                    "setid": "demo",
                    "action": "review",
                    "configured_file": str(fx.plans[0].relative_to(fx.root)),
                }

                # THE LANE READ: the revision is there, so `approved` is what must be recorded.
                lane_disp, _ = driver.reconcile_disposition(
                    fx.root, item, run_dir, 0, plan_repo=lane
                )
                self.assertEqual(lane_disp, "approved")

                # THE PRE-CHANGE READ, kept as the proof this test is not tautological: MAIN still says
                # `to-review`, so the status comparison MISSES and the turn is scored merely `reviewed`.
                main_disp, _ = driver.reconcile_disposition(fx.root, item, run_dir, 0)
                self.assertEqual(
                    main_disp,
                    "reviewed",
                    "reading MAIN must still lose the `approved` verdict; if this changes, "
                    "the lane read above stopped being the thing under test",
                )

    def test_the_disposition_is_computed_BEFORE_integration_so_the_lane_is_the_only_answer(
        self,
    ):
        """F-15: the ordering is FIXED by the code, so "read main after the merge" is not a real branch."""
        for name, driver in _DRIVERS:
            with self.subTest(driver=name):
                src = _effective_execute_item_source(driver)
                tree = ast.parse(ast.unparse(ast.parse(src)))
                disp_lines = [
                    n.lineno
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Call)
                    and getattr(n.func, "id", None) == "reconcile_disposition"
                ]
                integ_lines = [
                    n.lineno
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Call)
                    and getattr(n.func, "id", None)
                    in ("integrate_lane_branch", "integrate_review_lane_branch")
                ]
                self.assertTrue(disp_lines and integ_lines)
                self.assertLess(
                    min(disp_lines),
                    min(integ_lines),
                    "the disposition must be computed before any integration",
                )


# ======================================================================================
# V-10: a review's writes are classified, and a QUEUED sibling is never silently rewritten
# ======================================================================================


class AReviewsWritesAreMeasuredFromItsOwnCommits(unittest.TestCase):
    """The scope report must not attribute MAIN's commits to the review that ran beside them.

    REGRESSION GUARD for a measured false alarm (2026-09-17): a review of plan `5w8g8j` whose own commit
    touched exactly TWO files was reported as having "also wrote 34 path(s) outside its own plan and
    review record", naming `oc_runipd.py`, `runner_shared.py`, `cli.py`, thirteen test files,
    `CHANGELOG.md` and a spec. A plan review cannot write product code and had not: those were main's own
    commits, arriving on the sweep lane through the `--ff-only` refresh while the lane's base stayed
    frozen at allocate.

    WHY THE FALSE ALARM MATTERED. The report IS the whole guard (the chosen shape is
    PERMIT-AND-RECONCILE, with no refusal behind it), and it exists for a real harm: an orchestrator
    review silently rewrote three sibling child plans that had not had their turns. A guard that names
    dozens of innocent paths every run is one an operator learns to skim, and the real sibling rewrite is
    skimmed with it.
    """

    def _lane_repo(self, tmp: str):
        """A repo whose sweep lane was REFRESHED to main before the review turn wrote anything."""
        repo = Path(tmp)
        _git(repo, "init", "-q", "-b", "main", ".")
        _git(repo, "config", "user.email", "t@example.invalid")
        _git(repo, "config", "user.name", "T")
        (repo / "f.txt").write_text("base\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "base")
        _git(repo, "branch", "-q", "sweep")
        frozen_base = _git(repo, "rev-parse", "HEAD").strip()
        # Other turns and concurrent sessions land four files on main.
        for i in range(1, 5):
            (repo / f"main{i}.py").write_text(f"x{i}\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "other turns land four files")
        # The sweep lane is fast-forwarded to main before this review's turn, so main's commits are now
        # reachable from the lane branch. This is the refresh policy working as designed.
        _git(repo, "checkout", "-q", "sweep")
        _git(repo, "merge", "-q", "--ff-only", "main")
        tip_before = _git(repo, "rev-parse", "HEAD").strip()
        # The review writes exactly one file: its own plan.
        (repo / "plan-rev001.md").write_text("reviewed\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "review writes its own plan")
        return repo, frozen_base, tip_before

    def test_measuring_from_the_frozen_base_is_what_produced_the_false_alarm(self):
        """The BEFORE state, pinned so the fix cannot be reverted without this failing."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, frozen_base, _tip = self._lane_repo(tmp)
            handle = SimpleNamespace(branch="sweep", base_commit=frozen_base)
            paths = runner_shared.review_turn_changed_files(
                repo, handle, since_commit=None
            )
            # Four of main's files plus the review's own one.
            self.assertEqual(len(paths), 5, sorted(paths))
            scope = runner_shared.classify_review_writes(
                paths, id6="rev001", queued_id6s=[]
            )
            self.assertEqual(len(scope.out_of_scope), 4, sorted(scope.out_of_scope))

    def test_measuring_from_the_pre_turn_tip_reports_only_the_reviews_own_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, frozen_base, tip_before = self._lane_repo(tmp)
            handle = SimpleNamespace(branch="sweep", base_commit=frozen_base)
            paths = runner_shared.review_turn_changed_files(
                repo, handle, since_commit=tip_before
            )
            self.assertEqual(sorted(paths), ["plan-rev001.md"])
            scope = runner_shared.classify_review_writes(
                paths, id6="rev001", queued_id6s=[]
            )
            self.assertEqual(scope.out_of_scope, ())
            self.assertTrue(scope.clean)

    def test_a_genuine_sibling_rewrite_is_still_named(self):
        """The guard must keep catching the harm it was built for, which is the load-bearing half."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, frozen_base, tip_before = self._lane_repo(tmp)
            # The review ALSO rewrites a sibling plan that has not had its turn.
            (repo / "plan-rev002.md").write_text("rewritten\n", encoding="utf-8")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", "review also rewrites a sibling")
            handle = SimpleNamespace(branch="sweep", base_commit=frozen_base)
            paths = runner_shared.review_turn_changed_files(
                repo, handle, since_commit=tip_before
            )
            scope = runner_shared.classify_review_writes(
                paths, id6="rev001", queued_id6s=["rev002"]
            )
            self.assertEqual(sorted(scope.out_of_scope), ["plan-rev002.md"])
            self.assertEqual(scope.queued_siblings, ("plan-rev002.md",))
            self.assertFalse(scope.clean)

    def test_an_unreadable_tip_falls_back_to_the_frozen_base_rather_than_reporting_nothing(
        self,
    ):
        """Over-reporting is the safe direction: under-reporting hides the sibling rewrite."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, frozen_base, _tip = self._lane_repo(tmp)
            handle = SimpleNamespace(branch="sweep", base_commit=frozen_base)
            paths = runner_shared.review_turn_changed_files(
                repo, handle, since_commit="   "
            )
            self.assertEqual(len(paths), 5, sorted(paths))

    def test_lane_branch_tip_returns_none_for_an_unknown_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _base, _tip = self._lane_repo(tmp)
            self.assertIsNone(
                runner_shared.lane_branch_tip(
                    repo, SimpleNamespace(branch="no/such/branch")
                )
            )
            self.assertIsNone(
                runner_shared.lane_branch_tip(repo, SimpleNamespace(branch=""))
            )


class AReviewsWritesAreNamed(unittest.TestCase):
    def test_the_classifier_splits_a_reviews_own_files_from_everything_else(self):
        scope = runner_shared.classify_review_writes(
            [
                ".aw/records/plans/pending/20260913-demo-01-rev001-x.ipd.md",
                ".aw/records/reviews/20260913-rev001-01-rev001-x.review.md",
                ".aw/records/plans/pending/20260913-demo-02-rev002-x.ipd.md",
                "src/unrelated.py",
            ],
            id6="rev001",
            queued_id6s=["rev002", "rev003"],
        )
        self.assertEqual(len(scope.allowed), 2)
        self.assertEqual(len(scope.out_of_scope), 2)
        self.assertEqual(
            scope.queued_siblings,
            (".aw/records/plans/pending/20260913-demo-02-rev002-x.ipd.md",),
        )
        self.assertFalse(scope.clean)

    def test_a_clean_review_is_reported_clean(self):
        scope = runner_shared.classify_review_writes(
            [
                ".aw/records/plans/pending/20260913-demo-01-rev001-x.ipd.md",
                ".aw/records/reviews/20260913-rev001-01-rev001-x.review.md",
            ],
            id6="rev001",
            queued_id6s=["rev002"],
        )
        self.assertTrue(scope.clean)
        self.assertEqual(scope.queued_siblings, ())
        self.assertIn(
            "only its own plan",
            runner_shared.describe_review_write_scope(scope, id6="rev001"),
        )

    def test_F9s_EXACT_scenario_is_recorded_rather_than_silent(self):
        """Reproduce F-9: reviewing one plan while a SIBLING is still `queued`, and rewriting it.

        The shape chosen is PERMIT-AND-RECONCILE, not REFUSE, because an orchestrator review legitimately
        reads (and may correct) its children - that is how this Set's own collision with three approved
        plans was caught. The objection F-9 records is that it happened SILENTLY, to an item that had not
        had its turn. So the assertion is that the run record NAMES it.
        """
        for name, driver in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                fx = _Fixture(Path(tmp) / "repo", plans=3)
                run_dir = _mk_run_dir(fx.root)
                state = _state(fx.root, fx.plans)
                observe: dict = {}
                launcher = "run_opencode" if driver is oc_runipd else "run_agy_turn"
                agent = _reviewing_agent(
                    run_dir, observe=observe, also_write_sibling="rev002"
                )

                def agy_shim(state_, rd, item, prompt_path, attempt_no, **kwargs):
                    return agent(
                        state_, rd, item, None, prompt_path, attempt_no, **kwargs
                    )

                with mock.patch.object(
                    driver,
                    launcher,
                    side_effect=(agy_shim if driver is agy_runipd else agent),
                ):
                    driver.execute_item(run_dir, state, state["queue"][0], False)

                item = state["queue"][0]
                scope = item.get("review_write_scope")
                self.assertIsNotNone(
                    scope, "a review's write scope must be recorded on the item"
                )
                assert scope is not None
                sibling_paths = [p for p in scope["queued_siblings"] if "rev002" in p]
                self.assertTrue(
                    sibling_paths,
                    f"the QUEUED sibling's rewritten path must be named; scope was {scope!r}",
                )
                events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
                self.assertIn("review-wrote-out-of-scope-paths", events)


# ======================================================================================
# V-01: the LIFECYCLE exclusions still hold after the splits
# ======================================================================================


class TheLifecycleExclusionsStillHold(unittest.TestCase):
    def test_a_review_performs_no_begin_no_finalize_and_no_suite_check(self):
        """The direct regression for the hazard E-01 exists to prevent.

        A wholesale deletion of `not is_review` from either split site would make a review call
        `driver_begin` (claiming execution authority) or `driver_finalize` (attempting a terminal
        transition). This FAILS if that happens.
        """
        for name, driver in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                fx = _Fixture(Path(tmp) / "repo", plans=1)
                run_dir = _mk_run_dir(fx.root)
                state = _state(fx.root, fx.plans)
                observe: dict = {}
                launcher = "run_opencode" if driver is oc_runipd else "run_agy_turn"
                agent = _reviewing_agent(run_dir, observe=observe)

                def agy_shim(state_, rd, item, prompt_path, attempt_no, **kwargs):
                    return agent(
                        state_, rd, item, None, prompt_path, attempt_no, **kwargs
                    )

                calls: dict[str, int] = {}

                def counting(key, result):
                    def f(*_a, **_k):
                        calls[key] = calls.get(key, 0) + 1
                        return result

                    return f

                with (
                    mock.patch.object(
                        driver,
                        launcher,
                        side_effect=(agy_shim if driver is agy_runipd else agent),
                    ),
                    mock.patch.object(
                        driver, "driver_begin", side_effect=counting("begin", (0, "ok"))
                    ),
                    mock.patch.object(
                        driver,
                        "driver_finalize",
                        side_effect=counting("finalize", (0, "ok")),
                    ),
                    mock.patch.object(
                        driver,
                        "run_suite_check",
                        side_effect=counting("suite", None),
                    ),
                ):
                    driver.execute_item(run_dir, state, state["queue"][0], False)

                self.assertEqual(
                    calls,
                    {},
                    f"a review must call none of begin/finalize/suite-check; called {calls!r}",
                )


# ======================================================================================
# V-06 / V-11: parity, and the sweep lane's refresh policy (OQ-04 option (a))
# ======================================================================================


class TheSweepLaneRefreshPolicy(unittest.TestCase):
    def test_the_lane_is_FAST_FORWARDED_to_main_between_reviews(self):
        """OQ-04 option (a): the measured staleness defect (F-14) is closed by a refresh."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-test")
            lane = Path(handle.path)
            self.assertEqual(
                (lane / "PEER.md").read_text(encoding="utf-8"), "peer v1\n"
            )
            # MAIN ADVANCES, exactly as it does when a previous review's merge lands.
            fx.peer.write_text("peer v2\n", encoding="utf-8")
            _git(fx.root, "add", "PEER.md")
            _git(fx.root, "commit", "-qm", "main advances")

            result = runner_shared.refresh_sweep_lane(fx.root, handle)
            self.assertTrue(result.refreshed, result.reason)
            self.assertEqual(
                (lane / "PEER.md").read_text(encoding="utf-8"),
                "peer v2\n",
                "the refreshed lane must read main's CURRENT bytes, not its sweep-start snapshot",
            )

    def test_an_ALREADY_CURRENT_lane_is_a_no_op_and_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-test")
            result = runner_shared.refresh_sweep_lane(fx.root, handle)
            self.assertFalse(result.refreshed)
            self.assertTrue(result.already_current)

    def test_a_DIRTY_lane_is_left_EXACTLY_as_it_is(self):
        """A review's in-flight edits must never be overwritten by a refresh."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-test")
            lane = Path(handle.path)
            (lane / "PEER.md").write_text(
                "an in-flight review edit\n", encoding="utf-8"
            )
            fx.peer.write_text("peer v2\n", encoding="utf-8")
            _git(fx.root, "add", "PEER.md")
            _git(fx.root, "commit", "-qm", "main advances")

            result = runner_shared.refresh_sweep_lane(fx.root, handle)
            self.assertFalse(result.refreshed)
            self.assertIn("UNCOMMITTED", result.reason)
            self.assertEqual(
                (lane / "PEER.md").read_text(encoding="utf-8"),
                "an in-flight review edit\n",
            )

    def test_a_DIVERGED_lane_REFUSES_rather_than_rewriting_history(self):
        """`--ff-only`, never rebase/reset: the lane may hold a review whose merge has not landed."""
        with tempfile.TemporaryDirectory() as tmp:
            fx = _Fixture(Path(tmp) / "repo", plans=1)
            handle = runner_shared.allocate_review_sweep_worktree(fx.root, "run-test")
            lane = Path(handle.path)
            (lane / "LANE_ONLY.md").write_text("lane work\n", encoding="utf-8")
            _git(lane, "add", "LANE_ONLY.md")
            _git(lane, "commit", "-qm", "lane commits something main lacks")
            lane_head = _git(lane, "rev-parse", "HEAD").strip()
            fx.peer.write_text("peer v2\n", encoding="utf-8")
            _git(fx.root, "add", "PEER.md")
            _git(fx.root, "commit", "-qm", "main advances too")

            result = runner_shared.refresh_sweep_lane(fx.root, handle)
            self.assertFalse(result.refreshed)
            self.assertEqual(
                _git(lane, "rev-parse", "HEAD").strip(),
                lane_head,
                "a diverged lane's own commit must be untouched",
            )

    def test_the_sweep_lane_id_is_RUN_scoped_and_not_an_item_id6(self):
        """The lane belongs to the RUN, so two concurrent runs cannot fight over one lane."""
        a = runner_shared.review_sweep_lane_id("run-A")
        b = runner_shared.review_sweep_lane_id("run-B")
        self.assertNotEqual(a, b)
        self.assertTrue(runner_shared.is_review_sweep_lane_id(a))
        self.assertFalse(runner_shared.is_review_sweep_lane_id("rev001"))

    def test_an_INTERRUPTED_sweeps_lane_is_DISCOVERABLE_by_the_reclaimer(self):
        """E-11's interrupt case: a lane no attempt recorded must still be found.

        A run interrupted BETWEEN reviews leaves a sweep lane whose identity is not an item id6, so the
        per-item reader alone would not see it and the lane would be leaked with no owner.
        """
        state = {
            "queue": [],
            runner_shared.REVIEW_SWEEP_LANE_KEY: {
                "lane_id": "review-sweep-run-test",
                "branch": "aw/lane/review-sweep-run-test",
                "worktree": "/tmp/nope",
                "base_commit": "deadbeef",
            },
        }
        records = runner_shared.lane_records_including_sweep(state)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["branch"], "aw/lane/review-sweep-run-test")
        # A RETIRED lane is NOT reported: there is nothing left to reclaim.
        state[runner_shared.REVIEW_SWEEP_LANE_KEY]["retired"] = True
        self.assertEqual(runner_shared.lane_records_including_sweep(state), [])

    def test_both_drivers_read_lanes_through_the_SWEEP_AWARE_composer(self):
        """A one-driver-only fix must FAIL: a leaked lane on one host is still a leaked lane.

        DRIVEN, NOT GREPPED, and the three halves are deliberate because each catches a distinct way
        the claim can be false. A previous version asserted `"lane_records_including_sweep" in
        inspect.getsource(driver.reclaim_lanes_on_interrupt)`, which a COMMENT satisfies: the real
        function carries a five-line comment naming that very symbol, so the pin would have stayed
        green with the call itself deleted.

          (a) IDENTITY - both hosts resolve the composer to ONE object, so a re-fork fails here.
          (b) CALLED - a REAL `reclaim_lanes_on_interrupt` on each host invokes it, with a spy that
              returns a lane record the per-item reader does NOT produce. Binding the shared name
              and never reaching it fails here.
          (c) THE ANSWER IS SURFACED - the spied record's lane id comes back in the returned lane
              list and the lane really is reclaimed, so a host that calls the composer and then
              rebuilds the lane set from somewhere else fails here too.

        THE FIXTURE IS THE INTERRUPT CASE THE COMPOSER EXISTS FOR (E-11): a sweep lane recorded at
        RUN level with NO attempt naming it. `_lane_records_from_state` is asserted to return `[]`
        for that state first, so "the reclaimer found the lane" cannot be satisfied by the per-item
        reader and can only come from the sweep-aware composer.
        """
        for name, driver in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                # (a) ONE DEFINITION, reached identically by both hosts.
                self.assertIs(
                    driver.runner_shared.lane_records_including_sweep,
                    runner_shared.lane_records_including_sweep,
                    f"{name} must reach the SHARED composer, not a per-host copy",
                )

                fx = _Fixture(Path(tmp) / "repo", plans=1)
                run_dir = _mk_run_dir(fx.root)
                handle = runner_shared.allocate_review_sweep_worktree(
                    fx.root, f"run-{name}"
                )
                state = {
                    "queue": [],
                    "run_id": f"run-{name}",
                    "repo": str(fx.root),
                    runner_shared.REVIEW_SWEEP_LANE_KEY: {
                        "lane_id": handle.lane_id,
                        "branch": handle.branch,
                        "worktree": str(handle.path),
                        "base_commit": handle.base_commit,
                    },
                }
                # THE PER-ITEM READER IS BLIND TO IT, which is what makes the rest non-vacuous.
                self.assertEqual(runner_shared._lane_records_from_state(state), [])

                calls: list[dict] = []
                real = runner_shared.lane_records_including_sweep

                def spy(st, _calls=calls, _real=real):
                    _calls.append(st)
                    return _real(st)

                with mock.patch.object(
                    runner_shared, "lane_records_including_sweep", spy
                ):
                    lanes = driver.reclaim_lanes_on_interrupt(
                        fx.root, run_dir, state, interactive=False
                    )

                # (b) the shared composer was actually REACHED during a real invocation.
                self.assertEqual(
                    len(calls),
                    1,
                    f"{name} never called the sweep-aware composer during a real reclaim",
                )
                # (c) and its answer is what the reclaimer acted on and returned.
                self.assertEqual(
                    [lane["lane_id"] for lane in lanes],
                    [handle.lane_id],
                    f"{name} did not surface the composer's sweep lane; got {lanes!r}",
                )
                self.assertEqual(lanes[0]["action"], "reclaimed")
                self.assertNotIn("review-sweep", fx.worktrees())


class TheSharedDefinitionsAreShared(unittest.TestCase):
    def test_the_review_lane_helpers_have_exactly_one_definition(self):
        """Spec `7ckptx` R2.6/R6.1: a containment rule implemented per host is a forked rule."""
        for symbol in (
            "acquire_review_sweep_lane",
            "retire_review_sweep_lane",
            "refresh_sweep_lane",
            "classify_review_writes",
            "commit_review_lane_output",
            "turn_runs_in_review_sweep_lane",
        ):
            with self.subTest(symbol=symbol):
                self.assertTrue(hasattr(runner_shared, symbol))
                for name, driver in _DRIVERS:
                    defined = [
                        n
                        for n in ast.parse(
                            Path(str(driver.__file__)).read_text(encoding="utf-8")
                        ).body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and n.name == symbol
                    ]
                    self.assertEqual(
                        defined, [], f"{name} must not redefine `{symbol}`"
                    )

    def test_the_teardown_gate_is_the_EXISTING_shared_one(self):
        """No second classifier: `teardown_review_sweep_lane` delegates to the spec-R5.5 gate.

        DRIVEN, NOT GREPPED. A source search for `teardown_lane_if_classified` is satisfied by the
        function's own docstring, which names that gate twice in prose ("delegates to the EXISTING
        `teardown_lane_if_classified` gate (spec R5.5)"), so the pin would have stayed green with the
        delegation replaced by a second inline classifier.

        SPY PLUS SENTINEL, because the gate RETURNS the verdict the caller surfaces: patch it to
        return a decision no real inventory of this empty lane could produce (a refusal naming
        `SENTINEL.txt`) and assert that exact object comes back. A caller that reached the gate and
        then recomputed its own answer fails on the sentinel; one that never reached it fails on the
        call count.

        THE `items=None` PATH IS THE DELEGATING ONE and is what this asserts. With `items` supplied,
        the function legitimately runs the SAME `inventory_lane` per item and then removes directly
        (the union rule in its docstring), so it does not call the single-item gate at all; that
        branch's refusal behavior is covered by `TheSweepRunsInOneLaneAndMainIsUntouched` and by
        `tests/test_lane_retention.py`.
        """
        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp) / "lane"
            lane.mkdir()
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            handle = SimpleNamespace(
                path=lane,
                branch="aw/lane/review-sweep-run-test",
                lane_id="review-sweep-run-test",
                base_commit="0" * 40,
                disposition="created",
            )
            sentinel = lane_containment.LaneTeardownDecision(
                torn_down=False,
                inventory=lane_containment.LaneInventory(
                    lane_root=str(lane),
                    readable=True,
                    unknown_untracked=("SENTINEL.txt",),
                ),
            )
            calls: list[dict] = []

            def spy(**kwargs):
                calls.append(kwargs)
                return sentinel

            with mock.patch.object(
                lane_containment, "teardown_lane_if_classified", spy
            ):
                decision = lane_containment.teardown_review_sweep_lane(
                    repo=Path(tmp), handle=handle, run_dir=run_dir
                )

            self.assertEqual(
                len(calls),
                1,
                "the sweep teardown must consult the ONE shared R5.5 gate, exactly once",
            )
            self.assertIs(
                decision,
                sentinel,
                "the gate's verdict must be the answer, not recomputed by a second classifier",
            )
            self.assertIn("SENTINEL.txt", decision.reason)
            # The lane it was asked about is the one handed in, so the delegation is not to some
            # other lane's gate call.
            self.assertIs(calls[0]["handle"], handle)
            self.assertEqual(calls[0]["run_dir"], run_dir)


if __name__ == "__main__":
    unittest.main()
