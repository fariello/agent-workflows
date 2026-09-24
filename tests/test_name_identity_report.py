"""findtier Order 02 (`3i6rso`): the declared-identity-absent-from-filename ADVISORY.

WHAT THIS RULE IS FOR, because the severity and every false-positive guard below follow from it.
`aw find` cannot trust a filename to carry a record's identity, so it keeps a mandatory CONTENT
fallback that opens every record. Retiring that fallback needs EVIDENCE that the set of records whose
filename omits their declared identity is small and not growing, and nothing counted that set. This
rule is the count.

WHY THE TESTS ARE FIXTURE TREES AND NOT LIVE-TREE ASSERTIONS. The live members change: the pending
plan `76w6mq` removes the quoted-example readings, and several agents author records concurrently. A
test keyed on a live record would fail for a reason that has nothing to do with this rule. The live
tree appears in exactly ONE place here, `LiveCountEvidenceTests`, which records the count as EVIDENCE
with a tolerance rather than pinning members.

THE FOUR FALSE-POSITIVE GUARDS ARE THE POINT OF THIS FILE, not the positive case. A report that named
a correctly-named file as a rename candidate would be WORSE than no report: it would send a
maintainer to damage a correct name while appearing helpful. Each guard is a separate test with the
measured record that motivated it named in its docstring.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import artifact_naming as naming
from agent_workflows import check_engine as ce

RULE = "check.identity-absent-from-name"
IDENTITY_SLOT = "check.id6-identity-slot"

PLANS = ".aw/records/plans/pending"
EXECUTED = ".aw/records/plans/executed"
SPECS = ".aw/records/specs"


def _tree() -> Path:
    root = Path(tempfile.mkdtemp())
    for rel in (PLANS, EXECUTED, SPECS):
        (root / rel).mkdir(parents=True, exist_ok=True)
    return root


def _write(root: Path, rel: str, name: str, text: str) -> Path:
    p = root / rel / name
    p.write_text(text, encoding="utf-8")
    return p


def _plan(id6: str, setid: str = "demo", status: str = "approved") -> str:
    return (
        f"# IPD: x\n\n- Date: 2026-01-01\n- Kind: child\n- Status: {status}\n"
        f"- Set: {setid}\n- Order: 1\n- Id: {id6}\n\n## Goal\n\nx\n"
    )


def _spec(id6: str, setid: str = "demo") -> str:
    return (
        f"# Spec: x\n\n- Date: 2026-01-01\n- Status: reviewed\n- Set: {setid}\n"
        f"- Id: {id6}\n\n## Workflow history\n\n- 2026-01-01 created (aw specs): x\n"
    )


def _buckets(drift):
    """rule-scoped (bucket, path-name, field) tuples, parsed out of the reported detail."""
    out = []
    for d in drift:
        if d.rule != RULE:
            continue
        bucket = d.detail.split("]", 1)[0].lstrip("[")
        field = d.observed.split(":", 1)[0]
        out.append((bucket, Path(d.location).name, field))
    return out


# --------------------------------------------------------------------------------------------------
# E-05 / V-05: the seven required assertions. Each is a separate test because each names a DIFFERENT
# false-positive source measured on the live corpus, and a table row would hide which one regressed.
# --------------------------------------------------------------------------------------------------


class FourBucketTests(unittest.TestCase):
    def test_a_legacy_named_record_is_reported_with_a_resolvable_rename(self):
        """ASSERTION 1. The population the rule exists to count: a pre-id6-grammar name.

        The remedy is pinned too, not merely the finding, because the plan's F-10 is that a WRONG
        suggested command is worse than none. The selector must be the declared id6 rather than the
        filename: `aw rename plans <legacy-filename> --to-id6` refuses with "no plan has Id
        '<filename>'" (measured), while the id6 form resolves.
        """
        root = _tree()
        _write(
            root,
            EXECUTED,
            "20260808-0004-06-migrate-existing-plans.ipd.md",
            _plan("7qx7ys"),
        )
        # `include_retired=True` because the fixture is an `executed/` plan, which is where most of
        # this population actually lives. The DEFAULT scope deliberately excludes retired records
        # (AGENTS.md forbids editing a plan in `executed/`), which the scope test below pins.
        drift = ce.check_name_identity(root, include_retired=True)
        got = _buckets(drift)
        self.assertIn(
            ("legacy", "20260808-0004-06-migrate-existing-plans.ipd.md", "Id"),
            got,
            f"the legacy Id case must be reported as `legacy`; got {got!r}",
        )
        hints = [d.recovery for d in drift if d.rule == RULE and "Id:" in d.observed]
        self.assertEqual(
            hints,
            ["aw rename plans 7qx7ys --to-id6 --apply"],
            "the remedy must select the record by its DECLARED id6 (the filename form refuses) and "
            "name the `plans` type",
        )

    def test_a_conformant_modern_record_is_not_reported(self):
        """ASSERTION 2. THE POSITIVE CONTROL: every other row is vacuous while this one is broken.

        A rule that flagged everything would satisfy all six adversarial assertions below and be
        unusable, so this row is what makes them mean anything.
        """
        root = _tree()
        _write(
            root,
            PLANS,
            "20260101-demo-01-abc123-a-modern-plan.ipd.md",
            _plan("abc123", setid="demo"),
        )
        self.assertEqual(
            _buckets(ce.check_name_identity(root)),
            [],
            "a filename carrying both its declared Id and its declared Set must be silent",
        )

    def test_a_body_quoted_declaration_is_not_reported_as_a_naming_problem(self):
        """ASSERTION 3 (GUARD). The measured members are `27rjro`/`takpys` (research documents
        quoting a plan's front matter) and a SPEC quoting a frontmatter schema. All those filenames
        are CORRECT; the apparent mismatch is a READER bug (`cqytxf`, fixed by `76w6mq`). Reporting
        any of them as a rename target would send a maintainer to damage a correct name.
        """
        root = _tree()
        quoted = (
            "# Spec: the frontmatter schema\n\n- Date: 2026-01-01\n- Status: implemented\n"
            "- Set: realset\n- Id: aaa111\n\n## Schema\n\n```markdown\n"
            "- Set: quotedset\n- Id: zzz999\n```\n"
        )
        _write(root, SPECS, "20260101-realset-01-aaa111-schema.spec.md", quoted)
        got = _buckets(ce.check_name_identity(root))
        self.assertEqual(
            got,
            [],
            "the file's OWN declarations are both in its name, and the quoted block must not be "
            f"read as a second declaration; got {got!r}",
        )

    def test_a_quoted_declaration_outside_the_name_is_bucketed_artifact_and_never_a_rename(
        self,
    ):
        """ASSERTION 3b (GUARD, the live shape). When the quoted value is ALSO absent from the
        filename - which is the live `27rjro`/`takpys` shape, since the quoted plan is a different
        record entirely - the finding must be bucketed `artifact` and must offer NO rename.
        """
        root = _tree()
        body = (
            "---\nid: 27rjro\ncreated: 20260101\nset: realset\norder: 00\nkind: research-prompt\n"
            "status: reference\n---\n\n# Prompt\n\nExample of the metadata:\n\n```markdown\n"
            "- Set: runflags\n- Id: uyeko5\n```\n"
        )
        research = root / ".aw" / "records" / "research" / "reference" / "202601"
        research.mkdir(parents=True, exist_ok=True)
        (
            research / "20260101-realset-00-27rjro-a-prompt.research-prompt.md"
        ).write_text(body, encoding="utf-8")
        drift = [d for d in ce.check_name_identity(root) if d.rule == RULE]
        # The YAML envelope declares realset/27rjro, both in the name, so nothing from the METADATA
        # region is reported. Whatever IS reported must come from the quoted block and must be
        # bucketed `artifact` with no rename suggestion.
        for d in drift:
            bucket = d.detail.split("]", 1)[0].lstrip("[")
            self.assertEqual(
                bucket,
                "artifact",
                f"a quoted-block reading must bucket as `artifact`, not {bucket!r}: {d.detail}",
            )
            self.assertNotIn(
                "aw rename",
                d.recovery,
                "an artifact-bucket finding must never suggest a rename: the filename is correct",
            )

    def test_a_backtick_quoted_front_matter_value_produces_no_phantom(self):
        """ASSERTION 4 (GUARD). One live record declares ``- Set: `awoptimize` `` WITH BACKTICKS, and
        an un-normalized comparison invents drift on a correctly-named file. This is the phantom the
        plan's own audit hit once (F-9), so the normalization is pinned rather than trusted.
        """
        root = _tree()
        text = (
            "# Spec: x\n\n- Date: 2026-01-01\n- Status: reviewed\n- Set: `awoptimize`\n"
            "- Id: `abc123`\n\n## Workflow history\n\n- 2026-01-01 created (aw specs): x\n"
        )
        _write(root, SPECS, "20260101-awoptimize-01-abc123-x.spec.md", text)
        got = _buckets(ce.check_name_identity(root))
        self.assertEqual(
            got,
            [],
            f"a backtick-wrapped value must be compared STRIPPED, producing no finding; got {got!r}",
        )

    def test_genuine_drift_on_a_modern_name_is_reported_and_distinguished_from_legacy(
        self,
    ):
        """ASSERTION 5. A MODERN id6-clustered name whose metadata disagrees is a real defect, not a
        grandfathering question, so it must carry its own bucket. NONE was found on the live tree at
        authoring or at either review, which is why the class is proven from a fixture.
        """
        root = _tree()
        _write(
            root,
            PLANS,
            "20260101-wrongset-01-abc123-x.ipd.md",
            _plan("abc123", setid="realset"),
        )
        got = _buckets(ce.check_name_identity(root))
        self.assertEqual(
            got,
            [("drift", "20260101-wrongset-01-abc123-x.ipd.md", "Set")],
            f"a modern name whose Set segment disagrees must bucket as `drift`; got {got!r}",
        )

    def test_a_non_identifier_declared_value_produces_no_rename_suggestion(self):
        """ASSERTION 6 (GUARD). The measured member declares the literal `set: <terse-id>`, a
        documentation placeholder. No filename can satisfy it, so telling a maintainer to rename the
        spec to match `<terse-id>` would be nonsense.
        """
        root = _tree()
        text = (
            "# Spec: x\n\n- Date: 2026-01-01\n- Status: reviewed\n- Set: <terse-id>\n"
            "- Id: abc123\n\n## Workflow history\n\n- 2026-01-01 created (aw specs): x\n"
        )
        _write(root, SPECS, "20260101-real-01-abc123-x.spec.md", text)
        drift = [d for d in ce.check_name_identity(root) if d.rule == RULE]
        got = _buckets(drift)
        self.assertEqual(
            got,
            [("non-identifier", "20260101-real-01-abc123-x.spec.md", "Set")],
            f"a placeholder value must bucket as `non-identifier`; got {got!r}",
        )
        self.assertNotIn(
            "aw rename",
            drift[0].recovery,
            "no rename can satisfy a non-identifier value, so none may be suggested",
        )

    def test_a_legacy_slug_word_of_six_alphanumerics_buckets_as_legacy_not_drift(self):
        """ASSERTION 7 (GUARD). NOT hypothetical: `artifact_naming.parse_clustered` reports
        `20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md` as CONFORMANT with
        `id6='assess'`, and `_ID6_RE` accepts `assess` (six lowercase alphanumerics), so a comparator
        that trusted the parsed slot would call this legacy record MODERN and mis-bucket a real
        member of the exception set as genuine drift. The parse behavior is asserted here too, so the
        test states WHY the guard is needed rather than only that it works.
        """
        name = "20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md"
        m = naming.parse_clustered(name)
        self.assertIsNotNone(m, "the legacy name still parses as clustered (the trap)")
        assert m is not None
        self.assertEqual(
            m.group("id6"), "assess", "the parsed slot is the SLUG's first word"
        )
        self.assertTrue(ce._ID6_RE.match("assess"), "and it matches the id6 shape")

        root = _tree()
        _write(root, EXECUTED, name, _plan("wvlk84", setid="awphysical"))
        got = sorted(_buckets(ce.check_name_identity(root, include_retired=True)))
        self.assertEqual(
            got,
            [("legacy", name, "Id"), ("legacy", name, "Set")],
            f"both fields must bucket as `legacy`, never `drift`; got {got!r}",
        )


# --------------------------------------------------------------------------------------------------
# E-06 / V-06: the extend-versus-add decision and the REUSED discriminator.
# --------------------------------------------------------------------------------------------------


class DiscriminatorReuseTests(unittest.TestCase):
    """Kept separate from the bucket rows: the claim is about the SOURCE and the shared helper, not
    about any one tree."""

    def test_the_new_rule_sits_beside_the_identity_slot_rule_without_changing_it(self):
        """The existing `error`-severity rule must keep its severity and its legacy exemption: this
        plan ADDS a report and deliberately does not promote what the tree already tolerates."""
        slot = ce.RULE_REGISTRY[IDENTITY_SLOT]
        self.assertEqual(
            (slot.severity, slot.invariant),
            ("error", "I-09"),
            "the adjacent identity-slot rule must be untouched by this plan",
        )
        # And it genuinely does NOT cover the legacy population, which is what makes the gap real.
        root = _tree()
        _write(
            root,
            EXECUTED,
            "20260808-0004-06-migrate-existing-plans.ipd.md",
            _plan("7qx7ys", setid="plans-adopter"),
        )
        slot_findings = [
            d
            for d in ce.check_collisions(root, include_retired=True)
            if d.rule == IDENTITY_SLOT
        ]
        self.assertEqual(
            slot_findings,
            [],
            "a slot-less legacy name is exempt from the identity-slot rule BY CONSTRUCTION; that "
            "exemption is precisely the population this plan reports",
        )
        self.assertTrue(
            _buckets(ce.check_name_identity(root, include_retired=True)),
            "...and the new rule DOES cover it, which is the whole gap",
        )


# --------------------------------------------------------------------------------------------------
# E-04 / V-04: registration and the NO-ERROR-ADDED property.
# --------------------------------------------------------------------------------------------------


class AdvisoryRegistrationTests(unittest.TestCase):
    """Registry claims, not tree claims: an UNREGISTERED rule id falls back to `_DEFAULT_RULESPEC`
    (severity `error`), so registration is what makes the advisory posture real rather than stated."""

    def test_the_rule_is_registered_as_a_warning_following_the_review_dangling_precedent(
        self,
    ):
        spec = ce.RULE_REGISTRY.get(RULE)
        self.assertIsNotNone(spec, f"{RULE} is not in RULE_REGISTRY")
        assert spec is not None
        self.assertEqual(
            spec.severity,
            "warning",
            "`warning` is DELIBERATE: every member on this tree is grandfathered by decision "
            "(`executed/` plan bodies must not be re-committed; pre-cutover specs are "
            "grandfathered), so an `error` would fail the tree for states the maintainer CHOSE",
        )
        self.assertEqual(spec.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)
        self.assertEqual(
            spec.invariant, "I-09", "it belongs to the naming-grammar family"
        )
        # The precedent it follows, asserted so a future change to that rule is noticed here.
        self.assertEqual(ce.RULE_REGISTRY["check.review-dangling"].severity, "warning")

    def test_no_error_severity_finding_is_added(self):
        """THE PROPERTY F-7 REQUIRES, proven as a SEVERITY assertion.

        A live-tree exit-code comparison would be vacuous: `aw check all` already exits 1 with
        hundreds of findings, so "the exit code is unchanged" is satisfied no matter what this rule
        does. What actually matters is that no ERROR-severity finding is added, so the advisory could
        never turn an otherwise-green tree red.
        """
        root = _tree()
        _write(
            root,
            EXECUTED,
            "20260808-0004-06-migrate-existing-plans.ipd.md",
            _plan("7qx7ys"),
        )
        _write(
            root,
            SPECS,
            "20260101-real-01-abc123-x.spec.md",
            _spec("abc123", "<terse-id>"),
        )
        drift = ce.check_name_identity(root, include_retired=True)
        self.assertTrue(drift, "the fixture must actually produce findings")
        self.assertEqual(
            sorted({d.severity for d in drift}),
            ["warning"],
            "every finding this rule emits must be `warning`; a single `error` would let the "
            "advisory fail a tree that was otherwise clean",
        )

    def test_a_synthetic_tree_whose_only_finding_is_this_rule_still_fails_the_gate(
        self,
    ):
        """THE HONEST HALF, stated rather than papered over: `drift_exit_code` exempts ONLY `info`,
        so this `warning` DOES drive exit 1. The plan asked for a synthetic exit-0 proof; that
        premise is FALSE for `warning` in this codebase and asserting it would require registering
        the rule `info`, which would be the wrong contract (an unlocatable-by-name record is a real
        obligation to watch, not a nudge). What `warning` buys is documented in the two tests above
        (no error added) and below (no lifecycle gate consumes it). Recorded as DECISION 04-3i6rso-D1.
        """
        root = _tree()
        _write(
            root,
            EXECUTED,
            "20260808-0004-06-migrate-existing-plans.ipd.md",
            _plan("7qx7ys"),
        )
        drift = ce.check_name_identity(root, include_retired=True)
        self.assertEqual(
            core.drift_exit_code(drift),
            1,
            "a `warning` is loud: only `info` is exempt from the exit convention",
        )
        self.assertEqual(
            core.drift_exit_code([d._replace(severity="info") for d in drift]),
            0,
            "...and the exemption is genuinely severity-keyed, which is what makes the claim above "
            "a measurement rather than an assumption",
        )

    def test_the_rule_is_reached_by_the_full_sweep(self):
        """Placement (OQ-01): a SWEEP rule, so the count is on the surface agents and CI already run.
        A flag nobody runs would be close to not shipping a count whose purpose is to be watched."""
        root = _tree()
        _write(
            root,
            EXECUTED,
            "20260808-0004-06-migrate-existing-plans.ipd.md",
            _plan("7qx7ys"),
        )
        rules = {d.rule for d in ce.check_types(root, ["all"], include_retired=True)}
        self.assertIn(RULE, rules, "the full sweep must reach the advisory")


# --------------------------------------------------------------------------------------------------
# E-01 / V-01: the live count, as EVIDENCE.
# --------------------------------------------------------------------------------------------------


class ScopeAndOverlapTests(unittest.TestCase):
    """Kept separate from the bucket rows: these are claims about WHICH files the rule looks at and
    about its boundary with two adjacent rules, not about any one bucket."""

    def test_retirement_scope_is_honored_rather_than_overridden(self):
        """THE HONEST COST OF THE DEFAULT SCOPE, pinned so nobody is surprised by the count.

        Most of this population is RETIRED (`executed/` plans, terminal specs), so the DEFAULT scope
        reports the LIVE members only and the full historical count needs `--all`. Overriding the flag
        inside the rule was tried and rejected: retirement filters visibility for the whole engine
        because AGENTS.md forbids editing a plan in `executed/`, so a rule with private scope
        semantics would report findings whose remedy is not permitted on a narrowed scope.
        """
        root = _tree()
        _write(
            root,
            EXECUTED,
            "20260808-0004-06-migrate-existing-plans.ipd.md",
            _plan("7qx7ys"),
        )
        _write(
            root, PLANS, "20260101-1200-01-a-live-legacy-plan.ipd.md", _plan("lll111")
        )
        default = _buckets(ce.check_name_identity(root))
        widened = _buckets(ce.check_name_identity(root, include_retired=True))
        self.assertEqual(
            sorted({name for _b, name, _f in default}),
            ["20260101-1200-01-a-live-legacy-plan.ipd.md"],
            "the default scope must report the LIVE legacy record and not the retired one",
        )
        self.assertEqual(
            len(sorted({name for _b, name, _f in widened})),
            2,
            "`include_retired=True` must reach the retired member, which is where most of the real "
            "population lives",
        )

    def test_a_junk_filename_is_left_to_the_name_grammar_rule(self):
        """A name matching NO grammar is already `check.name-nonconformant`, whose remedy (rename to
        the grammar) SUBSUMES this advisory's. Double-reporting one authoring mistake under two rule
        ids is what `check.review-dangling` documents refusing for the same reason."""
        root = _tree()
        _write(root, PLANS, "not-a-grammar.md", _plan("bbb222"))
        self.assertTrue(
            [
                d
                for d in ce.check_names(root, "plans")
                if d.rule == "check.name-nonconformant"
            ],
            "the fixture must actually trip the grammar rule",
        )
        self.assertEqual(
            _buckets(ce.check_name_identity(root)),
            [],
            "the advisory must stay silent on a name the grammar rule already owns",
        )

    def test_a_modern_names_Id_half_is_left_to_the_identity_slot_rule(self):
        """A MODERN name whose slot id6 disagrees with its declared `- Id:` is
        `check.id6-identity-slot`'s subject at ERROR severity, and it names the owning file too. The
        advisory must not restate it under a weaker id; its contribution is the slot-LESS population
        plus the `Set` segment, which no rule checked at all.

        This also pins the classifier fix the overlap exposed: the slot token `slotaa` is nobody's
        declared id6, so the shared `_is_real_id6` returns False for it and a classifier consulting
        only that helper would call this MODERN name LEGACY and report it as grandfathered.
        """
        root = _tree()
        _write(
            root,
            PLANS,
            "20260101-demo-01-slotaa-a.ipd.md",
            _plan("fmbbb1", setid="demo"),
        )
        self.assertTrue(
            [d for d in ce.check_collisions(root) if d.rule == IDENTITY_SLOT],
            "the fixture must actually trip the identity-slot rule",
        )
        self.assertEqual(
            [b for b, _n, f in _buckets(ce.check_name_identity(root)) if f == "Id"],
            [],
            "the Id half of a modern name belongs to `check.id6-identity-slot`",
        )


class LiveCountEvidenceTests(unittest.TestCase):
    """The ONE live-tree test, and it asserts a BOUND rather than members.

    The count is this rule's deliverable, so recording it is the point; pinning the exact membership
    would make the test fail whenever `76w6mq` lands (removing the quoted-example readings) or an
    agent adds a record, which is drift in the corpus rather than a regression in the rule.
    """

    def test_the_exception_set_is_small_and_bucketed(self):
        repo = Path(__file__).resolve().parents[1]
        if not (repo / ".aw" / "records").is_dir():
            self.skipTest("not running inside the records tree")
        drift = ce.check_name_identity(repo, include_retired=True)
        buckets: dict = {}
        for bucket, _name, _field in _buckets(drift):
            buckets[bucket] = buckets.get(bucket, 0) + 1
        self.assertLessEqual(
            len(drift),
            60,
            "the exception set is expected to SHRINK, never to grow into the hundreds. MEASURED AT "
            "AUTHORING (full scope, `include_retired=True`): 13 findings over 11 records - 11 "
            "`legacy`, 1 `artifact`, 1 `non-identifier`, 0 `drift`. The DEFAULT scope reports 2, "
            "because most members are retired. Observed now: "
            f"{len(drift)} findings, {buckets!r}. If this bound is genuinely exceeded, the content "
            "fallback `aw find` keeps is load-bearing for far more records than anyone believed, and "
            "THAT is the finding rather than this assertion",
        )
        self.assertNotIn(
            "drift",
            buckets,
            "GENUINE DRIFT (a modern id6-clustered name disagreeing with its own metadata) is a real "
            "naming defect rather than a grandfathering question. None existed at authoring or at "
            f"either review; if one appears, fix the record. Measured now: {buckets!r}",
        )

    def test_no_correctly_named_record_is_offered_a_rename(self):
        """THE GUARD RESTATED AGAINST THE LIVE TREE, because this is the failure that would do real
        damage: a suggested `aw rename` on a file whose name is already right.

        Pinned as a PROPERTY rather than by member list: every finding that names a rename must be in
        a bucket whose name genuinely cannot be located by its identity (`legacy` or `drift`), and no
        `artifact` or `non-identifier` finding may carry one. The three measured artifact-class
        records (`27rjro`, `takpys`, and the `agents-artifact-organization` spec) all have CORRECT
        filenames, so a rename suggestion on any of them would be manufactured damage.
        """
        repo = Path(__file__).resolve().parents[1]
        if not (repo / ".aw" / "records").is_dir():
            self.skipTest("not running inside the records tree")
        offenders = []
        for d in ce.check_name_identity(repo, include_retired=True):
            if d.rule != RULE:
                continue
            bucket = d.detail.split("]", 1)[0].lstrip("[")
            if "aw rename" in d.recovery or "aw group" in d.recovery:
                if bucket not in ("legacy", "drift"):
                    offenders.append((bucket, Path(d.location).name, d.recovery))
        self.assertEqual(
            offenders,
            [],
            "a rename was suggested for a record whose filename is CORRECT; that is worse than no "
            f"report at all: {offenders!r}",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
