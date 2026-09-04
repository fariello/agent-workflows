"""Self-tests for the runner-safety capability extension and the fail-closed action preflight.

hostcap-01 (`mjx7ne`) E-01..E-06 / V-01..V-06. Covers:

- E-01 the three new capability fields and their CONSERVATIVE (not-supported) defaults;
- E-02 the `supports_fresh_verifier_session` probe's supported/not-supported paths, and the
  DECLARED-AND-NOT-PROBED verdict (plus its recorded reason) for the two capabilities whose
  enforcement does not exist in this repository;
- E-03 the forced-verdict test seam, including that a forced verdict cannot leak;
- E-04 the action-to-capability requirement map (spec 25kzda 5.2's FOUR action classes) and a
  checker that names EVERY missing capability;
- E-05 the fail-closed `RUN-HOST-CAPABILITY` refusal, its VERBATIM spec message including the
  recovery command, and its ITEM-LOCAL semantics (fail item, cascade dependents, do NOT abort);
- E-06 the two read-only inspection verbs and their `CommandDeclaration`s.

FALSIFIABILITY. The gate is demonstrated in BOTH directions: an action REFUSED when a required
capability is unsupported, and the SAME action PROCEEDING when it is supported. A happy-path-only
test would not show a gate at all.
"""

from __future__ import annotations

import argparse
import io
import json
import unittest
from contextlib import redirect_stdout

from agent_workflows import host_cmd
from agent_workflows import host_sandbox_profile as hsp
from agent_workflows.host_sandbox_profile import (
    ACTION_CAPABILITY_REQUIREMENTS,
    ACTION_CLASSES,
    ACTION_CONTRACTLESS_PROMPT,
    ACTION_MUTATE,
    ACTION_READ_ONLY,
    ACTION_REVIEW,
    CAP_COMMIT_GATEWAY,
    CAP_DENY_PUSH,
    CAP_FRESH_VERIFIER_SESSION,
    OUTCOME_FAILED,
    REASON_HOST_CAPABILITY_UNAVAILABLE,
    RUN_HOST_CAPABILITY,
    RUNNER_SAFETY_CAPABILITIES,
    UNREPRESENTED_SPEC_CAPABILITIES,
    HostSandboxCapabilities,
    UnknownActionError,
    check_action_capabilities,
    detect_host_capabilities,
    format_host_capability_finding,
    forced_runner_safety_verdicts,
    preflight_host_capabilities,
    probe_runner_safety_capabilities,
)

#: The spec's VERBATIM message (spec 25kzda `:534` and `:763`), transcribed here so the test
#: compares the implementation against the SPEC rather than against itself.
SPEC_MESSAGE = (
    "[RUN-HOST-CAPABILITY] Host <host> cannot enforce <capability> required by <item> "
    "action <action>. No work started for this item. Choose a capable host or enable and "
    "re-probe that capability, then run: aw <host> run <selector>"
)


def _fully_capable() -> HostSandboxCapabilities:
    """A descriptor with every runner-safety capability supported (the PROCEEDS side)."""
    caps = HostSandboxCapabilities(platform="linux")
    for name in RUNNER_SAFETY_CAPABILITIES:
        setattr(caps, name, True)
    return caps


class NewContractFieldTests(unittest.TestCase):
    """E-01: the three fields exist and default CONSERVATIVE (not-supported)."""

    def test_the_three_runner_safety_fields_default_not_supported(self):
        caps = HostSandboxCapabilities()
        for name in (CAP_COMMIT_GATEWAY, CAP_DENY_PUSH, CAP_FRESH_VERIFIER_SESSION):
            with self.subTest(field=name):
                self.assertIs(
                    getattr(caps, name),
                    False,
                    f"{name} must default False so an unprobed host is treated as LACKING "
                    "the guarantee rather than having it",
                )

    def test_a_descriptor_built_with_no_probes_reports_all_three_unsupported(self):
        snap = HostSandboxCapabilities().to_dict()
        for name in RUNNER_SAFETY_CAPABILITIES:
            self.assertIn(name, snap, "the new fields must appear in the snapshot")
            self.assertFalse(snap[name])

    def test_the_shipped_contract_tuple_covers_the_new_fields(self):
        """The shipped default-False guarantee is driven by a LITERAL tuple, not introspection.

        Without this, appending fields to the dataclass leaves them untested while
        `tests/test_host_sandbox_profile.py` stays green (F8).
        """
        from tests.test_host_sandbox_profile import CONTRACT_FIELDS

        for name in RUNNER_SAFETY_CAPABILITIES:
            self.assertIn(
                name,
                CONTRACT_FIELDS,
                "the new field is invisible to the shipped conservative-default guarantee",
            )

    def test_the_shipped_sandbox_fields_are_neither_renamed_nor_reordered(self):
        """`1o4eif`'s dispatch reads these by name and its 27 tests pin them."""
        import dataclasses

        names = [f.name for f in dataclasses.fields(HostSandboxCapabilities)]
        self.assertEqual(
            names[:7],
            [
                "supports_inline_permissions",
                "supports_read_only_phase",
                "supports_session_resume",
                "emits_structured_tool_events",
                "emits_child_permission_events",
                "supports_process_tree_kill",
                "supports_os_sandbox",
            ],
        )


