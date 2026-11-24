"""Tests for the research scan + find + drift check (Set research-org, Order 03).

Stdlib unittest, throwaway dirs. Verifies scan completeness, find filters, and check_drift across
the drift classes including dangling citations (via the Order 04 detector), with no finding for a
stale or missing INDEX file (plan 6qh68x). No INDEX file is written: the SQLite metadata cache
replaced them (spec 4sd62s 4.5).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as _core
from agent_workflows import research_contract as R
from agent_workflows import research_cmd as C
from agent_workflows import research_index as I

import pytest
from tests.record_builder import RecordBuilder

pytestmark = pytest.mark.core


def _write(
    root: Path,
    *,
    set_id,
    order,
    id6,
    slug,
    status,
    created,
    kind="notes",
    model=None,
    body: str | None = None,
    outcome: str = "none-yet",
):
    rroot = root / R.RESEARCH_ROOT
    rroot.mkdir(parents=True, exist_ok=True)
    name = R.format_name(
        R.ResearchName(
            date=created,
            set_id=set_id,
            order=f"{order:02d}",
            id6=id6,
            slug=slug,
            model=model,
            kind=kind,
        )
    )
    content = C.build_frontmatter(
        id6=id6,
        created=created,
        set_id=set_id,
        order=f"{order:02d}",
        topic=["t1"],
        model=model,
        kind=kind,
        status=status,
        outcome=outcome,
        summary=f"summary {id6}",
    )
    if body:
        content += f"\n{body}\n"
    (rroot / name).write_text(content, encoding="utf-8")
    return rroot / name


class IndexBuildTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="intake",
            created="20260701",
        )
        _write(
            self.root,
            set_id="beta",
            order=0,
            id6="bbbbbb",
            slug="b",
            status="reference",
            created="20260705",
        )
        _write(
            self.root,
            set_id="gamma",
            order=0,
            id6="cccccc",
            slug="c",
            status="archive",
            created="20260710",
        )

    def test_json_contains_every_doc(self):
        # Retargeted from INDEX.json to the scan entries `aw find research` reads (plan s6k01k):
        # every doc, archive included, carries its status.
        entries, drift = I._scan_docs(self.rroot)
        self.assertEqual(drift, [])
        by_id = {e.id6: e for e in entries}
        self.assertEqual(set(by_id), {"aaaaaa", "bbbbbb", "cccccc"})
        self.assertEqual(by_id["bbbbbb"].status, "reference")
        self.assertEqual(by_id["cccccc"].status, "archive")


class FindTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="intake",
            created="20260701",
        )
        _write(
            self.root,
            set_id="alpha",
            order=1,
            id6="aaaaab",
            slug="a2",
            status="active",
            created="20260702",
        )
        _write(
            self.root,
            set_id="beta",
            order=0,
            id6="bbbbbb",
            slug="b",
            status="reference",
            created="20260705",
        )

    def test_find_by_set(self):
        entries, _ = I._scan_docs(self.rroot)
        res = I.query(entries, set_id="alpha")
        self.assertEqual({e.id6 for e in res}, {"aaaaaa", "aaaaab"})

    def test_find_by_status(self):
        entries, _ = I._scan_docs(self.rroot)
        res = I.query(entries, status="reference")
        self.assertEqual([e.id6 for e in res], ["bbbbbb"])

    def test_find_by_status_not(self):
        entries, _ = I._scan_docs(self.rroot)
        res = I.query(entries, status_not="reference")
        self.assertEqual({e.id6 for e in res}, {"aaaaaa", "aaaaab"})

        # Multiple and comma-separated
        res_one = I.query(entries, status_not="reference,active")
        self.assertEqual([e.id6 for e in res_one], ["aaaaaa"])

        res_none = I.query(entries, status_not=["reference", "active", "todo"])
        self.assertEqual(res_none, [])

    def test_find_by_id(self):
        entries, _ = I._scan_docs(self.rroot)
        res = I.query(entries, id6="aaaaab")
        self.assertEqual([e.id6 for e in res], ["aaaaab"])


class CheckDriftTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="todo",
            created="20260701",
        )

    def test_stale_index_file_is_not_drift(self):
        # Plan 6qh68x (spec 4sd62s 4.5): the INDEX-file drift rules are deleted with the INDEX files.
        # A leftover manifest with arbitrary bytes is no longer a finding at all.
        (self.rroot / "INDEX.json").write_text("[]\n", encoding="utf-8")
        (self.rroot / "INDEX.md").write_text("stale", encoding="utf-8")
        drift = I.check_drift(self.root, self.rroot)
        self.assertEqual(drift, [])
        self.assertEqual(_core.drift_exit_code(drift), 0)

    def test_missing_index_file_is_not_drift(self):
        """A never-generated manifest is the normal state of a fresh clone or worktree.

        Plan 6qh68x (spec 4sd62s 4.5), the research twin of the plans assertion: the SQLite
        metadata cache replaced the INDEX files, so an absent manifest produces no finding and does
        not fail the gate.
        """
        for name in ("INDEX.json", "INDEX.md"):
            self.assertFalse((self.rroot / name).exists(), f"fixture sanity: {name}")
        drift = I.check_drift(self.root, self.rroot)
        self.assertEqual(drift, [])
        self.assertEqual(_core.drift_exit_code(drift), 0)

    def test_invalid_frontmatter_detected(self):
        # A file with frontmatter missing 'id'.
        bad = self.rroot / "20260701-alpha-01-zzzzzz-bad.notes.md"
        bad.write_text(
            RecordBuilder().research(
                when="2026-07-01",
                research_kind="notes",
                raw_fields={"id": None, "status": "intake"},
                text_only=True,
            ),
            encoding="utf-8",
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == "frontmatter-invalid" for d in drift))

    def test_dangling_citation_detected(self):
        (self.root / "DECISIONS.md").write_text(
            "cite 20260601-old-00-qppqpp-gone.notes.md\n", encoding="utf-8"
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == "dangling-citation" for d in drift))


class UnrunDerivationTests(unittest.TestCase):
    """IPD m383qb E-01: structural unrun/RUN derivation over the manifest."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        # UNRUN: a bare NN=00 research-prompt with no NN>=01 sibling.
        _write(
            self.root,
            set_id="unrunset",
            order=0,
            id6="prmpt1",
            slug="ask",
            status=None,
            created="20260801",
            kind="research-prompt",
        )
        # RUN: a NN=00 research-prompt WITH a NN=01 report sibling with body.
        _write(
            self.root,
            set_id="runset",
            order=0,
            id6="prmpt2",
            slug="ask",
            status=None,
            created="20260802",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="runset",
            order=1,
            id6="rprt01",
            slug="answer",
            status="todo",
            created="20260803",
            kind="research-report",
            body="## Report\nReport findings body.",
        )

    def test_derive_unrun_excludes_run_set_includes_bare_prompt(self):
        entries, _ = I._scan_docs(self.rroot)
        unrun = I.derive_unrun_prompts(entries)
        self.assertEqual([e.id6 for e in unrun], ["prmpt1"])
        self.assertEqual(I.unrun_set_ids(entries), {"unrunset"})
        self.assertEqual(I.run_prompt_set_ids(entries), {"runset"})

    def test_prompt_set_taxonomy_ignores_non_prompt_sets(self):
        # A lone non-prompt intake doc is neither a run prompt-set nor unrun.
        _write(
            self.root,
            set_id="lonenote",
            order=0,
            id6="note01",
            slug="n",
            status="intake",
            created="20260804",
            kind="notes",
        )
        entries, _ = I._scan_docs(self.rroot)
        self.assertNotIn("lonenote", I.unrun_set_ids(entries))
        self.assertNotIn("lonenote", I.run_prompt_set_ids(entries))


