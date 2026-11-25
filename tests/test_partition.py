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
from tests.record_builder import RecordBuilder


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
    # Contiguous topological slices keep every cut edge strictly forward
    # (shard 0: zzz001, aaa002; shard 1: mmm003, bbb004; shard 2: yyy005, ccc006)
    # so the shard dependency graph is acyclic and deadlock-free.
    expected_cut_edges = [
        ("bbb004", "zzz001"),
        ("ccc006", "mmm003"),
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

    # Every cut edge must point strictly forward (prereq shard < consumer shard): zero cycles.
    shard_of = {it.id: idx for idx, shard in enumerate(p.shards) for it in shard}
    for consumer, prereq in sn.cut_edges:
        assert shard_of[prereq] < shard_of[consumer], (
            f"Cut edge {consumer} -> {prereq} must point forward, "
            f"got shard {shard_of[prereq]} -> shard {shard_of[consumer]}"
        )

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
    # In Shard 0: zzz001 (depth 0) must precede aaa002 (depth 1)
    s0_ids = [it.id for it in p.shards[0]]
    assert s0_ids.index("zzz001") < s0_ids.index("aaa002")
    # In Shard 1: mmm003 (depth 2) must precede bbb004 (depth 3)
    s1_ids = [it.id for it in p.shards[1]]
    assert s1_ids.index("mmm003") < s1_ids.index("bbb004")
    # In Shard 2: yyy005 (depth 4) must precede ccc006 (depth 5)
    s2_ids = [it.id for it in p.shards[2]]
    assert s2_ids.index("yyy005") < s2_ids.index("ccc006")


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
        str(
            RecordBuilder().plan(
                id6="pln001",
                title="Plan One",
                when="2026-09-26",
                set="set1",
                order=1,
                status="approved",
                priority="high",
                item_dependencies="none",
                text_only=True,
            )
        )
    )

    # 2. Child plan 2 (approved, medium, depends on pln001)
    (pending / "20260926-set1-02-pln002-plan-two.ipd.md").write_text(
        str(
            RecordBuilder().plan(
                id6="pln002",
                title="Plan Two",
                when="2026-09-26",
                set="set1",
                order=2,
                status="approved",
                priority="medium",
                item_dependencies="executed:pln001",
                text_only=True,
            )
        )
    )

    # 3. Plan 3 (to-review, low)
    (pending / "20260926-set2-01-pln003-plan-three.ipd.md").write_text(
        str(
            RecordBuilder().plan(
                id6="pln003",
                title="Plan Three",
                when="2026-09-26",
                set="set2",
                order=1,
                status="to-review",
                priority="low",
                item_dependencies="none",
                text_only=True,
            )
        )
    )

    # 4. Terminal plan in executed/ directory
    (executed / "20260926-set3-01-pln004-plan-four.ipd.md").write_text(
        str(
            RecordBuilder().plan(
                id6="pln004",
                title="Plan Four",
                when="2026-09-26",
                set="set3",
                order=1,
                status="executed",
                priority="high",
                item_dependencies="none",
                disposition="executed",
                text_only=True,
            )
        )
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

    # 3b. Status-not filter & invalid status-not error
    candidates_not_app = part.collect(
        plan_fixture_repo, artifact_type="plans", statuses_not=["approved"]
    )
    assert {it.id for it in candidates_not_app} == {"pln003"}

    with pytest.raises(
        ValueError, match="status 'bogus' is not valid for artifact type 'plans'"
    ):
        part.collect(plan_fixture_repo, artifact_type="plans", statuses_not=["bogus"])

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
        str(
            RecordBuilder().plan(
                id6="plnx01",
                title="Other Plan",
                when="2026-09-20",
                set="setx",
                order=1,
                status="approved",
                item_dependencies="none",
                text_only=True,
            )
        )
    )

    # 1. bkl001: oldest open item (2026-09-20)
    (open_dir / "20260920-bkl001-01-bkl001-item-one.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl001",
            status="open",
            priority="high",
            item_dependencies="none",
            history=["- 2026-09-20 created: item one"],
            text_only=True,
        )
    )

    # 2. bkl002: second oldest open item (2026-09-22), depends on bkl001
    (open_dir / "20260922-bkl002-01-bkl002-item-two.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl002",
            status="open",
            priority="medium",
            item_dependencies="exists:backlog:bkl001",
            history=["- 2026-09-22 created: item two"],
            text_only=True,
        )
    )

    # 3. bkl003: third oldest open item (2026-09-25)
    (open_dir / "20260925-bkl003-01-bkl003-item-three.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl003",
            status="open",
            priority="low",
            item_dependencies="none",
            history=["- 2026-09-25 created: item three"],
            text_only=True,
        )
    )

    # 4. bkl004: newest open item (2026-09-28), depends on bkl003
    (open_dir / "20260928-bkl004-01-bkl004-item-four.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl004",
            status="open",
            priority="high",
            item_dependencies="exists:backlog:bkl003",
            history=["- 2026-09-28 created: item four"],
            text_only=True,
        )
    )

    # 5. bkl005: done item (2026-09-10) - non-runnable
    (done_dir / "20260910-bkl005-01-bkl005-item-five.backlog.md").write_text(
        RecordBuilder().backlog(
            id6="bkl005",
            status="done",
            priority="high",
            item_dependencies="none",
            history=["- 2026-09-10 created: item five"],
            text_only=True,
        )
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


def test_cli_partition_infers_backlog_type_and_clusters_shared_sets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Omitting -t infers backlog from selectors, and shared backlog Sets stay in one shard."""
    repo = tmp_path / "bkl_set_repo"
    open_dir = repo / ".aw" / "records" / "backlog" / "open"
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    open_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)
    (plans_dir / "20261119-demo-01-pln901-demo-plan.ipd.md").write_text(
        RecordBuilder().plan(
            id6="pln901", set="demo", order=1, status="approved", text_only=True
        ),
        encoding="utf-8",
    )

    # 3 items in Set 'metastore' and 3 singleton items.
    for idx, (bid, sid) in enumerate(
        (
            ("ms0001", "metastore"),
            ("ms0002", "metastore"),
            ("ms0003", "metastore"),
            ("sg0001", "sg0001"),
            ("sg0002", "sg0002"),
            ("sg0003", "sg0003"),
        ),
        start=1,
    ):
        (open_dir / f"2026111{idx}-{sid}-01-{bid}-item.backlog.md").write_text(
            RecordBuilder().backlog(
                id6=bid, status="open", work_kind="bug", set=sid, text_only=True
            ),
            encoding="utf-8",
        )

    # Also add a plan whose Set name collides with backlog id ms0001 (e.g. a sibling plan).
    (plans_dir / "20261119-ms0001-01-pln902-sibling.ipd.md").write_text(
        RecordBuilder().plan(
            id6="pln902", set="ms0001", order=1, status="approved", text_only=True
        ),
        encoding="utf-8",
    )

    # 1. Passing -t plan --action plan on a backlog selector produces the actionable hint.
    rc_hint = cli.main(
        [
            "partition",
            "-t",
            "plan",
            "--action",
            "plan",
            "sg0001",
            "--dir",
            str(repo),
        ]
    )
    assert rc_hint == 2
    err_hint = capsys.readouterr().err
    assert "belongs to 'backlog', not 'plans'" in err_hint
    assert "-t backlog" in err_hint

    # 2. Omitting -t (even WITHOUT --action plan, and even when a plan has Set: ms0001)
    # prefers id6 over setid, infers backlog, and keeps all 3 'metastore' items in ONE shard.
    rc_no_action = cli.main(
        [
            "partition",
            "-n",
            "3",
            "ms0001",
            "ms0002",
            "ms0003",
            "--dir",
            str(repo),
        ]
    )
    assert rc_no_action == 0
    assert "ms0001" in capsys.readouterr().out

    rc_ok = cli.main(
        [
            "partition",
            "-n",
            "3",
            "--action",
            "plan",
            "ms0001",
            "ms0002",
            "ms0003",
            "sg0001",
            "sg0002",
            "sg0003",
            "--dir",
            str(repo),
        ]
    )
    assert rc_ok == 0
    out_lines = [
        ln for ln in capsys.readouterr().out.splitlines() if "run --action plan" in ln
    ]
    assert len(out_lines) == 3
    metastore_shards = [
        ln for ln in out_lines if "ms0001" in ln or "ms0002" in ln or "ms0003" in ln
    ]
    assert len(metastore_shards) == 1
    assert all(m in metastore_shards[0] for m in ("ms0001", "ms0002", "ms0003"))

    # 3. Omitting -t with mixed plans + backlog or with no selectors fails cleanly (exit 2).
    assert cli.main(["partition", "ms0001", "pln901", "--dir", str(repo)]) == 2
    assert "multiple artifact types" in capsys.readouterr().err

    with pytest.raises(SystemExit) as exc_missing:
        cli.main(["partition", "--dir", str(repo)])
    assert exc_missing.value.code == 2
    assert "-t/--type/--tree is required" in capsys.readouterr().err


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
        RecordBuilder().spec(
            id6="spc001",
            status="to-review",
            priority="high",
            item_dependencies="none",
            history=["- 2026-09-21 created: spec one"],
            text_only=True,
        )
    )

    # 2. spc002: to-review (2026-09-23), depends on spc001
    (toreview_dir / "20260923-spc002-01-spc002-spec-two.spec.md").write_text(
        RecordBuilder().spec(
            id6="spc002",
            status="to-review",
            priority="medium",
            item_dependencies="exists:spec:spc001",
            history=["- 2026-09-23 created: spec two"],
            text_only=True,
        )
    )

    # 3. spc003: approved (2026-09-24)
    (approved_dir / "20260924-spc003-01-spc003-spec-three.spec.md").write_text(
        RecordBuilder().spec(
            id6="spc003",
            status="approved",
            priority="high",
            item_dependencies="none",
            history=["- 2026-09-24 created: spec three"],
            text_only=True,
        )
    )

    # 4. spc004: implemented (2026-09-18) - non-runnable
    (implemented_dir / "20260918-spc004-01-spc004-spec-four.spec.md").write_text(
        RecordBuilder().spec(
            id6="spc004",
            status="implemented",
            priority="low",
            item_dependencies="none",
            history=["- 2026-09-18 created: spec four"],
            text_only=True,
        )
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


# ==============================================================================
# (l) Active (already running) items exclusion and --include-active
# ==============================================================================


def test_collect_excludes_active_by_default_and_includes_with_flag(
    plan_fixture_repo: Path,
) -> None:
    # pln001 is active in live runner run; pln002 is not
    active_map = {"pln001": "running"}

    # Default (include_active=False): pln001 excluded
    cand_default = part.collect(
        plan_fixture_repo,
        artifact_type="plans",
        statuses=["approved"],
        include_active=False,
        run_map=active_map,
    )
    assert [it.id for it in cand_default] == ["pln002"]

    # Explicit include_active=True: pln001 included
    cand_included = part.collect(
        plan_fixture_repo,
        artifact_type="plans",
        statuses=["approved"],
        include_active=True,
        run_map=active_map,
    )
    assert {it.id for it in cand_included} == {"pln001", "pln002"}


def test_cli_partition_excludes_active_plans_by_default(
    plan_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "agent_workflows.attention.get_active_runs_map",
        lambda repo: {"pln001": "running"},
    )

    # Without --include-active: only pln002 is partitioned
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "--dir",
            str(plan_fixture_repo),
            "--run",
            "none",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "pln002" in captured.out
    assert "pln001" not in captured.out
    assert "Partitioned 1 items across 1 shard(s)" in captured.err

    # With --include-active: both pln001 and pln002 are partitioned
    code_inc = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "--include-active",
            "--dir",
            str(plan_fixture_repo),
            "--run",
            "none",
        ]
    )
    assert code_inc == 0
    captured_inc = capsys.readouterr()
    assert "pln001" in captured_inc.out
    assert "pln002" in captured_inc.out
    assert "Partitioned 2 items across 2 shard(s)" in captured_inc.err


def test_cli_partition_all_active_yields_no_matching_items(
    plan_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Both pln001 and pln002 are actively running
    monkeypatch.setattr(
        "agent_workflows.attention.get_active_runs_map",
        lambda repo: {"pln001": "running", "pln002": "queued"},
    )

    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "--dir",
            str(plan_fixture_repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "No matching plans items found to partition." in captured.err

    # With --include-active, they are scheduled
    code_inc = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "--include-active",
            "--dir",
            str(plan_fixture_repo),
            "--run",
            "none",
        ]
    )
    assert code_inc == 0
    captured_inc = capsys.readouterr()
    assert "pln001" in captured_inc.out
    assert "pln002" in captured_inc.out


def test_cli_partition_backlog_excludes_active(
    backlog_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # bkl001 is running
    monkeypatch.setattr(
        "agent_workflows.attention.get_active_runs_map",
        lambda repo: {"bkl001": "running"},
    )

    # Excluded by default
    code = cli.main(
        [
            "partition",
            "-t",
            "backlog",
            "-s",
            "open",
            "--dir",
            str(backlog_fixture_repo),
            "--run",
            "none",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "bkl001" not in captured.out
    assert "bkl002" in captured.out

    # Included with --include-active
    code_inc = cli.main(
        [
            "partition",
            "-t",
            "backlog",
            "-s",
            "open",
            "--include-active",
            "--dir",
            str(backlog_fixture_repo),
            "--run",
            "none",
        ]
    )
    assert code_inc == 0
    captured_inc = capsys.readouterr()
    assert "bkl001" in captured_inc.out
    assert "bkl002" in captured_inc.out


def test_cli_partition_ineligible_aggregated_diagnostics(
    plan_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Multiple ineligible items are aggregated with clear expected status and remedy hints."""
    pending = plan_fixture_repo / ".aw" / "records" / "plans" / "pending"
    (pending / "20261017-revset-01-r20rid-plan-r20.ipd.md").write_text(
        str(
            RecordBuilder().plan(
                id6="r20rid",
                title="Plan R20",
                when="2026-10-17",
                set="revset",
                order=1,
                status="reviewed",
                item_dependencies="none",
                text_only=True,
            )
        )
    )
    (pending / "20261017-revset-02-44nfmd-plan-44n.ipd.md").write_text(
        str(
            RecordBuilder().plan(
                id6="44nfmd",
                title="Plan 44N",
                when="2026-10-17",
                set="revset",
                order=2,
                status="reviewed",
                item_dependencies="none",
                text_only=True,
            )
        )
    )

    monkeypatch.setattr("sys.stdin", io.StringIO("r20rid\n44nfmd\n"))
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--stdin",
            "--dir",
            str(plan_fixture_repo),
        ]
    )
    assert code == 2
    captured = capsys.readouterr()
    assert "selection is ineligible for runner dispatch (2 items):" in captured.err
    assert "item r20rid must be in status 'approved' and not 'reviewed'" in captured.err
    assert "item 44nfmd must be in status 'approved' and not 'reviewed'" in captured.err
    assert "approve with aw ipd set approved r20rid 44nfmd --by-human" in captured.err
    assert "pass --skip-ineligible to omit" in captured.err


