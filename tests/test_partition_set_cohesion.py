"""Behavioral tests for Set cohesion, incomplete Set refusal, and --allow-partial-sets in `aw partition`."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agent_workflows import agent_schema, cli
from tests.record_builder import RecordBuilder


def make_fixture_plan(
    repo: Path,
    dir_kind: str,
    date: str,
    kind: str,
    status: str,
    setid: str,
    setname: str,
    order: int,
    id6: str,
    title: str,
    child_orders: tuple[tuple[str, str, str], ...] = (),
    item_dependencies: str = "none",
) -> Path:
    when = (
        f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        if len(date) == 8 and date.isdigit()
        else date
    )
    body_lines: list[str] = []
    if child_orders:
        body_lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Summary |",
                "|---|---|---|",
            ]
        )
        for ord_tok, cid, csum in child_orders:
            body_lines.append(f"| {ord_tok} | {cid} | {csum} |")
    body = "\n".join(body_lines) if body_lines else ""
    dest = RecordBuilder(repo).plan(
        id6=id6,
        plan_role=kind,
        title=title,
        when=when,
        set=setid,
        order=order,
        status=status,
        item_dependencies=item_dependencies,
        disposition=dir_kind,
        slug=title.lower().replace(" ", "-"),
        body=body,
    )
    assert isinstance(dest, Path)
    return dest


@pytest.fixture
def cohesion_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    # Set A: Orchestrator + 3 approved children
    table_a = (
        ("01", "achl01", "Child 1"),
        ("02", "achl02", "Child 2"),
        ("03", "achl03", "Child 3"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "seta",
        "Set A",
        0,
        "aorch0",
        "Set A Orchestrator",
        child_orders=table_a,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "seta",
        "Set A",
        1,
        "achl01",
        "Set A Child 1",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "seta",
        "Set A",
        2,
        "achl02",
        "Set A Child 2",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "seta",
        "Set A",
        3,
        "achl03",
        "Set A Child 3",
    )

    # Set B: Orchestrator + 1 executed child + 1 approved child + 1 to-review child
    table_b = (
        ("01", "bchl01", "Child 1"),
        ("02", "bchl02", "Child 2"),
        ("03", "bchl03", "Child 3"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setb",
        "Set B",
        0,
        "borch0",
        "Set B Orchestrator",
        child_orders=table_b,
    )
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "child",
        "executed",
        "setb",
        "Set B",
        1,
        "bchl01",
        "Set B Child 1",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setb",
        "Set B",
        2,
        "bchl02",
        "Set B Child 2",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "to-review",
        "setb",
        "Set B",
        3,
        "bchl03",
        "Set B Child 3",
    )

    return repo


def test_cohesion_orchestrator_and_children_share_shard(
    cohesion_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(a) cohesion: Set orchestrator and children share a shard for -n 1..4."""
    for n in (1, 2, 3, 4):
        code = cli.main(
            [
                "partition",
                "-t",
                "plans",
                "seta",
                "-n",
                str(n),
                "--run",
                "none",
                "--json",
                "--dir",
                str(cohesion_repo),
            ]
        )
        assert code == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        set_a_ids = {"aorch0", "achl01", "achl02", "achl03"}
        shards_with_set_a = [s for s in payload["shards"] if set_a_ids.intersection(s)]
        assert (
            len(shards_with_set_a) == 1
        ), f"Set A members split across shards at -n {n}: {payload['shards']}"
        shard = shards_with_set_a[0]
        assert set_a_ids.issubset(set(shard))
        # Orchestrator must sort last among Set A's members within the shard
        assert shard[-1] == "aorch0"


def test_default_refusal_incomplete_set(
    cohesion_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(b) default refusal: exit 2, no stdout, stderr names each blocked child, its status and its fix, and NO other Set's commands are emitted."""
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--run",
            "none",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        "error: Set 'setb' cannot finish in this batch, so nothing was scheduled."
        in captured.err
    )
    assert "bchl03" in captured.err
    assert "to-review" in captured.err
    assert (
        "/plan-review bchl03, then aw ipd set approved bchl03 --by-human"
        in captured.err
    )
    assert "achl01" not in captured.out


