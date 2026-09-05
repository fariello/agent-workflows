#!/usr/bin/env python3

"""THE CONTRACT TEST for spec `25kzda` 2.1's run flag surface (runflags-01, `uyeko5`).

WHAT THIS FILE IS FOR, since the individual flag assertions below are the least valuable part of it.
Spec 2.1 declares `aw <host> run`'s invocation surface as a CLOSED flag list, and measured at HEAD
`bd91909e` seven of its eight policy flags were unreachable from either runner's command line. The
failure was systematic, not a gap in one feature: THE POLICY LANDED AND THE OPERATOR SURFACE DID NOT.
`--allow-mixed` and `--unattended` had working, tested policy behind them and no flag to reach it, and
`run_selection_policy.decide` - the entire mixed-type gate executed plan `6lu3rq` built - had ZERO
callers anywhere in the package.

So the load-bearing test here is not "`--allow-mixed` parses". It is
:meth:`SpecFlagListTests.test_every_flag_the_spec_declares_is_accounted_for`, which reads the SPEC
FILE, extracts its grammar block, and fails when the spec declares a flag the code neither registers
nor explicitly excludes. That is what makes the drift a test failure instead of an archaeology
project the next time the spec grows a flag.

DATA-DRIVEN, NOT HAND-WRITTEN PER FLAG, for the same reason: eight hand-written assertions are eight
things to forget to add a ninth to. Every test below iterates `runner_shared.RUN_POLICY_FLAGS`.

WHY THIS FILE EXISTS RATHER THAN LIVING IN EITHER HOST'S SUITE: the property under test is that the
TWO hosts agree. Asserting that from inside `test_oc_runipd.py` would put the agy half of a symmetry
claim in the opencode suite, and `818uru` already set the precedent that shared runner code gets its
own test home (`tests/test_runner_shared.py`).
"""

from __future__ import annotations

import argparse
import re
import unittest

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.support import REPO_ROOT

_MODULES = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}
BOTH = ("oc_runipd", "agy_runipd")

#: The spec this surface implements. Read as a FILE, so a spec edit can fail this suite.
SPEC_PATH = (
    REPO_ROOT
    / ".aw"
    / "records"
    / "specs"
    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
)

#: Spec 2.1 grammar entries that are NOT part of this surface, each with the reason it is excluded.
#: An exclusion must be NAMED here to pass `test_every_flag_the_spec_declares_is_accounted_for`;
#: silence is a failure. That is deliberate: an unexplained gap between the spec and the code is
#: exactly the state this file exists to make impossible.
DECLARED_BUT_NOT_OWNED_HERE = {
    "--type": "spec 2.2/2.3 multi-type selection; needs the whole per-type dispatch table, not a flag",
    "--action": "revsweep-01 (`76gsmv`) registers it with its per-type legality refusal",
    "--json": "output shape, not policy; exists on `status` today and is not a `run` policy flag",
    "--allow-drafts": "spec 2.5a draft admission gate, owned by revsweep-02 (`6ypimw`)",
}


def _subparser(runner: str, name: str) -> argparse.ArgumentParser:
    parser = _MODULES[runner].build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices[name]
    raise AssertionError(f"{runner} has no subparsers")


def _option_strings(runner: str, name: str) -> set:
    return {
        opt
        for action in _subparser(runner, name)._actions
        for opt in action.option_strings
    }


def _action_for_flag(runner: str, subcommand: str, flag: str):
    for action in _subparser(runner, subcommand)._actions:
        if flag in action.option_strings:
            return action
    return None


def _parse(runner: str, argv: list) -> argparse.Namespace:
    return _MODULES[runner].build_parser().parse_args(argv)


