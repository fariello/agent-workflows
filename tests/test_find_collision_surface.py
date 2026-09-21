"""`aw find` surfaces a GENUINE id6 collision and stays SILENT on the legitimate conventions.

IPD `paw8so` (Set `id6integ`, Order 02) E-05. The defect: `find` rendered a corrupt identity as an
unremarkable multi-result list at exit 0, because `selectors.resolve_one` drops the ambiguity
verdict `resolve_for_mutation` acts on. The difficulty is NOT detection but DISCRIMINATION: at least
five distinct situations produce a multi-row answer and only two of them are defects.

EVERY TEST HERE BUILDS A FIXTURE TREE UNDER `--dir`, NEVER ASSERTING AGAINST THE LIVE REPOSITORY,
and that is a requirement rather than a preference. The backlog item this plan graduated from
(`h2ceme`) named two live examples, `y6mfgo` and `ntf6sx`, and BOTH were cleared by the same commit
that filed it; a test pinned to live records would have had nothing to reproduce. The live tree is
legitimate for a one-off MEASUREMENT recorded as evidence, never as a test's input.

THE FIVE SHAPES, two loud and three silent:

  (a) GENUINE CROSS-TYPE DUPLICATE - two artifacts of different types each DECLARE the same id6.
      WARNS, with the D140 identity remedy.
  (b) SAME-TYPE LIFECYCLE DUPLICATE - one plan present in two disposition directories. WARNS, with
      the LIFECYCLE remedy, which is a DIFFERENT message: one copy is stale, which is not an
      identity problem and does not have an identity fix.
  (c) LEGITIMATE REFERENCE BY CONVENTION - a review record carrying its SUBJECT's id6 in its
      filename identity slot, required by `.aw/records/reviews/README.md`. SILENT. Measured
      2026-09-21 on this repository: 257 review files, all 257 carrying a `- Subject-Id:` and none
      declaring an own `- Id:`. A warning here would fire 257 times and train the reader to ignore
      the real one.
  (d) SETID MULTI-MATCH - deliberately multi-target (`selectors.MATCH_SETID` is excluded from
      `UNIQUE_KINDS`). SILENT.
  (e) HEADER-INVISIBLE DECLARATION - a plan that genuinely DECLARES the id6 but whose `- Id:` line
      lies outside the resolver's BOUNDED read, so `resolve` reports `kind=substring` and the row
      LOOKS like a mere filename reference. SILENT, and classified as the declaring OWNER. This is
      the shape that proves the verdict does not rest on `Resolution.kind`, which means only "not
      proven to declare" and never "is a reference".
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import cli, selectors


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    """Run `aw <argv...>` capturing (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    rc = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


def _write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _plan(id6: str, status: str = "approved", setid: str = "tset") -> str:
    return (
        f"# Plan {id6}\n\n"
        "- Date: 2026-01-01\n"
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        f"- Set: {setid} (test set)\n\n"
        "## Goal\n\nbody\n"
    )


class GenuineCollisionWarnsTests(unittest.TestCase):
    """Shapes (a) and (b): the two defects, each with its OWN remedy."""

    def test_a_cross_type_declared_duplicate_warns_with_the_d140_identity_remedy(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-01-aaa111-a.ipd.md",
                _plan("aaa111"),
            )
            _write(
                root,
                ".aw/records/walkthroughs/20260101-tset-01-aaa111-w.walkthrough.md",
                "# W\n\n- Date: 2026-01-01\n- Id: aaa111\n\n## Body\n\nbody\n",
            )
            rc, out, _err = _run_cli(["find", "--dir", str(root), "aaa111"])

            # EXIT STAYS 0 and every matching row still prints: `find` is read-only and is often run
            # WHILE diagnosing a mess, so refusing to answer would make it useless when most needed.
            self.assertEqual(rc, 0, out)
            self.assertIn("20260101-tset-01-aaa111-a.ipd.md", out)
            self.assertIn("20260101-tset-01-aaa111-w.walkthrough.md", out)

            self.assertIn("id6 aaa111 is claimed as its OWN identity", out)
            self.assertIn("D140", out)
            self.assertIn("TYPED reference field", out)
            # NO COMMAND IS PROMISED, because `aw rename --to-id6` is a measured no-op on an
            # already-clustered name (which every colliding artifact necessarily has), so printing it
            # would send an operator to a command that silently does nothing and reports success.
            self.assertIn("No single verb delivers this today", out)

    def test_b_same_type_two_directory_duplicate_warns_with_the_lifecycle_remedy(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-02-bbb222-b.ipd.md",
                _plan("bbb222"),
            )
            _write(
                root,
                ".aw/records/plans/executed/20260101-tset-02-bbb222-b.ipd.md",
                _plan("bbb222", status="executed"),
            )
            rc, out, _err = _run_cli(["find", "--dir", str(root), "bbb222"])

            self.assertEqual(rc, 0, out)
            self.assertIn("pending/20260101-tset-02-bbb222-b.ipd.md", out)
            self.assertIn("executed/20260101-tset-02-bbb222-b.ipd.md", out)

            self.assertIn("SAME type", out)
            self.assertIn("STALE", out)
            self.assertIn("lifecycle problem, not an identity one", out)

    def test_the_two_shapes_do_not_share_one_message(self):
        """One message for both would send half of readers to the wrong remedy."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-01-aaa111-a.ipd.md",
                _plan("aaa111"),
            )
            _write(
                root,
                ".aw/records/walkthroughs/20260101-tset-01-aaa111-w.walkthrough.md",
                "# W\n\n- Date: 2026-01-01\n- Id: aaa111\n\n## Body\n",
            )
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-02-bbb222-b.ipd.md",
                _plan("bbb222"),
            )
            _write(
                root,
                ".aw/records/plans/executed/20260101-tset-02-bbb222-b.ipd.md",
                _plan("bbb222", status="executed"),
            )
            _rc_a, cross, _ = _run_cli(["find", "--dir", str(root), "aaa111"])
            _rc_b, same, _ = _run_cli(["find", "--dir", str(root), "bbb222"])

            self.assertIn("D140", cross)
            self.assertNotIn("D140", same)
            self.assertIn("lifecycle problem", same)
            self.assertNotIn("lifecycle problem", cross)


class LegitimateShapesStaySilentTests(unittest.TestCase):
    """Shapes (c), (d) and (e): every one asserts the ABSENCE of a warning.

    These three are the whole difficulty of the plan. Detection is easy; a warning that cries wolf
    on a documented convention is how a real one gets ignored.
    """

    def _assert_no_warning(self, out: str) -> None:
        self.assertNotIn("is claimed", out)
        self.assertNotIn("D140", out)
        self.assertNotIn(cli._FIND_ID6_COLLISION_RULE, out)

    def test_c_a_review_carrying_its_subjects_id6_is_silent(self):
        """`.aw/records/reviews/README.md`: "`<id6>` is the REVIEWED ARTIFACT's id6, not a fresh
        identifier ... so the join survives a rename". 257 review files rely on this."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-03-ccc333-c.ipd.md",
                _plan("ccc333"),
            )
            _write(
                root,
                ".aw/records/reviews/20260102-tset-03-ccc333-c.review.md",
                "# Review\n\n- Date: 2026-01-02\n- Subject-Id: ccc333\n- Subject-Type: plans\n\n## Findings\n",
            )
            rc, out, _err = _run_cli(["find", "--dir", str(root), "ccc333"])

            self.assertEqual(rc, 0, out)
            # BOTH rows still print - silence is about the WARNING, never about the result set.
            self.assertIn("20260101-tset-03-ccc333-c.ipd.md", out)
            self.assertIn("20260102-tset-03-ccc333-c.review.md", out)
            self._assert_no_warning(out)

    def test_d_a_setid_multi_match_is_silent_because_a_set_is_deliberately_a_group(
        self,
    ):
        """`MATCH_SETID` is excluded from `UNIQUE_KINDS` on purpose (`selectors.py`)."""
        with TemporaryDirectory() as td:
            root = Path(td)
            for n, i6 in (("01", "aaa111"), ("02", "bbb222"), ("03", "ccc333")):
                _write(
                    root,
                    f".aw/records/plans/pending/20260101-tset-{n}-{i6}-x.ipd.md",
                    _plan(i6, setid="tset"),
                )
            rc, out, _err = _run_cli(["find", "--dir", str(root), "tset"])

            self.assertEqual(rc, 0, out)
            self.assertEqual(
                3, sum(1 for line in out.splitlines() if ".ipd.md" in line), out
            )
            self._assert_no_warning(out)

    def test_e_a_header_invisible_sole_owner_is_silent_and_classified_as_the_owner(
        self,
    ):
        """The shape that proves the verdict does not rest on `Resolution.kind`.

        `resolve` reads a BOUNDED prefix (`selectors._read_header`, capped by `_HEADER_MAX_BYTES`),
        so a declaration beyond that bound is invisible to it and its OWNER resolves as
        `kind=substring` - indistinguishable, to `kind` alone, from a mere filename mention. The
        assertion on the byte offset is deliberate: if a future change moves the bound, this test
        must FAIL LOUDLY rather than silently stop exercising the shape it exists for.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            pad = "x" * (selectors._HEADER_MAX_BYTES + 4096)
            p = _write(
                root,
                ".aw/records/plans/pending/20260101-tset-04-ddd444-d.ipd.md",
                "# D\n\n- Date: 2026-01-01\n"
                f"- Concern: {pad}\n"
                "- Id: ddd444\n- Status: approved\n- Set: tset (test set)\n\n## Goal\n",
            )
            offset = p.read_text(encoding="utf-8").find("- Id: ddd444")
            self.assertGreater(
                offset,
                selectors._HEADER_MAX_BYTES,
                "the fixture must place the declaration BEYOND the bounded read, or it is not "
                "exercising shape (e) at all",
            )

            # The resolver cannot see the declaration...
            self.assertEqual(
                selectors.MATCH_SUBSTRING,
                selectors.resolve(root, "plans", "ddd444").kind,
            )
            # ...but the E-06 predicate can, and that is what the verdict uses.
            self.assertTrue(selectors.declares_id6(p, "ddd444"))
            self.assertEqual(
                selectors.OWNERSHIP_DECLARED, selectors.id6_ownership(p, "ddd444")
            )

            rc, out, _err = _run_cli(["find", "--dir", str(root), "ddd444"])
            self.assertEqual(rc, 0, out)
            self.assertIn("20260101-tset-04-ddd444-d.ipd.md", out)
            self._assert_no_warning(out)


class DeclarationPredicateTests(unittest.TestCase):
    """E-06: the per-row ownership predicate, which every later verdict rests on."""

    def test_the_predicate_is_bounded_to_the_metadata_region_so_a_quotation_is_not_a_claim(
        self,
    ):
        """A document QUOTING a metadata block is discussing an id6, not claiming it.

        This is the ARTIFACTS-NOT-MENTIONS contract (`selectors.metadata_region`). Without it, a
        research document citing a plan's front matter as an example would be read as a second
        DECLARER and reported as a collision - a false positive manufactured by the reader.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            quoting = _write(
                root,
                ".aw/records/prompts/20260101-tset-05-eee555-q.prompt.md",
                "# Q\n\n- Date: 2026-01-01\n- Id: eee555\n\n## Example\n\n- Id: aaa111\n",
            )
            self.assertFalse(selectors.declares_id6(quoting, "aaa111"))
            self.assertEqual(
                selectors.OWNERSHIP_FOREIGN_ID,
                selectors.id6_ownership(quoting, "aaa111"),
            )

    def test_a_typed_subject_field_makes_a_foreign_slot_a_reference_not_a_claim(self):
        """D140 prescribes a TYPED field for pointing at another artifact, and that is the
        discriminator - not the record's TYPE, which would be an exception list."""
        with TemporaryDirectory() as td:
            root = Path(td)
            review = _write(
                root,
                ".aw/records/reviews/20260102-tset-03-ccc333-c.review.md",
                "# R\n\n- Date: 2026-01-02\n- Subject-Id: ccc333\n\n## Findings\n",
            )
            self.assertEqual(
                selectors.OWNERSHIP_REFERENCE, selectors.id6_ownership(review, "ccc333")
            )

            # The SAME shape WITHOUT a typed field is the p7dqwz reuse D140 was written about: a
            # foreign id6 in the identity slot, no `- Id:` of its own, and nothing declaring the
            # relationship. That IS a claim, and must be reported.
            bare = _write(
                root,
                ".aw/records/walkthroughs/20260102-tset-03-ccc333-w.walkthrough.md",
                "# W\n\n- Date: 2026-01-02\n\n## Body\n",
            )
            self.assertEqual(
                selectors.OWNERSHIP_SLOT_ONLY, selectors.id6_ownership(bare, "ccc333")
            )

    def test_a_legacy_name_without_an_identity_slot_is_not_treated_as_holding_one(self):
        """`parse_clustered` can report `id6='assess'` for a legacy name whose real declared Id is
        something else (the trap recorded in `selectors.py`), so only a CANONICAL name has a slot."""
        with TemporaryDirectory() as td:
            root = Path(td)
            legacy = _write(
                root,
                ".aw/records/plans/pending/20260817-1357-01-assess-bugs-leftover.ipd.md",
                "# L\n\n- Date: 2026-08-17\n\n## Goal\n",
            )
            self.assertIsNone(selectors.filename_slot_id6(legacy))


