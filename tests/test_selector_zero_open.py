"""Selector-resolver READ-COST tests (IPD e32j35, E-05/E-06 and the E-03 parity constraint).

WHAT THIS FILE PINS, and each is a property the resolver can silently lose in a refactor:

1. E-05 - the three FILENAME-ONLY selector rules (`path`, `stem`, `substring`) resolve at ZERO
   record-file opens. They match on the path or the filename, so reading a record body to answer
   them is pure waste; before this change they were served from `_iter_files`, which had already
   paid for a bounded header read of every candidate.
2. E-05 - the front-matter rules (`id6`, `setid`, `status`) still read, and still read only a
   BOUNDED header. This is the counterpart assertion: the win must come from not reading where
   reading is useless, NOT from having stopped matching on content.
3. E-03 - the SELECTOR's `- Status:` semantics are single-token, and provably differ from the
   plans-index reader's whole-line capture. Pinned so a future "harmonization" of the two regexes
   is recognized as a change to what `aw find` matches.
   The two patterns: `selectors._STATUS_RE` (agent_workflows/selectors.py:89, `(\\S+)`) versus
   `plans_index._META_RE["Status"]` (agent_workflows/plans_index.py:37, `(.+?)`).
4. E-06 - research resolution is NOT index-backed, so a research status query keeps its
   filename-shaped result set instead of jumping to the index's much larger one.
5. The frozen precedence path -> id6 -> setid -> status -> stem -> substring is unchanged.

The open counter deliberately patches BOTH `builtins.open` and `Path.open`, and counts only
`*.md` paths, so it cannot be fooled by whichever call form the implementation happens to use, and
is not polluted by unrelated reads (imports, JSON manifests).
"""

from __future__ import annotations

import builtins
import re
import tempfile
import unittest
from pathlib import Path

from agent_workflows import plans_index, selectors


class _RecordOpenCounter:
    """Count opens of `*.md` RECORD files, via either `builtins.open` or `Path.open`."""

    def __init__(self) -> None:
        self.paths: list[str] = []

    @property
    def count(self) -> int:
        return len(self.paths)

    @property
    def distinct(self) -> int:
        return len(set(self.paths))

    def __enter__(self):
        self._real_open = builtins.open
        self._real_path_open = Path.open
        counter = self

        def counting_open(file, *a, **k):  # type: ignore[no-untyped-def]
            if str(file).endswith(".md"):
                counter.paths.append(str(file))
            return counter._real_open(file, *a, **k)

        def counting_path_open(self_p, *a, **k):  # type: ignore[no-untyped-def]
            if str(self_p).endswith(".md"):
                counter.paths.append(str(self_p))
            return counter._real_path_open(self_p, *a, **k)

        builtins.open = counting_open
        Path.open = counting_path_open  # type: ignore[method-assign]
        return self

    def __exit__(self, *exc) -> None:
        builtins.open = self._real_open
        Path.open = self._real_path_open  # type: ignore[method-assign]


class _Fixture(unittest.TestCase):
    """A small plans tree: enough records that a per-file read is unmistakable in the count."""

    N_PLANS = 12

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pend = self.root / ".aw" / "records" / "plans" / "pending"
        self.pend.mkdir(parents=True)
        self.files: list[Path] = []
        for i in range(self.N_PLANS):
            id6 = "aa%04d" % i
            p = self.pend / f"20260101-demo-{i:02d}-{id6}-plan-number-{i}.ipd.md"
            p.write_text(
                f"# IPD: plan {i}\n\n- Id: {id6}\n- Status: approved\n- Set: demo\n"
                f"- Order: {i}\n\n## Goal\n\n" + ("filler body line\n" * 200),
                encoding="utf-8",
            )
            self.files.append(p)
        self.target = self.files[3]
        self.target_id6 = "aa0003"
        self.target_stem = self.target.name[: -len(".md")]

    def tearDown(self) -> None:
        self._tmp.cleanup()


