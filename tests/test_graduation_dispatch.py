"""Tests for graduate Order 02 (`iuxtjy`): a SPEC selector resolves to the SPEC, on both hosts.

WHAT THIS FILE EXISTS TO FALSIFY. The defect this work fixes is SILENT, which is the only reason it
survived: `expand_selectors`' last resort is a FILENAME SUBSTRING match over plan filenames, and the
naming convention puts a spec's id6 in an adopting plan's slug, so naming a SPEC selected a PLAN ABOUT
that spec and started a run the operator did not ask for. Measured in this repository at execution
time, FIVE discoverable spec id6s resolved that way (`25kzda`, `77tr3o`, `7ckptx`, `c4gd2h`, `uonrjg`),
two of them to exactly one plan each and therefore with NO diagnostic at all.

THE ORDERING IS THE CONTENT, NOT THE BRANCH, which is why :class:`PrecedenceTests` is the heart of the
file. A spec branch appended AFTER the substring fallback is DEAD CODE for precisely the tokens that
are broken, so a test that only asserts "a spec selector refuses" passes against the broken order. Each
precedence case therefore builds a fixture in the shape the live tree actually has - a plan whose slug
CONTAINS the spec's id6, beside a spec declaring that id6 - and asserts the resolved artifact is the
SPEC.

FIXTURES, NOT THE LIVE SPEC TREE. The live discoverable-spec count moved 9 -> 10 -> 17 across this
plan's authoring, review and execution, so any assertion keyed to it would rot. The one live-corpus
assertion here is deliberate and different in kind: it asserts the PROPERTY that no discoverable spec
id6 resolves to a plan, which only the real corpus can demonstrate.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import agy_runipd
from agent_workflows import oc_runipd
from agent_workflows import runner_shared

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Both hosts, so every behavioral case below is asserted TWICE rather than on oc alone. The agy half
#: is not ceremony: the two `expand_selectors` bodies are independent copies, so a one-sided fix leaves
#: the other host resolving a spec to a plan and no oc-only test can notice.
HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))

PLAN = """# IPD: A test plan

- Date: 2026-09-08
- Kind: child
- Concern: Testing.
- Scope: Testing.
- Scope-Paths: x
- Item-Dependencies: none
- Status: {status}
- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Id: {id6}

## Workflow history
- 2026-09-08 created (test): Testing.
"""

SPEC = """# Spec: A test spec

- Date: 2026-09-08
- Status: {status}
{id_line}- Scope: Testing.

