"""Read-only inspection verbs over the host capability contract (hostcap-01 `mjx7ne` E-06).

WHAT THIS IS FOR. `host_sandbox_profile` decides, by EXECUTED probe, what a host can actually
guarantee, and `preflight_host_capabilities` refuses an action whose requirements a host does
not meet. Both were invisible from the command line: an operator told "this host cannot enforce
X" had no way to ask the host what it CAN enforce, or which actions that permits. These two
verbs answer exactly that and nothing else.

WHY A SEPARATE MODULE. `cli.py` owns registration and dispatch only, matching the owner-verb
shape `reviews`/`specs`/`backlog`/`research` already use: a module with `run_*` entry points
that `cli.py` calls. `host` is a NEW CLI namespace, so this module brings it into existence.

STRICTLY READ-ONLY, WITH ONE HONEST CAVEAT. Nothing here writes, moves, or mutates a
repository file; there is no `--apply` because there is nothing to apply. The caveat is that
`host probe` EXECUTES probes, and the sandbox probe deliberately builds a real jail in a
temporary directory (see `host_sandbox_profile._probe_landlock`) which it removes. So the verb
is read-only with respect to the REPOSITORY, not side-effect-free with respect to the process;
saying "read-only" without that distinction would overclaim.

HONEST LIMIT ON WHAT `capabilities` PROVES. It reports what the CONTRACT says, and the contract
records two capabilities that are DECLARED AND NEVER PROBED because the enforcement they name
does not exist in this repository yet. Those read not-supported on every host, so every action
requiring them is refused. That is fail-closed and correct, and this verb prints the recorded
reason rather than presenting the refusal as a host defect.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List

from agent_workflows import host_sandbox_profile as hsp

#: Hosts these verbs will report on when no host is named. Deliberately the two runner hosts
#: this repository actually drives, not `host_adapters.ALL_ADAPTER_HOSTS`: a capability report
#: for a host nobody runs would be noise, and the report is per-installation anyway.
DEFAULT_HOSTS = ("opencode", "antigravity")


def _capability_rows(caps: hsp.HostSandboxCapabilities) -> List[Dict[str, Any]]:
    """Every boolean capability field with its verdict and recorded probe note.

    Derived by INTROSPECTING the dataclass rather than from a hand-written name list, so a
    field added to the contract cannot silently vanish from the report (the shipped
    `CONTRACT_FIELDS` tuple in the tests is a literal list, and that is exactly how three
    fields once became structurally invisible to a guarantee that appeared to cover them).
    """
    snap = caps.to_dict()
    rows: List[Dict[str, Any]] = []
    for name, value in snap.items():
        if not isinstance(value, bool):
            continue
        rows.append(
            {
                "capability": name,
                "supported": value,
                "runner_safety": name in hsp.RUNNER_SAFETY_CAPABILITIES,
                "note": caps.probe_notes.get(name, ""),
            }
        )
    return rows


def _action_rows(caps: hsp.HostSandboxCapabilities, host: str) -> List[Dict[str, Any]]:
    """Per-action verdicts for this descriptor, in the spec's action-class order."""
    rows: List[Dict[str, Any]] = []
    for action in hsp.ACTION_CLASSES:
        verdict = hsp.check_action_capabilities(action, caps, host=host)
        rows.append(verdict.to_dict())
    return rows


def _describe_host(host: str) -> Dict[str, Any]:
    """The full read-only report for one host: contract snapshot + per-action verdicts."""
    caps = hsp.detect_host_capabilities(host)
    return {
        "host": host,
        "platform": caps.platform,
        "sandbox_mechanism": caps.sandbox_mechanism,
        "capabilities": _capability_rows(caps),
        "actions": _action_rows(caps, host),
        "probe_notes": dict(caps.probe_notes),
    }


