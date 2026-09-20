"""Clean-delta host adapters, D113 host-evidence gating, and zero-target-write guarantees.

(Originally written for IPD 20260810-awphysical-09; `agent_workflows/clean_delta.py` is the subject.)

WHY THE TESTS WERE RENAMED. Every test in this file was called `test_e01` ... `test_e08` after a
checklist item of the plan that produced it, which told a reader nothing about what broke when one
went red and made the file read as a plan receipt rather than as a description of behavior. Each is
now named for the PROPERTY it asserts. The executed plan under
`.aw/records/plans/executed/20260810-awphysical-09-*.ipd.md` cites the old method names in its
evidence table; that record is history and is not edited (AGENTS.md forbids amending an executed
plan in place), so the mapping is recorded here instead:

    E-01 -> AdapterManifestTests + CleanDeltaInstallTests
    E-02 -> PortableReferenceTests
    E-03 -> AdapterPurityTests
    E-04 -> HostEvidenceGateTests
    E-05 -> TargetDeltaTests
    E-06 -> LegacyConversionTests
    E-07 -> DriftRepairUninstallTests
    E-08 -> (deleted, see below)

WHAT WAS DELETED, and why. `test_e08` asserted `ADVERTISED_CLEAN_DELTA_CLAIMS == D113_EVIDENCE_PAIRS`
and then that each had `len() == 6` from a fixture. The equality is a TAUTOLOGY by construction:
`clean_delta.py` defines `ADVERTISED_CLEAN_DELTA_CLAIMS = set(D113_EVIDENCE_PAIRS)` on one line, so
the assertion restates an assignment and cannot fail unless that line is deleted. The two length
checks were a COUNT PIN against a fixture holding `6`: adding a genuinely proven host makes the
suite red for doing the right thing, and the count says nothing about whether any claim is
supported. The PROPERTY worth keeping (every advertised host/version pair is one the gate actually
accepts, and an unproven one is refused) is now asserted by
`HostEvidenceGateTests::test_every_advertised_claim_is_accepted_and_unproven_input_is_refused`,
which DRIVES `validate_host_evidence` over the real set instead of counting it.

THE FIXTURE FILES ARE GONE FROM THE ASSERTIONS. Each old test began by asserting a fixture JSON
existed and then read expected values out of it. Those files hold literals used exactly once
(`"clean_target_expected_delta": 0`, `"expected_detected_delta": 1`, `"forbidden_absolute_path_prefix":
"/home/"`), so the indirection made every expectation harder to read while adding a second file to
keep in sync and one more way to pass vacuously (a fixture typo silently relaxes a bound). Values
that are genuinely inputs are inline constants here; values that are DERIVABLE (the adapter count,
the owned shim path, the supported host set) are now derived from the module under test, which is
strictly stronger than a hardcoded number.

Tests are deliberately NOT merged into one table: each drives a DIFFERENT function of the module
with materially different setup, and three of them assert raises.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows.clean_delta import (
    ADVERTISED_CLEAN_DELTA_CLAIMS,
    D113_EVIDENCE_PAIRS,
    AdapterKind,
    AdapterPurityError,
    CleanDeltaManager,
    UnsupportedHostError,
    build_default_adapter_manifest,
    compute_target_delta,
    convert_legacy_adapters,
    detect_adapter_drift,
    repair_adapters,
    resolve_adapter_reference,
    snapshot_target_state,
    uninstall_adapters,
    validate_host_evidence,
    verify_adapter_purity,
)
from agent_workflows.project_registry import register_or_update_project
from agent_workflows.project_schema import DeliveryMode, RecordsBackend


class _CleanDeltaFixture(unittest.TestCase):
    """A registered, `.aw/`-configured throwaway target repo plus a separate AW_HOME."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.tmp_dir, "myrepo")
        os.makedirs(os.path.join(self.target_repo, ".git"), exist_ok=True)
        self.aw_home = os.path.join(self.tmp_dir, "aw_home")
        os.makedirs(self.aw_home, exist_ok=True)
        self.user_skills_dir = os.path.join(self.tmp_dir, "user_skills")
        os.makedirs(self.user_skills_dir, exist_ok=True)

        self._prev_aw_home = os.environ.get("AW_HOME")
        os.environ["AW_HOME"] = self.aw_home
        register_or_update_project(
            self.target_repo, self.aw_home, project_id="myrepo-cleandelta"
        )

        os.makedirs(
            os.path.join(self.target_repo, ".aw", "records", "plans"), exist_ok=True
        )
        os.makedirs(
            os.path.join(self.target_repo, ".aw", "state", "durable"), exist_ok=True
        )
        self.write_policy(DeliveryMode.TRACKED, RecordsBackend.REPOSITORY)

    def write_policy(self, delivery_mode, records_backend):
        """Rewrite the project's delivery policy (the input several behaviors branch on)."""

        config_dir = Path(self.target_repo) / ".aw" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            json.dumps(
                {
                    "delivery_mode": delivery_mode.value,
                    "records_backend": records_backend.value,
                    "aw_home": self.aw_home,
                }
            ),
            encoding="utf-8",
        )

    def manifest(self):
        return build_default_adapter_manifest(
            Path(self.target_repo),
            target_repo=self.target_repo,
            aw_home=self.aw_home,
        )

    def tearDown(self):
        if self._prev_aw_home is None:
            os.environ.pop("AW_HOME", None)
        else:
            os.environ["AW_HOME"] = self._prev_aw_home
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


