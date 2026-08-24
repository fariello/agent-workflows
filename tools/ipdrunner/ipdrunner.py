#!/usr/bin/env python3
"""Restartable non-interactive OpenCode driver for executing approved IPDs.

This driver manages execution queues for approved IPDs and Sets, storing durable
run records under the repository's `.aw/records/runs/` directory.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
TERMINAL_STATES = {
    "executed",
    "substantially-complete",
    "partial",
    "blocked",
    "dependency-blocked",
    "failed-safely",
    "not-attempted",
}
SUCCESS_STATES = {"executed"}
ID6_RE = re.compile(r"^[a-z0-9]{6}$")


class DriverError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_checked(argv: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise DriverError(
            f"Command failed ({result.returncode}): {shlex.join(argv)}\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def git_common_dir(repo: Path) -> Path:
    raw = run_checked(["git", "rev-parse", "--git-common-dir"], cwd=repo)
    path = Path(raw)
    return path if path.is_absolute() else (repo / path).resolve()


def git_head(repo: Path) -> str:
    return run_checked(["git", "rev-parse", "HEAD"], cwd=repo)


def git_branch(repo: Path) -> str:
    result = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout.strip() if result.returncode == 0 else "(detached)"


def git_status(repo: Path) -> str:
    return run_checked(["git", "status", "--short"], cwd=repo)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DriverError(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DriverError(f"Invalid JSON in {path}: {exc}") from exc


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        dir_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


@contextlib.contextmanager
def run_lock(run_dir: Path):
    lock_path = run_dir / "driver.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DriverError(
                f"Run is already controlled by another process: {run_dir.name}"
            ) from exc
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid={os.getpid()} started={utc_now()}\n")
        handle.flush()
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise DriverError("Unsupported manifest schema_version")
    plans = manifest.get("plans")
    sets = manifest.get("sets")
    if not isinstance(plans, dict) or not isinstance(sets, dict):
        raise DriverError("Manifest must contain object-valued 'plans' and 'sets'")
    for id6, plan in plans.items():
        if not ID6_RE.fullmatch(id6):
            raise DriverError(f"Invalid id6 in manifest: {id6}")
        if not isinstance(plan, dict) or not plan.get("file") or not plan.get("set"):
            raise DriverError(f"Plan {id6} requires file and set")
        dependencies = plan.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise DriverError(f"Plan {id6} dependencies must be a list")
        unknown = [dep for dep in dependencies if dep not in plans]
        if unknown:
            raise DriverError(f"Plan {id6} has unknown dependencies: {unknown}")
    for setid, group in sets.items():
        if not isinstance(group, dict) or not isinstance(group.get("order"), list):
            raise DriverError(f"Set {setid} requires an order list")
        unknown = [id6 for id6 in group["order"] if id6 not in plans]
        if unknown:
            raise DriverError(f"Set {setid} contains unknown plans: {unknown}")
        wrong = [id6 for id6 in group["order"] if plans[id6]["set"] != setid]
        if wrong:
            raise DriverError(f"Set {setid} contains plans assigned elsewhere: {wrong}")


def expand_selectors(manifest: dict[str, Any], selectors: Iterable[str]) -> list[str]:
    plans = manifest["plans"]
    sets = manifest["sets"]
    expanded: list[str] = []
    seen: set[str] = set()
    for selector in selectors:
        if selector in plans:
            candidates = [selector]
        elif selector in sets:
            candidates = sets[selector]["order"]
        else:
            prefix_matches = [s for s in sets if s.startswith(selector)]
            if len(prefix_matches) == 1:
                candidates = sets[prefix_matches[0]]["order"]
            elif len(prefix_matches) > 1:
                raise DriverError(
                    f"Ambiguous Set selector prefix: {selector} matches {prefix_matches}"
                )
            else:
                raise DriverError(f"Unknown id6/Set selector: {selector}")
        for id6 in candidates:
            if id6 not in seen:
                expanded.append(id6)
                seen.add(id6)
    if not expanded:
        raise DriverError("At least one id6 or Set selector is required")
    return expanded


def resolve_plan_path(repo: Path, configured: str, id6: str) -> Path:
    direct = (repo / configured).resolve()
    if direct.is_file():
        return direct
    roots = [repo / ".aw" / "records" / "plans", repo]
    matches: list[Path] = []
    for root in roots:
        if root.exists():
            matches.extend(
                path for path in root.rglob(f"*-{id6}-*.ipd.md") if path.is_file()
            )
    unique = sorted(set(matches))
    if len(unique) == 1:
        return unique[0].resolve()
    if not unique:
        raise DriverError(f"Cannot locate IPD {id6}; configured path was {configured}")
    raise DriverError(f"Ambiguous IPD {id6}: {', '.join(str(path) for path in unique)}")


def plan_bucket(path: Path) -> str | None:
    parts = path.parts
    for bucket in ("executed", "active", "pending", "reviewed", "approved"):
        if bucket in parts:
            return bucket
    return None


def new_run_id() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{stamp}-{os.getpid()}"


def state_root(repo: Path) -> Path:
    return repo / ".aw" / "records" / "runs"


def initialize_run(args: argparse.Namespace) -> Path:
    repo = Path(args.repo).expanduser().resolve()
    if not (repo / ".git").exists() and not git_common_dir(repo).exists():
        raise DriverError(f"Not a Git repository: {repo}")
    manifest_path = Path(args.manifest).expanduser().resolve()
    runbook_path = Path(args.runbook).expanduser().resolve()
    manifest = load_json(manifest_path)
    validate_manifest(manifest)
    queue_ids = expand_selectors(manifest, args.selectors)
    run_id = args.run_id or new_run_id()
    run_dir = state_root(repo) / run_id
    if run_dir.exists():
        raise DriverError(f"Run already exists: {run_id}")
    for name in ("sessions", "outcomes", "prompts"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    (run_dir / "decisions-and-questions.md").write_text(
        f"# Decisions and Questions for {run_id}\n\n", encoding="utf-8"
    )
    queue: list[dict[str, Any]] = []
    for position, id6 in enumerate(queue_ids, start=1):
        plan = manifest["plans"][id6]
        queue.append(
            {
                "position": position,
                "id6": id6,
                "setid": plan["set"],
                "configured_file": plan["file"],
                "dependencies": plan.get("dependencies", []),
                "status": "queued",
                "attempts": [],
            }
        )
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "repo": str(repo),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "runbook": str(runbook_path),
        "runbook_sha256": sha256_file(runbook_path),
        "selectors": list(args.selectors),
        "queue": queue,
        "set_sessions": {},
        "options": {
            "opencode": args.opencode,
            "model": args.model,
            "agent": args.agent,
            "auto": args.auto,
        },
        "driver": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__)),
        },
    }
    atomic_write_json(run_dir / "state.json", state)
    append_jsonl(
        run_dir / "events.jsonl",
        {"at": utc_now(), "event": "run-created", "run_id": run_id, "queue": queue_ids},
    )
    write_report(run_dir, state)
    return run_dir


def load_state(run_dir: Path) -> dict[str, Any]:
    return load_json(run_dir / "state.json")


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    atomic_write_json(run_dir / "state.json", state)
    write_report(run_dir, state)


def write_report(run_dir: Path, state: dict[str, Any]) -> None:
    counts: dict[str, int] = {}
    for item in state["queue"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    lines = [
        f"# Execution Report: {state['run_id']}",
        "",
        f"- Repository: `{state['repo']}`",
        f"- Created: {state['created_at']}",
        f"- Updated: {state['updated_at']}",
        f"- Selectors: `{' '.join(state['selectors'])}`",
        f"- Set sessions: `{json.dumps(state.get('set_sessions', {}), sort_keys=True)}`",
        f"- Counts: `{json.dumps(counts, sort_keys=True)}`",
        "- Pushed: no (required; verify independently in outcomes)",
        "",
        "| # | id6 | Set | Status | Attempts | Last session |",
        "|---:|---|---|---|---:|---|",
    ]
    for item in state["queue"]:
        attempts = item.get("attempts", [])
        session = attempts[-1].get("session_id", "") if attempts else ""
        lines.append(
            f"| {item['position']} | `{item['id6']}` | `{item['setid']}` | "
            f"{item['status']} | {len(attempts)} | `{session}` |"
        )
    lines.extend(
        [
            "",
            "## Review",
            "",
            "Review `decisions-and-questions.md` first, then `outcomes/` and `sessions/`.",
            "",
        ]
    )
    (run_dir / "execution-report.md").write_text("\n".join(lines), encoding="utf-8")


def extract_session_id(log_path: Path) -> str | None:
    if not log_path.exists():
        return None
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            value = event.get("sessionID")
            if isinstance(value, str) and value.startswith("ses_"):
                return value
    return None


def dependency_status(
    item: dict[str, Any], state: dict[str, Any]
) -> tuple[bool, list[str]]:
    by_id = {entry["id6"]: entry for entry in state["queue"]}
    unsatisfied: list[str] = []
    for dep in item.get("dependencies", []):
        if dep in by_id and by_id[dep]["status"] not in SUCCESS_STATES:
            unsatisfied.append(dep)
    return not unsatisfied, unsatisfied


def build_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    recovery: bool,
) -> str:
    setid = item["setid"]
    decisions = run_dir / "decisions-and-questions.md"
    outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    report = run_dir / "execution-report.md"
    mode = "RECOVERY/CONTINUATION" if recovery else "NORMAL EXECUTION"
    prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None
    return f"""# OpenCode IPD Driver Turn

