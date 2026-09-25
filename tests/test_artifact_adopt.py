"""Tests for `aw adopt` (IPD lznpv6 E-07 / V-07): the DANGEROUS cases, not the happy path.

The happy path is the least interesting thing about this verb. What matters is the eight ways an
adoption can quietly do permanent damage, each of which is measured here:

  1. a body carrying a BULLET `- Id: <id6>` must NOT have that id6 adopted (the forged-identity case
     `AGENTS.md` warns about: such a line in a raw drop is almost always a quoted example);
  2. a body opening with a YAML `---` fence carrying `id: <id6>` must likewise not have it adopted,
     which is the dialect the research destination ACTUALLY uses and therefore the shape this verb
     meets first;
  3. a `fail`-severity leak must refuse BEFORE any write (asserted on the filesystem: the
     destination does not exist and the original still does);
  4. the `--allow-leaks` override must proceed AND record the findings, while the leaked STRING is
     absent from the adopted artifact (recording a `Finding`'s evidence excerpt verbatim would copy
     the leak into a tracked file and make the record fail `aw sanitize` forever after);
  5. a body with em dashes and unusual formatting must survive BYTE-IDENTICAL;
  6. more than one input path must be refused (no bulk adoption, ever);
  7. a drop whose content already exists as a record must be FLAGGED in the preview (re-adopting
     mints a SECOND id6 for content that already has one, which `aw check` cannot detect because
     there is no id6 COLLISION);
  8. a failure injected at the index-refresh step must leave the original in the inbox and no
     partial artifact in the records tree.

Every case is built in a TEMPORARY repo. No test reads the real `.aw/inbox/`, which is gitignored,
machine-specific, and empties as drops are adopted, so a test pinned to it passes today and fails
tomorrow (there is an explicit assertion guarding that below).

The leak fixture is modeled on the REAL measured case rather than an invented one: a `home-path`
plus `handle` pair on a single line, which is exactly what a live drop carried when this was written.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import artifact_adopt as adopt
from agent_workflows import cli


# The leak fixture, assembled FROM FRAGMENTS so this test file does not itself contain a plain copy
# of a leak token (the same discipline `leak_sanitizer` applies to its own source, which is why that
# module and this kind of test are on the sanitizer's `_ALLOWED_PATHS` list).
_LEAK_USER = "gfa" + "riello"
_LEAK_LINE = (
    "See /home/" + _LEAK_USER + "/VC/agent-workflows/notes.md for the raw data."
)


class _AdoptRepo(unittest.TestCase):
    """A throwaway repo with an inbox and a research tree."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_adopt_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.inbox = self.tmp / ".aw" / "inbox"
        self.research = self.tmp / ".aw" / "records" / "research"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.research.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init", "-q", "."],
            cwd=str(self.tmp),
            check=True,
            capture_output=True,
        )

    # -- helpers -----------------------------------------------------------------------

    def _drop(self, name: str, text: str) -> Path:
        p = self.inbox / name
        # Bytes, not text mode: text mode would translate "\n" to CRLF on Windows.
        p.write_bytes(text.encode("utf-8"))
        return p

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.tmp)])
            except SystemExit as e:  # pragma: no cover - argparse usage exits
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def _adopted_files(self):
        return sorted(
            p for p in self.research.rglob("*.md") if p.name not in ("INDEX.md",)
        )


