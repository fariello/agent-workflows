"""Tests for research rename frontmatter updates and consistency.

Covers IPD ax8eg1 (backlog f7a2kc):
- Frontmatter set, order, kind, and model (conditional on name facet) updated in same transaction as rename.
- Prevents silent failure of INDEX generation.
- Preserves document body byte-for-byte even when body contains literal frontmatter keys.
- Preserves unrelated frontmatter keys and model provenance on facet-less names.
- Idempotent repeated regrouping.
- Works across both spellings of group (aw group research, aw research set-assign)
  and rename (aw rename research, aw research mv).
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess

import pytest

from agent_workflows import cli, research_contract as R


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Agent Tests"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "tests@example.com"], cwd=tmp_path, check=True
    )
    return tmp_path


def _seed_research_doc(
    repo_dir: Path,
    filename: str,
    *,
    id6: str = "k7m2xq",
    created: str = "20260901",
    set_id: str = "oldsetid",
    order: str = "03",
    topic: list[str] | None = None,
    model: str = "",
    kind: str = "notes",
    status: str = "todo",
    outcome: str = "none-yet",
    summary: str = "A demo doc",
    consumed_by: list[str] | None = None,
    body: str = "\n## Notes\nSome demo notes.\n",
) -> Path:
    rdir = repo_dir / ".aw" / "records" / "research" / "reference" / "202609"
    rdir.mkdir(parents=True, exist_ok=True)
    path = rdir / filename

    topic_str = f"[{', '.join(topic)}]" if topic is not None else "[demo]"
    consumed_str = f"[{', '.join(consumed_by)}]" if consumed_by is not None else "[]"
    model_str = f" {model}" if model else ""

    content = (
        "---\n"
        f"id: {id6}\n"
        f"created: {created}\n"
        f"set: {set_id}\n"
        f"order: {order}\n"
        f"topic: {topic_str}\n"
        f"model:{model_str}\n"
        f"kind: {kind}\n"
        f"status: {status}\n"
        f"outcome: {outcome}\n"
        f"summary: {summary}\n"
        f"consumed-by: {consumed_str}\n"
        "---\n"
        f"{body}"
    )
    path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"seed {filename}", "-q"], cwd=repo_dir, check=True
    )
    return path


def _run_cli(args: list[str]) -> tuple[int, str, str]:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(args)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _find_doc_by_id6(repo_dir: Path, id6: str) -> Path:
    rdir = repo_dir / ".aw" / "records" / "research"
    matches = list(rdir.glob(f"**/*{id6}*.md"))
    assert len(matches) == 1, f"Expected 1 file matching id6 {id6}, found {matches}"
    return matches[0]


def test_regroup_updates_set_and_order_frontmatter(temp_git_repo: Path):
    """E-01(a): aw group research updates set: and order: in frontmatter to match destination filename."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
        set_id="oldsetid",
        order="03",
    )
    rc, out, err = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"group failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["set"] == "newsetid"
    assert fm["order"] == "01"


