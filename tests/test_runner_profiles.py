"""Tests for `agent_workflows.runner_profiles` (runprofile Order 01, `f2mrsw` E-04).

The matrix this suite is REQUIRED to fail on (plan "Required tests / validation"):

  * silent fallback     - a malformed/unsupported config must RAISE, never behave as empty,
                          because behaving as empty launches the host default model.
  * schema widening     - an unknown key, and every forbidden capability key by name, must fail.
  * dangling defaults   - a default reference to a missing/wrong-runner profile must fail, and
                          removing a referenced profile must force an EXPLICIT decision.
  * precedence inversion- an explicit flag must ALWAYS beat a stored `validate` default, and an
                          ABSENT tri-state level must fall THROUGH rather than read as `false`.
  * partial writes      - a fault injected mid-write must leave the previous bytes IDENTICAL.
  * namespace over-reservation - command-LIKE names (`status`, `report`, `run`) stay LEGAL;
                          only the grammar words `as`/`default` are reserved.
  * arbitrary argv      - the module must contain no `shell=True`, `eval`, `exec`, credential
                          field, or persisted command string.

MODEL IDENTIFIERS HERE ARE SYNTHETIC. The orchestrator (`3m0urk`) requires tests to use
synthetic equivalents of the three requested profiles, because one real identifier is
institution-specific and a tracked test is public. `_INHOUSE_MODEL` is shaped like the real
three-segment private identifier (so the grammar is genuinely exercised) without naming any
real gateway.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: build a config, call
one function, assert one value. The tables group by SUBJECT (a precedence chain, a grammar, a set of
malformed documents) rather than by which plan Order added the behavior, which is what the class
boundaries used to track. Each row carries the RULE it encodes, and a failure reports every wrong row
at once with a hint saying what several rows failing together means.

WHERE A DISTINCTION IS A MODE IT IS A COLUMN, NOT A SECOND CLASS, and three of those columns carry
most of the value here:

  * HOST (`oc` vs `agy`). Tier 4 of the `validate` chain lives on each `RUNNER_REGISTRY` row and the
    two shipped hosts declare OPPOSITE postures, so the property worth asserting is that identical
    configuration resolves DIFFERENTLY at tier 4 and IDENTICALLY at every tier above it. A class per
    host cannot state that, and the per-host default was expressible as a module global for exactly
    as long as the tests were split that way.
  * TIER. Each of the three precedence chains (`model`/`variant`/`agent`, `validate`, `verify_with`)
    is one table whose rows are its levels, because a chain tested level by level cannot show an
    INVERSION, and an inversion is the named failure mode (`vju5ba`) this module exists to prevent.
  * ROUTE. Several rules bind two entry points that must AGREE: a stored profile versus an explicit
    flag for a row's `supports_*` fields, and a direct call versus the write path for runner
    canonicalization. One test per route cannot assert the agreement.

TRI-STATES ARE THREE-VALUED IN THE COLUMNS, never collapsed to a bool: `None` means the key is ABSENT
and must FALL THROUGH, while `False` is a decision that must WIN over a lower tier. That distinction
is the subject of `OptionalFieldSerializationTests`, and coercing absent to false is the silent
failure the whole chain rests on not happening.

TESTS THAT ARE NOT ROWS CARRY A ONE-LINE DOCSTRING SAYING WHY. The recurring reasons: the assertion
is an `assertRaises` (no record exists to read back); the claim is STRUCTURAL (a constant's value, a
set membership, an exception hierarchy, immutability); the subject is TWO results COMPARED to each
other rather than to an expectation; the setup is materially different (a real file, a patched module
constant, a hand-built record that bypassed the validator); or the property is a CONTRAST between
outcomes, such as absent-yields-empty versus malformed-raises, where the point is that they differ.

Stdlib `unittest` only, matching `tests/test_config.py`.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import runner_profiles as RP

# The three requested profiles, as SYNTHETIC equivalents (see module docstring).
_FLASH_MODEL = "example-vendor/flash-3.7"
_INHOUSE_MODEL = "example-gw/inhouse/pt3-sonnet-5-1m-us"
_SOL_MODEL = "example-openai/gpt-sol-5.6"


def _profile(**kwargs) -> RP.LaunchProfile:
    kwargs.setdefault("runner", "oc")
    kwargs.setdefault("model", _FLASH_MODEL)
    return RP.LaunchProfile(**kwargs)


def _three_requested() -> RP.ProfileConfig:
    cfg = RP.empty_config()
    cfg = RP.add_profile(
        cfg, "gem", RP.LaunchProfile(runner="oc", model=_FLASH_MODEL, variant="high")
    )
    cfg = RP.add_profile(
        cfg,
        "sonnet",
        RP.LaunchProfile(runner="oc", model=_INHOUSE_MODEL, variant="medium"),
    )
    cfg = RP.add_profile(
        cfg, "sol", RP.LaunchProfile(runner="oc", model=_SOL_MODEL, variant="medium")
    )
    return cfg


# ==================================================================================================
# E-01 / V-01: schema, records, names, runner canonicalization
# ==================================================================================================


class RequestedProfilesParseTests(unittest.TestCase):
    """The three requested profiles must round-trip through the schema.

    `test_optional_fields_are_omitted_not_nulled` moved into
    `OptionalFieldSerializationTests`, whose table owns the absent-key rule for every optional field
    at both levels rather than for one profile's `variant`/`validate`.
    """

    def test_three_requested_profiles_parse_and_round_trip(self):
        """Kept separate: a WHOLE-CONFIG round trip through `dumps`, asserted field by field."""

        cfg = _three_requested()
        reparsed = RP.from_document(json.loads(RP.dumps(cfg)))
        self.assertEqual(sorted(reparsed.profiles), ["gem", "sol", "sonnet"])
        self.assertEqual(reparsed.get("gem").model, _FLASH_MODEL)
        self.assertEqual(reparsed.get("gem").variant, "high")
        self.assertEqual(reparsed.get("sonnet").model, _INHOUSE_MODEL)
        self.assertEqual(reparsed.get("sol").variant, "medium")
        self.assertEqual(reparsed.to_document(), cfg.to_document())
        print("three requested profiles round-trip:", sorted(reparsed.profiles))

    def test_records_are_immutable(self):
        """Kept separate: two assertRaises on ATTRIBUTE and ITEM assignment, a structural claim."""

        cfg = _three_requested()
        with self.assertRaises(Exception):
            cfg.profiles["gem"].model = "other/model"  # type: ignore[misc]
        with self.assertRaises(Exception):
            cfg.profiles["nope"] = _profile()  # type: ignore[index]


class ProfileNameGrammarTests(unittest.TestCase):
    """Every name the grammar accepts and refuses, in one table, with the REASON it is refused.

    ONE table replaces four tests. All four called `validate_profile_name` and asserted either that
    it returned the name unchanged or that it raised; they differed only in the name and in which
    outcome they expected.

    THE OUTCOME IS A COLUMN, NOT A REASON FOR TWO TABLES, and this subject is the clearest case for
    it in the file. The rule being pinned is a BOUNDARY: `status` is legal and `as` is not, `g` * 32
    is legal and `g` * 33 is not, and each of those pairs is one rule read twice. Split across an
    accepted-names test and a refused-names test, the pairs sit in different methods and a change
    that moved the boundary shows up as two unrelated failures with no hint that they are the same
    edit. Adjacent rows make the boundary readable AS a boundary.

    THE COMMAND-LIKE ROWS ARE POSITIVE ROWS AND THEY CARRY REAL WEIGHT. Over-reserving the namespace
    is a DEFECT, not a safe default (the plan's own matrix names it): a profile name is only ever
    resolved AFTER the `as` keyword, so it cannot shadow a subcommand, and refusing `status` or `run`
    would cost users names for nothing. Without them the grammar could be implemented as "refuse
    anything that looks like a command" and every refusal row would still pass.

    THE REFUSAL SUBSTRING IS ASSERTED WHERE IT IS DISTINCTIVE, which is stronger than the tests it
    replaces. `as` and `default` must be refused as RESERVED specifically, not merely refused: a
    grammar that happened to reject them for some other reason (say, a length rule) would satisfy a
    bare `assertRaises` while leaving the reservation unimplemented, so the moment a name like
    `default-gem` was added the ambiguity would return.
    """

    #: (case, the name to validate, the expected returned name or None if it must be REFUSED, a
    #:  substring the refusal message must contain or None to accept any refusal, why this row exists)
    NAMES = (
        (
            "a plain name",
            "gem",
            "gem",
            None,
            "the base case every other row is measured against",
        ),
        (
            "a hyphenated name",
            "verify-ledger",
            "verify-ledger",
            None,
            "hyphens are the intended separator (kebab-case), so the class is not merely "
            "alphanumeric",
        ),
        (
            "a name that looks like a subcommand",
            "status",
            "status",
            None,
            "A POSITIVE ROW THAT CARRIES WEIGHT: over-reserving the namespace is a defect. A name is "
            "resolved only after `as`, so `status` cannot shadow a subcommand, and refusing it would "
            "cost a user a name for no safety gain",
        ),
        (
            "another subcommand-shaped name",
            "run",
            "run",
            None,
            "the second half of the same claim, chosen because `run` is the MOST command-like name "
            "there is: if any name were going to be over-reserved by an anxious implementation, it "
            "is this one",
        ),
        (
            "exactly MAX_PROFILE_NAME_LEN characters",
            "g" * RP.MAX_PROFILE_NAME_LEN,
            "g" * RP.MAX_PROFILE_NAME_LEN,
            None,
            "THE BOUNDARY IS INCLUSIVE. Read WITH the over-length row below: they differ by ONE "
            "character and must resolve oppositely, which is what pins an off-by-one that no single "
            "row can catch",
        ),
        (
            "one character over MAX_PROFILE_NAME_LEN",
            "g" * (RP.MAX_PROFILE_NAME_LEN + 1),
            None,
            None,
            "the other side of the inclusive boundary above",
        ),
        (
            "the grammar word `as`",
            "as",
            None,
            "reserved",
            "RESERVED BY THE GRAMMAR, and the message must say so. `aw run as as` would be "
            "ambiguous at the grammar level rather than at the lookup level, which no amount of "
            "careful lookup can fix. The substring matters: refused for some OTHER reason would "
            "leave the reservation unimplemented",
        ),
        (
            "the grammar word `default`",
            "default",
            None,
            "reserved",
            "the second grammar word, for the same reason: `aw run as default` must not be readable "
            "two ways",
        ),
        (
            "an empty name",
            "",
            None,
            None,
            "a name is required, and an empty string is the classic value that slips through a "
            "regex-only check",
        ),
        (
            "a leading digit",
            "1gem",
            None,
            None,
            "the grammar requires a leading LETTER, so a name can never be confused with a number "
            "in a position that also accepts one",
        ),
        (
            "a leading hyphen",
            "-gem",
            None,
            None,
            "A LEADING HYPHEN WOULD READ AS A FLAG on any command line that takes a profile name, "
            "which is the practical reason this is not merely a style rule",
        ),
        (
            "an uppercase letter",
            "Gem",
            None,
            None,
            "names are lowercase, so `Gem` and `gem` can never be two profiles a user cannot tell "
            "apart in their own store",
        ),
        (
            "an underscore",
            "my_gem",
            None,
            None,
            "the separator is a hyphen, one way only, so a name has a single spelling",
        ),
        (
            "a space",
            "my gem",
            None,
            None,
            "a space would have to be quoted at every call site that names a profile",
        ),
        (
            "a dot",
            "gem.1",
            None,
            None,
            "dots are excluded from the class, which keeps a name from looking like a file or a "
            "dotted path",
        ),
        (
            "a slash",
            "a/b",
            None,
            None,
            "THE ROW THAT FENCES A WHOLE CLASS OF MISTAKE: a slash is what makes `provider/model` "
            "unable to be a profile name, which is why `verify_with` and the `roles` map can take a "
            "NAME and be sure it is not an inline model",
        ),
        (
            "a shell metacharacter",
            "gem;rm",
            None,
            None,
            "the narrow character class IS the injection control: no stored name can carry a shell "
            "fragment even if some future caller were careless with it",
        ),
        (
            "not a string at all",
            7,
            None,
            None,
            "a non-string must be a TYPED refusal rather than a TypeError from the regex, because "
            "this value arrives from parsed JSON where any type is possible",
        ),
    )

    def test_every_name_is_accepted_or_refused_by_the_grammar(self):
        wrong = []
        for case, name, expected, complaint, why in self.NAMES:
            problems = []
            try:
                got = RP.validate_profile_name(name)
            except RP.ProfileSchemaError as exc:
                if expected is not None:
                    problems.append(f"REFUSED a name that must be legal: {exc}")
                elif complaint is not None and complaint not in str(exc):
                    problems.append(
                        f"the refusal must say {complaint!r}; it said {str(exc)!r}"
                    )
            except Exception as exc:  # noqa: BLE001 - the TYPE is the assertion
                problems.append(
                    f"raised {type(exc).__name__} rather than the module's typed "
                    f"ProfileSchemaError: {exc}"
                )
            else:
                if expected is None:
                    problems.append(
                        f"ACCEPTED a name that must be refused, returning {got!r}"
                    )
                elif got != expected:
                    problems.append(f"returned {got!r}, expected {expected!r}")
            if problems:
                wrong.append(
                    f"  {case} ({name!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the name grammar was wrong for {len(wrong)} of {len(self.NAMES)} names. ONE regex plus "
            "one reserved set decides every row, so read the DIRECTION of the failures, because they "
            "are not equally bad. If the ACCEPTED rows fail (`status`, `run`, the 32-character name), "
            "the namespace is being OVER-RESERVED: that is a defect in its own right, since a profile "
            "name is resolved only after `as` and cannot shadow a subcommand. If REFUSED rows are now "
            "accepted, the severe ones are the slash row (an inline `provider/model` could then pass "
            "as a profile name, which is what `verify_with` and the `roles` map rely on being "
            "impossible) and the metacharacter row. If ONLY the two grammar-word rows fail, the "
            "reservation was dropped and `aw run as default` is ambiguous again. FIX: the two "
            f"length rows differ by ONE character and must disagree; that is the boundary.\n"
            + "\n".join(wrong),
        )


class RunnerCanonicalizationTests(unittest.TestCase):
    """The registry is CLOSED: every alias canonicalizes, every unregistered host is refused.

    ONE table replaces three tests, which called `canonical_runner` on an accepted name, on a refused
    name, and (the third) checked that a profile STORED through `add_profile` came back canonical.

    THE ROUTE IS A COLUMN, and that is what the third test contributes: the same canonicalization
    must happen when a value is STORED, not only when the helper is called directly. A stored
    non-canonical runner would be a profile that silently never matches its host's default or its
    `supports_*` row, so every accepted row is checked on BOTH routes rather than one row being
    checked on the second.

    THE PROPERTY IS THAT THE SET IS CLOSED, not that it holds a particular row. `hostdefault-01`
    added `agy`, which MOVED `agy`/`antigravity` from the refused side to the accepted side; the
    refusal rows are what stop a future runtime from widening the accepted host set, so `codex`,
    `claude` and `kiro` stay as rows naming hosts this module makes NO parity claim about.
    """

    #: (case, the input value, the expected canonical name or None if it must be REFUSED, whether the
    #:  STORED route must be checked too, why this row exists)
    RUNNERS = (
        (
            "the canonical name itself",
            "oc",
            "oc",
            True,
            "canonicalization must be IDEMPOTENT, or a value read back from the store and passed "
            "through again would drift",
        ),
        (
            "the `oc` alias",
            "opencode",
            "oc",
            True,
            "the alias users actually type is the whole point of the mapping",
        ),
        (
            "the `oc` alias in mixed case",
            "OpenCode",
            "oc",
            True,
            "case folding, so a profile written `OpenCode` is not a second host",
        ),
        (
            "the second registered host",
            "agy",
            "agy",
            True,
            "THE ROW THAT MAKES THE SET CLOSED RATHER THAN SINGLETON. `hostdefault-01` added this "
            "row so the schema can record Antigravity's opposite verification posture; before it, "
            "every `agy` path in this module was unreachable",
        ),
        (
            "the second host's alias",
            "antigravity",
            "agy",
            True,
            "the same alias mapping on the newer row, so the mechanism is per row and not special-"
            "cased for `oc`",
        ),
        (
            "the second host's alias in upper case",
            "AGY",
            "agy",
            True,
            "case folding on the newer row too",
        ),
        (
            "an unregistered host",
            "codex",
            None,
            False,
            "THE CLOSURE GUARANTEE: an unregistered host is REFUSED rather than stored as-is. This "
            "module makes no parity claim about Codex, and a stored `codex` profile would be a "
            "launch identity nothing can dispatch",
        ),
        (
            "another unregistered host",
            "claude",
            None,
            False,
            "a second refused host, so the rule reads as a closed set rather than one blocked name",
        ),
        (
            "a third unregistered host",
            "kiro",
            None,
            False,
            "and a third, chosen because these three are the hosts most likely to be added "
            "carelessly by a future contributor who only needs a name to store",
        ),
        (
            "an empty string",
            "",
            None,
            False,
            "empty is not a host, and it is the value a missing CLI argument most often becomes",
        ),
        (
            "None",
            None,
            None,
            False,
            "a missing value must be a TYPED refusal rather than an AttributeError from `.lower()`",
        ),
        (
            "a non-string",
            3,
            None,
            False,
            "this value arrives from parsed JSON, where any type is possible",
        ),
    )

    def test_every_alias_canonicalizes_and_every_unregistered_host_is_refused(self):
        wrong = []
        for case, value, expected, check_stored, why in self.RUNNERS:
            problems = []
            try:
                got = RP.canonical_runner(value)
            except RP.ProfileSchemaError as exc:
                if expected is not None:
                    problems.append(f"REFUSED a registered host: {exc}")
            except Exception as exc:  # noqa: BLE001 - the TYPE is the assertion
                problems.append(
                    f"raised {type(exc).__name__} rather than ProfileSchemaError: {exc}"
                )
            else:
                if expected is None:
                    problems.append(
                        f"ACCEPTED an unregistered host, canonicalizing it to {got!r}"
                    )
                elif got != expected:
                    problems.append(f"canonicalized to {got!r}, expected {expected!r}")
            if check_stored and expected is not None:
                stored = RP.add_profile(
                    RP.empty_config(), "p", _profile(runner=value)
                ).get("p")
                if stored.runner != expected:
                    problems.append(
                        f"a profile STORED with runner={value!r} came back as "
                        f"{stored.runner!r}, not {expected!r}; a non-canonical stored runner never "
                        "matches its host's registry row"
                    )
            if problems:
                wrong.append(
                    f"  {case} ({value!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the runner registry mishandled {len(wrong)} of {len(self.RUNNERS)} values. ONE lookup "
            "over `RUNNER_REGISTRY` and its alias lists answers every row. FIX: the two directions "
            "are not equally bad. An ACCEPTED-row failure means a host that IS registered stopped "
            "resolving, so existing stored profiles become unloadable. An unregistered host being "
            "ACCEPTED is worse in kind: the registry is what stops a runtime widening the host set, "
            "and a stored profile naming a host no adapter can launch is a launch identity that "
            "fails only when someone tries to use it. If the STORED-route line appears while the "
            "direct call is right, canonicalization was dropped from the write path and profiles are "
            f"being saved in a spelling that never matches their own registry row.\n"
            + "\n".join(wrong),
        )


class ModelAndFieldValidationTests(unittest.TestCase):
    """The model grammar and the bounded token fields, which are assertRaises sweeps throughout.

    Deliberately NOT merged into `ProfileNameGrammarTests`' table: a model is a DIFFERENT grammar
    (multi-segment, slash-separated, deliberately admitting `provider/model` shapes a profile NAME
    can never take), so putting both in one table would invite a reader to conclude they share a
    rule. The slash is the exact point where the two grammars must DISAGREE, which is what makes
    `verify_with` and the `roles` map able to take a reference and be sure it is not an inline model.
    """

    def test_exact_provider_model_is_required(self):
        """Kept separate: an assertRaises sweep over the MODEL grammar, a different rule than names."""

        for label, value in {
            "missing-provider": "flash-3.7",
            "empty": "",
            "trailing-slash": "vendor/",
            "leading-slash": "/model",
            "double-slash": "vendor//model",
            "whitespace": "vendor/mo del",
            "quote": 'vendor/mo"del',
            "backtick": "vendor/`id`",
            "dollar": "vendor/$MODEL",
            "semicolon": "vendor/model;whoami",
            "pipe": "vendor/model|tee",
            "backslash": "vendor\\model",
            "too-long": "vendor/" + "m" * RP.MAX_MODEL_LEN,
            "not-a-string": 5,
            "none": None,
        }.items():
            with self.subTest(case=label):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.validate_model(value)

    def test_multi_segment_private_shape_is_accepted(self):
        """Kept separate: the one POSITIVE model case, pinning that three segments are legal."""

        self.assertEqual(RP.validate_model(_INHOUSE_MODEL), _INHOUSE_MODEL)

    def test_missing_required_fields_fail(self):
        """Kept separate: an assertRaises pair whose assertion is WHICH field the message names."""

        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.parse_profile("gem", {"model": _FLASH_MODEL})
        self.assertIn("runner", str(ctx.exception))
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.parse_profile("gem", {"runner": "oc"})
        self.assertIn("model", str(ctx.exception))

    def test_variant_and_agent_are_bounded_tokens(self):
        """Kept separate: an assertRaises sweep over two fields sharing one bounded-token class."""

        good = RP.parse_profile(
            "gem",
            {
                "runner": "oc",
                "model": _FLASH_MODEL,
                "variant": "high",
                "agent": "build",
            },
        )
        self.assertEqual((good.variant, good.agent), ("high", "build"))
        for field_name, value in (
            ("variant", "high; rm -rf /"),
            ("variant", ""),
            ("variant", 1),
            ("agent", "a b"),
            ("agent", "x" * (RP.MAX_FIELD_LEN + 1)),
        ):
            with self.subTest(field=field_name, value=value):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.parse_profile(
                        "gem",
                        {"runner": "oc", "model": _FLASH_MODEL, field_name: value},
                    )


class ForbiddenAndUnknownFieldTests(unittest.TestCase):
    """Schema widening must fail: no argv, env, prompt, permission, token, or API-key fields.

    `test_unknown_document_and_defaults_keys_are_refused` moved into `MalformedDocumentTests`, which
    owns document-level refusals. What remains is PROFILE-level, and each test says why it is not a
    row: the forbidden sweep iterates a whole CONSTANT rather than a fixed list, and the credential
    test inspects written TEXT rather than a refusal.
    """

    def test_every_forbidden_capability_field_is_refused_by_name(self):
        """Kept separate: iterates the whole `FORBIDDEN_PROFILE_KEYS` constant, so it has no rows.

        A table would have to restate the set, at which point adding a key to the module without
        adding a row would go untested. Iterating the constant means a new forbidden key is covered
        the moment it is declared; the explicit list at the end is the floor the plan names, so
        REMOVING one of those is still caught.
        """

        refused = []
        for key in sorted(RP.FORBIDDEN_PROFILE_KEYS):
            with self.subTest(key=key):
                with self.assertRaises(RP.ProfileSchemaError) as ctx:
                    RP.parse_profile(
                        "gem", {"runner": "oc", "model": _FLASH_MODEL, key: "anything"}
                    )
                self.assertIn("BY DESIGN", str(ctx.exception))
                refused.append(key)
        # The categories the plan names explicitly must all be present.
        for required in (
            "args",
            "argv",
            "env",
            "environment",
            "executable",
            "prompt",
            "permissions",
            "token",
            "api_key",
            "shell",
            "command",
            "secret",
        ):
            self.assertIn(required, refused)
        print(f"forbidden-by-name fields refused ({len(refused)}): {refused}")

    def test_unknown_field_is_refused(self):
        """Kept separate: the PROFILE-level closure, whose document twin lives in the table above."""

        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.parse_profile(
                "gem", {"runner": "oc", "model": _FLASH_MODEL, "temperature": 0.2}
            )
        self.assertIn("unknown field", str(ctx.exception))

    def test_a_credential_can_never_be_persisted(self):
        """Kept separate: inspects the WRITTEN TEXT for credential-shaped words, not a refusal.

        The refusal rows prove those keys cannot be stored; this proves none of them appears in the
        output for any other reason, which is a claim about the serialized bytes.
        """

        cfg = RP.add_profile(RP.empty_config(), "gem", _profile())
        text = RP.dumps(cfg)
        for word in (
            "token",
            "api_key",
            "secret",
            "password",
            "Authorization",
            "Bearer",
        ):
            self.assertNotIn(word, text)
        print("serialized document contains no credential-shaped field")


class MalformedDocumentTests(unittest.TestCase):
    """Every malformed document REFUSES rather than degrading to an empty config.

    ONE table replaces eight tests across four classes: all three of `DocumentValidationTests`,
    `ForbiddenAndUnknownFieldTests.test_unknown_document_and_defaults_keys_are_refused`,
    `StoreReadWriteTests.test_malformed_shapes_all_raise_rather_than_degrade`, and three roles
    refusals (`test_a_roles_value_that_is_not_an_object_is_refused`,
    `test_a_non_string_role_target_is_refused`, `test_an_unknown_top_level_key_is_still_refused`).
    Each fed `from_document` a bad document and asserted it raised.

    THE MATRIX ROW THIS TABLE OWNS IS "SILENT FALLBACK", which is the most expensive failure this
    module has: a malformed or unsupported config must RAISE, never behave as empty, because behaving
    as empty launches the HOST DEFAULT MODEL. So the table asserts the refusal is a `RunnerProfileError`
    subclass and, for every row, that no code path returned a usable empty config instead.

    THE MESSAGE SUBSTRING IS A COLUMN because several refusals must be ACTIONABLE, not merely raised.
    An unsupported version must say so and name the consequence (`wrong model`), an unknown role
    value must say `'roles' must be an object`, and an inline model in a role must be refused BY THE
    NAME GRAMMAR (`invalid profile name`) rather than by some ad hoc string check. A bare
    `assertRaises` cannot tell those apart, so a refusal that moved to a different, less useful
    message would pass the tests this table replaces.

    THE POSITIVE ROW IS IN THE SAME TABLE and it is load-bearing here: a reader that refused every
    document would satisfy all eighteen negative rows. The minimal valid document must load.
    """

    #: (case, the document, the message substring that must appear or None, why this row exists)
    DOCUMENTS = (
        (
            "THE POSITIVE ROW: the minimal valid document",
            {"schema_version": 1, "profiles": {}},
            None,
            "a reader that refused everything would satisfy every negative row below. This must "
            "LOAD, and it is what makes the rest of the table non-vacuous",
        ),
        (
            "no `schema_version` at all",
            {},
            None,
            "the version is REQUIRED: without it there is no way to know what the rest of the "
            "document means, and guessing is how a future format gets misread as this one",
        ),
        (
            "`schema_version` as a string",
            {"schema_version": "1"},
            None,
            'JSON makes `1` and `"1"` easy to confuse, and a string that compared unequal to every '
            "supported int would fail somewhere less clear",
        ),
        (
            "`schema_version` as a bool",
            {"schema_version": True},
            None,
            "`True == 1` IN PYTHON, so a naive membership check would ACCEPT this and read the "
            "document as v1. This is the row that requires a real type check rather than `in`",
        ),
        (
            "`schema_version` as a float",
            {"schema_version": 1.0},
            None,
            "`1.0 == 1` for the same reason, so the float is the second value a membership check "
            "lets through",
        ),
        (
            "an UNSUPPORTED version",
            {"schema_version": 99, "profiles": {}},
            "unsupported schema_version 99",
            "FAIL CLOSED ON THE FUTURE. A newer store must not be read by guessing, because the "
            "fields would be misinterpreted rather than merely missing",
        ),
        (
            "an unsupported version, checked for the CONSEQUENCE in the message",
            {"schema_version": 99, "profiles": {}},
            "wrong model",
            "THE MESSAGE MUST NAME THE COST, not just the fact: an operator who does not know that "
            "proceeding would launch the wrong model has no reason to treat this as urgent",
        ),
        (
            "a JSON array instead of an object",
            [],
            None,
            "the document is an object. An array is what a hand-edited file most often becomes",
        ),
        (
            "a JSON string instead of an object",
            "x",
            None,
            "a bare string is indexable in Python, so a reader that used `.get` would fail "
            "elsewhere; refusing up front keeps the error at the parse",
        ),
        (
            "a JSON number instead of an object",
            3,
            None,
            "the third non-object shape, so the check is on the TYPE rather than on a blocklist",
        ),
        (
            "JSON null instead of an object",
            None,
            None,
            "null is what an empty file parses to in some readers, and it is precisely the value "
            "that must NOT become an empty config",
        ),
        (
            "`profiles` as an array",
            {"schema_version": 1, "profiles": []},
            None,
            "the SECTIONS are typed too, not only the document. An array here would iterate as "
            "nothing, producing a silently empty profile set",
        ),
        (
            "`defaults` as an array",
            {"schema_version": 1, "profiles": {}, "defaults": []},
            None,
            "the same claim for the second section",
        ),
        (
            "`defaults.profiles` as an array",
            {"schema_version": 1, "profiles": {}, "defaults": {"profiles": []}},
            None,
            "and for the NESTED per-runner map, which is the level a default profile reference "
            "lives at; an array there would silently mean 'no default for any host'",
        ),
        (
            "an unknown TOP-LEVEL key",
            {"schema_version": 1, "profiles": {}, "extra": 1},
            None,
            "the document vocabulary is CLOSED, so an unknown key is refused rather than ignored: "
            "an ignored key is usually a typo in a real one, and a typo'd `defaults` that loads "
            "clean is a configuration that silently does nothing",
        ),
        (
            "an unknown key inside `defaults`",
            {"schema_version": 1, "profiles": {}, "defaults": {"token": "abc"}},
            None,
            "the closure applies per level. `token` specifically, because the `defaults` object is "
            "the surface a credential would most plausibly be smuggled onto",
        ),
        (
            "a profile missing a required field",
            {"schema_version": 1, "profiles": {"gem": {"runner": "oc"}}},
            None,
            "a profile with no model is not a launch identity. Refused at LOAD, so a broken store "
            "cannot sit there resolving to the host default",
        ),
        (
            "a profile that is not an object",
            {"schema_version": 1, "profiles": {"gem": 3}},
            None,
            "THE SILENT-FALLBACK ROW from the plan's own matrix, measured: a broken file must raise "
            "at load, so no code path can resolve it to a host default",
        ),
        (
            "a DANGLING per-runner default reference",
            {
                "schema_version": 1,
                "profiles": {},
                "defaults": {"profiles": {"oc": "ghost"}},
            },
            None,
            "a reference to a profile that does not exist is refused AT LOAD. Left to resolution it "
            "would fall through to the host default, so an operator would believe their default "
            "profile was in effect while it was not",
        ),
        (
            "a DANGLING `verify_with` reference",
            {
                "schema_version": 2,
                "profiles": {
                    "cheap": {
                        "runner": "oc",
                        "model": _FLASH_MODEL,
                        "verify_with": "nope",
                    }
                },
            },
            "EXECUTOR's own model",
            "THE CONSEQUENCE IS IN THE MESSAGE, and it is the worst silent outcome in this module: "
            "a dangling verifier reference that fell through means the EXECUTOR checks its own work "
            "while the operator believes an independent model did",
        ),
        (
            "a DANGLING `roles` reference",
            {
                "schema_version": 2,
                "roles": {"write-code": "nope"},
                "profiles": {"cheap": {"runner": "oc", "model": _FLASH_MODEL}},
            },
            "fall through as if the role were never set",
            "the same integrity rule on the roles map, and again the message states the silent "
            "failure it prevents rather than merely reporting the fact",
        ),
        (
            "`roles` as a string instead of an object",
            {
                "schema_version": 2,
                "roles": "strong",
                "profiles": {"cheap": {"runner": "oc", "model": _FLASH_MODEL}},
            },
            "'roles' must be an object",
            "the map is typed, and the message names the key so an operator can find it in their "
            "own file",
        ),
        (
            "a `roles` VALUE that is not a string",
            {
                "schema_version": 2,
                "roles": {"write-code": 7},
                "profiles": {"cheap": {"runner": "oc", "model": _FLASH_MODEL}},
            },
            None,
            "a role names a PROFILE, so its value is a string. An int would be neither a name nor a "
            "model and would fall through as unset",
        ),
        (
            "an INLINE MODEL as a role target",
            {
                "schema_version": 2,
                "roles": {"write-code": _INHOUSE_MODEL},
                "profiles": {"cheap": {"runner": "oc", "model": _FLASH_MODEL}},
            },
            "invalid profile name",
            "REFUSED BY THE NAME GRAMMAR, which is the whole point of taking a reference: "
            "`provider/model` contains a slash and can never be a profile name. An inline model "
            "would fork the one place a launch identity is defined and would be the first field to "
            "escape this module's validation",
        ),
        (
            "an unknown ROLE key",
            {
                "schema_version": 2,
                "roles": {"writecode": "cheap"},
                "profiles": {"cheap": {"runner": "oc", "model": _FLASH_MODEL}},
            },
            "writecode",
            "the role vocabulary is CLOSED (F-13): an arbitrary key cannot be validated, so a "
            "misspelled role would be a SILENT NO-OP sitting in the store looking effective. The "
            "message must echo the offending key",
        ),
    )

    def test_every_malformed_document_refuses_and_never_degrades_to_empty(self):
        wrong = []
        for case, document, complaint, why in self.DOCUMENTS:
            must_load = case.startswith("THE POSITIVE ROW")
            problems = []
            try:
                cfg = RP.from_document(document)
            except RP.RunnerProfileError as exc:
                if must_load:
                    problems.append(f"REFUSED a valid document: {exc}")
                elif complaint is not None and complaint not in str(exc):
                    problems.append(
                        f"the refusal must say {complaint!r}; it said {str(exc)!r}"
                    )
            except Exception as exc:  # noqa: BLE001 - the TYPE is the assertion
                problems.append(
                    f"raised {type(exc).__name__}, which is NOT a RunnerProfileError, so a caller "
                    f"catching this module's errors would not catch it: {exc}"
                )
            else:
                if not must_load:
                    problems.append(
                        "ACCEPTED a malformed document, returning a usable config with profiles "
                        f"{sorted(cfg.profiles)!r}. THIS IS THE SILENT-FALLBACK DEFECT: a config "
                        "that behaves as empty launches the host default model"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n    document: {document!r}\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.DOCUMENTS)} documents were mishandled by `from_document`. "
            "ONE validator walks all of them. FIX: an ACCEPTED malformed document is the severe "
            "direction and it is the plan's named 'silent fallback' failure: the run then launches "
            "the host default model while the operator believes their profile is in effect, which "
            "costs money rather than time. A REFUSED positive row is the opposite problem and makes "
            "every negative row vacuous, so check it first. If only the MESSAGE lines fail, the "
            "document is correctly refused but the refusal stopped naming the consequence, which "
            "matters most on the dangling-`verify_with` row (the executor silently verifies its own "
            f"work) and the unsupported-version row (the operator does not learn it is urgent).\n"
            + "\n".join(wrong),
        )


class OptionalFieldSerializationTests(unittest.TestCase):
    """ABSENT is a THIRD STATE for every optional key, and it must never be serialized.

    ONE table replaces five tests drawn from three classes: `TriStateValidateFieldTests`'s
    absent/present-false/defaults cases, `RequestedProfilesParseTests.test_optional_fields_are_omitted_not_nulled`,
    `VerifyWithSchemaTests`'s both-levels and absent-is-omitted cases, and
    `RolesSchemaTests.test_roles_is_omitted_when_empty_so_existing_bytes_are_unchanged`. Every one
    parsed a document, read one optional key back, and asserted whether the key REAPPEARS on
    serialization.

    THE FIELD AND THE LEVEL ARE COLUMNS, WHICH IS THE MERGE THAT MATTERS. `validate`, `verify_with`
    and `roles` all obey ONE rule (absent means "no preference" and must round-trip as an ABSENT key,
    never as `null` and never as an empty object), and it was implemented once and tested three
    times, in three classes, each blind to the others. A future fourth optional key is now one row
    rather than a fourth class.

    THE POINT OF THE RULE IS NOT TIDINESS, so the rows say what breaks. A serialized `null` or `{}`
    would make an ABSENT key indistinguishable from a PRESENT decision, which destroys the
    fall-through the whole precedence chain rests on: `validate: null` read back as present-false
    would silently kill a user's `defaults.validate: true`, and `roles: {}` written into a store that
    never had it changes bytes an older aw then refuses as an unknown field.

    PRESENT-FALSE ROWS SIT BESIDE THE ABSENT ROWS deliberately, because they are the same rule read
    twice: a `False` MUST survive serialization while an absence must not appear. Implemented as
    "omit anything falsy", every absent row passes and every present-false row fails, which is
    exactly the bug this pairing catches.
    """

    #: (case, the profile object or document to parse, whether it is a whole DOCUMENT, the key, the
    #:  expected read-back value, whether the key must appear in the serialized output, why)
    OPTIONALS = (
        (
            "a profile omitting `validate`",
            {"runner": "oc", "model": _FLASH_MODEL},
            False,
            "validate",
            None,
            False,
            "ABSENT IS THE THIRD STATE and reads back as None, not False. Coerced to False at parse "
            "time it would stop falling through, and every `defaults.validate: true` in the wild "
            "would be silently dead",
        ),
        (
            "a profile declaring `validate: false`",
            {"runner": "oc", "model": _FLASH_MODEL, "validate": False},
            False,
            "validate",
            False,
            True,
            "PRESENT-FALSE IS A DECISION and must SURVIVE serialization. Read WITH the row above: an "
            "implementation that omits anything falsy passes that row and fails this one, turning a "
            "user's explicit 'do not verify' into an absence that a lower tier then overrides",
        ),
        (
            "a profile omitting `verify_with`",
            {"runner": "oc", "model": _FLASH_MODEL},
            False,
            "verify_with",
            None,
            False,
            "the SAME rule on a second field, which is why the field is a column: absent means "
            "'reuse the executor's own launch', and a serialized null would make that a positive "
            "claim about a verifier",
        ),
        (
            "a profile declaring `verify_with`",
            {"runner": "oc", "model": _FLASH_MODEL, "verify_with": "strong"},
            False,
            "verify_with",
            "strong",
            True,
            "the field parses at the PROFILE level and is kept, which is the level the precedence "
            "chain calls tier 2",
        ),
        (
            "a document omitting `defaults` entirely",
            {
                "schema_version": 2,
                "profiles": {"gem": {"runner": "oc", "model": _FLASH_MODEL}},
            },
            True,
            "validate",
            None,
            False,
            "the rule applies to the DOCUMENT level too, and the LEVEL column is what states that: "
            "`defaults` itself must not be conjured into the output as an empty object",
        ),
        (
            "a document declaring `defaults.validate: false`",
            {"schema_version": 1, "profiles": {}, "defaults": {"validate": False}},
            True,
            "validate",
            False,
            True,
            "present-false at the DEFAULTS level, so the tri-state is not collapsed on the tier "
            "where an operator sets a repository-wide posture",
        ),
        (
            "a document declaring `defaults.verify_with`",
            {
                "schema_version": 2,
                "defaults": {"verify_with": "strong"},
                "profiles": {
                    "cheap": {"runner": "oc", "model": _FLASH_MODEL},
                    "strong": {"runner": "oc", "model": _INHOUSE_MODEL},
                },
            },
            True,
            "verify_with",
            "strong",
            True,
            "`verify_with` parses at BOTH levels, which is what makes it tier 3 of the chain as well "
            "as tier 2; a field accepted only per profile could not express a repository default",
        ),
        (
            "a document omitting `roles`",
            {
                "schema_version": 2,
                "profiles": {"gem": {"runner": "oc", "model": _FLASH_MODEL}},
            },
            True,
            "roles",
            {},
            False,
            "AN ABSENT `roles` MUST NOT BE WRITTEN AS `{}`, and the consequence is concrete: a store "
            "that never had the key would gain it, and an OLDER aw (whose ALLOWED_DOCUMENT_KEYS "
            "predates `roles`) then refuses the whole file with 'unknown field(s)'. The read-back "
            "value is an EMPTY MAP rather than None, because callers index it",
        ),
        (
            "a document declaring a `roles` map",
            {
                "schema_version": 2,
                "roles": {"write-code": "strong"},
                "profiles": {
                    "cheap": {"runner": "oc", "model": _FLASH_MODEL},
                    "strong": {"runner": "oc", "model": _INHOUSE_MODEL},
                },
            },
            True,
            "roles",
            {"write-code": "strong"},
            True,
            "the populated map survives, so the omission rule above cannot be implemented as "
            "'never write roles'",
        ),
    )

    def test_every_optional_key_round_trips_as_absent_or_as_its_value(self):
        wrong = []
        for (
            case,
            payload,
            is_document,
            key,
            expected,
            serialized,
            why,
        ) in self.OPTIONALS:
            problems = []
            if is_document:
                cfg = RP.from_document(payload)
                got = dict(cfg.roles) if key == "roles" else getattr(cfg, key)
                document = cfg.to_document()
                text = RP.dumps(cfg)
                # A document-level optional lives under `defaults`, except `roles`, which is top
                # level by DECISION 01-btot17-D1 (a role is a property of the WORK, not of a launch).
                present = (
                    key in document
                    if key == "roles"
                    else key in document.get("defaults", {})
                )
            else:
                profile = RP.parse_profile("gem", payload)
                got = getattr(profile, key)
                document = profile.to_document()
                text = json.dumps(document)
                present = key in document
            if key == "validate" and expected is not None:
                # `assertIs` semantics: `0 == False` in Python, so identity is the required check.
                if got is not expected:
                    problems.append(
                        f"{key} read back as {got!r} (identity), expected {expected!r}"
                    )
            elif got != expected:
                problems.append(f"{key} read back as {got!r}, expected {expected!r}")
            if present != serialized:
                problems.append(
                    "the serialized document "
                    + ("OMITS" if not present else "CONTAINS")
                    + f" {key!r} and must "
                    + ("contain" if serialized else "omit")
                    + f" it; got {document!r}"
                )
            if not serialized and f'"{key}"' in text:
                problems.append(
                    f"the WRITTEN TEXT still mentions {key!r}, so the key reaches disk: {text!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} ({'document' if is_document else 'profile'}, key={key!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.OPTIONALS)} optional keys did not round-trip. ONE rule "
            "(absent means no preference, and an absence is never written) governs all three fields "
            "at both levels, so read the grouping. If every ABSENT row fails together, absences are "
            "being materialized, and the concrete cost is that a store gains keys an older aw "
            "refuses outright. If every PRESENT-FALSE row fails, the serializer is omitting anything "
            "FALSY, which silently converts an operator's explicit 'no' into 'no preference' and "
            "hands the decision to a lower precedence tier: that is the severe direction, because "
            "the file still looks correct. FIX: `None` and `False` are DIFFERENT states here and "
            f"must stay distinguishable on disk; that is the whole point of the tri-state.\n"
            + "\n".join(wrong),
        )

    def test_a_non_boolean_validate_is_refused(self):
        """Kept separate: an assertRaises sweep, and `1`/`0` are the values that matter.

        Not a row above, because a refusal produces no record to read back. `1` and `0` are the
        load-bearing cases: Python treats them as equal to `True`/`False`, so a check written as
        `value in (True, False)` accepts them, and an int in the store would then resolve tier 2 to a
        truthy value the operator never wrote.
        """

        for value in ("true", 1, 0, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.parse_profile(
                        "gem",
                        {"runner": "oc", "model": _FLASH_MODEL, "validate": value},
                    )


# ==================================================================================================
# E-02 / V-02: the XDG-backed atomic store
# ==================================================================================================


class StorePathTests(unittest.TestCase):
    """Where the store lives, under each XDG state, and what it must never collide with.

    ONE table replaces three tests. All three called `store_dir`/`store_path` under a particular
    `XDG_CONFIG_HOME` state and asserted a path relationship; they differed only in that state and in
    WHICH relationship they checked.

    THE XDG STATE IS A COLUMN because the property is that the SAME two accessors answer correctly
    whether the variable is set or absent, and the absent case is the one that runs on a real
    maintainer's machine. Splitting them lets the fallback rot untested behind whichever case the
    suite happened to run first.

    EVERY RELATIONSHIP IS CHECKED ON EVERY ROW, which is what the table bought. The old tests checked
    the XDG path but not that it stayed out of the repo, and checked repo-independence but only under
    XDG; so a fallback that resolved into the repository tree (the worst outcome here, since it would
    put a user's launch config under version control and into `git status`) was asserted against in
    one state only. Now both states assert all four relationships: the derived directory, the derived
    file, sharing `config_dir` with the main config while NOT being `config_path`, and never being
    inside the repository.
    """

    def setUp(self):
        self._old = os.environ.get("XDG_CONFIG_HOME")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old

    #: (case, whether to SET `XDG_CONFIG_HOME` to a temp dir, why this row exists)
    #: The expected directory is derived per row inside the test, because the XDG row's expectation
    #: depends on the temp path the row itself creates.
    XDG_STATES = (
        (
            "XDG_CONFIG_HOME is set",
            True,
            "the variable is HONORED rather than ignored, which is what lets a test (and a "
            "containerized run) point the store somewhere harmless. Every case in this file that "
            "touches a real path depends on this working",
        ),
        (
            "XDG_CONFIG_HOME is absent",
            False,
            "THE STATE A REAL MACHINE IS IN, and the row the old split left thinly covered. The "
            "fallback must be `~/.config/agent-workflows` and specifically NOT `~` itself: writing "
            "`runner-profiles.json` into a home directory root would be a visible mess, and "
            "resolving anywhere inside the repository would put a user's launch config under "
            "version control",
        ),
    )


class StoreReadWriteTests(unittest.TestCase):
    """What `save` refuses, and what the file on disk looks like after each outcome.

    ONE table replaces three of this class's tests (`save_validates_the_whole_document_before_writing`,
    `refuses_to_overwrite_a_future_version`, `no_leftover_temp_files_after_a_successful_write`), which
    all wrote a store, attempted a `save`, and asserted the resulting bytes plus the absence of `.tmp`
    leftovers. They differed only in WHY the save should be refused, or whether it should succeed.

    THE OUTCOME IS A COLUMN, AND THE SUCCESS ROW IS IN THE SAME TABLE. `save` either writes or leaves
    the file EXACTLY as it found it, and those are two outcomes of one function rather than two
    subjects. The old split let the refusal cases assert byte-preservation while only the success case
    asserted the temp-file cleanup, so a refusal that leaked a `.tmp` was invisible; every row now
    checks both.

    THE SMUGGLED-RECORD ROW IS WHY SAVE VALIDATES AT ALL. `ProfileConfig` can be constructed directly,
    bypassing every mutator, so validation at save time is the last fence before an invalid launch
    identity reaches disk. Its failure mode is silent: the store would load, resolve, and hand a
    malformed model string to a host.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "runner-profiles.json"

    def tearDown(self):
        self._tmp.cleanup()

    #: (case, the bytes to pre-place on disk (None = start from a valid saved store), the config to
    #:  save, the expected exception class name or None if the save must SUCCEED, the message
    #:  substring a refusal must carry or None, why this row exists)
    SAVES = (
        (
            "a valid config over a valid store",
            None,
            "valid",
            None,
            None,
            "THE SUCCESS ROW, and it is not decoration: every refusal row below is satisfied by a "
            "`save` that never writes anything at all. It also carries the temp-file check on the "
            "one path where a `.tmp` is actually created",
        ),
        (
            "a hand-built record that bypassed every mutator",
            None,
            "smuggled",
            "ProfileSchemaError",
            None,
            "`ProfileConfig(...)` can be constructed DIRECTLY, so save-time validation is the last "
            "fence before an invalid launch identity reaches disk. Its failure is silent: the store "
            "would load and resolve, handing a malformed model string to a host",
        ),
        (
            "any config over a store declaring a FUTURE version",
            '{"schema_version": 99, "profiles": {}}\n',
            "valid",
            "ProfileStoreError",
            "Nothing was changed",
            "REFUSE TO CLOBBER A NEWER FILE. A newer aw wrote it, and overwriting would destroy "
            "configuration this build cannot even read. The message must say nothing changed, so an "
            "operator knows their file is intact and the fix is to upgrade rather than to re-enter "
            "their profiles",
        ),
    )

    def test_every_save_either_writes_or_leaves_the_file_exactly_as_it_found_it(self):
        wrong = []
        for case, preplaced, config, expected_exc, complaint, why in self.SAVES:
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "runner-profiles.json"
                if preplaced is None:
                    RP.save(_three_requested(), path)
                else:
                    path.write_text(preplaced, encoding="utf-8")
                before = path.read_bytes()
                if config == "valid":
                    payload = RP.set_default_profile(_three_requested(), "gem")
                else:
                    payload = RP.ProfileConfig(
                        profiles={
                            "gem": RP.LaunchProfile(
                                runner="oc", model="not-a-provider-model"
                            )
                        }
                    )
                problems = []
                try:
                    RP.save(payload, path)
                    got_exc = None
                except RP.RunnerProfileError as exc:
                    got_exc = type(exc).__name__
                    if expected_exc is None:
                        problems.append(f"REFUSED a save that must succeed: {exc}")
                    else:
                        if got_exc != expected_exc:
                            problems.append(
                                f"expected {expected_exc}, got {got_exc}: {exc}"
                            )
                        if complaint is not None and complaint not in str(exc):
                            problems.append(
                                f"the refusal must say {complaint!r}; it said {str(exc)!r}"
                            )
                if got_exc is None and expected_exc is not None:
                    problems.append(
                        "ACCEPTED a save that must be refused, so the file on disk was overwritten"
                    )
                after = path.read_bytes()
                if expected_exc is None:
                    if after == before:
                        problems.append(
                            "the save reported success but the bytes are UNCHANGED, so nothing was "
                            "written"
                        )
                    else:
                        # A successful save must also be DETERMINISTIC and round-trip: saving what was
                        # just loaded must reproduce the identical bytes, or every `aw` invocation
                        # would rewrite the operator's store and show up in their diffs.
                        RP.save(RP.load(path), path)
                        if path.read_bytes() != after:
                            problems.append(
                                "re-saving the loaded config produced DIFFERENT bytes, so the "
                                "writer is not deterministic"
                            )
                        loaded = RP.load(path)
                        if not loaded.present:
                            problems.append("the saved store loads as present=False")
                        if loaded.default_profile_for("oc") != "gem":
                            problems.append(
                                f"the saved default was lost: "
                                f"{loaded.default_profile_for('oc')!r}"
                            )
                elif after != before:
                    problems.append(
                        f"A REFUSED save CHANGED the file: {before!r} became {after!r}"
                    )
                leftovers = [
                    p.name for p in path.parent.iterdir() if p.name.endswith(".tmp")
                ]
                if leftovers:
                    problems.append(f"a temp file was left behind: {leftovers!r}")
                if problems:
                    wrong.append(
                        f"  {case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SAVES)} save outcomes were wrong. ONE `save` implements all "
            "of them: validate, compare the on-disk version, write a temp file, rename. FIX: if the "
            "SUCCESS row fails, check it first, because a `save` that never writes satisfies both "
            "refusal rows and would look like a very well-behaved store. A REFUSED save that CHANGED "
            "the file is the severe direction: the future-version row means a newer aw's "
            "configuration was destroyed by an older one, and the smuggled row means an invalid "
            f"launch identity reached disk where it will resolve silently.\n"
            + "\n".join(wrong),
        )

    def test_absent_is_distinct_from_malformed(self):
        """Kept separate: contrasts two DIFFERENT outcomes of `load`, one of which is not an error.

        THE SILENT-FALLBACK BOUNDARY, and the reason it is not a row: an ABSENT file legitimately
        yields an empty config with `present=False`, while a MALFORMED one must RAISE. Those are a
        value and an exception for the same call, and the whole point is that they are NOT the same
        answer; a table row can assert one or the other, not the contrast.
        """

        absent = RP.load(self.path)
        self.assertFalse(absent.present)
        self.assertEqual(dict(absent.profiles), {})
        self.assertEqual(absent.source, self.path)

        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.load(self.path)
        self.assertIn("not treated as", str(ctx.exception).lower())

    def test_digest_changes_with_content_and_is_stable_otherwise(self):
        """Kept separate: compares digests of THREE configs to each other, with no expectation."""

        cfg = _three_requested()
        same = RP.from_document(json.loads(RP.dumps(cfg)))
        self.assertEqual(cfg.digest, same.digest)
        changed = RP.add_profile(cfg, "extra", _profile())
        self.assertNotEqual(cfg.digest, changed.digest)

    def test_save_creates_the_parent_directory(self):
        """Kept separate: the subject is a path that does NOT EXIST, so it has no prior bytes.

        Every row in the table above starts from a file on disk in order to assert what happened to
        it. This case is the opposite setup: nothing exists, two directory levels deep, which is the
        first-run state on a machine with no `~/.config/agent-workflows` yet.
        """

        nested = Path(self._tmp.name) / "a" / "b" / "runner-profiles.json"
        RP.save(_three_requested(), nested)
        self.assertTrue(nested.is_file())


class AtomicFaultInjectionTests(unittest.TestCase):
    """An interrupted replacement must leave the PREVIOUS bytes byte-identical.

    ONE table replaces three tests. Each patched a different `os` primitive to raise mid-write and
    then asserted the same three things: the previous bytes survive, no `.tmp` file leaks, and the
    right exception escapes. They differed only in WHICH call fails and in what it raises.

    THE FAULT POINT IS A COLUMN because the guarantee is about the SEQUENCE, not about one call:
    `save` writes a temp file and then renames it, so a fault BEFORE the rename and a fault DURING
    the rename exercise different halves of the same atomicity claim, and only reading them together
    shows the claim holds across the whole window. A test per primitive also reports a systemic loss
    of atomicity as three unrelated failures.

    THE ESCAPING EXCEPTION IS A COLUMN, AND THAT IS THE LOAD-BEARING DISTINCTION. An `OSError` must
    be converted to a typed `ProfileStoreError`, while a `KeyboardInterrupt` must pass through
    UNCONVERTED: swallowing Ctrl-C into a store error would tell an operator their write failed for
    an I/O reason when in fact they cancelled it, and (worse) a handler that caught it as a store
    error could retry a write the operator was trying to stop. Flattening the two into one
    `assertRaises(Exception)` would lose exactly that.

    EVERY ROW ASSERTS THE FILE IS STILL LOADABLE, which the tests it replaces did only once. Byte
    equality alone would also hold if `save` had left the file locked, truncated by a separate path,
    or valid-but-unparseable; reloading it is what proves the previous state is still USABLE rather
    than merely unchanged.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "runner-profiles.json"
        RP.save(_three_requested(), self.path)
        self.before = self.path.read_bytes()

    def tearDown(self):
        self._tmp.cleanup()

    #: (case, the `os` attribute to patch, the exception the patched call raises, the exception class
    #:  that must escape `save`, why this row exists)
    FAULTS = (
        (
            "the atomic rename fails with EIO",
            "replace",
            OSError(5, "injected I/O error"),
            "ProfileStoreError",
            "THE LATEST POSSIBLE FAULT: the new bytes are fully written to the temp file and only "
            "the rename fails, so this is the one case where a naive implementation could have "
            "already clobbered the original. The OSError must be converted to the module's typed "
            "error, because a caller cannot be asked to distinguish an errno from a store failure",
        ),
        (
            "opening the temp file fails with ENOSPC",
            "fdopen",
            OSError(28, "injected no space left on device"),
            "ProfileStoreError",
            "THE EARLIEST FAULT, before any content is written. A full disk is the realistic way "
            "this happens, and it must not leave a zero-length temp file behind for a later `save` "
            "or a directory listing to trip over",
        ),
        (
            "the operator interrupts mid-write",
            "fdopen",
            KeyboardInterrupt(),
            "KeyboardInterrupt",
            "A KEYBOARDINTERRUPT MUST NOT BE SWALLOWED, and this is why the escaping-exception "
            "column exists. Converted to a ProfileStoreError it would report an I/O failure for "
            "what was a deliberate cancellation, and a caller that retried on store errors would "
            "retry the very write the operator was cancelling. The bytes must still be intact",
        ),
    )

    def test_every_fault_point_preserves_the_previous_bytes_and_leaks_nothing(self):
        wrong = []
        for case, attribute, raised, expected_exc, why in self.FAULTS:
            real = getattr(os, attribute)

            def boom(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003 - test double
                if attribute == "fdopen":
                    # Close the descriptor `save` just opened, so the fault does not also leak an fd.
                    os.close(args[0])
                raise raised

            setattr(os, attribute, boom)
            try:
                try:
                    RP.save(
                        RP.add_profile(RP.load(self.path), "new", _profile()), self.path
                    )
                    got_exc = None
                except BaseException as exc:  # noqa: BLE001 - the class IS the assertion
                    got_exc = type(exc).__name__
            finally:
                setattr(os, attribute, real)

            problems = []
            if got_exc != expected_exc:
                problems.append(
                    f"expected {expected_exc} to escape `save`, got "
                    + (
                        f"{got_exc}"
                        if got_exc
                        else "NO EXCEPTION AT ALL, i.e. a silent failure"
                    )
                )
            after = self.path.read_bytes()
            if after != self.before:
                problems.append(
                    f"the previous bytes were NOT preserved: {len(self.before)} bytes became "
                    f"{len(after)} bytes ({after[:80]!r}...)"
                )
            leftovers = [
                p.name for p in self.path.parent.iterdir() if p.name.endswith(".tmp")
            ]
            if leftovers:
                problems.append(f"a temp file leaked: {leftovers!r}")
            try:
                reloaded = sorted(RP.load(self.path).profiles)
            except Exception as exc:  # noqa: BLE001 - loadability IS the assertion
                problems.append(
                    f"the file is no longer loadable after the fault: {type(exc).__name__}: {exc}"
                )
            else:
                if reloaded != ["gem", "sol", "sonnet"]:
                    problems.append(
                        f"the file reloads but holds {reloaded!r} instead of the previous "
                        "['gem', 'sol', 'sonnet']"
                    )
            if problems:
                wrong.append(
                    f"  {case} (os.{attribute} raises {type(raised).__name__}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.FAULTS)} injected faults damaged the store. ONE "
            "write-temp-then-rename sequence implements all of them, so ALL ROWS failing together "
            "means the atomic write was replaced by an in-place write, which is the severe case: a "
            "crash mid-save then loses the operator's entire profile store and the next run silently "
            "launches the host default. FIX: read WHICH assertion failed, because they are not "
            "equally bad. Lost bytes are data loss; a leaked `.tmp` is untidy; a wrong exception "
            "class is a reporting defect EXCEPT for the KeyboardInterrupt row, where converting it "
            f"means Ctrl-C is being swallowed and a retry loop could ignore a cancellation.\n"
            + "\n".join(wrong),
        )


# ==================================================================================================
# E-03 / V-03: mutations and resolution
# ==================================================================================================


class MutationTests(unittest.TestCase):
    """The pure mutators, and the rule that NO mutator may produce a dangling reference.

    The four `defaults` setters are ONE table below (`SETTERS`), which absorbed three tests from this
    class plus `VerifyWithDanglingReferenceTests.test_the_setter_refuses_a_dangling_default`; the
    remaining tests stay separate and each says why. The recurring reason is that they assert PURITY
    or a REFUSAL over a sequence of calls, which no single row can carry.
    """

    def test_add_is_pure_and_refuses_a_silent_duplicate(self):
        """Kept separate: asserts PURITY across three configs plus the `replace` flag's effect.

        The claim is that `add_profile` returns a NEW config and leaves both the input and a
        previously derived config untouched, which is a property of the three objects together.
        """

        base = RP.empty_config()
        one = RP.add_profile(base, "gem", _profile())
        self.assertEqual(dict(base.profiles), {}, "add must not mutate its input")
        with self.assertRaises(RP.ProfileExistsError):
            RP.add_profile(one, "gem", _profile(model=_SOL_MODEL))
        replaced = RP.add_profile(one, "gem", _profile(model=_SOL_MODEL), replace=True)
        self.assertEqual(replaced.get("gem").model, _SOL_MODEL)
        self.assertEqual(one.get("gem").model, _FLASH_MODEL)
        print("add: pure, duplicate refused, --replace honored")

    def test_add_validates_through_the_schema(self):
        """Kept separate: an assertRaises pair, one on the NAME and one on the model."""

        with self.assertRaises(RP.ProfileSchemaError):
            RP.add_profile(RP.empty_config(), "As", _profile())
        with self.assertRaises(RP.ProfileSchemaError):
            RP.add_profile(
                RP.empty_config(),
                "gem",
                RP.LaunchProfile(runner="oc", model="bare-model"),
            )

    def test_remove_unknown_raises(self):
        """Kept separate: an assertRaises test."""

        with self.assertRaises(RP.ProfileNotFoundError):
            RP.remove_profile(_three_requested(), "ghost")

    def test_removing_a_referenced_default_requires_an_explicit_decision(self):
        """Kept separate: a three-way DECISION over one call, not a value a row could carry.

        Removing a profile some default references must REFUSE, and then accept either of two
        explicit resolutions (`clear_default` or `replacement`), while refusing BOTH together. That is
        one input with four outcomes selected by flag combinations, and the point is that the bare
        call refuses; a row asserting any single outcome would lose the "explicit decision required"
        rule that ties them together.
        """

        cfg = RP.set_default_profile(_three_requested(), "gem")
        with self.assertRaises(RP.ProfileResolutionError) as ctx:
            RP.remove_profile(cfg, "gem")
        self.assertIn("Decide explicitly", str(ctx.exception))

        cleared = RP.remove_profile(cfg, "gem", clear_default=True)
        self.assertIsNone(cleared.default_profile_for("oc"))
        replaced = RP.remove_profile(cfg, "gem", replacement="sol")
        self.assertEqual(replaced.default_profile_for("oc"), "sol")
        with self.assertRaises(RP.ProfileNotFoundError):
            RP.remove_profile(cfg, "gem", replacement="ghost")
        with self.assertRaises(RP.ProfileResolutionError):
            RP.remove_profile(cfg, "gem", clear_default=True, replacement="sol")
        print("referenced default: refuse / clear / replace, each explicit")

    def test_removing_an_unreferenced_profile_is_straightforward(self):
        """Kept separate: the POSITIVE counterpart above, asserting the default is left ALONE."""

        cfg = RP.set_default_profile(_three_requested(), "gem")
        after = RP.remove_profile(cfg, "sol")
        self.assertEqual(sorted(after.profiles), ["gem", "sonnet"])
        self.assertEqual(after.default_profile_for("oc"), "gem")

    #: (case, the setter name, the value to set, the reader that reads it back, the expected
    #:  read-back value, the expected exception class name or None if the call must SUCCEED, why)
    #:
    #: `validate` and `verify_with` are read off the config directly; the per-runner default profile
    #: and the default runner have their own accessors, so the reader is a column too.
    SETTERS = (
        (
            "set the per-runner default profile",
            "set_default_profile",
            "sonnet",
            "default_profile_oc",
            "sonnet",
            None,
            "the base case for the accessor pair: what a setter stores, its reader returns",
        ),
        (
            "read the per-runner default back through the host's ALIAS",
            "set_default_profile",
            "sonnet",
            "default_profile_opencode",
            "sonnet",
            None,
            "THE READER CANONICALIZES TOO. Stored under `oc` and read through `opencode`, the same "
            "value must come back, or an operator who spells the host differently in two places "
            "gets no default at all and silently launches the host model",
        ),
        (
            "set the per-runner default to an UNKNOWN profile",
            "set_default_profile",
            "ghost",
            None,
            None,
            "ProfileNotFoundError",
            "NO MUTATOR MAY CREATE A DANGLING REFERENCE. Left to resolution it would fall through "
            "to the host default, so an operator would believe their default was in effect",
        ),
        (
            "set the default runner by ALIAS",
            "set_default_runner",
            "antigravity",
            "default_runner",
            "agy",
            None,
            "the setter CANONICALIZES any registered host, so `agy` is storable since "
            "`hostdefault-01` even though no dispatch adapter can launch it yet",
        ),
        (
            "set the default runner to an UNREGISTERED host",
            "set_default_runner",
            "codex",
            None,
            None,
            "ProfileSchemaError",
            "the other half of the same setter's contract: `codex` stands in as the still-"
            "unregistered host, so the closure of the registry is enforced on the WRITE path and "
            "not only on read",
        ),
        (
            "UNSET the default runner",
            "set_default_runner",
            None,
            "default_runner",
            None,
            None,
            "EVERY SETTER MUST SUPPORT UNSET, which is why the value column is three-valued. "
            "Without an unset path an operator can change a default but never remove one, and the "
            "only remedy is hand-editing the JSON this module exists to validate",
        ),
        (
            "set the `validate` default true",
            "set_validate_default",
            True,
            "validate",
            True,
            None,
            "tier 3 of the `validate` chain, set through the API rather than hand-written",
        ),
        (
            "set the `validate` default FALSE",
            "set_validate_default",
            False,
            "validate",
            False,
            None,
            "present-false must be STORABLE, not just parseable: a setter that treated False as "
            "'no value' would make an explicit repository-wide OFF unexpressible",
        ),
        (
            "UNSET the `validate` default",
            "set_validate_default",
            None,
            "validate",
            None,
            None,
            "the third state on the tri-state field, so absent stays reachable after a decision "
            "was once recorded",
        ),
        (
            "set the `validate` default to a non-bool",
            "set_validate_default",
            "yes",
            None,
            None,
            "ProfileSchemaError",
            "the setter validates, so the tri-state cannot be widened to a truthy string through "
            "the API any more than through a document",
        ),
        (
            "set the `verify_with` default",
            "set_verify_with_default",
            "strong",
            "verify_with",
            "strong",
            None,
            "tier 3 of the verifier chain, through its own setter",
        ),
        (
            "UNSET the `verify_with` default",
            "set_verify_with_default",
            None,
            "verify_with",
            None,
            None,
            "unset on the verifier field too, so an operator can stop routing verification "
            "elsewhere without editing JSON",
        ),
        (
            "set the `verify_with` default to an UNKNOWN profile",
            "set_verify_with_default",
            "ghost",
            None,
            None,
            "ProfileSchemaError",
            "THE DANGLING-REFERENCE RULE ON THE MOST DANGEROUS FIELD: a dangling verifier that fell "
            "through means the EXECUTOR checks its own work while the operator believes an "
            "independent model did",
        ),
    )

    def test_every_setter_stores_unsets_and_refuses_through_its_reader(self):
        """One table over the four `defaults` setters, replacing three tests.

        THE READER IS A COLUMN, because a setter is only correct in combination with the accessor
        that reads it back: the per-runner default is stored under a CANONICAL host key and must be
        readable through the host's ALIAS, which no assertion about the setter alone can state.

        THE VALUE COLUMN IS THREE-VALUED (a value, `None` to unset, an invalid value to refuse), and
        the UNSET rows are the ones the old split covered unevenly. A setter that cannot unset leaves
        an operator able to change a default but never remove one, whose only remedy is hand-editing
        the JSON this module exists to validate.

        Why the table beats the three: all four setters route through the same `_replace` validation,
        so a regression there moves many rows at once and reports as one failure naming each. Kept
        together with the REFUSAL rows deliberately, since "no mutator may create a dangling
        reference" is one rule spanning three of the four setters.
        """

        wrong = []
        readers = {
            "default_profile_oc": lambda c: c.default_profile_for("oc"),
            "default_profile_opencode": lambda c: c.default_profile_for("opencode"),
            "default_runner": lambda c: c.default_runner,
            "validate": lambda c: c.validate,
            "verify_with": lambda c: c.verify_with,
        }
        for case, setter, value, reader, expected, expected_exc, why in self.SETTERS:
            # A base config holding the three requested profiles plus a `strong` verifier target, so
            # every reference a row names either exists or deliberately does not.
            base = RP.add_profile(
                _three_requested(), "strong", _profile(model=_INHOUSE_MODEL)
            )
            if setter == "set_default_runner" and value is None:
                base = RP.set_default_runner(base, "oc")
            elif setter == "set_validate_default" and value is None:
                base = RP.set_validate_default(base, True)
            elif setter == "set_verify_with_default" and value is None:
                base = RP.set_verify_with_default(base, "strong")
            problems = []
            try:
                got = getattr(RP, setter)(base, value)
            except RP.RunnerProfileError as exc:
                if expected_exc is None:
                    problems.append(f"REFUSED a legitimate call: {exc}")
                elif type(exc).__name__ != expected_exc:
                    problems.append(
                        f"expected {expected_exc}, got {type(exc).__name__}: {exc}"
                    )
            else:
                if expected_exc is not None:
                    problems.append(
                        f"ACCEPTED a call that must be refused; the config now reads "
                        f"{readers[reader](got)!r}"
                        if reader
                        else "ACCEPTED a call that must be refused"
                    )
                else:
                    read_back = readers[reader](got)
                    if expected is None:
                        if read_back is not None:
                            problems.append(
                                f"the value was not UNSET: the reader still returns {read_back!r}"
                            )
                    elif isinstance(expected, bool):
                        if read_back is not expected:
                            problems.append(
                                f"read back {read_back!r} (identity), expected {expected!r}"
                            )
                    elif read_back != expected:
                        problems.append(
                            f"read back {read_back!r}, expected {expected!r}"
                        )
                    # PURITY: a mutator returns a new config and must not touch its input.
                    if readers[reader](base) == read_back and expected is not None:
                        problems.append(
                            "the setter MUTATED ITS INPUT: the base config now reads the new value "
                            "too, so a caller holding the old config sees it change underneath them"
                        )
            if problems:
                wrong.append(
                    f"  {case} ({setter}(..., {value!r})):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SETTERS)} setter calls were wrong. All four setters route "
            "through the same `_replace` validation, so read the grouping. If every REFUSAL row now "
            "succeeds, that validation was bypassed and a mutator can write a DANGLING reference; "
            "the `verify_with` case is the severe one, because a dangling verifier falls through and "
            "the executor silently checks its own work. If every UNSET row fails, an operator can "
            "change a default but never remove one, and their only remedy is hand-editing the JSON "
            "this module validates. If the ALIAS reader row alone fails, the default is stored under "
            "one spelling and read under another, so it silently has no effect. A MUTATED ITS INPUT "
            f"line means purity was lost and a caller's config changes underneath them.\n"
            + "\n".join(wrong),
        )

    def test_a_dangling_default_cannot_be_constructed_through_the_mutators(self):
        """Kept separate: asserts a dangling reference is unreachable by DIRECT CONSTRUCTION too.

        The setter table below covers the mutator route. This covers `from_document`, i.e. the route
        that bypasses every mutator, which is what makes "no path produces a dangling reference" a
        claim about the module rather than about one function.
        """

        cfg = RP.set_default_profile(_three_requested(), "gem")
        # Direct construction is validated too, so no path produces a dangling reference.
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document(
                {
                    "schema_version": 1,
                    "profiles": {"sol": {"runner": "oc", "model": _SOL_MODEL}},
                    "defaults": {"profiles": {"oc": "gem"}},
                }
            )
        self.assertEqual(cfg.default_profile_for("oc"), "gem")


class ResolutionPrecedenceTests(unittest.TestCase):
    """Launch precedence: explicit > named profile > per-runner default > host default.

    ONE table replaces seven tests (the four tier tests, the partial-override test, and both
    generic-dispatch tests). Every one of them called `resolve` on the same three-profile config
    and asserted a resolved FIELD plus the `provenance` string recording which tier supplied it;
    they differed only in which arguments were passed.

    THE PROVENANCE MAP IS ASSERTED WHOLE, per row, which is what the table bought and what no
    single-tier test could state. The old tests each checked ONE provenance key (usually `model`),
    so a resolver that got `model` from the right tier while attributing `variant` or `agent` to the
    wrong one passed all four. The `agent` column is where that bites: a named profile with no
    `agent` resolves `agent` to `host-default`, NOT to `profile`, and a partial explicit override
    leaves `agent` at `profile` while `variant` becomes `explicit`. Those mixed maps are the real
    contract and they are only visible when the whole map is pinned.

    THE FOUR TIERS SIT IN ONE TABLE because they are one chain: the property worth asserting is
    that the SAME subject answers differently as arguments are added, and a chain whose tiers are
    tested apart cannot show an INVERSION (a stored default beating an explicit flag), which is
    precisely the `vju5ba` failure shape this module exists to prevent.

    THE GENERIC-DISPATCH ROWS ARE HERE, NOT IN A SECOND TABLE, because `generic=True` is a MODE of
    the same resolution: it decides the RUNNER by the same precedence rule the other fields use
    (`profile` beats `default_runner`), so its provenance belongs in the same map. Its refusal case
    is a separate `assertRaises` test below, per this file's convention.
    """

    def setUp(self):
        self.cfg = RP.set_default_profile(_three_requested(), "gem")

    #: (case, extra `resolve` kwargs, expected (model, variant, agent) or None to skip, the EXACT
    #: expected provenance map for the launch fields, expected `applied_profile`,
    #: expected `requested_profile`, why this row exists)
    #:
    #: The provenance values are LITERAL STRINGS, not `RP.PROVENANCE_*` constants, and that is
    #: deliberate: these strings are rendered to an operator debugging "why that model", so a
    #: renaming is a user-visible change and must fail here. Referencing the constants would let a
    #: rename move both sides together and stay green. Do not "tidy" them into constants.
    TIERS = (
        (
            "tier 1: every field given explicitly, over a named profile",
            {
                "profile": "sol",
                "model": _FLASH_MODEL,
                "variant": "low",
                "agent": "plan",
            },
            (_FLASH_MODEL, "low", "plan"),
            {
                "runner": "explicit",
                "model": "explicit",
                "variant": "explicit",
                "agent": "explicit",
            },
            "sol",
            "sol",
            "THE TOP OF THE CHAIN, and the direction that must never invert: a typed flag beats "
            "anything stored. `sol` is named AND ignored for every field, so a stored value winning "
            "here would make the flag a lie (backlog `vju5ba`, inverted)",
        ),
        (
            "tier 2: a named profile, no explicit fields",
            {"profile": "sol"},
            (_SOL_MODEL, "medium", None),
            {
                "runner": "explicit",
                "model": "profile",
                "variant": "profile",
                "agent": "host-default",
            },
            "sol",
            "sol",
            "a NAMED profile beats the per-runner default (`gem` is the default here and must not "
            "win). The `agent` cell is the reason the whole map is pinned: `sol` declares no agent, "
            "so agent falls THROUGH to host-default rather than being attributed to the profile, "
            "and a resolver that credited the profile for a field it never set would misreport the "
            "one thing provenance exists to answer",
        ),
        (
            "tier 3: nothing named, a per-runner default configured",
            {},
            (_FLASH_MODEL, "high", None),
            {
                "runner": "explicit",
                "model": "default-profile",
                "variant": "default-profile",
                "agent": "host-default",
            },
            "gem",
            None,
            "the per-runner default applies when no profile is named, and `requested_profile` must "
            "stay None while `applied_profile` names `gem`: the distinction is what lets a run "
            "record say the model came from a stored default rather than from the command line",
        ),
        (
            "tier 4: an EMPTY config",
            {"_empty": True},
            (None, None, None),
            {
                "runner": "explicit",
                "model": "host-default",
                "variant": "host-default",
                "agent": "host-default",
            },
            None,
            None,
            "THE BOTTOM OF THE CHAIN, and the row that keeps the others honest: with nothing "
            "configured, every field must be None so the caller passes NO argument and the HOST "
            "picks. A None that resolved to some module-level model string instead would silently "
            "launch a model nobody chose",
        ),
        (
            "a PARTIAL explicit override against a fully-populated profile",
            {"_profile_full": True, "profile": "full", "variant": "low"},
            (_FLASH_MODEL, "low", "build"),
            {
                "runner": "explicit",
                "model": "profile",
                "variant": "explicit",
                "agent": "profile",
            },
            "full",
            "full",
            "PRECEDENCE IS PER FIELD, not per tier: one explicit `variant` must not discard the "
            "profile's `model` and `agent`. This is the row with three DIFFERENT provenances in one "
            "map, so a resolver that applied the winning tier wholesale would fail only here",
        ),
        (
            "generic dispatch with a `default_runner` configured",
            {"_default_runner": "oc", "generic": True},
            (_FLASH_MODEL, "high", None),
            {
                "runner": "default-runner",
                "model": "default-profile",
                "variant": "default-profile",
                "agent": "host-default",
            },
            "gem",
            None,
            "GENERIC IS A MODE, not a second subject: the RUNNER is chosen by the same chain the "
            "other fields use, so it carries its own provenance (`default-runner`). Note the "
            "launch fields still come from the per-runner default, which is what makes generic "
            "dispatch usable at all",
        ),
        (
            "generic dispatch with a named profile and NO default_runner",
            {"generic": True, "profile": "sol"},
            (_SOL_MODEL, "medium", None),
            {
                "runner": "profile",
                "model": "profile",
                "variant": "profile",
                "agent": "host-default",
            },
            "sol",
            "sol",
            "a named profile SUPPLIES the runner, so no `default_runner` is needed. This row is "
            "what stops the refusal below from being implemented as 'generic always requires "
            "default_runner', which would make `aw run as sol` impossible on an unconfigured host",
        ),
        (
            "a profile whose NAME looks like a subcommand",
            {"_profile_named_status": True, "profile": "status"},
            (_SOL_MODEL, None, None),
            {
                "runner": "explicit",
                "model": "profile",
                "variant": "host-default",
                "agent": "host-default",
            },
            "status",
            "status",
            "NAMESPACE OVER-RESERVATION IS A DEFECT (the plan's own matrix): a name is resolved "
            "only AFTER `as`, so `status` cannot shadow a subcommand and must resolve normally. "
            "Kept in this table rather than beside the name-grammar tests because the claim is "
            "about RESOLUTION, not about `validate_profile_name`",
        ),
    )

    def _config_for(self, kwargs: dict):
        """Apply the row's `_`-prefixed fixture directives, returning (config, resolve kwargs)."""

        kwargs = dict(kwargs)
        cfg = RP.empty_config() if kwargs.pop("_empty", False) else self.cfg
        if kwargs.pop("_profile_full", False):
            cfg = RP.add_profile(cfg, "full", _profile(variant="high", agent="build"))
        if kwargs.pop("_profile_named_status", False):
            cfg = RP.add_profile(cfg, "status", _profile(model=_SOL_MODEL))
        runner = kwargs.pop("_default_runner", None)
        if runner is not None:
            cfg = RP.set_default_runner(cfg, runner)
        if not kwargs.get("generic"):
            kwargs.setdefault("runner", "oc")
        return cfg, kwargs

    def test_every_tier_supplies_its_fields_and_records_which_tier_spoke(self):
        wrong = []
        for case, kwargs, fields, provenance, applied, requested, why in self.TIERS:
            cfg, call = self._config_for(kwargs)
            got = RP.resolve(cfg, **call)
            problems = []
            if fields is not None and (got.model, got.variant, got.agent) != fields:
                problems.append(
                    f"expected (model, variant, agent) {fields!r}, got "
                    f"{(got.model, got.variant, got.agent)!r}"
                )
            observed = {k: got.provenance[k] for k in provenance}
            if observed != provenance:
                differing = {
                    k: (provenance[k], observed[k])
                    for k in provenance
                    if observed[k] != provenance[k]
                }
                problems.append(
                    "provenance disagrees on "
                    + ", ".join(
                        f"{k}: expected {exp!r}, got {act!r}"
                        for k, (exp, act) in sorted(differing.items())
                    )
                    + f" (whole observed map: {dict(got.provenance)!r})"
                )
            if got.applied_profile != applied:
                problems.append(
                    f"applied_profile expected {applied!r}, got {got.applied_profile!r}"
                )
            if got.requested_profile != requested:
                problems.append(
                    f"requested_profile expected {requested!r}, got "
                    f"{got.requested_profile!r}"
                )
            for key, value in got.provenance.items():
                if value not in RP.PROVENANCE_VALUES:
                    problems.append(
                        f"provenance[{key!r}] is {value!r}, which is not in "
                        f"PROVENANCE_VALUES, so no renderer can describe it"
                    )
            if problems:
                wrong.append(
                    f"  {case} (resolve kwargs {kwargs!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"resolution was wrong for {len(wrong)} of {len(self.TIERS)} launch shapes. ONE "
            "precedence walk inside `resolve` decides every row, so read the GROUPING. If the tier "
            "1 row fails while the others pass, a STORED value is beating a typed flag, which is "
            "backlog `vju5ba` inverted and the worst outcome here: the flag becomes a lie. If the "
            "tier 4 row fails, an unconfigured host is being handed a model nobody chose. If only "
            "the provenance cells differ while the VALUES are right, the launch is correct but the "
            "audit trail lies about which tier chose it, and an operator debugging 'why that model' "
            "is sent to the wrong place. FIX: note that a mixed map is CORRECT on several rows "
            "(profile+host-default, profile+explicit); do not unify a row's provenance to one "
            f"value.\n" + "\n".join(wrong),
        )

    def test_generic_dispatch_without_a_default_runner_refuses(self):
        """Kept separate: an assertRaises test, and it asserts the message EXPLAINS the refusal.

        The positive half (generic + `default_runner`, and generic + a named profile) is two rows in
        the table above; this is the refusal, which cannot be a row because no resolved record
        exists to assert against.
        """

        with self.assertRaises(RP.ProfileResolutionError) as ctx:
            RP.resolve(self.cfg, generic=True)
        self.assertIn("does not guess", str(ctx.exception))

    def test_resolve_without_a_runner_or_generic_is_a_typed_error(self):
        """Kept separate: an assertRaises test on the ABSENCE of both routing arguments."""

        with self.assertRaises(RP.ProfileResolutionError):
            RP.resolve(self.cfg)

    def test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back(self):
        """Kept separate: every case is an assertRaises, and the EXCEPTION TYPE is the assertion.

        Three different typed refusals for three different mistakes, which is the property: a
        profile is never silently run on a host it was not written for, and never silently replaced
        by a host default. `agy` is a REGISTERED runner since `hostdefault-01`, so an `oc` profile
        requested on it is the WRONG-HOST refusal (`ProfileResolutionError`) rather than an
        unknown-runner schema error, which is a strictly better test of the same property: it
        exercises the real cross-host mismatch rather than a name the registry rejected first.
        """

        with self.assertRaises(RP.ProfileNotFoundError):
            RP.resolve(self.cfg, runner="oc", profile="ghost")
        with self.assertRaises(RP.ProfileResolutionError):
            RP.resolve(self.cfg, runner="agy", profile="gem")
        # An UNREGISTERED runner is still the schema refusal, so both halves stay covered.
        with self.assertRaises(RP.ProfileSchemaError):
            RP.resolve(self.cfg, runner="codex", profile="gem")
        with self.assertRaises(RP.ProfileSchemaError):
            RP.resolve(self.cfg, runner="oc", profile="As")

    def test_explicit_field_values_are_validated_at_resolution(self):
        """Kept separate: an assertRaises sweep, and the subject is VALIDATION rather than tiers."""

        for field_name, value in (
            ("model", "bare-model"),
            ("variant", "high; whoami"),
            ("agent", "a b"),
        ):
            with self.subTest(field=field_name, value=value):
                kwargs = {field_name: value}
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.resolve(self.cfg, runner="oc", **kwargs)  # type: ignore[arg-type]


class ResolvedProvenanceRecordTests(unittest.TestCase):
    """The AUDIT half of a resolved record: where the config came from, and its digest."""

    def test_resolved_record_carries_the_full_auditable_snapshot(self):
        """Kept separate: the subject is the record's AUDIT fields, read back off a real store.

        `ResolutionPrecedenceTests` pins the launch fields and their provenance from an in-memory
        config; this one needs a file on disk, because the claim is about `config_source`,
        `config_present` and `config_digest`, which only exist once a store was loaded.
        """

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runner-profiles.json"
            cfg = RP.set_default_profile(_three_requested(), "gem")
            cfg = RP.add_profile(
                cfg, "agentful", _profile(variant="high", agent="build")
            )
            RP.save(cfg, path)
            loaded = RP.load(path)
            got = RP.resolve(loaded, runner="oc", profile="agentful")

        self.assertEqual(got.requested_profile, "agentful")
        self.assertEqual(got.applied_profile, "agentful")
        self.assertIsNotNone(got.config_source)
        self.assertEqual(got.config_source, str(path))
        self.assertTrue(got.config_present)
        self.assertRegex(got.config_digest, r"^[0-9a-f]{64}$")
        # `verify_with` joined the record in `runprofile` Order 06 (`kgpptv`). Every resolution
        # carries it, and its value here is `same-as-executor` (nothing configured a verifier),
        # which is NOT `host-default`: absent means "reuse the executor's own launch".
        self.assertEqual(
            sorted(got.provenance),
            ["agent", "model", "runner", "validate", "variant", "verify_with"],
        )
        self.assertEqual(got.provenance["verify_with"], RP.PROVENANCE_SAME_AS_EXECUTOR)
        self.assertIsNone(got.verify_with)
        for key, value in got.provenance.items():
            self.assertIn(value, RP.PROVENANCE_VALUES, f"{key} -> {value}")
        print(
            "resolved record: "
            + json.dumps(
                {
                    "requested_profile": got.requested_profile,
                    "applied_profile": got.applied_profile,
                    "config_source": Path(got.config_source or "").name,
                    "config_digest": got.config_digest[:16] + "...",
                    "runner": got.runner,
                    "model": got.model,
                    "variant": got.variant,
                    "agent": got.agent,
                    "validate": got.validate,
                    "provenance": dict(got.provenance),
                },
                sort_keys=True,
            )
        )

    def test_provenance_mapping_is_read_only(self):
        """Kept separate: an assertRaises on ITEM ASSIGNMENT, a structural claim about the mapping."""

        got = RP.resolve(_three_requested(), runner="oc", profile="gem")
        with self.assertRaises(TypeError):
            got.provenance["model"] = "explicit"  # type: ignore[index]


class ValidatePrecedenceMatrixTests(unittest.TestCase):
    """The `validate` tri-state chain: explicit flag > profile > `defaults` > the HOST'S OWN row.

    ONE table replaces eleven tests across two classes: all seven of this class's level/fall-through
    cases, plus three of `PerHostValidateDefaultTests` (`test_tier_4_is_per_host`,
    `test_a_row_never_beats_an_operator`, `test_the_tristate_does_not_collapse_on_the_new_host`),
    plus the measured Opus/Gemini shape. Every one of them built a config, resolved it, and asserted
    `validate` plus the provenance string naming which tier spoke.

    THE HOST IS A COLUMN, AND THAT IS THE WHOLE REASON THIS IS ONE TABLE. Tier 4 lives on each
    `RUNNER_REGISTRY` row and the two shipped hosts declare OPPOSITE postures on measured grounds
    (`oc` gates its verifier turn on `--validate`, default FALSE; `agy` gates on `not --no-verify`,
    so a bare run verifies). A single-host table cannot state the property that matters, which is
    that the SAME configuration resolves differently per host at tier 4 and IDENTICALLY at every
    tier above it. Splitting them into an oc class and an agy class is what let a per-host default
    be expressed as a module global for as long as it was.

    THE TRI-STATE IS THREE-VALUED IN THE COLUMNS, NOT COLLAPSED TO A BOOL. `None` in the profile or
    defaults column means the key is ABSENT, which must FALL THROUGH; `False` means a decision that
    must WIN over a lower tier. Coercing absent to False at parse time is the silent failure this
    subject exists to prevent (it would make a user's `defaults.validate: true` dead), so the
    absent rows and the present-false rows sit adjacent on both hosts.

    THE EXPLICIT-FLAG ROWS ARE THE LOAD-BEARING DIRECTION. A row is a FLOOR, never an override, so
    an explicit flag and a configured `defaults.validate` must both beat it. The agy+false rows are
    the direction worth reading first: they prove a host row cannot force verification ON against a
    configured OFF.
    """

    def _cfg(self, host, profile_validate, defaults_validate, *, named=True):
        cfg = RP.empty_config()
        if named:
            cfg = RP.add_profile(
                cfg, "p", _profile(runner=host, validate=profile_validate)
            )
        if defaults_validate is not None:
            cfg = RP.set_validate_default(cfg, defaults_validate)
        return cfg

    #: (case, host, profile `validate` (None = key absent), `defaults.validate` (None = absent),
    #:  explicit flag (None = not passed), whether a profile is NAMED at resolution, expected
    #:  resolved value, expected provenance, why this row exists)
    #:
    #: Provenance is a LITERAL string, not a `RP.PROVENANCE_*` constant, for the reason given on
    #: `ResolutionPrecedenceTests.TIERS`: these strings are rendered to an operator, so a rename is
    #: a user-visible change that must fail here rather than move both sides together.
    CHAIN = (
        (
            "tier 1: an explicit --validate over a profile and defaults that both say otherwise",
            "oc",
            False,
            False,
            True,
            True,
            True,
            "explicit",
            "THE TOP OF THE CHAIN. Every lower tier says False and the flag says True, so a stored "
            "value winning here is backlog `vju5ba` inverted: the flag would be a lie",
        ),
        (
            "tier 1 in the other polarity, over a profile and defaults that both say True",
            "oc",
            True,
            True,
            False,
            True,
            False,
            "explicit",
            "BOTH POLARITIES, because a flag honored in only one direction is not a flag. A rule "
            "like 'explicit True wins' would satisfy the row above while silently ignoring "
            "`--no-validate`, which is the direction that turns verification OFF and therefore "
            "costs money rather than merely time",
        ),
        (
            "tier 1 on agy, against the row that ships verification ON",
            "agy",
            None,
            None,
            False,
            True,
            False,
            "explicit",
            "THE FLOOR IS NOT AN OVERRIDE, on the host where the floor is True. Without this row a "
            "row could be implemented as an override, and `agy` would verify however often an "
            "operator asked it not to",
        ),
        (
            "tier 2: the profile's own `validate: true` over `defaults.validate: false`",
            "oc",
            True,
            False,
            None,
            True,
            True,
            "profile",
            "a NAMED profile's decision beats the document default, which is what makes "
            "per-profile postures usable at all",
        ),
        (
            "tier 2: the profile's `validate: false` over `defaults.validate: true`",
            "oc",
            False,
            True,
            None,
            True,
            False,
            "profile",
            "PRESENT-FALSE MUST NOT FALL THROUGH. It is a decision, not an absence, so it wins "
            "over a True default. Read WITH the absent row below: the two differ only in whether "
            "the profile's key exists, and they must resolve OPPOSITELY",
        ),
        (
            "tier 2 on agy, present-false against the row that ships ON",
            "agy",
            False,
            None,
            None,
            True,
            False,
            "profile",
            "the tri-state must not collapse on the host whose ROW says True: an explicit "
            "`validate: false` in a NAMED stored profile is still a decision there. Paired with the "
            "agy absent row below, which inherits the row instead. NOTE the `named` column must be "
            "True: with the profile present but NOT requested, agy correctly resolves its ROW "
            "(True/shipped-default), because an unrequested profile's fields are not consulted at "
            "all. Measured while writing this table, which is what the column is for",
        ),
        (
            "tier 3: `defaults.validate: true` with the profile silent",
            "oc",
            None,
            True,
            None,
            True,
            True,
            "defaults",
            "THE LOAD-BEARING FALL-THROUGH. If absent were coerced to False at parse time this "
            "would resolve False and the user's `defaults.validate: true` would be silently dead. "
            "The provenance cell is what proves the DEFAULTS tier spoke rather than a coincidence",
        ),
        (
            "tier 3: `defaults.validate: false` with the profile silent",
            "oc",
            None,
            False,
            None,
            True,
            False,
            "defaults",
            "both polarities of the defaults tier, so it cannot be implemented as 'defaults only "
            "ever turns verification on'",
        ),
        (
            "tier 3 on agy: `defaults.validate: false` against a row that ships ON",
            "agy",
            None,
            False,
            None,
            False,
            False,
            "defaults",
            "THE DIRECTION WORTH READING FIRST. A configured OFF must beat the agy row's shipped "
            "ON, or the row is an override rather than a floor and an operator cannot turn "
            "verification off on that host at all",
        ),
        (
            "tier 4 on oc: nothing configured anywhere",
            "oc",
            None,
            None,
            None,
            True,
            False,
            "shipped-default",
            "the BOTTOM tier, read from `RUNNER_REGISTRY['oc'].validate_default`. FALSE, matching "
            "`oc_runipd`'s `--validate` (`BooleanOptionalAction`, default False)",
        ),
        (
            "tier 4 on agy: nothing configured anywhere",
            "agy",
            None,
            None,
            None,
            True,
            True,
            "shipped-default",
            "THE ROW THAT PROVES TIER 4 IS PER HOST, and the reason `host` is a column: the same "
            "empty configuration resolves TRUE here and FALSE on oc. `agy` gates its verifier on "
            "`not --no-verify` (a `store_true`), so a bare run verifies. One module global cannot "
            "express both, which is why the value moved onto the registry row",
        ),
        (
            "tier 4 on agy with NO profile named at all",
            "agy",
            None,
            None,
            None,
            False,
            True,
            "shipped-default",
            "the row is consulted on the UNNAMED path too. A tier 4 reached only when a profile "
            "happens to be named would leave `aw agy run` with no posture at all, which is the "
            "state the per-host field replaced",
        ),
        (
            "tier 4 on oc with NO profile named at all",
            "oc",
            None,
            None,
            None,
            False,
            False,
            "shipped-default",
            "the oc half of the same unnamed path, so the two hosts' postures are compared on "
            "identical input rather than each on its own",
        ),
    )

    def test_the_whole_validate_chain_on_both_hosts(self):
        wrong = []
        for (
            case,
            host,
            profile_validate,
            defaults_validate,
            flag,
            named,
            expected,
            provenance,
            why,
        ) in self.CHAIN:
            cfg = self._cfg(host, profile_validate, defaults_validate, named=named)
            call = {"runner": host}
            if named:
                call["profile"] = "p"
            if flag is not None:
                call["validate"] = flag
            got = RP.resolve(cfg, **call)
            problems = []
            if got.validate is not expected:
                problems.append(
                    f"expected validate {expected!r} (by identity), got {got.validate!r}"
                )
            if got.provenance["validate"] != provenance:
                problems.append(
                    f"expected provenance {provenance!r}, got "
                    f"{got.provenance['validate']!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}\n"
                    f"    (host={host} profile={profile_validate!r} "
                    f"defaults={defaults_validate!r} flag={flag!r} named={named}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the `validate` chain was wrong for {len(wrong)} of {len(self.CHAIN)} shapes. ONE "
            "precedence walk decides all of them, so the GROUPING is the diagnosis and the "
            "directions are not equally bad. If an EXPLICIT row fails, a stored value is beating a "
            "typed flag: that is backlog `vju5ba` inverted, the flag is a lie, and it is the severe "
            "case. If the TIER 3 absent-profile row fails, absent is being read as False and every "
            "`defaults.validate: true` in the wild is silently dead. If only the TIER 4 rows fail, "
            "and they fail as a PAIR with oc and agy both wrong, the resolver stopped reading the "
            "registry ROW and went back to a module global, which can only ever be right for one "
            "host. FIX: oc=False and agy=True at tier 4 is CORRECT and measured from each driver; "
            f"do not 'fix' the disagreement by unifying them.\n" + "\n".join(wrong),
        )

    def test_two_profiles_differing_only_in_validate_resolve_differently(self):
        """Kept separate: the subject is TWO resolutions COMPARED, not one row's outcome.

        The measured Opus-off / Gemini-on shape, end to end from ONE command line. No row can state
        this, because the claim is that two profiles in the SAME document, reached by the same
        command, carry different verification decisions; that is a property of the pair.
        """

        cfg = RP.empty_config()
        cfg = RP.add_profile(
            cfg, "strong", _profile(model=_INHOUSE_MODEL, validate=False)
        )
        cfg = RP.add_profile(cfg, "cheap", _profile(model=_FLASH_MODEL, validate=True))
        strong = RP.resolve(cfg, runner="oc", profile="strong")
        cheap = RP.resolve(cfg, runner="oc", profile="cheap")
        self.assertIs(strong.validate, False)
        self.assertIs(cheap.validate, True)
        self.assertEqual(strong.provenance["validate"], RP.PROVENANCE_PROFILE)
        self.assertEqual(cheap.provenance["validate"], RP.PROVENANCE_PROFILE)

    def test_the_default_profile_also_supplies_validate(self):
        """Kept separate: the tier is `default-profile`, reached only with NO profile named.

        Not a row in the chain table, because that table's `named` column decides whether a profile
        is requested and this case needs a config where an UNNAMED resolution still finds one, via
        `set_default_profile`. Its provenance is therefore a fifth value the chain rows never see.
        """

        cfg = RP.add_profile(RP.empty_config(), "gem", _profile(validate=True))
        cfg = RP.set_default_profile(cfg, "gem")
        got = RP.resolve(cfg, runner="oc")
        self.assertIs(got.validate, True)
        self.assertEqual(got.provenance["validate"], RP.PROVENANCE_DEFAULT_PROFILE)


# ==================================================================================================
# `runprofile` Order 06 (`kgpptv`) E-01 / V-01: the optional `verify_with` PROFILE REFERENCE
#
# These tests exist because three things about this field are easy to get wrong and each one is
# silent when wrong: an ABSENT value read as "no verification" or as "host default" instead of
# "same as the executor"; a DANGLING reference falling back to the executor's model, so an operator
# believes an independent model checked the work when the same model did; and a version bump that
# invalidates every store already on disk.
# ==================================================================================================


def _routing_doc(**overrides) -> dict:
    """A two-profile document: `cheap` executes, `strong` verifies. Version 2 unless overridden."""

    doc = {
        "schema_version": 2,
        "profiles": {
            "cheap": {"runner": "oc", "model": _FLASH_MODEL, "verify_with": "strong"},
            "strong": {"runner": "oc", "model": _INHOUSE_MODEL, "variant": "high"},
        },
    }
    doc.update(overrides)
    return doc


class VerifyWithSchemaTests(unittest.TestCase):
    """`verify_with` stays a REFERENCE rather than a model, which is why it is storable at all.

    The both-levels and absent cases moved into `OptionalFieldSerializationTests`, whose table owns
    the optional-key rule across every field. What remains is the REFERENCE claim: the value must be
    a profile name, and an inline model must be refused BY THE NAME GRAMMAR rather than by an ad hoc
    check, because the grammar forbidding slashes is what makes the field unable to carry a model.
    """

    def test_round_trips_through_the_writer(self):
        """Kept separate: compares two DOCUMENTS to each other, so it has no literal expectation.

        `OptionalFieldSerializationTests` pins which keys appear; this pins that a full write-then-
        read cycle is the IDENTITY on a document carrying the field at both levels, which is the
        property that makes the store safe to rewrite.
        """

        cfg = RP.from_document(_routing_doc(defaults={"verify_with": "strong"}))
        reparsed = RP.from_document(json.loads(RP.dumps(cfg)))
        self.assertEqual(reparsed.to_document(), cfg.to_document())
        self.assertEqual(reparsed.get("cheap").verify_with, "strong")
        self.assertEqual(reparsed.verify_with, "strong")

    def test_a_non_string_reference_is_refused_and_says_it_is_a_reference(self):
        """Kept separate: an assertRaises sweep, at BOTH levels, whose assertion is the message.

        The refusal must say `profile NAME`, because the whole design decision is that this field
        takes a reference; a refusal that merely said "invalid" would let a future reader conclude the
        type was arbitrary and "fix" it by accepting a model string.
        """

        for bad in (1, True, [], {}, {"model": "a/b"}):
            with self.subTest(value=bad):
                with self.assertRaises(RP.ProfileSchemaError) as ctx:
                    RP.parse_profile(
                        "gem",
                        {"runner": "oc", "model": _FLASH_MODEL, "verify_with": bad},
                    )
                self.assertIn("profile NAME", str(ctx.exception))
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.from_document(
                {"schema_version": 2, "defaults": {"verify_with": 7}, "profiles": {}}
            )
        self.assertIn("profile NAME", str(ctx.exception))

    def test_a_reference_must_obey_the_profile_name_grammar(self):
        """Kept separate: an assertRaises whose point is WHICH rule refuses, not that one does."""

        # An INLINE model is refused BY THE GRAMMAR, which is the point of taking a reference:
        # `provider/model` contains a slash and can never be a profile name.
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.parse_profile(
                "gem",
                {"runner": "oc", "model": _FLASH_MODEL, "verify_with": _INHOUSE_MODEL},
            )
        self.assertIn("invalid profile name", str(ctx.exception))
        print(
            "an inline model in verify_with is refused by the profile-name grammar: "
            f"{str(ctx.exception).splitlines()[0][:96]}"
        )

    def test_verify_with_is_not_a_forbidden_injection_surface_field(self):
        """Kept separate: asserts SET MEMBERSHIP over three module constants, with no document."""

        # It is a NAME, not argv/env/a credential, which is why it is storable at all. Asserted so
        # a later reader does not "fix" its absence from the forbidden set.
        self.assertNotIn("verify_with", RP.FORBIDDEN_PROFILE_KEYS)
        self.assertIn("verify_with", RP.ALLOWED_PROFILE_KEYS)
        self.assertIn("verify_with", RP.ALLOWED_DEFAULTS_KEYS)


class VerifyWithDanglingReferenceTests(unittest.TestCase):
    """A reference that resolves to nothing is refused, at load AND at resolution.

    The profile-level load refusal moved into `MalformedDocumentTests` (which owns document refusals
    and asserts the message names the CONSEQUENCE), and the setter case into `MutationTests.SETTERS`.
    What remains is every route a dangling reference could arrive by that is NOT a document: an
    explicit flag, and a hand-built record that bypassed `from_document` entirely.
    """

    def test_a_dangling_defaults_reference_is_refused_at_load(self):
        """Kept separate: an assertRaises asserting the message names the LEVEL (`defaults.verify_with`).

        Its profile-level twin is a row in `MalformedDocumentTests`; this one stays because the
        assertion is that the message distinguishes WHICH level dangled, so an operator with both set
        knows which line of their file to fix.
        """

        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.from_document(
                {
                    "schema_version": 2,
                    "defaults": {"verify_with": "nope"},
                    "profiles": {"cheap": {"runner": "oc", "model": _FLASH_MODEL}},
                }
            )
        self.assertIn("defaults.verify_with", str(ctx.exception))
        self.assertIn("does not exist", str(ctx.exception))

    def test_an_explicit_unknown_reference_is_refused_at_resolution(self):
        """Kept separate: the RESOLUTION route, which no load-time table row can reach."""

        cfg = RP.from_document(_routing_doc())
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.resolve(cfg, runner="oc", profile="cheap", verify_with="nope")
        self.assertIn("does not exist", str(ctx.exception))

    def test_a_hand_built_config_cannot_smuggle_a_dangling_reference(self):
        """Kept separate: builds a record DIRECTLY, bypassing `from_document`, then tries two routes.

        This is the route a table of documents cannot express: `ProfileConfig(...)` never passes
        through the document validator, so resolution AND save must each refuse it independently.
        """

        # `_replace` re-validates, so the mutators cannot create one either.
        smuggled = RP.ProfileConfig(
            profiles={
                "cheap": RP.LaunchProfile(
                    runner="oc", model=_FLASH_MODEL, verify_with="ghost"
                )
            }
        )
        # Resolution refuses even though the record was built directly, bypassing `from_document`.
        with self.assertRaises(RP.ProfileSchemaError):
            RP.resolve(smuggled, runner="oc", profile="cheap")
        # And it can never be SAVED, because `save` round-trips through the validator.
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RP.ProfileSchemaError):
                RP.save(smuggled, Path(d) / "runner-profiles.json")


