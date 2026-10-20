"""Behavioral tests for test prune and per-test coverage tooling (IPD qqrgv3).

Exercises percov_run, percov_analyze, pinscan, and classify on synthetic
fixture data and subprocess execution, conforming to P16.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import coverage
import pytest

from tests.tools.classify import classify_suite
from tests.tools.percov_analyze import analyze_directory, compare_directories
from tests.tools.pinscan import scan_pins, summarize_pins

_REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.core
def test_percov_analyze_synthetic_counts(tmp_path: Path) -> None:
    """Validate unique lines/arcs, identical grouping, and no_coverage detection on synthetic data."""
    cov_file = tmp_path / ".coverage"
    cd = coverage.CoverageData(str(cov_file))

    # Test A: covers (1, 2) and (2, 3) on /repo/agent_workflows/foo.py
    cd.set_context("tests/test_mod.py::test_a")
    cd.add_arcs({"/repo/agent_workflows/foo.py": [(1, 2), (2, 3)]})

    # Test B: covers (2, 3) and (3, 4) on /repo/agent_workflows/foo.py
    cd.set_context("tests/test_mod.py::test_b")
    cd.add_arcs({"/repo/agent_workflows/foo.py": [(2, 3), (3, 4)]})

    # Test C: identical coverage to Test A: covers (1, 2) and (2, 3)
    cd.set_context("tests/test_mod.py::test_c")
    cd.add_arcs({"/repo/agent_workflows/foo.py": [(1, 2), (2, 3)]})
    cd.write()

    # Test D in collected.txt has no recorded coverage
    collected_txt = (
        "tests/test_mod.py::test_a\n"
        "tests/test_mod.py::test_b\n"
        "tests/test_mod.py::test_c\n"
        "tests/test_mod.py::test_d\n"
    )
    (tmp_path / "collected.txt").write_text(collected_txt, encoding="utf-8")

    res = analyze_directory(tmp_path)
    tests = res["tests"]

    # Line 1: covered by test_a, test_c (not unique)
    # Line 2: covered by test_a, test_b, test_c (not unique)
    # Line 3: covered by test_a, test_b, test_c (not unique)
    # Line 4: covered ONLY by test_b (unique!)
    assert tests["tests/test_mod.py::test_b"]["unique_lines"] == 1
    assert (
        tests["tests/test_mod.py::test_b"]["unique_arcs"] == 1
    )  # (3, 4) is unique to b

    assert tests["tests/test_mod.py::test_a"]["unique_lines"] == 0
    assert tests["tests/test_mod.py::test_a"]["unique_arcs"] == 0

    # Identical groups for test_a and test_c
    assert (
        "tests/test_mod.py::test_c"
        in tests["tests/test_mod.py::test_a"]["identical_group"]
    )
    assert (
        "tests/test_mod.py::test_a"
        in tests["tests/test_mod.py::test_c"]["identical_group"]
    )

    # No coverage detection for test_d
    assert tests["tests/test_mod.py::test_d"]["no_coverage"] is True
    assert res["totals"]["num_no_coverage"] == 1
    assert res["totals"]["num_tests"] == 4


@pytest.mark.core
def test_percov_analyze_subset_grouping(tmp_path: Path) -> None:
    """Validate subset containment group detection."""
    cov_file = tmp_path / ".coverage"
    cd = coverage.CoverageData(str(cov_file))

    # Test Sub: subset of Test Super
    cd.set_context("tests/test_mod.py::test_sub")
    cd.add_arcs({"/repo/agent_workflows/foo.py": [(1, 2), (2, 3)]})

    # Test Super: strictly contains Test Sub and covers more
    cd.set_context("tests/test_mod.py::test_super")
    cd.add_arcs({"/repo/agent_workflows/foo.py": [(1, 2), (2, 3), (3, 4), (4, 5)]})
    cd.write()

    (tmp_path / "collected.txt").write_text(
        "tests/test_mod.py::test_sub\ntests/test_mod.py::test_super\n",
        encoding="utf-8",
    )

    res = analyze_directory(tmp_path)
    tests = res["tests"]

    assert tests["tests/test_mod.py::test_sub"]["unique_lines"] == 0
    assert (
        "tests/test_mod.py::test_super"
        in tests["tests/test_mod.py::test_sub"]["subset_group"]
    )


@pytest.mark.core
def test_percov_compare_lost_lines_and_arcs(tmp_path: Path) -> None:
    """Validate compare_directories finds lost lines and arcs between runs."""
    base_dir = tmp_path / "base"
    curr_dir = tmp_path / "curr"
    base_dir.mkdir()
    curr_dir.mkdir()

    # Baseline covers lines 10, 20 and arc (10, 20)
    cd_base = coverage.CoverageData(str(base_dir / ".coverage"))
    cd_base.set_context("ctx")
    cd_base.add_arcs({"/repo/agent_workflows/bar.py": [(10, 20), (20, 30)]})
    cd_base.write()

    # Current drops arc (20, 30) and line 30
    cd_curr = coverage.CoverageData(str(curr_dir / ".coverage"))
    cd_curr.set_context("ctx")
    cd_curr.add_arcs({"/repo/agent_workflows/bar.py": [(10, 20)]})
    cd_curr.write()

    lost_lines, lost_arcs = compare_directories(curr_dir, base_dir)
    assert any(line_entry[1] == 30 for line_entry in lost_lines)
    assert any(a[1] == 20 and a[2] == 30 for a in lost_arcs)

    # Identical comparison yields zero lost lines and arcs
    zero_lines, zero_arcs = compare_directories(base_dir, base_dir)
    assert len(zero_lines) == 0
    assert len(zero_arcs) == 0


@pytest.mark.core
def test_classifier_rules_and_precedence(tmp_path: Path) -> None:
    """Validate fixed classifier rules, protected status, and precedence."""
    # Write synthetic percov.json
    percov_data = {
        "metadata": {"has_arcs": True},
        "totals": {
            "num_tests": 5,
            "num_no_coverage": 1,
            "union_lines": 50,
            "union_arcs": 30,
        },
        "modules": {
            "tests/test_foo.py": {
                "test_count": 5,
                "zero_unique_line_count": 4,
                "zero_unique_arc_count": 4,
                "no_coverage_count": 1,
                "union_unique_lines": 0,
                "union_unique_arcs": 0,
            }
        },
        "tests": {
            "tests/test_foo.py::test_live": {
                "line_count": 10,
                "arc_count": 5,
                "unique_lines": 0,
                "unique_arcs": 0,
                "identical_group": [],
                "subset_group": [],
                "no_coverage": False,
            },
            "tests/test_foo.py::test_core": {
                "line_count": 10,
                "arc_count": 5,
                "unique_lines": 0,
                "unique_arcs": 0,
                "identical_group": [],
                "subset_group": [],
                "no_coverage": False,
            },
            "tests/test_foo.py::test_defect": {
                "line_count": 10,
                "arc_count": 5,
                "unique_lines": 0,
                "unique_arcs": 0,
                "identical_group": ["tests/test_foo.py::test_core"],
                "subset_group": [],
                "no_coverage": False,
            },
            "tests/test_foo.py::test_slow": {
                "line_count": 10,
                "arc_count": 5,
                "unique_lines": 0,
                "unique_arcs": 0,
                "identical_group": [],
                "subset_group": [],
                "no_coverage": False,
            },
            "tests/test_foo.py::test_unprotected_redundant": {
                "line_count": 10,
                "arc_count": 5,
                "unique_lines": 0,
                "unique_arcs": 0,
                "identical_group": [],
                "subset_group": [],
                "no_coverage": False,
            },
        },
    }
    (tmp_path / "percov.json").write_text(json.dumps(percov_data), encoding="utf-8")

    # Synthetic markers.json
    markers = {
        "tests/test_foo.py::test_live": ["livecorpus"],
        "tests/test_foo.py::test_core": ["core"],
        "tests/test_foo.py::test_defect": [],
        "tests/test_foo.py::test_slow": [],
        "tests/test_foo.py::test_unprotected_redundant": [],
    }
    (tmp_path / "markers.json").write_text(json.dumps(markers), encoding="utf-8")

    # Synthetic junit.xml with duration > 2s for test_slow
    junit_xml = """<testsuites>
      <testsuite name="pytest">
        <testcase classname="tests.test_foo" name="test_live" file="tests/test_foo.py" time="0.10" />
        <testcase classname="tests.test_foo" name="test_core" file="tests/test_foo.py" time="0.15" />
        <testcase classname="tests.test_foo" name="test_defect" file="tests/test_foo.py" time="0.20" />
        <testcase classname="tests.test_foo" name="test_slow" file="tests/test_foo.py" time="3.50" />
        <testcase classname="tests.test_foo" name="test_unprotected_redundant" file="tests/test_foo.py" time="0.05" />
      </testsuite>
    </testsuites>"""
    (tmp_path / "junit.xml").write_text(junit_xml, encoding="utf-8")

    classified = classify_suite(tmp_path, pin_candidates=[])
    tests = classified["test_records"]

    # Rule 1: livecorpus is never delete-candidate
    assert (
        tests["tests/test_foo.py::test_live"]["proposed_disposition"]
        != "delete-candidate"
    )

    # Rule 2: core is never delete-candidate
    assert (
        tests["tests/test_foo.py::test_core"]["proposed_disposition"]
        != "delete-candidate"
    )

    # Rule 3: test_slow duration > 2s is speed-up
    assert tests["tests/test_foo.py::test_slow"]["proposed_disposition"] == "speed-up"

    # Rule 4: unprotected 0-unique test is delete-candidate
    assert (
        tests["tests/test_foo.py::test_unprotected_redundant"]["proposed_disposition"]
        == "delete-candidate"
    )


@pytest.mark.core
def test_pinscan_fixture_candidate(tmp_path: Path) -> None:
    """Validate pinscan detects candidate patterns in a fixture test file."""
    fixture_test = tmp_path / "test_fixture.py"
    fixture_test.write_text(
        "import inspect\n"
        "import ast\n"
        "def test_inspect_call():\n"
        "    src = inspect.getsource(int)\n"
        "    tree = ast.parse('x = 1')\n",
        encoding="utf-8",
    )

    candidates = scan_pins(tmp_path)
    summary = summarize_pins(candidates)

    pattern_ids = {c["pattern_id"] for c in candidates}
    assert "inspect_getsource" in pattern_ids
    assert "ast_parse_walk" in pattern_ids
    assert summary["total_hits"] >= 2


@pytest.mark.core
def test_failing_test_refusal_metadata(tmp_path: Path) -> None:
    """Validate that meta.json records nonzero pytest exit and failing node IDs."""
    meta = {
        "git_head": "abc1234",
        "python_version": "3.14",
        "coverage_version": "7.15",
        "core": "ctrace",
        "worker_count": 6,
        "wall_time": 5.0,
        "pytest_exit": 1,
        "failing_nodeids": ["tests/test_sample.py::test_failing"],
    }
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    loaded = json.loads(meta_path.read_text(encoding="utf-8"))
    assert loaded["pytest_exit"] == 1
    assert "tests/test_sample.py::test_failing" in loaded["failing_nodeids"]


def test_covctx_plugin_subprocess_context_propagation(tmp_path: Path) -> None:
    """Validate covctx_plugin propagates context into in-process and subprocess execution."""
    test_file = tmp_path / "test_contexts.py"
    test_file.write_text(
        "import sys, subprocess, agent_workflows.artifact_naming as an\n"
        "def test_one():\n"
        "    assert not an.is_clustered_conformant('invalid')\n"
        "def test_two():\n"
        "    res = subprocess.run([sys.executable, '-c', 'import agent_workflows.artifact_naming as an; an.is_clustered_conformant(\"invalid\")'], check=True)\n"
        "    assert res.returncode == 0\n",
        encoding="utf-8",
    )

    rc_file = tmp_path / ".coveragerc"
    data_file = tmp_path / ".coverage"

    rc_file.write_text(
        f"[run]\n"
        f"data_file = {data_file.as_posix()}\n"
        f"source = agent_workflows\n"
        f"branch = true\n"
        f"parallel = true\n"
        f"patch = subprocess\n",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env.pop("COVERAGE_PROCESS_START", None)
    env.pop("COVERAGE_FILE", None)
    env.pop("COVERAGE_PROCESS_CONFIG", None)
    env["COVERAGE_CORE"] = "ctrace"
    env["PYTHONPATH"] = f"{_REPO_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"

    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--rcfile={rc_file}",
        "-m",
        "pytest",
        str(test_file),
        "-o",
        "addopts=",
        "-q",
        "-p",
        "tests.tools.covctx_plugin",
        "-p",
        "no:cov",
    ]
    res = subprocess.run(
        cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, check=False
    )
    assert res.returncode == 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"

    clean_env = dict(env)
    clean_env.pop("COVERAGE_PROCESS_START", None)
    clean_env.pop("COVERAGE_FILE", None)
    clean_env.pop("COVERAGE_PROCESS_CONFIG", None)
    subprocess.run(
        [sys.executable, "-m", "coverage", "combine", f"--rcfile={rc_file}"],
        cwd=tmp_path,
        env=clean_env,
        check=True,
    )

    cov_data = coverage.CoverageData(str(data_file))
    cov_data.read()
    contexts = {c for c in cov_data.measured_contexts() if c}

    assert any("test_one" in c for c in contexts)
    assert any("test_two" in c for c in contexts)
