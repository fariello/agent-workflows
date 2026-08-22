"""`aw run` CLI handlers: show / evidence / verify-ledger.

awoptimize Order 04 (`yndh7k`) E-04.

Inspection CLI layer over run ledger and evidence verification:
  * `aw run show <target>`          - inspect run status, steps, verifier decisions, and completion.
  * `aw run evidence <target>`      - list and validate captured evidence envelopes and tool events.
  * `aw run verify-ledger <target>` - verify SHA-256 hash chaining and evidence validity.

Contract:
  * exit 0 = success / clean / complete;
    exit 1 = incomplete / invalid evidence / unsatisfied requirements;
    exit 2 = invocation error, missing ledger, or corrupted hash chain / unparseable JSON.
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

from agent_workflows import run_evidence as evidence
from agent_workflows import run_ledger_store as store


def run_cli(args: argparse.Namespace) -> int:
    """Dispatch `aw run <subcommand>`. Returns the process exit code."""
    sub = getattr(args, "run_command", None)
    if sub == "show":
        return _run_show(args)
    if sub == "evidence":
        return _run_evidence(args)
    if sub == "verify-ledger":
        return _run_verify_ledger(args)
    print(
        "usage: aw run {show|evidence|verify-ledger} <run-id-or-path> [--agent|--json] [--dir <dir>]"
    )
    return 2


def _machine(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "as_agent", False) or getattr(args, "as_json", False))


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
    if getattr(args, "as_agent", False):
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


def resolve_ledger_path(
    target: str, repo_root: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """Resolve a target argument (run id or path) to a concrete ledger JSONL path."""
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
        root / ".aw" / "state" / "runs" / target / "events.jsonl",
        root / ".aw" / "records" / "runs" / target / "events.jsonl",
        root / ".aw" / "state" / "runs" / target,
        root / ".aw" / "runs" / target / "events.jsonl",
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
    chain_ver = ledger_store.verify_chain(raise_on_error=False)

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