class SpecFlagListTests(unittest.TestCase):
    """The drift guard: the SPEC FILE is the input, not a transcription of it."""

    def spec_grammar_flags(self) -> set:
        """Every `--flag` on spec 2.1's `aw <host> run <selector>` STANZA of the grammar block.

        Parsed from the spec rather than copied out of it, which is the entire point: a flag added to
        section 2.1 and to nothing else must FAIL here.

        TWO SCOPING DECISIONS, both of which change the answer:

        * Scoped to the grammar BLOCK, not the whole section, because the surrounding prose also
          mentions flags the grammar deliberately does not declare - notably the
          `--no-verify`/`--skip-audit`/`--dangerous` group that `:140` states does NOT exist on `run`.
          Treating a prohibition as a declaration would invert its meaning.
        * Scoped within the block to the `aw <host> run <selector>` stanza, stopping at the next
          command. The block declares FIVE commands, and `aw <host> prompt`'s `--text`/`--file` are
          not `run` policy flags at all; including them would have this test demand that `run` grow
          `--text`, which is a different verb's surface. The stanza is delimited by the blank line
          before the next `aw ` line, which is the block's own structure and not a heuristic.
        """
        text = SPEC_PATH.read_text(encoding="utf-8")
        section = text.split("### 2.1 Command grammar", 1)
        self.assertEqual(
            len(section), 2, "spec 2.1 heading not found; did the spec move?"
        )
        block = section[1].split("```text", 1)[1].split("```", 1)[0]
        stanza: list = []
        started = False
        for line in block.splitlines():
            if line.startswith("aw ") and "run <selector>" in line:
                started = True
                continue
            if started:
                if not line.strip() or line.startswith("aw "):
                    break
                stanza.append(line)
        self.assertTrue(
            stanza, "spec 2.1's `aw <host> run <selector>` stanza not found"
        )
        return set(re.findall(r"--[a-z][a-z0-9-]*", "\n".join(stanza)))

    def test_every_flag_the_spec_declares_is_accounted_for(self):
        """THE LOAD-BEARING ASSERTION. Registered here, or excluded WITH A NAMED REASON."""
        declared = self.spec_grammar_flags()
        owned = set(runner_shared.RUN_POLICY_FLAGS_BY_FLAG)
        excluded = set(DECLARED_BUT_NOT_OWNED_HERE)
        unaccounted = sorted(declared - owned - excluded)
        self.assertEqual(
            unaccounted,
            [],
            "spec 25kzda 2.1 declares flag(s) that this surface neither registers nor "
            f"explicitly excludes: {unaccounted}. Add each to runner_shared.RUN_POLICY_FLAGS "
            "or to DECLARED_BUT_NOT_OWNED_HERE with the reason and the owner.",
        )

    def test_no_owned_flag_is_absent_from_the_spec(self):
        """The converse: this surface must not invent a flag the spec does not declare."""
        declared = self.spec_grammar_flags()
        invented = sorted(set(runner_shared.RUN_POLICY_FLAGS_BY_FLAG) - declared)
        self.assertEqual(
            invented,
            [],
            f"flag(s) registered here are NOT in spec 2.1's grammar: {invented}",
        )

    def test_the_owned_set_is_the_eight_this_plan_claims(self):
        """The plan's own count, re-derived rather than trusted."""
        self.assertEqual(len(runner_shared.RUN_POLICY_FLAGS), 8)
        self.assertEqual(
            len({row.flag for row in runner_shared.RUN_POLICY_FLAGS}),
            8,
            "duplicate flag",
        )
        self.assertEqual(
            len({row.dest for row in runner_shared.RUN_POLICY_FLAGS}),
            8,
            "duplicate dest",
        )

    def test_every_exclusion_names_a_reason(self):
        for flag, reason in sorted(DECLARED_BUT_NOT_OWNED_HERE.items()):
            with self.subTest(flag=flag):
                self.assertTrue(reason.strip(), f"{flag} is excluded with no reason")


class RegistrationTests(unittest.TestCase):
    """E-01: every spec 2.1 policy flag is REGISTERED on BOTH hosts' `run` parser.

    REGISTRATION ONLY, deliberately: that the flag parses and lands in the namespace. Behavior is
    asserted by the classes below, and conflating the two would make this class fail for two
    unrelated reasons and stop being a usable signal.
    """

    def test_every_flag_is_registered_on_both_hosts_start_parser(self):
        missing = []
        for runner in BOTH:
            registered = _option_strings(runner, "start")
            for row in runner_shared.RUN_POLICY_FLAGS:
                if row.flag not in registered:
                    missing.append(f"{runner}: {row.flag}")
        self.assertEqual(
            missing,
            [],
            "spec 25kzda 2.1 flag(s) NOT registered on the `run`/`start` parser:\n  "
            + "\n  ".join(missing),
        )

    def test_every_flag_is_registered_on_both_hosts_resume_parser(self):
        """`resume` must ACCEPT each flag, even the one it refuses.

        A flag argparse rejects produces `unrecognized arguments`, which tells the operator the flag
        does not exist. `--retry-budget` on resume must instead fail with the spec's actual reason
        (the frozen value cannot change), and that needs argparse to accept it first.
        """
        missing = []
        for runner in BOTH:
            registered = _option_strings(runner, "resume")
            for row in runner_shared.RUN_POLICY_FLAGS:
                if row.flag not in registered:
                    missing.append(f"{runner}: {row.flag}")
        self.assertEqual(
            missing, [], "not registered on `resume`:\n  " + "\n  ".join(missing)
        )

    def test_every_flag_lands_in_the_namespace_under_its_documented_dest(self):
        for runner in BOTH:
            args = _parse(runner, ["start", "demo"])
            for row in runner_shared.RUN_POLICY_FLAGS:
                with self.subTest(runner=runner, flag=row.flag):
                    self.assertTrue(
                        hasattr(args, row.dest),
                        f"{runner}: {row.flag} does not populate `{row.dest}`",
                    )

    def test_every_flag_appears_in_help_for_both_hosts(self):
        for runner in BOTH:
            text = _subparser(runner, "start").format_help()
            for row in runner_shared.RUN_POLICY_FLAGS:
                with self.subTest(runner=runner, flag=row.flag):
                    self.assertIn(row.flag, text)

    def test_the_two_hosts_flag_sets_are_identical(self):
        """The `rununify` property: one surface, not two that merely agree today."""
        oc = {
            f
            for f in _option_strings("oc_runipd", "start")
            if f in runner_shared.RUN_POLICY_FLAGS_BY_FLAG
        }
        agy = {
            f
            for f in _option_strings("agy_runipd", "start")
            if f in runner_shared.RUN_POLICY_FLAGS_BY_FLAG
        }
        self.assertEqual(oc, agy)
        self.assertEqual(oc, set(runner_shared.RUN_POLICY_FLAGS_BY_FLAG))

    def test_bool_flags_have_a_negation_on_both_hosts(self):
        """`BooleanOptionalAction`, matching the shipped `--full-auto`, so `--no-X` exists."""
        for runner in BOTH:
            registered = _option_strings(runner, "start")
            for row in runner_shared.RUN_POLICY_FLAGS:
                if row.kind != "bool":
                    continue
                with self.subTest(runner=runner, flag=row.flag):
                    self.assertIn(f"--no-{row.flag[2:]}", registered)


