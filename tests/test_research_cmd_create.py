"""Tests for the aw research create verbs (Set research-org, Order 02).

Stdlib unittest, throwaway dirs (mirrors tests/test_installer.py style). Verifies name assembly,
NN increment, singleton derivation, full spec-5.8 frontmatter, writing-command safety
(dry-run/apply/atomic/no-clobber), the multi-model comparison scaffold order, and invalid-input
rejection via the contract's suggestion API.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import research_cmd as C
from agent_workflows import research_contract as R


class NewPlanTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.research = self.root / R.RESEARCH_ROOT
        self.research.mkdir(parents=True)

    def test_new_well_formed_and_full_frontmatter(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="research-report",
            slug="Delivery Notes",
            summary="A summary.",
            set_id="aw-delivery",
            model="gpt-56",  # normalizes to gpt56
            topic=["delivery", "hosts"],
            date_str="20260726",
        )
        self.assertIsNone(err)
        self.assertEqual(len(files), 1)
        f = files[0]
        # Name parses back and is contract-conformant.
        parsed, perr = R.parse_name(f.path.name)
        self.assertIsNone(perr)
        self.assertEqual(parsed.set_id, "aw-delivery")
        self.assertEqual(parsed.slug, "delivery-notes")
        self.assertEqual(parsed.model, "gpt56")
        self.assertEqual(parsed.kind, "research-report")
        # Frontmatter is full and passes the validator.
        data = _parse_frontmatter(f.content)
        self.assertEqual(R.validate_frontmatter(data), [])
        self.assertEqual(
            data["status"], "todo"
        )  # rstodo p3o9je: created docs are born `todo`
        self.assertEqual(data["outcome"], "none-yet")

    def test_nn_increments_on_second_same_set_call(self):
        f1, _ = C.plan_new(
            research_root=self.research,
            kind="notes",
            slug="one",
            summary="s",
            set_id="myset",
            date_str="20260726",
        )
        # Write it so the second call sees it on disk.
        f1[0].path.write_text(f1[0].content, encoding="utf-8")
        f2, _ = C.plan_new(
            research_root=self.research,
            kind="notes",
            slug="two",
            summary="s",
            set_id="myset",
            date_str="20260726",
        )
        p1, _ = R.parse_name(f1[0].path.name)
        p2, _ = R.parse_name(f2[0].path.name)
        self.assertEqual(p1.order, "01")
        self.assertEqual(p2.order, "02")
        # Same set shares the date.
        self.assertEqual(p1.date, p2.date)

    def test_singleton_derives_set_from_slug(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="advisory",
            slug="my-finding",
            summary="s",
            date_str="20260726",
        )
        self.assertIsNone(err)
        parsed, _ = R.parse_name(files[0].path.name)
        self.assertEqual(parsed.set_id, "my-finding")
        self.assertEqual(parsed.order, "01")

    def test_unknown_kind_rejected_with_suggestion(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="reserch-reprt",
            slug="x",
            summary="s",
        )
        self.assertIsNone(files)
        self.assertIsNotNone(err)
        self.assertIn("unknown kind", err)


class WriteSafetyTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.research = self.root / R.RESEARCH_ROOT
        self.research.mkdir(parents=True)

    def _files(self):
        files, err = C.plan_new(
            research_root=self.research,
            kind="notes",
            slug="x",
            summary="s",
            set_id="s",
            date_str="20260726",
        )
        self.assertIsNone(err)
        return files

    def test_dry_run_writes_nothing(self):
        files = self._files()
        rc = C._emit_and_write(files, apply=False, overwrite=False)
        self.assertEqual(rc, 0)
        self.assertFalse(files[0].path.exists())

    def test_apply_writes_atomically(self):
        files = self._files()
        rc = C._emit_and_write(files, apply=True, overwrite=False)
        self.assertEqual(rc, 0)
        self.assertTrue(files[0].path.exists())
        # No temp file left behind.
        leftovers = list(self.research.glob(".research-tmp-*"))
        self.assertEqual(leftovers, [])

    def test_no_clobber_without_overwrite(self):
        files = self._files()
        files[0].path.write_text("existing", encoding="utf-8")
        rc = C._emit_and_write(files, apply=True, overwrite=False)
        self.assertEqual(rc, 1)
        self.assertEqual(files[0].path.read_text(encoding="utf-8"), "existing")


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.research = self.root / R.RESEARCH_ROOT
        self.research.mkdir(parents=True)

    def test_scaffold_order_and_tags(self):
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="host-probe",
            slug="probe",
            models=["gpt56", "sonnet5", "gemini31pro"],
            date_str="20260726",
        )
        self.assertIsNone(err)
        # 00 prompt + 3 models (01..03) + reconciliation (04) = 5
        self.assertEqual(len(files), 5)
        parsed = [R.parse_name(f.path.name)[0] for f in files]
        orders = [p.order for p in parsed]
        self.assertEqual(orders, ["00", "01", "02", "03", "04"])
        self.assertEqual(parsed[0].kind, "research-prompt")
        self.assertIsNone(parsed[0].model)
        self.assertEqual(parsed[1].model, "gpt56")
        self.assertEqual(parsed[4].kind, "reconciliation-report")
        self.assertEqual(parsed[4].model, "reconciliation")

    def test_unknown_model_accepted_and_malformed_rejected(self):
        # Unknown well-formed model is accepted and recorded verbatim
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="s",
            slug="x",
            models=["llama99"],
        )
        self.assertIsNone(err)
        self.assertIsNotNone(files)
        self.assertEqual(len(files), 3)
        parsed = [R.parse_name(f.path.name)[0] for f in files]
        self.assertEqual(parsed[1].model, "llama99")

        # Malformed model syntax (e.g. whitespace or dot) is still refused
        files_bad, err_bad = C.plan_new_comparison(
            research_root=self.research,
            set_id="s",
            slug="x",
            models=["llama 99"],
        )
        self.assertIsNone(files_bad)
        self.assertIn("malformed", err_bad)

    def test_comparison_scaffold_prompt_has_no_status_and_reports_are_todo(self):
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="probe-set",
            slug="probe",
            models=["gpt56", "sonnet5"],
            date_str="20260726",
        )
        self.assertIsNone(err)
        self.assertEqual(len(files), 4)
        prompt_content = files[0].content
        self.assertNotIn("status:", prompt_content)
        parsed_prompt = _parse_frontmatter(prompt_content)
        self.assertNotIn("status", parsed_prompt)
        self.assertEqual(R.validate_frontmatter(parsed_prompt), [])

        for f in files[1:]:
            self.assertIn("status: todo", f.content)
            parsed_doc = _parse_frontmatter(f.content)
            self.assertEqual(parsed_doc.get("status"), "todo")
            self.assertEqual(R.validate_frontmatter(parsed_doc), [])

    def test_comparison_summary_reaches_all_planned_documents(self):
        user_summary = "Which widget library should we adopt"
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="widget-set",
            slug="widget-study",
            models=["gpt56", "sonnet5"],
            summary=user_summary,
        )
        self.assertIsNone(err)
        self.assertEqual(len(files), 4)

        role_tokens = [
            "Originating prompt for the comparison set",
            "gpt56 report",
            "sonnet5 report",
            "Synthesis of the model reports",
        ]
        for f, token in zip(files, role_tokens):
            parsed = _parse_frontmatter(f.content)
            summary_val = parsed.get("summary", "")
            self.assertIn(user_summary, summary_val)
            self.assertIn(token, summary_val)
            self.assertEqual(R.validate_frontmatter(parsed), [])

    def test_compose_comparison_summary_unit(self):
        # Empty and whitespace-only return role unchanged
        self.assertEqual(
            C._compose_comparison_summary("", "gpt56 report."), "gpt56 report."
        )
        self.assertEqual(
            C._compose_comparison_summary("   ", "gpt56 report."), "gpt56 report."
        )

        # Normal input composes user and role without trailing dot
        self.assertEqual(
            C._compose_comparison_summary("Which widget library", "gpt56 report."),
            "Which widget library (gpt56 report)",
        )
        self.assertEqual(
            C._compose_comparison_summary(
                "Which widget library", "Originating prompt for the comparison set."
            ),
            "Which widget library (Originating prompt for the comparison set)",
        )
        self.assertEqual(
            C._compose_comparison_summary(
                "Which widget library", "Synthesis of the model reports."
            ),
            "Which widget library (Synthesis of the model reports)",
        )

        # Over-bound case derived from A.MAX_DESCRIPTIVE_LEN arithmetic
        long_user = "u" * (A.MAX_DESCRIPTIVE_LEN - 10)
        res = C._compose_comparison_summary(
            long_user, "Originating prompt for the comparison set."
        )
        self.assertEqual(res, long_user)

        # A.is_safe_descriptive holds on every return
        for user, role in [
            ("", "gpt56 report."),
            ("  ", "gpt56 report."),
            ("Which widget library", "gpt56 report."),
            ("Which widget library", "Originating prompt for the comparison set."),
            ("Which widget library", "Synthesis of the model reports."),
            (long_user, "Originating prompt for the comparison set."),
        ]:
            out = C._compose_comparison_summary(user, role)
            self.assertTrue(A.is_safe_descriptive(out))

    def test_comparison_no_summary_exact_strings(self):
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="no-summary-set",
            slug="no-sum",
            models=["gpt56", "sonnet5"],
        )
        self.assertIsNone(err)
        self.assertEqual(len(files), 4)
        parsed = [_parse_frontmatter(f.content) for f in files]
        self.assertEqual(
            parsed[0].get("summary"), "Originating prompt for the comparison set."
        )
        self.assertEqual(parsed[1].get("summary"), "gpt56 report.")
        self.assertEqual(parsed[2].get("summary"), "sonnet5 report.")
        self.assertEqual(parsed[3].get("summary"), "Synthesis of the model reports.")

    def test_comparison_invariants_under_non_empty_summary(self):
        files, err = C.plan_new_comparison(
            research_root=self.research,
            set_id="inv-set",
            slug="inv",
            models=["gpt56", "sonnet5"],
            summary="A non-empty user summary",
        )
        self.assertIsNone(err)
        self.assertEqual(len(files), 4)

        parsed_names = [R.parse_name(f.path.name)[0] for f in files]
        orders = [p.order for p in parsed_names]
        self.assertEqual(orders, ["00", "01", "02", "03"])

        self.assertEqual(parsed_names[0].kind, "research-prompt")
        self.assertIsNone(parsed_names[0].model)
        self.assertEqual(parsed_names[1].kind, "research-report")
        self.assertEqual(parsed_names[1].model, "gpt56")
        self.assertEqual(parsed_names[2].kind, "research-report")
        self.assertEqual(parsed_names[2].model, "sonnet5")
        self.assertEqual(parsed_names[3].kind, "reconciliation-report")
        self.assertEqual(parsed_names[3].model, "reconciliation")

        prompt_content = files[0].content
        self.assertNotIn("status:", prompt_content)
        parsed_prompt = _parse_frontmatter(prompt_content)
        self.assertNotIn("status", parsed_prompt)
        self.assertEqual(R.validate_frontmatter(parsed_prompt), [])

        for f in files[1:]:
            self.assertIn("status: todo", f.content)
            parsed_doc = _parse_frontmatter(f.content)
            self.assertEqual(parsed_doc.get("status"), "todo")
            self.assertEqual(R.validate_frontmatter(parsed_doc), [])


class IdCollisionTests(unittest.TestCase):
    def test_generate_avoids_existing(self):
        # Force a collision on the first draw, then succeed.
        seq = iter(["a", "a", "a", "a", "a", "a", "b", "c", "d", "e", "f", "g"])
        existing = {"aaaaaa"}
        got = C.generate_id6(existing, _rng=lambda alphabet: next(seq))
        self.assertNotIn(got, existing)
        self.assertTrue(R.is_valid_id6(got))


def _parse_frontmatter(text: str) -> dict:
    """Minimal frontmatter parser for the tool-authored block (list + scalar values)."""

    data: dict = {}
    lines = text.splitlines()
    assert lines[0] == "---"
    for line in lines[1:]:
        if line == "---":
            break
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [x.strip() for x in inner.split(",")] if inner else []
        else:
            data[key] = val
    return data


class SetOutcomeTests(unittest.TestCase):
    """IPD xjrdjp E-01: aw research set-outcome + the in-place frontmatter field updater."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.research = self.root / R.RESEARCH_ROOT
        self.research.mkdir(parents=True)
        files, err = C.plan_new(
            research_root=self.research,
            kind="research-report",
            slug="notes",
            summary="A summary.",
            set_id="aw-delivery",
            model=None,
            topic=["delivery"],
            date_str="20260726",
        )
        assert err is None
        self.doc = files[0].path
        self.doc.write_text(files[0].content, encoding="utf-8")
        # Append a body that intentionally contains a `status:`-like line to prove the updater
        # only touches the FIRST frontmatter block.
        self.doc.write_text(
            self.doc.read_text(encoding="utf-8") + "Body.\noutcome: not-frontmatter\n",
            encoding="utf-8",
        )
        self.id6 = R.parse_name(self.doc.name)[0].id6

    def test_updater_round_trips_only_named_fields(self):
        before = self.doc.read_text(encoding="utf-8")
        target, new_text, err = C.plan_set_outcome(
            self.research, self.id6, "adopted", ["pln001", "spc002"]
        )
        self.assertIsNone(err)
        fm_before = R.parse_frontmatter(before)
        fm_after = R.parse_frontmatter(new_text)
        # Only outcome + consumed-by changed; every other field byte-identical.
        for k in (
            "id",
            "created",
            "set",
            "order",
            "topic",
            "model",
            "kind",
            "status",
            "summary",
        ):
            self.assertEqual(fm_before.get(k), fm_after.get(k), f"field {k} changed")
        self.assertEqual(fm_after["outcome"], "adopted")
        self.assertEqual(fm_after["consumed-by"], ["pln001", "spc002"])
        # Body preserved, including the decoy `outcome:` body line.
        self.assertIn("outcome: not-frontmatter", new_text)
        self.assertEqual(
            before.split("---", 2)[2], new_text.split("---", 2)[2], "body changed"
        )

    def test_set_append_replace_clear(self):
        # set
        _t, txt, err = C.plan_set_outcome(
            self.research, self.id6, "informational", ["pln001"]
        )
        self.assertIsNone(err)
        self.assertEqual(R.parse_frontmatter(txt)["consumed-by"], ["pln001"])
        self.doc.write_text(txt, encoding="utf-8")
        # replace
        _t, txt, err = C.plan_set_outcome(
            self.research, self.id6, None, ["aaaaaa", "bbbbbb"]
        )
        self.assertIsNone(err)
        self.assertEqual(R.parse_frontmatter(txt)["consumed-by"], ["aaaaaa", "bbbbbb"])
        self.doc.write_text(txt, encoding="utf-8")
        # clear via '-'
        _t, txt, err = C.plan_set_outcome(
            self.research, self.id6, None, None, clear_consumed=True
        )
        self.assertIsNone(err)
        self.assertEqual(R.parse_frontmatter(txt)["consumed-by"], [])

    def test_invalid_outcome_rejected(self):
        _t, _txt, err = C.plan_set_outcome(self.research, self.id6, "bogus", None)
        self.assertIsNotNone(err)
        self.assertIn("outcome must be", err)

    def test_run_set_outcome_apply_writes(self):
        import argparse

        args = argparse.Namespace(
            id=self.id6,
            to="adopted",
            consumed_by="pln001",
            dir=str(self.root),
            apply=True,
        )
        rc = C.run_set_outcome(args)
        self.assertEqual(rc, 0)
        fm = R.parse_frontmatter(self.doc.read_text(encoding="utf-8"))
        self.assertEqual(fm["outcome"], "adopted")
        self.assertEqual(fm["consumed-by"], ["pln001"])

    def test_run_set_outcome_tolerates_two_spellings_of_one_dir(self):
        """Windows CI regression: ``--dir`` given as an 8.3 short path while the resolver returns the
        long path made ``relative_to`` raise AFTER a successful plan. A symlink is the portable twin
        of the short-vs-long mismatch, so this reproduces on every host that allows symlinks."""
        import argparse
        import os

        alias = Path(tempfile.mkdtemp()) / "alias"
        try:
            os.symlink(self.root, alias, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest(
                "symlinks unavailable (unprivileged Windows); CI covers it natively"
            )
        args = argparse.Namespace(
            id=self.id6, to="adopted", consumed_by=None, dir=str(alias), apply=True
        )
        rc = C.run_set_outcome(args)
        self.assertEqual(rc, 0)
        fm = R.parse_frontmatter(self.doc.read_text(encoding="utf-8"))
        self.assertEqual(fm["outcome"], "adopted")


if __name__ == "__main__":
    unittest.main()
