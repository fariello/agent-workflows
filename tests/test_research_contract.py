"""Tests for the canonical research-artifact contract (Set research-org, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies the contract against the specification
.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md (Sections 4.1, 4.2, 4.4,
4.5, 4.9, 5.4, 5.8).

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: hand a pure contract
function one token and assert it is accepted (and to what it normalizes) or rejected. That is a
(token -> verdict) table, which is the natural shape for a GRAMMAR plus a set of CLOSED VOCABULARIES.

ACCEPT AND REJECT ROWS LIVE IN THE SAME TABLE, and that is the single most important structural
decision here. This contract is machine-readable: `aw research` derives names from it and other
tooling PARSES those names back, so the failure that matters is not "one token moved" but "the
validator stopped discriminating". A table of only-accept rows is satisfied by a function that
returns ok for everything, and a table of only-reject rows by one that returns ok for nothing;
together they are satisfiable by neither, and each table's failure message says which direction
collapsed.

THE FILENAME GRAMMAR TOKENS ARE ASSERTED VERBATIM, never as "an error appeared". Parsers read
`YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.<model>.<kind>.md` literally and humans read the refusal text,
so a respelling is a BREAKING CHANGE and must fail here. Expected names and expected messages are
written as LITERAL STRINGS rather than rebuilt from the module's own regexes or constants, because a
constant and the value it produces move together and a respelling would be invisible.

WHAT WAS A CLASS PER FUNCTION IS NOW A COLUMN WHERE THE FUNCTION IS A MODE: the four normalizers
(`kind`, `model`, `status`, `kebab`) share one table under a VOCABULARY column, because they are one
behavior (fold a drifted spelling onto the canonical token, or refuse it with a hint) applied to four
closed sets. A regression in that shared machinery lights up rows across every vocabulary at once,
which N per-function tests actively hide.

Tests that are NOT rows carry a one-line docstring saying why they stay separate.
"""

from __future__ import annotations

import unittest

from agent_workflows import research_contract as R


# --------------------------------------------------------------------------------------------------
# The `sense` column shared by the accept/reject tables.
# --------------------------------------------------------------------------------------------------

ACCEPT = "accept"
REJECT = "reject"


