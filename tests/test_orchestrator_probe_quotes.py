"""Tests for orchestrator coverage probe quotes and named-child credit (IPD 8mabmu E-01..E-07)."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import coverage_record
from agent_workflows import runner_shared as rs


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


ORCHESTRATOR_FIXTURE_TEXT = """# IPD: Conforming orchestrator fixture

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Priority: medium
- Work-Kind: chore
- Status: approved
- Set: fixconf
- Order: 0
- Highest E allocated: 02
- Author: fixture
- Id: fix001
- Approval: 2026-09-24, fixture

## Workflow history

- 2026-09-24 approved (fixture): created.

## Goal

Fixture orchestrator.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  - Depends on: none
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-02 CONFIRM chd002 REACHED executed
  - Depends: E-01
  - Expected outcome: chd002 reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixconf-01-chd001.ipd.md | none |
| 02 | chd002 | pending | .aw/records/plans/pending/20260924-fixconf-02-chd002.ipd.md | 01 |

## Completion criteria (the whole Set is done only when)

- None.

## Cross-IPD validation

- None.

## Deferred / out of scope (with reason)

- None.

## Scope check

- None.

## Required tests / validation

- None.

## Open questions

- None.

## Validation and cross-check (verify before reporting the Set complete)

- [ ] V-01 validates E-01
  - Required evidence: check baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- None.
"""


NAMED_CHILD_ORCH_TEXT = """# IPD: Named child credit fixture

- Date: 2026-09-24
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: none
- Priority: medium
- Work-Kind: chore
- Status: approved
- Set: fixcred
- Order: 0
- Highest E allocated: 02
- Author: fixture
- Id: cred01
- Approval: 2026-09-24, fixture

## Workflow history

- 2026-09-24 approved (fixture): created.

## Goal

Fixture orchestrator with named child credit.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 CONFIRM chd001 REACHED executed
  - Depends on: none
  - Expected outcome: chd001 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-02 CONFIRM chd002 REACHED executed
  - Depends: E-01
  - Expected outcome: chd002 reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
| --- | --- | --- | --- | --- |
| 01 | chd001 | pending | .aw/records/plans/pending/20260924-fixcred-01-chd001.ipd.md | none |
| 02 | chd002 | pending | .aw/records/plans/pending/20260924-fixcred-02-chd002.ipd.md | 01 |

## Completion criteria (the whole Set is done only when)

- None.

## Cross-IPD validation

- None.

## Deferred / out of scope (with reason)

- None.

## Scope check

- None.

## Required tests / validation

THE SET IS ONLY DEMONSTRATED COMPLETE BY A FINAL CROSS-CHILD MEASUREMENT, which Order 02 carries as the last child.

## Open questions

- None.

## Validation and cross-check (verify before reporting the Set complete)

- [ ] V-01 validates E-01
  - Required evidence: check baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- None.