class StaleStateDriftTests(unittest.TestCase):
    """IPD m383qb E-02: --check flags stale hot state (RUN set OR cited-by-executed)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT

    def test_trigger_a_run_set_flags_intake_and_clean_after_promote(self):
        # A RUN (synthesized) prompt-set with an intake report member -> stale-state-to-promote.
        _write(
            self.root,
            set_id="runset",
            order=0,
            id6="prmpt2",
            slug="ask",
            status="reference",
            created="20260802",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="runset",
            order=1,
            id6="recon1",
            slug="reconcile",
            status="reference",
            created="20260803",
            kind="reconciliation-report",
            body="## Reconciliation\nSynthesized findings.",
        )
        rpt = _write(
            self.root,
            set_id="runset",
            order=2,
            id6="rprt01",
            slug="answer",
            status="intake",
            created="20260804",
            kind="research-report",
            body="## Report\nBody.",
        )
        drift = I.check_drift(self.root, self.rroot)
        stale = [d for d in drift if d.rule == I.STALE_STATE_RULE]
        self.assertTrue(
            any("rprt01" in d.location or "runset" in d.detail for d in stale),
            f"expected stale flag for the intake report; got {stale}",
        )
        # Promote it out of the hot band -> the stale flag clears (only stale rule considered).
        rpt.write_text(
            rpt.read_text(encoding="utf-8").replace(
                "status: intake", "status: reference"
            ),
            encoding="utf-8",
        )
        drift2 = I.check_drift(self.root, self.rroot)
        self.assertFalse(
            any(d.rule == I.STALE_STATE_RULE for d in drift2),
            "stale-state should clear once the doc is promoted",
        )

    def test_trigger_b_cited_by_executed_plan_flags_but_pending_does_not(self):
        # A standalone intake doc, cited only by a PENDING plan -> NOT flagged.
        _write(
            self.root,
            set_id="solo",
            order=0,
            id6="solo11",
            slug="s",
            status="intake",
            created="20260801",
            kind="notes",
        )
        RecordBuilder(self.root).plan(
            id6="pln001",
            title="Plan",
            when="2026-08-01",
            set="set",
            order=1,
            slug="x",
            disposition="pending",
            body="Uses research RSCH-solo11 for context.",
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertFalse(
            any(d.rule == I.STALE_STATE_RULE for d in drift),
            "a pending-only citer must NOT flag the intake doc",
        )
        # Now cited by an EXECUTED plan -> flagged.
        RecordBuilder(self.root).plan(
            id6="pln002",
            title="Plan",
            when="2026-08-01",
            set="set",
            order=1,
            slug="x",
            status="executed",
            disposition="executed",
            body="Uses research RSCH-solo11 for context.",
        )
        drift2 = I.check_drift(self.root, self.rroot)
        self.assertTrue(
            any(d.rule == I.STALE_STATE_RULE and "solo" in d.location for d in drift2),
            f"expected stale flag from the executed citer; got {[d for d in drift2 if d.rule == I.STALE_STATE_RULE]}",
        )

    def test_cited_by_executed_ids_reverse_traversal(self):
        _write(
            self.root,
            set_id="solo",
            order=0,
            id6="solo11",
            slug="s",
            status="intake",
            created="20260801",
            kind="notes",
        )
        # spec implemented citer
        sp = self.root / ".aw" / "records" / "specs"
        sp.mkdir(parents=True, exist_ok=True)
        (sp / "20260801-01-spc001-x.spec.md").write_text(
            RecordBuilder().spec(
                id6="spc001",
                title="Spec",
                when="2026-08-01",
                order=1,
                slug="x",
                status="implemented",
                body="cites RSCH-solo11 here",
                text_only=True,
            ),
            encoding="utf-8",
        )
        cited = I.cited_by_executed_ids(self.root, self.rroot)
        self.assertIn("solo11", cited)
        # a draft spec citer does NOT count
        (sp / "20260801-02-spc002-y.spec.md").write_text(
            RecordBuilder().spec(
                id6="spc002",
                title="Spec",
                when="2026-08-01",
                order=2,
                slug="y",
                status="draft",
                body="cites RSCH-nofind here",
                text_only=True,
            ),
            encoding="utf-8",
        )
        cited2 = I.cited_by_executed_ids(self.root, self.rroot)
        self.assertNotIn("nofind", cited2)


class ConsumedByIndexTests(unittest.TestCase):
    """IPD xjrdjp E-02: the scan entry carries consumed-by (retargeted from INDEX.json, s6k01k)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        p = _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="reference",
            created="20260701",
        )
        # give it a consumed-by
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "consumed-by: []", "consumed-by: [pln001]"
            ),
            encoding="utf-8",
        )

    def test_docentry_and_json_carry_consumed_by(self):
        entries, _ = I._scan_docs(self.rroot)
        self.assertEqual(entries[0].consumed_by, ["pln001"])
        self.assertEqual(entries[0]._asdict()["consumed_by"], ["pln001"])


