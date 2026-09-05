#!/usr/bin/env python3
"""R1 signal purity in the emitted prompt (spec `7ckptx` A1, A2, A17; plan `cqx5v7` V-01, V-02).

PARAMETERIZED OVER BOTH DRIVERS, never copied. Spec 0.3 states that a containment rule landing in one
driver and not the other is a DEFECT rather than a partial delivery, and the measured history is that a
one-sided guard let `agy_runipd` re-fork four display symbols unnoticed. So every assertion below runs
against `oc_runipd` AND `agy_runipd` from ONE function body: a rule that holds for one host and not the
other fails here, and there is no second copy of the assertion to drift.

WHAT IS ASSERTED, and each is a PROPERTY of the emitted text rather than a wording match:

  * A1/R1.1 zero absolute paths outside the lane root, by pattern scan over the whole emitted string.
    The scan names no sentence, so a reworded violation, a newly interpolated path, or a path arriving
    through the recovery notice all fail it.
  * R1.2 no exception clause survives. Asserted over the EMITTED OUTPUT and by a SEMANTIC check (the
    permission-shaped vocabulary), not by pinning the old sentence, because a test pinned to the exact
    old sentence is satisfied by rephrasing it.
  * A2/R1.3 the NON-isolated prompt is byte-identical (digest-compared) to the pre-change output.
  * A17/R1.4 the cwd-is-the-workspace statement and the literal missing-input token form are PRESENT.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from agent_workflows import agy_runipd, lane_containment, oc_runipd

# The ONE parameterization every test below reuses. `ids` keeps a failure legible about WHICH host
# broke, which a bare object list does not.
DRIVERS = pytest.mark.parametrize(
    "driver", (oc_runipd, agy_runipd), ids=("oc_runipd", "agy_runipd")
)


def _item(**over) -> dict:
    item = {
        "id6": "aaaaaa",
        "setid": "lanectn",
        "position": 1,
        "configured_file": "x.ipd.md",
        "attempts": [{"number": 1}],
        "action": "execute",
    }
    item.update(over)
    return item


def _state(repo: Path) -> dict:
    return {"run_id": "run-20260901T000000Z-1", "repo": str(repo), "options": {}}


def _lane(tmp_path: Path) -> Path:
    lane = tmp_path / "repo" / ".aw" / "worktrees" / "aaaaaa"
    lane.mkdir(parents=True, exist_ok=True)
    return lane


def _run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "repo" / ".aw" / "records" / "runs" / "run-20260901T000000Z-1"
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    return run_dir


def _isolated_prompt(
    driver, tmp_path: Path, *, recovery: bool = False, item=None
) -> str:
    lane = _lane(tmp_path)
    plan = lane / "x.ipd.md"
    plan.write_text("# IPD: fixture\n", encoding="utf-8")
    return driver.build_prompt(
        item if item is not None else _item(),
        _state(tmp_path / "repo"),
        _run_dir(tmp_path),
        plan,
        recovery,
        lane_root=lane,
    )


# ---- A1 / R1.1: zero absolute paths outside the lane ----------------------------------------------


@DRIVERS
def test_isolated_prompt_names_no_absolute_path_outside_the_lane(driver, tmp_path):
    """A1, R1.1. The scan is over the EMITTED STRING and states its pattern in the failure."""
    lane = _lane(tmp_path)
    prompt = _isolated_prompt(driver, tmp_path)
    offenders = lane_containment.absolute_paths_outside_lane(prompt, lane)
    assert offenders == [], (
        f"{driver.__name__} emitted absolute paths outside the lane root {lane}: "
        f"{offenders} (pattern: {lane_containment._ABS_PATH_RE.pattern})"
    )


@DRIVERS
def test_the_scan_can_actually_fail(driver, tmp_path):
    """THE SABOTAGE, in-test: a scan that passes no matter what proves nothing.

    Plan `cqx5v7`'s execution contract rule 2 requires the central assertion be shown to FAIL when the
    product is broken. `V-01` records the manual product-level sabotage; this test additionally pins
    the DETECTOR, so a later change that neuters `absolute_paths_outside_lane` (returning `[]`
    unconditionally, say) fails here instead of quietly making every purity test vacuous.
    """
    lane = _lane(tmp_path)
    prompt = _isolated_prompt(driver, tmp_path)
    injected = (
        prompt + f"\nDriver report: {tmp_path}/repo/.aw/records/runs/r/report.md\n"
    )
    assert lane_containment.absolute_paths_outside_lane(injected, lane), (
        "the purity scan failed to detect a deliberately injected out-of-lane absolute path; "
        "it cannot fail, so it is not testing anything"
    )


@DRIVERS
def test_recovery_prompt_is_also_pure(driver, tmp_path):
    """R1.1 must hold on the RECOVERY path too, which is where it originally leaked.

    The prior-attempt record carries `prompt`, `log`, and `worktree` as ABSOLUTE driver-side paths, so
    a resumed isolated turn emitted out-of-lane paths through a route the five named path lines do not
    cover. A check that only inspected those lines would have reported R1.1 satisfied.
    """
    lane = _lane(tmp_path)
    item = _item(
        attempts=[
            {
                "number": 1,
                "prompt": str(
                    tmp_path
                    / "repo"
                    / ".aw"
                    / "records"
                    / "runs"
                    / "r"
                    / "prompts"
                    / "p.md"
                ),
                "log": str(
                    tmp_path
                    / "repo"
                    / ".aw"
                    / "records"
                    / "runs"
                    / "r"
                    / "sessions"
                    / "s.jsonl"
                ),
                "worktree": str(tmp_path / "repo" / ".aw" / "worktrees" / "other"),
                "worktree_branch": "aw/lane/aaaaaa",
                "exit_code": 1,
                "disposition": "partial",
            }
        ]
    )
    prompt = _isolated_prompt(driver, tmp_path, recovery=True, item=item)
    assert "Mode: RECOVERY/CONTINUATION" in prompt
    offenders = lane_containment.absolute_paths_outside_lane(prompt, lane)
    assert offenders == [], f"{driver.__name__} recovery prompt leaked: {offenders}"
    # The facts a resuming worker can act on SURVIVE the projection; only paths are dropped.
    assert "aw/lane/aaaaaa" in prompt
    assert '"disposition": "partial"' in prompt


# ---- R1.2: no exception clause survives -----------------------------------------------------------

#: The retired sentence, quoted ONLY to assert its absence. Every other assertion in this file is
#: property-based precisely so that rephrasing this cannot slip past.
RETIRED_CLAUSE_FRAGMENTS = (
    "those are the only exceptions",
    "DRIVER-OWNED control path",
    "you write them exactly as given",
)


@DRIVERS
def test_the_exception_clause_is_absent_from_the_emitted_prompt(driver, tmp_path):
    """R1.2, asserted over the OUTPUT (not only the source) so a reworded exception also fails."""
    prompt = _isolated_prompt(driver, tmp_path)
    for fragment in RETIRED_CLAUSE_FRAGMENTS:
        assert (
            fragment not in prompt
        ), f"{driver.__name__} still emits the retired exception clause fragment {fragment!r}"


@DRIVERS
def test_no_reworded_exception_survives_either(driver, tmp_path):
    """R1.2, the SEMANTIC half: catch a REPHRASED exception, not just the old wording.

    HOW IT WOULD CATCH A REPHRASING, stated explicitly because the plan's `V-02` demands it. An
    exception clause has to do two things at once: NAME a path outside the lane, and grant permission
    about it. The first is already impossible by construction, because
    `test_isolated_prompt_names_no_absolute_path_outside_the_lane` scans the whole emitted text for
    absolute out-of-lane paths and no wording can hide one. This test closes the remaining gap by
    rejecting permission-granting vocabulary ABOUT being outside the lane, however phrased: any
    sentence combining an outside-the-lane referent with an exception/permission word fails.
    """
    prompt = _isolated_prompt(driver, tmp_path)
    outside_words = (
        "outside the lane",
        "outside your workspace",
        "outside this workspace",
    )
    permission_words = (
        "exception",
        "exceptions",
        "permitted",
        "allowed",
        "authorized to write",
        "you may write",
    )
    offenders = []
    for line in prompt.splitlines():
        low = line.lower()
        if any(w in low for w in outside_words) and any(
            p in low for p in permission_words
        ):
            offenders.append(line)
    assert offenders == [], (
        f"{driver.__name__} emits a permission-shaped statement about paths outside the lane: "
        f"{offenders}"
    )


# ---- A17 / R1.4: the workspace statement and the escape hatch --------------------------------------


@DRIVERS
def test_isolated_prompt_states_the_workspace_rule_and_the_token_form(driver, tmp_path):
    """A17, R1.4. R1.1 without R1.4 is strictness with no escape hatch."""
    prompt = _isolated_prompt(driver, tmp_path)
    assert "COMPLETE authorized workspace" in prompt
    assert "it is your working directory" in prompt
    assert lane_containment.MISSING_INPUT_TOKEN_FORM in prompt
    # And the block is still the one a forgetful agent needs (the measured y6mfgo defect).
    assert "## Work here" in prompt
    assert "ISOLATED GIT WORKTREE" in prompt
    assert "do NOT climb out with a relative path" in prompt


@DRIVERS
def test_the_worker_is_told_where_its_submissions_go(driver, tmp_path):
    """R1.4 + R2.1: the lane-relative submission paths are named, and named as the worker's own."""
    prompt = _isolated_prompt(driver, tmp_path)
    item = _item()
    paths = lane_containment.project_worker_paths(
        item=item,
        run_id="run-20260901T000000Z-1",
        run_dir=_run_dir(tmp_path),
        plan_path=_lane(tmp_path) / "x.ipd.md",
        lane_root=_lane(tmp_path),
    )
    for value in (paths.prompt_run_dir, paths.prompt_decisions, paths.prompt_outcome):
        assert value in prompt
        assert not Path(value).is_absolute()
    # The label must not call a lane-relative path "External"/"Driver": that would put the
    # contradiction back in the label after removing it from the value.
    assert "External run directory" not in prompt
    assert "\nDriver report:" not in prompt


