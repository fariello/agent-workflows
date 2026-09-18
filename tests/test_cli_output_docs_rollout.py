"""The CLI output-contract docs must EXIST and be internally valid.

WHAT THIS FILE USED TO BE. 15 tests asserting English words appeared in three shipped markdown
guides, several of them close to vacuous: `assertIn("0", text)` and `assertIn("find", text)` on a
document whose subject IS exit codes and the `find` verb, `assertIn("status", text)` on the status
migration guide. A test that cannot fail for the reason it was written is not evidence, and the
rest were change-detectors over prose describing a migration that has already shipped. Prose is
expected to be rewritten; git records that it was.

WHAT SURVIVES. The docs must exist (a dead link in the docs index is a real defect an adopter
hits), and they must pass `docs_check`, which validates the things that are MECHANICALLY
falsifiable about a doc: its internal links resolve, the subcommands it names actually exist, and
it carries no em/en dash. That check is the repository's ONE doc validator, so this file calls it
rather than re-implementing a dash scan (see `tests/test_docs.py`, which runs it repo-wide).

The `aw.agent/v1` schema id these guides document is pinned where it is load-bearing and testable:
against the emitter itself, in `tests/test_output_contract.py` and `tests/test_agent_schema.py`.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import docs_check as dc

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

HUMAN_GUIDE = DOCS_DIR / "cli-human-guide.md"
AGENT_REF = DOCS_DIR / "cli-agent-protocol.md"
MIGRATION = DOCS_DIR / "cli-migration.md"

AUTHORED_DOCS = (HUMAN_GUIDE, AGENT_REF, MIGRATION)


class AuthoredDocsTests(unittest.TestCase):
    def test_every_authored_doc_exists_and_passes_the_repository_doc_check(self):
        """Existence and validity in one test: a missing doc and a broken doc fail the same user.

        `docs_check.check_doc` is the repository's single doc validator (resolvable links, real
        subcommand names, ASCII dashes). Reporting all three docs' findings together means a fixer
        sees every problem in one run instead of rediscovering them one red test at a time.
        """
        problems: list[str] = []
        for doc in AUTHORED_DOCS:
            rel = doc.relative_to(REPO_ROOT).as_posix()
            if not doc.is_file():
                problems.append(
                    f"  MISSING: {rel} is referenced by the docs index but absent"
                )
                continue
            for finding in dc.check_doc(doc):
                problems.append(f"  INVALID {rel}: {finding}")
        self.assertEqual(
            problems,
            [],
            "the CLI output-contract docs are missing or fail docs_check:\n"
            + "\n".join(problems)
            + "\n  FIX: repair the link/subcommand/dash finding named above, or restore the doc. "
            "Run `aw check` to see the same findings for every doc in the tree.",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
