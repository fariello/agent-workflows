"""Defect report contracts, validator, prompt demand, and rescore logic."""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, reporting_contract as RC
from agent_workflows import runner_shared as R

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVERS = (oc_runipd, agy_runipd)


def _outcome(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": 1,
        "disposition": "executed",
        "summary": "did the thing",
        "incomplete_requirements": [],
        "pushed": False,
    }
    base.update(over)
    return base


class SchemaTests(unittest.TestCase):
    def test_states_and_absence(self) -> None:
        self.assertEqual(
            R.DEFECT_REPORT_STATES,
            (
                R.DEFECT_REPORT_FOUND,
                R.DEFECT_REPORT_NONE_FOUND,
                R.DEFECT_REPORT_ABSENT,
            ),
        )
        self.assertEqual(len(set(R.DEFECT_REPORT_STATES)), 3)
        none_found = R.validate_defect_report(
            _outcome(defect_report={"state": "none-found", "findings": []})
        )
        absent = R.validate_defect_report(_outcome())
        self.assertEqual(none_found.state, R.DEFECT_REPORT_NONE_FOUND)
        self.assertEqual(absent.state, R.DEFECT_REPORT_ABSENT)
        self.assertFalse(none_found.needs_reask)
        self.assertTrue(absent.needs_reask)

    def test_schema_literal(self) -> None:
        self.assertEqual(R.DEFECT_FINDING_KEYS, ("what", "where"))
        literal = R.defect_report_schema_literal()
        parsed = json.loads("{" + literal.rstrip(",") + "}")
        report = parsed[R.DEFECT_REPORT_KEY]
        self.assertEqual(sorted(report), ["findings", "state"])
        self.assertEqual(sorted(report["findings"][0]), ["what", "where"])
        self.assertIsInstance(report["findings"], list)
        self.assertIsInstance(report["findings"][0], dict)
        self.assertIn('"what":', literal)
        self.assertIn('"where":', literal)
        element = report["findings"][0]
        self.assertTrue(element["what"].strip())
        self.assertTrue(element["where"].strip())


class PromptDemandTests(unittest.TestCase):
    def _prompt(self, mod: Any) -> str:
        return mod.build_prompt(
            {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []},
            {"run_id": "run-x", "repo": "."},
            Path("/tmp/r"),
            Path("/tmp/p.md"),
            False,
        )

    def test_prompt_demand_block_content(self) -> None:
        flat = " ".join(R.defect_report_prompt_block().split())
        self.assertIn("Finding NOTHING is a REPORTABLE RESULT", flat)
        self.assertIn("must state affirmatively", flat)
        self.assertIn("Omitting the report is not the same answer", flat)
        self.assertIn("beyond this plan's own unmet requirements", flat)
        self.assertIn("bug in adjacent code", flat)
        self.assertIn("gap between a spec and its implementation", flat)
        self.assertIn("design concern you had to work around", flat)
        self.assertIn("FILE A BACKLOG ITEM with `aw backlog new`", flat)
        self.assertIn("a spec is supporting material and is NEVER the carrier", flat)
        self.assertIn("reporting outranks filing", flat)

        low = R.defect_report_prompt_block().lower()
        for forbidden in (
            "just a spec",
            "if it is only a spec",
            "decide whether a spec",
        ):
            self.assertNotIn(forbidden, low)

    def test_prompt_integration_and_format(self) -> None:
        block = R.defect_report_prompt_block()
        for mod in DRIVERS:
            prompt = self._prompt(mod)
            self.assertIn(block, prompt, mod.__name__)
            self.assertIn('"incomplete_requirements": [],', prompt)
            start = prompt.find(RC.REPORTING_SECTION_TITLE)
            self.assertGreater(start, -1, mod.__name__)
            self.assertEqual(
                prompt[start:].strip("\n"),
                RC.contract_text().strip("\n"),
                f"{mod.__name__}: text was added AFTER the reporting contract",
            )
            bad = sorted({c for c in prompt if ord(c) > 127})
            self.assertEqual(bad, [], f"{mod.__name__}: {bad}")


