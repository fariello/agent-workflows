"""Tests for the frozen attention-view contracts (Set attnview, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies:
- the class enum + tree-policy inventory shapes;
- the PURE, TOTAL per-tree mapping (coverage test: mapping keys == each tree's canonical native enum);
- the spec transition/authority table + the anti-self-approval floor is stated;
- the gate per-kind validators + output-safety rules;
- the workflow-history record grammar + last_history_at derivation;
- the closed stable rule-id catalog + the detail-escaping policy;
- that the on-disk fixtures parse / are rejected as intended.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import plans
from agent_workflows import research_contract

FIX = Path(__file__).parent / "fixtures" / "attnview"


class EnumAndPolicyTests(unittest.TestCase):
    def test_five_classes(self):
        self.assertEqual(
            A.ATTENTION_CLASSES,
            frozenset(("ready", "active", "blocked", "done", "parked")),
        )
        self.assertEqual(set(A.ATTENTION_CLASS_ORDER), A.ATTENTION_CLASSES)

    def test_tree_policy_tracked_and_excluded(self):
        tracked = {p.name for p in A.TREE_POLICY if p.tracked}
        self.assertEqual(tracked, {"specs", "plans", "research", "backlog", "releases"})
        for p in A.TREE_POLICY:
            if p.tracked:
                self.assertTrue(p.owner, f"tracked tree {p.name} needs an owner")
            else:
                self.assertTrue(p.reason, f"excluded tree {p.name} needs a rationale")
        # the evergreen prompt LIBRARY is an explicitly excluded tree (distinct from .agents/prompts)
        self.assertIn("docs-prompts", {p.name for p in A.TREE_POLICY if not p.tracked})

    def test_nonartifact_names(self):
        for n in (
            "README.md",
            "INDEX.md",
            "STATUS.md",
            "conformance-results-template.md",
            "00-README-index.md",
            "some-index.md",
        ):
            self.assertTrue(A.is_nonartifact_name(n), n)
        for n in ("20260808-attnview-01-abc123-x.md", "s.md", "a-real-spec.md"):
            self.assertFalse(A.is_nonartifact_name(n), n)


class MappingTotalityTests(unittest.TestCase):
    """The load-bearing guard (spec Section 6 / A2): mapping keys == each tree's canonical native enum."""

    def test_specs_total(self):
        self.assertEqual(set(A.CLASS_MAPS["specs"].keys()), set(A.SPEC_STATUSES))

    def test_plans_total_over_RECOGNIZED(self):
        self.assertEqual(set(A.CLASS_MAPS["plans"].keys()), set(plans.RECOGNIZED))

    def test_research_total_over_STATUSES(self):
        self.assertEqual(
            set(A.CLASS_MAPS["research"].keys()), set(research_contract.STATUSES)
        )

    def test_releases_total_over_RELEASE_STATUSES(self):
        """durablecapture-02 (`m867ox`) E-02: the missing sibling of the three tests above.

        `releases` was the only TRACKED tree with no map-totality guard (`RELEASE_STATUSES` grepped to
        zero hits under `tests/`), so the map happened to be total while nothing kept it so. This is
        what makes a status added to `releases.RELEASE_STATUSES` fail CLOSED here instead of reaching
        `class_of` unmapped at runtime.
        """
        from agent_workflows import releases

        self.assertEqual(
            set(A.CLASS_MAPS["releases"].keys()), set(releases.RELEASE_STATUSES)
        )

    def test_every_value_is_a_class(self):
        for tree, frag in A.CLASS_MAPS.items():
            for status, cls in frag.items():
                self.assertIn(cls, A.ATTENTION_CLASSES, f"{tree}:{status} -> {cls}")

    def test_class_of_and_unknown(self):
        self.assertEqual(A.class_of("specs", "implemented"), "done")
        self.assertEqual(A.class_of("plans", "approved"), "ready")  # OQ5: not active
        self.assertEqual(A.class_of("plans", "auto-approved"), "ready")
        self.assertEqual(
            A.class_of("research", "active"), "active"
        )  # live active source in v1
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("specs", "frobnicated")
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("prompts", "anything")  # not a tracked tree


