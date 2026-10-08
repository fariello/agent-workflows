"""CLI exit contract conformance gates (IPD 1mnit8).

Enforces load-bearing exit contract invariants across the command surface:
1. Tree-wide usage error floor gate: every declared parser leaf that exits 2 on an
   invalid flag must declare 2 in its exit_contract (E-02).
2. --help floor gate: every declared leaf that exits 0 from --help must declare 0,
   with skip-on-non-zero documenting REMAINDER-forwarding leaves (E-05).
3. Live observed-membership gate: every safe read/check leaf executed live in a real
   subprocess must yield an exit code declared in its exit_contract (E-04).
4. Universal 130 floor and signal code exclusion gate: cli.main returns 130 on
   interruption and no declaration enumerates signal-derived codes (130, 143) (IPD ug85or).
"""

from __future__ import annotations

import contextlib
import io
from unittest import mock
import pytest

from agent_workflows import cli, command_surface
from tests import conformance_matrix


def test_usage_error_floor_gate_tree_wide() -> None:
    """Every declared leaf that exits 2 on usage error must declare 2 in exit_contract.

    Coverage claim (IPD 1mnit8 E-02):
    This gate provides 100% coverage across all declared leaves in the CLI (including
    mutating commands, installers, and check/read commands) without executing mutations.

    In-process shortcut justification:
    Subprocesses in this test environment take roughly 0.369s per invocation, which
    across 162 leaves would total ~60s - approximately two-thirds of the 90s per-test
    hang budget in conftest.py (_DEFAULT_TEST_TIMEOUT = 90.0). On a loaded machine,
    60s leaves minimal headroom and risks spurious hang timeouts. By contrast, the
    in-process parse_args invocation takes 0.044s total for all 162 leaves (over 1300x
    faster). The in-process shortcut is faithful for this specific path because
    argparse.ArgumentParser.error raises SystemExit(2) before any command handler
    runs, verified by an empirical 30-leaf sample where in-process SystemExit.code
    and real subprocess returncode agreed 30 of 30.

    Derivation invariant:
    The observed exit code is derived dynamically from SystemExit.code, never
    hardcoded. If a future leaf legitimately does not exit 2 on an unrecognized flag
    (e.g., REMAINDER forwarder with add_help=False), it is not falsely forced to declare 2.
    """
    parser = cli._build_parser()
    leaves = sorted(command_surface.get_declared_leaves())
    violations = []

    for leaf in leaves:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                parser.parse_args([*leaf.split(), "--this-flag-does-not-exist"])
                observed_code = None
            except SystemExit as exc:
                observed_code = exc.code

        if observed_code == 2:
            decl = command_surface.get_declaration(leaf)
            assert (
                decl is not None
            ), f"Declared leaf {leaf!r} missing from declaration index"
            if 2 not in decl.exit_contract:
                violations.append((leaf, decl.exit_contract, observed_code))

    assert not violations, (
        f"Found {len(violations)} declared leaves where observed usage-error exit code is 2 "
        f"but 2 is not in exit_contract:\n"
        + "\n".join(
            f"  leaf={leaf!r}, declared exit_contract={contract}, observed={obs}"
            for leaf, contract, obs in violations
        )
    )


def test_help_floor_gate() -> None:
    """Every declared leaf that exits 0 from --help must declare 0 in exit_contract.

    Documented divergence and skip condition (IPD 1mnit8 E-05):
    149 of 161 declared leaves exit 0 from an in-process parse_args(["--help"]).
    Exactly 12 leaves exit 2 from the in-process parse:
      - 'agy exec'
      - 'agy integrate'
      - 'agy review'
      - 'agy runipd'
      - 'agy sessions'
      - 'agy view'
      - 'oc integrate'
      - 'oc review'
      - 'oc runipd'
      - 'pwatch'
      - 'run as'
      - 'run ipd'
    These leaves forward argv verbatim with add_help=False and argparse.REMAINDER to
    subordinate runner parsers. In a real subprocess, all 12 actually exit 0. Because of this
    architectural asymmetry, this gate SKIPS any leaf whose observed in-process code is
    non-zero, rather than asserting over all leaves.

    Standing warning on in-process shortcut:
    The in-process shortcut that test_usage_error_floor_gate_tree_wide relies on is
    justified PER PATH. While faithful for usage errors, it diverges on --help for
    REMAINDER forwarders, and must never be assumed for a new CLI path without
    empirical re-measurement.
    """
    parser = cli._build_parser()
    leaves = sorted(command_surface.get_declared_leaves())
    violations = []

    for leaf in leaves:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            try:
                parser.parse_args([*leaf.split(), "--help"])
                observed_code = None
            except SystemExit as exc:
                observed_code = exc.code

        # Skip leaves whose in-process parse does not exit 0 (the 12 divergent REMAINDER forwarders).
        if observed_code != 0:
            continue

        decl = command_surface.get_declaration(leaf)
        assert (
            decl is not None
        ), f"Declared leaf {leaf!r} missing from declaration index"
        if 0 not in decl.exit_contract:
            violations.append((leaf, decl.exit_contract, observed_code))

    assert not violations, (
        f"Found {len(violations)} declared leaves where observed --help exit code is 0 "
        f"but 0 is not in exit_contract:\n"
        + "\n".join(
            f"  leaf={leaf!r}, declared exit_contract={contract}, observed={obs}"
            for leaf, contract, obs in violations
        )
    )


