"""Behavioral tests for `aw-profile` (`collect`, `pack`, `ingest`, zstd traces, de-identification)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import aw_profile, platform_lock

_ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def _run_cli(argv: list[str]) -> tuple[str, str, int]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = aw_profile.main(argv)
    return out.getvalue(), err.getvalue(), rc


def _write_oc_run(
    runs_parent: Path,
    run_id: str,
    *,
    repo_label: str = "/secret/private-org/secret-repo",
    created_at: str = "2026-11-20T10:00:00Z",
    status: str = "executed",
    extra_session_lines: list[dict[str, Any]] | None = None,
) -> Path:
    rd = runs_parent / run_id
    (rd / "sessions").mkdir(parents=True, exist_ok=True)
    (rd / "telemetry").mkdir(parents=True, exist_ok=True)
    session_file = rd / "sessions" / "01-ab1234-attempt-1.jsonl"

    lines: list[dict[str, Any]] = [
        {
            "type": "step_start",
            "timestamp": 1763632810000,
            "sessionID": "ses_oc1",
            "part": {},
        },
        {
            "type": "tool_use",
            "timestamp": 1763632811500,
            "sessionID": "ses_oc1",
            "part": {
                "tool": "read",
                "state": {
                    "status": "completed",
                    "input": {
                        "filePath": f"{repo_label}/agent_workflows/secret_module.py"
                    },
                    "output": "SENSITIVE_SOURCE_CODE_CONTENT_XYZ123",
                    "time": {"start": 1763632810200, "end": 1763632810450},
                },
            },
        },
        {
            "type": "tool_use",
            "timestamp": 1763632814000,
            "sessionID": "ses_oc1",
            "part": {
                "tool": "bash",
                "state": {
                    "status": "error",
                    "input": {
                        "command": "cd /secret/private-org && pytest tests/test_secret.py -k SECRET_TOKEN_999"
                    },
                    "output": "FAILED SECRET_STDOUT_DUMP",
                    "error": "Command failed with exit code 1",
                    "metadata": {"exit": 1},
                    "time": {"start": 1763632811600, "end": 1763632813900},
                },
            },
        },
        {
            "type": "step_finish",
            "timestamp": 1763632815000,
            "sessionID": "ses_oc1",
            "part": {
                "cost": 0.042,
                "tokens": {
                    "input": 1200,
                    "output": 300,
                    "reasoning": 500,
                    "cache": {"read": 8000, "write": 400},
                },
            },
        },
    ]
    if extra_session_lines:
        lines.extend(extra_session_lines)
    session_file.write_text(
        "\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8"
    )

    state: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": created_at,
        "updated_at": "2026-11-20T10:05:00Z",
        "repo": repo_label,
        "driver": {
            "id": "oc_runipd",
            "path": f"{repo_label}/agent_workflows/oc_runipd.py",
        },
        "options": {
            "model": "anthropic/claude-opus-4",
            "variant": "high",
            "review_mode": "single",
            "isolate_execute": True,
            "retry_budget": 2,
            "stall_timeout": 1800,
        },
        "startup_timings": {
            "invocation_kind": "start",
            "startup_to_first_output_seconds": 1.25,
            "startup_to_first_question_seconds": 3.5,
            "startup_to_first_execution_seconds": 9.75,
            "first_output_to_first_question_seconds": 2.25,
            "first_question_to_first_execution_seconds": 6.25,
            "first_output_to_first_execution_seconds": 8.5,
        },
        "queue": [
            {
                "id6": "ab1234",
                "setid": "secretset",
                "order": 1,
                "action": "execute",
                "status": status,
                "disposition": "completed",
                "landed": True,
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-11-20T10:00:10Z",
                        "ended_at": "2026-11-20T10:04:50Z",
                        "log": str(session_file),
                        "exit_code": 0,
                    }
                ],
            }
        ],
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (rd / "events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {"at": created_at, "event": "run-created", "note": "SECRET_NOTE"}
                ),
                json.dumps(
                    {
                        "at": "2026-11-20T10:00:10Z",
                        "event": "ipd-started",
                        "id6": "ab1234",
                        "attempt": 1,
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (rd / "telemetry" / "session.jsonl").write_text(
        json.dumps(
            {
                "at": "2026-11-20T10:01:00Z",
                "event": "sample",
                "cpu_seconds": 12.5,
                "max_rss_bytes": 104857600,
                "load_average": 1.42,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return rd


def _write_agy_run(runs_parent: Path, run_id: str) -> Path:
    rd = runs_parent / run_id
    (rd / "sessions").mkdir(parents=True, exist_ok=True)
    session_file = rd / "sessions" / "01-cd5678-attempt-1.jsonl"
    lines = [
        {"event": "init", "conversation_id": "conv-agy-1"},
        # Streaming non-terminal delta (MUST be ignored so steps aren't overcounted!)
        {
            "event": "step_update",
            "step_update": {
                "step_index": 1,
                "step_type": "agent_response",
                "state": "RUNNING",
                "text_delta": "PRIVATE_THINKING_TEXT",
            },
        },
        # Terminal agent_response: Antigravity output_tokens=900 INCLUDES thinking_tokens=600 -> visible output=300
        {
            "event": "step_update",
            "step_update": {
                "step_index": 1,
                "step_type": "agent_response",
                "state": "DONE",
                "duration_seconds": 4.2,
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 900,
                    "thinking_tokens": 600,
                    "cache_read_tokens": 5000,
                },
            },
        },
        {
            "event": "step_update",
            "step_update": {
                "step_index": 2,
                "step_type": "tool",
                "state": "DONE",
                "duration_seconds": 1.35,
                "tool_name": "run_command",
                "tool_info": {
                    "parameters": {"CommandLine": "aw ipd set approved cd5678"},
                    "output": "ok SECRET_TOOL_OUT",
                },
            },
        },
    ]
    session_file.write_text(
        "\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8"
    )
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": "2026-11-20T11:00:00Z",
        "updated_at": "2026-11-20T11:03:00Z",
        "repo": "/secret/agy-repo",
        "driver": {
            "id": "agy_runipd",
            "path": "/secret/agy-repo/agent_workflows/agy_runipd.py",
        },
        "options": {"model": "gemini-4-neon-high"},
        "queue": [
            {
                "id6": "cd5678",
                "setid": "agyset",
                "order": 1,
                "action": "review",
                "status": "reviewed",
                "attempts": [
                    {
                        "number": 1,
                        "started_at": "2026-11-20T11:00:05Z",
                        "ended_at": "2026-11-20T11:02:55Z",
                        "log": str(session_file),
                    }
                ],
            }
        ],
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (rd / "events.jsonl").write_text(
        json.dumps({"at": "2026-11-20T11:00:00Z", "event": "run-created"}) + "\n",
        encoding="utf-8",
    )
    return rd


class AwProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_zstd_roundtrip_and_magic_header(self) -> None:
        raw = json.dumps({"hello": "world", "nums": list(range(100))}).encode("utf-8")
        comp = aw_profile.zstd_compress(raw)
        self.assertTrue(comp.startswith(_ZSTD_MAGIC))
        self.assertEqual(aw_profile.zstd_decompress(comp), raw)

    def test_collect_oc_and_agy_extracts_deep_tables_and_strips_all_sensitive_strings(
        self,
    ) -> None:
        runs_dir = self.root / "runs"
        _write_oc_run(runs_dir, "run-20261120T100000Z-1001")
        _write_agy_run(runs_dir, "run-20261120T110000Z-2002")
        cache_dir = self.root / "cache"

        out, err, rc = _run_cli(
            [
                "collect",
                "--runs-dir",
                str(runs_dir),
                "--cache-dir",
                str(cache_dir),
                "--json",
            ]
        )
        self.assertEqual(rc, 0, out + err)
        summary = json.loads(out)
        self.assertEqual(summary["discovered"], 2)
        self.assertEqual(summary["extracted"], 2)
        self.assertEqual(summary["cached_hits"], 0)
        self.assertEqual(summary["errors"], 0)

        oc_zst = cache_dir / "runs" / "run-20261120T100000Z-1001.trace.json.zst"
        agy_zst = cache_dir / "runs" / "run-20261120T110000Z-2002.trace.json.zst"
        self.assertTrue(oc_zst.read_bytes().startswith(_ZSTD_MAGIC))
        self.assertTrue(agy_zst.read_bytes().startswith(_ZSTD_MAGIC))

        oc_raw_text = aw_profile.zstd_decompress(oc_zst.read_bytes()).decode("utf-8")
        agy_raw_text = aw_profile.zstd_decompress(agy_zst.read_bytes()).decode("utf-8")

        # Strict de-identification check: NONE of the sensitive canary strings survive.
        for canary in (
            "private-org",
            "secret-repo",
            "secret_module.py",
            "SENSITIVE_SOURCE_CODE_CONTENT_XYZ123",
            "SECRET_TOKEN_999",
            "SECRET_STDOUT_DUMP",
            "SECRET_NOTE",
            "secretset",
            "ab1234",
            "PRIVATE_THINKING_TEXT",
            "SECRET_TOOL_OUT",
            "cd5678",
        ):
            self.assertNotIn(canary, oc_raw_text)
            self.assertNotIn(canary, agy_raw_text)

        oc_trace = json.loads(oc_raw_text)
        self.assertEqual(aw_profile.validate_trace(oc_trace), [])
        self.assertEqual(oc_trace["run"]["host"], "oc")
        self.assertEqual(
            oc_trace["run"]["startup_timings"]["startup_to_first_execution_seconds"],
            9.75,
        )
        self.assertEqual(len(oc_trace["steps"]), 1)
        self.assertEqual(oc_trace["steps"][0]["tokens_input"], 1200)
        self.assertEqual(oc_trace["steps"][0]["tokens_cache_read"], 8000)
        self.assertEqual(oc_trace["steps"][0]["context_size"], 9600)
        self.assertEqual(len(oc_trace["tool_calls"]), 2)
        read_call, bash_call = oc_trace["tool_calls"]
        self.assertEqual(read_call["tool_category"], "read")
        self.assertTrue(read_call["target_file_id"].startswith("file:"))
        self.assertEqual(read_call["file_ext"], ".py")
        self.assertEqual(bash_call["tool_category"], "shell")
        self.assertEqual(bash_call["cmd_kind"], "test")
        self.assertEqual(bash_call["cmd_families"], ["pytest"])
        self.assertTrue(bash_call["is_error"])
        self.assertEqual(bash_call["error_class"], "nonzero-exit")
        # Telemetry event preserved
        tel_events = [
            e for e in oc_trace["driver_events"] if e["source"] == "telemetry"
        ]
        self.assertEqual(len(tel_events), 1)
        self.assertEqual(tel_events[0]["max_rss_bytes"], 104857600)

        agy_trace = json.loads(agy_raw_text)
        self.assertEqual(aw_profile.validate_trace(agy_trace), [])
        self.assertEqual(agy_trace["run"]["host"], "agy")
        self.assertEqual(len(agy_trace["steps"]), 1)
        # Antigravity thinking tokens NOT double-counted!
        self.assertEqual(agy_trace["steps"][0]["tokens_output"], 300)
        self.assertEqual(agy_trace["steps"][0]["tokens_reasoning"], 600)
        self.assertEqual(agy_trace["attempts"][0]["thinking_in_output"], True)
        self.assertEqual(len(agy_trace["tool_calls"]), 1)
        self.assertEqual(agy_trace["tool_calls"][0]["cmd_families"], ["aw ipd set"])

    def test_watermark_cache_hit_resume_invalidation_and_active_lock_skip(self) -> None:
        runs_dir = self.root / "runs-wm"
        r1 = _write_oc_run(runs_dir, "run-20261120T100000Z-3001")
        r2 = _write_agy_run(runs_dir, "run-20261120T110000Z-3002")
        cache_dir = self.root / "cache-wm"

        # 1. Initial collect
        res1 = aw_profile.collect_runs(runs_dirs=[runs_dir], cache_dir=cache_dir)
        self.assertEqual(res1["extracted"], 2)
        self.assertEqual(res1["cached_hits"], 0)

        # 2. Second collect -> 100% cache hits
        res2 = aw_profile.collect_runs(runs_dirs=[runs_dir], cache_dir=cache_dir)
        self.assertEqual(res2["extracted"], 0)
        self.assertEqual(res2["updated"], 0)
        self.assertEqual(res2["cached_hits"], 2)

        # 3. Simulate `resume` appending a new session file & advancing mtime on r1
        s2 = r1 / "sessions" / "01-ab1234-attempt-2.jsonl"
        s2.write_text(
            json.dumps(
                {
                    "type": "step_finish",
                    "timestamp": 1763632900000,
                    "sessionID": "ses_oc2",
                    "part": {"tokens": {"input": 500, "output": 100}},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        s2_stat = s2.stat()
        os.utime(s2, ns=(s2_stat.st_atime_ns, s2_stat.st_mtime_ns + 1_000_000_000))
        res3 = aw_profile.collect_runs(runs_dirs=[runs_dir], cache_dir=cache_dir)
        self.assertEqual(res3["updated"], 1)
        self.assertEqual(res3["cached_hits"], 1)

        # 4. Hold driver.lock on r2 -> skipped by default, included with --include-active
        handle = platform_lock.acquire(r2 / "driver.lock")
        try:
            res4 = aw_profile.collect_runs(
                runs_dirs=[runs_dir], cache_dir=cache_dir, rebuild=True
            )
            self.assertEqual(res4["skipped_active"], 1)
            self.assertEqual(res4["updated"], 1)

            res5 = aw_profile.collect_runs(
                runs_dirs=[runs_dir],
                cache_dir=cache_dir,
                include_active=True,
                rebuild=True,
            )
            self.assertEqual(res5["skipped_active"], 0)
            self.assertEqual(res5["updated"], 2)
        finally:
            handle.release()

    def test_scan_follows_symlinked_root_and_prunes_analytics_worktrees_and_non_aw_runs(
        self,
    ) -> None:
        real_vc = self.root / "real-vc"
        repo_runs = real_vc / "myrepo" / ".aw" / "records" / "runs"
        _write_oc_run(repo_runs, "run-20261120T100000Z-4001")
        # Must be ignored: analytics snapshot, worktree run, unrelated run-* dir
        _write_oc_run(
            repo_runs / "analytics" / "snapshots" / "s1",
            "run-20261120T100000Z-9991",
        )
        (repo_runs / "analytics" / "manifest.json").write_text("{}", encoding="utf-8")
        _write_oc_run(
            real_vc
            / "myrepo"
            / ".aw"
            / "worktrees"
            / "wt1"
            / ".aw"
            / "records"
            / "runs",
            "run-20261120T100000Z-9992",
        )
        unrelated = real_vc / "other-project" / "run-benchmark-1"
        unrelated.mkdir(parents=True)
        (unrelated / "notes.txt").write_text("not an aw run\n", encoding="utf-8")

        vc_link = self.root / "VC"
        vc_link.symlink_to(real_vc)

        found = aw_profile.scan_runs_dirs(vc_link)
        self.assertEqual([p.name for p in found], ["run-20261120T100000Z-4001"])

    def test_pack_inspect_and_ingest_upgrade_dedup_collision_and_security_refusals(
        self,
    ) -> None:
        server_a_runs = self.root / "server-a-runs"
        r_a = _write_oc_run(
            server_a_runs,
            "run-20261120T100000Z-5001",
            created_at="2026-11-20T10:00:00Z",
        )
        cache_a = self.root / "cache-a"
        cache_central = self.root / "cache-central"

        aw_profile.collect_runs(runs_dirs=[server_a_runs], cache_dir=cache_a)

        # --inspect prints de-identified JSON without writing any file
        out_ins, err_ins, rc_ins = _run_cli(
            ["pack", "--cache-dir", str(cache_a), "--inspect", "1"]
        )
        self.assertEqual(rc_ins, 0, out_ins + err_ins)
        samples = json.loads(out_ins)
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]["run"]["run_id"], "run-20261120T100000Z-5001")

        # Pack to .tar.zst and ingest into central cache
        bundle1 = self.root / "server-a-v1.tar.zst"
        out_p, err_p, rc_p = _run_cli(
            ["pack", "--cache-dir", str(cache_a), "--out", str(bundle1), "--json"]
        )
        self.assertEqual(rc_p, 0, out_p + err_p)
        self.assertTrue(bundle1.read_bytes().startswith(_ZSTD_MAGIC))

        out_i1, err_i1, rc_i1 = _run_cli(
            [
                "ingest",
                str(bundle1),
                "--cache-dir",
                str(cache_central),
                "--batch",
                "server-a",
                "--json",
            ]
        )
        self.assertEqual(rc_i1, 0, out_i1 + err_i1)
        i1 = json.loads(out_i1)
        self.assertEqual(i1["added"], 1)
        self.assertEqual(i1["rejected"], 0)

        # Re-ingesting the exact same bundle skips it
        i2 = aw_profile.ingest_bundles(
            [bundle1], cache_dir=cache_central, batch="server-a"
        )
        self.assertEqual(i2["added"], 0)
        self.assertEqual(i2["upgraded"], 0)
        self.assertEqual(i2["skipped_same_or_older"], 1)

        # Simulate resume on server A -> re-collect -> re-pack -> ingest upgrades!
        ev_path = r_a / "events.jsonl"
        prev_ev_stat = ev_path.stat()
        ev_path.write_text(
            ev_path.read_text(encoding="utf-8")
            + json.dumps(
                {
                    "at": "2026-11-20T12:00:00Z",
                    "event": "run-startup-timings",
                    "invocation_kind": "resume",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        os.utime(
            ev_path,
            ns=(prev_ev_stat.st_atime_ns, prev_ev_stat.st_mtime_ns + 1_000_000_000),
        )
        aw_profile.collect_runs(runs_dirs=[server_a_runs], cache_dir=cache_a)
        bundle2 = self.root / "server-a-v2.tar.zst"
        aw_profile.pack_traces(cache_dir=cache_a, out_path=bundle2)
        i3 = aw_profile.ingest_bundles(
            [bundle2], cache_dir=cache_central, batch="server-a"
        )
        self.assertEqual(i3["upgraded"], 1)

        # Re-ingesting older bundle1 MUST NOT downgrade central cache
        i4 = aw_profile.ingest_bundles(
            [bundle1], cache_dir=cache_central, batch="server-a"
        )
        self.assertEqual(i4["upgraded"], 0)
        self.assertEqual(i4["skipped_same_or_older"], 1)

        # Malicious bundle with path traversal -> refused with exit 2
        bad_tar = io.BytesIO()
        with tarfile.open(fileobj=bad_tar, mode="w") as tf:
            data = b"{}"
            ti = tarfile.TarInfo(name="../escape.trace.json")
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
        bad_bundle = self.root / "evil.tar.zst"
        bad_bundle.write_bytes(aw_profile.zstd_compress(bad_tar.getvalue()))
        _out_b, err_b, rc_b = _run_cli(
            ["ingest", str(bad_bundle), "--cache-dir", str(cache_central)]
        )
        self.assertEqual(rc_b, 2)
        self.assertIn("unsafe archive member path", err_b)

        # Tampered contributor trace carrying a raw path -> rejected (exit 1)
        tampered = json.loads(json.dumps(samples[0]))
        tampered["run"]["model"] = "/home/user/secret/model"
        tampered_tar = io.BytesIO()
        with tarfile.open(fileobj=tampered_tar, mode="w") as tf:
            raw_t = json.dumps(tampered).encode("utf-8")
            ti = tarfile.TarInfo(name="traces/bad.trace.json")
            ti.size = len(raw_t)
            tf.addfile(ti, io.BytesIO(raw_t))
        tampered_bundle = self.root / "tampered.tar.zst"
        tampered_bundle.write_bytes(aw_profile.zstd_compress(tampered_tar.getvalue()))
        out_t, _err_t, rc_t = _run_cli(
            [
                "ingest",
                str(tampered_bundle),
                "--cache-dir",
                str(cache_central),
                "--json",
            ]
        )
        self.assertEqual(rc_t, 1)
        self.assertEqual(json.loads(out_t)["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
