#!/usr/bin/env python3
"""THE ONE PLAN RECORD AND ITS ONE READER (rununify Order 06, `sy7uwh`).

WHAT THIS FILE PROVES, and why the payoff needs its own guard rather than riding on the inverted pins.
Before this plan, the two host runners built DIFFERENT `PlanRecord` NamedTuples - `oc_runipd`'s carried
a `kind` field `agy_runipd`'s lacked - which forced `parse_plan_file` and `build_dynamic_manifest` to
stay forked and forced the antigravity host to RE-READ `- Kind:` from disk for information the opencode
host already had in hand. `818uru` pinned that split on purpose and wrote a test forbidding
unification, saying in the test itself that unifying was "a class (c) reconciliation for a later child".
This plan is that child.

THE FAILURE MODE THIS FILE EXISTS FOR IS SILENT AND TYPE-SHAPED, which is the whole reason
field-presence assertions are not enough. `818uru`'s own pinned test warned that a shared constructor
which DROPPED `kind` "would silently disable orchestrator detection" - not crash, not raise, just
quietly derive `execute` for a plan the runner is supposed to retire administratively, spending a paid
agent turn on a plan that authors no code. So the tests below assert the orchestrator DERIVATION END TO
END on both hosts, through the real `discover_plans` -> `build_dynamic_manifest` -> `action_for` path,
and `NonVacuityControls` proves those assertions can actually fail.

THE FOUR PROPERTIES, none of which implies another:

  1. ONE RECORD TYPE, ONE READER. Object identity (not merely equal shapes), plus a REPO-WIDE AST scan
     that fails if either symbol is ever re-forked anywhere in the package. Identity alone would pass
     while a stale duplicate definition sat in a file shadowed by a later import.
  2. `kind` POPULATED FROM A REAL PLAN FILE ON BOTH HOSTS, and no field lost in the merge.
  3. ORCHESTRATOR DETECTION STILL WORKS END TO END ON BOTH HOSTS. This is the property the whole
     coupling existed to serve, and the one a field check cannot substitute for.
  4. THE LEGACY-MANIFEST FALLBACK, COVERED FOR THE FIRST TIME. See below; this is the case that made
     the obvious implementation of this plan dangerous.

WHY (4) MATTERS MORE THAN ITS SIZE SUGGESTS. `agy_runipd._plan_kind` had TWO callers and only ONE of
them was the record-split workaround its docstring described. The other was a LEGACY-MANIFEST FALLBACK:
when a HAND-WRITTEN manifest carries no `kind` key (the shipped `tools/ipdrunner/*-driver-manifest.json`
is such a manifest), the antigravity host re-read the plan file rather than deriving `execute` for an
approved orchestrator. The opencode host had NO equivalent. Measured before this plan: given such a
manifest naming an approved orchestrator, `aw agy run` derived `orchestrate` and correctly retired it
while `aw oc run` derived `execute` - the exact defect orchretire-03 (`pgq326`) fixed, reintroduced on
one host, on a path NO test covered. Deleting the helper outright (which this plan's checklist
originally instructed) would therefore have looked FREE: every existing test would have stayed green.
`sy7uwh` OQ-03 resolved this by giving the fallback to BOTH hosts, and the tests here pin it for both.
"""

from __future__ import annotations

import ast
import json
import pathlib
import tempfile
import unittest

from agent_workflows import agy_runipd, oc_runipd, runner_shared

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "agent_workflows"

#: Both hosts, always. A one-host assertion is precisely how `818uru` recorded that a guard written for
#: one runner let the other re-fork four symbols and DRIFT one of them.
HOSTS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

#: The symbols this plan unified, each of which must now have exactly ONE definition in the package and
#: be the SAME object on both hosts.
UNIFIED = (
    "PlanRecord",
    "parse_plan_file",
    "build_dynamic_manifest",
    "_read_kind",
    "_read_item_dependencies",
    "_read_from_backlog",
    "_PLAN_FILENAME_RE",
)