class TransitionAuthorityTests(unittest.TestCase):
    def test_legal_and_illegal(self):
        self.assertTrue(A.transition_allowed("reviewed", "approved"))
        self.assertTrue(A.transition_allowed("approved", "implementing"))
        self.assertTrue(A.transition_allowed("implementing", "implemented"))
        self.assertFalse(A.transition_allowed("draft", "implemented"))
        self.assertFalse(A.transition_allowed("implemented", "approved"))

    def test_authority_and_floor(self):
        self.assertEqual(A.TRANSITION_AUTHORITY["->approved"]["who"], "human")
        self.assertTrue(
            A.TRANSITION_AUTHORITY["->approved"].get("by_human")
            or A.TRANSITION_AUTHORITY["->approved"].get("human_token")
        )
        self.assertTrue(A.TRANSITION_AUTHORITY["->implemented"]["evidence"])
        # The anti-self-approval floor requires an explicit --by-human attestation speed bump (revised 2026-08-15).
        self.assertIn("--by-human", A.APPROVAL_FLOOR)
        self.assertIn("INSUFFICIENT", A.APPROVAL_FLOOR)

    def test_reviewed_transition_is_attested(self):
        """revsweep `5slbpi` E-04: `->reviewed` carries a `review_record` requirement.

        It had NO entry at all before, which is the hole this plan closed: `aw specs set reviewed`
        succeeded with no review, no findings, and no record, while the same claim on a plan was
        policed. This asserts the entry exists AND that it is the record kind rather than being
        mis-declared as a `--evidence` citation (there is no `--evidence` flag on this transition, so
        declaring `evidence: True` would make it unsatisfiable).
        """
        entry = A.TRANSITION_AUTHORITY["->reviewed"]
        self.assertTrue(entry["review_record"])
        self.assertFalse(entry["evidence"])
        self.assertFalse(entry["by_human"])
        self.assertFalse(entry["human_token"])
        self.assertEqual(entry["who"], "reviewer")

    def test_approval_floor_states_the_review_record_requirement_and_its_limit(self):
        """The floor is the human-readable contract, so a new requirement must appear IN it.

        And it must appear WITH its honest limit: the attestation proves a review occurred and was
        recorded, never that it was competent. Overselling it is the failure mode the plan named.
        """
        self.assertIn("REVIEW RECORD", A.APPROVAL_FLOOR)
        self.assertIn("Subject-Id", A.APPROVAL_FLOOR)
        self.assertIn("does NOT prove the review was competent", A.APPROVAL_FLOOR)

    def test_every_authority_key_is_a_reachable_transition(self):
        """An authority entry for a transition the graph forbids would be dead, unfireable config.

        Asserted rather than eyeballed because the entry added by `5slbpi` is the first one whose
        target is a NON-terminal status, so the pairing with `SPEC_TRANSITIONS` is newly load-bearing.
        """
        reachable = {new for allowed in A.SPEC_TRANSITIONS.values() for new in allowed}
        for key in A.TRANSITION_AUTHORITY:
            self.assertTrue(key.startswith("->"), f"malformed authority key {key!r}")
            self.assertIn(
                key[2:],
                reachable,
                f"{key} has authority but no legal transition reaches it",
            )


