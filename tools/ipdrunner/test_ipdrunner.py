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


if __name__ == "__main__":
    unittest.main()