class BodyDeclaredId6IsNeverAdoptedTests(_AdoptRepo):
    """Case 1 + 2: neither front-matter dialect's id6 is ever adopted."""

    def test_bullet_dialect_id6_is_reported_but_not_adopted(self):
        src = self._drop(
            "widget-audit-research-report.md",
            "# Widget audit\n\nBody.\n\n- Id: abc123\n",
        )
        rc, out = self._run(["adopt", str(src)])
        self.assertEqual(rc, 0, out)
        # Reported as present-but-not-adopted...
        self.assertIn("abc123", out)
        self.assertIn("NOT ADOPTED", out)
        # ...and the plan's minted id6 is a DIFFERENT token.
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        self.assertNotEqual(plan.id6, "abc123")
        self.assertIn("abc123", plan.body_identities.bullet_declared)

    def test_yaml_dialect_id6_is_reported_but_not_adopted(self):
        # The dialect the RESEARCH destination actually uses (spec 5.8), and the one an external
        # LLM report is most likely to open with. A guard written against `^- Id:` alone misses it.
        src = self._drop(
            "metastore-research-report.md",
            "---\nid: abc123\nset: metastore\nstatus: reference\n---\n\n# Metastore\n\nBody.\n",
        )
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        self.assertIn("abc123", plan.body_identities.yaml_declared)
        self.assertNotEqual(plan.id6, "abc123")
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        files = self._adopted_files()
        self.assertEqual(len(files), 1, files)
        self.assertNotIn("abc123", files[0].name)

    def test_a_quoted_bullet_id_that_collides_with_a_live_owner_is_refused(self):
        """The VERBATIM body can itself forge a declaration; the collision case must refuse.

        FOUND BY MEASUREMENT, not by reading the plan. `check_engine._ID_LINE_RE` is applied to the
        WHOLE FILE, so a bullet `- Id: <id6>` line anywhere in an adopted artifact (including one
        merely QUOTED inside an external report) is harvested by `aw check` as that artifact's
        DECLARED identity. When a real artifact already owns that id6, `check.id6-collision` fires,
        which is exactly the forged-identity condition this verb exists to prevent, arriving through
        the preserved body rather than through the mint.
        """
        plans = self.tmp / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True, exist_ok=True)
        (plans / "20260901-someset-01-abc123-a-real-plan.ipd.md").write_text(
            "# IPD\n\n- Id: abc123\n", encoding="utf-8"
        )
        src = self._drop(
            "quoting-research-report.md",
            "# Report\n\nThe grammar looks like this:\n\n- Id: abc123\n\nend.\n",
        )
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 2, out)
        self.assertIn("already the identity of a real artifact", out.lower())
        self.assertEqual(self._adopted_files(), [])
        self.assertTrue(src.is_file())

    def test_a_quoted_bullet_id_owning_nothing_is_reported_and_allowed(self):
        """The refusal is PROPORTIONATE: a quoted id6 that owns nothing must not block adoption.

        Refusing every document that happens to quote the grammar would make the verb unusable on
        exactly the research reports it exists to adopt, so the guard fires only on a real collision.
        """
        src = self._drop(
            "harmless-research-report.md",
            "# Report\n\nExample only:\n\n- Id: abc123\n",
        )
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(self._adopted_files()), 1)

    def test_no_collision_drift_after_adopting_a_body_that_quotes_an_id(self):
        from agent_workflows import check_engine as check

        src = self._drop(
            "quoteclean-research-report.md", "# Report\n\nExample:\n\n- Id: abc123\n"
        )
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        drift = check.check_collisions(self.tmp, include_retired=True)
        self.assertEqual([d.rule for d in drift], [], [d._asdict() for d in drift])

    def test_a_horizontal_rule_is_not_mistaken_for_front_matter(self):
        # Narrowness matters in the other direction too: only a LEADING fence is front matter.
        src = self._drop(
            "rule-research-report.md", "# Title\n\ntext\n\n---\nid: abc123\n---\n"
        )
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        self.assertEqual(plan.body_identities.yaml_declared, ())


class RepositoryWideCollisionSetTests(_AdoptRepo):
    """The collision set is repository-wide AND dialect-complete, not tree-scoped."""

    def test_set_includes_bullet_declared_ids_from_another_tree(self):
        plans = self.tmp / ".aw" / "records" / "plans" / "pending"
        plans.mkdir(parents=True, exist_ok=True)
        (plans / "20260908-someset-01-zzz111-a-plan.ipd.md").write_text(
            "# IPD\n\n- Id: zzz111\n", encoding="utf-8"
        )
        ids = adopt.repository_id6s(self.tmp)
        self.assertIn(
            "zzz111", ids, "a plans-tree bullet id6 must be in the collision set"
        )

    def test_set_includes_yaml_declared_research_ids(self):
        (
            self.research / "20260908-topic-01-yyy222-a-report.research-report.md"
        ).write_text(
            "---\nid: yyy222\ncreated: 20260908\nset: topic\norder: 01\n"
            "topic: []\nmodel: \nkind: research-report\nstatus: todo\n"
            "outcome: none-yet\nsummary: x\nconsumed-by: []\n---\n\n# X\n",
            encoding="utf-8",
        )
        ids = adopt.repository_id6s(self.tmp)
        self.assertIn(
            "yyy222",
            ids,
            "a research YAML `id:` must be in the collision set; the bullet-only reader misses it",
        )