"""


class TestClassifyProbeReplyTable(unittest.TestCase):
    """Test classifier table against rs.classify_probe_reply (E-02)."""

    def setUp(self) -> None:
        self.excerpt = (
            "### Detailed Implementation Checklist\n"
            "- [ ] E-01 Uncovered obligation in orchestrator checklist\n"
            "This is a second passage across multiple\n"
            "lines in the excerpt."
        )

    def test_positive_one_valid_quote(self) -> None:
        raw = (
            f"{rs.PROBE_SENTINEL_EXECUTIONS}\n"
            f"QUOTE: - [ ] E-01 Uncovered obligation in orchestrator checklist"
        )
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_EXECUTIONS)
        self.assertEqual(
            res.quotes,
            ("- [ ] E-01 Uncovered obligation in orchestrator checklist",),
        )
        self.assertEqual(res.discarded, 0)

    def test_positive_zero_quotes(self) -> None:
        raw = rs.PROBE_SENTINEL_EXECUTIONS
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertEqual(res.quotes, ())
        self.assertEqual(res.discarded, 0)

    def test_positive_only_quote_absent_from_excerpt(self) -> None:
        raw = (
            f"{rs.PROBE_SENTINEL_EXECUTIONS}\n"
            f"QUOTE: this sentence does not exist anywhere in excerpt"
        )
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertEqual(res.quotes, ())
        self.assertEqual(res.discarded, 1)

    def test_positive_one_valid_and_one_invalid_quote(self) -> None:
        raw = (
            f"{rs.PROBE_SENTINEL_EXECUTIONS}\n"
            f"QUOTE: - [ ] E-01 Uncovered obligation in orchestrator checklist\n"
            f"QUOTE: this sentence does not exist anywhere in excerpt"
        )
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_EXECUTIONS)
        self.assertEqual(
            res.quotes,
            ("- [ ] E-01 Uncovered obligation in orchestrator checklist",),
        )
        self.assertEqual(res.discarded, 1)

    def test_positive_non_quote_trailing_line(self) -> None:
        raw = (
            f"{rs.PROBE_SENTINEL_EXECUTIONS}\n"
            f"QUOTE: - [ ] E-01 Uncovered obligation in orchestrator checklist\n"
            f"Here is some extra unquoted explanation that violates format"
        )
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertEqual(res.quotes, ())

    def test_negative_alone(self) -> None:
        raw = rs.PROBE_SENTINEL_NO_EXECUTIONS
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_NO_EXECUTIONS)
        self.assertEqual(res.quotes, ())
        self.assertEqual(res.discarded, 0)

    def test_negative_trailing_line(self) -> None:
        raw = (
            f"{rs.PROBE_SENTINEL_NO_EXECUTIONS}\n"
            f"Everything is well covered by the children"
        )
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertEqual(res.quotes, ())

    def test_both_sentinels_anywhere(self) -> None:
        raw = f"{rs.PROBE_SENTINEL_NO_EXECUTIONS}\n" f"{rs.PROBE_SENTINEL_EXECUTIONS}"
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_UNKNOWN)
        self.assertEqual(res.quotes, ())

    def test_empty_or_whitespace_reply(self) -> None:
        res = rs.classify_probe_reply("   \n\n  ", excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_COULD_NOT_ASK)
        self.assertEqual(res.quotes, ())

    def test_whitespace_normalization_in_quote_validation(self) -> None:
        raw = (
            f"{rs.PROBE_SENTINEL_EXECUTIONS}\n"
            f"QUOTE: This is a second passage across multiple lines in the excerpt."
        )
        res = rs.classify_probe_reply(raw, excerpt=self.excerpt)
        self.assertEqual(res.answer, rs.PROBE_ANSWER_EXECUTIONS)
        self.assertEqual(
            res.quotes,
            ("This is a second passage across multiple lines in the excerpt.",),
        )


class TestProbeOrchestratorPlanRecord(unittest.TestCase):
    """Test probe_orchestrator caching in plan, legacy 2-tuples, and store retirement (E-07)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _init_git(self.repo)
        plans_dir = self.repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_path = plans_dir / "20260924-fixconf-00-fix001.ipd.md"
        self.plan_path.write_text(ORCHESTRATOR_FIXTURE_TEXT, encoding="utf-8")
        _commit_all(self.repo, "init")

        self.state = {
            "queue": [
                {
                    "id6": "fix001",
                    "kind": "orchestrator",
                    "position": 1,
                    "setid": "fixconf",
                    "configured_file": str(self.plan_path),
                }
            ],
            "options": {"model": "claude-sonnet-4-6"},
        }

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_second_run_is_free_and_reads_quotes_from_plan(self) -> None:
        ask_count = 0
        uncovered_quote = "E-01 CONFIRM chd001 REACHED executed"

        def fake_asker(state, excerpt, host, repo, runner=None):
            nonlocal ask_count
            ask_count += 1
            return (
                rs.PROBE_ANSWER_EXECUTIONS,
                "found uncovered obligation",
                (uncovered_quote,),
            )

        target1 = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )
        outcome1 = rs.probe_orchestrator(
            self.state,
            target1,
            repo=self.repo,
            host="oc",
            retry_budget=0,
            asker=fake_asker,
        )
        self.assertEqual(outcome1.calls, 1)
        self.assertFalse(outcome1.cached)
        self.assertEqual(outcome1.quotes, (uncovered_quote,))

        # Verify plan on disk carries coverage record
        self.assertIn("- Coverage: fail", self.plan_path.read_text(encoding="utf-8"))

        # Second call with new target read from disk
        target2 = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )

        def exploding_asker(*args, **kwargs):
            raise AssertionError(
                "asker should not be called when plan record is current"
            )

        outcome2 = rs.probe_orchestrator(
            self.state,
            target2,
            repo=self.repo,
            host="oc",
            retry_budget=0,
            asker=exploding_asker,
        )
        self.assertEqual(outcome2.calls, 0)
        self.assertTrue(outcome2.cached)
        self.assertEqual(outcome2.quotes, (uncovered_quote,))

    def test_edited_plan_is_asked_again(self) -> None:
        # First write current record
        coverage_record.write(
            self.plan_path,
            "pass",
            quotes=(),
            model="test-model",
            tool="aw oc run",
            commit=True,
            repo=self.repo,
        )
        # Verify current
        t_clean = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )
        self.assertTrue(coverage_record.is_current(t_clean.text))

        # Edit checklist in plan
        edited_text = t_clean.text.replace("- [ ] E-01 ", "- [ ] E-01 edited ", 1)
        self.plan_path.write_text(edited_text, encoding="utf-8")
        _commit_all(self.repo, "edit checklist")

        target_edited = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )
        self.assertFalse(coverage_record.is_current(target_edited.text))

        ask_count = 0

        def fake_asker(state, excerpt, host, repo, runner=None):
            nonlocal ask_count
            ask_count += 1
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "all covered", ())

        outcome = rs.probe_orchestrator(
            self.state,
            target_edited,
            repo=self.repo,
            host="oc",
            retry_budget=0,
            asker=fake_asker,
        )
        self.assertEqual(ask_count, 1)
        self.assertEqual(outcome.calls, 1)
        self.assertFalse(outcome.cached)
        self.assertEqual(outcome.answer, rs.PROBE_ANSWER_NO_EXECUTIONS)

    def test_two_tuple_asker_compatibility(self) -> None:
        def two_tuple_asker(state, excerpt, host, repo, runner=None):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "all covered")

        target = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )
        outcome = rs.probe_orchestrator(
            self.state,
            target,
            repo=self.repo,
            host="oc",
            retry_budget=0,
            asker=two_tuple_asker,
        )
        self.assertEqual(outcome.answer, rs.PROBE_ANSWER_NO_EXECUTIONS)
        self.assertEqual(outcome.quotes, ())

    def test_legacy_two_tuple_executions_blocks_without_recording(self) -> None:
        def legacy_executions_asker(state, excerpt, host, repo, runner=None):
            return (rs.PROBE_ANSWER_EXECUTIONS, "uncovered work found")

        target = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )
        outcome = rs.probe_orchestrator(
            self.state,
            target,
            repo=self.repo,
            host="oc",
            retry_budget=0,
            asker=legacy_executions_asker,
        )
        self.assertEqual(outcome.answer, rs.PROBE_ANSWER_EXECUTIONS)
        self.assertTrue(outcome.blocks)
        self.assertEqual(outcome.quotes, ())

        # Must NOT be recorded in the plan
        plan_after = self.plan_path.read_text(encoding="utf-8")
        self.assertNotIn("- Coverage:", plan_after)
        self.assertNotIn("## Coverage findings", plan_after)

    def test_store_file_not_written(self) -> None:
        store_path = (
            self.repo / ".aw" / "state" / "runtime" / "orchestrator-probe-verdicts.json"
        )
        self.assertFalse(store_path.exists())


