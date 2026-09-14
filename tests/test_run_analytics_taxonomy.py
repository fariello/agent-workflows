#!/usr/bin/env python3
"""runanalytics Order 06 (`aflsz3`) E-01/E-02: the MULTI-LABEL taxonomy and its accounting.

HERMETICITY, WHICH IS A STOP CONDITION IN THE PLAN RATHER THAN A PREFERENCE. Every fixture here is a
literal constructed in this file. Nothing reads `.aw/records/runs/`: it is gitignored, absent from a
worker lane by construction, mutable, grows with every run, and carries absolute maintainer paths the
leak detector flags at `fail`. The plan's fourth stop condition is explicit ("if a test needs the live
corpus to pass, STOP and build a fixture"), and the two suite failures it cites as precedent are
themselves live-corpus couplings.

WHAT THESE TESTS ASSERT THAT A WEAKER SUITE WOULD NOT. The plan's central correction is that a
single-label taxonomy DISCARDS a real class in two of every five commands, so the tests assert the
LABEL SET rather than a winner, and `test_a_single_label_taxonomy_would_DISCARD_a_real_class` shows
the loss concretely by simulating the rejected design.
"""

from __future__ import annotations

import json
import unittest

from agent_workflows import run_analytics_taxonomy as tax
from agent_workflows.run_analytics_taxonomy import (
    ActivityClass,
    Confidence,
    SegmentKind,
    TaxonomyError,
)


#: An absolute-looking path used ONLY to prove a classification record never carries one.
#:
#: DELIBERATELY NOT HOME-DIRECTORY-SHAPED, and that is a real constraint rather than fussiness: the
#: shipped leak sanitizer (`aw sanitize --agent`, enforced by a pre-commit hook) flags a home-path
#: pattern in a TRACKED FILE at `fail` severity, and it does not and should not care that this
#: particular one is a test fixture. A detector that exempted files claiming to be tests would be
#: trivially defeated, and this very fixture tripped the hook on its first revision. The value below
#: is absolute enough to exercise the same code path (`_looks_like_path`, the basename reduction, the
#: file-category rules) while matching no user-directory shape.
_FAKE_ABS_PATH = "/srv/example-project/src/module.py"

#: A distinctive token that must never survive into a persisted record. Separate from the path so the
#: leak assertions can name what they are looking for.
_SECRET_TOKEN = "example-project"


class SegmentSplittingTests(unittest.TestCase):
    """The split that makes multi-label classification possible at all."""

    def test_a_compound_command_splits_into_its_segments(self):
        segments, had_cd = tax.split_command_segments("git status && python3 -m pytest")
        self.assertEqual(segments, ["git status", "python3 -m pytest"])
        self.assertFalse(had_cd)

    def test_a_leading_cd_is_STRIPPED_and_reported(self):
        """45.3 percent of real commands carry one; leaving it in classifies by the prologue."""

        segments, had_cd = tax.split_command_segments("cd /repo && git status")
        self.assertEqual(segments, ["git status"])
        self.assertTrue(had_cd)

    def test_every_separator_form_splits(self):
        for command, expected in (
            ("a && b", 2),
            ("a || b", 2),
            ("a | b", 2),
            ("a; b", 2),
            ("a\nb", 2),
            ("a && b | c; d", 4),
        ):
            with self.subTest(command=command):
                segments, _ = tax.split_command_segments(command)
                self.assertEqual(len(segments), expected)

    def test_an_empty_command_yields_NO_segment_rather_than_one_empty_one(self):
        """The corpus holds 3834 empty segments; counting them would inflate every denominator."""

        for blank in ("", "   ", "\n", "\t"):
            with self.subTest(blank=repr(blank)):
                self.assertEqual(tax.split_command_segments(blank), ([], False))

    def test_a_wrapper_head_is_skipped_so_the_real_head_is_found(self):
        for command, expected_class in (
            ("sudo apt install foo", ActivityClass.DEPENDENCY),
            ("time python3 -m pytest", ActivityClass.TESTS),
            ("timeout 30 ruff check .", ActivityClass.LINT_FORMAT),
            ("env FOO=1 git commit -m x", ActivityClass.GIT),
        ):
            with self.subTest(command=command):
                self.assertIn(expected_class, tax.classify_command(command).labels)

    def test_an_env_prefix_is_stripped_so_the_real_head_is_found(self):
        self.assertIn(
            ActivityClass.TESTS,
            tax.classify_command("PYTHONPATH=. pytest tests/").labels,
        )

    def test_an_absolute_head_reduces_to_its_BASENAME(self):
        """The same tool lives at different paths, and a path must not influence a label."""

        self.assertIn(
            ActivityClass.GIT, tax.classify_command("/usr/bin/git status").labels
        )