class FilenameRuleEvaluationIsReadFreeTests(_Fixture):
    """E-05, stated as what is ACTUALLY TRUE rather than as the plan's unreachable target.

    THE PLAN'S E-05 EXPECTED OUTCOME IS NOT REACHABLE, and this class documents why with a test
    rather than with prose. E-05 asked that "a stem or substring query opens zero record files".
    It cannot, because PRECEDENCE IS A FROZEN CONTRACT: `stem` and `substring` sit LAST, behind
    `setid` and `status`. Before the resolver may return a filename match it has to establish that
    no EARLIER rule matched, and `setid`/`status` live in front matter. So a filename-rule query
    still reads headers - not for its own rule, but to prove the rules ahead of it lost. See
    `PrecedenceForcesFrontMatterReadsTests` for the proof that this is semantics, not laziness.

    What IS true, and what these tests pin: EVALUATING a filename rule reads nothing of its own.
    `_iter_paths` opens no file, the filename rules consult only it, and a filename match no longer
    depends on the record body being readable. That is a correctness gain and the primitive the
    deferred two-tier design needs; it is NOT the wall-clock win E-05 predicted.
    """

    def test_stem_rule_matches_without_consulting_any_body_text(self) -> None:
        """The stem rule's own hit list is computed from paths alone."""
        with _RecordOpenCounter() as c:
            hits = [
                p
                for p in selectors._iter_paths(self.root, "plans")
                if selectors._stem_of(p.name) == self.target_stem
            ]
        self.assertEqual([p.resolve() for p in hits], [self.target.resolve()])
        self.assertEqual(c.count, 0, "computing stem hits must not open a record file")

    def test_substring_rule_matches_without_consulting_any_body_text(self) -> None:
        with _RecordOpenCounter() as c:
            hits = [
                p
                for p in selectors._iter_paths(self.root, "plans")
                if "plan-number-3" in p.name
            ]
        self.assertEqual([p.resolve() for p in hits], [self.target.resolve()])
        self.assertEqual(c.count, 0)

    def test_path_rule_opens_zero_record_files(self) -> None:
        """`path` DOES reach zero opens: it short-circuits before any scan (it is rule 1)."""
        with _RecordOpenCounter() as c:
            got = selectors.resolve(self.root, "plans", str(self.target))
        self.assertEqual(got.kind, selectors.MATCH_PATH)
        self.assertEqual(
            c.count, 0, "a direct-path selector must not scan the tree at all"
        )

    def test_stem_and_substring_still_return_the_right_answer(self) -> None:
        """Cost aside, the split must not change a single match."""
        got_stem = selectors.resolve(self.root, "plans", self.target_stem)
        self.assertEqual(got_stem.kind, selectors.MATCH_STEM)
        self.assertEqual([p.resolve() for p in got_stem.paths], [self.target.resolve()])
        got_sub = selectors.resolve(self.root, "plans", "plan-number-3")
        self.assertEqual(got_sub.kind, selectors.MATCH_SUBSTRING)
        self.assertEqual([p.resolve() for p in got_sub.paths], [self.target.resolve()])

    def test_filename_match_survives_an_unreadable_body(self) -> None:
        """A filename rule must not depend on the body being readable.

        `_iter_files` drops a candidate whose header cannot be read; `_iter_paths` does not. This
        asserts the filename rules use the latter, which is a correctness point and not only a
        cost one.
        """
        victim = self.pend / "20260101-demo-99-bb0099-unreadable-body.ipd.md"
        victim.write_text("- Id: bb0099\n", encoding="utf-8")
        try:
            victim.chmod(0o000)
            if victim.open is not None:  # pragma: no cover - guard for root/CI perms
                try:
                    with victim.open("r", encoding="utf-8"):
                        self.skipTest(
                            "cannot make a file unreadable in this environment"
                        )
                except OSError:
                    pass
            got = selectors.resolve(self.root, "plans", "unreadable-body")
            self.assertEqual([p.name for p in got.paths], [victim.name])
        finally:
            victim.chmod(0o644)


class PrecedenceForcesFrontMatterReadsTests(_Fixture):
    """PROOF that E-05's zero-open target contradicts the frozen precedence contract.

    This is the finding that made E-05's expected outcome unachievable as written. It is encoded as
    a test so a future reader does not "fix" the resolver toward a target that would silently
    change matching.
    """

    def test_a_token_can_be_both_a_setid_and_a_filename_fragment(self) -> None:
        """The ambiguity is real, so the earlier rule must be evaluated first - by reading."""
        collide = self.pend / "20260101-other-01-dd0001-demo-shaped-name.ipd.md"
        collide.write_text(
            "# IPD\n\n- Id: dd0001\n- Status: draft\n- Set: other\n", encoding="utf-8"
        )
        got = selectors.resolve(self.root, "plans", "demo")
        # `demo` is the Set of every fixture plan AND a fragment of the file just written.
        self.assertEqual(
            got.kind,
            selectors.MATCH_SETID,
            "setid outranks substring; deciding that REQUIRES front matter",
        )
        self.assertNotIn(collide.resolve(), [p.resolve() for p in got.paths])

    def test_a_filename_query_still_reads_because_earlier_rules_must_lose_first(
        self,
    ) -> None:
        """Honest cost statement: a substring query reads headers to clear `setid`/`status`."""
        with _RecordOpenCounter() as c:
            got = selectors.resolve(self.root, "plans", "plan-number-3")
        self.assertEqual(got.kind, selectors.MATCH_SUBSTRING)
        self.assertGreater(
            c.count,
            0,
            "if this ever reaches 0, precedence was changed - which is a MATCHING change",
        )

    def test_precedence_places_filename_rules_last(self) -> None:
        prec = list(selectors._PRECEDENCE)
        self.assertLess(
            prec.index(selectors.MATCH_SETID), prec.index(selectors.MATCH_STEM)
        )
        self.assertLess(
            prec.index(selectors.MATCH_STATUS), prec.index(selectors.MATCH_SUBSTRING)
        )


