"""Characterization tests for research frontmatter writers (IPD 9gy5jk E-03).

Pins the kept Phase-B behavior of `aw research mv`, `aw research set-assign`,
`aw archive research`, and `aw research promote` using isolated `tmp_path` git
repositories and the real CLI entry points.
"""

from __future__ import annotations

import io
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Optional

import pytest

from agent_workflows import artifact_meta as _meta, cli

pytestmark = pytest.mark.core


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "char@example.invalid"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Char"], cwd=root, check=True)
    (root / ".aw" / "records" / "research").mkdir(parents=True)
    return root


def _seed_doc(
    repo_root: Path,
    filename: str,
    *,
    id6: str,
    created: str = "20260701",
    set_id: str = "charset",
    order: Optional[str] = "03",
    topic: str = "[demo]",
    model: Optional[str] = "",
    kind: str = "notes",
    status: Optional[str] = None,
    outcome: str = "none-yet",
    summary: str = "Characterization fixture",
    consumed_by: str = "[]",
    body: str = "\n## Notes\nOriginal body line.\nmodel: untouched\nstatus: untouched\n",
) -> Path:
    rdir = repo_root / ".aw" / "records" / "research"
    rdir.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"id: {id6}",
        f"created: {created}",
        f"set: {set_id}",
    ]
    if order is not None:
        lines.append(f"order: {order}")
    lines.append(f"topic: {topic}")
    if model is not None:
        lines.append(f"model: {model}" if model else "model:")
    lines.append(f"kind: {kind}")
    if status is not None:
        lines.append(f"status: {status}" if status else "status:")
    lines.extend(
        [
            f"outcome: {outcome}",
            f"summary: {summary}",
            f"consumed-by: {consumed_by}",
            "---",
        ]
    )
    path = rdir / filename
    path.write_text("\n".join(lines) + body, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "commit", "-qm", f"seed {filename}"], cwd=repo_root, check=True
    )
    return path


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = cli.main(argv)
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _find_by_id6(repo_root: Path, id6: str) -> Path:
    matches = [
        p
        for p in (repo_root / ".aw" / "records" / "research").rglob(f"*{id6}*.md")
        if p.is_file()
    ]
    assert len(matches) == 1, f"Expected 1 file for {id6}, found {matches}"
    return matches[0]


