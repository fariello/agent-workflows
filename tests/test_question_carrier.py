# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for emergent question carrier in worker outcome file (qchan-01 0jooqz E-01..E-06).

Guards that:
1. Pure validator validate_questions never raises and returns QuestionsVerdict (valid, absent, malformed).
2. Question bounds, required keys, id6 validation, item_id6 match, duplicate id detection, and 20-entry cap.
3. Deterministic question_fingerprint with Unicode NFKC, casefolding, whitespace collapsing, trailing
   punctuation stripping, and sorted normalized option labels, identical on both hosts.
4. Rendered execute prompts on both hosts cite askme three-way sort and contain questions[] schema literal,
   with no contradictory deferred question instruction.
5. Review prompts are byte-identical when non-isolated and carry lane outcome path when isolated.
6. Driver intake in execute_item_core records attempt["questions_verdict"] for execute and review turns,
   enforces freshness, emits questions-malformed event for malformed questions, and treats stale outcomes as absent.
7. A30 carrier separation: AW_MISSING_INPUT token vs questions[] array remain completely disjoint.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


from agent_workflows import agy_runipd, lane_containment, oc_runipd, runner_shared
from tests.support import coordinator_role


def _create_test_repo(root: Path) -> Path:
    """Initialize a git repo with required .aw structure and commit."""
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)

    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/runs/\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")

    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "backlog" / "open").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "pending" / ".gitkeep").write_text(
        "", encoding="utf-8"
    )
    (repo / ".aw" / "records" / "backlog" / "open" / ".gitkeep").write_text(
        "", encoding="utf-8"
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "initial repo commit"], cwd=repo, check=True
    )
    return repo


def _create_plan_file(
    repo: Path,
    id6: str,
    *,
    setid: str = "testset",
    order: int = 1,
    status: str = "approved",
    action: str = "execute",
) -> Path:
    """Create a conforming plan file under .aw/records/plans/pending/."""
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / f"20261017-{setid}-{order:02d}-{id6}-plan.ipd.md"

    content = f"""# IPD: Test Plan {id6}

- Kind: child
- Status: {status}
- Set: {setid}
- Order: {order}
- Id: {id6}
- Priority: medium
- Work-Kind: feature
- Scope-Paths: README.md

## Detailed Implementation Checklist (TODO)
- [ ] E-01 Do work
- [ ] V-01 Verify work
"""
    plan_path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True)
    return plan_path


def _make_fake_agent_script(tmp_path: Path) -> Path:
    """Create a fake agent script that handles prompts, outcomes, and tokens."""
    from tests import support

    return support.make_fake_executable(
        tmp_path / "fake_agent",
        """#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path

# Print standard stream lines
print(json.dumps({"event": "init", "conversation_id": "ses-1", "init": {"model": "test-model"}}), flush=True)
print(json.dumps({"type": "text", "sessionID": "ses-1", "part": {"text": "working"}}), flush=True)

all_text = ""
for arg in sys.argv[1:]:
    if "Required JSON outcome:" in arg:
        all_text = arg
        break
    if Path(arg).is_file():
        try:
            content = Path(arg).read_text(encoding="utf-8")
            if "Required JSON outcome:" in content:
                all_text = content
                break
        except Exception:
            pass

payload_file = os.environ.get("FAKE_PAYLOAD_FILE")
payload_json = os.environ.get("FAKE_PAYLOAD_JSON")
emit_token = os.environ.get("FAKE_EMIT_TOKEN")

if emit_token:
    print(emit_token, flush=True)

if payload_file and Path(payload_file).is_file():
    payload_content = Path(payload_file).read_text(encoding="utf-8")
elif payload_json is not None:
    payload_content = payload_json
else:
    payload_content = json.dumps({"disposition": "executed", "defect_report": {"state": "none-found", "findings": []}, "pushed": False})

if payload_content != "__SUPPRESS_OUTCOME__" and all_text:
    m = re.search(r"Required JSON outcome: (\\S+)", all_text)
    if m:
        p = Path(m.group(1))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(payload_content, encoding="utf-8")

    m_pos = re.search(r"Queue position: (\\d+)", all_text)
    m_id6 = re.search(r"Assigned IPD: (\\w+)", all_text)
    m_rd = re.search(r"(?:Run directory|Run root): (\\S+)", all_text)
    if m_pos and m_id6 and m_rd:
        pos = int(m_pos.group(1))
        id6 = m_id6.group(1)
        rd = Path(m_rd.group(1))
        out_dir = rd / "outcomes"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{pos:02d}-{id6}.json").write_text(payload_content, encoding="utf-8")

sys.exit(0)
""",
    )


