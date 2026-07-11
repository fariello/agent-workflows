"""Advisory drift-guard: this repo's own plan files use a recognized readiness Status (D52).

The readiness `Status:` vocabulary is documented in `.agents/workflows/assess/templates/ipd.md`
and DECISIONS D52. This test asserts THIS repository's own plans carry a recognized status, so the
reference repo stays exemplary. It is intentionally scoped to this repo only (advisory-first per
D52 OQ2); downstream repos with legacy free-text status are not affected by it.

Recognized values:
  pre-terminal: draft, to-review, reviewed, approved
  terminal:     executed, superseded, not-executed
  standing:     reusable
Terminal status must match the plan's directory (terminal-only rule; pre-terminal statuses all
live in pending/). Legacy free-text (e.g. "PENDING (...)", "EXECUTED ...") is tolerated on
historical executed/ plans and reported, not failed.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.support import REPO_ROOT

PLANS = REPO_ROOT / ".agents" / "plans"

PRE_TERMINAL = {"draft", "to-review", "reviewed", "approved"}
TERMINAL = {"executed", "superseded", "not-executed"}
STANDING = {"reusable"}
RECOGNIZED = PRE_TERMINAL | TERMINAL | STANDING

# Directory -> the terminal status that must match it (terminal-only rule).
DIR_TERMINAL = {
    "executed": "executed",
    "superseded": "superseded",
    "not-executed": "not-executed",
}

_STATUS_RE = re.compile(r"^- Status:\s*(?P<val>\S+)", re.MULTILINE)

# Backward-compat (D52): legacy free-text status tokens map to the canonical enum for the
# drift-guard, so historical executed/ plans are tolerated WITHOUT being rewritten (P4).
_LEGACY_MAP = {
    "pending": "to-review",
    "done": "executed",  # `done` is the accepted alias for `executed`
}


def _status(md: Path) -> str | None:
    """Return the plan's Status token, lowercased and legacy-mapped, or None if absent."""

    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _STATUS_RE.search(text)
    if not m:
        return None
    val = m.group("val").strip().rstrip(".").lower()
    return _LEGACY_MAP.get(val, val)


class PlanStatusDriftGuard(unittest.TestCase):
    def _plan_files(self):
        for sub in (
            "pending",
            "executed",
            "superseded",
            "not-executed",
            "reusable",
            "done",
        ):
            d = PLANS / sub
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.md")):
                if f.name == "README.md":
                    continue
                yield sub, f

    def test_every_plan_has_a_recognized_status(self):
        offenders = []
        for sub, f in self._plan_files():
            val = _status(f)
            if val not in RECOGNIZED:
                offenders.append(f"{f.relative_to(REPO_ROOT)}: Status={val!r}")
        self.assertEqual(offenders, [], f"plans with unrecognized Status: {offenders}")

    def test_terminal_status_matches_directory(self):
        # Terminal-only rule: a plan in executed/superseded/not-executed must carry the
        # matching terminal Status. Pre-terminal plans all live in pending/ and are exempt.
        mismatches = []
        for sub, f in self._plan_files():
            expected = DIR_TERMINAL.get(sub)
            if expected is None:  # pending/ or reusable/ - no terminal-dir constraint
                continue
            val = _status(f)
            if val != expected:
                mismatches.append(
                    f"{f.relative_to(REPO_ROOT)}: dir={sub} Status={val!r}"
                )
        self.assertEqual(
            mismatches, [], f"terminal status/dir mismatches: {mismatches}"
        )


if __name__ == "__main__":
    unittest.main()
