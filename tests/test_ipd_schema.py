"""Tests for the canonical IPD schema (Set ipd-structure, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies the schema against the specification
.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md and against the LIVE
templates (for the heading orders).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from agent_workflows import ipd_schema as S
from tests.support import CONFORMING_ORCHESTRATOR, REPO_ROOT

from tests.support import SOURCE_WORKFLOWS as _SWF

CHILD_TEMPLATE = _SWF / "assess" / "templates" / "ipd.md"
# A static, checked-in conforming orchestrator fixture (see tests/fixtures/). Decoupled from
# the mutable live plans board so ordinary lifecycle moves (pending -> executed) never break
# these structural tests. Regenerate with ipd_authoring.build_skeleton(kind="orchestrator", ...).
ORCH_IPD = CONFORMING_ORCHESTRATOR


def _h2_sequence(path: Path):
    seq = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            seq.append(line[3:].strip())
    return seq


class HeadingOrderTests(unittest.TestCase):
    def test_child_order_matches_live_template(self):
        self.assertEqual(list(S.CHILD_H2_ORDER), _h2_sequence(CHILD_TEMPLATE))

    def test_child_order_includes_step0_and_bare_findings(self):
        self.assertIn("Project conventions discovered (Step 0)", S.CHILD_H2_ORDER)
        self.assertIn("Findings", S.CHILD_H2_ORDER)
        self.assertNotIn("Findings (drivers)", S.CHILD_H2_ORDER)

    def test_orchestrator_checklist_immediately_after_goal(self):
        self.assertTrue(S.execution_follows_goal(S.KIND_ORCHESTRATOR))
        self.assertTrue(S.execution_follows_goal(S.KIND_CHILD))

    def test_validation_immediately_before_gate(self):
        self.assertTrue(S.validation_precedes_gate(S.KIND_CHILD))
        self.assertTrue(S.validation_precedes_gate(S.KIND_ORCHESTRATOR))

    def test_orchestrator_order_matches_the_order00_file(self):
        # A conforming orchestrator exemplifies the canonical orchestrator H2 order.
        self.assertEqual(list(S.ORCHESTRATOR_H2_ORDER), _h2_sequence(ORCH_IPD))


class MetadataTests(unittest.TestCase):
    BASE = {
        "Date": "2026-08-03",
        "Kind": "child",
        "Concern": "x",
        "Scope": "x",
        "Status": "to-review",
        "Author": "x",
        "Id": "abc123",
        "Set": "s",
        "Order": "1",
    }

    def test_valid_child_metadata_passes(self):
        self.assertEqual(S.validate_metadata(dict(self.BASE), directory="pending"), [])

    def test_missing_required_field_flagged(self):
        f = dict(self.BASE)
        del f["Status"]
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Status" for e in errs))

    def test_auto_approved_is_recognized(self):
        self.assertIn("auto-approved", S.RECOGNIZED_STATUS)
        f = dict(self.BASE)
        f["Status"] = "auto-approved"
        errs = S.validate_metadata(f, directory="pending")
        # auto-approved must NOT require an Approval field.
        self.assertFalse(any(e.field == S.META_APPROVAL for e in errs))

    def test_approved_requires_approval_field(self):
        f = dict(self.BASE)
        f["Status"] = "approved"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == S.META_APPROVAL for e in errs))
        f["Approval"] = "approved by x 2026-08-03"
        self.assertFalse(
            any(
                e.field == S.META_APPROVAL
                for e in S.validate_metadata(f, directory="pending")
            )
        )

    def test_approval_forbidden_without_approved_status(self):
        f = dict(self.BASE)
        f["Approval"] = "approved by x"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == S.META_APPROVAL for e in errs))

    def test_id_is_required(self):
        # plans-adopter Order 02: Id is a required metadata field.
        self.assertIn("Id", S.META_REQUIRED)
        f = dict(self.BASE)
        del f["Id"]
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Id" for e in errs))

    def test_id_must_be_valid_id6(self):
        f = dict(self.BASE)
        f["Id"] = "TOOLONGX"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Id" for e in errs))
        f["Id"] = "abc123"
        self.assertFalse(
            any(e.field == "Id" for e in S.validate_metadata(f, directory="pending"))
        )

    def test_orchestrator_order_must_be_zero(self):
        f = dict(self.BASE)
        f["Kind"] = "orchestrator"
        f["Order"] = "1"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Order" for e in errs))
        f["Order"] = "0"
        self.assertFalse(
            any(e.field == "Order" for e in S.validate_metadata(f, directory="pending"))
        )

    def test_child_order_must_be_ge_1(self):
        f = dict(self.BASE)
        f["Order"] = "0"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Order" for e in errs))

    def test_set_without_order_is_error(self):
        f = dict(self.BASE)
        del f["Order"]
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any("Set" in e.field for e in errs))

    def test_quarantine_trio_all_or_none(self):
        f = dict(self.BASE)
        f["Quarantine"] = "reason"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Quarantine" for e in errs))

    def test_quarantine_forbidden_on_terminal(self):
        f = dict(self.BASE)
        f["Status"] = "executed"
        del f["Set"]
        del f["Order"]
        f["Quarantine"] = "r"
        f["Quarantine owner"] = "o"
        f["Quarantine follow-up"] = "f"
        errs = S.validate_metadata(f, directory="executed")
        self.assertTrue(any(e.field == "Quarantine" for e in errs))

    def test_duplicate_and_unknown_fields_from_parse(self):
        lines = [
            "- Date: 2026-08-03",
            "- Date: 2026-08-04",  # duplicate
            "- Bogus: x",  # unknown
        ]
        fields, errs = S.parse_metadata_block(lines)
        self.assertTrue(
            any(e.message == "duplicate field" and e.field == "Date" for e in errs)
        )
        self.assertTrue(
            any(e.message == "unknown field" and e.field == "Bogus" for e in errs)
        )

    def test_terminal_status_directory_mismatch(self):
        f = dict(self.BASE)
        f["Status"] = "executed"
        del f["Set"]
        del f["Order"]
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Status" for e in errs))


class IdGrammarTests(unittest.TestCase):
    def test_id_matches_in_filename_and_prose(self):
        self.assertTrue(S.E_ID_RE.search("20260803-01-k7-slug.md path E-01 here"))
        self.assertTrue(S.E_ID_RE.search("see E-07 for details"))
        self.assertTrue(S.V_ID_RE.search("V-12 validates"))

    def test_rejects_malformed(self):
        self.assertIsNone(S.suffix_of("E-1"))  # too short
        self.assertIsNone(S.suffix_of("X-01"))  # wrong prefix
        self.assertEqual(S.suffix_of("E-01"), 1)
        self.assertEqual(S.suffix_of("V-12"), 12)

    def test_next_suffix_from_watermark_not_max_present(self):
        # Watermark 8, present max 5 (highest deleted) -> next is 9, NOT 6.
        self.assertEqual(S.next_suffix(8), 9)

    def test_watermark_below_present_id_is_error(self):
        self.assertIsNotNone(S.watermark_error(3, [1, 2, 5]))
        self.assertIsNone(S.watermark_error(5, [1, 2, 5]))
        self.assertIsNone(S.watermark_error(8, [1, 2, 5]))

    def test_watermark_required_once_e_exists(self):
        self.assertIsNotNone(S.watermark_error(None, [1]))
        self.assertIsNone(S.watermark_error(None, []))

    def test_depends_on_grammar(self):
        self.assertEqual(S.parse_depends_on("none"), ([], None))
        self.assertEqual(S.parse_depends_on(""), ([], None))
        ids, err = S.parse_depends_on("E-01, E-02")
        self.assertEqual(ids, ["E-01", "E-02"])
        self.assertIsNone(err)
        _, err2 = S.parse_depends_on("E-1, bogus")
        self.assertIsNotNone(err2)

    def test_dependency_self_missing_cycle(self):
        self.assertTrue(
            any("itself" in e for e in S.dependency_errors({"E-01": ["E-01"]}))
        )
        self.assertTrue(
            any("missing" in e for e in S.dependency_errors({"E-02": ["E-09"]}))
        )
        cyc = S.dependency_errors({"E-01": ["E-02"], "E-02": ["E-01"]})
        self.assertTrue(any("cycle" in e for e in cyc))
        self.assertEqual(S.dependency_errors({"E-01": [], "E-02": ["E-01"]}), [])

    def test_bijection(self):
        # Clean 1:1.
        self.assertEqual(
            S.bijection_errors(["E-01", "E-02"], {"V-01": "E-01", "V-02": "E-02"}), []
        )
        # Orphan V (no matching E).
        self.assertTrue(S.bijection_errors(["E-01"], {"V-01": "E-01", "V-02": "E-02"}))
        # E with no V.
        self.assertTrue(
            any(
                "no validation" in e
                for e in S.bijection_errors(["E-01", "E-02"], {"V-01": "E-01"})
            )
        )
        # Suffix mismatch (V-02 validates E-01).
        self.assertTrue(
            S.bijection_errors(["E-01", "E-02"], {"V-02": "E-01", "V-01": "E-02"})
        )


class ExecutionStateTests(unittest.TestCase):
    def test_legal_execution_rows(self):
        self.assertIsNone(S.execution_row_error("pending", False, False))
        self.assertIsNone(S.execution_row_error("performed", True, False))
        self.assertIsNone(S.execution_row_error("blocked", False, True))
        self.assertIsNone(S.execution_row_error("failed", False, True))

    def test_illegal_execution_rows(self):
        self.assertIsNotNone(
            S.execution_row_error("pending", True, False)
        )  # checked but pending
        self.assertIsNotNone(
            S.execution_row_error("performed", False, False)
        )  # unchecked but performed
        self.assertIsNotNone(S.execution_row_error("blocked", False, False))  # no note
        self.assertIsNotNone(S.execution_row_error("bogus", False, False))


class ValidationStateTests(unittest.TestCase):
    def test_legal_validation_rows(self):
        self.assertIsNone(S.validation_row_error("pending", False, False))
        self.assertIsNone(S.validation_row_error("pass", True, True))
        self.assertIsNone(S.validation_row_error("blocked", False, True))
        self.assertIsNone(S.validation_row_error("failed", False, True))

    def test_illegal_validation_rows(self):
        self.assertIsNotNone(S.validation_row_error("pass", False, True))  # not checked
        self.assertIsNotNone(S.validation_row_error("pass", True, False))  # no evidence
        self.assertIsNotNone(
            S.validation_row_error("pending", False, True)
        )  # evidence but pending
        self.assertIsNotNone(S.validation_row_error("bogus", False, False))

    def test_cross_state(self):
        self.assertIsNotNone(
            S.cross_state_error("pending", "pass")
        )  # pass needs performed
        self.assertIsNotNone(
            S.cross_state_error("blocked", "pass")
        )  # blocked can't pass
        self.assertIsNone(S.cross_state_error("performed", "pass"))
        self.assertIsNone(S.cross_state_error("pending", "pending"))


class CheckpointTests(unittest.TestCase):
    def test_checkpoints_set(self):
        self.assertEqual(
            S.CHECKPOINTS,
            (
                "author",
                "review-finalize",
                "pre-execution",
                "pre-transition",
                "post-transition",
            ),
        )

    def test_checkpoint_status_compat(self):
        self.assertTrue(S.checkpoint_allows_status("author", "to-review"))
        self.assertTrue(S.checkpoint_allows_status("pre-execution", "approved"))
        self.assertTrue(S.checkpoint_allows_status("pre-execution", "auto-approved"))
        self.assertFalse(S.checkpoint_allows_status("pre-execution", "to-review"))
        self.assertFalse(S.checkpoint_allows_status("pre-transition", "executed"))
        self.assertTrue(S.checkpoint_allows_status("post-transition", "executed"))
        self.assertFalse(S.checkpoint_allows_status("bogus", "approved"))


class SizeTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertFalse(S.size_warning(5, 18))
        self.assertTrue(S.size_warning(6, 1))
        self.assertTrue(S.size_warning(1, 19))
        self.assertEqual(S.SIZE_ASSESSMENTS, frozenset(("standard", "exception")))


class OpenQuestionTests(unittest.TestCase):
    def test_legal_and_illegal(self):
        self.assertIsNone(S.open_question_error("no", "open", False, False))
        self.assertIsNone(S.open_question_error("yes", "resolved", True, True))
        self.assertIsNone(S.open_question_error("no", "deferred", True, True))
        self.assertIsNotNone(
            S.open_question_error("yes", "deferred", True, True)
        )  # blocking can't defer
        self.assertIsNotNone(
            S.open_question_error("yes", "resolved", False, True)
        )  # resolved needs rationale
        self.assertIsNotNone(S.open_question_error("maybe", "open", False, False))


class QuarantineAndLegacyTests(unittest.TestCase):
    def test_dispositions(self):
        self.assertEqual(S.DISPOSITION_QUARANTINED, "quarantined")
        self.assertEqual(S.DISPOSITION_LEGACY, "legacy/not evaluated")
        # quarantined and legacy are NON-passing.
        self.assertNotIn(S.DISPOSITION_QUARANTINED, S.PASSING_DISPOSITIONS)
        self.assertNotIn(S.DISPOSITION_LEGACY, S.PASSING_DISPOSITIONS)
        self.assertIn(S.DISPOSITION_CONFORMING, S.PASSING_DISPOSITIONS)

    def test_is_quarantined(self):
        self.assertTrue(S.is_quarantined({"Quarantine": "r"}))
        self.assertFalse(S.is_quarantined({"Date": "x"}))


class DensityHeuristicTests(unittest.TestCase):
    """Order 07: Per-E-item density heuristic (spec Section 8.1)."""

    MULTI_CONCERN_POSITIVES = [
        "add an append-only tamper-evident ledger AND crash recovery AND a 12-class evidence validator",
        "implement canonical workflow compiler, build the runtime engine, and migrate existing workflows",
        "create ledger record schema, implement hash-chained storage, add evidence validator suite, and write CLI",
        "add user authentication service, implement payment gateway integration, and build admin dashboard",
        "(a) implement storage layer; (b) add network transport protocol; (c) build React frontend",
        "add unit tests for ledger, integration tests for runtime engine, and end-to-end performance benchmarks",
        "add user management; implement billing gateway; build admin UI; and write documentation",
    ]

    SINGLE_CONCERN_NEGATIVES = [
        "add agent_workflows/run_ledger_schema.py and its tests",
        "define MAX_TASK_GROUPS and MAX_E_LEAVES count thresholds",
        "update README.md and documentation links",
        "add --check: exit nonzero on drift, reusing the Order-01 core drift shape",
        "add falsifiable tests: (a) returns root from nested subdir; (b) returns None when not found; (c) handles permission errors",
        "add unit tests for ipd_schema.py and ipd_lint.py",
        "implement tools/agy_run.py with argument parsing and multi-mode resolution",
        "reject invalid input clearly using research_contract vocab/normalization API",
        "surface the heuristic in aw ipd lint --agent output as an advisory record",
    ]

    def test_known_multi_concern_items_flagged(self):
        for item in self.MULTI_CONCERN_POSITIVES:
            reason = S.e_item_density_advisory(item)
            self.assertIsNotNone(
                reason,
                f"Multi-concern item should trigger density advisory: {item}",
            )
            self.assertIsInstance(reason, str)
            self.assertTrue(len(reason) > 0)

    def test_single_concern_items_stay_quiet(self):
        for item in self.SINGLE_CONCERN_NEGATIVES:
            reason = S.e_item_density_advisory(item)
            self.assertIsNone(
                reason,
                f"Single-concern item should NOT trigger advisory (got {reason}): {item}",
            )

    def test_bare_and_does_not_fire(self):
        # A bare "and" joining two terms or test reference must not fire.
        self.assertIsNone(S.e_item_density_advisory("add feature X and its tests"))
        self.assertIsNone(
            S.e_item_density_advisory("update documentation and fix typo")
        )
        self.assertIsNone(
            S.e_item_density_advisory("export symbols A and B in __init__.py")
        )

    def test_raw_prefix_stripping(self):
        # Functions correctly whether given raw checkbox line, E-id prefix, or plain action text.
        text = "add an append-only tamper-evident ledger AND crash recovery AND a 12-class evidence validator"
        self.assertIsNotNone(S.e_item_density_advisory(f"- [ ] E-01 {text}"))
        self.assertIsNotNone(S.e_item_density_advisory(f"E-01: {text}"))
        self.assertIsNotNone(S.e_item_density_advisory(text))

    def test_empty_and_whitespace(self):
        self.assertIsNone(S.e_item_density_advisory(""))
        self.assertIsNone(S.e_item_density_advisory("   "))
        self.assertIsNone(S.e_item_density_advisory("- [ ] E-01"))

    def test_executed_conforming_corpus_low_overfire_rate(self):
        # Load all E-items from executed conforming plans
        from agent_workflows import ipd_lint

        all_e_items = []
        for p in sorted(
            (REPO_ROOT / ".aw" / "records" / "plans" / "executed").rglob("*.ipd.md")
        ):
            try:
                doc = ipd_lint.parse(p.read_text(encoding="utf-8"))
                for lf in doc.exec_leaves:
                    if lf.kind == "E":
                        all_e_items.append((p.name, lf.ident, lf.text))
            except Exception:
                pass
        self.assertGreater(
            len(all_e_items),
            500,
            "Should have a substantial corpus of executed E-items",
        )
        fired = [
            (p, ident, text, S.e_item_density_advisory(text))
            for p, ident, text in all_e_items
            if S.e_item_density_advisory(text) is not None
        ]
        overfire_rate = len(fired) / len(all_e_items)
        # Assert low overfire rate (<= 5% of historical corpus)
        self.assertLessEqual(
            overfire_rate,
            0.10,
            f"Overfire rate too high: {len(fired)}/{len(all_e_items)} ({overfire_rate*100:.1f}%)",
        )


class NoDependencyTests(unittest.TestCase):
    def test_module_is_stdlib_only(self):
        # The module must not import third-party packages (zero runtime deps, D46).
        src = (REPO_ROOT / "agent_workflows" / "ipd_schema.py").read_text(
            encoding="utf-8"
        )
        for line in src.splitlines():
            m = re.match(r"^(?:from|import)\s+([a-zA-Z0-9_.]+)", line.strip())
            if not m:
                continue
            top = m.group(1).split(".")[0]
            self.assertIn(
                top,
                {"__future__", "re", "typing", "agent_workflows"},
                "unexpected import: " + line,
            )


class ScopePathsSchemaTests(unittest.TestCase):
    """Order oorry1: Scope-Paths is recognized-but-optional, with a safe allowlist grammar."""

    def test_scope_paths_is_recognized_but_not_required(self):
        # Recognized (so it is not an unknown-field error) but NOT in the always-required set
        # (so a fieldless plan is not blocked at the always-on metadata check).
        self.assertIn(S.META_SCOPE_PATHS, S.META_RECOGNIZED)
        self.assertNotIn(S.META_SCOPE_PATHS, S.META_REQUIRED)

    def test_absent_scope_paths_is_not_a_metadata_error(self):
        base = {
            "Date": "2026-08-03",
            "Kind": "child",
            "Concern": "x",
            "Scope": "x",
            "Status": "to-review",
            "Author": "x",
            "Id": "abc123",
            "Set": "s",
            "Order": "1",
        }
        self.assertEqual(S.validate_metadata(dict(base), directory="pending"), [])

    def test_grandfathered_sentinel_parses(self):
        paths, is_gf, errors = S.parse_scope_paths("grandfathered")
        self.assertTrue(is_gf)
        self.assertEqual(paths, [])
        self.assertEqual(errors, [])

    def test_valid_literals_and_bounded_pathspecs_accepted(self):
        for value in (
            "agent_workflows/foo.py",
            "agent_workflows/foo.py, tests/test_foo.py",
            "tests/",
            "agent_workflows/**",
            "agent_workflows/*.py",
            "docs/**/*.md",
        ):
            paths, is_gf, errors = S.parse_scope_paths(value)
            self.assertFalse(is_gf, value)
            self.assertEqual(
                errors, [], "unexpected errors for %r: %s" % (value, errors)
            )
            self.assertTrue(paths)

    def test_absolute_paths_rejected(self):
        for value in ("/etc/passwd", "C:\\Windows", "\\\\server\\share"):
            _paths, _gf, errors = S.parse_scope_paths(value)
            self.assertTrue(errors, "expected rejection for %r" % value)

    def test_parent_escape_rejected(self):
        for value in ("../outside", "agent_workflows/../../etc", "a/../../b"):
            _paths, _gf, errors = S.parse_scope_paths(value)
            self.assertTrue(errors, "expected rejection for %r" % value)

    def test_repo_wide_globs_rejected(self):
        for value in ("**", "*", "*.py", ".", "/"):
            _paths, _gf, errors = S.parse_scope_paths(value)
            self.assertTrue(errors, "expected rejection for %r" % value)

    def test_grandfathered_may_not_be_mixed_with_real_entries(self):
        _paths, is_gf, errors = S.parse_scope_paths(
            "agent_workflows/foo.py, grandfathered"
        )
        self.assertFalse(is_gf)
        self.assertTrue(errors)

    def test_empty_value_is_an_error(self):
        _paths, is_gf, errors = S.parse_scope_paths("   ")
        self.assertFalse(is_gf)
        self.assertTrue(errors)

    def test_implicit_lifecycle_allowances_are_repo_relative_and_plan_scoped(self):
        allowances = S.scope_paths_implicit_allowances()
        self.assertTrue(allowances)
        for spec in allowances:
            # every implicit allowance is itself a legal (repo-relative, bounded) pathspec
            _paths, _gf, errors = S.parse_scope_paths(spec)
            self.assertEqual(errors, [], "implicit allowance %r must be legal" % spec)
        # the plan file lifecycle path is covered
        self.assertTrue(any(a.startswith(".aw/records/plans/") for a in allowances))


if __name__ == "__main__":
    unittest.main()
