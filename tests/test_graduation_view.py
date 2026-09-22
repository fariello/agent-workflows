"""Tests for graduate Order 01 (`jxxec8`): the READ-ONLY pre-graduation view.

WHAT THIS FILE EXISTS TO FALSIFY, because the view's whole value is that it can be TRUSTED before
someone authors a plan, and three of the ways it could be wrong are silent:

1. IT COULD FLAG CORRECT WORK. 33 sources in this repository carry more than one artifact and the
   largest cluster (ten) is deliberate decomposition, so a `count > 1` rule would report legitimate
   work as a defect and teach every reader to ignore the view. That property can only be shown on
   the REAL corpus, because a fixture only proves the code does what its author expected, so
   :class:`LiveCorpusTests` asserts it there.
2. IT COULD BE SILENT ABOUT SPECS. A spec is an "equally valid gate carrier", and the plans-only
   version of this defect was ALREADY FIXED ONCE in `find_from_backlog_artifacts` ("the HANDOFF
   route previously scanned plan IPDs ONLY, so a spec-first graduation ... was invisible"). A
   plans-only reverse index passes every plans-only test BY CONSTRUCTION, so the spec carrier is
   asserted both live (`6m4kow` must surface under `25kzda`) and as a spec-ONLY fixture.
3. IT COULD DROP THE LANDED WORK. Re-doing executed work is the costly case the maintainer named, so
   a view reading `pending/` only would be worst exactly where it matters most. Hence the
   all-terminal fixture.

COUNTS ARE DERIVED, NEVER PINNED, and that is a measured requirement rather than caution: the
source-linked corpus went 71 -> 125 -> 166 -> 243 bullets across this work's own authoring, review
and execution. Every live assertion below therefore asserts a PROPERTY (a known member is PRESENT, no
defect is flagged, the count is at least the members enumerated) and computes the total.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import check_engine
from agent_workflows import cli

REPO_ROOT = Path(__file__).resolve().parents[1]


PLAN = """# IPD: {title}

- Date: 2026-09-08
- Kind: child
- Concern: Testing.
- Scope: Testing.
- Scope-Paths: x
- Item-Dependencies: none
{links}- Status: {status}
- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-08 created (test): Testing.
"""

SPEC = """# Spec: {title}

- Date: 2026-09-08
- Status: {status}
- Id: {id6}
{links}- Scope: Testing.

