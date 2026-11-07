"""Tests for prose em and en dash advisories in IPD lint, specs check, and backlog check (spec ecmw83 R-07, AC-05)."""

import argparse
from pathlib import Path
import tempfile
import pytest

from agent_workflows import (
    artifact_core,
    backlog,
    check_engine,
    ipd_lint,
    ipd_schema,
    prose_dash,
    specs,
    status_set,
)
from tests.test_ipd_lint import _conforming_child
from tests import support

pytestmark = pytest.mark.core

# --------------------------------------------------------------------------------------
# Base fixture templates for the three artifact types
# --------------------------------------------------------------------------------------

_SPEC_TEMPLATE = """# Spec: Test Spec
- Date: 2026-10-25{meta_dash}
- Status: draft
- Id: spc001

## Workflow history
- 2026-10-25 draft (test): created.

## 1. Goal
{body}
"""

_BACKLOG_TEMPLATE = """- Id: bkl001
- Status: open{meta_dash}
- Set: writestd
- Priority: high
- Work-Kind: feature
- Summary: Test summary

## Workflow history
- 2026-10-25 created (test): created.

## Problem
{body}
"""


def _make_ipd(body: str, meta_dash: str = "") -> str:
    plan = _conforming_child()
    if meta_dash:
        plan = plan.replace("- Concern: a concern", f"- Concern: a concern{meta_dash}")
    return plan.replace("Sample goal.", body)


def _make_spec(body: str, meta_dash: str = "") -> str:
    return _SPEC_TEMPLATE.format(body=body, meta_dash=meta_dash)


def _make_backlog(body: str, meta_dash: str = "") -> str:
    return _BACKLOG_TEMPLATE.format(body=body, meta_dash=meta_dash)


# Table-driven test cases across the 6 regions
# (region_name, body_text, meta_dash, expect_reported)
REGION_CASES = [
    (
        "prose",
        "Prose with em dash \u2014 and en dash \u2013.",
        "",
        True,
    ),
    (
        "fenced",
        "```\ncode fence with em dash \u2014 and en dash \u2013\n```",
        "",
        False,
    ),
    (
        "indented",
        "    indented code with em dash \u2014 and en dash \u2013",
        "",
        False,
    ),
    (
        "quote",
        "> block quote with em dash \u2014 and en dash \u2013",
        "",
        False,
    ),
    (
        "inline_code",
        "Prose with `code with em dash \u2014 and en dash \u2013` inside code span.",
        "",
        False,
    ),
    (
        "metadata",
        "Clean prose without dashes.",
        " \u2014 with em dash \u2013 in metadata",
        False,
    ),
]


class TestProseDashScanner:
    """Direct scanner tests for agent_workflows.prose_dash.find_prose_dashes."""

    @pytest.mark.parametrize(
        "region,body,meta_dash,expect_reported",
        REGION_CASES,
    )
    def test_scanner_regions(self, region, body, meta_dash, expect_reported):
        text = _make_spec(body, meta_dash)
        dashes = prose_dash.find_prose_dashes(text)
        if expect_reported:
            assert len(dashes) == 2
            chars = [d[2] for d in dashes]
            assert "\u2014" in chars
            assert "\u2013" in chars
        else:
            assert len(dashes) == 0

    def test_yaml_front_matter_excluded(self):
        text = """---
title: YAML with em dash \u2014 and en dash \u2013
---
## Heading
Prose line.
"""
        assert prose_dash.find_prose_dashes(text) == []


class TestTableDrivenArtifactAdvisories:
    """Table-driven advisory checks for each artifact type across all regions."""

    @pytest.mark.parametrize(
        "region,body,meta_dash,expect_reported",
        REGION_CASES,
    )
    def test_ipd_dash_advisory(self, region, body, meta_dash, expect_reported):
        text = _make_ipd(body, meta_dash)
        res = ipd_lint.lint_text(text, checkpoint="author", directory="pending")
        # Disposition must always be conforming
        assert res.disposition == ipd_schema.DISPOSITION_CONFORMING
        assert res.passing is True
        # Blocking diagnostics must be empty
        assert res.diagnostics == []

        dash_advisories = [a for a in res.advisories if a.code == ipd_lint.C_PROSE_DASH]
        if expect_reported:
            assert len(dash_advisories) == 2
            for adv in dash_advisories:
                assert adv.code == "IPD-C802"
                assert "spec ecmw83 R-07" in adv.message
        else:
            assert len(dash_advisories) == 0

    @pytest.mark.parametrize(
        "region,body,meta_dash,expect_reported",
        REGION_CASES,
    )
    def test_spec_dash_advisory(self, region, body, meta_dash, expect_reported):
        text = _make_spec(body, meta_dash)
        path = Path(".aw/records/specs/draft/20261025-spc001-01-spc001-test.spec.md")
        advisories = specs.prose_dash_advisories(path, text)
        assert artifact_core.drift_exit_code(advisories) == 0

        dash_advisories = [a for a in advisories if a.rule == "spec.prose-dash"]
        if expect_reported:
            assert len(dash_advisories) == 2
            for adv in dash_advisories:
                assert adv.severity == "info"
                assert adv.rule == "spec.prose-dash"
                assert "spec ecmw83 R-07" in adv.detail
        else:
            assert len(dash_advisories) == 0

    @pytest.mark.parametrize(
        "region,body,meta_dash,expect_reported",
        REGION_CASES,
    )
    def test_backlog_dash_advisory(self, region, body, meta_dash, expect_reported):
        text = _make_backlog(body, meta_dash)
        path = Path(
            ".aw/records/backlog/open/20261025-writestd-01-bkl001-test.backlog.md"
        )
        advisories = backlog.prose_dash_advisories(path, text)
        assert artifact_core.drift_exit_code(advisories) == 0

        dash_advisories = [a for a in advisories if a.rule == "backlog.prose-dash"]
        if expect_reported:
            assert len(dash_advisories) == 2
            for adv in dash_advisories:
                assert adv.severity == "info"
                assert adv.rule == "backlog.prose-dash"
                assert "spec ecmw83 R-07" in adv.detail
        else:
            assert len(dash_advisories) == 0


