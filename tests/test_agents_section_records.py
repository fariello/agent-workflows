"""Behavioral tests and live guard for AGENTS.md managed section records (IPD l5t4vx).

Verifies:
(a) Live guard: managed section records in .aw/system/managed-sections.json for this repo's
    AGENTS.md must match the on-disk content. If a generator change or AGENTS.md rewrite leaves
    them stale, consent hits case 3 (preserving disk and warning), failing this test.
(b) Synthesized reconcile: with identical text and stale hashes, reconcile leaves AGENTS.md
    byte-identical, updates recorded hashes, and leaves unrelated manifest entries and GEMINI.md
    unchanged.
(c) Synthesized refresh: when managed region text differs from generator, reconcile rewrites
    the block to match the generator, preserves foreign before/after text, and updates hashes;
    with check=True it reports staleness without modifying any file.
(d) Synthesized refusals: refuses with no edits on ambiguous openers, drift (missing closer with
    trailing text), unknown section slugs, legacy markers, and declined tombstones.
(e) Synthesized CLI: main returns 1 on check with stale records, 0 on reconcile, and 2 on refusal.
"""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import pytest

from agent_workflows import engine, manifest

pytestmark = pytest.mark.core


def stale_section_keys(agents_text: str, manifest_obj: manifest.Manifest) -> list[str]:
    """Return keys of sections in agents_text whose manifest records are stale.

    For each desired section, perturbs that section in memory and calls engine.merge_aw_block.
    If the manifest record is stale, merge_aw_block hits consent case 3 (preserving the
    on-disk body and emitting a manual modifications warning), so the sentinel line is not
    present in the returned text or a warning is emitted for that section key.
    """
    stale: list[str] = []
    desired = engine.agents_managed_sections("aw")
    sentinel = "<!-- aw:sentinel-probe -->"

    for sec in desired:
        key = f"AGENTS.md#aw:{sec.slug}"
        perturbed = [
            engine.AwSection(
                slug=s.slug,
                lines=list(s.lines) + ([sentinel] if s.slug == sec.slug else []),
            )
            for s in desired
        ]
        m_copy = copy.deepcopy(manifest_obj)
        warnings: list[str] = []
        result, _ = engine.merge_aw_block(
            agents_text,
            perturbed,
            manifest=m_copy,
            file_key="AGENTS.md",
            warnings=warnings,
        )
        if sentinel not in result or any(key in w for w in warnings):
            stale.append(key)

    return stale


def test_live_agents_md_section_records_are_current() -> None:
    """(a) Live guard asserting this repo's AGENTS.md section records are in step."""
    repo_root = Path(__file__).resolve().parent.parent
    agents_path = repo_root / "AGENTS.md"
    manifest_path = repo_root / ".aw/system/managed-sections.json"
    assert agents_path.is_file(), f"Missing {agents_path}"
    assert manifest_path.is_file(), f"Missing {manifest_path}"

    agents_text = agents_path.read_text(encoding="utf-8")
    m = manifest.load(manifest_path)

    stale = stale_section_keys(agents_text, m)
    if stale:
        warn_msgs: list[str] = []
        desired = engine.agents_managed_sections("aw")
        for sec in desired:
            key = f"AGENTS.md#aw:{sec.slug}"
            if key in stale:
                perturbed = [
                    engine.AwSection(
                        slug=s.slug,
                        lines=list(s.lines)
                        + (
                            ["<!-- aw:sentinel-probe -->"] if s.slug == sec.slug else []
                        ),
                    )
                    for s in desired
                ]
                w: list[str] = []
                engine.merge_aw_block(
                    agents_text,
                    perturbed,
                    manifest=copy.deepcopy(m),
                    file_key="AGENTS.md",
                    warnings=w,
                )
                warn_msgs.extend(w)

        remedy = "python3 -m tools.regen_agents_block"
        msg = (
            f"Stale section keys detected: {stale}\n"
            f"Warnings:\n" + "\n".join(warn_msgs) + "\n"
            f"Remedy: run `{remedy}` to reconcile section hashes."
        )
        assert not stale, msg


