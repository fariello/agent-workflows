#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock
from pathlib import Path

from agent_workflows import oc_runipd as driver
from agent_workflows import runner_stop
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
                json.dumps({"disposition": "executed", "pushed": False}),
                encoding="utf-8",
            )
            item = {
                "position": 1,
                "id6": "aaaaaa",
                "configured_file": str(plan.relative_to(repo)),
                "action": "execute",
            }
            disposition, _ = driver.reconcile_disposition(repo, item, run_dir, 0)
            self.assertEqual(disposition, "substantially-complete")

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
            fake = root / "opencode"
            fake.write_text(
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
                    executed=pathlib.Path(str(plan).replace('/pending/', '/executed/'))
                    executed.parent.mkdir(parents=True, exist_ok=True)
                    plan.rename(executed)
                    id6=re.search(r'Assigned IPD: ([a-z0-9]{6})', prompt).group(1)
                    outcome.write_text(json.dumps({'schema_version':1,'id6':id6,'disposition':'executed','pushed':False}))
                    print(json.dumps({'type':'text','sessionID':session,'part':{'text':'done'}}))
                    """
                ),
                encoding="utf-8",
            )
            fake.chmod(0o755)
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

            fake = root / "fake_opencode"
            fake.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json, pathlib, sys
                    args = sys.argv[1:]
                    prompt = args[args.index('--') + 1] if '--' in args else ""
                    session = args[args.index('--session') + 1] if '--session' in args else ("ses" + "_" + "firstreview")

                    # Verify review slash command format
                    if prompt.startswith("/plan-review"):
                        target_file = prompt.split()[-1]
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
                encoding="utf-8",
            )
            fake.chmod(0o755)

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
                    return -signal.SIGKILL
                return None

            def wait(self, timeout=None):
                if len(signals_sent) < 3:
                    raise subprocess.TimeoutExpired(["dummy"], timeout)
                return -signal.SIGKILL

            def send_signal(self, sig):
                signals_sent.append(("single", sig))

            def kill(self):
                signals_sent.append(("kill", signal.SIGKILL))

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
                    ("group", 9999, signal.SIGKILL),
                ],
            )
            self.assertTrue(proc.stdout.closed)
        finally:
            driver._SIGINT_GRACE_SECONDS = orig_sigint_grace
            driver._SIGTERM_GRACE_SECONDS = orig_sigterm_grace
            if orig_killpg is not None:
                os.killpg = orig_killpg
            if orig_getpgid is not None:
                os.getpgid = orig_getpgid
            if orig_getpgrp is not None:
                os.getpgrp = orig_getpgrp

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
                    return -signal.SIGKILL
                return None

            def wait(self, timeout=None):
                if len(signals_sent) < 3:
                    raise subprocess.TimeoutExpired(["dummy"], timeout)
                return -signal.SIGKILL

            def send_signal(self, sig):
                signals_sent.append(("single", sig))

            def kill(self):
                signals_sent.append(("kill", signal.SIGKILL))

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
                    ("single", signal.SIGKILL),
                ],
            )
            self.assertTrue(proc.stdout.closed)
        finally:
            driver._SIGINT_GRACE_SECONDS = orig_sigint_grace
            driver._SIGTERM_GRACE_SECONDS = orig_sigterm_grace
            if orig_killpg is not None:
                os.killpg = orig_killpg


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

            silent_child = root / "silent_opencode"
            silent_child.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import time
                    time.sleep(60)
                    """
                ),
                encoding="utf-8",
            )
            silent_child.chmod(0o755)

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

            active_child = root / "active_opencode"
            active_child.write_text(
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
                encoding="utf-8",
            )
            active_child.chmod(0o755)

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
                    # Full Auto Plan

                    ## Workflow history
                    - 2026-08-24 created: test stub
                    """
                ),
                encoding="utf-8",
            )

            fake = root / "fake_opencode"
            history_line = repr(
                "\n- 2026-08-24 /plan-review (opencode): APPROVE; no defects. Readiness: GO - PENDING HUMAN APPROVAL.\n"
            )
            fake_lines = [
                "#!/usr/bin/env python3",
                "import json, pathlib, re, sys",
                "args = sys.argv[1:]",
                'prompt = args[args.index("--") + 1] if "--" in args else ""',
                'session = args[args.index("--session") + 1] if "--session" in args else ("ses_" + "fullauto")',
                'if prompt.startswith("/plan-review"):',
                "    target_file = prompt.split()[-1]",
                "    p = pathlib.Path(target_file)",
                "    if not p.is_absolute():",
                "        p = pathlib.Path.cwd() / p",
                "    if p.is_file():",
                "        content = p.read_text()",
                '        content = content.replace("- Status: to-review", "- Status: reviewed")',
                f"        content += {history_line}",
                "        p.write_text(content)",
                '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "review done"}}))',
                'elif "Required JSON outcome:" in prompt:',
                '    outcome = pathlib.Path(re.search(r"Required JSON outcome: (.+)", prompt).group(1).strip())',
                '    plan = pathlib.Path(re.search(r"Plan file at launch: (.+)", prompt).group(1).strip())',
                '    executed = pathlib.Path(str(plan).replace("/pending/", "/executed/"))',
                "    executed.parent.mkdir(parents=True, exist_ok=True)",
                "    plan.rename(executed)",
                '    outcome.write_text(json.dumps({"schema_version": 1, "id6": "fa0001", "disposition": "executed", "pushed": False}))',
                '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "exec done"}}))',
                "else:",
                '    print(json.dumps({"type": "text", "sessionID": session, "part": {"text": "verify done"}}))',
            ]
            fake.write_text("\n".join(fake_lines) + "\n", encoding="utf-8")
            fake.chmod(0o755)

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

            fake = root / "fake_opencode"
            fake.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json, pathlib, re, sys
                    args = sys.argv[1:]
                    prompt = args[args.index('--') + 1] if '--' in args else ""
                    session = args[args.index('--session') + 1] if '--session' in args else ("ses" + "_" + "nofa")

                    if prompt.startswith("/plan-review"):
                        target_file = prompt.split()[-1]
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
                encoding="utf-8",
            )
            fake.chmod(0o755)

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
        state = {
            "repo": "/nonexistent",
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
        # Bracketed YAML array
        text1 = '- Dependencies: [5ahblp, pr2nd0]\n- Set: "my-set" (descriptive)'
        self.assertEqual(driver._read_deps(text1), ["5ahblp", "pr2nd0"])
        self.assertEqual(driver._read_set(text1), "my-set")

        # Quoted YAML array
        text2 = "- Depends-on: ['5ahblp', 'pr2nd0']\n- Set: 'custom-set'"
        self.assertEqual(driver._read_deps(text2), ["5ahblp", "pr2nd0"])
        self.assertEqual(driver._read_set(text2), "custom-set")

        # Inline notes / parentheticals
        text3 = "- Dependencies: 5ahblp (first step), pr2nd0 (second step)"
        self.assertEqual(driver._read_deps(text3), ["5ahblp", "pr2nd0"])

        # None / empty / n/a
        self.assertEqual(driver._read_deps("- Dependencies: None"), [])
        self.assertEqual(driver._read_deps("- Dependencies: none."), [])
        self.assertEqual(driver._read_deps("- Dependencies: n/a"), [])
        self.assertEqual(driver._read_deps("- Dependencies: "), [])

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

    def test_no_sessions_captured_success(self):
        hint = driver.render_continuation_hint(self._state({}), Path("/x"))
        self.assertIn("No OpenCode session was captured", hint)
        self.assertNotIn("ses_", hint)
        self.assertIn("aw runs run-xyz", hint)
        self.assertNotIn("resume", hint)

    def test_no_sessions_captured_incomplete(self):
        hint = driver.render_continuation_hint(
            self._state({}, queue=[{"status": "failed"}]), Path("/x")
        )
        self.assertIn("No OpenCode session was captured", hint)
        self.assertIn("aw oc run resume --repo /repo run-xyz", hint)
        self.assertNotIn("aw runs", hint)

    def test_single_session_success(self):
        hint = driver.render_continuation_hint(
            self._state({"demo": "ses_abc123"}, queue=[{"status": "reviewed"}]),
            Path("/x"),
        )
        self.assertIn("ses_abc123", hint)
        self.assertIn("aw oc run --session ses_abc123 <selector>", hint)
        self.assertIn("aw runs run-xyz", hint)
        self.assertNotIn("resume", hint)

    def test_single_session_incomplete(self):
        hint = driver.render_continuation_hint(
            self._state({"demo": "ses_abc123"}, queue=[{"status": "partial"}]),
            Path("/x"),
        )
        self.assertIn("ses_abc123", hint)
        self.assertIn("aw oc run --session ses_abc123 <selector>", hint)
        self.assertIn("aw oc run resume --repo /repo run-xyz", hint)
        self.assertNotIn("aw runs", hint)

    def test_multiple_sessions_lists_each_and_uses_last(self):
        hint = driver.render_continuation_hint(
            self._state({"setA": "ses_aaa", "setB": "ses_bbb"}), Path("/x")
        )
        self.assertIn("ses_aaa", hint)
        self.assertIn("ses_bbb", hint)
        # example command uses the most-recent (last) captured session
        self.assertIn("aw oc run --session ses_bbb <selector>", hint)
        self.assertIn("aw runs run-xyz", hint)

    def test_custom_driver_cmd(self):
        hint = driver.render_continuation_hint(
            self._state({"demo": "ses_abc123"}, queue=[{"status": "failed"}]),
            Path("/x"),
            driver_cmd="aw oc runipd",
        )
        self.assertIn("aw oc runipd --session ses_abc123 <selector>", hint)
        self.assertIn("aw oc runipd resume --repo /repo run-xyz", hint)


class VerifierPromptTests(unittest.TestCase):
    """#1: turn-2 verifier prompt is well-formed and instructs a fresh-session audit."""

    def test_build_verifier_prompt_contents(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            (run_dir / "outcomes").mkdir(parents=True)
            item = {"position": 3, "id6": "abc123", "setid": "demo"}
            state = {"run_id": "run-test"}
            prompt = driver.build_verifier_prompt(
                item, state, run_dir, Path("/plan.ipd.md")
            )
            self.assertIn("Independent Rigorous Verification", prompt)
            self.assertIn("fresh OpenCode session", prompt)
            self.assertIn("03-abc123-verification.json", prompt)
            self.assertIn("VERIFIED|CORRECTION_REQUIRED|BLOCKED", prompt)
            self.assertIn("Never push", prompt)

    def test_no_audit_flag_sets_option(self):
        # Default is validate=False
        args_default = driver.build_parser().parse_args(
            ["start", "demo", "--repo", "."]
        )
        self.assertFalse(args_default.validate)

        # --validate, --verify, --audit opt in
        args_val = driver.build_parser().parse_args(
            ["start", "demo", "--repo", ".", "--validate"]
        )
        self.assertTrue(args_val.validate)

        args_ver = driver.build_parser().parse_args(
            ["start", "demo", "--repo", ".", "--verify"]
        )
        self.assertTrue(args_ver.validate)

        args_aud = driver.build_parser().parse_args(
            ["start", "demo", "--repo", ".", "--audit"]
        )
        self.assertTrue(args_aud.validate)

        # --no-validate, --no-verify, --no-audit explicitly opt out
        args_noval = driver.build_parser().parse_args(
            ["start", "demo", "--repo", ".", "--no-validate"]
        )
        self.assertFalse(args_noval.validate)

        args_nover = driver.build_parser().parse_args(
            ["start", "demo", "--repo", ".", "--no-verify"]
        )
        self.assertFalse(args_nover.validate)

        args_noaud = driver.build_parser().parse_args(
            ["start", "demo", "--repo", ".", "--no-audit"]
        )
        self.assertFalse(args_noaud.validate)

    def test_verify_log_and_prompt_use_distinct_suffix(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            (run_dir / "sessions").mkdir(parents=True)
            (run_dir / "prompts").mkdir(parents=True)
            item = {
                "position": 2,
                "id6": "abc123",
                "setid": "demo",
                "action": "execute",
            }
            log = driver.attempt_log_path(run_dir, item, 1, suffix="verify")
            self.assertTrue(log.name.endswith("attempt-1-verify.jsonl"))
            p = driver.write_prompt(run_dir, item, "hi", 1, suffix="verify")
            self.assertIn("verify", p.name)

    def test_concurrent_work_statement_in_prompts(self):
        item = {"position": 1, "id6": "abc123", "setid": "testset"}
        state = {"run_id": "run-test-12345"}
        exec_prompt = driver.build_prompt(
            item, state, Path("/tmp/run"), Path("/tmp/plan.md"), recovery=False
        )
        verify_prompt = driver.build_verifier_prompt(
            item, state, Path("/tmp/run"), Path("/tmp/plan.md")
        )
        # coauthor Order 01 (a5ni7v): assert the REQUIRED PROPERTIES of this section rather than a
        # frozen blob. The previous form pinned the exact prose (including a curly apostrophe), so
        # adding the mandatory staged-set verification step broke it for no substantive reason.
        for prompt in (exec_prompt, verify_prompt):
            self.assertIn("## Concurrent Work", prompt)
            self.assertIn(
                "Other agents may modify this repository concurrently", prompt
            )
            self.assertIn(
                "Do not alter, revert, stage, or commit another agent's work", prompt
            )
            self.assertIn("never use `git add .` or `git add -A`", prompt)
            # The rule must be ACTIONABLE, not just a prohibition (a5ni7v E-03).
            self.assertIn("git diff --cached --name-only", prompt)
            self.assertIn("git restore --staged", prompt)
            self.assertIn("ALREADY STAGED", prompt)
            self.assertIn("Never discard their work", prompt)

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

    def test_driver_actor_is_parenthesis_free(self):
        # The terminal history line is `- <date> <status> (<actor>): <msg>`; a parenthesized actor
        # would misparse under the attribution lint, so the model is rendered as `model=<m>`.
        self.assertEqual(
            driver.driver_actor({"options": {"model": "opus-4.8"}}),
            "aw oc run model=opus-4.8",
        )
        self.assertNotIn("(", driver.driver_actor({"options": {"model": "x"}}))
        self.assertEqual(driver.driver_actor({"options": {}}), "aw oc run")

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

            # begin was attempted; run_opencode was NEVER launched; item recorded blocked.
            self.assertEqual(calls, [("begin", "wir001")])
            self.assertEqual(item["status"], "blocked")
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
                    json.dumps({"disposition": "executed", "pushed": False}),
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
                json.dumps({"disposition": "executed", "pushed": False}),
                encoding="utf-8",
            )
            # verifier outcome -> verified
            (run_dir / "outcomes" / "01-wir001-verification.json").write_text(
                json.dumps({"verdict": "CONFORMING"}), encoding="utf-8"
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
                json.dumps({"disposition": "executed", "pushed": False}),
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
            self.assertEqual(item["status"], "substantially-complete")
            self.assertTrue(plan.is_file(), "plan must remain in pending/ (not forced)")

    def test_finalize_refusal_does_not_stamp_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "wir001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(repo, plan, self_finalize=True)
            state["options"]["no_audit"] = False

            (run_dir / "outcomes" / "01-wir001.json").write_text(
                json.dumps({"disposition": "executed", "pushed": False}),
                encoding="utf-8",
            )
            (run_dir / "outcomes" / "01-wir001-verification.json").write_text(
                json.dumps({"verdict": "CONFORMING"}), encoding="utf-8"
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
            self.assertEqual(item["status"], "substantially-complete")
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
                json.dumps({"disposition": "executed", "pushed": False}),
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


class WorktreeIsolationTests(unittest.TestCase):
    """driverfin-02 (emus4n): each execute-action child runs in its OWN git worktree; the main tree
    stays clean during the turn; a verified child's commits integrate back to main via the REUSED
    integration gate; a non-passing gate leaves the child NOT integrated (deferred, not faked)."""

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
                ).write_text(json.dumps({"verdict": "CONFORMING"}), encoding="utf-8")
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
                json.dumps({"disposition": "executed", "pushed": False}),
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
                        json.dumps({"disposition": "executed", "pushed": False}),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(run_dir / "log"), ["oc"]
                (
                    run_dir
                    / "outcomes"
                    / f"{item['position']:02d}-{item['id6']}-verification.json"
                ).write_text(json.dumps({"verdict": "CONFORMING"}), encoding="utf-8")
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
            receipt = ipd_lifecycle.receipt_path_for(repo, "wir001")
            self.assertTrue(
                receipt.is_file(),
                f"begin receipt must be under MAIN repo's .aw/state at {receipt}",
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

            # NOT faked executed; recorded as merge-conflict (driverfin-03 E-02) with a reason.
            self.assertEqual(item["status"], "merge-conflict")
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
                ).write_text(json.dumps({"verdict": "CONFORMING"}), encoding="utf-8")
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
                json.dumps({"disposition": "executed", "pushed": False}),
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
                ).write_text(json.dumps({"verdict": "CONFORMING"}), encoding="utf-8")
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
                json.dumps({"disposition": "executed", "pushed": False}),
                encoding="utf-8",
            )
            return 0, "ses1", str(run_dir / "log"), ["oc"]

        return fake_run

    def test_dirty_overlapping_base_refuses_integration(self):
        # V-01: if MAIN has an un-owned dirty path overlapping the incoming lane's changed_files, the
        # integration gate is NOT invoked, the item status is `integration-blocked`, an
        # `integration-blocked` event is emitted, MAIN stays unmodified apart from the un-owned dirty
        # edit, and the verified branch/worktree are preserved.
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
            # Item recorded integration-blocked, NOT executed.
            self.assertEqual(item["status"], "integration-blocked")
            self.assertIn("integration_deferral", item)
            self.assertIn("src/demo.txt", item["integration_deferral"])
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
            # The fail-closed event was recorded.
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("ipd-integration-blocked", events)

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

            # merge-conflict recorded, NOT executed.
            self.assertEqual(item["status"], "merge-conflict")
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


if __name__ == "__main__":
    unittest.main()
