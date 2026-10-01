"""Behavioral tests for runner_fork_scan module-level constants census and resolution.

Drives the scanner exclusively over fixture modules in tmp_path via package_dir override,
never asserting on production agent_workflows source (conforming to P16).
"""

from __future__ import annotations

import pathlib
import sys
import pytest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import runner_fork_scan as rfs  # noqa: E402


def _setup_fixture_tree(
    tmp_path: pathlib.Path,
    oc_code: str,
    agy_code: str,
    shared_code: str,
) -> None:
    (tmp_path / "oc_runipd.py").write_text(oc_code, encoding="utf-8")
    (tmp_path / "agy_runipd.py").write_text(agy_code, encoding="utf-8")
    (tmp_path / "runner_shared.py").write_text(shared_code, encoding="utf-8")


def test_host_pair_divergent_constant_reported_with_values(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Property 1: A host-pair divergent constant is reported with both values."""
    shared = """
class HostLabels:
    def __init__(self, full_auto_actor: str):
        self.full_auto_actor = full_auto_actor

OC_HOST_LABELS = HostLabels(full_auto_actor="aw oc run --full-auto")
AGY_HOST_LABELS = HostLabels(full_auto_actor="aw agy run --full-auto")
"""
    oc = "FULL_AUTO_ACTOR = runner_shared.OC_HOST_LABELS.full_auto_actor\n"
    agy = "FULL_AUTO_ACTOR = runner_shared.AGY_HOST_LABELS.full_auto_actor\n"

    _setup_fixture_tree(tmp_path, oc, agy, shared)
    monkeypatch.setattr(rfs, "package_dir", lambda: tmp_path)

    data = rfs.census()
    cdata = data["constants"]

    assert cdata["host_pair_divergent"] == ["FULL_AUTO_ACTOR"]
    assert cdata["unresolved"] == []
    assert cdata["three_way_matches_neither"] == []
    assert cdata["values"]["FULL_AUTO_ACTOR"]["oc"] == "'aw oc run --full-auto'"
    assert cdata["values"]["FULL_AUTO_ACTOR"]["agy"] == "'aw agy run --full-auto'"

    rendered = rfs.render(
        data,
        closure=False,
        hazards=False,
        triples=False,
        repo_wide=False,
        constants=True,
    )
    assert "MODULE-LEVEL CONSTANTS" in rendered
    assert "READ, DO NOT RULE" in rendered
    assert "FULL_AUTO_ACTOR" in rendered
    assert "oc : 'aw oc run --full-auto'" in rendered
    assert "agy: 'aw agy run --full-auto'" in rendered


def test_same_value_different_reference_not_divergent(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Property 2: Different references resolving to the same value report as agreeing.

    This is the false-positive class a source-text comparison gets wrong:
    'runner_shared.MSG' != 'runner_shared.ALIAS' as AST source text, but both
    resolve to 'same-text'. Static resolution must report this as agreeing.
    """
    shared = """
MSG = "same-text"
ALIAS = "same-text"
"""
    oc = "GREETING = runner_shared.MSG\n"
    agy = "GREETING = runner_shared.ALIAS\n"

    _setup_fixture_tree(tmp_path, oc, agy, shared)
    monkeypatch.setattr(rfs, "package_dir", lambda: tmp_path)

    data = rfs.census()
    cdata = data["constants"]

    assert "GREETING" in cdata["co_defined"]
    assert cdata["host_pair_divergent"] == []
    assert cdata["unresolved"] == []


def test_three_way_matches_neither(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Property 3: Three-way constant where shared matches neither host is reported."""
    shared = 'SETTING = "shared_default"\n'
    oc = 'SETTING = "host_override"\n'
    agy = 'SETTING = "host_override"\n'

    _setup_fixture_tree(tmp_path, oc, agy, shared)
    monkeypatch.setattr(rfs, "package_dir", lambda: tmp_path)

    data = rfs.census()
    cdata = data["constants"]

    assert cdata["three_way_matches_neither"] == ["SETTING"]
    assert cdata["host_pair_divergent"] == []
    assert cdata["unresolved"] == []
    assert cdata["values"]["SETTING"]["sh"] == "'shared_default'"
    assert cdata["values"]["SETTING"]["oc"] == "'host_override'"
    assert cdata["values"]["SETTING"]["agy"] == "'host_override'"


def test_unresolvable_chain_reported_in_unresolved(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Property 4: Constant with unresolvable or cyclic chain reported in unresolved."""
    shared = "LOOP = runner_shared.LOOP\n"
    oc = "LOOP = runner_shared.LOOP\n"
    agy = "LOOP = runner_shared.LOOP\n"

    _setup_fixture_tree(tmp_path, oc, agy, shared)
    monkeypatch.setattr(rfs, "package_dir", lambda: tmp_path)

    data = rfs.census()
    cdata = data["constants"]

    assert cdata["unresolved"] == ["LOOP"]
    assert cdata["host_pair_divergent"] == []
    assert cdata["three_way_matches_neither"] == []


def test_tuple_target_constant_collected_in_unresolved(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Property 5: Module-scope tuple-target constant is collected and lands in unresolved."""
    shared = ""
    oc = "TUP_A, TUP_B = 1, 2\n"
    agy = "TUP_A, TUP_B = 1, 2\n"

    _setup_fixture_tree(tmp_path, oc, agy, shared)
    monkeypatch.setattr(rfs, "package_dir", lambda: tmp_path)

    data = rfs.census()
    cdata = data["constants"]

    assert "TUP_A" in cdata["co_defined"]
    assert "TUP_B" in cdata["co_defined"]
    assert "TUP_A" in cdata["unresolved"]
    assert "TUP_B" in cdata["unresolved"]
    assert cdata["host_pair_divergent"] == []
