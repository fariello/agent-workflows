"""agentadhere Phase 1 (IPD uisjns): versioned policy engine + fixture corpus.

Covers the three E-items:
  E-01 - the versioned policy schema + enriched finding shape (rule id, severity, assurance class,
         observed/required, recovery, determinism tag, schema_version), backward compatibility, and
         determinism.
  E-02 - a positive + ADVERSARIAL fixture corpus with per-rule-id equality for EVERY invariant the
         phase-1 engine actually encodes today.
  E-03 - the `check.ipd-draft-ready-to-review` detect-and-nudge rule + the `authoring_placeholders_resolved`
         predicate + the `aw ipd lint --phase author` passing nudge.

DEFERRED adversarial cases (DECISION 14-uisjns-D1): findings section 9 also lists code-before-IPD,
out-of-scope staged tree, claimed-but-unrun / stale-tree test evidence, and missing/disabled/malformed
hook. Those invariants (Phase-0 catalog I-01 scope, I-05/I-06 evidence, hook-presence) are delivered by
agentadhere phases 2-5 and have NO `check_engine` rule yet, so their adversarial fixtures belong to the
phases that introduce their rules. Phase 1 covers exactly the rules the engine encodes today.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from agent_workflows import ipd_authoring as authoring
from agent_workflows import ipd_lint as lint


# --------------------------------------------------------------------------------------
# E-01: versioned schema + enriched finding shape + backward compatibility + determinism
# --------------------------------------------------------------------------------------


class TestPolicySchemaAndFindingShape(unittest.TestCase):
    def test_drift_backward_compatible_three_arg(self):
        # A 3-arg Drift still constructs and reads exactly as before (anti-regression).
        d = core.Drift("loc", "check.name-nonconformant", "detail")
        self.assertEqual(
            (d.location, d.rule, d.detail),
            ("loc", "check.name-nonconformant", "detail"),
        )
        # the enrichment fields default empty
        self.assertEqual(d.observed, "")
        self.assertEqual(d.assurance, "")
        self.assertEqual(d.severity, "")

    def test_rule_registry_has_assurance_and_determinism(self):
        spec = ce.rule_spec("check.status-untooled")
        self.assertEqual(spec.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)
        self.assertEqual(spec.invariant, "I-03")
        # unknown rule -> conservative default, never silently unclassified
        dflt = ce.rule_spec("check.totally-unknown-rule")
        self.assertEqual(dflt.severity, "error")
        self.assertEqual(dflt.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(dflt.determinism, ce.DET_DETERMINISTIC)

    def test_finding_dict_full_shape(self):
        d = ce.enrich_drift(
            core.Drift("p", "check.name-nonconformant", "bad name"),
            recovery="aw rename ...",
        )
        fd = ce.finding_dict(d)
        for key in (
            "schema_version",
            "rule",
            "severity",
            "assurance",
            "determinism",
            "invariant",
            "location",
            "detail",
            "observed",
            "required",
            "recovery",
        ):
            self.assertIn(key, fd, f"finding shape missing {key}")
        self.assertEqual(fd["schema_version"], ce.POLICY_SCHEMA_VERSION)
        self.assertEqual(fd["assurance"], ce.ASSURANCE_REPOSITORY)
        self.assertEqual(fd["recovery"], "aw rename ...")

    def test_determinism_repeated_runs_identical(self):
        # V-01(c): two consecutive engine runs on the same tree produce identical findings.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        specs = root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True)
        (specs / "20260828-1200-01-legacy.spec.md").write_text(
            "# Spec: x\n\n- Date: 2026-08-28\n- Status: reviewed\n\n"
            "## Workflow history\n\n- 2026-08-28 created (aw specs): x\n",
            encoding="utf-8",
        )
        run1 = [
            ce.finding_dict(ce.enrich_drift(d), root)
            for d in ce.check_type(root, "specs")
        ]
        run2 = [
            ce.finding_dict(ce.enrich_drift(d), root)
            for d in ce.check_type(root, "specs")
        ]
        self.assertEqual(run1, run2)

    def test_backward_compat_characterization(self):
        # V-01(d): the enrichment did not change the 3-field Drift contract that existing consumers
        # (render_agent_drift, drift_exit_code, the two installed hooks) rely on. render_agent_drift
        # still emits the exact `location\trule\tdetail` triple, and a legacy 3-field Drift still
        # drives the historical exit code.
        d = core.Drift("some/loc.md", "check.name-nonconformant", "bad name")
        self.assertEqual(
            core.render_agent_drift([d]),
            "some/loc.md\tcheck.name-nonconformant\tbad name\n",
        )
        self.assertEqual(core.drift_exit_code([]), 0)
        self.assertEqual(core.drift_exit_code([d]), 1)
        # an enriched error Drift renders the SAME triple (extra fields never leak into the legacy line)
        e = ce.enrich_drift(d, recovery="aw rename ...", observed="o", required="r")
        self.assertEqual(
            core.render_agent_drift([e]),
            "some/loc.md\tcheck.name-nonconformant\tbad name\n",
        )
        self.assertEqual(core.drift_exit_code([e]), 1)

    def test_info_severity_is_advisory_non_failing(self):
        # An info-severity finding does NOT fail the gate; an error one does; a legacy empty-severity
        # 3-field Drift still fails (backward-compatible).
        info = ce.enrich_drift(core.Drift("p", "check.ipd-draft-ready-to-review", "x"))
        self.assertEqual(info.severity, "info")
        self.assertEqual(core.drift_exit_code([info]), 0)
        err = ce.enrich_drift(core.Drift("p", "check.name-nonconformant", "x"))
        self.assertEqual(core.drift_exit_code([err]), 1)
        legacy = core.Drift("p", "check.name-nonconformant", "x")
        self.assertEqual(core.drift_exit_code([legacy]), 1)


# --------------------------------------------------------------------------------------
# E-02: positive + adversarial fixture corpus (rule-id equality, per encoded invariant)
# --------------------------------------------------------------------------------------


class TestFixtureCorpus(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _plans(self):
        p = self.root / ".aw" / "records" / "plans" / "pending"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _specs(self):
        p = self.root / ".aw" / "records" / "specs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _backlog(self, status="open"):
        p = self.root / ".aw" / "records" / "backlog" / status
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---- positive: clean artifacts yield no FAILING findings ----

    def test_positive_clean_specs(self):
        s = self._specs()
        (s / "20260101-abc123-01-abc123-clean.spec.md").write_text(
            "# Spec: clean\n\n- Date: 2026-01-01\n- Status: reviewed\n- Id: abc123\n\n"
            "## Workflow history\n\n- 2026-01-01 created (aw specs): clean\n",
            encoding="utf-8",
        )
        drift = ce.check_type(self.root, "specs")
        self.assertEqual(core.drift_exit_code(drift), 0, [d.rule for d in drift])

    # ---- adversarial: each encoded rule fires with rule-id EQUALITY ----

    def test_adversarial_name_nonconformant(self):
        p = self._specs()
        # a post-cutover legacy-named spec must be id6-clustered (I-09)
        (p / "20260828-1200-01-legacy.spec.md").write_text(
            "# Spec: x\n\n- Date: 2026-08-28\n- Status: reviewed\n\n"
            "## Workflow history\n\n- 2026-08-28 created (aw specs): x\n",
            encoding="utf-8",
        )
        rules = {d.rule for d in ce.check_names(self.root, "specs")}
        self.assertEqual(rules, {"check.name-nonconformant"}, rules)

    def test_adversarial_setid_collision(self):
        # a spec declaring a setid that a plan already uses (cross-type reuse) -> I-09 family
        plans = self._plans()
        (plans / "20260101-shared-01-aaa111-p.ipd.md").write_text(
            "# IPD: p\n\n- Id: aaa111\n- Status: approved\n- Set: shared\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        specs = self._specs()
        (specs / "20260101-bbb222-01-bbb222-s.spec.md").write_text(
            "# Spec: s\n\n- Date: 2026-01-01\n- Status: reviewed\n- Id: bbb222\n- Set: shared\n\n"
            "## Workflow history\n\n- 2026-01-01 created (aw specs): s\n",
            encoding="utf-8",
        )
        rules = {d.rule for d in ce.check_collisions(self.root)}
        self.assertIn("check.setid-collision", rules)

    def test_adversarial_release_gate_blocking_close(self):
        # a release-blocking backlog item closed done with no preserved gate (I-07). This rule is
        # COMMIT-SCOPED (like check.status-untooled): the done+blocking item must be STAGED. So use a
        # git-backed fixture and stage the hand-edited close.
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        rel = self.root / ".aw" / "records" / "releases"
        rel.mkdir(parents=True, exist_ok=True)
        (rel / "20260101-rel01-01-rel001-next.release.md").write_text(
            "# Release: next\n\n- Id: rel001\n- Status: planned\n- Version: next\n- Summary: s\n",
            encoding="utf-8",
        )
        # start with the item OPEN and committed, then hand-edit it to done and STAGE (the bypass)
        openb = self._backlog("open")
        item = openb / "20260101-blk-01-blk001-item.backlog.md"
        item.write_text(
            "- Id: blk001\n- Status: open\n- Set: blk\n- Priority: high\n- Kind: chore\n"
            "- Summary: a blocking item\n- Blocks-Release: rel001\n\n"
            "## Workflow history\n- 2026-01-01 open (aw backlog): x\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)
        # hand-edit: flip to done and move into done/ (the exact hand-edit bypass), then stage
        done = self._backlog("done")
        item_done = done / "20260101-blk-01-blk001-item.backlog.md"
        item_done.write_text(
            "- Id: blk001\n- Status: done\n- Set: blk\n- Priority: high\n- Kind: chore\n"
            "- Summary: a blocking item\n- Blocks-Release: rel001\n\n"
            "## Workflow history\n- 2026-01-01 open (aw backlog): x\n",
            encoding="utf-8",
        )
        item.unlink()
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        rules = {d.rule for d in ce.check_release_gate_consistency(self.root)}
        self.assertIn("check.blocking-item-closed-without-gate", rules)

    def test_adversarial_ipd_dependency_malformed(self):
        plans = self._plans()
        (plans / "20260101-dep-01-dep001-p.ipd.md").write_text(
            "# IPD: p\n\n- Id: dep001\n- Status: approved\n- Set: dep\n"
            "- Item-Dependencies: not-a-valid-edge-format!!!\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        rules = {
            d.rule
            for d in ce.evaluate_ipd_dependencies(self.root, phase="pre-execution")
        }
        self.assertTrue(
            any(r.startswith("check.ipd-dependency-") for r in rules), rules
        )


# --------------------------------------------------------------------------------------
# E-02 (git-scoped): the commit-scoped untooled-status rule (I-03)
# --------------------------------------------------------------------------------------


class TestUntooledStatusFixture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)

    def _commit_all(self, msg):
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)

    def test_adversarial_hand_edited_status_untooled(self):
        f = self.plans / "20260101-unt-01-unt001-p.ipd.md"
        f.write_text(
            "# IPD: p\n\n- Id: unt001\n- Status: draft\n- Set: unt\n\n"
            "## Workflow history\n- 2026-01-01 draft (x): created.\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        self._commit_all("init")
        # hand-edit the status with NO tool-authored history line, then STAGE it
        f.write_text(
            "# IPD: p\n\n- Id: unt001\n- Status: approved\n- Set: unt\n\n"
            "## Workflow history\n- 2026-01-01 draft (x): created.\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        rules = {d.rule for d in ce.check_status_untooled(self.root)}
        self.assertIn("check.status-untooled", rules)


# --------------------------------------------------------------------------------------
# E-03: draft-readiness predicate + rule + lint author nudge
# --------------------------------------------------------------------------------------


_READY_DRAFT = """# IPD: A ready draft