def test_mv_model_updates_model_frontmatter(temp_git_repo: Path):
    """E-01(b): aw research mv --model updates model: in frontmatter."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
        model="",
    )
    rc, out, err = _run_cli(
        [
            "research",
            "mv",
            "k7m2xq",
            "--model",
            "sonnet5high",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"mv --model failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["model"] == "sonnet5high"


def test_mv_kind_updates_kind_frontmatter(temp_git_repo: Path):
    """E-01(c): aw research mv --kind updates kind: in frontmatter."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
        kind="notes",
    )
    rc, out, err = _run_cli(
        [
            "research",
            "mv",
            "k7m2xq",
            "--kind",
            "findings",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"mv --kind failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["kind"] == "findings"


def test_regroup_preserves_generated_index_path_resolution(temp_git_repo: Path):
    """E-02: After a regroup, generated INDEX.json points to a path that exists on disk."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
    )
    rc_idx, out_idx, err_idx = _run_cli(
        ["index", "research", "--apply", "--dir", str(temp_git_repo)]
    )
    assert rc_idx == 0, f"index failed: {out_idx}\n{err_idx}"
    idx_path = temp_git_repo / ".aw" / "records" / "research" / "INDEX.json"
    assert idx_path.exists(), "INDEX.json should exist"

    rc, out, err = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"group failed: {out}\n{err}"

    idx_data = json.loads(idx_path.read_text(encoding="utf-8"))
    entries = [e for e in idx_data if e.get("id6") == "k7m2xq"]
    assert len(entries) == 1, f"Expected entry for k7m2xq in index: {idx_data}"
    rel_path = entries[0]["path"]
    target_file = temp_git_repo / ".aw" / "records" / "research" / rel_path
    assert (
        target_file.exists()
    ), f"Path {rel_path} recorded in INDEX.json does not exist on disk"


def test_alternate_spelling_research_set_assign(temp_git_repo: Path):
    """E-06(a): aw research set-assign updates set: and order: in frontmatter."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
        set_id="oldsetid",
        order="03",
    )
    rc, out, err = _run_cli(
        [
            "research",
            "set-assign",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"set-assign failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["set"] == "newsetid"
    assert fm["order"] == "01"


def test_alternate_spelling_rename_research(temp_git_repo: Path):
    """E-06(b): aw rename research reconciles frontmatter order: to match destination filename."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-01-k7m2xq-a-demo-doc.notes.md",
        order="03",
    )
    rc, out, err = _run_cli(
        [
            "rename",
            "research",
            "k7m2xq",
            "--slug",
            "renamed-slug",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"rename research failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["order"] == "01"


def test_body_preservation_with_literal_frontmatter_keys(temp_git_repo: Path):
    """E-05(a): Body containing literal set:, order:, model:, kind: lines is byte-preserved."""
    body_text = (
        "\n## Analysis Body\n"
        "Literal frontmatter keys in body that must not be changed:\n"
        "set: oldsetid\n"
        "order: 03\n"
        "model: sonnet5high\n"
        "kind: notes\n"
        "End of body.\n"
    )
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
        body=body_text,
    )
    rc, out, err = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"group failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    text = dst.read_text(encoding="utf-8")
    assert text.endswith(body_text), "Body region must be byte-for-byte preserved"
    fm = R.parse_frontmatter(text)
    assert fm is not None
    assert fm["set"] == "newsetid"
    assert fm["order"] == "01"


def test_regroup_frontmatter_write_idempotence(temp_git_repo: Path):
    """E-05(b): Regrouping an already-consistent document is idempotent and leaves file byte-identical."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
    )
    rc1, out1, err1 = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc1 == 0, f"first group failed: {out1}\n{err1}"
    dst1 = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    content1 = dst1.read_bytes()

    rc2, out2, err2 = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc2 == 0, f"second group failed: {out2}\n{err2}"
    dst2 = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    content2 = dst2.read_bytes()

    assert (
        content1 == content2
    ), "Repeated identical regroup must leave content byte-identical"


def test_unrelated_frontmatter_keys_are_unmutated(temp_git_repo: Path):
    """E-05(c): Unrelated frontmatter keys (id, created, topic, status, outcome, summary, consumed-by) are untouched."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
        id6="k7m2xq",
        created="20260901",
        topic=["testing", "guards"],
        status="todo",
        outcome="none-yet",
        summary="Detailed custom summary for regression test",
        consumed_by=["plan-ref-123456"],
    )
    rc, out, err = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"group failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["id"] == "k7m2xq"
    assert fm["created"] == "20260901"
    assert fm["topic"] == ["testing", "guards"]
    assert fm["status"] == "todo"
    assert fm["outcome"] == "none-yet"
    assert fm["summary"] == "Detailed custom summary for regression test"
    assert fm["consumed-by"] == ["plan-ref-123456"]


def test_gate_agreement_on_all_four_fields(temp_git_repo: Path):
    """E-05(d): aw research index --check passes and INDEX.json records set_id, order, model, kind matching new name."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.sonnet5high.notes.md",
        model="sonnet5high",
        kind="notes",
    )
    rc, out, err = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"group failed: {out}\n{err}"

    # Validate gate passes
    rc_chk, out_chk, err_chk = _run_cli(
        ["index", "research", "--check", "--dir", str(temp_git_repo)]
    )
    assert rc_chk == 0, f"index --check failed: {out_chk}\n{err_chk}"

    # Validate generated INDEX.json fields
    idx_path = temp_git_repo / ".aw" / "records" / "research" / "INDEX.json"
    idx_data = json.loads(idx_path.read_text(encoding="utf-8"))
    entries = [e for e in idx_data if e.get("id6") == "k7m2xq"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["set_id"] == "newsetid"
    assert entry["order"] == "01"
    assert entry["model"] == "sonnet5high"
    assert entry["kind"] == "notes"


def test_model_provenance_preserved_on_facetless_name(temp_git_repo: Path):
    """E-05(e): A record with no model facet in filename retains populated model: in frontmatter on regroup."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.notes.md",
        model="sonnet5high",
    )
    rc, out, err = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"group failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["model"] == "sonnet5high"


def test_model_and_kind_preserved_through_mv_slug(temp_git_repo: Path):
    """E-05(f): aw research mv --slug preserves existing model and kind in frontmatter."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.sonnet5high.notes.md",
        model="sonnet5high",
        kind="notes",
    )
    rc, out, err = _run_cli(
        [
            "research",
            "mv",
            "k7m2xq",
            "--slug",
            "updated-slug",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"mv --slug failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["model"] == "sonnet5high"
    assert fm["kind"] == "notes"


def test_tier_independence_sibling_interaction(temp_git_repo: Path):
    """E-05(g): Disagreement between initial filename NN and frontmatter order resolves to destination name."""
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-01-k7m2xq-a-demo-doc.notes.md",
        order="03",
    )
    rc, out, err = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "2",
            "--apply",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc == 0, f"group failed: {out}\n{err}"
    dst = _find_doc_by_id6(temp_git_repo, "k7m2xq")
    parsed, _ = R.parse_name(dst.name)
    assert parsed is not None
    assert parsed.order == "02"
    fm = R.parse_frontmatter(dst.read_text(encoding="utf-8"))
    assert fm is not None
    assert fm["order"] == "02"


def test_preview_announces_frontmatter_metadata_write(temp_git_repo: Path):
    """E-04: Dry run announces metadata write with exactly the fields that apply will write."""
    # Case A: with model facet in destination name
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-k7m2xq-a-demo-doc.sonnet5high.notes.md",
        model="sonnet5high",
    )
    rc1, out1, err1 = _run_cli(
        [
            "group",
            "research",
            "k7m2xq",
            "--set",
            "newsetid",
            "--order",
            "1",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc1 == 0, f"preview failed: {out1}\n{err1}"
    assert "--- would set metadata set/order/model/kind in " in out1

    # Case B: without model facet in destination name
    _seed_research_doc(
        temp_git_repo,
        "20260901-oldsetid-03-ab12cd-a-demo-doc.notes.md",
        id6="ab12cd",
        model="",
    )
    rc2, out2, err2 = _run_cli(
        [
            "group",
            "research",
            "ab12cd",
            "--set",
            "newsetid",
            "--order",
            "2",
            "--dir",
            str(temp_git_repo),
        ]
    )
    assert rc2 == 0, f"preview failed: {out2}\n{err2}"
    assert "--- would set metadata set/order/kind in " in out2
