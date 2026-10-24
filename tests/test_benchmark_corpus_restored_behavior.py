"""Behavioral tests for benchmark_corpus load_corpus and SeededTask.workspace_seed_path.

Restores behavioral test coverage recorded in backlog item 3hurk1, findings wo21z5
group 12, following sibling plan 78g6ic which restored tests/test_benchmark_corpus.py.
Pins the observable contract of load_corpus (root validation, seed discovery, deterministic
order, error propagation) and of SeededTask.workspace_seed_path (exact executor-visible
subtree and separation from ground_truth.json) in the routine core tier.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agent_workflows import benchmark_corpus as corpus

pytestmark = pytest.mark.core

FIXTURE_CORPUS = Path(__file__).resolve().parent / "benchmark_fixtures" / "corpus"


def _copy_seed(name: str, dest: Path) -> Path:
    """Copy one fixture seed directory into dest."""
    shutil.copytree(FIXTURE_CORPUS / name, dest)
    return dest


# ======================================================================================
# E-02: load_corpus behavioral tests
# ======================================================================================


def test_load_corpus_case_a_nonexistent_root_raises(tmp_path: Path) -> None:
    """(a) Nonexistent root raises CorpusError matching 'corpus root is not a directory'."""
    nonexistent = tmp_path / "does_not_exist"
    with pytest.raises(corpus.CorpusError, match="corpus root is not a directory"):
        corpus.load_corpus(nonexistent)


def test_load_corpus_case_b_file_root_raises(tmp_path: Path) -> None:
    """(b) Regular file passed as corpus root raises CorpusError matching 'corpus root is not a directory'."""
    file_root = tmp_path / "not_a_dir.txt"
    file_root.write_text("hello", encoding="utf-8")
    with pytest.raises(corpus.CorpusError, match="corpus root is not a directory"):
        corpus.load_corpus(file_root)


def test_load_corpus_case_c_empty_directory_returns_empty(tmp_path: Path) -> None:
    """(c) Empty directory as corpus root returns empty list."""
    empty_root = tmp_path / "empty_corpus"
    empty_root.mkdir()
    assert corpus.load_corpus(empty_root) == []


def test_load_corpus_case_d_skips_non_seed_children(tmp_path: Path) -> None:
    """(d) Non-seed children (subdirs without task.json, loose files) are skipped."""
    root = tmp_path / "corpus_with_non_seeds"
    root.mkdir()
    subdir_no_task = root / "subdir_without_task"
    subdir_no_task.mkdir()
    (subdir_no_task / "random_file.txt").write_text("data", encoding="utf-8")
    (root / "loose.json").write_text("{}", encoding="utf-8")
    assert corpus.load_corpus(root) == []


def test_load_corpus_case_e_name_ordered_characterization_qtd3lj(
    tmp_path: Path,
) -> None:
    """(e) Seeds returned in directory name order, not task_class order.

    Characterization test for current name-based sort order (which contradicts
    the docstring claiming (task_class, seed_id) order). Backlog qtd3lj owns
    deciding the intended contract.
    """
    root = tmp_path / "ordered_corpus"
    root.mkdir()
    _copy_seed("simple_commands", root / "a_dir")
    _copy_seed("migration", root / "b_dir")
    tasks = corpus.load_corpus(root)
    assert len(tasks) == 2
    assert [t.seed_path.name for t in tasks] == ["a_dir", "b_dir"]
    assert [t.task_class for t in tasks] == ["simple_commands", "migration"]


def test_load_corpus_case_f_propagates_malformed_seed_error(tmp_path: Path) -> None:
    """(f) Malformed seed raises CorpusError and is propagated rather than skipped."""
    root = tmp_path / "corpus_with_bad_seed"
    root.mkdir()
    _copy_seed("simple_commands", root / "a_dir")
    _copy_seed("migration", root / "b_dir")
    bad_dir = root / "zz_bad"
    bad_dir.mkdir()
    (bad_dir / corpus.TASK_FILENAME).write_text(
        json.dumps({"task_class": "nope", "seed_id": "x"}), encoding="utf-8"
    )
    with pytest.raises(corpus.CorpusError, match="unknown task_class 'nope'"):
        corpus.load_corpus(root)


def test_load_corpus_case_g_str_root_fixture_corpus() -> None:
    """(g) String path accepted as root, returning all 7 task classes with Path seed_paths."""
    tasks = corpus.load_corpus(str(FIXTURE_CORPUS))
    assert len(tasks) == 7
    assert {t.task_class for t in tasks} == set(corpus.TASK_CLASSES)
    assert all(isinstance(t.seed_path, Path) for t in tasks)


# ======================================================================================
# E-03: SeededTask.workspace_seed_path behavioral tests
# ======================================================================================


def test_workspace_seed_path_fixture_tasks() -> None:
    """Verify workspace_seed_path invariants across all checked-in fixture tasks."""
    tasks = corpus.load_corpus(FIXTURE_CORPUS)
    assert len(tasks) == 7
    for t in tasks:
        ws = t.workspace_seed_path()
        assert ws == t.seed_path / corpus.WORKSPACE_DIRNAME
        assert ws.is_dir()
        assert ws != t.seed_path
        assert list(ws.rglob(corpus.GROUND_TRUTH_FILENAME)) == []
        assert (t.seed_path / corpus.GROUND_TRUTH_FILENAME).is_file()


def test_workspace_seed_path_pure_computation_nonexistent_dir(tmp_path: Path) -> None:
    """workspace_seed_path is a pure path computation that does not access the filesystem."""
    seed_dir = tmp_path / "nonexistent_seed"
    assert not seed_dir.exists()
    t = corpus.SeededTask("simple_commands", "s", {}, seed_dir)
    assert t.workspace_seed_path() == seed_dir / corpus.WORKSPACE_DIRNAME