class MultiLabelClassificationTests(unittest.TestCase):
    """E-01: THE central correction. Overlap is the norm, so a label SET is the result."""

    def test_a_command_that_is_simultaneously_git_and_test_yields_BOTH_labels(self):
        """The exemplar V-01 requires, with per-label evidence and no command text."""

        result = tax.classify_command("cd /repo && git status && python3 -m pytest")

        self.assertIn(ActivityClass.GIT, result.labels)
        self.assertIn(ActivityClass.TESTS, result.labels)
        self.assertTrue(result.is_multi_class)
        self.assertTrue(result.had_leading_cd)

        # Per-label evidence names the RULE and the SEGMENT KIND, never the text.
        self.assertEqual(result.evidence[ActivityClass.GIT].rule, "git:status")
        self.assertEqual(
            result.evidence[ActivityClass.GIT].kind, SegmentKind.COMMAND_SUBCOMMAND
        )
        self.assertEqual(
            result.evidence[ActivityClass.TESTS].rule, "python-module:pytest"
        )
        self.assertEqual(
            result.evidence[ActivityClass.TESTS].kind, SegmentKind.MODULE_INVOCATION
        )

    def test_a_single_label_taxonomy_would_DISCARD_a_real_class(self):
        """The rejected design, simulated, so the loss is demonstrated rather than asserted.

        This is the measured defect (41.9 percent of commands): a precedence chain keeps ONE label,
        and which it drops is an artifact of the ordering. Keeping the falsified design executable in
        a test is what stops a future reader from 'simplifying' the set back into a winner.
        """

        result = tax.classify_command("git status && python3 -m pytest")
        real = [c for c in result.labels if c is not ActivityClass.OTHER_UNKNOWN]
        self.assertGreaterEqual(
            len(real), 2, "the command genuinely carries 2+ classes"
        )

        # THE REJECTED SINGLE-LABEL RESULT: precedence picks one and the rest are lost.
        single = result.display_label()
        discarded = [c for c in real if c is not single]
        self.assertTrue(
            discarded,
            "a single-label result discards at least one real class, which is the defect",
        )

    def test_a_grep_into_a_redirect_is_simultaneously_inspection_AND_editing(self):
        result = tax.classify_command("grep -rn foo . > out.txt")
        self.assertIn(ActivityClass.INSPECTION, result.labels)
        self.assertIn(ActivityClass.IMPLEMENTATION, result.labels)
        self.assertEqual(
            result.evidence[ActivityClass.IMPLEMENTATION].kind, SegmentKind.REDIRECTION
        )

    def test_a_pipeline_of_inspection_into_editing_carries_both(self):
        result = tax.classify_command("grep -rn foo . | sed 's/a/b/' > out.txt")
        self.assertIn(ActivityClass.INSPECTION, result.labels)
        self.assertIn(ActivityClass.IMPLEMENTATION, result.labels)

    def test_a_redirect_to_dev_null_or_a_fd_is_NOT_an_edit(self):
        """Counting these would classify most diagnostic commands as implementation."""

        for command in ("pytest 2>&1", "ls >/dev/null", "make test > /dev/null 2>&1"):
            with self.subTest(command=command):
                result = tax.classify_command(command)
                impl = result.evidence.get(ActivityClass.IMPLEMENTATION)
                self.assertFalse(
                    impl is not None and impl.kind is SegmentKind.REDIRECTION,
                    "a discard redirect must not be recorded as a write",
                )

    def test_a_git_inspection_subcommand_is_BOTH_git_and_inspection(self):
        """`git status`/`diff`/`log` do not mutate, and filing them as git alone makes the git
        class unreadable as a measure of version-control work."""

        for subcommand in ("status", "diff", "log", "show", "blame"):
            with self.subTest(subcommand=subcommand):
                result = tax.classify_command(f"git {subcommand}")
                self.assertIn(ActivityClass.GIT, result.labels)
                self.assertIn(ActivityClass.INSPECTION, result.labels)

    def test_a_git_mutation_subcommand_is_git_and_NOT_inspection(self):
        for subcommand in ("commit", "merge", "rebase", "reset", "push"):
            with self.subTest(subcommand=subcommand):
                result = tax.classify_command(f"git {subcommand}")
                self.assertIn(ActivityClass.GIT, result.labels)
                self.assertNotIn(ActivityClass.INSPECTION, result.labels)

    def test_per_label_shares_sum_to_one_so_a_corpus_total_is_not_inflated(self):
        """Multi-label commands would double count without a share; this is what prevents it."""

        result = tax.classify_command("git status && pytest && ruff check .")
        self.assertAlmostEqual(sum(result.shares.values()), 1.0, places=9)

    def test_the_display_label_is_PRESENTATION_ONLY_and_removes_nothing(self):
        result = tax.classify_command("git status && python3 -m pytest")
        self.assertEqual(result.display_label(), ActivityClass.TESTS)
        # Every label survives. That is the whole distinction from precedence-as-classification.
        self.assertIn(ActivityClass.GIT, result.labels)
        self.assertIn(ActivityClass.INSPECTION, result.labels)

    def test_display_precedence_covers_EVERY_class_so_it_is_total(self):
        self.assertEqual(set(tax.DISPLAY_PRECEDENCE), set(tax.ACTIVITY_CLASSES))