class RunnerSafetyProbeTests(unittest.TestCase):
    """E-02: attempt-based where there is something to attempt; declared where there is not."""

    def test_fresh_verifier_probe_reports_supported_from_an_observation(self):
        ok, note = hsp._probe_fresh_verifier_session()
        self.assertTrue(ok, f"probe reported not-supported: {note}")
        # The note must record BOTH halves: a contract that never refuses enforces nothing.
        self.assertIn("REFUSED", note)
        self.assertIn("finalized", note)

    def test_fresh_verifier_probe_requires_the_reused_identity_to_be_REFUSED(self):
        """A contract that ACCEPTS a reused session identity must report not-supported.

        This is the fail-OPEN direction: separation would be claimed with no separation.
        Simulated by patching the collision guard away, which is exactly the defect.
        """
        from agent_workflows import agy_verifier as agy

        real = agy.run_fresh_verifier

        def never_refuses(packet, **kwargs):
            kwargs.pop("execution_session", None)
            verifier = kwargs.pop("verifier_session")
            # Always succeed, whatever identities were passed: no separation enforced.
            return real(
                packet,
                execution_session=agy.SessionIdentity(
                    session_id="distinct-executor", role="executor"
                ),
                verifier_session=verifier,
                **kwargs,
            )

        agy.run_fresh_verifier = never_refuses  # type: ignore[assignment]
        try:
            ok, note = hsp._probe_fresh_verifier_session()
        finally:
            agy.run_fresh_verifier = real  # type: ignore[assignment]
        self.assertFalse(ok, "a contract that never refuses must not report supported")
        self.assertIn("reused session identity", note)

    def test_a_raising_probe_yields_not_supported(self):
        saved = dict(hsp._RUNNER_SAFETY_PROBES)

        def boom():
            raise RuntimeError("probe exploded")

        hsp._RUNNER_SAFETY_PROBES[CAP_FRESH_VERIFIER_SESSION] = boom
        try:
            verdicts, notes = probe_runner_safety_capabilities()
        finally:
            hsp._RUNNER_SAFETY_PROBES.clear()
            hsp._RUNNER_SAFETY_PROBES.update(saved)
        self.assertFalse(verdicts[CAP_FRESH_VERIFIER_SESSION])
        self.assertIn("probe raised RuntimeError", notes[CAP_FRESH_VERIFIER_SESSION])

    def test_the_two_unenforced_capabilities_are_declared_and_not_probed(self):
        """OQ-03 option (a): declared False with a `probe_notes` entry saying so.

        A presence-based probe inferring support from `git_commit_helper.offer_commit` is
        FORBIDDEN, so these MUST have no probe at all.
        """
        verdicts, notes = probe_runner_safety_capabilities()
        for name in (CAP_COMMIT_GATEWAY, CAP_DENY_PUSH):
            with self.subTest(capability=name):
                self.assertIsNone(
                    hsp._RUNNER_SAFETY_PROBES[name],
                    "there is nothing to attempt, so there must be no probe",
                )
                self.assertFalse(verdicts[name])
                self.assertIn("DECLARED, NOT PROBED", notes[name])

    def test_no_runner_safety_probe_infers_support_from_helper_presence(self):
        """Structural: the probe module must not reach for the driver-side commit helper."""
        import inspect

        src = inspect.getsource(hsp)
        for forbidden in ("offer_commit", "git_commit_helper"):
            # Mentioned in the fail-OPEN explanation prose, but never as code that decides a
            # verdict: no probe may import or call it.
            self.assertNotIn(
                f"import {forbidden}",
                src,
                "a presence-based probe over the driver-side helper is forbidden",
            )

    def test_detect_host_capabilities_records_the_probe_notes(self):
        caps = detect_host_capabilities("opencode")
        for name in RUNNER_SAFETY_CAPABILITIES:
            self.assertIn(
                name,
                caps.probe_notes,
                "every runner-safety verdict must publish its evidence",
            )

    def test_a_platform_we_are_not_running_on_asserts_nothing(self):
        caps = detect_host_capabilities("opencode", "win32")
        for name in RUNNER_SAFETY_CAPABILITIES:
            self.assertFalse(
                getattr(caps, name),
                "a capability cannot be probed for a platform we are not on",
            )


