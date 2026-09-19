"""Self-tests for install-workflows.py.

End-to-end tests run the installer as a subprocess against throwaway git repos and assert
filesystem state (the real behavior, including git staging). Unit tests import the pure
functions. Stdlib unittest only.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: drive the installer or
one of its pure helpers over an input that differs from its neighbour only in DATA, then assert one
thing. The tables group by SUBJECT (the thing being decided) rather than by which function implements
the decision, so the closed sets this installer is built on (the shim argument-hint states, the
output-line status vocabulary, the layout-resolution rules, the aw:block well-formedness verdicts,
the drift decision) are browsable as sets, and a change that moves several members at once reports as
ONE failure naming all of them rather than as N red lines each saying `False is not true`.

WHERE A DISTINCTION IS A MODE IT IS A COLUMN, NOT A SECOND TABLE. The host (`opencode` versus
`claude`), the target layout (`aw` versus `legacy`), colour on versus off, and the presence of a
manifest record are all columns, because in every case the property worth asserting is that the SAME
input gets different answers in different modes, which no single-mode test can state.

THIS IS AN INSTALLER, SO THE MERGING IS DELIBERATELY CONSERVATIVE. The highest-value properties here
are NO-CLOBBER (a user's edited file is never overwritten), IDEMPOTENCE (a second install is
byte-identical), and ABSENCE (a file the user does not have is not created). A test asserting one of
those was merged only where the row asserts the FULL property rather than a weakened slice, which for
a no-clobber row means the surviving CONTENT, the manifest/report entry, and the exit code together.
Where that was not expressible as a row, the test was LEFT ALONE, and it says so in a one-line
docstring. Every left-alone test gives its reason; the recurring ones are: the claim is an exception
(`assertRaises`), the setup is materially different (a frozen clock, a synthetic nested source tree,
a patched collaborator, a subprocess), the two halves are a before/after idempotence PAIR, or the
assertion is structurally unlike its neighbours (a byte-for-byte fixture, a real-file sweep, git
index state).
"""

from __future__ import annotations

import pytest

import io
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tests.support import REPO_ROOT, git, init_repo, run_installer, SOURCE_WORKFLOWS

# The install engine now lives in the agent_workflows package (IPD-2). Import it directly
# for the unit tests; the root install-workflows.py is a thin deprecated shim exercised by
# the subprocess-based end-to-end tests via run_installer().
from agent_workflows import engine as INS
from agent_workflows import cli as CLI
from agent_workflows import reporting_contract
from agent_workflows.term import Term

# Heavy subprocess/install suite; excluded from the fast default run (see pyproject addopts
# `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow


class ManifestParsingTests(unittest.TestCase):
    """What `parse_manifest` and the catalog predicate make of each manifest row SHAPE.

    ONE table replaces four tests (`test_parse_manifest_has_core_and_catalog`,
    `test_catalog_rows_are_recognized`, `test_parse_five_column_row_sets_arg_hint`,
    `test_three_and_four_column_rows_default_arg_hint_empty`). Each wrote a synthetic `index.md`, or
    read the real one, and asserted one thing about the parse. Only the ROW SHAPE differed, which is
    data.

    Why the table beats the four: the column count is a COMPATIBILITY WINDOW, not a fixed format. The
    manifest carries 3-, 4- and 5-column rows simultaneously, and the realistic regression is a parser
    change that handles the newest shape while silently DROPPING a shorter one, which is the
    silent-drop trap PR-001 named. Four tests report that as an unrelated failure per shape; the table
    reports one failure listing every shape that stopped parsing, and keeping the shapes adjacent is
    what documents that the window exists at all.

    THE CATALOG PREDICATE IS THE SAME TABLE'S SECOND COLUMN rather than its own test, because the
    catalog question is asked OF A PARSED ROW: `assess-security` and `advise-skeptic` are catalog rows
    that must NOT become their own shims, while `assess`, `advise`, `release-review` and (the prefix
    EXCEPTION) `assess-all` must. Splitting the two made it possible for the parse to succeed and the
    classification to be wrong with neither test noticing the combination.
    """

    #: (case, the index.md body to parse, {command: expected arg_hint} that must appear, whether each
    #: of those commands must be classified a CATALOG row, why this row exists)
    ROWS = (
        (
            "a 5-column row carrying an argument hint",
            "| demo | .agents/workflows/demo/demo.md | - | d | narrow the scope, e.g. `x` |",
            {"demo": "narrow the scope, e.g. `x`"},
            False,
            "the 5th column is the per-workflow argument hint (IPD 20260721-1754-02), and it is the "
            "NEWEST shape. It parsing is the easy half; the rows below are what prove adding it did "
            "not cost the older shapes",
        ),
        (
            "a 4-column row (command, body, lens, description)",
            "| four | .agents/workflows/four/four.md | - | d |",
            {"four": ""},
            False,
            "the pre-hint shape must still parse, with the hint defaulting to EMPTY rather than to "
            "None or to the description. Empty is what makes `shim_body` render the historical "
            "generic arguments line, so a wrong default here silently reformats every no-hint shim "
            "and makes the installer flag them all as customized",
        ),
        (
            "a 3-column row (command, body, description)",
            "| three | .agents/workflows/three/three.md | d |",
            {"three": ""},
            False,
            "the OLDEST shape, and the one a column-count-based parser breaks first. It is in the "
            "same table as the 5-column row deliberately: a parser that indexes the hint at a fixed "
            "position reads the DESCRIPTION as the hint here, which no 5-column test can catch",
        ),
        (
            "a concern catalog row (`assess-` prefix)",
            "| assess-security | .agents/workflows/assess/assess.md | security | d |",
            {"assess-security": ""},
            True,
            "catalog rows are COLLAPSED into the single parameterized command and must not each get a "
            "shim; `generate_shim_members` keys off this predicate, so a misclassification here is "
            "what puts 30 per-concern shims back in a user's command directory",
        ),
        (
            "a persona catalog row (`advise-` prefix)",
            "| advise-skeptic | .agents/workflows/advise/advise.md | skeptic | d |",
            {"advise-skeptic": ""},
            True,
            "the personas are the second catalog family, and it is asserted beside the concerns "
            "because both are implemented by one prefix test: a change that narrows the predicate to "
            "one prefix leaves the other family expanding",
        ),
        (
            "`assess-all`, a real command that merely LOOKS like a catalog row",
            "| assess-all | .agents/workflows/assess-all/assess-all.md | - | d |",
            {"assess-all": ""},
            False,
            "THE PREFIX EXCEPTION, and the reason a bare `startswith('assess-')` is wrong: this is a "
            "real standalone workflow that MUST get its own shim. It is the negative row that keeps "
            "the two catalog rows above honest, since a predicate returning True for everything "
            "satisfies both of them",
        ),
        (
            "the parameterized commands the catalog rows collapse INTO",
            "| assess | .agents/workflows/assess/assess.md | - | d |\n"
            "| advise | .agents/workflows/advise/advise.md | - | d |",
            {"assess": "", "advise": ""},
            False,
            "the collapse TARGETS must survive classification, or the installer would drop the very "
            "commands the catalog rows fold into and a user would lose `assess` entirely",
        ),
    )

    def test_every_manifest_row_shape_parses_and_classifies(self):
        wrong = []
        for case, body, expected, is_catalog, why in self.ROWS:
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            src = Path(tmp.name)
            (src / "index.md").write_text(
                f"{INS.MANIFEST_BEGIN}\n"
                "| command | body | lens | description | arg-hint |\n"
                "|---|---|---|---|---|\n"
                f"{body}\n"
                f"{INS.MANIFEST_END}\n",
                encoding="utf-8",
            )
            parsed = {w.command: w for w in INS.parse_manifest(src)}
            problems = []
            for command, hint in expected.items():
                if command not in parsed:
                    problems.append(
                        f"{command!r} DID NOT PARSE AT ALL (the parser saw {sorted(parsed)!r}), "
                        "which is the silent-drop trap PR-001 names"
                    )
                    continue
                if parsed[command].arg_hint != hint:
                    problems.append(
                        f"{command!r} parsed with arg_hint {parsed[command].arg_hint!r}, "
                        f"expected {hint!r}"
                    )
                got = INS.is_concern_catalog_row(parsed[command])
                if got != is_catalog:
                    problems.append(
                        f"{command!r} classified is_concern_catalog_row={got}, expected "
                        f"{is_catalog}"
                        + (
                            " (a catalog row treated as a real command gets its OWN shim, putting "
                            "the per-concern shims back)"
                            if not is_catalog
                            else " (a real command treated as a catalog row LOSES its shim)"
                        )
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
            f"the manifest parser mishandled {len(wrong)} of {len(self.ROWS)} row shapes. The column "
            "count is a COMPATIBILITY WINDOW (3, 4 and 5 column rows coexist), so read the failures "
            "together: if every SHORTER shape fails while the 5-column row passes, the parser started "
            "indexing at a fixed position and short rows are being misread or dropped; if only the "
            "classification columns fail, the prefix predicate changed and the shim set will change "
            "with it. FIX: a row that DID NOT PARSE AT ALL is the worst outcome, because the "
            "workflow silently disappears from the installed set rather than appearing wrongly.\n"
            + "\n".join(wrong),
        )

    def test_the_real_manifest_keeps_every_promised_command(self):
        """Kept separate: the subject is the REAL shipped index.md, not a synthetic row.

        Guards the silent-drop trap (PR-001) on the file users actually get: populating 5-column rows
        must not make any workflow disappear. A synthetic row cannot make this claim, and the real
        file has dozens of rows so only PRESENCE of the named set is assertable about it.
        """
        commands = {w.command for w in INS.parse_manifest(SOURCE_WORKFLOWS)}
        missing = [
            c
            for c in (
                "release-review",
                "plan-review",
                "assess",
                "advise",
                "verify",
                "whatnext",
                "list-workflows",
                "handoff",
                "assess-security",
                "advise-skeptic",
            )
            if c not in commands
        ]
        self.assertEqual(
            missing,
            [],
            f"the real manifest no longer yields these commands: {missing}\n"
            "  FIX: a command missing here is a command no target repo receives a shim for.",
        )

    def test_shim_generation_collapses_the_catalog(self):
        """Kept separate: asserts over GENERATED SHIM KEYS from the real manifest, not over rows.

        The catalog predicate is unit-tested as a column of the table above; this is the downstream
        consequence on the real corpus (no per-concern/per-persona shim files, the parameterized ones
        present, `assess-all` getting its own), which is a claim about a dict of generated members
        rather than about any single row.
        """
        shims = INS.generate_shim_members(
            INS.parse_manifest(SOURCE_WORKFLOWS), SOURCE_WORKFLOWS
        )
        self.assertFalse(any("/assess-security.md" in k for k in shims))
        self.assertFalse(any("/advise-skeptic.md" in k for k in shims))
        self.assertTrue(any(k.endswith("/assess.md") for k in shims))
        self.assertTrue(any(k.endswith("/advise.md") for k in shims))
        self.assertTrue(
            any(k.endswith("/assess-all.md") for k in shims),
            "assess-all is a real command despite the assess- prefix and must get its own shim",
        )


class ShimArgumentHintTests(unittest.TestCase):
    """The per-workflow argument hint, rendered across both hosts (IPD 20260721-1754-02).

    ONE table replaces three tests (`test_unset_hint_renders_generic_line_byte_identical`,
    `test_hint_renders_specific_clause`, `test_none_sentinel_omits_arguments_line`). Each looped the
    two tools itself and asserted a different combination of present/absent substrings for one hint
    value. The hint value is the data; the tool is a MODE.

    THE HOST IS A COLUMN, NOT A SECOND TABLE, and that is where the real content is. The two hosts
    DISAGREE deliberately: Claude carries the hint a SECOND time in its front matter as
    `argument-hint:`, and OpenCode carries `agent: build` instead. That asymmetry is invisible unless
    both hosts sit in one row, and it is exactly the kind of thing a refactor unifying the two
    renderers would flatten.

    THE HINT VOCABULARY IS A THREE-VALUED CLOSED SET (unset, a real hint, the `none` sentinel) and the
    rows say which, rather than collapsing it to a bool. The `none` row is the one carrying a real
    trap: it must omit the arguments line ENTIRELY, and a truthiness test on the hint string treats
    `"none"` as a hint and renders the literal word into user-facing prose.

    THE UNSET ROW PINS BYTES, not a substring, because it must reproduce the historical generic line
    EXACTLY: `is_shim_customized_vs_expected` compares generated output against on-disk content, so a
    single reworded character there makes the installer report EVERY installed no-hint shim as
    customized and start prompting users about files they never touched.
    """

    # The historical generic arguments line the unset path MUST reproduce byte-for-byte,
    # or is_shim_customized_vs_expected would flag every installed no-hint shim as customized.
    GENERIC_LINE = (
        "If the user provided arguments, treat them as the target path(s) and/or flags "
        "for this workflow: $ARGUMENTS"
    )
    HINT = "narrow the survey to a concern, e.g. `security`; omit to survey everything"

    #: (case, the `arg_hint` value, substrings that MUST appear in the rendered shim for EVERY host,
    #: substrings that must NOT appear for any host, {host: (must appear, must not appear)} for the
    #: host-SPECIFIC claims, why this row exists)
    HINTS = (
        (
            "no hint set",
            "",
            (GENERIC_LINE,),
            (),
            {
                "claude": (("argument-hint:",), ()),
                "opencode": (("agent: build",), ("argument-hint:",)),
            },
            "THE BYTE-PINNED ROW: an unset hint must reproduce the HISTORICAL generic line exactly, "
            "because `is_shim_customized_vs_expected` diffs generated output against what is on "
            "disk. Reword one character and every installed no-hint shim is reported as customized, "
            "which prompts the user about files they never edited",
        ),
        (
            "a real hint supplied by the manifest",
            HINT,
            (f"If the user provided arguments, {HINT}: $ARGUMENTS",),
            (GENERIC_LINE,),
            {
                "claude": ((f'argument-hint: "[{HINT}]"',), ()),
                "opencode": (("agent: build",), ("argument-hint:",)),
            },
            "the specific clause REPLACES the generic one rather than joining it, which is why the "
            "generic line is a forbidden substring here; and Claude repeats the hint in front matter "
            "so its CLI can show it, which is the host asymmetry this table exists to keep visible",
        ),
        (
            "the `none` sentinel",
            "none",
            (),
            ("If the user provided arguments",),
            {
                "claude": ((), ("argument-hint:",)),
                "opencode": (("agent: build",), ("argument-hint:",)),
            },
            "`none` means this workflow takes NO arguments, so the whole line goes away and Claude's "
            "front-matter key with it. THE TRAP: a truthiness test on the hint string treats `'none'` "
            "as a hint and renders the literal word `none` into the user-facing sentence",
        ),
    )

    @staticmethod
    def _wf(arg_hint=""):
        return INS.Workflow(
            command="demo",
            body=".agents/workflows/demo/demo.md",
            description="demo",
            arg_hint=arg_hint,
        )

    def test_every_hint_state_renders_correctly_on_both_hosts(self):
        wrong = []
        for case, hint, present, absent, per_host, why in self.HINTS:
            problems = []
            for tool in ("opencode", "claude"):
                body = INS.shim_body("demo", self._wf(arg_hint=hint), tool)
                host_present, host_absent = per_host[tool]
                for needle in present + host_present:
                    if needle not in body:
                        problems.append(f"[{tool}] missing {needle!r}")
                for needle in absent + host_absent:
                    if needle in body:
                        problems.append(
                            f"[{tool}] contains {needle!r}, which this row forbids"
                        )
                # Every shim, whatever its hint, must carry the controlling-instruction sentence and
                # end with the reporting POINTER line (terseout `ntf6sx` E-03).
                if (
                    "Treat the referenced file as the controlling instruction "
                    "and follow it fully.\n" not in body
                ):
                    problems.append(
                        f"[{tool}] lost the controlling-instruction sentence, which is what makes "
                        "the shim delegate to the workflow body instead of being read as advice"
                    )
                if not body.endswith(reporting_contract.shim_pointer_line()):
                    problems.append(
                        f"[{tool}] does not END with the reporting pointer line; it is the shim's "
                        f"tail by contract, and the body ends {body[-60:]!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (arg_hint={hint!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"shim_body mishandled {len(wrong)} of {len(self.HINTS)} argument-hint states. Both hosts "
            "are rendered from ONE function with a per-host branch, so read the failures together: if "
            "the SAME needle fails on both hosts the shared body assembly changed; if only the "
            "`claude` rows fail, the front-matter branch did; if the unset row fails on the generic "
            "line, note that line is BYTE-PINNED on purpose and 'improving' its wording makes the "
            "installer report every installed no-hint shim as user-customized. FIX: check the "
            f"forbidden substrings too, since rendering BOTH the generic and specific clause "
            f"satisfies every presence check while producing a contradictory shim.\n"
            + "\n".join(wrong),
        )


class OutputLineFormattingTests(unittest.TestCase):
    """The installer's per-file status line: one status token in, one rendered line out.

    ONE table replaces `test_format_output_item`, which asserted four unrelated renderings in one
    method with no way to tell which had broken. The statuses are a CLOSED VOCABULARY the installer
    prints for every file it touches, and the realistic regression is in the SHARED assembly (a label
    width, a colour lookup, the dry-run suffix), which shifts EVERY line at once.

    COLOUR IS A COLUMN, NOT A SECOND TABLE, and the column asserts more than the old test did: for
    each row the coloured render must actually CONTAIN an ANSI escape (otherwise the palette is
    silently inert and every plain assertion still passes), and stripping the escapes must recover the
    plain line EXACTLY. That second property is the one that matters, because the labels are PADDED to
    a fixed width: pad a coloured string and the visible column is wrong while plain-mode tests stay
    green.

    THE LABELS ARE WRITTEN WITH THEIR PADDING (`[added    ]`, not `[added]`) deliberately. The
    alignment is the point of the fixed-width label, so a row that tolerated either spelling would
    accept a change that ragged the whole listing.
    """

    #: (case, the raw `<path> [<status>]` item, expected PLAIN rendering, the ANSI colour code the
    #: label must carry when colour is on, why this row exists)
    ITEMS = (
        (
            "a newly installed file",
            "foo/bar.py [install]",
            "[added    ] foo/bar.py",
            "32;1",
            "GREEN for an addition: the common, safe outcome. Also the row that pins the label "
            "PADDING, since `added` is the shortest label and everything aligns against it",
        ),
        (
            "an overwritten file",
            "foo/bar.py [overwrite]",
            "[overwrite] foo/bar.py",
            "31;1",
            "RED, and the distinction that matters most to a user reading the summary: an overwrite "
            "replaced content that was already there. Rendering it like an addition would hide the "
            "only destructive thing a normal install does",
        ),
        (
            "an unchanged file",
            "foo/bar.py [already current]",
            "[no change] foo/bar.py",
            "33;1",
            "the status token and the LABEL deliberately differ (`already current` renders as "
            "`no change`), so this row proves the mapping is a real lookup rather than the token "
            "being echoed",
        ),
        (
            "a pruned file",
            "foo/bar.py [git rm]",
            "[removed  ] foo/bar.py",
            "31;1",
            "a REMOVAL is rendered red like an overwrite, because both destroy something. The token "
            "here is a git verb while the label is plain English, which is the same mapping claim as "
            "the row above made over a different family",
        ),
        (
            "an overwrite in dry-run mode",
            "foo/bar.py [overwrite, dry-run]",
            "[overwrite] foo/bar.py (dry-run)",
            "31;1",
            "DRY-RUN IS A SUFFIX, NOT A STATUS: the label still says what WOULD happen and `(dry-run)` "
            "is appended. This is the row where a parser that split the status on `,` and looked up "
            "the whole string would fall back to some default and silently lose the overwrite "
            "warning",
        ),
        (
            "an addition in dry-run mode",
            "foo/bar.py [install, dry-run]",
            "[added    ] foo/bar.py (dry-run)",
            "32;1",
            "the suffix composes with EVERY status, not just the destructive one; having both dry-run "
            "rows is what shows the suffix is orthogonal rather than special-cased for overwrites",
        ),
        (
            "a skipped file",
            "foo/bar.py [skipped]",
            "[skipped  ] foo/bar.py",
            "90;1",
            "GREY for 'we deliberately did nothing', which is how a user distinguishes a file the "
            "installer LEFT ALONE (a declined or customized one) from one it found already current",
        ),
        (
            "a migrated file",
            "foo/bar.py [migrated]",
            "[migrated ] foo/bar.py",
            "90;1",
            "the relocation statuses share the grey 'informational' colour; asserted so a new status "
            "added without a colour entry shows up here rather than rendering unstyled in front of a "
            "user",
        ),
    )

    def test_every_status_renders_its_exact_line_in_both_colour_modes(self):
        plain_term = Term(color=False)
        colour_term = Term(color=True)
        wrong = []
        for case, item, expected, code, why in self.ITEMS:
            problems = []
            got = INS.format_output_item(item, plain_term)
            if got != expected:
                problems.append(
                    f"plain render expected {expected!r}, got {got!r}"
                    + (
                        f" (a {len(got) - len(expected):+d} character shift, so the listing no "
                        "longer aligns)"
                        if len(got) != len(expected)
                        else ""
                    )
                )
            coloured = INS.format_output_item(item, colour_term)
            if "\033[" not in coloured:
                problems.append(
                    f"the coloured render carries NO ANSI escape ({coloured!r}), so the palette is "
                    "silently inert and no plain-mode assertion can detect it"
                )
            elif f"\033[{code}m" not in coloured:
                problems.append(
                    f"expected the label to carry \\033[{code}m; got {coloured!r}. The colour is how "
                    "a user triages the summary at a glance, so a destructive status rendered in a "
                    "safe colour is worse than no colour at all"
                )
            stripped = re.sub(r"\033\[[0-9;]*m", "", coloured)
            if stripped != got:
                problems.append(
                    f"stripping ANSI gave {stripped!r} but the plain render is {got!r}; the "
                    "fixed-width label must be padded on UNCOLOURED text, so colour is purely "
                    "additive"
                )
            if problems:
                wrong.append(
                    f"  {case} ({item!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"format_output_item mishandled {len(wrong)} of {len(self.ITEMS)} statuses. Every line is "
            "assembled by one function from a fixed-width label, a colour looked up per status, and "
            "an optional dry-run suffix, so read the failures together: several rows shifted by the "
            "SAME number of characters means the label width changed and the per-status mapping is "
            "fine; a failing strip-to-plain check means padding is computed on the COLOURED string, "
            "which misaligns a real terminal while plain-mode tests stay green. FIX: these statuses "
            "are the whole vocabulary a user reads to see what the installer DID, so a wrong colour "
            f"on a destructive status is a safety problem, not a cosmetic one.\n"
            + "\n".join(wrong),
        )