class HelpHonestyTests(unittest.TestCase):
    """Spec/documentation sync: a divergence from the spec's full semantics is in `--help`.

    An operator reads `--help` and never reads an IPD, so recording an unimplemented flag or a missing
    precedence tier only in a plan leaves the shipped command lying about what it does.
    """

    def test_an_unimplemented_flags_help_says_so(self):
        for row in runner_shared.RUN_POLICY_FLAGS:
            if row.implemented:
                continue
            with self.subTest(flag=row.flag):
                self.assertIn("NOT YET IMPLEMENTED", row.help)
                self.assertIn("x8diyb", row.help, "the help must name the owner")

    def test_the_retry_budget_help_states_the_missing_policy_tier(self):
        row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG["--retry-budget"]
        self.assertIn("NOT IMPLEMENTED", row.help)
        self.assertIn("dh3us4", row.help)

    def test_the_unverifiable_ok_help_states_its_precondition(self):
        row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG["--unverifiable-ok"]
        self.assertIn("--allow-unverifiable", row.help)

    def test_full_auto_help_records_the_unattended_implication(self):
        row = runner_shared.RUN_POLICY_FLAGS_BY_FLAG["--full-auto"]
        self.assertIn("--unattended", row.help)

    def test_the_rendered_help_carries_each_rows_text_on_both_hosts(self):
        """The table's `help` is what an operator SEES, not just what the table says."""
        for runner in BOTH:
            for row in runner_shared.RUN_POLICY_FLAGS:
                action = _action_for_flag(runner, "start", row.flag)
                with self.subTest(runner=runner, flag=row.flag):
                    assert action is not None
                    self.assertEqual(action.help, row.help)


class MixedTypeGateWiringTests(unittest.TestCase):
    """E-02: `6lu3rq`'s gate is CALLED, and it APPLIES on a genuinely multi-type classification.

    THE DEFECT THIS CLASS EXISTS FOR is not a missing flag. `run_selection_policy.decide` had ZERO
    callers anywhere in the package, so a fully built and fully tested gate was unreachable and a
    mixed selection was silently accepted. A test that only checked `--allow-mixed` parses would pass
    while the gate stayed dead - which is exactly the state this plan found.

    AND `gate_applied=False` DOES NOT SATISFY THIS CLASS. `decide` short-circuits `gate_applied=False`
    whenever the classification is single-type, which is what a still-dead gate would also produce; so
    the assertions below construct a REAL multi-type classification and require `gate_applied=True`.

    THE LIMIT, asserted rather than merely commented, so a green run of this file is not mistaken for
    more than it proves: no live `aw <host> run` invocation can yet produce a mixed selection, because
    discovery is IPD-only and neither host registers `--type`. See
    :meth:`test_no_live_invocation_can_yet_produce_a_mixed_selection`.
    """

    def multi_type_paths(self, root) -> list:
        """A REAL multi-type path set: one IPD plus one spec, both typed by the shipped authority."""
        plans = root / ".aw" / "records" / "plans" / "pending"
        specs = root / ".aw" / "records" / "specs"
        plans.mkdir(parents=True, exist_ok=True)
        specs.mkdir(parents=True, exist_ok=True)
        ipd = plans / "20260905-demo-01-aaa111-demo.ipd.md"
        ipd.write_text("- Status: approved\n- Id: aaa111\n", encoding="utf-8")
        spec = specs / "20260905-bbb222-01-bbb222-demo.spec.md"
        spec.write_text("- Status: approved\n- Id: bbb222\n", encoding="utf-8")
        return [ipd, spec]

    def classify_multi(self, root):
        from agent_workflows import run_selection_policy

        classification = run_selection_policy.classify_paths(
            root, self.multi_type_paths(root)
        )
        self.assertTrue(
            classification.is_mixed,
            f"the fixture is not multi-type: {classification.spec_types}",
        )
        return classification

    def test_decide_is_called_from_the_runner(self):
        """The dead-gate fix itself: a call site exists, in SHARED code both hosts reach."""
        import ast
        import inspect

        # AST, not a substring search: a substring cannot tell a real call from the SAME text sitting
        # in a comment or docstring, and this module's docstrings mention `decide` repeatedly (they
        # explain the dead-gate defect), so a naive `assertIn` here would pass on prose alone.
        source = inspect.getsource(runner_shared.enforce_mixed_type_gate)
        called = {
            ast.unparse(node.func)
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
        }
        self.assertIn("run_selection_policy.decide", called)
        for runner in BOTH:
            with self.subTest(runner=runner):
                body = inspect.getsource(_MODULES[runner].initialize_run)
                self.assertIn("enforce_mixed_type_gate", body)

    def test_the_gate_APPLIES_and_REFUSES_a_multi_type_selection_unattended(self):
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            paths = self.multi_type_paths(root)
            with self.assertRaises(runner_shared.DriverError) as ctx:
                runner_shared.enforce_mixed_type_gate(
                    root,
                    paths,
                    allow_mixed=False,
                    interactive=False,
                    host="oc",
                    selector="all",
                )
            self.assertIn("[RUN-MIXED-TYPES]", str(ctx.exception))
            self.assertIn("No work started.", str(ctx.exception))

    def test_the_gate_APPLIES_and_PROCEEDS_with_allow_mixed(self):
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            verdict = runner_shared.enforce_mixed_type_gate(
                root,
                self.multi_type_paths(root),
                allow_mixed=True,
                interactive=False,
                host="oc",
                selector="all",
            )
            self.assertTrue(verdict.proceed)
            self.assertTrue(
                verdict.gate_applied,
                "gate_applied=False is the SINGLE-TYPE short circuit and would also be "
                "returned by a still-dead gate; it does not prove the gate applied",
            )
            self.assertEqual(verdict.record.response_or_flag, "--allow-mixed")

    def test_an_interactive_multi_type_selection_requires_the_exact_phrase(self):
        import tempfile
        from pathlib import Path as _P

        from agent_workflows import run_selection_policy

        with tempfile.TemporaryDirectory() as td:
            root = _P(td)
            classification = self.classify_multi(root)
            for bad in ("y", "yes", "", "run", "run mixed types"):
                with self.subTest(response=bad):
                    verdict = run_selection_policy.decide(
                        classification, interactive=True, response=bad
                    )
                    self.assertFalse(verdict.proceed)
                    self.assertTrue(verdict.gate_applied)
            good = run_selection_policy.decide(
                classification, interactive=True, response="run mixed"
            )
            self.assertTrue(good.proceed)
            self.assertTrue(good.gate_applied)

    def test_no_part_of_the_gate_was_reimplemented(self):
        """The refusal text must still come FROM `run_selection_policy`, not from a second copy."""
        import inspect

        from agent_workflows import run_selection_policy

        for module in (runner_shared, oc_runipd, agy_runipd):
            with self.subTest(module=module.__name__):
                source = inspect.getsource(module)
                self.assertNotIn(
                    run_selection_policy.REFUSAL_TEMPLATE[:40],
                    source,
                    f"{module.__name__} contains a COPY of the spec refusal text",
                )
                self.assertNotIn(
                    f'"{run_selection_policy.CONFIRM_PHRASE}"',
                    source,
                    f"{module.__name__} re-spells the exact confirmation phrase",
                )

    def test_no_live_invocation_can_yet_produce_a_mixed_selection(self):
        """THE LIMIT, as an assertion. Registering `--type` would falsify this and must fail here.

        Two independent reasons, both asserted: discovery is IPD-only, and neither host has `--type`.
        When a later plan builds multi-type selection it will have to update this test, which is the
        point - the limit becomes visible rather than being silently outgrown.
        """
        for runner in BOTH:
            for sub in ("start", "resume"):
                with self.subTest(runner=runner, subcommand=sub):
                    self.assertNotIn("--type", _option_strings(runner, sub))
        import inspect

        source = inspect.getsource(runner_shared.discover_plans)
        self.assertIn(".aw", source)
        self.assertNotIn(
            "specs", source, "discovery is IPD-only; a spec tree would change this"
        )