class MachineSurfaceTests(unittest.TestCase):
    """E-03: which surface carries the finding, and which are byte-frozen."""

    def _fixture(self, root: Path) -> None:
        _write(
            root,
            ".aw/records/plans/pending/20260101-tset-01-aaa111-a.ipd.md",
            _plan("aaa111"),
        )
        _write(
            root,
            ".aw/records/walkthroughs/20260101-tset-01-aaa111-w.walkthrough.md",
            "# W\n\n- Date: 2026-01-01\n- Id: aaa111\n\n## Body\n",
        )

    def test_json_carries_the_finding_in_diagnostics_with_a_stable_rule_string(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            self._fixture(root)
            rc, out, _err = _run_cli(["find", "--dir", str(root), "aaa111", "--json"])
            self.assertEqual(rc, 0, out)
            payload = json.loads(out)
            diags = payload["diagnostics"]
            self.assertEqual(1, len(diags), diags)
            self.assertEqual("find.id6-collision", diags[0]["rule"])
            self.assertEqual("warning", diags[0]["severity"])
            self.assertIn("aaa111", diags[0]["detail"])

    def test_json_diagnostics_is_empty_for_a_legitimate_multi_row_shape(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-03-ccc333-c.ipd.md",
                _plan("ccc333"),
            )
            _write(
                root,
                ".aw/records/reviews/20260102-tset-03-ccc333-c.review.md",
                "# R\n\n- Date: 2026-01-02\n- Subject-Id: ccc333\n\n## Findings\n",
            )
            rc, out, _err = _run_cli(["find", "--dir", str(root), "ccc333", "--json"])
            self.assertEqual(rc, 0, out)
            self.assertEqual([], json.loads(out)["diagnostics"])

    def test_paths_stdout_carries_no_warning_because_scripts_consume_it_line_by_line(
        self,
    ):
        with TemporaryDirectory() as td:
            root = Path(td)
            self._fixture(root)
            rc, out, err = _run_cli(["find", "--dir", str(root), "aaa111", "--paths"])
            self.assertEqual(rc, 0, out)
            for line in [x for x in out.splitlines() if x.strip()]:
                self.assertTrue(line.startswith(".aw/records/"), line)
            # `--paths` is the explicitly script-shaped surface: silent on BOTH streams.
            self.assertEqual("", err)

    def test_agent_stdout_is_bare_paths_and_the_finding_goes_to_stderr(self):
        """`--agent` shares `--paths`' bare-path early return, so it can never reach
        `CommandResult.diagnostics`. STDOUT stays parseable; the signal goes to STDERR."""
        with TemporaryDirectory() as td:
            root = Path(td)
            self._fixture(root)
            rc, out, err = _run_cli(["find", "--dir", str(root), "aaa111", "--agent"])
            self.assertEqual(rc, 0, out)
            for line in [x for x in out.splitlines() if x.strip()]:
                self.assertTrue(line.startswith(".aw/records/"), line)
            self.assertIn("aw-find-warning:find.id6-collision:aaa111:cross-type:", err)

    def test_check_is_left_inert_rather_than_quietly_given_meaning(self):
        """`find`'s parser already ACCEPTS `--check` and ignores it. Giving it meaning here would be
        a behavior change outside this plan's declared scope (paw8so F-14)."""
        with TemporaryDirectory() as td:
            root = Path(td)
            self._fixture(root)
            rc_plain, out_plain, _ = _run_cli(["find", "--dir", str(root), "aaa111"])
            rc_check, out_check, _ = _run_cli(
                ["find", "--dir", str(root), "aaa111", "--check"]
            )
            self.assertEqual(rc_plain, rc_check)
            self.assertEqual(out_plain, out_check)
            self.assertEqual(0, rc_check)


class NoSecondScanTests(unittest.TestCase):
    """E-04: share the collision DEFINITION, never fork a corpus-wide scan."""

    def test_the_find_path_never_invokes_the_repo_wide_collision_checker(self):
        """Negative proof over CODE, not prose.

        The detector's own docstring DISCUSSES `check_collisions` at length (explaining why it is
        not delegated to), so a naive substring search over the source region would match the
        explanation rather than a call. Walk the AST instead and assert no call or import reaches
        the checker from any function on the find path.
        """
        import ast

        tree = ast.parse(Path(cli.__file__).read_text(encoding="utf-8"))
        targets = {
            "_detect_id6_collisions",
            "_id6_collision_message",
            "_run_find",
            "_find_type_records",
            "_resolve_selectors_with_kinds",
        }
        checked = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name not in targets:
                continue
            checked.add(node.name)
            for sub in ast.walk(node):
                if isinstance(sub, ast.Attribute):
                    self.assertNotEqual("check_collisions", sub.attr, node.name)
                if isinstance(sub, ast.Name):
                    self.assertNotEqual("check_collisions", sub.id, node.name)
                if isinstance(sub, (ast.Import, ast.ImportFrom)):
                    names = [a.name for a in sub.names]
                    mod = getattr(sub, "module", None) or ""
                    self.assertNotIn("check_engine", names, node.name)
                    self.assertNotIn("check_engine", mod, node.name)
        self.assertEqual(
            targets, checked, "a find-path function was renamed or removed"
        )

    def test_resolve_for_mutation_does_not_see_the_cross_type_shape(self):
        """Why the cross-type join has to be NEW logic rather than a delegation.

        `resolve_for_mutation` applies its `UNIQUE_KINDS` policy per `record_type` to ONE
        `Resolution`, so on a plan and a walkthrough that BOTH declare `aaa111` it reports no error
        for EITHER type. Its refusal fires only for a SAME-TYPE ambiguous resolution. That gap is
        why `aw check` needed its own cross-type inventory, and why `find`'s already-assembled
        cross-type row set is a genuinely new vantage point.
        """
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-01-aaa111-a.ipd.md",
                _plan("aaa111"),
            )
            _write(
                root,
                ".aw/records/walkthroughs/20260101-tset-01-aaa111-w.walkthrough.md",
                "# W\n\n- Date: 2026-01-01\n- Id: aaa111\n\n## Body\n",
            )
            for record_type in ("plans", "walkthroughs"):
                _paths, err = selectors.resolve_for_mutation(
                    root, record_type, "aaa111"
                )
                self.assertIsNone(err, f"{record_type} unexpectedly refused: {err}")

            # The SAME-TYPE shape, by contrast, IS refused - which is the half this surface reuses.
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-02-bbb222-b.ipd.md",
                _plan("bbb222"),
            )
            _write(
                root,
                ".aw/records/plans/executed/20260101-tset-02-bbb222-b.ipd.md",
                _plan("bbb222", status="executed"),
            )
            _paths, err = selectors.resolve_for_mutation(root, "plans", "bbb222")
            self.assertIsNotNone(err)
            self.assertIn("collision", err or "")

    def test_the_verdict_covers_types_the_checker_does_not(self):
        """`find` spans `reviews`/`comms`/`other`; `check_engine.SUPPORTED` does not. Delegating to
        the checker would go blind on exactly the type whose convention matters most here."""
        from agent_workflows import artifact_types as at
        from agent_workflows import check_engine as ce

        self.assertIn("reviews", at.ARTIFACT_TYPES)
        self.assertNotIn("reviews", ce.SUPPORTED)


