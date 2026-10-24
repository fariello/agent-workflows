"""Behavioral tests for RunnerAdapter.adapter_digest and TrialResult.to_dict.

Restores behavioral coverage for benchmark runner payload keys recorded in backlog
item l9ssp6 (Set trimgap), plan rempo8, and research findings wo21z5.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import pytest

from agent_workflows.benchmark_corpus import SeededTask
from agent_workflows.benchmark_runners import (
    ModelProfile,
    RunnerAdapter,
    RunnerDouble,
)

pytestmark = pytest.mark.core

TASK = SeededTask(
    task_class="simple_commands",
    seed_id="t1",
    task={},
    seed_path=Path("/tmp/x"),
)
PROFILE = ModelProfile(
    model_id="m1",
    reasoning_effort="high",
    display_name="M",
    vendor="v",
)


class AdapterDigestTests(unittest.TestCase):
    """Behavioral tests for RunnerAdapter.adapter_digest calculation and manifest stamping."""

    def test_adapter_digest_pinned_and_canonical_json(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        expected_hex = (
            "da913cd8c86eabc9e0caac47030459a3ba9b7b9b41401b9a69ea6a6bf3c40924"
        )
        assert adapter.adapter_digest() == expected_hex
        canonical_json = json.dumps(
            {"host": "opencode", "host_version": "1.2.3", "extra_flags": ["--x"]},
            sort_keys=True,
            separators=(",", ":"),
        )
        assert (
            adapter.adapter_digest()
            == hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        )

    def test_adapter_digest_equality_and_sensitivity(self) -> None:
        a1 = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        a2 = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        assert a1.adapter_digest() == a2.adapter_digest()

        no_flags = RunnerAdapter("opencode", "1.2.3")
        assert (
            no_flags.adapter_digest()
            == "09f15fb5d5f124764dc4e7edcd8cb5f94158e1c002c7bdb6cf2a1ecdba7c0b74"
        )

        bumped_version = RunnerAdapter("opencode", "1.2.4")
        assert (
            bumped_version.adapter_digest()
            == "a9732341a1dc81c8126e7c8fd88ced68c22fa0e278a421305b77d1f826cbbb0c"
        )
        assert no_flags.adapter_digest() != bumped_version.adapter_digest()
        assert no_flags.adapter_digest() != a1.adapter_digest()

    def test_adapter_digest_reaches_trial_manifest(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3", extra_flags=["--x"])
        runner = RunnerDouble(adapter, default_outcome="success")
        result = runner.run_trial(TASK, PROFILE, trial=1)
        res_dict = result.to_dict()
        digest = res_dict["manifest"]["identity"]["adapter_digest"]
        assert digest == adapter.adapter_digest()
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)


class TrialResultToDictTests(unittest.TestCase):
    """Behavioral tests for TrialResult.to_dict serialization."""

    def test_trial_result_to_dict_timeout_payload(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3")
        runner = RunnerDouble(adapter, default_outcome="timeout")
        result = runner.run_trial(TASK, PROFILE, trial=1)
        res_dict = result.to_dict()

        expected_keys = {
            "trial_id",
            "status",
            "manifest",
            "rerun_command",
            "failure_kind",
            "error_message",
            "transcript",
            "score_result",
            "usage",
        }
        assert set(res_dict.keys()) == expected_keys
        assert res_dict["status"] == "pending"
        assert res_dict["failure_kind"] == "timeout"
        assert res_dict["score_result"] is None
        assert res_dict["transcript"] is None
        assert res_dict["manifest"] == result.manifest.to_dict()
        assert bool(res_dict["rerun_command"])
        assert res_dict["rerun_command"] == result.rerun_command

        assert json.loads(json.dumps(res_dict)) == res_dict

    def test_trial_result_to_dict_success_payload(self) -> None:
        adapter = RunnerAdapter("opencode", "1.2.3")
        runner = RunnerDouble(adapter, default_outcome="success")
        result = runner.run_trial(TASK, PROFILE, trial=1)
        res_dict = result.to_dict()

        assert res_dict["trial_id"] == "t1_m1_opencode_t1"
        assert res_dict["status"] == "completed"
        assert res_dict["failure_kind"] is None
        assert res_dict["score_result"] == {
            "verdict": "complete",
            "adversary_class": "",
            "reasons": ["no violation detected; terminal claim substantiated"],
            "claimed_complete": True,
        }

        assert json.loads(json.dumps(res_dict)) == res_dict
