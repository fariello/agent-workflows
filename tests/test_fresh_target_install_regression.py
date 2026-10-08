"""Regression test proving Set instbugs defects are resolved end-to-end on a scratch target.

Assigned IPD: kck7a5 (Order 11 of Set instbugs).
Re-creates the research report l6cbbb situation: a fresh install into a non-Python
(package.json-only) git repository, asserting all reported defects and cross-child
interactions are resolved:
- D01/N2: version reporting consistency, no host leak in install state records
- D02: durable state and local config ignored by git
- D03/N1: porcelain clean status after -y, run-scratch ignore advisory truth
- D04: consent plan resolved physical class paths exist on disk
- D05: state records under .aw/state/durable/, not at state root
- D06: no root workflow-artifacts/ directory
- D07: target-neutral managed AGENTS.md block
- D08/D09: no retired .agents/ paths, research README has no intake status
- D14: .aw/inbox/README.md tracked, drop files ignored
- D15: tracking truth table matches project.json git policies
- Dangling references: zero doctor.dangling-doc-reference diagnostics
- D10, D11, D12: research verbs composition (01 numbering, 0644 mode, order mismatch check)
"""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import time

import pytest

pytestmark = pytest.mark.slow

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@dataclasses.dataclass
class FreshTarget:
    target_dir: pathlib.Path
    fake_home: pathlib.Path
    env: dict[str, str]
    dry_run_stdout: str
    dry_run_stderr: str
    install_stdout: str
    install_stderr: str
    porcelain_after_install: str


@pytest.fixture(scope="module")
def fresh_target():
    """Build a package.json-only temp git repo and run dry-run and real installs once."""
    with tempfile.TemporaryDirectory(
        prefix="aw_fresh_home_"
    ) as home_td, tempfile.TemporaryDirectory(prefix="aw_fresh_repo_") as repo_td:
        fake_home = pathlib.Path(home_td).resolve()
        target_dir = pathlib.Path(repo_td).resolve()

        # Initialize git repo with attribution and package.json
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=target_dir, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test Committer"],
            cwd=target_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "committer@example.com"],
            cwd=target_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"],
            cwd=target_dir,
            check=True,
        )

        (target_dir / "package.json").write_text(
            '{"name": "fresh-target-pkg"}\n', encoding="utf-8"
        )
        subprocess.run(["git", "add", "package.json"], cwd=target_dir, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "Initial commit"], cwd=target_dir, check=True
        )

        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["XDG_CONFIG_HOME"] = str(fake_home / ".config")
        env["AW_NO_REEXEC"] = "1"
        env["GIT_AUTHOR_NAME"] = "Test Committer"
        env["GIT_AUTHOR_EMAIL"] = "committer@example.com"
        env["GIT_COMMITTER_NAME"] = "Test Committer"
        env["GIT_COMMITTER_EMAIL"] = "committer@example.com"
        existing_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{REPO_ROOT}:{existing_pp}".rstrip(":")

        # 1. Capture consent plan via dry run
        dry_res = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "install",
                ".",
                "--dry-run",
                "--preset",
                "private-target",
                "-y",
                "--no-interactive",
            ],
            cwd=target_dir,
            env=env,
            capture_output=True,
            text=True,
        )

        # 2. Perform real install
        inst_res = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "install",
                ".",
                "--preset",
                "private-target",
                "-y",
                "--no-interactive",
            ],
            cwd=target_dir,
            env=env,
            capture_output=True,
            text=True,
        )

        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )

        yield FreshTarget(
            target_dir=target_dir,
            fake_home=fake_home,
            env=env,
            dry_run_stdout=dry_res.stdout,
            dry_run_stderr=dry_res.stderr,
            install_stdout=inst_res.stdout,
            install_stderr=inst_res.stderr,
            porcelain_after_install=status_proc.stdout,
        )


