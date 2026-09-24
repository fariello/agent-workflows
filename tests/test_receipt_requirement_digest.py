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

SECOND SUBJECT (rcptwiden `63425h` E-03/E-05/E-08/E-09): the STRUCTURAL decomposition of a frozen-region
MISMATCH, which is what lets finalize tell an honest additive scope DECLARATION from a contract rewrite.
`receipt_is_current` returns one boolean for both, and that conflation stranded three of twelve items in
run `run-20260917T023628Z-4108757` ($95.71, 3h10m) while the CONCEALED equivalent finalized fine. The
comparison lives here rather than in the CLI test file because this is the file that owns
`frozen_region_digest`, the v2 receipt binding and the legacy v1 fallback, and the new predicate is a
narrowing of exactly those. See :class:`FrozenRegionComparisonTests`,
:class:`WideningEligibilityTests` and :class:`IneligibleReceiptShapeTests`.
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


class _WideningFixture(unittest.TestCase):
    """Shared fixture: a real git repo, a real begin receipt, and scope-mutation helpers."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir(exist_ok=True)
        (self.root / "tests").mkdir(exist_ok=True)
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        self.plan = d / "20260824-demo-01-abc123-demo.ipd.md"
        self.plan.write_text(_ready_plan_text(), encoding="utf-8")
        (self.root / "agent_workflows" / "demo.py").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("x\n", encoding="utf-8")
        _commit_all(self.root, "init")
        res = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        self.receipt = stored
        self.base_text = self.plan.read_text()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _rescoped(self, value: str) -> str:
        out = self.base_text.replace(
            "- Scope-Paths: " + _SCOPE, "- Scope-Paths: " + value
        )
        self.assertNotEqual(out, self.base_text, "the scope edit did not apply")
        return out

    def _widened(self, *added: str) -> str:
        return self._rescoped(", ".join([_SCOPE, *added]))

    def _compare(self, text: str) -> LC.FrozenRegionComparison:
        return LC.frozen_region_comparison(self.receipt, text, repo_root=self.root)


class FrozenRegionComparisonTests(_WideningFixture):
    """E-03: the SUBSTITUTION TEST decomposes a mismatch instead of collapsing it to one boolean."""

    def test_additive_widening_reports_added_and_non_scope_identical(self):
        """The measured incident's shape: one added path, nothing else changed."""
        cmp_result = self._compare(self._widened("tests/test_extra.py"))
        self.assertEqual(list(cmp_result.added), ["tests/test_extra.py"])
        self.assertEqual(list(cmp_result.removed), [])
        self.assertTrue(
            cmp_result.non_scope_identical,
            "substituting the receipt's scope must reproduce the stored digest",
        )
        self.assertTrue(cmp_result.eligible, cmp_result.ineligible_reason)
        self.assertTrue(LC.widening_is_acceptable(cmp_result))

    def test_requirement_rewrite_is_not_scope_identical(self):
        """GUARD-NOT-TOO-LOOSE: a rewritten E-item is a contract change and must never be accepted."""
        retasked = self.base_text.replace(
            "- [ ] E-01 ", "- [ ] E-01 REWRITTEN REQUIREMENT ", 1
        )
        self.assertIn("REWRITTEN REQUIREMENT", retasked)
        cmp_result = self._compare(retasked)
        self.assertEqual(list(cmp_result.added), [])
        self.assertFalse(cmp_result.non_scope_identical)
        self.assertFalse(LC.widening_is_acceptable(cmp_result))

    def test_widening_PLUS_requirement_rewrite_is_refused(self):
        """The adversarial combination: additions must not launder a simultaneous rewrite."""
        both = self._widened("tests/test_extra.py").replace(
            "- [ ] E-01 ", "- [ ] E-01 REWRITTEN REQUIREMENT ", 1
        )
        cmp_result = self._compare(both)
        self.assertEqual(list(cmp_result.added), ["tests/test_extra.py"])
        self.assertFalse(cmp_result.non_scope_identical)
        self.assertFalse(LC.widening_is_acceptable(cmp_result))

    def test_receipt_is_current_is_unchanged_by_this_work(self):
        """`receipt_is_current` keeps its exact meaning; the new predicate is a SECOND question."""
        # Unmodified plan: still current.
        self.assertTrue(LC.receipt_is_current(self.receipt, self.base_text))
        # Self-execution edits: still current (the xmqv5l fix is untouched).
        self.assertTrue(
            LC.receipt_is_current(self.receipt, _executed_like(self.base_text))
        )
        # A widening: still NOT current. The widening accept happens downstream, in finalize.
        self.assertFalse(
            LC.receipt_is_current(self.receipt, self._widened("tests/test_extra.py")),
            "receipt_is_current must NOT be loosened; finalize asks the second question",
        )
        # A requirement rewrite: still NOT current.
        self.assertFalse(
            LC.receipt_is_current(
                self.receipt,
                self.base_text.replace("- [ ] E-01 ", "- [ ] E-01 REWRITTEN ", 1),
            )
        )

    def test_removal_is_reported_and_never_acceptable(self):
        """E-05: a contract REDUCTION is named and refused, in either direction."""
        narrowed = self._rescoped("agent_workflows/demo.py")
        cmp_result = self._compare(narrowed)
        self.assertEqual(list(cmp_result.removed), ["tests/test_demo.py"])
        self.assertEqual(list(cmp_result.added), [])
        self.assertFalse(LC.widening_is_acceptable(cmp_result))

    def test_mixed_add_and_remove_is_treated_as_a_removal(self):
        """E-05: additions must not buy acceptance for a simultaneous re-fencing."""
        mixed = self._rescoped("agent_workflows/demo.py, tests/test_extra.py")
        cmp_result = self._compare(mixed)
        self.assertEqual(list(cmp_result.added), ["tests/test_extra.py"])
        self.assertEqual(list(cmp_result.removed), ["tests/test_demo.py"])
        self.assertTrue(cmp_result.non_scope_identical)
        self.assertFalse(
            LC.widening_is_acceptable(cmp_result),
            "a mixed add-and-remove must refuse rather than pass on its additions",
        )

    def test_pure_reordering_is_unchanged(self):
        """E-05: `Scope-Paths` order is not semantic, so a reorder is neither add nor remove."""
        reordered = self._rescoped("tests/test_demo.py, agent_workflows/demo.py")
        cmp_result = self._compare(reordered)
        self.assertEqual(list(cmp_result.added), [])
        self.assertEqual(list(cmp_result.removed), [])
        self.assertFalse(LC.widening_is_acceptable(cmp_result))
        # And the digest itself already treated it as unchanged (it sorts before hashing).
        self.assertTrue(LC.receipt_is_current(self.receipt, reordered))


