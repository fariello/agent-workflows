"""Behavioral tests for tools/aw_repo_survey.py: run it as a subprocess and read its JSON output."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support import clean_git_env

pytestmark = pytest.mark.core

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "aw_repo_survey.py"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=cwd, env=clean_git_env(), check=True, capture_output=True
    )


def _repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "t@example.com")
    _git(path, "config", "user.name", "T")
    return path


def _commit(path: Path) -> None:
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", "x")


def _run_survey(
    tmp_path: Path,
    *args: str,
    out_rel: str | None = "out.json",
    isolated: bool = True,
) -> tuple[dict, str]:
    """Run the survey. `isolated` adds `--no-run-aw --offline` unless a test opts in to either."""
    out = tmp_path / (out_rel or "unused")
    home_dir = tmp_path / "home"
    home_dir.mkdir(exist_ok=True)
    home_str = str(home_dir)
    # Set USERPROFILE alongside HOME so Path.home() resolves to tmp_path/home on Windows too.
    env = clean_git_env()
    env["HOME"] = home_str
    env["USERPROFILE"] = home_str
    for k in ("AW_CONFIG_DIR", "XDG_CONFIG_HOME", "AW_HOME", "HOMEDRIVE", "HOMEPATH"):
        env.pop(k, None)
    res = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            *args,
            *(["--no-run-aw", "--offline"] if isolated else []),
            *(["-o", str(out)] if out_rel else []),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    if out_rel is None:
        [out] = (home_dir / "aw-survey").glob("*.json")
    return json.loads(out.read_text(encoding="utf-8")), res.stderr


def _run(tmp_path: Path, *args: str) -> dict:
    return _run_survey(tmp_path, *args, out_rel="out.json")[0]


def _files(repo: dict, tree: str) -> dict:
    return {f["path"]: f for f in repo["trees"][tree]["files"]}


def test_classifies_names_and_bullets_in_both_trees(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "src" / "r1")
    plans = repo / ".aw" / "records" / "plans" / "executed"
    plans.mkdir(parents=True)
    (plans / "20261101-setx-01-ab12cd-do-thing.ipd.md").write_text(
        "# IPD: Do thing\n\n- Id: ab12cd\n- Status: executed\n\n## Concern\n\n- Id: zz9999\n",
        encoding="utf-8",
    )
    legacy = repo / ".agents" / "plans" / "executed"
    legacy.mkdir(parents=True)
    (legacy / "20250101-1200-01-old-plan.md").write_text(
        "# Old\n\n- Status: executed\n", encoding="utf-8"
    )
    (legacy / "notes.md").write_text("no bullets\n", encoding="utf-8")
    research = repo / ".aw" / "records" / "research"
    research.mkdir(parents=True)
    (research / "20261101-setx-02-rs0001-topic.model.findings.md").write_text(
        "---\nid: rs0001\nset: setx\n---\n# Topic\n", encoding="utf-8"
    )
    runs = repo / ".aw" / "records" / "runs" / "run-1"
    runs.mkdir(parents=True)
    (runs / "state.json").write_text("{}", encoding="utf-8")
    _commit(repo)
    (repo / ".aw" / "records" / "plans" / "executed" / "untracked.md").write_text(
        "x\n", encoding="utf-8"
    )

    doc = _run(tmp_path, str(repo), "--no-registry")

    assert doc["masked"] is False
    assert [r["path"] for r in doc["repos"]] == [str(repo.resolve())]
    r = doc["repos"][0]
    assert sorted(r["trees"]) == [".agents", ".aw"]

    aw = _files(r, ".aw")
    plan = aw["records/plans/executed/20261101-setx-01-ab12cd-do-thing.ipd.md"]
    assert plan["grammar"] == "clustered"
    assert plan["id6"] == "ab12cd" and plan["facet"] == "ipd"
    assert plan["bullets"]["head"] == {"Id": "ab12cd", "Status": "executed"}
    assert plan["bullets"]["ids_after_head"] == ["zz9999"]
    assert plan["id_valid"] is True and plan["id_matches_name"] is True
    assert plan["tracked"] is True and len(plan["sha256"]) == 64
    assert plan["title"] == "IPD: Do thing"

    assert aw["records/plans/executed/untracked.md"]["tracked"] is False
    res = aw["records/research/20261101-setx-02-rs0001-topic.model.findings.md"]
    assert res["bullets"]["yaml_front_matter"] == {"id": "rs0001", "set": "setx"}
    assert res["id_matches_name"] is True

    # Machine-written run directories are counted, not listed.
    assert not any(p.startswith("records/runs/") for p in aw)
    assert r["trees"][".aw"]["bulk_dirs"]["records/runs"]["files"] == 1

    ag = _files(r, ".agents")
    assert (
        ag["plans/executed/20250101-1200-01-old-plan.md"]["grammar"]
        == "legacy-timestamp"
    )
    assert ag["plans/executed/20250101-1200-01-old-plan.md"]["bullets"]["head"] == {
        "Status": "executed"
    }
    assert ag["plans/executed/notes.md"]["grammar"] == "other"


def test_scan_finds_repos_and_skips_listed_paths_that_are_not_repos(
    tmp_path: Path,
) -> None:
    a = _repo(tmp_path / "src" / "a")
    (a / ".aw").mkdir()
    (a / ".aw" / "x.md").write_text("x\n", encoding="utf-8")
    deep = _repo(tmp_path / "src" / "group" / "b")
    (deep / ".agents").mkdir()
    (deep / ".agents" / "y.md").write_text("y\n", encoding="utf-8")
    plain = _repo(tmp_path / "src" / "plain")
    (plain / "README.md").write_text("r\n", encoding="utf-8")

    doc = _run(tmp_path, str(plain), "--scan", str(tmp_path / "src"), "--no-registry")

    assert [r["path"] for r in doc["repos"]] == sorted(
        [str(a.resolve()), str(deep.resolve())]
    )
    assert doc["skipped"] == [
        {
            "path": str(plain.resolve()),
            "found_via": "argument",
            "reason": "no .git with .aw/ or .agents/",
        }
    ]


def test_registry_and_default_companion_are_surveyed(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "src" / "r2")
    (repo / ".aw" / "config").mkdir(parents=True)
    (repo / ".aw" / "config" / "project.json").write_text(
        json.dumps({"records_backend": "companion"}), encoding="utf-8"
    )
    _commit(repo)
    comp = _repo(tmp_path / "src" / "r2.aw")
    (comp / "records" / "plans" / "pending").mkdir(parents=True)
    (
        comp / "records" / "plans" / "pending" / "20261101-s-01-cc0001-c.ipd.md"
    ).write_text("# C\n\n- Id: cc0001\n- Status: draft\n", encoding="utf-8")
    _commit(comp)
    cfg = tmp_path / "home" / ".config" / "agent-workflows"
    cfg.mkdir(parents=True)
    (cfg / "config.json").write_text(
        json.dumps({"repos": {"installed": [str(repo), str(tmp_path / "gone")]}}),
        encoding="utf-8",
    )

    doc = _run(tmp_path)

    r = next(x for x in doc["repos"] if x["path"] == str(repo.resolve()))
    assert "user-config:installed" in r["found_via"]
    assert r["records_backend"] == "companion"
    [c] = r["companions"]
    assert c["source"] == "default:<repo>.aw" and c["is_git"] is True
    names = {f["path"]: f for f in c["tree"]["files"]}
    assert (
        names["records/plans/pending/20261101-s-01-cc0001-c.ipd.md"]["tracked"] is True
    )
    assert {
        "path": str((tmp_path / "gone").resolve()),
        "found_via": "user-config:installed",
        "reason": "not a directory",
    } in doc["skipped"]


def _run_full(tmp_path: Path, *args: str) -> tuple[dict, str]:
    return _run_survey(tmp_path, *args, out_rel="survey-out/out.json")


def _with_worktree(tmp_path: Path) -> tuple[Path, Path]:
    main = _repo(tmp_path / "src" / "m")
    (main / ".aw").mkdir()
    (main / ".aw" / "x.md").write_text("x\n", encoding="utf-8")
    _commit(main)
    wt = tmp_path / "src" / "m-wt"
    _git(main, "worktree", "add", "-q", str(wt), "-b", "side")
    return main, wt


def test_linked_worktree_skipped_by_default(tmp_path: Path) -> None:
    main, wt = _with_worktree(tmp_path)

    doc, _ = _run_full(tmp_path, "--scan", str(tmp_path / "src"), "--no-registry")

    assert [r["path"] for r in doc["repos"]] == [str(main.resolve())]
    [skip] = doc["skipped"]
    assert skip["path"] == str(wt.resolve())
    assert skip["reason"].startswith("linked worktree of ")
    assert "--include-worktrees" in skip["reason"]


def test_include_worktrees_surveys_them(tmp_path: Path) -> None:
    main, wt = _with_worktree(tmp_path)

    doc, _ = _run_full(
        tmp_path,
        "--scan",
        str(tmp_path / "src"),
        "--no-registry",
        "--include-worktrees",
    )

    assert sorted(r["path"] for r in doc["repos"]) == sorted(
        [str(main.resolve()), str(wt.resolve())]
    )
    assert doc["skipped"] == []


def test_config_search_roots_are_scanned_and_relative_ones_ignored(
    tmp_path: Path,
) -> None:
    root = tmp_path / "elsewhere"
    repo = _repo(root / "r")
    (repo / ".agents").mkdir()
    (repo / ".agents" / "y.md").write_text("y\n", encoding="utf-8")
    cfg = tmp_path / "home" / ".config" / "agent-workflows"
    cfg.mkdir(parents=True)
    (cfg / "config.json").write_text(
        json.dumps({"repos": {"search": [str(root), "rel/dir"]}}), encoding="utf-8"
    )

    doc, _ = _run_full(tmp_path, "--scan", str(tmp_path / "home"))

    assert [r["path"] for r in doc["repos"]] == [str(repo.resolve())]
    assert any(
        s["root"] == str(root.resolve()) and s["found"] == 1 and "search" in s["source"]
        for s in doc["scans"]
    )
    [ign] = doc["ignored_search_roots"]
    assert ign["entry"] == "rel/dir" and ign["reason"] == "relative path"


def test_stderr_lists_created_files(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "src" / "r")
    (repo / ".aw").mkdir()

    _, err = _run_full(tmp_path, str(repo), "--no-registry")

    out = tmp_path / "survey-out" / "out.json"
    assert "Files created (UNMASKED; do not commit or share):" in err
    assert f"{tmp_path / 'survey-out'}/ (directory)" in err
    assert f"{out} (" in err and "bytes)" in err


def _remote_pair(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A bare remote, a clone with `.aw/`, and a second clone used to advance the remote."""
    seed = _repo(tmp_path / "seed")
    (seed / ".aw").mkdir()
    (seed / ".aw" / "a.md").write_text("a\n", encoding="utf-8")
    _commit(seed)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "clone", "-q", "--bare", str(seed), str(bare))
    work = tmp_path / "src" / "work"
    _git(tmp_path, "clone", "-q", str(bare), str(work))
    _git(work, "config", "user.email", "t@example.com")
    _git(work, "config", "user.name", "T")
    other = tmp_path / "other"
    _git(tmp_path, "clone", "-q", str(bare), str(other))
    _git(other, "config", "user.email", "t@example.com")
    _git(other, "config", "user.name", "T")
    return bare, work, other