def test_install_d01_n2_version_consistency(fresh_target: FreshTarget) -> None:
    """D01/N2: installed_version in install.json matches aw --version, no HOME path leak."""
    install_json_path = (
        fresh_target.target_dir / ".aw" / "state" / "durable" / "install.json"
    )
    history_jsonl_path = (
        fresh_target.target_dir
        / ".aw"
        / "state"
        / "durable"
        / "history"
        / "installs.jsonl"
    )

    assert (
        install_json_path.is_file()
    ), "D01/N2: .aw/state/durable/install.json not found"
    assert (
        history_jsonl_path.is_file()
    ), "D01/N2: .aw/state/durable/history/installs.jsonl not found"

    install_text = install_json_path.read_text(encoding="utf-8")
    history_text = history_jsonl_path.read_text(encoding="utf-8")

    install_data = json.loads(install_text)
    installed_ver = install_data.get("installed_version")
    assert installed_ver, "D01/N2: installed_version missing or empty in install.json"

    ver_proc = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "--version"],
        cwd=fresh_target.target_dir,
        env=fresh_target.env,
        capture_output=True,
        text=True,
        check=True,
    )
    expected_ver = ver_proc.stdout.strip().split()[-1]
    assert (
        installed_ver == expected_ver
    ), f"D01/N2: installed_version {installed_ver!r} != expected version {expected_ver!r}"

    fake_home_str = str(fresh_target.fake_home)
    assert (
        fake_home_str not in install_text
    ), "D01/N2: temp HOME path leaked into install.json"
    assert (
        fake_home_str not in history_text
    ), "D01/N2: temp HOME path leaked into history/installs.jsonl"


def test_install_d02_state_and_config_ignored(fresh_target: FreshTarget) -> None:
    """D02: git check-ignore -q succeeds for install.json and local.json."""
    durable_file = ".aw/state/durable/install.json"
    local_config = ".aw/config/local.json"

    res_durable = subprocess.run(
        ["git", "check-ignore", "-q", durable_file],
        cwd=fresh_target.target_dir,
    )
    assert res_durable.returncode == 0, f"D02: {durable_file} is not ignored by git"

    res_config = subprocess.run(
        ["git", "check-ignore", "-q", local_config],
        cwd=fresh_target.target_dir,
    )
    assert res_config.returncode == 0, f"D02: {local_config} is not ignored by git"


def test_install_d03_n1_clean_porcelain_and_run_scratch_ignored(
    fresh_target: FreshTarget,
) -> None:
    """D03/N1: porcelain status after -y is empty, run scratch ignored, no STAGED but NOT committed."""
    assert (
        fresh_target.porcelain_after_install.strip() == ""
    ), f"D03/N1: git status --porcelain not empty after -y install:\n{fresh_target.porcelain_after_install}"

    # Captured install output's "Gitignore (run scratch)" line says "is ignored"
    scratch_lines = [
        line
        for line in fresh_target.install_stdout.splitlines()
        if "Gitignore (run scratch):" in line
    ]
    assert (
        scratch_lines
    ), "D03/N1: missing 'Gitignore (run scratch):' line in install output"
    assert (
        "is ignored" in scratch_lines[0]
    ), f"D03/N1: 'Gitignore (run scratch)' line did not state 'is ignored': {scratch_lines[0]}"

    # git check-ignore -q .aw/workflow-artifacts/README.md succeeds
    ci_proc = subprocess.run(
        ["git", "check-ignore", "-q", ".aw/workflow-artifacts/README.md"],
        cwd=fresh_target.target_dir,
    )
    assert (
        ci_proc.returncode == 0
    ), "D03/N1: .aw/workflow-artifacts/README.md is not ignored by git"

    # Install output does not contain "STAGED but NOT committed"
    assert (
        "STAGED but NOT committed" not in fresh_target.install_stdout
    ), "D03/N1: install output falsely contained 'STAGED but NOT committed'"


