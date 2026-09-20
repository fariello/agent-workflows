"""rununify 05 (`ct4w0a`): the TWO symbols where the two host runners genuinely DISAGREED.

Sixteen of this Set's shared symbols were duplicates that agreed. These two did not, and that is why
they were separated out: unifying them required DECIDING which behavior is correct, and a decision
nobody can see is a decision nobody can defend later. This file is where each decision is pinned.

WHAT IS ASSERTED, and why a bare "both hosts resolve the same object" would be worth very little here:

  1. ONE DEFINITION, reached identically from both hosts, with no module in the package re-forking it.
     Necessary, and nowhere near sufficient: a unified reader that lost one host's wire format would
     satisfy it perfectly while silently disabling that host's session resume.

  2. EVERY CAPABILITY EITHER HOST HAD, still present. `extract_session_id` must resolve an id for all
     four keys and both nesting shapes, and must still PREFER a `ses_`-prefixed value.

  3. THE FIRST-EVER COVERAGE FOR ANTIGRAVITY'S WIRE FORMAT. Measured while this plan was reviewed:
     `conversation_id` appeared in NO test in the repository, and `extract_session_id` was exercised
     only through two oc-shaped cases. So the central hazard -- that adopting oc's reader outright
     leaves agy unable to find its own session id -- was simultaneously TRUE and INVISIBLE. Every
     `AgyWireFormatTests` case below is additionally shown to FAIL against oc's pre-union reader
     (reconstructed here from its shipped body), which is what makes it a test of the CAPABILITY
     rather than a test that the union merely exists.

  4. THE PRECEDENCE DECISION, pinned as a decision. The two readers disagreed about return DISCIPLINE
     as well as about keys, so no union could preserve both answers; see `PrecedenceTests`.

  5. NON-VACUITY CONTROLS. Each capability is removed from a REPLICA of the shared body and the
     corresponding assertion is shown to fail. A capability test that would pass against a reader
     lacking the capability is decoration.

WHY A REPLICA RATHER THAN MONKEYPATCHING THE REAL FUNCTION: the controls must not mutate shared state
that another test in a parallel worker could observe. Each control below re-implements ONE deliberately
crippled variant locally and runs it over the same fixture, so the sabotage is inspectable and cannot
leak. The replicas are held to the real body by `ControlFidelityTests`, so a control cannot drift into
proving something about a strawman.
"""

from __future__ import annotations

import ast
import inspect
import json
import pathlib
import subprocess
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared

BOTH = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))
_PKG = pathlib.Path(runner_shared.__file__).parent

# Written in two pieces so this file never contains a literal that looks like a real session id.
_SES = "ses" + "_"


class _SpawnRecorder:
    """Record every child process spawned inside the block, and spawn none of them for real.

    WHY `subprocess.Popen` AND NOT `subprocess.run`: `run`, `check_output` and `check_call` are all
    thin wrappers that construct a `Popen`, so patching this ONE attribute observes every spelling of
    a launch, including an aliased import a source-text search would miss. That is the whole reason
    this recorder exists: the guards it replaces asserted the STRING `subprocess.run` was absent from
    a function body, which any other spelling defeats.

    Nothing is actually launched (a `_StubProcess` is returned), because these tests assert that a
    delegating wrapper spawns nothing; a wrapper that DOES spawn must not get to run a real child
    against a nonexistent repo path.
    """

    class _StubProcess:
        def __init__(self) -> None:
            self.pid = -1
            self.stdout = iter(())
            self.stderr = iter(())
            self.stdin = None
            self.returncode = 0
            self.args: list[str] = []

        def poll(self) -> int:
            return 0

        def wait(self, timeout=None) -> int:
            return 0

        def communicate(self, input=None, timeout=None):
            return ("", "")

        def kill(self) -> None:
            return None

        def __enter__(self):
            return self

        def __exit__(self, *exc) -> None:
            return None

    def __init__(self) -> None:
        self.argvs: list[list[str]] = []

    def __enter__(self) -> "_SpawnRecorder":
        def recording_popen(args, *a, **kw):
            if isinstance(args, (str, bytes)):
                self.argvs.append([args if isinstance(args, str) else args.decode()])
            else:
                self.argvs.append([str(token) for token in args])
            return self._StubProcess()

        self._patch = mock.patch.object(subprocess, "Popen", recording_popen)
        self._patch.start()
        return self

    def __exit__(self, *exc) -> None:
        self._patch.stop()


def _child_env_for_begin(host, **kwargs) -> dict[str, str]:
    """Return the env the REAL shared launcher hands its child for `host.driver_begin(**kwargs)`.

    Used to assert the EFFECT of the `isolated` declaration rather than only the argument, because the
    non-isolated call site passes no keyword and so inherits the shared function's DEFAULT: an
    argument-only assertion cannot see that default being flipped. Only `subprocess.run` is patched,
    so the argv/env construction under test runs for real and nothing is launched.
    """
    captured: dict[str, dict[str, str]] = {}

    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def recording_run(argv, *a, **kw):
        captured["env"] = dict(kw.get("env") or {})
        return _Result()

    with mock.patch.object(runner_shared.subprocess, "run", recording_run):
        host.driver_begin(
            pathlib.Path("/nonexistent-repo-for-this-test"),
            "abc123",
            "actor/model",
            **kwargs,
        )
    return captured.get("env", {})


_HARNESS_PLAN = (
    "# IPD: iso001\n\n"
    "- Date: 2026-09-08\n"
    "- Kind: child\n"
    "- Status: approved\n"
    "- Set: demo\n"
    "- Order: 1\n"
    "- Id: iso001\n\n"
    "## Goal\nA real goal statement.\n"
)


