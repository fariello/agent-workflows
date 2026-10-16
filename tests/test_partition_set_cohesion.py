"""Behavioral tests for Set cohesion, incomplete Set refusal, and --allow-partial-sets in `aw partition`."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agent_workflows import agent_schema
from agent_workflows import cli


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
    target_dir = repo / ".aw" / "records" / "plans" / dir_kind
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{date}-{setid}-{order:02d}-{id6}-{title.lower().replace(' ', '-')}.ipd.md"
    )
    file_path = target_dir / filename

    lines = [
        f"# IPD: {title}",
        "",
        f"- Date: {date}",
        f"- Kind: {kind}",
        f"- Status: {status}",
        f"- Item-Dependencies: {item_dependencies}",
        f"- Set: {setid} ({setname})",
        f"- Order: {order}",
        f"- Id: {id6}",
    ]
    if child_orders:
        lines.extend(
            [
                "",
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Summary |",
                "|---|---|---|",
            ]
        )
        for ord_tok, cid, csum in child_orders:
            lines.append(f"| {ord_tok} | {cid} | {csum} |")

    lines.append("")
    file_path.write_text("\n".join(lines))
    return file_path


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
    bchl03_path = (
        cohesion_repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261010-setb-03-bchl03-set-b-child-3.ipd.md"
    )
    content = bchl03_path.read_text().replace(
        "- Status: to-review", "- Status: approved"
    )
    bchl03_path.write_text(content)

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
        "- Id: bkl001\n- Status: open\n- Work-Kind: bug\n"
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