Mode: {mode}
Run ID: {state['run_id']}
Queue position: {item['position']}
Assigned IPD: {item['id6']}
Assigned Set: {setid}
Plan file at launch: {plan_path}
External run directory: {run_dir}
Decisions/questions register: {decisions}
Required JSON outcome: {outcome}
Driver report: {report}
Prior attempt: {json.dumps(prior, sort_keys=True) if prior else 'none'}

Execute only IPD {item['id6']}. Read the attached driver runbook, every applicable
repository instruction, the assigned IPD in full, its current orchestrator, current
repository state, and completed prerequisite artifacts before editing. Do not implement
another IPD in this turn.

All target IPDs are already human-approved. Do not ask for approval. This run is
non-interactive: do not invoke an interactive question tool or wait for human input.
When a material question arises, investigate the approved plans, repository decisions,
source, tests, history, and current primary documentation. If a reasonable recommended
approach exists, choose it, record it in the decisions/questions register with evidence,
alternatives, rationale, confidence, scope, reversibility, and validation, then continue.
If no reasonable approach exists, record a DEFERRED question with the work completed,
work blocked, dependency effect, exact preserved state, and recommended human action.
Continue every independent part of this IPD despite a deferred question.

Maximize safe forward progress. A local failure or unanswered question is not permission
to abandon independent work. Do not weaken checks, fabricate evidence, broaden approved
scope, bypass lifecycle controls, discard unrelated work, or push. Do not use git add -A,
git add ., git commit -a, --no-verify, destructive reset/clean, or stashing that could hide
ownership. Use the lifecycle available at this bootstrap stage and path-scoped commits.