#: THE ALLOWLIST FOR THE REPO-WIDE SCAN, and it is a NAME COLLISION rather than a re-fork.
#:
#: `agent_workflows/plans.py` defines its own `PlanRecord` with fields
#: `path`/`area`/`disposition`/`status`/`set_id`/`order` - a DIFFERENT concept (a plans-tree inventory
#: row) with no importers of that name, unrelated to the runners' plan record. The `rununify`
#: orchestrator's F10 requires the single-definition check be REPO-WIDE across `agent_workflows/*.py`
#: rather than pairwise between the two runners, precisely because a pairwise check passes while a third
#: copy sits in another module. So this scan WILL find that type, and the correct response is to
#: allowlist it WITH its reason: "fixing" it would unify two unrelated concepts that merely share a
#: name (a behavior change wearing a de-duplication's clothes), and narrowing the scan to a pairwise
#: check would remove exactly the coverage F10 demands.
ALLOWLISTED_COLLISIONS = {
    ("plans.py", "PlanRecord"): (
        "an UNRELATED plans-tree inventory row (path/area/disposition/status/set_id/order) with no "
        "importers of that name; a name collision, not a re-fork of the runners' record"
    ),
}


def _plan_text(id6: str, kind: str, status: str = "approved") -> str:
    return (
        f"# IPD: synthetic {id6}\n\n"
        f"- Date: 2026-09-17\n"
        f"- Kind: {kind}\n"
        f"- Id: {id6}\n"
        f"- Set: recset\n"
        f"- Order: {0 if kind == 'orchestrator' else 1}\n"
        f"- Status: {status}\n"
    )


def _repo_with(tmp: str, *plans: tuple[str, str]) -> pathlib.Path:
    """A repo containing one plan file per ``(id6, kind)`` pair. Returns its root."""
    root = pathlib.Path(tmp)
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    for id6, kind in plans:
        order = 0 if kind == "orchestrator" else 1
        name = f"20260917-recset-{order:02d}-{id6}-synthetic.ipd.md"
        (d / name).write_text(_plan_text(id6, kind), encoding="utf-8")
    return root


