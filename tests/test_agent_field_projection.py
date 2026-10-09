"""Tests for agent record field projection (token control) under aw.agent/v1.

Pins the contract that filtering/projecting fields with --fields preserves not only the
mandatory envelope fields, but also every field required for a record of any kind to remain
valid according to validate_agent_record.
"""

from __future__ import annotations

import io
import itertools
import json
from typing import Any, Dict, List


from agent_workflows import cli
from agent_workflows.agent_schema import (
    _MANDATORY_FIELDS,
    filter_record_fields,
    is_valid_agent_record,
)
from agent_workflows.renderers import AgentRenderer, OutputContext, OutputMode
from agent_workflows.result_types import CommandResult


CORPUS: List[Dict[str, Any]] = [
    {
        "schema": "aw.agent/v1",
        "kind": "result",
        "cmd": "check plans",
        "outcome": "clean",
        "exit": 0,
        "verified": True,
        "complete": True,
        "findings": 0,
        "target": "plans/foo",
        "evidence": ["lint:ok"],
    },
    {
        "schema": "aw.agent/v1",
        "kind": "result",
        "cmd": "rename plans",
        "outcome": "clean",
        "exit": 0,
        "verified": True,
        "complete": False,
        "applied": False,
        "findings": 0,
        "target": "plans/bar",
    },
    {
        "schema": "aw.agent/v1",
        "kind": "result",
        "cmd": "rename plans",
        "outcome": "preview",
        "exit": 0,
        "verified": True,
        "complete": False,
        "applied": False,
        "changes": ["a.txt"],
    },
    {
        "schema": "aw.agent/v1",
        "kind": "result",
        "cmd": "check specs",
        "outcome": "findings",
        "exit": 1,
        "verified": True,
        "complete": True,
        "findings": 2,
        "diagnostics": [{"rule": "test"}],
    },
    {
        "schema": "aw.agent/v1",
        "kind": "summary",
        "cmd": "find plans",
        "outcome": "clean",
        "exit": 0,
        "total": 5,
        "emitted": 5,
        "omitted": 0,
        "complete": True,
        "next": None,
    },
    {
        "schema": "aw.agent/v1",
        "kind": "summary",
        "cmd": "find plans",
        "outcome": "clean",
        "exit": 0,
        "total": 10,
        "emitted": 3,
        "omitted": 7,
        "complete": False,
        "next": "aw find plans --limit 10",
    },
    {
        "schema": "aw.agent/v1",
        "kind": "summary",
        "cmd": "attention",
        "outcome": "findings",
        "exit": 1,
        "total": 8,
        "emitted": 4,
        "omitted": 4,
        "complete": False,
    },
    {
        "schema": "aw.agent/v1",
        "kind": "item",
        "cmd": "find plans",
        "item": "20260928-plan.md",
        "status": "ready",
    },
    {
        "schema": "aw.agent/v1",
        "kind": "item",
        "cmd": "find plans",
        "item": "20260928-plan2.md",
        "status": "active",
        "details": {"key": "val"},
    },
    {
        "schema": "aw.agent/v1",
        "kind": "error",
        "cmd": "check",
        "outcome": "cannot-run",
        "exit": 2,
        "verified": False,
        "complete": False,
        "next": "aw check --help",
    },
]


def test_summary_field_projection_retains_required_count_fields():
    """FIRST assertion: render_summary with fields projection returns a valid record.

    Verbatim reproduction from backlog 3f4ayi: render_summary with ctx.fields=['cmd']
    must return a string that parses as JSON and satisfies is_valid_agent_record,
    rather than raising ValueError for missing total/emitted/omitted.
    """
    ctx = OutputContext(
        mode=OutputMode.AGENT,
        stdout=io.StringIO(),
        stderr=io.StringIO(),
        fields=["cmd"],
    )
    rendered = AgentRenderer().render_summary(
        "x",
        total=1,
        emitted=1,
        omitted=0,
        outcome="clean",
        exit_code=0,
        context=ctx,
    )
    data = json.loads(rendered)
    assert is_valid_agent_record(data)
    assert data["total"] == 1
    assert data["emitted"] == 1
    assert data["omitted"] == 0


def test_result_preview_projection_retains_applied():
    """SECOND assertion: result-kind preview projection retains applied via ordinary render.

    Exercises F-03 through the ordinary AgentRenderer.render path rather than stream helper.
    Projecting with fields must return a valid record retaining applied=False, avoiding greenwash violation.
    """
    ctx = OutputContext(
        mode=OutputMode.AGENT,
        stdout=io.StringIO(),
        stderr=io.StringIO(),
        fields=["findings"],
    )
    cmd_res = CommandResult(
        command="rename plans",
        status="clean",
        exit_code=0,
        complete=False,
        verified=True,
        applied=False,
    )
    rendered = AgentRenderer().render(cmd_res, ctx)
    data = json.loads(rendered)
    assert is_valid_agent_record(data)
    assert data.get("applied") is False


def test_derived_property_required_fields_preserved_under_projection():
    """THIRD assertion: self-maintaining derivation over corpus spanning all four kinds.

    For every field k in each record, if deleting k alone makes the record invalid,
    then a non-empty projection of that record (fields=['cmd']) must still contain k.
    """
    missing_required = []
    for record in CORPUS:
        assert is_valid_agent_record(
            record
        ), f"Corpus record not valid unprojected: {record}"
        for k in record:
            rec_without_k = {key: v for key, v in record.items() if key != k}
            if not is_valid_agent_record(rec_without_k):
                # Deleting k makes the record invalid, so k is required for validity.
                # Project with non-empty fields list:
                projected = filter_record_fields(record, fields=["cmd"])
                if k not in projected:
                    missing_required.append(k)

    assert (
        missing_required == []
    ), f"Required-but-not-preserved fields found: {sorted(set(missing_required))}"