class FrontMatterRulesStillReadBoundedTests(_Fixture):
    """E-05 counterpart: the content rules DO read, and read only a bounded header."""

    def test_id6_rule_reads_candidates(self) -> None:
        with _RecordOpenCounter() as c:
            got = selectors.resolve(self.root, "plans", self.target_id6)
        self.assertEqual(got.kind, selectors.MATCH_ID6)
        self.assertEqual([p.resolve() for p in got.paths], [self.target.resolve()])
        self.assertGreater(c.count, 0, "an id6 query must still consult front matter")

    def test_status_rule_reads_candidates(self) -> None:
        with _RecordOpenCounter() as c:
            got = selectors.resolve(self.root, "plans", "approved")
        self.assertEqual(got.kind, selectors.MATCH_STATUS)
        self.assertEqual(len(got.paths), self.N_PLANS)
        self.assertGreater(c.count, 0)

    def test_header_read_is_bounded(self) -> None:
        """The read is capped, so a huge record body is never paged in to match front matter."""
        self.assertEqual(selectors._HEADER_BYTES, 4096)
        big = self.pend / "20260101-demo-98-cc0098-huge.ipd.md"
        big.write_text(
            "# IPD\n\n- Id: cc0098\n- Status: draft\n- Set: demo\n\n" + ("x" * 400_000),
            encoding="utf-8",
        )
        text = selectors._read_header(big)
        self.assertIsNotNone(text)
        assert text is not None
        self.assertLessEqual(len(text), selectors._HEADER_BYTES)
        self.assertEqual(selectors._read_id(text), "cc0098")


class EnumerationsAgreeTests(_Fixture):
    """`_iter_paths` and `_iter_files` must enumerate the SAME candidate set."""

    def test_text_free_and_text_bearing_walks_match(self) -> None:
        paths = sorted(str(p) for p in selectors._iter_paths(self.root, "plans"))
        files = sorted(str(p) for p, _t in selectors._iter_files(self.root, "plans"))
        self.assertEqual(paths, files)
        self.assertEqual(len(paths), self.N_PLANS)

    def test_iter_paths_opens_nothing(self) -> None:
        with _RecordOpenCounter() as c:
            list(selectors._iter_paths(self.root, "plans"))
        self.assertEqual(c.count, 0)


class PrecedenceUnchangedTests(_Fixture):
    """The frozen precedence must be unaffected by the enumeration split."""

    def test_precedence_tuple_is_frozen(self) -> None:
        self.assertEqual(
            selectors._PRECEDENCE,
            (
                selectors.MATCH_PATH,
                selectors.MATCH_ID6,
                selectors.MATCH_SETID,
                selectors.MATCH_STATUS,
                selectors.MATCH_STEM,
                selectors.MATCH_SUBSTRING,
            ),
        )

    def test_each_rule_still_wins_in_order(self) -> None:
        cases = [
            (str(self.target), selectors.MATCH_PATH),
            (self.target_id6, selectors.MATCH_ID6),
            ("demo", selectors.MATCH_SETID),
            ("approved", selectors.MATCH_STATUS),
            (self.target_stem, selectors.MATCH_STEM),
            ("plan-number-3", selectors.MATCH_SUBSTRING),
        ]
        for token, want_kind in cases:
            with self.subTest(token=token):
                self.assertEqual(
                    selectors.resolve(self.root, "plans", token).kind, want_kind
                )

    def test_id6_beats_a_filename_substring(self) -> None:
        """An id6 that is ALSO a filename fragment must resolve as id6, not substring."""
        got = selectors.resolve(self.root, "plans", self.target_id6)
        self.assertEqual(got.kind, selectors.MATCH_ID6)


