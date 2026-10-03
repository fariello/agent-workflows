"""Behavioral guards for runner backlog-close delegation and host-independence.

This test module guards two essential architectural properties between the runner host
drivers (`oc_runipd` and `agy_runipd`) and `runner_shared`:

1. WHICH TWO PROPERTIES ARE GUARDED:
   (a) BACKLOG-CLOSE DELEGATION: Each of the four backlog-close wrappers
       (`collect_earned_paths`, `close_backlog_item`, `commit_backlog_close`,
       `process_backlog_close`) on BOTH host drivers resolves `runner_shared.<same name>`
       at call time, forwards its return value unchanged, and injects THIS host's
       `run_checked` rather than the peer host's. In addition, `process_backlog_close`
       injects this host's `close_backlog_item`, `commit_backlog_close` (late-bound so
       in-tree spy tests work), and this host's command label (`host_label`). For the
       eleven shared symbols that are direct re-exports rather than wrappers, object
       identity is preserved (`oc.<name> is agy.<name> is runner_shared.<name>`).
   (b) HOST-INDEPENDENCE: Neither host driver depends on or imports its peer driver. In a
       fresh interpreter subprocess with a `sys.meta_path` finder blocking any import of the
       peer driver with an `ImportError`, each host driver imports cleanly and performs real
       work through its own `run_checked`.

2. WHY EACH IS GUARDED BY OUTCOME RATHER THAN STRUCTURAL ASSERTIONS:
   Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted
   `tests/test_runner_backlog_close.py` and `tests/test_runner_layering.py`. Those deleted
   files asserted delegation structurally by using AST inspection to require each wrapper's
   body to hold exactly one statement naming `runner_shared.<same name>`, and froze a 56-name
   import table.
   Such structural code pins are strictly forbidden by GUIDING_PRINCIPLES P16 (which forbids
   reading production source with `inspect`, `ast`, regex, or substring search), and three
   separate maintainer rulings (carried verbatim in the workflow histories of backlog items
   `pn7rw3`, `s4jctz`, and `aced01`) establish that deleted code-pinning guards will not be
   restored.
   These tests therefore guard both properties strictly by observable behavioral outcome:
   exercising callables with recording fakes to observe call timing, return value forwarding,
   and dependency injection, and running fresh subprocesses to observe import isolation and
   execution side effects.

3. WHAT THIS MODULE DELIBERATELY DOES NOT RESTORE (AND WHAT IT GIVES UP):
   - A behavioral guard CANNOT see a wrapper that grew an extra harmless statement while
     continuing to delegate correctly; it DOES catch every shape in which delegation stops
     being delegation (late resolution failure, swallowed return, peer misinjection), which
     is the defect mode that shipped defect 2kspdy (re-homing with hardcoded host label).
     The replacement is an honest trade, not strictly stronger (plan 1o7i7g F-07).
   - It does NOT restore the 56-name import classification table or AST walkers from
     `tests/test_runner_layering.py`; the oc-to-agy import set is already empty, so the table
     is moot.
   - It does NOT restore the remaining 2,703 deleted lines of behavioral coverage from
     `test_runner_backlog_close.py` (which is tracked under backlog item yf1p8y).
   - For host-independence, driving `run_checked` proves that the executed path is free of
     lazy peer imports, but does not prove every conceivable uncalled lazy path is clean.
"""

from pathlib import Path
import subprocess
import sys
from unittest import mock

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared

BACKLOG_CLOSE_WRAPPERS = [
    "collect_earned_paths",
    "close_backlog_item",
    "commit_backlog_close",
    "process_backlog_close",
]

HOST_TABLE = {
    "oc_runipd": {
        "module": oc_runipd,
        "peer_module": agy_runipd,
        "peer_name": "agy_runipd",
        "expected_host_label": runner_shared.OC_HOST_LABELS.command,
        "peer_host_label": runner_shared.AGY_HOST_LABELS.command,
    },
    "agy_runipd": {
        "module": agy_runipd,
        "peer_module": oc_runipd,
        "peer_name": "oc_runipd",
        "expected_host_label": runner_shared.AGY_HOST_LABELS.command,
        "peer_host_label": runner_shared.OC_HOST_LABELS.command,
    },
}

ELEVEN_REEXPORTS = [
    "evaluate_backlog_close",
    "run_earned_paths",
    "resolve_backlog_item",
    "unclosed_backlog_items",
    "render_unclosed_report",
    "render_runs_pointer",
    "record_unclosed_backlog_items",
    "emit_shutdown_report",
    "register_signal_report",
    "signal_report_callback",
    "_read_from_backlog",
]


