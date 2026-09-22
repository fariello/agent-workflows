"""Plan `4h7tt0` E-04 / V-04: the no-push guarantee is RETIRED, and may not creep back as an inference.

WHAT THIS FILE IS FOR. Spec `25kzda` 4.2 used to carry a `RUN-NO-PUSH` finding code whose pass
criterion was "Capability preflight proved push denial". No such enforcement exists in this
repository, and every cheap mechanism that looks like one is evadable, so the maintainer RETIRED the
code on 2026-09-08 (commit `b23d447d`) rather than bind it to something that does not enforce
anything. This file pins the two halves of that outcome which a future well-meaning change could
undo:

  1. THE ROW IS GONE AND STAYS GONE, in the spec text, in `RUN_FINDING_CODES`, and in the count
     invariant `validate_finding_table` enforces.
  2. `supports_deny_push` IS STILL DECLARED, STILL FALSE, AND STILL NOT INFERRED FROM PRESENCE. The
     retirement removed a PROMISE (the 4.2 reporting code), not the PROTECTION (the 5.2 capability
     whose permanent False makes action classes fail closed). Deleting the capability was raised as
     OQ-02, answered separately, and is owned by backlog `aagh7v` - NOT by this plan.

WHY AN ANTI-INFERENCE TEST AT ALL, given nothing infers today. Because the tempting "completion" of
this work is to notice `git_commit_helper.offer_commit`, or a `pre-push` hook, or a config flag, and
report push prevention from its mere existence. That is forbidden in writing at
`host_sandbox_profile.py:88-95`, was already rejected once for the host capabilities, and is strictly
WORSE than the retirement: a fail-closed refusal becomes a fail-OPEN checker that passes because
nothing was checked. A test that only asserted "False today" would pass against such a change if the
artifact happened to be absent, so the cases below assert the DECISION LOGIC, with the artifacts
PRESENT, and one case proves the assertion has teeth by running it against a deliberately fail-open
stub and requiring it to FAIL.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import host_sandbox_profile as hsp
from agent_workflows import run_evidence as evidence
from agent_workflows.host_sandbox_profile import (
    CAP_DENY_PUSH,
    HostSandboxCapabilities,
    forced_runner_safety_verdicts,
    probe_runner_safety_capabilities,
)

_SPEC_PATH = (
    Path(__file__).resolve().parents[1]
    / ".aw"
    / "records"
    / "specs"
    / "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
)


class TestRunNoPushIsRetiredFromTheVocabulary(unittest.TestCase):
    """Half 1: the 4.2 reporting code is gone, and the count invariant agrees."""

    def test_the_finding_code_is_absent_from_the_shipped_table(self) -> None:
        self.assertNotIn("RUN-NO-PUSH", evidence.run_finding_codes())
        self.assertNotIn("RUN-NO-PUSH", evidence.RUN_FINDING_CODES_BY_CODE)

    def test_no_code_is_unbound_unbuilt_any_more(self) -> None:
        """The retirement's measurable consequence, asserted as a retirement not an implementation."""
        unbuilt = [
            row.code
            for row in evidence.RUN_FINDING_CODES
            if row.binding == evidence.UNBOUND_UNBUILT
        ]
        self.assertEqual(unbuilt, [])
        # ...while the two DEPENDENCY-blocked codes are untouched: an empty unbuilt set must not be
        # read as "every code now has a predicate behind it".
        self.assertEqual(
            sorted(evidence.unbound_run_finding_codes()),
            ["RUN-COMMIT-CONTENTS", "RUN-COMMIT-GATEWAY"],
        )

    def test_the_table_reports_itself_valid_at_the_new_count(self) -> None:
        """A forgotten `!= 13` invariant would mark the SHIPPED table invalid at runtime, not just
        fail a test, so this asserts the runtime self-check and not only the length."""
        self.assertEqual(len(evidence.RUN_FINDING_CODES), 12)
        result = evidence.validate_finding_table()
        self.assertTrue(
            result.ok, f"shipped table reports itself invalid: {result.findings}"
        )
        self.assertEqual(result.findings, ())

    def test_the_spec_row_is_gone_too_so_code_and_spec_cannot_disagree(self) -> None:
        if not _SPEC_PATH.exists():  # pragma: no cover - installed-package layout
            self.skipTest(f"spec 25kzda not present at {_SPEC_PATH}")
        text = _SPEC_PATH.read_text(encoding="utf-8")
        self.assertNotIn(
            "| `RUN-NO-PUSH` |",
            text,
            "the 4.2 table row was retired on 2026-09-08 (b23d447d); a reintroduced row would "
            "re-promise proved push denial that nothing enforces",
        )
        # The reason must SURVIVE the row. A silent deletion is indistinguishable from an oversight,
        # and the whole point of outcome (c) was a RECORDED withdrawal.
        self.assertIn("`RUN-NO-PUSH` WAS RETIRED FROM THIS TABLE", text)

    def test_spec_4_1_keeps_its_push_attempt_abort_class(self) -> None:
        """Deliberately ORPHANED, not tidied: 4.1 is pinned and an unused class is already tolerated
        (`Unknown or non-idempotent external outcome` has no code either)."""
        self.assertIn("Push attempt", evidence.ABORT_CLASSES)
        for row in evidence.RUN_FINDING_CODES:
            self.assertNotIn("Push attempt", row.abort_classes)