def test_synthesized_reconcile_preserves_text_and_updates_hashes() -> None:
    """(b) Synthesized reconcile leaves text identical, updates hashes, leaves unrelated entries intact."""
    from tools.regen_agents_block import reconcile

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        sys_dir = repo_root / ".aw" / "system"
        sys_dir.mkdir(parents=True)

        desired_block = engine.agents_managed_block(target_layout="aw")
        before_text = "# Sample Project\n\nSome introductory docs."
        after_text = "## Local Notes\nSome developer notes."
        agents_text = f"{before_text}\n\n{desired_block.strip()}\n\n{after_text}\n"

        agents_file = repo_root / "AGENTS.md"
        agents_file.write_text(agents_text, encoding="utf-8")

        gemini_file = repo_root / "GEMINI.md"
        gemini_text = "# GEMINI\n\nInstructions without block.\n"
        gemini_file.write_text(gemini_text, encoding="utf-8")

        manifest_path = sys_dir / "managed-sections.json"
        m = manifest.Manifest()
        m.record(
            "AGENTS.md#aw:pointer",
            "wrong pointer body",
            kind="section",
            host="",
            logical_id="pointer",
        )
        m.record(
            "AGENTS.md#aw:reporting",
            "wrong reporting body",
            kind="section",
            host="",
            logical_id="reporting",
        )
        m.record(
            ".gitignore#aw:untracked",
            "some untracked gitignore",
            kind="section",
            host="",
            logical_id="untracked",
        )
        m.files["unrelated.txt"] = manifest.FileEntry(
            path="unrelated.txt",
            sha256="deadbeef0123456789abcdef",
            kind="file",
        )
        manifest.save(m, manifest_path)

        agents_bytes_before = agents_file.read_bytes()
        gemini_bytes_before = gemini_file.read_bytes()

        res1 = reconcile(repo_root)
        assert res1["stale"] is True
        assert res1["text_changed"] is False
        assert set(res1["records_changed"]) == {
            "AGENTS.md#aw:pointer",
            "AGENTS.md#aw:reporting",
        }
        assert agents_file.read_bytes() == agents_bytes_before
        assert gemini_file.read_bytes() == gemini_bytes_before

        m_after = manifest.load(manifest_path)
        parsed = engine.parse_aw_block(agents_text)
        for sec in parsed.sections:
            key = f"AGENTS.md#aw:{sec.slug}"
            assert m_after.recorded_hash(key) == manifest.hash_content(sec.body)

        assert m_after.files["unrelated.txt"] == m.files["unrelated.txt"]
        assert m_after.recorded_hash(".gitignore#aw:untracked") == m.recorded_hash(
            ".gitignore#aw:untracked"
        )

        res2 = reconcile(repo_root)
        assert not res2["stale"]
        assert not res2["text_changed"]
        assert res2["records_changed"] == []


def test_synthesized_reconcile_rewrites_managed_region_and_preserves_foreign() -> None:
    """(c) Synthesized refresh rewrites only managed block, keeps foreign text, checks dry-run."""
    from tools.regen_agents_block import reconcile

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        sys_dir = repo_root / ".aw" / "system"
        sys_dir.mkdir(parents=True)

        before_foreign = "# Project Title\n\nForeign introductory text."
        after_foreign = "## Foreign Section\n\nForeign trailing text."
        stale_managed_block = (
            "<!-- aw:block -->\n"
            "<!-- aw:pointer -->\n"
            "Old stale pointer.\n"
            "<!-- aw:reporting -->\n"
            "Old stale reporting.\n"
            "<!-- /aw:block -->"
        )
        agents_text = f"{before_foreign}\n\n{stale_managed_block}\n\n{after_foreign}\n"

        agents_file = repo_root / "AGENTS.md"
        agents_file.write_text(agents_text, encoding="utf-8")

        manifest_path = sys_dir / "managed-sections.json"
        m = manifest.Manifest()
        m.record(
            "AGENTS.md#aw:pointer",
            "Old stale pointer.",
            kind="section",
            host="",
            logical_id="pointer",
        )
        m.record(
            "AGENTS.md#aw:reporting",
            "Old stale reporting.",
            kind="section",
            host="",
            logical_id="reporting",
        )
        manifest.save(m, manifest_path)

        agents_bytes_before = agents_file.read_bytes()
        agents_mtime_before = agents_file.stat().st_mtime_ns
        manifest_bytes_before = manifest_path.read_bytes()
        manifest_mtime_before = manifest_path.stat().st_mtime_ns

        # Dry-run check=True
        check_res = reconcile(repo_root, check=True)
        assert check_res["stale"] is True
        assert check_res["text_changed"] is True
        assert agents_file.read_bytes() == agents_bytes_before
        assert agents_file.stat().st_mtime_ns == agents_mtime_before
        assert manifest_path.read_bytes() == manifest_bytes_before
        assert manifest_path.stat().st_mtime_ns == manifest_mtime_before

        # Actual reconcile
        res = reconcile(repo_root)
        assert res["stale"] is True
        assert res["text_changed"] is True

        new_agents_text = agents_file.read_text(encoding="utf-8")
        parsed = engine.parse_aw_block(new_agents_text)
        assert parsed.found is True
        assert parsed.before.strip("\n") == before_foreign.strip("\n")
        assert parsed.after.strip("\n") == after_foreign.strip("\n")

        expected_sections = engine.agents_managed_sections("aw")
        assert len(parsed.sections) == len(expected_sections)
        for s_actual, s_exp in zip(parsed.sections, expected_sections):
            assert s_actual.slug == s_exp.slug
            assert manifest.hash_content(s_actual.body) == manifest.hash_content(
                s_exp.body
            )

        m_after = manifest.load(manifest_path)
        for s_exp in expected_sections:
            key = f"AGENTS.md#aw:{s_exp.slug}"
            assert m_after.recorded_hash(key) == manifest.hash_content(s_exp.body)


