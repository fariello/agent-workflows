"""Live per-leaf conformance scenario sweep and fact parity gates (IPD 34iwyp).

Default-collected CLI conformance gates covering:
1. Color contrast gate: proving run_cli_tty observes ANSI escapes on color-emitting leaves (E-07).
2. --help scenario sweep: exit 0 and documents usage across all 16 safe leaves (E-02).
3. Usage error scenario sweep: exit 2 and documents usage across all 16 safe leaves (E-02).
4. NO_COLOR scenario sweep: plain ANSI-free output across cheap leaves (default-collected, E-02)
   and heavy leaves (slow, E-03).
5. Non-vacuous human-agent fact parity gate across curated banner-emitting leaves (E-05).
6. Synthetic outcome banner extractor unit tests across Unicode and ASCII glyph sets (E-05).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Tuple
import pytest

from agent_workflows import agent_schema, command_surface
from tests.conformance_matrix import (
    ANSI_RE,
    FACT_PARITY_LEAVES,
    LEDGER_FIXTURE_RUN_ID,
    LEDGER_SAFE_LEAVES,
    LIVE_HEAVY_LEAVES,
    LIVE_SAFE_LEAVES,
    USAGE_ERROR_FLAG,
    get_seeded_project_dir,
    live_cheap_leaves,
    live_leaf_argv,
    outcome_family,
    run_cli,
    run_cli_tty,
    seed_ledger_fixture,
    semantic_facts_from_agent,
    semantic_facts_from_human,
)


@pytest.fixture(scope="session")
def live_ledger_dir() -> Path:
    return get_seeded_project_dir()


# Cheap leaves measured to emit ANSI escape sequences over a pty when NO_COLOR is NOT set,
# and zero ANSI sequences when NO_COLOR is set.
# Re-measured at execution (IPD 34iwyp E-07):
# - backlog check: True / False
# - context: True / False
# - ipd lint: True / False
# - layout: True / False
# - list-repos: True / False
# - spec check: True / False
# - specs check: True / False
# (check-local-leaks, sanitize, research check-refs, research check-miscategorized,
#  workflow validate, and workflow check-generated emit no ANSI in either state).
COLOR_EMITTING_LEAVES: Tuple[str, ...] = (
    "backlog check",
    "context",
    "ipd lint",
    "layout",
    "list-repos",
    "spec check",
    "specs check",
)


# --------------------------------------------------------------------------------------------------
# Task group 2: Per-leaf scenario sweep
# --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("leaf", COLOR_EMITTING_LEAVES)
def test_no_color_transport_contrast_observes_ansi(
    leaf: str, live_ledger_dir: Path
) -> None:
    """Transport contrast: run_cli_tty without NO_COLOR observes ANSI escape sequences (E-07)."""
    argv = live_leaf_argv(leaf, live_ledger_dir)
    res = run_cli_tty(argv, no_color=False, cwd=live_ledger_dir)
    assert res.returncode in (
        0,
        1,
    ), f"{leaf} exited with unexpected returncode {res.returncode}"
    assert ANSI_RE.search(
        res.stdout
    ), f"Expected ANSI in output of {leaf!r} over pty without NO_COLOR, got: {res.stdout!r}"


@pytest.mark.parametrize("leaf", sorted(LIVE_SAFE_LEAVES.keys()))
def test_help_scenario_exits_zero_and_documents_usage(
    leaf: str, live_ledger_dir: Path
) -> None:
    """--help over LIVE_SAFE_LEAVES must exit 0 and document usage (E-02)."""
    res = run_cli([*leaf.split(), "--help"], cwd=live_ledger_dir)
    assert res.returncode == 0, f"{leaf} --help rc={res.returncode}"
    assert "usage" in res.stdout.lower(), f"{leaf} --help output did not document usage"


@pytest.mark.parametrize("leaf", sorted(LIVE_SAFE_LEAVES.keys()))
def test_usage_error_scenario_exits_two(leaf: str, live_ledger_dir: Path) -> None:
    """Invalid flag over LIVE_SAFE_LEAVES must exit 2 with usage error (E-02)."""
    res = run_cli([*leaf.split(), USAGE_ERROR_FLAG], cwd=live_ledger_dir)
    assert (
        res.returncode == 2
    ), f"{leaf} bad-flag rc={res.returncode} (expected usage error 2)"
    assert (
        "usage" in (res.stdout + res.stderr).lower()
    ), f"{leaf} bad-flag output missing 'usage'"


@pytest.mark.parametrize("leaf", live_cheap_leaves())
def test_no_color_scenario_is_plain_cheap_leaves(
    leaf: str, live_ledger_dir: Path
) -> None:
    """NO_COLOR over live_cheap_leaves() via pty must produce plain output without ANSI (E-02)."""
    argv = live_leaf_argv(leaf, live_ledger_dir)
    res = run_cli_tty(argv, no_color=True, cwd=live_ledger_dir)
    assert not ANSI_RE.search(
        res.stdout
    ), f"NO_COLOR human stream for {leaf!r} contained ANSI: {res.stdout!r}"


@pytest.mark.parametrize("leaf", sorted(LIVE_HEAVY_LEAVES))
def test_no_color_scenario_is_plain_heavy_leaves(
    leaf: str, live_ledger_dir: Path
) -> None:
    """NO_COLOR over LIVE_HEAVY_LEAVES via pty must produce plain output without ANSI (c8bfp9 E-02 / E-03)."""
    argv = live_leaf_argv(leaf, live_ledger_dir)
    res = run_cli_tty(argv, no_color=True, cwd=live_ledger_dir)
    assert not ANSI_RE.search(
        res.stdout
    ), f"NO_COLOR heavy stream for {leaf!r} contained ANSI: {res.stdout!r}"


# --------------------------------------------------------------------------------------------------
# Task group 3: Fact-parity gate (non-vacuous)
# --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("leaf", sorted(FACT_PARITY_LEAVES.keys()))
def test_fact_parity_non_vacuous(leaf: str, tmp_path: Path) -> None:
    """Human vs agent outcome families must match, and the human banner must not be empty (E-05)."""
    extra = FACT_PARITY_LEAVES[leaf]
    (tmp_path / ".aw" / "records").mkdir(parents=True, exist_ok=True)
    if leaf == "record-history":
        p_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
        p_dir.mkdir(parents=True, exist_ok=True)
        (p_dir / "20261012-test-01-f36de0-plan.ipd.md").write_text(
            "# IPD: Test\n\n- Id: f36de0\n- Status: to-review\n", encoding="utf-8"
        )
    env_overrides = {
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path),
        "AW_HOME": str(tmp_path),
    }

    res_human = run_cli(
        [*leaf.split(), *extra], cwd=tmp_path, env_overrides=env_overrides
    )
    res_agent = run_cli(
        [*leaf.split(), *extra, "--agent"], cwd=tmp_path, env_overrides=env_overrides
    )

    human_facts = semantic_facts_from_human(res_human.stdout)
    agent_facts = semantic_facts_from_agent(res_agent.stdout)

    human_family = human_facts.get("outcome_family")
    assert human_family is not None, (
        f"Non-vacuity assertion failed: {leaf!r} did not emit a recognized outcome banner.\n"
        f"Human stdout:\n{res_human.stdout}"
    )

    agent_family = outcome_family(agent_facts.get("outcome"))
    assert (
        human_family == agent_family
    ), f"{leaf!r} outcome family mismatch: human={human_family!r} != agent={agent_family!r}"
    assert (
        res_human.returncode == res_agent.returncode
    ), f"{leaf!r} exit code mismatch: human={res_human.returncode} != agent={res_agent.returncode}"


def test_semantic_facts_from_human_synthesized_shapes() -> None:
    """semantic_facts_from_human recognizes standard banners and rejects non-banners (E-05)."""
    # 1. Unicode glyph banners
    assert semantic_facts_from_human("✓ CONFORMS  schema: 10 views") == {
        "outcome_family": "clean"
    }
    assert semantic_facts_from_human("✓ CLEAN  no configured repos") == {
        "outcome_family": "clean"
    }
    assert semantic_facts_from_human("✗ FINDINGS  3 found") == {
        "outcome_family": "findings"
    }
    assert semantic_facts_from_human("! PREVIEW  dry run") == {
        "outcome_family": "preview"
    }
    assert semantic_facts_from_human("AW runs query\n✓ CONFORMS  schema: 10 views") == {
        "outcome_family": "clean"
    }

    # 2. ASCII glyph banners
    assert semantic_facts_from_human("OK CONFORMS  schema: 10 views") == {
        "outcome_family": "clean"
    }
    assert semantic_facts_from_human("FAIL FINDINGS  3 found") == {
        "outcome_family": "findings"
    }
    assert semantic_facts_from_human("! PREVIEW  dry run") == {
        "outcome_family": "preview"
    }
    assert semantic_facts_from_human(
        "AW runs query\nOK CONFORMS  schema: 10 views"
    ) == {"outcome_family": "clean"}

    # 3. Non-banner forms (must return None outcome_family)
    assert semantic_facts_from_human("Repositories\nname path") == {
        "outcome_family": None
    }
    assert semantic_facts_from_human("STALE    /path") == {"outcome_family": None}
    assert semantic_facts_from_human("-    ✓  executed     plan ...") == {
        "outcome_family": None
    }
    assert semantic_facts_from_human("") == {"outcome_family": None}
    assert semantic_facts_from_human("AW something\nNo banner here") == {
        "outcome_family": None
    }


# --------------------------------------------------------------------------------------------------
# Task group 4: Live ledger non-vacuous conformance gates (g5s94t E-09)
# --------------------------------------------------------------------------------------------------

EXPECTED_READ_EXIT_CODES = {
    "runs decisions": 1,
    "runs questions": 1,
    "runs evidence": 0,
    "runs next": 0,
    "runs resume": 0,
    "runs show": 1,
    "runs status": 1,
    "runs verify-ledger": 1,
}

PROJECTION_MARKERS = {
    "runs decisions": "_No autonomous decisions recorded._",
    "runs questions": "_No unresolved questions._",
}


@pytest.mark.parametrize("leaf", sorted(LEDGER_SAFE_LEAVES))
def test_live_ledger_read_leaves_non_vacuous(leaf: str, live_ledger_dir: Path) -> None:
    """Live non-vacuous conformance assertions over the 8 aw runs leaves (E-09a)."""
    expected_rc = EXPECTED_READ_EXIT_CODES[leaf]
    argv_base = live_leaf_argv(leaf, live_ledger_dir)

    res_human = run_cli(argv_base, cwd=live_ledger_dir)
    res_agent = run_cli([*argv_base, "--agent"], cwd=live_ledger_dir)
    res_json = run_cli([*argv_base, "--json"], cwd=live_ledger_dir)

    for mode, res in (("human", res_human), ("agent", res_agent), ("json", res_json)):
        assert res.returncode == expected_rc, (
            f"leaf={leaf!r} mode={mode} returned rc={res.returncode}, expected {expected_rc}\n"
            f"Stdout: {res.stdout}\nStderr: {res.stderr}"
        )
        assert res.returncode not in (
            2,
            5,
            7,
        ), f"leaf={leaf!r} mode={mode} returned vacuous failure code {res.returncode}"
        assert not ANSI_RE.search(
            res.stdout
        ), f"leaf={leaf!r} mode={mode} stdout contained ANSI escapes: {res.stdout!r}"

    agent_lines = [ln.strip() for ln in res_agent.stdout.splitlines() if ln.strip()]
    assert agent_lines, f"leaf={leaf!r} --agent emitted empty stdout"
    data_agent = json.loads(agent_lines[-1])
    assert isinstance(
        data_agent, dict
    ), f"leaf={leaf!r} --agent last line did not parse as JSON dict"
    assert (
        agent_schema.validate_agent_record(data_agent) == []
    ), f"leaf={leaf!r} invalid agent record: {agent_schema.validate_agent_record(data_agent)}"
    assert data_agent["exit"] == res_agent.returncode

    if leaf in PROJECTION_MARKERS:
        marker = PROJECTION_MARKERS[leaf]
        assert (
            marker in res_human.stdout
        ), f"Marker {marker!r} missing from human stdout"
        # Machine modes emit ONE JSON object carrying the projection text (hbok5d).
        assert (
            len(agent_lines) == 1
        ), f"leaf={leaf!r} --agent must emit one line: {res_agent.stdout!r}"
        for mode, parsed in (
            ("agent", data_agent),
            ("json", json.loads(res_json.stdout.strip())),
        ):
            assert parsed.get("empty") is True, f"leaf={leaf!r} --{mode}: {parsed!r}"
            assert marker in parsed.get(
                "content", ""
            ), f"Marker {marker!r} missing from {mode} content"
    else:
        # Six ledger readers: json stdout parses as one JSON object
        data_json = json.loads(res_json.stdout.strip())
        assert isinstance(
            data_json, dict
        ), f"leaf={leaf!r} --json did not parse as JSON dict"

        for parsed in (data_json, data_agent):
            if leaf in ("runs next", "runs resume", "runs show", "runs status"):
                assert (
                    parsed.get("run_id") == LEDGER_FIXTURE_RUN_ID
                ), f"leaf={leaf!r} run_id mismatch: {parsed.get('run_id')} != {LEDGER_FIXTURE_RUN_ID}"
            elif leaf == "runs evidence":
                assert (
                    "ledger" in parsed
                ), f"leaf={leaf!r} missing 'ledger' key in output: {parsed}"
            elif leaf == "runs verify-ledger":
                assert (
                    parsed.get("chain_clean") is True
                ), f"leaf={leaf!r} chain_clean is not True: {parsed}"


def test_live_ledger_mutation_leaves_conformance(tmp_path: Path) -> None:
    """Verify aw run mutation leaves live against fixture ledger (E-09b)."""
    modes = [
        ("human", []),
        ("agent", ["--agent"]),
        ("json", ["--json"]),
        ("tty_no_color", ["tty"]),
    ]

    steps = [
        (
            "run start",
            [
                "run",
                "start",
                LEDGER_FIXTURE_RUN_ID,
                "--step",
                "S-01",
                "--workflow",
                "wf.json",
            ],
            0,
        ),
        (
            "run record",
            [
                "run",
                "record",
                LEDGER_FIXTURE_RUN_ID,
                "--step",
                "S-01",
                "--state",
                "performed",
                "--workflow",
                "wf.json",
            ],
            0,
        ),
        (
            "run finalize",
            ["run", "finalize", LEDGER_FIXTURE_RUN_ID, "--workflow", "wf.json"],
            1,
        ),
        (
            "run cancel",
            ["run", "cancel", LEDGER_FIXTURE_RUN_ID, "--reason", "conformance"],
            0,
        ),
    ]

    for mode_name, flags in modes:
        fixture_dir = tmp_path / f"mut_{mode_name}"
        fixture_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init"], cwd=fixture_dir, check=True, capture_output=True
        )
        seed_ledger_fixture(fixture_dir)

        for cmd_leaf, base_args, expected_rc in steps:
            decl = command_surface.get_declaration(cmd_leaf)
            assert (
                decl is not None
            ), f"Declared leaf {cmd_leaf!r} missing from declaration index"
            full_args = [*base_args, "--dir", str(fixture_dir)]
            if mode_name == "tty_no_color":
                res = run_cli_tty(full_args, no_color=True, cwd=fixture_dir)
            else:
                res = run_cli([*full_args, *flags], cwd=fixture_dir)

            assert res.returncode == expected_rc, (
                f"{cmd_leaf} in {mode_name} got {res.returncode}, expected {expected_rc}\n"
                f"Stdout: {res.stdout}\nStderr: {res.stderr}"
            )
            assert (
                res.returncode in decl.exit_contract
            ), f"{cmd_leaf} rc={res.returncode} not in exit_contract {decl.exit_contract}"
            assert not ANSI_RE.search(
                res.stdout
            ), f"{cmd_leaf} in {mode_name} contained ANSI: {res.stdout!r}"

            if mode_name == "agent":
                lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
                assert lines, f"{cmd_leaf} --agent stdout empty"
                obj = json.loads(lines[-1])
                assert isinstance(
                    obj, dict
                ), f"{cmd_leaf} --agent did not parse as JSON dict"
                if cmd_leaf in ("run start", "run record", "run cancel"):
                    assert (
                        agent_schema.validate_agent_record(obj) == []
                    ), f"{cmd_leaf} invalid agent record: {agent_schema.validate_agent_record(obj)}"
                    assert obj["exit"] == res.returncode
                # run finalize exits 1 via incomplete-run refusal (bare payload; owned by u1ujw9 / p7bvku)
            elif mode_name == "json":
                obj = json.loads(res.stdout.strip())
                assert isinstance(
                    obj, dict
                ), f"{cmd_leaf} --json did not parse as JSON dict"

        # Verify final state on ledger is cancelled
        st_res = run_cli(
            [
                "runs",
                "status",
                LEDGER_FIXTURE_RUN_ID,
                "--workflow",
                "wf.json",
                "--dir",
                str(fixture_dir),
                "--json",
            ],
            cwd=fixture_dir,
        )
        st_obj = json.loads(st_res.stdout.strip())
        assert (
            st_obj.get("run_state") == "cancelled"
        ), f"Expected run_state == 'cancelled', got {st_obj.get('run_state')!r}"