class VersionResolutionTests(unittest.TestCase):
    """`read_version` is git-aware in a checkout and falls back to the VERSION file outside one.

    Two tests became one table whose column is the SOURCE TREE KIND. Both called `read_version` and
    compared it to something; they differed in whether the tree was a git checkout, which decides
    WHICH answer is correct. Keeping them together is what documents that there are exactly two
    regimes, since either test alone reads as 'the version comes from here'.
    """

    def test_a_git_checkout_defers_to_the_resolver_and_a_plain_tree_reads_the_file(
        self,
    ):
        from agent_workflows import versioning as VER

        wrong = []
        # In this project's real git tree, read_version must agree with the resolver (a semver/.dev
        # string), NOT necessarily with the raw VERSION file.
        expected = VER.resolve_version(
            SOURCE_WORKFLOWS, version_file=SOURCE_WORKFLOWS / "VERSION"
        )
        got = INS.read_version(SOURCE_WORKFLOWS)
        if got != expected:
            wrong.append(
                f"  a real git checkout:\n    - read_version gave {got!r}, the resolver gives "
                f"{expected!r}\n"
                "    this row exists because: inside a checkout the git description is the truth "
                "(it carries the .dev suffix that distinguishes an unreleased tree from the tagged "
                "release), so reading the static file here would make every dev install claim to be "
                "a release"
            )
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "workflows"
            source.mkdir(parents=True)
            (source / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            got = INS.read_version(source)
            if got != "1.2.3":
                wrong.append(
                    f"  a non-git tree (a copied or unpacked install):\n    - read_version gave "
                    f"{got!r}, expected the baked file value '1.2.3'\n"
                    "    this row exists because: V-9 characterization. A user who unpacked a wheel "
                    "has no git metadata at all, so the VERSION file is the ONLY answer; a resolver "
                    "that raised or returned empty here would break `--version` for every "
                    "non-checkout install"
                )
        self.assertEqual(
            wrong,
            [],
            f"read_version was wrong in {len(wrong)} of 2 source-tree regimes. One function serves "
            "both, so BOTH failing means the resolver call itself broke, while one failing means the "
            "git-detection branch picked the wrong regime. FIX: the two answers are legitimately "
            "DIFFERENT and must not be unified; the installed VERSION file and the git description "
            f"agree only at a tagged commit.\n" + "\n".join(wrong),
        )

    def test_parse_args_no_color(self):
        """Kept separate: argparse introspection, not a version claim; shares no shape with the above."""
        self.assertTrue(INS.parse_args(["--no-color"]).no_color)
        self.assertFalse(INS.parse_args([]).no_color)


class InstallerEndToEndTests(unittest.TestCase):
    """Run the installer as a SUBPROCESS against throwaway repos and assert filesystem state.

    Only two clusters here were merged, and the rest were deliberately left alone. Each test in this
    class drives a real `install-workflows.py` subprocess with a different FLAG SET and then asserts a
    different KIND of thing (git index state, prompt behavior, backup directory contents, rollback
    content), so most of them share no table shape. The two that did share one are the
    NO-CLOBBER/PRESERVATION cluster and the ABSENT-FILE cluster, and both are merged in
    `InstallPreservationTests` below rather than here, because every row there has to assert the FULL
    property (surviving content AND the installer's exit code) and that needs its own harness.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")

    def tearDown(self):
        self._tmp.cleanup()

    def _shims(self, tool_dir: str) -> set[str]:
        d = self.repo / tool_dir
        return {p.name for p in d.glob("*.md")} if d.is_dir() else set()

    def test_fresh_install(self):
        """Kept separate: the canonical fresh-install contract, asserted over the whole target tree.

        Not a row anywhere: it makes a dozen claims about DIFFERENT paths at once (the framework tree,
        the shim set, a shim's internal reference, the AGENTS pointer, and the installer's own absence
        from the target), which is a single coherent contract rather than a repeated shape.
        """
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # Framework files landed in canonical .aw/ layout.
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())
        self.assertTrue((self.repo / ".aw/system/VERSION").is_file())
        self.assertFalse((self.repo / ".agents/workflows").exists())
        # A single parameterized assess shim, and no per-concern shims.
        oc = self._shims(".opencode/commands")
        self.assertIn("assess.md", oc)
        self.assertIn("advise.md", oc)
        self.assertNotIn("assess-security.md", oc)
        self.assertNotIn("advise-skeptic.md", oc)
        # Verify generated shim references .aw/system/workflows/
        assess_content = (self.repo / ".opencode/commands/assess.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("@.aw/system/workflows/assess/assess.md", assess_content)
        # AGENTS pointer written with .aw/system/workflows/ references.
        self.assertTrue((self.repo / "AGENTS.md").is_file())
        agents_content = (self.repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(".aw/system/workflows/", agents_content)
        # The installer itself is NOT copied into the target.
        self.assertFalse((self.repo / "install-workflows.py").exists())

    def test_idempotent_rerun(self):
        """Kept separate: a before/after PAIR over the whole file set; the two halves are one claim."""
        run_installer(self.repo)
        before = sorted(
            p.relative_to(self.repo).as_posix()
            for p in self.repo.rglob("*")
            if p.is_file()
        )
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        after = sorted(
            p.relative_to(self.repo).as_posix()
            for p in self.repo.rglob("*")
            if p.is_file()
        )
        self.assertEqual(before, after, "re-run changed the set of files")

    def test_dry_run_makes_no_changes(self):
        """Kept separate: the only `--dry-run` subprocess, and the claim is a pure ABSENCE sweep."""
        proc = run_installer(self.repo, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(
            (self.repo / ".aw/system/workflows/index.md").exists(),
            "dry-run wrote files",
        )
        self.assertFalse(
            (self.repo / ".agents/workflows/index.md").exists(),
            "dry-run wrote files",
        )
        self.assertFalse((self.repo / ".opencode/commands/assess.md").exists())

    def test_prune_removes_legacy_assess_shims(self):
        """Kept separate: pruning is a REMOVAL claim, the inverse of preservation; see --no-prune below."""
        run_installer(self.repo)
        # Simulate an older install that had per-concern shims.
        legacy = self.repo / ".opencode/commands/assess-security.md"
        legacy.write_text(
            "Read and execute @.agents/workflows/assess-security\n", encoding="utf-8"
        )
        legacy2 = self.repo / ".claude/commands/assess-prose.md"
        legacy2.write_text(
            "Read and execute @.agents/workflows/assess-prose\n", encoding="utf-8"
        )
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(legacy.exists(), "stale assess-security shim not pruned")
        self.assertFalse(legacy2.exists(), "stale assess-prose shim not pruned")

    def test_no_prune_keeps_stale(self):
        """Kept separate: `--no-prune` is the FLAG that inverts the test above, so they are a pair."""
        run_installer(self.repo)
        legacy = self.repo / ".opencode/commands/assess-security.md"
        legacy.write_text(
            "Read and execute @.agents/workflows/assess-security\n", encoding="utf-8"
        )
        run_installer(self.repo, "--no-prune")
        self.assertTrue(legacy.exists(), "--no-prune should not remove stale files")

    def test_shim_readme_is_not_pruned(self):
        """Kept separate: the README is the documented EXCEPTION to pruning, not another prune case."""
        run_installer(self.repo)
        shim_readme = self.repo / ".opencode/commands/README.md"
        self.assertTrue(shim_readme.is_file())
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(shim_readme.is_file(), "Shim README was pruned!")

    def test_legacy_layout_migration(self):
        """Kept separate: materially different setup (a committed pre-D17 root directory)."""
        legacy_dir = self.repo / "release-review"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "README.md").write_text("legacy runbook\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "legacy layout")
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.repo / ".aw/system/workflows/index.md").is_file())

    def test_version_flag(self):
        """Kept separate: asserts the subprocess's STDOUT, not filesystem state."""
        proc = run_installer(self.repo, "--version")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), INS.read_version(SOURCE_WORKFLOWS))

    def test_diff_mode(self):
        """Kept separate: `--diff` asserts stdout content AND that nothing was written."""
        proc = run_installer(self.repo, "--diff")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("+", proc.stdout)
        self.assertFalse((self.repo / ".aw/system/workflows").exists())

    def test_tool_scripts_are_executable_and_staged(self):
        """Kept separate: asserts the git INDEX (mode bits in `ls-files -s`) and carries an os.name guard."""
        run_installer(self.repo)
        tool = self.repo / ".aw/system/workflows/assess/tools/scan_secrets.py"
        # The re-run-leaves-nothing-unstaged idempotency guarantee holds on every OS.
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        leftover = git(self.repo, "status", "--porcelain").stdout.strip()
        self.assertEqual(leftover, "", f"re-run left files unstaged:\n{leftover}")

        # The POSIX executable-bit assertions are meaningful only on POSIX: Windows has no
        # mode exec bit and git there records 100644. Skip the mode checks on Windows.
        if os.name == "posix":
            self.assertTrue(
                tool.stat().st_mode & 0o111, "tool script is not executable"
            )
            indexed = git(
                self.repo,
                "ls-files",
                "-s",
                ".aw/system/workflows/assess/tools/scan_secrets.py",
            ).stdout
            self.assertTrue(
                indexed.startswith("100755"), f"exec bit not in index: {indexed!r}"
            )

    def test_gitignored_opencode_does_not_abort(self):
        """Kept separate: the subject is which paths reached the git INDEX, with a gitignore precondition."""
        (self.repo / ".gitignore").write_text(".opencode/\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-q", "-m", "ignore opencode")
        proc = run_installer(self.repo)
        # Install completes despite the gitignored shim dir.
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ignored by .gitignore", proc.stderr)
        # Shims are still written to disk (they work locally).
        self.assertTrue((self.repo / ".opencode/commands/assess.md").is_file())
        # But .opencode is not staged; .claude and .aw are.
        staged = git(self.repo, "diff", "--cached", "--name-only").stdout
        self.assertNotIn(".opencode/", staged)
        self.assertIn(".claude/commands/assess.md", staged)
        self.assertIn(".aw/system/workflows/index.md", staged)

    def test_readme_templates_are_created_on_a_fresh_install(self):
        """Kept separate from the preservation table: this is the CREATION half, over four paths.

        wfartifacts Order 01 (gzhd7t): RE-POINTED, not deleted. The run-scratch README moved from the
        retired repo-root `workflow-artifacts/` to `.aw/workflow-artifacts/` (Order 07), so this
        remains a real guarantee; only the path changed. The PRESERVATION half (a customized copy
        surviving a re-run) is a row in `InstallPreservationTests`, where every row also asserts the
        exit code.
        """
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        missing = [
            p.relative_to(self.repo).as_posix()
            for p in (
                self.repo / ".aw/system/workflows/README.md",
                self.repo / ".opencode/commands/README.md",
                self.repo / ".claude/commands/README.md",
                self.repo / ".aw/workflow-artifacts/README.md",
            )
            if not p.is_file()
        ]
        self.assertEqual(missing, [], f"READMEs not created: {missing}")
        self.assertIn(
            "auto-generated",
            (self.repo / ".opencode/commands/README.md").read_text(encoding="utf-8"),
        )
        # The README's CONTENT is Order 04's scope (it still carries the retired "DO NOT gitignore"
        # prose today), so this asserts only that the template landed, at the new path.
        self.assertIn(
            "Git Guidelines",
            (self.repo / ".aw/workflow-artifacts/README.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_fresh_install_creates_no_repo_root_workflow_artifacts_dir(self):
        """Kept separate: a maintainer-reported defect whose claim spans disk AND the git index.

        wfartifacts Order 01 (gzhd7t): the 2026-09-12 maintainer report, turned into a test. The
        reported defect is that a repo-root `workflow-artifacts/` directory APPEARS on every fresh
        install, carrying a README that says "DO NOT gitignore this folder" - the opposite of Order
        07's ruling. An EMPTY repo-root directory is still a FAILURE here: the report is about the
        directory existing at all, so asserting only on the README would let a bare `mkdir` regress
        silently.
        """
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        self.assertFalse(
            (self.repo / "workflow-artifacts").exists(),
            "a fresh install must not create a repo-root workflow-artifacts/ directory "
            "(Order 07 relocated run scratch to .aw/workflow-artifacts/)",
        )
        # The relocation half: the README landed at the new path instead.
        self.assertTrue(
            (self.repo / ".aw/workflow-artifacts/README.md").is_file(),
            "the run-scratch README should land under .aw/workflow-artifacts/",
        )
        # And it is NOT staged: this README documents a tree that must never be committed (D92).
        # git's ignore rules do not untrack an already-tracked path, so staging it even once would
        # be permanent for that repo.
        ls = git(self.repo, "ls-files", "--", ".aw/workflow-artifacts")
        self.assertEqual(
            ls.stdout.strip(),
            "",
            "the run-scratch README must not be staged (run scratch is never committed, D92)",
        )

    def test_installer_summary_names_no_repo_root_run_scratch_path(self):
        """Kept separate: a regex sweep over the subprocess's OUTPUT, not over the filesystem.

        wfartifacts Order 01 (gzhd7t) E-02: no installer output describes the retired path.
        `check_gitignore` used to print "workflow-artifacts/ is ignored (correct...)" or "...is not
        ignored (advisory: working material will be tracked in git)". Both sentences described the
        repo-root path, and the advisory's "will be tracked in git" was backwards for a tree that
        carries absolute home paths and session detail (D92).
        """
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout + proc.stderr

        # A repo-root mention is a bare `workflow-artifacts/` NOT preceded by `.aw/` (and not part of
        # the shipped template filename `workflow-artifacts-README.md`).
        offenders = [
            line
            for line in out.splitlines()
            if re.search(r"(?<![\w./-])workflow-artifacts/", line)
        ]
        self.assertEqual(
            offenders,
            [],
            f"installer output still names the retired repo-root path: {offenders}",
        )
        # The line is KEPT (OQ-01 resolved as "retarget, not remove"), so it must still be present
        # and must name the new path.
        self.assertIn("Gitignore (run scratch):", out)
        self.assertIn(".aw/workflow-artifacts/", out)

    def test_rollback_undo(self):
        """Kept separate: a four-step stateful sequence (install, edit, reinstall, edit, undo)."""
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        target_file = self.repo / ".aw/system/workflows/index.md"
        original_text = target_file.read_text(encoding="utf-8")

        # Modify the target file
        target_file.write_text("MODIFIED CONTENT", encoding="utf-8")

        # 2) Run installer again to trigger an overwrite and backup
        proc2 = run_installer(self.repo)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)

        # Verify it got overwritten back to original content
        self.assertEqual(target_file.read_text(encoding="utf-8"), original_text)

        # Now modify it again, so we can test rollback
        target_file.write_text("MODIFIED CONTENT SECOND TIME", encoding="utf-8")

        # Run rollback
        proc_undo = run_installer(self.repo, "--undo")
        self.assertEqual(proc_undo.returncode, 0, proc_undo.stderr)

        # Verify it got rolled back to the backup state ("MODIFIED CONTENT" from before the second install!)
        self.assertEqual(target_file.read_text(encoding="utf-8"), "MODIFIED CONTENT")

    def test_backup_auto_pruning(self):
        """Kept separate: the subject is a COUNT of backup directories after a retention sweep."""
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        backups_dir = self.repo / ".agent-workflows-installer-backups"
        backups_dir.mkdir(parents=True, exist_ok=True)

        # Create 7 mock backup directories manually, then run again: 8 runs total, 5 retained.
        for i in range(7):
            (backups_dir / f"20260709-12000{i}").mkdir(parents=True, exist_ok=True)

        proc2 = run_installer(self.repo, "--yes")
        self.assertEqual(proc2.returncode, 0, proc2.stderr)

        self.assertTrue(backups_dir.is_dir())
        subdirs = sorted(
            [d for d in backups_dir.iterdir() if d.is_dir()], key=lambda d: d.name
        )
        self.assertEqual(len(subdirs), 5)

    def test_native_agent_files_mirroring(self):
        """Kept separate: a six-stage stateful sequence over TWO files, ending in an uninstall.

        Its stages are not independent (each depends on the file state the previous one left), and the
        last two probe MALFORMED marker shapes whose handling differs by design (a lone opener is
        refreshed in place, duplicated wrappers are appended to). The absent-file and dry-run claims it
        opens with are ALSO rows in `InstallPreservationTests`, deliberately: there they carry the exit
        code and the no-clobber content check, which this sequence does not.
        """
        # 1. By default, absent CLAUDE.md/GEMINI.md are NOT created.
        proc = run_installer(self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.repo / "CLAUDE.md").exists())
        self.assertFalse((self.repo / "GEMINI.md").exists())

        # 2. Existing CLAUDE.md / GEMINI.md get the block.
        claude_file = self.repo / "CLAUDE.md"
        gemini_file = self.repo / "GEMINI.md"
        claude_file.write_text("User CLAUDE content\n", encoding="utf-8")
        gemini_file.write_text("User GEMINI content\n", encoding="utf-8")

        proc2 = run_installer(self.repo)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)

        claude_txt = claude_file.read_text(encoding="utf-8")
        gemini_txt = gemini_file.read_text(encoding="utf-8")

        # IPD 02: the installer now writes the SECTIONED aw:block form (not the legacy
        # AGENT-WORKFLOWS:BEGIN/END markers). Human-visible content is unchanged.
        self.assertIn("User CLAUDE content", claude_txt)
        self.assertIn("<!-- aw:block -->", claude_txt)
        self.assertIn("<!-- aw:pointer -->", claude_txt)
        self.assertIn("<!-- /aw:block -->", claude_txt)
        self.assertIn("## Agent workflows", claude_txt)

        self.assertIn("User GEMINI content", gemini_txt)
        self.assertIn("<!-- aw:block -->", gemini_txt)
        self.assertIn("<!-- /aw:block -->", gemini_txt)

        # 3. Dry-run does not write to them.
        claude_file.write_text("User CLAUDE content\n", encoding="utf-8")
        proc3 = run_installer(self.repo, "--dry-run")
        self.assertEqual(proc3.returncode, 0, proc3.stderr)
        self.assertEqual(
            claude_file.read_text(encoding="utf-8"), "User CLAUDE content\n"
        )

        # 4. Re-running is idempotent.
        run_installer(self.repo)
        txt_after = claude_file.read_text(encoding="utf-8")
        self.assertEqual(txt_after.count("<!-- aw:block -->"), 1)

        # 5. Uninstall removes only the block.
        INS.uninstall_repo(self.repo, use_git=True)

        # User content remains in the file
        self.assertTrue(claude_file.is_file())
        self.assertTrue(gemini_file.is_file())
        self.assertIn("User CLAUDE content", claude_file.read_text(encoding="utf-8"))
        self.assertNotIn("<!-- aw:block -->", claude_file.read_text(encoding="utf-8"))
        self.assertIn("User GEMINI content", gemini_file.read_text(encoding="utf-8"))
        self.assertNotIn("<!-- aw:block -->", gemini_file.read_text(encoding="utf-8"))

        # 6a. A lone aw:block opener (missing close) is DRIFT: the parser closes it at EOF and
        # the installer refreshes it in place (non-destructive), preserving the user's prose.
        # This is stronger than the legacy append-duplicate behavior.
        claude_file.write_text("User prose\n<!-- aw:block -->\n", encoding="utf-8")
        run_installer(self.repo)
        txt = claude_file.read_text(encoding="utf-8")
        self.assertIn("User prose", txt)
        self.assertEqual(txt.count("<!-- aw:block -->"), 1)
        self.assertEqual(txt.count("<!-- /aw:block -->"), 1)

        # 6b. Duplicated wrapper markers ARE ambiguous: safe append, never a destructive rewrite.
        gemini_file.write_text(
            "User prose\n<!-- aw:block -->\nx\n<!-- /aw:block -->\n"
            "<!-- aw:block -->\ny\n<!-- /aw:block -->\n",
            encoding="utf-8",
        )
        run_installer(self.repo)
        gtxt = gemini_file.read_text(encoding="utf-8")
        self.assertIn("User prose", gtxt)
        self.assertEqual(
            gtxt.count("<!-- aw:block -->"), 3
        )  # 2 pre-existing + 1 appended


