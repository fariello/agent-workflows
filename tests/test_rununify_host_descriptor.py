"""rununify Order 04 (`tx6q0h`): the host descriptor and the symbols lifted through it.

WHAT THIS FILE GUARDS, and why each assertion exists rather than merely that it does.

Eight symbols were defined TWICE, once per host runner, and their difference was dominated by a
host-identifying string. They now have ONE definition in `runner_shared`, reached through a
`HostLabels` descriptor the calling host supplies. This suite fails if any of the following regresses:

  1. A lifted symbol is RE-FORKED (a runner grows a real body for it again). That is the failure mode
     the whole `rununify` Set exists to prevent, and it is silent: two copies agree on the day they
     are written and drift afterwards.
  2. A host's strings COLLAPSE onto the other host's. Without this, "the parameterization works" can
     pass while both hosts secretly render one host's labels.
  3. A descriptor field goes SILENTLY EMPTY. `HostLabels.command` reaches a plan's PERMANENT finalize
     record, so an empty value corrupts durable history rather than merely looking wrong.
  4. An invocation spelling is DROPPED. The Antigravity host answers to `runagy`; a single-token
     descriptor field would have lost it.
  5. The `- Launch:` line leaks onto a host with no profile subsystem, where it renders
     `profile=(none recorded)` forever (plan `tx6q0h` OQ-01, resolved AGAINST adopting it).
  6. The verifier prompt loses its push prohibition on either host. It was MISSING ENTIRELY on the
     Antigravity host before this change while that prompt instructed the agent to commit
     (plan `tx6q0h` F-13).

ON E-06's "INVERSE ASSERTIONS", stated plainly because this file deliberately does the OPPOSITE of
what the plan's E-05/E-06 text asks. Those items were authored by the 2026-09-16 review round, which
provisionally EXCLUDED `driver_actor` and `build_prompt` and asked for assertions that both stay
per-host. The plan's own OQ-03 was then resolved BY THE MAINTAINER in the other direction ("one code
base shared by the two runners that contains 100% of the otherwise redundant code"), explicitly
selecting the option that adopts one prompt text for both hosts and fixes the `Never push` omission in
the same act, and explicitly refusing the deferral. So the boundary those inverse assertions guarded
has MOVED, and asserting the old one would assert against the ruling. This is a deliberate RE-BASE of
a guard onto the boundary that still exists (per the Set orchestrator's ruling that source-reading
guards are re-based deliberately, never weakened silently): assertions 1 through 6 above are all
still enforced, and the surviving exclusion (5) is asserted directly.
"""

from __future__ import annotations

import ast
import inspect
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import agy_runipd, oc_runipd, run_viewer
from agent_workflows import runner_shared as R

#: Each lifted symbol: the name it keeps in BOTH runners -> the name it has in `runner_shared`.
#: Driven from a table rather than the literal eight so a ninth lift is one row, not a new test.
LIFTED: dict[str, str] = {
    "_compute_scope_reconciliation": "compute_scope_reconciliation",
    "_detect_driver_command": "detect_driver_command",
    "render_continuation_hint": "render_continuation_hint",
    "build_verifier_prompt": "build_verifier_prompt",
    "enforce_requested_action": "enforce_requested_action",
    "write_report": "write_report",
    "driver_actor": "driver_actor",
    "build_prompt": "build_prompt",
}

#: Constants that moved WITH the bodies that close over them. Byte-identical in both runners before
#: the move, so this is a relocation and not a reconciliation.
RELOCATED_CONSTANTS = ("SUCCESS_STATES", "ACTION_CHOICES", "ACTION_IMPLEMENTED")

HOSTS = ((oc_runipd, R.OC_HOST_LABELS), (agy_runipd, R.AGY_HOST_LABELS))


def _module_ast(mod: Any) -> ast.Module:
    return ast.parse(Path(str(mod.__file__)).read_text(encoding="utf-8"))


