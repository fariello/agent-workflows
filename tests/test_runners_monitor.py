"""Tests for runners_monitor (runner journey and process-tree resource tracking).

Tests observable behavior and outcomes:
- RunnerInfo dataclass conversion and data integrity
- Activity classification (pytest, git, aw, agent LLM turns, idle coordination)
- Journey information extraction from run directories
- Active runner discovery via live lock records
- Table rendering and summary aggregation
- CLI entry points under --once, --json, and --agent flags
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli, pwatch, runners_monitor
from agent_workflows.run_viewer import HOLDER_LIVE, HOLDER_NONE


def test_format_bytes() -> None:
    assert runners_monitor.format_bytes(512 * 1024) == "512K"
    assert runners_monitor.format_bytes(250 * 1024 * 1024) == "250M"
    assert runners_monitor.format_bytes(int(3.5 * 1024 * 1024 * 1024)) == "3.5G"


def test_format_time_mmss() -> None:
    assert runners_monitor.format_time_mmss(45) == "00:45"
    assert runners_monitor.format_time_mmss(125) == "02:05"
    assert runners_monitor.format_time_mmss(3665) == "01:01:05"


def test_runner_info_to_dict(tmp_path: Path) -> None:
    info = runners_monitor.RunnerInfo(
        pid=1001,
        run_id="run-20261007T120000Z-1001",
        run_dir=tmp_path / "run-20261007T120000Z-1001",
        host="agy",
        step_str="3/10",
        setid="testset",
        id6="abc123",
        action="execute",
        attempt=2,
        status="running",
        activity="pytest (4 processes)",
        cpu_pct=150.5,
        cum_cpu_sec=75.2,
        rss_bytes=1024 * 1024 * 500,
        num_procs=5,
        descendant_pids={1002, 1003},
        total_cpus=4,
    )
    d = info.to_dict()
    assert d["pid"] == 1001
    assert d["run_id"] == "run-20261007T120000Z-1001"
    assert d["host"] == "agy"
    assert d["step"] == "3/10"
    assert d["setid"] == "testset"
    assert d["id6"] == "abc123"
    assert d["action"] == "execute"
    assert d["attempt"] == 2
    assert d["status"] == "running"
    assert d["activity"] == "pytest (4 processes)"
    assert d["cpu_percent"] == 150.5
    assert d["system_cpu_percent"] == 37.6
    assert d["total_cpus"] == 4
    assert d["cumulative_cpu_seconds"] == 75.2
    assert d["rss_bytes"] == 524288000
    assert d["num_processes"] == 5
    assert d["descendant_pids"] == [1002, 1003]


def test_classify_activity() -> None:
    root_pid = 100

    # Case 1: Idle runner with only root process
    procs = {
        100: pwatch.Process(
            pid=100,
            ppid=1,
            name="python3",
            cmdline=["python3", "-m", "agent_workflows.cli", "agy", "run", "all"],
        ),
    }
    assert (
        runners_monitor.classify_activity(root_pid, set(), procs)
        == "idle / coordinating"
    )

    # Case 2: Running pytest
    procs[101] = pwatch.Process(
        pid=101,
        ppid=100,
        name="pytest",
        cmdline=["python3", "-m", "pytest", "tests/test_foo.py"],
    )
    procs[102] = pwatch.Process(
        pid=102,
        ppid=101,
        name="python3",
        cmdline=["python3", "-m", "pytest", "tests/test_foo.py", "-n", "auto"],
    )
    assert "pytest" in runners_monitor.classify_activity(root_pid, {101, 102}, procs)

    # Case 3: Git operations
    procs_git = {
        100: pwatch.Process(
            pid=100,
            ppid=1,
            name="python3",
            cmdline=["python3", "-m", "agent_workflows.cli", "agy", "run", "all"],
        ),
        103: pwatch.Process(
            pid=103, ppid=100, name="git", cmdline=["git", "commit", "-m", "wip"]
        ),
    }
    assert "git (commit)" in runners_monitor.classify_activity(
        root_pid, {103}, procs_git
    )

    # Case 4: Agent turn
    procs_agent = {
        100: pwatch.Process(
            pid=100,
            ppid=1,
            name="python3",
            cmdline=["python3", "-m", "agent_workflows.cli", "agy", "run", "all"],
        ),
        104: pwatch.Process(
            pid=104,
            ppid=100,
            name="opencode",
            cmdline=["opencode", "run", "--prompt", "test"],
        ),
    }
    assert "opencode LLM" in runners_monitor.classify_activity(
        root_pid, {104}, procs_agent
    )

    # Case 5: Real aw CLI invocation
    procs_aw = {
        100: pwatch.Process(
            pid=100,
            ppid=1,
            name="python3",
            cmdline=["python3", "-m", "agent_workflows.cli", "agy", "run", "all"],
        ),
        105: pwatch.Process(
            pid=105,
            ppid=100,
            name="aw",
            cmdline=["aw", "check", "--agent"],
        ),
    }
    assert runners_monitor.classify_activity(root_pid, {105}, procs_aw) == "aw (check)"

    # Case 6: Shell script executed by agent tool does NOT get misclassified as aw
    procs_tool = {
        100: pwatch.Process(
            pid=100,
            ppid=1,
            name="python3",
            cmdline=["python3", "-m", "agent_workflows.cli", "agy", "run", "all"],
        ),
        104: pwatch.Process(
            pid=104,
            ppid=100,
            name="opencode",
            cmdline=["opencode", "run"],
        ),
        106: pwatch.Process(
            pid=106,
            ppid=104,
            name="bash",
            cmdline=[
                "bash",
                "-c",
                "for i in 1 2; do PYTHONPATH=. python3 -c 'import agent_workflows'; done",
            ],
        ),
    }
    assert (
        runners_monitor.classify_activity(root_pid, {104, 106}, procs_tool)
        == "agent tool (bash)"
    )


def test_extract_journey_info(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-test"
    run_dir.mkdir()

    # Empty directory fallback
    step_str, setid, id6, action, attempt, host = runners_monitor.extract_journey_info(
        run_dir
    )
    assert step_str == "1/?"
    assert setid == "-"
    assert id6 == "-"
    assert action == "execute"
    assert host == "unknown"

    # Populated files
    (run_dir / "manifest.json").write_text(
        json.dumps({"host": "opencode"}), encoding="utf-8"
    )
    (run_dir / "state.json").write_text(
        json.dumps(
            {
                "queue": ["p1", "p2", "p3", "p4", "p5"],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text(
        json.dumps(
            {
                "id6": "xyz789",
                "setid": "orderset",
                "action": "review",
                "attempt": 2,
                "host": "opencode",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    step_str, setid, id6, action, attempt, host = runners_monitor.extract_journey_info(
        run_dir
    )
    assert step_str == "1/5"
    assert setid == "orderset"
    assert id6 == "xyz789"
    assert action == "review"
    assert attempt == 2
    assert host == "opencode"


def test_find_active_runners(tmp_path: Path) -> None:
    import os

    runs_dir = tmp_path / ".aw" / "records" / "runs"
    runs_dir.mkdir(parents=True)

    my_pid = os.getpid()
    run_a = runs_dir / f"run-20261007T100000Z-{my_pid}"
    run_a.mkdir()
    (run_a / "driver.lock").write_text(json.dumps({"pid": my_pid}), encoding="utf-8")

    run_b = runs_dir / "run-20261007T100000Z-999999"
    run_b.mkdir()
    (run_b / "driver.lock").write_text(json.dumps({"pid": 999999}), encoding="utf-8")

    def mock_holder_state(path: Path) -> str:
        if str(my_pid) in path.name:
            return HOLDER_LIVE
        return HOLDER_NONE

    with patch(
        "agent_workflows.runners_monitor.driver_holder_state",
        side_effect=mock_holder_state,
    ), patch(
        "agent_workflows.runners_monitor.platform_lock.read_lock_record_pid",
        side_effect=lambda p: my_pid if str(my_pid) in str(p) else None,
    ):
        runners = runners_monitor.find_active_runners(tmp_path)

    assert len(runners) == 1
    assert runners[0][0] == my_pid
    assert runners[0][2] == f"run-20261007T100000Z-{my_pid}"


def test_render_runner_table_empty() -> None:
    output = runners_monitor.render_runner_table([], color_enabled=False)
    assert "No active aw runners detected." in output


def test_render_runner_table_with_data(tmp_path: Path) -> None:
    runner = runners_monitor.RunnerInfo(
        pid=9999,
        run_id="run-20261007T100000Z-9999",
        run_dir=tmp_path / "run",
        host="agy",
        step_str="2/15",
        setid="myset",
        id6="myid01",
        action="execute",
        attempt=1,
        status="running",
        activity="pytest (2 processes)",
        cpu_pct=95.0,
        cum_cpu_sec=120.0,
        rss_bytes=1024 * 1024 * 1024,
        num_procs=3,
        descendant_pids={10001, 10002},
    )
    # Multi-CPU system (e.g. 4 CPUs: 95.0% / 4 = 23.8% of all CPUs)
    table = runners_monitor.render_runner_table(
        [runner], color_enabled=False, total_cpus=4
    )
    assert "PID" in table
    assert "RUN ID" in table
    assert "STEP" in table
    assert "SETID" in table
    assert "ID6" in table
    assert "ACTION" in table
    assert "%CPU" in table
    assert "TIME" in table
    assert "RAM" in table
    assert "CURRENT ACTIVITY" in table
    assert "9999" in table
    assert "myset" in table
    assert "myid01" in table
    assert "23.8%" in table
    assert "1.0G" in table
    assert "pytest (2 processes)" in table
    assert (
        "Total: 1 active runner(s), 23.8% of all 4 CPUs (95.0% raw), 1.0G RAM across 3 processes"
        in table
    )

    # Single-CPU system
    table_1 = runners_monitor.render_runner_table(
        [runner], color_enabled=False, total_cpus=1
    )
    assert (
        "Total: 1 active runner(s), 95.0% CPU, 1.0G RAM across 3 processes" in table_1
    )

    # Raw CPU mode
    table_raw = runners_monitor.render_runner_table(
        [runner], color_enabled=False, raw_cpu=True, total_cpus=4
    )
    assert "CPU%" in table_raw
    assert "95.0%" in table_raw
    assert (
        "Total: 1 active runner(s), 95.0% raw CPU (23.8% of all 4 CPUs), 1.0G RAM across 3 processes"
        in table_raw
    )


def test_main_once_json(tmp_path: Path) -> None:
    runs_dir = tmp_path / ".aw" / "records" / "runs"
    runs_dir.mkdir(parents=True)

    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = runners_monitor.main(["--once", "--json", "--repo", str(tmp_path)])

    assert exit_code == 0
    parsed = json.loads(buf.getvalue())
    assert isinstance(parsed, list)


def test_main_once_agent(tmp_path: Path) -> None:
    runs_dir = tmp_path / ".aw" / "records" / "runs"
    runs_dir.mkdir(parents=True)

    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = runners_monitor.main(["--once", "--agent", "--repo", str(tmp_path)])

    assert exit_code == 0


def test_aw_cli_dispatch_runners(tmp_path: Path) -> None:
    runs_dir = tmp_path / ".aw" / "records" / "runs"
    runs_dir.mkdir(parents=True)

    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = cli.main(["runners", "--once", "--json", "--repo", str(tmp_path)])

    assert exit_code == 0
    parsed = json.loads(buf.getvalue())
    assert isinstance(parsed, list)


def test_render_runner_table_multiline_activity_sanitized(tmp_path: Path) -> None:
    runner = runners_monitor.RunnerInfo(
        pid=1234,
        run_id="run-test",
        run_dir=tmp_path / "run",
        activity="aw (for i in 1 2; do\nfrom pathlib import Path\nprint('hello')\ndone)",
        cpu_pct=10.0,
    )
    table = runners_monitor.render_runner_table(
        [runner], color_enabled=False, width=120
    )
    lines = table.split("\n")
    # Table should have exactly 5 lines: header, separator, 1 row, separator, summary
    assert len(lines) == 5
    # The row itself should be on a single line with whitespace collapsed
    row = lines[2]
    assert "\n" not in row
    assert "for i in 1 2; do from pathlib" in row or "..." in row


def test_runners_tab_completion() -> None:
    from agent_workflows import completion

    p = cli._build_parser()
    tree = completion.introspect_cli_tree(p)
    assert "runners" in tree["subcommands"]
    flags = [f["flag"] for f in tree["subcommands"]["runners"]["flags"]]
    assert "--interval" in flags
    assert "--once" in flags
    assert "--tree" in flags
    assert "--raw-cpu" in flags
    assert "--width" in flags
    assert "-i" in flags
    assert "-t" in flags

    # Dynamic completion parity for flags
    dyn = completion.complete_query(["aw", "runners", "--"], 2)
    assert "--interval" in dyn
    assert "--once" in dyn
    assert "--raw-cpu" in dyn
    assert "--tree" in dyn
    assert "--width" in dyn