class GateTests(unittest.TestCase):
    def test_gate_kinds(self):
        self.assertEqual(
            A.GATE_KINDS,
            frozenset(("artifact", "decision", "todo", "issue", "date", "external")),
        )

    def test_gate_ref_validators(self):
        self.assertTrue(A.validate_gate_ref("date", "2026-08-08"))
        self.assertFalse(A.validate_gate_ref("date", "2026-8-8"))
        self.assertTrue(A.validate_gate_ref("issue", "https://example.com/issues/1"))
        self.assertFalse(
            A.validate_gate_ref("issue", "javascript:alert(1)")
        )  # non-http rejected
        self.assertFalse(A.validate_gate_ref("issue", "http://"))
        self.assertTrue(A.validate_gate_ref("artifact", ".agents/plans/x.md#anchor"))
        self.assertFalse(
            A.validate_gate_ref("artifact", "../escape.md")
        )  # repo-escaping rejected
        self.assertFalse(A.validate_gate_ref("artifact", "/abs/path.md"))
        self.assertTrue(A.validate_gate_ref("decision", "D124"))
        self.assertFalse(A.validate_gate_ref("decision", "not-a-decision"))
        self.assertTrue(A.validate_gate_ref("todo", "TODO-14"))
        self.assertTrue(A.validate_gate_ref("external", "vendor-ticket-9"))
        self.assertFalse(A.validate_gate_ref("external", ""))
        self.assertFalse(A.validate_gate_ref("bogus-kind", "x"))

    def test_output_safety(self):
        self.assertTrue(A.is_safe_descriptive("a normal single line"))
        self.assertFalse(A.is_safe_descriptive("x" * (A.MAX_DESCRIPTIVE_LEN + 1)))
        self.assertFalse(A.is_safe_descriptive("line1\nline2"))
        self.assertFalse(A.is_safe_descriptive("bell\x07here"))
        self.assertFalse(A.is_safe_descriptive("esc\x1b[31mred"))


class HistoryTests(unittest.TestCase):
    """The `last_history_at` derivation (spec Section 8.5) and the ONE newest-record rule under it.

    WHY THE NEWEST-FIRST CASE BELOW IS THE LOAD-BEARING ONE (plan `vhbvwz` E-02/E-06, finding F-13).
    This class used to hold a single OLDEST-FIRST fixture, and an oldest-first fixture cannot tell
    the two candidate rules apart: its first and last records are both its extreme dates, so a
    reader taking the LAST record passes it while being wrong about every real artifact. That is why
    the contradiction between this derivation and `plan_readiness.extract_newest_history_entry`
    survived a review of the spec that introduced it, and why it stayed invisible for specs and
    backlog (slimmed to one record, where first and last coincide) while being wrong on 373 of 679
    multi-record plans. Keep BOTH fixtures: the newest-first one is the one that fails if the rule
    regresses.
    """

    def test_newest_first_section_yields_its_newest_record(self):
        # THE REAL SHAPE every writer produces: `status_set` PREPENDS, so the section is newest-first
        # and the artifact's current state is the FIRST record. A reader taking the last record
        # reports 2026-08-01 here, i.e. the date this plan was CREATED, as the date it was last
        # touched - the exact misreading measured on 534 live artifacts.
        lines = [
            "- 2026-08-08 approved (z): approved.",
            "not a record",
            "- 2026-08-05 reviewed (y): reviewed.",
            "- 2026-08-01 draft (x): created.",
        ]
        self.assertEqual(A.last_history_at(lines), "2026-08-08")
        self.assertEqual(
            A.newest_history_record(lines), "- 2026-08-08 approved (z): approved."
        )

    def test_last_history_at(self):
        # The legacy OLDEST-FIRST fixture, kept because a minority of real artifacts are written that
        # way and must still resolve. It is NOT evidence about the rule: see the class docstring.
        lines = [
            "- 2026-08-01 draft (x): created.",
            "- 2026-08-05 reviewed (y): reviewed.",
            "not a record",
            "- 2026-08-08 approved (z): approved.",
        ]
        self.assertEqual(A.last_history_at(lines), "2026-08-01")
        self.assertIsNone(A.last_history_at(["no records here", "- bad date line"]))
        self.assertIsNone(A.newest_history_record([]))

    def test_the_newest_record_rule_is_single_sourced(self):
        """`plan_readiness` must CONSUME the rule, not re-implement it (E-02's single-source demand).

        Two readers of "which record is newest" disagreed once already and the disagreement was a
        live bug; this asserts they cannot disagree again, by checking the plan-side reader returns
        exactly what the shared rule returns for a section whose first and last records differ.
        """
        from agent_workflows import plan_readiness as PR

        text = (
            "# IPD: x\n\n## Workflow history\n"
            "- 2026-09-03 approved (aw set): newest.\n"
            "- 2026-09-01 draft (aw set): oldest.\n\n## Goal\n"
        )
        self.assertEqual(
            PR.extract_newest_history_entry(text),
            "- 2026-09-03 approved (aw set): newest.",
        )
        self.assertEqual(
            PR.extract_newest_history_entry(text),
            A.newest_history_record(
                [
                    "- 2026-09-03 approved (aw set): newest.",
                    "- 2026-09-01 draft (aw set): oldest.",
                ]
            ),
        )


