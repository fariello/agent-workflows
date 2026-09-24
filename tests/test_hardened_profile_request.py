"""The REQUEST PATH for the hardened OS-sandbox profile (`hardreach` Order 01, `n5qca5`).

WHAT WAS WRONG, because it decides what these tests must falsify. The hardened profile worked, was
tested, and NOTHING COULD ASK FOR IT. `oc_runipd._apply_execution_profile` read
`options["execution_profile"]`, and no code in the package ever assigned that key: its single
occurrence outside the reader was a COMMENT, and no CLI flag existed. So
`select_execution_profile(None, caps)` returned `"default"` on every real invocation, the sandbox
branch below it was unreachable in production, and it was unreachable even on a host whose EXECUTED
probe reports `supports_os_sandbox=True`. This suite exists to keep a WRITER in place.

THE FOUR CLAIMS, each a way the request path could be broken while `test_host_sandbox_profile.py`
(which tests the sandbox itself) stayed green:

1. THE REQUEST IS CONSUMED, not merely stored. A profile field that reached `state.json` and never
   reached `select_execution_profile` would look correct in every state dump and enforce nothing.
2. AN UNSUPPORTED HOST REFUSES, deterministically. Asserted with a CONSTRUCTED all-False
   `HostSandboxCapabilities`, never by finding a host without a sandbox, so it fails on macOS,
   Windows and Linux alike. A test that merely SKIPS where there is no sandbox proves nothing.
3. THE NO-LANE REFUSAL FIRES. `_apply_execution_profile` raises when hardened is requested with no
   `work_dir`, because there would be no lane boundary to enforce. A request path makes that branch
   reachable for the FIRST time, so it needs a test rather than remaining incidentally dead.
4. THE DEFAULT PATH IS BYTE-UNCHANGED. An invocation that requests nothing must produce the identical
   `argv`, the identical frozen `options`, and the identical provenance map it did before this field
   existed.

WHAT THIS SUITE DELIBERATELY DOES NOT TEST: what the sandbox DOES once selected. The jail
construction, the probe ladder, and the discovery-then-execution split are `1o4eif`'s work and are
covered by `test_host_sandbox_profile.py`. This plan added a writer only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import oc_runipd as driver
from agent_workflows import runner_profiles as rp
from agent_workflows.host_sandbox_profile import (
    HardModeUnavailableError,
    HostSandboxCapabilities,
    SandboxProfileError,
    select_execution_profile,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Synthetic identifier only: a real provider/model string in a tracked file would disclose
# institutional topology, which is the reason the profile store is user-local at all.
JAIL_MODEL = "synthetic/jail-test"


def _store(tmp: Path, doc: dict) -> dict:
    """Write `runner-profiles.json` into an ISOLATED XDG dir; return the env overlay.

    Isolation matters: without it these tests would read the developer's real store, and their
    results would depend on whether that developer happens to request hardened mode.
    """

    cfg_dir = tmp / "xdg" / "agent-workflows"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "runner-profiles.json").write_text(json.dumps(doc), encoding="utf-8")
    return {"XDG_CONFIG_HOME": str(tmp / "xdg")}


def _hardened_doc(version: int = 2) -> dict:
    return {
        "schema_version": version,
        "profiles": {
            "jail": {
                "runner": "oc",
                "model": JAIL_MODEL,
                "execution_profile": "hardened",
            }
        },
    }


# ==================================================================================================
# The schema half: the field is storable, closed, and does not widen the storable surface
# ==================================================================================================


class ExecutionProfileFieldTests(unittest.TestCase):
    """The stored field: accepted, CLOSED, and refused in every shape that would widen the fence."""

    def test_the_field_round_trips_through_the_real_schema(self):
        cfg = rp.from_document(_hardened_doc())
        self.assertEqual(cfg.profiles["jail"].execution_profile, "hardened")
        # Serialization is exact and OMITS the key when absent, which is what keeps an existing
        # store's bytes (and therefore its `config_digest`) unchanged.
        self.assertEqual(
            cfg.profiles["jail"].to_document(),
            {
                "runner": "oc",
                "model": JAIL_MODEL,
                "execution_profile": "hardened",
            },
        )
        plain = rp.from_document(
            {
                "schema_version": 2,
                "profiles": {"p": {"runner": "oc", "model": JAIL_MODEL}},
            }
        )
        self.assertIsNone(plain.profiles["p"].execution_profile)
        self.assertNotIn("execution_profile", plain.profiles["p"].to_document())

    def test_the_vocabulary_is_closed_and_matches_the_resolver(self):
        """The two-member enum is DUPLICATED as a literal in `runner_profiles`, so pin it.

        `runner_profiles` deliberately does not import `host_sandbox_profile` (that module runs real
        sandbox subprocesses, and this one promises no subprocess), so the vocabulary is a copy. This
        is the assertion that keeps the copy from drifting from the resolver that consumes it.
        """

        self.assertEqual(rp.EXECUTION_PROFILE_NAMES, ("default", "hardened"))
        caps = HostSandboxCapabilities(platform="linux", supports_os_sandbox=True)
        for name in rp.EXECUTION_PROFILE_NAMES:
            with self.subTest(name=name):
                self.assertEqual(select_execution_profile(name, caps), name)

    def test_a_path_an_argv_fragment_and_a_permission_expression_are_all_REFUSED(self):
        """The fence this field sits next to: `permission`/`permissions` are forbidden BY NAME.

        So the field's VALUE SPACE has to be closed, and it is asserted here in the shapes that would
        matter if it were not: a filesystem path or root (which would let a stored value say what is
        writable), an argv fragment (the injection surface `args`/`argv` are forbidden for), and a
        permission expression (the shape of the forbidden keys themselves).
        """

        refused = {
            "a filesystem path": "/etc/passwd",
            "an absolute lane root": "/srv/checkouts/repo/.aw/worktrees/lane",
            "a relative path": "../../outside",
            "an argv fragment": "--dangerously-skip-permissions",
            "a shell fragment": "hardened; rm -rf /",
            "a permission expression": "write:/tmp",
            "an edit-permission expression": "edit=allow",
            "a near miss in case": "HARDENED",
            "a near miss in whitespace": "hardened ",
            "an unknown profile name": "semi-hardened",
            "the empty string": "",
            "a mapping (structure)": {"profile": "hardened"},
            "a list (structure)": ["hardened"],
            "a bool": True,
            "an int": 1,
        }
        accepted = []
        for why, value in refused.items():
            with self.subTest(shape=why):
                try:
                    rp.parse_profile(
                        "x",
                        {
                            "runner": "oc",
                            "model": JAIL_MODEL,
                            "execution_profile": value,
                        },
                    )
                except rp.ProfileSchemaError:
                    continue
                accepted.append(f"{why}: {value!r}")
        self.assertEqual(
            accepted,
            [],
            "these value shapes were ACCEPTED into the storable surface: "
            + "; ".join(accepted)
            + ". The field must be a NAME from a two-member enum. A path or root would let a "
            "stored value say WHICH paths are writable, which is exactly why `permission` and "
            "`permissions` are in FORBIDDEN_PROFILE_KEYS; an argv fragment is why `args`/`argv` "
            "are. FIX the validator, never the assertion.",
        )

    def test_the_storable_surface_did_not_widen_beyond_this_one_name(self):
        """The two properties the pinned fence tests state, re-asserted from the other direction."""

        self.assertEqual(
            rp.ALLOWED_PROFILE_KEYS & rp.FORBIDDEN_PROFILE_KEYS, frozenset()
        )
        for adjacent in ("permission", "permissions", "args", "argv", "env"):
            with self.subTest(key=adjacent):
                self.assertIn(adjacent, rp.FORBIDDEN_PROFILE_KEYS)
                self.assertNotIn(adjacent, rp.ALLOWED_PROFILE_KEYS)

    def test_a_schema_version_1_document_still_loads_with_NO_version_bump(self):
        """`SUPPORTED_SCHEMA_VERSIONS` is {1, 2} and NOTHING is migrated, so no bump was needed.

        The reader is deliberately version-AGNOSTIC about a FIELD, which is recorded in the module for
        `verify_with` and applies unchanged here. Asserted in both halves: a v1 document carrying the
        new field loads and keeps declaring 1, and the written version is still 2.
        """

        v1 = rp.from_document(_hardened_doc(version=1))
        self.assertEqual(v1.schema_version, 1)
        self.assertEqual(
            rp.resolve(v1, runner="oc", profile="jail").execution_profile, "hardened"
        )
        self.assertEqual(rp.SCHEMA_VERSION, 2)
        self.assertEqual(sorted(rp.SUPPORTED_SCHEMA_VERSIONS), [1, 2])
        # A pre-existing v1 store WITHOUT the field is byte-identical through a load/serialize
        # round trip, which is the compatibility claim that matters to an operator who has one.
        legacy_doc = {
            "schema_version": 1,
            "defaults": {"profiles": {"oc": "gem"}},
            "profiles": {
                "gem": {"runner": "oc", "model": JAIL_MODEL, "variant": "high"}
            },
        }
        self.assertEqual(rp.from_document(legacy_doc).to_document(), legacy_doc)


class ExecutionProfileResolutionTests(unittest.TestCase):
    """The RESOLVER half: which tiers speak, and what an absent field leaves untouched."""

    def test_a_named_profile_and_a_default_profile_both_supply_the_request(self):
        cfg = rp.from_document(_hardened_doc())
        named = rp.resolve(cfg, runner="oc", profile="jail")
        self.assertEqual(named.execution_profile, "hardened")
        self.assertEqual(named.provenance["execution_profile"], rp.PROVENANCE_PROFILE)

        with_default = rp.from_document(
            {**_hardened_doc(), "defaults": {"profiles": {"oc": "jail"}}}
        )
        unqualified = rp.resolve(with_default, runner="oc")
        self.assertEqual(unqualified.execution_profile, "hardened")
        self.assertEqual(
            unqualified.provenance["execution_profile"],
            rp.PROVENANCE_DEFAULT_PROFILE,
        )
        for value in (named.provenance, unqualified.provenance):
            self.assertIn(value["execution_profile"], rp.PROVENANCE_VALUES)

    def test_absent_leaves_the_resolved_record_AND_the_provenance_map_unchanged(self):
        """The invariance claim at the resolver level: absent adds NOTHING, not even a key.

        An unconditional provenance entry would change the map of every resolution ever performed, for
        a field that said nothing. The shipped suites assert that map's exact key set, so this is the
        assertion that says the omission is intended rather than incidental.
        """

        cfg = rp.from_document(
            {
                "schema_version": 2,
                "profiles": {"p": {"runner": "oc", "model": JAIL_MODEL}},
            }
        )
        got = rp.resolve(cfg, runner="oc", profile="p")
        self.assertIsNone(got.execution_profile)
        self.assertEqual(
            sorted(got.provenance),
            ["agent", "model", "runner", "validate", "variant", "verify_with"],
        )


# ==================================================================================================
# The DRIVER half: the request is consumed, and the refusals fire
# ==================================================================================================


class RequestReachesTheResolverTests(unittest.TestCase):
    """Claim 1: the stored request is CONSUMED by `select_execution_profile`, not merely frozen."""

    def test_the_frozen_option_is_what_the_seam_passes_to_the_resolver(self):
        """The end of the wire: whatever `initialize_run` froze is what the resolver is asked about.

        Spying on `select_execution_profile` is the point. Asserting only on `state.json` would pass
        for a field that is stored and never read, which is precisely the defect class this plan
        exists to remove (the reader existed; the writer did not).
        """

        seen: list = []

        def _spy(requested, capabilities):
            seen.append(requested)
            return select_execution_profile(requested, capabilities)

        caps = HostSandboxCapabilities(
            platform="linux", supports_os_sandbox=True, sandbox_mechanism="landlock"
        )
        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp) / "lane"
            lane.mkdir()
            state = {
                "options": {"execution_profile": "hardened"},
                "repo": str(Path(tmp)),
                "run_id": "r1",
                "control_root": str(Path(tmp) / "control"),
            }
            with (
                mock.patch.object(driver, "select_execution_profile", _spy),
                mock.patch.object(
                    driver, "detect_host_capabilities", lambda host: caps
                ),
                mock.patch.object(
                    driver, "enter_sandbox", lambda argv, *a, **k: ["JAILED", *argv]
                ),
            ):
                out = driver._apply_execution_profile(
                    state,
                    {"id6": "abc123"},
                    ["opencode", "run"],
                    str(lane),
                    str(lane),
                )
        self.assertEqual(
            seen,
            ["hardened"],
            "the frozen request never reached select_execution_profile, so the field is stored "
            "and inert: exactly the defect this plan removes, one layer further along",
        )
        self.assertEqual(out[0], "JAILED", "the launch argv was not wrapped")

    def test_the_whole_chain_from_a_real_store_to_the_frozen_option(self):
        """Store file -> `resolve_launch_pair` -> `state["options"]`, with no mocked layer between.

        This is the assertion that would have FAILED before this plan: `resolve_launch_pair` produced
        no such value and `initialize_run` wrote no such key, so the reader's key had no writer.
        """

        with tempfile.TemporaryDirectory() as tmp:
            env = _store(Path(tmp), _hardened_doc())
            args = argparse.Namespace(
                profile="jail",
                model=None,
                variant=None,
                agent=None,
                validate=None,
                verify_with=None,
            )
            with mock.patch.dict(os.environ, env):
                executor, verifier = driver.resolve_launch_pair(args)
        self.assertEqual(executor.execution_profile, "hardened")
        self.assertIsNone(verifier)
        record = driver.launch_profile_record(executor)
        self.assertEqual(record["execution_profile"], "hardened")
        self.assertEqual(record["provenance"]["execution_profile"], "profile")

    def test_the_audit_record_omits_the_key_when_nothing_asked(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = _store(
                Path(tmp),
                {
                    "schema_version": 2,
                    "profiles": {"p": {"runner": "oc", "model": JAIL_MODEL}},
                },
            )
            args = argparse.Namespace(
                profile="p",
                model=None,
                variant=None,
                agent=None,
                validate=None,
                verify_with=None,
            )
            with mock.patch.dict(os.environ, env):
                executor, _ = driver.resolve_launch_pair(args)
        self.assertIsNone(executor.execution_profile)
        self.assertNotIn("execution_profile", driver.launch_profile_record(executor))


class RefusalTests(unittest.TestCase):
    """Claims 2 and 3: an unsupported host, and a request with no lane, both REFUSE."""

    def test_an_unsupported_host_refuses_DETERMINISTICALLY_on_every_platform(self):
        """Claim 2, built from a CONSTRUCTED capability object rather than from this host.

        `select_execution_profile` takes capabilities as a PARAMETER, so an all-False
        `HostSandboxCapabilities` is sufficient and this assertion holds on Linux, macOS and Windows
        alike. A version of this test that skipped where no sandbox exists would prove nothing and
        must never be reported as a pass.
        """

        incapable = HostSandboxCapabilities()
        self.assertFalse(incapable.supports_os_sandbox)
        with self.assertRaises(HardModeUnavailableError):
            select_execution_profile("hardened", incapable)
        # And it does NOT silently answer "default", which is the degradation the raise exists to
        # prevent: a caller who got "default" back would run unsandboxed believing it had asked.
        self.assertEqual(select_execution_profile(None, incapable), "default")

    def test_the_request_path_refuses_on_an_unsupported_host_and_spawns_NOTHING(self):
        """The same refusal reached THROUGH the new request path, with a spawn tripwire.

        A refusal that still launched the worker would be the worst outcome available: the operator
        asked for a jail, saw an error, and the agent ran anyway.
        """

        incapable = HostSandboxCapabilities(platform="darwin")
        spawned: list = []

        class _Tripwire:
            def __init__(self, *a, **k):
                spawned.append(a)
                raise AssertionError("an unsandboxed worker must NEVER be spawned")

        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp) / "lane"
            lane.mkdir()
            with (
                mock.patch.object(
                    driver, "detect_host_capabilities", lambda host: incapable
                ),
                mock.patch.object(subprocess, "Popen", _Tripwire),
            ):
                with self.assertRaises(HardModeUnavailableError):
                    driver._apply_execution_profile(
                        {
                            "options": {"execution_profile": "hardened"},
                            "repo": str(Path(tmp)),
                            "run_id": "r1",
                        },
                        {"id6": "abc123"},
                        ["opencode", "run"],
                        str(lane),
                        str(lane),
                    )
        self.assertEqual(spawned, [])

    def test_a_request_with_NO_LANE_refuses_because_there_is_no_boundary(self):
        """Claim 3: the `work_dir`-less branch, reachable for the FIRST time now a writer exists.

        Hardened mode binds writes to the lane worktree. A turn in the main checkout has no lane, so
        there is nothing to enforce and the honest answer is a refusal rather than a jail that
        contains the whole repository.
        """

        caps = HostSandboxCapabilities(
            platform="linux", supports_os_sandbox=True, sandbox_mechanism="landlock"
        )
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                driver, "detect_host_capabilities", lambda host: caps
            ):
                with self.assertRaises(SandboxProfileError) as ctx:
                    driver._apply_execution_profile(
                        {
                            "options": {"execution_profile": "hardened"},
                            "repo": str(Path(tmp)),
                            "run_id": "r1",
                        },
                        {"id6": "abc123"},
                        ["opencode", "run"],
                        str(tmp),
                        None,
                    )
        self.assertIn("isolated lane", str(ctx.exception))

    def test_an_unknown_requested_name_refuses_even_on_a_capable_host(self):
        capable = HostSandboxCapabilities(platform="linux", supports_os_sandbox=True)
        with self.assertRaises(SandboxProfileError):
            select_execution_profile("semi-hardened", capable)


class DefaultPathInvarianceTests(unittest.TestCase):
    """Claim 4: an invocation that requests nothing is unchanged, argv included."""

    def test_requesting_nothing_produces_the_IDENTICAL_argv(self):
        """Byte-for-byte, and on a host that CAN enforce, so the check is not passing by inability."""

        capable = HostSandboxCapabilities(
            platform="linux", supports_os_sandbox=True, sandbox_mechanism="landlock"
        )
        argv = ["opencode", "run", "--model", "synthetic/x", "--", "prompt text"]
        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp) / "lane"
            lane.mkdir()
            with mock.patch.object(
                driver, "detect_host_capabilities", lambda host: capable
            ):
                for options in ({}, {"execution_profile": "default"}):
                    with self.subTest(options=options):
                        out = driver._apply_execution_profile(
                            {
                                "options": dict(options),
                                "repo": str(Path(tmp)),
                                "run_id": "r1",
                            },
                            {"id6": "abc123"},
                            list(argv),
                            str(lane),
                            str(lane),
                        )
                        self.assertEqual(out, argv)

    def test_no_PARALLEL_key_and_no_second_sandbox_code_path_were_added(self):
        """The negative proof: one key, one seam, one resolver call.

        A second key or a second wrapping site would fork the one place hardened mode is decided,
        which is the failure mode this plan's scope explicitly forbids.
        """

        source = (REPO_ROOT / "agent_workflows" / "oc_runipd.py").read_text(
            encoding="utf-8"
        )
        # Counted with the OPENING PAREN, so a bare import (which has none) is not counted and the
        # number is the number of CALL sites rather than of mentions.
        self.assertEqual(
            source.count("select_execution_profile("),
            1,
            "expected exactly ONE call site; a second call means a second place hardened mode is "
            "decided, which is the fork this plan's scope forbids",
        )
        self.assertEqual(
            source.count("_apply_execution_profile("),
            2,
            "expected exactly the definition and ONE invocation in the launch path",
        )
        self.assertEqual(
            source.count("enter_sandbox("),
            1,
            "expected exactly ONE wrapping site",
        )
        # And no near-miss key name crept in beside the real one.
        for parallel in (
            "sandbox_profile",
            "hardened_mode",
            "execution-profile",
            "use_sandbox",
        ):
            with self.subTest(key=parallel):
                self.assertNotIn(f'"{parallel}"', source)


class OpencodeOnlyByConstructionTests(unittest.TestCase):
    """The asymmetry, MEASURED rather than asserted from the docs, and named where it is honest."""

    def test_the_agy_host_reads_no_profile_identity_at_all(self):
        agy = (REPO_ROOT / "agent_workflows" / "agy_runipd.py").read_text(
            encoding="utf-8"
        )
        for symbol in (
            "execution_profile",
            "host_sandbox_profile",
            "runner_profiles",
            "resolve_launch_profile",
            "launch_profile",
        ):
            with self.subTest(symbol=symbol):
                self.assertEqual(
                    agy.count(symbol),
                    0,
                    f"{symbol} now appears in agy_runipd; the opencode-only claim in "
                    "docs/runner-profiles.md and in host_sandbox_profile's contract must be "
                    "re-measured and rewritten in the SAME change",
                )

    def test_the_user_facing_doc_states_the_limit_the_refusal_and_the_silent_agy_case(
        self,
    ):
        """The doc is the only place a user learns all three, so all three are pinned.

        The ORDER matters and is asserted: the platform limit must appear WITH the capability rather
        than after it, so a macOS reader learns it before deciding to use the field.
        """

        text = (REPO_ROOT / "docs" / "runner-profiles.md").read_text(encoding="utf-8")
        self.assertIn("execution_profile", text)
        heading = "## Asking for the OS sandbox (Linux only, and it refuses elsewhere)"
        self.assertIn(heading, text)
        section = text.split(heading)[1].split("\n## ")[0]
        self.assertIn("LINUX ONLY", section)
        self.assertIn("REFUSES", section)
        self.assertIn("IGNORES IT RATHER THAN REFUSING", section)
        self.assertIn("THE DEFAULT DOES NOT CHANGE", section)
        # The limit is in the HEADING itself and in the first paragraph, so it cannot be read as a
        # trailing caveat. Measured as a position, not merely as presence.
        first_para = section.strip().split("\n\n")[0]
        self.assertIn("LINUX ONLY", first_para)
        # Repository convention for user-facing prose, and a sibling suite enforces it for this file.
        self.assertNotIn("\u2014", section)
        self.assertNotIn("\u2013", section)

    def test_the_module_contract_says_HOW_hardened_mode_is_requested(self):
        """A contract describing a capability with no reachable request path is what produced this."""

        from agent_workflows import host_sandbox_profile as hsp

        doc = hsp.__doc__ or ""
        self.assertIn("execution_profile", doc)
        self.assertIn("runner-profiles.json", doc)
        self.assertIn("NO CLI FLAG", doc.upper())
        self.assertIn("IGNORES RATHER THAN REFUSES", doc.upper())


if __name__ == "__main__":
    unittest.main()