## Workflow history
- 2026-09-08 created (test): Testing.
"""


def _repo(root: Path) -> Path:
    (root / ".git").mkdir(parents=True, exist_ok=True)
    return root


def _plan(
    root: Path, id6: str, *, slug: str, setid: str = "tst", order: int = 1
) -> Path:
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"20260908-{setid}-{order:02d}-{id6}-{slug}.ipd.md"
    p.write_text(
        PLAN.format(status="approved", setid=setid, order=order, id6=id6),
        encoding="utf-8",
    )
    return p


def _spec(root: Path, *, id6: str | None, stem: str, status: str = "approved") -> Path:
    d = root / ".aw" / "records" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{stem}.spec.md"
    p.write_text(
        SPEC.format(status=status, id_line=f"- Id: {id6}\n" if id6 else ""),
        encoding="utf-8",
    )
    return p


def _manifest(host, root: Path) -> dict:
    return runner_shared.build_dynamic_manifest(root, host.discover_plans(root))


def _expand(host, root: Path, token: str):
    """Resolve one token, returning (expanded_or_None, refusal_message_or_None)."""
    try:
        return host.expand_selectors(_manifest(host, root), [token], root), None
    except runner_shared.DriverError as exc:
        return None, str(exc)


class PrecedenceTests(unittest.TestCase):
    """CASE 7 of the plan's eight: a spec id6 that ALSO appears in a plan filename resolves to the SPEC.

    This is the case the work would have shipped broken, and it is the one that fails against a spec
    branch placed after the substring fallback.
    """

    def test_a_spec_id6_inside_a_plan_slug_resolves_to_the_SPEC_on_both_hosts(self):
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                # The shape the LIVE tree has: a plan slugged `...adopt-spec-<specid>`.
                _plan(root, "aaa111", slug="adopt-spec-bbb222")
                spec = _spec(
                    root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec"
                )
                expanded, refusal = _expand(host, root, "bbb222")
                self.assertIsNone(
                    expanded,
                    "naming the SPEC resolved to a plan instead: the spec branch is sited AFTER the "
                    "filename-substring fallback, which makes it dead code for exactly the broken "
                    f"tokens (host {host_name}, got {expanded})",
                )
                assert refusal is not None
                self.assertIn(spec.name, refusal)
                self.assertNotIn(
                    "Ambiguous filename selector",
                    refusal,
                    "the substring fallback ran first",
                )

    def test_the_refusal_NAMES_the_plan_the_old_fallback_would_have_run(self):
        """The shadowed plan is evidence, not decoration: it is why the precedence matters."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="adopt-spec-bbb222")
                _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
                _, refusal = _expand(host, root, "bbb222")
                assert refusal is not None
                self.assertIn("aaa111", refusal)
                self.assertIn("FILENAME SUBSTRING", refusal)

    def test_a_plan_id6_still_wins_and_no_existing_resolution_moved(self):
        """LOAD-BEARING NEGATIVE. The exact-plan branch precedes the spec branch, so a token that is
        BOTH a plan id6 and a spec id6 must still resolve to the plan; otherwise this change would
        silently steal resolutions from the branch operators use most."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "ccc333", slug="a-plan")
                _spec(root, id6="ccc333", stem="20260908-ccc333-01-ccc333-a-test-spec")
                expanded, refusal = _expand(host, root, "ccc333")
                self.assertEqual(expanded, ["ccc333"], refusal)

    def test_a_Set_name_still_wins_over_a_spec_id6(self):
        """The Set branch also precedes the spec branch. Verified against the live tree that no
        discoverable spec id6 is a Set name or prefix, so this asserts the ordering rather than a
        behavior change."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "ddd444", slug="a-plan", setid="eee555")
                _spec(root, id6="eee555", stem="20260908-eee555-01-eee555-a-test-spec")
                expanded, refusal = _expand(host, root, "eee555")
                self.assertEqual(expanded, ["ddd444"], refusal)


class RefusalContentTests(unittest.TestCase):
    """CASES 1, 2 and 3: an approved spec, a spec with no `- Id:`, and a forbidden-status spec."""

    def test_an_approved_spec_resolves_to_the_spec_and_says_why_it_cannot_be_queued(
        self,
    ):
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="a-plan")
                spec = _spec(
                    root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec"
                )
                _, refusal = _expand(host, root, "bbb222")
                assert refusal is not None
                self.assertIn("is a spec", refusal)
                self.assertIn(spec.name, refusal)
                self.assertIn("plan-shaped", refusal)
                self.assertIn(
                    "z7nbn1",
                    refusal,
                    "the refusal must name the spec that OWNS per-type dispatch, so a reader knows "
                    "this is an unbuilt capability rather than a broken selector",
                )

    def test_it_does_NOT_point_at_action_plan_which_is_itself_refused(self):
        """Pointing at `--action plan` would send the operator to a SECOND refusal, since that action
        is registered and excluded from `ACTION_IMPLEMENTED`."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="a-plan")
                _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
                _, refusal = _expand(host, root, "bbb222")
                assert refusal is not None
                self.assertNotIn("--action plan", refusal)

    def test_a_spec_with_no_Id_refuses_with_an_explanation_and_the_conversion_verb(
        self,
    ):
        """The MAJORITY case, and its silence looks like a bug: the shared selector layer reaches such
        a file by stem while `discover_specs` deliberately skips it."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="a-plan")
                _spec(root, id6=None, stem="20260706-0000-01-a-legacy-spec")
                _, refusal = _expand(host, root, "20260706-0000-01-a-legacy-spec")
                assert refusal is not None
                self.assertIn("declares no `- Id:`", refusal)
                self.assertIn("deliberate, not a bug", refusal)
                self.assertIn("aw rename specs", refusal)
                self.assertIn("--to-id6", refusal)

    def test_a_spec_that_HAS_an_Id_reached_by_stem_does_not_get_the_id_less_note(self):
        """LOAD-BEARING NEGATIVE: the explanation must key on the ACTUAL absence of `- Id:`, not on
        the selector spelling, or it would assert something false about a conformant spec."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="a-plan")
                _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
                _, refusal = _expand(
                    host, root, "20260908-bbb222-01-bbb222-a-test-spec"
                )
                assert refusal is not None
                self.assertNotIn("declares no `- Id:`", refusal)

    def test_a_terminal_status_spec_still_resolves_to_the_spec_not_to_a_plan(self):
        """The precedence fix is about TYPE, not about status: an `implemented` spec must not fall
        through to the substring fallback either."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="adopt-spec-bbb222")
                spec = _spec(
                    root,
                    id6="bbb222",
                    stem="20260908-bbb222-01-bbb222-a-test-spec",
                    status="implemented",
                )
                _, refusal = _expand(host, root, "bbb222")
                assert refusal is not None
                self.assertIn(spec.name, refusal)