If the IPD cannot validly finalize, preserve partial work using the repository-supported
nonterminal checkpoint mechanism or an attributable isolated branch/worktree. Leave the
main execution checkout safe for subsequent turns. Never claim executed unless the real
terminal state and acceptance criteria support it.

Before exiting, write valid JSON to {outcome} with at least:
{{
  "schema_version": 1,
  "run_id": "{state['run_id']}",
  "position": {item['position']},
  "id6": "{item['id6']}",
  "setid": "{setid}",
  "disposition": "executed|substantially-complete|partial|blocked|failed-safely",
  "summary": "...",
  "starting_head": "...",
  "ending_head": "...",
  "commits": [],
  "files_changed": [],
  "tests": [],
  "decision_ids": [],
  "deferred_question_ids": [],
  "incomplete_requirements": [],
  "partial_work_location": null,
  "recommended_next_action": "...",
  "pushed": false
}}

The disposition must describe the actual repository result, not merely your effort. If no
material question arose, say so in the summary. Explicitly confirm pushed=false.
"""


def write_prompt(
    run_dir: Path, item: dict[str, Any], prompt: str, attempt_no: int
) -> Path:
    path = (
        run_dir
        / "prompts"
        / f"{item['position']:02d}-{item['id6']}-attempt-{attempt_no}.md"
    )
    path.write_text(prompt, encoding="utf-8")
    return path


def attempt_log_path(run_dir: Path, item: dict[str, Any], attempt_no: int) -> Path:
    return (
        run_dir
        / "sessions"
        / f"{item['position']:02d}-{item['id6']}-attempt-{attempt_no}.jsonl"
    )


def run_opencode(
    state: dict[str, Any],
    run_dir: Path,
    item: dict[str, Any],
    plan_path: Path,
    prompt_path: Path,
    attempt_no: int,
) -> tuple[int, str | None, Path, list[str]]:
    options = state["options"]
    opencode = options.get("opencode") or "opencode"
    argv = [opencode, "run"]
    set_session = state.get("set_sessions", {}).get(item["setid"])
    if set_session:
        argv.extend(["--session", set_session])
    argv.extend(["--dir", state["repo"], "--format", "json"])
    if options.get("model"):
        argv.extend(["--model", options["model"]])
    if options.get("agent"):
        argv.extend(["--agent", options["agent"]])
    if options.get("auto", True):
        argv.append("--auto")
    argv.extend(
        [
            "--title",
            f"aw-{state['run_id']}-{item['setid']}",
            "--file",
            state["runbook"],
            "--file",
            str(plan_path),
            "--",
            prompt_path.read_text(encoding="utf-8"),
        ]
    )
    log_path = attempt_log_path(run_dir, item, attempt_no)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            argv,
            cwd=state["repo"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        assert process.stdout is not None
        try:
            for line in process.stdout:
                log.write(line)
                log.flush()
                sys.stdout.write(line)
                sys.stdout.flush()
        except KeyboardInterrupt:
            process.send_signal(signal.SIGINT)
            raise
        returncode = process.wait()
        log.flush()
        os.fsync(log.fileno())
    return returncode, extract_session_id(log_path), log_path, argv


def reconcile_disposition(
    repo: Path, item: dict[str, Any], run_dir: Path, exit_code: int
) -> tuple[str, dict[str, Any] | None]:
    outcome_path = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    outcome: dict[str, Any] | None = None
    if outcome_path.exists():
        try:
            outcome = load_json(outcome_path)
        except DriverError:
            outcome = None
    try:
        current_plan = resolve_plan_path(repo, item["configured_file"], item["id6"])
        bucket = plan_bucket(current_plan)
    except DriverError:
        bucket = None
    if bucket == "executed":
        return "executed", outcome
    if outcome:
        disposition = outcome.get("disposition")
        if disposition == "executed":
            # A model-authored outcome is a claim, not the lifecycle authority.
            return "substantially-complete", outcome
        if disposition in TERMINAL_STATES - {"dependency-blocked", "not-attempted"}:
            return disposition, outcome
    return ("partial" if exit_code == 0 else "failed-safely"), outcome


def execute_item(
    run_dir: Path, state: dict[str, Any], item: dict[str, Any], recovery: bool
) -> None:
    repo = Path(state["repo"])
    plan_path = resolve_plan_path(repo, item["configured_file"], item["id6"])
    attempt_no = len(item.get("attempts", [])) + 1
    prompt = build_prompt(item, state, run_dir, plan_path, recovery)
    prompt_path = write_prompt(run_dir, item, prompt, attempt_no)
    attempt = {
        "number": attempt_no,
        "started_at": utc_now(),
        "starting_head": git_head(repo),
        "starting_branch": git_branch(repo),
        "starting_status": git_status(repo),
        "prompt": str(prompt_path),
        "prompt_sha256": sha256_file(prompt_path),
        "session_id": state.get("set_sessions", {}).get(item["setid"]),
        "log": str(attempt_log_path(run_dir, item, attempt_no)),
        "recovery": recovery,
    }
    item.setdefault("attempts", []).append(attempt)
    item["status"] = "running"
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "ipd-started",
            "id6": item["id6"],
            "attempt": attempt_no,
        },
    )
    try:
        exit_code, session_id, log_path, argv = run_opencode(
            state, run_dir, item, plan_path, prompt_path, attempt_no
        )
    except KeyboardInterrupt:
        attempt["interrupted_at"] = utc_now()
        item["status"] = "interrupted"
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {"at": utc_now(), "event": "ipd-interrupted", "id6": item["id6"]},
        )
        raise
    if session_id:
        existing = state.setdefault("set_sessions", {}).get(item["setid"])
        if existing and existing != session_id:
            raise DriverError(
                f"Set {item['setid']} changed session unexpectedly: {existing} -> {session_id}"
            )
        state["set_sessions"][item["setid"]] = session_id
        attempt["session_id"] = session_id
    attempt.update(
        {
            "ended_at": utc_now(),
            "exit_code": exit_code,
            "ending_head": git_head(repo),
            "ending_branch": git_branch(repo),
            "ending_status": git_status(repo),
            "log": str(log_path),
            "argv": argv,
        }
    )
    disposition, outcome = reconcile_disposition(repo, item, run_dir, exit_code)
    item["status"] = disposition
    item["last_outcome"] = outcome
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "ipd-finished",
            "id6": item["id6"],
            "attempt": attempt_no,
            "exit_code": exit_code,
            "status": disposition,
            "session_id": session_id,
        },
    )


def reconcile_interrupted(run_dir: Path, state: dict[str, Any]) -> None:
    repo = Path(state["repo"])
    for item in state["queue"]:
        if item["status"] != "running":
            continue
        attempts = item.get("attempts", [])
        if attempts:
            raw_log = attempts[-1].get("log")
            session_id = extract_session_id(Path(raw_log)) if raw_log else None
            if session_id:
                existing = state.setdefault("set_sessions", {}).get(item["setid"])
                if existing in (None, session_id):
                    state["set_sessions"][item["setid"]] = session_id
                    attempts[-1]["session_id"] = session_id
                else:
                    attempts[-1]["session_reconciliation_error"] = (
                        f"persisted={existing} observed={session_id}"
                    )
        try:
            path = resolve_plan_path(repo, item["configured_file"], item["id6"])
            if plan_bucket(path) == "executed":
                item["status"] = "executed"
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "interrupted-reconciled-executed",
                        "id6": item["id6"],
                    },
                )
                continue
        except DriverError:
            pass
        item["status"] = "interrupted"
        append_jsonl(
            run_dir / "events.jsonl",
            {"at": utc_now(), "event": "interrupted-detected", "id6": item["id6"]},
        )
    save_state(run_dir, state)


def run_queue(run_dir: Path, retry_incomplete: bool) -> int:
    state = load_state(run_dir)
    reconcile_interrupted(run_dir, state)
    if retry_incomplete:
        for item in state["queue"]:
            if item["status"] in {
                "interrupted",
                "substantially-complete",
                "partial",
                "failed-safely",
                "blocked",
                "dependency-blocked",
            }:
                item["status"] = "queued"
                item["recovery_next"] = True
        save_state(run_dir, state)
    while True:
        state = load_state(run_dir)
        queued = [item for item in state["queue"] if item["status"] == "queued"]
        if not queued:
            break
        runnable = None
        for item in queued:
            satisfied, _ = dependency_status(item, state)
            if satisfied:
                runnable = item
                break
        if runnable is None:
            for item in queued:
                _, missing = dependency_status(item, state)
                item["status"] = "dependency-blocked"
                item["unsatisfied_dependencies"] = missing
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "dependency-blocked",
                        "id6": item["id6"],
                        "dependencies": missing,
                    },
                )
            save_state(run_dir, state)
            break
        recovery = bool(runnable.pop("recovery_next", False))
        try:
            execute_item(run_dir, state, runnable, recovery=recovery)
        except DriverError as exc:
            runnable["status"] = "failed-safely"
            runnable["driver_error"] = str(exc)
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "ipd-driver-error",
                    "id6": runnable["id6"],
                    "error": str(exc),
                },
            )
            print(f"IPD {runnable['id6']} failed safely: {exc}", file=sys.stderr)
    state = load_state(run_dir)
    write_report(run_dir, state)
    return 0 if all(item["status"] == "executed" for item in state["queue"]) else 1


def print_status(run_dir: Path) -> None:
    state = load_state(run_dir)
    print(f"Run: {state['run_id']}")
    print(f"Repository: {state['repo']}")
    print(f"Updated: {state['updated_at']}")
    print(f"State directory: {run_dir}")
    for item in state["queue"]:
        print(
            f"{item['position']:02d} {item['id6']} {item['setid']:<12} "
            f"{item['status']:<24} attempts={len(item.get('attempts', []))}"
        )


def resolve_run_dir(repo_arg: str, run_id: str) -> Path:
    repo = Path(repo_arg).expanduser().resolve()
    run_dir = state_root(repo) / run_id
    if not run_dir.is_dir():
        raise DriverError(f"Run not found: {run_id}")
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ipdrunner",
        description="Restartable OpenCode driver for approved IPD and Set selectors.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="Create a run and execute its queue")
    start.add_argument("selectors", nargs="+", help="One or more id6 or Set IDs")
    start.add_argument("--repo", default=".", help="Target Git repository")
    start.add_argument("--manifest", required=True, help="Driver manifest JSON")
    start.add_argument(
        "--runbook", required=True, help="Driver prompt/runbook Markdown"
    )
    start.add_argument("--run-id", help="Explicit unique run ID")
    start.add_argument("--opencode", default="opencode", help="OpenCode executable")
    start.add_argument("--model", help="Exact provider/model identifier")
    start.add_argument("--agent", help="Primary OpenCode agent name")
    start.add_argument("--auto", action=argparse.BooleanOptionalAction, default=True)
    start.add_argument(
        "--prepare-only",
        action="store_true",
        help="Create and print the durable queue without launching OpenCode",
    )

    resume = sub.add_parser("resume", help="Resume an existing run")
    resume.add_argument("run_id")
    resume.add_argument("--repo", default=".")
    resume.add_argument(
        "--retry-incomplete",
        action="store_true",
        help="Retry interrupted, partial, failed, or blocked items in recovery mode",
    )

    status = sub.add_parser("status", help="Show an existing run")
    status.add_argument("run_id")
    status.add_argument("--repo", default=".")

    report = sub.add_parser("report", help="Regenerate and print report path")
    report.add_argument("run_id")
    report.add_argument("--repo", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "start":
            run_dir = initialize_run(args)
            print(f"Run ID: {run_dir.name}")
            print(f"State directory: {run_dir}")
            if args.prepare_only:
                print_status(run_dir)
                return 0
            with run_lock(run_dir):
                return run_queue(run_dir, retry_incomplete=False)
        run_dir = resolve_run_dir(args.repo, args.run_id)
        if args.command == "status":
            print_status(run_dir)
            return 0
        if args.command == "report":
            state = load_state(run_dir)
            write_report(run_dir, state)
            print(run_dir / "execution-report.md")
            return 0
        if args.command == "resume":
            with run_lock(run_dir):
                return run_queue(run_dir, retry_incomplete=args.retry_incomplete)
        raise DriverError(f"Unsupported command: {args.command}")
    except KeyboardInterrupt:
        print("Interrupted; durable run state was preserved.", file=sys.stderr)
        return 130
    except DriverError as exc:
        print(f"ipdrunner: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Preserve a distinct driver-failure code and traceback.
        print(f"ipdrunner: unexpected failure: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
