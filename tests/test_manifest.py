"""Tests for agent_workflows.manifest (IPD 20260723-1100-01, CP1).

Schema round-trip, atomic write, normalized-hash determinism, absent-manifest =
fresh-install, and the record/decline mutations. Stdlib unittest only.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: hand a pure function
two texts and assert their hashes are equal or unequal, or put one file on disk and assert which path
the resolver returns.

THE HASH-STABILITY AND HASH-DIFFERS ROWS ARE DELIBERATELY IN ONE TABLE, and that is the single most
important structural decision here. Split into a "same" test and a "differs" test, a `hash_content`
that returned a CONSTANT would pass every stability test, and a `hash_content` that hashed raw bytes
would pass every differs test; each half alone is satisfiable by a broken implementation. Together
they are not, because no single degenerate function can satisfy both directions, and the failure
message says so by name when one direction fails wholesale.

WHAT WAS A TEST PER CASE IS NOW A ROW, AND WHAT WAS A CASE IS NOW A COLUMN: the normalization table
carries a SENSE column (must-match versus must-differ) rather than two classes, and the resolver
table carries a LAYOUT column (which files exist on disk) rather than four one-file tests.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the subject is the SERIALIZED JSON rather than a hash; the assertion is about the
FILESYSTEM after a write (no temp file left behind) rather than a returned value; the claim is an
idempotence pair; or the claim is a persistence round trip through save+load.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import manifest as M

#: The `sense` column of `NORMALIZATION`: does this pair of texts share a hash, or must it not?
SAME = "same-hash"
DIFFERS = "different-hash"


class NormalizationHashTests(unittest.TestCase):
    """What `hash_content` treats as the same content and what it treats as a real change.

    ONE table replaces two tests, and it is the table whose merging buys the most: the old
    `test_hash_is_stable_across_line_endings_and_whitespace` and
    `test_hash_differs_on_real_body_change` were the SAME shape (two texts, one equality assertion)
    differing only in the SENSE of the comparison. Making the sense a COLUMN is what makes the suite
    unsatisfiable by a degenerate hash: a constant-returning `hash_content` passes every `SAME` row
    and fails every `DIFFERS` row, and a raw-bytes hash does the reverse. Neither can pass this
    table, and neither could be caught by either old test alone.

    Why the table beats the two more generally: the normalization is a SINGLE line-oriented pass
    (strip each line, drop empties, drop the front-matter `description:`), so every row is decided by
    the same three rules. The realistic regression is one rule being dropped or widened, which moves
    a legible group of rows: all four cosmetic rows failing together means normalization stopped
    happening at all, while the `description:` row alone means that carve-out went.

    EACH ROW ALSO CHECKS `normalize_for_hash` DIRECTLY, not only the hash, because a hash comparison
    cannot distinguish "normalized to the same thing" from "collided". That upgrade is what lets a
    failure say WHAT the two texts normalized to, which is the information needed to fix it.

    THE CONSEQUENCE IS NOT COSMETIC, which is why the rows are worth this much care: this hash is how
    the installer decides whether a managed file is still OURS (safe to overwrite) or carries a
    USER'S EDIT. A hash that is too sensitive re-prompts on every harmless reformat; a hash that is
    too loose silently overwrites someone's work.
    """

    #: (case, text A, text B, SAME or DIFFERS, why this row exists)
    NORMALIZATION = (
        (
            "CRLF line endings, trailing whitespace, and a reworded description",
            "---\ndescription: x\nagent: build\n---\nRead and execute @x\n",
            "---\r\ndescription: DIFFERENT WORDING\r\nagent: build\r\n---\r\n  Read and execute @x  \r\n\r\n",
            SAME,
            "THE COMPOSITE COSMETIC ROW, the realistic shape of a file round-tripped through another "
            "tool or another OS. All three differences at once is what a real editor produces, and "
            "if this row fails the installer starts treating its OWN files as user-edited",
        ),
        (
            "CRLF alone",
            "---\nagent: build\n---\nR\n",
            "---\r\nagent: build\r\n---\r\nR\r\n",
            SAME,
            "the LINE-ENDING rule isolated. With only the composite row above, a failure could not "
            "be attributed to any one rule; this row is what makes a Windows checkout's diagnosis "
            "unambiguous",
        ),
        (
            "per-line leading and trailing whitespace",
            "---\nagent: build\n---\nR\n",
            "---\n  agent: build  \n---\n   R   \n",
            SAME,
            "the STRIP rule isolated. Note that stripping happens per LINE, so indentation inside a "
            "managed file is cosmetic to this hash, which is a real decision and not an accident",
        ),
        (
            "extra blank lines, including trailing ones",
            "---\nagent: build\n---\nR\nS\n",
            "---\nagent: build\n---\nR\n\n\nS\n\n\n",
            SAME,
            "the DROP-EMPTY-LINES rule isolated, and the row that proves the normalization is "
            "line-oriented rather than a whole-text trim: a blank line in the MIDDLE is dropped too, "
            "not merely at the ends",
        ),
        (
            "a description line present versus absent entirely",
            "---\nagent: build\n---\nR\n",
            "---\ndescription: added later\nagent: build\n---\nR\n",
            SAME,
            "THE `description:` CARVE-OUT, in its harder direction: the line is not merely reworded, "
            "it is ABSENT on one side. Description wording legitimately varies (the installer "
            "rewrites it), so it must not count as content. This row is the one that fails if the "
            "carve-out is removed, and it also subsumes the old "
            "`test_matches_recorded_true_for_our_unchanged_file` claim at the hash layer",
        ),
        (
            "a changed body line",
            "---\nagent: build\n---\nRead and execute @x\n",
            "---\nagent: build\n---\nRead and execute @y\n",
            DIFFERS,
            "THE BASE MUST-DIFFER ROW: a real content change must change the hash, or the installer "
            "silently overwrites a user's edit believing the file is still its own. Every SAME row "
            "above is vacuous while this one is broken, because a constant-returning hash satisfies "
            "all of them",
        ),
        (
            "a changed front-matter field that is NOT description",
            "---\nagent: build\n---\nR\n",
            "---\nagent: plan\n---\nR\n",
            DIFFERS,
            "THE PRECISION OF THE CARVE-OUT: only `description:` is cosmetic. `agent:` selects which "
            "agent runs the command, so a hash that dropped the whole front matter (the obvious "
            "over-broad implementation) would pass the description row and this one is what catches "
            "it",
        ),
        (
            "a body line differing only in case",
            "---\nagent: build\n---\nRead\n",
            "---\nagent: build\n---\nread\n",
            DIFFERS,
            "NORMALIZATION IS NOT CASE FOLDING, asserted because case folding is a tempting addition "
            "for a prose-ish file and would make genuinely different instructions collide. Note the "
            "`description:` detection IS case-insensitive; this row pins that the BODY is not",
        ),
        (
            "an added body line",
            "---\nagent: build\n---\nRead and execute @advise\n",
            "---\nagent: build\n---\nRead and execute @advise\nMY OWN NOTE\n",
            DIFFERS,
            "THE USER-EDIT SHAPE, and what the old `test_matches_recorded_false_for_user_edit` was "
            "really asserting: a human APPENDING a note must be detected. Because empty lines are "
            "dropped, an added line is exactly the minimal edit that must still register",
        ),
    )

    def test_the_hash_ignores_cosmetics_and_nothing_else(self):
        wrong = []
        same_rows = differs_rows = 0
        same_failed = differs_failed = 0
        for case, a, b, sense, why in self.NORMALIZATION:
            na, nb = M.normalize_for_hash(a), M.normalize_for_hash(b)
            ha, hb = M.hash_content(a), M.hash_content(b)
            problems = []
            if sense == SAME:
                same_rows += 1
                if na != nb:
                    problems.append(
                        f"the two texts must NORMALIZE to the same string; they normalized to "
                        f"{na!r} and {nb!r}"
                    )
                if ha != hb:
                    problems.append(
                        f"the two texts must share a hash; got {ha[:12]}... and {hb[:12]}..."
                    )
            else:
                differs_rows += 1
                if na == nb:
                    problems.append(
                        f"the two texts must normalize DIFFERENTLY; both normalized to {na!r}, so "
                        "the normalization is discarding real content"
                    )
                if ha == hb:
                    problems.append(
                        f"the two texts must NOT share a hash; both hashed to {ha[:12]}..."
                    )
            if problems:
                if sense == SAME:
                    same_failed += 1
                else:
                    differs_failed += 1
                wrong.append(
                    f"  {case} [{sense}]:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if differs_failed == differs_rows and differs_rows:
            note = (
                " NOTE: EVERY must-differ row failed while the must-match rows did not, which is the "
                "fingerprint of a `hash_content` that returns a CONSTANT (or of a normalization that "
                "discards the body). That function would pass a stability-only test suite "
                "completely, which is exactly why both directions share this table."
            )
        elif same_failed == same_rows and same_rows:
            note = (
                " NOTE: EVERY must-match row failed while the must-differ rows did not, which is the "
                "fingerprint of a hash over RAW bytes with no normalization at all. That direction "
                "is the one that makes the installer re-prompt about its own files after any "
                "harmless reformat."
            )
        self.assertEqual(
            wrong,
            [],
            f"the content hash was wrong for {len(wrong)} of {len(self.NORMALIZATION)} text pairs "
            f"({same_failed} of {same_rows} must-match, {differs_failed} of {differs_rows} "
            f"must-differ).{note} ONE line-oriented pass decides every row (strip each line, drop "
            "empty lines, drop the front-matter `description:`), so read the grouping: the cosmetic "
            "rows failing together means normalization stopped running; the two `description:` rows "
            "disagreeing means that carve-out was widened to the whole front matter. FIX: this hash "
            "is how the installer decides whether a managed file is still OURS or carries a USER'S "
            "EDIT, so a hash that is too LOOSE silently overwrites someone's work, and one that is "
            f"too STRICT re-prompts on every reformat.\n" + "\n".join(wrong),
        )

    def test_normalize_is_idempotent(self):
        """Kept separate: an idempotence claim, so the second input is the first OUTPUT.

        No row can state this, because a row's inputs are fixed in the table while this one feeds the
        function its own result. Also pins that the `description:` line is gone after one pass, which
        is what makes the second pass a fixed point rather than a coincidence.
        """
        raw = "  a \r\n\r\n description: drop me \n b \n"
        once = M.normalize_for_hash(raw)
        self.assertEqual(M.normalize_for_hash(once), once)
        self.assertNotIn("description:", once)

    def test_matches_the_engine_customization_normalization(self):
        """Kept separate: the claim is that TWO functions agree, not what either returns.

        M13: the manifest normalization must be the SAME one the engine uses for its drift
        comparison, so a freshly written file matches its own recorded hash. A row asserting a value
        would pass even if the engine forked its own copy.
        """
        from agent_workflows import engine as INS

        text = "---\ndescription: whatever\nagent: build\n---\nRead and execute @z\n"
        self.assertEqual(
            M.normalize_for_hash(text), INS.strip_description_and_normalize(text)
        )


class MatchesRecordedTests(unittest.TestCase):
    """`matches_recorded`: is this file still OURS, unchanged by the user?

    ONE table replaces three tests. Each recorded (or did not record) one path and asked
    `matches_recorded` about one content, differing only in whether the path was known and whether the
    content was a cosmetic or a real change. Both are columns.

    Why the table beats the three: the predicate has exactly three outcomes for three reasons
    (unknown path, hash mismatch, hash match), and the UNKNOWN-PATH case returning the same False as a
    real edit is the subtle part. A reader seeing one test per case cannot tell that False is
    overloaded; the table's rows sit adjacent and say so, which matters because the CALLER must treat
    the two Falses differently (leave a foreign file alone versus prompt about a drifted one).

    THE TRUE ROW IS IN THE SAME TABLE and it is load-bearing: a predicate that returned False
    unconditionally would satisfy both False rows, and it would make the installer prompt about every
    file it has ever written.
    """

    #: (case, the content to RECORD or None to record nothing, the path to ask about, the content to
    #: ask with, the expected answer, why this row exists)
    RECORDED = (
        (
            "our own file, reformatted cosmetically",
            "---\nagent: build\n---\nRead and execute @advise\n",
            "advise.md",
            "---\r\ndescription: added later\r\nagent: build\r\n---\r\nRead and execute @advise\r\n",
            True,
            "THE POSITIVE ROW: cosmetic differences only, so this is still OUR file and is safe to "
            "overwrite. Both False rows below are vacuous while this is broken, and a predicate "
            "stuck at False would make the installer prompt about every file it wrote itself",
        ),
        (
            "our own file with a line the user added",
            "---\nagent: build\n---\nRead and execute @advise\n",
            "advise.md",
            "---\nagent: build\n---\nRead and execute @advise\nMY OWN NOTE\n",
            False,
            "REAL USER DRIFT, the case the whole manifest exists for: the recorded hash no longer "
            "matches, so the file must NOT be overwritten without asking. A True here destroys a "
            "user's edit silently",
        ),
        (
            "a path the manifest has never seen",
            None,
            "never-seen.md",
            "anything",
            False,
            "AN UNKNOWN PATH IS NOT OURS, and this row's adjacency to the one above is the point: "
            "the predicate returns the SAME False for two different reasons, and the caller must "
            "distinguish them (leave a foreign file alone versus prompt about a drifted one). A "
            "True here would let the installer claim and overwrite a file somebody else wrote",
        ),
    )

    def test_a_file_is_ours_only_when_its_recorded_hash_still_matches(self):
        wrong = []
        for case, recorded, path, content, expected, why in self.RECORDED:
            man = M.Manifest()
            if recorded is not None:
                man.record(path, recorded)
            actual = man.matches_recorded(path, content)
            if actual is not expected:
                wrong.append(
                    f"  {case} (path={path!r}, recorded={'yes' if recorded else 'no'}):\n"
                    f"    - expected {expected}, got {actual}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`matches_recorded` was wrong for {len(wrong)} of {len(self.RECORDED)} cases. One "
            "predicate decides all three (no record -> False, else recorded == hash), so read the "
            "grouping: BOTH False rows flipping to True means the record lookup stopped being "
            "consulted and every file now counts as ours; the True row alone failing means the hash "
            "comparison broke rather than the lookup. FIX: a wrong True is the destructive "
            "direction, because the caller's next act is to OVERWRITE the file, so a user's edit (or "
            f"another tool's file) is lost with no prompt.\n" + "\n".join(wrong),
        )


class ManifestRoundTripTests(unittest.TestCase):
    """Loading, saving, and the shape of the file on disk. Each claim is structurally different."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    #: (case, what to write at the manifest path (None = do not create the file at all), why this
    #: row exists)
    DEGRADED = (
        (
            "no manifest file at all, in a directory that does not exist either",
            None,
            "AN ABSENT MANIFEST IS A FRESH INSTALL, not an error: the very first `aw` run in a repo "
            "has no manifest, so `load` must return an empty one rather than raising. A raise here "
            "makes the tool unusable on exactly the repos it is meant to set up",
        ),
        (
            "a truncated, syntactically invalid JSON document",
            "{ this is not json",
            "A CORRUPT MANIFEST MUST NOT CRASH the installer. The degradation is deliberate and it "
            "has a cost worth stating: we lose the RECORD of which files are ours, so every managed "
            "file then looks foreign and is left alone. That is the safe direction (nothing is "
            "overwritten), which is why empty-not-raise is the right answer",
        ),
        (
            "an empty file",
            "",
            "the zero-byte case, which is what an interrupted write or a full disk leaves behind. "
            "It is a DIFFERENT parse path from the malformed-JSON row (empty input rather than "
            "invalid syntax) and is the more likely of the two in practice",
        ),
        (
            "valid JSON of the wrong TYPE (a list)",
            "[]",
            "SCHEMA-SHAPED, NOT JUST SYNTAX-SHAPED: the text parses fine and then fails every "
            "`.get` a dict-shaped reader would do. A loader that only guarded `json.JSONDecodeError` "
            "passes the two rows above and raises `AttributeError` here",
        ),
        (
            "valid JSON that is `null`",
            "null",
            "the other wrong-type case, and the one a naive `if data:` guard accidentally survives "
            "while a `data.get(...)` does not. Keeping both wrong-type rows is what makes the claim "
            "'any non-dict payload degrades safely' rather than 'lists degrade safely'",
        ),
    )

    def test_every_unusable_manifest_degrades_to_a_fresh_install(self):
        """One table over the degraded-load paths, replacing two tests.

        `test_absent_manifest_is_fresh_install` and `test_corrupt_manifest_yields_empty_not_crash`
        were the same shape (point `load` at something unusable, assert an empty manifest), differing
        only in WHAT was unusable, so that is the column. Three rows were added for the failure
        modes the two did not reach: an empty file, and two valid-JSON-wrong-TYPE payloads that a
        loader guarding only `JSONDecodeError` would crash on.

        Every row asserts the FULL fresh-install shape (no files, empty version, no recorded hash,
        nothing declined) rather than just `files == {}`, because a half-initialized manifest is
        worse than an empty one: it would answer `recorded_hash` with a stale value.
        """
        wrong = []
        for i, (case, content, why) in enumerate(self.DEGRADED):
            if content is None:
                path = self.base / f"absent{i}" / "managed-sections.json"
            else:
                path = self.base / f"degraded{i}.json"
                path.write_text(content, encoding="utf-8")
            problems = []
            try:
                man = M.load(path)
            except Exception as exc:  # noqa: BLE001 - the point is that nothing escapes
                problems.append(
                    f"`load` RAISED {type(exc).__name__}: {exc}. It must degrade to an empty "
                    "manifest instead, or the installer cannot run at all against this repo"
                )
                man = None
            if man is not None:
                if man.files != {}:
                    problems.append(f"expected no files, got {man.files!r}")
                if man.installed_version != "":
                    problems.append(
                        f"expected an empty installed_version, got "
                        f"{man.installed_version!r}; a stale version would make the installer skip "
                        "an upgrade it needs to perform"
                    )
                if man.recorded_hash("anything") is not None:
                    problems.append(
                        f"expected no recorded hash for an arbitrary path, got "
                        f"{man.recorded_hash('anything')!r}"
                    )
                if man.is_declined("anything"):
                    problems.append(
                        "an empty manifest must not report a path as declined, or the installer "
                        "would skip installing a file nobody declined"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`load` mishandled {len(wrong)} of {len(self.DEGRADED)} unusable manifests. One "
            "read-and-parse path handles every row, so read the grouping: the two WRONG-TYPE rows "
            "failing together means the guard catches only `JSONDecodeError` and not a shape "
            "mismatch; every row failing means the degradation was removed wholesale. FIX: a RAISE "
            "is the failure that matters, because an absent manifest is the NORMAL state of a "
            "first-ever run and a corrupt one must still leave the tool able to operate (it degrades "
            f"to treating every managed file as foreign, which overwrites nothing).\n"
            + "\n".join(wrong),
        )

    def test_round_trip_preserves_entries(self):
        """Kept separate: a save+load PERSISTENCE round trip, and the subject is a whole entry.

        Every field of a recorded entry (host, logical_id, kind, sha256) plus the installed version
        must survive serialization, and the sha256 is cross-checked against the IN-MEMORY manifest's
        own answer, which is a relationship between two objects rather than a value in a table.
        """
        man = M.Manifest(installed_version="1.3.0")
        man.record(
            ".opencode/commands/advise.md",
            "---\nagent: build\n---\nRead and execute @advise\n",
            kind="shim",
            host="opencode",
            logical_id="advise",
        )
        p = self.base / "sub" / "managed-sections.json"
        M.save(man, p)
        self.assertTrue(p.is_file())

        loaded = M.load(p)
        self.assertEqual(loaded.installed_version, "1.3.0")
        entry = loaded.get(".opencode/commands/advise.md")
        assert entry is not None
        self.assertEqual(entry.host, "opencode")
        self.assertEqual(entry.logical_id, "advise")
        self.assertEqual(entry.kind, "shim")
        self.assertEqual(
            entry.sha256, man.recorded_hash(".opencode/commands/advise.md")
        )

    def test_saved_json_is_sorted_and_has_reserved_sections_key(self):
        """Kept separate: the subject is the SERIALIZED JSON's own shape, not any hash or entry.

        Key ORDER is what keeps the committed manifest diff-stable, and the reserved
        `managed_sections` key plus the schema version are the forward-compatibility contract. None of
        those are expressible as a row about content hashing.
        """
        man = M.Manifest(installed_version="1.3.0")
        man.record("b.md", "b")
        man.record("a.md", "a")
        p = self.base / "managed-sections.json"
        M.save(man, p)
        raw = json.loads(p.read_text(encoding="utf-8"))
        self.assertIn("managed_sections", raw)  # reserved for IPD 02
        self.assertEqual(list(raw["files"].keys()), ["a.md", "b.md"])  # sorted
        self.assertEqual(raw["schema_version"], M.SCHEMA_VERSION)

    def test_save_is_atomic_no_temp_left_behind(self):
        """Kept separate: the assertion is about the DIRECTORY after a write, not a returned value."""
        man = M.Manifest()
        man.record("x.md", "x")
        p = self.base / "managed-sections.json"
        M.save(man, p)
        leftovers = [
            q.name
            for q in p.parent.iterdir()
            if q.name.startswith(".managed-sections.")
        ]
        self.assertEqual(leftovers, [], f"atomic temp file left behind: {leftovers}")