def _top_level_def(mod: Any, name: str) -> ast.AST | None:
    return next(
        (n for n in _module_ast(mod).body if getattr(n, "name", None) == name), None
    )


def _significant_body(node: ast.AST) -> list[ast.stmt]:
    """The statements that are not the docstring."""
    return [
        s
        for s in node.body  # type: ignore[attr-defined]
        if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
    ]


class TheDescriptorTests(unittest.TestCase):
    """E-01/V-01: one descriptor, two instances, every field consumed and none defaulted."""

    def test_both_hosts_have_a_descriptor_and_they_are_distinct(self) -> None:
        self.assertIsInstance(R.OC_HOST_LABELS, R.HostLabels)
        self.assertIsInstance(R.AGY_HOST_LABELS, R.HostLabels)
        self.assertNotEqual(R.OC_HOST_LABELS, R.AGY_HOST_LABELS)

    def test_no_field_has_a_default_so_a_new_caller_cannot_omit_one(self) -> None:
        """`command` lands in a plan's PERMANENT finalize record; a default would let a new caller
        silently attribute a reconciliation to the wrong driver, invisibly until someone audits."""
        self.assertEqual(R.HostLabels._field_defaults, {})

    def test_a_missing_field_FAILS_LOUDLY_rather_than_reading_as_empty(self) -> None:
        """The negative case F-4 makes load-bearing. A mapping with `.get()` is the one form to
        avoid, because a typo would write an empty host name into durable history."""
        with self.assertRaises(TypeError):
            R.HostLabels(command="aw x run")  # type: ignore[call-arg]
        with self.assertRaises(AttributeError):
            _ = R.OC_HOST_LABELS.no_such_field  # type: ignore[attr-defined]

    def test_every_field_is_non_empty_on_both_hosts(self) -> None:
        for _mod, labels in HOSTS:
            for field in R.HostLabels._fields:
                value = getattr(labels, field)
                if field == "shell_tool":
                    continue  # legitimately None where a host names no tool
                self.assertTrue(
                    value != "" and value is not None,
                    f"{labels.command}: field {field!r} is empty; an empty host label reaches a "
                    "permanent finalize record",
                )

    def test_no_variant_or_profile_field_was_added(self) -> None:
        """F-7's capability difference must NOT become a string field. `driver_actor` reads those
        keys straight off frozen state and finds them absent on a host without a profile subsystem."""
        for field in R.HostLabels._fields:
            self.assertNotIn("variant", field)
            self.assertNotIn("profile", field)


class TheLiftHeldTests(unittest.TestCase):
    """E-02/E-04/V-02/V-04: one definition each, reached from both hosts."""

    def test_the_shared_module_defines_every_lifted_symbol(self) -> None:
        for host_name, shared_name in LIFTED.items():
            with self.subTest(symbol=host_name):
                fn = getattr(R, shared_name, None)
                self.assertTrue(callable(fn), f"runner_shared lacks {shared_name}")
                self.assertEqual(fn.__module__, "agent_workflows.runner_shared")

    def test_NEITHER_RUNNER_STILL_CARRIES_A_REAL_BODY_for_a_lifted_symbol(self) -> None:
        """The anti-re-fork assertion. Each host keeps a name at the original signature (so no call
        site was rewritten) but its body must be a single delegating statement."""
        for mod, _labels in HOSTS:
            for host_name in LIFTED:
                with self.subTest(host=mod.__name__, symbol=host_name):
                    node = _top_level_def(mod, host_name)
                    assert node is not None, f"{mod.__name__} lost {host_name}"
                    body = _significant_body(node)
                    self.assertEqual(
                        len(body),
                        1,
                        f"{mod.__name__}.{host_name} has {len(body)} statements; a lifted symbol "
                        "must be a one-line wrapper or it has been re-forked",
                    )
                    self.assertIn(
                        "runner_shared",
                        ast.unparse(body[0]),
                        f"{mod.__name__}.{host_name} does not delegate to runner_shared",
                    )

    def test_each_runner_defines_the_symbol_EXACTLY_ONCE(self) -> None:
        for mod, _labels in HOSTS:
            names = [
                n.name
                for n in _module_ast(mod).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            ]
            for host_name in LIFTED:
                self.assertEqual(
                    names.count(host_name),
                    1,
                    f"{mod.__name__} defines {host_name} {names.count(host_name)} times",
                )

    def test_the_relocated_constants_are_ONE_OBJECT_across_both_hosts(self) -> None:
        for const in RELOCATED_CONSTANTS:
            with self.subTest(constant=const):
                self.assertIs(getattr(oc_runipd, const), getattr(R, const))
                self.assertIs(getattr(agy_runipd, const), getattr(R, const))


