"""A run may not act on a RETIRED plan, whichever selector names it, on EITHER host.

WHY THIS FILE EXISTS. Backlog `7ap6ku`, measured in production on 2026-09-20: `expand_selectors`
built its admission test as a closure INSIDE the `all` branch, so `aw oc run all` filtered terminal
plans correctly while every other branch (Set id, Set prefix, bare id6, filename, file path) took its
candidates VERBATIM. Run `run-20260920T041130Z-2037265` therefore queued four `setidhard` plans, three
of them RETIRED on 2026-09-10, each with `initial_status: superseded` and a live `execute`/
`orchestrate` action. Across the tree the asymmetry exposed 587 terminal plans in 271 Sets, 51 of them
orchestrators.

WHAT THESE TESTS PIN, stated as properties rather than as the current implementation's shape:

 1. The admission predicate itself, including its FAIL-CLOSED cases (absent entry, absent status,
    unknown status, and a status/directory disagreement). That last one matters most: a plan whose
    bullet says `approved` while its file sits in `superseded/` must be REFUSED, because the
    dangerous direction here is admitting, not refusing.
 2. Every selector FORM is filtered, not just `all`. Each case below names the same retired plan a
    different way, because the original defect was precisely that one form was checked and the others
    were not. A test that exercised only `all` would have passed against the bug.
 3. The two deliberately DIFFERENT shapes: a Set member is dropped SILENTLY (a Set is a topic label
    that legitimately holds its own finished work forever, so refusing the Set would make the
    selector unusable for exactly the Sets that have made progress), while an EXPLICITLY NAMED plan
    REFUSES LOUDLY (the operator typed that identifier, so a silent drop would send them hunting a
    typo that is not there).
 4. BOTH HOSTS give the SAME answers. The closure the fix deletes was a verbatim duplicate in
    `agy_runipd`, so the defect existed identically on both and a one-sided fix would have left the
    antigravity host broken. These tests drive each host's own `expand_selectors`.
 5. The empty-result message distinguishes "you named nothing" from "everything you named is
    finished". The fix made the second case common (263 Sets in this repository hold only terminal
    plans), and the old single message asserted the first, which is actively misleading.

NOTE ON FIXTURES: every plan here is written into a throwaway `tmp_path` repository. Nothing reads
`.aw/records/plans/` in the real tree, which is gitignored in CI and would make these tests pass
locally and fail everywhere else.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import agy_runipd, oc_runipd, runner_shared

HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _write(repo: Path, bucket: str, name: str, body: str) -> Path:
    target = repo / ".aw" / "records" / "plans" / bucket
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    path.write_text(body, encoding="utf-8")
    return path


class TheAdmissionPredicateTests(unittest.TestCase):
    """`manifest_entry_is_selectable` in isolation, fail-closed cases included."""

    def test_a_live_approved_plan_in_pending_is_selectable(self):
        self.assertTrue(
            runner_shared.manifest_entry_is_selectable(
                {"status": "approved", "file": ".aw/records/plans/pending/x.ipd.md"}
            )
        )

    def test_both_retired_dispositions_are_refused(self):
        for status, bucket in (
            ("superseded", "superseded"),
            ("not-executed", "not-executed"),
        ):
            with self.subTest(status=status):
                self.assertFalse(
                    runner_shared.manifest_entry_is_selectable(
                        {
                            "status": status,
                            "file": f".aw/records/plans/{bucket}/x.ipd.md",
                        }
                    )
                )

    def test_an_EXECUTED_plan_is_still_selectable_as_a_dependency_target(self):
        """The narrowing that a blunt "refuse everything terminal" rule gets WRONG.

        `initial_queue_status` preserves `executed` verbatim so a dependent's `executed:<id6>` edge is
        satisfied by a prerequisite that ran earlier in the same run, and spec `20260826-0718-01` 2.9
        forbids letting queue membership decide that edge. Filtering `executed` out of selection would
        restore the dead-prerequisite failure that killed 9 parents, 6 children and 2 orchestrators at
        queue build in one measured run.
        """

        self.assertTrue(
            runner_shared.manifest_entry_is_selectable(
                {"status": "executed", "file": ".aw/records/plans/executed/x.ipd.md"}
            )
        )
        self.assertIn("executed", runner_shared.TERMINAL_QUEUE_STATUSES)
        self.assertNotIn("executed", runner_shared.RETIRED_PLAN_STATUSES)

    def test_a_status_less_entry_is_still_selectable(self):
        """A hand-written static manifest carries no `status` key at all.

        `initial_queue_status(None)` answers `reviewed` for exactly that case, so an absent status
        means "this manifest does not track status", NOT "retired".
        """

        self.assertTrue(
            runner_shared.manifest_entry_is_selectable(
                {"file": ".aw/records/plans/pending/x.ipd.md"}
            )
        )

    def test_a_reusable_plan_is_selectable_because_it_is_standing(self):
        self.assertTrue(
            runner_shared.manifest_entry_is_selectable(
                {"status": "approved", "file": ".aw/records/plans/reusable/x.ipd.md"}
            )
        )

    def test_status_and_directory_are_checked_INDEPENDENTLY(self):
        """Either signal alone refuses, so a mid-move or hand-edited plan cannot slip through."""

        self.assertFalse(
            runner_shared.manifest_entry_is_selectable(
                {"status": "approved", "file": ".aw/records/plans/superseded/x.ipd.md"}
            )
        )
        self.assertFalse(
            runner_shared.manifest_entry_is_selectable(
                {"status": "superseded", "file": ".aw/records/plans/pending/x.ipd.md"}
            )
        )

    def test_an_absent_entry_fails_closed(self):
        for entry in (None, {}):
            with self.subTest(entry=entry):
                self.assertFalse(runner_shared.manifest_entry_is_selectable(entry))

    def test_the_sweep_rule_is_STRICTER_than_the_selection_rule(self):
        """`all` is opt-out so it skips finished work; a NAMED selector is opt-in so it does not."""

        executed = {"status": "executed", "file": ".aw/records/plans/executed/x.ipd.md"}
        self.assertTrue(runner_shared.manifest_entry_is_selectable(executed))
        self.assertFalse(runner_shared.manifest_entry_is_sweepable(executed))

        statusless = {"file": ".aw/records/plans/pending/x.ipd.md"}
        self.assertTrue(runner_shared.manifest_entry_is_selectable(statusless))
        self.assertFalse(runner_shared.manifest_entry_is_sweepable(statusless))

        live = {"status": "approved", "file": ".aw/records/plans/pending/x.ipd.md"}
        self.assertTrue(runner_shared.manifest_entry_is_selectable(live))
        self.assertTrue(runner_shared.manifest_entry_is_sweepable(live))

    def test_status_is_read_case_and_space_insensitively(self):
        self.assertTrue(
            runner_shared.manifest_entry_is_selectable(
                {"status": "  APPROVED  ", "file": ".aw/records/plans/pending/x.ipd.md"}
            )
        )


class EverySelectorFormIsFilteredTests(unittest.TestCase):
    """The same retired plan, named five different ways, refused every time, on both hosts.

    THE MIXED SET IS THE FIXTURE THE BUG NEEDED: one live child beside one retired orchestrator and
    one retired child, which is the `setidhard` shape that was measured in production.
    """

    def _repo(self, root: Path):
        repo = root / "repo"
        repo.mkdir()
        live = _write(
            repo,
            "pending",
            "20260908-mixed-02-liv111-still-open.ipd.md",
            "- Id: liv111\n- Set: mixed\n- Order: 2\n- Kind: child\n"
            "- Status: approved\n# Live\n",
        )
        retired_parent = _write(
            repo,
            "superseded",
            "20260908-mixed-00-ded000-retired-orchestrator.ipd.md",
            "RETIRED 2026-09-10: the design was reversed.\n\n"
            "- Id: ded000\n- Set: mixed\n- Order: 0\n- Kind: orchestrator\n"
            "- Status: superseded\n# Retired parent\n",
        )
        retired_child = _write(
            repo,
            "superseded",
            "20260908-mixed-01-ded111-retired-child.ipd.md",
            "RETIRED 2026-09-10: this deliverable must NOT happen.\n\n"
            "- Id: ded111\n- Set: mixed\n- Order: 1\n- Kind: child\n"
            "- Status: superseded\n# Retired child\n",
        )
        manifest = oc_runipd.build_dynamic_manifest(
            repo, oc_runipd.discover_plans(repo)
        )
        return repo, manifest, live, retired_parent, retired_child

    def test_naming_the_set_drops_the_retired_members_silently(self):
        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest, _live, _rp, _rc = self._repo(Path(tmp))
                # The Set's ORDER still contains all three: the drop happens at selection, and the
                # manifest is not rewritten.
                self.assertEqual(
                    manifest["sets"]["mixed"]["order"],
                    ["ded000", "ded111", "liv111"],
                )
                self.assertEqual(
                    driver.expand_selectors(manifest, ["mixed"], repo=repo),
                    ["liv111"],
                )

    def test_naming_the_set_by_unique_prefix_also_drops_them(self):
        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest, _live, _rp, _rc = self._repo(Path(tmp))
                self.assertEqual(
                    driver.expand_selectors(manifest, ["mix"], repo=repo), ["liv111"]
                )

    def test_the_all_selector_agrees_with_the_set_selector(self):
        """The regression that started it: these two disagreed, and `all` was the only safe one."""

        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest, _live, _rp, _rc = self._repo(Path(tmp))
                self.assertEqual(
                    driver.expand_selectors(manifest, ["all"], repo=repo),
                    driver.expand_selectors(manifest, ["mixed"], repo=repo),
                )

    def test_naming_a_retired_plan_by_id6_refuses_loudly(self):
        for label, driver in HOSTS:
            for id6 in ("ded000", "ded111"):
                with (
                    self.subTest(host=label, id6=id6),
                    TemporaryDirectory() as tmp,
                ):
                    repo, manifest, _live, _rp, _rc = self._repo(Path(tmp))
                    with self.assertRaises(runner_shared.DriverError) as caught:
                        driver.expand_selectors(manifest, [id6], repo=repo)
                    message = str(caught.exception)
                    self.assertIn(id6, message)
                    self.assertIn("superseded", message)
                    # It must NOT masquerade as a selector-syntax problem.
                    self.assertNotIn(
                        "At least one id6 or Set selector is required", message
                    )

    def test_naming_a_retired_plan_by_file_path_refuses_loudly(self):
        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest, _live, retired_parent, _rc = self._repo(Path(tmp))
                with self.assertRaises(runner_shared.DriverError) as caught:
                    driver.expand_selectors(manifest, [str(retired_parent)], repo=repo)
                self.assertIn("ded000", str(caught.exception))

    def test_naming_a_retired_plan_by_filename_substring_refuses_loudly(self):
        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest, _live, _rp, _rc = self._repo(Path(tmp))
                with self.assertRaises(runner_shared.DriverError) as caught:
                    driver.expand_selectors(
                        manifest, ["retired-orchestrator"], repo=repo
                    )
                self.assertIn("ded000", str(caught.exception))

    def test_a_live_plan_named_directly_still_runs(self):
        """The negative control. A filter that refused everything would pass every test above."""

        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest, live, _rp, _rc = self._repo(Path(tmp))
                self.assertEqual(
                    driver.expand_selectors(manifest, ["liv111"], repo=repo),
                    ["liv111"],
                )
                self.assertEqual(
                    driver.expand_selectors(manifest, [str(live)], repo=repo),
                    ["liv111"],
                )


class TheEmptyResultExplainsItselfTests(unittest.TestCase):
    """A Set whose every member is RETIRED must not report a selector syntax error.

    Both members below are retired (`superseded` and `not-executed`). An `executed` member would NOT
    belong here: it is legitimately selectable as a dependency target, so a Set containing one is not
    empty.
    """

    def _retired_only_repo(self, root: Path):
        repo = root / "repo"
        repo.mkdir()
        _write(
            repo,
            "superseded",
            "20260908-gone-01-gon111-retired.ipd.md",
            "- Id: gon111\n- Set: gone\n- Order: 1\n- Kind: child\n"
            "- Status: superseded\n# Gone\n",
        )
        _write(
            repo,
            "not-executed",
            "20260908-gone-02-gon222-declined.ipd.md",
            "- Id: gon222\n- Set: gone\n- Order: 2\n- Kind: child\n"
            "- Status: not-executed\n# Declined\n",
        )
        manifest = oc_runipd.build_dynamic_manifest(
            repo, oc_runipd.discover_plans(repo)
        )
        return repo, manifest

    def test_a_fully_finished_set_says_so_and_names_the_plans(self):
        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest = self._retired_only_repo(Path(tmp))
                with self.assertRaises(runner_shared.DriverError) as caught:
                    driver.expand_selectors(manifest, ["gone"], repo=repo)
                message = str(caught.exception)
                self.assertIn("was RETIRED", message)
                self.assertIn("gon111", message)
                self.assertIn("gon222", message)
                self.assertIn("superseded", message)
                self.assertIn("not-executed", message)
                # The point of the separate message: it is NOT a typo.
                self.assertIn("not a selector typo", message)
                self.assertNotIn(
                    "At least one id6 or Set selector is required", message
                )

    def test_passing_no_selectors_still_reports_a_missing_selector(self):
        """The other branch of the same error path must keep its own meaning."""

        for label, driver in HOSTS:
            with self.subTest(host=label), TemporaryDirectory() as tmp:
                repo, manifest = self._retired_only_repo(Path(tmp))
                with self.assertRaises(runner_shared.DriverError) as caught:
                    driver.expand_selectors(manifest, [], repo=repo)
                self.assertIn(
                    "At least one id6 or Set selector is required",
                    str(caught.exception),
                )


class TheTwoHostsShareOnePredicateTests(unittest.TestCase):
    """Anti-re-fork: the admission test must be ONE object, not a copy per host.

    The defect this file exists for was duplicated byte-for-byte across the two drivers, so a
    behavioral test alone would not stop it returning: someone re-inlining the closure in one host
    would keep these tests green until the two answers happened to differ. This asserts the shared
    binding directly.
    """

    def test_neither_driver_defines_its_own_admission_closure(self):
        for label, driver in HOSTS:
            with self.subTest(host=label):
                source = Path(driver.__file__).read_text(encoding="utf-8")
                self.assertNotIn(
                    "actionable_statuses = {",
                    source,
                    msg=(
                        f"{label} re-inlined the admission allowlist; call "
                        "runner_shared.manifest_entry_is_selectable instead"
                    ),
                )
                self.assertNotIn(
                    'or "/not-executed/" in f_str',
                    source,
                    msg=(
                        f"{label} re-implemented the terminal-directory test; ask "
                        "run_selection_policy.is_in_terminal_directory through the shared predicate"
                    ),
                )

    def test_the_shared_predicate_is_reachable_from_both_drivers(self):
        for _label, driver in HOSTS:
            self.assertIs(
                driver.runner_shared.manifest_entry_is_selectable,
                runner_shared.manifest_entry_is_selectable,
            )


if __name__ == "__main__":
    unittest.main()
