"""Tests for date reader clock parity across timezones (IPD hinpcf).

Asserts that date readers compute "today" on the same clock that wrote the stored
value they compare against:
1. UTC operand (attention._age_marker reading workflow history date): uses UTC clock.
2. LOCAL plan operand (plans_archive._age_days reading plan date): uses LOCAL clock.
3. LOCAL research operand (research_archive._age_days reading research created date): uses LOCAL clock.
4. Negative controls through the readers' own injectable 'today' seams verify that a
   mixed-clock pairing produces nonzero ages or inverted staleness verdicts.

Every case executes in a child process with an isolated TZ environment variable
so pytest worker processes under xdist never suffer global timezone mutation.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EAST_TZ = "XXX-24"  # UTC+24: local date is always one day ahead of UTC
WEST_TZ = "XXX+23:59"  # UTC-23:59: local date is one day behind UTC except in final UTC minute


def _run_child(
    snippet: str, tz: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Execute python snippet in a child process with an explicit TZ and isolated PYTHONPATH."""
    env = {
        **os.environ,
        "TZ": tz,
        "PYTHONPATH": f"{REPO_ROOT}:{os.environ.get('PYTHONPATH', '')}".rstrip(":"),
        "AW_NO_REEXEC": "1",
    }
    if env_extra:
        env.update(env_extra)
    res = subprocess.run(
        [sys.executable, "-c", snippet],
        env=env,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Child process failed under TZ={tz} (exit {res.returncode}):\n"
            f"STDOUT:\n{res.stdout}\n"
            f"STDERR:\n{res.stderr}"
        )
    return res