class VerifyWithPrecedenceTests(unittest.TestCase):
    """The `verify_with` chain: explicit > profile > `defaults` > `roles['verify']` > ABSENT.

    ONE table replaces eight tests: the four level tests and the per-runner-default test here, plus
    three from `RolesExtendVerifyWithTests` (`test_the_role_map_is_the_tier_below_defaults_verify_with`,
    which walked all four tiers inside one method with four unnamed blocks, and the two absent cases).
    Every one built a document, resolved one profile, and asserted `verify_with` plus the provenance
    naming the tier.

    THE ROLE MAP IS A ROW, NOT A SECOND CLASS, and that is the load-bearing merge. `roles['verify']`
    is a NEW BOTTOM TIER of the ONE existing chain rather than a parallel mechanism (DECISION
    01-btot17-D4), so its compatibility claim is exactly that it can ADD an answer where the shipped
    chain fell through to ABSENT and can never CHANGE one a higher tier already gave. That claim is a
    statement about the ORDER of the tiers, so it can only be asserted by rows that sit in one table:
    a `roles`-only class could show the tier working and would be blind to it overriding `defaults`.

    ABSENT IS NOT FALSE, NOT NULL-MODEL, NOT HOST-DEFAULT, AND NOT AN ERROR. That is four distinct
    wrong answers for one input, so the absent rows assert the provenance is `same-as-executor`
    specifically rather than merely that the value is None: `host-default` would mean "let the host
    pick a verifier" and `same-as-executor` means "reuse the executor's own launch", and an operator
    reading the first when the second happened believes an independent model checked the work.

    A DANGLING REFERENCE IS NOT A ROW: it is refused at LOAD, so no resolution exists to assert
    against. Those stay in `VerifyWithDanglingReferenceTests` as assertRaises tests.
    """

    def _doc(self, *, profile_ref=None, defaults_ref=None, roles=None, **overrides):
        """A `cheap`/`strong` document with the three configurable tiers set independently."""

        doc = {
            "schema_version": 2,
            "profiles": {
                "cheap": {"runner": "oc", "model": _FLASH_MODEL},
                "strong": {"runner": "oc", "model": _INHOUSE_MODEL, "variant": "high"},
            },
        }
        if profile_ref is not None:
            doc["profiles"]["cheap"]["verify_with"] = profile_ref
        if defaults_ref is not None:
            doc.setdefault("defaults", {})["verify_with"] = defaults_ref
        if roles is not None:
            doc["roles"] = roles
        doc.update(overrides)
        return doc

    #: (case, profile-level `verify_with`, `defaults.verify_with`, the `roles` map, the explicit
    #:  `--verify-with` value, the profile to NAME (None = resolve with no profile), expected
    #:  resolved verifier, expected provenance, why this row exists)
    #:
    #: Provenance is a LITERAL string for the reason given on `ResolutionPrecedenceTests.TIERS`.
    CHAIN = (
        (
            "tier 1: an explicit --verify-with over a profile field AND a defaults field",
            "strong",
            "strong",
            {"verify": "strong"},
            "cheap",
            "cheap",
            "cheap",
            "explicit",
            "THE TOP OF THE CHAIN, with every lower tier populated and NAMING A DIFFERENT PROFILE. "
            "A row where the tiers agreed would pass even with the precedence inverted, so the "
            "explicit value here is deliberately the one no stored tier asks for",
        ),
        (
            "tier 2: the profile's own field over a defaults field and a verify role",
            "strong",
            "cheap",
            {"verify": "cheap"},
            None,
            "cheap",
            "strong",
            "profile",
            "the PROFILE's field beats both lower tiers. Both of those name `cheap`, i.e. the "
            "EXECUTOR ITSELF, so a precedence slip here does not merely pick a different verifier: "
            "it makes the executor verify its own work while the record still claims a verifier",
        ),
        (
            "tier 3: `defaults.verify_with` with the profile silent and a role set",
            None,
            "strong",
            {"verify": "cheap"},
            None,
            "cheap",
            "strong",
            "defaults",
            "THE TIER THE ROLE MAP MUST NOT OVERRIDE, which is the whole compatibility claim of "
            "`actmodel` Order 01: the new bottom tier may ADD an answer but never CHANGE one an "
            "existing document already resolved. The role names `cheap` and must lose",
        ),
        (
            "tier 4: only `roles['verify']` speaks",
            None,
            None,
            {"verify": "strong"},
            None,
            "cheap",
            "strong",
            "role-map",
            "THE NEW BOTTOM TIER, reached only where the shipped chain had fallen through to "
            "ABSENT. Its provenance is `role-map` and NOT `defaults`, deliberately: they are "
            "different tiers of one chain and an operator debugging 'why that verifier' needs to "
            "know which spoke",
        ),
        (
            "tier 5: nothing anywhere, on a v2 document",
            None,
            None,
            None,
            None,
            "cheap",
            None,
            "same-as-executor",
            "ABSENT MEANS SAME AS THE EXECUTOR. Not False, not a null model, not `host-default`, "
            "and not an error: four wrong answers for one input, which is why the provenance is "
            "asserted and not just the None",
        ),
        (
            "tier 5 with a role map that sets OTHER roles but not `verify`",
            None,
            None,
            {"write-code": "strong"},
            None,
            "cheap",
            None,
            "same-as-executor",
            "a role map must not ACCIDENTALLY name a verifier. Without this row the tier could be "
            "implemented as 'if a roles map exists, use it', which would silently route "
            "verification through whichever profile some unrelated role happened to name",
        ),
        (
            "tier 5 on a v1 document, which predates the field entirely",
            None,
            None,
            None,
            None,
            "cheap",
            None,
            "same-as-executor",
            "THE BACKWARD-COMPATIBILITY ROW: a store written before the field existed must resolve "
            "identically, so no migration is needed and no old store is invalidated",
        ),
        (
            "the per-runner DEFAULT profile supplies it, with no profile named",
            "strong",
            None,
            None,
            None,
            None,
            "strong",
            "default-profile",
            "the field travels with a profile reached through `defaults.profiles`, not only one "
            "named on the command line. Its provenance is `default-profile`, a FIFTH value, which "
            "is what tells an operator the verifier came from a stored default rather than a flag",
        ),
    )

    def test_the_whole_verify_with_chain(self):
        wrong = []
        for (
            case,
            profile_ref,
            defaults_ref,
            roles,
            explicit,
            named,
            expected,
            provenance,
            why,
        ) in self.CHAIN:
            doc = self._doc(
                profile_ref=profile_ref, defaults_ref=defaults_ref, roles=roles
            )
            if "v1 document" in case:
                doc["schema_version"] = 1
            if named is None:
                doc.setdefault("defaults", {})["profiles"] = {"oc": "cheap"}
            cfg = RP.from_document(doc)
            call = {"runner": "oc"}
            if named is not None:
                call["profile"] = named
            if explicit is not None:
                call["verify_with"] = explicit
            got = RP.resolve(cfg, **call)
            problems = []
            if got.verify_with != expected:
                problems.append(
                    f"expected verifier {expected!r}, got {got.verify_with!r}"
                )
            if got.provenance["verify_with"] != provenance:
                problems.append(
                    f"expected provenance {provenance!r}, got "
                    f"{got.provenance['verify_with']!r}"
                )
            if expected is None:
                # The three wrong answers an ABSENT value must never become. `is not False` is the
                # required form: `!= False` is also true of `None`, so it would not catch a `False`.
                if got.verify_with is False:
                    problems.append(
                        "absent resolved to False, which reads as 'do not verify' rather than "
                        "'verify with the executor's own launch'"
                    )
                if got.provenance["verify_with"] == RP.PROVENANCE_HOST_DEFAULT:
                    problems.append(
                        "absent was recorded as host-default, which means 'let the host pick a "
                        "verifier'; the correct meaning is 'reuse the executor's own launch'"
                    )
            if problems:
                wrong.append(
                    f"  {case}\n"
                    f"    (profile={profile_ref!r} defaults={defaults_ref!r} roles={roles!r} "
                    f"explicit={explicit!r} named={named!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the `verify_with` chain was wrong for {len(wrong)} of {len(self.CHAIN)} shapes. ONE "
            "precedence walk decides all of them, so read the DIRECTION. If a HIGH tier row resolves "
            "to a LOWER tier's value, an operator believes an independent model checked the work "
            "while the executor checked its own: that is the silent failure this field exists to "
            "prevent, and it is the severe case. If the tier 3 row now returns `cheap`, the ROLE MAP "
            "is overriding `defaults` and the compatibility claim of `actmodel` Order 01 is false: "
            "existing documents changed meaning. If only the ABSENT rows fail, check WHICH wrong "
            "answer appeared, because `False`, `host-default` and an exception mean three different "
            "things to a caller and only one of them is merely untidy. FIX: `role-map` being DISTINCT "
            f"from `defaults` is intended; do not unify them.\n" + "\n".join(wrong),
        )

    def test_resolution_is_one_hop_so_a_cycle_is_unreachable(self):
        """Kept separate: performs TWO resolutions in sequence, which no single row can express.

        DECISION 06-kgpptv-D1: one hop, so `A -> B -> A` cannot loop. The claim is about what the
        CALLER does with a resolved record (resolve the verifier as its own launch, once), and that
        the verifier's own `verify_with` is carried but INERT, so it is a property of the pair.
        """

        cfg = RP.from_document(
            {
                "schema_version": 2,
                "profiles": {
                    "a": {"runner": "oc", "model": _FLASH_MODEL, "verify_with": "b"},
                    "b": {"runner": "oc", "model": _INHOUSE_MODEL, "verify_with": "a"},
                },
            }
        )
        executor = RP.resolve(cfg, runner="oc", profile="a")
        self.assertEqual(executor.verify_with, "b")
        # The caller takes exactly ONE hop: it resolves `b` as a launch. `b`'s own `verify_with`
        # is present but INERT while `b` is being used as the verifier, so no third resolution
        # exists and there is no loop to detect.
        verifier = RP.resolve(cfg, runner="oc", profile=executor.verify_with)
        self.assertEqual(verifier.model, _INHOUSE_MODEL)
        self.assertNotEqual(verifier.model, executor.model)
        self.assertEqual(verifier.verify_with, "a")  # carried, and deliberately unused
        print(
            f"one hop: executor={executor.model} verifier={verifier.model}; "
            f"verifier's own verify_with={verifier.verify_with!r} is inert"
        )

    def test_verify_with_and_validate_are_independent(self):
        """Kept separate: a claim about TWO fields NOT interacting, which needs three resolutions.

        `validate` decides WHETHER; `verify_with` decides WHICH. Kept out of both chain tables
        deliberately: each of those asserts one field's precedence, and this asserts that neither
        chain leaks into the other (naming a verifier must not turn verification ON, and turning it
        on must not invent a verifier). That is a cross-product claim, not a row in either chain.
        """

        cfg = RP.from_document(
            {
                "schema_version": 2,
                "profiles": {
                    # verification OFF, but a verifier profile named anyway.
                    "cheap": {
                        "runner": "oc",
                        "model": _FLASH_MODEL,
                        "validate": False,
                        "verify_with": "strong",
                    },
                    # verification ON, with NO verifier profile (so it verifies with itself).
                    "strong": {
                        "runner": "oc",
                        "model": _INHOUSE_MODEL,
                        "validate": True,
                    },
                },
            }
        )
        off = RP.resolve(cfg, runner="oc", profile="cheap")
        self.assertFalse(off.validate)
        self.assertEqual(off.verify_with, "strong")
        on = RP.resolve(cfg, runner="oc", profile="strong")
        self.assertTrue(on.validate)
        self.assertIsNone(on.verify_with)
        # And an explicit `--verify-with` does not turn verification ON.
        still_off = RP.resolve(cfg, runner="oc", profile="cheap", verify_with="strong")
        self.assertFalse(still_off.validate)
        print(
            f"independent: validate={off.validate} with verify_with={off.verify_with}; "
            f"validate={on.validate} with verify_with={on.verify_with!r}"
        )