def test_allow_partial_sets(
    cohesion_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(c) --allow-partial-sets: ready children emitted, orchestrator absent, warning present, exit 0."""
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--allow-partial-sets",
            "--run",
            "none",
            "--json",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "warning: Set 'setb'" in captured.err
    assert "held back orchestrator borch0" in captured.err

    payload = json.loads(captured.out)
    emitted_ids = [item for shard in payload["shards"] for item in shard]
    # Set A is whole
    assert {"aorch0", "achl01", "achl02", "achl03"}.issubset(set(emitted_ids))
    # Set B's ready child is emitted
    assert "bchl02" in emitted_ids
    # Set B's orchestrator is absent
    assert "borch0" not in emitted_ids
    # held_back_orchestrators is present
    assert "held_back_orchestrators" in payload
    assert payload["held_back_orchestrators"][0]["setid"] == "setb"
    assert payload["held_back_orchestrators"][0]["orchestrator"] == "borch0"


def test_allow_partial_sets_selector_setid(
    cohesion_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--allow-partial-sets with setid selector: only ready children emitted, blocked children and orchestrator absent."""
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setb",
            "--allow-partial-sets",
            "--run",
            "none",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "warning: Set 'setb'" in captured.err
    assert "held back orchestrator borch0" in captured.err
    assert "bchl02" in captured.out
    assert "bchl03" not in captured.out
    assert "borch0" not in captured.out


def test_all_children_finished_except_orchestrator(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(d) a Set whose children are all FINISHED except the orchestrator: the orchestrator alone is emitted."""
    repo = tmp_path / "repo_d"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    table_c = (
        ("01", "cchl01", "Child 1"),
        ("02", "cchl02", "Child 2"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setc",
        "Set C",
        0,
        "corch0",
        "Set C Orchestrator",
        child_orders=table_c,
    )
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "child",
        "executed",
        "setc",
        "Set C",
        1,
        "cchl01",
        "Set C Child 1",
    )
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "child",
        "executed",
        "setc",
        "Set C",
        2,
        "cchl02",
        "Set C Child 2",
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "2",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    emitted_ids = [item for shard in payload["shards"] for item in shard]
    assert emitted_ids == ["corch0"]


def test_filtered_out_child_and_setid_selection(
    cohesion_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(e) filtered-out child: selecting only some children of a Set by id6 refuses, naming missing child; setid selection passes."""
    # 1. Selecting only some children by id6 refuses
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "aorch0",
            "achl01",
            "achl02",
            "--run",
            "none",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert "error: Set 'seta' cannot finish in this batch" in captured.err
    assert (
        "add achl03 to the selection, or select the Set by its setid seta"
        in captured.err
    )

    # 2. Selecting Set B with full runnable members on disk
    # Make bchl03 approved so Set B can finish
    make_fixture_plan(
        cohesion_repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setb",
        "Set B",
        3,
        "bchl03",
        "Set B Child 3",
    )

    code_setid = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setb",
            "--run",
            "none",
            "--json",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code_setid == 0
    captured_setid = capsys.readouterr()
    payload = json.loads(captured_setid.out)
    emitted = [item for shard in payload["shards"] for item in shard]
    # Executed child bchl01 is skipped, runnable children + orch are emitted
    assert set(emitted) == {"borch0", "bchl02", "bchl03"}

    # 3. Explicitly selecting an executed item by id6 still raises ineligible
    code_ineligible = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "bchl01",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code_ineligible == 2
    assert "is ineligible for runner dispatch" in capsys.readouterr().err


def test_max_truncation_refusal(
    cohesion_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(f) --max truncation that would split a Set refuses with 'raise --max to N' fix and correct N."""
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "seta",
            "--max",
            "2",
            "--run",
            "none",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert "raise --max to 4 or select the Set by its setid" in captured.err


def test_color_and_no_color(
    cohesion_repo: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """(g) color: with --color refusal contains ANSI escapes, with --no-color and NO_COLOR=1 it contains none."""
    # With --color
    cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "--color",
            "--dir",
            str(cohesion_repo),
        ]
    )
    err_color = capsys.readouterr().err
    assert "\033[" in err_color

    # With --no-color
    cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "--no-color",
            "--dir",
            str(cohesion_repo),
        ]
    )
    err_nocolor = capsys.readouterr().err
    assert "\033[" not in err_nocolor

    # With NO_COLOR=1
    monkeypatch.setenv("NO_COLOR", "1")
    cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "--dir",
            str(cohesion_repo),
        ]
    )
    err_env = capsys.readouterr().err
    assert "\033[" not in err_env


def test_selection_with_no_orchestrators(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(h) a selection with no orchestrators at all, and a Set with no orchestrator, partitions byte-identically to today."""
    repo = tmp_path / "repo_h"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "noorch",
        "No Orch",
        1,
        "pln001",
        "Plan 1",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "noorch",
        "No Orch",
        2,
        "pln002",
        "Plan 2",
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "2",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert len(payload["shards"]) == 2
    assert "held_back_orchestrators" not in payload


def test_backlog_and_specs_unaffected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(i) backlog and specs types are unaffected."""
    repo = tmp_path / "repo_i"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    bkl_dir = repo / ".aw" / "records" / "backlog" / "open"
    bkl_dir.mkdir(parents=True, exist_ok=True)
    (bkl_dir / "20261010-bkl001-01-bkl001-item.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl001", status="open", work_kind="bug", text_only=True
        )
    )

    code_bkl = cli.main(
        [
            "partition",
            "-t",
            "backlog",
            "-s",
            "open",
            "-n",
            "1",
            "--run",
            "none",
            "--dir",
            str(repo),
        ]
    )
    assert code_bkl == 0
    assert "bkl001" in capsys.readouterr().out


def test_unauthored_child_row_refusal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(j) an orchestrator whose child table declares an unauthored row is refused with the orchestrator-cannot-retire cause."""
    repo = tmp_path / "repo_j"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    # Orchestrator declares rows 01, 02, 03, but child 03 is missing on disk
    table = (
        ("01", "jchl01", "Child 1"),
        ("02", "jchl02", "Child 2"),
        ("03", "jchl03", "Child 3"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setj",
        "Set J",
        0,
        "jorch0",
        "Set J Orchestrator",
        child_orders=table,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setj",
        "Set J",
        1,
        "jchl01",
        "Set J Child 1",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setj",
        "Set J",
        2,
        "jchl02",
        "Set J Child 2",
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "2",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "blocked_sets" in payload
    blocked_members = payload["blocked_sets"][0]["blocked"]
    assert any(b["cause"] == "orchestrator-cannot-retire" for b in blocked_members)
    assert "author the missing child for row 03" in captured.err


def test_agent_refusal_record(
    cohesion_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(k) --agent refusal record passes agent_schema.validate_agent_record with exit: 2, outcome: cannot-run."""
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--agent",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert agent_schema.validate_agent_record(record) == []
    assert record["schema"] == "aw.agent/v1"
    assert record["kind"] == "result"
    assert record["cmd"] == "partition"
    assert record["exit"] == 2
    assert record["outcome"] == "cannot-run"
    assert record["verified"] is True
    assert record["complete"] is True
    assert "blocked_sets" in record


def test_oversized_set_kept_whole(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(l) an oversized Set (more plans than the even share) stays whole in one shard and the note: line is printed."""
    repo = tmp_path / "repo_l"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    table = (
        ("01", "lchl01", "Child 1"),
        ("02", "lchl02", "Child 2"),
        ("03", "lchl03", "Child 3"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setl",
        "Set L",
        0,
        "lorch0",
        "Set L Orchestrator",
        child_orders=table,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setl",
        "Set L",
        1,
        "lchl01",
        "Set L Child 1",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setl",
        "Set L",
        2,
        "lchl02",
        "Set L Child 2",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setl",
        "Set L",
        3,
        "lchl03",
        "Set L Child 3",
    )
    # Independent plan
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "other",
        "Other",
        1,
        "oth001",
        "Other Plan 1",
    )

    # 5 plans across 3 shards -> cap = ceil(5/3) = 2. Set L has 4 plans > 2.
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["split_components"] == []
    set_l_ids = {"lorch0", "lchl01", "lchl02", "lchl03"}
    shards_with_l = [s for s in payload["shards"] if set_l_ids.intersection(s)]
    assert len(shards_with_l) == 1
    assert set_l_ids.issubset(set(shards_with_l[0]))
    assert "note: Set 'setl' (4 plans) kept whole in shard" in captured.err
    assert "exceeding the even share of 2" in captured.err


def test_partition_set_with_active_child_blocks_batch(
    cohesion_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Set A has aorch0, achl01, achl02, achl03.
    # achl01 is currently running in a live runner
    monkeypatch.setattr(
        "agent_workflows.attention.get_active_runs_map",
        lambda repo: {"achl01": "running"},
    )

    # By default, without --include-active, the batch is refused (exit 2)
    # because Set A cannot finish in this batch while achl01 is already running.
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "seta",
            "-s",
            "approved",
            "--dir",
            str(cohesion_repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert (
        "Set 'seta' cannot finish in this batch, so nothing was scheduled."
        in captured.err
    )
    assert "achl01 (approved, already running)" in captured.err
    assert "wait for active run to finish achl01" in captured.err

    # With --allow-partial-sets, ready children achl02, achl03 are scheduled,
    # holding back the orchestrator and warning about achl01.
    code_part = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "seta",
            "-s",
            "approved",
            "--allow-partial-sets",
            "--dir",
            str(cohesion_repo),
            "--run",
            "none",
        ]
    )
    assert code_part == 0
    captured_part = capsys.readouterr()
    assert "held back orchestrator aorch0" in captured_part.err
    assert "achl01 (approved, already running)" in captured_part.err
    assert "achl02" in captured_part.out
    assert "achl03" in captured_part.out
    assert "achl01" not in captured_part.out
    assert "aorch0" not in captured_part.out

    # With --include-active, achl01 is included and the full Set (including orchestrator) runs.
    code_inc = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "seta",
            "-s",
            "approved",
            "--include-active",
            "--dir",
            str(cohesion_repo),
            "--run",
            "none",
        ]
    )
    assert code_inc == 0
    captured_inc = capsys.readouterr()
    assert "achl01" in captured_inc.out
    assert "achl02" in captured_inc.out
    assert "achl03" in captured_inc.out
    assert "aorch0" in captured_inc.out


def test_partition_unsatisfied_cross_set_dependency_refusal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When a plan has an unsatisfied cross-set dependency, partition refuses by default (exit 2)."""
    repo = tmp_path / "repo_dep_refusal"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    # Set Prereq: Orchestrator + 1 child, status approved (in pending)
    table_p = (("01", "pchl01", "Prereq Child"),)
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setp",
        "Set P",
        0,
        "porch0",
        "Set P Orchestrator",
        child_orders=table_p,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setp",
        "Set P",
        1,
        "pchl01",
        "Set P Child",
    )

    # Set Consumer: Orchestrator + 2 children. Child 1 has no deps, Child 2 depends on pchl01
    table_c = (
        ("01", "cuch01", "Consumer Child 1"),
        ("02", "cuch02", "Consumer Child 2"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setc",
        "Set C",
        0,
        "corch0",
        "Set C Orchestrator",
        child_orders=table_c,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setc",
        "Set C",
        1,
        "cuch01",
        "Consumer Child 1",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setc",
        "Set C",
        2,
        "cuch02",
        "Consumer Child 2",
        item_dependencies="executed:pchl01",
    )

    # Only Set C is selected. pchl01 is approved on disk but not executed, and not in selection.
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setc",
            "--run",
            "none",
            "--dir",
            str(repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        "error: Set 'setc' cannot finish in this batch, so nothing was scheduled."
        in captured.err
    )
    assert "cuch02 (approved, unsatisfied dependency)" in captured.err
    assert (
        "run with --with-dependencies, or execute prerequisite pchl01 first"
        in captured.err
    )

    # With --allow-partial-sets: ready child cuch01 runs, cuch02 is dropped, orchestrator corch0 is held back
    code_partial = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setc",
            "--allow-partial-sets",
            "--run",
            "none",
            "--dir",
            str(repo),
        ]
    )
    assert code_partial == 0
    captured_part = capsys.readouterr()
    assert (
        "warning: Set 'setc' cannot finish in this batch; held back orchestrator corch0."
        in captured_part.err
    )
    assert "cuch02 (approved, unsatisfied dependency)" in captured_part.err
    assert "cuch01" in captured_part.out
    assert "cuch02" not in captured_part.out
    assert "corch0" not in captured_part.out

    # With --with-dependencies: Set P is pulled in, both sets complete and are partitioned
    code_with_deps = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setc",
            "--with-dependencies",
            "--run",
            "none",
            "--dir",
            str(repo),
        ]
    )
    assert code_with_deps == 0
    captured_deps = capsys.readouterr()
    assert "cuch01" in captured_deps.out
    assert "cuch02" in captured_deps.out
    assert "pchl01" in captured_deps.out
    assert "corch0" in captured_deps.out
    assert "porch0" in captured_deps.out


def test_partition_prerequisite_already_executed_on_disk(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When a plan's prerequisite is already executed on disk, the edge is satisfied and partition succeeds."""
    repo = tmp_path / "repo_prereq_exec"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    # Prereq child is executed on disk
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "child",
        "executed",
        "setp",
        "Set P",
        1,
        "pchl01",
        "Prereq Child Executed",
    )

    # Set C has child depending on pchl01
    table_c = (("01", "cuch01", "Consumer Child 1"),)
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setc",
        "Set C",
        0,
        "corch0",
        "Set C Orchestrator",
        child_orders=table_c,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setc",
        "Set C",
        1,
        "cuch01",
        "Consumer Child 1",
        item_dependencies="executed:pchl01",
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setc",
            "--run",
            "none",
            "--dir",
            str(repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "cuch01" in captured.out
    assert "corch0" in captured.out


def test_partition_set_with_executed_orchestrator_and_unsatisfied_child(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A Set whose orchestrator is already executed still refuses when a child has an unsatisfied dependency."""
    repo = tmp_path / "repo_exec_orch"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    # Orchestrator is in executed/
    table = (
        ("01", "xchl01", "Child 1"),
        ("02", "xchl02", "Child 2"),
    )
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "orchestrator",
        "executed",
        "setx",
        "Set X",
        0,
        "xorch0",
        "Set X Orchestrator",
        child_orders=table,
    )
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "child",
        "executed",
        "setx",
        "Set X",
        1,
        "xchl01",
        "Child 1 Executed",
    )
    # Child 2 is pending and requires missing prerequisite
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setx",
        "Set X",
        2,
        "xchl02",
        "Child 2 Pending",
        item_dependencies="executed:mis001",
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setx",
            "--run",
            "none",
            "--dir",
            str(repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert (
        "error: Set 'setx' cannot finish in this batch, so nothing was scheduled."
        in captured.err
    )
    assert "xchl02 (approved, unsatisfied dependency)" in captured.err

    # With --allow-partial-sets, warning notes orchestrator is already executed, child is dropped
    code_part = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setx",
            "--allow-partial-sets",
            "--run",
            "none",
            "--dir",
            str(repo),
        ]
    )
    assert code_part == 0
    captured_part = capsys.readouterr()
    assert (
        "warning: Set 'setx' cannot finish in this batch; orchestrator xorch0 is already executed."
        in captured_part.err
    )
    assert "xchl02 (approved, unsatisfied dependency)" in captured_part.err


def test_partition_executed_orchestrator_mixed_sibling_statuses_does_not_refuse(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A Set whose orchestrator already retired is not refused because siblings need a different action.

    Regression: `aw partition -t plans -s to-review` refused the whole batch naming the approved
    siblings of an executed orchestrator as "needs execute", although no retirement remained to protect.
    """
    repo = tmp_path / "repo_retired_orch"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    table = (
        ("01", "rchl01", "Child 1"),
        ("02", "rchl02", "Child 2"),
        ("03", "rchl03", "Child 3"),
        ("04", "rchl04", "Child 4"),
    )
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "orchestrator",
        "executed",
        "setr",
        "Set R",
        0,
        "rorch0",
        "Set R Orchestrator",
        child_orders=table,
    )
    make_fixture_plan(
        repo,
        "executed",
        "20261010",
        "child",
        "executed",
        "setr",
        "Set R",
        1,
        "rchl01",
        "Child 1 Executed",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setr",
        "Set R",
        2,
        "rchl02",
        "Child 2 Approved",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "to-review",
        "setr",
        "Set R",
        4,
        "rchl04",
        "Child 4 To Review",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "to-review",
        "setr",
        "Set R",
        3,
        "rchl03",
        "Child 3 To Review",
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "-n",
            "2",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert "cannot finish in this batch" not in captured.err
    payload = json.loads(captured.out)
    scheduled = json.dumps(payload)
    assert "rchl03" in scheduled
    assert "rchl02" not in scheduled
    assert "rorch0" not in scheduled
    # No retirement to protect, so the remaining members balance instead of being kept whole.
    assert "kept whole" not in captured.err
    shards = [json.dumps(s) for s in payload["shards"]]
    assert len(shards) == 2
    assert all(("rchl03" in s) != ("rchl04" in s) for s in shards)


def test_partition_split_sets_and_single_shard_hint_for_plans(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Large Set alone in 1 shard suggests --split-sets; --split-sets splits children across shards,
    preserves explicit Item-Dependencies, and holds back the orchestrator for post-shard retirement."""
    repo = tmp_path / "repo_split_sets"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    table = (
        ("01", "schl01", "Child 1"),
        ("02", "schl02", "Child 2"),
        ("03", "schl03", "Child 3"),
        ("04", "schl04", "Child 4"),
        ("05", "schl05", "Child 5"),
        ("06", "schl06", "Child 6"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setspl",
        "Set Split",
        0,
        "sorch0",
        "Set Split Orchestrator",
        child_orders=table,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setspl",
        "Set Split",
        1,
        "schl01",
        "Child 1",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setspl",
        "Set Split",
        2,
        "schl02",
        "Child 2",
        item_dependencies="executed:schl01",
    )
    for order, cid in ((3, "schl03"), (4, "schl04"), (5, "schl05"), (6, "schl06")):
        make_fixture_plan(
            repo,
            "pending",
            "20261010",
            "child",
            "approved",
            "setspl",
            "Set Split",
            order,
            cid,
            f"Child {order}",
        )

    # 1. Default run (no --split-sets): all 7 land in 1 shard and stderr suggests --split-sets
    code_default = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code_default == 0
    cap_def = capsys.readouterr()
    payload_def = json.loads(cap_def.out)
    non_empty_def = [s for s in payload_def["shards"] if s]
    assert len(non_empty_def) == 1
    assert len(non_empty_def[0]) == 7
    assert "ended up in 1 shard" in cap_def.err
    assert "--split-sets" in cap_def.err

    # 2. With --split-sets: 6 children split 2/2/2 across 3 shards, schl01+schl02 stay together,
    #    and orchestrator sorch0 is held back with a retire command
    code_split = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--split-sets",
            "--run",
            "agy",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code_split == 0
    cap_split = capsys.readouterr()
    payload_split = json.loads(cap_split.out)
    shards = payload_split["shards"]
    assert [len(s) for s in shards] == [2, 2, 2]
    all_scheduled = [cid for s in shards for cid in s]
    assert "sorch0" not in all_scheduled
    assert set(all_scheduled) == {
        "schl01",
        "schl02",
        "schl03",
        "schl04",
        "schl05",
        "schl06",
    }
    # Real dependency pair schl01 -> schl02 stays in the same shard with 0 cut edges
    pair_shards = [s for s in shards if "schl01" in s or "schl02" in s]
    assert len(pair_shards) == 1
    assert pair_shards[0] == ["schl01", "schl02"]
    assert payload_split["split_components"] == []
    assert any(
        h.get("orchestrator") == "sorch0" and h.get("reason") == "split-sets"
        for h in payload_split.get("held_back_orchestrators", [])
    )
    assert "sorch0" in cap_split.err and "held back under --split-sets" in cap_split.err
    assert "aw agy run" in cap_split.err


def test_partition_split_sets_review_keeps_orchestrator_in_shards(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """In review runs, --split-sets splits all plans including the orchestrator without holding it back."""
    repo = tmp_path / "repo_split_review"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    table = (
        ("01", "vchl01", "Child 1"),
        ("02", "vchl02", "Child 2"),
        ("03", "vchl03", "Child 3"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "to-review",
        "setrev",
        "Set Rev",
        0,
        "vorch0",
        "Set Rev Orchestrator",
        child_orders=table,
    )
    for order, cid in ((1, "vchl01"), (2, "vchl02"), (3, "vchl03")):
        make_fixture_plan(
            repo,
            "pending",
            "20261010",
            "child",
            "to-review",
            "setrev",
            "Set Rev",
            order,
            cid,
            f"Child {order}",
        )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "-n",
            "2",
            "--split-sets",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code == 0
    cap = capsys.readouterr()
    payload = json.loads(cap.out)
    assert [len(s) for s in payload["shards"]] == [2, 2]
    all_ids = {cid for s in payload["shards"] for cid in s}
    assert all_ids == {"vorch0", "vchl01", "vchl02", "vchl03"}
    assert not payload.get("held_back_orchestrators")


def test_partition_split_sets_for_backlog(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Backlog items sharing a Set stay in 1 shard with a --split-sets hint by default, and split with --split-sets."""
    repo = tmp_path / "repo_split_backlog"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    bkl_dir = repo / ".aw" / "records" / "backlog"
    bkl_dir.mkdir(parents=True, exist_ok=True)
    for idx, bid in enumerate(("bkl001", "bkl002", "bkl003", "bkl004"), start=1):
        (bkl_dir / f"20261010-bklset-{idx:02d}-{bid}-item-{idx}.backlog.md").write_text(
            f"# Backlog Item {idx}\n\n"
            f"- Id: {bid}\n"
            f"- Set: bklset (Backlog Set)\n"
            f"- Status: open\n"
            f"- Priority: medium\n",
            encoding="utf-8",
        )

    # Default: all 4 kept in 1 shard + hint suggesting --split-sets
    code_def = cli.main(
        [
            "partition",
            "-t",
            "backlog",
            "-s",
            "open",
            "-n",
            "2",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code_def == 0
    cap_def = capsys.readouterr()
    payload_def = json.loads(cap_def.out)
    assert [len(s) for s in payload_def["shards"]] == [4, 0]
    assert "ended up in 1 shard" in cap_def.err
    assert "--split-sets" in cap_def.err

    # With --split-sets: splits 2/2 across 2 shards
    code_split = cli.main(
        [
            "partition",
            "-t",
            "backlog",
            "-s",
            "open",
            "-n",
            "2",
            "--split-sets",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code_split == 0
    cap_split = capsys.readouterr()
    payload_split = json.loads(cap_split.out)
    assert [len(s) for s in payload_split["shards"]] == [2, 2]
    assert "hint:" not in cap_split.err


def test_partition_action_review_admits_explicit_rereview_ids_and_guards_sets_and_orchestrators(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Explicit non-orchestrator approved/reviewed IDs partition under --action review; Set names and orchestrators do not."""
    import io

    repo = tmp_path / "repo_rereview"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    table = (
        ("01", "rrch01", "Child 1"),
        ("02", "rrch02", "Child 2"),
        ("03", "rrch03", "Child 3"),
        ("04", "rrch04", "Child 4"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261122",
        "orchestrator",
        "approved",
        "rrset",
        "Re-review Set",
        0,
        "rrorch",
        "Re-review Orchestrator",
        child_orders=table,
    )
    for idx, (cid, st) in enumerate(
        (
            ("rrch01", "approved"),
            ("rrch02", "approved"),
            ("rrch03", "reviewed"),
            ("rrch04", "auto-approved"),
        ),
        start=1,
    ):
        make_fixture_plan(
            repo,
            "pending",
            "20261122",
            "child",
            st,
            "rrset",
            "Re-review Set",
            idx,
            cid,
            f"Child {idx}",
        )

    # 1. Explicit child IDs under --action review --split-sets succeed, split across shards, warn, and omit --yes.
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--action",
            "review",
            "--run",
            "agy",
            "--split-sets",
            "-n",
            "2",
            "--json",
            "--dir",
            str(repo),
            "rrch01",
            "rrch02",
            "rrch03",
            "rrch04",
        ]
    )
    assert code == 0
    cap = capsys.readouterr()
    payload = json.loads(cap.out)
    assert sorted(sum(payload["shards"], [])) == [
        "rrch01",
        "rrch02",
        "rrch03",
        "rrch04",
    ]
    assert sorted(len(s) for s in payload["shards"]) == [2, 2]
    assert payload["rereview_ids"] == ["rrch01", "rrch02", "rrch03", "rrch04"]
    assert all(
        cmd.startswith("aw agy run --action review ") and "--yes" not in cmd
        for cmd in payload["commands"]
    )
    assert (
        "warning: partitioning 4 plan(s) for re-review (3 already approved)" in cap.err
    )
    assert "requires typing 're-review' or passing --yes" in cap.err

    # 2. Explicit IDs via --stdin also work.
    monkeypatch.setattr("sys.stdin", io.StringIO("rrch01\nrrch03\n"))
    code_stdin = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--action",
            "review",
            "--run",
            "oc",
            "--stdin",
            "-n",
            "2",
            "--dir",
            str(repo),
        ]
    )
    assert code_stdin == 0
    cap_stdin = capsys.readouterr()
    assert "aw oc run --action review" in cap_stdin.out
    assert "rrch01" in cap_stdin.out and "rrch03" in cap_stdin.out

    # 3. Broad Set selector does NOT admit approved/reviewed plans for re-review.
    code_set = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--action",
            "review",
            "--dir",
            str(repo),
            "rrset",
        ]
    )
    assert code_set == 2
    capsys.readouterr()

    # 4. Explicit orchestrator ID is refused (and skipped with --skip-ineligible).
    code_orch = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--action",
            "review",
            "--dir",
            str(repo),
            "rrorch",
            "rrch01",
        ]
    )
    assert code_orch == 2
    cap_orch = capsys.readouterr()
    assert "orchestrator plan(s) cannot be re-reviewed" in cap_orch.err
    assert "rrorch" in cap_orch.err

    code_orch_skip = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--action",
            "review",
            "--skip-ineligible",
            "--run",
            "none",
            "--dir",
            str(repo),
            "rrorch",
            "rrch01",
        ]
    )
    assert code_orch_skip == 0
    cap_orch_skip = capsys.readouterr()
    assert "orchestrator plan" in cap_orch_skip.err and "skipping" in cap_orch_skip.err
    assert cap_orch_skip.out.strip() == "rrch01"


def test_unsatisfied_dependency_lists_prereqs_and_inspect_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unsatisfied-dependency refusals list all missing dependency id6s per blocked item,
    collapse repeated prerequisite fix clauses, emit aw att inspect commands, and expose
    unsatisfied_dependencies in --json output.
    """
    repo = tmp_path / "repo_unsat_inspect"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    # External prerequisite not selected
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setext",
        "External Prereq",
        1,
        "pext01",
        "External Prerequisite",
    )

    table_u = (
        ("01", "uchl01", "Child 1"),
        ("02", "uchl02", "Child 2"),
        ("03", "uchl03", "Child 3"),
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "setu",
        "Set U",
        0,
        "uorch0",
        "Set U Orchestrator",
        child_orders=table_u,
        item_dependencies="executed:uchl01, executed:uchl02, executed:uchl03",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setu",
        "Set U",
        1,
        "uchl01",
        "Child 1",
        item_dependencies="executed:pext01",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setu",
        "Set U",
        2,
        "uchl02",
        "Child 2",
        item_dependencies="executed:uchl01",
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "setu",
        "Set U",
        3,
        "uchl03",
        "Child 3",
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setu",
            "--run",
            "none",
            "--no-color",
            "--dir",
            str(repo),
        ]
    )
    assert code == 2
    cap = capsys.readouterr()
    assert cap.out == ""
    assert (
        "error: Set 'setu' cannot finish in this batch, so nothing was scheduled."
        in cap.err
    )
    assert "uchl01 (approved, unsatisfied dependency) [needs: pext01]" in cap.err
    assert "uchl02 (approved, unsatisfied dependency) [needs: uchl01]" in cap.err
    assert (
        "uorch0 (approved, unsatisfied dependency) [needs: uchl01, uchl02]" in cap.err
    )
    assert (
        "run with --with-dependencies, or execute prerequisites pext01, uchl01, uchl02 first"
        in cap.err
    )
    assert cap.err.count("run with --with-dependencies") == 1
    assert "for more info on dependencies, run: aw att pext01 uchl01 uchl02" in cap.err
    assert (
        "for more info on items missing those dependencies, run: aw att uorch0 uchl01 uchl02"
        in cap.err
    )

    # JSON output includes structured unsatisfied_dependencies per blocked member
    code_json = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "setu",
            "--run",
            "none",
            "--json",
            "--dir",
            str(repo),
        ]
    )
    assert code_json == 2
    cap_json = capsys.readouterr()
    payload = json.loads(cap_json.out)
    blocked_by_id = {b["id6"]: b for b in payload["blocked_sets"][0]["blocked"]}
    assert blocked_by_id["uchl01"]["unsatisfied_dependencies"] == ["pext01"]
    assert blocked_by_id["uchl02"]["unsatisfied_dependencies"] == ["uchl01"]
    assert blocked_by_id["uorch0"]["unsatisfied_dependencies"] == ["uchl01", "uchl02"]
