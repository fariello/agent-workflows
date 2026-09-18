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


class InstalledContractContentTests(unittest.TestCase):
    """The installed contract must carry the shared-checkout rule and make it ACTIONABLE.

    ONE test, not sixteen. The original E-01/E-02 shape asserted each required phrase in its own
    test method, so a reworded contract produced a wall of separate failures that all named the same
    root cause. This reports EVERY missing element at once, which is what an agent fixing a drifted
    contract actually needs.

    Substance is deliberately narrow: only phrases that are LOAD-BEARING because something other
    than a human reads them (the literal git commands an agent is told to run, and the section
    heading a grep looks for). Stylistic wording is NOT pinned; prose is expected to change.
    """

    REQUIRED = (
        # (needle, why it is load-bearing)
        (
            "### Shared checkout: you are not alone in this repo",
            "the section heading agents grep for",
        ),
        (
            "CONCURRENTLY",
            "states the checkout is shared, the fact the whole rule rests on",
        ),
        (
            "git diff --cached --name-only",
            "the verification command an agent must actually run",
        ),
        (
            "git restore --staged",
            "the precise unstage remedy (vs a destructive reset/stash)",
        ),
        (
            "BEFORE EVERY COMMIT",
            "binds the verification to every commit, not just the first",
        ),
        (
            "NOT by itself sufficient",
            "names the path-scoping trap that caused the incident",
        ),
        (
            "STOP and report",
            "the required action when changes cannot be safely combined",
        ),
    )

    def test_the_installed_contract_carries_every_load_bearing_element(self):
        block = _block()
        missing = [
            f"  MISSING {needle!r}\n    needed because: {why}"
            for needle, why in self.REQUIRED
            if needle not in block
        ]
        self.assertEqual(
            missing,
            [],
            "the generated AGENTS.md managed block (engine.agents_managed_block) no longer carries "
            "every load-bearing element of the shared-checkout contract. Each element below is "
            "machine-read or is a command an agent is instructed to run verbatim, so losing it "
            "silently disables the rule for every adopter on their next install.\n"
            + "\n".join(missing)
            + "\n  FIX: restore the element in engine.agents_managed_block, then run "
            "`aw setup-repo` (or reinstall) so this repo's AGENTS.md matches the generated block.",
        )

    def test_it_forbids_touching_another_partys_work(self):
        """The prohibition must name the acts, so 'I only reformatted it' is not a loophole."""
        block = _block()
        unnamed = [
            verb
            for verb in ("revert", "stage", "commit", "discard", "reformat", "clean up")
            if verb not in block
        ]
        self.assertEqual(
            unnamed,
            [],
            f"the contract must forbid each of these acts by name; {unnamed} are unnamed, which "
            "leaves an agent free to argue the act it performed was not prohibited",
        )

    def test_the_graduation_contract_ships_to_adopters(self):
        """Not just this repo: an adopter's agent needs the graduate/implement/execute rule too."""
        block = _block()
        self.assertIn("Acting on a backlog item", block)
        self.assertIn("graduated", block)


class DriverPromptParityTests(unittest.TestCase):
    """E-03/E-04: runner turns and interactive sessions must be told the same thing, in ASCII.

    RE-BASED by rununify Order 04 (`tx6q0h`), deliberately and without weakening. Both runners'
    `build_prompt`/`build_verifier_prompt` were de-duplicated into `runner_shared`, so the prompt
    prose this class reads now lives in that ONE module instead of being spelled twice. The property
    asserted is UNCHANGED (every Concurrent Work block still carries the verification command, still
    in ASCII); only the file it is read from moved, which is the point of the de-duplication. Reading
    the shared module is now STRICTLY STRONGER than reading the two runners was, because a single
    failure here can no longer be masked by the other host's copy still being correct.
    """

    DRIVERS = ("agent_workflows/runner_shared.py",)

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