def test_e03_1_archive_and_promote_without_status_insert_directly_after_kind(
    tmp_path: Path,
) -> None:
    """E-03 (1): archiving or promoting a status-less doc inserts `status: <new>` directly after `kind:`."""
    root = _init_repo(tmp_path)
    src_arch = _seed_doc(
        root,
        "20260701-charset-01-ch0001-no-status-arch.notes.md",
        id6="ch0001",
        order="01",
        kind="notes",
        status=None,
    )
    before_arch = src_arch.read_text(encoding="utf-8").splitlines()

    rc, out, err = _run_cli(
        ["archive", "research", "ch0001", "--apply", "--dir", str(root)]
    )
    assert rc == 0, f"archive failed: {out}\n{err}"

    dst_arch = _find_by_id6(root, "ch0001")
    assert "archive/202607" in dst_arch.as_posix()
    after_arch = dst_arch.read_text(encoding="utf-8").splitlines()
    kind_idx = before_arch.index("kind: notes")
    expected_arch = (
        before_arch[: kind_idx + 1] + ["status: archive"] + before_arch[kind_idx + 1 :]
    )
    assert after_arch == expected_arch
    assert "## Workflow history" not in dst_arch.read_text(encoding="utf-8")

    src_prom = _seed_doc(
        root,
        "20260701-charset-02-ch0002-no-status-prom.research-prompt.md",
        id6="ch0002",
        order="02",
        kind="research-prompt",
        status=None,
    )
    before_prom = src_prom.read_text(encoding="utf-8").splitlines()

    rc2, out2, err2 = _run_cli(
        [
            "research",
            "promote",
            "ch0002",
            "--to",
            "reference",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc2 == 0, f"promote failed: {out2}\n{err2}"

    dst_prom = _find_by_id6(root, "ch0002")
    assert "reference/202607" in dst_prom.as_posix()
    after_prom = dst_prom.read_text(encoding="utf-8").splitlines()
    kind_idx2 = before_prom.index("kind: research-prompt")
    expected_prom = (
        before_prom[: kind_idx2 + 1]
        + ["status: reference"]
        + before_prom[kind_idx2 + 1 :]
    )
    assert after_prom == expected_prom
    assert "## Workflow history" not in dst_prom.read_text(encoding="utf-8")


def test_e03_2_archive_and_promote_rewrite_existing_and_empty_status_in_place(
    tmp_path: Path,
) -> None:
    """E-03 (2): a doc whose block has a `status:` line (populated or empty) gets it rewritten in place."""
    root = _init_repo(tmp_path)
    src_pop = _seed_doc(
        root,
        "20260701-charset-01-ch0003-has-status.notes.md",
        id6="ch0003",
        order="01",
        status="todo",
    )
    before_pop = src_pop.read_text(encoding="utf-8").splitlines()

    rc, out, err = _run_cli(
        [
            "research",
            "promote",
            "ch0003",
            "--to",
            "reference",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc == 0, f"promote failed: {out}\n{err}"

    dst_pop = _find_by_id6(root, "ch0003")
    after_pop = dst_pop.read_text(encoding="utf-8").splitlines()
    assert len(after_pop) == len(before_pop)
    assert [(b, a) for b, a in zip(before_pop, after_pop) if b != a] == [
        ("status: todo", "status: reference")
    ]

    src_empty = _seed_doc(
        root,
        "20260701-charset-02-ch0004-empty-status.notes.md",
        id6="ch0004",
        order="02",
        status="",
    )
    before_empty = src_empty.read_text(encoding="utf-8").splitlines()

    rc2, out2, err2 = _run_cli(
        ["archive", "research", "ch0004", "--apply", "--dir", str(root)]
    )
    assert rc2 == 0, f"archive failed: {out2}\n{err2}"

    dst_empty = _find_by_id6(root, "ch0004")
    after_empty = dst_empty.read_text(encoding="utf-8").splitlines()
    assert len(after_empty) == len(before_empty)
    assert [(b, a) for b, a in zip(before_empty, after_empty) if b != a] == [
        ("status:", "status: archive")
    ]


def test_e03_3_mv_and_set_assign_leave_absent_keys_absent(tmp_path: Path) -> None:
    """E-03 (3): `aw research mv` and `aw research set-assign` leave a key absent when lacking its line."""
    root = _init_repo(tmp_path)
    src_mv = _seed_doc(
        root,
        "20260701-charset-03-ch0005-no-model.notes.md",
        id6="ch0005",
        order="03",
        model=None,
        status=None,
    )
    before_mv = src_mv.read_text(encoding="utf-8").splitlines()

    rc, out, err = _run_cli(
        [
            "research",
            "mv",
            "ch0005",
            "--model",
            "sonnet5high",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc == 0, f"mv --model failed: {out}\n{err}"

    dst_mv = _find_by_id6(root, "ch0005")
    assert dst_mv.name == "20260701-charset-03-ch0005-no-model.sonnet5high.notes.md"
    after_mv_text = dst_mv.read_text(encoding="utf-8")
    assert after_mv_text.splitlines() == before_mv
    assert "\nmodel:" not in after_mv_text.split("---", 2)[1]

    src_sa = _seed_doc(
        root,
        "20260701-charset-04-ch0006-no-order-model.notes.md",
        id6="ch0006",
        order=None,
        model=None,
        status=None,
    )
    before_sa = src_sa.read_text(encoding="utf-8").splitlines()

    rc2, out2, err2 = _run_cli(
        [
            "research",
            "set-assign",
            "ch0006",
            "--set",
            "assigned",
            "--order",
            "7",
            "--date",
            "20260815",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc2 == 0, f"set-assign failed: {out2}\n{err2}"

    dst_sa = _find_by_id6(root, "ch0006")
    assert dst_sa.name == "20260815-assigned-07-ch0006-no-order-model.notes.md"
    after_sa = dst_sa.read_text(encoding="utf-8").splitlines()
    assert len(after_sa) == len(before_sa)
    assert [(b, a) for b, a in zip(before_sa, after_sa) if b != a] == [
        ("set: charset", "set: assigned")
    ]
    fm_block = dst_sa.read_text(encoding="utf-8").split("---", 2)[1]
    assert "order:" not in fm_block
    assert "model:" not in fm_block


def test_e03_4_only_edited_frontmatter_lines_differ_and_no_workflow_history(
    tmp_path: Path,
) -> None:
    """E-03 (4): moved files differ from source only on edited frontmatter lines and have no `## Workflow history`."""
    root = _init_repo(tmp_path)
    src_mv = _seed_doc(
        root,
        "20260701-charset-03-ch0007-diff-mv.notes.md",
        id6="ch0007",
        order="03",
        model="",
        kind="notes",
        status=None,
    )
    before_mv = src_mv.read_text(encoding="utf-8").splitlines()

    rc, out, err = _run_cli(
        [
            "research",
            "mv",
            "ch0007",
            "--slug",
            "renamed-mv",
            "--model",
            "opus55high",
            "--kind",
            "findings",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc == 0, f"mv failed: {out}\n{err}"

    dst_mv = _find_by_id6(root, "ch0007")
    after_mv_text = dst_mv.read_text(encoding="utf-8")
    after_mv = after_mv_text.splitlines()
    assert len(after_mv) == len(before_mv)
    assert [(b, a) for b, a in zip(before_mv, after_mv) if b != a] == [
        ("model:", "model: opus55high"),
        ("kind: notes", "kind: findings"),
    ]
    assert "## Workflow history" not in after_mv_text

    src_sa = _seed_doc(
        root,
        "20260701-charset-04-ch0008-diff-sa.notes.md",
        id6="ch0008",
        order="04",
        model="",
        status=None,
    )
    before_sa = src_sa.read_text(encoding="utf-8").splitlines()

    rc2, out2, err2 = _run_cli(
        [
            "research",
            "set-assign",
            "ch0008",
            "--set",
            "grpset",
            "--order",
            "2",
            "--date",
            "20260820",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc2 == 0, f"set-assign failed: {out2}\n{err2}"

    dst_sa = _find_by_id6(root, "ch0008")
    after_sa_text = dst_sa.read_text(encoding="utf-8")
    after_sa = after_sa_text.splitlines()
    assert len(after_sa) == len(before_sa)
    assert [(b, a) for b, a in zip(before_sa, after_sa) if b != a] == [
        ("set: charset", "set: grpset"),
        ("order: 04", "order: 02"),
    ]
    assert "## Workflow history" not in after_sa_text


def test_e03_5_order_keeps_two_digit_nn_form(tmp_path: Path) -> None:
    """E-03 (5): `order:` keeps the destination filename's two-digit `NN` form (and 3-digit when >= 100)."""
    root = _init_repo(tmp_path)
    _seed_doc(
        root,
        "20260701-charset-05-ch0009-order-mv.notes.md",
        id6="ch0009",
        order="05",
        status=None,
    )
    rc, out, err = _run_cli(
        ["rename", "research", "ch0009", "--order", "1", "--apply", "--dir", str(root)]
    )
    assert rc == 0, f"rename research --order 1 failed: {out}\n{err}"

    dst1 = _find_by_id6(root, "ch0009")
    assert dst1.name == "20260701-charset-01-ch0009-order-mv.notes.md"
    fm1 = _meta.read_text(
        dst1.read_text(encoding="utf-8"), record_type="research"
    ).fields
    assert fm1
    assert fm1["order"] == "01"
    assert "order: 01" in dst1.read_text(encoding="utf-8").splitlines()

    rc2, out2, err2 = _run_cli(
        [
            "rename",
            "research",
            "ch0009",
            "--order",
            "129",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc2 == 0, f"rename research --order 129 failed: {out2}\n{err2}"

    dst2 = _find_by_id6(root, "ch0009")
    assert dst2.name == "20260701-charset-129-ch0009-order-mv.notes.md"
    fm2 = _meta.read_text(
        dst2.read_text(encoding="utf-8"), record_type="research"
    ).fields
    assert fm2
    assert fm2["order"] == "129"
    assert "order: 129" in dst2.read_text(encoding="utf-8").splitlines()

    _seed_doc(
        root,
        "20260701-charset-06-ch0010-order-sa.notes.md",
        id6="ch0010",
        order="06",
        status=None,
    )
    rc3, out3, err3 = _run_cli(
        [
            "research",
            "set-assign",
            "ch0010",
            "--set",
            "saset",
            "--order",
            "9",
            "--date",
            "20260825",
            "--apply",
            "--dir",
            str(root),
        ]
    )
    assert rc3 == 0, f"set-assign --start-order 9 failed: {out3}\n{err3}"

    dst3 = _find_by_id6(root, "ch0010")
    assert dst3.name == "20260825-saset-09-ch0010-order-sa.notes.md"
    fm3 = _meta.read_text(
        dst3.read_text(encoding="utf-8"), record_type="research"
    ).fields
    assert fm3
    assert fm3["order"] == "09"
    assert "order: 09" in dst3.read_text(encoding="utf-8").splitlines()
