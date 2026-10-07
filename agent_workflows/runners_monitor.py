"""Runner monitoring, journey tracking, and process-tree resource inspection.

Provides real-time visibility into active agent-workflows (`aw`) runners:
where each runner is in its journey (run ID, step N/M, setid, id6, action, attempt),
what each runner is actively doing (e.g. running pytest, agent LLM turn, git commit),
and total CPU% and memory (RSS) consumed across the entire process tree under each runner.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_workflows import platform_lock, pwatch, term
from agent_workflows.run_viewer import HOLDER_LIVE, driver_holder_state


@dataclass
class RunnerInfo:
    """Snapshot of a live runner's state, journey progress, and resource consumption."""

    pid: int
    run_id: str
    run_dir: Path
    host: str = "unknown"
    step_str: str = "-/-"
    setid: str = "-"
    id6: str = "-"
    action: str = "-"
    attempt: int = 1
    status: str = "running"
    activity: str = "idle / coordinating"
    cpu_pct: float = 0.0
    cum_cpu_sec: float = 0.0
    rss_bytes: int = 0
    num_procs: int = 1
    descendant_pids: set[int] = field(default_factory=set)
    total_cpus: int = field(default_factory=lambda: os.cpu_count() or 1)

    @property
    def system_cpu_pct(self) -> float:
        """Percentage of total system CPU capacity across all CPUs."""
        return self.cpu_pct / max(1, self.total_cpus)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "pid": self.pid,
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "host": self.host,
            "step": self.step_str,
            "setid": self.setid,
            "id6": self.id6,
            "action": self.action,
            "attempt": self.attempt,
            "status": self.status,
            "activity": self.activity,
            "cpu_percent": round(self.cpu_pct, 1),
            "system_cpu_percent": round(self.system_cpu_pct, 1),
            "total_cpus": self.total_cpus,
            "cumulative_cpu_seconds": round(self.cum_cpu_sec, 1),
            "rss_bytes": self.rss_bytes,
            "num_processes": self.num_procs,
            "descendant_pids": sorted(self.descendant_pids),
        }


def format_bytes(num_bytes: int) -> str:
    """Format byte count into compact human-readable string (e.g. '450M', '3.2G')."""
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.0f}K"
    if num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.0f}M"
    return f"{num_bytes / (1024 * 1024 * 1024):.1f}G"


