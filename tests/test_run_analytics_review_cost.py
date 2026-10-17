#!/usr/bin/env python3
"""Review-cost analytics: session facts, attempt-grain query views, and run-start recording.

Behavioral only. Fixture run directories are written to a temp repo, analyzed through the real
`run_analyze` leaf or `collect_rows`, and the published `attempts.jsonl` is queried through the real
`aw runs query` entry point (`run_query`). Recording is checked by driving both runners'
`initialize_run` with `--prepare-only` and reading the state.json they write.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from agent_workflows import run_analytics_cli as analytics_cli
from agent_workflows import run_analytics_query as query
from agent_workflows import run_dashboard as dash

T0 = 1_787_949_977_000  # 2026-08-28T..Z in ms


def _jl(path: Path, objs) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(o) for o in objs) + "\n", encoding="utf-8")


def _oc_review_session(
    path: Path,
    *,
    session: str,
    contexts: list[tuple[int, int, int]],
    cost: float = 0.5,
    bash: tuple[tuple[str, str], ...] | list[tuple[str, str]] = (),
    reads: tuple[str, ...] | list[str] = (),
) -> None:
    """An OpenCode session: one step_finish per (input, cache_read, cache_write) in ``contexts``."""

    objs = []
    t = T0
    for i, (inp, cread, cwrite) in enumerate(contexts):
        t += 1000
        objs.append(
            {"type": "step_start", "sessionID": session, "timestamp": t, "part": {}}
        )
        if i < len(bash):
            cmd, out = bash[i]
            objs.append(
                {
                    "type": "tool_use",
                    "sessionID": session,
                    "timestamp": t + 10,
                    "part": {
                        "tool": "bash",
                        "state": {
                            "status": "completed",
                            "input": {"command": cmd},
                            "output": out,
                            "time": {"start": t, "end": t + 50},
                        },
                    },
                }
            )
        if i < len(reads):
            objs.append(
                {
                    "type": "tool_use",
                    "sessionID": session,
                    "timestamp": t + 20,
                    "part": {
                        "tool": "read",
                        "state": {
                            "status": "completed",
                            "input": {"filePath": reads[i]},
                            "output": "x" * 100,
                            "time": {"start": t, "end": t + 5},
                        },
                    },
                }
            )
        objs.append(
            {
                "type": "step_finish",
                "sessionID": session,
                "timestamp": t + 900,
                "part": {
                    "tokens": {
                        "input": inp,
                        "output": 10,
                        "reasoning": 2,
                        "cache": {"read": cread, "write": cwrite},
                    },
                    "cost": cost / len(contexts),
                },
            }
        )
    _jl(path, objs)


def _review_run(
    runs: Path,
    run_id: str,
    *,
    label: str = "",
    variant: str = "",
    model: str = "uri/m-a",
) -> Path:
    """A two-item review run: item A in a NEW session, item B REUSING A's session, plus a verifier."""

    run = runs / run_id
    sess = run / "sessions"
    _oc_review_session(
        sess / "01-aaaaaa-attempt-1.jsonl",
        session="ses_A",
        contexts=[(30000, 0, 5000), (100, 40000, 0), (200, 60000, 0)],
        cost=0.6,
        bash=[
            ("cd /x && git log --oneline -3 | head -1", "abc"),
            ("python3 -m agent_workflows ipd lint p.md", "conforming" * 10),
        ],
        reads=["/somewhere/.aw/worktrees/lane1/agent_workflows/a.py"],
    )
    _oc_review_session(
        sess / "02-bbbbbb-attempt-1.jsonl",
        session="ses_A",
        contexts=[(100, 200000, 0), (100, 210000, 0)],
        cost=0.4,
        bash=[("rg -n foo src", "hit")],
        reads=["/somewhere/.aw/worktrees/lane2/agent_workflows/a.py"],
    )
    _oc_review_session(
        sess / "01-aaaaaa-attempt-1-verify.jsonl",
        session="ses_V",
        contexts=[(1000, 0, 0)],
        cost=0.05,
    )

    def att(id6: str, log: str, start: str, *, verify: bool = False) -> dict:
        a = {
            "number": 1,
            "action": "review",
            "disposition": "reviewed",
            "log": str(sess / log),
            "started_at": start,
            "ended_at": start.replace(":00:00", ":05:00"),
            "model": model,
        }
        if verify:
            a["verify_log"] = str(sess / "01-aaaaaa-attempt-1-verify.jsonl")
            a["verification"] = "verified"
        return a

    state = {
        "run_id": run_id,
        "created_at": "2026-09-10T00:00:00+00:00",
        "driver": {"id": "oc_runipd"},
        "options": {
            "opencode": "opencode",
            "label": label or None,
            "review_variant": variant or None,
        },
        "git": {
            "commit": "f" * 40,
            "dirty": False,
            "aw_version": "1.3.0rc2.dev1+g0123456789ab",
        },
        "queue": [
            {
                "id6": "aaaaaa",
                "setid": "s",
                "action": "review",
                "status": "reviewed",
                "attempts": [
                    att(
                        "aaaaaa",
                        "01-aaaaaa-attempt-1.jsonl",
                        "2026-09-10T01:00:00+00:00",
                        verify=True,
                    )
                ],
            },
            {
                "id6": "bbbbbb",
                "setid": "s",
                "action": "review",
                "status": "reviewed",
                "attempts": [
                    att(
                        "bbbbbb",
                        "02-bbbbbb-attempt-1.jsonl",
                        "2026-09-10T02:00:00+00:00",
                    )
                ],
            },
        ],
    }
    run.mkdir(parents=True, exist_ok=True)
    (run / "state.json").write_text(json.dumps(state), encoding="utf-8")
    events = [
        {
            "at": "2026-09-10T02:01:00+00:00",
            "event": "ipd-finalize-refused",
            "id6": "bbbbbb",
            "exit_code": 1,
        },
        {
            "at": "2026-09-10T02:02:00+00:00",
            "event": "ipd-turn-retry",
            "id6": "bbbbbb",
            "idempotency_key": "bbbbbb:attempt-1",
        },
        {
            "at": "2026-09-10T01:03:00+00:00",
            "event": "review-orchestrator-correction",
            "id6": "aaaaaa",
            "attempt": 1,
        },
    ]
    (run / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
    )
    return run


class SessionFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.runs = Path(self.tmp.name) / "runs"
        run_dir = _review_run(
            self.runs, "run-20260910T000000Z-1", label="exp1", variant="single-12"
        )
        self.rows, _ = dash.collect_rows(
            [run_dir], cache_path=None, repo=Path(self.tmp.name)
        )
        self.by = {(r["id6"], r["role"]): r for r in self.rows}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_context_first_last_max_per_step(self) -> None:
        a = self.by[("aaaaaa", "main")]
        # context = input + cache read + cache write, per step
        self.assertEqual(a["context_first"], 35000)
        self.assertEqual(a["context_last"], 60200)
        self.assertEqual(a["context_max"], 60200)
        self.assertEqual(a["steps"], 3)
        self.assertEqual(a["step_bucket"], "000-024")

    def test_token_components_are_separate(self) -> None:
        a = self.by[("aaaaaa", "main")]
        self.assertEqual(a["input"], 30300)
        self.assertEqual(a["cache_read"], 100000)
        self.assertEqual(a["cache_write"], 5000)
        self.assertEqual(a["output"], 30)
        self.assertEqual(a["reasoning"], 6)

    def test_session_origin_new_then_reused(self) -> None:
        self.assertEqual(self.by[("aaaaaa", "main")]["session_origin"], "new")
        self.assertEqual(self.by[("bbbbbb", "main")]["session_origin"], "reused")
        self.assertEqual(self.by[("aaaaaa", "verify")]["session_origin"], "new")

    def test_phase(self) -> None:
        self.assertEqual(self.by[("aaaaaa", "main")]["phase"], "review")
        self.assertEqual(self.by[("aaaaaa", "verify")]["phase"], "verifier")

    def test_tool_bytes_families_and_files(self) -> None:
        a = self.by[("aaaaaa", "main")]
        self.assertEqual(a["tool_bytes"]["bash"], 3 + 100)
        self.assertEqual(a["tool_bytes"]["read"], 100)
        self.assertEqual(a["families"], {"git log": 1, "head": 1, "aw ipd lint": 1})
        # Lane prefixes are dropped, so the same file reads the same in every worktree.
        self.assertEqual(a["read_counts"], {"agent_workflows/a.py": 1})
        self.assertEqual(
            self.by[("bbbbbb", "main")]["read_counts"], {"agent_workflows/a.py": 1}
        )

    def test_redo_counts_attach_to_their_attempt(self) -> None:
        b = self.by[("bbbbbb", "main")]
        self.assertEqual(
            (b["turn_retries"], b["refusals"], b["reasks"], b["redo_total"]),
            (1, 1, 0, 2),
        )
        a = self.by[("aaaaaa", "main")]
        self.assertEqual(
            (a["turn_retries"], a["refusals"], a["reasks"], a["redo_total"]),
            (0, 0, 1, 1),
        )

    def test_run_labels_and_commits(self) -> None:
        a = self.by[("aaaaaa", "main")]
        self.assertEqual(a["label"], "exp1")
        self.assertEqual(a["review_variant"], "single-12")
        self.assertEqual(a["code_commit"], "0123456789ab")
        self.assertEqual(a["repo_commit"], "f" * 12)
        self.assertEqual(a["repo_dirty"], "clean")


