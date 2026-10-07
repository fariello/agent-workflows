"""Behavioral guard asserting agent_workflows.worktree_lease stays stdlib-only (IPD d8sc5n, backlog rdl9lh).

WHY THIS GUARD EXISTS.
`worktree_lease` provides core worktree and leasing primitives. To keep import overhead low
(preventing a 2.10x import regression) and prevent latent import cycles with `runner_shared`,
`worktree_lease` imports no first-party `agent_workflows` modules at module level.

WHY A SUBPROCESS IS REQUIRED (NOT AN IN-PROCESS CHECK).
An in-process inspection of `sys.modules` suffers from order-dependent false positives: if an
earlier test in the same pytest-xdist worker process imported `agent_workflows.runner_shared`
(or any other first-party module), ambient `sys.modules` already contains it. Because
`pyproject.toml` configures `-n auto` and `pytest-randomly`, an in-process test would flake.
Spawning a fresh subprocess via `sys.executable` guarantees a clean interpreter state.
Subprocesses are pinned to THIS worktree using `tests.support.pinned_env()` to ensure
resolution against the current checkout rather than an editable install's `.pth` entry
(following the precedent in `tests/test_lane_import_root.py`).

WHY THE BASELINE IS DERIVED AT RUNTIME.
Bare `import agent_workflows` legitimately loads packages imported by `agent_workflows/__init__.py`
(such as `agent_workflows._compat` and `agent_workflows.versioning`). Deriving the baseline
dynamically by snapshotting `sys.modules` right after `import agent_workflows` prevents brittle
failures when `__init__.py` changes legitimately.

NOT A CODE-STRUCTURE PIN.
Per `GUIDING_PRINCIPLES.md` P16 and `AGENTS.md`, this test asserts observable interpreter outcomes
(which modules are actually loaded in `sys.modules`) rather than inspecting production source text
with `inspect`, `ast`, regex, or `read_text()`.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest

from tests import support


class WorktreeLeaseStdlibOnlyTests(unittest.TestCase):
    """Assert worktree_lease stays stdlib-only at module level and preserves lazy delegation."""

    def test_worktree_lease_imports_no_first_party_modules(self) -> None:
        """Importing worktree_lease must pull in zero first-party modules beyond the package baseline."""
        probe = textwrap.dedent(
            """
            import json
            import sys
            import agent_workflows

            # Derive baseline at runtime rather than hardcoding module names.
            baseline = {m for m in sys.modules if m.startswith("agent_workflows")}
            import agent_workflows.worktree_lease

            after = {m for m in sys.modules if m.startswith("agent_workflows")}
            delta = sorted(list(after - baseline - {"agent_workflows.worktree_lease"}))
            print(f"BASELINE={json.dumps(sorted(list(baseline)))}")
            print(f"AFTER={json.dumps(sorted(list(after)))}")
            print(f"DELTA={json.dumps(delta)}")
            """
        ).strip()

        proc = subprocess.run(
            [sys.executable, "-c", probe],
            env=support.pinned_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode, 0, f"Probe failed (rc={proc.returncode}):\n{proc.stderr}"
        )

        delta: list[str] | None = None
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("DELTA="):
                delta = json.loads(line.split("=", 1)[1])
                print(line)

        self.assertIsNotNone(
            delta, f"Probe stdout did not contain DELTA line:\n{proc.stdout}"
        )
        self.assertEqual(
            delta,
            [],
            f"Importing agent_workflows.worktree_lease pulled in unexpected first-party modules: {delta}",
        )

    def test_lane_merged_into_target_lazy_delegation(self) -> None:
        """lane_merged_into_target must lazily import runner_shared on call (absent before, present after)."""
        probe = textwrap.dedent(
            """
            import sys
            from pathlib import Path
            import agent_workflows.worktree_lease as WL

            file_path = getattr(WL, "__file__", "")
            before = "agent_workflows.runner_shared" in sys.modules
            tmp_repo = Path(sys.argv[1])
            ret = WL.lane_merged_into_target(tmp_repo, "definitely-nonexistent-branch-xyz")
            after = "agent_workflows.runner_shared" in sys.modules

            print(f"FILE={file_path}")
            print(f"BEFORE={before}")
            print(f"RET={ret}")
            print(f"AFTER={after}")
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            proc = subprocess.run(
                [sys.executable, "-c", probe, tmp_dir],
                env=support.pinned_env(),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(
            proc.returncode, 0, f"Probe failed (rc={proc.returncode}):\n{proc.stderr}"
        )

        parsed: dict[str, str] = {}
        for line in proc.stdout.splitlines():
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                parsed[k] = v
                print(line)

        self.assertIn("BEFORE", parsed, f"Probe output missing BEFORE:\n{proc.stdout}")
        self.assertIn("AFTER", parsed, f"Probe output missing AFTER:\n{proc.stdout}")
        self.assertIn("RET", parsed, f"Probe output missing RET:\n{proc.stdout}")

        before_loaded = parsed["BEFORE"] == "True"
        after_loaded = parsed["AFTER"] == "True"
        ret_val = parsed["RET"] == "True"

        self.assertFalse(
            before_loaded,
            "agent_workflows.runner_shared must NOT be present in sys.modules before lane_merged_into_target is called",
        )
        self.assertFalse(
            ret_val,
            "lane_merged_into_target must return False for a nonexistent branch in an empty repo root",
        )
        self.assertTrue(
            after_loaded,
            "agent_workflows.runner_shared MUST be present in sys.modules after lane_merged_into_target is called",
        )
