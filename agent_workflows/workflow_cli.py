"""`aw workflow` CLI handlers: validate / compile / check-generated.

awoptimize Order 01 (`nmwy3m`) E-06. Thin CLI layer over the pure engines:

  * `aw workflow validate <pkg>...`  - load + schema-validate a canonical package (read-only).
  * `aw workflow compile <pkg>...`   - compile to generated projections; write only with --apply.
  * `aw workflow check-generated <pkg>...` - fail if any `_generated/` file drifts from a fresh
                                             compile or was hand-edited (read-only).

Contract (mirrors the repository's other machine-facing CLIs and the E-06 acceptance):

  * exit 0 = success; exit 1 = a conformance/validation/drift failure the caller must fix;
    exit 2 = an invocation/internal error (bad path, unreadable). These are never conflated.
  * `--agent` (and `--json`) emit machine-readable output with NO ANSI; human mode is the default.
  * `validate` and `check-generated` make NO filesystem writes, ever. `compile` is dry-run by
    default and writes generated files only under `--apply` (mirrors the repo's write-tool
    precedent), atomically.

The heavy lifting is in the pure modules (workflow_schema/source/loader/compiler/profile); this file
only parses args, sequences calls, formats output, and maps outcomes to exit codes.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent_workflows import workflow_compiler as _compiler
from agent_workflows import workflow_loader as _loader
from agent_workflows import workflow_source as _source


def run_workflow(args: argparse.Namespace) -> int:
    """Dispatch `aw workflow <subcommand>`. Returns the process exit code."""

    sub = getattr(args, "workflow_command", None)
    if sub == "validate":
        return _run_validate(args)
    if sub == "compile":
        return _run_compile(args)
    if sub == "check-generated":
        return _run_check_generated(args)
    print("usage: aw workflow {validate|compile|check-generated} <package>...")
    return 2


def _packages(args: argparse.Namespace) -> List[Path]:
    raw = getattr(args, "path", None) or []
    return [Path(p) for p in raw]


def _machine(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "agent", False) or getattr(args, "json", False))


# Loader finding codes that mean "you pointed me at something that is not a resolvable package" -
# an INVOCATION error (exit 2), distinct from a conformance/schema failure of a real package (exit 1).
_INVOCATION_CODES = frozenset(("WF-L001",))


def _is_invocation_failure(result: Any) -> bool:
    return (not result.ok) and any(f.code in _INVOCATION_CODES for f in result.findings)


# --------------------------------------------------------------------------------------
# validate (read-only)
# --------------------------------------------------------------------------------------


def _run_validate(args: argparse.Namespace) -> int:
    packages = _packages(args)
    if not packages:
        print("error: no package given")
        return 2
    machine = _machine(args)
    any_fail = False
    any_invocation = False
    records: List[Dict[str, Any]] = []
    for pkg in packages:
        try:
            result = _loader.load_package(pkg)
        except Exception as exc:  # noqa: BLE001 - an unexpected load error is an invocation failure
            print("error: could not load {0}: {1}".format(pkg, exc))
            return 2
        ok = result.ok
        any_fail = any_fail or not ok
        any_invocation = any_invocation or _is_invocation_failure(result)
        if machine:
            records.append(
                {
                    "package": str(pkg),
                    "ok": ok,
                    "findings": [
                        {"code": f.code, "where": f.where, "message": f.message}
                        for f in result.findings
                    ],
                }
            )
        else:
            if ok:
                print("ok: {0}".format(pkg))
            else:
                print("FAIL: {0}".format(pkg))
                for f in result.findings:
                    print("  {0} {1}: {2}".format(f.code, f.where, f.message))
    if machine:
        _emit_machine(args, records)
    if any_invocation:
        return 2
    return 1 if any_fail else 0


# --------------------------------------------------------------------------------------
# compile (dry-run by default; writes only under --apply)
# --------------------------------------------------------------------------------------


def _run_compile(args: argparse.Namespace) -> int:
    packages = _packages(args)
    if not packages:
        print("error: no package given")
        return 2
    apply = bool(getattr(args, "apply", False))
    machine = _machine(args)
    any_fail = False
    any_invocation = False
    records: List[Dict[str, Any]] = []
    for pkg in packages:
        result = _loader.load_package(pkg)
        if not result.ok or result.ir is None:
            any_fail = True
            any_invocation = any_invocation or _is_invocation_failure(result)
            if machine:
                records.append(
                    {
                        "package": str(pkg),
                        "ok": False,
                        "findings": [
                            {"code": f.code, "where": f.where, "message": f.message}
                            for f in result.findings
                        ],
                    }
                )
            else:
                print("FAIL (cannot compile invalid package): {0}".format(pkg))
                for f in result.findings:
                    print("  {0} {1}: {2}".format(f.code, f.where, f.message))
            continue
        compiled = _compiler.compile_workflow(result.ir)
        files = _compiler.render_generated_files(compiled)
        if apply:
            written = _write_generated(Path(result.ir["source_root"]), files)
            action = "wrote"
        else:
            written = sorted(files.keys())
            action = "would write"
        if machine:
            records.append(
                {"package": str(pkg), "ok": True, "action": action, "files": written}
            )
        else:
            print(
                "{0} {1} generated file(s) for {2}:".format(action, len(written), pkg)
            )
            for rel in written:
                print("  {0}".format(rel))
    if machine:
        _emit_machine(args, records)
    if any_invocation:
        return 2
    return 1 if any_fail else 0


def _write_generated(source_root: Path, files: Dict[str, str]) -> List[str]:
    """Write each generated file atomically (temp + os.replace) under the package root. Creates parent
    dirs as needed. Returns the sorted list of written relative paths."""

    written: List[str] = []
    for rel in sorted(files.keys()):
        target = source_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=".wf-gen-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(files[rel])
            os.replace(tmp, str(target))
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        written.append(rel)
    return written


# --------------------------------------------------------------------------------------
# check-generated (read-only drift check)
# --------------------------------------------------------------------------------------


def _run_check_generated(args: argparse.Namespace) -> int:
    packages = _packages(args)
    if not packages:
        print("error: no package given")
        return 2
    machine = _machine(args)
    any_fail = False
    any_invocation = False
    records: List[Dict[str, Any]] = []
    for pkg in packages:
        result = _loader.load_package(pkg)
        if not result.ok or result.ir is None:
            any_fail = True
            any_invocation = any_invocation or _is_invocation_failure(result)
            _report_pkg_load_fail(machine, records, pkg, result)
            continue
        expected = _compiler.render_generated_files(
            _compiler.compile_workflow(result.ir)
        )
        drift = _compute_drift(Path(result.ir["source_root"]), expected)
        if drift:
            any_fail = True
        if machine:
            records.append({"package": str(pkg), "ok": not drift, "drift": drift})
        else:
            if not drift:
                print("ok (generated matches source): {0}".format(pkg))
            else:
                print("DRIFT: {0}".format(pkg))
                for kind, rel in drift:
                    print("  {0}: {1}".format(kind, rel))
    if machine:
        _emit_machine(args, records)
    if any_invocation:
        return 2
    return 1 if any_fail else 0


def _compute_drift(
    source_root: Path, expected: Dict[str, str]
) -> List[Tuple[str, str]]:
    """Return a sorted list of (kind, rel) drift records. kind is 'missing' (expected file absent),
    'changed' (on-disk bytes differ from a fresh compile), or 'unexpected' (a `_generated/` file that
    the compiler would not produce, i.e. hand-added)."""

    drift: List[Tuple[str, str]] = []
    for rel, text in expected.items():
        target = source_root / rel
        if not target.is_file():
            drift.append(("missing", rel))
        elif target.read_text(encoding="utf-8") != text:
            drift.append(("changed", rel))
    # unexpected files under _generated/
    gen_root = source_root / _source.GENERATED_DIRNAME
    if gen_root.is_dir():
        for path in gen_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(source_root).as_posix()
            if _source.is_ignored_rel(path.relative_to(source_root).parts):
                # ignore __pycache__/.pyc under _generated
                if path.suffix in (".pyc", ".pyo") or "__pycache__" in path.parts:
                    continue
            if rel not in expected:
                drift.append(("unexpected", rel))
    return sorted(drift)


def _report_pkg_load_fail(
    machine: bool, records: List[Dict[str, Any]], pkg: Path, result: Any
) -> None:
    if machine:
        records.append(
            {
                "package": str(pkg),
                "ok": False,
                "findings": [
                    {"code": f.code, "where": f.where, "message": f.message}
                    for f in result.findings
                ],
            }
        )
    else:
        print("FAIL (cannot load package): {0}".format(pkg))
        for f in result.findings:
            print("  {0} {1}: {2}".format(f.code, f.where, f.message))


def _emit_machine(args: argparse.Namespace, records: List[Dict[str, Any]]) -> None:
    """Emit machine-readable output with NO ANSI. `--agent` = one JSON object per line (jsonl);
    `--json` = a single pretty JSON array. Both are stable and colorless."""

    if getattr(args, "agent", False):
        for rec in records:
            print(
                json.dumps(
                    rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                )
            )
    else:  # --json
        print(json.dumps(records, sort_keys=True, indent=2, ensure_ascii=False))