class TestQuestionValidator(unittest.TestCase):
    """E-01: Pure validator unit tests for validate_questions."""

    def setUp(self) -> None:
        self.item_id6 = "0jooqz"
        self.valid_q = {
            "question_id": "q-design",
            "text": "Which architecture pattern should be adopted?",
            "artifact_id6": self.item_id6,
            "gates_verdict": True,
            "evidence": ["spec 6kwd2e R2.1", "plan 0jooqz E-01"],
            "options": ["Pattern A", "Pattern B"],
            "allow_free_text": True,
        }

    def test_absent_questions(self) -> None:
        """Absent verdict for None, empty mapping, empty list, or None questions key."""
        for empty_val in (None, {}, {"questions": None}, {"questions": []}, []):
            v = runner_shared.validate_questions(empty_val, item_id6=self.item_id6)
            self.assertTrue(v.is_absent)
            self.assertFalse(v.is_valid)
            self.assertFalse(v.is_malformed)
            self.assertEqual(v.questions, ())
            self.assertEqual(v.violations, ())

    def test_valid_single_and_multiple_questions(self) -> None:
        """Valid verdict for conforming question entries."""
        v1 = runner_shared.validate_questions(
            {"questions": [self.valid_q]}, item_id6=self.item_id6
        )
        self.assertTrue(v1.is_valid)
        self.assertFalse(v1.is_absent)
        self.assertFalse(v1.is_malformed)
        self.assertEqual(len(v1.questions), 1)
        self.assertEqual(v1.violations, ())
        q = v1.questions[0]
        self.assertEqual(q["question_id"], "q-design")
        self.assertEqual(q["artifact_id6"], self.item_id6)
        self.assertTrue(q["gates_verdict"])
        self.assertEqual(q["evidence"], ["spec 6kwd2e R2.1", "plan 0jooqz E-01"])
        self.assertEqual(q["options"], ["Pattern A", "Pattern B"])
        self.assertTrue(q["allow_free_text"])
        self.assertTrue(len(q["fingerprint"]) == 16)

        # Multiple questions
        q2 = dict(self.valid_q)
        q2["question_id"] = "q-schema"
        v2 = runner_shared.validate_questions(
            {"questions": [self.valid_q, q2]}, item_id6=self.item_id6
        )
        self.assertTrue(v2.is_valid)
        self.assertEqual(len(v2.questions), 2)

    def test_malformed_missing_required_fields(self) -> None:
        """Each missing required field yields a diagnostic naming the field."""
        required_fields = [
            "question_id",
            "text",
            "artifact_id6",
            "gates_verdict",
            "evidence",
        ]
        for field in required_fields:
            bad_q = dict(self.valid_q)
            del bad_q[field]
            v = runner_shared.validate_questions(
                {"questions": [bad_q]}, item_id6=self.item_id6
            )
            self.assertTrue(v.is_malformed)
            self.assertEqual(len(v.violations), 1)
            self.assertIn(field, v.violations[0])

    def test_malformed_over_length_and_empty_text(self) -> None:
        """Over-length text (> 2000 chars) and empty text yield named violations."""
        bad_over = dict(self.valid_q, text="x" * 2001)
        v_over = runner_shared.validate_questions(
            {"questions": [bad_over]}, item_id6=self.item_id6
        )
        self.assertTrue(v_over.is_malformed)
        self.assertIn("text", v_over.violations[0])
        self.assertIn("exceeds 2000", v_over.violations[0])

        bad_empty = dict(self.valid_q, text="   ")
        v_empty = runner_shared.validate_questions(
            {"questions": [bad_empty]}, item_id6=self.item_id6
        )
        self.assertTrue(v_empty.is_malformed)
        self.assertIn("text", v_empty.violations[0])
        self.assertIn("empty", v_empty.violations[0])

    def test_malformed_invalid_question_id(self) -> None:
        """Question_id must match [A-Za-z0-9._-]{1,40}."""
        bad_chars = dict(self.valid_q, question_id="bad id with spaces!")
        v = runner_shared.validate_questions(
            {"questions": [bad_chars]}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_malformed)
        self.assertIn("question_id", v.violations[0])

    def test_malformed_bad_artifact_id6(self) -> None:
        """Artifact_id6 must be a valid 6-char id6."""
        bad_id6 = dict(self.valid_q, artifact_id6="not_an_id6")
        v = runner_shared.validate_questions(
            {"questions": [bad_id6]}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_malformed)
        self.assertIn("artifact_id6", v.violations[0])

    def test_malformed_artifact_id6_mismatch(self) -> None:
        """Artifact_id6 mismatch with item_id6 yields a diagnostic naming both values."""
        diff_id6 = "other9"
        bad_mismatch = dict(self.valid_q, artifact_id6=diff_id6)
        v = runner_shared.validate_questions(
            {"questions": [bad_mismatch]}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_malformed)
        self.assertEqual(len(v.violations), 1)
        self.assertIn("artifact_id6", v.violations[0])
        self.assertIn(diff_id6, v.violations[0])
        self.assertIn(self.item_id6, v.violations[0])

    def test_malformed_duplicate_question_id(self) -> None:
        """Duplicate question_id makes the later entry malformed while first survives."""
        dup_q = dict(self.valid_q, text="Another question with same id")
        v = runner_shared.validate_questions(
            {"questions": [self.valid_q, dup_q]}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_malformed)
        self.assertEqual(len(v.questions), 1)
        self.assertEqual(len(v.violations), 1)
        self.assertIn("duplicate", v.violations[0])
        self.assertIn("question_id", v.violations[0])
        self.assertIn(self.valid_q["question_id"], v.violations[0])

    def test_malformed_options_bounds_and_types(self) -> None:
        """Options count must be 2..8, each <= 120 chars string."""
        bad_too_few = dict(self.valid_q, options=["single"])
        v1 = runner_shared.validate_questions(
            {"questions": [bad_too_few]}, item_id6=self.item_id6
        )
        self.assertTrue(v1.is_malformed)
        self.assertIn("options", v1.violations[0])

        bad_too_many = dict(self.valid_q, options=[str(i) for i in range(9)])
        v2 = runner_shared.validate_questions(
            {"questions": [bad_too_many]}, item_id6=self.item_id6
        )
        self.assertTrue(v2.is_malformed)
        self.assertIn("options", v2.violations[0])

        bad_opt_len = dict(self.valid_q, options=["A" * 121, "B"])
        v3 = runner_shared.validate_questions(
            {"questions": [bad_opt_len]}, item_id6=self.item_id6
        )
        self.assertTrue(v3.is_malformed)
        self.assertIn("options", v3.violations[0])

    def test_malformed_evidence_bounds(self) -> None:
        """Evidence count <= 10, items <= 500 chars."""
        bad_ev_count = dict(self.valid_q, evidence=[f"ev{i}" for i in range(11)])
        v1 = runner_shared.validate_questions(
            {"questions": [bad_ev_count]}, item_id6=self.item_id6
        )
        self.assertTrue(v1.is_malformed)
        self.assertIn("evidence", v1.violations[0])

        bad_ev_len = dict(self.valid_q, evidence=["e" * 501])
        v2 = runner_shared.validate_questions(
            {"questions": [bad_ev_len]}, item_id6=self.item_id6
        )
        self.assertTrue(v2.is_malformed)
        self.assertIn("evidence", v2.violations[0])

    def test_malformed_21st_entry_cap(self) -> None:
        """Array past 20 entries yields violation naming count, first 20 survive."""
        questions_21 = [dict(self.valid_q, question_id=f"q{i:02d}") for i in range(21)]
        v = runner_shared.validate_questions(
            {"questions": questions_21}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_malformed)
        self.assertEqual(len(v.questions), 20)
        self.assertEqual(len(v.violations), 1)
        self.assertIn("exceeds maximum of 20", v.violations[0])
        self.assertIn("21", v.violations[0])

    def test_per_entry_survival_with_bad_entry(self) -> None:
        """One bad entry does not drop the valid ones."""
        bad_entry = {"question_id": "bad1"}  # missing fields
        v = runner_shared.validate_questions(
            {"questions": [self.valid_q, bad_entry]}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_malformed)
        self.assertEqual(len(v.questions), 1)
        self.assertEqual(v.questions[0]["question_id"], self.valid_q["question_id"])
        self.assertTrue(len(v.violations) > 0)

    def test_worker_fingerprint_never_trusted(self) -> None:
        """Worker-supplied fingerprint is stored in proposed_fingerprint, never trusted."""
        proposed = "worker_fingerprint_bogus"
        q_with_fp = dict(self.valid_q, fingerprint=proposed)
        v = runner_shared.validate_questions(
            {"questions": [q_with_fp]}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_valid)
        clean = v.questions[0]
        self.assertNotEqual(clean["fingerprint"], proposed)
        self.assertEqual(clean.get("proposed_fingerprint"), proposed)
        expected_fp = runner_shared.question_fingerprint(
            clean["text"], clean.get("options")
        )
        self.assertEqual(clean["fingerprint"], expected_fp)

    def test_front_matter_sanitization(self) -> None:
        """Lines with front-matter patterns in text and evidence are sanitized."""
        injected = dict(
            self.valid_q,
            text="Header line\n- Status: approved\n- Id: evil01",
            evidence=["Intro\n- Readiness: go\nFact"],
        )
        v = runner_shared.validate_questions(
            {"questions": [injected]}, item_id6=self.item_id6
        )
        self.assertTrue(v.is_valid)
        clean = v.questions[0]
        self.assertNotIn("\n- Status:", clean["text"])
        self.assertIn("\n  - Status:", clean["text"])
        self.assertNotIn("\n- Readiness:", clean["evidence"][0])
        self.assertIn("\n  - Readiness:", clean["evidence"][0])


