"""Behavioral tests for `aw partition` command and dependency clustering algorithm."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from agent_workflows import agent_schema
from agent_workflows import attention
from agent_workflows import cli
from agent_workflows import partition as part


def make_item(
    id6: str,
    dependencies: tuple[str, ...] = (),
    path: str = "",
    native_status: str = "approved",
    priority: str | None = None,
) -> attention.Item:
    """Helper to construct an attention.Item for partitioning tests."""
    return attention.Item(
        id=id6,
        path=path or f".aw/records/plans/pending/20260926-test-01-{id6}-test.ipd.md",
        tree="plans",
        native_status=native_status,
        attention_class="active",
        gate=None,
        last_history_at=None,
        priority=priority,
        blocks_release=None,
        detail_kind=None,
        detail_text=None,
        readiness="go",
        oqs=(),
        rqs=(),
        item_dependencies=dependencies,
        exec_progress=None,
        valid_progress=None,
    )


# ==============================================================================
# (a) Components on synthetic Items: two chains, fork-join, isolated, cycle
# ==============================================================================


def test_components_synthetic_patterns() -> None:
    # 1. Two chains: chn001 -> chn002 and chn003 -> chn004
    items_chains = [
        make_item("chn001"),
        make_item("chn002", ("executed:chn001",)),
        make_item("chn003"),
        make_item("chn004", ("executed:chn003",)),
    ]
    comps_chains = part.components(items_chains)
    assert len(comps_chains) == 2
    sets_chains = [{it.id for it in c} for c in comps_chains]
    assert sets_chains == [{"chn001", "chn002"}, {"chn003", "chn004"}]

    # 2. Fork-join: frk001 root -> frk002 & frk003 -> frk004
    items_fork_join = [
        make_item("frk001"),
        make_item("frk002", ("executed:frk001",)),
        make_item("frk003", ("executed:frk001",)),
        make_item("frk004", ("executed:frk002", "executed:frk003")),
    ]
    comps_fj = part.components(items_fork_join)
    assert len(comps_fj) == 1
    assert [it.id for it in comps_fj[0]] == ["frk001", "frk002", "frk003", "frk004"]

    # 3. Isolated nodes: iso001, iso002, iso003
    items_isolated = [
        make_item("iso002"),
        make_item("iso001"),
        make_item("iso003"),
    ]
    comps_iso = part.components(items_isolated)
    assert len(comps_iso) == 3
    # Deterministic order: size descending, then smallest id6
    assert [[it.id for it in c] for c in comps_iso] == [
        ["iso001"],
        ["iso002"],
        ["iso003"],
    ]

    # 4. Cycle: cyc001 <-> cyc002
    items_cycle = [
        make_item("cyc001", ("executed:cyc002",)),
        make_item("cyc002", ("executed:cyc001",)),
    ]
    comps_cyc = part.components(items_cycle)
    assert len(comps_cyc) == 1
    assert [it.id for it in comps_cyc[0]] == ["cyc001", "cyc002"]


def test_in_selection_edges_ignores_external_and_self() -> None:
    items = [
        make_item("itm001", ("executed:ext999", "executed:itm001", "executed:itm002")),
        make_item("itm002"),
    ]
    edges = part.in_selection_edges(items)
    # itm001 depends on itm002 (in selection). ext999 and self are ignored.
    assert edges["itm001"] == {"itm002"}
    assert edges["itm002"] == set()


def test_in_selection_edges_mixed_type_fixture() -> None:
    # A plan declaring state:spec:approved:<id6> or exists:backlog:<id6> where
    # a selected plan shares that id6 must NOT create an in-selection edge.
    # Only ipd edges (e.g. executed:dddddd) are kept.
    items = [
        make_item(
            "aaaaaa",
            ("state:spec:approved:bbbbbb", "exists:backlog:cccccc", "executed:dddddd"),
        ),
        make_item("bbbbbb"),
        make_item("cccccc"),
        make_item("dddddd"),
    ]
    edges = part.in_selection_edges(items)
    assert edges["aaaaaa"] == {"dddddd"}
    assert edges["bbbbbb"] == set()
    assert edges["cccccc"] == set()
    assert edges["dddddd"] == set()


# ==============================================================================
# (b) Packing: K=1, K > N, empty, balanced independents, fitting whole, oversized split
# ==============================================================================


def test_packing_k_bounds_and_empty() -> None:
    # Empty selection
    p_empty = part.partition([], 3)
    assert p_empty.shards == []
    assert p_empty.split_components == []

    # K = 1
    items = [make_item("itm001"), make_item("itm002")]
    p_k1 = part.partition(items, 1)
    assert len(p_k1.shards) == 1
    assert [it.id for it in p_k1.shards[0]] == ["itm001", "itm002"]

    # K > N (clamped to N)
    p_k_large = part.partition(items, 5)
    assert len(p_k_large.shards) == 2
    assert [len(s) for s in p_k_large.shards] == [1, 1]


def test_packing_balanced_independents() -> None:
    # 5 independent items, K = 3 -> capacities balanced, max size difference <= 1
    items = [make_item(f"ind00{i}") for i in range(1, 6)]
    p = part.partition(items, 3)
    assert len(p.shards) == 3
    sizes = [len(s) for s in p.shards]
    assert max(sizes) - min(sizes) <= 1
    assert sum(sizes) == 5


def test_packing_fitting_component_kept_whole() -> None:
    # 6 items, K = 3 -> cap = 2.
    # Two connected pairs {p00001, c00001}, {p00002, c00002} and two singletons.
    # Size 2 <= cap, so each connected pair must be placed whole in one shard.
    items = [
        make_item("p00001"),
        make_item("c00001", ("executed:p00001",)),
        make_item("p00002"),
        make_item("c00002", ("executed:p00002",)),
        make_item("iso001"),
        make_item("iso002"),
    ]
    p = part.partition(items, 3)
    assert len(p.shards) == 3
    assert len(p.split_components) == 0

    shard_id_sets = [{it.id for it in s} for s in p.shards]
    assert any({"p00001", "c00001"}.issubset(s) for s in shard_id_sets)
    assert any({"p00002", "c00002"}.issubset(s) for s in shard_id_sets)

    # Within each shard, prerequisites precede dependents
    for shard in p.shards:
        ids = [it.id for it in shard]
        if "p00001" in ids and "c00001" in ids:
            assert ids.index("p00001") < ids.index("c00001")
        if "p00002" in ids and "c00002" in ids:
            assert ids.index("p00002") < ids.index("c00002")


def test_packing_oversized_component_split() -> None:
    # 6 items in one chain with non-lexical ID order:
    # zzz001 <- aaa002 <- mmm003 <- bbb004 <- yyy005 <- ccc006
    # K = 3 -> cap = ceil(6 / 3) = 2.
    # Component size 6 > 2, so component must be split.
    items = [
        make_item("zzz001"),
        make_item("aaa002", ("executed:zzz001",)),
        make_item("mmm003", ("executed:aaa002",)),
        make_item("bbb004", ("executed:mmm003", "executed:zzz001")),
        make_item("yyy005", ("executed:bbb004",)),
        make_item("ccc006", ("executed:yyy005", "executed:mmm003")),
    ]
    p = part.partition(items, 3)
    assert len(p.shards) == 3
    assert len(p.split_components) == 1

    sn = p.split_components[0]
    assert sn.component_ids == [
        "zzz001",
        "aaa002",
        "mmm003",
        "bbb004",
        "yyy005",
        "ccc006",
    ]
    assert sn.shard_indexes == [0, 1, 2]
    expected_cut_edges = [
        ("aaa002", "zzz001"),
        ("bbb004", "mmm003"),
        ("ccc006", "yyy005"),
        ("mmm003", "aaa002"),
        ("yyy005", "bbb004"),
    ]
    assert sn.cut_edges == expected_cut_edges

    # Every item should be in exactly one shard
    all_assigned = [it.id for s in p.shards for it in s]
    assert sorted(all_assigned) == [
        "aaa002",
        "bbb004",
        "ccc006",
        "mmm003",
        "yyy005",
        "zzz001",
    ]

    # For every shard, for every pair where item B declares an in-selection edge
    # to item A in the same shard, assert A's index < B's index.
    in_sel = part.in_selection_edges(items)
    for shard in p.shards:
        ids = [it.id for it in shard]
        for b_idx, b_id in enumerate(ids):
            for a_id in in_sel.get(b_id, ()):
                if a_id in ids:
                    a_idx = ids.index(a_id)
                    assert a_idx < b_idx, f"Prerequisite {a_id} must precede {b_id}"

    # Specifically prove that lexical ordering would fail:
    # In Shard 0: zzz001 (depth 0) must precede bbb004 (depth 3)
    s0_ids = [it.id for it in p.shards[0]]
    assert s0_ids.index("zzz001") < s0_ids.index("bbb004")
    # In Shard 2: mmm003 (depth 2) must precede ccc006 (depth 5)
    s2_ids = [it.id for it in p.shards[2]]
    assert s2_ids.index("mmm003") < s2_ids.index("ccc006")


def test_packing_determinism() -> None:
    items = [
        make_item("n00001"),
        make_item("n00002", ("executed:n00001",)),
        make_item("n00003", ("executed:n00002",)),
        make_item("p00001"),
        make_item("c00001", ("executed:p00001",)),
        make_item("iso001"),
        make_item("iso002"),
    ]
    p1 = part.partition(items, 3)
    p2 = part.partition(items, 3)
    assert [[it.id for it in s] for s in p1.shards] == [
        [it.id for it in s] for s in p2.shards
    ]
    assert [sc.to_dict() for sc in p1.split_components] == [
        sc.to_dict() for sc in p2.split_components
    ]


# ==============================================================================
# (c) Selection on a fixture repo with real plan files
# ==============================================================================


@pytest.fixture
def plan_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    pending = repo / ".aw" / "records" / "plans" / "pending"
    executed = repo / ".aw" / "records" / "plans" / "executed"
    pending.mkdir(parents=True)
    executed.mkdir(parents=True)

    # 1. Root plan 1 (approved, high)
    (pending / "20260926-set1-01-pln001-plan-one.ipd.md").write_text(
        "---\n"
        "- Id: pln001\n"
        "- Set: set1 (Set One)\n"
        "- Status: approved\n"
        "- Priority: high\n"
        "- Item-Dependencies: none\n"
        "---\n"
        "# Plan One\n"
    )

    # 2. Child plan 2 (approved, medium, depends on pln001)
    (pending / "20260926-set1-02-pln002-plan-two.ipd.md").write_text(
        "---\n"
        "- Id: pln002\n"
        "- Set: set1 (Set One)\n"
        "- Status: approved\n"
        "- Priority: medium\n"
        "- Item-Dependencies: executed:pln001\n"
        "---\n"
        "# Plan Two\n"
    )

    # 3. Plan 3 (to-review, low)
    (pending / "20260926-set2-01-pln003-plan-three.ipd.md").write_text(
        "---\n"
        "- Id: pln003\n"
        "- Set: set2 (Set Two)\n"
        "- Status: to-review\n"
        "- Priority: low\n"
        "- Item-Dependencies: none\n"
        "---\n"
        "# Plan Three\n"
    )

    # 4. Terminal plan in executed/ directory
    (executed / "20260926-set3-01-pln004-plan-four.ipd.md").write_text(
        "---\n"
        "- Id: pln004\n"
        "- Set: set3 (Set Three)\n"
        "- Status: executed\n"
        "- Priority: high\n"
        "- Item-Dependencies: none\n"
        "---\n"
        "# Plan Four\n"
    )

    return repo


def test_collect_candidates_selection_filters(plan_fixture_repo: Path) -> None:
    # 1. Terminal plans excluded
    candidates = part.collect(plan_fixture_repo, artifact_type="plans")
    cand_ids = {it.id for it in candidates}
    assert "pln004" not in cand_ids

    # 2. Selectors filter
    candidates_sel = part.collect(
        plan_fixture_repo, artifact_type="plans", selectors=["set2"]
    )
    assert [it.id for it in candidates_sel] == ["pln003"]

    # 3. Status filter
    candidates_app = part.collect(
        plan_fixture_repo, artifact_type="plans", statuses=["approved"]
    )
    assert {it.id for it in candidates_app} == {"pln001", "pln002"}

    # 4. Priority filter & invalid priority error
    candidates_pri = part.collect(
        plan_fixture_repo, artifact_type="plans", priorities=["high"]
    )
    assert [it.id for it in candidates_pri] == ["pln001"]

    with pytest.raises(ValueError, match="invalid priority 'urgent'"):
        part.collect(plan_fixture_repo, artifact_type="plans", priorities=["urgent"])

    # 5. Stdin selection with unknown ID refused
    with pytest.raises(ValueError, match="unknown selector 'unknown99'"):
        part.collect(
            plan_fixture_repo, artifact_type="plans", stdin_ids=["pln001", "unknown99"]
        )

    candidates_stdin = part.collect(
        plan_fixture_repo, artifact_type="plans", stdin_ids=["pln001"]
    )
    assert [it.id for it in candidates_stdin] == ["pln001"]

    # 6. --max keeps prerequisites before dependents
    candidates_max = part.collect(
        plan_fixture_repo, artifact_type="plans", statuses=["approved"], max_count=1
    )
    assert len(candidates_max) == 1
    # pln001 is depth 0 (prerequisite), pln002 is depth 1 (dependent), so pln001 is kept
    assert candidates_max[0].id == "pln001"


# ==============================================================================
# (d) Formatting: none, oc, agy, --as, --as refusal with --run oc, shell quoting
# ==============================================================================


def test_format_shard_all_modes() -> None:
    # 1. none
    assert part.format_shard("none", ["pln001", "pln002"]) == "pln001 pln002"

    # 2. oc
    assert part.format_shard("oc", ["pln001", "pln002"]) == "aw oc run pln001 pln002"

    # 3. agy
    assert part.format_shard("agy", ["pln001", "pln002"]) == "aw agy run pln001 pln002"

    # 4. --as routes through host-neutral `aw run as <profile>`
    assert (
        part.format_shard("as", ["pln001", "pln002"], profile="gem")
        == "aw run as gem pln001 pln002"
    )

    # 5. --as combined with --run oc is refused
    with pytest.raises(ValueError, match="--as cannot be combined with --run oc"):
        part.format_shard("oc", ["pln001"], profile="gem")

    # 6. Shell quoting and passthrough options
    cmd_quoted = part.format_shard(
        "oc",
        ["pln001", "pln002"],
        model="custom/model with spaces",
        variant="high-temp",
    )
    assert (
        cmd_quoted
        == "aw oc run pln001 pln002 --model 'custom/model with spaces' --variant high-temp"
    )

    # 7. Empty id list emits empty string (no command emitted)
    assert part.format_shard("oc", []) == ""


# ==============================================================================
# (e) CLI end-to-end on fixture, --json shape, exit codes, no repository mutation
# ==============================================================================


def test_cli_partition_end_to_end(
    plan_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Record directory tree before running CLI
    tree_before = sorted(
        str(p.relative_to(plan_fixture_repo)) for p in plan_fixture_repo.rglob("*")
    )

    # Run CLI end to end
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--dir",
            str(plan_fixture_repo),
            "-s",
            "approved",
            "-n",
            "2",
            "--run",
            "oc",
        ]
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.strip().split("\n") if line.strip()]
    # Two approved plans (pln001, pln002) where pln002 depends on pln001
    # Cap = ceil(2/2) = 1. Oversized component of 2 items is split across 2 shards.
    assert len(lines) == 2
    for line in lines:
        assert line.startswith("aw oc run")

    # Stderr summary exists
    assert "Partitioned 2 items across 2 shard(s)" in captured.err

    # Verify no files in repo were created or modified
    tree_after = sorted(
        str(p.relative_to(plan_fixture_repo)) for p in plan_fixture_repo.rglob("*")
    )
    assert tree_before == tree_after


def test_cli_partition_json_shape(
    plan_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--dir",
            str(plan_fixture_repo),
            "-s",
            "approved",
            "-n",
            "2",
            "--json",
        ]
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "shards" in payload
    assert "commands" in payload
    assert "split_components" in payload
    assert "cycles" in payload
    # 0hz005: "unknown" key removed because it was unconditionally [], dead weight;
    # collect refuses an unknown selector with ValueError instead.
    assert "unknown" not in payload
    assert set(payload.keys()) == {"shards", "commands", "split_components", "cycles"}
    assert len(payload["shards"]) == 2
    assert len(payload["commands"]) == 2


def test_cli_partition_exit_codes(
    plan_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # 1. Missing -t/--type -> exit 2 (argparse error)
    with pytest.raises(SystemExit) as exc:
        cli.main(["partition", "--dir", str(plan_fixture_repo)])
    assert exc.value.code == 2

    # 2. Invalid choice for -t -> exit 2 (argparse error)
    with pytest.raises(SystemExit) as exc:
        cli.main(["partition", "-t", "invalid", "--dir", str(plan_fixture_repo)])
    assert exc.value.code == 2

    # 3. Invalid status for artifact type (e.g. -t plans -s open) -> exit 2
    assert (
        cli.main(
            ["partition", "-t", "plans", "-s", "open", "--dir", str(plan_fixture_repo)]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "status 'open' is not valid for artifact type 'plans'" in err

    # 4. Invalid shards (-n 0) -> exit 2
    assert (
        cli.main(
            ["partition", "-t", "plans", "--dir", str(plan_fixture_repo), "-n", "0"]
        )
        == 2
    )

    # 5. Invalid max (--max 0) -> exit 2
    assert (
        cli.main(
            ["partition", "-t", "plans", "--dir", str(plan_fixture_repo), "--max", "0"]
        )
        == 2
    )

    # 6. Invalid priority -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "plans",
                "--dir",
                str(plan_fixture_repo),
                "-p",
                "invalid-pri",
            ]
        )
        == 2
    )

    # 7. Incompatible --as and --run oc -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "plans",
                "--dir",
                str(plan_fixture_repo),
                "--run",
                "oc",
                "--as",
                "gem",
            ]
        )
        == 2
    )

    # 8. Mixed actions refusal (selection contains both approved [execute] and to-review [review]) -> exit 2
    assert cli.main(["partition", "-t", "plans", "--dir", str(plan_fixture_repo)]) == 2
    err = capsys.readouterr().err
    assert "selection contains mixed actions (execute, review)" in err

    # 9. Conflicting explicit --action -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "plans",
                "-s",
                "approved",
                "--action",
                "plan",
                "--dir",
                str(plan_fixture_repo),
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "conflicts with requested --action 'plan'" in err

    # 10. Unknown selector token -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "plans",
                "nonexistent99",
                "--dir",
                str(plan_fixture_repo),
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "unknown selector 'nonexistent99'" in err

    # 11. Stdin unknown selector -> exit 2
    monkeypatch.setattr("sys.stdin", io.StringIO("unknown99\n"))
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "plans",
                "--stdin",
                "--dir",
                str(plan_fixture_repo),
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "unknown selector 'unknown99'" in err

    # 12. Ineligible explicitly selected item (pln004 is executed) -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "plans",
                "pln004",
                "--dir",
                str(plan_fixture_repo),
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "is ineligible for runner dispatch" in err


def test_cli_partition_stdin_end_to_end(
    plan_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("pln001\npln002\n"))
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--dir",
            str(plan_fixture_repo),
            "--stdin",
            "-n",
            "1",
            "--run",
            "oc",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "pln001" in captured.out
    assert "pln002" in captured.out


def test_cli_partition_positional_selector(
    plan_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "set1",
            "--dir",
            str(plan_fixture_repo),
            "-n",
            "1",
            "--run",
            "oc",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "pln001" in captured.out
    assert "pln002" in captured.out
    assert "pln003" not in captured.out


def test_cli_partition_json_empty_selection(
    plan_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "to-review",
            "-p",
            "high",
            "--dir",
            str(plan_fixture_repo),
            "--json",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["shards"] == []
    assert payload["commands"] == []


def test_cli_partition_agent_mode(
    plan_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--dir",
            str(plan_fixture_repo),
            "-s",
            "approved",
            "-n",
            "2",
            "--agent",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert agent_schema.validate_agent_record(record) == []
    assert record["schema"] == "aw.agent/v1"
    assert record["kind"] == "result"
    assert record["cmd"] == "partition"
    assert record["outcome"] == "ok"
    assert record["exit"] == 0
    assert record["verified"] is True
    assert record["complete"] is True
    assert len(record["shards"]) == 2
    assert len(record["commands"]) == 2
    # 0hz005: "unknown" key removed from agent record payload; ensure absence
    assert "unknown" not in record
    assert "Partitioned 2 items across 2 shard(s)" in captured.err


# ==============================================================================
# (f) Backlog partitioning fixture, graduation commands, dependencies & errors
# ==============================================================================


@pytest.fixture
def backlog_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "bkl_repo"
    open_dir = repo / ".aw" / "records" / "backlog" / "open"
    done_dir = repo / ".aw" / "records" / "backlog" / "done"
    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    open_dir.mkdir(parents=True)
    done_dir.mkdir(parents=True)
    plan_dir.mkdir(parents=True)

    # Cross-tree plan item to test wrong-type selector error
    (plan_dir / "20260920-setx-01-plnx01-other-plan.ipd.md").write_text(
        "---\n- Id: plnx01\n- Set: setx\n- Status: approved\n- Item-Dependencies: none\n---\n"
    )

    # 1. bkl001: oldest open item (2026-09-20)
    (open_dir / "20260920-bkl001-01-bkl001-item-one.backlog.md").write_text(
        "- Id: bkl001\n"
        "- Status: open\n"
        "- Priority: high\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-09-20 created: item one\n"
    )

    # 2. bkl002: second oldest open item (2026-09-22), depends on bkl001
    (open_dir / "20260922-bkl002-01-bkl002-item-two.backlog.md").write_text(
        "- Id: bkl002\n"
        "- Status: open\n"
        "- Priority: medium\n"
        "- Item-Dependencies: exists:backlog:bkl001\n\n"
        "## Workflow history\n"
        "- 2026-09-22 created: item two\n"
    )

    # 3. bkl003: third oldest open item (2026-09-25)
    (open_dir / "20260925-bkl003-01-bkl003-item-three.backlog.md").write_text(
        "- Id: bkl003\n"
        "- Status: open\n"
        "- Priority: low\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-09-25 created: item three\n"
    )

    # 4. bkl004: newest open item (2026-09-28), depends on bkl003
    (open_dir / "20260928-bkl004-01-bkl004-item-four.backlog.md").write_text(
        "- Id: bkl004\n"
        "- Status: open\n"
        "- Priority: high\n"
        "- Item-Dependencies: exists:backlog:bkl003\n\n"
        "## Workflow history\n"
        "- 2026-09-28 created: item four\n"
    )

    # 5. bkl005: done item (2026-09-10) - non-runnable
    (done_dir / "20260910-bkl005-01-bkl005-item-five.backlog.md").write_text(
        "- Id: bkl005\n"
        "- Status: done\n"
        "- Priority: high\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-09-10 created: item five\n"
    )

    return repo


def test_cli_partition_backlog_graduation_and_ordering(
    backlog_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Partition oldest 3 open backlog items across 2 shards
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "backlog",
            "-s",
            "open",
            "-n",
            "2",
            "--max",
            "3",
            "--dir",
            str(backlog_fixture_repo),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    lines = [
        line_item.strip()
        for line_item in captured.out.splitlines()
        if line_item.strip()
    ]
    assert len(lines) == 2

    # Both shards must emit `aw oc run --action plan ...`
    for line in lines:
        assert line.startswith("aw oc run --action plan ")

    # Oldest 3 open items are bkl001, bkl002, bkl003; bkl004 (newest) is excluded by --max 3
    # bkl001 and bkl002 are connected (size 2 <= cap 2), kept in one shard
    all_emitted = " ".join(lines)
    assert "bkl001" in all_emitted
    assert "bkl002" in all_emitted
    assert "bkl003" in all_emitted
    assert "bkl004" not in all_emitted
    assert "bkl005" not in all_emitted

    # Within the connected shard, bkl001 must precede bkl002
    shard_with_pair = next(line_item for line_item in lines if "bkl001" in line_item)
    assert shard_with_pair.index("bkl001") < shard_with_pair.index("bkl002")


def test_cli_partition_backlog_errors_and_wrong_type(
    backlog_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 1. Invalid status for backlog (e.g. approved) -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "backlog",
                "-s",
                "approved",
                "--dir",
                str(backlog_fixture_repo),
            ]
        )
        == 2
    )
    assert (
        "status 'approved' is not valid for artifact type 'backlog'"
        in capsys.readouterr().err
    )

    # 2. Ineligible explicitly selected item (bkl005 is done) -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "backlog",
                "bkl005",
                "--dir",
                str(backlog_fixture_repo),
            ]
        )
        == 2
    )
    assert "is ineligible for runner dispatch" in capsys.readouterr().err

    # 3. Wrong-type selector: plnx01 is a plan, not backlog -> exit 2
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "backlog",
                "plnx01",
                "--dir",
                str(backlog_fixture_repo),
            ]
        )
        == 2
    )
    assert "belongs to 'plans', not 'backlog'" in capsys.readouterr().err


# ==============================================================================
# (g) Specs partitioning fixture, action derivation, mixed refusal, profile formatting
# ==============================================================================


@pytest.fixture
def specs_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "spc_repo"
    toreview_dir = repo / ".aw" / "records" / "specs" / "to-review"
    approved_dir = repo / ".aw" / "records" / "specs" / "approved"
    implemented_dir = repo / ".aw" / "records" / "specs" / "implemented"
    toreview_dir.mkdir(parents=True)
    approved_dir.mkdir(parents=True)
    implemented_dir.mkdir(parents=True)

    # 1. spc001: to-review (2026-09-21)
    (toreview_dir / "20260921-spc001-01-spc001-spec-one.spec.md").write_text(
        "# Spec One\n\n"
        "- Id: spc001\n"
        "- Status: to-review\n"
        "- Priority: high\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-09-21 created: spec one\n"
    )

    # 2. spc002: to-review (2026-09-23), depends on spc001
    (toreview_dir / "20260923-spc002-01-spc002-spec-two.spec.md").write_text(
        "# Spec Two\n\n"
        "- Id: spc002\n"
        "- Status: to-review\n"
        "- Priority: medium\n"
        "- Item-Dependencies: exists:spec:spc001\n\n"
        "## Workflow history\n"
        "- 2026-09-23 created: spec two\n"
    )

    # 3. spc003: approved (2026-09-24)
    (approved_dir / "20260924-spc003-01-spc003-spec-three.spec.md").write_text(
        "# Spec Three\n\n"
        "- Id: spc003\n"
        "- Status: approved\n"
        "- Priority: high\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-09-24 created: spec three\n"
    )

    # 4. spc004: implemented (2026-09-18) - non-runnable
    (implemented_dir / "20260918-spc004-01-spc004-spec-four.spec.md").write_text(
        "# Spec Four\n\n"
        "- Id: spc004\n"
        "- Status: implemented\n"
        "- Priority: low\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n"
        "- 2026-09-18 created: spec four\n"
    )

    return repo


def test_cli_partition_specs_review_and_plan_actions(
    specs_fixture_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 1. to-review specs produce `--action review`
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "specs",
            "-s",
            "to-review",
            "-n",
            "1",
            "--dir",
            str(specs_fixture_repo),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "aw oc run --action review spc001 spc002"

    # 2. approved specs produce `--action plan`
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "specs",
            "-s",
            "approved",
            "-n",
            "1",
            "--dir",
            str(specs_fixture_repo),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "aw oc run --action plan spc003"

    # 3. Launch profile formatting: --as gem with --action review
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "specs",
            "-s",
            "to-review",
            "-n",
            "1",
            "--as",
            "gem",
            "--dir",
            str(specs_fixture_repo),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "aw run as gem --action review spc001 spc002"

    # 4. Runner 'none' produces space-separated IDs only
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "specs",
            "-s",
            "to-review",
            "-n",
            "1",
            "--run",
            "none",
            "--dir",
            str(specs_fixture_repo),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "spc001 spc002"

    # 5. Mixed actions refusal (to-review -> review, approved -> plan) -> exit 2
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "specs",
            "-n",
            "1",
            "--dir",
            str(specs_fixture_repo),
        ]
    )
    assert exit_code == 2
    assert "selection contains mixed actions (plan, review)" in capsys.readouterr().err

    # 6. Explicit action legality conflict -> exit 2
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "specs",
            "-s",
            "approved",
            "--action",
            "review",
            "--dir",
            str(specs_fixture_repo),
        ]
    )
    assert exit_code == 2
    assert "conflicts with requested --action 'review'" in capsys.readouterr().err


def test_cli_partition_deduplication_and_stdin(
    backlog_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Stdin with duplicate IDs: deduplicated before partitioning
    monkeypatch.setattr("sys.stdin", io.StringIO("bkl001\nbkl001\nbkl003\n"))
    exit_code = cli.main(
        [
            "partition",
            "-t",
            "backlog",
            "--stdin",
            "-n",
            "1",
            "--dir",
            str(backlog_fixture_repo),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "aw oc run --action plan bkl001 bkl003"
    assert "Partitioned 2 items across 1 shard(s)" in captured.err


def test_cli_partition_ambiguous_and_positional_types(
    backlog_fixture_repo: Path,
    specs_fixture_repo: Path,
    plan_fixture_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # 1. Positional selector for backlog
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "backlog",
                "bkl001",
                "--dir",
                str(backlog_fixture_repo),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "aw oc run --action plan bkl001"

    # 2. Positional selector for specs
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "specs",
                "spc001",
                "--dir",
                str(specs_fixture_repo),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "aw oc run --action review spc001"

    # 3. Wrong-type selector for specs (passing plnx01 from plans)
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "specs",
                "pln001",
                "--dir",
                str(plan_fixture_repo),
            ]
        )
        == 2
    )
    assert "belongs to 'plans', not 'specs'" in capsys.readouterr().err

    # 4. Ambiguous substring selector rejected
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "backlog",
                "item",
                "--dir",
                str(backlog_fixture_repo),
            ]
        )
        == 2
    )
    assert (
        "is ambiguous, matching multiple files via substring" in capsys.readouterr().err
    )

    # 5. Positional duplicate IDs deduplicated
    assert (
        cli.main(
            [
                "partition",
                "-t",
                "backlog",
                "bkl001",
                "bkl001",
                "--dir",
                str(backlog_fixture_repo),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert captured.out.strip() == "aw oc run --action plan bkl001"
    assert "Partitioned 1 items across 1 shard(s)" in captured.err
