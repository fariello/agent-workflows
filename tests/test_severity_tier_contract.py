"""Behavior tests pinning the check engine severity tier contract (IPD wm40yl).

This module enforces the contract published in `docs/cli-output-contract.md` section 3:
1. Exit mapping: `artifact_core.drift_exit_code` returns 0 for a lone `info` finding and
   for an empty list, and 1 for `error`, `warning`, and unrecognized severity strings.
2. Fail-closed on absence: legacy 3-positional `Drift(location, rule, detail)` with no
   explicit severity evaluates to exit 1.
3. Registry enum conformance: every registered rule in `check_engine.RULE_REGISTRY`
   declares one of the three canonical severities: `error`, `warning`, or `info`.
4. Conservative default: `check_engine.rule_spec` on an unregistered rule ID returns
   `RuleSpec` with severity `error` (`_DEFAULT_RULESPEC`).
5. At least one advisory rule exists: the advisory (`info`) tier in `RULE_REGISTRY` is non-empty.
"""

from __future__ import annotations

import unittest

from agent_workflows import artifact_core, check_engine


class SeverityTierContractTests(unittest.TestCase):
    """Behavior tests pinning the severity-to-exit-code contract."""

    # ----------------------------------------------------------------------------------
    # Property 1: The Exit Mapping
    # ----------------------------------------------------------------------------------

    def test_drift_exit_code_lone_info_returns_clean_zero(self) -> None:
        """A lone info finding returns exit code 0."""
        finding = artifact_core.Drift(
            location="some/path.md",
            rule="check.advisory-rule",
            detail="advisory detail",
            severity="info",
        )
        self.assertEqual(artifact_core.drift_exit_code([finding]), 0)

    def test_drift_exit_code_empty_list_returns_clean_zero(self) -> None:
        """An empty findings list returns exit code 0."""
        self.assertEqual(artifact_core.drift_exit_code([]), 0)

    def test_drift_exit_code_error_returns_failing_one(self) -> None:
        """An error finding returns exit code 1."""
        finding = artifact_core.Drift(
            location="some/path.md",
            rule="check.error-rule",
            detail="error detail",
            severity="error",
        )
        self.assertEqual(artifact_core.drift_exit_code([finding]), 1)

    def test_drift_exit_code_warning_returns_failing_one(self) -> None:
        """A warning finding returns exit code 1."""
        finding = artifact_core.Drift(
            location="some/path.md",
            rule="check.warning-rule",
            detail="warning detail",
            severity="warning",
        )
        self.assertEqual(artifact_core.drift_exit_code([finding]), 1)

    def test_drift_exit_code_unrecognized_severity_fails_closed(self) -> None:
        """Unrecognized or improperly cased severity strings return exit code 1."""
        for unrecognized in ("warn", "advisory", "INFO", "unknown", "warning "):
            with self.subTest(severity=unrecognized):
                finding = artifact_core.Drift(
                    location="some/path.md",
                    rule="check.custom-rule",
                    detail="detail",
                    severity=unrecognized,
                )
                self.assertEqual(artifact_core.drift_exit_code([finding]), 1)

    # ----------------------------------------------------------------------------------
    # Property 2: Fail-Closed on Absence
    # ----------------------------------------------------------------------------------

    def test_drift_exit_code_legacy_drift_without_severity_fails_closed(self) -> None:
        """A legacy 3-positional Drift carrying no severity defaults to '' and returns exit 1."""
        legacy = artifact_core.Drift(
            "some/path.md", "check.legacy-rule", "legacy detail"
        )
        self.assertEqual(legacy.severity, "")
        self.assertEqual(artifact_core.drift_exit_code([legacy]), 1)

    # ----------------------------------------------------------------------------------
    # Property 3: Registry Enum Conformance
    # ----------------------------------------------------------------------------------

    def test_rule_registry_severities_conform_to_canonical_enum(self) -> None:
        """Every RuleSpec in check_engine.RULE_REGISTRY specifies a valid canonical severity."""
        canonical_severities = {"error", "warning", "info"}
        out_of_enum = {
            rule_id: spec.severity
            for rule_id, spec in check_engine.RULE_REGISTRY.items()
            if spec.severity not in canonical_severities
        }
        self.assertEqual(
            out_of_enum,
            {},
            f"Found rules with non-canonical severity: {out_of_enum}",
        )

    # ----------------------------------------------------------------------------------
    # Property 4: The Conservative Default
    # ----------------------------------------------------------------------------------

    def test_rule_spec_unregistered_rule_defaults_to_error_severity(self) -> None:
        """An unregistered rule ID defaults to severity 'error' via _DEFAULT_RULESPEC."""
        spec = check_engine.rule_spec("check.unregistered-hypothetical-rule-xyz")
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec, check_engine._DEFAULT_RULESPEC)

    # ----------------------------------------------------------------------------------
    # Property 5: At Least One Advisory Rule Exists
    # ----------------------------------------------------------------------------------

    def test_rule_registry_contains_at_least_one_advisory_info_rule(self) -> None:
        """The registry contains at least one info (advisory) rule so the tier is not empty."""
        info_rules = [
            rule_id
            for rule_id, spec in check_engine.RULE_REGISTRY.items()
            if spec.severity == "info"
        ]
        self.assertGreaterEqual(
            len(info_rules),
            1,
            "RULE_REGISTRY must contain at least one advisory ('info') rule",
        )


if __name__ == "__main__":
    unittest.main()