class BacklogSelectorTests(unittest.TestCase):
    """CASE 4: the backlog half is DEFERRED (OQ-01), so a backlog selector must refuse INFORMATIVELY
    and must never silently no-op or imply success."""

    def test_a_backlog_selector_refuses_and_names_the_artifact_it_found(self):
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="a-plan")
                d = root / ".aw" / "records" / "backlog" / "open"
                d.mkdir(parents=True, exist_ok=True)
                (d / "20260908-tst-01-fff666-an-item.backlog.md").write_text(
                    "# Backlog: An item\n\n- Status: open\n- Id: fff666\n",
                    encoding="utf-8",
                )
                expanded, refusal = _expand(host, root, "fff666")
                self.assertIsNone(
                    expanded,
                    "a backlog selector must not silently resolve to anything while the backlog half "
                    "is deferred",
                )
                assert refusal is not None
                self.assertIn("backlog item", refusal)
                self.assertIn("not an IPD plan", refusal)


class PreGraduationViewTests(unittest.TestCase):
    """CASE 6 (and E-04): child 01's advisory view is REACHED, it INFORMS, and it duplicates nothing."""

    def test_the_cluster_report_is_emitted_and_names_the_existing_artifacts(self):
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                # Two plans already graduated from the spec: the cluster the view must surface.
                for n, id6 in enumerate(("aaa111", "ggg777"), start=1):
                    p = _plan(root, id6, slug="a-plan", setid="tst", order=n)
                    p.write_text(
                        p.read_text(encoding="utf-8").replace(
                            "- Item-Dependencies: none",
                            "- Item-Dependencies: none\n- From-Spec: bbb222",
                        ),
                        encoding="utf-8",
                    )
                _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
                _, refusal = _expand(host, root, "bbb222")
                assert refusal is not None
                self.assertIn("PRE-GRADUATION VIEW", refusal)
                self.assertIn("aaa111", refusal)
                self.assertIn("ggg777", refusal)

    def test_the_report_INFORMS_rather_than_refusing_on_the_cluster(self):
        """The cluster must never be the CAUSE of a refusal. Proven two ways: several artifacts for
        one source is legitimate decomposition, so the message says so; and a source with ZERO
        artifacts produces the SAME kind of refusal (caused by the plan-shaped queue), not a different
        outcome."""
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="a-plan")
                _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
                _, refusal = _expand(host, root, "bbb222")
                assert refusal is not None
                self.assertIn("nothing yet links to bbb222", refusal)
                self.assertIn("advisory", refusal)
                self.assertIn(
                    "nothing LINKED to it",
                    refusal,
                    "a zero result must be QUALIFIED: work carrying no `- From-*` bullet is invisible "
                    "to the view, and a silence mistaken for 'nothing exists' causes the very "
                    "duplication the view exists to prevent",
                )

    def test_it_applies_NO_count_greater_than_one_judgement(self):
        """MUTATION-RESISTANT ASSERTION: a cluster of several must read as LEGITIMATE, so a later
        editor who turns the view into a uniqueness rule fails here."""
        with TemporaryDirectory() as td:
            root = _repo(Path(td))
            for n, id6 in enumerate(("aaa111", "ggg777", "hhh888"), start=1):
                p = _plan(root, id6, slug="a-plan", setid="tst", order=n)
                p.write_text(
                    p.read_text(encoding="utf-8").replace(
                        "- Item-Dependencies: none",
                        "- Item-Dependencies: none\n- From-Spec: bbb222",
                    ),
                    encoding="utf-8",
                )
            line = runner_shared.summarize_graduation_cluster(root, "bbb222")
            self.assertIn("LEGITIMATE decomposition, not a defect", line)
            self.assertIn("refuses nothing", line)

    def test_no_cluster_logic_is_duplicated_in_the_runner(self):
        """It must CALL child 01's view. The runner must hold no `- From-*` parse and no terminal-status
        set of its own, or the two would drift and disagree about what a source became."""
        src = (REPO_ROOT / "agent_workflows" / "runner_shared.py").read_text(
            encoding="utf-8"
        )
        fn = src.split("def summarize_graduation_cluster", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("graduation_cluster(", fn)
        for forbidden in (
            "From-Spec:",
            "From-Backlog:",
            "_ITEM_FROM_SPEC_RE",
            "_iter_plan_ipds",
        ):
            self.assertNotIn(
                forbidden,
                fn,
                f"the runner re-implements {forbidden} instead of calling child 01's view",
            )

    def test_a_failing_advisory_never_becomes_a_failing_run(self):
        """An advisory that raised would convert a helpful line into an outage. Asserted on a
        directory that is not a repository at all."""
        with TemporaryDirectory() as td:
            self.assertEqual(
                runner_shared.summarize_graduation_cluster(Path(td) / "nope", "bbb222"),
                "",
            )
        self.assertEqual(runner_shared.summarize_graduation_cluster(None, "bbb222"), "")


class NoDurableStateTests(unittest.TestCase):
    """CASES 5 and 6's filesystem half: a refusal leaves NOTHING under the runs root.

    Asserted on the FILESYSTEM rather than on an exit code, because the existing fail-closed gates are
    sited before the run directory exists specifically so a refusal leaves nothing to reconcile, and a
    new gate that created a run directory and then refused would break that property silently.
    """

    def test_a_spec_selector_refusal_creates_no_run_directory(self):
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="adopt-spec-bbb222")
                _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
                runs = runner_shared.state_root(root)
                before = set(p.name for p in runs.iterdir()) if runs.exists() else set()
                _, refusal = _expand(host, root, "bbb222")
                self.assertIsNotNone(refusal)
                after = set(p.name for p in runs.iterdir()) if runs.exists() else set()
                self.assertEqual(before, after, "the refusal created durable run state")

    def test_an_unimplemented_action_still_fails_closed_and_starts_no_run(self):
        """CASE 5. This work does NOT widen `ACTION_IMPLEMENTED`: the legality derivation still cannot
        return `plan` (`action_for` returns only execute/review/orchestrate), so widening it alone
        would convert a clear 'not implemented' refusal into an incoherent one naming the wrong
        action. Asserted here so a later editor cannot widen it without noticing."""
        self.assertNotIn("plan", runner_shared.ACTION_IMPLEMENTED)
        self.assertNotIn("execute", runner_shared.ACTION_IMPLEMENTED)
        for host_name, host in HOSTS:
            with self.subTest(host=host_name):
                with self.assertRaises(runner_shared.DriverError) as ctx:
                    host.enforce_requested_action(
                        "plan", [("bbb222", "approved", "execute")]
                    )
                self.assertIn("not implemented", str(ctx.exception))
                self.assertIn("No run was started", str(ctx.exception))