class _ExecuteItemHarness:
    """A throwaway repo plus the state/item pair `execute_item` needs, for DRIVING one queue item.

    WHY THIS EXISTS. Several claims in this file are about what `execute_item` DOES at a particular
    decision point (which `isolated` value reaches the begin gate; whether the lane is allocated
    before or after begin). Each was previously asserted by reading `execute_item_core`'s SOURCE TEXT
    and searching for literals or comparing byte offsets, which breaks on any rename or reformat and
    is satisfiable by a comment. Driving the real function with the collaborators spied is what
    actually observes those decisions.

    The harness deliberately does NOT stub `driver_begin`: each test installs its own spy, because the
    gate's return value is what selects the path under test (refuse -> stop early, allow -> proceed to
    the lane). Nothing here launches an agent: the tests stop the turn at begin or at allocation.
    """

    def __init__(self, host, *, isolate_worktree: bool) -> None:
        self.host = host
        self._temp = tempfile.TemporaryDirectory()
        root = Path(self._temp.name)
        self.repo = root / "repo"
        self.repo.mkdir(parents=True)
        for args in (
            ["init", "-q"],
            ["config", "user.email", "t@e.com"],
            ["config", "user.name", "T"],
        ):
            subprocess.run(["git", *args], cwd=self.repo, check=True)
        plans = self.repo / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True)
        self.plan = plans / "20260908-demo-01-iso001-demo.ipd.md"
        self.plan.write_text(_HARNESS_PLAN, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.repo, check=True)

        self.run_dir = self.repo / ".aw" / "records" / "runs" / "run-test"
        (self.run_dir / "outcomes").mkdir(parents=True)
        (self.run_dir / "prompts").mkdir(parents=True)
        self.item: dict[str, object] = {
            "position": 1,
            "id6": "iso001",
            "setid": "demo",
            "status": "queued",
            "configured_file": str(self.plan.relative_to(self.repo)),
            "action": "execute",
        }
        self.state: dict[str, object] = {
            "run_id": "run-test",
            "created_at": "2026-09-08T00:00:00+00:00",
            "updated_at": "2026-09-08T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(self.repo),
            "queue": [self.item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": isolate_worktree,
                "no_audit": True,
            },
        }

    def __enter__(self) -> "_ExecuteItemHarness":
        return self

    def __exit__(self, *exc) -> None:
        self._temp.cleanup()

    def run(self) -> None:
        """Execute the one queued item, swallowing the deliberate stubs' AssertionErrors.

        A stub that raises is how a test says "this must not be reached"; the raise is recorded in the
        caller's order list, so the assertion is made there rather than by the traceback.
        """
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            with contextlib.suppress(AssertionError):
                self.host.execute_item(
                    self.run_dir, self.state, self.item, recovery=False
                )
        self.output = buffer.getvalue()


def _log(*events: object) -> Path:
    """Write a JSONL session log in a temp dir and return its path (caller owns the dir)."""
    temp = tempfile.mkdtemp()
    path = Path(temp) / "session.jsonl"
    path.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n",
        encoding="utf-8",
    )
    return path


# ---- the pre-union oc reader, reconstructed for the "does this test the capability?" control -------
#
# THE POINT OF KEEPING THIS. A test asserting the shared reader finds `conversation_id` proves the
# union works, but not that it was ever at RISK. Running the SAME fixture through oc's pre-union body
# and showing it returns None is what demonstrates the capability would really have been lost, which is
# the claim (F-1) that justified excepting this symbol from the Set's oc-preferred ruling.
_OC_PRE_UNION_KEYS = ("sessionID", "sessionId", "session_id")


def _oc_pre_union_reader(log_path: Path) -> str | None:
    """oc's `extract_session_id` as it stood at 1171f7b2: three flat keys, no nesting, no dict guard."""
    if not log_path.exists():
        return None
    fallback: str | None = None
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in _OC_PRE_UNION_KEYS:
                value = event.get(key)
                if not isinstance(value, str) or not value.strip():
                    continue
                if value.startswith(_SES):
                    return value
                if fallback is None:
                    fallback = value
    return fallback


class OneDefinitionTests(unittest.TestCase):
    """Property 1: one definition, reached identically, with no re-fork anywhere in the package."""

    SHARED = ("extract_session_id", "begin_baseline_env", "_SESSION_ID_KEYS")

    def test_both_hosts_resolve_the_same_object(self):
        for name in self.SHARED:
            with self.subTest(symbol=name):
                shared = getattr(runner_shared, name)
                for host_name, host in BOTH:
                    self.assertIs(
                        getattr(host, name),
                        shared,
                        f"{host_name}.{name} is a DIFFERENT object from the shared one",
                    )

    def test_the_defining_module_is_runner_shared(self):
        for name in ("extract_session_id", "begin_baseline_env"):
            with self.subTest(symbol=name):
                self.assertEqual(
                    getattr(runner_shared, name).__module__,
                    "agent_workflows.runner_shared",
                )

    def test_no_module_in_the_package_re_forks_either_symbol(self):
        """Checked REPO-WIDE by AST: a pairwise oc-vs-agy check passes while a third module copies."""
        for name in ("extract_session_id", "begin_baseline_env"):
            offenders = []
            for path in sorted(_PKG.rglob("*.py")):
                if path.name == "runner_shared.py":
                    continue
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except SyntaxError:  # pragma: no cover
                    continue
                for node in tree.body:
                    if (
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name == name
                    ):
                        offenders.append(f"{path.name}:{node.lineno}")
            with self.subTest(symbol=name):
                self.assertEqual(
                    offenders,
                    [],
                    f"{name} is re-defined outside runner_shared: {offenders}",
                )

    def test_the_session_key_list_is_ONE_tuple_with_all_four_keys(self):
        """It was defined TWICE with DIFFERENT contents (oc 3 keys, agy 4), which is how it forked."""
        self.assertEqual(
            runner_shared._SESSION_ID_KEYS,
            ("sessionID", "sessionId", "session_id", "conversation_id"),
        )
        sources = {}
        for host_name, host in BOTH:
            tree = ast.parse(inspect.getsource(host))
            sources[host_name] = [
                node.lineno
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(t, ast.Name) and t.id == "_SESSION_ID_KEYS"
                    for t in node.targets
                )
            ]
        self.assertEqual(
            sources,
            {"oc_runipd": [], "agy_runipd": []},
            "neither host may keep its own `_SESSION_ID_KEYS`; a second constant is how the next "
            f"reader re-forks the disagreement: {sources}",
        )

    def test_driver_begin_has_exactly_one_launcher_body(self):
        """The hosts keep WRAPPERS (their pin helpers cannot move); the BODY must exist once.

        A wrapper is not a re-fork -- it is the de-duplicated form the maintainer ruled for an injected
        dependency (`818uru` OQ-02) -- so what is asserted is that no host body launches a subprocess.

        DRIVEN, NOT GREPPED. This previously read each wrapper's SOURCE and asserted `subprocess.run`
        was absent from it while `runner_shared.driver_begin` was present. Both halves were weak: the
        absence half is satisfied by spelling the launch differently (`Popen`, `check_output`, an
        aliased import), and the presence half is satisfied by a COMMENT naming the shared function,
        which is the exact failure mode measured twice in this repository. So each wrapper is now
        CALLED with the shared launcher replaced by a spy: a wrapper that delegates records the call
        and spawns NOTHING, while a wrapper holding its own launcher body spawns a real child (seen by
        the argv recorder) and is caught however it spells the spawn.

        THE INJECTED DEPENDENCIES ARE ASSERTED BY IDENTITY, which is the point of the whole wrapper
        design: each host must bind ITS OWN `pinned_child_env` / `pinned_module_argv` objects, because
        the pin is what stops a nested `aw` resolving the package from a lane worktree (`af7i6p`). A
        wrapper that delegated but passed the WRONG host's pin would have satisfied the old text pin
        perfectly.
        """
        failures = []
        for host_name, host in BOTH:
            recorded: list[dict[str, object]] = []

            def spy(
                repo, id6, actor, *, isolated=False, env_builder=None, argv_builder=None
            ):
                recorded.append(
                    {
                        "repo": repo,
                        "id6": id6,
                        "actor": actor,
                        "isolated": isolated,
                        "env_builder": env_builder,
                        "argv_builder": argv_builder,
                    }
                )
                return (0, "stubbed by the delegation test")

            with _SpawnRecorder() as spawns:
                with mock.patch.object(runner_shared, "driver_begin", spy):
                    result = host.driver_begin(
                        pathlib.Path("/nonexistent-repo-for-this-test"),
                        "abc123",
                        "actor/model",
                        isolated=True,
                    )

            problems = []
            if len(recorded) != 1:
                problems.append(
                    f"the shared launcher was called {len(recorded)} time(s), expected exactly 1"
                )
            if spawns.argvs:
                problems.append(
                    f"the wrapper SPAWNED a child process itself: {spawns.argvs!r}"
                )
            if result != (0, "stubbed by the delegation test"):
                problems.append(
                    f"the wrapper did not return the shared launcher's result verbatim: {result!r}"
                )
            if recorded:
                call = recorded[0]
                if call["isolated"] is not True:
                    problems.append(
                        f"`isolated=True` was not forwarded (got {call['isolated']!r})"
                    )
                if call["id6"] != "abc123" or call["actor"] != "actor/model":
                    problems.append(f"arguments were altered in transit: {call!r}")
                if call["env_builder"] is not host.pinned_child_env:
                    problems.append(
                        "the wrapper did not bind THIS host's `pinned_child_env` object"
                    )
                if call["argv_builder"] is not host.pinned_module_argv:
                    problems.append(
                        "the wrapper did not bind THIS host's `pinned_module_argv` object"
                    )
            if problems:
                failures.append(f"  {host_name}: {'; '.join(problems)}")

        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(BOTH)} host `driver_begin` wrappers are not pure delegations. "
            "The sanctioned shape (`818uru` OQ-02) is: ONE launcher body in `runner_shared`, one "
            "one-line wrapper per host binding that host's pin helpers. A wrapper that spawns its own "
            "child is the second launcher body this Set exists to remove, and it is how agy's copy "
            "came to silently lack the `isolated` declaration in the first place. A wrapper that "
            "delegates but passes the WRONG host's pin is subtler and just as bad: the nested `aw` "
            "then resolves `agent_workflows` from the lane worktree (`af7i6p`).\n"
            + "\n".join(failures),
        )
        self.assertIs(
            oc_runipd.runner_shared.driver_begin,
            agy_runipd.runner_shared.driver_begin,
            "both hosts must reach the SAME shared launcher",
        )

    def test_each_wrapper_keeps_the_original_signature(self):
        """No call site in either driver may have needed rewriting."""
        for host_name, host in BOTH:
            with self.subTest(host=host_name):
                sig = inspect.signature(host.driver_begin)
                self.assertEqual(
                    list(sig.parameters),
                    ["repo", "id6", "actor", "isolated"],
                    f"{host_name}.driver_begin's public signature changed",
                )
                isolated = sig.parameters["isolated"]
                self.assertEqual(isolated.kind, inspect.Parameter.KEYWORD_ONLY)
                self.assertIs(isolated.default, False)
                # The injected dependencies must NOT leak into the host-facing signature.
                self.assertNotIn("env_builder", sig.parameters)
                self.assertNotIn("argv_builder", sig.parameters)