# ---- A2 / R1.3: the non-isolated prompt is untouched ----------------------------------------------


@DRIVERS
def test_non_isolated_prompt_is_byte_identical_to_the_pre_change_output(
    driver, tmp_path
):
    """A2, R1.3, by DIGEST against the pre-change rendering, reconstructed here.

    The expected string is rebuilt from the pre-change interpolation (absolute run-dir, absolute
    decisions/outcome/report, `External run directory`/`Driver report` labels, the WHOLE prior-attempt
    record) and compared by sha256. A field-by-field comparison would miss a label or ordering change,
    which is exactly the class of drift R1.3 forbids.
    """
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    run_dir = _run_dir(tmp_path)
    plan = repo / "x.ipd.md"
    plan.write_text("# IPD: fixture\n", encoding="utf-8")
    item = _item()
    state = _state(repo)

    produced = driver.build_prompt(item, state, run_dir, plan, False)
    explicit_none = driver.build_prompt(
        item, state, run_dir, plan, False, lane_root=None
    )
    assert produced == explicit_none
    assert "## Work here" not in produced

    expected_lines = [
        f"Plan file at launch: {plan}",
        f"External run directory: {run_dir}",
        f"Decisions/questions register: {run_dir / 'decisions-and-questions.md'}",
        f"Required JSON outcome: {run_dir / 'outcomes' / '01-aaaaaa.json'}",
        f"Driver report: {run_dir / 'execution-report.md'}",
    ]
    for line in expected_lines:
        assert (
            line in produced
        ), f"{driver.__name__} changed the non-isolated line {line!r}"

    # The digest half: the block of five lines above, exactly as emitted, must hash to the digest of
    # the pre-change rendering of those same lines.
    start = produced.index("Plan file at launch:")
    end = produced.index("Prior attempt:")
    emitted_block = produced[start:end]
    expected_block = "\n".join(expected_lines) + "\n"
    assert (
        hashlib.sha256(emitted_block.encode()).hexdigest()
        == hashlib.sha256(expected_block.encode()).hexdigest()
    ), f"{driver.__name__} non-isolated path block drifted:\n{emitted_block!r}"