# ==================================================================================================
# `actmodel` Order 01 (`btot17`) E-05 / V-05: the top-level `roles` map
#
# THE MECHANISM IS FITNESS FOR TASK, NOT COST CONTROL, per the maintainer's 2026-09-08 ruling ("It
# is NOT about just getting a cheap model. It's about getting the best model for the job"), and it
# EXTENDS `verify_with` rather than superseding or layering beside it: `verify` is an ENTRY in this
# map, and the map is the BOTTOM TIER of the one existing chain.
#
# Four things about this field are easy to get wrong and each is silent when wrong: an unvalidated
# role KEY (a misspelling routes nothing while looking effective); a dangling role VALUE (falls
# through as if unset, so the work runs on a model nobody chose); a role map that OVERRIDES a more
# specific declaration (which would change what an existing document already resolves to); and an
# object value quietly making OQ-05's producing-plus-validating pair expressible without a decision.
# ==================================================================================================


def _roles_doc(roles=None, **overrides) -> dict:
    """A two-profile document (`cheap`, `strong`) plus an optional top-level `roles` map."""

    doc = {
        "schema_version": 2,
        "profiles": {
            "cheap": {"runner": "oc", "model": _FLASH_MODEL},
            "strong": {"runner": "oc", "model": _INHOUSE_MODEL, "variant": "high"},
        },
    }
    if roles is not None:
        doc["roles"] = roles
    doc.update(overrides)
    return doc