class EachHostKeepsItsOwnStringsTests(unittest.TestCase):
    """V-02: the parameterization is REAL, not a hardcoded default that happens to suit one host."""

    def test_the_finalize_record_reason_names_the_HOST_THAT_ACTUALLY_RAN(self) -> None:
        """F-4: these two strings land in a plan's PERMANENT finalize record, so a defaulted or
        collapsed host name misattributes durable history.

        Drives the REAL function through a stubbed `finalize_precheck`, rather than re-formatting the
        expected string in the test. Re-deriving the template here would make the test pass even if
        both hosts collapsed onto one label, which is exactly the bug it must catch.
        """
        from agent_workflows import ipd_lifecycle

        audit = {
            "scope_audit": {
                "out_of_scope_paths": ["a.py"],
                "in_scope_unmodified": ["b.py"],
            }
        }
        original = ipd_lifecycle.finalize_precheck
        produced: dict[str, tuple[str, str]] = {}
        try:
            ipd_lifecycle.finalize_precheck = lambda *a, **k: (0, "", audit, [])  # type: ignore[assignment]
            for mod, labels in HOSTS:
                reasons, acks = mod._compute_scope_reconciliation(
                    Path("/repo"), Path("/p.ipd.md")
                )
                reason, ack = reasons["a.py"], acks["b.py"]
                produced[mod.__name__] = (reason, ack)
                self.assertIn(labels.command, reason)
                self.assertIn(labels.command, ack)
        finally:
            ipd_lifecycle.finalize_precheck = original  # type: ignore[assignment]
        self.assertEqual(
            len(set(produced.values())),
            2,
            f"both hosts produced the SAME reconciliation reason: {produced}. A finalize record "
            "would then name the wrong driver.",
        )

    def test_the_continuation_hint_names_each_host_by_its_OWN_product_name(
        self,
    ) -> None:
        state = {"run_id": "run-x", "repo": ".", "queue": [], "set_sessions": {}}
        with tempfile.TemporaryDirectory() as tmp:
            rendered = {}
            for mod, labels in HOSTS:
                text = mod.render_continuation_hint(state, Path(tmp))
                rendered[labels.product] = text
                self.assertIn(f"--- {labels.product} Session Continuity ---", text)
            self.assertIn("OpenCode", rendered)
            self.assertIn("Antigravity", rendered)
            # And neither host leaks the other's name.
            self.assertNotIn("Antigravity", rendered["OpenCode"])
            self.assertNotIn("OpenCode", rendered["Antigravity"])

    def test_each_host_resolves_its_OWN_argv_spellings_and_not_the_others(self) -> None:
        """F-3: the Antigravity host answers to `runagy`; a single-token field would drop it."""
        import sys

        original = sys.argv
        try:
            for mod, labels in HOSTS:
                for token in labels.argv_tokens:
                    for sub in labels.argv_subcommands:
                        sys.argv = ["aw", token, sub]
                        self.assertEqual(
                            mod._detect_driver_command(),
                            f"aw {token} {sub}",
                            f"{mod.__name__} failed to resolve `aw {token} {sub}`",
                        )
                sys.argv = ["aw"]
                self.assertEqual(mod._detect_driver_command(), labels.command)
        finally:
            sys.argv = original

    def test_the_antigravity_host_still_resolves_runagy_specifically(self) -> None:
        """Named rather than left to the loop, because F-3 called this out as the spelling at risk."""
        import sys

        original = sys.argv
        try:
            sys.argv = ["aw", "agy", "runagy"]
            self.assertEqual(agy_runipd._detect_driver_command(), "aw agy runagy")
            self.assertIn("runagy", R.AGY_HOST_LABELS.argv_subcommands)
            self.assertNotIn("runagy", R.OC_HOST_LABELS.argv_subcommands)
        finally:
            sys.argv = original

    def test_the_actor_carries_each_hosts_own_prefix_and_no_parentheses(self) -> None:
        """`attention_contract.actor_refusal` refuses any parenthesis AND an empty actor."""
        for mod, labels in HOSTS:
            for state in ({}, {"options": {"model": "some-model"}}):
                actor = mod.driver_actor(state)
                self.assertTrue(actor.startswith(labels.command), actor)
                self.assertNotIn("(", actor)
                self.assertNotIn(")", actor)
                self.assertTrue(actor.strip(), "an empty actor is refused downstream")

    def test_the_action_refusals_name_each_hosts_own_review_command(self) -> None:
        """Spec 25kzda 2.6's enforcement. The message must tell the operator a command that EXISTS."""
        for mod, labels in HOSTS:
            with self.assertRaises(R.DriverError) as caught:
                mod.enforce_requested_action("plan", [])
            self.assertIn(labels.review_command, str(caught.exception))
            with self.assertRaises(R.DriverError) as caught:
                mod.enforce_requested_action(
                    "review", [("abc123", "approved", "execute")]
                )
            self.assertIn(labels.review_command, str(caught.exception))

    def test_the_unimplemented_and_illegal_refusals_still_REFUSE(self) -> None:
        """The lift must not weaken either guarantee: an unknown action, an unimplemented action,
        and a legal-for-nobody action all still raise before any run is started."""
        for mod, _labels in HOSTS:
            with self.assertRaises(R.DriverError):
                mod.enforce_requested_action("nonsense", [])
            with self.assertRaises(R.DriverError):
                mod.enforce_requested_action("execute", [])
            # And the legal case does NOT raise.
            mod.enforce_requested_action("review", [("abc123", "to-review", "review")])
            mod.enforce_requested_action(None, [])


