"""Run-family CLI handlers, split by DIRECTION across two nouns (runnamecollapse `0soncw`).

awoptimize Order 04 (`yndh7k`) E-04, Order 07 (`7yqm1v`) E-03.

`aw runs` READS (this module's inspection handlers):
  * `aw runs show <target>`          - inspect run status, steps, verifier decisions, and completion.
  * `aw runs status <target>`        - reconstructed run + step state from the ledger.
  * `aw runs next <target>`          - steps whose dependencies and gates are satisfied.
  * `aw runs resume <target>`        - resumable steps; refuses on interrupted side effects.
  * `aw runs evidence <target>`      - list and validate captured evidence envelopes and tool events.
  * `aw runs verify-ledger <target>` - verify SHA-256 hash chaining and evidence validity.
  * `aw runs decisions|questions <run-id>` - a Set run's durable projections.
  * `aw runs [<target> ...]` / `aw runs list` - the driver-run viewer table (in `run_viewer`).

`aw run` WRITES (the ledger transaction handlers, also here):
  * `aw run start|record|cancel|finalize <target>`.

`next` and `resume` sound like actions but only reconstruct state and report, which is why they are
readers. `aw run` is NOT retired: it stays the writing/dispatch noun.

Contract:
  * exit 0 = success / clean / complete;
    exit 1 = incomplete / invalid evidence / unsatisfied requirements;
    exit 2 = invocation error, missing ledger, or corrupted hash chain / unparseable JSON;
    exit 7 = the target is healthy JSONL of some OTHER format, i.e. not a ledger at all.
  * WRONG-FORMAT IS NOT CORRUPTION. A file that carries none of the ledger envelope fields gets a
    'not a run ledger file' verdict (exit 7), never a corruption verdict: reporting healthy driver
    event logs as corrupt accused good data of damage it did not have (`e6b9kt`).
  * `--agent` and `--json` emit machine-readable output with NO ANSI; human mode is the default.
  * Read-only: makes NO filesystem writes, ever.
  * Redacts sensitive values in both human and machine outputs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from agent_workflows import run_engine, run_recovery, run_state
from agent_workflows import run_evidence as evidence
from agent_workflows import run_ledger_store as store

# ---- exit-code table (awoptimize Order 07 E-03) --------------------------------------------------
# Distinct nonzero codes let a caller/CI distinguish outcome classes. Kept small and consistent:
EXIT_OK: int = 0  # complete / success
EXIT_INCOMPLETE: int = 1  # run incomplete / unsatisfied predicates
EXIT_BLOCKED: int = (
    3  # blocked: unknown-outcome / retry budget exhausted / not runnable
)
EXIT_INVALID_EVIDENCE: int = 4  # captured evidence invalid / false-completion class
EXIT_CORRUPTED_LEDGER: int = 5  # hash chain / schema / torn-line corruption
EXIT_OPERATIONAL: int = (
    6  # operational failure (lock contention, illegal transition, unauthorized)
)
EXIT_INVALID_INVOCATION: int = 2  # bad invocation / missing ledger
EXIT_NOT_A_LEDGER: int = (
    7  # the target is healthy JSONL but is NOT a ledger (wrong format, NOT corruption)
)


def run_cli(args: argparse.Namespace) -> int:
    """Dispatch a run-family leaf from either noun. Returns the process exit code.

    runnamecollapse 0soncw: the surface is split by DIRECTION, so this one dispatcher serves both
    parser groups and reads whichever dest was populated - `runs_command` for the nine read-only
    leaves under `aw runs`, `run_command` for the four writers under `aw run`.

    The `("list", "runs", "summary", "viewer")` viewer aliases that used to be handled here are GONE
    (E-04). Only `list` was ever a registered parser leaf; `summary` and `viewer` were unreachable
    dead branches. The viewer is now reached as bare `aw runs` or `aw runs list`, routed in `cli.py`,
    so exactly one code path renders that table.
    """
    sub = getattr(args, "runs_command", None) or getattr(args, "run_command", None)
    if sub == "show":
        return _run_show(args)
    if sub == "evidence":
        return _run_evidence(args)
    if sub == "verify-ledger":
        return _run_verify_ledger(args)
    if sub == "start":
        return _run_start(args)
    if sub == "next":
        return _run_next(args)
    if sub == "record":
        return _run_record(args)
    if sub == "resume":
        return _run_resume(args)
    if sub == "cancel":
        return _run_cancel(args)
    if sub == "status":
        return _run_status(args)
    if sub == "finalize":
        return _run_finalize(args)
    if sub == "decisions":
        return _run_decisions(args)
    if sub == "questions":
        return _run_questions(args)
    print(
        "usage: aw run {start|record|cancel|finalize} <run-id-or-path> "
        "[--agent|--json] [--dir <dir>]\n"
        "       aw runs {show|status|next|resume|evidence|verify-ledger|decisions|questions|list} "
        "<run-id-or-path> [--agent|--json] [--dir <dir>]"
    )
    return EXIT_INVALID_INVOCATION


def _projection_dir(args: argparse.Namespace):
    """Resolve the run-artifacts dir for a Set run's durable projections (read-only)."""
    from pathlib import Path

    from agent_workflows import set_records
    from agent_workflows.project_context import resolve_verb_repo_root

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    run_id = getattr(args, "target", None) or ""
    workflow = getattr(args, "workflow", None) or "exec-set"
    return set_records.run_artifacts_dir(Path(repo_root), workflow, run_id)