class RuleCatalogTests(unittest.TestCase):
    def test_catalog_closed_and_named(self):
        # Every rule id is stable and namespaced; the set is closed (one per violation class).
        for rid in A.RULE_IDS:
            self.assertTrue(rid.startswith("attention."), rid)
        self.assertIn("attention.unclassified-tree", A.RULE_IDS)
        self.assertIn("attention.unsafe-field", A.RULE_IDS)
        self.assertGreaterEqual(len(A.RULE_IDS), 12)

    def test_detail_escaping_keeps_one_line(self):
        detail = "tab\there\nnewline\\backslash"
        esc = A.escape_detail(detail)
        self.assertNotIn("\n", esc)
        self.assertNotIn("\t", esc)
        self.assertIn("\\t", esc)
        self.assertIn("\\n", esc)


class FixtureParseTests(unittest.TestCase):
    """The committed fixtures parse (valid) or are rejected (violations) per the contract."""

    def _read_status(self, path):
        for line in path.read_text(encoding="utf-8").splitlines():
            m = A.SPEC_STATUS_RE.match(line)
            if m:
                return m.group("value")
        return None

    def test_valid_specs_have_bare_enum_status_and_map(self):
        for f in sorted((FIX / "specs-valid").glob("*.md")):
            status = self._read_status(f)
            self.assertIsNotNone(status, f"{f.name}: no bare-enum - Status: bullet")
            self.assertIn(
                status, A.SPEC_STATUSES, f"{f.name}: {status} not a spec status"
            )
            self.assertIn(A.class_of("specs", status), A.ATTENTION_CLASSES)

    def test_trailing_prose_status_is_rejected(self):
        # The grammar requires a bare token; the trailing-prose fixture must NOT parse as a bare status.
        f = FIX / "violations" / "status-trailing-prose.md"
        self.assertIsNone(
            self._read_status(f),
            "trailing-prose status must not match the bare-enum grammar",
        )

    def test_unknown_status_fixture_is_unmapped(self):
        f = FIX / "violations" / "unknown-status.md"
        status = self._read_status(f)
        self.assertEqual(status, "frobnicated")
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("specs", status)

    def test_unsafe_field_fixture_is_unsafe(self):
        f = FIX / "violations" / "unsafe-field.md"
        summary = None
        for line in f.read_text(encoding="utf-8").splitlines():
            m = A.GATE_SUMMARY_RE.match(line)
            if m:
                summary = m.group("value")
        self.assertIsNotNone(summary)
        self.assertFalse(A.is_safe_descriptive(summary))  # over-length

    def test_simulated_unreadable_and_symlink(self):
        # Non-committable violation classes, simulated in a temp tree (never committed).
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outside = root / "outside.md"
            outside.write_text("secret\n", encoding="utf-8")
            repo = root / "repo"
            repo.mkdir()
            link = repo / "escape.md"
            try:
                link.symlink_to(outside)
                # a symlink target escaping the repo root -> unstable-path class
                resolved = link.resolve()
                self.assertFalse(str(resolved).startswith(str(repo.resolve())))
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on this platform")