class TestDenyPushIsNotInferredFromPresence(unittest.TestCase):
    """Half 2: the capability survives, False, and never inferred from an artifact existing."""

    def test_the_capability_still_exists_and_defaults_false(self) -> None:
        """Retiring the 4.2 CODE did not remove the 5.2 CAPABILITY; that is backlog `aagh7v`."""
        self.assertIs(HostSandboxCapabilities().supports_deny_push, False)
        self.assertEqual(CAP_DENY_PUSH, "supports_deny_push")
        self.assertIn(CAP_DENY_PUSH, hsp.RUNNER_SAFETY_CAPABILITIES)

    def test_the_real_probe_path_reports_false_with_its_reason(self) -> None:
        verdicts, notes = probe_runner_safety_capabilities()
        self.assertFalse(verdicts[CAP_DENY_PUSH])
        self.assertIn("DECLARED, NOT PROBED", notes[CAP_DENY_PUSH])
        self.assertIn("fail-closed", notes[CAP_DENY_PUSH])

    def test_no_probe_is_registered_for_deny_push_so_nothing_can_infer_it(self) -> None:
        """The STRUCTURAL reason the verdict cannot drift: there is no probe function to get wrong.

        Note the shape precisely, because I asserted it wrongly first: the capability IS a key in
        `_RUNNER_SAFETY_PROBES`, mapped to `None`. That is deliberate - the key documents that the
        capability was considered and has no probe, rather than leaving a silent absence - and
        `probe_runner_safety_capabilities` reads the `None` as "declared, not probed => False". A
        future change that installs a real callable here must justify what it ATTEMPTS, not what it
        observes.
        """
        self.assertIn(
            CAP_DENY_PUSH,
            hsp._RUNNER_SAFETY_PROBES,
            "the key is expected to be PRESENT and None (considered, deliberately unprobed)",
        )
        self.assertIsNone(hsp._RUNNER_SAFETY_PROBES[CAP_DENY_PUSH])
        self.assertIn(CAP_DENY_PUSH, hsp._DECLARED_UNENFORCED)

    def test_the_commit_helper_exists_and_still_does_not_make_the_verdict_true(
        self,
    ) -> None:
        """THE FORBIDDEN INFERENCE, ASSERTED WITH ITS ARTIFACT PRESENT. `offer_commit` really is
        importable, which is exactly why "it exists, therefore push is prevented" is tempting; it is
        a helper the driver CHOOSES to call, not a boundary the agent cannot evade."""
        from agent_workflows import git_commit_helper

        self.assertTrue(
            callable(getattr(git_commit_helper, "offer_commit", None)),
            "precondition: the helper exists, so the inference is available to be made",
        )
        self.assertFalse(probe_runner_safety_capabilities()[0][CAP_DENY_PUSH])
        self.assertFalse(HostSandboxCapabilities().supports_deny_push)

    def test_local_push_feedback_exists_and_is_not_an_authority_boundary(self) -> None:
        """The second tempting inference: `check_engine.check_push_authorization` is LOCAL,
        bypassable pre-push FEEDBACK. Its presence must not promote the capability either."""
        from agent_workflows import check_engine

        self.assertTrue(
            callable(getattr(check_engine, "check_push_authorization", None))
        )
        self.assertFalse(probe_runner_safety_capabilities()[0][CAP_DENY_PUSH])

    def test_a_forced_true_verdict_does_not_stick(self) -> None:
        """The test seam can force any verdict, and the forcing is SCOPED. So even a caller that
        manages to assert support cannot leave the process believing it (sibling coverage lives at
        `tests/test_host_capability_extension.py`; repeated here because THIS file is what a future
        no-push change will be read against)."""
        with forced_runner_safety_verdicts({CAP_DENY_PUSH: (True, "forced by test")}):
            self.assertTrue(probe_runner_safety_capabilities()[0][CAP_DENY_PUSH])
        self.assertFalse(probe_runner_safety_capabilities()[0][CAP_DENY_PUSH])

    def test_this_files_own_assertion_fails_against_a_fail_open_implementation(
        self,
    ) -> None:
        """PROOF OF TEETH. A test that passes against a fail-open implementation pins nothing, so run
        the assertion above against a deliberately fail-open stand-in - one that reports support
        because `offer_commit` is importable, the exact inference `host_sandbox_profile.py:88-95`
        forbids - and require it to FAIL.

        The stub is the real forbidden logic, not a strawman: `hasattr(helper, "offer_commit")`.
        """

        def _fail_open_probe_deny_push() -> bool:
            from agent_workflows import git_commit_helper

            # THE FORBIDDEN PATTERN, written out: presence of a driver-side helper reported as host
            # enforcement.
            return hasattr(git_commit_helper, "offer_commit")

        self.assertTrue(
            _fail_open_probe_deny_push(),
            "precondition: the fail-open stub really does report support, so failing the "
            "assertion below is evidence of teeth and not of a broken stub",
        )
        with self.assertRaises(AssertionError):
            self.assertFalse(
                _fail_open_probe_deny_push(),
                "the shipped assertion must reject a presence-based verdict",
            )
        # And the SHIPPED path, subjected to the same assertion, passes it.
        self.assertFalse(probe_runner_safety_capabilities()[0][CAP_DENY_PUSH])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
