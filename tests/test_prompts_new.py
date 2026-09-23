"""Tests for `aw prompts new` (IPD jxqdcw E-06 / V-06, REVISED by IPD ubac5n E-01/E-02).

Covers the properties the plans make falsifiable:
  * dry-run is the DEFAULT and writes NOTHING (fails against an eager writer);
  * `--apply` writes exactly one file at the derived path, in the uniform CLUSTERED grammar
    `YYYYMMDD-<setid>-NN-<id6>-<slug>.prompt.md` with a freshly minted repository-unique id6;
  * the first line is a SINGLE-line `aw-prompt` HTML comment carrying the supplied fields AND the
    minted `Id:`/`Set:`, and nothing precedes it (the prompt-purity property, approved spec P4/P5);
  * `NN` is the ORDER WITHIN THE SET and increments for a second prompt in the same set;
  * that order is computed across the WHOLE prompts tree, so it does not collide with a set member
    that already moved to `executed/` (fails against a `pending/`-only sequencer);
  * an unrecognized `--kind` exits nonzero and writes nothing (fails against a permissive kind);
  * `--agent` emits the standard result envelope;
  * no placeholder author is emitted when `--author` is omitted.

WHAT CHANGED AT `ubac5n` AND WHY THE OLD ASSERTIONS ARE GONE RATHER THAN DELETED: two tests pinned
the LEGACY contract (the exact name `20260830-0930-01-token-compression.prompt.md`, and the per-minute
`-01`/`-02` increment). Those were CORRECT tests of the old behavior, which `ubac5n` OQ-01 deliberately
replaced, so each is REWRITTEN in place to assert the new contract at the same point rather than
dropped. The clock is still PINNED via `--date` (and, for the default-clock case, by patching
`prompts._now`) so assertions are deterministic under the default `xdist` parallel invocation.
`--time` is still passed in a few places on purpose: it is accepted and validated but no longer feeds
the name, and a test proves exactly that.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import cli
from agent_workflows import prompts as prompts_mod

#: The uniform clustered prompt name this verb must now emit.
_CLUSTERED_PROMPT_RE = re.compile(
    r"\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-"
    r"(?P<slug>[a-z0-9-]+)\.prompt\.md\Z"
)


class _PromptsRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_prompts_new_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.prompts = self.tmp / ".aw" / "records" / "prompts"
        self.pending = self.prompts / "pending"
        self.pending.mkdir(parents=True, exist_ok=True)

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.tmp)])
            except SystemExit as e:  # pragma: no cover - argparse usage exits
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def _pending_files(self):
        return sorted(p.name for p in self.pending.glob("*.md"))

    def _one_pending(self):
        """The single pending file, with its parsed clustered-name fields. Fails if not exactly one."""

        names = self._pending_files()
        self.assertEqual(len(names), 1, names)
        m = _CLUSTERED_PROMPT_RE.match(names[0])
        self.assertIsNotNone(
            m,
            f"{names[0]!r} is not the uniform clustered prompt grammar "
            "YYYYMMDD-<setid>-NN-<id6>-<slug>.prompt.md",
        )
        assert m is not None
        return self.pending / names[0], m


class TestDryRunDefault(_PromptsRepoTestCase):
    """Preview is the default; nothing is written without --apply."""

    def test_dry_run_prints_intended_path_and_writes_nothing(self):
        before = self._pending_files()
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "token-compression",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertIn("would write", out)
        # ubac5n E-01: the previewed name is the CLUSTERED grammar, not the legacy HHMM form. Matched
        # by pattern rather than pinned literally, because the id6 is minted and so is not predictable.
        self.assertRegex(
            out,
            r"20260830-token-compression-01-[0-9a-z]{6}-token-compression\.prompt\.md",
            out,
        )
        self.assertNotIn("20260830-0930-01-token-compression.prompt.md", out)
        # The falsifiable part: the directory is UNCHANGED.
        self.assertEqual(self._pending_files(), before)
        self.assertEqual(before, [])


class TestApplyWritesConformingFile(_PromptsRepoTestCase):
    def test_apply_writes_exactly_one_file_at_derived_path(self):
        """ubac5n E-01: REWRITTEN from the legacy pin `20260830-0930-01-token-compression.prompt.md`.

        The old assertion was a correct test of the OLD contract; OQ-01/OQ-02 replaced that contract,
        so this asserts the new one at the same point instead of being deleted. Every slot is checked
        individually, so a name missing any of date/set/NN/id6/slug/facet fails.
        """

        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "token-compression",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        path, m = self._one_pending()
        self.assertEqual(m.group("date"), "20260830")
        # No `--set`: the slug becomes a singleton set id.
        self.assertEqual(m.group("set"), "token-compression")
        self.assertEqual(m.group("nn"), "01")
        self.assertEqual(m.group("slug"), "token-compression")
        self.assertRegex(m.group("id6"), r"\A[0-9a-z]{6}\Z")
        # The minted id6 is the SAME one recorded inside the file (E-02), not a second draw.
        self.assertEqual(
            prompts_mod.read_metadata_id6(path.read_text(encoding="utf-8")),
            m.group("id6"),
        )

    def test_explicit_set_lands_in_the_set_slot(self):
        """ubac5n E-01: `--set` puts its own token in the set position, leaving the slug alone."""

        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "token-compression",
                "--set",
                "tokenwork",
                "--date",
                "2026-08-30",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        _path, m = self._one_pending()
        self.assertEqual(m.group("set"), "tokenwork")
        self.assertEqual(m.group("slug"), "token-compression")

    def test_an_over_long_derived_set_id_falls_back_to_the_id6_instead_of_refusing(
        self,
    ):
        """ubac5n E-01: a long SLUG must not make a `--set`-less call exit 2.

        Measured at execution: 15 of the 16 legacy prompt slugs exceed the 24-character setid maximum,
        so deriving the set id from the slug UNCONDITIONALLY would refuse the typical invocation with a
        message about a flag the caller never passed. The fallback is the artifact's own id6, which is
        what `specs.run_new` does for a standalone spec and is 6 characters by construction.
        """

        long_slug = "plain-language-reporting-instructions"  # 37 chars
        self.assertGreater(len(long_slug), 24)
        rc, out = self._run(
            ["prompts", "new", "--slug", long_slug, "--date", "2026-08-30", "--apply"]
        )
        self.assertEqual(rc, 0, out)
        _path, m = self._one_pending()
        self.assertEqual(m.group("set"), m.group("id6"))
        # The long slug still lands in the SLUG slot, where no length policy applies.
        self.assertEqual(m.group("slug"), long_slug)

    def test_an_over_long_explicit_set_is_still_refused(self):
        """The fallback above must NOT weaken the shared guard for a token the caller CHOSE."""

        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "x",
                "--set",
                "this-set-id-is-way-too-long-for-policy",
                "--date",
                "2026-08-30",
                "--apply",
            ]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("24-character maximum", out)
        self.assertEqual(self._pending_files(), [])

    def test_time_is_accepted_and_validated_but_absent_from_the_name(self):
        """ubac5n OQ-01: the clustered grammar has no HHMM slot, so `--time` cannot feed the name.

        It is KEPT rather than removed because the shipped `research-prompt` workflow passes it, and it
        is still VALIDATED rather than silently swallowed.
        """

        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "timeless",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        name = self._pending_files()[0]
        self.assertNotIn("0930", name)
        rc, out = self._run(
            ["prompts", "new", "--slug", "bad-time", "--time", "99", "--apply"]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("--time must be HHMM", out)

    def test_first_line_is_single_line_aw_prompt_comment_with_fields(self):
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "token-compression",
                "--kind",
                "research",
                "--author",
                "opencode (provider/model)",
                "--targets",
                "GPT-5.6",
                "--concerns",
                "prompt staging is untooled",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        path, m = self._one_pending()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        first = lines[0]
        # Purity property: the comment IS the first line (nothing precedes it) and it is exactly one
        # line (it opens and closes on that line).
        self.assertTrue(first.startswith("<!-- aw-prompt: "), first)
        self.assertTrue(first.endswith("-->"), first)
        self.assertEqual(text.count("<!-- aw-prompt:"), 1, text)
        self.assertEqual(text.count("-->"), 1, text)
        for field in (
            "Kind: research",
            # ubac5n E-02: the id6 and set are carried INSIDE this one comment.
            f"Id: {m.group('id6')}",
            "Set: token-compression",
            "Status: pending",
            "Created: 2026-08-30",
            "Author: opencode (provider/model)",
            "Targets: GPT-5.6",
            "Concerns: prompt staging is untooled",
        ):
            self.assertIn(field, first)
        # No YAML front-matter, no `- Id:` BULLET (which would be visible text above the prompt body
        # and an approved-spec violation), and no body boilerplate.
        self.assertFalse(text.startswith("---"), text)
        self.assertNotIn("\n- Id:", text)
        self.assertEqual([ln for ln in lines[1:] if ln.strip()], [], text)

    def test_omitted_author_emits_no_placeholder(self):
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "no-author",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        path, _m = self._one_pending()
        first = path.read_text(encoding="utf-8").splitlines()[0]
        self.assertNotIn("Author:", first)
        self.assertNotIn("unknown", first.lower())

    def test_default_clock_is_used_when_date_and_time_omitted(self):
        pinned = dt.datetime(2026, 8, 30, 9, 30, 0)
        with mock.patch.object(prompts_mod, "_now", return_value=pinned):
            rc, out = self._run(["prompts", "new", "--slug", "pinned-clock", "--apply"])
        self.assertEqual(rc, 0, out)
        _path, m = self._one_pending()
        # The DATE still comes from the clock; the time no longer appears anywhere in the name.
        self.assertEqual(m.group("date"), "20260830")
        self.assertEqual(m.group("slug"), "pinned-clock")


class TestSetOrderSequence(_PromptsRepoTestCase):
    """ubac5n OQ-01: `NN` is ORDER WITHIN THE SET, not a per-minute sequence.

    REWRITTEN from `TestPerMinuteSequence`. The old class asserted the per-minute contract, which was
    correct then and is now replaced; the three properties it protected (a second prompt increments,
    a member already in `executed/` still occupies its slot, a gitignored lane does not) are each
    re-expressed against the SET, so none of that coverage is lost.
    """

    def test_second_prompt_in_the_same_set_increments_to_02(self):
        for slug in ("first-topic", "second-topic"):
            rc, out = self._run(
                [
                    "prompts",
                    "new",
                    "--slug",
                    slug,
                    "--set",
                    "shared",
                    "--date",
                    "2026-08-30",
                    "--apply",
                ]
            )
            self.assertEqual(rc, 0, out)
        names = self._pending_files()
        self.assertEqual(len(names), 2, names)
        orders = sorted(_CLUSTERED_PROMPT_RE.match(n).group("nn") for n in names)  # type: ignore[union-attr]
        self.assertEqual(orders, ["01", "02"])
        # Distinct id6s: each mint is its own identity, never a reused one.
        id6s = {_CLUSTERED_PROMPT_RE.match(n).group("id6") for n in names}  # type: ignore[union-attr]
        self.assertEqual(len(id6s), 2, names)

    def test_two_singleton_prompts_each_get_order_01(self):
        """Different slugs mean different (derived) sets, so neither inherits the other's order."""

        for slug in ("alpha-topic", "beta-topic"):
            rc, out = self._run(
                ["prompts", "new", "--slug", slug, "--date", "2026-08-30", "--apply"]
            )
            self.assertEqual(rc, 0, out)
        names = self._pending_files()
        self.assertEqual(
            sorted(_CLUSTERED_PROMPT_RE.match(n).group("nn") for n in names),  # type: ignore[union-attr]
            ["01", "01"],
        )

    def test_order_does_not_collide_with_a_set_member_in_executed(self):
        executed = self.prompts / "executed"
        executed.mkdir(parents=True, exist_ok=True)
        (executed / "20260830-shared-01-aaa111-already-run.prompt.md").write_text(
            "<!-- aw-prompt: Kind: research | Id: aaa111 | Set: shared | Status: executed "
            "| Created: 2026-08-30 -->\n",
            encoding="utf-8",
        )
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "fresh-topic",
                "--set",
                "shared",
                "--date",
                "2026-08-30",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        # A `pending/`-only sequencer would have emitted NN=01 and shadowed the executed member.
        _path, m = self._one_pending()
        self.assertEqual(m.group("nn"), "02")

    def test_gitignored_lanes_do_not_consume_an_order_number(self):
        local = self.prompts / "local"
        local.mkdir(parents=True, exist_ok=True)
        (local / "20260830-shared-01-bbb222-raw-draft.prompt.md").write_text(
            "raw draft\n", encoding="utf-8"
        )
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "tracked-topic",
                "--set",
                "shared",
                "--date",
                "2026-08-30",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        _path, m = self._one_pending()
        self.assertEqual(m.group("nn"), "01")

    def test_a_minted_id6_never_collides_with_one_already_in_the_tree(self):
        """The mint consults the prompts tree's own ids (filename slot AND metadata comment)."""

        executed = self.prompts / "executed"
        executed.mkdir(parents=True, exist_ok=True)
        (executed / "20260830-other-01-ccc333-prior.prompt.md").write_text(
            "<!-- aw-prompt: Kind: research | Id: ccc333 | Status: executed "
            "| Created: 2026-08-30 -->\n",
            encoding="utf-8",
        )
        self.assertIn("ccc333", prompts_mod._existing_id6s(self.prompts))
        rc, out = self._run(
            ["prompts", "new", "--slug", "new-topic", "--date", "2026-08-30", "--apply"]
        )
        self.assertEqual(rc, 0, out)
        _path, m = self._one_pending()
        self.assertNotEqual(m.group("id6"), "ccc333")


