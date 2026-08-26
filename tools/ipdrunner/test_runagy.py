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

import runagy as driver  # noqa: E402


class AgyEventRenderTests(unittest.TestCase):
    def setUp(self):
        self.pal = driver.Palette(True)

    def test_render_init(self):
        line = json.dumps(
            {
                "event": "init",
                "conversation_id": "conv-12345678-abcd",
                "init": {"model": "gemini-3.7-flash-high"},
            }
        )
        rendered = driver.render_agy_event(line, self.pal)
        self.assertIsNotNone(rendered)
        self.assertIn("Initialized Antigravity (gemini-3.7-flash-high)", rendered)
        self.assertIn("conv-123", rendered)

    def test_render_result_success(self):
        line = json.dumps(
            {
                "event": "result",
                "result": {
                    "status": "SUCCESS",
                    "conversation_id": "conv-12345678-abcd",
                    "response": "Done!",
                },
            }
        )
        rendered = driver.render_agy_event(line, self.pal)
        self.assertIsNotNone(rendered)
        self.assertIn("Antigravity turn finished: SUCCESS", rendered)

    def test_render_result_failure(self):
        line = json.dumps(
            {
                "event": "result",
                "result": {
                    "status": "ERROR",
                    "error": "Timeout expired",
                    "conversation_id": "conv-12345678-abcd",
                },
            }
        )
        rendered = driver.render_agy_event(line, self.pal)
        self.assertIsNotNone(rendered)
        self.assertIn("Antigravity turn failed: Timeout expired", rendered)

    def test_render_tool_step_active_and_done(self):
        active_line = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "step_index": 3,
                    "state": "ACTIVE",
                    "step_type": "tool",
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"CommandLine": "pytest tests/ -v"},
                    },
                },
            }
        )
        active_rendered = driver.render_agy_event(active_line, self.pal)
        self.assertIsNotNone(active_rendered)
        self.assertIn("run_command", active_rendered)
        self.assertIn("pytest tests/ -v", active_rendered)

        done_line = json.dumps(
            {
                "event": "step_update",
                "step_update": {
                    "step_index": 3,
                    "state": "DONE",
                    "step_type": "tool",
                    "duration_seconds": 1.25,
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"CommandLine": "pytest tests/ -v"},
                    },
                },
            }
        )
        done_rendered = driver.render_agy_event(done_line, self.pal)
        self.assertIsNotNone(done_rendered)
        self.assertIn("1.25s", done_rendered)


class AgyParserAndDiscoveryTests(unittest.TestCase):
    def test_read_deps_and_set(self):
        text = textwrap.dedent(
            """
            - Date: 2026-08-24
            - Kind: child
            - Status: to-review
            - Set: "authset" (Authentication flow)
            - Order: 2
            - Dependencies: [dep001, dep002]
            - Id: a1b2c3
            """
        )
        self.assertEqual(driver._read_id(text), "a1b2c3")
        self.assertEqual(driver._read_set(text), "authset")
        self.assertEqual(driver._read_order(text), 2)
        self.assertEqual(driver._read_status(text), "to-review")
        self.assertEqual(driver._read_deps(text), ["dep001", "dep002"])

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
        exec_item_1 = {
            "id6": "tgt001",
            "action": "execute",
            "dependencies": ["dep001"],
        }
        sat, missing = driver.dependency_status(exec_item_1, state)
        self.assertFalse(sat)
        self.assertEqual(missing, ["dep001"])

        # Execution item depending on 'executed' plan -> satisfied
        exec_item_3 = {
            "id6": "tgt003",
            "action": "execute",
            "dependencies": ["dep003"],
        }
        sat, missing = driver.dependency_status(exec_item_3, state)
        self.assertTrue(sat)
        self.assertEqual(missing, [])

        # Review item depending on 'reviewed' plan -> satisfied
        rev_item_1 = {
            "id6": "tgt004",
            "action": "review",
            "dependencies": ["dep001"],
        }
        sat, missing = driver.dependency_status(rev_item_1, state)
        self.assertTrue(sat)
        self.assertEqual(missing, [])

    def test_validate_manifest(self):
        valid = {
            "schema_version": 1,
            "plans": {
                "p00001": {
                    "file": ".aw/records/plans/pending/p1.ipd.md",
                    "set": "demo",
                    "dependencies": [],
                }
            },
            "sets": {"demo": {"order": ["p00001"]}},
        }
        driver.validate_manifest(valid)

        invalid_schema = dict(valid, schema_version=99)
        with self.assertRaises(driver.DriverError):
            driver.validate_manifest(invalid_schema)

        invalid_dep = {
            "schema_version": 1,
            "plans": {
                "p00001": {
                    "file": ".aw/records/plans/pending/p1.ipd.md",
                    "set": "demo",
                    "dependencies": ["nonexistent"],
                }
            },
            "sets": {"demo": {"order": ["p00001"]}},
        }
        with self.assertRaises(driver.DriverError):
            driver.validate_manifest(invalid_dep)

    def test_expand_selectors_all_finds_actionable_plans(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "p00001": {
                    "file": ".aw/records/plans/pending/p1.ipd.md",
                    "set": "demo",
                    "status": "approved",
                },
                "p00002": {
                    "file": ".aw/records/plans/executed/p2.ipd.md",
                    "set": "demo",
                    "status": "executed",
                },
            },
            "sets": {"demo": {"order": ["p00001", "p00002"]}},
        }
        expanded = driver.expand_selectors(manifest, ["all"])
        self.assertEqual(expanded, ["p00001"])

    def test_set_prefix_and_substring_expansion(self):
        manifest = {
            "schema_version": 1,
            "plans": {
                "p00001": {
                    "file": ".aw/records/plans/pending/20260824-authsystem-01-p00001-login.ipd.md",
                    "set": "authsystem",
                    "dependencies": [],
                }
            },
            "sets": {"authsystem": {"order": ["p00001"]}},
        }
        # Prefix match 'auth'
        self.assertEqual(driver.expand_selectors(manifest, ["auth"]), ["p00001"])
        # Substring match 'login'
        self.assertEqual(driver.expand_selectors(manifest, ["login"]), ["p00001"])


