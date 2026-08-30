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
#
# Two forms are checked, because catching only the first is what let a whole class of stale
# references survive an earlier sweep (IPD lanename-01 j4v6ga):
#   1. the PATH form, e.g. `.aw/records/prompts/local/`, which an agent can copy and write to; and
#   2. the BARE LANE-NAME form, e.g. a `## The `local/` quarantine lane` heading or a
#      `(shared/, local/)` tree listing, which teaches the retired name without ever spelling a
#      full path. The prompts READMEs and three user-facing docs carried only form 2 and so passed
#      a form-1-only check while still documenting the wrong lane.
RETIRED_LANE_RE = re.compile(r"(?:prompts|comms)/local/")
# Deliberately NOT a bare `local/` match: prose legitimately contains unrelated paths such as
# "local/system" or "local/runtime". This targets the lane-name usages only, i.e. a backticked
# `local/` or a bare `local/` appearing as an item in a parenthesized/comma-separated dir listing.
RETIRED_LANE_NAME_RE = re.compile(r"`local/`|(?<=[(,]\s)local/(?=[),\s])")

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

# Additional exemptions that apply ONLY to the bare lane-name form. These are places that must be
# able to SAY the retired name without instructing anyone to use it.
_NAME_FORM_EXTRA_EXEMPT_PREFIXES = (
    ".aw/records/prompts/executed/",  # run prompts: historical, describe the `local/` era
    ".aw/records/walkthroughs/",  # narrative records of what was true at the time
)

# The migration code and the docs that explain it MUST name the lane they migrate FROM, otherwise
# the comment cannot say what it does. Exempted by exact path, not prefix, so a new file cannot
# inherit the exemption silently.
_NAME_FORM_EXEMPT_FILES = frozenset(
    {
        "agent_workflows/engine.py",  # migrate_local_lanes_to_untracked and its call site
        "agent_workflows/layout_migration.py",  # docstring naming the legacy lane it migrates
    }
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

    @staticmethod
    def _tracked_live_files(extra_exempt_prefixes=(), exempt_files=frozenset()):
        """Yield (rel, text) for every tracked, non-historical, text-bearing file.

        Enumerates via `git ls-files`, NOT a filesystem walk, so gitignored working material and
        untracked scratch clones are structurally out of scope rather than needing an ignore list
        that must be maintained (IPD lanename-01 OQ-02).
        """
        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split("\0")
        for rel in tracked:
            if not rel or rel in exempt_files:
                continue
            if rel.startswith(_EXEMPT_PREFIXES) or rel.startswith(
                extra_exempt_prefixes
            ):
                continue
            if not rel.endswith((".md", ".py", ".toml", ".json", ".yaml", ".yml")):
                continue
            try:
                yield rel, (REPO_ROOT / rel).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

    def test_no_tracked_live_file_names_the_retired_lane(self):
        offenders = [
            f"{rel}:{lineno}: {line.strip()[:120]}"
            for rel, text in self._tracked_live_files()
            for lineno, line in enumerate(text.splitlines(), 1)
            if RETIRED_LANE_RE.search(line)
        ]

        self.assertEqual(
            offenders,
            [],
            "The retired `local/` quarantine lane is still named in live prose. The live lane is "
            "`untracked/` (gitignored via `records/*/untracked/`); `local/` is NOT gitignored, so "
            "these instructions route sensitive handoffs into a committable path. Fix the prose, or "
            "add a justified exemption to _EXEMPT_PREFIXES if the file is genuinely historical:\n"
            + "\n".join(offenders),
        )

    def test_no_tracked_live_file_uses_the_retired_lane_NAME(self):
        """The path-form check above cannot see a doc that names the lane without a full path.

        That gap is not hypothetical: it is exactly how `.aw/records/prompts/README.md` kept a
        `## The `local/` quarantine lane` heading, how the SHIPPED template kept the same text, and
        how `README.md`/`ARCHITECTURE.md` kept a `(shared/, local/)` listing, all while the
        path-form guard reported clean. A doc that teaches the retired name still misroutes an
        agent, so the name form is checked too.
        """
        allowed_history = "its retired name was `local/`"
        offenders: list[str] = []
        for rel, text in self._tracked_live_files(
            extra_exempt_prefixes=_NAME_FORM_EXTRA_EXEMPT_PREFIXES,
            exempt_files=_NAME_FORM_EXEMPT_FILES,
        ):
            for lineno, line in enumerate(text.splitlines(), 1):
                if not RETIRED_LANE_NAME_RE.search(line):
                    continue
                # One sanctioned mention: a doc may map the old name to the new one exactly once so
                # a reader of an older checkout can follow (IPD lanename-01 OQ-01).
                if allowed_history in line:
                    continue
                offenders.append(f"{rel}:{lineno}: {line.strip()[:120]}")

        self.assertEqual(
            offenders,
            [],
            "The retired `local/` lane NAME is still used in live prose (headings, tree listings, "
            "or narrative), even though no full `local/` PATH remains. The lane is `untracked/`. "
            "Rename it, or, if the line legitimately maps the old name to the new one for readers "
            'of older checkouts, phrase it as "its retired name was `local/`":\n'
            + "\n".join(offenders),
        )

    def test_name_form_guard_does_not_scan_historical_records(self):
        """The guard must never pressure a future agent into rewriting an immutable record.

        Asserts the exemption POSITIVELY: a known historical file that really does contain the
        retired lane name is absent from the scanned set, so a green run cannot be mistaken for
        "history was cleaned up".
        """
        historical = (
            ".aw/records/prompts/executed/"
            "20260725-2341-01-aw-delivery-and-clean-delta.prompt.md"
        )
        self.assertTrue(
            (REPO_ROOT / historical).is_file(), f"fixture moved: {historical}"
        )
        self.assertIn(
            "`local/` lanes",
            (REPO_ROOT / historical).read_text(encoding="utf-8"),
            "fixture no longer contains the retired lane name; pick another historical file",
        )
        scanned = {
            rel
            for rel, _ in self._tracked_live_files(
                extra_exempt_prefixes=_NAME_FORM_EXTRA_EXEMPT_PREFIXES,
                exempt_files=_NAME_FORM_EXEMPT_FILES,
            )
        }
        self.assertNotIn(historical, scanned)
        for prefix in (
            ".aw/records/plans/",
            ".aw/records/research/",
            ".aw/records/specs/",
        ):
            self.assertFalse(
                [rel for rel in scanned if rel.startswith(prefix)],
                f"historical tree {prefix} must be exempt from the lane-name guard",
            )


if __name__ == "__main__":
    unittest.main()
