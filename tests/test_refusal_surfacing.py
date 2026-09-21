"""A refusal must be VISIBLE, and must say what to do about it (orchprobe `r2i1b1`).

WHAT THIS FILE DEFENDS, and why each guard is shaped the way it is. The measured defect had two
halves, and only the first is the obvious one:

* F-1, THE ALLOWLIST. The run summary's diagnostics block keyed on a hardcoded set of five statuses
  with no default branch, so any OTHER refusal produced a table row and not one word of diagnosis. A
  new refusal kind was invisible until somebody remembered to extend a list, which is a defect that
  re-arrives every time the vocabulary grows.
* F-4, THE FIELD-NAME MISMATCH, which is worse and is the reason a green suite proved nothing. TWO of
  those five allowlisted statuses (`integration-blocked`, `merge-conflict`) rendered NOTHING, because
  the branch gating them required `driver_error` while the code setting those statuses wrote
  `integration_deferral`. The pre-existing test passed only because it supplied `driver_error` on a
  `failed-safely` item, so the suite was green over two statuses that silently reported silence, and
  it cost the maintainer an unhelpful report twice (runs `ueg5cf`, `pgq326`).

Both guards therefore assert on BEHAVIOR (render a state, read the output) rather than on source
text: a guard that greps for `if status in (...)` passes the moment someone spells the allowlist
differently, which is precisely the class of false comfort that let F-4 survive.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    render_stream,
    run_viewer,
    runner_shared,
)
from agent_workflows.render_stream import (
    Palette,
    REFUSAL_KEY,
    Refusal,
    record_refusal,
    refusal_of_item,
    render_run_summary_table,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _item(status: str, **fields: object) -> dict:
    item = {
        "id6": "aaa111",
        "setid": "someset",
        "position": 1,
        "action": "execute",
        "status": status,
    }
    item.update(fields)
    return item


def _diagnostic_lines(*items: dict) -> list[str]:
    """The rendered diagnostics lines for a state holding ``items``."""
    out = render_run_summary_table(
        {"run_id": "run-guard", "queue": list(items)}, pal=Palette(False)
    )
    return [
        ln for ln in out.splitlines() if ln.strip().startswith(("\u2022", "\u2192"))
    ]


# --------------------------------------------------------------------------------------
# E-01: the record itself
# --------------------------------------------------------------------------------------


class TestRefusalRecord:
    def test_remedy_is_required_not_optional(self):
        """THE REMEDY IS THE POINT, so it cannot be omitted or left blank.

        `AGENTS.md` records the failure mode: a gate that says only "X is forbidden" gets complied
        with by DELETION. A refusal that cannot name the constructive action is incomplete by
        construction, so this is a type error rather than a style preference.
        """
        with pytest.raises(TypeError):
            Refusal(code="c", reason="r")  # type: ignore[call-arg]
        for blank in ("", "   ", "\n"):
            with pytest.raises(ValueError):
                Refusal(code="c", reason="r", remedy=blank)
            with pytest.raises(ValueError):
                Refusal(code="c", remedy="m", reason=blank)

    def test_reader_and_writer_agree_on_one_key(self):
        """The one writer and the one reader are paired, which is F-4's defect class at the source."""
        item = _item("whatever")
        written = record_refusal(
            item, code="k", reason="because", remedy="do this instead"
        )
        assert item[REFUSAL_KEY] == {
            "code": "k",
            "reason": "because",
            "remedy": "do this instead",
        }
        assert refusal_of_item(item) == written

    def test_tolerates_a_run_directory_frozen_before_this_record_existed(self):
        """Durable state is JSON an older driver wrote, so reading must degrade, never raise."""
        assert refusal_of_item({}) is None
        assert refusal_of_item({REFUSAL_KEY: None}) is None
        assert refusal_of_item({REFUSAL_KEY: "not a mapping"}) is None
        # A partial record is REPORTED with a placeholder rather than dropped: the reader must still
        # learn that a refusal happened even when the producer failed to say what to do.
        partial = refusal_of_item({REFUSAL_KEY: {"code": "k", "reason": "why"}})
        assert partial is not None
        assert partial.remedy


# --------------------------------------------------------------------------------------
# E-06: the allowlist must not come back
# --------------------------------------------------------------------------------------