def test_git_state_reports_up_to_date_then_push_and_pull_needs(tmp_path: Path) -> None:
    _, work, other = _remote_pair(tmp_path)

    doc, _ = _run_survey(
        tmp_path, str(work), "--no-registry", "--no-run-aw", isolated=False
    )
    g = doc["repos"][0]["git"]
    assert g["current_branch_state"] == "up-to-date"
    assert g["needs"] == [] and g["dirty"] is False
    assert g["remotes"]["origin"]["reachable"] is True
    assert g["remotes"]["origin"]["default_branch"] == "main"

    (work / "local.txt").write_text("l\n", encoding="utf-8")
    _commit(work)
    (work / "dirty.txt").write_text("d\n", encoding="utf-8")
    (other / "remote.txt").write_text("r\n", encoding="utf-8")
    _commit(other)
    _git(other, "push", "-q", "origin", "main")
    _git(work, "checkout", "-q", "-b", "scratch")
    _git(work, "checkout", "-q", "main")

    doc, err = _run_survey(
        tmp_path, str(work), "--no-registry", "--no-run-aw", isolated=False
    )
    g = doc["repos"][0]["git"]
    main = next(b for b in g["branches"] if b["name"] == "main")
    # The remote moved to a commit this clone never fetched: behind by an unknown count.
    assert main["live"]["state"] == "behind-unfetched"
    assert g["working_tree"]["untracked"] == 1 and g["dirty"] is True
    assert "commit-or-clean" in g["needs"] and "pull:main" in g["needs"]
    scratch = next(b for b in g["branches"] if b["name"] == "scratch")
    # It holds the unpushed local commit and has no upstream, so it exists nowhere else.
    assert scratch["live"]["state"] == "local-only"
    assert "push:scratch" in g["needs"]
    assert "Repositories needing attention:" in err

    _git(work, "fetch", "-q")
    doc, _ = _run_survey(
        tmp_path, str(work), "--no-registry", "--no-run-aw", isolated=False
    )
    main = next(b for b in doc["repos"][0]["git"]["branches"] if b["name"] == "main")
    assert main["live"] == {
        "state": "diverged",
        "ahead": 1,
        "behind": 1,
        "remote_sha": main["live"]["remote_sha"],
    }