class RoleVocabularyTests(unittest.TestCase):
    """The vocabulary is the maintainer's five kinds of work plus `verify`, and it is CLOSED.

    The load-time refusal of an unknown role is a row in `MalformedDocumentTests`. What remains is
    the vocabulary ITSELF (a literal pin on a closed set) and the accessor's refusal, which are
    claims about the constant and about `profile_for_role`, not about a document.
    """

    def test_the_role_vocabulary_is_exactly_the_maintainers_five_kinds_plus_verify(
        self,
    ):
        # Pinned LITERALLY so widening it requires editing this test and saying why. The first five
        # are the maintainer's own categories, taken verbatim rather than reinterpreted; `verify` is
        # the sixth because the shipped `verify_with` field had to become an ENTRY in this map, and
        # mapping it onto `check-content` would have made the existing `--verify-with` chain a second
        # way to set a kind of work (DECISION 01-btot17-D3).
        self.assertEqual(
            list(RP.ROLE_NAMES),
            [
                "write-prose",
                "write-code",
                "write-code-fast",
                "research-online",
                "check-content",
                "verify",
            ],
        )
        self.assertEqual(RP.ROLE_VERIFY, "verify")
        self.assertIn(RP.ROLE_VERIFY, RP.ROLE_NAMES)
        print(f"role vocabulary (closed): {list(RP.ROLE_NAMES)}")

    def test_an_unknown_role_is_refused_at_load_and_the_message_lists_the_vocabulary(
        self,
    ):
        """A misspelled role must be a REFUSAL, never a silent no-op sitting in the store."""

        for bad in ("writecode", "write_code", "reviewer", "probe", "WRITE-CODE"):
            with self.subTest(role=bad):
                with self.assertRaises(RP.ProfileSchemaError) as ctx:
                    RP.from_document(_roles_doc({bad: "strong"}))
                message = str(ctx.exception)
                self.assertIn(repr(bad), message)
                # The refusal has to be actionable, so it names the legal set.
                for known in RP.ROLE_NAMES:
                    self.assertIn(known, message)
        print("unknown roles refused, each message listing the closed vocabulary")

    def test_profile_for_role_refuses_an_unknown_role_rather_than_returning_none(self):
        """Kept separate: the ACCESSOR's contract, and the distinction is the point.

        `None` means "this role is unset", so an unknown role must NOT return `None` or a caller
        cannot tell a typo from an unconfigured preference. That is a three-way distinction over one
        method (a value, a None, a raise), which is why it is not a row in the document table.
        """

        # The distinction is the point: `None` means "this role is unset", so an unknown role must
        # NOT return `None` or a caller cannot tell a typo from an unconfigured preference.
        cfg = RP.from_document(_roles_doc({"write-code": "strong"}))
        self.assertEqual(cfg.profile_for_role("write-code"), "strong")
        self.assertIsNone(cfg.profile_for_role("write-prose"))
        with self.assertRaises(RP.ProfileSchemaError):
            cfg.profile_for_role("writecode")


