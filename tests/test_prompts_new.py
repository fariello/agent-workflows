"""Tests for `aw prompts new` (IPD jxqdcw E-06 / V-06).

Covers the properties the plan makes falsifiable:
  * dry-run is the DEFAULT and writes NOTHING (fails against an eager writer);
  * `--apply` writes exactly one file at the derived path;
  * the first line is a SINGLE-line `aw-prompt` HTML comment carrying the supplied fields, and
    nothing precedes it (the prompt-purity property, approved spec P4/P5);
  * the per-minute `NN` sequence increments within the same minute;
  * the sequence is computed across the WHOLE prompts tree, so it does not collide with a
    same-minute prompt that already moved to `executed/` (fails against a `pending/`-only sequencer);
  * an unrecognized `--kind` exits nonzero and writes nothing (fails against a permissive kind);
  * `--agent` emits the standard result envelope;
  * no placeholder author is emitted when `--author` is omitted.

The clock is PINNED via the explicit `--date`/`--time` flags (and, for the default-clock case, by
patching `prompts._now`) rather than raced against wall time, so the sequence assertions are
deterministic and safe under the default `xdist` parallel invocation.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import cli
from agent_workflows import prompts as prompts_mod


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
        self.assertIn("20260830-0930-01-token-compression.prompt.md", out)
        # The falsifiable part: the directory is UNCHANGED.
        self.assertEqual(self._pending_files(), before)
        self.assertEqual(before, [])


class TestApplyWritesConformingFile(_PromptsRepoTestCase):
    def test_apply_writes_exactly_one_file_at_derived_path(self):
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
        self.assertEqual(
            self._pending_files(), ["20260830-0930-01-token-compression.prompt.md"]
        )

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
        text = (
            self.pending / "20260830-0930-01-token-compression.prompt.md"
        ).read_text(encoding="utf-8")
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
            "Status: pending",
            "Created: 2026-08-30",
            "Author: opencode (provider/model)",
            "Targets: GPT-5.6",
            "Concerns: prompt staging is untooled",
        ):
            self.assertIn(field, first)
        # No YAML front-matter, and no body boilerplate: the verb writes the comment and stops.
        self.assertFalse(text.startswith("---"), text)
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
        first = (
            (self.pending / "20260830-0930-01-no-author.prompt.md")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        self.assertNotIn("Author:", first)
        self.assertNotIn("unknown", first.lower())

    def test_default_clock_is_used_when_date_and_time_omitted(self):
        pinned = dt.datetime(2026, 8, 30, 9, 30, 0)
        with mock.patch.object(prompts_mod, "_now", return_value=pinned):
            rc, out = self._run(["prompts", "new", "--slug", "pinned-clock", "--apply"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            self._pending_files(), ["20260830-0930-01-pinned-clock.prompt.md"]
        )


class TestPerMinuteSequence(_PromptsRepoTestCase):
    def test_second_call_in_same_minute_increments_to_02(self):
        for slug in ("first-topic", "second-topic"):
            rc, out = self._run(
                [
                    "prompts",
                    "new",
                    "--slug",
                    slug,
                    "--date",
                    "2026-08-30",
                    "--time",
                    "0930",
                    "--apply",
                ]
            )
            self.assertEqual(rc, 0, out)
        self.assertEqual(
            self._pending_files(),
            [
                "20260830-0930-01-first-topic.prompt.md",
                "20260830-0930-02-second-topic.prompt.md",
            ],
        )

    def test_sequence_does_not_collide_with_same_minute_file_in_executed(self):
        executed = self.prompts / "executed"
        executed.mkdir(parents=True, exist_ok=True)
        (executed / "20260830-0930-01-already-run.prompt.md").write_text(
            "<!-- aw-prompt: Kind: research | Status: executed | Created: 2026-08-30 -->\n",
            encoding="utf-8",
        )
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "fresh-topic",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        # A `pending/`-only sequencer would have emitted NN=01 and shadowed the executed prompt.
        self.assertEqual(
            self._pending_files(), ["20260830-0930-02-fresh-topic.prompt.md"]
        )

    def test_gitignored_lanes_do_not_consume_a_sequence_number(self):
        local = self.prompts / "local"
        local.mkdir(parents=True, exist_ok=True)
        (local / "20260830-0930-01-raw-draft.prompt.md").write_text(
            "raw draft\n", encoding="utf-8"
        )
        rc, out = self._run(
            [
                "prompts",
                "new",
                "--slug",
                "tracked-topic",
                "--date",
                "2026-08-30",
                "--time",
                "0930",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(
            self._pending_files(), ["20260830-0930-01-tracked-topic.prompt.md"]
        )


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
        self.assertIn(
            "20260830-0930-01-agent-mode.prompt.md", rec["changes"][0]["path"]
        )


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