def test_offline_does_not_contact_remotes(tmp_path: Path) -> None:
    _, work, _ = _remote_pair(tmp_path)

    doc, _ = _run_survey(tmp_path, str(work), "--no-registry")

    g = doc["repos"][0]["git"]
    assert g["online_checked"] is False
    assert "reachable" not in g["remotes"]["origin"]
    assert g["current_branch_state"] == "not-checked"


def _fake_aw(tmp_path: Path, touch: bool) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    # Windows CreateProcess cannot execute extensionless shebang scripts directly; wrap in .cmd.
    script = bin_dir / ("aw.py" if sys.platform == "win32" else "aw")
    body = [
        "#!" + sys.executable,
        "import json, pathlib, sys",
        "args = sys.argv[1:]",
        "if args == ['--version']:",
        "    print('agent-workflows 9.9.9'); sys.exit(0)",
        "if args[0] == 'check':",
        "    print(json.dumps({'kind': 'result', 'exit': 1, 'findings': 1,",
        "        'diagnostics': [{'location': 'x.md', 'rule': 'check.name-nonconformant'}]}))",
        "    sys.exit(1)",
        "if args[0] == 'attention':",
        "    print(json.dumps({'valid': False, 'items': [{'id': 'ab12cd', 'path': 'p',",
        "        'tree': 'plans', 'native_status': 'draft', 'attention_class': 'ready',",
        "        'detail_text': 'dropped'}], 'violations': [{'rule': 'attention.missing-status'}]}))",
        "    sys.exit(1)",
    ]
    if touch:
        body.append("pathlib.Path('.aw/written-by-doctor.txt').write_text('x')")
    body += ["print('not json'); sys.stderr.write('boom'); sys.exit(2)"]
    script.write_text("\n".join(body) + "\n", encoding="utf-8")
    if sys.platform == "win32":
        cmd = bin_dir / "aw.cmd"
        cmd.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
        return cmd
    script.chmod(0o755)
    return script