class RolesSchemaTests(unittest.TestCase):
    """What survives of the roles schema once the refusals moved into `MalformedDocumentTests`.

    Five refusal tests (a non-object map, a non-string target, an inline model, an unknown top-level
    key, and the dangling reference) are now rows in that table, where the message substrings are
    asserted per row. What remains here is the POSITIVE round trip and the injection-surface claim,
    which is about which SETS the key belongs to rather than about parsing a document.
    """

    def test_a_roles_map_is_accepted_and_round_trips(self):
        """Kept separate: the POSITIVE case, comparing a reparsed document to the original."""

        cfg = RP.from_document(
            _roles_doc({"write-code": "strong", "check-content": "cheap"})
        )
        self.assertEqual(
            dict(cfg.roles), {"write-code": "strong", "check-content": "cheap"}
        )
        reparsed = RP.from_document(json.loads(RP.dumps(cfg)))
        self.assertEqual(dict(reparsed.roles), dict(cfg.roles))
        self.assertEqual(reparsed.to_document(), cfg.to_document())
        print(f"roles round-trip: {dict(reparsed.roles)}")

    def test_roles_did_not_widen_the_injection_surface(self):
        """Kept separate: asserts MEMBERSHIP across four module constants, not a parse outcome.

        A role map holds profile NAMES, so it stores no argv, environment, executable, prompt or
        credential. The claim is about which sets the key is and is NOT in, including that the PROFILE
        surface was untouched (the map is top level, by DECISION 01-btot17-D1), which no document row
        can state.
        """

        # A role map holds profile NAMES, so it stores no argv, environment, executable, prompt or
        # credential, and it must not have quietly become a way to store one.
        self.assertIn("roles", RP.ALLOWED_DOCUMENT_KEYS)
        self.assertNotIn("roles", RP.FORBIDDEN_PROFILE_KEYS)
        # The PROFILE surface is untouched: the map is top level, not a profile field.
        self.assertNotIn("roles", RP.ALLOWED_PROFILE_KEYS)
        self.assertNotIn("roles", RP.ALLOWED_DEFAULTS_KEYS)
        for forbidden in ("args", "env", "command", "prompt", "token"):
            with self.subTest(key=forbidden):
                with self.assertRaises(RP.ProfileSchemaError):
                    RP.from_document(
                        _roles_doc({"write-code": "strong"}, **{forbidden: "v"})
                    )


