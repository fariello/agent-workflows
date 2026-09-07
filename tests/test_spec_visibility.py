"""`aw * run` must announce, before it starts, which queued plans will change a SPEC.

WHY (maintainer request 2026-09-07). A plan's `- Scope-Paths:` is its declared allowlist, and the
finalize gate already reconciles the real change set against it. But nothing SURFACED a spec edit to
the operator: the pre-run output printed the run order and nothing else, so "this run will rewrite an
approved specification" was discoverable only by opening every queued plan. A spec is the contract
other plans are reviewed against, which makes an unnoticed spec edit the highest-leverage change a run
can make and, until now, the least visible one.

The policy this rests on, decided by the maintainer the same day: an IPD MAY edit a spec. Plan
`51vw4y` proved the alternative is a dead end (the flag table it must extend is spec-governed, and the
plan had no spec-edit authority, so every route either edited an approved spec or weakened a shipped
contract test). Specs are living contracts, so the answer is to permit the amendment and make it LOUD.
"""

from __future__ import annotations

from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from agent_workflows.render_stream import (
    Palette,
    format_spec_impact_announcement,
)

PLAN = """\
# IPD: demo

- Date: 2026-09-07
- Kind: child
- Scope-Paths: {scope}
- Status: approved
- Set: demo
- Order: 1
- Id: {id6}
"""


def _plan(root: Path, id6: str, scope: str) -> Path:
    p = root / f"20260907-demo-01-{id6}-demo.ipd.md"
    p.write_text(PLAN.format(scope=scope, id6=id6), encoding="utf-8")
    return p


class TestDeclaredSpecPaths:
    def test_picks_out_spec_files_only(self) -> None:
        text = PLAN.format(
            scope="agent_workflows/cli.py, .aw/records/specs/20260826-0718-01-x.spec.md, tests/t.py",
            id6="aaa111",
        )
        assert runner_shared.declared_spec_paths(text) == [
            ".aw/records/specs/20260826-0718-01-x.spec.md"
        ]

    def test_multiple_specs_keep_declared_order(self) -> None:
        text = PLAN.format(
            scope="b/second.spec.md, a/first.spec.md",
            id6="aaa112",
        )
        assert runner_shared.declared_spec_paths(text) == [
            "b/second.spec.md",
            "a/first.spec.md",
        ]

    def test_no_specs_yields_empty(self) -> None:
        text = PLAN.format(scope="agent_workflows/cli.py, tests/t.py", id6="aaa113")
        assert runner_shared.declared_spec_paths(text) == []

    def test_grandfathered_and_none_yield_empty(self) -> None:
        for value in ("grandfathered", "none", ""):
            text = PLAN.format(scope=value, id6="aaa114")
            assert runner_shared.declared_spec_paths(text) == [], value

    def test_a_missing_scope_paths_field_yields_empty(self) -> None:
        assert runner_shared.declared_spec_paths("# IPD: no scope field\n") == []

    def test_identified_by_type_facet_not_directory(self) -> None:
        """A relocated records tree must not hide a spec edit."""
        text = PLAN.format(
            scope="somewhere/else/20260101-0000-01-y.spec.md", id6="aaa115"
        )
        assert runner_shared.declared_spec_paths(text) == [
            "somewhere/else/20260101-0000-01-y.spec.md"
        ]

    def test_a_spec_shaped_name_that_is_not_a_spec_is_ignored(self) -> None:
        """`.spec.md` is the facet; `spec.py` or a doc merely mentioning spec is not."""
        text = PLAN.format(
            scope="agent_workflows/ipd_schema.py, docs/spec.md", id6="aaa116"
        )
        assert runner_shared.declared_spec_paths(text) == []


class TestSpecImpactsForQueue:
    def test_collects_impacts_across_the_queue(self, tmp_path: Path) -> None:
        a = _plan(tmp_path, "bbb111", "x/one.spec.md, agent_workflows/cli.py")
        b = _plan(tmp_path, "bbb222", "agent_workflows/only_code.py")
        queue = [
            {"id6": "bbb111", "setid": "demo", "path": str(a)},
            {"id6": "bbb222", "setid": "demo", "path": str(b)},
        ]
        impacts = runner_shared.spec_impacts_for_queue(tmp_path, queue)
        assert impacts == [
            {"id6": "bbb111", "setid": "demo", "specs": ["x/one.spec.md"]}
        ]

    def test_resolves_a_repo_relative_path(self, tmp_path: Path) -> None:
        a = _plan(tmp_path, "ccc111", "x/one.spec.md")
        queue = [{"id6": "ccc111", "setid": "demo", "path": a.name}]
        impacts = runner_shared.spec_impacts_for_queue(tmp_path, queue)
        assert impacts and impacts[0]["specs"] == ["x/one.spec.md"]

    def test_an_unreadable_plan_is_skipped_not_fatal(self, tmp_path: Path) -> None:
        """Advisory surface: a missing plan must never stop a run from starting."""
        queue = [{"id6": "ddd111", "setid": "demo", "path": "does/not/exist.ipd.md"}]
        assert runner_shared.spec_impacts_for_queue(tmp_path, queue) == []

    def test_an_item_with_no_path_is_skipped(self, tmp_path: Path) -> None:
        assert runner_shared.spec_impacts_for_queue(tmp_path, [{"id6": "e"}]) == []


class TestAnnouncement:
    def test_silent_when_no_plan_touches_a_spec(self) -> None:
        assert format_spec_impact_announcement([]) == []
        assert format_spec_impact_announcement([{"id6": "x", "specs": []}]) == []

    def test_names_every_plan_and_every_spec(self) -> None:
        lines = format_spec_impact_announcement(
            [
                {"id6": "aaa111", "setid": "one", "specs": ["a/x.spec.md"]},
                {
                    "id6": "bbb222",
                    "setid": "two",
                    "specs": ["b/y.spec.md", "b/z.spec.md"],
                },
            ],
            pal=Palette(False),
        )
        blob = "\n".join(lines)
        assert "3 specification file(s)" in blob
        assert "2 queued plan(s)" in blob
        for token in ("aaa111", "bbb222", "a/x.spec.md", "b/y.spec.md", "b/z.spec.md"):
            assert token in blob, token

    def test_says_why_it_matters(self) -> None:
        """The line must explain the stake, not just list paths."""
        lines = format_spec_impact_announcement(
            [{"id6": "aaa111", "setid": "one", "specs": ["a/x.spec.md"]}],
            pal=Palette(False),
        )
        blob = "\n".join(lines)
        assert "contract other plans are reviewed against" in blob

    def test_is_pure(self, capsys) -> None:
        format_spec_impact_announcement(
            [{"id6": "a", "setid": "s", "specs": ["x.spec.md"]}], pal=Palette(False)
        )
        assert capsys.readouterr().out == ""


class TestBothHostsShareOneDefinition:
    """Anti-re-fork (2r306y/818uru): asserted by object identity, not by grep."""

    def test_shared(self) -> None:
        for name in ("spec_impacts_for_queue", "declared_spec_paths"):
            shared = getattr(runner_shared, name)
            assert getattr(oc_runipd, name) is shared
            assert getattr(agy_runipd, name) is shared
            assert shared.__module__ == "agent_workflows.runner_shared"
