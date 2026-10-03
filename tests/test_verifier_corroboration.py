"""Tests for verifier test evidence corroboration.

Validates session log command extraction, tolerant command matching, and three-state
fail-open corroboration verdicts across both OpenCode and Antigravity log formats.
Uses committed fixtures only; does not read live run directories.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

import agent_workflows.verifier_corroboration as vc
from agent_workflows import (
    agy_runipd,
    oc_runipd,
    render_stream,
    run_viewer,
    runner_shared,
)
from agent_workflows.runner_shared import (
    extract_verifier_test_commands,
    has_verifier_test_evidence,
)
from agent_workflows.term import Term

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "verifier_corroboration"


class TestSessionLogExtraction:
    """E-01 & E-02: Host-agnostic log extraction, counts, and hostile input handling."""

    def test_oc_and_agy_equivalent_extractions(self) -> None:
        """Verify equivalent session logs from both hosts produce identical command extractions."""
        oc_path = FIXTURES_DIR / "oc_session_corroborated.jsonl"
        agy_path = FIXTURES_DIR / "agy_session_corroborated.jsonl"

        oc_res = vc.extract_session_commands(oc_path)
        agy_res = vc.extract_session_commands(agy_path)

        assert oc_res.format == "oc"
        assert agy_res.format == "agy"
        assert len(oc_res.commands) == 1
        assert len(agy_res.commands) == 1

        assert oc_res.commands[0].command == "python3 -m pytest tests/"
        assert oc_res.commands[0].tool == "bash"
        assert oc_res.commands[0].host == "oc"
        assert oc_res.commands[0].error is False

        assert agy_res.commands[0].command == "python3 -m pytest tests/"
        assert agy_res.commands[0].tool == "run_command"
        assert agy_res.commands[0].host == "agy"
        assert agy_res.commands[0].error is False

    def test_three_categories_counted_separately_oc(self) -> None:
        """Verify OpenCode log distinguishes observed command, delegation, and missing command text."""
        p = FIXTURES_DIR / "oc_session_three_categories.jsonl"
        res = vc.extract_session_commands(p)

        assert len(res.commands) == 1
        assert res.commands[0].command == "python3 -m pytest tests/"
        assert res.delegation_count == 1
        assert res.missing_command_count == 1
        assert res.reason_code == ""

    def test_three_categories_counted_separately_agy(self) -> None:
        """Verify Antigravity twin distinguishes observed command, delegation, and missing command text."""
        p = FIXTURES_DIR / "agy_session_three_categories.jsonl"
        res = vc.extract_session_commands(p)

        assert len(res.commands) == 1
        assert res.commands[0].command == "python3 -m pytest tests/"
        assert res.delegation_count == 1
        assert res.missing_command_count == 1
        assert res.reason_code == ""

    @pytest.mark.parametrize(
        ("case_name", "writer", "expected_reason"),
        [
            ("nonexistent_path", lambda p: None, vc.INDETERMINATE_LOG_UNREADABLE),
            ("directory", lambda p: p.mkdir(), vc.INDETERMINATE_LOG_UNREADABLE),
            (
                "zero_byte_file",
                lambda p: p.write_bytes(b""),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "binary_file",
                lambda p: p.write_bytes(b"\x00\xff\xfe\x00\x01\x02"),
                vc.INDETERMINATE_LOG_UNREADABLE,
            ),
            (
                "not_json_lines",
                lambda p: p.write_text(
                    "hello not json\nworld not json\n", encoding="utf-8"
                ),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "jsonl_top_level_lists",
                lambda p: p.write_text('[1, 2, 3]\n["a", "b"]\n', encoding="utf-8"),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "jsonl_top_level_scalars",
                lambda p: p.write_text('"string"\n12345\ntrue\n', encoding="utf-8"),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
            (
                "mid_line_truncation",
                lambda p: p.write_text(
                    '{"type": "tool_use", "part": {"tool": "bash"',
                    encoding="utf-8",
                ),
                vc.INDETERMINATE_LOG_EMPTY,
            ),
        ],
    )
    def test_hostile_inputs_never_raise(
        self,
        case_name: str,
        writer: Any,
        expected_reason: str,
    ) -> None:
        """Verify hostile inputs return empty results with expected reason code and never raise."""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / f"hostile_{case_name}.log"
            if writer:
                writer(target)
            res = vc.extract_session_commands(target)
            assert res.commands == []
            assert res.reason_code == expected_reason


class TestTolerantCommandMatcher:
    """E-03: Tolerant matching across exact, truncation, prose, chaining, and indirection."""

    def test_exact_match(self) -> None:
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(
            command="python3 -m pytest tests/", tool="bash", host="oc"
        )
        assert vc.match_single_claim(claim, obs) is True

    def test_real_truncation_with_ellipsis(self) -> None:
        """Verify real >120 character truncation from extract_verifier_test_commands matches."""
        full_command = (
            "python3 -m pytest tests/test_verifier_corroboration.py "
            "-k test_a_very_long_test_name_exceeding_one_hundred_and_twenty_characters_long_for_real_truncation "
            "--verbose"
        )
        assert len(full_command) > 120
        claims = extract_verifier_test_commands({"tests_run": [full_command]})
        assert len(claims) == 1
        truncated_claim = claims[0]
        assert truncated_claim.endswith("...")

        obs = vc.ObservedCommand(command=full_command, tool="bash", host="oc")
        assert vc.match_single_claim(truncated_claim, obs) is True

    def test_prose_wrapped_command(self) -> None:
        claim = (
            "python -m unittest tests.test_release_gate_close -v -> "
            "Ran 25 tests in 0.102s OK (exit 0): all checks passed"
        )
        obs = vc.ObservedCommand(
            command="python -m unittest tests.test_release_gate_close -v",
            tool="bash",
            host="oc",
        )
        assert vc.match_single_claim(claim, obs) is True

    def test_chained_command_segment(self) -> None:
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(
            command="cd repo && python3 -m pytest tests/ ; echo done",
            tool="bash",
            host="oc",
        )
        assert vc.match_single_claim(claim, obs) is True

    def test_indirected_command_make_test(self) -> None:
        """Verify make test in KNOWN_TEST_INDIRECTIONS matches a pytest claim."""
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(command="make test", tool="bash", host="oc")
        assert vc.match_single_claim(claim, obs) is True

    def test_unrelated_command_does_not_match(self) -> None:
        claim = "python3 -m pytest tests/"
        obs = vc.ObservedCommand(command="git status", tool="bash", host="oc")
        assert vc.match_single_claim(claim, obs) is False

    def test_delegated_turn_has_no_match(self) -> None:
        claims = ["python3 -m pytest tests/"]
        res = vc.match_claims_to_observed(claims, [])
        assert res.matched_claims == []
        assert res.unmatched_claims == claims


class TestTurnLevelVerdicts:
    """E-04: Closed set of three states with six distinct indeterminate reason codes."""

    def test_corroborated_turn(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_corroborated.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.CORROBORATED
        assert v.reason_code == vc.CORROBORATED
        assert v.matched_count == 1

    def test_uncorroborated_turn(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_uncorroborated.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.UNCORROBORATED
        assert v.reason_code == vc.UNCORROBORATED
        assert v.matched_count == 0
        assert v.observed_count == 1

    def test_indeterminate_log_unreadable(self) -> None:
        claims = ["python3 -m pytest tests/"]
        v = vc.corroborate_verifier_turn("nonexistent_session.jsonl", claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_LOG_UNREADABLE

    def test_indeterminate_log_empty(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "session_empty.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_LOG_EMPTY

    def test_indeterminate_claims_empty(self) -> None:
        p = FIXTURES_DIR / "oc_session_corroborated.jsonl"
        v = vc.corroborate_verifier_turn(p, [])
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_CLAIMS_EMPTY

    def test_indeterminate_delegation_present(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_delegated.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_DELEGATION

    def test_indeterminate_missing_command_text(self) -> None:
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_missing_command_text.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_MISSING_COMMAND_TEXT

    def test_indeterminate_unresolved_indirection(self) -> None:
        """Verify make check fails open to indeterminate with indirection-unresolved."""
        claims = ["python3 -m pytest tests/"]
        p = FIXTURES_DIR / "oc_session_indirection_unresolved.jsonl"
        v = vc.corroborate_verifier_turn(p, claims)
        assert v.verdict == vc.INDETERMINATE
        assert v.reason_code == vc.INDETERMINATE_INDIRECTION_UNRESOLVED

    def test_falsifiability_uncorroborated_to_indeterminate_on_unreadable_log(
        self,
    ) -> None:
        """Verify mutating an uncorroborated log to unreadable resolves to indeterminate."""
        claims = ["python3 -m pytest tests/"]
        src = FIXTURES_DIR / "oc_session_uncorroborated.jsonl"

        with tempfile.TemporaryDirectory() as td:
            mutated_file = Path(td) / "mutated_session.jsonl"
            mutated_file.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

            # Prior to mutation: uncorroborated
            v_before = vc.corroborate_verifier_turn(mutated_file, claims)
            assert v_before.verdict == vc.UNCORROBORATED

            # Mutate to binary unreadable content
            mutated_file.write_bytes(b"\x00\xff\xfe\x00binary_corrupt")
            v_after = vc.corroborate_verifier_turn(mutated_file, claims)
            assert v_after.verdict == vc.INDETERMINATE
            assert v_after.reason_code == vc.INDETERMINATE_LOG_UNREADABLE


class TestHonestyPinAndFabricationGap:
    """E-05 (F-2): Durable pin for the fabrication gap."""

    def test_plausible_unrun_command_accepted_by_gate_reported_uncorroborated(
        self,
    ) -> None:
        """Pin the residual weakness: a plausible-but-unrun command passes has_verifier_test_evidence

        but is reported uncorroborated when the session log contains only unmatching tool calls.
        """
        # A plausible command claim that has never been run
        claimed_command = "python3 -m pytest tests/test_release_gate.py"
        verifier_data = {
            "verdict": "VERIFIED",
            "tests_run": [claimed_command],
        }

        # 1. Shipped evidence predicate accepts it (proves activity, not non-fabrication)
        assert has_verifier_test_evidence(verifier_data) is True

        # 2. Session log shows only git status was executed
        log_path = FIXTURES_DIR / "oc_session_uncorroborated.jsonl"
        extracted = vc.extract_session_commands(log_path)
        assert len(extracted.commands) == 1
        assert extracted.commands[0].command == "git status"

        # 3. Corroboration module reports uncorroborated
        verdict = vc.corroborate_verifier_turn(log_path, verifier_data["tests_run"])
        assert verdict.verdict == vc.UNCORROBORATED
        assert verdict.reason_code == vc.UNCORROBORATED
        assert verdict.matched_count == 0
        assert verdict.observed_count == 1


# --- E-05 Interaction and Outcome Equality Tests (Plan btak7a) ------------------------


def _setup_test_repo(root: Path) -> tuple[Path, Path]:
    """Create a minimal temporary git repo with an approved plan file."""
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "file.txt").write_text("initial content", encoding="utf-8")
    subprocess.run(
        ["git", "add", "file.txt"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=root,
        check=True,
        capture_output=True,
    )

    plan_dir = root / ".aw/records/plans/executed"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "20261001-test-01-tst001-test.ipd.md"
    plan_file.write_text(
        "# IPD: Test\n- Id: tst001\n- Set: test\n- Status: executed\n- Scope-Paths: file.txt\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "add plan"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return root, plan_file


def _drive_execute_turn(
    repo_root: Path,
    plan_file: Path,
    *,
    spawn_executor: Any = None,
    spawn_verifier: Any = None,
    validate: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Drive the real runner_shared.execute_item_core execution path."""
    run_dir = repo_root / ".aw/runs/run-test"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

    item: dict[str, Any] = {
        "id6": "tst001",
        "setid": "test",
        "position": 1,
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file.relative_to(repo_root)),
    }
    state: dict[str, Any] = {
        "repo": str(repo_root),
        "run_id": "run-test",
        "queue": [item],
        "options": {
            "isolate_worktrees": False,
            "self_finalize": False,
            "validate": validate,
        },
    }

    if spawn_executor is None:

        def default_executor(
            prompt_path: Path,
            work_dir: Any,
            tracker: Any,
            p_path: Path,
            attempt_no: int,
            session_id: Any,
            use_continue: bool,
        ) -> tuple[int, str, Path, list[str]]:
            log_path = run_dir / "logs/test.log"
            log_path.write_text("test log", encoding="utf-8")
            outcome = run_dir / "outcomes/01-tst001.json"
            outcome.write_text(
                json.dumps(
                    {
                        "disposition": "executed",
                        "defect_report": {"state": "none-found", "findings": []},
                        "pushed": False,
                    }
                ),
                encoding="utf-8",
            )
            return 0, "session-123", log_path, ["mock_agent"]

        spawn_executor = default_executor

    runner_shared.execute_item_core(
        run_dir,
        state,
        item,
        recovery=False,
        host_labels=runner_shared.OC_HOST_LABELS,
        spawn_executor=spawn_executor,
        spawn_verifier=spawn_verifier,
        raw_launcher=lambda *a, **k: None,
        run_suite_check=lambda p, s: None,
        process_backlog_close=lambda *a, **k: None,
        driver_module=oc_runipd,
    )
    return state, item