class AdapterManifestTests(_CleanDeltaFixture):
    """Was `test_e01` (first half): every out-of-`.aw` file AW writes has a manifest owner."""

    def test_every_entry_is_keyed_by_its_own_required_path_and_names_a_host(self):
        """The ledger's INVARIANT: the dict key IS the path, and ownership is attributable.

        The key is what `is_owned`/`get` are queried with during uninstall, so a key that disagrees
        with its entry's `required_exact_path` makes uninstall either miss an owned file (leaving
        AW content behind) or fail to recognize it. A blank `host` breaks `host_filter`, which is
        what keeps one host's uninstall from removing another's adapters.
        """

        manifest = self.manifest()
        self.assertTrue(manifest.entries, "the default manifest owns nothing at all")
        broken = []
        known_kinds = {k.value for k in AdapterKind}
        for path_key, entry in sorted(manifest.entries.items()):
            if entry.required_exact_path != path_key:
                broken.append(
                    f"  {path_key}: keyed under this path but declares "
                    f"required_exact_path={entry.required_exact_path!r}"
                )
            if not entry.host:
                broken.append(
                    f"  {path_key}: no owning host, so --host filtering cannot see it"
                )
            if entry.adapter_kind not in known_kinds:
                broken.append(
                    f"  {path_key}: adapter_kind={entry.adapter_kind!r} is not a member of "
                    f"AdapterKind {sorted(known_kinds)}"
                )
            if not entry.ownership_marker:
                broken.append(
                    f"  {path_key}: no ownership marker, so drift detection cannot tell our file "
                    "from a user's"
                )
            if entry.uninstall_behavior not in {"remove", "prune_block"}:
                broken.append(
                    f"  {path_key}: uninstall_behavior={entry.uninstall_behavior!r} is neither "
                    "`remove` nor `prune_block`, so uninstall silently skips it"
                )
        self.assertEqual(
            broken,
            [],
            f"{len(broken)} problem(s) in the default adapter manifest "
            f"({len(manifest.entries)} entries). Every field checked here is consumed by "
            "install/drift/uninstall, so a bad value means AW either leaves content behind or "
            "touches a file it does not own:\n" + "\n".join(broken),
        )

    def test_the_managed_block_adapter_prunes_while_shims_are_removed(self):
        """The two uninstall behaviors must be assigned by adapter KIND, not per file.

        `AGENTS.md` may hold a user's own prose, so its adapter must `prune_block`; a generated shim
        is wholly ours and must be removed outright. Getting this backwards either deletes a user's
        file or leaves a dead pointer behind, and both were observed classes of install bug.
        """

        manifest = self.manifest()
        wrong = []
        for path_key, entry in sorted(manifest.entries.items()):
            expected = (
                "prune_block"
                if entry.adapter_kind == AdapterKind.MANAGED_SECTION_BLOCK.value
                else "remove"
            )
            if entry.uninstall_behavior != expected:
                wrong.append(
                    f"  {path_key} (kind={entry.adapter_kind}): expected "
                    f"{expected!r}, got {entry.uninstall_behavior!r}"
                )
        self.assertEqual(
            wrong,
            [],
            "uninstall behavior no longer follows adapter kind:\n"
            + "\n".join(wrong)
            + "\n  FIX: a MANAGED_SECTION_BLOCK lives in a file that may carry the user's own "
            "content and must be PRUNED; anything else is a file we generated whole and is "
            "REMOVED. Reversing either loses user content or leaves AW content behind.",
        )