def _run_decisions(args: argparse.Namespace) -> int:
    """Print a Set run's recorded autonomous decisions (read-only). Exit 0 found / 1 none / 2 missing."""
    from agent_workflows import set_records

    base = _projection_dir(args)
    path = base / set_records.DECISIONS_FILE
    if not path.is_file():
        print("no decisions projection found for this run ({0})".format(path))
        return 2
    text = path.read_text(encoding="utf-8")
    print(text, end="" if text.endswith("\n") else "\n")
    return 1 if "_No autonomous decisions recorded._" in text else 0


def _run_questions(args: argparse.Namespace) -> int:
    """Print a Set run's unresolved questions (read-only). Exit 0 open / 1 none / 2 missing."""
    from agent_workflows import set_records

    base = _projection_dir(args)
    path = base / set_records.OPEN_QUESTIONS_FILE
    if not path.is_file():
        print("no open-questions projection found for this run ({0})".format(path))
        return 2
    text = path.read_text(encoding="utf-8")
    print(text, end="" if text.endswith("\n") else "\n")
    return 1 if "_No unresolved questions._" in text else 0


def _machine(args: argparse.Namespace) -> bool:
    return bool(
        getattr(args, "agent", False)
        or getattr(args, "as_agent", False)
        or getattr(args, "json", False)
        or getattr(args, "as_json", False)
    )


def _redact_output(data: Any) -> Any:
    """Recursively scrub any sensitive substrings or token patterns in output data."""
    if isinstance(data, str):
        # Redact common token patterns
        redacted = re.sub(
            r"(ghp_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._~+/-]+)", "[REDACTED]", data
        )
        return redacted
    if isinstance(data, list):
        return [_redact_output(item) for item in data]
    if isinstance(data, dict):
        res: Dict[str, Any] = {}
        for k, v in data.items():
            k_upper = str(k).upper()
            if any(
                sub in k_upper
                for sub in ("KEY", "TOKEN", "SECRET", "PASSWORD", "AUTH", "CRED")
            ):
                res[k] = "[REDACTED]"
            else:
                res[k] = _redact_output(v)
        return res
    return data


def _emit_machine(args: argparse.Namespace, payload: Any) -> None:
    """Emit ANSI-free machine output. `--agent` emits compact JSON/JSONL; `--json` emits pretty JSON."""
    sanitized = _redact_output(payload)
    if getattr(args, "agent", False) or getattr(args, "as_agent", False):
        if isinstance(sanitized, list):
            for item in sanitized:
                print(
                    json.dumps(
                        item, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                    )
                )
        else:
            print(
                json.dumps(
                    sanitized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                )
            )
    else:  # --json
        print(json.dumps(sanitized, sort_keys=True, indent=2, ensure_ascii=False))


def _emit_not_a_ledger(args: argparse.Namespace, exc: "store.NotALedgerError") -> int:
    """Report a WRONG-FORMAT target and return `EXIT_NOT_A_LEDGER`.

    Kept separate from every corruption path on purpose: the message must not contain the word
    corrupt, and machine consumers get `corrupted: false` plus an explicit `not_a_ledger: true` so a
    healthy foreign file is never mistaken for a damaged ledger (`e6b9kt`).
    """
    err_msg = f"error: not a run ledger: {exc}"
    if _machine(args):
        _emit_machine(
            args,
            {
                "ok": False,
                "error": err_msg,
                "corrupted": False,
                "not_a_ledger": True,
                "path": str(exc.path),
                "exit_code": EXIT_NOT_A_LEDGER,
            },
        )
    else:
        print(err_msg)
    return EXIT_NOT_A_LEDGER