class AmbiguityAndCoverageTests(unittest.TestCase):
    """E-02 and DECISION 03-aflsz3-D4: unclassified and ambiguous are DIFFERENT facts."""

    def test_a_bare_python3_is_AMBIGUOUS_with_low_confidence_not_a_guess(self):
        """Measured 3807 segments. It runs both tests and ad-hoc analysis, so a class is a guess."""

        result = tax.classify_command("python3")
        self.assertTrue(result.is_ambiguous)
        self.assertEqual(
            result.evidence[ActivityClass.OTHER_UNKNOWN].confidence, Confidence.LOW
        )
        self.assertEqual(
            result.evidence[ActivityClass.OTHER_UNKNOWN].rule,
            "ambiguous-interpreter:python3",
        )

    def test_an_AMBIGUOUS_command_is_NOT_counted_in_the_coverage_gap(self):
        """The separation D-4 exists for: mixing them makes a rising gap unattributable."""

        ambiguous = tax.classify_command("python3")
        self.assertTrue(ambiguous.is_ambiguous)
        self.assertFalse(
            ambiguous.is_unclassified,
            "an ambiguous command matched a rule; it is not a taxonomy coverage gap",
        )

        gap = tax.classify_command("wibblefrotz --xyz")
        self.assertTrue(gap.is_unclassified)
        self.assertFalse(gap.is_ambiguous)

    def test_a_resolvable_python_module_is_NOT_ambiguous(self):
        """The module form is checked first, so the resolvable case never falls through."""

        result = tax.classify_command("python3 -m pytest tests/")
        self.assertEqual(result.labels, (ActivityClass.TESTS,))
        self.assertFalse(result.is_ambiguous)
        self.assertEqual(
            result.evidence[ActivityClass.TESTS].confidence, Confidence.HIGH
        )

    def test_echo_is_NARRATION_rather_than_dumped_into_other_unknown(self):
        """`echo` is the largest single unclassified head at 14895 segments, an eighth of all."""

        result = tax.classify_command("echo 'starting the analysis'")
        self.assertEqual(result.labels, (ActivityClass.NARRATION,))
        self.assertFalse(result.is_unclassified)

    def test_the_measured_class_vocabulary_is_covered_by_rules(self):
        """Every class the baseline measured a count for must be reachable from a command."""

        exemplars = {
            ActivityClass.INSPECTION: "ls -la",
            ActivityClass.IMPLEMENTATION: "sed -i s/a/b/ f.py",
            ActivityClass.GIT: "git commit -m x",
            ActivityClass.TESTS: "pytest",
            ActivityClass.AW_TOOLING: "aw ipd lint",
            ActivityClass.LINT_FORMAT: "ruff check .",
            ActivityClass.DEPENDENCY: "pip install foo",
            ActivityClass.IDLE_WAIT: "sleep 5",
            ActivityClass.NARRATION: "echo hi",
        }
        for activity, command in exemplars.items():
            with self.subTest(activity=activity.value):
                self.assertIn(activity, tax.classify_command(command).labels)

        measured = set(tax.CORPUS_BASELINE["segment_class_counts"])
        self.assertTrue(
            measured <= {a.value for a in exemplars},
            "every class the baseline counted has a rule exemplar",
        )


