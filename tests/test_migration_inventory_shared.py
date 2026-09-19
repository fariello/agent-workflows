"""Tests for awoptimize Order 14 (`h1d5aa`): migration disposition inventory + shared families.

Covers the E-04 acceptance:
  * E-01: the completeness tool proves EVERY manifest row (command + lens + persona) and the
    non-invokable conformance package has EXACTLY ONE reviewed disposition + a valid canonical
    target, with ZERO silent omissions, and aliases distinguishable from independent workflows.
    Falsifiable: injecting an omission / a duplicate / an invalid target / an alias-that-targets-
    itself each makes a named assertion fail.
  * E-02: every assess lens resolves through the ONE assess harness and every advise persona through
    the ONE advise harness; a lens/persona that forks the harness lifecycle/evidence is REJECTED;
    the rollup requires explicit scope/cost confirmation and de-duplicates its members.
  * E-03: `plan-review` and `plan-review-long` compile from ONE package, share the semantic digest +
    arguments, both names are aliases, and a mutation of EITHER generated view is detected as drift.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: take the inventory
built from the LIVE manifest, mutate exactly one disposition, and assert one named finding. The
tables group by SUBJECT (the detection vocabulary, the two harness families, the two generated
views) rather than by which E-item of the plan introduced the behavior, which is what the class
boundaries used to track.

WHERE A DISTINCTION IS A MODE IT IS A COLUMN. The three that carry the weight here:

  * MUTATION. `check_completeness` is a report-everything-at-once function whose whole value is that
    each defect produces its OWN named finding. Tested one defect per test, a refactor that collapsed
    two causes onto one message would leave both tests green because each only asserts a substring of
    the finding it expects. The table therefore asserts each row's finding IS present AND that the
    row produced exactly the finding count it should, so a collapse fails on the count.
  * FAMILY (`assess`/lens versus `advise`/persona). The two registries are built by two functions
    over the same `HarnessRegistry` type and the load-bearing property is that each family resolves
    through ONE harness whose semantic digest is shared by every member. A class per family cannot
    state that the two digests DIFFER while each family's is internally constant, which is exactly
    the shape a copy-paste of `build_assess_harness` would break.
  * VIEW (`single_file` versus `long`). Drift detection is per-view by construction, so the property
    worth asserting is that mutating one view moves ITS digest and leaves the OTHER's alone. One test
    per view asserts only half of that and would pass a `view_digest` that ignored its argument.

THE POSITIVE ROWS SHARE THE TABLES WITH THE NEGATIVE ONES, deliberately. The inventory checker is a
gate, so both degenerate directions are catastrophic and each is invisible to one half of a table: a
checker that reported nothing satisfies the clean row while removing the gate, and one that reported
everything satisfies every detection row while making the live inventory permanently red. Each
failure message says which direction broke, and says that the negative rows are VACUOUS while a
positive one is broken.

TESTS THAT ARE NOT ROWS CARRY A ONE-LINE DOCSTRING SAYING WHY. The recurring reasons: the assertion
is an `assertRaises` (no record exists to read back, so there is nothing to tabulate); the claim is
STRUCTURAL (a set membership, a count over the live manifest); or the subject is TWO results COMPARED
to each other rather than to a fixed expectation (a recompile against the first compile).

Stdlib `unittest`, matching the repository convention.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import unittest
from pathlib import Path

from agent_workflows import engine
from agent_workflows import migration_inventory as MI
from agent_workflows import workflow_loader as LOADER
from tests.support import SOURCE_WORKFLOWS

FIXTURE_PKG = (
    Path(__file__).resolve().parent / "fixtures" / "workflow-src" / "plan-review"
)


# ==================================================================================================
# E-01: disposition inventory + completeness tool
# ==================================================================================================


class InventoryCompletenessTests(unittest.TestCase):
    """Every way the inventory can be wrong, each keeping its OWN row and its OWN named finding.

    ONE table replaces six tests (`test_inventory_is_complete_and_valid`,
    `test_detects_silent_omission`, `test_detects_disposition_for_nonexistent_row`,
    `test_detects_alias_targeting_own_id`, `test_detects_invalid_vocabulary`, and
    `test_order14_ownership_fence_detects_out_of_scope_claim`). Each had the identical shape: take the
    inventory built from the LIVE manifest, mutate exactly one disposition, call `check_completeness`,
    and assert one substring appears among the findings.

    WHY THE TABLE BEATS THE SIX. `check_completeness` is a report-EVERYTHING-at-once function: its
    docstring enumerates six numbered checks and its contract is that each defect yields its own
    named finding rather than aborting on the first. Six tests each asserting `any(substring in f)`
    cannot see the failure that actually threatens such a function, which is two causes COLLAPSING
    onto one message (or one cause firing for an unrelated mutation): every test still finds its
    substring somewhere in a longer list. The table asserts each row's finding AND the row's exact
    finding COUNT, so a collapse or a spurious extra finding fails on the count. It also makes the
    detection vocabulary browsable as a set, which is what a person adding a seventh check needs.

    THE CLEAN ROW IS IN THE SAME TABLE and it carries real weight: a checker that reported findings
    for everything would satisfy every detection row on its own. Its failure message says the
    detection rows are vacuous while it is broken.

    TWO ROWS PIN MORE THAN THE TESTS THEY REPLACE. The alias row now asserts BOTH findings the
    self-targeting alias produces (the row-level `Disposition.validate` complaint AND the
    inventory-level alias complaint), where the old test asserted only the second, so a validator that
    stopped policing the field while the inventory check still fired would now fail. And the
    dangling-target case gets TWO rows (alias versus independent workflow), because
    `check_completeness` reaches them through different branches and the old suite exercised neither.
    """

    #: Named mutations, applied to a COPY of the live inventory before the row runs. Kept as names
    #: rather than lambdas in the rows so the table reads as data.
    def _mutate(self, dispositions: dict, mutation) -> dict:
        out = dict(dispositions)
        if mutation is None:
            return out
        kind, arg = mutation
        if kind == "delete":
            del out[arg]
        elif kind == "ghost":
            out[arg] = dataclasses.replace(out["setup-repo"], subject=arg)
        elif kind == "field":
            subject, field, value = arg
            out[subject] = dataclasses.replace(out[subject], **{field: value})
        else:  # pragma: no cover - a typo in the table itself
            raise AssertionError(f"unknown mutation kind {kind!r}")
        return out

    #: (case, the mutation to apply or None, the findings that MUST each appear as a substring, the
    #: EXACT number of findings expected, why this row exists)
    MUTATIONS = (
        (
            "the live inventory, unmutated",
            None,
            (),
            0,
            "THE POSITIVE ROW: the shipped manifest plus the shipped disposition table must check "
            "CLEAN. Every detection row below is vacuous while this one is broken, because a checker "
            "that reported a finding for everything satisfies all of them",
        ),
        (
            "a disposition DELETED for a real manifest row",
            ("delete", "setup-repo"),
            ("subject 'setup-repo' has NO disposition (silent omission)",),
            1,
            "THE SILENT OMISSION, which is the defect the whole tool exists to make impossible: a "
            "command nobody dispositioned is a command nobody decided about, and it migrates by "
            "accident or not at all. Note the count is 1: an omission must not ALSO trip the "
            "canonical-target checks, or a single mistake would report as several unrelated ones",
        ),
        (
            "a disposition for a subject that is no manifest row",
            ("ghost", "ghost-workflow"),
            (
                "disposition 'ghost-workflow' does not correspond to any manifest row or "
                "conformance file",
            ),
            1,
            "THE INVERSE OMISSION, and it is not symmetric with the one above: an extra row is how a "
            "command that was RENAMED or REMOVED upstream leaves a stale decision behind, which reads "
            "as coverage while covering nothing that exists",
        ),
        (
            "a disposition carrying an out-of-vocabulary execution_mode",
            ("field", ("setup-repo", "execution_mode", "bogus-mode")),
            ("disposition 'setup-repo': bad execution_mode 'bogus-mode'",),
            1,
            "the disposition fields are CLOSED vocabularies, and `execution_mode` is the one a "
            "consumer branches on. An unpoliced value is usually a typo in a real mode, and a typo'd "
            "mode is a subject whose migration route nothing can read. The finding is asserted with "
            "its SUBJECT prefix, because a vocabulary complaint that cannot say WHICH row it is about "
            "sends a reader through 64 of them",
        ),
        (
            "an ALIAS whose canonical target is its own id",
            ("field", ("plan-review-long", "canonical_package", "plan-review-long")),
            (
                "disposition 'plan-review-long': alias must not target its own subject id",
                "alias 'plan-review-long' targets its own id (not distinguishable from an "
                "independent workflow)",
            ),
            2,
            "AN ALIAS MUST BE DISTINGUISHABLE FROM AN INDEPENDENT WORKFLOW, which is the whole "
            "content of `is_alias`: an alias pointing at itself claims to be its own canonical "
            "package, and the plan-review collapse (two names, ONE package) is then unprovable. BOTH "
            "findings are asserted deliberately, where the old test asserted only the second: the "
            "rule is enforced twice, once per-row in `Disposition.validate` and once across the "
            "inventory, so a validator that stopped policing the field would still pass a "
            "single-finding assertion",
        ),
        (
            "an ALIAS targeting a canonical package that does not exist",
            ("field", ("plan-review-long", "canonical_package", "no-such-package")),
            (
                "alias 'plan-review-long' targets unknown canonical package 'no-such-package'",
            ),
            1,
            "A DANGLING TARGET IS A BROKEN HANDOFF, exactly as `check.from-backlog-dangling` treats "
            "one in the records tree. Neither this row nor the next existed in the old suite, and "
            "they are SEPARATE rows because `check_completeness` reaches them through different "
            "branches of its alias test, so one could break while the other held",
        ),
        (
            "an INDEPENDENT workflow resolving to a package that does not exist",
            ("field", ("setup-repo", "canonical_package", "no-such-package")),
            ("'setup-repo' resolves to unknown canonical package 'no-such-package'",),
            1,
            "the non-alias half of the same rule, and the message deliberately DIFFERS from the alias "
            "one: an independent workflow must target its OWN dispositioned id, so this finding says "
            "'resolves to' rather than 'targets', and a reader can tell which kind of subject is "
            "broken from the message alone",
        ),
        (
            "an Order-16 family claiming Order-14 ownership",
            ("field", ("scaffold", "migration_owner", "order-14")),
            (
                "'scaffold' claims migration_owner order-14 but family 'scaffold' is out of "
                "Order-14 scope",
            ),
            1,
            "THE SCOPE FENCE, which is what keeps this Order honest about what it migrated: Order 14 "
            "owns the shared assess/advise families and the plan-review aliases and NOTHING else, so "
            "a row claiming order-14 ownership for `scaffold` claims work this Order did not do. A "
            "fence that stops firing is how a plan comes to report coverage it never delivered",
        ),
    )

    def setUp(self):
        self.result = MI.build_inventory(SOURCE_WORKFLOWS)
        self.workflows = engine.parse_manifest(Path(SOURCE_WORKFLOWS))

    def test_every_inventory_defect_produces_its_own_named_finding(self):
        wrong = []
        positive_rows_broken = 0
        for case, mutation, needles, count, why in self.MUTATIONS:
            dispositions = self._mutate(self.result.dispositions, mutation)
            findings = MI.check_completeness(
                dispositions, self.workflows, SOURCE_WORKFLOWS
            )
            problems = []
            for needle in needles:
                if not any(needle in f for f in findings):
                    problems.append(
                        f"no finding contains {needle!r}; the checker reported "
                        f"{findings or 'NOTHING AT ALL (it checked clean)'}"
                    )
            if len(findings) != count:
                problems.append(
                    f"expected EXACTLY {count} finding(s), got {len(findings)}: {findings!r}"
                )
            if problems:
                if mutation is None:
                    positive_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                " THE UNMUTATED ROW IS AMONG THE FAILURES, and while it is broken every detection "
                "row here is VACUOUS: a checker that reports a finding for everything satisfies all "
                "of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"`check_completeness` mishandled {len(wrong)} of {len(self.MUTATIONS)} inventory "
            f"mutations.{vacuity} This function's contract is that it reports EVERY defect at once, "
            "each with its OWN named finding, so SEVERAL ROWS FAILING ON THE COUNT usually means two "
            "causes COLLAPSED onto one message or one cause started firing for an unrelated "
            "mutation: read the reported finding lists side by side before touching individual "
            "checks. FIX: a row reporting NOTHING AT ALL is the worst outcome here, because a check "
            "that stopped firing lets an undispositioned command, a stale decision, or a "
            "self-targeting alias through the very tool that exists to prove the migration is "
            f"complete.\n" + "\n".join(wrong),
        )

    #: (case, the predicate over the built `InventoryResult`, the expected value, why this row
    #: exists). The predicates read the LIVE inventory rather than a mutation, so they are shapes of
    #: the shipped table rather than detections.
    def test_the_live_inventorys_shape_is_what_the_plan_claims(self):
        """ONE table replaces three tests about the shipped inventory's own shape.

        `test_every_manifest_row_dispositioned_exactly_once`,
        `test_conformance_package_dispositioned_once_as_non_invokable`, and
        `test_lenses_and_personas_present` all asked the SAME built result for a count or a field.
        They are rows rather than three tests because together they state one property that none of
        them states alone: the inventory covers the manifest EXACTLY once plus the one non-invokable
        conformance subject, and every catalog subject routes to its family's ONE harness. A count
        drifting in one kind while another absorbs it is invisible test by test and obvious here.
        """
        commands = [w.command for w in self.workflows]
        dispositions = self.result.dispositions
        lenses = [d for d in dispositions.values() if d.kind == "lens"]
        personas = [d for d in dispositions.values() if d.kind == "persona"]
        conformance = dispositions.get(MI.CONFORMANCE_TARGET)

        #: (case, actual, expected, why this row exists)
        shape = (
            (
                "the manifest names no command twice",
                len(commands),
                len(set(commands)),
                "every later count rests on this: a duplicated command row would be dispositioned "
                "once and counted twice, so the totals below would agree while a subject went "
                "undecided",
            ),
            (
                "every manifest command has a disposition",
                sorted(c for c in commands if c not in dispositions),
                [],
                "ZERO SILENT OMISSIONS is the E-01 acceptance, asserted over the LIVE manifest "
                "rather than a fixture, so adding a workflow without dispositioning it fails here",
            ),
            (
                "the inventory is the manifest PLUS the conformance package",
                len(dispositions),
                len(commands) + 1,
                "the `+ 1` is the load-bearing part: the conformance package is NOT a manifest row "
                "(it is non-invokable) yet it must be dispositioned, so an equality here proves both "
                "that nothing was dropped and that nothing extra was invented",
            ),
            (
                "the conformance subject's kind",
                conformance.kind if conformance else None,
                "conformance",
                "it is its own kind rather than a `command`, which is what keeps it out of every "
                "consumer that enumerates invokable commands",
            ),
            (
                "the conformance subject's execution mode",
                conformance.execution_mode if conformance else None,
                "non-invokable",
                "NON-INVOKABLE IS THE WHOLE POINT: a conformance package is read by an operator and "
                "never dispatched, so a mode that made it look runnable would put a non-command into "
                "a command surface",
            ),
            (
                "every lens routes to the ONE assess package",
                sorted({d.canonical_package for d in lenses}),
                ["assess"],
                "a lens with its own canonical package is a FORK of the shared harness, which is the "
                "defect E-02 exists to prevent. Asserted as the SET of targets so one stray lens "
                "cannot hide behind thirty correct ones",
            ),
            (
                "every persona routes to the ONE advise package",
                sorted({d.canonical_package for d in personas}),
                ["advise"],
                "the persona half of the same rule. Both families need a row because they are built "
                "by two separate functions over one type, so one could fork while the other held",
            ),
            (
                "the persona count is the documented seven",
                len(personas),
                7,
                "the personas are a CLOSED set named in the plan (an eighth would need its own "
                "reviewed disposition), unlike the lenses whose catalog legitimately grows, which is "
                "why this is an equality and the lens count below is a floor",
            ),
        )
        wrong = []
        for case, actual, expected, why in shape:
            if actual != expected:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected {expected!r}, got {actual!r}\n"
                    f"    this row exists because: {why}"
                )
        if len(lenses) < 30:
            wrong.append(
                f"  the lens catalog is at least 30 lenses:\n"
                f"    - expected >= 30, got {len(lenses)}\n"
                f"    this row exists because: the catalog is allowed to GROW, so this is a floor "
                f"rather than an equality; a collapse below it means lens rows stopped being "
                f"classified as lenses and were silently counted as commands"
            )
        self.assertEqual(
            wrong,
            [],
            f"the shipped inventory's shape is wrong in {len(wrong)} of {len(shape) + 1} respects. "
            "These rows are counts over the LIVE manifest, so SEVERAL FAILING TOGETHER almost always "
            "means one classification moved rather than several independent errors: check "
            "`enumerate_subjects` and `engine.is_concern_catalog_row` first, since a subject "
            "misclassified there is simultaneously missing from one kind and surplus in another. "
            "FIX: if a workflow was legitimately added, disposition it in the table rather than "
            f"relaxing these numbers.\n" + "\n".join(wrong),
        )

    def test_the_agent_report_is_machine_readable_json(self):
        """Kept separate: the subject is the CLI-facing report string, not a `check_completeness` result.

        Every row above reads a `Disposition` or a findings list in process; this is the only guard
        that the pasteable evidence surface is parseable JSON and that its count agrees with the
        inventory it claims to describe.
        """
        obj = json.loads(MI.render_agent_report(SOURCE_WORKFLOWS))
        self.assertTrue(obj["ok"], obj.get("findings"))
        self.assertEqual(obj["count"], len(self.result.dispositions))

    def test_an_alias_is_distinguishable_from_an_independent_workflow(self):
        """Kept separate: the claim is about the shipped alias SET, not a per-row expectation.

        The table above proves a MALFORMED alias is detected; this proves the live inventory actually
        contains the two aliases the plan names and that no alias targets its own id, which is the
        property the detection row would be vacuous without.
        """
        aliases = {s for s, d in self.result.dispositions.items() if d.is_alias}
        self.assertIn("plan-review-long", aliases)
        self.assertIn("release-review-plan", aliases)
        for subject in sorted(aliases):
            self.assertNotEqual(
                self.result.dispositions[subject].canonical_package, subject
            )
        independent = self.result.dispositions["setup-repo"]
        self.assertFalse(independent.is_alias)
        self.assertEqual(independent.canonical_package, "setup-repo")


# ==================================================================================================
# E-02: shared assess/advise harness resolution + no-fork parity + rollup
# ==================================================================================================


class SharedHarnessTests(unittest.TestCase):
    """ONE harness per family, with the FAMILY as a column rather than a second class.

    ONE table replaces four tests (`test_every_lens_resolves_through_one_harness`,
    `test_every_persona_resolves_through_one_harness`, `test_catalog_rows_all_bound_to_one_digest`,
    `test_clean_lens_contribution_has_no_reserved_keys`). All four walked a registry's members,
    resolved each, and asserted the harness id or the digest; they differed only in WHICH registry.

    WHY THE FAMILY IS A COLUMN. `build_assess_harness` and `build_advise_harness` are two functions
    over ONE `HarnessRegistry` type, which is precisely the shape a copy-paste divergence takes. The
    property worth asserting is that each family's digest is internally CONSTANT across every member
    AND that the two families' digests DIFFER. A class per family can state the first and cannot
    state the second, so a harness builder that returned the assess IR for advise would pass both old
    tests: every advise member would still agree with every other advise member.

    WHAT MAKES THE TWO DIGESTS DIFFER, measured rather than assumed, because the cross-family row is
    only meaningful if something really separates them. `semantic_digest` moves with the harness IR's
    `id` AND with its `interaction` (`assess` is `optional`, `advise` is `interactive`); it does NOT
    move with the IR's `summary`, its `intent`, or the IR-level `digest` field, so neither of those is
    load-bearing here. Two fields therefore separate the families, which is also why the cross-family
    check is stated as "the digests must differ" rather than pinned to either field: a future change
    that stopped one field mattering would still leave the property true, while a builder handing the
    wrong IR over breaks it.

    WHAT THE TABLE PINS PER FAMILY, all in one pass over the members: the resolved harness id, that
    the resolved member is the one asked for (not merely SOME member), that the digest is the same
    object value for every member, that the generated catalog rows all carry that same digest, and
    that no member's contribution touches a harness-reserved key. The last is the no-fork invariant
    from the READ side; its refusal side stays in the `assertRaises` tests below.
    """

    def setUp(self):
        self.assess = MI.build_assess_harness(SOURCE_WORKFLOWS)
        self.advise = MI.build_advise_harness(SOURCE_WORKFLOWS)

    #: (case, the registry attribute, the expected harness id, the member-map attribute, the resolver
    #: method name, the expected member field carrying the member's own id, the minimum member count,
    #: why this row exists)
    FAMILIES = (
        (
            "every assess LENS",
            "assess",
            "assess",
            "lenses",
            "resolve_lens",
            "concern",
            30,
            "THE LENS FAMILY, whose catalog is the large one (thirty-odd concerns) and therefore the "
            "one where a single forked member hides most easily. The member count is a FLOOR because "
            "the catalog legitimately grows",
        ),
        (
            "every advise PERSONA",
            "advise",
            "advise",
            "personas",
            "resolve_persona",
            "persona",
            7,
            "THE PERSONA FAMILY, built by a SECOND function over the same registry type, which is "
            "exactly where a copy-paste divergence lands. Without this row the assess assertions "
            "would all pass on a builder that handed advise the assess harness, because every advise "
            "member would still agree with every other advise member",
        ),
    )

    def test_each_family_resolves_every_member_through_its_ONE_harness(self):
        wrong = []
        digests = {}
        for (
            case,
            attribute,
            harness_id,
            member_attr,
            resolver,
            id_field,
            minimum,
            why,
        ) in self.FAMILIES:
            registry = getattr(self, attribute)
            members = getattr(registry, member_attr)
            resolve = getattr(registry, resolver)
            problems = []
            if len(members) < minimum:
                problems.append(
                    f"expected at least {minimum} member(s), found {len(members)}"
                )
            seen_digests = set()
            for member in sorted(members):
                got_id, module = resolve(member)
                if got_id != harness_id:
                    problems.append(
                        f"member {member!r} resolved to harness {got_id!r}, not {harness_id!r}"
                    )
                if getattr(module, id_field) != member:
                    problems.append(
                        f"resolving {member!r} returned the module for "
                        f"{getattr(module, id_field)!r}"
                    )
                reserved = sorted(set(module.contribution()) & MI.HARNESS_RESERVED_KEYS)
                if reserved:
                    problems.append(
                        f"member {member!r} contributes harness-reserved key(s) {reserved!r}, "
                        "which forks the lifecycle/evidence contract"
                    )
                seen_digests.add(registry.harness.semantic_digest())
            if len(seen_digests) != 1:
                problems.append(
                    f"the family must have ONE semantic digest across every member; saw "
                    f"{len(seen_digests)}: {sorted(seen_digests)!r}"
                )
            rows = registry.catalog_rows()
            if len(rows) != len(members):
                problems.append(
                    f"expected one catalog row per member ({len(members)}), got {len(rows)}"
                )
            row_digests = sorted({r["semantic_digest"] for r in rows})
            if row_digests != sorted(seen_digests):
                problems.append(
                    f"the generated catalog rows carry digest(s) {row_digests!r}, which is not the "
                    f"harness's own {sorted(seen_digests)!r}, so a row can drift from the harness"
                )
            digests[case] = sorted(seen_digests)
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        distinct = {tuple(v) for v in digests.values()}
        if len(distinct) != len(digests):
            wrong.append(
                "  the two families must NOT share one semantic digest:\n"
                f"    - got {digests!r}\n"
                "    this row exists because: `assess` and `advise` compile DIFFERENT IR (optional "
                "versus interactive interaction), so an identical digest means one builder handed "
                "the other family's harness over and every per-family assertion above passed "
                "vacuously"
            )
        self.assertEqual(
            wrong,
            [],
            f"harness resolution is broken for {len(wrong)} of {len(self.FAMILIES)} families (plus "
            "the cross-family digest check). BOTH FAMILIES FAILING TOGETHER points at the shared "
            "`HarnessRegistry`/`SharedHarness` code or at `_harness_ir`, while ONE family failing "
            "alone points at that family's builder. FIX: a member contributing a reserved key is the "
            "most serious row here, because a lens that carries its own `lifecycle` or `evidence` no "
            "longer shares the contract the whole family is reviewed against, and the shared digest "
            f"then attests to a contract that member is not following.\n"
            + "\n".join(wrong),
        )

    def test_a_contribution_redefining_a_reserved_key_is_refused(self):
        """Kept separate: an `assertRaises` test. There is no record to read back, only a raise.

        Every reserved key gets its own subTest because `HARNESS_RESERVED_KEYS` is a closed set that
        `assert_no_lens_fork` iterates, so a key silently dropped from the set stops being policed
        without any other test noticing.
        """
        for key in sorted(MI.HARNESS_RESERVED_KEYS):
            with self.subTest(reserved_key=key):
                with self.assertRaises(MI.HarnessForkError):
                    MI.assert_no_lens_fork({key: "override"})

    def test_registering_a_forking_lens_is_refused_at_REGISTRATION_time(self):
        """Kept separate: an `assertRaises`, and the setup is materially different (a subclass).

        The test above proves the PREDICATE refuses a reserved key; this proves the predicate is
        actually ON the registration path, so a lens whose `contribution()` forks cannot enter the
        registry at all. A lens that forked only when read would already be in the catalog.
        """

        class _ForkingLens(MI.LensModule):
            def contribution(self):  # type: ignore[override]
                base = dict(super().contribution())
                base["evidence"] = ["command"]  # attempt to fork the evidence contract
                return base

        fork = _ForkingLens(concern="rogue", lens_body="x", rubric_focus="y")
        with self.assertRaises(MI.HarnessForkError):
            self.assess.register_lens(fork)

    #: (case, the requested member list (None = all lenses), the expected member tuple, or None to
    #: compare against the LIVE lens catalog, the expected cost or None for the same reason, why this
    #: row exists)
    #:
    #: EVERY ROW HERE IS A CONFIRMED ROLLUP THAT MUST SUCCEED. The two refusal cases (unconfirmed, and
    #: an unknown member) are `assertRaises` tests below and are deliberately NOT rows: there is no
    #: returned record to read back, so a row for one would carry empty member and cost columns and
    #: would assert a different KIND of thing than its neighbours.
    ROLLUPS = (
        (
            "two distinct lenses",
            ["security", "bugs"],
            ("security", "bugs"),
            2,
            "THE BASELINE ROW, and it pins ORDER: members come back FIRST-SEEN, not sorted, so a "
            "caller can show the user the same sequence it was given. `security` before `bugs` is "
            "not alphabetical, which is what makes this row able to detect a sort creeping in",
        ),
        (
            "the same two lenses requested TWICE each",
            ["security", "security", "bugs", "bugs"],
            ("security", "bugs"),
            2,
            "DE-DUPLICATION IS A COST CONTROL, not tidiness: the cost the user confirmed is "
            "`len(members) * cost_per_member`, so a duplicate that survived would bill (and run) a "
            "lens twice while the confirmation said once. The COST column is what makes this row "
            "falsifiable rather than a set comparison",
        ),
        (
            "no member list at all (None)",
            None,
            None,
            None,
            "`None` MEANS ALL, which is the `assess-all` entry point. Expanded from the LIVE lens "
            "catalog rather than a frozen list, so adding a lens does not silently shrink what "
            "`assess-all` covers",
        ),
    )

    def test_a_confirmed_rollup_resolves_its_members_and_quotes_their_cost(self):
        wrong = []
        for case, requested, members, cost, why in self.ROLLUPS:
            problems = []
            plan = MI.plan_rollup(self.assess, requested, confirmed=True)
            expected_members = (
                tuple(sorted(self.assess.lenses)) if members is None else members
            )
            expected_cost = len(self.assess.lenses) if cost is None else cost
            if requested is None:
                # `None` means ALL, compared as a SET because the catalog's order is its own.
                if set(plan.members) != set(self.assess.lenses):
                    problems.append(
                        f"expected every live lens ({len(self.assess.lenses)}), got "
                        f"{len(plan.members)}; missing "
                        f"{sorted(set(self.assess.lenses) - set(plan.members))!r}"
                    )
            elif plan.members != expected_members:
                problems.append(
                    f"expected members {expected_members!r}, got {plan.members!r}"
                )
            if plan.estimated_cost_units != expected_cost:
                problems.append(
                    f"expected cost {expected_cost}, got {plan.estimated_cost_units}; the cost is "
                    f"what the user confirmed, so it must equal the RESOLVED member count "
                    f"({len(plan.members)})"
                )
            if not plan.confirmed:
                problems.append(
                    "the returned plan says `confirmed=False`, so a consumer cannot tell a gated "
                    "rollup from an ungated one"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`plan_rollup` resolved {len(wrong)} of {len(self.ROLLUPS)} confirmed rollups wrongly. "
            "The member set and the cost are ONE fact here (`cost == len(members) * "
            "cost_per_member`), so a MEMBER row and a COST row failing together is one bug in "
            "resolution rather than two. FIX: the cost is the number the user was shown before "
            "consenting, so a member set that resolves to more members than the quote covers spends "
            f"turns nobody approved.\n" + "\n".join(wrong),
        )

    def test_an_unconfirmed_rollup_is_refused(self):
        """Kept separate: an `assertRaises` test. No plan is returned, so there is nothing to tabulate.

        THE CONFIRMATION GATE: a rollup fans out one model turn per member, so it must never start
        without the user having seen the scope AND the cost. This is what makes `confirmed` a gate
        rather than a field, and it is the row the table above would be vacuous without, since a
        `plan_rollup` that ignored `confirmed` would satisfy every row there.
        """
        with self.assertRaises(MI.RollupConfirmationError):
            MI.plan_rollup(self.assess, ["security", "bugs"])

    def test_a_rollup_naming_an_unknown_lens_is_refused(self):
        """Kept separate: an `assertRaises` test, and its claim is about ORDERING, not a member set.

        An unknown member is refused BEFORE a cost is quoted, which is the part that matters: a
        typo'd lens name must not silently reduce the fan-out to the members that happened to parse,
        because the user would then confirm a scope smaller than the one they asked for and never be
        told.
        """
        with self.assertRaises(MI.InventoryError):
            MI.plan_rollup(self.assess, ["no-such-lens"], confirmed=True)


# ==================================================================================================
# E-03: plan-review one source -> two views -> parity + drift detection
# ==================================================================================================


class PlanReviewCollapseTests(unittest.TestCase):
    """TWO generated views of ONE package, with the VIEW as a column rather than a second test.

    ONE table replaces three tests (`test_mutation_of_single_file_view_detected_as_drift`,
    `test_mutation_of_long_view_detected_as_drift`, `test_identical_views_show_no_drift`). Each
    deep-copied the compiled views, tampered with one of them (or with neither), and asserted
    `detect_view_drift`.

    WHY THE VIEW IS A COLUMN. Drift detection is per-view BY CONSTRUCTION: `view_digest` selects a
    blob by name. So the property worth asserting is two-sided - mutating a view moves ITS digest AND
    LEAVES THE OTHER'S ALONE - and each old test asserted only one side. A `view_digest` that ignored
    its argument and hashed both views together would pass both drift tests and the no-drift test:
    every mutation would be detected, just attributed to both views at once, which is precisely the
    bug that makes drift detection useless for telling a reviewer WHICH generated view was tampered
    with. Each row here names the view it mutated and asserts the other view reports NO drift.

    THE UNTAMPERED ROW IS IN THE SAME TABLE and carries the usual weight: a detector that always
    reported drift would satisfy both mutation rows while making every legitimate recompile look
    tampered, and the digest parity it exists to prove would be unassertable.
    """

    def setUp(self):
        self.views = MI.compile_plan_review(FIXTURE_PKG)

    #: Named tampering recipes, applied to a deep copy of the compiled views. Kept as names rather
    #: than lambdas in the rows so the table reads as data. `PlanReviewViews` is a frozen dataclass,
    #: so a real tamperer's only route is `object.__setattr__`, which is what these use.
    def _tamper(self, views, recipe):
        mutated = copy.deepcopy(views)
        if recipe is None:
            return mutated
        if recipe == "single_file":
            object.__setattr__(
                mutated, "single_file", views.single_file + "\n<!-- tampered -->\n"
            )
        elif recipe == "long":
            packets = [dict(p) for p in copy.deepcopy(views.long)]
            packets[0]["action"] = packets[0]["action"] + " TAMPERED"
            object.__setattr__(mutated, "long", tuple(packets))
        else:  # pragma: no cover - a typo in the table itself
            raise AssertionError(f"unknown tampering recipe {recipe!r}")
        return mutated

    #: (case, the view to tamper with (None = tamper with nothing), the views that MUST report drift,
    #: the views that must report NO drift, why this row exists)
    DRIFTS = (
        (
            "nothing tampered with",
            None,
            (),
            ("single_file", "long"),
            "THE POSITIVE ROW: a deep copy of an untouched compile must show NO drift in EITHER "
            "view. Both mutation rows below are vacuous while this is broken, because a detector "
            "that always reported drift satisfies them both and makes every legitimate recompile "
            "look tampered",
        ),
        (
            "a comment appended to the SINGLE-FILE view",
            "single_file",
            ("single_file",),
            ("long",),
            "the portable single-file bundle is what a human copies into a prompt, so a silent edit "
            "to it changes what the workflow actually instructs while the semantic digest still "
            "attests to the source package. The `long` column is the load-bearing half: drift must "
            "be ATTRIBUTED to the view that moved, or a reviewer cannot tell which generated "
            "artifact to regenerate",
        ),
        (
            "an action string edited in the FIRST LONG step packet",
            "long",
            ("long",),
            ("single_file",),
            "the long view is a LIST OF DICTS rather than a string, so it reaches its digest through "
            "a JSON canonicalization the single-file view never touches; a serialization that "
            "dropped a field would leave this view's digest unmoved while its content changed. "
            "Editing a nested field inside the first packet is what exercises that path",
        ),
    )

    def test_a_tampered_view_drifts_and_only_that_view_drifts(self):
        wrong = []
        positive_rows_broken = 0
        for case, recipe, must_drift, must_not_drift, why in self.DRIFTS:
            mutated = self._tamper(self.views, recipe)
            problems = []
            for view in must_drift:
                if not MI.detect_view_drift(self.views, mutated, view):
                    problems.append(
                        f"the {view!r} view was tampered with and drift was NOT detected"
                    )
            for view in must_not_drift:
                if MI.detect_view_drift(self.views, mutated, view):
                    problems.append(
                        f"the {view!r} view was NOT tampered with, yet drift was reported for it, "
                        "so drift cannot be attributed to the view that actually moved"
                    )
            if problems:
                if recipe is None:
                    positive_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                " THE UNTAMPERED ROW IS AMONG THE FAILURES, and while it is broken both mutation "
                "rows are VACUOUS: a detector that always reports drift satisfies them."
            )
        self.assertEqual(
            wrong,
            [],
            f"view-drift detection is wrong for {len(wrong)} of {len(self.DRIFTS)} cases.{vacuity} "
            "BOTH MUTATION ROWS FAILING ON THE 'not tampered' COLUMN means `view_digest` stopped "
            "selecting by view name and is hashing both views together, which detects every "
            "tampering while attributing it to neither: look at `PlanReviewViews.view_digest` "
            "before looking at `detect_view_drift`. FIX: a tampering that goes UNDETECTED is the "
            "worse direction, because the shared semantic digest keeps attesting to the source "
            f"package while the generated artifact a human reads no longer matches it.\n"
            + "\n".join(wrong),
        )

    def test_one_package_yields_both_names_sharing_the_digest_and_the_arguments(self):
        """ONE test replaces three (`test_both_names_compile_from_one_package`,
        `test_both_views_share_the_semantic_digest`, `test_views_share_arguments`).

        They are merged rather than tabulated because they are not rows over data: all three
        interrogate the SAME single compile for three facets of ONE property, which is that two
        command names are two VIEWS of one package and therefore cannot diverge. Stated as separate
        tests, the parity result, the digest, and the argument policy read as independent claims.
        """
        parity = MI.plan_review_parity(self.views)
        wrong = []
        if not parity.ok:
            wrong.append(f"parity failed: {parity.reason}")
        if not parity.aliases_ok:
            wrong.append(
                f"both legacy names must resolve to the ONE package; aliases were "
                f"{self.views.aliases!r}"
            )
        if MI.PLAN_REVIEW_ALIAS not in self.views.aliases:
            wrong.append(
                f"{MI.PLAN_REVIEW_ALIAS!r} is missing from the compiled aliases "
                f"{self.views.aliases!r}, so the long name would need its own package"
            )
        if parity.semantic_digest != self.views.semantic_digest():
            wrong.append(
                f"the parity check reported digest {parity.semantic_digest!r} while the views carry "
                f"{self.views.semantic_digest()!r}, so the two disagree about what was checked"
            )
        descriptor = self.views.compiled["command_descriptor"]
        if descriptor.get("takes_argument") is None:
            wrong.append(
                "the command descriptor carries no argument policy, so the two names could accept "
                f"different arguments; descriptor was {descriptor!r}"
            )
        self.assertEqual(
            wrong,
            [],
            "the plan-review collapse is broken in "
            f"{len(wrong)} respect(s). The three facets are ONE property (two names, one package), "
            "so they normally fail together and the cause is upstream in `compile_plan_review` or "
            "the fixture package rather than in three places. FIX: if the aliases are wrong, the two "
            "command names have become two packages again, which is exactly the duplication this "
            f"Order removed.\n" + "\n".join(wrong),
        )

    def test_recompiling_the_same_package_is_byte_identical(self):
        """Kept separate: the subject is TWO results COMPARED to each other, not to an expectation.

        Determinism cannot be a row in the drift table because it has no fixed expected value: the
        claim is that a second compile of the same bytes equals the first, in the semantic digest AND
        in both generated views. Without it, every drift row could be satisfied by a compiler that
        produced a fresh nondeterministic digest each time.
        """
        again = MI.compile_plan_review(FIXTURE_PKG)
        self.assertEqual(again.semantic_digest(), self.views.semantic_digest())
        for view in ("single_file", "long"):
            with self.subTest(view=view):
                self.assertFalse(MI.detect_view_drift(self.views, again, view))

    def test_the_from_ir_seam_produces_the_same_views_as_compiling(self):
        """Kept separate: materially different setup (a pre-loaded IR, bypassing the loader path).

        `plan_review_views_from_ir` is a second entry point into view construction, so the property
        is that the seam and the full compile AGREE. Both generated views are compared, not only the
        semantic digest, because the digest is computed over the compiled projection and would match
        even if the seam rendered the views differently.
        """
        ir = LOADER.load_package(FIXTURE_PKG).ir
        assert ir is not None
        views = MI.plan_review_views_from_ir(ir)
        self.assertEqual(views.semantic_digest(), self.views.semantic_digest())
        for view in ("single_file", "long"):
            with self.subTest(view=view):
                self.assertEqual(views.view_digest(view), self.views.view_digest(view))

    def test_an_unknown_view_name_is_refused(self):
        """Kept separate: an `assertRaises` test, and it is what keeps the table above honest.

        Every row asserts drift for a NAMED view, so a `view_digest` that silently returned a
        constant for an unrecognized name would let a typo'd view name read as 'no drift'. Refusing
        the name makes that a loud failure instead.
        """
        with self.assertRaises(MI.InventoryError):
            self.views.view_digest("no-such-view")


if __name__ == "__main__":
    unittest.main()
