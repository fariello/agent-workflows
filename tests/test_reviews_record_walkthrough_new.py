"""Behavioral tests for the dormant `aw reviews record` and `aw walkthrough new` commands (IPD `724acb`).

Spec `4sd62s` 4.1a (typed review events), 4.2 (review payload, SHORT DESCRIPTION) and 4.6 (a
walkthrough needs a log). Each migrated fixture is a real `git init` repository under `tmp_path`
whose `project.json` carries `metadata_schema: 2` and whose subject plan has a
`.aw/records/meta/<id6>.jsonl` log written by `artifact_meta.create`; each unmigrated fixture has no
stamp, which is the state of every repository before the cutover. The tests drive the real CLI
through `cli.main` and assert on exit codes, the emitted agent record, the bytes of the log, and the
files on disk.

Node names carry `reviews_record` or `walkthrough` so the plan's `-k` selections pick them.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows import cli, meta_cli

pytestmark = pytest.mark.core

_PLAN_ID = "ab12cd"
_SPEC_ID = "sp34ef"
_PLAN_PATH = "plans/pending/20261109-demo-01-ab12cd-sample.ipd.md"
_SPEC_PATH = "specs/draft/20261109-sp34ef-01-sp34ef-sample.spec.md"
_GATE = "APPROVE WITH REVISIONS APPLIED"
_REFINE = "REVIEWED - MATERIAL CHANGES APPLIED"


def _git(repo: Path, *args: str) -> None:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr}"


def _init_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, schema: Optional[int] = 2
) -> Path:
    monkeypatch.setenv("AW_HOME", str(tmp_path / "aw_home"))
    repo = tmp_path / "repo"
    (repo / ".aw" / "records" / "meta").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test Agent")
    _git(repo, "config", "user.email", "test-agent@example.com")
    if schema is not None:
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            json.dumps({"metadata_schema": schema}) + "\n", encoding="utf-8"
        )
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _create(repo: Path, id6: str, kind: str, dest: str) -> None:
    fields = {"status": "draft", "title": "sample"}
    if kind == "ipd":
        fields.update({"set": "demo", "order": 1})
    res = meta.create(
        id6,
        kind,
        fields,
        "# sample\n",
        destination=dest,
        project_context=meta_cli.meta_context(repo),
        actor={"tool": "aw test"},
    )
    assert res.get("committed"), res


@pytest.fixture
def migrated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = _init_repo(tmp_path, monkeypatch)
    _create(repo, _PLAN_ID, "ipd", _PLAN_PATH)
    _create(repo, _SPEC_ID, "spec", _SPEC_PATH)
    return repo


def _log(repo: Path, id6: str) -> Path:
    return repo / ".aw" / "records" / "meta" / f"{id6}.jsonl"


def _events(repo: Path, id6: str) -> List[Dict]:
    return [
        json.loads(line)
        for line in _log(repo, id6).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _agent(capsys: pytest.CaptureFixture[str], argv: List[str]) -> tuple:
    rc = cli.main(argv + ["--agent"])
    out = capsys.readouterr().out
    recs = [json.loads(line) for line in out.splitlines() if line.strip()]
    assert recs, f"no agent record for {argv}"
    return rc, recs[-1]


def _rules(rec: Dict) -> List[str]:
    return [d["rule"] for d in rec.get("diagnostics", [])]


def _snapshot(root: Path) -> Dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def _record_argv(repo: Path, *extra: str, subject: str = _PLAN_ID) -> List[str]:
    return ["reviews", "record", subject, *extra, "--dir", str(repo)]


# --------------------------------------------------------------------------------------------------
# aw reviews record
# --------------------------------------------------------------------------------------------------


def test_reviews_record_appends_one_gate_event_with_readiness(migrated, capsys):
    before = _events(migrated, _PLAN_ID)
    rc, rec = _agent(
        capsys,
        _record_argv(
            migrated,
            "--round",
            "1",
            "--kind",
            "gate",
            "--verdict",
            _GATE,
            "--readiness",
            "go-pending-approval",
            "--review-depth",
            "standard",
            "--reviewer",
            "host/model",
        ),
    )
    assert rc == 0
    assert rec["kind"] == "result" and rec["outcome"] == "ok" and rec["exit"] == 0
    assert rec["applied"] is True
    after = _events(migrated, _PLAN_ID)
    assert after[: len(before)] == before
    assert len(after) == len(before) + 1
    ev = after[-1]
    assert ev["op"] == "review"
    assert ev["seq"] == before[-1]["seq"] + 1
    assert ev["round"] == 1 and ev["review_kind"] == "gate"
    assert ev["verdict"] == _GATE
    assert ev["readiness"] == "go-pending-approval"
    assert ev["review_depth"] == "standard"
    assert ev["reviewer"] == "host/model"
    assert ev["actor"] == {"tool": "aw reviews record"}
    state = meta.read(_PLAN_ID, project_context=meta_cli.meta_context(migrated))
    assert state.fields["readiness"] == "go-pending-approval"
    assert state.fields["review_depth"] == "standard"


def test_reviews_record_refinement_rounds_append_in_seq_order(migrated, capsys):
    for n in (1, 2, 3):
        rc, _ = _agent(
            capsys,
            _record_argv(
                migrated,
                "--round",
                str(n),
                "--kind",
                "refinement",
                "--verdict",
                _REFINE,
                subject=_SPEC_ID,
            ),
        )
        assert rc == 0
    reviews = [e for e in _events(migrated, _SPEC_ID) if e["op"] == "review"]
    assert [e["round"] for e in reviews] == [1, 2, 3]
    assert all(e["review_kind"] == "refinement" for e in reviews)
    assert all("readiness" not in e for e in reviews)
    seqs = [e["seq"] for e in _events(migrated, _SPEC_ID)]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)


@pytest.mark.parametrize(
    "extra, needle",
    [
        (
            ["--kind", "refinement", "--verdict", _REFINE, "--readiness", "go"],
            "reviews-record.readiness-on-refinement",
        ),
        (["--kind", "gate", "--verdict", _REFINE], "reviews-record.verdict-vocabulary"),
        (
            ["--kind", "refinement", "--verdict", "APPROVE"],
            "reviews-record.verdict-vocabulary",
        ),
        (["--kind", "gate", "--verdict", "LGTM"], "reviews-record.verdict-vocabulary"),
        (
            ["--kind", "gate", "--verdict", "APPROVE", "--readiness", "maybe"],
            "reviews-record.readiness-vocabulary",
        ),
        (
            ["--kind", "gate", "--verdict", "APPROVE", "--review-depth", "deep"],
            "reviews-record.review-depth-vocabulary",
        ),
    ],
    ids=[
        "refinement-readiness",
        "gate-with-refinement-verdict",
        "refinement-with-gate-verdict",
        "off-vocabulary-verdict",
        "unknown-readiness",
        "unknown-review-depth",
    ],
)
def test_reviews_record_refuses_off_vocabulary_payload_and_writes_nothing(
    migrated, capsys, extra, needle
):
    before = _snapshot(migrated)
    rc, rec = _agent(capsys, _record_argv(migrated, "--round", "1", *extra))
    assert rc == 2
    assert rec["exit"] == 2 and rec["outcome"] == "cannot-run"
    assert _rules(rec) == [needle]
    assert _snapshot(migrated) == before


def test_reviews_record_refuses_readiness_for_a_spec_subject(migrated, capsys):
    before = _events(migrated, _SPEC_ID)
    rc, rec = _agent(
        capsys,
        _record_argv(
            migrated,
            "--round",
            "1",
            "--kind",
            "gate",
            "--verdict",
            "APPROVE",
            "--readiness",
            "go",
            subject=_SPEC_ID,
        ),
    )
    assert rc == 2
    assert _rules(rec) == ["reviews-record.readiness-not-plan"]
    assert _events(migrated, _SPEC_ID) == before


def test_reviews_record_refuses_a_duplicate_round(migrated, capsys):
    argv = _record_argv(
        migrated, "--round", "1", "--kind", "gate", "--verdict", "APPROVE"
    )
    assert _agent(capsys, argv)[0] == 0
    before = _events(migrated, _PLAN_ID)
    rc, rec = _agent(capsys, argv)
    assert rc == 2
    assert _rules(rec) == ["reviews-record.duplicate-round"]
    assert _events(migrated, _PLAN_ID) == before
    # A second review FILE (distinct review_ref) may carry its own round 1.
    rc, _ = _agent(
        capsys, argv[:-2] + ["--review-ref", "second-file", "--dir", str(migrated)]
    )
    assert rc == 0
    assert len(_events(migrated, _PLAN_ID)) == len(before) + 1


def test_reviews_record_refuses_a_subject_without_a_log(migrated, capsys):
    before = _snapshot(migrated)
    rc, rec = _agent(
        capsys,
        _record_argv(
            migrated,
            "--round",
            "1",
            "--kind",
            "gate",
            "--verdict",
            "APPROVE",
            subject="zz99zz",
        ),
    )
    assert rc == 2
    assert _rules(rec) == ["reviews-record.no-log"]
    assert _snapshot(migrated) == before


def test_reviews_record_refuses_unmigrated_repo_naming_the_migration(
    tmp_path, monkeypatch, capsys
):
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    before = _snapshot(repo)
    rc = cli.main(
        _record_argv(repo, "--round", "1", "--kind", "gate", "--verdict", "APPROVE")
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "aw migrate metadata" in err
    assert _snapshot(repo) == before


def test_reviews_record_refuses_schema_one_under_agent(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path, monkeypatch, schema=1)
    before = _snapshot(repo)
    rc, rec = _agent(
        capsys,
        _record_argv(repo, "--round", "1", "--kind", "gate", "--verdict", "APPROVE"),
    )
    assert rc == 2 and rec["outcome"] == "cannot-run"
    assert _rules(rec) == ["metadata-schema-unmigrated"]
    assert rec["next"] == "aw migrate metadata"
    assert _snapshot(repo) == before


def test_reviews_record_human_success_line(migrated, capsys):
    rc = cli.main(
        _record_argv(migrated, "--round", "1", "--kind", "gate", "--verdict", "APPROVE")
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert out.startswith("aw reviews record: recorded review round 1 (gate): APPROVE")


# --------------------------------------------------------------------------------------------------
# aw walkthrough new
# --------------------------------------------------------------------------------------------------


def _walkthrough_argv(repo: Path, *extra: str) -> List[str]:
    return [
        "walkthrough",
        "new",
        "--set",
        "demo",
        "--order",
        "2",
        "--target",
        _PLAN_ID,
        "--slug",
        "cutover-notes",
        *extra,
        "--dir",
        str(repo),
    ]


def test_walkthrough_new_creates_file_and_log(migrated, capsys):
    rc, rec = _agent(
        capsys,
        _walkthrough_argv(migrated, "--summary", "How the cutover was verified."),
    )
    assert rc == 0 and rec["outcome"] == "ok"
    new_id6 = rec["target"]
    wdir = migrated / ".aw" / "records" / "walkthroughs"
    files = list(wdir.glob("*.walkthrough.md"))
    assert len(files) == 1
    name = files[0].name
    assert name.endswith(f"-demo-02-{new_id6}-cutover-notes.walkthrough.md")
    text = files[0].read_text(encoding="utf-8")
    assert f"id: {new_id6}" in text
    assert "How the cutover was verified." in text
    events = _events(migrated, new_id6)
    assert len(events) == 1
    create = events[0]
    assert create["op"] == "create"
    assert create["path"] == f"walkthroughs/{name}"
    assert create["fields"]["type"] == "walkthrough"
    assert create["fields"]["target_id"] == _PLAN_ID
    assert create["fields"]["set"] == "demo" and create["fields"]["order"] == 2
    assert create["fields"]["short_description"] == "How the cutover was verified."
    state = meta.read(new_id6, project_context=meta_cli.meta_context(migrated))
    assert state.type == "walkthrough"
    assert state.short_description == "How the cutover was verified."
    # The walkthrough is not an orphan: `aw check meta` reports it clean.
    rc, rec = _agent(capsys, ["check", "meta", "--dir", str(migrated)])
    assert rc == 0, rec


def test_walkthrough_new_without_summary_logs_no_short_description(migrated, capsys):
    rc, rec = _agent(capsys, _walkthrough_argv(migrated))
    assert rc == 0
    create = _events(migrated, rec["target"])[0]
    assert "short_description" not in create["fields"]


@pytest.mark.parametrize(
    "mutate, needle",
    [
        (lambda a: a[:7] + ["zz99zz"] + a[8:], "walkthrough-new.target-no-log"),
        (lambda a: a[:7] + ["NOT-ID"] + a[8:], "walkthrough-new.invalid-target"),
        (lambda a: a[:5] + ["0"] + a[6:], "walkthrough-new.bad-order"),
        (lambda a: a[:9] + ["!!!"] + a[10:], "walkthrough-new.bad-slug"),
        (
            lambda a: a[:-2] + ["--summary", "two\nlines"] + a[-2:],
            "walkthrough-new.unsafe-summary",
        ),
    ],
    ids=[
        "target-without-log",
        "bad-target",
        "zero-order",
        "empty-slug",
        "multiline-summary",
    ],
)
def test_walkthrough_new_refuses_bad_input_and_writes_nothing(
    migrated, capsys, mutate, needle
):
    before = _snapshot(migrated)
    rc, rec = _agent(capsys, mutate(_walkthrough_argv(migrated)))
    assert rc == 2 and rec["outcome"] == "cannot-run"
    assert _rules(rec) == [needle]
    assert _snapshot(migrated) == before


def test_walkthrough_new_refuses_unmigrated_repo_and_writes_nothing(
    tmp_path, monkeypatch, capsys
):
    repo = _init_repo(tmp_path, monkeypatch, schema=None)
    before = _snapshot(repo)
    home_before = _snapshot(tmp_path)
    rc = cli.main(_walkthrough_argv(repo))
    err = capsys.readouterr().err
    assert rc == 2
    assert "aw migrate metadata" in err
    assert _snapshot(repo) == before
    assert _snapshot(tmp_path) == home_before
    assert not (repo / ".aw" / "records" / "walkthroughs").exists()


def test_walkthrough_new_refuses_schema_one_under_agent(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path, monkeypatch, schema=1)
    before = _snapshot(tmp_path)
    rc, rec = _agent(capsys, _walkthrough_argv(repo))
    assert rc == 2 and rec["outcome"] == "cannot-run"
    assert _rules(rec) == ["metadata-schema-unmigrated"]
    assert rec["next"] == "aw migrate metadata"
    assert _snapshot(tmp_path) == before


def test_walkthrough_family_root_without_subcommand_is_usage_refusal(capsys):
    rc, rec = _agent(capsys, ["walkthrough"])
    assert rc == 2 and rec["outcome"] == "cannot-run"