def _setup_two_openers(agents_file: Path, manifest_path: Path) -> None:
    text = (
        "<!-- aw:block -->\n"
        "<!-- aw:pointer -->\n"
        "Some pointer\n"
        "<!-- /aw:block -->\n"
        "<!-- aw:block -->\n"
    )
    agents_file.write_text(text, encoding="utf-8")
    m = manifest.Manifest()
    manifest.save(m, manifest_path)


def _setup_drift_no_closer(agents_file: Path, manifest_path: Path) -> None:
    text = (
        "<!-- aw:block -->\n"
        "<!-- aw:pointer -->\n"
        "Some pointer\n"
        "Foreign trailing text without closer\n"
    )
    agents_file.write_text(text, encoding="utf-8")
    m = manifest.Manifest()
    manifest.save(m, manifest_path)


def _setup_unknown_slug(agents_file: Path, manifest_path: Path) -> None:
    text = (
        "<!-- aw:block -->\n"
        "<!-- aw:extra -->\n"
        "Extra section body\n"
        "<!-- /aw:block -->\n"
    )
    agents_file.write_text(text, encoding="utf-8")
    m = manifest.Manifest()
    manifest.save(m, manifest_path)


def _setup_legacy_marker(agents_file: Path, manifest_path: Path) -> None:
    text = f"{engine.AGENTS_BEGIN}\n" "Legacy block\n" f"{engine.AGENTS_END}\n"
    agents_file.write_text(text, encoding="utf-8")
    m = manifest.Manifest()
    manifest.save(m, manifest_path)


def _setup_declined_tombstone(agents_file: Path, manifest_path: Path) -> None:
    block = engine.agents_managed_block(target_layout="aw")
    agents_file.write_text(block, encoding="utf-8")
    m = manifest.Manifest()
    m.mark_declined("AGENTS.md#aw:pointer")
    manifest.save(m, manifest_path)


@pytest.mark.parametrize(
    "case_id, setup_fn",
    [
        ("two_openers", _setup_two_openers),
        ("drift_no_closer", _setup_drift_no_closer),
        ("unknown_slug", _setup_unknown_slug),
        ("legacy_marker", _setup_legacy_marker),
        ("declined_tombstone", _setup_declined_tombstone),
    ],
)
def test_synthesized_refusals(case_id: str, setup_fn) -> None:
    """(d) Synthesized refusals ensure files are untouched when malformed or declined."""
    from tools.regen_agents_block import reconcile

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        sys_dir = repo_root / ".aw" / "system"
        sys_dir.mkdir(parents=True)
        agents_file = repo_root / "AGENTS.md"
        manifest_path = sys_dir / "managed-sections.json"

        setup_fn(agents_file, manifest_path)

        agents_bytes_before = agents_file.read_bytes()
        manifest_bytes_before = manifest_path.read_bytes()

        res = reconcile(repo_root)
        assert (
            res.get("refused") is not None
        ), f"Expected refusal for case {case_id}, got {res}"
        assert agents_file.read_bytes() == agents_bytes_before
        assert manifest_path.read_bytes() == manifest_bytes_before


def test_synthesized_cli() -> None:
    """(e) Synthesized CLI returns 1 on stale check, 0 on reconcile, 2 on refusal."""
    from tools.regen_agents_block import main

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir)
        sys_dir = repo_root / ".aw" / "system"
        sys_dir.mkdir(parents=True)

        desired_block = engine.agents_managed_block(target_layout="aw")
        agents_file = repo_root / "AGENTS.md"
        agents_file.write_text(desired_block, encoding="utf-8")

        manifest_path = sys_dir / "managed-sections.json"
        m = manifest.Manifest()
        m.record(
            "AGENTS.md#aw:pointer",
            "stale pointer",
            kind="section",
            host="",
            logical_id="pointer",
        )
        m.record(
            "AGENTS.md#aw:reporting",
            "stale reporting",
            kind="section",
            host="",
            logical_id="reporting",
        )
        manifest.save(m, manifest_path)

        # 1: --check on stale records
        rc1 = main(["--dir", str(repo_root), "--check"])
        assert rc1 == 1

        # 0: reconcile
        rc2 = main(["--dir", str(repo_root)])
        assert rc2 == 0

        # 0: --check after reconcile
        rc3 = main(["--dir", str(repo_root), "--check"])
        assert rc3 == 0

        # 2: refusal on ambiguous file
        agents_file.write_text(
            "<!-- aw:block -->\n<!-- aw:block -->\n", encoding="utf-8"
        )
        rc4 = main(["--dir", str(repo_root)])
        assert rc4 == 2
