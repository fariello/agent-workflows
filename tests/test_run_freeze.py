"""Tests for agent_workflows.run_freeze (awoptimize Order 02 E-06, validates E-04..E-05).

Covers: freeze determinism (same input -> same ids + digests); the frozen requirement_set binds every
MUST/scope/validation/output id; a malformed requirement is refused before a set is emitted; a semantic
edit yields a new requirement_revision and invalidates evidence bound to the prior digest; a cosmetic
edit is a digest no-op; and a drop/redefine after approval is refused.
"""

import unittest

from agent_workflows import run_freeze as F
from agent_workflows import run_ledger_schema as S


def _reqs(must_last="tests pass"):
    return {
        "must": ["ship the CLI", must_last],
        "scope": ["only edit engine.py"],
        "validation": ["run make test"],
        "output": ["a wheel in dist/"],
    }


class FreezeDeterminismTest(unittest.TestCase):
    def test_same_input_same_ids_and_digests(self):
        a = F.freeze_requirements(_reqs())
        b = F.freeze_requirements(_reqs())
        self.assertEqual(a.requirement_digest, b.requirement_digest)
        self.assertEqual([i.id for i in a.items], [i.id for i in b.items])
        self.assertEqual([i.digest for i in a.items], [i.digest for i in b.items])

    def test_dict_order_does_not_change_set_digest(self):
        r1 = {"must": ["x"], "scope": ["y"]}
        r2 = {"scope": ["y"], "must": ["x"]}
        self.assertEqual(
            F.freeze_requirements(r1).requirement_digest,
            F.freeze_requirements(r2).requirement_digest,
        )

    def test_binds_every_category_id(self):
        frozen = F.freeze_requirements(_reqs())
        ids = {i.id for i in frozen.items}
        self.assertIn("M-01", ids)
        self.assertIn("M-02", ids)
        self.assertIn("SC-01", ids)
        self.assertIn("V-01", ids)
        self.assertIn("O-01", ids)


class MalformedInputTest(unittest.TestCase):
    def test_non_mapping_refused(self):
        with self.assertRaises(ValueError):
            F.freeze_requirements(["not", "a", "mapping"])  # type: ignore[arg-type]

    def test_empty_item_refused_before_set_emitted(self):
        with self.assertRaises(ValueError) as ctx:
            F.freeze_requirements({"must": ["ok", "   "]})
        self.assertIn("RF-E006", str(ctx.exception))

    def test_non_string_item_refused(self):
        with self.assertRaises(ValueError) as ctx:
            F.freeze_requirements({"must": [123]})  # type: ignore[list-item]
        self.assertIn("RF-E005", str(ctx.exception))


class RequirementSetRecordTest(unittest.TestCase):
    def test_record_is_schema_valid_and_binds_scope(self):
        frozen = F.freeze_requirements(_reqs())
        rec = F.requirement_set_record(
            run_id="run-deadbeef",
            seq=1,
            actor="coordinator",
            timestamp="2026-08-22T00:00:00Z",
            parent="",
            frozen=frozen,
        )
        res = S.validate_record(rec)
        self.assertTrue(res.ok, msg=str(res.findings))
        self.assertEqual(rec["requirement_digest"], frozen.requirement_digest)
        self.assertIn("SC-01", rec["scope_fence"])


class RevisionTest(unittest.TestCase):
    def test_cosmetic_edit_is_a_digest_noop(self):
        base = F.freeze_requirements(_reqs("tests pass"))
        cosmetic = F.freeze_requirements(_reqs("  tests   pass  "))  # whitespace only
        self.assertEqual(base.requirement_digest, cosmetic.requirement_digest)
        self.assertEqual(F.diff_requirements(base, cosmetic), ())

    def test_semantic_edit_yields_revision_and_invalidates_evidence(self):
        base = F.freeze_requirements(_reqs("tests pass"))
        changed = F.freeze_requirements(
            _reqs("tests may be skipped")
        )  # meaning changed
        # M-02 is the changed item; bind some evidence to its prior digest.
        prior_m2 = next(i for i in base.items if i.id == "M-02")
        evidence = {prior_m2.digest: ["ev-001", "ev-002"]}
        revs = F.diff_requirements(base, changed, evidence_by_digest=evidence)
        self.assertEqual(len(revs), 1)
        self.assertEqual(revs[0].id, "M-02")
        self.assertEqual(revs[0].invalidated_evidence, ("ev-001", "ev-002"))
        self.assertNotEqual(revs[0].prev_digest, revs[0].new_digest)

    def test_drop_after_approval_refused(self):
        base = F.freeze_requirements(_reqs())
        dropped = F.freeze_requirements(
            {
                "must": ["ship the CLI"],
                "scope": ["only edit engine.py"],
                "validation": ["run make test"],
                "output": ["a wheel in dist/"],
            }
        )  # M-02 removed
        res = F.refuse_drop_or_redefine(base, dropped)
        self.assertFalse(res.ok)
        self.assertIn("RF-E010", {f.code for f in res.findings})

    def test_redefine_after_approval_refused(self):
        base = F.freeze_requirements(_reqs("tests pass"))
        redefined = F.freeze_requirements(_reqs("tests may be skipped"))
        res = F.refuse_drop_or_redefine(base, redefined)
        self.assertFalse(res.ok)
        self.assertIn("RF-E011", {f.code for f in res.findings})

    def test_addition_after_approval_allowed(self):
        base = F.freeze_requirements({"must": ["a"]})
        added = F.freeze_requirements({"must": ["a", "b"]})
        res = F.refuse_drop_or_redefine(base, added)
        self.assertTrue(res.ok, msg=str(res.findings))


if __name__ == "__main__":
    unittest.main()
