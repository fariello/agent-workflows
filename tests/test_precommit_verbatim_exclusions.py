"""Tests pinning .pre-commit-config.yaml verbatim-preservation exclusions against artifact_core.

Precedent and rationale:
Like `tests/test_executed_transition_gate_e2e.py::PreCommitConfigStageRegistrationTests`,
this is a CONFIGURATION assertion ensuring that .pre-commit-config.yaml does not silently drift
from the toolkit's writer-side policy in `agent_workflows.artifact_core._VERBATIM_PRESERVED_SEGMENTS`.

Without this pin, physical layout migrations (such as spec 20260817-2124-01 which flattened
`.aw/records/docs/research/` to `.aw/records/research/`) update one and leave the other stale,
causing content-mutating hooks to silently rewrite as-delivered research artifacts.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import List

import yaml

from agent_workflows import artifact_core


class TestPrecommitVerbatimExclusions(unittest.TestCase):
    """Pin the four mutating hooks' exclude regexes to the live research trees."""

    MUTATING_HOOK_IDS = {
        "trailing-whitespace",
        "end-of-file-fixer",
        "ruff",
        "ruff-format",
    }

    SAFETY_HOOK_IDS = {
        "gitleaks",
        "check-added-large-files",
        "local-leaks",
    }

    # Allowlist of legacy paths intentionally retained in mutating hook exclude regexes.
    # BLIND SPOT NOTE: The allowlist entry ('.agents/docs/research/') is load-bearing because
    # this repository has no .agents/ tree, but target repositories on the legacy layout
    # still use it (and research_contract.resolve_research_root falls back to it).
    # The allowlist is the one path whose deadness this test cannot detect; if a future
    # migration flattens .agents/docs/research, this test will stay green on the stale path.
    # Any legacy-layout change requires re-checking this entry BY HAND.
    LEGACY_ALLOWLIST = {
        ".agents/docs/research/",
        ".agents/docs/research",
    }

    # Spec 20260817-2124-01 G4 flattened .aw/records/docs/research to .aw/records/research
    # and refused an intermediate .aw/records/docs/ migration hop. The tuple entry
    # ('.aw', 'records', 'docs', 'research') in artifact_core._VERBATIM_PRESERVED_SEGMENTS
    # is unreachable by design in repo layout; it is retained in the writer tuple only
    # so an already-written file in a partially-migrated checkout is still passed through
    # byte-for-byte by the writer. In the pre-commit hook configuration, E-01 specifically
    # deleted this dead path, so it must not be in the hook probe set.
    EXCLUDED_WRITER_SEGMENTS = {
        (".aw", "records", "docs", "research"),
    }

    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.config_path = self.repo_root / ".pre-commit-config.yaml"
        self.assertTrue(
            self.config_path.is_file(), f"Missing config: {self.config_path}"
        )
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config_data = yaml.safe_load(f)

    def _all_hooks(self):
        """Iterate all hooks defined in the configuration."""
        for repo in self.config_data.get("repos", []):
            for hook in repo.get("hooks", []):
                yield hook

    def _get_derived_probe_paths(self) -> List[str]:
        """Derive repo-relative probe paths from artifact_core._VERBATIM_PRESERVED_SEGMENTS.

        Filters out dead segments (EXCLUDED_WRITER_SEGMENTS) as specified in IPD 3fat1n E-03(a).
        """
        probe_paths = []
        for segments in artifact_core._VERBATIM_PRESERVED_SEGMENTS:
            if segments in self.EXCLUDED_WRITER_SEGMENTS:
                continue
            tree = "/".join(segments)
            probe_paths.append(f"{tree}/x.py")
        return probe_paths

    def test_mutating_hook_ids_are_complete(self) -> None:
        """(d) Assert all four mutating hook ids are found in the parsed config.

        Ensures that tests do not vacuously pass over an empty selection if hook ids are renamed or missing.
        """
        found_ids = {hook["id"] for hook in self._all_hooks()}
        missing = self.MUTATING_HOOK_IDS - found_ids
        self.assertEqual(
            missing,
            set(),
            f"Mutating hook ids missing from .pre-commit-config.yaml: {missing}",
        )
        selected_mutating = [
            hook for hook in self._all_hooks() if hook["id"] in self.MUTATING_HOOK_IDS
        ]
        self.assertEqual(
            len(selected_mutating),
            4,
            f"Expected exactly 4 mutating hooks configured, found {len(selected_mutating)}",
        )

    def test_mutating_hooks_exclude_verbatim_preserved_trees(self) -> None:
        """(a) Assert every mutating hook's exclude regex covers the verbatim-preserved probe paths."""
        probe_paths = self._get_derived_probe_paths()
        # Verify derived probe set contains the expected trees and not the excluded dead tree
        probe_trees = {Path(p).parent.as_posix() for p in probe_paths}
        self.assertIn(".aw/records/research", probe_trees)
        self.assertIn(".agents/docs/research", probe_trees)
        self.assertNotIn(".aw/records/docs/research", probe_trees)

        selected_mutating = [
            hook for hook in self._all_hooks() if hook["id"] in self.MUTATING_HOOK_IDS
        ]
        self.assertEqual(len(selected_mutating), 4)

        for hook in selected_mutating:
            hook_id = hook["id"]
            exclude_pattern = hook.get("exclude")
            self.assertIsNotNone(
                exclude_pattern,
                f"Mutating hook '{hook_id}' has no 'exclude' key configured",
            )
            for probe_path in probe_paths:
                matched = re.search(exclude_pattern, probe_path)
                self.assertIsNotNone(
                    matched,
                    f"Mutating hook '{hook_id}' does not exclude verbatim-preserved tree probe '{probe_path}' "
                    f"(exclude pattern: {exclude_pattern!r})",
                )

    def test_mutating_hook_excludes_contain_no_dead_paths(self) -> None:
        """(b) Assert every path alternative in mutating hook exclude regexes resolves to a real dir or allowlist."""
        selected_mutating = [
            hook for hook in self._all_hooks() if hook["id"] in self.MUTATING_HOOK_IDS
        ]
        self.assertEqual(len(selected_mutating), 4)

        for hook in selected_mutating:
            hook_id = hook["id"]
            exclude_pattern = hook.get("exclude", "")
            # Extract path alternatives from regex grouping e.g. '^(\.agents/...|\.aw/...)'
            m = re.search(r"\((.*?)\)", exclude_pattern)
            raw_alts = m.group(1).split("|") if m else exclude_pattern.split("|")
            alternatives = [
                alt.replace(r"\.", ".").strip() for alt in raw_alts if alt.strip()
            ]

            for alt in alternatives:
                clean_alt = alt.strip("^$()")
                exists = (self.repo_root / clean_alt).is_dir()
                allowlisted = (
                    clean_alt in self.LEGACY_ALLOWLIST
                    or clean_alt.rstrip("/") in self.LEGACY_ALLOWLIST
                    or (clean_alt + "/") in self.LEGACY_ALLOWLIST
                )
                self.assertTrue(
                    exists or allowlisted,
                    f"Exclude regex for hook '{hook_id}' contains dead path alternative '{clean_alt}' "
                    f"which does not exist in repository and is not in legacy allowlist {self.LEGACY_ALLOWLIST}. "
                    "(Allowlist reason: .agents/docs/research/ is retained for target repositories on the legacy "
                    "layout; dead paths must be removed, not allowlisted).",
                )

    def test_safety_hooks_do_not_exclude_verbatim_preserved_trees(self) -> None:
        """(c) Assert safety hooks (gitleaks, check-added-large-files, local-leaks) do not exclude verbatim trees."""
        probe_paths = self._get_derived_probe_paths()
        selected_safety = [
            hook for hook in self._all_hooks() if hook["id"] in self.SAFETY_HOOK_IDS
        ]
        # At least gitleaks, check-added-large-files, local-leaks should be present
        found_safety_ids = {h["id"] for h in selected_safety}
        self.assertEqual(
            self.SAFETY_HOOK_IDS,
            found_safety_ids,
            f"Safety hooks missing from config: {self.SAFETY_HOOK_IDS - found_safety_ids}",
        )

        for hook in selected_safety:
            hook_id = hook["id"]
            exclude_pattern = hook.get("exclude")
            if not exclude_pattern:
                continue
            for probe_path in probe_paths:
                matched = re.search(exclude_pattern, probe_path)
                self.assertIsNone(
                    matched,
                    f"Safety hook '{hook_id}' must NOT exclude verbatim-preserved tree probe '{probe_path}'",
                )