class CleanDeltaInstallTests(_CleanDeltaFixture):
    """Was `test_e01` (second half): the install reports target writes from OBSERVED evidence."""

    def test_a_clean_target_reports_zero_writes_and_a_planted_file_is_counted(self):
        """The positive and the canary in one test: the zero claim is only meaningful if a planted
        AW-owned file makes it nonzero. Asserted on a pristine repo (not the fixture's, which
        already carries a `.aw/` tree) so the zero is a real zero."""

        clean_repo = os.path.join(self.tmp_dir, "clean_repo")
        os.makedirs(os.path.join(clean_repo, ".git"), exist_ok=True)
        mgr = CleanDeltaManager(target_repo=clean_repo, aw_home=self.aw_home)

        result = mgr.install_clean_delta(
            "opencode", "1.0.0", user_skills_dir=self.user_skills_dir
        )
        self.assertEqual(
            result["target_writes"],
            0,
            "clean-delta mode wrote (or reported writing) into the target repo. The whole promise "
            f"of the mode is a zero target delta; got {result!r}",
        )
        self.assertEqual(result["mode"], DeliveryMode.CLEAN_DELTA.value)
        self.assertTrue(
            Path(result["user_skill_path"], "SKILL.md").is_file(),
            "the install reported zero target writes but also materialized nothing in the "
            "user-scope skills dir, so it may be reporting zero by doing nothing at all",
        )

        planted = Path(clean_repo) / ".aw" / "planted_target_file.txt"
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text("planted content", encoding="utf-8")

        after = mgr.install_clean_delta(
            "opencode", "1.0.0", user_skills_dir=self.user_skills_dir
        )
        self.assertGreaterEqual(
            after["target_writes"],
            1,
            "an AW-owned file planted in the target repo was NOT counted, so `target_writes` is a "
            "hardcoded claim rather than a measurement and the zero above proves nothing. "
            f"Got {after!r}",
        )

    def test_an_unproven_host_cannot_install_at_all(self):
        """The evidence gate must run BEFORE anything is materialized."""

        mgr = CleanDeltaManager(target_repo=self.target_repo, aw_home=self.aw_home)
        with self.assertRaises(UnsupportedHostError):
            mgr.install_clean_delta(
                "unsupported_host_xyz", "1.0.0", user_skills_dir=self.user_skills_dir
            )
        self.assertFalse(
            (Path(self.user_skills_dir) / "agent-workflows").exists(),
            "the refused install still wrote a user-scope skill, so the gate runs too late",
        )