class RegressionFloorTests(unittest.TestCase):
    """E-02: `other-unknown` may never silently absorb a growing share."""

    def _accounting(self, commands):
        return tax.accumulate([tax.classify_command(c) for c in commands])

    def test_a_clean_corpus_is_WITHIN_the_floor(self):
        accounting = self._accounting(
            ["git status", "pytest", "ruff check .", "ls", "echo hi", "aw ipd lint"] * 4
        )
        regressed, reason = accounting.unclassified_regressed()
        self.assertFalse(regressed, reason)
        self.assertEqual(accounting.unclassified_command_share, 0.0)

    def test_the_unclassified_share_regression_floor_FAILS_when_coverage_regresses(
        self,
    ):
        """The failing-then-passing demonstration V-02 requires, in one test.

        Half the commands are deliberately unrecognizable, pushing the share far above the measured
        8.7 percent floor plus its 2-point margin. Then the same check passes on a clean corpus, which
        proves the floor discriminates rather than always firing.
        """

        regressed_accounting = self._accounting(
            ["git status", "wibblefrotz", "zzquux", "pytest"] * 5
        )
        regressed, reason = regressed_accounting.unclassified_regressed()
        self.assertTrue(
            regressed, "a 50 percent unclassified share must trip the floor"
        )
        self.assertIn("exceeds the measured baseline", reason)
        self.assertGreater(regressed_accounting.unclassified_command_share, 0.4)

        clean_accounting = self._accounting(["git status", "pytest"] * 10)
        clean_regressed, clean_reason = clean_accounting.unclassified_regressed()
        self.assertFalse(clean_regressed, clean_reason)

    def test_an_EMPTY_corpus_does_not_regress(self):
        """No data is not a regression; reporting one would fire on every empty fixture."""

        regressed, reason = tax.accumulate([]).unclassified_regressed()
        self.assertFalse(regressed)
        self.assertEqual(reason, "no-commands-classified")

    def test_the_floor_carries_a_DECLARED_margin_over_the_measured_baseline(self):
        self.assertEqual(tax.UNCLASSIFIED_SHARE_MARGIN, 0.02)
        self.assertEqual(tax.CORPUS_BASELINE["unclassified_command_share"], 0.087)

    def test_the_ambiguous_share_is_reported_SEPARATELY_from_the_gap(self):
        accounting = self._accounting(
            ["python3", "python3", "git status", "wibblefrotz"]
        )
        self.assertEqual(accounting.ambiguous_command_count, 2)
        self.assertEqual(accounting.unclassified_command_count, 1)
        self.assertAlmostEqual(accounting.ambiguous_command_share, 0.5)
        self.assertAlmostEqual(accounting.unclassified_command_share, 0.25)