class TestRejections(_PromptsRepoTestCase):
    def test_unrecognized_kind_exits_nonzero_and_writes_nothing(self):
        rc, out = self._run(
            ["prompts", "new", "--slug", "bad-kind", "--kind", "nonsense", "--apply"]
        )
        self.assertNotEqual(rc, 0, out)
        self.assertEqual(rc, 2, out)
        self.assertIn("nonsense", out)
        self.assertEqual(self._pending_files(), [])

    def test_missing_slug_exits_two(self):
        rc, out = self._run(["prompts", "new", "--apply"])
        self.assertEqual(rc, 2, out)
        self.assertEqual(self._pending_files(), [])

    def test_recognized_kinds_are_the_measured_corpus_set(self):
        self.assertEqual(
            prompts_mod.PROMPT_KINDS, ("run-once", "research", "session-handoff")
        )
        for kind in prompts_mod.PROMPT_KINDS:
            rc, out = self._run(
                [
                    "prompts",
                    "new",
                    "--slug",
                    f"kind-{kind}",
                    "--kind",
                    kind,
                    "--date",
                    "2026-08-30",
                    "--time",
                    "0930",
                ]
            )
            self.assertEqual(rc, 0, out)


class TestAgentEnvelope(_PromptsRepoTestCase):
    def test_agent_output_is_the_standard_result_envelope(self):
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "agent-mode",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
                "--agent",
            ]
        )
        self.assertEqual(rc, 0, out)
        rec = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "prompts new")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertFalse(rec["applied"])
        self.assertEqual(rec["changes"][0]["kind"], "create")
        self.assertRegex(
            rec["changes"][0]["path"],
            r"20260830-agent-mode-01-[0-9a-z]{6}-agent-mode\.prompt\.md\Z",
        )
        self.assertNotIn(
            "20260830-0930-01-agent-mode.prompt.md", rec["changes"][0]["path"]
        )

    def test_the_declared_flag_surface_matches_the_parser(self):
        """ubac5n E-01: `--set` is DECLARED, not merely accepted, so the two cannot drift."""

        from agent_workflows.cli import _build_parser
        from agent_workflows import command_surface as cs

        decl = cs.get_declaration("prompts new")
        assert decl is not None
        self.assertIn("--set", decl.legacy_flags)
        prompts_parser = None
        for action in _build_parser()._actions:  # noqa: SLF001
            choices = getattr(action, "choices", None)
            if choices and hasattr(choices, "get") and choices.get("prompts"):
                prompts_parser = choices["prompts"]
                break
        assert prompts_parser is not None, "no `prompts` subparser"
        inner = {}
        for action in prompts_parser._actions:  # noqa: SLF001
            choices = getattr(action, "choices", None)
            if choices and hasattr(choices, "items"):
                inner.update(choices)
        accepted = {opt for act in inner["new"]._actions for opt in act.option_strings}  # noqa: SLF001
        self.assertEqual(set(decl.legacy_flags) - accepted, set())


class TestBackendRegistration(unittest.TestCase):
    def test_prompts_new_resolves_through_the_type_backend_registry(self):
        from agent_workflows import artifact_types as at

        self.assertEqual(at.TYPE_BACKENDS["prompts"]["new"], "prompts.run_new")
        self.assertIs(at.resolve_backend("prompts", "new"), prompts_mod.run_new)

    def test_prompts_new_is_declared_in_the_command_surface(self):
        from agent_workflows import command_surface as cs

        decl = cs.get_declaration("prompts new")
        assert decl is not None, "prompts new must carry a contract declaration"
        self.assertEqual(decl.command_class, "mutation")
        self.assertEqual(decl.mutation_gate, "dry_run_default")

    def test_prompts_new_is_not_an_undeclared_parser_leaf(self):
        """The suite-wide zero-undeclared-leaves test is RED at baseline for other verbs; this
        asserts only the part this plan owns, namely that `prompts new` is not in that set."""
        from agent_workflows.cli import _build_parser
        from agent_workflows.command_surface import find_undeclared_leaves

        self.assertNotIn("prompts new", find_undeclared_leaves(_build_parser()))


if __name__ == "__main__":
    unittest.main()