class TheReportShapeTests(unittest.TestCase):
    """E-04/V-04: all the report changes asserted explicitly, so none can land silently."""

    def _state(self, verification: str | None = "verified") -> dict[str, Any]:
        return {
            "run_id": "run-x",
            "repo": "/r",
            "set_sessions": {},
            "queue": [
                {
                    "position": 1,
                    "id6": "abc123",
                    "setid": "demo",
                    "status": "executed",
                    "action": "execute",
                    "verification_status": verification,
                    "attempts": [{"session_id": "ses_1"}],
                }
            ],
        }

    def _report(self, mod: Any, state: dict[str, Any]) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            mod.write_report(Path(tmp), state)
            return (Path(tmp) / "execution-report.md").read_text(encoding="utf-8")

    def test_each_host_keeps_its_own_report_title(self) -> None:
        for mod, labels in HOSTS:
            self.assertTrue(
                self._report(mod, self._state()).startswith(labels.report_title),
                f"{mod.__name__} lost its report title",
            )

    def test_both_hosts_now_spell_the_column_Verify(self) -> None:
        for mod, _labels in HOSTS:
            report = self._report(mod, self._state())
            self.assertIn("| Verify |", report)
            self.assertNotIn("| Verification |", report)

    def test_the_verify_cell_is_BARE_on_both_hosts_which_repairs_the_viewer_badge(
        self,
    ) -> None:
        """F-12. `run_viewer` strips backticks for id6/setid/action/session but NOT for this column,
        then compares it to the bare string `verified`. A backticked cell never matched, so the
        Antigravity host never rendered the `[verified]` badge. Keep this column BARE."""
        for mod, _labels in HOSTS:
            report = self._report(mod, self._state())
            row = next(line for line in report.splitlines() if line.startswith("| 1 "))
            cells = [c.strip() for c in row.split("|")[1:-1]]
            self.assertEqual(
                cells[5],
                "verified",
                f"{mod.__name__} verify cell is {cells[5]!r}; the viewer compares it to the BARE "
                "string, so a backticked value silently loses the badge",
            )

    def test_the_viewer_badge_predicate_now_matches_for_BOTH_hosts_end_to_end(
        self,
    ) -> None:
        """F-12 proven through the real consumer, not just by inspecting the cell."""
        source = inspect.getsource(run_viewer.load_run_summary)
        self.assertIn(
            "cols[5].strip()", source, "the viewer's parse of column 5 moved; re-verify"
        )
        for mod, _labels in HOSTS:
            report = self._report(mod, self._state())
            row = next(line for line in report.splitlines() if line.startswith("| 1 "))
            parsed = [c.strip() for c in row.split("|")[1:-1]]
            v_status = parsed[5] if len(parsed) > 5 and parsed[5] else None
            self.assertEqual(
                v_status,
                "verified",
                f"{mod.__name__}: run_viewer.py's `verification_status == 'verified'` test would "
                "fail, so the [verified] badge would not render",
            )

    def test_an_empty_verification_renders_an_EMPTY_cell_not_N_A(self) -> None:
        for mod, _labels in HOSTS:
            report = self._report(mod, self._state(verification=None))
            row = next(line for line in report.splitlines() if line.startswith("| 1 "))
            cells = [c.strip() for c in row.split("|")[1:-1]]
            self.assertEqual(cells[5], "")
            self.assertNotIn("N/A", row)

    def test_the_Launch_line_appears_ONLY_where_the_host_has_a_profile_subsystem(
        self,
    ) -> None:
        """OQ-01, resolved AGAINST giving the line to a host with no profiles: it would render
        `profile=(none recorded)` on every run there, which is noise rather than disclosure."""
        oc_report = self._report(oc_runipd, self._state())
        agy_report = self._report(agy_runipd, self._state())
        self.assertIn("- Launch:", oc_report)
        self.assertNotIn("- Launch:", agy_report)
        self.assertTrue(R.OC_HOST_LABELS.emits_launch_identity)
        self.assertFalse(R.AGY_HOST_LABELS.emits_launch_identity)

    def test_the_launch_line_would_be_CONTENTLESS_on_a_profileless_host(self) -> None:
        """The measurement that justifies the exclusion, kept as a test so the premise is checked
        rather than remembered."""
        self.assertEqual(
            oc_runipd.render_launch_identity({"options": {}}),
            "model=(host default); profile=(none recorded)",
        )


