#!/usr/bin/env python3
"""rununify Order 11 (`3dki3o`) E-02/E-03: CHARACTERIZE `main` on BOTH hosts, as behavior.

WHY THIS FILE EXISTS, and why every assertion here is on an OBSERVABLE result.

The parent Set forbids a child reconciling a symbol the characterization baseline has not pinned,
and `main` is the process entry point both runners are reached through. It is also, measured, the
most heavily SOURCE-pinned of the five large functions this Set splits: four existing pins read
`inspect.getsource(<host>.main)` and assert substrings or AST shapes of its body (inventoried in
`tests/test_rununify_main.py`). A source pin has two failure modes this file is the answer to. It
dies when the body MOVES even though behavior is unchanged, and it can be satisfied by a COMMENT
even when behavior is broken. So nothing below reads source text; each test drives the host's real
`main` and asserts the return code, the streams, and the on-disk state.

E-02 IS DELIBERATELY NOT ALLOWED TO ADD A FIFTH SOURCE PIN. Plan `3dki3o` E-02 states it directly:
"adding a fifth source pin would hand the next refactor a problem this plan is documenting."
`tests/test_rununify_main.py::TheSourcePinsAreStillPresent` asserts the count did not grow, so this
file cannot quietly acquire one.

AGY IS PRIORITIZED DELIBERATELY, per the plan's E-02. The parent Set measured the two hosts' suites
as asymmetric, so an agy-side regression can hide behind a green run. Every test here runs against
BOTH hosts through `subTest`, and each of the five exit codes is asserted on both.

WHAT IS PINNED HERE, branch by branch, because "characterize `main`" is otherwise unfalsifiable:

* THE FIVE EXIT CODES `main` actually returns: 0 (a completed command), 0 (the `print_help` path
  when no subcommand resolves), 2 (an invalid invocation translated from `DriverError`), 130
  (SIGINT via the `KeyboardInterrupt` funnel), and 143 (SIGTERM through the same funnel, which the
  handler marks by putting `SIGTERM` in the exception message).
* THE IMPLICIT-START SHIM, including the case it exists for: a bare `stop <run-id>` must NOT be
  rewritten to `start stop <run-id>`. That rewrite would launch a run whose selector is the literal
  string `stop`, which is the exact opposite of the operator's intent.
* THE FOUR `except` ARMS IN ORDER. The ordering is load-bearing rather than stylistic:
  `EmptyStatusSelection` is a SUBCLASS of `DriverError`, so an arm ordered after it would never
  run and an empty review sweep would exit 2 instead of 0.
* THE `--json` STATUS BRANCH suppressing the human pointer line, so machine-readable output stays
  parseable.

E-03'S EXIT-CODE CONTRACT lives in `TheEmptySweepExitCodeContract` at the bottom. It pins the
behavior (exit 0, the plain sentence, no run directory) AND the structural fact that makes the
hazard possible in the first place. Plan `3dki3o` F-7 predicted that a shared core hardcoding one
host's `EmptyStatusSelection` would silently return 2 on the other host. AT THIS HEAD THAT HAZARD
IS ALREADY GONE, because sibling `i3d6ml` lifted the class into `runner_shared`, and both hosts now
resolve the SAME object. The structural test asserts exactly that, so the day someone re-forks the
class into two per-host definitions this suite fails LOUDLY instead of the empty sweep quietly
starting to exit 2.
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from agent_workflows import agy_runipd, oc_runipd, runner_shared

HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

#: The per-host stderr prefix `main` puts on a translated `DriverError`. It is NOT the parser's
#: `prog` (that is a coincidence of spelling) and nothing else in `tests/` asserts it, which is why
#: it is pinned here: it is the one host-specific string in the error-translation tail, so a split
#: that dropped it would go unnoticed.
ERROR_PREFIX = {"oc_runipd": "runipd:", "agy_runipd": "runagy:"}


class MainCase(unittest.TestCase):
    """Drive a host's real `main` in-process and capture what an operator would see."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    # ---- fixtures ------------------------------------------------------------------------
    PLAN = """# IPD: characterization probe

- Date: 2026-09-17
- Kind: child
- Status: {status}
- Set: mainchar
- Order: 01
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-17 reviewed (test): APPROVE; no blocking findings.
"""

    def make_repo(
        self, *, id6: str = "mch001", status: str = "approved"
    ) -> pathlib.Path:
        """A minimal git repo with one plan, enough for `initialize_run` to resolve a selector.

        The directory name carries a counter because every test here builds one repo PER HOST, and a
        shared name would collide on the second `subTest` rather than isolating the two hosts.
        """
        self._repo_seq = getattr(self, "_repo_seq", 0) + 1
        repo = self.root / f"repo-{self._repo_seq:02d}-{id6}-{status}"
        repo.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)
        (pending / f"20260917-mainchar-01-{id6}-probe.ipd.md").write_text(
            self.PLAN.format(id6=id6, status=status), encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def call_main(self, mod, argv: list[str]) -> tuple[int, str, str]:
        """Return `(rc, stdout, stderr)` from a real in-process `main`."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = mod.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def prepared_run(
        self, mod, repo: pathlib.Path, id6: str = "mch001"
    ) -> pathlib.Path:
        """`start --prepare-only`, which creates the run dir and returns 0 without launching."""
        rc, out, err = self.call_main(
            mod, ["start", id6, "--repo", str(repo), "--prepare-only"]
        )
        self.assertEqual(rc, 0, f"prepare failed: {err or out}")
        runs = repo / ".aw" / "records" / "runs"
        dirs = sorted(p for p in runs.iterdir() if p.is_dir())
        self.assertEqual(len(dirs), 1, dirs)
        return dirs[0]


class TheFiveExitCodes(MainCase):
    """`main` owns the process exit status, so each code it can return is pinned on BOTH hosts.

    Spec `25kzda` 5.6 records that "the drivers themselves return only `0`/`2`/`130`/`143` today",
    citing `oc_runipd.main`. The fifth distinct RETURN is also 0, from `parser.print_help()` when no
    subcommand resolves; it is pinned separately because it is a different branch reaching the same
    code, and a split that lost it would turn a bare invocation into a crash.
    """

    def test_exit_0_a_prepare_only_start_completes(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod, ["start", "mch001", "--repo", str(repo), "--prepare-only"]
                )
                self.assertEqual(rc, 0, err)
                self.assertIn("Run ID:", out)
                self.assertIn("State directory:", out)

    def test_exit_0_no_subcommand_prints_help_rather_than_failing(self):
        """`main` returns 0 after `print_help()`; it must not raise and must not exit 2.

        REACHED THROUGH A NAMESPACE WHOSE `command` IS UNSET, which is the only way in: the shim
        rewrites a bare selector to `start`, so no command line reaches this branch on the shipped
        parser. It is pinned anyway because `main` still contains the branch, a caller constructing
        its own namespace can reach it, and the alternative to returning 0 here is an
        `AttributeError` on `args.command` further down.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                parser = mod.build_parser()
                ns = parser.parse_args(["status", "run-x", "--repo", str(self.root)])
                ns.command = None
                with patch.object(
                    mod, "build_parser", return_value=parser
                ), patch.object(parser, "parse_args", return_value=ns):
                    rc, out, err = self.call_main(mod, ["status", "run-x"])
                self.assertEqual(rc, 0, err)
                self.assertIn("usage", out.lower())

    def test_exit_2_an_unresolvable_selector_is_translated_not_raised(self):
        """A `DriverError` becomes the host-prefixed stderr line plus exit 2, never a traceback."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod, ["start", "nosuch", "--repo", str(repo), "--prepare-only"]
                )
                self.assertEqual(rc, 2, out)
                self.assertTrue(
                    err.startswith(ERROR_PREFIX[name]),
                    f"{name}: expected the {ERROR_PREFIX[name]!r} prefix, got {err!r}",
                )

    def test_exit_130_sigint_funnels_through_keyboardinterrupt(self):
        """CPython raises `KeyboardInterrupt` for SIGINT; `main` must translate it to 130."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod, "run_queue", side_effect=KeyboardInterrupt("Ctrl-C")
                ), patch.object(mod, "install_stop_triggers"):
                    rc, out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 130, err)
                self.assertIn("Interrupted", err)
                self.assertIn("durable run state was preserved", err)

    def test_exit_143_sigterm_is_marked_by_the_message_not_a_second_handler(self):
        """The SIGTERM handler raises `KeyboardInterrupt("...SIGTERM...")`; the MESSAGE selects 143.

        This is the mechanism, and it is easy to break by accident: both signals arrive at the SAME
        `except KeyboardInterrupt` arm, and the only thing distinguishing them is `"SIGTERM" in
        str(exc)`. A split that reconstructed the exception, or normalized its message, would return
        130 for a SIGTERM and the operator would misread a clean termination as an interrupt.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=KeyboardInterrupt("Terminated by SIGTERM"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 143, err)
                self.assertIn("Terminated by SIGTERM", err)

    def test_the_just_terminate_message_replaces_the_preserved_state_sentence(self):
        """The `just-terminate-no-cleanup` escape prints a DIFFERENT sentence, still exiting 130."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=KeyboardInterrupt("just-terminate-no-cleanup"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, _out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 130, err)
                self.assertIn("Terminated without clean up", err)
                self.assertNotIn("durable run state was preserved", err)