def test_install_d04_consent_plan_paths_exist(fresh_target: FreshTarget) -> None:
    """D04: every target path printed under Resolved Physical Classes in dry-run exists after real install."""
    dry_lines = fresh_target.dry_run_stdout.splitlines()
    in_section = False
    resolved_paths: dict[str, str] = {}

    for line in dry_lines:
        line_s = line.strip()
        if "Resolved Physical Classes" in line_s:
            in_section = True
            continue
        if in_section:
            if (
                not line_s
                or line_s.endswith(":")
                or line_s.startswith("Expected Deltas:")
            ):
                in_section = False
                continue
            # Match format: - <cls> : <path> [target] (<policy>)
            match = re.match(r"-\s*([a-zA-Z0-9_]+)\s*:\s*(\S+)\s*\[target\]", line_s)
            if match:
                cls_name = match.group(1)
                p_str = match.group(2)
                resolved_paths[cls_name] = p_str

    assert resolved_paths, "D04: could not parse any target classes from dry-run output"

    for cls_name, p_str in resolved_paths.items():
        p = pathlib.Path(p_str)
        if cls_name in ("config_project", "config_local"):
            assert (
                p.is_file()
            ), f"D04: config class {cls_name} path {p} is not an existing file"
        elif cls_name in ("state_durable", "state_runtime"):
            assert (
                p.exists() or p.parent.exists()
            ), f"D04: state class {cls_name} path {p} or parent does not exist"
        else:
            assert (
                p.is_dir()
            ), f"D04: class {cls_name} directory path {p} does not exist"


def test_install_d05_no_root_state_files(fresh_target: FreshTarget) -> None:
    """D05: .aw/state/ holds no install.json or history/ at root; exists under durable/."""
    state_dir = fresh_target.target_dir / ".aw" / "state"
    assert not (
        state_dir / "install.json"
    ).exists(), "D05: install.json exists at root of .aw/state/"
    assert not (
        state_dir / "history"
    ).exists(), "D05: history/ exists at root of .aw/state/"
    assert not (
        state_dir / "installs.jsonl"
    ).exists(), "D05: installs.jsonl exists at root of .aw/state/"

    assert (
        state_dir / "durable" / "install.json"
    ).is_file(), "D05: install.json missing from .aw/state/durable/"
    assert (
        state_dir / "durable" / "history" / "installs.jsonl"
    ).is_file(), "D05: installs.jsonl missing from .aw/state/durable/history/"


def test_install_d06_no_root_workflow_artifacts(fresh_target: FreshTarget) -> None:
    """D06: no root workflow-artifacts/ directory."""
    root_wa = fresh_target.target_dir / "workflow-artifacts"
    assert not root_wa.exists(), f"D06: retired root directory {root_wa} exists"


def test_install_d07_managed_agents_block_neutral(fresh_target: FreshTarget) -> None:
    """D07: managed AGENTS.md block names none of python3 -m pytest, RELEASING.md, oc_runipd.py."""
    agents_path = fresh_target.target_dir / "AGENTS.md"
    assert agents_path.is_file(), "D07: AGENTS.md was not installed"
    content = agents_path.read_text(encoding="utf-8")

    start_idx = content.find("<!-- aw:block -->")
    end_idx = content.find("<!-- /aw:block -->")
    assert (
        start_idx != -1 and end_idx != -1
    ), "D07: managed aw:block delimiters not found in AGENTS.md"

    managed_block = content[start_idx:end_idx]
    for prohibited in ("python3 -m pytest", "RELEASING.md", "oc_runipd.py"):
        assert (
            prohibited not in managed_block
        ), f"D07: managed block in AGENTS.md contains repo-local reference {prohibited!r}"


