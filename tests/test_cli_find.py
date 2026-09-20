"""Tests for aw find and token-efficient bare path discovery (--paths / -p).

Plan v8xdz4 (findpaths-01).

ALSO PINS THE `aw find` MATCHING CONTRACT (plan 826o13, findtier Order 01, E-01). Those tests
assert what the resolver ALREADY does; they are characterization pins, not a change. If one goes
red, the test is wrong or something changed underneath it - do NOT edit `selectors.py` to make one
pass, which would convert a pin into a silent contract change.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli, selectors
from agent_workflows.term import Term

_REPO_ROOT = Path(__file__).resolve().parents[1]


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


class TestCliFindPaths(unittest.TestCase):
    def test_find_with_paths_flag_emits_bare_relative_paths(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/plans/"))
            self.assertTrue(line.endswith(".ipd.md"))
            self.assertNotIn(" ", line)  # No column formatting or status text

    def test_find_with_long_paths_flag(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "--paths"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/plans/"))

    def test_find_with_agent_flag_emits_bare_relative_paths(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/plans/"))
            self.assertTrue(line.endswith(".ipd.md"))
            self.assertNotIn("{", line)  # Zero JSON overhead

    def test_find_all_types_with_paths_flag(self):
        rc, out, err = _run_cli(["find", "v8xdz4", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertTrue(line.startswith(".aw/records/"))

    def test_find_nonexistent_with_paths_exits_nonzero(self):
        rc, out, err = _run_cli(
            ["find", "plans", "definitely_nonexistent_id6_9999", "-p"]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip(), "")

    def test_find_json_includes_paths_and_matches(self):
        rc, out, err = _run_cli(["find", "plans", "v8xdz4", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data.get("command"), "find")
        self.assertIn("paths", data.get("data", {}))
        self.assertIn("matches", data.get("data", {}))
        paths = data["data"]["paths"]
        self.assertTrue(len(paths) >= 1)
        self.assertTrue(any("v8xdz4" in p for p in paths))

    def test_highlight_filename_matches_helper(self):
        term_color = Term(color=True)
        term_plain = Term(color=False)
        path = ".aw/records/plans/pending/20260904-runbypass-01-ki6tom-remove.ipd.md"

        # Plain mode returns identical string
        self.assertEqual(
            cli._highlight_filename_matches(path, ["ki6tom"], term_plain),
            path,
        )

        # Empty tokens returns identical string
        self.assertEqual(
            cli._highlight_filename_matches(path, [], term_color),
            path,
        )

        # Color mode highlights match in filename in bold orange-yellow (214)
        highlighted = cli._highlight_filename_matches(path, ["ki6tom"], term_color)
        expected_match = "\033[1;38;5;214mki6tom\033[0m"
        self.assertIn(expected_match, highlighted)
        self.assertTrue(highlighted.startswith(".aw/records/plans/pending/"))
        # Directory portion must not contain the escape code
        dir_part = highlighted[: len(".aw/records/plans/pending/")]
        self.assertEqual(dir_part, ".aw/records/plans/pending/")

    def test_find_highlights_matching_portions_in_color_mode(self):
        old_force = os.environ.get("FORCE_COLOR")
        try:
            os.environ["FORCE_COLOR"] = "1"
            rc, out, err = _run_cli(["find", "ki6tom", "25kzda"])
            self.assertEqual(rc, 0)
            # ki6tom and 25kzda should appear highlighted in bold orange-yellow (214)
            self.assertIn("\033[1;38;5;214mki6tom\033[0m", out)
            self.assertIn("\033[1;38;5;214m25kzda\033[0m", out)
        finally:
            if old_force is None:
                os.environ.pop("FORCE_COLOR", None)
            else:
                os.environ["FORCE_COLOR"] = old_force

    def test_find_no_color_flag_suppresses_color(self):
        rc, out, err = _run_cli(["find", "--no-color", "ki6tom", "25kzda"])
        self.assertEqual(rc, 0)
        self.assertNotIn("\033[", out)
        self.assertIn("ki6tom", out)
        self.assertIn("25kzda", out)


class _SyntheticCorpus(unittest.TestCase):
    """A small plans+research tree reproducing the SHAPES measured on the real repo.

    WHY SYNTHETIC AND NOT ONLY THE REAL TREE, which is a correctness point rather than a
    convenience one. The real corpus is a MOVING TARGET, and a pin written against its counts
    fails for reasons that have nothing to do with the contract: plan 826o13 recorded
    `aw find plans wtiso` returning THREE plans, and it returns EIGHT at the time these tests
    were written, because commit `ecdd348f` fixed a truncated header read (a `- Set:` bullet past
    byte 4096 was invisible, so five members were silently dropped from their own Set). The
    CONTRACT never changed; only the corpus-visible answer did, and the newer answer is the
    correct one. So the tight assertions live here, where the fixture is fixed, and the real tree
    carries PROPERTY assertions that survive the corpus growing (see `RealRepoContractTests`).
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        self.research = self.root / ".aw" / "records" / "research"
        self.research.mkdir(parents=True)

        def plan(
            name: str,
            *,
            id6: str,
            setid: str,
            status: str = "approved",
            body: str = "",
        ) -> Path:
            p = self.plans / name
            p.write_text(
                f"# IPD: {name}\n\n- Id: {id6}\n- Status: {status}\n- Set: {setid}\n"
                f"\n## Goal\n\n{body}\n",
                encoding="utf-8",
            )
            return p

        # Three members of Set `wtiso`, mirroring the real Set.
        self.members = [
            plan(
                "20260828-wtiso-01-8zgybk-phase-0-freeze-state.ipd.md",
                id6="8zgybk",
                setid="wtiso",
            ),
            plan(
                "20260828-wtiso-02-qcqhj7-phase-1-stop-the-deadlock.ipd.md",
                id6="qcqhj7",
                setid="wtiso",
            ),
            plan(
                "20260828-wtiso-07-1o4eif-phase-6-optional-sandbox.ipd.md",
                id6="1o4eif",
                setid="wtiso",
            ),
        ]
        # DIFFERENT Sets whose names merely CONTAIN `wtiso`. A naive `find -iname '*wtiso*'`
        # returns these; `aw find` must not.
        self.land = plan(
            "20260829-wtisoland-01-6knsrx-land-the-six-lane-branches.ipd.md",
            id6="6knsrx",
            setid="wtisoland",
        )
        self.debt = plan(
            "20260905-wtisodebt-01-ol8iyx-retirement-debt.ipd.md",
            id6="ol8iyx",
            setid="wtisodebt",
        )
        # A plan that MENTIONS another record's id6 in its body but is not that record.
        self.mentioner = plan(
            "20260830-other-01-zz0001-a-plan-that-cites-things.ipd.md",
            id6="zz0001",
            setid="other",
            body="This plan discusses 8zgybk at length and cites it repeatedly.",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()


class ArtifactsNotReferencesTests(_SyntheticCorpus):
    """E-01: `aw find` returns the ARTIFACTS a selector identifies, never records that MENTION it.

    This is the property a filename-shaped shortcut most endangers, which is why it is pinned
    before any future read-avoidance work touches the resolver: a `find | grep` equivalent cannot
    tell a Set member from a differently-named Set that shares a prefix, nor an artifact from a
    document citing it.
    """

    def test_a_setid_matches_its_members_and_not_a_longer_set_name(self) -> None:
        got = selectors.resolve(self.root, "plans", "wtiso")
        self.assertEqual(got.kind, selectors.MATCH_SETID)
        self.assertEqual(
            sorted(p.name for p in got.paths),
            sorted(m.name for m in self.members),
        )
        names = {p.name for p in got.paths}
        self.assertNotIn(self.land.name, names, "`wtisoland` is a DIFFERENT Set")
        self.assertNotIn(self.debt.name, names, "`wtisodebt` is a DIFFERENT Set")

    def test_the_filename_shortcut_would_get_this_wrong(self) -> None:
        """State the counterexample explicitly, so the contract's value is visible.

        A filename-substring sweep over the same tree returns the two foreign Sets as well. The
        resolver's answer is SMALLER than the filename sweep's on purpose.
        """
        by_filename = sorted(p.name for p in self.plans.iterdir() if "wtiso" in p.name)
        self.assertIn(self.land.name, by_filename)
        self.assertIn(self.debt.name, by_filename)
        resolved = sorted(
            p.name for p in selectors.resolve(self.root, "plans", "wtiso").paths
        )
        self.assertLess(len(resolved), len(by_filename))

    def test_an_id6_matches_the_artifact_that_IS_it_never_one_that_mentions_it(
        self,
    ) -> None:
        got = selectors.resolve(self.root, "plans", "8zgybk")
        self.assertEqual(got.kind, selectors.MATCH_ID6)
        self.assertEqual([p.name for p in got.paths], [self.members[0].name])
        self.assertNotIn(
            self.mentioner.name,
            [p.name for p in got.paths],
            "a plan that CITES 8zgybk is not the artifact 8zgybk",
        )
        self.assertIn(
            "8zgybk",
            self.mentioner.read_text(encoding="utf-8"),
            "fixture guard: the mentioner must really contain the token",
        )


class PerKindSemanticsTests(_SyntheticCorpus):
    """E-01: the per-kind match semantics documented in `selectors.py`'s precedence block.

    `setid` is deliberately MULTI-target; `path`/`id6`/`stem` are UNIQUE_KINDS whose multi-match
    is a DATA BUG rather than an intentional fan-out; `substring` is the explicit last resort.
    These are the rules any future optimization must not blur.
    """

    def test_setid_is_deliberately_multi_target(self) -> None:
        got = selectors.resolve(self.root, "plans", "wtiso")
        self.assertEqual(got.kind, selectors.MATCH_SETID)
        self.assertTrue(got.is_ambiguous, "a Set is a GROUP; >1 path is correct here")
        self.assertNotIn(selectors.MATCH_SETID, selectors.UNIQUE_KINDS)
        # A mutating verb acts on ALL members without --force, because this is not ambiguity.
        paths, err = selectors.resolve_for_mutation(self.root, "plans", "wtiso")
        self.assertIsNone(err)
        self.assertEqual(len(paths), len(self.members))

    def test_id6_and_stem_are_unique_kinds_whose_multi_match_is_a_data_bug(
        self,
    ) -> None:
        self.assertEqual(
            selectors.UNIQUE_KINDS,
            frozenset(
                {selectors.MATCH_PATH, selectors.MATCH_ID6, selectors.MATCH_STEM}
            ),
        )
        # Manufacture an id6 COLLISION: two records declaring the same `- Id:`.
        twin = self.plans / "20260830-other-02-8zgybk-a-colliding-declaration.ipd.md"
        twin.write_text(
            "# IPD\n\n- Id: 8zgybk\n- Status: draft\n- Set: other\n\n## Goal\n\n",
            encoding="utf-8",
        )
        got = selectors.resolve(self.root, "plans", "8zgybk")
        self.assertEqual(got.kind, selectors.MATCH_ID6)
        self.assertEqual(len(got.paths), 2)
        paths, err = selectors.resolve_for_mutation(self.root, "plans", "8zgybk")
        self.assertEqual(paths, [])
        self.assertIsNotNone(err)
        assert err is not None
        self.assertIn("collision", err)
        self.assertIn("not overridable by --force", err)
        # --force must NOT override a data bug.
        paths_forced, err_forced = selectors.resolve_for_mutation(
            self.root, "plans", "8zgybk", force=True
        )
        self.assertEqual(paths_forced, [])
        self.assertIsNotNone(err_forced)

    def test_substring_is_the_explicit_last_resort(self) -> None:
        got = selectors.resolve(self.root, "plans", "phase")
        self.assertEqual(got.kind, selectors.MATCH_SUBSTRING)
        self.assertTrue(got.is_ambiguous)
        # Unlike a setid fan-out, a substring fan-out REFUSES without --force.
        paths, err = selectors.resolve_for_mutation(self.root, "plans", "phase")
        self.assertEqual(paths, [])
        self.assertIsNotNone(err)
        assert err is not None
        self.assertIn("ambiguous", err)
        paths_forced, err_forced = selectors.resolve_for_mutation(
            self.root, "plans", "phase", force=True
        )
        self.assertIsNone(err_forced)
        self.assertGreater(len(paths_forced), 1)

    def test_an_earlier_kind_wins_outright(self) -> None:
        """`setid` outranks `substring`, so a token that is BOTH resolves as the setid.

        This is why the filename rules cannot be answered without reading front matter, and it is
        the mechanism behind the `_read_setid` pin in `BacktickSetValueIsPinnedTests`.
        """
        self.assertLess(
            list(selectors._PRECEDENCE).index(selectors.MATCH_SETID),
            list(selectors._PRECEDENCE).index(selectors.MATCH_SUBSTRING),
        )
        # `wtiso` is a Set id AND a filename fragment of five files here.
        self.assertEqual(
            selectors.resolve(self.root, "plans", "wtiso").kind,
            selectors.MATCH_SETID,
        )


class BacktickSetValueIsPinnedTests(unittest.TestCase):
    """E-04: CHARACTERIZATION of today's `- Set:` quoting behavior. Do NOT "fix" this.

    `_read_setid` returns a backtick-quoted value VERBATIM, so a record whose front matter reads
    `- Set: ``awoptimize``` does NOT match the `setid` rule and is reached by `substring` instead.

    WHY THIS IS PINNED RATHER THAN NORMALIZED, which is the whole point of the test. Stripping the
    backticks would make that record newly match `setid`, and `setid` (precedence 3) OUTRANKS
    `substring` (precedence 6), so the WINNING KIND for the token flips and the answer SHRINKS:
    `aw find research awoptimize` returns FOUR files by substring today and would return ONE by
    setid. That is a MATCHING-BEHAVIOR change, in the same family as the `_STATUS_RE` parity
    constraint documented at `_STATUS_RE`, and it is deliberately NOT made here. Quote
    normalization belongs at plan `3i6rso`'s report-only comparison site, where it changes no
    selector answer.
    """

    def test_read_setid_returns_a_backticked_value_verbatim(self) -> None:
        text = "# Doc\n\n- Id: effzzi\n- Set: `awoptimize`\n- Status: reference\n"
        self.assertEqual(selectors._read_setid(text), "`awoptimize`")
        self.assertNotEqual(
            selectors._read_setid(text),
            "awoptimize",
            "normalizing here would flip a real query from 4 substring hits to 1 setid hit",
        )

    def test_an_unquoted_value_is_read_as_the_bare_setid(self) -> None:
        """The contrast case, so the pin is about QUOTING and not about the reader being broken."""
        text = "# Doc\n\n- Id: effzzi\n- Set: awoptimize\n- Status: reference\n"
        self.assertEqual(selectors._read_setid(text), "awoptimize")

    def test_a_backticked_set_resolves_by_substring_not_setid(self) -> None:
        """End-to-end consequence of the pin, on a fixture rather than on the moving corpus."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rdir = root / ".aw" / "records" / "research"
            rdir.mkdir(parents=True)
            for nn, id6, facet in (
                ("00", "yq6aub", "research-prompt"),
                ("01", "y1eb0q", "research-report"),
                ("02", "f6i3z2", "reference-research"),
                ("03", "effzzi", "roadmap"),
            ):
                (
                    rdir
                    / f"20260821-awoptimize-{nn}-{id6}-optimal-architecture.{facet}.md"
                ).write_text(
                    f"# Doc\n\n- Id: {id6}\n- Set: `awoptimize`\n- Status: reference\n",
                    encoding="utf-8",
                )
            got = selectors.resolve(root, "research", "awoptimize")
            self.assertEqual(
                got.kind,
                selectors.MATCH_SUBSTRING,
                "the backticked `- Set:` must NOT match the setid rule",
            )
            self.assertEqual(len(got.paths), 4)


class RealRepoContractTests(unittest.TestCase):
    """The same contract asserted on the LIVE tree, as PROPERTIES rather than as counts.

    Counts here are a moving target (see `_SyntheticCorpus` for the `wtiso` 3 -> 8 case), so these
    assert what must hold for ANY corpus: every returned record genuinely declares the selector,
    and no record that merely mentions or prefix-shares it is returned.
    """

    def setUp(self) -> None:
        if not (_REPO_ROOT / ".aw" / "records" / "plans").is_dir():
            self.skipTest("not running inside the agent-workflows repo tree")

    def test_a_setid_query_returns_only_genuine_members(self) -> None:
        got = selectors.resolve(_REPO_ROOT, "plans", "wtiso")
        self.assertEqual(got.kind, selectors.MATCH_SETID)
        self.assertGreater(len(got.paths), 0)
        for p in got.paths:
            header = selectors._read_header(p)
            self.assertIsNotNone(header)
            assert header is not None
            self.assertEqual(
                selectors._read_setid(header),
                "wtiso",
                f"{p.name} was returned for the Set `wtiso` but does not declare it",
            )

    def test_a_setid_query_excludes_prefix_sharing_foreign_sets(self) -> None:
        resolved = {
            p.name for p in selectors.resolve(_REPO_ROOT, "plans", "wtiso").paths
        }
        by_filename = {
            p.name
            for p in (_REPO_ROOT / ".aw" / "records" / "plans").rglob("*wtiso*")
            if p.is_file()
        }
        foreign = {n for n in by_filename if "wtisoland" in n or "wtisoptr" in n}
        self.assertTrue(
            foreign, "fixture guard: expected some foreign wtiso* names on disk"
        )
        self.assertEqual(
            resolved & foreign,
            set(),
            "a differently-named Set must never be returned for `wtiso`",
        )
        self.assertLess(
            len(resolved),
            len(by_filename),
            "the resolver's answer must be SMALLER than the filename sweep's",
        )

    def test_an_id6_query_returns_the_declaring_artifact_not_its_citers(self) -> None:
        got = selectors.resolve(_REPO_ROOT, "plans", "y6mfgo")
        self.assertEqual(got.kind, selectors.MATCH_ID6)
        self.assertEqual(len(got.paths), 1, "an id6 is a UNIQUE kind")
        header = selectors._read_header(got.paths[0])
        assert header is not None
        self.assertEqual(selectors._read_id(header), "y6mfgo")
        citers = [
            p
            for p in (_REPO_ROOT / ".aw" / "records" / "plans").rglob("*.ipd.md")
            if p.resolve() != got.paths[0].resolve()
            and "y6mfgo" in p.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertTrue(citers, "fixture guard: expected other plans to cite y6mfgo")
        self.assertEqual(
            {p.resolve() for p in got.paths} & {p.resolve() for p in citers},
            set(),
            "records that merely CITE the id6 must not be returned",
        )

    def test_find_verb_end_to_end_excludes_foreign_sets(self) -> None:
        """The property through the VERB an operator actually runs, not only the resolver."""
        rc, out, _err = _run_cli(["find", "plans", "wtiso", "-p"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
        self.assertTrue(lines)
        for line in lines:
            self.assertNotIn("wtisoland", line)
            self.assertNotIn("wtisoptr", line)
            self.assertNotIn("wtisodebt", line)

    def test_the_parsed_filename_id6_slot_is_not_a_safe_discriminator(self) -> None:
        """F-16: a legacy name PARSES as conformant with a bogus id6 in the id6 slot.

        Pinned because it is a live trap for any future filename-based matching, independent of
        the optimization that was declined: the parsed slot says `assess` while the record's real
        declared Id is `wvlk84`, and `assess` satisfies the id6 shape. Match the WHOLE filename.
        """
        from agent_workflows import artifact_core, artifact_naming

        name = "20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md"
        parsed = artifact_naming.parse_clustered(name)
        self.assertIsNotNone(parsed, "the legacy name parses as clustered-conformant")
        assert parsed is not None
        self.assertEqual(parsed.groupdict()["id6"], "assess")
        self.assertTrue(
            artifact_core.ID6_RE.match("assess"),
            "`assess` satisfies the id6 shape, which is why the slot is unsafe",
        )
        matches = [
            p
            for p in (_REPO_ROOT / ".aw" / "records" / "plans").rglob(name)
            if p.is_file()
        ]
        if not matches:
            self.skipTest("the legacy record is no longer present in this tree")
        header = selectors._read_header(matches[0])
        assert header is not None
        self.assertEqual(
            selectors._read_id(header),
            "wvlk84",
            "the real declared Id differs from the parsed filename slot",
        )
        # And the resolver agrees with the DECLARATION, not with the filename slot.
        got = selectors.resolve(_REPO_ROOT, "plans", "wvlk84")
        self.assertEqual(got.kind, selectors.MATCH_ID6)
        self.assertIn(matches[0].resolve(), [p.resolve() for p in got.paths])


if __name__ == "__main__":
    unittest.main()