class TestNoStatusAllowlist:
    def test_an_unknown_status_with_a_refusal_still_reports(self):
        """E-06's GUARD. This is the exact shape F-1 records: a status nobody enumerated.

        The status here is deliberately invented. If the diagnostics block ever regains a closed set
        of statuses, this fails, which is the only reason the guard exists.
        """
        item = _item("orchestrator-refused")
        record_refusal(
            item,
            code="orchestrator-uncovered-work",
            reason="the plan declares a step no child covers",
            remedy="add a child plan for that step; do NOT delete the orchestration checklist",
        )
        lines = _diagnostic_lines(item)
        assert lines, "an item carrying a refusal rendered NO diagnostic line"
        assert "the plan declares a step no child covers" in "\n".join(lines)
        assert "add a child plan for that step" in "\n".join(lines)

    @pytest.mark.parametrize(
        "status",
        [
            "orchestrator-refused",
            "verdict-cache-stale",
            "some-status-invented-in-2027",
            "",
        ],
    )
    def test_every_status_shape_is_surfaced(self, status: str):
        """No status, however unlikely, may swallow a refusal."""
        item = _item(status)
        record_refusal(item, code="c", reason="a reason", remedy="a remedy")
        assert _diagnostic_lines(item), f"status {status!r} swallowed its refusal"

    def test_the_remedy_is_on_its_own_line(self):
        """So it survives the `head`/`tail` pipelines agents use, and a long reason cannot hide it."""
        item = _item("refused-somehow")
        record_refusal(
            item, code="c", reason="x" * 400, remedy="the constructive action here"
        )
        lines = _diagnostic_lines(item)
        assert any("the constructive action here" in ln for ln in lines)
        assert any(ln.strip().startswith("\u2192") for ln in lines)


# --------------------------------------------------------------------------------------
# E-07: a rendering condition must read a field a producer actually writes
# --------------------------------------------------------------------------------------


def _fields_read_by_diagnostics_block() -> set[str]:
    """Every item field the diagnostics block's conditions read, by AST rather than by eye.

    Scoped to the diagnostics block so an unrelated `it.get(...)` elsewhere in this large renderer
    cannot pad the set and dilute the guard.
    """
    src = inspect.getsource(render_stream.render_run_summary_table)
    marker = "# Failure / Dependency block diagnostics"
    assert marker in src, (
        "the diagnostics block's anchor comment is gone; re-point this guard at the block "
        "rather than deleting it"
    )
    block = src[src.index(marker) :]
    tree = ast.parse(inspect.cleandoc(block).replace(marker, "").strip())
    found: set[str] = set()
    for node in ast.walk(tree):
        # `it.get("field")`
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            found.add(node.args[0].value)
        # `it["field"]`
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            found.add(node.slice.value)
    return found


def _fields_written_by_the_runners() -> set[str]:
    """Every item field either host runner assigns, by AST over `item[...] = ...`.

    This is the OTHER half of the pair. F-4 existed because nobody ever compared these two sets.

    `runner_shared` IS SCANNED TOO, added 2026-09-14 when lanes `51vw4y` and `r2i1b1` were integrated
    together. This guard originally scanned only the two host modules, which was complete when every
    per-item write lived in a host. `51vw4y` then moved the integration-refusal write into the SHARED
    `runner_shared.record_integration_refusal` so the two hosts could not drift, and that made the
    guard report `integration_deferral` as an orphan even though the field is still written on exactly
    the path the renderer reads. Scanning the shared library keeps the guard measuring what it is FOR
    (does a producer write the name the renderer reads) rather than the narrower and now-wrong
    question of whether a HOST writes it. Not a loosening: the comparison is still total over every
    producing module, and a genuinely unwritten field is still an orphan and still fails.
    """
    written: set[str] = set()
    for module in (oc_runipd, agy_runipd, runner_shared):
        path = Path(inspect.getfile(module))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AugAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for tgt in targets:
                if (
                    isinstance(tgt, ast.Subscript)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id in {"item", "runnable"}
                    and isinstance(tgt.slice, ast.Constant)
                    and isinstance(tgt.slice.value, str)
                ):
                    written.add(tgt.slice.value)
    return written