def _top_level_definitions(path: pathlib.Path) -> dict[str, int]:
    """Every TOP-LEVEL definition or bare-name binding in ``path``, mapped to its line.

    AST-based rather than grep-based, per the orchestrator's own instruction that a `grep` proof "could
    never fail". A module-level assignment counts, because a re-forked CONSTANT (`_PLAN_FILENAME_RE`) is
    the same defect as a re-forked function - that is how `render_stream`'s ANSI constants came back. An
    `import X` does NOT count: importing the owner's object is the fix, not the violation.
    """
    found: dict[str, int] = {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:  # pragma: no cover - a broken module is a different failure
        return found
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.setdefault(node.name, node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found.setdefault(target.id, node.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.setdefault(node.target.id, node.lineno)
    return found


class ThereIsExactlyOneRecordAndOneReader(unittest.TestCase):
    """Property 1: object identity AND repo-wide single definition. Neither implies the other."""

    def test_both_hosts_bind_the_SAME_object_for_every_unified_symbol(self):
        for name in UNIFIED:
            with self.subTest(symbol=name):
                shared = getattr(runner_shared, name, None)
                self.assertIsNotNone(
                    shared, f"`runner_shared` must own `{name}` after `sy7uwh`"
                )
                for label, mod in HOSTS:
                    self.assertIs(
                        getattr(mod, name, None),
                        shared,
                        f"{label}.{name} is not `runner_shared.{name}`; a copy that merely "
                        "looks the same is the state this plan exists to end",
                    )

    def test_the_record_is_the_headline_identity(self):
        """Stated on its own line because it is the plan's whole claim, in one assertion."""
        self.assertIs(oc_runipd.PlanRecord, agy_runipd.PlanRecord)

    def test_neither_host_still_DEFINES_a_unified_symbol(self):
        """Identity alone passes while a stale duplicate sits in the file, shadowed by a later import.

        That is a trap rather than a fix: the shadowed body is what a reader edits, and the edit has no
        effect. So the AST half is separate and mandatory.
        """
        violations = []
        for label, mod in HOSTS:
            defined = _top_level_definitions(pathlib.Path(str(mod.__file__)))
            for name in UNIFIED:
                line = defined.get(name)
                if line is not None:
                    violations.append(f"{label}.py:{line} re-defines `{name}`")
        self.assertEqual(
            violations,
            [],
            "RE-FORK FOUND. Import from `runner_shared` instead of keeping a second copy; "
            "a fix to the shared definition does not reach a copy.\n  "
            + "\n  ".join(violations),
        )

    def test_the_repo_wide_scan_finds_exactly_one_definition_per_symbol(self):
        """REPO-WIDE across `agent_workflows/*.py`, not pairwise (the orchestrator's F10).

        A pairwise two-runner comparison passes while a third copy sits in another module, which is
        exactly the state F10 measured for `render_stream`. The one allowlisted entry is a NAME
        COLLISION with its reason recorded in `ALLOWLISTED_COLLISIONS`.
        """
        sites: dict[str, list[str]] = {n: [] for n in UNIFIED}
        for path in sorted(PACKAGE.glob("*.py")):
            for name, line in _top_level_definitions(path).items():
                if name in sites:
                    sites[name].append(f"{path.name}:{line}")
        for name in UNIFIED:
            with self.subTest(symbol=name):
                found = sites[name]
                allowed = [
                    s
                    for s in found
                    if (s.split(":")[0], name) in ALLOWLISTED_COLLISIONS
                ]
                counted = [s for s in found if s not in allowed]
                self.assertEqual(
                    counted,
                    [s for s in counted if s.startswith("runner_shared.py:")],
                    f"`{name}` is defined outside `runner_shared` at {counted}",
                )
                self.assertEqual(
                    len(counted),
                    1,
                    f"`{name}` must have exactly ONE definition; found {counted} "
                    f"(allowlisted collisions excluded: {allowed})",
                )

    def test_the_allowlisted_collision_is_REAL_and_carries_its_reason(self):
        """The allowlist must not be a place to hide a genuine re-fork.

        So each entry is checked to (a) actually exist, (b) carry a non-empty reason, and (c) be a
        DIFFERENT SHAPE from the runners' record - which is what makes it a collision rather than a
        fork. If someone ever allowlists a true copy, (c) fails.
        """
        from agent_workflows import plans as plans_module

        self.assertTrue(
            ALLOWLISTED_COLLISIONS, "the allowlist must be explicit, not empty"
        )
        for (filename, symbol), reason in ALLOWLISTED_COLLISIONS.items():
            with self.subTest(collision=f"{filename}:{symbol}"):
                self.assertIn(
                    symbol,
                    _top_level_definitions(PACKAGE / filename),
                    f"{filename} does not define `{symbol}`; remove the stale allowlist entry",
                )
                self.assertTrue(reason.strip(), "an allowlist entry must state WHY")
        # (c), for the one entry we have: a genuinely different shape.
        self.assertIsNot(plans_module.PlanRecord, runner_shared.PlanRecord)
        self.assertNotEqual(
            set(plans_module.PlanRecord._fields),
            set(runner_shared.PlanRecord._fields),
            "`plans.PlanRecord` now has the runners' shape, so it is no longer a mere name "
            "collision and the allowlist entry's premise has failed",
        )
        self.assertEqual(
            plans_module.PlanRecord._fields,
            ("path", "area", "disposition", "status", "set_id", "order"),
            "the allowlisted type's shape changed; re-check whether it is still unrelated",
        )

    def test_the_record_split_call_site_of_plan_kind_is_GONE(self):
        """`agy_runipd._plan_kind`'s FIRST caller (the record-split workaround) must not exist.

        Checked by AST rather than by the helper's absence, because the helper's SECOND caller was a
        legitimate legacy-manifest fallback that had to SURVIVE (see
        `TheLegacyManifestFallbackWorksOnBothHosts`). "The helper is gone" and "the workaround is gone"
        are different claims and this asserts the second.
        """
        for label, mod in HOSTS:
            with self.subTest(host=label):
                src = pathlib.Path(str(mod.__file__)).read_text(encoding="utf-8")
                calls = [
                    node.lineno
                    for node in ast.walk(ast.parse(src))
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_plan_kind"
                ]
                self.assertEqual(
                    calls,
                    [],
                    f"{label} still calls a private `_plan_kind` at lines {calls}; the record "
                    "carries `kind` now and the legacy fallback is the shared "
                    "`plan_kind_from_file`",
                )

    def test_the_manifest_no_longer_re_reads_the_file_per_plan(self):
        """The measurable payoff: `build_dynamic_manifest` reads `rec.kind`, not the disk.

        Asserted structurally, because "one fewer file read per plan per run" is the concrete cost the
        split imposed and a passing behavior test would not notice its return.
        """
        src = ast.unparse(
            ast.parse(
                pathlib.Path(str(runner_shared.__file__)).read_text(encoding="utf-8")
            )
        )
        body = src.split("def build_dynamic_manifest", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("'kind': rec.kind", body)
        self.assertNotIn("read_text", body)


class TheSharedRecordCarriesEveryFieldBothHostsHad(unittest.TestCase):
    """Property 2: `kind` populated from a real plan file on BOTH hosts, and nothing lost."""

    #: The two PRE-MERGE field sets, as literals measured at `sy7uwh`'s execution HEAD. Kept as data so
    #: a later change that drops a field one host used to have fails HERE, naming the field, rather than
    #: surfacing as a distant `AttributeError`.
    OC_PREMERGE = (
        "id6",
        "setid",
        "status",
        "order",
        "path",
        "rel_path",
        "dependencies",
        "kind",
        "dependency_error",
        "from_backlog",
    )
    AGY_PREMERGE = tuple(n for n in OC_PREMERGE if n != "kind")

    def test_the_shared_shape_is_the_UNION_of_the_two_pre_merge_shapes(self):
        shared = set(runner_shared.PlanRecord._fields)
        self.assertEqual(
            shared,
            set(self.OC_PREMERGE) | set(self.AGY_PREMERGE),
            "the merge must lose nothing and invent nothing (`sy7uwh` OQ-02)",
        )

    def test_oc_was_a_strict_SUPERSET_differing_in_exactly_kind(self):
        """The measurement the unify-toward-oc decision rests on, re-derived rather than trusted."""
        self.assertTrue(set(self.AGY_PREMERGE) < set(self.OC_PREMERGE))
        self.assertEqual(
            set(self.OC_PREMERGE) - set(self.AGY_PREMERGE),
            {"kind"},
        )

    def test_kind_is_populated_from_a_REAL_plan_file_on_both_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"), ("chirec", "child"))
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    found = mod.discover_plans(root)
                    self.assertEqual(found["orcrec"].kind, "orchestrator")
                    self.assertEqual(found["chirec"].kind, "child")

    def test_both_hosts_build_IDENTICAL_records_and_manifests(self):
        """Equality, beside the identity assertions: the same type AND the same values."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"), ("chirec", "child"))
            oc_found = oc_runipd.discover_plans(root)
            agy_found = agy_runipd.discover_plans(root)
            self.assertEqual(oc_found, agy_found)
            self.assertEqual(
                oc_runipd.build_dynamic_manifest(root, oc_found),
                agy_runipd.build_dynamic_manifest(root, agy_found),
            )

    def test_the_manifest_carries_the_correct_kind_on_both_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"), ("chirec", "child"))
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    manifest = mod.build_dynamic_manifest(
                        root, mod.discover_plans(root)
                    )
                    self.assertEqual(
                        manifest["plans"]["orcrec"]["kind"], "orchestrator"
                    )
                    self.assertEqual(manifest["plans"]["chirec"]["kind"], "child")


class OrchestratorDetectionStillWorksEndToEnd(unittest.TestCase):
    """Property 3: THE test a field-presence check cannot replace.

    `818uru`'s pinned class warned that dropping `kind` from a shared constructor "would silently
    disable orchestrator detection". A test asserting the field EXISTS would pass against a record whose
    field is always `None`, and the derivation would still be wrong. So these drive the real path:
    `discover_plans` -> `build_dynamic_manifest` -> `action_for`.
    """

    def test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"))
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    manifest = mod.build_dynamic_manifest(
                        root, mod.discover_plans(root)
                    )
                    entry = manifest["plans"]["orcrec"]
                    self.assertEqual(
                        mod.action_for(entry["kind"], entry["status"]),
                        "orchestrate",
                        "an approved orchestrator must NOT be agent-executed; deriving "
                        "`execute` here spends a paid agent turn on a plan that authors no code",
                    )

    def test_an_ordinary_child_still_derives_execute_on_BOTH_hosts(self):
        """The other side of the fence: the unification must not make everything an orchestrator."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("chirec", "child"))
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    manifest = mod.build_dynamic_manifest(
                        root, mod.discover_plans(root)
                    )
                    entry = manifest["plans"]["chirec"]
                    self.assertEqual(
                        mod.action_for(entry["kind"], entry["status"]), "execute"
                    )

    def test_the_decider_is_ONE_shared_object_on_both_hosts(self):
        """Object identity, because two copies agree until one is edited."""
        for name in ("action_for", "determine_action"):
            with self.subTest(symbol=name):
                self.assertIs(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                )
                self.assertIs(
                    getattr(oc_runipd, name),
                    getattr(runner_shared, name),
                )


class TheLegacyManifestFallbackWorksOnBothHosts(unittest.TestCase):
    """Property 4: THE CASE THAT HAD NO COVERAGE AT ALL, and the reason this plan nearly broke a host.

    A runner can be pointed at a HAND-WRITTEN manifest; the shipped
    `tools/ipdrunner/*-driver-manifest.json` is one. If such a manifest predates the `kind` key, then
    the plan's kind is absent from it, and deriving `execute` for an APPROVED ORCHESTRATOR means
    spending an agent turn on a plan that authors no code - the exact defect orchretire-03 (`pgq326`)
    fixed.

    Before `sy7uwh`, the fallback that prevented this existed on the ANTIGRAVITY host ONLY, inside a
    private `_plan_kind` whose docstring described a DIFFERENT caller. Measured: `aw agy run` derived
    `orchestrate` while `aw oc run` derived `execute`, so the two hosts disagreed about a correctness
    gate in the opencode host's DISFAVOR - and NO test observed it, which is why deleting the helper
    (as this plan's checklist originally said to) would have looked free. `sy7uwh` OQ-03 was resolved by
    the maintainer in favor of giving the fallback to BOTH hosts, so these tests assert it for both.
    """

    def _legacy_manifest(self, root: pathlib.Path, id6: str, rel: str) -> dict:
        """A manifest in the pre-`kind` shape: every key a hand-written one carries, and no `kind`."""
        manifest = {
            "schema_version": runner_shared.SCHEMA_VERSION,
            "plans": {
                id6: {
                    "set": "recset",
                    "file": rel,
                    "status": "approved",
                    "order": 0,
                    "dependencies": [],
                }
            },
            "sets": {"recset": {"order": [id6]}},
        }
        self.assertNotIn(
            "kind",
            manifest["plans"][id6],
            "this fixture is only meaningful if it OMITS the key",
        )
        return manifest

    def test_the_resolution_is_ONE_shared_object_on_both_hosts(self):
        for name in ("plan_kind_from_file", "resolve_manifest_kind"):
            with self.subTest(symbol=name):
                self.assertIs(
                    getattr(oc_runipd, name),
                    getattr(agy_runipd, name),
                    f"`{name}` must be ONE shared object; an agy-only fallback is the "
                    "host disagreement `sy7uwh` OQ-03 was resolved to end",
                )
                self.assertIs(getattr(oc_runipd, name), getattr(runner_shared, name))

    def test_a_manifest_WITHOUT_kind_still_derives_orchestrate_on_BOTH_hosts(self):
        """THE regression test that did not exist before this plan.

        This is the assertion that FAILS if `plan_kind_from_file` is deleted, and the one that would
        have failed on the opencode host at any point before `sy7uwh`.

        THE ACTION IS ASSERTED FIRST, AND THAT ORDER IS DELIBERATE. An earlier draft checked the
        resolved KIND first, and under the delete-the-fallback control it failed with
        `None != 'orchestrator'` - correct, but it stopped before reaching the statement that names the
        consequence. The consequence is what `sy7uwh` V-05(b) requires the control to report: `execute`
        where `orchestrate` was required, i.e. a paid agent turn spent on a plan that authors no code.
        So the DERIVATION is asserted first and the kind second, as corroboration.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"))
            plan_path = next(
                (root / ".aw" / "records" / "plans" / "pending").glob("*orcrec*.ipd.md")
            )
            rel = str(plan_path.relative_to(root))
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    manifest = self._legacy_manifest(root, "orcrec", rel)
                    entry = manifest["plans"]["orcrec"]
                    kind = mod.resolve_manifest_kind(entry, plan_path)
                    self.assertEqual(
                        mod.action_for(kind, entry["status"]),
                        "orchestrate",
                        f"{label} derived the wrong ACTION for an approved orchestrator named by a "
                        "LEGACY manifest that omits the `kind` key. `execute` here AGENT-EXECUTES a "
                        "plan that authors no code, reintroducing the exact defect orchretire-03 "
                        "(`pgq326`) fixed; the cause is a missing manifest-then-file fallback "
                        "(`plan_kind_from_file`)",
                    )
                    self.assertEqual(
                        kind,
                        "orchestrator",
                        f"{label} failed to fall back to the plan file for a manifest with "
                        "no `kind` key",
                    )

    def test_a_manifest_WITH_kind_is_trusted_and_no_file_is_read(self):
        """The fallback must be a fallback, not a second source of truth.

        A generated manifest always carries the key, so the normal path must not read the file at all -
        otherwise every run pays a read per plan, which is the cost this plan removed.
        """
        for label, mod in HOSTS:
            with self.subTest(host=label):
                entry = {"kind": "child", "status": "approved"}
                self.assertEqual(
                    mod.resolve_manifest_kind(
                        entry, pathlib.Path("/nonexistent/plan.ipd.md")
                    ),
                    "child",
                )

    def test_an_unreadable_plan_file_fails_to_the_SAFE_direction(self):
        """None -> `determine_action`, i.e. the plan is agent-HANDLED, never silently retired.

        The asymmetry is deliberate and worth pinning: a false `execute` costs an agent turn, while a
        false `orchestrate` would retire a plan whose work nobody performed.
        """
        missing = pathlib.Path("/nonexistent/definitely-not-here.ipd.md")
        for label, mod in HOSTS:
            with self.subTest(host=label):
                self.assertIsNone(mod.plan_kind_from_file(missing))
                self.assertIsNone(mod.resolve_manifest_kind({}, missing))
                self.assertEqual(
                    mod.action_for(mod.resolve_manifest_kind({}, missing), "approved"),
                    "execute",
                )

    def test_both_hosts_resolve_a_legacy_manifest_IDENTICALLY(self):
        """The property OQ-03 actually bought: no disagreement, whatever the answer is."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"), ("chirec", "child"))
            pending = root / ".aw" / "records" / "plans" / "pending"
            for id6 in ("orcrec", "chirec"):
                plan_path = next(pending.glob(f"*{id6}*.ipd.md"))
                entry = {"set": "recset", "file": str(plan_path.relative_to(root))}
                with self.subTest(plan=id6):
                    self.assertEqual(
                        oc_runipd.resolve_manifest_kind(entry, plan_path),
                        agy_runipd.resolve_manifest_kind(entry, plan_path),
                    )

    def test_the_shipped_hand_written_manifests_are_still_understood(self):
        """Not a hypothetical: the repo SHIPS manifests, so check whichever exist.

        Skips rather than fails when none is present, because their presence is not this plan's
        contract; what matters is that if one exists, the fallback's premise about it is TRUE.
        """
        manifests = sorted(
            (REPO_ROOT / "tools" / "ipdrunner").glob("*-driver-manifest.json")
        )
        if not manifests:
            self.skipTest("no shipped hand-written manifest in this checkout")
        for path in manifests:
            with self.subTest(manifest=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                plans = data.get("plans", {})
                self.assertTrue(plans, f"{path.name} declares no plans")
                # The point of the fallback: these entries carry no `kind`, so BOTH hosts must reach
                # for the plan file rather than deriving `execute`.
                without_kind = [k for k, v in plans.items() if v.get("kind") is None]
                self.assertEqual(
                    len(without_kind),
                    len(plans),
                    f"{path.name} now carries `kind` for some plans; the fallback's premise "
                    "changed and this test's framing should be re-checked",
                )


class NonVacuityControls(unittest.TestCase):
    """PROVE THE ASSERTIONS ABOVE CAN FAIL. A control that cannot fail leaves the change unproven.

    Both controls are performed IN-PROCESS against a rebuilt record/function rather than by editing the
    shipped source, so nothing is mutated on disk and the tests are safe to run in parallel. Each
    reproduces the exact silent failure its property guards against, and asserts that the guard's own
    logic rejects it.
    """

    def test_control_A_a_record_without_kind_breaks_orchestrator_detection(self):
        """`sy7uwh` F-3 / V-05(b) first control: the SILENT, type-shaped failure, reproduced.

        Build the pre-merge agy shape (no `kind`), parse a real orchestrator with it, and show that the
        manifest entry then carries NO kind and `action_for` derives `execute` - so an approved
        orchestrator would be AGENT-EXECUTED, with nothing raising.
        """
        from typing import NamedTuple

        class RecordWithoutKind(NamedTuple):
            id6: str
            setid: str
            status: str
            order: int
            path: pathlib.Path
            rel_path: str
            dependencies: list
            dependency_error: str | None = None
            from_backlog: str | None = None

        self.assertNotIn("kind", RecordWithoutKind._fields)
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"))
            real = oc_runipd.discover_plans(root)["orcrec"]
            self.assertEqual(real.kind, "orchestrator")
            degraded = RecordWithoutKind(
                id6=real.id6,
                setid=real.setid,
                status=real.status,
                order=real.order,
                path=real.path,
                rel_path=real.rel_path,
                dependencies=real.dependencies,
                dependency_error=real.dependency_error,
                from_backlog=real.from_backlog,
            )
            # The failure is SILENT: reading a missing field yields None through `getattr`, exactly as a
            # shared constructor building the wrong type would.
            degraded_kind = getattr(degraded, "kind", None)
            self.assertIsNone(degraded_kind)
            self.assertEqual(
                runner_shared.action_for(degraded_kind, degraded.status),
                "execute",
                "the control is vacuous: dropping `kind` must change the derivation",
            )
            # And the inverted pin's own assertion refuses the degraded shape.
            with self.assertRaises(AssertionError):
                self.assertIn("kind", RecordWithoutKind._fields)
            # While the shipped record satisfies it.
            self.assertIn("kind", runner_shared.PlanRecord._fields)

    def test_control_B_deleting_the_fallback_breaks_the_legacy_manifest(self):
        """`sy7uwh` F-7 / V-05(b) second control: the mistake the checklist originally invited.

        Reproduce "delete `plan_kind_from_file`" as the pass-through it degrades to, and show the legacy
        manifest then derives `execute` where `orchestrate` was required - naming both values, which is
        what the plan's V-05(b) demands.
        """

        def resolve_without_fallback(entry, _plan_path):
            """What `resolve_manifest_kind` becomes if the fallback is deleted: oc's old behavior."""
            return entry.get("kind")

        with tempfile.TemporaryDirectory() as tmp:
            root = _repo_with(tmp, ("orcrec", "orchestrator"))
            plan_path = next(
                (root / ".aw" / "records" / "plans" / "pending").glob("*orcrec*.ipd.md")
            )
            entry = {
                "set": "recset",
                "file": str(plan_path.relative_to(root)),
                "status": "approved",
            }
            without = resolve_without_fallback(entry, plan_path)
            self.assertIsNone(without)
            self.assertEqual(
                runner_shared.action_for(without, "approved"),
                "execute",
                "the control is vacuous: without the fallback the derivation must be `execute`",
            )
            # WITH the shipped fallback, on BOTH hosts, it is `orchestrate`.
            for label, mod in HOSTS:
                with self.subTest(host=label):
                    withf = mod.resolve_manifest_kind(entry, plan_path)
                    self.assertEqual(withf, "orchestrator")
                    self.assertEqual(mod.action_for(withf, "approved"), "orchestrate")

    def test_control_C_the_repo_wide_scan_would_catch_a_re_fork(self):
        """The scan's LOGIC exercised against a synthetic re-fork, without touching the real package.

        Asserts the scan is not vacuous in the way `2c122z`'s review found a `grep "return True"` proof
        to be: a second definition in a second file must be COUNTED, and an `import` must not be.
        """
        with tempfile.TemporaryDirectory() as tmp:
            fake = pathlib.Path(tmp)
            (fake / "owner.py").write_text(
                "class PlanRecord:\n    pass\n", encoding="utf-8"
            )
            (fake / "importer.py").write_text(
                "from owner import PlanRecord\n", encoding="utf-8"
            )
            (fake / "refork.py").write_text(
                "class PlanRecord:\n    pass\n", encoding="utf-8"
            )
            sites = []
            for path in sorted(fake.glob("*.py")):
                if "PlanRecord" in _top_level_definitions(path):
                    sites.append(path.name)
            self.assertEqual(
                sites,
                ["owner.py", "refork.py"],
                "the scan must count a second DEFINITION and must not count an IMPORT",
            )


if __name__ == "__main__":
    unittest.main()
