#!/usr/bin/env python3
"""Guard test ensuring all tracked pytest test modules are collected by bare pytest.

Authored under IPD 5s31xp (backlog n8adhb) to prevent test modules residing outside
`tests/` from rotting unobserved because pyproject.toml sets testpaths = ["tests"].
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Container, Iterable, Mapping, Sequence

# Explicit, reasoned, self-pruning exemption list.
# Every entry must name an owning backlog item or plan and a justification.
EXEMPT: dict[str, str] = {
    "tools/ipdrunner/test_runagy.py": (
        "owned by backlog 3rj8wr: 10 failing tests; triage and repair/relocation out of scope"
    ),
    "tools/awphysical/test_awphysical_tools.py": (
        "owned by backlog byz9pj: 1 failing binding test; requires updating scenario token bindings"
    ),
    "tools/aw_upgrade_test.py": (
        "not a test module: compat shim for `aw upgrade-test` matching *_test.py pattern with 0 tests"
    ),
    "tests/test_lift_drift_scan.py": (
        "retired placeholder under plan 96xtmi: empty TestCase with no test methods; 0 collected"
    ),
}

# Prefix exclusions for trees authored by any agent (e.g. research prototypes).
# Excluded from per-file stale checks to prevent merge blocking on prototype test files.
EXEMPT_PREFIXES: tuple[str, ...] = (".aw/",)


def is_pytest_test_filename(rel_path: str) -> bool:
    """Return True if rel_path matches pytest's default python_files patterns (test_*.py or *_test.py)."""
    name = Path(rel_path).name
    if not name.endswith(".py"):
        return False
    return name.startswith("test_") or name.endswith("_test.py")


@dataclass(frozen=True)
class CollectionAuditResult:
    """Result of evaluating test module collection."""

    uncollected: list[str]
    stale_missing: list[str]
    stale_collected: list[str]

    @property
    def is_clean(self) -> bool:
        return (
            not self.uncollected and not self.stale_missing and not self.stale_collected
        )


def evaluate_test_module_collection(
    candidates: Iterable[str],
    collected: Iterable[str],
    exempt: Mapping[str, str],
    exempt_prefixes: Sequence[str] = EXEMPT_PREFIXES,
    existing_files: Container[str] | None = None,
) -> CollectionAuditResult:
    """Evaluate whether tracked test files are collected or properly exempted.

    Pure helper factoring the set arithmetic away from live filesystem / subprocess execution.
    """
    candidate_set = {os.path.normpath(c) for c in candidates}
    collected_set = {os.path.normpath(c) for c in collected}
    exempt_map = {os.path.normpath(k): v for k, v in exempt.items()}

    uncollected: list[str] = []
    for c in sorted(candidate_set):
        if c in collected_set:
            continue
        if any(
            c.startswith(os.path.normpath(p)) or c.startswith(p)
            for p in exempt_prefixes
        ):
            continue
        if c in exempt_map:
            continue
        uncollected.append(c)

    stale_missing: list[str] = []
    stale_collected: list[str] = []
    for e in sorted(exempt_map.keys()):
        if existing_files is not None and e not in existing_files:
            stale_missing.append(e)
        if e in collected_set:
            stale_collected.append(e)

    return CollectionAuditResult(
        uncollected=uncollected,
        stale_missing=stale_missing,
        stale_collected=stale_collected,
    )