def resolve_ledger_path(
    target: str, repo_root: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """Resolve a target argument (run id or path) to a concrete ledger JSONL path.

    A run ledger owns exactly ONE filename, `store.LEDGER_FILENAME` (`ledger.jsonl`). It must NEVER
    resolve a bare run id to `<...>/runs/<target>/events.jsonl`: that file exists for every real
    driver run but is the RUNNER's own event log in a different format, so claiming it made
    `aw run show <any-real-run>` parse healthy data as a ledger and report it corrupt (`e6b9kt`).

    An EXPLICIT path argument is still honoured verbatim, whatever it is named, so an operator can
    point the reader at a ledger stored anywhere; the shape check downstream decides what it is.
    """
    if not target:
        return None

    path_obj = Path(target)
    if path_obj.is_file():
        return path_obj.resolve()

    root = Path(repo_root) if repo_root else Path.cwd()
    candidates = [
        path_obj,
        root / target,
        root / f"{target}.jsonl",
        root / ".aw" / "state" / "runs" / target / store.LEDGER_FILENAME,
        root / ".aw" / "records" / "runs" / target / store.LEDGER_FILENAME,
        root / ".aw" / "state" / "runs" / target,
        root / ".aw" / "runs" / target / store.LEDGER_FILENAME,
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()

    return None


# --------------------------------------------------------------------------------------------------
# show (read-only run inspection and completion evaluation)
# --------------------------------------------------------------------------------------------------


def _run_show(args: argparse.Namespace) -> int:
    target = getattr(args, "target", None)
    if not target:
        print("error: no run id or ledger path given")
        return 2

    repo_dir = getattr(args, "dir", None)
    ledger_file = resolve_ledger_path(target, repo_dir)
    machine = _machine(args)

    if not ledger_file:
        err_msg = f"error: ledger file not found for target '{target}'"
        if machine:
            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
        else:
            print(err_msg)
        return 2

    ledger_store = store.RunLedgerStore(ledger_file)
    try:
        records = ledger_store.read_records(verify=True)
    except store.NotALedgerError as exc:
        return _emit_not_a_ledger(args, exc)
    except store.LedgerCorruption as exc:
        err_msg = f"error: ledger corruption detected: {exc}"
        if machine:
            _emit_machine(
                args,
                {"ok": False, "error": err_msg, "corrupted": True, "exit_code": 2},
            )
        else:
            print(err_msg)
        return 2
    except Exception as exc:
        err_msg = f"error: failed to read ledger: {exc}"
        if machine:
            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
        else:
            print(err_msg)
        return 2

    evaluation = evidence.evaluate_completion(records)

    # Extract metadata from records
    run_rec = records[0] if records and records[0].get("kind") == "run" else {}
    run_id = run_rec.get("run_id", target)
    repo = run_rec.get("repo", "")
    head = run_rec.get("head", "")
    workflow_digest = run_rec.get("workflow_digest", "")

    step_attempts = [r for r in records if r.get("kind") == "step_attempt"]
    verifier_decisions = [r for r in records if r.get("kind") == "verifier_decision"]
    evidence_envelopes = [r for r in records if r.get("kind") == "evidence_envelope"]

    predicates_dict = {
        name: {"satisfied": p.satisfied, "details": p.details}
        for name, p in evaluation.predicates.items()
    }

    if machine:
        payload = {
            "run_id": run_id,
            "repo": repo,
            "head": head,
            "workflow_digest": workflow_digest,
            "records_count": len(records),
            "step_attempts_count": len(step_attempts),
            "verifier_decisions_count": len(verifier_decisions),
            "evidence_envelopes_count": len(evidence_envelopes),
            "is_complete": evaluation.is_complete,
            "predicates": predicates_dict,
            "missing_evidence": list(evaluation.missing_evidence),
            "unresolved_blockers": list(evaluation.unresolved_blockers),
            "reasons": list(evaluation.reasons),
        }
        _emit_machine(args, payload)
    else:
        print(f"Run: {run_id}")
        if repo:
            print(f"Repository: {repo}")
        if head:
            print(f"HEAD: {head}")
        print(f"Ledger: {ledger_file} ({len(records)} records)")
        print(f"Steps Attempted: {len(step_attempts)}")
        print(f"Verifier Decisions: {len(verifier_decisions)}")
        print(f"Evidence Envelopes: {len(evidence_envelopes)}")
        print("\nCompletion Predicates:")
        for name, p in evaluation.predicates.items():
            status_tag = "PASS" if p.satisfied else "FAIL"
            print(f"  [{status_tag}] {name}: {p.details}")

        if evaluation.is_complete:
            print("\nOutcome: COMPLETE (all predicates satisfied)")
        else:
            print("\nOutcome: INCOMPLETE")
            for r in evaluation.reasons:
                print(f"  - {r}")

    return 0 if evaluation.is_complete else 1


# --------------------------------------------------------------------------------------------------
# evidence (read-only evidence inspection and per-envelope validation)
# --------------------------------------------------------------------------------------------------


def _run_evidence(args: argparse.Namespace) -> int:
    target = getattr(args, "target", None)
    if not target:
        print("error: no run id or ledger path given")
        return 2

    repo_dir = getattr(args, "dir", None)
    ledger_file = resolve_ledger_path(target, repo_dir)
    machine = _machine(args)

    if not ledger_file:
        err_msg = f"error: ledger file not found for target '{target}'"
        if machine:
            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
        else:
            print(err_msg)
        return 2

    ledger_store = store.RunLedgerStore(ledger_file)
    try:
        records = ledger_store.read_records(verify=True)
    except store.NotALedgerError as exc:
        return _emit_not_a_ledger(args, exc)
    except store.LedgerCorruption as exc:
        err_msg = f"error: ledger corruption detected: {exc}"
        if machine:
            _emit_machine(
                args,
                {"ok": False, "error": err_msg, "corrupted": True, "exit_code": 2},
            )
        else:
            print(err_msg)
        return 2
    except Exception as exc:
        err_msg = f"error: failed to read ledger: {exc}"
        if machine:
            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
        else:
            print(err_msg)
        return 2

    evidence_records: List[Dict[str, Any]] = []
    any_invalid = False

    for idx, rec in enumerate(records):
        kind = rec.get("kind")
        if kind in ("evidence_envelope", "tool_event", "artifact_ref"):
            val_res = evidence.validate_evidence(rec, check_filesystem=True)
            if not val_res.ok:
                any_invalid = True
            rec_summary: Dict[str, Any] = {
                "seq": rec.get("seq", idx),
                "kind": kind,
                "valid": val_res.ok,
                "actor": rec.get("actor", ""),
                "timestamp": rec.get("timestamp", ""),
                "findings": [
                    {
                        "code": f.code,
                        "where": f.where,
                        "message": f.message,
                        "reason": f.reason,
                    }
                    for f in val_res.findings
                ],
            }
            if kind == "tool_event":
                rec_summary["argv"] = rec.get("argv")
                rec_summary["exit_code"] = rec.get("exit_code")
                rec_summary["stdout_sha256"] = rec.get("stdout_sha256")
                rec_summary["cwd"] = rec.get("cwd")
            elif kind == "evidence_envelope":
                rec_summary["evidence_kind"] = rec.get("evidence_kind")
                rec_summary["binds"] = rec.get("binds")
                rec_summary["head"] = rec.get("head")
                rec_summary["worktree"] = rec.get("worktree")
            elif kind == "artifact_ref":
                rec_summary["path"] = rec.get("path")
                rec_summary["sha256"] = rec.get("sha256")

            evidence_records.append(rec_summary)

    if machine:
        payload = {
            "ledger": str(ledger_file),
            "evidence_count": len(evidence_records),
            "all_valid": not any_invalid,
            "evidence": evidence_records,
        }
        _emit_machine(args, payload)
    else:
        print(f"Evidence for {ledger_file} ({len(evidence_records)} items):")
        if not evidence_records:
            print("  No captured evidence envelopes or tool events found.")
        for item in evidence_records:
            status = "VALID" if item["valid"] else "INVALID"
            seq = item["seq"]
            kind = item["kind"]
            print(f"\n[{status}] Seq {seq} ({kind})")
            if kind == "tool_event":
                print(f"  Command: {item.get('argv')}")
                print(f"  Exit Code: {item.get('exit_code')}")
                print(f"  Stdout Hash: {item.get('stdout_sha256')}")
            elif kind == "evidence_envelope":
                print(f"  Kind: {item.get('evidence_kind')}")
                print(f"  Binds: {item.get('binds')}")
                print(f"  HEAD: {item.get('head')}")
            elif kind == "artifact_ref":
                print(f"  Path: {item.get('path')}")
                print(f"  Hash: {item.get('sha256')}")

            if not item["valid"]:
                for f in item["findings"]:
                    print(f"  Finding: {f['code']} ({f['where']}): {f['message']}")

    return 1 if any_invalid else 0


# --------------------------------------------------------------------------------------------------
# verify-ledger (read-only hash chain and evidence validity verification)
# --------------------------------------------------------------------------------------------------


def _run_verify_ledger(args: argparse.Namespace) -> int:
    target = getattr(args, "target", None)
    if not target:
        print("error: no run id or ledger path given")
        return 2

    repo_dir = getattr(args, "dir", None)
    ledger_file = resolve_ledger_path(target, repo_dir)
    machine = _machine(args)

    if not ledger_file:
        err_msg = f"error: ledger file not found for target '{target}'"
        if machine:
            _emit_machine(args, {"ok": False, "error": err_msg, "exit_code": 2})
        else:
            print(err_msg)
        return 2

    ledger_store = store.RunLedgerStore(ledger_file)
    try:
        chain_ver = ledger_store.verify_chain(raise_on_error=False)
    except store.NotALedgerError as exc:
        return _emit_not_a_ledger(args, exc)

    if not chain_ver.clean:
        break_info = chain_ver.break_info
        err_details = (
            f"Broken chain at seq {break_info.seq}: {break_info.reason} (expected {break_info.expected!r}, got {break_info.actual!r})"
            if break_info
            else "Broken chain"
        )
        if machine:
            _emit_machine(
                args,
                {
                    "ok": False,
                    "chain_clean": False,
                    "error": err_details,
                    "records_checked": chain_ver.count,
                    "exit_code": 2,
                },
            )
        else:
            print(f"FAIL: Ledger verification failed for {ledger_file}")
            print(f"  {err_details}")
        return 2

    # Chain is clean, now verify evidence and completion predicates
    records = ledger_store.read_records(verify=False)
    evidence_val = evidence.validate_ledger_evidence(records, check_filesystem=True)
    evaluation = evidence.evaluate_completion(records)

    is_valid = evidence_val.ok and evaluation.is_complete

    if machine:
        payload = {
            "ok": is_valid,
            "chain_clean": True,
            "records_count": chain_ver.count,
            "evidence_valid": evidence_val.ok,
            "is_complete": evaluation.is_complete,
            "findings": [
                {
                    "code": f.code,
                    "where": f.where,
                    "message": f.message,
                    "reason": f.reason,
                }
                for f in evidence_val.findings
            ],
            "reasons": list(evaluation.reasons),
        }
        _emit_machine(args, payload)
    else:
        print(f"Ledger: {ledger_file}")
        print(f"Hash Chain: CLEAN ({chain_ver.count} records verified)")
        print(f"Evidence Validity: {'CLEAN' if evidence_val.ok else 'INVALID'}")
        print(
            f"Completion Predicates: {'SATISFIED' if evaluation.is_complete else 'UNSATISFIED'}"
        )

        if not evidence_val.ok:
            print("\nEvidence Findings:")
            for f in evidence_val.findings:
                print(f"  - {f.code} ({f.where}): {f.message}")

        if not evaluation.is_complete:
            print("\nUnsatisfied Completion Criteria:")
            for r in evaluation.reasons:
                print(f"  - {r}")

        if is_valid:
            print("\nOverall Status: PASS (chain clean, evidence valid, run complete)")
        else:
            print("\nOverall Status: FAIL")

    if not evidence_val.ok or not evaluation.is_complete:
        return 1
    return 0


# ==================================================================================================
# awoptimize Order 07 E-03: mutating subcommands (start | next | record | resume | cancel | status
# | finalize). Human + JSON/agent machine modes; ANSI-free machine output; the exit-code table above.
# ==================================================================================================


def _emit_error(args: argparse.Namespace, message: str, exit_code: int) -> int:
    """Emit an error in human or machine mode and return the exit code."""
    if _machine(args):
        _emit_machine(args, {"ok": False, "error": message, "exit_code": exit_code})
    else:
        print(f"error: {message}")
    return exit_code


def _resolve_or_error(args: argparse.Namespace) -> tuple[Optional[Path], int]:
    """Resolve the ledger path or return an invalid-invocation error tuple."""
    target = getattr(args, "target", None)
    if not target:
        return None, _emit_error(
            args, "no run id or ledger path given", EXIT_INVALID_INVOCATION
        )
    ledger_file = resolve_ledger_path(target, getattr(args, "dir", None))
    if not ledger_file:
        return None, _emit_error(
            args,
            f"ledger file not found for target '{target}'",
            EXIT_INVALID_INVOCATION,
        )
    return ledger_file, EXIT_OK


def _load_workflow_arg(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """Load a workflow definition from --workflow JSON path, or None if not supplied."""
    wf_path = getattr(args, "workflow", None)
    if not wf_path:
        return None
    p = Path(wf_path)
    if not p.is_file():
        raise FileNotFoundError(f"workflow file not found: {wf_path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if (
        isinstance(data, dict)
        and "workflow" in data
        and isinstance(data["workflow"], dict)
    ):
        return data
    return data if isinstance(data, dict) else None


def _reconstruct_workflow_from_ledger(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a minimal workflow skeleton (id/steps/requirements) from ledger records.

    Used when no --workflow file is supplied: the ledger is authoritative, and step ids + requirement
    ids can be recovered from step_attempt and requirement_set records. Dependency edges are unknown
    from the ledger alone, so the skeleton has no depends_on/gates (ledger-driven commands like status
    /resume/cancel/finalize do not need the DAG).
    """
    wf_id = "reconstructed"
    step_ids: List[str] = []
    seen_steps: set[str] = set()
    requirements: List[Dict[str, Any]] = []
    seen_reqs: set[str] = set()
    for rec in records:
        kind = rec.get("kind")
        if kind == "run":
            wf_id = (
                str(rec.get("workflow_digest", "reconstructed"))[:16] or "reconstructed"
            )
        elif kind == "step_attempt":
            sid = str(rec.get("step", ""))
            if sid and sid not in seen_steps:
                seen_steps.add(sid)
                step_ids.append(sid)
        elif kind == "requirement_set":
            for req in rec.get("requirements", []):
                if isinstance(req, dict):
                    rid = req.get("id")
                    if rid and rid not in seen_reqs:
                        seen_reqs.add(rid)
                        requirements.append({"id": rid})
    steps = [
        {"id": sid, "action": "", "depends_on": [], "satisfies": []} for sid in step_ids
    ]
    return {"id": wf_id, "steps": steps, "requirements": requirements}


def _build_engine(
    args: argparse.Namespace, ledger_file: Path
) -> tuple[Optional[run_engine.RunEngine], List[Dict[str, Any]], int]:
    """Construct a RunEngine over a ledger. Returns (engine, records, exit_code)."""
    ledger_store = store.RunLedgerStore(ledger_file)
    try:
        records = ledger_store.read_records(verify=True)
    except store.NotALedgerError as exc:
        return None, [], _emit_not_a_ledger(args, exc)
    except store.LedgerCorruption as exc:
        return (
            None,
            [],
            _emit_error(
                args, f"ledger corruption detected: {exc}", EXIT_CORRUPTED_LEDGER
            ),
        )
    except Exception as exc:  # noqa: BLE001 - fail closed on any read failure
        return (
            None,
            [],
            _emit_error(args, f"failed to read ledger: {exc}", EXIT_INVALID_INVOCATION),
        )

    if not records:
        return None, [], _emit_error(args, "ledger is empty", EXIT_INVALID_INVOCATION)

    try:
        workflow = _load_workflow_arg(args)
    except (OSError, ValueError) as exc:
        return (
            None,
            records,
            _emit_error(
                args, f"failed to load workflow: {exc}", EXIT_INVALID_INVOCATION
            ),
        )
    if workflow is None:
        workflow = _reconstruct_workflow_from_ledger(records)

    run_rec = records[0] if records[0].get("kind") == "run" else {}
    run_id = str(run_rec.get("run_id") or "run-00000001")
    engine = run_engine.RunEngine(workflow, ledger_store, run_id=run_id)
    return engine, records, EXIT_OK


def rebuild_index(ledger_file: Union[str, Path]) -> List[Dict[str, Any]]:
    """Rebuild a per-run runtime INDEX (append-only JSONL) purely from the authoritative ledger.

    The ledger stays the source of truth; the index is a rebuildable projection (never SQLite). Each
    index row summarizes one ledger record so a caller can page state without replaying the chain.
    """
    ledger_store = store.RunLedgerStore(ledger_file)
    records = ledger_store.read_records(verify=True)
    index_rows: List[Dict[str, Any]] = []
    for rec in records:
        row: Dict[str, Any] = {
            "seq": rec.get("seq"),
            "kind": rec.get("kind"),
            "actor": rec.get("actor"),
        }
        kind = rec.get("kind")
        if kind == "step_attempt":
            row["step"] = rec.get("step")
            row["state"] = rec.get("state")
            row["attempt"] = rec.get("attempt")
        elif kind == "retry":
            row["retries_step"] = rec.get("retries_step")
            row["failure_class"] = rec.get("failure_class")
            row["idempotency_key"] = rec.get("idempotency_key")
        elif kind == "verifier_decision":
            row["requirement"] = rec.get("requirement")
            row["result"] = rec.get("result")
        elif kind == "terminal_transaction":
            row["terminal_status"] = rec.get("terminal_status")
        index_rows.append(row)
    return index_rows


def write_index(ledger_file: Union[str, Path], index_path: Union[str, Path]) -> Path:
    """Materialize the rebuilt index to an append-only JSONL file and return its path."""
    rows = rebuild_index(ledger_file)
    out = Path(index_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        for r in rows
    ]
    out.write_text(("\n".join(lines) + ("\n" if lines else "")), encoding="utf-8")
    return out


def _snapshot_payload(snapshot: run_engine.RunStateSnapshot) -> Dict[str, Any]:
    """Build an ANSI-free machine payload from a run state snapshot."""
    return {
        "run_id": snapshot.run_id,
        "run_state": snapshot.state,
        "workflow_id": snapshot.workflow_id,
        "record_count": snapshot.record_count,
        "steps": {
            sid: {
                "state": st.state,
                "attempts": st.attempts,
                "last_attempt_state": st.last_attempt_state,
            }
            for sid, st in sorted(snapshot.steps.items())
        },
        "approvals": dict(snapshot.approvals),
        "verifier_decisions": dict(snapshot.verifier_decisions),
        "cancellation_reason": snapshot.cancellation_reason,
    }


# ---- start ---------------------------------------------------------------------------------------


def _run_start(args: argparse.Namespace) -> int:
    """Release + start a runnable step (pending -> runnable -> running) through the engine."""
    ledger_file, code = _resolve_or_error(args)
    if ledger_file is None:
        return code
    engine, _records, code = _build_engine(args, ledger_file)
    if engine is None:
        return code

    step_id = getattr(args, "step", None)
    if not step_id:
        return _emit_error(
            args, "start requires --step <step-id>", EXIT_INVALID_INVOCATION
        )
    actor = getattr(args, "actor", None) or "runtime"

    try:
        with engine.lease():
            runnable_ids = {s.step_id for s in engine.get_runnable_steps()}
            step = engine.reconstruct_state().steps.get(step_id)
            if step is None:
                return _emit_error(
                    args, f"unknown step '{step_id}'", EXIT_INVALID_INVOCATION
                )
            if step.state == run_state.STATE_PENDING and step_id not in runnable_ids:
                return _emit_error(
                    args,
                    f"step '{step_id}' is not runnable (unsatisfied dependencies or gates)",
                    EXIT_BLOCKED,
                )
            if step.state == run_state.STATE_PENDING:
                engine.release_step(step_id, actor=actor)
            engine.start_step(step_id, actor=actor)
    except store.LedgerLockError as exc:
        return _emit_error(args, f"lock contention: {exc}", EXIT_OPERATIONAL)
    except run_state.RunStateError as exc:
        return _emit_error(
            args, f"illegal/unauthorized transition: {exc}", EXIT_OPERATIONAL
        )
    except store.LedgerCorruption as exc:
        return _emit_error(args, f"ledger corruption: {exc}", EXIT_CORRUPTED_LEDGER)

    snapshot = engine.reconstruct_state()
    if _machine(args):
        payload = _snapshot_payload(snapshot)
        payload["started_step"] = step_id
        _emit_machine(args, payload)
    else:
        print(f"Started step {step_id} (state: {snapshot.steps[step_id].state})")
    return EXIT_OK


# ---- next ----------------------------------------------------------------------------------------


def _run_next(args: argparse.Namespace) -> int:
    """List the currently runnable steps according to the DAG and gate approvals."""
    ledger_file, code = _resolve_or_error(args)
    if ledger_file is None:
        return code
    engine, _records, code = _build_engine(args, ledger_file)
    if engine is None:
        return code

    try:
        snapshot = engine.reconstruct_state()
        runnable = engine.get_runnable_steps()
    except store.LedgerCorruption as exc:
        return _emit_error(args, f"ledger corruption: {exc}", EXIT_CORRUPTED_LEDGER)

    runnable_ids = [s.step_id for s in runnable]
    terminal = snapshot.state in run_state.TERMINAL_STATES

    if _machine(args):
        _emit_machine(
            args,
            {
                "run_id": snapshot.run_id,
                "run_state": snapshot.state,
                "runnable_steps": runnable_ids,
                "terminal": terminal,
            },
        )
    else:
        if terminal:
            print(
                f"Run {snapshot.run_id} is terminal ({snapshot.state}); no runnable steps."
            )
        elif runnable_ids:
            print("Runnable steps:")
            for sid in runnable_ids:
                print(f"  - {sid}")
        else:
            print(
                "No runnable steps (waiting on dependencies, gates, or verification)."
            )
    if terminal:
        return EXIT_OK
    return EXIT_OK if runnable_ids else EXIT_BLOCKED


# ---- record --------------------------------------------------------------------------------------


def _run_record(args: argparse.Namespace) -> int:
    """Record a step attempt outcome (performed | blocked | failed) in the append-only ledger."""
    ledger_file, code = _resolve_or_error(args)
    if ledger_file is None:
        return code
    engine, _records, code = _build_engine(args, ledger_file)
    if engine is None:
        return code

    step_id = getattr(args, "step", None)
    outcome = getattr(args, "state", None)
    if not step_id or not outcome:
        return _emit_error(
            args,
            "record requires --step <step-id> --state <performed|blocked|failed>",
            EXIT_INVALID_INVOCATION,
        )
    from agent_workflows import run_ledger_schema as _schema

    if outcome not in _schema.ATTEMPT_STATES:
        return _emit_error(
            args,
            f"invalid --state '{outcome}'; must be one of {sorted(_schema.ATTEMPT_STATES)}",
            EXIT_INVALID_INVOCATION,
        )
    actor = getattr(args, "actor", None) or "executor"

    try:
        # Advance a runnable step through pending -> runnable -> running before recording the
        # outcome, so a single CLI invocation records a durable step_attempt. Running is ephemeral
        # (not persisted), so it must be re-derived within this same process before the append.
        step = engine.reconstruct_state().steps.get(step_id)
        if step is None:
            return _emit_error(
                args, f"unknown step '{step_id}'", EXIT_INVALID_INVOCATION
            )
        if step.state == run_state.STATE_PENDING:
            runnable_ids = {s.step_id for s in engine.get_runnable_steps()}
            if step_id not in runnable_ids:
                return _emit_error(
                    args,
                    f"step '{step_id}' is not runnable (unsatisfied dependencies or gates)",
                    EXIT_BLOCKED,
                )
            engine.release_step(step_id, actor="runtime")
            engine.start_step(step_id, actor="runtime")
        # The engine's record_step_attempt takes the store's single-writer lock internally.
        engine.record_step_attempt(step_id, state=outcome, actor=actor)
    except KeyError:
        return _emit_error(args, f"unknown step '{step_id}'", EXIT_INVALID_INVOCATION)
    except store.LedgerLockError as exc:
        return _emit_error(args, f"lock contention: {exc}", EXIT_OPERATIONAL)
    except run_state.RunStateError as exc:
        return _emit_error(
            args, f"illegal/unauthorized transition: {exc}", EXIT_OPERATIONAL
        )
    except store.LedgerCorruption as exc:
        return _emit_error(args, f"ledger corruption: {exc}", EXIT_CORRUPTED_LEDGER)

    snapshot = engine.reconstruct_state()
    if _machine(args):
        payload = _snapshot_payload(snapshot)
        payload["recorded"] = {"step": step_id, "state": outcome}
        _emit_machine(args, payload)
    else:
        print(f"Recorded attempt: {step_id} -> {outcome}")
    # A recorded failure/blocked outcome is not a success; surface it as blocked.
    if outcome in (run_state.STATE_FAILED, run_state.STATE_BLOCKED):
        return EXIT_BLOCKED
    return EXIT_OK


# ---- resume --------------------------------------------------------------------------------------


def _run_resume(args: argparse.Namespace) -> int:
    """Reconstruct run state from the ledger and report what may safely proceed.

    Refuses to advance when a side effect was interrupted mid-flight (unknown_outcome).
    """
    ledger_file, code = _resolve_or_error(args)
    if ledger_file is None:
        return code
    engine, _records, code = _build_engine(args, ledger_file)
    if engine is None:
        return code

    try:
        report = run_recovery.resume(engine)
    except run_recovery.UnknownOutcomeError as exc:
        unknown = run_recovery.detect_unknown_outcomes(engine)
        if _machine(args):
            _emit_machine(
                args,
                {
                    "ok": False,
                    "error": str(exc),
                    "condition": run_recovery.UNKNOWN_OUTCOME,
                    "unknown_outcome_steps": list(unknown),
                    "exit_code": EXIT_BLOCKED,
                },
            )
        else:
            print(f"error: {exc}")
            print(f"  reconcile these steps before resuming: {list(unknown)}")
        return EXIT_BLOCKED
    except store.LedgerCorruption as exc:
        return _emit_error(args, f"ledger corruption: {exc}", EXIT_CORRUPTED_LEDGER)

    if _machine(args):
        _emit_machine(
            args,
            {
                "run_id": report.run_id,
                "run_state": report.run_state,
                "resumable_steps": list(report.resumable_steps),
                "unknown_outcome_steps": list(report.unknown_outcome_steps),
                "terminal": report.terminal,
            },
        )
    else:
        print(f"Run {report.run_id} state: {report.run_state}")
        if report.terminal:
            print("Run is terminal; nothing to resume.")
        elif report.resumable_steps:
            print("Resumable steps:")
            for sid in report.resumable_steps:
                print(f"  - {sid}")
        else:
            print(
                "No resumable steps (waiting on dependencies, gates, or verification)."
            )
    return EXIT_OK


# ---- cancel --------------------------------------------------------------------------------------


def _run_cancel(args: argparse.Namespace) -> int:
    """Cancel an active run (records a terminal cancellation transaction)."""
    ledger_file, code = _resolve_or_error(args)
    if ledger_file is None:
        return code
    engine, _records, code = _build_engine(args, ledger_file)
    if engine is None:
        return code

    actor = getattr(args, "actor", None) or "coordinator"
    reason = getattr(args, "reason", None) or "cancelled"

    try:
        # cancel_run takes the store's single-writer lock internally.
        snapshot = run_recovery.cancel(engine, reason=reason, actor=actor)
    except store.LedgerLockError as exc:
        return _emit_error(args, f"lock contention: {exc}", EXIT_OPERATIONAL)
    except run_state.RunStateError as exc:
        return _emit_error(
            args, f"illegal/unauthorized cancellation: {exc}", EXIT_OPERATIONAL
        )
    except store.LedgerCorruption as exc:
        return _emit_error(args, f"ledger corruption: {exc}", EXIT_CORRUPTED_LEDGER)

    if _machine(args):
        payload = _snapshot_payload(snapshot)
        payload["cancelled"] = True
        _emit_machine(args, payload)
    else:
        print(f"Cancelled run {snapshot.run_id} (reason: {reason})")
    return EXIT_OK


# ---- status --------------------------------------------------------------------------------------


def _run_status(args: argparse.Namespace) -> int:
    """Report reconstructed run + step state from the ledger (mutating-family status view)."""
    ledger_file, code = _resolve_or_error(args)
    if ledger_file is None:
        return code
    engine, _records, code = _build_engine(args, ledger_file)
    if engine is None:
        return code

    try:
        snapshot = engine.reconstruct_state()
    except store.LedgerCorruption as exc:
        return _emit_error(args, f"ledger corruption: {exc}", EXIT_CORRUPTED_LEDGER)

    if _machine(args):
        _emit_machine(args, _snapshot_payload(snapshot))
    else:
        print(f"Run: {snapshot.run_id}")
        print(f"State: {snapshot.state}")
        print(f"Records: {snapshot.record_count}")
        print("Steps:")
        for sid, st in sorted(snapshot.steps.items()):
            print(f"  {sid}: {st.state} (attempts={st.attempts})")
        if snapshot.cancellation_reason:
            print(f"Cancellation: {snapshot.cancellation_reason}")

    if snapshot.state == run_state.STATE_COMPLETE:
        return EXIT_OK
    if snapshot.state == run_state.STATE_CANCELLED:
        return EXIT_BLOCKED
    return EXIT_INCOMPLETE


# ---- finalize ------------------------------------------------------------------------------------


def _run_finalize(args: argparse.Namespace) -> int:
    """Compute the Order-04 completion predicate and, if satisfied, record terminal completion.

    Requires COORDINATOR authority. Refuses an incomplete/invalid/unauthorized run. Succeeds (exit 0)
    only after the predicates pass and the terminal transaction is recorded.
    """
    ledger_file, code = _resolve_or_error(args)
    if ledger_file is None:
        return code
    engine, records, code = _build_engine(args, ledger_file)
    if engine is None:
        return code

    actor = getattr(args, "actor", None) or "coordinator"
    if actor != "coordinator":
        return _emit_error(
            args,
            f"finalize requires coordinator authority, got actor '{actor}'",
            EXIT_OPERATIONAL,
        )

    # 1. Evidence validity gate (distinct invalid-evidence class).
    evidence_val = evidence.validate_ledger_evidence(records)
    if not evidence_val.ok:
        if _machine(args):
            _emit_machine(
                args,
                {
                    "ok": False,
                    "error": "captured evidence is invalid",
                    "findings": [
                        {"code": f.code, "where": f.where, "message": f.message}
                        for f in evidence_val.findings
                    ],
                    "exit_code": EXIT_INVALID_EVIDENCE,
                },
            )
        else:
            print("error: captured evidence is invalid; refusing to finalize")
            for f in evidence_val.findings:
                print(f"  - {f.code} ({f.where}): {f.message}")
        return EXIT_INVALID_EVIDENCE

    # 2. Completion predicate gate (Order-04 predicate over the ledger).
    evaluation = evidence.evaluate_completion(records, coordinator_authority=True)
    if not evaluation.is_complete:
        if _machine(args):
            _emit_machine(
                args,
                {
                    "ok": False,
                    "error": "run is incomplete; completion predicates not satisfied",
                    "reasons": list(evaluation.reasons),
                    "predicates": {
                        name: {"satisfied": p.satisfied, "details": p.details}
                        for name, p in evaluation.predicates.items()
                    },
                    "exit_code": EXIT_INCOMPLETE,
                },
            )
        else:
            print("error: run is incomplete; refusing to finalize")
            for r in evaluation.reasons:
                print(f"  - {r}")
        return EXIT_INCOMPLETE

    # 3. Record the terminal transaction through the engine (enforces verified -> complete + authority).
    #    complete_run takes the store's single-writer lock internally.
    try:
        snapshot = engine.complete_run(actor=actor)
    except run_state.UnauthorizedActorError as exc:
        return _emit_error(args, f"unauthorized completion: {exc}", EXIT_OPERATIONAL)
    except run_state.PredicateUnsatisfiedError as exc:
        return _emit_error(
            args, f"completion predicates failed: {exc}", EXIT_INCOMPLETE
        )
    except run_state.RunStateError as exc:
        return _emit_error(
            args, f"illegal completion transition: {exc}", EXIT_OPERATIONAL
        )
    except store.LedgerLockError as exc:
        return _emit_error(args, f"lock contention: {exc}", EXIT_OPERATIONAL)
    except store.LedgerCorruption as exc:
        return _emit_error(args, f"ledger corruption: {exc}", EXIT_CORRUPTED_LEDGER)

    if _machine(args):
        payload = _snapshot_payload(snapshot)
        payload["finalized"] = True
        payload["is_complete"] = True
        _emit_machine(args, payload)
    else:
        print(f"Finalized run {snapshot.run_id}: COMPLETE")
    return EXIT_OK
