"""Shared helpers for the framework self-tests (stdlib only)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import unittest.mock
from pathlib import Path

# Repo root = the directory containing install-workflows.py (two up from this file's dir).
REPO_ROOT = Path(__file__).resolve().parent.parent
# Static, checked-in test fixtures (decoupled from the mutable live plans board).
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CONFORMING_ORCHESTRATOR = FIXTURES / "conforming-orchestrator.md"
INSTALLER = REPO_ROOT / "install-workflows.py"


def _source_workflows_root() -> Path:
    """The framework's OWN source workflow bundle, layout-aware.

    Canonical nested `.aw/system/workflows/` after the physical-layout migration; falls back
    to the legacy `.agents/workflows/` for a pre-migration checkout. Keeping this dual-aware
    lets the self-tests run before AND after the source repo is migrated.
    """

    aw = REPO_ROOT / ".aw" / "system" / "workflows"
    return aw if aw.is_dir() else REPO_ROOT / ".agents" / "workflows"


SOURCE_WORKFLOWS = _source_workflows_root()


def _source_plans_root() -> Path:
    """The framework's OWN source plans tree, layout-aware: `.aw/records/plans/` after the
    migration, else legacy `.agents/plans/`."""

    aw = REPO_ROOT / ".aw" / "records" / "plans"
    return aw if aw.is_dir() else REPO_ROOT / ".agents" / "plans"


SOURCE_PLANS = _source_plans_root()


def _source_docs_root() -> Path:
    """The framework's OWN source doc-types base, layout-aware. Consumers use ``SOURCE_DOCS/<type>``
    (e.g. ``/specs``). Order 07 (spec 20260817-2124-01) FLATTENED the doc types out of ``docs/``:
    they now sit directly under ``.aw/records/`` (so the base is the records root). Falls back to the
    intermediate ``.aw/records/docs/`` and then legacy ``.agents/docs/`` for older/pre-migration trees."""

    flat = REPO_ROOT / ".aw" / "records"
    if (flat / "specs").is_dir():
        return flat
    nested = REPO_ROOT / ".aw" / "records" / "docs"
    if nested.is_dir():
        return nested
    return REPO_ROOT / ".agents" / "docs"


SOURCE_DOCS = _source_docs_root()
SCANNER = SOURCE_WORKFLOWS / "assess" / "tools" / "scan_secrets.py"
RUN_CHECKS = SOURCE_WORKFLOWS / "verify" / "tools" / "run_checks.py"
BENCH_ENV = SOURCE_WORKFLOWS / "benchmark" / "tools" / "bench_env.py"
SETUP_TOOLS = SOURCE_WORKFLOWS / "setup-repo" / "tools" / "setup_tools.py"
CONFORMANCE_HARNESS = (
    SOURCE_WORKFLOWS / "conformance" / "tools" / "conformance_harness.py"
)


# --------------------------------------------------------------------------------------
# Declare the execution ROLE a test exercises, instead of inheriting it (plan `e4lkv5`).
# --------------------------------------------------------------------------------------

EXECUTION_ROLE_ENV = "AW_EXECUTION_ROLE"
ROLE_WORKER = "worker"


def execution_role(role: str | None):
    """Return a context manager that DECLARES the execution role for the current process.

    Pass ``role=None`` to assert the COORDINATOR role (the marker absent, which is what
    ``aw ipd begin``/``finalize`` require), or ``role="worker"`` to assert the managed-lane
    role that `AW-LIFECYCLE-ROLE-001` refuses. Either way the value is SET by the test
    rather than read from whatever launched pytest.

    WHY A TEST MUST DECLARE ITS ROLE, and why INHERITING is a defect in BOTH directions.
    The runners export ``AW_EXECUTION_ROLE=worker`` into an isolated execute turn
    (``oc_runipd.py``, ``agy_runipd.py``), and `ipd_lifecycle.run_begin`/`run_finalize`
    read the AMBIENT process environment (``worker_role_active(os.environ)``). So a test
    that drives those wrappers without declaring a role gets whichever role happened to
    launch the suite: it FAILS with the lifecycle refusal when a runner launched it, and
    PASSES in a human's shell, which makes it evidence about the environment rather than
    about the code. The mirror case is worse and is silent: a test ASSERTING the refusal
    while inheriting the marking passes VACUOUSLY, so a safety guard stops testing
    anything without any run going red to say so.

    Use this instead of a pytest fixture. Every affected test here is a
    ``unittest.TestCase`` method, into which pytest does NOT inject fixtures, so
    ``monkeypatch`` silently arrives as ``None``.

    Two shipped precedents this generalizes, and the shape to keep extending:

    * ``tests/test_orchestrator_retirement.py`` passes ``env={}`` EXPLICITLY into the
      lifecycle call, with the comment that "the suite itself may run inside a managed
      lane ... and a test that silently read os.environ would then refuse for the wrong
      reason and pass vacuously". Prefer that when the code under test accepts an ``env``
      mapping: an explicit argument beats any process-wide mutation.
    * ``tests/test_worker_role_refusal.py``'s ``_run_cli(role=...)`` normalizes the role on
      the env dict it hands to each subprocess. Prefer that when spawning a subprocess
      directly.

    This helper is for the remaining case, where the code under test reads the ambient
    environment itself (an in-process driver helper, or a CLI wrapper reached in-process)
    and takes no ``env`` parameter to thread a value through.

    Usage from a ``unittest.TestCase``::

        def setUp(self):
            self.enterContext(support.execution_role(None))  # coordinator

    On Python 3.10 or earlier, ``addCleanup`` the ``__exit__`` instead of ``enterContext``.
    """

    if role is None:
        return _PoppedEnv(EXECUTION_ROLE_ENV)
    return unittest.mock.patch.dict(os.environ, {EXECUTION_ROLE_ENV: role})


class _PoppedEnv:
    """Context manager that REMOVES one env var for its duration and restores it after.

    ``mock.patch.dict`` can only SET keys, and the coordinator role is expressed by the
    marker being ABSENT, so removal needs its own tiny manager. Restoring the prior value
    matters because the suite runs with ``-n auto``: a test that leaked a role change into
    its worker process would decide the role for every test that follows it there.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._had = False
        self._prior: str | None = None

    def __enter__(self) -> None:
        self._had = self._name in os.environ
        self._prior = os.environ.get(self._name)
        os.environ.pop(self._name, None)
        return None

    def __exit__(self, *exc) -> bool:
        if self._had:
            os.environ[self._name] = self._prior or ""
        else:
            os.environ.pop(self._name, None)
        return False