class Id6Tests(unittest.TestCase):
    """Which 6-char tokens `is_valid_id6` admits as an artifact identity.

    ONE table replaces three tests (`test_valid_id6`, `test_reject_wrong_length`,
    `test_reject_non_base36`). All three called the same predicate with one token and asserted a
    bool, differing only in the token and in the SENSE of the expected answer, so the sense is a
    column rather than a reason for a second test.

    Why the table beats the three: an id6 is the STABLE HANDLE every records tree keys on, and the
    grammar is two independent rules (exactly 6 characters, and every character in base36-lowercase).
    A regression in either rule moves a legible GROUP of rows - both length rows failing together
    means the length check went, both case/punctuation rows means the alphabet check did - and that
    grouping is the information needed to fix it. Three tests report it as three unrelated `False is
    not true` lines.

    THE ACCEPT ROWS ARE IN THE SAME TABLE deliberately: a predicate that returned False for
    everything satisfies every reject row on its own, and one that returned True for everything
    satisfies every accept row. The failure message names which direction collapsed.
    """

    #: (token, ACCEPT or REJECT, why this row exists)
    ID6S = (
        (
            "k7m2xq",
            ACCEPT,
            "THE ORDINARY CASE: six base36-lowercase characters, letters and digits mixed. This is "
            "the shape `aw research new` mints, so every reject row below is vacuous while this row "
            "is broken",
        ),
        (
            "000000",
            ACCEPT,
            "THE ALL-DIGIT BOUNDARY of the alphabet. A validator implemented with a 'must contain a "
            "letter' heuristic, or one that treats the token as a number and drops leading zeros, "
            "refuses exactly this and nothing else",
        ),
        (
            "zzzzzz",
            ACCEPT,
            "the other end of the same boundary, all-letter and the alphabet's last character. "
            "Together with the row above it pins the interval rather than one interior point",
        ),
        (
            "k7m2x",
            REJECT,
            "FIVE CHARACTERS: the length is EXACT, not a minimum. A short id6 would collide sooner "
            "and, worse, would parse out of a filename leaving a stray character in the slug",
        ),
        (
            "k7m2xqq",
            REJECT,
            "SEVEN CHARACTERS: the length is exact in the other direction too. A too-long token "
            "accepted here would be truncated by every consumer that slices six characters, so two "
            "distinct artifacts would answer to one handle",
        ),
        (
            "K7M2XQ",
            REJECT,
            "UPPERCASE IS NOT A SPELLING OF THE SAME ID, it is invalid. Accepting it would make "
            "`K7M2XQ` and `k7m2xq` two handles for one artifact on a case-sensitive filesystem and "
            "one handle on a case-insensitive one, which is how a records tree comes to disagree "
            "with itself across machines",
        ),
        (
            "k7m2x-",
            REJECT,
            "THE HYPHEN IS THE FILENAME'S FIELD SEPARATOR, so it can never be inside an id6: a token "
            "containing one would make `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>` ambiguous to split",
        ),
        (
            "k7m2x_",
            REJECT,
            "the underscore is the other plausible non-alnum character to leak in from a Python "
            "identifier or a slugifier. Base36 means alnum ONLY, and this row states that the rule "
            "is an alphabet allowlist rather than a hyphen denylist",
        ),
    )

    def test_only_base36_lowercase_tokens_of_length_six_are_valid(self):
        wrong = []
        accept_rows_broken = 0
        reject_rows_broken = 0
        for token, sense, why in self.ID6S:
            got = R.is_valid_id6(token)
            want = sense == ACCEPT
            if got is not want:
                if want:
                    accept_rows_broken += 1
                else:
                    reject_rows_broken += 1
                wrong.append(
                    f"  {token!r} ({len(token)} chars): expected is_valid_id6 to {sense} it "
                    f"(return {want}), got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        direction = ""
        if accept_rows_broken and not reject_rows_broken:
            direction = (
                f" ALL {accept_rows_broken} failing row(s) are ACCEPT rows, so the predicate has "
                "narrowed: legitimate ids are being refused, which breaks every existing artifact "
                "rather than only new ones."
            )
        elif reject_rows_broken and not accept_rows_broken:
            direction = (
                f" ALL {reject_rows_broken} failing row(s) are REJECT rows, so the predicate has "
                "WIDENED and is no longer discriminating; a predicate that returns True for "
                "everything passes every ACCEPT row here, which is why both senses share one table."
            )
        self.assertEqual(
            wrong,
            [],
            f"`is_valid_id6` misjudged {len(wrong)} of {len(self.ID6S)} tokens.{direction} Two "
            "independent rules decide every row (length is EXACTLY 6, alphabet is base36-lowercase), "
            "so read the grouping: both length rows failing together means the length check went, "
            "both of the case/punctuation rows means the alphabet check did. FIX: an id6 is the "
            "stable handle every records tree keys on, so a widened predicate does not merely accept "
            "a bad name, it lets two artifacts answer to one handle.\n"
            + "\n".join(wrong),
        )

    def test_id6_is_found_at_word_boundaries_in_filenames_and_in_prose(self):
        """Kept separate: EXTRACTION from surrounding text, not validation of one token.

        `iter_id6_in_text` scans for candidates inside hyphen-delimited filenames and inside running
        prose, so its subject is a word-boundary rule rather than the alphabet/length grammar the
        table above pins. Note the filename case legitimately yields a SECOND candidate (`report`, a
        6-char alnum word in the `.research-report` facet), which is why membership rather than the
        exact list is asserted there.
        """
        found = R.iter_id6_in_text(
            "20260726-aw-delivery-02-k7m2xq-notes.gpt56.research-report.md"
        )
        self.assertIn("k7m2xq", found)
        self.assertEqual(R.iter_id6_in_text("see k7m2xq for details"), ["k7m2xq"])


#: `VOCABULARY` column values: which normalizer a row exercises.
KIND = "normalize_kind"
MODEL = "normalize_model"
STATUS = "normalize_status"
KEBAB = "kebab"


class NormalizationTests(unittest.TestCase):
    """What every closed vocabulary accepts, what it folds a drifted spelling onto, and what it refuses.

    ONE table replaces eleven tests spread over three classes (`VocabTests`, `KebabTests`, and
    `SchemaConstantsTests.test_legacy_intake_normalizes_to_todo`). Every one of them had the identical
    shape: hand a normalizer one token and assert `ok` plus the canonical `value`. The class
    boundaries tracked WHICH FUNCTION implements the fold, which is an implementation detail; the
    behavior is one policy applied to four closed sets.

    THE VOCABULARY IS A COLUMN, and that is what the merge bought. All four normalizers share one
    fold-then-validate implementation with a per-vocabulary alias map, so the realistic regression is
    in the shared machinery and it moves rows across EVERY vocabulary at once. Eleven tests report
    that as eleven unrelated failures in three classes; the table reports one failure whose grouping
    says whether the fold broke everywhere or one alias map lost an entry.

    THE REJECT ROWS ARE IN THE SAME TABLE, with their message needles, because this contract exists
    to be MACHINE-READ: a normalizer that answered `ok` for every token would satisfy every accept
    row on its own, and the accept rows would then prove nothing at all. The failure message says so
    outright when a reject row is among the failures.

    ROWS PIN THE CANONICAL VALUE EXACTLY, never merely `ok`. The value is what gets written into a
    filename facet and later parsed back, so folding `gemini38flash` onto `gemini36flash` would file
    a report under a model that did not write it - a provenance loss the facet exists to prevent, and
    one an `ok`-only assertion cannot see. The `gemini38flash` and `gemini36flash` rows sit adjacent
    for exactly that reason: two exact-value rows are strictly stronger than the inequality assertion
    they replace.
    """

    #: The four normalizers, each adapted to one shape: token -> (ok, value, message, suggestion).
    #: `kebab` is here because slugifying IS a normalization; it simply cannot fail, so its rows
    #: carry `ok=True` and are judged on the canonical value alone.
    NORMALIZERS = {
        KIND: lambda t: (
            R.normalize_kind(t).ok,
            R.normalize_kind(t).value,
            R.normalize_kind(t).message,
            R.normalize_kind(t).suggestion,
        ),
        MODEL: lambda t: (
            R.normalize_model(t).ok,
            R.normalize_model(t).value,
            R.normalize_model(t).message,
            R.normalize_model(t).suggestion,
        ),
        STATUS: lambda t: (
            R.normalize_status(t).ok,
            R.normalize_status(t).value,
            R.normalize_status(t).message,
            R.normalize_status(t).suggestion,
        ),
        KEBAB: lambda t: (True, R.kebab(t), "", None),
    }

    #: (vocabulary, input token, ACCEPT or REJECT, the EXACT canonical value (None on a reject), a
    #: substring the message must contain or None, whether a closest-match suggestion is REQUIRED,
    #: why this row exists)
    NORMALIZATIONS = (
        (
            KIND,
            "research-report",
            ACCEPT,
            "research-report",
            None,
            False,
            "THE IDENTITY CASE: a canonical kind must survive normalization UNCHANGED. Every fold row "
            "below is vacuous while this is broken, because a normalizer that rewrote everything "
            "would still appear to 'normalize correctly' on the alias rows alone",
        ),
        (
            KIND,
            "finding",
            ACCEPT,
            "findings",
            None,
            False,
            "THE SINGULAR/PLURAL FOLD, the commonest human slip when naming a findings artifact. It "
            "must land on the PLURAL canonical token, because the kind is a filename facet and a "
            "`.finding.md` file would be invisible to every consumer globbing `.findings.md`",
        ),
        (
            KIND,
            "reserch-reprt",
            REJECT,
            None,
            "unknown kind",
            True,
            "A TYPO MUST BE REFUSED WITH A HINT, not silently guessed into the nearest kind. The "
            "suggestion is REQUIRED because refusing without one strands the author, while folding "
            "automatically would file the artifact under a kind nobody chose. Note the closest match "
            "here is `research-prompt`, NOT `research-report`, which is precisely why the hint is "
            "advice and the fold is refused",
        ),
        (
            MODEL,
            "sonnet5",
            ACCEPT,
            "sonnet5",
            None,
            False,
            "the model vocabulary's identity case, the twin of the canonical-kind row: a known model "
            "token passes through unchanged",
        ),
        (
            MODEL,
            "gpt-56",
            ACCEPT,
            "gpt56",
            None,
            False,
            "HYPHEN DRIFT: humans write the model the way the vendor does, with a hyphen, while the "
            "facet grammar reserves the hyphen as the filename's field separator. So this fold is not "
            "cosmetic - an unfolded `gpt-56` facet would make the name ambiguous to split",
        ),
        (
            MODEL,
            "chatgpt",
            ACCEPT,
            "gpt56",
            None,
            False,
            "A PRODUCT NAME MAPS ONTO THE MODEL THAT ANSWERED. The provenance the facet records is "
            "which model wrote the report, not which product surface it was typed into, so the alias "
            "must resolve rather than being accepted as a distinct value",
        ),
        (
            MODEL,
            "llama99",
            REJECT,
            None,
            "unknown model",
            False,
            "AN UNKNOWN MODEL IS REFUSED, and this row carries the load for the whole accept half: "
            "the vocabulary is CLOSED, so a normalizer that accepted any well-formed token would pass "
            "every accept row above while recording provenance nobody can verify. No suggestion is "
            "required because nothing in the vocabulary is close",
        ),
        (
            MODEL,
            "gpt56solhigh",
            ACCEPT,
            "gpt56solhigh",
            None,
            False,
            "REASONING EFFORT IS PART OF THE MODEL IDENTITY. Each effort row is a configuration that "
            "produced a real report in the `awmetastore` comparison set, so a high-effort run must be "
            "nameable distinctly from a default one",
        ),
        (
            MODEL,
            "sonnet5high",
            ACCEPT,
            "sonnet5high",
            None,
            False,
            "EFFORT IS NOT A gpt56-ONLY PRIVILEGE, which is the bug this family of rows was added "
            "for: the vocabulary originally encoded effort for gpt56 alone, so a genuine high-effort "
            "Sonnet report could not be named at all",
        ),
        (
            MODEL,
            "gemini31prohigh",
            ACCEPT,
            "gemini31prohigh",
            None,
            False,
            "the same property across a THIRD family, so the effort suffix is shown to be general "
            "rather than enumerated per vendor",
        ),
        (
            MODEL,
            "gemini38flashhigh",
            ACCEPT,
            "gemini38flashhigh",
            None,
            False,
            "effort on a model whose own token already carries a variant (`flash`), which is where a "
            "suffix-stripping implementation breaks first",
        ),
        (
            MODEL,
            "sonnet-5-high",
            ACCEPT,
            "sonnet5high",
            None,
            False,
            "EFFORT SPELLING DRIFT: the hyphenated form a human types must fold onto the effort token, "
            "not merely onto the base model. Dropping the effort silently would record a default-effort "
            "provenance for a high-effort report",
        ),
        (
            MODEL,
            "gpt56-sol-high",
            ACCEPT,
            "gpt56solhigh",
            None,
            False,
            "the same drift with TWO interior hyphens, so the fold is shown to be a general separator "
            "strip rather than a single-hyphen special case",
        ),
        (
            MODEL,
            "gemini-31-pro-high",
            ACCEPT,
            "gemini31prohigh",
            None,
            False,
            "the drift form with THREE hyphens, spanning vendor, version and variant. This is the "
            "shape a human copies straight out of vendor documentation",
        ),
        (
            MODEL,
            "gemini38flash-high",
            ACCEPT,
            "gemini38flashhigh",
            None,
            False,
            "PARTIAL drift: the base token already canonical and only the effort hyphenated. A fold "
            "keyed to the whole string rather than to separators would miss exactly this",
        ),
        (
            MODEL,
            "gemini38flash",
            ACCEPT,
            "gemini38flash",
            None,
            False,
            "A NEW MODEL MUST NEVER BE FOLDED ONTO AN OLDER ONE'S TOKEN. With the row below, these "
            "two pin `gemini38flash` and `gemini36flash` as DISTINCT canonical values; collapsing "
            "them (which the closest-match hint would invite) would file a report under a model that "
            "did not write it. Two exact-value rows are strictly stronger than the inequality "
            "assertion this replaced",
        ),
        (
            MODEL,
            "gemini36flash",
            ACCEPT,
            "gemini36flash",
            None,
            False,
            "the other half of that pair: the OLDER model keeps its own token. If either row's value "
            "moved onto the other's, provenance for a whole comparison set would be wrong while every "
            "other row here still passed",
        ),
        (
            STATUS,
            "todo",
            ACCEPT,
            "todo",
            None,
            False,
            "the canonical lifecycle status, unchanged. `todo` is the name this status settled on "
            "(rstodo `p3o9je` renamed it from `intake`)",
        ),
        (
            STATUS,
            "intake",
            ACCEPT,
            "todo",
            None,
            False,
            "BACKWARD COMPATIBILITY IS A CONTRACT: `intake` is the pre-rename spelling and real "
            "artifacts on disk still carry it, so it must fold onto `todo` rather than be refused. A "
            "rename that dropped this alias would invalidate history that is already written",
        ),
        (
            KEBAB,
            "AW Delivery & Clean Delta",
            ACCEPT,
            "aw-delivery-clean-delta",
            None,
            False,
            "the slug facet must be lowercase kebab-case with PUNCTUATION DROPPED, not merely "
            "space-substituted: an `&` surviving into a filename is a shell metacharacter, and "
            "uppercase would break the same cross-platform case collision the id6 rule guards",
        ),
        (
            KEBAB,
            "  spaced  out  ",
            ACCEPT,
            "spaced-out",
            None,
            False,
            "RUNS OF WHITESPACE COLLAPSE AND EDGES ARE TRIMMED, so a copy-pasted title cannot produce "
            "`-spaced--out-` with leading, doubled or trailing separators - each of which would make "
            "the name unparseable by the field-splitting grammar",
        ),
    )

    def test_every_vocabulary_folds_its_aliases_and_refuses_what_is_not_in_it(self):
        wrong = []
        reject_rows_broken = 0
        identity_rows_broken = 0
        for (
            vocab,
            token,
            sense,
            value,
            needle,
            wants_suggestion,
            why,
        ) in self.NORMALIZATIONS:
            ok, got_value, message, suggestion = self.NORMALIZERS[vocab](token)
            problems = []
            want_ok = sense == ACCEPT
            if ok is not want_ok:
                problems.append(
                    f"expected ok={want_ok} ({sense}), got ok={ok!r} with message {message!r}"
                )
                if not want_ok:
                    reject_rows_broken += 1
            if got_value != value:
                problems.append(
                    f"canonical value is {got_value!r}, expected {value!r}; the value is what gets "
                    "WRITTEN INTO THE FILENAME and parsed back, so a wrong one misfiles the artifact"
                )
                if want_ok and token == value:
                    identity_rows_broken += 1
            if needle is not None and needle not in (message or ""):
                problems.append(
                    f"the refusal message must contain {needle!r} (humans and `aw research` both "
                    f"read it); got {message!r}"
                )
            if wants_suggestion and not suggestion:
                problems.append(
                    "a closest-match suggestion is REQUIRED on this refusal, so the author is told "
                    f"what to write instead; got suggestion={suggestion!r}"
                )
            if problems:
                wrong.append(
                    f"  {vocab}({token!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if reject_rows_broken:
            extra += (
                f" {reject_rows_broken} REJECT row(s) are among the failures, and while any of those "
                "is broken every ACCEPT row here is VACUOUS: a normalizer that returns ok for "
                "everything satisfies all of them."
            )
        if identity_rows_broken:
            extra += (
                f" {identity_rows_broken} IDENTITY row(s) (a canonical token that must pass through "
                "unchanged) failed, which means the fold is rewriting values it should leave alone - "
                "that breaks artifacts ALREADY on disk, not only new ones."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.NORMALIZATIONS)} vocabulary normalizations are wrong.{extra} "
            "One fold-then-validate implementation with a per-vocabulary alias map decides every row, "
            "so read the VOCABULARY column: failures spread across kind/model/status/kebab mean the "
            "shared machinery broke, while failures confined to one vocabulary mean that alias map "
            "lost an entry. FIX: these values become FILENAME FACETS, so a wrong fold does not just "
            "mislabel - `finding` instead of `findings` hides the file from every consumer globbing "
            "the canonical facet, and folding a new model onto an old one records provenance that is "
            "false.\n" + "\n".join(wrong),
        )


