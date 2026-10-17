"""The `/plain` repair command is delivered to both hosts and points at its workflow body.

Plain-language research (`ng0ga4`; reports 8tcq84, o7v25q, ky28a9, ne3jy6) found the user's
"plain version" correction is the one remedy observed to work. `/plain` makes that correction a
command, so these tests check it is actually installed and reachable, not how it is worded.
"""

from __future__ import annotations

import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from agent_workflows import engine, reporting_contract
from tests.support import SOURCE_WORKFLOWS, init_repo


def test_plain_is_a_manifest_command_with_a_real_body() -> None:
    wfs = {w.command: w for w in engine.parse_manifest(SOURCE_WORKFLOWS)}
    assert "plain" in wfs
    body = SOURCE_WORKFLOWS.parents[2] / wfs["plain"].body
    assert body.is_file(), body


@pytest.mark.parametrize("tool", ["opencode", "claude"])
@pytest.mark.parametrize("layout", ["aw", "legacy"])
def test_plain_shim_points_at_its_body_and_is_supported(tool: str, layout: str) -> None:
    wf = {w.command: w for w in engine.parse_manifest(SOURCE_WORKFLOWS)}["plain"]
    shim = engine.shim_body("plain", wf, tool, target_layout=layout)
    assert engine.validate_shim_grammar(shim, tool)
    assert "plain/plain.md" in shim
    assert "Supported alias" in shim and "Deprecation notice" not in shim
    assert shim.endswith(reporting_contract.shim_pointer_line())


@pytest.mark.slow
def test_installer_delivers_plain_and_the_repair_rule() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = init_repo(Path(td) / "target")
        with redirect_stdout(io.StringIO()):
            engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)
        for path in (".opencode/commands/plain.md", ".claude/commands/plain.md"):
            assert (repo / path).is_file(), path
        agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
        assert reporting_contract.contract_text() in agents