class UnionCoversEveryKeyAndNestingTests(unittest.TestCase):
    """Property 2: an id is found for EVERY key and EVERY nesting shape in the union.

    INCLUDING THE THREE KEYS AND THE `init` NESTING THAT ZERO REAL LOGS CONTAIN. They are retained
    deliberately (narrowing a wire-format reader on 627 logs is absence-of-evidence reasoning, and the
    same tuple is read live by `oc_runipd._event_session_id`), and a retained branch with no test is
    exactly how a branch rots. So each is exercised here.
    """

    def test_every_flat_key_resolves(self):
        for key in runner_shared._SESSION_ID_KEYS:
            with self.subTest(key=key, nesting="flat"):
                log = _log({"type": "text", key: "id-for-" + key})
                self.assertEqual(runner_shared.extract_session_id(log), "id-for-" + key)

    def test_every_key_resolves_inside_every_nesting(self):
        for nest in runner_shared._SESSION_ID_NESTS:
            for key in runner_shared._SESSION_ID_KEYS:
                with self.subTest(key=key, nesting=nest):
                    log = _log({"type": "x", nest: {key: "nested-" + key}})
                    self.assertEqual(
                        runner_shared.extract_session_id(log), "nested-" + key
                    )

    #: (case, the log to read - a tuple of events, or a RAW string written verbatim, or None for an
    #: absent file - the id the reader must return, why this row exists)
    #:
    #: ONE TABLE because every row is the same operation: hand `extract_session_id` a whole log and
    #: compare its answer. What used to be five separate tests were five DATA shapes, and reading them
    #: as a set is what makes the reader's contract legible: which events are skipped, which values are
    #: rejected as ids, and what "no id" returns.
    WHOLE_LOG_READS = (
        (
            "a `ses_`-prefixed value arriving LATER than an unprefixed one",
            ({"sessionID": "raw-provider-id"}, {"sessionID": _SES + "realsession1"}),
            _SES + "realsession1",
            "OC'S PREFERENCE, the shipped tested contract this union deliberately kept (decision "
            "`06-ct4w0a-D1`). The prefixed value must win even though it is SECOND, which is the whole "
            "reason the reader scans the entire file instead of returning its first hit",
        ),
        (
            "list, int and string events preceding a real one",
            (["not", "a", "dict"], 42, "a string", {"sessionID": _SES + "after"}),
            _SES + "after",
            "AGY'S GUARD, kept. A JSONL line may legitimately be a list or a scalar and `.get` on one "
            "RAISES; oc's reader had no such guard, so adopting it outright would have crashed on an "
            "agy-shaped log rather than merely failing to find the id",
        ),
        (
            "an unparseable line preceding a real one",
            "{not json at all\n" + json.dumps({"sessionID": _SES + "ok"}) + "\n",
            _SES + "ok",
            "a truncated or interleaved write must not cost the whole log. Written as RAW TEXT because "
            "the point is bytes that are not JSON at all, which no event tuple can express",
        ),
        (
            "an absent log file",
            None,
            None,
            "ABSENCE IS None, NOT AN EXCEPTION: the reader is called on a log path that may not exist "
            "yet (a turn that died before its first write), and a raise there would take down the "
            "driver rather than merely leaving the session unresumable",
        ),
        (
            "a log with events but no id anywhere",
            ({"type": "text"},),
            None,
            "the other None case, kept beside the absent-file row so a reader that returned a truthy "
            "sentinel for 'nothing found' fails one of them",
        ),
        (
            "blank, whitespace, numeric and null values before a real id",
            (
                {"sessionID": ""},
                {"sessionID": "   "},
                {"sessionID": 12345},
                {"sessionID": None},
                {"conversation_id": "real-conv-id"},
            ),
            "real-conv-id",
            "A PRESENT KEY IS NOT AN ID. Each of these four would be accepted by a naive "
            "`if key in event` check, and any one of them latching would bind the run to a session id "
            "of `''` or `12345`, which no host can resume",
        ),
    )

    def test_the_reader_resolves_a_whole_log_correctly_for_every_shape(self):
        failures = []
        for case, source, expected, why in self.WHOLE_LOG_READS:
            if source is None:
                log = Path(tempfile.mkdtemp()) / "absent.jsonl"
            elif isinstance(source, str):
                log = Path(tempfile.mkdtemp()) / "s.jsonl"
                log.write_text(source, encoding="utf-8")
            else:
                log = _log(*source)
            got = runner_shared.extract_session_id(log)
            if got != expected:
                failures.append(
                    f"  {case}: expected {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"extract_session_id returned the wrong id for {len(failures)} of "
            f"{len(self.WHOLE_LOG_READS)} whole-log shapes. Read them together: if the two None rows "
            "are the only failures, the reader now invents an id where there is none, and a run will "
            "try to resume a session that does not exist; if the PREFERENCE row alone failed, "
            "somebody reverted the return discipline to agy's first-hit form, which is a DECISION "
            "change and must be made in the open rather than by drift (see `PrecedenceTests`); if the "
            "skip rows failed with an exception, a malformed line can now kill a turn. FIX: the reader "
            "is `runner_shared.extract_session_id`, the ONE definition both hosts use.\n"
            + "\n".join(failures),
        )