class AccountingTests(unittest.TestCase):
    """E-02: the accounting is a MEASURED output computed from input, never copied from baseline."""

    def test_every_share_is_computed_from_the_INPUT_not_the_baseline(self):
        """The property that makes a stale baseline harmless: it cannot change a measurement."""

        accounting = tax.accumulate(
            [tax.classify_command(c) for c in ["git status && pytest", "ls"]]
        )
        self.assertEqual(accounting.command_count, 2)
        self.assertAlmostEqual(accounting.multi_class_command_share, 0.5)
        # The baseline's own figure is different, proving the value was not copied from it.
        self.assertNotAlmostEqual(
            accounting.multi_class_command_share,
            tax.CORPUS_BASELINE["multi_class_command_share"],
        )

    def test_the_baseline_is_LABELED_as_a_snapshot_and_not_current(self):
        """DECISION 03-aflsz3-D1: a labeled snapshot is auditable; a restated number is not."""

        self.assertEqual(tax.CORPUS_BASELINE["provenance"], "review-time-snapshot")
        self.assertEqual(tax.CORPUS_BASELINE["measured_at"], "2026-09-08")
        self.assertIs(tax.CORPUS_BASELINE["is_current"], False)
        self.assertIn("re-measure", tax.CORPUS_BASELINE["note"])

    def test_compare_to_baseline_marks_EVERY_row_as_not_current(self):
        comparison = tax.accumulate(
            [tax.classify_command("git status")]
        ).compare_to_baseline()
        self.assertIs(comparison["baseline_is_current"], False)
        for key in (
            "multi_class_command_share",
            "unclassified_command_share",
            "multi_segment_command_share",
        ):
            with self.subTest(key=key):
                self.assertIs(comparison[key]["baseline_is_current"], False)
                self.assertIn("observed", comparison[key])

    def test_class_segment_mass_does_not_double_count_a_multi_label_command(self):
        """A command counts once in total mass however many labels it carries."""

        accounting = tax.accumulate(
            [tax.classify_command("git status && pytest && ruff check .")]
        )
        self.assertAlmostEqual(
            sum(accounting.class_segment_mass.values()), 1.0, places=9
        )
        # While the per-class COMMAND counts legitimately exceed the command count.
        self.assertGreater(sum(accounting.class_command_counts.values()), 1)

    def test_four_or_more_classes_are_counted_so_a_fixed_arity_is_visibly_wrong(self):
        """1.6 percent of real commands match 4+, which is why 'primary plus secondary' truncates."""

        accounting = tax.accumulate(
            [
                tax.classify_command(
                    "git status && pytest && ruff check . && pip install foo"
                )
            ]
        )
        self.assertEqual(accounting.four_or_more_class_command_count, 1)

    def test_the_report_is_pasteable_and_names_both_shares(self):
        report = tax.accumulate(
            [tax.classify_command(c) for c in ["python3", "wibblefrotz", "git status"]]
        ).format_report()
        self.assertIn("UNCLASSIFIED share", report)
        self.assertIn("AMBIGUOUS share", report)
        self.assertIn("coverage gap", report)
        self.assertIn("regression floor", report)