def test_install_d08_d09_no_retired_agents_paths_or_intake(
    fresh_target: FreshTarget,
) -> None:
    """D08/D09: no .agents/(plans|prompts|comms|docs|workflows) in output, gitignore or records; no intake status."""
    retired_re = re.compile(r"\.agents/(plans|prompts|comms|docs|workflows)")

    assert not retired_re.search(
        fresh_target.install_stdout
    ), "D08/D09: install output contains retired .agents/ path"

    target_gi = fresh_target.target_dir / ".gitignore"
    if target_gi.is_file():
        assert not retired_re.search(
            target_gi.read_text(encoding="utf-8")
        ), "D08/D09: target .gitignore contains retired .agents/ path"

    aw_gi = fresh_target.target_dir / ".aw" / ".gitignore"
    assert aw_gi.is_file(), "D08/D09: .aw/.gitignore not found"
    assert not retired_re.search(
        aw_gi.read_text(encoding="utf-8")
    ), "D08/D09: .aw/.gitignore contains retired .agents/ path"

    records_dir = fresh_target.target_dir / ".aw" / "records"
    if records_dir.is_dir():
        for f in records_dir.rglob("*"):
            if f.is_file():
                f_text = f.read_text(encoding="utf-8", errors="replace")
                assert not retired_re.search(
                    f_text
                ), f"D08/D09: record file {f.relative_to(fresh_target.target_dir)} contains retired .agents/ path"

    # Research README does not present intake as a current status
    research_readme = records_dir / "research" / "README.md"
    assert (
        research_readme.is_file()
    ), "D08/D09: .aw/records/research/README.md not found"
    readme_text = research_readme.read_text(encoding="utf-8")
    # Must not present | `intake` | as a primary status column entry
    assert not re.search(
        r"\|\s*`intake`\s*\|", readme_text
    ), "D08/D09: research README presents `intake` as a current status"


def test_install_d14_inbox_readme_tracked_and_drops_ignored(
    fresh_target: FreshTarget,
) -> None:
    """D14: git ls-files lists .aw/inbox/README.md; drop files are ignored by git check-ignore."""
    inbox_readme = ".aw/inbox/README.md"
    ls_proc = subprocess.run(
        ["git", "ls-files", inbox_readme],
        cwd=fresh_target.target_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        ls_proc.stdout.strip() == inbox_readme
    ), f"D14: {inbox_readme} is not tracked by git: {ls_proc.stdout}"

    drop_file = fresh_target.target_dir / ".aw" / "inbox" / "drop.md"
    drop_file.write_text("# Untracked drop\n", encoding="utf-8")
    try:
        ign_proc = subprocess.run(
            ["git", "check-ignore", "-q", ".aw/inbox/drop.md"],
            cwd=fresh_target.target_dir,
        )
        assert (
            ign_proc.returncode == 0
        ), "D14: .aw/inbox/drop.md was not reported ignored by git"
    finally:
        if drop_file.exists():
            drop_file.unlink()