class TestDateReaderClockParity(unittest.TestCase):
    """Behavioral test suite for date reader clock parity across timezones."""

    # --------------------------------------------------------------------------
    # Case (a): UTC operand (attention._age_marker)
    # --------------------------------------------------------------------------

    def _utc_operand_snippet(self, tz: str) -> str:
        return f"""
from datetime import date, datetime, timedelta, timezone
from agent_workflows import artifact_core
from agent_workflows.attention import _age_marker

local_today = date.today()
utc_today = datetime.now(timezone.utc).date()
assert local_today != utc_today, (
    f"Skew precondition failed under {tz}: local {{local_today}} == utc {{utc_today}}"
)

# 1. Fresh date from utc_history_date() returns ''
val = artifact_core.utc_history_date()
fresh_marker = _age_marker(val, "plans")
assert fresh_marker == "", f"Expected '' for fresh UTC date, got {{fresh_marker!r}}"

# 2. Boundary date where reader clock decides verdict
if "{tz}" == "XXX-24":
    # 30 days before UTC today: age under UTC is 30 -> '' (under LOCAL it would be 31 -> '!')
    d30 = (utc_today - timedelta(days=30)).isoformat()
    verdict = _age_marker(d30, "plans")
    assert verdict == "", f"Expected '' for 30d boundary under XXX-24, got {{verdict!r}}"
    print(f"[{tz}] UTC boundary 30d verdict: {{verdict!r}} (correctly recent)")
else:
    # 31 days before UTC today: age under UTC is 31 -> '!' (under LOCAL it would be 30 -> '')
    d31 = (utc_today - timedelta(days=31)).isoformat()
    verdict = _age_marker(d31, "plans")
    assert verdict == "!", f"Expected '!' for 31d boundary under XXX+23:59, got {{verdict!r}}"
    print(f"[{tz}] UTC boundary 31d verdict: {{verdict!r}} (correctly stale)")
"""

    def test_utc_operand_east(self):
        """Case (a): attention._age_marker reads UTC operand correctly under XXX-24."""
        proc = _run_child(self._utc_operand_snippet(EAST_TZ), EAST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)

    def test_utc_operand_west(self):
        """Case (a): attention._age_marker reads UTC operand correctly under XXX+23:59."""
        proc = _run_child(self._utc_operand_snippet(WEST_TZ), WEST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)

    # --------------------------------------------------------------------------
    # Case (b): LOCAL plan operand (plans_archive._age_days)
    # --------------------------------------------------------------------------

    def _local_plan_snippet(self, tz: str) -> str:
        return f"""
import os, subprocess, sys, tempfile, shutil
from pathlib import Path
from datetime import date, datetime, timezone
from agent_workflows import plans_archive

local_today = date.today()
utc_today = datetime.now(timezone.utc).date()
assert local_today != utc_today, (
    f"Skew precondition failed under {tz}: local {{local_today}} == utc {{utc_today}}"
)

tmp = Path(tempfile.mkdtemp(prefix="test_plan_reader_"))
try:
    repo = tmp / "repo"
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    cfg = repo / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text('{{"schema_version": 2}}', encoding="utf-8")

    cmd = [
        sys.executable, "-m", "agent_workflows.cli",
        "ipd", "scaffold",
        "--kind", "child",
        "--title", "x",
        "--set", "xset",
        "--order", "1",
        "--author", "probe",
        "--priority", "low",
        "--work-kind", "chore",
        "--apply"
    ]
    res = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=True)
    files = list(pending.glob("*.ipd.md"))
    assert len(files) == 1, f"Expected 1 plan file, got {{files}}"
    plan_path = files[0]
    text = plan_path.read_text(encoding="utf-8")

    plan_date = plans_archive._resolve_plan_date(plan_path.name, text)
    age = plans_archive._age_days(plan_date)
    assert age == 0.0, f"Expected plan age 0.0, got {{age}}"
    print(f"[{tz}] Plan scaffold date: {{plan_date}}, age: {{age}}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
"""

    def test_local_plan_operand_east(self):
        """Case (b): plans_archive._age_days returns 0.0 for scaffolded plan under XXX-24."""
        proc = _run_child(self._local_plan_snippet(EAST_TZ), EAST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)

    def test_local_plan_operand_west(self):
        """Case (b): plans_archive._age_days returns 0.0 for scaffolded plan under XXX+23:59."""
        proc = _run_child(self._local_plan_snippet(WEST_TZ), WEST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)

    # --------------------------------------------------------------------------
    # Case (c): LOCAL research operand (research_archive._age_days)
    # --------------------------------------------------------------------------

    def _local_research_snippet(self, tz: str) -> str:
        return f"""
import os, re, subprocess, sys, tempfile, shutil
from pathlib import Path
from datetime import date, datetime, timezone
from agent_workflows import research_contract as R
from agent_workflows import research_archive

local_today = date.today()
utc_today = datetime.now(timezone.utc).date()
assert local_today != utc_today, (
    f"Skew precondition failed under {tz}: local {{local_today}} == utc {{utc_today}}"
)

tmp = Path(tempfile.mkdtemp(prefix="test_research_reader_"))
try:
    home_dir = tmp / "home"
    home_dir.mkdir(parents=True)
    repo_dir = tmp / "repo"
    repo_dir.mkdir(parents=True)
    research_root = repo_dir / ".aw" / "records" / "research"
    research_root.mkdir(parents=True)

    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo_dir, check=True)

    env = {{
        **os.environ,
        "TZ": "{tz}",
        "HOME": str(home_dir),
        "XDG_CONFIG_HOME": str(home_dir),
        "AW_NO_REEXEC": "1",
    }}

    cmd = [
        sys.executable, "-m", "agent_workflows.cli",
        "research", "new",
        "--kind", "finding",
        "--slug", "probe-x",
        "--apply"
    ]
    res = subprocess.run(cmd, cwd=repo_dir, env=env, capture_output=True, text=True, check=True)

    m = re.search(r"wrote\\s+(\\S+)", res.stdout)
    assert m, f"No wrote line in stdout: {{res.stdout}}"
    doc_path = Path(m.group(1))
    if not doc_path.is_absolute():
        doc_path = repo_dir / doc_path

    # Verify doc was written under the test temp HOME / repo and not the real user HOME
    real_home = Path.home().resolve()
    assert doc_path.is_file(), f"Doc file does not exist: {{doc_path}}"
    assert str(doc_path.resolve()).startswith(str(tmp.resolve())), (
        f"Doc {{doc_path}} escaped temp base {{tmp}}"
    )
    assert not str(doc_path.resolve()).startswith(str(real_home / ".aw")), (
        f"Doc {{doc_path}} leaked into real home {{real_home}}"
    )
    print(f"[{tz}] Research doc written under temp isolation: {{doc_path}}")

    text = doc_path.read_text(encoding="utf-8")
    fm = R.parse_frontmatter(text)
    assert fm is not None, "Failed to parse research front matter"
    created = str(fm.get("created"))
    age = research_archive._age_days(created)
    assert age == 0.0, f"Expected research age 0.0, got {{age}}"
    print(f"[{tz}] Research created: {{created}}, age: {{age}}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
"""

    def test_local_research_operand_east(self):
        """Case (c): research_archive._age_days returns 0.0 for doc under XXX-24."""
        proc = _run_child(self._local_research_snippet(EAST_TZ), EAST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)

    def test_local_research_operand_west(self):
        """Case (c): research_archive._age_days returns 0.0 for doc under XXX+23:59."""
        proc = _run_child(self._local_research_snippet(WEST_TZ), WEST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)

    # --------------------------------------------------------------------------
    # Case (d): Negative controls through readers' own injectable 'today' seams
    # --------------------------------------------------------------------------

    def _negative_control_snippet(self, tz: str) -> str:
        return f"""
import os, re, subprocess, sys, tempfile, shutil
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from agent_workflows.attention import _age_marker
from agent_workflows import plans_archive
from agent_workflows import research_contract as R
from agent_workflows import research_archive

local_today = date.today()
utc_today = datetime.now(timezone.utc).date()
assert local_today != utc_today, (
    f"Skew precondition failed under {tz}: local {{local_today}} == utc {{utc_today}}"
)

# 1. Negative control on attention._age_marker:
# Passing today=local_today inverts the boundary verdict compared to UTC today
if "{tz}" == "XXX-24":
    d30 = (utc_today - timedelta(days=30)).isoformat()
    utc_verdict = _age_marker(d30, "plans")
    mixed_verdict = _age_marker(d30, "plans", today=local_today)
    assert utc_verdict == "", f"Expected '' for UTC verdict, got {{utc_verdict!r}}"
    assert mixed_verdict == "!", f"Expected '!' for mixed-clock verdict, got {{mixed_verdict!r}}"
    print(f"[{tz}] Negative control attention: UTC verdict={{utc_verdict!r}} vs mixed={{mixed_verdict!r}}")
else:
    d31 = (utc_today - timedelta(days=31)).isoformat()
    utc_verdict = _age_marker(d31, "plans")
    mixed_verdict = _age_marker(d31, "plans", today=local_today)
    assert utc_verdict == "!", f"Expected '!' for UTC verdict, got {{utc_verdict!r}}"
    assert mixed_verdict == "", f"Expected '' for mixed-clock verdict, got {{mixed_verdict!r}}"
    print(f"[{tz}] Negative control attention: UTC verdict={{utc_verdict!r}} vs mixed={{mixed_verdict!r}}")

tmp = Path(tempfile.mkdtemp(prefix="test_neg_control_"))
try:
    # 2. Negative control on plans_archive._age_days:
    repo = tmp / "repo"
    pending = repo / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    cfg = repo / ".aw" / "config"
    cfg.mkdir(parents=True)
    (cfg / "project.json").write_text('{{"schema_version": 2}}', encoding="utf-8")

    cmd_plan = [
        sys.executable, "-m", "agent_workflows.cli",
        "ipd", "scaffold",
        "--kind", "child",
        "--title", "x",
        "--set", "xset",
        "--order", "1",
        "--author", "probe",
        "--priority", "low",
        "--work-kind", "chore",
        "--apply"
    ]
    subprocess.run(cmd_plan, cwd=repo, capture_output=True, text=True, check=True)
    plan_path = list(pending.glob("*.ipd.md"))[0]
    plan_date = plans_archive._resolve_plan_date(plan_path.name, plan_path.read_text(encoding="utf-8"))
    local_plan_age = plans_archive._age_days(plan_date)
    mixed_plan_age = plans_archive._age_days(plan_date, today=utc_today)
    assert local_plan_age == 0.0, f"Expected 0.0, got {{local_plan_age}}"
    assert mixed_plan_age != 0.0, f"Expected nonzero mixed plan age, got {{mixed_plan_age}}"
    expected_mixed_plan = -1.0 if "{tz}" == "XXX-24" else 1.0
    assert mixed_plan_age == expected_mixed_plan, (
        f"Expected {{expected_mixed_plan}} for mixed plan age, got {{mixed_plan_age}}"
    )
    print(f"[{tz}] Negative control plan: local age={{local_plan_age}} vs mixed age={{mixed_plan_age}}")

    # 3. Negative control on research_archive._age_days:
    home_dir = tmp / "home"
    home_dir.mkdir(parents=True)
    repo_res = tmp / "repo_res"
    repo_res.mkdir(parents=True)
    (repo_res / ".aw" / "records" / "research").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo_res, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=repo_res, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo_res, check=True)

    env_res = {{
        **os.environ,
        "TZ": "{tz}",
        "HOME": str(home_dir),
        "XDG_CONFIG_HOME": str(home_dir),
        "AW_NO_REEXEC": "1",
    }}
    cmd_res = [
        sys.executable, "-m", "agent_workflows.cli",
        "research", "new",
        "--kind", "finding",
        "--slug", "probe-x",
        "--apply"
    ]
    res = subprocess.run(cmd_res, cwd=repo_res, env=env_res, capture_output=True, text=True, check=True)
    m = re.search(r"wrote\\s+(\\S+)", res.stdout)
    doc_path = Path(m.group(1))
    if not doc_path.is_absolute():
        doc_path = repo_res / doc_path
    fm = R.parse_frontmatter(doc_path.read_text(encoding="utf-8"))
    created = str(fm.get("created"))
    local_res_age = research_archive._age_days(created)
    mixed_res_age = research_archive._age_days(created, today=utc_today)
    assert local_res_age == 0.0, f"Expected 0.0, got {{local_res_age}}"
    assert mixed_res_age != 0.0, f"Expected nonzero mixed research age, got {{mixed_res_age}}"
    expected_mixed_res = -1.0 if "{tz}" == "XXX-24" else 1.0
    assert mixed_res_age == expected_mixed_res, (
        f"Expected {{expected_mixed_res}} for mixed research age, got {{mixed_res_age}}"
    )
    print(f"[{tz}] Negative control research: local age={{local_res_age}} vs mixed age={{mixed_res_age}}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
"""

    def test_negative_control_east(self):
        """Case (d): Negative controls verify clock mismatch detection under XXX-24."""
        proc = _run_child(self._negative_control_snippet(EAST_TZ), EAST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)

    def test_negative_control_west(self):
        """Case (d): Negative controls verify clock mismatch detection under XXX+23:59."""
        proc = _run_child(self._negative_control_snippet(WEST_TZ), WEST_TZ)
        print(proc.stdout.strip())
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