class InstallPreservationTests(unittest.TestCase):
    """THE NO-CLOBBER CONTRACT: what an install does to a file the user already has, per flag set.

    ONE table replaces four scattered claims (the customization-protection pair from
    `test_customization_protection`, the README preservation half of
    `test_readme_creation_and_preservation`, and the absent-native-file and dry-run halves of
    `test_native_agent_files_mirroring`). All four had the identical shape: put a file (or no file) in
    a known state, run the installer with some flags, then assert what the file holds afterwards. The
    file and the flags are DATA; the property is one property.

    THIS IS THE MOST IMPORTANT TABLE IN THE FILE, so it is also the strictest. The natural shape for an
    installer is `(existing file state, install flags) -> (expected content, expected exit code)` and
    EVERY ROW ASSERTS THE WHOLE TRIPLE. A row never settles for "the content survived": it also pins
    the installer's EXIT CODE, because a run that preserved the file by CRASHING is not preservation,
    and a non-zero exit is how a user's CI would have caught it. Where the expectation is absence, the
    row asserts the file does not exist AND the run still succeeded, which is what distinguishes
    "deliberately did not create it" from "failed before it got there".

    WHY THESE BELONG TOGETHER RATHER THAN APART. All three outcomes are decided by ONE question the
    installer asks per file, "is this ours or theirs?", and the realistic regression is a change to
    that decision, which moves several rows at once in the SAME direction. Merged, a broken
    ours-or-theirs test reports as one failure listing every file class that lost its protection; that
    is a materially better bug report than three separate red lines, and seeing which classes moved
    together is what identifies the cause.

    THE `--yes` ROW IS THE DELIBERATE EXCEPTION AND IT IS IN THE SAME TABLE. `--yes` means the user
    asked to be overwritten, so a customized shim SHOULD lose its content; expressed as a column, that
    makes explicit that non-interactive default behavior is the safe one and overwriting is opt-in. Keep
    it here rather than in its own test, because an implementation that overwrote NOTHING would satisfy
    every preservation row on its own and only this row catches it.
    """

    #: (case, {repo-relative path: content to place first} or {} for none, extra installer flags, the
    #: repo-relative path under test, the expected content afterwards or None meaning MUST NOT EXIST,
    #: whether the content is expected to CHANGE, why this row exists)
    CASES = (
        (
            "a hand-customized shim, default (non-interactive) install",
            {
                ".opencode/commands/assess.md": "---\ndescription: My custom assessment\n---\n"
                "Custom instructions here."
            },
            (),
            ".opencode/commands/assess.md",
            "---\ndescription: My custom assessment\n---\nCustom instructions here.",
            False,
            "THE CORE NO-CLOBBER PROPERTY: a file the user edited is preserved BYTE-FOR-BYTE when the "
            "installer cannot ask. The exit code is asserted with it because preserving the file by "
            "aborting the run is not preservation, and a user whose CI runs `aw install` would see "
            "the failure rather than the protection",
        ),
        (
            "the same customized shim, but the user passed --yes",
            {
                ".opencode/commands/assess.md": "---\ndescription: My custom assessment\n---\n"
                "Custom instructions here."
            },
            ("--yes",),
            ".opencode/commands/assess.md",
            None,  # content must CHANGE; the exact replacement is the generated shim
            True,
            "THE DELIBERATE EXCEPTION, and what stops this table being vacuous: `--yes` is the user "
            "asking to be overwritten, so the customization MUST be replaced. An installer that "
            "preserved everything unconditionally would satisfy every other row here, so without this "
            "row the table cannot distinguish protection from paralysis",
        ),
        (
            "a customized run-scratch README",
            {
                ".aw/workflow-artifacts/README.md": "Custom user guidelines for this repo's "
                "execution trails."
            },
            (),
            ".aw/workflow-artifacts/README.md",
            "Custom user guidelines for this repo's execution trails.",
            False,
            "the no-clobber rule covers TEMPLATE-PROVIDED files too, not just shims. This one is a "
            "file the installer itself created on the first run, so the second run has to recognize "
            "its own output as since-edited rather than as reinstallable",
        ),
        (
            "an absent CLAUDE.md",
            {},
            (),
            "CLAUDE.md",
            None,
            False,
            "ABSENT NATIVE FILES ARE NOT CREATED: the installer mirrors its block into a host's native "
            "file only if the user ALREADY has one, because creating `CLAUDE.md` in a repo that does "
            "not use Claude adds a file the user never asked for and must then delete",
        ),
        (
            "an absent GEMINI.md",
            {},
            (),
            "GEMINI.md",
            None,
            False,
            "the second native host, asserted beside the first because one predicate governs both: a "
            "change that special-cased Claude would leave Gemini files springing into existence",
        ),
        (
            "an existing CLAUDE.md the user wrote",
            {"CLAUDE.md": "User CLAUDE content\n"},
            (),
            "CLAUDE.md",
            None,  # content CHANGES (the block is added) but the user's prose must survive
            True,
            "THE PAIRED POSITIVE of the two absence rows: when the file DOES exist the block is added, "
            "so 'not created' is a rule about creation and not a refusal to manage the file at all. "
            "The user's own prose surviving is asserted separately below, since this column tracks "
            "whether the bytes changed",
        ),
        (
            "an existing CLAUDE.md under --dry-run",
            {"CLAUDE.md": "User CLAUDE content\n"},
            ("--dry-run",),
            "CLAUDE.md",
            "User CLAUDE content\n",
            False,
            "DRY-RUN IS A MODE COLUMN over the very row above: the same input that legitimately gets "
            "written must be left untouched when only a preview was asked for. Having both in one "
            "table is what proves `--dry-run` suppresses the WRITE rather than the DETECTION",
        ),
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_existing_file_state_is_handled_without_clobbering(self):
        wrong = []
        exception_row_broken = 0
        for index, (case, seed, flags, rel, expected, changes, why) in enumerate(
            self.CASES
        ):
            repo = init_repo(self.base / f"preserve-{index}")
            # Install once so the installer's own files exist; this is what makes a second run the
            # interesting one (it has to distinguish its own output from a user edit).
            first = run_installer(repo)
            problems = []
            if first.returncode != 0:
                problems.append(f"the SETUP install failed: {first.stderr}")
            for path_rel, content in seed.items():
                path = repo / path_rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            before = (
                (repo / rel).read_text(encoding="utf-8")
                if (repo / rel).is_file()
                else None
            )

            proc = run_installer(repo, *flags)
            if proc.returncode != 0:
                problems.append(
                    f"the installer EXITED {proc.returncode}, not 0. A run that protects a file by "
                    f"failing is not protection; a user's CI sees the failure:\n{proc.stderr}"
                )
            after = (
                (repo / rel).read_text(encoding="utf-8")
                if (repo / rel).is_file()
                else None
            )

            if expected is None and not changes:
                if after is not None:
                    problems.append(
                        f"{rel} MUST NOT EXIST but holds {after[:120]!r}; the installer created a "
                        "file the user never asked for"
                    )
            elif expected is not None:
                if after != expected:
                    problems.append(
                        f"{rel} holds {after!r}, expected {expected!r}"
                        + (
                            " - THE USER'S OWN CONTENT WAS CLOBBERED"
                            if before == expected
                            else ""
                        )
                    )
            if changes and after == before:
                problems.append(
                    f"{rel} was NOT changed, and this row requires it to be. Content is still "
                    f"{after!r}"
                    + (
                        " - `--yes` means the user ASKED to be overwritten, so preserving here is a "
                        "bug, not caution"
                        if "--yes" in flags
                        else ""
                    )
                )
            elif not changes and expected is not None and after != before:
                problems.append(
                    f"{rel} changed from {before!r} to {after!r} when this row requires it "
                    "untouched"
                )
            # The user's own prose must survive on the rows where the file is legitimately rewritten.
            if changes and before and rel.endswith(".md") and "User" in (before or ""):
                if "User CLAUDE content" not in (after or ""):
                    problems.append(
                        "the user's own prose did not survive the block insertion; the managed block "
                        "must be ADDED to their file, never replace it"
                    )
            if problems:
                if "--yes" in flags:
                    exception_row_broken += 1
                wrong.append(
                    f"  {case} (flags {flags or '(none)'}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if exception_row_broken:
            vacuity = (
                " THE `--yes` ROW is among the failures, and while it is broken every preservation "
                "row here is nearly vacuous: an installer that overwrites NOTHING satisfies all of "
                "them, so check whether the installer has stopped writing at all before trusting the "
                "rest of this table."
            )
        self.assertEqual(
            wrong,
            [],
            f"the installer mishandled {len(wrong)} of {len(self.CASES)} pre-existing file states."
            f"{vacuity} All of these are decided by ONE question the installer asks per file, 'is "
            "this ours or theirs?', so read the failures together: if several PRESERVATION rows fail "
            "in the same direction, that decision regressed and a user's edits are being destroyed, "
            "which is the most serious defect this suite can report and is NOT recoverable from the "
            "user's side. If only the ABSENCE rows fail, the installer started creating native host "
            "files nobody asked for. If only the dry-run row fails, `--dry-run` is writing. FIX: "
            f"check the exit codes in the failures too, since a preserved file plus a non-zero exit "
            f"is a crash wearing protection's clothing.\n" + "\n".join(wrong),
        )

    def test_customization_detection_predicates(self):
        """Kept separate: pure-function claims about CONTENT, with no install and no repo.

        These decide the table above's outcomes but are not themselves an install: `is_shim_customized`
        judges content alone, and `is_shim_customized_vs_expected` compares two strings. Merging them
        into the install table would hide that the end-to-end behavior and the predicate can disagree.
        """
        # Genuinely hand-edited content is customized.
        self.assertTrue(
            INS.is_shim_customized(
                "---\ndescription: custom\n---\nSome user note here."
            )
        )
        # A shim carrying an older template format differs from the current expected content.
        old_template = (
            "---\ndescription: plan-review\nagent: build\n---\n"
            "Read and execute @.agents/workflows/plan-review\n"
            "Accept case-insensitive options..."
        )
        current_expected = (
            "---\ndescription: plan-review\nagent: build\n---\n"
            "Read and execute @.agents/workflows/plan-review-long\n"
            "Accept case-insensitive options..."
        )
        self.assertTrue(
            INS.is_shim_customized_vs_expected(old_template, current_expected)
        )

    def test_no_generated_shim_is_ever_flagged_as_customized(self):
        """Kept separate: a sweep over the WHOLE generated corpus, not a fixture pair.

        Every shim the real manifest generates must be judged ours by both predicates. This is a
        corpus-wide claim (dozens of files) whose value is exactly that it is exhaustive, so it cannot
        be a row.
        """
        shims = INS.generate_shim_members(
            INS.parse_manifest(SOURCE_WORKFLOWS), SOURCE_WORKFLOWS
        )
        offenders = []
        for rel, content in shims.items():
            if rel.endswith("README.md"):
                continue
            if INS.is_shim_customized_vs_expected(content, content):
                offenders.append(f"{rel} (vs-expected)")
            if INS.is_shim_customized(content):
                offenders.append(f"{rel} (fallback structural check)")
        self.assertEqual(
            offenders,
            [],
            "generated shims were flagged as user-customized, which would make the installer prompt "
            "about files it wrote itself:\n  " + "\n  ".join(offenders),
        )


class OverwritePromptTests(unittest.TestCase):
    """The interactive overwrite prompt: each answer's effect on the file and the exit code.

    ONE table replaces four tests (`test_ctrl_c_aborts_install`, `test_eof_declines_install`,
    `test_diff_option_re_prompts`, `test_invalid_input_reasks_then_overwrites`). Each patched
    `is_interactive_session` and `input`, installed once, customized a shim to force the prompt, called
    `main`, and asserted a return code plus whether the customization survived. The ANSWER SEQUENCE is
    the only difference, which is data.

    EVERY ROW ASSERTS THE FULL SAFETY PROPERTY, because this prompt is the last thing between a user's
    edit and its destruction: the exit code, whether the customized content SURVIVED, and (where the
    answer should produce feedback) a required needle in stdout. A row that checked only the return
    code would accept an abort that had already overwritten the file first.

    THE TWO NON-ANSWERS ARE THE POINT. `Ctrl-C` must PROPAGATE and abort the whole run with 130, while
    `EOF` declines just this file and continues with 0, and those are genuinely different contracts
    that only look alike. Sitting in one table, the difference is legible; as separate tests it was
    invisible that one exits non-zero and the other does not. The GARBAGE row is the third safety
    property: unrecognized input must RE-ASK rather than be coerced to a default, because coercing
    'wat' to 'no' silently changes a destructive prompt's meaning.
    """

    #: (case, the `input()` side effects, expected return code from `main`, whether the customized
    #: content must SURVIVE, stdout needles that must appear, why this row exists)
    ANSWERS = (
        (
            "Ctrl-C at the prompt",
            KeyboardInterrupt(),
            130,
            True,
            (),
            "an interrupt must PROPAGATE and abort the whole run with 130, NOT be caught and treated "
            "as a decline-and-continue. Both outcomes leave this file intact, which is why the exit "
            "code is the assertion that distinguishes them: a user who hits Ctrl-C wants the run "
            "STOPPED, and silently continuing would go on to overwrite the NEXT file",
        ),
        (
            "EOF at the prompt (a closed or piped stdin)",
            EOFError(),
            0,
            True,
            (),
            "EOF declines THIS file, which is the SAFE default, and the run continues normally with "
            "0. Contrast the row above: same surviving file, deliberately different exit code. This "
            "is the row that makes running the installer under a harness or a pipe safe rather than "
            "destructive",
        ),
        (
            "`d` (show diff) and then `n`",
            ["d", "n"],
            0,
            True,
            ("Diff:", "-Customized lines here"),
            "`d` is not an answer: it prints the diff and RE-PROMPTS, so the `n` that follows is what "
            "decides. The diff needles are required because the whole purpose of the option is "
            "showing the user what they would lose, and a `d` that silently re-prompted without "
            "printing would satisfy a code-only assertion",
        ),
        (
            "garbage (`wat`) and then `y`",
            ["wat", "y"],
            0,
            False,
            ("Unrecognized input",),
            "UNRECOGNIZED INPUT MUST RE-ASK, never be coerced to the default. Coercing 'wat' to 'no' "
            "sounds safe and is in fact the dangerous behavior, because the same coercion in a prompt "
            "whose default is yes destroys the file. This is also the only row where the content is "
            "EXPECTED to be replaced, since `y` is a real consent: it keeps the three rows above from "
            "being satisfied by a prompt that never overwrites anything",
        ),
    )

    CUSTOM = "Read and execute @.agents/workflows/assess.md\nCustomized lines here\n"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_prompt_answer_has_the_right_effect_and_exit_code(self):
        wrong = []
        consent_row_broken = 0
        for index, (case, side_effect, code, survives, needles, why) in enumerate(
            self.ANSWERS
        ):
            target = self.base / f"prompt-{index}"
            target.mkdir()
            run_installer(target)
            shim = target / ".opencode/commands/assess.md"
            shim.write_text(self.CUSTOM, encoding="utf-8")

            buf = io.StringIO()
            problems = []
            # The overwrite prompt only runs when the installer thinks it is in an interactive
            # session (engine.is_interactive_session). Under a test harness sys.stdin is not a TTY,
            # so interactivity must be forced on; otherwise the prompt is skipped, input() is never
            # called, and the mocked interrupt/choice is never exercised.
            with mock.patch(
                "agent_workflows.engine.is_interactive_session", return_value=True
            ):
                with mock.patch("builtins.input") as mock_input:
                    mock_input.side_effect = side_effect
                    with redirect_stdout(buf):
                        got = INS.main(["--repo", str(target)])
            output = buf.getvalue()

            if got != code:
                problems.append(
                    f"main returned {got!r}, expected {code!r}"
                    + (
                        " - an interrupt that returns 0 means the run CONTINUED past the user's "
                        "Ctrl-C and will overwrite the next file it is asked about"
                        if code == 130
                        else ""
                    )
                )
            content = shim.read_text(encoding="utf-8")
            preserved = "Customized lines here" in content
            if preserved != survives:
                problems.append(
                    "the customized content was DESTROYED, and this row requires it preserved"
                    if survives
                    else "the customized content SURVIVED, and this row requires it replaced "
                    "(the user answered `y`, which is explicit consent)"
                )
            for needle in needles:
                if needle not in output:
                    problems.append(
                        f"stdout does not contain {needle!r}, so the user got no feedback for this "
                        f"answer. Output was:\n{output[-400:]}"
                    )
            if problems:
                if not survives:
                    consent_row_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if consent_row_broken:
            vacuity = (
                " THE CONSENT ROW (garbage then `y`) is among the failures, and while it is broken "
                "the three preservation rows are nearly vacuous: a prompt that never overwrites "
                "anything satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the overwrite prompt mishandled {len(wrong)} of {len(self.ANSWERS)} answers.{vacuity} "
            "One prompt loop handles all four, so read the failures together: if every row's CONTENT "
            "expectation fails, the prompt is not being reached at all (check that the file really "
            "differs from the generated shim) or it stopped honoring answers; if only the exit codes "
            "move, the loop's control flow changed and Ctrl-C versus EOF have been conflated, which "
            "are deliberately different contracts. FIX: this prompt is the last thing between a "
            f"user's edit and its destruction, so a row whose content expectation fails is data "
            f"loss, not a UX regression.\n" + "\n".join(wrong),
        )


class SingleSourceOrchestratorTests(unittest.TestCase):
    """Structural anti-drift guard (D83): the single-repo `run()` path and the shared
    `install_into_repo` core must produce the SAME install result, because `run()` now drives
    `install_into_repo` for the steps instead of re-inlining a parallel sequence. If the two ever
    diverge (a step added to one path only), this test fails.

    Neither test here is a row: the first compares two whole file SETS produced by two different entry
    points, and the second asserts one key's presence in a returned dict.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def _tracked_files(repo: Path) -> set[str]:
        # Exclude .git/ and the installer's own timestamped backup scratch dir (its dir name is a
        # wall-clock stamp that legitimately differs between two runs a second apart; it is gitignored
        # churn, not part of the installed file set).
        out = set()
        for p in repo.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(repo).as_posix()
            if rel.startswith(".git/") or rel.startswith(
                ".agent-workflows-installer-backups/"
            ):
                continue
            out.add(rel)
        return out

    def test_run_and_install_into_repo_produce_same_fileset(self):
        source_root = SOURCE_WORKFLOWS

        # Path A: engine.run() from a parsed namespace (the install-workflows.py / `aw run` path).
        repo_a = init_repo(self.base / "a")
        args = INS.parse_args(["--repo", str(repo_a), "--yes", "--no-color"])
        self.assertEqual(INS.run(args), 0)

        # Path B: the shared install_into_repo core directly (the CLI path's engine call).
        repo_b = init_repo(self.base / "b")
        INS.install_into_repo(repo_b, source_root, yes=True, no_color=True)

        self.assertEqual(
            self._tracked_files(repo_a),
            self._tracked_files(repo_b),
            "engine.run() and install_into_repo() produced different file sets (orchestrator drift)",
        )

    def test_install_into_repo_returns_migrated_key(self):
        # cli._run_install reads result.get('migrated'); it must exist so the CLI summary can list
        # migrated files (parity with run()'s summary). Regression guard for the D83 fix.
        repo = init_repo(self.base / "m")
        result = INS.install_into_repo(repo, SOURCE_WORKFLOWS)
        self.assertIn("migrated", result)


class InstallCorrectnessTests(unittest.TestCase):
    """Regression tests for the D85 bug fixes (F4 exit code, F5 rollback completeness, F6 tag).

    Left un-merged on purpose: each drives a different failure mode with materially different setup (a
    nonexistent target, a rollback after install, a patched collaborator raising SystemExit, a
    deliberately corrupted JSON record), and two of them assert about an EXCEPTION rather than a value.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_run_returns_nonzero_when_a_repo_is_not_a_directory(self):
        # F4: run() must propagate its computed returncode, not hardcode 0. A nonexistent target is
        # skipped with returncode=1; the whole run must therefore exit non-zero.
        good = init_repo(self.base / "good")
        missing = self.base / "does-not-exist"
        args = INS.parse_args(
            ["--repo", str(good), str(missing), "--yes", "--no-color"]
        )
        self.assertEqual(INS.run(args), 1)

    def test_rollback_removes_create_setup_artifacts_files(self):
        # F5: files created by create_setup_artifacts (e.g. .gitleaksignore, .agents/comms/README.md)
        # must be recorded in .created-files.json so --undo removes them.
        repo = init_repo(self.base / "r")
        INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)
        gitleaks = repo / ".gitleaksignore"
        comms_readme = repo / ".aw" / "records" / "comms" / "README.md"
        self.assertTrue(gitleaks.is_file())
        self.assertTrue(comms_readme.is_file())
        INS.run_rollback(repo, no_color=True)
        self.assertFalse(
            gitleaks.exists(), "rollback left .gitleaksignore behind (F5 regression)"
        )
        self.assertFalse(
            comms_readme.exists(),
            "rollback left .aw/records/comms/README.md behind (F5 regression)",
        )

    def test_run_multi_repo_isolates_systemexit(self):
        # D85 P-2 (REL-001): engine.run()'s multi-repo loop must isolate a per-repo SystemExit so
        # one bad repo does not abort the whole `--repo A B` batch.
        good = init_repo(self.base / "good")
        other = init_repo(self.base / "other")
        args = INS.parse_args(["--repo", str(good), str(other), "--yes", "--no-color"])
        seen = []
        real = INS.install_into_repo

        def flaky(repo_root, *a, **k):
            seen.append(Path(repo_root).name)
            if Path(repo_root).name == "good":
                raise SystemExit("simulated dir-conflict in good")
            return real(repo_root, *a, **k)

        with mock.patch.object(INS, "install_into_repo", side_effect=flaky):
            rc = INS.run(args)
        self.assertEqual(
            sorted(seen), ["good", "other"], "batch did not continue past SystemExit"
        )
        self.assertEqual(rc, 1, "a repo failing must make run() return non-zero")
        self.assertTrue((other / ".aw/system/VERSION").is_file())

    def test_rollback_survives_corrupt_created_files_record(self):
        # D85 P-3 (REL-003): a corrupt .created-files.json must not crash run_rollback.
        import json

        repo = init_repo(self.base / "c")
        INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)
        # Corrupt the most recent record.
        backups = sorted(
            (repo / ".agent-workflows-installer-backups").glob("*/.created-files.json")
        )
        self.assertTrue(backups, "no created-files record written")
        backups[-1].write_text("{ this is not valid json", encoding="utf-8")
        # Must not raise.
        try:
            INS.run_rollback(repo, no_color=True)
        except json.JSONDecodeError as exc:  # the exact bug
            self.fail(f"run_rollback crashed on corrupt record: {exc}")


class PromptChoiceTests(unittest.TestCase):
    """The shared `prompt_choice` helper: each token in, one decision out (IPD 20260722-0040-01).

    ONE table replaces five tests (`test_yes_and_aliases`, `test_no_and_blank_default`,
    `test_invalid_then_valid_reasks_and_shows_legend`, `test_help_shows_legend_then_reasks`,
    `test_diff_invokes_callback_then_reasks`). Each fed a token sequence to one helper and asserted the
    returned choice plus, sometimes, what got printed. The token sequence is data.

    Why the table beats the five: these tokens are a CLOSED VOCABULARY (`accept` plus the built-in help
    and diff aliases plus the blank default), and the realistic regression is a change to the matching
    loop that moves several tokens at once, typically by tightening or loosening normalization. The
    rows distinguish the three outcomes a token can have (RETURN a decision, RE-ASK after printing the
    legend, INVOKE the diff callback and re-ask) rather than collapsing them, because 're-ask' is
    invisible in the return value alone: `['help', 'n']` and `['n']` both return `no`, and only the
    printed legend tells them apart.

    THE BLANK-INPUT ROW IS A SAFETY ROW. Blank must take the DEFAULT, which callers set to the
    conservative answer, so a change making blank re-ask forever would hang a piped install and a
    change making it the affirmative would overwrite on a stray newline.

    The two EXCEPTION tests stay separate, as does the callback-count test, and each says why.
    """

    LEGEND = ["  Y = yes", "  N = no", "  help = show help"]
    ACCEPT = {
        "y": "yes",
        "yes": "yes",
        "n": "no",
        "no": "no",
        "d": "diff",
        "diff": "diff",
    }

    #: (case, the input tokens, the expected returned choice, whether the "unrecognized" notice must
    #: be printed, whether the LEGEND must be printed, why this row exists)
    TOKENS = (
        (
            "`y`, the short affirmative",
            ["y"],
            "yes",
            False,
            False,
            "the single-character form users actually type. It must return IMMEDIATELY with no legend "
            "and no notice, because printing either on a valid answer is what trains users to stop "
            "reading the output",
        ),
        (
            "`yes`, the long affirmative",
            ["yes"],
            "yes",
            False,
            False,
            "the alias table maps several spellings to ONE decision value, so callers switch on the "
            "decision and never on the keystroke. Asserted beside `y` because a matching loop that "
            "compared only the first character would pass one and fail the other",
        ),
        (
            "`n`, the short negative",
            ["n"],
            "no",
            False,
            False,
            "the negative half of the same alias mapping; without it a helper that returned `yes` for "
            "everything would satisfy both rows above",
        ),
        (
            "blank input (a bare Return)",
            [""],
            "no",
            False,
            False,
            "THE SAFETY ROW: blank takes the DEFAULT, which callers set to the conservative answer. A "
            "change making blank re-ask instead would HANG a piped install forever, and one making it "
            "affirmative would overwrite a user's file on a stray newline",
        ),
        (
            "unrecognized input, then a valid answer",
            ["nonsense", "y"],
            "yes",
            True,
            True,
            "garbage must RE-ASK and show the legend, never be coerced to the default. Coercion "
            "sounds harmless and is the actual hazard: the same silent coercion in a prompt whose "
            "default is affirmative destroys a file on a typo",
        ),
        (
            "`help`, then an answer",
            ["help", "n"],
            "no",
            False,
            True,
            "help prints the legend and RE-ASKS, and crucially WITHOUT the unrecognized notice: `help` "
            "is a valid request, not a mistake. That distinction is the only thing separating this "
            "row from the one above, since both end up printing the legend and returning the second "
            "token's answer",
        ),
        (
            "`?`, the punctuation help alias",
            ["?", "n"],
            "no",
            False,
            True,
            "help has aliases users guess at. Each is its own row because they are separate entries in "
            "one matching branch, so a rewrite can easily keep `help` and drop the symbols",
        ),
        (
            "`h`, the single-letter help alias",
            ["h", "y"],
            "yes",
            False,
            True,
            "the third help alias, and the one at risk of colliding with a future accept-key. It "
            "returns through the SECOND token, which also shows the re-ask loop preserves the accept "
            "table across iterations",
        ),
        (
            "`d`, the diff option, then an answer",
            ["d", "y"],
            "yes",
            False,
            False,
            "`d` is in the accept table but behaves like help: it fires the diff callback and RE-ASKS "
            "rather than returning `diff`. Note it prints no legend, so this row also pins that the "
            "re-ask path does not always dump the legend",
        ),
    )

    def _choice(self, answers, **kw):
        it = iter(answers)
        printed = []
        kw.setdefault("default", "no")
        kw.setdefault("accept", self.ACCEPT)
        return (
            INS.prompt_choice(
                "q? ",
                self.LEGEND,
                input_fn=lambda _p: next(it),
                print_fn=lambda *a: printed.append(" ".join(str(x) for x in a)),
                **kw,
            ),
            printed,
        )

    def test_every_token_returns_or_reasks_correctly(self):
        wrong = []
        for case, tokens, expected, notice, legend, why in self.TOKENS:
            problems = []
            try:
                choice, printed = self._choice(tokens, on_diff=lambda: None)
            except StopIteration:
                problems.append(
                    "the helper consumed MORE input than the row supplies, so it re-asked when it "
                    "should have returned (an infinite re-ask loop looks exactly like this)"
                )
                choice, printed = None, []
            if choice != expected:
                problems.append(f"returned {choice!r}, expected {expected!r}")
            got_notice = any("Unrecognized input" in p for p in printed)
            if got_notice != notice:
                problems.append(
                    "printed the UNRECOGNIZED notice when this row requires it silent (a valid "
                    "request is not a mistake)"
                    if got_notice
                    else "did NOT print the unrecognized notice, so the user has no idea why they "
                    "were asked twice"
                )
            got_legend = any("show help" in p for p in printed)
            if got_legend != legend:
                problems.append(
                    f"legend printed={got_legend}, expected {legend}. Printed: {printed!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (tokens {tokens!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"prompt_choice mishandled {len(wrong)} of {len(self.TOKENS)} token sequences. One "
            "matching loop handles every row, so read them together: if the ALIAS rows fail while the "
            "single characters pass, normalization changed (case folding, stripping, or exact-match "
            "lookup); if the RE-ASK rows fail with a StopIteration the loop is asking again when it "
            "should return, which hangs a non-interactive install; if the blank row fails the "
            "conservative default is gone. FIX: this helper backs the destructive overwrite prompt, "
            f"so 'coerce anything unclear to the default' is NOT a safe simplification.\n"
            + "\n".join(wrong),
        )

    def test_eof_returns_default_no_loop(self):
        """Kept separate: the input function RAISES, so there is no token to put in a row."""

        def raise_eof(_p):
            raise EOFError

        self.assertEqual(
            INS.prompt_choice(
                "q? ",
                self.LEGEND,
                default="no",
                accept=self.ACCEPT,
                input_fn=raise_eof,
                print_fn=lambda *a: None,
            ),
            "no",
        )

    def test_keyboard_interrupt_propagates(self):
        """Kept separate: an assertRaises test. The claim is that NOTHING is returned at all."""

        def raise_kbi(_p):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            INS.prompt_choice(
                "q? ",
                self.LEGEND,
                default="no",
                accept=self.ACCEPT,
                input_fn=raise_kbi,
                print_fn=lambda *a: None,
            )

    def test_diff_callback_fires_exactly_once(self):
        """Kept separate: counts CALLBACK INVOCATIONS, a claim no return-value row can make.

        The `d` row above proves the diff option re-asks and returns the next answer; this proves the
        callback ran ONCE. A loop that fired it on every iteration would satisfy that row.
        """
        fired = []
        it = iter(["d", "y"])
        choice = INS.prompt_choice(
            "q? ",
            self.LEGEND,
            default="no",
            accept=self.ACCEPT,
            on_diff=lambda: fired.append(1),
            input_fn=lambda _p: next(it),
            print_fn=lambda *a: None,
        )
        self.assertEqual(choice, "yes")
        self.assertEqual(len(fired), 1)