class AgyWireFormatTests(unittest.TestCase):
    """Property 3: THE FIRST-EVER COVERAGE for Antigravity's session wire format.

    Measured at this plan's review: `conversation_id` appeared in NO test file in the repository, and
    `extract_session_id` was exercised only by two oc-shaped cases in `tests/test_oc_runipd.py`. That
    is why "adopt oc's reader" would have disabled agy's session resume SILENTLY: nothing anywhere
    would have gone red. Each test here therefore does two things -- asserts the shared reader finds
    the id, and asserts oc's PRE-UNION reader does NOT -- so it tests the capability rather than the
    union's existence.

    WHAT LOSING THIS WOULD COST, since it explains why a `None` here is not cosmetic: with no observed
    session id, `aw agy run` cannot resume a session, and the `b7xarm` one-shot defect-report re-ask
    REFUSES to fire, so a real defect report would be dropped rather than re-requested.
    """

    #: (case, the events of the log, the id the SHARED reader must return, the id OC'S PRE-UNION reader
    #: returns for the same log, why this row exists)
    #:
    #: THE FOURTH COLUMN IS THE NON-VACUITY CONTROL, carried per row rather than in a separate class:
    #: `None` means "this capability would really have been LOST by adopting oc's reader outright",
    #: which is the F-1 claim that justified excepting this symbol from the Set's oc-preferred ruling.
    #: The oc row carries a real id instead, which is what proves the union traded nothing away.
    WIRE_FORMATS = (
        (
            "flat conversation_id (agy)",
            ({"type": "result", "conversation_id": "conv-flat-1"},),
            "conv-flat-1",
            None,
            "THE CENTRAL CAPABILITY. `conversation_id` appeared in NO test in the repository when this "
            "plan was reviewed, so 'adopt oc's reader' would have disabled agy's session resume with "
            "nothing anywhere going red",
        ),
        (
            "conversation_id nested under `result` (agy)",
            ({"type": "result", "result": {"conversation_id": "conv-nested-1"}},),
            "conv-nested-1",
            None,
            "the shape actually OBSERVED in the real corpus: agy writes it both flat and under "
            "`result`, so a reader covering only the flat form still loses real logs",
        ),
        (
            "conversation_id nested under `init` (agy)",
            ({"type": "init", "init": {"conversation_id": "conv-init-1"}},),
            "conv-init-1",
            None,
            "UNOBSERVED in the 627 logs censused and retained DELIBERATELY (narrowing a wire-format "
            "reader on a finite census is absence-of-evidence reasoning). A retained branch with no "
            "test is exactly how a branch rots, so it is exercised here",
        ),
        (
            "a realistic multi-event agy log",
            (
                {"type": "system", "subtype": "init"},
                {"type": "assistant", "message": {"content": "working"}},
                {"type": "result", "result": {"conversation_id": "conv-realistic-9"}},
            ),
            "conv-realistic-9",
            None,
            "not a single hand-built event but the SEQUENCE agy really writes, so the reader is shown "
            "to skip the preceding events rather than merely to parse one crafted line",
        ),
        (
            "oc's own wire format",
            ({"type": "step-start", "sessionID": _SES + "ocshape1"},),
            _SES + "ocshape1",
            _SES + "ocshape1",
            "THE OTHER DIRECTION, and the row that stops this table from proving a one-sided win: the "
            "union must not have traded oc's format for agy's. Its control column is a real id rather "
            "than None precisely because oc's reader always handled this",
        ),
    )

    def test_every_hosts_wire_format_resolves_and_the_capability_was_really_at_risk(
        self,
    ):
        failures = []
        for case, events, expected, pre_union_expected, why in self.WIRE_FORMATS:
            log = _log(*events)
            got = runner_shared.extract_session_id(log)
            pre_union = _oc_pre_union_reader(log)
            problems = []
            if got != expected:
                problems.append(
                    f"the shared reader returned {got!r}, expected {expected!r}"
                )
            if pre_union != pre_union_expected:
                problems.append(
                    f"oc's PRE-UNION reader returned {pre_union!r}, expected "
                    f"{pre_union_expected!r}; the non-vacuity control for this row is wrong, so the "
                    "row proves nothing about the union"
                )
            if problems:
                failures.append(
                    f"  {case}: {'; '.join(problems)}\n    this row exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(self.WIRE_FORMATS)} wire formats are broken. Read the two "
            "columns together: a failure in the SHARED reader column on the agy rows means agy can no "
            "longer find its own session id, and the cost is concrete - `aw agy run` cannot resume a "
            "session and the `b7xarm` one-shot defect-report re-ask REFUSES to fire, so a real defect "
            "report is dropped rather than re-requested. A failure in the PRE-UNION column instead "
            "means this file's reconstruction of oc's old reader has drifted (see "
            "`ControlFidelityTests`), which invalidates the capability claim rather than the code. If "
            "the OC row fails while the agy rows pass, the union traded one host's format for the "
            "other's, which is the exact failure this symbol was separated out to prevent.\n"
            + "\n".join(failures),
        )


