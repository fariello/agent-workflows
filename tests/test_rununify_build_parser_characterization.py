#!/usr/bin/env python3
"""rununify Order 10 (`s16omw`) E-02: the PER-HOST flag contract, which no existing test states.

WHY THIS FILE EXISTS, and why it is not a duplicate of `tests/test_run_flag_surface.py`. That suite
is the CONTRACT test for spec `25kzda` 2.1: it reads the spec file and asserts, in both directions,
that the spec's declared flag list and the code's registered flag list agree. It therefore checks
each host against the SPEC. It does NOT state what either host's own shipped command line looks
like, which means the whole class of change this plan is about - a shared `build_parser` silently
adding a flag to one host, removing one from the other, or moving a `dest` - is invisible to it
whenever the flag involved is outside the spec's twelve policy rows.

THE SHARPEST THING THIS FILE PINS is an INCOMPATIBILITY, not an agreement. Measured live at
execution HEAD:

  * on `oc`, all six of `--validate`, `--no-validate`, `--verify`, `--no-verify`, `--audit` and
    `--no-audit` resolve to ONE dest, `validate`;
  * on `agy`, `--verify` and `--audit` DO NOT EXIST, `--no-verify`/`--no-audit` resolve to a
    SEPARATE dest `no_verify`, and `--validate`/`--no-validate` resolve to `validate`.

So `--no-verify` means different things on the two hosts, BY DESIGN. `agy` defends that design with
a build-time guard, `agy_runipd.assert_verification_flags_are_distinct`
(`agent_workflows/agy_runipd.py:2034`), whose docstring records the measured hazard: registering
oc's alias list on agy makes `BooleanOptionalAction` auto-generate `--no-verify`/`--no-audit`, which
under `conflict_handler="resolve"` SILENTLY STEALS agy's shipped spellings. `oc` has no such guard
and needs none. This is the one place in this Set where the maintainer's "resolve to the oc version"
ruling cannot be applied, because applying it would break a shipped CLI.

ASSERTED ON THE PARSER OBJECT, NEVER ON SOURCE TEXT, deliberately. Measured at execution HEAD:
`build_parser` carries ZERO source-inspection pins, uniquely among this Set's five large functions
(`execute_item` carries 14, `initialize_run` 11). All 35 test files that touch it call
`build_parser()` and assert on the resulting parser. Introducing the first source pin this function
has ever had would be a self-inflicted obstacle to the very relocation this Set exists to perform,
so every assertion here survives the function moving to `runner_shared`.
"""

from __future__ import annotations

import argparse
import unittest

from agent_workflows import agy_runipd, oc_runipd

HOSTS = {"oc": oc_runipd, "agy": agy_runipd}

#: The six spellings whose `dest` mapping IS the incompatible contract (F-7).
VERIFICATION_FLAGS = (
    "--validate",
    "--no-validate",
    "--verify",
    "--no-verify",
    "--audit",
    "--no-audit",
)