class TestFingerprintDeterminismAndParity(unittest.TestCase):
    """E-02: Normalization, determinism, and cross-host parity for question_fingerprint."""

    def test_normalization_invariance(self) -> None:
        """Case, whitespace, and trailing punctuation variants produce equal fingerprints."""
        t1 = "Should we adopt SQLite or Postgres?"
        t2 = "  should   WE  adopt sqlite or postgres ???  "
        t3 = "should we adopt sqlite or postgres."
        t4 = "SHOULD WE ADOPT SQLITE OR POSTGRES"

        fp1 = runner_shared.question_fingerprint(t1)
        fp2 = runner_shared.question_fingerprint(t2)
        fp3 = runner_shared.question_fingerprint(t3)
        fp4 = runner_shared.question_fingerprint(t4)

        self.assertEqual(fp1, fp2)
        self.assertEqual(fp1, fp3)
        self.assertEqual(fp1, fp4)
        self.assertEqual(len(fp1), 16)

    def test_option_set_sorting_and_differentiation(self) -> None:
        """Sorted normalized options produce equal fingerprints; different options differ."""
        text = "Choose database"
        opts_a = ["PostgreSQL", "SQLite"]
        opts_b = ["sqlite", "postgresql"]
        opts_diff = ["PostgreSQL", "SQLite", "MySQL"]

        fp_a = runner_shared.question_fingerprint(text, opts_a)
        fp_b = runner_shared.question_fingerprint(text, opts_b)
        fp_diff = runner_shared.question_fingerprint(text, opts_diff)

        self.assertEqual(fp_a, fp_b)
        self.assertNotEqual(fp_a, fp_diff)

    def test_host_parity(self) -> None:
        """Both hosts compute identical fingerprints through oc_runipd and agy_runipd re-exports."""
        text = "Which strategy should be used?"
        opts = ["Opt1", "Opt2"]

        fp_shared = runner_shared.question_fingerprint(text, opts)
        fp_oc = oc_runipd.question_fingerprint(text, opts)
        fp_agy = agy_runipd.question_fingerprint(text, opts)

        self.assertEqual(fp_shared, fp_oc)
        self.assertEqual(fp_shared, fp_agy)