class ValidatorTests(unittest.TestCase):
    def test_valid_and_coerced_reports(self) -> None:
        v_a = R.validate_defect_report(
            _outcome(
                defect_report={
                    "state": "found",
                    "findings": [{"what": "leaks a fd", "where": "mod.py:12"}],
                }
            )
        )
        self.assertEqual(v_a.verdict, R.DEFECT_VERDICT_VALID)
        self.assertEqual(v_a.state, R.DEFECT_REPORT_FOUND)
        self.assertFalse(v_a.needs_reask)

        v_b = R.validate_defect_report(
            _outcome(defect_report={"state": "none-found", "findings": []})
        )
        self.assertEqual(v_b.verdict, R.DEFECT_VERDICT_VALID)
        self.assertEqual(v_b.state, R.DEFECT_REPORT_NONE_FOUND)
        self.assertFalse(v_b.needs_reask)

        v_d = R.validate_defect_report(
            _outcome(
                defect_report={
                    "state": "found",
                    "findings": ["run_viewer mis-renders a null cost"],
                }
            )
        )
        self.assertEqual(v_d.verdict, R.DEFECT_VERDICT_COERCED)
        self.assertEqual(v_d.state, R.DEFECT_REPORT_FOUND)
        self.assertEqual(
            v_d.findings,
            (
                {
                    "what": "run_viewer mis-renders a null cost",
                    "where": R.DEFECT_WHERE_UNSPECIFIED,
                },
            ),
        )
        self.assertTrue(v_d.coerced)
        self.assertFalse(v_d.needs_reask)

        v_label = R.validate_defect_report(
            _outcome(
                defect_report={
                    "state": "none-found",
                    "findings": [{"what": "x", "where": "y"}],
                }
            )
        )
        self.assertEqual(v_label.state, R.DEFECT_REPORT_FOUND)
        self.assertTrue(v_label.coerced)

    def test_absent_and_ambiguous_reports(self) -> None:
        v_absent = R.validate_defect_report(_outcome())
        self.assertEqual(v_absent.verdict, R.DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS)
        self.assertEqual(v_absent.state, R.DEFECT_REPORT_ABSENT)
        self.assertTrue(v_absent.needs_reask)

        v_empty = R.validate_defect_report(_outcome(defect_report={}))
        self.assertEqual(v_empty.verdict, R.DEFECT_VERDICT_ABSENT_OR_AMBIGUOUS)
        self.assertTrue(v_empty.needs_reask)

        v_nofindings = R.validate_defect_report(
            _outcome(defect_report={"state": "found", "findings": []})
        )
        self.assertTrue(v_nofindings.needs_reask)
        self.assertIn("what was found is unknown", v_nofindings.violation)

    def test_validator_never_raises(self) -> None:
        for junk in (
            None,
            "",
            "nothing to report",
            [],
            [{"what": "a"}],
            0,
            3.5,
            True,
            {"defect_report": []},
            {"defect_report": "found a thing"},
            {"defect_report": 7},
            {"defect_report": {"state": None, "findings": None}},
            {"defect_report": {"findings": [None, {}, "", 5]}},
            {"defect_report": {"state": "FOUND", "findings": {"what": "x"}}},
        ):
            with self.subTest(junk=junk):
                v = R.validate_defect_report(junk)
                self.assertIn(v.verdict, R.DEFECT_VERDICTS)
                self.assertIn(v.state, R.DEFECT_REPORT_STATES)


class ReaskPredicateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.absent = R.validate_defect_report(_outcome())
        self.usable = R.validate_defect_report(
            _outcome(defect_report={"state": "none-found", "findings": []})
        )

    def test_reask_warranted_predicates(self) -> None:
        ok, why = R.defect_reask_is_warranted(
            self.absent, disposition="executed", session_id="ses-1"
        )
        self.assertTrue(ok, why)

        ok, why = R.defect_reask_is_warranted(
            self.usable, disposition="executed", session_id="ses-1"
        )
        self.assertFalse(ok)
        self.assertIn("usable", why)

        for disposition in sorted(R.DEFECT_REASK_SKIPPED_STATUSES):
            with self.subTest(disposition=disposition):
                ok, why = R.defect_reask_is_warranted(
                    self.absent, disposition=disposition, session_id="ses-1"
                )
                self.assertFalse(ok, disposition)
                self.assertIn("no reportable work", why)

        ok, why = R.defect_reask_is_warranted(
            self.absent, disposition="executed", session_id=None
        )
        self.assertFalse(ok)
        self.assertIn("no resumable session", why)

        ok, why = R.defect_reask_is_warranted(
            self.absent,
            disposition="executed",
            session_id="ses-1",
            already_reasked=True,
        )
        self.assertFalse(ok)
        self.assertIn("already been spent", why)

    def test_reask_turn_count_and_budget(self) -> None:
        counts: dict[str, int] = {"ses-1": 2}
        R.perform_defect_reask(
            verdict=self.absent,
            prompt_path=Path("/tmp/does-not-matter.md"),
            outcome_path=None,
            resume=lambda _p: (0, "ses-1", Path("/tmp/l"), ["x"]),
            session_turn_counts=counts,
            session_id="ses-1",
        )
        self.assertEqual(counts["ses-1"], 3)