def _drive_wrapper(host_mod, wrapper_name: str):
    """Invoke the wrapper on `host_mod` with representative arguments."""
    fn = getattr(host_mod, wrapper_name)
    if wrapper_name == "collect_earned_paths":
        return fn(Path("/fake/repo"), {"id6": "test01"})
    elif wrapper_name == "close_backlog_item":
        return fn(
            Path("/fake/repo"),
            Path("/fake/item.md"),
            "test01",
            "evidence",
            "message",
        )
    elif wrapper_name == "commit_backlog_close":
        return fn(Path("/fake/repo"), "test01", "message")
    elif wrapper_name == "process_backlog_close":
        return fn(Path("/fake/run_dir"), {}, {"id6": "test01"})
    raise ValueError(f"Unknown wrapper: {wrapper_name}")


class TestRunnerBacklogCloseDelegation:
    """Delegation guards proving the four backlog-close wrappers delegate by outcome."""

    @pytest.mark.parametrize(
        "host_name",
        ["oc_runipd", "agy_runipd"],
    )
    @pytest.mark.parametrize(
        "wrapper_name",
        BACKLOG_CLOSE_WRAPPERS,
    )
    def test_delegation_resolves_late_forwards_return_and_injects_correct_host(
        self, host_name: str, wrapper_name: str
    ):
        """Assert (a) late resolution, (b) return forwarding, and (c) correct injection.

        For both hosts and all four wrappers:
        - The fake in `runner_shared` is called exactly once (late resolution).
        - The wrapper returns the fake's sentinel unchanged (return forwarding).
        - The injected `run_checked` is THIS host's and IS NOT the peer host's (correct injection).
        - For `process_backlog_close`: `close_backlog_item`, `commit_backlog_close`, and `host_label`
          are THIS host's and ARE NOT the peer's.
        """
        cfg = HOST_TABLE[host_name]
        host_mod = cfg["module"]
        peer_mod = cfg["peer_module"]
        sentinel = object()

        with mock.patch.object(
            runner_shared, wrapper_name, return_value=sentinel
        ) as fake:
            result = _drive_wrapper(host_mod, wrapper_name)

            # (a) LATE RESOLUTION: fake called exactly once
            assert (
                fake.call_count == 1
            ), f"{host_name}.{wrapper_name} did not call runner_shared.{wrapper_name} (call_count={fake.call_count})"

            # (b) RETURN FORWARDING: wrapper forwards sentinel unchanged
            assert (
                result is sentinel
            ), f"{host_name}.{wrapper_name} swallowed or modified return value: {result!r}"

            # (c) CORRECT INJECTION: run_checked is this host's and not peer's
            kwargs = fake.call_args.kwargs
            injected_rc = kwargs.get("run_checked")
            assert (
                injected_rc is host_mod.run_checked
            ), f"{host_name}.{wrapper_name} did not inject this host's run_checked"
            assert (
                injected_rc is not peer_mod.run_checked
            ), f"{host_name}.{wrapper_name} injected peer host's run_checked!"

            # For process_backlog_close, verify the three additional host-specific injections
            if wrapper_name == "process_backlog_close":
                injected_cbi = kwargs.get("close_backlog_item")
                injected_cbc = kwargs.get("commit_backlog_close")
                injected_hl = kwargs.get("host_label")

                assert (
                    injected_cbi is host_mod.close_backlog_item
                ), f"{host_name}.process_backlog_close did not inject this host's close_backlog_item"
                assert (
                    injected_cbi is not peer_mod.close_backlog_item
                ), f"{host_name}.process_backlog_close injected peer host's close_backlog_item!"

                assert (
                    injected_cbc is host_mod.commit_backlog_close
                ), f"{host_name}.process_backlog_close did not inject this host's commit_backlog_close"
                assert (
                    injected_cbc is not peer_mod.commit_backlog_close
                ), f"{host_name}.process_backlog_close injected peer host's commit_backlog_close!"

                assert (
                    injected_hl == cfg["expected_host_label"]
                ), f"{host_name}.process_backlog_close host_label {injected_hl!r} != {cfg['expected_host_label']!r}"
                assert (
                    injected_hl != cfg["peer_host_label"]
                ), f"{host_name}.process_backlog_close host_label matches peer host_label!"

    @pytest.mark.parametrize("host_name", ["oc_runipd", "agy_runipd"])
    def test_delegation_process_backlog_close_late_bound_closers(self, host_name: str):
        """Assert process_backlog_close resolves close_backlog_item and commit_backlog_close at call time.

        Four in-tree tests patch `<host>.close_backlog_item` to spy on argv received by the gated setter;
        this test proves that a patched closer on the host driver reaches the shared callable at call time.
        """
        cfg = HOST_TABLE[host_name]
        host_mod = cfg["module"]
        spy_closer = object()
        spy_committer = object()

        with mock.patch.object(
            host_mod, "close_backlog_item", spy_closer
        ), mock.patch.object(
            host_mod, "commit_backlog_close", spy_committer
        ), mock.patch.object(runner_shared, "process_backlog_close") as fake:
            _drive_wrapper(host_mod, "process_backlog_close")

            assert fake.call_count == 1
            assert (
                fake.call_args.kwargs.get("close_backlog_item") is spy_closer
            ), f"{host_name}.process_backlog_close did not pass late-patched close_backlog_item"
            assert (
                fake.call_args.kwargs.get("commit_backlog_close") is spy_committer
            ), f"{host_name}.process_backlog_close did not pass late-patched commit_backlog_close"

    @pytest.mark.parametrize("name", ELEVEN_REEXPORTS)
    def test_delegation_reexport_single_implementation_identity(self, name: str):
        """Assert object identity for all eleven direct re-exports across oc, agy, and runner_shared."""
        oc_sym = getattr(oc_runipd, name)
        agy_sym = getattr(agy_runipd, name)
        shared_sym = getattr(runner_shared, name)
        assert oc_sym is agy_sym is shared_sym, (
            f"Re-export {name} is not identical across oc, agy, and runner_shared: "
            f"oc={id(oc_sym)}, agy={id(agy_sym)}, shared={id(shared_sym)}"
        )