class ConsumedByValidationTests(unittest.TestCase):
    """IPD xjrdjp E-03: --check flags dangling consumed-by + adopted-without-consumer."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT

    def test_dangling_consumed_by_flagged(self):
        p = _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="reference",
            created="20260701",
        )
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "consumed-by: []", "consumed-by: [nofind]"
            ),
            encoding="utf-8",
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(
            any(
                d.rule == I.DANGLING_CONSUMED_RULE and "nofind" in d.detail
                for d in drift
            )
        )
        # add a real plan with that id -> resolves, clears.
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "consumed-by: [nofind]", "consumed-by: [pln001]"
            ),
            encoding="utf-8",
        )
        RecordBuilder(self.root).plan(
            id6="pln001",
            title="Plan",
            when="2026-08-01",
            set="set",
            order=1,
            slug="x",
            status="executed",
            disposition="executed",
            body="body",
        )
        drift2 = I.check_drift(self.root, self.rroot)
        self.assertFalse(any(d.rule == I.DANGLING_CONSUMED_RULE for d in drift2))

    def test_adopted_without_consumer_flagged(self):
        p = _write(
            self.root,
            set_id="beta",
            order=0,
            id6="bbbbbb",
            slug="b",
            status="reference",
            created="20260701",
        )
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "outcome: none-yet", "outcome: adopted"
            ),
            encoding="utf-8",
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == I.ADOPTED_NO_CONSUMER_RULE for d in drift))
        # give it a resolving consumer -> clears.
        RecordBuilder(self.root).plan(
            id6="pln002",
            title="Plan",
            when="2026-08-01",
            set="set",
            order=1,
            slug="x",
            status="executed",
            disposition="executed",
            body="body",
        )
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "consumed-by: []", "consumed-by: [pln002]"
            ),
            encoding="utf-8",
        )
        drift2 = I.check_drift(self.root, self.rroot)
        self.assertFalse(any(d.rule == I.ADOPTED_NO_CONSUMER_RULE for d in drift2))

    def test_resolvable_consumer_ids_spans_trees(self):
        # plan, spec, backlog ids all resolve.
        RecordBuilder(self.root).plan(
            id6="pln003",
            title="Plan",
            when="2026-08-01",
            set="set",
            order=1,
            slug="x",
            status="executed",
            disposition="executed",
            body="body",
        )
        sp = self.root / ".aw" / "records" / "specs"
        sp.mkdir(parents=True, exist_ok=True)
        (sp / "20260801-01-spc003-x.spec.md").write_text(
            RecordBuilder().spec(id6="spc003", text_only=True), encoding="utf-8"
        )
        bk = self.root / ".aw" / "records" / "backlog" / "open"
        bk.mkdir(parents=True, exist_ok=True)
        (bk / "item.md").write_text(
            RecordBuilder().backlog(id6="bkl003", status="open", text_only=True),
            encoding="utf-8",
        )
        ids = I.resolvable_consumer_ids(self.root)
        self.assertTrue({"pln003", "spc003", "bkl003"}.issubset(ids))


class PendingQueryTests(unittest.TestCase):
    """IPD h40usm E-01: aw research pending lists exactly the unrun prompts."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / ".agents" / "docs" / "research"
        # UNRUN: bare NN=00 prompt.
        _write(
            self.root,
            set_id="unrunset",
            order=0,
            id6="prmpt1",
            slug="ask",
            status=None,
            created="20260801",
            kind="research-prompt",
        )
        # RUN: prompt + report sibling.
        _write(
            self.root,
            set_id="runset",
            order=0,
            id6="prmpt2",
            slug="ask",
            status=None,
            created="20260802",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="runset",
            order=1,
            id6="rprt01",
            slug="answer",
            status="todo",
            created="20260803",
            kind="research-report",
            body="## Report\nFindings.",
        )

    def _run(self, agent=False):
        import argparse
        import io
        from contextlib import redirect_stdout

        args = argparse.Namespace(dir=str(self.root), agent=agent)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = I.run_pending(args)
        return rc, buf.getvalue()

    def test_pending_human_lists_only_unrun(self):
        rc, out = self._run(agent=False)
        self.assertEqual(rc, 0)
        self.assertIn("prmpt1", out)
        self.assertNotIn("prmpt2", out)  # RUN set prompt excluded
        self.assertNotIn("rprt01", out)

    def test_pending_agent_lists_only_unrun(self):
        rc, out = self._run(agent=True)
        self.assertEqual(rc, 0)
        lines = [ln for ln in out.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("prmpt1\t"))


class PipelinePositionDerivationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT

    def tearDown(self):
        import shutil

        shutil.rmtree(self.root, ignore_errors=True)

    def test_all_stub_comparison_set_is_unrun(self):
        _write(
            self.root,
            set_id="stubcmp",
            order=0,
            id6="prm001",
            slug="ask",
            status=None,
            created="20260801",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="stubcmp",
            order=1,
            id6="rpt001",
            slug="ans1",
            status="todo",
            created="20260801",
            kind="research-report",
            body=None,
        )
        _write(
            self.root,
            set_id="stubcmp",
            order=2,
            id6="rpt002",
            slug="ans2",
            status="todo",
            created="20260801",
            kind="research-report",
            body=None,
        )
        entries, _ = I._scan_docs(self.rroot)
        positions = I.derive_pipeline_positions(entries)
        self.assertEqual(positions.get("stubcmp"), "unrun")
        unrun = I.derive_unrun_prompts(entries)
        self.assertEqual([e.id6 for e in unrun], ["prm001"])

    def test_one_bodied_report_of_two_is_partial(self):
        _write(
            self.root,
            set_id="partset",
            order=0,
            id6="prm002",
            slug="ask",
            status=None,
            created="20260801",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="partset",
            order=1,
            id6="rpt003",
            slug="ans1",
            status="todo",
            created="20260801",
            kind="research-report",
            body="## Report\nLanded body.",
        )
        _write(
            self.root,
            set_id="partset",
            order=2,
            id6="rpt004",
            slug="ans2",
            status="todo",
            created="20260801",
            kind="research-report",
            body=None,
        )
        entries, _ = I._scan_docs(self.rroot)
        positions = I.derive_pipeline_positions(entries)
        self.assertEqual(positions.get("partset"), "partial")
        self.assertEqual(I.run_prompt_set_ids(entries), {"partset"})
        unrun = I.derive_unrun_prompts(entries)
        self.assertEqual([e.id6 for e in unrun if e.set_id == "partset"], [])

    def test_bodied_reconciliation_is_synthesized(self):
        _write(
            self.root,
            set_id="synset",
            order=0,
            id6="prm003",
            slug="ask",
            status=None,
            created="20260801",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="synset",
            order=1,
            id6="rpt005",
            slug="recon",
            status="todo",
            created="20260801",
            kind="reconciliation-report",
            body="## Summary\nReconciled findings.",
        )
        entries, _ = I._scan_docs(self.rroot)
        positions = I.derive_pipeline_positions(entries)
        self.assertEqual(positions.get("synset"), "synthesized")
        self.assertEqual(I.run_prompt_set_ids(entries), {"synset"})

    def test_adopted_lone_prompt_and_archive_lone_prompt_are_absent(self):
        _write(
            self.root,
            set_id="adoptedset",
            order=0,
            id6="prm004",
            slug="adopted-prompt",
            status=None,
            created="20260801",
            kind="research-prompt",
            outcome="adopted",
        )
        _write(
            self.root,
            set_id="archiveset",
            order=0,
            id6="prm005",
            slug="archive-prompt",
            status="archive",
            created="20260801",
            kind="research-prompt",
        )
        entries, _ = I._scan_docs(self.rroot)
        positions = I.derive_pipeline_positions(entries)
        self.assertNotIn("adoptedset", positions)
        self.assertNotIn("archiveset", positions)
        unrun = I.derive_unrun_prompts(entries)
        self.assertEqual(unrun, [])

    def test_set_with_no_prompt_is_absent(self):
        _write(
            self.root,
            set_id="noprompt",
            order=0,
            id6="rpt006",
            slug="report-only",
            status="todo",
            created="20260801",
            kind="research-report",
            body="## Body\nContent.",
        )
        entries, _ = I._scan_docs(self.rroot)
        positions = I.derive_pipeline_positions(entries)
        self.assertNotIn("noprompt", positions)


class PositionFilterTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        _write(
            self.root,
            set_id="unrunset",
            order=0,
            id6="prm010",
            slug="ask-unrun",
            status=None,
            created="20260801",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="partset",
            order=0,
            id6="prm011",
            slug="ask-part",
            status=None,
            created="20260801",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="partset",
            order=1,
            id6="rpt011",
            slug="ans-part",
            status="todo",
            created="20260801",
            kind="research-report",
            body="## Report\nLanded.",
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.root, ignore_errors=True)

    def test_query_filter_by_position(self):
        entries, _ = I._scan_docs(self.rroot)
        res_unrun = I.query(entries, position="unrun")
        self.assertEqual([e.id6 for e in res_unrun], ["prm010"])
        res_part = I.query(entries, position="partial")
        self.assertEqual([e.id6 for e in res_part], ["prm011"])
        res_syn = I.query(entries, position="synthesized")
        self.assertEqual(res_syn, [])

    def test_run_find_by_position(self):
        import argparse
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = I.run_find(
                argparse.Namespace(
                    dir=str(self.root),
                    position="unrun",
                    status=None,
                    set=None,
                    topic=None,
                    model=None,
                    kind=None,
                    id=None,
                    agent=False,
                    json=False,
                )
            )
        self.assertEqual(rc, 0)
        self.assertIn("prm010", buf.getvalue())
        self.assertNotIn("prm011", buf.getvalue())


