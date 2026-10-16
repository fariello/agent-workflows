"""Pytest plugin to probe declared aw command leaves driven by tests.

Loaded via: pytest -p tests.tools.leaf_probe

Records declared leaves driven by:
(a) in-process dispatch via argparse.ArgumentParser.parse_known_args for prog='agent-workflows'
(b) subprocess dispatch via subprocess.Popen.__init__ for argv containing -m agent_workflows

A leaf is the longest positional prefix in command_surface.get_declared_leaves().
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import shlex
import subprocess
import sys
from typing import Any

from agent_workflows import command_surface

_DECLARED_LEAVES: set[str] = set()
_DRIVEN_LEAVES: dict[str, set[str]] = collections.defaultdict(set)
_PATCHED = False


def _get_declared() -> set[str]:
    global _DECLARED_LEAVES
    if not _DECLARED_LEAVES:
        _DECLARED_LEAVES = set(command_surface.get_declared_leaves())
    return _DECLARED_LEAVES


def _extract_leaf(argv: list[str]) -> str | None:
    declared = _get_declared()
    words = [arg for arg in argv if not arg.startswith("-")]
    for length in range(len(words), 0, -1):
        candidate = " ".join(words[:length])
        if candidate in declared:
            return candidate
    return None


def _record_leaf(argv: list[str]) -> None:
    leaf = _extract_leaf(argv)
    if leaf:
        current_test = os.environ.get("PYTEST_CURRENT_TEST", "")
        nodeid = current_test.split(" ")[0] if current_test else "<unknown>"
        _DRIVEN_LEAVES[leaf].add(nodeid)


def _patch_dispatchers() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    # (a) In-process dispatch
    orig_parse_known_args = argparse.ArgumentParser.parse_known_args

    def probed_parse_known_args(
        self: Any, args: Any = None, namespace: Any = None
    ) -> Any:
        if getattr(self, "prog", None) == "agent-workflows":
            actual_args = list(args) if args is not None else list(sys.argv[1:])
            _record_leaf(actual_args)
        return orig_parse_known_args(self, args=args, namespace=namespace)

    argparse.ArgumentParser.parse_known_args = probed_parse_known_args

    # (b) Subprocess dispatch
    orig_popen_init = subprocess.Popen.__init__

    def probed_popen_init(self: Any, args: Any, *a: Any, **kw: Any) -> Any:
        try:
            tokens: list[str] = []
            if isinstance(args, str):
                tokens = shlex.split(args)
            elif isinstance(args, (list, tuple)):
                tokens = [str(t) for t in args]
            if tokens:
                for i in range(len(tokens) - 1):
                    if tokens[i] == "-m" and tokens[i + 1] in (
                        "agent_workflows",
                        "agent_workflows.cli",
                    ):
                        _record_leaf(tokens[i + 2 :])
                        break
                    base = os.path.basename(tokens[i])
                    if base in ("aw", "agent-workflows", "agentwf"):
                        _record_leaf(tokens[i + 1 :])
                        break
                else:
                    if tokens:
                        base = os.path.basename(tokens[0])
                        if base in ("aw", "agent-workflows", "agentwf"):
                            _record_leaf(tokens[1:])
        except Exception:
            pass
        return orig_popen_init(self, args, *a, **kw)

    subprocess.Popen.__init__ = probed_popen_init


_patch_dispatchers()


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("leaf_probe", "leaf probe plugin options")
    group.addoption(
        "--leaf-probe-out",
        dest="leaf_probe_out",
        default=None,
        help="Path to write leaf probe JSON report.",
    )


def pytest_configure(config: Any) -> None:
    _patch_dispatchers()
    if config.pluginmanager.hasplugin("xdist"):

        class _XdistLeafProbeHooks:
            def pytest_testnodedown(self, node: Any, error: Any) -> None:
                worker_output = getattr(node, "workeroutput", {})
                if worker_output and "leaf_probe_driven" in worker_output:
                    for leaf, nodes in worker_output["leaf_probe_driven"].items():
                        _DRIVEN_LEAVES[leaf].update(nodes)

        config.pluginmanager.register(_XdistLeafProbeHooks(), name="leaf_probe_xdist")


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    config = getattr(session, "config", None)
    if config and hasattr(config, "workeroutput"):
        config.workeroutput["leaf_probe_driven"] = {
            leaf: list(nodes) for leaf, nodes in _DRIVEN_LEAVES.items()
        }


def pytest_terminal_summary(
    terminalreporter: Any, exitstatus: Any, config: Any
) -> None:
    declared = _get_declared()
    driven = set(_DRIVEN_LEAVES.keys())
    missing = declared - driven

    out_path = config.getoption("leaf_probe_out") or os.environ.get("LEAF_PROBE_OUT")
    if out_path:
        payload = {
            "declared_count": len(declared),
            "driven_count": len(driven),
            "missing_count": len(missing),
            "driven_leaves": {
                leaf: sorted(list(nodes))
                for leaf, nodes in sorted(_DRIVEN_LEAVES.items())
            },
            "missing_leaves": sorted(list(missing)),
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    terminalreporter.section("Leaf probe")
    terminalreporter.write_line(
        f"Leaf probe: {len(driven)}/{len(declared)} declared leaves driven "
        f"({len(driven) / len(declared) * 100:.1f}%)"
    )
    if missing:
        missing_list = ", ".join(sorted(missing)[:15])
        if len(missing) > 15:
            missing_list += f" ... (+{len(missing) - 15} more)"
        terminalreporter.write_line(f"Missing leaves ({len(missing)}): {missing_list}")