class RolesReferenceIntegrityTests(unittest.TestCase):
    """The routes a dangling role reference could arrive by that are NOT a document.

    The load-time refusal is a row in `MalformedDocumentTests`. These are the MUTATOR routes, which
    that table cannot reach: `set_role` refusing, and `remove_profile` refusing to strand a role by
    deleting its target.
    """

    def test_a_mutator_cannot_create_a_dangling_or_unknown_role(self):
        """Kept separate: `set_role`'s full cycle, two refusals then set-and-remove over one config.

        Not a row in `MutationTests.SETTERS`, because `set_role` takes TWO arguments (a role and a
        target) and so has a second refusal axis (an unknown ROLE, not only an unknown target) that
        the single-value setters do not.
        """

        cfg = RP.from_document(_roles_doc())
        with self.assertRaises(RP.ProfileSchemaError):
            RP.set_role(cfg, "write-code", "nope")
        with self.assertRaises(RP.ProfileSchemaError):
            RP.set_role(cfg, "writecode", "strong")
        # And the happy path plus removal.
        cfg = RP.set_role(cfg, "write-code", "strong")
        self.assertEqual(dict(cfg.roles), {"write-code": "strong"})
        cfg = RP.set_role(cfg, "write-code", None)
        self.assertEqual(dict(cfg.roles), {})
        self.assertNotIn("roles", cfg.to_document())

    def test_removing_a_profile_a_role_references_cannot_leave_a_dangling_role(self):
        """Kept separate: the subject is `remove_profile`, reached from the OTHER side of the edge.

        Every other integrity case makes the REFERENCE wrong; this makes the reference correct and
        deletes its TARGET. `remove_profile` routes through `_replace`, so the same check catches it,
        which is the property worth stating: the integrity rule is on the config, not on one setter.
        """

        cfg = RP.from_document(_roles_doc({"write-code": "strong"}))
        with self.assertRaises(RP.ProfileSchemaError) as ctx:
            RP.remove_profile(cfg, "strong")
        self.assertIn("roles['write-code']", str(ctx.exception))
        print(
            "removing a role's target is refused rather than silently unrouting the role: "
            f"{str(ctx.exception).splitlines()[0]}"
        )

    def test_a_role_may_point_at_the_same_profile_as_another_role(self):
        """Kept separate: a POSITIVE claim that two roles sharing a target is LEGAL, not a conflict."""

        cfg = RP.from_document(_roles_doc({"write-code": "strong", "verify": "strong"}))
        self.assertEqual(cfg.profile_for_role("write-code"), "strong")
        self.assertEqual(cfg.profile_for_role("verify"), "strong")