class PrecedenceTests(unittest.TestCase):
    """Property 4: THE PRECEDENCE DECISION, recorded as a decision (decision `06-ct4w0a-D1`).

    The two readers disagreed about RETURN DISCIPLINE, not only about keys: agy returned the FIRST
    non-empty hit immediately, while oc scanned the WHOLE file and kept a non-`ses_` value only as a
    fallback. NO UNION CAN PRESERVE BOTH ANSWERS, so on the one shape where they differ -- an
    unprefixed id EARLY and a `ses_` id LATER in the same log -- somebody's answer had to change.

    THE DECISION IS OC'S DISCIPLINE, for three stated reasons: oc's preference is a SHIPPED TESTED
    CONTRACT (`tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed`)
    while nothing pinned agy's ordering anywhere; the standing maintainer ruling prefers oc absent a
    significant behavioral difference; and the affected shape needs an OpenCode-style `ses_` id to
    appear in a log that also carries an Antigravity `conversation_id`, which occurred in 0 of the 627
    logs censused. This test exists so that answer is a recorded decision rather than an emergent
    property a later reader discovers from a surprising run.
    """

    def _mixed_log(self) -> Path:
        return _log(
            {"type": "result", "conversation_id": "conv-EARLY"},
            {"type": "step", "sessionID": _SES + "LATER"},
        )

    def test_the_union_returns_the_ses_prefixed_value_not_the_earlier_conversation_id(
        self,
    ):
        self.assertEqual(
            runner_shared.extract_session_id(self._mixed_log()),
            _SES + "LATER",
            "the recorded decision is oc's discipline: scan the whole log and prefer `ses_`",
        )

    def test_this_is_the_answer_agys_pre_union_reader_did_NOT_give(self):
        """The change is disclosed rather than asserted away: agy returned `conv-EARLY` here.

        Reconstructs agy's pre-union first-hit discipline over the same fixture, so the behavior
        change this plan makes is visible in the suite rather than only in a plan's prose.
        """

        def agy_pre_union(log_path: Path) -> str | None:
            with log_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        continue
                    for key in runner_shared._SESSION_ID_KEYS:
                        value = event.get(key)
                        if isinstance(value, str) and value.strip():
                            return value  # FIRST hit, immediately
            return None

        log = self._mixed_log()
        self.assertEqual(agy_pre_union(log), "conv-EARLY")
        self.assertEqual(runner_shared.extract_session_id(log), _SES + "LATER")

    def test_a_log_with_no_prefixed_value_still_returns_the_first_it_saw(self):
        """The fallback is FIRST-seen, so the change is confined to the mixed case."""
        log = _log(
            {"conversation_id": "conv-first"},
            {"sessionID": "raw-second"},
        )
        self.assertEqual(runner_shared.extract_session_id(log), "conv-first")

    def test_the_fallback_local_is_live_here_and_no_host_holds_a_second_body_to_deaden(
        self,
    ):
        """agy's body initialized `fallback`, returned it, and could never reach it non-None.

        Here `fallback` is LIVE (it IS oc's discipline), which is exactly why the dead twin had to go:
        a reader comparing the two would otherwise credit agy with a discipline it did not have.

        CONVERTED FROM TEXT TO AST, and one half CONVERTED TO BEHAVIOR. The old form did
        `assertIn("fallback", src)` plus `assertNotIn("def extract_session_id", mod_src)`, i.e. two
        substring searches. Both are satisfiable by prose: a docstring sentence containing the word
        `fallback` satisfies the first (and the real docstring DOES discuss it at length, so the check
        was very close to vacuous already), and the second is defeated by any different spacing.

        WHY AST IS THE HONEST FORM FOR THE SECOND HALF AND NOT A BEHAVIORAL TEST. "No host defines a
        second body" is a claim about the MODULE's structure, and there is no behavior to drive: the
        hosts already re-export the shared object, so `agy_runipd.extract_session_id(log)` returns the
        right answer whether or not a shadowed second definition also exists lower in the file. A
        comment cannot satisfy an `ast.FunctionDef` scan, so this is strictly stronger than the text
        it replaces, and it is the strongest available form for an absence-of-definition claim.
        (`test_no_module_in_the_package_re_forks_either_symbol` already scans the whole package this
        way; this test keeps the per-host statement because the DEAD LOCAL is the thing being
        prevented and the hosts are where it lived.)

        WHY THE FIRST HALF BECAME BEHAVIORAL RATHER THAN AST. That `fallback` is LOAD-BEARING is a
        claim about what the reader DOES, and it has a directly observable consequence: a log whose
        only id is unprefixed must still resolve. An AST check that the name is bound and read would
        pass on a body that assigned it and returned it from an unreachable branch, which is precisely
        the dead shape agy had.
        """
        # LIVE, proven by the observable consequence of the fallback existing at all: a log with no
        # `ses_`-prefixed value anywhere must STILL resolve, which only the fallback path can do.
        unprefixed_only = _log({"type": "x", "sessionID": "raw-provider-id"})
        self.assertEqual(
            runner_shared.extract_session_id(unprefixed_only),
            "raw-provider-id",
            "the shared reader's `fallback` is load-bearing: without it a log carrying only an "
            "unprefixed id resolves to None and the session cannot be resumed",
        )

        offenders = []
        for host_name, host in BOTH:
            tree = ast.parse(
                pathlib.Path(inspect.getfile(host)).read_text(encoding="utf-8")
            )
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "extract_session_id"
                ):
                    offenders.append(f"{host_name}:{node.lineno}")
        self.assertEqual(
            offenders,
            [],
            "a host DEFINES its own `extract_session_id` again, at "
            f"{offenders!r}. That is the fork this Set removed, and agy's copy is where the DEAD "
            "`fallback` local lived: initialized to None, returned at the end, and unreachable in "
            "that state because every assigning branch returned immediately. A second body is how "
            "the two readers came to disagree about return discipline in the first place. FIX: "
            "re-export `runner_shared.extract_session_id` rather than redefining it.",
        )


