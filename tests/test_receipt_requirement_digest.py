"""Receipt validity is keyed on the FROZEN REGION, not the whole file (wtiso-03 `rchpms` E-01..E-03).

Fixes backlog `xmqv5l`. The begin receipt used to be invalidated by ANY byte change to the plan
(`plan_content_digest`), but a CORRECT execution is required to edit its own plan - mark each E item
performed, fill each V item's `Observed evidence`/`Result`, append a `## Workflow history` line - so
the receipt always went stale and `finalize_precheck` refused every self-finalizing run with "the
begin receipt ... is STALE".

The guard must therefore be rebound, NOT removed, so these tests assert BOTH directions:

  * ADVERSARIAL GUARD (a), the regression: self-execution edits keep the receipt CURRENT
    (`test_self_execution_edits_keep_receipt_current`).
  * ADVERSARIAL GUARD (b), guard-not-too-loose: a `Scope-Paths` or E/V requirement edit still
    INVALIDATES (`test_scope_or_requirement_edit_invalidates_receipt`). Without this half the fix
    would be indistinguishable from deleting the check.

Stdlib unittest with git-backed throwaway repos, matching `tests/test_ipd_lifecycle_cli.py` (the
receipt binds a real base HEAD and refuses a dirty in-scope tree).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lifecycle as LC

_SCOPE = "agent_workflows/demo.py, tests/test_demo.py"


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    # Mirror the real repo: receipts live in the gitignored .aw/state/ tree.
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def _ready_plan_text(*, plan_id: str = "abc123", scope_paths: str = _SCOPE) -> str:
    """A conforming child IPD that lints CONFORMING at the pre-execution checkpoint."""
    txt = A.build_skeleton(
        kind="child",
        title="demo",
        author="tester",
        when="2026-08-24",
        set_name="demo",
        order=1,
        plan_id=plan_id,
    )
    out = []
    in_meta = True
    for ln in txt.splitlines():
        if ln.startswith("## "):
            in_meta = False
        if in_meta and ln.startswith("- Status:"):
            out.append("- Status: approved")
            continue
        if in_meta and ln.startswith("- Scope-Paths:"):
            out.append("- Scope-Paths: " + scope_paths)
            continue
        if in_meta and ln.startswith("- Item-Dependencies:"):
            out.append("- Item-Dependencies: none")
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            out.append("- Approval: 2026-08-24, human: approved")
    return "\n".join(out) + "\n"


def _executed_like(text: str) -> str:
    """Apply exactly the edits a CONFORMING self-execution makes to its own plan.

    This is the mutation set backlog xmqv5l names: checkbox marks, `Execution state:`, `Result:`,
    `Observed evidence:`, and an appended `## Workflow history` record.
    """
    out = text.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    out = (
        out.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n",
            "  - Observed evidence: pasted real command output, exit 0.\n",
            1,
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    return out + "\n- 2026-08-24 executed (opencode/test): all V items verified.\n"


class FrozenRegionDigestTests(unittest.TestCase):
    """E-01: the pure digest covers the contract and excludes mutable execution state."""

    def test_frozen_region_digest_ignores_checklist_state(self):
        text = _ready_plan_text()
        base = LC.frozen_region_digest(text)

        # A stable 64-char hex sha256.
        self.assertEqual(len(base), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in base))
        self.assertEqual(base, LC.frozen_region_digest(text), "digest is not stable")

        # Differing ONLY in execution/validation state, history, and checkbox marks -> IDENTICAL.
        executed = _executed_like(text)
        self.assertNotEqual(executed, text, "the self-execution edit did not apply")
        self.assertEqual(
            base,
            LC.frozen_region_digest(executed),
            "checklist state/evidence/history must NOT affect the frozen-region digest",
        )
        # Sanity: the WHOLE-FILE digest *does* change - i.e. the old key was the bug.
        self.assertNotEqual(
            LC.plan_content_digest(text), LC.plan_content_digest(executed)
        )

        # Changing an E-item's ACTION text is a contract change -> DIFFERENT.
        retasked = text.replace("- [ ] E-01 ", "- [ ] E-01 REWRITTEN ACTION ", 1)
        self.assertNotEqual(retasked, text, "the E-text edit did not apply")
        self.assertNotEqual(base, LC.frozen_region_digest(retasked))

        # Changing a Scope-Paths entry is a contract change -> DIFFERENT.
        rescoped = _ready_plan_text(scope_paths=_SCOPE + ", agent_workflows/extra.py")
        self.assertNotEqual(base, LC.frozen_region_digest(rescoped))


class ReceiptBindingTests(unittest.TestCase):
    """E-02/E-03: the receipt carries the new key, and the predicate uses it."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        self.plan = d / "20260824-demo-01-abc123-demo.ipd.md"
        self.plan.write_text(_ready_plan_text(), encoding="utf-8")
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _begin(self):
        res = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        return stored

    def test_receipt_carries_frozen_region_digest(self):
        """V-02: the receipt records the new validity key and keeps the whole legacy shape."""
        # The schema version increased (v1 -> v2) for the additive field.
        self.assertGreater(LC.RECEIPT_SCHEMA_VERSION, 1)
        self.assertEqual(LC.RECEIPT_SCHEMA_VERSION, 2)

        stored = self._begin()
        plan_text = self.plan.read_text()

        self.assertTrue(stored.get("frozen_region_digest"))
        self.assertEqual(
            stored["frozen_region_digest"], LC.frozen_region_digest(plan_text)
        )
        # The pre-existing bindings are all still present (no reader is broken).
        for field in (
            "requirement_digest",
            "scope_paths",
            "base_head",
            "plan_content_digest",
        ):
            self.assertIn(field, stored)
            self.assertTrue(stored[field], f"{field} is empty")
        self.assertEqual(stored["schema_version"], LC.RECEIPT_SCHEMA_VERSION)

    def test_self_execution_edits_keep_receipt_current(self):
        """ADVERSARIAL GUARD (a) - the xmqv5l regression.

        Begin, then make exactly the edits a conforming execution makes, and assert the receipt is
        STILL current. Before E-03 this returned False and finalize refused as STALE.
        """
        stored = self._begin()
        self.assertTrue(LC.receipt_is_current(stored, self.plan.read_text()))

        edited = _executed_like(self.plan.read_text())
        self.assertNotEqual(edited, self.plan.read_text())
        self.assertTrue(
            LC.receipt_is_current(stored, edited),
            "self-execution edits must NOT invalidate the begin receipt (xmqv5l)",
        )

    def test_scope_or_requirement_edit_invalidates_receipt(self):
        """ADVERSARIAL GUARD (b) - the guard must not be merely loosened.

        A change to the reviewed CONTRACT makes this a different plan than the one the pre-execution
        gate approved, so the receipt MUST go stale.
        """
        stored = self._begin()

        rescoped = self.plan.read_text().replace(
            "- Scope-Paths: " + _SCOPE,
            "- Scope-Paths: " + _SCOPE + ", agent_workflows/snuck_in.py",
        )
        self.assertIn("snuck_in.py", rescoped, "the scope edit did not apply")
        self.assertFalse(
            LC.receipt_is_current(stored, rescoped),
            "a Scope-Paths change MUST invalidate the receipt",
        )

        retasked = self.plan.read_text().replace(
            "- [ ] E-01 ", "- [ ] E-01 DIFFERENT REQUIREMENT ", 1
        )
        self.assertIn(
            "DIFFERENT REQUIREMENT", retasked, "the E-text edit did not apply"
        )
        self.assertFalse(
            LC.receipt_is_current(stored, retasked),
            "an E-item requirement change MUST invalidate the receipt",
        )

    def test_legacy_receipt_without_frozen_region_uses_whole_file(self):
        """A pre-Phase-2 (v1) receipt is judged by the OLD whole-file rule, never spuriously accepted."""
        stored = self._begin()
        plan_text = self.plan.read_text()

        legacy = dict(stored)
        legacy.pop("frozen_region_digest", None)
        legacy["schema_version"] = 1
        self.assertNotIn("frozen_region_digest", legacy)

        # Unchanged text: the legacy whole-file comparison still matches.
        self.assertTrue(LC.receipt_is_current(legacy, plan_text))

        # A non-contract edit that the NEW rule would forgive still invalidates a LEGACY receipt,
        # because that receipt was never bound under the new key.
        commented = plan_text + "\n<!-- a non-contract edit -->\n"
        self.assertTrue(
            LC.receipt_is_current(stored, commented),
            "sanity: the v2 receipt forgives a non-contract edit",
        )
        self.assertFalse(
            LC.receipt_is_current(legacy, commented),
            "a legacy v1 receipt must fall back to the whole-file rule",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
