"""Self-tests for tests.livecorpus_notice pytest plugin.

Tests cover:
(a) The audit hook records live reads when pointed at a guarded root.
(b) The audit hook ignores reads to unguarded paths.
(c) The LIVE-CORPUS NOTE section appears in test failure output under pytest (subprocess test).
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


import tests.livecorpus_notice as lc


def test_hook_records_guarded_reads(tmp_path: Path) -> None:
    """The hook records reads when the guarded root matches."""
    fake_guarded = tmp_path / "guarded_dir"
    fake_guarded.mkdir()
    sample_file = fake_guarded / "file.txt"
    sample_file.write_text("hello guarded", encoding="utf-8")

    orig_root = lc.GUARDED_ROOT
    lc.GUARDED_ROOT = str(fake_guarded.resolve())
    try:
        # Enumerate and open
        list(fake_guarded.iterdir())
        with open(sample_file, encoding="utf-8") as f:
            f.read()

        resolved_sample = str(sample_file.resolve())
        resolved_dir = str(fake_guarded.resolve())

        matches = [
            p
            for p in lc.RECORDED_PATHS
            if p in (resolved_sample, resolved_dir, str(sample_file), str(fake_guarded))
        ]
        assert (
            matches
        ), f"Expected guarded paths in recorded set, got: {lc.RECORDED_PATHS}"
    finally:
        lc.GUARDED_ROOT = orig_root


def test_hook_ignores_unguarded_reads(tmp_path: Path) -> None:
    """The hook ignores reads to paths outside the guarded root."""
    unguarded = tmp_path / "unguarded_dir"
    unguarded.mkdir()
    sample_file = unguarded / "file.txt"
    sample_file.write_text("hello unguarded", encoding="utf-8")

    lc.RECORDED_PATHS.clear()
    list(unguarded.iterdir())
    with open(sample_file, encoding="utf-8") as f:
        f.read()

    resolved_sample = str(sample_file.resolve())
    resolved_dir = str(unguarded.resolve())

    assert resolved_sample not in lc.RECORDED_PATHS
    assert resolved_dir not in lc.RECORDED_PATHS
    assert str(sample_file) not in lc.RECORDED_PATHS
    assert str(unguarded) not in lc.RECORDED_PATHS


def test_report_section_appears_on_failure() -> None:
    """A failing test that read guarded paths receives a LIVE-CORPUS NOTE section."""
    with tempfile.TemporaryDirectory() as td:
        plugin_src = Path(__file__).resolve().parent / "livecorpus_notice.py"
        plugin_dst = Path(td) / "plugin.py"
        shutil.copyfile(plugin_src, plugin_dst)

        test_file = Path(td) / "test_demo.py"
        test_file.write_text(
            """
import os
import plugin

def test_demonstrate_failure(tmp_path):
    fake_root = os.path.realpath(str(tmp_path / "fake_records"))
    os.makedirs(fake_root, exist_ok=True)
    sample_file = os.path.join(fake_root, "trap.ipd.md")
    with open(sample_file, "w") as f:
        f.write("content")

    orig = plugin.GUARDED_ROOT
    plugin.GUARDED_ROOT = fake_root
    try:
        with open(sample_file) as f:
            f.read()
        assert False, "forced test failure for reporting check"
    finally:
        plugin.GUARDED_ROOT = orig
""",
            encoding="utf-8",
        )

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-o",
            "addopts=",
            "-p",
            "plugin",
            "-p",
            "no:randomly",
            "test_demo.py",
        ]
        res = subprocess.run(
            cmd,
            cwd=td,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        assert (
            res.returncode != 0
        ), f"Expected non-zero exit code, got {res.returncode}. Output:\n{res.stdout}"
        assert (
            "LIVE-CORPUS NOTE" in res.stdout
        ), f"LIVE-CORPUS NOTE missing in output:\n{res.stdout}"
        assert (
            "trap.ipd.md" in res.stdout
        ), f"Expected recorded path in note, got:\n{res.stdout}"
        assert (
            "Note: .aw/records/ is a LIVE tree" in res.stdout
        ), f"Actionable note missing:\n{res.stdout}"
