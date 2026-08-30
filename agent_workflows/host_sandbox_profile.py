"""Optional OS-sandbox HARD-ENFORCEMENT execution profile (wtiso Phase 6, `1o4eif`).

Implements x03wgn Section 8 "Phase 6" with Sections 1 ("Two enforcement profiles"),
4 ("Container or OS sandbox") and 6 Layer 4 (host capability contract + read-only
discovery then write execution).

PUBLISHED GUARANTEES (x03wgn Section 8 Phase 6.3 "publish its guarantees")
==========================================================================

WHAT THIS PREVENTS. In the `hardened` profile the OPERATING SYSTEM - not a prompt, not a
git hook, not a Python role check - denies a worker process any write outside its own lane:

  * the CONTROL ROOT (run state, receipts, journals, ledgers) is inaccessible;
  * the MAIN WORKTREE is inaccessible;
  * every SIBLING LANE root is inaccessible;
  * the INTEGRATION CANDIDATE tree is inaccessible;
  * CREDENTIALS not needed by the task are inaccessible;
  * the GIT COMMON DIRECTORY is READ-ONLY.

The git-common-dir rule closes a subtlety specific to linked worktrees (x03wgn Section 4):
a linked worktree's `.git` is a FILE pointing into the shared common directory, so a
worker with common-dir write access can mutate shared refs, `config`, and `hooks` - and
thereby attack every other worktree - WITHOUT ever touching a main working file. Hardened
mode therefore keeps that directory read-only and THE DRIVER PERFORMS ALL GIT MUTATION
(`git add`, commits, refs, hooks) after the worker exits. The worker edits files; it never
writes git metadata. Read-only is deliberate rather than inaccessible so the worker's own
`git status`/`git diff`/`git log` keep working.

WHAT THIS DOES NOT DO. It does not make the DEFAULT profile a security boundary. The
default profile (wtiso-01..05) makes a FORGETFUL agent safe by removing voluntary tool use
from the correctness path; it is explicitly NOT a boundary against a MALICIOUS same-user
worker (x03wgn Section 1: "A same-user process with arbitrary shell access cannot be
cryptographically or filesystem-enforced from prompts, hooks, environment variables, or
Python role checks alone."). This module is the OPT-IN complement for when "the driver is
the only writer" must be literal. Hardened mode is NOT the default (Phase 6.4). Network
scoping and container isolation are out of scope here.

PLATFORM AND PROBE THE GUARANTEE WAS VERIFIED ON. Linux ONLY. The mechanism is a ladder,
and every rung is decided by an EXECUTED probe, never by inspection:

  1. `landlock`  - the Landlock LSM (kernel >= 5.13, ABI >= 1), unprivileged, rules
                   inherited by every descendant process. VERIFIED on Linux
                   6.8.0-137-generic, Landlock ABI 4.
  2. `bwrap`     - `bubblewrap` with `--unshare-user` and the plan's bind set.
  3. `userns`    - NOT A PROVEN RUNG. A bare `unshare -Umr` restricts no path, so it cannot
                   enforce the partition above; its probe always reports False and
                   `enter_sandbox` REFUSES it rather than returning a launcher that would
                   enforce nothing. It stays listed only so its report says why.

EVERY RUNG MUST PROVE A DENIAL, NOT A LAUNCH. A probe passes only if a real jail was built
AND the kernel actually REFUSED a write outside the allowed root while permitting one
inside it. "The launcher exited 0" is deliberately insufficient: a misconfigured jail (say
`--bind / /` instead of `--ro-bind / /`) starts perfectly cleanly and enforces nothing, so a
launch-only criterion cannot tell an enforcing jail from a permissive one.

THE GUARANTEE IS VOID ON ANY HOST WHERE THE EXECUTED PROBE RETURNS False. There is no
partial credit and no silent degradation: `supports_os_sandbox` is True only when a real
jail was actually constructed and a real write outside the allowed root was actually
refused by the kernel. On every non-Linux platform, and on any Linux host where all rungs
fail, `supports_os_sandbox` is False and requesting `hardened` raises
`HardModeUnavailableError` (x03wgn Section 8 Phase 6.3: "fail rather than silently
degrading when hard mode is requested but unavailable").

WHY THE PROBE EXECUTES INSTEAD OF INSPECTING. Inspection MEASURABLY LIES. On the host
where this module was developed, `/proc/sys/kernel/unprivileged_userns_clone` was `1`,
`/proc/sys/user/max_user_namespaces` was `514277`, and BOTH `/usr/bin/unshare` and
`/usr/bin/bwrap` were installed - every signal said "sandbox available" - yet
`unshare -Umr true` failed with `Operation not permitted` writing `/proc/self/uid_map`
and `bwrap` failed with `setting up uid map: Permission denied`, because the host was
itself inside a namespace whose `uid_map` was `0 0 4294967295`. A sysctl/binary-presence
probe would have reported `supports_os_sandbox=True` on a host that CANNOT enforce the
sandbox, granting hard mode and failing OPEN. Therefore `_probe_linux_sandbox()` builds an
actual jail in a subprocess and treats ANY nonzero exit, exception, or timeout as False,
and the SAME probe backs both the capability report and the tests' skip decision so the
two can never disagree.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "HostSandboxCapabilities",
    "SandboxPlan",
    "SandboxProfileError",
    "HardModeUnavailableError",
    "detect_host_capabilities",
    "build_sandbox_plan",
    "enter_sandbox",
    "select_execution_profile",
    "run_discovery_then_execution",
    "landlock_bootstrap_source",
]

# The single platform this phase certifies (x03wgn Section 8 Phase 6.3: start on ONE).
CERTIFIED_PLATFORM = "linux"

# Probe timeout. A jail attempt either works immediately or is not available.
_PROBE_TIMEOUT_SECONDS = 20


class SandboxProfileError(ValueError):
    """A sandbox plan is internally inconsistent (e.g. the git common dir is writable)."""


class HardModeUnavailableError(RuntimeError):
    """`hardened` was requested on a host whose EXECUTED probe says it cannot enforce it.

    Raised instead of returning `"default"`, so hard mode FAILS CLOSED rather than silently
    degrading to an unsandboxed launch (x03wgn Section 8 Phase 6.3).
    """


# ---------------------------------------------------------------------------
# E-01: the host capability contract
# ---------------------------------------------------------------------------


@dataclass
class HostSandboxCapabilities:
    """The x03wgn Section 6 Layer 4 host capability contract.

    Every capability defaults to False: an UNPROBED host claims NOTHING (fail-closed). A
    field may only be set True by code that actually executed a probe for it.
    """

    supports_inline_permissions: bool = False
    supports_read_only_phase: bool = False
    supports_session_resume: bool = False
    emits_structured_tool_events: bool = False
    emits_child_permission_events: bool = False
    supports_process_tree_kill: bool = False
    supports_os_sandbox: bool = False

    platform: str = ""
    # Which rung of the ladder was PROVEN by an executed probe: "landlock" | "bwrap" |
    # "userns" | None. Named so the published guarantee can say what was verified.
    sandbox_mechanism: Optional[str] = None
    # Human-readable record of what each probe actually did, for durable snapshotting.
    probe_notes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """A JSON-safe snapshot for the run/lane manifest."""
        return asdict(self)


# ---------------------------------------------------------------------------
# E-02: executed (never inspected) capability probes
# ---------------------------------------------------------------------------

# Landlock access bits (uapi/linux/landlock.h). ABI 1 defines bits 0..12; ABI 2 adds
# REFER (13); ABI 3 adds TRUNCATE (14).
_LL_EXECUTE = 1 << 0
_LL_WRITE_FILE = 1 << 1
_LL_READ_FILE = 1 << 2
_LL_READ_DIR = 1 << 3
_LL_TRUNCATE = 1 << 14

# Rights that are meaningful on a REGULAR FILE. Landlock rejects (EINVAL) a rule that
# carries directory-only rights on a non-directory, so file rules must be masked.
_LL_FILE_MASK = _LL_EXECUTE | _LL_WRITE_FILE | _LL_READ_FILE | _LL_TRUNCATE

_LL_READONLY = _LL_EXECUTE | _LL_READ_FILE | _LL_READ_DIR


def _landlock_all_rights(abi: int) -> int:
    """Every right defined by the running kernel's Landlock ABI.

    The ruleset's `handled_access_fs` must not name a bit the kernel does not know, so the
    mask is derived from the ABI the kernel actually reported.
    """
    if abi >= 3:
        return (1 << 15) - 1  # bits 0..14
    if abi == 2:
        return (1 << 14) - 1  # bits 0..13
    return (1 << 13) - 1  # ABI 1: bits 0..12


def landlock_bootstrap_source(
    writable: Sequence[str],
    readonly: Sequence[str],
    argv: Sequence[str],
    cwd: Optional[str] = None,
) -> str:
    """Python source for the in-process Landlock bootstrap that then `execv`s `argv`.

    The bootstrap applies the ruleset to ITSELF and then replaces its own image, so the
    restriction is in force before the worker's first instruction and - because Landlock
    domains are inherited across `fork`/`exec` and cannot be relaxed - applies to every
    descendant. A shell-capable worker cannot escape by spawning children.

    Paths that do not exist are skipped rather than fatal: a rule needs an existing inode,
    and a missing path is already inaccessible (fail-closed).
    """
    return textwrap.dedent(
        """\
        import ctypes, os, struct, sys

        LL_CREATE, LL_ADD_RULE, LL_RESTRICT = 444, 445, 446
        FILE_MASK = {file_mask}
        RO = {ro}

        libc = ctypes.CDLL("libc.so.6", use_errno=True)

        def _abi():
            return libc.syscall(LL_CREATE, None, ctypes.c_size_t(0), ctypes.c_uint32(1))

        abi = _abi()
        if abi < 1:
            sys.stderr.write("landlock unavailable: abi=%r\\n" % (abi,))
            raise SystemExit(125)

        if abi >= 3:
            ALL = (1 << 15) - 1
        elif abi == 2:
            ALL = (1 << 14) - 1
        else:
            ALL = (1 << 13) - 1

        attr = struct.pack("=QQ", ALL, 0)
        buf = ctypes.create_string_buffer(attr, len(attr))
        fd = libc.syscall(LL_CREATE, ctypes.byref(buf), ctypes.c_size_t(len(attr)), ctypes.c_uint32(0))
        if fd < 0:
            sys.stderr.write("landlock_create_ruleset failed errno=%d\\n" % ctypes.get_errno())
            raise SystemExit(125)

        def add(path, rights):
            if not os.path.exists(path):
                return
            if not os.path.isdir(path):
                rights &= FILE_MASK
            if not rights:
                return
            pfd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                rule = struct.pack("=Qi", rights, pfd)
                rb = ctypes.create_string_buffer(rule, len(rule))
                if libc.syscall(LL_ADD_RULE, ctypes.c_int(fd), ctypes.c_uint32(1),
                                ctypes.byref(rb), ctypes.c_uint32(0)) != 0:
                    sys.stderr.write("landlock add_rule failed for %s errno=%d\\n"
                                     % (path, ctypes.get_errno()))
                    raise SystemExit(125)
            finally:
                os.close(pfd)

        for p in {readonly!r}:
            add(p, RO)
        for p in {writable!r}:
            add(p, ALL)

        PR_SET_NO_NEW_PRIVS = 38
        if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
            sys.stderr.write("prctl(NO_NEW_PRIVS) failed\\n")
            raise SystemExit(125)
        if libc.syscall(LL_RESTRICT, ctypes.c_int(fd), ctypes.c_uint32(0)) != 0:
            sys.stderr.write("landlock_restrict_self failed errno=%d\\n" % ctypes.get_errno())
            raise SystemExit(125)

        cwd = {cwd!r}
        if cwd:
            os.chdir(cwd)
        argv = {argv!r}
        os.execvp(argv[0], argv)
        """
    ).format(
        file_mask=_LL_FILE_MASK,
        ro=_LL_READONLY,
        readonly=list(readonly),
        writable=list(writable),
        argv=list(argv),
        cwd=cwd,
    )


def _run_probe(argv: Sequence[str], **kwargs: Any) -> Tuple[int, str]:
    """Execute a probe command, mapping ANY failure to a nonzero result (fail-closed)."""
    try:
        proc = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
            **kwargs,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # includes TimeoutExpired
        return 127, f"{type(exc).__name__}: {exc}"
    return proc.returncode, (proc.stderr or proc.stdout or "").strip()


def _denial_checker_source(allowed_file: Path, denied_file: Path) -> str:
    """A checker that EXITS 0 only if the jail let the allowed write through and REFUSED the other.

    This is the standard EVERY rung must meet (see `_probe_bwrap`): "the launcher started"
    is not evidence of enforcement, because a misconfigured jail starts perfectly well and
    enforces nothing. Only an observed kernel REFUSAL proves a boundary exists.
    """
    return textwrap.dedent(
        f"""\
        import sys
        ok = {str(allowed_file)!r}
        bad = {str(denied_file)!r}
        try:
            open(ok, "w").write("x")
        except OSError as exc:
            sys.stderr.write("allowed write was DENIED: %s\\n" % exc)
            raise SystemExit(3)
        try:
            open(bad, "w").write("x")
        except OSError:
            raise SystemExit(0)          # enforced
        sys.stderr.write("denied write SUCCEEDED - not enforced\\n")
        raise SystemExit(4)
        """
    )


def _probe_landlock() -> Tuple[bool, str]:
    """ATTEMPT a Landlock jail and prove it actually DENIES a write outside the allowed root.

    Success requires more than "the syscalls returned 0": the probe writes inside its
    allowed root (which must SUCCEED) and outside it (which must be REFUSED). A kernel that
    accepts the ruleset but does not enforce it therefore reports False.
    """
    import tempfile

    with tempfile.TemporaryDirectory(prefix="aw-ll-probe-") as tmp:
        allowed = Path(tmp) / "allowed"
        denied = Path(tmp) / "denied"
        allowed.mkdir()
        denied.mkdir()
        checker = _denial_checker_source(allowed / "ok.txt", denied / "bad.txt")
        script = Path(tmp) / "check.py"
        script.write_text(checker, encoding="utf-8")
        boot = Path(tmp) / "boot.py"
        boot.write_text(
            landlock_bootstrap_source(
                writable=[str(allowed)],
                readonly=_default_toolchain_roots() + [tmp],
                argv=[sys.executable, str(script)],
            ),
            encoding="utf-8",
        )
        rc, err = _run_probe([sys.executable, str(boot)])
        if rc == 0:
            return (
                True,
                "landlock jail enforced: write outside the allowed root was refused",
            )
        return False, f"landlock probe rc={rc}: {err[:300]}"


def _probe_bwrap() -> Tuple[bool, str]:
    """ATTEMPT a real `bwrap` jail and prove it actually DENIES a write outside the lane.

    Held to the SAME standard as the Landlock rung (found at verification): the previous
    version returned True on `bwrap ... true` merely EXITING 0, which proves the launcher
    started, NOT that the partition is enforced. A `--bind / /` jail (fully writable)
    launches just as cleanly as a `--ro-bind / /` one, so a launch-only criterion cannot
    tell an enforcing jail from a permissive one - and reporting True for the permissive
    case is the fail-OPEN direction the design forbids. This now builds the REAL bind set
    (writable allowed root, read-only elsewhere) and requires the kernel to refuse the
    outside write.
    """
    if not shutil.which("bwrap"):
        return False, "bwrap not installed"
    import tempfile

    with tempfile.TemporaryDirectory(prefix="aw-bw-probe-") as tmp:
        allowed = Path(tmp) / "allowed"
        denied = Path(tmp) / "denied"
        allowed.mkdir()
        denied.mkdir()
        script = Path(tmp) / "check.py"
        script.write_text(
            _denial_checker_source(allowed / "ok.txt", denied / "bad.txt"),
            encoding="utf-8",
        )
        argv = ["bwrap", "--unshare-user", "--ro-bind", "/", "/", "--dev", "/dev"]
        argv += ["--bind", str(allowed), str(allowed)]
        argv += [sys.executable, str(script)]
        rc, err = _run_probe(argv)
        if rc == 0:
            return True, "bwrap jail enforced: write outside the bound root was refused"
        return False, f"bwrap probe rc={rc}: {err[:300]}"


def _probe_userns() -> Tuple[bool, str]:
    """A bare user namespace is NOT a per-path write boundary, so it is never a proven rung.

    Found at verification: `unshare -Umr` was previously treated as a proven sandbox rung,
    but `enter_sandbox` can only return `["unshare", "-Umr", "--", *argv]` for it - an argv
    that communicates NOTHING about the plan's writable/read-only/inaccessible partition.
    A worker launched that way shares the host mount namespace's paths and can still write
    the control root, the main worktree, every sibling lane, and the git common dir. Yet
    `detect_host_capabilities` would have set `supports_os_sandbox=True`,
    `select_execution_profile("hardened", ...)` would have GRANTED hard mode, and the
    module's published guarantees would have been claimed - with no boundary at all. That
    is precisely the silent degradation x03wgn Section 8 Phase 6.3 forbids, so this rung
    reports False until it is implemented as a real mount-namespace partition (mapping the
    plan's classes via `mount --bind` + remount-ro inside the new namespace).
    """
    return (
        False,
        "a bare user namespace enforces no per-path partition; not a proven sandbox rung "
        "(would fail OPEN - see _probe_userns docstring)",
    )


# The ladder, strongest-first. Each entry is (mechanism, probe). A rung may only appear
# here if its probe proves an actual DENIAL and `enter_sandbox` can enforce the full
# partition for it; `userns` stays listed so its report explains why it is never proven.
_SANDBOX_LADDER: Tuple[Tuple[str, Callable[[], Tuple[bool, str]]], ...] = (
    ("landlock", _probe_landlock),
    ("bwrap", _probe_bwrap),
    ("userns", _probe_userns),
)

# Cached per process: the probe launches subprocesses, and the answer cannot change
# mid-process. `None` means "not yet probed".
_SANDBOX_PROBE_CACHE: Optional[Tuple[Optional[str], Dict[str, str]]] = None


def _probe_linux_sandbox(
    force: bool = False,
) -> Tuple[Optional[str], Dict[str, str]]:
    """Execute the ladder and return (proven_mechanism_or_None, per-rung notes).

    THE SINGLE SOURCE OF SANDBOX TRUTH. `detect_host_capabilities` and the tests' skip
    helper both call this, so a reported capability and a skipped test can never disagree.
    """
    global _SANDBOX_PROBE_CACHE
    if _SANDBOX_PROBE_CACHE is not None and not force:
        return _SANDBOX_PROBE_CACHE

    notes: Dict[str, str] = {}
    proven: Optional[str] = None
    if sys.platform.startswith("linux"):
        for mechanism, probe in _SANDBOX_LADDER:
            try:
                ok, note = probe()
            except Exception as exc:  # a probe must never propagate; unknown => False
                ok, note = False, f"probe raised {type(exc).__name__}: {exc}"
            notes[mechanism] = note
            if ok:
                proven = mechanism
                break
    else:
        notes["platform"] = f"{sys.platform} is not the certified platform"

    _SANDBOX_PROBE_CACHE = (proven, notes)
    return _SANDBOX_PROBE_CACHE


def os_sandbox_available() -> bool:
    """True iff an ACTUAL jail attempt succeeded on this host. Backs the tests' skipif."""
    mechanism, _ = _probe_linux_sandbox()
    return mechanism is not None


def os_sandbox_mechanism() -> Optional[str]:
    """Which ladder rung this host proved, or None."""
    return _probe_linux_sandbox()[0]


def os_sandbox_probe_notes() -> Dict[str, str]:
    """Why each rung passed or failed - the evidence a skip must publish."""
    return dict(_probe_linux_sandbox()[1])


def detect_host_capabilities(
    host: str,
    platform_name: Optional[str] = None,
) -> HostSandboxCapabilities:
    """The x03wgn Layer 4 capability snapshot for `host`, fail-closed by default.

    `platform_name` (defaulting to `sys.platform`) selects the platform being asked about.
    Any platform other than the single certified one gets the all-False default: this phase
    certifies Linux only, so `hardened` fails closed elsewhere rather than pretending.

    `supports_os_sandbox` is NEVER decided by inspection. It is True only when
    `_probe_linux_sandbox()` actually built a jail and observed the kernel refuse a write
    outside the allowed root. See the module docstring for the measured counterexample that
    makes this mandatory.
    """
    plat = (platform_name or sys.platform or "").lower()
    caps = HostSandboxCapabilities(platform=plat)

    if not plat.startswith(CERTIFIED_PLATFORM):
        caps.probe_notes["platform"] = (
            f"{plat!r} is not the certified platform ({CERTIFIED_PLATFORM!r}); "
            "no capability asserted (fail-closed)"
        )
        return caps

    # POSIX process-group kill is what the driver already relies on to reap a worker tree
    # (`start_new_session=True` + `os.killpg`), so it is proven on this platform.
    caps.supports_process_tree_kill = os.name == "posix"

    if plat != (sys.platform or "").lower():
        # Asked about Linux from a non-Linux interpreter: we cannot execute a probe for a
        # platform we are not running on, so assert nothing.
        caps.probe_notes["platform"] = (
            f"cannot probe {plat!r} from {sys.platform!r}; no sandbox capability asserted"
        )
        return caps

    mechanism, notes = _probe_linux_sandbox()
    caps.probe_notes.update(notes)
    caps.sandbox_mechanism = mechanism
    caps.supports_os_sandbox = mechanism is not None
    # A read-only discovery phase is exactly a sandbox with the product tree read-only, so
    # it is available precisely when the sandbox itself is - and never otherwise.
    caps.supports_read_only_phase = caps.supports_os_sandbox

    if host == "opencode":
        # Proven by the existing driver: `--format json` streams structured events and
        # `--session <id>` resumes an exact session (oc_runipd.run_opencode).
        caps.emits_structured_tool_events = True
        caps.supports_session_resume = True
    return caps


def _default_toolchain_roots() -> List[str]:
    """Read-only roots a worker needs merely to RUN (interpreter, libs, config).

    Deliberately conservative: a missing entry is skipped, and nothing here is writable.

    The INTERPRETER roots are derived from the running interpreter rather than assumed to
    live under `/usr`: a venv splits `sys.prefix` (site-packages) from `sys.base_prefix`
    (stdlib), and omitting either makes the jailed process die in `init_import_site` before
    reaching its first instruction - which would look like "no sandbox" instead of "broken
    toolchain". `sys.path` entries are included because an import-path root outside those
    prefixes (a `PYTHONPATH` checkout) is equally required to start.
    """
    roots = ["/usr", "/lib", "/lib64", "/bin", "/sbin", "/etc", "/opt", "/proc"]
    for prefix in (sys.prefix, sys.base_prefix, sys.exec_prefix):
        if prefix:
            roots.append(str(Path(prefix).resolve()))
    roots.append(str(Path(sys.executable).resolve().parent))
    for entry in sys.path:
        if entry and os.path.exists(entry):
            roots.append(str(Path(entry).resolve()))
    home = os.path.expanduser("~")
    if home and home != "~":
        # The git identity a driver-side commit needs to READ. Never writable.
        roots.append(str(Path(home) / ".gitconfig"))
    seen: List[str] = []
    for root in roots:
        if root and root not in seen:
            seen.append(root)
    return seen


# ---------------------------------------------------------------------------
# E-03 / E-04: the writable / read-only / inaccessible partition
# ---------------------------------------------------------------------------


def _canon(path: Any) -> str:
    return str(Path(path).expanduser().resolve())


def _canon_all(paths: Optional[Iterable[Any]]) -> List[str]:
    return [_canon(p) for p in (paths or [])]


@dataclass
class SandboxPlan:
    """The explicit mount/permission classes required by x03wgn Section 4.

    A pure data structure with no side effects, so the partition can be unit-asserted.

    INACCESSIBLE is a class, not a rule list: under a default-deny sandbox anything not
    named writable or read-only is already unreachable. The set is materialized so the
    guarantee can be ASSERTED rather than assumed.
    """

    writable: List[str] = field(default_factory=list)
    readonly: List[str] = field(default_factory=list)
    inaccessible: List[str] = field(default_factory=list)
    git_common_dir: str = ""
    driver_owns_git_mutation: bool = True
    # `/dev` must be writable for the toolchain to function at all (git opens `/dev/null`
    # read-write; measured: with `/dev` read-only every git invocation dies with
    # "fatal: could not open '/dev/null' for reading and writing"). Device nodes are not
    # product state, so this is not a product-write capability.
    device_roots: List[str] = field(default_factory=lambda: ["/dev"])

    def validate(self) -> "SandboxPlan":
        """Refuse an internally unsafe plan (E-04). Returns self so it can be chained."""
        if self.git_common_dir and self.git_common_dir in self.writable:
            raise SandboxProfileError(
                "the git common directory must never be writable by the worker: "
                f"{self.git_common_dir!r} appears in `writable`. A linked worktree's .git "
                "points into the common dir, so a writable common dir lets the worker "
                "mutate shared refs/hooks/config (x03wgn Section 4). The DRIVER owns all "
                "git mutation."
            )
        overlap = set(self.writable) & set(self.inaccessible)
        if overlap:
            raise SandboxProfileError(
                f"paths cannot be both writable and inaccessible: {sorted(overlap)!r}"
            )
        if not self.driver_owns_git_mutation:
            raise SandboxProfileError(
                "hardened mode requires driver_owns_git_mutation=True: the worker cannot "
                "write the git common dir, so only the driver can stage/commit."
            )
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_sandbox_plan(
    lane_worktree: Any,
    lane_scratch: Any,
    toolchain_roots: Optional[Iterable[Any]] = None,
    control_root: Any = None,
    main_worktree: Any = None,
    sibling_lane_roots: Optional[Iterable[Any]] = None,
    integration_candidate: Any = None,
    credential_paths: Optional[Iterable[Any]] = None,
    git_common_dir: Any = None,
    build_caches: Optional[Iterable[Any]] = None,
    product_tree_readonly: bool = False,
) -> SandboxPlan:
    """Compute the x03wgn Section 4 partition for one lane. Pure; no side effects.

    WRITABLE     lane worktree, lane scratch, explicitly selected build caches
    READ-ONLY    required toolchain/dependencies, AND the git common directory (E-04)
    INACCESSIBLE control root, main worktree, every sibling lane, integration candidate,
                 credentials not needed by the task

    `product_tree_readonly=True` produces the PHASE 1 (discovery) variant: the lane product
    tree becomes read-only and only the narrow submission channel (`lane_scratch`) stays
    writable (x03wgn Section 6 Layer 4 step 1).
    """
    lane = _canon(lane_worktree)
    scratch = _canon(lane_scratch)
    common = _canon(git_common_dir) if git_common_dir else ""

    writable = [scratch] if product_tree_readonly else [lane, scratch]
    writable += [c for c in _canon_all(build_caches) if c not in writable]

    readonly: List[str] = []
    for root in _canon_all(
        toolchain_roots if toolchain_roots is not None else _default_toolchain_roots()
    ):
        if root not in readonly:
            readonly.append(root)
    if product_tree_readonly and lane not in readonly:
        readonly.append(lane)
    # The git common dir is read-only, NEVER writable (E-04). Read-only rather than
    # inaccessible so the worker's own `git status`/`diff`/`log` still work.
    if common and common not in readonly:
        readonly.append(common)

    inaccessible: List[str] = []
    for path in (
        [control_root, main_worktree, integration_candidate]
        + list(sibling_lane_roots or [])
        + list(credential_paths or [])
    ):
        if path is None:
            continue
        canon = _canon(path)
        if canon not in inaccessible:
            inaccessible.append(canon)

    # A path may not be BOTH reachable and inaccessible. The lane and the common dir are
    # deliberately reachable (that is the point of the profile), so they win. Everything
    # else named inaccessible must be stripped from the reachable classes.
    reachable_wins = set(writable) | {common} if common else set(writable)
    inaccessible = [p for p in inaccessible if p not in reachable_wins]
    readonly = [
        r for r in readonly if r not in set(inaccessible) and r not in set(writable)
    ]

    return SandboxPlan(
        writable=writable,
        readonly=readonly,
        inaccessible=inaccessible,
        git_common_dir=common,
        driver_owns_git_mutation=True,
    ).validate()


# ---------------------------------------------------------------------------
# E-05: wrap the worker argv in the jail
# ---------------------------------------------------------------------------


def _readonly_rule_paths(plan: SandboxPlan) -> List[str]:
    """Read-only roots to grant, MINUS anything the plan declares inaccessible.

    A broad toolchain root (say a user's home directory) can contain an inaccessible path (control
    root). Landlock resolves the DEEPEST matching rule, so a deep inaccessible path is not
    re-granted by a shallow read-only ancestor - but a read-only rule that IS an
    inaccessible path would be, so those are filtered out.
    """
    deny = set(plan.inaccessible)
    return [p for p in plan.readonly if p not in deny]


def enter_sandbox(
    argv: Sequence[str],
    sandbox_plan: SandboxPlan,
    capabilities: HostSandboxCapabilities,
    cwd: Optional[Any] = None,
    scratch_dir: Optional[Any] = None,
) -> List[str]:
    """Wrap the worker `argv` so the OS enforces `sandbox_plan`.

    Invoked ONLY when the hardened profile was explicitly selected AND
    `capabilities.supports_os_sandbox` is True. Refuses otherwise, so this function can
    never be the path by which an unsandboxed worker is launched while a caller believes it
    is hardened.

    The DRIVER - not the sandboxed worker - performs `git add`/commit/refs afterwards, so
    the worker never needs common-dir write access (x03wgn Section 4).
    """
    if not capabilities.supports_os_sandbox:
        raise HardModeUnavailableError(
            "refusing to build a sandbox launcher on a host whose executed probe reports "
            f"supports_os_sandbox=False (platform={capabilities.platform!r}, "
            f"notes={capabilities.probe_notes!r})"
        )
    sandbox_plan.validate()
    mechanism = capabilities.sandbox_mechanism or os_sandbox_mechanism()

    writable = list(sandbox_plan.writable) + list(sandbox_plan.device_roots)
    readonly = _readonly_rule_paths(sandbox_plan)

    if mechanism == "landlock":
        boot_dir = Path(scratch_dir) if scratch_dir else Path(sandbox_plan.writable[-1])
        boot_dir.mkdir(parents=True, exist_ok=True)
        boot = boot_dir / "aw-landlock-bootstrap.py"
        boot.write_text(
            landlock_bootstrap_source(
                writable=writable,
                readonly=readonly,
                argv=list(argv),
                cwd=str(cwd) if cwd else None,
            ),
            encoding="utf-8",
        )
        return [sys.executable, str(boot)]

    if mechanism == "bwrap":
        wrapped: List[str] = ["bwrap", "--unshare-user", "--die-with-parent"]
        for root in readonly:
            if Path(root).exists():
                wrapped += ["--ro-bind", root, root]
        for root in writable:
            if Path(root).exists():
                wrapped += ["--bind", root, root]
        wrapped += ["--dev", "/dev"]
        if cwd:
            wrapped += ["--chdir", str(cwd)]
        return wrapped + list(argv)

    if mechanism == "userns":
        # REFUSED rather than returned (found at verification). `unshare -Umr -- <argv>`
        # gives the worker a private user/mount namespace but does NOT restrict any path:
        # the control root, main worktree, sibling lanes, and git common dir all remain
        # writable. Returning it here would hand back a launcher that enforces nothing
        # while the caller believes hardened mode is active - a fail-OPEN outcome. Hard
        # mode fails CLOSED instead (x03wgn Section 8 Phase 6.3).
        raise HardModeUnavailableError(
            "the 'userns' mechanism cannot enforce the writable/read-only/inaccessible "
            "partition: a bare user namespace restricts no path, so the worker could still "
            "write the control root, main worktree, sibling lanes, and git common dir. "
            "Refusing to claim hardened mode without a real write boundary."
        )

    raise HardModeUnavailableError(
        f"no sandbox mechanism was proven on this host (mechanism={mechanism!r})"
    )


# ---------------------------------------------------------------------------
# E-06: fail-closed profile dispatch
# ---------------------------------------------------------------------------


def select_execution_profile(
    requested_profile: Optional[str],
    capabilities: HostSandboxCapabilities,
) -> str:
    """Resolve the execution profile, FAILING CLOSED when hard mode is unavailable.

    x03wgn Section 8 Phase 6.3: "fail rather than silently degrading when hard mode is
    requested but unavailable." Returning `"default"` for an unsupported `"hardened"`
    request would be that silent degradation, so this raises instead.
    """
    requested = (requested_profile or "default").strip().lower()
    if requested in ("", "default"):
        return "default"
    if requested != "hardened":
        raise SandboxProfileError(
            f"unknown execution profile {requested_profile!r}; expected "
            '"default" or "hardened"'
        )
    if not capabilities.supports_os_sandbox:
        raise HardModeUnavailableError(
            "the hardened execution profile was requested, but this host's EXECUTED "
            "sandbox probe reports it cannot enforce it "
            f"(platform={capabilities.platform!r}, notes={capabilities.probe_notes!r}). "
            "Refusing to run unsandboxed: hard mode fails closed rather than silently "
            "degrading (x03wgn Section 8 Phase 6.3)."
        )
    return "hardened"


# ---------------------------------------------------------------------------
# E-07: read-only discovery, then write execution
# ---------------------------------------------------------------------------


@dataclass
class DiscoveryExecutionResult:
    """Outcome of the two-phase run, including whether a REAL barrier existed."""

    barrier_enforced: bool
    discovery_plan: Optional[SandboxPlan] = None
    execution_plan: Optional[SandboxPlan] = None
    discovery_validated: bool = False
    discovery_submission: Optional[Any] = None
    discovery_result: Optional[Any] = None
    execution_result: Optional[Any] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        for key in ("discovery_plan", "execution_plan"):
            if out[key] is not None:
                out[key] = dict(out[key])
        return out


def run_discovery_then_execution(
    lane_worktree: Any,
    lane_scratch: Any,
    capabilities: HostSandboxCapabilities,
    run_discovery: Callable[[SandboxPlan], Any],
    validate_submission: Callable[[Any], bool],
    run_execution: Callable[[SandboxPlan, Any], Any],
    read_submission: Optional[Callable[[], Any]] = None,
    **plan_kwargs: Any,
) -> DiscoveryExecutionResult:
    """x03wgn Section 6 Layer 4: read-only discovery, then write execution.

    PHASE 1 launches the worker with the PRODUCT TREE READ-ONLY and only the narrow
    submission channel (`lane_scratch`) writable.
    PHASE 2 flips the sandbox to grant product writes and relaunches/resumes with the
    validated discovery result injected.

    Offered ONLY when `supports_read_only_phase` AND `emits_structured_tool_events` are
    both True. Otherwise NO before-edit barrier is claimed (`barrier_enforced=False`) and
    the caller must keep the prerequisite in the driver - x03wgn Layer 4: "If the host
    cannot enforce read-only files or phase-specific tools, the barrier is advisory."

    A PROSE claim is never sufficient: the driver validates a STRUCTURED submission, and a
    submission that fails validation does NOT get product writes.
    """
    if not (
        capabilities.supports_read_only_phase
        and capabilities.emits_structured_tool_events
    ):
        missing = [
            name
            for name, present in (
                ("supports_read_only_phase", capabilities.supports_read_only_phase),
                (
                    "emits_structured_tool_events",
                    capabilities.emits_structured_tool_events,
                ),
            )
            if not present
        ]
        return DiscoveryExecutionResult(
            barrier_enforced=False,
            reason=(
                "no before-edit barrier is claimed: this host lacks "
                f"{', '.join(missing)}. The barrier would be advisory only, so the "
                "prerequisite must stay in the driver (x03wgn Section 6 Layer 4)."
            ),
        )

    discovery_plan = build_sandbox_plan(
        lane_worktree,
        lane_scratch,
        product_tree_readonly=True,
        **plan_kwargs,
    )
    execution_plan = build_sandbox_plan(
        lane_worktree,
        lane_scratch,
        product_tree_readonly=False,
        **plan_kwargs,
    )

    discovery_result = run_discovery(discovery_plan)
    submission = read_submission() if read_submission is not None else discovery_result
    validated = bool(validate_submission(submission))
    if not validated:
        return DiscoveryExecutionResult(
            barrier_enforced=True,
            discovery_plan=discovery_plan,
            execution_plan=execution_plan,
            discovery_validated=False,
            discovery_submission=submission,
            discovery_result=discovery_result,
            reason=(
                "the structured discovery submission failed driver validation; product "
                "writes were NOT authorized (x03wgn Section 6 Layer 4 step 2)."
            ),
        )

    execution_result = run_execution(execution_plan, submission)
    return DiscoveryExecutionResult(
        barrier_enforced=True,
        discovery_plan=discovery_plan,
        execution_plan=execution_plan,
        discovery_validated=True,
        discovery_submission=submission,
        discovery_result=discovery_result,
        execution_result=execution_result,
        reason="discovery validated; product writes authorized for the execution phase.",
    )
