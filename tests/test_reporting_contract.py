"""Tests for the portable concise-reporting contract (terseout Order 01, `ntf6sx`).

Covers E-07 (contract source, managed-section rendering, installer safety, first-sibling-section
consent/drift) and E-08 (shim pointer, driver prompts, parity/anti-duplication, size budget, and
the `build_review_prompt` exact-match regression guard).

What these tests CAN prove: the contract text exists once, is reachable on every delivery
surface, and the surfaces do not carry independently maintained copies. What they CANNOT prove:
that a probabilistic model obeys it. Delivery is deterministic; obedience is not (plan `ntf6sx`
execution contract item 7).

Stdlib ``unittest`` (repository convention).
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd
from agent_workflows import engine as INS
from agent_workflows import reporting_contract as RC
from tests.support import SOURCE_WORKFLOWS, init_repo

REPO_ROOT = Path(__file__).resolve().parent.parent

# Baseline measured at plan time (V-03): 48 generated shim files, 42,701 bytes. The pointer is
# one short line per shim, so the corpus may grow by at most this much. A duplication of the
# full prose (~1.7KB x 48 = ~80KB) blows through it by more than an order of magnitude, which is
# exactly what this budget exists to catch.
SHIM_CORPUS_BASELINE_BYTES = 42_701
SHIM_POINTER_BUDGET_BYTES_PER_FILE = 160


def _flat(text: str) -> str:
    """Collapse whitespace so a needle assertion is insensitive to line wrapping.

    The contract is hard-wrapped for readability inside instruction files, so a phrase like
    "durable artifacts" can legitimately straddle a newline. Asserting on the flattened text
    checks the WORDING without freezing the wrap column.
    """

    return " ".join(text.split())


def _shim_corpus() -> dict[str, str]:
    """Every generated command shim for both hosts, from the live manifest."""

    workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
    members = INS.generate_shim_members(workflows, SOURCE_WORKFLOWS, target_layout="aw")
    return {
        rel: text
        for rel, text in members.items()
        if rel.endswith(".md") and not rel.endswith("/README.md")
    }


class ContractSourceTests(unittest.TestCase):
    """E-01/V-01: one importable, provider-neutral source of truth."""

    def setUp(self) -> None:
        self.text = RC.contract_text()
        self.flat = _flat(self.text)

    def test_module_imports_and_returns_text(self) -> None:
        self.assertTrue(self.text.strip())
        self.assertTrue(self.text.endswith("\n"))
        # Stable across calls (no time/randomness in the contract).
        self.assertEqual(self.text, RC.contract_text())

    def test_contract_states_every_brevity_rule(self) -> None:
        needles = (
            "Lead with the OUTCOME",
            "`Yes.`",
            "`No.`",
            "one sentence",
            "preambles",
            "praise",
            "restatement",
            "narration",
            "recaps",
            "closing offers",
            "plain direct language",
            "changed files",
            "verification status",
            "blockers",
            "OMIT a category",
            "at or below 100 words",
            "one short progress sentence",
        )
        for needle in needles:
            self.assertIn(needle, self.flat, f"contract must state {needle!r}")

    def test_contract_states_every_completeness_exception(self) -> None:
        needles = (
            "explicit user request",
            "OVERRIDES the default",
            "required evidence",
            "safety warnings",
            "destructive-action",
            "structured outcomes",
            "durable artifacts",
            "not analysis, implementation, testing",
        )
        for needle in needles:
            self.assertIn(needle, self.flat, f"contract must except {needle!r}")

    def test_contract_cannot_be_read_as_permission_to_do_less(self) -> None:
        self.assertIn("Saying less is never permission to do", self.flat)
        self.assertIn("verify less", self.flat)

    def test_word_cap_constant_matches_the_prose(self) -> None:
        self.assertEqual(RC.ROUTINE_FINAL_WORD_CAP, 100)
        self.assertIn(f"at or below {RC.ROUTINE_FINAL_WORD_CAP} words", self.flat)

    def test_contract_is_pure_ascii(self) -> None:
        """It is embedded into prompts and instruction files asserted to be ASCII."""

        bad = sorted({c for c in self.text if ord(c) > 127})
        self.assertEqual(bad, [], f"non-ASCII characters in the contract: {bad}")

    def test_no_second_independently_maintained_production_copy(self) -> None:
        """Only `reporting_contract.py` may contain the contract's opening sentence."""

        sentence = "Report to the user concisely."
        owners = []
        for py in (REPO_ROOT / "agent_workflows").rglob("*.py"):
            if sentence in py.read_text(encoding="utf-8"):
                owners.append(py.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(
            owners,
            ["agent_workflows/reporting_contract.py"],
            "the contract prose must live in exactly one production module",
        )


class PrecedenceTests(unittest.TestCase):
    """E-06/V-06: the required-report override must be explicit and bidirectional."""

    def setUp(self) -> None:
        self.text = RC.contract_text()
        self.flat = _flat(self.text)

    def test_names_the_required_report_override(self) -> None:
        self.assertIn("PRECEDENCE", self.flat)
        self.assertIn("required report", self.flat)
        self.assertIn("IN FULL", self.flat)
        self.assertIn(
            f"do NOT apply the {RC.ROUTINE_FINAL_WORD_CAP}-word cap to it", self.flat
        )

    def test_names_the_conflicting_workflows_concretely(self) -> None:
        self.assertIn("plan-review", self.flat)
        self.assertIn("literal final output", self.flat)
        self.assertIn("release-review", self.flat)

    def test_inverse_guard_brevity_does_not_excuse_skipping_evidence(self) -> None:
        self.assertIn("NEVER licenses truncating a mandated report", self.flat)
        self.assertIn("ACTUAL runner output", self.flat)

    def test_the_quoted_workflow_rule_still_exists_in_the_repo(self) -> None:
        """The override quotes plan-review; if that rule moves, this contract text is stale."""

        body = (
            REPO_ROOT / ".aw/system/workflows/plan-review/plan-review.md"
        ).read_text(encoding="utf-8")
        self.assertIn("literal final output", body)


class ManagedSectionTests(unittest.TestCase):
    """E-02/V-02: a separately owned `aw:reporting` sibling section."""

    def test_two_sections_are_emitted_pointer_then_reporting(self) -> None:
        slugs = [s.slug for s in INS.agents_managed_sections(target_layout="aw")]
        self.assertEqual(slugs, [INS.AW_POINTER_SLUG, INS.AW_REPORTING_SLUG])

    def test_slug_constant_comes_from_the_contract_module(self) -> None:
        self.assertEqual(INS.AW_REPORTING_SLUG, RC.REPORTING_SLUG)
        self.assertEqual(INS.AW_REPORTING_SLUG, "reporting")

    def test_rendered_block_carries_exactly_one_reporting_marker(self) -> None:
        block = INS.agents_managed_block(target_layout="aw")
        self.assertEqual(block.count("<!-- aw:reporting -->"), 1)
        self.assertEqual(block.count("<!-- aw:pointer -->"), 1)
        self.assertEqual(block.count("<!-- aw:block -->"), 1)
        self.assertEqual(block.count("<!-- /aw:block -->"), 1)

    def test_reporting_body_is_the_contract_verbatim(self) -> None:
        sections = {
            s.slug: s.body for s in INS.agents_managed_sections(target_layout="aw")
        }
        self.assertEqual(
            sections[INS.AW_REPORTING_SLUG].strip("\n"),
            RC.contract_text().strip("\n"),
        )

    def test_block_round_trips_through_the_parser(self) -> None:
        block = INS.agents_managed_block(target_layout="aw")
        parsed = INS.parse_aw_block(block)
        self.assertTrue(parsed.found)
        self.assertFalse(parsed.drift)
        self.assertFalse(parsed.ambiguous)
        self.assertEqual(
            [s.slug for s in parsed.sections],
            [INS.AW_POINTER_SLUG, INS.AW_REPORTING_SLUG],
        )

    def test_this_repos_agents_md_carries_the_section_inside_the_block(self) -> None:
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        start = text.find("<!-- aw:block -->")
        end = text.find("<!-- /aw:block -->")
        at = text.find("<!-- aw:reporting -->")
        self.assertGreater(at, start, "the section must be inside the managed block")
        self.assertLess(at, end)
        self.assertIn("Report to the user concisely.", text)


class InstallerSafetyTests(unittest.TestCase):
    """E-07/V-07: install, mirror, idempotence, absent-native, and the consent paths."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.source = SOURCE_WORKFLOWS

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _install(self, repo: Path) -> None:
        INS.install_into_repo(repo, self.source, yes=True, no_color=True)

    def test_fresh_install_writes_exactly_one_reporting_section(self) -> None:
        repo = init_repo(self.base / "fresh")
        self._install(repo)
        txt = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(txt.count("<!-- aw:reporting -->"), 1)
        self.assertEqual(txt.count("<!-- aw:pointer -->"), 1)
        self.assertIn("Report to the user concisely.", txt)

    def test_second_install_is_byte_idempotent(self) -> None:
        repo = init_repo(self.base / "idem")
        self._install(repo)
        first = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self._install(repo)
        second = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(first, second)
        self.assertEqual(second.count("<!-- aw:reporting -->"), 1)

    def test_existing_native_files_get_the_section_with_foreign_prose_preserved(
        self,
    ) -> None:
        repo = init_repo(self.base / "native")
        (repo / "CLAUDE.md").write_text("User CLAUDE prose\n", encoding="utf-8")
        (repo / "GEMINI.md").write_text("User GEMINI prose\n", encoding="utf-8")
        self._install(repo)
        for name, marker in (
            ("CLAUDE.md", "User CLAUDE prose"),
            ("GEMINI.md", "User GEMINI prose"),
        ):
            txt = (repo / name).read_text(encoding="utf-8")
            self.assertIn(marker, txt, f"{name} lost the user's own prose")
            self.assertEqual(txt.count("<!-- aw:reporting -->"), 1, name)
            self.assertIn("Report to the user concisely.", txt, name)

    def test_absent_native_files_are_still_not_created(self) -> None:
        repo = init_repo(self.base / "no-native")
        self._install(repo)
        self.assertFalse((repo / "CLAUDE.md").exists())
        self.assertFalse((repo / "GEMINI.md").exists())

    def test_foreign_sibling_block_stays_byte_identical(self) -> None:
        repo = init_repo(self.base / "sibling")
        sibling = (
            "<!-- AGENT-PLANS:BEGIN -->\n## Agent plans\npolicy text\n"
            "<!-- AGENT-PLANS:END -->\n"
        )
        (repo / "AGENTS.md").write_text(
            "# AGENTS\n\n" + sibling + "\nuser epilogue\n", encoding="utf-8"
        )
        self._install(repo)
        txt = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(sibling, txt)
        self.assertIn("user epilogue", txt)
        self.assertEqual(txt.count("<!-- aw:reporting -->"), 1)

    def test_declined_reporting_section_is_omitted_but_pointer_stays(self) -> None:
        """First sibling section to exercise the decline tombstone path."""

        from agent_workflows import manifest as M

        repo = init_repo(self.base / "declined")
        self._install(repo)
        mpath = repo / ".aw" / "system" / "managed-sections.json"
        man = M.load(mpath)
        man.mark_declined("AGENTS.md#aw:reporting", kind="section")
        M.save(man, mpath)
        (repo / "AGENTS.md").write_text("# AGENTS\n\nuser only\n", encoding="utf-8")
        self._install(repo)
        txt = (repo / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn(
            "<!-- aw:reporting -->", txt, "a declined section must not be written"
        )
        self.assertIn(
            "<!-- aw:pointer -->",
            txt,
            "declining one section must not drop its sibling",
        )

    def test_user_edited_reporting_body_is_preserved_not_clobbered(self) -> None:
        """First sibling section to exercise the user-drift preservation path."""

        repo = init_repo(self.base / "drift")
        self._install(repo)
        agents = repo / "AGENTS.md"
        txt = agents.read_text(encoding="utf-8")
        edited = txt.replace(
            "Report to the user concisely.",
            "MY OWN REPORTING RULE: be as verbose as you like.",
        )
        self.assertNotEqual(edited, txt, "fixture must actually change the body")
        agents.write_text(edited, encoding="utf-8")
        self._install(repo)
        after = agents.read_text(encoding="utf-8")
        self.assertIn(
            "MY OWN REPORTING RULE",
            after,
            "a user-edited aw:reporting body must be preserved",
        )
        self.assertNotIn("Report to the user concisely.", after)
        # The sibling pointer section is still refreshed normally.
        self.assertIn("<!-- aw:pointer -->", after)
        self.assertIn("## Agent workflows", after)

    def test_manifest_records_the_new_section_hash_as_an_install_side_effect(
        self,
    ) -> None:
        from agent_workflows import manifest as M

        repo = init_repo(self.base / "manifest")
        self._install(repo)
        man = M.load(repo / ".aw" / "system" / "managed-sections.json")
        self.assertIn("AGENTS.md#aw:reporting", man.files)
        self.assertTrue(
            man.matches_recorded("AGENTS.md#aw:reporting", RC.contract_text())
        )


class ShimPointerTests(unittest.TestCase):
    """E-03/V-03: shims carry a POINTER, keep their host grammar, and stay small."""

    def setUp(self) -> None:
        self.workflows = INS.parse_manifest(SOURCE_WORKFLOWS)
        self.by_command = {w.command: w for w in self.workflows}

    def test_pointer_line_names_the_managed_section(self) -> None:
        line = RC.shim_pointer_line()
        self.assertIn("AGENTS.md#aw:reporting", line)
        self.assertEqual(RC.POINTER_TARGET, "AGENTS.md#aw:reporting")
        self.assertTrue(line.endswith("\n"))
        self.assertEqual(len(line.splitlines()), 1, "the pointer must be ONE line")

    def test_pointer_mentions_the_required_report_override(self) -> None:
        """A shim reader who never resolves the pointer still learns the key exception."""

        self.assertIn("required reports still in full", RC.shim_pointer_line())

    def test_every_generated_shim_carries_the_pointer(self) -> None:
        corpus = _shim_corpus()
        self.assertGreaterEqual(len(corpus), 40, "unexpectedly small shim corpus")
        for rel, text in sorted(corpus.items()):
            self.assertIn(RC.POINTER_TARGET, text, f"{rel} lacks the reporting pointer")

    def test_no_shim_embeds_the_full_contract_prose(self) -> None:
        for rel, text in sorted(_shim_corpus().items()):
            self.assertNotIn(
                "Report to the user concisely.",
                text,
                f"{rel} embeds the contract prose; E-03 requires a POINTER",
            )

    def test_host_grammars_are_preserved(self) -> None:
        for rel, text in sorted(_shim_corpus().items()):
            tool = "opencode" if rel.startswith(".opencode/") else "claude"
            self.assertTrue(
                INS.validate_shim_grammar(text, tool), f"{rel} fails {tool} grammar"
            )
            if tool == "opencode":
                self.assertIn("agent: build", text, rel)
            else:
                self.assertNotIn("\nagent:", text, rel)

    def test_arguments_semantics_unchanged(self) -> None:
        for rel, text in sorted(_shim_corpus().items()):
            if "$ARGUMENTS" in text:
                self.assertIn("If the user provided arguments", text, rel)

    def test_claude_argument_hint_still_pairs_with_arguments(self) -> None:
        hinted = INS.shim_body(
            "plan-review",
            self.by_command["plan-review"],
            "claude",
            target_layout="aw",
        )
        self.assertIn("argument-hint:", hinted)
        self.assertIn("$ARGUMENTS", hinted)

    def test_pointer_bearing_shim_is_not_flagged_as_user_customized(self) -> None:
        """A regenerated shim must be recognized as installer-owned, not hand-edited."""

        for tool in ("opencode", "claude"):
            body = INS.shim_body(
                "plan-review",
                self.by_command["plan-review"],
                tool,
                target_layout="aw",
            )
            self.assertFalse(
                INS.is_shim_customized(body),
                f"{tool} shim with the generated pointer must not read as customized",
            )

    def test_dispatcher_shim_carries_the_pointer_for_both_hosts(self) -> None:
        for tool in ("opencode", "claude"):
            body = INS.aw_dispatcher_shim(self.workflows, tool, target_layout="aw")
            self.assertIn(RC.POINTER_TARGET, body, tool)
            self.assertTrue(INS.validate_shim_grammar(body, tool), tool)
            self.assertNotIn("Report to the user concisely.", body, tool)

    def test_shim_corpus_size_budget(self) -> None:
        """The anti-duplication BUDGET guard (E-08). Copying the prose blows this up."""

        corpus = _shim_corpus()
        total = sum(len(t.encode("utf-8")) for t in corpus.values())
        allowance = SHIM_POINTER_BUDGET_BYTES_PER_FILE * len(corpus)
        ceiling = SHIM_CORPUS_BASELINE_BYTES + allowance
        self.assertLessEqual(
            total,
            ceiling,
            f"shim corpus is {total} bytes across {len(corpus)} files, over the "
            f"{ceiling}-byte ceiling (baseline {SHIM_CORPUS_BASELINE_BYTES} + "
            f"{SHIM_POINTER_BUDGET_BYTES_PER_FILE}/file). The contract prose was "
            "probably duplicated into the shims; E-03 requires a pointer.",
        )

    def test_per_shim_growth_is_one_short_line(self) -> None:
        pointer_bytes = len(RC.shim_pointer_line().encode("utf-8"))
        self.assertLessEqual(pointer_bytes, SHIM_POINTER_BUDGET_BYTES_PER_FILE)

    def test_budget_guard_actually_fails_on_duplication(self) -> None:
        """A guard never observed failing is not proven: simulate the regression."""

        corpus = _shim_corpus()
        duplicated = {rel: text + RC.contract_text() for rel, text in corpus.items()}
        total = sum(len(t.encode("utf-8")) for t in duplicated.values())
        ceiling = SHIM_CORPUS_BASELINE_BYTES + SHIM_POINTER_BUDGET_BYTES_PER_FILE * len(
            duplicated
        )
        self.assertGreater(
            total,
            ceiling,
            "duplicating the prose into every shim MUST breach the budget ceiling",
        )


class DriverPromptTests(unittest.TestCase):
    """E-04/V-04: both drivers embed the contract in execution AND verifier prompts."""

    DRIVERS = (oc_runipd, agy_runipd)

    def _item(self) -> dict:
        return {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}

    def _state(self) -> dict:
        return {"run_id": "run-20260101T000000Z-1", "repo": "."}

    def _exec_prompt(self, mod) -> str:
        return mod.build_prompt(
            self._item(),
            self._state(),
            Path("/tmp/run-dir"),
            Path("/tmp/repo/plan.ipd.md"),
            False,
        )

    def _verifier_prompt(self, mod) -> str:
        return mod.build_verifier_prompt(
            self._item(),
            self._state(),
            Path("/tmp/run-dir"),
            Path("/tmp/repo/plan.ipd.md"),
        )

    def test_execution_prompts_carry_the_contract(self) -> None:
        for mod in self.DRIVERS:
            self.assertIn(
                RC.contract_text().strip("\n"),
                self._exec_prompt(mod),
                f"{mod.__name__} execution prompt lacks the contract",
            )

    def test_verifier_prompts_carry_the_contract(self) -> None:
        for mod in self.DRIVERS:
            self.assertIn(
                RC.contract_text().strip("\n"),
                self._verifier_prompt(mod),
                f"{mod.__name__} verifier prompt lacks the contract",
            )

    def test_execution_prompts_retain_required_json_keys_and_rules(self) -> None:
        required = (
            '"schema_version": 1',
            '"disposition"',
            '"files_changed"',
            '"tests"',
            '"decision_ids"',
            '"deferred_question_ids"',
            '"incomplete_requirements"',
            '"recommended_next_action"',
            '"pushed": false',
            "## Concurrent Work",
            "git diff --cached --name-only",
            "path-scoped",
        )
        for mod in self.DRIVERS:
            prompt = self._exec_prompt(mod)
            for needle in required:
                self.assertIn(needle, prompt, f"{mod.__name__}: lost {needle!r}")

    def test_verifier_prompts_retain_evidence_requirements(self) -> None:
        required = (
            '"verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED"',
            "Paste the actual runner output with exit code.",
            "Evidence Table",
            "Begin independent verification now.",
        )
        for mod in self.DRIVERS:
            prompt = self._verifier_prompt(mod)
            for needle in required:
                self.assertIn(needle, prompt, f"{mod.__name__}: lost {needle!r}")

    def test_prompts_are_pure_ascii(self) -> None:
        for mod in self.DRIVERS:
            for label, prompt in (
                ("exec", self._exec_prompt(mod)),
                ("verifier", self._verifier_prompt(mod)),
            ):
                bad = sorted({c for c in prompt if ord(c) > 127})
                self.assertEqual(bad, [], f"{mod.__name__} {label}: {bad}")

    def test_review_prompt_is_exactly_the_slash_command(self) -> None:
        """E-05 regression guard: prose here would be parsed as $ARGUMENTS."""

        for mod in self.DRIVERS:
            value = mod.build_review_prompt(
                self._item(),
                self._state(),
                Path("/tmp/run-dir"),
                Path("/tmp/repo/plans/plan.ipd.md"),
                Path("/tmp/repo"),
            )
            self.assertRegex(value, r"^/plan-review \S+$")
            self.assertEqual(value, "/plan-review plans/plan.ipd.md")
            self.assertNotIn("Report to the user concisely.", value)


class ParityTests(unittest.TestCase):
    """E-08/V-08: every surface derives from the ONE source; no second copy exists."""

    def test_drivers_import_the_module_rather_than_inlining_the_prose(self) -> None:
        for rel in ("agent_workflows/oc_runipd.py", "agent_workflows/agy_runipd.py"):
            src = (REPO_ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("from agent_workflows import reporting_contract", src, rel)
            self.assertIn("reporting_contract.prompt_block()", src, rel)
            self.assertNotIn("Report to the user concisely.", src, rel)

    def test_engine_renders_the_section_from_the_module(self) -> None:
        src = (REPO_ROOT / "agent_workflows/engine.py").read_text(encoding="utf-8")
        self.assertIn("reporting_contract.contract_text()", src)
        self.assertIn("reporting_contract.shim_pointer_line()", src)
        self.assertNotIn("Report to the user concisely.", src)

    def test_all_prose_surfaces_are_byte_equal_to_the_source(self) -> None:
        canonical = RC.contract_text().strip("\n")
        surfaces = {
            "aw:reporting section": {
                s.slug: s.body for s in INS.agents_managed_sections(target_layout="aw")
            }[INS.AW_REPORTING_SLUG].strip("\n"),
        }
        item = {"position": 1, "id6": "abc123", "setid": "demo", "attempts": []}
        state = {"run_id": "run-x", "repo": "."}
        for mod in (oc_runipd, agy_runipd):
            exec_prompt = mod.build_prompt(
                item, state, Path("/tmp/r"), Path("/tmp/p.md"), False
            )
            verifier = mod.build_verifier_prompt(
                item, state, Path("/tmp/r"), Path("/tmp/p.md")
            )
            for label, prompt in (
                (f"{mod.__name__} exec", exec_prompt),
                (f"{mod.__name__} verifier", verifier),
            ):
                start = prompt.find(RC.REPORTING_SECTION_TITLE)
                self.assertGreater(start, -1, f"{label} lacks the contract heading")
                surfaces[label] = prompt[start:].strip("\n")
        for label, text in surfaces.items():
            self.assertEqual(text, canonical, f"{label} drifted from the source")

    def test_only_expected_files_contain_the_full_contract_prose(self) -> None:
        """A new independently maintained copy anywhere in the tree fails this."""

        sentence = "Report to the user concisely."
        allowed = {
            "agent_workflows/reporting_contract.py",
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
        }
        found = set()
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in (".py", ".md"):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel.startswith((".git/", ".aw/records/", ".aw/worktrees/", "tests/")):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if sentence in text:
                found.add(rel)
        unexpected = sorted(found - allowed)
        self.assertEqual(
            unexpected,
            [],
            "unexpected copies of the contract prose (use a pointer or the module): "
            f"{unexpected}",
        )

    def test_parity_check_detects_a_mutated_copy(self) -> None:
        """Falsifiability: a mutated rendered copy must NOT compare equal."""

        canonical = RC.contract_text()
        mutated = canonical.replace("Lead with the OUTCOME", "Lead with a preamble")
        self.assertNotEqual(mutated, canonical)
        self.assertNotRegex(mutated, re.escape("Lead with the OUTCOME"))


class DocumentationTests(unittest.TestCase):
    """E-09/V-09: the docs describe the policy and POINT at the source module."""

    DOC = REPO_ROOT / "docs/reporting-contract.md"

    def test_doc_exists_and_is_linked_from_the_docs_index(self) -> None:
        self.assertTrue(self.DOC.is_file(), "docs/reporting-contract.md must exist")
        index = (REPO_ROOT / "docs/README.md").read_text(encoding="utf-8")
        self.assertIn("reporting-contract.md", index)

    def test_doc_points_at_the_source_without_forking_the_prose(self) -> None:
        text = self.DOC.read_text(encoding="utf-8")
        self.assertIn("agent_workflows/reporting_contract.py", text)
        self.assertNotIn(
            "Report to the user concisely.",
            text,
            "the doc must POINT at the contract, not fork its prose",
        )

    def test_doc_records_the_rejected_alternatives(self) -> None:
        text = self.DOC.read_text(encoding="utf-8")
        for needle in (
            "~/.config/opencode",
            "textVerbosity",
            "output-token",
            "cli-output-contract.md",
        ):
            self.assertIn(needle, text, f"the doc must address {needle!r}")

    def test_doc_records_the_pointer_not_copy_decision(self) -> None:
        text = self.DOC.read_text(encoding="utf-8")
        self.assertIn("pointer", text.lower())
        self.assertIn("AGENTS.md#aw:reporting", text)

    def test_doc_states_the_honest_limit(self) -> None:
        text = self.DOC.read_text(encoding="utf-8").lower()
        self.assertIn("deterministic", text)
        self.assertTrue(
            "obedience" in text or "probabilistic" in text,
            "the doc must state that delivery is provable but compliance is not",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
