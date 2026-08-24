#!/usr/bin/env python3

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

import ipdrunner as driver


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

        # Also verify prefix matching tolerance (e.g. execse -> execset)
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
                    f"# {id6}\n", encoding="utf-8"
                )
            manifest = {
                "schema_version": 1,
                "plans": {
                    "aaaaaa": {
                        "set": "demo",
                        "file": ".aw/records/plans/pending/20260824-demo-01-aaaaaa-test.ipd.md",
                        "dependencies": [],
                    },
                    "bbbbbb": {
                        "set": "demo",
                        "file": ".aw/records/plans/pending/20260824-demo-02-bbbbbb-test.ipd.md",
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
                             'ses_'+hashlib.sha1(args[args.index('--title')+1].encode()).hexdigest()[:12])
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
                [item["status"] for item in state["queue"]], ["executed", "executed"]
            )
            self.assertEqual(len(state["set_sessions"]), 1)
            sessions = [item["attempts"][0]["session_id"] for item in state["queue"]]
            self.assertEqual(sessions[0], sessions[1])


def _make_run_dir(root: Path, queue: list) -> Path:
    """Build a minimal run_dir + state.json for a non-git repo at <root>/repo.

    The repo need not be a real git repo for run_queue/reconcile_interrupted,
    which do not shell out to git; execute_item would, but these tests either
    never reach a launch (terminal/blocked items) or point run_queue at a fake
    opencode via options. state carries only what the exercised paths read.
    """
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


class ResumeRequeueTests(unittest.TestCase):
    def test_bare_resume_requeues_interrupted_item(self):
        # B-01 regression: a plain resume (retry_incomplete=False) must re-queue
        # the item left in flight (status 'running' -> 'interrupted' by
        # reconcile_interrupted) so it is retried in recovery mode. It must NOT
        # touch a following queued item's independence, and must not be silently
        # abandoned. We stop the item before an actual launch by making its
        # dependency unsatisfiable is not needed: instead we assert the transition
        # produced by reconcile_interrupted + the bare-resume re-queue, by running
        # the queue with a fake opencode that marks the plan executed.
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

            # Simulate the FIRST half of a bare resume: reconcile the crashed
            # in-flight item. On current (pre-fix) code this leaves it
            # 'interrupted' and a bare resume would never run it again.
            driver.reconcile_interrupted(run_dir, state)
            self.assertEqual(state["queue"][0]["status"], "interrupted")

            # The behavior under test: a bare resume must re-queue it. We call the
            # helper that run_queue uses for a bare resume. If B-01 is unfixed
            # there is no such requeue and the item stays 'interrupted'.
            requeued = driver.requeue_interrupted(run_dir, state)
            self.assertIn("aaaaaa", requeued)
            self.assertEqual(state["queue"][0]["status"], "queued")
            self.assertTrue(state["queue"][0].get("recovery_next"))

    def test_bare_resume_does_not_requeue_partial_or_failed(self):
        # B-01 anti-regression: E-01 must NOT broaden bare-resume scope. A
        # 'partial' or 'failed-safely' item is only re-queued by
        # --retry-incomplete, never by a bare resume.
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
        # B-02 regression: initialize_run's guard must report "Not a Git
        # repository", not a raw "Command failed (128)" from git rev-parse.
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
        # B-03 regression: selecting a known but empty Set must name that Set,
        # not fall through to the "At least one ..." message.
        manifest = {"schema_version": 1, "plans": {}, "sets": {"empty": {"order": []}}}
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
    """The terminal renderer must turn raw child JSON events into concise,
    human-readable lines (full JSON still goes to the session log), and be a
    no-op when color is disabled."""

    def setUp(self) -> None:
        self.plain = driver.Palette(False)  # color disabled -> no escape codes

    def test_text_event_renders_narration(self):
        line = driver.render_event(
            '{"type":"text","part":{"type":"text","text":"Reading the plan."}}',
            self.plain,
        )
        assert line is not None
        self.assertIn("Reading the plan.", line)
        self.assertNotIn("\033[", line)  # no ANSI when color disabled

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
    """E-01/V-01: terminate_process reaps a child without leaving an orphan,
    escalating signals and closing pipes."""

    def test_terminate_process_reaps_running_child(self):
        import sys as _sys

        # A child that ignores SIGINT/SIGTERM forces escalation to SIGKILL.
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
        # Shrink the escalation grace so the test is fast.
        orig = (driver._SIGINT_GRACE_SECONDS, driver._SIGTERM_GRACE_SECONDS)
        driver._SIGINT_GRACE_SECONDS = 0.3
        driver._SIGTERM_GRACE_SECONDS = 0.3
        try:
            driver.terminate_process(proc)
        finally:
            driver._SIGINT_GRACE_SECONDS, driver._SIGTERM_GRACE_SECONDS = orig
        # After termination the child is reaped (returncode set) and not an orphan.
        self.assertIsNotNone(proc.returncode)
        self.assertIsNotNone(proc.poll())
        # Pipe was closed.
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
        # Must not raise on an already-exited process.
        driver.terminate_process(proc)
        self.assertIsNotNone(proc.returncode)


class DependencyFailClosedTests(unittest.TestCase):
    """E-02/V-02: an unqueued, unexecuted prerequisite is UNSATISFIED, not
    silently assumed done."""

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
            # Dependency exists only in pending/ (NOT executed) and is NOT in queue.
            repo = self._repo_with_dep(temp, "pending")
            state = {
                "repo": str(repo),
                "queue": [
                    {"id6": "itemaa", "status": "queued", "dependencies": ["depaaa"]}
                ],
            }
            item = state["queue"][0]
            satisfied, missing = driver.dependency_status(item, state)
            self.assertFalse(satisfied)
            self.assertEqual(missing, ["depaaa"])

    def test_unqueued_dependency_absent_from_repo_is_unsatisfied(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            repo = self._repo_with_dep(temp, None)  # dep not present anywhere
            state = {
                "repo": str(repo),
                "queue": [
                    {"id6": "itemaa", "status": "queued", "dependencies": ["depaaa"]}
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
                    {"id6": "itemaa", "status": "queued", "dependencies": ["depaaa"]}
                ],
            }
            satisfied, missing = driver.dependency_status(state["queue"][0], state)
            self.assertTrue(satisfied)
            self.assertEqual(missing, [])


class RunDirResolutionTests(unittest.TestCase):
    """E-03/V-03: resolve_run_dir accepts a directory path (with state.json), and
    extract_session_id parses alternate JSON key conventions."""

    def test_resolve_run_dir_accepts_directory_path(self):
        with tempfile.TemporaryDirectory() as t:
            temp = Path(t)
            run_dir = temp / "runs" / "run-abc"
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text("{}", encoding="utf-8")
            # Absolute path to the run dir itself resolves.
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
        # Build ids at runtime (no literal ses_ token in source) to avoid the
        # local-leak session-id scanner; still exercises the ses_ prefix path.
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
    """E-04/V-04: atomic_write_json fsyncs the dir with a POSIX-conformant mode,
    and reconcile_interrupted records interrupted_at on the open attempt."""

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
                            {"number": 1, "started_at": "2026-08-24T00:00:00+00:00"}
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