class MockSeamTests(unittest.TestCase):
    """E-03: force any capability to any verdict without owning the host."""

    def test_the_seam_can_force_each_verdict(self):
        for forced in (True, False):
            with self.subTest(forced=forced):
                with forced_runner_safety_verdicts(
                    {CAP_COMMIT_GATEWAY: (forced, "forced by test")}
                ):
                    verdicts, notes = probe_runner_safety_capabilities()
                self.assertIs(verdicts[CAP_COMMIT_GATEWAY], forced)
                self.assertIn("FORCED VERDICT", notes[CAP_COMMIT_GATEWAY])

    def test_a_forced_verdict_does_not_leak_out_of_the_context(self):
        """The seam is process-global, so a leak would corrupt every later test."""
        with forced_runner_safety_verdicts({CAP_COMMIT_GATEWAY: (True, "forced")}):
            self.assertTrue(probe_runner_safety_capabilities()[0][CAP_COMMIT_GATEWAY])
        # Back to the REAL value (declared-and-unprobed => False) in the same process.
        verdicts, notes = probe_runner_safety_capabilities()
        self.assertFalse(verdicts[CAP_COMMIT_GATEWAY])
        self.assertIn("DECLARED, NOT PROBED", notes[CAP_COMMIT_GATEWAY])

    def test_the_seam_is_restored_even_when_the_body_raises(self):
        with self.assertRaises(ValueError):
            with forced_runner_safety_verdicts({CAP_DENY_PUSH: (True, "forced")}):
                raise ValueError("boom")
        self.assertFalse(probe_runner_safety_capabilities()[0][CAP_DENY_PUSH])

    def test_the_production_path_is_unchanged_with_no_mock_supplied(self):
        self.assertIsNone(
            hsp._FORCED_RUNNER_SAFETY, "no mock must be installed by default"
        )
        real = probe_runner_safety_capabilities()[0]
        self.assertTrue(real[CAP_FRESH_VERIFIER_SESSION])
        self.assertFalse(real[CAP_COMMIT_GATEWAY])

    def test_a_forced_verdict_flows_through_detect_host_capabilities(self):
        with forced_runner_safety_verdicts({CAP_COMMIT_GATEWAY: (True, "forced")}):
            caps = detect_host_capabilities("opencode")
        self.assertTrue(caps.supports_commit_gateway)
        self.assertFalse(detect_host_capabilities("opencode").supports_commit_gateway)