class RepeatedFrontmatterKeyTests(unittest.TestCase):
    """Behavioral tests for research.frontmatter-key-repeated (Set jnpl08 / IPD 7d4bgs E-04)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / ".aw" / "records" / "research"
        self.rroot.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.root, ignore_errors=True)

    def _write_doc(
        self,
        id6: str = "abc001",
        slug: str = "test-doc",
        extra_fm_lines: list[str] | None = None,
        body: str = "",
        custom_frontmatter: str | None = None,
    ) -> Path:
        name = R.format_name(
            R.ResearchName(
                date="20261002",
                set_id="test",
                order="01",
                id6=id6,
                slug=slug,
                model=None,
                kind="notes",
            )
        )
        doc_path = self.rroot / name
        if custom_frontmatter is not None:
            raw = custom_frontmatter + (f"\n\n{body}\n" if body else "\n")
        else:
            base_fm = C.build_frontmatter(
                id6=id6,
                created="20261002",
                set_id="test",
                order="01",
                topic=["t1"],
                model=None,
                kind="notes",
                status="todo",
                outcome="none-yet",
                summary=f"Summary {id6}",
                consumed_by=[],
            )
            lines = base_fm.splitlines()
            extras = extra_fm_lines or []
            injected_lines = lines[:-1] + extras + ["---"]
            raw = "\n".join(injected_lines) + (f"\n\n{body}\n" if body else "\n")
        doc_path.write_text(raw, encoding="utf-8")
        return doc_path

    def test_case_1_two_status_lines(self):
        self._write_doc(
            id6="rep001", slug="two-status", extra_fm_lines=["status: reference"]
        )
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 1)
        self.assertIn("status", rep[0].detail)
        self.assertIn("2", rep[0].detail)
        self.assertEqual(rep[0].severity, "error")
        self.assertEqual(_core.drift_exit_code(drift), 1)

    def test_case_2_two_blocks_release_lines(self):
        self._write_doc(
            id6="rep002",
            slug="two-br",
            extra_fm_lines=["blocks-release: next", "blocks-release: none"],
        )
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 1)
        self.assertIn("blocks-release", rep[0].detail)
        self.assertIn("2", rep[0].detail)
        self.assertEqual(rep[0].severity, "error")
        self.assertEqual(_core.drift_exit_code(drift), 1)

    def test_case_3_blocks_release_spelling_family(self):
        self._write_doc(
            id6="rep003",
            slug="br-casing",
            extra_fm_lines=["blocks-release: next", "Blocks-Release: next"],
        )
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 1)
        self.assertIn("blocks-release", rep[0].detail)
        self.assertIn("2", rep[0].detail)
        self.assertEqual(rep[0].severity, "error")

    def test_case_4_two_id_lines_last_matching_filename(self):
        # F-03 case: last id matches filename; name-frontmatter-mismatch cannot see it
        name = R.format_name(
            R.ResearchName(
                date="20261002",
                set_id="test",
                order="01",
                id6="rep004",
                slug="two-id",
                model=None,
                kind="notes",
            )
        )
        base_fm = C.build_frontmatter(
            id6="aaaaaa",
            created="20261002",
            set_id="test",
            order="01",
            topic=["t1"],
            model=None,
            kind="notes",
            status="todo",
            outcome="none-yet",
            summary="summary rep004",
            consumed_by=[],
        )
        lines = base_fm.splitlines()
        raw = "\n".join(lines[:-1] + ["id: rep004", "---"]) + "\n"
        (self.rroot / name).write_text(raw, encoding="utf-8")
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 1)
        self.assertIn("id", rep[0].detail)
        self.assertIn("2", rep[0].detail)
        self.assertEqual(rep[0].severity, "error")
        self.assertFalse(any(d.rule == "name-frontmatter-mismatch" for d in drift))

    def test_case_5_two_different_repeated_keys_yield_two_findings(self):
        self._write_doc(
            id6="rep005",
            slug="two-keys",
            extra_fm_lines=["status: reference", "priority: high", "priority: low"],
        )
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 2)
        details = [d.detail for d in rep]
        self.assertTrue(any("status" in det and "2" in det for det in details))
        self.assertTrue(any("priority" in det and "2" in det for det in details))
        for d in rep:
            self.assertEqual(d.severity, "error")

    def test_case_6_conformant_doc_yields_zero_findings(self):
        self._write_doc(id6="rep006", slug="conformant")
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 0)
        self.assertEqual(drift, [])

    def test_case_7_body_status_line_after_closing_fence_yields_zero_findings(self):
        self._write_doc(
            id6="rep007",
            slug="body-status",
            body="## Notes\nstatus: reference\npriority: high\n",
        )
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 0)
        self.assertEqual(drift, [])

    def test_case_8_doc_with_no_closed_fence_yields_frontmatter_missing_only(self):
        self._write_doc(
            id6="rep008",
            slug="no-fence",
            custom_frontmatter=(
                "---\n"
                "id: rep008\n"
                "created: 20261002\n"
                "set: test\n"
                "order: 01\n"
                "topic: [t1]\n"
                "kind: notes\n"
                "status: todo\n"
                "outcome: none-yet\n"
                "summary: summary rep008\n"
                "consumed-by: []\n"
                "status: reference\n"
                "# Note: no closing fence\n"
            ),
        )
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 0)
        self.assertTrue(any(d.rule == "frontmatter-missing" for d in drift))

    def test_case_9_agreeing_status_lines_flagged_once(self):
        self._write_doc(
            id6="rep009", slug="agreeing-status", extra_fm_lines=["status: todo"]
        )
        drift = I.check_drift(self.root, self.rroot)
        rep = [d for d in drift if d.rule == I.FRONTMATTER_KEY_REPEATED_RULE]
        self.assertEqual(len(rep), 1)
        self.assertIn("status", rep[0].detail)
        self.assertIn("2", rep[0].detail)
        self.assertEqual(rep[0].severity, "error")

    def test_consumer_surfaces_behavior(self):
        from agent_workflows import cli

        self._write_doc(
            id6="rep010", slug="consumer-test", extra_fm_lines=["status: reference"]
        )

        # 1. aw research index --check: fails (exit 1) on repeated key
        rc_idx = cli.main(["research", "index", "--check", "--dir", str(self.root)])
        self.assertEqual(rc_idx, 1)

        # 2. aw check research --all: fails (exit 1) on repeated key
        rc_all = cli.main(["check", "research", "--all", "--dir", str(self.root)])
        self.assertEqual(rc_all, 1)

        # 3. default aw check research: passes (exit 0), content validator gated by include_retired
        rc_def = cli.main(["check", "research", "--dir", str(self.root)])
        self.assertEqual(rc_def, 0)


class StatusTierMismatchTests(unittest.TestCase):
    """Set zdsf35 / IPD ucwlwt E-04: status-versus-tier drift rule tests."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT
        self.rroot.mkdir(parents=True, exist_ok=True)

    def _write_doc(
        self,
        *,
        id6: str,
        status: str,
        tier: str = "root",
        shard_month: str = "202607",
        created: str = "20260701",
        kind: str = "notes",
    ) -> Path:
        name = R.format_name(
            R.ResearchName(
                date=created,
                set_id="testset",
                order="00",
                id6=id6,
                slug="testdoc",
                model=None,
                kind=kind,
            )
        )
        content = C.build_frontmatter(
            id6=id6,
            created=created,
            set_id="testset",
            order="00",
            topic=["test"],
            model=None,
            kind=kind,
            status=status,
            outcome="none-yet",
            summary=f"summary {id6}",
        )
        if tier == "root":
            target_dir = self.rroot
        else:
            target_dir = self.rroot / tier / shard_month
        target_dir.mkdir(parents=True, exist_ok=True)
        doc_path = target_dir / name
        doc_path.write_text(content, encoding="utf-8")
        return doc_path

    def test_case_1_cold_status_at_hot_root_flagged(self):
        # Case 1: cold-status doc at hot root is flagged (catches F-09 .value trap).
        doc = self._write_doc(id6="stm001", status="reference", tier="root")
        drift = I.check_drift(self.root, self.rroot)
        mismatches = [d for d in drift if d.rule == I.STATUS_TIER_MISMATCH_RULE]
        self.assertEqual(len(mismatches), 1)
        finding = mismatches[0]
        self.assertEqual(finding.rule, I.STATUS_TIER_MISMATCH_RULE)
        self.assertEqual(finding.severity, "warning")
        self.assertEqual(finding.location, doc.relative_to(self.rroot).as_posix())
        self.assertEqual(_core.drift_exit_code(drift), 1)

    def test_case_2_hot_status_in_reference_shard_flagged(self):
        # Case 2: hot-status doc inside a reference/ shard is flagged.
        doc = self._write_doc(id6="stm002", status="active", tier="reference")
        drift = I.check_drift(self.root, self.rroot)
        mismatches = [d for d in drift if d.rule == I.STATUS_TIER_MISMATCH_RULE]
        self.assertEqual(len(mismatches), 1)
        finding = mismatches[0]
        self.assertEqual(finding.rule, I.STATUS_TIER_MISMATCH_RULE)
        self.assertEqual(finding.severity, "warning")
        self.assertEqual(finding.location, doc.relative_to(self.rroot).as_posix())
        self.assertEqual(_core.drift_exit_code(drift), 1)

    def test_case_3_hot_status_in_archive_shard_flagged(self):
        # Case 3: hot-status doc inside an archive/ shard is flagged.
        doc = self._write_doc(id6="stm003", status="todo", tier="archive")
        drift = I.check_drift(self.root, self.rroot)
        mismatches = [d for d in drift if d.rule == I.STATUS_TIER_MISMATCH_RULE]
        self.assertEqual(len(mismatches), 1)
        finding = mismatches[0]
        self.assertEqual(finding.rule, I.STATUS_TIER_MISMATCH_RULE)
        self.assertEqual(finding.severity, "warning")
        self.assertEqual(finding.location, doc.relative_to(self.rroot).as_posix())
        self.assertEqual(_core.drift_exit_code(drift), 1)

    def test_case_4_correctly_placed_docs_produce_no_finding(self):
        # Case 4: correctly-placed doc of each tier produces NO finding of this rule.
        self._write_doc(id6="stm004", status="active", tier="root")
        self._write_doc(id6="stm005", status="reference", tier="reference")
        self._write_doc(id6="stm006", status="archive", tier="archive")
        drift = I.check_drift(self.root, self.rroot)
        mismatches = [d for d in drift if d.rule == I.STATUS_TIER_MISMATCH_RULE]
        self.assertEqual(len(mismatches), 0)
        self.assertEqual(_core.drift_exit_code(drift), 0)

    def test_case_5_legacy_intake_status_in_cold_shard_flagged(self):
        # Case 5: legacy intake-status doc inside cold shard is flagged (proves normalization).
        doc = self._write_doc(id6="stm007", status="intake", tier="reference")
        drift = I.check_drift(self.root, self.rroot)
        mismatches = [d for d in drift if d.rule == I.STATUS_TIER_MISMATCH_RULE]
        self.assertEqual(len(mismatches), 1)
        finding = mismatches[0]
        self.assertEqual(finding.rule, I.STATUS_TIER_MISMATCH_RULE)
        self.assertEqual(finding.severity, "warning")
        self.assertEqual(finding.location, doc.relative_to(self.rroot).as_posix())
        self.assertEqual(_core.drift_exit_code(drift), 1)

    def test_case_6_empty_or_unrecognized_status_produces_no_finding(self):
        # Case 6: doc whose status is EMPTY or unrecognized produces NO finding (pins F-10 skip).
        # Doc 1: empty status (e.g. .research-prompt.md)
        self._write_doc(id6="stm008", status="", tier="root")
        # Doc 2: unrecognized status token
        self._write_doc(id6="stm009", status="unrecognized-custom", tier="root")
        drift = I.check_drift(self.root, self.rroot)
        mismatches = [d for d in drift if d.rule == I.STATUS_TIER_MISMATCH_RULE]
        self.assertEqual(len(mismatches), 0)

    def test_manifest_regeneration_not_blocked_by_tier_mismatch(self):
        # V-02: emission is in check_drift ONLY, so _scan_docs drift is clean and the
        # tier-mismatched doc stays in the scan `aw find research` reads (retargeted from the
        # INDEX files, plan s6k01k).
        self._write_doc(id6="stm010", status="reference", tier="root")
        entries, scan_drift = I._scan_docs(self.rroot)
        self.assertEqual(scan_drift, [])
        self.assertEqual([e.id6 for e in entries], ["stm010"])
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == I.STATUS_TIER_MISMATCH_RULE for d in drift))


if __name__ == "__main__":
    unittest.main()
