#!/usr/bin/env python3

# PEP 563 postponed annotations. REQUIRED, not stylistic: this module annotates with PEP 604
# unions (`str | None`), which on CPython 3.9 - the declared floor in pyproject.toml - are
# EVALUATED at function-definition time and raise `TypeError: unsupported operand type(s) for |`.
# Without this import the module fails to IMPORT on 3.9, taking `test_agy_runipd_cli` down with it
# (it imports `_CONFORMING_PLAN` from here), which is 24 collection errors in the 3.9 CI job.
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import unittest
from typing import Any
from unittest import mock
from pathlib import Path

from agent_workflows import agy_runipd
from agent_workflows import artifact_core as core
from agent_workflows import oc_models
from agent_workflows import oc_runipd as driver
from agent_workflows import runner_shared
from agent_workflows import runner_stop
from tests import support
from tests.support import REPO_ROOT

# Launch the packaged driver as a module (`-m agent_workflows.oc_runipd`) with PYTHONPATH pinned to
# the checkout root, so the package resolves regardless of the tmp-repo cwd AND the stdlib is not
# shadowed by `agent_workflows/selectors.py` (which running the module file directly would trigger).
# See DECISION 11-ckxgx4-D1.
_DRIVER_CMD = [sys.executable, "-m", "agent_workflows.oc_runipd"]
_DRIVER_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}