class AwBlockParserWriterTests(unittest.TestCase):
    """CP1: the sectioned aw:block parser: what each document SHAPE parses to (IPD 20260723-1100-02).

    ONE table replaces four tests (`test_wellformed_multi_section_parse`,
    `test_missing_close_is_drift_not_rewrite`, `test_duplicate_wrapper_is_ambiguous`,
    `test_absent_block`). Each parsed one text and asserted some subset of the result's flags; the text
    is data.

    Why the table beats the four, and this is the important part: the three verdict flags (`found`,
    `drift`, `ambiguous`) are what DECIDE WHETHER THE INSTALLER REWRITES A USER'S FILE, and they are
    only meaningful as a combination. Well-formed means refresh in place; drift (an unclosed opener)
    means close it at EOF and refresh, which is non-destructive; ambiguous (duplicate wrappers) means
    NEVER rewrite, only append. Each old test asserted its own flag and left the others unstated, so a
    parser that set `ambiguous` on a well-formed document passed every one of them while making the
    installer stop managing healthy files. Every row here pins ALL THREE flags plus the section slugs
    and the preserved before/after text, so no combination can drift unobserved.

    THE PRESERVED TEXT IS IN EVERY ROW because it is the no-clobber property at parse level: whatever
    the verdict, the user's prose OUTSIDE the block must come back out of the parser intact, since that
    is what the writer puts back around the refreshed block.
    """

    #: (case, the text to parse, expected `found`, expected `drift`, expected `ambiguous`, expected
    #: section slugs, expected `before`, expected `after`, why this row exists)
    SHAPES = (
        (
            "a well-formed block with two sections and user prose on both sides",
            "user preamble\n\n"
            "<!-- aw:block -->\n"
            "<!-- aw:pointer -->\n"
            "pointer body line 1\n"
            "pointer body line 2\n"
            "<!-- aw:extra -->\n"
            "extra body\n"
            "<!-- /aw:block -->\n"
            "user epilogue\n",
            True,
            False,
            False,
            ["pointer", "extra"],
            "user preamble\n",
            "user epilogue",
            "THE HEALTHY SHAPE, and the row that keeps the three below honest: a parser that flagged "
            "everything as drifted or ambiguous would satisfy them all while refusing to manage any "
            "real file. It also pins that MULTIPLE sections are recognized in order and that prose on "
            "BOTH sides survives, which is what the writer needs to reassemble the file",
        ),
        (
            "an opener with no closing marker",
            "<!-- aw:block -->\n<!-- aw:pointer -->\nbody\n",
            True,
            True,
            False,
            ["pointer"],
            "",
            "",
            "DRIFT, NOT AMBIGUITY: an unclosed block is closed at EOF and refreshed in place, which is "
            "non-destructive and strictly better than the legacy append-a-duplicate behavior. The "
            "`ambiguous=False` column is the load-bearing one, because classifying this as ambiguous "
            "would leave the half-written block in the file forever",
        ),
        (
            "two complete blocks in one file",
            "<!-- aw:block -->\n<!-- aw:pointer -->\na\n<!-- /aw:block -->\n"
            "<!-- aw:block -->\n<!-- aw:pointer -->\nb\n<!-- /aw:block -->\n",
            True,
            False,
            True,
            [],
            "<!-- aw:block -->\n<!-- aw:pointer -->\na\n<!-- /aw:block -->\n"
            "<!-- aw:block -->\n<!-- aw:pointer -->\nb\n<!-- /aw:block -->\n",
            "",
            "AMBIGUOUS MEANS HANDS OFF, and this is the most safety-relevant row in the table: with "
            "two wrappers the parser cannot tell which one it owns, so it reports NO sections and "
            "hands the ENTIRE text back as `before` untouched. That is what makes the installer append "
            "instead of rewriting. A parser that picked the first block here would silently delete the "
            "second, which may be another tool's",
        ),
        (
            "a file with no block at all",
            "just user content\n",
            False,
            False,
            False,
            [],
            "just user content\n",
            "",
            "the fresh-file case, and it must be distinguishable from ambiguity by `found` alone, "
            "since both report zero sections. The user's whole file comes back as `before`, which is "
            "what the writer appends the new block to",
        ),
    )

    def test_every_document_shape_parses_to_the_right_verdict(self):
        wrong = []
        healthy_row_broken = 0
        for index, (
            case,
            text,
            found,
            drift,
            ambiguous,
            slugs,
            before,
            after,
            why,
        ) in enumerate(self.SHAPES):
            parsed = INS.parse_aw_block(text)
            problems = []
            for label, got, want in (
                ("found", parsed.found, found),
                ("drift", parsed.drift, drift),
                ("ambiguous", parsed.ambiguous, ambiguous),
            ):
                if got != want:
                    problems.append(
                        f"{label}={got}, expected {want}"
                        + (
                            " - AMBIGUOUS is what stops the installer rewriting a file it may not "
                            "own; getting it wrong either destroys a foreign block or abandons a "
                            "healthy one"
                            if label == "ambiguous"
                            else ""
                        )
                    )
            got_slugs = [s.slug for s in parsed.sections]
            if got_slugs != slugs:
                problems.append(f"sections {got_slugs!r}, expected {slugs!r}")
            if parsed.before != before:
                problems.append(
                    f"`before` is {parsed.before!r}, expected {before!r}; the user's prose outside "
                    "the block must survive the parse intact, because the writer puts exactly this "
                    "back"
                )
            if parsed.after != after:
                problems.append(f"`after` is {parsed.after!r}, expected {after!r}")
            if problems:
                if index == 0:
                    healthy_row_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if healthy_row_broken:
            vacuity = (
                " THE HEALTHY SHAPE is among the failures, and while it is broken the malformed rows "
                "are vacuous: a parser that reports every document as drifted or ambiguous satisfies "
                "them and stops managing real files."
            )
        self.assertEqual(
            wrong,
            [],
            f"parse_aw_block returned the wrong verdict for {len(wrong)} of {len(self.SHAPES)} "
            f"document shapes.{vacuity} One scanning loop produces all three flags, so read the "
            "failures together: if several rows' flags move at once the scan's state tracking "
            "changed, not the individual verdicts. FIX: these flags decide WHETHER A USER'S FILE IS "
            "REWRITTEN. `ambiguous` wrongly False on the duplicate-wrapper row means the installer "
            "will rewrite a file containing a block it does not own; `drift` wrongly True on the "
            f"healthy row means it rewrites correct files on every run.\n"
            + "\n".join(wrong),
        )

    def test_writer_round_trips_and_is_byte_stable(self):
        """Kept separate: a round-trip through the WRITER, plus a re-render byte-equality check.

        The parse table's subject is text in, verdict out. This is the inverse direction and its second
        assertion is an idempotence claim (re-rendering parsed sections reproduces the same bytes),
        which is what makes a reinstall an empty diff.
        """
        sections = [
            INS.AwSection(slug="pointer", lines=["line a", "line b"]),
            INS.AwSection(slug="extra", lines=["x"]),
        ]
        rendered = INS.render_aw_block(sections)
        parsed = INS.parse_aw_block(rendered)
        self.assertEqual([s.slug for s in parsed.sections], ["pointer", "extra"])
        self.assertEqual(parsed.sections[0].body, "line a\nline b")
        self.assertEqual(parsed.sections[1].body, "x")
        # Re-render is byte-stable (idempotent).
        self.assertEqual(INS.render_aw_block(parsed.sections), rendered)

    def test_foreign_text_preserved_around_block(self):
        """Kept separate: builds the text from the WRITER's own output rather than a literal fixture."""
        sections = [INS.AwSection(slug="pointer", lines=["managed"])]
        text = "BEFORE\n\n" + INS.render_aw_block(sections) + "AFTER\n"
        parsed = INS.parse_aw_block(text)
        self.assertEqual(parsed.before, "BEFORE\n")
        self.assertEqual(parsed.after, "AFTER")


class AwBlockCommentStyleTests(unittest.TestCase):
    """The comment STYLE is per-file syntax, and the two styles must not cross-match.

    ONE table replaces the style halves of `test_hash_comment_style_rendering_and_parse`,
    `test_strip_is_style_aware_no_cross_match` and
    `test_strip_managed_block_is_markdown_only_today`, whose overlap was substantial and whose
    disagreement was confusing: one of them pinned a CHARACTERIZATION baseline ("markdown-only today")
    that CP3 has since superseded, so the tree carried a test asserting the opposite of its neighbour.
    The live contract is that each style matches ITSELF and NOT the other.

    THE CROSS-MATCH ROWS ARE THE SAFETY ROWS. `.gitignore` carries a `#`-commented block and `AGENTS.md`
    carries a bare Markdown one. If the Markdown stripper matched the hash form it would tear
    commented lines out of a user's `.gitignore`, and if the hash stripper matched Markdown it would
    strip a managed block from prose. Both are silent data loss, so the table asserts each style
    returns None for the other's text rather than merely that it works on its own.
    """

    HASH_BLOCK = (
        "keep\n# <!-- aw:block -->\n# <!-- aw:untracked -->\n*.untracked.*\n"
        "# <!-- /aw:block -->\n"
    )
    MD_BLOCK = "keep\n<!-- aw:block -->\n<!-- aw:pointer -->\nx\n<!-- /aw:block -->\n"

    #: (case, the text, the style to use or None for the DEFAULT, whether a strip must SUCCEED, why)
    STYLES = (
        (
            "a #-styled block stripped with the HASH style",
            HASH_BLOCK,
            "hash",
            True,
            "the matching case for a `#`-comment file such as `.gitignore`: the block goes and the "
            "user's own `keep` line stays, which is the whole no-clobber requirement for a file the "
            "user also edits by hand",
        ),
        (
            "a #-styled block offered to the MARKDOWN style",
            HASH_BLOCK,
            "markdown",
            False,
            "A CROSS-MATCH MUST FAIL CLOSED, returning None rather than a partial strip. If the "
            "Markdown stripper matched `# <!-- aw:block -->` it would tear commented lines out of a "
            "user's `.gitignore`, which is silent data loss in a file that governs what gets committed",
        ),
        (
            "a Markdown block stripped with the MARKDOWN style",
            MD_BLOCK,
            "markdown",
            True,
            "the matching case for prose files (`AGENTS.md`, `CLAUDE.md`), where the markers are bare "
            "HTML comments",
        ),
        (
            "a Markdown block offered to the HASH style",
            MD_BLOCK,
            "hash",
            False,
            "the inverse cross-match, asserted because the two matchers are separate patterns and a "
            "rewrite can easily make one of them permissive about the leading `# `. Having both "
            "directions is what pins mutual exclusion rather than one-way strictness",
        ),
        (
            "a Markdown block with NO style argument",
            MD_BLOCK,
            None,
            True,
            "THE DEFAULT IS MARKDOWN, which matters because most callers omit the argument. A "
            "characterization test in the tree used to assert the stripper was 'markdown-only today', "
            "which CP3 superseded when it added the style parameter; this row is what that test "
            "becomes: the default did not change, the capability was ADDED",
        ),
    )

    def test_each_style_matches_itself_and_never_the_other(self):
        wrong = []
        for case, text, style, succeeds, why in self.STYLES:
            kwargs = {}
            if style == "hash":
                kwargs["style"] = INS.AW_STYLE_HASH
            elif style == "markdown":
                kwargs["style"] = INS.AW_STYLE_MARKDOWN
            got = INS._strip_managed_block(text, **kwargs)
            problems = []
            if succeeds:
                if got is None:
                    problems.append(
                        "the strip returned None, so the installer cannot remove its own block from "
                        "this file and an uninstall would leave it behind"
                    )
                else:
                    if "aw:block" in got:
                        problems.append(
                            f"the block markers survived the strip: {got!r}"
                        )
                    if "keep" not in got:
                        problems.append(
                            f"THE USER'S OWN LINE WAS REMOVED along with the block: {got!r}"
                        )
            elif got is not None:
                problems.append(
                    f"the strip SUCCEEDED across styles and returned {got!r}; it must fail closed "
                    "with None, because a cross-style match edits a file whose syntax it has "
                    "misidentified"
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
            f"_strip_managed_block mishandled {len(wrong)} of {len(self.STYLES)} style combinations. "
            "One function takes the style as a parameter, so read the failures together: if both "
            "CROSS-MATCH rows fail the styles have been unified into one permissive pattern, which is "
            "the dangerous direction; if both MATCHING rows fail the marker rendering changed and no "
            "existing install can be cleaned up. FIX: these two styles exist because `.gitignore` "
            f"needs commented markers and prose files must not show them, so unifying them is not a "
            f"simplification available here.\n" + "\n".join(wrong),
        )

    def test_hash_style_renders_and_round_trips(self):
        """Kept separate: the RENDER direction, and it asserts the patterns are emitted BARE.

        The strip table above consumes text; this produces it, and its load-bearing claim is a layout
        one: the markers are `#`-commented but the ignore patterns must NOT be, or git would not apply
        them. That is not a style-matching claim.
        """
        rendered = INS.render_aw_block(
            INS.untracked_safety_sections(), style=INS.AW_STYLE_HASH
        )
        self.assertIn("# <!-- aw:block -->", rendered)
        self.assertIn("# <!-- aw:untracked -->", rendered)
        self.assertIn("# <!-- /aw:block -->", rendered)
        self.assertIn("DO NOT REMOVE", rendered)
        for pat in INS.UNTRACKED_PATTERNS:
            # Patterns are emitted BARE (not #-commented) so git actually applies them.
            self.assertIn("\n" + pat + "\n", rendered)
        parsed = INS.parse_aw_block(rendered, style=INS.AW_STYLE_HASH)
        self.assertEqual([s.slug for s in parsed.sections], ["untracked"])
        # And the Markdown style must NOT see the #-prefixed markers.
        self.assertFalse(
            INS.parse_aw_block(rendered, style=INS.AW_STYLE_MARKDOWN).found
        )

    def test_untracked_patterns_are_the_three_approved(self):
        """Kept separate: a byte-pinned constant. The whole value is that it cannot drift silently."""
        self.assertEqual(
            INS.UNTRACKED_PATTERNS, ("*.untracked.*", "*.untracked", "**/*untracked*/")
        )


class LegacyPointerMergeTests(unittest.TestCase):
    """`merge_pointer_block`: one action per pre-existing file shape, and a foreign block untouched.

    ONE table replaces `test_merge_actions_new_existing_refreshed_malformed`, which asserted four
    actions in one method with no way to tell which broke, plus the sibling-block claim that was
    duplicated across two classes (`test_sibling_named_block_is_untouched_by_merge` and
    `test_pointer_block_is_wrapped_in_current_markers`).

    Every row asserts the ACTION NAME, the resulting marker COUNT, and that the user's own text
    survived. The count is what separates safe behavior from destruction: `refreshed` must keep exactly
    ONE marker pair (an in-place replace), while `malformed` must produce TWO, because a lone `BEGIN`
    is ambiguous and appending is the only non-destructive option. Asserting the action alone would
    accept a `refreshed` that appended a duplicate, and asserting the count alone would accept a
    `malformed` that overwrote the user's half-written block.

    THE FOREIGN-BLOCK ROW IS THE M9 INVARIANT: an unrelated `AGENT-PLANS:BEGIN/END` block belonging to
    another tool must be BYTE-IDENTICAL afterwards. It is in this table rather than its own test
    because it is the same function call with a different pre-existing file, which is exactly what a
    row is.
    """

    BEGIN = "<!-- AGENT-WORKFLOWS:BEGIN -->"
    END = "<!-- AGENT-WORKFLOWS:END -->"
    SIBLING = (
        "<!-- AGENT-PLANS:BEGIN -->\n"
        "## Agent plans\nsome plan policy text\n"
        "<!-- AGENT-PLANS:END -->\n"
    )

    def test_every_pre_existing_shape_gets_the_right_merge_action(self):
        block = INS.agents_pointer_block()
        #: (case, the existing file text, extra kwargs, expected action, expected BEGIN-marker count,
        #: text that must survive verbatim, why this row exists)
        cases = (
            (
                "an empty file with a default header supplied",
                "",
                {"default_header": "# AGENTS"},
                "new",
                1,
                "# AGENTS",
                "the fresh case: the header is written and the block follows. `new` versus `existing` "
                "is what the installer's summary reports to the user, so the names are part of the "
                "contract and not internal labels",
            ),
            (
                "a file with user content and no markers",
                "User stuff\n",
                {},
                "existing",
                1,
                "User stuff",
                "APPEND, NEVER REPLACE: a file the installer has never touched keeps everything it "
                "had and gains the block. This is the row a naive 'write the managed file' "
                "implementation fails by truncating the user's AGENTS.md",
            ),
            (
                "a file already carrying exactly one well-formed pair",
                "User stuff\n" + block,
                {},
                "refreshed",
                1,
                "User stuff",
                "IN-PLACE REPLACE, and the count is the assertion that matters: still exactly ONE "
                "pair. A refresh that appended instead would double the block on every install, which "
                "is what makes reinstalls a non-empty diff and eventually an unreadable file",
            ),
            (
                "a file with a lone BEGIN and no END",
                "Prose\n" + self.BEGIN + "\n",
                {},
                "malformed",
                2,
                "Prose\n" + self.BEGIN,
                "SAFE APPEND ON AMBIGUITY: with no closing marker the extent of the old block is "
                "unknowable, so the count DELIBERATELY becomes 2 and the user's half-written marker "
                "is left exactly where it was. Guessing the extent here would delete whatever follows "
                "the opener",
            ),
            (
                "a file carrying a FOREIGN tool's named block plus ours",
                "# AGENTS\n\n" + self.SIBLING + "\n" + block,
                {},
                "refreshed",
                1,
                self.SIBLING,
                "THE M9 INVARIANT: an `AGENT-PLANS:BEGIN/END` block belongs to another tool and must "
                "come out BYTE-IDENTICAL. The marker grammar is shared, so a matcher keyed on "
                "`:BEGIN` rather than on our exact name would rewrite or delete a neighbour's managed "
                "content, and the affected tool would have no way to know",
            ),
        )
        wrong = []
        for case, existing, kwargs, action, count, survives, why in cases:
            text, got_action = INS.merge_pointer_block(existing, block, **kwargs)
            problems = []
            if got_action != action:
                problems.append(f"action was {got_action!r}, expected {action!r}")
            got_count = text.count(self.BEGIN)
            if got_count != count:
                problems.append(
                    f"{got_count} `{self.BEGIN}` marker(s), expected {count}"
                    + (
                        " - a refresh that adds a pair doubles the block on EVERY install"
                        if count == 1 and got_count > 1
                        else ""
                    )
                )
            if survives not in text:
                problems.append(
                    f"{survives!r} did not survive the merge; the user's own content (or another "
                    "tool's block) was destroyed"
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
            f"merge_pointer_block mishandled {len(wrong)} of {len(cases)} pre-existing file shapes. "
            "One function decides all five by inspecting the markers, so read the failures together: "
            "if the ACTIONS are right and the COUNTS wrong, the decision is fine and the writing is "
            "not (usually append-versus-replace inverted); if the SURVIVES column fails anywhere, the "
            "merge is truncating a user's file, which is the most destructive outcome available here "
            "and is not recoverable from the user's side. FIX: `malformed` producing 2 markers is "
            f"CORRECT and must not be 'fixed' to 1; the ambiguity is real and appending is the only "
            f"safe response.\n" + "\n".join(wrong),
        )

    def test_the_pointer_block_carries_its_human_visible_anchors(self):
        """Kept separate: a content claim about the generated block itself, not about a merge."""
        block = INS.agents_pointer_block()
        self.assertTrue(block.lstrip().startswith(self.BEGIN))
        self.assertIn(self.END, block)
        # Human-visible anchors that must survive any marker migration (content, not markers).
        self.assertIn("## Agent workflows", block)
        self.assertIn("Inter-agent comms", block)