class NameGrammarTests(unittest.TestCase):
    """The filename grammar in both directions: what `format_name` emits and what `parse_name` admits.

    ONE table replaces seven tests (`NameParseFormatTests` entire). Three were round trips, one was a
    drift-normalizing parse, and three were refusals; all seven handed one name to one pair of pure
    functions and asserted the outcome, so the accept/reject SENSE and the round-trip direction are
    columns.

    ACCEPT AND REJECT ROWS ARE IN ONE TABLE BY NECESSITY HERE, more than anywhere else in this file.
    `parse_name` is the reader half of a machine-readable contract: a parser that accepted everything
    would satisfy all four accept rows and would let a malformed artifact into the tree, and one that
    accepted nothing would satisfy all three reject rows while breaking every real file. Neither can
    pass this table.

    THE EXPECTED NAMES AND THE REFUSAL TEXT ARE LITERAL STRINGS. The grammar
    `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.<model>.<kind>.md` is read verbatim by other tooling and its
    spelling appears in the refusal messages, so rebuilding either from the module's own regexes would
    make a respelling invisible. Do not 'tidy' these into references to `R._CORE_RE` or `R.KINDS`.

    TWO ROWS PIN MORE THAN THE TESTS THEY REPLACE. The reconciliation row now asserts the exact
    emitted filename where the old test only checked that format-then-parse round-tripped (which a
    pair of mutually consistent but wrong functions passes), and each reject row now pins a substring
    of the message so the three refusals are shown to be three DIFFERENT diagnoses rather than one
    catch-all.
    """

    #: (case, filename, the EXACT ResearchName it must parse to (None on a reject), whether
    #: `format_name` of that record must reproduce this filename byte-for-byte, a substring the error
    #: must contain (None when it must parse), why this row exists)
    NAMES = (
        (
            "a full name carrying a model facet",
            "20260726-aw-delivery-02-k7m2xq-delivery-notes.gpt56.research-report.md",
            R.ResearchName(
                date="20260726",
                set_id="aw-delivery",
                order="02",
                id6="k7m2xq",
                slug="delivery-notes",
                model="gpt56",
                kind="research-report",
            ),
            True,
            None,
            "THE CANONICAL SHAPE, and the row that makes the refusals below meaningful: writer and "
            "reader must agree on it byte-for-byte, since `aw research new` emits the name and other "
            "tooling parses it back. Both directions are asserted, so a pair of functions that were "
            "consistent with each other but wrong about the grammar cannot pass",
        ),
        (
            "a singleton with NO model facet",
            "20260716-opencode-advisory-00-ab12cd-unauthenticated-server.advisory.md",
            R.ResearchName(
                date="20260716",
                set_id="opencode-advisory",
                order="00",
                id6="ab12cd",
                slug="unauthenticated-server",
                model=None,
                kind="advisory",
            ),
            True,
            None,
            "THE MODEL FACET IS OPTIONAL and Order `00` is legal, so the parser must not read the "
            "single remaining facet as a model. This is the row where an over-eager splitter fails: "
            "it would parse `advisory` as the MODEL and leave no kind at all",
        ),
        (
            "a reconciliation report, whose model facet is not a model",
            "20260726-host-probe-05-9z8y7x-synthesis.reconciliation.reconciliation-report.md",
            R.ResearchName(
                date="20260726",
                set_id="host-probe",
                order="05",
                id6="9z8y7x",
                slug="synthesis",
                model="reconciliation",
                kind="reconciliation-report",
            ),
            True,
            None,
            "`reconciliation` OCCUPIES THE MODEL SLOT to say no single model wrote this: the artifact "
            "reconciles several. The near-identical model and kind facets are also the case most "
            "likely to be collapsed by a deduplicating implementation. The old test asserted only "
            "that format-then-parse round-tripped; the literal name is pinned here instead",
        ),
        (
            "drifted model and kind facets, normalized on the way in",
            "20260722-token-eff-01-aa11bb-managed-sections.gpt-56.finding.md",
            R.ResearchName(
                date="20260722",
                set_id="token-eff",
                order="01",
                id6="aa11bb",
                slug="managed-sections",
                model="gpt56",
                kind="findings",
            ),
            False,
            None,
            "THE READER IS LENIENT WHERE THE WRITER IS STRICT: a file already on disk with drifted "
            "facets must still be readable, and must yield CANONICAL values so consumers index it "
            "correctly. `format_name` deliberately does NOT reproduce this input (it emits the "
            "canonical `.gpt56.findings.md`), which is why the round-trip column is False - and that "
            "asymmetry is itself the normalization claim",
        ),
        (
            "a name with no kind facet at all",
            "20260726-set-01-k7m2xq-slug.md",
            None,
            False,
            "'.<kind>' suffix",
            "THE KIND IS MANDATORY: it is what tells a consumer whether the file is a prompt, a "
            "report or an advisory, and no default is safe to assume. The needle pins the refusal as "
            "naming the MISSING FACET, since a generic 'bad name' message leaves the author guessing "
            "which of five fields is wrong",
        ),
        (
            "a kind facet on a core that fits no grammar",
            "not-a-valid-core.research-report.md",
            None,
            False,
            "core must be 'YYYYMMDD-<set-id>-<NN>-<id6>-<slug>'",
            "THE GRAMMAR IS QUOTED VERBATIM IN THE REFUSAL, and this row pins that spelling because "
            "humans fix names from this message and the same token appears in the docs. A correct "
            "kind facet must not buy acceptance for a malformed core, which is the failure mode of a "
            "parser that validates the facets it recognizes and shrugs at the rest",
        ),
        (
            "a correct name with a .txt extension",
            "20260726-set-01-k7m2xq-slug.research-report.txt",
            None,
            False,
            "must end in '.md'",
            "MARKDOWN IS PART OF THE CONTRACT, not a convention: every consumer reads these as "
            "markdown with front matter. This row also guards the reverse mistake of treating `txt` "
            "as the KIND facet, which would produce an unknown-kind error instead of the honest one",
        ),
    )

    def test_the_name_grammar_accepts_exactly_the_conforming_forms(self):
        wrong = []
        reject_rows_broken = 0
        accept_rows_broken = 0
        for case, filename, expected, round_trips, needle, why in self.NAMES:
            parsed, err = R.parse_name(filename)
            problems = []
            if expected is None:
                if err is None or parsed is not None:
                    reject_rows_broken += 1
                    problems.append(
                        f"must be REFUSED; parse_name returned {parsed!r} with err={err!r}"
                    )
                elif needle is not None and needle not in str(
                    getattr(err, "message", err)
                ):
                    problems.append(
                        f"the refusal must say {needle!r} (authors fix names from this text); got "
                        f"{getattr(err, 'message', err)!r}"
                    )
            else:
                if err is not None or parsed != expected:
                    accept_rows_broken += 1
                    problems.append(
                        f"must parse to {expected!r}; got {parsed!r} with err={err!r}"
                    )
                if round_trips:
                    emitted = R.format_name(expected)
                    if emitted != filename:
                        problems.append(
                            f"format_name must emit this name byte-for-byte; emitted {emitted!r}"
                        )
            if problems:
                wrong.append(
                    f"  {case} ({filename!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if reject_rows_broken and not accept_rows_broken:
            extra = (
                f" ALL {reject_rows_broken} failing row(s) are REJECT rows, so the parser has WIDENED "
                "and the accept rows above now prove nothing: a parser that accepts everything passes "
                "all of them while letting malformed artifacts into the tree."
            )
        elif accept_rows_broken and not reject_rows_broken:
            extra = (
                f" ALL {accept_rows_broken} failing row(s) are ACCEPT rows, so the grammar has "
                "NARROWED and files ALREADY on disk have become unreadable, which is the more urgent "
                "direction."
            )
        self.assertEqual(
            wrong,
            [],
            f"the name grammar mishandled {len(wrong)} of {len(self.NAMES)} names.{extra} One "
            "core-plus-facets splitter decides every row, so read the grouping: every row failing "
            "means the splitter itself changed, while the optional-model row alone means facet "
            "arity is being guessed rather than derived. FIX: the tokens in these names and in these "
            "refusal messages are read VERBATIM by other tooling and by humans, so a respelling is a "
            "breaking change - update the consumers and the docs, do not relax the expectation "
            "here.\n" + "\n".join(wrong),
        )


class ShardTests(unittest.TestCase):
    """Which shard directory names the reference/archive trees accept, and which form is canonical.

    ONE table replaces two tests (`test_shard_dirname`, `test_valid_shard`). Both asked about one
    directory-name string; one asserted the canonical form produced for a month and the other
    accepted or refused four shapes. The CANONICAL-FORM check is therefore a column on the row it
    applies to rather than a separate test.

    Why the table beats the two: `is_valid_shard_dirname` admits a CLOSED set of two shapes (the
    canonical `YYYYMM` and a grandfathered weekly `YYYYMM-Wnn`) and refuses hyphenated dates, and the
    realistic regression is a date-format change that reclassifies several shapes at once. The reject
    rows share the table because a predicate returning True for everything would satisfy both accept
    rows while letting a sharded tree grow directories nothing can enumerate.
    """

    #: (directory name, ACCEPT or REJECT, the value `shard_dirname` must produce for this name (None
    #: to skip that check), why this row exists)
    SHARDS = (
        (
            "202607",
            ACCEPT,
            "202607",
            "THE CANONICAL MONTHLY SHARD, and the only shape `shard_dirname` emits. The canonical-form "
            "column is checked here so the writer and the validator are pinned to agree: a writer "
            "emitting a form its own validator refuses would break sharding at the first archive",
        ),
        (
            "202607-W30",
            ACCEPT,
            None,
            "LEGACY WEEKLY TOLERANCE: real archived trees already contain weekly shards, so the "
            "validator must keep reading them even though nothing emits them any more. No canonical "
            "check, because `shard_dirname` must NOT produce this form",
        ),
        (
            "2026-07",
            REJECT,
            None,
            "A HYPHENATED DATE IS REFUSED. It sorts identically, which is exactly why it is dangerous: "
            "it would be accepted by a lenient validator and then split wrongly by any consumer that "
            "parses the directory name into a year and a month",
        ),
        (
            "2026-W30",
            REJECT,
            None,
            "the hyphenated twin of the legacy weekly form, so the tolerance above is shown to be "
            "NARROW: `YYYYMM-Wnn` is grandfathered, `YYYY-Wnn` is not. Without this row the weekly "
            "tolerance could be a loose 'contains a W' match",
        ),
    )

    def test_only_the_canonical_and_grandfathered_shard_shapes_are_valid(self):
        wrong = []
        reject_rows_broken = 0
        for name, sense, canonical, why in self.SHARDS:
            problems = []
            got = R.is_valid_shard_dirname(name)
            want = sense == ACCEPT
            if got is not want:
                problems.append(
                    f"expected is_valid_shard_dirname to return {want}, got {got!r}"
                )
                if not want:
                    reject_rows_broken += 1
            if canonical is not None:
                emitted = R.shard_dirname(name)
                if emitted != canonical:
                    problems.append(
                        f"shard_dirname must emit {canonical!r} for this month, got {emitted!r}; the "
                        "writer and the validator must agree or sharding breaks at the first archive"
                    )
            if problems:
                wrong.append(
                    f"  {name!r}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if reject_rows_broken:
            extra = (
                f" {reject_rows_broken} REJECT row(s) failed, so the accept rows are VACUOUS: a "
                "predicate returning True for everything satisfies them both."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SHARDS)} shard directory names were judged wrongly.{extra} "
            "Two shapes are admitted (canonical `YYYYMM`, grandfathered `YYYYMM-Wnn`) and the two "
            "hyphenated forms are refused, so read the grouping: both hyphenated rows failing "
            "together means the date pattern was loosened, while `202607-W30` failing alone means the "
            "legacy tolerance was dropped and an existing archive just became unreadable. FIX: shard "
            "names are DIRECTORY names in a tree that is enumerated by pattern, so an accepted "
            "non-conforming shard hides every artifact inside it.\n" + "\n".join(wrong),
        )