class TestRunnerHostIndependence:
    """Host-independence guards proving neither driver depends on its peer."""

    @pytest.mark.parametrize(
        "host_name,peer_name",
        [("oc_runipd", "agy_runipd"), ("agy_runipd", "oc_runipd")],
    )
    def test_host_independence_with_peer_blocked(self, host_name: str, peer_name: str):
        """Prove in a fresh subprocess that host_name works with peer_name blocked.

        In a fresh Python interpreter:
        1. A sys.meta_path finder is installed that raises ImportError if peer_name is imported.
        2. The finder logs every 'agent_workflows.*' module name requested.
        3. host_name is imported and performs real work via host.run_checked.
        4. Verifies host_name returned 'work-ok', peer_name is NOT in sys.modules,
           and the finder was consulted for host_name itself (proving it was live).
        """
        code = f"""
import sys

consulted = []

class PeerBlocker:
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("agent_workflows"):
            consulted.append(fullname)
        if fullname == "agent_workflows.{peer_name}" or fullname.startswith("agent_workflows.{peer_name}."):
            raise ImportError("PEER BLOCKED: " + fullname)
        return None

sys.meta_path.insert(0, PeerBlocker())

import agent_workflows.{host_name} as host

res = host.run_checked([sys.executable, "-c", "print('work-ok')"])
if "work-ok" not in res:
    print(f"ERROR: unexpected run_checked output: {{res!r}}", file=sys.stderr)
    sys.exit(2)

peer_loaded = "agent_workflows.{peer_name}" in sys.modules
if peer_loaded:
    print(f"ERROR: {peer_name} is in sys.modules!", file=sys.stderr)
    sys.exit(3)

if f"agent_workflows.{host_name}" not in consulted:
    print(f"ERROR: {host_name} not in consulted: {{consulted}}", file=sys.stderr)
    sys.exit(4)

print(f"CONSULTED: {{consulted}}")
print(f"OK {host_name} works with {peer_name} blocked; peer_loaded={{peer_loaded}}; host_consulted=True")
"""
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=False,
        )
        print(proc.stdout, end="")

        assert proc.returncode == 0, (
            f"Subprocess for {host_name} failed with exit {proc.returncode}.\n"
            f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
        )
        assert "work-ok" in proc.stdout or "OK " in proc.stdout
        assert "peer_loaded=False" in proc.stdout
        assert "host_consulted=True" in proc.stdout
        assert f"agent_workflows.{host_name}" in proc.stdout
