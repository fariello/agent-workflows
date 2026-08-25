"""Tests for the research index generator + find + --check (Set research-org, Order 03).

Stdlib unittest, throwaway dirs. Verifies JSON completeness, INDEX.md bounding (archive excluded,
reference included, intake shown, N honored), determinism (regenerate twice byte-identical), find
filters, and --check across the spec-5.2 four drift classes including dangling citations (via the
Order 04 detector).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import research_contract as R
from agent_workflows import research_cmd as C
from agent_workflows import research_index as I


def _write(
    root: Path, *, set_id, order, id6, slug, status, created, kind="notes", model=None
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
        outcome="none-yet",
        summary=f"summary {id6}",
    )
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
        entries, drift = I._scan_docs(self.rroot)
        self.assertEqual(drift, [])
        ids = {e.id6 for e in entries}
        self.assertEqual(ids, {"aaaaaa", "bbbbbb", "cccccc"})

    def test_index_md_archive_excluded_reference_included_intake_shown(self):
        entries, _ = I._scan_docs(self.rroot)
        md = I.build_index_md(entries)
        self.assertIn("aaaaaa", md)  # intake shown
        self.assertIn("bbbbbb", md)  # reference included
        self.assertNotIn("cccccc", md)  # archive excluded
        self.assertIn("Needs addressing (intake)", md)

    def test_n_honored(self):
        # Add more hot docs and bound to 2.
        for i in range(5):
            _write(
                self.root,
                set_id=f"s{i}",
                order=0,
                id6=f"d{i}{i}{i}{i}{i}",
                slug="x",
                status="active",
                created="2026080%d" % (i + 1),
            )
        entries, _ = I._scan_docs(self.rroot)
        md = I.build_index_md(entries, limit=2)
        # "Most recent" section should list only 2 bullets.
        recent_block = md.split("## Most recent")[1]
        bullets = [ln for ln in recent_block.splitlines() if ln.startswith("- `")]
        self.assertEqual(len(bullets), 2)

    def test_determinism(self):
        entries, _ = I._scan_docs(self.rroot)
        a = I.build_index_json(entries) + I.build_index_md(entries)
        entries2, _ = I._scan_docs(self.rroot)
        b = I.build_index_json(entries2) + I.build_index_md(entries2)
        self.assertEqual(a, b)


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
            status="reference",
            created="20260701",
        )

    def _regen(self):
        entries, _ = I._scan_docs(self.rroot)
        (self.rroot / I.INDEX_JSON).write_text(
            I.build_index_json(entries), encoding="utf-8"
        )
        (self.rroot / I.INDEX_MD).write_text(
            I.build_index_md(entries), encoding="utf-8"
        )

    def test_clean_after_regen(self):
        self._regen()
        drift = I.check_drift(self.root, self.rroot)
        self.assertEqual(drift, [])

    def test_stale_index_detected(self):
        self._regen()
        (self.rroot / I.INDEX_MD).write_text("stale", encoding="utf-8")
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == "stale-index" for d in drift))

    def test_invalid_frontmatter_detected(self):
        # A file with frontmatter missing 'id'.
        bad = self.rroot / "20260701-alpha-01-zzzzzz-bad.notes.md"
        bad.write_text(
            "---\ncreated: 20260701\nkind: notes\nstatus: intake\n---\n",
            encoding="utf-8",
        )
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == "frontmatter-invalid" for d in drift))

    def test_dangling_citation_detected(self):
        self._regen()
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
            status="intake",
            created="20260801",
            kind="research-prompt",
        )
        # RUN: a NN=00 research-prompt WITH a NN=01 report sibling.
        _write(
            self.root,
            set_id="runset",
            order=0,
            id6="prmpt2",
            slug="ask",
            status="intake",
            created="20260802",
            kind="research-prompt",
        )
        _write(
            self.root,
            set_id="runset",
            order=1,
            id6="rprt01",
            slug="answer",
            status="intake",
            created="20260803",
            kind="research-report",
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

    def _regen(self):
        entries, _ = I._scan_docs(self.rroot)
        (self.rroot / I.INDEX_JSON).write_text(
            I.build_index_json(entries), encoding="utf-8"
        )
        (self.rroot / I.INDEX_MD).write_text(
            I.build_index_md(entries), encoding="utf-8"
        )

    def _write_plan(self, disposition, id6_cite, plan_id="pln001"):
        d = self.root / ".aw" / "records" / "plans" / disposition
        d.mkdir(parents=True, exist_ok=True)
        (d / f"20260801-set-01-{plan_id}-x.ipd.md").write_text(
            f"# Plan\n\n- Id: {plan_id}\n\nUses research RSCH-{id6_cite} for context.\n",
            encoding="utf-8",
        )

    def test_trigger_a_run_set_flags_intake_and_clean_after_promote(self):
        # A RUN prompt-set with an intake report member -> stale-state-to-promote.
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
        rpt = _write(
            self.root,
            set_id="runset",
            order=1,
            id6="rprt01",
            slug="answer",
            status="intake",
            created="20260803",
            kind="research-report",
        )
        self._regen()
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
        self._regen()
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
        self._regen()
        self._write_plan("pending", "solo11", plan_id="pln001")
        drift = I.check_drift(self.root, self.rroot)
        self.assertFalse(
            any(d.rule == I.STALE_STATE_RULE for d in drift),
            "a pending-only citer must NOT flag the intake doc",
        )
        # Now cited by an EXECUTED plan -> flagged.
        self._write_plan("executed", "solo11", plan_id="pln002")
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
            "# Spec\n\n- Status: implemented\n\ncites RSCH-solo11 here\n",
            encoding="utf-8",
        )
        cited = I.cited_by_executed_ids(self.root, self.rroot)
        self.assertIn("solo11", cited)
        # a draft spec citer does NOT count
        (sp / "20260801-02-spc002-y.spec.md").write_text(
            "# Spec\n\n- Status: draft\n\ncites RSCH-nofind here\n", encoding="utf-8"
        )
        cited2 = I.cited_by_executed_ids(self.root, self.rroot)
        self.assertNotIn("nofind", cited2)


class ConsumedByIndexTests(unittest.TestCase):
    """IPD xjrdjp E-02: INDEX.json carries consumed-by."""

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
        js = I.build_index_json(entries)
        self.assertIn('"consumed_by"', js)
        self.assertIn("pln001", js)


class ConsumedByValidationTests(unittest.TestCase):
    """IPD xjrdjp E-03: --check flags dangling consumed-by + adopted-without-consumer."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / R.RESEARCH_ROOT

    def _regen(self):
        entries, _ = I._scan_docs(self.rroot)
        (self.rroot / I.INDEX_JSON).write_text(
            I.build_index_json(entries), encoding="utf-8"
        )
        (self.rroot / I.INDEX_MD).write_text(
            I.build_index_md(entries), encoding="utf-8"
        )

    def _write_plan_with_id(self, plan_id):
        d = self.root / ".aw" / "records" / "plans" / "executed"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"20260801-set-01-{plan_id}-x.ipd.md").write_text(
            f"# Plan\n\n- Id: {plan_id}\n\nbody\n", encoding="utf-8"
        )

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
        self._regen()
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
        self._write_plan_with_id("pln001")
        self._regen()
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
        self._regen()
        drift = I.check_drift(self.root, self.rroot)
        self.assertTrue(any(d.rule == I.ADOPTED_NO_CONSUMER_RULE for d in drift))
        # give it a resolving consumer -> clears.
        self._write_plan_with_id("pln002")
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "consumed-by: []", "consumed-by: [pln002]"
            ),
            encoding="utf-8",
        )
        self._regen()
        drift2 = I.check_drift(self.root, self.rroot)
        self.assertFalse(any(d.rule == I.ADOPTED_NO_CONSUMER_RULE for d in drift2))

    def test_resolvable_consumer_ids_spans_trees(self):
        # plan, spec, backlog ids all resolve.
        self._write_plan_with_id("pln003")
        sp = self.root / ".aw" / "records" / "specs"
        sp.mkdir(parents=True, exist_ok=True)
        (sp / "20260801-01-spc003-x.spec.md").write_text(
            "# Spec\n\n- Id: spc003\n", encoding="utf-8"
        )
        bk = self.root / ".aw" / "records" / "backlog" / "open"
        bk.mkdir(parents=True, exist_ok=True)
        (bk / "item.md").write_text("- Id: bkl003\n- Status: open\n", encoding="utf-8")
        ids = I.resolvable_consumer_ids(self.root)
        self.assertTrue({"pln003", "spc003", "bkl003"}.issubset(ids))


class RunIndexOutputTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.rroot = self.root / ".agents" / "docs" / "research"
        _write(
            self.root,
            set_id="alpha",
            order=0,
            id6="aaaaaa",
            slug="a",
            status="intake",
            created="20260701",
        )

    def test_run_index_change_detection_and_output(self):
        import argparse
        import io
        from contextlib import redirect_stdout

        args = argparse.Namespace(
            dir=str(self.root), limit=None, check=False, quiet=False, no_color=True
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = I.run_index(args)
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("wrote", out)
        self.assertIn(".agents/docs/research/INDEX.json, INDEX.md", out)
        self.assertIn("(1 docs)", out)

        # Second run: up to date
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = I.run_index(args)
        self.assertEqual(rc2, 0)
        out2 = buf2.getvalue()
        self.assertIn("up to date", out2)
        self.assertIn(".agents/docs/research/INDEX.json, INDEX.md", out2)


class DefaultLimitTests(unittest.TestCase):
    def test_default_is_40(self):
        self.assertEqual(I.DEFAULT_INDEX_LIMIT, 40)


if __name__ == "__main__":
    unittest.main()