class FullAutoImpliesUnattendedTests(unittest.TestCase):
    """E-02: spec `:134` - `--full-auto` implies `--unattended`, and implies NOTHING else."""

    def frozen(self, **kw) -> dict:
        base = {row.dest: False for row in runner_shared.RUN_POLICY_FLAGS}
        base["retry_budget"] = None
        base.update(kw)
        return runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))

    def test_full_auto_implies_unattended(self):
        self.assertTrue(self.frozen(full_auto=True)["unattended"])

    def test_full_auto_implies_nothing_else(self):
        frozen = self.frozen(full_auto=True)
        for row in runner_shared.RUN_POLICY_FLAGS:
            if row.dest in ("full_auto", "unattended", "retry_budget"):
                continue
            with self.subTest(flag=row.flag):
                self.assertFalse(
                    frozen[row.dest],
                    f"--full-auto must not imply {row.flag} (spec :134)",
                )

    def test_unattended_alone_does_not_imply_full_auto(self):
        self.assertFalse(self.frozen(unattended=True)["full_auto"])

    def test_an_unattended_run_is_not_interactive_even_with_a_tty(self):
        """The operator's declaration outranks a TTY that happens to exist."""

        class _TTY:
            def isatty(self):
                return True

        self.assertFalse(
            runner_shared.is_interactive_run(
                argparse.Namespace(unattended=True, full_auto=False), stream=_TTY()
            )
        )
        self.assertFalse(
            runner_shared.is_interactive_run(
                argparse.Namespace(unattended=False, full_auto=True), stream=_TTY()
            )
        )

    def test_no_tty_means_not_interactive_regardless_of_flags(self):
        class _NotTTY:
            def isatty(self):
                return False

        self.assertFalse(
            runner_shared.is_interactive_run(
                argparse.Namespace(unattended=False, full_auto=False), stream=_NotTTY()
            )
        )