class TestNoFieldNameMismatch:
    """E-07's GUARD, for the defect class F-4 actually found.

    A branch whose rendering condition reads a field the producing code never writes renders SILENCE
    under a green suite. That is what made `integration-blocked` and `merge-conflict` invisible.
    """

    def test_every_field_the_diagnostics_block_reads_is_one_a_runner_writes(self):
        read = _fields_read_by_diagnostics_block()
        written = _fields_written_by_the_runners()
        # Fields the renderer legitimately reads that are not per-item runner assignments: the
        # refusal record (written through the shared `record_refusal` helper, not by subscript) and
        # the item identity/status the queue always carries.
        renderer_owned = {
            REFUSAL_KEY,
            "id6",
            "status",
            "position",
            "action",
            "setid",
            # Read from the ATTEMPT record, which is where every producing site writes it, through
            # `_interrupt_reason_of`. See `test_the_interrupted_arm_reads_where_the_runners_write`:
            # this guard FOUND that mismatch, which is why the name is exempted deliberately here
            # rather than silently.
            "attempts",
            "interrupt_reason",
        }
        orphans = {f for f in read - written - renderer_owned}
        assert not orphans, (
            f"the diagnostics block reads {sorted(orphans)}, which NO runner writes. "
            f"This is F-4's defect class: such a branch renders SILENCE while the suite stays "
            f"green. Either write the field at the source or read the name the runners use."
        )

    def test_the_refusal_key_is_written_through_the_shared_writer(self):
        """`record_refusal` is the only writer, so the pair cannot drift by a typo at a call site."""
        for module in (oc_runipd, agy_runipd):
            src = Path(inspect.getfile(module)).read_text(encoding="utf-8")
            assert f'["{REFUSAL_KEY}"]' not in src, (
                f"{module.__name__} assigns the refusal key directly; route it through "
                f"`record_refusal` so the writer cannot drift from the reader"
            )

    @pytest.mark.parametrize("status", ["merge-needs-human", "merge-refused"])
    def test_the_two_repaired_statuses_render_the_field_the_runners_write(
        self, status: str
    ):
        """F-4's regression test, stated in the terms the bug actually had.

        `integration_deferral`, NOT `driver_error`: rendered with the field the RUNNERS write, these
        two produced no diagnostic line at all before this plan.
        """
        item = _item(status, integration_deferral="dirty overlap on src/demo.txt")
        lines = _diagnostic_lines(item)
        assert lines, f"{status} rendered NO diagnostic line (this is exactly F-4)"
        assert "dirty overlap on src/demo.txt" in "\n".join(lines)

    def test_the_interrupted_arm_reads_where_the_runners_write(self):
        """A THIRD INSTANCE OF F-4, found by the guard above rather than by inspection.

        The plan recorded two dead statuses. This one makes three: the block read
        `item["interrupt_reason"]` while all EIGHT producing sites write
        `attempt["interrupt_reason"]` and set only `item["status"]`. The existing pin in
        `tests/test_run_summary_table.py` passed because it HOISTS the reason onto the item, a shape
        no runner produces, so the arm was dead for every real run.
        """
        runner_written = _item(
            "interrupted",
            attempts=[{"interrupt_reason": "stall_timeout", "interrupted_at": "t"}],
        )
        lines = _diagnostic_lines(runner_written)
        assert lines, (
            "an interrupted item with its reason on the ATTEMPT (the only shape the runners "
            "produce) rendered NO diagnostic line"
        )
        assert "stall_timeout" in "\n".join(lines)

        # The newest attempt wins, so a retried item reports why it stopped THIS time.
        retried = _item(
            "interrupted",
            attempts=[
                {"interrupt_reason": "deliberate-stop-at-checkpoint"},
                {"interrupt_reason": "stall_timeout"},
            ],
        )
        assert "stall_timeout" in "\n".join(_diagnostic_lines(retried))

    def test_the_three_previously_working_statuses_are_unchanged(self):
        """The three that DID work keep their exact wording, which `test_run_summary_table` pins."""
        assert _diagnostic_lines(
            _item(
                "dependency-blocked",
                unsatisfied_dependencies=["base01"],
                unsatisfied_dependency_reasons={"base01": "spec approval required"},
            )
        ) == ["  \u2022 aaa111: dependency-blocked (base01 (spec approval required))"]
        assert _diagnostic_lines(
            _item("failed-safely", driver_error="merge conflict in tests/test_main.py")
        ) == ["  \u2022 aaa111: failed-safely (merge conflict in tests/test_main.py)"]
        assert _diagnostic_lines(
            _item("interrupted", interrupt_reason="stall_timeout")
        ) == ["  \u2022 aaa111: interrupted (stall_timeout)"]


# --------------------------------------------------------------------------------------
# E-03/E-04: ONE predicate, and every `aw runs` surface agreeing
# --------------------------------------------------------------------------------------


def _step(**fields: object) -> run_viewer.StepSummary:
    base = {
        "position": 1,
        "id6": "aaa111",
        "setid": "someset",
        "action": "execute",
        "status": "executed",
        "configured_file": "",
        "stem": "20260907-someset-01-aaa111-demo",
    }
    base.update(fields)
    return run_viewer.StepSummary(**base)  # type: ignore[arg-type]