def test_aw_runs_recorded_and_side_effects_detected(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "src" / "r")
    (repo / ".aw").mkdir()
    (repo / ".aw" / "a.md").write_text("a\n", encoding="utf-8")
    _commit(repo)
    aw = _fake_aw(tmp_path, touch=True)

    doc, err = _run_survey(
        tmp_path,
        str(repo),
        "--no-registry",
        "--offline",
        "--aw",
        str(aw),
        isolated=False,
    )

    assert doc["aw"]["version"] == "agent-workflows 9.9.9"
    runs = doc["repos"][0]["aw_runs"]
    cmds = runs["commands"]
    assert cmds["check"]["exit"] == 1
    assert cmds["check"]["result"]["diagnostics"] == [
        {"location": "x.md", "rule": "check.name-nonconformant"}
    ]
    att = cmds["attention"]["result"]
    assert att["valid"] is False and att["item_count"] == 1
    assert att["violations"] == [{"rule": "attention.missing-status"}]
    assert "detail_text" not in att["items"][0]
    assert cmds["doctor"]["exit"] == 2
    assert cmds["doctor"]["stdout_head"].startswith("not json")
    assert cmds["doctor"]["stderr_tail"] == "boom"
    se = runs["side_effects"]
    assert se["git_status_added"] == ["?? .aw/written-by-doctor.txt"]
    assert str(repo.resolve() / ".aw" / "written-by-doctor.txt") in se["files_modified"]
    assert "WARNING: aw commands changed files in:" in err


def test_aw_runs_clean_when_aw_writes_nothing_and_skipped_with_no_run_aw(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "src" / "r")
    (repo / ".aw").mkdir()
    (repo / ".aw" / "a.md").write_text("a\n", encoding="utf-8")
    _commit(repo)
    aw = _fake_aw(tmp_path, touch=False)

    doc, err = _run_survey(
        tmp_path,
        str(repo),
        "--no-registry",
        "--offline",
        "--aw",
        str(aw),
        isolated=False,
    )
    assert not any(doc["repos"][0]["aw_runs"]["side_effects"].values())
    assert "WARNING" not in err

    doc, _ = _run_survey(tmp_path, str(repo), "--no-registry")
    assert "aw_runs" not in doc["repos"][0]
    assert doc["aw"] == {"requested": False}


def test_default_output_name_sorts_by_date_then_host_then_time(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "src" / "r")
    (repo / ".aw").mkdir()

    doc, err = _run_survey(tmp_path, str(repo), "--no-registry", out_rel=None)

    [out] = (tmp_path / "home" / "aw-survey").glob("*.json")
    gen = doc["generated_at"]
    assert out.name == f"aw-repo-survey-{gen[:8]}-{doc['host']}-{gen[9:15]}.json"
    assert str(out) in err