def test_install_d15_tracking_truth_table(fresh_target: FreshTarget) -> None:
    """D15: tracking truth table matches project.json git policies; state_durable is ignored."""
    proj_json = fresh_target.target_dir / ".aw" / "config" / "project.json"
    assert proj_json.is_file(), "D15: project.json missing"
    data = json.loads(proj_json.read_text(encoding="utf-8"))
    git_policies = data.get("git_policies", {})

    assert (
        git_policies.get("state_durable") == "ignored"
    ), f"D15: state_durable git policy is {git_policies.get('state_durable')!r}, expected 'ignored'"

    # Check config_project: target-git -> tracked
    assert (
        git_policies.get("config_project") == "target-git"
    ), "D15: config_project git policy is not target-git"
    cf_proc = subprocess.run(
        ["git", "ls-files", ".aw/config/project.json"],
        cwd=fresh_target.target_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        cf_proc.stdout.strip() == ".aw/config/project.json"
    ), "D15: .aw/config/project.json is not tracked by git"

    # Check config_local: ignored -> reported by check-ignore
    assert (
        git_policies.get("config_local") == "ignored"
    ), "D15: config_local git policy is not ignored"
    ci_local = subprocess.run(
        ["git", "check-ignore", "-q", ".aw/config/local.json"],
        cwd=fresh_target.target_dir,
    )
    assert ci_local.returncode == 0, "D15: .aw/config/local.json is not ignored by git"

    # Check state_durable: ignored -> every on-disk file in .aw/state/durable is ignored
    durable_dir = fresh_target.target_dir / ".aw" / "state" / "durable"
    for f in durable_dir.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(fresh_target.target_dir))
            ci = subprocess.run(
                ["git", "check-ignore", "-q", rel],
                cwd=fresh_target.target_dir,
            )
            assert (
                ci.returncode == 0
            ), f"D15: state_durable file {rel} is not ignored by git"

    # Check records: target-git -> every on-disk file in .aw/records is tracked
    assert (
        git_policies.get("records") == "target-git"
    ), "D15: records git policy is not target-git"
    records_dir = fresh_target.target_dir / ".aw" / "records"
    for f in records_dir.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(fresh_target.target_dir))
            ls = subprocess.run(
                ["git", "ls-files", rel],
                cwd=fresh_target.target_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            assert (
                ls.stdout.strip() == rel
            ), f"D15: records file {rel} is not tracked by git"

    # Check system: target-git -> every on-disk file in .aw/system (except generated layout artifacts) is tracked
    assert (
        git_policies.get("system") == "target-git"
    ), "D15: system git policy is not target-git"
    system_dir = fresh_target.target_dir / ".aw" / "system"
    for f in system_dir.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(fresh_target.target_dir))
            if f.name in ("layout.json", "layout.schema.json"):
                # Generated install-time artifacts explicitly ignored by .aw/.gitignore (engine._AW_GITIGNORE_TEMPLATE)
                ci = subprocess.run(
                    ["git", "check-ignore", "-q", rel],
                    cwd=fresh_target.target_dir,
                )
                assert (
                    ci.returncode == 0
                ), f"D15: generated layout artifact {rel} must be ignored by git"
            else:
                ls = subprocess.run(
                    ["git", "ls-files", rel],
                    cwd=fresh_target.target_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                assert (
                    ls.stdout.strip() == rel
                ), f"D15: system file {rel} is not tracked by git"


def test_install_doctor_zero_dangling_references(fresh_target: FreshTarget) -> None:
    """Dangling references: aw doctor --json --dir <target> reports 0 doctor.dangling-doc-reference diagnostics."""
    doc_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "doctor",
            "--json",
            "--dir",
            str(fresh_target.target_dir),
        ],
        cwd=fresh_target.target_dir,
        env=fresh_target.env,
        capture_output=True,
        text=True,
        check=False,
    )
    doc_data = json.loads(doc_proc.stdout)
    dangling_findings = [
        diag
        for diag in doc_data.get("diagnostics", [])
        if diag.get("rule") == "doctor.dangling-doc-reference"
    ]
    assert (
        dangling_findings == []
    ), f"Dangling doc references detected in fresh target:\n{dangling_findings}"