class CommandFamilyTests(unittest.TestCase):
    def test_families(self) -> None:
        cases = {
            "cd /x && git log --oneline -5 | head": ["git log", "head"],
            "python3 -m agent_workflows ipd lint foo.md": ["aw ipd lint"],
            "aw commit --no-plan -m msg -- a": ["aw commit"],
            "git -C /x diff --stat": ["git diff"],
            "FOO=1 timeout 60 python3 -m pytest -q": ["pytest"],
            "for f in *.py; do grep -n x $f; done": ["grep"],
            "grep -n 'a|b;c' f | head -3": ["grep", "head"],
            "python3 - <<'EOF'\nimport os\nfor a in b:\n    print(a)\nEOF\necho ok": [
                "python",
                "echo",
            ],
        }
        for command, want in cases.items():
            self.assertEqual(dash.command_families(command), want, command)


class AttemptQueryTests(unittest.TestCase):
    """Publish a bundle with `run_analyze`, then answer the attempt-grain views through `run_query`."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve()
        runs = self.repo / ".aw" / "records" / "runs"
        # 14 runs so medians clear the shared minimum n (12); two variants and two models.
        for i in range(14):
            variant = "grouped-6" if i % 2 else "single-12"
            model = "uri/m-a" if i < 7 else "uri/m-b"
            _review_run(
                runs,
                f"run-20260910T{i:02d}0000Z-{i}",
                label="exp1",
                variant=variant,
                model=model,
            )
        args = argparse.Namespace(
            dir=str(self.repo),
            path=False,
            list=False,
            open=False,
            rebuild=False,
            keep_snapshot=None,
            targets=[],
            agent=False,
            json=False,
            color=False,
            no_color=True,
            fields=None,
            verbose=False,
            limit=None,
            since=None,
            until=None,
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(analytics_cli.run_analyze(args), 0)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_bundle_carries_attempt_facts(self) -> None:
        latest = self.repo / ".aw" / "records" / "runs" / "analytics" / "latest"
        lines = (latest / dash.ATTEMPT_FACTS_FILENAME).read_text().splitlines()
        self.assertEqual(json.loads(lines[0])["record"], "header")
        self.assertEqual(len(lines) - 1, 14 * 3)

    def test_attempts_composition_and_shares(self) -> None:
        res = query.run_query(
            "attempts",
            repo=self.repo,
            filters=["action=review"],
            metric="total_tokens,input,cache_read,cache_write,output,reasoning,cost",
            stat="sum",
        )
        row = res.rows[0]
        self.assertEqual(row["n"], 28)  # main sessions only by default
        self.assertEqual(row["cache_read"], 14 * (100000 + 410000))
        shares = row["token_share"]
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=3)
        self.assertGreater(shares["cache_read"], 0.9)
        self.assertAlmostEqual(sum(row["cost_share"].values()), 1.0, places=3)

    def test_group_by_session_origin_and_step_bucket(self) -> None:
        res = query.run_query(
            "attempts",
            repo=self.repo,
            filters=["action=review"],
            group_by="session_origin",
            metric="context_first,steps",
        )
        rows = {r["session_origin"]: r for r in res.rows}
        self.assertEqual(rows["new"]["context_first"], 35000)
        self.assertEqual(rows["reused"]["context_first"], 200100)
        res = query.run_query(
            "attempts",
            repo=self.repo,
            group_by="step_bucket",
            metric="cost",
            stat="count",
        )
        self.assertEqual([r["step_bucket"] for r in res.rows], ["000-024"])

    def test_phase_reaches_verifier_sessions(self) -> None:
        res = query.run_query(
            "attempts",
            repo=self.repo,
            filters=["phase=verifier"],
            metric="steps",
            stat="count",
        )
        self.assertEqual(res.rows[0]["n"], 14)

    def test_under_powered_group_is_refused_not_computed(self) -> None:
        res = query.run_query(
            "attempts",
            repo=self.repo,
            filters=["id6=aaaaaa", "review_variant=grouped-6"],
            metric="cost",
        )
        row = res.rows[0]
        self.assertEqual(row["n"], 7)
        self.assertIsNone(row["cost"])
        self.assertIn("below minimum n=12", row["refused"])

    def test_model_source_coverage(self) -> None:
        res = query.run_query(
            "attempts",
            repo=self.repo,
            group_by="phase,model_source",
            metric="steps",
            stat="count",
        )
        by = {(r["phase"], r["model_source"]): r for r in res.rows}
        # Every review attempt carries `attempts[].model`, reported under the resolver's own label.
        self.assertEqual(by[("review", "options")]["n"], 28)
        self.assertEqual(by[("review", "options")]["with_model"], 28)

    def test_redo_counts_by_model(self) -> None:
        res = query.run_query(
            "attempts",
            repo=self.repo,
            group_by="model",
            metric="redo_total,turn_retries,refusals,reasks",
            stat="sum",
        )
        by = {r["model"]: r for r in res.rows}
        self.assertEqual(by["m-a"]["redo_total"], 7 * 3)
        self.assertEqual(by["m-b"]["turn_retries"], 7)

    def test_tools_view(self) -> None:
        res = query.run_query(
            "tools", repo=self.repo, filters=["action=review"], limit=10
        )
        tools = {r["name"]: r for r in res.rows if r["section"] == "tool"}
        self.assertEqual(tools["bash"]["calls"], 14 * 3)
        self.assertEqual(tools["bash"]["output_bytes"], 14 * (3 + 100 + 3))
        fams = {r["name"]: r["count"] for r in res.rows if r["section"] == "command"}
        self.assertEqual(fams["aw ipd lint"], 14)
        files = {r["name"]: r["count"] for r in res.rows if r["section"] == "file_read"}
        self.assertEqual(files, {"agent_workflows/a.py": 28})

    def test_experiment_view(self) -> None:
        res = query.run_query("experiment", repo=self.repo, filters=["label=exp1"])
        rows = {(r["id6"], r["review_variant"], r["model"]): r for r in res.rows}
        self.assertEqual(len(rows), 8)  # 2 plans x 2 variants x 2 models
        r = rows[("aaaaaa", "single-12", "m-a")]
        self.assertEqual(r["items"], 4)
        self.assertEqual(r["attempts"], 4)
        self.assertEqual(r["outcome"], {"reviewed": 4})
        # The verifier's cost is folded into the item it verified.
        self.assertAlmostEqual(r["cost_median"], 0.65, places=4)

    def test_disallowed_fields_refused(self) -> None:
        for kw in (
            {"filters": ["bogus=1"]},
            {"group_by": "run"},
            {"metric": "nope"},
            {"stat": "mode"},
        ):
            with self.assertRaises(query.QueryError):
                query.run_query("attempts", repo=self.repo, **kw)

    def test_schema_lists_attempt_vocabulary(self) -> None:
        payload = query.run_query("schema").payload
        self.assertIn("experiment", payload["views"])
        self.assertIn("session_origin", payload["attempt_grain"]["group_by_fields"])


class MissingBundleTests(unittest.TestCase):
    def test_query_before_analyze_is_cannot_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(query.QueryError) as ctx:
                query.run_query("attempts", repo=Path(td))
            self.assertIn("aw runs analyze", str(ctx.exception))


PLAN = """# IPD: label probe

