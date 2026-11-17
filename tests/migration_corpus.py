"""Five-shape anonymized migration fixture corpus for spec 4sd62s C12 and AC-42.

Each builder writes one committed git repository (or target + companion pair) of a
recorded historical toolkit layout into a caller-supplied empty directory outside any
git work tree. All titles, prose, and ``id6`` values are synthetic.

Structural evidence per shape (naming no private repository):

- ``legacy_agents_layout`` (shape a): surveyed from public history in this repository at
  ``b928f3aaa`` (2026-08-09) via ``git ls-tree -r --name-only b928f3aaa -- .agents``:
  491 entries under ``.agents/`` including 129 executed plans and 14 pending plans
  (plans carrying ``- Id:`` and ``- Status:``), 11 specs under ``.agents/docs/specs/``
  (0 with ``- Id:``, 11 with ``- Status:``), 80 research ``.md`` files excluding
  ``README``/``INDEX``/``STATUS`` under ``.agents/docs/research/`` (0 with ``- Id:``, 1
  with ``- Status:``), 8 walkthroughs (neither bullet), ``.agents/workflows/``, and no
  ``.agents/backlog/``.
- ``mixed_layout`` (shape b): surveyed from public history in this repository at
  ``f296f6f40`` (2026-08-17) via ``git ls-tree -r --name-only f296f6f40 -- .agents``
  (564 entries, 520 ``.md`` files) and
  ``git ls-tree -r --name-only f296f6f40 -- .aw/records`` (410 entries, 380 ``.md``
  files), with 164 overlapping ``plans/executed`` basenames (163 byte-identical
  ``.md`` plans plus ``.gitkeep``), 30 backlog entries in each tree, and 29 legacy
  timestamp names remaining under ``.agents/``.
- ``idless_prose`` (shape c): derived from ``g5hpbb`` F-03 (measured on a private
  repository, quoted here with no repository name or path): a tracked executed plan
  opening ``# Implementation Plan Document (IPD) - <title>`` with prose only and no
  ``- Id:`` or ``- Status:`` metadata bullets, paired with an unclassifiable ``.md``
  note under ``.aw/records/notes/``.
- ``no_sidecar`` (shape d): derived from ``git log --diff-filter=A --
  agent_workflows/record_history.py`` (sidecar writer first landed ``c3bff2528``,
  2026-08-19) and ``.aw/.gitignore`` line ``records/history.jsonl`` (which keeps the
  sidecar untracked across clones), so repositories created earlier or freshly cloned
  with ``- Id:``/``- Status:`` records and non-setter history carry no sidecar.
- ``companion_backend`` (shape e): constructed from
  ``project_context.project_records_dir`` and
  ``tests/test_records_root_accessor.py::test_accessor_companion``; no
  companion-backend repository was surveyed (``9vf2iv`` OQ-01).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from tests import support

_FIXED_GIT_DATE = "2026-01-15T12:00:00Z"


@dataclass(frozen=True)
class CorpusRecord:
    """Expected metadata record written by a corpus builder."""

    path: str
    record_type: str
    id6: str | None
    status: str | None


def _validate_dest(dest: Path) -> Path:
    """Validate that ``dest`` is an absolute, existing, empty dir outside any git tree."""
    dest_path = Path(dest)
    if not dest_path.is_absolute():
        raise ValueError(f"dest must be an absolute path: {dest}")
    if not dest_path.exists() or not dest_path.is_dir():
        raise ValueError(f"dest must be an existing directory: {dest}")
    if any(dest_path.iterdir()):
        raise ValueError(f"dest must be an empty directory: {dest}")

    probe = subprocess.run(
        ["git", "-C", str(dest_path), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
        env=support.clean_git_env(),
    )
    if probe.returncode == 0:
        raise ValueError(f"dest must lie outside every git work tree: {dest}")
    return dest_path


def _write_files(root: Path, files: dict[str, str]) -> list[str]:
    """Write ``files`` (mapping repo-relative POSIX path to UTF-8 text) under ``root``."""
    rel_paths: list[str] = []
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        rel_paths.append(rel)
    return rel_paths


def _commit_repo(root: Path, rel_paths: Sequence[str], message: str) -> None:
    """Stage ``rel_paths`` and commit with fixed deterministic author/committer dates."""
    env = support.clean_git_env()
    env["GIT_AUTHOR_DATE"] = _FIXED_GIT_DATE
    env["GIT_COMMITTER_DATE"] = _FIXED_GIT_DATE

    add_proc = support.git(root, "add", "--", *rel_paths, env=env)
    if add_proc.returncode != 0:
        raise RuntimeError(
            f"git add failed at {root}: {add_proc.stderr.strip() or add_proc.stdout.strip()}"
        )

    commit_proc = support.git(root, "commit", "-m", message, "-q", env=env)
    if commit_proc.returncode != 0:
        raise RuntimeError(
            f"git commit failed at {root}: {commit_proc.stderr.strip() or commit_proc.stdout.strip()}"
        )


def _init_and_commit(root: Path, files: dict[str, str], message: str) -> Path:
    """Initialize a deterministic git repository at ``root`` and commit ``files``."""
    support.init_repo(root)
    rel_paths = _write_files(root, files)
    _commit_repo(root, rel_paths, message)
    return root


def legacy_agents_layout(dest: Path) -> Path:
    """Build shape (a): legacy ``.agents/`` layout without ``.agents/skills/``."""
    root = _validate_dest(dest)
    files = {
        ".agents/plans/pending/20260701-alpha-01-qa1z01-first-pending-plan.md": (
            "# IPD: Synthetic pending plan\n\n"
            "- Date: 2026-07-01\n"
            "- Kind: child\n"
            "- Set: alpha\n"
            "- Order: 01\n"
            "- Status: to-review\n"
            "- Id: qa1z01\n\n"
            "## Goal\n\n"
            "Synthetic pending plan for the legacy layout fixture.\n"
        ),
        ".agents/plans/executed/20260701-alpha-00-qa1z02-alpha-orchestrator.md": (
            "# IPD: Synthetic executed orchestrator\n\n"
            "- Date: 2026-07-01\n"
            "- Kind: orchestrator\n"
            "- Set: alpha\n"
            "- Order: 00\n"
            "- Status: executed\n"
            "- Id: qa1z02\n\n"
            "## Goal\n\n"
            "Synthetic executed orchestrator for the legacy layout fixture.\n"
        ),
        ".agents/plans/executed/20260705-1015-01-legacy-setup.md": (
            "# IPD: Synthetic legacy timestamp plan\n\n"
            "- Date: 2026-07-05\n"
            "- Kind: child\n"
            "- Status: executed\n\n"
            "## Goal\n\n"
            "Synthetic legacy timestamp plan carrying no Id bullet.\n"
        ),
        ".agents/docs/specs/20260706-0900-01-core-spec.spec.md": (
            "# Spec: Synthetic legacy spec\n\n"
            "- Date: 2026-07-06\n"
            "- Status: approved\n\n"
            "## Scope\n\n"
            "Synthetic spec under .agents/docs/specs carrying Status without Id.\n"
        ),
        ".agents/docs/research/20260708-survey-notes.md": (
            "# Synthetic Legacy Research Note\n\n"
            "Synthetic research note carrying neither Id nor Status bullets.\n"
        ),
        ".agents/workflows/demo/demo.md": (
            "# Demo Workflow\n\n"
            "Synthetic workflow file moved by the layout stage, not a record.\n"
        ),
        ".agents/plans/INDEX.md": (
            "# Plans Index\n\n" "Synthetic legacy plans index.\n"
        ),
        ".agents/plans/README.md": (
            "# Plans Directory\n\n" "Synthetic legacy plans README.\n"
        ),
    }
    return _init_and_commit(root, files, "corpus: legacy_agents_layout")


def mixed_layout(dest: Path) -> Path:
    """Build shape (b): mixed ``.agents/`` and ``.aw/records/`` layout with duplicate plan."""
    root = _validate_dest(dest)
    shared_plan = (
        "# IPD: Synthetic shared executed plan\n\n"
        "- Date: 2026-07-10\n"
        "- Kind: child\n"
        "- Set: beta\n"
        "- Order: 01\n"
        "- Status: executed\n"
        "- Id: qa1z03\n\n"
        "## Goal\n\n"
        "Synthetic executed plan present identically in both trees.\n"
    )
    files = {
        ".agents/plans/executed/20260710-beta-01-qa1z03-shared-plan.md": shared_plan,
        ".aw/records/plans/executed/20260710-beta-01-qa1z03-shared-plan.md": shared_plan,
        ".agents/backlog/open/20260815-qa1z04-01-qa1z04-legacy-backlog-item.md": (
            "# Backlog: Synthetic legacy backlog item\n\n"
            "- Id: qa1z04\n"
            "- Status: open\n"
            "- Set: qa1z04\n"
            "- Priority: medium\n"
            "- Kind: chore\n"
            "- Summary: Synthetic backlog item in legacy .agents/backlog/open.\n"
        ),
        ".aw/records/specs/draft/20260816-qa1z05-01-qa1z05-draft-spec.spec.md": (
            "# Spec: Synthetic draft spec\n\n"
            "- Date: 2026-08-16\n"
            "- Status: draft\n"
            "- Id: qa1z05\n"
            "- Set: beta\n\n"
            "## Scope\n\n"
            "Synthetic draft spec under .aw/records/specs/draft.\n"
        ),
    }
    return _init_and_commit(root, files, "corpus: mixed_layout")


def idless_prose(dest: Path) -> Path:
    """Build shape (c): ``.aw/records/`` prose plan with no metadata bullets plus note."""
    root = _validate_dest(dest)
    files = {
        ".aw/records/plans/executed/20260715-prose-migration-ipd.md": (
            "# Implementation Plan Document (IPD) - Synthetic Prose Plan\n\n"
            "## Summary\n\n"
            "Synthetic prose plan with no metadata bullets anywhere.\n"
        ),
        ".aw/records/notes/scratch.md": (
            "# Scratch Notes\n\n"
            "Synthetic unclassifiable markdown note left untouched by migration.\n"
        ),
    }
    return _init_and_commit(root, files, "corpus: idless_prose")


def no_sidecar(dest: Path) -> Path:
    """Build shape (d): repository backend with id-bearing records and no history sidecar."""
    root = _validate_dest(dest)
    files = {
        ".aw/config/project.json": (
            json.dumps({"schema_version": 2, "records_backend": "repository"}) + "\n"
        ),
        ".aw/records/specs/approved/20260820-delta-01-qa1z06-no-sidecar-spec.spec.md": (
            "# Spec: Synthetic no-sidecar spec\n\n"
            "- Date: 2026-08-20\n"
            "- Status: approved\n"
            "- Id: qa1z06\n"
            "- Set: delta\n"
            "- Scope: Synthetic spec authored without a history sidecar.\n\n"
            "## Workflow history\n"
            "- 2026-08-20 draft (author): created by hand\n"
            "- 2026-08-20 approved (maintainer): approved in review\n"
        ),
        ".aw/records/backlog/open/20260821-delta-01-qa1z07-no-sidecar-backlog.backlog.md": (
            "- Id: qa1z07\n"
            "- Status: open\n"
            "- Set: delta\n"
            "- Priority: medium\n"
            "- Work-Kind: chore\n"
            "- Summary: Synthetic backlog item without history sidecar\n\n"
            "## Workflow history\n"
            "- 2026-08-21 open (author): filed by hand\n"
        ),
    }
    return _init_and_commit(root, files, "corpus: no_sidecar")


def companion_backend(dest: Path) -> Path:
    """Build shape (e): target and companion repositories linked via ignored ``local.json``."""
    root = _validate_dest(dest)
    target = root / "target"
    companion = root / "companion"
    target.mkdir()
    companion.mkdir()

    target_files = {
        ".aw/config/project.json": json.dumps({"records_backend": "companion"}) + "\n",
        ".gitignore": ".aw/config/local.json\n",
    }
    _init_and_commit(target, target_files, "corpus: companion_backend target")

    # Written after commit and excluded by .gitignore so local absolute paths stay untracked.
    local_cfg = target / ".aw" / "config" / "local.json"
    local_cfg.write_text(
        json.dumps({"companion_dir": str(companion)}) + "\n",
        encoding="utf-8",
    )

    companion_files = {
        "records/plans/pending/20260825-epsilon-01-qa1z08-companion-plan.ipd.md": (
            "# IPD: Synthetic companion plan\n\n"
            "- Date: 2026-08-25\n"
            "- Kind: child\n"
            "- Set: epsilon\n"
            "- Order: 01\n"
            "- Status: approved\n"
            "- Id: qa1z08\n\n"
            "## Goal\n\n"
            "Synthetic pending plan stored in the companion repository.\n"
        ),
        "records/backlog/open/20260826-epsilon-01-qa1z09-companion-backlog.backlog.md": (
            "- Id: qa1z09\n"
            "- Status: open\n"
            "- Set: epsilon\n"
            "- Priority: medium\n"
            "- Work-Kind: chore\n"
            "- Summary: Synthetic backlog item stored in the companion repository\n"
        ),
    }
    _init_and_commit(companion, companion_files, "corpus: companion_backend companion")
    return target


EXPECTED: dict[str, tuple[CorpusRecord, ...]] = {
    "legacy_agents_layout": (
        CorpusRecord(
            path=".agents/plans/pending/20260701-alpha-01-qa1z01-first-pending-plan.md",
            record_type="plans",
            id6="qa1z01",
            status="to-review",
        ),
        CorpusRecord(
            path=".agents/plans/executed/20260701-alpha-00-qa1z02-alpha-orchestrator.md",
            record_type="plans",
            id6="qa1z02",
            status="executed",
        ),
        CorpusRecord(
            path=".agents/plans/executed/20260705-1015-01-legacy-setup.md",
            record_type="plans",
            id6=None,
            status="executed",
        ),
        CorpusRecord(
            path=".agents/docs/specs/20260706-0900-01-core-spec.spec.md",
            record_type="specs",
            id6=None,
            status="approved",
        ),
        CorpusRecord(
            path=".agents/docs/research/20260708-survey-notes.md",
            record_type="research",
            id6=None,
            status=None,
        ),
    ),
    "mixed_layout": (
        CorpusRecord(
            path=".agents/plans/executed/20260710-beta-01-qa1z03-shared-plan.md",
            record_type="plans",
            id6="qa1z03",
            status="executed",
        ),
        CorpusRecord(
            path=".aw/records/plans/executed/20260710-beta-01-qa1z03-shared-plan.md",
            record_type="plans",
            id6="qa1z03",
            status="executed",
        ),
        CorpusRecord(
            path=".agents/backlog/open/20260815-qa1z04-01-qa1z04-legacy-backlog-item.md",
            record_type="backlog",
            id6="qa1z04",
            status="open",
        ),
        CorpusRecord(
            path=".aw/records/specs/draft/20260816-qa1z05-01-qa1z05-draft-spec.spec.md",
            record_type="specs",
            id6="qa1z05",
            status="draft",
        ),
    ),
    "idless_prose": (
        CorpusRecord(
            path=".aw/records/plans/executed/20260715-prose-migration-ipd.md",
            record_type="plans",
            id6=None,
            status=None,
        ),
    ),
    "no_sidecar": (
        CorpusRecord(
            path=".aw/records/specs/approved/20260820-delta-01-qa1z06-no-sidecar-spec.spec.md",
            record_type="specs",
            id6="qa1z06",
            status="approved",
        ),
        CorpusRecord(
            path=".aw/records/backlog/open/20260821-delta-01-qa1z07-no-sidecar-backlog.backlog.md",
            record_type="backlog",
            id6="qa1z07",
            status="open",
        ),
    ),
    "companion_backend": (
        CorpusRecord(
            path="companion:records/plans/pending/20260825-epsilon-01-qa1z08-companion-plan.ipd.md",
            record_type="plans",
            id6="qa1z08",
            status="approved",
        ),
        CorpusRecord(
            path="companion:records/backlog/open/20260826-epsilon-01-qa1z09-companion-backlog.backlog.md",
            record_type="backlog",
            id6="qa1z09",
            status="open",
        ),
    ),
}

UNCLASSIFIABLE: dict[str, tuple[str, ...]] = {
    "legacy_agents_layout": (
        ".agents/workflows/demo/demo.md",
        ".agents/plans/INDEX.md",
        ".agents/plans/README.md",
    ),
    "mixed_layout": (),
    "idless_prose": (".aw/records/notes/scratch.md",),
    "no_sidecar": (),
    "companion_backend": (),
}

SHAPES: dict[str, Callable[[Path], Path]] = {
    "legacy_agents_layout": legacy_agents_layout,
    "mixed_layout": mixed_layout,
    "idless_prose": idless_prose,
    "no_sidecar": no_sidecar,
    "companion_backend": companion_backend,
}