class ResolverBoundsUnchangedTests(unittest.TestCase):
    """Negative proof: this plan changes a REPORT, not what `aw find` MATCHES."""

    def test_the_bounded_read_constants_are_untouched(self):
        """Widening them would change which records match for every type and every front-matter
        kind, which `selectors.py`'s own precedent records as a MATCHING-BEHAVIOR decision and not a
        cleanup (paw8so OQ-04)."""
        self.assertEqual(4096, selectors._HEADER_CHUNK_BYTES)
        self.assertEqual(262144, selectors._HEADER_MAX_BYTES)

    def test_a_single_match_lookup_reads_no_extra_file(self):
        """The predicate runs over ALREADY-MATCHED rows, so the overwhelmingly common single-row
        lookup must pay nothing at all for it."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                ".aw/records/plans/pending/20260101-tset-01-aaa111-a.ipd.md",
                _plan("aaa111"),
            )
            matches = [
                cli._FindMatch(
                    "aaa111",
                    "plans",
                    root / ".aw/records/plans/pending/20260101-tset-01-aaa111-a.ipd.md",
                    selectors.MATCH_ID6,
                )
            ]
            opened: list[str] = []
            real_read_text = Path.read_text

            def _counting_read_text(self, *a, **kw):
                opened.append(str(self))
                return real_read_text(self, *a, **kw)

            Path.read_text = _counting_read_text  # type: ignore[method-assign]
            try:
                self.assertEqual([], cli._detect_id6_collisions(root, matches))
            finally:
                Path.read_text = real_read_text  # type: ignore[method-assign]
            # ONE row, so at most that row's own declaration is read; never a corpus sweep.
            self.assertLessEqual(len(opened), 1, opened)


if __name__ == "__main__":
    unittest.main()