def test_projection_anti_overreach_and_combinatorial_sweep():
    """FOURTH assertion: anti-overreach properties and combinatorial sweep.

    A projection must add no key absent from the source record, must never alter
    a retained value, and must still drop unrequested fields that the validator
    does not consult (e.g. projecting a result with fields=['findings'] omits
    target and evidence while retaining findings).
    """
    # Specific anti-overreach check:
    res_rec = {
        "schema": "aw.agent/v1",
        "kind": "result",
        "cmd": "check plans",
        "outcome": "clean",
        "exit": 0,
        "verified": True,
        "complete": True,
        "findings": 0,
        "target": "plans/foo",
        "evidence": ["lint:ok"],
    }
    proj_res = filter_record_fields(res_rec, fields=["findings"])
    assert "target" not in proj_res
    assert "evidence" not in proj_res
    assert proj_res.get("findings") == 0

    # Exhaustive combinatorial sweep over non-envelope keys
    for record in CORPUS:
        non_env = [k for k in record if k not in _MANDATORY_FIELDS]
        for r in range(len(non_env) + 1):
            for subset in itertools.combinations(non_env, r):
                fields_arg = list(subset) if subset else ["cmd"]
                projected = filter_record_fields(record, fields=fields_arg)
                # Adds no key absent from source
                assert set(
                    projected.keys()
                ).issubset(
                    set(record.keys())
                ), f"Keys added in projection: {set(projected.keys()) - set(record.keys())}"
                # Never alters a retained value
                for k, v in projected.items():
                    assert (
                        v == record[k]
                    ), f"Value altered for key {k}: {v} != {record[k]}"


def test_cli_projection_releases_show_retains_next(tmp_path, capsys):
    """E-01: aw releases show preserves non-null next across --fields projection."""
    (tmp_path / ".aw" / "records" / "releases").mkdir(parents=True, exist_ok=True)
    tmp = str(tmp_path)
    # 1. Unprojected run
    capsys.readouterr()
    cli.main(["releases", "show", "zzzzzz", "--dir", tmp, "--agent"])
    out_unproj, _ = capsys.readouterr()
    lines_unproj = [line for line in out_unproj.strip().splitlines() if line.strip()]
    assert len(lines_unproj) == 1, f"Expected exactly 1 record, got: {lines_unproj}"
    rec_unproj = json.loads(lines_unproj[0])
    assert rec_unproj.get("schema") == "aw.agent/v1"
    assert rec_unproj.get("next") == "aw releases list"

    # 2. Projected run with --fields findings
    cli.main(
        [
            "releases",
            "show",
            "zzzzzz",
            "--dir",
            tmp,
            "--agent",
            "--fields",
            "findings",
        ]
    )
    out_proj, _ = capsys.readouterr()
    lines_proj = [line for line in out_proj.strip().splitlines() if line.strip()]
    assert len(lines_proj) == 1, f"Expected exactly 1 record, got: {lines_proj}"
    rec_proj = json.loads(lines_proj[0])
    assert rec_proj.get("schema") == "aw.agent/v1"
    assert rec_proj.get("next") == rec_unproj.get("next")
    assert rec_proj.get("next") == "aw releases list"


def test_cli_projection_runs_query_retains_next(tmp_path, capsys):
    """E-01: aw runs query preserves non-null next across --fields projection."""
    tmp = str(tmp_path)
    # 1. Unprojected run
    capsys.readouterr()
    cli.main(["runs", "query", "bogusview", "--dir", tmp, "--agent"])
    out_unproj, _ = capsys.readouterr()
    lines_unproj = [line for line in out_unproj.strip().splitlines() if line.strip()]
    assert len(lines_unproj) == 1, f"Expected exactly 1 record, got: {lines_unproj}"
    rec_unproj = json.loads(lines_unproj[0])
    assert rec_unproj.get("schema") == "aw.agent/v1"
    assert rec_unproj.get("next") == "aw runs query schema"

    # 2. Projected run with --fields findings
    cli.main(
        [
            "runs",
            "query",
            "bogusview",
            "--dir",
            tmp,
            "--agent",
            "--fields",
            "findings",
        ]
    )
    out_proj, _ = capsys.readouterr()
    lines_proj = [line for line in out_proj.strip().splitlines() if line.strip()]
    assert len(lines_proj) == 1, f"Expected exactly 1 record, got: {lines_proj}"
    rec_proj = json.loads(lines_proj[0])
    assert rec_proj.get("schema") == "aw.agent/v1"
    assert rec_proj.get("next") == rec_unproj.get("next")
    assert rec_proj.get("next") == "aw runs query schema"


def test_summary_field_projection_retains_next_continuation():
    """E-02: render_summary with fields projection retains non-null next continuation command."""
    ctx = OutputContext(
        mode=OutputMode.AGENT,
        stdout=io.StringIO(),
        stderr=io.StringIO(),
        fields=["cmd"],
    )
    rendered = AgentRenderer().render_summary(
        "runs query",
        total=5,
        emitted=2,
        omitted=3,
        outcome="clean",
        exit_code=0,
        next_cmd="aw runs query --offset 2",
        complete=False,
        context=ctx,
    )
    data = json.loads(rendered)
    assert is_valid_agent_record(data)
    assert data.get("next") == "aw runs query --offset 2"