class TestPromptContents(unittest.TestCase):
    """E-03 / E-04: Prompt content and carrier tests across execute and review turns."""

    def setUp(self) -> None:
        self.item = {
            "id6": "0jooqz",
            "position": 1,
            "setid": "qchan",
            "action": "execute",
        }
        self.state = {"run_id": "run-test-prompt-123", "repo": "."}
        self.run_dir = Path("/tmp/test_carrier_run_dir")
        self.plan_path = Path(".aw/records/plans/pending/test.ipd.md")

    def test_execute_prompt_on_both_hosts(self) -> None:
        """Rendered execute prompt on both hosts contains questions[] literal and askme citation."""
        for mod, name in [(oc_runipd, "oc"), (agy_runipd, "agy")]:
            prompt = mod.build_prompt(
                self.item, self.state, self.run_dir, self.plan_path, False
            )
            self.assertIn(".aw/system/workflows/askme/askme.md", prompt)
            self.assertIn("Establish facts before asking", prompt)
            self.assertIn('"questions": [', prompt)
            self.assertIn('"deferred_question_ids": []', prompt)
            self.assertIn("which supersedes `deferred_question_ids`", prompt)
            self.assertEqual(prompt.count("record a DEFERRED question"), 0)

    def test_review_prompt_byte_identical_when_non_isolated(self) -> None:
        """Non-isolated review prompt returns byte-identical single line."""
        item = {
            "id6": "rev001",
            "position": 2,
            "setid": "qchan",
            "action": "review",
            "review_handler": "plan-review",
        }
        prompt = runner_shared.build_review_prompt(
            item, self.state, self.run_dir, self.plan_path, Path("."), lane_root=None
        )
        self.assertEqual(prompt, f"/plan-review {self.plan_path}")
        self.assertEqual(len(prompt.splitlines()), 1)

    def test_review_prompt_contains_carrier_when_isolated(self) -> None:
        """Isolated review prompt carries lane outcome path and askme instruction."""
        with tempfile.TemporaryDirectory() as td:
            lane_root = Path(td)
            item = {
                "id6": "rev001",
                "position": 2,
                "setid": "qchan",
                "action": "review",
                "review_handler": "plan-review",
            }
            plan_in_lane = lane_root / "test.ipd.md"
            plan_in_lane.write_text("content", encoding="utf-8")

            prompt = runner_shared.build_review_prompt(
                item,
                self.state,
                self.run_dir,
                plan_in_lane,
                Path("."),
                lane_root=lane_root,
            )
            lines = prompt.splitlines()
            self.assertEqual(lines[0], "/plan-review test.ipd.md")
            self.assertIn("Required JSON outcome:", prompt)
            self.assertIn("When a material question is the HUMAN'S to decide", prompt)
            self.assertIn(".aw/system/workflows/askme/askme.md", prompt)

            # Assert directory created
            m = re.search(r"Required JSON outcome: (\S+)", prompt)
            self.assertIsNotNone(m)
            outcome_path = lane_root / m.group(1)
            self.assertTrue(outcome_path.parent.is_dir())