class TestGitCommitOnWriteAndDirtyPlan(unittest.TestCase):
    """Test git commit on write and dirty plan protection (E-07)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _init_git(self.repo)
        plans_dir = self.repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_path = plans_dir / "20260924-fixconf-00-fix001.ipd.md"
        self.plan_path.write_text(ORCHESTRATOR_FIXTURE_TEXT, encoding="utf-8")
        _commit_all(self.repo, "init")

        self.state = {
            "queue": [
                {
                    "id6": "fix001",
                    "kind": "orchestrator",
                    "position": 1,
                    "setid": "fixconf",
                    "configured_file": str(self.plan_path),
                }
            ],
            "options": {"model": "test-model"},
        }

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_commit_on_write_leaves_plan_clean(self) -> None:
        target = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )

        def fake_asker(state, excerpt, host, repo, runner=None):
            return (
                rs.PROBE_ANSWER_EXECUTIONS,
                "found uncovered obligation",
                ("E-01 CONFIRM chd001 REACHED executed",),
            )

        outcome = rs.probe_orchestrator(
            self.state,
            target,
            repo=self.repo,
            host="oc",
            retry_budget=0,
            asker=fake_asker,
        )
        self.assertEqual(outcome.answer, rs.PROBE_ANSWER_EXECUTIONS)

        # Plan file should be clean in git status
        st_res = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                str(self.plan_path.relative_to(self.repo)),
            ],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(st_res.stdout.strip(), "")

        # Latest commit for this plan should be the coverage commit
        log_res = subprocess.run(
            [
                "git",
                "log",
                "-1",
                "--format=%s",
                "--",
                str(self.plan_path.relative_to(self.repo)),
            ],
            cwd=str(self.repo),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(
            log_res.stdout.strip(),
            "coverage(oc): record the coverage answer for fix001",
        )

    def test_dirty_plan_is_not_written_or_committed(self) -> None:
        # Add uncommitted modification to plan file
        dirty_content = (
            self.plan_path.read_text(encoding="utf-8") + "\n<!-- uncommitted edit -->\n"
        )
        self.plan_path.write_text(dirty_content, encoding="utf-8")

        target = rs.ProbeTarget(
            id6="fix001",
            position=1,
            setid="fixconf",
            path=self.plan_path,
            text=self.plan_path.read_text(encoding="utf-8"),
        )

        def fake_asker(state, excerpt, host, repo, runner=None):
            return (
                rs.PROBE_ANSWER_EXECUTIONS,
                "found uncovered obligation",
                ("E-01 CONFIRM chd001 REACHED executed",),
            )

        outcome = rs.probe_orchestrator(
            self.state,
            target,
            repo=self.repo,
            host="oc",
            retry_budget=0,
            asker=fake_asker,
        )
        self.assertTrue(outcome.written)
        self.assertFalse(outcome.committed)
        self.assertTrue(outcome.write_attempted)
        self.assertIn(
            "already has uncommitted changes; record written without commit",
            outcome.write_detail,
        )
        # Content has the dirty edit AND the - Coverage: line added without commit
        plan_content_now = self.plan_path.read_text(encoding="utf-8")
        self.assertIn("- Coverage: fail", plan_content_now)
        self.assertIn("<!-- uncommitted edit -->", plan_content_now)


class TestEnforceOrchestratorProbeGateEndToEnd(unittest.TestCase):
    """Test enforce_orchestrator_probe_gate with quotes in refusal (E-04)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _init_git(self.repo)
        plans_dir = self.repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_path = plans_dir / "20260924-fixconf-00-fix001.ipd.md"
        self.plan_path.write_text(ORCHESTRATOR_FIXTURE_TEXT, encoding="utf-8")
        _commit_all(self.repo, "init")

        self.state = {
            "queue": [
                {
                    "id6": "fix001",
                    "kind": "orchestrator",
                    "position": 1,
                    "setid": "fixconf",
                    "configured_file": str(self.plan_path),
                }
            ],
            "options": {"model": "test-model"},
        }
        self.run_dir = rs.state_root(self.repo) / "run-test"
        self.run_dir.mkdir(parents=True)
        (self.run_dir / "events.jsonl").touch()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_refusal_reason_and_message_contain_quote_and_remedy(self) -> None:
        uncovered_passage = "- [ ] E-01 CONFIRM chd001 REACHED executed"

        def fake_asker(state, excerpt, host, repo, runner=None):
            return (
                rs.PROBE_ANSWER_EXECUTIONS,
                "uncovered work found",
                (uncovered_passage,),
            )

        decision = rs.enforce_orchestrator_probe_gate(
            self.run_dir,
            self.state,
            repo=self.repo,
            host="oc",
            interactive=False,
            write_report_fn=lambda *a: None,
            asker=fake_asker,
            color=False,
        )
        self.assertFalse(decision.proceed)

        # Message contains the quote and the id6
        self.assertIn("fix001", decision.message)
        self.assertIn(f'"{uncovered_passage}"', decision.message)

        # Message contains the remedy instructions
        self.assertIn(
            "assign this obligation by id6 to a child in the `## Child IPDs` table, or add a child that performs it",
            decision.message,
        )
        self.assertIn("do not delete the checklist", decision.message)

        # Refusal reason recorded in state.json refusal has quotes and remedy clause
        state_item = self.state["queue"][0]
        self.assertIn("refusal", state_item)
        refusal_reason = state_item["refusal"]["reason"]
        self.assertIn(
            "the orchestrator coverage probe reports that fix001 carries work no child covers",
            refusal_reason,
        )
        self.assertIn(f'[fix001] "{uncovered_passage}"', refusal_reason)
        self.assertIn(
            "Remedy: assign this obligation by id6 to a child in the `## Child IPDs` table",
            refusal_reason,
        )


