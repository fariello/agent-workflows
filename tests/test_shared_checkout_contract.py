"""Tests for coauthor Order 01 (a5ni7v): the shared-checkout contract must reach every agent.

Incident: an INTERACTIVE `agy` session committed bd3fed1 and swept another session's uncommitted
run_viewer.py/cli.py edits into it. Root cause: the `## Concurrent Work` warning lived only in the
DRIVER PROMPT, while `host_adapters.py` maps the `antigravity` host's pointer file to `AGENTS.md`, whose
managed block never mentioned concurrency. So for any non-runner session the rule did not exist.

These assertions run against the GENERATED block (`engine.agents_managed_block`), not this repo's
AGENTS.md, because that generated text is what every ADOPTER receives on install/update.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import engine, host_adapters

REPO_ROOT = Path(__file__).resolve().parents[1]


def _block() -> str:
    return engine.agents_managed_block(target_layout="aw")


class SharedCheckoutSectionTests(unittest.TestCase):
    """E-01: the installed contract must state the checkout is shared."""

    def test_section_exists(self):
        self.assertIn("### Shared checkout: you are not alone in this repo", _block())

    def test_states_concurrency(self):
        """The exact word an agent (or a grep) would look for."""
        self.assertIn("CONCURRENTLY", _block())

    def test_states_foreign_work_is_not_yours(self):
        b = _block()
        self.assertIn("you did not create are NOT yours", b)

    def test_forbids_cleaning_up_someone_elses_work(self):
        b = _block()
        for verb in ("revert", "stage", "commit", "discard", "reformat", "clean up"):
            self.assertIn(verb, b, f"the rule must name {verb!r}")

    def test_requires_stop_and_report_on_conflict(self):
        self.assertIn("STOP and report", _block())

    def test_terms_absent_before_this_change_are_now_present(self):
        """Regression pins: each of these was verified ABSENT from the contract block."""
        b = _block()
        for term in ("CONCURRENTLY", "another party", "staged"):
            self.assertIn(term, b, f"{term!r} must be in the installed contract")


class VerificationStepTests(unittest.TestCase):
    """E-02: the rule must be ACTIONABLE, since prose alone did not prevent the sweep."""

    def test_names_the_verification_command(self):
        self.assertIn("git diff --cached --name-only", _block())

    def test_names_the_unstage_remedy(self):
        self.assertIn("git restore --staged", _block())

    def test_warns_path_scoping_is_insufficient(self):
        """The specific trap that caused the incident."""
        b = _block()
        self.assertIn("ALREADY STAGED", b)
        self.assertIn("NOT by itself sufficient", b)

    def test_requires_verification_before_every_commit(self):
        self.assertIn("BEFORE EVERY COMMIT", _block())


class GraduationContractTests(unittest.TestCase):
    """The graduate/implement/execute rule must ship to adopters, not just this repo."""

    def test_contract_is_in_the_installed_block(self):
        b = _block()
        self.assertIn("### Acting on a backlog item", b)
        self.assertIn("REVIEW-READY", b)
        self.assertIn("From-Backlog", b)
        self.assertIn("`graduated`, NOT `done`", b)

    def test_graduated_status_is_documented(self):
        self.assertIn("`graduated`->`active`", _block())


class DriverPromptParityTests(unittest.TestCase):
    """E-03/E-04: runner turns and interactive sessions must be told the same thing, in ASCII."""

    DRIVERS = ("agent_workflows/oc_runipd.py", "agent_workflows/agy_runipd.py")

    def _concurrent_blocks(self, rel: str) -> list[str]:
        src = (REPO_ROOT / rel).read_text(encoding="utf-8")
        out, i = [], 0
        while True:
            i = src.find("## Concurrent Work", i)
            if i < 0:
                return out
            out.append(src[i : i + 1400])
            i += 1

    def test_each_driver_has_concurrent_work_sections(self):
        for rel in self.DRIVERS:
            self.assertTrue(self._concurrent_blocks(rel), f"{rel} lost its section")

    def test_every_block_carries_the_verification_step(self):
        for rel in self.DRIVERS:
            for n, block in enumerate(self._concurrent_blocks(rel), start=1):
                self.assertIn(
                    "git diff --cached --name-only",
                    block,
                    f"{rel} block {n} lacks the verification command",
                )

    def test_every_block_is_pure_ascii(self):
        """A curly apostrophe shipped in the delivered prompt text before this change."""
        for rel in self.DRIVERS:
            for n, block in enumerate(self._concurrent_blocks(rel), start=1):
                bad = sorted({c for c in block if ord(c) > 127})
                self.assertEqual(bad, [], f"{rel} block {n} has non-ASCII: {bad}")

    def test_no_curly_apostrophe_remains(self):
        for rel in self.DRIVERS:
            for block in self._concurrent_blocks(rel):
                self.assertNotIn("\u2019", block)


class NoDriftTests(unittest.TestCase):
    """E-05: this repo's delivered copy must equal the generated source of truth."""

    def test_repo_agents_block_equals_generated(self):
        cur = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        i = cur.find("<!-- aw:block -->")
        j = cur.find("<!-- /aw:block -->") + len("<!-- /aw:block -->")
        self.assertGreater(i, -1, "managed block markers missing")
        self.assertEqual(cur[i:j].strip(), _block().strip())

    def test_contract_is_not_duplicated_inside_and_outside_the_block(self):
        """P8: the graduation contract is stated once, in the managed block."""
        cur = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        j = cur.find("<!-- /aw:block -->")
        after = cur[j:]
        self.assertNotIn(
            "the whole job is\nyours",
            after,
            "the contract body must not be restated outside the managed block",
        )

    def test_antigravity_host_reads_agents_md(self):
        """Why the installed block is load-bearing for the observed incident."""
        self.assertEqual(host_adapters.HOST_POINTER_FILE["antigravity"], "AGENTS.md")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