class ReaskMessageTests(unittest.TestCase):
    def test_reask_message_generation(self) -> None:
        v = R.validate_defect_report(
            _outcome(defect_report={"state": "found", "findings": []})
        )
        msg = R.defect_reask_message(v)
        self.assertIn("what was found is unknown", msg)
        self.assertIn("defect_report", msg)
        self.assertIn(R.defect_report_schema_literal().strip(), msg)


class ReaskExecutionTests(unittest.TestCase):
    def _write(self, tmp: Path, payload: Any) -> Path:
        path = tmp / "01-abc123.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_reask_execution_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            outcome_path = self._write(tmp, _outcome())
            calls: list[Path] = []

            def resume_good(prompt_path: Path) -> tuple[int, str, Path, list[str]]:
                calls.append(prompt_path)
                outcome_path.write_text(
                    json.dumps(
                        _outcome(
                            defect_report={
                                "state": "found",
                                "findings": [{"what": "a bug", "where": "x.py"}],
                            }
                        )
                    ),
                    encoding="utf-8",
                )
                return 0, "ses-1", tmp / "log", ["stub"]

            before = R.validate_defect_report(
                json.loads(outcome_path.read_text(encoding="utf-8"))
            )
            self.assertTrue(before.needs_reask)
            after, rc = R.perform_defect_reask(
                verdict=before,
                prompt_path=tmp / "reask.md",
                outcome_path=outcome_path,
                resume=resume_good,
            )
            self.assertEqual(len(calls), 1)
            self.assertEqual(rc, 0)
            self.assertEqual(after.state, R.DEFECT_REPORT_FOUND)
            self.assertFalse(after.needs_reask)

        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            outcome_path = self._write(tmp, _outcome())
            calls_fruitless = []

            def resume_fruitless(prompt_path: Path) -> tuple[int, str, Path, list[str]]:
                calls_fruitless.append(prompt_path)
                return 0, "ses-1", tmp / "log", ["stub"]

            before = R.validate_defect_report(
                json.loads(outcome_path.read_text(encoding="utf-8"))
            )
            after, _rc = R.perform_defect_reask(
                verdict=before,
                prompt_path=tmp / "reask.md",
                outcome_path=outcome_path,
                resume=resume_fruitless,
            )
            self.assertEqual(len(calls_fruitless), 1)
            self.assertTrue(after.needs_reask)
            record = R.defect_report_record(
                before, reasked=True, reask_reason="absent", reask_verdict=after
            )
            self.assertTrue(record["reasked"])
            self.assertEqual(record["state"], R.DEFECT_REPORT_ABSENT)
            self.assertEqual(record["reask_state"], R.DEFECT_REPORT_ABSENT)

    def test_reask_error_resilience(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tmp = Path(temp)
            bad = tmp / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            self.assertIsNone(R.read_defect_report_outcome(bad))
            self.assertIsNone(R.read_defect_report_outcome(tmp / "absent.json"))
            self.assertIsNone(R.read_defect_report_outcome(None))

            outcome_path = self._write(tmp, _outcome())

            def boom() -> None:
                raise RuntimeError("collection failed")

            after, _rc = R.perform_defect_reask(
                verdict=R.validate_defect_report(_outcome()),
                prompt_path=tmp / "reask.md",
                outcome_path=outcome_path,
                resume=lambda _p: (0, "s", tmp / "l", ["x"]),
                recollect=boom,
            )
            self.assertTrue(after.needs_reask)


class HostResumeSpellingTests(unittest.TestCase):
    def _argv(self, driver: Any) -> list[str]:
        captured: dict[str, list[str]] = {}

        def fake_popen(argv: Any, **_kw: Any) -> Any:
            captured["argv"] = list(argv)
            raise RuntimeError("stop-before-launch")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True
            )
            run_dir = root / "run"
            (run_dir / "sessions").mkdir(parents=True)
            prompt = root / "reask.md"
            prompt.write_text("answer the report question\n", encoding="utf-8")
            plan = repo / "plan.ipd.md"
            plan.write_text("- Id: abc123\n", encoding="utf-8")
            state = {
                "run_id": "run-x",
                "repo": str(repo),
                "set_sessions": {},
                "session_turn_counts": {},
                "options": {"opencode": "/bin/false", "agy_executable": "/bin/false"},
                "queue": [],
            }
            item = {
                "id6": "abc123",
                "setid": "demo",
                "position": 1,
                "action": "execute",
            }
            import subprocess as _sp

            real = _sp.Popen
            _sp.Popen = fake_popen  # type: ignore[assignment]
            try:
                if driver is oc_runipd:
                    driver.run_opencode(
                        state, run_dir, item, plan, prompt, 1, resume_session="ses-1"
                    )
                else:
                    driver.run_agy_turn(
                        state,
                        run_dir,
                        item,
                        prompt,
                        1,
                        session_id="ses-1",
                        use_continue=False,
                    )
            except Exception:
                pass
            finally:
                _sp.Popen = real  # type: ignore[assignment]
        return captured.get("argv", [])

    def test_opencode_resumes_with_session(self) -> None:
        argv = self._argv(oc_runipd)
        self.assertIn("--session", argv)
        self.assertEqual(argv[argv.index("--session") + 1], "ses-1")

    def test_antigravity_resumes_with_conversation(self) -> None:
        argv = self._argv(agy_runipd)
        self.assertIn("--conversation", argv)
        self.assertEqual(argv[argv.index("--conversation") + 1], "ses-1")
        self.assertNotIn("--session", argv)