class BeginBaselineTests(unittest.TestCase):
    """`driver_begin` emits the isolated declaration if and only if `isolated=True`, on BOTH hosts."""

    def test_the_overlay_is_exactly_the_declaration_or_nothing(self):
        self.assertEqual(
            runner_shared.begin_baseline_env(True), {"AW_ISOLATED_BASELINE": "1"}
        )
        self.assertEqual(runner_shared.begin_baseline_env(False), {})

    def test_the_child_env_carries_the_declaration_only_when_isolated(self):
        """Built exactly as the shared launcher builds it, for each host's bound env builder."""
        for host_name, host in BOTH:
            for isolated in (True, False):
                with self.subTest(host=host_name, isolated=isolated):
                    env = {
                        **host.pinned_child_env(),
                        **runner_shared.begin_baseline_env(isolated),
                    }
                    if isolated:
                        self.assertEqual(env.get("AW_ISOLATED_BASELINE"), "1")
                    else:
                        self.assertNotIn(
                            "AW_ISOLATED_BASELINE",
                            env,
                            "a non-isolated turn must send NOTHING (not '0'), which is what keeps "
                            "that path byte-identical to its pre-change behavior",
                        )

    def test_the_non_isolated_child_env_is_byte_identical_to_the_bare_pin(self):
        """E-05's property, asserted permanently rather than only in the plan's evidence.

        Every existing test exercises the NON-isolated path, so a silent change there would be
        invisible. The key count is asserted too, or an empty-dict bug would pass this vacuously.
        """
        for host_name, host in BOTH:
            with self.subTest(host=host_name):
                bare = host.pinned_child_env()
                with_overlay = {**bare, **runner_shared.begin_baseline_env(False)}
                self.assertEqual(with_overlay, bare)
                self.assertGreater(len(bare), 1, "the pinned env must not be empty")

    #: (case, the run's `isolate_worktree` option, the `isolated` value the begin gate must receive,
    #: why this row exists)
    #:
    #: THE HOST IS THE OTHER COLUMN and is iterated inside, because the whole point of this Set is
    #: that the two hosts must not differ here; a per-host test body is how they came to differ.
    ISOLATE_DECLARATIONS = (
        (
            "an isolated run",
            True,
            True,
            "THE DECLARATION AGY SILENTLY LACKED, which is why this symbol was separated out. An "
            "isolated turn will execute in a fresh worktree, so begin must MEASURE that baseline; "
            "without the declaration it measures the main tree and the frozen base is wrong",
        ),
        (
            "a non-isolated run (--no-isolate-worktree)",
            False,
            False,
            "TRUTHFULNESS IN THE OTHER DIRECTION, and the row a naive fix breaks: passing "
            "`isolated=True` unconditionally would make both hosts' call shapes match and would pass "
            "the isolated row, while declaring a lane baseline for a turn that runs in the MAIN tree. "
            "A non-isolated turn must send NOTHING (not even `AW_ISOLATED_BASELINE=0`), which is what "
            "keeps that path byte-identical to its pre-change behavior",
        ),
    )

    def test_both_hosts_declare_the_run_s_real_isolation_to_the_begin_gate(self):
        """BEHAVIORAL replacement for a pin that searched `execute_item_core` for four literals.

        WHAT THE OLD FORM ASSERTED AND WHY IT WAS WEAK. It required the source to contain
        `if isolate:`, `driver_begin(repo, item["id6"], actor, isolated=True)`, the bare
        three-argument spelling, and the exact `isolate = state.get(...)` line. Four substring
        searches, so: a comment quoting any of them satisfies it (measured twice in this repository),
        renaming the local `isolate` to `isolated_run` breaks it while changing no behavior, and
        reformatting the call across lines breaks it too. Worst of all it could not detect the actual
        defect it was written for, because a body that computed `isolate` correctly and then passed
        `isolated=True` on BOTH branches still contains every one of those four strings.

        WHAT IS ASSERTED NOW: the run is really executed with the begin gate spied, and the `isolated`
        keyword the gate RECEIVES must equal the run's own `isolate_worktree` option. The gate is
        stubbed to REFUSE, which is deliberate - it makes the turn stop immediately after begin, so
        the test never spawns an agent, never allocates a lane, and observes exactly the one value
        under test.
        """
        failures = []
        for case, isolate_option, expected_isolated, why in self.ISOLATE_DECLARATIONS:
            for host_name, host in BOTH:
                recorded: list[dict[str, object]] = []

                def spy(repo, id6, actor, **kwargs):
                    recorded.append({"id6": id6, "kwargs": dict(kwargs)})
                    return (1, "begin refused by the declaration test")

                with _ExecuteItemHarness(
                    host, isolate_worktree=isolate_option
                ) as harness:
                    with mock.patch.object(host, "driver_begin", spy):
                        harness.run()

                problems = []
                if len(recorded) != 1:
                    problems.append(
                        f"the begin gate was called {len(recorded)} time(s), expected 1"
                    )
                else:
                    got = recorded[0]["kwargs"].get("isolated", False)
                    if got != expected_isolated:
                        problems.append(
                            f"begin received isolated={got!r}, expected {expected_isolated!r}"
                        )
                    # THE EFFECT, not only the argument, and this layer earned its place by MEASUREMENT.
                    # The non-isolated call site passes NO `isolated` keyword and so inherits the host
                    # WRAPPER's default, which means a defect can live entirely in that default with
                    # every call site still reading correctly. Verified by mutation: flipping
                    # `oc_runipd.driver_begin`'s `isolated` default to True declares a lane baseline
                    # for a MAIN-TREE turn, and an argument-only assertion passes it happily because
                    # the argument it inspects is the one the wrapper then overrides. Replaying the
                    # same (host, isolation) pair through the REAL shared launcher and reading
                    # `AW_ISOLATED_BASELINE` out of the child env catches it, because that variable is
                    # the observable the whole declaration exists to produce.
                    #
                    # (The deleted source-text pin was blind to this too: all four of its literals
                    # remain present verbatim under that mutation, since it read CALL SITES and the
                    # defect is in a DEFAULT.)
                    child_env = _child_env_for_begin(host, **recorded[0]["kwargs"])
                    flag = child_env.get("AW_ISOLATED_BASELINE")
                    expected_flag = "1" if expected_isolated else None
                    if flag != expected_flag:
                        problems.append(
                            f"the child env carried AW_ISOLATED_BASELINE={flag!r}, expected "
                            f"{expected_flag!r} (a non-isolated turn must send NOTHING, not '0')"
                        )
                    if "AW_PIN_KEEP_ROOT" not in child_env:
                        problems.append(
                            "the runner's import pin vanished from the child env; the baseline "
                            "declaration must be layered ON TOP of the pin, never instead of it"
                        )
                if harness.item.get("status") != "blocked":
                    problems.append(
                        "a refused begin must block the item (fail closed), but its status is "
                        f"{harness.item.get('status')!r}"
                    )
                if problems:
                    failures.append(
                        f"  {host_name} / {case}: {'; '.join(problems)}\n"
                        f"    this row exists because: {why}"
                    )

        total = len(self.ISOLATE_DECLARATIONS) * len(BOTH)
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {total} (host x isolation) combinations declared the wrong baseline "
            "to `aw ipd begin`. Read the grid, because the pattern names the defect: if BOTH "
            "non-isolated rows failed with `isolated=True`, somebody hardcoded the declaration to "
            "make the two hosts' call shapes match, which is exactly the untruthful fix this test "
            "exists to refuse; if only ONE HOST's rows failed, the hosts have diverged again, which "
            "is the whole reason this symbol was separated out of the Set. FIX: the value must be "
            "read from the run's own `options.isolate_worktree` in `execute_item_core` and forwarded, "
            "never defaulted to match a sibling.\n" + "\n".join(failures),
        )

    def test_begin_still_runs_before_the_lane_is_allocated_on_both_hosts(self):
        """Fail-closed ordering (authority BEFORE side effects) must survive the unification.

        This is why the isolated baseline is a frozen base COMMIT rather than a path: at begin time the
        lane does not exist yet. Previously asserted for oc only.

        MEASURED BY OBSERVED ORDER, NOT BY BYTE OFFSETS. The old form compared `src.index(...)` of two
        literals in the source text, which is a change-detector in the most literal sense: moving
        either statement, reformatting the call, or adding a COMMENT that mentions either spelling
        earlier in the module changes the answer without changing any behavior. It also could not see
        the ordering that matters at RUNTIME, since a source-order check says nothing about which call
        actually happens first under a branch.

        Now both calls are spied and their ORDER OF INVOCATION is asserted, plus the load-bearing
        consequence: when begin REFUSES, the lane must never be allocated at all.
        """
        failures = []
        for host_name, host in BOTH:
            order: list[str] = []

            def spy_begin(repo, id6, actor, **kwargs):
                order.append("begin")
                return (0, "ok")

            def spy_allocate(repo, id6, *a, **k):
                order.append("allocate")
                raise AssertionError(
                    "the lane allocator is stubbed to raise: this test asserts ORDER and must not "
                    "create a real worktree"
                )

            with _ExecuteItemHarness(host, isolate_worktree=True) as harness:
                with (
                    mock.patch.object(host, "driver_begin", spy_begin),
                    mock.patch.object(
                        host, "allocate_isolation_worktree", spy_allocate, create=True
                    ),
                    mock.patch.object(
                        runner_shared, "allocate_isolation_worktree", spy_allocate
                    ),
                ):
                    harness.run()

            if order[:2] != ["begin", "allocate"]:
                failures.append(
                    f"  {host_name}: observed call order {order!r}, expected begin before allocate"
                )

            # ...and the consequence that makes the ordering load-bearing: a REFUSED begin must leave
            # no lane behind at all.
            refused_order: list[str] = []

            def refuse_begin(repo, id6, actor, **kwargs):
                refused_order.append("begin")
                return (1, "begin refused")

            def never_allocate(repo, id6, *a, **k):
                refused_order.append("allocate")
                raise AssertionError("allocated a lane after begin REFUSED")

            with _ExecuteItemHarness(host, isolate_worktree=True) as harness:
                with (
                    mock.patch.object(host, "driver_begin", refuse_begin),
                    mock.patch.object(
                        host, "allocate_isolation_worktree", never_allocate, create=True
                    ),
                    mock.patch.object(
                        runner_shared, "allocate_isolation_worktree", never_allocate
                    ),
                ):
                    harness.run()
            if refused_order != ["begin"]:
                failures.append(
                    f"  {host_name}: after a REFUSED begin the observed calls were "
                    f"{refused_order!r}, expected begin only"
                )

        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(BOTH)} hosts broke the fail-closed ordering. AUTHORITY MUST "
            "PRECEDE SIDE EFFECTS: `aw ipd begin` writes the receipt that grants execution authority, "
            "and the lane is a side effect, so allocating first means a refused item can still leave a "
            "worktree and a branch behind for a human to clean up. It is also why the isolated "
            "baseline is a frozen base COMMIT rather than a path: at begin time the lane does not "
            "exist yet.\n" + "\n".join(failures),
        )