class TestRequiredInvariants:
    """Specific required invariants (a) through (d) from plan k2x0yl E-04."""

    def test_a_validators_return_no_prose_dash_drift(self):
        """(a) specs.validate_spec and backlog.validate_item return no *.prose-dash drift for a dash-bearing artifact."""
        dash_spec = _make_spec("Prose with em dash \u2014 and en dash \u2013.")
        spec_drift = specs.validate_spec(
            Path(".aw/records/specs/draft/20261025-spc001-01-spc001-test.spec.md"),
            dash_spec,
        )
        assert not any(d.rule == "spec.prose-dash" for d in spec_drift)
        assert spec_drift == []

        dash_backlog = _make_backlog("Problem with em dash \u2014 and en dash \u2013.")
        backlog_drift = backlog.validate_item(
            Path(
                ".aw/records/backlog/open/20261025-writestd-01-bkl001-test.backlog.md"
            ),
            dash_backlog,
        )
        assert not any(d.rule == "backlog.prose-dash" for d in backlog_drift)
        assert backlog_drift == []

    def test_b_no_error_added_proof_shape(self):
        """(b) the no-error-added proof shape for both rules:
        check_engine.rule_spec(rule).severity == "info", and
        artifact_core.drift_exit_code(drift) == 0 on the real advisory list while
        the same list with severity replaced by "error" exits 1.
        """
        for rule, adv_fn, make_fn, path in [
            (
                "spec.prose-dash",
                specs.prose_dash_advisories,
                _make_spec,
                Path(".aw/records/specs/draft/20261025-spc001-01-spc001-test.spec.md"),
            ),
            (
                "backlog.prose-dash",
                backlog.prose_dash_advisories,
                _make_backlog,
                Path(
                    ".aw/records/backlog/open/20261025-writestd-01-bkl001-test.backlog.md"
                ),
            ),
        ]:
            assert check_engine.rule_spec(rule).severity == "info"

            text = make_fn("Prose with em dash \u2014 and en dash \u2013.")
            drift_list = adv_fn(path, text)
            assert len(drift_list) > 0
            assert all(d.severity == "info" for d in drift_list)

            # Real advisory list exits 0
            assert artifact_core.drift_exit_code(drift_list) == 0

            # Same list with severity replaced by "error" exits 1
            as_errors = [d._replace(severity="error") for d in drift_list]
            assert artifact_core.drift_exit_code(as_errors) == 1

    def test_c_driving_aw_specs_set_on_dash_bearing_spec_succeeds(self):
        """(c) driving aw specs set (or status_set) on a dash-bearing spec still succeeds."""
        with tempfile.TemporaryDirectory() as td:
            repo_root = support.init_repo(Path(td) / "repo")
            draft_dir = repo_root / ".aw/records/specs/draft"
            draft_dir.mkdir(parents=True)
            spec_file = draft_dir / "20261025-spc001-01-spc001-test-spec.spec.md"
            spec_file.write_text(
                _make_spec("Prose goal with em dash \u2014 and en dash \u2013.")
            )

            ns = argparse.Namespace(
                dir=str(repo_root),
                by_human=True,
                message="advance to to-review",
            )
            rc = status_set.run_set_command(
                ["to-review", "spc001"],
                repo_root=repo_root,
                args=ns,
                scoped_type="specs",
            )
            assert rc == 0
            dest = (
                repo_root
                / ".aw/records/specs/to-review/20261025-spc001-01-spc001-test-spec.spec.md"
            )
            assert dest.exists()

    def test_d_executed_plan_gets_no_c802(self):
        """(d) a dash-bearing plan under an executed/ directory gets no IPD-C802."""
        dash_plan = _make_ipd("Sample goal with em dash \u2014 and en dash \u2013.")
        dash_plan = dash_plan.replace("- Status: to-review", "- Status: executed")
        res = ipd_lint.lint_text(dash_plan, directory="executed")
        assert not any(d.code == ipd_lint.C_PROSE_DASH for d in res.advisories)
        assert not any(d.code == ipd_lint.C_PROSE_DASH for d in res.diagnostics)
        assert res.disposition == ipd_schema.DISPOSITION_LEGACY