## Workflow history
- 2026-09-08 created (test): Testing.
"""


def _links(*, backlog: str | None = None, spec: str | None = None) -> str:
    out = ""
    if backlog:
        out += f"- From-Backlog: {backlog}\n"
    if spec:
        out += f"- From-Spec: {spec}\n"
    return out


def _plan(
    root: Path,
    id6: str,
    *,
    status: str = "to-review",
    setid: str = "tst",
    order: int = 1,
    backlog: str | None = None,
    spec: str | None = None,
    disposition: str = "pending",
) -> Path:
    d = root / ".aw" / "records" / "plans" / disposition
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260908-{setid}-{order:02d}-{id6}-a-test-plan.ipd.md"
    p.write_text(
        PLAN.format(
            title="A test plan",
            links=_links(backlog=backlog, spec=spec),
            status=status,
            setid=setid,
            order=order,
            id6=id6,
        ),
        encoding="utf-8",
    )
    return p


def _spec(
    root: Path,
    id6: str,
    *,
    status: str = "approved",
    backlog: str | None = None,
    spec: str | None = None,
) -> Path:
    d = root / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260908-{id6}-01-{id6}-a-test-spec.spec.md"
    p.write_text(
        SPEC.format(
            title="A test spec",
            links=_links(backlog=backlog, spec=spec),
            status=status,
            id6=id6,
        ),
        encoding="utf-8",
    )
    return p


class ReverseIndexFixtureTests(unittest.TestCase):
    """E-01/E-04 fixture cases: every behavioral shape, on a corpus whose contents are known."""

    def test_a_source_with_no_artifacts_reports_an_empty_cluster(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            _plan(root, "aaaaaa", backlog="bbbbbb")
            cluster = check_engine.graduation_cluster(root, "zzzzzz")
            self.assertEqual(cluster.artifact_count, 0)
            self.assertEqual(cluster.artifacts, ())
            self.assertEqual(cluster.setids, ())

    def test_a_source_with_one_artifact_reports_it_with_type_status_and_set(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            _plan(root, "aaaaaa", backlog="bbbbbb", status="approved", setid="solo")
            cluster = check_engine.graduation_cluster(root, "bbbbbb")
            self.assertEqual(cluster.artifact_count, 1)
            only = cluster.artifacts[0]
            self.assertEqual(only.artifact_type, "plan")
            self.assertEqual(only.id6, "aaaaaa")
            self.assertEqual(only.status, "approved")
            self.assertEqual(only.setid, "solo")
            self.assertEqual(cluster.setids, ("solo",))

    def test_several_artifacts_in_ONE_set_are_reported_as_one_set(self):
        """LEGITIMATE DECOMPOSITION: one Set, several Orders. Must report, must not flag."""
        with TemporaryDirectory() as d:
            root = Path(d)
            for n, id6 in enumerate(("aaaaaa", "bbbbbb", "cccccc"), start=1):
                _plan(root, id6, backlog="ssssss", setid="onset", order=n)
            cluster = check_engine.graduation_cluster(root, "ssssss")
            self.assertEqual(cluster.artifact_count, 3)
            self.assertEqual(
                cluster.setids,
                ("onset",),
                "three children of ONE Set must read as one Set, which is what makes "
                "decomposition visible to a human",
            )

    def test_artifacts_across_DIFFERENT_sets_expose_the_partly_visible_case(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            _plan(root, "aaaaaa", backlog="ssssss", setid="alpha")
            _plan(root, "bbbbbb", backlog="ssssss", setid="beta")
            cluster = check_engine.graduation_cluster(root, "ssssss")
            self.assertEqual(cluster.artifact_count, 2)
            self.assertEqual(cluster.setids, ("alpha", "beta"))

    def test_an_all_terminal_cluster_is_visible_and_flagged_as_landed(self):
        """THE COSTLY CASE. Every member already executed; a view reading `pending/` would be empty
        here, which is precisely where re-doing work is most expensive."""
        with TemporaryDirectory() as d:
            root = Path(d)
            _plan(
                root,
                "aaaaaa",
                backlog="ssssss",
                status="executed",
                disposition="executed",
            )
            _plan(
                root,
                "bbbbbb",
                backlog="ssssss",
                status="executed",
                disposition="executed",
                order=2,
            )
            cluster = check_engine.graduation_cluster(root, "ssssss")
            self.assertEqual(cluster.artifact_count, 2)
            self.assertEqual(
                len(cluster.terminal_artifacts),
                2,
                "both members are `executed`, so both must be reported as already landed",
            )

    def test_a_SPEC_ONLY_source_is_still_reported(self):
        """The spec-first graduation shape. A plans-only index reports NOTHING here and every
        plans-only test still passes, which is why this case exists."""
        with TemporaryDirectory() as d:
            root = Path(d)
            _spec(root, "specid", backlog="ssssss")
            cluster = check_engine.graduation_cluster(root, "ssssss")
            self.assertEqual(
                cluster.artifact_count,
                1,
                "a spec carrying the source link must be reported even with no plan at all",
            )
            self.assertEqual(cluster.artifacts[0].artifact_type, "spec")
            self.assertEqual(cluster.artifacts[0].id6, "specid")

    def test_a_dual_link_artifact_appears_under_BOTH_of_its_sources(self):
        """Six real plans carry both link kinds, so a first-match read would drop one edge each."""
        with TemporaryDirectory() as d:
            root = Path(d)
            _plan(root, "aaaaaa", backlog="bbbbbb", spec="cccccc")
            by_backlog = check_engine.graduation_cluster(root, "bbbbbb")
            by_spec = check_engine.graduation_cluster(root, "cccccc")
            self.assertEqual([a.id6 for a in by_backlog.artifacts], ["aaaaaa"])
            self.assertEqual([a.id6 for a in by_spec.artifacts], ["aaaaaa"])

    def test_the_two_link_kinds_are_not_conflated(self):
        """A `From-Spec: x` and a `From-Backlog: x` are DIFFERENT sources; `--kind` must separate
        them even though the unioning default is what an operator typing an id6 wants."""
        with TemporaryDirectory() as d:
            root = Path(d)
            _plan(root, "aaaaaa", backlog="ssssss")
            _plan(root, "bbbbbb", spec="ssssss", order=2)
            self.assertEqual(
                [
                    a.id6
                    for a in check_engine.graduation_cluster(
                        root, "ssssss", source_kind="backlog"
                    ).artifacts
                ],
                ["aaaaaa"],
            )
            self.assertEqual(
                [
                    a.id6
                    for a in check_engine.graduation_cluster(
                        root, "ssssss", source_kind="spec"
                    ).artifacts
                ],
                ["bbbbbb"],
            )
            self.assertEqual(
                check_engine.graduation_cluster(root, "ssssss").artifact_count,
                2,
                "the default unions both kinds, because an id6 is unique across the inventory",
            )


class LiveCorpusTests(unittest.TestCase):
    """E-04: the properties only the REAL corpus can demonstrate.

    NOT ONE COUNT IS PINNED here. Each assertion names a member that must be PRESENT and derives the
    total, because the corpus provably grows during work of this kind.
    """

    @classmethod
    def setUpClass(cls):
        cls.index = check_engine.build_graduation_reverse_index(REPO_ROOT)

    def test_the_largest_real_cluster_is_reported_and_flags_no_defect(self):
        """THE ANTI-OVER-REACH GUARD, driven through the REAL surface rather than the helper.

        Asserting on the helper alone would be satisfiable by a view that reports the cluster
        cleanly in Python and then flags it at the CLI, which is exactly the uniqueness rule this
        plan forbids. So this runs the command and asserts the EMITTED record carries no
        diagnostic and exits 0, on the largest real (and CORRECT) cluster in the repository.
        """
        cluster = check_engine.graduation_cluster(REPO_ROOT, "25kzda", index=self.index)
        derived = len(cluster.artifacts)
        self.assertGreater(
            derived,
            1,
            "spec 25kzda is the repository's largest source cluster; if this is <=1 the index is "
            "not reading the corpus (count DERIVED, never pinned)",
        )
        self.assertEqual(cluster.artifact_count, derived)

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["graduation", "25kzda", "--dir", str(REPO_ROOT), "--json"])
        record = json.loads(buf.getvalue())
        self.assertEqual(
            rc,
            0,
            "a legitimate multi-artifact cluster must not make the view exit nonzero",
        )
        self.assertEqual(
            record["diagnostics"],
            [],
            f"the view flagged the {derived}-artifact 25kzda cluster as a finding. That cluster is "
            "DELIBERATE decomposition (spec 25kzda's own graduation text says a run 'may produce "
            "more than one IPD'), so flagging it reports correct work as a defect and teaches every "
            "reader to ignore the view",
        )
        self.assertEqual(record["status"], "clean")
        self.assertEqual(
            len(record["data"]["artifacts"]),
            derived,
            "the cluster must be REPORTED in full; not flagging it is only half the requirement",
        )
        # And the ADVISORY posture is stated as data rather than implied.
        self.assertEqual(len(check_engine.GRADUATION_VIEW_LIMITS), 3)

    def test_the_spec_carrier_surfaces_in_the_live_cluster(self):
        """The assertion a plans-only index fails and every plans-only test passes."""
        kz = check_engine.graduation_cluster(REPO_ROOT, "25kzda", index=self.index)
        self.assertIn(
            "6m4kow",
            [a.id6 for a in kz.artifacts if a.artifact_type == "spec"],
            "spec 6m4kow carries `- From-Backlog: 25kzda`-side provenance for this source and MUST "
            "appear; a plans-only reverse index omits it and thereby hides the already-addressed "
            "case the view exists to show",
        )
        kx = check_engine.graduation_cluster(REPO_ROOT, "kxkc04", index=self.index)
        self.assertIn(
            "77tr3o",
            [a.id6 for a in kx.artifacts if a.artifact_type == "spec"],
            "spec 77tr3o must appear alongside the orchretire plans for backlog kxkc04",
        )
        self.assertGreater(
            len([a for a in kx.artifacts if a.artifact_type == "plan"]),
            1,
            "the kxkc04 cluster is plans PLUS a spec; the plan side must not have vanished",
        )

    def test_terminal_directories_are_included_not_filtered(self):
        cluster = check_engine.graduation_cluster(REPO_ROOT, "25kzda", index=self.index)
        self.assertTrue(
            [a for a in cluster.artifacts if "/executed/" in a.path],
            "most members of a mature cluster are executed; a view that read pending/ only would "
            "miss the costly already-landed case entirely",
        )
        self.assertTrue(cluster.terminal_artifacts)

    def test_a_real_dual_link_plan_appears_under_both_of_its_sources(self):
        """Derived, not pinned: find a dual-link artifact in the live index and prove both edges."""
        backlog_paths = {
            a.path for k, v in self.index.items() if k[0] == "backlog" for a in v
        }
        spec_paths = {
            a.path for k, v in self.index.items() if k[0] == "spec" for a in v
        }
        dual = sorted(backlog_paths & spec_paths)
        self.assertTrue(
            dual,
            "the corpus contains artifacts carrying BOTH a From-Backlog and a From-Spec bullet; if "
            "none is found under both kinds the index read only the first match",
        )

    def test_the_live_index_covers_both_artifact_types(self):
        types = {a.artifact_type for v in self.index.values() for a in v}
        self.assertEqual(types, set(check_engine.GRADUATION_ARTIFACT_TYPES))


class OutputHonestyTests(unittest.TestCase):
    """E-03: the limits and the coverage boundary must be IN THE OUTPUT, not only in a plan."""

    def _run(self, *argv) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(list(argv))
        return rc, buf.getvalue()

    def test_the_human_output_states_all_three_cases_with_its_verdict_for_each(self):
        rc, out = self._run(
            "graduation", "25kzda", "--dir", str(REPO_ROOT), "--no-color"
        )
        self.assertEqual(rc, 0)
        self.assertIn("legitimate decomposition", out)
        self.assertIn("VISIBLE", out)
        self.assertIn("accidental duplication", out)
        self.assertIn("PARTLY VISIBLE", out)
        self.assertIn("already implemented", out)
        self.assertIn("NOT DETECTABLE", out)
        self.assertIn(
            "f1sw71",
            out,
            "the undetectable case must name the carrier of the gap, so a reader who knows WHY does "
            "not assume the view failed",
        )

    def test_the_human_output_qualifies_what_its_silence_proves(self):
        rc, out = self._run(
            "graduation", "zzzzzz", "--dir", str(REPO_ROOT), "--no-color"
        )
        self.assertEqual(
            rc, 0, "a source with nothing linked is a normal answer, not an error"
        )
        self.assertIn("nothing yet", out)
        self.assertIn("PLANS and SPECS", out)
        self.assertIn(
            "never 'nothing exists'",
            out,
            "an unqualified zero answer is the one output that can cause the duplication this view "
            "prevents, so the coverage boundary must appear beside it",
        )

    def test_the_output_does_not_claim_to_detect_duplication(self):
        _rc, out = self._run(
            "graduation", "25kzda", "--dir", str(REPO_ROOT), "--no-color"
        )
        self.assertIn("it does not decide", out)
        self.assertNotIn("duplicate plan detected", out)
        self.assertNotIn("DUPLICATION DETECTED", out)

    def test_the_json_record_carries_the_cluster_and_the_limits(self):
        rc, out = self._run("graduation", "25kzda", "--dir", str(REPO_ROOT), "--json")
        self.assertEqual(rc, 0)
        data = json.loads(out)["data"]
        self.assertEqual(data["source"], "25kzda")
        self.assertGreater(len(data["artifacts"]), 1)
        self.assertEqual(
            [limit["case"] for limit in data["limits"]],
            [case for case, _v, _w in check_engine.GRADUATION_VIEW_LIMITS],
            "a machine consumer must receive the honesty too, not only a human reader",
        )
        self.assertIn("never 'nothing exists'", data["coverage"])
        self.assertTrue(data["advisory"])

    def test_the_COMPACT_agent_record_still_states_every_limit(self):
        """The compact `--agent` record DROPS `data` by design, so a limits statement living only
        there would leave an agent consumer with the cluster and no statement of its meaning. The
        verdicts therefore travel as EVIDENCE, which compaction preserves."""
        rc, out = self._run("graduation", "25kzda", "--dir", str(REPO_ROOT), "--agent")
        self.assertEqual(rc, 0)
        rec = json.loads(out.strip().splitlines()[-1])
        self.assertNotIn(
            "data",
            rec,
            "the compact agent record is expected to omit `data` (schema contract)",
        )
        evidence = rec["evidence"]
        for case, verdict, _why in check_engine.GRADUATION_VIEW_LIMITS:
            self.assertIn(
                f"limit:{case}:{verdict}",
                evidence,
                f"the compact agent record dropped the {case!r} verdict",
            )
        self.assertTrue(
            any("never 'nothing exists'" in e for e in evidence),
            "the coverage boundary must reach the agent surface too",
        )
        self.assertEqual(rec["findings"], 0, "the view reports no defect, by design")

    def test_the_surface_is_a_declared_read_leaf_with_no_findings_exit(self):
        from agent_workflows.command_surface import (
            discover_parser_leaves,
            get_declaration,
        )

        self.assertIn("graduation", discover_parser_leaves(cli._build_parser()))
        decl = get_declaration("graduation")
        self.assertIsNotNone(decl)
        assert decl is not None
        self.assertEqual(decl.command_class, "read")
        self.assertEqual(decl.mutation_gate, "none")
        self.assertNotIn(
            1,
            decl.exit_contract,
            "exit 1 means `findings`; this view produces none by design, so an exit contract "
            "including 1 would assert a judgement it deliberately never makes",
        )


class NoUniquenessRuleTests(unittest.TestCase):
    """E-02's single most important prohibition, asserted structurally rather than by inspection."""

    def test_no_check_rule_was_registered_for_this_view(self):
        offenders = [
            rule
            for rule in check_engine.RULE_REGISTRY
            if "graduation" in rule or "duplicate" in rule
        ]
        self.assertEqual(
            offenders,
            [],
            "OQ-01 resolved to a READ SURFACE, not a `check` rule: a rule would fire on every "
            "legitimate multi-artifact cluster on every `aw check` run",
        )

    def test_the_added_code_contains_no_count_comparison(self):
        """A grep, in a test, so a later edit that adds the prohibited rule goes red."""
        import re

        engine_src = (REPO_ROOT / "agent_workflows" / "check_engine.py").read_text(
            encoding="utf-8"
        )
        start = engine_src.index("def build_graduation_reverse_index")
        end = engine_src.index("class CloseVerdict")
        region = engine_src[start:end]
        # Strip comments and docstrings-ish prose lines: the PROHIBITION is discussed in prose
        # deliberately, and asserting on prose would be a change-detector.
        code_only = "\n".join(
            line for line in region.splitlines() if not line.strip().startswith("#")
        )
        self.assertIsNone(
            re.search(r"len\([^)]*\)\s*>\s*1", code_only),
            "a `count > 1` comparison in the reverse index would be the uniqueness rule this plan "
            "forbids: 33 real sources have more than one artifact and the largest cluster is correct",
        )


if __name__ == "__main__":
    unittest.main()