class WideningEligibilityTests(_WideningFixture):
    """E-08: an added entry that would NEUTER the fence is ineligible, however additive it looks."""

    def test_directory_and_glob_additions_are_refused_and_named(self):
        """F-11: one added entry could otherwise convert a two-file fence into a repo-wide one."""
        for entry in ("tests/", "agent_workflows", "agent_workflows/**", "*"):
            with self.subTest(entry=entry):
                cmp_result = self._compare(self._widened(entry))
                self.assertEqual(list(cmp_result.added), [entry])
                self.assertFalse(
                    cmp_result.eligible,
                    f"{entry!r} widens the fence to a tree and must be ineligible",
                )
                self.assertIn(entry, cmp_result.ineligible_reason)
                self.assertFalse(LC.widening_is_acceptable(cmp_result))

    def test_a_literal_file_path_addition_is_accepted(self):
        """The contrast case, so the rule above is a restriction and not a blanket refusal."""
        cmp_result = self._compare(self._widened("tests/test_resumedupe.py"))
        self.assertEqual(list(cmp_result.added), ["tests/test_resumedupe.py"])
        self.assertTrue(cmp_result.eligible, cmp_result.ineligible_reason)
        self.assertTrue(LC.widening_is_acceptable(cmp_result))

    def test_the_eligibility_classifier_and_scope_match_agree_on_entry_shapes(self):
        """E-08: the eligibility rule and the MATCHING rule must not disagree about a shape.

        The table is shared deliberately: eligibility exists to keep an entry that matches a TREE out
        of the widening accept, so for every shape, `eligible` must imply that `_scope_match` treats
        the entry as a single file rather than a prefix.
        """
        # (entry, a path INSIDE the tree it would admit, expected literal-file eligibility)
        table = [
            ("tests/", "tests/test_secret.py", False),
            ("tests/**", "tests/test_secret.py", False),
            ("agent_workflows/**", "agent_workflows/check_engine.py", False),
            ("*", "RELEASING.md", False),
            ("tests/test_*.py", "tests/test_secret.py", False),
            ("tests/test_resumedupe.py", "tests/test_resumedupe.py", True),
        ]
        for entry, probe, expected in table:
            with self.subTest(entry=entry):
                self.assertEqual(
                    LC.scope_entry_is_literal_file(entry),
                    expected,
                    f"{entry!r} classified wrongly",
                )
                # `_scope_match` admits the probe in every case; what differs is whether the entry
                # admits ONLY that exact path (eligible) or a whole family of them (ineligible).
                self.assertTrue(
                    LC._scope_match(probe, entry), f"{entry!r} should match {probe!r}"
                )
                if not expected:
                    # An ineligible entry admits at least one path it does not literally name.
                    self.assertNotEqual(
                        entry.strip("*/"), probe, "probe must not be the literal entry"
                    )

        # THE BARE-DIRECTORY CASE, which has no glob character yet matches by PREFIX. The pure
        # classifier cannot see the filesystem, so the directory probe is what catches it, and the two
        # together must agree with `_scope_match`.
        self.assertTrue(
            LC.scope_entry_is_literal_file("agent_workflows"),
            "the pure classifier sees no glob character here (this is why the probe exists)",
        )
        self.assertTrue(
            LC._scope_match("agent_workflows/check_engine.py", "agent_workflows"),
            "a bare directory matches by prefix, so it admits the whole tree",
        )
        self.assertTrue(LC._entry_is_bare_directory(self.root, "agent_workflows"))
        self.assertFalse(LC._entry_is_bare_directory(self.root, "tests/test_demo.py"))
        # And the combined decision refuses it (asserted above via the full comparison too).
        self.assertFalse(self._compare(self._widened("agent_workflows")).eligible)