class UnverifiableAdmissionTests(unittest.TestCase):
    """E-03: `--unverifiable-ok` is bound to `zub5f1`'s predicate, precondition and all."""

    def args(self, **kw) -> argparse.Namespace:
        base = {"unverifiable_ok": False, "allow_unverifiable": False}
        base.update(kw)
        return argparse.Namespace(**base)

    def test_unverifiable_ok_alone_is_refused_naming_the_missing_admission(self):
        with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
            runner_shared.evaluate_unverifiable_admission(
                self.args(unverifiable_ok=True)
            )
        message = str(ctx.exception)
        self.assertIn("--unverifiable-ok", message)
        self.assertIn("--allow-unverifiable", message)

    def test_unverifiable_ok_with_its_admission_is_honored(self):
        aggregation = runner_shared.evaluate_unverifiable_admission(
            self.args(unverifiable_ok=True, allow_unverifiable=True)
        )
        self.assertTrue(aggregation.unverifiable_ok_applied)
        self.assertEqual(aggregation.refusals, ())

    def test_allow_unverifiable_alone_is_legal(self):
        """The ADMISSION is not itself the neutrality grant, so it needs no companion flag."""
        aggregation = runner_shared.evaluate_unverifiable_admission(
            self.args(allow_unverifiable=True)
        )
        self.assertFalse(aggregation.unverifiable_ok_applied)
        self.assertEqual(aggregation.refusals, ())

    def test_the_aggregation_rule_is_not_reimplemented_in_the_runners(self):
        """`zub5f1` owns the aggregate rule; this surface supplies the flags and calls it."""
        import inspect

        from agent_workflows import run_evidence

        for module in (runner_shared, oc_runipd, agy_runipd):
            with self.subTest(module=module.__name__):
                source = inspect.getsource(module)
                self.assertNotIn(
                    "CONTRIBUTION_NEUTRAL",
                    source,
                    f"{module.__name__} re-decides aggregate neutrality",
                )
        self.assertTrue(
            hasattr(run_evidence, "REFUSAL_UNVERIFIABLE_OK_UNADMITTED"),
            "the refusal predicate must come from run_evidence",
        )

    def test_the_refusal_message_is_the_predicates_own(self):
        from agent_workflows import run_evidence

        aggregation = run_evidence.aggregate_run_exit(
            [], unverifiable_ok=True, unverifiable_admitted=False
        )
        predicate = next(
            r
            for r in aggregation.refusals
            if r.name == run_evidence.REFUSAL_UNVERIFIABLE_OK_UNADMITTED
        )
        with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
            runner_shared.evaluate_unverifiable_admission(
                self.args(unverifiable_ok=True)
            )
        self.assertIn(predicate.details, str(ctx.exception))


class RetryBudgetTests(unittest.TestCase):
    """E-04: the flag, its precedence, and `sq61qd`'s bound CALLED rather than re-checked."""

    def test_the_default_is_still_two(self):
        from agent_workflows import run_recovery

        self.assertEqual(run_recovery.DEFAULT_RETRY_LIMIT, 2)
        self.assertEqual(runner_shared.resolve_retry_budget(None), 2)

    def test_a_cli_value_overrides_the_default(self):
        self.assertEqual(runner_shared.resolve_retry_budget(7), 7)

    def test_zero_is_legal_and_is_not_treated_as_unset(self):
        """`0` means NO retries. Reading it as unset would silently restore two retries."""
        self.assertEqual(runner_shared.resolve_retry_budget(0), 0)

    def test_both_bounds_are_accepted(self):
        self.assertEqual(runner_shared.resolve_retry_budget(0), 0)
        self.assertEqual(runner_shared.resolve_retry_budget(10), 10)

    def test_an_out_of_range_value_is_refused(self):
        for bad in (-1, 11, 999):
            with self.subTest(value=bad):
                with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                    runner_shared.resolve_retry_budget(bad)
                self.assertIn("0..10", str(ctx.exception))

    def test_the_bound_is_sq61qds_and_is_not_re_checked_here(self):
        """CALLED, not copied: `sq61qd` made `validate_retry_budget` the single definition."""
        import inspect

        from agent_workflows import run_recovery

        source = inspect.getsource(runner_shared.resolve_retry_budget)
        self.assertIn("validate_retry_budget", source)
        self.assertNotIn(
            "10", source.split('"""')[-1], "a literal bound would be a second copy"
        )
        with self.assertRaises(run_recovery.InvalidRetryBudgetError):
            run_recovery.validate_retry_budget(11)

    def test_an_out_of_range_value_refuses_the_whole_run(self):
        """Refused at initialize_run, before a run directory exists."""
        import inspect

        for runner in BOTH:
            with self.subTest(runner=runner):
                source = inspect.getsource(_MODULES[runner].initialize_run)
                self.assertIn("resolve_retry_budget", source)

    def test_the_frozen_value_is_the_effective_integer(self):
        base = {row.dest: False for row in runner_shared.RUN_POLICY_FLAGS}
        base["retry_budget"] = None
        self.assertEqual(
            runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))[
                "retry_budget"
            ],
            2,
        )
        base["retry_budget"] = 5
        self.assertEqual(
            runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))[
                "retry_budget"
            ],
            5,
        )