class FrontmatterTests(unittest.TestCase):
    """Which front-matter documents `validate_frontmatter` passes, and which field each error names.

    ONE table replaces seven tests (`FrontmatterTests` as it was, plus the validation half of
    `test_legacy_intake_normalizes_to_todo`). Every one took the same valid document, broke exactly
    one field, and asserted an error naming that field, so the mutation is a column.

    Why the table beats the seven: one validator walks a single field schema, so the realistic
    regression is the walk itself (every row fails) or one field's rule (one row fails), and that
    distinction is the first thing a reader needs. Seven tests report either case as unrelated red
    lines.

    THE CLEAN ROWS ARE IN THE SAME TABLE and carry real weight: a validator that reported an error for
    everything satisfies all five break rows on its own. There are two clean rows, the untouched
    document and the one whose `status` is the legacy `intake` spelling, and the failure message says
    the break rows are vacuous while either is broken.

    ROWS ASSERT THE EXACT SET OF FIELDS FLAGGED, not merely that some error mentions the field. An
    error set that grew a spurious second entry would be invisible to an `any(...)` assertion, and a
    validator that flagged EVERY field would satisfy every one of the old tests.
    """

    #: The conforming document every row mutates. Built fresh per row, so a row cannot leak into the
    #: next one through a shared dict.
    @staticmethod
    def _valid() -> dict:
        return {
            "id": "k7m2xq",
            "created": "20260726",
            "set": "aw-delivery",
            "order": "02",
            "topic": ["delivery", "hosts"],
            "model": "reconciliation",
            "kind": "reconciliation-report",
            "status": "reference",
            "outcome": "adopted",
            "summary": "One-line summary.",
            "consumed-by": ["D107"],
        }

    #: (case, the field to change (None to leave the document untouched), the value to set (the
    #: sentinel `DELETE` removes the field), the EXACT sorted list of field names that must be
    #: flagged, why this row exists)
    DELETE = object()

    FRONTMATTER = (
        (
            "the conforming document, untouched",
            None,
            None,
            [],
            "THE POSITIVE ROW: every break row below is vacuous while this one is broken, because a "
            "validator that rejected every document would satisfy all of them. It is also the only "
            "row that states the full required field set is SATISFIABLE",
        ),
        (
            "a legacy `intake` status on an otherwise conforming document",
            "status",
            "intake",
            [],
            "THE SECOND POSITIVE ROW, and a compatibility contract: `intake` is the pre-rename "
            "spelling of `todo` (rstodo `p3o9je`) and real artifacts on disk carry it, so the "
            "validator must normalize rather than refuse. A rename that only updated the canonical "
            "set would invalidate history that is already written",
        ),
        (
            "the required `id` field removed",
            "id",
            DELETE,
            ["id"],
            "THE IDENTITY FIELD IS REQUIRED. An artifact with no id cannot be cited, indexed, or "
            "regrouped, so its absence must be an error rather than something a consumer guesses "
            "from the filename",
        ),
        (
            "an out-of-vocabulary `status`",
            "status",
            "cold",
            ["status"],
            "STATUS DRIVES PLACEMENT: hot statuses live in the live tree and sharded ones under a "
            "month shard, so an unknown value has no home directory at all. The vocabulary is closed "
            "and `cold` is the plausible invention a human reaches for",
        ),
        (
            "a malformed `id` VALUE rather than a missing field",
            "id",
            "TOOLONGX",
            ["id"],
            "PRESENCE IS NOT ENOUGH, the value must satisfy the id6 grammar. This row pairs with the "
            "removal row above to show the field is checked TWICE, which a validator implemented as a "
            "required-keys sweep alone would fail",
        ),
        (
            "an out-of-vocabulary `outcome`",
            "outcome",
            "maybe",
            ["outcome"],
            "THE SECOND CLOSED VOCABULARY in this schema, so the enum check is shown to be general "
            "rather than a `status` special case. `maybe` is refused precisely because the outcome "
            "records what was DONE with the research; `none-yet` is how you say not yet",
        ),
        (
            "`topic` given as a string instead of a list",
            "topic",
            "delivery",
            ["topic"],
            "THE TYPE IS PART OF THE SCHEMA. A bare string is iterable, so a validator that only "
            "checked membership would accept it and every consumer would then index the artifact "
            "under eight single-character topics",
        ),
    )

    def test_each_field_rule_flags_exactly_its_own_field(self):
        wrong = []
        clean_rows_broken = 0
        for case, field, value, expected, why in self.FRONTMATTER:
            data = self._valid()
            if field is not None:
                if value is self.DELETE:
                    del data[field]
                else:
                    data[field] = value
            errs = R.validate_frontmatter(data)
            got = sorted(e.field for e in errs)
            if got != sorted(expected):
                if not expected:
                    clean_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected exactly these fields flagged: {sorted(expected)!r}\n"
                    f"    - got: {got!r} ({[e.message for e in errs]!r})\n"
                    f"    this row exists because: {why}"
                )
        extra = ""
        if clean_rows_broken:
            extra = (
                f" {clean_rows_broken} CLEAN row(s) are among the failures, and while either is "
                "broken every break row here is VACUOUS: a validator that rejects every document "
                "satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"`validate_frontmatter` judged {len(wrong)} of {len(self.FRONTMATTER)} documents "
            f"wrongly.{extra} One schema walk decides every row, so read the grouping: EVERY row "
            "failing means the walk broke (or the required-field list changed), while one row failing "
            "means that field's rule did. The two `id` rows failing together but no others means "
            "presence and VALUE are no longer checked separately. FIX: rows assert the EXACT set of "
            "flagged fields, so a failure listing MORE fields than expected is a validator that "
            "became noisy - which is as unusable as one that went quiet, since an author cannot tell "
            "which complaint to act on.\n" + "\n".join(wrong),
        )


