"""Tests for aw ipd scaffold + non-destructive sync (Set ipd-structure, Order 03).

Covers scaffold args/defaults/metadata + dry-run/apply/overwrite + atomic write; sync placeholder
recognition, monotonic watermark assignment, gap stability, no-reuse-after-deletion, matching V
skeletons, content preservation, and refusal after execution/approval. Stdlib unittest.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import tempfile
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S


def _ns(**kw) -> argparse.Namespace:
    base = dict(
        kind=None,
        title=None,
        path=None,
        set=None,
        order=None,
        author=None,
        apply=False,
        overwrite=False,
        legacy_name=True,
        # planprio lkexaw: scaffold refuses without decided values (or --from-backlog).
        priority="medium",
        work_kind="chore",
        from_backlog=None,
    )
    base.update(kw)
    return argparse.Namespace(**base)


def _run(fn, ns) -> tuple:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(ns)
    return rc, buf.getvalue()


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_dry_run_writes_nothing(self):
        target = self.tmp / "a.md"
        rc, out = _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
            ),
        )
        self.assertEqual(rc, 0)
        self.assertFalse(target.exists())
        self.assertTrue("would write" in out or "create" in out or "applied" in out)

    def test_apply_writes_conforming_child(self):
        target = self.tmp / "b.md"
        rc, _ = _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 0)
        self.assertTrue(target.exists())
        res = L.lint_text(target.read_text(), checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_scaffold_emits_scope_paths_stub(self):
        # Order oorry1: scaffold emits a Scope-Paths metadata stub, and the stub still lints
        # clean at the author phase (the field is recognized-but-optional, and the checkpoint
        # requirement does not fire while drafting).
        text = A.build_skeleton(
            kind="child",
            title="t",
            author="tester",
            when="2026-08-24",
            set_name="x",
            order=1,
            plan_id="abc123",
        )
        meta_lines = []
        for ln in text.splitlines():
            if ln.startswith("## "):
                break
            meta_lines.append(ln)
        self.assertTrue(
            any(ln.startswith("- Scope-Paths:") for ln in meta_lines),
            "scaffold must emit a Scope-Paths metadata stub",
        )
        res = L.lint_text(text, checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_apply_writes_conforming_orchestrator(self):
        target = self.tmp / "orch.md"
        rc, _ = _run(
            A.run_scaffold,
            _ns(
                kind="orchestrator",
                title="o (Set x, Order 0)",
                path=str(target),
                set="x",
                order=0,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 0)
        res = L.lint_text(target.read_text(), checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_scaffold_emits_unique_valid_id(self):
        # plans-adopter Order 02: scaffold emits a valid, collision-checked `- Id:`.
        import re as _re

        def _scaffold(name):
            target = self.tmp / name
            _run(
                A.run_scaffold,
                _ns(
                    kind="child",
                    title="t (Set x, Order 1)",
                    path=str(target),
                    set="x",
                    order=1,
                    author="tester",
                    apply=True,
                ),
            )
            m = _re.search(r"(?m)^- Id: ([0-9a-z]{6})$", target.read_text())
            return m.group(1) if m else None

        id_a = _scaffold("ida.md")
        id_b = _scaffold("idb.md")
        self.assertIsNotNone(id_a)
        self.assertIsNotNone(id_b)
        self.assertNotEqual(id_a, id_b)

    def test_overwrite_refused_without_flag(self):
        target = self.tmp / "c.md"
        target.write_text("existing\n")
        rc, out = _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 1)
        self.assertTrue(
            "refusing to overwrite" in out
            or "ipd.scaffold_refused" in out
            or "findings" in out
        )
        self.assertEqual(target.read_text(), "existing\n")

    def test_orchestrator_order_must_be_zero(self):
        target = self.tmp / "d.md"
        rc, out = _run(
            A.run_scaffold,
            _ns(
                kind="orchestrator",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 2)

    def test_set_without_order_rejected(self):
        target = self.tmp / "e.md"
        rc, out = _run(
            A.run_scaffold,
            _ns(kind="child", title="t", path=str(target), set="x", author="tester"),
        )
        self.assertEqual(rc, 2)
        self.assertIn("--order is required", out)

    def test_order_without_set_rejected(self):
        target = self.tmp / "e2.md"
        rc, out = _run(
            A.run_scaffold,
            _ns(kind="child", title="t", path=str(target), order=1, author="tester"),
        )
        self.assertEqual(rc, 2)
        self.assertIn("--set is required", out)

    def test_author_required(self):
        target = self.tmp / "f.md"
        old = os.environ.pop("AW_IPD_AUTHOR", None)
        try:
            rc, out = _run(
                A.run_scaffold,
                _ns(
                    kind="child",
                    title="t (Set x, Order 1)",
                    path=str(target),
                    set="x",
                    order=1,
                ),
            )
            self.assertEqual(rc, 2)
        finally:
            if old is not None:
                os.environ["AW_IPD_AUTHOR"] = old


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "plan.md"
        _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(self.path),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )

    def _add_unassigned(self, n=1):
        t = self.path.read_text()
        marker = "  - Execution state: pending\n"
        idx = t.index(marker) + len(marker)
        block = ""
        for _ in range(n):
            block += (
                f"- [ ] {A.UNASSIGNED_MARKER} TODO action.\n  - Depends on: none\n"
                "  - Expected outcome: TODO.\n  - Execution state: pending\n"
            )
        self.path.write_text(t[:idx] + block + t[idx:])

    def test_sync_assigns_from_watermark_and_advances(self):
        self._add_unassigned(2)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 0)
        t = self.path.read_text()
        # scaffold shipped E-01 (watermark 01); two new leaves -> E-02, E-03; watermark -> 03.
        self.assertIn("- [ ] E-02", t)
        self.assertIn("- [ ] E-03", t)
        self.assertIn("- Highest E allocated: 03", t)
        self.assertIn("- [ ] V-02 validates E-02", t)
        self.assertIn("- [ ] V-03 validates E-03", t)
        res = L.lint_text(t, checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_sync_backfills_missing_id_and_leaves_present_id(self):
        # plans-adopter Order 02: sync backfills a missing `- Id:`, leaves an existing one.
        import re as _re

        t = self.path.read_text()
        m0 = _re.search(r"(?m)^- Id: ([0-9a-z]{6})$", t)
        self.assertIsNotNone(m0)  # scaffold already emitted one
        # Strip the Id to simulate a legacy plan lacking it.
        t_noid = _re.sub(r"(?m)^- Id: [0-9a-z]{6}\n", "", t)
        self.path.write_text(t_noid)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 0)
        t_after = self.path.read_text()
        m1 = _re.search(r"(?m)^- Id: ([0-9a-z]{6})$", t_after)
        self.assertIsNotNone(m1)  # backfilled
        # Running sync again does not add a second Id or change the existing one.
        existing = m1.group(1)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        ids = _re.findall(r"(?m)^- Id: ([0-9a-z]{6})$", self.path.read_text())
        self.assertEqual(ids, [existing])

    def test_dry_run_writes_nothing(self):
        self._add_unassigned(1)
        before = self.path.read_text()
        rc, out = _run(A.run_sync, _ns(path=str(self.path)))
        self.assertEqual(rc, 0)
        self.assertEqual(self.path.read_text(), before)
        self.assertTrue("would assign" in out or "update" in out or "applied" in out)

    def test_no_reuse_after_deleting_highest(self):
        # Assign up to E-03 (watermark 03), then delete the highest E and its V, then add one.
        self._add_unassigned(2)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        t = self.path.read_text()
        # remove E-03 leaf + V-03 row (pre-approval deletion of the highest).
        t = re.sub(r"- \[ \] E-03 .*?\n(?:  - .*\n)+", "", t)
        t = re.sub(r"- \[ \] V-03 validates E-03\n(?:  - .*\n)+", "", t)
        self.path.write_text(t)
        self.assertIn(
            "- Highest E allocated: 03", self.path.read_text()
        )  # watermark not decreased
        # Add a new leaf and sync: it must get E-04 (above watermark), NOT reuse E-03.
        self._add_unassigned(1)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        t = self.path.read_text()
        self.assertIn("- [ ] E-04", t)
        self.assertNotIn("- [ ] E-03", t)
        self.assertIn("- Highest E allocated: 04", t)

    def test_refuses_after_execution_begun(self):
        # Add an unassigned leaf FIRST, then mark the scaffolded E-01 performed -> execution has
        # begun -> sync must refuse (do not consume the pending marker before adding the leaf).
        self._add_unassigned(1)
        t = (
            self.path.read_text()
            .replace("- [ ] E-01", "- [x] E-01")
            .replace(
                "  - Execution state: pending", "  - Execution state: performed", 1
            )
        )
        self.path.write_text(t)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 1)
        self.assertTrue(
            "execution has begun" in out or "ipd.sync_error" in out or "findings" in out
        )

    def test_refuses_when_approved(self):
        t = (
            self.path.read_text()
            .replace("- Status: draft", "- Status: approved")
            .replace(
                "- Author: tester",
                "- Approval: approved by x 2026-08-03\n- Author: tester",
            )
        )
        self.path.write_text(t)
        self._add_unassigned(1)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 1)
        self.assertTrue(
            "Status is 'approved'" in out
            or "ipd.sync_error" in out
            or "findings" in out
        )

    def test_preserves_existing_content(self):
        # Author real evidence text into V-01, then sync a new leaf; the evidence must survive.
        t = self.path.read_text().replace(
            "  - Required evidence: TODO falsifiable evidence.",
            "  - Required evidence: the artifact exists at PATH-X.",
            1,
        )
        self.path.write_text(t)
        self._add_unassigned(1)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertIn("the artifact exists at PATH-X.", self.path.read_text())

    def test_missing_watermark_refused(self):
        t = self.path.read_text().replace("- Highest E allocated: 01\n", "")
        self.path.write_text(t)
        self._add_unassigned(1)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 1)
        self.assertTrue(
            "Highest E allocated" in out or "ipd.sync_error" in out or "findings" in out
        )

    def test_no_unassigned_is_noop(self):
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 0)
        self.assertTrue("nothing to sync" in out or "clean" in out)


class AtomicWriteTests(unittest.TestCase):
    def test_atomic_write_leaves_no_temp(self):
        tmp = Path(tempfile.mkdtemp())
        target = tmp / "x.md"
        A._atomic_write(target, "hello\n")
        self.assertEqual(target.read_text(), "hello\n")
        leftovers = [p for p in tmp.iterdir() if p.name.startswith(".ipd-tmp-")]
        self.assertEqual(leftovers, [])


class NoDependencyTests(unittest.TestCase):
    @unittest.skipIf(
        sys.version_info < (3, 10),
        "sys.stdlib_module_names (the stdlib census this check uses) exists only on Python 3.10+",
    )
    def test_authoring_module_is_stdlib_only(self):
        code = (
            "import sys\n"
            "class StrictStdlibFinder:\n"
            "    def find_spec(self, fullname, path, target=None):\n"
            "        top = fullname.split('.')[0]\n"
            "        if top not in sys.stdlib_module_names and top != 'agent_workflows':\n"
            "            raise ImportError(f'Non-stdlib import attempted: {fullname}')\n"
            "        return None\n"
            "sys.meta_path.insert(0, StrictStdlibFinder())\n"
            "import agent_workflows.ipd_authoring\n"
        )
        res = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        )
        self.assertEqual(
            res.returncode,
            0,
            f"Module import failed or attempted non-stdlib import: {res.stderr}",
        )


class AtomicWriteDelegatesToCoreTests(unittest.TestCase):
    """`_atomic_write` must DELEGATE, not duplicate, so plans inherit the shared normalization.

    WHY THIS IS NOT A STYLE POINT (IPD `lqly9m` E-10). This module used to keep a byte-for-byte COPY of
    `artifact_core.atomic_write`, and `aw ipd scaffold`/`aw ipd sync` write plans through it. So
    normalizing only the core helper would have left PLANS -- the highest-volume artifact an agent
    writes, and the one the mutating pre-commit hooks reject most often -- entirely un-normalized.
    """

    def test_a_plan_written_through_it_carries_no_trailing_whitespace(self):
        tmp = Path(tempfile.mkdtemp())
        target = tmp / "p.ipd.md"
        A._atomic_write(target, "# IPD: x\n\nbody with trailing   \nsecond\t\n\n\n")
        text = target.read_text(encoding="utf-8")
        self.assertEqual([ln for ln in text.split("\n") if ln != ln.rstrip()], [])
        self.assertTrue(text.endswith("\n"))
        self.assertFalse(text.endswith("\n\n"))
        self.assertEqual(
            [p for p in tmp.iterdir() if p.name.startswith(".ipd-tmp-")], []
        )

    def test_scaffold_and_sync_both_write_a_clean_plan(self):
        """Proven THROUGH THE REAL VERBS, since the helper alone was never the risk."""
        tmp = Path(tempfile.mkdtemp())
        target = tmp / "20260916-wsprobe-01-zz9zz9-probe.ipd.md"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.run_scaffold(
                _ns(
                    kind="child",
                    title="Probe",
                    path=str(target),
                    set="wsprobe",
                    order=1,
                    author="opencode test",
                    apply=True,
                )
            )
        self.assertEqual(rc, 0, buf.getvalue())
        scaffolded = target.read_text(encoding="utf-8")
        self.assertEqual([ln for ln in scaffolded.split("\n") if ln != ln.rstrip()], [])

        # Hand-inject dirt (NOT through the write path) plus an unassigned leaf, then sync.
        dirty = scaffolded.replace(
            "- [ ] E-01",
            "- [ ] E-NEW a new leaf with trailing whitespace   \n"
            "  - Depends on: none\n"
            "  - Expected outcome: TODO observable result.\n"
            "  - Execution state: pending\n\n"
            "- [ ] E-01",
            1,
        )
        target.write_text(dirty, encoding="utf-8")
        self.assertTrue([ln for ln in dirty.split("\n") if ln != ln.rstrip()])

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.run_sync(argparse.Namespace(path=str(target), apply=True))
        self.assertEqual(rc, 0, buf.getvalue())
        synced = target.read_text(encoding="utf-8")
        self.assertEqual([ln for ln in synced.split("\n") if ln != ln.rstrip()], [])


class ScaffoldDurableCarrierGateTests(unittest.TestCase):
    """Scaffolded plans pass the durable-carrier gate without being stubs (plan vtkfq8 E-02)."""

    def test_scaffold_passes_carrier_gate_and_remains_stub_and_flags_on_real_question(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            pending_dir = repo_root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)

            text = A.build_skeleton(
                title="Carrier Gate Probe",
                plan_id="abc123",
                kind="child",
                author="tester",
                when="2026-09-26",
                set_name="carriergate",
                order=1,
            )
            plan_file = (
                pending_dir / "20260926-carriergate-01-abc123-carrier-gate-probe.ipd.md"
            )
            plan_file.write_text(text, encoding="utf-8")

            from agent_workflows import check_engine as ce

            # Assertion 1: check_durable_carrier returns no findings for plan AS SCAFFOLDED
            findings = ce.check_durable_carrier(repo_root)
            self.assertEqual(findings, [])

            # Assertion 2: untouched scaffold still reports unfinished via authoring_placeholders_resolved
            self.assertFalse(A.authoring_placeholders_resolved(text))

            # Assertion 3: editing example question heading to a real heading with - Status: open
            # and no carrier MUST still produce the check.ipd-uncarried-obligation finding
            edited_text = text.replace(
                "### OQ-01: TODO a question", "### OQ-01: Real question to be answered?"
            )
            plan_file.write_text(edited_text, encoding="utf-8")
            findings_edited = ce.check_durable_carrier(repo_root)
            self.assertEqual(len(findings_edited), 1)
            self.assertEqual(findings_edited[0].rule, "check.ipd-uncarried-obligation")
            self.assertIn("OQ-01", findings_edited[0].detail)


class ScaffoldVocabularyIntroTests(unittest.TestCase):
    """Scaffolded plans must state both closed vocabularies in their section intros (plan uh9jsk)."""

    def test_scaffold_intros_state_closed_vocabularies_and_no_unaccepted_values(self):
        expected_exec = set(S.EXEC_STATES)
        expected_valid = set(S.VALIDATION_RESULTS)

        for kind in ("child", "orchestrator"):
            text = A.build_skeleton(
                kind=kind,
                title=f"Vocabulary Intro Test {kind}",
                author="tester",
                when="2026-10-01",
                set_name="vocabprobe",
                order=1 if kind == "child" else 0,
                plan_id="vcb123",
            )
            # Locate intro lines in the scaffold by their section headings
            lines = text.splitlines()
            exec_intro = None
            valid_intro = None
            for i, line in enumerate(lines):
                if line.startswith("## ") and line[3:].strip() == S.H_EXECUTION:
                    for candidate in lines[i + 1 : i + 5]:
                        if candidate.startswith("Execution-state rule:"):
                            exec_intro = candidate
                            break
                elif line.startswith("## ") and line[3:].strip() in (
                    S.H_VALIDATION_CHILD,
                    S.H_VALIDATION_ORCH,
                ):
                    for candidate in lines[i + 1 : i + 5]:
                        if candidate.startswith("Validation-state rule:"):
                            valid_intro = candidate
                            break

            self.assertIsNotNone(
                exec_intro, f"missing execution intro in {kind} scaffold"
            )
            self.assertIsNotNone(
                valid_intro, f"missing validation intro in {kind} scaffold"
            )

            # Positive assertions: every member of the closed vocabulary is stated
            for state in expected_exec:
                self.assertIn(
                    state,
                    exec_intro,
                    f"execution intro in {kind} missing member {state!r}",
                )
            for result in expected_valid:
                self.assertIn(
                    result,
                    valid_intro,
                    f"validation intro in {kind} missing member {result!r}",
                )

            # Terminal gate demand is stated
            self.assertIn("'performed'", exec_intro)
            self.assertIn("'pass'", valid_intro)

            # Negative assertions: extract the rendered value list from each intro
            # and verify NO token is outside the frozenset.
            m_exec = re.search(r"Accepted execution states:\s*([^;]+);", exec_intro)
            self.assertIsNotNone(
                m_exec, f"could not locate execution states list in {kind} intro"
            )
            exec_tokens = {t.strip() for t in m_exec.group(1).split(",") if t.strip()}
            unrecognized_exec = exec_tokens - expected_exec
            self.assertEqual(
                unrecognized_exec,
                set(),
                f"execution intro in {kind} advertises out-of-vocabulary value: {unrecognized_exec}",
            )
            self.assertEqual(
                exec_tokens,
                expected_exec,
                f"execution intro in {kind} does not match EXEC_STATES",
            )

            m_valid = re.search(r"Accepted validation results:\s*([^;]+);", valid_intro)
            self.assertIsNotNone(
                m_valid, f"could not locate validation results list in {kind} intro"
            )
            valid_tokens = {t.strip() for t in m_valid.group(1).split(",") if t.strip()}
            unrecognized_valid = valid_tokens - expected_valid
            self.assertEqual(
                unrecognized_valid,
                set(),
                f"validation intro in {kind} advertises out-of-vocabulary value: {unrecognized_valid}",
            )
            self.assertEqual(
                valid_tokens,
                expected_valid,
                f"validation intro in {kind} does not match VALIDATION_RESULTS",
            )


class ConformingOrchestratorScaffoldTests(unittest.TestCase):
    """Plan zojfn6: scaffolded orchestrator conforms to the typed row grammar and gates begin."""

    def test_scaffolded_orchestrator_conforms_to_row_grammar(self):
        text = A.build_skeleton(
            kind="orchestrator",
            title="A title",
            author="tester",
            when="2026-10-01",
            set_name="testset",
            order=0,
            plan_id="tmp1d6",
            priority="medium",
            work_kind="chore",
        )
        res = L.orchestrator_row_conformance(text)
        self.assertTrue(res.applies)
        self.assertTrue(res.conforming)
        self.assertEqual(res.table_reason, "")
        self.assertEqual(len(res.rows), 1)
        row = res.rows[0]
        self.assertEqual(row.ident, "E-01")
        self.assertEqual(row.child_id6, "c0ch01")
        self.assertEqual(row.status, "executed")
        self.assertEqual(row.depends_on, "none")
        self.assertTrue(row.conforming)

    def test_child_skeleton_unaffected_and_row_rule_does_not_apply(self):
        text = A.build_skeleton(
            kind="child",
            title="A title",
            author="tester",
            when="2026-10-01",
            set_name="testset",
            order=1,
            plan_id="tmp1d6",
            priority="medium",
            work_kind="chore",
        )
        res = L.orchestrator_row_conformance(text)
        self.assertFalse(res.applies)
        self.assertTrue(res.conforming)
        self.assertIn("- [ ] E-01 TODO one observable action.", text)

    def test_authoring_placeholders_resolved_reports_fresh_scaffolds_as_unresolved(
        self,
    ):
        orch = A.build_skeleton(
            kind="orchestrator",
            title="A title",
            author="tester",
            when="2026-10-01",
            set_name="testset",
            order=0,
            plan_id="tmp1d6",
            priority="medium",
            work_kind="chore",
        )
        child = A.build_skeleton(
            kind="child",
            title="A title",
            author="tester",
            when="2026-10-01",
            set_name="testset",
            order=1,
            plan_id="tmp1d6",
            priority="medium",
            work_kind="chore",
        )
        self.assertFalse(A.authoring_placeholders_resolved(orch))
        self.assertFalse(A.authoring_placeholders_resolved(child))

    def test_begin_and_pre_execution_gate_untyped_orchestrator(self):
        from agent_workflows import ipd_lifecycle as LC

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "t@e.com"], cwd=root, check=True
            )
            subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
            (root / "init.txt").write_text("init\n")
            subprocess.run(["git", "add", "init.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)

            fresh_text = A.build_skeleton(
                kind="orchestrator",
                title="Fresh Orch",
                author="tester",
                when="2026-10-01",
                set_name="testset",
                order=0,
                plan_id="orc001",
                priority="medium",
                work_kind="chore",
            )
            p_fresh = root / "fresh.ipd.md"
            p_fresh.write_text(fresh_text, encoding="utf-8")

            untyped_text = fresh_text.replace(
                "- [ ] E-01 CONFIRM c0ch01 REACHED executed",
                "- [ ] E-01 TODO one observable action.",
            )
            p_untyped = root / "untyped.ipd.md"
            p_untyped.write_text(untyped_text, encoding="utf-8")

            # 1. begin on untyped orchestrator fails with IPD-S407 in findings
            res_untyped = LC.begin(
                root, p_untyped, "tester model=m", timestamp="2026-10-01T00:00:00Z"
            )
            self.assertEqual(res_untyped.exit_code, LC.EXIT_FINDINGS)
            s407_findings = [f for f in res_untyped.findings if "IPD-S407" in f]
            self.assertTrue(len(s407_findings) > 0, res_untyped.findings)

            # 2. begin on freshly scaffolded orchestrator does NOT produce IPD-S407
            res_fresh = LC.begin(
                root, p_fresh, "tester model=m", timestamp="2026-10-01T00:00:00Z"
            )
            s407_fresh = [f for f in res_fresh.findings if "IPD-S407" in f]
            self.assertEqual(len(s407_fresh), 0, res_fresh.findings)

            # 3. pre-execution lint on untyped plan returns IPD-S407 diagnostic
            res_lint = L.lint_file(p_untyped, checkpoint="pre-execution")
            s407_diags = [d for d in res_lint.diagnostics if d.code == L.C_ORCH_ROW]
            self.assertTrue(len(s407_diags) > 0)


if __name__ == "__main__":
    unittest.main()