class AgyExecutionLifecycleTests(unittest.TestCase):
    def _create_mock_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test Agent"],
            cwd=repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "agent@example.com"],
            cwd=repo,
            check=True,
        )

        plans_pending = repo / ".aw" / "records" / "plans" / "pending"
        plans_pending.mkdir(parents=True)

        plan1 = plans_pending / "20260824-demo-01-a1b2c3-implement-first-feature.ipd.md"
        plan1.write_text(
            textwrap.dedent(
                """
            # IPD: First Feature

            - Date: 2026-08-24
            - Kind: child
            - Status: approved
            - Set: demo
            - Order: 1
            - Author: Antigravity
            - Id: a1b2c3

            ## Workflow history
            - 2026-08-24 approved (Human): ready

            ## Goal
            Goal 1
            """
            ),
            encoding="utf-8",
        )

        dummy = repo / "README.md"
        dummy.write_text("# Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
        return repo

    def _write_fake_agy(self, root: Path, behavior: str = "normal") -> Path:
        fake_agy = root / "fake_agy.py"
        fake_agy.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json, pathlib, re, sys, time

                args = sys.argv[1:]
                prompt = ""
                if "-p" in args:
                    prompt = args[args.index("-p") + 1]

                session = "conv-exec-1111"
                if "--conversation" in args:
                    session = args[args.index("--conversation") + 1]

                if "{behavior}" == "stall":
                    time.sleep(2.0)
                    sys.exit(0)

                if "Independent Rigorous Verification" in prompt:
                    verify_session = "conv-verify-9999"
                    print(json.dumps({{"event":"init","conversation_id":verify_session,"init":{{"model":"gemini-3.7-flash-high"}}}}))
                    print(json.dumps({{"event":"step_update","step_update":{{"step_index":1,"state":"DONE","step_type":"tool","tool_info":{{"name":"run_command","parameters":{{"CommandLine":"pytest"}}}}}}}}))
                    # Write verification outcome JSON
                    m = re.search(r"Verification Outcome JSON to write: `(.+?)`", prompt)
                    if m:
                        out_p = pathlib.Path(m.group(1).strip())
                        out_p.parent.mkdir(parents=True, exist_ok=True)
                        if "{behavior}" == "verify_blocked":
                            out_p.write_text(json.dumps({{"schema_version":1,"id6":"a1b2c3","verdict":"BLOCKED","summary":"Defects found"}}))
                        else:
                            out_p.write_text(json.dumps({{"schema_version":1,"id6":"a1b2c3","verdict":"VERIFIED","summary":"Clean audit"}}))
                    print(json.dumps({{"event":"result","result":{{"status":"SUCCESS","conversation_id":verify_session,"response":"Verification done"}}}}))
                    sys.exit(0)
                elif prompt.startswith("/plan-review"):
                    target_file = prompt.split()[-1]
                    p = pathlib.Path(target_file)
                    if not p.is_absolute():
                        p = pathlib.Path.cwd() / p
                    if p.is_file():
                        content = p.read_text()
                        content = content.replace("- Status: to-review", "- Status: reviewed")
                        content += "\\n- 2026-08-24 /plan-review (agy): APPROVE. Readiness: GO - PENDING HUMAN APPROVAL.\\n"
                        p.write_text(content)
                    print(json.dumps({{"event":"init","conversation_id":"conv-review-0000","init":{{"model":"gemini-3.7-flash-high"}}}}))
                    print(json.dumps({{"event":"result","result":{{"status":"SUCCESS","conversation_id":"conv-review-0000","response":"Review done"}}}}))
                    sys.exit(0)
                else:
                    print(json.dumps({{"event":"init","conversation_id":session,"init":{{"model":"gemini-3.7-flash-high"}}}}))
                    print(json.dumps({{"event":"step_update","step_update":{{"step_index":1,"state":"DONE","step_type":"tool","tool_info":{{"name":"run_command","parameters":{{"CommandLine":"touch feature.py"}}}}}}}}))
                    # Write execution outcome JSON and move plan to executed
                    m_out = re.search(r"Required JSON outcome: (.+)", prompt)
                    m_plan = re.search(r"Plan file at launch: (.+)", prompt)
                    if m_out:
                        out_p = pathlib.Path(m_out.group(1).strip())
                        out_p.parent.mkdir(parents=True, exist_ok=True)
                        out_p.write_text(json.dumps({{"schema_version":1,"id6":"a1b2c3","disposition":"executed","pushed":False}}))
                    if m_plan:
                        plan_p = pathlib.Path(m_plan.group(1).strip())
                        if plan_p.is_file():
                            exec_p = pathlib.Path(str(plan_p).replace("/pending/", "/executed/"))
                            exec_p.parent.mkdir(parents=True, exist_ok=True)
                            plan_p.rename(exec_p)
                    print(json.dumps({{"event":"result","result":{{"status":"SUCCESS","conversation_id":session,"response":"Execution complete"}}}}))
                    sys.exit(0)
                """
            ),
            encoding="utf-8",
        )
        fake_agy.chmod(0o755)
        return fake_agy

    def test_runagy_two_turn_execution_with_clean_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)
            fake_agy = self._write_fake_agy(root)

            # Start runagy
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            # Locate run directory
            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            state_file = run_dir / "state.json"
            self.assertTrue(state_file.is_file())

            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(len(state["queue"]), 1)
            item = state["queue"][0]
            self.assertEqual(item["status"], "executed")
            self.assertEqual(item["verification_status"], "verified")
            self.assertEqual(len(item["attempts"]), 1)

            # Confirm events.jsonl contains structured events
            events_file = run_dir / "events.jsonl"
            self.assertTrue(events_file.is_file())
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            event_types = [e["event"] for e in events]
            self.assertIn("run-created", event_types)
            self.assertIn("ipd-started", event_types)
            self.assertIn("ipd-finished", event_types)

            # Confirm both execution session log and verification session log exist
            exec_log = run_dir / "sessions" / "01-a1b2c3-attempt-1.jsonl"
            verify_log = run_dir / "sessions" / "01-a1b2c3-verify-attempt-1.jsonl"
            self.assertTrue(exec_log.is_file())
            self.assertTrue(verify_log.is_file())

            # Confirm clean session used for verification (different conv IDs)
            self.assertIn("conv-exec-1111", exec_log.read_text())
            self.assertIn("conv-verify-9999", verify_log.read_text())

    def test_default_start_subcommand_inference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)
            fake_agy = self._write_fake_agy(root)

            # Invoke runagy without "start" subcommand (e.g. runagy a1b2c3 ...)
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Run ID:", result.stdout)

    def test_prepare_only_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)

            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--prepare-only",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("01 a1b2c3 demo", result.stdout)

    def test_explicit_run_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)
            fake_agy = self._write_fake_agy(root)

            custom_id = "run-my-custom-2026"
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--run-id",
                    custom_id,
                    "--agy",
                    os.fspath(fake_agy),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = repo / ".aw" / "records" / "runs" / custom_id
            self.assertTrue(run_dir.is_dir())

    def test_runagy_no_verify_skips_turn2(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)
            fake_agy = self._write_fake_agy(root)

            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                    "--no-verify",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            verify_log = run_dir / "sessions" / "01-a1b2c3-verify-attempt-1.jsonl"
            self.assertFalse(verify_log.exists())

    def test_verification_blocked_sets_disposition_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)
            fake_agy = self._write_fake_agy(root, behavior="verify_blocked")

            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 1)

            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["queue"][0]["status"], "partial")
            self.assertEqual(state["queue"][0]["verification_status"], "blocked")

    def test_stall_timeout_and_resume_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)
            stall_agy = self._write_fake_agy(root, behavior="stall")

            # Start with 0.3s stall timeout so fake_agy (sleeping 2s) stalls
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(stall_agy),
                    "--stall-timeout",
                    "0.3",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 1)

            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )
            run_dir = repo / ".aw" / "records" / "runs" / run_id
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["queue"][0]["status"], "interrupted")

            # Now switch agy to normal and resume with --retry-incomplete
            normal_agy = self._write_fake_agy(root, behavior="normal")
            resume_res = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "resume",
                    run_id,
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(normal_agy),
                    "--retry-incomplete",
                    "--stall-timeout",
                    "10.0",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(resume_res.returncode, 0, resume_res.stderr)
            res_state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(res_state["queue"][0]["status"], "executed")
            self.assertEqual(len(res_state["queue"][0]["attempts"]), 2)
            self.assertTrue(res_state["queue"][0]["attempts"][1]["recovery"])

    def test_runagy_status_and_report_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = self._create_mock_repo(root)
            fake_agy = self._write_fake_agy(root)

            # Start run
            result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "start",
                    "a1b2c3",
                    "--repo",
                    os.fspath(repo),
                    "--agy",
                    os.fspath(fake_agy),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            run_id = next(
                line.split(": ", 1)[1].split()[0]
                for line in result.stdout.splitlines()
                if line.startswith("Run ID:")
            )

            # Test status command (text)
            status_res = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "status",
                    run_id,
                    "--repo",
                    os.fspath(repo),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(status_res.returncode, 0)
            self.assertIn(run_id, status_res.stdout)
            self.assertIn("a1b2c3", status_res.stdout)

            # Test status command (json)
            status_json_res = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "status",
                    run_id,
                    "--repo",
                    os.fspath(repo),
                    "--json",
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(status_json_res.returncode, 0)
            status_data = json.loads(status_json_res.stdout)
            self.assertEqual(status_data["run_id"], run_id)
            self.assertEqual(status_data["queue"][0]["id6"], "a1b2c3")

            # Test report command
            report_res = subprocess.run(
                [
                    sys.executable,
                    os.fspath(Path(driver.__file__).resolve()),
                    "report",
                    run_id,
                    "--repo",
                    os.fspath(repo),
                ],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(report_res.returncode, 0)
            self.assertIn("execution-report.md", report_res.stdout)

    def test_continuation_hint_rendering(self):
        state = {
            "repo": "/my/repo",
            "run_id": "run-test-12345",
            "set_sessions": {
                "setA": "conv-setA-1111",
                "setB": "conv-setB-2222",
            },
        }
        hint = driver.render_continuation_hint(state, Path("/tmp"))
        self.assertIn("conv-setA-1111", hint)
        self.assertIn("conv-setB-2222", hint)
        self.assertIn("runagy resume --repo /my/repo run-test-12345", hint)

    def test_concurrent_work_statement_in_prompts(self):
        item = {"position": 1, "id6": "a1b2c3", "setid": "testset"}
        state = {"run_id": "run-test-12345"}
        exec_prompt = driver.build_prompt(
            item, state, Path("/tmp/run"), Path("/tmp/plan.md"), recovery=False
        )
        verify_prompt = driver.build_verifier_prompt(
            item, state, Path("/tmp/run"), Path("/tmp/plan.md")
        )
        expected = (
            "## Concurrent Work\n\n"
            "Other agents may modify this repository concurrently. Work only on files required for your task. Ignore unrelated changes, commits, and untracked files.\n\n"
            "Do not alter, revert, stage, or commit another agent’s work. Stage only your files; never use `git add .` or `git add -A`.\n\n"
            "Stop only if another agent changes a file you are editing or must edit and the changes cannot be safely combined. Never discard their work."
        )
        self.assertIn(expected, exec_prompt)
        self.assertIn(expected, verify_prompt)


if __name__ == "__main__":
    unittest.main()