class PersistedRecordTests(unittest.TestCase):
    def _record(self, report: Any = "omit", **kw: Any) -> dict[str, Any]:
        outcome = _outcome() if report == "omit" else _outcome(defect_report=report)
        return R.defect_report_record(R.validate_defect_report(outcome), **kw)

    def test_persisted_record_facts_and_serialization(self) -> None:
        record = self._record({"state": "found", "findings": ["a bare one"]})
        self.assertEqual(
            sorted(record),
            [
                "coerced",
                "coercions",
                "findings",
                "reask_reason",
                "reask_state",
                "reask_verdict",
                "reasked",
                "state",
                "verdict",
            ],
        )
        self.assertEqual(record["state"], R.DEFECT_REPORT_FOUND)
        self.assertTrue(record["coerced"])
        self.assertTrue(record["coercions"])
        self.assertFalse(record["reasked"])
        json.dumps(self._record({"state": "found", "findings": ["x"]}))
        json.dumps(self._record())

    def test_none_found_and_absent_differ_on_disk(self) -> None:
        none_found = self._record({"state": "none-found", "findings": []})
        absent = self._record()
        found = self._record(
            {"state": "found", "findings": [{"what": "x", "where": "y"}]}
        )
        a = json.dumps(none_found, sort_keys=True)
        b = json.dumps(absent, sort_keys=True)
        c = json.dumps(found, sort_keys=True)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(b, c)
        self.assertEqual(none_found["state"], R.DEFECT_REPORT_NONE_FOUND)
        self.assertEqual(absent["state"], R.DEFECT_REPORT_ABSENT)