def _scan_root_covers_tree(root: str, tree: str) -> bool:
    """True when scan root ``root`` causes tree ``tree``'s records to be walked.

    THE THREE NAIVE FORMS ARE MEASURED WRONG and are recorded here so the next reader does not
    "simplify" this back into one of them (all measured at HEAD ``cdace6a5``):

    (a) SUBSTRING, ``any(tree in root ...)``. It happens to give the right answers today, but it
        matches any root whose TEXT contains the tree name, so an unrelated path (``.agents/releases-
        archive``, a ``docs/plans-notes``) would be reported as covering a tree it never walks. It
        tests spelling, not containment.
    (b) CLASSIFY-ONLY, ``_classify_tree(root).name == tree``. It fails on an ANCESTOR root:
        ``_classify_tree('.agents/docs')`` returns ``None`` while ``.agents/docs`` is precisely the
        root under which the ``specs`` (``.agents/docs/specs``) and ``research``
        (``.agents/docs/research``) policy roots live. Measured over the legacy ``.agents/``-only
        root set, this form reports ``specs`` and ``research`` UNCOVERED, which is wrong.
    (c) TREE-NAME-ONLY policy lookup, ``next(p for p in TREE_POLICY if p.name == t)``. It RAISES
        ``StopIteration`` for a tracked tree with no policy. That cannot arise through the derived
        ``TRACKED_TREES``, but it is exactly what the mutation test constructs, so the lookup below is
        written defensively (``next(..., None)``) rather than assuming a policy exists.

    THE FORM USED HERE accepts a root that IS the policy root, is INSIDE it, CONTAINS it (the
    ancestor case (b) misses), or CLASSIFIES to it (which is what resolves the ``.aw/records/<type>``
    twin spelling through ``attention._classify_tree``'s rewrite).
    """

    from agent_workflows import attention as ATT

    pol = next((p for p in A.TREE_POLICY if p.name == tree), None)
    if pol is None:
        return False
    r = root.replace("\\", "/")
    proot = pol.root.replace("\\", "/")
    if r == proot or r.startswith(proot + "/"):
        return True  # the root is, or is inside, the tree
    if proot.startswith(r + "/"):
        return True  # the root is an ANCESTOR of the tree (e.g. .agents/docs -> specs)
    classified = ATT._classify_tree(r)
    return classified is not None and classified.name == tree