class NonVacuityControlTests(unittest.TestCase):
    """Property 5: remove each capability from a REPLICA and show the matching assertion FAILS.

    A capability test that would also pass against a reader LACKING the capability proves nothing. Each
    control below is a deliberately crippled variant of the shared body, run over the same fixtures.
    `ControlFidelityTests` holds the replicas to the real body, so a control cannot drift into testing
    a strawman that stopped resembling the code.
    """

    @staticmethod
    def _reader(
        keys: tuple[str, ...],
        nests: tuple[str, ...],
        *,
        prefer_ses: bool,
    ) -> Callable[[Path], str | None]:
        def read(log_path: Path) -> str | None:
            if not log_path.exists():
                return None
            fallback: str | None = None
            with log_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    scopes = [event]
                    for nest in nests:
                        nested = event.get(nest)
                        if isinstance(nested, dict):
                            scopes.append(nested)
                    for scope in scopes:
                        for key in keys:
                            value = scope.get(key)
                            if not isinstance(value, str) or not value.strip():
                                continue
                            if prefer_ses and value.startswith(_SES):
                                return value
                            if not prefer_ses:
                                return value
                            if fallback is None:
                                fallback = value
            return fallback

        return read

    #: (control, the keys the crippled replica reads, the nestings it reads, whether it prefers `ses_`,
    #: the log events, what the CRIPPLED reader returns, what the REAL reader must return, why this
    #: control exists)
    #:
    #: Four controls, one body: each removes exactly ONE capability and shows the corresponding answer
    #: changes. Which capability is removed is DATA (a key tuple, a nesting tuple, a flag), which is
    #: precisely the "differ only in data" shape a table is for; the four had identical structure.
    CONTROLS = (
        (
            "(a) drop `conversation_id` from the key list",
            ("sessionID", "sessionId", "session_id"),
            runner_shared._SESSION_ID_NESTS,
            True,
            ({"type": "result", "conversation_id": "conv-flat-1"},),
            None,
            "conv-flat-1",
            "this is oc's pre-union key list exactly, so the control demonstrates the F-1 claim "
            "directly: adopting oc's reader outright leaves agy unable to find its own session id",
        ),
        (
            "(b) drop the `ses_` preference (first-hit discipline)",
            runner_shared._SESSION_ID_KEYS,
            runner_shared._SESSION_ID_NESTS,
            False,
            ({"sessionID": "raw-provider-id"}, {"sessionID": _SES + "real1"}),
            "raw-provider-id",
            _SES + "real1",
            "agy's discipline, and the ONE shape where the two readers give different answers, which is "
            "why precedence had to be DECIDED rather than unioned (decision `06-ct4w0a-D1`). Note the "
            "crippled answer is a WRONG ID rather than None: this capability fails silently",
        ),
        (
            "(c) drop the `result` nesting",
            runner_shared._SESSION_ID_KEYS,
            ("init",),
            True,
            ({"type": "result", "result": {"conversation_id": "conv-nested-1"}},),
            None,
            "conv-nested-1",
            "the `result` nesting carries agy's REAL OBSERVED shape, so losing it loses real logs and "
            "not a hypothetical one",
        ),
        (
            "(d) drop the `init` nesting",
            runner_shared._SESSION_ID_KEYS,
            ("result",),
            True,
            ({"type": "init", "init": {"conversation_id": "conv-init-1"}},),
            None,
            "conv-init-1",
            "the `init` path is UNOBSERVED in the census and retained on purpose, which makes its "
            "control MORE valuable rather than less: an untested retained branch is the one most "
            "likely to be 'simplified' away by someone who cannot see what it is for",
        ),
    )

    def test_removing_any_one_capability_changes_the_answer(self):
        failures = []
        for (
            control,
            keys,
            nests,
            prefer_ses,
            events,
            crippled_expected,
            real_expected,
            why,
        ) in self.CONTROLS:
            crippled = self._reader(keys, nests, prefer_ses=prefer_ses)
            log = _log(*events)
            crippled_got = crippled(log)
            real_got = runner_shared.extract_session_id(log)
            problems = []
            if crippled_got != crippled_expected:
                problems.append(
                    f"the CRIPPLED replica returned {crippled_got!r}, expected "
                    f"{crippled_expected!r} - so it is not really crippled and this control proves "
                    "nothing"
                )
            if real_got != real_expected:
                problems.append(
                    f"the REAL reader returned {real_got!r}, expected {real_expected!r} - the "
                    "capability itself is broken"
                )
            if problems:
                failures.append(
                    f"  {control}: {'; '.join(problems)}\n    this control exists because: {why}"
                )
        self.assertEqual(
            failures,
            [],
            f"{len(failures)} of {len(self.CONTROLS)} non-vacuity controls failed. WHICH HALF FAILED "
            "DECIDES WHERE TO LOOK: a CRIPPLED-replica mismatch means the control is no longer a "
            "control (the replica drifted, or the capability it removes is no longer load-bearing), so "
            "the corresponding capability test in this file is now DECORATION and must be re-derived; "
            "a REAL-reader mismatch means the union actually lost that capability, which is the defect "
            "the controls exist to make visible. `ControlFidelityTests` holds the replicas to the real "
            "body, so check it too before concluding the code is at fault.\n"
            + "\n".join(failures),
        )


