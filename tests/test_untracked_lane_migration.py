"""Tests for awuntracked Order 01: migrating an existing repo's `local/` quarantine lanes to
`untracked/` (rename + content preservation + idempotency)."""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine

REPO_ROOT = Path(__file__).resolve().parents[1]

# The retired quarantine-lane names. The live lane is `<tree>/untracked/`, ignored by
# `records/*/untracked/` in `.aw/.gitignore`; `<tree>/local/` is NOT ignored, so prose that
# still names it sends an agent to write a candid handoff into a COMMITTABLE path while
# promising the opposite. That is a privacy defect, not a cosmetic stale name.
RETIRED_LANE_RE = re.compile(r"(?:prompts|comms)/local/")

# Historical records are immortal by design: an executed plan or a past decision describes the
# repo as it WAS, so rewriting it would falsify the record. Only the LIVE instructional surface
# (what an agent reads to decide where to write TODAY) is governed here.
_EXEMPT_PREFIXES = (
    ".aw/records/plans/",  # executed/superseded plans: historical
    ".aw/records/runs/",  # run logs: historical
    ".aw/records/prompts/untracked/",  # gitignored scratch
    ".aw/worktrees/",  # lane checkouts, not this tree's surface
    "opencode-recovery/",  # archived session transcripts
    "tmp/",  # scratch clones
    ".agent-workflows-installer-backups/",  # pre-install snapshots
    "workflow-artifacts/",  # dated workflow outputs: historical
    "tests/test_untracked_lane_migration.py",  # this guard names the retired string on purpose
    "CHANGELOG.md",  # release history: describes the rename itself
    "DECISIONS.md",  # ADR record: describes the rename itself
    "tests/test_layout_migration.py",  # migrates FROM the retired layout, must name it
    ".aw/records/research/",  # research reports: dated findings, historical
    ".aw/records/specs/",  # specs record the convention as designed at the time
    ".aw/records/prompts/superseded/",  # retired prompts: historical
    # Opaque CLI-argument fixtures for the legacy `tools/agy_run.py` shim. These assert that a
    # path string round-trips through arg parsing; they instruct nobody where to write.
    "tools/test_agy_run.py",
)


class UntrackedLaneMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.dirs = {
            "prompts": ".aw/records/prompts",
            "comms": ".aw/records/comms",
        }
        pl = self.root / ".aw/records/prompts/local"
        pl.mkdir(parents=True)
        (pl / "notes.md").write_text("draft prompt\n", encoding="utf-8")
        cl = self.root / ".aw/records/comms/local/inbox"
        cl.mkdir(parents=True)
        (cl / "msg.md").write_text("hello\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_rename_preserves_contents(self):
        renamed = engine.migrate_local_lanes_to_untracked(self.root, self.dirs)
        self.assertIn(".aw/records/prompts/untracked", renamed)
        self.assertIn(".aw/records/comms/untracked", renamed)
        self.assertFalse((self.root / ".aw/records/prompts/local").exists())
        self.assertEqual(
            (self.root / ".aw/records/prompts/untracked/notes.md").read_text(),
            "draft prompt\n",
        )
        self.assertEqual(
            (self.root / ".aw/records/comms/untracked/inbox/msg.md").read_text(),
            "hello\n",
        )

    def test_idempotent(self):
        engine.migrate_local_lanes_to_untracked(self.root, self.dirs)
        again = engine.migrate_local_lanes_to_untracked(self.root, self.dirs)
        self.assertEqual(again, [])  # nothing left to rename

    def test_noop_when_no_local(self):
        empty = Path(self._tmp.name) / "sub"
        empty.mkdir()
        self.assertEqual(engine.migrate_local_lanes_to_untracked(empty, self.dirs), [])


class RetiredLaneNameNotInLiveProseTests(unittest.TestCase):
    """Fail when the LIVE instructional surface still names the retired `local/` quarantine lane.

    Why this guard exists: the `local/` -> `untracked/` rename was attempted three times
    (`awuntracked-01` c32roo, `awuntrackedfix-01` njfyjt, `lanename-01` j4v6ga) and each pass
    fixed only the call sites its hand-written `Scope-Paths` happened to enumerate. j4v6ga's own
    review caught three user-facing docs that "the plan's Scope-Paths named none of". Enumerating
    paths by hand cannot converge; a deterministic check over the whole tracked surface can.
    """

    def test_no_tracked_live_file_names_the_retired_lane(self):
        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split("\0")

        offenders: list[str] = []
        for rel in tracked:
            if not rel or rel.startswith(_EXEMPT_PREFIXES):
                continue
            if not rel.endswith((".md", ".py", ".toml", ".json", ".yaml", ".yml")):
                continue
            path = REPO_ROOT / rel
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if RETIRED_LANE_RE.search(line):
                    offenders.append(f"{rel}:{lineno}: {line.strip()[:120]}")

        self.assertEqual(
            offenders,
            [],
            "The retired `local/` quarantine lane is still named in live prose. The live lane is "
            "`untracked/` (gitignored via `records/*/untracked/`); `local/` is NOT gitignored, so "
            "these instructions route sensitive handoffs into a committable path. Fix the prose, or "
            "add a justified exemption to _EXEMPT_PREFIXES if the file is genuinely historical:\n"
            + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