class SchemaConstantsTests(unittest.TestCase):
    """The closed vocabularies and the field order, pinned as whole values.

    ONE table replaces three tests (`test_statuses`, `test_hot_vs_sharded`,
    `test_frontmatter_field_order`). Each compared one module constant against a literal, so the
    constant under test is a column.

    Why the table beats the three: these sets are one interlocking design - `HOT_STATUSES` and
    `SHARDED_STATUSES` must PARTITION `STATUSES`, since a status in neither has no home directory and
    one in both has two. Stated as three tests that relationship is invisible and can be broken by
    editing one constant; here the partition is asserted after the rows, on the actual values, so
    adding a status without deciding where it lives fails.

    EXPECTED VALUES ARE LITERAL. Deriving them from the module would make any edit self-consistent
    and this test unable to fail, which is the standard failure of a constants test.
    """

    #: (the constant's name, its actual value, the EXACT expected value, why this row exists)
    CONSTANTS = (
        (
            "STATUSES",
            R.STATUSES,
            frozenset({"todo", "active", "reference", "archive"}),
            "THE LIFECYCLE IS FOUR STATES and the set is closed, because `validate_frontmatter` "
            "refuses anything outside it and every tree layout decision keys on it. `intake` is "
            "deliberately ABSENT: it is accepted via normalization, not as a canonical member "
            "(rstodo `p3o9je`), so a fifth member appearing here means the rename regressed",
        ),
        (
            "HOT_STATUSES",
            R.HOT_STATUSES,
            frozenset({"todo", "active"}),
            "HOT MEANS UNSHARDED: these artifacts live directly in the live tree because they are "
            "being worked on. Widening this set silently un-shards an archive; narrowing it buries "
            "active work under a month directory",
        ),
        (
            "SHARDED_STATUSES",
            R.SHARDED_STATUSES,
            frozenset({"reference", "archive"}),
            "the complement, and the reason both sets are pinned together rather than separately: "
            "they must PARTITION `STATUSES`, which is asserted below on the real values. A status in "
            "neither set has no home directory, and one in both has two",
        ),
        (
            "FRONTMATTER_FIELDS[0]",
            R.FRONTMATTER_FIELDS[0],
            "id",
            "FIELD ORDER IS PART OF THE WRITTEN ARTIFACT (it is the order emitted into front matter), "
            "and `id` leads because it is the identity a reader needs first. Pinning the ends rather "
            "than the whole tuple keeps adding a middle field cheap while making a REORDER fail",
        ),
        (
            "FRONTMATTER_FIELDS[-1]",
            R.FRONTMATTER_FIELDS[-1],
            "consumed-by",
            "the other end: `consumed-by` is last because it is the field most often appended later, "
            "when a decision finally cites the research. Together these two rows pin the order's "
            "endpoints without freezing its interior",
        ),
    )

    def test_the_closed_vocabularies_and_field_order_are_what_the_contract_says(self):
        wrong = []
        for name, actual, expected, why in self.CONSTANTS:
            if actual != expected:
                wrong.append(
                    f"  {name}:\n"
                    f"    - expected {expected!r}\n"
                    f"    - got      {actual!r}\n"
                    f"    this row exists because: {why}"
                )
        # THE PARTITION PROPERTY, asserted on the ACTUAL values rather than on the literals above, so
        # that adding a status without deciding where it lives fails here even if every row is edited
        # to match.
        if R.HOT_STATUSES | R.SHARDED_STATUSES != R.STATUSES:
            wrong.append(
                "  the hot/sharded partition:\n"
                f"    - HOT_STATUSES | SHARDED_STATUSES is {set(R.HOT_STATUSES | R.SHARDED_STATUSES)!r}, "
                f"which is not STATUSES {set(R.STATUSES)!r}\n"
                "    this row exists because: a status in NEITHER set has no home directory, so an "
                "artifact carrying it cannot be filed at all"
            )
        if R.HOT_STATUSES & R.SHARDED_STATUSES:
            wrong.append(
                "  the hot/sharded partition:\n"
                f"    - these statuses are in BOTH sets: {set(R.HOT_STATUSES & R.SHARDED_STATUSES)!r}\n"
                "    this row exists because: a status in both has two candidate homes, so two runs "
                "would file the same artifact in different places"
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.CONSTANTS)} pinned contract constants (plus the partition "
            "property) are wrong. These sets are ONE interlocking design rather than three "
            "independent values, so read the grouping: a status set and the partition failing "
            "together means a state was added without deciding whether it shards, while a "
            "`FRONTMATTER_FIELDS` row alone means the emitted field order moved. FIX: expected values "
            "here are LITERAL on purpose - deriving them from the module would make any edit "
            "self-consistent and this test unable to fail. If a change is intended, update the "
            "literal AND the consumers that read these names.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()