@pytest.mark.slow
@pytest.mark.timeout(500)
def test_live_safe_leaves_exit_contract_membership() -> None:
    """Every live-executed safe leaf must produce an exit code declared in exit_contract.

    Coverage boundary (IPD 1mnit8 E-04):
    This gate covers 16 of 163 declarations (the curated LIVE_SAFE_LEAVES population in
    tests/conformance_matrix.py). It drives the real CLI in a subprocess across both the
    human and --agent surfaces (32 invocations total). Mutations, installers, and disk-writing
    verbs are excluded from live execution for safety and remain covered by declaration
    and the tree-wide usage error floor gate (test_usage_error_floor_gate_tree_wide).

    Justification and regression prevention (backlog cn5np0):
    This gate is green at introduction (0 violations across all 32 invocations). Its value
    is durable regression prevention: the silent drift that motivated backlog item cn5np0
    ('aw ipd board' declaring (0, 2) while reachably returning 3) was exactly this shape
    and would have been caught by this gate.

    Timing decisions recorded (IPD 1mnit8 F-14):
    1. Hang budget: The 32 invocations take 185.650s serially at execution base (dominated
       by 'doctor' at 53.345s human and 92.121s agent). Because conftest.py's 90s hang budget
       ignores @pytest.mark.slow, an explicit @pytest.mark.timeout(500) is set, providing
       >2.5x headroom over the measured serial total.
    2. Slow marker: Marked @pytest.mark.slow because the 185.650s serial runtime far exceeds
       one-third of 90s (~30s). In CI (.github/workflows/tests.yml), -m slow runs as an
       advisory continue-on-error step, trading enforcement for suite execution speed.
    """
    safe_leaves = sorted(conformance_matrix.LIVE_SAFE_LEAVES.keys())
    assert len(safe_leaves) == 16, f"Expected 16 safe leaves, got {len(safe_leaves)}"
    violations = []

    for leaf in safe_leaves:
        extra = conformance_matrix.LIVE_SAFE_LEAVES[leaf]
        decl = command_surface.get_declaration(leaf)
        assert (
            decl is not None
        ), f"Declared leaf {leaf!r} missing from declaration index"

        # 1. Human surface
        argv_human = [*leaf.split(), *extra]
        res_human = conformance_matrix.run_cli(argv_human)
        if res_human.returncode not in decl.exit_contract:
            violations.append((leaf, "human", res_human.returncode, decl.exit_contract))

        # 2. Agent surface
        argv_agent = [*leaf.split(), *extra, "--agent"]
        res_agent = conformance_matrix.run_cli(argv_agent)
        if res_agent.returncode not in decl.exit_contract:
            violations.append((leaf, "agent", res_agent.returncode, decl.exit_contract))

    assert not violations, (
        f"Found {len(violations)} live membership violations:\n"
        + "\n".join(
            f"  leaf={leaf!r}, surface={surface}, observed_rc={rc}, declared={contract}"
            for leaf, surface, rc, contract in violations
        )
    )


def test_universal_130_floor_and_signal_code_exclusion() -> None:
    """Universal 130 floor and tree-wide signal code exclusion gate (IPD ug85or).

    Enforces two load-bearing exit contract invariants:
    1. THE UNIVERSAL 130 FLOOR IS REAL: cli.main returns 130 when execution is
       interrupted by KeyboardInterrupt or EOFError.
    2. TREE-WIDE SIGNAL CODE EXCLUSION: no declaration in
       command_surface.get_all_declarations() enumerates signal-derived codes
       (130 or 143) in its exit_contract.

    In-process shortcut justification and signal measurement:
    Real signal probes (SIGINT via os.killpg to doctor, check, and next subprocesses)
    empirically return 130 (measured out-of-band in IPD ug85or E-01). Real signal
    probes are omitted from this suite because process-group signaling is slow (requiring
    sleep periods to reach work) and flaky under pytest-xdist parallel execution.
    The in-process cli.main invocation exercises the exact except KeyboardInterrupt
    and except EOFError arms reached by SIGINT/EOF, providing deterministic, fast
    verification without sleep overhead. Testing multiple argvs in-process does not
    prove verb-independence (since the patched cli._dispatch ignores argv); the
    multi-verb proof is the out-of-band subprocess signal measurement.

    Exclusion rationale:
    Exit contracts declare codes produced by a command's own return path and deliberately
    exclude signal-derived codes (DECISIONS.md D162, command_surface.CommandDeclaration.exit_contract).
    Adding 130 to declarations would duplicate the universal floor across all leaves,
    143 is not a returned code on ordinary verbs (WIFSIGNALED / shell 128+15), and verbs
    like pwatch return 0 on signals.
    """
    # 1. Universal 130 floor assertion
    with mock.patch.object(cli, "_dispatch", side_effect=KeyboardInterrupt):
        rc_ki = cli.main(["status"])
        assert (
            rc_ki == 130
        ), f"Expected cli.main to return 130 on KeyboardInterrupt, got {rc_ki}"

    with mock.patch.object(cli, "_dispatch", side_effect=EOFError):
        rc_eof = cli.main(["status"])
        assert (
            rc_eof == 130
        ), f"Expected cli.main to return 130 on EOFError, got {rc_eof}"

    # 2. Tree-wide signal code exclusion assertion
    violations = []
    for decl in command_surface.get_all_declarations():
        forbidden = set(decl.exit_contract) & {130, 143}
        if forbidden:
            violations.append((decl.command, decl.exit_contract, sorted(forbidden)))

    assert not violations, (
        f"Found {len(violations)} declarations containing signal-derived exit codes (130/143) "
        f"in exit_contract, violating the contract decided in DECISIONS.md D162 and "
        f"documented in command_surface.CommandDeclaration.exit_contract. "
        f"Do NOT widen exit_contract to include signal-derived codes; document unusual signal "
        f"behavior at the verb instead:\n"
        + "\n".join(
            f"  command={cmd!r}, declared exit_contract={contract}, forbidden_codes={forb}"
            for cmd, contract, forb in violations
        )
    )