- Date: 2026-08-28
- Kind: child
- Concern: A real, fully authored concern statement for review.
- Scope: A real scope statement describing what this plan changes.
- Scope-Paths: agent_workflows/foo.py, tests/
- Item-Dependencies: none
- Status: draft
- Set: rdy
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: rdy001

## Workflow history
- 2026-08-28 draft (tester): created.

## Goal

Deliver a real, fully authored goal statement.

## Detailed Implementation Checklist (TODO)

### Task group 1: real work

- [ ] E-01 Do a real observable action.
  - Depends on: none
  - Expected outcome: a real observable result.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: a real falsifiable evidence statement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
"""


class TestDraftReadiness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)

    def test_predicate_resolved_true_for_ready_draft(self):
        self.assertTrue(authoring.authoring_placeholders_resolved(_READY_DRAFT))

    def test_predicate_false_for_scaffold_placeholder(self):
        stub = _READY_DRAFT.replace(
            "- Concern: A real, fully authored concern statement for review.",
            "- Concern: TODO.",
        )
        self.assertFalse(authoring.authoring_placeholders_resolved(stub))

    def test_predicate_no_false_positive_on_prose_todo(self):
        # OQ-02: narrative "TODO" that is NOT a scaffold placeholder must not count.
        prose = _READY_DRAFT.replace(
            "- Concern: A real, fully authored concern statement for review.",
            "- Concern: We plan to clear the TODO items in the backlog next.",
        )
        self.assertTrue(authoring.authoring_placeholders_resolved(prose))

    def test_rule_nudges_ready_draft_with_recovery(self):
        (self.plans / "20260828-rdy-01-rdy001-ready.ipd.md").write_text(
            _READY_DRAFT, encoding="utf-8"
        )
        drift = ce.check_ipd_draft_ready(self.root)
        rules = {d.rule for d in drift}
        self.assertEqual(rules, {"check.ipd-draft-ready-to-review"}, rules)
        self.assertEqual(drift[0].recovery, "aw ipd set to-review rdy001")
        self.assertEqual(drift[0].severity, "info")  # advisory, non-failing

    def test_rule_silent_for_stub_draft(self):
        stub = _READY_DRAFT.replace(
            "- Scope: A real scope statement describing what this plan changes.",
            "- Scope: TODO.",
        )
        (self.plans / "20260828-stub-01-stub01-stub.ipd.md").write_text(
            stub, encoding="utf-8"
        )
        drift = ce.check_ipd_draft_ready(self.root)
        self.assertEqual(drift, [])

    def test_rule_never_auto_flips_status(self):
        f = self.plans / "20260828-rdy-01-rdy001-ready.ipd.md"
        f.write_text(_READY_DRAFT, encoding="utf-8")
        ce.check_ipd_draft_ready(self.root)
        # detect-and-nudge: the status is unchanged on disk
        self.assertIn("- Status: draft", f.read_text(encoding="utf-8"))

    def test_lint_author_phase_emits_nudge_advisory(self):
        f = self.plans / "20260828-rdy-01-rdy001-ready.ipd.md"
        f.write_text(_READY_DRAFT, encoding="utf-8")
        res = lint.lint_file(f, checkpoint="author")
        codes = {a.code for a in res.advisories}
        self.assertIn("check.ipd-draft-ready-to-review", codes)

    def test_lint_author_phase_silent_for_stub(self):
        stub = _READY_DRAFT.replace(
            "- Scope: A real scope statement describing what this plan changes.",
            "- Scope: TODO.",
        )
        f = self.plans / "20260828-stub-01-stub01-stub.ipd.md"
        f.write_text(stub, encoding="utf-8")
        res = lint.lint_file(f, checkpoint="author")
        codes = {a.code for a in res.advisories}
        self.assertNotIn("check.ipd-draft-ready-to-review", codes)


if __name__ == "__main__":
    unittest.main()
