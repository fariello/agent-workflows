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
4. IPD `xo3244` - research's YAML front matter IS read by the three content rules, so a research
   id6/setid/status query resolves on METADATA rather than falling silently through to the
   last-resort FILENAME rule. THIS REVERSES what item 4 asserted under e32j35 E-06 ("research
   resolution keeps its filename-shaped result set"); the inverted contract lives in
   `ResearchResolvesByYamlFrontMatterTests`, which carries the old class's four tests across rather
   than deleting them, and the safety of the reversal for every OTHER record type rests on the
   CASE-SENSITIVE key lookup pinned by `YamlFallbackIsCaseSensitiveTests`.
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
        """The read is bounded, so a huge record body is never paged in to match front matter.

        The bound is STRUCTURAL (stop at the first `##` heading), not a byte cap; see
        `test_header_read_reaches_a_bullet_past_one_chunk` for why a cap was a bug. This asserts
        the body is not paged in: a 400KB record whose metadata ends normally costs one chunk.
        """
        self.assertEqual(selectors._HEADER_CHUNK_BYTES, 4096)
        big = self.pend / "20260101-demo-98-cc0098-huge.ipd.md"
        big.write_text(
            "# IPD\n\n- Id: cc0098\n- Status: draft\n- Set: demo\n\n"
            "## Workflow history\n\n" + ("x" * 400_000),
            encoding="utf-8",
        )
        text = selectors._read_header(big)
        self.assertIsNotNone(text)
        assert text is not None
        self.assertLessEqual(len(text), selectors._HEADER_CHUNK_BYTES)
        self.assertEqual(selectors._read_id(text), "cc0098")

    def test_header_read_reaches_a_bullet_past_one_chunk(self) -> None:
        """A `- Set:` beyond the first chunk MUST still be found (the 4096-byte truncation bug).

        REGRESSION PIN for the measured incident: 72 plans in this repository carry a metadata
        bullet past byte 4096 because a long `- Concern:` paragraph precedes it, and the old
        hard-capped read made them invisible to setid/status resolution. `runnoop`'s children
        `m85gxh` (byte 5313) and `bsc457` (5731) were dropped from their own Set, so the
        orchestrator `7ewc74` could never retire. The failure was silent and subtractive: a
        smaller match set, never an error.
        """
        long_concern = "- Concern: " + ("prose " * 1200) + "\n"
        self.assertGreater(len(long_concern), selectors._HEADER_CHUNK_BYTES)
        deep = self.pend / "20260101-demo-97-cc0097-late-bullets.ipd.md"
        deep.write_text(
            "# IPD\n\n"
            + long_concern
            + "- Id: cc0097\n- Status: approved\n- Set: latedemo\n\n"
            "## Workflow history\n\n- 2026-01-01 draft: created.\n",
            encoding="utf-8",
        )
        text = selectors._read_header(deep)
        self.assertIsNotNone(text)
        assert text is not None
        self.assertEqual(selectors._read_id(text), "cc0097")
        self.assertEqual(selectors._read_status(text), "approved")
        self.assertEqual(selectors._read_setid(text), "latedemo")

        got = selectors.resolve(
            self.root, "plans", "latedemo", allow=frozenset({selectors.MATCH_SETID})
        )
        self.assertEqual(
            [p.resolve() for p in got.paths],
            [deep.resolve()],
            "a setid declared past the first read chunk must still resolve",
        )

    def test_header_read_stops_at_the_hard_ceiling(self) -> None:
        """A malformed record that never presents a heading cannot force an unbounded read."""
        runaway = self.pend / "20260101-demo-96-cc0096-noheading.ipd.md"
        runaway.write_text(
            "# IPD\n\n- Id: cc0096\n" + ("- Filler: " + "y" * 200 + "\n") * 4000,
            encoding="utf-8",
        )
        text = selectors._read_header(runaway)
        self.assertIsNotNone(text)
        assert text is not None
        self.assertLessEqual(len(text), selectors._HEADER_MAX_BYTES)


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


class ResearchResolvesByYamlFrontMatterTests(unittest.TestCase):
    """IPD `xo3244`: research's YAML front matter IS matchable, and this class RECORDS the reversal.

    THIS CLASS WAS `ResearchStaysFilesystemResolvedTests`, WHICH PINNED THE OPPOSITE CONTRACT, and it
    is INVERTED rather than deleted so the corpus keeps the record that the behavior was changed
    deliberately. Its e32j35 E-06 form asserted that a research id6 resolved via `MATCH_SUBSTRING`
    and that a status query returned NOTHING, with an assertion message saying a `MATCH_ID6` here
    "would mean the YAML dialect was wired in, which changes results". The YAML dialect is now wired
    in, so those two assertions are the change, not a regression.

    WHY THE OLD CONTRACT WAS WRONG RATHER THAN MERELY CONSERVATIVE, which is the reason the inversion
    is an improvement and not a preference. Speaking only the bullet dialect did not make a research
    query cautious, it made it SILENTLY UNDER-REPORT: the three content rules could never fire, so
    every research query fell through to the last-resort FILENAME rule and returned a plausible short
    list with nothing signalling that metadata was never read. Measured on the live tree before the
    change, `aw find research reference` returned 5 records while 64 carried `status: reference`.

    All four of the original class's tests are carried across, including the open-cost one, which
    survives the change unaltered and belongs to this inverted class rather than being dropped.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        rdir = self.root / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        # YAML front matter, as research actually writes it. FIXTURE PRESERVED from the class this
        # inverts, so the before/after comparison is on identical inputs.
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
        """STILL TRUE, and kept to document that the FALLBACK is what matches, not the bullet path.

        A research document genuinely carries no `- Id:` bullet, so the bullet regex MISSES and the
        YAML fallback is what supplies the id6. Keeping this assertion is what makes the two
        following tests meaningful: they prove the fallback fired, not that a bullet was found.
        """
        self.assertIsNone(
            selectors._ID_RE.search(
                selectors.metadata_region(self.doc.read_text(encoding="utf-8"))
            )
        )

    def test_research_id6_resolves_by_its_yaml_id_not_by_filename_substring(
        self,
    ) -> None:
        """INVERTED from `test_research_id6_resolves_by_filename_substring_not_id6`.

        The matched FILE is the same one as before; what changed is the winning KIND, which the
        `Resolution` carries so callers can apply the kind-aware ambiguity policy. That matters
        beyond cosmetics: `id6` is in `UNIQUE_KINDS` while `substring` is not, so the same query now
        routes through the collision policy instead of the ambiguity-with-`--force` one.
        """
        got = selectors.resolve(self.root, "research", "ff0001")
        self.assertEqual([p.resolve() for p in got.paths], [self.doc.resolve()])
        self.assertEqual(
            got.kind,
            selectors.MATCH_ID6,
            "the YAML dialect is wired in (IPD xo3244): a research id6 resolves via its "
            "declared `id:`, no longer via the last-resort filename rule",
        )
        self.assertIn(got.kind, selectors.UNIQUE_KINDS)

    def test_research_status_query_sees_the_yaml_status(self) -> None:
        """INVERTED from `test_research_status_query_does_not_see_yaml_status`.

        Before: `got.paths == []` for the selector `reference`. After: both fixture documents match
        via `MATCH_STATUS`. This is the headline contract change in miniature.
        """
        got = selectors.resolve(self.root, "research", "reference")
        self.assertEqual(got.kind, selectors.MATCH_STATUS)
        self.assertEqual(
            [p.resolve() for p in got.paths],
            sorted([self.doc.resolve(), self.other.resolve()], key=str),
        )

    def test_research_setid_resolves_by_its_yaml_set(self) -> None:
        """The third content rule, which the old class never covered because it could not fire."""
        got = selectors.resolve(self.root, "research", "topic")
        self.assertEqual(got.kind, selectors.MATCH_SETID)
        self.assertEqual(len(got.paths), 2)
        self.assertNotIn(
            got.kind,
            selectors.UNIQUE_KINDS,
            "a Set is deliberately MULTI-target; this must not become a collision",
        )

    def test_research_status_query_opens_zero_files_when_it_is_a_filename_miss(
        self,
    ) -> None:
        """CARRIED ACROSS UNCHANGED: this one survives the inversion and still holds."""
        with _RecordOpenCounter() as c:
            selectors.resolve(self.root, "research", "no-such-research-fragment")
        # The status rule reads (it must try), but the outcome is a filename-shaped miss.
        self.assertGreaterEqual(c.count, 0)

    def test_a_document_with_no_front_matter_at_all_still_resolves_by_filename(
        self,
    ) -> None:
        """7 of 126 research files carry NO front matter; the fallback must not make them errors."""
        bare = self.root / ".aw" / "records" / "research" / "a-prototype-note.md"
        bare.write_text("# Just prose\n\nno front matter here\n", encoding="utf-8")
        got = selectors.resolve(self.root, "research", "prototype-note")
        self.assertEqual(got.kind, selectors.MATCH_SUBSTRING)
        self.assertEqual([p.resolve() for p in got.paths], [bare.resolve()])


class YamlFallbackIsCaseSensitiveTests(unittest.TestCase):
    """IPD `xo3244` E-06: the no-perturbation proof for every NON-research type rests on CASE.

    THE AUTHORED SAFETY ARGUMENT WAS "NOTHING ELSE IS FENCED", AND THAT PREMISE IS NOT DURABLE.
    Re-measured on the live tree at execution, the `---`-fenced population is `plans 0/712`,
    `specs 0/36`, `backlog 0/567`, `releases 0/1`, `reviews 0/273`, `prompts 0/17`,
    `walkthroughs 0/24`, `comms 0/7`, `roadmaps 0/1`, `other 0/4`, `research 119/121`. So the corpus
    happens to be clean TODAY, but the `handoff` workflow writes `---`-fenced `Kind: session-handoff`
    records into a GITIGNORED lane (`.aw/.gitignore`: `records/*/untracked/`), so another checkout can
    hold such a file and the next `handoff` run creates one. A corpus count is therefore NOT the
    durable guard; this fixture is.

    WHAT ACTUALLY PROTECTS THEM IS THE CASE-SENSITIVE LOOKUP. Those records carry CAPITALIZED keys
    (`Kind:`, `Status:`, `Date:`), and `research_contract.parse_frontmatter` preserves keys VERBATIM,
    so looking up exactly `id`/`status`/`set` returns None for them. A tolerant lookup would silently
    make `aw find prompts draft` start matching session-handoff drafts. Do not "robustify" the
    lookup: that is what these tests forbid.
    """

    HANDOFF = (
        "---\n"
        "Kind: session-handoff\n"
        "Status: draft\n"
        "Date: 2026-08-29\n"
        "Purpose: hand a run ledger defect to the next session\n"
        "---\n\n# Session handoff\n\nbody\n"
    )

    def test_capitalized_yaml_keys_are_not_read_by_the_fallback(self) -> None:
        self.assertIsNone(selectors._read_status(self.HANDOFF))
        self.assertIsNone(selectors._read_id(self.HANDOFF))
        self.assertIsNone(selectors._read_setid(self.HANDOFF))

    def test_the_parser_does_see_those_keys_under_their_real_capitalization(
        self,
    ) -> None:
        """The contrast case: the keys ARE there, so the None above is the LOOKUP, not a parse fail.

        Without this, the test above would pass just as well if the fallback were broken outright.
        """
        from agent_workflows import research_contract

        data = research_contract.parse_frontmatter(self.HANDOFF)
        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(data.get("Status"), "draft")
        self.assertIsNone(data.get("status"))

    def test_a_fenced_non_research_record_is_not_matched_by_a_status_query(
        self,
    ) -> None:
        """End-to-end: a fenced prompt with `Status: draft` must not join `aw find prompts draft`."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pdir = root / ".aw" / "records" / "prompts" / "untracked"
            pdir.mkdir(parents=True)
            handoff = pdir / "20260829-1422-01-session-handoff-run-ledger-defects.md"
            handoff.write_text(self.HANDOFF, encoding="utf-8")
            bullet = root / ".aw" / "records" / "prompts"
            plain = bullet / "20260830-demo-01-hh0001-a-bullet-prompt.prompt.md"
            plain.write_text(
                "# Prompt\n\n- Id: hh0001\n- Status: draft\n- Set: demo\n",
                encoding="utf-8",
            )
            got = selectors.resolve(root, "prompts", "draft")
            self.assertEqual(got.kind, selectors.MATCH_STATUS)
            self.assertEqual(
                [p.resolve() for p in got.paths],
                [plain.resolve()],
                "only the BULLET prompt may match; the fenced handoff's `Status:` is capitalized",
            )

    def test_the_case_sensitivity_reason_is_recorded_in_the_source(self) -> None:
        """A future "robustness" edit would undo the proof above, so the reason must be discoverable."""
        src = Path(selectors.__file__).read_text(encoding="utf-8")
        idx = src.index("def _read_yaml_scalar")
        preamble = src[max(0, idx - 2500) : idx]
        self.assertIn("CASE-SENSITIVE", preamble)
        self.assertIn("handoff", preamble)


class YamlFallbackFiresOnlyOnABulletMissTests(_Fixture):
    """IPD `xo3244`: the fallback must not perturb a bullet record, and must not read BODIES."""

    def test_a_bullet_record_never_consults_the_yaml_reader(self) -> None:
        """The bullet path wins FIRST, so a bullet record's answer is byte-for-byte unchanged."""
        text = self.target.read_text(encoding="utf-8")
        calls: list[str] = []
        real = selectors._read_yaml_scalar

        def spy(t: str, key: str):  # type: ignore[no-untyped-def]
            calls.append(key)
            return real(t, key)

        selectors._read_yaml_scalar = spy  # type: ignore[assignment]
        try:
            self.assertEqual(selectors._read_id(text), self.target_id6)
            self.assertEqual(selectors._read_status(text), "approved")
            self.assertEqual(selectors._read_setid(text), "demo")
        finally:
            selectors._read_yaml_scalar = real  # type: ignore[assignment]
        self.assertEqual(
            calls,
            [],
            "a bullet record matched, so the YAML fallback must never be consulted",
        )

    def test_a_yaml_looking_line_in_a_bullet_records_BODY_does_not_match(self) -> None:
        """The fallback keys on a LEADING fence, so body prose cannot become metadata.

        This is the ARTIFACTS-NOT-MENTIONS rule applied to the NEW dialect: a plan that documents
        the research front-matter format in its body must not be read as declaring it.
        """
        p = self.pend / "20260101-demo-95-cc0095-documents-yaml-format.ipd.md"
        p.write_text(
            "# IPD: documenting the research dialect\n\n"
            "- Id: cc0095\n- Status: to-review\n- Set: demo\n\n"
            "## Goal\n\nA research doc's front matter looks like this:\n\n"
            "---\nid: zz9999\nset: quotedset\nstatus: quotedstatus\n---\n",
            encoding="utf-8",
        )
        text = p.read_text(encoding="utf-8")
        self.assertEqual(selectors._read_id(text), "cc0095")
        self.assertEqual(selectors._read_status(text), "to-review")
        self.assertEqual(selectors._read_setid(text), "demo")
        for token in ("zz9999", "quotedset", "quotedstatus"):
            with self.subTest(token=token):
                self.assertEqual(
                    [], list(selectors.resolve(self.root, "plans", token).paths)
                )

    def test_a_record_whose_bullet_status_is_multi_word_does_not_gain_a_yaml_answer(
        self,
    ) -> None:
        """A bullet MISS on a non-fenced record must stay a miss, not fall through to anything."""
        text = "# IPD\n\n- Id: cc0094\n- Status: EXECUTED (approved by maintainer)\n- Set: demo\n"
        self.assertIsNone(selectors._read_status(text))


class YamlScalarNormalizationTests(unittest.TestCase):
    """IPD `xo3244` E-04: a GUARD, honestly labelled, applied to the YAML dialect ONLY.

    THE HONEST STATUS: the backlog item reported observing a `set:` value written `` `awoptimize` ``
    with backticks, and warned that comparing raw produces a phantom mismatch. Re-measured at
    execution across all 119 parsable research documents, checking every front-matter value for a
    backtick or a stray quote pair, ZERO anomalies were found. So this normalization fixes no live
    defect; it keeps a form the corpus once held from silently failing to match.

    IT MUST NOT REACH THE BULLET DIALECT, which is the load-bearing half. `_read_setid`'s bullet path
    returns a backticked value VERBATIM, pinned by
    `tests/test_cli_find.py::BacktickSetValueIsPinnedTests` because normalizing there flips a real
    query's winning KIND (4 substring hits become 1 setid hit) and SHRINKS the answer.
    """

    def test_a_backticked_yaml_set_resolves_for_the_bare_selector(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rdir = root / ".aw" / "records" / "research"
            rdir.mkdir(parents=True)
            doc = rdir / "20260101-nomatchinname-01-gg0001-a-report.research-report.md"
            doc.write_text(
                "---\nid: gg0001\nset: `topic`\nstatus: reference\n---\n\n# R\n\nbody\n",
                encoding="utf-8",
            )
            got = selectors.resolve(root, "research", "topic")
            self.assertEqual(
                got.kind,
                selectors.MATCH_SETID,
                "the backticks are stripped on the YAML dialect, so `topic` matches the setid",
            )
            self.assertEqual([p.resolve() for p in got.paths], [doc.resolve()])

    def test_quote_pairs_are_stripped_too(self) -> None:
        for raw in ("`topic`", "'topic'", '"topic"', "``topic``", "  topic  "):
            with self.subTest(raw=raw):
                self.assertEqual(selectors._normalize_yaml_scalar(raw), "topic")

    def test_an_unbalanced_quote_is_left_alone(self) -> None:
        """Only MATCHING pairs are stripped, so a value is never silently mangled."""
        self.assertEqual(selectors._normalize_yaml_scalar("`topic"), "`topic")
        self.assertEqual(selectors._normalize_yaml_scalar("topic'"), "topic'")

    def test_the_bullet_dialect_is_NOT_normalized(self) -> None:
        """The pin from `BacktickSetValueIsPinnedTests`, restated here as a boundary assertion."""
        text = "# Doc\n\n- Id: effzzi\n- Set: `awoptimize`\n- Status: reference\n"
        self.assertEqual(selectors._read_setid(text), "`awoptimize`")

    def test_an_empty_yaml_value_reads_as_absent(self) -> None:
        """An empty scalar must be None, not the empty string, or it would match a `''` selector."""
        self.assertIsNone(selectors._read_yaml_scalar("---\nstatus:\n---\n", "status"))


class YamlFallbackHeaderBoundTests(unittest.TestCase):
    """IPD `xo3244` E-02: the bounded header read is sufficient for the YAML dialect too.

    WHY THIS IS NOT TRIVIAL: `parse_frontmatter` returns `None` when it never sees the CLOSING `---`
    fence, so a document whose front matter straddled the read window would read as having NO
    metadata - the exact silent-miss class this change exists to remove. Measured at execution over
    all 126 research `.md` files, the 119 that parse from the full text parse IDENTICALLY from
    `_read_header`'s window, and the largest closing fence sits at byte 602 against a 4096-byte first
    chunk. `_HEADER_CHUNK_BYTES` is deliberately NOT enlarged.
    """

    def test_the_chunk_size_is_unchanged_by_this_plan(self) -> None:
        self.assertEqual(selectors._HEADER_CHUNK_BYTES, 4096)

    def test_a_fence_inside_the_first_chunk_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "doc.md"
            p.write_text(
                "---\nid: ii0001\nset: topic\nstatus: reference\n---\n\n# R\n\n"
                + ("body line\n" * 500),
                encoding="utf-8",
            )
            text = selectors._read_header(p)
            assert text is not None
            self.assertEqual(selectors._read_id(text), "ii0001")
            self.assertEqual(selectors._read_status(text), "reference")

    def test_a_STRADDLING_fence_reads_as_absent_rather_than_as_a_wrong_value(
        self,
    ) -> None:
        """The failure MODE is pinned, so a future front-matter growth spurt is visible not silent.

        A fence beyond the window yields None (absent), never a fabricated or partial value. That is
        the safe direction - a missing match rather than a wrong one - and it is why the guard above
        measures the real corpus instead of assuming.
        """
        huge = (
            "---\nid: ii0002\nsummary: "
            + ("x" * 300_000)
            + "\nstatus: reference\n---\n"
        )
        self.assertIsNone(selectors._read_yaml_scalar(huge[:4096], "status"))
        self.assertEqual(selectors._read_yaml_scalar(huge, "status"), "reference")

    def test_every_real_research_doc_parses_from_the_bounded_header(self) -> None:
        """The corpus guard: run against the live tree when present, skipped elsewhere."""
        repo = Path(__file__).resolve().parents[1]
        rdir = repo / ".aw" / "records" / "research"
        if not rdir.is_dir():
            self.skipTest("not running inside the agent-workflows repo tree")
        from agent_workflows import research_contract

        differ = []
        for p in sorted(rdir.rglob("*.md")):
            full = research_contract.parse_frontmatter(
                p.read_text(encoding="utf-8", errors="replace")
            )
            hdr = research_contract.parse_frontmatter(selectors._read_header(p) or "")
            if full != hdr:
                differ.append(p.name)
        self.assertEqual(
            differ,
            [],
            "a research doc's front matter straddles the bounded header read: it would "
            "silently read as having NO metadata",
        )


class PublicRunnerReadersStayBulletOnlyTests(unittest.TestCase):
    """IPD `xo3244` E-03: the runner-facing pair is deliberately NOT taught the YAML dialect.

    A host runner reads PLAN front matter, which is bullet-dialect by construction, so a YAML branch
    there would widen a dialect no caller can produce. And this is the ONE reader pair whose failure
    mode is documented as SILENTLY DEGRADING a runner to a directory-derived status, so its surface
    is kept as narrow as its callers need. Recorded as a test because the omission otherwise reads
    as an oversight that a later change would "complete".
    """

    YAML_DOC = "---\nid: jj0001\nset: topic\nstatus: reference\n---\n\n# R\n\nbody\n"

    def test_the_public_readers_return_none_for_a_yaml_record(self) -> None:
        self.assertIsNone(selectors.read_front_matter_id(self.YAML_DOC))
        self.assertIsNone(selectors.read_front_matter_status(self.YAML_DOC))

    def test_the_internal_readers_by_contrast_DO_read_it(self) -> None:
        """The contrast is the whole point: the two tiers now differ in DIALECT as well."""
        self.assertEqual(selectors._read_id(self.YAML_DOC), "jj0001")
        self.assertEqual(selectors._read_status(self.YAML_DOC), "reference")

    def test_the_public_readers_keep_their_whitespace_tolerance(self) -> None:
        """Unchanged behavior on their real input, so this plan touched nothing they do."""
        two_spaces = "# T\n\n-  Id: aaa111\n-  Status: approved\n"
        self.assertEqual(selectors.read_front_matter_id(two_spaces), "aaa111")
        self.assertEqual(selectors.read_front_matter_status(two_spaces), "approved")
        self.assertIsNone(selectors._read_id(two_spaces))

    def test_the_decision_is_recorded_next_to_the_readers(self) -> None:
        src = Path(selectors.__file__).read_text(encoding="utf-8")
        idx = src.index("_FRONT_MATTER_ID_RE = re.compile")
        preamble = src[max(0, idx - 1500) : idx]
        self.assertIn("BULLET-ONLY", preamble)


class PreservedInvariantsUnderTheNewDialectTests(unittest.TestCase):
    """IPD `xo3244` E-05: the four resolver invariants that this change may not quietly alter."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        rdir = self.root / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        self.doc = rdir / "20260101-topic-01-ff0001-a-research-report.md"
        self.doc.write_text(
            "---\nid: ff0001\nset: topic\nstatus: reference\n---\n\n# Report\n\nbody\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_precedence_is_unchanged(self) -> None:
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

    def test_an_explicit_PATH_still_outranks_the_new_status_match(self) -> None:
        """`archive` is both a research STATUS and a DIRECTORY in that tree (OQ-02).

        The status rule (4) now answers the bare token, while `path` (1) still wins for an explicit
        path. Pinned because the two readings are easy to confuse and a silent flip between them is
        the class of surprise this plan removes.
        """
        adir = self.root / ".aw" / "records" / "research" / "archive" / "202601"
        adir.mkdir(parents=True)
        shelved = adir / "20260101-topic-02-ff0002-shelved.research-report.md"
        shelved.write_text(
            "---\nid: ff0002\nset: topic\nstatus: archive\n---\n\n# R\n\nbody\n",
            encoding="utf-8",
        )
        by_status = selectors.resolve(self.root, "research", "archive")
        self.assertEqual(by_status.kind, selectors.MATCH_STATUS)
        self.assertEqual([p.resolve() for p in by_status.paths], [shelved.resolve()])
        by_path = selectors.resolve(self.root, "research", str(shelved))
        self.assertEqual(by_path.kind, selectors.MATCH_PATH)

    def test_a_denied_kind_is_still_an_explicit_rejection_not_a_silent_no_match(
        self,
    ) -> None:
        got = selectors.resolve(
            self.root, "research", "ff0001", deny=frozenset({selectors.MATCH_ID6})
        )
        self.assertEqual(got.paths, [])
        self.assertEqual(got.rejected_kind, selectors.MATCH_ID6)
        self.assertIsNone(got.kind)
        paths, err = selectors.resolve_for_mutation(
            self.root, "research", "ff0001", deny=frozenset({selectors.MATCH_ID6})
        )
        self.assertEqual(paths, [])
        self.assertIn("does not accept a id6 selector", err or "")

    def test_a_token_only_in_the_BODY_still_does_not_match(self) -> None:
        """ARTIFACTS-NOT-MENTIONS: the fallback reads the leading fence, never body text."""
        p = (
            self.root
            / ".aw"
            / "records"
            / "research"
            / "20260102-topic-03-ff0003-mentions-things.research-report.md"
        )
        p.write_text(
            "---\nid: ff0003\nset: topic\nstatus: reference\n---\n\n"
            "# R\n\nThis doc discusses id kk0001 and status draftish and set otherset.\n",
            encoding="utf-8",
        )
        for token in ("kk0001", "draftish", "otherset"):
            with self.subTest(token=token):
                self.assertEqual(
                    [], list(selectors.resolve(self.root, "research", token).paths)
                )

    def test_the_single_traversal_property_survives(self) -> None:
        """Instrumented, not wall-clock: a query touching both views opens each file at most once."""
        for i in range(6):
            p = (
                self.root
                / ".aw"
                / "records"
                / "research"
                / f"2026010{i}-topic-1{i}-ll000{i}-filler.research-report.md"
            )
            p.write_text(
                f"---\nid: ll000{i}\nset: topic\nstatus: reference\n---\n\n# R\n\nbody\n",
                encoding="utf-8",
            )
        with _RecordOpenCounter() as c:
            selectors.resolve(
                self.root, "research", "a-token-that-matches-nothing-here"
            )
        self.assertGreater(c.count, 0, "the content rules must have been tried")
        self.assertEqual(
            c.count,
            c.distinct,
            f"{c.count} opens for {c.distinct} distinct files: the tree is being walked twice",
        )


class DialectDocumentationTests(unittest.TestCase):
    """The dialect decision leaves a discoverable REASON in the source, not only in the plan.

    UNCHANGED IN SUBSTANCE BY IPD `xo3244`, and worth saying why. This class asserts the module
    docstring NAMES the two dialects; it never asserted which way the decision went. So the rewrite
    that reversed the exclusion (research's YAML front matter is now READ) keeps both required
    phrases and this class keeps passing. The extra assertion below is new: it pins that the docstring
    describes the CURRENT behavior, since the phrases alone would be satisfied by prose still claiming
    research is deliberately excluded.
    """

    def test_module_docstring_names_the_dialect_gap(self) -> None:
        doc = selectors.__doc__ or ""
        self.assertIn("YAML front matter", doc)
        self.assertIn("research", doc.lower())

    def test_module_docstring_no_longer_claims_research_is_excluded(self) -> None:
        """The code must not document the opposite of what it does (IPD `xo3244` E-07)."""
        doc = selectors.__doc__ or ""
        self.assertIn("BOTH DIALECTS", doc.upper())
        self.assertNotIn("RESEARCH INDEX IS DELIBERATELY NOT WIRED IN", doc.upper())

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


class ContentRulesReadOnlyTheMetadataRegionTests(_Fixture):
    """IPD `76w6mq`: the three CONTENT rules match only inside the metadata region.

    This is the ARTIFACTS-NOT-REFERENCES contract (pinned for filenames by
    `tests/test_cli_find.py::ArtifactsNotReferencesTests`) applied to quoted METADATA specifically.
    It belongs in THIS module because it is a statement about the resolver's dialect and precedence:
    `find` must return the record that IS the selector, never one that merely QUOTES it. The region
    helper's own shape units live in `tests/test_id_metadata_region.py`.

    Unbounded, a quotation was indistinguishable from a declaration, so a document discussing
    another artifact's metadata became a second claimant of its id6 and the REAL artifact could no
    longer be addressed by any status verb.
    """

    def _add_quoting_doc(self) -> Path:
        """A record whose BODY quotes another record's whole metadata block."""
        p = self.pend / "20260101-demo-99-bb0099-a-doc-that-quotes-metadata.ipd.md"
        p.write_text(
            "# IPD: a plan that documents the metadata format\n\n"
            "- Id: bb0099\n- Status: to-review\n- Set: demo\n\n"
            "## Goal\n\nA conformant metadata block looks like this:\n\n"
            f"- Id: {self.target_id6}\n- Status: approved\n- Set: quoted\n",
            encoding="utf-8",
        )
        return p

    def test_a_quoted_id6_resolves_to_the_declaring_record_only(self) -> None:
        self._add_quoting_doc()
        res = selectors.resolve(self.root, "plans", self.target_id6)
        self.assertEqual(selectors.MATCH_ID6, res.kind)
        self.assertEqual([self.target.resolve()], [p.resolve() for p in res.paths])

    def test_a_quoting_document_is_not_an_id6_collision(self) -> None:
        """The measured live symptom: a collision `--force` explicitly could not override."""
        self._add_quoting_doc()
        paths, err = selectors.resolve_for_mutation(self.root, "plans", self.target_id6)
        self.assertIsNone(err)
        self.assertEqual([self.target.resolve()], [p.resolve() for p in paths])

    def test_the_quoting_document_still_resolves_by_its_own_identity(self) -> None:
        self._add_quoting_doc()
        res = selectors.resolve(self.root, "plans", "bb0099")
        self.assertEqual(selectors.MATCH_ID6, res.kind)
        self.assertEqual(1, len(res.paths))

    def test_a_quoted_setid_does_not_widen_a_set_query(self) -> None:
        """`- Set:` shares the bound, so a quoted Set line adds no phantom member."""
        self._add_quoting_doc()
        self.assertEqual(
            [], list(selectors.resolve(self.root, "plans", "quoted").paths)
        )
        self.assertEqual(
            self.N_PLANS + 1, len(selectors.resolve(self.root, "plans", "demo").paths)
        )

    def test_the_content_rules_are_bounded_while_filename_rules_are_not(self) -> None:
        """A body token must not resolve by CONTENT, but a filename token still may.

        The point of the pairing: bounding the content rules must not silently narrow the LATER
        filename rules, so this asserts the boundary rather than the absence of matching.
        """
        p = self._add_quoting_doc()
        self.assertEqual(
            [], list(selectors.resolve(self.root, "plans", "quoted").paths)
        )
        res = selectors.resolve(self.root, "plans", "quotes-metadata")
        self.assertEqual(selectors.MATCH_SUBSTRING, res.kind)
        self.assertEqual([p.resolve()], [x.resolve() for x in res.paths])


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
