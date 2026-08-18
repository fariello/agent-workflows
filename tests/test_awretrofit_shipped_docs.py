"""Drift guard for IPD awretrofit Order 02: shipped, agent-executed artifacts must not reintroduce
legacy `.agents/` paths that no longer exist in a fresh/migrated `.aw/` install.

Release-review run 20260817-153418 (findings S4-D01/S4-D02) found the shipped workflow bodies, the
`index.md` catalog, the record-README templates, and the always-loaded AGENTS.md block still
instructed agents to use `.agents/` paths. This test fails if a future edit re-adds a class-(a)
executable/instructional `.agents/` path to a shipped body, template, or the index catalog, or if
AGENTS.md regains a legacy path.

Legitimate remainders are explicitly allowlisted:
- the release-review runbook's layout-agnostic fallbacks (it reviews OTHER repos): they lead with
  `.aw/` and keep `.agents/` only as a named legacy alternative;
- the `migrate/` workflow (documents migrating FROM `.agents/`);
- `normalize_plan_names.py` legacy-fallback descriptions;
- the conformance host-skill matrix (`.agents/skills/` is a host-adapter concept, not the records
  layout this migration changed).
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_BUNDLE = _REPO / ".aw" / "system" / "workflows"
_AGENTS_MD = _REPO / "AGENTS.md"

# Files/subtrees allowed to retain `.agents/` references (class-b layout-agnostic / class-c
# host-adapter / legacy-fallback prose). Paths are relative to the bundle root.
_ALLOWLIST_PREFIXES = (
    "release-review/",  # layout-agnostic runbook: leads with .aw/, keeps .agents/ as named legacy
    "migrate/",  # documents migrating FROM .agents/
    "conformance/",  # .agents/skills/ host-adapter matrix, not the records layout
    "setup-repo/tools/normalize_plan_names.py",  # legacy-fallback descriptions
)


def _iter_tracked_bundle_files():
    for p in sorted(_BUNDLE.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix == ".pyc" or "__pycache__" in p.parts:
            continue
        yield p


class ShippedDocsNoLegacyPathTests(unittest.TestCase):
    def test_no_legacy_agents_paths_in_shipped_bundle(self):
        """No shipped body/template/index outside the allowlist may reference `.agents/`."""
        offenders = []
        for p in _iter_tracked_bundle_files():
            rel = p.relative_to(_BUNDLE).as_posix()
            if any(rel.startswith(pre) for pre in _ALLOWLIST_PREFIXES):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if ".agents/" in text:
                # Report the first offending line for a helpful failure.
                for i, line in enumerate(text.splitlines(), 1):
                    if ".agents/" in line:
                        offenders.append(f"{rel}:{i}: {line.strip()[:120]}")
                        break
        self.assertEqual(
            offenders,
            [],
            "shipped bundle reintroduced legacy .agents/ path(s):\n"
            + "\n".join(offenders),
        )

    def test_index_catalog_uses_aw_system_paths(self):
        """The index.md invocation catalog must reference `.aw/system/workflows/`, not legacy."""
        index = (_BUNDLE / "index.md").read_text(encoding="utf-8")
        self.assertIn(".aw/system/workflows/", index)
        self.assertNotIn(".agents/workflows/", index)
        self.assertIn("source of truth: `.aw/system/VERSION`", index)

    def test_agents_md_managed_block_is_aw_clean(self):
        """This repo's AGENTS.md (regenerated + hand-fixed) carries no legacy `.agents/` path."""
        text = _AGENTS_MD.read_text(encoding="utf-8")
        self.assertNotIn(".agents/", text)
        # And it references the correct docs/ sub-paths (the PR-001 generator fix).
        self.assertIn(".aw/records/docs/research/", text)
        self.assertIn(".aw/system/workflows/", text)

    def test_release_review_leads_with_aw(self):
        """The allowlisted release-review runbook still leads with `.aw/` (not stripped to legacy)."""
        proto = (_BUNDLE / "release-review" / "00-run-protocol.md").read_text(
            encoding="utf-8"
        )
        # The discovery lists were reordered to name the .aw/ location first.
        self.assertIn(".aw/records/plans/pending/", proto)


if __name__ == "__main__":
    unittest.main()