class UncollectedTestModulesGuardTests(unittest.TestCase):
    """Guard against tracked pytest-discoverable test files not collected by bare pytest."""

    def test_evaluate_test_module_collection_synthetic_inputs(self) -> None:
        """Verify the pure set-arithmetic helper independently of the live tree."""
        # 1. Uncollected file flagged
        res = evaluate_test_module_collection(
            candidates=["tools/test_foo.py"],
            collected=[],
            exempt={},
            exempt_prefixes=(".aw/",),
            existing_files={"tools/test_foo.py"},
        )
        self.assertEqual(res.uncollected, ["tools/test_foo.py"])
        self.assertFalse(res.is_clean)

        # 2. Exempt file passes
        res = evaluate_test_module_collection(
            candidates=["tools/test_exempt.py"],
            collected=[],
            exempt={"tools/test_exempt.py": "reason"},
            exempt_prefixes=(".aw/",),
            existing_files={"tools/test_exempt.py"},
        )
        self.assertEqual(res.uncollected, [])
        self.assertEqual(res.stale_missing, [])
        self.assertEqual(res.stale_collected, [])
        self.assertTrue(res.is_clean)

        # 3. Stale exemption flagged when missing
        res = evaluate_test_module_collection(
            candidates=[],
            collected=[],
            exempt={"tools/test_vanished.py": "reason"},
            exempt_prefixes=(".aw/",),
            existing_files=set(),
        )
        self.assertEqual(res.stale_missing, ["tools/test_vanished.py"])
        self.assertFalse(res.is_clean)

        # 4. Stale exemption flagged when now collected
        res = evaluate_test_module_collection(
            candidates=["tests/test_now_collected.py"],
            collected=["tests/test_now_collected.py"],
            exempt={"tests/test_now_collected.py": "reason"},
            exempt_prefixes=(".aw/",),
            existing_files={"tests/test_now_collected.py"},
        )
        self.assertEqual(res.stale_collected, ["tests/test_now_collected.py"])
        self.assertFalse(res.is_clean)

        # 5. Prefix-excluded file passes (e.g. .aw/)
        res = evaluate_test_module_collection(
            candidates=[".aw/records/research/prototype/test_broker.py"],
            collected=[],
            exempt={},
            exempt_prefixes=(".aw/",),
            existing_files={".aw/records/research/prototype/test_broker.py"},
        )
        self.assertEqual(res.uncollected, [])
        self.assertTrue(res.is_clean)

        # 6. Collected file passes
        res = evaluate_test_module_collection(
            candidates=["tests/test_regular.py"],
            collected=["tests/test_regular.py"],
            exempt={},
            exempt_prefixes=(".aw/",),
            existing_files={"tests/test_regular.py"},
        )
        self.assertEqual(res.uncollected, [])
        self.assertTrue(res.is_clean)

    def test_no_uncollected_test_modules(self) -> None:
        """Assert every tracked test file is collected by pytest or explicitly exempt."""
        repo_root = Path(__file__).resolve().parent.parent

        if shutil.which("git") is None:
            self.skipTest("git executable not found in PATH")

        git_check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if git_check.returncode != 0 or git_check.stdout.strip() != "true":
            self.skipTest(f"Not inside a git worktree: {repo_root}")

        git_ls = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        candidates = [
            line.strip()
            for line in git_ls.stdout.splitlines()
            if is_pytest_test_filename(line.strip())
        ]

        pytest_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "-m",
            "",
            "-p",
            "no:randomly",
        ]
        pytest_proc = subprocess.run(
            pytest_cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if pytest_proc.returncode not in (0, 5):
            self.fail(
                f"pytest collection failed with returncode {pytest_proc.returncode}:\n"
                f"STDOUT:\n{pytest_proc.stdout}\nSTDERR:\n{pytest_proc.stderr}"
            )

        collected = {
            line.split("::", 1)[0].strip()
            for line in pytest_proc.stdout.splitlines()
            if "::" in line
        }

        existing_files = {p for p in EXEMPT if (repo_root / p).is_file()}

        result = evaluate_test_module_collection(
            candidates=candidates,
            collected=collected,
            exempt=EXEMPT,
            exempt_prefixes=EXEMPT_PREFIXES,
            existing_files=existing_files,
        )

        if not result.is_clean:
            messages: list[str] = []
            if result.uncollected:
                uncollected_list = "\n".join(
                    f"  - {path}" for path in result.uncollected
                )
                messages.append(
                    f"Found tracked pytest-discoverable test module(s) not collected by bare `pytest`:\n"
                    f"{uncollected_list}\n\n"
                    f"To fix: move each module under tests/ so bare `pytest` collects it, "
                    f"or add a reasoned entry to EXEMPT in tests/test_uncollected_test_modules.py "
                    f"naming an owning backlog item."
                )
            if result.stale_missing:
                stale_missing_list = "\n".join(
                    f"  - {path}" for path in result.stale_missing
                )
                messages.append(
                    f"Found EXEMPT test module entries that do not exist on disk (stale exemptions):\n"
                    f"{stale_missing_list}\n\n"
                    f"To fix: remove stale entries from EXEMPT in tests/test_uncollected_test_modules.py."
                )
            if result.stale_collected:
                stale_collected_list = "\n".join(
                    f"  - {path}" for path in result.stale_collected
                )
                messages.append(
                    f"Found EXEMPT test module entries that are now collected by pytest (stale exemptions):\n"
                    f"{stale_collected_list}\n\n"
                    f"To fix: remove entries from EXEMPT in tests/test_uncollected_test_modules.py "
                    f"because they are now collected."
                )
            self.fail("\n\n" + "\n\n".join(messages))


if __name__ == "__main__":
    unittest.main()