def declare_execution_role(case, role: str | None = None):
    """Declare the execution role for one ``unittest.TestCase``, undone on teardown.

    The single line a test class needs, callable from ``setUp``::

        def setUp(self):
            support.declare_execution_role(self)          # coordinator (marker absent)
            support.declare_execution_role(self, "worker")  # managed-lane worker

    Entered immediately and unwound through ``addCleanup``, which works on every supported
    interpreter (``requires-python >= 3.9``); ``TestCase.enterContext`` is 3.11+ and so is
    deliberately not used. The unwind is what keeps the declaration from leaking into the
    next test in the same ``-n auto`` worker process.

    See :func:`execution_role` for why declaring the role beats inheriting it.
    """

    manager = execution_role(role)
    manager.__enter__()
    case.addCleanup(manager.__exit__, None, None, None)
    return manager


def coordinator_role():
    """Declare the COORDINATOR role: the marker absent, so lifecycle verbs are permitted.

    Thin alias for ``execution_role(None)``, for call sites where naming the role reads
    better than passing ``None``. See :func:`execution_role` for why declaring beats
    inheriting.
    """

    return execution_role(None)


def worker_role():
    """Declare the managed-lane WORKER role, which `AW-LIFECYCLE-ROLE-001` refuses.

    Use this in a test that ASSERTS the refusal, so it asserts against a role it SET. A
    refusal test that relies on the ambient value passes vacuously whenever the ambient
    value is not ``worker``. See :func:`execution_role`.
    """

    return execution_role(ROLE_WORKER)


