"""One file-name parser (maintainer ruling 2026-11-09).

Every consumer that reads identity from a record filename must agree with THE library,
`agent_workflows.artifact_naming`. Private copies of the grammar drifted twice: the attention board
showed the whole filename as the Set for every Order-100+ plan after the library learned three-digit
Orders, and `aw ipd lint` rejected 8 backlog names the library accepted.

These tests drive each consumer through its real entry point on every tracked record filename plus
a set of edge names, and compare the answer with the library's. They do not read source code.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

from agent_workflows import artifact_naming as N
from agent_workflows import (
    artifact_refs,
    attention,
    ipd_lifecycle,
    plans_refs,
    run_viewer,
)
from agent_workflows import check_engine

pytestmark = pytest.mark.core

REPO = Path(__file__).resolve().parents[1]

EDGE_NAMES = (
    "20261109-metastore-100-o19353-build-the-marker.ipd.md",
    "20261109-metastore-07-o19353-build-the-marker.ipd.md",
    "20261109-a-1-123-abc123-x.ipd.md",
    "20260101-foo-12-abc123-bar-01-def456-slug.ipd.md",
    "20261016-rq-05-kdg4uz-telegram-signal-channels.gpt61med.research-report.md",
    "20260818-1525-02-assess-workflow.spec.md",
    "20261001-ezv744-01-ezv744-trailing-hyphen-.backlog.md",
    "20261109-s-1000-abc123-x.ipd.md",
    "README.md",
)


def _tracked_names() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", ".aw/records"], cwd=REPO, capture_output=True, text=True
    ).stdout.split()
    return sorted({p.rsplit("/", 1)[-1] for p in out if p.endswith(".md")})


ALL_NAMES = tuple(_tracked_names()) + EDGE_NAMES


def _item(name: str) -> attention.Item:
    return attention.Item(
        id="",
        path=f".aw/records/plans/pending/{name}",
        tree="plans",
        native_status="to-review",
        attention_class="ready",
        gate=None,
        last_history_at=None,
    )


def test_board_reads_the_same_identity_as_the_library():
    wrong = []
    for name in ALL_NAMES:
        lib = N.identity_parts(name)
        leg = N.legacy_identity_parts(name)
        got = attention._extract_identity_parts(_item(name))
        if leg:
            want = (leg[0], leg[2], leg[1], "-")
        elif lib:
            want = lib
        else:
            continue
        if got != want:
            wrong.append((name, got, want))
    assert not wrong, wrong[:5]


def test_board_stem_matches_the_library_identity():
    for name in ALL_NAMES:
        lib = N.identity_parts(name)
        if lib:
            assert attention._identity_stem(f"x/{name}") == "-".join(lib), name


def test_run_viewer_reads_the_same_identity_as_the_library():
    wrong = []
    for name in ALL_NAMES:
        lib = N.identity_parts(name)
        if lib is None or N.legacy_identity_parts(name):
            continue
        got = run_viewer.extract_identity_parts(path=name)
        if got != lib:
            wrong.append((name, got, lib))
    assert not wrong, wrong[:5]


def test_plan_id_from_filename_matches_the_library(tmp_path: Path):
    for name in ALL_NAMES:
        lib = N.identity_parts(name)
        p = tmp_path / name
        p.write_text("no metadata\n", encoding="utf-8")
        assert ipd_lifecycle._extract_plan_id(p) == (lib[3] if lib else None), name


def test_legacy_stem_readers_match_the_library():
    for name in ALL_NAMES:
        want = N.legacy_stem_prefix(name)
        assert artifact_refs._legacy_prefix_stem(name) == want, name
        assert plans_refs._old_stem(name) == want, name


def test_lint_and_check_judge_plan_names_exactly_as_the_library():
    """`aw ipd lint` / `aw check` load the shipped name tool; it must give the library's answer."""
    npn = check_engine._load_normalizer()
    assert npn is not None
    for name in ALL_NAMES:
        for facet in ("ipd", "backlog", "spec", "review"):
            for req in (False, True):
                want = N.is_plan_name_conformant(
                    name, expected_type=facet, require_id6=req
                )
                got = npn.is_conformant(name, expected_type=facet, require_id6=req)
                assert got == want, (name, facet, req)
    # and the rule itself: three-digit Order valid, trailing-hyphen slug and Order 1000 invalid
    assert N.is_plan_name_conformant("20261109-metastore-100-o19353-x.ipd.md")
    assert not N.is_plan_name_conformant("20261001-ezv744-01-ezv744-gates-.ipd.md")
    assert not N.is_plan_name_conformant("20261109-s-1000-abc123-x.ipd.md")


def test_every_tracked_record_name_is_valid_under_the_one_strict_grammar():
    """No tracked clustered-looking record carries a name the strict grammar rejects (the 8
    trailing-hyphen names were renamed when the grammar became strict)."""
    bad = [
        n
        for n in _tracked_names()
        if N.parse_clustered_prefix(n) is not None
        and N.parse_clustered(n) is None
        and N.parse_uniform_permissive(n) is not None
        and n.rsplit(".", 2)[0].endswith("-")
    ]
    assert bad == []


def test_the_shipped_name_tool_uses_the_library_objects():
    """Behavioral: the tool's answers come from the library, so changing a library rule changes
    the tool's answer (checked on a name only the widened Order rule accepts)."""
    spec = importlib.util.spec_from_file_location(
        "npn_probe",
        REPO / ".aw/system/workflows/setup-repo/tools/normalize_plan_names.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    name = "20261109-metastore-100-o19353-x.ipd.md"
    assert mod.is_conformant(name) is True
    assert mod.parse_name("20260818-1525-02-assess-workflow.spec.md").nn == "02"


def test_slug_builder_never_leaves_a_hyphen_at_a_cut():
    from agent_workflows import artifact_core as core

    title = "Make the thing work for every repository and its many kinds of record trees now"
    s = core.kebab_slug(title, 60, "x")
    assert not s.endswith("-") and not s.startswith("-") and len(s) <= 60
    assert N.parse_clustered(f"20261109-s-01-abc123-{s}.ipd.md") is not None
    assert core.kebab_slug("---", 60, "fallback") == "fallback"