def test_cli_partition_skip_ineligible_flag(
    plan_fixture_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--skip-ineligible warns on stderr and partitions the runnable subset."""
    pending = plan_fixture_repo / ".aw" / "records" / "plans" / "pending"
    (pending / "20261017-revset-01-r20rid-plan-r20.ipd.md").write_text(
        str(
            RecordBuilder().plan(
                id6="r20rid",
                title="Plan R20",
                when="2026-10-17",
                set="revset",
                order=1,
                status="reviewed",
                item_dependencies="none",
                text_only=True,
            )
        )
    )

    monkeypatch.setattr("sys.stdin", io.StringIO("r20rid\npln001\n"))
    code = cli.main(
        [
            "partition",
            "-t",
            "plans",
            "--stdin",
            "--skip-ineligible",
            "-n",
            "1",
            "--run",
            "none",
            "--dir",
            str(plan_fixture_repo),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert (
        "warning: item r20rid must be in status 'approved' and not 'reviewed' (skipping)"
        in captured.err
    )
    assert "pln001" in captured.out
    assert "r20rid" not in captured.out


def test_partition_id6_highlighting_with_color(
    plan_fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When color is enabled, id6s and diagnostic elements carry ANSI styling."""
    import argparse
    from agent_workflows import partition
    from agent_workflows.term import Term

    pending = plan_fixture_repo / ".aw" / "records" / "plans" / "pending"
    (pending / "20261017-revset-01-r20rid-plan-r20.ipd.md").write_text(
        str(
            RecordBuilder().plan(
                id6="r20rid",
                title="Plan R20",
                when="2026-10-17",
                set="revset",
                order=1,
                status="reviewed",
                item_dependencies="none",
                text_only=True,
            )
        )
    )

    stderr_buf = io.StringIO()
    monkeypatch.setattr("sys.stderr", stderr_buf)
    colored_term = Term(stream=stderr_buf, color=True, depth="256")

    args = argparse.Namespace(
        dir=str(plan_fixture_repo),
        artifact_type="plans",
        selectors=["r20rid"],
        shards=1,
        max=None,
        as_profile=None,
        run=None,
        model=None,
        variant=None,
        action=None,
        order_by=None,
        json=False,
        agent=False,
        stdin=False,
        status=[],
        status_not=[],
        priority=[],
        allow_partial_sets=False,
        skip_ineligible=False,
        with_dependencies=False,
        include_active=False,
    )

    code = partition.run_partition(args, term=colored_term)
    assert code == 2
    err_text = stderr_buf.getvalue()
    # id6 must be bold highlighted
    assert "\033[1mr20rid\033[0m" in err_text
    # Error label must be bold red
    assert colored_term.colorize("Error:", "red", "bold") in err_text
    # Remedy command and flag must be cyan
    assert "\033[36maw ipd set approved r20rid --by-human\033[0m" in err_text
    assert "\033[36m--skip-ineligible\033[0m" in err_text

    # With color=False, verify no ANSI escapes are present
    plain_buf = io.StringIO()
    monkeypatch.setattr("sys.stderr", plain_buf)
    plain_term = Term(stream=plain_buf, color=False)
    code_plain = partition.run_partition(args, term=plain_term)
    assert code_plain == 2
    plain_text = plain_buf.getvalue()
    assert "\033[" not in plain_text
    assert (
        "item r20rid with status 'reviewed' is ineligible for runner dispatch"
        in plain_text
    )
    assert "item r20rid must be in status 'approved' and not 'reviewed'" in plain_text


def test_dag_safe_split_extracts_parallel_branches_and_appends_poll_for_deps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--split-sets on a multi-branch Set emits runnable parallel shards + --poll-for-deps tail,
    suppresses raw cut-edge dumps unless --verbose, and colorizes stderr while keeping stdout plain."""
    import argparse
    import io
    from agent_workflows import partition, runner_shared
    from agent_workflows.term import Term
    from tests.support import git, init_repo

    repo = init_repo(tmp_path / "dagrepo")
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True, exist_ok=True)

    def _write_plan(
        id6: str,
        order: int,
        deps: str = "none",
        kind: str | None = None,
        children_table: str = "",
    ) -> None:
        text = str(
            RecordBuilder().plan(
                id6=id6,
                title=f"Plan {id6}",
                when="2026-11-23",
                set="dagset",
                order=order,
                status="approved",
                readiness="go-pending-approval",
                approval="2026-11-23, tester",
                priority="medium",
                item_dependencies=deps,
                kind=kind,
                history=[
                    "- 2026-11-23 approved (tester): approved",
                    "- 2026-11-23 /plan-review (tester): APPROVE",
                    "- 2026-11-23 draft (tester): created.",
                ],
                text_only=True,
            )
        )
        if children_table:
            text += "\n## Child IPDs\n\n" + children_table + "\n"
        (pending / f"20261123-dagset-{order:02d}-{id6}-plan-{id6}.ipd.md").write_text(
            text, encoding="utf-8"
        )

    child_ids = [
        ("br1001", 1, "none"),
        ("br1002", 2, "executed:br1001"),
        ("br1003", 3, "executed:br1002"),
        ("br2001", 4, "none"),
        ("br2002", 5, "executed:br2001"),
        ("br3001", 6, "none"),
        ("jn0001", 7, "executed:br1003, executed:br2002, executed:br3001"),
        ("jn0002", 8, "executed:jn0001"),
    ]
    rows = "\n".join(
        f"| {order:02d} | `{cid}` | Plan {cid} | approved |"
        for cid, order, _ in child_ids
    )
    table = "| Order | ID | Title | Status |\n|---:|---|---|---|\n" + rows
    _write_plan("orch00", 0, deps="none", kind="orchestrator", children_table=table)
    for cid, order, deps in child_ids:
        _write_plan(cid, order, deps=deps)
    git(repo, "add", ".aw/records/plans/pending")
    git(repo, "commit", "-qm", "seed dagset")

    def _run(verbose: bool, color: bool) -> tuple[int, str, str]:
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        monkeypatch.setattr("sys.stdout", out_buf)
        monkeypatch.setattr("sys.stderr", err_buf)
        term = Term(stream=err_buf, color=color, depth="256" if color else None)
        args = argparse.Namespace(
            dir=str(repo),
            artifact_type="plans",
            selectors=[],
            shards=4,
            max=None,
            as_profile=None,
            run="oc",
            model=None,
            variant=None,
            action=None,
            order_by=None,
            json=False,
            agent=False,
            verbose=verbose,
            stdin=False,
            status=["approved"],
            status_not=[],
            priority=[],
            allow_partial_sets=False,
            split_sets=True,
            skip_ineligible=False,
            with_dependencies=False,
            include_active=True,
            review_unreviewed_deps=False,
        )
        rc = partition.run_partition(args, term=term)
        return rc, out_buf.getvalue(), err_buf.getvalue()

    # 1. Default (non-verbose, colored) run
    rc, stdout_c, stderr_c = _run(verbose=False, color=True)
    assert rc == 0
    # stdout commands remain plain uncolored text; stderr uses ANSI colors
    assert "\033[" not in stdout_c
    assert "\033[" in stderr_c
    # No raw Python tuple dump on default output; concise summary + --verbose hint
    assert "[('" not in stderr_c
    assert "3 cut edge(s)" in stderr_c
    assert "--verbose" in stderr_c
    assert "--poll-for-deps 5m" in stderr_c

    cmds = [ln.strip() for ln in stdout_c.splitlines() if ln.strip()]
    assert len(cmds) == 4
    # First 3 shards are independent parallel branches with zero --poll-for-deps
    for parallel_cmd in cmds[:3]:
        assert "--poll-for-deps" not in parallel_cmd
    # Shard 3 is the downstream join tail (jn0001, jn0002) with --poll-for-deps 5m
    assert "--poll-for-deps 5m" in cmds[3]
    assert "jn0001" in cmds[3] and "jn0002" in cmds[3]

    # 2. Verbose (plain) run lists formatted cut edges
    rc_v, stdout_v, stderr_v = _run(verbose=True, color=False)
    assert rc_v == 0
    assert "\033[" not in stderr_v
    assert "jn0001 (shard 3) <-" in stderr_v
    assert "br1003" in stderr_v and "br2002" in stderr_v and "br3001" in stderr_v

    # 3. Verify with real freeze-time refusal gate that all 4 emitted shards are runnable:
    #    shards 0..2 pass immediately; shard 3 enters waitable polling instead of refusing.
    deps_by_id = {
        cid: [d.strip() for d in deps.split(",") if d.strip() and d.strip() != "none"]
        for cid, _order, deps in child_ids
    }
    for idx, cmd in enumerate(cmds):
        toks = cmd.split()
        # strip `aw oc run` and optional `--poll-for-deps 5m`
        ids = [t for t in toks[3:] if t not in ("--poll-for-deps", "5m")]
        queue = [
            {
                "id6": pid,
                "action": "execute",
                "status": "queued",
                "initial_status": "approved",
                "artifact_type": "ipd",
                "dependencies": deps_by_id[pid],
                "configured_file": str(
                    next(pending.glob(f"*{pid}*.ipd.md")).relative_to(repo)
                ),
            }
            for pid in ids
        ]
        if idx < 3:
            runner_shared.enforce_freeze_time_refusal(
                queue,
                repo=repo,
                host="oc",
                allow_waitable_external_deps=False,
            )
        else:
            with pytest.raises(
                runner_shared.DriverError, match="RUN-DEPENDENCY-UNSATISFIABLE"
            ):
                runner_shared.enforce_freeze_time_refusal(
                    queue,
                    repo=repo,
                    host="oc",
                    allow_waitable_external_deps=False,
                )
            with pytest.raises(runner_shared.WaitableExternalDependencies) as exc_info:
                runner_shared.enforce_freeze_time_refusal(
                    queue,
                    repo=repo,
                    host="oc",
                    allow_waitable_external_deps=True,
                )
            waiting_targets = {t[2] for t in exc_info.value.waiting_deps}
            assert waiting_targets == {"br1003", "br2002", "br3001"}


@pytest.mark.core
class TestArtifactMetaWidenedFrontMatterReaders:
    """Behavioral tests for IPD 75jciz: artifact_meta helpers and migrated readers/writers."""

    def test_scope_paths_plan_and_apply_rewrites_and_skips(
        self, tmp_path: Path
    ) -> None:
        from agent_workflows import artifact_refs

        repo = tmp_path / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)

        old_p = ".aw/records/backlog/open/20261124-bk0001-01-bk0001-item.backlog.md"
        new_p = (
            ".aw/records/backlog/graduated/20261124-bk0001-01-bk0001-item.backlog.md"
        )
        path_map = {old_p: new_p}

        fenced_block = f"```sh\necho {old_p}\n```\n"
        prose_line = f"Historical prose mentions {old_p} untouched.\n"
        history_entries = ["- 2026-11-24 draft (tester): seeded plan"]

        # 1. Normal pending plan: Scope-Paths rewritten, prose/fenced/history unchanged.
        normal_plan = pending / "20261124-demo-01-pl0001-normal.ipd.md"
        normal_text = RecordBuilder().plan(
            title="Normal Rewrite Plan",
            id6="pl0001",
            set="demo",
            order=1,
            status="approved",
            scope_paths=f"{old_p}, agent_workflows/artifact_meta.py",
            history=history_entries,
            body=f"## Notes\n\n{prose_line}\n{fenced_block}",
            text_only=True,
        )
        normal_plan.write_text(normal_text, encoding="utf-8")

        # 2. Grandfathered Scope-Paths: skipped, bytes untouched.
        gf_plan = pending / "20261124-demo-02-pl0002-gf.ipd.md"
        gf_text = RecordBuilder().plan(
            title="Grandfathered Plan",
            id6="pl0002",
            set="demo",
            order=2,
            status="approved",
            scope_paths="grandfathered",
            body=f"## Notes\n\nMentions {old_p} in prose only.\n",
            text_only=True,
        )
        gf_plan.write_text(gf_text, encoding="utf-8")

        # 3. Forward declaration (destination already listed): skipped with reason, untouched.
        fwd_plan = pending / "20261124-demo-03-pl0003-fwd.ipd.md"
        fwd_text = RecordBuilder().plan(
            title="Forward Declaration Plan",
            id6="pl0003",
            set="demo",
            order=3,
            status="approved",
            scope_paths=f"{old_p}, {new_p}",
            text_only=True,
        )
        fwd_plan.write_text(fwd_text, encoding="utf-8")

        edits, skipped = artifact_refs.plan_scope_path_reference_rewrites(
            repo, path_map
        )
        assert [e.file for e in edits] == [normal_plan]
        assert edits[0].old == old_p
        assert edits[0].new == new_p
        assert len(skipped) == 1
        assert skipped[0][0] == fwd_plan
        assert "destination already declared in Scope-Paths" in skipped[0][1]

        modified = artifact_refs.apply_scope_path_reference_rewrites(repo, edits)
        assert modified == [normal_plan]

        updated = normal_plan.read_text(encoding="utf-8")
        assert f"- Scope-Paths: {new_p}, agent_workflows/artifact_meta.py\n" in updated
        assert prose_line in updated
        assert fenced_block in updated
        assert updated.count("2026-11-24 draft (tester): seeded plan") == 1
        # No new history entry was appended.
        hist_idx = updated.index("## Workflow history")
        next_h2 = updated.find("\n## ", hist_idx + 1)
        hist_section = updated[hist_idx : next_h2 if next_h2 != -1 else len(updated)]
        hist_bullets = [ln for ln in hist_section.splitlines() if ln.startswith("- ")]
        assert len(hist_bullets) == 1
        assert gf_plan.read_text(encoding="utf-8") == gf_text
        assert fwd_plan.read_text(encoding="utf-8") == fwd_text

    def test_orchestrator_detection_partition_and_review_basis(
        self, tmp_path: Path
    ) -> None:
        from agent_workflows import review_basis

        repo = tmp_path / "repo"
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True)

        orch_rel = ".aw/records/plans/pending/20261124-demo-00-or0001-orch.ipd.md"
        (repo / orch_rel).write_text(
            "# IPD: Orchestrator\n\n- Kind: Orchestrator\n- Status: approved\n- Id: or0001\n",
            encoding="utf-8",
        )
        lower_rel = ".aw/records/plans/pending/20261124-demo-00-or0002-lower.ipd.md"
        (repo / lower_rel).write_text(
            "# IPD: Lowercase Kind\n\n- kind: ORCHESTRATOR\n- Status: approved\n- Id: or0002\n",
            encoding="utf-8",
        )
        child_rel = ".aw/records/plans/pending/20261124-demo-01-ch0001-child.ipd.md"
        child_text = (
            "# IPD: Child Plan\n\n"
            "- Kind: child\n"
            "- Status: approved\n"
            "- Id: ch0001\n\n"
            "## Goal\n\n"
            "Body prose quoting:\n"
            "- Kind: orchestrator\n"
        )
        (repo / child_rel).write_text(child_text, encoding="utf-8")

        assert part._is_orchestrator_plan(make_item("or0001", path=orch_rel), repo)
        assert part._is_orchestrator_plan(make_item("or0002", path=lower_rel), repo)
        assert not part._is_orchestrator_plan(make_item("ch0001", path=child_rel), repo)

        assert review_basis._is_orchestrator_text(
            (repo / orch_rel).read_text(encoding="utf-8")
        )
        assert review_basis._is_orchestrator_text(
            (repo / lower_rel).read_text(encoding="utf-8")
        )
        assert not review_basis._is_orchestrator_text(child_text)

    def test_check_engine_multiline_cited_spec_ids_and_review_index(
        self, tmp_path: Path
    ) -> None:
        from agent_workflows import check_engine

        plan_text = (
            "# IPD: Multiline Citations\n\n"
            "- Concern: Enforces spec sp0001\n"
            "  and continuation cites sp0002.\n"
            "- Scope: Covers sp0002 again and\n"
            "  adds sp0003 on continuation.\n"
            "- Scope-Paths: .aw/records/specs/20261124-sp0004-01-sp0004-demo.spec.md\n"
            "  extra/sp0005.py\n"
            "- Status: draft\n\n"
            "## Goal\n\n"
            "Body prose citing sp9999 must be ignored.\n"
        )
        known = ["sp0001", "sp0002", "sp0003", "sp0004", "sp0005", "sp9999"]
        cited = check_engine.parse_cited_spec_ids(plan_text, known)
        assert cited == ["sp0001", "sp0002", "sp0003", "sp0004", "sp0005"]

        repo = tmp_path / "repo"
        reviews = repo / ".aw" / "records" / "reviews"
        reviews.mkdir(parents=True)
        rev_valid = reviews / "20261124-demo-01-ab1234-plan.review.md"
        rev_valid.write_text(
            "# Plan Review\n\n- Subject-Id: ab1234\n- Verdict: APPROVE\n\n## Findings\n- Subject-Id: zz9999\n",
            encoding="utf-8",
        )
        rev_invalid = reviews / "20261124-demo-02-badid-plan.review.md"
        rev_invalid.write_text(
            "# Plan Review\n\n- Subject-Id: NOTVALID\n",
            encoding="utf-8",
        )
        rev_body_only = reviews / "20261124-demo-03-body-plan.review.md"
        rev_body_only.write_text(
            "# Plan Review\n\n## Body\n\n- Subject-Id: cd5678\n",
            encoding="utf-8",
        )

        index = check_engine._review_index(repo)
        assert index == {"ab1234": [rev_valid]}

    def test_coverage_record_read_explicit_model_and_host_default(self) -> None:
        from agent_workflows import coverage_record

        explicit_text = (
            "# IPD: Orchestrator\n\n"
            "- Kind: orchestrator\n"
            "- Coverage: pass\n"
            "- Coverage-Fingerprint: deadbeef1234\n"
            "- Coverage-Checked: 2026-11-24 by claude-sonnet-4-6\n"
            "- Status: approved\n"
        )
        rec_explicit = coverage_record.read(explicit_text)
        assert rec_explicit.verdict == "pass"
        assert rec_explicit.fingerprint == "deadbeef1234"
        assert rec_explicit.date == "2026-11-24"
        assert rec_explicit.model == "claude-sonnet-4-6"

        default_text = (
            "# IPD: Orchestrator\n\n"
            "- Kind: orchestrator\n"
            "- Coverage: fail\n"
            "- Coverage-Fingerprint: cafe0000beef\n"
            "- Coverage-Checked: 2026-11-24 by host-default\n"
            "- Status: approved\n\n"
            "## Coverage findings\n\n"
            '- "missing child for step 2"\n'
        )
        rec_default = coverage_record.read(default_text)
        assert rec_default.verdict == "fail"
        assert rec_default.fingerprint == "cafe0000beef"
        assert rec_default.date == "2026-11-24"
        assert rec_default.model == "by host-default"
        assert rec_default.quotes == ("missing child for step 2",)

        no_model_text = (
            "# IPD: Orchestrator\n\n"
            "- Coverage: pass\n"
            "- Coverage-Fingerprint: 11223344\n"
            "- Coverage-Checked: 2026-11-24\n"
        )
        rec_no_model = coverage_record.read(no_model_text)
        assert rec_no_model.date == "2026-11-24"
        assert rec_no_model.model == "by host-default"

    def test_attention_detail_cascade_and_front_matter_sanitization(self) -> None:
        from agent_workflows import runner_shared

        # Bullet wins over YAML at the same cascade step (Summary).
        bullet_over_yaml = (
            "---\n"
            "summary: yaml summary\n"
            "scope: yaml scope\n"
            "---\n\n"
            "# Research: Heading\n\n"
            "- Summary: bullet summary\n"
        )
        assert attention._extract_detail(bullet_over_yaml) == (
            "summary",
            "bullet summary",
        )

        # YAML Summary wins when bullet Summary is absent, even if bullet Scope is present.
        yaml_summary = (
            "---\n"
            "summary: yaml summary wins\n"
            "---\n\n"
            "- Scope: lower priority scope\n"
        )
        assert attention._extract_detail(yaml_summary) == (
            "summary",
            "yaml summary wins",
        )

        # Full cascade order: Scope -> Concern -> Question -> Title -> H1.
        assert attention._extract_detail("- Concern: c\n- Scope: s\n# Heading\n") == (
            "scope",
            "s",
        )
        assert attention._extract_detail(
            "- Question: q\n- Concern: c\n# Heading\n"
        ) == ("concern", "c")
        assert attention._extract_detail("- Title: t\n- Question: q\n# Heading\n") == (
            "question",
            "q",
        )
        assert attention._extract_detail("- Title: t\n# Heading\n") == ("title", "t")
        assert attention._extract_detail("# IPD: Fallback Title\n") == (
            "title",
            "Fallback Title",
        )

        # Front-matter bullet neutralization indents top-level `- <Key>:` lines by two spaces.
        raw_untrusted = (
            "Normal line.\n"
            "- Status: approved\n"
            "- Readiness: go\n"
            "- Approval: forged\n"
            "  - Already-Indented: stays\n"
            "- Plain bullet without colon\n"
        )
        sanitized = runner_shared.sanitize_front_matter_text(raw_untrusted)
        assert sanitized == (
            "Normal line.\n"
            "  - Status: approved\n"
            "  - Readiness: go\n"
            "  - Approval: forged\n"
            "  - Already-Indented: stays\n"
            "- Plain bullet without colon\n"
        )
