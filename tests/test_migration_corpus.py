"""Behavioral contract tests for the five-shape migration fixture corpus."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from agent_workflows import project_context
from tests import support
from tests.migration_corpus import EXPECTED, SHAPES, UNCLASSIFIABLE

pytestmark = pytest.mark.core

_COMPANION_PREFIX = "companion:"
_SIDECAR_SETTER_PATTERNS = (
    "(aw set)",
    "aw ipd set",
    "aw backlog set",
    "aw specs set",
    "aw spec set",
    "(aw backlog)",
    "(aw specs)",
)


def _git_clean_env() -> dict[str, str]:
    return support.clean_git_env()


def _git_ls_files(repo: Path) -> set[str]:
    proc = support.git(repo, "ls-files", "-z", env=_git_clean_env())
    assert proc.returncode == 0, proc.stderr
    return {entry for entry in proc.stdout.split("\0") if entry}


def _git_status_porcelain(repo: Path) -> str:
    proc = support.git(repo, "status", "--porcelain", env=_git_clean_env())
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _git_head_tree(repo: Path) -> str:
    proc = support.git(repo, "rev-parse", "HEAD^{tree}", env=_git_clean_env())
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _leading_bullet_block(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            break
        lines.append(line)
    return "\n".join(lines)


def _record_file(shape: str, root: Path, rec_path: str) -> Path:
    if shape == "companion_backend":
        assert rec_path.startswith(_COMPANION_PREFIX)
        rel = rec_path[len(_COMPANION_PREFIX) :]
        return root.parent / "companion" / rel
    return root / rec_path


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_contract_1_git_clean_and_ls_files(shape: str, tmp_path: Path) -> None:
    """Every built repo has empty porcelain status and exact committed file set."""
    dest = tmp_path / "fixture"
    dest.mkdir()
    root = SHAPES[shape](dest)

    assert _git_status_porcelain(root) == ""

    expected_paths = {rec.path for rec in EXPECTED[shape]} | set(UNCLASSIFIABLE[shape])
    if shape == "no_sidecar":
        expected_paths.add(".aw/config/project.json")

    if shape == "companion_backend":
        companion_root = dest / "companion"
        assert _git_status_porcelain(companion_root) == ""
        assert _git_ls_files(root) == {".aw/config/project.json", ".gitignore"}
        companion_expected = {p[len(_COMPANION_PREFIX) :] for p in expected_paths}
        assert _git_ls_files(companion_root) == companion_expected
    else:
        assert _git_ls_files(root) == expected_paths


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_contract_2_expected_metadata_bullets(shape: str, tmp_path: Path) -> None:
    """Every EXPECTED record carries - Id: and - Status: iff those fields are non-None."""
    dest = tmp_path / "fixture"
    dest.mkdir()
    root = SHAPES[shape](dest)

    for rec in EXPECTED[shape]:
        fpath = _record_file(shape, root, rec.path)
        assert fpath.is_file(), f"Missing expected record: {fpath}"
        block = _leading_bullet_block(fpath.read_text(encoding="utf-8"))
        id_matches = re.findall(r"(?m)^- Id:\s*(\S+)\s*$", block)
        status_matches = re.findall(r"(?m)^- Status:\s*(\S+)\s*$", block)

        if rec.id6 is None:
            assert id_matches == [], f"{rec.path} unexpectedly has - Id: {id_matches}"
        else:
            assert id_matches == [rec.id6], f"{rec.path} id mismatch: {id_matches}"

        if rec.status is None:
            assert (
                status_matches == []
            ), f"{rec.path} unexpectedly has - Status: {status_matches}"
        else:
            assert status_matches == [
                rec.status
            ], f"{rec.path} status mismatch: {status_matches}"


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_contract_3_shape_content_invariants(shape: str, tmp_path: Path) -> None:
    """Each shape has the exact structural files and prose/header shape defined by C12."""
    dest = tmp_path / "fixture"
    dest.mkdir()
    root = SHAPES[shape](dest)

    if shape == "legacy_agents_layout":
        legacy_plan = root / ".agents/plans/executed/20260705-1015-01-legacy-setup.md"
        assert legacy_plan.is_file()
        assert (root / ".agents/plans/INDEX.md").is_file()
        assert (root / ".agents/plans/README.md").is_file()
        assert (root / ".agents/workflows/demo/demo.md").is_file()
    elif shape == "mixed_layout":
        a_plan = root / ".agents/plans/executed/20260710-beta-01-qa1z03-shared-plan.md"
        b_plan = (
            root / ".aw/records/plans/executed/20260710-beta-01-qa1z03-shared-plan.md"
        )
        assert a_plan.read_bytes() == b_plan.read_bytes()
    elif shape == "idless_prose":
        prose_plan = root / ".aw/records/plans/executed/20260715-prose-migration-ipd.md"
        text = prose_plan.read_text(encoding="utf-8")
        first_line = text.splitlines()[0]
        assert first_line.startswith("# Implementation Plan Document (IPD) - ")
        assert not any(
            line.startswith("- Id:") or line.startswith("- Status:")
            for line in text.splitlines()
        )
        assert (root / ".aw/records/notes/scratch.md").is_file()
    elif shape == "no_sidecar":
        cfg = json.loads((root / ".aw/config/project.json").read_text(encoding="utf-8"))
        assert cfg == {"schema_version": 2, "records_backend": "repository"}
    elif shape == "companion_backend":
        cfg = json.loads((root / ".aw/config/project.json").read_text(encoding="utf-8"))
        assert cfg == {"records_backend": "companion"}
        assert (
            ".aw/config/local.json"
            in (root / ".gitignore").read_text(encoding="utf-8").splitlines()
        )


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_contract_4_layout_sidecar_and_backend(
    shape: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify layout boundaries, no-sidecar history rule, and companion backend resolution."""
    dest = tmp_path / "fixture"
    dest.mkdir()
    root = SHAPES[shape](dest)

    if shape == "legacy_agents_layout":
        assert not (root / ".agents/skills").exists()
        assert not (root / ".aw").exists()
    elif shape == "mixed_layout":
        assert (root / ".agents").is_dir()
        assert (root / ".aw/records").is_dir()
    elif shape == "idless_prose":
        assert not (root / ".agents").exists()
        assert (root / ".aw/records").is_dir()
    elif shape == "no_sidecar":
        assert not (root / ".aw/records/history.jsonl").exists()
        for rec in EXPECTED[shape]:
            text = (root / rec.path).read_text(encoding="utf-8")
            assert "## Workflow history" in text
            lowered = text.lower()
            for token in _SIDECAR_SETTER_PATTERNS:
                assert token not in lowered
    elif shape == "companion_backend":
        local_rel = ".aw/config/local.json"
        unmatch = support.git(
            root, "ls-files", "--error-unmatch", local_rel, env=_git_clean_env()
        )
        assert unmatch.returncode != 0
        ignored = support.git(
            root,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            env=_git_clean_env(),
        )
        assert ignored.returncode == 0
        assert local_rel in ignored.stdout.splitlines()

        aw_home = tmp_path / "aw_home"
        aw_home.mkdir()
        monkeypatch.setenv("AW_HOME", str(aw_home))
        resolved = project_context.project_records_dir(root)
        assert resolved.resolve() == (dest / "companion" / "records").resolve()


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_contract_5_deterministic_tree_ids(shape: str, tmp_path: Path) -> None:
    """Two builds into separate empty directories yield identical ls-files and tree ids."""
    dest_a = tmp_path / "build_a"
    dest_b = tmp_path / "build_b"
    dest_a.mkdir()
    dest_b.mkdir()

    root_a = SHAPES[shape](dest_a)
    root_b = SHAPES[shape](dest_b)

    assert _git_ls_files(root_a) == _git_ls_files(root_b)
    assert _git_head_tree(root_a) == _git_head_tree(root_b)

    if shape == "companion_backend":
        comp_a = dest_a / "companion"
        comp_b = dest_b / "companion"
        assert _git_ls_files(comp_a) == _git_ls_files(comp_b)
        assert _git_head_tree(comp_a) == _git_head_tree(comp_b)


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_refuse_non_empty_dest(shape: str, tmp_path: Path) -> None:
    """Builders raise ValueError and leave dest untouched when dest is not empty."""
    dest = tmp_path / "non_empty"
    dest.mkdir()
    sentinel = dest / "keep.txt"
    sentinel.write_text("unchanged", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        SHAPES[shape](dest)

    assert [p.name for p in dest.iterdir()] == ["keep.txt"]
    assert sentinel.read_text(encoding="utf-8") == "unchanged"


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_refuse_relative_dest(
    shape: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Builders raise ValueError and write nothing when dest is relative."""
    rel_dir = tmp_path / "rel_empty"
    rel_dir.mkdir()
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="absolute"):
        SHAPES[shape](Path("rel_empty"))

    assert list(rel_dir.iterdir()) == []


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_refuse_inside_git_worktree_dest(shape: str, tmp_path: Path) -> None:
    """Builders raise ValueError and write nothing when dest lies inside a git work tree."""
    outer = support.init_repo(tmp_path / "outer")
    dest = outer / "empty_subdir"
    dest.mkdir()

    with pytest.raises(ValueError, match="work tree"):
        SHAPES[shape](dest)

    assert list(dest.iterdir()) == []