#: E-01(a) measured at execution HEAD `4a1bb873`. Per host, per subparser, the EXACT set of option
#: strings that subparser registers. A table rather than prose so an addition or a removal fails
#: with the flag named, and so the two hosts' surfaces can be compared without either suite
#: guessing at the other's.
#:
#: `-h`/`--help` is included rather than filtered: argparse adds it, and a shared core that
#: suppressed it on one host would be an operator-visible change this plan must catch.
EXPECTED_OPTION_STRINGS: dict[str, dict[str, frozenset[str]]] = {
    "oc": {
        # integpath-04 (`rl67b0`): the `integrate` verb, declared through the ONE shared
        # `runner_shared.add_integrate_parser`, so BOTH hosts carry the identical row.
        "integrate": frozenset({"--help", "--repo", "--run-id", "-h", "id6"}),
        "report": frozenset({"--help", "--repo", "-h", "run_id"}),
        "resume": frozenset(
            {
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--audit",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--max-items-per-session",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-audit",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-validate",
                "--no-verify",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--retry-incomplete",
                "--session",
                "--stall-timeout",
                "--unattended",
                "--unverifiable-ok",
                "--validate",
                "--variant",
                "--verbose",
                "--verify",
                "--verify-with",
                "--with-dependencies",
                "-h",
                "-v",
                "run_id",
            }
        ),
        "start": frozenset(
            {
                "--action",
                "--agent",
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--audit",
                "--auto",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--manifest",
                "--max-items-per-session",
                "--model",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-audit",
                "--no-auto",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-isolate-worktree",
                "--no-self-finalize",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-validate",
                "--no-verify",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--opencode",
                "--prepare-only",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--run-id",
                "--runbook",
                "--session",
                "--stall-timeout",
                "--unattended",
                "--unverifiable-ok",
                "--validate",
                "--variant",
                "--verbose",
                "--verify",
                "--verify-with",
                "--with-dependencies",
                "-h",
                "-v",
                "selectors",
            }
        ),
        "status": frozenset({"--help", "--json", "--repo", "-h", "run_id"}),
        "stop": frozenset(
            {
                "--after-call",
                "--after-set",
                "--help",
                "--now",
                "--now-force",
                "--repo",
                "-h",
                "run_id",
            }
        ),
    },
    "agy": {
        # integpath-04 (`rl67b0`): the `integrate` verb, declared through the ONE shared
        # `runner_shared.add_integrate_parser`, so BOTH hosts carry the identical row.
        "integrate": frozenset({"--help", "--repo", "--run-id", "-h", "id6"}),
        "report": frozenset({"--help", "--repo", "-h", "run_id"}),
        "resume": frozenset(
            {
                "--agy",
                "--agy-executable",
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--max-items-per-session",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--retry-incomplete",
                "--session",
                "--stall-timeout",
                "--unattended",
                "--unverifiable-ok",
                "--verbose",
                "--with-dependencies",
                "-h",
                "-v",
                "run_id",
            }
        ),
        "start": frozenset(
            {
                "--action",
                "--agy",
                "--agy-executable",
                "--allow-dirty-base",
                "--allow-drafts",
                "--allow-mixed",
                "--allow-unverifiable",
                "--dangerous",
                "--dangerously-skip-permissions",
                "--effort",
                "--follow-generated",
                "--full-auto",
                "--help",
                "--integration-retry-limit",
                "--manifest",
                "--max-items-per-session",
                "--model",
                "--new-session",
                "--no-allow-dirty-base",
                "--no-allow-drafts",
                "--no-allow-mixed",
                "--no-allow-unverifiable",
                "--no-audit",
                "--no-dangerously-skip-permissions",
                "--no-follow-generated",
                "--no-full-auto",
                "--no-isolate-worktree",
                "--no-self-finalize",
                "--no-unattended",
                "--no-unverifiable-ok",
                "--no-validate",
                "--no-verify",
                "--no-with-dependencies",
                "--on-integration-blocked",
                "--prepare-only",
                "--quiet",
                "--raw",
                "--repo",
                "--retry-budget",
                "--run-id",
                "--runbook",
                "--session",
                "--stall-timeout",
                "--timeout",
                "--unattended",
                "--unverifiable-ok",
                "--validate",
                "--verbose",
                "--with-dependencies",
                "-h",
                "-v",
                "selectors",
            }
        ),
        "status": frozenset({"--help", "--json", "--repo", "-h", "run_id"}),
        "stop": frozenset(
            {
                "--after-call",
                "--after-set",
                "--help",
                "--now",
                "--now-force",
                "--repo",
                "-h",
                "run_id",
            }
        ),
    },
}


def subparsers(host: str) -> dict[str, argparse.ArgumentParser]:
    """Every subparser the host's `build_parser` registers, by name.

    Reached through the parser OBJECT (the `_SubParsersAction`'s `choices`), so this survives the
    function being relocated to `runner_shared`.
    """

    parser = HOSTS[host].build_parser()
    found: dict[str, argparse.ArgumentParser] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            found.update(action.choices)
    return found


def option_strings(parser: argparse.ArgumentParser) -> set[str]:
    """Every option string, plus every POSITIONAL's dest, registered on this parser.

    Positionals are included by dest because `selectors` and `run_id` are as much a part of the
    operator-visible surface as any flag, and a shared core dropping one would otherwise pass.
    """

    got: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        if action.option_strings:
            got.update(action.option_strings)
        else:
            got.add(action.dest)
    return got