class UnimplementedFlagRefusalTests(unittest.TestCase):
    """E-05: `--follow-generated` and `--with-dependencies` REFUSE; they never silently no-op.

    A pasted `--help` does not prove this. A flag that parses and does nothing is strictly WORSE than
    no flag, because an operator who passes `--with-dependencies` and gets no closure expansion has
    been told a falsehood about what the run enforced. Only an observed refusal proves otherwise.
    """

    def unimplemented(self) -> list:
        return [row for row in runner_shared.RUN_POLICY_FLAGS if not row.implemented]

    def test_there_are_exactly_two_and_they_are_the_expected_two(self):
        self.assertEqual(
            sorted(row.flag for row in self.unimplemented()),
            ["--follow-generated", "--with-dependencies"],
        )

    def test_each_refuses_when_passed(self):
        for row in self.unimplemented():
            with self.subTest(flag=row.flag):
                args = argparse.Namespace(**{row.dest: True})
                with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                    runner_shared.refuse_unimplemented_run_flags(args)
                message = str(ctx.exception)
                self.assertIn(row.flag, message)
                self.assertIn("not yet implemented", message)
                self.assertIn(
                    "x8diyb", message, "the refusal must name the owning backlog item"
                )

    def test_not_passing_them_is_silent(self):
        args = argparse.Namespace(**{row.dest: False for row in self.unimplemented()})
        runner_shared.refuse_unimplemented_run_flags(args)

    def test_an_implemented_flag_is_never_refused_by_this_predicate(self):
        args = argparse.Namespace(
            **{
                row.dest: True
                for row in runner_shared.RUN_POLICY_FLAGS
                if row.implemented
            }
        )
        runner_shared.refuse_unimplemented_run_flags(args)

    def test_both_runners_refuse_before_any_durable_state(self):
        import inspect

        for runner in BOTH:
            source = inspect.getsource(_MODULES[runner].initialize_run)
            before_run_dir = source.split("run_dir = state_root")[0]
            with self.subTest(runner=runner):
                self.assertIn("refuse_unimplemented_run_flags", before_run_dir)


class FreezeAndResumeTests(unittest.TestCase):
    """E-06: values frozen at queue build; `--retry-budget` refused on resume; omission preserves."""

    def resume_args(self, **kw) -> argparse.Namespace:
        base = {row.dest: None for row in runner_shared.RUN_POLICY_FLAGS}
        base.update(kw)
        return argparse.Namespace(**base)

    def test_every_flag_marked_freeze_is_frozen(self):
        base = {row.dest: False for row in runner_shared.RUN_POLICY_FLAGS}
        base["retry_budget"] = None
        frozen = runner_shared.freeze_run_policy_flags(argparse.Namespace(**base))
        for row in runner_shared.RUN_POLICY_FLAGS:
            if row.freeze:
                with self.subTest(flag=row.flag):
                    self.assertIn(row.dest, frozen)

    def test_both_runners_freeze_through_the_shared_function(self):
        import inspect

        for runner in BOTH:
            with self.subTest(runner=runner):
                self.assertIn(
                    "freeze_run_policy_flags",
                    inspect.getsource(_MODULES[runner].initialize_run),
                )

    def test_retry_budget_with_resume_is_refused(self):
        with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
            runner_shared.refuse_frozen_flags_on_resume(
                self.resume_args(retry_budget=5)
            )
        self.assertIn("--retry-budget", str(ctx.exception))
        self.assertIn("frozen", str(ctx.exception))

    def test_retry_budget_zero_with_resume_is_also_refused(self):
        """`0` is a real value, so `if value:` would let it through. The check is `is not None`."""
        with self.assertRaises(runner_shared.RunFlagRefusal):
            runner_shared.refuse_frozen_flags_on_resume(
                self.resume_args(retry_budget=0)
            )

    def test_resume_without_the_frozen_flag_is_allowed(self):
        runner_shared.refuse_frozen_flags_on_resume(self.resume_args())

    def test_an_omitted_flag_on_resume_does_not_clobber_the_frozen_value(self):
        state = {
            "options": {"allow_mixed": True, "full_auto": True, "unattended": True}
        }
        changed = runner_shared.apply_run_policy_flags_on_resume(
            state, self.resume_args()
        )
        self.assertFalse(changed)
        self.assertEqual(
            state["options"],
            {"allow_mixed": True, "full_auto": True, "unattended": True},
        )

    def test_a_passed_flag_on_resume_overwrites_the_frozen_value(self):
        """The SHIPPED `--full-auto` resume behavior, preserved and generalized, not changed."""
        state = {"options": {"full_auto": True}}
        changed = runner_shared.apply_run_policy_flags_on_resume(
            state, self.resume_args(full_auto=False)
        )
        self.assertTrue(changed)
        self.assertIs(state["options"]["full_auto"], False)

    def test_resume_does_not_reapply_the_unattended_implication(self):
        """Flipping a SECOND frozen option the operator did not name is a hidden write."""
        state = {"options": {"full_auto": False, "unattended": False}}
        runner_shared.apply_run_policy_flags_on_resume(
            state, self.resume_args(full_auto=True)
        )
        self.assertIs(state["options"]["unattended"], False)

    def test_resume_never_applies_a_refused_flag(self):
        state = {"options": {"retry_budget": 2}}
        runner_shared.apply_run_policy_flags_on_resume(
            state, self.resume_args(retry_budget=9)
        )
        self.assertEqual(state["options"]["retry_budget"], 2)

    def test_both_runners_refuse_and_apply_on_resume(self):
        import inspect

        for runner in BOTH:
            source = inspect.getsource(_MODULES[runner].main)
            with self.subTest(runner=runner):
                self.assertIn("refuse_frozen_flags_on_resume", source)
                self.assertIn("apply_run_policy_flags_on_resume", source)

    def test_every_resume_declaration_defaults_to_None(self):
        """`default=None` is the mechanism: without it, resume cannot tell `--no-X` from silence."""
        for runner in BOTH:
            for row in runner_shared.RUN_POLICY_FLAGS:
                action = _action_for_flag(runner, "resume", row.flag)
                with self.subTest(runner=runner, flag=row.flag):
                    assert action is not None
                    self.assertIsNone(action.default)