def format_time_mmss(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS."""
    total_secs = int(max(0.0, seconds))
    mins, secs = divmod(total_secs, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def find_active_runners(repo: Path) -> list[tuple[int, Path, str]]:
    """Discover active runner processes holding live locks under .aw/records/runs.

    Returns a list of tuples: (pid, run_dir, run_id).
    """
    runs_dir = repo / ".aw" / "records" / "runs"
    if not runs_dir.is_dir():
        # Check if we are inside a linked git worktree
        git_file = repo / ".git"
        if git_file.is_file():
            try:
                content = git_file.read_text(encoding="utf-8").strip()
                if content.startswith("gitdir:"):
                    gitdir = Path(content.split(":", 1)[1].strip()).resolve()
                    primary_repo = gitdir.parent.parent.parent
                    runs_dir = primary_repo / ".aw" / "records" / "runs"
            except Exception:
                pass

    if not runs_dir.is_dir():
        return []

    active: list[tuple[int, Path, str]] = []
    seen_pids: set[int] = set()

    for lock_path in sorted(runs_dir.glob("*/driver.lock"), reverse=True):
        run_dir = lock_path.parent
        # Authoritative OS flock probe
        if driver_holder_state(run_dir) != HOLDER_LIVE:
            continue
        pid = platform_lock.read_lock_record_pid(lock_path)
        if pid is None or pid in seen_pids:
            continue
        # Verify process is truly alive in /proc
        if not (Path("/proc") / str(pid)).is_dir():
            continue

        seen_pids.add(pid)
        active.append((pid, run_dir, run_dir.name))

    return active


def extract_journey_info(run_dir: Path) -> tuple[str, str, str, str, int, str]:
    """Extract journey progress and active plan metadata from a run directory.

    Returns: (step_str, setid, id6, action, attempt, host)
    """
    queue: list[str] = []
    host = "unknown"

    state_file = run_dir / "state.json"
    if state_file.is_file():
        try:
            s_data = json.loads(
                state_file.read_text(encoding="utf-8", errors="replace")
            )
            queue = s_data.get("queue", [])
            host_cap = s_data.get("host_capabilities", {})
            if isinstance(host_cap, dict) and host_cap.get("product"):
                host = str(host_cap["product"]).lower()
        except Exception:
            pass

    plans_meta: dict[str, Any] = {}
    manifest_file = run_dir / "manifest.json"
    if manifest_file.is_file():
        try:
            m_data = json.loads(
                manifest_file.read_text(encoding="utf-8", errors="replace")
            )
            plans_meta = m_data.get("plans", {})
            if host == "unknown" and m_data.get("host"):
                host = str(m_data["host"]).lower()
        except Exception:
            pass

    last_id6 = "-"
    last_setid = "-"
    last_action = "execute"
    last_attempt = 1

    events_file = run_dir / "events.jsonl"
    if events_file.is_file():
        try:
            with open(events_file, encoding="utf-8", errors="replace") as ef:
                for line in ef:
                    line = line.strip()
                    if not line:
                        continue
                    ev = json.loads(line)
                    if "id6" in ev and ev["id6"]:
                        last_id6 = ev["id6"]
                    if "setid" in ev and ev["setid"]:
                        last_setid = ev["setid"]
                    if "action" in ev and ev["action"]:
                        last_action = ev["action"]
                    if "attempt" in ev and ev["attempt"]:
                        try:
                            last_attempt = int(ev["attempt"])
                        except (ValueError, TypeError):
                            pass
                    if "host" in ev and ev["host"]:
                        host = str(ev["host"]).lower()
        except Exception:
            pass

    # Count completed outcomes
    outcomes_dir = run_dir / "outcomes"
    outcomes_count = 0
    if outcomes_dir.is_dir():
        for f in outcomes_dir.glob("[0-9]*.json"):
            if not f.name.endswith("-verification.json"):
                outcomes_count += 1

    step_num = outcomes_count + 1
    total_q = len(queue)
    step_str = f"{step_num}/{total_q}" if total_q > 0 else f"{step_num}/?"

    # Resolve setid from manifest if not found in events
    if last_setid == "-" and last_id6 in plans_meta:
        last_setid = plans_meta[last_id6].get("set", "-")

    return step_str, last_setid, last_id6, last_action, last_attempt, host


def classify_activity(
    runner_pid: int,
    descendant_pids: set[int],
    processes: dict[int, pwatch.Process],
    host: str = "unknown",
) -> str:
    """Determine what the runner process tree is actively doing."""
    pytest_procs: list[pwatch.Process] = []
    git_procs: list[pwatch.Process] = []
    aw_procs: list[pwatch.Process] = []
    agent_procs: list[pwatch.Process] = []

    for pid in descendant_pids:
        proc = processes.get(pid)
        if proc is None:
            continue
        cmd_str = " ".join(proc.cmdline) if proc.cmdline else ""
        comm = proc.name.lower()

        if "pytest" in cmd_str or comm == "pytest":
            pytest_procs.append(proc)
        elif comm == "git" or (proc.arguments and proc.arguments[0] == "git"):
            git_procs.append(proc)
        elif ("agent_workflows" in cmd_str or comm == "aw") and pid != runner_pid:
            aw_procs.append(proc)
        elif comm in ("agy", "antigravity", "opencode", "claude") and pid != runner_pid:
            agent_procs.append(proc)

    if pytest_procs:
        count = len(pytest_procs)
        # Try to find target test file from arguments
        test_file = ""
        for p in pytest_procs:
            for arg in p.arguments:
                if arg.startswith("tests/") and arg.endswith(".py"):
                    test_file = Path(arg).name
                    break
            if test_file:
                break
        if test_file:
            return f"pytest ({count} procs: {test_file})"
        return f"pytest ({count} processes)"

    if git_procs:
        git_proc = git_procs[0]
        subcmd = ""
        for arg in git_proc.arguments:
            if not arg.startswith("-"):
                subcmd = arg
                break
        return f"git ({subcmd or 'running'})"

    if aw_procs:
        aw_proc = aw_procs[0]
        subcmd = ""
        for arg in aw_proc.arguments:
            if arg not in ("-m", "agent_workflows") and not arg.startswith("-"):
                subcmd = arg
                break
        return f"aw ({subcmd or 'command'})"

    if agent_procs:
        agent_name = agent_procs[0].name
        if "agy" in agent_name or "antigravity" in agent_name:
            return "agent turn (antigravity/gemini LLM)"
        if "opencode" in agent_name:
            return "agent turn (opencode LLM)"
        return f"agent turn ({agent_name})"

    return "idle / coordinating"


def sample_runners(
    repo: Path,
    sample_interval: float = 0.3,
) -> list[RunnerInfo]:
    """Sample active runners and compute process-tree CPU and memory usage."""
    raw_runners = find_active_runners(repo)
    if not raw_runners:
        return []

    clk_tck = os.sysconf(os.sysconf_names.get("SC_CLK_TCK", 100))

    # First sample
    procs_t1 = pwatch.read_processes()
    t1 = time.monotonic()

    if sample_interval > 0:
        time.sleep(sample_interval)

    # Second sample
    procs_t2 = pwatch.read_processes()
    t2 = time.monotonic()
    dt = max(0.001, t2 - t1)

    # Build parent -> children map for t2
    child_map: dict[int, list[int]] = {}
    for pid, proc in procs_t2.items():
        child_map.setdefault(proc.ppid, []).append(pid)

    def collect_descendants(root_pid: int) -> set[int]:
        desc = {root_pid}
        stack = [root_pid]
        while stack:
            curr = stack.pop()
            for child_pid in child_map.get(curr, []):
                if child_pid not in desc:
                    desc.add(child_pid)
                    stack.append(child_pid)
        return desc

    runners: list[RunnerInfo] = []

    for rpid, run_dir, run_id in raw_runners:
        descendants = collect_descendants(rpid)
        step_str, setid, id6, action, attempt, host = extract_journey_info(run_dir)

        total_cum_ticks = 0
        total_delta_ticks = 0
        total_rss = 0

        for dpid in descendants:
            p2 = procs_t2.get(dpid)
            if p2 is not None:
                cum_p2 = p2.utime + p2.stime
                total_cum_ticks += cum_p2
                total_rss += p2.rss_bytes
                p1 = procs_t1.get(dpid)
                if p1 is not None:
                    delta = max(0, cum_p2 - (p1.utime + p1.stime))
                    total_delta_ticks += delta

        cpu_pct = (total_delta_ticks / (dt * clk_tck)) * 100.0
        cum_sec = total_cum_ticks / clk_tck if clk_tck > 0 else 0.0
        activity = classify_activity(rpid, descendants, procs_t2, host)

        total_cpus = os.cpu_count() or 1
        info = RunnerInfo(
            pid=rpid,
            run_id=run_id,
            run_dir=run_dir,
            host=host,
            step_str=step_str,
            setid=setid,
            id6=id6,
            action=action,
            attempt=attempt,
            status="running",
            activity=activity,
            cpu_pct=cpu_pct,
            cum_cpu_sec=cum_sec,
            rss_bytes=total_rss,
            num_procs=len(descendants),
            descendant_pids=descendants,
            total_cpus=total_cpus,
        )
        runners.append(info)

    # Sort primarily by CPU% descending, then by PID
    runners.sort(key=lambda r: (-r.cpu_pct, r.pid))
    return runners


def render_runner_table(
    runners: list[RunnerInfo],
    color_enabled: bool = True,
    width: int = 120,
    raw_cpu: bool = False,
    total_cpus: int | None = None,
) -> str:
    """Render formatted summary table for active runners."""
    if not runners:
        return "No active aw runners detected."

    if total_cpus is None:
        if runners and hasattr(runners[0], "total_cpus"):
            total_cpus = runners[0].total_cpus
        else:
            total_cpus = os.cpu_count() or 1

    # ANSI styles
    r = pwatch.C_RESET if color_enabled else ""
    bold = pwatch.C_BOLD if color_enabled else ""
    dim = pwatch.C_DIM if color_enabled else ""
    c_pid = pwatch.C_PID if color_enabled else ""
    c_step = "\033[38;5;81m" if color_enabled else ""
    c_set = "\033[38;5;186m" if color_enabled else ""
    c_id6 = "\033[1;38;5;220m" if color_enabled else ""
    c_act = "\033[38;5;214m" if color_enabled else ""
    c_cpu_high = "\033[1;38;5;203m" if color_enabled else ""
    c_cpu_mid = "\033[38;5;215m" if color_enabled else ""
    c_activity = "\033[38;5;255m" if color_enabled else ""

    show_raw_in_col = not raw_cpu and width >= 115

    if raw_cpu:
        cpu_hdr = f"{'CPU%':>7}"
    elif show_raw_in_col:
        cpu_hdr = f"{'%CPU (RAW)':>13}"
    else:
        cpu_hdr = f"{'%CPU':>7}"

    lines: list[str] = []
    header = (
        f"{'PID':<8} {'RUN ID':<28} {'STEP':<7} {'SETID':<12} "
        f"{'ID6':<8} {'ACTION':<9} {cpu_hdr} {'TIME':>8} {'RAM':>7}  {'CURRENT ACTIVITY'}"
    )
    lines.append(f"{bold}{header}{r}")
    sep_len = min(width, len(pwatch.strip_ansi(header)) + 20)
    lines.append(f"{dim}{'─' * sep_len}{r}")

    tot_cpu = 0.0
    tot_rss = 0
    tot_procs = 0

    for runner in runners:
        tot_cpu += runner.cpu_pct
        tot_rss += runner.rss_bytes
        tot_procs += runner.num_procs

        # CPU color coding
        if runner.cpu_pct >= 100.0:
            cpu_style = c_cpu_high
        elif runner.cpu_pct >= 20.0:
            cpu_style = c_cpu_mid
        else:
            cpu_style = dim

        if raw_cpu:
            cpu_formatted = f"{cpu_style}{runner.cpu_pct:>6.1f}%{r}"
        elif show_raw_in_col:
            sys_pct = runner.cpu_pct / total_cpus
            cpu_formatted = f"{cpu_style}{sys_pct:>5.1f}% ({runner.cpu_pct:>3.0f}%){r}"
        else:
            sys_pct = runner.cpu_pct / total_cpus
            cpu_formatted = f"{cpu_style}{sys_pct:>6.1f}%{r}"

        time_formatted = f"{dim}{format_time_mmss(runner.cum_cpu_sec):>8}{r}"
        ram_formatted = f"{format_bytes(runner.rss_bytes):>7}"
        step_formatted = f"{c_step}{runner.step_str:<7}{r}"
        set_formatted = f"{c_set}{runner.setid:<12}{r}"
        id6_formatted = f"{c_id6}{runner.id6:<8}{r}"
        act_formatted = f"{c_act}{runner.action:<9}{r}"
        pid_formatted = f"{c_pid}{runner.pid:<8}{r}"
        run_formatted = f"{runner.run_id:<28}"
        activity_formatted = f"{c_activity}{runner.activity}{r}"

        row = (
            f"{pid_formatted} {run_formatted} {step_formatted} {set_formatted} "
            f"{id6_formatted} {act_formatted} {cpu_formatted} {time_formatted} {ram_formatted}  {activity_formatted}"
        )
        lines.append(row)

    lines.append(f"{dim}{'─' * sep_len}{r}")

    tot_sys_pct = tot_cpu / total_cpus
    if total_cpus > 1:
        if raw_cpu:
            cpu_summary = (
                f"{tot_cpu:.1f}% raw CPU ({tot_sys_pct:.1f}% of all {total_cpus} CPUs)"
            )
        else:
            cpu_summary = (
                f"{tot_sys_pct:.1f}% of all {total_cpus} CPUs ({tot_cpu:.1f}% raw)"
            )
    else:
        cpu_summary = f"{tot_cpu:.1f}% CPU"

    summary = (
        f"Total: {len(runners)} active runner(s), {cpu_summary}, "
        f"{format_bytes(tot_rss)} RAM across {tot_procs} processes"
    )
    lines.append(f"{bold}{summary}{r}")

    return "\n".join(lines)


def run_table_dashboard(args: argparse.Namespace) -> int:
    """Run runner table dashboard loop (or single snapshot)."""
    repo = Path(getattr(args, "repo", ".") or ".").resolve()
    is_interactive = not getattr(args, "once", False) and sys.stdout.isatty()
    color_enabled = not getattr(args, "no_color", False) and term.should_color(
        sys.stdout
    )
    interval = float(getattr(args, "interval", 2.0))
    width = int(getattr(args, "width", 120))
    raw_cpu = getattr(args, "raw_cpu", False)
    total_cpus = os.cpu_count() or 1

    def stop_cleanly(_sig: int, _frame: object) -> None:
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop_cleanly)
    signal.signal(signal.SIGTERM, stop_cleanly)

    try:
        if is_interactive:
            sys.stdout.write(pwatch.ENTER_ALT_SCREEN)
            sys.stdout.flush()

        while True:
            term_cols = shutil.get_terminal_size((width, 24)).columns
            effective_width = (
                min(width, max(20, term_cols - 1)) if is_interactive else width
            )

            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            runners = sample_runners(repo, sample_interval=min(0.5, interval / 2.0))

            if getattr(args, "json", False):
                print(json.dumps([r.to_dict() for r in runners], indent=2))
                return 0

            if getattr(args, "agent", False):
                for r in runners:
                    record = {
                        "v": "aw.agent/v1",
                        "kind": "runner_status",
                        "at": now_str,
                        "data": r.to_dict(),
                    }
                    print(json.dumps(record))
                return 0

            table = render_runner_table(
                runners,
                color_enabled=color_enabled,
                width=effective_width,
                raw_cpu=raw_cpu,
                total_cpus=total_cpus,
            )

            r = pwatch.C_RESET if color_enabled else ""
            c_banner = pwatch.C_BANNER if color_enabled else ""
            c_dim = pwatch.C_DIM if color_enabled else ""
            c_time = pwatch.C_TIMESTAMP if color_enabled else ""

            header = (
                f"{c_banner}aw runners{r} {c_dim}(every {interval}s | {total_cpus} CPUs){r} {c_dim}──{r} "
                f"{c_time}{now_str}{r}\n\n"
            )

            if is_interactive:
                frame_lines = f"{header}{table}".split("\n")
                frame = "".join(f"{line}{pwatch.CLEAR_LINE}\n" for line in frame_lines)
                sys.stdout.write(f"{pwatch.CURSOR_HOME}{frame}{pwatch.CLEAR_TO_EOS}")
                sys.stdout.flush()
            else:
                sys.stdout.write(f"{header}{table}\n")
                sys.stdout.flush()

            if getattr(args, "once", False):
                return 0

            time.sleep(interval)

    except (KeyboardInterrupt, SystemExit):
        return 0
    finally:
        if is_interactive:
            sys.stdout.write(pwatch.LEAVE_ALT_SCREEN)
            sys.stdout.flush()


def build_parser() -> argparse.ArgumentParser:
    """Build parser for `aw runners` and `tools/watch-runners.py`."""
    parser = argparse.ArgumentParser(
        prog="aw runners",
        description="Monitor active aw runners, their journey state, and subtree CPU/RAM usage.",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=2.0,
        help="seconds between dashboard refreshes (default: 2.0)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="print one snapshot and exit (default when stdout is not a TTY)",
    )
    parser.add_argument(
        "--tree",
        "-t",
        action="store_true",
        help="display full process trees under each runner instead of the summary table",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=120,
        help="maximum display width (default: 120)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI color output",
    )
    parser.add_argument(
        "--raw-cpu",
        action="store_true",
        help="show unscaled per-core CPU percentages instead of percentage of all CPUs",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="output JSON representation",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="output machine-readable JSONL stream (aw.agent/v1)",
    )
    parser.add_argument(
        "--repo",
        "-d",
        type=Path,
        default=Path("."),
        help="target repository root (default: current directory)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for runner monitoring."""
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.tree:
        # Delegate tree visualization directly to pwatch --runners with forwarded settings
        pwatch_argv = ["--runners"]
        if args.once or not sys.stdout.isatty():
            pwatch_argv.append("--once")
        if args.no_color:
            pwatch_argv.append("--no-color")
        if args.interval:
            pwatch_argv.extend(["--interval", str(args.interval)])
        if args.width:
            pwatch_argv.extend(["--width", str(args.width)])
        return pwatch.main(pwatch_argv)

    return run_table_dashboard(args)


if __name__ == "__main__":
    raise SystemExit(main())