- Date: 2026-10-17
- Kind: child
- Concern: fixture
- Scope: fixture
- Scope-Paths: README.md
- Status: approved
- Set: lblprobe
- Order: 1
- Highest E allocated: 01
- Author: test
- Priority: medium
- Work-Kind: feature
- Id: lbl001
- Approval: 2026-10-17, fixture
- Readiness: go-pending-approval

## Workflow history
- 2026-10-17 reviewed (test): APPROVE.

## Goal
Goal.

## Detailed Implementation Checklist (TODO)
### Task group 1: work
- [ ] E-01 Step 1
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
None.

## Findings
None.

## Proposed changes (ordered, validatable)
None.

## Deferred / out of scope (with reason)
None.

## Scope check
None.

## Required tests / validation
None.

## Spec / documentation sync
None.

## Open questions
None.

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: done
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


class RunStartRecordingTests(unittest.TestCase):
    """Both runners record `--label`, `--review-variant` and the run-start git block in state.json."""

    def _state(self, module, argv: list[str], *, dirty: bool = False) -> dict:
        from tests.repo_template import copy_template_repo

        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": home}, clear=False):
                repo = copy_template_repo(pathlib.Path(td) / "repo")
                (repo / ".gitignore").write_text(
                    ".aw/records/runs/\n", encoding="utf-8"
                )
                pending = repo / ".aw" / "records" / "plans" / "pending"
                pending.mkdir(parents=True, exist_ok=True)
                (pending / "20261017-lblprobe-01-lbl001-probe.ipd.md").write_text(
                    PLAN, encoding="utf-8"
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "initial"], cwd=repo, check=True
                )
                head = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    check=True,
                    text=True,
                    capture_output=True,
                ).stdout.strip()
                if dirty:
                    (repo / "untracked.txt").write_text("x", encoding="utf-8")
                args = module.build_parser().parse_args(
                    ["start", "lbl001", "--repo", str(repo), *argv]
                )
                args.prepare_only = True
                run_dir = module.initialize_run(args)
                state = runner_shared.load_state(run_dir)
                state["_head"] = head
                return state

    def test_both_hosts_record_label_variant_and_git(self) -> None:
        for module in (oc_runipd, agy_runipd):
            with self.subTest(host=module.__name__):
                state = self._state(
                    module, ["--label", "exp-7", "--review-variant", "grouped-6"]
                )
                self.assertEqual(state["options"]["label"], "exp-7")
                self.assertEqual(state["options"]["review_variant"], "grouped-6")
                self.assertEqual(state["git"]["commit"], state["_head"])
                self.assertEqual(len(state["git"]["commit"]), 40)
                self.assertIs(state["git"]["dirty"], False)
                self.assertTrue(state["git"]["aw_version"])

    def test_unlabeled_run_and_dirty_tree(self) -> None:
        state = self._state(oc_runipd, [], dirty=True)
        self.assertIsNone(state["options"]["label"])
        self.assertIsNone(state["options"]["review_variant"])
        self.assertIs(state["git"]["dirty"], True)


if __name__ == "__main__":
    unittest.main()