class StructuredToolSignalTests(unittest.TestCase):
    """E-01: `edit`/`read`/`write` carry a structured signal and need no free text at all."""

    def test_a_file_tool_is_classified_from_its_TOOL_NAME(self):
        for tool, expected in (
            ("read", ActivityClass.INSPECTION),
            ("grep", ActivityClass.INSPECTION),
            ("glob", ActivityClass.INSPECTION),
            ("edit", ActivityClass.IMPLEMENTATION),
            ("write", ActivityClass.IMPLEMENTATION),
        ):
            with self.subTest(tool=tool):
                result = tax.classify_tool_call(tool)
                self.assertEqual(result.labels, (expected,))
                self.assertEqual(result.evidence[expected].kind, SegmentKind.TOOL_NAME)

    def test_a_file_path_contributes_only_its_CATEGORY_never_the_path(self):
        result = tax.classify_tool_call("edit", file_path=_FAKE_ABS_PATH)
        evidence = result.evidence[ActivityClass.IMPLEMENTATION]
        self.assertEqual(evidence.kind, SegmentKind.FILE_CATEGORY)
        self.assertEqual(evidence.rule, "tool:edit+category:source-code")
        serialized = json.dumps(result.to_dict())
        self.assertNotIn(_SECRET_TOKEN, serialized)
        self.assertNotIn("/srv/", serialized)
        self.assertNotIn("module.py", serialized)

    def test_the_measured_file_categories_are_all_reachable(self):
        for path, expected in (
            ("tests/test_foo.py", "test-code"),
            ("agent_workflows/module.py", "source-code"),
            (".aw/records/plans/pending/x.ipd.md", "plan-or-ipd"),
            (".aw/records/specs/y.spec.md", "spec"),
            ("README.md", "documentation"),
            ("pyproject.toml", "configuration"),
            ("some.unknownext", "other"),
        ):
            with self.subTest(path=path):
                self.assertEqual(tax._file_category(path), expected)

    def test_an_UNKNOWN_tool_name_is_unclassified_rather_than_guessed(self):
        result = tax.classify_tool_call("some_future_tool")
        self.assertTrue(result.is_unclassified)

    def test_a_bash_call_with_NO_command_recorded_counts_in_the_gap(self):
        """A missing signal must not silently vanish from the accounting."""

        result = tax.classify_tool_call("bash", command=None)
        self.assertTrue(result.is_unclassified)

    def test_the_measured_tool_census_is_recorded_and_has_ten_names(self):
        """The census V-01 asks for, as a labeled snapshot rather than a restated measurement."""

        census = tax.CORPUS_BASELINE["tool_name_counts"]
        self.assertEqual(len(census), 10)
        self.assertEqual(census["bash"], 22757)
        self.assertEqual(max(census, key=lambda k: census[k]), "bash")

    def test_classify_accepts_the_mapping_shape_a_session_log_yields(self):
        result = tax.classify({"tool": "bash", "command": "git status"})
        self.assertIn(ActivityClass.GIT, result.labels)
        result = tax.classify({"tool": "edit", "filePath": "tests/test_x.py"})
        self.assertIn(ActivityClass.IMPLEMENTATION, result.labels)

    def test_classify_REFUSES_a_non_mapping(self):
        for bad in ("a string", 42, None, ["list"]):
            with self.subTest(bad=bad):
                with self.assertRaises(TaxonomyError):
                    tax.classify(bad)  # type: ignore[arg-type]

    def test_a_corpus_sweep_survives_a_malformed_call(self):
        """One bad event costs its own label and nothing else."""

        results, accounting = tax.classify_corpus_calls(
            [
                {"tool": "bash", "command": "git status"},
                {"tool": None},
                {"tool": "read"},
            ]
        )
        self.assertEqual(len(results), 3)
        self.assertEqual(accounting.command_count, 3)