def _write_human(report: Dict[str, Any], out: Any) -> None:
    """Render one host's report as plain aligned text."""
    out.write(
        "host {0}  platform={1}  sandbox_mechanism={2}\n".format(
            report["host"],
            report["platform"] or "?",
            report["sandbox_mechanism"] or "none",
        )
    )
    for row in report["capabilities"]:
        mark = "yes" if row["supported"] else "NO"
        tag = " (runner-safety)" if row["runner_safety"] else ""
        out.write("  {0:<4} {1}{2}\n".format(mark, row["capability"], tag))
        if row["note"]:
            out.write("       why: {0}\n".format(row["note"]))
    out.write("  actions:\n")
    for row in report["actions"]:
        if row["satisfied"]:
            out.write("    ALLOWED  {0}\n".format(row["action"]))
        else:
            out.write(
                "    REFUSED  {0}  missing: {1}\n".format(
                    row["action"], ", ".join(row["missing"])
                )
            )
        if row["unrepresented"]:
            out.write(
                "             not representable by this contract: {0}\n".format(
                    ", ".join(row["unrepresented"])
                )
            )


def _emit(
    args, command: str, target, reports: List[Dict[str, Any]], summary: str
) -> int:
    """Emit the report through the shared renderer boundary (agent/JSON) or as text."""
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import CommandResult, Evidence, select_output

    ctx = select_output(args)
    if ctx.is_agent or ctx.is_json:
        res = CommandResult(
            command=command,
            status="clean",
            exit_code=0,
            summary=summary,
            evidence=[
                Evidence(
                    key=r["host"],
                    value={
                        "platform": r["platform"],
                        "sandbox_mechanism": r["sandbox_mechanism"],
                        "supported": sorted(
                            row["capability"]
                            for row in r["capabilities"]
                            if row["supported"]
                        ),
                        "allowed_actions": sorted(
                            row["action"] for row in r["actions"] if row["satisfied"]
                        ),
                    },
                    status="clean",
                )
                for r in reports
            ],
            data={
                "hosts": reports,
                "action_classes": list(hsp.ACTION_CLASSES),
                "runner_safety_capabilities": list(hsp.RUNNER_SAFETY_CAPABILITIES),
                "unrepresented_spec_capabilities": dict(
                    hsp.UNREPRESENTED_SPEC_CAPABILITIES
                ),
                "finding_code": hsp.RUN_HOST_CAPABILITY,
            },
            target=target,
            verified=True,
            complete=True,
        )
        return get_renderer(ctx).emit(res, ctx)

    out = sys.stdout
    for r in reports:
        _write_human(r, out)
    out.write("\n{0}\n".format(summary))
    return 0


def run_probe(args) -> int:
    """`aw host probe <host>`: execute the capability probes and report what they observed.

    Read-only with respect to the repository (see the module docstring's caveat about the
    sandbox probe's temporary jail). Exit contract is `(0, 2)`: 0 whenever the probes could
    run, whatever they concluded, because "this host cannot enforce X" is a legitimate ANSWER
    and not a failure of the asking; 2 only for a usage error such as conflicting output
    flags. There is deliberately no exit 1 - a capability the host lacks is reported by
    `preflight_host_capabilities` when an ACTION needs it, and refusing here would make an
    honest not-supported look like a broken command.
    """
    host = getattr(args, "host", None) or DEFAULT_HOSTS[0]
    report = _describe_host(host)
    supported = [r["capability"] for r in report["capabilities"] if r["supported"]]
    refused = [r["action"] for r in report["actions"] if not r["satisfied"]]
    summary = (
        "{0}: {1} of {2} capabilities supported; {3} of {4} actions refused".format(
            host,
            len(supported),
            len(report["capabilities"]),
            len(refused),
            len(report["actions"]),
        )
    )
    return _emit(args, "host probe", host, [report], summary)


def run_capabilities(args) -> int:
    """`aw host capabilities [host]`: print the capability contract and per-action verdicts.

    With no host, reports every host in `DEFAULT_HOSTS`. Same exit contract and same
    read-only posture as `run_probe`; the two differ in framing, not in safety: `probe` asks
    about ONE host, `capabilities` surveys the contract across hosts.
    """
    host = getattr(args, "host", None)
    hosts = [host] if host else list(DEFAULT_HOSTS)
    reports = [_describe_host(h) for h in hosts]
    total_refused = sum(
        1 for r in reports for row in r["actions"] if not row["satisfied"]
    )
    summary = "{0} host(s) reported; {1} (host, action) pair(s) refused".format(
        len(reports), total_refused
    )
    return _emit(args, "host capabilities", host, reports, summary)


__all__ = ["DEFAULT_HOSTS", "run_probe", "run_capabilities"]