class TestA10Contract(unittest.TestCase):
    """A10a / A10b / A31: Contract tests between decisions/questions register and question carrier."""

    def test_a10a_decision_row_without_question_not_parked(self) -> None:
        """Worker that resolves question from evidence records D-* row and no question in questions[]."""
        outcome_with_d_row = {
            "disposition": "executed",
            "decision_ids": ["D-01"],
            "questions": [],
            "defect_report": {"state": "none-found", "findings": []},
            "pushed": False,
        }
        v = runner_shared.validate_questions(outcome_with_d_row, item_id6="0jooqz")
        self.assertTrue(v.is_absent)
        self.assertEqual(len(v.questions), 0)

    def test_a10b_gating_question_recorded_in_verdict(self) -> None:
        """Worker unsure on blocking question escalates via questions[] array."""
        outcome_with_question = {
            "disposition": "executed",
            "questions": [
                {
                    "question_id": "q-blocking",
                    "text": "Human decision required for release scope",
                    "artifact_id6": "0jooqz",
                    "gates_verdict": True,
                    "evidence": ["ambiguous requirement in spec"],
                }
            ],
            "defect_report": {"state": "none-found", "findings": []},
            "pushed": False,
        }
        v = runner_shared.validate_questions(outcome_with_question, item_id6="0jooqz")
        self.assertTrue(v.is_valid)
        self.assertEqual(len(v.questions), 1)
        self.assertTrue(v.questions[0]["gates_verdict"])

    def test_a31_prompt_cites_askme_three_way_sort(self) -> None:
        """Prompt explicitly names the askme sort that governs decision vs ask."""
        item = {"id6": "0jooqz", "position": 1, "setid": "qchan", "action": "execute"}
        state = {"run_id": "run-test-a31", "repo": "."}
        run_dir = Path("/tmp/test_a31")
        plan_path = Path(".aw/records/plans/pending/test.ipd.md")

        prompt = runner_shared.build_prompt(
            item, state, run_dir, plan_path, False, labels=runner_shared.OC_HOST_LABELS
        )
        self.assertIn("askme three-way sort", prompt)
        self.assertIn(
            "`.aw/system/workflows/askme/askme.md` 'Establish facts before asking'",
            prompt,
        )