class ControlFidelityTests(unittest.TestCase):
    """Guard the controls: a replica that stopped resembling the real body proves nothing.

    The controls above re-implement the shared reader in order to cripple it. That is only legitimate
    while the replica matches the real thing on the UNCRIPPLED inputs, so this class asserts the
    full-capability replica agrees with the real function across every shape the suite uses.
    """

    def test_the_uncrippled_replica_agrees_with_the_real_reader(self):
        replica = NonVacuityControlTests._reader(
            runner_shared._SESSION_ID_KEYS,
            runner_shared._SESSION_ID_NESTS,
            prefer_ses=True,
        )
        fixtures = [
            _log({"sessionID": _SES + "a"}),
            _log({"conversation_id": "conv-b"}),
            _log({"result": {"conversation_id": "conv-c"}}),
            _log({"init": {"session_id": "sn-d"}}),
            _log({"sessionID": "raw-e"}, {"sessionID": _SES + "f"}),
            _log({"conversation_id": "conv-early"}, {"sessionID": _SES + "late"}),
            _log({"type": "text"}),
        ]
        for log in fixtures:
            with self.subTest(log=log.parent.name):
                self.assertEqual(
                    replica(log),
                    runner_shared.extract_session_id(log),
                    "the control replica has drifted from the real body; the controls above are no "
                    "longer evidence about the real reader",
                )

    def test_the_pre_union_oc_replica_matches_the_shipped_body_it_reconstructs(self):
        """The oc replica used by `AgyWireFormatTests` must behave like the real pre-union oc reader.

        Verified against the SHIPPED body at the execution HEAD rather than against memory: if that
        commit is unreachable (a shallow clone) this skips, because the claim is historical.
        """
        import subprocess as sp

        head = "1171f7b22da8065390f190458070a0ad842c2376"
        repo_root = Path(__file__).resolve().parents[1]
        proc = sp.run(
            ["git", "show", f"{head}:agent_workflows/oc_runipd.py"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,  # a missing commit is handled by the skip below, not by an exception
            stdin=sp.DEVNULL,
        )
        if proc.returncode != 0:
            self.skipTest(f"execution HEAD {head[:8]} not reachable in this clone")
        # `exec` on TWO hand-picked AST nodes (one assignment, one function def) taken from a FIXED
        # commit's `oc_runipd.py`, into a private namespace. Deliberate and narrow: the point is to run
        # the SHIPPED pre-union body rather than a hand-copy of it, because a hand-copy is exactly what
        # `_oc_pre_union_reader` already is and this test exists to verify THAT copy is faithful. Nothing
        # here reads untrusted input: the source comes from this repository's own git object store at a
        # pinned SHA. `# noqa: S102` is scoped to the two exec lines below, not to the file.
        namespace: dict[str, object] = {"json": json, "Path": Path}
        tree = ast.parse(proc.stdout)
        wanted = {"extract_session_id"}
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_SESSION_ID_KEYS"
                for t in node.targets
            ):
                exec(compile(ast.Module([node], []), "<pre>", "exec"), namespace)  # noqa: S102
            if isinstance(node, ast.FunctionDef) and node.name in wanted:
                exec(compile(ast.Module([node], []), "<pre>", "exec"), namespace)  # noqa: S102
        real_pre_union = namespace.get("extract_session_id")
        if not callable(
            real_pre_union
        ):  # pragma: no cover - a load failure, not an assertion
            self.fail("could not load the pre-union oc reader from git history")
        self.assertEqual(
            namespace.get("_SESSION_ID_KEYS"),
            _OC_PRE_UNION_KEYS,
            "this file's reconstruction of oc's pre-union key list is wrong",
        )
        for log in (
            _log({"conversation_id": "conv-x"}),
            _log({"result": {"conversation_id": "conv-y"}}),
            _log({"sessionID": _SES + "z"}),
            _log({"sessionID": "raw"}, {"sessionID": _SES + "w"}),
        ):
            with self.subTest(log=log.parent.name):
                self.assertEqual(
                    _oc_pre_union_reader(log),
                    real_pre_union(log),
                    "the reconstructed oc reader disagrees with the body it claims to reconstruct",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