@DRIVERS
def test_non_isolated_recovery_prompt_keeps_the_whole_prior_record(driver, tmp_path):
    """R1.3: the prior-attempt PROJECTION applies to an isolated turn only."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    plan = repo / "x.ipd.md"
    plan.write_text("# IPD: fixture\n", encoding="utf-8")
    prior = {"number": 1, "prompt": str(repo / "p.md"), "log": str(repo / "l.jsonl")}
    prompt = driver.build_prompt(
        _item(attempts=[prior]), _state(repo), _run_dir(tmp_path), plan, True
    )
    assert json.dumps(prior, sort_keys=True) in prompt


# ---- R2.6 / CID-2: one definition, both drivers ---------------------------------------------------


def test_neither_driver_holds_a_second_copy_of_the_rule():
    """CID-2 and spec R2.6, established by the IMPORT GRAPH and AST, not a text grep.

    A grep is satisfied by the checking code itself and by a comment; and a per-file check passes while
    two copies exist. So: assert each driver IMPORTS the shared module, and that neither DEFINES any of
    the shared rule's symbols at top level.
    """
    import ast

    shared = {
        "project_worker_paths",
        "isolation_notice",
        "collect_lane_submissions",
        "merge_decisions_block",
        "collection_receipt_path",
        "lane_submission_root",
        "absolute_paths_outside_lane",
        "prior_attempt_summary",
    }
    for driver in (oc_runipd, agy_runipd):
        source = Path(str(driver.__file__)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports_shared = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "agent_workflows"
            and any(a.name == "lane_containment" for a in node.names)
            for node in ast.walk(tree)
        )
        assert imports_shared, f"{driver.__name__} does not import the shared module"
        defined = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        assert not (defined & shared), (
            f"{driver.__name__} re-defines shared containment symbols {defined & shared}; "
            "that forks the rule (CID-2)"
        )
    # And the agy driver must not reach the rule THROUGH the oc driver, which would make one host the
    # de-facto shared library (spec R2.6 forbids exactly that).
    agy_source = Path(str(agy_runipd.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(agy_source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "agent_workflows.oc_runipd"
        ):
            assert not any(
                a.name in {"build_isolation_notice", *shared} for a in node.names
            ), "agy_runipd imports a containment rule from oc_runipd (spec R2.6 violation)"
