#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Add tool directory to sys.path before importing driver
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import runipd as driver  # noqa: E402


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
            Path(__file__).parent / "20260823-pending-ipds-driver-manifest.json"
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
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "demo",
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
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
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
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "--repo",
                    os.fspath(repo),
                    "--prepare-only",
                    "tst001",
                ],
                cwd=repo,
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

    def test_step_finish_summarizes_tokens_and_cost(self):
        line = driver.render_event(
            '{"type":"step_finish","part":{"tokens":{"total":1234},"cost":0.0042}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("1234 tok", line)
        self.assertIn("$0.0042", line)

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


if __name__ == "__main__":
    unittest.main()
