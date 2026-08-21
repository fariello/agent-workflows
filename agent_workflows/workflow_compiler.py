"""Deterministic workflow compiler: normalized IR -> portable generated projections.

awoptimize Order 01 (`nmwy3m`) E-04. Consumes the normalized IR produced by the loader (E-03) and
emits the six projection forms the architecture needs, all deterministically:

  1. prompt_bundle  - a portable Markdown prompt assembled from the entry + resource bodies.
  2. step_packets   - one bounded just-in-time packet per step (the runtime releases these one at a
                      time; each carries only what that step needs + its evidence contract).
  3. manifest       - a machine-readable JSON manifest (identity, intent, risk, ids, digests).
  4. evidence       - the evidence requirements per requirement + validation (what must be captured).
  5. catalog_row    - a single human catalog row (command | intent | risk | summary), manifest-style.
  6. command_descriptor - an adapter-neutral command descriptor host adapters (Order 05) specialize.

Determinism (the E-04 acceptance): identical source yields BYTE-IDENTICAL normalized outputs across
two clean runs. Achieved by (a) sorting all mapping keys and using fixed JSON separators at emit
time, and (b) ordering every list EXPLICITLY (steps by id, requirements by id, resources by path) so
nothing depends on filesystem enumeration or dict insertion order. Per D139 the JSON emit needs no
dependency (stdlib `json`), so this module is import-safe in any context; it does not read the
filesystem, call a model, or use the network - it is a pure IR -> artifacts transform.

This module compiles STRUCTURE; it does not establish that a workflow is semantically correct (that
remains review's job), and it never performs a lifecycle transition.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Tuple

COMPILER_VERSION = 1

# The six projection keys, fixed so consumers and the drift check (E-06) agree on the set.
PROJECTION_KEYS: Tuple[str, ...] = (
    "prompt_bundle",
    "step_packets",
    "manifest",
    "evidence",
    "catalog_row",
    "command_descriptor",
)


class CompileError(Exception):
    """Raised when asked to compile something that is not a valid IR (fail closed). The loader
    guarantees a valid IR, so this only trips on misuse (e.g. compiling raw entry data)."""


def _require_ir(ir: Any) -> Dict[str, Any]:
    if not isinstance(ir, Mapping) or "workflow" not in ir or "resources" not in ir:
        raise CompileError(
            "compile() requires a normalized IR from workflow_loader.load_package"
        )
    return dict(ir)


def _dumps(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact fixed separators, trailing newline. Byte-stable."""

    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    )


def _sorted_steps(workflow: Mapping[str, Any]) -> List[Dict[str, Any]]:
    steps = [s for s in workflow.get("steps", []) if isinstance(s, Mapping)]
    return [dict(s) for s in sorted(steps, key=lambda s: str(s.get("id")))]


def _sorted_requirements(workflow: Mapping[str, Any]) -> List[Dict[str, Any]]:
    reqs = [r for r in workflow.get("requirements", []) if isinstance(r, Mapping)]
    return [dict(r) for r in sorted(reqs, key=lambda r: str(r.get("id")))]


def _sorted_validations(workflow: Mapping[str, Any]) -> List[Dict[str, Any]]:
    vals = [v for v in workflow.get("validations", []) if isinstance(v, Mapping)]
    return [dict(v) for v in sorted(vals, key=lambda v: str(v.get("verifies")))]


def compile_workflow(ir: Any) -> Dict[str, Any]:
    """Compile a normalized IR into the six projection forms. Returns a mapping keyed by
    :data:`PROJECTION_KEYS`. Deterministic and side-effect-free."""

    ir_map = _require_ir(ir)
    workflow: Dict[str, Any] = dict(ir_map["workflow"])
    resources: Dict[str, Any] = dict(ir_map.get("resources", {}))
    wf_id = str(workflow.get("id"))

    steps = _sorted_steps(workflow)
    requirements = _sorted_requirements(workflow)
    validations = _sorted_validations(workflow)

    return {
        "prompt_bundle": _compile_prompt_bundle(workflow, resources, steps),
        "step_packets": _compile_step_packets(wf_id, workflow, resources, steps),
        "manifest": _compile_manifest(ir_map, workflow, steps, requirements),
        "evidence": _compile_evidence(wf_id, requirements, validations),
        "catalog_row": _compile_catalog_row(workflow),
        "command_descriptor": _compile_command_descriptor(workflow),
    }