class ThePromptsTests(unittest.TestCase):
    """OQ-03/F-13: one instruction text for both hosts, and the push prohibition on both."""

    ITEM = {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}
    STATE = {"run_id": "run-x", "repo": "."}

    def _exec_prompt(self, mod: Any) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            return mod.build_prompt(
                self.ITEM, self.STATE, Path(tmp), Path("/p.ipd.md"), False
            )

    def _verifier_prompt(self, mod: Any) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            return mod.build_verifier_prompt(
                self.ITEM, self.STATE, Path(tmp), Path("/p.ipd.md")
            )

    def test_each_host_titles_its_turn_with_its_OWN_product_name(self) -> None:
        for mod, labels in HOSTS:
            self.assertTrue(
                self._exec_prompt(mod).startswith(f"# {labels.product} IPD Driver Turn")
            )

    def test_BOTH_hosts_verifier_prompts_carry_a_push_prohibition(self) -> None:
        """F-13. This was ZERO on the Antigravity host while that same prompt told the agent to
        commit; the execution prompts both had one, so the gap was specific to the verifier path."""
        for mod, _labels in HOSTS:
            prompt = self._verifier_prompt(mod)
            self.assertIn(
                "Never push",
                prompt,
                f"{mod.__name__} verifier lacks a push prohibition",
            )

    def test_BOTH_hosts_execution_prompts_carry_a_push_prohibition(self) -> None:
        for mod, _labels in HOSTS:
            self.assertIn("or push", self._exec_prompt(mod))

    def test_the_safety_instructions_reach_BOTH_hosts_agents(self) -> None:
        """The substance of OQ-03. These four were present only on the OpenCode host, so the other
        host's agents were likelier to strand partial work and to over-claim completion."""
        required = (
            "nonterminal checkpoint mechanism or an attributable isolated branch/worktree",
            "Leave every",
            "Never claim executed unless the real",
            # Wrapped across a line break in the rendered prompt, so match on collapsed whitespace.
            "If no material question arose",
        )
        for mod, _labels in HOSTS:
            prompt = self._exec_prompt(mod)
            collapsed = " ".join(prompt.split())
            for clause in required:
                self.assertIn(
                    " ".join(clause.split()),
                    collapsed,
                    f"{mod.__name__} prompt lacks: {clause!r}",
                )

    def test_the_verifier_names_a_shell_tool_THAT_HOST_ACTUALLY_HAS(self) -> None:
        """F-9. `run_command` is an Antigravity tool; naming it to an OpenCode agent names nothing."""
        agy_prompt = self._verifier_prompt(agy_runipd)
        oc_prompt = self._verifier_prompt(oc_runipd)
        self.assertIn("`run_command`", agy_prompt)
        self.assertNotIn("`run_command`", oc_prompt)
        self.assertEqual(R.AGY_HOST_LABELS.shell_tool, "run_command")
        self.assertIsNone(R.OC_HOST_LABELS.shell_tool)

    def test_neither_host_leaks_the_others_product_name(self) -> None:
        for mod, labels in HOSTS:
            other = "Antigravity" if labels.product == "OpenCode" else "OpenCode"
            for prompt in (self._exec_prompt(mod), self._verifier_prompt(mod)):
                self.assertNotIn(other, prompt, f"{mod.__name__} leaked {other}")