class TrackedTreeScanCoverageTests(unittest.TestCase):
    """durablecapture-02 (`m867ox`) E-04: every TRACKED tree must have at least one SCAN root.

    THE DRIFT THIS EXISTS TO STOP, which actually happened: ``releases`` was declared tracked in
    ``TREE_POLICY``, carried a complete status map, and matched NO entry in
    ``artifact_core.SCAN_ROOTS``, so every release record was invisible to ``aw attention`` while the
    view still reported ``valid: true``. It reported valid because ``attention.scan`` raises
    ``attention.unclassified-tree`` only for paths under ``.agents/``, so a ``.aw/records/`` file
    under no scanned root is dropped SILENTLY. Two lists encoded one fact and they diverged with no
    test in between.

    WHAT THIS GUARD PROVES, AND WHAT IT DOES NOT. It proves DECLARATION: a tracked tree has SOME scan
    root. It does NOT prove REACHABILITY: that the tree's records actually ARRIVE in the view.
    Measured, so this limit is a fact and not a caveat: with only ``.agents/releases`` in
    ``SCAN_ROOTS`` this guard is GREEN while ``attention.scan`` still yields ZERO releases items,
    because ``releases._releases_dir`` writes and reads ``.aw/records/releases`` and no
    ``.agents/releases`` directory exists in this repository. So a reader must not treat this passing
    as evidence that a tree is surfaced; `ReleaseRecordsReachTheViewTests` below asserts reachability
    for releases specifically, and E-05 mutation 3 proves the gap is real.

    THE CHECK IS DELIBERATELY ONE-DIRECTIONAL (tracked tree -> scan root, never the reverse).
    ``SCAN_ROOTS`` legitimately contains entries that are NOT tracked trees, because it is the shared
    tracked-TEXT enumeration for the citation/dangling tools, not a list of lifecycle trees: four root
    docs (``DECISIONS.md``, ``TODO.md``, ``README.md``, ``ARCHITECTURE.md``), the ``.agents/docs``
    ancestor, and three deliberately EXCLUDED trees (``.aw/records/walkthroughs``,
    ``.aw/records/roadmaps``, ``.aw/records/prompt-library``). A symmetric assertion would fail
    immediately and WRONGLY on all eight, so do not "fix" this into one.
    """

    def test_every_tracked_tree_has_a_scan_root(self):
        from agent_workflows import artifact_core as core

        uncovered = [
            t
            for t in A.TRACKED_TREES
            if not any(_scan_root_covers_tree(r, t) for r in core.SCAN_ROOTS)
        ]
        self.assertEqual(
            uncovered,
            [],
            "TRACKED but never SCANNED: "
            + ", ".join(uncovered)
            + ". Every tree in TRACKED_TREES must have at least one artifact_core.SCAN_ROOTS entry, "
            "or its records are invisible to `aw attention` while the view still reports "
            "valid: true (an unclassified file is only flagged as drift under .agents/). "
            "THE CONSTRUCTIVE FIX IS TO ADD THE TREE'S SCAN ROOT to artifact_core.SCAN_ROOTS "
            "(add BOTH the .agents/<tree> and .aw/records/<tree> spellings, as plans and backlog "
            "do; the .aw/records/ one is normally the load-bearing entry). "
            "DO NOT silence this by removing the tree from the attention view: TRACKED_TREES is "
            "DERIVED from TREE_POLICY, so flipping that policy's tracked=True to tracked=False "
            "would make this pass while HIDING the tree from the view entirely, which is the "
            "opposite of the fix.",
        )

    def test_the_predicate_handles_the_ancestor_and_twin_spelling_cases(self):
        """The two cases that reject the naive predicate forms, asserted directly.

        Without these, a future simplification to a classify-only predicate would pass this module's
        other test on the CURRENT root list (because ``.aw/records/specs`` is also present) and only
        break on a repository still using the legacy ``.agents/`` layout.
        """

        from agent_workflows import attention as ATT

        # ANCESTOR: `.agents/docs` classifies to NOTHING, yet it is the scanned parent of both
        # `.agents/docs/specs` and `.agents/docs/research`.
        self.assertIsNone(ATT._classify_tree(".agents/docs"))
        self.assertTrue(_scan_root_covers_tree(".agents/docs", "specs"))
        self.assertTrue(_scan_root_covers_tree(".agents/docs", "research"))
        # TWIN SPELLING: the `.aw/records/<type>` generation resolves through `_classify_tree`'s
        # rewrite even though it does not literally prefix-match the `.agents/` policy root.
        self.assertTrue(_scan_root_covers_tree(".aw/records/specs", "specs"))
        self.assertTrue(_scan_root_covers_tree(".aw/records/releases", "releases"))
        # NEGATIVE: an unrelated root covers nothing, and a tree with no policy is never "covered"
        # (the defensive lookup returns False instead of raising StopIteration).
        self.assertFalse(_scan_root_covers_tree("DECISIONS.md", "releases"))
        self.assertFalse(_scan_root_covers_tree(".aw/records/releases", "frobnicated"))

    def test_the_guard_fails_for_a_tracked_tree_with_no_scan_root(self):
        """E-05 mutation 1, as a permanent test: a tracked tree with no scan root must FAIL.

        MUTATED THROUGH ``TREE_POLICY``, NOT ``TRACKED_TREES``. The latter is DERIVED
        (``tuple(p.name for p in TREE_POLICY if p.tracked)``), so appending to it would be a no-op
        against the real value and the mutation would prove nothing.
        """

        from agent_workflows import artifact_core as core

        mutated_policy = A.TREE_POLICY + (
            A.TreePolicy("frobnicated", ".agents/frobnicated", True, "aw frob", "test"),
        )
        mutated_tracked = tuple(p.name for p in mutated_policy if p.tracked)
        self.assertIn("frobnicated", mutated_tracked)
        original = A.TREE_POLICY
        try:
            A.TREE_POLICY = mutated_policy  # type: ignore[misc]
            uncovered = [
                t
                for t in mutated_tracked
                if not any(_scan_root_covers_tree(r, t) for r in core.SCAN_ROOTS)
            ]
        finally:
            A.TREE_POLICY = original  # type: ignore[misc]
        self.assertEqual(uncovered, ["frobnicated"])
        # and the real lists are unchanged after the revert
        self.assertEqual(
            [
                t
                for t in A.TRACKED_TREES
                if not any(_scan_root_covers_tree(r, t) for r in core.SCAN_ROOTS)
            ],
            [],
        )

    def test_removing_the_releases_scan_root_fails_the_guard(self):
        """E-05 mutation 2, as a permanent test: the guard would have caught the REAL defect.

        This is the load-bearing mutation. It reconstructs the exact pre-fix state (``releases``
        tracked, no releases scan root) and asserts the guard names it.
        """

        from agent_workflows import artifact_core as core

        pre_fix_roots = tuple(r for r in core.SCAN_ROOTS if not r.endswith("/releases"))
        self.assertNotIn(".aw/records/releases", pre_fix_roots)
        self.assertNotIn(".agents/releases", pre_fix_roots)
        uncovered = [
            t
            for t in A.TRACKED_TREES
            if not any(_scan_root_covers_tree(r, t) for r in pre_fix_roots)
        ]
        self.assertEqual(uncovered, ["releases"])