class IneligibleReceiptShapeTests(_WideningFixture):
    """E-09: three shapes the widening accept was never reasoned about, each fail-closed."""

    def test_legacy_v1_receipt_is_not_eligible_and_is_not_even_compared(self):
        """(a) A v1 receipt is bound to the WHOLE-FILE rule.

        `receipt_is_current`'s fallback exists so a pre-Phase-2 receipt "must not be spuriously
        ACCEPTED by a rule it was never bound under". Running a v2-shaped substitution on it would be
        exactly that error, so the comparison must not attempt it at all.
        """
        legacy = dict(self.receipt)
        legacy.pop("frozen_region_digest", None)
        legacy["schema_version"] = 1

        cmp_result = LC.frozen_region_comparison(
            legacy, self._widened("tests/test_extra.py"), repo_root=self.root
        )
        self.assertFalse(cmp_result.eligible)
        self.assertIn("legacy v1", cmp_result.ineligible_reason)
        self.assertFalse(LC.widening_is_acceptable(cmp_result))
        # The substitution was NOT attempted: no scope delta was computed and nothing was proven
        # about the non-scope categories.
        self.assertEqual(list(cmp_result.added), [])
        self.assertEqual(list(cmp_result.removed), [])
        self.assertFalse(cmp_result.non_scope_identical)

    def test_a_plan_that_BECOMES_grandfathered_reads_as_a_removal(self):
        """(c) The mirror case: emptying the allowlist is a REMOVAL, not an unchanged empty set."""
        gf = self._rescoped("grandfathered")
        cmp_result = self._compare(gf)
        self.assertFalse(cmp_result.eligible)
        self.assertIn("grandfathered", cmp_result.ineligible_reason)
        self.assertEqual(
            sorted(cmp_result.removed),
            ["agent_workflows/demo.py", "tests/test_demo.py"],
            "every previously declared path must be reported as removed",
        )
        self.assertFalse(LC.widening_is_acceptable(cmp_result))

    def test_a_grandfathered_receipt_gaining_paths_is_a_changed_scope_MODEL(self):
        """(b) `_frozen_scope_paths` is [] while `requirements["scope"]` is the sentinel + prose.

        So "adding a path" here is not widening an allowlist, it is CONVERTING from no-fence to fence.
        The two scope inputs are not the same field in this shape, which is precisely why it is
        excluded rather than reasoned about.
        """
        gf_text = self._rescoped("grandfathered")
        # Confirm the shape this test depends on, rather than assuming it.
        self.assertEqual(LC._frozen_scope_paths(gf_text), [])
        self.assertEqual(
            LC._requirements_from_plan(gf_text)["scope"][0],
            "grandfathered",
            "a grandfathered plan freezes the sentinel plus its free-form Scope prose",
        )

        gf_receipt = dict(self.receipt)
        gf_receipt["scope_paths"] = []
        gf_receipt["frozen_region_digest"] = LC.frozen_region_digest(gf_text)

        cmp_result = LC.frozen_region_comparison(
            gf_receipt, self.base_text, repo_root=self.root
        )
        self.assertFalse(cmp_result.eligible)
        self.assertIn("no declared allowlist", cmp_result.ineligible_reason)
        self.assertEqual(
            sorted(cmp_result.added),
            ["agent_workflows/demo.py", "tests/test_demo.py"],
        )
        self.assertFalse(LC.widening_is_acceptable(cmp_result))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