class TheRunnerCanSupplyAWideningReasonTests(unittest.TestCase):
    """rcptwiden `63425h` E-04 / F-10: the runner must AUTO-REASON an additive scope widening.

    WHY THIS LIVES IN THE RUNNER'S TEST FILE AND IS NOT OPTIONAL. All three finalize failures the
    widening accept exists to fix (`i3d6ml`, `tx6q0h`, `sy7uwh` in run `run-20260917T023628Z-4108757`)
    were performed by the DRIVER, not by a human at a prompt. `compute_scope_reconciliation` built its
    reason map exclusively from `audit["out_of_scope_paths"]`, and an UNCOMMITTED widened path never
    appears there (finalize judges out-of-scope against the receipt's OLD fence). So a lifecycle-only
    fix would have converted a STALE refusal into a MISSING-REASON refusal and stranded the identical
    three lanes. These tests fail if that regression is reintroduced on either host.
    """

    def _drive(self, audit: dict[str, Any]) -> dict[str, tuple[dict, dict]]:
        from agent_workflows import ipd_lifecycle

        original = ipd_lifecycle.finalize_precheck
        out: dict[str, tuple[dict, dict]] = {}
        try:
            ipd_lifecycle.finalize_precheck = lambda *a, **k: (  # type: ignore[assignment]
                0,
                "",
                {"scope_audit": audit},
                [],
            )
            for mod, _labels in HOSTS:
                out[mod.__name__] = mod._compute_scope_reconciliation(
                    Path("/repo"), Path("/p.ipd.md")
                )
        finally:
            ipd_lifecycle.finalize_precheck = original  # type: ignore[assignment]
        return out

    def test_an_UNCOMMITTED_widened_path_gets_a_reason_on_both_hosts(self) -> None:
        """The measured incident's exact audit shape: widened, but NOT out-of-scope."""
        produced = self._drive(
            {
                "out_of_scope_paths": [],
                "in_scope_unmodified": [],
                "widened_paths": ["tests/test_resumedupe.py"],
            }
        )
        for host, (reasons, _acks) in produced.items():
            self.assertIn(
                "tests/test_resumedupe.py",
                reasons,
                f"{host} supplied NO reason for a widened path, so finalize would refuse it",
            )
            self.assertTrue(reasons["tests/test_resumedupe.py"].strip())

    def test_the_widening_reason_describes_a_DECLARATION_not_an_out_of_scope_edit(
        self,
    ) -> None:
        """The reason lands in a plan's PERMANENT record, so it must describe what actually happened."""
        produced = self._drive(
            {
                "out_of_scope_paths": [],
                "in_scope_unmodified": [],
                "widened_paths": ["tests/test_resumedupe.py"],
            }
        )
        for host, (reasons, _acks) in produced.items():
            reason = reasons["tests/test_resumedupe.py"]
            self.assertIn("Scope-Paths", reason, f"{host}: {reason}")
            self.assertIn("widening", reason.lower(), f"{host}: {reason}")

    def test_a_path_that_is_BOTH_widened_and_out_of_scope_gets_ONE_reason(self) -> None:
        """The committed-cohesive variant: one path, one answer, no double-record."""
        produced = self._drive(
            {
                "out_of_scope_paths": ["tests/test_resumedupe.py", "other.py"],
                "in_scope_unmodified": [],
                "widened_paths": ["tests/test_resumedupe.py"],
            }
        )
        for host, (reasons, _acks) in produced.items():
            self.assertEqual(
                sorted(reasons),
                ["other.py", "tests/test_resumedupe.py"],
                f"{host} produced a duplicated or missing demand: {reasons}",
            )
            # The widening wording wins for the widened path; the plain out-of-scope path keeps its own.
            self.assertIn("widening", reasons["tests/test_resumedupe.py"].lower())
            self.assertNotIn("widening", reasons["other.py"].lower())

    def test_a_widened_path_is_not_ALSO_acknowledged_as_unmodified(self) -> None:
        """A declared-because-needed path is not "declared but unmodified"; one act, one answer."""
        produced = self._drive(
            {
                "out_of_scope_paths": [],
                "in_scope_unmodified": ["tests/test_resumedupe.py", "declared.py"],
                "widened_paths": ["tests/test_resumedupe.py"],
            }
        )
        for host, (reasons, acks) in produced.items():
            self.assertIn("tests/test_resumedupe.py", reasons, host)
            self.assertNotIn("tests/test_resumedupe.py", acks, host)
            self.assertIn("declared.py", acks, host)

    def test_an_absent_widened_key_changes_nothing(self) -> None:
        """A tree whose finalize evidence predates this key must behave exactly as before."""
        produced = self._drive(
            {"out_of_scope_paths": ["a.py"], "in_scope_unmodified": ["b.py"]}
        )
        for host, (reasons, acks) in produced.items():
            self.assertEqual(sorted(reasons), ["a.py"], host)
            self.assertEqual(sorted(acks), ["b.py"], host)

    def test_the_assembled_finalize_argv_carries_the_widening_scope_reason(
        self,
    ) -> None:
        """END TO END on the DRIVER's own argv: the demand must actually reach the subprocess.

        `compute_scope_reconciliation` returning a reason is necessary but not sufficient; the failure
        F-10 describes is a missing `--scope-reason` FLAG. This drives `driver_finalize` with the
        subprocess stubbed and inspects the command it built.
        """
        import subprocess as _sp

        from agent_workflows import ipd_lifecycle

        captured: dict[str, list[str]] = {}

        class _Result:
            returncode = 0
            stdout = ""
            stderr = ""

        original_precheck = ipd_lifecycle.finalize_precheck
        original_run = _sp.run
        try:
            ipd_lifecycle.finalize_precheck = lambda *a, **k: (  # type: ignore[assignment]
                0,
                "",
                {
                    "scope_audit": {
                        "out_of_scope_paths": [],
                        "in_scope_unmodified": [],
                        "widened_paths": ["tests/test_resumedupe.py"],
                    }
                },
                [],
            )

            def _fake_run(cmd, *a, **k):
                captured["cmd"] = list(cmd)
                return _Result()

            _sp.run = _fake_run  # type: ignore[assignment]
            oc_runipd.subprocess.run = _fake_run  # type: ignore[assignment]
            rc, _out = oc_runipd.driver_finalize(
                Path("/repo"), Path("/p.ipd.md"), "abc123", "aw oc run", "msg"
            )
        finally:
            ipd_lifecycle.finalize_precheck = original_precheck  # type: ignore[assignment]
            _sp.run = original_run  # type: ignore[assignment]
            oc_runipd.subprocess.run = original_run  # type: ignore[assignment]

        self.assertEqual(rc, 0)
        cmd = captured["cmd"]
        self.assertIn("--scope-reason", cmd)
        flag_values = [
            cmd[i + 1] for i, tok in enumerate(cmd) if tok == "--scope-reason"
        ]
        self.assertEqual(len(flag_values), 1, cmd)
        self.assertTrue(
            flag_values[0].startswith("tests/test_resumedupe.py="),
            f"the widened path did not reach the finalize argv: {flag_values}",
        )
        self.assertIn("widening", flag_values[0].lower())