class TestCorroborationInteractionAndOutcomeEquality:
    """E-05 / V-05: Interaction and outcome-equality guarantees for verifier corroboration.

    Tests drive the real runner_shared.execute_item_core pipeline rather than simulating it,
    validating that corroboration verdicts are recorded accurately without altering downstream
    verification disposition, item status, recorded refusals, or earned integration.
    """

    @pytest.mark.parametrize(
        "verdict_kind",
        ["corroborated", "uncorroborated", "indeterminate"],
    )
    def test_no_refusal_downgrade_or_disposition_change_across_corroboration_verdicts(
        self, verdict_kind: str
    ) -> None:
        """Outcome equality: verify_disp, disposition, refusal absence, and earned integration

        are byte-identical whether corroboration is corroborated, uncorroborated, or indeterminate.
        This pins the plan's central safety contract: corroboration is an observational record and
        never introduces a refusal or outcome downgrade.
        """
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-test"

            def verifier_spawner(
                prompt_path: Path,
                plan_path: Path,
                work_dir: Any,
                tracker: Any,
                attempt_no: int,
            ) -> tuple[int, str, Path, list[str]]:
                outcomes_dir = run_dir / "outcomes"
                logs_dir = run_dir / "logs"
                outcomes_dir.mkdir(parents=True, exist_ok=True)
                logs_dir.mkdir(parents=True, exist_ok=True)

                v_outcome = outcomes_dir / "01-tst001-verification.json"
                v_outcome.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "id6": "tst001",
                            "verdict": "VERIFIED",
                            "tests_run": ["python3 -m pytest tests/"],
                        }
                    ),
                    encoding="utf-8",
                )

                log_file = logs_dir / "01-tst001-attempt-1-verify.jsonl"
                if verdict_kind == "corroborated":
                    event = {
                        "event": "step_update",
                        "step_update": {
                            "state": "DONE",
                            "step_type": "tool",
                            "tool_name": "run_command",
                            "tool_info": {
                                "parameters": {
                                    "CommandLine": "python3 -m pytest tests/"
                                }
                            },
                        },
                    }
                    log_file.write_text(json.dumps(event) + "\n", encoding="utf-8")
                elif verdict_kind == "uncorroborated":
                    event = {
                        "event": "step_update",
                        "step_update": {
                            "state": "DONE",
                            "step_type": "tool",
                            "tool_name": "run_command",
                            "tool_info": {"parameters": {"CommandLine": "git status"}},
                        },
                    }
                    log_file.write_text(json.dumps(event) + "\n", encoding="utf-8")
                elif verdict_kind == "indeterminate":
                    log_file.write_bytes(b"\x00\xff\xfe\x00corrupt")

                return 0, "sess-v-1", log_file, ["mock_verifier"]

            state, item = _drive_execute_turn(
                repo_root,
                plan_file,
                spawn_verifier=verifier_spawner,
                validate=True,
            )

            attempts = item.get("attempts", [])
            assert len(attempts) == 1
            attempt = attempts[0]

            # 1. Corroboration fields recorded on attempt and item
            assert attempt["corroboration_verdict"] == verdict_kind
            assert item["corroboration_verdict"] == verdict_kind
            assert "corroboration_reason" in attempt
            assert "corroboration_counts" in attempt
            assert "corroboration_reason" in item
            assert "corroboration_counts" in item

            # 2. Downstream facts strictly equal and unrefused across all three verdict values
            # Fact A: verify_disp is "verified"
            assert attempt["verification_status"] == "verified"
            assert item["verification_status"] == "verified"

            # Fact B: disposition is "executed"
            assert attempt["disposition"] == "executed"
            assert item["status"] == "executed"

            # Fact C: no refusal recorded
            assert render_stream.refusal_of_item(item) is None

            # Fact D: integration_is_earned is True
            earned = runner_shared.integration_is_earned(
                validate=True,
                verify_disp=item["verification_status"],
                suite_result=0,
            )
            assert earned.earned is True

    def test_corroboration_raising_computation_cannot_break_turn(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """E-01 / V-01: An unexpected exception in corroboration computation is caught and guarded.

        The turn must complete with verified outcome and record indeterminate with reason 'computation-failed'.
        """

        def broken_corroborate(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("simulated unexpected crash in corroboration")

        monkeypatch.setattr(
            vc,
            "corroborate_verifier_turn",
            broken_corroborate,
        )

        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-test"

            def verifier_spawner(
                prompt_path: Path,
                plan_path: Path,
                work_dir: Any,
                tracker: Any,
                attempt_no: int,
            ) -> tuple[int, str, Path, list[str]]:
                outcomes_dir = run_dir / "outcomes"
                logs_dir = run_dir / "logs"
                outcomes_dir.mkdir(parents=True, exist_ok=True)
                logs_dir.mkdir(parents=True, exist_ok=True)

                v_outcome = outcomes_dir / "01-tst001-verification.json"
                v_outcome.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "id6": "tst001",
                            "verdict": "VERIFIED",
                            "tests_run": ["python3 -m pytest tests/"],
                        }
                    ),
                    encoding="utf-8",
                )
                log_file = logs_dir / "01-tst001-attempt-1-verify.jsonl"
                log_file.write_text("{}", encoding="utf-8")
                return 0, "sess-v-1", log_file, ["mock_verifier"]

            state, item = _drive_execute_turn(
                repo_root,
                plan_file,
                spawn_verifier=verifier_spawner,
                validate=True,
            )

            attempt = item["attempts"][0]
            assert attempt["corroboration_verdict"] == "indeterminate"
            assert attempt["corroboration_reason"] == "computation-failed"
            assert item["corroboration_verdict"] == "indeterminate"
            assert item["corroboration_reason"] == "computation-failed"
            assert item["verification_status"] == "verified"
            assert attempt["disposition"] == "executed"
            assert render_stream.refusal_of_item(item) is None

    def test_unreadable_outcome_sets_initialization_reason_not_computation_guard(
        self,
    ) -> None:
        """F-4b / V-01: An unreadable verification outcome reaches indeterminate via pre-guard initialization.

        Asserts that corrupt outcome JSON records reason 'outcome-unreadable' and NOT 'computation-failed',
        proving the call was not placed where v_data was unbound.
        """
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-test"

            def verifier_spawner(
                prompt_path: Path,
                plan_path: Path,
                work_dir: Any,
                tracker: Any,
                attempt_no: int,
            ) -> tuple[int, str, Path, list[str]]:
                outcomes_dir = run_dir / "outcomes"
                logs_dir = run_dir / "logs"
                outcomes_dir.mkdir(parents=True, exist_ok=True)
                logs_dir.mkdir(parents=True, exist_ok=True)

                v_outcome = outcomes_dir / "01-tst001-verification.json"
                v_outcome.write_text("{corrupt json", encoding="utf-8")
                log_file = logs_dir / "01-tst001-attempt-1-verify.jsonl"
                log_file.write_text("{}", encoding="utf-8")
                return 0, "sess-v-1", log_file, ["mock_verifier"]

            state, item = _drive_execute_turn(
                repo_root,
                plan_file,
                spawn_verifier=verifier_spawner,
                validate=True,
            )

            attempt = item["attempts"][0]
            assert attempt["corroboration_verdict"] == "indeterminate"
            assert attempt["corroboration_reason"] == "outcome-unreadable"
            assert attempt["corroboration_reason"] != "computation-failed"
            assert item["corroboration_verdict"] == "indeterminate"
            assert item["corroboration_reason"] == "outcome-unreadable"

    def test_no_outcome_file_records_no_corroboration_keys(self) -> None:
        """E-02 / V-02: A run where the verifier produced no outcome file carries no corroboration key."""
        with tempfile.TemporaryDirectory() as td:
            repo_root, plan_file = _setup_test_repo(Path(td))
            run_dir = repo_root / ".aw/runs/run-test"

            def verifier_spawner(
                prompt_path: Path,
                plan_path: Path,
                work_dir: Any,
                tracker: Any,
                attempt_no: int,
            ) -> tuple[int, str, Path, list[str]]:
                log_file = run_dir / "logs/01-tst001-attempt-1-verify.jsonl"
                log_file.parent.mkdir(parents=True, exist_ok=True)
                log_file.write_text("{}", encoding="utf-8")
                return 0, "sess-v-1", log_file, ["mock_verifier"]

            state, item = _drive_execute_turn(
                repo_root,
                plan_file,
                spawn_verifier=verifier_spawner,
                validate=True,
            )

            attempt = item["attempts"][0]
            assert "corroboration_verdict" not in attempt
            assert "corroboration_reason" not in attempt
            assert "corroboration_counts" not in attempt
            assert "corroboration_verdict" not in item
            assert "corroboration_reason" not in item
            assert "corroboration_counts" not in item

    def test_cross_driver_symmetry(self) -> None:
        """E-05: Assert oc_runipd and agy_runipd re-export format_verifier_evidence_section identically."""
        assert (
            oc_runipd.format_verifier_evidence_section
            is runner_shared.format_verifier_evidence_section
        )
        assert (
            agy_runipd.format_verifier_evidence_section
            is runner_shared.format_verifier_evidence_section
        )

    def test_format_verifier_evidence_section_preserves_byte_identical_when_empty_and_renders_verdict(
        self,
    ) -> None:
        """E-03 / V-03: Empty verification evidence returns [] identically; populated evidence renders verdict."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            outcomes_dir = run_dir / "outcomes"
            outcomes_dir.mkdir(parents=True, exist_ok=True)

            # 1. Empty case: no verification evidence -> returns []
            state_empty = {
                "queue": [
                    {
                        "position": 1,
                        "id6": "abc123",
                        "verification_status": "unverified",
                    }
                ]
            }
            assert (
                runner_shared.format_verifier_evidence_section(state_empty, run_dir)
                == []
            )

            # 2. Populated case with corroboration verdict
            v_outcome = outcomes_dir / "01-abc123-verification.json"
            v_outcome.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id6": "abc123",
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m pytest tests/"],
                    }
                ),
                encoding="utf-8",
            )
            state_pop = {
                "queue": [
                    {
                        "position": 1,
                        "id6": "abc123",
                        "verification_status": "verified",
                        "tests_run": ["python3 -m pytest tests/"],
                        "corroboration_verdict": "corroborated",
                        "corroboration_reason": "corroborated",
                    }
                ]
            }
            lines = runner_shared.format_verifier_evidence_section(state_pop, run_dir)
            report_text = "\n".join(lines)
            assert "## Verification evidence" in report_text
            assert "- `abc123` (position 1):" in report_text
            assert "  - Tests run:" in report_text
            assert "    - `python3 -m pytest tests/`" in report_text
            assert (
                "  - Corroboration: corroborated (reason: corroborated)" in report_text
            )
            assert "  - Corrections made:" in report_text

            # Check adjacency: Corroboration line immediately follows Tests run section
            idx_tests = lines.index("  - Tests run:")
            idx_cmd = lines.index("    - `python3 -m pytest tests/`")
            idx_corr = lines.index(
                "  - Corroboration: corroborated (reason: corroborated)"
            )
            assert idx_tests < idx_cmd < idx_corr < lines.index("  - Corrections made:")

    def test_step_summary_surfaces_corroboration_verdict_and_backward_compatible(
        self,
    ) -> None:
        """E-04 / V-04: StepSummary surfaces corroboration verdict in human details, --json, and --agent."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            outcomes_dir = run_dir / "outcomes"
            outcomes_dir.mkdir(parents=True, exist_ok=True)

            # Case A: Carry corroboration field
            state_file = run_dir / "state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "run_id": "run-test-carry",
                        "queue": [
                            {
                                "position": 1,
                                "id6": "abc123",
                                "setid": "testset",
                                "status": "executed",
                                "verification_status": "verified",
                                "tests_run": ["python3 -m pytest tests/"],
                                "corroboration_verdict": "corroborated",
                                "corroboration_reason": "corroborated",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            v_outcome = outcomes_dir / "01-abc123-verification.json"
            v_outcome.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id6": "abc123",
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m pytest tests/"],
                        "corroboration_verdict": "corroborated",
                        "corroboration_reason": "corroborated",
                    }
                ),
                encoding="utf-8",
            )

            summary = run_viewer.load_run_summary(run_dir)
            assert summary is not None
            assert len(summary.steps) == 1
            step = summary.steps[0]
            assert step.corroboration_verdict == "corroborated"
            assert step.corroboration_reason == "corroborated"

            # Check asdict serialization (powers --json and --agent)
            payload = asdict(step)
            assert "corroboration_verdict" in payload
            assert payload["corroboration_verdict"] == "corroborated"
            assert "corroboration_reason" in payload
            assert payload["corroboration_reason"] == "corroborated"

            # Check human details rendering
            term = Term(color=False)
            details = run_viewer.render_step_details([step], term)
            details_str = "\n".join(details)
            assert "corroboration: corroborated (reason: corroborated)" in details_str
            assert "test: python3 -m pytest tests/" in details_str

            # Case B: Backward compatibility: state carries NO corroboration field
            state_file_old = run_dir / "state.json"
            state_file_old.write_text(
                json.dumps(
                    {
                        "run_id": "run-test-old",
                        "queue": [
                            {
                                "position": 1,
                                "id6": "abc123",
                                "setid": "testset",
                                "status": "executed",
                                "verification_status": "verified",
                                "tests_run": ["python3 -m pytest tests/"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            v_outcome.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id6": "abc123",
                        "verdict": "VERIFIED",
                        "tests_run": ["python3 -m pytest tests/"],
                    }
                ),
                encoding="utf-8",
            )

            summary_old = run_viewer.load_run_summary(run_dir)
            assert summary_old is not None
            step_old = summary_old.steps[0]
            assert step_old.corroboration_verdict is None
            assert step_old.corroboration_reason is None

            # asdict serializes without error
            payload_old = asdict(step_old)
            assert payload_old["corroboration_verdict"] is None

            # Details renders cleanly with NO corroboration line and NO error
            details_old = run_viewer.render_step_details([step_old], term)
            details_old_str = "\n".join(details_old)
            assert "corroboration" not in details_old_str
            assert "test: python3 -m pytest tests/" in details_old_str
