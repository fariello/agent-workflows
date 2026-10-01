"""Tests for selector type containment on mutating verbs (IPD eby93o).

Pins that a type-scoped mutating verb (e.g. `aw rename <type>`) refuses a path belonging
to a foreign artifact type rather than silently renaming that foreign artifact and rewriting
every citation of its old name across the repository.
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess

import pytest

from agent_workflows import cli, selectors, status_set


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def test_cross_type_rename_refuses_foreign_path_and_leaves_file_untouched(
    temp_git_repo: Path,
):
    """E-01 / V-01: A type-scoped verb handed a foreign-type path must refuse at exit 2, and the
    foreign artifact must remain untouched on disk (same path, same bytes).
    """
    repo = temp_git_repo
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / "20260929-demo-01-ab12cd-a-demo-plan.ipd.md"
    plan_content = (
        "# IPD: A demo plan\n\n"
        "- Date: 2026-09-29\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: ab12cd\n"
        "- Set: demo\n"
    )
    plan_path.write_text(plan_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(
            [
                "--no-interactive",
                "rename",
                "specs",
                str(plan_path),
                "--slug",
                "zzz",
                "--apply",
                "--dir",
                str(repo),
            ]
        )

    out = buf_out.getvalue() + buf_err.getvalue()
    assert rc == 2, f"Expected refusal rc=2, got rc={rc}. Output: {out}"
    assert "error: specs verb cannot act on" in out
    assert str(plan_path) in out
    assert (
        plan_path.exists()
    ), f"Plan file at {plan_path} was moved or removed! Output: {out}"
    assert (
        plan_path.read_text(encoding="utf-8") == plan_content
    ), "Plan file content was modified!"
    renamed_path = plans_dir / "20260929-demo-01-ab12cd-zzz.ipd.md"
    assert (
        not renamed_path.exists()
    ), f"Renamed plan file {renamed_path} should not exist!"


def test_cross_type_rename_does_not_rewrite_citations_of_foreign_artifact(
    temp_git_repo: Path,
):
    """E-02 / V-02: A wrong rename rewrites citations across the repository. Assert that an unrelated
    record's bytes are unchanged when a foreign path rename is attempted.
    """
    repo = temp_git_repo
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / "20260929-demo-01-ab12cd-a-demo-plan.ipd.md"
    plan_content = (
        "# IPD: A demo plan\n\n"
        "- Date: 2026-09-29\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: ab12cd\n"
        "- Set: demo\n"
    )
    plan_path.write_text(plan_content, encoding="utf-8")

    backlog_dir = repo / ".aw" / "records" / "backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    citing_path = backlog_dir / "20260929-demo-01-c1t301-citing-item.backlog.md"
    citing_content = (
        "# Backlog: Citing item\n\n"
        "- Date: 2026-09-29\n"
        "- Status: open\n"
        "- Id: c1t301\n\n"
        "See plan 20260929-demo-01-ab12cd-a-demo-plan.ipd.md for implementation details.\n"
    )
    citing_path.write_text(citing_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(
            [
                "--no-interactive",
                "rename",
                "specs",
                str(plan_path),
                "--slug",
                "zzz",
                "--apply",
                "--dir",
                str(repo),
            ]
        )

    assert rc == 2
    citing_bytes_after = citing_path.read_bytes()
    # The assertion is on the citing file's bytes, not on whether the rewriter was called.
    assert (
        citing_bytes_after == citing_content.encode("utf-8")
    ), f"Citing file bytes were modified! Content after:\n{citing_path.read_text(encoding='utf-8')}"


def test_cross_type_rename_refusal_cannot_be_overridden_by_force(temp_git_repo: Path):
    """E-03 / V-03: --force must NOT override the cross-type refusal."""
    repo = temp_git_repo
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / "20260929-demo-01-ab12cd-a-demo-plan.ipd.md"
    plan_content = (
        "# IPD: A demo plan\n\n"
        "- Date: 2026-09-29\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: ab12cd\n"
        "- Set: demo\n"
    )
    plan_path.write_text(plan_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(
            [
                "--no-interactive",
                "rename",
                "specs",
                str(plan_path),
                "--slug",
                "zzz",
                "--apply",
                "--force",
                "--dir",
                str(repo),
            ]
        )

    out = buf_out.getvalue() + buf_err.getvalue()
    assert rc == 2, f"--force should not override refusal, got rc={rc}. Output: {out}"
    assert "error: specs verb cannot act on" in out
    assert plan_path.exists()
    assert plan_path.read_text(encoding="utf-8") == plan_content


def test_fail_closed_when_record_dirs_empty(temp_git_repo: Path):
    """E-03 / V-03: In a repo with a plans tree and NO specs tree, aw rename specs <plan path>
    must fail closed (rc=2), name the type and path, mention that no specs records tree was found,
    and leave the plan untouched.
    """
    repo = temp_git_repo
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / "20260929-demo-01-ab12cd-a-demo-plan.ipd.md"
    plan_content = (
        "# IPD: A demo plan\n\n"
        "- Date: 2026-09-29\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: ab12cd\n"
        "- Set: demo\n"
    )
    plan_path.write_text(plan_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    # Verify specs records tree does NOT exist
    specs_dirs = selectors.record_dirs(repo, "specs")
    assert specs_dirs == [], f"Expected empty specs dirs, got {specs_dirs}"

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(
            [
                "--no-interactive",
                "rename",
                "specs",
                str(plan_path),
                "--slug",
                "zzz",
                "--apply",
                "--dir",
                str(repo),
            ]
        )

    out = buf_out.getvalue() + buf_err.getvalue()
    assert rc == 2
    assert "error: specs verb cannot act on" in out
    assert str(plan_path) in out
    assert "(no specs records tree found)" in out
    assert plan_path.exists()
    assert plan_path.read_text(encoding="utf-8") == plan_content


def test_six_type_refusal_matrix(temp_git_repo: Path):
    """E-05 / V-05: Defect is reachable through six verbs: specs, prompts, backlog, walkthroughs,
    roadmaps, releases. Show a foreign-type path is refused for each of the six.
    """
    repo = temp_git_repo
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / "20260929-demo-01-ab12cd-a-demo-plan.ipd.md"
    plan_content = (
        "# IPD: A demo plan\n\n"
        "- Date: 2026-09-29\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: ab12cd\n"
        "- Set: demo\n"
    )
    plan_path.write_text(plan_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    six_types = ["specs", "prompts", "backlog", "walkthroughs", "roadmaps", "releases"]
    for t in six_types:
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = cli.main(
                [
                    "--no-interactive",
                    "rename",
                    t,
                    str(plan_path),
                    "--slug",
                    "zzz",
                    "--apply",
                    "--dir",
                    str(repo),
                ]
            )
        out = buf_out.getvalue() + buf_err.getvalue()
        assert rc == 2, f"Type {t} expected refusal rc=2, got rc={rc}. Output: {out}"
        assert f"error: {t} verb cannot act on" in out
        assert str(plan_path) in out
        assert plan_path.exists()
        assert plan_path.read_text(encoding="utf-8") == plan_content


def test_must_not_refuse_matrix(temp_git_repo: Path):
    """E-04 / V-04: Must-not-refuse matrix.
    For specs and backlog:
      (a) repo-relative path reaches rename preview (rc=0)
      (b) absolute path reaches rename preview (rc=0)
      (c) id6 reaches rename preview (rc=0)
    For research:
      In selectors.resolve_for_mutation: (a) repo-relative path, (b) absolute path, (c) id6 all resolve.
      In CLI aw rename research: (c) id6 reaches rename preview (rc=0).
    For plans:
      (c) id6 reaches rename preview (rc=0)
      (a) repo-relative path -> rc=2, 'no plan has Id' (pins pre-existing refusal for Order 02)
      (b) absolute path -> rc=2, 'no plan has Id' (pins pre-existing refusal for Order 02)
    """
    repo = temp_git_repo

    # 1. Specs
    sdir = repo / ".aw" / "records" / "specs"
    sdir.mkdir(parents=True, exist_ok=True)
    spec = sdir / "20260929-sp0001-01-sp0001-test-spec.spec.md"
    spec.write_text(
        "# Spec: Test\n\n- Date: 2026-09-29\n- Status: draft\n- Id: sp0001\n",
        encoding="utf-8",
    )

    # 2. Backlog
    bdir = repo / ".aw" / "records" / "backlog"
    bdir.mkdir(parents=True, exist_ok=True)
    backlog = bdir / "20260929-bk0001-01-bk0001-test-item.backlog.md"
    backlog.write_text(
        "# Backlog: Test\n\n- Date: 2026-09-29\n- Status: open\n- Id: bk0001\n",
        encoding="utf-8",
    )

    # 3. Research
    rdir = repo / ".aw" / "records" / "research"
    rdir.mkdir(parents=True, exist_ok=True)
    research = rdir / "20260929-demoset-01-rs0001-test-research.findings.md"
    research.write_text(
        "---\nid: rs0001\nstatus: todo\n---\n# Research\n", encoding="utf-8"
    )

    # 4. Plans
    pdir = repo / ".aw" / "records" / "plans" / "pending"
    pdir.mkdir(parents=True, exist_ok=True)
    plan = pdir / "20260929-pl0001-01-pl0001-test-plan.ipd.md"
    plan.write_text(
        "# IPD: Test\n\n- Date: 2026-09-29\n- Status: pending\n- Id: pl0001\n- Set: pl0001\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    def run_cli(*args):
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = cli.main(["--no-interactive"] + list(args) + ["--dir", str(repo)])
        return rc, buf.getvalue()

    # Specs assertions
    rc, out = run_cli(
        "rename", "specs", str(spec.relative_to(repo)), "--slug", "newslug"
    )
    assert rc == 0 and "would rename" in out, f"specs relpath failed: rc={rc}, {out}"
    rc, out = run_cli("rename", "specs", str(spec.resolve()), "--slug", "newslug")
    assert rc == 0 and "would rename" in out, f"specs abspath failed: rc={rc}, {out}"
    rc, out = run_cli("rename", "specs", "sp0001", "--slug", "newslug")
    assert rc == 0 and "would rename" in out, f"specs id6 failed: rc={rc}, {out}"

    # Backlog assertions
    rc, out = run_cli(
        "rename", "backlog", str(backlog.relative_to(repo)), "--slug", "newslug"
    )
    assert rc == 0 and "would rename" in out, f"backlog relpath failed: rc={rc}, {out}"
    rc, out = run_cli("rename", "backlog", str(backlog.resolve()), "--slug", "newslug")
    assert rc == 0 and "would rename" in out, f"backlog abspath failed: rc={rc}, {out}"
    rc, out = run_cli("rename", "backlog", "bk0001", "--slug", "newslug")
    assert rc == 0 and "would rename" in out, f"backlog id6 failed: rc={rc}, {out}"

    # Research: resolve_for_mutation covers path and id6; CLI rename research covers id6
    paths, err = selectors.resolve_for_mutation(
        repo, "research", str(research.relative_to(repo))
    )
    assert err is None and len(paths) == 1 and paths[0].resolve() == research.resolve()
    paths, err = selectors.resolve_for_mutation(
        repo, "research", str(research.resolve())
    )
    assert err is None and len(paths) == 1 and paths[0].resolve() == research.resolve()
    paths, err = selectors.resolve_for_mutation(repo, "research", "rs0001")
    assert err is None and len(paths) == 1 and paths[0].resolve() == research.resolve()
    rc, out = run_cli("rename", "research", "rs0001", "--slug", "newslug")
    assert rc == 0 and "would rename" in out, f"research id6 failed: rc={rc}, {out}"

    # Plans: id6 succeeds; path selectors exhibit pre-existing refusal with "no plan has Id"
    rc, out = run_cli("rename", "plans", "pl0001", "--slug", "newslug")
    assert rc == 0 and "would rename" in out, f"plans id6 failed: rc={rc}, {out}"
    rc, out = run_cli(
        "rename", "plans", str(plan.relative_to(repo)), "--slug", "newslug"
    )
    assert (
        rc == 2 and "no plan has Id" in out
    ), f"plans relpath unexpected result: rc={rc}, {out}"
    rc, out = run_cli("rename", "plans", str(plan.resolve()), "--slug", "newslug")
    assert (
        rc == 2 and "no plan has Id" in out
    ), f"plans abspath unexpected result: rc={rc}, {out}"


def test_effzzi_research_roadmap_facet_resolves_by_id6(temp_git_repo: Path):
    """E-04 / V-04: The effzzi near-miss.
    Seed a research doc whose name carries the .roadmap.md facet.
    Assert status_set.detect_artifact_type returns 'roadmaps' (proving why type equality would fail!).
    Assert aw rename research <id6> resolves and reaches preview.
    """
    repo = temp_git_repo
    rdir = repo / ".aw" / "records" / "research" / "reference" / "202608"
    rdir.mkdir(parents=True, exist_ok=True)
    doc = rdir / "20260821-awoptimize-03-effzzi-optimal-arch.roadmap.md"
    doc.write_text(
        "---\n"
        "id: effzzi\n"
        "status: reference\n"
        "---\n"
        "# Research doc with roadmap facet\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    # 1. detect_artifact_type types it as 'roadmaps' because of .roadmap.md suffix
    detected = status_set.detect_artifact_type(doc, repo_root=repo)
    assert (
        detected == "roadmaps"
    ), f"Expected 'roadmaps' from detect_artifact_type, got {detected}"

    # 2. selectors.resolve_for_mutation resolves it under 'research'
    paths, err = selectors.resolve_for_mutation(repo, "research", "effzzi")
    assert err is None, f"resolve_for_mutation failed: {err}"
    assert len(paths) == 1
    assert paths[0].resolve() == doc.resolve()

    # 3. CLI aw rename research effzzi reaches preview
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        rc = cli.main(
            [
                "--no-interactive",
                "rename",
                "research",
                "effzzi",
                "--slug",
                "newslog",
                "--dir",
                str(repo),
            ]
        )
    out = buf.getvalue()
    assert rc == 0, f"Expected rc=0, got {rc}. Output: {out}"
    assert "would rename" in out


def test_setid_multi_target_resolves_all_members_without_force(temp_git_repo: Path):
    """E-04 / V-04: A setid naming several records of the requested type must still resolve
    to all of them without --force (intentional multi-target).
    """
    repo = temp_git_repo
    sdir = repo / ".aw" / "records" / "specs"
    sdir.mkdir(parents=True, exist_ok=True)
    spec1 = sdir / "20260929-demoset-01-sp0001-spec-one.spec.md"
    spec1.write_text(
        "# Spec: One\n\n- Date: 2026-09-29\n- Status: draft\n- Id: sp0001\n- Set: demoset\n",
        encoding="utf-8",
    )
    spec2 = sdir / "20260929-demoset-02-sp0002-spec-two.spec.md"
    spec2.write_text(
        "# Spec: Two\n\n- Date: 2026-09-29\n- Status: draft\n- Id: sp0002\n- Set: demoset\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    paths, err = selectors.resolve_for_mutation(repo, "specs", "demoset", force=False)
    assert err is None, f"Expected no error, got {err}"
    assert len(paths) == 2, f"Expected 2 paths, got {len(paths)}"
    resolved_names = {p.name for p in paths}
    assert resolved_names == {spec1.name, spec2.name}


def test_corpus_sweep_zero_false_refusals():
    """E-05 / V-05: Real corpus sweep proving zero false refusals.
    Every (type, own-file) pair in the repository must be accepted by is_path_in_record_dirs.
    """
    repo = Path(".").resolve()
    types = sorted(selectors.KNOWN_PRIMARY_TYPES)
    checked = 0
    wrongly_refused = 0

    for t in types:
        dirs = selectors.record_dirs(repo, t)
        for d in dirs:
            for p in d.rglob("*.md"):
                if not p.is_file():
                    continue
                checked += 1
                if not selectors.is_path_in_record_dirs(repo, t, p):
                    wrongly_refused += 1

    assert checked > 1000, f"Sanity check: expected >1000 records, checked {checked}"
    assert wrongly_refused == 0, f"Found {wrongly_refused} wrongly refused files!"


def test_read_side_resolve_and_find_unperturbed(temp_git_repo: Path):
    """E-05 / V-05: Prove the READ side is unperturbed.
    selectors.resolve still resolves a path selector across types (permissive read-side),
    and `aw find plans <path>` still works.
    """
    repo = temp_git_repo
    pdir = repo / ".aw" / "records" / "plans" / "pending"
    pdir.mkdir(parents=True, exist_ok=True)
    plan = pdir / "20260929-demo-01-ab12cd-a-demo-plan.ipd.md"
    plan.write_text(
        "# IPD: Demo\n\n- Date: 2026-09-29\n- Status: pending\n- Id: ab12cd\n- Set: demo\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    # 1. Read-side resolve is permissive: querying 'specs' for a plan path resolves with kind='path'
    res = selectors.resolve(repo, "specs", str(plan))
    assert res.kind == selectors.MATCH_PATH
    assert len(res.paths) == 1
    assert res.paths[0].resolve() == plan.resolve()

    # 2. aw find plans <path> resolves the plan
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        rc = cli.main(["find", "plans", str(plan), "--dir", str(repo)])
    out = buf.getvalue()
    assert rc == 0, f"aw find plans failed: rc={rc}, {out}"
    assert "ab12cd" in out