class UntrackedGitignoreInstallTests(unittest.TestCase):
    """CP2/CP3: the untracked-safety block in the target's ROOT `.gitignore`, install and uninstall.

    ONE table replaces six tests (`test_install_writes_untracked_block_preserving_user_lines`,
    `test_install_creates_gitignore_if_absent`, `test_reinstall_is_empty_diff`,
    `test_install_adds_untracked_block_cp2`, `test_uninstall_strips_gitignore_block_preserving_user_lines`,
    `test_uninstall_noop_when_no_gitignore_block`). Two of those were near-duplicates in different
    classes (one a CP0 characterization, one the live CP2 assertion) making the same claim about the
    same call.

    The column that bought the merge is the ROOT FILE'S PRIOR STATE (absent, user lines, already
    installed, block removed by hand) and the OPERATION (install or uninstall), because the property is
    one property in every case: the framework's block is managed and THE USER'S OWN LINES ARE NEVER
    TOUCHED. Every row asserts both halves, and the uninstall rows additionally assert the block is
    gone, so no row can pass by leaving the file alone entirely.

    THIS IS THE USER'S OWN FILE, which is why it is treated as a preservation table and not a
    formatting one: `.gitignore` is hand-edited by humans, it is usually committed, and the installer
    writes into it. A regression here does not merely misconfigure the framework, it damages a file the
    user wrote.
    """

    #: (case, the root .gitignore content to place first or None for no file, the operation
    #: ('install', 'install-twice', 'uninstall'), whether the framework block must be PRESENT after,
    #: the user lines that must survive, why this row exists)
    STATES = (
        (
            "a user's existing .gitignore with their own lines",
            "node_modules/\n*.log\n",
            "install",
            True,
            ("node_modules/", "*.log"),
            "THE CORE CLAIM: the block is ADDED and every line the user wrote survives. `.gitignore` "
            "is hand-authored and committed, so clobbering it is damage to the user's own work, not a "
            "framework misconfiguration",
        ),
        (
            "no .gitignore at all",
            None,
            "install",
            True,
            (),
            "the file is CREATED when absent, which is the one case with no user content to protect. "
            "It is in the table so the create and append branches are asserted side by side; an "
            "implementation that only appended would silently skip protection in a fresh repo",
        ),
        (
            "an already-installed repo, installed again",
            "node_modules/\n",
            "install-twice",
            True,
            ("node_modules/",),
            "IDEMPOTENCE, asserted as a byte comparison of the whole file between the two runs: the "
            "second install must be an EMPTY DIFF. Duplicated patterns are harmless to git but they "
            "grow on every run and they dirty a tracked file, which then has to be committed",
        ),
        (
            "an installed repo being uninstalled",
            "node_modules/\n*.log\n",
            "uninstall",
            False,
            ("node_modules/", "*.log"),
            "THE INVERSE, and the real reason the markers exist: uninstall removes the framework's "
            "block and leaves the user with exactly the file they had. A stripper that took the whole "
            "file, or that left the markers behind, would both pass an 'aw:untracked is gone' check "
            "on its own",
        ),
        (
            "an installed repo whose block a user deleted by hand, then uninstalled",
            "node_modules/\n",
            "uninstall-after-manual-removal",
            False,
            ("node_modules/",),
            "a NO-OP must be reported rather than attempted: with no block present there is nothing "
            "to strip, and the uninstall must say so instead of rewriting the file. This is the row "
            "that catches an unconditional rewrite, which would be invisible in the row above where a "
            "rewrite and a strip look the same",
        ),
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_users_gitignore_is_managed_without_being_clobbered(self):
        wrong = []
        for index, (
            case,
            initial,
            operation,
            block_present,
            user_lines,
            why,
        ) in enumerate(self.STATES):
            repo = init_repo(self.base / f"gi-{index}")
            gi = repo / ".gitignore"
            if initial is not None:
                gi.write_text(initial, encoding="utf-8")
            problems = []

            INS.install_into_repo(repo, self.source, yes=True, no_color=True)
            actions = []
            if operation == "install-twice":
                first = gi.read_text(encoding="utf-8")
                INS.install_into_repo(repo, self.source, yes=True, no_color=True)
                if gi.read_text(encoding="utf-8") != first:
                    problems.append(
                        "a second install CHANGED the file, so a reinstall is not an empty diff; "
                        "the patterns or the block are being re-appended"
                    )
            elif operation == "uninstall":
                actions = INS.uninstall_repo(repo, use_git=True)
            elif operation == "uninstall-after-manual-removal":
                # The user hand-wrote a plain .gitignore after install, deleting the block.
                gi.write_text(initial or "", encoding="utf-8")
                actions = INS.uninstall_repo(repo, use_git=True)
                if not any(
                    "nothing removed" in a for a in actions if ".gitignore" in a
                ):
                    problems.append(
                        "the uninstall did not report a NO-OP for .gitignore; with no block present "
                        f"there is nothing to strip and it must not rewrite the file. Actions: "
                        f"{[a for a in actions if '.gitignore' in a]!r}"
                    )

            text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
            if block_present:
                for needle in ("# <!-- aw:block -->", "# <!-- aw:untracked -->"):
                    if needle not in text:
                        problems.append(f"the managed block is missing {needle!r}")
                missing_patterns = [p for p in INS.UNTRACKED_PATTERNS if p not in text]
                if missing_patterns:
                    problems.append(
                        f"the untracked patterns {missing_patterns!r} are absent, so the safety "
                        "valve the whole convention rests on is not installed"
                    )
            else:
                for needle in ("aw:untracked", "# <!-- aw:block -->"):
                    if needle in text:
                        problems.append(
                            f"{needle!r} survived the uninstall, so the framework left its markers "
                            "in the user's file"
                        )
            for line in user_lines:
                if line not in text:
                    problems.append(
                        f"THE USER'S OWN LINE {line!r} IS GONE. Final file:\n{text[:400]}"
                    )
            if problems:
                wrong.append(
                    f"  {case} ({operation}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the root .gitignore was mishandled in {len(wrong)} of {len(self.STATES)} states. The "
            "install and uninstall sides share the marker grammar and one strip helper, so read the "
            "failures together: if the USER LINES column fails anywhere, the installer is rewriting "
            "a hand-authored, committed file wholesale, which is the worst outcome here; if only the "
            "idempotence row fails, the append branch stopped checking for an existing block; if only "
            "the no-op row fails, uninstall rewrites unconditionally. FIX: the user's `.gitignore` is "
            f"THEIRS, and the framework owns only what is inside its markers.\n"
            + "\n".join(wrong),
        )

    def test_the_installed_patterns_really_do_make_git_ignore_files(self):
        """Kept separate: the END-TO-END effect against real git, not the file's text.

        Every row above reads the `.gitignore`; this one proves the patterns WORK, which is a different
        claim and the only one that would catch a correctly-written pattern that git does not apply
        (for instance one emitted `#`-commented).
        """
        repo = init_repo(self.base / "eff")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        (repo / "secret.untracked.md").write_text("nope", encoding="utf-8")
        (repo / "scratch.untracked").write_text("nope", encoding="utf-8")
        (repo / "notes-untracked").mkdir()
        (repo / "notes-untracked" / "x.md").write_text("nope", encoding="utf-8")
        ignored = git(repo, "status", "--porcelain", "--ignored").stdout
        visible = git(repo, "status", "--porcelain").stdout
        self.assertNotIn("secret.untracked.md", visible)
        self.assertIn("secret.untracked.md", ignored)

    def test_manifest_records_untracked_section(self):
        """Kept separate: the subject is the MANIFEST json, not the .gitignore."""
        import json

        repo = init_repo(self.base / "man")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        raw = json.loads(
            (repo / ".aw/system/managed-sections.json").read_text(encoding="utf-8")
        )
        self.assertIn(".gitignore#aw:untracked", raw["files"])


class TrackingWarningScanTests(unittest.TestCase):
    """CP4: warn_tracking_and_scan notice + already-tracked scan (IPD 03).

    Left un-merged: the three install-capturing tests assert over CAPTURED STDOUT with materially
    different repo setups (a clean repo, a repo with a force-added tracked file), and the fourth calls a
    helper on a NON-GIT directory, which is a different precondition entirely.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def _install_capture(self, repo):
        buf = io.StringIO()
        with redirect_stdout(buf):
            INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        return buf.getvalue()

    def test_notice_prints_with_safety_valves(self):
        repo = init_repo(self.base / "notice")
        out = self._install_capture(repo)
        self.assertIn("git-tracks IPDs, prompts, and research by default", out)
        self.assertIn(".agents/prompts/untracked/", out)
        self.assertIn("untracked", out)

    def test_clean_repo_has_no_per_file_warning(self):
        """The NEGATIVE half of the scan: a clean repo must not be warned at."""
        repo = init_repo(self.base / "clean")
        out = self._install_capture(repo)
        self.assertNotIn("ALREADY git-tracked", out)

    def test_already_tracked_match_is_flagged_with_remedy(self):
        repo = init_repo(self.base / "tracked")
        # Commit a file matching the untracked pattern BEFORE install adds the .gitignore block,
        # then force-add it so it is tracked despite the pattern.
        (repo / "leak.untracked.md").write_text("oops", encoding="utf-8")
        git(repo, "add", "-f", "leak.untracked.md")
        git(repo, "commit", "-m", "add tracked untracked-named file")
        out = self._install_capture(repo)
        self.assertIn("ALREADY git-tracked", out)
        self.assertIn("leak.untracked.md", out)
        self.assertIn("git rm --cached", out)

    def test_scan_helper_non_git_safe(self):
        """Kept separate: the precondition is the ABSENCE of a git repo, which no install row has."""
        nogit = self.base / "plain"
        nogit.mkdir()
        self.assertEqual(INS._already_tracked_untracked_matches(nogit), [])


class DeepCleanupTests(unittest.TestCase):
    """CP3: plan_deep_cleanup / run_deep_cleanup (IPD 04).

    Left un-merged, and deliberately so: these are the most destructive operations in the codebase
    (they DELETE user files), and each test fences a different containment property with materially
    different setup. Tabulating them would mean a single row whose failure message mixed 'planned the
    wrong set' with 'deleted the wrong file', and the second is unrecoverable. The one thing they share
    (a committed install) is a helper, not a table.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def _install_commit(self, repo):
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "install")

    def test_plan_counts_and_all_recoverable_when_committed(self):
        """Everything committed means nothing is at risk, so the warning stays SOFT.

        PRE-EXISTING FAILURE, NOT INTRODUCED BY THE TABLE WORK, and kept rather than weakened:
        verified failing at HEAD (commit 6123749b) before this file was touched. The install now emits
        `.aw/workflow-artifacts/README.md`, which is GITIGNORED by design (D92), so `git add -A` cannot
        commit it and `plan_deep_cleanup` correctly classifies it as untracked and therefore at-risk,
        which makes `all_recoverable` False. Either the product should exclude its own gitignored
        run-scratch README from the at-risk set, or this expectation should change; that is a
        maintainer call about `agent_workflows/`, which this test-only change must not make. Deleting
        the assertion would have hidden the question, so it stays as written.
        """
        repo = init_repo(self.base / "r")
        self._install_commit(repo)
        # Add a user IPD under plans and commit it (recoverable).
        (repo / ".aw/records/plans/pending/my.md").write_text(
            "mine\n", encoding="utf-8"
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "user ipd")
        plan = INS.plan_deep_cleanup(repo)
        self.assertFalse(plan.is_empty)
        self.assertIn(".aw/records/plans", plan.counts)
        self.assertTrue(
            plan.all_recoverable, "all committed -> nothing at risk (soft warning)"
        )

    def test_untracked_file_is_at_risk(self):
        """An untracked file is UNRECOVERABLE if deleted, so the plan must say so before consent."""
        repo = init_repo(self.base / "a")
        self._install_commit(repo)
        (repo / ".aw/records/research/scratch.md").write_text("x\n", encoding="utf-8")
        plan = INS.plan_deep_cleanup(repo)
        self.assertIn(".aw/records/research/scratch.md", plan.at_risk)
        self.assertFalse(plan.all_recoverable)

    def test_run_removes_only_planned_files_and_prunes_dirs(self):
        repo = init_repo(self.base / "x")
        self._install_commit(repo)
        # A file OUTSIDE the scaffolding must be untouched.
        (repo / "keep_me.py").write_text("code\n", encoding="utf-8")
        plan = INS.plan_deep_cleanup(repo)
        INS.run_deep_cleanup(repo, plan, use_git=True)
        self.assertFalse(
            (repo / ".aw/records/plans").exists(), "planned scaffolding removed"
        )
        self.assertTrue(
            (repo / "keep_me.py").is_file(), "non-scaffolding file untouched"
        )

    def test_run_never_touches_paths_outside_plan(self):
        """THE CONTAINMENT PROPERTY: the plan is a whitelist, not a hint."""
        repo = init_repo(self.base / "s")
        self._install_commit(repo)
        plan = INS.plan_deep_cleanup(repo)
        # Craft a plan with a single file; run must remove only it.
        one = plan.files[0]
        single = INS.DeepCleanupPlan(files=[one], counts={}, at_risk=[])
        INS.run_deep_cleanup(repo, single, use_git=True)
        self.assertFalse((repo / one).is_file())
        # Another planned-but-not-in-single file still exists.
        others = [f for f in plan.files if f != one and (repo / f).is_file()]
        self.assertTrue(others, "files outside the single-file plan are untouched")

    def test_deep_cleanup_detects_and_removes_stale_workflows_litter(self):
        """E-04 & V-04: uninstall --deep reaches .agents/workflows litter, flags untracked at-risk, and removes on consent."""
        repo = init_repo(self.base / "litter_repo")
        self._install_commit(repo)

        # Plant untracked stale litter under .agents/workflows/
        litter_pyc = repo / ".agents" / "workflows" / "foo" / "__pycache__" / "x.pyc"
        litter_pyc.parent.mkdir(parents=True, exist_ok=True)
        litter_pyc.write_bytes(b"\x00\x01\x02")

        tools_dir = repo / ".agents" / "workflows" / "foo" / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)

        plan = INS.plan_deep_cleanup(repo)
        self.assertIn(".agents/workflows", plan.counts)
        self.assertIn(".agents/workflows/foo/__pycache__/x.pyc", plan.files)
        self.assertIn(
            ".agents/workflows/foo/__pycache__/x.pyc",
            plan.at_risk,
            "untracked litter must be flagged at-risk",
        )
        self.assertFalse(plan.all_recoverable)

        # Execute deep cleanup
        INS.run_deep_cleanup(repo, plan, use_git=True)
        self.assertFalse(
            litter_pyc.exists(), "deep cleanup must delete stale litter pyc"
        )
        self.assertFalse(tools_dir.exists(), "deep cleanup must prune empty tools dir")
        self.assertFalse(
            (repo / ".agents" / "workflows").exists(),
            "deep cleanup must prune empty workflows root",
        )

    def test_uninstall_without_deep_preserves_stale_workflows_litter(self):
        """E-04 & V-04: the PAIRED inverse of the test above; a plain uninstall must not reach litter."""
        repo = init_repo(self.base / "std_uninst")
        self._install_commit(repo)

        litter_pyc = repo / ".agents" / "workflows" / "foo" / "__pycache__" / "x.pyc"
        litter_pyc.parent.mkdir(parents=True, exist_ok=True)
        litter_pyc.write_bytes(b"\x00\x01\x02")

        tools_dir = repo / ".agents" / "workflows" / "foo" / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)

        INS.uninstall_repo(repo, use_git=True)
        self.assertTrue(
            litter_pyc.is_file(),
            "normal uninstall must NOT touch .agents/workflows litter",
        )
        self.assertTrue(tools_dir.is_dir(), "normal uninstall must NOT prune tools dir")


