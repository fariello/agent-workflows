"""Default-visible preview/apply scaffolding parity tests (IPD 3pwpq1).

Covers eight properties:
(1) Parity property: preview's proposed key set for a fresh repo is a superset of the
    declarative scaffolding an apply writes, with the residual containing ONLY the deliberately
    excluded classes asserted via an explicit allow-list.
(2) Zero-byte member coverage: every .gitkeep an apply writes appears in the preview diff headers,
    asserted by path and not merely by count.
(3) Side-effect freedom: collect_scaffold_members writes no files and creates no directories.
(4) Idempotence: --diff against an already-installed repo reports no changes.
(5) Layout correctness: a legacy target produces the legacy target set and no .aw/ paths.
(6) Defensive template-miss omission: an unreadable template results in omission rather than invented content.
(7) No false overwrite: customized scaffolding on an installed repo is never previewed as an overwrite diff.
(8) Overwrite members still diff: modified body members still produce Diff headers.

Behavioral only: drives real engine functions and CLI arguments without inspect, ast,
production-source substring matching, or symbol counting (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import engine


def _run_diff(repo: Path) -> str:
    """Run engine --diff on repo and return stdout text."""
    args = engine.parse_args(["--repo", str(repo), "--diff", "--no-color"])
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = engine.run(args)
    assert rc == 0, f"engine.run --diff failed with returncode {rc}"
    return buf.getvalue()


def _extract_diff_headers(out: str) -> set[str]:
    """Extract set of repo-relative paths from 'Diff: <rel>' lines."""
    headers: set[str] = set()
    for line in out.splitlines():
        if line.startswith("Diff: "):
            headers.add(line[6:].strip())
    return headers


def test_preview_proposed_set_is_superset_of_declarative_scaffolding_parity(
    tmp_path: Path,
) -> None:
    """Property 1: preview headers on a fresh repo match apply files except for the 8 excluded paths."""
    source_root = engine.resolve_source_root(None)
    preview_repo = tmp_path / "preview_repo"
    apply_repo = tmp_path / "apply_repo"
    preview_repo.mkdir()
    apply_repo.mkdir()

    preview_headers = _extract_diff_headers(_run_diff(preview_repo))
    engine.install_into_repo(apply_repo, source_root, yes=True, no_color=True)

    apply_files = {
        str(p.relative_to(apply_repo)).replace("\\", "/")
        for p in apply_repo.rglob("*")
        if p.is_file() and not str(p.relative_to(apply_repo)).startswith(".git/")
    }

    apply_only = apply_files - preview_headers

    # Explicit allow-list of deliberately excluded classes (F-03, F-04, F-12):
    # - 1 create-or-append back-fill: .aw/.gitignore
    # - 2 merge-writer: AGENTS.md, .gitignore
    # - 2 layout artifacts: .aw/system/layout.json, .aw/system/layout.schema.json
    # - 3 bookkeeping: .aw/system/managed-sections.json, backup dir files
    allowed_residual_fixed = {
        "AGENTS.md",
        ".gitignore",
        ".aw/.gitignore",
        ".aw/system/layout.json",
        ".aw/system/layout.schema.json",
        ".aw/system/managed-sections.json",
    }

    for path in apply_only:
        if path.startswith(".agent-workflows-installer-backups/"):
            continue
        assert (
            path in allowed_residual_fixed
        ), f"New omission detected! Path '{path}' was written by apply but missing from preview."


def test_every_apply_written_gitkeep_appears_in_preview(tmp_path: Path) -> None:
    """Property 2: every .gitkeep written by apply appears in preview headers by path."""
    source_root = engine.resolve_source_root(None)
    preview_repo = tmp_path / "preview_repo"
    apply_repo = tmp_path / "apply_repo"
    preview_repo.mkdir()
    apply_repo.mkdir()

    preview_headers = _extract_diff_headers(_run_diff(preview_repo))
    engine.install_into_repo(apply_repo, source_root, yes=True, no_color=True)

    apply_gitkeeps = {
        str(p.relative_to(apply_repo)).replace("\\", "/")
        for p in apply_repo.rglob("*.gitkeep")
        if p.is_file() and not str(p.relative_to(apply_repo)).startswith(".git/")
    }

    assert (
        len(apply_gitkeeps) == 23
    ), f"Expected 23 .gitkeep files from apply, found {len(apply_gitkeeps)}"
    for gk in apply_gitkeeps:
        assert (
            gk in preview_headers
        ), f"Zero-byte member '{gk}' was dropped from preview diff headers"


def test_scaffold_producer_is_side_effect_free(tmp_path: Path) -> None:
    """Property 3: collect_scaffold_members creates no files and no directories."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "existing.txt").write_text("existing", encoding="utf-8")

    before_listing = sorted(
        str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("*")
    )
    members = engine.collect_scaffold_members(repo, source_root)
    after_listing = sorted(
        str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("*")
    )

    assert (
        before_listing == after_listing
    ), "collect_scaffold_members mutated the repository filesystem"
    assert len(members) > 0, "collect_scaffold_members returned an empty map"