class TestE06DriverIntake(unittest.TestCase):
    """E-06 / V-06: Driver intake tests in execute_item_core."""

    def test_e06_execute_valid(self) -> None:
        """Scripted execute turn with valid question ends with attempt['questions_verdict']['verdict'] == 'valid'."""
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            repo = _create_test_repo(tmp_path)
            plan_file = _create_plan_file(repo, "exe001")
            fake_bin = _make_fake_agent_script(tmp_path)

            run_dir = repo / ".aw" / "records" / "runs" / "run-e06-exec"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            outcome_payload = {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-valid-1",
                        "text": "Proceed with migration?",
                        "artifact_id6": "exe001",
                        "gates_verdict": True,
                        "evidence": ["migration plan v1"],
                    }
                ],
                "pushed": False,
            }

            item: dict[str, Any] = {
                "id6": "exe001",
                "setid": "testset",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
                "attempts": [],
            }
            state: dict[str, Any] = {
                "repo": str(repo),
                "run_id": "run-e06-exec",
                "queue": [item],
                "options": {
                    "no_verify": True,
                    "validate": False,
                    "self_finalize": False,
                    "output_mode": "quiet",
                    "opencode": str(fake_bin),
                },
            }

            with mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
            ), coordinator_role():
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(item["attempts"]), 1)
            attempt = item["attempts"][0]
            qv = attempt.get("questions_verdict")
            self.assertIsNotNone(qv)
            self.assertEqual(qv["verdict"], "valid")
            self.assertEqual(len(qv["questions"]), 1)
            self.assertEqual(qv["questions"][0]["question_id"], "q-valid-1")
            self.assertEqual(len(qv["questions"][0]["fingerprint"]), 16)
            self.assertEqual(qv["violations"], [])
            # Print for V-06 visibility
            print("PRINTED_ATTEMPT_QUESTIONS_VERDICT:", qv)

    def test_e06_isolated_review_valid(self) -> None:
        """Scripted isolated review turn with valid question ends with valid questions_verdict."""
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            repo = _create_test_repo(tmp_path)
            plan_file = _create_plan_file(repo, "rev001")
            fake_bin = _make_fake_agent_script(tmp_path)

            run_dir = repo / ".aw" / "records" / "runs" / "run-e06-rev"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            outcome_payload = {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-rev-1",
                        "text": "Review question on architectural boundary?",
                        "artifact_id6": "rev001",
                        "gates_verdict": False,
                        "evidence": ["boundary diagram"],
                    }
                ],
                "pushed": False,
            }

            item: dict[str, Any] = {
                "id6": "rev001",
                "setid": "testset",
                "position": 1,
                "action": "review",
                "review_handler": "plan-review",
                "status": "queued",
                "configured_file": str(plan_file),
                "attempts": [],
            }
            state: dict[str, Any] = {
                "repo": str(repo),
                "run_id": "run-e06-rev",
                "queue": [item],
                "options": {
                    "no_verify": True,
                    "validate": False,
                    "self_finalize": False,
                    "isolate_review": True,
                    "output_mode": "quiet",
                    "opencode": str(fake_bin),
                },
            }

            with mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
            ), coordinator_role():
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(item["attempts"]), 1)
            attempt = item["attempts"][0]
            qv = attempt.get("questions_verdict")
            self.assertIsNotNone(qv)
            self.assertEqual(qv["verdict"], "valid")
            self.assertEqual(len(qv["questions"]), 1)
            self.assertEqual(qv["questions"][0]["question_id"], "q-rev-1")

    def test_e06_malformed_event_and_log(self) -> None:
        """Malformed question entry yields questions-malformed event in events.jsonl and yellow line on stderr."""
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            repo = _create_test_repo(tmp_path)
            plan_file = _create_plan_file(repo, "mal001")
            fake_bin = _make_fake_agent_script(tmp_path)

            run_dir = repo / ".aw" / "records" / "runs" / "run-e06-mal"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            # Missing text and invalid artifact_id6
            outcome_payload = {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-bad",
                        "artifact_id6": "wrong6",
                        "gates_verdict": True,
                        "evidence": ["ev"],
                    }
                ],
                "pushed": False,
            }

            item: dict[str, Any] = {
                "id6": "mal001",
                "setid": "testset",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
                "attempts": [],
            }
            state: dict[str, Any] = {
                "repo": str(repo),
                "run_id": "run-e06-mal",
                "queue": [item],
                "options": {
                    "no_verify": True,
                    "validate": False,
                    "self_finalize": False,
                    "output_mode": "quiet",
                    "opencode": str(fake_bin),
                },
            }

            stderr_buf = io.StringIO()
            with mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)}
            ), mock.patch("sys.stderr", stderr_buf), coordinator_role():
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            attempt = item["attempts"][0]
            qv = attempt.get("questions_verdict")
            self.assertIsNotNone(qv)
            self.assertEqual(qv["verdict"], "malformed")
            self.assertTrue(len(qv["violations"]) >= 1)

            # Check events.jsonl
            events_file = run_dir / "events.jsonl"
            self.assertTrue(events_file.is_file())
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            mal_events = [e for e in events if e.get("event") == "questions-malformed"]
            self.assertEqual(len(mal_events), 1)
            self.assertEqual(mal_events[0]["id6"], "mal001")
            self.assertEqual(mal_events[0]["attempt"], 1)
            self.assertEqual(mal_events[0]["violations"], qv["violations"])
            print("PRINTED_QUESTIONS_MALFORMED_EVENT:", mal_events[0])

            # Check stderr output
            stderr_text = stderr_buf.getvalue()
            self.assertIn("questions malformed", stderr_text)

    def test_e06_stale_outcome_retry_recorded_absent(self) -> None:
        """Retry attempt that writes no new outcome records questions_verdict as absent."""
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            repo = _create_test_repo(tmp_path)
            plan_file = _create_plan_file(repo, "stl001")
            fake_bin = _make_fake_agent_script(tmp_path)

            run_dir = repo / ".aw" / "records" / "runs" / "run-e06-stale"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            outcome_payload = {
                "disposition": "partial",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-first",
                        "text": "First attempt question?",
                        "artifact_id6": "stl001",
                        "gates_verdict": True,
                        "evidence": ["ev"],
                    }
                ],
                "pushed": False,
            }

            item: dict[str, Any] = {
                "id6": "stl001",
                "setid": "testset",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
                "attempts": [],
            }
            state: dict[str, Any] = {
                "repo": str(repo),
                "run_id": "run-e06-stale",
                "queue": [item],
                "options": {
                    "no_verify": True,
                    "validate": False,
                    "self_finalize": False,
                    "output_mode": "quiet",
                    "opencode": str(fake_bin),
                },
            }

            # Seed pre-existing outcome file from prior attempt
            outcome_path = run_dir / "outcomes" / "01-stl001.json"
            outcome_path.write_text(json.dumps(outcome_payload), encoding="utf-8")

            # Retry turn does NOT touch or write outcome
            with mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_JSON": "__SUPPRESS_OUTCOME__"}
            ), coordinator_role():
                oc_runipd.execute_item(run_dir, state, item, recovery=True)

            self.assertEqual(len(item["attempts"]), 1)
            attempt = item["attempts"][0]
            qv = attempt.get("questions_verdict")
            self.assertIsNotNone(qv)
            self.assertEqual(qv["verdict"], "absent")