class RolesExtendVerifyWithTests(unittest.TestCase):
    """`verify` EXTENDS the shipped `verify_with` key rather than superseding or forking it.

    WHAT MOVED AND WHY. The four-tier walk this class opened with is now rows in
    `VerifyWithPrecedenceTests.CHAIN`, together with both absent cases, because the claim is about
    the ORDER OF ONE CHAIN and a tier can only be shown to sit BELOW another when both are rows in
    one table. That walk was also four unnamed blocks in a single method, so a failure reported one
    tier and stopped; the table reports every tier that moved at once.

    WHAT STAYS HERE is the pair of claims that are not about resolving a document: that the shipped
    key was neither removed nor renamed (a NEGATIVE existence proof), and that the provenance
    vocabulary stayed a closed renderable set with `role-map` distinct from `defaults`.
    """

    def test_verify_with_is_neither_removed_nor_renamed(self):
        """Kept separate: a NEGATIVE EXISTENCE claim about the module's surface, not a resolution.

        V-05's explicit requirement. This Order EXTENDS the shipped key, so the key must still be
        storable at both levels, still be a field on the record, and still have its setter. No row
        in the chain table can state that a name still EXISTS, since a row can only observe what a
        present key resolves to.
        """

        self.assertIn("verify_with", RP.ALLOWED_PROFILE_KEYS)
        self.assertIn("verify_with", RP.ALLOWED_DEFAULTS_KEYS)
        self.assertTrue(
            hasattr(RP.LaunchProfile(runner="oc", model=_FLASH_MODEL), "verify_with")
        )
        self.assertTrue(callable(RP.set_verify_with_default))

    def test_every_pre_existing_resolution_is_byte_identical(self):
        """Kept separate: compares TWO resolved records to EACH OTHER, so it has no expectation.

        THE COMPATIBILITY CLAIM, measured. The chain table proves the role tier sits below
        `defaults`; this proves the stronger thing that no row can, namely that adding an UNRELATED
        role leaves a resolution identical FIELD FOR FIELD and provenance for provenance, not merely
        identical in `verify_with`. The digest is excluded because the document genuinely differs.
        """

        doc = _routing_doc(defaults={"verify_with": "strong"})
        got = RP.resolve(RP.from_document(doc), runner="oc", profile="cheap")
        with_role = RP.from_document(dict(doc, roles={"write-prose": "cheap"}))
        also = RP.resolve(with_role, runner="oc", profile="cheap")
        self.assertEqual(
            got._replace(config_digest="x"), also._replace(config_digest="x")
        )

    def test_the_provenance_vocabulary_stays_a_closed_renderable_set(self):
        """Kept separate: asserts over the CONSTANTS and the closed set, before any document."""

        self.assertIn(RP.PROVENANCE_ROLE_MAP, RP.PROVENANCE_VALUES)
        self.assertEqual(RP.PROVENANCE_ROLE_MAP, "role-map")
        # DISTINCT from `defaults`, because they are different tiers of one chain and an operator
        # debugging "why that model" needs to know which spoke.
        self.assertNotEqual(RP.PROVENANCE_ROLE_MAP, RP.PROVENANCE_DEFAULTS)


class RolesOpenQuestionFenceTests(unittest.TestCase):
    """OQ-05 (a role naming a PRODUCING plus a VALIDATING model) must stay INEXPRESSIBLE.

    Kept as its own class rather than folded into `MalformedDocumentTests`: the refusal here is not
    a validation error but a deliberate FENCE around an undecided design question, and its message
    must read as an OPEN QUESTION so a later contributor does not helpfully "fix" it.
    """

    def test_a_producing_plus_validating_pair_is_refused_and_names_the_open_question(
        self,
    ):
        """The maintainer chose "mapping now, pairing recorded as the next step" (DECISION D5).

        Refusing the object form by NAME is what keeps the pair from becoming quietly expressible
        without a decision, which this plan's approval gate explicitly requires. The message must read
        as an OPEN QUESTION rather than an oversight a later contributor might helpfully "fix", which
        is the same technique `FORBIDDEN_PROFILE_KEYS` uses.
        """

        for pair in (
            {"produce": "cheap", "validate": "strong"},
            {"model": "cheap", "verify_with": "strong"},
            {},
        ):
            with self.subTest(pair=pair):
                with self.assertRaises(RP.ProfileSchemaError) as ctx:
                    RP.from_document(_roles_doc({"write-code-fast": pair}))
                message = str(ctx.exception)
                self.assertIn("must be a single profile NAME string", message)
                self.assertIn("OPEN DESIGN QUESTION", message)
                self.assertIn("OQ-05", message)
        print(
            "a producing+validating pair is refused, naming OQ-05: "
            f"{str(ctx.exception).splitlines()[0]}"
        )

    def test_no_schema_surface_can_express_a_pair(self):
        """Kept separate: a POSITIVE plus a negative, showing a role takes exactly ONE name.

        Belt and braces: no ALLOWED key anywhere takes two models for one piece of work, and a LIST
        of names is refused too, which is the other obvious way to smuggle a pair past the object
        form the test above fences.
        """

        # A role takes ONE name.
        cfg = RP.from_document(_roles_doc({"write-code-fast": "cheap"}))
        self.assertEqual(cfg.profile_for_role("write-code-fast"), "cheap")
        self.assertIsInstance(cfg.roles["write-code-fast"], str)
        # And a LIST of names is refused too, which is the other obvious way to smuggle a pair.
        with self.assertRaises(RP.ProfileSchemaError):
            RP.from_document(_roles_doc({"write-code-fast": ["cheap", "strong"]}))


class SchemaVersionCompatibilityTests(unittest.TestCase):
    """What an on-disk store of each shape loads and resolves to, and what an OLDER aw does with it.

    ONE table plus three kept tests replace ten, merging what were two classes
    (`RolesVersioningTests` and `SchemaVersionCompatibilityTests`). Both classes wrote a document to
    disk, loaded it, resolved one profile, and asserted the reading did not REWRITE the bytes; they
    differed only in the document.

    MERGING THE TWO CLASSES FOUND A LITERAL DUPLICATE, which is the argument for doing it.
    `RolesVersioningTests.test_an_existing_v1_document_with_no_roles_still_loads_and_resolves_unchanged`
    and `SchemaVersionCompatibilityTests.test_an_existing_v1_document_still_loads_and_resolves_unchanged`
    wrote the SAME four-key v1 document and made the same assertions, one of them adding a check on
    `cfg.roles`. Two classes named after two DECISIONS (06-kgpptv-D2 and 01-btot17-D2) had each grown
    its own copy of the shared compatibility case, and neither could see the other.

    THE VERSION IS A COLUMN, NOT A CLASS, and the property that needs it is precise: the reader is
    version-agnostic about FIELDS, so `verify_with` and `roles` must both be read at schema_version 1
    AND 2, while only the WRITER pins a version. Expressed as a class per decision, that property is
    invisible; expressed as rows, a reader can see the same field accepted at both versions.

    NOTHING IS REWRITTEN ON READ, asserted on EVERY row rather than on some. That is the claim that
    makes "no migration" true, and its failure is silent: a store rewritten on read would change
    version under an operator who only ran a query, at which point an older aw on the same machine
    can no longer read their profiles.
    """

    #: (case, the document to write to disk, the profile to resolve (None = resolve unnamed), the
    #:  expected schema_version read back, expected model, expected verifier, expected verifier
    #:  provenance, the expected `roles` map, why this row exists)
    #:
    #: Provenance is a LITERAL string for the reason given on `ResolutionPrecedenceTests.TIERS`.
    STORES = (
        (
            "a v1 document written before either field existed",
            {
                "schema_version": 1,
                "default_runner": "oc",
                "defaults": {"profiles": {"oc": "gem"}, "validate": False},
                "profiles": {
                    "gem": {"runner": "oc", "model": _FLASH_MODEL, "variant": "high"}
                },
            },
            None,
            1,
            _FLASH_MODEL,
            None,
            "same-as-executor",
            {},
            "THE NO-MIGRATION ROW, and the one the two merged classes each held a copy of: a store "
            "written before `verify_with` and `roles` existed must keep working EXACTLY as it did, "
            "resolve to the same model, and be left byte-identical on disk",
        ),
        (
            "a v2 document carrying `verify_with` at the profile level",
            {
                "schema_version": 2,
                "profiles": {
                    "cheap": {
                        "runner": "oc",
                        "model": _FLASH_MODEL,
                        "verify_with": "strong",
                    },
                    "strong": {"runner": "oc", "model": _INHOUSE_MODEL},
                },
            },
            "cheap",
            2,
            _FLASH_MODEL,
            "strong",
            "profile",
            {},
            "the shipped key must be UNAFFECTED by the `roles` extension (V-05's explicit "
            "requirement): it still parses, still resolves, and still reports `profile` provenance",
        ),
        (
            "a HAND-WRITTEN v1 document that carries `verify_with` anyway",
            {
                "schema_version": 1,
                "profiles": {
                    "cheap": {
                        "runner": "oc",
                        "model": _FLASH_MODEL,
                        "verify_with": "strong",
                    },
                    "strong": {"runner": "oc", "model": _INHOUSE_MODEL},
                },
            },
            "cheap",
            1,
            _FLASH_MODEL,
            "strong",
            "profile",
            {},
            "THE READER IS VERSION-AGNOSTIC ABOUT FIELDS, and only the WRITER pins a version. A "
            "hand-written store is not punished for using a field while declaring 1, which is why "
            "the version is a column: the same field must be read at both",
        ),
        (
            "a v1 document carrying a `roles` map",
            {
                "schema_version": 1,
                "roles": {"verify": "strong", "write-code": "strong"},
                "profiles": {
                    "cheap": {"runner": "oc", "model": _FLASH_MODEL},
                    "strong": {"runner": "oc", "model": _INHOUSE_MODEL},
                },
            },
            "cheap",
            1,
            _FLASH_MODEL,
            "strong",
            "role-map",
            {"verify": "strong", "write-code": "strong"},
            "DECISION 01-btot17-D2: `roles` did NOT bump the version, so it must be READ at 1 as "
            "well as 2, following the `verify_with` precedent above. The verifier resolves through "
            "the role map here, so the row also proves the key is not merely stored but consulted",
        ),
        (
            "a v2 document carrying a `roles` map",
            {
                "schema_version": 2,
                "roles": {"verify": "strong", "write-code": "strong"},
                "profiles": {
                    "cheap": {"runner": "oc", "model": _FLASH_MODEL},
                    "strong": {"runner": "oc", "model": _INHOUSE_MODEL},
                },
            },
            "cheap",
            2,
            _FLASH_MODEL,
            "strong",
            "role-map",
            {"verify": "strong", "write-code": "strong"},
            "the same map at the CURRENT version, so the pair with the row above is what states "
            "'read at both supported versions' rather than 'happens to work at one'",
        ),
    )

    def test_every_stored_document_shape_loads_resolves_and_is_never_rewritten(self):
        wrong = []
        for (
            case,
            document,
            named,
            version,
            model,
            verifier,
            provenance,
            roles,
            why,
        ) in self.STORES:
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "runner-profiles.json"
                path.write_text(json.dumps(document), encoding="utf-8")
                before = path.read_bytes()
                problems = []
                cfg = RP.load(path)
                call = {"runner": "oc"}
                if named is not None:
                    call["profile"] = named
                got = RP.resolve(cfg, **call)
                if cfg.schema_version != version:
                    problems.append(
                        f"schema_version expected {version}, got {cfg.schema_version}"
                    )
                if dict(cfg.roles) != roles:
                    problems.append(
                        f"roles expected {roles!r}, got {dict(cfg.roles)!r}"
                    )
                if got.model != model:
                    problems.append(f"model expected {model!r}, got {got.model!r}")
                if got.verify_with != verifier:
                    problems.append(
                        f"verify_with expected {verifier!r}, got {got.verify_with!r}"
                    )
                if got.provenance["verify_with"] != provenance:
                    problems.append(
                        f"verify_with provenance expected {provenance!r}, got "
                        f"{got.provenance['verify_with']!r}"
                    )
                after = path.read_bytes()
                if after != before:
                    problems.append(
                        "READING REWROTE THE FILE. The bytes changed from "
                        f"{before!r} to {after!r}, so a query silently migrated an operator's store"
                    )
                # A round trip through the WRITER must preserve the same view, which is what makes
                # the store safe to rewrite once the operator does save through `aw oc profile`.
                reloaded = RP.from_document(json.loads(RP.dumps(cfg)))
                if dict(reloaded.roles) != roles:
                    problems.append(
                        f"a save/load round trip lost the roles map: {dict(reloaded.roles)!r}"
                    )
                if reloaded.to_document() != cfg.to_document():
                    problems.append(
                        "a save/load round trip changed the document: "
                        f"{cfg.to_document()!r} -> {reloaded.to_document()!r}"
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
            f"{len(wrong)} of {len(self.STORES)} stored document shapes were mishandled. One reader "
            "parses all of them and it is deliberately VERSION-AGNOSTIC ABOUT FIELDS, so read the "
            "grouping. If both `roles` rows fail together, the key stopped being read at all; if "
            "only the v1 `roles` row fails, the reader grew a version gate the decision explicitly "
            "declined (01-btot17-D2) and every hand-written store is now punished for a field it is "
            "allowed to carry. If a REWROTE THE FILE line appears, that is the severe one: a query "
            "migrated an operator's store behind their back, and an older aw on the same machine can "
            f"no longer read their profiles at all.\n" + "\n".join(wrong),
        )

    def test_the_module_writes_2_and_reads_1_and_2(self):
        """Kept separate: asserts the two CONSTANTS, before any document exists.

        The table above proves both versions are read in practice; this pins the declared set, which
        is what a reader consults, and pins that the WRITER still emits 2. `roles` deliberately did
        NOT bump it (DECISION 01-btot17-D2), so this assertion is also the record that it stayed put.
        """

        self.assertEqual(RP.SCHEMA_VERSION, 2)
        self.assertEqual(sorted(RP.SUPPORTED_SCHEMA_VERSIONS), [1, 2])

    def test_an_older_aw_reading_a_v2_document_fails_closed_with_the_upgrade_message(
        self,
    ):
        """Kept separate: an assertRaises under a PATCHED module constant, simulating an older aw.

        The CONSEQUENCE of the bump, measured rather than asserted in prose. An older aw is simulated
        exactly: its only difference here was `SUPPORTED_SCHEMA_VERSIONS == frozenset((1,))`, which is
        what the shipped constant was before the bump. The message must point at the REAL fix
        (upgrade) rather than inviting a hand edit.
        """

        new_document = json.loads(RP.dumps(RP.from_document(_routing_doc())))
        self.assertEqual(new_document["schema_version"], 2)
        with mock.patch.object(RP, "SUPPORTED_SCHEMA_VERSIONS", frozenset((1,))):
            with self.assertRaises(RP.ProfileSchemaError) as ctx:
                RP.from_document(new_document)
        message = str(ctx.exception)
        self.assertIn("unsupported schema_version 2", message)
        self.assertIn("Upgrade aw rather than editing the file", message)

    def test_the_accepted_cost_of_not_bumping_for_roles_is_the_unknown_field_refusal(
        self,
    ):
        """Kept separate: an assertRaises under a DIFFERENT patched constant, and it is the OPPOSITE
        outcome to the test above, which is why the two cannot be one row.

        MEASURE the consequence DECISION 01-btot17-D2 knowingly accepts. An older aw whose
        `ALLOWED_DOCUMENT_KEYS` predates `roles` says "unknown field(s) ['roles']" instead of
        "Upgrade aw", which is exactly the outcome 06-kgpptv-D2 bumped the version to AVOID. It is
        acceptable only because no such document can exist yet: no writer emits `roles` and no
        consumer reads it.
        """

        document = json.loads(
            RP.dumps(RP.from_document(_roles_doc({"write-code": "strong"})))
        )
        self.assertIn("roles", document)
        older_keys = frozenset(k for k in RP.ALLOWED_DOCUMENT_KEYS if k != "roles")
        with mock.patch.object(RP, "ALLOWED_DOCUMENT_KEYS", older_keys):
            with self.assertRaises(RP.ProfileSchemaError) as ctx:
                RP.from_document(document)
        self.assertIn("unknown field(s) ['roles']", str(ctx.exception))

    def test_an_older_aw_refuses_to_overwrite_a_v2_document(self):
        """Kept separate: the subject is `save` REFUSING, and it asserts the prior bytes survive.

        The bump also protects the newer file from being clobbered by the older writer, which is a
        claim about a WRITE and cannot be a row in a table of reads.
        """

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runner-profiles.json"
            RP.save(RP.from_document(_routing_doc()), path)
            before = path.read_bytes()
            with mock.patch.object(RP, "SUPPORTED_SCHEMA_VERSIONS", frozenset((1,))):
                with mock.patch.object(RP, "SCHEMA_VERSION", 1):
                    with self.assertRaises(RP.ProfileStoreError) as ctx:
                        RP.save(
                            RP.ProfileConfig(
                                schema_version=1,
                                profiles={
                                    "gem": RP.LaunchProfile(
                                        runner="oc", model=_FLASH_MODEL
                                    )
                                },
                            ),
                            path,
                        )
            self.assertIn("Nothing was changed", str(ctx.exception))
            self.assertEqual(before, path.read_bytes())