def test_diff_preview_against_already_installed_repo_is_idempotent(
    tmp_path: Path,
) -> None:
    """Property 4: --diff against an already-installed repo reports no changes."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "installed_repo"
    repo.mkdir()
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)

    out = _run_diff(repo)
    assert "No changes (everything is already current)." in out
    assert len(_extract_diff_headers(out)) == 0


def test_legacy_layout_scaffold_targets_exclude_aw_paths(tmp_path: Path) -> None:
    """Property 5: legacy layout target produces legacy layout paths and zero .aw/ paths."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "legacy_repo"
    repo.mkdir()
    (repo / ".agents" / "workflows").mkdir(parents=True)

    members = engine.collect_scaffold_members(repo, source_root)
    aw_paths = [p for p in members if p.startswith(".aw/")]
    assert aw_paths == [], f"Legacy layout generated .aw/ paths: {aw_paths}"
    assert ".agents/plans/README.md" in members
    assert ".agents/prompts/README.md" in members


def test_template_miss_member_is_omitted_defensively(tmp_path: Path) -> None:
    """Property 6: when a template is unreadable or missing, the member is omitted from the map."""
    fake_source = tmp_path / "fake_source"
    tmpl_dir = fake_source / "templates"
    tmpl_dir.mkdir(parents=True)
    # Provide only one template
    (tmpl_dir / "agents-README.md").write_text("# Record root", encoding="utf-8")

    target_repo = tmp_path / "target_repo"
    target_repo.mkdir()

    members = engine.collect_scaffold_members(target_repo, fake_source)
    assert ".aw/records/README.md" in members
    assert ".aw/records/plans/README.md" not in members


def test_no_false_overwrite_diff_on_customized_scaffolding(tmp_path: Path) -> None:
    """Property 7: customized scaffolding files preview no diff and emit no removal lines."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "custom_repo"
    repo.mkdir()
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)

    plan_readme = repo / ".aw" / "records" / "plans" / "README.md"
    comms_readme = repo / ".aw" / "records" / "comms" / "README.md"
    gitleaks = repo / ".gitleaksignore"

    s1 = "TEAM_CUSTOM_PLANS_SECRET_12345"
    s2 = "TEAM_CUSTOM_COMMS_POLICY_67890"
    s3 = "TEAM_CUSTOM_GITLEAKS_RULE_99999"

    plan_readme.write_text(f"# {s1}\n", encoding="utf-8")
    comms_readme.write_text(f"# {s2}\n", encoding="utf-8")
    gitleaks.write_text(f"# {s3}\n", encoding="utf-8")

    out = _run_diff(repo)
    headers = _extract_diff_headers(out)

    assert ".aw/records/plans/README.md" not in headers
    assert ".aw/records/comms/README.md" not in headers
    assert ".gitleaksignore" not in headers

    assert s1 not in out
    assert s2 not in out
    assert s3 not in out

    # Confirm real apply does not overwrite the customized files
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)
    assert s1 in plan_readme.read_text(encoding="utf-8")
    assert s2 in comms_readme.read_text(encoding="utf-8")
    assert s3 in gitleaks.read_text(encoding="utf-8")


def test_overwrite_body_members_still_diff(tmp_path: Path) -> None:
    """Property 8: modified body members still produce a Diff header (counter-case for existence filter)."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "body_repo"
    repo.mkdir()
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)

    advise_readme = repo / ".aw" / "system" / "workflows" / "advise" / "README.md"
    advise_readme.write_text(
        advise_readme.read_text(encoding="utf-8") + "\n# Modified body line\n",
        encoding="utf-8",
    )

    out = _run_diff(repo)
    headers = _extract_diff_headers(out)
    assert ".aw/system/workflows/advise/README.md" in headers