class PortableReferenceTests(_CleanDeltaFixture):
    """Was `test_e02`: an adapter must never embed a machine-local absolute path."""

    CANONICAL = ".aw/system/workflows/scaffold/scaffold.md"

    def test_a_target_resident_system_is_referenced_by_its_relative_path(self):
        self.write_policy(DeliveryMode.TRACKED, RecordsBackend.REPOSITORY)
        ref = resolve_adapter_reference(
            self.CANONICAL, target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertEqual(
            ref,
            self.CANONICAL,
            "a target-resident system must be referenced by the target-relative path verbatim; "
            f"got {ref!r}",
        )

    def test_an_external_system_is_referenced_by_a_portable_invocation(self):
        self.write_policy(DeliveryMode.CLEAN_DELTA, RecordsBackend.HOME)
        ref = resolve_adapter_reference(
            self.CANONICAL, target_repo=self.target_repo, aw_home=self.aw_home
        )
        self.assertTrue(
            ref.startswith("python3 -m agent_workflows"),
            "with the system OUTSIDE the target, the adapter must carry a stable module "
            f"invocation rather than a path into someone's home directory; got {ref!r}",
        )
        self.assertIn(
            self.CANONICAL, ref, "the invocation must still name what to execute"
        )

    def test_the_external_invocation_strips_an_absolute_path(self):
        """The property the old `forbidden_absolute_path_prefix: "/home/"` fixture stood for.

        Generalized from that ONE prefix to any absolute input, because `/home/` is only the Linux
        spelling and the same leak on macOS starts `/Users/`.

        A WRONG EXPECTATION FOUND AND CORRECTED HERE, recorded because the corrected version is
        narrower than it looks. I first asserted this in BOTH delivery modes and it FAILED in
        `tracked`: `resolve_adapter_reference` returns the canonical identity VERBATIM on the
        target-resident branch (`clean_delta.py:338`) and applies `lstrip("/")` only on the external
        branch (`clean_delta.py:342`). So the no-absolute-path guarantee is a property of the
        EXTERNAL branch alone; in `tracked` mode the function is a passthrough and the guarantee
        comes from the manifest never holding an absolute identity, which
        `test_every_manifest_identity_is_relative` below asserts directly. Asserting it of both
        branches was testing a contract the module does not have.
        """

        self.write_policy(DeliveryMode.CLEAN_DELTA, RecordsBackend.HOME)
        leaks = []
        for identity in (
            self.CANONICAL,
            "/" + self.CANONICAL,
            self.aw_home + "/x.md",
            "//" + self.CANONICAL,
        ):
            ref = resolve_adapter_reference(
                identity, target_repo=self.target_repo, aw_home=self.aw_home
            )
            for token in ref.split():
                if token.startswith("/"):
                    leaks.append(
                        f"  input {identity!r} -> {ref!r} (absolute token {token!r})"
                    )
        self.assertEqual(
            leaks,
            [],
            "the external-system invocation carried an ABSOLUTE path. An adapter is written into "
            "the user's repository, so an absolute path here both breaks on every other machine "
            "and identifies the authoring one (the leak-sanitizer's whole subject):\n"
            + "\n".join(leaks),
        )

    def test_every_manifest_identity_is_relative(self):
        """What actually makes the TRACKED passthrough safe, asserted at the source.

        The tracked branch returns its input unchanged, so portability there is a property of the
        CALLER. Every caller in this module passes an entry's `canonical_system_identity`, so this
        is the assertion that keeps an absolute path from reaching a tracked adapter.
        """

        absolute = [
            f"  {rel}: canonical_system_identity={entry.canonical_system_identity!r}"
            for rel, entry in sorted(self.manifest().entries.items())
            if entry.canonical_system_identity.startswith("/")
            or entry.canonical_system_identity.startswith("~")
        ]
        self.assertEqual(
            absolute,
            [],
            "an adapter manifest entry names its canonical workflow by an ABSOLUTE path. "
            "`resolve_adapter_reference` returns that value VERBATIM for a target-resident system, "
            "so the path would be written into a tracked adapter and committed:\n"
            + "\n".join(absolute),
        )


class AdapterPurityTests(unittest.TestCase):
    """Was `test_e03`: an adapter POINTS at a workflow; it never carries a copy of one."""

    SHIM = Path(".opencode/commands/scaffold.md")

    def test_a_pointer_carrying_an_ownership_marker_is_pure(self):
        self.assertTrue(
            verify_adapter_purity(
                self.SHIM,
                "<!-- aw:pointer -->\nRun canonical workflow via system provider.\n",
            )
        )

    def test_a_duplicated_workflow_body_is_refused(self):
        """A forked body is the defect: the shim stops tracking the canonical workflow silently."""

        with self.assertRaises(AdapterPurityError):
            verify_adapter_purity(
                self.SHIM,
                "<!-- aw:pointer -->\n## Detailed Step-by-Step Instructions\n1. Do step 1\n",
            )

    def test_a_legacy_path_reference_is_refused(self):
        """A `.agents/workflows` pointer resolves to nothing in a migrated install."""

        with self.assertRaises(AdapterPurityError):
            verify_adapter_purity(
                self.SHIM, "<!-- aw:pointer -->\n.agents/workflows/scaffold/scaffold.md"
            )

    def test_content_with_no_ownership_marker_is_refused(self):
        """Without a marker, uninstall and drift detection cannot tell our file from a user's."""

        with self.assertRaises(AdapterPurityError):
            verify_adapter_purity(self.SHIM, "Run the scaffold workflow.\n")


class HostEvidenceGateTests(unittest.TestCase):
    """Was `test_e04` (and the salvageable half of `test_e08`): support claims are GATED."""

    def test_every_advertised_claim_is_accepted_and_unproven_input_is_refused(self):
        """Drives the gate over the REAL claim set instead of counting it.

        This is what replaced `test_e08`'s tautological `ADVERTISED == D113` plus two `len() == 6`
        fixture counts. The property that matters is not how many claims there are: it is that
        every advertised pair is one the gate accepts (no claim without evidence) and that a pair
        outside the set is refused (the evidence is actually load-bearing). Adding a genuinely
        proven host now passes, as it should.
        """

        self.assertTrue(
            ADVERTISED_CLEAN_DELTA_CLAIMS, "no host/mode is advertised at all"
        )
        problems = []
        for pair in sorted(
            ADVERTISED_CLEAN_DELTA_CLAIMS, key=lambda p: (p.host_name, p.version)
        ):
            try:
                got = validate_host_evidence(pair.host_name, pair.version)
            except UnsupportedHostError as exc:
                problems.append(
                    f"  ADVERTISED BUT UNPROVEN: {pair.host_name} {pair.version} is claimed as "
                    f"supported, but the evidence gate refuses it ({exc})"
                )
                continue
            if got != pair:
                problems.append(
                    f"  MISMATCH: {pair.host_name} {pair.version} resolved to a DIFFERENT evidence "
                    f"record ({got})"
                )
            if not got.writable_scope:
                problems.append(
                    f"  NO SCOPE: {pair.host_name} {pair.version} names no writable scope, so the "
                    "claim does not say WHERE the host lets us write"
                )
            try:
                validate_host_evidence(pair.host_name, "99.0.0")
            except UnsupportedHostError:
                pass
            else:
                problems.append(
                    f"  VERSION IGNORED: {pair.host_name} accepted an untested version 99.0.0, so "
                    "the gate keys on the host name only and every future release is silently "
                    "claimed as proven"
                )
        self.assertEqual(
            problems,
            [],
            f"{len(problems)} problem(s) across {len(ADVERTISED_CLEAN_DELTA_CLAIMS)} advertised "
            "clean-delta claims. Each advertised host/version must be backed by a D113 evidence "
            "record, and the version must be part of the key:\n" + "\n".join(problems),
        )

    def test_an_unknown_host_is_refused(self):
        with self.assertRaises(UnsupportedHostError):
            validate_host_evidence("unsupported_host_xyz", "1.0.0")

    def test_the_advertised_set_is_not_a_second_hand_maintained_list(self):
        """Kept from `test_e08`, but as an EQUALITY OF CONTENT rather than of counts.

        `clean_delta.py` derives `ADVERTISED_CLEAN_DELTA_CLAIMS` from `D113_EVIDENCE_PAIRS`, and the
        point of that derivation is that a claim cannot be added without evidence. Asserted so a
        future edit that forks the advertised set into its own literal is caught.
        """

        self.assertEqual(
            ADVERTISED_CLEAN_DELTA_CLAIMS,
            D113_EVIDENCE_PAIRS,
            "the advertised claim set and the evidence set have diverged. They must be one list: a "
            "host advertised without an evidence record is an unproven support claim, which is the "
            "exact failure this module exists to prevent.",
        )


class TargetDeltaTests(_CleanDeltaFixture):
    """Was `test_e05`: the zero-delta proof must be a MEASUREMENT, in all three directions."""

    def test_an_unchanged_tree_measures_zero(self):
        before = snapshot_target_state(self.target_repo)
        after = snapshot_target_state(self.target_repo)
        delta = compute_target_delta(before, after)
        self.assertEqual(
            delta["total_changes"],
            0,
            f"two snapshots of an untouched tree differ, so every 'zero delta' proof built on "
            f"this comparison is noise: {delta!r}",
        )

    #: (label, what to do to the tree, the delta bucket it must land in, why this case exists)
    MUTATIONS = (
        (
            "added file",
            "add",
            "added",
            "a planted AW-owned write is the canary the whole zero-delta claim rests on",
        ),
        (
            "modified file",
            "modify",
            "modified",
            "content-level change with no name change: caught only because the snapshot hashes "
            "contents rather than listing names",
        ),
        (
            "deleted file",
            "delete",
            "deleted",
            "an install that REMOVES a user's file is as much a target delta as one that adds; a "
            "name-set comparison in one direction would miss it",
        ),
    )

    def test_every_kind_of_change_is_detected_and_classified(self):
        """One table over the three mutation kinds: same measurement, different tree change.

        The old test only planted a NEW file. A snapshot that compared names in one direction, or
        that did not hash contents, would pass that and miss both other rows.
        """

        probe = Path(self.target_repo) / "probe.txt"
        probe.write_text("original\n", encoding="utf-8")
        before = snapshot_target_state(self.target_repo)

        wrong = []
        for label, action, bucket, why in self.MUTATIONS:
            extra = Path(self.target_repo) / ".aw" / "planted_canary.txt"
            if action == "add":
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_text("canary\n", encoding="utf-8")
                expected_member = ".aw/planted_canary.txt"
            elif action == "modify":
                probe.write_text("changed\n", encoding="utf-8")
                expected_member = "probe.txt"
            else:
                probe.unlink()
                expected_member = "probe.txt"

            delta = compute_target_delta(
                before, snapshot_target_state(self.target_repo)
            )
            if expected_member not in delta[bucket]:
                wrong.append(
                    f"  {label}: expected {expected_member!r} in delta[{bucket!r}], got "
                    f"{delta!r}\n    this case exists because: {why}"
                )
            if delta["total_changes"] < 1:
                wrong.append(
                    f"  {label}: total_changes is {delta['total_changes']}, so the change was not "
                    f"counted at all\n    this case exists because: {why}"
                )

            # restore for the next row
            if action == "add":
                extra.unlink()
            elif action == "modify":
                probe.write_text("original\n", encoding="utf-8")
            else:
                probe.write_text("original\n", encoding="utf-8")

        self.assertEqual(
            wrong,
            [],
            f"the target-delta measurement missed or misclassified {len(wrong)} of "
            f"{len(self.MUTATIONS)} change kinds. A missed change means an install that DID touch "
            "the target repo reports a clean delta, which is the one lie this module must never "
            "tell:\n" + "\n".join(wrong),
        )


class LegacyConversionTests(_CleanDeltaFixture):
    """Was `test_e06`: migration REPLACES our block and leaves the user's content untouched."""

    FOREIGN = "# User AGENTS file\nUser custom prompt here.\n"
    LEGACY_BLOCK = (
        "<!-- BEGIN AGENT-WORKFLOWS -->\nold block\n<!-- END AGENT-WORKFLOWS -->\n"
    )

    def test_conversion_replaces_our_block_and_preserves_foreign_content_byte_for_byte(
        self,
    ):
        agents_path = Path(self.target_repo) / "AGENTS.md"
        agents_path.write_text(self.FOREIGN + self.LEGACY_BLOCK, encoding="utf-8")

        result = convert_legacy_adapters(self.target_repo, aw_home=self.aw_home)
        self.assertIn("AGENTS.md", result["converted"])

        converted = agents_path.read_text(encoding="utf-8")
        self.assertIn(
            "<!-- aw:block -->",
            converted,
            "the legacy block was not replaced with the current sectioned marker, so the file is "
            "no longer recognized by the parser that owns it",
        )
        self.assertNotIn(
            "<!-- BEGIN AGENT-WORKFLOWS -->",
            converted,
            "the legacy marker survived, so the file now carries TWO managed regions and the next "
            "install will write a third",
        )
        self.assertTrue(
            converted.startswith(self.FOREIGN),
            "the user's own prose above our block was altered. Preserving it byte for byte is the "
            f"non-negotiable property of an in-place conversion; got {converted[: len(self.FOREIGN) + 40]!r}",
        )

    def test_a_shim_is_repointed_while_a_users_own_command_is_left_alone(self):
        """The same preserve-foreign rule one directory over, where the files are whole.

        A user's own file in `.opencode/commands/` is indistinguishable from ours by LOCATION, so
        conversion must decide by CONTENT. This is the case that catches a migration written as a
        directory-wide rewrite.
        """

        shim_dir = Path(self.target_repo) / ".opencode" / "commands"
        shim_dir.mkdir(parents=True, exist_ok=True)
        ours = shim_dir / "scaffold.md"
        ours.write_text(
            "<!-- aw:pointer -->\nRun via .agents/workflows/scaffold/scaffold.md\n",
            encoding="utf-8",
        )
        theirs = shim_dir / "user_custom.md"
        theirs.write_text("my own command\n", encoding="utf-8")

        result = convert_legacy_adapters(self.target_repo, aw_home=self.aw_home)

        self.assertIn(".opencode/commands/scaffold.md", result["converted"])
        self.assertIn(
            ".aw/system/workflows/scaffold/scaffold.md",
            ours.read_text(encoding="utf-8"),
            "our shim still points at the legacy path, which resolves to nothing after migration",
        )
        self.assertEqual(
            theirs.read_text(encoding="utf-8"),
            "my own command\n",
            "a user's own command file in the same directory was rewritten",
        )
        self.assertIn(".opencode/commands/user_custom.md", result["preserved_foreign"])

    def test_converting_twice_changes_nothing_further(self):
        """Idempotence, kept as its own test (a before/after pair is not a table row).

        A migration an operator may re-run must be safe to re-run; a second pass that converts
        again would mean the first pass left something the detector still matches.
        """

        agents_path = Path(self.target_repo) / "AGENTS.md"
        agents_path.write_text(self.FOREIGN + self.LEGACY_BLOCK, encoding="utf-8")
        convert_legacy_adapters(self.target_repo, aw_home=self.aw_home)
        after_first = agents_path.read_text(encoding="utf-8")

        second = convert_legacy_adapters(self.target_repo, aw_home=self.aw_home)
        self.assertEqual(
            second["converted"],
            [],
            f"a second conversion pass converted again ({second['converted']}), so the first pass "
            "left content the legacy detector still matches",
        )
        self.assertEqual(
            agents_path.read_text(encoding="utf-8"),
            after_first,
            "the second pass changed the file, so re-running the migration is not safe",
        )


class DriftRepairUninstallTests(_CleanDeltaFixture):
    """Was `test_e07`: repair and uninstall touch ONLY manifest-owned content."""

    def test_repair_recreates_every_owned_adapter_and_clears_the_drift_report(self):
        manifest = self.manifest()
        before = detect_adapter_drift(self.target_repo, manifest)
        self.assertEqual(
            len(before["missing"]),
            len(manifest.entries),
            "the fixture repo was expected to start with NO adapters in place; if it does not, "
            "this test is not measuring repair",
        )

        repaired = repair_adapters(self.target_repo, manifest=manifest)
        self.assertEqual(
            sorted(repaired),
            sorted(manifest.entries),
            "repair did not restore exactly the manifest-owned set",
        )

        after = detect_adapter_drift(self.target_repo, manifest)
        self.assertEqual(
            (after["missing"], after["drifted"]),
            ([], []),
            f"drift persists after repair, so repair writes content its own detector rejects: "
            f"{after!r}",
        )

    def test_every_repaired_adapter_passes_the_purity_check(self):
        """Cross-checks two halves of the module against each other: what repair WRITES must be
        what `verify_adapter_purity` ACCEPTS. Each half passing alone is not enough; a repair that
        emits a body its own purity gate would refuse is a defect neither test sees in isolation."""

        manifest = self.manifest()
        impure = []
        for rel in repair_adapters(self.target_repo, manifest=manifest):
            content = (Path(self.target_repo) / rel).read_text(encoding="utf-8")
            try:
                verify_adapter_purity(Path(rel), content)
            except AdapterPurityError as exc:
                impure.append(f"  {rel}: {exc}")
        self.assertEqual(
            impure,
            [],
            "repair wrote adapter content that the module's OWN purity gate refuses:\n"
            + "\n".join(impure),
        )

    def test_host_scoped_uninstall_removes_only_that_hosts_adapters(self):
        """The isolation property, asserted in all three directions at once.

        The old test checked one owned shim was removed and one planted foreign file survived. It
        did not check that the OTHER HOSTS' adapters survived, which is the failure a missing
        `host_filter` produces and the one an operator notices (disabling one host wipes another).
        """

        manifest = self.manifest()
        repair_adapters(self.target_repo, manifest=manifest)

        foreign = Path(self.target_repo) / ".opencode" / "commands" / "user_custom.md"
        foreign.parent.mkdir(parents=True, exist_ok=True)
        foreign.write_text("user custom command", encoding="utf-8")

        owned_by_opencode = sorted(
            rel for rel, e in manifest.entries.items() if e.host == "opencode"
        )
        owned_by_others = sorted(
            rel for rel, e in manifest.entries.items() if e.host != "opencode"
        )
        self.assertTrue(
            owned_by_opencode, "the manifest owns no opencode adapters to remove"
        )
        self.assertTrue(
            owned_by_others, "no other host's adapters exist, so isolation is vacuous"
        )

        removed = uninstall_adapters(
            self.target_repo, manifest=manifest, host_filter="opencode"
        )

        problems = []
        if sorted(removed) != owned_by_opencode:
            problems.append(
                f"  removed set {sorted(removed)} != opencode's owned set {owned_by_opencode}"
            )
        for rel in owned_by_opencode:
            if (Path(self.target_repo) / rel).exists():
                problems.append(f"  {rel}: reported removed but still on disk")
        for rel in owned_by_others:
            if not (Path(self.target_repo) / rel).exists():
                problems.append(
                    f"  {rel}: another host's adapter was destroyed by an opencode-scoped uninstall"
                )
        if not foreign.is_file():
            problems.append(
                "  .opencode/commands/user_custom.md: the user's OWN file in the adapter directory "
                "was deleted"
            )
        self.assertEqual(
            problems,
            [],
            f"{len(problems)} problem(s) in host-scoped uninstall. It must remove exactly the "
            "named host's manifest-owned adapters, leave every other host's in place, and never "
            "touch a file it does not own:\n" + "\n".join(problems),
        )

    def test_pruning_a_managed_block_keeps_the_users_own_prose(self):
        """`prune_block` is the destructive-adjacent path: it edits a file it does not fully own."""

        agents = Path(self.target_repo) / "AGENTS.md"
        foreign = "# User AGENTS file\nUser custom prompt here.\n"
        agents.write_text(
            foreign + "<!-- aw:block -->\npointer\n<!-- /aw:block -->\n",
            encoding="utf-8",
        )
        manifest = self.manifest()
        block_hosts = sorted(
            {
                e.host
                for e in manifest.entries.values()
                if e.adapter_kind == AdapterKind.MANAGED_SECTION_BLOCK.value
            }
        )
        self.assertEqual(
            len(block_hosts), 1, f"expected one managed-block host, got {block_hosts}"
        )

        removed = uninstall_adapters(
            self.target_repo, manifest=manifest, host_filter=block_hosts[0]
        )
        self.assertIn("AGENTS.md", removed)
        self.assertEqual(
            agents.read_text(encoding="utf-8"),
            foreign,
            "pruning the managed block must leave the user's prose EXACTLY as it was; got "
            f"{agents.read_text(encoding='utf-8')!r}",
        )


if __name__ == "__main__":
    unittest.main()