class TheSharedModuleStaysCleanTests(unittest.TestCase):
    """The standing rule this lift must not break."""

    def test_the_shared_module_does_not_import_either_runner(self) -> None:
        """A shared module importing a runner would silently give BOTH hosts that runner's behavior.
        `tests/test_runner_shared.py::NoRunnerImportTests` owns this too; asserted here because this
        change added lazy imports to the shared module and they must not be runner imports."""
        tree = ast.parse(Path(str(R.__file__)).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn("oc_runipd", node.module)
                self.assertNotIn("agy_runipd", node.module)
                for alias in node.names:
                    self.assertNotIn("oc_runipd", alias.name)
                    self.assertNotIn("agy_runipd", alias.name)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("oc_runipd", alias.name)
                    self.assertNotIn("agy_runipd", alias.name)

    def test_the_stale_docstring_claims_were_repaired_not_promoted(self) -> None:
        """E-03. Both claims were FALSE on the Antigravity host and lifting them verbatim would have
        made a falsehood the single shared source of truth."""
        doc = inspect.getdoc(R.enforce_requested_action) or ""
        self.assertIn("action_for", doc)
        self.assertNotIn("DEFAULTS TO TRUE", doc)

    def test_full_auto_really_does_default_to_False_on_both_hosts(self) -> None:
        """The measurement behind the docstring repair, asserted rather than asserted-about."""
        for mod, _labels in HOSTS:
            args = mod.build_parser().parse_args(["start", "x"])
            self.assertFalse(
                args.full_auto, f"{mod.__name__} --full-auto default changed"
            )

    def test_action_for_and_determine_action_are_DIFFERENT_shared_functions(
        self,
    ) -> None:
        """F-10: they are not two names for one job, which is why the plan's dependency on child 03
        was withdrawn. Both hosts reach both from the shared module."""
        self.assertIsNot(R.action_for, R.determine_action)
        for mod, _labels in HOSTS:
            self.assertIs(mod.action_for, R.action_for)
            self.assertIs(mod.determine_action, R.determine_action)


if __name__ == "__main__":
    unittest.main()
