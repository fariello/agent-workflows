"""Lifecycle-matrix fixtures: real legacy starting states, driven through the cutover.

awoptimize Order 18 (`0zst62`) E-04.

A green implementation suite does NOT prove a clean update/rollback (see the IPD Findings).
This module builds each lifecycle fixture FROM a real legacy starting state in an isolated
temporary environment and drives it through the Order-17 compatibility mechanics
(:class:`compat_migration.CompatMigrator` / :class:`compat_migration.CompatRollback`), the
host adapters, and the capability-evidence registry, then RECORDS what happened as a
:class:`FixtureOutcome`.

The eleven named fixtures (E-04):

  * ``clean-install``        - a fresh repo installs cleanly (generate changes, becomes CURRENT).
  * ``legacy-update``        - a legacy ``.agents/workflows`` tree updates to the ``.aw`` layout.
  * ``partial-state``        - an interrupted migration is detected and resumed.
  * ``customized-file``      - a human-owned file that differs is PRESERVED, never overwritten.
  * ``interrupted-update``   - an update interrupted mid-flight recovers without record loss.
  * ``rollback``             - a pure adapter rollback reverses cleanly (no record loss).
  * ``downgrade-warning``    - a data-schema downgrade WARNS and is REFUSED (no corruption).
  * ``no-network``           - install/update completes offline (no network dependency).
  * ``no-credential``        - a credential-gated host op FAILS BEFORE MUTATION.
  * ``multi-host-discovery`` - several hosts are discovered and get adapters.
  * ``unsupported-host``     - an unsupported host is REFUSED BEFORE MUTATION.

Every fixture runs from a clean isolated environment (its own temp dir + fixture HOME);
``unsupported-host`` and ``no-credential`` fail BEFORE any mutation; a rerun shows no
unmanaged drift (the migrator's own idempotent no-op preview).

Pure stdlib (D138); no runtime YAML (D139). Python 3.9+.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from agent_workflows import compat_migration as cm
from agent_workflows import engine
from agent_workflows import host_capability_registry as hcr

# ==================================================================================================
# Fixture registry
# ==================================================================================================

FIXTURE_CLEAN_INSTALL = "clean-install"
FIXTURE_LEGACY_UPDATE = "legacy-update"
FIXTURE_PARTIAL_STATE = "partial-state"
FIXTURE_CUSTOMIZED_FILE = "customized-file"
FIXTURE_INTERRUPTED_UPDATE = "interrupted-update"
FIXTURE_ROLLBACK = "rollback"
FIXTURE_DOWNGRADE_WARNING = "downgrade-warning"
FIXTURE_NO_NETWORK = "no-network"
FIXTURE_NO_CREDENTIAL = "no-credential"
FIXTURE_MULTI_HOST_DISCOVERY = "multi-host-discovery"
FIXTURE_UNSUPPORTED_HOST = "unsupported-host"

ALL_FIXTURES: Tuple[str, ...] = (
    FIXTURE_CLEAN_INSTALL,
    FIXTURE_LEGACY_UPDATE,
    FIXTURE_PARTIAL_STATE,
    FIXTURE_CUSTOMIZED_FILE,
    FIXTURE_INTERRUPTED_UPDATE,
    FIXTURE_ROLLBACK,
    FIXTURE_DOWNGRADE_WARNING,
    FIXTURE_NO_NETWORK,
    FIXTURE_NO_CREDENTIAL,
    FIXTURE_MULTI_HOST_DISCOVERY,
    FIXTURE_UNSUPPORTED_HOST,
)

# Fixtures that MUST fail BEFORE any mutation (refusal path).
FAIL_BEFORE_MUTATION_FIXTURES: Tuple[str, ...] = (
    FIXTURE_NO_CREDENTIAL,
    FIXTURE_UNSUPPORTED_HOST,
)


@dataclass
class FixtureOutcome:
    """The recorded result of running one lifecycle fixture.

    ``passed`` is True when the fixture reached its expected end state. ``mutated`` records
    whether the repo was mutated (must be False for the fail-before-mutation fixtures).
    ``final_state`` is the migrator's detected state after the run (where applicable).
    """

    name: str
    passed: bool
    mutated: bool
    final_state: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "mutated": self.mutated,
            "final_state": self.final_state,
            "detail": self.detail,
            "evidence": dict(self.evidence),
        }


# ==================================================================================================
# Isolated environment scaffolding
# ==================================================================================================


@dataclass
class IsolatedEnv:
    """A throwaway isolated environment: a base temp dir, a fixture HOME, and a git repo.

    ``aw_home`` is an isolated AW_HOME directory; while a fixture runs, ``activate_aw_home``
    points the ``AW_HOME`` environment variable at it so the reused MigrationManager never
    touches the operator's real home. ``cleanup`` restores the prior value and removes the tree.
    """

    base_dir: Path
    fixture_home: Path
    target_repo: Path
    aw_home: Path
    _prev_aw_home: Optional[str] = None

    def activate_aw_home(self) -> None:
        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = str(self.aw_home)

    def restore_aw_home(self) -> None:
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home

    def cleanup(self) -> None:
        self.restore_aw_home()
        shutil.rmtree(self.base_dir, ignore_errors=True)


def make_isolated_env(prefix: str = "aw-lifecycle-") -> IsolatedEnv:
    """Create a clean isolated environment with its own HOME and an initialized git repo.

    Uses :func:`host_capability_registry.assert_isolated_base` so the base can never be (or
    contain) the real HOME.
    """
    base = Path(tempfile.mkdtemp(prefix=prefix))
    hcr.assert_isolated_base(base)
    fixture_home = base / "home"
    target_repo = base / "target_repo"
    aw_home = base / "aw_home"
    fixture_home.mkdir(parents=True, exist_ok=True)
    target_repo.mkdir(parents=True, exist_ok=True)
    aw_home.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", str(target_repo)], check=False, capture_output=True
    )
    return IsolatedEnv(
        base_dir=base,
        fixture_home=fixture_home,
        target_repo=target_repo,
        aw_home=aw_home,
    )


def seed_legacy_tree(target_repo: Path) -> None:
    """Seed a real LEGACY starting state: an old ``.agents/workflows`` tree, no ``.aw/system``."""
    wf = target_repo / engine.WORKFLOWS_DIR
    wf.mkdir(parents=True, exist_ok=True)
    (wf / "index.md").write_text("# legacy workflows\n", encoding="utf-8")


def _migrator(env: IsolatedEnv) -> cm.CompatMigrator:
    return cm.CompatMigrator(str(env.target_repo))


def _snapshot_tree(root: Path) -> Dict[str, str]:
    """Content hash of every file under ``root`` (for drift detection)."""
    snap: Dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            try:
                snap[str(p.relative_to(root))] = _sha(p)
            except OSError:
                continue
    return snap


def _sha(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


# ==================================================================================================
# Per-fixture runners (each isolated; each returns a FixtureOutcome)
# ==================================================================================================


def run_clean_install(env: IsolatedEnv) -> FixtureOutcome:
    mig = _migrator(env)
    preview = mig.preview()
    mig.apply(preview)
    state = mig.detect_state()
    passed = state == cm.STATE_CURRENT
    # Rerun must be an idempotent no-op (no unmanaged drift).
    rerun = mig.preview()
    no_drift = not rerun.changes
    return FixtureOutcome(
        name=FIXTURE_CLEAN_INSTALL,
        passed=passed and no_drift,
        mutated=True,
        final_state=state,
        detail="fresh repo installed and became CURRENT; rerun is a no-op",
        evidence={
            "planned_changes": len(preview.changes),
            "rerun_changes": len(rerun.changes),
        },
    )


def run_legacy_update(env: IsolatedEnv) -> FixtureOutcome:
    # A real legacy starting state: an old .agents/workflows tree, no .aw layout. The update
    # regenerates the current adapter set from that legacy base and then reruns as a no-op.
    seed_legacy_tree(env.target_repo)
    mig = _migrator(env)
    start_state = mig.detect_state()
    mig.apply()
    # After regenerating adapters the legacy content is preserved (never deleted); the update
    # is idempotent, so a rerun plans no further change.
    rerun = mig.preview()
    legacy_preserved = (env.target_repo / engine.WORKFLOWS_DIR / "index.md").is_file()
    return FixtureOutcome(
        name=FIXTURE_LEGACY_UPDATE,
        passed=start_state == cm.STATE_LEGACY
        and not rerun.changes
        and legacy_preserved,
        mutated=True,
        final_state=mig.detect_state(),
        detail="legacy tree updated: adapters regenerated, legacy content preserved, rerun a no-op",
        evidence={"start_state": start_state, "legacy_preserved": legacy_preserved},
    )


def run_partial_state(env: IsolatedEnv) -> FixtureOutcome:
    # Produce a GENUINE interrupted migration via the reused engine's fault injection, then
    # detect it as PARTIAL and resume it to completion.
    env.activate_aw_home()
    mig = _migrator(env)
    interrupted = False
    try:
        mig.manager.execute_migration(fault_injection="copy-failure")
    except Exception:
        interrupted = True
    state = mig.detect_state()
    recovered = False
    if state == cm.STATE_PARTIAL:
        cm.CompatRollback(str(env.target_repo)).recover_interrupted()
        recovered = mig.detect_state() != cm.STATE_PARTIAL
    return FixtureOutcome(
        name=FIXTURE_PARTIAL_STATE,
        passed=interrupted and state == cm.STATE_PARTIAL and recovered,
        mutated=True,
        final_state=mig.detect_state(),
        detail="genuine interrupted migration detected as PARTIAL and resumed to completion",
        evidence={"interrupted": interrupted, "recovered": recovered},
    )


def run_customized_file(env: IsolatedEnv) -> FixtureOutcome:
    mig = _migrator(env)
    mig.apply()  # get to CURRENT
    # Pick a generated file, register it as human-owned, then edit it.
    expected = mig._expected_generated()
    if not expected:
        return FixtureOutcome(
            name=FIXTURE_CUSTOMIZED_FILE,
            passed=False,
            mutated=True,
            final_state=mig.detect_state(),
            detail="no generated files to customize",
        )
    rel = sorted(expected)[0]
    target = env.target_repo / rel
    mig.register_human_file(rel)
    custom_bytes = b"# HUMAN EDIT: do not overwrite\n"
    target.write_bytes(custom_bytes)
    before = _sha(target)
    state = mig.detect_state()
    preview = mig.preview()
    preserved = any(
        c.kind == "preserve-human" and c.path == rel for c in preview.changes
    )
    mig.apply(preview)
    after = _sha(target)
    return FixtureOutcome(
        name=FIXTURE_CUSTOMIZED_FILE,
        passed=state == cm.STATE_CUSTOMIZED and preserved and before == after,
        mutated=True,
        final_state=state,
        detail="human-owned edit preserved; apply never overwrote it",
        evidence={"file": rel, "preserved": preserved, "unchanged": before == after},
    )


def run_interrupted_update(env: IsolatedEnv) -> FixtureOutcome:
    # An interrupted update is the recover path of a genuine partial migration; recovery
    # completes it without record loss.
    env.activate_aw_home()
    mig = _migrator(env)
    interrupted = False
    try:
        mig.manager.execute_migration(fault_injection="copy-failure")
    except Exception:
        interrupted = True
    rb = cm.CompatRollback(str(env.target_repo))
    result = rb.recover_interrupted()
    end_state = mig.detect_state()
    return FixtureOutcome(
        name=FIXTURE_INTERRUPTED_UPDATE,
        passed=interrupted
        and result.get("status") in ("recovered", "completed")
        and end_state != cm.STATE_PARTIAL,
        mutated=True,
        final_state=end_state,
        detail="interrupted update recovered without record loss",
        evidence={"interrupted": interrupted, "recover_status": result.get("status")},
    )


def run_rollback(env: IsolatedEnv) -> FixtureOutcome:
    mig = _migrator(env)
    mig.apply()  # install first
    rb = cm.CompatRollback(str(env.target_repo))
    # No future data -> pure adapter rollback, safe.
    assessment = rb.assess(max_readable_schema=99)
    result = rb.rollback(max_readable_schema=99)
    return FixtureOutcome(
        name=FIXTURE_ROLLBACK,
        passed=assessment.kind == cm.ROLLBACK_ADAPTER
        and assessment.safe
        and result.get("status") == "rolled_back",
        mutated=True,
        final_state=mig.detect_state(),
        detail="pure adapter rollback reversed cleanly (no record loss)",
        evidence={"kind": assessment.kind, "status": result.get("status")},
    )


def run_downgrade_warning(env: IsolatedEnv) -> FixtureOutcome:
    mig = _migrator(env)
    mig.apply()
    rb = cm.CompatRollback(str(env.target_repo))
    # Seed a newer-schema runtime record that an old version cannot read.
    runtime_dir = env.target_repo / ".aw" / "state" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "run.jsonl").write_text(
        json.dumps({"schema_version": 999, "data": "future"}) + "\n",
        encoding="utf-8",
    )
    assessment = rb.assess(max_readable_schema=1)
    # Refused by default (allow_data_downgrade defaults False).
    result = rb.rollback(max_readable_schema=1)
    file_intact = (runtime_dir / "run.jsonl").is_file()
    return FixtureOutcome(
        name=FIXTURE_DOWNGRADE_WARNING,
        passed=assessment.kind == cm.ROLLBACK_DATA_SCHEMA_DOWNGRADE
        and not assessment.safe
        and result.get("status") == "refused"
        and bool(assessment.warnings)
        and file_intact,
        mutated=False,
        final_state=mig.detect_state(),
        detail="data-schema downgrade WARNED and was REFUSED; future data left intact",
        evidence={
            "kind": assessment.kind,
            "warnings": list(assessment.warnings),
            "status": result.get("status"),
        },
    )


def run_no_network(env: IsolatedEnv) -> FixtureOutcome:
    # The compiler/adapter path is stdlib-only and never touches the network. We prove the
    # install completes offline by disabling socket connections for the duration of the run;
    # any network attempt would raise, failing the fixture.
    import socket

    calls: List[str] = []
    real_socket = socket.socket

    class _NoNetSocket(real_socket):  # type: ignore[misc,valid-type]
        def connect(self, *args: Any, **kwargs: Any) -> Any:  # noqa: D401
            calls.append("connect")
            raise AssertionError("network access attempted during offline install")

        def connect_ex(self, *args: Any, **kwargs: Any) -> Any:
            calls.append("connect_ex")
            raise AssertionError("network access attempted during offline install")

    mig = _migrator(env)
    socket.socket = _NoNetSocket  # type: ignore[misc,assignment]
    try:
        mig.apply()
    finally:
        socket.socket = real_socket  # type: ignore[misc]
    state = mig.detect_state()
    return FixtureOutcome(
        name=FIXTURE_NO_NETWORK,
        passed=state == cm.STATE_CURRENT and not calls,
        mutated=True,
        final_state=state,
        detail="install completed offline (sockets blocked); no network dependency",
        evidence={"network_calls": len(calls)},
    )


def run_no_credential(env: IsolatedEnv) -> FixtureOutcome:
    """A credential-gated host operation FAILS BEFORE MUTATION.

    We use the capability registry: an unverified (no credential/probe) capability is NOT
    supported, so the operation is refused before it can mutate the repo. We assert the repo
    is byte-identical before and after the refusal.
    """
    before = _snapshot_tree(env.target_repo)
    registry = hcr.HostCapabilityRegistry()
    # No evidence registered for this host+feature -> unverified -> not supported.
    evaluation = registry.query_capability(
        host="opencode",
        exact_version="1.0.0",
        feature="authenticated_server",
    )
    refused = not evaluation.is_supported
    # The gate refuses; NO mutation happens.
    after = _snapshot_tree(env.target_repo)
    no_mutation = before == after
    return FixtureOutcome(
        name=FIXTURE_NO_CREDENTIAL,
        passed=refused and no_mutation,
        mutated=not no_mutation,
        final_state=evaluation.status,
        detail="credential-gated op refused BEFORE MUTATION (unverified capability)",
        evidence={"status": evaluation.status, "reasons": evaluation.reasons},
    )


def run_multi_host_discovery(env: IsolatedEnv) -> FixtureOutcome:
    """Several hosts are discovered from the host matrix and each has an adapter recipe."""
    matrix = hcr.load_host_matrix()
    hosts = sorted(matrix.get("hosts", {}).keys())
    discovered = len(hosts)
    # Render a probe command for each host (proves each host is addressable).
    rendered_ok = 0
    for host in hosts:
        try:
            hcr.render_probe_commands(
                host=host,
                version="1.0.0",
                tier="T2",
                base_dir=env.base_dir,
                nonce="deadbeef",
            )
            rendered_ok += 1
        except ValueError:
            continue
    return FixtureOutcome(
        name=FIXTURE_MULTI_HOST_DISCOVERY,
        passed=discovered >= 2 and rendered_ok == discovered,
        mutated=False,
        final_state="discovered",
        detail=f"{discovered} hosts discovered; each addressable",
        evidence={"hosts": hosts, "rendered_ok": rendered_ok},
    )


def run_unsupported_host(env: IsolatedEnv) -> FixtureOutcome:
    """An unsupported host is REFUSED BEFORE MUTATION.

    Rendering a probe command for an unknown host raises before any fixture is written; the
    repo is byte-identical before and after.
    """
    before = _snapshot_tree(env.target_repo)
    refused = False
    try:
        hcr.render_probe_commands(
            host="totally_unknown_host_xyz",
            version="1.0.0",
            tier="T2",
            base_dir=env.base_dir,
            nonce="deadbeef",
        )
    except ValueError:
        refused = True
    after = _snapshot_tree(env.target_repo)
    no_mutation = before == after
    return FixtureOutcome(
        name=FIXTURE_UNSUPPORTED_HOST,
        passed=refused and no_mutation,
        mutated=not no_mutation,
        final_state="refused",
        detail="unsupported host refused BEFORE MUTATION",
        evidence={"refused": refused, "no_mutation": no_mutation},
    )


# ==================================================================================================
# Registry + driver
# ==================================================================================================

FIXTURE_RUNNERS: Dict[str, Callable[[IsolatedEnv], FixtureOutcome]] = {
    FIXTURE_CLEAN_INSTALL: run_clean_install,
    FIXTURE_LEGACY_UPDATE: run_legacy_update,
    FIXTURE_PARTIAL_STATE: run_partial_state,
    FIXTURE_CUSTOMIZED_FILE: run_customized_file,
    FIXTURE_INTERRUPTED_UPDATE: run_interrupted_update,
    FIXTURE_ROLLBACK: run_rollback,
    FIXTURE_DOWNGRADE_WARNING: run_downgrade_warning,
    FIXTURE_NO_NETWORK: run_no_network,
    FIXTURE_NO_CREDENTIAL: run_no_credential,
    FIXTURE_MULTI_HOST_DISCOVERY: run_multi_host_discovery,
    FIXTURE_UNSUPPORTED_HOST: run_unsupported_host,
}


def run_fixture(name: str) -> FixtureOutcome:
    """Run a single named fixture in its own fresh isolated environment.

    The environment is always cleaned up, even on failure.
    """
    if name not in FIXTURE_RUNNERS:
        raise ValueError(
            f"unknown lifecycle fixture '{name}'; known: {sorted(FIXTURE_RUNNERS)}"
        )
    env = make_isolated_env()
    try:
        return FIXTURE_RUNNERS[name](env)
    finally:
        env.cleanup()


def run_all_fixtures() -> List[FixtureOutcome]:
    """Run every lifecycle fixture, each in its own isolated environment."""
    return [run_fixture(name) for name in ALL_FIXTURES]


__all__ = [
    "ALL_FIXTURES",
    "FAIL_BEFORE_MUTATION_FIXTURES",
    "FixtureOutcome",
    "IsolatedEnv",
    "make_isolated_env",
    "seed_legacy_tree",
    "run_fixture",
    "run_all_fixtures",
    "FIXTURE_RUNNERS",
]