def _resource_text(resources: Mapping[str, Any], rel: str) -> str:
    entry = resources.get(rel)
    if isinstance(entry, Mapping) and isinstance(entry.get("text"), str):
        return entry["text"]
    return ""


def _compile_prompt_bundle(
    workflow: Mapping[str, Any],
    resources: Mapping[str, Any],
    steps: List[Dict[str, Any]],
) -> str:
    """A portable Markdown prompt: title, summary, then each referenced resource in the entry's
    declared order (deterministic because the entry list is authored order, not FS order), then a
    compact step outline. Ends with a trailing newline for byte-stability."""

    lines: List[str] = []
    lines.append("# Workflow: {0}".format(workflow.get("id")))
    lines.append("")
    lines.append(str(workflow.get("summary", "")).strip())
    lines.append("")
    # resources in the entry's declared order (closure guaranteed by the loader)
    declared = [r for r in workflow.get("resources", []) if isinstance(r, str)]
    for rel in declared:
        body = _resource_text(resources, rel).rstrip("\n")
        lines.append("<!-- resource: {0} -->".format(rel))
        lines.append(body)
        lines.append("")
    # compact step outline (sorted by id)
    lines.append("## Steps")
    for s in steps:
        lines.append("- {0}: {1}".format(s.get("id"), str(s.get("action", "")).strip()))
    text = "\n".join(lines).rstrip("\n") + "\n"
    return text


