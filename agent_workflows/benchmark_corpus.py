"""Seeded benchmark task corpus: deterministic repos with hidden ground truth.

awoptimize Order 12 (`1jfxvo`) E-02.

This module loads and materializes small SEEDED task repositories, one per agent-behavior task class:

    simple_commands, interactive_planning, complex_review, multi_step_implementation,
    migration, failure_recovery, orchestration.

Each seeded task is a directory tree of files. A task carries HIDDEN ground truth (the reference the
scorer needs) that is kept OUT of the executor-visible tree: the executor materializes only the
``workspace/`` subtree of a seed, while the ``ground_truth.json`` sits beside it and is never copied
into the workspace. :func:`materialize_task` refuses to expose ground truth to an executor path, and
:func:`reset_task` produces a byte-identical workspace every time (identical content hash), giving a
deterministic setup/teardown.

The scorer's ground truth is a plain, independently reviewable JSON document (no code, no eval).

Pure + stdlib-only (D138; D139: no runtime YAML). The only filesystem effects are reading the checked-in
seed tree and writing a fresh workspace copy on materialize/reset (both fully deterministic).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Sequence, Tuple

CORPUS_SCHEMA_VERSION = 1

# The seven agent-behavior task classes this corpus represents.
TASK_CLASSES: Tuple[str, ...] = (
    "simple_commands",
    "interactive_planning",
    "complex_review",
    "multi_step_implementation",
    "migration",
    "failure_recovery",
    "orchestration",
)

# The subtree name inside a seed that is the ONLY thing an executor may see.
WORKSPACE_DIRNAME = "workspace"
# The hidden ground-truth file name that sits beside the workspace and is NEVER exposed to executors.
GROUND_TRUTH_FILENAME = "ground_truth.json"
# The task descriptor (executor-visible prompt + metadata).
TASK_FILENAME = "task.json"


class CorpusError(ValueError):
    """Raised on a malformed seed tree or an attempt to expose hidden ground truth."""


class SeededTask(NamedTuple):
    """A loaded seeded task: its class, seed id, executor-visible descriptor, and the SEED path.

    The hidden ground truth is intentionally NOT a field here: it is loaded separately via
    :func:`load_ground_truth`, guarded so that executor-facing code paths cannot reach it.
    """

    task_class: str
    seed_id: str
    task: Dict[
        str, Any
    ]  # executor-visible descriptor (prompt, allowed tools, expected artifacts)
    seed_path: Path

    def workspace_seed_path(self) -> Path:
        return self.seed_path / WORKSPACE_DIRNAME

    def ground_truth_path(self) -> Path:
        return self.seed_path / GROUND_TRUTH_FILENAME


# ---- deterministic hashing ------------------------------------------------------------------------


def hash_tree(root: Path) -> str:
    """Compute a deterministic SHA-256 over a directory tree: sorted (relpath, mode-bit, content-hash)
    triples. Two trees with identical relative paths + file bytes hash identically, independent of
    filesystem ordering or mtimes. Directories are represented by their (sorted) contents."""
    root = Path(root)
    if not root.exists():
        raise CorpusError("cannot hash a nonexistent tree: {0}".format(root))
    entries: List[Tuple[str, str]] = []
    for p in sorted(
        root.rglob("*"), key=lambda x: str(x.relative_to(root)).replace("\\", "/")
    ):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if p.is_dir():
            entries.append((rel + "/", "dir"))
        elif p.is_file():
            content_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            # executable bit is the only mode facet we track (deterministic across checkouts)
            exe = "x" if (p.stat().st_mode & 0o111) else "-"
            entries.append((rel, "{0}:{1}".format(exe, content_hash)))
    blob = json.dumps(
        entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---- loading the corpus ---------------------------------------------------------------------------


def load_task(seed_path: Path) -> SeededTask:
    """Load a seeded task from its seed directory. Validates the task class + presence of the
    executor-visible descriptor and the hidden ground truth, WITHOUT loading the ground truth into any
    executor-visible structure."""
    seed_path = Path(seed_path)
    task_file = seed_path / TASK_FILENAME
    if not task_file.is_file():
        raise CorpusError("seed missing {0}: {1}".format(TASK_FILENAME, seed_path))
    task = json.loads(task_file.read_text(encoding="utf-8"))
    task_class = task.get("task_class")
    if task_class not in TASK_CLASSES:
        raise CorpusError(
            "seed {0} has unknown task_class {1!r}".format(seed_path, task_class)
        )
    seed_id = task.get("seed_id")
    if not seed_id:
        raise CorpusError("seed {0} missing seed_id".format(seed_path))
    if not (seed_path / GROUND_TRUTH_FILENAME).is_file():
        raise CorpusError(
            "seed {0} missing hidden ground truth {1}".format(
                seed_path, GROUND_TRUTH_FILENAME
            )
        )
    if not (seed_path / WORKSPACE_DIRNAME).is_dir():
        raise CorpusError(
            "seed {0} missing {1}/ subtree".format(seed_path, WORKSPACE_DIRNAME)
        )
    return SeededTask(
        task_class=task_class,
        seed_id=seed_id,
        task=task,
        seed_path=seed_path,
    )


def load_corpus(corpus_root: Path) -> List[SeededTask]:
    """Load every seeded task under a corpus root. A corpus root contains one subdirectory per seed
    (each with a task.json). Returns tasks sorted by (task_class, seed_id) for determinism."""
    corpus_root = Path(corpus_root)
    if not corpus_root.is_dir():
        raise CorpusError("corpus root is not a directory: {0}".format(corpus_root))
    tasks: List[SeededTask] = []
    for child in sorted(corpus_root.iterdir(), key=lambda p: p.name):
        if child.is_dir() and (child / TASK_FILENAME).is_file():
            tasks.append(load_task(child))
    return tasks


def task_classes_present(tasks: Sequence[SeededTask]) -> Tuple[str, ...]:
    """The distinct task classes covered by a set of loaded tasks (sorted)."""
    return tuple(sorted({t.task_class for t in tasks}))


# ---- hidden ground truth --------------------------------------------------------------------------


def load_ground_truth(task: SeededTask) -> Dict[str, Any]:
    """Load a task's HIDDEN ground truth. This is the SCORER-ONLY path. It is a plain JSON document
    (independently reviewable). Executor-facing code must never call this."""
    gt_path = task.ground_truth_path()
    if not gt_path.is_file():
        raise CorpusError("ground truth missing for {0}".format(task.seed_id))
    return json.loads(gt_path.read_text(encoding="utf-8"))


def is_ground_truth_accessible(workspace: Path) -> bool:
    """Return True if a materialized executor workspace CONTAINS the hidden ground-truth file anywhere.
    A correct materialization always returns False (the truth was never copied into the workspace)."""
    workspace = Path(workspace)
    if not workspace.exists():
        return False
    for p in workspace.rglob("*"):
        if p.name == GROUND_TRUTH_FILENAME:
            return True
    return False


# ---- deterministic materialization / reset --------------------------------------------------------


def materialize_task(task: SeededTask, dest: Path) -> Path:
    """Materialize ONLY the executor-visible workspace subtree of a seed into ``dest``. The hidden
    ground truth is never copied. Returns the destination workspace path. Deterministic: repeated calls
    produce byte-identical trees (identical hash_tree)."""
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    src = task.workspace_seed_path()
    if not src.is_dir():
        raise CorpusError("seed workspace missing: {0}".format(src))
    # copy2 preserves the executable bit; we deliberately do NOT preserve mtimes in the hash.
    shutil.copytree(src, dest)
    # Guard: the workspace must never contain the ground-truth file.
    if is_ground_truth_accessible(dest):
        raise CorpusError(
            "materialized workspace leaks hidden ground truth: {0}".format(dest)
        )
    return dest


def reset_task(task: SeededTask, dest: Path) -> str:
    """Reset an executor workspace to the pristine seed state and return its deterministic content
    hash. A DETERMINISTIC RESET: two resets of the same seed yield identical hashes."""
    materialize_task(task, dest)
    return hash_tree(dest)


def seed_workspace_hash(task: SeededTask) -> str:
    """The deterministic hash of a seed's pristine workspace subtree (the reset invariant)."""
    return hash_tree(task.workspace_seed_path())