def test_research_composition_d10_d11_d12(fresh_target: FreshTarget) -> None:
    """E-03: research new and adopt produce -01- filenames with order: 01 (D12), mode 0o644 (D11),

    and research index --check catches order mismatch (D10).
    """
    t0 = time.perf_counter()
    preexec = (lambda: os.umask(0o022)) if os.name == "posix" else None

    # 1. aw research new --kind research-report --set newset --slug a --apply
    res_new = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "research",
            "new",
            "--kind",
            "research-report",
            "--set",
            "newset",
            "--slug",
            "a",
            "--apply",
        ],
        cwd=fresh_target.target_dir,
        env=fresh_target.env,
        capture_output=True,
        text=True,
        preexec_fn=preexec,
    )
    assert (
        res_new.returncode == 0
    ), f"research new failed: {res_new.stderr}\n{res_new.stdout}"

    # 2. Write .aw/inbox/drop.md and run aw adopt
    drop_file = fresh_target.target_dir / ".aw" / "inbox" / "drop.md"
    drop_file.write_text(
        "# Dropped Research Document\n\nExternal drop content.\n", encoding="utf-8"
    )

    res_adopt = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "adopt",
            ".aw/inbox/drop.md",
            "--type",
            "research",
            "--kind",
            "research-report",
            "--set",
            "otherset",
            "--slug",
            "b",
            "--apply",
            "--yes",
        ],
        cwd=fresh_target.target_dir,
        env=fresh_target.env,
        capture_output=True,
        text=True,
        preexec_fn=preexec,
    )
    assert (
        res_adopt.returncode == 0
    ), f"adopt failed: {res_adopt.stderr}\n{res_adopt.stdout}"

    # Find the created research files
    research_dir = fresh_target.target_dir / ".aw" / "records" / "research"
    f1_list = list(research_dir.glob("*-newset-*-a.research-report.md"))
    f2_list = list(research_dir.glob("*-otherset-*-b.research-report.md"))

    assert len(f1_list) == 1, f"Expected 1 research file for newset, found: {f1_list}"
    assert len(f2_list) == 1, f"Expected 1 research file for otherset, found: {f2_list}"

    f1 = f1_list[0]
    f2 = f2_list[0]

    try:
        # D12: Both filenames carry '-01-'
        assert "-01-" in f1.name, f"D12: {f1.name} does not carry -01-"
        assert "-01-" in f2.name, f"D12: {f2.name} does not carry -01-"

        # D12: Both front matters carry 'order: 01'
        f1_content = f1.read_text(encoding="utf-8")
        f2_content = f2.read_text(encoding="utf-8")
        assert re.search(
            r"^order:\s*01\b", f1_content, re.MULTILINE
        ), f"D12: {f1.name} does not carry 'order: 01' front matter"
        assert re.search(
            r"^order:\s*01\b", f2_content, re.MULTILINE
        ), f"D12: {f2.name} does not carry 'order: 01' front matter"

        # D11: Both files have mode 0o644
        mode1 = stat.S_IMODE(f1.stat().st_mode)
        mode2 = stat.S_IMODE(f2.stat().st_mode)
        assert mode1 == 0o644, f"D11: {f1.name} mode is {oct(mode1)}, expected 0o644"
        assert mode2 == 0o644, f"D11: {f2.name} mode is {oct(mode2)}, expected 0o644"

        # research index --check exits 0
        idx_check1 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "research",
                "index",
                "--check",
            ],
            cwd=fresh_target.target_dir,
            env=fresh_target.env,
            capture_output=True,
            text=True,
            preexec_fn=preexec,
        )
        assert (
            idx_check1.returncode == 0
        ), f"research index --check failed unexpectedly:\n{idx_check1.stdout}\n{idx_check1.stderr}"

        # Rewrite one file's front matter to 'order: 05' (leaving its filename -01-)
        f1_tampered = re.sub(
            r"^order:\s*01\b", "order: 05", f1_content, count=1, flags=re.MULTILINE
        )
        f1.write_text(f1_tampered, encoding="utf-8")

        # D10 check half (okw4ke): research index --check exits non-zero and names 'order'
        idx_check2 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "research",
                "index",
                "--check",
            ],
            cwd=fresh_target.target_dir,
            env=fresh_target.env,
            capture_output=True,
            text=True,
            preexec_fn=preexec,
        )
        assert (
            idx_check2.returncode != 0
        ), "D10: research index --check did not exit non-zero on order mismatch"
        combined_output = f"{idx_check2.stdout}\n{idx_check2.stderr}"
        assert (
            "order" in combined_output
        ), f"D10: research index --check output did not name 'order':\n{combined_output}"

    finally:
        # Clean up created files to leave target clean
        if f1.exists():
            f1.unlink()
        if f2.exists():
            f2.unlink()
        for idx_file in (research_dir / "INDEX.json", research_dir / "INDEX.md"):
            if idx_file.exists():
                idx_file.unlink()

    elapsed = time.perf_counter() - t0
    print(f"\nResearch composition test wall time: {elapsed:.2f}s")