class PrivacyBoundaryTests(unittest.TestCase):
    """E-01: classification READS command text and PERSISTS only labels. Proven, not trusted."""

    def test_a_persisted_record_contains_NO_part_of_the_command(self):
        """The one item in the Set where the privacy boundary and the algorithm touch."""

        command = (
            f"cd /srv/{_SECRET_TOKEN} && git commit -m 'fix the widget' "
            f"&& cat {_FAKE_ABS_PATH}"
        )
        result = tax.classify_command(command)
        self.assertTrue(result.labels, "the command classified, so text WAS read")

        serialized = json.dumps(result.to_dict())
        for leak in (_SECRET_TOKEN, "widget", "/srv/", _FAKE_ABS_PATH, "module.py"):
            with self.subTest(leak=leak):
                self.assertNotIn(leak, serialized)

        # And the mechanical check agrees.
        tax.assert_no_command_text(result, command)

    def test_an_UNRECOGNIZED_aw_subcommand_does_not_reach_the_record(self):
        """THE REGRESSION TEST FOR A LEAK THIS SUITE ACTUALLY CAUGHT.

        An earlier revision built the rule as `f"aw:{first_arg}"`, interpolating the next token
        UNBOUNDED. `aw <anything>` would therefore have carried `<anything>` into a persisted rule
        identifier, which is the exact class of leak E-01's boundary exists to prevent. The fix looks
        the subcommand up in a closed vocabulary; this pins it.
        """

        result = tax.classify_command("aw supersecretsubcommand --flag")
        self.assertIn(ActivityClass.AW_TOOLING, result.labels)
        serialized = json.dumps(result.to_dict())
        self.assertNotIn("supersecretsubcommand", serialized)
        self.assertEqual(result.evidence[ActivityClass.AW_TOOLING].rule, "aw")

        # A RECOGNIZED subcommand still gets its granularity, so the fix did not simply blunt the rule.
        known = tax.classify_command("aw ipd lint")
        self.assertEqual(known.evidence[ActivityClass.AW_TOOLING].rule, "aw:ipd")

    def test_an_UNRECOGNIZED_python_module_does_not_reach_the_record(self):
        """The same leak shape on the module rule, closed the same way."""

        result = tax.classify_command("python3 -m secretinternalmodule")
        serialized = json.dumps(result.to_dict())
        self.assertNotIn("secretinternalmodule", serialized)
        self.assertEqual(
            result.evidence[ActivityClass.OTHER_UNKNOWN].rule,
            "python-module:unrecognized",
        )

    def test_the_closed_vocabulary_is_DERIVED_from_the_tables(self):
        """A hard-coded exception list would silently stop covering a table that later grew."""

        vocabulary = tax._closed_vocabulary()
        for token in ("commit", "status", "pytest", "ruff", "echo", "sleep"):
            with self.subTest(token=token):
                self.assertIn(token, vocabulary)
        for outsider in ("supersecretsubcommand", "widget", "secretinternalmodule"):
            with self.subTest(outsider=outsider):
                self.assertNotIn(outsider, vocabulary)

    def test_the_leak_CHECK_ITSELF_fires_on_a_planted_leak(self):
        """A control: a checker that refused nothing and one that was not looking are identical."""

        planted = {"labels": ["git"], "oops_the_command": "secretcommand --flag"}
        with self.assertRaises(TaxonomyError) as ctx:
            tax.assert_no_command_text(planted, "secretcommand --flag")
        self.assertIn("secretcommand", str(ctx.exception))

    def test_evidence_carries_a_RULE_and_a_KIND_and_no_text_field(self):
        result = tax.classify_command("git status")
        payload = result.evidence[ActivityClass.GIT].to_dict()
        self.assertEqual(
            set(payload), {"rule", "segment_kind", "confidence", "segment_count"}
        )
        for value in payload.values():
            self.assertIsInstance(value, (str, int))

    def test_every_persisted_label_is_a_bare_enum_token(self):
        """Labels cross the privacy projector's closed-vocabulary check, so they must be tokens."""

        payload = tax.classify_command("git status && pytest").to_dict()
        for label in payload["labels"]:
            self.assertIsInstance(label, str)
            self.assertRegex(label, r"^[a-z][a-z-]*$")


class VersioningTests(unittest.TestCase):
    """The taxonomy version is a contract Orders 07, 08 and 10 consume."""

    def test_a_classification_records_the_version_that_produced_it(self):
        self.assertEqual(
            tax.classify_command("git status").to_dict()["taxonomy_version"],
            tax.TAXONOMY_VERSION,
        )

    def test_the_accounting_records_the_version_too(self):
        self.assertEqual(
            tax.accumulate([]).to_dict()["taxonomy_version"], tax.TAXONOMY_VERSION
        )


if __name__ == "__main__":
    unittest.main()
