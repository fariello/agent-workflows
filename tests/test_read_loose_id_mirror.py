"""Behavioral tests for artifact_meta.read_loose_id on post-cutover mirrors (backlog 91eazx)."""

from __future__ import annotations

import pytest

from agent_workflows import agy_runipd, artifact_meta, oc_runipd

pytestmark = pytest.mark.core


def test_read_loose_id_reads_yaml_and_prompt_mirrors_and_legacy_bullets() -> None:
    """read_loose_id resolves post-cutover YAML/prompt mirrors and preserves legacy bullet behavior."""
    yaml_mirror = "---\nid: ab12cd\nstatus: approved\n---\n\n# IPD: Example\n"
    yaml_mirror_bom = (
        "\ufeff---\nid: ef34gh\nstatus: to-review\n---\n\n# Spec: Example\n"
    )
    yaml_statusless = "---\nid: st9876\n---\n\n# Walkthrough\n"
    prompt_mirror = (
        "<!-- aw-managed-prompt: id: pr1234 status: pending -->\n\n# Prompt\n"
    )
    legacy_bullet = (
        "# IPD: Legacy\n\n- Id: lg5678\n- Status: approved\n\n## Goal\nBody.\n"
    )
    quoted_body_only = "# Notes\n\n## Body\n\n- Id: fake00\n"

    assert artifact_meta.read_loose_id(yaml_mirror) == "ab12cd"
    assert artifact_meta.read_loose_id(yaml_mirror_bom) == "ef34gh"
    assert artifact_meta.read_loose_id(yaml_statusless) == "st9876"
    assert artifact_meta.read_loose_id(prompt_mirror) == "pr1234"
    assert artifact_meta.read_loose_id(legacy_bullet) == "lg5678"
    assert artifact_meta.read_loose_id(quoted_body_only) is None
    assert artifact_meta.read_loose_id("") is None


def test_host_runners_read_id_resolve_post_cutover_yaml_mirror() -> None:
    """Both oc_runipd._read_id and agy_runipd._read_id resolve post-cutover YAML mirrors."""
    yaml_mirror = "---\nid: rn90ab\nstatus: approved\n---\n\n# IPD: Runner Target\n"
    assert oc_runipd._read_id(yaml_mirror) == "rn90ab"
    assert agy_runipd._read_id(yaml_mirror) == "rn90ab"