class TheImplicitStartShim(MainCase):
    """A first token that is not a subcommand gets `start` prepended; the exceptions are pinned.

    The shim's set is required to stay an INLINE LITERAL in each host's own source: two tests in
    `tests/test_runner_stop_triggers.py` regex `subcommands = \\{(.*?)\\}` out of BOTH files and
    require the sets to be identical, and each runner carries a KEEP-THIS-INLINE comment recording
    that hoisting it to a module constant makes the guard silently unmatchable. This class pins the
    BEHAVIOR that guard protects, so the property survives even if the guard's form changes.
    """

    def test_a_bare_selector_is_treated_as_start(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod, ["mch001", "--repo", str(repo), "--prepare-only"]
                )
                self.assertEqual(rc, 0, err)
                self.assertIn("Run ID:", out)

    def test_a_bare_stop_is_NOT_rewritten_into_start_stop(self):
        """THE CASE THE SHIM'S SET EXISTS FOR, asserted as behavior on both hosts.

        If `stop` were missing from the set, this invocation would become
        `start stop <run-id>`, i.e. it would LAUNCH a run whose selector is the literal `stop`. So
        the discriminator is not the exit code but the absence of any run: a rewritten `stop` builds
        a run directory, and a correctly routed one never does.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                rc, out, err = self.call_main(
                    mod,
                    [
                        "stop",
                        "run-20260917T000000Z-0001",
                        "--repo",
                        str(repo),
                        "--now",
                    ],
                )
                self.assertNotEqual(
                    rc, 0, "a stop naming no live run must not report success"
                )
                self.assertFalse(
                    (repo / ".aw" / "records" / "runs").exists(),
                    f"{name}: `stop` was rewritten to `start stop`, which launched a run",
                )
                self.assertNotIn("Run ID:", out)

    def test_each_real_subcommand_routes_without_a_rewrite(self):
        """`status`/`report`/`resume`/`stop`/`start` are all in the set on both hosts."""
        for name, mod in HOSTS:
            for verb in ("start", "resume", "status", "report", "stop"):
                with self.subTest(driver=name, verb=verb):
                    parser = mod.build_parser()
                    # A parse that RESOLVES the verb proves the verb is a real subcommand, which is
                    # the precondition for the shim leaving it alone.
                    self.assertIn(verb, parser.format_help())


class TheFourExceptArmsInOrder(MainCase):
    """The `except` ladder is `KeyboardInterrupt`, `EmptyStatusSelection`, `DriverError`, `Exception`.

    ORDER IS LOAD-BEARING, not stylistic. `EmptyStatusSelection` is a SUBCLASS of `DriverError`, so
    if the generic arm came first the empty-review sweep would exit 2 instead of 0 and violate spec
    `25kzda` 2.4a property 3. Each arm is proven reachable BY BEHAVIOR here rather than by reading
    the source, so the property survives a relocation of the body.
    """

    def test_the_generic_exception_arm_reraises_after_reporting(self):
        """An unexpected error must print the host-prefixed line AND re-raise, never return 0.

        Swallowing it would be the worst outcome: a crashed run reported as a clean exit.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                out, err = io.StringIO(), io.StringIO()
                with patch.object(
                    mod, "run_queue", side_effect=ZeroDivisionError("boom")
                ), patch.object(mod, "install_stop_triggers"):
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(
                        err
                    ):
                        with self.assertRaises(ZeroDivisionError):
                            mod.main(["resume", run_dir.name, "--repo", str(repo)])
                self.assertIn(
                    f"{ERROR_PREFIX[name]} unexpected failure:", err.getvalue()
                )

    def test_a_driver_error_from_the_queue_returns_2_and_is_not_reraised(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=runner_shared.DriverError("queue said no"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, _out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(rc, 2)
                self.assertIn("queue said no", err)

    def test_the_empty_status_arm_precedes_the_driver_error_arm(self):
        """Proven BY BEHAVIOR: raise `EmptyStatusSelection` and require 0, not 2.

        Because the class is a `DriverError` subclass, getting 0 here is only possible if its arm is
        ordered FIRST. That makes this a behavioral test of an ordering property, which is what the
        maintainer's 2026-09-16 ruling asks for where a source pin would otherwise be used.
        """
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                with patch.object(
                    mod,
                    "run_queue",
                    side_effect=runner_shared.EmptyStatusSelection("empty"),
                ), patch.object(mod, "install_stop_triggers"):
                    rc, out, err = self.call_main(
                        mod, ["resume", run_dir.name, "--repo", str(repo)]
                    )
                self.assertEqual(
                    rc,
                    0,
                    f"{name}: EmptyStatusSelection fell through to the DriverError arm "
                    f"(stderr={err!r})",
                )
                self.assertIn("Nothing awaiting review", out)


class TheJsonStatusBranch(MainCase):
    """`status --json` must emit parseable JSON and SUPPRESS the human pointer sentence.

    One existing pin (`tests/test_runner_backlog_close.py:923`) asserts this by walking the AST of
    `main`'s source for an `if` whose body contains `json.dumps` and not `render_runs_pointer`. This
    asserts the same contract as OUTPUT, which is both stronger (a comment cannot satisfy it) and
    survives the body moving.
    """

    def test_json_status_is_parseable_and_carries_no_pointer_line(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, out, err = self.call_main(
                    mod, ["status", run_dir.name, "--repo", str(repo), "--json"]
                )
                self.assertEqual(rc, 0, err)
                parsed = json.loads(out)  # fails loudly if a human line leaked in
                self.assertIn("queue", parsed)
                self.assertNotIn("Run `aw runs", out)

    def test_plain_status_DOES_carry_the_pointer_line(self):
        """The inverse half: without `--json` the pointer is expected, so the suppression above is
        a real branch rather than a line nobody prints."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, out, err = self.call_main(
                    mod, ["status", run_dir.name, "--repo", str(repo)]
                )
                self.assertEqual(rc, 0, err)
                self.assertIn("Run `aw runs", out)


class TheReportBranch(MainCase):
    """`report` writes the file and prints its path, on both hosts."""

    def test_report_writes_the_execution_report_and_prints_the_path(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, out, err = self.call_main(
                    mod, ["report", run_dir.name, "--repo", str(repo)]
                )
                self.assertEqual(rc, 0, err)
                report = run_dir / "execution-report.md"
                self.assertTrue(report.is_file(), f"{name}: no report written")
                self.assertIn(str(report), out)


class TheResumeFreezeContract(MainCase):
    """Resume REFUSES a frozen flag and APPLIES a passed policy flag, on both hosts.

    A source pin (`tests/test_run_flag_surface.py:837`) requires `main`'s source to mention
    `refuse_frozen_flags_on_resume` and `apply_run_policy_flags_on_resume`. These two tests assert
    what those calls DO, so the contract is pinned to behavior as well as to text.
    """

    def test_retry_budget_is_refused_on_resume(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                rc, _out, err = self.call_main(
                    mod,
                    [
                        "resume",
                        run_dir.name,
                        "--repo",
                        str(repo),
                        "--retry-budget",
                        "9",
                    ],
                )
                self.assertEqual(rc, 2, "a frozen flag must be refused, not applied")
                self.assertIn("retry-budget", err.replace("_", "-"))

    def test_a_passed_policy_flag_is_applied_to_the_frozen_state(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                repo = self.make_repo(id6="mch001")
                run_dir = self.prepared_run(mod, repo)
                before = runner_shared.load_state(run_dir)["options"].get("unattended")
                with patch.object(mod, "run_queue", return_value=0), patch.object(
                    mod, "install_stop_triggers"
                ):
                    rc, _out, err = self.call_main(
                        mod,
                        ["resume", run_dir.name, "--repo", str(repo), "--unattended"],
                    )
                self.assertEqual(rc, 0, err)
                after = runner_shared.load_state(run_dir)["options"].get("unattended")
                self.assertTrue(
                    after, f"{name}: --unattended was not applied on resume"
                )
                self.assertNotEqual(before, after)


class OcOnlyProfileGrammar(MainCase):
    """The `as <profile>` clause is OC-ONLY, and its absence on agy is pinned as a fact.

    This is the measurement that decides how much of `main` can be shared at all: 19 of the 46
    differing AST-normalized lines are this grammar, and agy has NO profile subsystem to support it.
    Pinning it here means a later split cannot quietly grow the clause onto agy (a FEATURE the
    parent Set forbids a child from adding) or quietly drop it from oc.
    """

    def test_oc_refuses_a_profile_named_on_a_non_start_command(self):
        repo = self.make_repo(id6="mch001")
        run_dir = self.prepared_run(oc_runipd, repo)
        parser = oc_runipd.build_parser()
        ns = parser.parse_args(["resume", run_dir.name, "--repo", str(repo)])
        setattr(ns, "profile", "gem")
        with patch.object(oc_runipd, "build_parser", return_value=parser), patch.object(
            parser, "parse_args", return_value=ns
        ):
            rc, _out, err = self.call_main(
                oc_runipd, ["resume", run_dir.name, "--repo", str(repo)]
            )
        self.assertEqual(rc, 2)
        self.assertIn("cannot be named on", err)
        self.assertIn("frozen when the run is created", err)

    def test_agy_has_no_profile_clause_extractor_at_all(self):
        """Not a style difference: the whole subsystem is absent, so there is nothing to unify."""
        self.assertTrue(hasattr(oc_runipd, "extract_profile_clause"))
        self.assertFalse(hasattr(agy_runipd, "extract_profile_clause"))
        self.assertTrue(hasattr(oc_runipd, "ProfileClauseError"))
        self.assertFalse(hasattr(agy_runipd, "ProfileClauseError"))

    def test_oc_refuses_verify_with_on_resume_and_agy_never_offered_it(self):
        repo = self.make_repo(id6="mch001")
        run_dir = self.prepared_run(oc_runipd, repo)
        rc, _out, err = self.call_main(
            oc_runipd,
            ["resume", run_dir.name, "--repo", str(repo), "--verify-with", "opus"],
        )
        self.assertEqual(rc, 2)
        self.assertIn("cannot be changed on resume", err)
        self.assertNotIn("--verify-with", agy_runipd.build_parser().format_help())


class AgyOnlyResumeFlag(MainCase):
    """`--agy-executable` is agy's own resume-time state write, with no oc counterpart."""

    def test_agy_executable_is_written_to_the_frozen_options_on_resume(self):
        repo = self.make_repo(id6="mch001")
        run_dir = self.prepared_run(agy_runipd, repo)
        with patch.object(agy_runipd, "run_queue", return_value=0), patch.object(
            agy_runipd, "install_stop_triggers"
        ):
            rc, _out, err = self.call_main(
                agy_runipd,
                [
                    "resume",
                    run_dir.name,
                    "--repo",
                    str(repo),
                    "--agy-executable",
                    "/usr/bin/true",
                ],
            )
        self.assertEqual(rc, 0, err)
        state = runner_shared.load_state(run_dir)
        self.assertEqual(state["options"]["agy_executable"], "/usr/bin/true")
        self.assertNotIn("--agy-executable", oc_runipd.build_parser().format_help())


class OcOnlyLaunchIdentity(MainCase):
    """`print_launch_identity` runs on oc's `--prepare-only` and `status`; agy has no such symbol."""

    def test_oc_prints_the_launch_identity_and_agy_has_none_to_print(self):
        self.assertTrue(hasattr(oc_runipd, "print_launch_identity"))
        self.assertFalse(hasattr(agy_runipd, "print_launch_identity"))
        repo = self.make_repo(id6="mch001")
        with patch.object(oc_runipd, "print_launch_identity") as spy:
            rc, _out, err = self.call_main(
                oc_runipd, ["start", "mch001", "--repo", str(repo), "--prepare-only"]
            )
        self.assertEqual(rc, 0, err)
        self.assertEqual(
            spy.call_count,
            1,
            "oc's --prepare-only must report what it will launch with",
        )


# ==========================================================================================
# E-03: THE EXIT-CODE CONTRACT PLAN `3dki3o` F-7 SHOWS IS SILENTLY BREAKABLE
# ==========================================================================================


class TheEmptySweepExitCodeContract(unittest.TestCase):
    """E-03: an empty review sweep exits 0, and the class that makes that possible is ONE object.

    THE HAZARD, as plan `3dki3o` F-7 proved by construction at review time: if the two hosts define
    SEPARATE `EmptyStatusSelection` classes (siblings under the shared `DriverError`, neither a
    subclass of the other), then a SHARED core writing `except EmptyStatusSelection` resolves ONE of
    them, and the other host's instance falls through to `except DriverError` and returns 2 where
    spec `25kzda` 2.4a property 3 requires 0. Its failure mode is what makes it worth a test of its
    own: nothing crashes, the run simply reports failure on a healthy repository.

    WHAT CHANGED SINCE THE PLAN WAS WRITTEN, and it is the good news: sibling `i3d6ml` (commit
    `d26c1061`) lifted `EmptyStatusSelection` into `runner_shared`, so at this HEAD both hosts
    resolve the SAME class and the hazard is structurally gone. The plan's own Goal table lists the
    symbol as "STILL DEFINED TWICE"; that is now stale, which
    `tests/test_rununify_main.py` records as a class change.

    So this class pins BOTH halves: the behavior (0, the plain sentence, no run directory) and the
    structural precondition (one class, shared, a `DriverError` subclass). A future re-fork into two
    per-host classes fails HERE, loudly, instead of turning exit 0 into exit 2 in production.
    """

    PLAN_TO_REVIEW = """# IPD: nothing to review

- Date: 2026-09-17
- Kind: child
- Status: executed
- Set: emptysweep
- Order: 01
- Highest E allocated: 01
- Author: test
- Id: esw001

## Workflow history
- 2026-09-17 executed (test): done.
"""

    def make_repo_with_nothing_to_review(self, root: pathlib.Path) -> pathlib.Path:
        repo = root / "repo"
        repo.mkdir(parents=True)
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=repo, check=True)
        (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
        executed = repo / ".aw" / "records" / "plans" / "executed"
        executed.mkdir(parents=True)
        (executed / "20260917-emptysweep-01-esw001-done.ipd.md").write_text(
            self.PLAN_TO_REVIEW, encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo

    def test_an_empty_review_sweep_exits_zero_on_both_hosts(self):
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo_with_nothing_to_review(pathlib.Path(td))
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(
                        err
                    ):
                        rc = mod.main(
                            [
                                "start",
                                "reviews",
                                "--repo",
                                str(repo),
                                "--prepare-only",
                            ]
                        )
                    self.assertEqual(
                        rc,
                        0,
                        f"{name}: an empty review sweep is the HEALTHY state and must exit 0 "
                        f"(spec 25kzda 2.4a property 3); stderr={err.getvalue()!r}",
                    )
                    self.assertIn("Nothing awaiting review", out.getvalue())
                    self.assertFalse(
                        (repo / ".aw" / "records" / "runs").exists(),
                        f"{name}: an empty sweep must create no run directory",
                    )

    def test_empty_status_selection_is_ONE_shared_class_not_two_per_host(self):
        """THE STRUCTURAL HALF, which no other test in the repository asserts.

        If this fails because the classes were re-forked, the empty-sweep behavior above is one
        careless `except` away from returning 2 in a shared core. See F-7.
        """
        self.assertIs(
            oc_runipd.EmptyStatusSelection,
            agy_runipd.EmptyStatusSelection,
            "the two hosts' EmptyStatusSelection must be the SAME object; two sibling classes "
            "let a shared `except` arm miss one host and return 2 instead of 0 (F-7)",
        )
        self.assertIs(
            oc_runipd.EmptyStatusSelection,
            runner_shared.EmptyStatusSelection,
            "the shared class must be the one `runner_shared` owns, so a shared core's `except` "
            "arm resolves the same object both hosts raise",
        )

    def test_the_shared_class_is_still_a_driver_error_subclass(self):
        """The subclass relation is WHY the arm ordering matters; losing it changes the ladder."""
        self.assertTrue(
            issubclass(runner_shared.EmptyStatusSelection, runner_shared.DriverError)
        )
        self.assertIsNot(runner_shared.EmptyStatusSelection, runner_shared.DriverError)

    def test_a_plain_driver_error_still_exits_2_so_the_zero_is_not_blanket(self):
        """NON-VACUITY of the contract above: only the EMPTY sweep gets 0, not every failure."""
        for name, mod in HOSTS:
            with self.subTest(driver=name):
                with tempfile.TemporaryDirectory() as td:
                    repo = self.make_repo_with_nothing_to_review(pathlib.Path(td))
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(
                        err
                    ):
                        rc = mod.main(
                            ["start", "zzzzzz", "--repo", str(repo), "--prepare-only"]
                        )
                    self.assertEqual(rc, 2, out.getvalue())
                    self.assertNotIn("Nothing awaiting review", out.getvalue())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
