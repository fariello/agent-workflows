"""Self-tests for generated Agent Skills, host adapters, and the agy fresh verifier.

awoptimize Order 11 (`bmd1ur`) E-05 validates E-01..E-04:
- Generated-artifact + semantic-digest-parity (E-01).
- Per-host adapter metadata gated by the Order-10 registry; reuse (not fork) of the
  engine.py shim generator; role/permission mapping; external-runtime fallback (E-02).
- Discovery diagnostics + skill-authority restriction; disabling a skill leaves the
  explicit runtime invocation usable (E-03).
- agy fresh-session verifier doubles: distinct session identity + Order-08 packet; the
  same-session audit is diagnostic and cannot finalize (E-04).
- Security tests: local-server loopback/auth, permission denial, external-path refusal
  (assert_contained / assert_isolated_base), secret redaction.

Pure stdlib unittest; no live host/agy/network probes.

MOST OF THIS FILE IS TABLE-DRIVEN, because most of it was one shape repeated: build one artifact from
one configuration and assert one property of it. The tables group BY SUBJECT (the generated package,
the digest, the registry-gated adapter, the role map, the discovery policy, the verifier's modes, the
negative probes) rather than by which function implements the answer.

WHAT WAS A CONFIGURATION IS NOW A COLUMN. `build_skill_package`'s budget override and its
`extra_resources` seam, the registry's evidence state, the verifier's MODE, and the negative probe
CLASS were each being expressed as a separate test over the same subject, which is what made these
suites sprawl.

CLAIMS THAT CONSTRAIN EACH OTHER SHARE A TABLE, and the digest table is the clearest case: a digest
function returning a CONSTANT satisfies every determinism row, and one hashing a timestamp satisfies
every differs row, so the two senses are only meaningful together. Likewise the adapter table pairs a
promoted feature with an unproven one, because an adapter advertising everything and one advertising
nothing each satisfy exactly half of it.

NO SECURITY ROW SETTLES FOR "IT REFUSED": the negative-probe rows assert BOTH that the refusal was
observed AND that the side effect was prevented, since a host that reported a refusal after already
writing is the failure that matters.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the claim is an `assertRaises`; the subject is the real workflow tree on disk rather than a
fixture; the claim is structural (object identity between two modules); or the setup is materially
different (a temporary directory used as an isolation base).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_verifier as av
from agent_workflows import engine
from agent_workflows import host_adapters as ha
from agent_workflows import host_capability_registry as hcr
from agent_workflows import verify_roles
from agent_workflows.run_ledger_store import RedactionPolicy


# --------------------------------------------------------------------------------------------------
# Shared fixtures / builders
# --------------------------------------------------------------------------------------------------


def make_workflow(
    command="assess",
    body=".aw/system/workflows/assess/HARNESS.md",
    description="Assess a single concern deeply and write an IPD",
    lens="",
    arg_hint="",
):
    return engine.Workflow(
        command=command,
        body=body,
        description=description,
        lens=lens,
        arg_hint=arg_hint,
    )


def make_supported_record(host, version, feature):
    """Build a proven-positive EvidenceRecord that query_capability will mark supported."""
    return hcr.EvidenceRecord(
        host=host,
        exact_version=version,
        feature=feature,
        probe_variant="default",
        result=hcr.STATUS_SUPPORTED,
        source_type=hcr.SOURCE_ISOLATED_PROBE,
        evidence_artifact="PROBE-OK-example.txt",
        resolved=True,
        followed=True,
        side_effect_verified=True,
        diagnostic_evidence="probe resolved and followed with nonce side effect",
    )


def make_verifier_packet(run_id="run-deadbeef01"):
    return verify_roles.build_verifier_packet(
        run_id=run_id,
        workflow_id="assess",
        base_commit="a" * 40,
        head_commit="b" * 40,
        worktree_path="/tmp/isolated-worktree",
        frozen_requirements={"must": ["Do the thing"]},
        declared_scope={"allowed_paths": ["agent_workflows/*"]},
        actual_diff="diff --git a/x.py b/x.py\n+ added",
    )


# --------------------------------------------------------------------------------------------------
# E-01: skill package generation + semantic digest parity
# --------------------------------------------------------------------------------------------------

#: The `sense` column of `SkillDigestTests.DIGESTS`.
SAME = "same-digest"
DIFFERS = "different-digest"


class SkillPackageTests(unittest.TestCase):
    """What `build_skill_package` produces under each configuration it accepts.

    ONE table replaces seven tests (`test_generated_skill_passes_format_validation`,
    `test_trigger_description_distinguishes_use_vs_non_use`,
    `test_resource_references_resolve_within_package`, `test_main_file_meets_budget`,
    `test_budget_violation_is_detected`, `test_router_carries_digest_and_explicit_invocation_not
    _inlined_body`, `test_no_per_package_script_resource_is_emitted`,
    `test_script_kind_remains_reachable_via_extra_resources`). Every one built a package and asserted
    something about it; the CONFIGURATION (the budget override, the injected extra resource) is a
    column, and what each row checks is expressed as data rather than as a separate method.

    Why the table beats the seven: one builder produces every row, so the realistic regression is in
    the builder and it moves several rows at once - a template change breaks the trigger tokens and
    the router tokens together, while a resource-emission change moves the resource rows alone. Seven
    tests report that as seven unrelated failures; the table reports one that names each broken
    property and its configuration.

    THE BUDGET-VIOLATION ROW IS THE FALSIFIER for the clean rows, which is why it lives here rather
    than apart: a validator returning no findings for anything would satisfy every clean row on its
    own. Its expected finding is matched by a SUBSTRING, because the message legitimately carries the
    measured byte count.

    THE `extra_resources` ROW PINS AN ACCEPTED-BUT-UNPRODUCED KIND. IPD `8fhjjc` removed the
    per-package verification script, so the default package must emit NO `kind=='script'` resource
    (enforced at the GENERATOR level, not merely at install time, so a re-introduction fails here and
    not only in the slow install suite), and `verify_digest` must be absent from the router. The
    `script` kind itself stays injectable through the caller-facing seam, which is what keeps
    re-adding one a one-entry change, so it is pinned rather than assumed.
    """

    #: (case, kwargs for `build_skill_package`, a substring every finding list must contain (None when
    #: the package must validate CLEAN), whether `within_budget()` must hold, the EXACT sorted resource
    #: relative paths (None to skip), resource paths that must be present (for the injected row),
    #: substrings the main file must contain, substrings the main file must NOT contain, why this row
    #: exists)
    PACKAGES = (
        (
            "the default generated package",
            {},
            None,
            True,
            ["reference/canonical-body.md"],
            (),
            (),
            ("verify_digest",),
            "THE SHIPPED ARTIFACT, and the row every other row is measured against: the default "
            "package must validate CLEAN and be exactly the router plus the canonical-body pointer. "
            "`verify_digest` is forbidden because IPD `8fhjjc` deleted the per-package verification "
            "script, and forbidding it at the GENERATOR level means a re-introduction fails here "
            "rather than only in the slow install suite",
        ),
        (
            "a package built with an absurdly small budget",
            {"main_budget_bytes": 10},
            "exceeds budget",
            False,
            None,
            (),
            (),
            (),
            "THE FALSIFIER for every clean row above: a validator that returned no findings for "
            "anything would satisfy them all. The budget exists because a router that grows into a "
            "full document defeats the point of a router, so the violation must be DETECTED rather "
            "than silently tolerated. Matched by substring, since the message carries the measured "
            "byte count",
        ),
        (
            "a package with a `script` resource injected through `extra_resources`",
            {
                "extra_resources": [
                    ha.SkillResource(
                        relative_path="scripts/custom.py",
                        kind="script",
                        content="#!/usr/bin/env python3\n",
                    )
                ]
            },
            None,
            True,
            None,
            ("scripts/custom.py",),
            (),
            (),
            "THE `script` KIND IS ACCEPTED-BUT-UNPRODUCED, not removed. Keeping the caller-facing seam "
            "working is what makes re-adding a per-package script a one-entry change instead of a "
            "generator rewrite, and it must still validate CLEAN - so the default package emitting no "
            "script is a POLICY choice rather than a lost capability",
        ),
    )

    def test_every_build_configuration_produces_a_valid_router_package(self):
        workflow = make_workflow()
        wrong = []
        clean_rows_broken = 0
        for (
            case,
            kwargs,
            finding_needle,
            within_budget,
            exact_resources,
            required_resources,
            required_content,
            forbidden_content,
            why,
        ) in self.PACKAGES:
            pkg = ha.build_skill_package(workflow, **kwargs)
            findings = ha.validate_skill_package(pkg)
            problems = []
            if finding_needle is None:
                if findings:
                    clean_rows_broken += 1
                    problems.append(f"must validate CLEAN; got findings {findings!r}")
            elif not any(finding_needle in f for f in findings):
                problems.append(
                    f"expected a finding containing {finding_needle!r}; got {findings!r}"
                )
            if pkg.within_budget() is not within_budget:
                problems.append(
                    f"within_budget() is {pkg.within_budget()!r}, expected {within_budget} "
                    f"({pkg.main_file_bytes()} bytes against a budget of {pkg.main_budget_bytes})"
                )
            if within_budget and pkg.main_file_bytes() > pkg.main_budget_bytes:
                problems.append(
                    f"the main file is {pkg.main_file_bytes()} bytes, over its own budget of "
                    f"{pkg.main_budget_bytes}, while within_budget() claims otherwise"
                )
            got_resources = sorted(r.relative_path for r in pkg.resources)
            if exact_resources is not None and got_resources != sorted(exact_resources):
                problems.append(
                    f"resources are {got_resources!r}, expected exactly {sorted(exact_resources)!r}"
                )
            missing_resources = [
                r for r in required_resources if r not in got_resources
            ]
            if missing_resources:
                problems.append(
                    f"these resources are absent: {missing_resources!r}; got {got_resources!r}"
                )
            if exact_resources is not None:
                scripts = [r.relative_path for r in pkg.resources if r.kind == "script"]
                if scripts:
                    problems.append(
                        f"the DEFAULT package emitted `kind=='script'` resource(s) {scripts!r}; IPD "
                        "`8fhjjc` removed the per-package verification script, so the generator must "
                        "produce none"
                    )
            # Every declared resource reference must resolve inside the package's own file map,
            # otherwise the installed skill points at a file that was never written.
            files = pkg.to_files()
            unresolved = [ref for ref in pkg.resource_paths() if ref not in files]
            if unresolved:
                problems.append(
                    f"these resource references do not resolve within the package: {unresolved!r}; "
                    f"the package writes {sorted(files)!r}"
                )
            # The trigger description must say when to use the skill AND when not to; a one-sided
            # trigger is what makes a host fire a skill on unrelated requests.
            for token in ("Use when", "Do not use"):
                if token not in pkg.trigger_description:
                    problems.append(
                        f"the trigger description omits {token!r}, so the host is told when to fire "
                        f"the skill but not when to refrain: {pkg.trigger_description!r}"
                    )
            # The router must carry the digest and the explicit invocation; the digest is how an
            # installed skill is matched to the workflow it was generated from, and the explicit
            # invocation is what keeps the workflow usable when the skill is disabled.
            for needle in (
                pkg.semantic_digest,
                pkg.explicit_invocation,
                *required_content,
            ):
                if needle not in pkg.main_file_content:
                    problems.append(
                        f"the main file omits {needle!r}, which the router must carry"
                    )
            for needle in forbidden_content:
                if needle in pkg.main_file_content:
                    problems.append(
                        f"the main file contains {needle!r}, which it must NOT"
                    )
            if problems:
                wrong.append(
                    f"  {case} (kwargs={sorted(kwargs)!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        extra = ""
        if clean_rows_broken:
            extra = (
                f" {clean_rows_broken} row(s) that must validate CLEAN are among the failures, and "
                "while any of those is broken the budget-violation row proves nothing: a validator "
                "that flags everything satisfies it."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.PACKAGES)} build configurations produced a wrong package."
            f"{extra} ONE builder produces every row, so read the grouping: the trigger and router "
            "tokens failing together means the SKILL.md template changed; the resource rows alone "
            "means resource emission changed; an unresolved resource reference means the package "
            "points at a file it never writes, which installs a broken skill. FIX: the default "
            "package emitting a `kind=='script'` resource is a REGRESSION of IPD `8fhjjc`, not a "
            "feature - the `script` kind stays reachable through `extra_resources` (the third row), so "
            "re-adding one belongs there and not in the generator.\n"
            + "\n".join(wrong),
        )


class SkillDigestTests(unittest.TestCase):
    """What the semantic digest treats as the same workflow and what it treats as a real change.

    ONE table replaces two tests (`test_semantic_digest_parity_deterministic_and_matches_scheme`,
    `test_semantic_digest_changes_when_semantics_change`) whose only difference was the SENSE of the
    comparison, which is now a column.

    THE TWO SENSES MUST SHARE THIS TABLE, and that is the whole point: a digest function returning a
    CONSTANT passes every `SAME` row while making the digest useless for detecting drift, and one
    mixing in a timestamp or an object id passes every `DIFFERS` row while making a freshly generated
    package look changed on every run. No single degenerate implementation can pass both, and neither
    old test alone could catch its own degenerate case.

    THE SCHEME ROW IS THE THIRD CLAIM and it is the one that makes the digest useful at all: the value
    embedded in the generated package must be the SAME value `compute_workflow_semantic_digest`
    computes, because that is how an installed skill is matched back to the workflow it came from. A
    package carrying an internally consistent but differently-derived digest would satisfy determinism
    and difference while never matching anything the rest of the toolkit computes.
    """

    #: (case, the first workflow, the second workflow (None to compare the package's digest against
    #: `compute_workflow_semantic_digest` of the first), SAME or DIFFERS, why this row exists)
    DIGESTS = (
        (
            "the same workflow built twice",
            make_workflow(),
            make_workflow(),
            SAME,
            "DETERMINISM: building the same workflow twice must yield one digest, or every "
            "regeneration would look like a change and the digest could not be used to detect drift "
            "at all",
        ),
        (
            "the package's digest against the scheme function",
            make_workflow(),
            None,
            SAME,
            "THE SCHEME ROW, and the claim that makes the digest useful: the value EMBEDDED in the "
            "generated package must equal what `compute_workflow_semantic_digest` computes, because "
            "that is how an installed skill is matched back to its workflow. An internally consistent "
            "but differently-derived digest would satisfy the other two rows and match nothing",
        ),
        (
            "two workflows differing in command and body",
            make_workflow(),
            make_workflow(
                command="verify", body=".aw/system/workflows/verify/HARNESS.md"
            ),
            DIFFERS,
            "THE FALSIFIER: a digest returning a CONSTANT satisfies both rows above while being "
            "worthless. Command and body are the workflow's identity and its authority, so two "
            "workflows differing in them must never collide - a collision would let one skill's "
            "router claim another's canonical body",
        ),
    )

    def test_the_digest_is_deterministic_and_changes_only_with_the_workflow(self):
        wrong = []
        same_rows_broken = 0
        differs_rows_broken = 0
        for case, first, second, sense, why in self.DIGESTS:
            a = ha.build_skill_package(first).semantic_digest
            if second is None:
                b = ha.compute_workflow_semantic_digest(first)
            else:
                b = ha.build_skill_package(second).semantic_digest
            equal = a == b
            if equal is not (sense == SAME):
                if sense == SAME:
                    same_rows_broken += 1
                else:
                    differs_rows_broken += 1
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected the two digests to be {'EQUAL' if sense == SAME else 'DIFFERENT'}\n"
                    f"    - got {a!r} and {b!r}\n"
                    f"    this row exists because: {why}"
                )
        direction = ""
        if differs_rows_broken and not same_rows_broken:
            direction = (
                " The DIFFERS row failed, so the digest is COLLIDING: it no longer distinguishes two "
                "workflows, and the determinism rows above are satisfied trivially by a constant."
            )
        elif same_rows_broken and not differs_rows_broken:
            direction = (
                f" {same_rows_broken} SAME row(s) failed, so the digest is UNSTABLE (a timestamp, an "
                "object id, or unordered iteration has leaked in) and every regeneration will look "
                "like a change; the DIFFERS row proves nothing while that is true."
            )
        self.assertEqual(
            wrong,
            [],
            f"the semantic digest was wrong in {len(wrong)} of {len(self.DIGESTS)} "
            f"comparisons.{direction} Both senses share this table because no single degenerate "
            "implementation can pass it: a constant digest passes every SAME row and a "
            "timestamp-seeded one passes every DIFFERS row. Read the grouping: the SCHEME row failing "
            "ALONE is the subtle case - the digest is then deterministic and discriminating but is no "
            "longer the value the rest of the toolkit computes, so nothing can match an installed "
            "skill to its workflow. FIX: derive the package's digest from "
            "`compute_workflow_semantic_digest` rather than recomputing it beside it.\n"
            + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------------------
# E-02: host adapters gated by the Order-10 registry, reuse of engine shim generator
# --------------------------------------------------------------------------------------------------


class HostAdapterTests(unittest.TestCase):
    """What an adapter may advertise, given what the capability registry can prove.

    ONE table replaces three tests (`test_unverified_capability_not_advertised_as_supported`,
    `test_registry_promotion_advertises_supported`, `test_support_table_never_exceeds_recorded_claim`).
    All three built a registry, built an adapter from it, and asserted which features appeared where;
    the REGISTRY STATE is the row and the rendered support table is one more column rather than a
    separate test.

    THE EMPTY-REGISTRY ROW AND THE PROMOTED ROW MUST SHARE THIS TABLE. This is a fail-closed gate, so
    both directions are real failures: an adapter that advertised everything would satisfy the promoted
    row while claiming capabilities nothing probed (the exact overclaiming the registry exists to
    stop), and one that advertised nothing would satisfy the empty row while making every proven
    capability unusable. Neither can pass both rows.

    THE PROMOTED ROW CARRIES AN UNPROVEN FEATURE ALONGSIDE THE PROVEN ONE, which is what turns "the
    registry can promote" into "the registry promotes EXACTLY what it has evidence for". One proven
    feature in isolation is satisfied by an adapter that promotes on request.

    THE RENDERED TABLE IS A COLUMN because it is the operator-facing surface and it must never exceed
    the recorded claim: a support table printing `supported` for a feature the adapter itself lists as
    unverified would mislead the human while every structural assertion passed.
    """

    #: (case, features to record proven evidence for, the `candidate_features` argument (None to
    #: omit), features that must be advertised SUPPORTED, features that must be UNVERIFIED, rows the
    #: rendered support table must contain, substrings the rendered table must contain, why this row
    #: exists)
    ADAPTERS = (
        (
            "an EMPTY registry, nothing probed",
            (),
            None,
            (),
            ("command", "skill", "subagent", "permissions", "run_json"),
            (),
            (),
            "FAIL CLOSED BY DEFAULT: with no evidence at all, nothing may be advertised as supported. "
            "The whole point of the Order-10 registry is that a capability claim requires a probe, so "
            "an unprobed host must advertise nothing - and every unverified feature must carry a "
            "REASON, or an operator cannot tell 'not probed' from 'probed and failed'",
        ),
        (
            "one feature proven, one candidate with no evidence",
            ("command",),
            ("command", "subagent"),
            ("command",),
            ("subagent",),
            ("| opencode | 1.0.0 | command | router | supported |",),
            ("unverified", "subagent"),
            "PROMOTION IS EVIDENCE-BOUND, and the unproven feature beside the proven one is what makes "
            "that a real claim rather than 'promotes on request'. The rendered row is pinned verbatim "
            "because the support table is the OPERATOR-FACING surface: a table printing `supported` "
            "for a feature the adapter lists as unverified would mislead a human while every "
            "structural assertion passed",
        ),
    )

    def test_an_adapter_advertises_exactly_what_the_registry_can_prove(self):
        wrong = []
        supported_rows_broken = 0
        unverified_rows_broken = 0
        for (
            case,
            proven,
            candidates,
            expect_supported,
            expect_unverified,
            table_rows,
            table_needles,
            why,
        ) in self.ADAPTERS:
            registry = hcr.HostCapabilityRegistry()
            for feature in proven:
                registry.register_record(
                    make_supported_record("opencode", "1.0.0", feature)
                )
            kwargs = (
                {} if candidates is None else {"candidate_features": list(candidates)}
            )
            adapter = ha.build_host_adapter(
                "opencode", registry, exact_version="1.0.0", **kwargs
            )
            problems = []
            missing_supported = [
                f for f in expect_supported if f not in adapter.supported_features
            ]
            if missing_supported:
                supported_rows_broken += len(missing_supported)
                problems.append(
                    f"these PROVEN features are not advertised supported: {missing_supported!r}; "
                    f"supported_features={adapter.supported_features!r}"
                )
            for feature in expect_unverified:
                if feature not in adapter.unverified_features:
                    unverified_rows_broken += 1
                    problems.append(
                        f"{feature!r} has no evidence yet is missing from unverified_features "
                        f"({adapter.unverified_features!r})"
                    )
                elif adapter.advertises_supported(feature):
                    unverified_rows_broken += 1
                    problems.append(
                        f"{feature!r} is listed unverified yet `advertises_supported` returns True, "
                        "so the adapter contradicts itself and overclaims"
                    )
                elif feature not in adapter.capability_reasons:
                    problems.append(
                        f"{feature!r} is unverified with no entry in capability_reasons, so an "
                        "operator cannot tell 'not probed' from 'probed and failed'"
                    )
            leaked = [f for f in expect_unverified if f in adapter.supported_features]
            if leaked:
                problems.append(
                    f"these UNPROVEN features are advertised supported: {leaked!r}, which is exactly "
                    "the overclaiming the capability registry exists to prevent"
                )
            still_unverified = [
                f for f in expect_supported if f in adapter.unverified_features
            ]
            if still_unverified:
                problems.append(
                    f"these proven features remain in unverified_features: {still_unverified!r}"
                )
            if table_rows or table_needles:
                table = ha.build_support_table({"opencode": adapter})
                for row in table_rows:
                    if row not in table:
                        problems.append(
                            f"the rendered support table omits the row {row!r}; it renders as:\n"
                            f"{table}"
                        )
                for needle in table_needles:
                    if needle not in table:
                        problems.append(
                            f"the rendered support table omits {needle!r}, so an unproven feature is "
                            f"not visibly unverified to the operator; it renders as:\n{table}"
                        )
            if problems:
                wrong.append(
                    f"  {case} (proven={list(proven)!r}, candidates={candidates!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if unverified_rows_broken and not supported_rows_broken:
            direction = (
                f" {unverified_rows_broken} UNVERIFIED expectation(s) failed, so the adapter is "
                "OVERCLAIMING: it advertises capabilities nothing probed, which is the failure the "
                "capability registry exists to prevent. The promoted row proves nothing while that is "
                "true, since an adapter advertising everything satisfies it."
            )
        elif supported_rows_broken and not unverified_rows_broken:
            direction = (
                f" {supported_rows_broken} SUPPORTED expectation(s) failed, so promotion is broken and "
                "a proven capability is unusable; the empty-registry row proves nothing while that is "
                "true, since an adapter advertising nothing satisfies it."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.ADAPTERS)} registry states produced a wrong adapter."
            f"{direction} Read the grouping: a feature appearing in BOTH `supported_features` and "
            "`unverified_features` means the two lists are computed independently and have drifted; a "
            "missing `capability_reasons` entry means the adapter can no longer explain itself; a "
            "rendered-table mismatch with correct structural lists means the OPERATOR-FACING view "
            "exceeds the recorded claim, which is the form of overclaiming a human actually reads. "
            "FIX: never widen an expectation to match an adapter that advertises more than was "
            "probed.\n" + "\n".join(wrong),
        )

    #: `direction` column values for `ROLES`.
    FEATURE_TO_ROLE = "map_feature_to_role"
    ROLE_TO_TARGET = "resolve_role_target"

    #: (direction, host, the feature or role to look up, the EXACT expected answer, why this row
    #: exists)
    ROLES = (
        (
            FEATURE_TO_ROLE,
            "opencode",
            "subagent",
            ha.ROLE_ISOLATED_EXECUTOR,
            "A NATIVE FEATURE MAPS TO THE ROLE IT FILLS: opencode's subagent is an isolated executor, "
            "which is what lets the toolkit ask for a ROLE and let each host answer with whatever it "
            "actually has",
        ),
        (
            FEATURE_TO_ROLE,
            "codex",
            "exec",
            ha.ROLE_NONINTERACTIVE_RUNTIME,
            "A DIFFERENT HOST, A DIFFERENT FEATURE, THE SAME MECHANISM. Keeping a second host in the "
            "table is what states the map is per-host data rather than opencode's vocabulary with "
            "exceptions",
        ),
        (
            FEATURE_TO_ROLE,
            "codex",
            "subagent",
            None,
            "AN ABSENT FEATURE MAPS TO NOTHING, and this row is the falsifier for the two above: a map "
            "returning a plausible role for any input would satisfy them both. `None` here is what "
            "forces the fallback the next row asserts",
        ),
        (
            ROLE_TO_TARGET,
            "codex",
            ha.ROLE_ISOLATED_EXECUTOR,
            ha.HOST_NONINTERACTIVE_RUNTIME["codex"],
            "THE EXTERNAL-RUNTIME FALLBACK, and the reason roles exist at all: codex has no native "
            "isolated executor, so the role must resolve to its non-interactive runtime rather than "
            "failing. This is the row that pairs with the `None` row above - an unmapped feature must "
            "degrade to coordination, not to an error",
        ),
        (
            ROLE_TO_TARGET,
            "opencode",
            ha.ROLE_ISOLATED_EXECUTOR,
            "subagent",
            "THE NATIVE PATH MUST NOT BE LOST TO THE FALLBACK: a host that HAS the feature must "
            "resolve to it. Without this row the fallback could apply universally and every host would "
            "be driven through an external runtime, silently giving up real isolation",
        ),
    )

    def test_roles_map_to_native_features_and_fall_back_when_absent(self):
        wrong = []
        for direction, host, key, expected, why in self.ROLES:
            if direction == self.FEATURE_TO_ROLE:
                got = ha.map_feature_to_role(host, key)
            else:
                got = ha.resolve_role_target(host, key)
            if got != expected:
                wrong.append(
                    f"  {direction}({host!r}, {key!r}):\n"
                    f"    - expected {expected!r}\n"
                    f"    - got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.ROLES)} role lookups are wrong. The two DIRECTIONS are "
            "complementary halves of one design - `map_feature_to_role` says what a host's feature IS, "
            "`resolve_role_target` says what to USE for a role - so read the grouping: every "
            f"{self.FEATURE_TO_ROLE} row failing means the per-host feature map changed shape, while "
            f"the {self.ROLE_TO_TARGET} rows failing together means the fallback policy did. The "
            "`codex`/`subagent` -> None row and the codex fallback row are a PAIR: an absent feature "
            "must degrade to the non-interactive runtime rather than erroring. FIX: the opencode "
            "fallback row failing means the fallback is now applied universally, which silently gives "
            "up real isolation on hosts that have it - a capability loss no error message would "
            "report.\n" + "\n".join(wrong),
        )

    def test_reuses_engine_shim_generator_not_forked(self):
        """Kept separate: object IDENTITY between two modules, plus a sweep over the REAL workflow tree.

        Every table row builds a fixture; this asserts `host_adapters` is the same object as
        `engine`'s generator (a re-forked copy that behaves identically today is how two generators
        drift apart) and then generates from the shipped `.aw/system/workflows` tree, whose absence
        legitimately skips the test.
        """
        self.assertIs(ha.generate_shim_members, engine.generate_shim_members)
        self.assertIs(ha.shim_body, engine.shim_body)
        self.assertEqual(ha.COMMAND_SHIM_DIRS, engine.COMMAND_SHIM_DIRS)

        source_root = _find_source_root()
        workflows = engine.parse_manifest(source_root)
        registry = hcr.HostCapabilityRegistry()
        bundle = ha.generate_adapter_bundle(workflows, source_root, registry)
        expected = engine.generate_shim_members(
            workflows, source_root, target_layout="aw"
        )
        self.assertEqual(bundle.shims, expected)
        # Every generated shim is grammatically valid for its host (reused validator).
        for path, content in bundle.shims.items():
            if path.endswith("README.md"):
                continue
            tool = "claude" if path.startswith(".claude") else "opencode"
            self.assertTrue(
                ha.validate_shim_grammar(content, tool),
                f"invalid shim grammar for {path}",
            )


# --------------------------------------------------------------------------------------------------
# E-03: discovery diagnostics + skill-authority restriction
# --------------------------------------------------------------------------------------------------


class DiscoveryPolicyTests(unittest.TestCase):
    """How a workflow's shape decides its discovery surface, and what the router may not contain.

    TWO tables replace five tests. The first replaces the two classification tests
    (`test_complex_workflow_becomes_skill_entry_point`,
    `test_simple_command_may_remain_generated_command`), whose only difference was the WORKFLOW and
    therefore the expected policy. The second replaces the authority pair
    (`test_authority_never_inlined_only_in_skill_prose`, `test_inlined_authority_is_detected`), whose
    only difference was whether the router had been corrupted.

    THEY STAY TWO TABLES rather than one because the subjects are different functions over different
    inputs; what they share is the reason each is a table at all: in both cases the two rows are
    opposite senses of one judgement, and each sense alone is satisfiable by a degenerate
    implementation. A classifier returning `skill_entry_point` for everything would pass the lensed
    row, and a detector returning findings for everything would pass the inlined row.

    THE AUTHORITY CHECK IS THE SECURITY-SHAPED ONE OF THE TWO: the canonical body is the AUTHORITY and
    the router merely points at it, so a router that inlined the body would ship a stale, unreviewable
    copy of the instructions a host actually follows. The clean row proves the check does not fire on
    an ordinary package; the corrupted row proves it fires when it must.
    """

    #: (case, the workflow, the EXACT expected discovery policy, why this row exists)
    POLICIES = (
        (
            "a workflow carrying a lens",
            make_workflow(
                command="assess", lens=".aw/system/workflows/assess/lenses/security.md"
            ),
            ha.POLICY_SKILL_ENTRY_POINT,
            "A LENS MAKES A WORKFLOW COMPLEX, and complex workflows need a skill as their entry point "
            "so the host can load the right lens on demand instead of inlining every variant into one "
            "command",
        ),
        (
            "a simple argument-less listing command",
            make_workflow(
                command="list-workflows",
                body=".aw/system/workflows/list-workflows/HARNESS.md",
                description="List available workflows",
                arg_hint="none",
            ),
            ha.POLICY_GENERATED_COMMAND,
            "THE FALSIFIER: a classifier answering `skill_entry_point` for everything would satisfy the "
            "row above. A simple command MAY stay a plain generated command, which keeps the skill "
            "surface small - and a small skill surface is what keeps a host's skill selection accurate",
        ),
    )

    def test_each_workflow_shape_gets_the_discovery_policy_it_needs(self):
        wrong = []
        for case, workflow, expected, why in self.POLICIES:
            got = ha.classify_discovery_policy(workflow)
            if got != expected:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected {expected!r}\n"
                    f"    - got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.POLICIES)} workflows were classified wrongly. The two rows are "
            "opposite senses of ONE judgement and neither is safe alone: a classifier answering "
            "`skill_entry_point` for everything passes the lensed row while bloating the skill surface "
            "(which degrades a host's skill selection), and one answering `generated_command` for "
            "everything passes the simple row while making lensed workflows undiscoverable. BOTH rows "
            "failing means the predicate inverted; one failing means its threshold moved. FIX: a lens "
            "is the signal for complexity here, so check what `classify_discovery_policy` reads before "
            "editing either expectation.\n" + "\n".join(wrong),
        )

    #: (case, whether to corrupt the router by appending part of itself, whether findings are REQUIRED,
    #: why this row exists)
    AUTHORITY = (
        (
            "an ordinary router beside a real canonical body",
            False,
            False,
            "THE CLEAN CASE: a router that merely POINTS at the canonical body must not be flagged. "
            "Without this row the check could report findings unconditionally and the corrupted row "
            "below would still pass",
        ),
        (
            "a router with the canonical body inlined into it",
            True,
            True,
            "THE DETECTION THAT MATTERS: the canonical body is the AUTHORITY and the router only "
            "references it, so an inlined copy ships instructions that can go stale and that no review "
            "of the canonical file would ever see. This must be DETECTED, not tolerated",
        ),
    )

    def test_inlined_authority_is_detected_without_flagging_a_clean_router(self):
        wrong = []
        for case, corrupt, expect_findings, why in self.AUTHORITY:
            pkg = ha.build_skill_package(make_workflow())
            if corrupt:
                pkg.main_file_content += "\n" + pkg.main_file_content[:250]
                body = pkg.main_file_content[:250]
            else:
                body = (
                    "STEP 1: Freeze requirements.\nSTEP 2: Execute in scope.\n"
                    "STEP 3: Verify with a fresh session.\n" * 20
                )
            findings = ha.check_authority_not_inlined(pkg, body)
            if bool(findings) is not expect_findings:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected findings: {expect_findings}\n"
                    f"    - got {findings!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`check_authority_not_inlined` was wrong on {len(wrong)} of {len(self.AUTHORITY)} "
            "packages. Both senses share this table because neither is safe alone: a check returning "
            "findings unconditionally passes the corrupted row while making every clean package fail "
            "validation, and one returning none passes the clean row while letting an inlined body "
            "ship. FIX: the canonical body is the AUTHORITY and the router only points at it, so an "
            "undetected inline means a host follows a stale copy nobody reviews - repair the check, "
            "never the expectation.\n" + "\n".join(wrong),
        )

    def test_disabling_skill_leaves_explicit_invocation_usable(self):
        """Kept separate: the claim is about the workflow's usability when the SKILL is OFF.

        Both tables above judge a package as generated; this asserts the escape hatch survives
        disabling, which is a property of the package's relationship to the runtime rather than of its
        content or its classification.
        """
        pkg = ha.build_skill_package(make_workflow())
        self.assertTrue(ha.disabled_skill_still_invocable(pkg))


# --------------------------------------------------------------------------------------------------
# E-04: agy fresh-session verifier doubles
# --------------------------------------------------------------------------------------------------

#: A `VERIFICATIONS` row's `finalize` column when `finalize_run` must REFUSE.
CANNOT_FINALIZE = av.SameSessionCannotFinalizeError


class AgyFreshVerifierTests(unittest.TestCase):
    """What a verification run may conclude, per verification MODE.

    ONE table replaces two tests (`test_fresh_verifier_consumes_packet_and_finalizes`,
    `test_same_session_audit_is_diagnostic_and_cannot_finalize`). Both built the doubles, ran the
    verifier over a packet, and asserted four fields of the result; the MODE is the only thing that
    varied, so it is a column.

    THE TWO MODES MUST SHARE THIS TABLE, because the property worth stating is not what either mode
    does - it is that the SAME packet and the SAME pair of sessions reach OPPOSITE conclusions
    depending on the mode. That is the entire self-verification guard: a fresh session is
    authoritative and may finalize, while a same-session audit is diagnostic and may not. Split in two,
    an implementation that ignored the mode would fail one test in a way that reads as a bug in that
    mode rather than as the guard collapsing.

    THE `finalize` COLUMN IS TWO-VALUED BY NECESSITY and holds either an expected return value or an
    expected EXCEPTION, because the refusal to finalize IS the same-session mode's defining behavior
    and separating it would leave the mode's row asserting only flags. That is a deliberate exception
    to keeping `assertRaises` cases apart: the two pure raise-cases below (an identity collision and a
    non-verifier author) stay separate, since for those the raise is the whole test.
    """

    #: (case, the verification mode, expected is_authoritative, expected can_finalize, expected
    #: diagnostic_only, the expected `finalization` field, either the value `finalize_run` must return
    #: or the exception class it must raise, why this row exists)
    VERIFICATIONS = (
        (
            "a fresh verifier session",
            av.MODE_FRESH_SESSION,
            True,
            True,
            False,
            av.FINAL_VERIFIED,
            av.FINAL_VERIFIED,
            "THE AUTHORITATIVE PATH: a verifier in a genuinely fresh session has not seen the "
            "execution's reasoning, so its verdict is independent and may finalize the run. Without "
            "this row the guard below could be 'nothing may ever finalize', which would make the whole "
            "verification pipeline inert",
        ),
        (
            "a same-session audit",
            av.MODE_SAME_SESSION_AUDIT,
            False,
            False,
            True,
            av.FINAL_NOT_FINALIZED,
            CANNOT_FINALIZE,
            "THE SELF-VERIFICATION GUARD, on the SAME packet and the SAME sessions as the row above - "
            "only the mode differs, which is the whole claim. An audit in the executing session is "
            "useful DIAGNOSTICALLY and must never be authoritative, because a session that just did "
            "the work cannot independently judge it. `finalize_run` must REFUSE rather than return a "
            "weaker verdict, since a returned value would be recorded as a result",
        ),
    )

    def test_each_verification_mode_reaches_the_opposite_conclusion_on_one_packet(self):
        wrong = []
        authoritative_rows_broken = 0
        diagnostic_rows_broken = 0
        for (
            case,
            mode,
            authoritative,
            can_finalize,
            diagnostic_only,
            finalization,
            finalize,
            why,
        ) in self.VERIFICATIONS:
            exec_dbl, verifier_dbl = av.make_execution_and_verifier_doubles("run-modes")
            packet = make_verifier_packet()
            result = av.run_fresh_verifier(
                packet, exec_dbl.identity, verifier_dbl.identity, mode=mode
            )
            problems = []
            for field, got, want in (
                ("is_authoritative", result.is_authoritative, authoritative),
                ("can_finalize", result.can_finalize, can_finalize),
                ("diagnostic_only", result.diagnostic_only, diagnostic_only),
            ):
                if got is not want:
                    problems.append(f"{field} is {got!r}, expected {want!r}")
                    # Attribute the failure to the mode's OWN direction, so the message can say
                    # whether the guard collapsed or the pipeline went inert.
                    if authoritative:
                        authoritative_rows_broken += 1
                    else:
                        diagnostic_rows_broken += 1
            if result.finalization != finalization:
                problems.append(
                    f"finalization is {result.finalization!r}, expected {finalization!r}"
                )
            if result.packet_digest != packet.packet_digest:
                problems.append(
                    f"packet_digest is {result.packet_digest!r} but the packet's own digest is "
                    f"{packet.packet_digest!r}, so the result cannot be tied to what was verified"
                )
            if isinstance(finalize, type) and issubclass(finalize, BaseException):
                try:
                    returned = av.finalize_run(result)
                except finalize:
                    pass
                except Exception as exc:  # noqa: BLE001 - the wrong exception is the finding
                    problems.append(
                        f"finalize_run raised {type(exc).__name__} ({exc}), expected "
                        f"{finalize.__name__}"
                    )
                else:
                    problems.append(
                        f"finalize_run RETURNED {returned!r} instead of raising "
                        f"{finalize.__name__}; a returned value here gets recorded as a result, which "
                        "is how a self-audit becomes an authoritative verdict"
                    )
            else:
                got_final = av.finalize_run(result)
                if got_final != finalize:
                    problems.append(
                        f"finalize_run returned {got_final!r}, expected {finalize!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (mode={mode!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        direction = ""
        if diagnostic_rows_broken and not authoritative_rows_broken:
            direction = (
                " The SAME-SESSION row failed, so a session is now authoritative over its own work: "
                "that is the self-verification guard collapsing, and the fresh row proves nothing "
                "while it is true."
            )
        elif authoritative_rows_broken and not diagnostic_rows_broken:
            direction = (
                " The FRESH row failed, so no verification can finalize and the pipeline is inert; the "
                "same-session row is then satisfied trivially."
            )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.VERIFICATIONS)} verification modes reached the wrong "
            f"conclusion.{direction} BOTH rows run the SAME packet through the SAME pair of sessions "
            "and differ only in MODE, so if both fail the mode is being IGNORED - which is the "
            "dangerous case, since a same-session audit would then finalize a run. Read the fields: "
            "flags right but `finalization` wrong means the verdict is computed and then recorded "
            "wrongly; a `packet_digest` mismatch means the result cannot be tied to what was verified, "
            "so no audit trail exists at all. FIX: `finalize_run` must RAISE for a same-session audit "
            "rather than return a weaker value, because a returned value gets recorded as a result.\n"
            + "\n".join(wrong),
        )

    def test_execution_and_verifier_have_distinct_sessions(self):
        """Kept separate: the subject is the DOUBLES FACTORY, not a verification run.

        The table above consumes identities the factory produced; this asserts the factory mints two
        DIFFERENT sessions with the two correct roles, which is the precondition every row silently
        relies on and which no row can state.
        """
        exec_dbl, verifier_dbl = av.make_execution_and_verifier_doubles("run-1")
        self.assertNotEqual(
            exec_dbl.identity.session_id, verifier_dbl.identity.session_id
        )
        self.assertEqual(exec_dbl.identity.role, verify_roles.ROLE_EXECUTOR)
        self.assertEqual(verifier_dbl.identity.role, verify_roles.ROLE_VERIFIER)

    def test_fresh_verifier_refuses_same_session_identity(self):
        """Kept separate: an assertRaises whose subject is a COLLIDING identity, not a mode."""
        exec_dbl, _ = av.make_execution_and_verifier_doubles("run-3")
        colliding = av.SessionIdentity(
            session_id=exec_dbl.identity.session_id, role=verify_roles.ROLE_VERIFIER
        )
        packet = make_verifier_packet()
        with self.assertRaises(av.SessionIdentityCollisionError):
            av.run_fresh_verifier(
                packet, exec_dbl.identity, colliding, mode=av.MODE_FRESH_SESSION
            )

    def test_non_verifier_role_cannot_author_decision(self):
        """Kept separate: an assertRaises on the ROLE of the deciding session, a different guard."""
        exec_dbl, _ = av.make_execution_and_verifier_doubles("run-5")
        bad = av.SessionIdentity(session_id="agy-x", role=verify_roles.ROLE_EXECUTOR)
        packet = make_verifier_packet()
        with self.assertRaises(verify_roles.SelfVerificationForbiddenError):
            av.run_fresh_verifier(packet, exec_dbl.identity, bad)

    def test_doubles_never_spawn_agy(self):
        """Kept separate: determinism of REPEATED invocation plus call recording, not one verdict."""
        _, verifier_dbl = av.make_execution_and_verifier_doubles("run-6")
        r1 = verifier_dbl.invoke("verify the packet")
        r2 = verifier_dbl.invoke("verify the packet")
        self.assertEqual(r1["response_id"], r2["response_id"])
        self.assertEqual(len(verifier_dbl.calls), 2)


# --------------------------------------------------------------------------------------------------
# Security tests: loopback/auth, permission denial, external path, secret redaction
# --------------------------------------------------------------------------------------------------


class SecurityTests(unittest.TestCase):
    """The fail-closed negative probes, and the guards whose refusal is an exception.

    ONE table replaces three tests (`test_permission_denial_capability_fails_closed`,
    `test_local_server_requires_auth_loopback`, `test_external_path_negative_probe_refused`). All
    three ran `evaluate_negative_probe` in a temp directory and asserted its fail-closed fields, so
    the PROBE CLASS is the only thing that varied.

    Why the table beats the three: these are the three fail-closed properties the capability registry
    stakes its promotions on, and one harness evaluates all of them. A regression in that harness
    breaks every row at once, which is the shape of the real risk and is what a single failure naming
    all three conveys.

    EVERY ROW ASSERTS `side_effect_prevented` AS WELL AS `fail_closed_observed`, WHICH IS STRICTER
    THAN THE TESTS IT REPLACES. The server-auth test asserted only that a refusal was observed; the
    harness does in fact report the side effect prevented for it too (verified against real output),
    and the pair is what the claim needs: a host that REPORTS a refusal after already writing has not
    failed closed, and asserting the report alone cannot tell those apart.
    """

    #: (the probe class, why this row exists)
    PROBES = (
        (
            hcr.NEGATIVE_PROBE_DENIED_PERMISSION,
            "A DENIED PERMISSION MUST HALT THE MUTATION, not be reported and then ignored. This is the "
            "probe the registry's permission-gated promotions rest on: if a host proceeds after a "
            "denial, no permission claim about it means anything",
        ),
        (
            hcr.NEGATIVE_PROBE_SERVER_AUTH,
            "AN UNAUTHENTICATED REQUEST TO THE LOCAL SERVER MUST BE REJECTED. A local daemon is "
            "reachable by anything running as the user, so 'it is only on loopback' is not "
            "authentication - and a server that answered unauthenticated requests would expose every "
            "capability the host has",
        ),
        (
            hcr.NEGATIVE_PROBE_EXTERNAL_PATH_REFUSAL,
            "A PATH ESCAPING THE REPOSITORY BOUNDARY MUST BE REFUSED, which is the containment "
            "property every isolated execution depends on. Kept beside the other two so the three "
            "fail-closed guarantees are browsable as the SET the registry actually stakes its "
            "promotions on",
        ),
    )

    def test_every_negative_probe_is_observed_to_fail_closed_with_no_side_effect(self):
        wrong = []
        for probe, why in self.PROBES:
            with tempfile.TemporaryDirectory() as tmp:
                res = hcr.evaluate_negative_probe(probe, "opencode", "1.0.0", tmp)
            problems = []
            if not res.fail_closed_observed:
                problems.append(
                    f"fail_closed_observed is {res.fail_closed_observed!r}; the refusal was not "
                    f"observed at all (rejection_evidence={res.rejection_evidence!r})"
                )
            if not res.side_effect_prevented:
                problems.append(
                    f"side_effect_prevented is {res.side_effect_prevented!r}; a host that REPORTS a "
                    "refusal after already writing has not failed closed, and the report alone cannot "
                    "distinguish the two"
                )
            if not res.rejection_evidence:
                problems.append(
                    "no rejection_evidence was recorded, so the refusal cannot be shown to anyone "
                    "later; a probe result with no evidence is an unverifiable claim"
                )
            if problems:
                wrong.append(
                    f"  {probe}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.PROBES)} negative probes did not fail closed. ONE harness "
            "evaluates all three, so read the grouping: EVERY row failing means the harness itself "
            "broke (check it before suspecting three independent regressions), while one row means "
            "that specific guard did. FIX: `fail_closed_observed` true with `side_effect_prevented` "
            "false is the dangerous combination and must never be accepted as a pass - it is exactly a "
            "host that reports a refusal after the write already happened. No row here may be relaxed "
            "to a single-field assertion, because these three properties are what the capability "
            "registry stakes its promotions on.\n" + "\n".join(wrong),
        )

    def test_external_path_refusal_via_assert_contained(self):
        """Kept separate: an assertRaises, paired with the acceptance it is the negation of."""
        with tempfile.TemporaryDirectory() as tmp:
            base = ha.assert_isolated_base(tmp)
            inside = base / "skills" / "assess" / "SKILL.md"
            # Contained path is accepted.
            self.assertEqual(ha.assert_contained(inside, base), inside.resolve())
            # An external path (escaping the base) is refused fail-closed.
            with self.assertRaises(ha.SafetyError):
                ha.assert_contained("/etc/passwd", base)

    def test_isolated_base_refuses_real_home(self):
        """Kept separate: an assertRaises whose subject is the REAL home directory, not a fixture."""
        with self.assertRaises(ha.SafetyError):
            ha.assert_isolated_base(str(Path.home()))

    def test_secret_redaction_in_adapter_reasons(self):
        """Kept separate: the subject is `RedactionPolicy`, not an adapter or a probe.

        The secret-shaped token is BUILT AT RUNTIME from character codes on purpose: a literal
        credential-shaped string in a test file trips the `gitleaks` commit hook, whose only
        suppression mechanism is a line-number fingerprint that rots on the next edit to this file.
        """
        token = (
            "sk-"
            + "".join(chr(c) for c in (83, 69, 67, 82, 69, 84))
            + "-"
            + "".join(chr(c) for c in (84, 79, 75, 69, 78))
        )
        policy = RedactionPolicy(patterns=[token])
        payload = {"reason": f"probe failed with token {token} in log"}
        redacted, was = policy.redact(payload)
        self.assertTrue(was)
        self.assertNotIn(token, redacted["reason"])
        self.assertIn("[REDACTED]", redacted["reason"])


# --------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------


def _find_source_root() -> Path:
    """Locate the canonical workflow source root (`.aw/system/workflows`)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".aw" / "system" / "workflows"
        if (candidate / "index.md").is_file():
            return candidate
        legacy = parent / ".agents" / "workflows"
        if (legacy / "index.md").is_file():
            return legacy
    raise unittest.SkipTest("no workflow source root with index.md found")


if __name__ == "__main__":
    unittest.main()