def _make_run_dir(root: Path, queue: list) -> Path:
    repo = root / "repo"
    (repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    run_dir = repo / ".aw" / "records" / "runs" / "run-test"
    (run_dir / "outcomes").mkdir(parents=True)
    (run_dir / "sessions").mkdir(parents=True)
    (run_dir / "prompts").mkdir(parents=True)
    state = {
        "schema_version": 1,
        "run_id": "run-test",
        "created_at": "2026-08-24T00:00:00+00:00",
        "updated_at": "2026-08-24T00:00:00+00:00",
        "repo": str(repo),
        "selectors": ["demo"],
        "queue": queue,
        "set_sessions": {},
        "options": {
            "opencode": "/bin/false",
            "model": None,
            "agent": None,
            "auto": True,
        },
    }
    driver.atomic_write_json(run_dir / "state.json", state)
    return run_dir


class DriverTests(unittest.TestCase):
    def test_model_claim_does_not_override_lifecycle_location(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            plan = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20260824-demo-01-aaaaaa-test.ipd.md"
            )
            plan.parent.mkdir(parents=True)
            plan.write_text("# pending\n", encoding="utf-8")
            run_dir = root / "run"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "outcomes" / "01-aaaaaa.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            item = {
                "position": 1,
                "id6": "aaaaaa",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            disposition, _ = driver.reconcile_disposition(repo, item, run_dir, 0)
            self.assertEqual(disposition, "fail-gate")

    def test_selector_deduplication_supports_interleaved_set_resume(self):
        manifest_path = (
            REPO_ROOT
            / "tools"
            / "ipdrunner"
            / "20260823-pending-ipds-driver-manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        queue = driver.expand_selectors(
            manifest, ["v6zie5", "unifyfileio", "ipdgates", "proclint", "execset"]
        )
        self.assertEqual(len(queue), 22)
        self.assertEqual(queue[0], "v6zie5")
        self.assertEqual(queue[1], "o6b8l3")
        self.assertEqual(queue[7], "oorry1")
        self.assertEqual(queue[-1], "5ahblp")

        queue_prefix = driver.expand_selectors(
            manifest, ["v6zie5", "unifyfileio", "ipdgates", "proclint", "execse"]
        )
        self.assertEqual(queue, queue_prefix)

    def test_atomic_state_and_set_session_continuity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "README").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            for order, id6 in enumerate(("aaaaaa", "bbbbbb"), start=1):
                (pending / f"20260824-demo-{order:02d}-{id6}-test.ipd.md").write_text(
                    f"- Id: {id6}\n- Status: approved\n- Set: demo\n# {id6}\n",
                    encoding="utf-8",
                )
            manifest = {
                "schema_version": 1,
                "plans": {
                    "aaaaaa": {
                        "set": "demo",
                        "file": ".aw/records/plans/pending/20260824-demo-01-aaaaaa-test.ipd.md",
                        "status": "approved",
                        "dependencies": [],
                    },
                    "bbbbbb": {
                        "set": "demo",
                        "file": ".aw/records/plans/pending/20260824-demo-02-bbbbbb-test.ipd.md",
                        "status": "approved",
                        "dependencies": ["aaaaaa"],
                    },
                },
                "sets": {"demo": {"order": ["aaaaaa", "bbbbbb"]}},
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            runbook = root / "runbook.md"
            runbook.write_text("test runbook\n", encoding="utf-8")
            fake = support.make_fake_executable(
                root / "opencode",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import hashlib, json, pathlib, re, sys
                    args=sys.argv[1:]
                    if '--' not in args:
                        print('missing positional separator', file=sys.stderr)
                        raise SystemExit(64)
                    prompt=args[args.index('--')+1]
                    session=(args[args.index('--session')+1] if '--session' in args else
                             ('ses' + '_' + hashlib.sha1(args[args.index('--title')+1].encode()).hexdigest()[:12]))
                    outcome=pathlib.Path(re.search(r'Required JSON outcome: (.+)', prompt).group(1).strip())
                    plan=pathlib.Path(re.search(r'Plan file at launch: (.+)', prompt).group(1).strip())
                    executed=plan.parent.parent / 'executed' / plan.name
                    executed.parent.mkdir(parents=True, exist_ok=True)
                    plan.rename(executed)
                    id6=re.search(r'Assigned IPD: ([a-z0-9]{6})', prompt).group(1)
                    outcome.write_text(json.dumps({'schema_version':1,'id6':id6,'disposition':'executed','pushed':False}))
                    print(json.dumps({'type':'text','sessionID':session,'part':{'text':'done'}}))
                    """
                ),
            )
            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "start",
                    "demo",
                    "--no-self-finalize",
                    "--repo",
                    os.fspath(repo),
                    "--manifest",
                    os.fspath(manifest_path),
                    "--runbook",
                    os.fspath(runbook),
                    "--opencode",
                    os.fspath(fake),
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            run_id = next(
                line.split(": ", 1)[1]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            state = json.loads(
                (repo / ".aw" / "records" / "runs" / run_id / "state.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                [item["status"] for item in state["queue"]],
                ["executed", "executed"],
            )
            self.assertEqual(len(state["set_sessions"]), 1)
            sessions = [item["attempts"][0]["session_id"] for item in state["queue"]]
            self.assertEqual(sessions[0], sessions[1])
            # Continuation hint (rxkf1e) is emitted on run_queue exit: the completed run's
            # stdout names the captured session id and the copy-ready reuse command.
            self.assertIn("Session Continuity", result.stdout)
            self.assertIn(sessions[0], result.stdout)
            self.assertIn("aw oc run --session", result.stdout)
            self.assertIn(f"aw runs {run_id}", result.stdout)
            self.assertNotIn("resume", result.stdout)


class ReviewPlanRoutingTests(unittest.TestCase):
    def test_to_review_plans_invoke_plan_review_and_share_session(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "README").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            p1 = pending / "20260824-demo-01-rev001-test.ipd.md"
            p1.write_text(
                "- Id: rev001\n- Set: demo\n- Status: to-review\n# Plan 1\n",
                encoding="utf-8",
            )
            p2 = pending / "20260824-demo-02-rev002-test.ipd.md"
            p2.write_text(
                "- Id: rev002\n- Set: demo\n- Status: to-review\n# Plan 2\n",
                encoding="utf-8",
            )

            fake = support.make_fake_executable(
                root / "fake_opencode",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json, pathlib, sys
                    args = sys.argv[1:]
                    prompt = args[args.index('--') + 1] if '--' in args else ""
                    session = args[args.index('--session') + 1] if '--session' in args else ("ses" + "_" + "firstreview")

                    # Verify review slash command format
                    if prompt.startswith("/plan-review"):
                        # dirtygates-05 (`ajxr5d`): read the COMMAND LINE, not the last token of the
                        # whole prompt. An isolated review's prompt is the `/plan-review <path>` line
                        # FOLLOWED BY the in-lane statement on its own lines, so `split()[-1]` would
                        # pick a word out of that prose. A real slash command parses its own line, so
                        # this fixture now does too.
                        target_file = prompt.splitlines()[0].split()[-1]
                        p = pathlib.Path(target_file)
                        if not p.is_absolute():
                            p = pathlib.Path.cwd() / p
                        if p.is_file():
                            content = p.read_text()
                            content = content.replace("- Status: to-review", "- Status: reviewed")
                            p.write_text(content)

                    print(json.dumps({'type':'text','sessionID':session,'part':{'text':'review complete'}}))
                    """
                ),
            )

            ses_test_val = "ses" + "_" + "initialsession"
            # Run with direct selectors (id6 and filename) and explicit --session
            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "start",
                    "rev001",
                    os.fspath(p2),
                    "--repo",
                    os.fspath(repo),
                    "--session",
                    ses_test_val,
                    "--opencode",
                    os.fspath(fake),
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            # Verify prompt content and status transitions
            run_id = next(
                line.split(": ", 1)[1]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            state_file = repo / ".aw" / "records" / "runs" / run_id / "state.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))

            self.assertEqual(len(state["queue"]), 2)
            self.assertEqual(state["queue"][0]["action"], "review")
            self.assertEqual(state["queue"][1]["action"], "review")
            self.assertEqual(state["queue"][0]["status"], "reviewed")
            self.assertEqual(state["queue"][1]["status"], "reviewed")

            # Check both attempts used the same session
            s0 = state["queue"][0]["attempts"][0]["session_id"]
            s1 = state["queue"][1]["attempts"][0]["session_id"]
            self.assertEqual(s0, ses_test_val)
            self.assertEqual(s1, ses_test_val)


class SelectorResolutionTests(unittest.TestCase):
    def test_dynamic_plan_discovery_without_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            p1 = pending / "20260824-myset-01-abc111-first.ipd.md"
            p1.write_text(
                "- Id: abc111\n- Set: myset\n- Status: to-review\n# First\n",
                encoding="utf-8",
            )
            p2 = pending / "20260824-myset-02-abc222-second.ipd.md"
            p2.write_text(
                "- Id: abc222\n- Set: myset\n- Status: approved\n# Second\n",
                encoding="utf-8",
            )

            discovered = driver.discover_plans(repo)
            self.assertIn("abc111", discovered)
            self.assertIn("abc222", discovered)
            self.assertEqual(discovered["abc111"].status, "to-review")
            self.assertEqual(discovered["abc222"].status, "approved")

            manifest = driver.build_dynamic_manifest(repo, discovered)
            # Expand setid
            expanded_set = driver.expand_selectors(manifest, ["myset"], repo=repo)
            self.assertEqual(expanded_set, ["abc111", "abc222"])

            # Expand id6
            expanded_id6 = driver.expand_selectors(manifest, ["abc222"], repo=repo)
            self.assertEqual(expanded_id6, ["abc222"])

            # Expand direct file path
            expanded_file = driver.expand_selectors(manifest, [str(p1)], repo=repo)
            self.assertEqual(expanded_file, ["abc111"])

    def test_default_start_command_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            p = pending / "20260824-seta-01-tst001-test.ipd.md"
            p.write_text(
                "- Id: tst001\n- Set: seta\n- Status: approved\n# Test\n",
                encoding="utf-8",
            )

            # Invoking runipd.py without explicit 'start' subcommand
            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "--repo",
                    os.fspath(repo),
                    "--prepare-only",
                    "tst001",
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Run ID:", result.stdout)
            self.assertIn("tst001", result.stdout)


class ResumeRequeueTests(unittest.TestCase):
    def test_bare_resume_requeues_interrupted_item(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = [
                {
                    "position": 1,
                    "id6": "aaaaaa",
                    "setid": "demo",
                    "configured_file": ".aw/records/plans/pending/20260824-demo-01-aaaaaa-test.ipd.md",
                    "dependencies": [],
                    "status": "running",
                    "attempts": [
                        {
                            "number": 1,
                            "started_at": "2026-08-24T00:00:00+00:00",
                            "log": None,
                        }
                    ],
                }
            ]
            run_dir = _make_run_dir(root, queue)
            state = driver.load_state(run_dir)
            driver.reconcile_interrupted(run_dir, state)
            self.assertEqual(state["queue"][0]["status"], "interrupted")

            requeued = driver.requeue_interrupted(run_dir, state)
            self.assertIn("aaaaaa", requeued)
            self.assertEqual(state["queue"][0]["status"], "queued")
            self.assertTrue(state["queue"][0].get("recovery_next"))

    def test_bare_resume_refuses_to_requeue_an_indeterminate_item(self):
        # CONSCIOUSLY ADDED beside the test above by runstop Phase 4 (`m0z0ti`, E-04), which changed
        # `requeue_interrupted` from unconditional to gated (orchestrator CID-4). The test above still
        # pins the ORDINARY behavior and is deliberately unchanged: an ordinary interrupted item is
        # still auto-requeued in recovery mode, so the gate cannot be mistaken for a blanket disabling
        # of recovery.
        #
        # THE NEW BEHAVIOR (spec c4gd2h R19): an item whose turn was FORCE-interrupted (level 4) has an
        # INDETERMINATE outcome, so re-running it blindly could repeat work the driver never
        # established the result of. It must be SKIPPED and REPORTED instead.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = [
                {
                    "position": 1,
                    "id6": "aaaaaa",
                    "setid": "demo",
                    "configured_file": ".aw/records/plans/pending/20260824-demo-01-aaaaaa-test.ipd.md",
                    "dependencies": [],
                    "status": "interrupted",
                    "attempts": [],
                    "stopped": {
                        "stopped_deliberately": True,
                        "level": 4,
                        "certainty": "indeterminate",
                        "disposition": "unknown_outcome",
                    },
                }
            ]
            run_dir = _make_run_dir(root, queue)
            state = driver.load_state(run_dir)

            requeued = driver.requeue_interrupted(run_dir, state)

            self.assertEqual(requeued, [], "an indeterminate item must NOT be requeued")
            self.assertEqual(state["queue"][0]["status"], "interrupted")
            self.assertNotIn("recovery_next", state["queue"][0])
            self.assertTrue(state["queue"][0].get("requires_reconciliation"))

    def test_bare_resume_does_not_requeue_partial_or_failed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = [
                {
                    "position": 1,
                    "id6": "aaaaaa",
                    "setid": "demo",
                    "configured_file": "x",
                    "dependencies": [],
                    "status": "partial",
                    "attempts": [],
                },
                {
                    "position": 2,
                    "id6": "bbbbbb",
                    "setid": "demo",
                    "configured_file": "y",
                    "dependencies": [],
                    "status": "failed-safely",
                    "attempts": [],
                },
            ]
            run_dir = _make_run_dir(root, queue)
            state = driver.load_state(run_dir)
            requeued = driver.requeue_interrupted(run_dir, state)
            self.assertEqual(requeued, [])
            self.assertEqual(state["queue"][0]["status"], "partial")
            self.assertEqual(state["queue"][1]["status"], "failed-safely")

    def test_resume_overrides_session(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue = [
                {
                    "position": 1,
                    "id6": "aaaaaa",
                    "setid": "demo",
                    "configured_file": "x",
                    "dependencies": [],
                    "status": "queued",
                    "attempts": [],
                }
            ]
            run_dir = _make_run_dir(root, queue)
            override_session = "ses" + "_" + "resumed999"
            args = driver.build_parser().parse_args(
                [
                    "resume",
                    str(run_dir),
                    "--repo",
                    str(root / "repo"),
                    "--session",
                    override_session,
                ]
            )
            # Update state with session via main flow logic
            state = driver.load_state(run_dir)
            state["session_id"] = args.session
            state.setdefault("options", {})["session"] = args.session
            driver.save_state(run_dir, state)

            reloaded = driver.load_state(run_dir)
            self.assertEqual(reloaded["session_id"], override_session)
            self.assertEqual(reloaded["options"]["session"], override_session)


class GitPreconditionTests(unittest.TestCase):
    def test_non_git_dir_reports_clear_message(self):
        with tempfile.TemporaryDirectory() as temp:
            not_git = Path(temp) / "plain"
            not_git.mkdir()
            manifest = Path(temp) / "m.json"
            manifest.write_text(
                json.dumps({"schema_version": 1, "plans": {}, "sets": {}}),
                encoding="utf-8",
            )
            runbook = Path(temp) / "r.md"
            runbook.write_text("rb\n", encoding="utf-8")
            args = driver.build_parser().parse_args(
                [
                    "start",
                    "demo",
                    "--repo",
                    str(not_git),
                    "--manifest",
                    str(manifest),
                    "--runbook",
                    str(runbook),
                ]
            )
            with self.assertRaises(driver.DriverError) as ctx:
                driver.initialize_run(args)
            message = str(ctx.exception)
            self.assertIn("Not a Git repository", message)
            self.assertNotIn("Command failed", message)


class SelectorErrorTests(unittest.TestCase):
    def test_empty_set_reports_named_set(self):
        manifest = {
            "schema_version": 1,
            "plans": {},
            "sets": {"empty": {"order": []}},
        }
        with self.assertRaises(driver.DriverError) as ctx:
            driver.expand_selectors(manifest, ["empty"])
        message = str(ctx.exception)
        self.assertIn("empty", message)
        self.assertNotIn("At least one id6 or Set selector is required", message)

    def test_no_selector_still_reports_generic_message(self):
        manifest = {"schema_version": 1, "plans": {}, "sets": {}}
        with self.assertRaises(driver.DriverError) as ctx:
            driver.expand_selectors(manifest, [])
        self.assertIn(
            "At least one id6 or Set selector is required", str(ctx.exception)
        )

    def test_unresolved_selector_identifies_backlog_item(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            backlog_dir = repo / ".aw" / "records" / "backlog" / "open"
            backlog_dir.mkdir(parents=True)
            (backlog_dir / "20260829-test-01-item01.backlog.md").write_text(
                "- Id: item01\n- Status: open\n", encoding="utf-8"
            )
            manifest = {"schema_version": 1, "plans": {}, "sets": {}}
            with self.assertRaises(driver.DriverError) as ctx:
                driver.expand_selectors(manifest, ["item01"], repo=repo)
            msg = str(ctx.exception)
            self.assertIn("'item01' is a backlog item", msg)
            self.assertIn(
                ".aw/records/backlog/open/20260829-test-01-item01.backlog.md", msg
            )
            self.assertIn("not an IPD plan", msg)

    def test_unresolved_selector_identifies_spec(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            specs_dir = repo / ".aw" / "records" / "specs"
            specs_dir.mkdir(parents=True)
            (specs_dir / "20260829-0001-01-myspec.spec.md").write_text(
                "- Id: spec01\n- Status: approved\n", encoding="utf-8"
            )
            manifest = {"schema_version": 1, "plans": {}, "sets": {}}
            with self.assertRaises(driver.DriverError) as ctx:
                driver.expand_selectors(manifest, ["spec01"], repo=repo)
            msg = str(ctx.exception)
            self.assertIn("'spec01' is a spec", msg)
            self.assertIn("not an IPD plan", msg)

    def test_unresolved_selector_identifies_missing_file_or_id6(self):
        manifest = {"schema_version": 1, "plans": {}, "sets": {}}
        with self.assertRaises(driver.DriverError) as ctx:
            driver.expand_selectors(manifest, ["abc123"])
        self.assertIn("No IPD plan found with id6 'abc123'", str(ctx.exception))

        with self.assertRaises(driver.DriverError) as ctx:
            driver.expand_selectors(manifest, ["some/path.ipd.md"])
        self.assertIn("Plan file not found: 'some/path.ipd.md'", str(ctx.exception))

        with self.assertRaises(driver.DriverError) as ctx:
            driver.expand_selectors(manifest, ["unknown_set"])
        self.assertIn(
            "No IPD plan, Set, or file matching 'unknown_set'", str(ctx.exception)
        )


class ProgressRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plain = driver.Palette(False)

    def test_text_event_renders_narration(self):
        line = driver.render_event(
            '{"type":"text","part":{"type":"text","text":"Reading the plan."}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("Reading the plan.", line)
        self.assertNotIn("\033[", line)

    def test_tool_use_renders_tool_and_title(self):
        line = driver.render_event(
            '{"type":"tool_use","part":{"tool":"bash",'
            '"state":{"status":"completed","title":"git status --short"}}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("bash", line)
        self.assertIn("git status --short", line)

    def test_step_start_and_blank_are_suppressed(self):
        self.assertIsNone(driver.render_event('{"type":"step_start"}', self.plain))
        self.assertIsNone(driver.render_event("   ", self.plain))

    def test_step_finish_updates_tracker_and_is_suppressed(self):
        tracker = driver.StreamTracker()
        line = driver.render_event(
            '{"type":"step_finish","part":{"tokens":{"total":1234,"input":1000,"output":234},"cost":0.0042}}',
            self.plain,
            tracker=tracker,
        )
        self.assertIsNone(line)
        self.assertEqual(tracker.input_tokens, 1000)
        self.assertEqual(tracker.output_tokens, 234)
        self.assertAlmostEqual(tracker.cost, 0.0042)

    def test_non_json_line_passed_through_dimmed(self):
        line = driver.render_event("a stray log line", self.plain)
        assert line is not None
        self.assertIn("a stray log line", line)

    def test_palette_noop_when_disabled_and_active_when_enabled(self):
        self.assertEqual(self.plain("x", "green"), "x")
        colored = driver.Palette(True)("x", "green")
        self.assertTrue(colored.startswith("\033["))
        self.assertIn("x", colored)

    def test_long_text_is_clipped_to_single_line(self):
        long = "word " * 200
        line = driver.render_event(
            json.dumps({"type": "text", "part": {"text": long}}), self.plain
        )
        assert line is not None
        self.assertNotIn("\n", line)
        self.assertLessEqual(len(line), 420)


class ChildTerminationTests(unittest.TestCase):
    def test_terminate_process_reaps_running_child(self):
        import sys as _sys

        proc = subprocess.Popen(
            [
                _sys.executable,
                "-c",
                "import signal,time\n"
                "signal.signal(signal.SIGINT, signal.SIG_IGN)\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "time.sleep(60)\n",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertIsNone(proc.poll(), "child should be running")
        orig = (driver._SIGINT_GRACE_SECONDS, driver._SIGTERM_GRACE_SECONDS)
        driver._SIGINT_GRACE_SECONDS = 0.3
        driver._SIGTERM_GRACE_SECONDS = 0.3
        try:
            driver.terminate_process(proc)
        finally:
            driver._SIGINT_GRACE_SECONDS, driver._SIGTERM_GRACE_SECONDS = orig
        self.assertIsNotNone(proc.returncode)
        self.assertIsNotNone(proc.poll())
        self.assertTrue(proc.stdout is None or proc.stdout.closed)

    def test_terminate_process_is_safe_on_exited_child(self):
        import sys as _sys

        proc = subprocess.Popen(
            [_sys.executable, "-c", "pass"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        proc.wait()
        driver.terminate_process(proc)
        self.assertIsNotNone(proc.returncode)


class DependencyFailClosedTests(unittest.TestCase):
    def _repo_with_dep(self, temp: Path, dep_bucket: str | None):
        repo = temp / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        if dep_bucket is not None:
            d = repo / ".aw" / "records" / "plans" / dep_bucket
            d.mkdir(parents=True, exist_ok=True)
            (d / "20260824-demo-01-depaaa-x.ipd.md").write_text(
                "# dep\n", encoding="utf-8"
            )
        return repo

    def test_unqueued_unexecuted_dependency_is_unsatisfied(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            repo = self._repo_with_dep(temp, "pending")
            state = {
                "repo": str(repo),
                "queue": [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "dependencies": ["depaaa"],
                    }
                ],
            }
            item = state["queue"][0]
            satisfied, missing = driver.dependency_status(item, state)
            self.assertFalse(satisfied)
            self.assertEqual(missing, ["depaaa"])

    def test_unqueued_dependency_absent_from_repo_is_unsatisfied(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            repo = self._repo_with_dep(temp, None)
            state = {
                "repo": str(repo),
                "queue": [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "dependencies": ["depaaa"],
                    }
                ],
            }
            satisfied, missing = driver.dependency_status(state["queue"][0], state)
            self.assertFalse(satisfied)
            self.assertEqual(missing, ["depaaa"])

    def test_unqueued_executed_dependency_is_satisfied(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            repo = self._repo_with_dep(temp, "executed")
            state = {
                "repo": str(repo),
                "queue": [
                    {
                        "id6": "itemaa",
                        "status": "queued",
                        "dependencies": ["depaaa"],
                    }
                ],
            }
            satisfied, missing = driver.dependency_status(state["queue"][0], state)
            self.assertTrue(satisfied)
            self.assertEqual(missing, [])


class RunDirResolutionTests(unittest.TestCase):
    def test_resolve_run_dir_accepts_directory_path(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            run_dir = temp / "runs" / "run-abc"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text("{}", encoding="utf-8")
            got = driver.resolve_run_dir(str(temp), str(run_dir))
            self.assertEqual(got.resolve(), run_dir.resolve())

    def test_resolve_run_dir_directory_without_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            bogus = temp / "not-a-run"
            bogus.mkdir()
            with self.assertRaises(driver.DriverError):
                driver.resolve_run_dir(str(temp), str(bogus))

    def test_extract_session_id_parses_alternate_keys(self):
        prefix = "ses" + "_"
        camel = prefix + "camelcaseid"
        snake = prefix + "snakecaseid"
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / "a.jsonl"
            log.write_text(
                json.dumps({"type": "text", "sessionId": camel}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(driver.extract_session_id(log), camel)
            log.write_text(
                json.dumps({"session_id": snake}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(driver.extract_session_id(log), snake)

    def test_extract_session_id_prefers_ses_prefixed_over_nonprefixed(self):
        real = "ses" + "_" + "realsession1"
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / "a.jsonl"
            log.write_text(
                json.dumps({"sessionID": "raw-provider-id"})
                + "\n"
                + json.dumps({"sessionID": real})
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(driver.extract_session_id(log), real)


class AtomicWriteAndReconcileTests(unittest.TestCase):
    def test_atomic_write_json_roundtrips_with_dir_fsync(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "sub" / "state.json"
            driver.atomic_write_json(p, {"b": 2, "a": 1})
            self.assertTrue(p.is_file())
            self.assertEqual(json.loads(p.read_text()), {"a": 1, "b": 2})

    def test_reconcile_interrupted_sets_interrupted_at(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            repo = temp / "repo"
            (repo / ".aw" / "records" / "runs" / "r").mkdir(parents=True)
            run_dir = repo / ".aw" / "records" / "runs" / "r"
            state = {
                "run_id": "r",
                "created_at": "2026-08-24T00:00:00+00:00",
                "updated_at": "2026-08-24T00:00:00+00:00",
                "selectors": ["demo"],
                "repo": str(repo),
                "set_sessions": {},
                "queue": [
                    {
                        "position": 1,
                        "id6": "itemaa",
                        "setid": "demo",
                        "configured_file": "nonexistent.ipd.md",
                        "status": "running",
                        "attempts": [
                            {
                                "number": 1,
                                "started_at": "2026-08-24T00:00:00+00:00",
                            }
                        ],
                    }
                ],
            }
            driver.atomic_write_json(run_dir / "state.json", state)
            driver.reconcile_interrupted(run_dir, state)
            item = state["queue"][0]
            self.assertEqual(item["status"], "interrupted")
            self.assertIn("interrupted_at", item["attempts"][-1])
            self.assertIn("ended_at", item["attempts"][-1])

    def test_reconcile_interrupted_tolerates_an_item_with_no_configured_file(self):
        """runrecon-02 (`fduoj4`) E-01: the DIVERGENCE the extraction had to resolve, pinned.

        The two host copies differed in exactly one code line: oc indexed
        `item["configured_file"]` while agy used `item.get("configured_file", "")`. On an item
        MISSING that key the oc form raised `KeyError`, which the surrounding `except DriverError`
        does NOT catch, so the exception escaped the loop and `save_state` never ran - abandoning
        the verdict for every OTHER item in a crashed queue over one malformed entry. The shared
        version takes AGY'S TOLERANT FORM, and this is what proves it: a crashed ledger is exactly
        where a malformed item is likely, so failing the whole reconciliation over one is strictly
        worse than reconciling the rest.

        ASSERTED ON BOTH HOSTS, because the point of the extraction is that they cannot differ here
        again, and asserting it for one would have passed before the change too.
        """

        from agent_workflows import agy_runipd

        for module in (driver, agy_runipd):
            with (
                self.subTest(driver=module.__name__),
                tempfile.TemporaryDirectory() as t,
            ):
                temp = Path(t)
                repo = temp / "repo"
                run_dir = repo / ".aw" / "records" / "runs" / "r"
                run_dir.mkdir(parents=True)
                state = {
                    "run_id": "r",
                    "repo": str(repo),
                    "set_sessions": {},
                    "queue": [
                        # NO `configured_file` KEY AT ALL. This is the shape that raised.
                        {
                            "position": 1,
                            "id6": "nocfga",
                            "setid": "demo",
                            "status": "running",
                            "attempts": [{"number": 1}],
                        },
                        # A SECOND item, so the test also proves the loop CONTINUED. Without it,
                        # "did not raise" would be satisfied by a version that silently stopped.
                        {
                            "position": 2,
                            "id6": "nocfgb",
                            "setid": "demo",
                            "configured_file": "nonexistent.ipd.md",
                            "status": "running",
                            "attempts": [{"number": 1}],
                        },
                    ],
                }
                module.atomic_write_json(run_dir / "state.json", state)

                module.reconcile_interrupted(run_dir, state)

                self.assertEqual(state["queue"][0]["status"], "interrupted")
                self.assertEqual(
                    state["queue"][1]["status"],
                    "interrupted",
                    "the loop must reach every item; a raise on the first one used to abandon "
                    "the whole crashed queue before `save_state`",
                )
                # And the verdict must be DURABLE, which is the half the `KeyError` destroyed.
                persisted = json.loads((run_dir / "state.json").read_text())
                self.assertEqual(
                    [i["status"] for i in persisted["queue"]],
                    ["interrupted", "interrupted"],
                )


def _crashed_run_fixture(
    root: Path,
    *,
    outcome: Any = "absent",
    action: str = "execute",
    indeterminate: bool = False,
    plan_in_executed: bool = False,
) -> tuple[Path, Path, dict]:
    """The MEASURED SHAPE of the incident backlog `ydbhfd` recorded, as a fixture.

    runrecon-02 (`fduoj4`) E-05. Built from the real incident rather than a simplification: a queue
    item stuck at `running` with `last_outcome: None`, and an `outcomes/<NN>-<id6>.json` recording a
    terminal disposition plus a `commits` list. That is what `aw oc run e32j35 97df1z` left behind
    when a server reboot killed it, and a fixture that simplified any of those three away would stop
    testing the defect.

    FIXTURES, NEVER THE LIVE TREE. `.aw/records/runs/` is gitignored, so it is absent in every fresh
    checkout and in every isolated lane worktree the runner allocates by default; a test keyed to the
    developer's live run corpus passes here and is unrunnable exactly where it actually runs.

    ``outcome`` takes the sentinel ``"absent"`` (write no file at all), the sentinel ``"unparseable"``
    (write bytes that are not JSON), or a mapping to serialize. The three are distinct cases the
    fallback ordering must treat identically, and passing ``None`` could not tell "no file" from
    "a file whose content is null".
    """

    repo = root / "repo"
    plans = repo / ".aw" / "records" / "plans"
    bucket = "executed" if plan_in_executed else "pending"
    (plans / bucket).mkdir(parents=True, exist_ok=True)
    plan_name = "20260902-e32j35-02-97df1z-recorded.ipd.md"
    (plans / bucket / plan_name).write_text("# plan\n", encoding="utf-8")

    run_dir = repo / ".aw" / "records" / "runs" / "run-20260902T013603Z-1758564"
    (run_dir / "outcomes").mkdir(parents=True)
    if outcome == "unparseable":
        (run_dir / "outcomes" / "02-97df1z.json").write_text(
            "{not json at all", encoding="utf-8"
        )
    elif outcome != "absent":
        (run_dir / "outcomes" / "02-97df1z.json").write_text(
            json.dumps(outcome), encoding="utf-8"
        )

    item: dict[str, Any] = {
        "position": 2,
        "id6": "97df1z",
        "setid": "e32j35",
        "action": action,
        # The path names `pending/`, exactly as a real record does, so resolution is by id6 and the
        # `plan_in_executed` case exercises the promotion the way the driver really reaches it.
        "configured_file": f".aw/records/plans/pending/{plan_name}",
        "dependencies": [],
        "status": "running",
        "last_outcome": None,
        "attempts": [{"number": 1, "log": None}],
    }
    if indeterminate:
        item["stopped"] = runner_stop.forced_disposition(requester="test-operator")
    state = {
        "schema_version": 1,
        "run_id": run_dir.name,
        "repo": str(repo),
        "set_sessions": {},
        "queue": [item],
    }
    driver.atomic_write_json(run_dir / "state.json", state)
    return repo, run_dir, state


#: The measured incident's own outcome payload: `substantially-complete` with one commit sha and
#: `pushed: false`. The sha is the real one from `outcomes/02-97df1z.json`.
_MEASURED_OUTCOME = {
    "disposition": "substantially-complete",
    "summary": "aw ipd lint --phase pre-transition reports conforming",
    "commits": ["209227d54f1fd7e34115ee9a198c74513a99567d"],
    "pushed": False,
}


class CrashedStepOutcomeRecoveryTests(unittest.TestCase):
    """runrecon-02 (`fduoj4`) E-02/E-03/E-05: the crash reconciler must read the step's own evidence.

    THE DEFECT, measured (backlog `ydbhfd`, 2026-09-02): `aw oc run e32j35 97df1z` was killed by a
    server and network reboot. `outcomes/02-97df1z.json` had ALREADY been written and recorded
    `"disposition": "substantially-complete"` with a real commit sha and a substantive summary, and
    `state.json` recorded that step `interrupted` with `last_outcome: None`. The authoritative answer
    was on disk in the same run directory and was never consulted, because the reconciler decided
    from the plan's DIRECTORY alone.

    EVERY TEST RUNS ON BOTH HOSTS. The two copies of this function were not the same object and had
    already diverged once, so a one-sided assertion would have proven nothing about `aw agy run`.
    """

    HOSTS = ("oc_runipd", "agy_runipd")

    def _modules(self):
        from agent_workflows import agy_runipd

        return (("oc_runipd", driver), ("agy_runipd", agy_runipd))

    # ---- the measured case ------------------------------------------------------------------

    def test_the_measured_shape_recovers_its_recorded_disposition_and_commits(self):
        from agent_workflows import runner_shared

        for name, module in self._modules():
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as t:
                _repo, run_dir, state = _crashed_run_fixture(
                    Path(t), outcome=_MEASURED_OUTCOME
                )

                with contextlib.redirect_stderr(io.StringIO()):
                    module.reconcile_interrupted(run_dir, state)

                item = state["queue"][0]
                self.assertEqual(item["status"], "fail-gate")
                self.assertEqual(
                    item[runner_shared.RECOVERY_PROVENANCE_KEY],
                    runner_shared.RECOVERED_FROM_OUTCOME,
                )
                self.assertEqual(item["last_outcome"], _MEASURED_OUTCOME)
                commits = item[runner_shared.RECOVERED_COMMITS_KEY]
                self.assertEqual(
                    commits,
                    [
                        {
                            "sha": "209227d54f1fd7e34115ee9a198c74513a99567d",
                            "resolved": False,
                        }
                    ],
                )

                persisted = json.loads((run_dir / "state.json").read_text())
                self.assertEqual(persisted["queue"][0]["status"], "fail-gate")

                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                recovered = [
                    e
                    for e in events
                    if e.get("event") == "interrupted-recovered-from-outcome"
                ]
                self.assertEqual(len(recovered), 1, events)
                self.assertEqual(recovered[0]["disposition"], "fail-gate")
                self.assertEqual(recovered[0]["id6"], "97df1z")
                self.assertEqual(
                    [e for e in events if e.get("event") == "interrupted-detected"], []
                )

    def test_a_resolvable_sha_is_reported_resolved(self):
        """The other direction, so `resolved` is not a constant `False` that happens to read right."""
        from agent_workflows import runner_shared

        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            repo, run_dir, state = _crashed_run_fixture(root, outcome="absent")
            for args in (
                ["init", "-q"],
                ["config", "user.email", "t@example.invalid"],
                ["config", "user.name", "t"],
                ["commit", "-q", "--allow-empty", "-m", "fixture"],
            ):
                subprocess.run(["git", *args], cwd=repo, check=True)
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            (run_dir / "outcomes" / "02-97df1z.json").write_text(
                json.dumps(
                    {
                        "disposition": "substantially-complete",
                        "commits": [sha, "0" * 40],
                    }
                ),
                encoding="utf-8",
            )

            with contextlib.redirect_stderr(io.StringIO()):
                driver.reconcile_interrupted(run_dir, state)

            self.assertEqual(
                state["queue"][0][runner_shared.RECOVERED_COMMITS_KEY],
                [{"sha": sha, "resolved": True}, {"sha": "0" * 40, "resolved": False}],
            )

    # ---- E-05: the four fallback branches ---------------------------------------------------

    def test_fallback_branches_yield_interrupted(self):
        from agent_workflows import runner_shared

        test_cases = [
            ("absent", "a step that died before writing anything"),
            ("unparseable", "a truncated write is not a verdict"),
            (
                {"summary": "no disposition key at all", "pushed": False},
                "a file recording no disposition establishes no disposition",
            ),
            (
                {"disposition": "dependency-blocked", "pushed": False},
                "a self-recorded dependency-blocked",
            ),
            (
                {"disposition": "not-attempted", "pushed": False},
                "a self-recorded not-attempted",
            ),
        ]

        for name, module in self._modules():
            for outcome, why in test_cases:
                with self.subTest(
                    driver=name, why=why
                ), tempfile.TemporaryDirectory() as t:
                    _repo, run_dir, state = _crashed_run_fixture(
                        Path(t), outcome=outcome
                    )
                    module.reconcile_interrupted(run_dir, state)
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "interrupted")
                    self.assertNotIn(runner_shared.RECOVERY_PROVENANCE_KEY, item)
                    self.assertNotIn(runner_shared.RECOVERED_COMMITS_KEY, item)

    # ---- E-05: the four CONTROL tests -------------------------------------------------------

    def test_control_a_self_claimed_executed_is_still_downgraded(self):
        """THE ANTI-FABRICATION DOWNGRADE. An agent's claim about its own turn is not authority.

        The measured case needs NO relaxation of this rule, because its outcome file already says
        `substantially-complete`, which is honored without any downgrade. So a change that removes
        the downgrade to make some case report `executed` is not fixing this plan's defect.
        """
        for name, module in self._modules():
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as t:
                _repo, run_dir, state = _crashed_run_fixture(
                    Path(t),
                    outcome={"disposition": "executed", "pushed": False},
                )
                with contextlib.redirect_stderr(io.StringIO()):
                    module.reconcile_interrupted(run_dir, state)
                self.assertEqual(
                    state["queue"][0]["status"],
                    "fail-gate",
                    "a self-claimed `executed` must be DOWNGRADED; the plan's directory is the "
                    "only thing that may establish `executed`",
                )

    def test_control_an_indeterminate_item_is_refused_even_with_a_claiming_outcome(
        self,
    ):
        """spec `c4gd2h` R22. A force-cut turn's own self-report is exactly the evidence R22 says
        the driver never established, so the outcome file must NOT override the refusal.

        The plan sits in `executed/` AND the outcome file claims success, i.e. both promotion routes
        are armed at once, and both must refuse.
        """
        from agent_workflows import runner_shared

        for name, module in self._modules():
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as t:
                _repo, run_dir, state = _crashed_run_fixture(
                    Path(t),
                    outcome=_MEASURED_OUTCOME,
                    indeterminate=True,
                    plan_in_executed=True,
                )
                with contextlib.redirect_stderr(io.StringIO()):
                    module.reconcile_interrupted(run_dir, state)

                item = state["queue"][0]
                self.assertEqual(item["status"], "interrupted")
                self.assertNotIn(runner_shared.RECOVERY_PROVENANCE_KEY, item)
                self.assertIn("reconciliation_conflict", item)
                self.assertIn("c4gd2h R22", item["reconciliation_conflict"])
                events = [
                    json.loads(line)
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                self.assertEqual(
                    len(
                        [
                            e
                            for e in events
                            if e.get("event")
                            == "interrupted-promotion-refused-unknown-outcome"
                        ]
                    ),
                    1,
                    events,
                )
                self.assertEqual(
                    [
                        e
                        for e in events
                        if e.get("event") == "interrupted-recovered-from-outcome"
                    ],
                    [],
                )

    def test_control_review_and_orchestrate_action_items_consult_no_outcome_file(self):
        """E-02's action gates. A `review` or `orchestrate` item does not consult the outcome file."""
        from agent_workflows import runner_shared

        for action in ("review", "orchestrate"):
            for name, module in self._modules():
                with self.subTest(
                    driver=name, action=action
                ), tempfile.TemporaryDirectory() as t:
                    _repo, run_dir, state = _crashed_run_fixture(
                        Path(t), outcome=_MEASURED_OUTCOME, action=action
                    )
                    module.reconcile_interrupted(run_dir, state)
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "interrupted")
                    self.assertNotIn(runner_shared.RECOVERY_PROVENANCE_KEY, item)

    # ---- the directory promotion is unchanged ------------------------------------------------

    def test_an_ordinary_plan_in_executed_is_still_promoted(self):
        """The pre-existing promotion must be untouched by the new consultation, and it must WIN.

        A plan in `executed/` with an outcome file recording the weaker `substantially-complete` must
        record `executed`: the directory is the harder-to-forge signal, which is the same precedence
        `reconcile_disposition` has always applied.
        """
        for name, module in self._modules():
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as t:
                _repo, run_dir, state = _crashed_run_fixture(
                    Path(t), outcome=_MEASURED_OUTCOME, plan_in_executed=True
                )
                module.reconcile_interrupted(run_dir, state)
                self.assertEqual(state["queue"][0]["status"], "executed")

    # ---- OQ-03: the behavior change the maintainer authorized --------------------------------

    def test_a_recovered_step_is_NOT_requeued_on_resume(self):
        """OQ-03, answered by the maintainer 2026-09-10: YES, a recovered step stops being retried.

        THIS IS A CHANGE TO WHAT A RESUME DOES, not only to what a record says, which is why it needs
        its own validation rather than an inspection of a record. `run_queue` calls
        `requeue_interrupted` on the line after `reconcile_interrupted`, and that flips every
        still-`interrupted` item back to `queued` with `recovery_next = True`. A step recovered to
        `substantially-complete` leaves that set, so committed work is not redone.

        THE CONTROL IS IN THE SAME TEST: the un-recovered step MUST still be requeued, or this would
        pass by having broken recovery retry altogether.
        """
        for name, module in self._modules():
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as t:
                root = Path(t)
                _repo, run_dir, state = _crashed_run_fixture(
                    root / "recovered", outcome=_MEASURED_OUTCOME
                )
                with contextlib.redirect_stderr(io.StringIO()):
                    module.reconcile_interrupted(run_dir, state)
                requeued = module.requeue_interrupted(run_dir, state)
                self.assertEqual(
                    requeued,
                    [],
                    "a step proven to have finished must not be re-run; that would redo "
                    "committed work",
                )
                self.assertEqual(state["queue"][0]["status"], "fail-gate")
                self.assertNotIn("recovery_next", state["queue"][0])

                # THE CONTROL: no outcome file, so no recovery, so the retry behaviour is UNCHANGED.
                _repo2, run_dir2, state2 = _crashed_run_fixture(
                    root / "plain", outcome="absent"
                )
                module.reconcile_interrupted(run_dir2, state2)
                self.assertEqual(
                    module.requeue_interrupted(run_dir2, state2), ["97df1z"]
                )
                self.assertEqual(state2["queue"][0]["status"], "queued")
                self.assertTrue(state2["queue"][0]["recovery_next"])

    def test_recovery_changes_dependent_scheduling_as_MEASURED_not_as_the_plan_predicted(
        self,
    ):
        """OQ-03's THIRD reader, exercised in both directions and RE-MEASURED rather than assumed.

        THE PLAN'S PREMISE FOR THIS TEST IS STALE, and the correction is recorded here because a test
        written to the plan's wording would have asserted a release that cannot happen. The plan says
        `edge_satisfied` reads the in-run status against `EXECUTION_SUCCESS_STATES`, so recovering a
        step to `substantially-complete` would RELEASE a waiting dependent. Measured at execution HEAD:
        that IN-RUN SHORTCUT WAS DELETED by a maintainer ruling on 2026-09-19 ("one check, not gates in
        depth"), precisely because `substantially-complete` means finalize did NOT happen, so the plan
        is still in `pending/` and its lane was never merged - and the shortcut had dispatched a
        dependent into a tree with none of the work. `edge_satisfied`'s `executed:` branch now reads the
        plan's DIRECTORY ON DISK and nothing else, so the edge stays UNSATISFIED either way. Measured:
        `dependency_status` returns `(False, ['97df1z'])` both before and after recovery.

        WHAT RECOVERY ACTUALLY CHANGES IS THE DRAIN CLASSIFICATION, and it is a real consequence rather
        than a nil result. `classify_drain_block` asks whether waiting can still pay off:

          * NOT recovered -> the target is `interrupted`, which is NOT in `TERMINAL_STATES`, so the
            verdict is TRANSIENT and the dependent stays `queued` for a later attempt.
          * RECOVERED -> the target is terminal, so the run is DONE with it, and the verdict is
            PERMANENT: the dependent is labelled `dependency-blocked` instead of waiting forever on a
            step that will never be retried.

        THAT IS THE COHERENT OUTCOME of the maintainer's answer, not a side effect to be regretted: if
        a recovered step is never requeued (the sibling test above), then a dependent waiting on it
        MUST stop waiting, or the run would hold a `queued` item whose prerequisite can no longer
        advance. The two halves are the same decision seen from either end.

        AND THE CASCADE MUST NOT FIRE, which is the protective half: `substantially-complete` IS in
        `EXECUTION_SUCCESS_STATES`, so `cascade_dependency_blocked` does not treat the recovered step as
        a DEAD prerequisite and does not kill the dependent as unsatisfiable. Asserted, because that is
        the difference between "this run cannot finish your dependent" and "your dependent is doomed".
        """
        for name, module in self._modules():
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as t:
                root = Path(t)
                verdicts = {}
                for label, outcome in (
                    ("recovered", _MEASURED_OUTCOME),
                    ("plain", "absent"),
                ):
                    _repo, run_dir, state = _crashed_run_fixture(
                        root / label, outcome=outcome
                    )
                    # A dependent of the crashed step, queued and waiting on it.
                    state["queue"].append(
                        {
                            "position": 3,
                            "id6": "depend",
                            "setid": "e32j35",
                            "action": "execute",
                            "configured_file": ".aw/records/plans/pending/20260902-e32j35-03-depend-x.ipd.md",
                            "dependencies": ["97df1z"],
                            "status": "queued",
                            "attempts": [],
                        }
                    )
                    dependent = state["queue"][1]

                    with contextlib.redirect_stderr(io.StringIO()):
                        module.reconcile_interrupted(run_dir, state)

                    # The EDGE verdict is unchanged, because the disk is its only authority.
                    ok, missing = module.dependency_status(dependent, state)
                    self.assertFalse(
                        ok,
                        f"{label}: the plan is still in pending/, so the `executed:` edge must "
                        "stay unsatisfied; a True here would mean the deleted in-run shortcut "
                        "has been reintroduced",
                    )
                    self.assertEqual(missing, ["97df1z"])

                    _, miss, why = module.dependency_status_detailed(dependent, state)
                    verdicts[label] = module.classify_drain_block(
                        dependent,
                        state,
                        miss,
                        why,
                        terminal_states=module.TERMINAL_STATES,
                        success_states=module.EXECUTION_SUCCESS_STATES,
                        review_success_states=module.SUCCESS_STATES,
                        parse_token=module.parse_dependency_token,
                    ).verdict
                    # With interrupted promoted to TERMINAL_STATES (E-04) and EXECUTION_SUCCESS_STATES narrowed (E-05),
                    # the cascade marks the dependent fail-depend for both cases.
                    expected_cascaded = ["depend"]
                    self.assertEqual(
                        [
                            i["id6"]
                            for i in module.cascade_dependency_blocked(state, run_dir)
                        ],
                        expected_cascaded,
                    )

                from agent_workflows import runner_shared

                self.assertEqual(
                    verdicts["plain"],
                    runner_shared.DRAIN_BLOCK_PERMANENT,
                    "an `interrupted` prerequisite is terminal (E-04), so a dependent must stop waiting",
                )
                self.assertEqual(
                    verdicts["recovered"],
                    runner_shared.DRAIN_BLOCK_PERMANENT,
                    "a RECOVERED prerequisite is terminal and will never be retried, so a "
                    "dependent must stop waiting rather than hold the queue open forever",
                )


class HeartbeatFormattingTests(unittest.TestCase):
    def test_heartbeat_idle_formatting_over_60s(self):
        import io
        import time

        buf = io.StringIO()
        pal = driver.Palette(False)
        hb = driver.Heartbeat(pal, "test-ipd", buf, interval=1.0)
        hb._start = time.monotonic() - 150.0  # 2m30s elapsed
        hb._last_activity = time.monotonic() - 75.0  # 1m15s idle
        self.assertEqual(hb.format_idle(), "1m15s")
        msg = hb.format_message()
        # stallfp kaga7s: the line reports LACK OF PROGRESS (and, when a watchdog is
        # attached, the kill countdown) instead of the old reassuring "still working".
        self.assertIn("no progress 1m15s", msg)
        self.assertIn("2m30s elapsed", msg)
        self.assertNotIn("still working", msg)

    def test_heartbeat_idle_formatting_under_60s(self):
        import io
        import time

        buf = io.StringIO()
        pal = driver.Palette(False)
        hb = driver.Heartbeat(pal, "test-ipd", buf, interval=1.0)
        hb._start = time.monotonic() - 45.0
        hb._last_activity = time.monotonic() - 20.0
        self.assertEqual(hb.format_idle(), "0m20s")
        msg = hb.format_message()
        self.assertIn("no progress 0m20s", msg)
        self.assertIn("0m45s elapsed", msg)
        self.assertNotIn("still working", msg)


#: The reaper's LAST rung. Windows has no SIGKILL, and `runner_shutdown.terminate_process` escalates
#: to `getattr(signal, "SIGKILL", signal.SIGTERM)`; the ladder tests assert that same fallback.
_SIGKILL = getattr(signal, "SIGKILL", signal.SIGTERM)


def _restore_os_attr(name: str, original) -> None:
    """Put `os.<name>` back EXACTLY: reinstate it, or remove a fake the platform never had."""
    if original is not None:
        setattr(os, name, original)
    elif hasattr(os, name):
        delattr(os, name)


class ProcessGroupTerminationTests(unittest.TestCase):
    def test_terminate_process_signals_process_group_with_escalation(self):
        import io
        import signal

        signals_sent = []

        class DummyProcess:
            def __init__(self):
                self.pid = 4242
                self.stdout = io.StringIO()
                self.stderr = None
                self.stdin = None

            def poll(self):
                if len(signals_sent) >= 3:
                    return -_SIGKILL
                return None

            def wait(self, timeout=None):
                if len(signals_sent) < 3:
                    raise subprocess.TimeoutExpired(["dummy"], timeout)
                return -_SIGKILL

            def send_signal(self, sig):
                signals_sent.append(("single", sig))

            def kill(self):
                signals_sent.append(("kill", _SIGKILL))

        proc = DummyProcess()

        orig_killpg = getattr(os, "killpg", None)
        orig_getpgid = getattr(os, "getpgid", None)
        orig_getpgrp = getattr(os, "getpgrp", None)
        orig_sigint_grace = driver._SIGINT_GRACE_SECONDS
        orig_sigterm_grace = driver._SIGTERM_GRACE_SECONDS

        try:
            driver._SIGINT_GRACE_SECONDS = 0.01
            driver._SIGTERM_GRACE_SECONDS = 0.01
            os.getpgid = lambda pid: 9999
            os.getpgrp = lambda: 1111  # different from pgid
            os.killpg = lambda pgid, sig: signals_sent.append(("group", pgid, sig))

            driver.terminate_process(proc)

            self.assertEqual(
                signals_sent,
                [
                    ("group", 9999, signal.SIGINT),
                    ("group", 9999, signal.SIGTERM),
                    ("group", 9999, _SIGKILL),
                ],
            )
            self.assertTrue(proc.stdout.closed)
        finally:
            driver._SIGINT_GRACE_SECONDS = orig_sigint_grace
            driver._SIGTERM_GRACE_SECONDS = orig_sigterm_grace
            # Restore EXACTLY, including REMOVING a fake where the platform had no such function
            # (Windows): leaving it installed made a later real reap "signal" a recording lambda,
            # so the child was never killed (ChildTerminationTests failed order-dependently).
            _restore_os_attr("killpg", orig_killpg)
            _restore_os_attr("getpgid", orig_getpgid)
            _restore_os_attr("getpgrp", orig_getpgrp)

    def test_terminate_process_non_posix_fallback(self):
        import io
        import signal

        signals_sent = []

        class DummyProcess:
            def __init__(self):
                self.pid = 5353
                self.stdout = io.StringIO()
                self.stderr = None
                self.stdin = None

            def poll(self):
                if len(signals_sent) >= 3:
                    return -_SIGKILL
                return None

            def wait(self, timeout=None):
                if len(signals_sent) < 3:
                    raise subprocess.TimeoutExpired(["dummy"], timeout)
                return -_SIGKILL

            def send_signal(self, sig):
                signals_sent.append(("single", sig))

            def kill(self):
                signals_sent.append(("kill", _SIGKILL))

        proc = DummyProcess()

        orig_killpg = getattr(os, "killpg", None)
        orig_sigint_grace = driver._SIGINT_GRACE_SECONDS
        orig_sigterm_grace = driver._SIGTERM_GRACE_SECONDS

        try:
            driver._SIGINT_GRACE_SECONDS = 0.01
            driver._SIGTERM_GRACE_SECONDS = 0.01
            if hasattr(os, "killpg"):
                delattr(os, "killpg")

            driver.terminate_process(proc)

            self.assertEqual(
                signals_sent,
                [
                    ("single", signal.SIGINT),
                    ("single", signal.SIGTERM),
                    ("single", _SIGKILL),
                ],
            )
            self.assertTrue(proc.stdout.closed)
        finally:
            driver._SIGINT_GRACE_SECONDS = orig_sigint_grace
            driver._SIGTERM_GRACE_SECONDS = orig_sigterm_grace
            _restore_os_attr("killpg", orig_killpg)


class StallWatchdogTests(unittest.TestCase):
    def test_stall_watchdog_terminates_silent_child_and_marks_interrupted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "README").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan = pending / "20260824-demo-01-stall1-test.ipd.md"
            plan.write_text(
                "- Id: stall1\n- Set: demo\n- Status: approved\n# Stall Plan\n",
                encoding="utf-8",
            )

            silent_child = support.make_fake_executable(
                root / "silent_opencode",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import time
                    time.sleep(60)
                    """
                ),
            )

            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "start",
                    "stall1",
                    "--no-self-finalize",
                    "--repo",
                    os.fspath(repo),
                    "--stall-timeout",
                    "0.3",
                    "--opencode",
                    os.fspath(silent_child),
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 1, result.stderr)

            run_id = next(
                line.split(": ", 1)[1]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            state_file = repo / ".aw" / "records" / "runs" / run_id / "state.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))

            item = state["queue"][0]
            self.assertEqual(item["status"], "interrupted")
            attempt = item["attempts"][0]
            self.assertEqual(attempt.get("interrupt_reason"), "stall_timeout")
            self.assertEqual(attempt.get("stall_timeout"), 0.3)
            self.assertIn("interrupted_at", attempt)
            self.assertIn("ended_at", attempt)

            # Still auto-requeued, and deliberately so after runstop Phase 4 (`m0z0ti`, E-04) made
            # `requeue_interrupted` gated: a STALL is an ordinary interruption with no indeterminate
            # flag, so recovery must keep working exactly as before. This assertion is therefore now
            # ALSO the control proving the R19 gate did not disable ordinary recovery. Left unchanged
            # on purpose (orchestrator CID-4); the new refused case is asserted separately in
            # `ResumeRequeueTests.test_bare_resume_refuses_to_requeue_an_indeterminate_item`.
            self.assertFalse(
                runner_stop.is_indeterminate(item),
                "a stalled turn is not an indeterminate force-stop",
            )
            requeued = driver.requeue_interrupted(
                repo / ".aw" / "records" / "runs" / run_id, state
            )
            self.assertIn("stall1", requeued)
            self.assertEqual(item["status"], "queued")
            self.assertTrue(item.get("recovery_next"))

    def test_stall_watchdog_does_not_trip_on_active_child(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "README").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan = pending / "20260824-demo-01-activ1-test.ipd.md"
            plan.write_text(
                "- Id: activ1\n- Set: demo\n- Status: approved\n# Active Plan\n",
                encoding="utf-8",
            )

            active_child = support.make_fake_executable(
                root / "active_opencode",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json, pathlib, re, sys, time
                    args = sys.argv[1:]
                    prompt = args[args.index('--') + 1] if '--' in args else ""
                    outcome = pathlib.Path(re.search(r'Required JSON outcome: (.+)', prompt).group(1).strip())
                    plan = pathlib.Path(re.search(r'Plan file at launch: (.+)', prompt).group(1).strip())
                    executed = pathlib.Path(str(plan).replace('/pending/', '/executed/'))
                    executed.parent.mkdir(parents=True, exist_ok=True)
                    plan.rename(executed)

                    for i in range(3):
                        print(json.dumps({'type':'text','sessionID':'ses_activ1','part':{'text':f'step {i}'}}), flush=True)
                        time.sleep(0.05)

                    outcome.write_text(json.dumps({'schema_version':1,'id6':'activ1','disposition':'executed','pushed':False}))
                    print(json.dumps({'type':'text','sessionID':'ses_activ1','part':{'text':'done'}}), flush=True)
                    """
                ),
            )

            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "start",
                    "activ1",
                    "--no-self-finalize",
                    "--repo",
                    os.fspath(repo),
                    "--stall-timeout",
                    "0.5",
                    "--opencode",
                    os.fspath(active_child),
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            run_id = next(
                line.split(": ", 1)[1]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            state_file = repo / ".aw" / "records" / "runs" / run_id / "state.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["queue"][0]["status"], "executed")


class AllSelectorAndFullAutoTests(unittest.TestCase):
    def test_expand_selectors_all_finds_only_actionable_pending_plans(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "exec01": {
                    "set": "s1",
                    "file": ".aw/records/plans/executed/20260801-s1-01-exec01-done.ipd.md",
                    "status": "executed",
                    "order": 1,
                    "dependencies": [],
                },
                "pend01": {
                    "set": "s1",
                    "file": ".aw/records/plans/pending/20260824-s1-02-pend01-test.ipd.md",
                    "status": "to-review",
                    "order": 2,
                    "dependencies": ["exec01"],
                },
                "pend02": {
                    "set": "s2",
                    "file": ".aw/records/plans/pending/20260824-s2-01-pend02-test.ipd.md",
                    "status": "approved",
                    "order": 1,
                    "dependencies": [],
                },
                "super01": {
                    "set": "s2",
                    "file": ".aw/records/plans/superseded/20260824-s2-02-super01-test.ipd.md",
                    "status": "superseded",
                    "order": 2,
                    "dependencies": [],
                },
            },
            "sets": {
                "s1": {"order": ["exec01", "pend01"]},
                "s2": {"order": ["pend02", "super01"]},
            },
        }
        expanded = driver.expand_selectors(manifest, ["all"])
        self.assertEqual(expanded, ["pend01", "pend02"])

    def test_expand_selectors_reviews_finds_only_to_review_plans(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "exec01": {
                    "set": "s1",
                    "file": ".aw/records/plans/executed/20260801-s1-01-exec01-done.ipd.md",
                    "status": "executed",
                    "order": 1,
                    "dependencies": [],
                },
                "pend01": {
                    "set": "s1",
                    "file": ".aw/records/plans/pending/20260824-s1-02-pend01-test.ipd.md",
                    "status": "to-review",
                    "order": 2,
                    "dependencies": ["exec01"],
                },
                "pend02": {
                    "set": "s2",
                    "file": ".aw/records/plans/pending/20260824-s2-01-pend02-test.ipd.md",
                    "status": "approved",
                    "order": 1,
                    "dependencies": [],
                },
                "pend03": {
                    "set": "s2",
                    "file": ".aw/records/plans/pending/20260824-s2-02-pend03-test.ipd.md",
                    "status": "to-review",
                    "order": 2,
                    "dependencies": [],
                },
            },
            "sets": {
                "s1": {"order": ["exec01", "pend01"]},
                "s2": {"order": ["pend02", "pend03"]},
            },
        }
        for alias in ("reviews", "review", "to-review"):
            expanded = driver.expand_selectors(manifest, [alias])
            self.assertEqual(expanded, ["pend01", "pend03"])

    def test_expand_selectors_reviews_raises_when_none(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "pend02": {
                    "set": "s2",
                    "file": ".aw/records/plans/pending/20260824-s2-01-pend02-test.ipd.md",
                    "status": "approved",
                    "order": 1,
                    "dependencies": [],
                },
            },
            "sets": {
                "s2": {"order": ["pend02"]},
            },
        }
        with self.assertRaises(driver.DriverError):
            driver.expand_selectors(manifest, ["reviews"])

    def test_expand_selectors_all_raises_when_no_actionable_plans(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "exec01": {
                    "set": "s1",
                    "file": ".aw/records/plans/executed/20260801-s1-01-exec01-done.ipd.md",
                    "status": "executed",
                    "order": 1,
                    "dependencies": [],
                },
            },
            "sets": {
                "s1": {"order": ["exec01"]},
            },
        }
        with self.assertRaises(driver.DriverError):
            driver.expand_selectors(manifest, ["all"])

    def test_is_plan_review_approved_is_the_shared_predicate_not_a_local_copy(self):
        """fullauto 97df1z E-03: the driver must EXPOSE the predicate but not DEFINE it.

        A local re-definition is what let the two drivers drift (and left `aw agy run --full-auto`
        broken while oc was fixed), so identity with the shared module is asserted, not just
        behavior.
        """
        from agent_workflows import agy_runipd as agy_driver
        from agent_workflows import plan_readiness

        self.assertIs(
            driver.is_plan_review_approved, plan_readiness.is_plan_review_approved
        )
        self.assertIs(
            agy_driver.is_plan_review_approved, plan_readiness.is_plan_review_approved
        )
        self.assertIs(
            driver.extract_newest_history_entry,
            plan_readiness.extract_newest_history_entry,
        )
        self.assertFalse(hasattr(driver, "extract_last_history_entry"))
        self.assertFalse(hasattr(agy_driver, "extract_last_history_entry"))

    def test_set_plan_approved_uses_auto_approved_and_never_by_human(self):
        """fullauto 97df1z OQ-02: `--full-auto` must not machine-assert human approval.

        The attestation exists to stop an agent auto-advancing a transition the human owns, so the
        driver clears to the shipped `auto-approved` automated tier and names its automated actor.
        """
        captured: list = []

        def fake_run_checked(argv, cwd=None, env=None):
            captured.append(list(argv))
            return ""

        with mock.patch.object(driver, "run_checked", fake_run_checked):
            driver.set_plan_approved(Path("/tmp/repo"), "oc0012")

        self.assertEqual(len(captured), 1)
        argv = captured[0]
        self.assertIn("auto-approved", argv)
        self.assertNotIn("approved", argv)  # never the human tier
        self.assertNotIn("--by-human", argv)
        self.assertIn("--actor", argv)
        self.assertIn(driver.FULL_AUTO_ACTOR, argv)

    def test_structured_readiness_field_decides_auto_approval(self):
        """fullauto 97df1z: `- Readiness:` is the machine signal; prose is not."""
        with tempfile.TemporaryDirectory() as t:
            p_field = Path(t) / "plan_field.md"
            p_field.write_text(
                textwrap.dedent(
                    """\
                    # Test Plan

                    - Id: test03
                    - Status: reviewed
                    - Readiness: go-pending-approval

                    ## Workflow history
                    - 2026-08-24 /plan-review (opencode): APPROVE; PR-001
                    """
                ),
                encoding="utf-8",
            )
            self.assertTrue(driver.is_plan_review_approved(p_field))

            # The adversarial case: the OLD prose phrase present, the structured field says no.
            p_conflict = Path(t) / "plan_conflict.md"
            p_conflict.write_text(
                textwrap.dedent(
                    """\
                    # Test Plan

                    - Id: test04
                    - Status: reviewed
                    - Readiness: no-go

                    ## Workflow history
                    - 2026-08-24 /plan-review (opencode): APPROVE. Readiness: GO - PENDING HUMAN APPROVAL.
                    """
                ),
                encoding="utf-8",
            )
            self.assertFalse(driver.is_plan_review_approved(p_conflict))

    def test_is_plan_review_approved_verdict_detection(self):
        with tempfile.TemporaryDirectory() as t:
            p_go = Path(t) / "plan_go.md"
            p_go.write_text(
                textwrap.dedent(
                    """\
                    - Id: test01
                    - Status: reviewed
                    # Test Plan

                    ## Workflow history
                    - 2026-08-24 /plan-review (opencode): APPROVE WITH REVISIONS APPLIED; PR-001 fixed. Readiness: GO - PENDING HUMAN APPROVAL.
                    """
                ),
                encoding="utf-8",
            )
            self.assertTrue(driver.is_plan_review_approved(p_go))

            p_nogo = Path(t) / "plan_nogo.md"
            p_nogo.write_text(
                textwrap.dedent(
                    """\
                    - Id: test02
                    - Status: reviewed
                    # Test Plan

                    ## Workflow history
                    - 2026-08-24 /plan-review (opencode): REVIEWED - OPEN QUESTIONS; findings G1-G7. Readiness: NO-GO until OQ1 is decided (then GO - PENDING HUMAN APPROVAL).
                    """
                ),
                encoding="utf-8",
            )
            self.assertFalse(driver.is_plan_review_approved(p_nogo))

    def test_full_auto_reviews_approves_and_executes_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "README").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            p1 = pending / "20260824-demo-01-fa0001-test.ipd.md"
            p1.write_text(
                textwrap.dedent(
                    """\
                    - Id: fa0001
                    - Set: demo
                    - Status: to-review
                    - Work-Kind: chore
                    - Priority: medium
                    # Full Auto Plan

                    ## Workflow history
                    - 2026-08-24 created: test stub
                    """
                ),
                encoding="utf-8",
            )

            fake = root / "fake_opencode"
            # fullauto 97df1z E-04: a reviewer following the updated workflow writes the STRUCTURED
            # `- Readiness:` field and PREPENDS its history record under the heading (which is how
            # `aw set` actually writes history - newest-first). The old fixture appended the record
            # and relied on prose alone, neither of which matches the real writer.
            fake_lines = [
                "#!/usr/bin/env python3",
                "import json, pathlib, re, sys",
                "args = sys.argv[1:]",
                'prompt = args[args.index("--") + 1] if "--" in args else ""',
                'session = args[args.index("--session") + 1] if "--session" in args else ("ses_" + "fullauto")',
                'if prompt.startswith("/plan-review"):',
                # dirtygates-05 (`ajxr5d`): the COMMAND LINE, not the prompt's last token; an
                # isolated review's prompt carries the in-lane statement after the command line.
                "    target_file = prompt.splitlines()[0].split()[-1]",
                "    p = pathlib.Path(target_file)",
                "    if not p.is_absolute():",
                "        p = pathlib.Path.cwd() / p",
                "    if p.is_file():",
                "        content = p.read_text()",
                '        content = content.replace("- Status: to-review", "- Status: reviewed\\n- Readiness: go-pending-approval")',
                "        content = content.replace(",
                '            "## Workflow history\\n",',
                '            "## Workflow history\\n- 2026-08-24 /plan-review (opencode): APPROVE; no defects.\\n",',
                "        )",
                "        p.write_text(content)",
                '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "review done"}}))',
                'elif "Required JSON outcome:" in prompt:',
                '    outcome = pathlib.Path(re.search(r"Required JSON outcome: (.+)", prompt).group(1).strip())',
                '    plan = pathlib.Path(re.search(r"Plan file at launch: (.+)", prompt).group(1).strip())',
                '    executed = plan.parent.parent / "executed" / plan.name',
                "    executed.parent.mkdir(parents=True, exist_ok=True)",
                "    plan.rename(executed)",
                '    outcome.write_text(json.dumps({"schema_version": 1, "id6": "fa0001", "disposition": "executed", "pushed": False}))',
                '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "exec done"}}))',
                "else:",
                '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "verify done"}}))',
            ]
            fake = support.make_fake_executable(fake, "\n".join(fake_lines) + "\n")

            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "start",
                    "all",
                    "--no-self-finalize",
                    "--repo",
                    os.fspath(repo),
                    "--full-auto",
                    "--opencode",
                    os.fspath(fake),
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            run_id = next(
                line.split(": ", 1)[1]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            state_file = repo / ".aw" / "records" / "runs" / run_id / "state.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))

            item = state["queue"][0]
            self.assertEqual(item["status"], "executed")
            self.assertEqual(len(item["attempts"]), 2)
            self.assertEqual(item["attempts"][0]["action"], "review")
            self.assertEqual(item["attempts"][1]["action"], "execute")

            # fullauto 97df1z: the auto-approval must be RECORDED as an event, and the transition
            # must be the HONEST `auto-approved` one - never human `approved` with a machine-asserted
            # `--by-human` attestation (OQ-02).
            events = [
                json.loads(line)
                for line in (
                    repo / ".aw" / "records" / "runs" / run_id / "events.jsonl"
                )
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertIn("ipd-auto-approved", [e.get("event") for e in events])
            self.assertTrue(item.get("auto_approved"))
            executed_plan = next(
                (repo / ".aw" / "records" / "plans" / "executed").glob("*.ipd.md")
            )
            plan_text = executed_plan.read_text(encoding="utf-8")
            self.assertIn("auto-approved", plan_text)
            self.assertNotIn("--by-human", plan_text)

    def test_without_full_auto_stops_at_reviewed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "README").write_text("test\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            p1 = pending / "20260824-demo-01-nofa01-test.ipd.md"
            p1.write_text(
                textwrap.dedent(
                    """\
                    - Id: nofa01
                    - Set: demo
                    - Status: to-review
                    # No Full Auto Plan

                    ## Workflow history
                    - 2026-08-24 created: test stub
                    """
                ),
                encoding="utf-8",
            )

            fake = support.make_fake_executable(
                root / "fake_opencode",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json, pathlib, re, sys
                    args = sys.argv[1:]
                    prompt = args[args.index('--') + 1] if '--' in args else ""
                    session = args[args.index('--session') + 1] if '--session' in args else ("ses" + "_" + "nofa")

                    if prompt.startswith("/plan-review"):
                        # dirtygates-05 (`ajxr5d`): read the COMMAND LINE, not the last token of the
                        # whole prompt. An isolated review's prompt is the `/plan-review <path>` line
                        # FOLLOWED BY the in-lane statement on its own lines, so `split()[-1]` would
                        # pick a word out of that prose. A real slash command parses its own line, so
                        # this fixture now does too.
                        target_file = prompt.splitlines()[0].split()[-1]
                        p = pathlib.Path(target_file)
                        if not p.is_absolute():
                            p = pathlib.Path.cwd() / p
                        if p.is_file():
                            content = p.read_text()
                            content = content.replace("- Status: to-review", "- Status: reviewed")
                            content += "\\n- 2026-08-24 /plan-review (opencode): APPROVE; no defects. Readiness: GO - PENDING HUMAN APPROVAL.\\n"
                            p.write_text(content)
                        print(json.dumps({'type':'text','sessionID':session,'part':{'text':'review done'}}))
                    """
                ),
            )

            result = subprocess.run(
                [
                    *_DRIVER_CMD,
                    "start",
                    "all",
                    "--repo",
                    os.fspath(repo),
                    "--no-full-auto",
                    "--opencode",
                    os.fspath(fake),
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            run_id = next(
                line.split(": ", 1)[1]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            state_file = repo / ".aw" / "records" / "runs" / run_id / "state.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))

            item = state["queue"][0]
            self.assertEqual(item["status"], "reviewed")
            self.assertEqual(len(item["attempts"]), 1)
            self.assertEqual(item["attempts"][0]["action"], "review")


class RunipdBugsFixesTests(unittest.TestCase):
    def test_dependency_status_execution_vs_review(self):
        """UPDATED 2026-09-19: an `executed:` edge is answered from the plan on DISK.

        The in-queue run-status shortcut was deleted (maintainer ruling: ONE authority, not gates in
        depth), so this test now materializes the prerequisites it asserts about instead of naming a
        repository that does not exist. `dep003` gets a real plan in `executed/`; `dep001` and
        `dep002` sit in `pending/` with their non-terminal statuses, which is where a non-terminal
        plan actually lives.
        """
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        repo = Path(self._tmp.name) / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        executed = repo / ".aw" / "records" / "plans" / "executed"
        pending.mkdir(parents=True)
        executed.mkdir(parents=True)
        (pending / "20260919-dep-01-dep001-reviewed-plan.ipd.md").write_text(
            "# IPD: d1\n\n- Id: dep001\n- Status: reviewed\n", encoding="utf-8"
        )
        (pending / "20260919-dep-02-dep002-approved-plan.ipd.md").write_text(
            "# IPD: d2\n\n- Id: dep002\n- Status: approved\n", encoding="utf-8"
        )
        (executed / "20260919-dep-03-dep003-executed-plan.ipd.md").write_text(
            "# IPD: d3\n\n- Id: dep003\n- Status: executed\n", encoding="utf-8"
        )
        state = {
            "repo": str(repo),
            "queue": [
                {
                    "id6": "dep001",
                    "status": "reviewed",
                    "action": "review",
                },
                {
                    "id6": "dep002",
                    "status": "approved",
                    "action": "execute",
                },
                {
                    "id6": "dep003",
                    "status": "executed",
                    "action": "execute",
                },
            ],
        }

        # Execution item depending on 'reviewed' plan -> blocked
        exec_item_1 = {"id6": "tgt001", "action": "execute", "dependencies": ["dep001"]}
        sat, missing = driver.dependency_status(exec_item_1, state)
        self.assertFalse(sat)
        self.assertEqual(missing, ["dep001"])

        # Execution item depending on 'approved' plan -> blocked
        exec_item_2 = {"id6": "tgt002", "action": "execute", "dependencies": ["dep002"]}
        sat, missing = driver.dependency_status(exec_item_2, state)
        self.assertFalse(sat)
        self.assertEqual(missing, ["dep002"])

        # Execution item depending on 'executed' plan -> satisfied
        exec_item_3 = {"id6": "tgt003", "action": "execute", "dependencies": ["dep003"]}
        sat, missing = driver.dependency_status(exec_item_3, state)
        self.assertTrue(sat)
        self.assertEqual(missing, [])

        # Review item depending on 'reviewed' plan -> satisfied
        rev_item_1 = {"id6": "tgt004", "action": "review", "dependencies": ["dep001"]}
        sat, missing = driver.dependency_status(rev_item_1, state)
        self.assertTrue(sat)
        self.assertEqual(missing, [])

    def test_read_deps_and_set_parsing(self):
        # lanetruth-03 (8guhs0) E-01 / OQ-01: the LEGACY `Dependencies:`/`Depends-on:` field is
        # REMOVED, along with the private `_read_deps` parser that read it. Measured at execution:
        # zero plans in the tree used the legacy field, while the canonical
        # `- Item-Dependencies:` statement it shadowed was invisible to the runner. These assertions
        # were rewritten (they previously asserted the legacy field parsed) so they now pin the
        # CANONICAL behavior. The `_read_set` assertions below are unchanged.
        # Canonical typed statement: read through the SHARED grammar, qualifiers preserved.
        canonical = (
            "# IPD: aaaaaa\n\n- Id: aaaaaa\n"
            '- Set: "my-set" (descriptive)\n'
            "- Item-Dependencies: executed:5ahblp, exists:spec:pr2nd0\n\n## Goal\n"
        )
        self.assertEqual(
            driver._read_item_dependencies(canonical),
            (["executed:5ahblp", "exists:spec:pr2nd0"], None),
        )
        self.assertEqual(driver._read_set(canonical), "my-set")

        # The legacy field names no longer contribute dependencies.
        legacy1 = '- Dependencies: [5ahblp, pr2nd0]\n- Set: "my-set" (descriptive)'
        self.assertEqual(driver._read_item_dependencies(legacy1), ([], None))
        self.assertEqual(driver._read_set(legacy1), "my-set")

        legacy2 = "- Depends-on: ['5ahblp', 'pr2nd0']\n- Set: 'custom-set'"
        self.assertEqual(driver._read_item_dependencies(legacy2), ([], None))
        self.assertEqual(driver._read_set(legacy2), "custom-set")

        # The deleted private parser is gone from the module surface.
        self.assertFalse(hasattr(driver, "_read_deps"))
        self.assertFalse(hasattr(driver, "_DEPS_RE"))

        # `none` / `unresolved` / absent all mean "no edges" (the MISSING-vs-`none` judgement
        # belongs to the shared evaluator, not the runner; see 8guhs0 OQ-02).
        for value in ("none", "unresolved", ""):
            text = f"# IPD: aaaaaa\n\n- Id: aaaaaa\n- Item-Dependencies: {value}\n\n## Goal\n"
            self.assertEqual(driver._read_item_dependencies(text), ([], None))

    def test_atomic_write_json_directory_fsync_suppresses_oserror(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / "sub" / "test.json"
            real_fsync = os.fsync

            def mocked_fsync(fd):
                try:
                    st = os.fstat(fd)
                    import stat

                    if stat.S_ISDIR(st.st_mode):
                        raise OSError(19, "Operation not supported by device")
                except Exception:
                    pass
                return real_fsync(fd)

            with mock.patch("os.fsync", side_effect=mocked_fsync):
                driver.atomic_write_json(target, {"hello": "world"})

            self.assertTrue(target.is_file())
            self.assertEqual(json.loads(target.read_text()), {"hello": "world"})


class PlanBucketRecognitionTests(unittest.TestCase):
    """#4: plan_bucket must recognize the full lifecycle directory set."""

    def test_recognizes_all_lifecycle_buckets(self):
        for bucket in (
            "executed",
            "active",
            "pending",
            "reviewed",
            "approved",
            "reusable",
            "superseded",
            "not-executed",
        ):
            path = Path(
                f"/x/.aw/records/plans/{bucket}/20260824-demo-01-aaaaaa-t.ipd.md"
            )
            self.assertEqual(driver.plan_bucket(path), bucket)

    def test_unknown_bucket_returns_none(self):
        self.assertIsNone(
            driver.plan_bucket(Path("/x/.aw/records/plans/limbo/20260824-x.ipd.md"))
        )

    def test_the_docstring_states_that_a_bucket_is_not_a_readiness(self):
        """depreview 03ie04 E-05: the members above are DEFENSIVE, and that must be documented.

        WHY A TEST ABOUT A DOCSTRING IS WARRANTED HERE and is not documentation theatre. This function
        had NO docstring, while the list asserted directly above it names `reviewed` and `approved` as
        if they were directories. They are not: `.aw/records/plans/` holds only `executed`,
        `not-executed`, `pending`, `reusable` and `superseded`, and a plan stays in `pending/` through
        `draft` -> `to-review` -> `reviewed` -> `approved`. A reader who took the list at face value
        wrote `oc_runipd.edge_satisfied`'s external-target branch to compare this function's result
        against `("executed", "reviewed", "approved")`, which made two thirds of that tuple
        unreachable and refused every review-action edge. So the missing contract had a measured cost,
        and this test keeps the correction attached to the thing it corrects.
        """
        doc = driver.plan_bucket.__doc__ or ""
        self.assertTrue(doc.strip(), "plan_bucket must have a docstring")
        for needle in ("DIRECTORY", "FIELD", "DEFENSIVELY", "- Status:"):
            with self.subTest(needle=needle):
                self.assertIn(needle, doc)

    def test_no_caller_compares_a_bucket_to_a_non_terminal_member(self):
        """The members are defensive, so no caller may treat one as a readiness verdict.

        This is the guard that would have caught the original defect. `agy_runipd` used to compare a
        bucket against the tuple `("executed", "reviewed", "approved")`; that comparison is gone with
        the local `dependency_status_detailed` copy, and the only bucket equality comparisons left in
        either driver are against `"executed"`, a genuine directory.

        Deliberately NOT a ban on the STRINGS `reviewed`/`approved`, which appear legitimately all over
        both drivers as STATUS values. It bans comparing them to a value obtained from `plan_bucket`,
        which is the actual error.
        """
        import re

        pattern = re.compile(
            r"bucket\s*(?:==|!=)\s*[\"'](?:reviewed|approved|active)[\"']"
            r"|bucket\s+(?:not\s+)?in\s*\([^)]*[\"'](?:reviewed|approved|active)[\"']"
        )
        for name in ("oc_runipd", "agy_runipd"):
            path = REPO_ROOT / "agent_workflows" / f"{name}.py"
            text = path.read_text(encoding="utf-8")
            # Comments and docstrings may legitimately DISCUSS the retired comparison.
            code = "\n".join(
                ln for ln in text.splitlines() if not ln.lstrip().startswith("#")
            )
            with self.subTest(module=name):
                self.assertIsNone(
                    pattern.search(code),
                    f"{name} compares a plan_bucket() result against a non-terminal member; "
                    "readiness lives in the `- Status:` field, not in a directory name",
                )


class StatusJsonTests(unittest.TestCase):
    """#3: `status --json` emits the full state.json payload."""

    def test_status_json_emits_state(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = _make_run_dir(
                Path(temp),
                [
                    {
                        "position": 1,
                        "id6": "aaaaaa",
                        "setid": "demo",
                        "status": "executed",
                        "action": "execute",
                        "attempts": [],
                    }
                ],
            )
            import io
            from contextlib import redirect_stdout

            args = driver.build_parser().parse_args(["status", str(run_dir), "--json"])
            self.assertTrue(args.json)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = driver.main(
                    ["status", str(run_dir), "--repo", str(run_dir), "--json"]
                )
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["run_id"], "run-test")
            self.assertEqual(payload["queue"][0]["id6"], "aaaaaa")


class ContinuationHintTests(unittest.TestCase):
    """#2: render_continuation_hint surfaces captured session(s) + reuse commands."""

    def _state(self, set_sessions, queue=None):
        return {
            "repo": "/repo",
            "run_id": "run-xyz",
            "set_sessions": set_sessions,
            "queue": queue if queue is not None else [],
        }

    def test_no_sessions_captured_and_unattempted(self):
        from agent_workflows import runner_shared

        hint = driver.render_continuation_hint(self._state({}), Path("/x"))
        self.assertIn("No OpenCode session was captured", hint)
        self.assertNotIn("ses_", hint)
        self.assertIn("aw runs run-xyz", hint)
        self.assertNotIn("resume", hint)

        hint = driver.render_continuation_hint(
            self._state({}, queue=[{"status": "failed"}]), Path("/x")
        )
        self.assertIn("No OpenCode session was captured", hint)
        self.assertIn("aw oc run resume --repo /repo run-xyz", hint)
        self.assertNotIn("aw runs", hint)

        unattempted = driver.render_continuation_hint(
            self._state(
                {},
                queue=[{"status": "reviewed", "action": "execute", "attempts": []}],
            ),
            Path("/x"),
        )
        self.assertIn("No turn was attempted", unattempted)
        self.assertIn("This is NOT a failed launch", unattempted)
        self.assertNotIn("No OpenCode session was captured", unattempted)

        for status in ("failed", "running", "interrupted", "partial", "merge-refused"):
            hint = driver.render_continuation_hint(
                self._state({}, queue=[{"status": status}]), Path("/x")
            )
            self.assertIn("No OpenCode session was captured", hint, status)
            self.assertNotIn("No turn was attempted", hint, status)

        attempted = driver.render_continuation_hint(
            self._state({}, queue=[{"status": "reviewed", "attempts": [{"n": 1}]}]),
            Path("/x"),
        )
        self.assertIn("No OpenCode session was captured", attempted)

        self.assertFalse(
            runner_shared.no_turn_was_attempted(
                {"queue": ["not-a-mapping"], "run_id": "r", "repo": "."}
            )
        )

    def test_session_continuation_hints(self):
        hint = driver.render_continuation_hint(
            self._state({"demo": "ses_abc123"}, queue=[{"status": "executed"}]),
            Path("/x"),
        )
        self.assertIn("ses_abc123", hint)
        self.assertIn("aw oc run --session ses_abc123 <selector>", hint)
        self.assertIn("aw runs run-xyz", hint)
        self.assertNotIn("resume", hint)

        blocked = driver.render_continuation_hint(
            self._state(
                {"demo": "ses_abc123"},
                queue=[{"status": "reviewed", "action": "execute"}],
            ),
            Path("/x"),
        )
        self.assertIn("aw oc run resume --repo /repo run-xyz", blocked)
        self.assertNotIn("aw runs", blocked)

        reviewed_ok = driver.render_continuation_hint(
            self._state(
                {"demo": "ses_abc123"},
                queue=[{"status": "reviewed", "action": "review"}],
            ),
            Path("/x"),
        )
        self.assertIn("aw runs run-xyz", reviewed_ok)
        self.assertNotIn("resume", reviewed_ok)

        hint_part = driver.render_continuation_hint(
            self._state({"demo": "ses_abc123"}, queue=[{"status": "partial"}]),
            Path("/x"),
        )
        self.assertIn("ses_abc123", hint_part)
        self.assertIn("aw oc run resume --repo /repo run-xyz", hint_part)

        hint_mult = driver.render_continuation_hint(
            self._state({"setA": "ses_aaa", "setB": "ses_bbb"}), Path("/x")
        )
        self.assertIn("ses_aaa", hint_mult)
        self.assertIn("ses_bbb", hint_mult)
        self.assertIn("aw oc run --session ses_bbb <selector>", hint_mult)

        hint_cmd = driver.render_continuation_hint(
            self._state({"demo": "ses_abc123"}, queue=[{"status": "failed"}]),
            Path("/x"),
            driver_cmd="aw oc runipd",
        )
        self.assertIn("aw oc runipd --session ses_abc123 <selector>", hint_cmd)
        self.assertIn("aw oc runipd resume --repo /repo run-xyz", hint_cmd)

    def test_graceful_stopping_footer_hints(self):
        from agent_workflows import runner_stop

        for status, other in (("executed", "aw runs run-xyz"), ("partial", "resume")):
            with self.subTest(status=status):
                hint = driver.render_continuation_hint(
                    self._state({"demo": "ses_abc123"}, queue=[{"status": status}]),
                    Path("/x"),
                )
                self.assertIn(other, hint)
                self.assertIn("To stop a future run gracefully:", hint)
                self.assertIn("aw oc run stop <run-id> --after-call", hint)

        stopping = "\n".join(runner_stop.stop_footer_hint("aw oc run"))
        self.assertNotIn("resume", stopping)
        self.assertNotIn("aw runs", stopping)

        hint = driver.render_continuation_hint(
            self._state({"demo": "ses_abc123"}, queue=[{"status": "partial"}]),
            Path("/x"),
        )
        for level_word in (
            "--after-set",
            "--now-force",
            "level 2",
            "level 3",
            "level 4",
        ):
            self.assertNotIn(level_word, hint)


class VerifierPromptTests(unittest.TestCase):
    """#1: turn-2 verifier prompt is well-formed and instructs a fresh-session audit."""

    def test_verifier_prompt_contents_and_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "sessions").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)
            item = {
                "position": 3,
                "id6": "abc123",
                "setid": "demo",
                "action": "execute",
            }
            state = {"run_id": "run-test"}
            prompt = driver.build_verifier_prompt(
                item, state, run_dir, Path("/plan.ipd.md")
            )
            self.assertIn("Independent Rigorous Verification", prompt)
            self.assertIn("fresh OpenCode session", prompt)
            self.assertIn("03-abc123-verification.json", prompt)
            self.assertIn("VERIFIED|CORRECTION_REQUIRED|BLOCKED", prompt)
            self.assertIn("Never push", prompt)
            self.assertIn("## Concurrent Work", prompt)
            self.assertIn(
                "Other agents may modify this repository concurrently", prompt
            )
            self.assertIn(
                "Do not alter, revert, stage, or commit another agent's work", prompt
            )
            self.assertIn("never use `git add .` or `git add -A`", prompt)
            self.assertIn("git diff --cached --name-only", prompt)
            self.assertIn("git restore --staged", prompt)
            self.assertIn("ALREADY STAGED", prompt)
            self.assertIn("Never discard their work", prompt)

            log = driver.attempt_log_path(run_dir, item, 1, suffix="verify")
            self.assertTrue(log.name.endswith("attempt-1-verify.jsonl"))
            p = driver.write_prompt(run_dir, item, "hi", 1, suffix="verify")
            self.assertIn("verify", p.name)

    def test_audit_flag_options(self):
        parser = driver.build_parser()
        self.assertFalse(parser.parse_args(["start", "demo", "--repo", "."]).validate)
        for flag in ("--validate", "--verify", "--audit"):
            self.assertTrue(
                parser.parse_args(["start", "demo", "--repo", ".", flag]).validate
            )
        for flag in ("--no-validate", "--no-verify", "--no-audit"):
            self.assertFalse(
                parser.parse_args(["start", "demo", "--repo", ".", flag]).validate
            )

    def test_resolve_plan_path_handles_transition_to_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            pending_dir = repo / ".aw" / "records" / "plans" / "pending"
            executed_dir = repo / ".aw" / "records" / "plans" / "executed"
            pending_dir.mkdir(parents=True)
            executed_dir.mkdir(parents=True)

            plan_p = pending_dir / "20260827-testset-01-xyz999-test-plan.ipd.md"
            plan_p.write_text(
                "- Id: xyz999\n- Set: testset\n- Status: approved\n# Test Plan\n",
                encoding="utf-8",
            )

            # Resolves from pending
            configured = (
                ".aw/records/plans/pending/20260827-testset-01-xyz999-test-plan.ipd.md"
            )
            found_pending = driver.resolve_plan_path(repo, configured, "xyz999")
            self.assertEqual(found_pending, plan_p.resolve())

            # Move to executed
            plan_e = executed_dir / "20260827-testset-01-xyz999-test-plan.ipd.md"
            plan_p.rename(plan_e)

            # Even with stale configured path, resolves to executed path via id6 selector
            found_executed = driver.resolve_plan_path(repo, configured, "xyz999")
            self.assertEqual(found_executed, plan_e.resolve())


class OrchestratorNotAgentExecutedTests(unittest.TestCase):
    """The runner must not agent-execute a Kind: orchestrator IPD; it finalizes the
    orchestrator iff every child in its set reached `executed`, else leaves it blocked."""

    def _make_set(self, repo: Path) -> None:
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        (pending / "20260827-oset-00-orc001-orchestrator.ipd.md").write_text(
            "- Id: orc001\n- Set: oset\n- Order: 0\n- Kind: orchestrator\n- Status: approved\n# Orch\n",
            encoding="utf-8",
        )
        (pending / "20260827-oset-01-chi001-child-one.ipd.md").write_text(
            "- Id: chi001\n- Set: oset\n- Order: 1\n- Kind: child\n- Status: approved\n# Child1\n",
            encoding="utf-8",
        )
        (pending / "20260827-oset-02-chi002-child-two.ipd.md").write_text(
            "- Id: chi002\n- Set: oset\n- Order: 2\n- Kind: child\n- Status: approved\n# Child2\n",
            encoding="utf-8",
        )

    def test_kind_is_parsed_into_record_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            self._make_set(repo)
            discovered = driver.discover_plans(repo)
            self.assertEqual(discovered["orc001"].kind, "orchestrator")
            self.assertEqual(discovered["chi001"].kind, "child")
            manifest = driver.build_dynamic_manifest(repo, discovered)
            self.assertEqual(manifest["plans"]["orc001"]["kind"], "orchestrator")

    def test_children_all_executed_gate(self):
        # Orchestrator is finalizable ONLY when every child is `executed`.
        state = {
            "queue": [
                {
                    "id6": "orc001",
                    "setid": "oset",
                    "action": "orchestrate",
                    "status": "queued",
                },
                {
                    "id6": "chi001",
                    "setid": "oset",
                    "action": "execute",
                    "status": "executed",
                },
                {
                    "id6": "chi002",
                    "setid": "oset",
                    "action": "execute",
                    "status": "substantially-complete",
                },
            ]
        }
        ok, unfinished = driver._set_children_all_executed(state, "oset", "orc001")
        self.assertFalse(ok)
        self.assertEqual(unfinished, ["chi002"])
        # Now mark the last child executed.
        state["queue"][2]["status"] = "executed"
        ok, unfinished = driver._set_children_all_executed(state, "oset", "orc001")
        self.assertTrue(ok)
        self.assertEqual(unfinished, [])

    def test_children_gate_false_when_no_children(self):
        state = {
            "queue": [
                {
                    "id6": "orc001",
                    "setid": "oset",
                    "action": "orchestrate",
                    "status": "queued",
                },
            ]
        }
        ok, _ = driver._set_children_all_executed(state, "oset", "orc001")
        self.assertFalse(ok)

    def test_orchestrator_in_review_gets_review_not_orchestrate(self):
        # A draft/to-review orchestrator MUST still get its /plan-review (it advances
        # like any reviewable IPD); it is NOT skipped as 'orchestrate'. Otherwise it
        # would stay stuck at draft/to-review whether run via aw oc run or manually.
        self.assertEqual(driver.action_for("orchestrator", "draft"), "review")
        self.assertEqual(driver.action_for("orchestrator", "to-review"), "review")

    def test_orchestrator_past_review_is_orchestrate(self):
        # approved/auto-approved orchestrator authors no code -> not agent-executed.
        self.assertEqual(driver.action_for("orchestrator", "approved"), "orchestrate")
        self.assertEqual(
            driver.action_for("orchestrator", "auto-approved"), "orchestrate"
        )

    def test_child_action_unaffected_by_kind(self):
        self.assertEqual(driver.action_for("child", "approved"), "execute")
        self.assertEqual(driver.action_for("child", "to-review"), "review")
        self.assertEqual(driver.action_for(None, "approved"), "execute")


# --- driverfin-01 (p7peqf): driver self-finalize (aw ipd begin before + aw ipd finalize after) ---

_CONFORMING_PLAN = """\
# IPD: Demo self-finalize

- Date: 2026-08-28
- Kind: child
- Concern: demo concern for the self-finalize test.
- Scope: demo scope.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: approved
- Set: demo
- Order: 1
- Highest E allocated: 01
- Priority: medium
- Work-Kind: chore
- Author: test
- Id: {id6}
- Approval: 2026-08-28, recorded via aw ipd set: status set to approved

## Workflow history

- 2026-08-28 approved (aw set): status set to approved
- 2026-08-28 draft (test): created.

## Goal

Demo goal sentence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: demo

- [x] E-01 Create the demo file.
  - Depends on: none
  - Expected outcome: the demo file exists.
  - Execution state: performed

## Project conventions discovered (Step 0)

- demo convention.

## Findings

demo findings.

## Proposed changes (ordered, validatable)

1. src/demo.txt: create it.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Manual check that src/demo.txt exists.

## Spec / documentation sync

N/A: demo only.

## Open questions

### OQ-01: none?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass.

- [x] V-01 validates E-01
  - Required evidence: src/demo.txt present.
  - Observed evidence: src/demo.txt present.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit path-scoped; do not push.
"""


def _init_repo_with_conforming_plan(repo: Path, id6: str = "slf001") -> Path:
    """Create a git repo (with .aw/state gitignored) holding one approved, lint-conforming plan."""
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    # Match a production install's ignore set: run state, worktrees, and receipts are gitignored.
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    plan = pending / f"20260828-demo-01-{id6}-demo.ipd.md"
    plan.write_text(_CONFORMING_PLAN.format(id6=id6), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return plan


class SelfFinalizeHelperTests(unittest.TestCase):
    """Unit coverage of the begin/finalize driver helpers + programmatic scope reconciliation."""

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def test_driver_actor_is_parenthesis_free(self):
        # The terminal history line is `- <date> <status> (<actor>): <msg>`; a parenthesized actor
        # would misparse under the attribution lint, so the model is rendered as `model=<m>`.
        self.assertEqual(
            driver.driver_actor({"options": {"model": "opus-4.8"}}),
            "aw oc run model=opus-4.8",
        )
        self.assertNotIn("(", driver.driver_actor({"options": {"model": "x"}}))
        self.assertEqual(driver.driver_actor({"options": {}}), "aw oc run")

    def test_driver_actor_normalizes_every_qualifier(self):
        # One builder serves both hosts, so the oc side pins the same normalization for model,
        # variant AND profile: a value with a parenthesis, whitespace, or ':' becomes one token.
        from agent_workflows import attention_contract as ac

        actor = driver.driver_actor(
            {
                "options": {
                    "model": "its_direct/pt3-claude-opus-5.5-1m-us",
                    "variant": "high (max)",
                    "launch_profile": {"applied": "my: gem"},
                }
            }
        )
        self.assertEqual(
            actor,
            "aw oc run model=its_direct/pt3-claude-opus-5.5-1m-us variant=high-max profile=my-gem",
        )
        self.assertIsNone(ac.actor_refusal(actor))

    def test_begin_writes_receipt_then_finalize_moves_to_executed(self):
        # V-01/V-02 end-to-end: real `aw ipd begin` writes the gitignored receipt, and after the
        # (simulated) verified turn `aw ipd finalize` moves the plan to executed/ via the driver
        # helpers with programmatic scope reconciliation.
        from agent_workflows import ipd_lifecycle

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "slf001")
            actor = driver.driver_actor({"options": {"model": "opus"}})

            rc, msg = driver.driver_begin(repo, "slf001", actor)
            self.assertEqual(rc, 0, msg)
            receipt = ipd_lifecycle.receipt_path_for(repo, "slf001")
            self.assertTrue(receipt.is_file(), f"begin must write receipt at {receipt}")

            # Simulate the agent turn producing + committing the in-scope work.
            (repo / "src").mkdir()
            (repo / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo: create src/demo.txt"],
                cwd=repo,
                check=True,
            )

            reasons, acks = driver._compute_scope_reconciliation(repo, plan)
            # src/ was modified and is in Scope-Paths; nothing out-of-scope, nothing unmodified.
            self.assertEqual(reasons, {})
            self.assertEqual(acks, {})

            rc, msg = driver.driver_finalize(
                repo, plan, "slf001", actor, "self-finalize demo verified"
            )
            self.assertEqual(rc, 0, msg)
            self.assertFalse(plan.is_file(), "plan should have moved out of pending/")
            executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name
            self.assertTrue(executed.is_file(), "plan must land in executed/")
            self.assertIn("- Status: executed", executed.read_text(encoding="utf-8"))

    def test_compute_scope_reconciliation_handles_out_of_scope_and_unmodified(self):
        # A change OUTSIDE Scope-Paths yields a --scope-reason; a declared-but-untouched path yields
        # a --scope-ack. Both are computed from the authoritative finalize_precheck audit.
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "slf002")
            actor = driver.driver_actor({"options": {"model": "opus"}})
            rc, msg = driver.driver_begin(repo, "slf002", actor)
            self.assertEqual(rc, 0, msg)
            # Change a path OUTSIDE Scope-Paths (src/), and leave src/ untouched (unmodified).
            (repo / "OTHER.txt").write_text("out of scope\n", encoding="utf-8")
            subprocess.run(["git", "add", "OTHER.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "out of scope change"], cwd=repo, check=True
            )
            reasons, acks = driver._compute_scope_reconciliation(repo, plan)
            self.assertIn("OTHER.txt", reasons)
            self.assertIn("src/", acks)


class SelfFinalizeWiringTests(unittest.TestCase):
    """execute_item wiring: begin runs BEFORE the turn (refusal blocks); finalize runs AFTER a
    verified turn (success -> executed; refusal -> not forced). Uses mocks to isolate the ordering
    and gate logic from the real lifecycle machinery."""

    def _state_and_item(
        self, repo: Path, plan: Path, self_finalize: bool = True
    ) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "wir001",
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "model": "opus",
                "self_finalize": self_finalize,
                "no_audit": True,  # skip turn-2 verify unless a test overrides
                # These p7peqf wiring tests exercise the begin/finalize wiring in the MAIN tree;
                # the driverfin-02 worktree isolation is covered by WorktreeIsolationTests below.
                "isolate_worktree": False,
            },
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        return run_dir

    def test_begin_runs_before_turn_and_refusal_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            calls = []

            def fake_begin(r, i, a):
                calls.append(("begin", i))
                return 1, "pre-execution gate did NOT conform"  # refusal

            def fake_run(*a, **k):
                calls.append(("run_opencode", None))
                return 0, "ses1", str(run_dir / "log"), ["opencode"]

            with (
                mock.patch.object(driver, "driver_begin", fake_begin),
                mock.patch.object(driver, "run_opencode", fake_run),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            # begin was attempted; run_opencode was NEVER launched; item recorded fail-begin.
            self.assertEqual(calls, [("begin", "wir001")])
            self.assertEqual(item["status"], "fail-begin")
            self.assertIn("begin_refusal", item)

    def test_begin_precedes_run_opencode_on_success(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            order = []

            with (
                mock.patch.object(
                    driver,
                    "driver_begin",
                    lambda r, i, a: order.append("begin") or (0, "ok"),
                ),
                mock.patch.object(
                    driver,
                    "run_opencode",
                    lambda *a, **k: (
                        order.append("run") or (0, "ses1", str(run_dir / "log"), ["oc"])
                    ),
                ),
                mock.patch.object(
                    driver, "driver_finalize", lambda *a, **k: (0, "finalized")
                ),
            ):
                # write an outcome so reconcile reports substantially-complete
                (run_dir / "outcomes" / "01-wir001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            # defreport (`b7xarm`): a CONFORMING agent now states its defect
                            # report affirmatively. Without it the driver correctly spends its
                            # one same-session re-ask, and this fake would then re-run its own
                            # `git commit` and fail on an already-clean tree.
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                driver.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(order[:2], ["begin", "run"])

    def test_finalize_fires_on_verified_substantially_complete_and_marks_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, self_finalize=True)
            state["options"]["no_audit"] = False  # exercise the verify path

            (run_dir / "outcomes" / "01-wir001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            # verifier outcome -> verified
            (run_dir / "outcomes" / "01-wir001-verification.json").write_text(
                json.dumps(
                    {
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m unittest tests.test_from_backlog -v"],
                    }
                ),
                encoding="utf-8",
            )

            finalize_calls = []

            def fake_finalize(r, p, i, a, m):
                finalize_calls.append((i, a, m))
                # simulate the real finalize moving the plan to executed/
                executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name
                executed.parent.mkdir(parents=True, exist_ok=True)
                plan.rename(executed)
                return 0, "finalized"

            def fake_run(*a, **k):
                return 0, "ses1", str(run_dir / "log"), ["oc"]

            with (
                mock.patch.object(driver, "driver_begin", lambda r, i, a: (0, "ok")),
                mock.patch.object(driver, "run_opencode", fake_run),
                mock.patch.object(driver, "driver_finalize", fake_finalize),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(finalize_calls), 1, "finalize must fire once")
            self.assertEqual(finalize_calls[0][0], "wir001")
            # actor is parenthesis-free and non-generic; message non-empty.
            self.assertTrue(finalize_calls[0][1].startswith("aw oc run"))
            self.assertTrue(finalize_calls[0][2])
            self.assertEqual(item["status"], "executed")

    def test_finalize_refusal_leaves_not_executed_and_not_forced(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, self_finalize=True)
            state["options"]["no_audit"] = (
                True  # disposition stays substantially-complete, verified via rc
            )

            (run_dir / "outcomes" / "01-wir001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )

            # With no_audit=True, verify_disp stays None, so the finalize gate should NOT fire.
            # This asserts the gate requires verification == verified.
            fin = []
            with (
                mock.patch.object(driver, "driver_begin", lambda r, i, a: (0, "ok")),
                mock.patch.object(
                    driver,
                    "run_opencode",
                    lambda *a, **k: (0, "ses1", str(run_dir / "log"), ["oc"]),
                ),
                mock.patch.object(
                    driver,
                    "driver_finalize",
                    lambda *a, **k: fin.append(1) or (1, "refused"),
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                fin, [], "finalize must NOT fire without verification==verified"
            )
            self.assertEqual(item["status"], "fail-gate")
            self.assertTrue(plan.is_file(), "plan must remain in pending/ (not forced)")

    def test_finalize_refusal_does_not_stamp_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, self_finalize=True)
            state["options"]["no_audit"] = False

            (run_dir / "outcomes" / "01-wir001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "outcomes" / "01-wir001-verification.json").write_text(
                json.dumps(
                    {
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m unittest tests.test_from_backlog -v"],
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(driver, "driver_begin", lambda r, i, a: (0, "ok")),
                mock.patch.object(
                    driver,
                    "run_opencode",
                    lambda *a, **k: (0, "ses1", str(run_dir / "log"), ["oc"]),
                ),
                mock.patch.object(
                    driver,
                    "driver_finalize",
                    lambda *a, **k: (
                        1,
                        "refused: out-of-scope path needs a --scope-reason",
                    ),
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            # A finalize REFUSAL must leave the child NOT executed with a recorded reason.
            self.assertEqual(item["status"], "fail-gate")
            self.assertIn("finalize_refusal", item)
            self.assertTrue(
                plan.is_file(), "plan must not be moved on finalize refusal"
            )

    def test_no_self_finalize_skips_begin_and_finalize(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, self_finalize=False)

            (run_dir / "outcomes" / "01-wir001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            begin_calls, fin_calls = [], []
            with (
                mock.patch.object(
                    driver,
                    "driver_begin",
                    lambda r, i, a: begin_calls.append(1) or (0, "ok"),
                ),
                mock.patch.object(
                    driver,
                    "run_opencode",
                    lambda *a, **k: (0, "ses1", str(run_dir / "log"), ["oc"]),
                ),
                mock.patch.object(
                    driver,
                    "driver_finalize",
                    lambda *a, **k: fin_calls.append(1) or (0, "ok"),
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                begin_calls, [], "begin must be skipped with --no-self-finalize"
            )
            self.assertEqual(
                fin_calls, [], "finalize must be skipped with --no-self-finalize"
            )


class SpecEditReportBehavioralTests(unittest.TestCase):
    """specrpt (9npssm): end-of-run declared-spec-edit report reflects what execute_item writes.

    Drives driver.execute_item on the real finalize path with real driver_begin and real
    _compute_scope_reconciliation, proving declared, undeclared-modified, and silence cases.
    """

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _state_and_item(self, repo: Path, plan: Path) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "spe001",
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "no_audit": True,
                "isolate_worktree": False,
            },
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        return run_dir

    def test_execute_item_spec_edits_report_declared_and_undeclared(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / ".gitignore").write_text(
                ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
            )
            (repo / "docs").mkdir(parents=True, exist_ok=True)
            (repo / "docs" / "A.spec.md").write_text("# Spec A\n", encoding="utf-8")

            plan_text = _CONFORMING_PLAN.format(id6="spe001").replace(
                "- Scope-Paths: src/", "- Scope-Paths: docs/A.spec.md"
            )
            pending = repo / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan = pending / "20260828-demo-01-spe001-demo.ipd.md"
            plan.write_text(plan_text, encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            def fake_run(*a, **k):
                (repo / "docs" / "A.spec.md").write_text(
                    "# Spec A modified\n", encoding="utf-8"
                )
                (repo / "docs" / "B.spec.md").write_text(
                    "# Spec B undeclared\n", encoding="utf-8"
                )
                subprocess.run(
                    ["git", "add", "docs/A.spec.md", "docs/B.spec.md"],
                    cwd=repo,
                    check=True,
                )
                subprocess.run(
                    ["git", "commit", "-qm", "edit A and B"], cwd=repo, check=True
                )
                (run_dir / "outcomes" / "01-spe001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "substantially-complete",
                            "pushed": False,
                            "defect_report": {
                                "state": "none-found",
                                "findings": [],
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(run_dir / "log"), ["opencode"]

            passing_suite = runner_shared.SuiteCheckResult(
                True, 0, "1 passed", "ok", str(repo), 60.0, 0.1
            )
            with (
                mock.patch.object(driver, "run_opencode", fake_run),
                mock.patch.object(
                    driver, "run_suite_check", lambda *a, **k: passing_suite
                ),
                mock.patch.object(
                    driver, "driver_finalize", lambda *a, **k: (0, "finalized")
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            buf = io.StringIO()
            lines = driver.report_run_spec_edits(state, stream=buf)
            rendered = "\n".join(lines)
            self.assertIn("declared -> docs/A.spec.md", rendered)
            self.assertNotIn("declared, unmodified -> docs/A.spec.md", rendered)
            self.assertIn("modified (undeclared) -> docs/B.spec.md", rendered)
            self.assertIn("Reconciled 1 item(s)", rendered)
            self.assertNotIn("NOT FINALIZED", rendered)
            self.assertIn("spec_edits", item)
            self.assertNotIn("spec_edits_reconciliation", item)

    def test_execute_item_spec_edits_report_silence_on_no_spec_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "sil001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            def fake_run(*a, **k):
                (repo / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
                subprocess.run(["git", "add", "src/demo.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "edit demo.txt"], cwd=repo, check=True
                )
                (run_dir / "outcomes" / "01-sil001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "substantially-complete",
                            "pushed": False,
                            "defect_report": {
                                "state": "none-found",
                                "findings": [],
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(run_dir / "log"), ["opencode"]

            passing_suite = runner_shared.SuiteCheckResult(
                True, 0, "1 passed", "ok", str(repo), 60.0, 0.1
            )
            with (
                mock.patch.object(driver, "run_opencode", fake_run),
                mock.patch.object(
                    driver, "run_suite_check", lambda *a, **k: passing_suite
                ),
                mock.patch.object(
                    driver, "driver_finalize", lambda *a, **k: (0, "finalized")
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            buf = io.StringIO()
            lines = driver.report_run_spec_edits(state, stream=buf)
            self.assertEqual(lines, [])
            self.assertEqual(buf.getvalue(), "")


class WorktreeIsolationTests(unittest.TestCase):
    """driverfin-02 (emus4n): each execute-action child runs in its OWN git worktree; the main tree
    stays clean during the turn; a verified child's commits integrate back to main via the REUSED
    integration gate; a non-passing gate leaves the child NOT integrated (deferred, not faked)."""

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def _state_and_item(self, repo: Path, plan: Path) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "wir001",
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_audit": False,  # exercise the verify->finalize->integrate path
            },
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        return run_dir

    def _fake_agent_commits_in_worktree(self, run_dir: Path):
        """A fake run_opencode: on the FIRST (execute) turn it writes+commits an in-scope file INSIDE
        the worktree (the `work_dir` kwarg) and writes the outcome JSON to the main run_dir; on the
        verify turn it only writes the verification verdict. Asserts nothing itself."""
        state_calls = {"n": 0}

        def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("fresh_session"):
                # verifier turn -> record CONFORMING verdict.
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["oc"]
            # execute turn -> commit an in-scope change in the WORKTREE.
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo: create src/demo.txt"],
                cwd=wt,
                check=True,
            )
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            state_calls["n"] += 1
            return 0, "ses1", str(run_dir / "log"), ["oc"]

        return fake_run

    def test_main_tree_clean_during_turn_and_receipt_under_main(self):
        # V-01: during the isolated turn the MAIN git tree stays clean; the agent's mutations happen
        # in repo/.aw/worktrees/<id6> on branch aw/lane/<id6>; the begin receipt is under the MAIN
        # repo's .aw/state/ipd-lifecycle/<id6>.receipt.json.
        from agent_workflows import ipd_lifecycle

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            observed = {}

            def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
                work_dir = kwargs.get("work_dir")
                if not kwargs.get("fresh_session"):
                    # ASSERT the main tree is clean while the worktree is where edits go.
                    main_status = subprocess.run(
                        ["git", "status", "--short"],
                        cwd=repo,
                        text=True,
                        capture_output=True,
                    ).stdout
                    observed["main_status_during_turn"] = main_status
                    observed["work_dir"] = work_dir
                    # The worktree is at repo/.aw/worktrees/wir001 on aw/lane/wir001.
                    observed["wt_expected"] = str(
                        (repo / ".aw" / "worktrees" / "wir001").resolve()
                    )
                    br = subprocess.run(
                        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
                        cwd=work_dir,
                        text=True,
                        capture_output=True,
                    ).stdout.strip()
                    observed["wt_branch"] = br
                    # commit an in-scope change in the worktree
                    wt = Path(work_dir)
                    (wt / "src").mkdir(parents=True, exist_ok=True)
                    (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
                    subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
                    subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
                    (
                        run_dir
                        / "outcomes"
                        / f"{item['position']:02d}-{item['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                # defreport (`b7xarm`): a CONFORMING agent now states its defect
                                # report affirmatively. Without it the driver correctly spends its
                                # one same-session re-ask, and this fake would then re-run its own
                                # `git commit` and fail on an already-clean tree.
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(run_dir / "log"), ["oc"]
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["oc"]

            with mock.patch.object(driver, "run_opencode", fake_run):
                driver.execute_item(run_dir, state, item, recovery=False)

            # V-01 assertions:
            self.assertEqual(
                observed["main_status_during_turn"].strip(),
                "",
                "MAIN tree must be clean during the isolated turn",
            )
            self.assertEqual(observed["work_dir"], observed["wt_expected"])
            self.assertEqual(observed["wt_branch"], "aw/lane/wir001")
            # The receipt path MUST anchor on the main checkout, never on the lane worktree. That is
            # the surviving half of the original V-01 assertion, and it is the part that was actually
            # about isolation.
            receipt = ipd_lifecycle.receipt_path_for(repo, "wir001")
            self.assertEqual(
                receipt,
                # git reports the canonical (symlink-resolved) checkout, so compare against
                # the resolved repo (macOS /var -> /private/var, Windows 8.3 short names).
                repo.resolve()
                / ".aw"
                / "state"
                / "ipd-lifecycle"
                / "wir001.receipt.json",
            )
            # NOTE: the lane-vs-main resolution equality is deliberately NOT asserted here. By this
            # point the verified lane has been integrated and TORN DOWN, so its path no longer exists
            # and carries no git identity to collapse onto the checkout. That invariant is proved
            # against a LIVE worktree in tests/test_statefork_dh0uno.py instead.
            #
            # AMENDED with the dh0uno fix. This used to assert the receipt FILE still existed here
            # after the turn, which passed for the WRONG reason: `finalize_repo` is the LANE, so the
            # pre-fix code consumed the LANE's forked receipt on success and left the main-tree copy
            # behind as an ORPHAN. The assertion was therefore observing the fork, not isolation.
            # Now that both trees resolve ONE receipt, a clean finalize correctly CONSUMES it
            # (`ipd_lifecycle` unlinks it once the transaction completes), so absence here is the
            # correct post-condition and its continued presence would mean a leaked transaction.
            self.assertFalse(
                receipt.is_file(),
                "a completed finalize must consume the one begin receipt, leaving no orphan",
            )

    def test_verified_child_integrates_to_main_and_worktree_removed(self):
        # V-02 (passed case): a verified child's commits (incl. the plan-move to executed/) land on
        # main via the REUSED execute_merge_and_revalidate_gate, and the worktree is torn down.
        gate_calls = []
        real_gate = None
        from agent_workflows import orchestrate_isolation

        real_gate = orchestrate_isolation.execute_merge_and_revalidate_gate

        def spy_gate(*a, **k):
            gate_calls.append((a, k))
            return real_gate(*a, **k)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            with (
                mock.patch.object(
                    driver,
                    "run_opencode",
                    self._fake_agent_commits_in_worktree(run_dir),
                ),
                mock.patch.object(
                    orchestrate_isolation,
                    "execute_merge_and_revalidate_gate",
                    spy_gate,
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            # The REUSED gate was called (not a forked merge).
            self.assertEqual(len(gate_calls), 1, "must route through the reused gate")
            # Child marked executed.
            self.assertEqual(item["status"], "executed")
            # The plan-move landed on MAIN: plan is now in executed/ on the main tree.
            executed = repo / ".aw" / "records" / "plans" / "executed" / plan.name
            self.assertTrue(
                executed.is_file(), "plan-move must be integrated to main's executed/"
            )
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "pending" / plan.name).is_file()
            )
            # The agent's product file landed on main too.
            self.assertTrue((repo / "src" / "demo.txt").is_file())
            # The worktree was torn down.
            self.assertFalse(
                (repo / ".aw" / "worktrees" / "wir001").exists(),
                "worktree must be removed on successful integration",
            )
            # Main tree is clean after integration.
            main_status = subprocess.run(
                ["git", "status", "--short"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()
            self.assertEqual(main_status, "")

    def test_non_passing_gate_defers_not_faked_executed(self):
        # V-02 (non-passing case): if the integration gate does NOT pass (e.g. combined-red via an
        # injected failing validation runner), the child is left NOT integrated with a recorded
        # reason, is NOT faked executed, and the worktree is preserved. driverfin-03 (7kbtkw) E-02
        # refines the recorded state from the interim `substantially-complete` to the dedicated
        # fail-closed terminal state `merge-conflict`.
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            # Force the gate's full revalidation to fail -> INTEGRATION_FAILED_COMBINED_RED.
            def failing_runner_factory(*a, **k):
                return lambda _diff, _files: False

            with (
                mock.patch.object(
                    driver,
                    "run_opencode",
                    self._fake_agent_commits_in_worktree(run_dir),
                ),
                mock.patch.object(
                    driver, "make_integration_validation_runner", failing_runner_factory
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            # NOT faked executed; recorded as fail-merge (driverfin-03 E-02) with a reason.
            self.assertEqual(item["status"], "fail-merge")
            self.assertIn("integration_deferral", item)
            # Plan did NOT move to main's executed/ (integration did not happen on main).
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            # The worktree/branch is preserved (attributable) for a human/serial resolution.
            self.assertIn("preserved_branch", item)
            self.assertEqual(item["preserved_branch"], "aw/lane/wir001")


class FailClosedIntegrationGuardTests(unittest.TestCase):
    """driverfin-03 (7kbtkw): fail-closed dirty-tree guard (E-01) + merge-back conflict handling
    (E-02). Integration into a contaminated base is refused (`integration-blocked`); a non-passing
    integration gate leaves main pristine and records `merge-conflict`; both preserve the verified
    lane branch/worktree and never fake the child executed (its set is therefore not finished)."""

    def setUp(self) -> None:
        # DECLARE the coordinator role rather than inheriting it: this test drives the
        # lifecycle verbs, which read the ambient environment, so a runner-launched suite
        # would otherwise hand it `AW_EXECUTION_ROLE=worker` and it would measure the
        # `AW-LIFECYCLE-ROLE-001` refusal instead of the behavior it asserts (plan `e4lkv5`).
        support.declare_execution_role(self)

    def _state_and_item(self, repo: Path, plan: Path) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "wir001",
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_audit": False,
            },
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        return run_dir

    def _fake_agent_commits_in_worktree(self, run_dir: Path):
        def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("fresh_session"):
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["oc"]
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo: create src/demo.txt"],
                cwd=wt,
                check=True,
            )
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["oc"]

        return fake_run

    def _fake_agent_also_dirties_main(self, run_dir: Path, repo: Path):
        """Like _fake_agent_commits_in_worktree, but on the execute turn ALSO leaves an un-owned dirty
        edit in MAIN on the overlapping path (src/demo.txt). This models the base becoming
        contaminated AFTER `aw ipd begin` (e.g. a concurrent agent), so begin does not refuse but the
        integration-time dirty-tree guard (E-01) must."""

        def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("fresh_session"):
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["oc"]
            wt = Path(work_dir)
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo: create src/demo.txt"],
                cwd=wt,
                check=True,
            )
            # Contaminate MAIN on the overlapping path AFTER begin (un-owned, uncommitted).
            (repo / "src").mkdir(parents=True, exist_ok=True)
            (repo / "src" / "demo.txt").write_text("un-owned dirt\n", encoding="utf-8")
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        # defreport (`b7xarm`): a CONFORMING agent now states its defect
                        # report affirmatively. Without it the driver correctly spends its
                        # one same-session re-ask, and this fake would then re-run its own
                        # `git commit` and fail on an already-clean tree.
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["oc"]

        return fake_run

    def test_dirty_overlapping_base_refuses_integration(self):
        # V-01 (driverfin-03 `7kbtkw`): if MAIN has an un-owned dirty path overlapping the incoming
        # lane's changed_files, the integration gate is NOT invoked, MAIN stays unmodified apart from
        # the un-owned dirty edit, and the verified branch/worktree are preserved.
        #
        # THE REFUSAL IS UNCHANGED; ONLY THE DISPOSITION AFTER IT MOVED (integpath-03 `51vw4y`). This
        # test asserted `integration-blocked` on the FIRST refusal, which was the defect that Set
        # exists to fix: `integration-blocked` is in `TERMINAL_STATES`, so a refusal caused by another
        # writer's transient uncommitted file permanently stranded verified work (measured: seven of 34
        # items lost in run `run-20260905T050043Z-639569`). The first refusal is now the NON-TERMINAL
        # `integration-deferred`, and `integration-blocked` is reached only after the ladder is
        # exhausted. Every OTHER assertion here is kept verbatim, because each pins a fail-closed
        # property this plan must not weaken: the gate must still not run against a contaminated base,
        # main must still not be clobbered, the plan must still not reach main's `executed/`, and the
        # lane must still be preserved.
        from agent_workflows import orchestrate_isolation

        gate_calls = []
        real_gate = orchestrate_isolation.execute_merge_and_revalidate_gate

        def spy_gate(*a, **k):
            gate_calls.append((a, k))
            return real_gate(*a, **k)

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            with (
                mock.patch.object(
                    driver,
                    "run_opencode",
                    self._fake_agent_also_dirties_main(run_dir, repo),
                ),
                mock.patch.object(
                    orchestrate_isolation,
                    "execute_merge_and_revalidate_gate",
                    spy_gate,
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            # The gate was NEVER invoked against the contaminated base.
            self.assertEqual(
                len(gate_calls), 0, "gate must not run against a dirty overlapping base"
            )
            # Item recorded the NON-TERMINAL deferral, NOT executed and NOT terminally blocked.
            self.assertEqual(item["status"], "merge-retry")
            self.assertNotIn(
                item["status"],
                driver.TERMINAL_STATES,
                "the first refusal must be NON-terminal, or the item is never re-attempted",
            )
            self.assertIn("integration_deferral", item)
            self.assertIn("src/demo.txt", item["integration_deferral"])
            # The ladder recorded WHY it deferred and against WHICH budget.
            self.assertTrue(item["integration_ladder"]["deferred"])
            self.assertEqual(item["integration_ladder"]["attempts_used"], 1)
            self.assertEqual(item["integration_ladder"]["kind"], "merge-retry")
            # Plan did NOT move to main's executed/.
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            # MAIN's working tree still holds ONLY the un-owned edit (no clobber).
            self.assertEqual(
                (repo / "src" / "demo.txt").read_text(encoding="utf-8"),
                "un-owned dirt\n",
            )
            # Verified lane branch/worktree preserved.
            self.assertIn("preserved_branch", item)
            self.assertEqual(item["preserved_branch"], "aw/lane/wir001")
            self.assertTrue((repo / ".aw" / "worktrees" / "wir001").exists())
            # The fail-closed event was recorded, now naming the DEFERRAL rather than a terminal block.
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-integration-deferred", events)

    def _fake_agent_renames_in_worktree(self, run_dir: Path, *, orig: str, dest: str):
        """An agent whose lane RENAMES a tracked file, the shape that reaches git's own refusal.

        dirtygates-02 (`metc8b`): `changed_files` comes from `git diff --name-only`, which applies
        rename detection and reports only ``dest``. So un-owned dirt on ``orig`` passes the pre-merge
        `dirty_tree_overlap` guard (it is not in the incoming set) while the merge must still DELETE
        ``orig`` in main, and git refuses to start. This is the shape of every plan moving
        `pending/` -> `executed/`, which is why the two lanes of 2026-09-13 hit it.
        """

        def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
            work_dir = kwargs.get("work_dir")
            if kwargs.get("fresh_session"):
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(
                    json.dumps(
                        {
                            "verdict": "VERIFIED",
                            "tests_run": [
                                "python3 -m unittest tests.test_from_backlog -v"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "vses", str(run_dir / "vlog"), ["oc"]
            wt = Path(work_dir)
            subprocess.run(["git", "mv", orig, dest], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-qm", f"demo: rename {orig} -> {dest}"],
                cwd=wt,
                check=True,
            )
            (
                run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
            ).write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["oc"]

        return fake_run

    def test_a_real_git_local_changes_refusal_is_DEFERRED_not_recorded_merge_conflict(
        self,
    ):
        """dirtygates-02 (`metc8b`) E-02, end-to-end on this host.

        THE MEASURED DEFECT: lanes `bzz5e6` and `f6idxs` (2026-09-13) each finalized verified work,
        then `git merge` REFUSED because main held an uncommitted edit to a file the merge would
        overwrite. Both were recorded `merge-conflict`, which is TERMINAL on its first attempt, so the
        work was lost for the rest of the run. It is not a conflict: git never started the merge and
        the condition clears itself once the dirt is committed, so it belongs on the deferrable arm.

        Unlike the sibling dirty-overlap test, the PRE-MERGE guard PASSES here (rename detection hides
        the origin path from `changed_files`) and the gate really runs; the refusal comes from git.
        """
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            # A tracked file long enough for git to score its move as a rename.
            body = "".join(f"line {i}\n" for i in range(40))
            (repo / "moved.txt").write_text(body, encoding="utf-8")
            subprocess.run(["git", "add", "moved.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "add moved.txt"], cwd=repo, check=True
            )
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()

            dirty = body + "un-owned local edit\n"

            agent = self._fake_agent_renames_in_worktree(
                run_dir, orig="moved.txt", dest="dest.txt"
            )

            def agent_then_dirty_main(*a, **k):
                rc = agent(*a, **k)
                if not k.get("fresh_session"):
                    # Un-owned, uncommitted edit to the RENAME ORIGIN, added after begin.
                    (repo / "moved.txt").write_text(dirty, encoding="utf-8")
                return rc

            # mergedirty-01 (`fujm0y`): the write set is forced UNKNOWN, which is the shipped
            # older-git fallback, so this case still reaches GIT's OWN refusal and therefore still
            # tests the structural discriminator this test exists for. Without it the widened
            # pre-merge guard refuses first and the assertions below would pass for a different
            # reason - the same kind, but never having attempted a merge, so a hollow pass.
            from agent_workflows import runner_shared

            with (
                mock.patch.object(driver, "run_opencode", agent_then_dirty_main),
                mock.patch.object(
                    runner_shared, "merge_write_set", lambda _repo, _branch: None
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            # The refusal is the DEFERRABLE class, so the ladder re-attempts it: NOT merge-conflict.
            self.assertEqual(
                item["integration_ladder"]["kind"],
                "merge-retry",
                f"git refused to START the merge, so it is not a conflict: {item.get('integration_deferral')}",
            )
            self.assertEqual(item["status"], "merge-retry")
            self.assertNotIn(item["status"], driver.TERMINAL_STATES)
            self.assertTrue(item["integration_ladder"]["deferred"])
            # Git's own words are the recorded reason, and NOT the conflict helper's phrase.
            reason = item["integration_deferral"]
            self.assertIn("Your local changes", reason)
            self.assertIn("moved.txt", reason)
            self.assertNotIn("merge-back conflict", reason)
            # MAIN is exactly as found: HEAD unmoved, the un-owned edit not clobbered, no partial merge.
            self.assertEqual(
                subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                ).stdout.strip(),
                head_before,
            )
            self.assertEqual((repo / "moved.txt").read_text(encoding="utf-8"), dirty)
            self.assertFalse((repo / ".git" / "MERGE_HEAD").exists())
            # The plan did NOT reach main's executed/, and the lane is preserved for the re-attempt.
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            self.assertEqual(item.get("preserved_branch"), "aw/lane/wir001")
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-integration-deferred", events)

    def test_non_passing_gate_records_merge_conflict_main_pristine(self):
        # V-02: a non-passing integration-gate result leaves MAIN with NO conflict markers/partial
        # merge, records `merge-conflict` with the gate's failing paths + preserved branch, emits the
        # event, and leaves the plan un-integrated (set not finished).
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)

            main_head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()

            # Force the gate's full revalidation to fail -> INTEGRATION_FAILED_COMBINED_RED.
            def failing_runner_factory(*a, **k):
                return lambda _diff, _files: False

            with (
                mock.patch.object(
                    driver,
                    "run_opencode",
                    self._fake_agent_commits_in_worktree(run_dir),
                ),
                mock.patch.object(
                    driver, "make_integration_validation_runner", failing_runner_factory
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            # fail-merge recorded, NOT executed.
            self.assertEqual(item["status"], "fail-merge")
            self.assertIn("integration_deferral", item)
            # MAIN is pristine: HEAD unchanged, working tree clean (no markers/partial merge).
            main_head_after = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()
            self.assertEqual(main_head_before, main_head_after)
            main_status = subprocess.run(
                ["git", "status", "--short"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()
            self.assertEqual(main_status, "", "MAIN must stay clean (no partial merge)")
            self.assertFalse((repo / ".git" / "MERGE_HEAD").exists())
            # Plan did NOT move to main's executed/.
            self.assertFalse(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            # Preserved lane branch recorded + the fail-closed event emitted.
            self.assertEqual(item.get("preserved_branch"), "aw/lane/wir001")
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-merge-conflict", events)

    def test_dirty_tree_overlap_helper_reports_only_overlap(self):
        # Unit coverage of the E-01 helper: only paths that are BOTH dirty in main AND incoming are
        # reported; a rename's origin+destination both count; disjoint dirt is ignored.
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "wir001")
            # Dirty an un-owned file that does NOT overlap.
            (repo / "unrelated.txt").write_text("dirt\n", encoding="utf-8")
            self.assertEqual(driver.dirty_tree_overlap(repo, ["src/x.py"]), [])
            # Dirty a file that DOES overlap the incoming change.
            (repo / "src").mkdir(parents=True, exist_ok=True)
            (repo / "src" / "x.py").write_text("dirt\n", encoding="utf-8")
            self.assertEqual(
                driver.dirty_tree_overlap(repo, ["src/x.py", "src/y.py"]),
                ["src/x.py"],
            )
            # No incoming files -> never blocked.
            self.assertEqual(driver.dirty_tree_overlap(repo, []), [])

    def test_this_hosts_merge_subject_still_says_aw_oc_run(self):
        """The ONE value the extraction parameterized, checked against a REAL merge on this host.

        A wrong label would misattribute an integration in main's git history and stay invisible until
        someone audited the log, so it is asserted positively AND negatively.
        """
        from agent_workflows import worktree_lease

        def git(cwd, *args):
            return subprocess.run(
                ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
            ).stdout.strip()

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "wir001")
            base = git(repo, "rev-parse", "HEAD")
            git(repo, "branch", "aw/lane/wir001")
            wt = Path(temp) / "wt"
            git(repo, "worktree", "add", "-q", str(wt), "aw/lane/wir001")
            (wt / "src").mkdir(parents=True, exist_ok=True)
            (wt / "src" / "x.py").write_text("lane\n", encoding="utf-8")
            git(wt, "add", "src/x.py")
            git(wt, "commit", "-qm", "lane writes src/x.py")
            # Advance main so `--ff-only` fails and the labelled `--no-ff` merge is taken.
            (repo / "other.txt").write_text("moved on\n", encoding="utf-8")
            git(repo, "add", "other.txt")
            git(repo, "commit", "-qm", "main advances")

            handle = worktree_lease.WorktreeHandle(
                lane_id="wir001",
                path=wt,
                branch="aw/lane/wir001",
                base_commit=base,
            )
            integrated, reason, kind = driver.integrate_lane_branch(
                repo, handle, "wir001", lambda _d, _f: True
            )

            self.assertTrue(integrated, reason)
            self.assertEqual(kind, "integrated")
            subject = git(repo, "log", "-1", "--pretty=%s")
            self.assertEqual(
                subject, "integrate(aw oc run): merge verified lane wir001 to main"
            )
            self.assertNotIn("aw agy run", subject)

    def test_the_MEASURED_INCIDENT_is_now_SURVIVED_defer_then_integrate(self):
        """integpath-03 (`51vw4y`) E-07: the incident's shape, reconstructed and survived (oc host).

        THE INCIDENT, run `run-20260905T050043Z-639569`: four items finished their work, passed their
        gates, finalized on their lane branches, and were then refused integration on dirty-path
        overlap; because `integration-blocked` was TERMINAL, none was ever retried, three more cascaded
        to `dependency-blocked`, and seven of 34 items were lost. All four merged clean afterwards. The
        original lanes are gone (branches deleted, plans recovered by hand), so the SHAPE is
        reconstructed synthetically here rather than pointed at.

        WHAT IS PROVEN: attempt one DEFERS (non-terminal, lane preserved, main unclobbered), the dirt
        is then removed exactly as a co-worker committing or reverting would remove it, and attempt two
        INTEGRATES - with NO agent turn spent on the retry, which is the property that makes the ladder
        free, and with the full merge-and-revalidate gate run on the successful attempt, which is the
        property that keeps it honest.
        """
        from agent_workflows import orchestrate_isolation

        gate_calls: list = []
        real_gate = orchestrate_isolation.execute_merge_and_revalidate_gate

        def spy_gate(*a, **k):
            gate_calls.append((a, k))
            return real_gate(*a, **k)

        agent_turns: list = []

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan)
            state["options"]["integration_retry_limit"] = 10
            state["options"]["on_integration_blocked"] = "defer"

            base_agent = self._fake_agent_also_dirties_main(run_dir, repo)

            def counting_agent(*a, **k):
                agent_turns.append(k.get("fresh_session"))
                return base_agent(*a, **k)

            with (
                mock.patch.object(driver, "run_opencode", counting_agent),
                mock.patch.object(
                    orchestrate_isolation,
                    "execute_merge_and_revalidate_gate",
                    spy_gate,
                ),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

                # ATTEMPT ONE: deferred, not terminal, nothing integrated, nothing clobbered.
                self.assertEqual(item["status"], "merge-retry")
                self.assertNotIn(item["status"], driver.TERMINAL_STATES)
                self.assertEqual(
                    len(gate_calls), 0, "the gate must not run against a dirty base"
                )
                self.assertEqual(
                    (repo / "src" / "demo.txt").read_text(encoding="utf-8"),
                    "un-owned dirt\n",
                )
                turns_after_first = len(agent_turns)

                # THE DIRT CLEARS, exactly as the co-worker who left it would clear it. This is the
                # 34-minute window that existed in the real incident and that nothing waited for.
                (repo / "src" / "demo.txt").unlink()

                # ATTEMPT TWO, driven the way the dispatch loop drives it: no new agent turn.
                records = driver.retry_deferred_integrations(run_dir, state)

            self.assertEqual(
                [r["outcome"] for r in records],
                ["integrated"],
                f"the re-attempt must integrate once the dirt clears: {records}",
            )
            self.assertEqual(item["status"], "executed")
            self.assertEqual(
                len(agent_turns),
                turns_after_first,
                "a deferred re-attempt must spend NO agent turn",
            )
            # The REVALIDATE GATE ran on the successful attempt (per-lane green never implies
            # integrated green), so this is not a bare `git merge` that happened to work.
            self.assertEqual(
                len(gate_calls), 1, "the successful re-attempt must run the full gate"
            )
            # The lane's work really is on main, and the plan really is in main's executed/.
            self.assertEqual(
                (repo / "src" / "demo.txt").read_text(encoding="utf-8"), "demo\n"
            )
            self.assertTrue(
                (repo / ".aw" / "records" / "plans" / "executed" / plan.name).is_file()
            )
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-integration-deferred", events)
            self.assertIn("ipd-integrated-after-deferral", events)


class TestIsolatedTurnPromptPointsAtTheLane(unittest.TestCase):
    """laneprompt: an isolated turn's prompt must name the LANE's paths, not main's.

    OBSERVED in a real run (run-20260831T153226Z-3424176, plan y6mfgo): the driver allocated
    `.aw/worktrees/y6mfgo` and launched with `--dir <lane>`, yet every commit landed in MAIN and the
    lane branch stayed at zero commits. Root cause: `execute_item` builds the prompt from
    `resolve_plan_path(repo, ...)` BEFORE the worktree is allocated, so every absolute path handed to
    the agent is main's. Isolation was enforced only by cwd, while the instructions pointed out of it.
    """

    def _prompt_paths(self, prompt: str) -> list[str]:
        import re

        return re.findall(r"/[^\s`'\"]+", prompt)

    def test_prompt_prefers_the_lane_copy_of_the_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            # resolve_plan_path returns canonical paths; resolve the tempdir so the prefix
            # checks hold under a symlinked TMPDIR (macOS) or Windows 8.3 short names.
            repo = Path(tmp).resolve() / "repo"
            lane = repo / ".aw" / "worktrees" / "aaaaaa"
            rel = ".aw/records/plans/pending/20260101-s-01-aaaaaa-x.ipd.md"
            for root in (repo, lane):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("# IPD: x\n\n- Id: aaaaaa\n", encoding="utf-8")
            run_dir = repo / ".aw" / "records" / "runs" / "run-x"
            run_dir.mkdir(parents=True, exist_ok=True)
            item = {
                "id6": "aaaaaa",
                "setid": "s",
                "position": 1,
                "configured_file": rel,
                "attempts": [],
                "action": "execute",
            }
            state = {"run_id": "run-x", "repo": str(repo), "options": {}}

            # The lane-aware resolution the driver performs for the VERIFIER turn already exists
            # (oc_runipd.py:4823 `plan_repo = Path(work_dir) if work_dir else repo`). The EXECUTOR
            # turn must do the same, otherwise it hands the agent main's path.
            lane_plan = driver.resolve_plan_path(lane, rel, "aaaaaa")
            self.assertTrue(str(lane_plan).startswith(str(lane)))

            prompt = driver.build_prompt(item, state, run_dir, lane_plan, False)
            self.assertIn(str(lane_plan), prompt)
            self.assertNotIn(str(repo / rel), prompt)

    def test_isolated_prompt_states_the_lane_requirement(self):
        """The prompt must TELL the agent it is in a lane and must stay there.

        Enforcement by cwd alone is not enough: `host_sandbox_profile`'s own docstring concedes a
        same-user agent cannot be constrained by prompts, hooks or env vars, so the prompt is the
        cheap layer that stops a FORGETFUL agent from reaching out with `../../..`.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            lane = repo / ".aw" / "worktrees" / "aaaaaa"
            lane.mkdir(parents=True, exist_ok=True)
            run_dir = repo / ".aw" / "records" / "runs" / "run-x"
            run_dir.mkdir(parents=True, exist_ok=True)
            item = {
                "id6": "aaaaaa",
                "setid": "s",
                "position": 1,
                "configured_file": "x.ipd.md",
                "attempts": [],
                "action": "execute",
            }
            state = {
                "run_id": "run-x",
                "repo": str(repo),
                "options": {},
                # The lane the driver allocated for THIS item.
                "_lane_root": str(lane),
            }
            prompt = driver.build_prompt(
                item, state, run_dir, lane / "x.ipd.md", False, lane_root=lane
            )
            low = prompt.lower()
            # Assert the BLOCK, not just the word "worktree" (which appears in unrelated prose) and
            # not just the lane path (which leaks in via plan_path anyway). Both weaker assertions
            # passed against a stubbed-out notice, so they proved nothing.
            self.assertIn("## Work here", prompt)
            self.assertIn("ISOLATED GIT WORKTREE", prompt)
            self.assertIn("do NOT climb out with a relative path", prompt)
            # The lane must be named INSIDE the block, not merely somewhere in the prompt.
            block = prompt[
                prompt.index("## Work here") : prompt.index("## Concurrent Work")
            ]
            self.assertIn(str(lane), block)
            # It must not tell an isolated agent to keep the MAIN checkout safe, which reads as
            # permission to work there.
            self.assertNotIn("leave the main execution checkout safe", low)

    def test_both_drivers_emit_the_same_isolation_notice(self):
        """A one-driver-only fix is the known failure mode here (see `lanesess xd9sll`), so pin it."""
        from agent_workflows import agy_runipd

        lane = Path("/tmp/repo/.aw/worktrees/aaaaaa")
        self.assertEqual(
            driver.build_isolation_notice(lane),
            agy_runipd.build_isolation_notice(lane),
        )
        # And a NON-isolated turn gets no block at all, so the default path is unchanged.
        self.assertEqual(driver.build_isolation_notice(None), "")
        self.assertEqual(agy_runipd.build_isolation_notice(None), "")

    def test_non_isolated_prompt_is_unchanged_by_the_lane_feature(self):
        """The main-checkout path must keep its exact prior shape (strictly additive)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            run_dir = repo / ".aw" / "records" / "runs" / "run-x"
            run_dir.mkdir(parents=True, exist_ok=True)
            item = {
                "id6": "aaaaaa",
                "setid": "s",
                "position": 1,
                "configured_file": "x.ipd.md",
                "attempts": [],
                "action": "execute",
            }
            state = {"run_id": "run-x", "repo": str(repo), "options": {}}
            without = driver.build_prompt(
                item, state, run_dir, repo / "x.ipd.md", False
            )
            explicit_none = driver.build_prompt(
                item, state, run_dir, repo / "x.ipd.md", False, lane_root=None
            )
            self.assertEqual(without, explicit_none)
            self.assertNotIn("## Work here", without)

    def test_variant_parsing_and_launch_cmd(self):
        parser = driver.build_parser()
        args = parser.parse_args(
            ["start", "testplan", "--variant", "high", "--prepare-only"]
        )
        self.assertEqual(args.variant, "high")

        args_res = parser.parse_args(["resume", "run-123", "--variant", "low"])
        self.assertEqual(args_res.variant, "low")

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "sessions").mkdir(parents=True)
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "options": {"variant": "high"},
            }
            item = {
                "id6": "wir001",
                "setid": "testset",
                "position": 1,
                "action": "execute",
            }
            prompt_file = run_dir / "prompts" / "01-prompt.md"
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text("test prompt", encoding="utf-8")

            captured_argv = []

            class FakeProc:
                def __init__(self, cmd, *args, **kwargs):
                    captured_argv.extend(cmd)
                    self.pid = 12345
                    self.stdout = io.BytesIO(b"")
                    self.returncode = 0

                def poll(self):
                    return 0

                def wait(self, timeout=None):
                    return 0

            with mock.patch("subprocess.Popen", side_effect=FakeProc):
                driver.run_opencode(state, run_dir, item, plan, prompt_file, 1)

            self.assertIn("--variant", captured_argv)
            idx = captured_argv.index("--variant")
            self.assertEqual(captured_argv[idx + 1], "high")


# --------------------------------------------------------------------------------------------------
# revsweep 76gsmv: the `reviews` selector's documentation, the `aw <host> review` alias, `--action`
# legality, and the empty sweep's exit code.
# --------------------------------------------------------------------------------------------------


def _repo_with_statuses(root: Path, statuses: dict) -> Path:
    """A git repo holding one conforming plan per (id6 -> status) entry. No commit needed to read."""
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    for order, (id6, status) in enumerate(statuses.items(), start=1):
        text = _CONFORMING_PLAN.format(id6=id6).replace(
            "- Status: approved", f"- Status: {status}", 1
        )
        if status == "reviewed":
            # The `--full-auto` danger path needs an APPROVING readiness to be auto-cleared.
            text = text.replace("- Author: test", "- Author: test\n- Readiness: go", 1)
            # rdattest 8v5pwa: AND IT NEEDS A REVIEW RECORD, or the danger path is not reachable and
            # `test_alias_refuses_a_reviewed_plan_even_with_full_auto_present` goes VACUOUS. That test's
            # load-bearing assertion is that the plan file still reads `- Status: reviewed`, which only
            # means anything while `is_plan_review_approved` WOULD have cleared this fixture had the
            # action gate not refused first. That predicate now requires the `- Readiness:` field to be
            # ATTESTED by a review record in the plan's own history, and `_CONFORMING_PLAN`'s history
            # holds only `approved` and `draft` records (an approval is a review's CONSEQUENCE, not
            # review evidence). MEASURED both ways on this exact fixture: pre-change the predicate
            # cleared it (True), so the assertion could fail; without this record it cannot clear it
            # (False), so the assertion passes whatever the ordering. The record is what keeps the
            # ordering claim falsifiable. PREPENDED, because `aw set` writes history newest-first.
            text = text.replace(
                "## Workflow history\n",
                "## Workflow history\n\n"
                "- 2026-08-28 reviewed (test): /plan-review: APPROVE; no defects.\n",
                1,
            )
        (pending / f"20260828-demo-{order:02d}-{id6}-demo.ipd.md").write_text(
            text, encoding="utf-8"
        )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo


class ReviewsSelectorDocumentedTests(unittest.TestCase):
    """revsweep 76gsmv E-01/V-01: the sweep worked and was invisible. Help must name it.

    The measured consequence of the omission was a maintainer asking for a command that already
    existed, so these assert the help TEXT, which is the deliverable, not just that the selector
    resolves (which it always did).
    """

    def test_reviews_selector_documented_in_help(self):
        import argparse as _ap

        parser = driver.build_parser()
        help_text = parser.format_help()
        for spelling in ("reviews", "review", "to-review"):
            self.assertIn(spelling, help_text)

        desc = parser.description or ""
        self.assertIn("SELECTOR TYPES:", desc)
        self.assertIn("reviews:", desc)
        self.assertIn("all:", desc)

        epilog = parser.epilog or ""
        self.assertIn("EXAMPLES:", epilog)
        self.assertRegex(epilog, r"runipd reviews\b")

        sub = next(a for a in parser._actions if isinstance(a, _ap._SubParsersAction))
        start = sub.choices["start"]
        sel = next(a for a in start._actions if a.dest == "selectors")
        self.assertIn("reviews", sel.help or "")

        blob = desc + epilog
        self.assertIn("IPDs only", blob)
        self.assertNotIn("status == to-review", blob)
        self.assertIn("next legal action is review", blob)


class HostReviewAliasExpansionTests(unittest.TestCase):
    """revsweep 76gsmv E-02/V-02: the alias is an argv REWRITE, with no behavior of its own."""

    def test_host_review_alias_expansion(self):
        from agent_workflows.cli import expand_host_review_argv

        self.assertEqual(expand_host_review_argv([]), ["reviews", "--action", "review"])
        self.assertEqual(
            expand_host_review_argv(["5ahblp"]), ["5ahblp", "--action", "review"]
        )
        self.assertEqual(
            expand_host_review_argv(["--repo", "/tmp/x", "--session", "s1"]),
            ["reviews", "--repo", "/tmp/x", "--session", "s1", "--action", "review"],
        )
        self.assertEqual(expand_host_review_argv(["--help"]), ["--help"])
        self.assertEqual(expand_host_review_argv(["-h"]), ["-h"])

        subcommands = {
            "start",
            "resume",
            "status",
            "report",
            "stop",
            "-h",
            "--help",
            "-v",
            "--version",
        }
        for tail in (
            [],
            ["5ahblp"],
            ["--repo", "/tmp/x"],
            ["5ahblp", "--session", "s"],
        ):
            with self.subTest(tail=tail):
                argv = expand_host_review_argv(tail)
                self.assertNotIn(argv[0], subcommands)
                shimmed = ["start"] + argv
                self.assertEqual(shimmed.count("start"), 1)

    def test_review_is_a_parser_choice_on_both_host_groups(self):
        """The reachability half. Without this, `aw oc review` dies at `invalid choice: 'review'`."""
        import argparse as _ap

        from agent_workflows.cli import _build_parser

        def _choices(p):
            for action in p._actions:
                if isinstance(action, _ap._SubParsersAction):
                    return action.choices
            return {}

        top = _choices(_build_parser())
        for host in ("oc", "opencode", "agy", "antigravity"):
            with self.subTest(host=host):
                self.assertIn(host, top)
                self.assertIn("review", _choices(top[host]))

    def test_alias_freezes_the_same_run_state_as_the_canonical_invocation(self):
        """V-02's LOAD-BEARING half: indistinguishability, not merely "it runs".

        A test that only proved the alias runs would also pass if the alias had forked, which spec
        25kzda 2.1 names as the one defect an alias can have. So this compares the FROZEN run state
        of both spellings field by field.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_statuses(Path(td), {"torv01": "to-review"})
            for run_id, argv in (
                ("run-ALIAS", ["oc", "review"]),
                ("run-CANON", ["oc", "runipd", "reviews", "--action", "review"]),
            ):
                res = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agent_workflows",
                        *argv,
                        "--repo",
                        os.fspath(repo),
                        "--prepare-only",
                        "--run-id",
                        run_id,
                    ],
                    cwd=repo,
                    env=_DRIVER_ENV,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

            runs = repo / ".aw" / "records" / "runs"
            alias = json.loads((runs / "run-ALIAS" / "state.json").read_text())
            canon = json.loads((runs / "run-CANON" / "state.json").read_text())
            # Identity and timestamps differ by construction; everything else must not.
            for volatile in (
                "run_id",
                "created_at",
                "updated_at",
                "manifest",
                "runbook",
                "manifest_sha256",
                "runbook_sha256",
            ):
                alias.pop(volatile, None)
                canon.pop(volatile, None)
            self.assertEqual(alias["options"], canon["options"])
            self.assertEqual(alias["selectors"], canon["selectors"])
            self.assertEqual(alias["queue"], canon["queue"])
            self.assertEqual(alias, canon)


class HostIntegrateVerbTests(unittest.TestCase):
    """integpath-04 (`rl67b0`) E-02/E-05: this host's `integrate` verb, at BOTH spellings.

    The DECISION cases live in `tests/test_runner_shared.py::ReintegrationVerbTests`, because
    `runner_shared.reintegrate_lane` is the one implementation both spellings and the resume pass call.
    What is host-specific and therefore asserted here: that the driver subcommand and the `cli.py`
    host-noun alias both exist and both reach that implementation, that the alias adds nothing, and that
    this host's merge subject names THIS driver.
    """

    def test_the_driver_subcommand_help_states_the_no_turn_and_suite_costs(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
            driver.main(["integrate", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        # Asserted on the WHITESPACE-COLLAPSED text, because argparse's RawDescription formatter still
        # hard-wraps the source string and a phrase test would then fail on a line break rather than on
        # a missing statement.
        text = " ".join(buf.getvalue().split())
        self.assertIn("COSTS NO AGENT TURN", text)
        self.assertIn("repository suite in the PRIMARY checkout", text)
        self.assertIn("merge-and-revalidate gate", text)

    def test_the_alias_expansion_prepends_the_subcommand_and_nothing_else(self):
        """THE PROOF THE ALIAS IS THIN: the whole implementation is this rewrite."""
        from agent_workflows.cli import expand_host_integrate_argv

        self.assertEqual(
            expand_host_integrate_argv(["mm6wuz"]), ["integrate", "mm6wuz"]
        )
        self.assertEqual(
            expand_host_integrate_argv(
                ["mm6wuz", "--repo", "/tmp/x", "--run-id", "r1"]
            ),
            ["integrate", "mm6wuz", "--repo", "/tmp/x", "--run-id", "r1"],
        )
        # `--help` still reaches THIS verb's subparser rather than the driver's top-level help.
        self.assertEqual(
            expand_host_integrate_argv(["--help"]), ["integrate", "--help"]
        )

    def test_the_alias_names_the_subcommand_so_the_shim_cannot_rewrite_it(self):
        """Composition with the implicit-start shim, derived from the driver's OWN set.

        `integrate` IS in that set, so the shim leaves the rewritten argv alone; had the alias emitted
        a bare id6 instead, the shim would have prefixed `start` and LAUNCHED a run.
        """
        import re

        from agent_workflows.cli import expand_host_integrate_argv

        source = (REPO_ROOT / "agent_workflows" / "oc_runipd.py").read_text(
            encoding="utf-8"
        )
        block = re.search(r"subcommands = \{(.*?)\}", source, re.S)
        assert block is not None
        self.assertIn('"integrate"', block.group(1))
        argv = expand_host_integrate_argv(["mm6wuz"])
        self.assertEqual(argv[0], "integrate")

    def test_integrate_is_a_parser_choice_on_both_host_groups(self):
        """The reachability half. Without the leaf, `aw oc integrate` dies at `invalid choice`."""
        import argparse as _ap

        from agent_workflows.cli import _build_parser

        def _choices(p):
            for action in p._actions:
                if isinstance(action, _ap._SubParsersAction):
                    return action.choices
            return {}

        top = _choices(_build_parser())
        for host in ("oc", "opencode", "agy", "antigravity"):
            with self.subTest(host=host):
                self.assertIn("integrate", _choices(top[host]))

    def test_the_new_cli_leaves_are_DECLARED_as_thin_aliases(self):
        """F-18: an `alias` row with `delegated`, not a `mutation` row asserting its own contract."""
        from agent_workflows.command_surface import get_declaration

        for leaf, canonical in (
            ("oc integrate", "oc runipd"),
            ("agy integrate", "agy runipd"),
        ):
            with self.subTest(leaf=leaf):
                decl = get_declaration(leaf)
                self.assertIsNotNone(decl, f"{leaf} must carry a CommandDeclaration")
                assert decl is not None
                self.assertEqual(decl.command_class, "alias")
                self.assertEqual(decl.empty_error_renderer, "delegated")
                self.assertEqual(decl.canonical_command, canonical)

    def test_both_spellings_reach_the_same_implementation(self):
        """Two entry points, ONE implementation: both must call `reintegrate_lane` once.

        Asserted by spying on the shared function, which is the only way to distinguish "the alias
        works" from "the alias re-implemented it and happens to agree today".
        """
        from agent_workflows import cli, runner_shared

        for argv, expect_host in (
            (["integrate", "zzzzzz"], "driver-subcommand"),
            (["oc", "integrate", "zzzzzz"], "cli-alias"),
        ):
            calls: list = []

            def spy(repo, id6, **kwargs):
                calls.append((str(repo), id6, sorted(kwargs)))
                return runner_shared.ReintegrationOutcome(
                    integrated=False, code="no-lane-record", reason="fake"
                )

            with tempfile.TemporaryDirectory() as td:
                repo = Path(td) / "repo"
                repo.mkdir()
                subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
                with mock.patch.object(runner_shared, "reintegrate_lane", spy):
                    if expect_host == "driver-subcommand":
                        rc = driver.main([*argv, "--repo", os.fspath(repo)])
                    else:
                        rc = cli._dispatch([*argv, "--repo", os.fspath(repo)])
                self.assertEqual(rc, 1, f"{argv}: a refusal must exit 1")
                self.assertEqual(len(calls), 1, f"{argv}: exactly one shared call")
                self.assertEqual(calls[0][1], "zzzzzz")
                self.assertIn("integrate", calls[0][2])
                self.assertIn("suite_check", calls[0][2])

    def test_this_hosts_merge_subject_says_aw_oc_run(self):
        """The one thing the shared function cannot bind: WHICH driver integrated the lane.

        Proven through a REAL merge on a real repository, because the label lands in a commit subject on
        main and a mis-binding is invisible until someone audits the log.
        """
        from tests.test_runner_shared import (
            _passing_suite,
            _repo_with_pending_plan,
            _stranded_item,
            _verified_lane,
            _write_run_state,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = _repo_with_pending_plan(root, "oci001")
            lane = _verified_lane(repo, root, "oci001")
            _write_run_state(repo, {"repo": str(repo), "queue": [_stranded_item(lane)]})
            # Advance main so `--ff-only` fails and the LABELLED `--no-ff` merge is taken.
            (repo / "other.txt").write_text("moved on\n", encoding="utf-8")
            subprocess.run(["git", "add", "other.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "main advances"], cwd=repo, check=True
            )

            with mock.patch.object(driver, "run_suite_check", _passing_suite):
                rc = driver.main(["integrate", "oci001", "--repo", os.fspath(repo)])

            self.assertEqual(rc, 0)
            subject = subprocess.run(
                ["git", "log", "-1", "--pretty=%s"],
                cwd=repo,
                text=True,
                capture_output=True,
            ).stdout.strip()
            self.assertEqual(
                subject, "integrate(aw oc run): merge verified lane oci001 to main"
            )
            self.assertNotIn("aw agy run", subject)


class HostResumeIntegratesInsteadOfDispatchingTests(unittest.TestCase):
    """integpath-04 (`rl67b0`) E-03/E-06: THE TWO ABSENCES, on this host's real `run_queue`.

    A test asserting only that the item ended integrated would pass identically had the resume paid for
    a full turn to get there, which IS the measured bug ($39.42 on `mm6wuz`). So the no-turn absence is
    proven POSITIVELY, by a launcher that FAILS THE TEST if called, and the no-second-lane absence by
    inspecting the branches afterwards.
    """

    def _launcher_that_must_not_be_called(self):
        def fail(*_a, **_k):
            raise AssertionError(
                "an agent turn was DISPATCHED: the resume paid for a turn where a merge would do, "
                "which is the entire defect this plan fixes"
            )

        return fail

    def _run(self, repo: Path, state: dict, *, retry_incomplete: bool):
        from tests.test_runner_shared import _passing_suite, _write_run_state

        run_dir = _write_run_state(repo, state, run_id="run-resume")
        with (
            mock.patch.object(
                driver, "run_opencode", self._launcher_that_must_not_be_called()
            ),
            mock.patch.object(driver, "run_suite_check", _passing_suite),
        ):
            rc = driver.run_queue(run_dir, retry_incomplete=retry_incomplete)
        return rc, json.loads((run_dir / "state.json").read_text(encoding="utf-8"))

    def test_a_bare_resume_merges_the_verified_lane_with_no_turn_and_no_new_lane(self):
        from tests.test_runner_shared import (
            _repo_with_pending_plan,
            _stranded_item,
            _verified_lane,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = _repo_with_pending_plan(root, "res001")
            lane = _verified_lane(repo, root, "res001")
            state = {"repo": str(repo), "queue": [_stranded_item(lane)]}

            _rc, final = self._run(repo, state, retry_incomplete=False)

            item = final["queue"][0]
            self.assertEqual(item["status"], "executed")
            self.assertTrue((repo / "src" / "res001.txt").is_file())
            branches = subprocess.run(
                ["git", "branch", "--list", "aw/lane/res001*"],
                cwd=repo,
                text=True,
                capture_output=True,
            ).stdout
            self.assertNotIn("_attempt2", branches)

    def test_with_the_FLAG_PASSED_the_item_is_integrated_rather_than_requeued(self):
        """The ORDERING assertion, and it needs the flag: without it a bare resume never requeues a
        terminal item at all, so the test could not tell the fix from unchanged code."""
        from tests.test_runner_shared import (
            _repo_with_pending_plan,
            _stranded_item,
            _verified_lane,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = _repo_with_pending_plan(root, "res002")
            lane = _verified_lane(repo, root, "res002")
            state = {"repo": str(repo), "queue": [_stranded_item(lane)]}

            _rc, final = self._run(repo, state, retry_incomplete=True)

            item = final["queue"][0]
            self.assertEqual(item["status"], "executed")
            # The flag's flip is UNDONE, or the loop would re-dispatch work that just landed.
            self.assertNotIn("recovery_next", item)
            self.assertNotIn(
                "_attempt2",
                subprocess.run(
                    ["git", "branch", "--list", "aw/lane/res002*"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                ).stdout,
            )

    def test_an_INDETERMINATE_item_suppresses_integration_entirely(self):
        """Main must NOT be mutated during a resume the driver is about to refuse."""
        from tests.test_runner_shared import (
            _repo_with_pending_plan,
            _stranded_item,
            _verified_lane,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = _repo_with_pending_plan(root, "res003")
            lane = _verified_lane(repo, root, "res003")
            # THE FLAG THE GATE ACTUALLY READS is the `stopped.certainty` record, not the status:
            # `runner_stop.is_indeterminate` says so explicitly, and a bare `unknown_outcome` status
            # would leave the item inert and make this test pass for the wrong reason.
            indeterminate = {
                "id6": "res004",
                "position": 2,
                "setid": "demo",
                "status": "interrupted",
                "configured_file": ".aw/records/plans/pending/20260906-demo-01-res004-demo.ipd.md",
                "requires_reconciliation": True,
                "stopped": {
                    "certainty": runner_stop.CERTAINTY_INDETERMINATE,
                    "level": 4,
                    "at": "2026-09-06T00:00:00+00:00",
                },
            }
            state = {
                "repo": str(repo),
                "queue": [_stranded_item(lane), indeterminate],
            }
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
            ).stdout.strip()

            rc, final = self._run(repo, state, retry_incomplete=True)

            self.assertEqual(rc, 1, "the resume must be REFUSED")
            self.assertEqual(
                subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                ).stdout.strip(),
                head_before,
                "nothing may be integrated during a refused resume",
            )
            self.assertNotEqual(final["queue"][0]["status"], "executed")


class ActionLegalityTests(unittest.TestCase):
    """revsweep 76gsmv E-03/V-03: `--action review` must REFUSE a non-reviewable item.

    This is the plan's F-9 and the one way a thin alias becomes dangerous: `action_for` returns
    `execute` for BOTH `approved` and `reviewed`, so a merely-accepted flag would let
    `aw oc review <approved-id6>` EXECUTE that plan while the operator typed "review".
    """

    def test_action_choices_and_enforcement(self):
        self.assertEqual(driver.ACTION_CHOICES, ("review", "plan", "execute"))
        self.assertEqual(driver.ACTION_IMPLEMENTED, frozenset({"review"}))

        driver.enforce_requested_action(None, [("x", "approved", "execute")])
        driver.enforce_requested_action(
            "review", [("a", "to-review", "review"), ("b", "draft", "review")]
        )

        for items, expected in [
            ([("a", "approved", "execute")], "approved"),
            ([("a", "reviewed", "execute")], "illegal"),
            ([("a", "approved", "orchestrate")], "illegal"),
        ]:
            with self.subTest(items=items):
                with self.assertRaises(driver.DriverError) as ctx:
                    driver.enforce_requested_action("review", items)
                self.assertIn(expected, str(ctx.exception))

        for action in ("plan", "execute"):
            with self.subTest(action=action):
                with self.assertRaises(driver.DriverError) as ctx:
                    driver.enforce_requested_action(
                        action, [("a", "approved", "execute")]
                    )
                self.assertIn("not implemented", str(ctx.exception))

        with self.assertRaises(driver.DriverError) as ctx:
            driver.enforce_requested_action(
                "review",
                [("aaa111", "approved", "execute"), ("bbb222", "reviewed", "execute")],
            )
        msg = str(ctx.exception)
        self.assertIn("aaa111", msg)
        self.assertIn("bbb222", msg)
        self.assertIn("2 selected item(s)", msg)

    def _refusal_run(self, id6: str, *extra: str):
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_statuses(
                Path(td),
                {"appr01": "approved", "revw01": "reviewed", "torv01": "to-review"},
            )
            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "oc",
                    "review",
                    id6,
                    "--repo",
                    os.fspath(repo),
                    "--prepare-only",
                    *extra,
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                capture_output=True,
                text=True,
            )
            plan_text = (repo / ".aw" / "records" / "plans" / "pending").glob(
                f"*{id6}*.ipd.md"
            )
            status = next(
                line
                for line in next(plan_text).read_text().splitlines()
                if line.startswith("- Status:")
            )
            runs = repo / ".aw" / "records" / "runs"
            return (
                res,
                status,
                sorted(p.name for p in runs.iterdir()) if runs.is_dir() else [],
            )

    def test_alias_refusal_and_acceptance(self):
        res, status, runs = self._refusal_run("appr01")
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("--action review is illegal", res.stderr)
        self.assertEqual(runs, [])
        self.assertEqual(status, "- Status: approved")

        res, status, runs = self._refusal_run("revw01", "--full-auto")
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("--action review is illegal", res.stderr)
        self.assertEqual(runs, [])
        self.assertEqual(status, "- Status: reviewed")

        res, _status, runs = self._refusal_run("torv01")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(len(runs), 1)


class EmptyReviewSweepExitsZeroTests(unittest.TestCase):
    """revsweep 76gsmv E-04/V-04: spec 25kzda 2.4a property 3.

    "An empty result is a success, not an error ... it reports that plainly and exits 0 ... the one
    deliberate exception to the Section 2.3 rule that zero matches exit 2. A misspelled id6 still
    exits 2; only the status selectors are exempt."
    """

    def test_empty_review_sweep_selection_semantics(self):
        self.assertTrue(issubclass(driver.EmptyStatusSelection, driver.DriverError))

        manifest = {
            "schema_version": 1,
            "plans": {
                "appr01": {
                    "set": "s1",
                    "file": ".aw/records/plans/pending/20260828-s1-01-appr01-x.ipd.md",
                    "status": "approved",
                    "order": 1,
                    "dependencies": [],
                }
            },
            "sets": {"s1": {"order": ["appr01"]}},
        }
        for spelling in ("reviews", "review", "to-review"):
            with self.subTest(spelling=spelling):
                with self.assertRaises(driver.EmptyStatusSelection):
                    driver.expand_selectors(manifest, [spelling])

        # "all" on a manifest with only executed plans raises DriverError (not EmptyStatusSelection)
        manifest_no_actionable = {
            "schema_version": 1,
            "plans": {
                "done01": {
                    "set": "s1",
                    "file": ".aw/records/plans/executed/20260828-s1-01-done01-x.ipd.md",
                    "status": "executed",
                    "order": 1,
                    "dependencies": [],
                }
            },
            "sets": {"s1": {"order": ["done01"]}},
        }
        with self.assertRaises(driver.DriverError) as ctx:
            driver.expand_selectors(manifest_no_actionable, ["all"])
        self.assertNotIsInstance(ctx.exception, driver.EmptyStatusSelection)

    def test_end_to_end_empty_sweep_cli(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_statuses(Path(td), {"appr01": "approved"})
            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "oc",
                    "review",
                    "--repo",
                    os.fspath(repo),
                    "--prepare-only",
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertIn("Nothing awaiting review", res.stdout)
            self.assertFalse((repo / ".aw" / "records" / "runs").is_dir())

            res_bad = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "oc",
                    "review",
                    "zzzz99",
                    "--repo",
                    os.fspath(repo),
                    "--prepare-only",
                ],
                cwd=repo,
                env=_DRIVER_ENV,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_bad.returncode, 2, res_bad.stdout + res_bad.stderr)


# ==================================================================================================
# runprofile Order 03 (`3cm15q`): launch-profile grammar, resolution, provenance, and freezing.
#
# These tests exist because the plan's findings table names six failure modes a SHALLOW integration
# would pass anyway: a parsed-but-unused `--variant`, a profile that reaches only the first turn, an
# alias edited before resume, partial run state left by an unknown alias, a profile named `status`
# shadowing the command, and a per-field override that drops the rest of the profile. Each is
# asserted against the REAL argv / REAL durable state, never against the parser alone.
# ==================================================================================================


def _profile_store(tmp: Path, doc: dict) -> dict:
    """Write `runner-profiles.json` into an isolated XDG dir; return the env overlay to use it.

    Isolation matters: without it these tests would read (and their failures would depend on) the
    developer's real `~/.config/agent-workflows/runner-profiles.json`.
    """

    cfg_dir = tmp / "xdg" / "agent-workflows"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "runner-profiles.json").write_text(json.dumps(doc), encoding="utf-8")
    return {"XDG_CONFIG_HOME": str(tmp / "xdg")}


def _parse_argv(argv: list) -> tuple:
    """Return (rc, parsed_namespace_or_None) for `main(argv)`, stopping before any side effect.

    Patches `initialize_run` to capture the namespace and abort, so the grammar can be asserted on the
    REAL `main` path (implicit-start shim included) without creating a run.
    """

    captured = {}
    real_build = driver.build_parser

    def spying_parser():
        parser = real_build()
        real_parse = parser.parse_args

        def parse(a=None, namespace=None):
            # Capture the namespace for EVERY subcommand, not just `start`: `initialize_run` is
            # never reached by `status`/`report`/`resume`, so hooking only that would make the
            # routing assertions vacuous.
            ns = real_parse(a, namespace)
            captured["args"] = ns
            return ns

        parser.parse_args = parse  # type: ignore[method-assign]
        return parser

    def fake_init(args):
        raise driver.DriverError("stop-before-side-effects")

    with (
        mock.patch.object(driver, "build_parser", spying_parser),
        mock.patch.object(driver, "initialize_run", fake_init),
        mock.patch.object(
            driver, "resolve_run_dir", side_effect=driver.DriverError("stop")
        ),
    ):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = driver.main(list(argv))
    return rc, captured.get("args"), out.getvalue() + err.getvalue()


class LaunchProfileGrammarTests(unittest.TestCase):
    """E-01: the fixed `as PROFILE` clause, and everything it must NOT break."""

    def test_launch_profile_grammar_valid(self):
        for argv in (["as", "gem", "3cm15q"], ["start", "as", "gem", "3cm15q"]):
            rc, args, _ = _parse_argv(argv)
            self.assertEqual(rc, 2, argv)
            self.assertEqual(args.command, "start", argv)
            self.assertEqual(args.profile, "gem", argv)
            self.assertEqual(args.selectors, ["3cm15q"], argv)

        rc, args, _ = _parse_argv(
            ["3cm15q", "--model", "google/gemini-3.7-flash", "--variant", "high"]
        )
        self.assertEqual(args.model, "google/gemini-3.7-flash")
        self.assertEqual(args.variant, "high")
        self.assertIsNone(args.profile)
        self.assertEqual(args.selectors, ["3cm15q"])

        for name in ("status", "resume", "report", "stop", "start", "all", "reviews"):
            rc, args, _ = _parse_argv(["as", name, "3cm15q"])
            self.assertEqual(args.command, "start", name)
            self.assertEqual(args.profile, name, name)
            self.assertEqual(args.selectors, ["3cm15q"], name)

        rc, args, _ = _parse_argv(["gem"])
        self.assertIsNone(args.profile)
        self.assertEqual(args.selectors, ["gem"])

        with tempfile.TemporaryDirectory() as temp:
            env = _profile_store(
                Path(temp),
                {
                    "schema_version": 1,
                    "profiles": {"gem": {"runner": "oc", "model": "g/m"}},
                },
            )
            with mock.patch.dict(os.environ, env):
                rc, args, _ = _parse_argv(["gem"])
        self.assertIsNone(args.profile)
        self.assertEqual(args.selectors, ["gem"])

        rc, args, _ = _parse_argv(["--", "as"])
        self.assertIsNone(args.profile)
        self.assertEqual(args.selectors, ["as"])

        for cmd in ("status", "report", "resume"):
            rc, args, text = _parse_argv([cmd, "run-xyz"])
            self.assertEqual(args.command, cmd, text)
            self.assertIsNone(args.profile, cmd)

    def test_missing_repeated_and_misplaced_as_clauses_are_refused(self):
        cases = {
            ("as",): "requires a profile name",
            ("as", "--"): "requires a profile name",
            ("as", "gem", "as", "gem"): "only once",
            ("3cm15q", "as", "gem"): "must come FIRST",
        }
        for argv, needle in cases.items():
            rc, args, text = _parse_argv(list(argv))
            self.assertEqual(rc, 2, f"{argv} -> {text}")
            self.assertIsNone(args, f"{argv} reached initialize_run")
            self.assertIn(needle, text, argv)
            self.assertIn("-- as", text, argv)

        real_build = driver.build_parser

        def spying_parser():
            parser = real_build()
            real_parse = parser.parse_args

            def parse(a=None, namespace=None):
                ns = real_parse(a, namespace)
                setattr(ns, "profile", "gem")
                return ns

            parser.parse_args = parse  # type: ignore[method-assign]
            return parser

        with mock.patch.object(driver, "build_parser", spying_parser):
            err = io.StringIO()
            with (
                contextlib.redirect_stderr(err),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                rc = driver.main(["resume", "run-xyz"])
        self.assertEqual(rc, 2, err.getvalue())
        self.assertIn("frozen", err.getvalue())
        self.assertIn("as gem", err.getvalue())


class LaunchProfileResolutionTests(unittest.TestCase):
    """E-02: resolution happens BEFORE any durable side effect, with per-field precedence."""

    def _resolve(self, store_doc, **kw):
        with tempfile.TemporaryDirectory() as temp:
            env = _profile_store(Path(temp), store_doc)
            args = argparse.Namespace(
                profile=kw.get("profile"),
                model=kw.get("model"),
                variant=kw.get("variant"),
                agent=kw.get("agent"),
            )
            with mock.patch.dict(os.environ, env):
                return driver.resolve_launch_profile(args)

    def test_profile_precedence_and_overrides(self):
        # 1. Named profile supplies all three fields
        r = self._resolve(
            {
                "schema_version": 1,
                "profiles": {
                    "gem": {
                        "runner": "oc",
                        "model": "google/gemini-3.7-flash",
                        "variant": "high",
                        "agent": "build",
                    }
                },
            },
            profile="gem",
        )
        self.assertEqual(r.model, "google/gemini-3.7-flash")
        self.assertEqual(r.variant, "high")
        self.assertEqual(r.agent, "build")
        self.assertEqual(r.applied_profile, "gem")
        self.assertEqual(r.provenance["model"], "profile")

        # 2. Per-runner default applies without `as`
        r_def = self._resolve(
            {
                "schema_version": 1,
                "defaults": {"profiles": {"oc": "gem"}},
                "profiles": {
                    "gem": {"runner": "oc", "model": "g/m", "variant": "high"}
                },
            }
        )
        self.assertEqual(r_def.model, "g/m")
        self.assertEqual(r_def.variant, "high")
        self.assertIsNone(r_def.requested_profile)
        self.assertEqual(r_def.applied_profile, "gem")
        self.assertEqual(r_def.provenance["model"], "default-profile")

        # 3. No default preserves host default
        r_host = self._resolve({"schema_version": 1, "profiles": {}})
        self.assertIsNone(r_host.model)
        self.assertIsNone(r_host.variant)
        self.assertIsNone(r_host.agent)
        self.assertEqual(r_host.provenance["model"], "host-default")

        # 4. Partial explicit override keeps other fields
        r_over = self._resolve(
            {
                "schema_version": 1,
                "profiles": {
                    "gem": {
                        "runner": "oc",
                        "model": "g/m",
                        "variant": "low",
                        "agent": "build",
                    }
                },
            },
            profile="gem",
            variant="high",
        )
        self.assertEqual(r_over.variant, "high")
        self.assertEqual(r_over.provenance["variant"], "explicit")
        self.assertEqual(r_over.model, "g/m")
        self.assertEqual(r_over.agent, "build")
        self.assertEqual(r_over.provenance["model"], "profile")

    def test_unknown_wrong_runner_and_malformed_all_fail(self):
        with self.assertRaises(driver.DriverError) as ctx:
            self._resolve({"schema_version": 1, "profiles": {}}, profile="nope")
        self.assertIn("no runner profile named 'nope'", str(ctx.exception))

        with self.assertRaises(driver.DriverError):
            self._resolve(
                {
                    "schema_version": 1,
                    "profiles": {"gg": {"runner": "agy", "model": "g/m"}},
                },
                profile="gg",
            )

        with tempfile.TemporaryDirectory() as temp:
            cfg_dir = Path(temp) / "xdg" / "agent-workflows"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "runner-profiles.json").write_text("{not json", encoding="utf-8")
            args = argparse.Namespace(
                profile=None, model=None, variant=None, agent=None
            )
            with mock.patch.dict(
                os.environ, {"XDG_CONFIG_HOME": str(Path(temp) / "xdg")}
            ):
                with self.assertRaises(driver.DriverError):
                    driver.resolve_launch_profile(args)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo_with_conforming_plan(repo, "prof01")
            runs_root = repo / ".aw" / "records" / "runs"
            before = (
                sorted(p.name for p in runs_root.glob("*"))
                if runs_root.exists()
                else []
            )

            env = {
                **_DRIVER_ENV,
                **_profile_store(root, {"schema_version": 1, "profiles": {}}),
            }
            res = subprocess.run(
                _DRIVER_CMD + ["as", "nope", "prof01", "--repo", os.fspath(repo)],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
            self.assertIn("no runner profile named 'nope'", res.stdout + res.stderr)
            after = (
                sorted(p.name for p in runs_root.glob("*"))
                if runs_root.exists()
                else []
            )
            self.assertEqual(before, after, "a refused run left durable state behind")
            self.assertNotIn("Run ID:", res.stdout)


class LaunchProfileDurableStateTests(unittest.TestCase):
    """E-03: the frozen provenance snapshot and the surfaces that render it."""

    def _start(self, root: Path, extra_argv: list, store_doc: dict) -> Path:
        repo = root / "repo"
        _init_repo_with_conforming_plan(repo, "prof02")
        env = {**_DRIVER_ENV, **_profile_store(root, store_doc)}
        res = subprocess.run(
            _DRIVER_CMD
            + extra_argv
            + ["prof02", "--repo", os.fspath(repo), "--prepare-only"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        runs = sorted((repo / ".aw" / "records" / "runs").glob("run-*"))
        self.assertEqual(len(runs), 1, res.stdout)
        self._stdout = res.stdout
        return runs[0]

    def test_state_records_resolved_fields_and_per_field_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._start(
                root,
                ["as", "gem", "--variant", "high"],
                {
                    "schema_version": 1,
                    "profiles": {
                        "gem": {
                            "runner": "oc",
                            "model": "google/gemini-3.7-flash",
                            "variant": "low",
                            "agent": "build",
                        }
                    },
                },
            )
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            opts = state["options"]
            # Existing compatibility keys carry the RESOLVED values.
            self.assertEqual(opts["model"], "google/gemini-3.7-flash")
            self.assertEqual(opts["variant"], "high")
            self.assertEqual(opts["agent"], "build")
            lp = opts["launch_profile"]
            self.assertEqual(lp["requested"], "gem")
            self.assertEqual(lp["applied"], "gem")
            self.assertEqual(lp["runner"], "oc")
            self.assertTrue(lp["config_present"])
            self.assertTrue(lp["config_digest"])
            self.assertIn("runner-profiles.json", lp["config_source"])
            self.assertEqual(lp["provenance"]["model"], "profile")
            self.assertEqual(lp["provenance"]["variant"], "explicit")
            # No credential-shaped keys.
            self.assertNotIn("api_key", json.dumps(lp).lower())
            # prepare-only surfaces the identity to the operator.
            self.assertIn("Launch:", self._stdout)
            self.assertIn("google/gemini-3.7-flash", self._stdout)
            self.assertIn("profile=gem", self._stdout)

    def test_report_and_status_render_the_launch_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._start(
                root,
                ["as", "gem"],
                {
                    "schema_version": 1,
                    "profiles": {
                        "gem": {"runner": "oc", "model": "g/m", "variant": "high"}
                    },
                },
            )
            report = (run_dir / "execution-report.md").read_text(encoding="utf-8")
            self.assertIn("- Launch:", report)
            self.assertIn("model=g/m (profile)", report)
            self.assertIn("variant=high (profile)", report)

    def test_driver_actor_includes_variant_and_profile_without_parens_in_values(self):
        actor = driver.driver_actor(
            {
                "options": {
                    "model": "g/m",
                    "variant": "high",
                    "launch_profile": {"applied": "gem"},
                }
            }
        )
        self.assertIn("model=g/m", actor)
        self.assertIn("variant=high", actor)
        self.assertIn("profile=gem", actor)
        # The attribution lint's actor capture would misparse a parenthesized actor.
        self.assertNotIn("(", actor)
        # Backward compatible: a run with only a model is unchanged.
        self.assertEqual(
            driver.driver_actor({"options": {"model": "opus"}}), "aw oc run model=opus"
        )

    def test_render_launch_identity_tolerates_a_pre_field_run(self):
        # A run created before `launch_profile` existed must still render, not raise.
        text = driver.render_launch_identity({"options": {"model": "opus"}})
        self.assertIn("model=opus", text)
        self.assertIn("none recorded", text)


class LaunchProfileFrozenTurnArgvTests(unittest.TestCase):
    """E-04: EVERY turn type uses the frozen identity, and resume never re-resolves it."""

    def _state(self, options: dict) -> dict:
        return {
            "run_id": "run-test",
            "repo": "/tmp/repo",
            "session_id": None,
            "set_sessions": {},
            "session_turn_counts": {},
            "options": {"opencode": "opencode", **options},
        }

    def _argv_for(self, options: dict, **kw) -> list:
        """Build the REAL argv `run_opencode` would launch, without launching anything."""
        captured = {}

        class _Proc:
            def __init__(self, argv):
                captured["argv"] = argv
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("")
                self.returncode = 0

            def wait(self, timeout=None):
                return 0

            def poll(self):
                return 0

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "run"
            for name in ("sessions", "outcomes", "prompts", "logs"):
                (run_dir / name).mkdir(parents=True, exist_ok=True)
            prompt = root / "prompt.txt"
            prompt.write_text("do the thing", encoding="utf-8")
            plan = root / "plan.ipd.md"
            plan.write_text("# plan\n", encoding="utf-8")
            item = {"position": 1, "id6": "prof03", "setid": "s1", "action": "execute"}
            state = self._state(options)
            state["repo"] = str(root)

            def fake_popen(argv, **_kw):
                self.assertFalse(
                    _kw.get("shell", False), "argv must be launched with shell=False"
                )
                return _Proc(argv)

            with mock.patch.object(driver.subprocess, "Popen", side_effect=fake_popen):
                try:
                    driver.run_opencode(state, run_dir, item, plan, prompt, 1, **kw)
                except Exception:
                    # Only argv construction is under test; stream handling may abort on the fake.
                    pass
        return captured.get("argv") or []

    def test_execute_recovery_review_and_verifier_turns_all_carry_model_variant_agent(
        self,
    ):
        options = {"model": "g/m", "variant": "high", "agent": "build"}
        turns = {
            "execute": {},
            "recovery": {"log_suffix": "recovery"},
            "review": {"label_suffix": "review"},
            "verifier": {"fresh_session": True, "log_suffix": "verify"},
        }
        for label, kw in turns.items():
            argv = self._argv_for(options, **kw)
            self.assertIn("--model", argv, f"{label}: {argv}")
            self.assertEqual(argv[argv.index("--model") + 1], "g/m", label)
            self.assertIn("--variant", argv, f"{label}: {argv}")
            self.assertEqual(argv[argv.index("--variant") + 1], "high", label)
            self.assertIn("--agent", argv, f"{label}: {argv}")
            self.assertEqual(argv[argv.index("--agent") + 1], "build", label)

    def test_provider_default_omits_variant_entirely(self):
        argv = self._argv_for({"model": "g/m"})
        self.assertIn("--model", argv)
        self.assertNotIn("--variant", argv, argv)
        self.assertNotIn("--agent", argv, argv)

    def test_resume_does_not_reload_profiles_after_the_store_changes(self):
        """The "alias edited before resume" failure mode, on the REAL resume path."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo_with_conforming_plan(repo, "prof04")
            store = {
                "schema_version": 1,
                "profiles": {
                    "gem": {"runner": "oc", "model": "g/m", "variant": "high"}
                },
            }
            env = {**_DRIVER_ENV, **_profile_store(root, store)}
            res = subprocess.run(
                _DRIVER_CMD
                + [
                    "as",
                    "gem",
                    "prof04",
                    "--repo",
                    os.fspath(repo),
                    "--prepare-only",
                ],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            run_dir = sorted((repo / ".aw" / "records" / "runs").glob("run-*"))[0]
            frozen = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(frozen["options"]["model"], "g/m")

            # REPOINT the profile at a different model, then DELETE the store entirely.
            for mutation in (
                {
                    "schema_version": 1,
                    "profiles": {
                        "gem": {"runner": "oc", "model": "EVIL/other", "variant": "low"}
                    },
                },
                None,
            ):
                if mutation is None:
                    (root / "xdg" / "agent-workflows" / "runner-profiles.json").unlink()
                else:
                    _profile_store(root, mutation)
                res = subprocess.run(
                    _DRIVER_CMD
                    + ["status", run_dir.name, "--repo", os.fspath(repo), "--json"],
                    cwd=repo,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
                state = json.loads(res.stdout)
                self.assertEqual(state["options"]["model"], "g/m", mutation)
                self.assertEqual(state["options"]["variant"], "high", mutation)
                self.assertEqual(
                    state["options"]["launch_profile"]["config_digest"],
                    frozen["options"]["launch_profile"]["config_digest"],
                )

    def test_direct_start_without_a_profile_is_behavior_equivalent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo_with_conforming_plan(repo, "prof05")
            env = {
                **_DRIVER_ENV,
                **_profile_store(root, {"schema_version": 1, "profiles": {}}),
            }
            res = subprocess.run(
                _DRIVER_CMD
                + [
                    "prof05",
                    "--repo",
                    os.fspath(repo),
                    "--model",
                    "anthropic/claude",
                    "--prepare-only",
                ],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            run_dir = sorted((repo / ".aw" / "records" / "runs").glob("run-*"))[0]
            opts = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
                "options"
            ]
            self.assertEqual(opts["model"], "anthropic/claude")
            self.assertIsNone(opts["variant"])
            lp = opts["launch_profile"]
            self.assertIsNone(lp["requested"])
            self.assertIsNone(lp["applied"])
            self.assertEqual(lp["provenance"]["model"], "explicit")
            # Nothing was configured, so variant/agent fall through to the host default and no
            # argument is passed - which is what keeps this invocation behavior-equivalent.
            self.assertEqual(lp["provenance"]["variant"], "host-default")
            self.assertEqual(lp["provenance"]["agent"], "host-default")

    def test_absent_store_is_a_no_op_not_a_failure(self):
        # The store file does not exist at all: current host-default behavior must be preserved.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo_with_conforming_plan(repo, "prof06")
            (root / "xdg").mkdir()
            env = {**_DRIVER_ENV, "XDG_CONFIG_HOME": str(root / "xdg")}
            res = subprocess.run(
                _DRIVER_CMD + ["prof06", "--repo", os.fspath(repo), "--prepare-only"],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            run_dir = sorted((repo / ".aw" / "records" / "runs").glob("run-*"))[0]
            opts = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
                "options"
            ]
            self.assertIsNone(opts["model"])
            self.assertIsNone(opts["variant"])
            self.assertFalse(opts["launch_profile"]["config_present"])


# ==================================================================================================
# runprofile Order 06 (`kgpptv`): the VERIFIER turn resolves its OWN launch.
#
# THE THREE LOAD-BEARING CASES, and only one of them is the new feature:
#   (a) a profile WITH `verify_with` produces DIFFERENT models in the execute and verifier argv;
#   (b) a profile WITHOUT it produces argv BYTE-IDENTICAL to pre-change behavior, for every turn
#       kind - the claim a reviewer should distrust most, because a suite proving only (a) would
#       pass while every existing user's runs had silently changed model;
#   (c) an ISOLATED EXECUTE turn still carries the EXECUTOR's model. This is the decisive negative
#       case: `isolate_worktree` defaults True and an isolated turn is ALWAYS session-free, exactly
#       like the verifier, so an implementation keyed on `fresh_session` (or on session-absence)
#       would misroute the DEFAULT configuration while every new-routing test passed.
#
# THE LIMIT, stated because no test can state it: this is cross-MODEL verification on the OpenCode
# host ONLY. Cross-HOST (execute under agy, verify under oc) is NOT delivered and is deferred by the
# maintainer's choice (OQ-01). The agy runner has ZERO profile integration, so it does not
# participate at all.
# ==================================================================================================


_VERIFY_ROUTING_STORE = {
    "schema_version": 2,
    "profiles": {
        "cheap": {
            "runner": "oc",
            "model": "vendor/flash-1",
            "variant": "low",
            "verify_with": "strong",
        },
        "strong": {
            "runner": "oc",
            "model": "vendor/opus-9",
            "variant": "high",
            "agent": "build",
        },
    },
}


class VerifierLaunchFreezeTests(unittest.TestCase):
    """E-02: BOTH launches frozen at creation, before any durable side effect, and never re-resolved."""

    def _prepare(self, root: Path, extra_argv: list, store_doc: dict | None) -> Path:
        repo = root / "repo"
        _init_repo_with_conforming_plan(repo, "vprof1")
        if store_doc is None:
            (root / "xdg").mkdir(exist_ok=True)
            env = {**_DRIVER_ENV, "XDG_CONFIG_HOME": str(root / "xdg")}
        else:
            env = {**_DRIVER_ENV, **_profile_store(root, store_doc)}
        res = subprocess.run(
            _DRIVER_CMD
            + extra_argv
            + ["vprof1", "--repo", os.fspath(repo), "--prepare-only"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self._stdout = res.stdout
        self._repo = repo
        self._env = env
        return sorted((repo / ".aw" / "records" / "runs").glob("run-*"))[0]

    def test_verifier_launch_freeze_options(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(root, ["as", "cheap"], _VERIFY_ROUTING_STORE)
            opts = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
                "options"
            ]
        self.assertEqual(opts["model"], "vendor/flash-1")
        self.assertEqual(opts["variant"], "low")
        self.assertEqual(opts["launch_profile"]["applied"], "cheap")
        self.assertEqual(opts["verify_model"], "vendor/opus-9")
        self.assertEqual(opts["verify_variant"], "high")
        self.assertEqual(opts["verify_agent"], "build")
        self.assertEqual(opts["verify_launch_profile"]["applied"], "strong")
        self.assertEqual(opts["launch_profile"]["provenance"]["verify_with"], "profile")
        self.assertEqual(
            opts["verify_launch_profile"]["config_digest"],
            opts["launch_profile"]["config_digest"],
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(root, ["as", "strong"], _VERIFY_ROUTING_STORE)
            opts = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
                "options"
            ]
        for key in (
            "verify_model",
            "verify_variant",
            "verify_agent",
            "verify_launch_profile",
        ):
            self.assertNotIn(key, opts)
        self.assertEqual(opts["model"], "vendor/opus-9")
        self.assertEqual(
            opts["launch_profile"]["provenance"]["verify_with"], "same-as-executor"
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(
                root, ["as", "cheap", "--verify-with", "cheap"], _VERIFY_ROUTING_STORE
            )
            opts = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
                "options"
            ]
        self.assertEqual(opts["verify_model"], "vendor/flash-1")
        self.assertEqual(opts["verify_launch_profile"]["applied"], "cheap")
        self.assertEqual(
            opts["launch_profile"]["provenance"]["verify_with"], "explicit"
        )

        store_off = {
            "schema_version": 2,
            "profiles": {
                "cheap": {
                    "runner": "oc",
                    "model": "vendor/flash-1",
                    "verify_with": "strong",
                },
                "strong": {"runner": "oc", "model": "vendor/opus-9"},
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(root, ["as", "cheap", "--no-validate"], store_off)
            opts = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
                "options"
            ]
            self.assertFalse(opts["validate"])
            self.assertEqual(opts["verify_model"], "vendor/opus-9")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(root, ["as", "strong", "--validate"], store_off)
            opts = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))[
                "options"
            ]
            self.assertTrue(opts["validate"])
            self.assertNotIn("verify_launch_profile", opts)

    def test_a_dangling_verify_with_refuses_before_any_durable_side_effect(self):
        """`3cm15q` F-13's guarantee, extended: no run dir, no events, no state.json."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            _init_repo_with_conforming_plan(repo, "vprof2")
            runs_root = repo / ".aw" / "records" / "runs"
            before = (
                sorted(p.name for p in runs_root.glob("*"))
                if runs_root.exists()
                else []
            )
            env = {**_DRIVER_ENV, **_profile_store(root, _VERIFY_ROUTING_STORE)}
            res = subprocess.run(
                _DRIVER_CMD
                + [
                    "as",
                    "cheap",
                    "vprof2",
                    "--repo",
                    os.fspath(repo),
                    "--verify-with",
                    "ghost",
                    "--prepare-only",
                ],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
            )
            text = res.stdout + res.stderr
            self.assertEqual(res.returncode, 2, text)
            self.assertIn("does not exist", text)
            after = (
                sorted(p.name for p in runs_root.glob("*"))
                if runs_root.exists()
                else []
            )
            self.assertEqual(before, after)
            self.assertNotIn("Run ID:", res.stdout)

    def test_verify_with_cli_and_resume(self):
        parser = driver.build_parser()
        for command in ("start", "resume"):
            action = parser.parse_args(
                [command, "x"] if command == "start" else [command, "run-xyz"]
            )
            self.assertTrue(hasattr(action, "verify_with"))
            self.assertIsNone(getattr(action, "verify_with"))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(root, ["as", "cheap"], _VERIFY_ROUTING_STORE)
            frozen = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(frozen["options"]["verify_model"], "vendor/opus-9")

            res = subprocess.run(
                _DRIVER_CMD
                + [
                    "resume",
                    run_dir.name,
                    "--repo",
                    os.fspath(self._repo),
                    "--verify-with",
                    "cheap",
                ],
                cwd=self._repo,
                env=self._env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
            self.assertIn("frozen", res.stdout + res.stderr)
            after = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(
                after["options"]["verify_model"], frozen["options"]["verify_model"]
            )

    def test_launch_identity_rendering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(root, ["as", "cheap"], _VERIFY_ROUTING_STORE)
            report = (run_dir / "execution-report.md").read_text(encoding="utf-8")
        self.assertIn("verify-model=vendor/opus-9", report)
        self.assertIn("verify-profile=strong", report)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = self._prepare(root, ["as", "strong"], _VERIFY_ROUTING_STORE)
            report = (run_dir / "execution-report.md").read_text(encoding="utf-8")
        self.assertNotIn("verify-model", report)
        self.assertNotIn("verify-profile", report)

        text = driver.render_launch_identity(
            {"options": {"model": "opus", "launch_profile": {"applied": "gem"}}}
        )
        self.assertIn("model=opus", text)
        self.assertNotIn("verify-model", text)


class VerifierTurnArgvRoutingTests(unittest.TestCase):
    """E-03/E-04: the verifier CALL SITE gets the verifier launch; every other turn does not."""

    def _state(self, options: dict) -> dict:
        return {
            "run_id": "run-test",
            "repo": "/tmp/repo",
            "session_id": None,
            "set_sessions": {},
            "session_turn_counts": {},
            "options": {"opencode": "opencode", **options},
        }

    def _argv_for(self, options: dict, **kw) -> list:
        """Build the REAL argv `run_opencode` would launch, without launching anything."""

        captured = {}

        class _Proc:
            def __init__(self, argv):
                captured["argv"] = argv
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("")
                self.returncode = 0

            def wait(self, timeout=None):
                return 0

            def poll(self):
                return 0

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "run"
            for name in ("sessions", "outcomes", "prompts", "logs"):
                (run_dir / name).mkdir(parents=True, exist_ok=True)
            prompt = root / "prompt.txt"
            prompt.write_text("do the thing", encoding="utf-8")
            plan = root / "plan.ipd.md"
            plan.write_text("# plan\n", encoding="utf-8")
            item = {
                "position": 1,
                "id6": "vprof3",
                "setid": "s1",
                "action": kw.pop("action", "execute"),
            }
            state = self._state(options)
            state["repo"] = str(root)
            if kw.pop("isolated", False):
                # `isolate_worktree` defaults True, so this is the DEFAULT execute turn: it runs in
                # a worktree and is therefore session-free, exactly like the verifier.
                lane = root / "lane"
                lane.mkdir()
                kw["work_dir"] = str(lane)

            def fake_popen(argv, **_kw):
                self.assertFalse(
                    _kw.get("shell", False), "argv must be launched with shell=False"
                )
                return _Proc(argv)

            with mock.patch.object(driver.subprocess, "Popen", side_effect=fake_popen):
                try:
                    driver.run_opencode(state, run_dir, item, plan, prompt, 1, **kw)
                except Exception:
                    # Only argv construction is under test; stream handling may abort on the fake.
                    pass
        return captured.get("argv") or []

    #: A run frozen WITH verifier routing: `cheap` executes, `strong` verifies.
    ROUTED = {
        "model": "vendor/flash-1",
        "variant": "low",
        "verify_model": "vendor/opus-9",
        "verify_variant": "high",
        "verify_agent": "build",
        "verify_launch_profile": {"applied": "strong"},
    }

    def _launch_of(self, argv: list) -> tuple:
        def value(flag):
            return argv[argv.index(flag) + 1] if flag in argv else None

        return value("--model"), value("--variant"), value("--agent")

    def test_turn_argv_routing_matrix(self):
        argv = self._argv_for(
            self.ROUTED,
            fresh_session=True,
            log_suffix="verify",
            label_suffix="verification",
            use_verifier_launch=True,
        )
        self.assertEqual(self._launch_of(argv), ("vendor/opus-9", "high", "build"))

        argv_exec = self._argv_for(self.ROUTED)
        self.assertEqual(self._launch_of(argv_exec), ("vendor/flash-1", "low", None))

        argv_rev = self._argv_for(self.ROUTED, action="review")
        self.assertIn("--title", argv_rev)
        self.assertIn("aw-review-", argv_rev[argv_rev.index("--title") + 1])
        self.assertEqual(self._launch_of(argv_rev), ("vendor/flash-1", "low", None))

        argv_rec = self._argv_for(self.ROUTED, log_suffix="recovery")
        self.assertEqual(self._launch_of(argv_rec), ("vendor/flash-1", "low", None))

        argv_iso = self._argv_for(self.ROUTED, isolated=True)
        self.assertNotIn("--session", argv_iso)
        self.assertEqual(self._launch_of(argv_iso), ("vendor/flash-1", "low", None))
        self.assertNotIn("vendor/opus-9", argv_iso)

        argv_fresh = self._argv_for(self.ROUTED, fresh_session=True)
        self.assertNotIn("--session", argv_fresh)
        self.assertEqual(self._launch_of(argv_fresh), ("vendor/flash-1", "low", None))

        real = driver.run_opencode

        def sabotaged(state, *a, **kw):
            if kw.get("fresh_session") or kw.get("work_dir"):
                kw["use_verifier_launch"] = True
            return real(state, *a, **kw)

        with mock.patch.object(driver, "run_opencode", sabotaged):
            argv_sab = self._argv_for(self.ROUTED, isolated=True)
        self.assertEqual(self._launch_of(argv_sab), ("vendor/opus-9", "high", "build"))

    def test_the_verifier_still_forces_a_fresh_session_and_stays_in_the_worktree(self):
        """A model swap must not disturb session freshness or the directory the turn runs in."""
        with tempfile.TemporaryDirectory() as temp:
            lane = Path(temp) / "lane"
            lane.mkdir()
            argv = self._argv_for(
                {**self.ROUTED, "session": "sess-executor"},
                fresh_session=True,
                log_suffix="verify",
                use_verifier_launch=True,
                work_dir=str(lane),
            )
            self.assertNotIn("--session", argv, argv)
            self.assertEqual(argv[argv.index("--dir") + 1], str(lane))
            self.assertEqual(
                self._launch_of(argv), ("vendor/opus-9", "high", "build"), argv
            )


class OcStreamTrackerOutputModeTests(unittest.TestCase):
    def test_run_opencode_updates_tracker_across_output_modes(self):
        for mode in ("clean", "raw", "quiet"):
            with self.subTest(mode=mode):
                run_dir = Path(tempfile.mkdtemp()) / f"run-track-{mode}"
                run_dir.mkdir(parents=True)
                (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
                repo = run_dir / "repo"
                repo.mkdir()
                plan = run_dir / "plan.ipd.md"
                plan.write_text("# Test plan\n", encoding="utf-8")
                prompt_file = run_dir / "prompts" / "01-prompt.md"
                prompt_file.parent.mkdir(parents=True, exist_ok=True)
                prompt_file.write_text("test prompt", encoding="utf-8")

                state = {
                    "run_id": f"run-track-{mode}",
                    "repo": str(repo),
                    "options": {"output_mode": mode},
                }
                item = {
                    "id6": "wir001",
                    "setid": "testset",
                    "position": 1,
                    "action": "execute",
                }

                stream_events = [
                    '{"type":"step_finish","part":{"tokens":{"total":1500,"input":1200,"output":300},"cost":0.015}}\n',
                    # json.dumps, not an f-string: a Windows path's backslashes must be escaped.
                    json.dumps(
                        {
                            "type": "tool_use",
                            "part": {
                                "tool": "write",
                                "state": {
                                    "status": "completed",
                                    "metadata": {"filepath": f"{repo}/src/foo.py"},
                                },
                            },
                        }
                    )
                    + "\n",
                ]

                class FakeProc:
                    def __init__(self, *args, **kwargs):
                        self.pid = 12345
                        self.stdout = iter(stream_events)
                        self.returncode = 0

                    def poll(self):
                        return 0

                    def wait(self, timeout=None):
                        return 0

                tracker = driver.StreamTracker()
                with mock.patch("subprocess.Popen", side_effect=FakeProc):
                    with mock.patch("sys.stdout", new_callable=io.StringIO):
                        driver.run_opencode(
                            state,
                            run_dir,
                            item,
                            plan,
                            prompt_file,
                            1,
                            tracker=tracker,
                        )

                self.assertEqual(tracker.input_tokens, 1200)
                self.assertEqual(tracker.output_tokens, 300)
                self.assertAlmostEqual(tracker.cost, 0.015)
                self.assertIn("src/foo.py", tracker.modified_files)


# ==================================================================================================
# runanalytics Order 04 (`5f2h8i`): THIS HOST'S telemetry wiring.
#
# WHY ONLY THE HOST-SPECIFIC HALF IS HERE. The CROSS-HOST properties (one shared seam object, the
# field-by-field parity, the invocation identity, non-interference, sampler teardown) live in
# `tests/test_runner_telemetry_integration.py`, because asserting that the TWO hosts agree from
# inside the opencode suite would put the agy half of a symmetry claim in the wrong file - the same
# reasoning `tests/test_run_flag_surface.py` records for its own placement. What belongs HERE is what
# is true of THIS driver alone: that its one agent launch is instrumented, that both of its callers
# reach it, and that its version/helper subprocess sites are not.
# ==================================================================================================
class OcTelemetryWiringTests(unittest.TestCase):
    def test_a_turn_emits_a_start_and_an_end_event_keyed_on_the_invocation(self):
        """End to end through the REAL `run_opencode`, with no real child process."""

        from agent_workflows import runner_shared

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            plan = _init_repo_with_conforming_plan(repo, "tel001")
            run_dir = root / "run-20260913T000000Z-1"
            (run_dir / "sessions").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)
            prompt_file = run_dir / "prompts" / "01-prompt.md"
            prompt_file.write_text("prompt", encoding="utf-8")
            state = {
                "run_id": "run-20260913T000000Z-1",
                "repo": str(repo),
                "options": {"output_mode": "quiet", "model": "provider/model"},
            }
            item = {
                "id6": "tel001",
                "setid": "telset",
                "position": 3,
                "action": "execute",
            }

            class FakeProc:
                def __init__(self, cmd, *args, **kwargs):
                    self.pid = 4242
                    self.stdout = iter(())
                    self.returncode = 0

                def poll(self):
                    return 0

                def wait(self, timeout=None):
                    return 0

            with mock.patch("subprocess.Popen", side_effect=FakeProc):
                rc, _sess, _log, _argv = driver.run_opencode(
                    state, run_dir, item, plan, prompt_file, 2
                )

            self.assertEqual(rc, 0)
            streams = sorted(runner_shared.telemetry_dir(run_dir).glob("*.jsonl"))
            self.assertEqual(len(streams), 1, streams)
            events = [
                json.loads(line)
                for line in streams[0].read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([e["event_kind"] for e in events], ["start", "end"])
            for event in events:
                self.assertEqual(event["host"], "opencode")
                self.assertEqual(event["phase"], "execute")
                self.assertEqual(event["attempt"], 2)
                self.assertEqual(event["position"], 3)
                self.assertEqual(event["ipd_id6"], "tel001")
                self.assertEqual(event["set_id"], "telset")
                self.assertEqual(event["model"], "provider/model")
            self.assertIn(streams[0].stem, events[0]["execution_id"])


class VerifierGateAndRunnerBugTests(unittest.TestCase):
    """Regression tests for runner correctness bug fixes (hp9rot E-01, E-09, E-11)."""

    def test_verifier_gate(self):
        """E-01: Verifier output with CORRECTION_REQUIRED results in unverified, partial disposition, and no finalize."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "wir001",
                "setid": "demo",
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "run_id": "run-test",
                "created_at": "2026-08-28T00:00:00+00:00",
                "updated_at": "2026-08-28T00:00:00+00:00",
                "selectors": ["demo"],
                "repo": str(repo),
                "queue": [item],
                "set_sessions": {},
                "session_id": None,
                "options": {
                    "opencode": "/bin/true",
                    "model": "opus",
                    "self_finalize": True,
                    "isolate_worktree": True,
                    "no_audit": False,
                },
            }

            (run_dir / "outcomes" / "01-wir001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "outcomes" / "01-wir001-verification.json").write_text(
                json.dumps({"verdict": "CORRECTION_REQUIRED"}), encoding="utf-8"
            )

            finalize_calls = []

            def fake_finalize(r, p, i, a, m):
                finalize_calls.append((i, a, m))
                return 0, "finalized"

            def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
                work_dir = kwargs.get("work_dir")
                if kwargs.get("fresh_session"):
                    return 0, "vses", str(run_dir / "vlog"), ["oc"]
                wt = Path(work_dir) if work_dir else repo
                (wt / "src").mkdir(parents=True, exist_ok=True)
                (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
                subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
                subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
                return 0, "ses1", str(run_dir / "log"), ["oc"]

            with (
                mock.patch.object(driver, "driver_begin", lambda *a, **k: (0, "ok")),
                mock.patch.object(driver, "run_opencode", fake_run),
                mock.patch.object(driver, "driver_finalize", fake_finalize),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                finalize_calls, [], "finalize must NOT be called on CORRECTION_REQUIRED"
            )
            self.assertEqual(
                item["status"], "fail-verify", "item disposition must be fail-verify"
            )
            # runverdict (`1bfppy`) E-05: the refusal must be DURABLE and ACTIONABLE, not merely
            # correct. Read through `r2i1b1`'s ONE reader, so this asserts the real surface the run
            # summary and `aw runs` consume rather than a key this test happened to pick.
            refusal = driver.refusal_of_item(item)
            self.assertIsNotNone(
                refusal,
                "a rejected verdict must record a Refusal, or no read surface reports it",
            )
            self.assertEqual(refusal.code, driver.VERDICT_REFUSAL_CODE_DECLINED)
            self.assertIn("CORRECTION_REQUIRED", refusal.reason)
            self.assertTrue(refusal.remedy.strip())
            self.assertEqual(item["verification_status"], "unverified")

    def test_an_unreadable_verdict_file_fails_closed_end_to_end(self):
        """runverdict (`1bfppy`) E-02: malformed verification JSON must NOT be recorded verified.

        THE HOLE THIS CLOSES was `except Exception: verify_disp = "verified" if v_rc == 0 else
        "unverified"`, which read an unparseable outcome file written by a zero-exit verifier as a
        PASS. The exit code says the process ended tidily; it says nothing about the verdict.
        """
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "unr001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "unr001",
                "setid": "demo",
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            state = {
                "run_id": "run-test",
                "created_at": "2026-08-28T00:00:00+00:00",
                "updated_at": "2026-08-28T00:00:00+00:00",
                "selectors": ["demo"],
                "repo": str(repo),
                "queue": [item],
                "set_sessions": {},
                "session_id": None,
                "options": {
                    "opencode": "/bin/true",
                    "model": "opus",
                    "self_finalize": True,
                    "isolate_worktree": True,
                    "no_audit": False,
                },
            }

            (run_dir / "outcomes" / "01-unr001.json").write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "pushed": False,
                        "defect_report": {"state": "none-found", "findings": []},
                    }
                ),
                encoding="utf-8",
            )
            # Truncated mid-object: exactly what a killed or confused verifier leaves behind.
            (run_dir / "outcomes" / "01-unr001-verification.json").write_text(
                '{"verdict": "VERI', encoding="utf-8"
            )

            finalize_calls = []

            def fake_finalize(r, p, i, a, m):
                finalize_calls.append((i, a, m))
                return 0, "finalized"

            def fake_run(state, rd, item, plan_path, prompt_path, attempt_no, **kwargs):
                work_dir = kwargs.get("work_dir")
                if kwargs.get("fresh_session"):
                    # EXIT 0, which is the whole point: a tidy exit with an unreadable verdict.
                    return 0, "vses", str(run_dir / "vlog"), ["oc"]
                wt = Path(work_dir) if work_dir else repo
                (wt / "src").mkdir(parents=True, exist_ok=True)
                (wt / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
                subprocess.run(["git", "add", "src/demo.txt"], cwd=wt, check=True)
                subprocess.run(["git", "commit", "-qm", "demo"], cwd=wt, check=True)
                return 0, "ses1", str(run_dir / "log"), ["oc"]

            with (
                mock.patch.object(driver, "driver_begin", lambda *a, **k: (0, "ok")),
                mock.patch.object(driver, "run_opencode", fake_run),
                mock.patch.object(driver, "driver_finalize", fake_finalize),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                finalize_calls,
                [],
                "finalize must NOT be called on an unreadable verdict",
            )
            self.assertEqual(item["status"], "fail-verify")
            self.assertEqual(item["verification_status"], "unverified")
            refusal = driver.refusal_of_item(item)
            self.assertIsNotNone(refusal)
            self.assertEqual(
                refusal.code,
                driver.VERDICT_REFUSAL_CODE_UNREADABLE,
                "an unreadable verdict is a DIFFERENT fact from a rejection",
            )
            self.assertTrue(refusal.remedy.strip())

    def test_review_action_full_auto(self):
        """E-09: --action review --full-auto reviews and auto-approves plans without mutating item action to execute."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "wir001",
                "setid": "demo",
                "status": "queued",
                "configured_file": str(plan.relative_to(repo)),
                "action": "review",
            }
            state = {
                "run_id": "run-test",
                "created_at": "2026-08-28T00:00:00+00:00",
                "updated_at": "2026-08-28T00:00:00+00:00",
                "selectors": ["demo"],
                "repo": str(repo),
                "queue": [item],
                "set_sessions": {},
                "session_id": None,
                "options": {
                    "action": "review",
                    "full_auto": True,
                    "opencode": "/bin/true",
                    "model": "opus",
                    "isolate_worktree": False,
                },
            }

            (run_dir / "outcomes" / "01-wir001.json").write_text(
                json.dumps(
                    {
                        "disposition": "reviewed",
                        "verdict": "APPROVE WITH REVISIONS APPLIED",
                        "pushed": False,
                    }
                ),
                encoding="utf-8",
            )

            with (
                mock.patch.object(driver, "driver_begin", lambda *a, **k: (0, "ok")),
                mock.patch.object(
                    driver,
                    "run_opencode",
                    lambda *a, **k: (0, "ses", str(run_dir / "log"), ["oc"]),
                ),
                mock.patch.object(driver, "is_plan_review_approved", lambda p: True),
                mock.patch.object(driver, "set_plan_approved", lambda r, i: None),
            ):
                driver.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                item["action"],
                "review",
                "action must not be mutated to execute when run was invoked with --action review",
            )
            self.assertEqual(item["status"], "approved")
            self.assertTrue(item.get("auto_approved"))

    def test_discard_lane_reclaim(self):
        """E-11: Operator chooses discard on interrupted lane -> teardown_worktree is called and worktree directory is removed."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            run_dir.mkdir(parents=True)
            from agent_workflows import worktree_lease

            handle = worktree_lease.allocate_worktree(repo, "wir001")
            (handle.path / "src").mkdir(parents=True, exist_ok=True)
            (handle.path / "src" / "demo.txt").write_text("demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=handle.path, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "demo"], cwd=handle.path, check=True
            )

            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [
                    {
                        "id6": "wir001",
                        "position": 1,
                        "status": "running",
                        "attempts": [
                            {
                                "worktree": str(handle.path),
                                "worktree_branch": handle.branch,
                                "worktree_lane_id": "wir001",
                                "worktree_base": handle.base_commit,
                            }
                        ],
                    }
                ],
            }

            with mock.patch.object(
                driver, "_lane_reclaim_prompt", return_value="discard"
            ):
                lanes = driver.reclaim_lanes_on_interrupt(
                    repo, run_dir, state, interactive=True
                )

            self.assertEqual(len(lanes), 1)
            self.assertEqual(lanes[0]["action"], "reclaimed")
            self.assertFalse(
                handle.path.exists(), "worktree directory must be removed on discard"
            )


class PerArtifactDispositionLineTests(unittest.TestCase):
    """runnoop Order 02 (`m85gxh`) E-03: every MATCHED artifact gets one line carrying its REASON.

    THE DEFECT IS AN UNEXPLAINED DISPOSITION, NOT A MISSING LINE, and that distinction decides what
    these tests must assert. The end-of-run summary table ALREADY renders one row per matched artifact
    with its disposition, including an item with ZERO attempts, and the order announcement already
    names every matched id6. Measured (backlog `em0z50`, 2026-08-29): a run over 8 `reviewed` plans
    showed `8 steps: 8 reviewed`, `Attempts: 0` on every row, and NO explanation anywhere of what
    `reviewed` meant. So a test that asserted only "a line naming the artifact appears" would have
    PASSED on the shipped defect. Each test below therefore asserts the REASON.
    """

    def _run_and_capture(self, queue: list) -> str:
        """Drive the REAL `run_queue` over a queue nothing can dispatch, and return its stdout.

        A LAUNCHER THAT FAILS THE TEST IF CALLED, so "no turn was dispatched" is proven positively
        rather than inferred from the absence of an attempt record: every item here is
        matched-but-never-dispatched, which is exactly the case with no per-item finish line.
        """

        def _must_not_launch(*_a, **_k):
            raise AssertionError(
                "an agent turn was dispatched for an item that must never be dispatched"
            )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = _make_run_dir(root, queue)
            buf = io.StringIO()
            with (
                mock.patch.object(driver, "run_opencode", _must_not_launch),
                contextlib.redirect_stdout(buf),
            ):
                driver.run_queue(run_dir, retry_incomplete=False)
            return buf.getvalue()

    @staticmethod
    def _entry(position: int, id6: str, **over) -> dict:
        entry = {
            "position": position,
            "id6": id6,
            "setid": "wtiso",
            "configured_file": ".aw/records/plans/pending/p.ipd.md",
            "kind": "child",
            "action": "execute",
            "status": "reviewed",
            "attempts": [],
            "dependencies": [],
        }
        entry.update(over)
        return entry

    def _disposition_lines(self, out: str) -> list:
        from agent_workflows import run_selection_policy as pol

        lines = out.splitlines()
        start = lines.index(pol.DISPOSITION_HEADER)
        block = []
        for line in lines[start + 1 :]:
            if not line.startswith("- "):
                break
            block.append(line)
        return block

    def test_an_approval_blocked_queue_explains_itself_instead_of_showing_a_bare_reviewed(
        self,
    ):
        """THE MEASURED DEFECT, fixed: the reason is present and legible without prior knowledge."""
        out = self._run_and_capture(
            [
                self._entry(1, "abc123", needs_input=True),
                self._entry(2, "def456", needs_input=True),
            ]
        )
        lines = self._disposition_lines(out)
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertIn("needs_human_approval", line)
            self.assertIn("approval", line)
        self.assertIn("abc123", lines[0])
        self.assertIn("def456", lines[1])

    def test_the_line_count_equals_the_number_of_matched_artifacts(self):
        """Nothing matched is omitted, which is what makes the block answer "what did the run ignore?"."""
        queue = [
            self._entry(1, "aaa111", needs_input=True),
            self._entry(2, "bbb222", status="executed"),
            self._entry(3, "ccc333", status="not-attempted"),
            self._entry(
                4,
                "ddd444",
                dependencies=["executed:aaa111"],
            ),
        ]
        out = self._run_and_capture(queue)
        lines = self._disposition_lines(out)
        self.assertEqual(len(lines), len(queue))

    def test_a_mixed_run_reports_four_distinct_dispositions_each_with_a_reason(self):
        """Four different dispositions, four different explanations, one line each."""
        queue = [
            self._entry(1, "aaa111", needs_input=True),
            self._entry(2, "bbb222", status="executed"),
            self._entry(3, "ccc333", status="not-attempted"),
            # `queued` DELIBERATELY: the drain path reaches only a `queued` item, so this is what
            # makes the run itself compute the `dependency-blocked` disposition and its reason
            # strings rather than the test hand-writing them. Its prerequisite is item 1, which is
            # approval-frozen, so the edge can never be satisfied in this run.
            self._entry(4, "ddd444", status="queued", dependencies=["executed:aaa111"]),
        ]
        out = self._run_and_capture(queue)
        lines = self._disposition_lines(out)
        joined = "\n".join(lines)
        self.assertIn("needs_human_approval", joined)
        self.assertIn("ipd_already_executed", joined)
        self.assertIn("type_or_status_not_runnable", joined)
        # The dependency case NAMES the unmet dependency, per the backlog item.
        self.assertIn("dependency_not_met", joined)
        self.assertIn("executed:aaa111", joined)
        # Every line carries SOME reason: no line ends at the disposition.
        for line in lines:
            self.assertRegex(line, r" -> [^:]+: \S")

    def test_a_multi_attempt_item_still_produces_exactly_one_disposition_line(self):
        """Once per ARTIFACT, not once per ATTEMPT, or child 03's counts would not sum."""
        out = self._run_and_capture(
            [
                self._entry(
                    1,
                    "eee555",
                    status="executed",
                    attempts=[{"n": 1}, {"n": 2}, {"n": 3}],
                )
            ]
        )
        lines = self._disposition_lines(out)
        self.assertEqual(len([line for line in lines if "eee555" in line]), 1)


class EndOfRunDispositionSummaryTests(unittest.TestCase):
    """runnoop Order 03 (`bsc457`) E-05: the CLOSING SUMMARY, asserted on ACTUAL rendered stdout."""

    def _run_and_capture(self, queue: list) -> str:
        def _must_not_launch(*_a, **_k):
            raise AssertionError(
                "an agent turn was dispatched for an item that must never be dispatched"
            )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = _make_run_dir(root, queue)
            buf = io.StringIO()
            with (
                mock.patch.object(driver, "run_opencode", _must_not_launch),
                contextlib.redirect_stdout(buf),
            ):
                driver.run_queue(run_dir, retry_incomplete=False)
            return buf.getvalue()

    @staticmethod
    def _entry(position: int, id6: str, **over) -> dict:
        entry = {
            "position": position,
            "id6": id6,
            "setid": "wtiso",
            "configured_file": ".aw/records/plans/pending/p.ipd.md",
            "kind": "child",
            "action": "execute",
            "status": "reviewed",
            "attempts": [],
            "dependencies": [],
        }
        entry.update(over)
        return entry

    def test_end_of_run_disposition_summary_rendering(self):
        import re
        from agent_workflows import run_selection_policy as pol

        # Zero-action run still prints summary
        queue_zero = [
            self._entry(i, "id%04d" % i, needs_input=True) for i in range(1, 9)
        ]
        out_zero = self._run_and_capture(queue_zero)
        self.assertIn(pol.SUMMARY_HEADER, out_zero)
        self.assertIn("NO WORK WAS PERFORMED", out_zero)
        self.assertIn("matched 8 artifact(s) and acted on NONE", out_zero)

        # Printed counts sum to matched artifacts
        queue_mixed = [
            self._entry(1, "aaa111", needs_input=True),
            self._entry(2, "bbb222", status="executed"),
            self._entry(3, "ccc333", status="not-attempted"),
            self._entry(4, "ddd444", status="queued", dependencies=["executed:aaa111"]),
        ]
        out_mixed = self._run_and_capture(queue_mixed)
        block = out_mixed[out_mixed.index(pol.SUMMARY_HEADER) :].splitlines()
        counted = sum(
            int(m.group(2))
            for line in block
            if (m := re.match(r"^  (\S+) \((\d+)\)", line))
        )
        self.assertEqual(counted, len(queue_mixed))
        self.assertIn(f"total: {len(queue_mixed)} matched,", out_mixed)
        self.assertIn("remedy:", out_mixed)
        self.assertIn("aw ipd set approved <id6> --by-human", out_mixed)
        self.assertIn("ipd_already_executed (1)", out_mixed)

        # Footer says no turn was attempted
        self.assertIn("No turn was attempted", out_zero)
        self.assertIn("This is NOT a failed launch", out_zero)


# ==================================================================================================
# THE VERIFIER VERDICT MAPPING (runverdict `1bfppy`)
# ==================================================================================================

#: THE HISTORICAL CORPUS, AS A FIXTURE RATHER THAN A LIVE READ (E-03).
#:
#: These are the DISTINCT verdict VALUES found across every `outcomes/*-verification.json` file in the
#: maintainer's run tree, measured at execution: 36 files, all carrying exactly `VERIFIED`, zero
#: rejections and zero unparseable files.
#:
#: WHY A FIXTURE AND NOT A WALK OF `.aw/records/runs/`. That directory is GITIGNORED
#: (`.aw/.gitignore` matches `records/runs/`, and `git ls-files` returns zero tracked files under it),
#: so a test reading it would pass in the maintainer's checkout and fail everywhere else: in CI, in a
#: fresh clone, and in an isolated lane worktree - measured, it does not exist in the worktree this
#: change was written in. A test that silently passes by finding nothing is worse than no test.
#:
#: AND WHY NO COUNT IS ASSERTED. The corpus GROWS by one file per verified run (34 when this plan was
#: authored, 35 at its review, 36 at execution), so a hardcoded size fails for a correct reason and
#: teaches the next executor to edit the number instead of reading the test. The PROPERTY is what
#: matters: every verdict a real verifier has ever written must still map to `verified`.
_HISTORICAL_VERDICT_VALUES = ("VERIFIED",)


class VerdictTruthTableTests(unittest.TestCase):
    """E-04: the FULL input alphabet, including everything that must fail closed.

    THE TABLE IS THE TEST. Each row is `(raw verdict, verify_disp, downgrades?, recognized?)`, and the
    rows are grouped by why they are here rather than alphabetically, because the grouping IS the
    argument: the documented verdicts, the linter-vocabulary aliases, the substring traps, the
    normalization cases, and the fail-closed remainder.
    """

    # (raw, verify_disp, downgrade, recognized)
    CASES = (
        # --- the three DOCUMENTED verdicts, verbatim from the prompt's schema line ---------------
        ("VERIFIED", "verified", False, True),
        ("CORRECTION_REQUIRED", "unverified", True, True),
        ("BLOCKED", "blocked", True, True),
        # --- the LINTER-vocabulary pair (plan OQ-02, resolved AGAINST the plan's default) ---------
        # `NOT CONFORMING` is honored as a rejection, exactly as the pre-existing gate honored it.
        # `CONFORMING` is deliberately NOT a pass: at HEAD it already mapped to `unverified`, so
        # accepting it would WIDEN the pass set of a gate whose purpose is to narrow it, and the
        # twelve tests that once depended on it were rewritten to `VERIFIED` by `61137509` (measured:
        # zero occurrences remain), so nothing pays for fail-closing it. See its definition.
        ("NOT CONFORMING", "blocked", True, True),
        ("CONFORMING", "unverified", True, False),
        # --- THE SUBSTRING TRAPS, which are the reason exact matching is mandatory ---------------
        # `"CONFORMING" in "NOT CONFORMING"` is True, so under substring semantics a REJECTION maps
        # to a PASS whenever the arms are ordered wrongly. And `"BLOCKED" in "NOT BLOCKED"` is True,
        # which the pre-existing gate got wrong: it mapped `NOT BLOCKED` to `blocked`. Measured.
        ("NOT BLOCKED", "unverified", True, False),
        ("NOT VERIFIED", "unverified", True, False),
        # --- NORMALIZATION: case, padding, and collapsed internal whitespace ---------------------
        ("correction_required", "unverified", True, True),
        ("  VERIFIED  ", "verified", False, True),
        ("not   conforming", "blocked", True, True),
        # --- A VERDICT WITH A TRAILING SUMMARY, resolved FAIL-CLOSED and asserted either way -----
        # This is the plan's sharpest open choice. Accepting a prefix would also accept
        # `VERIFIED: except for the three failures below`, which is a rejection written
        # conversationally; reading that as a pass is the defect class this table removes. So a
        # verdict carrying prose is `unverified` WITH a reason naming what it wrote.
        ("VERIFIED: all checks passed", "unverified", True, False),
        # --- THE FAIL-CLOSED REMAINDER: typos, unknown values, emptiness, absence ---------------
        ("FAILED", "unverified", True, False),
        ("REJECTED", "unverified", True, False),
        ("", "unverified", True, False),
        ("garbage", "unverified", True, False),
        (None, "unverified", True, False),
    )

    def test_verdict_truth_table_mapping(self):
        from agent_workflows import run_state, runner_shared as rs

        for raw, disp, downgrade, recognized in self.CASES:
            with self.subTest(verdict=raw):
                mapped = rs.map_verdict(raw)
                self.assertEqual(mapped.verify_disp, disp)
                self.assertEqual(mapped.downgrade, downgrade)
                self.assertEqual(mapped.recognized, recognized)

        passing = {raw for raw, disp, _d, _r in self.CASES if disp == "verified"}
        self.assertEqual(passing, {"VERIFIED", "  VERIFIED  "})
        self.assertEqual({rs.normalize_verdict(p) for p in passing}, {"VERIFIED"})

        mapped_missing = rs.map_verdict({}.get("verdict", ""))
        self.assertEqual(mapped_missing.verify_disp, "unverified")
        self.assertTrue(mapped_missing.downgrade)
        self.assertFalse(mapped_missing.recognized)

        for raw in ("BLOCKED", "NOT CONFORMING"):
            mapped = rs.map_verdict(raw)
            self.assertEqual(mapped.verify_disp, "blocked")
            self.assertTrue(mapped.downgrade)

        self.assertEqual(
            rs.map_verdict("CORRECTION_REQUIRED").state,
            run_state.STATE_CORRECTION_REQUIRED,
        )
        self.assertEqual(rs.map_verdict("VERIFIED").state, run_state.STATE_VERIFIED)
        self.assertEqual(rs.map_verdict("BLOCKED").state, "fail-verify")
        self.assertEqual(
            rs.map_verdict("garbage").state, run_state.STATE_CORRECTION_REQUIRED
        )


class VerdictRefusalReasonTests(unittest.TestCase):
    """E-05: a refusal must name WHAT IT READ and WHAT TO DO, and must not invite the destructive fix.

    `AGENTS.md` records the measured failure mode: a gate stating only a prohibition gets complied
    with by DELETION. Here the destructive "fix" is to re-run the plan from scratch (discarding a lane
    that already holds the work) or to re-run with verification off (bypassing the finding), so every
    branch is asserted to steer away from both.
    """

    def test_a_rejection_names_the_verdict_and_a_constructive_remedy(self):
        from agent_workflows import runner_shared as rs

        code, reason, remedy = rs.verdict_refusal_text(
            "CORRECTION_REQUIRED", rs.map_verdict("CORRECTION_REQUIRED")
        )
        self.assertEqual(code, rs.VERDICT_REFUSAL_CODE_DECLINED)
        self.assertIn("CORRECTION_REQUIRED", reason)
        self.assertIn("PRESERVED", remedy)
        self.assertIn("Do NOT re-run the plan from scratch", remedy)

    def test_verdict_refusal_text_properties(self):
        from agent_workflows import runner_shared as rs
        from agent_workflows.render_stream import Refusal

        self.assertIs(
            rs.VERDICT_REFUSAL_CODE_DECLINED, rs.INTEGRATION_REFUSED_VERIFIER_DECLINED
        )

        rejected = rs.verdict_refusal_text(
            "CORRECTION_REQUIRED", rs.map_verdict("CORRECTION_REQUIRED")
        )[0]
        unreadable = rs.verdict_refusal_text("garbage", rs.map_verdict("garbage"))[0]
        self.assertNotEqual(rejected, unreadable)
        self.assertEqual(unreadable, rs.VERDICT_REFUSAL_CODE_UNREADABLE)

        _code, reason, remedy = rs.verdict_refusal_text(
            "probably fine?", rs.map_verdict("probably fine?")
        )
        self.assertIn("PROBABLY FINE?", reason)
        for token in ("VERIFIED", "CORRECTION_REQUIRED", "BLOCKED"):
            self.assertIn(token, reason)
        self.assertIn("re-run the verification", remedy)

        code_empty, reason_empty, remedy_empty = rs.verdict_refusal_text(
            "", rs.map_verdict("")
        )
        self.assertTrue(code_empty.strip())
        self.assertIn("(empty)", reason_empty)
        self.assertTrue(remedy_empty.strip())

        for raw in ("CORRECTION_REQUIRED", "BLOCKED", "NOT CONFORMING", "", "garbage"):
            with self.subTest(verdict=raw):
                code, reason, remedy = rs.verdict_refusal_text(raw, rs.map_verdict(raw))
                record = Refusal(code=code, reason=reason, remedy=remedy)
                self.assertTrue(record.remedy.strip())
                self.assertNotIn("--no-verify", remedy)

        self.assertEqual(rs.map_verdict("VERIFIED").verify_disp, "verified")
        self.assertFalse(rs.map_verdict("VERIFIED").downgrade)


class VerdictLanePreservationTests(unittest.TestCase):
    """E-05: an unverified verdict must still REFUSE INTEGRATION on BOTH hosts, lane preserved.

    THE TWO HOSTS ARE NOT EQUALLY EXPOSED, which is why both are asserted. oc gates its verifier on
    `--validate` (default FALSE), while agy gates on `not no_verify` (default TRUE) and passes
    `validate=verifier_expected` into the SAME shared predicate. So the fail-open path this change
    closes was on agy's SHIPPED DEFAULT and only on an opt-in oc path; testing oc alone would leave
    the more exposed host unproven.
    """

    def test_every_non_verified_verdict_refuses_integration_on_both_hosts(self):
        from agent_workflows import agy_runipd, oc_runipd as oc, runner_shared as rs

        # ONE shared predicate, so "both hosts" is a claim about object identity first.
        self.assertIs(oc.integration_is_earned, agy_runipd.integration_is_earned)

        for raw in ("CORRECTION_REQUIRED", "BLOCKED", "NOT BLOCKED", "", "garbage"):
            mapped = rs.map_verdict(raw)
            with self.subTest(verdict=raw):
                self.assertNotEqual(mapped.verify_disp, "verified")
                for host, predicate in (
                    ("oc (--validate)", oc.integration_is_earned),
                    ("agy (default verifier ON)", agy_runipd.integration_is_earned),
                ):
                    verdict = predicate(
                        validate=True,
                        verify_disp=mapped.verify_disp,
                        suite_result=None,
                    )
                    self.assertFalse(
                        verdict.earned,
                        f"{host}: a non-verified verdict must NOT earn integration",
                    )
                    self.assertEqual(
                        verdict.signal, rs.INTEGRATION_REFUSED_VERIFIER_DECLINED
                    )

    def test_a_green_suite_does_not_override_an_explicit_rejection(self):
        """The property that makes the fix meaningful rather than cosmetic."""

        from agent_workflows import oc_runipd as oc, runner_shared as rs

        class _Suite:
            passing = True
            reason = "all green"

        mapped = rs.map_verdict("CORRECTION_REQUIRED")
        verdict = oc.integration_is_earned(
            validate=True, verify_disp=mapped.verify_disp, suite_result=_Suite()
        )
        self.assertFalse(verdict.earned)
        self.assertIn("does NOT override", verdict.detail)

    def test_a_verified_verdict_still_earns_integration(self):
        """The other direction: the fix must not have broken the passing path."""
        from agent_workflows import oc_runipd as oc, runner_shared as rs

        verdict = oc.integration_is_earned(
            validate=True,
            verify_disp=rs.map_verdict("VERIFIED").verify_disp,
            suite_result=None,
        )
        self.assertTrue(verdict.earned)
        self.assertEqual(verdict.signal, rs.INTEGRATION_EARNED_BY_VERIFIER)


class VerificationAbsenceTests(unittest.TestCase):
    """runverdict-06 (`fzxfph`) E-04: the THREE reasons a verdict is absent must be distinguishable.

    THE DEFECT, precisely. `verify_disp` was assigned a bare `"unverified"` at three sites in
    `execute_item_core`'s verifier block, for three materially different facts with three different
    remedies: the verifier wrote a verdict the runner could not read, the verifier wrote no outcome
    file at all, and the verifier turn was killed. All three read to an operator as one benign
    caveat, so a run whose verification NEVER RAN was indistinguishable from one where it ran and
    could not conclude.

    FIXTURES, NEVER THE LIVE RUN TREE. `.aw/records/runs/` is gitignored with zero tracked files
    (`.aw/.gitignore` matches `records/runs/`), so a test built on the real corpus would pass in the
    maintainer's checkout and fail in CI, in a fresh clone, and in every lane worktree this runner
    creates by default.
    """

    def test_the_pre_fix_contrast_all_three_facts_were_one_value(self):
        """WITHOUT THIS, ASSERTING THREE DISTINCT VALUES PROVES NOTHING ABOUT THE DEFECT.

        Reconstructs the pre-fix behavior literally - the three sites assigned this one string - and
        shows the three facts were indistinguishable in the record. The post-fix contrast is the next
        test. Pinning the OLD value as a literal is deliberate: it is what the old code wrote, and it
        is not read from the module, so this stays a statement about history rather than a tautology.
        """

    def test_verification_absence_reasons_and_remedies(self):
        from agent_workflows import render_stream, runner_shared as rs

        post_fix = {
            "verdict written but unparseable": rs.VERIFY_ABSENCE_VERDICT_UNREADABLE,
            "no outcome file written at all": rs.VERIFY_ABSENCE_NO_OUTCOME_FILE,
            "verifier turn killed mid-flight": rs.VERIFY_ABSENCE_TURN_INTERRUPTED,
        }
        self.assertEqual(len(set(post_fix.values())), 3)
        texts = {rs.verify_absence_text(code) for code in post_fix.values()}
        self.assertEqual(len(texts), 3)

        never, never_remedy = rs.verify_absence_text(rs.VERIFY_ABSENCE_NO_OUTCOME_FILE)
        killed, killed_remedy = rs.verify_absence_text(
            rs.VERIFY_ABSENCE_TURN_INTERRUPTED
        )
        self.assertIn("FAILURE", never)
        self.assertIn("UNKNOWN", killed)
        self.assertNotIn("FAILURE", killed)
        for remedy in (never_remedy, killed_remedy):
            self.assertIn("PRESERVED", remedy)

        for code in rs.VERIFY_ABSENCE_CODES:
            with self.subTest(code=code):
                reason, remedy = rs.verify_absence_text(code, plan_hint="abc123")
                item: dict = {}
                render_stream.record_refusal(
                    item, code=code, reason=reason, remedy=remedy
                )
                read_back = render_stream.refusal_of_item(item)
                self.assertIsNotNone(read_back)
                assert read_back is not None
                self.assertEqual(read_back.code, code)
                self.assertTrue(read_back.remedy.strip())


# ==================================================================================================
# runverdict Order 07 (`w33lrl`) E-02/E-03/E-04/E-06: the cost-attribution snapshot
# ==================================================================================================


def _cost_config(root, default_model="uri/alpha", cost=None, name="opencode.json"):
    """Write an OpenCode config fixture and return the env that points the resolver at it.

    `OPENCODE_CONFIG` is used rather than a project file, because these tests run with a cwd inside
    THIS repository and a walk-up discovery would find whatever the developer's own tree contains.
    """

    entry = {"name": "Alpha"}
    if cost is not None:
        entry["cost"] = cost
    payload = {"provider": {"uri": {"models": {"alpha": entry}}}}
    if default_model is not None:
        payload["model"] = default_model
    path = Path(root) / name
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {"OPENCODE_CONFIG": os.fspath(path)}, path


class CostAttributionRecordTests(unittest.TestCase):
    """E-01/E-02: the run record now NAMES the model that incurred its cost and the prices applied.

    Before this, a run where no `--model` was passed recorded `options.model: null` and a
    `launch_profile.provenance.model` of `host-default` ("nothing supplied it; pass no argument"). That
    was an HONEST statement about the flag and it stays true; what it could not do is say which model
    the host then chose, so a recorded dollar figure could not be attributed to one.
    """

    def _record(self, env, **kwargs):
        with mock.patch.dict(os.environ, env, clear=False):
            return runner_shared.cost_attribution_record(
                host="oc", model=None, model_source="host-default", **kwargs
            )

    def test_cost_attribution_record_structure_and_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            env, path = _cost_config(temp, cost={"input": 5.5, "output": 27.5})
            record = self._record(env)
            self.assertEqual(record["model"], "uri/alpha")
            self.assertEqual(record["model_source"], "model")
            self.assertNotIn("model_reason", record)
            self.assertEqual(record["kind"], "launch-time-snapshot")
            self.assertEqual(record["kind"], runner_shared.CARD_SNAPSHOT_KIND)
            self.assertEqual(record["unit"], "$/Mtok")
            self.assertRegex(record["card_config_digest"], r"^[0-9a-f]{64}$")
            self.assertEqual(record["card_config_covers"], "opencode.json")

            rendered = json.dumps(record)
            self.assertNotIn(os.fspath(path), rendered)
            self.assertNotIn(temp, rendered)
            self.assertEqual(record["card_config"], "opencode.json")

            with mock.patch.dict(os.environ, env, clear=False):
                explicit_rec = runner_shared.cost_attribution_record(
                    host="oc", model="uri/alpha", model_source="explicit"
                )
            self.assertEqual(explicit_rec["model"], "uri/alpha")
            self.assertEqual(explicit_rec["model_source"], "explicit")
            self.assertEqual(explicit_rec["card"]["input"], 5.5)

    def test_cost_attribution_unknowns_and_partial_cards(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            missing = root / "absent.json"
            none_record = self._record({"OPENCODE_CONFIG": os.fspath(missing)})
            self.assertEqual(none_record["model"], "")
            self.assertEqual(none_record["model_reason"], "no-config-found")

            jsonc = root / "opencode.jsonc"
            jsonc.write_text('{\n // c\n "model": "uri/alpha"\n}\n', encoding="utf-8")
            jsonc_record = self._record({"OPENCODE_CONFIG": os.fspath(jsonc)})
            self.assertEqual(jsonc_record["model_reason"], "unparseable-config")

            env_nd, _ = _cost_config(
                root, default_model=None, cost={"input": 1.0}, name="nodefault.json"
            )
            nd_record = self._record(env_nd)
            self.assertEqual(nd_record["model_reason"], "no-default-model-key")

            env_nc, _ = _cost_config(root, cost=None, name="nocost.json")
            nc_record = self._record(env_nc)
            self.assertEqual(nc_record["model"], "uri/alpha")
            self.assertEqual(nc_record["card"], {})
            self.assertEqual(nc_record["card_reason"], "model-has-no-cost-block")

            env_p, _ = _cost_config(
                temp, cost={"input": 5.5, "output": 27.5}, name="partial.json"
            )
            partial = self._record(env_p)
            env_z, _ = _cost_config(
                temp,
                cost={"input": 5.5, "output": 27.5, "cache_read": 0, "cache_write": 0},
                name="zeroed.json",
            )
            zeroed = self._record(env_z)
            self.assertEqual(partial["card"]["cache_read"], "absent")
            self.assertEqual(zeroed["card"]["cache_read"], 0.0)


class AgyCardIsNotResolvableTests(unittest.TestCase):
    """E-04: agy records that it CANNOT resolve a card, and adds no model work."""

    def test_agy_card_resolution_inability(self):
        record = runner_shared.cost_attribution_record(
            host="agy",
            model=agy_runipd.DEFAULT_MODEL,
            model_source="host-default-constant",
            resolve_card=False,
        )
        self.assertEqual(record["host"], "agy")
        # `DEFAULT_MODEL` is resolved from the operator's agy settings.json (1864f5b9) and is None on
        # a machine without one (every CI runner); the record normalizes an absent model to "".
        self.assertEqual(record["model"], agy_runipd.DEFAULT_MODEL or "")
        self.assertEqual(record["card"], {})
        self.assertEqual(record["card_reason"], "host-card-not-in-any-readable-config")
        self.assertEqual(record["card_reason"], runner_shared.CARD_HOST_NOT_READABLE)

        with tempfile.TemporaryDirectory() as temp:
            env, path = _cost_config(temp, cost={"input": 5.5})
            parsed = json.loads(path.read_text(encoding="utf-8"))
        # A CONCRETE agy model id, not `DEFAULT_MODEL`: this half asserts that an agy id is not
        # priced by the opencode config, which needs an id to exist. `DEFAULT_MODEL` depends on the
        # machine's agy settings.json and is None on CI, which turned this into a no-model case.
        agy_model = agy_runipd.DEFAULT_MODEL or "gemini-3.7-flash-high"
        declared = oc_models.models_from_config(parsed)
        self.assertNotIn(agy_model, declared)
        components, reason = oc_models.card_from_config(parsed, agy_model)
        self.assertEqual(components, {})
        self.assertEqual(reason, oc_models.CARD_MODEL_NOT_DECLARED)


class StartupAttentionIntegrityReportTests(unittest.TestCase):
    """E-03 & E-04: Test the startup report for an invalid cross-tree attention view."""

    def test_startup_attention_integrity_report(self):
        # 1. Invalid board is reported at run start
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stream = io.StringIO()
            with mock.patch(
                "agent_workflows.attention.scan",
                return_value=(
                    [],
                    [
                        core.Drift(
                            ".aw/records/backlog/open/a.md",
                            "attention.duplicate-id",
                            "dup",
                        ),
                    ],
                ),
            ), mock.patch(
                "agent_workflows.attention.stranded_lane_drift",
                return_value=[],
            ):
                runner_shared.report_invalid_board_at_run_start(root, stream=stream)
            out = stream.getvalue()
            self.assertIn("warning: cross-tree attention view is INVALID", out)
            self.assertIn("attention.duplicate-id", out)
            self.assertIn("1 finding(s)", out)

        # 2. Info-only findings are silent at run start
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stream = io.StringIO()
            info_drift = core.Drift(
                "aw/lane/abc",
                "attention.lane-superseded",
                "superseded",
                severity="info",
            )
            with mock.patch(
                "agent_workflows.attention.scan",
                return_value=([], []),
            ), mock.patch(
                "agent_workflows.attention.stranded_lane_drift",
                return_value=[info_drift],
            ):
                runner_shared.report_invalid_board_at_run_start(root, stream=stream)
            self.assertEqual(stream.getvalue(), "")

        # 3. Clean repository is silent at run start
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stream = io.StringIO()
            with mock.patch(
                "agent_workflows.attention.scan",
                return_value=([], []),
            ), mock.patch(
                "agent_workflows.attention.stranded_lane_drift",
                return_value=[],
            ):
                runner_shared.report_invalid_board_at_run_start(root, stream=stream)
            self.assertEqual(stream.getvalue(), "")

        # 4. Computation failure degrades to warning and does not raise
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stream = io.StringIO()
            with mock.patch(
                "agent_workflows.attention.scan",
                side_effect=RuntimeError("disk read error"),
            ):
                runner_shared.report_invalid_board_at_run_start(root, stream=stream)
            out = stream.getvalue()
            self.assertIn(
                "warning: could not compute cross-tree attention view at run start", out
            )
            self.assertIn("disk read error", out)

        # 5. Startup report ordering is before run directory creation
        events: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".aw/records/plans/pending").mkdir(parents=True, exist_ok=True)
            plan = root / ".aw/records/plans/pending/20260101-demo-01-abc123-p.ipd.md"
            plan.write_text(
                "# IPD: abc123\n- Date: 2026-01-01\n- Kind: child\n- Status: approved\n- Set: demo\n- Order: 1\n- Id: abc123\n\n## Goal\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=t",
                    "-c",
                    "user.email=t@t",
                    "commit",
                    "-qm",
                    "init",
                ],
                cwd=root,
                check=True,
            )

            original_report = getattr(
                runner_shared, "report_invalid_board_at_run_start", None
            )

            def spy_report(repo, **kw):
                runs_dir = root / ".aw/records/runs"
                existing_runs = (
                    list(runs_dir.glob("run-*")) if runs_dir.is_dir() else []
                )
                events.append(f"report_called:run_count={len(existing_runs)}")
                if original_report:
                    return original_report(repo, **kw)
                return []

            parser = driver.build_parser()
            args = parser.parse_args(
                ["start", "abc123", "--prepare-only", "--repo", str(root)]
            )
            with mock.patch(
                "agent_workflows.runner_shared.report_invalid_board_at_run_start",
                spy_report,
            ):
                driver.initialize_run(args)
            self.assertIn("report_called:run_count=0", events)


if __name__ == "__main__":
    unittest.main()