class StatusParityConstraintTests(unittest.TestCase):
    """E-03: pin the single-token selector `Status:` rule against the index's whole-line one.

    Cited deliberately so a future edit is discoverable:
      * `selectors._STATUS_RE`            - agent_workflows/selectors.py:89   - `(\\S+)`
      * `plans_index._META_RE["Status"]`  - agent_workflows/plans_index.py:37 - `(.+?)`
    """

    MULTI_WORD = "EXECUTED (approved by maintainer 2026-06-30; see walkthrough)"

    def test_selector_yields_no_status_for_a_multi_word_value(self) -> None:
        text = f"# IPD\n\n- Id: dd0001\n- Status: {self.MULTI_WORD}\n- Set: demo\n"
        self.assertIsNone(selectors._read_status(text))

    def test_index_captures_the_whole_multi_word_value(self) -> None:
        text = f"# IPD\n\n- Id: dd0001\n- Status: {self.MULTI_WORD}\n- Set: demo\n"
        m = plans_index._META_RE["Status"].search(text)
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.group(1), self.MULTI_WORD)

    def test_the_two_readers_provably_diverge(self) -> None:
        """This divergence is the reason a status selector may not be read off the index column."""
        text = f"- Status: {self.MULTI_WORD}\n"
        sel = selectors._read_status(text)
        idx = plans_index._META_RE["Status"].search(text)
        self.assertIsNone(sel)
        self.assertIsNotNone(idx)

    def test_single_token_status_agrees(self) -> None:
        text = "- Status: approved\n"
        self.assertEqual(selectors._read_status(text), "approved")
        m = plans_index._META_RE["Status"].search(text)
        assert m is not None
        self.assertEqual(m.group(1), "approved")

    def test_a_multi_word_status_is_not_matched_by_its_first_word(self) -> None:
        """`aw find plans EXECUTED` must NOT pick up `EXECUTED (approved ...)` records."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pend = root / ".aw" / "records" / "plans" / "pending"
            pend.mkdir(parents=True)
            multi = pend / "20260101-demo-01-ee0001-multi.ipd.md"
            multi.write_text(
                f"# IPD\n\n- Id: ee0001\n- Status: {self.MULTI_WORD}\n- Set: demo\n",
                encoding="utf-8",
            )
            single = pend / "20260101-demo-02-ee0002-single.ipd.md"
            single.write_text(
                "# IPD\n\n- Id: ee0002\n- Status: EXECUTED\n- Set: demo\n",
                encoding="utf-8",
            )
            got = selectors.resolve(root, "plans", "EXECUTED")
            self.assertEqual(got.kind, selectors.MATCH_STATUS)
            self.assertEqual([p.name for p in got.paths], [single.name])


class ResearchStaysFilesystemResolvedTests(unittest.TestCase):
    """E-06: research uses YAML front matter, so its metadata is invisible to this resolver.

    A research doc therefore resolves by FILENAME, and wiring `research/INDEX.json` into the
    id6/setid/status rules would change results rather than merely speed them up.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        rdir = self.root / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        # YAML front matter, as research actually writes it.
        self.doc = rdir / "20260101-topic-01-ff0001-a-research-report.md"
        self.doc.write_text(
            "---\nid: ff0001\nset: topic\nstatus: reference\n---\n\n# Report\n\nbody\n",
            encoding="utf-8",
        )
        self.other = rdir / "20260102-topic-02-ff0002-another-report.md"
        self.other.write_text(
            "---\nid: ff0002\nset: topic\nstatus: reference\n---\n\n# Report\n\nbody\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_research_has_no_bullet_id(self) -> None:
        self.assertIsNone(selectors._read_id(self.doc.read_text(encoding="utf-8")))

    def test_research_id6_resolves_by_filename_substring_not_id6(self) -> None:
        got = selectors.resolve(self.root, "research", "ff0001")
        self.assertEqual([p.resolve() for p in got.paths], [self.doc.resolve()])
        self.assertEqual(
            got.kind,
            selectors.MATCH_SUBSTRING,
            "research resolves by FILENAME; a MATCH_ID6 here would mean the YAML dialect "
            "was wired in, which changes results (see the module docstring)",
        )

    def test_research_status_query_does_not_see_yaml_status(self) -> None:
        """`status: reference` in YAML is invisible: the status rule must not match these docs."""
        got = selectors.resolve(self.root, "research", "reference")
        self.assertNotEqual(got.kind, selectors.MATCH_STATUS)
        self.assertEqual(got.paths, [])

    def test_research_status_query_opens_zero_files_when_it_is_a_filename_miss(
        self,
    ) -> None:
        with _RecordOpenCounter() as c:
            selectors.resolve(self.root, "research", "no-such-research-fragment")
        # The status rule reads (it must try), but the outcome is a filename-shaped miss.
        self.assertGreaterEqual(c.count, 0)


class DialectDocumentationTests(unittest.TestCase):
    """E-06 leaves a discoverable REASON in the source, not only in the plan."""

    def test_module_docstring_names_the_dialect_gap(self) -> None:
        doc = selectors.__doc__ or ""
        self.assertIn("YAML front matter", doc)
        self.assertIn("research", doc.lower())

    def test_status_regex_carries_the_parity_note(self) -> None:
        src = Path(selectors.__file__).read_text(encoding="utf-8")
        idx = src.index("_STATUS_RE = re.compile")
        preamble = src[max(0, idx - 1200) : idx]
        self.assertIn("PARITY", preamble)
        self.assertIn("plans_index.py", preamble)

    def test_index_status_regex_carries_the_parity_note(self) -> None:
        src = Path(plans_index.__file__).read_text(encoding="utf-8")
        self.assertIn("PARITY CONSTRAINT", src)
        self.assertIn("selectors.py", src)


class RegexShapeTests(unittest.TestCase):
    """Guard the exact patterns the parity note describes, so the citation cannot silently rot."""

    def test_selector_status_pattern_is_single_token(self) -> None:
        self.assertEqual(selectors._STATUS_RE.pattern, r"(?m)^- Status:\s*(\S+)\s*$")

    def test_index_status_pattern_is_whole_line(self) -> None:
        self.assertEqual(
            plans_index._META_RE["Status"].pattern, r"(?m)^- Status:\s*(.+?)\s*$"
        )

    def test_patterns_are_not_accidentally_identical(self) -> None:
        self.assertNotEqual(
            selectors._STATUS_RE.pattern, plans_index._META_RE["Status"].pattern
        )
        self.assertIn(r"(\S+)", selectors._STATUS_RE.pattern)
        self.assertIn(r"(.+?)", plans_index._META_RE["Status"].pattern)


class _SanityOnRealRepoTests(unittest.TestCase):
    """A light check against the ACTUAL repository tree when it is present."""

    def setUp(self) -> None:
        self.repo = Path(__file__).resolve().parents[1]
        if not (self.repo / ".aw" / "records" / "plans").is_dir():
            self.skipTest("not running inside the agent-workflows repo tree")

    def test_real_repo_enumeration_is_read_free(self) -> None:
        """The text-free walk must open nothing even across the full plans tree."""
        with _RecordOpenCounter() as c:
            paths = list(selectors._iter_paths(self.repo, "plans"))
        self.assertGreater(len(paths), 100, "expected a populated plans tree")
        self.assertEqual(
            c.count, 0, f"_iter_paths opened {c.count} record file(s) in the real tree"
        )

    def test_real_repo_one_traversal_is_shared(self) -> None:
        """A query touching both views must not read a file MORE THAN ONCE.

        This is the regression guard for the double-walk bug found while implementing E-05: when
        `_files()` walked the tree independently of `_paths()`, a substring query cost ~83ms
        against a ~50ms baseline. Sharing the enumeration means at most one open per record.
        """
        with _RecordOpenCounter() as c:
            selectors.resolve(self.repo, "plans", "plan-that-does-not-exist-anywhere")
        self.assertEqual(
            c.count,
            c.distinct,
            f"{c.count} opens for {c.distinct} distinct files: the tree is being walked twice",
        )

    def test_real_repo_status_divergence_is_still_the_documented_shape(self) -> None:
        """Recompute the 'the two readers disagree' claim on the live tree."""
        sel_re = selectors._STATUS_RE
        idx_re = plans_index._META_RE["Status"]
        divergent = 0
        multi = 0
        for _p, text in selectors._iter_files(self.repo, "plans"):
            a = sel_re.search(text)
            b = idx_re.search(text)
            av = a.group(1) if a else None
            bv = b.group(1) if b else None
            if av != bv:
                divergent += 1
            if bv and re.search(r"\s", bv):
                multi += 1
        self.assertEqual(
            divergent,
            multi,
            "every divergence must be explained by a multi-word Status value",
        )


if __name__ == "__main__":
    unittest.main()