class FullAutoDefaultNormalizationTests(unittest.TestCase):
    """E-07: `--full-auto` defaults `False` on BOTH hosts, at ALL THREE sites per host.

    A parser-only fix would leave the old behavior live while `--help` claimed otherwise, which is the
    worst of the three outcomes. Before this, `aw agy run <selector>` auto-cleared a `reviewed` plan
    with an approving `- Readiness:` to `auto-approved` and EXECUTED it with no flag passed, so
    execution was opt-OUT on one host and opt-IN on the other.
    """

    def test_site_1_the_parser_default_is_False_on_both_hosts(self):
        for runner in BOTH:
            action = _action_for_flag(runner, "start", "--full-auto")
            with self.subTest(runner=runner):
                assert action is not None
                self.assertIs(action.default, False)

    def test_site_2_the_args_fallback_is_False_on_both_hosts(self):
        """The `getattr(args, "full_auto", <default>)` in `initialize_run`."""
        import inspect
        import re as _re

        for runner in BOTH:
            source = inspect.getsource(_MODULES[runner].initialize_run)
            found = _re.findall(
                r'getattr\(\s*args,\s*"full_auto",\s*(\w+)\s*\)', source
            )
            with self.subTest(runner=runner):
                self.assertEqual(found, ["False"], f"{runner} args fallback: {found}")

    def test_site_3_the_run_state_fallback_is_False_on_both_hosts(self):
        """The `state["options"].get("full_auto", <default>)` in `execute_item`."""
        import inspect
        import re as _re

        for runner in BOTH:
            source = inspect.getsource(_MODULES[runner].execute_item)
            found = _re.findall(r'get\(\s*"full_auto",\s*(\w+)\s*\)', source)
            with self.subTest(runner=runner):
                self.assertEqual(
                    found, ["False"], f"{runner} run-state fallback: {found}"
                )

    def test_no_True_default_for_full_auto_survives_anywhere(self):
        """The catch-all: any of the three spellings with a `True` default fails here."""
        import inspect
        import re as _re

        patterns = (
            r'getattr\(\s*args,\s*"full_auto",\s*True\s*\)',
            r'get\(\s*"full_auto",\s*True\s*\)',
        )
        for runner in BOTH:
            source = inspect.getsource(_MODULES[runner])
            for pattern in patterns:
                with self.subTest(runner=runner, pattern=pattern):
                    self.assertEqual(_re.findall(pattern, source), [])

    def test_a_bare_run_does_not_request_auto_approval_on_either_host(self):
        for runner in BOTH:
            args = _parse(runner, ["start", "demo"])
            with self.subTest(runner=runner):
                self.assertIs(args.full_auto, False)

    def test_an_explicit_full_auto_still_works_on_both_hosts(self):
        for runner in BOTH:
            with self.subTest(runner=runner):
                self.assertIs(
                    _parse(runner, ["start", "demo", "--full-auto"]).full_auto, True
                )
                self.assertIs(
                    _parse(runner, ["start", "demo", "--no-full-auto"]).full_auto, False
                )

    def test_the_resume_declaration_is_still_None_on_both_hosts(self):
        """F-6's mechanism is a DIFFERENT concern and was already correct; it stays untouched."""
        for runner in BOTH:
            action = _action_for_flag(runner, "resume", "--full-auto")
            with self.subTest(runner=runner):
                assert action is not None
                self.assertIsNone(action.default)