class QueueSeamTests(unittest.TestCase):
    """CASE 8: a spec id6 must never reach the queue loop's BARE `manifest["plans"][id6]` subscript.

    That subscript is the measured failure mode of a discovery-only change: it raises `KeyError`
    rather than refusing. The property asserted is that the outcome is a NAMED REFUSAL and not a
    traceback.
    """

    def test_a_spec_selector_yields_a_named_refusal_and_never_a_KeyError(self):
        for host_name, host in HOSTS:
            with self.subTest(host=host_name), TemporaryDirectory() as td:
                root = _repo(Path(td))
                _plan(root, "aaa111", slug="adopt-spec-bbb222")
                _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
                manifest = _manifest(host, root)
                try:
                    host.expand_selectors(manifest, ["bbb222"], root)
                except runner_shared.DriverError as exc:
                    self.assertIn("is a spec", str(exc))
                except KeyError as exc:  # pragma: no cover - the defect this guards
                    self.fail(
                        f"spec id6 reached the bare queue subscript: KeyError {exc}"
                    )
                else:  # pragma: no cover
                    self.fail("a spec selector resolved into the queue")

    def test_the_bare_subscript_is_still_there_so_this_guard_is_still_needed(self):
        """DERIVE THE HAZARD, DO NOT ASSUME IT. If a later plan makes the queue builder tolerant of a
        non-plan id6, this test tells its author that the guard above changed meaning rather than
        letting it pass vacuously."""
        src = (REPO_ROOT / "agent_workflows" / "runner_shared.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('plan = manifest["plans"][id6]', src)


class SharedImplementationTests(unittest.TestCase):
    """E-05: ONE implementation, sited in `runner_shared`, reached identically by both hosts."""

    def test_both_hosts_bind_the_same_shared_objects(self):
        self.assertIs(
            oc_runipd.runner_shared.match_spec_selector,
            runner_shared.match_spec_selector,
        )
        self.assertIs(
            agy_runipd.runner_shared.match_spec_selector,
            runner_shared.match_spec_selector,
        )
        self.assertEqual(
            runner_shared.match_spec_selector.__module__,
            "agent_workflows.runner_shared",
        )

    def test_both_hosts_refuse_the_same_spec_with_only_the_host_command_differing(self):
        """The two refusals must differ ONLY in the host's own review command, or the hosts disagree
        about what a spec selector means."""
        with TemporaryDirectory() as td:
            root = _repo(Path(td))
            _plan(root, "aaa111", slug="adopt-spec-bbb222")
            _spec(root, id6="bbb222", stem="20260908-bbb222-01-bbb222-a-test-spec")
            _, oc_msg = _expand(oc_runipd, root, "bbb222")
            _, agy_msg = _expand(agy_runipd, root, "bbb222")
            assert oc_msg is not None and agy_msg is not None
            self.assertNotEqual(oc_msg, agy_msg, "the host command should differ")
            self.assertEqual(
                oc_msg.replace(runner_shared.OC_HOST_LABELS.review_command, "<review>"),
                agy_msg.replace(
                    runner_shared.AGY_HOST_LABELS.review_command, "<review>"
                ),
            )


class NoSecondEnumerationTests(unittest.TestCase):
    """The enumeration is `discover_specs` and nothing else, so the review sweep and selector
    expansion cannot disagree about which specs exist."""

    def test_the_spec_branch_calls_discover_specs(self):
        src = (REPO_ROOT / "agent_workflows" / "runner_shared.py").read_text(
            encoding="utf-8"
        )
        fn = src.split("def match_spec_selector", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("discover_specs(", fn)

    def test_exactly_one_spec_enumeration_survives(self):
        src = (REPO_ROOT / "agent_workflows" / "runner_shared.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(src.count("def discover_specs"), 1)


class LiveCorpusPropertyTests(unittest.TestCase):
    """ONE live assertion, deliberately different in kind from the fixtures above.

    The property "no discoverable spec id6 resolves to a plan" can only be shown on the REAL corpus,
    because the collision arises from the repository's own naming convention. Counts are DERIVED: the
    discoverable-spec count moved 9 -> 10 -> 17 across this plan's authoring, review and execution.
    """

    def test_no_discoverable_spec_id6_resolves_to_a_plan_on_either_host(self):
        specs = runner_shared.discover_specs(REPO_ROOT)
        self.assertGreater(
            len(specs), 0, "no specs discoverable; the assertion would be vacuous"
        )
        for host_name, host in HOSTS:
            manifest = _manifest(host, REPO_ROOT)
            for id6 in sorted(specs):
                with self.subTest(host=host_name, spec=id6):
                    try:
                        resolved = host.expand_selectors(manifest, [id6], REPO_ROOT)
                    except runner_shared.DriverError as exc:
                        self.assertIn(f"'{id6}' is a spec", str(exc))
                    else:  # pragma: no cover - the defect this fixes
                        self.fail(
                            f"spec {id6} resolved to plan(s) {resolved} on host {host_name}: the "
                            "filename-substring fallback is still winning"
                        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