class RescorePredicateTests(unittest.TestCase):
    def test_rescore_rank_logic(self) -> None:
        from agent_workflows import runner_stop

        # Improvements
        for before, after in (
            ("partial", "substantially-complete"),
            ("partial", "executed"),
            ("failed-safely", "substantially-complete"),
            ("failed-safely", "executed"),
            ("substantially-complete", "executed"),
        ):
            with self.subTest(case="improvement", before=before, after=after):
                self.assertTrue(R.rescore_is_an_improvement(before, after))

        # Equal
        for status in (
            "partial",
            "substantially-complete",
            "executed",
            "failed-safely",
        ):
            with self.subTest(case="equal", status=status):
                self.assertFalse(R.rescore_is_an_improvement(status, status))

        # Downgrades
        for before, after in (
            ("substantially-complete", "partial"),
            ("executed", "partial"),
            ("executed", "substantially-complete"),
            ("executed", "failed-safely"),
            ("partial", "failed-safely"),
        ):
            with self.subTest(case="downgrade", before=before, after=after):
                self.assertFalse(R.rescore_is_an_improvement(before, after))

        # Never replaceable
        never = (
            R.INTEGRATION_DEFERRED_STATUS,
            runner_stop.STOPPED_DISPOSITION,
            runner_stop.FORCED_DISPOSITION,
        )
        for status in never:
            for other in (
                "partial",
                "substantially-complete",
                "executed",
                "failed-safely",
            ):
                with self.subTest(case="never-replaceable", status=status, other=other):
                    self.assertFalse(R.rescore_is_an_improvement(status, other))
                    self.assertFalse(R.rescore_is_an_improvement(other, status))

        # Unrecognized
        for before, after in (
            ("partial", "a-status-nobody-ranked"),
            ("a-status-nobody-ranked", "executed"),
            (None, "executed"),
            ("partial", None),
            ("", ""),
        ):
            with self.subTest(case="unrecognized", before=before, after=after):
                self.assertFalse(R.rescore_is_an_improvement(before, after))

    def test_no_argument_or_table_mutation(self) -> None:
        before_table = dict(R.RESCORE_DISPOSITION_RANK)
        args = ["partial", "executed"]
        R.rescore_is_an_improvement(args[0], args[1])
        self.assertEqual(args, ["partial", "executed"])
        self.assertEqual(R.RESCORE_DISPOSITION_RANK, before_table)