class TestNamedChildCreditRule(unittest.TestCase):
    """Test named-child credit rule by Order number in prompt and gate (E-01)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _init_git(self.repo)
        plans_dir = self.repo / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.plan_path = plans_dir / "20260924-fixcred-00-cred01.ipd.md"
        self.plan_path.write_text(NAMED_CHILD_ORCH_TEXT, encoding="utf-8")
        _commit_all(self.repo, "init")

        self.state = {
            "queue": [
                {
                    "id6": "cred01",
                    "kind": "orchestrator",
                    "position": 1,
                    "setid": "fixcred",
                    "configured_file": str(self.plan_path),
                }
            ],
            "options": {"model": "test-model"},
        }
        self.run_dir = rs.state_root(self.repo) / "run-test"
        self.run_dir.mkdir(parents=True)
        (self.run_dir / "events.jsonl").touch()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_rendered_prompt_contains_child_table_and_named_child_rule(self) -> None:
        captured_prompt = ""

        def fake_runner(argv, cwd, timeout):
            nonlocal captured_prompt
            captured_prompt = [arg for arg in argv if "Child IPDs table" in arg][0]
            # Verify named-child rule instructions are in prompt
            self.assertIn(
                "naming that child by its id6 OR by an Order number", captured_prompt
            )
            self.assertIn("Order column", captured_prompt)
            self.assertIn("chd002", captured_prompt)
            self.assertIn("Order 02 carries", captured_prompt)
            return (0, rs.PROBE_SENTINEL_NO_EXECUTIONS, "")

        def fake_asker(state, excerpt, host, repo, runner=None):
            return rs.ask_orchestrator_probe(
                state, excerpt, host=host, repo=repo, runner=fake_runner
            )

        decision = rs.enforce_orchestrator_probe_gate(
            self.run_dir,
            self.state,
            repo=self.repo,
            host="oc",
            interactive=False,
            write_report_fn=lambda *a: None,
            asker=fake_asker,
            color=False,
        )
        self.assertTrue(decision.proceed)
        self.assertTrue(captured_prompt)