class RequirementMapTests(unittest.TestCase):
    """E-04: the policy is DATA, keyed by the spec's FOUR action classes."""

    def test_the_map_uses_the_specs_four_action_classes(self):
        self.assertEqual(
            set(ACTION_CAPABILITY_REQUIREMENTS),
            {
                ACTION_READ_ONLY,
                ACTION_REVIEW,
                ACTION_MUTATE,
                ACTION_CONTRACTLESS_PROMPT,
            },
        )
        self.assertEqual(len(ACTION_CLASSES), 4)

    def test_the_map_is_data_not_branching_logic(self):
        for action, req in ACTION_CAPABILITY_REQUIREMENTS.items():
            with self.subTest(action=action):
                self.assertIsInstance(req.required, tuple)
                self.assertIsInstance(req.unrepresented, tuple)
                self.assertTrue(req.spec_basis, "each row must cite its spec basis")
                self.assertIn("25kzda", req.spec_basis)

    def test_every_unrepresented_name_resolves_to_a_recorded_gap(self):
        """A typo here would silently DROP a spec requirement, which is fail-OPEN."""
        for action, req in ACTION_CAPABILITY_REQUIREMENTS.items():
            for name in req.unrepresented:
                with self.subTest(action=action, capability=name):
                    self.assertIn(name, UNREPRESENTED_SPEC_CAPABILITIES)

    def test_every_required_name_is_a_real_contract_field(self):
        caps = HostSandboxCapabilities()
        for action, req in ACTION_CAPABILITY_REQUIREMENTS.items():
            for name in req.required:
                with self.subTest(action=action, capability=name):
                    self.assertTrue(hasattr(caps, name))

    def test_the_mutating_actions_record_the_capabilities_the_contract_cannot_express(
        self,
    ):
        """The spec names eight for review; three are representable, five must be RECORDED."""
        review = ACTION_CAPABILITY_REQUIREMENTS[ACTION_REVIEW]
        self.assertTrue(review.unrepresented, "omitting them would pass silently")
        for name in ("isolated_worktree", "argv_capture", "hook_preserving_commit"):
            self.assertIn(name, review.unrepresented)

    def test_a_read_only_action_requires_nothing_this_contract_represents(self):
        self.assertEqual(ACTION_CAPABILITY_REQUIREMENTS[ACTION_READ_ONLY].required, ())


class CheckerTests(unittest.TestCase):
    """E-04: the checker names EVERY missing capability, not just the first."""

    def test_it_names_multiple_missing_capabilities_in_one_verdict(self):
        caps = HostSandboxCapabilities(platform="linux")  # all three unsupported
        verdict = check_action_capabilities(ACTION_REVIEW, caps, host="opencode")
        self.assertFalse(verdict.satisfied)
        self.assertEqual(
            verdict.missing,
            (CAP_COMMIT_GATEWAY, CAP_DENY_PUSH, CAP_FRESH_VERIFIER_SESSION),
            "all three, in contract order, not just the first",
        )

    def test_a_fully_capable_host_passes_every_action(self):
        caps = _fully_capable()
        for action in ACTION_CLASSES:
            with self.subTest(action=action):
                self.assertTrue(
                    check_action_capabilities(action, caps, host="opencode").satisfied
                )

    def test_the_verdict_carries_the_evidence_for_each_missing_capability(self):
        caps = detect_host_capabilities("opencode")
        verdict = check_action_capabilities(ACTION_MUTATE, caps, host="opencode")
        self.assertTrue(verdict.missing)
        for name in verdict.missing:
            self.assertIn("DECLARED, NOT PROBED", verdict.notes[name])

    def test_an_unknown_action_raises_rather_than_defaulting(self):
        """Defaulting would let a mutating action inherit the read-only policy."""
        with self.assertRaises(UnknownActionError):
            check_action_capabilities("execute", _fully_capable(), host="opencode")

    def test_the_checker_runs_no_probe(self):
        """Pure over the descriptor it is given: a forced seam must not change its answer."""
        caps = HostSandboxCapabilities(platform="linux")
        with forced_runner_safety_verdicts({CAP_COMMIT_GATEWAY: (True, "forced")}):
            verdict = check_action_capabilities(ACTION_REVIEW, caps, host="opencode")
        self.assertIn(CAP_COMMIT_GATEWAY, verdict.missing)