class RescoreAfterAReaskTests(unittest.TestCase):
    PLAN = (
        "# IPD: rescore fixture\n\n"
        "- Date: 2026-09-19\n"
        "- Kind: child\n"
        "- Id: prb001\n"
        "- Set: reask\n"
        "- Order: 1\n"
        "- Status: approved\n\n"
        "## Goal\n\nfixture\n"
    )

    GOOD = {
        "schema_version": 1,
        "disposition": "executed",
        "summary": "did the whole job",
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }
    REASK_COMPLETE = GOOD
    NO_REPORT_PARTIAL = {
        "schema_version": 1,
        "disposition": "partial",
        "summary": "got part way",
        "pushed": False,
    }
    REASK_STILL_PARTIAL = {
        "schema_version": 1,
        "disposition": "partial",
        "summary": "still only part way",
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }

    def _git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
        if proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} in {repo}: {proc.stderr}")
        return proc.stdout

    def _fixture(self, root: Path):
        repo = root / "repo"
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        self._git(root, "init", "-q", str(repo))
        self._git(repo, "config", "user.email", "t@example.invalid")
        self._git(repo, "config", "user.name", "t")
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n",
            encoding="utf-8",
        )
        plan = (
            repo
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260919-reask-01-prb001-rescore-fixture.ipd.md"
        )
        plan.write_text(self.PLAN, encoding="utf-8")
        self._git(repo, "add", ".gitignore", str(plan.relative_to(repo)))
        self._git(repo, "commit", "-qm", "init")
        run_dir = repo / ".aw" / "records" / "runs" / "run-rescore"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        item = {
            "position": 1,
            "id6": "prb001",
            "setid": "reask",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-rescore",
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "selectors": ["reask"],
            "options": {
                "opencode": "/bin/false",
                "agy_executable": "/bin/false",
                "model": "probe",
                "self_finalize": True,
                "no_audit": True,
                "isolate_worktree": True,
                "allow_dirty_base": True,
            },
        }
        return repo, run_dir, state, item

    def _suite(self, passing: bool = True):
        return oc_runipd.SuiteCheckResult(
            passing=passing,
            exit_code=0 if passing else 1,
            summary=("7081 passed in 97.10s" if passing else "1 failed, 7080 passed"),
            reason="stub",
            cwd="/primary",
            timeout_seconds=oc_runipd.SUITE_CHECK_TIMEOUT_SECONDS,
            elapsed_seconds=98.49,
            failures=(
                () if passing else ("FAILED tests/test_x.py::test_y - assert 1 == 2",)
            ),
        )

    def _drive(
        self,
        root: Path,
        *,
        first_outcome: dict[str, Any] | None,
        reask_outcome: dict[str, Any] | None,
        wrap_collect: Any = None,
        reconcile: Any = None,
    ):
        from agent_workflows import lane_containment

        repo, run_dir, state, item = self._fixture(root)
        launches: list[dict[str, Any]] = []
        gate_kwargs: dict[str, Any] = {}

        def _lane_write(work_dir: Any, payload: dict[str, Any]) -> None:
            lane_root = lane_containment.lane_submission_root(
                Path(work_dir), state["run_id"], item, 1
            )
            target = lane_root / "outcomes" / f"{lane_containment.item_slug(item)}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload), encoding="utf-8")

        def _launch(*args: Any, **kwargs: Any):
            launches.append(kwargs)
            payload = first_outcome if len(launches) == 1 else reask_outcome
            work_dir = kwargs.get("work_dir")
            if payload is not None and work_dir:
                _lane_write(work_dir, payload)
            return 0, "ses-1", run_dir / "log.jsonl", ["probe"]

        def _gate(**kwargs: Any):
            gate_kwargs.update(kwargs)
            return oc_runipd.IntegrationVerdict(
                False,
                oc_runipd.INTEGRATION_REFUSED_NO_SIGNAL,
                "stub: refusal kept in place so no merge is performed",
            )

        patches = [
            mock.patch.object(oc_runipd, "run_opencode", _launch),
            mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
            mock.patch.object(oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")),
            mock.patch.object(
                oc_runipd, "assert_child_tool_identity", lambda *a, **k: None
            ),
            mock.patch.object(oc_runipd, "extract_suite_failures", None),
            mock.patch.object(
                oc_runipd, "run_suite_check", lambda *a, **k: self._suite(True)
            ),
            mock.patch.object(oc_runipd, "integration_is_earned", _gate),
        ]
        if wrap_collect is not None:
            patches.append(
                mock.patch.object(
                    lane_containment,
                    "collect_lane_submissions",
                    wrap_collect(lane_containment.collect_lane_submissions),
                )
            )
        if reconcile is not None:
            patches.append(
                mock.patch.object(oc_runipd, "reconcile_disposition", reconcile)
            )

        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            oc_runipd.execute_item(run_dir, state, item, recovery=False)

        events_path = run_dir / "events.jsonl"
        events = (
            [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if events_path.is_file()
            else []
        )
        return run_dir, state, item, events, gate_kwargs, launches

    @staticmethod
    def _rescored(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [e for e in events if e.get("event") == "ipd-rescored"]

    def test_the_MEASURED_case_is_rescued_instead_of_recorded_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=self.REASK_COMPLETE
            )
            self.assertEqual(2, len(launches))
            self.assertEqual("substantially-complete", item["status"])
            rescored = self._rescored(events)
            self.assertEqual(1, len(rescored))
            self.assertEqual(item["id6"], rescored[0]["id6"])
            self.assertEqual("partial", rescored[0]["before"])
            self.assertEqual("substantially-complete", rescored[0]["after"])

    def test_controls_refuse(self) -> None:
        from agent_workflows import lane_containment

        # Control A: failed receipt
        def wrap_a(real: Any) -> Any:
            def wrapper(**kwargs: Any) -> Any:
                receipt = real(**kwargs)
                path = lane_containment.collection_receipt_path(
                    kwargs["run_dir"], kwargs["item"], kwargs["attempt"]
                )
                data = json.loads(path.read_text(encoding="utf-8"))
                if "outcome" in (data.get("collected") or []):
                    data["collected"] = [
                        name for name in data["collected"] if name != "outcome"
                    ]
                    data["failed"] = sorted(set(data.get("failed", []) + ["outcome"]))
                    path.write_text(
                        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
                    )
                    return data
                return receipt

            return wrapper

        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp),
                first_outcome=None,
                reask_outcome=self.REASK_COMPLETE,
                wrap_collect=wrap_a,
            )
            self.assertEqual("partial", item["status"])
            self.assertEqual([], self._rescored(events))
            self.assertEqual(2, len(launches))

        # Control B: no receipt
        def wrap_b(real: Any) -> Any:
            def wrapper(**kwargs: Any) -> Any:
                receipt = real(**kwargs)
                lane_containment.collection_receipt_path(
                    kwargs["run_dir"], kwargs["item"], kwargs["attempt"]
                ).unlink(missing_ok=True)
                return receipt

            return wrapper

        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp),
                first_outcome=None,
                reask_outcome=self.REASK_COMPLETE,
                wrap_collect=wrap_b,
            )
            self.assertEqual("partial", item["status"])
            self.assertEqual([], self._rescored(events))
            self.assertEqual(2, len(launches))

        # Control C: absent outcome with complete receipt
        with tempfile.TemporaryDirectory() as temp:
            run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=None
            )
            receipt = lane_containment.read_collection_receipt(run_dir, item, 1)
            assert receipt is not None
            self.assertEqual(
                (lane_containment.RECEIPT_COMPLETE, [], []),
                (receipt["status"], receipt["collected"], receipt["failed"]),
            )
            self.assertEqual(2, len(launches))
            self.assertEqual("partial", item["status"])
            self.assertEqual([], self._rescored(events))

    def test_deferral_behavior(self) -> None:
        calls: list[int] = []

        def scripted(repo, item, run_dir, exit_code, plan_repo=None):
            calls.append(exit_code)
            if len(calls) == 1:
                return R.INTEGRATION_DEFERRED_STATUS, None
            return "substantially-complete", dict(self.GOOD)

        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp),
                first_outcome=None,
                reask_outcome=self.REASK_COMPLETE,
                reconcile=scripted,
            )
            self.assertEqual(2, len(launches))
            self.assertEqual(2, len(calls))
            self.assertEqual(R.INTEGRATION_DEFERRED_STATUS, item["status"])
            self.assertEqual([], self._rescored(events))

        # Negative control
        calls_neg: list[int] = []

        def scripted_neg(repo, item, run_dir, exit_code, plan_repo=None):
            calls_neg.append(exit_code)
            if len(calls_neg) == 1:
                return R.INTEGRATION_DEFERRED_STATUS, None
            return "substantially-complete", dict(self.GOOD)

        def rank_only(before: str | None, after: str | None) -> bool:
            ranks = dict(R.RESCORE_DISPOSITION_RANK)
            ranks[R.INTEGRATION_DEFERRED_STATUS] = 1
            b, a = ranks.get(before or ""), ranks.get(after or "")
            return b is not None and a is not None and a > b

        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(R, "rescore_is_an_improvement", rank_only):
                _run_dir, _state, item, events, _gate, _launches = self._drive(
                    Path(temp),
                    first_outcome=None,
                    reask_outcome=self.REASK_COMPLETE,
                    reconcile=scripted_neg,
                )
            self.assertEqual("substantially-complete", item["status"])
            self.assertEqual(1, len(self._rescored(events)))

    def test_carrier_agreement_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir, state, item, events, gate_kwargs, _launches = self._drive(
                Path(temp), first_outcome=None, reask_outcome=self.REASK_COMPLETE
            )
            attempt = item["attempts"][-1]
            collected = json.loads(
                (
                    run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("substantially-complete", item["status"])
            self.assertEqual("substantially-complete", attempt["disposition"])
            self.assertEqual(collected, item["last_outcome"])

            persisted = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            entry = next(q for q in persisted["queue"] if q["id6"] == item["id6"])
            self.assertEqual("substantially-complete", entry["status"])
            self.assertEqual(collected, entry["last_outcome"])
            self.assertIs(state["queue"][0], item)

            rescored = self._rescored(events)
            self.assertEqual(1, len(rescored))
            self.assertEqual(item["id6"], rescored[0]["id6"])
            self.assertEqual("partial", rescored[0]["before"])
            self.assertEqual("substantially-complete", rescored[0]["after"])

            self.assertEqual("substantially-complete", item["status"])
            self.assertFalse(gate_kwargs["validate"])
            self.assertIsNone(gate_kwargs["verify_disp"])
            self.assertTrue(gate_kwargs["suite_result"].passing)

        # No reask = no event
        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp), first_outcome=self.GOOD, reask_outcome=self.GOOD
            )
            self.assertEqual(1, len(launches))
            self.assertEqual("substantially-complete", item["status"])
            self.assertEqual([], self._rescored(events))

        # Reask not improvement = no event
        with tempfile.TemporaryDirectory() as temp:
            _run_dir, _state, item, events, _gate, launches = self._drive(
                Path(temp),
                first_outcome=self.NO_REPORT_PARTIAL,
                reask_outcome=self.REASK_STILL_PARTIAL,
            )
            self.assertEqual(2, len(launches))
            self.assertEqual("partial", item["status"])
            self.assertEqual([], self._rescored(events))


if __name__ == "__main__":
    unittest.main()
