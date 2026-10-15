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

from pathlib import Path
from typing import Tuple
import pytest

from tests.conformance_matrix import (
    ANSI_RE,
    FACT_PARITY_LEAVES,
    LIVE_HEAVY_LEAVES,
    LIVE_SAFE_LEAVES,
    USAGE_ERROR_FLAG,
    live_cheap_leaves,
    outcome_family,
    run_cli,
    run_cli_tty,
    semantic_facts_from_agent,
    semantic_facts_from_human,
)

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
def test_no_color_transport_contrast_observes_ansi(leaf: str) -> None:
    """Transport contrast: run_cli_tty without NO_COLOR observes ANSI escape sequences (E-07)."""
    extra = LIVE_SAFE_LEAVES[leaf]
    res = run_cli_tty([*leaf.split(), *extra], no_color=False)
    assert res.returncode in (
        0,
        1,
    ), f"{leaf} exited with unexpected returncode {res.returncode}"
    assert ANSI_RE.search(
        res.stdout
    ), f"Expected ANSI in output of {leaf!r} over pty without NO_COLOR, got: {res.stdout!r}"


@pytest.mark.parametrize("leaf", sorted(LIVE_SAFE_LEAVES.keys()))
def test_help_scenario_exits_zero_and_documents_usage(leaf: str) -> None:
    """--help over LIVE_SAFE_LEAVES must exit 0 and document usage (E-02)."""
    res = run_cli([*leaf.split(), "--help"])
    assert res.returncode == 0, f"{leaf} --help rc={res.returncode}"
    assert "usage" in res.stdout.lower(), f"{leaf} --help output did not document usage"


@pytest.mark.parametrize("leaf", sorted(LIVE_SAFE_LEAVES.keys()))
def test_usage_error_scenario_exits_two(leaf: str) -> None:
    """Invalid flag over LIVE_SAFE_LEAVES must exit 2 with usage error (E-02)."""
    res = run_cli([*leaf.split(), USAGE_ERROR_FLAG])
    assert (
        res.returncode == 2
    ), f"{leaf} bad-flag rc={res.returncode} (expected usage error 2)"
    assert (
        "usage" in (res.stdout + res.stderr).lower()
    ), f"{leaf} bad-flag output missing 'usage'"


@pytest.mark.parametrize("leaf", live_cheap_leaves())
def test_no_color_scenario_is_plain_cheap_leaves(leaf: str) -> None:
    """NO_COLOR over live_cheap_leaves() via pty must produce plain output without ANSI (E-02)."""
    extra = LIVE_SAFE_LEAVES[leaf]
    res = run_cli_tty([*leaf.split(), *extra], no_color=True)
    assert not ANSI_RE.search(
        res.stdout
    ), f"NO_COLOR human stream for {leaf!r} contained ANSI: {res.stdout!r}"


@pytest.mark.slow
@pytest.mark.timeout(500)
@pytest.mark.parametrize("leaf", sorted(LIVE_HEAVY_LEAVES))
def test_no_color_scenario_is_plain_heavy_leaves(leaf: str) -> None:
    """NO_COLOR over LIVE_HEAVY_LEAVES via pty must produce plain output without ANSI (slow, E-03)."""
    extra = LIVE_SAFE_LEAVES[leaf]
    res = run_cli_tty([*leaf.split(), *extra], no_color=True)
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