class FailClosedPreflightTests(unittest.TestCase):
    """E-05: the `RUN-HOST-CAPABILITY` refusal, verbatim, item-local, and two-sided."""

    def test_the_finding_code_string_is_exact(self):
        self.assertEqual(RUN_HOST_CAPABILITY, "RUN-HOST-CAPABILITY")

    def test_the_message_matches_the_specs_verbatim_text(self):
        rendered = format_host_capability_finding(
            host="<host>",
            capability="<capability>",
            item="<item>",
            action="<action>",
            selector="<selector>",
        )
        self.assertEqual(rendered, SPEC_MESSAGE)

    def test_the_message_carries_the_recovery_command(self):
        msg = preflight_host_capabilities(
            ACTION_REVIEW,
            HostSandboxCapabilities(platform="linux"),
            host="opencode",
            item="mjx7ne",
        ).message
        self.assertIn("then run: aw opencode run mjx7ne", msg)
        self.assertIn("required by mjx7ne action review", msg)
        self.assertIn("No work started for this item.", msg)

    def test_it_REFUSES_when_a_required_capability_is_unsupported(self):
        caps = _fully_capable()
        caps.supports_commit_gateway = False
        pre = preflight_host_capabilities(
            ACTION_MUTATE, caps, host="opencode", item="mjx7ne"
        )
        self.assertFalse(pre.ok)
        self.assertEqual(pre.finding_code, RUN_HOST_CAPABILITY)
        self.assertEqual(pre.outcome, OUTCOME_FAILED)
        self.assertEqual(pre.reason_code, REASON_HOST_CAPABILITY_UNAVAILABLE)
        self.assertIn(CAP_COMMIT_GATEWAY, pre.message)

    def test_it_PROCEEDS_when_the_same_action_is_satisfied(self):
        """The other half of the gate: a one-sided demonstration proves nothing."""
        pre = preflight_host_capabilities(
            ACTION_MUTATE, _fully_capable(), host="opencode", item="mjx7ne"
        )
        self.assertTrue(pre.ok)
        self.assertEqual(pre.message, "")
        self.assertEqual(pre.outcome, "")
        self.assertEqual(pre.reason_code, "")

    def test_the_refusal_starts_no_session_and_mutates_nothing(self):
        pre = preflight_host_capabilities(
            ACTION_REVIEW,
            HostSandboxCapabilities(platform="linux"),
            host="opencode",
            item="mjx7ne",
        )
        self.assertFalse(pre.session_started)
        self.assertFalse(pre.mutated)

    def test_the_refusal_is_ITEM_LOCAL_and_does_not_abort_the_run(self):
        """Spec 4.2: FAIL ITEM; cascade dependents; CONTINUE independent items."""
        pre = preflight_host_capabilities(
            ACTION_REVIEW,
            HostSandboxCapabilities(platform="linux"),
            host="opencode",
            item="mjx7ne",
        )
        self.assertTrue(pre.cascade_dependents)
        self.assertFalse(
            pre.aborts_run, "an item-local failure must not abort the queue"
        )

    def test_an_independent_item_still_passes_after_another_is_refused(self):
        """Concretely: the refusal of one (item, action) does not taint the next check."""
        incapable = HostSandboxCapabilities(platform="linux")
        refused = preflight_host_capabilities(
            ACTION_REVIEW, incapable, host="opencode", item="blocked1"
        )
        independent = preflight_host_capabilities(
            ACTION_READ_ONLY, incapable, host="opencode", item="independent1"
        )
        self.assertFalse(refused.ok)
        self.assertTrue(independent.ok, "an independent item must continue")

    def test_the_preflight_does_not_raise_for_an_unmet_requirement(self):
        """A refusal is a recordable OUTCOME, not a crash: the driver must be able to log it."""
        pre = preflight_host_capabilities(
            ACTION_MUTATE,
            HostSandboxCapabilities(platform="linux"),
            host="opencode",
            item="mjx7ne",
        )
        self.assertIsInstance(pre.to_dict(), dict)
        self.assertFalse(pre.to_dict()["ok"])

    def test_an_unknown_action_still_raises(self):
        with self.assertRaises(UnknownActionError):
            preflight_host_capabilities(
                "execute", _fully_capable(), host="opencode", item="mjx7ne"
            )

    def test_a_real_host_today_refuses_the_mutating_actions(self):
        """The ACCEPTED CONSEQUENCE of OQ-03 option (a), asserted rather than assumed."""
        caps = detect_host_capabilities("opencode")
        pre = preflight_host_capabilities(
            ACTION_MUTATE, caps, host="opencode", item="mjx7ne"
        )
        self.assertFalse(pre.ok, "the two unenforced capabilities must fail CLOSED")
        self.assertEqual(set(pre.verdict.missing), {CAP_COMMIT_GATEWAY, CAP_DENY_PUSH})