class DeclineTombstoneTests(unittest.TestCase):
    """Decline tombstones: both remaining claims are about a mutation SEQUENCE."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_decline_persists_across_save_load(self):
        """Kept separate: a save+load persistence round trip, like its sibling above."""
        man = M.Manifest()
        man.mark_declined(".claude/commands/advise.md", kind="shim", host="claude")
        p = self.base / "managed-sections.json"
        M.save(man, p)
        loaded = M.load(p)
        self.assertTrue(loaded.is_declined(".claude/commands/advise.md"))

    def test_record_preserves_existing_decline(self):
        """Kept separate: the claim is that one mutation does NOT undo a PRIOR one.

        Recording a written hash must not silently un-decline a path, so the content is the ORDER of
        two mutations on one manifest, which a single-input row cannot carry.
        """
        man = M.Manifest()
        man.mark_declined("advise.md")
        # Recording a written hash should not silently un-decline.
        man.record("advise.md", "content")
        self.assertTrue(man.is_declined("advise.md"))


class ManifestPathResolverTests(unittest.TestCase):
    """E-04 / V-04 (manifest side): which manifest path `resolve_manifest_path` returns.

    ONE table replaces four tests. Each created zero, one, or both manifest files in a temp repo and
    asserted which path came back, so the LAYOUT (which files exist) is the only thing that varied:
    a (layout -> resolved path) table is the natural shape.

    Why the table beats the four: the resolver is a three-step precedence (new if it exists, else
    legacy if it exists, else new as the CREATE default), and precedence is a property of the ORDERED
    SET of layouts, not of any one layout. Four separate tests cannot state that the both-present
    answer and the new-only answer must agree while the legacy-only answer differs; adjacent rows
    can, and a regression in the ordering moves them as a group.

    The rows are ordered as the precedence is evaluated, so the table reads as the specification.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    #: (case, create the new-location file, create the legacy-location file, which relative path must
    #: be returned, why this row exists)
    LAYOUTS = (
        (
            "neither location exists",
            False,
            False,
            M.DEFAULT_MANIFEST_RELPATH,
            "THE CREATE DEFAULT, which is the case every fresh install hits: with nothing on disk "
            "the resolver must name the NEW location, or a brand-new repo would have its manifest "
            "written into the legacy path and be born un-migrated",
        ),
        (
            "only the new location exists (a migrated repo)",
            True,
            False,
            M.DEFAULT_MANIFEST_RELPATH,
            "THE MIGRATED REPO, and the row whose answer must match the one above: a repo that has "
            "already moved keeps using the new path. If these two ever disagree, the location "
            "depends on whether a manifest happens to exist yet, which is not a property anything "
            "should vary on",
        ),
        (
            "only the legacy location exists (an un-migrated repo)",
            False,
            True,
            M.LEGACY_MANIFEST_RELPATH,
            "THE FALLBACK, and the row that is FALSIFIABLE in the useful direction: with ONLY the "
            "legacy file present the resolver MUST return it, not the create-default, or an "
            "un-migrated repo's manifest becomes INVISIBLE and every managed file in it looks "
            "foreign. This is the bounded compatibility the resolver exists to provide",
        ),
        (
            "BOTH locations exist",
            True,
            True,
            M.DEFAULT_MANIFEST_RELPATH,
            "THE PRECEDENCE ROW, which no single-file layout can state: mid-migration both files can "
            "exist, and the NEW one wins. Reading the legacy copy here would silently resurrect a "
            "stale record of which files are ours, after the new one had already moved on",
        ),
    )

    def test_the_resolver_prefers_the_new_location_and_falls_back_to_legacy(self):
        wrong = []
        for case, make_new, make_legacy, expected_rel, why in self.LAYOUTS:
            with tempfile.TemporaryDirectory() as td:
                repo = Path(td)
                for make, rel in (
                    (make_new, M.DEFAULT_MANIFEST_RELPATH),
                    (make_legacy, M.LEGACY_MANIFEST_RELPATH),
                ):
                    if make:
                        p = repo / rel
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text("{}", encoding="utf-8")
                actual = M.resolve_manifest_path(repo)
                expected = repo / expected_rel
            if actual != expected:
                wrong.append(
                    f"  {case} (new={make_new}, legacy={make_legacy}):\n"
                    f"    - expected {expected_rel!r}, got {str(actual)[len(str(repo)) + 1 :]!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`resolve_manifest_path` was wrong for {len(wrong)} of {len(self.LAYOUTS)} on-disk "
            "layouts. It is a THREE-STEP PRECEDENCE (new if present, else legacy if present, else "
            "new as the create default) and the rows are in precedence order, so read the grouping: "
            "the two new-location rows disagreeing means the resolved location now depends on "
            "whether a file happens to exist; the LEGACY-ONLY row alone failing means the fallback "
            "was dropped, which makes an un-migrated repo's manifest INVISIBLE so every managed file "
            "in it looks foreign; the BOTH row alone failing means the ordering reversed and a stale "
            f"legacy record would be read after migration.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()
