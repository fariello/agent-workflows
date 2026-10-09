"""Behavioral tests for stale record Scope-Paths detection and dispatch refusal.

Plan 6h8j1r / backlog mlc6mj.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, artifact_core, check_engine, oc_runipd
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN, _init_repo_with_conforming_plan


class ScopePathTargetStaleTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)

    def test_01_predicate_moved_terminal_plan(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        self.assertIsNotNone(func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            executed = repo / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True)
            target_plan = executed / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n", encoding="utf-8"
            )
            declared_path = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )
            plan_text = (
                f"# IPD: Subject\n- Status: approved\n- Scope-Paths: {declared_path}\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path, declared_path)
            self.assertEqual(
                results[0].classification, check_engine.SCOPE_STALE_MOVED_TERMINAL
            )
            self.assertEqual(
                results[0].resolved, (target_plan.relative_to(repo).as_posix(),)
            )

    def test_02_predicate_moved_terminal_backlog(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        self.assertIsNotNone(func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            done_dir = repo / ".aw" / "records" / "backlog" / "done"
            done_dir.mkdir(parents=True)
            target_backlog = done_dir / "20260901-01-bkl001-target.backlog.md"
            target_backlog.write_text(
                "# Backlog: Target\n- Status: done\n- Id: bkl001\n", encoding="utf-8"
            )
            declared_path = (
                ".aw/records/backlog/open/20260901-01-bkl001-target.backlog.md"
            )
            plan_text = (
                f"# IPD: Subject\n- Status: approved\n- Scope-Paths: {declared_path}\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path, declared_path)
            self.assertEqual(
                results[0].classification, check_engine.SCOPE_STALE_MOVED_TERMINAL
            )
            self.assertEqual(
                results[0].resolved, (target_backlog.relative_to(repo).as_posix(),)
            )

    def test_03_predicate_moved_non_retired_spec(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        self.assertIsNotNone(func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            to_review = repo / ".aw" / "records" / "specs" / "to-review"
            to_review.mkdir(parents=True)
            target_spec = to_review / "20260901-spc001-01-spc001-target.spec.md"
            target_spec.write_text(
                "# Spec: Target\n- Status: to-review\n- Id: spc001\n", encoding="utf-8"
            )
            declared_path = (
                ".aw/records/specs/approved/20260901-spc001-01-spc001-target.spec.md"
            )
            plan_text = (
                f"# IPD: Subject\n- Status: approved\n- Scope-Paths: {declared_path}\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path, declared_path)
            self.assertEqual(results[0].classification, check_engine.SCOPE_STALE_MOVED)
            self.assertEqual(
                results[0].resolved, (target_spec.relative_to(repo).as_posix(),)
            )

    def test_04_predicate_vanished_records_path(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        self.assertIsNotNone(func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            declared_path = (
                ".aw/records/specs/approved/20260901-spc999-01-spc999-target.spec.md"
            )
            plan_text = (
                f"# IPD: Subject\n- Status: approved\n- Scope-Paths: {declared_path}\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path, declared_path)
            self.assertEqual(
                results[0].classification, check_engine.SCOPE_STALE_VANISHED
            )
            self.assertEqual(results[0].resolved, ())

    def test_05_predicate_non_records_path_ignored(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        if func is None:
            return
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            plan_text = (
                "# IPD: Subject\n- Status: approved\n"
                "- Scope-Paths: agent_workflows/new_module.py, tests/test_new.py\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(results, [])

    def test_06_predicate_glob_and_existing_dir_ignored(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        if func is None:
            return
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / ".aw" / "records" / "specs").mkdir(parents=True)
            plan_text = (
                "# IPD: Subject\n- Status: approved\n"
                "- Scope-Paths: .aw/records/plans/pending/**, .aw/records/specs/\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(results, [])

    def test_07_predicate_grandfathered_scope_paths(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        if func is None:
            return
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            plan_text = (
                "# IPD: Subject\n- Status: approved\n- Scope-Paths: grandfathered\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(results, [])

    def test_08_predicate_legacy_spec_basename_fallback(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        self.assertIsNotNone(func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            impl_dir = repo / ".aw" / "records" / "specs" / "implemented"
            impl_dir.mkdir(parents=True)
            target_spec = impl_dir / "20260815-1200-01-legacy-spec.spec.md"
            target_spec.write_text(
                "# Spec: Legacy\n- Status: implemented\n- Id: spcleg\n",
                encoding="utf-8",
            )
            declared_path = (
                ".aw/records/specs/approved/20260815-1200-01-legacy-spec.spec.md"
            )
            plan_text = (
                f"# IPD: Subject\n- Status: approved\n- Scope-Paths: {declared_path}\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path, declared_path)
            self.assertEqual(
                results[0].classification, check_engine.SCOPE_STALE_MOVED_TERMINAL
            )
            self.assertEqual(
                results[0].resolved, (target_spec.relative_to(repo).as_posix(),)
            )

    def test_09_check_scope_path_target_stale(self) -> None:
        check_func = getattr(check_engine, "check_scope_path_target_stale", None)
        self.assertIsNotNone(check_func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            executed = repo / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True)
            target_plan = executed / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n", encoding="utf-8"
            )
            declared_path = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            subj = pending / "20260902-subj-01-sub001-subj.ipd.md"
            subj_text = f"# IPD: Subj\n- Status: approved\n- Id: sub001\n- Scope-Paths: {declared_path}\n"
            subj.write_text(subj_text, encoding="utf-8")

            findings = check_func(repo)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].rule, "check.scope-path-target-stale")
            self.assertIn("moved-terminal", findings[0].detail)
            self.assertIn(declared_path, findings[0].detail)

            subj.unlink()
            subj_exec = executed / "20260902-subj-01-sub001-subj.ipd.md"
            subj_exec.write_text(subj_text, encoding="utf-8")
            self.assertEqual(check_func(repo), [])

    def test_10_dispatch_oc_host_refusal_moved_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")

            executed = repo / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True)
            target_plan = executed / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n", encoding="utf-8"
            )
            declared_stale = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )

            text = plan.read_text(encoding="utf-8")
            text = text.replace(
                "- Scope-Paths: src/", f"- Scope-Paths: {declared_stale}"
            )
            plan.write_text(text, encoding="utf-8")

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item = {
                "id6": "wir001",
                "setid": "demo",
                "order": 1,
                "position": 1,
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {
                    "self_finalize": False,
                    "isolate_worktree": False,
                },
            }

            def fail_launcher(*a, **k):
                raise AssertionError(
                    "run_opencode should not be called for refused item"
                )

            with mock.patch.object(oc_runipd, "run_opencode", fail_launcher):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-gate")
            self.assertIn(declared_stale, item.get("scope_target_refusal", ""))
            self.assertIn("attempts", item)
            self.assertNotIn("worktree", item["attempts"][-1])

            events_file = run_dir / "events.jsonl"
            self.assertTrue(events_file.exists())
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            stale_events = [e for e in events if e.get("event") == "scope-target-stale"]
            self.assertEqual(len(stale_events), 1)
            self.assertEqual(stale_events[0]["id6"], "wir001")
            self.assertIn(declared_stale, stale_events[0]["paths"])

    def test_11_dispatch_agy_host_refusal_moved_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")

            executed = repo / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True)
            target_plan = executed / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n", encoding="utf-8"
            )
            declared_stale = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )

            text = plan.read_text(encoding="utf-8")
            text = text.replace(
                "- Scope-Paths: src/", f"- Scope-Paths: {declared_stale}"
            )
            plan.write_text(text, encoding="utf-8")

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item = {
                "id6": "agy001",
                "setid": "demo",
                "order": 1,
                "position": 1,
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {
                    "self_finalize": False,
                    "isolate_worktree": False,
                },
            }

            def fail_launcher(*a, **k):
                raise AssertionError(
                    "run_agy_turn should not be called for refused item"
                )

            with mock.patch.object(agy_runipd, "run_agy_turn", fail_launcher):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-gate")
            self.assertIn(declared_stale, item.get("scope_target_refusal", ""))
            self.assertIn("attempts", item)
            self.assertNotIn("worktree", item["attempts"][-1])

            events_file = run_dir / "events.jsonl"
            self.assertTrue(events_file.exists())
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            stale_events = [e for e in events if e.get("event") == "scope-target-stale"]
            self.assertEqual(len(stale_events), 1)

    def test_12_dispatch_two_item_queue_run_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan1 = _init_repo_with_conforming_plan(repo, "wir001")

            plan2 = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260828-demo-02-wir002-demo.ipd.md"
            )
            plan2.write_text(_CONFORMING_PLAN.format(id6="wir002"), encoding="utf-8")

            executed = repo / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True)
            target_plan = executed / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n", encoding="utf-8"
            )
            declared_stale = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )
            text1 = plan1.read_text(encoding="utf-8")
            text1 = text1.replace(
                "- Scope-Paths: src/", f"- Scope-Paths: {declared_stale}"
            )
            plan1.write_text(text1, encoding="utf-8")

            import subprocess

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "setup"], cwd=repo, check=True)

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item1 = {
                "id6": "wir001",
                "setid": "demo",
                "order": 1,
                "position": 1,
                "status": "queued",
                "configured_file": str(plan1.relative_to(repo)),
                "action": "execute",
            }
            item2 = {
                "id6": "wir002",
                "setid": "demo",
                "order": 2,
                "position": 2,
                "status": "queued",
                "configured_file": str(plan2.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "schema_version": 1,
                "run_id": "run-test",
                "created_at": "2026-08-28T00:00:00+00:00",
                "updated_at": "2026-08-28T00:00:00+00:00",
                "selectors": ["demo"],
                "repo": str(repo),
                "queue": [item1, item2],
                "set_sessions": {},
                "session_id": None,
                "options": {
                    "opencode": "/bin/false",
                    "model": None,
                    "agent": None,
                    "auto": True,
                    "isolate_worktree": False,
                },
            }
            (run_dir / "state.json").write_text(
                json.dumps(state, indent=2), encoding="utf-8"
            )

            launched = []

            def fake_opencode(
                st, rdir, itm, plan_path, prompt_path, attempt_no, **kwargs
            ):
                launched.append(itm["id6"])
                outcome_file = (
                    rdir / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                )
                outcome_file.write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                v_outcome_file = (
                    rdir
                    / "outcomes"
                    / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                )
                v_outcome_file.write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": ["python3 -m unittest tests/test_foo.py"],
                        }
                    ),
                    encoding="utf-8",
                )
                if kwargs.get("fresh_session") or kwargs.get("log_suffix") == "verify":
                    return 0, "ses_verify", str(rdir / "log"), ["oc"]
                return 0, "ses", str(rdir / "log"), ["oc"]

            with (
                mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
                mock.patch.object(
                    oc_runipd, "driver_finalize", lambda *a, **k: (0, "ok")
                ),
                mock.patch.object(oc_runipd, "run_opencode", fake_opencode),
                mock.patch.object(oc_runipd, "run_suite_check", lambda *a, **k: True),
            ):
                oc_runipd.run_queue(run_dir, retry_incomplete=False)

            saved_state = oc_runipd.load_state(run_dir)
            q1 = saved_state["queue"][0]
            q2 = saved_state["queue"][1]
            self.assertEqual(q1["status"], "fail-gate")
            self.assertEqual(q2["status"], "executed")
            self.assertIn("wir002", launched)
            self.assertNotIn("wir001", launched)

    def test_13_dispatch_new_code_file_not_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")

            text = plan.read_text(encoding="utf-8")
            text = text.replace(
                "- Scope-Paths: src/", "- Scope-Paths: src/new_module.py"
            )
            plan.write_text(text, encoding="utf-8")

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item = {
                "id6": "wir001",
                "setid": "demo",
                "order": 1,
                "position": 1,
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {
                    "self_finalize": False,
                    "isolate_worktree": False,
                },
            }

            reached = []

            def fake_launcher(*a, **k):
                reached.append(True)
                return 0, "ses", str(run_dir / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_launcher):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertTrue(reached)
            self.assertNotEqual(item["status"], "fail-gate")

    def test_14_dispatch_moved_negative_reaches_launcher_and_check_reports(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")

            impl = repo / ".aw" / "records" / "specs" / "implementing"
            impl.mkdir(parents=True)
            target_spec = impl / "20260901-spc001-01-spc001-sample.spec.md"
            target_spec.write_text(
                "# Spec: Sample\n- Status: implementing\n- Id: spc001\n",
                encoding="utf-8",
            )
            declared_stale = (
                ".aw/records/specs/approved/20260901-spc001-01-spc001-sample.spec.md"
            )

            text = plan.read_text(encoding="utf-8")
            text = text.replace(
                "- Scope-Paths: src/", f"- Scope-Paths: {declared_stale}"
            )
            plan.write_text(text, encoding="utf-8")

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item = {
                "id6": "wir001",
                "setid": "demo",
                "order": 1,
                "position": 1,
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {
                    "self_finalize": False,
                    "isolate_worktree": False,
                },
            }

            reached = []

            def fake_launcher(*a, **k):
                reached.append(True)
                return 0, "ses", str(run_dir / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_launcher):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertTrue(
                reached, "Launcher must be reached for plain 'moved' artifact"
            )
            self.assertNotEqual(item["status"], "fail-gate")

            check_func = getattr(check_engine, "check_scope_path_target_stale", None)
            if check_func is not None:
                findings = check_func(repo)
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].rule, "check.scope-path-target-stale")
                self.assertIn("moved", findings[0].detail)

    def test_15_predicate_non_artifact_basename_vanished_empty_resolved(self) -> None:
        func = getattr(check_engine, "stale_record_scope_paths", None)
        self.assertIsNotNone(func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            plans_dir = repo / ".aw" / "records" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "INDEX.json").write_text("{}", encoding="utf-8")

            declared_path = ".aw/records/research/INDEX.json"
            plan_text = (
                f"# IPD: Subject\n- Status: approved\n- Scope-Paths: {declared_path}\n"
            )
            results = func(repo, plan_text)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].path, declared_path)
            self.assertEqual(
                results[0].classification, check_engine.SCOPE_STALE_VANISHED
            )
            self.assertEqual(results[0].resolved, ())

    def test_16_dispatch_no_orphan_prompt_on_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")

            executed = repo / ".aw" / "records" / "plans" / "executed"
            executed.mkdir(parents=True)
            target_plan = executed / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n", encoding="utf-8"
            )
            declared_stale = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )

            text = plan.read_text(encoding="utf-8")
            text = text.replace(
                "- Scope-Paths: src/", f"- Scope-Paths: {declared_stale}"
            )
            plan.write_text(text, encoding="utf-8")

            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            prompts_dir = run_dir / "prompts"
            prompts_dir.mkdir(parents=True)

            item = {
                "id6": "wir001",
                "setid": "demo",
                "order": 1,
                "position": 1,
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {
                    "self_finalize": False,
                    "isolate_worktree": False,
                },
            }

            def fake_launcher(*a, **k):
                return 0, "ses", str(run_dir / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_launcher):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            if item.get("status") == "fail-gate":
                prompt_files = list(prompts_dir.glob("*wir001*"))
                self.assertEqual(prompt_files, [])

    def test_17_check_severity_plain_moved_info_and_exit_code_zero(self) -> None:
        check_func = getattr(check_engine, "check_scope_path_target_stale", None)
        self.assertIsNotNone(check_func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            spec_dir = repo / ".aw" / "records" / "specs" / "to-review"
            spec_dir.mkdir(parents=True)
            target_spec = spec_dir / "20260901-spc001-01-spc001-target.spec.md"
            target_spec.write_text(
                "# Spec: Target\n- Status: to-review\n- Id: spc001\n",
                encoding="utf-8",
            )
            declared_path = (
                ".aw/records/specs/approved/20260901-spc001-01-spc001-target.spec.md"
            )

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            subj = pending / "20260902-subj-01-sub001-subj.ipd.md"
            subj_text = (
                f"# IPD: Subj\n- Status: approved\n- Id: sub001\n"
                f"- Scope-Paths: {declared_path}\n"
            )
            subj.write_text(subj_text, encoding="utf-8")

            findings = check_func(repo)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.rule, "check.scope-path-target-stale")
            self.assertEqual(f.severity, "info")
            self.assertIn("moved", f.detail)
            self.assertEqual(artifact_core.drift_exit_code([f]), 0)

    def test_18_check_severity_moved_terminal_error_and_exit_code_one(self) -> None:
        check_func = getattr(check_engine, "check_scope_path_target_stale", None)
        self.assertIsNotNone(check_func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            exec_dir = repo / ".aw" / "records" / "plans" / "executed"
            exec_dir.mkdir(parents=True)
            target_plan = exec_dir / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n",
                encoding="utf-8",
            )
            declared_path = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            subj = pending / "20260902-subj-01-sub001-subj.ipd.md"
            subj_text = (
                f"# IPD: Subj\n- Status: approved\n- Id: sub001\n"
                f"- Scope-Paths: {declared_path}\n"
            )
            subj.write_text(subj_text, encoding="utf-8")

            findings = check_func(repo)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.rule, "check.scope-path-target-stale")
            self.assertEqual(f.severity, "error")
            self.assertIn("moved-terminal", f.detail)
            self.assertEqual(artifact_core.drift_exit_code([f]), 1)

    def test_19_check_severity_vanished_error_and_exit_code_one(self) -> None:
        check_func = getattr(check_engine, "check_scope_path_target_stale", None)
        self.assertIsNotNone(check_func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            declared_path = (
                ".aw/records/specs/approved/20260901-spc999-01-spc999-target.spec.md"
            )

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            subj = pending / "20260902-subj-01-sub001-subj.ipd.md"
            subj_text = (
                f"# IPD: Subj\n- Status: approved\n- Id: sub001\n"
                f"- Scope-Paths: {declared_path}\n"
            )
            subj.write_text(subj_text, encoding="utf-8")

            findings = check_func(repo)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f.rule, "check.scope-path-target-stale")
            self.assertEqual(f.severity, "error")
            self.assertIn("vanished", f.detail)
            self.assertEqual(artifact_core.drift_exit_code([f]), 1)

    def test_20_check_severity_mixed_tree_retains_exit_code_one(self) -> None:
        check_func = getattr(check_engine, "check_scope_path_target_stale", None)
        self.assertIsNotNone(check_func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            spec_dir = repo / ".aw" / "records" / "specs" / "to-review"
            spec_dir.mkdir(parents=True)
            target_spec = spec_dir / "20260901-spc001-01-spc001-target.spec.md"
            target_spec.write_text(
                "# Spec: Target\n- Status: to-review\n- Id: spc001\n",
                encoding="utf-8",
            )
            decl_moved = (
                ".aw/records/specs/approved/20260901-spc001-01-spc001-target.spec.md"
            )

            exec_dir = repo / ".aw" / "records" / "plans" / "executed"
            exec_dir.mkdir(parents=True)
            target_plan = exec_dir / "20260901-test-01-tst001-target.ipd.md"
            target_plan.write_text(
                "# IPD: Target\n- Status: executed\n- Id: tst001\n",
                encoding="utf-8",
            )
            decl_terminal = (
                ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"
            )

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            subj = pending / "20260902-subj-01-sub001-subj.ipd.md"
            subj_text = (
                f"# IPD: Subj\n- Status: approved\n- Id: sub001\n"
                f"- Scope-Paths: {decl_moved}, {decl_terminal}\n"
            )
            subj.write_text(subj_text, encoding="utf-8")

            findings = check_func(repo)
            self.assertEqual(len(findings), 2)
            severities = {f.severity for f in findings}
            self.assertEqual(severities, {"info", "error"})
            self.assertEqual(artifact_core.drift_exit_code(findings), 1)

    def test_21_check_all_three_classifications_reported_count_and_detail(self) -> None:
        check_func = getattr(check_engine, "check_scope_path_target_stale", None)
        self.assertIsNotNone(check_func)
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            exec_dir = repo / ".aw" / "records" / "plans" / "executed"
            exec_dir.mkdir(parents=True)
            t1 = exec_dir / "20260901-test-01-tst001-target.ipd.md"
            t1.write_text(
                "# IPD: Target1\n- Status: executed\n- Id: tst001\n",
                encoding="utf-8",
            )
            decl1 = ".aw/records/plans/pending/20260901-test-01-tst001-target.ipd.md"

            spec_dir = repo / ".aw" / "records" / "specs" / "to-review"
            spec_dir.mkdir(parents=True)
            t2 = spec_dir / "20260901-spc001-01-spc001-target.spec.md"
            t2.write_text(
                "# Spec: Target2\n- Status: to-review\n- Id: spc001\n",
                encoding="utf-8",
            )
            decl2 = (
                ".aw/records/specs/approved/20260901-spc001-01-spc001-target.spec.md"
            )

            decl3 = (
                ".aw/records/specs/approved/20260901-spc999-01-spc999-target.spec.md"
            )

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            subj = pending / "20260902-subj-01-sub001-subj.ipd.md"
            subj_text = (
                f"# IPD: Subj\n- Status: approved\n- Id: sub001\n"
                f"- Scope-Paths: {decl1}, {decl2}, {decl3}\n"
            )
            subj.write_text(subj_text, encoding="utf-8")

            findings = check_func(repo)
            self.assertEqual(len(findings), 3)
            details = [f.detail for f in findings]
            self.assertTrue(any("moved-terminal" in d for d in details))
            self.assertTrue(
                any("moved" in d and "moved-terminal" not in d for d in details)
            )
            self.assertTrue(any("vanished" in d for d in details))


if __name__ == "__main__":
    unittest.main()