def _compile_step_packets(
    wf_id: str,
    workflow: Mapping[str, Any],
    resources: Mapping[str, Any],
    steps: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """One bounded packet per step, sorted by step id. Each packet carries only that step's
    action, the requirements it satisfies, its dependencies, its evidence contract, and any
    step-local body resource (a `steps/<id>...` resource if one is referenced). No global prose."""

    declared = [r for r in workflow.get("resources", []) if isinstance(r, str)]
    packets: List[Dict[str, Any]] = []
    for s in steps:
        sid = str(s.get("id"))
        # a step body is any declared resource under steps/ whose filename starts with the numeric
        # suffix of the step id (e.g. S-01 -> steps/01-*.md); best-effort, deterministic.
        num = sid.split("-", 1)[-1]
        body_rel = next(
            (
                r
                for r in declared
                if r.startswith("steps/") and r.split("/", 1)[1].startswith(num)
            ),
            None,
        )
        packets.append(
            {
                "workflow": wf_id,
                "step": sid,
                "action": str(s.get("action", "")).strip(),
                "satisfies": sorted(
                    str(x) for x in s.get("satisfies", []) if isinstance(x, str)
                ),
                "depends_on": sorted(
                    str(x) for x in s.get("depends_on", []) if isinstance(x, str)
                ),
                "evidence": sorted(
                    str(x) for x in s.get("evidence", []) if isinstance(x, str)
                ),
                "stop_conditions": [
                    str(x) for x in s.get("stop_conditions", []) if isinstance(x, str)
                ],
                "body": _resource_text(resources, body_rel).rstrip("\n")
                if body_rel
                else "",
                "body_resource": body_rel,
            }
        )
    return packets


def _compile_manifest(
    ir_map: Mapping[str, Any],
    workflow: Mapping[str, Any],
    steps: List[Dict[str, Any]],
    requirements: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Machine-readable manifest: identity, classification, ids, and the source digest that binds the
    compiled output to exact source bytes."""

    return {
        "compiler_version": COMPILER_VERSION,
        "source_digest": ir_map.get("digest"),
        "id": workflow.get("id"),
        "aliases": sorted(
            str(a) for a in workflow.get("aliases", []) if isinstance(a, str)
        ),
        "intent": workflow.get("intent"),
        "risk": workflow.get("risk"),
        "interaction": workflow.get("interaction"),
        "mutation_boundary": workflow.get("mutation_boundary"),
        "host_capabilities": sorted(
            str(c) for c in workflow.get("host_capabilities", []) if isinstance(c, str)
        ),
        "requirement_ids": [str(r.get("id")) for r in requirements],
        "step_ids": [str(s.get("id")) for s in steps],
        "resumable": bool(workflow.get("resumable", False)),
    }


def _compile_evidence(
    wf_id: str, requirements: List[Dict[str, Any]], validations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Evidence requirements: per requirement, the evidence kinds that must be captured; and per
    validation, the target requirement + its evidence kinds. The runtime (Order 02/03) consumes
    this to know what a valid completion needs."""

    return {
        "workflow": wf_id,
        "requirements": [
            {
                "id": str(r.get("id")),
                "evidence": sorted(
                    str(e) for e in r.get("evidence", []) if isinstance(e, str)
                ),
            }
            for r in requirements
        ],
        "validations": [
            {
                "verifies": str(v.get("verifies")),
                "evidence": sorted(
                    str(e) for e in v.get("evidence", []) if isinstance(e, str)
                ),
            }
            for v in validations
        ],
    }


def _compile_catalog_row(workflow: Mapping[str, Any]) -> Dict[str, Any]:
    """A single human-facing catalog row. Kept as structured data; the manifest/doc generator renders
    it to a Markdown table row so the row and the machine data cannot drift."""

    return {
        "command": workflow.get("id"),
        "intent": workflow.get("intent"),
        "risk": workflow.get("risk"),
        "interaction": workflow.get("interaction"),
        "summary": str(workflow.get("summary", "")).strip(),
        "aliases": sorted(
            str(a) for a in workflow.get("aliases", []) if isinstance(a, str)
        ),
    }


def _compile_command_descriptor(workflow: Mapping[str, Any]) -> Dict[str, Any]:
    """Adapter-neutral command descriptor. Host adapters (Order 05) specialize this into a native
    shim; it names the canonical command, whether it takes an argument, and the mutation boundary so
    an adapter can request the right permissions."""

    return {
        "command": workflow.get("id"),
        "aliases": sorted(
            str(a) for a in workflow.get("aliases", []) if isinstance(a, str)
        ),
        "takes_argument": workflow.get("interaction") != "noninteractive",
        "mutation_boundary": workflow.get("mutation_boundary"),
        "interaction": workflow.get("interaction"),
    }


def render_generated_files(compiled: Mapping[str, Any]) -> Dict[str, str]:
    """Render the compiled projections to a deterministic map of `_generated/`-relative filename ->
    exact file text. This is what the compiler CLI (E-06) would write and what `check-generated`
    hashes. Byte-stable: JSON via :func:`_dumps`, Markdown already newline-normalized."""

    manifest = compiled["manifest"]
    files: Dict[str, str] = {}
    files["{0}/prompt.md".format(_GEN)] = compiled["prompt_bundle"]
    files["{0}/manifest.json".format(_GEN)] = _dumps(manifest)
    files["{0}/evidence.json".format(_GEN)] = _dumps(compiled["evidence"])
    files["{0}/catalog-row.json".format(_GEN)] = _dumps(compiled["catalog_row"])
    files["{0}/command.json".format(_GEN)] = _dumps(compiled["command_descriptor"])
    # step packets: one file per step, name by step id (already deterministic + sorted upstream)
    for packet in compiled["step_packets"]:
        files["{0}/packets/{1}.json".format(_GEN, packet["step"])] = _dumps(packet)
    return files


_GEN = "_generated"