class TestOneIssuePredicate:
    def test_a_refusal_counts_as_an_issue_and_a_clean_step_does_not(self):
        clean_audit = run_viewer.StepArtifactAudit(
            id6="aaa111", stem="s", run_status="executed"
        )
        clean_step = _step()
        assert run_viewer.step_has_issue(clean_audit, clean_step) is False
        assert run_viewer.step_issue_reasons(clean_audit, clean_step) == []

        refused = _step(
            refusal={"code": "k", "reason": "why it stopped", "remedy": "do this"}
        )
        assert run_viewer.step_has_issue(clean_audit, refused) is True
        assert any(
            "why it stopped" in r
            for r in run_viewer.step_issue_reasons(clean_audit, refused)
        )

    def test_the_three_original_artifact_terms_still_count(self):
        """The extraction must not change what the pre-existing terms mean."""
        for field in ("missing_entirely", "location_mismatch", "status_mismatch"):
            audit = run_viewer.StepArtifactAudit(
                id6="aaa111", stem="s", run_status="executed"
            )
            # Set the one term under test, rather than passing it as **kwargs: a splatted dict widens
            # to every field's type and makes a type checker complain about unrelated parameters.
            setattr(audit, field, True)
            assert run_viewer.step_has_issue(audit, _step()) is True, field

    def test_a_refused_step_is_reported_without_any_flag(self):
        """E-05/F-5: `render_step_details` runs only under `if detail:`, so the flagless reader
        needed a surface of its own. A `YES` with no explanation is what this prevents."""
        refused = _step(
            refusal={
                "code": "orchestrator-uncovered-work",
                "reason": "a step no child covers",
                "remedy": "add a child plan for it",
            }
        )
        block = run_viewer.format_refusal_summary(
            [refused], run_viewer.Term(color=False)
        )
        assert "a step no child covers" in block
        assert "add a child plan for it" in block

    def test_the_detail_view_carries_the_full_reason_and_remedy(self):
        refused = _step(refusal={"code": "k", "reason": "R" * 300, "remedy": "M" * 300})
        text = "\n".join(
            run_viewer.render_step_details([refused], run_viewer.Term(color=False))
        )
        assert "R" * 300 in text, "the detail view truncated the reason"
        assert "M" * 300 in text, "the detail view truncated the remedy"

    def test_a_clean_run_reports_no_refusal_block(self):
        assert (
            run_viewer.format_refusal_summary([_step()], run_viewer.Term(color=False))
            == ""
        )


# --------------------------------------------------------------------------------------
# E-08: ONE definition shared by both hosts, without deepening the oc-to-agy coupling
# --------------------------------------------------------------------------------------


class TestOneDefinitionAcrossHosts:
    """The anti-re-fork discipline `2r306y`/`818uru` established, asserted by OBJECT IDENTITY.

    A behavioral comparison passes against a COPY, which is exactly how the `Heartbeat` divergence
    this module's docstring cites went unnoticed. Identity is the only assertion that cannot.
    """

    @pytest.mark.parametrize(
        "name",
        [
            "REFUSAL_KEY",
            "Refusal",
            "record_refusal",
            "record_integration_refusal",
            "refusal_of_item",
        ],
    )
    def test_both_hosts_bind_the_same_object(self, name: str):
        owner = getattr(render_stream, name)
        assert getattr(oc_runipd, name) is owner, f"oc_runipd re-forked {name}"
        assert getattr(agy_runipd, name) is owner, f"agy_runipd re-forked {name}"

    def test_the_viewer_reads_through_the_shared_reader(self):
        assert run_viewer.refusal_of_item is render_stream.refusal_of_item
        assert run_viewer.REFUSAL_KEY is render_stream.REFUSAL_KEY

    def test_render_stream_still_imports_no_first_party_module(self):
        """E-01's siting argument (F-7) is load-bearing and must keep holding.

        `runner_shared` already imports `render_stream`, so a first-party import here would create
        the cycle that forced this record into this module in the first place.
        """
        tree = ast.parse(
            Path(inspect.getfile(render_stream)).read_text(encoding="utf-8")
        )
        offenders: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders += [
                    a.name for a in node.names if a.name.startswith("agent_workflows")
                ]
            elif isinstance(node, ast.ImportFrom):
                if node.level or (node.module or "").startswith("agent_workflows"):
                    offenders.append(node.module or f"(relative level {node.level})")
        assert not offenders, (
            f"render_stream now imports first-party module(s) {offenders}; "
            f"`runner_shared` imports render_stream, so this risks a cycle"
        )

    def test_no_new_symbol_deepens_the_oc_to_agy_coupling(self):
        """The refusal symbols must be imported from `render_stream`, NEVER from the other host.

        Backlog `cnwy8g` recorded 40 names imported from `oc_runipd`; it was 47 when this plan was
        written. The assertion is DIRECTIONAL rather than a magic number, because a number pinned
        here turns every unrelated sharing decision into a failure in this file.
        """
        tree = ast.parse(Path(inspect.getfile(agy_runipd)).read_text(encoding="utf-8"))
        from_oc: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
                "oc_runipd"
            ):
                from_oc.update(a.name for a in node.names)
        for name in (
            "REFUSAL_KEY",
            "Refusal",
            "record_refusal",
            "record_integration_refusal",
            "refusal_of_item",
        ):
            assert name not in from_oc, (
                f"agy_runipd imports {name} from oc_runipd, making one host the de-facto "
                f"shared library; import it from `render_stream` instead"
            )