class LeakGateTests(_AdoptRepo):
    """Case 3 + 4: the gate refuses before writing, and the override records rules not text."""

    def _leaky_drop(self) -> Path:
        return self._drop(
            "leaky-research-report.md",
            "# Leaky report\n\n" + _LEAK_LINE + "\n\nMore body.\n",
        )

    def test_fail_severity_leak_refuses_before_any_write(self):
        src = self._leaky_drop()
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 2, out)
        self.assertIn("leak sanitizer", out)
        # The filesystem assertions are the point: nothing written, original intact.
        self.assertEqual(self._adopted_files(), [])
        self.assertTrue(src.is_file(), "the original must still be in the inbox")

    def test_the_gate_calls_scan_text_not_scan_working_tree(self):
        # `scan_working_tree` enumerates TRACKED files via `git ls-files`; an inbox drop is
        # gitignored, so a gate built on it would silently pass EVERYTHING.
        src = self._leaky_drop()
        report = adopt.scan_drop_for_leaks(
            self.tmp, src.read_text(encoding="utf-8"), src.name
        )
        self.assertEqual(report.scan_function, "leak_sanitizer.scan_text")
        self.assertTrue(report.has_fail)
        self.assertIn("home-path", report.fail_rules)
        self.assertIn("handle", report.fail_rules)

    def test_warn_only_drop_proceeds(self):
        src = self._drop("clean-research-report.md", "# Clean\n\nOrdinary body.\n")
        report = adopt.scan_drop_for_leaks(
            self.tmp, src.read_text(encoding="utf-8"), src.name
        )
        self.assertFalse(report.has_fail)
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(self._adopted_files()), 1)

    def test_override_proceeds_and_records_rules_but_never_the_leaked_string(self):
        src = self._leaky_drop()
        original = src.read_text(encoding="utf-8")
        rc, out = self._run(
            [
                "adopt",
                str(src),
                "--allow-leaks",
                "--yes",
                "--actor",
                "test-actor",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, out)
        files = self._adopted_files()
        self.assertEqual(len(files), 1, files)
        adopted = files[0].read_text(encoding="utf-8")
        # The RULE NAMES and the actor are recorded (the override is auditable)...
        self.assertIn("home-path", adopted)
        self.assertIn("handle", adopted)
        self.assertIn("test-actor", adopted)
        self.assertIn("leak-gate override", adopted)
        # ...and the leaked string appears ONLY in the verbatim body, which is exactly the one place
        # it cannot be removed without corrupting the document. The AUDIT NOTE must not repeat it,
        # or the note itself would be a second copy of the leak.
        note_end = adopted.index(original)
        header = adopted[:note_end]
        self.assertNotIn(_LEAK_USER, header)
        self.assertNotIn("/home/", header)

    def test_allow_leaks_refuses_without_a_tty_and_without_an_attestation(self):
        # The established fence: no TTY on BOTH streams means the automatic decision applies, and
        # the automatic decision must be the SAFE one (refuse), never a hang and never acceptance.
        src = self._leaky_drop()
        rc, out = self._run(["adopt", str(src), "--allow-leaks", "--apply"])
        self.assertEqual(rc, 2, out)
        self.assertIn("needs a human", out)
        self.assertEqual(self._adopted_files(), [])
        self.assertTrue(src.is_file())

    def test_interactivity_predicate_requires_both_streams_and_honors_ci(self):
        class _TTY:
            def isatty(self):
                return True

        class _Pipe:
            def isatty(self):
                return False

        self.assertTrue(
            adopt.leak_gate_is_interactive(stdin=_TTY(), stdout=_TTY(), environ={})
        )
        self.assertFalse(
            adopt.leak_gate_is_interactive(stdin=_TTY(), stdout=_Pipe(), environ={})
        )
        self.assertFalse(
            adopt.leak_gate_is_interactive(
                stdin=_TTY(), stdout=_TTY(), environ={"CI": "true"}
            )
        )


class VerbatimBodyTests(_AdoptRepo):
    """Case 5: the body survives byte-identical, em dashes and all."""

    BODY = (
        "# A Report \u2014 With Em Dashes\n"
        "\n"
        "Text with an em dash \u2014 and an en dash \u2013 and trailing spaces.   \n"
        "\ttab-indented line\n"
        "\n"
        "  * odd bullet spacing\n"
        "\n"
        "Final line with no newline at end"
    )

    def test_body_is_byte_identical_after_adoption(self):
        src = self._drop("dashes-research-report.md", self.BODY)
        before = src.read_bytes()
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        files = self._adopted_files()
        self.assertEqual(len(files), 1, files)
        # Decode the raw bytes (no newline translation) so a CRLF-writing product cannot pass.
        adopted = files[0].read_bytes().decode("utf-8")
        self.assertTrue(
            adopted.endswith(self.BODY),
            "the body must be appended VERBATIM below the front matter and provenance",
        )
        self.assertEqual(before.decode("utf-8"), self.BODY)


class BulkRefusalTests(_AdoptRepo):
    """Case 6: more than one path is refused with a stated reason."""

    def test_two_paths_are_refused_and_nothing_is_written(self):
        a = self._drop("a-research-report.md", "# A\n")
        b = self._drop("b-research-report.md", "# B\n")
        rc, out = self._run(["adopt", str(a), str(b), "--apply"])
        self.assertEqual(rc, 2, out)
        self.assertIn("exactly ONE", out)
        self.assertEqual(self._adopted_files(), [])
        self.assertTrue(a.is_file())
        self.assertTrue(b.is_file())

    def test_zero_paths_is_a_usage_error(self):
        rc, out = self._run(["adopt"])
        self.assertEqual(rc, 2, out)


class AlreadyAdoptedWarningTests(_AdoptRepo):
    """Case 7: a drop whose content is already a record is FLAGGED (not refused)."""

    BODY = "# Metastore research\n\nThe body of a report that was already filed.\n"

    def _seed_adopted_copy(self) -> Path:
        shard = self.research / "reference" / "202609"
        shard.mkdir(parents=True, exist_ok=True)
        p = (
            shard
            / "20260901-metastore-01-xn6f6u-metastore.gemini31prohigh.research-report.md"
        )
        p.write_text(
            "---\nid: xn6f6u\ncreated: 20260901\nset: metastore\norder: 01\n"
            "topic: []\nmodel: gemini31prohigh\nkind: research-report\nstatus: reference\n"
            "outcome: informational\nsummary: seeded\nconsumed-by: []\n---\n\n"
            + self.BODY,
            encoding="utf-8",
        )
        return p

    def test_identical_body_is_flagged_in_the_preview_as_already_adopted(self):
        self._seed_adopted_copy()
        src = self._drop("metastore-research-report.gemini31prohigh.agy.md", self.BODY)
        rc, out = self._run(["adopt", str(src)])
        self.assertEqual(rc, 0, out)
        self.assertIn("may already be adopted", out)
        self.assertIn("xn6f6u", out)
        # A WARNING, not a refusal: the human decides, exactly as with the leak gate.
        self.assertTrue(src.is_file())

    def test_the_warning_does_not_block_apply(self):
        self._seed_adopted_copy()
        src = self._drop("metastore-research-report.gemini31prohigh.agy.md", self.BODY)
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        self.assertFalse(src.exists())

    def test_a_distinct_drop_is_not_flagged(self):
        self._seed_adopted_copy()
        src = self._drop(
            "unrelated-research-report.md",
            "# Something else entirely\n\nDifferent text.\n",
        )
        rc, out = self._run(["adopt", str(src)])
        self.assertEqual(rc, 0, out)
        self.assertNotIn("may already be adopted", out)


class FailureOrderingTests(_AdoptRepo):
    """Case 8: the destructive step is LAST, so no failure point loses the file."""

    def test_index_refresh_failure_rolls_back_and_leaves_the_original(self):
        src = self._drop("ordered-research-report.md", "# Ordered\n\nBody.\n")
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None

        def _boom(_repo_root):
            raise RuntimeError("injected index failure")

        result, apply_err = adopt.apply_adoption(
            plan, repo_root=self.tmp, refresh_index=_boom
        )
        self.assertIsNone(result)
        self.assertIsNotNone(apply_err)
        assert apply_err is not None
        self.assertIn("index refresh failed", apply_err)
        # Both halves of the invariant, asserted on the FILESYSTEM.
        self.assertTrue(src.is_file(), "the original must still be in the inbox")
        self.assertFalse(
            plan.destination.exists(),
            "no partial artifact may remain in the records tree",
        )

    def test_destination_write_failure_leaves_the_original(self):
        src = self._drop("blocked-research-report.md", "# Blocked\n\nBody.\n")
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        # Make the destination's parent a FILE so the atomic write cannot create it.
        blocker = plan.destination.parent
        shutil.rmtree(blocker, ignore_errors=True)
        blocker.write_text("not a directory", encoding="utf-8")
        result, apply_err = adopt.apply_adoption(plan, repo_root=self.tmp)
        self.assertIsNone(result)
        assert apply_err is not None
        self.assertIn("destination write failed", apply_err)
        self.assertTrue(src.is_file())

    def test_successful_adoption_removes_the_original_and_writes_the_artifact(self):
        src = self._drop("happy-research-report.md", "# Happy\n\nBody.\n")
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        self.assertFalse(
            src.exists(), "the original must be gone after a successful adoption"
        )
        files = self._adopted_files()
        self.assertEqual(len(files), 1, files)

    def test_existing_destination_is_not_clobbered(self):
        src = self._drop("clash-research-report.md", "# Clash\n\nBody.\n")
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        plan.destination.parent.mkdir(parents=True, exist_ok=True)
        plan.destination.write_text("pre-existing", encoding="utf-8")
        result, apply_err = adopt.apply_adoption(plan, repo_root=self.tmp)
        self.assertIsNone(result)
        assert apply_err is not None
        self.assertIn("refusing to overwrite", apply_err)
        self.assertEqual(plan.destination.read_text(encoding="utf-8"), "pre-existing")
        self.assertTrue(src.is_file())


class ScopeAndPreviewTests(_AdoptRepo):
    """The preview IS the confirmation surface; the inbox restriction is enforced."""

    def test_bare_invocation_writes_nothing_and_shows_the_proposal(self):
        src = self._drop("proposal-research-report.md", "# Proposal\n\nBody.\n")
        rc, out = self._run(["adopt", str(src)])
        self.assertEqual(rc, 0, out)
        for token in ("type:", "kind:", "slug:", "set:", "id6:", "destination:"):
            self.assertIn(token, out)
        self.assertIn("(suggested)", out)
        self.assertIn("re-run with --apply", out)
        self.assertEqual(self._adopted_files(), [])
        self.assertTrue(src.is_file())

    def test_a_path_outside_the_inbox_is_refused(self):
        outside = self.tmp / "stray-report.md"
        outside.write_text("# Stray\n", encoding="utf-8")
        rc, out = self._run(["adopt", str(outside), "--apply"])
        self.assertEqual(rc, 2, out)
        self.assertIn("outside", out)
        self.assertTrue(outside.is_file())

    def test_an_unsupported_destination_type_is_refused_with_the_reason(self):
        src = self._drop("typed-research-report.md", "# Typed\n\nBody.\n")
        rc, out = self._run(["adopt", str(src), "--type", "specs", "--apply"])
        self.assertEqual(rc, 2, out)
        self.assertIn("unsupported destination type", out)
        self.assertEqual(self._adopted_files(), [])

    def test_agent_mode_emits_the_structured_envelope(self):
        src = self._drop("agentmode-research-report.md", "# Agent mode\n\nBody.\n")
        rc, out = self._run(["adopt", str(src), "--agent"])
        self.assertEqual(rc, 0, out)
        payload = json.loads([ln for ln in out.splitlines() if ln.strip()][0])
        self.assertEqual(payload["schema"], "aw.agent/v1")
        self.assertEqual(payload["cmd"], "adopt")
        self.assertEqual(payload["outcome"], "preview")
        self.assertFalse(payload["applied"])
        kinds = sorted(c["kind"] for c in payload["changes"])
        self.assertEqual(kinds, ["create", "delete"], payload["changes"])

    def test_the_same_set_groups_successive_adoptions(self):
        # OQ-03's recommendation, made falsifiable: multi-file comparison sets COMPOSE from the
        # single-file verb because `plan_new` assigns the next NN within a set automatically.
        a = self._drop("topic-a-research-report.md", "# A\n\nBody A.\n")
        b = self._drop("topic-b-research-report.md", "# B\n\nBody B.\n")
        rc, out = self._run(["adopt", str(a), "--set", "shared", "--apply"])
        self.assertEqual(rc, 0, out)
        rc, out = self._run(["adopt", str(b), "--set", "shared", "--apply"])
        self.assertEqual(rc, 0, out)
        names = sorted(p.name for p in self._adopted_files())
        self.assertEqual(len(names), 2, names)
        orders = sorted(n.split("-")[2] for n in names)
        self.assertEqual(orders, ["00", "01"], names)


class SuggestionTests(_AdoptRepo):
    """Metadata suggestion reads the filename; every guess is shown for confirmation."""

    def test_model_facet_and_kind_are_suggested_from_the_filename(self):
        src = self._drop(
            "agent-skill-runtimes-research.gemini31prohigh.agy.md",
            "# Skills\n\nBody.\n",
        )
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        self.assertEqual(plan.suggestion.model, "gemini31prohigh")
        self.assertEqual(plan.suggestion.kind, "research-report")
        self.assertIn("model", plan.suggestion.suggested_fields)
        self.assertIn("kind", plan.suggestion.suggested_fields)

    def test_an_explicit_flag_is_not_marked_suggested(self):
        src = self._drop("explicit-research-report.md", "# Explicit\n\nBody.\n")
        plan, err = adopt.plan_adoption(
            repo_root=self.tmp, source=src, kind="findings", slug="my-slug"
        )
        self.assertIsNone(err)
        assert plan is not None
        self.assertEqual(plan.suggestion.kind, "findings")
        self.assertEqual(plan.suggestion.slug, "my-slug")
        self.assertNotIn("kind", plan.suggestion.suggested_fields)
        self.assertNotIn("slug", plan.suggestion.suggested_fields)

    def test_an_implementation_prompt_is_suggested_as_a_prompt_kind(self):
        src = self._drop(
            "run-analytics-spa-implementation-prompt.md", "# Prompt\n\nBody.\n"
        )
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        self.assertEqual(plan.suggestion.kind, "research-prompt")


class ConformanceOfTheAdoptedArtifactTests(_AdoptRepo):
    """The adopted artifact satisfies the repository-wide invariants that are the real criteria."""

    def test_adopted_artifact_passes_name_and_frontmatter_validation(self):
        from agent_workflows import research_contract as R

        src = self._drop("conformance-research-report.md", "# Conformance\n\nBody.\n")
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        files = self._adopted_files()
        self.assertEqual(len(files), 1, files)
        parsed, name_err = R.parse_name(files[0].name)
        self.assertIsNone(name_err, name_err)
        assert parsed is not None
        data = R.parse_frontmatter(files[0].read_text(encoding="utf-8"))
        self.assertIsNotNone(data)
        assert data is not None
        self.assertEqual(R.validate_frontmatter(data), [])
        self.assertEqual(data["id"], parsed.id6)

    def test_id6_uniqueness_holds_under_the_existing_collision_check(self):
        from agent_workflows import check_engine as check

        src = self._drop("unique-research-report.md", "# Unique\n\nBody.\n")
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        drift = check.check_collisions(self.tmp, include_retired=True)
        offenders = [
            d
            for d in drift
            if d.rule in ("check.id6-collision", "check.id6-identity-slot")
        ]
        self.assertEqual(offenders, [], [d._asdict() for d in offenders])

    def test_aw_check_proves_nothing_about_a_research_id6_so_the_mint_must(self):
        """A clean `aw check` is a WEAKER guarantee here than it looks; pin the real one.

        MEASURED, and it corrects the plan's assumption in both halves. For a RESEARCH artifact:
          * `check_engine`'s declared-id map reads only the bullet `- Id:` dialect, so a research
            YAML `id:` contributes NOTHING to it; and
          * the filename identity-slot rule EXEMPTS the name, because `research-report` is not a
            member of the CLOSED `ARTIFACT_TYPE_FACETS` enum, so `parse_clustered` rejects it and
            `_identity_slot_token` returns None.
        So NEITHER collision rule fires, and two research files can carry the SAME id6 with
        `aw check` reporting clean. That gap is PRE-EXISTING and outside this plan's fence.

        The consequence for `aw adopt` is what this test pins: the uniqueness of an adopted research
        id6 rests ENTIRELY on the mint being made against the repository-wide, dialect-complete
        collision set, and on nothing downstream. If that injection regressed, no check would catch
        it, so it is asserted directly here.
        """
        from agent_workflows import check_engine as check
        from agent_workflows import artifact_naming as naming

        taken = "20260901-topic-01-tkntkn-taken.research-report.md"
        (self.research / taken).write_text(
            "---\nid: tkntkn\ncreated: 20260901\nset: topic\norder: 01\ntopic: []\n"
            "model: \nkind: research-report\nstatus: todo\noutcome: none-yet\n"
            "summary: x\nconsumed-by: []\n---\n\n# Taken\n",
            encoding="utf-8",
        )
        # Neither collision rule can see that id6 (the weakness this test documents).
        self.assertIsNone(naming.parse_clustered(taken))
        self.assertIsNone(check._identity_slot_token(taken))
        self.assertEqual(check.check_collisions(self.tmp, include_retired=True), [])
        # But the MINT sees it, because the collision set reads the YAML dialect.
        self.assertIn("tkntkn", adopt.repository_id6s(self.tmp))
        src = self._drop("mint-research-report.md", "# Mint\n\nBody.\n")
        plan, err = adopt.plan_adoption(repo_root=self.tmp, source=src)
        self.assertIsNone(err)
        assert plan is not None
        self.assertNotEqual(plan.id6, "tkntkn")

    def test_the_provenance_marker_is_present_and_names_the_original(self):
        src = self._drop("provenance-research-report.md", "# Provenance\n\nBody.\n")
        rc, out = self._run(["adopt", str(src), "--apply"])
        self.assertEqual(rc, 0, out)
        adopted = self._adopted_files()[0].read_text(encoding="utf-8")
        self.assertIn("<!-- aw-adopt: provenance -->", adopted)
        self.assertIn("provenance-research-report.md", adopted)


class NoTestReadsTheRealInboxTests(unittest.TestCase):
    """A test pinned to the real `.aw/inbox/` passes today and fails tomorrow; prove none is."""

    def test_this_module_never_references_the_repository_inbox_path(self):
        text = Path(__file__).read_text(encoding="utf-8")
        for line in text.splitlines():
            if ".aw/inbox" in line and "self.inbox" not in line:
                # Only prose/docstrings and the module constant reference may mention it.
                stripped = line.strip()
                self.assertFalse(
                    stripped.startswith(("Path(", "src =", "p =")),
                    f"a test must not read the real inbox: {stripped}",
                )


class ModuleContractTests(unittest.TestCase):
    """Small invariants that are cheap to assert and expensive to lose."""

    def test_only_research_is_supported_on_day_one(self):
        self.assertEqual(adopt.SUPPORTED_TYPES, ("research",))

    def test_the_leak_note_never_contains_matched_text(self):
        report = adopt.LeakReport(
            fail_rules=("home-path",),
            warn_rules=(),
            fail_locations=("drop.md:3",),
            warn_locations=(),
            scan_function="leak_sanitizer.scan_text",
        )
        note = adopt.render_leak_note(report, override_actor="someone")
        self.assertIn("home-path", note)
        self.assertIn("drop.md:3", note)
        self.assertIn("someone", note)
        self.assertNotIn("/home/", note)

    def test_a_rule_name_that_embeds_the_matched_token_is_redacted(self):
        # FOUND BY THIS TEST SUITE, NOT BY READING (see the module note on F-18's second half):
        # `build_ruleset` registers the auto-derived advisory patterns as `derived:<token>` and a
        # config-promoted hostname as `hostname:<token>`, so recording the RULE NAME verbatim writes
        # the leaked username or hostname into the tracked artifact just as surely as recording the
        # matched line would. The rule-name allowlist collapses those two namespaces to their class.
        secret = "somebody" + "-secret"
        self.assertEqual(
            adopt.safe_rule_name("derived:" + secret), "derived:<redacted>"
        )
        self.assertEqual(
            adopt.safe_rule_name("hostname:" + secret), "hostname:<redacted>"
        )
        # A structural or indexed config rule name carries no secret and passes through unchanged.
        for rule in (
            "home-path",
            "handle",
            "session-id",
            "repo-pattern-0",
            "user-hint-1",
        ):
            self.assertEqual(adopt.safe_rule_name(rule), rule)
        note = adopt.render_leak_note(
            adopt.LeakReport(
                fail_rules=("hostname:" + secret,),
                warn_rules=("derived:" + secret,),
                fail_locations=("drop.md:1",),
                warn_locations=("drop.md:1",),
                scan_function="leak_sanitizer.scan_text",
            ),
            override_actor="someone",
        )
        self.assertNotIn(secret, note)
        self.assertIn("<redacted>", note)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