class FullAutoEndToEndBehaviorTests(unittest.TestCase):
    """E-07's BEHAVIOR, not just its default: a bare run no longer auto-approves.

    V-07 requires this because a pasted parser default proves nothing about what the run DOES. The
    auto-approve decision lives in `initialize_run`, so this drives that function on a real repository
    holding a `Status: reviewed` plan whose `- Readiness:` is approving - the exact input that was
    silently cleared and executed by `aw agy run <selector>` with no flag passed.
    """

    PLAN = """# IPD: bare-run auto-approve probe

- Date: 2026-09-05
- Kind: child
- Concern: probe.
- Scope: probe.
- Scope-Paths: src/
- Item-Dependencies: none
- Status: reviewed
- Readiness: go
- Set: probe
- Order: 1
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-05 reviewed (test): APPROVE; no blocking findings.
"""

    def make_repo(self, root, id6: str = "prb001"):
        import subprocess

        repo = root / "repo"
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
        plan = pending / f"20260905-probe-01-{id6}-probe.ipd.md"
        plan.write_text(self.PLAN.format(id6=id6), encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
        return repo, plan

    def run_and_read_status(self, runner: str, argv: list):
        """`initialize_run` on a fresh repo; returns (plan text after, queue initial_status)."""
        import tempfile
        from pathlib import Path as _P

        with tempfile.TemporaryDirectory() as td:
            repo, plan = self.make_repo(_P(td))
            args = _parse(runner, ["start", "prb001", "--repo", str(repo), *argv])
            args.prepare_only = True
            run_dir = _MODULES[runner].initialize_run(args)
            state = runner_shared.load_state(run_dir)
            entry = state["queue"][0]
            # The plan may have been MOVED by an auto-approve, so re-read by id6 rather than by path.
            found = list((repo / ".aw" / "records" / "plans").rglob("*prb001*.ipd.md"))
            self.assertEqual(len(found), 1, found)
            return found[0].read_text(encoding="utf-8"), entry["initial_status"], state

    def test_a_bare_run_does_NOT_auto_approve_on_either_host(self):
        for runner in BOTH:
            with self.subTest(runner=runner):
                text, initial_status, state = self.run_and_read_status(runner, [])
                self.assertIn("- Status: reviewed", text)
                self.assertNotIn("auto-approved", text)
                self.assertEqual(initial_status, "reviewed")
                self.assertIs(state["options"]["full_auto"], False)

    def test_an_explicit_full_auto_DOES_auto_approve_on_either_host(self):
        """The capability is preserved; only the DEFAULT changed."""
        for runner in BOTH:
            with self.subTest(runner=runner):
                text, initial_status, state = self.run_and_read_status(
                    runner, ["--full-auto"]
                )
                self.assertIn("- Status: auto-approved", text)
                self.assertEqual(initial_status, "auto-approved")
                self.assertIs(state["options"]["full_auto"], True)
                self.assertIs(
                    state["options"]["unattended"],
                    True,
                    "spec :134: --full-auto implies --unattended",
                )

    def test_the_frozen_options_match_across_hosts(self):
        """The `rununify` property at the STATE level, not just the parser level."""
        frozen = {}
        for runner in BOTH:
            _text, _status, state = self.run_and_read_status(runner, [])
            frozen[runner] = {
                row.dest: state["options"][row.dest]
                for row in runner_shared.RUN_POLICY_FLAGS
            }
        self.assertEqual(frozen["oc_runipd"], frozen["agy_runipd"])

    def test_the_mixed_type_gate_ledger_record_is_written(self):
        """Spec 2.5 bullet 4's four facts, durable, on a real run."""
        import json
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo, _plan = self.make_repo(_P(td))
                    args = _parse(runner, ["start", "prb001", "--repo", str(repo)])
                    args.prepare_only = True
                    run_dir = _MODULES[runner].initialize_run(args)
                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl").read_text().splitlines()
                        if line.strip()
                    ]
                    record = next(e for e in events if e["event"] == "mixed-type-gate")
                    for key in (
                        "type_counts",
                        "action_preview",
                        "response_or_flag",
                        "queue_digest",
                    ):
                        self.assertIn(key, record)
                    # Single-type selection: the gate is REACHED and correctly does not APPLY.
                    self.assertFalse(record["gate_applied"])
                    self.assertTrue(record["proceed"])
                    self.assertEqual(record["type_counts"], {"ipd": 1})

    def test_an_unimplemented_flag_refuses_before_a_run_directory_exists(self):
        """E-05 end-to-end: nothing durable is created by a refused invocation."""
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            for flag in ("--with-dependencies", "--follow-generated"):
                with self.subTest(runner=runner, flag=flag):
                    with tempfile.TemporaryDirectory() as td:
                        repo, _plan = self.make_repo(_P(td))
                        args = _parse(
                            runner, ["start", "prb001", "--repo", str(repo), flag]
                        )
                        with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                            _MODULES[runner].initialize_run(args)
                        self.assertIn("not yet implemented", str(ctx.exception))
                        runs = repo / ".aw" / "records" / "runs"
                        self.assertEqual(
                            list(runs.glob("run-*")) if runs.exists() else [],
                            [],
                            "a refused invocation must leave NO durable run state",
                        )

    def test_an_out_of_range_retry_budget_refuses_before_a_run_directory_exists(self):
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo, _plan = self.make_repo(_P(td))
                    args = _parse(
                        runner,
                        [
                            "start",
                            "prb001",
                            "--repo",
                            str(repo),
                            "--retry-budget",
                            "11",
                        ],
                    )
                    with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                        _MODULES[runner].initialize_run(args)
                    self.assertIn("0..10", str(ctx.exception))
                    runs = repo / ".aw" / "records" / "runs"
                    self.assertEqual(
                        list(runs.glob("run-*")) if runs.exists() else [], []
                    )

    def test_unverifiable_ok_alone_refuses_the_whole_run(self):
        import tempfile
        from pathlib import Path as _P

        for runner in BOTH:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as td:
                    repo, _plan = self.make_repo(_P(td))
                    args = _parse(
                        runner,
                        ["start", "prb001", "--repo", str(repo), "--unverifiable-ok"],
                    )
                    with self.assertRaises(runner_shared.RunFlagRefusal) as ctx:
                        _MODULES[runner].initialize_run(args)
                    self.assertIn("--allow-unverifiable", str(ctx.exception))

    def test_the_effective_retry_budget_is_frozen(self):
        for runner in BOTH:
            with self.subTest(runner=runner):
                _t, _s, state = self.run_and_read_status(runner, [])
                self.assertEqual(state["options"]["retry_budget"], 2)
                _t, _s, state = self.run_and_read_status(
                    runner, ["--retry-budget", "0"]
                )
                self.assertEqual(state["options"]["retry_budget"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