class TestA30CarrierSeparation(unittest.TestCase):
    """A30: Carrier separation between AW_MISSING_INPUT token and questions[] array."""

    def test_a30_carrier_separation_missing_input_token_not_question(self) -> None:
        """Worker emitting AW_MISSING_INPUT token with no questions yields no question verdict."""
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            repo = _create_test_repo(tmp_path)
            plan_file = _create_plan_file(repo, "mis001")
            fake_bin = _make_fake_agent_script(tmp_path)

            run_dir = repo / ".aw" / "records" / "runs" / "run-a30-token"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            missing_token = lane_containment.format_missing_input_token(
                "missing/config.yaml", "required for deployment"
            )

            outcome_payload = {
                "disposition": "partial",
                "defect_report": {"state": "none-found", "findings": []},
                "pushed": False,
            }

            item: dict[str, Any] = {
                "id6": "mis001",
                "setid": "testset",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
                "attempts": [],
            }
            state: dict[str, Any] = {
                "repo": str(repo),
                "run_id": "run-a30-token",
                "queue": [item],
                "options": {
                    "no_verify": True,
                    "validate": False,
                    "self_finalize": False,
                    "output_mode": "quiet",
                    "opencode": str(fake_bin),
                },
            }

            with mock.patch.dict(
                os.environ,
                {
                    "FAKE_PAYLOAD_JSON": json.dumps(outcome_payload),
                    "FAKE_EMIT_TOKEN": missing_token,
                },
            ), coordinator_role():
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            attempt = item["attempts"][0]
            qv = attempt.get("questions_verdict")
            self.assertIsNotNone(qv)
            self.assertEqual(qv["verdict"], "absent")
            # Missing input path handled the token
            self.assertTrue(attempt.get("lane_paused_for_missing_input"))
            refusals = attempt.get("missing_input_refusals", [])
            self.assertEqual(len(refusals), 1)
            self.assertEqual(refusals[0]["path"], "missing/config.yaml")

    def test_a30_carrier_separation_question_containing_token_not_missing_input(
        self,
    ) -> None:
        """Valid question entry whose text contains AW_MISSING_INPUT is not treated as missing input."""
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            repo = _create_test_repo(tmp_path)
            plan_file = _create_plan_file(repo, "qnt001")
            fake_bin = _make_fake_agent_script(tmp_path)

            run_dir = repo / ".aw" / "records" / "runs" / "run-a30-qtoken"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
            (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

            token_in_text = "AW_MISSING_INPUT:some/path:how should this be handled?"

            outcome_payload = {
                "disposition": "executed",
                "defect_report": {"state": "none-found", "findings": []},
                "questions": [
                    {
                        "question_id": "q-text-token",
                        "text": token_in_text,
                        "artifact_id6": "qnt001",
                        "gates_verdict": True,
                        "evidence": ["ev"],
                    }
                ],
                "pushed": False,
            }

            item: dict[str, Any] = {
                "id6": "qnt001",
                "setid": "testset",
                "position": 1,
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_file),
                "attempts": [],
            }
            state: dict[str, Any] = {
                "repo": str(repo),
                "run_id": "run-a30-qtoken",
                "queue": [item],
                "options": {
                    "no_verify": True,
                    "validate": False,
                    "self_finalize": False,
                    "output_mode": "quiet",
                    "opencode": str(fake_bin),
                },
            }

            with mock.patch.dict(
                os.environ,
                {"FAKE_PAYLOAD_JSON": json.dumps(outcome_payload)},
            ), coordinator_role():
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            attempt = item["attempts"][0]
            qv = attempt.get("questions_verdict")
            self.assertIsNotNone(qv)
            self.assertEqual(qv["verdict"], "valid")
            self.assertEqual(len(qv["questions"]), 1)
            self.assertEqual(qv["questions"][0]["text"], token_in_text)
            # Not handled as a missing input report
            self.assertFalse(attempt.get("lane_paused_for_missing_input", False))
            self.assertFalse(attempt.get("missing_input_refusals", []))