def dest_of(parser: argparse.ArgumentParser, flag: str) -> str | None:
    """The `dest` `flag` resolves to on `parser`, or `None` when the flag is not registered.

    This is the function that makes F-7 testable: the collision hazard is a property of HOW the
    parser was built, so it is only decidable here and not on a parsed namespace.
    """

    for action in parser._actions:
        if flag in (action.option_strings or []):
            return action.dest
    return None


class EachHostRegistersExactlyItsOwnFlagSet(unittest.TestCase):
    """The per-host flag contract, asserted from a table so a drift names the flag.

    THIS IS THE CLASS THE SPLIT NEEDS. A shared `build_parser` core is a refactor whose whole risk
    is that one host's command line quietly changes; `test_run_flag_surface.py` cannot see that for
    any flag outside spec 2.1's twelve policy rows, which is most of them (measured: 51 shared
    option strings live on these parsers against 12 policy rows).
    """

    def test_the_two_hosts_register_the_same_six_subparsers(self):
        # SIX since 2026-09-17: integpath-04 (`rl67b0`) added `integrate`, declared on BOTH hosts through
        # the ONE shared `runner_shared.add_integrate_parser`, exactly as `stop` is. What this test is
        # actually about is that the two hosts register the SAME set, and they still do.
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(
                    sorted(subparsers(host)),
                    ["integrate", "report", "resume", "start", "status", "stop"],
                    f"{host} no longer registers exactly the six expected subparsers",
                )

    def test_every_subparser_registers_exactly_the_measured_option_strings(self):
        for host, expected_by_sub in EXPECTED_OPTION_STRINGS.items():
            live = subparsers(host)
            for sub_name, expected in expected_by_sub.items():
                with self.subTest(host=host, subparser=sub_name):
                    actual = option_strings(live[sub_name])
                    added = sorted(actual - expected)
                    removed = sorted(expected - actual)
                    self.assertEqual(
                        (added, removed),
                        ([], []),
                        f"{host} `{sub_name}` flag surface CHANGED: added={added} "
                        f"removed={removed}. If this change is intended, update "
                        f"EXPECTED_OPTION_STRINGS in the SAME change and say why; if it is not, a "
                        f"refactor has altered an operator-visible command line",
                    )

    def test_the_table_is_not_stale_against_the_live_subparser_names(self):
        """The table cannot silently stop covering a subparser that exists.

        Without this, adding a sixth subparser would leave it entirely unpinned while every
        assertion above still passed.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(
                    sorted(EXPECTED_OPTION_STRINGS[host]),
                    sorted(subparsers(host)),
                    f"the {host} table does not cover every subparser {host} registers",
                )

    def test_the_host_only_partition_is_what_was_measured(self):
        """The 8 oc-only / 8 agy-only split of the LIVE surface, asserted with members.

        NOTE THE NUMBERS, because they differ from this plan's review and the difference is
        explained rather than papered over. The review recorded 17 shared / 7 oc-only / 10 agy-only
        by counting option-string LITERALS in each `build_parser` source; that method cannot see a
        `--no-X` that `BooleanOptionalAction` auto-generates, nor anything a shared helper
        registers. Counted on the LIVE parsers, which is what an operator actually meets, the
        partition is 52 shared / 8 oc-only / 8 agy-only.

        RE-MEASURED 2026-09-17 (shared 51 -> 52) by integpath-04 (`rl67b0`): the `integrate` verb's
        positional `id6` is the one new shared entry, and because the verb is declared through ONE
        shared helper the partition moved SYMMETRICALLY. Neither host-only set changed, which is the
        property this test exists to police.
        """

        oc_all: set[str] = set()
        agy_all: set[str] = set()
        for host, bucket in (("oc", oc_all), ("agy", agy_all)):
            for sub in subparsers(host).values():
                bucket |= option_strings(sub)

        self.assertEqual(
            sorted(oc_all - agy_all),
            [
                "--agent",
                "--audit",
                "--auto",
                "--no-auto",
                "--opencode",
                "--variant",
                "--verify",
                "--verify-with",
            ],
            "the oc-only flag set changed",
        )
        self.assertEqual(
            sorted(agy_all - oc_all),
            [
                "--agy",
                "--agy-executable",
                "--dangerous",
                "--dangerously-skip-permissions",
                "--effort",
                "--new-session",
                "--no-dangerously-skip-permissions",
                "--timeout",
            ],
            "the agy-only flag set changed",
        )
        self.assertEqual(
            len(oc_all & agy_all),
            52,
            "the number of SHARED option strings changed; a flag became host-specific or stopped "
            "being so",
        )


class TheVerificationDestAsymmetryIsPinnedPerHost(unittest.TestCase):
    """F-7 made executable: `--no-verify` means different things on the two hosts, BY DESIGN.

    THIS IS THE ASSERTION THAT REFUSES THE OC-PREFERRED RULING for this symbol. The Set's rule is
    "resolve a difference to the oc version unless it is a real capability". Here the difference IS
    the capability: adopting oc's `--verify`/`--audit` aliases on agy makes `BooleanOptionalAction`
    auto-generate `--no-verify`/`--no-audit` and steal agy's shipped spellings, which is precisely
    what `agy_runipd.assert_verification_flags_are_distinct` exists to catch.

    WHEN THE SPLIT HAPPENS this class must be RE-BASED and not deleted: whatever mechanism hands
    the shared core each host's verification-flag policy must still produce exactly these dests, and
    this class is how that is proven rather than assumed.
    """

    def test_oc_collapses_all_six_spellings_onto_one_dest(self):
        for sub_name in ("start", "resume"):
            with self.subTest(subparser=sub_name):
                parser = subparsers("oc")[sub_name]
                actual = {flag: dest_of(parser, flag) for flag in VERIFICATION_FLAGS}
                self.assertEqual(
                    actual,
                    {flag: "validate" for flag in VERIFICATION_FLAGS},
                    "oc's six verification spellings must ALL resolve to dest `validate`; on this "
                    "host they are aliases of one tri-state",
                )

    def test_agy_splits_the_spellings_across_two_dests_and_omits_two(self):
        parser = subparsers("agy")["start"]
        self.assertEqual(
            {flag: dest_of(parser, flag) for flag in VERIFICATION_FLAGS},
            {
                "--validate": "validate",
                "--no-validate": "validate",
                "--verify": None,
                "--no-verify": "no_verify",
                "--audit": None,
                "--no-audit": "no_verify",
            },
            "agy's verification surface must stay DISTINCT from oc's: `--verify`/`--audit` do not "
            "exist here, and `--no-verify`/`--no-audit` carry their own dest `no_verify`. If this "
            "failed after a de-duplication, oc's alias list has been registered on agy and agy's "
            "shipped `--no-verify` no longer means what its documentation says",
        )

    def test_agy_registers_no_verification_flags_on_resume_at_all(self):
        """The measured fact, pinned so a split cannot ADD flags to agy's resume by accident.

        A shared core that registered oc's `resume` verification block on both hosts would give
        agy six new flags. That is an operator-visible addition, and spec-surface tests would not
        catch it for the four spellings outside spec 2.1's policy rows.
        """

        parser = subparsers("agy")["resume"]
        self.assertEqual(
            {flag: dest_of(parser, flag) for flag in VERIFICATION_FLAGS},
            {flag: None for flag in VERIFICATION_FLAGS},
            "agy's `resume` registers NONE of the six verification spellings; a split must not "
            "give it any",
        )

    def test_agys_build_time_collision_guard_is_still_called_and_still_passes(self):
        """The guard must be INVOKED by `build_parser`, not merely present in the module.

        Building the parser is the proof: `assert_verification_flags_are_distinct` raises
        `DriverError` on a collision, so a successful build is a passing guard. Importing the
        module would establish nothing.
        """

        parser = (
            agy_runipd.build_parser()
        )  # raises DriverError if the spellings collided
        self.assertIsNotNone(parser)
        # And the guard still refuses the collision it was installed for, so it is not vacuous.
        stolen = argparse.ArgumentParser()
        stolen.add_argument(
            "--validate",
            "--verify",
            "--audit",
            dest="validate",
            action=argparse.BooleanOptionalAction,
            default=None,
        )
        with self.assertRaises(agy_runipd.DriverError):
            agy_runipd.assert_verification_flags_are_distinct(stolen)

    def test_oc_has_no_such_guard_and_does_not_need_one(self):
        """The asymmetry's other half, asserted so it reads as a decision rather than an omission.

        oc registers ONE action for all six spellings, so there is nothing to collide. A future
        agent tempted to "add the missing guard to oc for symmetry" should read this first.
        """

        self.assertFalse(
            hasattr(oc_runipd, "assert_verification_flags_are_distinct"),
            "oc has acquired a verification-collision guard; if that is deliberate, this "
            "assertion should be replaced with one that pins what the new guard asserts",
        )
        parser = subparsers("oc")["start"]
        aliases = [
            action.option_strings
            for action in parser._actions
            if action.dest == "validate" and action.option_strings
        ]
        self.assertEqual(
            len(aliases),
            1,
            "oc's six verification spellings must remain ONE action; splitting them into several "
            "is the state agy's guard refuses",
        )


class TheBranchesASplitWouldMoveAreCharacterized(unittest.TestCase):
    """Behavioral characterization of what `build_parser` actually PRODUCES, both hosts.

    THE PARENT SET'S CONSTRAINT is that a child may not change what a runner does, and forbids
    reconciling a symbol the characterization baseline has not pinned. For a parser, "what it does"
    is: which subparser a command line selects, what defaults it freezes, and how a flag parses. All
    of that is asserted here on the parsed `Namespace`, so it survives relocation.

    AGY IS COVERED DELIBERATELY. The parent measured the two hosts' suites as asymmetric (95 oc
    tests against 21 agy at the time), so every assertion below runs against BOTH hosts unless the
    property is genuinely host-specific, and the agy-only defaults are pinned explicitly.
    """

    def test_a_bare_start_parses_and_freezes_the_measured_defaults_on_both_hosts(self):
        expected_shared = {
            "output_mode": "clean",
            "verbosity": 0,
            "prepare_only": False,
            "stall_timeout": 600.0,
            "self_finalize": True,
            "isolate_worktree": True,
        }
        for host in HOSTS:
            with self.subTest(host=host):
                args = HOSTS[host].build_parser().parse_args(["start", "s16omw"])
                self.assertEqual(args.command, "start")
                self.assertEqual(args.selectors, ["s16omw"])
                for key, value in expected_shared.items():
                    self.assertEqual(
                        getattr(args, key),
                        value,
                        f"{host} start default for {key} changed",
                    )

    def test_the_output_mode_flags_are_mutually_exclusive_on_both_hosts(self):
        """`--quiet` and `--raw` choose WHICH renderer runs, so both at once is refused.

        This is a property of `_add_output_mode_flags`, which is one of only two symbols in this
        function's closure still defined twice, and which is currently owned by no sibling plan
        (F-8). Pinning it behaviorally on both hosts means whichever plan eventually shares it has
        a test that already spans both.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                self.assertEqual(
                    parser.parse_args(["start", "x", "--quiet"]).output_mode, "quiet"
                )
                self.assertEqual(
                    parser.parse_args(["start", "x", "--raw"]).output_mode, "raw"
                )
                with self.assertRaises(SystemExit):
                    parser.parse_args(["start", "x", "--quiet", "--raw"])

    def test_resume_leaves_verbosity_absent_so_a_frozen_tier_survives_on_both_hosts(
        self,
    ):
        """`verbosity_default` is 0 on `start` and None on `resume`, on BOTH hosts.

        The distinction is load-bearing: an omitted `-v` on resume must not silently reset a frozen
        tier to 0. A shared core that passed one default for both subcommands would break it, and
        no spec-surface test would notice.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                self.assertIsNone(parser.parse_args(["resume", "run-x"]).verbosity)
                self.assertEqual(
                    parser.parse_args(["resume", "run-x", "-vv"]).verbosity, 2
                )

    def test_the_action_choices_are_constrained_identically_on_both_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                self.assertEqual(
                    parser.parse_args(["start", "x", "--action", "review"]).action,
                    "review",
                )
                with self.assertRaises(SystemExit):
                    parser.parse_args(["start", "x", "--action", "nonsense"])

    def test_agy_only_start_defaults_are_what_was_measured(self):
        """agy's own flags, pinned because a shared core must not drop or re-default them."""

        args = agy_runipd.build_parser().parse_args(["start", "x"])
        self.assertIsNone(args.validate)
        self.assertFalse(args.no_verify)
        self.assertIsNone(
            args.effort,
            "agy's --effort has no default; the host decides downstream, and a shared core "
            "inventing one here would change what a bare `start` requests",
        )
        self.assertFalse(args.new_session)
        self.assertEqual(
            args.timeout,
            agy_runipd.DEFAULT_TIMEOUT,
            "agy's --timeout default must remain the module constant, not a literal a shared "
            "core supplies",
        )
        self.assertEqual(
            args.timeout, "240m", "the measured value of DEFAULT_TIMEOUT changed"
        )
        self.assertIs(
            args.dangerously_skip_permissions,
            True,
            "agy's --dangerously-skip-permissions DEFAULTS TO TRUE, which is the opposite of what "
            "the flag name suggests and is exactly why it is pinned: a shared core that supplied "
            "the safer-looking default would silently change this host's launch posture",
        )

    def test_oc_only_start_defaults_are_what_was_measured(self):
        """oc's own flags, the mirror of the agy assertion above."""

        args = oc_runipd.build_parser().parse_args(["start", "x"])
        self.assertIsNone(args.validate)
        self.assertIsNone(args.variant)
        self.assertIsNone(args.agent)
        self.assertFalse(hasattr(args, "no_verify"))
        self.assertFalse(
            hasattr(args, "effort"),
            "oc has acquired agy's --effort; that is an operator-visible addition",
        )

    def test_the_verification_tristate_reads_each_hosts_flags_as_measured(self):
        """The dest asymmetry's CONSEQUENCE, not just its shape.

        Proving the parsed namespace feeds each host's own tri-state resolver correctly is what
        makes the dest table above matter. On agy, `--no-verify` and `--validate` together are a
        CONTRADICTION the host refuses rather than resolving by precedence.
        """

        agy_parser = agy_runipd.build_parser()
        self.assertIs(
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x"])
            ),
            None,
        )
        self.assertIs(
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x", "--no-verify"])
            ),
            False,
        )
        self.assertIs(
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x", "--validate"])
            ),
            True,
        )
        with self.assertRaises(Exception):
            agy_runipd.verification_flag_tristate(
                agy_parser.parse_args(["start", "x", "--no-verify", "--validate"])
            )

        oc_parser = oc_runipd.build_parser()
        self.assertIs(oc_parser.parse_args(["start", "x", "--verify"]).validate, True)
        self.assertIs(
            oc_parser.parse_args(["start", "x", "--no-verify"]).validate, False
        )
        self.assertIs(oc_parser.parse_args(["start", "x", "--audit"]).validate, True)

    def test_the_run_policy_flags_parse_identically_on_both_hosts(self):
        """The already-shared half (F-3), asserted to BE shared behaviorally.

        These twelve rows are registered from `runner_shared.register_run_policy_flags`, so they
        should parse the same on both hosts. Asserting it means a future host-side override shows
        up here rather than in a production incident.
        """

        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                args = parser.parse_args(
                    ["start", "x", "--allow-mixed", "--retry-budget", "5"]
                )
                self.assertTrue(args.allow_mixed)
                self.assertEqual(args.retry_budget, 5)
                self.assertFalse(
                    parser.parse_args(["start", "x", "--no-allow-mixed"]).allow_mixed
                )
                with self.assertRaises(SystemExit):
                    parser.parse_args(
                        ["start", "x", "--on-integration-blocked", "nonsense"]
                    )

    def test_status_and_report_accept_a_run_id_and_repo_on_both_hosts(self):
        for host in HOSTS:
            with self.subTest(host=host):
                parser = HOSTS[host].build_parser()
                args = parser.parse_args(["status", "run-x", "--json"])
                self.assertEqual(
                    (args.command, args.run_id, args.json), ("status", "run-x", True)
                )
                self.assertEqual(parser.parse_args(["report", "run-y"]).run_id, "run-y")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
