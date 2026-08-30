"""Tests for testinvoke Order 01 (uyd3lw): the agent contract's test-invocation rule.

The defect this guards: nothing in the always-loaded agent contract said HOW to run this repo's
suite, so an agent overrode the configured `-n auto` with `-n0` (measured 4.7x slower on this
checkout: 35.44s vs 167.19s) and then spent minutes fighting a `-q` it had added itself, which
compounded with the configured `-q` into `-qq` and suppressed the very `N passed` summary line the
contract requires it to paste.

Covers E-01/E-02 (the rule reaches the rendered AGENTS.md, and carries no em/en dash) and E-04 (the
rule cannot silently diverge from `pyproject.toml`'s `addopts`).

The load-bearing test is `test_addopts_still_supplies_parallelism`: the guidance tells agents to rely
on a repo default. If someone changes that default to serial, AGENTS.md would be instructing agents
to depend on something that no longer exists, so this fails loudly instead.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Heading of the section the rule lives in, and a window generous enough to cover it.
CONTRACT_HEADING = "### Agent execution contract"
CONTRACT_WINDOW = 4200


def _agents_md() -> str:
    return (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")


def _contract_section(text: str) -> str:
    """The authored execution-contract section, scoped so unrelated prose cannot affect assertions."""

    start = text.find(CONTRACT_HEADING)
    assert start > 0, "the agent execution contract section must exist in AGENTS.md"
    return text[start : start + CONTRACT_WINDOW]


class AgentContractTestInvocationTests(unittest.TestCase):
    """The invocation rule must be present in the block an agent actually loads."""

    def test_agents_md_states_the_bare_invocation_rule(self):
        section = _contract_section(_agents_md())
        for phrase in (
            "HOW TO RUN THE SUITE",
            "python3 -m pytest",
            "make test",
            "addopts",
        ):
            self.assertIn(phrase, section, f"AGENTS.md must state: {phrase}")

    def test_agents_md_names_every_forbidden_flag(self):
        """V-01's contract: a rule missing any of the three flags does not satisfy this plan."""

        section = _contract_section(_agents_md())
        self.assertIn("-n0", section, "the rule must forbid -n0 (it disables xdist)")
        self.assertIn(
            "-qq",
            section,
            "the rule must explain that a second -q compounds into -qq and hides the summary",
        )
        self.assertIn(
            "-p no:randomly",
            section,
            "the rule must forbid -p no:randomly (it hides order-dependence bugs)",
        )

    def test_agents_md_names_the_escape_hatch(self):
        """An agent that legitimately needs per-test counts must be told the supported way."""

        section = _contract_section(_agents_md())
        self.assertIn(
            '-o addopts=""',
            section,
            'the rule must name the -o addopts="" escape hatch for narrowed runs',
        )

    def test_invocation_rule_states_the_penalty_as_a_range(self):
        """Per F-9: no single authoritative constant, so nobody 'reconciles' it with CONTRIBUTING.md.

        `CONTRIBUTING.md` tells humans "roughly 5-8x" for a different scope. Two hard numbers in two
        contracts invite a future editor to invent a third that neither measured.
        """

        section = _contract_section(_agents_md())
        self.assertIn(
            "4x to 6x",
            section,
            "the -n0 penalty must be stated as a range, not a single constant",
        )
        self.assertIn(
            "core count",
            section,
            "the rule must say the ratio varies with core count and load",
        )

    def test_agents_md_contract_has_no_em_or_en_dash(self):
        """Repo rule: no em/en dashes in user-facing prose we author.

        Deliberately tests the UNICODE dashes ONLY. The ASCII hyphen-minus is legitimate and is
        already used as a clause separator in this very section ("end users) - this keeps..."), so a
        naive "no dashes" check would fail on shipped, correct text.
        """

        section = _contract_section(_agents_md())
        self.assertNotIn("\u2014", section, "em dash in authored user-facing prose")
        self.assertNotIn("\u2013", section, "en dash in authored user-facing prose")

    def test_ascii_hyphen_is_present_and_tolerated(self):
        """Proves the dash assertion above is correctly scoped rather than vacuous.

        If this ever fails, the pre-existing hyphen moved and the no-dash test may no longer be
        proving that it tolerates ASCII hyphens.
        """

        section = _contract_section(_agents_md())
        self.assertIn("-", section, "the section legitimately contains ASCII hyphens")

    def test_rule_lives_inside_the_managed_block(self):
        """The rule must be inside the aw:block region, i.e. owned by the generator, not hand-edited."""

        text = _agents_md()
        start = text.find("<!-- aw:block -->")
        end = text.find("<!-- /aw:block -->")
        self.assertGreater(start, -1, "AGENTS.md must carry the aw:block open marker")
        self.assertGreater(end, start, "AGENTS.md must carry the aw:block close marker")
        rule_at = text.find("HOW TO RUN THE SUITE")
        self.assertGreater(
            rule_at, start, "the rule must appear after the aw:block open marker"
        )
        self.assertLess(
            rule_at, end, "the rule must appear before the aw:block close marker"
        )

    def test_generator_owns_the_rule(self):
        """The rule must come from engine.py, so a reinstall cannot silently drop it."""

        from agent_workflows import engine

        prose = engine.agents_pointer_prose(target_layout="aw")
        self.assertIn("HOW TO RUN THE SUITE", prose)
        self.assertIn("-n0", prose)
        self.assertIn("-p no:randomly", prose)


class AddoptsConsistencyTests(unittest.TestCase):
    """E-04: the guidance and the actual configuration cannot silently diverge."""

    @staticmethod
    def _addopts() -> str:
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^addopts\s*=\s*"([^"]*)"', text, re.M)
        assert match is not None, "pyproject.toml must define addopts"
        return match.group(1)

    def test_addopts_still_supplies_parallelism(self):
        """If the repo default stops being parallel, AGENTS.md's advice becomes a lie. Fail loudly."""

        addopts = self._addopts()
        self.assertIn(
            "-n auto",
            addopts,
            "AGENTS.md tells agents a BARE run is already parallel; pyproject addopts no longer "
            f"supplies -n auto (got: {addopts!r}). Update both together or the guidance is wrong.",
        )

    def test_addopts_still_supplies_quiet_and_fast_subset(self):
        """The rule's other two claims (already quiet, already fast-subset) must also hold."""

        addopts = self._addopts()
        self.assertIn("-q", addopts, "the rule claims a bare run is already quiet")
        self.assertIn(
            "not slow", addopts, "the rule claims a bare run is already the fast subset"
        )

    def test_agents_md_quotes_the_real_addopts_flags(self):
        """The flags AGENTS.md quotes must be the flags actually configured."""

        section = _contract_section(_agents_md())
        addopts = self._addopts()
        for flag in ("-n auto", "--dist=worksteal"):
            self.assertIn(flag, addopts, f"pyproject addopts must still contain {flag}")
            self.assertIn(flag, section, f"AGENTS.md must quote the configured {flag}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