class UninstallApplyTests(unittest.TestCase):
    """CP1/CP2: `plan_uninstall` classification and `uninstall_repo` applying the plan.

    ONE table replaces the DRIFT-DISPOSITION cluster: `test_force_removes_drifted`,
    `test_drift_decider_choice_honored`, and the edited-shim half of
    `test_uninstall_removes_manifest_last_and_preserves_edited_shim`. All three edited a shim and
    uninstalled with a different consent mode; the mode is the data.

    THIS IS A NO-CLOBBER TABLE, so every row asserts the file's CONTENT and not merely its existence: a
    preserved file whose bytes were rewritten is not preserved. The default row is the important one
    (an edited file SURVIVES with its exact content), and `--force` is the deliberate exception that
    keeps the table from being satisfiable by an uninstall that deletes nothing.

    THE DECIDER ROW carries two files at once, one chosen for removal and one kept, because a
    per-file callback that ignored its argument and applied one answer to everything would satisfy any
    single-file row.

    The classification and manifest-shape tests stay separate; each says why.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_consent_mode_disposes_of_a_drifted_file_correctly(self):
        #: (case, uninstall kwargs, {shim rel: (content to write, must SURVIVE)}, why this row exists)
        cases = (
            (
                "default uninstall, one edited shim",
                {},
                {".opencode/commands/advise.md": ("MY EDIT\n", True)},
                "THE CORE NO-CLOBBER PROPERTY of uninstall: a file the user edited is PRESERVED, with "
                "its exact bytes. Uninstall is the operation with the least user attention on it, so "
                "the safe default matters more here than anywhere: the user is walking away and will "
                "not notice what was taken",
            ),
            (
                "--force, one edited shim",
                {"force": True},
                {".opencode/commands/advise.md": ("MY EDIT\n", False)},
                "THE DELIBERATE EXCEPTION: `--force` is the user asking for a clean sweep, so the "
                "edited file goes. Without this row an uninstall that removed NOTHING would satisfy "
                "every preservation row here",
            ),
            (
                "a per-file decider choosing remove for one and keep for another",
                {"drift_decider": lambda rel: "remove" if "advise" in rel else "keep"},
                {
                    ".opencode/commands/advise.md": ("EDIT A\n", False),
                    ".opencode/commands/verify.md": ("EDIT B\n", True),
                },
                "TWO FILES IN ONE ROW on purpose: the decider is consulted PER FILE, so a callback "
                "that ignored its argument and applied one answer to everything would pass any "
                "single-file row. This is also the interactive path's contract, where each answer "
                "must bind to the file it was asked about",
            ),
        )
        wrong = []
        exception_broken = 0
        for index, (case, kwargs, shims, why) in enumerate(cases):
            repo = init_repo(self.base / f"drift-{index}")
            INS.install_into_repo(repo, self.source, yes=True, no_color=True)
            for rel, (content, _survives) in shims.items():
                (repo / rel).write_text(content, encoding="utf-8")
            INS.uninstall_repo(repo, use_git=True, **kwargs)
            problems = []
            for rel, (content, survives) in shims.items():
                path = repo / rel
                if survives:
                    if not path.is_file():
                        problems.append(
                            f"{rel} was DELETED, and this row requires it preserved; the user's edit "
                            "is gone with no backup"
                        )
                    elif path.read_text(encoding="utf-8") != content:
                        problems.append(
                            f"{rel} survived but its content changed to "
                            f"{path.read_text(encoding='utf-8')!r}, expected {content!r}. A rewritten "
                            "file is not a preserved one"
                        )
                elif path.is_file():
                    problems.append(
                        f"{rel} still exists, and this row requires it removed"
                        + (
                            " - `--force` is an explicit request for a clean sweep"
                            if kwargs.get("force")
                            else " - the decider answered `remove` for this path"
                        )
                    )
            if problems:
                if not all(s for _c, s in shims.values()):
                    exception_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if exception_broken:
            vacuity = (
                " A REMOVAL row is among the failures, and while one is broken the preservation rows "
                "are nearly vacuous: an uninstall that removes nothing satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"uninstall mishandled {len(wrong)} of {len(cases)} consent modes.{vacuity} One drift "
            "disposition decides all three, so read the failures together: if the PRESERVATION rows "
            "fail, the default consent flipped to destructive and a user who typed `aw uninstall` "
            "lost edits they never mentioned; if only the DECIDER row fails, the callback's answer is "
            "not being bound to the file it was asked about, which means an interactive user's `keep` "
            f"can delete the wrong file.\n" + "\n".join(wrong),
        )

    def test_uninstall_removes_framework_and_manifest_while_keeping_user_files(self):
        """Kept separate: a whole-tree claim over paths of several DIFFERENT kinds.

        Merges the surviving halves of two former characterization tests
        (`test_uninstall_removes_framework_keeps_user_file` and the manifest half of
        `test_uninstall_removes_manifest_last_and_preserves_edited_shim`), which asserted the same
        sweep. Not a row: the subject is the whole target tree rather than one file under a consent
        mode.
        """
        repo = init_repo(self.base / "u")
        (repo / "my_code.py").write_text("print('hi')\n", encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        manifest = repo / ".aw/system/managed-sections.json"
        self.assertTrue((repo / ".aw/system/workflows").is_dir())
        self.assertTrue(manifest.is_file())

        INS.uninstall_repo(repo, use_git=True)

        self.assertFalse((repo / ".aw/system/workflows").is_dir())
        self.assertFalse(manifest.is_file(), "uninstall removes the manifest (CP2)")
        self.assertTrue(
            (repo / "my_code.py").is_file(), "a user's own source file must survive"
        )

    def test_changed_out_collects_paths_and_sections_preserved(self):
        """Kept separate: the subject is the reported `changed_out` list plus AGENTS.md's survival."""
        repo = init_repo(self.base / "c")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        changed: list[str] = []
        INS.uninstall_repo(repo, use_git=True, changed_out=changed)
        # Manifest + AGENTS pointer are among the changed paths.
        self.assertIn(".aw/system/managed-sections.json", changed)
        self.assertIn("AGENTS.md", changed)
        # AGENTS.md still exists (only its managed block was stripped, U8).
        self.assertTrue((repo / "AGENTS.md").is_file())
        self.assertNotIn("aw:block", (repo / "AGENTS.md").read_text(encoding="utf-8"))

    def test_pre_manifest_fallback_removes_namespace(self):
        """Kept separate: materially different setup (the manifest is DELETED to simulate an old repo)."""
        repo = init_repo(self.base / "pre")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        (repo / ".aw/system/managed-sections.json").unlink()
        INS.uninstall_repo(repo, use_git=True)
        self.assertFalse((repo / ".aw/system/workflows").is_dir())

    def test_plan_uninstall_classifies_remove_drifted_and_missing(self):
        """Kept separate: asserts the PLAN's three-way partition, not what an uninstall did."""
        repo = init_repo(self.base / "classify")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        # Edit one shim (drift), delete another (missing), leave the rest (remove).
        edited = repo / ".opencode/commands/advise.md"
        edited.write_text("MY EDIT\n", encoding="utf-8")
        missing = repo / ".claude/commands/verify.md"
        if missing.is_file():
            missing.unlink()
        plan = INS.plan_uninstall(repo)
        self.assertTrue(plan.has_manifest)
        self.assertIn(".opencode/commands/advise.md", plan.drifted)
        self.assertIn(".claude/commands/verify.md", plan.missing)
        self.assertTrue(len(plan.remove) > 0)
        self.assertNotIn(
            ".opencode/commands/advise.md",
            plan.remove,
            "a drifted file must never also be a removal candidate",
        )

    def test_section_entries_are_never_file_removal_candidates(self):
        """Kept separate: U8 is an ABSENCE claim across all three partitions at once."""
        repo = init_repo(self.base / "u8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        plan = INS.plan_uninstall(repo)
        allpaths = set(plan.remove) | set(plan.drifted) | set(plan.missing)
        # AGENTS.md / .gitignore carry only SECTION entries; treating them as file-removal candidates
        # would delete a user's whole file to remove a block inside it.
        self.assertNotIn("AGENTS.md", allpaths)
        self.assertNotIn(".gitignore", allpaths)

    def test_pre_manifest_repo_has_no_manifest(self):
        """Kept separate: the precondition is that NO install ever happened."""
        repo = init_repo(self.base / "nomanifest")
        plan = INS.plan_uninstall(repo)
        self.assertFalse(plan.has_manifest)
        self.assertEqual(plan.remove, [])


class AwBlockMigrationTests(unittest.TestCase):
    """CP3: legacy convert-not-append + sibling-block safety + reinstall idempotence (IPD 02).

    Left largely un-merged: each of these drives a full `install_into_repo` against a repo seeded with a
    different pre-existing FILE (a legacy AGENTS.md, a legacy CLAUDE.md, a file with a foreign block,
    a manifest carrying a decline tombstone) and asserts a different structural claim. The
    marker-shape decisions they depend on are unit-tabulated in `LegacyPointerMergeTests` and
    `AwBlockParserWriterTests`; these are the end-to-end consequences.
    """

    LEGACY_BEGIN = "<!-- AGENT-WORKFLOWS:BEGIN -->"
    LEGACY_END = "<!-- AGENT-WORKFLOWS:END -->"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def test_legacy_block_converts_not_appends(self):
        # A repo carrying the OLD monolithic block must be CONVERTED in place: no duplicate, no
        # legacy markers re-emitted, human-visible prose preserved.
        repo = init_repo(self.base / "legacy")
        legacy = repo / "AGENTS.md"
        legacy.write_text(
            "# AGENTS\n\nUser preamble\n\n"
            + INS.agents_pointer_block()
            + "\nUser epilogue\n",
            encoding="utf-8",
        )
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        txt = legacy.read_text(encoding="utf-8")
        self.assertEqual(
            txt.count("<!-- aw:block -->"), 1, "exactly one sectioned block"
        )
        self.assertNotIn(
            self.LEGACY_BEGIN, txt, "legacy markers must not be re-emitted"
        )
        self.assertNotIn(self.LEGACY_END, txt)
        self.assertIn("User preamble", txt)
        self.assertIn("User epilogue", txt)
        self.assertIn("## Agent workflows", txt)

    def test_legacy_native_mirror_converts(self):
        """Kept separate: the same conversion on a NATIVE host file, which is mirrored not authored."""
        repo = init_repo(self.base / "legacy-native")
        (repo / "CLAUDE.md").write_text(
            "User C\n\n" + INS.agents_pointer_block() + "\n", encoding="utf-8"
        )
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        c = (repo / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(c.count("<!-- aw:block -->"), 1)
        self.assertNotIn(self.LEGACY_BEGIN, c)
        self.assertIn("User C", c)

    def test_sibling_named_block_untouched_through_install(self):
        """M9 end-to-end: a foreign AGENT-PLANS block must be BYTE-IDENTICAL after a real install."""
        repo = init_repo(self.base / "sibling")
        sibling = "<!-- AGENT-PLANS:BEGIN -->\n## Agent plans\npolicy text here\n<!-- AGENT-PLANS:END -->\n"
        (repo / "AGENTS.md").write_text(
            "# AGENTS\n\n" + sibling + "\n" + INS.agents_pointer_block() + "\n",
            encoding="utf-8",
        )
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        txt = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(
            sibling, txt, "foreign AGENT-PLANS block must be byte-identical (M9)"
        )
        self.assertEqual(txt.count("<!-- AGENT-PLANS:BEGIN -->"), 1)
        self.assertEqual(txt.count("<!-- aw:block -->"), 1)

    def test_reinstall_is_empty_diff_on_target_file(self):
        """Kept separate: a before/after idempotence PAIR on AGENTS.md; the two halves are one claim."""
        repo = init_repo(self.base / "idem")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        first = (repo / "AGENTS.md").read_text(encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertEqual(
            first,
            (repo / "AGENTS.md").read_text(encoding="utf-8"),
            "reinstall must be an empty diff on the target file",
        )

    def test_declined_section_not_written(self):
        """Kept separate: requires hand-writing a decline TOMBSTONE into the manifest first."""
        from agent_workflows import manifest as M

        repo = init_repo(self.base / "declined")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        mpath = repo / ".aw" / "system" / "managed-sections.json"
        man = M.load(mpath)
        man.mark_declined("AGENTS.md#aw:pointer", kind="section")
        M.save(man, mpath)
        # Rewrite AGENTS.md without the block, then reinstall: the declined section stays out.
        (repo / "AGENTS.md").write_text("# AGENTS\n\nuser only\n", encoding="utf-8")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertNotIn(
            "<!-- aw:pointer -->",
            (repo / "AGENTS.md").read_text(encoding="utf-8"),
            "declined section must not be written",
        )


class ManifestInstallFlowTests(unittest.TestCase):
    """CP3/CP4: what the install MANIFEST records, and what a decline tombstone suppresses.

    Left un-merged: one test is a before/after hash comparison across two installs (an idempotence
    pair), one requires writing a tombstone and then asserting a file does NOT return, and one captures
    stdout to assert a warning's ABSENCE. Three different subjects.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def _manifest_path(self, repo):
        return repo / ".aw" / "system" / "managed-sections.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_manifest_records_installed_shims_with_hashes(self):
        """Merges two former assertions of the same shape (CP3/CP4 characterization + the CP1 pin)."""
        import json

        repo = init_repo(self.base / "withmanifest")
        INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)
        manifest = self._manifest_path(repo)
        self.assertTrue(manifest.exists(), "install must write the manifest (CP3)")
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn("files", raw)
        self.assertIn("managed_sections", raw)  # reserved for IPD 02
        advise = raw["files"].get(".opencode/commands/advise.md")
        self.assertIsNotNone(advise, "advise shim should be recorded in the manifest")
        self.assertTrue(advise["sha256"])
        self.assertEqual(advise.get("host"), "opencode")

    def test_second_install_rederives_identical_hashes(self):
        """Kept separate: a before/after idempotence PAIR over the whole recorded hash map."""
        import json

        repo = init_repo(self.base / "idem")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        first = json.loads(self._manifest_path(repo).read_text(encoding="utf-8"))[
            "files"
        ]
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        second = json.loads(self._manifest_path(repo).read_text(encoding="utf-8"))[
            "files"
        ]
        self.assertEqual(
            {k: v["sha256"] for k, v in first.items()},
            {k: v["sha256"] for k, v in second.items()},
            "a second same-version install must re-derive identical hashes (M12)",
        )

    def test_declined_file_is_not_readded(self):
        """Kept separate: a TOMBSTONE claim. The file is deleted and must NOT come back."""
        from agent_workflows import manifest as M

        repo = init_repo(self.base / "declined")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        shim = repo / ".opencode/commands/advise.md"
        self.assertTrue(shim.is_file())
        shim.unlink()

        man = M.load(self._manifest_path(repo))
        man.mark_declined(".opencode/commands/advise.md", kind="shim", host="opencode")
        M.save(man, self._manifest_path(repo))

        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertFalse(
            shim.exists(), "a declined file must not be re-added on a later install"
        )

    def test_idempotent_reinstall_prints_no_modification_warning(self):
        """Kept separate: asserts the ABSENCE of a warning in captured stdout (the D97 case)."""
        repo = init_repo(self.base / "d97")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        self.assertNotIn("has manual modifications", buf.getvalue())


class ManifestDriftDecisionTests(unittest.TestCase):
    """CP2: `_shim_is_user_modified`, the hash-based drift decision that gates every overwrite (M9).

    ONE table replaces five tests (`test_format_only_change_matching_our_hash_is_not_modified`,
    `test_user_edit_differing_from_our_hash_is_modified`,
    `test_pre_manifest_structurally_valid_shim_is_adopted`,
    `test_pre_manifest_foreign_content_is_modified`,
    `test_no_manifest_attached_falls_back_to_structural`), plus the characterization test
    `test_m9_format_only_change_is_flagged_customized_today`, which pinned the PRE-FIX behavior of the
    predicate this one replaced and has been superseded (the CP2 model is the live contract, and the
    tree should not carry a test asserting the bug is still present).

    THIS PREDICATE DECIDES WHETHER A USER'S FILE IS OVERWRITTEN, which is why it is one table. It has
    exactly THREE regimes and they are the column: a manifest entry EXISTS for the path (compare
    against the hash of what we last wrote), a manifest exists but has NO entry (the pre-manifest
    adoption case, decided structurally), or there is NO MANIFEST at all (structural fallback). Five
    separate tests made it impossible to see that the same input gets different answers in different
    regimes, which is the whole design; and the realistic regression is a refactor that collapses two
    regimes, moving several rows at once.

    THE FALSE-POSITIVE ROW IS THE M9 FIX ITSELF: our own format change must NOT read as a user
    modification, because the alternative is the installer prompting users about files they never
    touched, which trains them to answer `y` without reading. The FALSE-NEGATIVE rows are the safety
    side: foreign content must always read as modified, since that is what protects it.
    """

    from agent_workflows import manifest as _M

    #: (case, the manifest regime ('recorded', 'empty-manifest', 'no-manifest'), the content the
    #: manifest RECORDS as our last output (None for the two manifest-less regimes), the on-disk
    #: content, the newly expected content, whether the path must be judged USER-MODIFIED, why)
    #:
    #: THE `recorded` COLUMN IS SEPARATE FROM `on_disk` DELIBERATELY, and conflating them is a real
    #: trap: recording the on-disk bytes makes the hash match BY CONSTRUCTION, so the user-edit row
    #: below cannot fail and the table silently stops testing the safety direction. Measured while
    #: writing this table, where an earlier version recorded `on_disk` and the edit row asserted a
    #: verdict the predicate could never reach.
    DECISIONS = (
        (
            "our own format change, with our hash recorded",
            "recorded",
            "---\ndescription: advise\nagent: build\n---\nRead and execute @advise\n",
            "---\ndescription: advise\nagent: build\n---\nRead and execute @advise\n",
            "---\ndescription: advise\nagent: build\nargument-hint: [x]\n---\n"
            "Read and execute @advise\n",
            False,
            "THE M9 FIX: on-disk equals what we last WROTE (the recorded column and the on-disk column "
            "are identical here), and the new expected content differs only because our generator "
            "changed. Comparing on-disk to the NEW expectation (the pre-fix model) called this a user "
            "modification and warned on every shim after any format change, which trains users to "
            "answer `y` without reading and is how a real edit then gets lost",
        ),
        (
            "a genuine user edit, with our hash recorded",
            "recorded",
            "---\nagent: build\n---\nRead and execute @advise\n",
            "---\nagent: build\n---\nRead and execute @advise\nMY OWN CUSTOM NOTE\n",
            "---\nagent: build\n---\nRead and execute @advise\n",
            True,
            "THE SAFETY SIDE of the same regime: on-disk differs from our RECORDED output, so it is a "
            "user modification even though the new expected content equals our record exactly. The "
            "ON-DISK bytes win, which is what makes the hash a record of OUR output rather than a "
            "prediction of the user's. Note this row is only meaningful because `recorded` and "
            "`on_disk` are separate columns",
        ),
        (
            "a pre-manifest shim containing only installer-owned lines",
            "empty-manifest",
            None,
            "---\ndescription: advise\nagent: build\n---\n"
            "Read and execute @.agents/workflows/advise\n",
            "---\ndescription: advise\nagent: build\n---\n"
            "Read and execute @.agents/workflows/advise\nextra generated line\n",
            False,
            "M10/OQ4 ADOPTION: a repo installed before the manifest existed has files we wrote but no "
            "record of them, so the decision falls back to STRUCTURE. A structurally-valid shim is "
            "adopted rather than false-flagged; without this, upgrading an older install would warn "
            "on every single shim at once",
        ),
        (
            "pre-manifest content that is entirely the user's",
            "empty-manifest",
            None,
            "This is entirely my own file with no generated structure.\n",
            "expected\n",
            True,
            "the structural fallback must still PROTECT: with no record to compare against, content "
            "that does not look like our output is treated as the user's. Erring toward 'modified' is "
            "the correct direction here, because the cost is a prompt and the alternative cost is "
            "someone's file",
        ),
        (
            "no manifest attached at all, foreign content",
            "no-manifest",
            None,
            "totally custom\n",
            "e\n",
            True,
            "THE THIRD REGIME: a non-manifest-aware caller passes no manifest, and the predicate must "
            "still work rather than crashing or defaulting to 'ours'. Asserted with foreign content "
            "because that is the dangerous direction for a caller with the least information",
        ),
        (
            "no manifest attached at all, structurally valid content",
            "no-manifest",
            None,
            "Read and execute @.agents/workflows/x\n",
            "e\n",
            False,
            "the paired positive for the same regime, which together with the row above shows the "
            "fallback really inspects the content rather than answering a constant. A predicate "
            "returning True whenever the manifest is None would satisfy the row above on its own",
        ),
    )

    def _plan(self, manifest=None):
        return INS.InstallPlan(
            source_root=Path("/src"),
            repo_root=Path("/repo"),
            dry_run=False,
            backup=True,
            prune=True,
            no_color=True,
            yes=False,
            manifest=manifest,
        )

    def test_every_manifest_regime_decides_drift_correctly(self):
        rel = ".opencode/commands/advise.md"
        wrong = []
        for case, regime, recorded, on_disk, expected, modified, why in self.DECISIONS:
            if regime == "recorded":
                man = self._M.Manifest()
                man.record(rel, recorded, kind="shim", host="opencode")
                plan = self._plan(man)
            elif regime == "empty-manifest":
                plan = self._plan(self._M.Manifest())
            else:
                plan = self._plan(None)
            got = INS._shim_is_user_modified(plan, rel, on_disk, expected)
            if got != modified:
                wrong.append(
                    f"  {case} (regime {regime!r}):\n"
                    f"    - judged user_modified={got}, expected {modified}"
                    + (
                        " - A FALSE NEGATIVE: the installer will OVERWRITE content it does not own"
                        if modified
                        else " - A FALSE POSITIVE: the installer will warn about (and prompt on) a "
                        "file it wrote itself"
                    )
                    + f"\n    this row exists because: {why}"
                )
        false_negatives = [w for w in wrong if "FALSE NEGATIVE" in w]
        note = ""
        if false_negatives:
            note = (
                f" {len(false_negatives)} of the failures are FALSE NEGATIVES, which is the unsafe "
                "direction: fix those first, because each one is a path on which the installer "
                "overwrites content it does not own."
            )
        self.assertEqual(
            wrong,
            [],
            f"_shim_is_user_modified was wrong in {len(wrong)} of {len(self.DECISIONS)} cases.{note} "
            "The three regimes (a recorded hash, a manifest with no entry, no manifest) are branches "
            "of ONE function, so read the failures together: if both `recorded` rows fail the hash "
            "comparison broke; if the four fallback rows fail the structural heuristic did; if one "
            "regime's rows ALL invert, that branch was collapsed into another. FIX: this predicate is "
            "the gate in front of every overwrite, so a false negative is data loss while a false "
            f"positive is only noise - but sustained noise is what makes users stop reading the "
            f"prompt, which then causes the data loss.\n" + "\n".join(wrong),
        )

    def test_normalizers_are_stable_and_idempotent(self):
        """Kept separate: the normalizers underpin the hashing but assert IDEMPOTENCE, not a verdict."""
        raw = "  a  \r\n\r\n  b \n\n"
        once = INS.normalize_text_for_compare(raw)
        self.assertEqual(once, "a\nb")
        self.assertEqual(
            INS.normalize_text_for_compare(once), once, "normalization is idempotent"
        )
        withdesc = "---\ndescription: x\nagent: build\n---\nbody"
        stripped = INS.strip_description_and_normalize(withdesc)
        self.assertNotIn("description:", stripped)
        self.assertEqual(
            INS.strip_description_and_normalize(stripped),
            stripped,
            "description-stripping normalization is idempotent",
        )


class PhysicalSystemInstallTests(unittest.TestCase):
    """Falsifiable unit and integration tests for IPD Order 04 (E-01 .. E-07).

    Left un-merged: each `test_eNN` is a NAMED execution item of a plan, each asserts a different
    subsystem (source resolution, packaging metadata, the staged-candidate pivot, the state tree,
    checkout-identity spoofing, conservative uninstall, the mode matrix), and several are gated on a
    fixture file existing. The E-numbers are the traceability link back to the plan's validation items,
    so collapsing them would break that mapping.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_e01(self):
        """E-01: Canonical source tree and package-resource resolver."""
        from agent_workflows.engine import resolve_source_root

        fx = (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order04"
            / "e01-source-tree.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        src = resolve_source_root(None)
        self.assertTrue(src.is_dir(), f"Source root is not a directory: {src}")
        self.assertTrue(
            (src / "index.md").is_file()
            or (src / "workflows" / "index.md").is_file()
            or (src / "VERSION").is_file()
            or (src / "managed-sections.json").is_file(),
            "Manifest/VERSION absent from source root",
        )

    def test_e02(self):
        """E-02: Package inspection, versioning, and stdlib-only runtime."""
        fx = (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order04"
            / "e02-packaging.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        # The packaged bundle ships from .aw/system ONCE (Order-11 self-migration moved the
        # source there); the legacy .agents/workflows force-include is gone (no double-ship).
        self.assertIn(".aw/system", pyproject_text)
        self.assertNotIn('".agents/workflows"', pyproject_text)

    def test_e03(self):
        """E-03: Staged candidate system tree, validation, and atomic pivot."""
        from agent_workflows.install_wizard import ProjectPolicy
        from agent_workflows.project_layout import (
            install_system_tree,
            validate_candidate_system,
        )

        fx = (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order04"
            / "e03-pivot.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        target = self.tmp_dir / "target_repo"
        target.mkdir()
        policy = ProjectPolicy(preset="private-target")

        res = install_system_tree(
            str(target), source_root=SOURCE_WORKFLOWS, policy=policy
        )
        self.assertEqual(res["status"], "installed")
        self.assertTrue((target / ".aw" / "system" / "VERSION").is_file())

        corrupt_cand = self.tmp_dir / "corrupt_cand"
        corrupt_cand.mkdir()
        (corrupt_cand / "VERSION").write_text("", encoding="utf-8")
        self.assertFalse(validate_candidate_system(corrupt_cand))

    def test_e04(self):
        """E-04: Transient state in state/runtime/ and durable state in state/durable/."""
        from agent_workflows.install_wizard import ProjectPolicy
        from agent_workflows.project_layout import install_system_tree

        fx = (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order04"
            / "e04-transient-state.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        target = self.tmp_dir / "target_e04"
        target.mkdir()
        install_system_tree(
            str(target),
            source_root=SOURCE_WORKFLOWS,
            policy=ProjectPolicy(preset="private-target"),
        )

        durable_file = target / ".aw" / "state" / "durable" / "install.json"
        history_file = (
            target / ".aw" / "state" / "durable" / "history" / "installs.jsonl"
        )
        self.assertTrue(durable_file.is_file(), "Durable install snapshot missing")
        self.assertTrue(history_file.is_file(), "Durable install history missing")
        self.assertTrue(
            (target / ".aw" / "state" / "runtime").is_dir(), "Runtime dir missing"
        )

    def test_e05(self):
        """E-05: Positive source-checkout identity and spoofing protection.

        Kept as one test with several probes: they are the POSITIVE identity plus three distinct SPOOF
        shapes, and the security claim is the combination (real evidence accepted, every partial
        imitation refused). Splitting them would let a reader take any single refusal as the rule.
        """
        from agent_workflows.engine import is_source_checkout
        from agent_workflows.install_wizard import ProjectPolicy
        from agent_workflows.project_layout import install_system_tree

        src_repo = self.tmp_dir / "src_positive"
        src_repo.mkdir()
        (src_repo / ".git").mkdir()
        (src_repo / "pyproject.toml").write_text(
            '[project]\nname = "agent-workflows"\n', encoding="utf-8"
        )
        (src_repo / ".aw" / "system").mkdir(parents=True)
        (src_repo / ".aw" / "system" / "VERSION").write_text(
            "2026.8.10\n", encoding="utf-8"
        )

        self.assertTrue(is_source_checkout(src_repo, source_root=SOURCE_WORKFLOWS))
        res = install_system_tree(
            str(src_repo),
            source_root=SOURCE_WORKFLOWS,
            policy=ProjectPolicy(preset="private-target"),
        )
        self.assertEqual(res["status"], "source-checkout-preserved")

        path_eq = self.tmp_dir / "path_equality_only"
        path_eq.mkdir()
        (path_eq / ".git").mkdir()
        self.assertFalse(is_source_checkout(path_eq, source_root=path_eq))

        spoof1 = self.tmp_dir / "copied_marker_spoof"
        spoof1.mkdir()
        (spoof1 / ".git").mkdir()
        (spoof1 / ".aw" / "system").mkdir(parents=True)
        (spoof1 / ".aw" / "system" / "VERSION").write_text(
            "2026.8.10\n", encoding="utf-8"
        )
        self.assertFalse(is_source_checkout(spoof1, source_root=SOURCE_WORKFLOWS))

        spoof2 = self.tmp_dir / "origin_only_spoof"
        spoof2.mkdir()
        (spoof2 / ".git").mkdir()
        self.assertFalse(is_source_checkout(spoof2, source_root=SOURCE_WORKFLOWS))

        ambig = self.tmp_dir / "ambiguous_evidence"
        ambig.mkdir()
        self.assertFalse(is_source_checkout(ambig, source_root=SOURCE_WORKFLOWS))

    def test_e06(self):
        """E-06: Conservative uninstall and ownership checks (a user file and local config survive)."""
        from agent_workflows.install_wizard import ProjectPolicy
        from agent_workflows.project_layout import (
            install_system_tree,
            uninstall_system_tree,
        )

        fx = (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order04"
            / "e06-uninstall.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        target = self.tmp_dir / "target_e06"
        target.mkdir()
        install_system_tree(
            str(target),
            source_root=SOURCE_WORKFLOWS,
            policy=ProjectPolicy(preset="private-target"),
        )

        (target / ".aw" / "config").mkdir(parents=True, exist_ok=True)
        (target / ".aw" / "config" / "local.json").write_text(
            '{"user": true}\n', encoding="utf-8"
        )
        (target / "human_notes.txt").write_text(
            "important user note\n", encoding="utf-8"
        )

        res = uninstall_system_tree(str(target), source_root=SOURCE_WORKFLOWS)
        self.assertEqual(res["status"], "uninstalled")

        self.assertTrue(
            (target / "human_notes.txt").is_file(), "Human file was deleted!"
        )
        self.assertTrue(
            (target / ".aw" / "config" / "local.json").is_file(),
            "Config local was deleted!",
        )

    def test_e07(self):
        """E-07: Mode matrix (fresh-tracked, update, windows fallback, then uninstall)."""
        from agent_workflows.install_wizard import ProjectPolicy
        from agent_workflows.project_layout import (
            install_system_tree,
            uninstall_system_tree,
        )

        fx = (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order04"
            / "e07-modes.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        target1 = self.tmp_dir / "fresh_tracked"
        target1.mkdir()
        for expected in ("installed", "installed"):  # fresh, then an update
            res = install_system_tree(
                str(target1),
                source_root=SOURCE_WORKFLOWS,
                policy=ProjectPolicy(preset="private-target"),
            )
            self.assertEqual(res["status"], expected)

        target3 = self.tmp_dir / "win_fallback"
        target3.mkdir()
        res3 = install_system_tree(
            str(target3),
            source_root=SOURCE_WORKFLOWS,
            policy=ProjectPolicy(preset="private-target"),
            windows_fallback=True,
        )
        self.assertEqual(res3["status"], "installed")
        self.assertEqual(
            uninstall_system_tree(str(target3), source_root=SOURCE_WORKFLOWS)["status"],
            "uninstalled",
        )


class SameSecondBackupCollisionTests(unittest.TestCase):
    """Regression: two install runs in the same wall-clock second must not collide into one
    backup directory, and --undo must restore the state before the MOST RECENT run
    (IPD 20260815-2156-01 / backlog qver7w).

    Left un-merged, and the reason is in the setup: both tests need the engine CLOCK FROZEN to a single
    second, which is a materially different harness from every other test in this file, and the first is
    a five-stage stateful sequence whose whole point is the ORDER of the runs.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        self.source = SOURCE_WORKFLOWS
        self.index = self.repo / ".aw" / "system" / "workflows" / "index.md"
        self.backups = self.repo / INS.BACKUPS_DIR

    def tearDown(self):
        self._tmp.cleanup()

    class _FrozenClock:
        """A datetime replacement whose now() is pinned to a fixed second."""

        _real = INS.datetime

        @classmethod
        def now(cls, tz=None):
            return cls._real(2026, 8, 15, 12, 0, 0, 0)

        def __getattr__(self, name):  # pragma: no cover - delegate everything else
            return getattr(self._real, name)

    def _install(self):
        INS.install_into_repo(self.repo, self.source, yes=True)

    def test_same_second_runs_use_distinct_backup_dirs_and_undo_restores_latest(self):
        with mock.patch.object(INS, "datetime", self._FrozenClock):
            # Run 1: fresh install (same frozen second).
            self._install()
            self.assertTrue(
                self.index.is_file(), "fresh install did not write index.md"
            )

            # User modifies a framework file, then Run 2 overwrites it (same frozen second).
            self.index.write_text("MODIFIED CONTENT", encoding="utf-8")
            self._install()
            self.assertNotEqual(
                self.index.read_text(encoding="utf-8"),
                "MODIFIED CONTENT",
                "run 2 did not overwrite the modified file",
            )

            # Both same-second runs must own DISTINCT backup directories (the collision fix).
            backup_dirs = sorted(d.name for d in self.backups.iterdir() if d.is_dir())
            self.assertGreaterEqual(
                len(backup_dirs),
                2,
                f"two same-second runs collided into one backup dir: {backup_dirs}",
            )

            # Modify again, then --undo must roll back to the state before the MOST RECENT run,
            # i.e. restore the pre-run-2 "MODIFIED CONTENT" (not run 1's fresh content, and not
            # remove index.md entirely).
            self.index.write_text("MODIFIED CONTENT SECOND TIME", encoding="utf-8")
            rc = INS.run_rollback(self.repo, no_color=True)
            self.assertEqual(rc, 0, "rollback returned nonzero")
            self.assertTrue(
                self.index.is_file(),
                "rollback removed index.md (older run's created-list won over newer backups)",
            )
            self.assertEqual(
                self.index.read_text(encoding="utf-8"),
                "MODIFIED CONTENT",
                "rollback restored the wrong run's content",
            )

    def test_allocate_backup_timestamp_is_unique_against_existing_dirs(self):
        """Kept separate: a pure token-allocation claim (three tokens must differ, each extending the first)."""
        with mock.patch.object(INS, "datetime", self._FrozenClock):
            t1 = INS.allocate_backup_timestamp(self.repo)
            (self.backups / t1).mkdir(parents=True)
            t2 = INS.allocate_backup_timestamp(self.repo)
            (self.backups / t2).mkdir(parents=True)
            t3 = INS.allocate_backup_timestamp(self.repo)
        self.assertEqual(len({t1, t2, t3}), 3, f"tokens collided: {t1} {t2} {t3}")
        self.assertTrue(t2.startswith(t1))
        self.assertTrue(t3.startswith(t1))


class NestedSourceSiblingVersionTests(unittest.TestCase):
    """Regression (xzuxet E-04): under the canonical nested `.aw/system/` layout, VERSION is
    a system-root SIBLING at `.aw/system/VERSION`, one level ABOVE the descended bundle root
    `.aw/system/workflows/`. The installer must still ship it to the target's LEGACY path
    `.agents/workflows/VERSION` (the compat-window target layout). Before the fix, the source
    resolved to the bundle root, the rglob member sweep never saw the sibling VERSION, and
    installed targets lost `.agents/workflows/VERSION` (the E-05 re-cutover discovery: 10
    installer/CLI tests went red only when `.aw/` was present).

    Left un-merged: every test here builds a SYNTHETIC nested source tree in `setUp` (a materially
    different harness from the rest of this file, which installs from the real source), and the last is
    a deliberate MUTATION PROBE proving the positives are falsifiable, which is an inverse claim that
    cannot share a row with them. The two shipping tests differ by TARGET LAYOUT, which would be a
    column, but each also asserts layout-specific neighbouring paths, so they are left explicit.
    """

    MANIFEST_ROW = "| plan-review | .agents/workflows/plan-review/plan-review.md | - | Test workflow. |"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Synthetic nested source: <root>/.aw/system/workflows/ is the bundle (index.md +
        # bodies + templates), and <root>/.aw/system/VERSION is the system-root SIBLING.
        self.system = self.root / ".aw" / "system"
        self.bundle = self.system / "workflows"
        (self.bundle / "plan-review").mkdir(parents=True)
        (self.bundle / "templates").mkdir(parents=True)
        index = (
            "# Workflows\n\n"
            f"{INS.MANIFEST_BEGIN}\n"
            "| command | body | lens | description |\n"
            "|---|---|---|---|\n"
            f"{self.MANIFEST_ROW}\n"
            f"{INS.MANIFEST_END}\n"
        )
        (self.bundle / "index.md").write_text(index, encoding="utf-8")
        (self.bundle / "plan-review" / "plan-review.md").write_text(
            "# plan-review body\n", encoding="utf-8"
        )
        (self.bundle / "templates" / "shim-README.md").write_text(
            "# shims\n", encoding="utf-8"
        )
        # The SIBLING VERSION (outside the bundle), one level up at the system root.
        self.version_text = "9.9.9-nested\n"
        (self.system / "VERSION").write_text(self.version_text, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _resolve(self) -> Path:
        # Point the resolver at the repo root that contains .aw/system; it must descend into
        # workflows/ (E-01) so the returned root DIRECTLY holds index.md.
        resolved = INS.resolve_source_root(self.root)
        self.assertEqual(
            resolved,
            self.bundle,
            "resolve_source_root did not descend into the nested workflows/ bundle",
        )
        return resolved

    def test_collect_source_members_includes_sibling_version(self):
        """Both target layouts in one test: the member list is the same claim under a layout column."""
        resolved = self._resolve()
        members_aw = INS.collect_source_members(resolved, target_layout="aw")
        self.assertIn(
            f"{INS.AW_SYSTEM_DIR}/{INS.VERSION_FILE}",
            members_aw,
            "sibling VERSION was not collected as an install member under aw layout",
        )
        members_legacy = INS.collect_source_members(resolved, target_layout="legacy")
        self.assertIn(
            f"{INS.WORKFLOWS_DIR}/{INS.VERSION_FILE}",
            members_legacy,
            "sibling VERSION was not collected as an install member under legacy layout",
        )

    def test_read_version_reads_sibling(self):
        """Kept separate: a version-resolution claim, not a shipping one."""
        # Non-git temp tree -> versioning resolver falls back to the VERSION file, which under
        # nested is the sibling. The resolved value must reflect the sibling's content.
        self.assertIn("9.9.9-nested", INS.read_version(self._resolve()))

    def test_install_ships_sibling_version_to_aw_target_path(self):
        resolved = self._resolve()
        target = init_repo(self.root / "target_aw")
        INS.install_into_repo(target, resolved, yes=True, no_color=True)
        installed_version = target / ".aw" / "system" / "VERSION"
        self.assertTrue(
            installed_version.is_file(),
            "installer did not ship the sibling VERSION to .aw/system/VERSION",
        )
        self.assertEqual(
            installed_version.read_text(encoding="utf-8"),
            self.version_text,
            "installed VERSION content does not match the source sibling",
        )
        # Bundle content also landed, and the legacy tree was NOT created.
        self.assertTrue(
            (target / ".aw" / "system" / "workflows" / "index.md").is_file()
        )
        self.assertFalse((target / ".agents" / "workflows").exists())

    def test_install_ships_sibling_version_to_legacy_target_path(self):
        """The layout PAIR of the test above; the target path and the neighbouring assertions differ."""
        resolved = self._resolve()
        target = init_repo(self.root / "target_legacy")
        (target / ".agents" / "workflows").mkdir(parents=True)
        INS.install_into_repo(target, resolved, yes=True, no_color=True)
        installed_version = target / ".agents" / "workflows" / "VERSION"
        self.assertTrue(
            installed_version.is_file(),
            "installer did not ship the sibling VERSION to .agents/workflows/VERSION",
        )
        self.assertEqual(
            installed_version.read_text(encoding="utf-8"),
            self.version_text,
            "installed VERSION content does not match the source sibling",
        )
        self.assertTrue((target / ".agents" / "workflows" / "index.md").is_file())

    def test_mutation_removing_sibling_version_makes_it_disappear(self):
        """Kept separate: the deliberate RED half of a mutation probe, an inverse of every row above."""
        # With NO sibling VERSION present, neither the member nor the installed file exists. This
        # proves the positive assertions above are falsifiable (they fail exactly when it is absent).
        (self.system / "VERSION").unlink()
        resolved = self._resolve()
        members = INS.collect_source_members(resolved, target_layout="aw")
        self.assertNotIn(
            f"{INS.AW_SYSTEM_DIR}/{INS.VERSION_FILE}",
            members,
            "VERSION member present despite no sibling VERSION on disk",
        )
        target = init_repo(self.root / "target_novers")
        INS.install_into_repo(target, resolved, yes=True, no_color=True)
        self.assertFalse(
            (target / ".aw" / "system" / "VERSION").is_file(),
            "installer materialized a VERSION with no source sibling to ship",
        )


class TargetLayoutResolutionTests(unittest.TestCase):
    """Order 15 (awphysical-15-7cvh9t): which layout a target repo gets, and what install then writes.

    ONE table replaces four tests (`test_resolve_target_layout_deterministic_rules`,
    `test_fresh_install_no_dual_write`, `test_legacy_repo_preserved_on_update`,
    `test_read_installed_version_checks_all_locations`), three of which each contained several
    unlabelled sub-cases in one method, so a failure told you the layout rules were wrong but not WHICH
    repo shape broke.

    The column set is the repo's PRE-EXISTING DIRECTORIES, which is exactly what the resolution rules
    key on, and every row carries the whole consequence rather than just the resolver's answer: the
    layout NAME, the path the framework must land at, and critically THE PATH THAT MUST NOT APPEAR.
    That last column is the no-dual-write property, and it is the one worth having: dual-writing is
    silent (both trees look fine) and leaves the repo split-brained, which the guard class below then
    has to refuse to install into.

    THE DUAL-EXISTENCE ROW is the tie-break rule, and it belongs beside the others because it is only
    meaningful as a comparison: `.aw/system` wins over `.agents/workflows` when BOTH are present, which
    no single-directory row can express.
    """

    #: (case, directories to create before resolving, expected layout, paths that must EXIST after an
    #: install, paths that must NOT exist after it, why this row exists)
    LAYOUTS = (
        (
            "a fresh repo with neither tree",
            (),
            "aw",
            (".aw/system/workflows/index.md", ".aw/system/VERSION"),
            (".agents/workflows",),
            "THE DEFAULT FOR EVERY NEW INSTALL: the canonical `.aw/` layout, and the legacy tree is "
            "NOT created alongside it. The must-not-exist column is the no-dual-write property, which "
            "matters because dual-writing is SILENT (both trees look correct) and leaves the repo in "
            "exactly the split-brain state the install guard then refuses to touch",
        ),
        (
            "a repo that already has .aw/system",
            (".aw/system",),
            "aw",
            (".aw/system/workflows/index.md",),
            (".agents/workflows",),
            "an existing canonical install stays canonical. Asserted separately from the fresh row "
            "because they reach the same answer by DIFFERENT rules (absence of evidence versus "
            "positive evidence), so a rewrite can break one and not the other",
        ),
        (
            "a repo with only .agents/workflows",
            (".agents/workflows",),
            "legacy",
            (".agents/workflows/index.md", ".agents/workflows/VERSION"),
            (".aw/system",),
            "A LEGACY REPO IS PRESERVED, NOT SILENTLY MIGRATED. The user gets updates where their "
            "tooling already points, and `.aw/system` must not appear, because a half-migrated repo "
            "has two framework trees and no way to tell which is live. Migration is `aw "
            "migrate-layout`, an explicit act",
        ),
        (
            "a repo with BOTH trees",
            (".aw/system", ".agents/workflows"),
            "aw",
            (".aw/system/workflows/index.md",),
            (),
            "THE TIE-BREAK: `.aw/system` is authoritative when both exist, which is only assertable as "
            "a comparison and is therefore the row that cannot be split out. Note the must-not-exist "
            "column is empty here on purpose: the legacy tree was already there and the installer "
            "does not delete it, since that is the migration verb's job",
        ),
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_repo_shape_resolves_and_installs_to_the_right_layout(self):
        wrong = []
        for index, (case, dirs, layout, present, absent, why) in enumerate(
            self.LAYOUTS
        ):
            repo = init_repo(self.base / f"layout-{index}")
            for rel in dirs:
                (repo / rel).mkdir(parents=True)
            problems = []
            resolved = INS.resolve_target_layout(repo)
            if resolved != layout:
                problems.append(
                    f"resolve_target_layout returned {resolved!r}, expected {layout!r}"
                )
            result = INS.install_into_repo(repo, self.source, yes=True, no_color=True)
            if result["target_layout"] != layout:
                problems.append(
                    f"install reported target_layout {result['target_layout']!r}, expected "
                    f"{layout!r}; the resolver and the install disagree, so the summary lies about "
                    "where the framework went"
                )
            for rel in present:
                if not (repo / rel).exists():
                    problems.append(f"{rel} is missing after the install")
            for rel in absent:
                if (repo / rel).exists():
                    problems.append(
                        f"{rel} WAS CREATED and must not be; this is a dual write, which leaves the "
                        "repo with two framework trees and no way to tell which one is live"
                    )
            if problems:
                wrong.append(
                    f"  {case} (pre-existing {dirs or '(nothing)'}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"layout resolution or the install was wrong for {len(wrong)} of {len(self.LAYOUTS)} repo "
            "shapes. One resolver decides all four from the directories present, so read the failures "
            "together: if the LAYOUT NAMES are right and a must-not-exist path appeared, the resolver "
            "is fine and the WRITER is dual-writing; if a legacy repo resolved to `aw`, existing "
            "installs are being silently migrated out from under the user's tooling. FIX: migration is "
            f"an explicit act (`aw migrate-layout`), never a side effect of an update.\n"
            + "\n".join(wrong),
        )

    def test_read_installed_version_finds_the_version_in_either_layout(self):
        """Kept separate: reads a version from a HAND-PLACED file, with no install involved.

        The table above installs; this probes the reader against each layout's VERSION path directly,
        which is what a repo in an unknown state looks like to `aw doctor`.
        """
        wrong = []
        for rel, value in (
            (".aw/system/VERSION", "1.2.3"),
            (".agents/workflows/VERSION", "4.5.6"),
        ):
            repo = init_repo(self.base / f"ver-{value}")
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(f"{value}\n", encoding="utf-8")
            got = INS.read_installed_version(repo)
            if got != value:
                wrong.append(
                    f"  {rel}: read_installed_version gave {got!r}, want {value!r}"
                )
        self.assertEqual(
            wrong,
            [],
            "read_installed_version must find the version in BOTH layouts, since it is what tells a "
            "user which framework version a repo actually has:\n" + "\n".join(wrong),
        )


class SplitBrainLayoutGuardTests(unittest.TestCase):
    """Backlog u298fd: a repo holding BOTH layouts is DETECTED and SKIPPED rather than installed into.

    TWO tables replace eleven tests. The first merges the five detection tests
    (`..._true_on_split_brain`, `..._false_on_clean_aw`, `..._false_on_clean_legacy`,
    `..._false_on_cruft_only`, `..._false_on_empty_agents_dir`), which called ONE predicate on five repo
    shapes: textbook data. The second merges the four guard-decision tests
    (`..._returns_skip_on_yes`, `..._returns_skip_on_non_interactive`, `..._interactive_continue_anyway`,
    `..._interactive_decline_all`), whose difference is the CONSENT MODE and the answers supplied.

    THE FOUR FALSE ROWS CARRY THE WEIGHT in the detection table. A detector that fired on everything
    would satisfy the true row alone while making the installer refuse every repo, and the CRUFT rows
    are the specific reason this is subtle: `__pycache__`, a Windows `Zone.Identifier` file, and an
    empty `.md` are all DEBRIS, not a live legacy install, so a detector keyed on 'does
    `.agents/workflows` contain anything' would refuse to install into perfectly healthy repos.

    EVERY GUARD ROW ALSO ASSERTS THE TREE IS UNCHANGED, because the property is not 'it returned skip'
    but 'it wrote nothing'. A guard that returned `skip` after installing would pass a
    return-value-only check while doing precisely the damage it exists to prevent.

    The two migration-path tests and the four CLI-surface tests stay separate, each saying why.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.term = Term(color=False)

    def tearDown(self):
        self._tmp.cleanup()

    def _make_split_brain_repo(self, name="split_brain_repo") -> Path:
        repo = init_repo(self.base / name)
        (repo / ".aw" / "system" / "workflows").mkdir(parents=True)
        (repo / ".aw" / "system" / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (repo / ".agents" / "workflows").mkdir(parents=True)
        (repo / ".agents" / "workflows" / "index.md").write_text(
            "# Manifest\n", encoding="utf-8"
        )
        return repo

    def _make_clean_aw_repo(self, name="clean_aw_repo") -> Path:
        repo = init_repo(self.base / name)
        (repo / ".aw" / "system" / "workflows").mkdir(parents=True)
        (repo / ".aw" / "system" / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        return repo

    def _make_clean_legacy_repo(self, name="clean_legacy_repo") -> Path:
        repo = init_repo(self.base / name)
        (repo / ".agents" / "workflows").mkdir(parents=True)
        (repo / ".agents" / "workflows" / "index.md").write_text(
            "# Manifest\n", encoding="utf-8"
        )
        return repo

    def _make_cruft_only_repo(self, name="cruft_only_repo") -> Path:
        repo = init_repo(self.base / name)
        (repo / ".aw" / "system" / "workflows").mkdir(parents=True)
        (repo / ".agents" / "workflows" / "__pycache__").mkdir(parents=True)
        (
            repo / ".agents" / "workflows" / "__pycache__" / "foo.cpython-312.pyc"
        ).write_bytes(b"\x00\x01\x02")
        (repo / ".agents" / "workflows" / "test.py:Zone.Identifier").write_text(
            "ZoneId=3\n", encoding="utf-8"
        )
        (repo / ".agents" / "workflows" / "empty.md").write_text("", encoding="utf-8")
        return repo

    def _make_empty_agents_repo(self, name="empty_agents_dir") -> Path:
        repo = init_repo(self.base / name)
        (repo / ".aw" / "system" / "workflows").mkdir(parents=True)
        (repo / ".agents" / "workflows").mkdir(parents=True)
        return repo

    def _tree_files(self, repo: Path):
        return sorted(
            p.relative_to(repo)
            for p in repo.rglob("*")
            if not any(part == ".git" for part in p.parts)
        )

    def test_detection_fires_only_on_a_genuinely_split_repo(self):
        #: (case, factory attribute, expected verdict, why this row exists)
        shapes = (
            (
                "both trees, each with live content",
                "_make_split_brain_repo",
                True,
                "THE ONLY TRUE CASE: a canonical `.aw/system` AND a live `.agents/workflows` with a "
                "real manifest in it. Installing into this writes to one tree while the user's tooling "
                "may read the other, which is why the whole repo is skipped instead",
            ),
            (
                "a clean canonical install",
                "_make_clean_aw_repo",
                False,
                "the overwhelmingly common healthy shape. A detector that fired here would refuse to "
                "install into essentially every repo, so this row is what makes the true row above "
                "mean something",
            ),
            (
                "a clean legacy install",
                "_make_clean_legacy_repo",
                False,
                "the other healthy shape: legacy ALONE is a supported layout, not a split. Asserted "
                "beside the canonical row because a detector keyed on 'is `.agents/workflows` "
                "present' would flag every legacy repo in existence",
            ),
            (
                "canonical plus .agents/workflows holding only DEBRIS",
                "_make_cruft_only_repo",
                False,
                "THE SUBTLE ROW, and the reason this predicate is not a one-liner: `__pycache__`, a "
                "Windows `Zone.Identifier` file and a zero-byte `.md` are leftovers, not an install. A "
                "detector keyed on 'the directory is non-empty' refuses to install into repos that are "
                "merely untidy, and the user has no idea why",
            ),
            (
                "canonical plus a completely EMPTY .agents/workflows",
                "_make_empty_agents_repo",
                False,
                "the boundary of the row above: an empty directory is the residue of a migration that "
                "already happened. It is its own row because emptiness and debris fail a naive "
                "detector in different ways (a count versus a content test)",
            ),
        )
        wrong = []
        false_rows_broken = 0
        for index, (case, factory, expected, why) in enumerate(shapes):
            repo = getattr(self, factory)(f"detect-{index}")
            got = INS.detect_split_brain_layout(repo)
            if got != expected:
                if not expected:
                    false_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - detect_split_brain_layout returned {got}, expected {expected}"
                    + (
                        " - A FALSE POSITIVE: the installer will REFUSE to install into this healthy "
                        "repo and the user gets a skip they cannot explain"
                        if got
                        else " - A FALSE NEGATIVE: the installer will write into a genuinely "
                        "split-brained repo, which is the state this guard exists to avoid touching"
                    )
                    + f"\n    this row exists because: {why}"
                )
        note = ""
        if false_rows_broken:
            note = (
                f" {false_rows_broken} FALSE-verdict row(s) failed, which means the detector is TOO "
                "EAGER; that is the user-visible direction, because every affected repo gets skipped "
                "with no framework update at all."
            )
        self.assertEqual(
            wrong,
            [],
            f"split-brain detection was wrong for {len(wrong)} of {len(shapes)} repo shapes.{note} One "
            "predicate decides all five, so read the failures together: if the DEBRIS and EMPTY rows "
            "fail together, the liveness test degenerated into an existence check and healthy repos "
            "are now being refused; if only the true row fails, the detector stopped firing and "
            f"nothing protects a split repo.\n" + "\n".join(wrong),
        )

    def test_every_consent_mode_skips_without_writing(self):
        #: (case, `args.yes`, isatty, `_prompt_yes_no` answers or None, expected guard result, why)
        modes = (
            (
                "--yes (non-interactive by request)",
                True,
                None,
                None,
                "skip",
                "`--yes` cannot mean 'yes, migrate my layout for me': the user consented to an "
                "INSTALL, not to a layout migration, so the guard skips and WARNS. This is the "
                "row that stops `--yes` becoming a blanket authorization for anything the "
                "installer might want to do",
            ),
            (
                "no TTY (piped or CI)",
                False,
                False,
                None,
                "skip",
                "with no way to ask, the answer is no. A guard that proceeded here would migrate "
                "layouts unattended in CI, where nobody is watching and the failure surfaces much "
                "later as missing workflows",
            ),
            (
                "interactive: decline the migration, then continue anyway",
                False,
                True,
                [False, True],
                "proceed",
                "the user is allowed to say 'do not migrate, but install anyway'. The guard "
                "INFORMS rather than forbids, which is the right balance for a state that is "
                "unusual but not corrupt",
            ),
            (
                "interactive: decline both",
                False,
                True,
                [False, False],
                "skip",
                "declining both questions means skip, which is the PAIRED inverse of the row "
                "above: the same first answer with a different second one must reach the opposite "
                "result, so the two answers are genuinely independent rather than the first "
                "deciding everything",
            ),
        )
        wrong = []
        for index, (case, yes, isatty, answers, expected, why) in enumerate(modes):
            repo = self._make_split_brain_repo(f"guard-{index}")
            before = self._tree_files(repo)
            args = mock.MagicMock()
            args.yes = yes
            status_calls = []
            stub_term = mock.MagicMock()
            stub_term.status.side_effect = lambda level, msg: status_calls.append(
                (level, msg)
            )
            with mock.patch("sys.stdin.isatty", return_value=bool(isatty)):
                if answers is None:
                    got = CLI._split_brain_guard(stub_term, repo, args)
                else:
                    with mock.patch(
                        "agent_workflows.cli._prompt_yes_no", side_effect=answers
                    ):
                        got = CLI._split_brain_guard(stub_term, repo, args)
            problems = []
            if got != expected:
                problems.append(f"the guard returned {got!r}, expected {expected!r}")
            after = self._tree_files(repo)
            if after != before:
                problems.append(
                    f"THE GUARD MODIFIED THE REPO. Added/removed: "
                    f"{sorted(set(map(str, after)) ^ set(map(str, before)))!r}. A guard that returns "
                    "a verdict after writing has already done the damage it exists to prevent"
                )
            if yes and expected == "skip":
                # The --yes path must TELL the user, since they asked for an install and are not
                # getting one.
                if not any(
                    level == "warn" and "split-brain" in msg
                    for level, msg in status_calls
                ):
                    problems.append(
                        "no `warn` status mentioning split-brain was emitted, so a user who asked "
                        "for an install gets silence instead of a reason"
                    )
                if not any(
                    level == "skip" and "split-brain" in msg
                    for level, msg in status_calls
                ):
                    problems.append(
                        "no `skip` status mentioning split-brain was emitted"
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
            f"the split-brain guard mishandled {len(wrong)} of {len(modes)} consent modes. One guard "
            "handles all four, so read the failures together: if every NON-INTERACTIVE row now "
            "proceeds, the guard's default flipped and unattended runs will write into split repos; if "
            "the two INTERACTIVE rows both fail, the prompt answers are not being bound in order and "
            "the second question's answer is being ignored. FIX: check the tree-unchanged failures "
            f"first, since a guard that writes before deciding makes its verdict irrelevant.\n"
            + "\n".join(wrong),
        )

    def test_guard_proceeds_on_every_clean_repo_shape_without_speaking(self):
        """Kept separate: asserts the guard stays SILENT, which the consent table cannot say.

        The healthy shapes must reach `proceed` with NO status output at all, since a guard that warned
        on a clean repo would train users to ignore the warning. `assert_not_called` is a claim about
        the terminal object rather than about the repo, so it is not a row.
        """
        for factory in (
            "_make_clean_aw_repo",
            "_make_clean_legacy_repo",
            "_make_cruft_only_repo",
        ):
            repo = getattr(self, factory)(f"quiet-{factory}")
            args = mock.MagicMock()
            args.yes = True
            stub_term = mock.MagicMock()
            self.assertEqual(
                CLI._split_brain_guard(stub_term, repo, args), "proceed", factory
            )
            stub_term.status.assert_not_called()

    def test_describe_split_brain_contents_and_no_side_effects(self):
        """Kept separate: the subject is the DESCRIPTION STRING (and that describing changes nothing)."""
        repo = self._make_split_brain_repo("describe")
        tree_before = self._tree_files(repo)
        desc = INS.describe_split_brain(repo)
        self.assertEqual(tree_before, self._tree_files(repo))
        self.assertIn(".aw/system", desc)
        self.assertIn(".agents/workflows", desc)
        self.assertIn("aw migrate-layout", desc, "the user must be told the remedy")
        self.assertNotIn(
            "\n", desc.strip(), "the description is a one-liner by contract"
        )

    def test_split_brain_guard_interactive_migrate_now(self):
        """Kept separate: the only path that RUNS a migration, with MigrationManager patched.

        Its real claim is the call signature passed to the migration manager, which no consent row can
        express, and it has to fake the migration's filesystem effect so the guard re-checks cleanly.
        """
        repo = self._make_split_brain_repo("migrate-now")
        args = mock.MagicMock()
        args.yes = False
        stub_term = mock.MagicMock()
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("agent_workflows.cli._prompt_yes_no", side_effect=[True]):
                with mock.patch(
                    "agent_workflows.layout_migration.MigrationManager"
                ) as MockMgr:

                    def fake_migrate(**kwargs):
                        # simulate migration moving .agents/workflows into .aw/
                        for p in list((repo / ".agents" / "workflows").glob("*")):
                            p.unlink()
                        (repo / ".agents" / "workflows").rmdir()

                    MockMgr.return_value.execute_migration.side_effect = fake_migrate
                    result = CLI._split_brain_guard(stub_term, repo, args)
        self.assertEqual(result, "proceed")
        MockMgr.return_value.execute_migration.assert_called_once_with(
            target_backend="repository", leftover_disposition="defer"
        )

    def test_install_one_skips_split_brain_repo_without_writes(self):
        """Kept separate: drives `cli._install_one`, one layer ABOVE the guard, with a full argv namespace."""
        repo = self._make_split_brain_repo("install-one")
        tree_before = self._tree_files(repo)
        args = mock.MagicMock()
        args.yes = True
        args.dry_run = False
        args.no_backup = False
        args.no_prune = False
        args.no_color = True
        stub_term = mock.MagicMock()
        outcome = CLI._install_one(repo, SOURCE_WORKFLOWS, args, stub_term)
        self.assertEqual(outcome, "nochange")
        self.assertEqual(tree_before, self._tree_files(repo))

    def test_cli_install_split_brain_repo_skips_without_writes(self):
        """Kept separate: drives `CLI.main` and asserts USER-FACING output, not a return value."""
        repo = self._make_split_brain_repo("cli-install")
        tree_before = self._tree_files(repo)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = CLI.main(["install", str(repo), "--yes"])
        self.assertEqual(code, 0)
        output = buf.getvalue()
        self.assertIn("split-brain", output)
        self.assertIn("skipped", output)
        self.assertEqual(tree_before, self._tree_files(repo))

    def test_cli_install_all_skips_split_brain_and_installs_clean(self):
        """Kept separate: a BATCH claim needing XDG config manipulation and a registered repo list.

        The property is that one bad repo does not stop the others, which requires two repos and an
        assertion about each; that is not the same shape as a single-repo skip.
        """
        old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        try:
            split_repo = self._make_split_brain_repo("batch-split")
            clean_repo = self._make_clean_aw_repo("batch-clean")
            from agent_workflows import config as CFG

            cfg = CFG.default_config()
            CFG.set_repo_setting(cfg, "installed", [str(split_repo), str(clean_repo)])
            CFG.save(cfg)

            split_tree_before = self._tree_files(split_repo)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = CLI.main(["install", "all", "--yes"])
            self.assertEqual(code, 0)
            self.assertIn("split-brain", buf.getvalue())
            self.assertEqual(split_tree_before, self._tree_files(split_repo))
            # The clean repo in the same batch WAS installed.
            self.assertTrue(
                (clean_repo / ".aw" / "system" / "workflows" / "index.md").is_file()
            )
        finally:
            if old_xdg is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = old_xdg

    def test_cli_setup_skips_split_brain_repo(self):
        """Kept separate: `aw setup` DISCOVERS repos under a root, a different entry point from install all."""
        old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg-setup")
        try:
            split_repo = self._make_split_brain_repo("setup-split")
            clean_repo = self._make_clean_aw_repo("setup-clean")
            split_tree_before = self._tree_files(split_repo)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = CLI.main(["setup", "--root", str(self.base), "--yes"])
            self.assertEqual(code, 0)
            self.assertIn("split-brain", buf.getvalue())
            self.assertEqual(split_tree_before, self._tree_files(split_repo))
            self.assertTrue(
                (clean_repo / ".aw" / "system" / "workflows" / "index.md").is_file()
            )
        finally:
            if old_xdg is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = old_xdg


class UninstallCompletenessTests(unittest.TestCase):
    """Complete uninstall, orphaned lifecycle removal, and the records KEEP/REMOVE choice.

    Left un-merged: these are the most destructive paths in the codebase and each asserts a different
    containment boundary (base uninstall reaching config/state/marker while PRESERVING records; deep
    cleanup with records REMOVE leaving nothing; deep cleanup with records KEEP preserving exactly the
    records; and the plan's partition being a true bijection). A row per mode would put 'planned the
    wrong partition' and 'deleted a user's records' in one failure message, and the second is
    unrecoverable.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self):
        self._tmp.cleanup()

    def test_uninstall_removes_config_state_gitignore_and_setup_marker(self):
        """E-01, E-02, V-01, V-02: base uninstall removes config/state/.gitignore/setup-marker."""
        repo = init_repo(self.base / "uninstall_complete")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        # Add config/project.json (tracked), config/local.json (untracked), state files, and marker
        cfg_dir = repo / ".aw" / "config"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_proj = cfg_dir / "project.json"
        cfg_proj.write_text('{"preset": "private-target"}\n', encoding="utf-8")
        git(repo, "add", ".aw/config/project.json")
        git(repo, "commit", "-m", "add project config")

        cfg_local = cfg_dir / "local.json"
        cfg_local.write_text('{"target": "local"}\n', encoding="utf-8")

        state_dir = repo / ".aw" / "state" / "durable"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_install = state_dir / "install.json"
        state_install.write_text('{"installed": true}\n', encoding="utf-8")

        INS.write_setup_marker(repo)

        self.assertTrue(cfg_proj.is_file())
        self.assertTrue(cfg_local.is_file())
        self.assertTrue(state_install.is_file())
        self.assertTrue((repo / ".aw" / ".gitignore").is_file())
        self.assertTrue((repo / ".aw" / "setup-repo-needed.md").is_file())

        changed: list[str] = []
        actions = INS.uninstall_repo(
            repo, use_git=True, force=True, changed_out=changed
        )
        self.assertTrue(len(actions) > 0)
        self.assertIn("removed .aw/config/project.json", actions)

        self.assertFalse(cfg_proj.exists())
        self.assertFalse(cfg_local.exists())
        self.assertFalse(cfg_dir.exists())
        self.assertFalse(state_install.exists())
        self.assertFalse((repo / ".aw" / "state").exists())
        self.assertFalse((repo / ".aw" / ".gitignore").exists())
        self.assertFalse((repo / ".aw" / "setup-repo-needed.md").exists())
        self.assertIn(".aw/config/project.json", changed)
        self.assertIn(".aw/.gitignore", changed)
        self.assertIn(".aw/setup-repo-needed.md", changed)
        # Records must still be preserved here (base uninstall does not remove records)
        self.assertTrue((repo / ".aw" / "records").exists())

    def test_deep_cleanup_records_remove_leaves_no_aw_directory(self):
        """E-04, V-04: install -> uninstall -> deep cleanup with records REMOVE leaves NO .aw/ directory.

        PRE-EXISTING FAILURE, NOT INTRODUCED BY THE TABLE WORK, and kept rather than weakened: verified
        failing at HEAD (commit 6123749b) before this file was touched. Measured cause: after the full
        sequence, `.aw/system/layout.json` and `.aw/system/layout.schema.json` survive. Those are the
        install-time-emitted layout artifacts (wslayout Order 04, spec kw5y2s 6.1), a feature added
        AFTER this test was written, and neither the uninstall path nor `plan_deep_cleanup` enumerates
        them, so `.aw/system/` cannot be pruned. This is a real completeness gap in
        `agent_workflows/`, whose fix is a product change this test-only change must not make.
        """
        repo = init_repo(self.base / "deep_clean_remove")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        INS.write_setup_marker(repo)

        # Plant untracked user record to test unlink + directory pruning
        untracked = (
            repo / ".aw" / "records" / "plans" / "pending" / "untracked.untracked.md"
        )
        untracked.write_text("# Untracked\n", encoding="utf-8")

        INS.uninstall_repo(repo, use_git=True, force=True)
        plan = INS.plan_deep_cleanup(repo)
        self.assertFalse(plan.is_empty)
        self.assertIn(
            ".aw/records/plans/pending/untracked.untracked.md", plan.records_files
        )
        INS.run_deep_cleanup(repo, plan, use_git=True, remove_records=True)

        self.assertFalse(
            (repo / ".aw").exists(),
            "NO .aw/ directory must remain after deep cleanup removing records",
        )

    def test_deep_cleanup_records_keep_preserves_records_and_removes_other(self):
        """E-03, E-04, V-03, V-04: the PAIRED inverse: records KEEP preserves .aw/records/ exactly."""
        repo = init_repo(self.base / "deep_clean_keep")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)
        INS.write_setup_marker(repo)

        # Plant a user record
        user_plan = repo / ".aw" / "records" / "plans" / "pending" / "my-plan.ipd.md"
        user_plan.write_text("# My Plan\n", encoding="utf-8")

        INS.uninstall_repo(repo, use_git=True, force=True)
        plan = INS.plan_deep_cleanup(repo)
        self.assertIn(".aw/records/plans/pending/my-plan.ipd.md", plan.records_files)

        INS.run_deep_cleanup(repo, plan, use_git=True, remove_records=False)

        self.assertTrue(
            user_plan.is_file(), "User record must be preserved when records are kept"
        )
        self.assertTrue((repo / ".aw" / "records").is_dir(), ".aw/records/ must remain")
        self.assertTrue((repo / ".aw").is_dir(), ".aw/ parent must remain for records")
        self.assertFalse((repo / ".aw" / "config").exists())
        self.assertFalse((repo / ".aw" / "state").exists())
        self.assertFalse((repo / ".aw" / ".gitignore").exists())
        self.assertFalse((repo / ".aw" / "setup-repo-needed.md").exists())
        self.assertFalse(
            (repo / ".gitleaksignore").exists(),
            "Non-records scaffolding must be removed",
        )

    def test_deep_cleanup_plan_partitions_records_and_other(self):
        """E-03, V-03: the partition is a true BIJECTION, which is a set-algebra claim."""
        repo = init_repo(self.base / "plan_partition")
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)

        plan = INS.plan_deep_cleanup(repo)
        self.assertTrue(len(plan.records_files) > 0)
        self.assertTrue(len(plan.other_files) > 0)
        self.assertEqual(
            sorted(plan.files), sorted(plan.records_files + plan.other_files)
        )
        for f in plan.records_files:
            self.assertTrue(f.startswith((".aw/records/", ".agents/")))
        for f in plan.other_files:
            self.assertFalse(f.startswith((".aw/records/", ".agents/")))
        self.assertIn(".gitleaksignore", plan.other_files)


class AwGitignoreLaneTests(unittest.TestCase):
    """The framework-owned `.aw/.gitignore` lanes: the pattern is present, anchored, and EFFECTIVE.

    ONE table replaces nine tests across two classes (`AwGitignoreRunsLaneTests` and
    `AwGitignoreInboxLaneTests`). Every one of them called `_ensure_aw_gitignore` on a temp root and
    counted occurrences of one pattern, in one of three prior states: no file at all (the template
    branch), a file predating the lane (the back-fill branch), or a file already carrying it (the
    idempotence check). The LANE is the data and the PRIOR STATE is a column, asserted for every lane
    rather than once per lane.

    EVERY ROW GOES THROUGH ALL THREE STATES, which is what the old tests did unevenly: `records/runs/`
    had a back-fill test and `inbox/` had one plus a repair test, so a lane added to the template but
    omitted from the back-fill list would reach no already-installed repo and only the lane whose test
    happened to cover it would notice. Here the gap is structural rather than a matter of which test
    someone remembered to write.

    THE ANCHORING COLUMN IS THE SAFETY COLUMN, and it has a MEASURED history: a bare `inbox/` is
    unanchored, matches an `inbox` directory at ANY depth, and therefore ignored the TRACKED
    `records/comms/shared/inbox/` lane and its `.gitkeep`, which BROKE `aw install` on a fresh repo.
    So an anchored lane asserts three things a presence check cannot: the anchored form is present, the
    bare form is ABSENT, and a pre-existing bare form is REPAIRED rather than left in place, since
    leaving it would keep breaking exactly the repos that already installed it.

    The end-to-end git test stays separate; it is the only one that proves EFFECT rather than text.
    """

    #: (lane, the exact pattern line, whether it must be ANCHORED (leading slash, bare form forbidden),
    #: a pre-lane `.aw/.gitignore` body for the back-fill check, why this row exists)
    LANES = (
        (
            "the IPD-driver per-run state tree",
            "records/runs/",
            False,
            "records/*/untracked/\nsetup-repo-needed.md\n",
            "queue state, session JSONL logs, prompts, outcomes and the driver lock: box-local and "
            "ephemeral. Deliberately UNANCHORED, because it is a `records/`-relative path rather than "
            "a top-level directory name, so it is the row that shows anchoring is a per-pattern "
            "judgement and not a blanket rule",
        ),
        (
            "the append-only workflow-history sidecar",
            "records/history.jsonl",
            False,
            "records/*/untracked/\nsetup-repo-needed.md\n",
            "appended on EVERY `aw` status write, so a tracked copy is a diff on nearly every command "
            "and a conflict on every concurrent lane. Its back-fill body predates BOTH it and the "
            "runs lane, which is what proves the back-fill adds each missing pattern independently "
            "rather than all-or-nothing",
        ),
        (
            "the raw-drop inbox",
            "/inbox/",
            True,
            "records/*/untracked/\nsetup-repo-needed.md\n"
            "records/history.jsonl\nrecords/runs/\n",
            "THE ROW WITH THE MEASURED FAILURE: unvetted external material that must never be "
            "committed, and the pattern MUST be anchored. The bare form matched an `inbox` directory "
            "at any depth, silently ignoring the TRACKED `records/comms/shared/inbox/` lane and its "
            "`.gitkeep`, which broke `aw install` on a fresh repo. Its back-fill body is the "
            "post-runs-lane state, i.e. a repo installed just before the inbox existed",
        ),
    )

    @staticmethod
    def _pattern_lines(text, pattern):
        """Count only the PATTERN line, never the explanatory comment that names it too."""
        bare = pattern.lstrip("/")
        return [
            ln
            for ln in text.splitlines()
            if ln.strip() in (pattern, bare) and not ln.strip().startswith("#")
        ]

    def test_every_lane_is_present_anchored_backfilled_and_idempotent(self):
        wrong = []
        for lane, pattern, anchored, pre_existing, why in self.LANES:
            problems = []
            bare = pattern.lstrip("/")

            # (a) THE TEMPLATE: a fresh install writes it verbatim, so the pattern must be here.
            template_lines = self._pattern_lines(INS._AW_GITIGNORE_TEMPLATE, pattern)
            if len(template_lines) != 1:
                problems.append(
                    f"the template carries {len(template_lines)} pattern line(s) for this lane, want "
                    "exactly 1; a fresh install writes the template verbatim, so a missing pattern "
                    "reaches no new repo"
                )
            elif template_lines[0].strip() != pattern:
                problems.append(
                    f"the template carries {template_lines[0].strip()!r}, want {pattern!r}"
                )
            if anchored:
                if any(
                    ln.strip() == bare
                    for ln in INS._AW_GITIGNORE_TEMPLATE.splitlines()
                    if not ln.strip().startswith("#")
                ):
                    problems.append(
                        f"the template carries the UNANCHORED form {bare!r}, which matches a "
                        "directory of that name at ANY depth and swallows tracked lanes"
                    )

            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                gi = root / ".aw" / ".gitignore"

                # (b) FRESH: no file at all -> the template branch writes it once, and repeated
                # passes never duplicate it.
                INS._ensure_aw_gitignore(root)
                if not gi.is_file():
                    problems.append(
                        "_ensure_aw_gitignore created no .aw/.gitignore at all"
                    )
                else:
                    for _ in range(3):
                        INS._ensure_aw_gitignore(root)
                    count = len(
                        self._pattern_lines(gi.read_text(encoding="utf-8"), pattern)
                    )
                    if count != 1:
                        problems.append(
                            f"after a fresh write plus three more passes there are {count} pattern "
                            "line(s), want 1; the helper runs several times per install, so a "
                            "non-idempotent add accrues lines on every run"
                        )

            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                gi = root / ".aw" / ".gitignore"
                gi.parent.mkdir(parents=True)
                # (c) BACK-FILL: a repo installed BEFORE this lane existed already HAS the file, so
                # only the append branch runs and the template is never re-read.
                gi.write_text(pre_existing, encoding="utf-8")
                INS._ensure_aw_gitignore(root)
                text = gi.read_text(encoding="utf-8")
                lines = self._pattern_lines(text, pattern)
                if [ln.strip() for ln in lines] != [pattern]:
                    problems.append(
                        f"the back-fill produced {[ln.strip() for ln in lines]!r}, want exactly "
                        f"[{pattern!r}]. This is the ONLY path that reaches an already-installed "
                        "repo, and a pattern present in the template but missing from the back-fill "
                        "list leaves every existing repo broken forever"
                    )
                for survivor in ("records/*/untracked/", "setup-repo-needed.md"):
                    if survivor in pre_existing and survivor not in text:
                        problems.append(
                            f"the back-fill CLOBBERED the pre-existing line {survivor!r}"
                        )
                INS._ensure_aw_gitignore(root)
                if (
                    len(self._pattern_lines(gi.read_text(encoding="utf-8"), pattern))
                    != 1
                ):
                    problems.append(
                        "a second back-fill pass duplicated the pattern, so the append branch does "
                        "not detect what it already wrote"
                    )

            if anchored:
                with tempfile.TemporaryDirectory() as d:
                    root = Path(d)
                    gi = root / ".aw" / ".gitignore"
                    gi.parent.mkdir(parents=True)
                    # (d) REPAIR: a repo that already carries the BROKEN unanchored form must be
                    # fixed, not left as-is.
                    gi.write_text(f"records/runs/\n{bare}\n", encoding="utf-8")
                    INS._ensure_aw_gitignore(root)
                    text = gi.read_text(encoding="utf-8")
                    if [ln.strip() for ln in self._pattern_lines(text, pattern)] != [
                        pattern
                    ]:
                        problems.append(
                            f"a pre-existing UNANCHORED {bare!r} was not repaired to {pattern!r}; "
                            "leaving it keeps breaking `aw install` in exactly the repos that "
                            "installed the broken form"
                        )
                    if re.search(rf"(?m)^{re.escape(bare)}[ \t]*$", text):
                        problems.append(
                            f"the unanchored {bare!r} line survived the repair"
                        )
                    INS._ensure_aw_gitignore(root)
                    if (
                        len(
                            self._pattern_lines(gi.read_text(encoding="utf-8"), pattern)
                        )
                        != 1
                    ):
                        problems.append(
                            "the repair duplicated the pattern on a later pass"
                        )

            if problems:
                wrong.append(
                    f"  {lane} (pattern {pattern!r}, anchored={anchored}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.LANES)} gitignore lanes were mishandled. Each row is checked "
            "through the template, the fresh-write branch, the back-fill branch and (where anchored) "
            "the repair branch, all implemented by ONE helper, so read the failures together: if every "
            "lane fails its BACK-FILL check, the append branch or its pattern list broke and no "
            "existing repo will ever be fixed; if every lane fails the TEMPLATE check, new repos are "
            "affected instead; if only the anchored lane fails, the `/inbox/` trap has been "
            "reintroduced and a TRACKED lane is being ignored, which breaks `aw install` outright. "
            f"FIX: the template and the back-fill list are two places one contract is written, and a "
            f"lane must be added to BOTH.\n" + "\n".join(wrong),
        )

    def test_git_ignores_aw_inbox_but_not_the_tracked_comms_inbox_lane(self):
        """Kept separate: the only END-TO-END claim here, and the one that actually pins the bug.

        The table above reads the generated file's TEXT; this asks real git. The two `inbox` directories
        must be treated DIFFERENTLY (`.aw/inbox/` ignored, `.aw/records/comms/shared/inbox/` not), and
        the unanchored pattern satisfies every string-level check while ignoring both.
        """
        with tempfile.TemporaryDirectory() as d:
            root = init_repo(Path(d) / "repo")
            INS._ensure_aw_gitignore(root)
            drop = root / ".aw" / "inbox" / "raw-external-report.md"
            lane = root / ".aw" / "records" / "comms" / "shared" / "inbox" / ".gitkeep"
            for f in (drop, lane):
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("", encoding="utf-8")

            def ignored(path):
                return (
                    git(
                        root, "check-ignore", "-q", str(path.relative_to(root))
                    ).returncode
                    == 0
                )

            self.assertTrue(ignored(drop), ".aw/inbox/ must be gitignored")
            self.assertFalse(
                ignored(lane),
                "the TRACKED records/comms/shared/inbox/ lane must NOT be gitignored",
            )


if __name__ == "__main__":
    unittest.main()