def load_module(name: str, path: Path):
    """Import a Python file as a named module, registered in sys.modules.

    Registration is required so that decorators like @dataclass in the imported module
    can resolve `cls.__module__` (Python 3.12+/3.14 look the module up in sys.modules).
    """

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a git command in cwd, returning the completed process."""

    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )


def init_repo(path: Path) -> Path:
    """Initialize a minimal git repo at path with a deterministic identity."""

    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test")
    git(path, "config", "commit.gpgsign", "false")
    return path


def run_installer(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    """Run the installer against a target repo, from the repo's own source tree."""

    return subprocess.run(
        [sys.executable, str(INSTALLER), "--repo", str(repo), *extra],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )


def run_tool(
    tool: Path, *args: str, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    """Run one of the framework's Python tools with args."""

    return subprocess.run(
        [sys.executable, str(tool), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )


def run_cli(
    *args: str | list[str] | tuple[str, ...],
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run the ``agent_workflows`` CLI in a subprocess pinned to THIS tree via ``PYTHONPATH``.

    Ensures that subprocess CLI invocations resolve ``agent_workflows`` from the repository
    containing this test suite (``REPO_ROOT``) rather than an editable install pin in
    site-packages or the parent checkout (IPD `lhjsu0`, bug `ccbe60`).
    """

    merged_env = dict(os.environ) if env is None else dict(env)
    existing_pp = merged_env.get("PYTHONPATH", "")
    root_str = str(REPO_ROOT)
    if root_str not in existing_pp.split(os.pathsep):
        merged_env["PYTHONPATH"] = f"{root_str}{os.pathsep}{existing_pp}".rstrip(
            os.pathsep
        )
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("check", False)

    cli_args: list[str] = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            cli_args.extend(str(a) for a in arg)
        else:
            cli_args.append(str(arg))

    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *cli_args],
        cwd=str(cwd) if cwd is not None else None,
        env=merged_env,
        **kwargs,
    )


# ==================================================================================================
# THE ONE PLAN FIXTURE BUILDER
# ==================================================================================================
#
# WHY THIS EXISTS, measured rather than asserted. Twenty-one test files each carried their OWN private
# copy of "write a throwaway plan", and they were near-identical: most called
# `ipd_authoring.build_skeleton` and then line-patched `- Status:`, `- Scope-Paths:` and
# `- Item-Dependencies:` in the same way. When `planprio` (`lkexaw`) made `Priority` and `Work-Kind`
# REQUIRED at the ready-to-execute gate, all twenty-one broke at once: 175 failed, 8686 passed. One
# rule change, twenty-one files to repair, because the shape was duplicated twenty-one times.
#
# THE SCAFFOLD IS NOT THE PROBLEM AND MUST NOT BE "FIXED". `build_skeleton` correctly emits
# `- Priority: unresolved` / `- Work-Kind: unresolved`: a DRAFT has not decided them yet, and the
# sentinel is what makes the gate refuse an unfinished plan. A fixture that wants to be
# EXECUTION-READY is the thing that must resolve them, exactly as a human author would.
#
# WHY REAL VALUES AND NOT THE `grandfathered` SENTINEL (maintainer decision, 2026-09-24). Both satisfy
# the gate, but `grandfathered` is advisory-satisfied rather than silent, so every fixture would carry a
# permanent "a re-reviewed or new plan should declare a real priority" nudge that nobody will ever
# action; and the sentinel ASSERTS the plan predates the rule, which is false for a plan created
# milliseconds ago in a temp directory. `grandfathered` stays reserved for the legacy corpus it was
# designed for, and for the handful of tests that assert grandfathering itself.
READY_PLAN_PRIORITY = "medium"
READY_PLAN_WORK_KIND = "chore"


def ready_plan_text(
    *,
    plan_id: str = "abc123",
    kind: str = "child",
    title: str = "demo",
    author: str = "tester",
    when: str = "2026-08-24",
    set_name: str = "demo",
    order: int = 1,
    status: str = "approved",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
    item_dependencies: str = "none",
    priority: str | None = None,
    work_kind: str | None = None,
    approval: str | None = "2026-08-24, human: approved",
) -> str:
    """A plan that lints CONFORMING at the `pre-execution` checkpoint.

    BUILT FROM THE REAL GENERATOR (`ipd_authoring.build_skeleton`) rather than from a hand-written
    string, so a change to the authored skeleton reaches every fixture instead of drifting away from
    twenty-one hand-maintained copies. Then it resolves exactly the fields a DRAFT leaves open and an
    execution-ready plan must decide:

      * `Status:`             -> `approved` (overridable), because the gate fires for a plan whose
                                persisted status is in `READY_TO_EXECUTE` regardless of checkpoint.
      * `Scope-Paths:`        -> real paths, since the scaffold emits a `TODO` placeholder.
      * `Item-Dependencies:`  -> `none`, since the scaffold emits `unresolved`, which is correctly
                                blocked at `pre-execution`.
      * `Priority:`/`Work-Kind:` -> real vocabulary values, since the scaffold emits `unresolved`.
      * `Approval:`           -> added BESIDE `Status:` when the status is at the gate, because
                                `IPD-M104` requires an approval attestation whenever `Status` is
                                `approved` and the scaffold (a draft) carries none. Pass
                                `approval=None` to omit it and test that refusal.

    `priority` and `work_kind` are OVERRIDABLE so a test asserting the gate's own behavior can pass
    `"unresolved"`, `"grandfathered"`, or a bogus value and get the refusal it is testing. Passing
    `None` (the default) means "resolve it to a real value", which is what a conforming fixture wants.
    """

    from agent_workflows import ipd_authoring as _authoring

    text = _authoring.build_skeleton(
        kind=kind,
        title=title,
        author=author,
        when=when,
        set_name=set_name,
        order=order,
        plan_id=plan_id,
    )
    status_block = f"- Status: {status}"
    if approval is not None and status in ("approved", "auto-approved"):
        status_block += f"\n- Approval: {approval}"
    replacements = {
        "- Status:": status_block,
        "- Scope-Paths:": f"- Scope-Paths: {scope_paths}",
        "- Item-Dependencies:": f"- Item-Dependencies: {item_dependencies}",
        "- Priority:": f"- Priority: {priority or READY_PLAN_PRIORITY}",
        "- Work-Kind:": f"- Work-Kind: {work_kind or READY_PLAN_WORK_KIND}",
    }
    out: list[str] = []
    in_meta = True
    for line in text.splitlines():
        # THE METADATA REGION ONLY. A `## ` heading ends it, and every later line is body prose that
        # may legitimately quote a bullet (a plan discussing `- Status:` is normal), so rewriting
        # outside the region would corrupt the very prose some tests assert on.
        if line.startswith("## "):
            in_meta = False
        if in_meta:
            for prefix, replacement in replacements.items():
                if line.startswith(prefix):
                    out.append(replacement)
                    break
            else:
                out.append(line)
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def make_fake_executable(path: Path, source: str) -> Path:
    """Write ``source`` (a Python program) as a DIRECTLY EXECUTABLE file and return what to invoke.

    POSIX: a ``#!<this interpreter>`` script at ``path``, chmod 0755, returned as-is.

    WINDOWS: ``CreateProcess`` ignores shebang lines (it only runs ``.exe``/``.com``, and hands
    ``.bat``/``.cmd`` to ``cmd.exe``, which mangles multi-line arguments such as a prompt), so a
    ``#!`` script fails with ``WinError 193``. Instead build a real ``<path>.exe`` the same way pip
    builds console scripts (``opencode.exe`` included): distlib's launcher stub, then a ``#!`` line
    naming this interpreter, then a zip whose ``__main__.py`` is ``source``. The launcher passes argv
    through untouched, so the product's own argv handling is exercised exactly as on POSIX.
    """

    path = Path(path)
    body = source.lstrip()
    if body.startswith("#!"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    if os.name != "nt":
        path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        path.chmod(0o755)
        return path

    return _write_windows_launcher(path, body)


def _write_windows_launcher(path: Path, body: str) -> Path:
    """The Windows half of :func:`make_fake_executable`; callable on any OS so it can be unit-checked."""

    import io
    import struct
    import zipfile

    from pip._vendor import distlib

    bits = 64 if struct.calcsize("P") == 8 else 32
    launcher = (Path(distlib.__file__).parent / f"t{bits}.exe").read_bytes()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("__main__.py", body)
    exe = path.with_suffix(".exe") if path.suffix.lower() != ".exe" else path
    shebang = f"#!{sys.executable}\r\n".encode("utf-8")
    exe.write_bytes(launcher + shebang + buf.getvalue())
    return exe
