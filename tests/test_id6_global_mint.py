"""Behavioral tests for global_id6s and mint_id6 over-collection of quoted id6s (IPD ztx39t)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core

RESEARCH = ".aw/records/research"

QUOTING_REPORT_TEXT = """---
id: own111
kind: research-report
---

# Report

Here is an example of a plan's metadata block:

```markdown
- Id: qut111
- Status: approved
```
"""

NON_QUOTING_REPORT_TEXT = """---
id: own111
kind: research-report
---

# Report

No quoted metadata block here.
"""


class GlobalMintSupersetTests(unittest.TestCase):
    """Behavioral tests for global_id6s superset collection and mint refusal."""

    def test_the_mint_set_over_collects_quoted_ids_and_that_is_deliberate(self):
        """E-07 / ztx39t E-01: identity readers are UNBOUNDED, so global_id6s is a conservative superset."""
        quoted = "qut111"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / RESEARCH / "20260101-demo-01-own111-r.research-report.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(QUOTING_REPORT_TEXT, encoding="utf-8")

            got = core.global_id6s(root)
            self.assertIn(
                "own111",
                got,
                "the document's OWN declared identity must be collected",
            )
            self.assertIn(
                quoted,
                got,
                "MEASURED BEHAVIOR, deliberately pinned: an id6 QUOTED inside a fenced code block is "
                "collected too, because the underlying identity readers are unbounded. That makes the set "
                "a conservative SUPERSET, which is deliberate for MINTING (sk7ggr E-07) and wrong for CHECKING. "
                "If this assertion starts failing because a reader was bounded, the mint path is still "
                "correct (the set merely got tighter) - see IPD 76w6mq / xvon5j",
            )

    def test_mint_id6_refuses_quoted_id_and_mints_next_candidate(self):
        """E-02: mint_id6 refuses quoted id6 and advances to next candidate; control tree mints quoted id6."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / RESEARCH / "20260101-demo-01-own111-r.research-report.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(QUOTING_REPORT_TEXT, encoding="utf-8")

            chars = iter("qut111fre111")

            def _rng(_alphabet):
                return next(chars)

            minted = core.mint_id6(root, _rng=_rng)
            self.assertEqual(
                minted,
                "fre111",
                "mint_id6 must refuse the quoted candidate 'qut111' and advance to 'fre111'",
            )

        with tempfile.TemporaryDirectory() as td_control:
            root_control = Path(td_control)
            p_control = (
                root_control / RESEARCH / "20260101-demo-01-own111-r.research-report.md"
            )
            p_control.parent.mkdir(parents=True, exist_ok=True)
            p_control.write_text(NON_QUOTING_REPORT_TEXT, encoding="utf-8")

            chars_control = iter("qut111fre111")

            def _rng_control(_alphabet):
                return next(chars_control)

            minted_control = core.mint_id6(root_control, _rng=_rng_control)
            self.assertEqual(
                minted_control,
                "qut111",
                "on the control tree without the quoted block, the same candidate 'qut111' is free and must be minted",
            )


if __name__ == "__main__":
    unittest.main()