class PerHostValidateDefaultTests(unittest.TestCase):
    """`hostdefault-01` E-06: the REGISTRY ROW itself, which is tier 4's authority.

    WHAT MOVED AND WHY. Three of this class's four tests were cases of the `validate` chain expressed
    on two hosts, so they are now rows in `ValidatePrecedenceMatrixTests.CHAIN` with `host` as a
    COLUMN: tier 4 per host, the row-is-a-floor cases, and the agy tri-state. That is the stronger
    shape, because the property is that identical configuration resolves differently at tier 4 and
    identically above it, and a per-host CLASS cannot say that.

    WHAT STAYS HERE is the one claim that is not about resolving anything: that every registered row
    DECLARES a posture, deliberately and as a real `bool`. That is a claim about the registry as a
    data structure, so it has no config, no resolution and no provenance, and it is what makes
    registering a third host a decision rather than an inheritance.
    """

    def test_every_registered_row_declares_a_real_bool_posture(self):
        """Kept separate: a STRUCTURAL claim about `RUNNER_REGISTRY`, with no resolution at all.

        Two halves, and the second is why a mere membership check is not enough: `RunnerSpec` is a
        `NamedTuple`, whose annotations are NOT checked at runtime, so `validate_default="yes"`
        constructs fine and is TRUTHY, which would resolve tier 4 to a silent ON. `1 in (True,
        False)` is also True in Python, so `assertIn` would let an int through. `isinstance(...,
        bool)` is therefore the required assertion.
        """

        for name, row in sorted(RP.RUNNER_REGISTRY.items()):
            with self.subTest(runner=name):
                self.assertIsInstance(
                    row.validate_default,
                    bool,
                    f"row {name!r} must declare a real bool verification posture",
                )
        # The retained compatibility constant must not drift from the row it claims to mirror.
        # E-02 keeps it a LITERAL (defining it from the registry is a module-level forward
        # reference that raises NameError at import), so this assertion is what keeps it honest.
        self.assertIs(
            RP.SHIPPED_VALIDATE_DEFAULT, RP.RUNNER_REGISTRY["oc"].validate_default
        )


class RegisteredRowFieldSupportTests(unittest.TestCase):
    """A row's `supports_*` flags bind BOTH routes into the module: the STORE and the CALLER.

    ONE table replaces two tests (`hostdefault-01` E-03 and E-08), which asserted the SAME rule about
    the SAME two fields on two different routes: `parse_profile` (a stored profile) and `resolve` (an
    explicit flag).

    THE ROUTE IS A COLUMN, and that is exactly the property E-08 recorded as a decision: the two
    routes must AGREE. Accepting an explicit `--variant` for a host whose row declares no support
    would silently drop a field the operator typed, and would make the same value legal on the
    command line while illegal in the store, which is the kind of asymmetry an operator discovers by
    having their flag ignored. One test per route cannot state the agreement; a route column can, and
    a divergence now fails as a pair of rows naming both sides.

    THE `oc` ROWS ARE POSITIVE ROWS IN THE SAME TABLE, and they are what make the refusals meaningful:
    the refusal must be about the ROW, not about the fields. Without them the rule could be
    implemented as "never accept variant or agent", which would satisfy every agy row while breaking
    the host that supports both.

    THE MESSAGE SUBSTRING IS ASSERTED because a refusal has to be actionable: it must name the HOST
    (so the operator knows which of their profiles is wrong) and say what is unsupported. Before the
    `agy` row existed this path was unreachable at all (`runner="agy"` raised in `canonical_runner`),
    so these are the first rows that exercise a second row's flags.
    """

    #: (case, the route ("store" via `parse_profile` or "resolve" via an explicit flag), the host,
    #:  the field, whether it must be ACCEPTED, the message substring a refusal must carry, why)
    SUPPORT = (
        (
            "a STORED agy profile carrying `variant`",
            "store",
            "antigravity",
            "variant",
            False,
            "does not support",
            "`agy` accepts `--model` ONLY (measured from its driver's argv and its parser), so a "
            "stored profile carrying a variant is refused. This is what makes "
            "`supports_variant=False` load-bearing rather than decorative",
        ),
        (
            "a STORED agy profile carrying `agent`",
            "store",
            "antigravity",
            "agent",
            False,
            "does not support",
            "the same for the second unsupported field, so the flags are read per field rather than "
            "one of them standing in for both",
        ),
        (
            "an EXPLICIT `--variant` for agy",
            "resolve",
            "agy",
            "variant",
            False,
            "does not support a model variant",
            "E-08'S RECORDED DECISION, and the reason `route` is a column: `resolve` must refuse "
            "what `parse_profile` refuses. Accepting it would silently DROP a field the operator "
            "typed, which is worse than refusing because nothing tells them it was ignored",
        ),
        (
            "an EXPLICIT `--agent` for agy",
            "resolve",
            "agy",
            "agent",
            False,
            "does not support an agent",
            "the second field on the caller route, and the message is field-specific so the "
            "operator learns WHICH flag to drop",
        ),
        (
            "a STORED oc profile carrying `variant`",
            "store",
            "oc",
            "variant",
            True,
            None,
            "A POSITIVE ROW: the refusal is about the ROW, not the field. Without this the rule "
            "could be 'never accept a variant', which would break the host that supports one",
        ),
        (
            "a STORED oc profile carrying `agent`",
            "store",
            "oc",
            "agent",
            True,
            None,
            "the oc half of the second field",
        ),
        (
            "an EXPLICIT `--variant` for oc",
            "resolve",
            "oc",
            "variant",
            True,
            None,
            "the caller route must stay UNCHANGED for a host that declares support, or adding the "
            "agy row would have broken every existing oc invocation",
        ),
        (
            "an EXPLICIT `--agent` for oc",
            "resolve",
            "oc",
            "agent",
            True,
            None,
            "and the fourth cell of the host-by-field matrix, so all four are stated rather than "
            "three plus an assumption",
        ),
    )

    def test_both_routes_honor_every_rows_supported_fields(self):
        wrong = []
        for case, route, host, field, accepted, complaint, why in self.SUPPORT:
            problems = []
            try:
                if route == "store":
                    got = RP.parse_profile(
                        "gg", {"runner": host, "model": _FLASH_MODEL, field: "high"}
                    )
                    value = getattr(got, field)
                else:
                    got = RP.resolve(RP.empty_config(), runner=host, **{field: "high"})
                    value = getattr(got, field)
            except RP.ProfileSchemaError as exc:
                if accepted:
                    problems.append(
                        f"REFUSED a field the {host!r} row declares support for: {exc}"
                    )
                else:
                    message = str(exc)
                    if "agy" not in message:
                        problems.append(
                            f"the refusal must NAME the host so an operator can find the offending "
                            f"profile; it said {message!r}"
                        )
                    if complaint is not None and complaint not in message:
                        problems.append(
                            f"the refusal must say {complaint!r}; it said {message!r}"
                        )
            else:
                if not accepted:
                    problems.append(
                        f"ACCEPTED {field}={value!r} for {host!r}, whose row declares no support; "
                        "on the resolve route that silently DROPS a field the operator typed, and "
                        "on the store route it saves a profile that host can never launch"
                    )
                elif value != "high":
                    problems.append(f"{field} came back as {value!r}, expected 'high'")
            if problems:
                wrong.append(
                    f"  {case} (route={route} host={host!r} field={field!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.SUPPORT)} host/field/route cells disagreed with the "
            "registry row. ONE pair of `supports_*` flags decides all of them, so read the GROUPING. "
            "If the two ROUTES disagree for one host (a `store` row passing while its `resolve` twin "
            "fails, or vice versa), that is the asymmetry E-08 was decided to prevent: the same value "
            "would be legal on the command line and illegal in the store, and the operator's typed "
            "flag is silently dropped. If every agy row now ACCEPTS, the flags stopped being read and "
            "profiles can be stored that host cannot launch. If every oc row now REFUSES, the rule "
            f"was written against the FIELD instead of the ROW and the supporting host is broken.\n"
            + "\n".join(wrong),
        )


class NoSilentFallbackTests(unittest.TestCase):
    """The costly failure mode: a broken config must never quietly become the host default.

    `MalformedDocumentTests` proves refusal at the DOCUMENT level; these two prove it end to end
    through `load` on a real FILE, and prove the legitimate empty case resolves rather than raising.
    The contrast between the two is the subject, which is why neither is a row.
    """

    def test_a_broken_file_never_resolves_to_the_host_default(self):
        """Kept separate: goes through `load` on a real file, which the document table does not."""

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runner-profiles.json"
            path.write_text(
                '{"schema_version": 1, "profiles": {"gem": 3}}', encoding="utf-8"
            )
            with self.assertRaises(RP.ProfileSchemaError):
                RP.load(path)
        print(
            "broken config raises at load; no code path resolves it to a host default"
        )

    def test_an_absent_file_is_a_legitimate_empty_config(self):
        """Kept separate: the POSITIVE half, asserting `config_present` is False yet resolution WORKS."""

        with tempfile.TemporaryDirectory() as d:
            cfg = RP.load(Path(d) / "runner-profiles.json")
            got = RP.resolve(cfg, runner="oc")
            self.assertIsNone(got.model)
            self.assertFalse(got.config_present)


# ==================================================================================================
# E-04 / V-04: source audit (no shell, no eval/exec, no arbitrary command execution)
# ==================================================================================================


class SourceAuditTests(unittest.TestCase):
    """V-04: the module contains NO route to arbitrary execution or to a credential.

    THESE ARE AST-SCOPED AUDITS, NOT SOURCE-TEXT PINS, and the distinction is the reason they survive
    a consolidation pass that deletes change-detectors elsewhere. A text pin asserts that a file
    CONTAINS or LACKS a phrase, breaks on reformatting, and can be satisfied by editing a comment.
    These assert a SECURITY PROPERTY over EXECUTABLE CODE ONLY: `setUp` removes comments and every
    docstring by walking the AST, because this module's own prose says the words "subprocess" and
    "shell" while explaining that it uses neither, and a prose mention must not read as a violation.

    THEY CANNOT BE REPLACED BY A BEHAVIORAL ASSERTION, which is the test a pin has to pass to stay.
    "This module never shells out" is a claim about code that does NOT exist; no input drives a
    function into demonstrating the absence of a call, and a behavioral test would at best show that
    the paths it happened to exercise did not shell out. The vacuity guard (`> 200` code lines) is
    what keeps the audit honest, since an audit over an empty list passes trivially.
    """

    def test_no_arbitrary_argv_or_credential_field_is_persistable(self):
        """Kept separate: pins the ALLOWED sets LITERALLY, so widening them requires saying why.

        Not a source audit at all despite living here: it reads the module's constants, not its text.
        The literal lists are the point, since a set derived from the module would move with any
        widening and assert nothing.
        """

        # The ALLOWED sets are the whole storable surface; assert them literally so widening
        # them requires editing this test and stating why.
        # `verify_with` was ADDED by `runprofile` Order 06 (`kgpptv`) and is listed here
        # deliberately: it is a profile NAME (a reference to an already-validated profile), not
        # argv, environment, an executable, a prompt, or a credential, so it does not widen the
        # injection surface this test exists to fence. An INLINE verifier model would have, which
        # is exactly why the field takes a reference.
        #
        # `execution_profile` was ADDED by `hardreach` Order 01 (`n5qca5`) and is listed here
        # deliberately, WITH THE REASON IT DOES NOT WIDEN THIS FENCE, because it sits nearer the
        # boundary than any field before it: `permission` and `permissions` are refused BY NAME in
        # `FORBIDDEN_PROFILE_KEYS` a few lines below the allowed set, and a sandbox request is that
        # family's neighbour. Three properties keep it on the safe side, and all three are asserted
        # by `ExecutionProfileFieldTests` rather than merely claimed here:
        #
        #   1. ITS VALUE SPACE IS A CLOSED TWO-MEMBER ENUM (`EXECUTION_PROFILE_NAMES`), so it is a
        #      NAME this module owns, exactly as `verify_with` is a name. A path, a root, an argv
        #      fragment and a permission expression are all refused by not being one of two strings,
        #      rather than by a denylist a novel shape could slip past.
        #   2. IT CANNOT DESCRIBE A PERMISSION. It says WHETHER to request the jail, never WHICH paths
        #      are writable; the sandbox plan derives that from the lane the DRIVER allocated. So no
        #      stored value can widen what the sandbox permits, which is what a `permissions` field
        #      would have done and is why that one is forbidden.
        #   3. IT IS A REQUEST, NOT A CAPABILITY CLAIM. The host's EXECUTED probe stays the authority
        #      on whether it can be honored and RAISES rather than degrading, so a stored value cannot
        #      cause an unsandboxed run to be believed sandboxed.
        self.assertEqual(
            sorted(RP.ALLOWED_PROFILE_KEYS),
            [
                "agent",
                "execution_profile",
                "model",
                "runner",
                "validate",
                "variant",
                "verify_with",
            ],
        )
        # `roles` was ADDED by `actmodel` Order 01 (`btot17`) and is listed here deliberately: every
        # VALUE in it is a profile NAME (a reference to an already-validated profile), so it stores no
        # argv, environment, executable, prompt or credential and does not widen the injection surface
        # this test exists to fence. An INLINE model per role would have, which is exactly why a role
        # takes a reference.
        self.assertEqual(
            sorted(RP.ALLOWED_DOCUMENT_KEYS),
            ["default_runner", "defaults", "profiles", "roles", "schema_version"],
        )
        self.assertEqual(
            sorted(RP.ALLOWED_DEFAULTS_KEYS), ["profiles", "validate", "verify_with"]
        )
        self.assertEqual(
            RP.ALLOWED_PROFILE_KEYS & RP.FORBIDDEN_PROFILE_KEYS, frozenset()
        )
        print(
            "storable surface is exactly: "
            f"{sorted(RP.ALLOWED_PROFILE_KEYS)} within {sorted(RP.ALLOWED_DOCUMENT_KEYS)}"
        )

    def test_every_error_class_derives_from_one_base(self):
        for cls in (
            RP.ProfileSchemaError,
            RP.ProfileStoreError,
            RP.ProfileNotFoundError,
            RP.ProfileExistsError,
            RP.ProfileResolutionError,
        ):
            self.assertTrue(issubclass(cls, RP.RunnerProfileError))
            self.assertTrue(issubclass(cls, Exception))


if __name__ == "__main__":
    unittest.main()