class InspectionVerbTests(unittest.TestCase):
    """E-06: the two read-only verbs, in-process (no subprocess needed)."""

    def _args(self, **kwargs):
        ns = argparse.Namespace(
            host=None, agent=False, json=False, no_color=True, dir=None
        )
        for k, v in kwargs.items():
            setattr(ns, k, v)
        return ns

    def test_probe_reports_one_host_and_exits_zero(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = host_cmd.run_probe(self._args(host="opencode"))
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("host opencode", out)
        self.assertIn(CAP_FRESH_VERIFIER_SESSION, out)

    def test_capabilities_with_no_host_reports_every_runner_host(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = host_cmd.run_capabilities(self._args())
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        for host in host_cmd.DEFAULT_HOSTS:
            self.assertIn(f"host {host}", out)

    def test_capabilities_shows_both_an_allowed_and_a_refused_action(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            host_cmd.run_capabilities(self._args(host="opencode"))
        out = buf.getvalue()
        self.assertIn("ALLOWED  read_only", out)
        self.assertIn("REFUSED  mutate", out)

    def test_the_agent_stream_is_valid_jsonl_and_carries_the_finding_code(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = host_cmd.run_capabilities(self._args(host="opencode", agent=True))
        self.assertEqual(rc, 0)
        records = [
            json.loads(line) for line in buf.getvalue().splitlines() if line.strip()
        ]
        self.assertTrue(records)
        self.assertEqual(records[-1]["cmd"], "host capabilities")
        self.assertEqual(records[-1]["exit"], 0)

    def test_the_json_payload_carries_the_full_contract_and_action_verdicts(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            host_cmd.run_capabilities(self._args(host="opencode", json=True))
        payload = json.loads(buf.getvalue())
        data = payload["data"]
        self.assertEqual(data["finding_code"], RUN_HOST_CAPABILITY)
        self.assertEqual(len(data["action_classes"]), 4)
        host = data["hosts"][0]
        self.assertEqual(host["host"], "opencode")
        self.assertEqual(len(host["actions"]), 4)

    def test_the_capability_rows_are_derived_by_introspection(self):
        """A field added to the contract must not be able to vanish from the report."""
        caps = HostSandboxCapabilities(platform="linux")
        rows = host_cmd._capability_rows(caps)
        names = {r["capability"] for r in rows}
        for name in RUNNER_SAFETY_CAPABILITIES:
            self.assertIn(name, names)
        self.assertIn("supports_os_sandbox", names)

    def test_the_verbs_write_nothing_to_the_repository(self):
        """Read-only: no repository path is opened for writing by either verb."""
        import builtins

        opened = []
        real_open = builtins.open

        def spy(path, mode="r", *a, **kw):
            if any(flag in mode for flag in ("w", "a", "x", "+")):
                opened.append(str(path))
            return real_open(path, mode, *a, **kw)

        builtins.open = spy  # type: ignore[assignment]
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                host_cmd.run_capabilities(self._args(host="opencode"))
        finally:
            builtins.open = real_open  # type: ignore[assignment]
        self.assertEqual(
            opened, [], f"the capabilities verb opened paths for writing: {opened}"
        )


class CommandDeclarationTests(unittest.TestCase):
    """E-06: each new parser leaf carries a matching `CommandDeclaration`."""

    def test_both_leaves_are_declared(self):
        from agent_workflows.command_surface import get_declaration

        for leaf in ("host probe", "host capabilities"):
            with self.subTest(leaf=leaf):
                decl = get_declaration(leaf)
                self.assertIsNotNone(decl, f"{leaf} has no CommandDeclaration")
                assert decl is not None
                self.assertEqual(decl.command_class, "read")
                self.assertEqual(decl.mutation_gate, "none")
                self.assertNotIn(
                    1,
                    decl.exit_contract,
                    "a not-supported capability is an ANSWER, not a finding",
                )

    def test_the_parser_exposes_exactly_the_declared_host_leaves(self):
        from agent_workflows.cli import _build_parser
        from agent_workflows.command_surface import discover_parser_leaves

        leaves = {
            leaf
            for leaf in discover_parser_leaves(_build_parser())
            if leaf.startswith("host ")
        }
        self.assertEqual(leaves, {"host probe", "host capabilities"})

    def test_no_undeclared_parser_leaf_was_introduced(self):
        """The deterministic CI gate this plan could otherwise have broken."""
        from agent_workflows.cli import _build_parser
        from agent_workflows.command_surface import find_undeclared_leaves

        undeclared = {
            leaf
            for leaf in find_undeclared_leaves(_build_parser())
            if leaf.startswith("host")
        }
        self.assertEqual(undeclared, set())


if __name__ == "__main__":
    unittest.main()