class ReviewsTreeIsDecidedTests(unittest.TestCase):
    """durablecapture-02 (`m867ox`) E-03: `reviews` is an EXPLICIT exclusion, not an omission.

    Spec 20260808-1945-01 Section 8.6 requires every known tree to be tracked or excluded WITH a
    rationale; `reviews` was neither, which that section itself calls a violation.
    """

    def test_reviews_is_excluded_with_a_rationale(self):
        pol = next((p for p in A.TREE_POLICY if p.name == "reviews"), None)
        self.assertIsNotNone(pol, "the reviews tree must be inventoried, not absent")
        assert pol is not None
        self.assertFalse(pol.tracked)
        self.assertEqual(pol.owner, "")
        # The reason must state BOTH halves, to the standard the five existing exclusions set.
        self.assertIn("Status:", pol.reason)  # no native status enum to be total over
        self.assertIn(
            "check.review-finding-unescalated", pol.reason
        )  # enforcement kept

    def test_reviews_has_no_status_map_and_no_scan_root(self):
        from agent_workflows import artifact_core as core

        # No map: an excluded tree has no (tree, native_status) -> class mapping to be total over.
        self.assertNotIn("reviews", A.CLASS_MAPS)
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("reviews", "anything")
        # No scan root: `attention.scan` filters an excluded tree AFTER reading it, so a root would
        # buy nothing but per-invocation file reads.
        self.assertFalse(
            any(_scan_root_covers_tree(r, "reviews") for r in core.SCAN_ROOTS)
        )


class ReleaseRecordsReachTheViewTests(unittest.TestCase):
    """durablecapture-02 (`m867ox`) E-02: assert REACHABILITY, through `attention.scan`.

    The defect this closes was a correct map that nothing ever called, so asserting `class_of`
    directly would not have caught it. These synthesize records in a temp repo rather than reading the
    one live record in this checkout, which would break the day that release ships, and they assert no
    total item count (every count in this plan's history went stale).
    """

    def _scan_synth(self, status: str, subdir: str):
        from agent_workflows import attention as ATT

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = f".aw/records/releases/{subdir}20260101-rel-01-relr{status[0]}-x.release.md"
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                f"# Release 9.9.9\n\n- Status: {status}\n- Id: relr{status[0]}\n"
                f"- Version: 9.9.9\n\n## Workflow history\n- 2026-01-01 {status} (r): n\n",
                encoding="utf-8",
            )
            items, drift = ATT.scan(root)
            return [i for i in items if i.tree == "releases"], drift, rel

    def test_every_release_status_reaches_its_declared_class_through_scan(self):
        from agent_workflows import releases

        # Both layouts are in live use: FLAT (the live record) and a `<status>/` SUBDIRECTORY.
        for subdir in ("", "planned/"):
            for status in releases.RELEASE_STATUSES:
                got, drift, rel = self._scan_synth(status, subdir)
                self.assertEqual(
                    [i.path for i in got], [rel], f"{status} @ {subdir!r} not scanned"
                )
                self.assertEqual(got[0].native_status, status)
                self.assertEqual(
                    got[0].attention_class,
                    A.CLASS_MAPS["releases"][status],
                    f"{status} @ {subdir!r} got the wrong class",
                )
                self.assertEqual(drift, [])

    def test_the_release_readme_is_not_an_artifact(self):
        """The tree's README must be dropped by `is_nonartifact_name`, not counted as a record."""

        self.assertTrue(A.is_nonartifact_name("README.md"))


if __name__ == "__main__":
    unittest.main()
