"""Behavioral test coverage for benchmark_manifest digest keys.

Addresses backlog item g5ypvb and findings wo21z5 by exercising
BenchmarkManifest.digest, Ceilings.digest, and _digest through the public
API to verify digest shape, determinism, differential sensitivity, usage
invariance, and ceilings digest cross-referencing.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from agent_workflows import benchmark_manifest as bm

pytestmark = pytest.mark.core

HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _ceilings(
    trial_count: int = 3,
    host_reports_tokens: bool = False,
    per_trial_wall_seconds: float = 600.0,
) -> bm.Ceilings:
    return bm.make_ceilings(
        per_trial_wall_seconds=per_trial_wall_seconds,
        trial_count=trial_count,
        token_ceiling=100000 if host_reports_tokens else None,
        host_reports_tokens=host_reports_tokens,
    )


def _manifest(**overrides: Any) -> bm.BenchmarkManifest:
    kwargs: dict[str, Any] = {
        "model_id": "its_direct/pt3-claude-opus",
        "reasoning_effort": "medium",
        "host": "opencode",
        "host_version": "1.2.3",
        "adapter_digest": "a" * 64,
        "workflow_digest": "b" * 64,
        "tool_policy_digest": "c" * 64,
        "task_seed": "simple_commands-001",
        "trial": 0,
        "timeout_seconds": 600.0,
        "ceilings": _ceilings(),
        "environment_fingerprint": "d" * 64,
    }
    kwargs.update(overrides)
    return bm.build_manifest(**kwargs)


def test_manifest_and_ceilings_digest_format():
    manifest = _manifest()
    ceilings = _ceilings()

    manifest_digest = manifest.digest()
    assert isinstance(manifest_digest, str)
    assert HEX64_PATTERN.fullmatch(manifest_digest) is not None

    ceilings_digest = ceilings.digest()
    assert isinstance(ceilings_digest, str)
    assert HEX64_PATTERN.fullmatch(ceilings_digest) is not None


def test_digest_deterministic_equality():
    manifest_a = _manifest()
    manifest_b = _manifest()
    assert manifest_a.digest() == manifest_b.digest()

    ceilings_a = _ceilings()
    ceilings_b = _ceilings()
    assert ceilings_a.digest() == ceilings_b.digest()


def test_manifest_digest_distinguishes_trial_and_reasoning_effort():
    base = _manifest(trial=0, reasoning_effort="medium")
    different_trial = _manifest(trial=1, reasoning_effort="medium")
    different_reasoning = _manifest(trial=0, reasoning_effort="high")

    assert base.digest() != different_trial.digest()
    assert base.digest() != different_reasoning.digest()


def test_ceilings_and_manifest_digest_distinguish_trial_count():
    ceilings_a = _ceilings(trial_count=3)
    ceilings_b = _ceilings(trial_count=4)
    assert ceilings_a.digest() != ceilings_b.digest()

    manifest_a = _manifest(ceilings=ceilings_a)
    manifest_b = _manifest(ceilings=ceilings_b)
    assert manifest_a.digest() != manifest_b.digest()


def test_manifest_digest_unaffected_by_usage():
    manifest = _manifest()
    exported = manifest.to_dict()
    exported["usage"]["wall_time"] = 12.5
    round_tripped = bm.manifest_from_dict(exported)
    assert manifest.digest() == round_tripped.digest()


def test_manifest_identity_ceilings_digest_matches_ceilings():
    ceilings = _ceilings()
    manifest = _manifest(ceilings=ceilings)

    ceilings_digest = ceilings.digest()
    manifest_ceilings_digest = manifest.identity["ceilings_digest"]

    assert manifest_ceilings_digest == ceilings_digest
    assert isinstance(manifest_ceilings_digest, str)
    assert HEX64_PATTERN.fullmatch(manifest_ceilings_digest) is not None
